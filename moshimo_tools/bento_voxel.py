"""物語回2「もしも、親にしてもらったことの回数が、頭の上に見えたら？」（台本 20261124）。story_voxel のセット・人を使う。
登場人物はすべてオリジナル：
  僕   …高校生。白いシャツ・紺のズボン・黒い短髪
  母さん…ベージュの服・ピンクのエプロン・おだんご（story_voxel と同じ）
頭の上の数字は、画面の上の方（見出しより上）に文字で重ねる。
使い方:
  python3 bento_voxel.py stills k:t,... out.png
  python3 bento_voxel.py 0,2,4"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import ease, C, f32, camera
import story_voxel as SV
from story_voxel import H_, HEAD, aim, shoot, crowd, bento, FY, P_MOM, GOLD, CYAN, PINK, font, project
from kaguya2_voxel import cut, snap, lerp

W, H, FPS = SV.W, SV.H, SV.FPS
_est = [3.8, 3.6, 1.5, 1.5, 5.9, 3.7, 2.2, 1.7, 3.8, 2.7, 2.6, 3.2, 1.4, 1.5, 3.4, 2.7]
CLIPS = [round(x * 1.27 * 1.15, 1) for x in _est]
SV.CLIPS = CLIPS
P_STU = {"髪": (0.1, 0.08, 0.07), "服": (0.95, 0.95, 0.95), "服2": (0.85, 0.85, 0.88), "下": (0.14, 0.17, 0.3), "靴": (0.3, 0.2, 0.14)}
EVE = (1.06, 0.86, 0.72)
SEPIA = SV.SEPIA

MX, MZ = 45, 56          # 台所の母さん
BX, BZ = 45, 20          # 台所の僕
HX, HMZ, HBZ = 50, 56, 22   # 玄関


_K = SV.get("kitchen"); _K.lights = [((45, FY + 40, 22), (0.75, 0.68, 0.6), 70)]; _K.amb = C(0.7, 0.68, 0.68)


def box(c, m, x, y, z, col):
    SV.put(c, m, x, x + 8, y, y + 3, z, z + 6, col, 1, 0.02)
    SV.put(c, m, x + 1, x + 7, y + 3, y + 4, z + 1, z + 5, (0.98, 0.98, 0.96), 1, 0.02)


BOXC = [(0.2, 0.25, 0.55), (0.85, 0.3, 0.3), (0.95, 0.7, 0.2), (0.3, 0.6, 0.35), (0.6, 0.35, 0.65)]


def me(cx, cz, f=1, face="ふつう", fy=FY, **kw):
    return H_(cx=cx, fy=fy, cz=cz, P=P_STU, face=face, f=f, **kw)


def mom(cx, cz, f=-1, face="笑顔", fy=FY, **kw):
    return H_(cx=cx, fy=fy, cz=cz, P=P_MOM, face=face, f=f, bun=True, apron=True, **kw)


def held_bento(cx, cz, f, fy=FY, empty=False):
    """arms="front" の手の上のお弁当"""
    z0 = cz + 8 if f > 0 else cz - 14
    def d(c, m):
        if empty:
            SV.put(c, m, cx - 4, cx + 4, fy + 20, fy + 23, z0, z0 + 6, (0.2, 0.25, 0.55), 1, 0.02)
        else:
            bento(c, m, cx - 4, fy + 20, z0)
    return d


def tags2(img, cam, tgt, fov, items):
    """items: [(頭の3D位置, 文字, 濃さ, 色)]。顔の右どなりに、上に小さく名前・下に大きく数字の札を置く。
    上の見出し（0〜22%）と真ん中の字幕（36%〜）にかからないよう、たての位置は 23〜33% におさめる。"""
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for p, text, a, col in items:
        if a <= 0.01:
            continue
        pr = project(cam, tgt, fov, p)
        if pr is None:
            continue
        x, y, z = pr
        lab, num = (text.rsplit(" ", 1) if " " in text else ("", text))
        fl, fn = font(42), font(104)
        bl = d.textbbox((0, 0), lab, font=fl, anchor="mm") if lab else (0, 0, 0, 0)
        bn = d.textbbox((0, 0), num, font=fn, anchor="mm")
        bw = max(bl[2] - bl[0], bn[2] - bn[0]) + 56
        bh = (bn[3] - bn[1]) + (bl[3] - bl[1] + 18 if lab else 0) + 44
        cx = float(np.clip(x + W * 0.17 + bw / 2, bw / 2 + 24, W - bw / 2 - 24))
        cy = float(np.clip(y, H * 0.23 + bh / 2, H * 0.335 - bh / 2))
        d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], radius=30,
                            fill=(15, 23, 42, int(190 * a)), outline=col + (int(255 * a),), width=6)
        if lab:
            d.text((cx, cy - bh / 2 + 22 + (bl[3] - bl[1]) / 2), lab, font=fl, fill=(235, 238, 245, int(255 * a)), anchor="mm")
            d.text((cx, cy + bh / 2 - 22 - (bn[3] - bn[1]) / 2), num, font=fn, fill=col + (int(255 * a),), anchor="mm")
        else:
            d.text((cx, cy), num, font=fn, fill=col + (int(255 * a),), anchor="mm")
    im = Image.alpha_composite(im, lay).convert("RGB")
    return np.asarray(im).astype(f32) / 255


def fixed_tags(img, items):
    """画面の決まった高さに、まん中そろえで札を置く"""
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for y, text, a, col in items:
        if a <= 0.01:
            continue
        f = font(66); bb = d.textbbox((0, 0), text, font=f, anchor="mm"); tw, th = bb[2] - bb[0], bb[3] - bb[1]; pad = 26; x = W / 2
        d.rounded_rectangle([x - tw / 2 - pad, y - th / 2 - pad * 0.8, x + tw / 2 + pad, y + th / 2 + pad * 0.8], radius=34,
                            fill=(15, 23, 42, int(190 * a)), outline=col + (int(255 * a),), width=6)
        d.text((x, y), text, font=f, fill=col + (int(255 * a),), anchor="mm")
    im = Image.alpha_composite(im, lay).convert("RGB")
    return np.asarray(im).astype(f32) / 255


def shot(set_, cam, tgt, fov, draws, tg=(), **kw):
    img = shoot(set_, cam, tgt, fov, draws, **kw)
    if tg:
        img = tags2(img, cam, tgt, fov, tg)
    return img


def fade(t, t0, d=0.4):
    return float(np.clip((t - t0) / d, 0, 1))


def frame(k, t):
    T = CLIPS[k]; u = t / T
    mh = HEAD(MX, FY, MZ); bh = HEAD(BX, FY, BZ)
    if k == 0:   # もしも：台所の母さん。頭の上に「？？？」がふわっと出る
        z = ease(u)
        c1, t1, f1 = aim(mh, -1, 34, 0.25, 4, 48)
        c2, t2, _ = aim(mh, -1, 26, 0.05, 2, 46)
        return shot("kitchen", lerp(c1, c2, z), lerp(t1, t2, z), 46, [mom(MX, MZ)], t=t, tg=[(mh, "？？？", fade(t, 0.8), GOLD)])
    if k == 1:   # ある朝：僕のおどろいた顔 → 母さんの頭の上の数字
        c_, uu = cut(t, T, [0.5])
        if c_ == 0:
            cam, tgt, fov = aim(bh, 1, 24 - 3 * uu, 0.2, 2, 46)
            return shot("kitchen", cam, tgt, fov, [me(BX, BZ, face="驚き"), mom(MX, MZ)], t=t)
        cam = (BX + 14, FY + 32, BZ - 12 + 3 * uu); tgt = (MX - 2, FY + 24, MZ)
        return shot("kitchen", cam, tgt, 48, [me(BX, BZ, face="驚き"), mom(MX, MZ)], t=t, tg=[(mh, "？？？", 1.0, GOLD)])
    if k == 2:   # お弁当、1200：お弁当をさし出す母さん
        z = ease(u)
        c1, t1, _ = aim(mh, -1, 34, -0.2, 4, 48)
        c2, t2, _ = aim(mh, -1, 28, -0.05, 2, 46)
        return shot("kitchen", lerp(c1, c2, z), lerp(t1, t2, z), 46, [mom(MX, MZ, arms="front"), held_bento(MX, MZ, -1)], t=t,
                    tg=[(mh, "お弁当 1200", fade(t, 0.15, 0.3), GOLD)])
    if k == 3:   # 多くね？：僕のアップ（ズーム）
        z = ease(u)
        c1, t1, _ = aim(bh, 1, 26, -0.15, 2, 46)
        c2, t2, _ = aim(bh, 1, 18, -0.05, 2, 44)
        return shot("kitchen", lerp(c1, c2, z), lerp(t1, t2, z), 46, [me(BX, BZ, face="驚き")], t=t, sh=0.2 if t < 0.4 else 0.0)
    if k == 4:   # 6年×約200日：テーブルの上にお弁当がどんどん積み上がる（セピア）
        n = int(1 + 39 * ease(min(1, u * 1.15)))
        def stack(c, m):
            for i in range(n):
                col, lv = i % 5, i // 5
                box(c, m, 21 + col * 10, FY + 15 + lv * 4, 37, BOXC[(col + lv * 2) % 5])
        z = ease(u)
        cam = (45, FY + 30 + 10 * z, 2); tgt = (45, FY + 18 + 12 * z, 40)
        return shot("kitchen", cam, tgt, 56, [stack], t=t, grade=SEPIA, vign=0.5)
    if k == 5:   # 玄関：見送る母さん（手をふる）。僕のうしろ姿ごし
        c_, uu = cut(t, T, [0.5])
        dr = [mom(HX, HMZ, fy=FY + 4, arms="wave"), me(HX + 4, HBZ, f=1)]
        mhh = HEAD(HX, FY + 4, HMZ)
        if c_ == 0:
            cam = (HX + 26, FY + 36, HBZ - 14 + 2 * uu); tgt = (HX - 2, FY + 26, HMZ)
            return shot("home", cam, tgt, 48, dr, t=t)
        cam, tgt, fov = aim(mhh, -1, 30 - 2 * uu, 0.15, 2, 46)
        return shot("home", cam, tgt, fov, dr[:1], t=t, tg=[(mhh, "いってらっしゃい ？", fade(uu * T * 0.5, 0.1), PINK)])
    if k == 6:   # いってらっしゃい、約4000
        mhh = HEAD(HX, FY + 4, HMZ)
        z = ease(u)
        c1, t1, _ = aim(mhh, -1, 30, 0.1, 2, 46)
        c2, t2, _ = aim(mhh, -1, 24, 0.0, 2, 46)
        return shot("home", lerp(c1, c2, z), lerp(t1, t2, z), 46, [mom(HX, HMZ, fy=FY + 4, arms="wave")], t=t,
                    tg=[(mhh, "いってらっしゃい 4000", 1.0, PINK)])
    if k == 7:   # そんなに言ってたっけ：玄関で、母さんの方をふり返る僕
        bhh = HEAD(HX + 4, FY, HBZ)
        cam, tgt, fov = aim(bhh, 1, 22 - 2 * u, 0.3, 2, 46)
        return shot("home", cam, tgt, fov, [me(HX + 4, HBZ, f=1, face="ふつう")], t=t)
    if k == 8:   # 帰り道（夕方）：歩いてきて、立ち止まる。自分の頭の上に「？」
        zz = int(70 - 5 * min(t, T * 0.5))
        walk = t < T * 0.5
        h_ = HEAD(60, FY, zz)
        cam, tgt, fov = aim(h_, -1, 34 - 6 * ease(u), 0.25, 3, 48)
        return shot("street", cam, tgt, fov, [me(60, zz, f=-1, face="驚き" if not walk else "ふつう", step=t * 1.4 if walk else 0.0)], t=t,
                    grade=EVE, tg=[(h_, "？", fade(t, T * 0.55), PINK)])
    if k == 9:   # ありがとう 3：僕のアップ
        h_ = HEAD(60, FY, 60)
        z = ease(u)
        c1, t1, _ = aim(h_, -1, 28, 0.1, 2, 46)
        c2, t2, _ = aim(h_, -1, 22, 0.0, 2, 46)
        return shot("street", lerp(c1, c2, z), lerp(t1, t2, z), 46, [me(60, 60, f=-1, face="驚き")], t=t, grade=EVE, vign=0.5,
                    tg=[(h_, "ありがとう 3", fade(t, 0.2, 0.3), PINK)])
    if k == 10:  # 1200回に、3回：僕の肩ごしに母さん。2つの数字をならべる
        cam = (BX + 10, FY + 34, BZ - 14 + 2 * u); tgt = (MX - 2, FY + 22, MZ)
        img = shoot("kitchen", cam, tgt, 50, [mom(MX, MZ), me(BX, BZ)], t=t, grade=EVE, vign=0.4)
        return fixed_tags(img, [(H * 0.255, "母さん：お弁当 1200", 1.0, GOLD), (H * 0.325, "僕：ありがとう 3", fade(t, 0.4), PINK)])
    if k == 11:  # その夜：空のお弁当箱を持って、母さんの前へ
        c_, uu = cut(t, T, [0.5])
        dr = [mom(MX, MZ), me(BX, BZ + 4, arms="front"), held_bento(BX, BZ + 4, 1, empty=True)]
        if c_ == 0:
            cam = (MX + 30, FY + 36, MZ + 12 - 2 * uu); tgt = (BX, FY + 22, BZ + 4)
            return shot("kitchen", cam, tgt, 50, dr, t=t, grade=EVE)
        cam = (BX + 2 * uu, FY + 30, BZ + 14); tgt = (BX, FY + 20, BZ + 24)
        return shot("kitchen", cam, tgt, 46, dr, t=t, grade=EVE)
    if k == 12:  # いつも、ありがとう：僕のアップ（母さんの肩ごし）
        h_ = HEAD(BX, FY, BZ + 4)
        cam, tgt, fov = aim(h_, 1, 22 - 2 * u, 0.2, 2, 46)
        return shot("kitchen", cam, tgt, fov, [me(BX, BZ + 4, face="決意", arms="front"), held_bento(BX, BZ + 4, 1, empty=True)], t=t, grade=EVE)
    if k == 13:  # 3 → 4
        h_ = HEAD(BX, FY, BZ + 4)
        cam, tgt, fov = aim(h_, 1, 26, -0.1, 2, 46)
        v = "4" if t > T * 0.35 else "3"
        return shot("kitchen", cam, tgt, fov, [me(BX, BZ + 4, face="笑顔" if v == "4" else "決意")], t=t, grade=EVE,
                    tg=[(h_, "ありがとう " + v, 1.0, GOLD if v == "4" else PINK)])
    if k == 14:  # 母さんは少しだけ笑っていた
        z = ease(u)
        c1, t1, _ = aim(mh, -1, 28, 0.2, 2, 46)
        c2, t2, _ = aim(mh, -1, 20, 0.05, 1, 44)
        return shot("kitchen", lerp(c1, c2, z), lerp(t1, t2, z), 46, [mom(MX, MZ, face="笑顔")], t=t, grade=EVE, vign=0.4)
    if k == 15:  # あなたは？：夜の通り、たくさんの数字。上へ引いていく
        dr, hd = crowd(16, 7, 34, 86, 10, 130, t)
        mine = me(60, 60, f=-1)
        z = ease(u)
        c1, t1, _ = aim(HEAD(60, FY, 60), -1, 34, 0.0, 6, 52)
        cam = lerp(c1, (80, FY + 60, 60 - 60), z); tgt = lerp(t1, (60, FY, 80), z)
        img = shoot("night", cam, tgt, 52, dr + [mine], t=t,
                    tg=[(p, s, 1.0, 0.45, CYAN) for p, s in hd])
        return tags2(img, cam, tgt, 52, [(HEAD(60, FY, 60), "あなたは？", fade(t, T * 0.4), GOLD)])


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
        os.makedirs('clips_bento', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips_bento/{k + 1:02d}.mp4')
