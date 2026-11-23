#!/usr/bin/env bash
# Converts the vertical 4K HDR phone clips to 1080x1920 normal (BT.709) video
# with natural color, plus a 48kHz WAV of each clip's sound for cleanup.
set -euo pipefail
cd "$(dirname "$0")/.."
HDR='zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=pc'
mkdir -p public/footage/vlog
for f in public/footage/IMG_30*.mov; do
  n=$(basename "$f" | cut -d. -f1)
  [ -f public/footage/vlog/$n.mp4 ] || ffmpeg -v error -y -i "$f" \
    -vf "$HDR,scale=1080:1920:flags=lanczos:out_color_matrix=bt709:out_range=tv,format=yuv420p" \
    -c:v libx264 -crf 16 -preset fast -colorspace bt709 -color_primaries bt709 \
    -color_trc bt709 -color_range tv -an public/footage/vlog/$n.mp4
  [ -f public/footage/vlog/$n.wav ] || ffmpeg -v error -y -i "$f" -vn -ac 2 -ar 48000 public/footage/vlog/$n.wav
  echo "done $n"
done
