#!/usr/bin/env bash
# Downloads footage from Google Drive straight into public/footage/.
#
# Usage:
#   scripts/fetch-footage.sh <drive-link-or-file-id> [more ...]
#   scripts/fetch-footage.sh            # reads links/IDs from footage-sources.txt
#
# Each file must be shared as "Anyone with the link". Files that are already
# downloaded are skipped, so the script is safe to run again (for example in a
# fresh cloud session, where earlier downloads are gone).
set -euo pipefail

cd "$(dirname "$0")/.."
OUT=public/footage
FFPROBE=node_modules/@remotion/compositor-linux-x64-gnu/ffprobe
mkdir -p "$OUT"

if [ $# -eq 0 ]; then
  [ -f footage-sources.txt ] || { echo "No links given and no footage-sources.txt" >&2; exit 1; }
  mapfile -t ARGS < <(grep -v '^\s*#' footage-sources.txt | grep -v '^\s*$')
else
  ARGS=("$@")
fi

# Pull the file ID out of the common Drive link shapes, or accept a bare ID.
to_id() {
  local s="$1"
  if [[ "$s" =~ /d/([A-Za-z0-9_-]{20,}) ]]; then echo "${BASH_REMATCH[1]}"
  elif [[ "$s" =~ [?\&]id=([A-Za-z0-9_-]{20,}) ]]; then echo "${BASH_REMATCH[1]}"
  elif [[ "$s" =~ ^[A-Za-z0-9_-]{20,}$ ]]; then echo "$s"
  else return 1; fi
}

fail=0
for arg in "${ARGS[@]}"; do
  id=$(to_id "$arg") || { echo "SKIP  not a Drive file link: $arg" >&2; fail=1; continue; }
  if ls "$OUT"/*."$id".* >/dev/null 2>&1; then echo "HAVE  $(ls "$OUT"/*."$id".*)"; continue; fi

  tmp=$(mktemp -d)
  # confirm=t skips Drive's "can't scan this large file for viruses" page.
  if ! (cd "$tmp" && curl -fsSL --retry 4 --retry-delay 3 -J -O \
      "https://drive.usercontent.google.com/download?id=${id}&export=download&confirm=t"); then
    echo "FAIL  $id: download refused. Is it shared as 'Anyone with the link'?" >&2
    rm -rf "$tmp"; fail=1; continue
  fi
  src=$(ls "$tmp"/* | head -1)
  name=$(basename "$src")
  # Drive returns an HTML page instead of the file when access is denied.
  if ! "$FFPROBE" -v error -show_entries format=duration -of csv=p=0 "$src" >/dev/null 2>&1; then
    echo "FAIL  $id: got '$name', which is not a video. Check the sharing setting." >&2
    rm -rf "$tmp"; fail=1; continue
  fi
  # Keep the original name but add the Drive ID so re-runs can find it.
  safe=$(echo "${name%.*}" | tr -c 'A-Za-z0-9_-' '_' | sed 's/_*$//')
  ext="${name##*.}"
  dest="$OUT/${safe}.${id}.${ext,,}"
  mv "$src" "$dest"; rm -rf "$tmp"
  info=$("$FFPROBE" -v error -select_streams v:0 \
    -show_entries stream=width,height:format=duration,size -of default=nw=1:nk=1 "$dest" | paste -sd' ')
  echo "OK    $dest  ($info)"
done
exit $fail
