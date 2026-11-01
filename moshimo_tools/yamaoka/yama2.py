"""山岡家（作り直し版）の背景7シーン。720x1280・30fps。文字やロゴは描かない。
使い方: python3 yama2.py stills <秒>   /   python3 yama2.py 1,3,5"""
import math, random, subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import scenes as S
from scenes import W, H, FPS, grad, glow, stars, shop, steam, bowl

CLIPS = [4.8, 6.5, 5.7, 6.0, 5.6, 6.0, 4.4]
VANISH = 0.75  # 1シーン目でラーメンが消える時刻（クリップ内の秒）


def counter_bg(night=True):
    img = grad((10, 10, 22), (34, 26, 30)) if night else grad((235, 205, 160), (150, 100, 60))
    d = ImageDraw.Draw(img)
    # 店の中の壁と、ぼんやりした明かり
    for x in range(0, W, 120):
        d.rectangle([x + 8, 180, x + 112, 470], fill=(28, 24, 30) if night else (200, 165, 120))
    d.rectangle([0, 760, W, H], fill=(70, 40, 28) if night else (120, 78, 44))  # カウンター
    d.rectangle([0, 752, W, 770], fill=(110, 70, 46) if night else (160, 110, 70))
    return img


def k1(t):  # 深夜のカウンター。ラーメンが一瞬で消える
    img = counter_bg(True)
    def lamp(g):
        g.ellipse([300, 120, 420, 180], fill=(255, 210, 140))
        g.polygon([(330, 160), (390, 160), (560, 760), (160, 760)], fill=(70, 50, 30))
    img = glow(img, lamp, 40, 0.9)
    d = ImageDraw.Draw(img)
    if t < VANISH:
        z = 1 + 0.03 * t
        bowl(d, 360, 660, int(210 * z))
        st = Image.new("RGB", (W, H))
        steam(ImageDraw.Draw(st), 360, 600, t, n=14, spread=80, height=420, alpha=170)
        st = st.filter(ImageFilter.GaussianBlur(16))
        img = Image.fromarray(np.clip(np.asarray(img, float) + np.asarray(st, float) * 0.55, 0, 255).astype(np.uint8))
    else:
        k = t - VANISH
        # 消えた瞬間の白い光と、散っていく湯気
        if k < 0.25:
            a = 1 - k / 0.25
            def flash(g):
                g.ellipse([360 - 260, 660 - 120, 360 + 260, 660 + 120], fill=(int(255 * a), int(240 * a), int(210 * a)))
            img = glow(img, flash, 50, 1.4)
        st = Image.new("RGB", (W, H))
        sd = ImageDraw.Draw(st)
        r = random.Random(4)
        for i in range(18):
            ang = r.uniform(0, math.pi * 2); sp = r.uniform(120, 260)
            x = 360 + math.cos(ang) * sp * k; y = 620 + math.sin(ang) * sp * 0.5 * k - 60 * k
            s = 26 + 30 * k; a = int(200 * max(0, 1 - k / 1.6))
            sd.ellipse([x - s, y - s, x + s, y + s], fill=(a, a, a))
        st = st.filter(ImageFilter.GaussianBlur(18))
        img = Image.fromarray(np.clip(np.asarray(img, float) + np.asarray(st, float) * 0.6, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(img)
        d.ellipse([360 - 150, 720 - 20, 360 + 150, 720 + 20], outline=(150, 100, 70), width=4)  # 器のあと
    return img


def k5(t):  # ラーメン難民：明かりの消えた店の並び、さまよう車
    img = grad((6, 8, 20), (20, 20, 34))
    d = ImageDraw.Draw(img)
    stars(d, t, 0.7)
    gy = 760
    d.rectangle([0, gy, W, H], fill=(16, 16, 20))
    d.rectangle([0, gy + 40, W, gy + 200], fill=(30, 30, 34))
    for k in range(8):
        x = (k * 110 + t * 60) % (W + 110) - 110
        d.rectangle([x, gy + 116, x + 50, gy + 124], fill=(150, 150, 120))
    for cx, w in ((110, 200), (360, 220), (610, 200)):
        shop(d, cx, gy, w, lit=0.03)
    cars = [(-60 + t * 130, gy + 80, 1), (W + 40 - t * 110, gy + 160, -1)]
    for x, y, dirn in cars:
        d.rounded_rectangle([x - 70, y - 34, x + 70, y + 10], 14, fill=(50, 56, 72))
        d.rounded_rectangle([x - 44, y - 62, x + 40, y - 30], 12, fill=(40, 44, 58))
        d.ellipse([x - 52, y, x - 28, y + 24], fill=(12, 12, 12)); d.ellipse([x + 28, y, x + 52, y + 24], fill=(12, 12, 12))

    def lights(g):
        for x, y, dirn in cars:
            hx = x + 70 * dirn
            g.ellipse([hx - 10, y - 26, hx + 10, y - 12], fill=(255, 245, 200))
            g.polygon([(hx, y - 20), (hx + 300 * dirn, y - 80), (hx + 300 * dirn, y + 40)], fill=(80, 75, 50))
            tx = x - 70 * dirn
            g.rectangle([tx - 6, y - 24, tx + 6, y - 14], fill=(255, 40, 40))
    return glow(img, lights, 26, 1.1)


def k7(t):  # 深夜のラーメン（左）と朝ラー（右）の2択
    left = counter_bg(True)
    right = counter_bg(False)
    dl, dr = ImageDraw.Draw(left), ImageDraw.Draw(right)
    stars(dl, t, 0.5)
    z = 1 + 0.03 * t
    bowl(dl, 360 - 180, 700, int(150 * z))
    bowl(dr, 360 + 180, 700, int(150 * z))
    img = Image.fromarray(np.concatenate([np.asarray(left)[:, :W // 2], np.asarray(right)[:, W // 2:]], axis=1))
    st = Image.new("RGB", (W, H))
    sd = ImageDraw.Draw(st)
    steam(sd, 180, 650, t, n=10, spread=50, height=330, alpha=150)
    steam(sd, 540, 650, t + 1.3, n=10, spread=50, height=330, alpha=150)
    st = st.filter(ImageFilter.GaussianBlur(14))
    img = Image.fromarray(np.clip(np.asarray(img, float) + np.asarray(st, float) * 0.5, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.rectangle([W // 2 - 3, 0, W // 2 + 3, H], fill=(250, 200, 60))  # 真ん中の仕切り線
    return img


def k4(t):  # 大鍋：中身が下の字幕に隠れないよう少し上へ
    im = S.s5(t)
    return im.crop((0, 120, W, H)).resize((W, H - 120)).crop((0, 0, W, H - 120)).resize((W, H)) if False else im


SCENES = [k1, S.s2, S.s3, S.s5, k5, S.s4, k7]


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
        t = float(sys.argv[2])
        ims = [f(t) for f in SCENES]
        sheet = Image.new("RGB", (W * 7 // 3, H // 3))
        for k, im in enumerate(ims):
            sheet.paste(im.resize((W // 3, H // 3)), (k * W // 3, 0))
        sheet.save("still2.png")
    else:
        for i in map(int, sys.argv[1].split(",")):
            render(i)
