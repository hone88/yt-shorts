"""28本目「もしも、心臓が打てる回数が決まっていたら？」（台本 20261201）。感動系・1話完結。
11/26 の反省（人物＋カードの使い回しで場面が変わらない）から、1場面ごとに場所かカメラを変える。
登場人物はオリジナル：僕（白シャツ・紺ズボン）、母さん（ベージュの服・ピンクのエプロン）、あの子（紺の服・おだんご）。
使い方: python3 heart_voxel.py stills k:t,... out.png / python3 heart_voxel.py 0,2,4"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bento_voxel as BV
from bento_voxel import me, mom, tags2, fixed_tags, shot, fade, H_, HEAD, aim, shoot, crowd, FY, GOLD, CYAN, PINK, EVE, SEPIA
from voxel import ease
from kaguya2_voxel import cut, lerp

W, H, FPS = BV.W, BV.H, BV.FPS
_est = [4.3, 2.5, 4.3, 3.2, 5.6, 2.2, 3.8, 3.2, 4.1, 2.8]
CLIPS = [max(2.6, round(x * 1.27 * 1.15, 1)) for x in _est]
BV.SV.CLIPS = CLIPS
P_GIRL = {"髪": (0.16, 0.1, 0.08), "服": (0.18, 0.22, 0.42), "服2": (0.95, 0.95, 0.96), "下": (0.18, 0.22, 0.42), "靴": (0.3, 0.2, 0.15)}
NIGHT = (0.7, 0.78, 1.1)
RED = (240, 70, 90)
MX, MZ = BV.MX, BV.MZ
BX, BZ = BV.BX, BV.BZ
HX, HMZ, HBZ = BV.HX, BV.HMZ, BV.HBZ


def girl(cx, cz, f=-1, face="笑顔", **kw):
    return H_(cx=cx, fy=FY, cz=cz, P=P_GIRL, face=face, f=f, bun=True, **kw)


def beat(t, bpm=70):
    """どくん、の強さ 0〜1"""
    ph = (t * bpm / 60.0) % 1.0
    return math.exp(-ph * 9) + 0.6 * math.exp(-max(0, ph - 0.18) * 12) * (ph > 0.18)


def count_txt(n):
    return f"{n:,}回"


def frame(k, t):
    T = CLIPS[k]; u = t / T
    if k == 0:   # もしも：昼の通り。人ごみの上から → 僕の顔へ
        dr, _ = crowd(14, 3, 34, 86, 10, 130, t)
        h = HEAD(60, FY, 60)
        c_, uu = cut(t, T, [0.45])
        if c_ == 0:
            cam = lerp((90, FY + 70, 0), (75, FY + 50, 20), ease(uu)); tgt = (60, FY + 10, 70)
            return shoot("street", cam, tgt, 54, dr + [me(60, 60, f=-1)], t=t)
        cam, tgt, fov = aim(h, -1, 26 - 4 * uu, 0.25, 2, 46)
        return shot("street", cam, tgt, fov, [me(60, 60, f=-1, face="驚き")], t=t, tg=[(h, "心臓の回数 ？", fade(uu * T * 0.55, 0.15, 0.3), GOLD)])
    if k == 1:   # 一生 約30億回：真下から見上げる → 胸の前に数字
        h = HEAD(60, FY, 60)
        c_, uu = cut(t, T, [0.4])
        if c_ == 0:
            cam = (60, FY + 6, 60 - 30 + 4 * uu); tgt = (60, FY + 30, 60)
            return shoot("street", cam, tgt, 54, [me(60, 60, f=-1)], t=t, sh=0.15 * beat(t))
        cam, tgt, fov = aim(h, -1, 30 - 3 * uu, -0.5, 4, 48)
        return shot("street", cam, tgt, fov, [me(60, 60, f=-1)], t=t, tg=[(h, "一生 約30億回", fade(uu * T * 0.6, 0.05, 0.25), RED)])
    if k == 2:   # 1日 約10万回：夜の部屋。数字がへっていく → 窓の外の夜
        h = HEAD(40, FY, 40)
        n = 3_000_000_000 - int(100_000 * t / T)
        c_, uu = cut(t, T, [0.5])
        if c_ == 0:
            cam, tgt, fov = aim(h, -1, 36, 0.3 + 0.2 * uu, 10, 56, 0.3)
            return shoot("room1", cam, tgt, fov, [me(40, 40, f=-1)], t=t, grade=NIGHT, vign=0.5)
        cam, tgt, fov = aim(h, -1, 22, -0.7, 2, 48, 0.28)
        img = shoot("room1", cam, tgt, fov, [me(40, 40, f=-1, face="ふつう")], t=t, grade=NIGHT, vign=0.6)
        return fixed_tags(img, [(H * 0.28, "残り " + count_txt(n), 1.0, RED)])
    if k == 3:   # ドキドキ：駅前。あの子の笑顔 → 僕の顔（ゆれる）
        c_, uu = cut(t, T, [0.45])
        if c_ == 0:
            gh = HEAD(56, FY, 82)
            cam, tgt, fov = aim(gh, -1, 26 - 3 * uu, 0.3, 2, 46)
            return shoot("station", cam, tgt, fov, [girl(56, 82, arms="wave")], t=t)
        bh = HEAD(66, FY, 60)
        cam, tgt, fov = aim(bh, 1, 22 - 2 * uu, -0.3, 2, 46)
        return shot("station", cam, tgt, fov, [me(66, 60, f=1, face="驚き")], t=t, sh=0.5 * beat(t, 140),
                    tg=[(bh, "ドキドキ ＋", fade(uu * T * 0.55, 0.05, 0.2), PINK)])
    if k == 4:   # 計算：帰りの電車。2つの数字 → 窓の外
        sh_ = HEAD(60, FY, 8, sit=True)
        c_, uu = cut(t, T, [0.55])
        if c_ == 0:
            cam, tgt, fov = aim(sh_, 1, 26 - 3 * uu, 0.6, 4, 52, 0.32)
            return shoot("train", cam, tgt, fov, [me(60, 8, f=1, sit=True)], t=t)
        cam, tgt, fov = aim(sh_, 1, 30, 1.2, 2, 50, 0.3)
        return shoot("train", cam, tgt, fov, [me(60, 8, f=1, sit=True, face="笑顔")], t=t)
    if k == 5:   # 最初の1回は？：夕方の通り。歩いて、立ち止まる
        zz = int(30 + 5 * min(t, T * 0.6))
        walk = t < T * 0.6
        h = HEAD(60, FY, zz)
        c_, uu = cut(t, T, [0.5])
        if c_ == 0:
            cam, tgt, fov = aim(h, -1, 30, 0.0, 4, 52, 0.3)
            return shoot("street", cam, tgt, fov, [me(60, zz, f=1, step=t * 1.4 if walk else 0.0)], t=t, grade=EVE)
        cam, tgt, fov = aim(h, 1, 26, 1.0, 1, 48, 0.3)
        return shot("street", cam, tgt, fov, [me(60, zz, f=1, face="驚き")], t=t, grade=EVE, tg=[(h, "最初の1回 ？", fade(uu * T * 0.5, 0.05, 0.25), GOLD)])
    if k == 6:   # 答え：セピアの台所。若いころの母さん → 寄る
        mh = HEAD(MX, FY, MZ)
        c_, uu = cut(t, T, [0.45])
        if c_ == 0:
            cam, tgt, fov = aim(mh, -1, 44, 0.35, 6, 52, 0.3)
            return shoot("kitchen", cam, tgt, fov, [mom(MX, MZ, face="笑顔", arms="front")], t=t, grade=SEPIA, vign=0.6)
        z = ease(uu)
        c1, t1, _ = aim(mh, -1, 30, 0.1, 2, 46); c2, t2, _ = aim(mh, -1, 24, 0.0, 2, 46)
        return shoot("kitchen", lerp(c1, c2, z), lerp(t1, t2, z), 46, [mom(MX, MZ, face="笑顔", arms="front")], t=t, grade=SEPIA, vign=0.6)
    if k == 7:   # そのとき：セピアの玄関。どくん、どくん（画面がふるえ、赤い光がにじむ）
        mh = HEAD(HX, FY + 4, HMZ)
        b = beat(t)
        c_, uu = cut(t, T, [0.5])
        if c_ == 0:
            cam = (HX + 26, FY + 36, HBZ - 14 + 3 * uu); tgt = (HX - 2, FY + 26, HMZ)
        else:
            cam, tgt, fov0 = aim(mh, -1, 26 - 3 * uu, -0.25, 2, 46)
        g = (SEPIA[0] * (1 + 0.12 * b), SEPIA[1], SEPIA[2])
        img = shoot("home", cam, tgt, 48 if c_ == 0 else 46, [mom(HX, HMZ, fy=FY + 4, face="笑顔")], t=t, grade=g, vign=0.6 + 0.2 * b, sh=0.25 * b)
        return fixed_tags(img, [(H * 0.28, "どくん", min(1.0, b * 1.3), RED)])
    if k == 8:   # お母さんの心臓の音：今の台所（夕方）。僕の肩ごし → 母さんの笑顔
        mh = HEAD(MX, FY, MZ)
        c_, uu = cut(t, T, [0.45])
        if c_ == 0:
            cam = (BX + 10, FY + 34, BZ - 14 + 2 * uu); tgt = (MX - 2, FY + 22, MZ)
            return shot("kitchen", cam, tgt, 50, [mom(MX, MZ), me(BX, BZ)], t=t, grade=EVE, vign=0.4)
        z = ease(uu)
        c1, t1, _ = aim(mh, -1, 28, 0.2, 2, 46); c2, t2, _ = aim(mh, -1, 20, 0.05, 1, 44)
        return shoot("kitchen", lerp(c1, c2, z), lerp(t1, t2, z), 46, [mom(MX, MZ, face="笑顔")], t=t, grade=EVE, vign=0.4)
    if k == 9:   # 誰に使う？：夜の通り。僕から一気に上へ引く
        dr, _ = crowd(6, 5, 30, 50, 10, 130, t); dr2, _ = crowd(6, 9, 70, 90, 10, 130, t); dr = dr + dr2
        z = ease(u)
        c1, t1, _ = aim(HEAD(60, FY, 60), -1, 22, 0.15, 10, 52)
        cam = lerp(c1, (80, FY + 64, 0), z); tgt = lerp(t1, (60, FY, 80), z)
        return shoot("night", cam, tgt, 52, dr + [me(60, 60, f=-1, face="笑顔")], t=t)


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
        cols = min(8, len(ims))
        sheet = Image.new('RGB', (180 * cols, 320 * ((len(ims) + cols - 1) // cols)))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % cols) * 180, (i // cols) * 320))
        sheet.save(sys.argv[3])
    else:
        os.makedirs('clips_heart', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips_heart/{k + 1:02d}.mp4')
