#!/usr/bin/env python3
"""Render the supplied liquid-glass shader into GitHub-safe README media.

Requires Pillow 12.x. Run this file, open the printed local URL, and choose
Render animation. Authoring controls are excluded from the exported media.
"""

import argparse
import io
import re
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image, _webp

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, FRAMES, DURATION_MS = 1400, 520, 450, 20


def encode_webp(paths):
    # Full-colour WebP preserves glass refraction; GIF is a universal fallback.
    # Stream frames into Pillow's WebP encoder rather than keeping all RGB images
    # in memory. This follows the encoder interface used by WebPImagePlugin.
    encoder = _webp.WebPAnimEncoder((WIDTH, HEIGHT), 0xFF0D1117, 0, False, 3, 5, False, False)
    for index, path in enumerate(paths):
        with Image.open(path) as image:
            frame = image.convert('RGBX')
            # Preserve low-contrast fade frames exactly so no ghost remains at loop end.
            encoder.add(frame.getim(), index * DURATION_MS, index >= 305, 84, 100, 4)
        if index % 100 == 0:
            print(f'Encoded {index}/{FRAMES} full-colour frames', flush=True)
    encoder.add(None, FRAMES * DURATION_MS, False, 84, 100, 0)
    webp = ROOT / 'assets/glass-script-signature.webp'
    webp.write_bytes(encoder.assemble('', '', ''))
    with Image.open(webp) as image:
        assert image.size == (WIDTH, HEIGHT) and 1 < image.n_frames <= FRAMES
    return webp


def assemble(directory):
    paths = [directory / f'{i:03}.png' for i in range(FRAMES)]
    if not all(path.is_file() for path in paths):
        raise ValueError('Missing rendered frames')
    webp = encode_webp(paths)
    # One shared palette keeps the glass rim steady in the GIF fallback.
    atlas = Image.new('RGB', (700, 260 * 5))
    for row, index in enumerate((30, 90, 150, 220, 290)):
        with Image.open(paths[index]) as image:
            atlas.paste(image.convert('RGB').resize((700, 260)), (0, row * 260))
    palette = atlas.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    indexed = []
    for path in paths[::2]:
        with Image.open(path) as image:
            indexed.append(image.convert('RGB').quantize(palette=palette, dither=Image.Dither.NONE))
    output = ROOT / 'assets/glass-script-signature.gif'
    indexed[0].save(output, save_all=True, append_images=indexed[1:],
                    duration=DURATION_MS * 2, loop=0, optimize=True, disposal=1)
    with Image.open(paths[245]) as image:
        image.convert('RGB').save(ROOT / 'assets/glass-script-signature.png', optimize=True)
    with Image.open(output) as image:
        assert image.size == (WIDTH, HEIGHT)
        assert 1 < image.n_frames <= FRAMES // 2
        assert image.info['loop'] == 0
    print(f'Exported {WIDTH}x{HEIGHT}, {FRAMES} frames, 50 fps, '
          f'9-second logo and script reveal, WebP {webp.stat().st_size:,} bytes, '
          f'GIF fallback {output.stat().st_size:,} bytes', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--preview-output', type=Path, default=ROOT / 'assets/glass-script-signature.png')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='glass-ending-') as temporary:
        frames = Path(temporary)

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.split('?')[0] == '/':
                    path = ROOT / 'scripts/glass_ending.html'
                elif self.path.split('?')[0] in ('/assets/uttkarsh-monogram.png', '/assets/uttkarsh-signature.svg'):
                    path = ROOT / self.path.split('?')[0].lstrip('/')
                else:
                    self.send_error(404); return
                if not path.is_file():
                    self.send_error(404); return
                self.send_response(200)
                self.send_header('Content-Type', {'.html': 'text/html', '.svg': 'image/svg+xml', '.png': 'image/png'}.get(path.suffix, 'text/javascript'))
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

        print(f'Liquid glass renderer: http://127.0.0.1:{args.port}', flush=True)
        ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
