"""23本目「もしも、スカイツリーから野球ボールを落としたら？」（台本 20261126）。すいかの回のセットを使う。
キャッチャーはオリジナルの人物（紺の帽子・茶色のミット）。1908年の場面はセピア。
使い方: python3 ball_voxel.py stills k:t,... out.png / python3 ball_voxel.py 0,1,2"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import render, particles, smooth, ease, C, f32, Scene
import suika_voxel as SU
from suika_voxel import build_ground, build_sky, tower, get, GY
import elevator_voxel as _EVX
from elevator_voxel import person, put, finish, shake

W, H, FPS, RS = 1080, 1920, 30, 3
_EVX.RS = RS
_est = [5.9, 2.7, 6.7, 4.5, 1.1, 10.4, 5.6, 1.8]
CLIPS = [max(2.6, round(x * 1.27 * 1.15, 1)) for x in _est]
SEPIA = (1.12, 0.95, 0.72)
GLOVE = (0.45, 0.26, 0.12)


def ball(c, m, cx, cy, cz, r, rot=0.0):
    """白い球に赤い縫い目（2本の波線）"""
    xs, ys, zs = np.meshgrid(np.arange(int(cx - r - 1), int(cx + r + 2)), np.arange(int(cy - r - 1), int(cy + r + 2)),
                             np.arange(int(cz - r - 1), int(cz + r + 2)), indexing='ij')
    dx, dy, dz = xs + 0.5 - cx, ys + 0.5 - cy, zs + 0.5 - cz
    rr = np.sqrt(dx * dx + dy * dy + dz * dz)
    inside = rr < r
    ok = inside & (xs >= 0) & (ys >= 0) & (zs >= 0) & (xs < c.shape[0]) & (ys < c.shape[1]) & (zs < c.shape[2])
    a = np.arctan2(dz, dx) + rot
    el = np.arcsin(np.clip(dy / np.maximum(rr, 1e-3), -1, 1))
    seam = np.abs(el - 0.55 * np.sin(2 * a)) < 0.13
    shell = rr > r - 1.3
    col = np.where((seam & shell)[..., None], np.array(C(1.2, 0.15, 0.15)), np.array(C(1.05, 1.03, 0.98)))
    c[xs[ok], ys[ok], zs[ok]] = col[ok]
    m[xs[ok], ys[ok], zs[ok]] = 1


def catcher(c, m, x, z, pose="stand", look=0, glove_up=False, f=1):
    person(c, m, x, GY, z, pose, look=look)
    put(c, m, x - 3, x + 3, GY + 25, GY + 27, z - 3, z + 3, (0.12, 0.16, 0.35), 1, 0.02)     # 紺の帽子
    if glove_up:
        put(c, m, x - 4, x + 4, GY + 27, GY + 32, z - 8, z - 4, GLOVE, 1, 0.05)
        put(c, m, x - 2, x + 2, GY + 28, GY + 31, z - 9, z - 8, (0.3, 0.16, 0.07), 1, 0.0)
    else:
        put(c, m, x + 3, x + 6, GY + 11, GY + 15, z - 3, z, GLOVE, 1, 0.05)


def obelisk(c, m, x, z, h=66):
    """細長い白い塔（1908年の場面）"""
    for y in range(GY, min(GY + h, c.shape[1])):
        w_ = 4 - int(2 * (y - GY) / h)
        put(c, m, x - w_, x + w_, y, y + 1, z - w_, z + w_, (0.92, 0.9, 0.86), 1, 0.04)


def speed_label(img01, text, a):
    if a <= 0.01:
        return img01
    from bento_voxel import font
    im = Image.fromarray((np.clip(img01, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = font(96); bb = d.textbbox((0, 0), text, font=f, anchor="mm"); tw = bb[2] - bb[0]
    x, y = W / 2, H * 0.30
    d.rounded_rectangle([x - tw / 2 - 30, y - 70, x + tw / 2 + 30, y + 70], radius=36, fill=(15, 23, 42, int(200 * a)), outline=(255, 214, 90, int(255 * a)), width=6)
    d.text((x, y), text, font=f, fill=(255, 214, 90, int(255 * a)), anchor="mm")
    return np.asarray(Image.alpha_composite(im, lay).convert("RGB")).astype(f32) / 255


def frame(k, t):
    w, h = W // RS, H // RS
    T = CLIPS[k]; p = ease(t / T)
    if k in (0, 2):   # 空：塔の横をボールと一緒に落ちる。2場面目は速さが一定（流れる速さが変わらない）
        S = get('sky', build_sky)
        c = np.zeros((60, 60, 60, 3), f32); m = np.zeros((60, 60, 60), np.uint8)
        if k == 0:
            drop = 0 if t < 0.6 else (t - 0.6) ** 2 * 10
        else:
            drop = 40 * t
        tower(c, m, drop)
        if k == 0:
            dy = int(min(60, drop))
            put(c, m, 12, 30, 22 + dy, 25 + dy, 18, 42, (0.85, 0.88, 0.95), 1, 0.02)
        ball(c, m, 30, 30, 30, 5, rot=0 if (k == 0 and t < 0.6) else t * 5)
        if k == 0:
            a = 0.3 + 0.9 * p
            cam = (30 + 28 * math.sin(a), 36 + 4 * math.cos(t), 30 - 28 * math.cos(a)); tgt = (30, 30, 30); fov = 66 - 16 * p
        else:
            a = 1.2 + 0.3 * t
            cam = (30 + 24 * math.sin(a), 34, 30 - 24 * math.cos(a)); tgt = (30, 30, 30); fov = 56
        img, depth = render(S, c, m, cam, tgt, fov, w, h)
        if drop > 0:
            rg = np.random.default_rng(5); n = 200
            sp = np.stack([rg.uniform(14, 50, n), (rg.uniform(0, 60, n) + (70 * t if k == 0 else 55 * t)) % 60, rg.uniform(5, 55, n)], 1)
            for kk in range(5):
                particles(img, depth, cam, tgt, fov, sp - np.array([0, kk * 0.9, 0]), np.tile(C(1, 1, 1) * (1 - kk / 5), (n, 1)), 0.12)
        out = finish(img)
        if k == 2:
            out = speed_label(out, "時速 約150km", smooth(T * 0.25, T * 0.4, t))
        return out

    S = get('ground', build_ground)
    c, m = S.base_c.copy(), S.base_m.copy()
    S.lights = []
    if k == 1:   # 見上げる人。上から小さなボールが迫る
        person(c, m, 40, GY, 52, "stand", look=0)
        k2 = smooth(0, T, t)
        ball(c, m, 40, GY + 27 - 3 * k2, 36 + 4 * k2, 2.2 + 1.2 * k2, rot=t * 6)
        cam = (40 + 6 * math.sin(t * 0.6), GY + 6, 22 - 3 * p); tgt = (40, GY + 31, 52)
        img, depth = render(S, c, m, cam, tgt, 64, w, h)
        return finish(img)
    if k == 3:   # ピッチャーが投げる：うしろから。ボールが奥へまっすぐ飛んでいく
        catcher(c, m, 40, 68, "stand")
        q = min(1.0, max(0.0, (t - 0.8) / 1.0))
        bz = 62 - 46 * q
        ball(c, m, 40, GY + 16, bz, 2.0, rot=t * 20)
        cam = (50, GY + 22, 94 - 2 * p); tgt = (40, GY + 13, 30)
        img, depth = render(S, c, m, cam, tgt, 58, w, h)
        if t > 0.8:
            n = 40; zs_ = np.linspace(min(62, bz + 16), bz, n)
            particles(img, depth, cam, tgt, 58, np.stack([np.full(n, 40.0), np.full(n, GY + 16.0), zs_], 1), np.tile(C(1.4, 1.4, 1.4), (n, 1)) * np.linspace(0.1, 1, n)[:, None], 0.5)
        out = finish(img)
        return speed_label(out, "時速 約150km", smooth(0.9, 1.3, t))
    if k == 4:   # キャッチャーが上を見て、ミットを構える
        catcher(c, m, 40, 52, "stand", look=0, glove_up=True)
        cam = (40 + 4 * math.sin(t), GY + 8, 52 - 24 + 4 * p); tgt = (40, GY + 26, 52)
        img, depth = render(S, c, m, cam, tgt, 60, w, h)
        return finish(img)
    if k == 5:   # 1908年（セピア）：細長い塔の下でキャッチャー。ボールが落ちてきて、ミットに入る
        obelisk(c, m, 24, 64)
        catcher(c, m, 42, 52, "stand", look=0, glove_up=True)
        catchT = T * 0.62
        if t < catchT:
            q = t / catchT
            ball(c, m, 41.5 - 16 * (1 - q) * 0.0, GY + 66 - (66 - 33) * q ** 1.6, 49.5, 1.6, rot=t * 8)
        z = ease(min(1.0, t / catchT))
        cam = (42 + 30 * (1 - z) + 6, GY + 18 + 10 * (1 - z), 52 - 40 + 14 * z); tgt = (36 + 6 * z, GY + 30 + 10 * (1 - z), 54)
        if catchT < t < catchT + 0.5:
            cam, tgt = shake(cam, tgt, 0.5 * (1 - (t - catchT) / 0.5), t)
        img, depth = render(S, c, m, cam, tgt, 58, w, h)
        out = finish(img, grade=SEPIA)
        if catchT < t < catchT + 0.15:
            out = out * 0.6 + 0.4
        return out
    if k == 6:   # 注意：首をふる人（赤っぽく）
        person(c, m, 40, GY, 52, "stand", look=int(round(math.sin(t * 7) * 1.4)))
        cam = (40 + 4 * math.sin(t * 0.8), GY + 20, 52 - 20 + 4 * p); tgt = (40, GY + 20, 52)
        img, depth = render(S, c, m, cam, tgt, 56, w, h)
        return finish(img, grade=(1.15, 0.85, 0.82))
    if k == 7:   # ボールを持った人の顔にゆっくり寄る
        person(c, m, 40, GY, 52, "stand", look=int(round(math.sin(t * 1.2))))
        ball(c, m, 46, GY + 19, 49, 2.2, rot=0.3)
        cam = (42, GY + 19, 52 - 26 + 9 * p); tgt = (42, GY + 18, 52)
        img, depth = render(S, c, m, cam, tgt, 54, w, h)
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
            ims.append(im)
        cols = min(8, len(ims))
        sheet = Image.new('RGB', (180 * cols, 320 * ((len(ims) + cols - 1) // cols)))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % cols) * 180, (i // cols) * 320))
        sheet.save(sys.argv[3])
    else:
        os.makedirs('clips_ball', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips_ball/{k + 1:02d}.mp4')
