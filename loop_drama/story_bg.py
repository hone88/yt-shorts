"""インスタのストーリー用アンケート背景（1080×1920）。真ん中を空け、すみに小さいカナタとミオ。
python3 story_bg.py → out_story/ストーリー背景_説明会アンケート.png"""
import math, os
from PIL import Image, ImageDraw, ImageFilter
import g3d as G
from g3d import Camera, Rig, render
import characters as C
import engine as E

W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_story"
BG = E.sky((255, 255, 255), (255, 255, 255)).convert("RGB").resize((W * G.SS, H * G.SS))


def cutout(spec, expr, yaw, pose, tag):
    """キャラクターを全身で描いて、背景を抜く"""
    r = Rig(spec, (0, 0, 0), yaw, tag=tag)
    r.set(**pose)
    r.expr = expr
    cam = Camera((0.0, -4.6, 1.15), (0.0, 0.0, 1.0), 34)
    img, mask = render(r.boxes(), cam, BG, keep={tag})
    img = img.convert("RGBA")
    img.putalpha(mask.convert("L").resize(img.size) if mask.size != img.size else mask.convert("L"))
    return img.crop(img.getbbox())


def shadow(im):
    a = im.getchannel("A").filter(ImageFilter.GaussianBlur(10))
    sh = Image.new("RGBA", im.size, (40, 60, 120, 0))
    sh.putalpha(a.point(lambda v: int(v * 0.25)))
    return sh


def place(bg, im, cx, bottom, h):
    s = h / im.height
    im = im.resize((int(im.width * s), h), Image.LANCZOS)
    x, y = int(cx - im.width / 2), int(bottom - h)
    bg.alpha_composite(shadow(im), (x + 10, y + 12))
    bg.alpha_composite(im, (x, y))


def main():
    # 明るくシンプルな背景：うすい空色 → 白、ブロック調の小さな四角を少しだけ
    bg = E.sky((196, 226, 255), (255, 248, 236)).convert("RGBA").resize((W, H))
    d = ImageDraw.Draw(bg)
    for (x, y, s, c) in ((70, 300, 46, (255, 216, 77)), (930, 420, 36, (120, 190, 245)), (120, 1560, 30, (255, 138, 31)),
                         (960, 1500, 50, (230, 90, 90)), (900, 260, 24, (255, 138, 31)), (60, 1060, 26, (120, 190, 245)),
                         (1000, 1000, 28, (255, 216, 77))):
        d.rectangle([x, y, x + s, y + s], fill=c + (150,))
    kanata = cutout(C.KANATA, "open", math.pi - 0.35, dict(armL=0.05, armR=0.05, head_pitch=-0.05), "kanata")
    mio = cutout(C.MIO, "smile", math.pi + 0.35, dict(armL=0.05, armR=-2.8, armR_out=0.3), "mio")
    # 真ん中（y 520〜1400）はアンケート用に空ける
    place(bg, mio, 830, 560, 400)          # 右上：手をふるミオ
    place(bg, kanata, 230, 1740, 420)      # 左下：カナタ
    os.makedirs(OUT, exist_ok=True)
    p = f"{OUT}/ストーリー背景_説明会アンケート.png"
    bg.convert("RGB").save(p)
    print(p)


if __name__ == "__main__":
    main()
