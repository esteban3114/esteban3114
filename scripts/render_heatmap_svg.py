#!/usr/bin/env python3
"""Render data/contributions.json as an animated 53×7 contribution heatmap SVG.

Rounded, colored day boxes reveal once on a diagonal slide-in (CSS keyframes
that play on load then freeze — no looping), with a Less→More legend and a
one-line stats footer. All motion is self-contained so GitHub renders it from
an <img>. Output: contrib-heatmap.svg
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

# none -> brightest (level 5 is a neon top end reserved for peak days)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 11          # box size
GAP = 3            # gap between boxes
PITCH = CELL + GAP # 14
PAD_L = 30         # left gutter for weekday labels
PAD_T = 24         # top gutter for month labels
PAD_R = 16
GRID_BOTTOM_GAP = 26  # space under grid for legend/footer
STEP = 0.035       # seconds of stagger per diagonal
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


def gh_weekday(d: date) -> int:
    """Sunday=0 .. Saturday=6 (GitHub's row order)."""
    return (d.weekday() + 1) % 7


def color_for(day: dict, best: int) -> str:
    lvl = int(day["level"])
    if best > 0 and day["count"] >= best and lvl >= 4:
        return PALETTE[5]
    return PALETTE[max(0, min(lvl, 4))]


def build() -> str:
    data = json.loads(DATA.read_text())
    days = data["days"]
    best = data.get("best_day", {}).get("count", 0)
    total = data.get("total", 0)
    current = data.get("current_streak", 0)
    longest = data.get("longest_streak", 0)

    start = date.fromisoformat(days[0]["date"])
    start_sunday = start - timedelta(days=gh_weekday(start))
    n_cols = (date.fromisoformat(days[-1]["date"]) - start_sunday).days // 7 + 1

    grid_w = n_cols * PITCH - GAP
    grid_h = 7 * PITCH - GAP
    width = PAD_L + grid_w + PAD_R
    height = PAD_T + grid_h + GRID_BOTTOM_GAP

    rects: list[str] = []
    month_labels: list[str] = []
    seen_month: set[str] = set()

    for day in days:
        d = date.fromisoformat(day["date"])
        col = (d - start_sunday).days // 7
        row = gh_weekday(d)
        x = PAD_L + col * PITCH
        y = PAD_T + row * PITCH
        # left-to-right sweep with a slight vertical cascade (per-cell delay),
        # exactly like the reference profile's heatmap reveal
        delay = col * 0.06 + row * 0.035
        cls = "c g" if day["count"] > 0 else "c"   # 'g' cells also flash
        fill = color_for(day, best)
        rects.append(
            f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" '
            f'height="{CELL}" rx="2.5" fill="{fill}" '
            f'style="animation-delay:{delay:.3f}s"><title>'
            f'{day["count"]} on {day["date"]}</title></rect>'
        )
        # month label at the column where a new month first appears (top row-ish)
        ym = day["date"][:7]
        if ym not in seen_month and row <= 1:
            seen_month.add(ym)
            mx = PAD_L + col * PITCH
            month_labels.append(
                f'<text x="{mx}" y="{PAD_T - 8}" class="mlabel">'
                f'{MONTHS[d.month - 1]}</text>'
            )

    # weekday labels: Mon / Wed / Fri (rows 1, 3, 5)
    wlabels = []
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        wy = PAD_T + row * PITCH + CELL - 2
        wlabels.append(f'<text x="0" y="{wy}" class="wlabel">{name}</text>')

    # legend (bottom-right)
    legend_y = PAD_T + grid_h + 16
    legend_x = width - PAD_R - (5 * (CELL + 3)) - 70
    legend = [f'<text x="{legend_x - 6}" y="{legend_y + CELL - 2}" '
              f'class="legend" text-anchor="end">Less</text>']
    for i in range(5):
        lx = legend_x + i * (CELL + 3)
        legend.append(f'<rect x="{lx}" y="{legend_y}" width="{CELL}" '
                      f'height="{CELL}" rx="2.5" fill="{PALETTE[i]}"/>')
    legend.append(f'<text x="{legend_x + 5 * (CELL + 3) + 4}" '
                  f'y="{legend_y + CELL - 2}" class="legend">More</text>')

    # footer stat (bottom-left)
    footer = (
        f'<text x="{PAD_L}" y="{legend_y + CELL - 2}" class="foot">'
        f'<tspan class="num">{total:,}</tspan> contributions in the last year'
        f'<tspan class="dim">  ·  streak {current}d · longest {longest}d</tspan>'
        f'</text>'
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" font-family="{FONT}" role="img"
     aria-label="{total} contributions in the last year">
  <style>
    .bg {{ fill: #0d1117; stroke: #21262d; stroke-width: 1; }}
    .c {{ transform-box: fill-box; transform-origin: center; opacity: 0;
          animation: pop .55s ease-out both; }}
    .g {{ animation: pop .55s ease-out both, flash .7s ease-out both; }}
    @keyframes pop {{
      0%   {{ opacity: 0; transform: scale(.2); }}
      60%  {{ opacity: 1; transform: scale(1.1); }}
      100% {{ opacity: 1; transform: scale(1); }}
    }}
    @keyframes flash {{
      0%   {{ filter: brightness(2.4); }}
      45%  {{ filter: brightness(2.4); }}
      100% {{ filter: brightness(1); }}
    }}
    .mlabel, .wlabel, .legend {{ fill: #7d8590; font-size: 10px; }}
    .foot {{ fill: #7d8590; font-size: 12px; }}
    .foot .num {{ fill: #e6edf3; font-weight: 700; }}
    .foot .dim {{ fill: #57606a; }}
    @media (prefers-reduced-motion: reduce) {{
      .c {{ opacity: 1 !important; animation: none !important; }}
    }}
  </style>
  <rect class="bg" x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10"/>
  {"".join(month_labels)}
  {"".join(wlabels)}
  {"".join(rects)}
  {"".join(legend)}
  {footer}
</svg>
'''
    return svg


def main() -> int:
    OUT.write_text(build())
    print(f"✓ {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
