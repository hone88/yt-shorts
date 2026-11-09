"""16本目「もしもスカイツリーからアリを落としたら？」（台本 20261118）。マイクラ調。
車の回（car2_voxel.py）と同じく、全場面でカメラを大きく動かす（寄る・引く・回る）。
使い方: python3 ant_voxel.py stills [k:t,...] / python3 ant_voxel.py 0,1,2"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import render, particles, smooth, ease, C, f32
import suika_voxel as SV
from elevator_voxel import person, put, draw_x, finish, shake
import car_voxel as CV
import car2_voxel as C2

W, H, FPS, RS = 1080, 1920, 30, 3
CLIPS = [4.4, 4.4, 5.6, 8.4, 5.7, 5.3, 6.7, 5.1]
GY = SV.GY
lerp, snap, ground = C2.lerp, C2.snap, C2.ground
BODY = (0.15, 0.15, 0.18)     # アリの体（黒・少し青みのグレー）
LEG = (0.12, 0.12, 0.15)
EYE = (0.02, 0.02, 0.03)
FOOT = 1.45                   # 足の先は体の中心から 1.45r 下（ひざが高い）


def _set(c, m, X, Y, Z, col, var=0.12):
    ok = (X >= 0) & (Y >= 0) & (Z >= 0) & (X < c.shape[0]) & (Y < c.shape[1]) & (Z < c.shape[2])
    X, Y, Z = X[ok], Y[ok], Z[ok]
    c[X, Y, Z] = (C(*col) * (1 - var + 2 * var * np.random.default_rng(len(X)).random((len(X), 1)))).astype(f32); m[X, Y, Z] = 1


def ant(c, m, cx, cy, cz, r, yaw=0.0, phase=0.0, pose="walk", pitch=0.0):
    """黒いブロックのアリ（参考画像の形）。頭が+x。cy は体の中心（足の先は cy-1.45r）。
    pose: walk（6本脚で立つ）/ fall（脚を横に広げる）"""
    ca, sa = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)

    def W_(lx, ly, lz):
        lx, ly = lx * cp - ly * sp, lx * sp + ly * cp
        return cx + lx * ca - lz * sa, cy + ly, cz + lx * sa + lz * ca

    def blob(ox, oy, oz, rx, ry, rz, col, pw=2.0):
        """pw=2 で楕円、4 で角の丸い箱"""
        R_ = max(rx, ry, rz) * 1.2 + 1
        px, py, pz = W_(ox, oy, oz)
        xs, ys, zs = np.meshgrid(np.arange(int(px - R_), int(px + R_) + 2), np.arange(int(py - R_), int(py + R_) + 2),
                                 np.arange(int(pz - R_), int(pz + R_) + 2), indexing='ij')
        dx, dy, dz = xs + 0.5 - px, ys + 0.5 - py, zs + 0.5 - pz
        lx = dx * ca + dz * sa; lz = -dx * sa + dz * ca; ly = dy
        lx, ly = lx * cp + ly * sp, -lx * sp + ly * cp
        ins = np.abs(lx / rx) ** pw + np.abs(ly / ry) ** pw + np.abs(lz / rz) ** pw < 1
        _set(c, m, xs[ins], ys[ins], zs[ins], col)

    def line(pts, col, th):
        for p0, p1 in zip(pts[:-1], pts[1:]):
            n = int(max(2, math.dist(p0, p1) * 2))
            for i in range(n + 1):
                k = i / n
                x, y, z = W_(*[a + (b - a) * k for a, b in zip(p0, p1)])
                h = max(0.5, th / 2)
                X, Y, Z = np.meshgrid(np.arange(int(x - h + 0.5), int(x + h + 0.5) + 1), np.arange(int(y - h + 0.5), int(y + h + 0.5) + 1),
                                      np.arange(int(z - h + 0.5), int(z + h + 0.5) + 1), indexing='ij')
                _set(c, m, X.ravel(), Y.ravel(), Z.ravel(), col, 0.08)

    blob(-2.05 * r, 0.25 * r, 0, 1.3 * r, 1.0 * r, 1.05 * r, BODY, 2.2)         # おなか（段々の大きな丸）
    blob(-0.75 * r, 0.05 * r, 0, 0.3 * r, 0.42 * r, 0.28 * r, BODY, 3.0)         # くびれのこぶ
    blob(0.35 * r, 0.05 * r, 0, 0.85 * r, 0.42 * r, 0.42 * r, BODY, 4.0)         # むね（箱）
    blob(0.85 * r, 0.25 * r, 0, 0.4 * r, 0.42 * r, 0.44 * r, BODY, 4.0)          # むねの前の盛り上がり
    blob(1.95 * r, 0.15 * r, 0, 0.7 * r, 0.62 * r, 0.68 * r, BODY, 4.0)          # 頭（角の丸い箱）
    for s in (-1, 1):
        blob(2.15 * r, 0.3 * r, s * 0.62 * r, 0.2 * r, 0.18 * r, 0.1 * r, EYE, 4.0)    # 目（小さな四角）
        line([(2.55 * r, -0.25 * r, s * 0.32 * r), (3.15 * r, -0.4 * r, s * 0.32 * r), (3.25 * r, -0.4 * r, s * 0.05 * r)], LEG, 0.24 * r)  # あご
        wig = 0.2 * r * math.sin(phase * 3 + s)
        line([(2.35 * r, 0.65 * r, s * 0.3 * r), (2.2 * r, 1.75 * r, s * 0.45 * r),                               # 触角（くの字・長い）
              (3.3 * r, 2.05 * r + wig, s * 0.75 * r), (4.0 * r, 1.65 * r + wig, s * 0.95 * r)], LEG, 0.22 * r)
        for j, (ox, fx, tx) in enumerate(((0.95, 0.5, 1.5), (0.45, 0.0, 0.1), (-0.05, -0.5, -1.7))):
            sw = 0.3 * r * math.sin(phase * 6 + j * 2.1 + (0 if s > 0 else math.pi))
            if pose == "fall":
                knee = ((ox + fx) * r, 0.45 * r, s * 1.4 * r); foot = ((ox + tx) * r, 0.15 * r, s * 2.9 * r)
            else:
                knee = ((ox + fx) * r + sw * 0.4, 0.55 * r, s * 1.25 * r); foot = ((ox + tx) * r + sw, -FOOT * r, s * 2.3 * r)
            tip = (foot[0] + 0.25 * r * (1 if tx >= 0 else -1), foot[1], foot[2] + s * 0.25 * r)
            line([(ox * r, -0.25 * r, s * 0.3 * r), knee, foot, tip], LEG, 0.22 * r)


# ---------------------------------------------------------------- 空の場面
def sky(t, drop, cam, tgt, fov, ant_kw, deck_up=None, lines=0.0, wind=0.0, car_y=None):
    S = SV.get('sky', SV.build_sky)
    c = np.zeros((60, 60, 60, 3), f32); m = np.zeros((60, 60, 60), np.uint8)
    SV.tower(c, m, drop)
    if deck_up is not None and deck_up < 40:
        put(c, m, 12, 26, 22 + deck_up, 25 + deck_up, 14, 46, (0.85, 0.88, 0.95), 1, 0.02)         # 展望台の床
        put(c, m, 25, 26, 25 + deck_up, 27 + deck_up, 14, 46, (0.6, 0.65, 0.72), 1, 0.02)          # ふち
    if car_y is not None and -10 < car_y < 70:
        CV.car_s(c, m, 22, car_y, 26, 5, rot=t * 6)
    ant(c, m, **ant_kw)
    img, depth = render(S, c, m, cam, tgt, fov, W // RS, H // RS)
    if lines > 0:
        C2.speedlines(img, depth, cam, tgt, fov, t, sp=20 * lines, n=int(120 * lines))
    if wind > 0:
        rg = np.random.default_rng(9); n = 160
        p = np.stack([rg.uniform(14, 58, n), rg.uniform(4, 58, n), (rg.uniform(0, 60, n) + 40 * t) % 60], 1)
        for kk in range(6):
            particles(img, depth, cam, tgt, fov, p - np.array([0, 0, kk * 1.2]), np.tile(C(1, 1, 1) * wind * (1 - kk / 6), (n, 1)), 0.12)
    return finish(img)


def dust(img, depth, cam, tgt, fov, k, x, y, z):
    rg = np.random.default_rng(3); n = 60
    a = rg.uniform(0, 2 * math.pi, n); sp = rg.uniform(1.5, 4, n)
    p = np.stack([x + np.cos(a) * sp * k * 2, y + 0.3 + 2.5 * k * (1 - k) * rg.uniform(0.5, 1.5, n), z + np.sin(a) * sp * k * 2], 1)
    particles(img, depth, cam, tgt, fov, p, np.tile(C(0.85, 0.78, 0.62) * (1 - k), (n, 1)), 0.4)


def tree(c, m, x0, z0):
    put(c, m, x0, x0 + 8, GY, 70, z0, z0 + 8, (0.4, 0.27, 0.16), 1, 0.1)                  # 幹
    for y in range(GY, 70, 3):
        put(c, m, x0, x0 + 8, y, y + 1, z0 - 1, z0, (0.32, 0.21, 0.12), 1, 0.08)
    for (dx, dz, s) in ((-12, 14, 4), (14, 20, 5)):                                       # 森の下草
        put(c, m, x0 + dx - s, x0 + dx + s, GY, GY + 2 * s, z0 + dz - s, z0 + dz + s, (0.2, 0.48, 0.2), 1, 0.15)
    for (tx, tz) in ((8, 74), (52, 80), (66, 68), (20, 90)):                               # 奥の木
        put(c, m, tx, tx + 5, GY, 70, tz, tz + 5, (0.36, 0.25, 0.15), 1, 0.1)
    put(c, m, 0, 80, GY, 66, 92, 100, (0.15, 0.38, 0.16), 1, 0.2)                          # 森の奥（町をかくす）
    put(c, m, 0, 80, 64, 70, 58, 100, (0.17, 0.42, 0.18), 1, 0.15)                         # 上の葉


def frame(k, t):
    w, h = W // RS, H // RS
    T = CLIPS[k]
    if k == 0:   # 展望台のふちを歩くアリに超アップ → ふちから落ちた瞬間、一気に引いて高さを見せる
        tip = 1.3
        f = max(0.0, t - tip)
        drop = 6 * f * f if f < 1 else 6 + 12 * (f - 1)        # すぐに一定の遅い速さになる
        ax = 18 + min(t, tip) * 3.0
        ay = 25 + 1.45 * 2.4 + 0.3
        k2 = snap(t, tip, 1.6)
        a = 0.9 + 0.7 * k2
        d = 34 + 26 * k2
        cam = (30 + d * math.sin(a), 30 + 12 + 4 * k2, 30 - d * math.cos(a)); tgt = (27, 28 - 4 * k2, 30)
        kw = dict(cx=ax if t < tip else 30, cy=ay if t < tip else 30, cz=30, r=2.4, yaw=0.0, phase=t * 4,
                  pose="walk" if t < tip else "fall", pitch=-0.5 * min(1, f * 2))
        return sky(t, drop, cam, tgt, 40 + 32 * k2, kw, deck_up=int(min(60, drop)) if t >= tip else 0, lines=min(1, f) * 0.4)
    if k == 1:   # 「車みたいにぺしゃんこ？」→ ×  →「いいえ、平気」草の上で触角を動かすアリ
        if t < T * 0.58:
            out = C2.frame(5, 2.2 + t * 0.4)
            if t >= T * 0.38:
                out = draw_x(out, min(1.0, (t - T * 0.38) / 0.15))
            return out
        u = (t - T * 0.58) / (T * 0.42)
        S, c, m = ground()
        ant(c, m, 40, GY + 1.45 * 2.4 + 0.2, 52, 2.4, yaw=-1.9, phase=t * 3, pose="walk")
        z = ease(u)
        cam = lerp((40 - 8, GY + 14, 52 - 30), (40 - 12, GY + 18, 52 - 40), z); tgt = (40, GY + 3, 52)
        img, depth = render(S, c, m, cam, tgt, 44, w, h)
        return finish(img, grade=(1.05, 1.05, 1.0))
    if k == 2:   # 車はすぐ横をビューンと落ちていく → アリのまわりをカメラが回る（アリはまだ空の上）
        drop = 20 + 4 * t
        a = 0.6 + 0.55 * t
        d = 40 - 8 * ease(t / T)
        cam = (30 + d * math.sin(a), 40, 30 - d * math.cos(a)); tgt = (30, 29, 30)
        car_y = 80 - 75 * max(0, t - 0.5) if t < 2.2 else None
        kw = dict(cx=30, cy=30, cz=30, r=2.4, yaw=t * 0.7, phase=t * 3, pose="fall", pitch=0.15 * math.sin(t * 2))
        if car_y is not None and car_y < 60:
            cam, tgt = shake(cam, tgt, 0.4, t)
        return sky(t, drop, cam, tgt, 54, kw, lines=0.25, car_y=car_y)
    if k == 3:   # 時速10キロ＝ジョギング：ジョギングする僕の横を、アリがゆっくり落ちていく
        S, c, m = ground()
        bob = abs(math.sin(t * 7)) * 1.2
        person(c, m, 34, GY + int(round(bob)), 52, "stand", look=0)
        ay = GY + 26 - 20 * (t / T)
        ant(c, m, 45, ay, 55, 2.0, yaw=-1.57, phase=t * 3, pose="fall", pitch=0.2 * math.sin(t * 1.7))
        a = -0.15 + 0.3 * ease(t / T)
        d = 44 - 2 * ease(t / T)
        cam = (40 + d * math.sin(a), GY + 20, 52 - d * math.cos(a)); tgt = (40, GY + 23 + (ay - GY - 16) * 0.2, 53)
        cam, tgt = shake(cam, tgt, 0.12, t)
        img, depth = render(S, c, m, cam, tgt, 56, w, h)
        rg = np.random.default_rng(4); n = 40                                         # 走る横線（風）
        p = np.stack([rg.uniform(20, 60, n), rg.uniform(GY + 4, GY + 30, n), (rg.uniform(30, 80, n) - 60 * t) % 50 + 30], 1)
        for kk in range(5):
            particles(img, depth, cam, tgt, fov := 56, p + np.array([0, 0, kk * 1.2]), np.tile(C(1, 1, 1) * 0.6 * (1 - kk / 5), (n, 1)), 0.1)
        return finish(img)
    if k == 4:   # 2分以上・風で流される：アリから一気に遠くへ引く。白い風の線が横に流れる
        drop = 40 + 5 * t
        z = snap(t, 0.6, 2.2)
        d = 38 + 26 * z
        a = 1.3 - 0.5 * z
        drift = 3 * math.sin(t * 0.8)
        cam = (30 + d * math.sin(a), 38 + 8 * z, 30 - d * math.cos(a)); tgt = (30 - 4 * z, 29, 30)
        kw = dict(cx=30, cy=30, cz=30 + drift, r=2.4, yaw=t * 1.2, phase=t * 3, pose="fall", pitch=0.4 * math.sin(t * 2.3))
        return sky(t, drop, cam, tgt, 50 + 20 * z, kw, wind=0.8)
    if k == 5:   # 着地：上から落ちてきてポン → 小さくはねて、そのまま歩きだす
        S, c, m = ground()
        L = 1.1
        if t < L:
            ay = GY + 3.7 + 24 * (1 - t / L)
        else:
            u = t - L
            ay = GY + 3.7 + max(0, 3 * math.sin(min(u, 0.35) / 0.35 * math.pi)) if u < 0.35 else GY + 3.7
        walk = max(0, t - L - 0.6)
        ax = 40 - 4.5 * walk
        ant(c, m, ax, ay, 52, 2.4, yaw=math.pi if t > L + 0.4 else 0.4 * t, phase=t * (6 if walk > 0 else 2), pose="walk" if t > L else "fall")
        z = ease(min(1, t / (L + 0.3)))
        cam = lerp((40, GY + 28, 52 - 38), (40 - 4, GY + 12, 52 - 36), z); tgt = lerp((40, GY + 12, 52), (ax - 2, GY + 3, 52), z)
        if L <= t < L + 0.3:
            cam, tgt = shake(cam, tgt, 0.5, t)
        img, depth = render(S, c, m, cam, tgt, 48, w, h)
        if t >= L:
            dust(img, depth, cam, tgt, 48, min(1, (t - L) / 0.8), 40, GY, 52)
        return finish(img)
    if k == 6:   # おまけ：中南米の森。落ちながら向きを変えて、おしりから木の幹へ滑空
        S, c, m = ground()
        tree(c, m, 30, 48)
        u = ease(min(1, t / (T * 0.75)))
        ax, ay, az = 66 - 22 * u, GY + 26 - 12 * u, 52
        yaw = 0.0 if t < 0.8 else math.pi * min(1, (t - 0.8) / 0.8)               # くるっと向きを変える（おしりが幹へ）
        ant(c, m, ax, ay, az, 2.2, yaw=yaw, phase=t * 3, pose="fall", pitch=-0.3)
        cam = lerp((74, GY + 17, 18), (62, GY + 15, 14), u); tgt = (ax - 6, ay - 1, az)
        img, depth = render(S, c, m, cam, tgt, 54, w, h)
        return finish(img, grade=(0.92, 1.08, 0.92))
    if k == 7:   # 最後：僕の顔から一気に引くと、まわりに次の候補（木・野球ボール・鉄のかたまり）
        S, c, m = ground()
        person(c, m, 40, GY, 52, "stand", look=int(round(math.sin(t * 1.5))))
        put(c, m, 26, 32, GY, GY + 5, 48, 54, (0.55, 0.56, 0.6), 1, 0.08)          # 鉄のかたまり
        put(c, m, 51, 53, GY, GY + 8, 50, 52, (0.42, 0.28, 0.16), 1, 0.05)          # 木
        put(c, m, 49, 55, GY + 8, GY + 13, 48, 54, (0.25, 0.55, 0.22), 1, 0.12)
        xs, ys, zs = np.meshgrid(np.arange(31, 37), np.arange(GY, GY + 6), np.arange(40, 46), indexing='ij')   # 野球ボール
        d_ = (xs + 0.5 - 34) ** 2 + (ys + 0.5 - GY - 2.6) ** 2 + (zs + 0.5 - 43) ** 2
        ins = d_ < 2.6 ** 2
        _set(c, m, xs[ins], ys[ins], zs[ins], (0.96, 0.95, 0.92), 0.02)
        put(c, m, 32, 33, GY + 1, GY + 5, 40, 41, (0.85, 0.15, 0.15), 1, 0.0); put(c, m, 35, 36, GY + 1, GY + 5, 40, 41, (0.85, 0.15, 0.15), 1, 0.0)
        z = snap(t, 0.4, 0.8)
        cam = lerp((40, GY + 22, 52 - 14), (40, GY + 18, 52 - 40), z); tgt = lerp((40, GY + 22.5, 52), (40, GY + 13, 52), z)
        img, depth = render(S, c, m, cam, tgt, 46 + 18 * z, w, h)
        return finish(img)


# ---------------------------------------------------------------- デザイン定義シート
def sheet(out="sheet_ant.png"):
    from kaguya2_voxel import studio, sheet_base, hexs, F
    im, d = sheet_base("アリ", "16本目からのレギュラー・黒いブロックのアリ")
    cx, cy, cz, r = 55, 10, 55, 5.0
    draw = lambda pose="walk", yaw=0.0, pitch=0.0, ph=0.6: (lambda c, m: ant(c, m, cx, cy, cz, r, yaw=yaw, phase=ph, pose=pose, pitch=pitch))
    tgt = (cx + 1, cy + 1, cz)
    views = [("横（基本）", (cx + 1, cy + 30, cz - 115)), ("斜め上", (cx + 70, cy + 70, cz - 70)), ("上から", (cx - 1, cy + 120, cz - 2)), ("正面", (cx + 120, cy + 6, cz))]
    for i_, (nm, cam) in enumerate(views):
        v = studio(draw(), cam, tgt, 26, 300, 330, (0.94, 0.95, 0.98))
        x = 50 + i_ * 317; im.paste(v, (x, 142))
        d.text((x + 150, 500), nm, font=F(30), fill=(40, 45, 60), anchor="mm")
    d.text((50, 560), "ポーズ", font=F(40), fill=(20, 20, 30))
    poses = [("歩く", draw("walk", -0.6, 0.0, 1.2), (cx + 50, cy + 40, cz - 60)),
             ("落ちる（脚を広げる）", draw("fall", 0.4, -0.3), (cx + 40, cy + 60, cz - 60)),
             ("滑空（おしりから）", draw("fall", math.pi, -0.3), (cx - 60, cy + 30, cz - 60)),
             ("着地して歩きだす", draw("walk", math.pi * 0.8, 0.0, 2.0), (cx - 40, cy + 45, cz - 70))]
    for i_, (nm, f, cam) in enumerate(poses):
        v = studio(f, cam, tgt, 27, 300, 300, (0.94, 0.95, 0.98))
        x = 50 + i_ * 317; im.paste(v, (x, 615))
        d.text((x + 150, 940), nm, font=F(28), fill=(40, 45, 60), anchor="mm")
    d.text((1350, 150), "色", font=F(40), fill=(20, 20, 30))
    cols = {"体": BODY, "脚・触角": LEG, "目": EYE}
    for i_, (nm, cc) in enumerate(cols.items()):
        y = 205 + i_ * 52
        d.rounded_rectangle([1350, y, 1393, y + 42], 6, fill=tuple(int(min(1, v) * 255) for v in cc), outline=(200, 200, 210))
        d.text((1410, y + 3), nm, font=F(28), fill=(30, 30, 40)); d.text((1640, y + 6), hexs(cc), font=F(26), fill=(90, 95, 110))
    d.text((1350, 445), "寸法（r＝大きさ）", font=F(40), fill=(20, 20, 30))
    for i_, s_ in enumerate(["全長 約5.5r（ふだん r=2.4で約13マス）", "おなか 2.6r×2r（段々の丸）", "むね 1.7r の箱／前が少し高い", "頭 1.4r の角の丸い箱・前にあご",
                             "触角 くの字×2（長い）／脚 6本・ひざが高い", "足の先は体の中心から1.45r下"]):
        d.text((1350, 500 + i_ * 40), s_, font=F(26), fill=(60, 65, 80))
    d.text((1350, 760), "撮り方", font=F(40), fill=(20, 20, 30))
    for i_, s_ in enumerate(["画面の幅の4〜7割に収める", "脚が見えるよう斜め上か真横から", "黒いので明るい背景（空・草）の前で", "寄りすぎると塊に見える"]):
        d.text((1350, 815 + i_ * 40), s_, font=F(26), fill=(60, 65, 80))
    d.text((50, 1010), "目印：黒い体／ひざの高い長い6本脚／長いくの字の触角／前にあご／段々の大きなおなか。", font=F(36), fill=(200, 50, 50))
    d.text((50, 1065), "道具：ant_voxel.py の ant(c, m, x, y, z, r, yaw, phase, pose, pitch)。pose は walk（脚が下）／fall（脚を横に広げる）。", font=F(28), fill=(90, 95, 110))
    im.save(out)


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
    if sys.argv[1] == 'sheet':
        sheet()
    elif sys.argv[1] == 'stills':
        spec = sys.argv[2]
        ims = []
        for s_ in spec.split(','):
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
        sheet.save(sys.argv[3] if len(sys.argv) > 3 else 'ant_stills.png')
    else:
        os.makedirs('clips', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips/{k + 1:02d}.mp4')
