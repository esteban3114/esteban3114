#!/usr/bin/env python3
"""Turn assets/source-prepped.png into a self-typing monochrome ASCII SVG.

The prepped image is downsampled to a character grid (~100 wide). Each cell's
brightness picks a glyph from a density ramp — sparse chars for bright areas,
dense ones for dark. Two choices keep it clean instead of noisy:

  · Monochrome  — one light-gray fill (per-char rainbow is what makes most
                  ASCII portraits look like static).
  · High contrast — a busy background washes out to the space glyph, so only
                  the subject prints.

Each row is revealed by a left-to-right clip wipe with a small block cursor
riding the edge, staggered top to bottom. The portrait prints once and freezes
— no looping. Motion is SMIL inside the SVG, so GitHub plays it from an <img>.

Output: avi-ascii.svg
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "source-prepped.png"
OUT = ROOT / "ascii-portrait.svg"

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)
#        ^ leading space clears the background to nothing

COLS = 100              # character columns
CHAR_ASPECT = 0.5       # a monospace cell is ~half as wide as it is tall
FS = 9                  # font size (px)
CHAR_W = 5.0            # advance width per glyph (px) — forced via textLength
LINE_H = 9.0            # line box height (px)
PAD = 16               # dark card padding (top/sides)
PAD_BOTTOM = 30        # extra breathing room under the last row
FILL = "#adbac7"        # single light-gray glyph color
ROW_STAGGER = 0.07      # seconds between successive rows starting to type
TYPE_DUR = 0.65         # seconds for one row to fully wipe in
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def image_to_rows(img: Image.Image) -> list[str]:
    w, h = img.size
    rows = max(1, round(COLS * (h / w) * CHAR_ASPECT))
    small = img.convert("L").resize((COLS, rows), Image.LANCZOS)
    px = small.load()
    ramp_last = len(RAMP) - 1
    out: list[str] = []
    for y in range(rows):
        line = []
        for x in range(COLS):
            v = px[x, y]                       # 0 dark .. 255 white
            idx = round((255 - v) / 255 * ramp_last)
            line.append(RAMP[idx])
        # trailing spaces carry no ink; drop them to shrink the file
        out.append("".join(line).rstrip())
    return out


def build(rows: list[str]) -> str:
    n = len(rows)
    grid_w = COLS * CHAR_W
    grid_h = n * LINE_H
    width = round(grid_w + 2 * PAD)
    height = round(grid_h + PAD + PAD_BOTTOM)

    defs: list[str] = []
    body: list[str] = []

    for i, row in enumerate(rows):
        y = PAD + i * LINE_H
        begin = i * ROW_STAGGER
        row_len = len(row)
        if row_len == 0:
            continue
        row_w = row_len * CHAR_W
        clip_id = f"w{i}"
        # clip rect wipes 0 -> row width, then freezes
        defs.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="{PAD:.0f}" y="{y:.2f}" width="0" height="{LINE_H:.2f}">'
            f'<animate attributeName="width" from="0" to="{row_w:.1f}" '
            f'begin="{begin:.2f}s" dur="{TYPE_DUR:.2f}s" '
            f'calcMode="linear" fill="freeze"/></rect></clipPath>'
        )
        # the glyph row, geometry forced to CHAR_W per char via textLength
        body.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<text x="{PAD:.0f}" y="{y + FS - 1:.2f}" textLength="{row_w:.1f}" '
            f'lengthAdjust="spacing" xml:space="preserve">{esc(row)}</text></g>'
        )
        # block cursor rides the wipe edge, fades out when the row is done
        body.append(
            f'<rect class="cur" x="{PAD:.0f}" y="{y:.2f}" width="{CHAR_W:.1f}" '
            f'height="{LINE_H:.2f}">'
            f'<animate attributeName="x" from="{PAD:.0f}" to="{PAD + row_w:.1f}" '
            f'begin="{begin:.2f}s" dur="{TYPE_DUR:.2f}s" calcMode="linear" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + TYPE_DUR:.2f}s"/>'
            f'</rect>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" font-family="{FONT}" role="img"
     aria-label="ASCII self-portrait">
  <style>
    text {{ fill: {FILL}; font-size: {FS}px; white-space: pre; }}
    .cur {{ fill: {FILL}; opacity: .9; }}
    .card {{ fill: #0d1117; stroke: #21262d; stroke-width: 1; }}
  </style>
  <defs>
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fff"/>
      <stop offset="0.72" stop-color="#fff"/>
      <stop offset="1" stop-color="#000"/>
    </linearGradient>
    <mask id="vign"><rect x="0" y="0" width="{width}" height="{height}" fill="url(#fade)"/></mask>
    {"".join(defs)}
  </defs>
  <rect class="card" x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10"/>
  <g mask="url(#vign)">
  {"".join(body)}
  </g>
</svg>
'''


def main() -> int:
    if not SRC.exists():
        print(f"!! missing {SRC.relative_to(ROOT)} — run prep_photo.py first")
        return 1
    rows = image_to_rows(Image.open(SRC))
    OUT.write_text(build(rows))
    print(f"✓ {OUT.relative_to(ROOT)}  ({COLS}×{len(rows)} grid)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
