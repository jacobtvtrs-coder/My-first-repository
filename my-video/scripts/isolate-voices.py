"""Keeps only the voices in a clip: separates speech from everything else
(music in the room, background noise) with the UVR MDX-NET Voc_FT model.

Writes public/footage/vlog-audio/<clip>.voice.wav (44.1kHz stereo), which
clean-vlog-audio.py then uses instead of the original sound.

Usage: python3 scripts/isolate-voices.py IMG_3065 IMG_3066
Needs: pip install onnxruntime librosa soundfile, and the model file
~/models/Voc_FT.onnx (UVR-MDX-NET-Voc_FT, ONNX format, from Hugging Face).
"""

import glob
import os
import subprocess
import sys
import time

import librosa
import numpy as np
import onnxruntime as ort
import soundfile as sf

MODEL = os.path.expanduser("~/models/Voc_FT.onnx")
SR = 44100
N_FFT, HOP, DIM_F, DIM_T = 7680, 1024, 3072, 256
COMPENSATE = 1.021  # model-specific level correction
CHUNK = HOP * (DIM_T - 1)
TRIM = N_FFT // 2
GEN = CHUNK - 2 * TRIM


def stft(x):  # x: (2, CHUNK) -> (1, 4, DIM_F, DIM_T)
    specs = [librosa.stft(c, n_fft=N_FFT, hop_length=HOP, window="hann", center=True,
                          pad_mode="reflect")[:DIM_F] for c in x]
    s = np.stack(specs)  # (2, DIM_F, DIM_T) complex
    return np.concatenate([s.real, s.imag])[None].astype(np.float32)


def istft(y):  # (1, 4, DIM_F, DIM_T) -> (2, CHUNK)
    y = y[0]
    full = np.zeros((2, N_FFT // 2 + 1, DIM_T), np.complex64)
    full[:, :DIM_F] = y[:2] + 1j * y[2:]
    return np.stack([librosa.istft(c, hop_length=HOP, window="hann", center=True, length=CHUNK)
                     for c in full])


def separate(mix, sess):  # mix: (2, n)
    n = mix.shape[1]
    pad = GEN - n % GEN
    padded = np.concatenate([np.zeros((2, TRIM)), mix, np.zeros((2, pad + TRIM))], 1)
    out = []
    for i in range(0, n + pad, GEN):
        chunk = padded[:, i:i + CHUNK]
        spec = sess.run(None, {"input": stft(chunk)})[0]
        out.append(istft(spec)[:, TRIM:-TRIM])
    return np.concatenate(out, 1)[:, :n] * COMPENSATE


def main():
    so = ort.SessionOptions()
    so.intra_op_num_threads = 4
    sess = ort.InferenceSession(MODEL, so, providers=["CPUExecutionProvider"])
    for name in sys.argv[1:]:
        src = glob.glob(f"public/footage/{name}.*.mov")[0]
        out = f"public/footage/vlog-audio/{name}.voice.wav"
        t = time.time()
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vn", "-ac", "2", "-ar", str(SR),
                              "-f", "f32le", "-"], capture_output=True, check=True).stdout
        mix = np.frombuffer(raw, np.float32).reshape(-1, 2).T.astype(np.float64)
        voice = separate(mix, sess)
        sf.write(out, voice.T.astype(np.float32), SR, subtype="PCM_16")
        rest = mix - voice
        db = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
        print(f"{name}: {mix.shape[1] / SR:.0f}s in {time.time() - t:.0f}s | "
              f"mix {db(mix):.1f} dB, voice {db(voice):.1f} dB, removed {db(rest):.1f} dB", flush=True)


if __name__ == "__main__":
    main()
