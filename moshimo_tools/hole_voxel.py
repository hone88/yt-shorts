"""もしもの続き 10本目「地球の反対側まで穴を掘って飛び込んだら」マイクラ調・動きの大きい背景（文字なし）
使い方: python3 hole_voxel.py stills  /  python3 hole_voxel.py 0,1,2"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import Scene, render, particles, tone, blur, vnoise, smooth, ease, C, f32
import taiyou_voxel as TV
from elevator_voxel import person, put, draw_x, finish, shake

W, H, FPS, RS = 1080, 1920, 30, 3
CLIPS = [4.3, 4.5, 4.2, 6.2, 4.3, 4.3, 5.0, 5.5]
XFRAC = 0.44
R = np.random.default_rng(10)
GY = 40                    # 地面の高さ
HX0, HX1, HZ0, HZ1 = 24, 56, 34, 66   # 穴（キャラが寝て入る広さ）
HCX, HCZ = 40, 50
STRATA = [(0.36, 0.25, 0.16), (0.5, 0.36, 0.22), (0.45, 0.45, 0.48), (0.62, 0.5, 0.36), (0.38, 0.38, 0.42), (0.55, 0.3, 0.2)]


def build_town():
    S = Scene(80, 70, 100)
    c, m = S.col, S.mat
    for y in range(0, GY):  # 地層
        band = STRATA[(y // 4) % len(STRATA)]
        put(c, m, 0, 80, y, y + 1, 0, 100, band, 1, 0.1)
    put(c, m, 0, 80, GY - 1, GY, 0, 100, (0.33, 0.62, 0.25), 1, 0.08)  # 草
    put(c, m, 0, 80, GY - 1, GY, 22, 30, (0.32, 0.32, 0.34), 1, 0.05)  # 道
    for z in range(22, 30):
        pass
    c[38:42, GY - 1, 26] = C(0.9, 0.9, 0.85)
    # 家と木
    for (x0, z0, w, d, h, col) in [(6, 60, 12, 12, 9, (0.9, 0.85, 0.75)), (60, 62, 12, 10, 11, (0.8, 0.55, 0.42)), (8, 36, 10, 8, 8, (0.85, 0.88, 0.92)), (62, 36, 11, 9, 9, (0.9, 0.82, 0.6)), (24, 80, 12, 10, 10, (0.75, 0.78, 0.85)), (50, 82, 14, 10, 12, (0.88, 0.75, 0.6))]:
        put(c, m, x0, x0 + w, GY, GY + h, z0, z0 + d, col, 1, 0.04)
        for k in range(4):
            put(c, m, x0 - 1 + k, x0 + w + 1 - k, GY + h + k, GY + h + k + 1, z0 - 1, z0 + d + 1, (0.55, 0.22, 0.16), 1, 0.05)
    for (x, z) in [(14, 26), (66, 28), (12, 74), (68, 76), (40, 84)]:
        put(c, m, x, x + 2, GY, GY + 5, z, z + 2, (0.42, 0.28, 0.16), 1, 0.05)
        put(c, m, x - 2, x + 4, GY + 5, GY + 9, z - 2, z + 4, (0.25, 0.55, 0.22), 1, 0.12)
    # 穴（縁は黄色と黒のしま）
    m[HX0:HX1, 1:GY, HZ0:HZ1] = 0
    c[HX0:HX1, 0, HZ0:HZ1] = C(0.05, 0.03, 0.02)  # 底は真っ暗（どこまでも続く穴）
    for x in range(HX0 - 1, HX1 + 1):
        for z in (HZ0 - 1, HZ1):
            c[x, GY - 1, z] = C(1.0, 0.8, 0.1) if (x // 2) % 2 == 0 else C(0.1, 0.1, 0.1)
    for z in range(HZ0 - 1, HZ1 + 1):
        for x in (HX0 - 1, HX1):
            c[x, GY - 1, z] = C(1.0, 0.8, 0.1) if (z // 2) % 2 == 0 else C(0.1, 0.1, 0.1)
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = np.array([0.35, 0.85, -0.4]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.1, 1.0, 0.9); S.amb = C(0.55, 0.6, 0.72)
    S.hor = C(0.75, 0.85, 1.0); S.top = C(0.3, 0.55, 0.95); S.fog0, S.fogk = 60, 200
    return S


def build_cut():
    """地球を半分に切った断面（手前 z<32 を切り取り）。"""
    S = Scene(64, 64, 64)
    xs, ys, zs = np.meshgrid(np.arange(64), np.arange(64), np.arange(64), indexing='ij')
    d = np.sqrt((xs + 0.5 - 32) ** 2 + (ys + 0.5 - 32) ** 2 + (zs + 0.5 - 32) ** 2)
    ball = (d < 28) & (zs >= 32)
    col = np.zeros((64, 64, 64, 3), f32)
    col[:] = C(0.75, 0.32, 0.15)                       # マントル
    col[d < 22] = C(0.9, 0.45, 0.15)
    col[d < 14] = C(1.6, 0.8, 0.25)                    # 外核
    col[d < 7] = C(2.0, 1.7, 0.9)                      # 内核
    crust = d >= 26
    lat = np.arcsin(np.clip((ys + 0.5 - 32) / np.maximum(d, 1e-3), -1, 1)); lon = np.arctan2(zs + 0.5 - 32, xs + 0.5 - 32)
    land = vnoise(64, 64, 8, 3, seed=8)[((lat / np.pi + 0.5) * 63).astype(int), ((lon / (2 * np.pi) + 0.5) * 63).astype(int)] > 0.52
    col[crust] = np.where(land[crust][:, None], C(0.2, 0.5, 0.22), C(0.1, 0.28, 0.65))
    S.col[ball] = col[ball] * (0.9 + 0.2 * R.random((ball.sum(), 1))).astype(f32)
    S.mat[ball] = np.where(d[ball] < 14, 4, 1)
    S.sun = None; S.amb = C(0.85, 0.85, 0.95)
    S.lights = [((32, 32, -40), (0.6, 0.6, 0.7), 80)]
    S.hor = C(0.0, 0.0, 0.02); S.top = C(0.0, 0.0, 0.0); S.fog0, S.fogk = 1000, 1e9
    S.sky = TV.star_sky(Scene.sky.__get__(S), 0.994, allsky=True)
    return S


def build_ocean():
    S = Scene(80, 50, 90)
    c, m = S.col, S.mat
    for y in range(0, 12):
        put(c, m, 0, 80, y, y + 1, 0, 90, (0.06, 0.25 + 0.02 * y, 0.6), 3 if y == 11 else 1, 0.06)
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = np.array([-0.3, 0.8, 0.5]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.1, 1.0, 0.9); S.amb = C(0.55, 0.62, 0.75)
    S.hor = C(0.8, 0.88, 1.0); S.top = C(0.25, 0.5, 0.95); S.fog0, S.fogk = 40, 150
    return S


_S = {}


def get(k, fn):
    if k not in _S:
        _S[k] = fn()
    return _S[k]


def shaft_colors(c, off):
    """穴の壁の地層を、off だけ上にずらす（落ちているように見せる）。"""
    for y in range(0, GY - 1):
        band = STRATA[int((y + off) // 4) % len(STRATA)]
        hot = min(1.0, max(0.0, off / 600.0))
        col = np.array(band, f32) * (1 - hot) + C(1.4, 0.55, 0.2) * hot
        if y == 0:
            c[HX0:HX1, 0, HZ0:HZ1] = C(0.05, 0.03, 0.02) * (1 - hot) + C(1.6, 0.6, 0.2) * hot
        c[HX0 - 1, y, HZ0:HZ1] = col; c[HX1, y, HZ0:HZ1] = col
        c[HX0:HX1, y, HZ0 - 1] = col; c[HX0:HX1, y, HZ1] = col


def path_points(t_dot):
    """断面の中を通る点線と、落ちていく人の位置（0→1→0 の往復）。"""
    ys = np.arange(4.5, 60, 1.6)
    line = np.stack([np.full_like(ys, 32.0), ys, np.full_like(ys, 31.6)], 1)
    yy = 32 + 27 * math.cos(math.pi * t_dot)
    return line, np.array([[32.0, yy, 31.4]])


def frame(k, t):
    w, h = W // RS, H // RS
    T = CLIPS[k]; p = ease(t / T)
    if k == 0:   # 明るい町 → 走って穴へジャンプ → カメラも一緒に落ちる
        S = get('town', build_town)
        c, m = S.base_c.copy(), S.base_m.copy()
        jump = 1.3
        if t < jump:
            z = 12 + 20 * (t / jump); y = GY
            person(c, m, HCX, y, int(z), "stand")
            cam, tgt = (HCX + 16 - 6 * t, GY + 14, z - 30), (HCX, GY + 23, z + 8)
        else:
            f = t - jump
            y = max(18.0, GY + 4 * f - 22 * f * f)
            if y <= 18.0:
                tf = f - math.sqrt((GY - 18 + 0.2) / 22)
                shaft_colors(c, 40 * tf + 30 * tf * tf)
            person(c, m, HCX, int(y), HCZ - 4, "lie")
            k2 = smooth(0, 1.2, f)
            cam = (HCX + 0.3, y + 34 - 12 * k2, HCZ - 9 + 2 * k2); tgt = (HCX, y, HCZ + 4)
        S.lights = []
        img, depth = render(S, c, m, cam, tgt, 68, w, h)
        return finish(img)
    if k == 1:   # 地球を貫く線。ブラジル？ → ×
        S = get('earth', TV.build_earth)
        S.sky = TV.star_sky(Scene.sky.__get__(S), 0.994, allsky=True)
        a = 0.9 + 0.35 * t
        cam = (32 + 95 * math.sin(a), 32 + 25 - 10 * p, 32 - 95 * math.cos(a)); tgt = (32, 32, 32)
        img, depth = render(S, S.col, S.mat, cam, tgt, 46 - 6 * p, w, h)
        del S.sky
        nrm = np.array([0.35, 0.75, -0.56]); nrm /= np.linalg.norm(nrm)
        s_ = np.linspace(-33, 33, 70)
        pts = np.array([32, 32, 32]) + s_[:, None] * nrm[None]
        prog = smooth(0.1, 1.2, t)
        show = (s_ <= -33 + 66 * prog)
        particles(img, np.full_like(depth, np.inf), cam, tgt, 46 - 6 * p, pts[show][::-1][:, :], np.tile(C(1.6, 1.4, 0.4), (show.sum(), 1)), 0.9)
        out = finish(img)
        if t >= T * XFRAC:
            out = draw_x(out, min(1.0, (t - T * XFRAC) / 0.15))
        return out
    if k == 2:   # 穴の中、顔に超アップ。地層がビュンビュン流れる
        S = get('town', build_town)
        c, m = S.base_c.copy(), S.base_m.copy()
        shaft_colors(c, 30 * t + 40 * t * t)
        person(c, m, HCX, 12, HCZ - 4, "lie")
        zoom = smooth(0, T, t)
        cam = (HCX + 1.5 * math.sin(t * 2) + 0.3, 38, HCZ - 6); tgt = (HCX, 18, HCZ + 4)
        cam, tgt = shake(cam, tgt, 0.25, t)
        S.lights = [((HCX, 34, HCZ), (1.1, 1.0, 0.9), 40)]
        sun, S.sun = S.sun, None
        img, depth = render(S, c, m, cam, tgt, 70 - 40 * zoom, w, h)
        S.sun = sun
        rg = np.random.default_rng(5); n = 140
        sp = np.stack([rg.uniform(HX0, HX1, n), (rg.uniform(0, 40, n) + 70 * t) % 40, rg.uniform(HZ0, HZ1, n)], 1)
        for kk in range(4):
            particles(img, depth, cam, tgt, 70 - 40 * zoom, sp - np.array([0, kk * 0.7, 0]), np.tile(C(1, 0.95, 0.8) * (1 - kk / 4), (n, 1)), 0.12)
        return finish(img)
    if k == 3:   # 地球の断面。点が中心へ一気に
        S = get('cut', build_cut)
        a = -0.6 + 0.9 * p
        cam = (32 + 80 * math.sin(a), 40 + 20 * math.cos(t), 32 - 80 * math.cos(a) - 5); tgt = (32, 32, 32)
        img, depth = render(S, S.col, S.mat, cam, tgt, 50 - 14 * p, w, h)
        line, dot = path_points(min(0.5, t / T * 0.6))
        particles(img, np.full_like(depth, np.inf), cam, tgt, 50 - 14 * p, line, np.tile(C(1.2, 1.2, 1.2), (len(line), 1)), 0.35)
        particles(img, np.full_like(depth, np.inf), cam, tgt, 50 - 14 * p, dot, C(2.5, 2.5, 2.5)[None], 2.0)
        return finish(img)
    if k == 4:   # 中心：真っ赤な熱の中でふわふわ
        S = get('town', build_town)
        c, m = S.base_c.copy(), S.base_m.copy()
        shaft_colors(c, 900)
        person(c, m, HCX, int(13 + 2 * math.sin(t * 1.6)), HCZ - 4, "lie")
        a = t * 0.9
        cam = (HCX + 8 * math.sin(a), 38, HCZ + 4 - 8 * math.cos(a) - 0.01); tgt = (HCX, 15, HCZ + 4)
        S.lights = [((HCX, 30, HCZ), (1.6, 0.8, 0.4), 40)]
        sun, S.sun = S.sun, None
        img, depth = render(S, c, m, cam, tgt, 52, w, h)
        S.sun = sun
        rg = np.random.default_rng(int(t * 10)); n = 180
        age = rg.uniform(0, 1, n)
        em = np.stack([rg.uniform(HX0, HX1, n), 14 + age * 22, rg.uniform(HZ0, HZ1, n)], 1)
        particles(img, depth, cam, tgt, 52, em, C(2.4, 1.0, 0.3) * (1 - age)[:, None], 0.18)
        return finish(img, grade=(1.08, 0.95, 0.88))
    if k == 5:   # 海からポン！
        S = get('ocean', build_ocean)
        c, m = S.base_c.copy(), S.base_m.copy()
        pop = 0.8
        up = 0 if t < pop else min(9.0, (t - pop) * 30 - 30 * (t - pop) ** 2 * 1.5)
        up = max(up, 0)
        bob = 0 if t < pop + 1.2 else 1.0 * math.sin((t - pop) * 3)
        person(c, m, 40, int(11 - 14 + up + 6 + bob) if t >= pop else -20, 45, "float" if t < pop + 1.0 else "stand")
        cam = (40 + 10 * math.sin(0.4 * t), 15 + 2 * p, 45 - 38 + 6 * p); tgt = (40, 27 + 2 * p, 45)
        img, depth = render(S, c, m, cam, tgt, 62, w, h)
        if t >= pop:
            f = t - pop
            rg = np.random.default_rng(3); n = 220
            ang = rg.uniform(0, 2 * np.pi, n); sp = rg.uniform(4, 12, n); vy = rg.uniform(8, 18, n)
            x = 40 + np.cos(ang) * sp * f; z = 45 + np.sin(ang) * sp * f; y = 12 + vy * f - 25 * f * f
            ok = y > 11
            particles(img, depth, cam, tgt, 62, np.stack([x, y, z], 1)[ok], np.tile(C(1.2, 1.3, 1.45), (ok.sum(), 1)), 0.35)
        return finish(img)
    if k == 6:   # 断面の中を、点が行ったり来たり
        S = get('cut', build_cut)
        a = 0.5 - 1.2 * p
        cam = (32 + 85 * math.sin(a), 32 + 30 * math.sin(t * 0.8), 32 - 85 * math.cos(a) - 5); tgt = (32, 32, 32)
        img, depth = render(S, S.col, S.mat, cam, tgt, 44, w, h)
        line, _ = path_points(0)
        particles(img, np.full_like(depth, np.inf), cam, tgt, 44, line, np.tile(C(1.2, 1.2, 1.2), (len(line), 1)), 0.35)
        for j in range(6):  # 残像つきで往復
            _, dot = path_points(t * 0.9 - j * 0.03)
            particles(img, np.full_like(depth, np.inf), cam, tgt, 44, dot, C(2.5, 2.5, 2.5)[None] * (1 - j / 6), 2.0 - j * 0.2)
        return finish(img)
    if k == 7:   # 穴のふちに立つ人。穴の底からカメラがせり上がって顔にアップ
        S = get('town', build_town)
        c, m = S.base_c.copy(), S.base_m.copy()
        person(c, m, HCX, GY, HZ1 + 4, "stand", look=int(round(math.sin(t * 1.3))))
        rise = smooth(0, T * 0.75, t)
        cam = (HCX + 0.01, 6 + (GY + 22 - 6) * rise, HCZ - 4 - 4 * rise); tgt = (HCX, GY + 8 + 13 * rise, HZ1 + 4)
        S.lights = [((HCX, GY - 8, HCZ), (0.9, 0.85, 0.75), 30)]
        img, depth = render(S, c, m, cam, tgt, 64, w, h)
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
        spec = sys.argv[2] if len(sys.argv) > 2 else '0:0.1,0:1.6,0:2.6,1:3.0,2:2.0,3:3.0,4:2.0,5:1.4,6:2.0,7:4.5'
        ims = []
        for s_ in spec.split(','):
            k, t = s_.split(':')
            ims.append(Image.fromarray((frame(int(k), float(t)) * 255).astype(np.uint8)).resize((216, 384)))
        sheet = Image.new('RGB', (216 * 5, 384 * ((len(ims) + 4) // 5)))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % 5) * 216, (i // 5) * 384))
        sheet.save('hole_stills.png')
    else:
        os.makedirs('clips', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips/{k + 1:02d}.mp4')
