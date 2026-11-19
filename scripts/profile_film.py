#!/usr/bin/env python3
"""Render the six-shot profile film, its README animation, and a reduced-motion poster.

Requires Pillow 12.x, ffmpeg, and Three.js 0.180.0. Start with --three pointing to
node_modules/three, open the printed local URL, then choose Render animation.
The exported film has no authoring controls and uses no external network assets.
"""
import argparse
import io
import re
import subprocess
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from PIL import Image, _webp

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, FRAMES, FPS = 1440, 810, 900, 30
PREVIEW_SIZE = (768, 432)


def assemble(directory):
    paths = [directory / f'{i:03}.jpg' for i in range(FRAMES)]
    if not all(p.is_file() for p in paths):
        raise ValueError('Missing film frames')
    movie = ROOT / 'assets/uttkarsh-behind-the-code.mp4'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                    '-framerate', str(FPS), '-i', str(directory / '%03d.jpg'),
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
                    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', str(movie)], check=True)
    print(f'Full film: {movie.stat().st_size:,} bytes', flush=True)
    encoder = _webp.WebPAnimEncoder(PREVIEW_SIZE, 0xFF070C13, 0, False, 3, 5, False, False)
    for index, path in enumerate(paths):
        with Image.open(path) as source:
            frame = source.convert('RGB').resize(PREVIEW_SIZE, Image.Resampling.LANCZOS).convert('RGBX')
            encoder.add(frame.getim(), round(index * 1000 / FPS), index >= FRAMES - 3, 70, 100, 4)
        if index % 100 == 0:
            print(f'Encoded {index}/{FRAMES} preview frames', flush=True)
    encoder.add(None, 30_000, True, 70, 100, 0)
    preview = ROOT / 'assets/uttkarsh-behind-the-code.webp'
    preview.write_bytes(encoder.assemble('', '', ''))
    with Image.open(paths[110]) as source:
        source.convert('RGB').save(ROOT / 'assets/uttkarsh-behind-the-code.png', optimize=True)
    with Image.open(preview) as image:
        assert image.size == PREVIEW_SIZE and image.info['loop'] == 0
        total = 0
        for index in range(image.n_frames):
            image.seek(index); image.load(); total += image.info['duration']
        assert total == 30_000
    print(f'Exported 30-second film and preview ({preview.stat().st_size:,} bytes).', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--three', type=Path, required=True)
    parser.add_argument('--frames', type=Path, help='Optional frame directory for resuming an interrupted export')
    parser.add_argument('--port', type=int, default=8768)
    parser.add_argument('--preview-output', type=Path, default=ROOT / 'assets/uttkarsh-behind-the-code.png')
    args = parser.parse_args()
    three = args.three.resolve()
    if not (three / 'build/three.module.js').is_file():
        parser.error('--three must point to node_modules/three')
    with tempfile.TemporaryDirectory(prefix='profile-film-') as temporary:
        frames = args.frames.resolve() if args.frames else Path(temporary)
        frames.mkdir(parents=True, exist_ok=True)
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.split('?')[0] == '/':
                    path = ROOT / 'scripts/profile_film.html'
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
                    if match and 0 <= int(match[1]) < FRAMES and 0 < length < 8_000_000:
                        data = self.rfile.read(length)
                        with Image.open(io.BytesIO(data)) as image:
                            if image.size != (WIDTH, HEIGHT):
                                raise ValueError('Unexpected dimensions')
                            image.verify()
                        (frames / f'{match[1]}.jpg').write_bytes(data)
                        if int(match[1]) % 100 == 0:
                            print(f'Received {int(match[1])}/{FRAMES} frames', flush=True)
                    elif self.path == '/finish':
                        assemble(frames)
                    elif self.path == '/preview' and 0 < length < 8_000_000:
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
        print(f'Profile film: http://127.0.0.1:{args.port}', flush=True)
        ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()

if __name__ == '__main__':
    main()
