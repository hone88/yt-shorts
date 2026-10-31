"""マイクラ風ブロックの等角（アイソメ）描画エンジン。1コマずつ PIL で描く。"""
import math, random
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
COS = 0.8660254
FONT_BLACK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

# 素材: (上面の色, 側面の色, 模様)
MATS = {
    "grass": ((106, 176, 76), (134, 96, 67), "grass"),
    "dirt": ((134, 96, 67), (134, 96, 67), "noise"),
    "stone": ((128, 128, 132), (128, 128, 132), "noise"),
    "road": ((88, 90, 98), (88, 90, 98), "noise"),
    "line": ((235, 235, 225), (235, 235, 225), "flat"),
    "sand": ((222, 205, 150), (222, 205, 150), "noise"),
    "water": ((64, 140, 220), (50, 115, 195), "water"),
    "pool": ((90, 200, 240), (80, 170, 220), "water"),
    "snow": ((245, 248, 252), (225, 232, 240), "noise"),
    "ice": ((180, 220, 245), (160, 200, 235), "flat"),
    "wood": ((176, 132, 82), (150, 108, 64), "plank"),
    "darkwood": ((110, 76, 48), (96, 66, 40), "plank"),
    "log": ((150, 110, 70), (102, 76, 48), "log"),
    "leaves": ((70, 150, 60), (58, 128, 50), "leaves"),
    "pink": ((246, 168, 190), (230, 140, 168), "leaves"),
    "brick": ((178, 86, 70), (160, 74, 60), "brick"),
    "white": ((236, 236, 232), (222, 222, 216), "noise"),
    "cream": ((242, 228, 196), (226, 210, 176), "noise"),
    "glass": ((170, 215, 240), (150, 200, 232), "glass"),
    "red": ((214, 64, 60), (194, 52, 50), "noise"),
    "blue": ((60, 110, 210), (50, 95, 190), "noise"),
    "navy": ((40, 56, 110), (34, 48, 96), "noise"),
    "green": ((70, 170, 90), (60, 150, 78), "noise"),
    "yellow": ((250, 204, 60), (236, 184, 40), "noise"),
    "orange": ((255, 140, 40), (236, 120, 30), "noise"),
    "purple": ((150, 100, 210), (130, 84, 190), "noise"),
    "gray": ((160, 162, 168), (140, 142, 150), "noise"),
    "black": ((44, 44, 50), (36, 36, 42), "noise"),
    "gold": ((255, 214, 80), (240, 190, 50), "glow"),
    "lamp": ((255, 236, 150), (250, 220, 120), "glow"),
    "carpet": ((170, 44, 56), (150, 38, 50), "noise"),
    "board": ((40, 80, 60), (34, 70, 52), "flat"),
    "paper": ((250, 250, 245), (235, 235, 230), "flat"),
    # 人の部品
    "skin": ((240, 196, 156), (226, 178, 138), "flat"),
    "skin2": ((205, 150, 110), (190, 136, 98), "flat"),
    "hair": ((52, 38, 30), (44, 32, 26), "flat"),
    "hair2": ((120, 76, 40), (104, 64, 34), "flat"),
    "hair3": ((210, 210, 214), (190, 190, 196), "flat"),
    "suit": ((44, 52, 74), (38, 44, 64), "flat"),
    "shirt_w": ((240, 240, 240), (222, 222, 222), "flat"),
    "jeans": ((60, 90, 150), (50, 78, 132), "flat"),
    "shoe": ((40, 36, 34), (34, 30, 28), "flat"),
    "t_orange": ((255, 140, 40), (236, 120, 30), "flat"),
    "t_blue": ((70, 150, 230), (56, 130, 210), "flat"),
    "t_green": ((90, 190, 110), (74, 170, 94), "flat"),
    "t_red": ((230, 80, 80), (210, 64, 64), "flat"),
    "t_yellow": ((250, 210, 70), (236, 190, 50), "flat"),
    "t_pink": ((246, 150, 190), (230, 130, 170), "flat"),
    "t_purple": ((160, 110, 220), (140, 94, 200), "flat"),
    "skirt": ((90, 70, 130), (76, 58, 112), "flat"),
    "coat_w": ((235, 235, 240), (215, 215, 222), "flat"),
}


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def _face_cells(draw, p0, e1, e2, base, pat, face, rnd, sub=4):
    for i in range(sub):
        for j in range(sub):
            col = base
            if pat in ("noise", "grass", "leaves", "water"):
                amp = {"noise": 0.06, "grass": 0.07, "leaves": 0.16, "water": 0.05}[pat]
                col = shade(base, 1 + rnd.uniform(-amp, amp))
            if pat == "grass" and face != "top":
                col = shade(MATS["grass"][0], 0.9 if face == "l" else 0.75) if j == 0 else shade(base, 1 + rnd.uniform(-.07, .07))
                if face == "l":
                    col = col if j == 0 else shade(col, 0.82 / 0.82)
            if pat == "plank" and j in (0,):
                col = shade(base, 0.86)
            if pat == "brick" and (j % 2 == 0):
                col = shade(base, 0.9)
            if pat == "log" and face == "top":
                col = shade(base, 1.15 if (i in (1, 2) and j in (1, 2)) else 1.0)
            if pat == "water" and face == "top" and (i + j) % 3 == 0:
                col = shade(base, 1.12)
            if pat == "glass":
                col = shade(base, 1.08) if (i in (0, sub - 1) or j in (0, sub - 1)) else base
            a = (p0[0] + e1[0] * i / sub + e2[0] * j / sub, p0[1] + e1[1] * i / sub + e2[1] * j / sub)
            b = (a[0] + e1[0] / sub, a[1] + e1[1] / sub)
            c = (b[0] + e2[0] / sub, b[1] + e2[1] / sub)
            d = (a[0] + e2[0] / sub, a[1] + e2[1] / sub)
            draw.polygon([a, b, c, d], fill=col)


