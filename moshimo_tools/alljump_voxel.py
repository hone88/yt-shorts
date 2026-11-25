"""27本目「もしも、地球の全員が同時にジャンプしたら？」（台本 20261130）。もしも系・図で見せる回。
体は描かない：服を着た「僕」＋図のカード（シャツの記号・週のものさし・設計図）。
事実：乳首の元は妊娠4〜6週、男女の分かれ道（SRY）は7週ごろ、テストステロンは9週ごろ（UNSW 2019 / Live Science）。
使い方: python3 nip_voxel.py stills k:t,... out.png / python3 nip_voxel.py 0,1,2"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bento_voxel as BV
from bento_voxel import me, tags2, fixed_tags, shot, fade, HEAD, aim, shoot, crowd, FY, GOLD, CYAN, PINK, font
from voxel import ease, f32
from kaguya2_voxel import lerp
import elevator_voxel as _EVX

W, H, FPS = BV.W, BV.H, BV.FPS
_est = [3.6, 2.6, 4.2, 5.6, 5.4, 3.8, 4.2, 2.4]
CLIPS = [max(2.6, round(x * 1.27 * 1.15, 1)) for x in _est]
BV.SV.CLIPS = CLIPS
BX, BZ = BV.BX, BV.BZ
import story_voxel as SVX
NAVY = (15, 23, 42)
CY0, CY1 = 830, 1262          # カードを置く高さ（見出しと字幕の間）


def _im(img):
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert("RGBA")


def _back(im):
    return np.asarray(im.convert("RGB")).astype(f32) / 255


def card(img, draw_fn, a=1.0):
    if a <= 0.01:
        return img
    im = _im(img)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([70, CY0, W - 70, CY1], radius=40, fill=NAVY + (int(215 * a),), outline=(255, 255, 255, int(60 * a)), width=4)
    draw_fn(d, a)
    return _back(Image.alpha_composite(im, lay))




def jumpers(t, jump):
    rg = np.random.default_rng(11)
    shirts = [(0.85, 0.35, 0.3), (0.3, 0.5, 0.85), (0.95, 0.85, 0.4), (0.4, 0.4, 0.45), (0.9, 0.9, 0.9), (0.55, 0.35, 0.6)]
    dr = []
    for i in range(34):
        P = {"髪": [(0.1, 0.08, 0.07), (0.35, 0.22, 0.12), (0.55, 0.5, 0.48)][int(rg.integers(0, 3))], "服": shirts[int(rg.integers(0, 6))],
             "服2": (0.9, 0.9, 0.9), "下": [(0.2, 0.25, 0.4), (0.3, 0.3, 0.32), (0.45, 0.35, 0.25)][int(rg.integers(0, 3))], "靴": (0.25, 0.25, 0.28)}
        cx = int(rg.integers(18, 106)); cz = int(rg.integers(70, 175))
        dr.append(SVX.H_(cx=cx, fy=FY + int(round(jump)), cz=cz, P=P, f=-1, step=0.0))
    return dr


def bignum(d, a, top, num, unit="", col=GOLD):
    d.text((W / 2, CY0 + 90), top, font=font(46), fill=(200, 210, 225, int(255 * a)), anchor="mm")
    d.text((W / 2, CY0 + 240), num, font=font(130), fill=col + (int(255 * a),), anchor="mm")
    if unit:
        d.text((W / 2, CY0 + 360), unit, font=font(46), fill=(255, 255, 255, int(255 * a)), anchor="mm")


def atom(d, a, u):
    """原子と、地球が動く距離"""
    cx, cy = W / 2 - 160, CY0 + 215
    R = 130
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(140, 200, 255, int(255 * a)), width=6)
    d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=(255, 120, 120, int(255 * a)))
    ang = 6.28 * u * 2
    ex, ey = cx + R * math.cos(ang), cy + R * math.sin(ang)
    d.ellipse([ex - 10, ey - 10, ex + 10, ey + 10], fill=CYAN + (int(255 * a),))
    d.text((cx, cy + R + 40), "原子1個", font=font(40), fill=(200, 210, 225, int(255 * a)), anchor="mm")
    b = fade(u, 0.35, 0.15)
    d.line([(cx + R + 60, cy), (cx + R + 61, cy)], fill=GOLD + (int(255 * a * b),), width=6)
    d.text((W / 2 + 230, cy - 20), "約2500分の1", font=font(64), fill=GOLD + (int(255 * a * b),), anchor="mm")
    d.text((W / 2 + 230, cy + 50), "地球が動く距離", font=font(40), fill=(255, 255, 255, int(255 * a * b)), anchor="mm")


def scale_card(d, a, tilt):
    """てんびん：「消す手間」と「困らない」"""
    f = font(50); cx, cy = W / 2, CY0 + 150
    ang = math.radians(tilt)
    L = 300
    lx, ly = cx - L * math.cos(ang), cy - L * math.sin(ang)
    rx, ry = cx + L * math.cos(ang), cy + L * math.sin(ang)
    w = (255, 255, 255, int(255 * a))
    d.line([(cx, cy), (cx, cy + 150)], fill=w, width=10)
    d.line([(lx, ly), (rx, ry)], fill=w, width=10)
    d.polygon([(cx - 60, cy + 170), (cx + 60, cy + 170), (cx, cy + 120)], fill=w)
    for (x, y, text, col) in [(lx, ly, "82億人", (255, 200, 120)), (rx, ry, "地球", (120, 200, 255))]:
        d.line([(x, y), (x, y + 70)], fill=w, width=4)
        d.rounded_rectangle([x - 130, y + 70, x + 130, y + 150], radius=24, fill=col + (int(235 * a),))
        d.text((x, y + 110), text, font=f, fill=NAVY + (int(255 * a),), anchor="mm")



def frame(k, t):
    T = CLIPS[k]; u = t / T; z = ease(u)
    bh = HEAD(BX, FY, BZ)
    c1, t1, _ = aim(bh, 1, 30, 0.25, 4, 48); c2, t2, _ = aim(bh, 1, 24, 0.05, 2, 46)
    def base(face="ふつう", tg=()):
        return shot("kitchen", lerp(c1, c2, z), lerp(t1, t2, z), 46, [me(BX, BZ, f=1, face=face)], t=t, tg=tg)
    def crowdshot(jumpfn):
        cam = (62 + 10 * math.sin(0.3 * t), FY + 66, 6 - 4 * z); tgt = (62, FY + 8, 115)
        return shoot("street", cam, tgt, 56, jumpers(t, jumpfn(t)), t=t)
    if k == 0:   # 全員で同時にジャンプ
        img = crowdshot(lambda t: 6 * max(0.0, math.sin(min(1, max(0, (t - 1.0) / 1.2)) * math.pi)))
        return img
    if k == 1:   # 約82億人
        return card(crowdshot(lambda t: 0), lambda d, a: bignum(d, a, "世界の人口", "約82億人"), fade(t, 0.1, 0.3))
    if k == 2:   # 全員で約5000億kg
        return card(base("ふつう"), lambda d, a: bignum(d, a, "1人60キロとすると、全員で", "約5000億kg"), fade(t, 0.1, 0.3))
    if k == 3:   # 地球は約60垓トン、12兆倍
        def dr(d, a):
            scale_card(d, a, 12 * ease(fade(t, 0.3, 1.0)))
        return card(base("驚き"), dr, 1.0)
    if k == 4:   # 50cm跳ぶと、地球は反対に少しだけ動く
        return card(base("ふつう"), lambda d, a: bignum(d, a, "全員が50センチ跳ぶと、地球は", "反対に", "ほんの少しだけ動く"), 1.0)
    if k == 5:   # 原子1個の約2500分の1
        return card(base("驚き", [(bh, "！", fade(t, 0.3), GOLD)]), lambda d, a: atom(d, a, u), 1.0)
    if k == 6:   # びくともしない
        img = crowdshot(lambda t: 6 * abs(math.sin(t * 2.2)))
        return card(img, lambda d, a: bignum(d, a, "82億人で跳んでも", "びくともしない"), fade(t, 0.6, 0.3))
    if k == 7:
        return base("笑顔", [(bh, "？", fade(t, 0.2), GOLD)])


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
            ims.append(Image.fromarray((np.clip(frame(int(k), float(t)), 0, 1) * 255).astype(np.uint8)).resize((270, 480)))
        cols = min(5, len(ims))
        sheet = Image.new('RGB', (270 * cols, 480 * ((len(ims) + cols - 1) // cols)))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % cols) * 270, (i // cols) * 480))
        sheet.save(sys.argv[3])
    else:
        os.makedirs('clips_all', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips_all/{k + 1:02d}.mp4')
