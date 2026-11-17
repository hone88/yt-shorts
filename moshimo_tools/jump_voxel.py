"""20本目「もしも摩擦ゼロの地面で、真上にジャンプしたら？」（台本 20261125）。摩擦の回・地球の回の続き。
使い方: python3 jump_voxel.py stills k:t,... out.png / python3 jump_voxel.py 0,1,2"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import render, particles, ease, smooth, C, f32, Scene
from elevator_voxel import person, put, finish, shake
import friction_voxel as FV
import earth_voxel as EV
from earth_voxel import earth, hstreaks, GY, surf, TOKYO
from kaguya2_voxel import snap, lerp

W, H, FPS, RS = 1080, 1920, 30, 3
import elevator_voxel as _EVX
_EVX.RS = RS             # kaguya2_voxel を読むと elevator_voxel.RS が 4 になり、finish() の拡大がずれるので戻す（11/17）
_est = [4.4, 2.2, 4.5, 5.5, 5.2, 7.6, 7.4, 7.5, 5.8, 5.6, 7.9]
CLIPS = [round(x * 1.27 * 1.15, 1) for x in _est]
PX, PZ = 40, 50          # 立つ位置
HOP = 7                  # 跳ぶ高さ（ブロック。約0.5m）


_T = {}


def town():
    """町（高さ70では跳んだ頭が切れるので、上を30足して100に）"""
    if 't' not in _T:
        S0 = EV.town()
        S = Scene(80, 100, 100)
        S.col[:, :70, :] = S0.base_c; S.mat[:, :70, :] = S0.base_m
        for a in ('sun', 'sunc', 'amb', 'hor', 'top', 'fog0', 'fogk', 'sundisk'):
            setattr(S, a, getattr(S0, a))
        S.lights = []
        S.base_c, S.base_m = S.col.copy(), S.mat.copy()
        _T['t'] = S
    return _T['t']


def roll_town(S, sh):
    return np.roll(S.base_c, -sh, axis=0).copy(), np.roll(S.base_m, -sh, axis=0).copy()


def ice():
    S = town(); c, m = S.base_c.copy(), S.base_m.copy()
    FV.icy(c, m, 1.0)
    return S, c, m


def hop(t, t0, dur=0.9):
    """t0 から dur 秒の放物線ジャンプの高さ（0〜HOP）"""
    u = (t - t0) / dur
    if u <= 0 or u >= 1:
        return 0.0
    return HOP * 4 * u * (1 - u)


def mark(c, m, x, z, col=(1.3, 0.25, 0.25)):
    """地面の×じるし（着地点）"""
    for i in range(-3, 4):
        put(c, m, x + i, x + i + 1, GY - 1, GY, z + i, z + i + 1, col, 1, 0.0)
        put(c, m, x + i, x + i + 1, GY - 1, GY, z - i, z - i + 1, col, 1, 0.0)


def arrow_up(img, depth, cam, tgt, fov, x, y0, y1, z, a=1.0):
    n = 30
    p = np.stack([np.full(n, x), np.linspace(y0, y1, n), np.full(n, z)], 1)
    particles(img, depth, cam, tgt, fov, p, np.tile(C(1.8, 1.6, 0.4) * a, (n, 1)), 0.35)


def build_macro():
    """足もとの超アップ（1ブロック＝約0.008mm）：くつ底のふち、元の線、髪の毛"""
    S = Scene(80, 40, 80)
    c, m = S.col, S.mat
    put(c, m, 0, 80, 0, 4, 0, 80, (0.72, 0.86, 1.0), 1, 0.06)                  # 氷の床（表面のざらつき）
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = np.array([0.3, 0.85, -0.4]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.15, 1.08, 1.0); S.amb = C(0.55, 0.6, 0.72)
    S.hor = C(0.85, 0.9, 1.0); S.top = C(0.5, 0.65, 0.95); S.fog0, S.fogk = 200, 400
    return S


_F = {}


def jfont(sz):
    if sz not in _F:
        from PIL import ImageFont
        _F[sz] = ImageFont.truetype(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts', 'NotoSansCJK-Black.ttc'), sz)
    return _F[sz]


def lens(img01, a, land):
    """画面の上に虫めがねの円。1px＝約0.00033mm（髪の毛0.08mm＝240px、ズレ0.025mm＝75px）"""
    if a <= 0.01:
        return img01
    im = Image.fromarray((np.clip(img01, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    R_, cx, cy = 220, W - 250, int(H * 0.235)             # 1px＝約0.00045mm（髪の毛0.08mm＝176px、ズレ0.025mm＝55px）
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.line([(cx - 60, cy + R_ - 10), (int(W * 0.5), int(H * 0.62))], fill=(255, 255, 255, 200), width=8)
    inner = Image.new("RGBA", (2 * R_, 2 * R_), (205, 235, 250, 255)); di = ImageDraw.Draw(inner)
    lx = R_ + 70                                                    # 元の位置（赤い線）
    sx = lx - int(55 * land)                                        # くつのふち（着地で55pxだけ左＝西へ）
    di.rectangle([sx, 0, 2 * R_, int(R_ * 1.1)], fill=(60, 62, 70, 255))
    di.rectangle([sx, 0, sx + 8, int(R_ * 1.1)], fill=(35, 36, 42, 255))
    for yy in range(0, 2 * R_, 24):
        di.line([(lx, yy), (lx, yy + 14)], fill=(230, 40, 40, 255), width=7)
    di.rectangle([0, int(R_ * 1.25), 2 * R_, int(R_ * 1.25) + 176], fill=(70, 45, 25, 255))   # 髪の毛
    di.text((lx + 12, int(R_ * 1.12)), "元の位置", font=jfont(30), fill=(220, 30, 30, 255))
    di.text((110, int(R_ * 1.25) + 70), "髪の毛の太さ", font=jfont(36), fill=(255, 235, 200, 255))
    if land > 0.95:
        y0 = int(R_ * 0.7)
        di.line([(sx, y0), (lx, y0)], fill=(255, 214, 90, 255), width=8)
        di.text((sx - 10, y0), "0.025mm", font=jfont(40), fill=(255, 214, 90, 255), anchor="rm",
                stroke_width=4, stroke_fill=(20, 20, 30, 255))
    mask = Image.new("L", inner.size, 0); ImageDraw.Draw(mask).ellipse([0, 0, 2 * R_ - 1, 2 * R_ - 1], fill=int(255 * a))
    lay.paste(inner, (cx - R_, cy - R_), mask)
    d.ellipse([cx - R_, cy - R_, cx + R_, cy + R_], outline=(255, 255, 255, int(255 * a)), width=12)
    im = Image.alpha_composite(im, lay).convert("RGB")
    return np.asarray(im).astype(f32) / 255


_M = {}


def macro():
    if 'm' not in _M:
        _M['m'] = build_macro()
    return _M['m']


def frame(k, t):
    w, h = W // RS, H // RS
    T = CLIPS[k]; u = t / T
    if k == 0:   # 摩擦ゼロ：歩こうとしても足がすべってもがく
        S, c, m = ice()
        pose = ("stand", "float", "crouch", "jump")[int(t * 7) % 4]
        person(c, m, PX, GY, PZ, pose, look=int(round(math.sin(t * 6))))
        z = ease(min(1, u * 1.3))
        cam = lerp((PX + 8, GY + 10, PZ - 40), (PX + 26, GY + 22, PZ - 56), z); tgt = (PX, GY + 9, PZ)
        img, depth = render(S, c, m, cam, tgt, 56, w, h)
        FV.sparkles(img, depth, cam, tgt, 56, t)
        rg = np.random.default_rng(int(t * 8)); n = 40
        fp = np.stack([PX + rg.normal(0, 2, n), GY + rg.uniform(0, 1.5, n), PZ + rg.normal(0, 2, n)], 1)
        particles(img, depth, cam, tgt, 56, fp, np.tile(C(1.8, 1.9, 2.0), (n, 1)), 0.12)
        return finish(img)
    if k == 1:   # 真上なら？：しゃがんで、ためる（下から見上げる）
        S, c, m = ice()
        person(c, m, PX, GY, PZ, "crouch" if t > 0.6 else "stand", look=0)
        z = ease(u)
        cam = lerp((PX - 16, GY + 4, PZ - 44), (PX - 10, GY + 3, PZ - 38), z); tgt = (PX, GY + 12, PZ)
        img, depth = render(S, c, m, cam, tgt, 58, w, h)
        FV.sparkles(img, depth, cam, tgt, 58, t)
        return finish(img)
    if k == 2:   # できる：真上にジャンプ、ジャンプ（上向きの光）
        S, c, m = ice()
        ts = [0.5, 2.0, 3.5, 5.0]
        y = max(hop(t, s) for s in ts)
        air = y > 0.3
        person(c, m, PX, GY + int(round(y)), PZ, "jump" if air else "stand", look=0)
        a = 0.3 + 0.6 * ease(u)
        cam = (PX + 56 * math.sin(a), GY + 16, PZ - 56 * math.cos(a)); tgt = (PX, GY + 11, PZ)
        img, depth = render(S, c, m, cam, tgt, 56, w, h)
        FV.sparkles(img, depth, cam, tgt, 56, t)
        if air:
            arrow_up(img, depth, cam, tgt, 56, PX - 8, GY + 2, GY + 22, PZ, 1.0)
        return finish(img)
    if k == 3:   # コメント：「ちょっとずつズレるのは？」 宙に浮いた僕のまわりをカメラが回る
        S, c, m = ice()
        y = hop(t % 1.6, 0.2, 1.2) * 1.2
        person(c, m, PX, GY + int(round(y)), PZ, "jump" if y > 0.3 else "stand", look=int(round(math.sin(t * 1.5))))
        mark(c, m, PX, PZ - 6)
        a = -0.6 + 0.9 * ease(u)
        cam = (PX + 50 * math.sin(a), GY + 24, PZ - 50 * math.cos(a)); tgt = (PX, GY + 9, PZ)
        img, depth = render(S, c, m, cam, tgt, 56, w, h)
        return finish(img)
    if k == 4:   # 地球は時速1,360kmで回っている：回る地球と、光る東京
        E = earth()
        ang = 0.9 * t
        z = ease(u)
        cam = lerp((32 - 30, 70, 32 - 120), (32 - 14, 58, 32 - 86), z); tgt = (32, 34, 32)
        p1 = 1 + 0.25 * math.sin(t * 8)
        mk = [(surf(TOKYO[0], TOKYO[1], ang, 28.5), C(2.0, 1.7, 0.4), 3.0 * p1)]
        img, depth = E.draw(ang, cam, tgt, 46, mk)
        return finish(img)
    if k == 5:   # もし地球だけ先に回ったら：浮いている間に、地面が後ろへ流れていく（240m）
        S = town()
        t0 = 0.6
        uu = max(0.0, t - t0)
        nfr = round(uu * FPS)
        sh = min(nfr * 2, nfr * (nfr + 1) // 6)
        c, m = roll_town(S, sh)
        y = 0 if t < t0 else min(HOP, (t - t0) * 20)
        person(c, m, PX, GY + int(round(y)), 26, "jump" if t >= t0 else "crouch", look=0)
        z = snap(t, t0 + 0.2, 0.8)
        cam = lerp((PX + 10, GY + 20, 26 - 30), (PX - 34, GY + 26, 26 - 46), z); tgt = lerp((PX, GY + 14, 26), (PX + 6, GY + 12, 30), z)
        img, depth = render(S, c, m, cam, tgt, 54 + 6 * z, w, h)
        if t >= t0:
            hstreaks(img, depth, cam, tgt, 60, t, -240 * min(1, uu * 2), n=160, y0=GY + 1, y1=GY + 28, z0=6, z1=60)
        return finish(img)
    if k == 6:   # 置いていかれない：×じるしの上で跳んで、同じ×に着地（何度も）
        S, c, m = ice()
        mark(c, m, PX, PZ)
        ts = [0.6, 2.4, 4.2, 6.0]
        y = max(hop(t, s, 1.1) for s in ts)
        person(c, m, PX, GY + int(round(y)), PZ, "jump" if y > 0.3 else "stand", look=0)
        z = ease(u)
        cam = lerp((PX + 30, GY + 30, PZ - 50), (PX + 16, GY + 20, PZ - 48), z); tgt = (PX, GY + 9, PZ)
        img, depth = render(S, c, m, cam, tgt, 54, w, h)
        FV.sparkles(img, depth, cam, tgt, 54, t)
        return finish(img)
    if k == 7:   # 0.025ミリ：着地した足もとに寄る → 虫めがね（元の線・くつのふち・髪の毛の太さ）
        S, c, m = ice()
        mark(c, m, PX, PZ)
        person(c, m, PX, GY, PZ, "stand", look=0)
        z = ease(min(1, u * 1.5))
        cam = lerp((PX + 16, GY + 20, PZ - 40), (PX + 10, GY + 8, PZ - 26), z); tgt = lerp((PX, GY + 9, PZ), (PX, GY + 1, PZ), z)
        img, depth = render(S, c, m, cam, tgt, 54, w, h)
        return lens(finish(img), smooth(T * 0.15, T * 0.3, t), smooth(T * 0.3, T * 0.45, t))
    if k == 8:   # 1度ななめに蹴ると：着地してからも止まらずに滑っていく
        S, c, m = ice()
        mark(c, m, PX, PZ)
        t0 = 0.6
        y = hop(t, t0, 1.0)
        dz = 0.0 if t < t0 else (t - t0) * 2.2
        person(c, m, PX, GY + int(round(y)), int(round(PZ + dz)), "jump" if y > 0.3 else ("float" if t > t0 + 1.0 else "stand"),
               look=int(round(math.sin(t * 4))) if t > t0 + 1.0 else 0)
        cam = (PX + 34, GY + 26, PZ - 46 + dz * 0.6); tgt = (PX, GY + 9, PZ + dz)
        img, depth = render(S, c, m, cam, tgt, 54, w, h)
        FV.sparkles(img, depth, cam, tgt, 54, t)
        return finish(img)
    if k == 9:   # 1時間で約200m：上から見ると、町をゆっくり横切っていく（早回し）
        S = town(); c, m = S.base_c.copy(), S.base_m.copy()
        FV.icy(c, m, 1.0)
        zz = int(round(20 + 60 * ease(u)))
        person(c, m, PX, GY, zz, "float", look=0)
        cam = (PX + 24, GY + 46, zz - 34); tgt = (PX, GY + 4, zz + 4)
        img, depth = render(S, c, m, cam, tgt, 56, w, h)
        rg = np.random.default_rng(4); n = 30                  # 通ったあとの光るすじ
        p = np.stack([np.full(n, PX) + rg.normal(0, 0.6, n), np.full(n, GY + 0.2), np.linspace(20, zz, n)], 1)
        particles(img, depth, cam, tgt, 56, p, np.tile(C(1.6, 1.8, 2.0), (n, 1)), 0.4)
        return finish(img)
    if k == 10:  # 最後：すべっていく僕から、一気に上へ引く
        S = town(); c, m = S.base_c.copy(), S.base_m.copy()
        FV.icy(c, m, 1.0)
        zz = int(round(30 + 3 * t))
        person(c, m, PX, GY, zz, "float", look=int(round(math.sin(t * 1.5))))
        z = snap(t, T * 0.5, 1.2)
        cam = lerp((PX, GY + 20, zz - 40), (PX + 18, GY + 50, max(2, zz - 48)), z); tgt = lerp((PX, GY + 12, zz), (PX, GY + 2, zz + 8), z)
        img, depth = render(S, c, m, cam, tgt, 48 + 12 * z, w, h)
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
        sheet.save(sys.argv[3])
    else:
        os.makedirs('clips_jump', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips_jump/{k + 1:02d}.mp4')
