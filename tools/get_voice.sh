#!/usr/bin/env bash
# VOICEVOX で作った声を voice-out ブランチから取り出す。
#   bash tools/get_voice.sh loop_ep2 loop_drama/voice/ep2
#   （tools/voice/loop_ep2.json を push → Actions「voice」が終わってから実行）
set -e
cd "$(dirname "$0")/.."
NAME="$1"; DEST="$2"
git fetch -q --force origin voice-out:refs/remotes/origin/voice-out
TMP=$(mktemp -d)
git archive origin/voice-out "$NAME" | tar -x -C "$TMP"
mkdir -p "$DEST"
find "$TMP/$NAME" -name '*.wav' -exec cp {} "$DEST"/ \;
ls "$DEST" | wc -l | xargs echo "取り出した声の数:"
