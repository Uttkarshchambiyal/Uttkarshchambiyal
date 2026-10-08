#!/usr/bin/env python3
"""Build README-safe versions of the supplied staggered BlurReveal effect.

GitHub renders SVG images but does not execute React. The letters use the
component's 12px blur, 10px rise, 20ms stagger, and 600ms reveal. A long readable
hold lets visitors catch the effect even after scrolling down the profile.
"""

from html import escape
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HEADINGS = {
    "whoami-heading": "> whoami",
    "tech-stack-heading": "> tech --stack",
    "cp-platforms-heading": "> cp --platforms",
    "contributions-heading": "> contributions --skyline",
}
ROOT = Path(__file__).resolve().parents[1]
CYCLE = 12
FONT = json.loads((ROOT / "assets" / "heading-font-glyphs.json").read_text())


def render(text):
    width, height, baseline = 1000, 112, 77
    glyphs, tracking = FONT["glyphs"], FONT["tracking"]
    text_width = sum(glyphs[char]["advance"] for char in text) + (len(text) - 1) * tracking
    start_x = (width - text_width) / 2
    positions = []
    x = start_x
    for char in text:
        positions.append(x)
        x += glyphs[char]["advance"] + tracking
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
        f'<title id="title">{escape(text)}</title>',
        '<desc id="description">A centered heading reveals letter by letter, rising gently from a soft blur. The animation repeats every twelve seconds, with a long readable pause. Reduced motion displays a stationary heading.</desc>',
        '<!-- Inter SemiBold, 64px, tight tracking; glyph outlines preserve the reference typography on every device. Font license: licenses/Inter-OFL.txt. -->',
        '<style>svg{color:#1f2328}use{fill:currentColor}.still{display:none}@media(prefers-color-scheme:dark){svg{color:#f0f3f6}}@media(prefers-reduced-motion:reduce){.motion{display:none}.still{display:inline}}</style>',
        '<defs>',
    ]
    for char in sorted(set(text) - {" "}):
        parts.append(f'<path id="glyph-{ord(char):x}" d="{glyphs[char]["path"]}"/>')
    for i, char in enumerate(text):
        if char == " ":
            continue
        reveal_start = (.1 + i * .02) / CYCLE
        reveal_end = reveal_start + .6 / CYCLE
        exit_start = (10.3 + (len(text) - 1 - i) * .02) / CYCLE
        exit_end = exit_start + .35 / CYCLE
        keys = f'0;{reveal_start:.6f};{reveal_end:.6f};{exit_start:.6f};{exit_end:.6f};1'
        # Each glyph gets its own blur, matching the supplied component.
        parts.append(
            f'<filter id="blur-{i}" x="-150%" y="-100%" width="400%" height="300%" color-interpolation-filters="sRGB">'
            '<feGaussianBlur stdDeviation="0">'
            f'<animate attributeName="stdDeviation" values="12;12;0;0;12;12" keyTimes="{keys}" dur="{CYCLE}s" repeatCount="indefinite" calcMode="spline" keySplines="0 0 1 1;.25 .1 .25 1;0 0 1 1;.4 0 1 1;0 0 1 1"/>'
            '</feGaussianBlur></filter>'
        )
    parts += ['</defs>', '<g class="still" aria-hidden="true">']
    for i, char in enumerate(text):
        if char != " ":
            parts.append(f'<use href="#glyph-{ord(char):x}" x="{positions[i]:.3f}" y="{baseline}"/>')
    parts += ['</g>', '<g class="motion" aria-hidden="true">']
    for i, char in enumerate(text):
        if char == " ":
            continue
        reveal_start = (.1 + i * .02) / CYCLE
        reveal_end = reveal_start + .6 / CYCLE
        exit_start = (10.3 + (len(text) - 1 - i) * .02) / CYCLE
        exit_end = exit_start + .35 / CYCLE
        keys = f'0;{reveal_start:.6f};{reveal_end:.6f};{exit_start:.6f};{exit_end:.6f};1'
        timing = f'keyTimes="{keys}" dur="{CYCLE}s" repeatCount="indefinite" calcMode="spline" keySplines="0 0 1 1;.25 .1 .25 1;0 0 1 1;.4 0 1 1;0 0 1 1"'
        parts.append(
            f'<g opacity="1"><animate attributeName="opacity" values="0;0;1;1;0;0" {timing}/>'
            f'<g><animateTransform attributeName="transform" type="translate" values="0 10;0 10;0 0;0 0;0 10;0 10" {timing}/>'
            f'<use href="#glyph-{ord(char):x}" x="{positions[i]:.3f}" y="{baseline}" filter="url(#blur-{i})"/>'
            '</g></g>'
        )
    parts += ['</g>', '</svg>']
    svg = '\n'.join(parts) + '\n'
    ET.fromstring(svg)
    return svg


def main():
    for name, text in HEADINGS.items():
        (ROOT / "assets" / f"{name}-inter.svg").write_text(render(text))
        print(f"Built {name}: {text}")


if __name__ == "__main__":
    main()
