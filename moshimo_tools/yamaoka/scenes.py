"""山岡家回の背景7シーンを描く。720x1280・30fps・各5秒。文字やロゴは一切描かない。
使い方: python3 scenes.py <シーン番号1-7|all> [--still 秒]"""
import math, random, subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H, FPS, SEC = 720, 1280, 30, 5.0
N = int(FPS * SEC)


def grad(top, bot, h=H):
    t = np.linspace(0, 1, h)[:, None]
    a, b = np.array(top, float), np.array(bot, float)
    col = (a * (1 - t) + b * t)[:, None, :].repeat(W, 1)
    return Image.fromarray(col.astype(np.uint8), "RGB")


def glow(base, draw_fn, radius=25, strength=1.0):
    """draw_fn で描いた光を、ぼかして加算する。"""
    layer = Image.new("RGB", base.size, (0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    soft = layer.filter(ImageFilter.GaussianBlur(radius))
    out = np.asarray(base, float) + np.asarray(soft, float) * strength + np.asarray(layer, float) * 0.6
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


rng = random.Random(7)
STARS = [(rng.random() * W, rng.random() * H * 0.55, rng.random()) for _ in range(160)]


def stars(d, t, alpha=1.0):
    for x, y, b in STARS:
        tw = 0.6 + 0.4 * math.sin(t * 2 + b * 20)
        v = int(255 * b * tw * alpha)
        r = 1 if b < 0.8 else 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=(v, v, min(255, v + 20)))


def shop(d, cx, gy, w, lit, warmth=1.0):
    """文字のない小さなラーメン屋。lit=0..1 で明かり。"""
    h = int(w * 0.55)
    x0, x1, y1 = cx - w // 2, cx + w // 2, gy
    y0 = y1 - h
    d.rectangle([x0, y0, x1, y1], fill=(38, 34, 40))
    d.polygon([(x0 - 14, y0), (x1 + 14, y0), (x1 - 6, y0 - 26), (x0 + 6, y0 - 26)], fill=(28, 24, 30))
    win = (int(60 + 195 * lit * warmth), int(40 + 150 * lit * warmth), int(30 + 70 * lit))
    for i in range(3):
        wx = x0 + 16 + i * (w - 32) // 3
        d.rectangle([wx, y0 + 30, wx + (w - 32) // 3 - 12, y0 + h * 0.62], fill=win)
    sign = (int(40 + 200 * lit), int(20 + 40 * lit), int(20 + 20 * lit))
    d.rectangle([cx - w * 0.32, y0 - 64, cx + w * 0.32, y0 - 34], fill=sign)  # 文字なしの看板
    d.rectangle([cx - 22, y1 - h * 0.45, cx + 22, y1], fill=(int(30 + 120 * lit), int(24 + 90 * lit), 30))


def steam(d, cx, by, t, n=14, spread=40, height=320, alpha=200):
    r = random.Random(3)
    for i in range(n):
        ph = (t * 0.25 + i / n) % 1
        x = cx + math.sin(ph * 6 + i) * spread * ph + r.uniform(-spread, spread) * 0.4
        y = by - ph * height
        s = 18 + ph * 60
        a = int(alpha * (1 - ph) * min(1, ph * 5))
        d.ellipse([x - s, y - s, x + s, y + s], fill=(a, a, a))


def s1(t):  # 深夜2時、明かりの消えた店、車のライトが通る
    img = grad((6, 8, 20), (18, 18, 30))
    d = ImageDraw.Draw(img)
    stars(d, t, 0.8)
    gy = 800
    d.rectangle([0, gy, W, H], fill=(14, 14, 18))
    d.polygon([(0, H), (W, H), (W * 0.62, gy), (W * 0.38, gy)], fill=(24, 24, 28))
    for k in range(6):
        y = gy + 40 + k * k * 12
        d.rectangle([W / 2 - 3 - k, y, W / 2 + 3 + k, y + 14 + k * 3], fill=(70, 70, 60))
    shop(d, 520, gy, 260, lit=0.02)
    d.rectangle([150, gy - 330, 158, gy], fill=(30, 30, 34))  # 消えた街灯
    p = (t / SEC)
    cx = -200 + p * (W + 400)

    def lights(g):
        g.ellipse([cx - 30, gy + 60, cx + 30, gy + 80], fill=(255, 245, 200))
        g.polygon([(cx + 20, gy + 70), (cx + 420, gy + 10), (cx + 420, gy + 150)], fill=(90, 85, 60))
    img = glow(img, lights, 30, 1.2)
    return img


def s2(t):  # 田舎道、あたたかく光る小さな店（ノスタルジック）
    img = grad((20, 18, 45), (70, 45, 60))
    d = ImageDraw.Draw(img)
    stars(d, t, 0.5)
    gy = 800
    for i, c in enumerate([(30, 30, 40), (24, 26, 34)]):
        pts = [(0, gy - 120 + i * 50)] + [(x, gy - 120 + i * 50 - 60 * math.sin(x / 140 + i)) for x in range(0, W + 40, 40)] + [(W, gy), (0, gy)]
        d.polygon(pts, fill=c)
    d.rectangle([0, gy, W, H], fill=(20, 22, 20))
    d.polygon([(0, H), (W, H), (W * 0.55, gy), (W * 0.45, gy)], fill=(34, 32, 30))
    z = 1 + 0.06 * t / SEC
    sw = int(240 * z)
    shop(d, 360, gy + 10, sw, lit=1.0)

    def warm(g):
        g.rectangle([360 - sw * 0.45, gy - sw * 0.5, 360 + sw * 0.45, gy], fill=(150, 90, 30))
    img = glow(img, warm, 45, 0.9)
    arr = np.asarray(img, float)
    arr = arr * np.array([1.08, 1.0, 0.85]) + np.random.default_rng(int(t * 30)).normal(0, 5, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def s3(t):  # 夜の高速、トラックが明るい駐車場へ
    img = grad((8, 10, 24), (22, 24, 40))
    d = ImageDraw.Draw(img)
    stars(d, t, 0.4)
    gy = 780
    d.rectangle([0, gy, W, H], fill=(18, 18, 22))
    d.rectangle([0, gy + 120, W, gy + 330], fill=(30, 30, 34))
    for k in range(8):
        x = (k * 120 - (t * 140) % 120)
        d.rectangle([x, gy + 222, x + 60, gy + 230], fill=(200, 200, 170))
    shop(d, 170, gy + 10, 230, lit=1.0)
    p = t / SEC
    tx = 760 - p * 430
    ty = gy + 150 - p * 60
    d.rectangle([tx, ty - 120, tx + 220, ty], fill=(70, 80, 95))
    d.rectangle([tx - 70, ty - 90, tx, ty], fill=(110, 40, 40))
    d.rectangle([tx - 60, ty - 80, tx - 20, ty - 50], fill=(150, 190, 210))
    for wx in (tx - 45, tx + 40, tx + 170):
        d.ellipse([wx - 22, ty - 18, wx + 22, ty + 26], fill=(15, 15, 15))

    def lamps(g):
        for lx in (60, 300):
            g.ellipse([lx - 14, gy - 300, lx + 14, gy - 280], fill=(255, 230, 170))
            g.polygon([(lx, gy - 290), (lx - 120, gy + 120), (lx + 120, gy + 120)], fill=(70, 60, 40))
        g.ellipse([tx - 78, ty - 30, tx - 62, ty - 14], fill=(255, 250, 210))
        g.rectangle([170 - 230 * 0.45, gy - 120, 170 + 230 * 0.45, gy], fill=(120, 70, 30))
    for lx in (60, 300):
        d.rectangle([lx - 3, gy - 290, lx + 3, gy + 10], fill=(40, 40, 46))
    img = glow(img, lamps, 30, 1.0)
    return img


def bowl(d, cx, cy, r):
    d.ellipse([cx - r, cy - r * 0.35, cx + r, cy + r * 0.35], fill=(40, 20, 18))
    d.chord([cx - r, cy - r * 0.9, cx + r, cy + r * 0.9], 0, 180, fill=(150, 30, 30))
    d.ellipse([cx - r * 0.92, cy - r * 0.3, cx + r * 0.92, cy + r * 0.3], fill=(225, 190, 140))
    rr = random.Random(5)
    for i in range(26):
        a = rr.uniform(0, math.pi * 2)
        rad = rr.uniform(0.1, 0.8)
        x, y = cx + math.cos(a) * r * rad, cy + math.sin(a) * r * 0.26 * rad
        d.arc([x - 40, y - 8, x + 40, y + 8], 0, 180, fill=(245, 215, 120), width=5)
    d.ellipse([cx + r * 0.2, cy - r * 0.2, cx + r * 0.6, cy + r * 0.05], fill=(170, 110, 80))  # チャーシュー
    d.rectangle([cx - r * 0.75, cy - r * 0.3, cx - r * 0.35, cy - r * 0.05], fill=(25, 40, 25))  # のり
    for i in range(10):
        x = cx - r * 0.1 + rr.uniform(-40, 40)
        y = cy + rr.uniform(-18, 18)
        d.ellipse([x - 6, y - 4, x + 6, y + 4], fill=(90, 160, 60))


def s4(t):  # 朝の光、湯気の立つ豚骨ラーメン
    img = grad((235, 205, 160), (120, 80, 50))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 720, W, H], fill=(110, 70, 40))
    for i in range(0, W, 90):
        d.line([(i, 720), (i - 60, H)], fill=(95, 60, 34), width=3)
    z = 1 + 0.05 * t / SEC
    bowl(d, 360, 720, int(250 * z))
    st = Image.new("RGB", (W, H))
    steam(ImageDraw.Draw(st), 360, 660, t, n=16, spread=90, height=520, alpha=160)
    st = st.filter(ImageFilter.GaussianBlur(18))
    out = np.asarray(img, float) + np.asarray(st, float) * 0.55

    def sun(g):
        g.polygon([(W, 0), (W, 260), (100, 900), (0, 700), (0, 500)], fill=(80, 60, 30))
    img = glow(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)), sun, 60, 0.6)
    return img


