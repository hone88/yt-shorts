"""19本目「もしも地球の公転が一瞬で止まったら？」（台本 20261123）。地球の回（earth_voxel）の続編。
使い方: python3 kouten_voxel.py stills k:t,... out.png / python3 kouten_voxel.py 0,1,2"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import render, particles, ease, C, f32, Scene, vnoise
from elevator_voxel import person, put, finish, shake
import earth_voxel as EV
from earth_voxel import earth, town, hstreaks, GY, get, lerp, snap

W, H, FPS, RS = 1080, 1920, 30, 3
_est = [4.2, 3.7, 5.8, 4.9, 2.9, 8.1, 4.8, 3.1]
CLIPS = [round(x * 1.27 * 1.15, 1) for x in _est]


def stars(img, depth, cam, tgt, fov, n=900, seed=9):
    rg = np.random.default_rng(seed)
    v = rg.normal(size=(n, 3)); v /= np.linalg.norm(v, axis=1, keepdims=True)
    particles(img, depth, cam, tgt, fov, np.array(cam) + v * 400, np.tile(C(1, 1, 1), (n, 1)) * rg.uniform(0.4, 1, (n, 1)), 0.9)


def sphere(c, m, cx, cy, cz, r, col, mat=1, var=0.06):
    r0 = int(math.ceil(r))
    xs, ys, zs = np.meshgrid(np.arange(int(cx) - r0, int(cx) + r0 + 1), np.arange(int(cy) - r0, int(cy) + r0 + 1),
                             np.arange(int(cz) - r0, int(cz) + r0 + 1), indexing='ij')
    ok = (xs + 0.5 - cx) ** 2 + (ys + 0.5 - cy) ** 2 + (zs + 0.5 - cz) ** 2 < r * r
    ok &= (xs >= 0) & (ys >= 0) & (zs >= 0) & (xs < c.shape[0]) & (ys < c.shape[1]) & (zs < c.shape[2])
    rg = np.random.default_rng(int(cx * 7 + cz))
    cc = np.array(col, f32)[None] * (1 - var / 2 + var * rg.random((ok.sum(), 1)))
    c[xs[ok], ys[ok], zs[ok]] = cc
    m[xs[ok], ys[ok], zs[ok]] = mat


# ---------------------------------------------------------------- 宇宙（太陽）
SX, SY, SZ = 60, 40, 60


def build_space():
    S = Scene(140, 80, 140)
    sphere(S.col, S.mat, SX, SY, SZ, 16, (1.25, 0.72, 0.22), 4, 0.45)
    S.base_c, S.base_m = S.col.copy(), S.mat.copy()
    S.sun = None; S.amb = C(0.5, 0.5, 0.58)
    S.lights = [((SX, SY, SZ), (1.6, 1.3, 0.9), 140)]
    S.hor = C(0.0, 0.0, 0.02); S.top = C(0.0, 0.0, 0.01); S.fog0, S.fogk = 1000, 1e9
    return S


def mini_earth(c, m, x, y, z, r=3.2):
    sphere(c, m, x, y, z, r, (0.15, 0.35, 0.75), 1, 0.2)
    for dx, dz in ((1, 0), (-1, 1), (0, -1)):
        put(c, m, int(x + dx), int(x + dx) + 2, int(y), int(y) + 2, int(z + dz), int(z + dz) + 1, (0.2, 0.55, 0.25), 1, 0.05)


def sunglow(img, depth, cam, tgt, fov, t):
    rg = np.random.default_rng(int(t * 10)); n = 200
    v = rg.normal(size=(n, 3)); v /= np.linalg.norm(v, axis=1, keepdims=True)
    p = np.array([SX, SY, SZ]) + v * rg.uniform(16, 22, (n, 1))
    particles(img, depth, cam, tgt, fov, p, np.tile(C(2.0, 1.2, 0.4), (n, 1)) * 0.5, 0.8)


# ---------------------------------------------------------------- 宇宙ステーション（大きな地球の上）
PX, PY, PZ = 60, 62, 60


def build_orbit():
    S = Scene(120, 90, 120)
    c, m = S.col, S.mat
    R = 70
    xs, ys, zs = np.meshgrid(np.arange(120), np.arange(0, 30), np.arange(120), indexing='ij')
    d = np.sqrt((xs + 0.5 - 60) ** 2 + (ys + 0.5 + R - 26) ** 2 + (zs + 0.5 - 60) ** 2)
    shell = (d < R) & (d > R - 3)
    tex = vnoise(120, 120, 18, 4, seed=8) > 0.55
    land = tex[xs[shell], zs[shell]]
    col = np.where(land[:, None], C(0.22, 0.5, 0.22), C(0.1, 0.3, 0.68))
    c[xs[shell], ys[shell], zs[shell]] = col
    m[xs[shell], ys[shell], zs[shell]] = 1
    rg = np.random.default_rng(3)
    for _ in range(40):                                                   # 雲
        x, z = int(rg.integers(0, 116)), int(rg.integers(0, 116))
        y = int(26 - (((x - 60) ** 2 + (z - 60) ** 2) / (2 * R))) + 1
        if y > 0:
            put(c, m, x, x + int(rg.integers(3, 8)), y, y + 1, z, z + int(rg.integers(3, 8)), (0.97, 0.97, 1.0), 1, 0.03)
    # 宇宙ステーション
    W_, G_, P_ = (0.9, 0.9, 0.88), (0.6, 0.6, 0.62), (0.15, 0.2, 0.45)
    put(c, m, PX - 22, PX + 22, PY, PY + 2, PZ - 1, PZ + 1, G_, 1, 0.03)                  # トラス
    for sx in (-20, -12, 12, 20):                                                       # 太陽電池パネル
        put(c, m, PX + sx - 2, PX + sx + 2, PY + 1, PY + 2, PZ - 12, PZ - 1, P_, 1, 0.05)
        put(c, m, PX + sx - 2, PX + sx + 2, PY + 1, PY + 2, PZ + 1, PZ + 12, P_, 1, 0.05)
        for z in range(PZ - 12, PZ + 12, 3):
            put(c, m, PX + sx - 2, PX + sx + 2, PY + 1, PY + 2, z, z + 1, (0.5, 0.55, 0.6), 1, 0.0)
    put(c, m, PX - 3, PX + 3, PY - 2, PY + 3, PZ - 10, PZ + 10, W_, 1, 0.03)              # モジュール
    put(c, m, PX - 8, PX + 8, PY - 1, PY + 2, PZ - 2, PZ + 2, W_, 1, 0.03)
    for z in range(PZ - 8, PZ + 9, 4):
        put(c, m, PX - 3, PX + 3, PY, PY + 1, z, z + 1, (0.3, 0.32, 0.36), 1, 0.0)
    put(c, m, PX - 1, PX + 1, PY + 1, PY + 2, PZ - 10, PZ - 9, (1.4, 1.5, 1.7), 4, 0.0)  # 窓
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = np.array([-0.6, 0.6, -0.5]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.3, 1.25, 1.15); S.amb = C(0.25, 0.27, 0.35); S.lights = []
    S.hor = C(0.0, 0.0, 0.02); S.top = C(0.0, 0.0, 0.01); S.fog0, S.fogk = 1000, 1e9
    return S


SETS = {}


def gs(k):
    if k == 'space':
        return get('space', build_space)
    if k == 'orbit':
        return get('orbit', build_orbit)
    if k == 'pole':
        return get('pole', EV.build_pole)


# ---------------------------------------------------------------- 場面
def frame(k, t):
    w, h = W // RS, H // RS
    T = CLIPS[k]; u = t / T
    if k == 0:   # 前回の北極点：ポールのそばの僕に寄る → 「公転も止まったら？」でゆれる（11/17 冒頭を変更）
        S = gs('pole'); c, m = S.base_c.copy(), S.base_m.copy()
        person(c, m, 40, GY, 46, "stand", look=int(round(math.sin(t * 1.5))))
        z = ease(min(1, u * 1.2))
        cam = lerp((42 + 30, GY + 30, 46 - 50), (40 + 6, GY + 24, 46 - 30), z); tgt = lerp((44, GY + 14, 48), (40, GY + 22, 46), z)
        if T * 0.82 < t < T * 0.82 + 0.4:
            cam, tgt = shake(cam, tgt, 0.8, t)
        img, depth = render(S, c, m, cam, tgt, 50, w, h)
        rg = np.random.default_rng(7); n = 200
        p = np.stack([rg.uniform(10, 75, n), (rg.uniform(0, 40, n) - 2.5 * t) % 40 + GY, rg.uniform(20, 90, n)], 1)
        particles(img, depth, cam, tgt, 50, p, np.tile(C(1.2, 1.2, 1.25), (n, 1)), 0.18)
        return finish(img)
    if k == 1:   # 地球が太陽のまわりを回る（光の尾）
        S = gs('space'); c, m = S.base_c.copy(), S.base_m.copy()
        R = 32; a = 3.9 + 1.3 * u
        ex, ez = SX + R * math.cos(a), SZ + R * math.sin(a)
        mini_earth(c, m, ex, SY, ez, 5)
        cam = (SX, SY + 80, SZ - 66); tgt = (SX, SY - 2, SZ + 2)
        img, depth = render(S, c, m, cam, tgt, 56, w, h)
        stars(img, depth, cam, tgt, 56)
        n = 60; aa = a - np.linspace(0, 0.5, n)
        p = np.stack([SX + R * np.cos(aa), np.full(n, SY), SZ + R * np.sin(aa)], 1)
        particles(img, depth, cam, tgt, 56, p, np.tile(C(0.6, 0.9, 1.6), (n, 1)) * np.linspace(1, 0, n)[:, None], 0.6)
        sunglow(img, depth, cam, tgt, 56, t)
        return finish(img)
    if k == 2:   # 北極点でもアウト：ドン！で僕が横へ吹き飛ぶ
        S = gs('pole'); c, m = S.base_c.copy(), S.base_m.copy()
        t0 = 0.8
        if t < t0:
            person(c, m, 40, GY, 46, "stand")
            cam = (40 + 4, GY + 22, 46 - 26); tgt = (40, GY + 20, 46)
        else:
            s = t - t0
            px = int(40 + 24 * min(s, 1.2))
            person(c, m, px, GY + min(8, int(s * 20)), 46, "float")
            cam = (px - 6, GY + 26, 46 - 40); tgt = (px + 4, GY + 18, 46)
        if t0 <= t < t0 + 0.45:
            cam, tgt = shake(cam, tgt, 1.4, t)
        img, depth = render(S, c, m, cam, tgt, 54, w, h)
        if t >= t0:
            hstreaks(img, depth, cam, tgt, 54, t, 300, n=260, y0=GY, y1=GY + 30, z0=20, z1=90, col=(1.1, 1.1, 1.2), sz=0.3, ln=10)
        return finish(img)
    if k == 3:   # もう戻れない：地球の表面から、全部同じ向きに飛び出していく
        E = earth()
        cam = (32 - 12, 52, 32 - 96 + 10 * u); tgt = (40, 32, 32)
        img, depth = E.draw(1.0, cam, tgt, 52)
        rg = np.random.default_rng(1); n = 500
        la = rg.uniform(-1.3, 1.3, n); lo = rg.uniform(0, 2 * math.pi, n); r = 27.6
        base = np.stack([32 + r * np.cos(la) * np.cos(lo), 32 + r * np.sin(la), 32 + r * np.cos(la) * np.sin(lo)], 1)
        sp = rg.uniform(20, 45, n)[:, None]
        for kk in range(4):
            p = base + np.array([1.0, 0.0, 0.0]) * sp * max(0, t - 0.2 - kk * 0.04)
            particles(img, depth, cam, tgt, 52, p, np.tile(C(1.4, 1.3, 1.1) * (1 - kk / 4), (n, 1)), 0.35)
        return finish(img)
    if k == 4:   # 人も海も空気も：町の上を、水しぶきと雲が横へ飛んでいく
        S = town(); c, m = S.base_c.copy(), S.base_m.copy()
        lift = int(min(3, t * 6))          # 町の箱は高さ70まで（それ以上は体が切れる）
        bx = int(34 + 14 * t)
        person(c, m, bx, GY + lift, 22, "float")
        cam = (bx - 18, GY + 36 + lift, 22 - 62); tgt = (bx + 4, GY + 30 + lift, 28)
        img, depth = render(S, c, m, cam, tgt, 58, w, h)
        hstreaks(img, depth, cam, tgt, 58, t, 260, n=320, y0=GY, y1=GY + 40, z0=0, z1=100, col=(1.1, 1.1, 1.2), sz=0.4, ln=10)
        rg = np.random.default_rng(4); n = 260
        p = np.stack([(rg.uniform(0, 120, n) + 90 * t) % 140 - 20, GY + rg.uniform(0, 30, n) + 12 * t, rg.uniform(10, 95, n)], 1)
        particles(img, depth, cam, tgt, 58, p, np.where(rg.random((n, 1)) < 0.5, C(0.3, 0.55, 1.0), C(1.1, 1.1, 1.1)), 0.7)
        return finish(img)
    if k == 5:   # 宇宙ステーション：静かに浮いている。下の地球から、ちりが飛んでいく
        S = gs('orbit'); c, m = S.base_c.copy(), S.base_m.copy()
        a = -0.7 + 0.9 * ease(u)
        d = 60 - 18 * ease(u)
        cam = (PX + d * math.sin(a), PY + 14 - 6 * u, PZ - d * math.cos(a)); tgt = (PX, PY - 2, PZ)
        img, depth = render(S, c, m, cam, tgt, 52, w, h)
        stars(img, depth, cam, tgt, 52)
        rg = np.random.default_rng(6); n = 160
        p = np.stack([(rg.uniform(0, 140, n) + 70 * t) % 140 - 10, rg.uniform(20, 40, n), rg.uniform(0, 120, n)], 1)
        particles(img, depth, cam, tgt, 52, p, np.tile(C(0.9, 0.9, 1.0) * 0.7, (n, 1)), 0.3)
        return finish(img)
    if k == 6:   # 止まった地球が、太陽へ落ちていく（だんだん速く）
        S = gs('space'); c, m = S.base_c.copy(), S.base_m.copy()
        s = ease(u) ** 2
        ex = SX + 66 - 44 * s
        mini_earth(c, m, ex, SY, SZ)
        cam = (ex + 20, SY + 6, SZ + 5); tgt = (SX, SY, SZ)
        img, depth = render(S, c, m, cam, tgt, 60, w, h)
        stars(img, depth, cam, tgt, 60)
        sunglow(img, depth, cam, tgt, 60, t)
        return finish(img)
    if k == 7:   # 最後：地球をゆっくり回りながら引く
        E = earth()
        a = -0.4 + 0.8 * u
        cam = (32 + 100 * math.sin(a), 46 + 10 * u, 32 - 100 * math.cos(a)); tgt = (32, 33, 32)
        img, depth = E.draw(0.5 + 0.3 * t, cam, tgt, 46)
        return finish(img)


def render_clip(k, out):
    n = int(round(CLIPS[k] * FPS))
    tmp = out[:-4] + '.part.mp4'
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write((np.clip(frame(k, i / FPS), 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
        if i % 30 == 0: print(k, i, flush=True)
    ff.stdin.close()
    if ff.wait() == 0:
        os.replace(tmp, out); print('done', out, flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        ims = []
        for s_ in sys.argv[2].split(','):
            k, t = s_.split(':')
            im = Image.fromarray((np.clip(frame(int(k), float(t)), 0, 1) * 255).astype(np.uint8)).resize((180, 320))
            d = ImageDraw.Draw(im)
            for y in (int(320 * .36), int(320 * .43), int(320 * .68)):
                d.line([(0, y), (180, y)], fill=(255, 0, 0), width=1)
            ims.append(im)
        cols = min(8, len(ims))
        sheet = Image.new('RGB', (180 * cols, 320 * ((len(ims) + cols - 1) // cols)))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % cols) * 180, (i // cols) * 320))
        sheet.save(sys.argv[3])
    else:
        os.makedirs('clips_kouten', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips_kouten/{k + 1:02d}.mp4')
