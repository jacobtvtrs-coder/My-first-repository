"""Paints out the white paper neck strip in the BEFORE part of the footage.

The strip is replaced with the black of the cape, so the before shots match the
after shots (where the cape sits directly at the neck). Writes a short clip that
BarberCuts uses for its before shots.

Usage:
  python3 scripts/remove-neck-strip.py <footage.mov> <start_sec> <seconds> <out.mp4> [debug_dir]
  python3 scripts/remove-neck-strip.py <footage.mov> <start_sec> <seconds> <out.mp4> --plain

Needs: pip install opencv-python-headless, and ffmpeg on PATH.
"""

import subprocess
import sys

import cv2
import numpy as np

# Area around the neck where the strip can be (x0, y0, x1, y1) in the 720x1280
# footage. Anything outside it is never touched.
ROI = (0, 680, 400, 1080)
# The strip is only ever inside this shape (drawn around it with a margin for
# the few pixels the head moves). Keeps the light wall behind him untouched.
ALLOWED = np.array(
    [(40, 728), (145, 728), (160, 760), (272, 940), (290, 968),
     (255, 1030), (150, 1030), (40, 800)],
    np.int32,
)
# Points that are on the strip; the detected area must touch one of them.
SEEDS = [(170, 900), (200, 970), (120, 820)]


def strip_mask(frame: np.ndarray) -> np.ndarray:
    x0, y0, x1, y1 = ROI
    roi = frame[y0:y1, x0:x1]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY).astype(np.float32)
    spread = roi.max(axis=2).astype(int) - roi.min(axis=2).astype(int)

    # Strip is light and colorless, like the wall behind it...
    bright = (gray > 150) & (spread < 28)
    # ...but the wall is perfectly smooth, while the paper has texture.
    mean = cv2.blur(gray, (9, 9))
    std = np.sqrt(np.maximum(cv2.blur(gray * gray, (9, 9)) - mean * mean, 0))
    textured = cv2.dilate((std > 1.6).astype(np.uint8), np.ones((5, 5), np.uint8))

    allowed = np.zeros(frame.shape[:2], np.uint8)
    cv2.fillPoly(allowed, [ALLOWED], 1)
    cand = (bright & (textured > 0) & (allowed[y0:y1, x0:x1] > 0)).astype(np.uint8)
    cand = cv2.morphologyEx(cand, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

    n, labels = cv2.connectedComponents(cand)
    keep = np.zeros_like(cand)
    for sx, sy in SEEDS:
        lab = labels[sy - y0, sx - x0]
        if lab > 0:
            keep[labels == lab] = 1

    # Fill small holes (creases, shadows) and grow a little past the edge so no
    # white fringe is left.
    contours, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    keep = np.zeros_like(keep)
    cv2.drawContours(keep, contours, -1, 1, thickness=cv2.FILLED)
    keep = cv2.dilate(keep, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))

    full = np.zeros(frame.shape[:2], np.uint8)
    full[y0:y1, x0:x1] = keep
    # The edge growth must not spill back out over the wall either.
    return full & cv2.dilate(allowed, np.ones((5, 5), np.uint8))


def paint_cape(frame: np.ndarray, mask: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    # Cape color taken from just around the strip (dark pixels only).
    ring = cv2.dilate(mask, np.ones((25, 25), np.uint8)) & (1 - mask)
    near = frame[ring > 0]
    dark = near[near.max(axis=1) < 70]
    color = np.median(dark, axis=0) if len(dark) > 50 else np.array([22, 18, 16])

    fill = np.empty_like(frame, dtype=np.float32)
    fill[:] = color
    # Soft fold shading and fine grain so the fill doesn't look flat.
    h, w = frame.shape[:2]
    shade = cv2.GaussianBlur(rng.normal(0, 1, (h // 16, w // 16)).astype(np.float32), (0, 0), 1.5)
    shade = cv2.resize(shade, (w, h), interpolation=cv2.INTER_CUBIC) * 5
    grain = rng.normal(0, 1.2, (h, w)).astype(np.float32)
    fill += (shade + grain)[..., None]

    alpha = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.5)[..., None]
    out = frame.astype(np.float32) * (1 - alpha) + fill * alpha
    return np.clip(out, 0, 255).astype(np.uint8)


def main() -> None:
    src, start, seconds, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    debug = sys.argv[5] if len(sys.argv) > 5 else None
    # "--plain": convert only, no strip removal. Used for the AFTER shots so
    # both looks go through exactly the same color conversion.
    plain = debug == "--plain"
    if plain:
        debug = None

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,r_frame_rate", "-of", "csv=p=0", src],
        capture_output=True, text=True, check=True,
    ).stdout.strip().split(",")
    w, h = int(probe[0]), int(probe[1])
    num, den = probe[2].split("/")
    fps = int(num) / int(den)
    total = round(seconds * fps)

    # Decode with ffmpeg, the same way Remotion reads the footage for the AFTER
    # shots. (The phone footage is HDR; OpenCV decodes it brighter and washed
    # out, which made the BEFORE shots look graded differently.)
    dec = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-ss", f"{start:.4f}", "-i", src,
         "-frames:v", str(total), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
        stdout=subprocess.PIPE,
    )
    # Encode as standard BT.709 video and label it so, so it is read back with
    # exactly the colors that were written.
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
         "-s", f"{w}x{h}", "-r", probe[2], "-i", "-",
         "-vf", "scale=out_color_matrix=bt709:out_range=tv",
         "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt", "yuv420p",
         "-colorspace", "bt709", "-color_primaries", "bt709",
         "-color_trc", "bt709", "-color_range", "tv", out],
        stdin=subprocess.PIPE,
    )
    rng = np.random.default_rng(7)
    areas = []
    for i in range(total):
        buf = dec.stdout.read(w * h * 3)
        if len(buf) < w * h * 3:
            break
        frame = np.frombuffer(buf, np.uint8).reshape(h, w, 3).copy()
        mask = np.zeros(frame.shape[:2], np.uint8) if plain else strip_mask(frame)
        areas.append(int(mask.sum()))
        clean = frame if plain else paint_cape(frame, mask, rng)
        if debug and i % 30 == 0:
            over = frame.copy()
            over[mask > 0] = (0.5 * over[mask > 0] + [0, 0, 127]).astype(np.uint8)
            cv2.imwrite(f"{debug}/mask_{i:03d}.png", over)
            cv2.imwrite(f"{debug}/clean_{i:03d}.png", clean)
        enc.stdin.write(clean.tobytes())
    dec.stdout.close()
    dec.wait()
    enc.stdin.close()
    enc.wait()
    print(f"frames={len(areas)} strip area px min={min(areas)} max={max(areas)} median={int(np.median(areas))}")


if __name__ == "__main__":
    main()
