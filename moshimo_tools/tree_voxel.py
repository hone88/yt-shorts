"""17本目「もしもスカイツリーから木を落としたら？」（台本 20261119）。マイクラ調。
アリの回（ant_voxel.py）と同じ部品を使い、全場面でカメラを動かし続ける。
使い方: python3 tree_voxel.py stills k:t,... [out.png] / python3 tree_voxel.py 0,1,2"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import render, particles, ease, C, f32
import suika_voxel as SV
from elevator_voxel import person, put, finish, shake
import car_voxel as CV
import car2_voxel as C2
from ant_voxel import _set, dust

W, H, FPS, RS = 1080, 1920, 30, 3
_est = [3.7, 5.3, 3.6, 4.6, 5.9, 3.6, 3.3, 4.7]
CLIPS = [round(x * 1.27 * 1.15, 1) for x in _est]   # 声より少し長く作る（足りないと組み立てでゆっくり再生になり、コマが重なってカクつく）
GY = SV.GY
lerp, snap, ground = C2.lerp, C2.snap, C2.ground
BARK = (0.42, 0.28, 0.16)
LEAF = (0.22, 0.55, 0.2)
LEAF2 = (0.3, 0.66, 0.24)
ROOT = (0.36, 0.24, 0.14)
SOIL = (0.45, 0.33, 0.2)


def tree(c, m, cx, cy, cz, s=1.0, tilt=0.0, yaw=0.0, leaves=1.0):
    """根っこごと抜いた木。cy は重心（幹の下のほう）。tilt=0 で根が下、tilt=pi/2 で横倒し。
    leaves=1 で葉がいっぱい、0 に近いほど葉が散って小さくなる。"""
    ct, st = math.cos(tilt), math.sin(tilt)
    cyw, syw = math.cos(yaw), math.sin(yaw)
    R = 18 * s
    xs, ys, zs = np.meshgrid(np.arange(int(cx - R), int(cx + R) + 1), np.arange(int(cy - R), int(cy + R) + 1),
                             np.arange(int(cz - R), int(cz + R) + 1), indexing='ij')
    dx, dy, dz = xs + 0.5 - cx, ys + 0.5 - cy, zs + 0.5 - cz
    lx = dx * cyw + dz * syw; lz = -dx * syw + dz * cyw; ly = dy           # yaw を戻す
    lx, ly = lx * ct + ly * st, -lx * st + ly * ct                        # tilt を戻す
    lx, ly, lz = lx / s, ly / s, lz / s
    rr = np.sqrt(lx ** 2 + lz ** 2)
    # 根っこ（土のかたまり＋根）：y -7〜-2
    soil = ((lx / 4.2) ** 2 + ((ly + 4.5) / 2.6) ** 2 + (lz / 4.2) ** 2) < 1
    root = (np.abs(ly + 5) < 3.2) & (rr < 6.5) & ((np.floor(lx + 7) + np.floor(lz + 7) + np.floor(ly + 9)) % 3 == 0) & ~soil
    trunk = (np.abs(lx) <= 1.3) & (np.abs(lz) <= 1.3) & (ly > -2.5) & (ly < 12)
    k = max(0.25, leaves)
    crown = ((lx / (7.5 * k)) ** 2 + ((ly - 13) / (5.5 * k)) ** 2 + (lz / (7.5 * k)) ** 2) < 1
    crown2 = ((lx / (5 * k)) ** 2 + ((ly - 17) / (3.5 * k)) ** 2 + (lz / (5 * k)) ** 2) < 1
    if leaves < 1:
        rnd = np.random.default_rng(int(leaves * 100)).random(crown.shape)
        crown &= rnd < (0.35 + 0.65 * leaves)
        crown2 &= rnd < (0.35 + 0.65 * leaves)
    branch = (leaves < 0.6) & (np.abs(ly - 11) < 0.8) & ((np.abs(lx) < 6) & (np.abs(lz) < 0.8) | (np.abs(lz) < 6) & (np.abs(lx) < 0.8))
    for msk, col, var in ((soil, SOIL, 0.12), (root, ROOT, 0.1), (trunk, BARK, 0.1), (branch, BARK, 0.08),
                          (crown & ~crown2, LEAF, 0.18), (crown2, LEAF2, 0.15)):
        _set(c, m, xs[msk], ys[msk], zs[msk], col, var)


def shuttle(c, m, cx, cy, cz, s=1.0):
    """バドミントンの羽根（コルクが下）"""
    xs, ys, zs = np.meshgrid(np.arange(int(cx - 6 * s), int(cx + 6 * s) + 1), np.arange(int(cy - 3 * s), int(cy + 10 * s) + 1),
                             np.arange(int(cz - 6 * s), int(cz + 6 * s) + 1), indexing='ij')
    dx, dy, dz = (xs + 0.5 - cx) / s, (ys + 0.5 - cy) / s, (zs + 0.5 - cz) / s
    rr = np.sqrt(dx ** 2 + dz ** 2)
    cork = (dx ** 2 + dy ** 2 + dz ** 2 < 6.5) & (dy < 1.5)
    feather = (dy >= 1.5) & (dy < 9) & (np.abs(rr - (1.8 + 0.42 * (dy - 1.5))) < 0.7)
    band = feather & (np.abs(dy - 3) < 0.6)
    _set(c, m, xs[cork], ys[cork], zs[cork], (0.95, 0.95, 0.92), 0.03)
    _set(c, m, xs[feather & ~band], ys[feather & ~band], zs[feather & ~band], (0.98, 0.98, 1.0), 0.02)
    _set(c, m, xs[band], ys[band], zs[band], (0.85, 0.2, 0.2), 0.02)


def leafburst(img, depth, cam, tgt, fov, t, cx, cy, cz, amt=1.0, up=1.0):
    rg = np.random.default_rng(11); n = int(260 * amt)
    a = rg.uniform(0, 2 * math.pi, n); r0 = rg.uniform(3, 9, n); sp = rg.uniform(4, 12, n)
    ph = (rg.uniform(0, 1, n) + t * 0.7) % 1
    p = np.stack([cx + np.cos(a) * (r0 + sp * ph), cy + up * (4 + 30 * ph) * rg.uniform(0.6, 1.2, n), cz + np.sin(a) * (r0 + sp * ph)], 1)
    col = np.where(rg.random((n, 1)) < 0.5, C(*LEAF) * 1.3, C(*LEAF2) * 1.3)
    particles(img, depth, cam, tgt, fov, p, col * (1 - 0.5 * ph[:, None]), 0.5)


def sky(t, drop, cam, tgt, fov, draws, deck_up=None, lines=0.0, fx=None):
    S = SV.get('sky', SV.build_sky)
    c = np.zeros((60, 60, 60, 3), f32); m = np.zeros((60, 60, 60), np.uint8)
    SV.tower(c, m, drop)
    if deck_up is not None and deck_up < 40:
        put(c, m, 12, 26, 22 + deck_up, 25 + deck_up, 14, 46, (0.85, 0.88, 0.95), 1, 0.02)
        put(c, m, 25, 26, 25 + deck_up, 27 + deck_up, 14, 46, (0.6, 0.65, 0.72), 1, 0.02)
    for d in draws:
        d(c, m)
    img, depth = render(S, c, m, cam, tgt, fov, W // RS, H // RS)
    if lines > 0:
        C2.speedlines(img, depth, cam, tgt, fov, t, sp=20 * lines, n=int(120 * lines))
    if fx:
        fx(img, depth, cam, tgt, fov)
    return finish(img)


def T(**kw):
    return lambda c, m: tree(c, m, **kw)


def frame(k, t):
    w, h = W // RS, H // RS
    Tn = CLIPS[k]
    if k == 0:   # 展望台のふちの木に寄る → 横に倒れて落ちる → 一気に引いて高さを見せる
        tip = 1.6
        f = max(0.0, t - tip)
        n = round(f * FPS)
        drop = round(12.5 * f * f) if f < 1.2 else 18 + (n - 36)     # 加速して、毎秒30マス（1コマ1マス）に
        tl = 0.0 if t < tip - 0.5 else min(math.pi / 2, (t - tip + 0.5) * 1.6)
        k2 = snap(t, tip, 1.8)
        d = 46 + 22 * k2; a = 0.9 + 0.5 * k2
        cam = (30 + d * math.sin(a), 38 + 6 * k2, 30 - d * math.cos(a)); tgt = (24 + 6 * k2, 34 - 2 * k2, 30)
        cy = 32
        cxx = 20 + 10 * snap(t, tip - 0.4, 0.9)          # ふちから外へ、なめらかに動く（瞬間移動しない）
        return sky(t, drop, cam, tgt, 46 + 12 * k2, [T(cx=cxx, cy=cy, cz=30, s=0.9, tilt=tl)], deck_up=0 if t < tip else int(min(60, drop)),
                   lines=min(1, f) * 0.4)
    if k == 1:   # 重さ：地面で車と木が並ぶ。カメラが回り込む
        S, c, m = ground()
        tree(c, m, 30, GY + 7, 56, s=0.9)
        CV.car_s(c, m, 54, GY + 3, 56, 5, rot=0.0)
        a = -0.5 + 0.9 * ease(t / Tn)
        cam = (42 + 62 * math.sin(a), GY + 26, 56 - 62 * math.cos(a)); tgt = (42, GY + 13, 56)
        img, depth = render(S, c, m, cam, tgt, 52, w, h)
        return finish(img)
    if k == 2:   # くるっと回る：横倒し → 根が下へ（少し行き過ぎてもどる）
        u = t / Tn
        tl = math.pi / 2 * (1 - ease(min(1, u * 1.3))) + 0.25 * math.sin(min(1, u * 1.3) * math.pi) * (1 - u)
        drop = 20 + round(t * FPS)
        a = 0.4 + 0.9 * u; d = 72
        cam = (30 + d * math.sin(a), 34, 30 - d * math.cos(a)); tgt = (30, 34, 30)
        return sky(t, drop, cam, tgt, 52, [T(cx=30, cy=30, cz=30, s=0.9, tilt=tl, yaw=0.4 * u)], lines=0.3)
    if k == 3:   # バドミントンの羽根：木と羽根を並べて、同じ姿勢で落ちる
        drop = 40 + round(t * FPS)
        a = 1.2 - 0.25 * ease(t / Tn); d = 80
        cam = (30 + d * math.sin(a), 32, 30 - d * math.cos(a)); tgt = (30, 32, 28)
        sw = 0.08 * math.sin(t * 3)
        return sky(t, drop, cam, tgt, 54, [T(cx=24, cy=28, cz=20, s=0.85, tilt=sw), lambda c, m: shuttle(c, m, 34, 24, 38, s=1.3)], lines=0.4)
    if k == 4:   # 葉っぱがブレーキ：真下から見上げる → 横へ回り込む。風の線
        drop = 60 + round(t * FPS)
        u = ease(t / Tn)
        cam = lerp((30.5, -26, 30), (30 + 70 * math.sin(1.1), 30, 30 - 70 * math.cos(1.1)), u); tgt = (30, 34, 30)
        return sky(t, drop, cam, tgt, 58 - 6 * u, [T(cx=30, cy=26, cz=30, s=0.9, tilt=0.05 * math.sin(t * 2))], lines=0.8)
    if k == 5:   # 葉っぱが飛び散る：葉が減っていく。葉の粒が上へ飛ぶ
        drop = 90 + round(t * FPS)
        u = t / Tn
        lv = 1 - 0.6 * u
        a = 0.6 + 0.6 * u; d = 74 - 10 * u
        cam = (30 + d * math.sin(a), 40, 30 - d * math.cos(a)); tgt = (30, 34, 30)
        fx = lambda img, dp, cam_, tgt_, fov: leafburst(img, dp, cam_, tgt_, fov, t, 30, 36, 30)
        return sky(t, drop, cam, tgt, 54, [T(cx=30, cy=26, cz=30, s=0.9, leaves=lv, tilt=0.06 * math.sin(t * 3))], lines=0.9, fx=fx)
    if k == 6:   # 着地：上から落ちてきて根っこからドスン（ゆれ・土ぼこり）
        S, c, m = ground()
        L = 1.0
        if t < L:
            cy = GY + 6 + 40 * (1 - t / L)
        else:
            cy = GY + 6 - min(1.5, (t - L) * 6)
        tilt = 0.0 if t < L + 0.3 else min(0.22, (t - L - 0.3) * 0.4)
        tree(c, m, 40, cy, 56, s=0.9, tilt=tilt, leaves=0.45)
        u = min(1, t / (L + 0.2))
        cam = lerp((40, GY + 54, 56 - 54), (40 - 30, GY + 18, 56 - 52), ease(u)); tgt = lerp((40, GY + 26, 56), (40, GY + 12, 56), ease(u))
        if L <= t < L + 0.5:
            cam, tgt = shake(cam, tgt, 1.0, t)
        img, depth = render(S, c, m, cam, tgt, 54, w, h)
        if t >= L:
            dust(img, depth, cam, tgt, 54, min(1, (t - L) / 1.0), 40, GY, 56)
            dust(img, depth, cam, tgt, 54, min(1, (t - L) / 1.4), 36, GY, 60)
        return finish(img)
    if k == 7:   # 最後：僕の顔から一気に引くと、まわりに次の候補（野球ボール・鉄のかたまり・？の箱）
        S, c, m = ground()
        person(c, m, 40, GY, 52, "stand", look=int(round(math.sin(t * 1.5))))
        put(c, m, 26, 32, GY, GY + 5, 48, 54, (0.55, 0.56, 0.6), 1, 0.08)          # 鉄のかたまり
        xs, ys, zs = np.meshgrid(np.arange(31, 37), np.arange(GY, GY + 6), np.arange(40, 46), indexing='ij')   # 野球ボール
        ins = (xs + 0.5 - 34) ** 2 + (ys + 0.5 - GY - 2.6) ** 2 + (zs + 0.5 - 43) ** 2 < 2.6 ** 2
        _set(c, m, xs[ins], ys[ins], zs[ins], (0.96, 0.95, 0.92), 0.02)
        put(c, m, 32, 33, GY + 1, GY + 5, 40, 41, (0.85, 0.15, 0.15), 1, 0.0); put(c, m, 35, 36, GY + 1, GY + 5, 40, 41, (0.85, 0.15, 0.15), 1, 0.0)
        put(c, m, 49, 55, GY, GY + 6, 48, 54, (0.95, 0.75, 0.2), 1, 0.05)          # ？の箱
        put(c, m, 51, 53, GY + 6, GY + 7, 50, 52, (0.95, 0.75, 0.2), 1, 0.05)
        for (x0, y0) in ((51, 4), (52, 4), (53, 3), (52, 2), (52, 0)):             # 「？」（箱の前面）
            put(c, m, x0, x0 + 1, GY + y0 + 1, GY + y0 + 2, 47, 48, (0.15, 0.12, 0.1), 1, 0.0)
        z = snap(t, 0.4, 0.8)
        cam = lerp((40, GY + 22, 52 - 14), (40, GY + 18, 52 - 40), z); tgt = lerp((40, GY + 22.5, 52), (40, GY + 13, 52), z)
        img, depth = render(S, c, m, cam, tgt, 46 + 18 * z, w, h)
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
        sheet.save(sys.argv[3] if len(sys.argv) > 3 else 'tree_stills.png')
    else:
        os.makedirs('clips', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips/{k + 1:02d}.mp4')
