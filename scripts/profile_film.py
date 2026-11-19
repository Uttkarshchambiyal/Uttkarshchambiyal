#!/usr/bin/env python3
"""Stream a supersampled six-shot profile film into sharp README media.

Requires Pillow 12.x, ffmpeg with libx264, and Three.js 0.180.0. Start with
--three pointing to node_modules/three, open the printed URL, and Render animation.
Frames are captured losslessly at 2x resolution and encoded as they arrive;
no large temporary frame directory is needed. Authoring controls are excluded.
"""
import argparse
import io
import re
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from PIL import Image, _webp

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, FRAMES, FPS = 1440, 810, 900, 30
CAPTURE_SIZE = (WIDTH * 2, HEIGHT * 2)
QUALITY = 90
PREFIX = 'uttkarsh-behind-the-code-hd'


class FilmEncoder:
    def __init__(self):
        self.process = None
        self.encoder = None
        self.next_frame = 0
        self.movie = ROOT / f'assets/{PREFIX}.mp4'
        self.preview = ROOT / f'assets/{PREFIX}.webp'
        self.poster = ROOT / f'assets/{PREFIX}.png'

    def start(self):
        self.abort()
        self.process = subprocess.Popen([
            'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
            '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', f'{WIDTH}x{HEIGHT}',
            '-framerate', str(FPS), '-i', 'pipe:0', '-c:v', 'libx264',
            '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart', '-an', str(self.movie)
        ], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.encoder = _webp.WebPAnimEncoder((WIDTH, HEIGHT), 0xFF070C13, 0, False, 3, 5, False, False)
        self.next_frame = 0

    def add(self, index, source):
        if index == 0:
            self.start()
        if self.encoder is None or index != self.next_frame:
            raise ValueError(f'Expected frame {self.next_frame}, received {index}; restart from frame 0')
        if source.size != CAPTURE_SIZE:
            raise ValueError(f'Expected supersampled frame {CAPTURE_SIZE}, received {source.size}')
        # Downsample directly from a lossless capture, without an intermediate JPEG.
        frame = source.convert('RGB').resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        self.process.stdin.write(frame.tobytes())
        self.encoder.add(frame.convert('RGBX').getim(), round(index * 1000 / FPS),
                         index >= FRAMES - 3, QUALITY, 100, 4)
        if index == 110:
            frame.save(self.poster, optimize=True)
        self.next_frame += 1
        if index % 100 == 0:
            print(f'Encoded {index}/{FRAMES} lossless-source HD frames', flush=True)

    def finish(self):
        if self.next_frame != FRAMES:
            raise ValueError(f'Expected {FRAMES} frames; received {self.next_frame}')
        self.process.stdin.close()
        if self.process.wait() != 0:
            raise RuntimeError('MP4 encoding failed')
        self.process = None
        self.encoder.add(None, 30_000, True, QUALITY, 100, 0)
        self.preview.write_bytes(self.encoder.assemble('', '', ''))
        self.encoder = None
        # Still and animated media both stay at their native README display resolution.
        with Image.open(self.preview) as image:
            assert image.size == (WIDTH, HEIGHT) and image.info['loop'] == 0
            total = 0
            for i in range(image.n_frames):
                image.seek(i); image.load(); total += image.info['duration']
            assert total == 30_000
        print(f'Exported native {WIDTH}x{HEIGHT}, quality {QUALITY}, 30 fps, 30 seconds; '
              f'WebP {self.preview.stat().st_size:,} bytes; MP4 {self.movie.stat().st_size:,} bytes.', flush=True)

    def abort(self):
        if self.process is not None:
            try:
                self.process.stdin.close()
            except (BrokenPipeError, OSError):
                pass
            if self.process.poll() is None:
                self.process.terminate()
            self.process.wait()
            self.process = None
        self.encoder = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--three', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8768)
    parser.add_argument('--preview-output', type=Path, default=ROOT / f'assets/{PREFIX}.png')
    args = parser.parse_args()
    three = args.three.resolve()
    if not (three / 'build/three.module.js').is_file():
        parser.error('--three must point to node_modules/three')
    encoder = FilmEncoder()

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
                if match and 0 <= int(match[1]) < FRAMES and 0 < length < 16_000_000:
                    with Image.open(io.BytesIO(self.rfile.read(length))) as image:
                        encoder.add(int(match[1]), image)
                elif self.path == '/finish':
                    encoder.finish()
                elif self.path == '/preview' and 0 < length < 16_000_000:
                    with Image.open(io.BytesIO(self.rfile.read(length))) as image:
                        image.convert('RGB').resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(args.preview_output)
                else:
                    self.send_error(404); return
                self.send_response(200); self.end_headers(); self.wfile.write(b'OK')
            except Exception as error:
                self.send_error(400, str(error))

        def log_message(self, *_):
            pass

    print(f'Profile film: http://127.0.0.1:{args.port}', flush=True)
    try:
        HTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
    finally:
        encoder.abort()


if __name__ == '__main__':
    main()
