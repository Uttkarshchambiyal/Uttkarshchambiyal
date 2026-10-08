#!/usr/bin/env python3
"""Render desktop and mobile README cards from Uttkarsh's profile details.

Adapted from the supplied dark feature-card reference. GitHub cannot run its
React state or click handlers, so focus cards rotate automatically. All SVG
icons are bundled from Lucide under the license in assets/licenses.
"""

from html import escape
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ICONS = json.loads((ROOT / "assets/whoami-icons.json").read_text())
FOCUS = [
    ("code-xml", "Frontend", "Interactive web experiences", "Building interfaces", "React, JavaScript, HTML & CSS"),
    ("cpu", "DSA", "Data structures & algorithms", "Thinking through problems", "C++ and Java · one problem at a time"),
    ("trophy", "Competitive coding", "Practice. Solve. Improve.", "Learning through practice", "LeetCode, Codeforces & GeeksforGeeks"),
    ("pen-tool", "UI / UX design", "Design with Figma", "Crafting thoughtful experiences", "Figma · clean layouts · smooth motion"),
]
DESCRIPTION = (
    "Uttkarsh Chambiyal, B.Tech CSE student, semester 3, based in Bengaluru, Karnataka, India. "
    "Focus: frontend development, data structures and algorithms, competitive programming, and UI/UX design with Figma. "
    "Currently learning React, Node.js, MongoDB, Spring Boot and SwiftUI; also exploring system design and AI/ML. "
    "Tools: Claude, Codex, IntelliJ IDEA, PyCharm and DataGrip. "
    "Open to internships, hackathons, freelance projects and open source. "
    "Hobbies: coding, video editing, Formula 1 and hackathons. The focus panel rotates automatically."
)


