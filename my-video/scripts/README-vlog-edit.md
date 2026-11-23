# Preparing the VlogEdit files

Everything generated lands in `public/footage/` (not committed: it contains
the footage and the transcript of a private conversation). Run from `my-video/`.

```bash
scripts/fetch-footage.sh                 # download the clips from Google Drive
scripts/convert-vlog.sh                  # 4K HDR -> 1080x1920 natural color
# 16kHz audio for transcription
for f in public/footage/IMG_30*.mov; do n=$(basename $f | cut -d. -f1);
  ffmpeg -i $f -vn -ac 1 -ar 16000 public/footage/vlog-audio/$n.16k.wav; done
python3 scripts/transcribe-vlog.py medium   # needs faster-whisper + Hugging Face access
# (the Spanish section of IMG_3065, 37.5-121s, is re-transcribed with language="es"
#  into IMG_3065.es.json)
python3 scripts/clean-vlog-audio.py      # denoise + silence between speech
python3 scripts/build-vlog-edit.py       # shot list + subtitles -> edit.json
npx remotion render VlogEdit out/vlog-edit.mp4
```
