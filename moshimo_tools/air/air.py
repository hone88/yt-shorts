"""「もしも空気が10秒だけ消えたら」背景8シーン。720x1280・30fps・文字なし。
主役は y=553〜860 に置く（上は文字、下は字幕で隠れる）。
使い方: python3 air.py stills <秒>  /  python3 air.py 1,3,5"""
import math, random, subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, "/home/claude/yama")
from scenes import W, H, FPS, grad, glow, stars

CLIPS = [5.1, 4.3, 4.4, 5.6, 4.2, 4.2, 6.1, 5.6]
FLIP = 0.45  # 1シーン目で空が黒くなる時刻
SUN = (560, 300)
SKY_T, SKY_B = (70, 150, 235), (175, 215, 250)
BLK_T, BLK_B = (2, 3, 10), (8, 10, 22)


def cl(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def mixc(a, b, k):
    return tuple(int(x + (y - x) * k) for x, y in zip(a, b))


def sky(k, t):
    """k=0 青空, k=1 真っ黒（星と、にじまない太陽）"""
    img = grad(mixc(SKY_T, BLK_T, k), mixc(SKY_B, BLK_B, k))
    d = ImageDraw.Draw(img)
    if k > 0.3:
        stars(d, t, cl((k - 0.3) / 0.7))
    sx, sy = SUN
    if k < 1:
        def halo(g):
            a = 1 - k
            g.ellipse([sx - 90, sy - 90, sx + 90, sy + 90], fill=(int(255 * a), int(240 * a), int(190 * a)))
        img = glow(img, halo, 60, 1.0)
        d = ImageDraw.Draw(img)
    d.ellipse([sx - 46, sy - 46, sx + 46, sy + 46], fill=(255, 252, 235))
    return img


rc = random.Random(3)
BLD = []
x = -20
while x < W + 20:
    w = rc.randint(70, 130); h = rc.randint(330, 560)
    BLD.append((x, w, h, rc.random()))
    x += w + rc.randint(4, 14)


def city(img, k):
    d = ImageDraw.Draw(img)
    for x, w, h, r in BLD:
        top = H - h - 300
        base = mixc((95, 110, 140), (30, 34, 48), k)
        d.rectangle([x, top, x + w, H], fill=mixc(base, (60, 70, 95), r * 0.4))
        for wy in range(top + 18, H, 34):
            for wx in range(x + 12, x + w - 16, 26):
                lit = (hash((wx, wy)) % 5 == 0)
                c = mixc((180, 205, 235), (55, 62, 82), k)
                d.rectangle([wx, wy, wx + 12, wy + 18], fill=c)
    return img


def s1(t):  # 昼の街 → 一瞬で空が真っ黒
    k = cl((t - FLIP) / 0.12)
    img = city(sky(k, t), k)
    if FLIP <= t < FLIP + 0.3:  # 切り替わりの白いフラッシュ
        a = 1 - (t - FLIP) / 0.3
        arr = np.asarray(img, float) * (1 - 0.5 * a) + 255 * 0.5 * a
        img = Image.fromarray(arr.astype(np.uint8))
    return img


def s7(t):  # 黒い空 → 青空が戻る、風が吹き抜ける
    k = 1 - cl((t - 0.4) / 0.5)
    img = city(sky(k, t), k)
    d = ImageDraw.Draw(img)
    if t > 0.4:
        r = random.Random(8)
        for i in range(16):
            y = r.uniform(380, 860); sp = r.uniform(900, 1500); L = r.uniform(120, 260)
            xx = ((t - 0.4) * sp + r.uniform(0, W)) % (W + 400) - 200
            a = int(255 * cl((t - 0.4) / 0.4) * 0.8)
            d.line([(xx, y), (xx + L, y - 8)], fill=(a, a, a), width=4)
        for i in range(5):  # 鳥がまた飛ぶ
            bx = (t * 90 + i * 140) % (W + 100) - 50; by = 520 + 30 * math.sin(i * 2) + 8 * math.sin(t * 6 + i)
            f = 14 * math.sin(t * 12 + i)
            d.line([(bx - 22, by - f), (bx, by), (bx + 22, by - f)], fill=(30, 40, 60), width=5)
    return img


def street(t):
    img = sky(1, t)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 900, W, H], fill=(40, 42, 50))
    d.rectangle([0, 892, W, 904], fill=(80, 82, 92))
    return img, d