@lru_cache(maxsize=4000)
def sprite(mat, S, face_dir=None, kind="block"):
    """一辺 S px のブロック画像。face_dir: 'x' か 'y' なら、その面に目を描く（頭用）。"""
    ss = 4
    s = S * ss
    a, b = s * COS, s * 0.5
    w, h = int(math.ceil(2 * a)) + 2 * ss, int(math.ceil(2 * b + s)) + 2 * ss
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    top, side, pat = MATS[mat]
    rnd = random.Random(hash(mat) & 0xffff)
    o = (ss, ss)
    T = [(o[0] + a, o[1]), (o[0] + 2 * a, o[1] + b), (o[0] + a, o[1] + 2 * b), (o[0], o[1] + b)]
    sub = 4 if S >= 14 else 2
    if kind == "head":
        sub = 4
    # 上面
    topc = top
    if kind == "head":
        topc = MATS[face_dir[1]][0]
    _face_cells(d, T[0], (T[1][0] - T[0][0], T[1][1] - T[0][1]), (T[3][0] - T[0][0], T[3][1] - T[0][1]), topc, pat, "top", rnd, sub)
    # 左面（+y）
    L0 = T[3]
    _face_cells(d, L0, (T[2][0] - T[3][0], T[2][1] - T[3][1]), (0, s), shade(side, 0.82), pat, "l", rnd, sub)
    # 右面（+x）
    R0 = T[2]
    _face_cells(d, R0, (T[1][0] - T[2][0], T[1][1] - T[2][1]), (0, s), shade(side, 0.64), pat, "r", rnd, sub)
    if kind == "head":
        hair = MATS[face_dir[1]][1]
        fd = face_dir[0]
        # 髪：正面は上1/4、横顔は上半分、後ろ頭は全部
        for face, p0, e1, k in (("y", L0, (T[2][0] - T[3][0], T[2][1] - T[3][1]), 0.82), ("x", R0, (T[1][0] - T[2][0], T[1][1] - T[2][1]), 0.64)):
            rows = 1 if fd == face else (4 if fd == "-" + face else 2)
            for i in range(4):
                for j in range(rows):
                    a_ = (p0[0] + e1[0] * i / 4, p0[1] + e1[1] * i / 4 + s * j / 4)
                    d.polygon([a_, (a_[0] + e1[0] / 4, a_[1] + e1[1] / 4), (a_[0] + e1[0] / 4, a_[1] + e1[1] / 4 + s / 4), (a_[0], a_[1] + s / 4)], fill=shade(hair, k))
            if fd == face:
                # 目（2マス目の行に、左右1マスずつ）
                for i in (1, 2):
                    j = 2
                    a_ = (p0[0] + e1[0] * (i + 0.15) / 4, p0[1] + e1[1] * (i + 0.15) / 4 + s * (j - 0.6) / 4)
                    ew, eh = 0.55, 0.5
                    d.polygon([a_, (a_[0] + e1[0] * ew / 4, a_[1] + e1[1] * ew / 4), (a_[0] + e1[0] * ew / 4, a_[1] + e1[1] * ew / 4 + s * eh / 4), (a_[0], a_[1] + s * eh / 4)], fill=(30, 30, 40))
                # 口
                a_ = (p0[0] + e1[0] * 1.5 / 4, p0[1] + e1[1] * 1.5 / 4 + s * 3.1 / 4)
                d.polygon([a_, (a_[0] + e1[0] / 4, a_[1] + e1[1] / 4), (a_[0] + e1[0] / 4, a_[1] + e1[1] / 4 + s * 0.22 / 4), (a_[0], a_[1] + s * 0.22 / 4)], fill=(170, 90, 80))
    if pat == "glow":
        pass
    # 輪郭
    lw = max(1, int(ss * (0.8 if S >= 20 else 0.5)))
    ec = (0, 0, 0, 70)
    d.line(T + [T[0]], fill=ec, width=lw)
    d.line([T[3], (T[3][0], T[3][1] + s), (T[2][0], T[2][1] + s), (T[1][0], T[1][1] + s), T[1]], fill=ec, width=lw)
    d.line([T[2], (T[2][0], T[2][1] + s)], fill=ec, width=lw)
    out = img.resize((max(1, w // ss), max(1, h // ss)), Image.LANCZOS)
    return out, 1.0  # 左上の余白 = 1px


class Cam:
    def __init__(self, s, cx, cy, cz=0, sx=540, sy=1010):
        self.s, self.cx, self.cy, self.cz, self.sx, self.sy = s, cx, cy, cz, sx, sy

    def proj(self, x, y, z):
        dx, dy, dz = x - self.cx, y - self.cy, z - self.cz
        return self.sx + (dx - dy) * COS * self.s, self.sy + (dx + dy) * 0.5 * self.s - dz * self.s


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def cam_at(k0, k1, t):
    """k = (s, cx, cy, cz)。t は 0..1"""
    e = ease(t)
    return Cam(*(lerp(a, b, e) for a, b in zip(k0, k1)))


def draw_boxes(img, boxes, cam):
    """boxes: (x, y, z, size, mat[, head_info])。奥から順に描く。"""
    items = []
    for bx in boxes:
        x, y, z, sz = bx[0], bx[1], bx[2], bx[3]
        key = x + y + z + 1.5 * sz
        items.append((key, z, bx))
    items.sort(key=lambda t: (t[0], t[1]))
    for _, _, bx in items:
        x, y, z, sz, mat = bx[:5]
        S = max(2, int(round(sz * cam.s)))
        if len(bx) > 5 and bx[5]:
            spr, pad = sprite(mat, S, bx[5], "head")
        else:
            spr, pad = sprite(mat, S)
        u, v = cam.proj(x, y, z + sz)
        px = int(round(u - S * COS - pad))
        py = int(round(v - pad))
        if px > W or py > H or px + spr.width < 0 or py + spr.height < 0:
            continue
        img.alpha_composite(spr, (max(0, px), max(0, py)), (max(0, -px), max(0, -py)))


def cull(blocks):
    """完全に隠れているブロックを除く（上・+x・+y が埋まっている単位ブロック）。"""
    occ = {(b[0], b[1], b[2]) for b in blocks if b[3] == 1}
    out = []
    for b in blocks:
        x, y, z = b[0], b[1], b[2]
        if b[3] == 1 and (x, y, z + 1) in occ and (x + 1, y, z) in occ and (x, y + 1, z) in occ:
            continue
        out.append(b)
    return out


# ---------- 人 ----------
class Person:
    """マイクラ風の人。高さ2ブロック。facing: 'x' / 'y' / '-x' / '-y'"""

    def __init__(self, x, y, z=1, facing="x", shirt="t_blue", pants="jeans", hair="hair", skin="skin", scale=1.0, skirt=False):
        self.x, self.y, self.z, self.facing = x, y, z, facing
        self.shirt, self.pants, self.hair, self.skin, self.scale, self.skirt = shirt, pants, hair, skin, scale, skirt
        self.walk = 0.0      # 歩きの位相の振幅 0..1
        self.phase = 0.0
        self.arm_up = (0.0, 0.0)  # 右腕・左腕の上げ具合 0..1
        self.bob = 0.0
        self.jump = 0.0
        self.visible = True

    def boxes(self):
        if not self.visible:
            return []
        m = 0.25 * self.scale
        f = {"x": (1, 0), "-x": (-1, 0), "y": (0, 1), "-y": (0, -1)}[self.facing]
        r = (-f[1], f[0]) if True else None  # 右手方向
        ox, oy = self.x, self.y
        oz = self.z + self.bob + self.jump
        sw = math.sin(self.phase) * self.walk
        out = []

        def put(fo, ro, zo, mat, sz=m, head=None):
            px = ox + f[0] * fo + r[0] * ro - sz / 2
            py = oy + f[1] * fo + r[1] * ro - sz / 2
            out.append((px, py, oz + zo, sz, mat, head) if head else (px, py, oz + zo, sz, mat))

        # 脚
        for side, s_ in ((-0.5, 1), (0.5, -1)):
            off = s_ * sw * 0.18 * self.scale
            lift = max(0, s_ * sw) * 0.06 * self.scale
            for k in range(3):
                mat = "shoe" if k == 0 else self.pants
                if self.skirt and k == 2:
                    mat = self.shirt
                put(off, side * m, k * m + lift, mat)
        # 胴
        for k in range(3, 6):
            for side in (-0.5, 0.5):
                put(0, side * m, k * m, self.shirt)
        # 腕（p=0 肩, 1 ひじ, 2 手）
        for idx, side in enumerate((-1.5, 1.5)):
            up = self.arm_up[idx]
            s_ = -1 if side < 0 else 1
            swing = -s_ * sw * 0.16 * self.scale * (1 - up)
            for p in range(3):
                zz = (5 + p * (2 * up - 1)) * m
                put(swing + up * 0.05 * self.scale * p, side * m, zz, self.skin if p == 2 else self.shirt)
        # 頭
        hs = 2 * m
        fd = self.facing
        put(0, 0, 6 * m + hs / 2 - hs / 2, self.skin, hs, (fd, self.hair))
        return out


def sky(top, bottom):
    g = Image.new("RGBA", (1, 256))
    for i in range(256):
        t = i / 255
        g.putpixel((0, i), tuple(int(lerp(a, b, t)) for a, b in zip(top, bottom)) + (255,))
    return g.resize((W, H), Image.BILINEAR)


def clouds(img, t, seed=1, color=(255, 255, 255, 230), y0=560, y1=1300, n=5, speed=18):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img)
    for i in range(n):
        x = (rnd.uniform(-200, 1200) + t * speed * rnd.uniform(0.6, 1.4)) % 1500 - 260
        y = rnd.uniform(y0, y1)
        w = rnd.uniform(120, 240)
        hh = w * 0.22
        d.rectangle([x, y, x + w, y + hh], fill=color)
        d.rectangle([x + w * 0.2, y - hh * 0.8, x + w * 0.7, y + 1], fill=color)


# ---------- 文字 ----------
@lru_cache(maxsize=64)
def font(path, size):
    return ImageFont.truetype(path, size, index=0)


def text_block(lines, size, fill=(255, 255, 255), stroke=(22, 30, 58), sw=10, path=FONT_BLACK, hl=None, gap=1.18):
    """複数行の文字を、縁取り付きで1枚の画像にする。hl: 強調する行番号と色。"""
    f = font(path, size)
    widths = [f.getbbox(l, stroke_width=sw)[2] for l in lines]
    lh = int(size * gap)
    img = Image.new("RGBA", (max(widths) + 2 * sw + 8, lh * len(lines) + 2 * sw + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        x = (img.width - widths[i]) // 2
        col = fill
        if hl and i in hl:
            col = hl[i]
        d.text((x + sw, sw + i * lh), l, font=f, fill=col, stroke_width=sw, stroke_fill=stroke)
    return img


def fit_text(lines, size, maxw, **kw):
    while True:
        im = text_block(lines, size, **kw)
        if im.width <= maxw or size < 30:
            return im
        size -= 4


def rounded_badge(text, size=34, bg=(255, 138, 31), fg=(255, 255, 255), pad=(22, 10)):
    f = font(FONT_BLACK, size)
    bb = f.getbbox(text)
    w, h = bb[2] + pad[0] * 2, size + pad[1] * 2 + 6
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=bg)
    d.text((pad[0], pad[1] - bb[1] + 3), text, font=f, fill=fg)
    return img


def paste_center(img, im, cx, cy, scale=1.0, alpha=1.0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if alpha < 1.0:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy()
        im.putalpha(a)
    img.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def pop(t, dur=0.28):
    """出てくるときの拡大（少し行き過ぎて戻る）。"""
    if t >= dur:
        return 1.0
    x = t / dur
    return 0.6 + 0.4 * (1 + 2.2 * (x - 1) ** 3 + 1.2 * (x - 1) ** 2) if x < 1 else 1.0
