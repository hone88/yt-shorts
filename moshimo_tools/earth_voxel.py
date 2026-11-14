"""18本目「もしも地球が一瞬で止まったら？」（台本 20261120）。マイクラ調。
使い方: python3 earth_voxel.py stills k:t,... [out.png] / python3 earth_voxel.py 0,1,2"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import render, particles, ease, C, f32, Scene, vnoise
import suika_voxel as SV
import hole_voxel as HV
from elevator_voxel import person, put, finish, shake, SHIRT, SKIN, HAIR, PANTS, SHOE, EYE, MOUTH
import car_voxel as CV
import car2_voxel as C2
from ant_voxel import _set, dust

W, H, FPS, RS = 1080, 1920, 30, 3
_est = [2.4, 4.8, 3.2, 4.4, 6.0, 4.6, 5.8, 3.0]
CLIPS = [round(x * 1.27 * 1.15, 1) for x in _est]   # 声より長く作る（足りないとゆっくり再生でカクつく）
GY = 40
lerp, snap = C2.lerp, C2.snap


def smooth01(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


# ------------------------------------------------------------ 回る地球
class Earth:
    def __init__(s):
        S = Scene(64, 64, 64)
        rr = 27
        xs, ys, zs = np.meshgrid(np.arange(64), np.arange(64), np.arange(64), indexing='ij')
        d = np.sqrt((xs + 0.5 - 32) ** 2 + (ys + 0.5 - 32) ** 2 + (zs + 0.5 - 32) ** 2)
        s.shell = (d < rr) & (d > rr - 3)
        s.lat = np.arcsin(np.clip((ys + 0.5 - 32) / np.maximum(d, 1e-3), -1, 1))[s.shell]
        s.lon = np.arctan2(zs + 0.5 - 32, xs + 0.5 - 32)[s.shell]
        s.tex = vnoise(128, 256, 22, 4, seed=8) > 0.54
        s.var = (0.9 + 0.2 * np.random.default_rng(2).random((s.shell.sum(), 1))).astype(f32)
        S.mat[s.shell] = 1
        S.sun = np.array([-0.5, 0.45, -0.75]); S.sun /= np.linalg.norm(S.sun)
        S.sunc = C(1.15, 1.08, 1.0); S.amb = C(0.32, 0.36, 0.5)
        S.hor = C(0.01, 0.01, 0.03); S.top = C(0.0, 0.0, 0.01); S.fog0, S.fogk = 1000, 1e9
        s.S = S
        rg = np.random.default_rng(9); n = 900
        v = rg.normal(size=(n, 3)); v /= np.linalg.norm(v, axis=1, keepdims=True)
        s.stars = v; s.starc = rg.uniform(0.4, 1.0, (n, 1))

    def paint(s, ang):
        lon = (s.lon - ang) % (2 * np.pi)
        tx = (lon / (2 * np.pi) * 255).astype(int) % 256
        ty = np.clip(((0.5 - s.lat / np.pi) * 127).astype(int), 0, 127)
        land = s.tex[ty, tx]
        col = np.where(land[:, None], C(0.2, 0.5, 0.2), C(0.1, 0.28, 0.65))
        col[np.abs(s.lat) > 1.15] = C(0.92, 0.95, 1.0)
        s.S.col[s.shell] = col * s.var

    def draw(s, ang, cam, tgt, fov, marks=()):
        s.paint(ang)
        w, h = W // RS, H // RS
        img, depth = render(s.S, s.S.col, s.S.mat, cam, tgt, fov, w, h)
        st = np.array(cam) + s.stars * 400
        particles(img, depth, cam, tgt, fov, st, np.tile(C(1, 1, 1), (len(st), 1)) * s.starc, 0.9)
        for p, col, sz in marks:
            particles(img, depth, cam, tgt, fov, np.array([p]), np.array([col]), sz)
        return img, depth


_E = {}


def earth():
    if 'e' not in _E:
        _E['e'] = Earth()
    return _E['e']


# ------------------------------------------------------------ 町（地面を流せるように）
def town():
    S = SV.get('ground', SV.build_ground); S.lights = []
    return S


def roll_town(S, sh):
    c = np.roll(S.base_c, -sh, axis=0); m = np.roll(S.base_m, -sh, axis=0)
    return c.copy(), m.copy()


def hstreaks(img, depth, cam, tgt, fov, t, sp, n=200, y0=GY, y1=GY + 40, z0=0, z1=100, col=(1, 1, 1), seed=5, ln=6, sz=0.12):
    """横（x方向）に流れる風の線"""
    rg = np.random.default_rng(seed)
    p = np.stack([(rg.uniform(0, 160, n) + sp * t) % 160 - 40, rg.uniform(y0, y1, n), rg.uniform(z0, z1, n)], 1)
    for kk in range(ln):
        particles(img, depth, cam, tgt, fov, p - np.array([kk * 0.6, 0, 0]), np.tile(C(*col) * (1 - kk / ln), (n, 1)), sz)


# ------------------------------------------------------------ 北極点
def build_pole():
    S = Scene(80, 70, 100)
    c, m = S.col, S.mat
    put(c, m, 0, 80, 0, GY, 0, 100, (0.75, 0.85, 0.95), 1, 0.05)
    put(c, m, 0, 80, GY - 1, GY, 0, 100, (0.95, 0.97, 1.0), 1, 0.04)
    rg = np.random.default_rng(4)
    for _ in range(14):     # 雪のでこぼこ
        x, z, w, d = rg.integers(0, 76), rg.integers(0, 96), rg.integers(3, 9), rg.integers(3, 9)
        put(c, m, x, x + w, GY, GY + 1, z, z + d, (0.93, 0.96, 1.0), 1, 0.03)
    for y in range(GY, GY + 22):   # 赤白のしまのポール
        col = (0.9, 0.15, 0.15) if (y // 3) % 2 == 0 else (0.97, 0.97, 0.97)
        put(c, m, 46, 48, y, y + 1, 50, 52, col, 1, 0.02)
    put(c, m, 48, 56, GY + 16, GY + 21, 51, 52, (0.95, 0.75, 0.2), 1, 0.03)   # 旗
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = np.array([0.6, 0.35, -0.7]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.15, 1.02, 0.9); S.amb = C(0.6, 0.66, 0.8)
    S.hor = C(0.85, 0.9, 1.0); S.top = C(0.35, 0.55, 0.92); S.fog0, S.fogk = 70, 220
    return S


# ------------------------------------------------------------ 飛行機
def plane(c, m, cx, cy, cz, s=1.0):
    """x の正の向きに飛ぶ旅客機。中心 (cx,cy,cz)。"""
    L = int(18 * s)
    WH, BL, WN = (0.95, 0.96, 0.98), (0.2, 0.35, 0.75), (0.15, 0.22, 0.35)
    r = 3 * s
    xs, ys, zs = np.meshgrid(np.arange(int(cx - L - 3), int(cx + L + 4)), np.arange(int(cy - r - 1), int(cy + r + 2)),
                             np.arange(int(cz - r - 1), int(cz + r + 2)), indexing='ij')
    dx = xs + 0.5 - cx
    rad = r * np.clip(np.minimum((L + 3 - dx) / 4.0, (dx + L + 3) / 9.0 + 0.35), 0, 1)
    body = ((ys + 0.5 - cy) ** 2 + (zs + 0.5 - cz) ** 2 < rad ** 2) & (np.abs(dx) < L + 3)
    _set(c, m, xs[body], ys[body], zs[body], WH, 0.02)
    stripe = body & (np.abs(ys + 0.5 - cy + 0.6 * s) < 0.6)
    _set(c, m, xs[stripe], ys[stripe], zs[stripe], BL, 0.02)
    win = body & (np.abs(ys + 0.5 - cy - 0.9 * s) < 0.55) & (np.abs(dx) < L - 2) & (xs % 2 == 0)
    _set(c, m, xs[win], ys[win], zs[win], WN, 0.0)
    ck = body & (dx > L) & (ys + 0.5 - cy > 0.5)
    _set(c, m, xs[ck], ys[ck], zs[ck], WN, 0.0)
    wy = int(cy - 1)
    for k in range(int(15 * s)):         # 主翼（後ろへ流れる）
        x0 = int(cx + 2 * s - k * 0.45)
        put(c, m, x0 - int(4 * s), x0, wy, wy + 1, int(cz + r + k), int(cz + r + k + 1), WH, 1, 0.02)
        put(c, m, x0 - int(4 * s), x0, wy, wy + 1, int(cz - r - k - 1), int(cz - r - k), WH, 1, 0.02)
    for k in range(int(6 * s)):          # 水平尾翼
        x0 = int(cx - L + 1 - k * 0.4)
        put(c, m, x0 - 3, x0, int(cy), int(cy) + 1, int(cz + r + k - 1), int(cz + r + k), WH, 1, 0.02)
        put(c, m, x0 - 3, x0, int(cy), int(cy) + 1, int(cz - r - k), int(cz - r - k + 1), WH, 1, 0.02)
    for k in range(int(7 * s)):          # 垂直尾翼
        x0 = int(cx - L - 1 - k * 0.5)
        put(c, m, x0, x0 + 4, int(cy + r + k - 1), int(cy + r + k), int(cz), int(cz) + 1, BL, 1, 0.02)
    for sgn in (1, -1):                  # エンジン
        z0 = int(cz + sgn * (r + 4 * s))
        put(c, m, int(cx + 1), int(cx + 5 * s), wy - 2, wy, z0 - 1, z0 + 1, (0.7, 0.72, 0.78), 1, 0.02)


def clouds(c, m, seed=3, n=10, y0=4, y1=20):
    rg = np.random.default_rng(seed)
    for _ in range(n):
        x, y, z = rg.integers(0, 110), rg.integers(y0, y1), rg.integers(0, 110)
        for j in range(4):
            dx, dz = rg.integers(-6, 6), rg.integers(-6, 6)
            w, d, h = rg.integers(6, 14), rg.integers(6, 14), rg.integers(2, 5)
            put(c, m, max(0, x + dx), min(120, x + dx + w), y, y + h, max(0, z + dz), min(120, z + dz + d), (1.0, 1.0, 1.0), 1, 0.03)


def build_air():
    S = Scene(120, 70, 120)
    clouds(S.col, S.mat)
    S.base_c, S.base_m = S.col.copy(), S.mat.copy()
    S.sun = np.array([0.4, 0.8, -0.45]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.1, 1.0, 0.9); S.amb = C(0.62, 0.66, 0.8)
    S.hor = C(0.75, 0.86, 1.0); S.top = C(0.22, 0.45, 0.92); S.fog0, S.fogk = 120, 400
    return S


def build_cabin():
    """機内（x が前）。座席が2列×何列か。"""
    S = Scene(70, 30, 30)
    c, m = S.col, S.mat
    put(c, m, 0, 70, 0, 2, 0, 30, (0.35, 0.38, 0.5), 1, 0.05)          # 床
    put(c, m, 0, 70, 22, 24, 0, 30, (0.92, 0.92, 0.9), 1, 0.02)         # 天井
    put(c, m, 0, 70, 2, 22, 0, 2, (0.9, 0.9, 0.88), 1, 0.02)            # 左の壁
    put(c, m, 0, 70, 2, 22, 28, 30, (0.9, 0.9, 0.88), 1, 0.02)          # 右の壁
    for x in range(3, 70, 7):           # 窓（明るい空）
        put(c, m, x, x + 3, 11, 16, 0, 1, (1.4, 1.5, 1.7), 4, 0.0)
        put(c, m, x, x + 3, 11, 16, 29, 30, (1.4, 1.5, 1.7), 4, 0.0)
    for x in range(6, 66, 9):           # 座席
        for z0 in (3, 8, 18, 23):
            put(c, m, x, x + 4, 2, 6, z0, z0 + 4, (0.2, 0.3, 0.6), 1, 0.04)
            put(c, m, x - 1, x, 2, 13, z0, z0 + 4, (0.2, 0.3, 0.6), 1, 0.04)
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = None; S.amb = C(0.9, 0.9, 0.95)
    S.lights = [((35, 20, 15), (0.9, 0.85, 0.75), 60)]
    S.hor = C(0.8, 0.88, 1.0); S.top = C(0.4, 0.6, 0.95); S.fog0, S.fogk = 200, 400
    return S


def sitter(c, m, cx, fy, cz, look=0, cup=False):
    """座席にすわる人（前＝x+ を向く）。"""
    put(c, m, cx, cx + 6, fy + 4, fy + 6, cz - 3, cz + 3, PANTS)                 # もも
    put(c, m, cx + 5, cx + 7, fy, fy + 5, cz - 3, cz + 3, PANTS)                 # すね
    put(c, m, cx - 1, cx + 2, fy + 6, fy + 14, cz - 3, cz + 3, SHIRT)            # 体
    hy = fy + 14
    put(c, m, cx - 2, cx + 3, hy, hy + 6, cz - 3, cz + 3, SKIN, 1, 0.03)
    put(c, m, cx - 2, cx + 3, hy + 5, hy + 7, cz - 3, cz + 3, HAIR, 1, 0.05)
    put(c, m, cx - 2, cx, hy + 2, hy + 6, cz - 3, cz + 3, HAIR, 1, 0.05)
    put(c, m, cx + 3, cx + 4, hy + 3, hy + 4, cz - 2 + look, cz - 1 + look, EYE, 1, 0.0)
    put(c, m, cx + 3, cx + 4, hy + 3, hy + 4, cz + 1 + look, cz + 2 + look, EYE, 1, 0.0)
    put(c, m, cx + 3, cx + 4, hy + 1, hy + 2, cz - 1, cz + 1, MOUTH, 1, 0.0)
    put(c, m, cx + 2, cx + 5, fy + 9, fy + 11, cz - 4, cz - 2, SHIRT)            # 腕
    if cup:
        put(c, m, cx + 4, cx + 6, fy + 10, fy + 13, cz - 4, cz - 2, (0.95, 0.95, 0.95), 1, 0.0)


# ------------------------------------------------------------ 恐竜
DINO, DINO2 = (0.36, 0.55, 0.3), (0.28, 0.44, 0.24)


def dino(c, m, cx, cz, step=0.0, head=0.0):
    """首の長い恐竜（x+ を向く）。cx,cz は胴の中心。"""
    y = GY
    xs, ys, zs = np.meshgrid(np.arange(cx - 14, cx + 15), np.arange(y + 8, y + 22), np.arange(cz - 7, cz + 8), indexing='ij')
    body = ((xs + 0.5 - cx) / 12.5) ** 2 + ((ys + 0.5 - y - 15) / 6) ** 2 + ((zs + 0.5 - cz) / 6.5) ** 2 < 1
    _set(c, m, xs[body], ys[body], zs[body], DINO, 0.08)
    for i, (lx, lz) in enumerate(((-7, -4), (-7, 2), (7, -4), (7, 2))):
        ph = math.sin(step * 2 * math.pi + (0 if i in (0, 3) else math.pi))
        dx = int(round(ph * 1.5))
        put(c, m, cx + lx + dx - 1, cx + lx + dx + 3, y, y + 11, cz + lz, cz + lz + 3, DINO2, 1, 0.06)
    for k in range(18):                   # 首（上へ前へ）
        a = k / 17
        nx = int(cx + 10 + a * 9); ny = int(y + 17 + a * 16 + head * a * 3);
        put(c, m, nx, nx + 4, ny, ny + 4, cz - 2, cz + 2, DINO, 1, 0.06)
    hx, hy = int(cx + 19), int(y + 33 + head * 3)
    put(c, m, hx, hx + 7, hy, hy + 4, cz - 2, cz + 3, DINO, 1, 0.05)
    put(c, m, hx + 3, hx + 4, hy + 2, hy + 3, cz - 3, cz - 2, EYE, 1, 0.0)
    put(c, m, hx + 3, hx + 4, hy + 2, hy + 3, cz + 3, cz + 4, EYE, 1, 0.0)
    for k in range(20):                   # しっぽ
        a = k / 19
        tx = int(cx - 12 - a * 18); ty = int(y + 15 - a * 9); s_ = max(1, int(3 - 2 * a))
        put(c, m, tx, tx + 2, ty, ty + s_, cz - s_ // 2 - 1, cz + s_ // 2 + 1, DINO, 1, 0.06)


def build_jungle():
    S = Scene(110, 70, 100)
    c, m = S.col, S.mat
    put(c, m, 0, 110, 0, GY, 0, 100, (0.45, 0.33, 0.2), 1, 0.1)
    put(c, m, 0, 110, GY - 1, GY, 0, 100, (0.36, 0.6, 0.24), 1, 0.1)
    rg = np.random.default_rng(6)
    for _ in range(16):    # シダのような木
        x, z = int(rg.integers(2, 106)), int(rg.integers(60, 98))
        h = int(rg.integers(10, 22))
        put(c, m, x, x + 2, GY, GY + h, z, z + 2, (0.45, 0.3, 0.17), 1, 0.05)
        put(c, m, x - 5, x + 7, GY + h, GY + h + 2, z - 5, z + 7, (0.2, 0.5, 0.2), 1, 0.12)
        put(c, m, x - 2, x + 4, GY + h + 2, GY + h + 4, z - 2, z + 4, (0.25, 0.58, 0.22), 1, 0.12)
    for (x, z) in ((90, 8), (96, 30), (10, 12)):   # 火山（奥の小山）
        pass
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = np.array([0.35, 0.8, -0.45]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.15, 1.0, 0.85); S.amb = C(0.58, 0.6, 0.66)
    S.hor = C(0.95, 0.85, 0.7); S.top = C(0.35, 0.55, 0.9); S.fog0, S.fogk = 70, 230
    return S


_S = {}


def get(k, fn):
    if k not in _S:
        _S[k] = fn()
    return _S[k]


# ------------------------------------------------------------ 場面
TOKYO = (0.62, 2.38)   # 地球の上の東京の向き（緯度, 経度）


def surf(lat, lon, ang, r=27.5):
    lo = lon + ang
    return (32 + r * math.cos(lat) * math.cos(lo), 32 + r * math.sin(lat), 32 + r * math.cos(lat) * math.sin(lo))


def frame(k, t):
    w, h = W // RS, H // RS
    Tn = CLIPS[k]
    if k == 0:   # 速く回る地球に寄っていく → 急停止（ゆれ・光る粒が東へ飛び散る）
        E = earth()
        tip = 1.5
        spin = 1.6
        ang = spin * t if t < tip else spin * tip
        z = ease(min(1, t / tip))
        cam = lerp((32 - 20, 52, 32 - 130), (32 - 10, 46, 32 - 88), z); tgt = (32, 33, 32)
        if tip <= t < tip + 0.5:
            cam, tgt = shake(cam, tgt, 1.6 * (1 - (t - tip) / 0.5), t)
        img, depth = E.draw(ang, cam, tgt, 46)
        if t >= tip:     # 地表から、東（回っていた向き）へ飛び出す粒
            u = t - tip
            rg = np.random.default_rng(1); n = 260
            la = rg.uniform(-1.0, 1.0, n); lo = rg.uniform(0, 2 * math.pi, n); sp = rg.uniform(6, 16, n)
            r = 27.6
            base = np.stack([32 + r * np.cos(la) * np.cos(lo), 32 + r * np.sin(la), 32 + r * np.cos(la) * np.sin(lo)], 1)
            tan = np.stack([-np.sin(lo), np.zeros(n), np.cos(lo)], 1)
            for kk in range(4):
                p = base + tan * (sp * max(0, u - kk * 0.03))[:, None]
                particles(img, depth, cam, tgt, 46, p, np.tile(C(1.3, 1.15, 0.8) * (1 - kk / 4) * max(0, 1 - u / 1.6), (n, 1)), 0.35)
        return finish(img)
    if k == 1:   # 東京：顔のアップ → ドン！で体が浮き、東（x+）へ。地面が後ろへ流れる
        S = town()
        t0 = 0.7
        u = max(0.0, t - t0)
        n = round(u * FPS)
        sh = n * 2 if n > 6 else (n * (n + 1)) // 7        # 地面の流れ（1コマ2マスまで）
        c, m = roll_town(S, sh)
        lift = 0 if t < t0 else min(5, round(u * 14))
        person(c, m, 34, GY + lift, 22, "float" if t >= t0 else "stand", look=0)
        k2 = snap(t, t0 + 0.15, 0.7)
        cam = lerp((34, GY + 22, 22 - 20), (34 - 30, GY + 26, 22 - 46), k2); tgt = lerp((34, GY + 22.5, 22), (40, GY + 14, 24), k2)
        fov = 44 + 14 * k2
        if t0 <= t < t0 + 0.45:
            cam, tgt = shake(cam, tgt, 1.2, t)
        img, depth = render(S, c, m, cam, tgt, fov, w, h)
        if t >= t0:
            hstreaks(img, depth, cam, tgt, fov, t, -260 * min(1, u * 2), n=180, y0=GY + 1, y1=GY + 30, z0=6, z1=60)
        return finish(img)
    if k == 2:   # どこなら助かる？：止まった地球をぐるっと回る。北極点と飛行機の印が光る
        E = earth()
        u = t / Tn
        a = -0.9 + 1.2 * ease(u)
        d = 110 - 12 * u
        cam = (32 + d * math.cos(a) * 0.8, 32 + 40 + 14 * u, 32 + d * math.sin(a) * 0.8); tgt = (32, 34, 32)
        marks = []
        p1 = 1 + 0.25 * math.sin(t * 8)
        if t > 0.9:
            marks.append(((32, 32 + 29.5, 32), C(2.0, 1.7, 0.4) * min(1, (t - 0.9) * 3), 3.5 * p1))
        if t > 1.7:
            pp = surf(0.7, 2.0, 1.6 * 1.5, 31.5)
            marks.append((pp, C(2.0, 2.0, 2.0) * min(1, (t - 1.7) * 3), 3.0 * p1))
        img, depth = E.draw(1.6 * 1.5, cam, tgt, 48, marks)
        return finish(img)
    if k == 3:   # 北極点：ポールのそばに立つ僕。何も起きない。カメラがゆっくり回る
        S = get('pole', build_pole)
        c, m = S.base_c.copy(), S.base_m.copy()
        lk = int(round(math.sin(t * 1.4) * 1.2))
        person(c, m, 40, GY, 46, "stand", look=lk)
        u = t / Tn
        z = snap(t, 0.0, 1.2)
        a = -0.35 + 0.7 * ease(u)
        d = lerp((60,), (34,), 1 - z)[0] + 0 * z
        d = 60 - 26 * (1 - z) if False else 22 + 40 * z
        cam = (42 + d * math.sin(a), GY + 18 + 6 * z, 46 - d * math.cos(a)); tgt = (43, GY + 14 + 2 * (1 - z), 48)
        img, depth = render(S, c, m, cam, tgt, 50, w, h)
        rg = np.random.default_rng(7); n = 220     # ゆっくり降る雪
        p = np.stack([rg.uniform(10, 75, n), (rg.uniform(0, 40, n) - 2.5 * t) % 40 + GY, rg.uniform(20, 90, n)], 1)
        particles(img, depth, cam, tgt, 50, p, np.tile(C(1.2, 1.2, 1.25), (n, 1)), 0.18)
        return finish(img)
    if k == 4:   # 飛行機：外から回り込む（雲も一緒に進むので止まって見える）→ 機内（いつもどおり）
        cut = 4.6
        if t < cut:
            S = get('air', build_air)
            c, m = S.base_c.copy(), S.base_m.copy()
            plane(c, m, 60, 36, 60, s=1.4)
            u = t / cut
            a = -1.2 + 1.5 * ease(u)
            d = 70 - 18 * ease(u)
            cam = (60 + d * math.sin(a), 46 - 4 * u, 60 - d * math.cos(a)); tgt = (60, 36, 60)
            img, depth = render(S, c, m, cam, tgt, 52, w, h)
            return finish(img)
        S = get('cabin', build_cabin)
        c, m = S.base_c.copy(), S.base_m.copy()
        tt = t - cut
        sitter(c, m, 33, 2, 10, look=0, cup=True)
        sitter(c, m, 24, 2, 5, look=0)
        z = snap(tt, 0.0, 0.8)
        cam = lerp((69, 18, 15), (62, 17, 15), z); tgt = lerp((20, 11, 12), (24, 13, 10), z)
        img, depth = render(S, c, m, cam, tgt, 62 - 6 * z, w, h)
        return finish(img)
    if k == 5:   # 地上は暴風：上空から町へ降りていく。屋根や木の葉が東へ飛ぶ。風の線
        S = town()
        c, m = S.base_c.copy(), S.base_m.copy()
        u = ease(t / Tn)
        cam = lerp((40, GY + 70, 50 - 30), (40 - 50, GY + 22, 50 - 40), u); tgt = lerp((40, GY, 50), (44, GY + 6, 56), u)
        fov = 56
        img, depth = render(S, c, m, cam, tgt, fov, w, h)
        hstreaks(img, depth, cam, tgt, fov, t, 220, n=420, y0=GY, y1=GY + 26, z0=0, z1=100, col=(1.0, 0.97, 0.92), sz=0.35, ln=10)
        rg = np.random.default_rng(12); n = 160        # 飛ぶ屋根のかけら・葉
        p = np.stack([(rg.uniform(0, 110, n) + 90 * t) % 110 - 15, GY + rg.uniform(2, 20, n) + 2 * np.sin(t * 5 + rg.uniform(0, 6, n)),
                      rg.uniform(10, 95, n)], 1)
        col = np.where(rg.random((n, 1)) < 0.5, C(0.55, 0.22, 0.16), C(0.25, 0.55, 0.22))
        particles(img, depth, cam, tgt, fov, p, col, 1.1)
        return finish(img)
    if k == 6:   # 恐竜のころ：首の長い恐竜が歩く。太陽が空を速く動く
        S = get('jungle', build_jungle)
        c, m = S.base_c.copy(), S.base_m.copy()
        dx = round(t * 6)
        dino(c, m, 40 + dx, 48, step=t * 0.9, head=0.4 * math.sin(t * 1.3))
        sa = -0.6 + 1.2 * (t / Tn)
        S.sun = np.array([math.sin(sa) * 0.9, 0.6 + 0.3 * math.cos(sa), -0.5]); S.sun /= np.linalg.norm(S.sun)
        u = ease(t / Tn)
        cam = lerp((40 - 10, GY + 30, 48 - 80), (40 + dx + 30, GY + 22, 48 - 62), u); tgt = (40 + dx + 6, GY + 20, 48)
        img, depth = render(S, c, m, cam, tgt, 58, w, h)
        return finish(img)
    if k == 7:   # 最後：僕の顔のアップから、一気に引く（候補は置かない）
        S = town()
        c, m = S.base_c.copy(), S.base_m.copy()
        person(c, m, 40, GY, 26, "stand", look=int(round(math.sin(t * 1.5))))
        z = snap(t, 0.5, 0.9)
        cam = lerp((40, GY + 22, 26 - 20), (40, GY + 22, 26 - 50), z); tgt = lerp((40, GY + 22.5, 26), (40, GY + 13, 26), z)
        img, depth = render(S, c, m, cam, tgt, 46 + 16 * z, w, h)
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
        sheet.save(sys.argv[3] if len(sys.argv) > 3 else 'earth_stills.png')
    else:
        os.makedirs('clips', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips/{k + 1:02d}.mp4')
