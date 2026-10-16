#!/usr/bin/env python3
"""Copy Rook brand derivatives over every upstream image touchpoint. Re-runnable.
Run rebrand/gen_assets.py first. Requires Pillow."""
import re
import shutil
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
G = ROOT / "brand" / "generated"

def png(src: Path, dst: Path, size: int):
    Image.open(src).convert("RGBA").resize((size, size), Image.LANCZOS).save(dst)

mark = G / "rook-mark-2048.png"
outline = G / "rook-mark-outline-1024.png"

# README + docs banner / social
shutil.copy(G / "banner.png", ROOT / "assets/banner.png")
shutil.copy(G / "banner.png", ROOT / "website/static/img/reign-banner.png")
# Docs site logo + favicons (outline reads better small)
png(mark, ROOT / "website/static/img/logo.png", 512)
png(mark, ROOT / "website/static/img/apple-touch-icon.png", 180)
png(outline, ROOT / "website/static/img/favicon-16x16.png", 16)
png(outline, ROOT / "website/static/img/favicon-32x32.png", 32)
shutil.copy(G / "favicon.ico", ROOT / "website/static/img/favicon.ico")
shutil.copy(G / "rook-mark-outline.svg", ROOT / "website/static/img/favicon.svg")
(ROOT / "website/static/img/nous-logo.png").unlink(missing_ok=True)
# Web dashboard favicon (index.html declares it as svg+xml; ship an .ico anyway, browsers sniff)
shutil.copy(G / "favicon.ico", ROOT / "web/public/favicon.ico")
# Desktop app (Electron)
shutil.copy(G / "icon.icns", ROOT / "apps/desktop/assets/icon.icns")
shutil.copy(G / "icon.ico", ROOT / "apps/desktop/assets/icon.ico")
png(mark, ROOT / "apps/desktop/assets/icon.png", 1024)
png(mark, ROOT / "apps/desktop/public/apple-touch-icon.png", 180)
png(mark, ROOT / "apps/desktop/public/rook-mark.png", 512)
# Empty-chat imagemark (masked in chat/intro.tsx): the outline mark, viewBox cropped to the
# mark itself so `contain` sizes the ring rather than the 1366-wide artboard.
_svg = (G / "rook-mark-outline.svg").read_text()
_svg = re.sub(r'viewBox="[^"]*"', 'viewBox="318 22 725 725"', _svg).replace(' style="enable-background:new 0 0 1366 768;"', "")
(ROOT / "apps/desktop/public/rook-mark-outline.svg").write_text(_svg)
(ROOT / "web/public/rook-mark-outline.svg").write_text(_svg)  # dashboard sidebar mark
(ROOT / "apps/desktop/public/nous-girl.jpg").unlink(missing_ok=True)
for p in [ROOT / "apps/desktop/public/reign.png", ROOT / "apps/desktop/public/reign-sprite.png"]:
    p.unlink(missing_ok=True)
shutil.rmtree(ROOT / "apps/desktop/public/reign-frames", ignore_errors=True)
# Desktop backdrop: rendered at 2.5% opacity with mix-blend-difference + invert,
# so a plain black outline mark on white becomes a faint watermark.
W = 2000
bg = Image.new("RGB", (W, int(W * 1.6)), (255, 255, 255))
m = Image.open(outline).convert("RGBA").resize((int(W * 0.8), int(W * 0.8)), Image.LANCZOS)
bg.paste(m, (int(W * 0.1), int(W * 0.25)), m)
bg.save(ROOT / "apps/desktop/public/ds-assets/filler-bg0.jpg", quality=85)
# Tauri bootstrap installer
ti = ROOT / "apps/bootstrap-installer/src-tauri/icons"
png(mark, ti / "32x32.png", 32)
png(mark, ti / "128x128.png", 128)
png(mark, ti / "128x128@2x.png", 256)
shutil.copy(G / "icon.icns", ti / "icon.icns")
shutil.copy(G / "icon.ico", ti / "icon.ico")
png(mark, ROOT / "apps/bootstrap-installer/public/rook-mark.png", 512)
(ROOT / "apps/bootstrap-installer/public/nous-girl.jpg").unlink(missing_ok=True)
print("images placed")
