#!/usr/bin/env python3
"""Re-cut Reign from a newer upstream hermes-agent commit.

    python rebrand/sync_upstream.py --dry-run          # gates only, report, no commit
    python rebrand/sync_upstream.py                    # also creates branch sync/upstream-<date>
    python rebrand/sync_upstream.py --ref upstream/main --no-lockfiles

Steps (all in a throwaway git worktree at the upstream ref):
  1. copy rebrand/ + brand/ + plan into the worktree
  2. run rebrand/rebrand.py            (stages 1-5: delete, protect, replace, rename, post_replace)
  3. git apply --3way rebrand/overlay/hand-edits.patch   (Phase 3/4 hand edits)
  4. run rebrand/place_images.py
  5. regenerate uv.lock and npm lockfiles (--no-lockfiles to skip; the overlay never carries them)
  6. gates: rebrand.py --check residual delta vs. rebrand/audit/residual-after-phase4.txt,
            upstream image hashes, conflict markers left by step 3
  7. git commit-tree with parents (current Reign HEAD, upstream commit) -> branch sync/upstream-<date>

The result is a merge commit, so existing installs fast-forward on `reign update`.
Nothing touches the current branch or main; review the sync branch and open a PR.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REBRAND = ROOT / "rebrand"
PY = ROOT / ".venv" / "bin" / "python"
NEUTRAL_IMAGE_RE = re.compile(
    r"website/static/img/(dashboard|docs|kanban-tutorial)/|telegram-botfather|unbroker|pet-egg|"
    r"feature-(automation|connect|memory|sandbox)|session-source-folders|reign-achievements/docs"
)


def sh(*cmd: str, cwd: Path = ROOT, check: bool = True, quiet: bool = False) -> str:
    r = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if check and r.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd)}\n{r.stdout}\n{r.stderr}")
    if not quiet and r.stdout.strip():
        print(r.stdout.rstrip())
    return r.stdout


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="upstream/main")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-lockfiles", dest="lockfiles", action="store_false", help="skip regenerating uv.lock and npm lockfiles")
    ap.add_argument("--keep-worktree", action="store_true")
    args = ap.parse_args()

    if not PY.exists():
        sys.exit("project venv missing: run uv sync first")
    date = dt.date.today().isoformat()
    wt = Path(os.environ.get("REIGN_SYNC_WORKTREE", f"/tmp/reign-sync-{date}"))
    if wt.exists():
        sh("git", "worktree", "remove", "--force", str(wt), check=False, quiet=True)
        shutil.rmtree(wt, ignore_errors=True)

    print(f"→ fetching upstream and checking out {args.ref}")
    sh("git", "fetch", "-q", "upstream", quiet=True)
    upstream_sha = sh("git", "rev-parse", args.ref, quiet=True).strip()
    reign_head = sh("git", "rev-parse", "HEAD", quiet=True).strip()
    sh("git", "worktree", "add", "-q", "--detach", str(wt), upstream_sha, quiet=True)
    print(f"  upstream {upstream_sha[:10]}  reign HEAD {reign_head[:10]}  worktree {wt}")

    print("→ staging rebrand tooling and brand assets")
    for name in ("rebrand", "brand"):
        shutil.copytree(ROOT / name, wt / name, dirs_exist_ok=True)
    shutil.copy(ROOT / "REIGN-REBRAND-PLAN.md", wt / "REIGN-REBRAND-PLAN.md")
    sh("git", "add", "-A", "rebrand", "brand", "REIGN-REBRAND-PLAN.md", cwd=wt, quiet=True)

    print("→ running codemod")
    out = sh(str(PY), "rebrand/rebrand.py", cwd=wt, quiet=True)
    print("  " + "\n  ".join(l for l in out.splitlines() if l.startswith(("deleted", "files ", "post_replace", "mode"))))

    print("→ applying hand-edit overlay (3-way, per file so one failure cannot abort the rest)")
    sh("git", "add", "-A", cwd=wt, quiet=True)  # --3way needs the index to match the codemod output
    patch = REBRAND / "overlay" / "hand-edits.patch"
    patch_files = re.findall(r"^diff --git a/(.*?) b/", patch.read_text(errors="replace"), re.M)
    failed = []
    for pf in patch_files:
        r = subprocess.run(["git", "apply", "--3way", f"--include={pf}", str(patch)], cwd=wt, text=True, capture_output=True)
        if r.returncode != 0 and "with conflicts" not in (r.stdout + r.stderr):
            msg = next((l for l in (r.stdout + r.stderr).splitlines() if "error:" in l), r.stderr.strip()[:120])
            failed.append(f"{pf}: {msg}")
    conflicts = sh("git", "diff", "--name-only", "--diff-filter=U", cwd=wt, quiet=True).split()
    print(f"  overlay: {len(patch_files)} files; {len(conflicts)} with conflicts, {len(failed)} could not apply")
    for c in conflicts:
        print(f"   conflict: {c}")
    for f in failed[:20]:
        print(f"   failed:   {f}")

    print("→ placing images")
    sh(str(PY), "rebrand/place_images.py", cwd=wt, quiet=True)

    if args.lockfiles:
        print("→ regenerating lockfiles")
        env = dict(os.environ, PATH="/opt/homebrew/bin:" + os.environ.get("PATH", ""))
        subprocess.run(["uv", "lock"], cwd=wt, env=env, check=True)
        for d in (".", "plugins/platforms/photon/sidecar", "scripts/whatsapp-bridge"):
            subprocess.run(["npm", "install", "--package-lock-only", "--ignore-scripts", "--no-audit", "--no-fund"],
                           cwd=wt / d, env=env, check=True)
        subprocess.run(["npx", "-y", "npm@12", "install", "--package-lock-only", "--ignore-scripts", "--no-audit", "--no-fund"],
                       cwd=wt / "website", env=env, check=True)

    print("→ gates")
    sh("git", "add", "-A", cwd=wt, quiet=True)
    res = subprocess.run([str(PY), "rebrand/rebrand.py", "--check"], cwd=wt, text=True, capture_output=True).stdout
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
            import hashlib
            if hashlib.sha256(p.read_bytes()).hexdigest() in upstream_hashes and not NEUTRAL_IMAGE_RE.search(str(p.relative_to(wt))):
                survivors.append(str(p.relative_to(wt)))
    print(f"  images: {len(survivors)} upstream image(s) survived outside the neutral set")
    for s_ in survivors[:20]:
        print(f"   {s_}")
    markers = sh("git", "grep", "-l", "^<<<<<<< ", "--", ".", cwd=wt, check=False, quiet=True).split()
    print(f"  conflict markers: {len(markers)} file(s)")

    blocked = conflicts or failed or survivors or markers
    if args.dry_run or blocked:
        print("\nDRY RUN — no commit." if args.dry_run else "\nBLOCKED — resolve the items above in the worktree, then re-run gates by hand.")
        if not args.keep_worktree and args.dry_run and not blocked:
            sh("git", "worktree", "remove", "--force", str(wt), quiet=True)
        else:
            print(f"worktree kept at {wt}")
        return

    print("→ recording merge commit")
    tree = sh("git", "write-tree", cwd=wt, quiet=True).strip()
    msg = (f"Reign: sync with upstream {upstream_sha[:10]} ({date})\n\n"
           f"Re-cut from NousResearch/hermes-agent {upstream_sha} via rebrand/sync_upstream.py:\n"
           f"codemod + hand-edit overlay + image placement. Parents: previous Reign head\n"
           f"{reign_head} and the upstream commit.\n\nCo-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>\n")
    commit = subprocess.run(["git", "commit-tree", tree, "-p", reign_head, "-p", upstream_sha, "-m", msg],
                            cwd=wt, text=True, capture_output=True, check=True).stdout.strip()
    branch = f"sync/upstream-{date}"
    sh("git", "branch", "-f", branch, commit, quiet=True)
    print(f"  {branch} -> {commit[:10]}  (review, run scripts/run_tests.sh, then open a PR)")
    if not args.keep_worktree:
        sh("git", "worktree", "remove", "--force", str(wt), quiet=True)


if __name__ == "__main__":
    main()
