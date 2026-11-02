"""もしもの続き 7本目「エレベーターが落ちたら」マイクラ調の背景クリップ（文字なし）
主役のキャラにぐっと寄る。主役は画面の y=553〜860（720x1280換算）に置く。
使い方: python3 elevator_voxel.py stills 0:0.2,1:2.0  /  python3 elevator_voxel.py 0,1,2"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import Scene, render, particles, tone, blur, smooth, ease, C, f32

W, H, FPS, RS = 1080, 1920, 30, 3
CLIPS = [2.8, 4.6, 4.5, 7.1, 6.6, 6.3, 5.9, 6.7]
XFRAC = 0.6        # 2シーン目で×が出る位置（クリップの割合）
R = np.random.default_rng(4)

# 色
SKIN, HAIR, SHIRT, PANTS, SHOE = (0.95, 0.74, 0.58), (0.13, 0.09, 0.07), (1.0, 0.52, 0.18), (0.24, 0.32, 0.68), (0.22, 0.22, 0.26)
EYE, MOUTH = (0.08, 0.08, 0.12), (0.45, 0.12, 0.12)
METAL, PANEL, FLOOR = (0.78, 0.8, 0.84), (0.68, 0.7, 0.75), (0.42, 0.36, 0.3)

# 箱（かご）の位置
X0, X1, Z0, Z1, FY, CY = 18, 46, 18, 46, 10, 42
CX, CZ = 32, 34


def put(c, m, x0, x1, y0, y1, z0, z1, col, mat=1, var=0.05):
    sl = (slice(int(x0), int(x1)), slice(int(y0), int(y1)), slice(int(z0), int(z1)))
    shp = m[sl].shape
    if 0 in shp:
        return
    v = (1 + R.uniform(-var, var, shp)).astype(f32)[..., None]
    c[sl] = np.clip(C(*col) * v, 0, 3); m[sl] = mat


def build_base():
    S = Scene(64, 100, 64)
    c, m = S.col, S.mat
    # 昇降路の壁（左右・奥）
    put(c, m, 10, 12, 0, 100, 8, 56, (0.46, 0.46, 0.5), 1, 0.08)
    put(c, m, 52, 54, 0, 100, 8, 56, (0.46, 0.46, 0.5), 1, 0.08)
    put(c, m, 10, 54, 0, 100, 54, 56, (0.42, 0.42, 0.46), 1, 0.08)
    # レール
    put(c, m, 12, 14, 0, 100, 30, 34, (0.3, 0.31, 0.35), 1, 0.03)
    put(c, m, 50, 52, 0, 100, 30, 34, (0.3, 0.31, 0.35), 1, 0.03)
    # かご：床・天井・奥と左右の壁（手前は開けて中を見せる）
    put(c, m, X0, X1, FY - 2, FY, Z0, Z1, (0.55, 0.56, 0.6), 1)
    put(c, m, X0, X1, FY, FY + 1, Z0, Z1 - 1, FLOOR, 1, 0.08)
    put(c, m, X0, X1, CY, CY + 2, Z0, Z1, (0.62, 0.63, 0.67), 1)
    put(c, m, X0, X1, FY, CY, Z1 - 1, Z1, PANEL, 1, 0.03)
    put(c, m, X0, X0 + 1, FY, CY, Z0, Z1, PANEL, 1, 0.03)
    put(c, m, X1 - 1, X1, FY, CY, Z0, Z1, PANEL, 1, 0.03)
    # 壁の縦の継ぎ目
    for z in range(Z0 + 7, Z1, 7):
        put(c, m, X0, X0 + 1, FY, CY, z, z + 1, (0.55, 0.57, 0.6), 1, 0.0)
        put(c, m, X1 - 1, X1, FY, CY, z, z + 1, (0.55, 0.57, 0.6), 1, 0.0)
    for x in range(X0 + 7, X1, 7):
        put(c, m, x, x + 1, FY, CY, Z1 - 1, Z1, (0.55, 0.57, 0.6), 1, 0.0)
    # 手すり
    put(c, m, X0 + 1, X0 + 2, FY + 13, FY + 14, Z0 + 2, Z1 - 2, (0.85, 0.85, 0.9), 1, 0.0)
    put(c, m, X1 - 2, X1 - 1, FY + 13, FY + 14, Z0 + 2, Z1 - 2, (0.85, 0.85, 0.9), 1, 0.0)
    # 天井の照明（光る）
    put(c, m, X0 + 6, X1 - 6, CY - 1, CY, Z0 + 6, Z1 - 6, (1.5, 1.45, 1.3), 4, 0.0)
    # ボタンのパネル（右の壁）
    put(c, m, X1 - 2, X1 - 1, FY + 12, FY + 22, Z0 + 3, Z0 + 7, (0.3, 0.32, 0.36), 1, 0.0)
    for k in range(4):
        put(c, m, X1 - 3, X1 - 2, FY + 13 + 2 * k, FY + 14 + 2 * k, Z0 + 4, Z0 + 6, (1.6, 1.2, 0.4) if k == 1 else (0.9, 0.9, 0.95), 4 if k == 1 else 1, 0.0)
    # ロープ（かごの上）
    S.ropes = [(x, z) for x in (27, 29, 31, 33, 35, 37) for z in (31, 33)]
    for x, z in S.ropes:
        put(c, m, x, x + 1, CY + 2, 100, z, z + 1, (0.8, 0.8, 0.85), 1, 0.0)
    put(c, m, 25, 39, CY + 2, CY + 4, 29, 35, (0.4, 0.4, 0.45), 1)
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = None
    S.amb = C(0.55, 0.55, 0.6)
    S.hor = C(0.02, 0.02, 0.03); S.top = C(0.0, 0.0, 0.0); S.fog0, S.fogk = 80, 200
    return S


def shaft_lines(c, m, off):
    """昇降路の壁に、各階の明かりのすじ（下から上へ流れると落ちて見える）。"""
    ys = np.arange(100)
    band = ((ys + off) % 26) < 2
    for xa in (11, 52):
        for y in ys[band]:
            if FY - 2 <= y <= CY + 2:
                continue
            put(c, m, xa, xa + 1, y, y + 1, 12, 52, (1.5, 1.35, 1.0), 4, 0.0)
    for y in ys[band]:
        put(c, m, 12, 52, y, y + 1, 54, 55, (1.3, 1.2, 0.9), 4, 0.0)


def person(c, m, cx, fy, cz, pose="stand", look=0):
    """ブロックの人。顔は手前（zが小さい側）。pose: stand / float / crouch / jump / lie"""
    if pose == "lie":  # 床に仰向け（頭が奥）
        y = fy
        put(c, m, cx - 3, cx + 3, y, y + 3, cz - 2, cz + 7, SHIRT)          # 体
        put(c, m, cx - 3, cx + 3, y, y + 6, cz + 7, cz + 13, SKIN)          # 頭
        put(c, m, cx - 3, cx + 3, y + 5, y + 6, cz + 7, cz + 13, SKIN)
        put(c, m, cx - 3, cx + 3, y, y + 6, cz + 12, cz + 14, HAIR)
        put(c, m, cx - 2, cx - 1, y + 6, y + 7, cz + 9, cz + 10, EYE); put(c, m, cx + 1, cx + 2, y + 6, y + 7, cz + 9, cz + 10, EYE)
        put(c, m, cx - 1, cx + 1, y + 6, y + 7, cz + 7, cz + 8, MOUTH)
        put(c, m, cx - 3, cx, y, y + 3, cz - 11, cz - 2, PANTS); put(c, m, cx, cx + 3, y, y + 3, cz - 11, cz - 2, PANTS)
        put(c, m, cx - 4, cx - 1, y, y + 3, cz - 13, cz - 11, SHOE); put(c, m, cx + 1, cx + 4, y, y + 3, cz - 13, cz - 11, SHOE)
        put(c, m, cx - 12, cx - 3, y, y + 2, cz + 4, cz + 6, SHIRT); put(c, m, cx - 14, cx - 12, y, y + 2, cz + 4, cz + 6, SKIN)
        put(c, m, cx + 3, cx + 12, y, y + 2, cz + 4, cz + 6, SHIRT); put(c, m, cx + 12, cx + 14, y, y + 2, cz + 4, cz + 6, SKIN)
        return
    leg = 5 if pose == "crouch" else 9
    y = fy
    spread = 1 if pose in ("float", "jump") else 0
    put(c, m, cx - 3 - spread, cx - spread, y, y + 2, cz - 2, cz + 2, SHOE)
    put(c, m, cx + spread, cx + 3 + spread, y, y + 2, cz - 2, cz + 2, SHOE)
    put(c, m, cx - 3 - spread, cx - spread, y + 2, y + leg, cz - 1, cz + 2, PANTS)
    put(c, m, cx + spread, cx + 3 + spread, y + 2, y + leg, cz - 1, cz + 2, PANTS)
    by = y + leg
    put(c, m, cx - 3, cx + 3, by, by + 9, cz - 1, cz + 2, SHIRT)
    hy = by + 9
    # 腕
    if pose in ("float", "jump"):
        put(c, m, cx - 5, cx - 3, hy - 1, hy + 8, cz - 1, cz + 2, SHIRT); put(c, m, cx - 5, cx - 3, hy + 8, hy + 10, cz - 1, cz + 2, SKIN)
        put(c, m, cx + 3, cx + 5, hy - 1, hy + 8, cz - 1, cz + 2, SHIRT); put(c, m, cx + 3, cx + 5, hy + 8, hy + 10, cz - 1, cz + 2, SKIN)
    elif pose == "crouch":
        put(c, m, cx - 5, cx - 3, by + 1, by + 9, cz, cz + 3, SHIRT); put(c, m, cx - 5, cx - 3, by - 1, by + 1, cz + 1, cz + 4, SKIN)
        put(c, m, cx + 3, cx + 5, by + 1, by + 9, cz, cz + 3, SHIRT); put(c, m, cx + 3, cx + 5, by - 1, by + 1, cz + 1, cz + 4, SKIN)
    else:
        put(c, m, cx - 5, cx - 3, by + 2, by + 9, cz - 1, cz + 2, SHIRT); put(c, m, cx - 5, cx - 3, by, by + 2, cz - 1, cz + 2, SKIN)
        put(c, m, cx + 3, cx + 5, by + 2, by + 9, cz - 1, cz + 2, SHIRT); put(c, m, cx + 3, cx + 5, by, by + 2, cz - 1, cz + 2, SKIN)
    # 頭
    put(c, m, cx - 3, cx + 3, hy, hy + 6, cz - 3, cz + 3, SKIN, 1, 0.03)
    put(c, m, cx - 3, cx + 3, hy + 5, hy + 7, cz - 3, cz + 3, HAIR, 1, 0.05)
    put(c, m, cx - 3, cx + 3, hy + 2, hy + 6, cz + 2, cz + 3, HAIR, 1, 0.05)
    put(c, m, cx - 3, cx - 2, hy + 3, hy + 6, cz - 3, cz + 3, HAIR, 1, 0.05)
    put(c, m, cx + 2, cx + 3, hy + 3, hy + 6, cz - 3, cz + 3, HAIR, 1, 0.05)
    ex = look
    put(c, m, cx - 2 + ex, cx - 1 + ex, hy + 3, hy + 4, cz - 4, cz - 3, EYE, 1, 0.0)
    put(c, m, cx + 1 + ex, cx + 2 + ex, hy + 3, hy + 4, cz - 4, cz - 3, EYE, 1, 0.0)
    if pose in ("float", "jump", "crouch"):  # あわてた口
        put(c, m, cx - 1, cx + 1, hy + 1, hy + 3, cz - 4, cz - 3, MOUTH, 1, 0.0)
    else:
        put(c, m, cx - 1, cx + 1, hy + 1, hy + 2, cz - 4, cz - 3, MOUTH, 1, 0.0)


_S = {}


def base():
    if "b" not in _S:
        _S["b"] = build_base()
    return _S["b"]


def finish(img, expo=1.12, grade=(1, 1, 1)):
    img = tone(img, expo) * C(*grade)
    img = np.repeat(np.repeat(img, RS, 0), RS, 1)
    bright = np.clip(img - 0.85, 0, None)
    img = img + blur(bright, 12) * 1.2
    return np.clip(img, 0, 1)


def shake(cam, tgt, amt, t):
    dx = amt * math.sin(t * 53); dy = amt * math.sin(t * 41 + 1)
    return (cam[0] + dx, cam[1] + dy, cam[2]), (tgt[0] + dx, tgt[1] + dy, tgt[2])


def streaks(img, depth, cam, tgt, fov, t, speed, n=160):
    rg = np.random.default_rng(12)
    px = np.where(rg.random(n) < 0.5, rg.uniform(12.5, 17, n), rg.uniform(47, 51.5, n))
    pz = rg.uniform(10, 54, n)
    py = (rg.uniform(0, 100, n) + speed * t) % 100
    pts = []
    cols = []
    for k in range(6):  # 縦に伸ばした点で、すじに見せる
        pts.append(np.stack([px, py - k * 0.8, pz], 1)); cols.append(np.tile(C(0.9, 0.9, 1.0) * (1 - k / 6), (n, 1)))
    particles(img, depth, cam, tgt, fov, np.concatenate(pts), np.concatenate(cols), 0.35)


def draw_x(img01, a):
    im = Image.fromarray((img01 * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    cx, cy, L = W / 2, 1060, 300 * a
    for s in (1, -1):
        d.line([(cx - L, cy - L * s), (cx + L, cy + L * s)], fill=(239, 68, 68), width=44)
    return np.asarray(im).astype(f32) / 255


def frame(k, t):
    w, h = W // RS, H // RS
    T = CLIPS[k]; p = ease(t / T)
    S = base()
    c, m = S.base_c.copy(), S.base_m.copy()
    S.lights = [((CX, CY - 3, CZ - 4), (0.9, 0.85, 0.75), 30)]

    if k == 0:   # 0秒：止まっていたかごが、急に落ちはじめる（明るいかごの中の人）
        t0 = 0.35
        f = max(0.0, t - t0)
        shaft_lines(c, m, 70 * f * f)
        lift = min(4.0, 6 * f * f)
        person(c, m, CX, FY + 1 + lift, CZ, "float" if f > 0.15 else "stand")
        cam, tgt = (CX + 6, FY + 21, -14), (CX, FY + 20, CZ)
        if f > 0:
            cam, tgt = shake(cam, tgt, 0.5, t)
        img, depth = render(S, c, m, cam, tgt, 60, w, h)
        if f > 0.1:
            streaks(img, depth, cam, tgt, 60, t, 90)
        return finish(img)
    if k == 1:   # ジャンプで助かる？→ムリ（キャラのアップ）
        shaft_lines(c, m, 60 * t)
        jt = T * 0.35
        if t < jt:
            person(c, m, CX, FY + 1, CZ, "crouch")
        else:
            person(c, m, CX, FY + 1 + min(3.0, (t - jt) * 10), CZ, "jump")
        cam, tgt = shake((CX + 3, FY + 20, CZ - 32), (CX, FY + 19, CZ), 0.25, t)
        img, depth = render(S, c, m, cam, tgt, 55, w, h)
        out = finish(img)
        if t >= T * XFRAC:
            out = draw_x(out, min(1.0, (t - T * XFRAC) / 0.15))
        return out
    if k == 2:   # 体がふわっと浮く
        shaft_lines(c, m, 70 * t)
        dy = 3 + 2.5 * math.sin(t * 1.6)
        person(c, m, CX + int(round(math.sin(t * 0.9) * 2)), FY + 1 + dy, CZ, "float", look=int(round(math.sin(t * 1.3))))
        cam = (CX - 6 + 8 * p, FY + 26, CZ - 32 + 4 * p); tgt = (CX, FY + 24, CZ)
        img, depth = render(S, c, m, cam, tgt, 52, w, h)
        rg = np.random.default_rng(3); n = 80
        dust = np.stack([rg.uniform(X0 + 2, X1 - 2, n), FY + 2 + (rg.uniform(0, 28, n) + 1.5 * t) % 28, rg.uniform(Z0 + 2, Z1 - 3, n)], 1)
        particles(img, depth, cam, tgt, 52, dust, np.tile(C(1.0, 0.95, 0.85), (n, 1)), 0.18)
        return finish(img)
    if k == 3:   # 時速80キロ以上（引きの画で、すごい速さで落ちる）
        shaft_lines(c, m, 160 * t)
        person(c, m, CX, FY + 5, CZ, "float")
        cam, tgt = shake((CX + 2, FY + 8 - 6 * p, -40), (CX, FY + 22, CZ), 0.6, t)
        img, depth = render(S, c, m, cam, tgt, 62, w, h)
        streaks(img, depth, cam, tgt, 62, t, 200, 260)
        return finish(img, grade=(0.98, 1.0, 1.05))
    if k == 4:   # 何本ものロープ（かごの上から見上げる）
        person(c, m, CX, FY + 1, CZ, "stand", look=0)
        shaft_lines(c, m, 6 * t)
        cam = (CX + 4, CY - 2 + 6 * p, -6); tgt = (CX, CY + 30 + 8 * p, CZ)
        S.lights = [((CX, CY + 20, CZ - 10), (1.2, 1.15, 1.0), 60)]
        img, depth = render(S, c, m, cam, tgt, 64, w, h)
        return finish(img)
    if k == 5:   # 非常ブレーキがレールをはさむ（火花）
        stopT = 2.2
        tt = min(t, stopT)
        shaft_lines(c, m, 110 * tt - 25 * tt * tt)
        clamp = smooth(0.2, 0.6, t)
        put(c, m, X1, X1 + 3, FY - 2, FY + 2, 29, 35, (0.85, 0.2, 0.15), 1, 0.0)
        put(c, m, X1 + 3 - int(clamp * 0) , 50, FY - 2, FY + 2, 29, 30, (0.85, 0.2, 0.15), 1, 0.0)
        put(c, m, X1 + 3, 50, FY - 2, FY + 2, 34, 35, (0.85, 0.2, 0.15), 1, 0.0)
        person(c, m, CX, FY + 1, CZ, "crouch" if t < stopT else "stand")
        S.lights = [((CX, CY - 3, CZ - 4), (0.9, 0.85, 0.75), 30), ((49, FY + 6, 22), (1.6, 1.3, 0.9), 22)]
        cam, tgt = shake((49, FY + 10 - 3 * p, 12), (48, FY + 4, 32), 0.3 if t < stopT else 0.0, t)
        img, depth = render(S, c, m, cam, tgt, 58, w, h)
        if t < stopT + 0.3:
            rg = np.random.default_rng(int(t * 30)); n = 120
            age = rg.uniform(0, 0.4, n)
            sp = np.stack([50 + rg.normal(0, 1, n) * 4 * age * 3 - 1, FY + rg.normal(0, 1, n) * 1.5 + age * 18, 32 + rg.normal(0, 1, n) * 6 * age], 1)
            hot = (1 - age / 0.4)[:, None]
            particles(img, depth, cam, tgt, 58, sp, C(2.2, 1.3, 0.4) * hot, 0.25)
        return finish(img)
    if k == 6:   # 床に寝そべる（真上から）
        person(c, m, CX, FY + 1, CZ - 1, "lie")
        cam = (CX + 0.01, CY - 1.5, CZ - 6 - 0.5); tgt = (CX, FY, CZ - 6)
        put(c, m, X0, X1, CY, CY + 2, Z0, Z1, (0.62, 0.63, 0.67), 0)  # 天井を外して真上から
        put(c, m, X0 + 6, X1 - 6, CY - 1, CY, Z0 + 6, Z1 - 6, (1.5, 1.45, 1.3), 0)
        cam = (CX + 0.01, FY + 31 - 3 * p, CZ - 3); tgt = (CX, FY, CZ + 5)
        S.lights = [((CX, FY + 28, CZ - 6), (0.9, 0.85, 0.75), 40)]
        img, depth = render(S, c, m, cam, tgt, 62, w, h)
        return finish(img)
    if k == 7:   # あなたならどうする？（顔のアップ、ゆっくり寄る）
        person(c, m, CX, FY + 1, CZ, "stand", look=int(round(math.sin(t * 1.2))))
        cam = (CX, FY + 23, CZ - 30 + 8 * p); tgt = (CX, FY + 22.5, CZ)
        img, depth = render(S, c, m, cam, tgt, 50, w, h)
        return finish(img)


def render_clip(k, out):
    n = int(round(CLIPS[k] * FPS))
    tmp = out[:-4] + '.part.mp4'
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write((frame(k, i / FPS) * 255 + 0.5).astype(np.uint8).tobytes())
        if i % 30 == 0: print(k, i, flush=True)
    ff.stdin.close()
    if ff.wait() == 0:
        os.replace(tmp, out); print('done', out, flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        ims = []
        for spec in sys.argv[2].split(','):
            k, t = spec.split(':')
            ims.append(Image.fromarray((frame(int(k), float(t)) * 255).astype(np.uint8)).resize((270, 480)))
        sheet = Image.new('RGB', (270 * min(4, len(ims)), 480 * ((len(ims) + 3) // 4)))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % 4) * 270, (i // 4) * 480))
        sheet.save('elev_stills.png')
    else:
        os.makedirs('clips', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips/{k + 1:02d}.mp4')
