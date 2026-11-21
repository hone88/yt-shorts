"""物語回3「もしも、父さんの頭の上に数字が見えたら？」（台本 20261127）。お弁当の回（bento_voxel）の続き。
登場人物はオリジナル：僕（白シャツ・紺ズボン）、父さん（紺のスーツ・白シャツ・短髪）。
使い方: python3 tousan_voxel.py stills k:t,... out.png / python3 tousan_voxel.py 0,2,4"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bento_voxel as BV
from bento_voxel import me, tags2, fixed_tags, shot, fade, H_, HEAD, aim, shoot, crowd, FY, GOLD, CYAN, PINK, EVE, SEPIA
from voxel import ease, C
from kaguya2_voxel import cut, lerp
import elevator_voxel as _EVX

W, H, FPS = BV.W, BV.H, BV.FPS
_est = [2.9, 3.8, 1.9, 5.8, 3.0, 3.0, 1.2, 3.0, 2.9, 1.8, 1.9, 1.2, 1.2, 3.2, 1.4, 2.7]
CLIPS = [max(2.6, round(x * 1.27 * 1.15, 1)) for x in _est]
BV.SV.CLIPS = CLIPS
P_DAD = {"髪": (0.08, 0.07, 0.07), "服": (0.16, 0.2, 0.34), "服2": (0.92, 0.92, 0.94), "下": (0.16, 0.19, 0.32), "靴": (0.1, 0.08, 0.08)}
HX, HMZ, HBZ = BV.HX, BV.HMZ, BV.HBZ
NIGHT = (0.78, 0.82, 1.05)


def dad(cx, cz, f=-1, face="ふつう", fy=FY, **kw):
    return H_(cx=cx, fy=fy, cz=cz, P=P_DAD, face=face, f=f, **kw)


def frame(k, t):
    T = CLIPS[k]; u = t / T
    dh = HEAD(HX, FY + 4, HMZ)          # 玄関の父さん
    if k == 0:   # もしも：玄関の父さん。頭の上に ？？？
        z = ease(u)
        c1, t1, _ = aim(dh, -1, 34, 0.25, 4, 48); c2, t2, _ = aim(dh, -1, 26, 0.05, 2, 46)
        return shot("home", lerp(c1, c2, z), lerp(t1, t2, z), 46, [dad(HX, HMZ, fy=FY + 4)], t=t, tg=[(dh, "？？？", fade(t, 0.8), GOLD)])
    if k == 1:   # ある朝：僕のうしろ姿ごしに、出かける父さん
        cam = (HX + 26, FY + 36, HBZ - 14 + 2 * u); tgt = (HX - 2, FY + 26, HMZ)
        return shot("home", cam, tgt, 48, [dad(HX, HMZ, fy=FY + 4), me(HX + 4, HBZ, f=1)], t=t, tg=[(dh, "？", fade(t, T * 0.6), GOLD)])
    if k == 2:   # 仕事に行った日 約5000
        z = ease(u)
        c1, t1, _ = aim(dh, -1, 30, 0.1, 2, 46); c2, t2, _ = aim(dh, -1, 24, 0.0, 2, 46)
        return shot("home", lerp(c1, c2, z), lerp(t1, t2, z), 46, [dad(HX, HMZ, fy=FY + 4)], t=t,
                    tg=[(dh, "仕事に行った日 約5000", fade(t, 0.1, 0.3), GOLD)])
    if k == 3:   # 20年×約250日：セピアの玄関で、毎朝出ていく父さん（コマ送り）
        n = int(t * 3)
        face = ["ふつう", "決意", "ふつう"][n % 3]
        cam = (HX + 10 + 6 * math.sin(n), FY + 34, HBZ - 6); tgt = (HX, FY + 22, HMZ)
        img = shoot("home", cam, tgt, 48, [dad(HX + (n % 3) * 3 - 3, HMZ, fy=FY + 4, face=face)], t=t, grade=SEPIA, vign=0.5)
        return fixed_tags(img, [(H * 0.29, f"{min(5000, int(5000 * ease(min(1, u * 1.2)))):,}日", 1.0, GOLD)])
    if k in (4, 5):   # 帰り道（夕方）：前を歩く父さんの背中 → ため息 約3000
        zz = 70 - 4 * t
        h_ = HEAD(60, FY, zz)
        if k == 4:
            cam = (60 + 6, FY + 32, zz + 44 - 2 * u); tgt = (60, FY + 20, zz)
            return shot("street", cam, tgt, 48, [dad(60, int(zz), f=-1, step=t * 1.4)], t=t, grade=EVE)
        cam, tgt, fov = aim(h_, 1, 28 - 3 * u, 0.6, 3, 46)
        return shot("street", cam, tgt, fov, [dad(60, int(zz), f=-1, step=t * 1.4)], t=t, grade=EVE, vign=0.4,
                    tg=[(h_, "ため息 約3000", fade(t, 0.2, 0.3), CYAN)])
    if k == 6:   # 知らなかった：立ち止まる僕
        h_ = HEAD(60, FY, 40)
        cam, tgt, fov = aim(h_, -1, 22 - 2 * u, 0.2, 2, 46)
        return shot("street", cam, tgt, fov, [me(60, 40, f=-1, face="驚き")], t=t, grade=EVE)
    if k in (7, 8):   # 自分の頭の上にも → 今年 話した時間 約3時間
        h_ = HEAD(60, FY, 40)
        z = ease(u)
        c1, t1, _ = aim(h_, -1, 30, 0.1, 2, 46); c2, t2, _ = aim(h_, -1, 22, 0.0, 2, 46)
        tg = [(h_, "？", fade(t, T * 0.5), PINK)] if k == 7 else [(h_, "今年 話した時間 約3時間", fade(t, 0.2, 0.3), PINK)]
        return shot("street", lerp(c1, c2, z), lerp(t1, t2, z), 46, [me(60, 40, f=-1, face="驚き")], t=t, grade=EVE, vign=0.4, tg=tg)
    if k == 9:   # 5000日に、3時間
        cam = (60 + 30, FY + 32, 40 - 18 - 2 * u); tgt = (60, FY + 20, 52)
        img = shoot("street", cam, tgt, 50, [me(60, 40, f=1), dad(60, 64, f=-1)], t=t, grade=EVE, vign=0.4)
        return fixed_tags(img, [(H * 0.255, "父さん：仕事に行った日 5000", 1.0, GOLD), (H * 0.325, "僕：話した時間 3時間", fade(t, 0.4), PINK)])
    if k == 10:   # その夜：玄関のドアが開く。帰ってくる父さん
        cam = (HX + 26, FY + 36, HBZ - 12 + 2 * u); tgt = (HX - 2, FY + 26, HMZ)
        return shot("home", cam, tgt, 48, [dad(HX, HMZ + 6 - int(6 * ease(u)), fy=FY + 4, step=t * 1.2), me(HX + 4, HBZ, f=1)], t=t, grade=NIGHT)
    if k == 11:   # おかえり：僕のアップ
        bh = HEAD(HX + 4, FY, HBZ)
        cam, tgt, fov = aim(bh, 1, 22 - 2 * u, 0.3, 2, 46)
        return shot("home", cam, tgt, fov, [me(HX + 4, HBZ, f=1, face="決意")], t=t, grade=NIGHT)
    if k in (12, 13, 14):   # ……おう → 新しい数字 → うれしかった 1
        z = ease(u)
        c1, t1, _ = aim(dh, -1, 28, 0.15, 2, 46); c2, t2, _ = aim(dh, -1, 22 if k < 14 else 18, 0.05, 1, 44)
        tg = []
        if k == 13:
            tg = [(dh, "？", fade(t, T * 0.5), GOLD)]
        if k == 14:
            tg = [(dh, "うれしかった 1", fade(t, 0.1, 0.3), GOLD)]
        return shot("home", lerp(c1, c2, z), lerp(t1, t2, z), 46, [dad(HX, HMZ, fy=FY + 4, face="笑顔" if k == 14 else "ふつう")], t=t,
                    grade=NIGHT, vign=0.4, tg=tg)
    if k == 15:   # あなたは？：夜の通り、たくさんの数字。上へ引いていく
        dr, hd = crowd(16, 7, 34, 86, 10, 130, t)
        mine = me(60, 60, f=-1)
        z = ease(u)
        c1, t1, _ = aim(HEAD(60, FY, 60), -1, 34, 0.0, 6, 52)
        cam = lerp(c1, (80, FY + 60, 60 - 60), z); tgt = lerp(t1, (60, FY, 80), z)
        img = shoot("night", cam, tgt, 52, dr + [mine], t=t, tg=[(p, s, 1.0, 0.45, CYAN) for p, s in hd])
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
            ims.append(Image.fromarray((np.clip(frame(int(k), float(t)), 0, 1) * 255).astype(np.uint8)).resize((180, 320)))
        cols = min(8, len(ims))
        sheet = Image.new('RGB', (180 * cols, 320 * ((len(ims) + cols - 1) // cols)))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % cols) * 180, (i // cols) * 320))
        sheet.save(sys.argv[3])
    else:
        os.makedirs('clips_tousan', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips_tousan/{k + 1:02d}.mp4')
