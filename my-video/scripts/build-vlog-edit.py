"""Builds public/footage/vlog/edit.json for the VlogEdit composition: the shot
list (which moments of which clip, zooms, transitions) and word-timed
subtitles for the talking parts.

The shot list below was chosen from the transcript. Subtitles come from the
transcription (French, plus the Spanish section re-transcribed in Spanish),
with obvious recognition errors corrected and unclear words left out.
Usage: python3 scripts/build-vlog-edit.py
"""

import json
import re

A = "public/footage/vlog-audio/"

# (clip, in, out, zoom, transition-in)
# zoom: none | in (slow push in) | out (slow pull out) | punch (comedy jump zoom)
SHOTS = [
    # Cold open: the reaction, as a hook
    ("IMG_3066", 37.55, 39.70, "punch", "cut"),
    # Setup
    ("IMG_3065", 24.85, 30.45, "in", "fade"),
    # The Spanish attempt: just the beginning
    ("IMG_3065", 41.00, 45.00, "none", "cut"),
    ("IMG_3065", 58.45, 64.70, "in", "cut"),
    ("IMG_3065", 65.90, 66.75, "punch", "cut"),
    # How long have they known each other
    ("IMG_3065", 121.55, 128.10, "in", "fade"),
    # The wife found the barbershop
    ("IMG_3065", 150.30, 154.05, "none", "fade"),
    ("IMG_3065", 163.75, 167.15, "in", "cut"),
    ("IMG_3065", 168.35, 169.45, "none", "cut"),
    ("IMG_3065", 178.05, 179.95, "punch", "cut"),
    # "It's a script" / "this is real"
    ("IMG_3065", 191.55, 196.85, "out", "cut"),
    # Why he keeps coming back
    ("IMG_3065", 235.30, 239.45, "in", "fade"),
    ("IMG_3065", 254.25, 257.40, "none", "cut"),
    ("IMG_3065", 259.80, 262.80, "in", "cut"),
    # The word hunt
    ("IMG_3065", 289.35, 294.25, "none", "fade"),
    ("IMG_3065", 296.10, 297.00, "punch", "cut"),
    ("IMG_3065", 299.25, 303.30, "in", "cut"),
    # Bloopers
    ("IMG_3065", 344.85, 351.30, "none", "fade"),
    ("IMG_3065", 354.90, 355.90, "punch", "cut"),
    ("IMG_3065", 373.50, 381.35, "in", "cut"),
    ("IMG_3065", 382.60, 384.15, "punch", "cut"),
    ("IMG_3065", 394.50, 398.95, "none", "cut"),
    # Ready? Let's go -> cape covers the lens -> straight to the result
    ("IMG_3065", 434.20, 437.70, "in", "cut"),
    ("IMG_3065", 452.40, 454.10, "none", "cut"),
    ("IMG_3066", 11.30, 17.70, "in", "cut"),
    ("IMG_3066", 19.60, 20.80, "none", "cut"),  # he leans out to the side: no zoom
    ("IMG_3066", 39.80, 43.40, "none", "cut"),
    ("IMG_3066", 45.10, 48.10, "out", "cut"),
    # The cut from every angle
    ("IMG_3067", 0.20, 1.80, "in", "fade"),
    ("IMG_3068", 0.30, 1.90, "out", "cut"),
    ("IMG_3071", 0.40, 2.00, "in", "cut"),
    ("IMG_3072", 1.00, 2.70, "out", "cut"),
    ("IMG_3073", 0.40, 2.00, "in", "cut"),
    # Logo
    ("IMG_3078", 0.60, 3.60, "out", "fade"),
]

# Thinking pauses inside the talking shots are cut out (jump cuts): a stretch
# with no words and no voice/laugh that lasts longer than PAUSE_MIN is removed,
# keeping PAUSE_KEEP of breathing room on each side.
PAUSE_MIN = 0.35
PAUSE_KEEP = 0.12
QUIET_DB = -42
TALK_CLIPS = {"IMG_3065", "IMG_3066"}
NO_PAUSE_CUT = {("IMG_3065", 452.40)}  # the cape sweep: keep it whole

# Suspense sound: starts on "Tu es prêt pour ta coupe ?" and hits on the cut
# to the finished haircut.
SUSPENSE_FROM = ("IMG_3065", 434.20)
SUSPENSE_HIT = ("IMG_3066", 11.30)

