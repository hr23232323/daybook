#!/usr/bin/env bash
set -euo pipefail

SOCIAL_DIR="$(cd "$(dirname "$0")" && pwd)"
REPOSITORY_DIR="$(cd "${SOCIAL_DIR}/../../.." && pwd)"
SOURCE_DIR="${REPOSITORY_DIR}/marketing/video/source"

mkdir -p "${SOCIAL_DIR}"

render() {
  local source="$1"
  local filter="$2"
  local output="$3"

  ffmpeg \
    -hide_banner \
    -loglevel error \
    -y \
    -i "${SOURCE_DIR}/${source}" \
    -vf "${filter},setsar=1,format=rgb24" \
    -frames:v 1 \
    "${SOCIAL_DIR}/${output}"
}

# Card 1 keeps the complete product visible so the carousel opens with context.
render \
  "statement.png" \
  "scale=1440:900:flags=lanczos,pad=1440:1440:0:270:color=#efebe3,unsharp=3:3:0.22" \
  "01-statement.png"

# Cards 2 and 3 crop into the product itself so the key details remain legible
# in X's two-by-two mobile gallery preview.
render \
  "discoveries.png" \
  "crop=1000:1000:300:0,scale=1440:1440:flags=lanczos,unsharp=3:3:0.22" \
  "02-discoveries.png"

render \
  "advisor.png" \
  "crop=1000:1000:300:0,scale=1440:1440:flags=lanczos,unsharp=3:3:0.22" \
  "03-advisor.png"

# The import screen needs both local and connected paths in view, so it uses a
# wider crop with the same quiet page color above and below.
render \
  "import.png" \
  "crop=1200:1000:285:0,scale=1440:1200:flags=lanczos,pad=1440:1440:0:120:color=#efebe3,unsharp=3:3:0.22" \
  "04-import.png"

echo "Wrote X launch images to ${SOCIAL_DIR}"
