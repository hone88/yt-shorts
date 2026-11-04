"""「もしもスカイツリーから1円玉を落としたら」背景8シーン。2D・720x1280・30fps・文字なし。
主役は y=553〜860 に置く（上は大きい字幕、下は字幕帯で隠れる）。
使い方: python3 coin.py stills / python3 coin.py 1,3,5"""
import math, random, subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, "/home/claude/air")
import air, air2
from air import W, H, FPS, sky, cl, mixc, SKIN

CLIPS = [3.4, 4.8, 4.8, 5.4, 4.8, 2.8, 5.6, 6.0]
XFRAC = 0.58     # 2シーン目で「いいえ」が来る位置（コインが頭に当たる）
SILVER, COPPER = (214, 220, 228), (196, 116, 70)


def ease(x):
    x = cl(x); return 0.5 - 0.5 * math.cos(math.pi * x)


def ground_city(d, y0=880):
    d.rectangle([0, y0, W, H], fill=(150, 155, 165))
    d.rectangle([0, y0 - 6, W, y0 + 4], fill=(200, 200, 205))


def skytree(d, cx, base, top, w=1.0):
    """シンプルなスカイツリー（白い格子の塔＋展望台2つ）。"""
    h = base - top
    def half(y):  # 下は広く、上は細い
        k = (base - y) / h
        return (70 * (1 - k) ** 1.6 + 9) * w
    pts_l = [(cx - half(y), y) for y in np.linspace(base, top + 30, 40)]
    pts_r = [(cx + half(y), y) for y in np.linspace(top + 30, base, 40)]
    d.polygon(pts_l + pts_r, fill=(236, 242, 250))
    for y in np.arange(base, top + 40, -26 * w):  # 格子
        a, b = half(y), half(y - 26 * w)
        d.line([(cx - a, y), (cx + b, y - 26 * w)], fill=(180, 196, 220), width=max(1, int(2 * w)))
        d.line([(cx + a, y), (cx - b, y - 26 * w)], fill=(180, 196, 220), width=max(1, int(2 * w)))
    for frac, r in ((0.55, 34), (0.7, 26)):  # 展望台
        y = base - h * frac
        d.rounded_rectangle([cx - r * w, y - 14 * w, cx + r * w, y + 14 * w], int(8 * w), fill=(200, 214, 236))
        d.rectangle([cx - r * w, y - 4 * w, cx + r * w, y + 4 * w], fill=(120, 160, 210))
    d.line([(cx, top + 30), (cx, top)], fill=(236, 242, 250), width=max(2, int(5 * w)))
    return base - h * 0.55  # 展望台の高さ


def coin(d, x, y, r, ang=0.0, col=SILVER):
    """回転して見えるコイン（ang=0で正面、π/2で真横）。"""
    sx = max(0.12, abs(math.cos(ang)))
    edge = mixc(col, (90, 95, 110), 0.45)
    d.ellipse([x - r * sx - 2, y - r - 2, x + r * sx + 2, y + r + 2], fill=edge)
    d.ellipse([x - r * sx, y - r, x + r * sx, y + r], fill=col)
    if sx > 0.4:
        d.ellipse([x - r * sx * 0.78, y - r * 0.78, x + r * sx * 0.78, y + r * 0.78], outline=mixc(col, (255, 255, 255), 0.5), width=max(1, int(r * 0.08)))
        d.ellipse([x - r * sx * 0.45, y - r * 0.6, x - r * sx * 0.1, y - r * 0.3], fill=mixc(col, (255, 255, 255), 0.7))


def sparkle(d, x, y, s, a=1.0):
    c = (int(255 * a), int(250 * a), int(200 * a))
    d.line([(x - s, y), (x + s, y)], fill=c, width=3); d.line([(x, y - s), (x, y + s)], fill=c, width=3)