def render(mobile=False):
    width, height = (480, 1360) if mobile else (1000, 820)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
        '<title id="title">About Uttkarsh Chambiyal</title>',
        f'<desc id="description">{escape(DESCRIPTION)}</desc>',
        '<style>text{font-family:Inter,-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif;fill:#fafafa}.muted{fill:#a1a1aa}.eyebrow{fill:#b2b2bb;font-size:10px;font-weight:600;letter-spacing:1.6px}.code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12.5px}.still{display:none}@media(prefers-reduced-motion:reduce){.motion{display:none}.still{display:inline}}</style>',
        '<defs>',
    ]
    for name, content in ICONS.items():
        parts.append(f'<symbol id="icon-{name}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{content}</symbol>')
    parts += ['</defs>', f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="24" fill="#080808" stroke="#27272a"/>']

    def rect(x, y, w, h, fill="#0d0d0f", stroke="#27272a", radius=18, extra=""):
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" {extra}/>')

    def text(x, y, value, size=14, weight=400, cls="", extra=""):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" class="{cls}" {extra}>{escape(value)}</text>')

    def icon(name, x, y, size=21, color="#e4e4e7"):
        parts.append(f'<use href="#icon-{name}" x="{x}" y="{y}" width="{size}" height="{size}" color="{color}"/>')

    def active(index):
        values = ["1" if i % 4 == index else "0" for i in range(5)]
        return f'<animate attributeName="opacity" values="{";".join(values)}" keyTimes="0;.25;.5;.75;1" dur="20s" repeatCount="indefinite" calcMode="discrete"/>'

    inset = 24 if mobile else 32
    rect(inset, 30, 269, 30, "#18181b", "#3f3f46", 15)
    icon("sparkles", inset+12, 37, 16)
    text(inset+39, 50, "B.TECH CSE · SEMESTER 3", 10, 600, "muted", 'letter-spacing="1"')
    text(inset, 114 if not mobile else 109, "Uttkarsh Chambiyal", 48 if not mobile else 33, 650, extra='letter-spacing="-1.5"')
    text(inset, 150 if not mobile else 140, "Learning by building interactive experiences.", 18 if not mobile else 15, cls="muted")

    # The large focus card retains the reference's 2x2 selector and detail area.
    fx, fy, fw, fh = (24, 178, 432, 422) if mobile else (32, 184, 466, 434)
    rect(fx, fy, fw, fh)
    icon("sparkles", fx+24, fy+23, 17)
    text(fx+50, fy+36, "WHAT I FOCUS ON", 10, 600, "eyebrow")
    text(fx+24, fy+77, "Code. Create. Compete.", 27 if mobile else 29, 650, extra='letter-spacing="-.8"')
    text(fx+24, fy+103, "Four things that keep me building.", 14, cls="muted")
    tile_width = (fw-60)/2
    for i, (name, title, subtitle, detail, tags) in enumerate(FOCUS):
        tx, ty = fx+24+(i % 2)*(tile_width+12), fy+128+(i//2)*86
        rect(tx, ty, tile_width, 74, "#151518", "#29292e", 12)
        parts.append(f'<g class="motion" opacity="{1 if i == 0 else 0}">{active(i)}')
        rect(tx, ty, tile_width, 74, "#27272a", "#71717a", 12)
        parts.append('</g>')
        if i == 0:
            parts.append('<g class="still">')
            rect(tx, ty, tile_width, 74, "#27272a", "#71717a", 12)
            parts.append('</g>')
        icon(name, tx+13, ty+13, 19)
        text(tx+41, ty+28, title, 12.5 if mobile else 13, 600)
        text(tx+13, ty+56, subtitle, 10.5 if mobile else 11, cls="muted")
    dx, dy, dw = fx+24, fy+310, fw-48
    rect(dx, dy, dw, 99, "#18181b", "#3f3f46", 12)
    text(dx+16, dy+24, "IN FOCUS", 9, 600, "eyebrow")
    for i, (_, title, subtitle, detail, tags) in enumerate(FOCUS):
        parts.append(f'<g class="motion" opacity="{1 if i == 0 else 0}">{active(i)}')
        text(dx+16, dy+53, detail, 18 if mobile else 19, 600, extra='letter-spacing="-.4"')
        text(dx+16, dy+78, tags, 11 if mobile else 12, cls="muted")
        parts.append('</g>')
    parts.append('<g class="still">')
    text(dx+16, dy+53, FOCUS[0][3], 18 if mobile else 19, 600)
    text(dx+16, dy+78, FOCUS[0][4], 11 if mobile else 12, cls="muted")
    parts.append('</g>')

    # A place card and a learning card replace the reference's invented metrics.
    ix, iy, iw, ih = (24, 616, 208, 218) if mobile else (514, 184, 219, 220)
    lx, ly, lw, lh = (248, 616, 208, 218) if mobile else (749, 184, 219, 220)
    rect(ix, iy, iw, ih)
    rect(ix+20, iy+20, 37, 37, "#27272a", "#3f3f46", 10)
    icon("map-pin", ix+28, iy+28)
    text(ix+20, iy+90, "Based in", 17, 600)
    text(ix+20, iy+122, "Bengaluru", 24, 650, extra='letter-spacing="-.7"')
    text(ix+20, iy+147, "Karnataka, India", 13, cls="muted")
    rect(ix+20, iy+169, 111, 27, "#27272a", "#3f3f46", 7)
    text(ix+32, iy+187, "CSE STUDENT", 10, 600, "muted", 'letter-spacing=".7"')
    rect(lx, ly, lw, lh)
    rect(lx+20, ly+20, 37, 37, "#27272a", "#3f3f46", 10)
    icon("layers", lx+28, ly+28)
    text(lx+20, ly+87, "Currently learning", 16, 600)
    for j, line in enumerate(["React · Node.js", "MongoDB", "Spring Boot", "SwiftUI"]):
        rect(lx+20, ly+100+j*25, lw-40, 22, "#18181b", "#29292e", 6)
        text(lx+30, ly+115+j*25, line, 12, 500)

    # A truthful code-style snapshot of the user's actual learning and tools.
    cx, cy, cw, ch = (24, 850, 432, 206) if mobile else (514, 420, 454, 198)
    rect(cx, cy, cw, ch)
    icon("terminal", cx+20, cy+20, 19)
    text(cx+49, cy+35, "Builder's config", 14, 600)
    text(cx+cw-22, cy+34, "profile.ts", 11, cls="muted", extra='text-anchor="end"')
    rect(cx+16, cy+50, cw-32, ch-66, "#080808", "#27272a", 10)
    lines = [
        "const uttkarsh = {",
        '  learning: ["MERN", "Spring Boot", "SwiftUI"],',
        '  tools: ["Claude", "Codex", "IntelliJ IDEA",',
        '          "PyCharm", "DataGrip"],',
        '  exploring: ["System design", "AI / ML"]',
        "};",
    ]
    for j, line in enumerate(lines):
        text(cx+28, cy+74+j*19, line, cls="code", extra='xml:space="preserve"')

    oy = 1090 if mobile else 650
    text(inset, oy-14, "OPEN TO", 10, 600, "eyebrow")
    opportunities = [
        ("rocket", "Internships", "Learn with a team"),
        ("trophy", "Hackathons", "Build under pressure"),
        ("briefcase-business", "Freelance projects", "Thoughtful web projects"),
        ("git-branch", "Open source", "Collaborate & contribute"),
    ]
    for i, (name, title, sub) in enumerate(opportunities):
        ox = 24+(i % 2)*224 if mobile else 32+i*238
        sy = oy+(i//2)*104 if mobile else oy
        sw = 208 if mobile else 222
        rect(ox, sy, sw, 88, radius=12)
        icon(name, ox+16, sy+15, 18)
        text(ox+44, sy+30, title, 13 if mobile else 14, 600)
        text(ox+16, sy+61, sub, 11 if mobile else 12, cls="muted")
    footer_y = 1306 if mobile else 779
    parts.append(f'<path d="M{inset} {footer_y-16}H{width-inset}" stroke="#27272a"/>')
    if mobile:
        text(inset, footer_y+7, "OFF THE KEYBOARD", 9, 600, "eyebrow")
        text(inset, footer_y+29, "Video editing · Formula 1 · Hackathons", 12, cls="muted")
    else:
        text(inset, footer_y+6, "OFF THE KEYBOARD", 10, 600, "eyebrow")
        text(216, footer_y+6, "Video editing · Formula 1 · Hackathons", 13, cls="muted")
    parts.append('</svg>')
    svg = '\n'.join(parts)+'\n'
    ET.fromstring(svg)
    return svg


def main():
    for mobile in (False, True):
        name = "whoami-card-mobile.svg" if mobile else "whoami-card.svg"
        (ROOT / "assets" / name).write_text(render(mobile))
        print(f"Built {name}")


if __name__ == "__main__":
    main()
