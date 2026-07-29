# Daybook launch films

All launch films are built from real Daybook screens populated only with the
repository's deterministic fictional-data generator. Keep the earlier cuts for
comparison; v3 is the recommended social upload.

## V3 — organic share cut

`output/daybook-launch-v3-organic-square.mp4` is the recommended X upload. It is a
15-second, full-bleed product recording with a smooth cursor and a deliberately steady
camera. The frame pans only to expose a navigation click and zooms only to make a
specific result easier to read. There is no ad frame, headline layer, or end card.

```bash
cd marketing/video/v2
npm install
npm run render:organic
npm run cover:organic
```

It writes:

- `output/daybook-launch-v3-organic-square.mp4` — recommended X video
- `output/daybook-launch-v3-organic-cover.png` — optional thumbnail

## V2 — designed product trailer

`output/daybook-launch-v2-square.mp4` is the more designed cut. It is 15 seconds,
1080×1080, 30 fps, H.264/AAC, under 10 MB, and understandable with sound off. It adds
cursor choreography, click feedback, camera-follow zooms, depth, spring motion, and an
original ambient sound design.

Requirements: Node.js, npm, Python 3, and `ffmpeg`.

```bash
cd marketing/video/v2
npm install
npm run render
```

Useful development commands:

```bash
npm run studio
npm run cover
```

The renderer stages repository assets into the gitignored `v2/public/` directory,
renders a high-quality intermediate, normalizes audio for social playback, and
preserves the H.264 picture while creating the final upload.

It writes:

- `output/daybook-launch-v2-square.mp4` — recommended mobile-first X video
- `output/daybook-launch-v2-cover.png` — optional v2 thumbnail

## V1 — widescreen launch film

Install Daybook first, then run:

```bash
.venv/bin/python marketing/video/render.py
```

The renderer has no Python package dependencies. It uses `rsvg-convert`, `ffmpeg`, and
`ffprobe` from the system. It generates the motion frames in a temporary directory,
synthesizes an original sound bed, and writes:

- `output/daybook-launch-16x9.mp4` — upload-ready video
- `output/daybook-launch-cover.png` — optional thumbnail

## Updating the footage

The PNG files in `source/` are 1600×1000 browser captures from an isolated Daybook
instance using `scripts/seed_fake_data.py`. Never replace them with captures containing
real financial records, bank names, tokens, or API credentials.

The advisor frame is a staged rendering of facts computed from that same fictional
dataset; no model request is made during capture or render.
