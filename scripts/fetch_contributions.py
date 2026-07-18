#!/usr/bin/env python3
"""Scrape the public GitHub contributions calendar — no token, no GraphQL.

GitHub serves everyone's contribution calendar as a plain HTML fragment at
https://github.com/users/<username>/contributions (the same one the profile
page embeds). We fetch it, read each day cell's date/level/count, and write
data/contributions.json with the raw days plus a few derived stats.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME", "esteban3114")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"

URL = f"https://github.com/users/{USERNAME}/contributions"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (profile-art bot; +https://github.com/{})".format(USERNAME),
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "text/html",
}


def parse_count(text: str) -> int:
    """'3 contributions on July 1st.' -> 3 ; 'No contributions...' -> 0."""
    if not text:
        return 0
    text = text.strip()
    if text.lower().startswith("no "):
        return 0
    m = re.search(r"([\d,]+)\s+contribution", text)
    return int(m.group(1).replace(",", "")) if m else 0


def fetch_html() -> str:
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    # Counts sometimes live in <tool-tip for="<cell id>"> siblings; index them.
    tips: dict[str, str] = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        if target:
            tips[target] = tip.get_text(" ", strip=True)

    days: list[dict] = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        d = td.get("data-date")
        if not d:
            continue
        level = int(td.get("data-level", 0) or 0)

        # Count: from the linked tool-tip, else from an inner sr-only span.
        text = ""
        cid = td.get("id")
        if cid and cid in tips:
            text = tips[cid]
        if not text:
            span = td.find("span", class_="sr-only")
            if span:
                text = span.get_text(" ", strip=True)
        if not text:
            text = td.get("aria-label", "") or td.get_text(" ", strip=True)

        days.append({"date": d, "count": parse_count(text), "level": level})

    days.sort(key=lambda x: x["date"])
    return days


def derive_stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)

    # Longest streak: max run of consecutive days with any contribution.
    longest = run = 0
    for d in days:
        if d["count"] > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0

    # Current streak: trailing run of >0 days (a 0 only today doesn't break it).
    current = 0
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        elif d is days[-1]:
            continue  # today may legitimately be empty
        else:
            break

    best = max(days, key=lambda x: x["count"], default={"date": "", "count": 0})

    monthly: dict[str, int] = defaultdict(int)
    for d in days:
        monthly[d["date"][:7]] += d["count"]

    active = sum(1 for d in days if d["count"] > 0)

    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_days": active,
        "monthly": dict(sorted(monthly.items())),
    }


def main() -> int:
    print(f"→ fetching {URL}")
    try:
        html = fetch_html()
    except requests.RequestException as e:
        print(f"!! fetch failed: {e}", file=sys.stderr)
        return 1

    days = parse_days(html)
    if not days:
        print("!! no day cells parsed — GitHub markup may have changed", file=sys.stderr)
        return 2

    stats = derive_stats(days)
    payload = {
        "username": USERNAME,
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "start": days[0]["date"],
        "end": days[-1]["date"],
        "weeks": (date.fromisoformat(days[-1]["date"]) - date.fromisoformat(days[0]["date"])).days // 7 + 1,
        "days": days,
        **stats,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    print(
        f"✓ {OUT.relative_to(ROOT)} — {len(days)} days, "
        f"{stats['total']:,} contributions, "
        f"streak {stats['current_streak']} (longest {stats['longest_streak']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