def face(d, cx, cy, s, mood="normal", look_up=False):
    """大きな顔（アップ用）。mood: normal / worry / smile"""
    d.ellipse([cx - 120 * s, cy - 130 * s, cx + 120 * s, cy + 120 * s], fill=SKIN)
    d.pieslice([cx - 128 * s, cy - 150 * s, cx + 128 * s, cy + 40 * s], 180, 360, fill=(40, 28, 22))
    ey = cy - (25 if look_up else 5) * s
    for ex in (-45, 45):
        d.ellipse([cx + (ex - 13) * s, ey - 16 * s, cx + (ex + 13) * s, ey + 16 * s], fill=(30, 30, 40))
        d.ellipse([cx + (ex - 5) * s, ey - 12 * s, cx + (ex + 3) * s, ey - 4 * s], fill=(255, 255, 255))
    if mood == "worry":
        for ex, sg in ((-45, 1), (45, -1)):
            d.line([(cx + (ex - 22) * s, ey - (36 + 8 * sg) * s), (cx + (ex + 22) * s, ey - (36 - 8 * sg) * s)], fill=(40, 28, 22), width=int(8 * s))
        d.ellipse([cx - 18 * s, cy + 45 * s, cx + 18 * s, cy + 75 * s], fill=(140, 50, 60))
    elif mood == "smile":
        d.arc([cx - 45 * s, cy + 15 * s, cx + 45 * s, cy + 75 * s], 15, 165, fill=(140, 50, 60), width=int(9 * s))
        for ex in (-80, 80):
            d.ellipse([cx + (ex - 20) * s, cy + 15 * s, cx + (ex + 20) * s, cy + 35 * s], fill=(245, 170, 160))
    else:
        d.ellipse([cx - 14 * s, cy + 50 * s, cx + 14 * s, cy + 66 * s], fill=(140, 50, 60))


def body(d, cx, top, s):
    d.rounded_rectangle([cx - 150 * s, top, cx + 150 * s, H + 50], int(60 * s), fill=(255, 138, 61))


# ---------------------------------------------------------------- scenes
def c1(t):  # 明るい青空のスカイツリー。展望台からコインがキラッと落ちる
    img = sky(0, t); d = ImageDraw.Draw(img)
    ground_city(d)
    deck = skytree(d, 300, 1000, 1000 - 720, 2.2)
    air2.person(d, 560, 640, t, walk=False, look_up=True, scale=0.75)
    f = max(0.0, t - 0.25)
    y = deck + 20 + 70 * f + 12 * f * f
    x = 300 + 95 + 22 * math.sin(f * 5)
    coin(d, x, y, 16, f * 7)
    sparkle(d, x + 16, y - 16, 22 + 6 * math.sin(t * 9))
    return img


def c2(t):  # 見上げる顔のアップ → コインがコツンと当たって、ほっとする
    T = CLIPS[1]; hit = T * XFRAC
    img = sky(0, t); d = ImageDraw.Draw(img)
    air.city(img, 0); d = ImageDraw.Draw(img)
    body(d, 360, 900, 1.2)
    mood = "worry" if t < hit else "smile"
    face(d, 360, 760, 1.15, mood, look_up=t < hit)
    if t < hit:
        k = t / hit
        y = 520 + 120 * k ** 1.5; x = 360 + 30 * math.sin(k * 9)
        coin(d, x, y, 22, k * 12)
    else:
        k = t - hit
        x = 360 + 140 * k; y = 600 - 120 * k + 260 * k * k
        coin(d, x, y, 22, k * 15)
        if k < 0.6:
            for a in range(0, 360, 45):
                r = 40 + 80 * k
                sparkle(d, 360 + r * math.cos(math.radians(a)), 610 + r * 0.6 * math.sin(math.radians(a)), 10, 1 - k / 0.6)
    return img