# Recognition fixes (whole-word, case-sensitive) and words to leave out.
FIXES = {"Moldière.": "Molière.", "estiliste.": "styliste.", "estiliste,": "styliste,",
         "llegas": "llevas", "llegas?": "llevas?", "llegas,": "llevas,", "conmigo?": "conmigo?",
         "table,": "taper,", "J?": "Jay?", "G?": "Jay?", "Cabelo.": "Cabello.",
         "Coche": "Corte", "cabelo.": "cabello."}
DROP = re.compile(r"^(Deo\??|Si|se|encana,|Scrop|scrop|de|don\.?|don,|non,)$")
DROP_RANGES = {"IMG_3065": [(76.0, 77.0), (296.95, 301.10)]}  # unclear words
# Faces sit in the upper-middle of these shots; zoom towards them.
FOCUS = {"IMG_3065": "52% 33%", "IMG_3066": "50% 30%"}


def load_words():
    words = {}
    fr = json.load(open(A + "IMG_3065.json"))["segments"]
    es = json.load(open(A + "IMG_3065.es.json"))
    w65 = [w for s in fr if not (37.5 <= s["start"] < 121) for w in s["words"]]
    w65 += [w for s in es for w in s["words"]]
    words["IMG_3065"] = sorted(w65, key=lambda w: w["start"])
    w66 = [w for s in json.load(open(A + "IMG_3066.json"))["segments"] for w in s["words"]]
    for w in w66:  # one word was timed across a long silence
        w["end"] = min(w["end"], w["start"] + 1.0)
    words["IMG_3066"] = w66
    return words


def merge_tokens(ws):
    """Join pieces like ' c' + "'est" into one word."""
    out = []
    for w in ws:
        if out and not w["word"].startswith(" ") and w["start"] - out[-1]["end"] < 0.4:
            out[-1] = {**out[-1], "word": out[-1]["word"] + w["word"], "end": w["end"]}
        else:
            out.append(dict(w))
    return out


def lines_for(clip, ws, a, b):
    ws = [w for w in ws if a - 0.05 <= w["start"] < b - 0.05]
    ws = [w for w in ws if not any(x <= w["start"] < y for x, y in DROP_RANGES.get(clip, []))]
    ws = [{**w, "word": w["word"].replace("«", "").replace("»", "")} for w in ws]
    ws = [w for w in ws if w["word"].strip()]
    ws = merge_tokens(ws)
    cleaned = []
    for w in ws:
        t = w["word"].strip()
        if DROP.match(t) and any(x - 2 <= w["start"] <= y + 2 for x, y in DROP_RANGES.get(clip, [])):
            continue
        t = FIXES.get(t, t)
        if re.fullmatch(r"[?!.,]+", t):  # stray punctuation token: attach to previous word
            if cleaned:
                cleaned[-1]["word"] += t
            continue
        t = t.replace("« ", "").replace(" »", "").replace("«", "").replace("»", "")
        if not t:
            continue
        cleaned.append({"start": w["start"], "end": min(w["end"], b), "word": t})

    # group into short lines that break at natural pauses: after punctuation
    # once a line has 2+ words, or when it gets long, or on a pause
    lines, cur = [], []
    for w in cleaned:
        if cur and (len(cur) >= 5 or len(" ".join(x["word"] for x in cur + [w])) > 26
                    or w["start"] - cur[-1]["end"] > 0.6):
            lines.append(cur)
            cur = []
        cur.append(w)
        if re.search(r"[.?!,…]$", w["word"]) and (len(cur) >= 2 or re.search(r"[.?!]$", w["word"])):
            lines.append(cur)
            cur = []
    if cur:
        lines.append(cur)
    # a lone short word left at the end of a sentence joins the previous line
    fixed = []
    for ln in lines:
        if (fixed and len(ln) == 1 and len(ln[0]["word"]) <= 6 and not re.search(r"[?!]$", ln[0]["word"])
                and ln[0]["start"] - fixed[-1][-1]["end"] < 0.3
                and len(" ".join(x["word"] for x in fixed[-1] + ln)) <= 30):
            fixed[-1] = fixed[-1] + ln
        else:
            fixed.append(ln)
    lines = fixed

    caps = []
    for i, ln in enumerate(lines):
        end = ln[-1]["end"] + 0.35
        if i + 1 < len(lines):
            end = min(end, lines[i + 1][0]["start"])
        end = min(end, b)
        caps.append({"start": round(ln[0]["start"], 2), "end": round(end, 2),
                     "words": [{"start": x["start"], "end": x["end"],
                                "word": (" " if j else "") + x["word"]} for j, x in enumerate(ln)]})
    return caps


