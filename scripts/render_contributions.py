"""Render an animated skyline from GitHub's publicly visible contribution calendar.

Standard library only. The public HTML calendar is fetched without authentication.
If GitHub changes its markup or any day cannot be parsed, fail before writing output.
"""

import argparse
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
import json
from math import log1p
from pathlib import Path
import re
from urllib.request import Request, urlopen

from update_project_feed import OWNER


@dataclass(frozen=True)
class Day:
    date: str
    count: int
    level: int


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.tooltips = {}
        self.current_tooltip = None
        self.tooltip_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-date" in attrs and "data-level" in attrs:
            identity = attrs["id"]
            if identity in self.cells:
                raise ValueError("Duplicate contribution calendar cell")
            self.cells[identity] = (attrs["data-date"], int(attrs["data-level"]))
        if tag == "tool-tip":
            self.current_tooltip = attrs.get("for")
            self.tooltip_text = []

    def handle_data(self, data):
        if self.current_tooltip is not None:
            self.tooltip_text.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.current_tooltip is not None:
            self.tooltips[self.current_tooltip] = " ".join(self.tooltip_text).strip()
            self.current_tooltip = None


def parse_calendar(html, start, end):
    parser = CalendarParser()
    parser.feed(html)
    days = {}
    for identity, (when, level) in parser.cells.items():
        parsed_date = date.fromisoformat(when)
        if not start <= parsed_date <= end:
            continue
        text = parser.tooltips.get(identity, "")
        match = re.match(r"(No|[0-9][0-9,]*) contributions? on\b", text)
        if not match or not 0 <= level <= 4 or when in days:
            raise ValueError(f"Unrecognized contribution data for {when}")
        count = 0 if match[1] == "No" else int(match[1].replace(",", ""))
        if (count == 0) != (level == 0):
            raise ValueError(f"Inconsistent contribution count and level for {when}")
        days[when] = Day(when, count, level)
    expected = {(start + timedelta(days=offset)).isoformat()
                for offset in range((end - start).days + 1)}
    if set(days) != expected:
        raise ValueError("GitHub's calendar is missing dates; keeping the previous published skyline")
    return [days[when] for when in sorted(days)]


def fetch_calendar(start, end):
    # The default calendar spans the rolling year. Date query parameters select
    # a calendar year on GitHub and can omit the previous November/December.
    url = f"https://github.com/users/{OWNER}/contributions"
    request = Request(url, headers={"User-Agent": "Hudson-Forge-Profile-Updates",
                                    "Accept": "text/html", "Accept-Language": "en-US"})
    with urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8")
    return parse_calendar(html, start, end), url


def points(vertices):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in vertices)


