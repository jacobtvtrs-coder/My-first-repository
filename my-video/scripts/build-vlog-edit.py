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
    ("IMG_3065", 24.85, 33.20, "in", "fade"),
    # The Spanish attempt
    ("IMG_3065", 41.00, 45.00, "none", "cut"),
    ("IMG_3065", 58.45, 64.70, "in", "cut"),
    ("IMG_3065", 65.90, 66.75, "punch", "cut"),
    ("IMG_3065", 73.60, 79.10, "none", "cut"),
    ("IMG_3065", 79.15, 84.95, "in", "cut"),
    ("IMG_3065", 85.10, 89.30, "punch", "cut"),
    ("IMG_3065", 105.65, 108.75, "none", "cut"),
    ("IMG_3065", 113.75, 116.55, "punch", "cut"),
    ("IMG_3065", 118.00, 120.80, "out", "cut"),
    # How long have they known each other
    ("IMG_3065", 121.55, 128.10, "in", "fade"),
    # The wife found the barbershop
    ("IMG_3065", 150.30, 154.05, "none", "fade"),
    ("IMG_3065", 162.55, 169.45, "in", "cut"),
    ("IMG_3065", 178.05, 179.95, "punch", "cut"),
    # "It's a script" / "this is real"
    ("IMG_3065", 191.55, 196.85, "out", "cut"),
    # Why he keeps coming back
    ("IMG_3065", 233.70, 239.45, "in", "fade"),
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
    ("IMG_3066", 19.60, 20.80, "punch", "cut"),
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


def main():
    words = load_words()
    segments, captions = [], {}
    for clip, a, b, zoom, tr in SHOTS:
        seg = {"clip": clip, "inSec": a, "outSec": b, "zoom": zoom, "transition": tr}
        if clip in FOCUS:
            seg["focus"] = FOCUS[clip]
        if clip not in words:
            seg["mute"] = True  # angle shots: no talking, so no sound
        segments.append(seg)
        if clip in words:
            captions.setdefault(clip, []).extend(lines_for(clip, words[clip], a, b))
    total = sum(round((s["outSec"] - s["inSec"]) * 30) for s in segments)
    overlaps = sum(8 for i, s in enumerate(segments) if i and s["transition"] != "cut")
    json.dump({"segments": segments, "captions": captions},
              open("public/footage/vlog/edit.json", "w"), ensure_ascii=False, indent=1)
    secs = (total - overlaps) / 30
    print(f"{len(segments)} shots, {secs:.1f}s ({int(secs // 60)}:{secs % 60:04.1f}), "
          f"{sum(len(v) for v in captions.values())} subtitle lines")


if __name__ == "__main__":
    main()
