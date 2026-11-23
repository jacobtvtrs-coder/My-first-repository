"""Cleans the vlog sound: removes hum/rumble and hiss from each clip, then
silences everything except the moments someone is talking or laughing.

"Talking" = transcribed words (from transcribe-vlog.py) OR loud enough to be a
voice/laugh (laughs are not transcribed, but are the funny part). Short pauses
inside a sentence are kept so speech doesn't sound chopped.

Writes public/footage/vlog-audio/<clip>.clean.wav (48kHz mono).
Usage: python3 scripts/clean-vlog-audio.py
"""

import glob
import json
import os
import subprocess

import numpy as np

SR = 48000
HOP = 480  # 10ms analysis steps
VOICE_DB = -36  # louder than this (after denoise) counts as voice/laugh
KEEP_GAP = 0.45  # pauses shorter than this inside speech are kept
PAD_BEFORE, PAD_AFTER = 0.10, 0.20
FADE = 0.03
# Clips with music playing in the room: loudness can't tell voice from music,
# so only the transcribed words open the gate (music is muted between them).
WORDS_ONLY = {"IMG_3066"}

# Remove rumble/hum below 80Hz, light noise reduction (the voices-only track
# is already clean), then make the voice a little clearer and keep peaks under
# control.
FILTER = ("highpass=f=80,afftdn=nf=-50:nr=8:tn=1,"
          "equalizer=f=3000:t=q:w=1.2:g=2,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120")


def load(path: str) -> np.ndarray:
    # Prefer the voices-only track from isolate-voices.py when it exists, so
    # music and background sounds are gone even underneath the talking.
    name = os.path.basename(path).split(".")[0]
    voice = f"public/footage/vlog-audio/{name}.voice.wav"
    if os.path.exists(voice):
        path = voice
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-af", FILTER, "-ac", "1",
                          "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def mask_from(regions, n):
    m = np.zeros(n, bool)
    for a, b in regions:
        m[max(0, int(a * SR / HOP)):int(b * SR / HOP) + 1] = True
    return m


def to_regions(m):
    regions, start = [], None
    for i, v in enumerate(np.append(m, False)):
        if v and start is None:
            start = i
        elif not v and start is not None:
            regions.append((start * HOP / SR, i * HOP / SR))
            start = None
    return regions


def main():
    for mov in sorted(glob.glob("public/footage/IMG_30*.mov")):
        name = os.path.basename(mov).split(".")[0]
        out = f"public/footage/vlog-audio/{name}.clean.wav"
        y = load(mov)
        n = len(y) // HOP
        rms = np.sqrt(np.mean(y[: n * HOP].reshape(n, HOP) ** 2, axis=1))
        db = 20 * np.log10(rms + 1e-9)
        # smooth over 50ms so single clicks don't open the gate
        loud = np.convolve(db, np.ones(5) / 5, "same") > VOICE_DB

        words = []
        for tj in (f"public/footage/vlog-audio/{name}.json", f"public/footage/vlog-audio/{name}.es.json"):
            if os.path.exists(tj):
                data = json.load(open(tj))
                for seg in data["segments"] if isinstance(data, dict) else data:
                    words += [(w["start"], w["end"]) for w in seg["words"]]
        active = mask_from(words, n) if name in WORDS_ONLY else loud | mask_from(words, n)

        # merge short gaps, drop tiny blips, then pad
        regions = to_regions(active)
        merged = []
        for a, b in regions:
            if merged and a - merged[-1][1] < KEEP_GAP:
                merged[-1] = (merged[-1][0], b)
            else:
                merged.append((a, b))
        merged = [(a - PAD_BEFORE, b + PAD_AFTER) for a, b in merged if b - a > 0.12]

        # build a smooth gain curve: 1 in speech, 0 elsewhere, 30ms fades
        gain = np.zeros(len(y), np.float32)
        f = int(FADE * SR)
        for a, b in merged:
            i0, i1 = max(0, int(a * SR)), min(len(y), int(b * SR))
            gain[i0:i1] = 1
        kernel = np.ones(f, np.float32) / f
        gain = np.convolve(gain, kernel, "same")
        clean = y * gain

        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1",
                        "-i", "-", "-c:a", "pcm_s16le", out], input=clean.tobytes(), check=True)
        kept = sum(b - a for a, b in merged)
        json.dump([(round(a, 2), round(b, 2)) for a, b in merged],
                  open(f"public/footage/vlog-audio/{name}.speech.json", "w"))
        print(f"{name}: {len(y) / SR:.1f}s, voice kept {kept:.1f}s in {len(merged)} parts", flush=True)


if __name__ == "__main__":
    main()
