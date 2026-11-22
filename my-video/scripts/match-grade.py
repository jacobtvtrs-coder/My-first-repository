"""Matches a clip's color grade to a reference clip, in place.

Measures the wall (light) and the cape (dark) in both clips, then applies a
per-channel levels adjustment so the clip's wall and cape come out the same
color as the reference's. Used so the BEFORE shots match the AFTER shots.

Usage:
  python3 scripts/match-grade.py <clip.mp4> <reference.mp4>
"""

import os
import subprocess
import sys

import numpy as np

# Regions in the 720x1280 footage: plain wall, and cape below the neck.
WALL = (20, 60, 200, 300)  # x0, y0, x1, y1
CAPE = (30, 1100, 180, 1250)
W, H = 720, 1280
ENCODE = ["-vf", "scale=out_color_matrix=bt709:out_range=tv",
          "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt", "yuv420p",
          "-colorspace", "bt709", "-color_primaries", "bt709",
          "-color_trc", "bt709", "-color_range", "tv"]


def frames(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        yield np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    p.wait()


def region_means(path):
    wall, cape = [], []
    for f in frames(path):
        for acc, (x0, y0, x1, y1) in ((wall, WALL), (cape, CAPE)):
            acc.append(f[y0:y1, x0:x1].reshape(-1, 3).mean(0))
    return np.mean(wall, 0), np.mean(cape, 0)


def main() -> None:
    clip, ref = sys.argv[1], sys.argv[2]
    cw, cc = region_means(clip)
    rw, rc = region_means(ref)
    gain = (rw - rc) / (cw - cc)
    offset = rc - gain * cc
    print("gain", gain.round(3), "offset", offset.round(2))

    fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", clip],
                         capture_output=True, text=True, check=True).stdout.strip()
    tmp = clip + ".tmp.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", fps, "-i", "-", *ENCODE, tmp],
                           stdin=subprocess.PIPE)
    for f in frames(clip):
        out = np.clip(f.astype(np.float32) * gain + offset, 0, 255)
        enc.stdin.write(np.round(out).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()
    os.replace(tmp, clip)

    nw, nc = region_means(clip)
    print("wall", nw.round(1), "ref", rw.round(1), "| cape", nc.round(1), "ref", rc.round(1))


if __name__ == "__main__":
    main()