def render_skyline(days, refreshed, animated):
    start, end = date.fromisoformat(days[0].date), date.fromisoformat(days[-1].date)
    sunday = start - timedelta(days=(start.weekday() + 1) % 7)
    total = sum(day.count for day in days)
    active = sum(day.count > 0 for day in days)
    maximum = max(day.count for day in days)
    palette = ("#172738", "#734936", "#af7047", "#df9a63", "#ffd5a3")
    bars = []
    months = []
    for day in days:
        when = date.fromisoformat(day.date)
        week, weekday = divmod((when - sunday).days, 7)
        x, y = 34 + week * 11.6 + weekday * 8.8, 365 - week * 2.7 + weekday * 5.1
        height = 1 if day.count == 0 else 5 + 66 * log1p(day.count) / log1p(maximum)
        base = [(x, y), (x + 10.2, y - 2.4), (x + 18, y + 2.1), (x + 7.8, y + 4.5)]
        roof = [(px, py - height) for px, py in base]
        left = [base[0], base[3], roof[3], roof[0]]
        right = [base[3], base[2], roof[2], roof[3]]
        light = (f'<polygon class="glow" style="animation-delay:{-week * .13:.2f}s" '
                 f'points="{points(roof)}" fill="#fff0d2" opacity="0"/>') if animated and day.count else ""
        label = escape(f"{day.date}: {day.count} contributions")
        bar = (f'<g><title>{label}</title>'
               f'<polygon points="{points(left)}" fill="{palette[day.level]}"/>'
               f'<polygon points="{points(left)}" fill="#040b14" opacity=".30"/>'
               f'<polygon points="{points(right)}" fill="{palette[day.level]}"/>'
               f'<polygon points="{points(right)}" fill="#040b14" opacity=".57"/>'
               f'<polygon points="{points(roof)}" fill="{palette[day.level]}"/>{light}</g>')
        bars.append((y, x, bar))
        if when.day == 1:
            mx, my = 34 + week * 11.6 + 7 * 8.8, 365 - week * 2.7 + 7 * 5.1 + 15
            months.append(f'<text x="{mx:.1f}" y="{my:.1f}" fill="#a8bacb" font-size="11" '
                          f'transform="rotate(-13 {mx:.1f} {my:.1f})">{when:%b}</text>')
    motion = """<style>
      @keyframes forge-wave { 0%,65%,100% { opacity:0 } 73% { opacity:.8 } 82% { opacity:0 } }
      .glow { animation:forge-wave 12s ease-in-out infinite }
      @media (prefers-reduced-motion:reduce) { .glow { animation:none;opacity:0 } }
    </style>""" if animated else ""
    legend = "".join(f'<rect x="{618 + i * 18}" y="422" width="13" height="9" rx="2" fill="{color}"/>'
                     for i, color in enumerate(palette))
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="760" height="460" viewBox="0 0 760 460" '
        'font-family="system-ui,sans-serif">\n'
        '<title>Hudson Forge contribution skyline</title>\n'
        f'<desc>{total:,} contributions on {active} active days from {start} to {end}. '
        'One building per day; height uses a logarithmic scale. Copper light moves across the roofs.</desc>\n'
        f'{motion}\n'
        '<defs><radialGradient id="halo"><stop stop-color="#76482e" stop-opacity=".3"/>'
        '<stop offset="1" stop-color="#0b1420" stop-opacity="0"/></radialGradient></defs>\n'
        '<rect x="1" y="1" width="758" height="458" rx="16" fill="#0b1420" stroke="#405366"/>\n'
        '<ellipse cx="475" cy="275" rx="310" ry="155" fill="url(#halo)"/>\n'
        '<text x="28" y="34" fill="#edb483" font-size="14" letter-spacing="2">BUILT DAY BY DAY</text>\n'
        '<text x="28" y="73" fill="#eef3f7" font-size="30" font-weight="700">The contribution skyline</text>\n'
        f'<text x="28" y="108" fill="#edb483" font-size="22" font-weight="700">{total:,}</text>\n'
        f'<text x="109" y="108" fill="#bdc9d4" font-size="15">contributions · {active} active days · past {len(days)} days</text>\n'
        '<path d="M28 128 H732" stroke="#304152"/>\n'
        + "\n".join(bar for _, _, bar in sorted(bars)) + "\n"
        + "\n".join(months) + "\n"
        + f'<text x="28" y="432" fill="#bdc9d4" font-size="12">{start:%b %d, %Y} – {end:%b %d, %Y} · refreshed {refreshed} UTC</text>\n'
        '<text x="574" y="431" fill="#bdc9d4" font-size="12">Less</text>'
        f'{legend}<text x="715" y="431" fill="#bdc9d4" font-size="12">More</text>\n'
        '</svg>\n'
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=364)
    days, source = fetch_calendar(start, end)
    outputs = {
        "contribution-skyline.svg": render_skyline(days, end, animated=True),
        "contribution-skyline-static.svg": render_skyline(days, end, animated=False),
        "contributions.json": json.dumps({"source": source, "refreshed_utc": str(end),
                                          "days": [asdict(day) for day in days]}, indent=2) + "\n",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        (args.output_dir / name).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
