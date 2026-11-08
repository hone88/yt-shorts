"""もしもの続き「世界から摩擦が10秒だけ消えたら」マイクラ調・カメラが動き続ける背景（文字なし）
使い方: python3 friction_voxel.py stills  /  python3 friction_voxel.py 0,1,2"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import render, particles, smooth, ease, C, f32
import suika_voxel as SV
from elevator_voxel import person, put, draw_x, finish, shake

W, H, FPS, RS = 1080, 1920, 30, 3
CLIPS = [2.8, 4.2, 6.3, 5.9, 5.5, 5.5, 4.4, 6.5]
XFRAC = 0.73
GY = SV.GY
ICE = (0.72, 0.88, 1.05)


def icy(c, m, k):
    """地面の一番上を、ツルツルに光る氷のような色に（k=0〜1）。"""
    top = c[:, GY - 1, :]
    msk = m[:, GY - 1, :] > 0
    c[:, GY - 1, :][msk] = top[msk] * (1 - k) + C(*ICE) * k
    if k > 0.5:
        m[:, GY - 1, :][msk & (m[:, GY, :] == 0)] = 3


def ground():
    S = SV.get('ground', SV.build_ground)
    S.lights = []
    return S, S.base_c.copy(), S.base_m.copy()


def sparkles(img, depth, cam, tgt, fov, t, n=60):
    rg = np.random.default_rng(3)
    p = np.stack([rg.uniform(15, 65, n), np.full(n, GY + 0.1), rg.uniform(25, 75, n)], 1)
    tw = (0.5 + 0.5 * np.sin(t * 9 + rg.uniform(0, 6, n)))[:, None]
    particles(img, depth, cam, tgt, fov, p, C(1.8, 1.9, 2.0) * tw, 0.15)


def frame(k, t):
    w, h = W // RS, H // RS
    T = CLIPS[k]; p = ease(t / T)
    S, c, m = ground()
    if k == 0:   # 歩いていたら、地面が一瞬で氷のように光り、つるっと転ぶ
        slip = 0.45
        ki = smooth(slip, slip + 0.15, t)
        icy(c, m, ki)
        if t < slip:
            z = 40 + 6 * t
            person(c, m, 40, GY, int(z), "stand", look=0)
        else:
            f = t - slip
            z = 40 + 6 * slip + 10 * f
            person(c, m, 40, GY, int(z), "float" if f < 0.35 else "lie")
        cam = (40 + 16 - 10 * p, GY + 16 - 6 * p, z - 30 + 8 * p); tgt = (40, GY + (21 if t < slip else 9), z)
        if slip < t < slip + 0.4:
            cam, tgt = shake(cam, tgt, 0.6, t)
        img, depth = render(S, c, m, cam, tgt, 62, w, h)
        if t > slip:
            sparkles(img, depth, cam, tgt, 62, t)
            if t < slip + 0.15:
                img = img + 0.8 * (1 - (t - slip) / 0.15)
        return finish(img)
    if k == 1:   # 手をばたばたさせながら、氷の上をぐるぐる回る → ×
        icy(c, m, 1.0)
        person(c, m, 40, GY, 52, "float" if int(t * 6) % 2 else "jump", look=int(round(math.sin(t * 5))))
        a = 0.5 + 1.4 * t
        cam = (40 + 34 * math.sin(a), GY + 16, 52 - 34 * math.cos(a)); tgt = (40, GY + 25, 52)
        img, depth = render(S, c, m, cam, tgt, 60, w, h)
        sparkles(img, depth, cam, tgt, 60, t)
        out = finish(img)
        if t >= T * XFRAC:
            out = draw_x(out, min(1.0, (t - T * XFRAC) / 0.15))
        return out
    if k == 2:   # 足が空回り：足もとのアップから、その場でもがく全身へ
        icy(c, m, 1.0)
        pose = ("stand", "float", "crouch", "jump")[int(t * 8) % 4]
        person(c, m, 40, GY, 52, pose, look=int(round(math.sin(t * 6))))
        up = smooth(0, T * 0.8, t)
        cam = (40 + 5 - 3 * up, GY + 3 + 14 * up, 52 - 12 - 16 * up); tgt = (40, GY + 1 + 22 * up, 52)
        img, depth = render(S, c, m, cam, tgt, 58, w, h)
        rg = np.random.default_rng(int(t * 8)); n = 40  # 足もとで空回りする細かい光
        fp = np.stack([40 + rg.normal(0, 2, n), GY + rg.uniform(0, 1.5, n), 52 + rg.normal(0, 2, n)], 1)
        particles(img, depth, cam, tgt, 58, fp, np.tile(C(1.8, 1.9, 2.0), (n, 1)), 0.12)
        return finish(img)
    if k == 3:   # 2本の柱のあいだで、ひもの結び目がするするほどける
        icy(c, m, 1.0)
        for px in (30, 50):
            put(c, m, px, px + 2, GY, GY + 16, 50, 52, (0.45, 0.3, 0.18), 1, 0.05)
        undo = smooth(1.2, T - 1.0, t)
        cx, cy, cz = 40.5, GY + 12, 50.5
        for i in range(-9, 10):  # ひも：両側からまっすぐ、まん中は輪（結び目）
            x = cx + i
            sag = (1 - undo) * 0 + undo * (0.06 * (i * i) - 5.4) * smooth(1.5, 3.5, t)
            put(c, m, x, x + 1, cy + sag, cy + sag + 1, cz, cz + 1, (0.95, 0.85, 0.35), 1, 0.0)
        if undo < 1:
            r = 2.6 * (1 - undo) + 0.01
            for a in np.linspace(0, 2 * np.pi, 28):
                put(c, m, cx + r * math.cos(a), cx + r * math.cos(a) + 1, cy + 1.3 * r * math.sin(a) + 0.5, cy + 1.3 * r * math.sin(a) + 1.5, cz - 0.5 + 0.7 * math.sin(2 * a), cz + 0.5 + 0.7 * math.sin(2 * a), (1.0, 0.9, 0.4), 1, 0.0)
        a = -0.5 + 0.8 * p
        cam = (cx + 18 * math.sin(a), cy + 4, cz - 18 * math.cos(a) + 4 * p); tgt = (cx, cy + 2.5, cz)
        img, depth = render(S, c, m, cam, tgt, 54 - 10 * p, w, h)
        return finish(img)
    if k == 4:   # 車が曲がれず、角をまっすぐ滑っていく（カメラが横を並走）
        icy(c, m, 1.0)
        put(c, m, 66, 72, GY, GY + 3, 10, 40, (0.8, 0.8, 0.82), 1, 0.05)  # 曲がり角のガードレール
        x = 4 + 13 * t
        SV.car(c, m, x, GY, 26)
        cam = (x - 4 + 2 * math.sin(t), GY + 6, 8); tgt = (x + 3, GY + 4, 26)
        cam, tgt = shake(cam, tgt, 0.15, t)
        img, depth = render(S, c, m, cam, tgt, 64, w, h)
        rg = np.random.default_rng(5); n = 140
        sp = np.stack([(rg.uniform(0, 80, n) - 40 * t) % 80, rg.uniform(GY, GY + 12, n), rg.uniform(14, 40, n)], 1)
        for kk in range(4):
            particles(img, depth, cam, tgt, 64, sp + np.array([kk * 0.9, 0, 0]), np.tile(C(1, 1, 1) * (1 - kk / 4), (n, 1)), 0.1)
        return finish(img)
    if k == 5:   # 棚のネジが抜けて、板と本がバラバラに
        x0, z0 = 32, 56
        put(c, m, x0, x0 + 1, GY, GY + 18, z0, z0 + 4, (0.55, 0.35, 0.2), 1, 0.05)
        put(c, m, x0 + 15, x0 + 16, GY, GY + 18, z0, z0 + 4, (0.55, 0.35, 0.2), 1, 0.05)
        fall = smooth(1.4, 2.0, t)
        rg = np.random.default_rng(8)
        for j, by in enumerate((GY + 5, GY + 10, GY + 15)):
            d = fall * (by - GY - 0.5) * min(1.0, (t - 1.4 - 0.12 * j) * 2.5) if t > 1.4 + 0.12 * j else 0
            tilt = 0 if d == 0 else 1
            put(c, m, x0 + 1, x0 + 15, by - d, by - d + 1, z0 + tilt * 0.5, z0 + 4 - tilt * 0.5, (0.65, 0.45, 0.28), 1, 0.05)
            for b in range(5):  # 本
                bx = x0 + 2 + b * 2.6 + (rg.normal(0, 3) * fall if d else 0)
                bh = 3 + (b % 2)
                col = [(0.85, 0.2, 0.2), (0.2, 0.5, 0.9), (0.95, 0.75, 0.2), (0.3, 0.7, 0.35), (0.6, 0.3, 0.75)][(b + j) % 5]
                put(c, m, bx, bx + 2, by - d + 1, by - d + 1 + (bh if not d else 1.5), z0 + 1, z0 + 3, col, 1, 0.03)
        cam = (x0 + 8 + 6 * math.sin(0.4 * t), GY + 11, z0 - 32 + 4 * p); tgt = (x0 + 8, GY + 7, z0)
        if 1.4 < t < 2.4:
            cam, tgt = shake(cam, tgt, 0.7, t)
        img, depth = render(S, c, m, cam, tgt, 60, w, h)
        if t > 1.2:  # ネジがポンポン飛ぶ
            f = t - 1.2
            n = 8
            sp = np.stack([np.repeat([x0 + 0.5, x0 + 15.5], 4) + np.tile([-1, 1, -1, 1], 2) * 6 * f, GY + np.tile([5, 10, 15, 12], 2) + 6 * f - 9 * f * f, np.full(n, z0 - 0.5)], 1)
            ok = sp[:, 1] > GY
            particles(img, depth, cam, tgt, 60, sp[ok], np.tile(C(1.4, 1.4, 1.5), (ok.sum(), 1)), 0.4)
        return finish(img)
    if k == 6:   # 摩擦が戻る：滑っていた車が急にガツンと止まる（氷が緑に戻る）
        stop = 1.3
        ki = 1 - smooth(stop - 0.1, stop + 0.2, t)
        icy(c, m, ki)
        x = 10 + 22 * min(t, stop) + (0 if t < stop else 0.6 * math.sin((t - stop) * 18) * math.exp(-(t - stop) * 5))
        SV.car(c, m, x, GY, 26)
        person(c, m, int(x) - 2, GY, 38, "lie" if t < stop else "stand")
        cam = (x - 2, GY + 12, 4); tgt = (x, GY + 3, 30)
        if stop < t < stop + 0.6:
            cam, tgt = shake(cam, tgt, 1.2 * (1 - (t - stop) / 0.6), t)
        img, depth = render(S, c, m, cam, tgt, 66, w, h)
        if stop < t < stop + 0.5:
            f = t - stop
            rg = np.random.default_rng(2); n = 120
            v = rg.normal(0, 1, (n, 3)); v[:, 1] = np.abs(v[:, 1])
            pp = np.array([x + 7, GY + 0.5, 26]) + v * 9 * f
            particles(img, depth, cam, tgt, 66, pp, np.tile(C(0.8, 0.75, 0.7), (n, 1)), 0.4)
        return finish(img)
    if k == 7:   # 顔にゆっくり寄る
        person(c, m, 40, GY, 52, "stand", look=int(round(math.sin(t * 1.2))))
        cam = (40, GY + 19, 52 - 26 + 9 * p); tgt = (40, GY + 22, 52)
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
        spec = sys.argv[2] if len(sys.argv) > 2 else '0:0.2,0:1.5,1:3.0,2:0.5,2:5.5,3:0.5,3:5.0,4:3.0,5:2.5,6:2.0'
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
        sheet.save('friction_stills.png')
    else:
        os.makedirs('clips', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips/{k + 1:02d}.mp4')
