import numpy as np, math, sys, subprocess, os
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SS = 1080, 1920, 30, 2
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'
FBD = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
GROUND = 1240
TEXT_Y = 560
SUB_Y = 1560
YEL = (255, 212, 59)
NAVY = (10, 20, 48)
_fc = {}


def font(path, size):
    k = (path, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, size, index=0)
    return _fc[k]


def cl(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = cl(x); return 0.5 - 0.5 * math.cos(math.pi * x)


def lerp(a, b, t):
    return a + (b - a) * t


def mul(c, k):
    return tuple(int(cl(v * k, 0, 255)) for v in c)


def mix(a, b, t):
    return tuple(int(lerp(x, y, t)) for x, y in zip(a, b))


# ------------------------------------------------------------------ camera / primitives
class Cam:
    def __init__(s, cx=540.0, cy=960.0, z=1.0):
        s.cx, s.cy, s.z = cx, cy, z

    def P(s, x, y):
        return ((x - s.cx) * s.z + 540) * SS, ((y - s.cy) * s.z + 960) * SS

    def L(s, v):
        return v * s.z * SS

    def layer(s, k):
        return Cam(540 + (s.cx - 540) * k, 960 + (s.cy - 960) * k, s.z)


def seg(d, cam, a, b, w, col):
    pa, pb = cam.P(*a), cam.P(*b)
    wd = max(1.0, cam.L(w))
    d.line([pa, pb], fill=col, width=int(round(wd)))
    r = wd / 2
    for p in (pa, pb):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)


def circ(d, cam, c, r, col):
    p = cam.P(*c); rr = cam.L(r)
    d.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], fill=col)


def rect(d, cam, x0, y0, x1, y1, col):
    a = cam.P(x0, y0); b = cam.P(x1, y1)
    d.rectangle([a[0], a[1], b[0], b[1]], fill=col)


def poly(d, cam, pts, col):
    d.polygon([cam.P(*p) for p in pts], fill=col)


def dotted(d, cam, pts, r, col, gap=26):
    acc = 0.0
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        L = math.hypot(x1 - x0, y1 - y0)
        while acc <= L:
            t = acc / L if L else 0
            circ(d, cam, (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t), r, col)
            acc += gap
        acc -= L


def label(d, cam, x, y, txt, size, col, anchor='mm', stroke=None):
    p = cam.P(x, y)
    f = font(FB, int(size * SS * cam.z))
    d.text(p, txt, font=f, fill=col, anchor=anchor, stroke_width=int(size * SS * cam.z * 0.09) if stroke else 0, stroke_fill=stroke)


# ------------------------------------------------------------------ person
SKIN = (241, 199, 163); HAIR = (40, 28, 22); SHIRT = (255, 138, 61); PANTS = (110, 132, 210)
SHOE = (248, 248, 250); SOLE = (70, 74, 90)
KEYS = ['lt_f', 'lk_f', 'lt_b', 'lk_b', 'at_f', 'ae_f', 'at_b', 'ae_b', 'lean']


def pblend(a, b, t):
    return {k: lerp(a[k], b[k], t) for k in KEYS}


def P_(lt_f, lk_f, lt_b, lk_b, at_f, ae_f, at_b, ae_b, lean=0.0):
    return dict(zip(KEYS, [lt_f, lk_f, lt_b, lk_b, at_f, ae_f, at_b, ae_b, lean]))


def walk_pose(phi):
    def leg(p):
        return 0.42 * math.sin(p), 0.1 + 0.7 * max(0.0, math.cos(p))
    a, b = leg(phi), leg(phi + math.pi)
    return P_(a[0], a[1], b[0], b[1], -0.38 * math.sin(phi), 0.35, 0.38 * math.sin(phi), 0.35, 0.06)


STAND = P_(0.06, 0.04, -0.05, 0.04, 0.12, 0.2, -0.1, 0.2, 0.0)
CROUCH = P_(1.15, 1.9, 1.05, 1.8, -0.9, 0.3, -1.0, 0.3, 0.45)
LEAP = P_(0.08, 0.06, -0.12, 0.15, 2.9, 0.1, 2.75, 0.1, -0.02)
FALL = P_(0.45, 0.7, 0.1, 0.35, 2.3, 0.4, 2.6, 0.3, -0.05)
FLOAT_ARMS = dict(at_f=0.9, ae_f=0.5, at_b=0.6, ae_b=0.5)


def limb(base, a1, a2, l1, l2):
    j = (base[0] + l1 * math.sin(a1), base[1] + l1 * math.cos(a1))
    e = (j[0] + l2 * math.sin(a2), j[1] + l2 * math.cos(a2))
    return j, e


def dims(s):
    Hh = 600 * s
    return dict(H=Hh, th=0.26 * Hh, sh=0.25 * Hh, tor=0.30 * Hh, ua=0.17 * Hh, fa=0.16 * Hh, hr=0.075 * Hh)


def foot_depth(s, pose):
    D = dims(s)
    ys = []
    for side in ('f', 'b'):
        ta, ka = pose['lt_' + side], pose['lk_' + side]
        _, e = limb((0, 0), ta, ta - ka, D['th'], D['sh'])
        ys.append(e[1])
    return max(ys) + 0.054 * D['H']


