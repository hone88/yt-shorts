#!/usr/bin/env bash
# 別の環境で動画づくりを始めるときに1回だけ実行する。
#   bash tools/setup.sh            … 道具とフォントをそろえる
set -e
cd "$(dirname "$0")/.."
command -v ffmpeg >/dev/null || { (apt-get install -y ffmpeg || sudo apt-get install -y ffmpeg) >/dev/null 2>&1 || echo "ffmpeg を入れてください"; }
python3 -c "import numpy, PIL" 2>/dev/null || pip install --break-system-packages -q numpy pillow || pip install -q numpy pillow
# 日本語フォントはリポジトリの fonts/ に入っている（システムにあればそちらを使う）
python3 -c "import sys; sys.path.insert(0,'loop_drama'); import engine; print('フォントOK:', engine.FONT_BLACK)"
echo "準備できました"
