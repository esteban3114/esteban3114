#!/usr/bin/env python3
"""Hand-author a neofetch-style info card SVG (info-card.svg).

A terminal window chrome + a `user@host` header + colored key/value rows +
the classic neofetch color-block footer. Each line fades and slides in on a
short stagger so the panel looks like it's printing next to the portrait.
Set STATIC=1 to emit a frozen frame (handy for local Quick Look previews).

Everything here is easy to edit: change HEADER / TAGLINE / ROWS below.
"""
from __future__ import annotations

import html
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

# ─────────────────────────── EDIT ME ───────────────────────────
HEADER = "esteban3114@github"
TAGLINE = "builder · self-hoster · CPGE"
# (key, value, key-color)
ROWS = [
    ("Now",        "hq-bot · student-os",              "#39d353"),
    ("Stack",      "Python · SvelteKit · TypeScript",  "#58a6ff"),
    ("Infra",      "Docker · Supabase · GH Actions",   "#d2a8ff"),
    ("Focus",      "automation · self-hosting",        "#f0883e"),
    ("Highlights", "full-auto issue → PR → deploy",     "#ff7b72"),
    ("Contact",    "github.com/esteban3114",           "#79c0ff"),
]
# terminal ANSI-ish palette for the color-block footer
BLOCKS = ["#161b22", "#ff7b72", "#3fb950", "#d29922",
          "#58a6ff", "#bc8cff", "#39c5cf", "#e6edf3"]
# ────────────────────────────────────────────────────────────────

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
PAD = 22
LINE_H = 26
KEY_W = 108          # px reserved for the key column
CHROME_H = 34        # title bar height


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def build() -> str:
    key_col = max(len(k) for k, _, _ in ROWS)
    width = 470
    header_y = CHROME_H + PAD + 4
    tag_y = header_y + 18
    rule_y = tag_y + 12
    rows_top = rule_y + 24
    rows_h = len(ROWS) * LINE_H
    blocks_y = rows_top + rows_h + 6
    height = blocks_y + 34

    def anim(idx: int) -> str:
        if STATIC:
            return ""
        return f' style="animation-delay:{idx * 0.11:.2f}s"'

    parts: list[str] = []

    # window chrome
    parts.append(f'<rect class="bg" x="0.5" y="0.5" width="{width - 1}" '
                 f'height="{height - 1}" rx="12"/>')
    parts.append(f'<path class="bar" d="M0.5 12.5 A12 12 0 0 1 12.5 0.5 '
                 f'L{width - 12.5} 0.5 A12 12 0 0 1 {width - 0.5} 12.5 '
                 f'L{width - 0.5} {CHROME_H} L0.5 {CHROME_H} Z"/>')
    for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{20 + i * 20}" cy="{CHROME_H / 2}" r="6" fill="{c}"/>')
    parts.append(f'<text x="{width / 2}" y="{CHROME_H / 2 + 4}" '
                 f'class="chrome" text-anchor="middle">— neofetch —</text>')

    # header + tagline + rule
    parts.append(f'<g class="row"{anim(0)}>'
                 f'<text x="{PAD}" y="{header_y}" class="head">{esc(HEADER)}</text></g>')
    parts.append(f'<g class="row"{anim(1)}>'
                 f'<text x="{PAD}" y="{tag_y}" class="tag">{esc(TAGLINE)}</text></g>')
    rule = "-" * (key_col + 34)
    parts.append(f'<g class="row"{anim(2)}>'
                 f'<text x="{PAD}" y="{rule_y}" class="rule">{rule}</text></g>')

    # key/value rows
    for i, (k, v, kc) in enumerate(ROWS):
        y = rows_top + i * LINE_H
        parts.append(
            f'<g class="row"{anim(i + 3)}>'
            f'<text x="{PAD}" y="{y}" class="key" fill="{kc}">{esc(k)}</text>'
            f'<text x="{PAD + KEY_W}" y="{y}" class="val">{esc(v)}</text>'
            f'</g>'
        )

    # neofetch color-block footer (two rows of 8)
    bw = 18
    for r in range(2):
        for i, c in enumerate(BLOCKS):
            bx = PAD + i * bw
            by = blocks_y + r * 12
            fill = c if r == 0 else _dim(c)
            parts.append(f'<g class="row"{anim(len(ROWS) + 3 + r)}>'
                         f'<rect x="{bx}" y="{by}" width="{bw - 3}" height="9" '
                         f'rx="1.5" fill="{fill}"/></g>')

    anim_css = "" if STATIC else (
        ".row{opacity:0;transform:translateX(-8px);"
        "animation:slidein .45s ease-out forwards}"
        "@keyframes slidein{to{opacity:1;transform:none}}"
        "@media (prefers-reduced-motion:reduce){"
        ".row{opacity:1;transform:none;animation:none}}"
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" font-family="{FONT}" role="img"
     aria-label="{esc(HEADER)} info card">
  <style>
    .bg {{ fill: none; stroke: #30363d; stroke-width: 1; }}
    .bar {{ fill: #161b22; }}
    .chrome {{ fill: #6e7681; font-size: 11px; letter-spacing: .5px; }}
    .head {{ fill: #e6edf3; font-size: 16px; font-weight: 700; }}
    .tag  {{ fill: #7d8590; font-size: 12px; }}
    .rule {{ fill: #30363d; font-size: 13px; }}
    .key  {{ font-size: 13px; font-weight: 600; }}
    .val  {{ fill: #c9d1d9; font-size: 13px; }}
    {anim_css}
  </style>
  {"".join(parts)}
</svg>
'''


def _dim(hexc: str) -> str:
    """Return a darker variant of a #rrggbb color for the second block row."""
    h = hexc.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (int(c * 0.55) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def main() -> int:
    OUT.write_text(build())
    print(f"✓ {OUT.relative_to(ROOT)}{' (static)' if STATIC else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