def person(d, cam, hx, hy, s, pose, tint=None):
    D = dims(s); Hh = D['H']
    C = (lambda c, k=1.0: mul(c, k)) if tint is None else (lambda c, k=1.0: tint)
    lean = pose['lean']
    sh = (hx + D['tor'] * math.sin(lean), hy - D['tor'] * math.cos(lean))
    hand = {}

    def arm(side, k):
        a, e = pose['at_' + side], pose['ae_' + side]
        j, h = limb(sh, a, a + e, D['ua'], D['fa'])
        seg(d, cam, sh, j, 0.075 * Hh, C(SHIRT, k)); seg(d, cam, j, h, 0.062 * Hh, C(SKIN, k))
        circ(d, cam, h, 0.04 * Hh, C(SKIN, k))
        hand[side] = h

    def leg(side, k):
        ta, ka = pose['lt_' + side], pose['lk_' + side]
        j, e = limb((hx, hy), ta, ta - ka, D['th'], D['sh'])
        seg(d, cam, (hx, hy), j, 0.11 * Hh, C(PANTS, k)); seg(d, cam, j, e, 0.095 * Hh, C(PANTS, k))
        ax, ay = e
        seg(d, cam, (ax - 0.025 * Hh, ay + 0.022 * Hh), (ax + 0.085 * Hh, ay + 0.026 * Hh), 0.058 * Hh, C(SHOE, k))
        seg(d, cam, (ax - 0.045 * Hh, ay + 0.047 * Hh), (ax + 0.112 * Hh, ay + 0.047 * Hh), 0.016 * Hh, C(SOLE, k))

    arm('b', 0.72); leg('b', 0.75)
    seg(d, cam, (hx, hy), sh, 0.165 * Hh, C(SHIRT))
    leg('f', 1.0)
    nk = (sh[0] + 0.02 * Hh * math.sin(lean), sh[1] - 0.03 * Hh)
    hc = (nk[0] + 0.012 * Hh + (D['hr'] + 0.01 * Hh) * math.sin(lean), nk[1] - (D['hr'] + 0.01 * Hh) * math.cos(lean))
    seg(d, cam, sh, nk, 0.06 * Hh, C(SKIN))
    circ(d, cam, hc, D['hr'], C(HAIR))
    circ(d, cam, (hc[0] + 0.016 * Hh, hc[1] + 0.012 * Hh), D['hr'] * 0.86, C(SKIN))
    circ(d, cam, (hc[0] - 0.012 * Hh, hc[1] - 0.03 * Hh), D['hr'] * 0.7, C(HAIR))
    if tint is None:
        circ(d, cam, (hc[0] + 0.05 * Hh, hc[1] - 0.004 * Hh), 0.009 * Hh, (30, 30, 40))
    arm('f', 1.0)
    return hand


# ------------------------------------------------------------------ backgrounds
def make_sky(top=(7, 13, 36), bot=(30, 52, 108), stars=True):
    y = np.linspace(0, 1, H * SS)[:, None, None]
    g = (np.array(top)[None, None] * (1 - y) + np.array(bot)[None, None] * y)
    img = np.broadcast_to(g, (H * SS, W * SS, 3)).astype(np.float32).copy()
    if stars:
        rg = np.random.default_rng(3)
        n = 260
        ys = rg.integers(0, int(H * SS * 0.55), n); xs = rg.integers(0, W * SS, n)
        b = rg.random(n) ** 3 * 170 + 40
        for xx, yy, bb in zip(xs, ys, b):
            img[yy:yy + 3, xx:xx + 3] += bb
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


SKY = None


def gen_buildings(seed, period, hmin, hmax, wmin, wmax):
    rg = np.random.default_rng(seed); out = []; x = 0
    while x < period - 40:
        w = int(rg.integers(wmin, wmax))
        w = min(w, period - x)
        out.append((x, w, int(rg.integers(hmin, hmax)), int(rg.integers(0, 10 ** 6)), float(rg.uniform(0.85, 1.12))))
        x += w + int(rg.integers(4, 18))
    return out


FAR = gen_buildings(5, 364, 520, 900, 70, 140)
NEAR = gen_buildings(6, 728, 380, 1700, 120, 230)


def h01(*a):
    v = 0
    for i, x in enumerate(a):
        v = (v * 1000003 + int(x) * (2654435761 + i * 97)) & 0xFFFFFFFF
        v ^= v >> 15
    return (v & 0xFFFF) / 65535.0