def s2(t):  # スピーカーは鳴っているのに、音の輪が消えていく
    img, d = street(t)
    cx, cy = 360, 700
    vib = 6 * math.sin(t * 60)
    d.rounded_rectangle([cx - 130, cy - 170, cx + 130, cy + 170], 30, fill=(48, 52, 66), outline=(120, 125, 145), width=5)
    for yy, rr in ((cy - 80, 50), (cy + 50, 90)):
        d.ellipse([cx - rr - vib / 2, yy - rr - vib / 2, cx + rr + vib / 2, yy + rr + vib / 2], fill=(20, 22, 30), outline=(150, 150, 170), width=4)
        d.ellipse([cx - rr * 0.35, yy - rr * 0.35, cx + rr * 0.35, yy + rr * 0.35], fill=(90, 95, 110))
    fade = 1 - cl((t - 0.2) / 0.8)  # 音の輪は最初だけ、すぐ消える
    for i in range(4):
        ph = (t * 1.2 + i * 0.25) % 1
        r = 170 + ph * 200
        a = int(230 * fade * (1 - ph))
        if a > 4:
            for side in (-1, 1):
                box = [cx - r, cy - r, cx + r, cy + r]
                d.arc(box, 180 - 35 if side < 0 else -35, 180 + 35 if side < 0 else 35, fill=(a, int(a * 0.85), int(a * 0.3)), width=8)
    if t > 1.0:  # 「消えた」ことを示す斜線つきの輪
        a = int(255 * cl((t - 1.0) / 0.4))
        c = (a, int(a * 0.25), int(a * 0.25))
        d.ellipse([cx - 230, cy - 230, cx + 230, cy + 230], outline=c, width=14)
        d.line([(cx - 160, cy + 160), (cx + 160, cy - 160)], fill=c, width=14)
    return img


def plane(d, cx, cy, ang, s=1.0):
    def R(px, py):
        c, sn = math.cos(ang), math.sin(ang)
        return cx + (px * c - py * sn) * s, cy + (px * sn + py * c) * s
    body = [R(-150, -14), R(130, -14), R(170, 0), R(130, 14), R(-150, 14)]
    d.polygon(body, fill=(235, 238, 245))
    d.polygon([R(-10, 0), R(40, 0), R(-40, 120), R(-70, 120)], fill=(200, 205, 220))
    d.polygon([R(-10, 0), R(40, 0), R(-40, -120), R(-70, -120)], fill=(215, 220, 232))
    d.polygon([R(-150, 0), R(-120, 0), R(-150, -60), R(-170, -60)], fill=(210, 60, 60))
    for k in range(6):
        wx, wy = R(-90 + k * 32, -4)
        d.ellipse([wx - 5, wy - 5, wx + 5, wy + 5], fill=(60, 90, 140))


def s3(t):  # 鳥と飛行機が落ちはじめる
    img = sky(1, t)
    d = ImageDraw.Draw(img)
    fall = 0.5 * 160 * max(0, t - 0.3) ** 2
    plane(d, 380 + 30 * t, 600 + fall * 0.6, 0.15 + 0.12 * t, 1.25)
    r = random.Random(2)
    for i in range(7):
        bx = r.uniform(60, 660); by = r.uniform(420, 560) + fall * r.uniform(0.8, 1.3)
        sp = r.uniform(1.5, 3)
        rot = t * sp
        for side in (-1, 1):
            ex = bx + side * 26 * math.cos(rot); ey = by - 20 * math.sin(rot + side)
            d.line([(bx, by), (ex, ey)], fill=(230, 230, 240), width=5)
        d.ellipse([bx - 6, by - 6, bx + 6, by + 6], fill=(230, 230, 240))
    for i in range(10):  # 落下を示す縦の線
        lx = r.uniform(80, 640); ly = (r.uniform(0, H) + t * 700) % H
        d.line([(lx, ly), (lx, ly + 60)], fill=(70, 75, 100), width=3)
    return img


