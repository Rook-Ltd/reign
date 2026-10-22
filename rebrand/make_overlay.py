#!/usr/bin/env python3
"""Regenerate rebrand/overlay/hand-edits.patch.

overlay = diff( codemod(upstream fork point) , HEAD )  minus tooling, brand assets and images.
Anything the codemod rules already produce drops out of the overlay automatically, so
promote churn-prone hand edits to mapping.yaml rules and re-run this to shrink the patch.

    python rebrand/make_overlay.py            # uses the fork point from rebrand/UPSTREAM.md
    python rebrand/make_overlay.py --base SHA
"""
import argparse, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv" / "bin" / "python"
EXCLUDES = [":(exclude)rebrand", ":(exclude)brand", ":(exclude)REIGN-REBRAND-PLAN.md",
            ":(exclude)*.png", ":(exclude)*.jpg", ":(exclude)*.ico", ":(exclude)*.icns", ":(exclude)*.svg",
            ":(exclude)MagicMock", ":(exclude)hermes_agent.egg-info",
            ":(exclude)uv.lock", ":(exclude)package-lock.json", ":(exclude)**/package-lock.json",
            ":(exclude)flake.lock"]  # regenerated per sync


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", help="upstream commit the current Reign tree was cut from")
    args = ap.parse_args()
    base = args.base or re.search(r"Forked at: ([0-9a-f]{40})", (ROOT / "rebrand/UPSTREAM.md").read_text()).group(1)
    wt = Path(tempfile.gettempdir()) / "reign-overlay-base"
    subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=ROOT, capture_output=True, check=False)
    shutil.rmtree(wt, ignore_errors=True)
    subprocess.run(["git", "worktree", "add", "-q", "--detach", str(wt), base], cwd=ROOT, check=True)
    shutil.copytree(ROOT / "rebrand", wt / "rebrand", dirs_exist_ok=True)
    shutil.copytree(ROOT / "brand", wt / "brand", dirs_exist_ok=True)
    subprocess.run(["git", "add", "-A", "rebrand", "brand"], cwd=wt, check=True)
    print(f"→ codemod on {base[:10]}")
    subprocess.run([str(PY), "rebrand/rebrand.py"], cwd=wt, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=wt, check=True)
    tree = subprocess.run(["git", "write-tree"], cwd=wt, check=True, capture_output=True, text=True).stdout.strip()
    import yaml
    owned = yaml.safe_load((ROOT / "rebrand/mapping.yaml").read_text()).get("overlay_exclude", [])
    out = ROOT / "rebrand/overlay/hand-edits.patch"
    with out.open("w") as fh:
        subprocess.run(["git", "diff", "--binary", tree, "HEAD", "--", "."] + EXCLUDES + [f":(exclude){p}" for p in owned], cwd=ROOT, check=True, stdout=fh)
        # Rook-authored workflow lives under an excluded directory; carry it explicitly.
        subprocess.run(["git", "diff", "--binary", tree, "HEAD", "--", ".github/workflows/upstream-sync.yml"], cwd=ROOT, check=True, stdout=fh)
    n = sum(1 for l in out.read_text(errors="replace").splitlines() if l.startswith("diff --git"))
    print(f"→ overlay: {n} files ({out.stat().st_size // 1024} KB)  base tree {tree[:10]}")
    subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