def loudness(clip):
    import soundfile as sf
    import numpy as np
    y, sr = sf.read(A + f"{clip}.clean.wav", dtype="float32")
    hop = sr // 100
    n = len(y) // hop
    rms = np.sqrt((y[: n * hop].reshape(n, hop) ** 2).mean(1))
    return 20 * np.log10(rms + 1e-9)  # one value per 10ms


def split_pauses(clip, a, b, ws, db):
    """Returns the (in, out) pieces of a shot with thinking pauses removed."""
    import numpy as np
    i0, i1 = int(a * 100), int(b * 100)
    busy = db[i0:i1] > QUIET_DB
    # a breath or creak shorter than 0.25s doesn't count as talking/laughing
    k = 0
    while k < len(busy):
        if busy[k]:
            j = k
            while j < len(busy) and busy[j]:
                j += 1
            if j - k < 25:
                busy[k:j] = False
            k = j
        else:
            k += 1
    for w in ws:
        x, y = int(w["start"] * 100) - i0, int(w["end"] * 100) - i0
        busy[max(0, x):max(0, y + 1)] = True
    pieces, start, k = [], a, 0
    while k < len(busy):
        if not busy[k]:
            j = k
            while j < len(busy) and not busy[j]:
                j += 1
            p0, p1 = a + k / 100, a + j / 100
            if p1 - p0 > PAUSE_MIN and k > 0 and j < len(busy):
                pieces.append((start, p0 + PAUSE_KEEP))
                start = p1 - PAUSE_KEEP
            k = j
        else:
            k += 1
    pieces.append((start, b))
    # very short pieces join their neighbour instead of flashing by
    merged = []
    for x, y in pieces:
        if merged and (y - x < 0.4 or merged[-1][1] - merged[-1][0] < 0.4):
            merged[-1] = (merged[-1][0], y) if y - x < 0.4 else (x, y) if False else (merged[-1][0], y)
        else:
            merged.append((x, y))
    return merged


def make_suspense(build_frames, out):
    """Synthesizes the suspense sound: an impact on the question, a low drone
    with a heartbeat while he answers, a rising whoosh over the cape, and a
    deep boom exactly on the cut to the result."""
    import numpy as np
    import soundfile as sf
    sr = 48000
    hit = build_frames / 30
    total = hit + 2.2
    t = np.arange(int(total * sr)) / sr
    rng = np.random.default_rng(3)
    y = np.zeros_like(t)

    def boom(at, freq0, freq1, decay, gain):
        tt = t - at
        on = tt >= 0
        ph = 2 * np.pi * np.cumsum(np.where(on, freq1 + (freq0 - freq1) * np.exp(-tt.clip(0) * 18), 0)) / sr
        env = np.where(on, np.exp(-tt.clip(0) / decay) * (1 - np.exp(-tt.clip(0) * 400)), 0)
        return gain * env * np.sin(ph)

    # 1) the "dun": low impact on the question
    y += boom(0.0, 120, 42, 0.9, 0.9)
    # 2) drone: two low detuned tones swelling until the hit, with slow tremolo
    swell = np.clip(t / hit, 0, 1) ** 1.5 * (t < hit)
    trem = 0.75 + 0.25 * np.sin(2 * np.pi * 3.2 * t)
    drone = (np.sin(2 * np.pi * 55 * t) + 0.6 * np.sin(2 * np.pi * 82.4 * t + 1)
             + 0.35 * np.sin(2 * np.pi * 110.7 * t + 2))
    y += 0.15 * (0.25 + 0.75 * swell) * trem * drone * (t < hit)
    # 3) heartbeat: double thump, speeding up towards the hit
    beat = 0.6
    k = 0.55
    while k < hit - 0.4:
        y += boom(k, 90, 50, 0.12, 0.55) + boom(k + 0.16, 85, 48, 0.12, 0.4)
        k += beat
        beat = max(0.32, beat * 0.9)
    # 4) riser over the last 1.8s: noise swept upward + rising tone
    r0 = max(0.0, hit - 1.8)
    rp = np.clip((t - r0) / (hit - r0), 0, 1) * (t < hit)
    noise = rng.standard_normal(len(t))
    # simple one-pole lowpass whose cutoff rises with the sweep
    lp = np.empty_like(noise)
    acc = 0.0
    for i in range(len(noise)):
        a = 0.02 + 0.5 * rp[i] ** 2
        acc += a * (noise[i] - acc)
        lp[i] = acc
    y += 0.35 * rp ** 2 * lp
    y += 0.12 * rp ** 2 * np.sin(2 * np.pi * np.cumsum(200 + 900 * rp ** 2) / sr)
    # 5) the hit: deep boom with a noisy crack, ringing out
    y += boom(hit, 160, 38, 1.1, 1.0)
    crack = np.where(t >= hit, np.exp(-(t - hit).clip(0) / 0.08), 0) * rng.standard_normal(len(t))
    y += 0.25 * crack
    # gentle fade at the very end, normalize to -3 dBFS peak
    y *= np.clip((total - t) / 0.4, 0, 1)
    y = y / np.abs(y).max() * 10 ** (-3 / 20)
    sf.write(out, np.stack([y, y], 1).astype(np.float32), sr, subtype="PCM_16")


