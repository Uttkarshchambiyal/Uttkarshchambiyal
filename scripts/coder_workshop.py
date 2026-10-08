#!/usr/bin/env python3
"""Serve the Three.js workshop renderer and assemble GitHub-safe animated media.

Requires Pillow and Three.js 0.180.0. Install Three.js in a temporary directory
with npm, then pass its node_modules/three directory as --three. Open the printed
local URL and use Render animation. Controls belong to this authoring page only;
the exported README media contains no controls, scripts, or external requests.
"""

import argparse
import io
import re
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, FRAMES, DURATION_MS = 1600, 1024, 200, 40


def assemble(directory):
    paths = [directory / f'{i:03}.png' for i in range(FRAMES)]
    if not all(path.is_file() for path in paths):
        raise ValueError('Missing rendered frames')
    # Full-colour WebP preserves the rounded lighting; GIF is a universal fallback.
    rendered = []
    for path in paths:
        with Image.open(path) as image:
            rendered.append(image.convert('RGB'))
    webp = ROOT / 'assets/coder-workshop.webp'
    rendered[0].save(webp, save_all=True, append_images=rendered[1:],
                     duration=DURATION_MS, loop=0, quality=94, method=3,
                     minimize_size=True)
    for image in rendered:
        image.close()
    del rendered
    with Image.open(webp) as image:
        assert image.size == (WIDTH, HEIGHT) and image.n_frames == FRAMES
    # One palette for the whole loop keeps stationary surfaces from flickering.
    atlas = Image.new('RGB', (800, 512 * 5))
    for row, index in enumerate((0, 40, 80, 120, 160)):
        with Image.open(paths[index]) as image:
            atlas.paste(image.convert('RGB').resize((800, 512)), (0, row * 512))
    palette = atlas.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    indexed = []
    for path in paths:
        with Image.open(path) as image:
            indexed.append(image.convert('RGB').quantize(palette=palette, dither=Image.Dither.NONE))
    output = ROOT / 'assets/coder-workshop.gif'
    indexed[0].save(output, save_all=True, append_images=indexed[1:],
                    duration=DURATION_MS, loop=0, optimize=True, disposal=1)
    with Image.open(paths[12]) as image:
        image.convert('RGB').save(ROOT / 'assets/coder-workshop.png', optimize=True)
    with Image.open(output) as image:
        assert image.size == (WIDTH, HEIGHT)
        assert image.n_frames == FRAMES
        assert image.info['loop'] == 0
    print(f'Exported {WIDTH}x{HEIGHT}, {FRAMES} frames, 25 fps, '
          f'8-second loop, WebP {webp.stat().st_size:,} bytes, '
          f'GIF fallback {output.stat().st_size:,} bytes', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--three', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--preview-output', type=Path, default=ROOT / 'assets/coder-workshop.png')
    args = parser.parse_args()
    three = args.three.resolve()
    if not (three / 'build/three.module.js').is_file():
        parser.error('--three must point to node_modules/three')
    with tempfile.TemporaryDirectory(prefix='coder-workshop-') as temporary:
        frames = Path(temporary)

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.split('?')[0] == '/':
                    path = ROOT / 'scripts/coder_workshop.html'
                elif self.path.startswith('/vendor/'):
                    path = (three / self.path.removeprefix('/vendor/')).resolve()
                    if not path.is_relative_to(three):
                        self.send_error(404); return
                else:
                    self.send_error(404); return
                if not path.is_file():
                    self.send_error(404); return
                self.send_response(200)
                self.send_header('Content-Type', 'text/html' if path.suffix == '.html' else 'text/javascript')
                self.end_headers(); self.wfile.write(path.read_bytes())

            def do_POST(self):
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                    match = re.fullmatch(r'/frame/(\d{3})', self.path)
                    if match and 0 <= int(match[1]) < FRAMES and 0 < length < 5_000_000:
                        data = self.rfile.read(length)
                        with Image.open(io.BytesIO(data)) as image:
                            if image.size != (WIDTH, HEIGHT):
                                raise ValueError('Unexpected dimensions')
                            image.verify()
                        (frames / f'{match[1]}.png').write_bytes(data)
                        if int(match[1]) % 25 == 0:
                            print(f'Received {int(match[1])}/{FRAMES} frames', flush=True)
                    elif self.path == '/finish':
                        assemble(frames)
                    elif self.path == '/preview' and 0 < length < 5_000_000:
                        data = self.rfile.read(length)
                        with Image.open(io.BytesIO(data)) as image:
                            image.convert('RGB').save(args.preview_output)
                    else:
                        self.send_error(404); return
                    self.send_response(200); self.end_headers(); self.wfile.write(b'OK')
                except Exception as error:
                    self.send_error(400, str(error))

            def log_message(self, *_):
                pass

        print(f'Workshop renderer: http://127.0.0.1:{args.port}', flush=True)
        ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
