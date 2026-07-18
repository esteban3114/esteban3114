#!/usr/bin/env python3
"""Prep a photo for ASCII conversion — run once per source image.

A flatly-lit face converts to a dark, unreadable blob, so we:
  1. Remove the background (rembg) → isolate the subject.
  2. Boost local contrast (OpenCV CLAHE) → real highlights and shadows.
  3. Composite onto pure white → background maps to the blank end of the
     ASCII ramp (white → spaces).

Heavy libs (rembg, opencv, numpy) are optional: if they're missing the script
falls back to a Pillow-only path so it still produces a usable grayscale.

Usage:  python scripts/prep_photo.py assets/source-photo.jpg
Output: assets/source-prepped.png  (grayscale)
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "source-prepped.png"
MAX_SIDE = 900  # downscale big photos before the (slow) contrast pass


def load_rgb(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    img = ImageOps.exif_transpose(img)  # honor phone orientation
    if max(img.size) > MAX_SIDE:
        img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    return img


def remove_bg(img: Image.Image) -> Image.Image:
    """Return RGBA with background alpha removed, if rembg is available."""
    try:
        from rembg import remove
    except Exception:
        print("· rembg not installed — skipping background removal")
        return img
    print("· removing background with rembg")
    return remove(img)


def crop_to_subject(rgba: Image.Image, margin: float = 0.05) -> Image.Image:
    """Crop to the subject's alpha bounding box (+ margin) so a wide photo
    fills the character grid instead of shrinking the face to a few rows."""
    if rgba.mode != "RGBA":
        return rgba
    bbox = rgba.split()[3].getbbox()
    if not bbox:
        return rgba
    x0, y0, x1, y1 = bbox
    mx = int((x1 - x0) * margin)
    my = int((y1 - y0) * margin)
    box = (max(0, x0 - mx), max(0, y0 - my),
           min(rgba.width, x1 + mx), min(rgba.height, y1 + my))
    print(f"· cropping to subject {box}")
    return rgba.crop(box)


def to_gray_clahe(img_rgba: Image.Image) -> Image.Image:
    """Grayscale + local contrast. Uses OpenCV CLAHE, else Pillow equalize."""
    try:
        import cv2
        import numpy as np
    except Exception:
        print("· opencv/numpy not installed — Pillow autocontrast fallback")
        gray = ImageOps.grayscale(img_rgba.convert("RGB"))
        return ImageOps.autocontrast(gray, cutoff=2)

    print("· boosting local contrast with CLAHE")
    rgb = np.array(img_rgba.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    out = clahe.apply(gray)
    return Image.fromarray(out, mode="L")


def composite_on_white(gray: Image.Image, alpha: Image.Image | None) -> Image.Image:
    """Paste the subject (via alpha) onto pure white so the bg → white → space."""
    white = Image.new("L", gray.size, 255)
    if alpha is not None:
        white.paste(gray, (0, 0), alpha)
        return white
    return gray


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python scripts/prep_photo.py <source-photo>", file=sys.stderr)
        return 2
    src = Path(argv[1])
    if not src.exists():
        print(f"!! not found: {src}", file=sys.stderr)
        return 1

    img = load_rgb(src)
    cut = remove_bg(img)
    cut = crop_to_subject(cut)

    # keep the alpha (subject mask) if bg removal produced one
    alpha = cut.split()[3] if cut.mode == "RGBA" else None
    gray = to_gray_clahe(cut)
    final = composite_on_white(gray, alpha)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    final.save(OUT)
    print(f"✓ {OUT.relative_to(ROOT)}  ({final.size[0]}×{final.size[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
