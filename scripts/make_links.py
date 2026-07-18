#!/usr/bin/env python3
"""Generate on-brand terminal-style link badges (links/*.svg) + the README row.

Each badge is a self-contained dark "pill" (matching info-card.svg): a drawn
icon in a brand color + a monospace label, faded/slid in on a short stagger.
No third-party badge service. Badges are decorative <img>; the click target is
the <a href> in the README, which this script also prints for pasting.

Output: links/<slug>.svg  (one per entry) + a README snippet on stdout.
"""
from __future__ import annotations

import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "links"

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
H = 30                 # badge height
FS = 12.5              # label font-size
CHAR_W = 7.35          # monospace advance at FS (forced via textLength)
IX = 12                # icon left inset
ICON = 16              # icon box
GAP = 8                # icon → label gap
PAD_R = 13             # right padding

# slug, label, url, brand color, icon key
LINKS = [
    ("website",   "este-dls.com",       "https://este-dls.com",                                    "#39d353", "globe"),
    ("x",         "@este_krs",          "https://x.com/este_krs",                                  "#e6edf3", "x"),
    ("instagram", "@este.dls",          "https://instagram.com/este.dls",                          "#e1306c", "instagram"),
    ("linkedin",  "Esteban de la Sala", "https://fr.linkedin.com/in/esteban-de-la-sala-5732123b1", "#58a6ff", "linkedin"),
    ("email",     "email",              "mailto:este3112008@gmail.com",                            "#f0883e", "mail"),
]


def icon(kind: str, x: float, cy: float, c: str) -> str:
    """Return SVG for a 16px icon whose box starts at x, vertically at cy."""
    cx = x + ICON / 2
    if kind == "globe":
        return (f'<circle cx="{cx}" cy="{cy}" r="7" fill="none" stroke="{c}" stroke-width="1.4"/>'
                f'<ellipse cx="{cx}" cy="{cy}" rx="3" ry="7" fill="none" stroke="{c}" stroke-width="1.2"/>'
                f'<line x1="{x+1}" y1="{cy}" x2="{x+15}" y2="{cy}" stroke="{c}" stroke-width="1.2"/>')
    if kind == "x":
        return (f'<path d="M{x+2.5} {cy-6.5} L{x+13.5} {cy+6.5} M{x+13.5} {cy-6.5} L{x+2.5} {cy+6.5}" '
                f'stroke="{c}" stroke-width="2" stroke-linecap="round"/>')
    if kind == "instagram":
        return (f'<rect x="{x+1}" y="{cy-7}" width="14" height="14" rx="4.5" fill="none" stroke="{c}" stroke-width="1.4"/>'
                f'<circle cx="{cx}" cy="{cy}" r="3.4" fill="none" stroke="{c}" stroke-width="1.4"/>'
                f'<circle cx="{x+11.6}" cy="{cy-3.6}" r="1.1" fill="{c}"/>')
    if kind == "linkedin":
        return (f'<rect x="{x+1}" y="{cy-7}" width="14" height="14" rx="3" fill="{c}"/>'
                f'<text x="{cx}" y="{cy+3.3}" font-size="9" font-weight="700" fill="#0d1117" '
                f'text-anchor="middle" font-family="{FONT}">in</text>')
    if kind == "mail":
        return (f'<rect x="{x+1}" y="{cy-5.5}" width="14" height="11" rx="2" fill="none" stroke="{c}" stroke-width="1.4"/>'
                f'<path d="M{x+1.6} {cy-4.6} L{cx} {cy+1.2} L{x+14.4} {cy-4.6}" fill="none" stroke="{c}" stroke-width="1.4"/>')
    return ""


def badge_svg(label: str, color: str, kind: str, delay: float) -> str:
    text_w = len(label) * CHAR_W
    width = round(IX + ICON + GAP + text_w + PAD_R)
    cy = H / 2
    tx = IX + ICON + GAP
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{H}"
     viewBox="0 0 {width} {H}" font-family="{FONT}" role="img" aria-label="{html.escape(label)}">
  <style>
    .b {{ opacity: 0; animation: pop .5s ease-out forwards; animation-delay: {delay:.2f}s; }}
    @keyframes pop {{ from {{ opacity: 0; transform: translateY(4px); }} to {{ opacity: 1; transform: none; }} }}
    @media (prefers-reduced-motion: reduce) {{ .b {{ opacity: 1; animation: none; }} }}
  </style>
  <g class="b">
    <rect x="0.5" y="0.5" width="{width-1}" height="{H-1}" rx="8" fill="#161b22" stroke="#30363d"/>
    {icon(kind, IX, cy, color)}
    <text x="{tx}" y="{cy+4.2}" textLength="{text_w:.1f}" lengthAdjust="spacing"
          font-size="{FS}" fill="#c9d1d9">{html.escape(label)}</text>
  </g>
</svg>
'''


def main() -> int:
    OUTDIR.mkdir(exist_ok=True)
    lines = []
    for i, (slug, label, url, color, kind) in enumerate(LINKS):
        (OUTDIR / f"{slug}.svg").write_text(badge_svg(label, color, kind, i * 0.12))
        lines.append(f'<a href="{url}"><img src="./links/{slug}.svg" height="{H}" alt="{html.escape(label)}" /></a>')
    print(f"✓ {len(LINKS)} badges -> {OUTDIR.relative_to(ROOT)}/")
    print("\n--- README snippet ---")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
