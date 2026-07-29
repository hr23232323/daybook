# Daybook launch video

The 15-second launch film is built from real Daybook screens populated only with the
repository's deterministic fictional-data generator. It is designed for X playback:
1280×720, 30 fps, H.264 video, AAC audio, and complete comprehension with sound off.

## Render

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
