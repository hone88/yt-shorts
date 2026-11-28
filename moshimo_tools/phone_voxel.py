"""29本目「もしも、スカイツリーから携帯を落としたら？」（台本 20261202・リクエスト「携帯」）。
すいかの回・野球ボールの回のセット（空・町）を使う。場面ごとに場所かカメラを変える（11/26のルール）。
最後の場面は1場面目の塔の上に戻る（ループ）。
使い方: python3 phone_voxel.py stills k:t,... out.png / python3 phone_voxel.py 0,1,2"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import render, particles, smooth, ease, C, f32
from suika_voxel import build_ground, build_sky, tower, get, GY
import elevator_voxel as _EVX
from elevator_voxel import person, put, finish, shake
import ball_voxel as BL
from ball_voxel import speed_label

W, H, FPS, RS = 1080, 1920, 30, 3
_EVX.RS = RS
_est = [3.6, 3.1, 4.1, 4.1, 2.8, 4.6, 5.6, 2.8, 6.0, 2.6]
CLIPS = [max(2.6, round(x * 1.27 * 1.15, 1)) for x in _est]
BL.CLIPS = CLIPS
SKIN = (0.95, 0.76, 0.6)


def phone(c, m, cx, cy, cz, s=1.0, flat=True, crack=False):
    """黒い本体＋青い画面。flat=True なら画面が下（y-）向きの水平、False なら縦向き"""
    hw, hl, th = max(1.0, 3.5 * s), max(1.5, 7.0 * s), max(0.5, 0.8 * s)
    if flat:
        x0, x1, y0, y1, z0, z1 = cx - hw, cx + hw, cy - th, cy + th, cz - hl, cz + hl
        put(c, m, int(x0), int(x1), int(y0), int(y1), int(z0), int(z1), (0.09, 0.09, 0.11), 1, 0.3)
        put(c, m, int(x0) + 1, int(x1) - 1, int(y0), int(y0) + 1, int(z0) + 1, int(z1) - 1, (0.25, 0.45, 0.85), 1, 0.5)
        put(c, m, int(x0) + 1, int(x1) - 1, int(y1) - 1, int(y1), int(z0) + 1, int(z1) - 1, (0.25, 0.45, 0.85), 1, 0.5)
        if crack:
            for i in range(int(z1 - z0) - 2):
                xx = int(cx + 1.5 * math.sin(i * 1.7))
                put(c, m, xx, xx + 1, int(y1) - 1, int(y1), int(z0) + 1 + i, int(z0) + 2 + i, (0.95, 0.97, 1.0), 1, 0.0)
    else:
        x0, x1, y0, y1, z0, z1 = cx - hw, cx + hw, cy - hl, cy + hl, cz - th, cz + th
        put(c, m, int(x0), int(x1), int(y0), int(y1), int(z0), int(z1), (0.09, 0.09, 0.11), 1, 0.3)
        put(c, m, int(x0) + 1, int(x1) - 1, int(y0) + 1, int(y1) - 1, int(z0), int(z0) + 1, (0.25, 0.45, 0.85), 1, 0.5)


def hand(c, m, x, y, z, s=1.0):
    put(c, m, int(x - 4 * s), int(x + 4 * s), int(y), int(y + 3 * s), int(z), int(z + 7 * s), SKIN, 1, 0.05)
    put(c, m, int(x - 4 * s), int(x + 4 * s), int(y - 1), int(y + 4 * s), int(z + 7 * s), int(z + 30 * s), (0.85, 0.86, 0.9), 1, 0.05)   # 白い袖


def plane(c, m, x, y, z):
    put(c, m, x - 3, x + 3, y - 3, y + 3, z - 20, z + 20, (0.95, 0.96, 0.98), 1, 0.1)
    put(c, m, x - 22, x + 22, y - 1, y + 1, z - 4, z + 6, (0.9, 0.91, 0.94), 1, 0.1)
    put(c, m, x - 1, x + 1, y + 3, y + 11, z + 14, z + 20, (0.2, 0.35, 0.65), 1, 0.1)
    for i in range(-16, 17, 4):
        put(c, m, x + 3, x + 4, y, y + 2, z + i, z + i + 2, (0.3, 0.4, 0.55), 1, 0.4)


def bush(c, m, x, z, rg):
    for _ in range(70):
        bx, by, bz = x + rg.integers(-9, 10), GY + rg.integers(0, 7), z + rg.integers(-7, 8)
        g = rg.uniform(0.75, 1.15)
        put(c, m, bx, bx + 2, by, by + 2, bz, bz + 2, (0.22 * g, 0.52 * g, 0.2 * g), 1, 0.05)


def sky_frame(k, t, T, p, w, h):
    S = get('sky', build_sky)
    c = np.zeros((60, 60, 60, 3), f32); m = np.zeros((60, 60, 60), np.uint8)
    lab = None
    if k in (0, 9):   # 塔の上：手が携帯を持って、はなす（9はループで同じ場面に戻る）
        rel = 1.4 if k == 0 else 99
        drop = 0 if t < rel else (t - rel) ** 2 * 10
        tower(c, m, drop)
        dy = int(min(60, drop))
        hand(c, m, 30, 33 + dy, 19, s=0.6)
        phone(c, m, 30, 31 - (0 if t < rel else (t - rel) ** 2 * 4), 26, flat=True)
        if k == 0:
            from kaguya2_voxel import cut
            ci, uu = cut(t, T, [0.5])
            if ci == 0:
                cam = (30 + 34 * math.sin(0.7 + 0.3 * uu), 40, 30 - 34 * math.cos(0.7 + 0.3 * uu)); tgt = (30, 31, 26); fov = 58
            else:
                cam = (40, 52, 44); tgt = (30, 24, 26); fov = 64
                lab = ("地上 約450m", smooth(0.1, 0.5, uu * T * 0.5))
        else:
            cam = (30 + 34 * math.sin(0.7 + 0.4 * p), 40, 30 - 34 * math.cos(0.7 + 0.4 * p)); tgt = (30, 31, 26); fov = 58 - 8 * p
    elif k == 1:      # 真上から見下ろす：携帯がはるか下へ小さくなる
        tower(c, m, 0)
        q = smooth(0, T, t)
        phone(c, m, 32, 50 - 40 * q, 30, s=1.0 - 0.6 * q, flat=True)
        cam = (34, 59, 33); tgt = (32, 0, 30); fov = 70
    elif k in (2, 3):  # 落ちていく携帯の横（2）と真下（3）。塔の格子が流れる
        tower(c, m, 40 * t)
        rot = 0.0 if k == 3 else 0.3 * math.sin(t * 2)
        phone(c, m, 30, 30, 30, s=1.1, flat=True)
        if k == 2:
            a = 1.0 + 0.35 * t
            cam = (30 + 24 * math.sin(a), 34, 30 - 24 * math.cos(a)); tgt = (30, 30, 30); fov = 56
            lab = ("2〜3秒で 一定の速さ", smooth(T * 0.35, T * 0.5, t))
        else:
            from kaguya2_voxel import cut
            ci, uu = cut(t, T, [0.45])
            cam = (31, 8, 31) if ci == 0 else (46, 22, 14); tgt = (30, 30, 30); fov = 60
            lab = ("時速 約50km", smooth(T * 0.3, T * 0.45, t))
    elif k == 6:      # 飛行機から落ちる（約5000m）
        plane(c, m, 30, 44, 34)
        q = smooth(0.6, T, t)
        phone(c, m, 34, 40 - 34 * q, 30 - 6 * q, s=0.5, flat=(int(t * 3) % 2 == 0))
        cam = (30 + 55 * math.sin(0.5 + 0.2 * p), 26 - 4 * p, 34 - 55 * math.cos(0.5 + 0.2 * p)); tgt = (30, 34 - 10 * q, 32); fov = 70
        lab = ("約5000m", smooth(T * 0.15, T * 0.3, t))
    img, depth = render(S, c, m, cam, tgt, fov, w, h)
    falling = (k in (2, 3)) or (k == 0 and t > 1.4) or k == 1
    if falling:
        rg = np.random.default_rng(5); n = 200
        sp = np.stack([rg.uniform(14, 50, n), (rg.uniform(0, 60, n) + 55 * t) % 60, rg.uniform(5, 55, n)], 1)
        for kk in range(5):
            particles(img, depth, cam, tgt, fov, sp - np.array([0, kk * 0.9, 0]), np.tile(C(1, 1, 1) * (1 - kk / 5), (n, 1)), 0.12)
    out = finish(img)
    if lab:
        out = speed_label(out, lab[0], lab[1])
    return out


def frame(k, t):
    w, h = W // RS, H // RS
    T = CLIPS[k]; p = ease(t / T)
    if k in (0, 1, 2, 3, 6, 9):
        return sky_frame(k, t, T, p, w, h)
    S = get('ground', build_ground)
    c, m = S.base_c.copy(), S.base_m.copy()
    S.lights = []
    from kaguya2_voxel import cut
    if k == 4:   # 手から落とす：道路の上。立った人の手から携帯が落ちる → 道路すれすれ
        person(c, m, 40, GY, 30, "stand", look=0)
        q = min(1.0, max(0.0, (t - 0.7) / 0.55)) ** 2
        phone(c, m, 44, GY + 14 - 13 * q, 27, s=0.25, flat=True)
        ci, uu = cut(t, T, [0.55])
        if ci == 0:
            cam = (58, GY + 16, 8 + 3 * uu); tgt = (42, GY + 11, 30); fov = 56
        else:
            cam = (54, GY + 5, 14); tgt = (44, GY + 2, 27); fov = 52
        img, depth = render(S, c, m, cam, tgt, fov, w, h)
        return speed_label(finish(img), "時速 約20km", smooth(T * 0.3, T * 0.45, t))
    if k == 5:   # くらべる：人のまわりを回る
        person(c, m, 40, GY, 52, "stand", look=int(round(math.sin(t * 1.5))))
        phone(c, m, 45, GY + 13, 49, s=0.22, flat=False)
        a = -0.6 + 1.2 * p
        cam = (40 + 26 * math.sin(a), GY + 22, 52 - 26 * math.cos(a)); tgt = (40, GY + 16, 52)
        img, depth = render(S, c, m, cam, tgt, 56, w, h)
        return speed_label(finish(img), "手 20km ／ 塔 50km", smooth(T * 0.2, T * 0.35, t))
    if k == 7:   # 草むら：遠くから → 草の中の携帯に寄る
        rg = np.random.default_rng(3)
        bush(c, m, 40, 60, rg)
        phone(c, m, 40, GY + 4, 58, s=0.25, flat=True)
        ci, uu = cut(t, T, [0.45])
        if ci == 0:
            cam = (40 + 20 * math.sin(0.4), GY + 30, 60 - 34); tgt = (40, GY + 2, 60); fov = 58
        else:
            cam = (46, GY + 12, 52 + 2 * uu); tgt = (40, GY + 3, 58); fov = 46
        img, depth = render(S, c, m, cam, tgt, fov, w, h)
        return finish(img)
    if k == 8:   # 硬い道路：割れた画面 → 首をふる人（赤っぽく）
        ci, uu = cut(t, T, [0.45])
        if ci == 0:
            phone(c, m, 40, GY + 1, 26, s=0.6, flat=True, crack=True)
            cam = (44, GY + 10, 18 + 2 * uu); tgt = (40, GY, 26)
            if t < 0.4:
                cam, tgt = shake(cam, tgt, 0.6, t)
            img, depth = render(S, c, m, cam, tgt, 50, w, h)
            return finish(img)
        person(c, m, 40, GY, 52, "stand", look=int(round(math.sin(t * 7) * 1.4)))
        cam = (40 + 4 * math.sin(t * 0.8), GY + 20, 52 - 20 + 4 * uu); tgt = (40, GY + 20, 52)
        img, depth = render(S, c, m, cam, tgt, 56, w, h)
        return finish(img, grade=(1.15, 0.85, 0.82))


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
            ims.append(Image.fromarray((np.clip(frame(int(k), float(t)), 0, 1) * 255).astype(np.uint8)).resize((180, 320)))
        cols = min(10, len(ims))
        sheet = Image.new('RGB', (180 * cols, 320 * ((len(ims) + cols - 1) // cols)))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % cols) * 180, (i // cols) * 320))
        sheet.save(sys.argv[3])
    else:
        os.makedirs('clips_phone', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips_phone/{k + 1:02d}.mp4')
