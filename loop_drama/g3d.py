"""遠近のあるブロック3D描画（目の高さのカメラ用）。
座標：x 右、y 奥、z 上。1ブロック = 1.0。人物の1ドット = 1/16。"""
import math
from PIL import Image, ImageDraw

W, H = 1080, 1920
SS = 2  # 2倍で描いて縮める

LIGHT = (0.35, -0.55, 0.76)


def norm(v):
    l = math.sqrt(sum(a * a for a in v)) or 1
    return tuple(a / l for a in v)


LIGHT = norm(LIGHT)


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def rx(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


def ry(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c)


def rz(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class Camera:
    def __init__(self, pos, target, fov=50, roll=0.0):
        self.pos = pos
        f = norm(sub(target, pos))
        r = norm(cross(f, (0, 0, 1)))
        u = cross(r, f)
        if roll:
            c, s = math.cos(roll), math.sin(roll)
            r, u = add(mul(r, c), mul(u, s)), add(mul(u, c), mul(r, -s))
        self.f, self.r, self.u = f, r, u
        self.focal = (H / 2) / math.tan(math.radians(fov) / 2)

    def to_cam(self, p):
        d = sub(p, self.pos)
        return (dot(d, self.r), dot(d, self.u), dot(d, self.f))

    def proj(self, c):
        return (W / 2 + c[0] / c[2] * self.focal) * SS, (H / 2 - c[1] / c[2] * self.focal) * SS


# 箱の面：(法線, 左上の角, u軸, v軸) 箱の中の 0〜1 座標で
FACES = {
    "front": ((0, 1, 0), (1, 1, 1), (-1, 0, 0), (0, 0, -1)),
    "back": ((0, -1, 0), (0, 0, 1), (1, 0, 0), (0, 0, -1)),
    "px": ((1, 0, 0), (1, 0, 1), (0, 1, 0), (0, 0, -1)),
    "nx": ((-1, 0, 0), (0, 1, 1), (0, -1, 0), (0, 0, -1)),
    "top": ((0, 0, 1), (0, 0, 1), (1, 0, 0), (0, 1, 0)),
    "bottom": ((0, 0, -1), (0, 0, 0), (1, 0, 0), (0, 1, 0)),
}


class Box:
    """xform(p) が箱の 0〜1 座標をワールド座標に変える。tex: 面ごとの (行のリスト, パレット)"""

    def __init__(self, xform, color, tex=None, tag=None, glow=False):
        self.xform, self.color, self.tex, self.tag, self.glow = xform, color, tex or {}, tag, glow


def box_aabb(x, y, z, w, d, h, color, tex=None, tag=None, glow=False):
    return Box(lambda p, x=x, y=y, z=z, w=w, d=d, h=h: (x + p[0] * w, y + p[1] * d, z + p[2] * h), color, tex, tag, glow)


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3])


def render(boxes, cam, bg, keep=None):
    """keep: tag の集合。返り値 (画像, keepマスク or None)"""
    polys = []
    for b in boxes:
        corners = {}

        def C(p):
            k = p
            if k not in corners:
                corners[k] = b.xform(p)
            return corners[k]
        for name, (n0, o, u, v) in FACES.items():
            o_w = C(o)
            ou = C(tuple(o[i] + u[i] for i in range(3)))
            ov = C(tuple(o[i] + v[i] for i in range(3)))
            uw, vw = sub(ou, o_w), sub(ov, o_w)
            n = norm(cross(vw, uw)) if name not in () else None
            # 法線の向きを n0 に合わせて確認（変換後）
            ctr = add(o_w, add(mul(uw, 0.5), mul(vw, 0.5)))
            n_ref = norm(sub(b.xform((0.5 + n0[0] * 0.5, 0.5 + n0[1] * 0.5, 0.5 + n0[2] * 0.5)), b.xform((0.5, 0.5, 0.5))))
            if dot(n_ref, sub(cam.pos, ctr)) <= 0:
                continue
            quad = [o_w, ou, add(ou, vw), ov]
            cq = [cam.to_cam(p) for p in quad]
            if min(c[2] for c in cq) < 0.06:
                continue
            depth = sum(c[2] for c in cq) / 4
            lit = 1.0 if b.glow else 0.74 + 0.26 * max(0.0, dot(n_ref, LIGHT)) + 0.06 * max(0.0, dot(n_ref, norm(sub(cam.pos, ctr))))
            tex = b.tex.get(name)
            if tex is None and "side" in b.tex and name in ("px", "nx"):
                rows, pal = b.tex["side"]
                if name == "nx":
                    rows = [r[::-1] for r in rows]
                tex = (rows, pal)
            if tex is None and "all" in b.tex:
                tex = b.tex["all"]
            polys.append((depth, b, cq, o_w, uw, vw, lit, tex))
    polys.sort(key=lambda t: -t[0])
    img = bg.resize((W * SS, H * SS)) if bg.size != (W * SS, H * SS) else bg.copy()
    d = ImageDraw.Draw(img)
    mimg = mdraw = None
    if keep:
        mimg = Image.new("L", (W * SS, H * SS), 0)
        mdraw = ImageDraw.Draw(mimg)
    for depth, b, cq, o_w, uw, vw, lit, tex in polys:
        is_keep = keep is not None and b.tag in keep
        if tex is None:
            pts = [cam.proj(c) for c in cq]
            col = shade(b.color, lit)
            d.polygon(pts, fill=col)
            if mdraw:
                mdraw.polygon(pts, fill=255 if is_keep else 0)
            continue
        rows, pal = tex
        nr, nc = len(rows), len(rows[0])
        for i, row in enumerate(rows):
            j = 0
            while j < nc:
                ch = row[j]
                k = j
                while k + 1 < nc and row[k + 1] == ch:
                    k += 1
                col = pal.get(ch, b.color) if ch != "." else b.color
                if col is not None:
                    a0, a1 = j / nc, (k + 1) / nc
                    b0, b1 = i / nr, (i + 1) / nr
                    q = [add(o_w, add(mul(uw, a), mul(vw, bb))) for a, bb in ((a0, b0), (a1, b0), (a1, b1), (a0, b1))]
                    pts = [cam.proj(cam.to_cam(p)) for p in q]
                    gl = ch.islower() and ch in "zl"  # z, l は光る色
                    d.polygon(pts, fill=shade(col, 1.0 if gl else lit))
                    if mdraw:
                        mdraw.polygon(pts, fill=255 if is_keep else 0)
                j = k + 1
    out = img.resize((W, H), Image.LANCZOS)
    mask = mimg.resize((W, H), Image.BILINEAR) if mimg else None
    return out, mask


