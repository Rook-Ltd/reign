#!/usr/bin/env python3
"""Re-derive codemod-only files in the current tree from an upstream ref.

For every tracked file whose upstream counterpart exists and which the overlay does
not touch, recompute codemod(upstream) with the CURRENT mapping and overwrite the
working copy when it differs. Use after changing mapping.yaml mid-sync so the tree
matches what a fresh sync would produce, without re-running the whole sync.

    python rebrand/rederive.py --ref v2026.9.24 [--dry-run]
"""
import argparse, re, subprocess, sys, yaml
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rebrand import Rebrander, MAPPING, ROOT, globs_match, is_binary, tracked_files

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ref", required=True); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    mp = yaml.safe_load(MAPPING.read_text()); rb = Rebrander(mp)
    overlay = set(re.findall(r"^diff --git a/(.*?) b/", (ROOT / "rebrand/overlay/hand-edits.patch").read_text(errors="replace"), re.MULTILINE))
    def upstream_path(rel):  # reverse the path rename: reign_cli -> hermes_cli etc. (best effort)
        return rel.replace("reign_cli", "hermes_cli").replace("reign_state", "hermes_state").replace("reign-ink", "hermes-ink").replace("reign-achievements", "hermes-achievements").replace("reign-bots", "hermes-bots")
    up_files = set(subprocess.run(["git", "ls-tree", "-r", "--name-only", f"{a.ref}^{{commit}}"], capture_output=True, text=True, check=False).stdout.split("\n"))
    changed = []
    for rel in tracked_files():
        if rel in overlay or globs_match(rel, rb.exclude) or rel.startswith(("rebrand/", "brand/")) or rel.endswith((".lock", "package-lock.json")):
            continue
        up = upstream_path(rel)
        if up not in up_files:
            continue
        raw = subprocess.run(["git", "show", f"{a.ref}^{{commit}}:{up}"], capture_output=True, check=False).stdout
        if is_binary(raw):
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        new = rb.transform_text(text)
        for globs, rules in rb.post:
            if globs_match(rel, globs):
                for rx, repl in rules:
                    new = rx.sub(repl, new)
        cur = (ROOT / rel).read_bytes()
        if b"\r\n" in cur:  # eol=crlf checkouts (install.ps1): keep the working-copy line endings
            new = new.replace("\r\n", "\n").replace("\n", "\r\n")
        if new.encode("utf-8") != cur:
            changed.append(rel)
            if not a.dry_run:
                (ROOT / rel).write_bytes(new.encode("utf-8"))
    print(f"{'would change' if a.dry_run else 'rewrote'} {len(changed)} files")
    for c in changed[:60]:
        print("  ", c)

if __name__ == "__main__":
    main()
