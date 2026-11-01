"""空気の回・作り直し版（重力の型）。1コマ目から明るい街と人。
使い方: python3 air2.py stills <秒> / python3 air2.py 1,3,5"""
import math, random, subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, "/home/claude/air")
import air
from air import W, H, FPS, sky, city, cl, SKIN

CLIPS = [2.3, 3.8, 5.7, 4.4, 5.1, 4.2, 5.1, 5.9]
FLIP = 0.5


def ground(d, k):
    d.rectangle([0, 885, W, H], fill=air.mixc((150, 155, 165), (45, 48, 58), k))
    d.rectangle([0, 880, W, 890], fill=air.mixc((200, 200, 205), (70, 72, 84), k))


def person(d, cx, top, t, walk=True, look_up=False, scale=1.0):
    s = scale
    bob = 6 * abs(math.sin(t * 6)) if walk else 0
    y = top - bob
    sw = 22 * math.sin(t * 6) if walk else 0
    # 脚
    d.line([(cx - 25 * s, y + 250 * s), (cx - 25 * s - sw * s, y + 330 * s)], fill=(60, 70, 120), width=int(30 * s))
    d.line([(cx + 25 * s, y + 250 * s), (cx + 25 * s + sw * s, y + 330 * s)], fill=(60, 70, 120), width=int(30 * s))
    # 腕
    d.line([(cx - 75 * s, y + 130 * s), (cx - 95 * s + sw * s, y + 240 * s)], fill=SKIN, width=int(24 * s))
    d.line([(cx + 75 * s, y + 130 * s), (cx + 95 * s - sw * s, y + 240 * s)], fill=SKIN, width=int(24 * s))
    d.rounded_rectangle([cx - 80 * s, y + 110 * s, cx + 80 * s, y + 265 * s], int(40 * s), fill=(255, 138, 61))
    d.ellipse([cx - 58 * s, y, cx + 58 * s, y + 120 * s], fill=SKIN)
    d.pieslice([cx - 62 * s, y - 6 * s, cx + 62 * s, y + 80 * s], 180, 360, fill=(40, 28, 22))
    ey = y + (48 if look_up else 62) * s
    for ex in (-22, 22):
        d.ellipse([cx + (ex - 7) * s, ey - 7 * s, cx + (ex + 7) * s, ey + 7 * s], fill=(30, 30, 40))
    d.ellipse([cx - 10 * s, y + 88 * s, cx + 10 * s, y + 104 * s], fill=(140, 50, 60))


def a1(t):  # 明るい街を歩く人 → 0.5秒で空が真っ黒
    k = cl((t - FLIP) / 0.12)
    img = city(sky(k, t), k)
    d = ImageDraw.Draw(img)
    ground(d, k)
    person(d, 360, 560, t, walk=t < FLIP + 0.1, look_up=t > FLIP + 0.2)
    if FLIP <= t < FLIP + 0.3:
        a = 1 - (t - FLIP) / 0.3
        img = Image.fromarray((np.asarray(img, float) * (1 - 0.5 * a) + 127 * a).astype(np.uint8))
    return img


def a2(t):  # 体がふくらむ…？ → 大きな×、ふつうの体のまま
    img = city(sky(1, t), 1)
    d = ImageDraw.Draw(img)
    ground(d, 1)
    puff = 1 + 0.25 * cl(t / 1.2) * (1 if t < 1.8 else 0)
    if t < 1.8:  # 風船みたいにふくらむ想像（点線の輪郭）
        r = 175 * puff
        for a in range(0, 360, 12):
            x0 = 360 + r * math.cos(math.radians(a)); y0 = 700 + r * 1.15 * math.sin(math.radians(a))
            d.ellipse([x0 - 10, y0 - 10, x0 + 10, y0 + 10], fill=(255, 120, 130))
    sc = puff if t < 1.8 else 1.0
    person(d, 360, 885 - 330 * sc, t, walk=False, scale=sc)
    if t >= 1.8:  # ×
        a = cl((t - 1.8) / 0.15)
        L = 190 * a
        for sgn in (1, -1):
            d.line([(360 - L, 700 - L * sgn), (360 + L, 700 + L * sgn)], fill=(239, 68, 68), width=26)
    return img


def a8(t):  # 黒い空を見上げる人と、赤く減っていくリング（戻らなかったら？）
    img = city(sky(1, t), 1)
    d = ImageDraw.Draw(img)
    cx, cy = 360, 700
    d.ellipse([cx - 175, cy - 175, cx + 175, cy + 175], fill=(20, 22, 34))
    gone = int(cl(t / 4.5) * 10)
    for i in range(10):
        a0 = -90 + i * 36 + 3
        col = (239, 68, 68) if i < gone else (90, 95, 115)
        d.arc([cx - 160, cy - 160, cx + 160, cy + 160], a0, a0 + 30, fill=col, width=26)
    person(d, cx, cy - 100, t, walk=False, look_up=True, scale=0.62)
    return img


SCENES = [a1, a2, air.s2, air.s3, air.s4, air.s5, air.s7, a8]


def render(i):
    fn, sec = SCENES[i - 1], CLIPS[i - 1]
    os.makedirs("clips2", exist_ok=True)
    tmp, final = f"clips2/{i:02d}.part.mp4", f"clips2/{i:02d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                          "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for f in range(int(sec * FPS)):
        p.stdin.write(fn(f / FPS).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, final); print("ok", final)


if __name__ == "__main__":
    if sys.argv[1] == "stills":
        ts = [float(x) for x in sys.argv[2].split(",")]
        ims = [a1(ts[0]), a1(ts[1]), a2(1.0), a2(2.2), a8(1.0), a8(4.0)]
        sheet = Image.new("RGB", (W // 3 * 6, H // 3))
        for k, im in enumerate(ims):
            sheet.paste(im.resize((W // 3, H // 3)), (k * W // 3, 0))
        sheet.save("still2.png")
    else:
        for i in map(int, sys.argv[1].split(",")):
            render(i)