SKIN = (241, 199, 163)


def s4(t):  # 横顔の人。肺がしぼみ、口から空気が出ていく
    img = sky(1, t)
    d = ImageDraw.Draw(img)
    cx = 330
    d.rounded_rectangle([cx - 150, 640, cx + 150, H], 80, fill=(255, 138, 61))  # 体
    d.ellipse([cx - 95, 420, cx + 95, 620], fill=SKIN)  # 顔
    d.pieslice([cx - 100, 405, cx + 100, 560], 180, 360, fill=(40, 28, 22))  # 髪
    d.ellipse([cx + 30, 485, cx + 48, 503], fill=(30, 30, 40))  # 目
    d.ellipse([cx + 72, 560, cx + 98, 580], fill=(140, 50, 60))  # 口
    k = cl(t / 3.0)
    for side in (-1, 1):  # 肺（しぼむ）
        w, h = 85 - 25 * k, 150 - 40 * k
        lx = cx + side * 62
        d.ellipse([lx - w / 2, 760 - h / 2, lx + w / 2, 760 + h / 2], fill=(240, 120, 140), outline=(255, 180, 190), width=4)
    d.line([(cx, 640), (cx, 700)], fill=(240, 120, 140), width=10)
    st = Image.new("RGB", (W, H)); sd = ImageDraw.Draw(st)
    r = random.Random(4)
    for i in range(22):  # 口から出ていく息
        ph = (t * 0.9 + i / 22) % 1
        x = cx + 100 + ph * 300 + r.uniform(-20, 20); y = 570 - ph * 120 + r.uniform(-40, 40)
        s = 10 + ph * 40; a = int(220 * (1 - ph))
        sd.ellipse([x - s, y - s, x + s, y + s], fill=(a, a, a))
    st = st.filter(ImageFilter.GaussianBlur(10))
    return Image.fromarray(np.clip(np.asarray(img, float) + np.asarray(st, float) * 0.7, 0, 255).astype(np.uint8))


def s5(t):  # 開いた口のアップ。舌の上のつばがぶくぶく
    img = grad((50, 20, 24), (30, 10, 14))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], fill=SKIN)
    cx, cy = 360, 700
    d.ellipse([cx - 300, cy - 210, cx + 300, cy + 210], fill=(200, 70, 80))  # 唇
    d.ellipse([cx - 255, cy - 170, cx + 255, cy + 170], fill=(70, 15, 25))  # 口の中
    d.rounded_rectangle([cx - 200, cy - 170, cx + 200, cy - 120], 18, fill=(250, 248, 240))  # 上の歯
    d.ellipse([cx - 210, cy - 20, cx + 210, cy + 190], fill=(225, 100, 115))  # 舌
    d.line([(cx, cy + 10), (cx, cy + 150)], fill=(200, 80, 95), width=6)
    r = random.Random(9)
    for i in range(40):
        bx = cx + r.uniform(-170, 170); by0 = cy + r.uniform(20, 140)
        ph = (t * r.uniform(0.8, 1.6) + r.random()) % 1
        if t < 0.3:
            continue
        rr = 6 + 16 * ph
        by = by0 - ph * 60
        a = 1 - ph * 0.6
        d.ellipse([bx - rr, by - rr, bx + rr, by + rr], outline=(int(255 * a), int(255 * a), int(255 * a)), width=3)
        d.ellipse([bx - rr * 0.4 + rr * 0.3, by - rr * 0.6, bx + rr * 0.1 + rr * 0.3, by - rr * 0.2], fill=(255, 255, 255))
    return img


