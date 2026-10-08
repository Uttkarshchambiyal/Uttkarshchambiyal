#!/usr/bin/env python3
"""Render GitHub's public contribution calendar as a README-safe animated SVG.

No credentials or third-party Python packages are required. If GitHub changes
its calendar markup, fail before replacing the last good image.
"""

import argparse
import datetime as dt
import html
from html.parser import HTMLParser
import math
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.tooltips = {}
        self.tooltip_id = None
        self.text = []
        self.in_heading = False
        self.heading = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('data-date'):
            self.cells[attrs['id']] = {
                'date': attrs['data-date'], 'level': int(attrs['data-level'])
            }
        if tag == 'tool-tip' and attrs.get('for'):
            self.tooltip_id = attrs['for']
            self.text = []
        if attrs.get('id') == 'js-contribution-activity-description':
            self.in_heading = True

    def handle_data(self, text):
        if self.tooltip_id:
            self.text.append(text)
        if self.in_heading:
            self.heading.append(text)

    def handle_endtag(self, tag):
        if tag == 'tool-tip' and self.tooltip_id:
            self.tooltips[self.tooltip_id] = ''.join(self.text).strip()
            self.tooltip_id = None
        if tag == 'h2':
            self.in_heading = False

    def days(self):
        days = []
        for identifier, cell in self.cells.items():
            label = self.tooltips.get(identifier, '')
            match = re.match(r'(No|[\d,]+) contributions? on ', label)
            if not match:
                raise ValueError(f'Missing or invalid contribution count: {cell["date"]}')
            count = 0 if match[1] == 'No' else int(match[1].replace(',', ''))
            if not 0 <= cell['level'] <= 4 or (count == 0) != (cell['level'] == 0):
                raise ValueError('Contribution level does not match count')
            days.append({**cell, 'count': count})
        days.sort(key=lambda day: day['date'])
        if not 365 <= len(days) <= 371:
            raise ValueError(f'Expected a full year, received {len(days)} days')
        dates = [dt.date.fromisoformat(day['date']) for day in days]
        if len(set(dates)) != len(dates) or any(
            b - a != dt.timedelta(days=1) for a, b in zip(dates, dates[1:])
        ):
            raise ValueError('Contribution calendar has missing or duplicate dates')
        heading = re.search(r'([\d,]+)\s+contributions?\s+in the last year', ''.join(self.heading))
        if not heading or sum(day['count'] for day in days) != int(heading[1].replace(',', '')):
            raise ValueError('Daily contribution sum differs from the GitHub calendar total')
        return days


def statistics(days):
    run = longest = 0
    for day in days:
        run = run + 1 if day['count'] else 0
        longest = max(longest, run)
    current = 0
    tail = days if days[-1]['count'] else days[:-1]
    for day in reversed(tail):
        if not day['count']:
            break
        current += 1
    return sum(day['count'] for day in days), max(day['count'] for day in days), longest, current


