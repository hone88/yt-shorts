"""もしもの続き「スカイツリーから車を落としたら」マイクラ調・カメラが動き続ける背景（文字なし）
すいかの回（suika_voxel）の仕組みを使い、落とす物を車にして、着地をもっと大きくする。
使い方: python3 car_voxel.py stills  /  python3 car_voxel.py 0,1,2"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import render, particles, smooth, ease, C, f32
import suika_voxel as SV
from elevator_voxel import person, put, draw_x, finish, shake

W, H, FPS, RS = 1080, 1920, 30, 3
CLIPS = [3.3, 3.6, 3.4, 6.6, 3.8, 4.9, 4.4, 4.8]
GY = SV.GY
LAND = 1.5
RED, GLASS, TIRE = (0.85, 0.15, 0.15), (0.75, 0.82, 0.92), (0.08, 0.08, 0.08)


def car_s(c, m, cx, cy, cz, r, rot=0.0, crushed=0.0):
    """中心(cx,cy,cz)、大きさ r（すいかの半径と同じ感覚）で車を描く。crushed=1 でぺしゃんこ。"""
    s = r / 7.0
    hb = 4 * s * (1 - 0.7 * crushed)
    hc = 3 * s * (1 - 0.85 * crushed)
    y0 = cy - (hb + hc) / 2
    flip = int(rot // math.pi) % 2  # 回りながら落ちる感じ：上下を入れ替える
    if flip and crushed == 0:
        put(c, m, cx - 4 * s, cx + 4 * s, y0, y0 + hc, cz - 3.5 * s, cz + 3.5 * s, GLASS, 3, 0.0)
        put(c, m, cx - 7 * s, cx + 7 * s, y0 + hc, y0 + hc + hb, cz - 4 * s, cz + 4 * s, RED, 1, 0.03)
        ty = y0 + hc + hb
        for wx in (-4.5, 3.5):
            for wz in (-4.5, 3.5):
                put(c, m, cx + wx * s, cx + (wx + 2) * s, ty, ty + 2 * s, cz + wz * s, cz + (wz + 1) * s, TIRE, 1, 0.0)
        return
    put(c, m, cx - 7 * s * (1 + 0.15 * crushed), cx + 7 * s * (1 + 0.15 * crushed), y0, y0 + hb, cz - 4 * s, cz + 4 * s, RED, 1, 0.05 + 0.1 * crushed)
    put(c, m, cx - 4 * s, cx + 4 * s, y0 + hb, y0 + hb + hc, cz - 3.5 * s, cz + 3.5 * s, GLASS, 3 if crushed < 0.5 else 1, 0.0)
    if crushed < 0.5:
        for wx in (-4.5, 3.5):
            for wz in (-4.5, 3.5):
                put(c, m, cx + wx * s, cx + (wx + 2) * s, y0 - 1.5 * s, y0 + 1 * s, cz + wz * s, cz + (wz + 1) * s, TIRE, 1, 0.0)


# すいか → 車 に差しかえて、すいかの回の場面をそのまま使う
SV.melon = lambda c, m, cx, cy, cz, r, rot=0.0: car_s(c, m, cx, cy, cz, r, rot)


def crater(t, cam_mode):
    S = SV.get('ground', SV.build_ground); S.lights = []
    c, m = S.base_c.copy(), S.base_m.copy()
    w, h = W // RS, H // RS
    cx, cz = 40, 50
    if cam_mode == 'impact' and t < LAND:
        q = t / LAND
        car_s(c, m, cx, 66 - 20 * q ** 4, cz, 0.9 + 6.0 * q ** 4, rot=t * 6)
        cam = (cx + 3, GY + 1.5, cz - 9); tgt = (cx, 66, cz + 0.5)
        fov = 40 + 30 * q ** 4
        cam, tgt = shake(cam, tgt, 0.2 * q, t)
        img, depth = render(S, c, m, cam, tgt, fov, w, h)
        rg = np.random.default_rng(6); n = 60
        sp = np.stack([cx + rg.normal(0, 3, n), (66 - (t * 40 + rg.uniform(0, 30, n)) % 30), cz + rg.normal(0, 3, n)], 1)
        particles(img, depth, cam, tgt, fov, sp, np.tile(C(1, 1, 1), (n, 1)), 0.08)
        return finish(img)
    f = (t - LAND) if cam_mode == 'impact' else (3.0 + t)
    grow = min(1.0, f / 0.12)
    xs, zs = np.meshgrid(np.arange(cx - 22, cx + 23), np.arange(cz - 22, cz + 23), indexing='ij')
    rr = np.hypot(xs + 0.5 - cx, zs + 0.5 - cz)
    dep = np.clip(9.0 * (1 - (rr / 15.0) ** 2), 0, None) * grow
    for x, z, d_, r_ in zip(xs.ravel(), zs.ravel(), dep.ravel(), rr.ravel()):
        if not (0 <= x < c.shape[0] and 0 <= z < c.shape[2]):
            continue
        if d_ > 0.5:
            top = GY - int(round(d_))
            m[x, top:GY, z] = 0
            c[x, top - 1, z] = C(0.45, 0.3, 0.18) if (hash((x, z)) % 5) else C(0.25, 0.22, 0.2)
        elif 14.5 <= r_ < 18 and grow >= 1:
            put(c, m, x, x + 1, GY, GY + 1 + (hash((x, z)) % 3), z, z + 1, (0.42, 0.3, 0.18), 1, 0.1)
        elif 18 <= r_ < 22 and grow >= 1 and hash((x, z, 7)) % 4 == 0:
            put(c, m, x, x + 1, GY, GY + 1, z, z + 1, (0.5, 0.36, 0.22), 1, 0.1)
    if grow >= 1:  # ぺしゃんこの車が、穴の底にめり込んでいる
        car_s(c, m, cx, GY - 8.0, cz, 6.5, crushed=1.0)
    if cam_mode == 'impact':
        a = 0.6 + 0.5 * min(1.0, f / 2.0)
        cam = (cx + 34 * math.sin(a), GY + 20 + 6 * min(1.0, f / 2.0), cz - 34 * math.cos(a)); tgt = (cx, GY - 6, cz)
        if f < 1.0:
            cam, tgt = shake(cam, tgt, 2.2 * (1 - f), t)
    else:  # 真上からぐんぐん引いて、穴の大きさを見せる
        k = smooth(0, CLIPS[5], t)
        cam = (cx + 0.01, GY + 22 + 30 * k, cz - 14 - 10 * k); tgt = (cx, GY - 4, cz)
    fov = 64
    img, depth = render(S, c, m, cam, tgt, fov, w, h)
    if cam_mode == 'impact':
        if f < 0.15:
            img = img * (1 - 0.8 * (1 - f / 0.15)) + 1.7 * 0.8 * (1 - f / 0.15)
        rg = np.random.default_rng(4); n = 900
        v = rg.normal(0, 1, (n, 3)); v[:, 1] = np.abs(v[:, 1]) * 1.8 + 0.6
        sp = rg.uniform(14, 44, n)[:, None]
        pp = np.array([cx, GY + 1, cz]) + v * sp * f + np.array([0, -20, 0]) * f * f
        pp[:, 1] = np.maximum(pp[:, 1], GY + 0.2)
        kind = rg.random(n)
        col = np.where((kind < 0.2)[:, None], C(1.1, 0.15, 0.15), np.where((kind < 0.35)[:, None], C(1.2, 1.25, 1.35), C(0.5, 0.36, 0.22)))
        particles(img, depth, cam, tgt, fov, pp, col, 0.7)
        ring = np.linspace(0, 2 * np.pi, 200)
        R_ = 6 + 50 * f
        if f < 1.2:
            rp = np.stack([cx + R_ * np.cos(ring), np.full_like(ring, GY + 0.6), cz + R_ * np.sin(ring)], 1)
            particles(img, depth, cam, tgt, fov, rp, np.tile(C(1.6, 1.6, 1.6) * (1 - f / 1.2), (len(ring), 1)), 1.1)
        if f < 1.8:
            nd = 90
            dv = rg.normal(0, 1, (nd, 3)); dv[:, 1] = np.abs(dv[:, 1]) * 0.7
            dp = np.array([cx, GY + 2, cz]) + dv * (7 + 12 * f)
            particles(img, depth, cam, tgt, fov, dp, np.tile(C(0.85, 0.78, 0.66), (nd, 1)), 1.6 * (1 - f / 1.8))
    return finish(img)


def pile(t):  # 車と、すいかの山（カメラが横に流れる）
    S = SV.get('ground', SV.build_ground); S.lights = []
    c, m = S.base_c.copy(), S.base_m.copy()
    w, h = W // RS, H // RS
    car_s(c, m, 31, GY + 4.5, 50, 6.0)
    for layer, (nx, nz) in enumerate(((4, 3), (3, 2), (2, 1))):  # すいかをピラミッドに積む
        for i in range(nx):
            for j in range(nz):
                x = 46 + (i - (nx - 1) / 2) * 5.0; z = 50 + (j - (nz - 1) / 2) * 5.0
                SV_melon_orig(c, m, x, GY + 2.3 + layer * 4.2, z, 2.4, rot=i + j)
    p = ease(t / CLIPS[2])
    cam = (39 - 6 + 12 * p, GY + 12, 22 + 3 * p); tgt = (39, GY + 4, 50)
    img, depth = render(S, c, m, cam, tgt, 64, w, h)
    return finish(img)


import importlib
_sv2 = importlib.reload(importlib.import_module('suika_voxel'))
SV_melon_orig = _sv2.melon
SCALE = [1.0]
SV.melon = lambda c, m, cx, cy, cz, r, rot=0.0: car_s(c, m, cx, cy, cz, r * SCALE[0], rot)

MAP = {0: 0, 1: 1, 3: 3, 6: 6, 7: 7}


def frame(k, t):
    if k in MAP:
        SCALE[0] = {3: 0.6, 7: 0.75}.get(k, 1.0)
        SV.CLIPS = list(SV.CLIPS)
        SV.CLIPS[MAP[k]] = CLIPS[k]
        if k == 1:
            SV.XFRAC = 0.45
        return SV.frame(MAP[k], t)
    if k == 2:
        return pile(t)
    if k == 4:
        return crater(t, 'impact')
    if k == 5:
        return crater(t, 'aerial')


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
        spec = sys.argv[2] if len(sys.argv) > 2 else '0:0.2,0:2.5,1:2.5,2:1.5,3:3.0,4:1.2,4:1.6,4:2.6,5:2.5,7:3.0'
        ims = []
        for s_ in spec.split(','):
            k, t = s_.split(':')
            im = Image.fromarray((frame(int(k), float(t)) * 255).astype(np.uint8)).resize((216, 384))
            d = ImageDraw.Draw(im)
            for y in (int(384 * .36), int(384 * .43), int(384 * .68)):
                d.line([(0, y), (216, y)], fill=(255, 0, 0), width=1)
            ims.append(im)
        sheet = Image.new('RGB', (216 * 5, 384 * ((len(ims) + 4) // 5)))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % 5) * 216, (i // 5) * 384))
        sheet.save('car_stills.png')
    else:
        os.makedirs('clips', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips/{k + 1:02d}.mp4')
