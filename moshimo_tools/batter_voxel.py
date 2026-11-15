"""受託の見本「もし、世界一のバッターのスイングが100倍だったら？」（台本 20261122・勝手に広島PR）。マイクラ風3D。
バッターはオリジナル（白地に紺のしまのユニフォーム・紺のヘルメット）。実在の選手・球団・公式キャラは描かない。
使い方: python3 batter_voxel.py stills k:t,... out.png / python3 batter_voxel.py 0,1,2"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import particles, ease, C, f32, Scene, vnoise
from elevator_voxel import put
import story_voxel as SV
from story_voxel import hito, H_, aim, HEAD, shoot, cut, snap, lerp, FY

SV.RS = 3
W, H, FPS = SV.W, SV.H, 30
_est = [5.2, 2.7, 3.7, 4.1, 4.4, 3.6, 2.9, 2.4, 5.3, 6.1]
CLIPS = [round(x * 1.27 * 1.15, 1) for x in _est]

P_BAT = {"髪": (0.1, 0.08, 0.07), "服": (0.95, 0.95, 0.95), "服2": (0.15, 0.2, 0.45), "下": (0.93, 0.93, 0.93), "靴": (0.12, 0.12, 0.14)}
NAVY = (0.15, 0.2, 0.45)
WOOD, IRON = (0.75, 0.55, 0.32), (0.55, 0.58, 0.64)


def sky(S, top=(0.3, 0.55, 0.95), hor=(0.82, 0.9, 1.0)):
    S.sun = np.array([0.4, 0.75, -0.5]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.15, 1.05, 0.92); S.amb = C(0.6, 0.63, 0.72); S.lights = []
    S.hor = C(*hor); S.top = C(*top); S.fog0, S.fogk = 120, 320


# ---------------------------------------------------------------- 球場
BX, BZ = 60, 120          # バッターの位置（外野は -z）


def build_stadium():
    S = Scene(120, 70, 160)
    c, m = S.col, S.mat
    put(c, m, 0, 120, 0, FY, 0, 160, (0.3, 0.6, 0.28), 1, 0.06)
    xs, zs = np.meshgrid(np.arange(120), np.arange(160), indexing='ij')
    stripe = ((zs // 8) % 2 == 0)
    c[:, FY - 1, :][stripe] *= 0.9
    d = np.hypot(xs - BX, zs - BZ)
    infield = (d < 34) & (zs < BZ + 6)
    c[:, FY - 1, :][infield & (d > 22)] = C(0.72, 0.52, 0.34)
    c[:, FY - 1, :][d < 6] = C(0.72, 0.52, 0.34)
    put(c, m, BX - 1, BX + 2, FY - 1, FY, BZ - 1, BZ + 2, (0.97, 0.97, 0.97), 1, 0.0)      # ホームベース
    for k in range(40):                                                                  # ファウルライン
        for sgn in (-1, 1):
            x, z = int(BX + sgn * k * 0.7), int(BZ - k * 0.7)
            put(c, m, x, x + 1, FY - 1, FY, z, z + 1, (0.97, 0.97, 0.97), 1, 0.0)
    for i in range(8):                                                                   # 外野席
        put(c, m, 0, 120, FY + i * 3, FY + i * 3 + 3, max(0, 10 - i * 2), 12 - i * 2 + 2, (0.25, 0.35, 0.55) if i % 2 else (0.35, 0.45, 0.65), 1, 0.08)
    put(c, m, 0, 120, FY, FY + 6, 12, 14, (0.15, 0.4, 0.25), 1, 0.03)                     # 外野フェンス
    for x in (8, 108):                                                                   # 照明
        put(c, m, x, x + 2, FY, FY + 50, 6, 8, (0.6, 0.6, 0.62), 1, 0.0)
        put(c, m, x - 4, x + 6, FY + 50, FY + 56, 5, 9, (1.5, 1.5, 1.4), 4, 0.0)
    put(c, m, 0, 120, FY, FY + 4, 150, 160, (0.3, 0.3, 0.33), 1, 0.05)                    # バックネット裏
    S.base_c, S.base_m = c.copy(), m.copy()
    sky(S)
    return S


def bat(c, m, hx, hy, hz, ang, col=WOOD, L=20, broken=0):
    """手元(hx,hy,hz)から水平に伸びるバット。ang は xz 平面の角度。"""
    for s in range(L - broken):
        x = int(round(hx + math.cos(ang) * s)); z = int(round(hz + math.sin(ang) * s))
        r = 1 if s < 8 else 2
        put(c, m, x - (r // 2), x + r - (r // 2), hy, hy + r, z - (r // 2), z + r - (r // 2), col, 1, 0.03)


def batter(t_sw, cx=BX - 6, cz=BZ, col=WOOD, broken=0, face="決意"):
    """t_sw：スイングの進み（0=構え, 1=振り切り）。バッターは -z（ピッチャー側）を向く。"""
    def d(c, m):
        hito(c, m, cx, FY, cz, P_BAT, face=face, arms="front", f=-1, cap=True, stripe=True)
        hy0 = FY + 24
        put(c, m, cx - 4, cx + 4, hy0 + 7, hy0 + 10, cz - 4, cz + 4, NAVY, 1, 0.02)          # 紺のヘルメット
        put(c, m, cx - 4, cx + 4, hy0 + 7, hy0 + 8, cz - 7, cz - 4, NAVY, 1, 0.02)
        hy = FY + 24 - 6
        hx, hz = cx, cz - 9
        a0, a1 = math.radians(20), math.radians(-200)
        k = ease(min(1, max(0, t_sw)))
        bat(c, m, hx, hy, hz, a0 + (a1 - a0) * k, col, broken=broken)
    return d


def ballp(img, depth, cam, tgt, fov, p, col=(1.4, 1.4, 1.35), size=2.0, trail=None, tcol=(1.2, 1.2, 1.2), tsize=0.8):
    p = np.array(p, float)
    if trail is not None:
        n = 14
        for k in range(1, n):
            q = p - np.array(trail) * k / n
            particles(img, depth, cam, tgt, fov, q[None], C(*tcol)[None] * (1 - k / n), tsize * (1 - k / n * 0.6))
    particles(img, depth, cam, tgt, fov, p[None], C(*col)[None], size)


def fire(img, depth, cam, tgt, fov, p, v, t, n=80):
    rg = np.random.default_rng(int(t * 30))
    q = np.array(p)[None] - np.array(v)[None] * rg.uniform(0, 1, (n, 1)) + rg.normal(0, 0.8, (n, 3))
    hot = rg.uniform(0, 1, (n, 1))
    col = np.concatenate([np.full((n, 1), 2.0), 0.5 + 1.0 * hot, 0.15 * hot], 1)
    particles(img, depth, cam, tgt, fov, q, col, 0.7)


# ---------------------------------------------------------------- 空
def build_sky():
    S = Scene(80, 60, 80)
    rg = np.random.default_rng(4)
    for _ in range(14):
        x, z, y = rg.integers(0, 70), rg.integers(0, 70), rg.integers(4, 14)
        for j in range(3):
            dx, dz = rg.integers(-5, 5), rg.integers(-5, 5)
            put(S.col, S.mat, max(0, x + dx), min(80, x + dx + rg.integers(6, 12)), y, y + rg.integers(2, 4),
                max(0, z + dz), min(80, z + dz + rg.integers(6, 12)), (1, 1, 1), 1, 0.03)
    S.base_c, S.base_m = S.col.copy(), S.mat.copy()
    sky(S, top=(0.05, 0.12, 0.4), hor=(0.6, 0.78, 1.0))
    S.fog0, S.fogk = 200, 500
    return S


# ---------------------------------------------------------------- 日本の上（富士山・街・瀬戸内）
def build_japan():
    S = Scene(200, 70, 120)
    c, m = S.col, S.mat
    xs, zs = np.meshgrid(np.arange(200), np.arange(120), indexing='ij')
    hgt = (vnoise(200, 120, 18, 3, seed=5) * 6).astype(int) + 2
    fuji = np.hypot(xs - 40, zs - 60)
    hgt = np.maximum(hgt, (34 - fuji * 1.1).astype(int))
    sea = (xs > 150) & (vnoise(200, 120, 25, 2, seed=8) < 0.55)
    for x in range(200):
        for z in range(120):
            if sea[x, z]:
                put(c, m, x, x + 1, 0, 2, z, z + 1, (0.15, 0.4, 0.7), 1, 0.05); continue
            h_ = int(hgt[x, z])
            col = (0.95, 0.96, 1.0) if h_ > 26 else (0.42, 0.4, 0.45) if h_ > 12 else (0.32, 0.55, 0.28)
            put(c, m, x, x + 1, 0, h_, z, z + 1, col, 1, 0.08)
    rg = np.random.default_rng(3)
    for _ in range(90):                                                     # 大阪あたりの街
        x, z = int(rg.integers(95, 135)), int(rg.integers(30, 90))
        hh = int(rg.integers(4, 16))
        put(c, m, x, x + 3, int(hgt[x, z]), int(hgt[x, z]) + hh, z, z + 3, (0.75, 0.75, 0.8), 1, 0.08)
    S.base_c, S.base_m = c.copy(), m.copy()
    sky(S, top=(0.28, 0.5, 0.92), hor=(0.85, 0.9, 1.0))
    S.fog0, S.fogk = 140, 400
    return S


# ---------------------------------------------------------------- レモン畑（瀬戸内の島の斜面）
LX, LZ = 60, 60


def lemon_tree(c, m, x, y, z, s=1.0):
    put(c, m, x, x + 2, y, y + 5, z, z + 2, (0.45, 0.3, 0.18), 1, 0.05)
    r = int(5 * s)
    xs, ys, zs = np.meshgrid(np.arange(x - r, x + r + 2), np.arange(y + 4, y + 4 + 2 * r), np.arange(z - r, z + r + 2), indexing='ij')
    ok = ((xs + 0.5 - x - 1) ** 2 + ((ys + 0.5 - y - 4 - r) * 1.1) ** 2 + (zs + 0.5 - z - 1) ** 2) < r * r
    rg = np.random.default_rng(x * 131 + z)
    lem = ok & (rg.random(ok.shape) < 0.06) & (((xs + 0.5 - x - 1) ** 2 + (zs + 0.5 - z - 1) ** 2) > (r - 2) ** 2)
    leaf = ok & ~lem
    from ant_voxel import _set
    _set(c, m, xs[leaf], ys[leaf], zs[leaf], (0.16, 0.45, 0.18), 0.12)
    _set(c, m, xs[lem], ys[lem], zs[lem], (1.05, 0.9, 0.15), 0.05)


def build_lemon():
    S = Scene(120, 70, 140)
    c, m = S.col, S.mat
    for z in range(140):                                                     # 海へ下る斜面
        h_ = int(max(1, 16 - z * 0.12)) if z < 110 else 0
        if z >= 110:
            put(c, m, 0, 120, 0, 2, z, z + 1, (0.15, 0.42, 0.72), 1, 0.04)
        else:
            put(c, m, 0, 120, 0, h_, z, z + 1, (0.5, 0.36, 0.22), 1, 0.08)
            put(c, m, 0, 120, h_ - 1, h_, z, z + 1, (0.42, 0.58, 0.26), 1, 0.1)
    for z in range(10, 100, 14):
        for x in range(6, 116, 13):
            if abs(x - LX) < 9 and abs(z - LZ) < 9:
                continue
            y = int(max(1, 16 - z * 0.12))
            lemon_tree(c, m, x, y, z, 0.9 + 0.2 * ((x * z) % 3) / 2)
    for x in range(20, 110, 30):                                             # 遠くの島
        put(c, m, x, x + 18, 0, 6, 128, 136, (0.3, 0.5, 0.3), 1, 0.1)
    S.base_c, S.base_m = c.copy(), m.copy()
    sky(S, top=(0.3, 0.55, 0.95), hor=(0.95, 0.92, 0.85))
    return S


def ground_y(z):
    return int(max(1, 16 - z * 0.12))


# ---------------------------------------------------------------- 海（かき筏・大鳥居）
def build_sea():
    S = Scene(140, 60, 140)
    c, m = S.col, S.mat
    put(c, m, 0, 140, 0, 3, 0, 140, (0.12, 0.38, 0.62), 1, 0.05)
    for gx in (20, 52):                                                      # かき筏
        for gz in (30, 62):
            for k in range(0, 28, 4):
                put(c, m, gx, gx + 28, 3, 4, gz + k, gz + k + 1, (0.6, 0.48, 0.3), 1, 0.05)
                put(c, m, gx + k, gx + k + 1, 3, 4, gz, gz + 28, (0.6, 0.48, 0.3), 1, 0.05)
    TX, TZ = 100, 70                                                         # 大鳥居（朱色）
    V = (0.85, 0.22, 0.12)
    for x0 in (TX - 10, TX + 8):
        put(c, m, x0, x0 + 3, 3, 30, TZ, TZ + 3, V, 1, 0.03)
    put(c, m, TX - 16, TX + 17, 30, 33, TZ - 1, TZ + 4, (0.12, 0.1, 0.1), 1, 0.02)
    put(c, m, TX - 14, TX + 15, 27, 30, TZ, TZ + 3, V, 1, 0.03)
    put(c, m, TX - 12, TX + 13, 22, 24, TZ, TZ + 3, V, 1, 0.03)
    for x in (TX - 6, TX + 4):
        put(c, m, x, x + 2, 24, 27, TZ + 1, TZ + 2, V, 1, 0.03)
    for i in range(10):                                                      # 奥の山（島）
        put(c, m, 60 + i * 6, 66 + i * 6, 0, 8 + int(18 * math.sin(i / 9 * math.pi)), 120, 135, (0.25, 0.45, 0.25), 1, 0.1)
    S.base_c, S.base_m = c.copy(), m.copy()
    sky(S, top=(0.3, 0.55, 0.95), hor=(0.95, 0.88, 0.78))
    return S


def build_teppan():
    S = Scene(70, 40, 70)
    c, m = S.col, S.mat
    put(c, m, 0, 70, 0, 2, 0, 70, (0.5, 0.35, 0.22), 1, 0.04)
    put(c, m, 10, 60, 2, 12, 15, 55, (0.35, 0.25, 0.18), 1, 0.04)
    put(c, m, 10, 60, 12, 13, 15, 55, (0.18, 0.18, 0.2), 1, 0.02)              # 鉄板
    xs, zs = np.meshgrid(np.arange(70), np.arange(70), indexing='ij')
    d = np.hypot(xs - 35, zs - 35)
    from ant_voxel import _set
    for y, rr, col in ((13, 12, (0.85, 0.65, 0.35)), (14, 12, (0.55, 0.32, 0.12)), (15, 11, (0.45, 0.22, 0.08))):
        ok = d < rr
        _set(c, m, xs[ok], np.full(ok.sum(), y), zs[ok], col, 0.06)
    rg = np.random.default_rng(2)
    ok = (d < 10) & (rg.random(d.shape) < 0.15)
    _set(c, m, xs[ok], np.full(ok.sum(), 16), zs[ok], (0.25, 0.5, 0.2), 0.05)    # 青のり
    ok = (d < 9) & (np.abs((xs - zs) % 9) == 0)
    _set(c, m, xs[ok], np.full(ok.sum(), 16), zs[ok], (0.98, 0.95, 0.75), 0.02)  # マヨネーズ
    put(c, m, 50, 52, 13, 14, 30, 42, (0.75, 0.75, 0.78), 1, 0.0)              # へら
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = None; S.amb = C(0.85, 0.78, 0.7); S.lights = [((35, 35, 20), (0.9, 0.75, 0.5), 50)]
    S.hor = C(0.95, 0.85, 0.7); S.top = C(0.6, 0.5, 0.45); S.fog0, S.fogk = 200, 400
    return S


SV.SETS.update({"stadium": build_stadium, "sky2": build_sky, "japan": build_japan, "lemon": build_lemon,
                "sea": build_sea, "teppan": build_teppan})


# ---------------------------------------------------------------- 場面
def frame(k, t):
    T = CLIPS[k]
    u = t / T
    hb = HEAD(BX - 6, FY, BZ)
    if k == 0:   # 構え → 打つ → ボールが空へ（カメラが追って空を見上げる）
        sw = snap(t, 1.6, 0.25)
        bt = batter(sw)
        c_, uu = cut(t, T, [0.3])
        if c_ == 0:
            cam, tgt, fov = aim(hb, -1, 30, 0.6, 2, 48, 0.24)
            return shoot("stadium", cam, tgt, fov, [bt], t=t)
        tb = max(0, t - 1.85)
        bp = (BX - 6, FY + 18 + 30 * tb, BZ - 9 - 60 * tb)
        cam = (BX + 30, FY + 14, BZ + 26); tgt = lerp((BX - 6, FY + 18, BZ - 10), bp, min(1, tb * 1.5))
        fx = lambda img, dp, cm, tg_, fv: ballp(img, dp, cm, tg_, fv, bp, trail=(0, 30 * 0.4, -60 * 0.4))
        return shoot("stadium", cam, tgt, 52, [batter(1.0)], t=t, fx=fx)
    if k == 1:   # ふつうの打球：外野席へ（時速約180キロ）
        tb = t / T
        bp = (BX + 4 * tb, FY + 4 + 40 * math.sin(tb * math.pi * 0.9), BZ - 10 - 110 * tb)
        cam = (BX + 40, FY + 20, BZ - 30); tgt = lerp((BX, FY + 20, BZ - 40), bp, 0.6)
        fx = lambda img, dp, cm, tg_, fv: ballp(img, dp, cm, tg_, fv, bp, trail=(-1, -4, 14))
        return shoot("stadium", cam, tgt, 58, [batter(1.0)], t=t, fx=fx)
    if k == 2:   # 100倍：光るバッター → フルスイング → 衝撃波
        sw = snap(t, 1.4, 0.12)
        bt = batter(sw)
        def fx(img, dp, cm, tg_, fv):
            rg = np.random.default_rng(int(t * 20)); n = 120
            p = np.array(hb) + rg.normal(0, 7, (n, 3)) - np.array([0, 10, 0])
            particles(img, dp, cm, tg_, fv, p, np.tile(C(1.6, 1.3, 0.5), (n, 1)) * min(1, t), 0.35)
            if t > 1.45:
                r = (t - 1.45) * 60; a = np.linspace(0, 2 * np.pi, 160)
                q = np.stack([BX - 6 + r * np.cos(a), np.full(160, FY + 2.0), BZ - 9 + r * np.sin(a)], 1)
                particles(img, dp, cm, tg_, fv, q, np.tile(C(1.6, 1.6, 1.6) * max(0, 1 - (t - 1.45)), (160, 1)), 0.6)
        cam, tgt, fov = aim(hb, -1, 34 + 6 * u, -0.5, 6, 52, 0.24)
        return shoot("stadium", cam, tgt, fov, [bt], t=t, fx=fx, sh=1.2 if 1.4 < t < 2.0 else 0.0)
    if k == 3:   # 木のバットが折れる → 鉄の特製バット
        c_, uu = cut(t, T, [0.55])
        if c_ == 0:
            sw = snap(t, 1.0, 0.15)
            brk = 12 if t > 1.15 else 0
            def fx(img, dp, cm, tg_, fv):
                if t > 1.15:
                    rg = np.random.default_rng(5); n = 40; s = (t - 1.15)
                    v = rg.normal(0, 1, (n, 3)) * 18
                    p = np.array([BX - 6 - 10, FY + 18, BZ - 18]) + v * s + np.array([0, -20, 0]) * s * s
                    particles(img, dp, cm, tg_, fv, p, np.tile(C(*WOOD), (n, 1)), 0.8)
            cam = (BX + 18, FY + 24, BZ - 30); tgt = (BX - 8, FY + 18, BZ - 12)
            return shoot("stadium", cam, tgt, 50, [batter(sw, broken=brk, face="驚き")], t=t, fx=fx)
        cam = (BX - 34 + 4 * uu, FY + 28, BZ - 40); tgt = (BX + 2, FY + 18, BZ - 6)
        return shoot("stadium", cam, tgt, 46, [batter(0.0, col=IRON)], t=t)
    if k == 4:   # ボールが燃える → 燃えない特製ボール（空を背景に、ボールのアップ）
        c_, uu = cut(t, T, [0.55])
        p = (40, 30 + 3 * math.sin(t * 2), 40)
        cam = (40 + 14, 33, 40 - 12); tgt = p
        if c_ == 0:
            fx = lambda img, dp, cm, tg_, fv: (fire(img, dp, cm, tg_, fv, p, (-8, -2, 8), t), ballp(img, dp, cm, tg_, fv, p, col=(1.6, 0.9, 0.3), size=2.2))
            return shoot("sky2", cam, tgt, 40, [], t=t, fx=fx)
        def fx(img, dp, cm, tg_, fv):
            rg = np.random.default_rng(int(t * 30)); n = 40
            q = np.array(p) + rg.normal(0, 2.2, (n, 3))
            particles(img, dp, cm, tg_, fv, q, np.tile(C(0.6, 0.9, 1.6), (n, 1)), 0.3)
            ballp(img, dp, cm, tg_, fv, p, col=(1.3, 1.35, 1.45), size=2.2)
        return shoot("sky2", cam, tgt, 40, [], t=t, fx=fx)
    if k == 5:   # 2000キロ以上：雲を突き抜けて、空が暗くなるほど高く
        p = (40, 10 + 70 * u, 40 - 20 * u)
        cam = (40 + 30, 10 + 70 * u - 18, 40 + 26); tgt = p
        S = SV.get("sky2")
        S.top = C(0.05 * (1 - u) + 0.0, 0.12 * (1 - u) + 0.01, 0.4 * (1 - u) + 0.06)
        fx = lambda img, dp, cm, tg_, fv: ballp(img, dp, cm, tg_, fv, p, trail=(0, -16, 5), size=1.6)
        return shoot("sky2", cam, tgt, 56, [], t=t, fx=fx)
    if k == 6:   # 富士山を越え、大阪を越えて西へ
        c_, uu = cut(t, T, [0.5])
        if c_ == 0:
            p = (10 + 70 * uu, 52, 60)
            cam = (20 + 30 * uu, 46, 10); tgt = (40, 22, 60)
        else:
            p = (100 + 70 * uu, 46, 60)
            cam = (110 + 20 * uu, 40, 14); tgt = (118, 10, 60)
        fx = lambda img, dp, cm, tg_, fv: ballp(img, dp, cm, tg_, fv, p, trail=(-26, 0, 0), size=1.4)
        return shoot("japan", cam, tgt, 60, [], t=t, fx=fx)
    if k == 7:   # 広島県のレモン畑にズドン
        gy = ground_y(LZ)
        land = 0.9
        if t < land:
            p = (LX - 40 + 40 * t / land, gy + 60 - 60 * t / land, LZ)
        else:
            p = (LX, gy + 1, LZ)
        def crater(c, m):
            if t >= land:
                xs, zs = np.meshgrid(np.arange(LX - 6, LX + 7), np.arange(LZ - 6, LZ + 7), indexing='ij')
                ok = np.hypot(xs - LX, zs - LZ) < 5
                for x, z in zip(xs[ok], zs[ok]):
                    m[x, gy - 2:gy, z] = 0
        def fx(img, dp, cm, tg_, fv):
            if t < land:
                ballp(img, dp, cm, tg_, fv, p, trail=(-14, 20, 0), size=1.6)
            else:
                s = t - land; rg = np.random.default_rng(7); n = 120
                v = rg.normal(0, 1, (n, 3)) * np.array([14, 10, 14]) + np.array([0, 16, 0])
                q = np.array([LX, gy, LZ]) + v * s + np.array([0, -30, 0]) * s * s
                particles(img, dp, cm, tg_, fv, q, np.tile(C(0.6, 0.45, 0.3), (n, 1)) * max(0, 1 - s / 2), 0.7)
                ballp(img, dp, cm, tg_, fv, (LX, gy - 0.5, LZ), col=(1.3, 1.35, 1.45), size=1.4)
        cam = (LX + 26, gy + 26, LZ + 34); tgt = (LX, gy + 4, LZ)
        return shoot("lemon", cam, tgt, 54, [crater], t=t, fx=fx, sh=1.0 if land < t < land + 0.4 else 0.0)
    if k == 8:   # 勝手にPR：レモン → かき筏 → 大鳥居 → お好み焼き
        c_, uu = cut(t, T, [0.25, 0.5, 0.75])
        if c_ == 0:
            x, z = 45, 52; y = ground_y(z)
            cam = (x + 1 + 3 * uu, y + 28, z - 14); tgt = (x + 1, y + 8, z + 1)
            return shoot("lemon", cam, tgt, 44, [], t=t)
        if c_ == 1:
            cam = (36 + 10 * uu, 26, 10); tgt = (50, 3, 58)
            return shoot("sea", cam, tgt, 54, [], t=t)
        if c_ == 2:
            cam = (100 - 16 + 8 * uu, 10, 70 - 46); tgt = (100, 18, 71)
            return shoot("sea", cam, tgt, 52, [], t=t)
        cam = (35 + 18 * math.cos(uu * 0.8), 34, 35 - 22); tgt = (35, 14, 37)
        def steam(img, dp, cm, tg_, fv):
            rg = np.random.default_rng(3); n = 50
            q = np.stack([rg.uniform(26, 44, n), 16 + (rg.uniform(0, 12, n) + 6 * t) % 12, rg.uniform(26, 44, n)], 1)
            particles(img, dp, cm, tg_, fv, q, np.tile(C(1.1, 1.1, 1.1) * 0.5, (n, 1)), 0.5)
        return shoot("teppan", cam, tgt, 50, [], t=t, fx=steam)
    if k == 9:   # 最後：穴の中のボール。遠くからバッターが歩いてくる → 引いて瀬戸内の海
        gy = ground_y(LZ)
        def crater(c, m):
            xs, zs = np.meshgrid(np.arange(LX - 6, LX + 7), np.arange(LZ - 6, LZ + 7), indexing='ij')
            ok = np.hypot(xs - LX, zs - LZ) < 5
            for x, z in zip(xs[ok], zs[ok]):
                m[x, gy - 2:gy, z] = 0
        bz = int(LZ - 34 + 20 * ease(min(1, u * 1.3)))
        walker = H_(cx=LX - 4, fy=ground_y(bz), cz=bz, P=P_BAT, face="笑顔", f=1, cap=True, stripe=True, step=t * 1.3)
        def helmet(c, m, x=LX - 4, y=ground_y(bz) + 24, z=bz):
            put(c, m, x - 4, x + 4, y + 7, y + 10, z - 4, z + 4, NAVY, 1, 0.02)
            put(c, m, x - 4, x + 4, y + 7, y + 8, z + 4, z + 7, NAVY, 1, 0.02)
        fx = lambda img, dp, cm, tg_, fv: ballp(img, dp, cm, tg_, fv, (LX, gy - 0.5, LZ), col=(1.3, 1.35, 1.45), size=1.4)
        z = ease(u)
        cam = lerp((LX + 10, gy + 24, LZ + 22), (LX + 30, gy + 60, LZ + 70), z); tgt = lerp((LX - 2, gy + 6, LZ - 8), (LX, gy, LZ - 10), z)
        return shoot("lemon", cam, tgt, 52 + 8 * z, [crater, walker, helmet], t=t, fx=fx)


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
        os.makedirs('clips_batter', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips_batter/{k + 1:02d}.mp4')