def s6(t):  # 黒い空の下、海の表面が泡立つ
    img = sky(1, t)
    d = ImageDraw.Draw(img)
    hz = 600
    for y in range(hz, H):
        k = (y - hz) / (H - hz)
        d.line([(0, y), (W, y)], fill=mixc((20, 40, 70), (8, 20, 40), k))
    r = random.Random(11)
    for i in range(18):  # 波のすじ
        y = hz + 10 + i * 18 + (i * i) % 7
        x0 = (r.uniform(0, W) + t * 20) % W
        d.line([(x0 - 120, y), (x0 + 120, y)], fill=(40, 70, 110), width=2)
    for i in range(110):  # 泡
        bx = r.uniform(0, W); by = r.uniform(hz + 20, 900)
        ph = (t * r.uniform(1.0, 2.2) + r.random()) % 1
        if t < 0.4 * r.random():
            continue
        persp = 0.4 + (by - hz) / 300
        rr = (8 + 26 * ph) * persp
        a = int(255 * (1 - ph * 0.7))
        d.ellipse([bx - rr, by - rr * 0.7, bx + rr, by + rr * 0.7], outline=(a, a, a), width=4)
    st = Image.new("RGB", (W, H)); sd = ImageDraw.Draw(st)
    for i in range(14):  # 立ちのぼる湯気
        x = r.uniform(0, W); ph = (t * 0.3 + r.random()) % 1
        y = 640 - ph * 200; s = 30 + ph * 60; a = int(120 * (1 - ph) * cl(t / 1.0))
        sd.ellipse([x - s, y - s, x + s, y + s], fill=(a, a, a))
    st = st.filter(ImageFilter.GaussianBlur(20))
    return Image.fromarray(np.clip(np.asarray(img, float) + np.asarray(st, float) * 0.6, 0, 255).astype(np.uint8))


def s8(t):  # 空を見上げる人と、10個の目盛りが減っていくリング
    img = city(sky(0, t), 0)
    d = ImageDraw.Draw(img)
    cx, cy = 360, 700
    d.ellipse([cx - 175, cy - 175, cx + 175, cy + 175], fill=(255, 255, 255))
    left = 10 - int(cl(t / 5.0) * 10)
    for i in range(10):
        a0 = -90 + i * 36 + 3
        col = (251, 191, 36) if i < left else (210, 215, 225)
        d.arc([cx - 160, cy - 160, cx + 160, cy + 160], a0, a0 + 30, fill=col, width=26)
    # 見上げる人（リングの中）
    d.ellipse([cx - 55, cy - 95, cx + 55, cy + 15], fill=SKIN)
    d.pieslice([cx - 60, cy - 100, cx + 60, cy - 10], 180, 360, fill=(40, 28, 22))
    d.ellipse([cx - 25, cy - 70, cx - 11, cy - 56], fill=(30, 30, 40)); d.ellipse([cx + 11, cy - 70, cx + 25, cy - 56], fill=(30, 30, 40))
    d.ellipse([cx - 12, cy - 25, cx + 12, cy - 5], fill=(140, 50, 60))
    d.rounded_rectangle([cx - 90, cy + 25, cx + 90, cy + 140], 40, fill=(255, 138, 61))
    return img


SCENES = [s1, s2, s3, s4, s5, s6, s7, s8]


def render(i):
    fn, sec = SCENES[i - 1], CLIPS[i - 1]
    os.makedirs("clips", exist_ok=True)
    tmp, final = f"clips/{i:02d}.part.mp4", f"clips/{i:02d}.mp4"
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
        t = float(sys.argv[2])
        ims = [f(t) for f in SCENES]
        sheet = Image.new("RGB", (W * 8 // 4, H // 4 * 1))
        sheet = Image.new("RGB", (W // 3 * 4, H // 3 * 2))
        for k, im in enumerate(ims):
            sheet.paste(im.resize((W // 3, H // 3)), ((k % 4) * W // 3, (k // 4) * H // 3))
        sheet.save("still.png")
    else:
        for i in map(int, sys.argv[1].split(",")):
            render(i)
