# Preparing the ClipEdit files

All of these land in `public/footage/` (not committed). Run from `my-video/`.

```bash
scripts/fetch-footage.sh   # downloads the clips listed in footage-sources.txt

# Clip: convert the phone's HDR to normal video with natural color
python3 scripts/remove-neck-strip.py public/footage/copy_*1ip5nNU*.mov 0 29.05 \
  public/footage/clip2-sdr.mp4 --plain

# Song: one exact loop (26.4333s from where the music starts at 1.531s,
# plus 27ms to cancel the AAC encoder delay)
ffmpeg -ss 1.558 -t 26.4333 -i public/footage/ScreenRecording_*1FC0SKf*.mp4 \
  -vn -c:a aac -b:a 256k public/footage/clip2-song.m4a

npx remotion render ClipEdit out/clip-edit.mp4
```
