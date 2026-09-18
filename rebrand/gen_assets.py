#!/usr/bin/env python3
"""Generate Reign brand derivatives from the source files in brand/.

Requires: pdftocairo (poppler), Pillow, iconutil (macOS) for .icns.
Outputs to brand/generated/.
"""
import re, shutil, subprocess, sys
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "brand"
OUT = SRC / "generated"
OUT.mkdir(exist_ok=True)

MARK_SVG = SRC / "Imagemark for embroidery.svg"
MARK_AI = SRC / "Rook Imagemark.ai"
STRAP_AI = SRC / "Rook Logo With Strap.ai"
OUTLINE_AI = SRC / "Imagemark for embroidery.ai"  # ring + solid rook, for small sizes

SIZES = [16, 32, 48, 64, 128, 256, 512, 1024]


def run(*cmd):
    print("+", " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], check=True)


def ai_to_svg(ai: Path, svg: Path):
    # .ai files are PDF-compatible; pdftocairo renders page 1 to SVG.
    run("pdftocairo", "-svg", "-f", "1", "-l", "1", ai, svg)


def ai_to_png(ai: Path, png: Path, width: int, transparent=True):
    args = ["pdftocairo", "-png", "-singlefile", "-f", "1", "-l", "1",
            "-scale-to-x", str(width), "-scale-to-y", "-1"]
    if transparent:
        args.append("-transp")
    run(*args, ai, png.with_suffix(""))


def svg_to_png(svg: Path, png: Path, width: int):
    # pdftocairo can't read SVG; use the .ai (PDF) for raster, keep svg as-is.
    raise NotImplementedError


def trim_alpha(img: Image.Image, pad_ratio=0.0) -> Image.Image:
    bbox = img.getchannel("A").getbbox()
    img = img.crop(bbox)
    if pad_ratio:
        w, h = img.size
        pad = int(max(w, h) * pad_ratio)
        img = ImageOps.expand(img, pad, (0, 0, 0, 0))
    return img


def square(img: Image.Image) -> Image.Image:
    w, h = img.size
    s = max(w, h)
    canvas = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    canvas.paste(img, ((s - w) // 2, (s - h) // 2))
    return canvas


def invert_black_to_white(img: Image.Image) -> Image.Image:
    """Invert luminance of opaque pixels (black->white, white->black), keep alpha."""
    r, g, b, a = img.split()
    rgb = Image.merge("RGB", (r, g, b))
    inv = ImageOps.invert(rgb)
    inv.putalpha(a)
    return inv


def main():
    if not shutil.which("pdftocairo"):
        sys.exit("pdftocairo not found (brew install poppler)")

    # --- circle mark (primary: black disc, white rook) ---
    ai_to_svg(MARK_AI, OUT / "rook-mark.svg")
    ai_to_png(MARK_AI, OUT / "_mark_raw.png", 2048)
    mark = trim_alpha(Image.open(OUT / "_mark_raw.png").convert("RGBA"))
    mark = square(mark)
    mark.save(OUT / "rook-mark-2048.png")
    mark_white = invert_black_to_white(mark)
    mark_white.save(OUT / "rook-mark-white-2048.png")
    for s in SIZES:
        mark.resize((s, s), Image.LANCZOS).save(OUT / f"rook-mark-{s}.png")
        mark_white.resize((s, s), Image.LANCZOS).save(OUT / f"rook-mark-white-{s}.png")

    # favicon.ico (multi-size)
    mark.resize((256, 256), Image.LANCZOS).save(
        OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    # icon.icns via iconutil
    iconset = OUT / "icon.iconset"
    iconset.mkdir(exist_ok=True)
    for s in (16, 32, 128, 256, 512):
        mark.resize((s, s), Image.LANCZOS).save(iconset / f"icon_{s}x{s}.png")
        mark.resize((s * 2, s * 2), Image.LANCZOS).save(iconset / f"icon_{s}x{s}@2x.png")
    if shutil.which("iconutil"):
        run("iconutil", "-c", "icns", iconset, "-o", OUT / "icon.icns")
    # windows .ico for electron
    mark.resize((256, 256), Image.LANCZOS).save(
        OUT / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    # --- outline mark (ring + solid rook; the "embroidery" simplification, best under ~64px) ---
    shutil.copy(MARK_SVG, OUT / "rook-mark-outline.svg")
    ai_to_png(OUTLINE_AI, OUT / "_outline_raw.png", 2048)
    outline = square(trim_alpha(Image.open(OUT / "_outline_raw.png").convert("RGBA")))
    outline_white = invert_black_to_white(outline)
    for s in SIZES:
        outline.resize((s, s), Image.LANCZOS).save(OUT / f"rook-mark-outline-{s}.png")
        outline_white.resize((s, s), Image.LANCZOS).save(OUT / f"rook-mark-outline-white-{s}.png")

    # --- wordmark with strap ---
    ai_to_svg(STRAP_AI, OUT / "rook-logo-strap-black.svg")
    svg = (OUT / "rook-logo-strap-black.svg").read_text()
    (OUT / "rook-logo-strap-white.svg").write_text(
        re.sub(r"rgb\(\s*0%\s*,\s*0%\s*,\s*0%\s*\)", "rgb(100%,100%,100%)", svg))
    ai_to_png(STRAP_AI, OUT / "_strap_raw.png", 3000)
    strap = trim_alpha(Image.open(OUT / "_strap_raw.png").convert("RGBA"), pad_ratio=0.03)
    strap.save(OUT / "rook-logo-strap-black.png")
    invert_black_to_white(strap).save(OUT / "rook-logo-strap-white.png")

    # --- README banner: mark + wordmark on white, 1600x500 ---
    W, H = 1600, 500
    banner = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    m = mark.resize((360, 360), Image.LANCZOS)
    sw = 900
    s = strap.resize((sw, int(strap.height * sw / strap.width)), Image.LANCZOS)
    gap = 80
    total = m.width + gap + s.width
    x0 = (W - total) // 2
    banner.alpha_composite(m, (x0, (H - m.height) // 2))
    banner.alpha_composite(s, (x0 + m.width + gap, (H - s.height) // 2))
    banner.convert("RGB").save(OUT / "banner.png")

    # --- social card 1200x630, black background, white mark + wordmark ---
    W, H = 1200, 630
    card = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    m = mark_white.resize((300, 300), Image.LANCZOS)
    sw = 640
    sw_img = invert_black_to_white(strap).resize((sw, int(strap.height * sw / strap.width)), Image.LANCZOS)
    gap = 60
    total = m.width + gap + sw_img.width
    x0 = (W - total) // 2
    card.alpha_composite(m, (x0, (H - m.height) // 2))
    card.alpha_composite(sw_img, (x0 + m.width + gap, (H - sw_img.height) // 2))
    card.convert("RGB").save(OUT / "social-card.png")

    for p in OUT.glob("_*"):
        p.unlink()
    shutil.rmtree(iconset, ignore_errors=True)
    print("done ->", OUT)


if __name__ == "__main__":
    main()
