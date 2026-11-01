#!/usr/bin/env bash
# 別の環境で動画づくりを始めるときに1回だけ実行する。
#   bash tools/setup.sh            … 道具とフォントをそろえる
set -e
cd "$(dirname "$0")/.."
command -v ffmpeg >/dev/null || { (apt-get install -y ffmpeg || sudo apt-get install -y ffmpeg) >/dev/null 2>&1 || echo "ffmpeg を入れてください"; }
python3 -c "import numpy, PIL" 2>/dev/null || pip install --break-system-packages -q numpy pillow || pip install -q numpy pillow
if [ ! -f /usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc ] && [ ! -f fonts/NotoSansCJKjp-Black.otf ]; then
  (apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra >/dev/null 2>&1) || true
  if [ ! -f /usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc ]; then
    mkdir -p fonts
    for w in Black Bold; do
      curl -sSfL -o fonts/NotoSansCJKjp-$w.otf "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-$w.otf"
    done
  fi
fi
python3 -c "import sys; sys.path.insert(0,'loop_drama'); import engine; print('フォントOK:', engine.FONT_BLACK)"
echo "準備できました"