def s5(t):  # 大鍋の豚骨スープがぐつぐつ
    img = grad((30, 28, 30), (60, 50, 44))
    d = ImageDraw.Draw(img)
    for x in range(0, W, 60):
        d.rectangle([x, 0, x + 56, 700], fill=(70, 72, 76))
    cx, top = 360, 640
    d.rectangle([cx - 300, top, cx + 300, 1180], fill=(150, 152, 158))
    d.rectangle([cx - 300, top, cx - 270, 1180], fill=(190, 192, 198))
    d.ellipse([cx - 300, top - 70, cx + 300, top + 70], fill=(200, 200, 205))
    d.ellipse([cx - 280, top - 58, cx + 280, top + 58], fill=(232, 220, 196))
    rr = random.Random(11)
    for i in range(40):
        ph = (t * 1.6 + rr.random()) % 1
        a, rad = rr.uniform(0, 6.28), rr.uniform(0, 0.9)
        x, y = cx + math.cos(a) * 270 * rad, top + math.sin(a) * 50 * rad
        s = 6 + 22 * math.sin(ph * math.pi)
        d.ellipse([x - s, y - s * 0.5, x + s, y + s * 0.5], outline=(250, 245, 230), width=3)

    def fire(g):
        for k in range(9):
            fx = cx - 220 + k * 55
            h = 40 + 25 * math.sin(t * 9 + k)
            g.polygon([(fx - 18, 1200), (fx + 18, 1200), (fx, 1200 - h)], fill=(40, 90, 230))
    img = glow(img, fire, 18, 1.2)
    st = Image.new("RGB", (W, H))
    steam(ImageDraw.Draw(st), cx, top - 20, t * 1.6, n=24, spread=220, height=700, alpha=200)
    st = st.filter(ImageFilter.GaussianBlur(22))
    out = np.asarray(img, float) + np.asarray(st, float) * 0.7
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def s6(t):  # 夜道を走る車（後ろから）、遠くの光へ
    img = grad((6, 8, 22), (20, 22, 40))
    d = ImageDraw.Draw(img)
    stars(d, t, 0.9)
    hz = 480
    d.rectangle([0, hz, W, H], fill=(14, 14, 16))
    d.polygon([(W * 0.48, hz), (W * 0.52, hz), (W, H), (0, H)], fill=(28, 28, 30))
    for k in range(12):
        ph = (k / 12 + t * 0.35) % 1
        y0 = hz + (H - hz) * ph ** 2
        y1 = hz + (H - hz) * (ph + 0.03) ** 2
        w0 = 2 + 10 * ph
        d.polygon([(W / 2 - w0, y0), (W / 2 + w0, y0), (W / 2 + w0 * 1.2, y1), (W / 2 - w0 * 1.2, y1)], fill=(200, 190, 140))
    cx, cy = 360, 880
    d.rounded_rectangle([cx - 170, cy - 110, cx + 170, cy + 40], 30, fill=(40, 44, 60))
    d.rounded_rectangle([cx - 120, cy - 200, cx + 120, cy - 100], 30, fill=(30, 34, 46))
    d.rectangle([cx - 100, cy - 185, cx + 100, cy - 115], fill=(60, 70, 90))

    def lights(g):
        g.ellipse([W / 2 - 40, hz - 40, W / 2 + 40, hz + 10], fill=(120, 90, 40))
        g.polygon([(cx - 150, cy - 110), (W / 2 - 60, hz), (W / 2 + 60, hz), (cx + 150, cy - 110)], fill=(50, 50, 40))
        for sx in (cx - 140, cx + 110):
            g.rectangle([sx, cy - 60, sx + 30, cy - 40], fill=(255, 40, 40))
    img = glow(img, lights, 26, 1.1)
    return img


