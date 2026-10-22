#!/usr/bin/env python3
"""Re-cut Reign from a newer upstream hermes-agent commit.

    python rebrand/sync_upstream.py --dry-run          # gates only, report, no commit
    python rebrand/sync_upstream.py                    # also creates branch sync/upstream-<date>
    python rebrand/sync_upstream.py --ref upstream/main --no-lockfiles

Reign's hand edits are carried by a three-way merge, not a patch file:

  base   = replay(upstream commit in rebrand/UPSTREAM.md "Synced at")
  theirs = replay(new upstream ref)
  ours   = current Reign HEAD

where replay(ref) runs, in a throwaway git worktree at ref:
  1. copy rebrand/ + brand/ + plan into the worktree
  2. run rebrand/rebrand.py            (stages 1-5: delete, protect, replace, rename, post_replace)
  3. run rebrand/place_images.py, then website/scripts/generate-skill-docs.py
  4. regenerate uv.lock and npm lockfiles (--no-lockfiles to skip), then eslint --fix the JS
     workspaces and ruff --fix RUF022: hermes->reign renames reorder sorted imports, keys and
     __all__ lists, which the lint rules reject (--no-lint-fix to skip)

ours - base is then exactly what Reign changed by hand since the last sync (Rook-authored files,
test fixes, features), so every such edit carries over, including ones nobody remembered to put
in rebrand/overlay/hand-edits.patch. After the merge:
  5. .github/workflows comes from theirs (workflows are regenerated from upstream plus mapping
     rules; Rook-authored workflows upstream doesn't have are kept), lockfiles are regenerated
  6. gates: rebrand.py --check residual delta vs. rebrand/audit/residual-after-phase4.txt,
            upstream image hashes, merge conflicts and conflict markers
  7. git commit-tree with parents (current Reign HEAD, upstream commit) -> branch sync/upstream-<date>

The result is a merge commit, so existing installs fast-forward on `reign update`.
Nothing touches the current branch or main; review the sync branch and open a PR.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REBRAND = ROOT / "rebrand"
PY = ROOT / ".venv" / "bin" / "python"
NEUTRAL_IMAGE_RE = re.compile(
    r"website/static/img/(dashboard|docs|kanban-tutorial)/|telegram-botfather|unbroker|pet-egg|"
    r"feature-(automation|connect|memory|sandbox)|session-source-folders|reign-achievements/docs"
)
LOCKFILE_RE = re.compile(r"(^|/)(uv\.lock|package-lock\.json)$")
ENV = dict(os.environ, PATH="/opt/homebrew/bin:" + os.environ.get("PATH", ""))


def sh(*cmd: str, cwd: Path = ROOT, check: bool = True, quiet: bool = False) -> str:
    r = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)
    if check and r.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd)}\n{r.stdout}\n{r.stderr}")
    if not quiet and r.stdout.strip():
        print(r.stdout.rstrip())
    return r.stdout


def add_worktree(wt: Path, ref: str) -> None:
    if wt.exists():
        sh("git", "worktree", "remove", "--force", str(wt), check=False, quiet=True)
        shutil.rmtree(wt, ignore_errors=True)
    sh("git", "worktree", "add", "-q", "--detach", str(wt), ref, quiet=True)


def regenerate_lockfiles(wt: Path) -> None:
    subprocess.run(["uv", "lock"], cwd=wt, env=ENV, check=True)
    for d in (".", "plugins/platforms/photon/sidecar", "scripts/whatsapp-bridge"):
        subprocess.run(["npm", "install", "--package-lock-only", "--ignore-scripts", "--no-audit", "--no-fund"],
                       cwd=wt / d, env=ENV, check=True)
    subprocess.run(["npx", "-y", "npm@12", "install", "--package-lock-only", "--ignore-scripts", "--no-audit", "--no-fund"],
                   cwd=wt / "website", env=ENV, check=True)


def replay(ref: str, wt: Path, args: argparse.Namespace) -> tuple[str, dict[str, int]]:
    """Rebrand upstream `ref` in worktree `wt`; return the resulting tree and the post_replace
    rule hit counts."""
    print(f"→ replaying {ref[:10]} in {wt}")
    add_worktree(wt, ref)
    for name in ("rebrand", "brand"):
        shutil.copytree(ROOT / name, wt / name, dirs_exist_ok=True)
    shutil.copy(ROOT / "REIGN-REBRAND-PLAN.md", wt / "REIGN-REBRAND-PLAN.md")
    sh("git", "add", "-A", "rebrand", "brand", "REIGN-REBRAND-PLAN.md", cwd=wt, quiet=True)

    out = sh(str(PY), "rebrand/rebrand.py", cwd=wt, quiet=True)
    print("  " + "\n  ".join(l for l in out.splitlines() if l.startswith(("deleted", "files ", "post_replace", "mode"))))
    hits = {m.group(2): int(m.group(1)) for m in re.finditer(r"^ +(\d+)  (post:.*)$", out, re.MULTILINE)}
    sh(str(PY), "rebrand/place_images.py", cwd=wt, quiet=True)
    sh(str(PY), "website/scripts/generate-skill-docs.py", cwd=wt, quiet=True)
    if args.lockfiles:
        print("  regenerating lockfiles")
        regenerate_lockfiles(wt)
    if args.lint_fix:
        print("  eslint --fix (renames change sort order)")
        subprocess.run(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=wt, env=ENV, check=True,
                       stdout=subprocess.DEVNULL)
        for d, paths in (("apps/shared", ["src/"]), ("apps/desktop", ["src/", "electron/"]), ("ui-tui", ["src/", "packages/"])):
            r = subprocess.run(["npx", "eslint", "--fix", *paths], cwd=wt / d, env=ENV, text=True, capture_output=True, check=False)
            if r.returncode:
                print(f"   {d}: errors eslint cannot fix remain (JS & TS checks will fail)")
        # Renamed strings in the English catalog change the committed i18n key index.
        for d in ("apps/desktop", "ui-tui"):
            subprocess.run(["npm", "run", "i18n:keys"], cwd=wt / d, env=ENV, check=False, stdout=subprocess.DEVNULL)
        # Same for Python: renamed names reorder sorted __all__ lists (RUF022), which the
        # blocking `ruff check .` rejects. Uses the ruff CI pins.
        pin = sh(str(PY), "-m", "scripts.code_health", "--print-pins", cwd=wt, check=False, quiet=True).strip()
        if pin.startswith("ruff=="):
            subprocess.run(["uvx", "--from", pin, "ruff", "check", "--fix", "--select", "RUF022", "--exit-zero", "--quiet", "."],
                           cwd=wt, env=ENV, check=False)
    sh("git", "add", "-A", cwd=wt, quiet=True)
    return sh("git", "write-tree", cwd=wt, quiet=True).strip(), hits


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="upstream/main")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-lockfiles", dest="lockfiles", action="store_false", help="skip regenerating uv.lock and npm lockfiles")
    ap.add_argument("--no-lint-fix", dest="lint_fix", action="store_false", help="skip eslint --fix on the JS workspaces")
    ap.add_argument("--no-fetch", dest="fetch", action="store_false", help="use the upstream refs already fetched")
    ap.add_argument("--keep-worktree", action="store_true")
    ap.add_argument("--ci", action="store_true", help="exit 2 when blocked, 3 when nothing to sync; write report to $GITHUB_STEP_SUMMARY-style file rebrand/audit/sync-report.md")
    ap.add_argument("--branch", default=None, help="name for the sync branch (default sync/upstream-<date>)")
    args = ap.parse_args()

    if not PY.exists():
        sys.exit("project venv missing: run uv sync first")
    date = dt.date.today().isoformat()
    wt = Path(os.environ.get("REIGN_SYNC_WORKTREE") or Path(tempfile.gettempdir()) / f"reign-sync-{date}")
    base_wt = wt.with_name(wt.name + "-base")

    if args.fetch:
        print("→ fetching upstream")
        sh("git", "fetch", "-q", "upstream", quiet=True)
    upstream_sha = sh("git", "rev-parse", f"{args.ref}^{{commit}}", quiet=True).strip()  # annotated tags -> commit
    reign_head = sh("git", "rev-parse", "HEAD", quiet=True).strip()
    synced_line = next((l for l in (REBRAND / "UPSTREAM.md").read_text().splitlines() if l.startswith("- Synced at:")), "")
    if upstream_sha in synced_line:
        print(f"  already synced at {upstream_sha[:10]}; nothing to do")
        sys.exit(3 if args.ci else 0)
    m = re.search(r"\b([0-9a-f]{40})\b", synced_line)
    if not m:
        sys.exit("rebrand/UPSTREAM.md has no '- Synced at: <sha>' line to use as the merge base")
    base_sha = m.group(1)
    print(f"  base {base_sha[:10]}  upstream {upstream_sha[:10]}  reign HEAD {reign_head[:10]}")

    base_tree, base_hits = replay(base_sha, base_wt, args)
    new_tree, new_hits = replay(upstream_sha, wt, args)
    # A mapping rule that matched the old upstream but not the new one usually means upstream
    # reshaped the code it targets, and the Reign change it made is silently gone.
    dead_rules = sorted(r for r in base_hits if r not in new_hits)
    print(f"  mapping rules that stopped matching: {len(dead_rules)}")
    for r in dead_rules:
        print(f"   {r}")

    print("→ merging Reign's hand edits (HEAD vs. replayed base) onto the replayed upstream")
    c_base = sh("git", "commit-tree", base_tree, "-m", "replayed base", quiet=True).strip()
    c_new = sh("git", "commit-tree", new_tree, "-m", "replayed upstream", quiet=True).strip()
    r = subprocess.run(["git", "merge-tree", "--write-tree", "--name-only", "--no-messages", "--merge-base", c_base, reign_head, c_new],
                       cwd=ROOT, text=True, capture_output=True, check=False)
    if r.returncode not in (0, 1):
        sys.exit(f"git merge-tree failed:\n{r.stderr}")
    lines = r.stdout.splitlines()
    merged_tree, conflicted = lines[0], sorted({l for l in lines[1:] if l})
    sh("git", "read-tree", "--reset", "-u", merged_tree, cwd=wt, quiet=True)
    # Workflows are regenerated from upstream plus mapping rules; Rook-authored ones upstream
    # doesn't have stay as merged.
    sh("git", "checkout", c_new, "--", ".github/workflows", cwd=wt, quiet=True)
    manifests = [p for p in conflicted if p.endswith("package.json") or p.endswith("pyproject.toml")]
    relocked = args.lockfiles and not manifests
    if args.lockfiles and manifests:
        print(f"  not regenerating lockfiles: {', '.join(manifests)} conflicted (resolve, then rerun them)")
    elif args.lockfiles:
        print("  regenerating lockfiles on the merged tree")
        locks = [p for p in sh("git", "ls-tree", "-r", "--name-only", c_new, cwd=wt, quiet=True).splitlines() if LOCKFILE_RE.search(p)]
        sh("git", "checkout", c_new, "--", *locks, cwd=wt, quiet=True)
        regenerate_lockfiles(wt)
    sh("git", "add", "-A", cwd=wt, quiet=True)
    resolved = lambda p: p.startswith(".github/workflows/") and sh("git", "cat-file", "-t", f"{c_new}:{p}", cwd=wt, check=False, quiet=True).strip() == "blob"
    conflicts = [p for p in conflicted if not (resolved(p) or (relocked and LOCKFILE_RE.search(p)))]
    hand_edited = len(sh("git", "diff", "--name-only", base_tree, reign_head, "--", ".", ":(exclude)rebrand", quiet=True).split())
    print(f"  hand-edited files carried: {hand_edited}; {len(conflicts)} with conflicts")
    for c in conflicts:
        print(f"   conflict: {c}")

    up = wt / "rebrand" / "UPSTREAM.md"
    txt = [l for l in up.read_text().splitlines() if not l.startswith("- Synced at:")]
    idx = next(i for i, l in enumerate(txt) if l.startswith("- Forked at:")) + 1
    txt.insert(idx, f"- Synced at: {upstream_sha} ({args.ref}, {date})")
    up.write_text("\n".join(txt) + "\n")

    print("→ gates")
    sh("git", "add", "-A", cwd=wt, quiet=True)
    res = subprocess.run([str(PY), "rebrand/rebrand.py", "--check"], cwd=wt, text=True, capture_output=True, check=False).stdout
    (wt / "rebrand/audit/residual-after-sync.txt").write_text(res)
    def keyed(text: str) -> list[tuple[str, str]]:
        out, cur = [], ""
        for l in text.splitlines():
            if l and not l.startswith(" ") and not l.startswith("residual:"):
                cur = l
            elif re.match(r"\s+\d+: ", l):
                out.append((cur, re.sub(r"^\s+\d+: ", "", l).strip()))
        return out
    baseline = set(keyed((REBRAND / "audit" / "residual-after-phase4.txt").read_text()))
    new_lines = [(f, l) for f, l in keyed(res) if (f, l) not in baseline]
    print(f"  residual: {res.strip().splitlines()[-1]}; {len(new_lines)} line(s) not in the Phase 4 baseline")
    for f, l in new_lines[:25]:
        print(f"   {f}: {l[:130]}")
    upstream_hashes = {l.split()[0] for l in (REBRAND / "audit" / "images-sha256.txt").read_text().splitlines()}
    survivors = []
    for p in wt.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".icns", ".webp"} and "node_modules" not in p.parts and ".git" not in p.parts and "brand" not in p.parts[:1]:
            if hashlib.sha256(p.read_bytes()).hexdigest() in upstream_hashes and not NEUTRAL_IMAGE_RE.search(str(p.relative_to(wt))):
                survivors.append(str(p.relative_to(wt)))
    print(f"  images: {len(survivors)} upstream image(s) survived outside the neutral set")
    for s_ in survivors[:20]:
        print(f"   {s_}")
    markers = sh("git", "grep", "-l", "^<<<<<<< ", "--", ".", cwd=wt, check=False, quiet=True).split()
    print(f"  conflict markers: {len(markers)} file(s)")

    blocked = conflicts or survivors or markers
    report = [f"# Upstream sync report — {args.ref} ({upstream_sha[:10]}) on {date}", "",
              f"- base: {base_sha[:10]}; hand-edited files carried: {hand_edited}, {len(conflicts)} with conflicts",
              f"- residual: {res.strip().splitlines()[-1]}; {len(new_lines)} new line(s)",
              f"- images surviving: {len(survivors)}; conflict-marker files: {len(markers)}", ""]
    report += [f"- conflict: `{c}`" for c in conflicts]
    report += [f"- rule stopped matching (check it): `{r}`" for r in dead_rules]
    report += [f"- residual: `{f}`: `{l[:120]}`" for f, l in new_lines[:40]]
    (REBRAND / "audit" / "sync-report.md").write_text("\n".join(report) + "\n")
    if not args.keep_worktree:
        sh("git", "worktree", "remove", "--force", str(base_wt), check=False, quiet=True)
    if args.dry_run or blocked:
        print("\nDRY RUN — no commit." if args.dry_run else "\nBLOCKED — resolve the items above in the worktree, then re-run gates by hand.")
        if not args.keep_worktree and args.dry_run and not blocked:
            sh("git", "worktree", "remove", "--force", str(wt), quiet=True)
        else:
            print(f"worktree kept at {wt}")
        sys.exit(2 if (blocked and args.ci) else 0)

    print("→ recording merge commit")
    tree = sh("git", "write-tree", cwd=wt, quiet=True).strip()
    msg = (f"Reign: sync with upstream {upstream_sha[:10]} ({date})\n\n"
           f"Re-cut from NousResearch/hermes-agent {upstream_sha} via rebrand/sync_upstream.py:\n"
           f"codemod + image placement, with Reign's hand edits since {base_sha[:10]} merged in.\n"
           f"Parents: previous Reign head {reign_head} and the upstream commit.\n")
    commit = subprocess.run(["git", "commit-tree", tree, "-p", reign_head, "-p", upstream_sha, "-m", msg],
                            cwd=wt, text=True, capture_output=True, check=True).stdout.strip()
    branch = args.branch or f"sync/upstream-{date}"
    sh("git", "branch", "-f", branch, commit, quiet=True)
    print(f"  {branch} -> {commit[:10]}  (review, run scripts/run_tests.sh, then open a PR)")
    if not args.keep_worktree:
        sh("git", "worktree", "remove", "--force", str(wt), quiet=True)


if __name__ == "__main__":
    main()
