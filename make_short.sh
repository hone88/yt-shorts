#!/usr/bin/env bash
# 使い方: CHANNEL=moshimo ./make_short.sh   （省略時は ai1h）
# 台本 → 背景画像 → 音声 → 動画 を順に実行する。出力は out/<チャンネル>/ に入る。
set -euo pipefail
cd "$(dirname "$0")"
export CHANNEL="${CHANNEL:-ai1h}"
OUT="out/$CHANNEL"
rm -rf "$OUT" && mkdir -p "$OUT"
python3 generate_script.py "$OUT/script.json"
python3 images.py "$OUT/script.json"
python3 tts.py "$OUT/script.json"
python3 render.py "$OUT/script.json"