def main():
    words = load_words()
    dbs = {c: loudness(c) for c in TALK_CLIPS}
    removed = 0.0
    first_index = {}
    segments, captions = [], {}
    for clip, a, b, zoom, tr in SHOTS:
        pieces = (split_pauses(clip, a, b, words[clip], dbs[clip])
                  if clip in TALK_CLIPS and (clip, a) not in NO_PAUSE_CUT else [(a, b)])
        first_index[(clip, a)] = len(segments)
        removed += (b - a) - sum(y - x for x, y in pieces)
        for k, (x, y) in enumerate(pieces):
            # first piece keeps the shot's zoom; after a jump cut, alternate
            # between normal and slightly closer framing (punch stays punch)
            z = zoom if (k == 0 or zoom == "punch") else ("jump" if k % 2 else "none")
            seg = {"clip": clip, "inSec": round(x, 2), "outSec": round(y, 2), "zoom": z,
                   "transition": tr if k == 0 else "cut"}
            if clip in FOCUS:
                seg["focus"] = FOCUS[clip]
            if clip not in words:
                seg["mute"] = True  # angle shots: no talking, so no sound
            segments.append(seg)
            if clip in words:
                captions.setdefault(clip, []).extend(lines_for(clip, words[clip], x, y))
    total = sum(round((s["outSec"] - s["inSec"]) * 30) for s in segments)
    overlaps = sum(8 for i, s in enumerate(segments) if i and s["transition"] != "cut")
    # edit-time frame where each segment starts (fades overlap by 8 frames)
    starts, f = [], 0
    for i, sg in enumerate(segments):
        if i and sg["transition"] != "cut":
            f -= 8
        starts.append(f)
        f += round((sg["outSec"] - sg["inSec"]) * 30)
    sfx_from = starts[first_index[SUSPENSE_FROM]]
    sfx_hit = starts[first_index[SUSPENSE_HIT]]
    make_suspense(sfx_hit - sfx_from, "public/footage/vlog-audio/suspense.wav")
    sfx = [{"file": "footage/vlog-audio/suspense.wav", "fromFrame": sfx_from, "volume": 0.32}]
    print(f"suspense: frame {sfx_from} -> hit at {sfx_hit} ({(sfx_hit - sfx_from) / 30:.2f}s build)")
    json.dump({"segments": segments, "captions": captions, "sfx": sfx},
              open("public/footage/vlog/edit.json", "w"), ensure_ascii=False, indent=1)
    secs = (total - overlaps) / 30
    print(f"pauses removed: {removed:.1f}s")
    print(f"{len(segments)} shots, {secs:.1f}s ({int(secs // 60)}:{secs % 60:04.1f}), "
          f"{sum(len(v) for v in captions.values())} subtitle lines")


if __name__ == "__main__":
    main()
