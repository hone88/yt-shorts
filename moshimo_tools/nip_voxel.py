"""25本目「もしも、男に乳首がなかったら？」（台本 20261128）。もしも系・図で見せる回。
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
_est = [3.0, 4.6, 4.0, 4.6, 3.6, 5.0, 4.2, 4.0, 2.0]
CLIPS = [max(2.6, round(x * 1.27 * 1.15, 1)) for x in _est]
BV.SV.CLIPS = CLIPS
HX, HMZ, HBZ = BV.HX, BV.HMZ, BV.HBZ
NAVY = (15, 23, 42)
CY0, CY1 = 780, 1225          # カードを置く高さ（見出しと字幕の間）


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


def shirt(d, cx, cy, s, a, dots=1.0, cross=0.0):
    """シャツの記号（線だけ）＋胸の2つの点"""
    w = (255, 255, 255, int(255 * a))
    pts = [(cx - 0.5 * s, cy - 0.5 * s), (cx - 0.18 * s, cy - 0.62 * s), (cx, cy - 0.5 * s), (cx + 0.18 * s, cy - 0.62 * s),
           (cx + 0.5 * s, cy - 0.5 * s), (cx + 0.75 * s, cy - 0.15 * s), (cx + 0.55 * s, cy - 0.02 * s), (cx + 0.42 * s, cy - 0.18 * s),
           (cx + 0.42 * s, cy + 0.6 * s), (cx - 0.42 * s, cy + 0.6 * s), (cx - 0.42 * s, cy - 0.18 * s), (cx - 0.55 * s, cy - 0.02 * s),
           (cx - 0.75 * s, cy - 0.15 * s)]
    d.line(pts + [pts[0]], fill=w, width=8, joint="curve")
    if dots > 0.01:
        r = 0.06 * s
        for sx in (-1, 1):
            x, y = cx + sx * 0.2 * s, cy - 0.12 * s
            d.ellipse([x - r, y - r, x + r, y + r], fill=PINK + (int(255 * a * dots),))
    if cross > 0.01:
        L = 0.75 * s * cross
        d.line([(cx - L, cy - L), (cx + L, cy + L)], fill=(255, 90, 90, int(255 * a)), width=14)


def ruler(d, a, show_pink=1.0, show_cyan=0.0, arrow=0.0):
    """妊娠0〜10週のものさし"""
    x0, x1, y = 140, W - 140, CY0 + 270
    wx = lambda wk: x0 + (x1 - x0) * wk / 10
    f = font(40); fb = font(54)
    d.text((W / 2, CY0 + 45), "おなかの中の週", font=f, fill=(200, 210, 225, int(255 * a)), anchor="mm")
    d.line([(x0, y), (x1, y)], fill=(255, 255, 255, int(255 * a)), width=8)
    for wk in range(0, 11):
        d.line([(wx(wk), y - 14), (wx(wk), y + 14)], fill=(255, 255, 255, int(200 * a)), width=4)
        if wk % 2 == 0 or wk in (7, 9):
            d.text((wx(wk), y + 46), f"{wk}", font=f, fill=(200, 210, 225, int(255 * a)), anchor="mm")
    if show_pink > 0.01:
        p = show_pink
        d.rounded_rectangle([wx(4), y - 26, wx(4) + (wx(6) - wx(4)) * p, y + 26], radius=12, fill=PINK + (int(230 * a),))
        d.text(((wx(4) + wx(6)) / 2, y - 80), "乳首の元", font=fb, fill=PINK + (int(255 * a * p),), anchor="mm")
    if show_cyan > 0.01:
        q = show_cyan
        d.line([(wx(7), y - 135), (wx(7), y + 26)], fill=CYAN + (int(255 * a * q),), width=10)
        d.text((wx(7) + 40, y - 170), "男女の分かれ道", font=fb, fill=CYAN + (int(255 * a * q),), anchor="mm")
    if arrow > 0.01:
        d.text((W / 2, CY1 - 50), "分かれる前に、もうできていた", font=fb, fill=GOLD + (int(255 * a * arrow),), anchor="mm")


def blueprint(d, a, n=1, plus=0.0):
    """設計図（方眼の紙）。n=2 で男女の2枚、plus で「消す仕組み +1」"""
    f = font(48)
    xs = [W / 2] if n == 1 else [W / 2 - 200, W / 2 + 200]
    for i, cx in enumerate(xs):
        x0, y0, x1, y1 = cx - 150, CY0 + 50, cx + 150, CY0 + 270
        d.rectangle([x0, y0, x1, y1], fill=(30, 64, 120, int(240 * a)), outline=(180, 210, 255, int(255 * a)), width=5)
        for g in range(1, 6):
            gx = x0 + (x1 - x0) * g / 6; gy = y0 + (y1 - y0) * g / 6
            d.line([(gx, y0), (gx, y1)], fill=(120, 160, 220, int(120 * a)), width=2)
            d.line([(x0, gy), (x1, gy)], fill=(120, 160, 220, int(120 * a)), width=2)
        shirt(d, cx, (y0 + y1) / 2 + 10, 150, a)
        if n == 2:
            d.text((cx, y1 + 40), "男" if i == 0 else "女", font=f, fill=(255, 255, 255, int(255 * a)), anchor="mm")
    if plus > 0.01:
        d.rounded_rectangle([W / 2 - 280, CY1 - 92, W / 2 + 280, CY1 - 18], radius=30, fill=(255, 90, 90, int(220 * a * plus)))
        d.text((W / 2, CY1 - 55), "男だけ「消す仕組み」＋1", font=f, fill=(255, 255, 255, int(255 * a * plus)), anchor="mm")


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
    for (x, y, text, col) in [(lx, ly, "消す手間", (255, 120, 120)), (rx, ry, "困らない", (120, 230, 160))]:
        d.line([(x, y), (x, y + 70)], fill=w, width=4)
        d.rounded_rectangle([x - 130, y + 70, x + 130, y + 150], radius=24, fill=col + (int(235 * a),))
        d.text((x, y + 110), text, font=f, fill=NAVY + (int(255 * a),), anchor="mm")


def frame(k, t):
    T = CLIPS[k]; u = t / T; z = ease(u)
    bh = HEAD(HX + 4, FY, HBZ)
    c1, t1, _ = aim(bh, 1, 30, 0.25, 4, 48); c2, t2, _ = aim(bh, 1, 24, 0.05, 2, 46)
    base = lambda face="ふつう", tg=(): shot("home", lerp(c1, c2, z), lerp(t1, t2, z), 46, [me(HX + 4, HBZ, f=1, face=face)], t=t, tg=tg)
    if k == 0:   # 男にも、乳首がある。使わないのに、なぜ？
        img = base("ふつう", [(bh, "？", fade(t, T * 0.55), GOLD)])
        return card(img, lambda d, a: shirt(d, W / 2, CY0 + 225, 270, a), fade(t, 0.1, 0.3))
    if k == 1:   # もしも、なかったら？ → 体が早くから「男だ」と知っている必要
        img = base("驚き")
        dots = 1 - fade(t, 0.6, 0.6); cr = fade(t, 0.9, 0.4) * (1 - fade(t, T * 0.62, 0.3))
        def dr(d, a):
            shirt(d, W / 2, CY0 + 180, 220, a, dots=max(dots, fade(t, T * 0.62, 0.3)), cross=cr)
            if t > T * 0.62:
                d.text((W / 2, CY1 - 45), "体が先に「男だ」と知っていれば…", font=font(48), fill=GOLD + (int(255 * a * fade(t, T * 0.62)),), anchor="mm")
        return card(img, dr, 1.0)
    if k == 2:   # 乳首の元は 4〜6週
        img = base("ふつう")
        return card(img, lambda d, a: ruler(d, a, show_pink=ease(fade(t, 0.5, 1.2))), fade(t, 0.0, 0.3))
    if k == 3:   # 7週ごろ 男女の分かれ道
        img = base("驚き")
        return card(img, lambda d, a: ruler(d, a, 1.0, ease(fade(t, 0.4, 0.8))), 1.0)
    if k == 4:   # 分かれる前に、もうできていた
        img = base("驚き", [(bh, "！", fade(t, 0.2), GOLD)])
        return card(img, lambda d, a: ruler(d, a, 1.0, 1.0, ease(fade(t, 0.3, 0.6))), 1.0)
    if k == 5:   # 男だけ消すなら、消す仕組みがもう1つ要る
        img = base("ふつう")
        n = 1 if t < T * 0.3 else 2
        return card(img, lambda d, a: blueprint(d, a, n, ease(fade(t, T * 0.45, 0.5))), fade(t, 0.0, 0.3))
    if k == 6:   # 困らないものは、残る
        img = base("ふつう")
        tilt = 10 * ease(fade(t, 0.5, 1.2))
        def dr(d, a):
            scale_card(d, a, tilt)
            if t > T * 0.55:
                d.text((W / 2, CY1 - 45), "困らないものは、消されずに残る", font=font(50), fill=GOLD + (int(255 * a * fade(t, T * 0.55)),), anchor="mm")
        return card(img, dr, fade(t, 0.0, 0.3))
    if k == 7:   # あなたも：生まれる前、体のつくりは男女同じだった
        dr_, hd = crowd(16, 7, 34, 86, 10, 130, t)
        mine = me(60, 60, f=-1)
        c1_, t1_, _ = aim(HEAD(60, FY, 60), -1, 34, 0.0, 6, 52)
        cam = lerp(c1_, (80, FY + 60, 0), z); tgt = lerp(t1_, (60, FY, 80), z)
        img = shoot("night", cam, tgt, 52, dr_ + [mine], t=t, tg=[(p, "同じ設計図", 1.0, 0.45, CYAN) for p, s in hd])
        return tags2(img, cam, tgt, 52, [(HEAD(60, FY, 60), "あなたも", fade(t, T * 0.3), GOLD)])
    if k == 8:   # 次は、どんなもしもがいい？
        return base("笑顔", [(bh, "次のもしもは？", fade(t, 0.2), GOLD)])


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
        os.makedirs('clips_nip', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips_nip/{k + 1:02d}.mp4')
