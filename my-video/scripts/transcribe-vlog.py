"""Transcribes the vlog clips with word timings (for subtitles and finding the
talking parts). Writes public/footage/vlog-audio/<clip>.json.

Usage: python3 scripts/transcribe-vlog.py [model]   (default: medium)
Needs: pip install faster-whisper (downloads the model from Hugging Face).
"""

import glob
import json
import os
import sys
import time

# Download over plain HTTPS (the Xet transfer client needs extra hosts).
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

import soundfile as sf
from faster_whisper import WhisperModel

model_name = sys.argv[1] if len(sys.argv) > 1 else "medium"
model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=4)

for wav in sorted(glob.glob("public/footage/vlog-audio/*.16k.wav")):
    out = wav.replace(".16k.wav", ".json")
    if os.path.exists(out):
        continue
    t = time.time()
    # Pass samples directly (its own decoder breaks with newer PyAV versions).
    audio, _ = sf.read(wav, dtype="float32")
    segments, info = model.transcribe(
        audio, word_timestamps=True, vad_filter=True, beam_size=5,
        vad_parameters={"min_silence_duration_ms": 400},
    )
    segs = []
    for s in segments:
        segs.append({
            "start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
            "words": [{"start": round(w.start, 2), "end": round(w.end, 2), "word": w.word,
                       "p": round(w.probability, 2)} for w in (s.words or [])],
        })
    json.dump({"language": info.language, "language_probability": round(info.language_probability, 2),
               "duration": round(info.duration, 2), "segments": segs},
              open(out, "w"), ensure_ascii=False, indent=1)
    print(f"{os.path.basename(wav)}: {info.language} ({info.language_probability:.2f}), "
          f"{len(segs)} segments, {time.time() - t:.0f}s", flush=True)