def c3(t):  # コインのアップ。木の葉のようにひらひら（遠くにスカイツリー）
    img = sky(0, t); d = ImageDraw.Draw(img)
    skytree(d, 600, 1300, 380, 0.7)
    trail = []
    for i in range(12):
        tt = t - i * 0.07
        x = 360 + 150 * math.sin(tt * 2.6); y = 700 + 30 * math.sin(tt * 5.2)
        trail.append((x, y, tt))
    for i, (x, y, tt) in enumerate(reversed(trail)):
        a = (i + 1) / len(trail)
        c = mixc((200, 220, 245), (255, 255, 255), a)
        d.ellipse([x - 5 * a, y - 5 * a, x + 5 * a, y + 5 * a], fill=c)
    x, y, tt = trail[0]
    coin(d, x, y, 70, math.sin(t * 2.6) * 1.2)
    for k in range(5):  # 空気の流れ
        yy = 560 + k * 70 + 20 * math.sin(t * 3 + k)
        xx = (k * 170 - t * 220) % (W + 200) - 100
        d.arc([xx - 60, yy - 20, xx + 60, yy + 20], 200, 340, fill=(255, 255, 255), width=4)
    return img


def c4(t):  # スピードメーター：針が上がって、途中でピタッと止まる
    T = CLIPS[3]
    img = sky(0, t); d = ImageDraw.Draw(img)
    cx, cy, R = 360, 760, 210
    d.ellipse([cx - R - 14, cy - R - 14, cx + R + 14, cy + R + 14], fill=(30, 41, 59))
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(248, 250, 252))
    for i in range(11):  # 目盛り（210°〜-30°）
        a = math.radians(210 - i * 24)
        r0 = R - (34 if i % 2 == 0 else 20)
        d.line([(cx + r0 * math.cos(a), cy - r0 * math.sin(a)), (cx + (R - 6) * math.cos(a), cy - (R - 6) * math.sin(a))], fill=(30, 41, 59), width=6 if i % 2 == 0 else 3)
    d.arc([cx - R + 10, cy - R + 10, cx + R - 10, cy + R - 10], -30 - 0, 30 + 0 - 60 + 60 - 60 + 30, fill=(239, 68, 68), width=14)
    lim = 210 - 4 * 24  # ここで頭打ち
    k = ease(min(1.0, t / (T * 0.4)))
    ang = 210 - (210 - lim) * k + (2 * math.sin(t * 20) if k >= 1 else 0)
    a = math.radians(ang)
    d.line([(cx, cy), (cx + (R - 40) * math.cos(a), cy - (R - 40) * math.sin(a))], fill=(239, 68, 68), width=12)
    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=(30, 41, 59))
    # 横で落ちるコイン
    coin(d, 600, (520 + t * 180) % 420 + 520, 26, t * 8, COPPER)
    if k >= 1:  # 「止まった」マーク：針の先がキラッ
        sparkle(d, cx + (R - 40) * math.cos(a), cy - (R - 40) * math.sin(a), 14 + 4 * math.sin(t * 10))
    return img


def c5(t):  # 1セント（銅色・重い）と1円（銀・軽い）が並んで落ちる
    img = sky(0, t); d = ImageDraw.Draw(img)
    for x, col, sp, r in ((210, COPPER, 150, 72), (510, SILVER, 80, 72)):
        y = 540 + (t * sp) % 360
        for i in range(1, 8):
            yy = y - i * sp * 0.06
            d.ellipse([x - 4, yy - 4, x + 4, yy + 4], fill=mixc((200, 220, 245), (255, 255, 255), 1 - i / 8))
        coin(d, x + (20 * math.sin(t * 4) if col == SILVER else 0), y, r, t * (9 if col == COPPER else 4), col)
    return img


def c6(t):  # デコピン：指でおでこをピン
    img = sky(0, t); air.city(img, 0); d = ImageDraw.Draw(img)
    body(d, 360, 920, 1.2)
    hitT = 0.9
    mood = "smile" if t > hitT + 0.25 else "normal"
    face(d, 360, 780, 1.15, mood)
    k = cl((t - 0.3) / 0.6)
    hx = 610 - 90 * ease(k); hy = 660
    d.ellipse([hx - 60, hy - 50, hx + 60, hy + 50], fill=(232, 180, 145))   # こぶし
    fl = 1 if t > hitT else 0
    d.rounded_rectangle([hx - 120 + 20 * (1 - fl), hy - 18, hx - 20, hy + 6], 12, fill=(232, 180, 145))  # 伸びる指
    if hitT < t < hitT + 0.5:
        a = 1 - (t - hitT) / 0.5
        for ang in range(0, 360, 60):
            r = 30 + 40 * (1 - a)
            sparkle(d, 250 + r * math.cos(math.radians(ang)), 650 + r * math.sin(math.radians(ang)), 9, a)
    return img


