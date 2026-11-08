"""車の回・作り直し版：全場面でズームアップ／ズームダウン（寄り・引き）を大きく使う。
伸びた回（重力・穴・すいか）と参考動画の分析から：
 - 1コマ目から動いている／超アップ→一気に引いて高さを見せる
 - 場面ごとに「寄る」か「引く」がはっきり分かる大きなカメラの動き
 - 最後は短く（問いかけの場面で離脱が多かったので）
使い方: python3 car2_voxel.py stills / python3 car2_voxel.py 0,1,2"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import render, particles, smooth, ease, C, f32
import suika_voxel as SV
from elevator_voxel import person, put, draw_x, finish, shake
import car_voxel as CV

W, H, FPS, RS = 1080, 1920, 30, 3
CLIPS = [3.3, 3.6, 3.4, 6.6, 3.8, 4.9, 4.4, 3.7]
XFRAC = 0.40
GY = SV.GY
car_s = CV.car_s
melon = CV.SV_melon_orig


def lerp(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


def snap(t, t0, d=0.35):
    """t0 から d 秒で 0→1（速く動いて、ピタッと止まる）"""
    x = min(1.0, max(0.0, (t - t0) / d))
    return 1 - (1 - x) ** 3


def speedlines(img, depth, cam, tgt, fov, t, sp=80, n=220):
    rg = np.random.default_rng(5)
    p = np.stack([rg.uniform(14, 50, n), (rg.uniform(0, 60, n) + sp * t) % 60, rg.uniform(5, 55, n)], 1)
    for kk in range(5):
        particles(img, depth, cam, tgt, fov, p - np.array([0, kk * 0.9, 0]), np.tile(C(1, 1, 1) * (1 - kk / 5), (n, 1)), 0.12)


def sky_frame(t, drop, cam, tgt, fov, deck_up=None, rot=0.0, lines=True):
    S = SV.get('sky', SV.build_sky)
    c = np.zeros((60, 60, 60, 3), f32); m = np.zeros((60, 60, 60), np.uint8)
    SV.tower(c, m, drop)
    if deck_up is not None:
        put(c, m, 12, 30, 22 + deck_up, 25 + deck_up, 18, 42, (0.85, 0.88, 0.95), 1, 0.02)
    car_s(c, m, 30, 30, 30, 7, rot=rot)
    img, depth = render(S, c, m, cam, tgt, fov, W // RS, H // RS)
    if lines and drop > 0:
        speedlines(img, depth, cam, tgt, fov, t)
    return finish(img)


def ground():
    S = SV.get('ground', SV.build_ground); S.lights = []
    return S, S.base_c.copy(), S.base_m.copy()


def frame(k, t):
    w, h = W // RS, H // RS
    T = CLIPS[k]; p = ease(t / T)
    if k == 0:   # 展望台のふちの車に超アップ → 落ちた瞬間、一気に引いて高さを見せる
        tip = 0.6
        f = max(0.0, t - tip)
        drop = 14 * f * f
        k2 = snap(t, tip, 1.4)
        a = 0.5 + 0.6 * k2
        d = 20 + 36 * k2
        cam = (30 + d * math.sin(a), 32 + 10 * k2, 30 - d * math.cos(a)); tgt = (30, 30 - 4 * k2, 30)
        fov = 44 + 30 * k2
        if t < tip:
            cam, tgt = shake(cam, tgt, 0.15, t)
        return sky_frame(t, drop, cam, tgt, fov, deck_up=int(min(60, drop)), rot=f * 3)
    if k == 1:   # 見上げる人と、頭上の車 → 顔へ一気にズームアップ → ×
        S, c, m = ground()
        person(c, m, 40, GY, 52, "stand", look=0)
        k2 = smooth(0, T, t)
        car_s(c, m, 40, GY + 25 - 3 * k2, 34 + 5 * k2, 4.5 * 1.2, rot=t * 5)
        z = snap(t, 0.9, 0.45)
        cam = lerp((40 + 8 * math.sin(t * 0.6), GY + 6, 18), (40, GY + 22, 33), z)
        tgt = lerp((40, GY + 31, 52), (40, GY + 23.5, 52), z)
        fov = 70 - 30 * z
        img, depth = render(S, c, m, cam, tgt, fov, w, h)
        out = finish(img)
        if t >= T * XFRAC:
            out = draw_x(out, min(1.0, (t - T * XFRAC) / 0.15))
        return out
    if k == 2:   # すいか1個の超アップ → 一気に引くと、車とすいかの山
        S, c, m = ground()
        car_s(c, m, 31, GY + 4.5, 50, 6.0)
        for layer, (nx, nz) in enumerate(((4, 3), (3, 2), (2, 1))):
            for i in range(nx):
                for j in range(nz):
                    x = 46 + (i - (nx - 1) / 2) * 5.0; z = 50 + (j - (nz - 1) / 2) * 5.0
                    melon(c, m, x, GY + 2.3 + layer * 4.2, z, 2.4, rot=i + j)
        z = snap(t, 0.5, 1.0)
        cam = lerp((46, GY + 12, 32), (37, GY + 13, 18), z); tgt = lerp((46, GY + 11, 50), (39, GY + 3, 50), z)
        fov = 42 + 24 * z
        img, depth = render(S, c, m, cam, tgt, fov, w, h)
        return finish(img)
    if k == 3:   # 落ちる車と並んで落ちる：寄る→一気に引く→また寄る
        drop = 40 + 9 * (t + 2) ** 2
        out_ = snap(t, 1.6, 0.5) - snap(t, 4.4, 0.5)
        d = 22 + 28 * out_
        a = 1.0 + 0.5 * t
        cam = (30 + d * math.sin(a), 33 + 6 * out_, 30 - d * math.cos(a)); tgt = (30, 30, 30)
        cam, tgt = shake(cam, tgt, 0.35 * (1 - out_), t)
        return sky_frame(t, drop, cam, tgt, 56 + 12 * out_, rot=t * 4)
    if k == 4:   # 着地：下から見上げると車が迫る → ドガーンの瞬間に一気に引く（CVの着地場面）
        return CV.crater(t, 'impact')
    if k == 5:   # ぺしゃんこの車に超アップ → 真上へぐんぐん引いて、穴の大きさを見せる
        CV.CLIPS[5] = T
        S, c, m = ground()
        cx, cz = 40, 50
        xs, zs = np.meshgrid(np.arange(cx - 22, cx + 23), np.arange(cz - 22, cz + 23), indexing='ij')
        rr = np.hypot(xs + 0.5 - cx, zs + 0.5 - cz)
        dep = np.clip(9.0 * (1 - (rr / 15.0) ** 2), 0, None)
        for x, z_, d_, r_ in zip(xs.ravel(), zs.ravel(), dep.ravel(), rr.ravel()):
            if d_ > 0.5:
                top = GY - int(round(d_)); m[x, top:GY, z_] = 0
                c[x, top - 1, z_] = C(0.45, 0.3, 0.18) if (hash((x, z_)) % 5) else C(0.25, 0.22, 0.2)
            elif 14.5 <= r_ < 18:
                put(c, m, x, x + 1, GY, GY + 1 + (hash((x, z_)) % 3), z_, z_ + 1, (0.42, 0.3, 0.18), 1, 0.1)
        car_s(c, m, cx, GY - 8.0, cz, 6.5, crushed=1.0)
        z = smooth(0.3, T, t)
        cam = lerp((cx + 0.01, GY + 6, cz - 13), (cx + 0.01, GY + 58, cz - 26), z); tgt = (cx, GY - 7, cz)
        fov = 50 + 16 * z
        img, depth = render(S, c, m, cam, tgt, fov, w, h)
        return finish(img)
    if k == 6:   # 注意：引きから顔へ一気にズームアップ（赤っぽく）
        S, c, m = ground()
        person(c, m, 40, GY, 52, "stand", look=int(round(math.sin(t * 7) * 1.4)))
        z = snap(t, 0.2, 0.5)
        cam = lerp((40, GY + 12, 52 - 40), (40, GY + 19, 52 - 19), z); tgt = lerp((40, GY + 14, 52), (40, GY + 21, 52), z)
        img, depth = render(S, c, m, cam, tgt, 62 - 22 * z, w, h)
        return finish(img, grade=(1.15, 0.85, 0.82))
    if k == 7:   # 最後：顔のアップから一気に引くと、まわりに次の候補（鉄・木・アリ）
        S, c, m = ground()
        person(c, m, 40, GY, 52, "stand", look=int(round(math.sin(t * 1.5))))
        put(c, m, 26, 32, GY, GY + 5, 48, 54, (0.55, 0.56, 0.6), 1, 0.08)          # 鉄のかたまり
        put(c, m, 51, 53, GY, GY + 8, 50, 52, (0.42, 0.28, 0.16), 1, 0.05)          # 木
        put(c, m, 49, 55, GY + 8, GY + 13, 48, 54, (0.25, 0.55, 0.22), 1, 0.12)
        put(c, m, 34, 35, GY, GY + 0.6, 44, 45.5, (0.1, 0.08, 0.08), 1, 0.0)       # アリ
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
        ff.stdin.write((frame(k, i / FPS) * 255 + 0.5).astype(np.uint8).tobytes())
        if i % 30 == 0: print(k, i, flush=True)
    ff.stdin.close()
    if ff.wait() == 0:
        os.replace(tmp, out); print('done', out, flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        spec = sys.argv[2] if len(sys.argv) > 2 else '0:0.2,0:2.5,1:0.3,1:2.0,2:0.2,2:2.5,3:0.5,3:3.0,5:0.2,5:4.5,6:0.1,6:2.0,7:0.1,7:2.5'
        ims = []
        for s_ in spec.split(','):
            k, t = s_.split(':')
            im = Image.fromarray((frame(int(k), float(t)) * 255).astype(np.uint8)).resize((180, 320))
            d = ImageDraw.Draw(im)
            for y in (int(320 * .36), int(320 * .43), int(320 * .68)):
                d.line([(0, y), (180, y)], fill=(255, 0, 0), width=1)
            ims.append(im)
        sheet = Image.new('RGB', (180 * 7, 320 * ((len(ims) + 6) // 7)))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % 7) * 180, (i // 7) * 320))
        sheet.save('car2_stills.png')
    else:
        os.makedirs('clips', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips/{k + 1:02d}.mp4')
