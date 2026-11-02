#!/usr/bin/env bash
# 前回のおさらい（前の話の名場面を数秒ずつ）を、完成した動画の頭につなぐ。
#   bash add_recap.sh <前回の完成動画> <今回の完成動画> <出力> "<開始秒 長さ>" ["<開始秒 長さ>" ...]
# 例：bash add_recap.sh 第1話.mp4 第2話.mp4 第2話_おさらい付き.mp4 "0 2.0" "6.0 1.5" "20.05 2.55" "24.8 1.8"
set -e
PREV="$1"; CUR="$2"; OUT="$3"; shift 3
HERE="$(cd "$(dirname "$0")" && pwd)"
TMP=$(mktemp -d)
HERE_DIR="$HERE" python3 -c "
import sys; sys.path.insert(0, '$HERE')
from PIL import Image, ImageDraw
import engine as E
im = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
f = E.font(E.FONT_BLACK, 46); txt = '◀◀ 前回のガクチカ・ループ'; w = f.getlength(txt) + 60
d.rounded_rectangle([540 - w / 2, 1540, 540 + w / 2, 1610], radius=35, fill=(200, 40, 50, 235))
d.text((540 - w / 2 + 30, 1548), txt, font=f, fill=(255, 255, 255))
im.save('$TMP/label.png')"
i=0; IN=(); FC=""
for seg in "$@"; do
  set -- $seg
  END=$(python3 -c "print($2 - 0.08)")
  ffmpeg -v error -y -ss $1 -t $2 -i "$PREV" -i "$TMP/label.png" -filter_complex \
    "[0:v][1:v]overlay=0:0,format=yuv420p[v];[0:a]afade=t=in:d=0.05,afade=t=out:st=$END:d=0.08,aresample=48000[a]" \
    -map "[v]" -map "[a]" -r 30 -c:v libx264 -preset veryfast -crf 19 -c:a aac -b:a 192k "$TMP/seg$i.mp4"
  IN+=(-i "$TMP/seg$i.mp4"); FC="$FC[$i:v][$i:a]"; i=$((i+1))
done
IN+=(-i "$CUR"); FC="$FC[$i:v][$i:a]"; n=$((i+1))
ffmpeg -v error -y "${IN[@]}" -filter_complex "${FC}concat=n=$n:v=1:a=1[v][a]" -map "[v]" -map "[a]" \
  -c:v libx264 -preset veryfast -crf 19 -pix_fmt yuv420p -c:a aac -b:a 192k "$OUT"
rm -rf "$TMP"
