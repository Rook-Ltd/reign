#!/usr/bin/env python3
"""Reign rebrand codemod: transforms an upstream hermes-agent checkout into Reign.

Usage (from repo root, inside a git checkout):
  python rebrand/rebrand.py --dry-run     # report what would change, touch nothing
  python rebrand/rebrand.py               # apply: delete, rewrite, rename (git mv)
  python rebrand/rebrand.py --check       # list residual hermes/nous hits not allowlisted

Driven by rebrand/mapping.yaml. Idempotent: a second run is a no-op.
Requires PyYAML (available in the project venv).
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MAPPING = Path(__file__).resolve().parent / "mapping.yaml"
SENT_L, SENT_R = "", ""  # private-use sentinels for protected spans
HIT_RE = re.compile(r"hermes|\bnous", re.IGNORECASE)


def sh(*cmd: str, check: bool = True) -> str:
    return subprocess.run(cmd, cwd=ROOT, check=check, capture_output=True, text=True).stdout


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True).stdout
    return [p.decode("utf-8", "surrogateescape") for p in out.split(b"\0") if p]


def globs_match(path: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(path, pat.rstrip("/**")) or path.startswith(pat.rstrip("*").rstrip("/") + "/"):
            return True
    return False


def is_binary(data: bytes) -> bool:
    return b"\0" in data[:8192]


class Rebrander:
    def __init__(self, mapping: dict):
        self.m = mapping
        self.exclude = mapping.get("exclude_files", [])
        self.protect = [re.compile(p) for p in mapping.get("protect", [])]
        self.replace = []
        for r in mapping.get("replace", []):
            if "plain" in r:
                self.replace.append((re.compile(re.escape(r["plain"])), r["with"]))
            else:
                self.replace.append((re.compile(r["regex"]), r["with"]))
        self.rename = [(re.compile(re.escape(r["plain"])), r["with"]) for r in mapping.get("rename_paths", [])]
        self.check_allow = [re.compile(p) for p in mapping.get("check_allow", [])]
        self.stats = Counter()
        self.rule_hits = Counter()

    # ---------- content ----------
    def transform_text(self, text: str) -> str:
        store: list[str] = []

        def shield(match: re.Match) -> str:
            store.append(match.group(0))
            return f"{SENT_L}{len(store) - 1}{SENT_R}"

        for rx in self.protect:
            text = rx.sub(shield, text)
        for rx, repl in self.replace:
            text, n = rx.subn(repl, text)
            if n:
                self.rule_hits[rx.pattern[:40]] += n
        if store:
            text = re.sub(f"{SENT_L}(\\d+){SENT_R}", lambda m: store[int(m.group(1))], text)
        return text

    def rewrite_files(self, files: list[str], apply: bool) -> list[str]:
        changed = []
        for rel in files:
            if globs_match(rel, self.exclude):
                continue
            p = ROOT / rel
            if not p.is_file() or p.is_symlink():
                continue
            data = p.read_bytes()
            if is_binary(data):
                continue
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                self.stats["undecodable"] += 1
                continue
            if not HIT_RE.search(text):
                continue
            new = self.transform_text(text)
            if new != text:
                changed.append(rel)
                if apply:
                    p.write_bytes(new.encode("utf-8"))
        self.stats["files_rewritten"] = len(changed)
        return changed

    # ---------- paths ----------
    def new_path(self, rel: str) -> str:
        if globs_match(rel, self.exclude):
            return rel
        parts = []
        for comp in rel.split("/"):
            for rx, repl in self.rename:
                comp = rx.sub(repl, comp)
            parts.append(comp)
        return "/".join(parts)

    def rename_files(self, files: list[str], apply: bool) -> list[tuple[str, str]]:
        moves = [(f, self.new_path(f)) for f in files]
        moves = [(a, b) for a, b in moves if a != b]
        targets = Counter(b for _, b in moves)
        clashes = [b for b, n in targets.items() if n > 1]
        if clashes:
            sys.exit(f"rename clash: {clashes[:5]}")
        existing = set(files)
        for a, b in moves:
            if b in existing and b not in {x for x, _ in moves}:
                sys.exit(f"rename target already exists: {a} -> {b}")
        if apply:
            for a, b in moves:
                (ROOT / b).parent.mkdir(parents=True, exist_ok=True)
                for attempt in range(6):
                    r = subprocess.run(["git", "mv", "-k", a, b], cwd=ROOT, capture_output=True, text=True)
                    if r.returncode == 0:
                        break
                    if "index.lock" in r.stderr and attempt < 5:
                        import time; time.sleep(0.5 * (attempt + 1))
                        continue
                    sys.exit(f"git mv failed: {a} -> {b}\n{r.stderr}")
            # prune emptied directories
            for a, _ in moves:
                d = (ROOT / a).parent
                while d != ROOT and d.exists() and not any(d.iterdir()):
                    d.rmdir()
                    d = d.parent
        self.stats["files_renamed"] = len(moves)
        return moves

    # ---------- deletions ----------
    def delete_paths(self, apply: bool) -> list[str]:
        gone = []
        for rel in self.m.get("delete", []):
            p = ROOT / rel
            if p.exists():
                gone.append(rel)
                if apply:
                    subprocess.run(["git", "rm", "-r", "-q", "--", rel], cwd=ROOT, check=True)
        self.stats["paths_deleted"] = len(gone)
        return gone

    # ---------- residual check ----------
    def check(self, files: list[str]) -> int:
        residual = defaultdict(list)
        total = 0
        for rel in files:
            if globs_match(rel, self.exclude):
                continue
            p = ROOT / rel
            if not p.is_file():
                continue
            data = p.read_bytes()
            if is_binary(data):
                if HIT_RE.search(rel):
                    residual["<binary path>"].append(rel)
                    total += 1
                continue
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if not HIT_RE.search(line):
                    continue
                stripped = line
                for rx in self.check_allow:
                    stripped = rx.sub("", stripped)
                if HIT_RE.search(stripped):
                    residual[rel].append(f"{i}: {line.strip()[:160]}")
                    total += 1
        for rel in sorted(residual):
            print(f"\n{rel}")
            for ln in residual[rel][:8]:
                print(f"   {ln}")
            if len(residual[rel]) > 8:
                print(f"   ... {len(residual[rel]) - 8} more")
        print(f"\nresidual: {total} lines in {len(residual)} files")
        return total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    mapping = yaml.safe_load(MAPPING.read_text())
    rb = Rebrander(mapping)
    files = tracked_files()

    if args.check:
        sys.exit(1 if rb.check(files) else 0)

    apply = not args.dry_run
    gone = rb.delete_paths(apply)
    if apply:
        files = tracked_files()
    else:
        files = [f for f in files if not any(f == g or f.startswith(g.rstrip("/") + "/") for g in gone)]
    changed = rb.rewrite_files(files, apply)
    moves = rb.rename_files(files, apply)

    print(f"deleted paths:   {len(gone)}")
    for g in gone:
        print(f"   - {g}")
    print(f"files rewritten: {len(changed)}")
    print(f"files renamed:   {len(moves)}")
    top_dirs = Counter(m[0].split('/')[0] for m in moves)
    for d, n in top_dirs.most_common(12):
        print(f"   {n:4d}  {d}")
    print("rule hits:")
    for rule, n in rb.rule_hits.most_common():
        print(f"   {n:7d}  {rule}")
    if rb.stats.get("undecodable"):
        print(f"undecodable files skipped: {rb.stats['undecodable']}")
    print("mode:", "DRY RUN (nothing written)" if args.dry_run else "APPLIED")


if __name__ == "__main__":
    main()