def s7(t):  # 夜明け、湯気の出るラーメン屋
    p = t / SEC
    top = tuple(int(a + (b - a) * p) for a, b in zip((40, 50, 100), (120, 150, 210)))
    img = grad(top, (250, 170, 110))
    d = ImageDraw.Draw(img)
    gy = 820
    d.ellipse([W / 2 - 90, gy - 60 - 40 * p, W / 2 + 90, gy + 120 - 40 * p], fill=(255, 220, 160))
    d.rectangle([0, gy, W, H], fill=(40, 34, 36))
    z = 1 + 0.07 * p
    sw = int(300 * z)
    shop(d, 360, gy + 20, sw, lit=0.9)
    st = Image.new("RGB", (W, H))
    steam(ImageDraw.Draw(st), 360, gy - 40, t, n=14, spread=60, height=420, alpha=170)
    st = st.filter(ImageFilter.GaussianBlur(20))
    out = np.asarray(img, float) + np.asarray(st, float) * 0.5
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


SCENES = [s1, s2, s3, s4, s5, s6, s7]


def render(i):
    fn = SCENES[i - 1]
    tmp, final = f"{i:02d}.tmp.mp4", f"{i:02d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                          "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for f in range(N):
        p.stdin.write(fn(f / FPS).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, final)
        print("ok", final)


if __name__ == "__main__":
    arg = sys.argv[1]
    if "--still" in sys.argv:
        t = float(sys.argv[sys.argv.index("--still") + 1])
        ims = [f(t) for f in SCENES] if arg == "all" else [SCENES[int(arg) - 1](t)]
        sheet = Image.new("RGB", (W * len(ims) // 3, H // 3))
        for k, im in enumerate(ims):
            sheet.paste(im.resize((W // 3, H // 3)), (k * W // 3, 0))
        sheet.save(f"still_{arg}.png")
    else:
        for i in (range(1, 8) if arg == "all" else [int(arg)]):
            render(i)
