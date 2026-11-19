# Behind the code

A silent, 30-second animated profile film for Uttkarsh Chambiyal. The captions
carry the story without sound. The orange hoodie and its black back print stay
consistent with the existing character.

| Time | Scene and camera | Story |
| --- | --- | --- |
| 00–05 | Wide entrance shot; camera gently tracks toward the workspace | Hi, I’m Uttkarsh. Frontend developer and DSA practitioner. |
| 05–10 | High-angle view over the desk; a UI design develops on the monitor | Ideas become thoughtful interfaces. Figma and UI/UX. |
| 10–15 | Close-up over the shoulder; syntax-highlighted code is typed | Building with React, TypeScript, and Java. |
| 15–20 | Separate 3D array scene; camera arcs over binary search | Find 23 in a sorted array: compare 11, then find 23 at index 5. |
| 20–25 | Character portrait from the side; floating learning cards | Exploring Spring Boot, SwiftUI, and the MERN stack. |
| 25–30 | Wide orbit and pullback; a completed interface on the monitor | Open to internships, hackathons, and open source. |

Chapter cuts dip briefly to dark. The first and last frames match, so the README
preview loops cleanly. The separate glass signature remains the README’s ending.
No project results, employers, achievements, or expertise levels are invented.

## Render

Requires Python with Pillow 12.x, ffmpeg with libx264, and Three.js 0.180.0.
Install Three.js in a temporary directory, then run:

```sh
python3 scripts/profile_film.py --three /path/to/node_modules/three
```

Open the printed local URL. Scrub and save stills to inspect the shots, then use
**Render animation**. Exported media contains no authoring controls. The source
runs locally with no external fonts, images, or services. Frames stream directly
into the encoders so no large temporary frame directory is needed.

- Capture: 2880 × 1620, lossless PNG, with antialiasing and 2x screen textures.
- MP4: 1440 × 810, CRF 16, 30 fps, 30 seconds, H.264, silent, fast-start playback.
- WebP: native 1440 × 810, quality 90, 30 fps, 30-second loop for the README.
- PNG: native 1440 × 810 poster for reduced-motion settings and fallback browsers.

The capture is downsampled once from lossless pixels. There is no intermediate
JPEG compression and no upscaling of a 768px preview. Labels and monitor textures
are generated at double resolution, with anisotropic filtering for angled screens.

GitHub READMEs cannot run the Three.js source. The README uses the animated WebP;
the MP4 master is retained as a repository asset without adding a download link.
