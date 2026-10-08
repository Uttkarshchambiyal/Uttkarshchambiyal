#!/usr/bin/env python3
"""Build README-safe layered Londrina headings from the supplied React effect.

The two font layers retain separate stagger offsets. Nested SVG transforms
combine the original stepped skew and scale animations. Bundled glyph outlines
avoid external font requests; reduced motion shows stationary lettering.
"""

from html import escape
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FONT = json.loads((ROOT / "assets/stagger-heading-glyphs.json").read_text())
HEADINGS = {
    "whoami": ("whoami-heading-staggered.svg", "Whoami"),
    "tech-stack": ("tech-stack-heading-staggered.svg", "Tech Stack"),
    "cp-platforms": ("cp-platforms-heading-staggered.svg", "CP Platforms"),
    "contributions": ("contributions-heading-staggered.svg", "Contribution Skyline"),
}


def delay(index, base):
    char_number = index + 1
    return base - (1000 if char_number % 7 == 0 else 500 if char_number % 5 == 0 else 250 if char_number % 3 == 0 else 0)


def render(label):
    solid = FONT["layers"]["solid"]
    tracking = FONT["tracking"]
    total = sum(solid[char]["advance"] for char in label) + (len(label)-1)*tracking
    position = (1000-total)/2
    centers = []
    for char in label:
        centers.append(position+solid[char]["advance"]/2)
        position += solid[char]["advance"]+tracking
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 1000 144" role="img" aria-labelledby="title description">',
        f'<title id="title">{escape(label)}</title>',
        '<desc id="description">A clean centered heading in layered Londrina Solid and Londrina Sketch lettering. Orange letters and their sketch layer playfully skew and scale with staggered timing. Reduced motion displays stationary text.</desc>',
        '<!-- Londrina font licenses are bundled in assets/licenses. -->',
        '<style>svg{--solid:#ea580c;--outline:#18181b}.solid{fill:var(--solid)}.sketch{fill:var(--outline)}.still{display:none}@media(prefers-color-scheme:dark){svg{--solid:#fb923c;--outline:#f4f4f5}}@media(prefers-reduced-motion:reduce){.motion{display:none}.still{display:inline}}</style>',
        '<defs>',
    ]
    for layer in ("solid", "sketch"):
        for char in sorted(set(label)-{" "}):
            parts.append(f'<path id="{layer}-{ord(char):x}" d="{FONT["layers"][layer][char]["path"]}"/>')
    parts += ['</defs>']
    for layer, base in (("solid", 200), ("sketch", 0)):
        parts.append(f'<g class="{layer}" aria-hidden="true">')
        for index, char in enumerate(label):
            if char == " ":
                continue
            glyph = FONT["layers"][layer][char]
            use = f'<use href="#{layer}-{ord(char):x}" x="{-glyph["advance"]/2:.3f}" y="34.2"/>'
            begin = f'{delay(index, base)/1000:g}s'
            parts.append(f'<g transform="translate({centers[index]:.3f} 68.8)">')
            parts.append(f'<g class="still">{use}</g>')
            parts.append('<g class="motion"><g>')
            parts.append(f'<animateTransform attributeName="transform" type="skewX" values="6;-4;8;-6;2;-10" keyTimes="0;.2;.4;.6;.8;1" dur="2s" begin="{begin}" repeatCount="indefinite" calcMode="discrete"/>')
            parts.append('<g>')
            parts.append(f'<animateTransform attributeName="transform" type="scale" values="1;1.1;.9;1.05;.9;1.2" keyTimes="0;.2;.4;.6;.8;1" dur="1s" begin="{begin}" repeatCount="indefinite" calcMode="discrete"/>')
            parts.append(use+'</g></g></g></g>')
        parts.append('</g>')
    parts.append('</svg>')
    svg = '\n'.join(parts)+'\n'
    ET.fromstring(svg)
    return svg


def main():
    for filename, label in HEADINGS.values():
        (ROOT / "assets" / filename).write_text(render(label))
        print(f"Built {filename}: {label}")


if __name__ == "__main__":
    main()