# ---------- 人物 ----------
U = 1 / 16  # 1ドット


class Rig:
    """人物モデル。spec は characters.py の定義。pose を変えて boxes() を取る"""

    def __init__(self, spec, pos=(0, 0, 0), yaw=0.0, scale=1.0, tag=None):
        self.spec, self.pos, self.yaw, self.scale = spec, pos, yaw, scale
        self.tag = tag or spec["name"]
        self.pose = dict(head_yaw=0.0, head_pitch=0.0, armL=0.0, armR=0.0, armL_out=0.0, armR_out=0.0, legL=0.0, legR=0.0, sit=False, bob=0.0, lean=0.0)
        self.expr = "normal"
        self.visible = True

    def set(self, **kw):
        self.pose.update(kw)
        return self

    def boxes(self):
        if not self.visible:
            return []
        s, P = self.spec, self.pose
        sc = self.scale
        sit = P["sit"]
        dz = (-0.25 if sit else 0.0) + P["bob"]

        def world(mp):
            mp = (mp[0], mp[1], mp[2] + dz)
            q = rz(mp, self.yaw)
            return (self.pos[0] + q[0] * sc, self.pos[1] + q[1] * sc, self.pos[2] + q[2] * sc)

        bones = {
            # pivot, rotation function (body lean applies to upper body)
            "body": ((0, 0, 0.75), lambda p: rx(p, -P["lean"])),
            "head": ((0, 0, 1.5), lambda p: rx(rz(rx(p, -P["head_pitch"]), P["head_yaw"]), 0)),
            "armL": ((0.375, 0, 1.375), lambda p: ry(rx(p, P["armL"]), -P["armL_out"])),
            "armR": ((-0.375, 0, 1.375), lambda p: ry(rx(p, P["armR"]), P["armR_out"])),
            "legL": ((0.125, 0, 0.75), lambda p: rx(p, P["legL"] + (math.pi / 2 if sit else 0))),
            "legR": ((-0.125, 0, 0.75), lambda p: rx(p, P["legR"] + (math.pi / 2 if sit else 0))),
        }
        lean = P["lean"]
        upper = ("head", "armL", "armR")
        out = []
        for part in s["parts"](self.expr):
            bone, off, size, tex, color = part["bone"], part["off"], part["size"], part.get("tex"), part["color"]
            pivot, rot = bones[bone]

            def xf(p, off=off, size=size, pivot=pivot, rot=rot, bone=bone):
                lp = (off[0] + p[0] * size[0], off[1] + p[1] * size[1], off[2] + p[2] * size[2])
                mp = rot(lp)
                mp = add(mp, pivot)
                if bone in upper and lean:
                    mp = add(rx(sub(mp, (0, 0, 0.75)), -lean), (0, 0, 0.75))
                return world(mp)
            out.append(Box(xf, color, tex, self.tag, part.get("glow", False)))
        return out
