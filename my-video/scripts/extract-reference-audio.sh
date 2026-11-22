#!/usr/bin/env bash
# Cuts the song out of the reference screen recording, lined up with the edit.
# The reference's first cut happens 0.0383s in, so the audio starts there and
# runs for the length of the BarberCuts composition (208 frames at 30fps).
# Output stays in public/footage/, which is not committed to git.
set -euo pipefail
cd "$(dirname "$0")/.."
REF=$(ls public/footage/ScreenRecording_*.mov | head -1)
ffmpeg -v error -y -ss 0.0383 -t 6.9333 -i "$REF" -vn -c:a aac -b:a 256k \
  public/footage/reference-audio.m4a
echo "Wrote public/footage/reference-audio.m4a"
