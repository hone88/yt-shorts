"""もしもの続き 5本目「太陽が突然消えたら」マイクラ調の背景クリップ（文字なし）"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voxel as M
from voxel import Scene, render, particles, tone, blur, vnoise, hsh, smooth, ease, C, f32

W, H, FPS, RS = 1080, 1920, 30, 3
R = np.random.default_rng(5)
CLIPS = [3.8, 5.8, 5.5, 7.1, 5.9, 6.5, 7.9]


def put(S, sl, c, m=1, var=0.06):
    shp = S.mat[sl].shape
    v = (1 + R.uniform(-var, var, shp)).astype(f32)[..., None]
    S.col[sl] = np.clip(C(*c) * v, 0, 3); S.mat[sl] = m


def star_sky(base_sky, density=0.996, moon=None, allsky=False):
    def sky(d):
        out = base_sky(d)
        q = np.floor(d * 700).astype(np.int64)
        h = hsh(q[:, 0], q[:, 1], q[:, 2])
        st = (h > density) & ((d[:, 1] > -0.02) | allsky)
        out[st] += ((h[st] - density) / (1 - density) * 1.6)[:, None] * C(1, 1, 1.1)
        if moon is not None:
            md, size, a = moon()
            if a > 0:
                # Minecraft-like square moon: project onto plane around md
                up = np.array([0, 1.0, 0]); rt = np.cross(md, up); rt /= np.linalg.norm(rt); up2 = np.cross(rt, md)
                u = d @ rt; v = d @ up2; fw = d @ md
                inside = (fw > 0) & (np.abs(u) < size) & (np.abs(v) < size)
                gx = np.floor((u + size) / (2 * size) * 8); gy = np.floor((v + size) / (2 * size) * 8)
                tex = 0.85 + 0.15 * hsh(gx.astype(np.int64), gy.astype(np.int64))
                crater = hsh(gx.astype(np.int64) + 7, gy.astype(np.int64) + 3) < 0.22
                mc = np.where(crater, 0.72, 1.0) * tex
                out[inside] = out[inside] * (1 - a) + (mc[inside, None] * C(1.25, 1.22, 1.1)) * a
                glow = np.exp(-np.maximum(np.maximum(np.abs(u), np.abs(v)) - size, 0) / 0.05) * (fw > 0) * ~inside
                out += (glow * 0.25 * a)[:, None] * C(0.7, 0.75, 0.9)
        return out
    return sky


# ------------------------------------------------------------- town (scene 1 & 3)
def build_town():
    S = Scene(120, 60, 230)
    NX, NY, NZ = S.dims
    X, Z = np.meshgrid(np.arange(NX), np.arange(NZ), indexing='ij')
    road = np.abs(X - 60) <= 7
    side = (np.abs(X - 60) > 7) & (np.abs(X - 60) <= 11)
    g = np.where(road[..., None], C(0.3, 0.3, 0.32), np.where(side[..., None], C(0.62, 0.6, 0.56), C(0.33, 0.6, 0.25)))
    g = g * (1 + R.uniform(-0.07, 0.07, (NX, NZ, 1))).astype(f32)
    line = road & (X == 60) & ((Z // 4) % 2 == 0)
    g[line] = C(0.9, 0.9, 0.85)
    S.col[:, 0, :] = g; S.mat[:, 0, :] = 1
    S.windows = []
    S.lamps = []
    walls = [(0.85, 0.8, 0.7), (0.78, 0.55, 0.42), (0.9, 0.9, 0.88), (0.65, 0.68, 0.72), (0.86, 0.74, 0.55)]
    roofs = [(0.55, 0.2, 0.15), (0.25, 0.3, 0.45), (0.35, 0.33, 0.33)]
    for sx in (-1, 1):
        z = 4
        while z < NZ - 16:
            w = int(R.integers(11, 17)); h = int(R.integers(7, 12)); dep = int(R.integers(10, 16))
            x0 = 60 + sx * 13 if sx > 0 else 60 - 13 - dep
            x1 = x0 + dep
            wc = walls[int(R.integers(0, len(walls)))]
            put(S, (slice(x0, x1), slice(1, h), slice(z, z + w)), wc, 1, 0.04)
            rc = roofs[int(R.integers(0, len(roofs)))]
            for k in range(5):
                put(S, (slice(x0 - 1 + k, x1 + 1 - k), slice(h + k, h + k + 1), slice(z - 1, z + w + 1)), rc, 1, 0.05)
            fx = x0 if sx > 0 else x1 - 1
            for wy in (3, 7):
                if wy + 2 >= h: continue
                for wz in range(z + 2, z + w - 2, 4):
                    S.col[fx, wy:wy + 2, wz:wz + 2] = C(0.35, 0.5, 0.65); S.mat[fx, wy:wy + 2, wz:wz + 2] = 3
                    S.windows.append((fx, wy, wz))
            put(S, (slice(fx, fx + 1), slice(1, 4), slice(z + w // 2, z + w // 2 + 2)), (0.4, 0.26, 0.16), 1)
            z += w + int(R.integers(2, 5))
    for z in range(14, NZ - 10, 22):
        for sx in (-1, 1):
            x = 60 + sx * 9
            put(S, (slice(x, x + 1), slice(1, 8), slice(z, z + 1)), (0.3, 0.32, 0.35), 1, 0.0)
            S.col[x, 8, z] = C(0.85, 0.85, 0.75); S.mat[x, 8, z] = 1
            S.lamps.append((x, 8, z))
    for z in range(25, NZ - 10, 22):
        for sx in (-1, 1):
            x = 60 + sx * 10
            put(S, (slice(x, x + 1), slice(1, 5), slice(z, z + 1)), (0.4, 0.28, 0.18))
            put(S, (slice(x - 2, x + 3), slice(5, 9), slice(z - 2, z + 3)), (0.25, 0.5, 0.2), 1, 0.12)
    # parked car
    put(S, (slice(64, 67), slice(1, 3), slice(40, 46)), (0.85, 0.15, 0.12), 1, 0.03)
    put(S, (slice(64, 67), slice(3, 4), slice(41, 45)), (0.2, 0.25, 0.32), 3, 0.03)
    S.base_col = S.col.copy(); S.base_mat = S.mat.copy()
    S.fog0, S.fogk = 80, 260
    return S


def town_state(S, mode, t_after=0.0, lamp_on=1.0, win_frac=0.0):
    c, m = S.base_col.copy(), S.base_mat.copy()
    base = S.sky
    if mode == 'day':
        S.sun = np.array([0.12, 0.52, 0.85]); S.sun /= np.linalg.norm(S.sun)
        S.sunc = C(1.35, 1.2, 1.0); S.amb = C(0.55, 0.6, 0.72)
        S.hor = C(0.78, 0.88, 1.0); S.top = C(0.28, 0.52, 0.95); S.sundisk = 1.4; S.lights = []
        return c, m, Scene.sky.__get__(S)
    S.sun = None; S.amb = C(0.06, 0.07, 0.11)
    S.hor = C(0.02, 0.025, 0.05); S.top = C(0.0, 0.0, 0.01)
    S.lights = []
    if lamp_on > 0:
        for (x, y, z) in S.lamps:
            c[x, y, z] = C(1.6, 1.3, 0.8) * lamp_on; m[x, y, z] = 4
            S.lights.append(((x + 0.5, y - 0.5, z + 0.5), tuple(np.array([1.0, 0.8, 0.45]) * 1.3 * lamp_on), 9))
    for i, (x, y, z) in enumerate(S.windows):
        if hsh(x, y, z) < win_frac:
            c[x, y:y + 2, z:z + 2] = C(1.3, 1.0, 0.55); m[x, y:y + 2, z:z + 2] = 4
    return c, m, star_sky(Scene.sky.__get__(S))


# ------------------------------------------------------------- park (scene 2)
def person(S, x, z, h0, shirt, pants, sit=False, face=0):
    skin = (0.93, 0.76, 0.6)
    if sit:
        put(S, (slice(x, x + 2), slice(h0, h0 + 1), slice(z - 2, z + 1)), pants, 1, 0.02)
        put(S, (slice(x, x + 2), slice(h0 - 2, h0), slice(z - 2, z - 1)), pants, 1, 0.02)
        put(S, (slice(x, x + 2), slice(h0 + 1, h0 + 4), slice(z, z + 1)), shirt, 1, 0.02)
        put(S, (slice(x, x + 2), slice(h0 + 4, h0 + 6), slice(z - 1, z + 1)), skin, 1, 0.02)
        put(S, (slice(x, x + 2), slice(h0 + 6, h0 + 7), slice(z - 1, z + 1)), (0.2, 0.13, 0.08), 1, 0.02)
    else:
        put(S, (slice(x, x + 2), slice(h0, h0 + 3), slice(z, z + 1)), pants, 1, 0.02)
        put(S, (slice(x, x + 2), slice(h0 + 3, h0 + 6), slice(z, z + 1)), shirt, 1, 0.02)
        put(S, (slice(x, x + 2), slice(h0 + 6, h0 + 8), slice(z - 1 if face else z, z + 1)), skin, 1, 0.02)
        put(S, (slice(x, x + 2), slice(h0 + 8, h0 + 9), slice(z - 1 if face else z, z + 1)), (0.2, 0.13, 0.08), 1, 0.02)


def build_park():
    S = Scene(160, 50, 160)
    NX, NY, NZ = S.dims
    X, Z = np.meshgrid(np.arange(NX), np.arange(NZ), indexing='ij')
    n = vnoise(NX, NZ, 10, 3, seed=4)
    g = C(0.33, 0.62, 0.24)[None, None] * (0.85 + 0.3 * n)[..., None]
    path = np.abs((Z - 70) - 0.25 * (X - 80)) < 3.5
    g[path] = C(0.75, 0.68, 0.52)
    pond = ((X - 110) / 18) ** 2 + ((Z - 105) / 12) ** 2 < 1
    g[pond] = C(0.25, 0.45, 0.75)
    S.col[:, 0, :] = g; S.mat[:, 0, :] = 1
    S.mat[:, 0, :][pond] = 3
    for k in range(26):
        x, z = int(R.integers(5, NX - 5)), int(R.integers(80, NZ - 5))
        if pond[x, z] or path[x, z]: continue
        th = int(R.integers(5, 8))
        put(S, (slice(x, x + 1), slice(1, th), slice(z, z + 1)), (0.42, 0.3, 0.18))
        r = int(R.integers(3, 5))
        for y in range(th - 1, th + r + 1):
            rr = r if y < th + r - 1 else r - 1
            put(S, (slice(max(x - rr, 0), x + rr + 1), slice(y, y + 1), slice(max(z - rr, 0), z + rr + 1)), (0.22, 0.5, 0.16), 1, 0.12)
    # bench
    put(S, (slice(70, 78), slice(2, 3), slice(58, 60)), (0.55, 0.36, 0.2))
    put(S, (slice(70, 78), slice(3, 5), slice(60, 61)), (0.55, 0.36, 0.2))
    put(S, (slice(70, 71), slice(1, 2), slice(58, 60)), (0.2, 0.2, 0.22)); put(S, (slice(77, 78), slice(1, 2), slice(58, 60)), (0.2, 0.2, 0.22))
    person(S, 71, 59, 2, (0.85, 0.2, 0.2), (0.25, 0.3, 0.55), sit=True)
    person(S, 74, 59, 2, (0.95, 0.85, 0.3), (0.3, 0.3, 0.35), sit=True)
    # flowers
    for k in range(160):
        x, z = int(R.integers(0, NX)), int(R.integers(20, NZ))
        if pond[x, z] or path[x, z]: continue
        S.col[x, 1, z] = [C(1, 0.9, 0.2), C(1, 0.4, 0.5), C(0.95, 0.95, 1)][k % 3]; S.mat[x, 1, z] = 1
    S.sun = np.array([-0.25, 0.5, 0.83]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.35, 1.2, 1.0); S.amb = C(0.55, 0.6, 0.72)
    S.hor = C(0.78, 0.88, 1.0); S.top = C(0.28, 0.52, 0.95); S.sundisk = 1.4
    S.fog0, S.fogk = 90, 260
    S.base_col = S.col.copy(); S.base_mat = S.mat.copy()
    return S


# ------------------------------------------------------------- earth in space (scene 4)
def build_earth():
    S = Scene(64, 64, 64)
    rr = 27
    xs, ys, zs = np.meshgrid(np.arange(64), np.arange(64), np.arange(64), indexing='ij')
    d = np.sqrt((xs + 0.5 - 32) ** 2 + (ys + 0.5 - 32) ** 2 + (zs + 0.5 - 32) ** 2)
    shell = (d < rr) & (d > rr - 3)
    lat = np.arcsin(np.clip((ys + 0.5 - 32) / np.maximum(d, 1e-3), -1, 1)); lon = np.arctan2(zs + 0.5 - 32, xs + 0.5 - 32)
    tx = ((lon / (2 * np.pi) + 0.5) * 255).astype(int) % 256; ty = np.clip(((0.5 - lat / np.pi) * 127).astype(int), 0, 127)
    landT = vnoise(128, 256, 22, 4, seed=8) > 0.54
    land = landT[ty, tx]
    col = np.where(land[..., None], C(0.16, 0.42, 0.18), C(0.08, 0.2, 0.55))
    ice = np.abs(lat) > 1.15
    col[ice] = C(0.85, 0.9, 0.95)
    S.col[shell] = col[shell] * (0.9 + 0.2 * R.random((shell.sum(), 1))).astype(f32); S.mat[shell] = 1
    city = shell & land & ~ice & (hsh(xs, ys, zs) < 0.06)
    S.col[city] = C(1.6, 1.2, 0.6); S.mat[city] = 4
    S.sun = None; S.amb = C(0.5, 0.55, 0.75)
    S.lights = [((32 - 60, 32 + 50, 32 - 80), (0.25, 0.32, 0.55), 70)]
    S.hor = C(0.0, 0.0, 0.01); S.top = C(0.0, 0.0, 0.0); S.fog0, S.fogk = 1000, 1e9
    return S


# ------------------------------------------------------------- frost (scene 5)
def build_frost():
    S = Scene(70, 24, 90)
    NX, NY, NZ = S.dims
    X, Z = np.meshgrid(np.arange(NX), np.arange(NZ), indexing='ij')
    hm = (1 + 2 * vnoise(NX, NZ, 18, 3, seed=11)).astype(int)
    for x in range(NX):
        for z in range(NZ):
            S.mat[x, :hm[x, z], z] = 1
            S.col[x, :hm[x, z], z] = C(0.4, 0.28, 0.18)
            S.col[x, hm[x, z] - 1, z] = C(0.3, 0.55, 0.22) * (0.85 + 0.3 * R.random())
    S.hm = hm
    for k in range(260):
        x, z = int(R.integers(0, NX)), int(R.integers(0, NZ)); y = hm[x, z]
        hgt = int(R.integers(1, 3))
        S.col[x, y:y + hgt, z] = C(0.25, 0.58, 0.2) * (0.8 + 0.4 * R.random()); S.mat[x, y:y + hgt, z] = 1
    for k in range(14):
        x, z = int(R.integers(3, NX - 3)), int(R.integers(10, NZ - 3)); y = hm[x, z]
        r = int(R.integers(2, 4))
        put(S, (slice(x - r, x + r + 1), slice(y, y + r + 1), slice(z - r, z + r + 1)), (0.18, 0.45, 0.15), 1, 0.15)
        holes = R.random((2 * r + 1, r + 1, 2 * r + 1)) < 0.25
        sub = S.mat[x - r:x + r + 1, y:y + r + 1, z - r:z + r + 1]; sub[holes[:sub.shape[0], :sub.shape[1], :sub.shape[2]]] = 0
    S.front = vnoise(NX, NZ, 14, 3, seed=12)
    S.base_col = S.col.copy(); S.base_mat = S.mat.copy()
    S.sun = np.array([0.3, 0.8, -0.5]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(0.18, 0.24, 0.42); S.amb = C(0.3, 0.38, 0.62); S.sundisk = 0.0
    S.hor = C(0.02, 0.04, 0.09); S.top = C(0.0, 0.0, 0.02); S.fog0, S.fogk = 30, 110
    return S


# ------------------------------------------------------------- frozen ocean cutaway (scene 6)
def build_ocean():
    S = Scene(110, 40, 110)
    NX, NY, NZ = S.dims
    X, Z = np.meshgrid(np.arange(NX), np.arange(NZ), indexing='ij')
    S.col[:, 0, :] = C(0.15, 0.13, 0.12); S.mat[:, 0, :] = 1
    for y in range(1, 26):
        k = y / 26
        glow = (1 - k) ** 1.5
        S.col[:, y, :] = (C(0.02, 0.08, 0.2) * (0.6 + 0.6 * k) + C(0.05, 0.25, 0.55) * glow * 0.9) * (1 + R.uniform(-0.08, 0.08, (NX, NZ, 1))).astype(f32)
        S.mat[:, y, :] = 4
    ice = C(0.8, 0.9, 1.0)
    for y in range(26, 29):
        S.col[:, y, :] = ice * (0.85 + 0.25 * vnoise(NX, NZ, 6, 2, seed=20 + y))[..., None]
        S.mat[:, y, :] = 1
    crack = np.abs(vnoise(NX, NZ, 20, 3, seed=31) - 0.5) < 0.02
    S.col[:, 28, :][crack] = C(0.45, 0.6, 0.8)
    for k in range(40):
        x, z = int(R.integers(0, NX)), int(R.integers(0, NZ))
        put(S, (slice(x, x + int(R.integers(2, 5))), slice(29, 30), slice(z, z + int(R.integers(2, 5)))), (0.9, 0.95, 1.0), 1, 0.05)
    S.sun = None; S.amb = C(0.45, 0.52, 0.75)
    S.lights = []
    S.hor = C(0.01, 0.015, 0.04); S.top = C(0.0, 0.0, 0.01); S.fog0, S.fogk = 120, 400
    return S


# ------------------------------------------------------------- deep sea vent (scene 7)
def build_vent():
    S = Scene(80, 60, 80)
    NX, NY, NZ = S.dims
    hm = (2 + 4 * vnoise(NX, NZ, 16, 3, seed=40)).astype(int)
    for x in range(NX):
        for z in range(NZ):
            S.mat[x, :hm[x, z], z] = 1
            S.col[x, :hm[x, z], z] = C(0.16, 0.15, 0.17) * (0.8 + 0.4 * R.random())
    cx, cz = 40, 46
    for y in range(hm[cx, cz], 36):
        r = 4.5 - 2.6 * (y / 36) + 0.8 * math.sin(y * 0.9)
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            for z in range(int(cz - r - 1), int(cz + r + 2)):
                if (x - cx) ** 2 + (z - cz) ** 2 <= r * r:
                    S.mat[x, y, z] = 1
                    S.col[x, y, z] = C(0.3, 0.27, 0.27) * (0.8 + 0.5 * R.random())
                    if R.random() < 0.08: S.col[x, y, z] = C(0.45, 0.32, 0.2)
    S.col[cx - 1:cx + 2, 35, cz - 1:cz + 2] = C(1.6, 0.6, 0.15); S.mat[cx - 1:cx + 2, 35, cz - 1:cz + 2] = 4
    for k in range(70):
        a = R.uniform(0, 6.28); rr = R.uniform(6, 13)
        x, z = int(cx + rr * math.cos(a)), int(cz + rr * math.sin(a))
        if not (0 <= x < NX and 0 <= z < NZ): continue
        y = hm[x, z]; h = int(R.integers(2, 6))
        S.col[x, y:y + h, z] = C(0.92, 0.9, 0.85); S.mat[x, y:y + h, z] = 1
        S.col[x, y + h, z] = C(1.3, 0.2, 0.2); S.mat[x, y + h, z] = 4
    S.sun = None; S.amb = C(0.22, 0.27, 0.38)
    S.lights = [((cx + 0.5, 37, cz + 0.5), (1.0, 0.5, 0.18), 18), ((cx + 0.5, 20, cz - 16), (0.45, 0.6, 0.85), 30)]
    S.hor = C(0.01, 0.04, 0.09); S.top = C(0.0, 0.02, 0.05); S.fog0, S.fogk = 15, 70
    S.vent = (cx + 0.5, 36.0, cz + 0.5)
    return S


_S = {}


def get(k, fn):
    if k not in _S: _S[k] = fn()
    return _S[k]


def finish(img, expo=1.12, grade=(1, 1, 1)):
    img = tone(img, expo) * C(*grade)
    img = np.repeat(np.repeat(img, RS, 0), RS, 1)
    bright = np.clip(img - 0.85, 0, None)
    img = img + blur(bright, 12) * 1.2
    return np.clip(img, 0, 1)


def frame(k, t):
    w, h = W // RS, H // RS
    T = CLIPS[k]; p = ease(t / T)
    if k == 0:   # 昼なのに真っ暗
        S = get('town', build_town)
        tb = 0.9
        if t < tb:
            c, m, sky = town_state(S, 'day')
        else:
            dt = t - tb
            on = 0.0
            if dt > 0.25: on = 1.0 if (dt > 0.45 or 0.32 < dt < 0.38) else 0.0
            c, m, sky = town_state(S, 'night', dt, on, win_frac=min(0.6, max(0, dt - 0.9) * 0.35))
        S.sky = sky
        cam = (60, 4.0, 6 + 10 * p); tgt = (60, 28, 200)
        img, depth = render(S, c, m, cam, tgt, 72, w, h)
        del S.sky
        # birds in the day sky
        if t < tb:
            bx = np.array([40, 46, 52, 58, 50]) + 30 * t; by = np.array([50, 53, 49, 52, 56]); bz = np.full(5, 160.0)
            particles(img, depth, cam, tgt, 72, np.stack([bx, by, bz], 1), np.tile(C(0.1, 0.1, 0.12), (5, 1)), 1.0)
        return finish(img)
    if k == 1:   # いつもの昼の公園
        S = get('park', build_park)
        a = math.radians(-14 + 26 * p)
        cam = (74 + 3 * p, 6.5, 30)
        tgt = (cam[0] + 100 * math.sin(a), 16, cam[2] + 100 * math.cos(a))
        img, depth = render(S, S.col, S.mat, cam, tgt, 70, w, h)
        bx = np.array([100, 105, 110]) - 20 * t; by = np.array([38, 40, 37]); bz = np.full(3, 140.0)
        particles(img, depth, cam, tgt, 70, np.stack([bx, by, bz], 1), np.tile(C(0.1, 0.1, 0.12), (3, 1)), 1.0)
        return finish(img)
    if k == 2:   # 月も消える
        S = get('town', build_town)
        c, m, _ = town_state(S, 'night', 5, 1.0, 0.45)
        md = np.array([0.0, 0.42, 0.9]); md /= np.linalg.norm(md)
        a = 1.0 - smooth(1.9, 2.5, t)
        S.sky = star_sky(Scene.sky.__get__(S), moon=lambda: (md, 0.075, a))
        cam = (60, 4.0, 40); tgt = (60, 30 + 22 * p, 200)
        img, depth = render(S, c, m, cam, tgt, 70, w, h)
        del S.sky
        return finish(img)
    if k == 3:   # 地球がまっすぐ進む
        S = get('earth', build_earth)
        E = np.array([32.0, 32.0, 32.0])
        S.sky = star_sky(Scene.sky.__get__(S), 0.994, allsky=True)
        ang = 0.25 * t
        cam = (32 - 20 * p, 175, 32 - 95); tgt = (32 + 4 * p, 32, 58)
        img, depth = render(S, S.col, S.mat, cam, tgt, 62, w, h)
        del S.sky
        Ro = 80.0; v = 12.0
        aa = np.linspace(-1.6, 1.6, 200)
        orbit = np.stack([E[0] + Ro * np.sin(aa) - v * t, np.full_like(aa, E[1]), E[2] + Ro - Ro * np.cos(aa)], 1)
        s_ = np.arange(-300, 600, 5.0)
        straight = np.stack([E[0] + s_ - v * t, np.full_like(s_, E[1]), np.full_like(s_, E[2])], 1)
        straight = straight[np.abs(straight[:, 0] - E[0]) > 30]
        orbit = orbit[np.hypot(orbit[:, 0] - E[0], orbit[:, 2] - E[2]) > 30]
        ka = smooth(0.4, 1.4, t)
        particles(img, depth, cam, tgt, 62, orbit, np.tile(C(0.75, 0.82, 1.0) * ka, (len(orbit), 1)), 2.4)
        ahead = straight[:, 0] > E[0]
        sc = np.where(ahead[:, None], C(1.4, 1.15, 0.3), C(0.7, 0.6, 0.25)) * smooth(1.2, 2.4, t)
        particles(img, depth, cam, tgt, 62, straight, sc, 2.8)
        return finish(img)
    if k == 4:   # 世界が凍り始める
        S = get('frost', build_frost)
        c, m = S.base_col.copy(), S.base_mat.copy()
        thr = 0.15 + 0.75 * (t / T)
        froz = S.front < thr
        xs, ys, zs = np.nonzero(m > 0)
        fz = froz[xs, zs] & (ys >= S.hm[xs, zs] - 1)
        mixk = np.clip((thr - S.front[xs, zs]) * 6, 0, 1)[fz][:, None]
        c[xs[fz], ys[fz], zs[fz]] = c[xs[fz], ys[fz], zs[fz]] * (1 - mixk) + C(0.85, 0.93, 1.05) * mixk
        cam = (35, 6.5 - 1.5 * p, 8 + 12 * p); tgt = (35, 1, 50)
        img, depth = render(S, c, m, cam, tgt, 70, w, h)
        rg = np.random.default_rng(3)
        n = 260
        sp = np.stack([rg.uniform(0, 70, n), (rg.uniform(0, 30, n) - 2.2 * t) % 30, rg.uniform(0, 90, n)], 1)
        particles(img, depth, cam, tgt, 70, sp, np.tile(C(0.9, 0.95, 1.0), (n, 1)), 0.18)
        return finish(img, grade=(0.95, 1.0, 1.08))
    if k == 5:   # 海にふたができる
        S = get('ocean', build_ocean)
        S.sky = star_sky(Scene.sky.__get__(S), 0.995)
        cam = (55 + 4 * p, lerp(92, 40, p), lerp(30, -48, p)); tgt = (55, lerp(0, 20, p), lerp(70, 40, p))
        img, depth = render(S, S.col, S.mat, cam, tgt, 66, w, h)
        del S.sky
        return finish(img)
    if k == 6:   # 深海で生き残る
        S = get('vent', build_vent)
        cam = (40, 14 + 4 * p, -8 + 14 * p); tgt = (40, 24, 46)
        img, depth = render(S, S.col, S.mat, cam, tgt, 66, w, h)
        rg = np.random.default_rng(8)
        n = 220
        age = (rg.uniform(0, 4, n) + t) % 4
        vx, vy, vz = S.vent
        sm = np.stack([vx + rg.normal(0, 1, n) * (0.5 + age * 0.9) + 0.6 * np.sin(age * 3 + rg.uniform(0, 6, n)), vy + age * 6, vz + rg.normal(0, 1, n) * (0.5 + age * 0.9)], 1)
        heat = np.clip(1 - age / 4, 0, 1)[:, None]
        scol = C(1.5, 0.7, 0.25) * heat ** 2 + C(0.25, 0.25, 0.3) * (1 - heat)
        particles(img, depth, cam, tgt, 66, sm, scol, 0.7)
        m_ = 40
        cr = np.stack([30 + 22 * rg.random(m_) + 2 * np.sin(t * 0.8 + rg.uniform(0, 6, m_)), 12 + 25 * rg.random(m_) + 1.5 * np.sin(t * 1.1 + rg.uniform(0, 6, m_)), 28 + 30 * rg.random(m_) + 2 * np.cos(t * 0.7 + rg.uniform(0, 6, m_))], 1)
        tw = (0.6 + 0.4 * np.sin(t * 3 + rg.uniform(0, 6, m_)))[:, None]
        particles(img, depth, cam, tgt, 66, cr, C(0.4, 1.4, 1.5) * tw, 0.45)
        return finish(img)


def lerp(a, b, t):
    return a + (b - a) * t


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
        for spec in sys.argv[2].split(','):
            k, t = spec.split(':'); k = int(k); t = float(t)
            Image.fromarray((frame(k, t) * 255).astype(np.uint8)).save(f'st_{k}_{t:04.1f}.png')
    else:
        os.makedirs('clips', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips/{k + 1:02d}.mp4')