def render(days, username):
    total, busiest, longest, current = statistics(days)
    maximum = max(1, busiest)
    start = dt.date.fromisoformat(days[0]['date'])
    week_offset = (start.weekday() + 1) % 7
    cells = []
    for i, day in enumerate(days):
        week, weekday = divmod(i + week_offset, 7)
        height = 0.4 + (day['count'] / maximum) ** 0.85 * 7.2 if day['count'] else 0.2
        cells.append({**day, 'week': week, 'weekday': weekday, 'height': height})

    def world(cell, z):
        x, y = cell['week'], cell['weekday']
        return [(x, y, z), (x + .78, y, z), (x + .78, y + .78, z), (x, y + .78, z)]

    def project(point, flat=False):
        x, y, z = point
        if flat:
            return x, y
        yaw, elev = math.pi / 4, math.radians(34)
        return x * math.cos(yaw) - y * math.sin(yaw), (x * math.sin(yaw) + y * math.cos(yaw)) * math.sin(elev) - z * math.cos(elev)

    # Fit the whole skyline, including its highest bar, inside the scene.
    points = [project(point) for cell in cells for z in (0, cell['height']) for point in world(cell, z)]
    min_x, max_x = min(p[0] for p in points), max(p[0] for p in points)
    min_y, max_y = min(p[1] for p in points), max(p[1] for p in points)
    scale = min(900 / (max_x - min_x), 350 / (max_y - min_y))
    ox = 500 - (min_x + max_x) * scale / 2
    oy = 385 - (min_y + max_y) * scale / 2
    weeks = cells[-1]['week'] + 1
    flat_scale = 900 / weeks

    def screen(points, flat=False):
        out = []
        for p in points:
            x, y = project(p, flat)
            out.append((50 + x * flat_scale, 315 + y * flat_scale) if flat else (ox + x * scale, oy + y * scale))
        return ' '.join(f'{x:.2f},{y:.2f}' for x, y in out)

    colors = ['#202936', '#164b31', '#177e45', '#27b85c', '#61e889']

    def shade(color, factor):
        values = [min(255, round(int(color[i:i + 2], 16) * factor)) for i in (1, 3, 5)]
        return '#' + ''.join(f'{value:02x}' for value in values)

    animated, still = [], []
    # Painter's order: furthest bars first, so taller near bars occlude correctly.
    for cell in sorted(cells, key=lambda c: (c['week'] + c['weekday'], c['week'])):
        top, bottom = world(cell, cell['height']), world(cell, 0)
        faces = [( [bottom[1], bottom[2], top[2], top[1]], .62),
                 ( [bottom[2], bottom[3], top[3], top[2]], .82),
                 (top, 1)]
        title = html.escape(f'{cell["date"]}: {cell["count"]:,} contributions')
        for face, factor in faces:
            iso, flat = screen(face), screen(face, True)
            fill = shade(colors[cell['level']], factor)
            polygon = f'<polygon points="{iso}" fill="{fill}" stroke="#0d1721" stroke-width="0.55" stroke-linejoin="round">'
            still.append(f'{polygon}<title>{title}</title></polygon>')
            # One scene folds between a heat map and the skyline. Each week's
            # transition begins slightly later, giving the original rising wave.
            delay = cell['week'] / max(1, weeks - 1) * .12
            keys = f'0;{.08 + delay:.3f};{.34 + delay:.3f};.80;1'
            animated.append(
                f'{polygon}<title>{title}</title>'
                f'<animate attributeName="points" values="{flat};{flat};{iso};{iso};{flat}" '
                f'keyTimes="{keys}" dur="12s" repeatCount="indefinite" '
                'calcMode="spline" keySplines="0 0 1 1;0.4 0 0.2 1;0 0 1 1;0.4 0 0.2 1"/></polygon>'
            )

    fmt_date = lambda date: dt.date.fromisoformat(date).strftime('%d %b %Y')
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 1000 650" role="img" aria-labelledby="title description">',
        f'<title id="title">{html.escape(username)} contribution skyline</title>',
        f'<desc id="description">{total:,} GitHub contributions from {days[0]["date"]} to {days[-1]["date"]}. '
        f'Busiest day: {busiest}. Longest streak: {longest} days. Current streak: {current} days. '
        'A contribution heat map rises into a 3D skyline. Counts come from the public GitHub profile.</desc>',
        '<defs><linearGradient id="background" x2="1" y2="1"><stop stop-color="#111b29"/><stop offset="1" stop-color="#090e16"/></linearGradient></defs>',
        '<style>text{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif}.still{display:none}@media(prefers-reduced-motion:reduce){.motion{display:none}.still{display:inline}}</style>',
        '<rect x=".5" y=".5" width="999" height="649" rx="20" fill="url(#background)" stroke="#293343"/>',
        '<text x="40" y="47" fill="#7ee5a0" font-size="12" letter-spacing="3">A YEAR OF BUILDING</text>',
        '<text x="40" y="83" fill="#eff4fa" font-size="27" font-weight="650">Contribution Skyline</text>',
        f'<text x="960" y="78" text-anchor="end" fill="#98a7b8" font-size="14">@{html.escape(username)}</text>',
    ]
    for x, label, value, suffix in [
        (40, 'YEAR TOTAL', total, 'contributions'), (285, 'BUSIEST DAY', busiest, 'contributions'),
        (530, 'LONGEST STREAK', longest, 'days'), (775, 'CURRENT STREAK', current, 'days')
    ]:
        svg.extend([
            f'<rect x="{x}" y="109" width="185" height="85" rx="10" fill="#121e2c" stroke="#243343"/>',
            f'<text x="{x + 16}" y="133" fill="#91a3b7" font-size="10" letter-spacing="1.2">{label}</text>',
            f'<text x="{x + 16}" y="167" fill="#8ce9ad" font-size="29" font-weight="650">{value:,}</text>',
            f'<text x="{x + 16}" y="183" fill="#91a3b7" font-size="10">{suffix}</text>',
        ])
    svg.append('<g class="still">' + ''.join(still) + '</g>')
    svg.append('<g class="motion">' + ''.join(animated) + '</g>')
    svg.extend([
        '<path d="M40 578H960" stroke="#243343"/>',
        f'<text x="40" y="603" fill="#a4b3c4" font-size="12">{fmt_date(days[0]["date"])} — {fmt_date(days[-1]["date"])}</text>',
        '<text x="40" y="625" fill="#7e8d9e" font-size="11">Real GitHub activity · refreshed every 6 hours</text>',
        '<text x="805" y="610" fill="#a4b3c4" font-size="11">Less</text>',
    ])
    for i, color in enumerate(colors):
        svg.append(f'<rect x="{837 + i * 17}" y="599" width="12" height="12" rx="2" fill="{color}"/>')
    svg.extend(['<text x="929" y="610" fill="#a4b3c4" font-size="11">More</text>', '</svg>'])
    return '\n'.join(svg) + '\n'


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--username', default='Uttkarshchambiyal')
    cli.add_argument('--html', type=Path, help='Use a previously downloaded GitHub calendar')
    cli.add_argument('--output', type=Path, default=Path('assets/contribution-skyline.svg'))
    args = cli.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}', args.username):
        raise ValueError('Invalid GitHub username')
    if args.html:
        source = args.html.read_text()
    else:
        source = subprocess.run(
            ['curl', '--fail', '--silent', '--show-error', '--location', '--retry', '3', '--max-time', '45',
             f'https://github.com/users/{args.username}/contributions'],
            check=True, capture_output=True, text=True,
        ).stdout
    parser = CalendarParser()
    parser.feed(source)
    days = parser.days()
    if not args.html and abs((dt.datetime.now(dt.timezone.utc).date() - dt.date.fromisoformat(days[-1]['date'])).days) > 1:
        raise ValueError('GitHub returned a stale contribution calendar')
    svg = render(days, args.username)
    ET.fromstring(svg)  # Reject invalid SVG before overwriting the published asset.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix('.tmp')
    temporary.write_text(svg)
    temporary.replace(args.output)
    total, busiest, longest, current = statistics(days)
    print(f'{len(days)} days | {total:,} contributions | busiest {busiest} | longest {longest} | current {current}')
    print(f'Saved {args.output}')


if __name__ == '__main__':
    main()
