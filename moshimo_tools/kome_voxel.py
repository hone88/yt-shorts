"""26本目「もしも、お米が100倍の大きさだったら？」（台本 20261129）。勝手にPR系：SANPO（広島市西区庚午北・天然酵母の米粉ベーグル）。
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
_est = [3.7, 5.0, 3.0, 6.7, 3.2, 3.2, 4.5, 7.7, 4.0, 3.8]
CLIPS = [max(2.6, round(x * 1.27 * 1.15, 1)) for x in _est]
BV.SV.CLIPS = CLIPS
BX, BZ = BV.BX, BV.BZ
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



RICE = (250, 248, 240)
BROWN = (196, 140, 80)


def grain(d, cx, cy, L, a, ang=0.0):
    """お米1粒（白い楕円＋胚芽のくぼみ）"""
    w = L * 0.62
    d.ellipse([cx - L / 2, cy - w / 2, cx + L / 2, cy + w / 2], fill=RICE + (int(255 * a),), outline=(200, 195, 180, int(255 * a)), width=max(2, int(L * 0.03)))
    r = w * 0.16
    d.ellipse([cx - L / 2 + r * 0.6, cy - r, cx - L / 2 + r * 2.6, cy + r], fill=(225, 215, 190, int(255 * a)))


def c_big(d, a, u):
    """5mm の1粒が 50cm に"""
    f = font(52); fb = font(70)
    grain(d, 230, CY0 + 200, 40, a)
    d.text((230, CY0 + 290), "5ミリ", font=f, fill=(255, 255, 255, int(255 * a)), anchor="mm")
    L = 40 + 360 * ease(min(1, u * 1.6))
    grain(d, 660, CY0 + 200, L, a)
    if u > 0.45:
        b = fade(u, 0.45, 0.15)
        d.text((660, CY0 + 350), "50センチ／約22キロ", font=fb, fill=GOLD + (int(255 * a * b),), anchor="mm")


def c_bowls(d, a, u):
    """お茶碗が 320 杯ならぶ"""
    n = int(320 * ease(min(1, u * 1.4)))
    cols, s = 20, 38
    x0 = W / 2 - cols * s / 2 + s / 2; y0 = CY0 + 50
    for i in range(n):
        x = x0 + (i % cols) * s; y = y0 + (i // cols) * 18
        d.pieslice([x - 15, y - 12, x + 15, y + 18], 0, 180, fill=(235, 235, 240, int(255 * a)))
        d.ellipse([x - 12, y - 6, x + 12, y + 6], fill=RICE + (int(255 * a),))
    d.text((W / 2, CY1 - 55), f"お茶碗 約{n}杯", font=font(66), fill=GOLD + (int(255 * a),), anchor="mm")


def c_time(d, a, u):
    """しみこむ時間：30分 と 約200日"""
    f = font(48); x0 = 140; x1 = W - 140
    d.text((x0, CY0 + 70), "ふつうの1粒", font=f, fill=(255, 255, 255, int(255 * a)), anchor="lm")
    d.rounded_rectangle([x0, CY0 + 110, x0 + 18, CY0 + 160], radius=8, fill=CYAN + (int(255 * a),))
    d.text((x0 + 40, CY0 + 135), "約30分", font=f, fill=CYAN + (int(255 * a),), anchor="lm")
    if u > 0.35:
        b = ease(min(1, (u - 0.35) / 0.45))
        d.text((x0, CY0 + 230), "100倍の1粒（1万倍の時間）", font=f, fill=(255, 255, 255, int(255 * a)), anchor="lm")
        d.rounded_rectangle([x0, CY0 + 270, x0 + (x1 - x0) * b, CY0 + 320], radius=8, fill=GOLD + (int(255 * a),))
        if b > 0.95:
            d.text((x1, CY0 + 370), "約200日", font=font(64), fill=GOLD + (int(255 * a),), anchor="rm")


def c_halfyear(d, a, u):
    grain(d, 330, CY0 + 215, 330, a)
    cx, cy, r = 760, CY0 + 215, 120
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, int(255 * a)), width=10)
    ang = math.radians(-90 + 360 * 6 * u)
    d.line([(cx, cy), (cx + 0.8 * r * math.cos(ang), cy + 0.8 * r * math.sin(ang))], fill=GOLD + (int(255 * a),), width=10)
    d.text((cx, cy + r + 50), "半年以上", font=font(56), fill=GOLD + (int(255 * a),), anchor="mm")


def c_powder(d, a, u):
    """大きな1粒 → くだけて粉に"""
    z = ease(min(1, u * 1.3))
    if z < 0.5:
        grain(d, W / 2, CY0 + 215, 330 * (1 - z), a)
    import random
    rnd = random.Random(3)
    n = int(260 * z)
    for i in range(n):
        x = W / 2 + rnd.gauss(0, 160) * z; y = CY0 + 215 + rnd.gauss(0, 70) * z + 60 * z
        r = rnd.uniform(3, 8)
        d.ellipse([x - r, y - r, x + r, y + r], fill=RICE + (int(255 * a),))
    if u > 0.5:
        d.text((W / 2, CY1 - 50), "米粉", font=font(64), fill=GOLD + (int(255 * a * fade(u, 0.5, 0.15)),), anchor="mm")


def c_bagel(d, a, u):
    cx, cy, R, r = W / 2, CY0 + 200, 150, 52
    d.ellipse([cx - R, cy - R * 0.8, cx + R, cy + R * 0.8], fill=BROWN + (int(255 * a),))
    d.ellipse([cx - R + 14, cy - R * 0.8 + 10, cx + R - 14, cy + R * 0.8 - 22], fill=(214, 164, 104, int(255 * a)))
    d.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], fill=NAVY + (int(255 * a),))
    f = font(58)
    if u > 0.25:
        d.text((cx - 300, cy + 10), "外はカリッ", font=f, fill=(255, 255, 255, int(255 * a * fade(u, 0.25, 0.1))), anchor="mm")
    if u > 0.55:
        d.text((cx + 300, cy + 10), "中はもっちり", font=f, fill=GOLD + (int(255 * a * fade(u, 0.55, 0.1)),), anchor="mm")
    d.text((cx, CY1 - 45), "お米の粉で焼いたベーグル", font=font(46), fill=(200, 210, 225, int(255 * a)), anchor="mm")


def c_shop(d, a, u):
    f = font(46); fb = font(96)
    d.text((W / 2, CY0 + 70), "広島市西区・庚午北", font=f, fill=(200, 210, 225, int(255 * a)), anchor="mm")
    d.text((W / 2, CY0 + 175), "SANPO", font=fb, fill=GOLD + (int(255 * a),), anchor="mm")
    items = ["有機栽培コシヒカリの米粉", "天然酵母のベーグル"]
    for i, s in enumerate(items):
        b = fade(u, 0.3 + 0.2 * i, 0.12)
        d.text((W / 2, CY0 + 285 + 62 * i), s, font=f, fill=(255, 255, 255, int(255 * a * b)), anchor="mm")


def c_days(d, a, u):
    f = font(58)
    days = ["月", "火", "水", "木", "金", "土", "日"]; on = {"火", "水", "金"}
    s = 120; x0 = W / 2 - 3 * s
    for i, dd in enumerate(days):
        x = x0 + i * s; y = CY0 + 170
        col = GOLD if dd in on else (90, 100, 120)
        d.rounded_rectangle([x - 48, y - 48, x + 48, y + 48], radius=20, fill=col + (int(235 * a),))
        d.text((x, y), dd, font=f, fill=NAVY + (int(255 * a),), anchor="mm")
    d.text((W / 2, CY0 + 320), "12時から", font=font(62), fill=(255, 255, 255, int(255 * a)), anchor="mm")


def frame(k, t):
    T = CLIPS[k]; u = t / T; z = ease(u)
    bh = HEAD(BX, FY, BZ)
    c1, t1, _ = aim(bh, 1, 30, 0.25, 4, 48); c2, t2, _ = aim(bh, 1, 24, 0.05, 2, 46)
    def base(face="ふつう", tg=(), where="kitchen", grade=None):
        kw = {"grade": grade} if grade is not None else {}
        return shot(where, lerp(c1, c2, z), lerp(t1, t2, z), 46, [me(BX, BZ, f=1, face=face)], t=t, tg=tg, **kw)
    if k == 0:
        img = base("ふつう", [(bh, "？", fade(t, T * 0.5), GOLD)])
        return card(img, lambda d, a: (grain(d, W / 2 - 120, CY0 + 215, 160, a), d.text((W / 2 + 150, CY0 + 215), "×100", font=font(110), fill=GOLD + (int(255 * a),), anchor="mm")), fade(t, 0.1, 0.3))
    if k == 1:
        return card(base("驚き"), lambda d, a: c_big(d, a, u), 1.0)
    if k == 2:
        return card(base("驚き", [(bh, "！", fade(t, 0.3), GOLD)]), lambda d, a: c_bowls(d, a, u), 1.0)
    if k == 3:
        return card(base("ふつう"), lambda d, a: c_time(d, a, u), 1.0)
    if k == 4:
        return card(base("驚き"), lambda d, a: c_halfyear(d, a, u), 1.0)
    if k == 5:
        return card(base("決意", [(bh, "？", fade(t, 0.3), GOLD)]), lambda d, a: c_powder(d, a, u), 1.0)
    if k == 6:
        return card(base("笑顔"), lambda d, a: c_bagel(d, a, u), 1.0)
    if k == 7:
        return card(base("笑顔"), lambda d, a: c_shop(d, a, u), 1.0)
    if k == 8:
        return card(base("笑顔"), lambda d, a: (grain(d, 260, CY0 + 215, 200, a), d.text((W / 2 + 40, CY0 + 215), "→", font=font(110), fill=(255, 255, 255, int(255 * a)), anchor="mm"), c_bagel_small(d, a)), 1.0)
    if k == 9:
        return card(base("笑顔", [(bh, "？", fade(t, T * 0.5), GOLD)]), lambda d, a: c_days(d, a, u), 1.0)


def c_bagel_small(d, a):
    cx, cy, R, r = 800, CY0 + 215, 110, 38
    d.ellipse([cx - R, cy - R * 0.8, cx + R, cy + R * 0.8], fill=BROWN + (int(255 * a),))
    d.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], fill=NAVY + (int(255 * a),))


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
        os.makedirs('clips_kome', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips_kome/{k + 1:02d}.mp4')
