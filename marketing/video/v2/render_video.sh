#!/usr/bin/env bash
set -euo pipefail

V2_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="${V2_DIR}/../output"
RENDER_TEMP="$(mktemp -d "${TMPDIR:-/tmp}/daybook-video.XXXXXX")"
COMPOSITION="${1:-DaybookSquare}"
OUTPUT_NAME="${2:-daybook-launch-v2-square.mp4}"

cleanup() {
  rm -rf "${RENDER_TEMP}"
}
trap cleanup EXIT

cd "${V2_DIR}"
mkdir -p "${OUTPUT_DIR}"

python3 prepare_assets.py
python3 make_audio.py

npx remotion render \
  src/index.tsx \
  "${COMPOSITION}" \
  "${RENDER_TEMP}/raw.mp4" \
  --public-dir public \
  --codec h264 \
  --crf 14 \
  --pixel-format yuv420p \
  --audio-codec aac \
  --audio-bitrate 192K \
  --log info

# Bring the original sound design to a consistent social-video level, then
# remux it without re-encoding the already high-quality H.264 picture.
ffmpeg -hide_banner -loglevel warning -y \
  -i "${RENDER_TEMP}/raw.mp4" \
  -vn \
  -af loudnorm=I=-16:TP=-1.5:LRA=11 \
  -c:a aac \
  -b:a 192k \
  -ar 48000 \
  "${RENDER_TEMP}/normalized.m4a"

ffmpeg -hide_banner -loglevel warning -y \
  -i "${RENDER_TEMP}/raw.mp4" \
  -i "${RENDER_TEMP}/normalized.m4a" \
  -map 0:v:0 \
  -map 1:a:0 \
  -c copy \
  -t 15 \
  -movflags +faststart \
  "${OUTPUT_DIR}/${OUTPUT_NAME}"

echo "Wrote ${OUTPUT_DIR}/${OUTPUT_NAME}"