def draw_layer(d, cam, blds, period, base_col, windows):
    left = cam.cx - 540 / cam.z - 300; right = cam.cx + 540 / cam.z + 300
    k0 = int(math.floor(left / period)) - 1
    k = k0
    while k * period < right:
        for (x, w, h, sd, sh) in blds:
            X = k * period + x
            if X + w < left or X > right: continue
            rect(d, cam, X, GROUND - h, X + w, GROUND + 2, mul(base_col, sh))
            if windows:
                cols = max(1, (w - 16) // 26)
                rows = (h - 30) // 38
                for c in range(cols):
                    for r in range(rows):
                        wx = X + 12 + c * 26; wy = GROUND - h + 22 + r * 38
                        lit = h01(sd, c, r) < 0.18
                        col = (250, 214, 120) if lit else mul((48, 70, 128), sh)
                        rect(d, cam, wx, wy, wx + 14, wy + 20, col)
        k += 1


def street(d, cam, plaza=False):
    draw_layer(d, cam.layer(0.55), FAR, 364, (24, 38, 82), False)
    draw_layer(d, cam, NEAR, 728, (30, 48, 98), True)
    left = cam.cx - 540 / cam.z - 100; right = cam.cx + 540 / cam.z + 100
    if plaza:
        rect(d, cam, left, GROUND, right, GROUND + 1400, (54, 72, 130))
        for i in range(int(left // 110) - 1, int(right // 110) + 2):
            seg(d, cam, (i * 110, GROUND), (i * 110 + (i * 110 - 540) * 0.9, GROUND + 700), 3, (44, 60, 112))
        for j, yy in enumerate([GROUND + 40, GROUND + 100, GROUND + 180, GROUND + 290, GROUND + 440]):
            seg(d, cam, (left, yy), (right, yy), 3, (44, 60, 112))
        return
    rect(d, cam, left, GROUND, right, GROUND + 100, (56, 74, 134))
    for i in range(int(left // 91) - 1, int(right // 91) + 2):
        seg(d, cam, (i * 91, GROUND + 2), (i * 91, GROUND + 98), 3, (44, 60, 112))
    rect(d, cam, left, GROUND + 100, right, GROUND + 112, (100, 120, 182))
    rect(d, cam, left, GROUND + 112, right, GROUND + 1600, (22, 30, 64))
    for i in range(int(left // 160) - 1, int(right // 160) + 2):
        rect(d, cam, i * 160, GROUND + 330, i * 160 + 80, GROUND + 342, (200, 200, 212))
    # street lamps
    for i in range(int(left // 364) - 1, int(right // 364) + 2):
        x = i * 364 + 180
        rect(d, cam, x - 5, GROUND - 430, x + 5, GROUND + 80, (78, 98, 150))
        seg(d, cam, (x, GROUND - 430), (x - 46, GROUND - 440), 9, (78, 98, 150))
        circ(d, cam, (x - 50, GROUND - 428), 40, (60, 72, 120))
        circ(d, cam, (x - 50, GROUND - 428), 24, (150, 140, 120))
        circ(d, cam, (x - 50, GROUND - 428), 12, (255, 236, 170))


# ------------------------------------------------------------------ overlays
_tc = {}


def big_text(lines, size=126):
    key = (tuple(lines), size)
    if key in _tc: return _tc[key]
    f = font(FB, size); stroke = 12
    lh = int(size * 1.22)
    widths = []
    for ln in lines:
        w = 0
        for seg_, yel in parse(ln): w += f.getlength(seg_)
        widths.append(w)
    Wt = int(max(widths) + stroke * 2 + 30); Ht = lh * len(lines) + stroke * 2 + 30
    img = Image.new('RGBA', (Wt, Ht), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        x = (Wt - widths[i]) / 2; y = 15 + stroke + i * lh
        for seg_, yel in parse(ln):
            d.text((x + 6, y + 8), seg_, font=f, fill=(0, 0, 20, 150), stroke_width=stroke, stroke_fill=(0, 0, 20, 150))
            d.text((x, y), seg_, font=f, fill=YEL if yel else (255, 255, 255), stroke_width=stroke, stroke_fill=NAVY)
            x += f.getlength(seg_)
    _tc[key] = img
    return img


def parse(ln):
    out = []; buf = ''; yel = False
    for ch in ln:
        if ch in '[]':
            if buf: out.append((buf, yel))
            buf = ''; yel = ch == '['
        else:
            buf += ch
    if buf: out.append((buf, yel))
    return out


def sub_img(text):
    key = ('sub', text)
    if key in _tc: return _tc[key]
    f = font(FBD, 52); lines = text.split('\n')
    lh = 72; wmax = max(f.getlength(l) for l in lines)
    Wt = int(wmax + 70); Ht = lh * len(lines) + 34
    img = Image.new('RGBA', (Wt, Ht), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, Wt - 1, Ht - 1], radius=22, fill=(0, 6, 22, 170))
    for i, l in enumerate(lines):
        d.text((Wt / 2, 17 + lh * i + lh / 2), l, font=f, fill=(255, 255, 255), anchor='mm', stroke_width=4, stroke_fill=(0, 0, 0))
    _tc[key] = img
    return img


def badge_img(text):
    key = ('badge', text)
    if key in _tc: return _tc[key]
    f = font(FB, 60)
    w = int(f.getlength(text)) + 64; h = 100
    img = Image.new('RGBA', (w + 8, h + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([6, 8, w + 6, h + 6], radius=26, fill=(0, 0, 20, 110))
    d.rounded_rectangle([0, 0, w, h], radius=26, fill=YEL)
    d.text((w / 2, h / 2 + 2), text, font=f, fill=NAVY, anchor='mm')
    _tc[key] = img
    return img


def paste_center(base, im, cx, cy, scale=1.0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    base.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


# ------------------------------------------------------------------ script
SCENES = [
    dict(t0=0, t1=2, badge='0.0秒', big=['重力が', '[1秒]消える'],
         subs=[(0, 2, '重力が、1秒だけ消えた。')]),
    dict(t0=2, t1=5, badge='0.1秒', big=['宇宙に飛ぶ？', '→[ほぼ浮かない]'],
         subs=[(2, 3.5, '人は宇宙に飛ばされる？'), (3.5, 5, '……いいえ、ほとんど浮きません。')]),
    dict(t0=5, t1=11, badge='0.3秒', big=['浮くのは', 'たった[2cm]'],
         subs=[(5, 8, '地球は秒速460mで回っているのに、'), (8, 11, '1秒で地面から離れるのは、\nたった2cm。')]),
    dict(t0=11, t1=17, badge='0.5秒', big=['ジャンプが', '止まらない'],
         subs=[(11, 14, 'ジャンプ中の人は、落ちてこない。'), (14, 17, '蹴った勢いのまま、上へ上へ。')]),
    dict(t0=17, t1=23, badge='0.8秒', big=['噴水が[空へ]'],
         subs=[(17, 20, '投げたボールも、噴水の水も、'), (20, 23, 'まっすぐ空へ。')]),
    dict(t0=23, t1=28, badge='1.0秒', big=['重力が戻る'],
         subs=[(23, 25.2, 'そして1秒後、重力が戻る。'), (25.2, 28, 'ジャンプしていた人は、\nいつもより高いところから落ちてくる。')]),
    dict(t0=28, t1=30, badge='？', big=['もし', '戻らなかったら[？]'],
         subs=[(28, 30, '……もし、戻ってこなかったら？')]),
]


# ------------------------------------------------------------------ shots
S1 = 0.6
_bt = np.linspace(0, 6, 1801)
_b = np.array([ease((t - 0.6) / 1.6) for t in _bt])
_phi = 2 * math.pi * np.concatenate([[0], np.cumsum((1 - _b[:-1]) * (_bt[1] - _bt[0]))])


def walk_state(t):
    """time since scene start (gravity vanishes at ~0.5s)"""
    b = float(np.interp(t, _bt, _b)); phi = float(np.interp(t, _bt, _phi)) + 0.6
    pose = walk_pose(phi)
    for k, v in FLOAT_ARMS.items():
        pose[k] = lerp(pose[k], v, b * 0.8)
    lift = 5.0 * ease((t - 0.6) / 1.8)
    x = 540 + 364 * t
    hy = GROUND - foot_depth(S1, pose) - lift
    return x, hy, pose


DUST = [(float(a), float(b), float(c)) for a, b, c in zip(np.random.default_rng(1).uniform(0, 4000, 90), np.random.default_rng(2).uniform(-10, 95, 90), np.random.default_rng(4).uniform(0.6, 1.6, 90))]


def dust(d, cam, tg):
    if tg < 0.5: return
    for x, y, k in DUST:
        circ(d, cam, (x, GROUND + y - 22 * (tg - 0.5) * k), 3.2, (200, 212, 245))


def shot_walk(d, t, extra=None):
    x, hy, pose = walk_state(t)
    cam = Cam(x, 960, 1.0)
    street(d, cam); dust(d, cam, t)
    person(d, cam, x, hy, S1, pose)
    return cam


def scene_frame(t):
    """t global seconds -> 2x RGB image, plus post fx dict"""
    img = SKY.copy(); d = ImageDraw.Draw(img); fx = {}
    if t < 2 or t >= 28:
        lt = t if t < 2 else t - 28
        shot_walk(d, lt)
        if 0.42 < lt < 0.62: fx['glitch'] = 1 - abs(lt - 0.52) / 0.1
    elif t < 5:
        lt = t - 2; tg = t
        x, hy, pose = walk_state(tg)
        zp = ease((lt - 0.9) / 2.0)
        cam = Cam(x + 20 * zp, lerp(960, GROUND - 70, zp), lerp(1.0, 3.2, zp))
        street(d, cam); dust(d, cam, tg)
        if lt < 1.5:
            gy = hy - 3000 * max(0.0, lt - 0.05) ** 2
            a = cl(1 - (lt - 0.9) / 0.6)
            gl = Image.new('RGB', img.size, (0, 0, 0)); gd = ImageDraw.Draw(gl)
            mask = Image.new('L', img.size, 0); md = ImageDraw.Draw(mask)
            dotted(md, cam, [(x + 30, hy - 120), (x + 30, gy - 260)], 7, int(200 * a), 34)
            person(gd, cam, x + 30, gy, S1, pblend(pose, LEAP, 0.7), tint=(150, 200, 255))
            person(md, cam, x + 30, gy, S1, pblend(pose, LEAP, 0.7), tint=int(150 * a))
            gl.paste((150, 200, 255), (0, 0), mask) if False else None
            col = Image.new('RGB', img.size, (150, 200, 255))
            img.paste(col, (0, 0), mask)
            d = ImageDraw.Draw(img)
            if lt > 0.45:
                k = cl((lt - 0.45) / 0.12)
                cx, cy = x + 30, 560
                r = 95 * (1.4 - 0.4 * k)
                ca = mix((30, 30, 60), (255, 70, 70), a)
                seg(d, Cam(cam.cx, cam.cy, 1.0), (cx - r, cy - r), (cx + r, cy + r), 34, ca)
                seg(d, Cam(cam.cx, cam.cy, 1.0), (cx - r, cy + r), (cx + r, cy - r), 34, ca)
        person(d, cam, x, hy, S1, pose)
    elif t < 8:
        lt = t - 5
        z = lerp(1.0, 1.75, ease(lt / 3.0))
        cam = Cam(540, lerp(960, 1010, ease(lt / 3.0)), z)
        earth(img, cam, (540, 1600), 560, lt)
        d = ImageDraw.Draw(img)
        R = 610
        pts = [(540 + R * math.cos(math.radians(a)), 1600 - R * math.sin(math.radians(a))) for a in np.linspace(150, 42, 40)]
        for i in range(len(pts) - 1):
            seg(d, cam, pts[i], pts[i + 1], 20, YEL)
        ex, ey = pts[-1]; a = math.radians(42)
        tx, ty = math.sin(a), math.cos(a)  # tangent (clockwise)
        nx, ny = math.cos(a), -math.sin(a)
        poly(d, cam, [(ex + tx * 50, ey + ty * 50), (ex - nx * 34, ey - ny * 34), (ex + nx * 34, ey + ny * 34)], YEL)
        label(d, cam, 760, 1120, '秒速460m', 38, YEL, stroke=NAVY)
        pz = 1600 - 560
        ps = 0.16
        pp = STAND
        person(d, cam, 540, pz - foot_depth(ps, pp), ps, pp)
        k = cl((lt - 0.6) / 1.2)
        if k > 0:
            dotted(d, cam, [(560, pz - 2), (560 + 380 * k, pz - 2)], 4.5, (235, 240, 255), 16)
            if k > 0.95:
                poly(d, cam, [(950, pz - 2), (930, pz - 14), (930, pz + 10)], (235, 240, 255))
    elif t < 11:
        lt = t - 8
        x = 540
        pose = P_(0.22, 0.05, -0.2, 0.05, 0.6, 0.4, 0.4, 0.4, 0.0)
        gapcm = 2.0 * ease(lt / 2.0)
        px_cm = 600 * S1 / 170
        hy = GROUND - foot_depth(S1, pose) - gapcm * px_cm
        z = lerp(6.5, 7.3, ease(lt / 3.0))
        cam = Cam(551, GROUND - 30, z)
        street(d, cam)
        rg = np.random.default_rng(9)
        for xx, yy in zip(rg.uniform(380, 760, 260), rg.uniform(GROUND + 2, GROUND + 60, 260)):
            circ(d, cam, (xx, yy), 0.6, (70, 90, 150))
        person(d, cam, x, hy, S1, pose)
        sole = GROUND - gapcm * px_cm
        bx = 551
        if gapcm > 0.15:
            seg(d, cam, (bx, sole), (bx, GROUND), 1.6, YEL)
            seg(d, cam, (bx - 8, sole), (bx + 8, sole), 1.6, YEL)
            seg(d, cam, (bx - 8, GROUND), (bx + 8, GROUND), 1.6, YEL)
        label(d, cam, bx, GROUND + 12, f'{gapcm:.1f}cm' if lt < 2.0 else '2cm', 12, YEL, stroke=NAVY)
        label(d, cam, bx + 34, GROUND + 13, '（1秒後）', 5, (235, 240, 255), stroke=NAVY)
    elif t < 17:
        lt = t - 11
        s = S1; x = 540
        if lt < 0.22: pose = STAND
        elif lt < 0.5: pose = pblend(STAND, CROUCH, ease((lt - 0.22) / 0.28))
        elif lt < 0.64: pose = pblend(CROUCH, LEAP, ease((lt - 0.5) / 0.14))
        else: pose = LEAP
        up = 0.0 if lt < 0.6 else 85.0 * (lt - 0.6) + 40 * ease((lt - 0.6) / 0.3)
        hy = GROUND - foot_depth(s, pose) - up
        hy0 = GROUND - foot_depth(s, LEAP)
        cy = 960 if lt < 3.0 else min(960, lerp(960, hy - 40, ease((lt - 3.0) / 1.2)))
        cam = Cam(540, cy, 1.0)
        street(d, cam)
        apex = hy0 - 124
        dotted(d, cam, [(100, apex - 230), (980, apex - 230)], 6, (200, 220, 255), 30)
        label(d, cam, 860, apex - 266, 'いつもの頂点', 40, (200, 220, 255), stroke=NAVY)
        if 0.6 < lt < 2.2:
            a = cl(1 - (lt - 1.6) / 0.6)
            mask = Image.new('L', img.size, 0); md = ImageDraw.Draw(mask)
            person(md, cam, x, apex, s, LEAP, tint=int(110 * a))
            img.paste(Image.new('RGB', img.size, (150, 200, 255)), (0, 0), mask); d = ImageDraw.Draw(img)
        if lt > 0.65:
            for i in range(4):
                yy = hy + 60 + i * 45
                seg(d, cam, (x - 70 + i * 40, yy), (x - 70 + i * 40, yy + 70), 3, (190, 210, 250))
        person(d, cam, x, hy, s, pose)
    elif t < 20:
        lt = t - 17
        s = S1
        cam = Cam(lerp(540, 600, ease(lt / 3)), lerp(960, 900, ease(lt / 3)), lerp(1.0, 1.08, ease(lt / 3)))
        street(d, cam)
        px = 300
        rel = 0.42
        k = ease(cl((lt - 0.05) / (rel - 0.05)))
        pose = dict(STAND); pose['at_f'] = lerp(-2.2, 2.3, k); pose['ae_f'] = lerp(0.6, 0.1, k); pose['lean'] = lerp(-0.12, 0.12, k)
        hy = GROUND - foot_depth(s, pose)
        hd = person(ImageDraw.Draw(Image.new('RGB', (8, 8))), Cam(-99999, 0), px, hy, s, pose)
        ang = math.radians(58); dx, dy = math.cos(ang), -math.sin(ang)
        rpt = person.__defaults__ and None
        p0 = (px + 0.0, 0)
        pose_r = dict(STAND); pose_r['at_f'] = lerp(-2.2, 2.3, 1.0); pose_r['ae_f'] = 0.1; pose_r['lean'] = 0.12
        hr_ = person(ImageDraw.Draw(Image.new('RGB', (8, 8))), Cam(-99999, 0), px, GROUND - foot_depth(s, pose_r), s, pose_r)['f']
        ghost = []
        v = 520
        for i in range(60):
            tt = i * 0.03
            ghost.append((hr_[0] + v * dx * tt, hr_[1] + v * dy * tt + 0.5 * 1100 * tt * tt))
        dotted(d, cam, [g for g in ghost if g[1] < GROUND + 10], 5, (150, 175, 230), 28)
        person(d, cam, px, hy, s, pose)
        if lt < rel:
            bp = hd['f']
        else:
            tt = lt - rel
            bp = (hr_[0] + v * dx * tt, hr_[1] + v * dy * tt)
            for j in range(1, 6):
                circ(d, cam, (bp[0] - dx * j * 18, bp[1] - dy * j * 18), 16 - 2.5 * j, (255, 190, 120))
        circ(d, cam, bp, 17, (255, 120, 60))
        circ(d, cam, (bp[0] - 5, bp[1] - 5), 6, (255, 200, 160))
    elif t < 23:
        lt = t - 20
        cam = Cam(540, lerp(980, 900, ease(lt / 3)), lerp(1.0, 0.92, ease(lt / 3)))
        street(d, cam, plaza=True)
        fountain(d, cam, lt + 3.0)
    else:
        lt = t - 23
        s = S1
        hy0 = GROUND - foot_depth(s, LEAP)
        upA = 85.0 * (6 - 0.6) + 40          # height reached at end of scene 4
        tf = 0.3                               # gravity returns
        if lt < tf:
            up = upA + 85 * lt; pose = LEAP
        else:
            dec = 1.3; up_dec = 85 * dec / 2
            if lt < tf + dec:
                tt = lt - tf; up = upA + 85 * tf + 85 * tt - 85 / (2 * dec) * tt * tt
            else:
                apexh = upA + 85 * tf + up_dec
                tt = lt - tf - dec
                land = 2.6
                acc = 2 * apexh / land ** 2
                up = max(0.0, apexh - 0.5 * acc * tt * tt)
            pose = pblend(LEAP, FALL, ease((lt - tf) / 1.2))
        landed = up <= 0 and lt > 2
        if landed:
            tl = lt - (tf + 1.3 + 2.6)
            pose = pblend(CROUCH, STAND, ease((tl - 0.15) / 0.6)) if tl > 0.15 else pblend(FALL, CROUCH, ease(tl / 0.15))
        hy = GROUND - foot_depth(s, pose) - up
        cy = min(960, hy - 40)
        cam = Cam(540, cy, 1.0)
        street(d, cam)
        apex = hy0 - 124
        dotted(d, cam, [(100, apex - 230), (980, apex - 230)], 6, (200, 220, 255), 30)
        label(d, cam, 860, apex - 266, 'いつもの頂点', 40, (200, 220, 255), stroke=NAVY)
        if lt > 1.8 and not landed:
            for i in range(4):
                yy = hy - 330 - i * 50
                seg(d, cam, (x_ := 470 + i * 45, yy), (x_, yy - 90), 3, (190, 210, 250))
        if landed:
            tl = lt - (tf + 1.3 + 2.6)
            for i in range(10):
                a = math.pi * (0.05 + 0.9 * i / 9)
                rr = 30 + 220 * ease(tl / 0.5)
                circ(d, cam, (540 + rr * math.cos(a) * (1 if i % 2 else -1), GROUND - 6 - 24 * math.sin(a) * ease(tl / 0.3)), 9 * (1 - cl(tl / 0.7)), (200, 212, 245))
        person(d, cam, 540, hy, s, pose)
        if tf - 0.02 < lt < tf + 0.35:
            fx['flash'] = 1 - (lt - tf) / 0.35
    return img, fx


# ------------------------------------------------------------------ earth
def vnoise(h, w, cell, octs, seed):
    rg = np.random.default_rng(seed)
    tot = np.zeros((h, w), np.float32); amp = 1.0; norm = 0.0
    for _ in range(octs):
        gh, gw = int(h / cell) + 3, int(w / cell) + 3
        g = rg.random((gh, gw)).astype(np.float32)
        g[:, -3:] = g[:, :3]
        im = Image.fromarray(g, 'F').resize((int(gw * cell), int(gh * cell)), Image.BICUBIC)
        tot += np.asarray(im)[:h, :w] * amp; norm += amp; amp *= 0.5; cell = max(1.0, cell / 2)
    return tot / norm


TEX = None


def earth(img, cam, c, r, lt):
    global TEX
    if TEX is None:
        n = vnoise(256, 512, 60, 5, 12)
        TEX = n > 0.53
    cx, cy = cam.P(*c); R = cam.L(r)
    x0, x1 = max(0, int(cx - R - 2)), min(W * SS, int(cx + R + 2))
    y0, y1 = max(0, int(cy - R - 2)), min(H * SS, int(cy + R + 2))
    if x1 <= x0 or y1 <= y0: return
    st = 2
    ys, xs = np.mgrid[y0:y1:st, x0:x1:st].astype(np.float32)
    u = (xs - cx) / R; v = (ys - cy) / R
    r2 = u * u + v * v
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    lat = np.arcsin(np.clip(-v, -1, 1)); lon = np.arctan2(u, z) - 0.32 * lt
    tu = ((lon / (2 * np.pi) + 0.5) * 512).astype(int) % 512
    tv = np.clip(((0.5 - lat / np.pi) * 256).astype(int), 0, 255)
    land = TEX[tv, tu]
    col = np.where(land[..., None], np.array([76, 175, 109], np.float32), np.array([47, 111, 214], np.float32))
    ice = np.abs(lat) > 1.25
    col[ice] = [235, 240, 250]
    shade = 0.55 + 0.45 * np.clip(-0.5 * u - 0.5 * v + 0.7 * z, 0, 1)
    col = col * shade[..., None]
    rim = np.clip(1 - z, 0, 1) ** 3
    col = col * (1 - rim[..., None] * 0.6) + np.array([120, 180, 255]) * rim[..., None] * 0.6
    a = np.clip((1 - np.sqrt(r2)) * R / st + 0.5, 0, 1)
    halo = np.exp(-np.maximum(np.sqrt(r2) - 1, 0) * R / 40) * (r2 >= 1) * 0.55
    rgba = np.concatenate([col, (a * 255)[..., None]], -1)
    hal = np.zeros_like(rgba); hal[..., :3] = [110, 170, 255]; hal[..., 3] = halo * 255
    top = Image.fromarray(np.clip(hal, 0, 255).astype(np.uint8), 'RGBA').resize((x1 - x0, y1 - y0), Image.BILINEAR)
    img.paste(top, (x0, y0), top)
    eimg = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), 'RGBA').resize((x1 - x0, y1 - y0), Image.BILINEAR)
    img.paste(eimg, (x0, y0), eimg)


# ------------------------------------------------------------------ fountain
def fountain(d, cam, tt):
    bx, by = 540, GROUND + 120
    # ghost (normal) arcs
    for ang in (-24, -12, 0, 12, 24):
        a = math.radians(ang)
        pts = []
        for i in range(80):
            s_ = i * 0.02
            x = bx + 560 * math.sin(a) * s_ * 1.0
            y = by - 120 - 900 * math.cos(a) * s_ + 0.5 * 1500 * s_ * s_
            if y > by - 60 and i > 5: break
            pts.append((x, y))
        dotted(d, cam, pts, 4, (120, 150, 210), 24)
    # basin back
    rect(d, cam, bx - 300, by - 120, bx + 300, by - 70, (90, 110, 170))
    rect(d, cam, bx - 300, by - 70, bx + 300, by + 30, (70, 90, 150))
    rect(d, cam, bx - 280, by - 118, bx + 280, by - 96, (90, 170, 230))
    rect(d, cam, bx - 30, by - 175, bx + 30, by - 115, (110, 130, 190))
    rect(d, cam, bx - 50, by - 185, bx + 50, by - 168, (130, 150, 210))
    rg = np.random.default_rng(21)
    for ang in (-24, -12, 0, 12, 24):
        a = math.radians(ang); dx, dy = math.sin(a), -math.cos(a)
        ox, oy = bx + dx * 30, by - 185
        for i in range(140):
            age = (tt * 1.0 + i * 0.045 + rg.random() * 0.02) % (140 * 0.045)
            p = (ox + dx * 520 * age + rg.normal() * 3, oy + dy * 520 * age)
            if p[1] < -3000: continue
            rr = 9 + rg.random() * 6
            circ(d, cam, p, rr, (170, 225, 255) if rg.random() < 0.6 else (120, 200, 250))


# ------------------------------------------------------------------ compose
def compose(t):
    img2, fx = scene_frame(t)
    im = img2.reduce(2).convert('RGB')
    sc = next(s for s in SCENES if s['t0'] <= t < s['t1'] or (s is SCENES[-1] and t >= s['t0']))
    lt = t - sc['t0']
    if fx.get('flash'):
        a = cl(fx['flash'])
        im = Image.blend(im, Image.new('RGB', im.size, (255, 255, 255)), 0.75 * a)
    if fx.get('glitch'):
        g = cl(fx['glitch']); arr = np.asarray(im).copy()
        sh = int(14 * g)
        arr[..., 0] = np.roll(arr[..., 0], sh, 1); arr[..., 2] = np.roll(arr[..., 2], -sh, 1)
        for y0 in (520, 1180, 1400):
            arr[y0:y0 + 60] = np.roll(arr[y0:y0 + 60], int(40 * g), 1)
        im = Image.fromarray(arr)
    big = big_text(sc['big'])
    pop = 0.86 + 0.14 * ease(lt / 0.16)
    paste_center(im, big, 540, TEXT_Y, pop)
    b = badge_img(sc['badge'])
    im.paste(b, (48, 120), b)
    for (a0, a1, txt) in sc['subs']:
        if a0 <= t < a1:
            paste_center(im, sub_img(txt), 540, SUB_Y)
    return im


def srt():
    def ts(x):
        ms = int(round(x * 1000)); h_, ms = divmod(ms, 3600000); m_, ms = divmod(ms, 60000); s_, ms = divmod(ms, 1000)
        return f'{h_:02d}:{m_:02d}:{s_:02d},{ms:03d}'
    out = []; i = 1
    for sc in SCENES:
        for a0, a1, txt in sc['subs']:
            out.append(f'{i}\n{ts(a0)} --> {ts(a1)}\n{txt}\n'); i += 1
    return '\n'.join(out)


def render_scene(k, out):
    sc = SCENES[k]
    f0, f1 = int(round(sc['t0'] * FPS)), int(round(sc['t1'] * FPS))
    tmp = out[:-4] + '.part.mp4'
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS), tmp], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        ff.stdin.write(compose(f / FPS).tobytes())
    ff.stdin.close()
    if ff.wait() == 0:
        os.replace(tmp, out)
        print('done', out, flush=True)



def clean_frame(t):
    img2, fx = scene_frame(t)
    im = img2.reduce(2).convert('RGB')
    if fx.get('flash'):
        im = Image.blend(im, Image.new('RGB', im.size, (255, 255, 255)), 0.75 * cl(fx['flash']))
    if fx.get('glitch'):
        g = cl(fx['glitch']); arr = np.asarray(im).copy(); sh = int(14 * g)
        arr[..., 0] = np.roll(arr[..., 0], sh, 1); arr[..., 2] = np.roll(arr[..., 2], -sh, 1)
        for y0 in (520, 1100, 1300):
            arr[y0:y0 + 60] = np.roll(arr[y0:y0 + 60], int(40 * g), 1)
        im = Image.fromarray(arr)
    return im

# (scene start, native length, output length, native-time mode)
CLIPS = [(0, 2, 2.2), (2, 3, 3.5), (5, 6, 9.9), (11, 6, 4.8), (17, 6, 3.7), (23, 5, 5.8), ('walk', 5.9, 5.9)]

def walk_long(lt):
    img = SKY.copy(); d = ImageDraw.Draw(img)
    shot_walk(d, lt)
    fx = {'glitch': 1 - abs(lt - 0.52) / 0.1} if 0.42 < lt < 0.62 else {}
    return img, fx

def render_clip(k, out):
    t0, nat, outlen = CLIPS[k]
    n = int(round(outlen * FPS))
    tmp = out[:-4] + '.part.mp4'
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    for i in range(n):
        lt = i / FPS * nat / outlen
        if t0 == 'walk':
            img2, fx = walk_long(lt)
            im = img2.reduce(2).convert('RGB')
            if fx:
                g = cl(fx['glitch']); arr = np.asarray(im).copy(); sh = int(14 * g)
                arr[..., 0] = np.roll(arr[..., 0], sh, 1); arr[..., 2] = np.roll(arr[..., 2], -sh, 1)
                im = Image.fromarray(arr)
        else:
            im = clean_frame(min(t0 + lt, t0 + nat - 1e-3))
        ff.stdin.write(im.tobytes())
    ff.stdin.close()
    if ff.wait() == 0:
        os.replace(tmp, out); print('done', out, flush=True)

if __name__ == '__main__':
    SKY = make_sky()
    if sys.argv[1] == 'stills':
        for t in [float(x) for x in sys.argv[2].split(',')]:
            clean_frame(t).save(f'clean/st_{t:05.2f}.png')
    else:
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clean/{k + 1:02d}.mp4')
