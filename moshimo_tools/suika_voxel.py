"""もしもの続き「スカイツリーからすいかを落としたら」マイクラ調・カメラが動き続ける背景（文字なし）
主役は画面のまん中（上下43〜67%）に置く。
使い方: python3 suika_voxel.py stills  /  python3 suika_voxel.py 0,1,2"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import Scene, render, particles, smooth, ease, C, f32
import hole_voxel as HV
from elevator_voxel import person, put, draw_x, finish, shake

W, H, FPS, RS = 1080, 1920, 30, 3
CLIPS = [3.6, 4.4, 3.7, 5.7, 4.9, 3.2, 4.4, 4.9]
XFRAC = 0.42
R = np.random.default_rng(12)
GY = HV.GY
GREEN, DARK, RED = (0.25, 0.62, 0.2), (0.07, 0.28, 0.08), (0.95, 0.18, 0.2)


def melon(c, m, cx, cy, cz, r, rot=0.0):
    xs, ys, zs = np.meshgrid(np.arange(int(cx - r - 1), int(cx + r + 2)), np.arange(int(cy - r - 1), int(cy + r + 2)),
                             np.arange(int(cz - r - 1), int(cz + r + 2)), indexing='ij')
    dx, dy, dz = xs + 0.5 - cx, ys + 0.5 - cy, zs + 0.5 - cz
    inside = dx * dx + dy * dy * 1.08 + dz * dz < r * r
    ok = inside & (xs >= 0) & (ys >= 0) & (zs >= 0) & (xs < c.shape[0]) & (ys < c.shape[1]) & (zs < c.shape[2])
    lon = np.arctan2(dz, dx) + rot
    stripe = np.sin(lon * 7 + 0.6 * np.sin(dy * 0.8)) > 0.35
    X, Y, Z = xs[ok], ys[ok], zs[ok]
    col = np.where(stripe[ok][:, None], C(*DARK), C(*GREEN))
    c[X, Y, Z] = col * (0.92 + 0.16 * R.random((len(X), 1))).astype(f32); m[X, Y, Z] = 1
    put(c, m, cx - 0.5, cx + 0.5, cy + r - 0.3, cy + r + 1.2, cz - 0.5, cz + 0.5, (0.4, 0.3, 0.12), 1, 0.0)  # へた


def build_ground():
    S = HV.build_town()
    c, m = S.col, S.mat
    for y in range(0, GY):  # 穴をうめて、ふつうの町に
        band = HV.STRATA[(y // 4) % len(HV.STRATA)]
        put(c, m, HV.HX0 - 1, HV.HX1 + 1, y, y + 1, HV.HZ0 - 1, HV.HZ1 + 1, band, 1, 0.1)
    put(c, m, HV.HX0 - 1, HV.HX1 + 1, GY - 1, GY, HV.HZ0 - 1, HV.HZ1 + 1, (0.33, 0.62, 0.25), 1, 0.08)
    put(c, m, 0, 80, GY - 1, GY, 22, 30, (0.32, 0.32, 0.34), 1, 0.05)
    S.base_c, S.base_m = c.copy(), m.copy()
    return S


def build_sky():
    """スカイツリーのすぐ横の空。白い格子の塔の壁が、下から上へ流れて見える。"""
    S = Scene(60, 60, 60)
    S.sun = np.array([0.4, 0.8, -0.45]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.1, 1.0, 0.9); S.amb = C(0.6, 0.65, 0.78)
    S.hor = C(0.75, 0.86, 1.0); S.top = C(0.28, 0.52, 0.95); S.fog0, S.fogk = 80, 300
    return S


def tower(c, m, off):
    """塔の壁（x=6〜12）。off ぶん格子を上にずらす。"""
    for y in range(60):
        yy = int(y + off)
        lattice = (yy % 6 == 0)
        for z in range(0, 60):
            diag = ((yy + z) % 6 == 0) or ((yy - z) % 6 == 0)
            col = (0.95, 0.97, 1.0) if (lattice or diag) else (0.7, 0.78, 0.9)
            c[10:12, y, z] = C(*col); m[10:12, y, z] = 1
    c[6:10, :, :] = C(0.62, 0.7, 0.82); m[6:10, :, :] = 1


_S = {}


def get(k, fn):
    if k not in _S:
        _S[k] = fn()
    return _S[k]


def coin(c, m, x, y, z):
    put(c, m, x - 1, x + 1, y, y + 1, z - 1, z + 1, (0.85, 0.87, 0.92), 1, 0.0)


def eraser(c, m, x, y, z):
    put(c, m, x - 2, x + 2, y, y + 2, z - 1, z + 1, (0.95, 0.95, 0.95), 1, 0.0)
    put(c, m, x - 2, x, y, y + 2, z - 1.2, z + 1.2, (0.2, 0.35, 0.8), 1, 0.0)


def car(c, m, x, y, z):
    put(c, m, x - 7, x + 7, y + 1, y + 5, z - 4, z + 4, (0.85, 0.15, 0.15), 1, 0.03)
    put(c, m, x - 4, x + 4, y + 5, y + 8, z - 3.5, z + 3.5, (0.75, 0.82, 0.92), 3, 0.0)
    for wx in (-4.5, 3.5):
        for wz in (-4.5, 3.5):
            put(c, m, x + wx, x + wx + 2, y, y + 2.5, z + wz, z + wz + 1, (0.08, 0.08, 0.08), 1, 0.0)


def burst(img, depth, cam, tgt, fov, t, cx, cy, cz):
    rg = np.random.default_rng(4); n = 420
    v = rg.normal(0, 1, (n, 3)); v[:, 1] = np.abs(v[:, 1]) * 1.2 + 0.3
    sp = rg.uniform(8, 26, n)[:, None]
    p = np.array([cx, cy, cz]) + v * sp * t + np.array([0, -18, 0]) * t * t
    p[:, 1] = np.maximum(p[:, 1], GY + 0.2)
    red = rg.random(n) < 0.7
    col = np.where(red[:, None], C(1.3, 0.22, 0.25), C(0.25, 0.65, 0.2))
    seeds = rg.random(n) < 0.12
    col[seeds] = C(0.05, 0.05, 0.05)
    particles(img, depth, cam, tgt, fov, p, col, 0.55)


def frame(k, t):
    w, h = W // RS, H // RS
    T = CLIPS[k]; p = ease(t / T)
    if k in (0, 3):   # 空：すいかと一緒に落ちる
        S = get('sky', build_sky)
        c = np.zeros((60, 60, 60, 3), f32); m = np.zeros((60, 60, 60), np.uint8)
        drop = 0 if (k == 0 and t < 0.35) else (t - (0.35 if k == 0 else -2)) ** 2 * (14 if k == 0 else 9)
        tower(c, m, drop)
        if k == 0:
            dy = int(min(60, drop))
            put(c, m, 12, 30, 22 + dy, 25 + dy, 18, 42, (0.85, 0.88, 0.95), 1, 0.02)  # 展望台のふち
        melon(c, m, 30, 30, 30, 7, rot=0.0 if (k == 0 and t < 0.35) else t * (3 if k == 0 else 6))
        if k == 0:
            a = 0.3 + 0.9 * p
            cam = (30 + 30 * math.sin(a), 36 + 4 * math.cos(t), 30 - 30 * math.cos(a)); tgt = (30, 30, 30)
            fov = 70 - 18 * p
        else:
            a = 1.2 + 0.5 * t
            cam = (30 + 17 * math.sin(a), 34, 30 - 17 * math.cos(a)); tgt = (30, 30, 30)
            fov = 58
            cam, tgt = shake(cam, tgt, 0.35, t)
        img, depth = render(S, c, m, cam, tgt, fov, w, h)
        if drop > 0:
            rg = np.random.default_rng(5); n = 200
            sp = np.stack([rg.uniform(14, 50, n), (rg.uniform(0, 60, n) + 70 * t) % 60, rg.uniform(5, 55, n)], 1)
            for kk in range(5):
                particles(img, depth, cam, tgt, fov, sp - np.array([0, kk * 0.9, 0]), np.tile(C(1, 1, 1) * (1 - kk / 5), (n, 1)), 0.12)
        return finish(img)

    S = get('ground', build_ground)
    c, m = S.base_c.copy(), S.base_m.copy()
    S.lights = []
    if k == 1:   # 見上げる人と、上から迫るすいか → ×
        person(c, m, 40, GY, 52, "stand", look=0)
        k2 = smooth(0, T, t)
        melon(c, m, 40, GY + 25 - 3 * k2, 34 + 5 * k2, 4.5, rot=t * 5)  # 高さに限りがあるので、手前上に置いて頭上に見せる
        cam = (40 + 8 * math.sin(t * 0.6), GY + 6, 22 - 3 * p); tgt = (40, GY + 31, 52)
        img, depth = render(S, c, m, cam, tgt, 64, w, h)
        out = finish(img)
        if t >= T * XFRAC:
            out = draw_x(out, min(1.0, (t - T * XFRAC) / 0.15))
        return out
    if k == 2:   # 1円玉・消しゴム・すいかを並べて、カメラが横に流れる
        coin(c, m, 30, GY, 50); eraser(c, m, 38, GY, 50); melon(c, m, 52, GY + 6, 50, 6)
        x = 26 + 26 * p
        cam = (x, GY + 6 + 3 * p, 38 - 4 * p); tgt = (x + 2, GY + 2, 50)
        img, depth = render(S, c, m, cam, tgt, 56, w, h)
        return finish(img)
    if k == 4:   # 車が壁にぶつかる勢い
        put(c, m, 10, 70, GY, GY + 10, 60, 62, (0.75, 0.72, 0.68), 1, 0.06)
        hitT = T * 0.45
        z = 30 + min(1.0, t / hitT) * 21.5
        car(c, m, 40, GY, z)
        cam = (40 + 26 - 8 * p, GY + 12, z - 8); tgt = (40, GY + 1.5, z + 3)
        if hitT < t < hitT + 0.6:
            cam, tgt = shake(cam, tgt, 0.6 * (1 - (t - hitT) / 0.6), t)
        img, depth = render(S, c, m, cam, tgt, 62, w, h)
        if t > hitT:
            f = t - hitT
            rg = np.random.default_rng(9); n = 120
            v = rg.normal(0, 1, (n, 3)); v[:, 2] = -np.abs(v[:, 2]); v[:, 1] = np.abs(v[:, 1])
            pp = np.array([40, GY + 4, 59.5]) + v * 10 * f + np.array([0, -15, 0]) * f * f
            ok = pp[:, 1] > GY
            particles(img, depth, cam, tgt, 62, pp[ok], np.tile(C(0.8, 0.78, 0.75), (ok.sum(), 1)), 0.3)
        return finish(img)
    if k == 5:   # 着地で粉々
        land = 0.5
        if t < land:
            melon(c, m, 40, GY + 6 + 70 * (land - t), 50, 6, rot=t * 8)
        else:
            rg = np.random.default_rng(2)
            for _ in range(40):
                x = 40 + rg.normal(0, 6); z = 50 + rg.normal(0, 6)
                put(c, m, x, x + 1.5, GY - 1, GY, z, z + 1.5, (0.85, 0.15, 0.2), 1, 0.1)
        cam = (40 + 18, GY + 7 + 3 * p, 50 - 18); tgt = (40, GY + 6, 50)
        if land < t < land + 0.5:
            cam, tgt = shake(cam, tgt, 0.8 * (1 - (t - land) / 0.5), t)
        img, depth = render(S, c, m, cam, tgt, 60, w, h)
        if t >= land:
            burst(img, depth, cam, tgt, 60, t - land, 40, GY + 3, 50)
        return finish(img)
    if k == 6:   # 注意：首をふる人（赤っぽく）
        person(c, m, 40, GY, 52, "stand", look=int(round(math.sin(t * 7) * 1.4)))
        cam = (40 + 4 * math.sin(t * 0.8), GY + 20, 52 - 20 + 4 * p); tgt = (40, GY + 20, 52)
        img, depth = render(S, c, m, cam, tgt, 56, w, h)
        return finish(img, grade=(1.15, 0.85, 0.82))
    if k == 7:   # すいかを持った人の顔にゆっくり寄る
        person(c, m, 40, GY, 52, "stand", look=int(round(math.sin(t * 1.2))))
        melon(c, m, 46, GY + 19, 49, 3.5, rot=0.3)
        cam = (42, GY + 19, 52 - 26 + 9 * p); tgt = (42, GY + 18, 52)
        img, depth = render(S, c, m, cam, tgt, 54, w, h)
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
        spec = sys.argv[2] if len(sys.argv) > 2 else '0:0.1,0:2.5,1:0.5,1:3.0,2:1.8,3:2.0,4:3.0,5:0.9,6:2.0,7:3.0'
        ims = []
        from PIL import ImageDraw
        for s_ in spec.split(','):
            k, t = s_.split(':')
            im = Image.fromarray((frame(int(k), float(t)) * 255).astype(np.uint8)).resize((216, 384)).convert('RGBA')
            d = ImageDraw.Draw(im, 'RGBA')
            d.rectangle([0, int(384 * .36), 216, int(384 * .43)], fill=(255, 0, 0, 70)); d.rectangle([0, int(384 * .68), 216, 384], fill=(0, 0, 255, 50))
            ims.append(im.convert('RGB'))
        sheet = Image.new('RGB', (216 * 5, 384 * ((len(ims) + 4) // 5)))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % 5) * 216, (i // 5) * 384))
        sheet.save('suika_stills.png')
    else:
        os.makedirs('clips', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips/{k + 1:02d}.mp4')