def c7(t):  # スマホとペンが落ちる＋赤い注意マーク
    img = sky(0, t); d = ImageDraw.Draw(img)
    ov = Image.new("RGB", (W, H), (239, 68, 68))
    img = Image.blend(img, ov, 0.18 + 0.06 * math.sin(t * 6))
    d = ImageDraw.Draw(img)
    y1 = 520 + (t * 260) % 420; y2 = 480 + (t * 300 + 200) % 460
    d.rounded_rectangle([170, y1 - 80, 260, y1 + 80], 16, fill=(30, 35, 45))
    d.rounded_rectangle([180, y1 - 68, 250, y1 + 64], 8, fill=(90, 140, 220))
    ang = t * 3
    px, py = 540, y2
    dx, dy = 90 * math.cos(ang), 90 * math.sin(ang)
    d.line([(px - dx, py - dy), (px + dx, py + dy)], fill=(40, 90, 200), width=18)
    d.line([(px + dx * 0.8, py + dy * 0.8), (px + dx, py + dy)], fill=(230, 230, 235), width=18)
    s = 1 + 0.06 * math.sin(t * 8)  # 注意マーク
    cx, cy = 360, 720
    d.polygon([(cx, cy - 110 * s), (cx - 125 * s, cy + 100 * s), (cx + 125 * s, cy + 100 * s)], fill=(250, 204, 21), outline=(30, 30, 30))
    d.rounded_rectangle([cx - 13 * s, cy - 50 * s, cx + 13 * s, cy + 40 * s], 8, fill=(30, 30, 30))
    d.ellipse([cx - 15 * s, cy + 55 * s, cx + 15 * s, cy + 85 * s], fill=(30, 30, 30))
    return img


def c8(t):  # 1円玉を持ってにっこり、うしろにスカイツリー
    img = sky(0, t); d = ImageDraw.Draw(img)
    skytree(d, 600, 1300, 300, 0.9)
    body(d, 330, 930, 1.2)
    face(d, 330, 790, 1.1, "smile")
    hx, hy = 520, 830 + 8 * math.sin(t * 2)
    d.ellipse([hx - 50, hy - 40, hx + 50, hy + 50], fill=(232, 180, 145))
    coin(d, hx, hy - 70, 44, 0.3 * math.sin(t * 2))
    sparkle(d, hx + 40, hy - 110, 12 + 4 * math.sin(t * 5))
    return img


SCENES = [c1, c2, c3, c4, c5, c6, c7, c8]


def render(i):
    fn, sec = SCENES[i - 1], CLIPS[i - 1]
    os.makedirs("coin_clips", exist_ok=True)
    tmp, final = f"coin_clips/{i:02d}.part.mp4", f"coin_clips/{i:02d}.mp4"
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
        ts = [(0, 0.1), (0, 1.5), (1, 1.0), (1, 3.5), (2, 1.0), (3, 3.0), (4, 1.5), (5, 1.2), (6, 1.0), (7, 2.0)]
        sheet = Image.new("RGB", (W // 4 * 5, H // 4 * 2))
        for k, (i, t) in enumerate(ts):
            im = SCENES[i](t).resize((W // 4, H // 4))
            dd = ImageDraw.Draw(im, "RGBA")
            dd.rectangle([0, int(H / 4 * 0.36), W // 4, int(H / 4 * 0.43)], fill=(255, 0, 0, 60))
            dd.rectangle([0, int(H / 4 * 0.68), W // 4, H // 4], fill=(0, 0, 255, 50))
            sheet.paste(im, ((k % 5) * W // 4, (k // 5) * H // 4))
        sheet.save("coin_stills.png")
    else:
        for i in map(int, sys.argv[1].split(",")):
            render(i)
