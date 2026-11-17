"""個人用の実験「深呼吸するたびに、セロトニンが2倍になったら？」（11/18）。投稿しない。
参考動画（ドーパミン×2のリール）と同じ型：深呼吸のたびに ×2、上に数値の表示、明朝体のひとこと、最後に ×0 で虚無。
声は tools/voice/sero_breath.json（VOICEVOX）。長さは環境変数 SERO_VDIR の dur.json から読み、場面の長さを声に合わせる。
使い方: python3 sero_voxel.py stills t1,t2,... out.png / python3 sero_voxel.py render a b out.mp4（a〜b秒）"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import render, ease, C, f32, Scene
from elevator_voxel import put
import story_voxel as SV
from story_voxel import hito, HEAD, aim, tone, SKIN

W, H, FPS, RS = 1080, 1920, 30, 4
FY = 2
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
SANS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts', 'NotoSansCJK-Black.ttc')
_F = {}


def ft(path, sz):
    k = (path, sz)
    if k not in _F:
        _F[k] = ImageFont.truetype(path, sz, index=0)
    return _F[k]


SV.FACES["疲れ"] = ["HHHHHHHH", "HHHHHHHH", "HSSSSSSH", "SSSSSSSS", "SWESSEWS", "SEESSEES", "SSSSSSSS", "SSMMMMSS"]
SV.FACES["恍惚"] = ["HHHHHHHH", "HHHHHHHH", "HSSSSSSH", "SSSSSSSS", "SEESSEES", "SPSSSSPS", "SSMMMMSS", "SSSMMSSS"]
SV.FACES["悟り"] = ["HHHHHHHH", "HHHHHHHH", "HSSSSSSH", "SSSSSSSS", "SEESSEES", "SSSSSSSS", "SSSMMSSS", "SSSMMSSS"]
SV.FACES["無"] = ["HHHHHHHH", "HHHHHHHH", "HSSSSSSH", "SSSSSSSS", "SWESSEWS", "SSSSSSSS", "SSSSSSSS", "SSSSSSSS"]
P_MAN = {"髪": (0.1, 0.08, 0.07), "服": (0.85, 0.35, 0.25), "服2": (0.75, 0.3, 0.2), "下": (0.22, 0.25, 0.35), "靴": (0.9, 0.9, 0.9)}
MX, MZ = 40, 48

# ------------------------------------------------------------------ 台本（タイムライン）
LV = [  # (倍率, 状態, ひとこと×2（声の字幕）, 状態チップの色)
    (1, "日常のストレス", ["締め切りやばい！ 課題終わらない！", "イライラ するーー！"], (120, 120, 130)),
    (2, "ちょい安心", ["……あれ？", "ちょっと 落ち着いたかも"], (230, 170, 40)),
    (4, "ちょい安心", ["なんか 肩が軽い", "温泉 入った？"], (230, 170, 40)),
    (8, "ほっこり", ["教授に怒られたの", "ありがたい 気がしてきた"], (240, 120, 160)),
    (16, "聖人モード", ["締め切り？", "地球46億年から見たら 0秒じゃん"], (150, 110, 240)),
    (32, "聖人モード", ["ハトさん こんにちは", "そもそも ケンカしてなかったね"], (150, 110, 240)),
    (64, "聖人モード", ["みんな違って", "みんないい……"], (150, 110, 240)),
    (128, "悟りかけ", ["見える……", "レジ袋のゆらぎに 宇宙の真理が……"], (60, 190, 120)),
    (256, "重力より上", ["あ、浮いてる", "締め切りは 地球に置いてきた"], (60, 140, 240)),
    (512, "宇宙とワンネス", ["私は……", "全宇宙と ひとつになった……"], (40, 200, 220)),
    (1024, "欲の完全消滅", ["もう 何も欲しくない……", "オーーーム……"], (255, 90, 200)),
]
ZERO = ["……お腹も 空かない", "……連絡も 返さない", "……生きている意味も 特にない", "……すばらしい"]

import json as _json
_VD = os.path.join(os.environ.get("SERO_VDIR", "."), "dur.json")
VO = _json.load(open(_VD)) if os.path.exists(_VD) else {}
def vd(k, d=2.5):
    return VO.get(k, d)

INTRO = max(3.0, vd("00") + 0.7)
L0 = vd("01") + 1.0
GL, ND = 1.4, 4.5
SEG = [("intro", 0, INTRO), ("lv", 0, L0)]
VOICE = [(0.3, "00"), (INTRO + 0.25, "01")]
for i in range(1, 11):
    SEG += [("scroll", i, vd("br", 3.0) + 0.4), ("lv", i, max(4.2, vd(f"{i + 1:02d}") + 1.4))]
SEG += [("glitch", 0, GL)]
for k in range(4):
    SEG += [("zero", k, vd(f"z{k + 1}") + 1.0)]
SEG += [("notif", 0, ND)]
STARTS = []
_t = 0.0
for s_ in SEG:
    STARTS.append(_t); _t += s_[2]
DUR = _t
for (kind, i, d), s0 in zip(SEG, STARTS):
    if kind == "scroll": VOICE.append((s0 + 0.1, "br"))
    if kind == "lv" and i > 0: VOICE.append((s0 + 0.3, f"{i + 1:02d}"))
    if kind == "zero": VOICE.append((s0 + 0.35, f"z{i + 1}"))
FACE_OVR = [None]


def seg_at(t):
    for (kind, i, d), s0 in zip(SEG, STARTS):
        if t < s0 + d:
            return kind, i, t - s0, d
    kind, i, d = SEG[-1]
    return kind, i, d - 1e-3, d


# ------------------------------------------------------------------ セット
def build_room():
    S = Scene(80, 64, 80)
    c, m = S.col, S.mat
    put(c, m, 0, 80, 0, FY, 0, 80, (0.55, 0.45, 0.36), 1, 0.05)               # 床
    put(c, m, 0, 80, FY, 64, 74, 78, (0.78, 0.76, 0.8), 1, 0.02)              # うしろの壁
    m[22:58, FY + 26:FY + 50, 74:78] = 0                                       # 夜の窓
    put(c, m, 22, 58, FY + 37, FY + 38, 74, 78, (0.6, 0.6, 0.65), 1, 0.0)
    put(c, m, 0, 80, FY, 64, 79, 80, (0.06, 0.07, 0.16), 1, 0.0)
    for (x, y) in ((28, 44), (35, 47), (47, 41), (53, 46), (40, 33)):          # 星
        put(c, m, x, x + 1, FY + y - 10, FY + y - 9, 79, 80, (1.6, 1.6, 1.4), 1, 0.0)
    put(c, m, 0, 3, FY, 64, 0, 78, (0.8, 0.78, 0.82), 1, 0.02)               # 横の壁
    put(c, m, 77, 80, FY, 64, 0, 78, (0.8, 0.78, 0.82), 1, 0.02)
    put(c, m, 60, 74, FY, FY + 40, 64, 74, (0.55, 0.4, 0.28), 1, 0.04)        # 本だな
    for yy in (10, 20, 30):
        put(c, m, 60, 74, FY + yy, FY + yy + 1, 63, 64, (0.5, 0.35, 0.25), 1, 0.0)
        for x in range(61, 73, 2):
            put(c, m, x, x + 1, FY + yy - 7, FY + yy, 64, 66, [(0.8, 0.3, 0.3), (0.3, 0.5, 0.8), (0.9, 0.8, 0.3)][x % 3], 1, 0.03)
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = np.array([0.3, 0.8, -0.5]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(0.75, 0.72, 0.7); S.amb = C(0.55, 0.55, 0.62)
    S.lights = [((40, FY + 30, 30), (0.9, 0.8, 0.65), 60)]
    S.hor = C(0.1, 0.12, 0.25); S.top = C(0.03, 0.04, 0.12); S.fog0, S.fogk = 300, 400
    return S


def build_void():
    S = Scene(80, 90, 80)
    S.base_c, S.base_m = S.col.copy(), S.mat.copy()
    S.sun = np.array([0.2, 0.6, -0.8]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.0, 0.95, 1.05); S.amb = C(0.75, 0.7, 0.85); S.lights = []
    S.hor = C(0, 0, 0); S.top = C(0, 0, 0); S.fog0, S.fogk = 400, 500
    return S


_S = {}


def get(k):
    if k not in _S:
        _S[k] = {"room": build_room, "void": build_void}[k]()
    return _S[k]


def desk(c, m, laptop_open=True):
    put(c, m, 24, 56, FY + 12, FY + 14, 28, 38, (0.62, 0.45, 0.3), 1, 0.03)
    for x in (25, 54):
        put(c, m, x, x + 1, FY, FY + 12, 29, 37, (0.5, 0.36, 0.24), 1, 0.0)
    put(c, m, 33, 47, FY + 14, FY + 15, 30, 37, (0.25, 0.26, 0.3), 1, 0.0)
    if laptop_open:
        put(c, m, 34, 46, FY + 15, FY + 21, 30, 31, (0.25, 0.26, 0.3), 1, 0.0)
        put(c, m, 35, 45, FY + 16, FY + 20, 31, 32, (0.5, 0.75, 1.3), 1, 0.0)
    put(c, m, 26, 30, FY + 14, FY + 19, 31, 35, (0.95, 0.95, 0.92), 1, 0.0)    # マグカップ
    put(c, m, 49, 54, FY + 14, FY + 16, 31, 36, (0.95, 0.92, 0.6), 1, 0.0)     # 書類


def chair(c, m):
    put(c, m, 34, 46, FY + 6, FY + 8, 42, 54, (0.2, 0.2, 0.25), 1, 0.02)
    put(c, m, 34, 46, FY + 8, FY + 26, 53, 55, (0.2, 0.2, 0.25), 1, 0.02)
    put(c, m, 39, 41, FY, FY + 6, 47, 49, (0.3, 0.3, 0.33), 1, 0.0)


def man(c, m, fy, face, arms="front", phone=True, scr=(0.4, 0.8, 1.6), cz=MZ, cx=MX):
    face = FACE_OVR[0] or face
    hito(c, m, cx, fy, cz, P_MAN, face=face, arms=arms, f=-1, sit=True)
    if phone and arms == "front":
        put(c, m, cx - 3, cx + 3, fy + 11, fy + 17, cz - 11, cz - 10, (0.1, 0.1, 0.12), 1, 0.0)
        put(c, m, cx - 2, cx + 2, fy + 12, fy + 16, cz - 12, cz - 11, scr, 1, 0.0)


def halo(c, m, fy, a, cx=MX, cz=MZ):
    y = fy + 31
    for k in range(28):
        th = 2 * math.pi * k / 28 + a
        x = int(round(cx + 5.5 * math.cos(th))); z = int(round(cz + 5.5 * math.sin(th)))
        put(c, m, x, x + 1, y, y + 1, z, z + 1, (2.2, 1.8, 0.6), 1, 0.0)


def dove(c, m, x, y, z, flap):
    x, y, z = int(x), int(y), int(z)
    put(c, m, x, x + 4, y, y + 2, z, z + 2, (0.98, 0.98, 0.98), 1, 0.0)
    put(c, m, x + 3, x + 5, y + 1, y + 3, z, z + 2, (0.98, 0.98, 0.98), 1, 0.0)
    put(c, m, x + 5, x + 6, y + 1, y + 2, z, z + 1, (1.0, 0.6, 0.2), 1, 0.0)
    wy = y + 2 if flap else y - 1
    put(c, m, x + 1, x + 3, wy, wy + 1, z - 2, z + 4, (0.92, 0.92, 0.95), 1, 0.0)


def bag(c, m, x, y, z, t):
    x, y, z = int(x), int(y), int(z)
    sw = int(round(1.5 * math.sin(t * 3)))
    put(c, m, x, x + 8, y, y + 9, z, z + 3, (0.75, 0.82, 0.95), 1, 0.06)
    put(c, m, x + 1 + sw, x + 7 + sw, y + 9, y + 11, z, z + 3, (0.75, 0.82, 0.95), 1, 0.06)
    put(c, m, x + sw, x + 2 + sw, y + 11, y + 14, z + 1, z + 2, (0.55, 0.6, 0.75), 1, 0.0)
    put(c, m, x + 6 + sw, x + 8 + sw, y + 11, y + 14, z + 1, z + 2, (0.55, 0.6, 0.75), 1, 0.0)


# ------------------------------------------------------------------ 画面効果
def hue(img, a):
    """RGB を色相 a ラジアン回す"""
    cA, sA = math.cos(a), math.sin(a)
    k = 1 / 3; q = math.sqrt(1 / 3)
    M = np.array([[cA + (1 - cA) * k, k * (1 - cA) - q * sA, k * (1 - cA) + q * sA],
                  [k * (1 - cA) + q * sA, cA + k * (1 - cA), k * (1 - cA) - q * sA],
                  [k * (1 - cA) - q * sA, k * (1 - cA) + q * sA, cA + k * (1 - cA)]], f32)
    return np.clip(img @ M.T, 0, 1)


def pastel(img, a):
    if a <= 0: return img
    pk = np.array([1.0, 0.82, 0.92], f32)
    out = img * (1 - 0.45 * a) + pk * 0.45 * a
    g = out.mean(2, keepdims=True)
    return np.clip(g + (out - g) * (1 + 0.6 * a), 0, 1)


def rgbsplit(img, px):
    px = int(px)
    if px <= 0: return img
    o = img.copy()
    o[:, px:, 0] = img[:, :-px, 0]; o[:, :-px, 2] = img[:, px:, 2]
    return o


def kaleido(img, n=1):
    o = img.copy()
    o[:, W // 2:] = o[:, :W // 2][:, ::-1]
    if n > 1:
        o[H // 2:] = o[:H // 2][::-1]
    return o


def space_bg(h, w, t, k):
    """宇宙：星と、ゆっくり回る色の雲（低解像度で作る）"""
    yy, xx = np.mgrid[0:h, 0:w].astype(f32)
    x = (xx / w - 0.5) * 2; y = (yy / h - 0.5) * 2 * h / w
    r = np.sqrt(x * x + y * y) + 1e-3; a = np.arctan2(y, x)
    v = 0.5 + 0.5 * np.sin(6 * a + 4 * r - t * 1.5 * k)
    col = np.stack([0.5 + 0.5 * np.sin(r * 3 - t + 0), 0.5 + 0.5 * np.sin(r * 3 - t + 2.1), 0.5 + 0.5 * np.sin(r * 3 - t + 4.2)], -1)
    img = col * (0.15 + 0.55 * v[..., None] * k) * np.exp(-r * 0.6)[..., None]
    rg = np.random.default_rng(3)
    sx = rg.integers(0, w, 300); sy = rg.integers(0, h, 300)
    tw = 0.6 + 0.4 * np.sin(t * 4 + np.arange(300))
    img[sy, sx] = np.maximum(img[sy, sx], tw[:, None])
    return img.astype(f32)


def mandala(lay, t, a, cy=H * 0.58, R=520):
    if a <= 0: return
    d = ImageDraw.Draw(lay)
    for ring in range(5):
        n = 8 + ring * 4; rr = R * (0.25 + ring * 0.18)
        rot = t * (0.6 if ring % 2 else -0.45) + ring
        hcol = [int(127 + 127 * math.sin(t * 2 + ring * 1.3 + p)) for p in (0, 2.1, 4.2)]
        for k in range(n):
            th = rot + 2 * math.pi * k / n
            px, py = W / 2 + rr * math.cos(th), cy + rr * math.sin(th)
            s = 30 + ring * 10
            pts = [(px + s * math.cos(th + q), py + s * math.sin(th + q)) for q in (0, 2.0, math.pi, -2.0)]
            d.polygon(pts, fill=tuple(hcol) + (int(170 * a),))


def rainbow_rings(lay, t, a, cy=H * 0.35):
    if a <= 0: return
    d = ImageDraw.Draw(lay)
    for k in range(7):
        r = ((t * 260 + k * 160) % 1150)
        col = [int(127 + 127 * math.sin(k * 0.9 + p)) for p in (0, 2.1, 4.2)]
        d.ellipse([W / 2 - r, cy - r * 0.6, W / 2 + r, cy + r * 0.6], outline=tuple(col) + (int(150 * a * (1 - r / 1150)),), width=14)


def sparkles(lay, t, a, n=40, seed=1):
    if a <= 0: return
    d = ImageDraw.Draw(lay); rg = np.random.default_rng(seed)
    for k in range(n):
        x, y = rg.uniform(0, W), rg.uniform(H * 0.2, H * 0.95)
        s = (8 + 18 * rg.random()) * (0.5 + 0.5 * math.sin(t * 5 + k))
        if s < 2: continue
        al = int(230 * a)
        d.polygon([(x, y - s * 2), (x + s * 0.4, y), (x, y + s * 2), (x - s * 0.4, y)], fill=(255, 250, 220, al))
        d.polygon([(x - s * 2, y), (x, y + s * 0.4), (x + s * 2, y), (x, y - s * 0.4)], fill=(255, 250, 220, al))


def mouth_light(lay, t, a, p):
    if a <= 0 or p is None: return
    d = ImageDraw.Draw(lay); rg = np.random.default_rng(int(t * 30))
    x0, y0 = p
    for k in range(60):
        u = rg.random(); ang = rg.uniform(-0.6, 0.6) + math.pi / 2
        r = u * 700
        x, y = x0 + r * math.cos(ang) * rg.choice([-1, 1]) * 0.5, y0 + r * math.sin(ang)
        s = 4 + 10 * (1 - u)
        col = [int(200 + 55 * math.sin(k + p_)) for p_ in (0, 2, 4)]
        d.ellipse([x - s, y - s, x + s, y + s], fill=tuple(col) + (int(220 * a * (1 - u)),))


# ------------------------------------------------------------------ 文字
def num(v):
    return f"×{v}"


def hud(d, val, scroll, status, scol, a=1.0, big=None):
    A = int(255 * a)
    d.text((W / 2, 118), "セロトニン", font=ft(SANS, 30), fill=(255, 255, 255, A), anchor="mm")
    d.text((W / 2, 196), big or num(val), font=ft(SERIF, 118), fill=(255, 255, 255, A), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, int(A * 0.5)))
    d.text((W / 2, 272), f"深呼吸 {scroll}回目", font=ft(SANS, 26), fill=(255, 255, 255, A), anchor="mm")
    f = ft(SANS, 24)
    t1, t2 = "深呼吸ごとに×2", status
    w1 = d.textlength(t1, font=f) + 24; w2 = d.textlength(t2, font=f) + 24
    x0 = W / 2 - (w1 + w2 + 10) / 2
    d.rectangle([x0, 296, x0 + w1, 330], fill=(10, 10, 14, int(A * 0.85)))
    d.text((x0 + w1 / 2, 313), t1, font=f, fill=(255, 255, 255, A), anchor="mm")
    d.rectangle([x0 + w1 + 10, 296, x0 + w1 + 10 + w2, 330], fill=tuple(scol) + (A,))
    d.text((x0 + w1 + 10 + w2 / 2, 313), t2, font=f, fill=(255, 255, 255, A), anchor="mm")


def caption(d, text, a=1.0, y=470):
    if a <= 0.01: return
    lines = text.split(" ")
    if len(lines) > 2:
        lines = [lines[0], " ".join(lines[1:])]
    A = int(255 * a)
    for k, ln in enumerate(lines):
        d.text((W / 2, y + k * 86 - (len(lines) - 1) * 43), ln, font=ft(SERIF, 66), fill=(255, 255, 255, A), anchor="mm",
               stroke_width=5, stroke_fill=(20, 10, 30, int(A * 0.75)))


def cap2(lines, u):
    """2つのひとことを、前半・後半に（ふわっと入れかえ）"""
    i = 0 if u < 0.5 else 1
    uu = u * 2 - i
    a = min(1, uu / 0.12) * (1 if (i == 1 or uu < 0.92) else 1)
    if i == 0 and uu > 0.92: a = max(0, (1 - uu) / 0.08)
    return lines[i], a


# ------------------------------------------------------------------ 1コマ
def to_img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")


def from_img(im):
    return np.asarray(im.convert("RGB")).astype(f32) / 255


SKY = [None]
LASTVIEW = [None]


def scene3d(set_, cam, tgt, fov, draws, bg=None, fx=None):
    S = get(set_)
    c, m = S.base_c.copy(), S.base_m.copy()
    for dr in draws:
        dr(c, m)
    w, h = W // RS, H // RS
    img, depth = render(S, c, m, cam, tgt, fov, w, h)
    img = tone(img)
    if bg is not None:
        sky = ~np.isfinite(depth.reshape(h, w)) if depth.ndim == 1 else ~np.isfinite(depth)
        img = np.where(sky[..., None], bg, img)
        SKY[0] = np.repeat(np.repeat(sky, RS, 0), RS, 1).astype(f32)
    img = np.repeat(np.repeat(img, RS, 0), RS, 1)
    LASTVIEW[0] = (cam, tgt, fov)
    return img.astype(f32), (cam, tgt, fov)


def proj(view, p):
    pr = SV.project(*view, p)
    return None if pr is None else (pr[0], pr[1])


def camf(dist, yaw=0.0, h=36, ty=27, cx=MX, cz=MZ, fy=FY):
    return (cx + dist * math.sin(yaw), fy + h, cz - dist * math.cos(yaw)), (cx, fy + ty, cz), 46


def lvl_frame(i, t, u, T, text=True):
    """i 段目（0〜10）。t は段の中の秒、u=t/T"""
    val, st, lines, scol = LV[i]
    hd = HEAD(MX, FY, MZ, sit=True)
    sp = 0.5 + 0.5 * math.sin(t * 2)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mpos = None
    if i == 0:   # 締め切り：必死にキーボード（手がふるえる）
        jit = int(t * 14) % 2
        cam, tgt, fov = camf(62 - 10 * u, 0.15, 40 + jit * 0.4)
        img, view = scene3d("room", cam, tgt, fov, [desk, chair, lambda c, m: man(c, m, FY + jit * 0, "疲れ", phone=False)])
        img = img * np.array([0.85, 0.88, 1.0], f32)
    elif i <= 6:  # 部屋で、どんどんほわほわ
        face = "ふつう" if i == 1 else ("笑顔" if i <= 4 else "恍惚")
        a_ = 0.3 * math.sin(t * 0.7)
        cam, tgt, fov = camf(58 - 8 * u - (i - 1) * 1.5, a_, 36)
        scr = [(0.4, 0.8, 1.6), (1.6, 0.9, 0.3), (1.6, 0.5, 0.9), (0.6, 1.6, 0.8)][i % 4]
        dr = [lambda c, m: desk(c, m, False), chair, lambda c, m: man(c, m, FY, face, scr=scr)]
        if i >= 5:
            for k in range(5 if i == 5 else 8):
                ph = t * 0.9 + k * 1.3
                dr.append(lambda c, m, ph=ph, k=k: dove(c, m, 40 + 26 * math.cos(ph), FY + 34 + 6 * math.sin(ph * 2 + k), 40 + 18 * math.sin(ph), int(t * 8 + k) % 2))
        if i >= 6:
            dr.append(lambda c, m: halo(c, m, FY, t))
        img, view = scene3d("room", cam, tgt, fov, dr)
        img = img * (1 + 0.08 * i)
        img = pastel(np.clip(img, 0, 1), [0, 0, 0.15, 0.3, 0.5, 0.7, 0.85][i])
        sparkles(lay, t, [0, 0, 0, 0.4, 0.6, 0.8, 1.0][i], n=20 + 6 * i, seed=i)
        if i >= 6:
            rainbow_rings(lay, t, 0.8)
    elif i == 7:  # レジ袋のゆらぎ：浮かぶレジ袋、色がうねる
        z = ease(u)
        cam = (MX + 8 - 14 * z, FY + 34, 3 + 4 * z); tgt = (MX, FY + 28, 34)
        img, view = scene3d("room", cam, tgt, 48, [lambda c, m: desk(c, m, False), chair, lambda c, m: man(c, m, FY, "悟り"),
                                                     lambda c, m: bag(c, m, MX + 5, FY + 15 + 2 * math.sin(t * 2), 34, t)])
        img = hue(pastel(img, 0.3), t * 1.2)
        rainbow_rings(lay, t, 0.5, cy=H * 0.62)
        mandala(lay, t, 0.35 * u)
    elif i == 8:  # イスから浮く → 部屋が消えて宇宙
        lift = 22 * ease(min(1, u * 1.6))
        z = ease(u)
        cam = (MX + 16 * z, FY + 34 + lift * 0.7, 1); tgt = (MX, FY + 33 + lift, MZ)
        roomv = smooth_(0.45, 0.75, u)
        dr = [lambda c, m: man(c, m, FY + int(lift), "悟り", arms="front", phone=False)]
        if roomv < 1:
            img, view = scene3d("room", cam, tgt, 50, [lambda c, m: desk(c, m, False), chair] + dr)
            img = hue(pastel(img, 0.6), t)
        if roomv > 0:
            bg = space_bg(H // RS, W // RS, t, 0.6)
            img2, view = scene3d("void", (cam[0], cam[1], cam[2]), tgt, 50, [lambda c, m: man(c, m, FY + 30, "悟り", arms="front", phone=False, cz=40)], bg=bg)
            img = img2 if roomv >= 1 else img * (1 - roomv) + img2 * roomv
        sparkles(lay, t, 0.8)
    else:        # 9: ワンネス（あぐらで合掌、曼荼羅）、10: 欲の完全消滅（口から光、全部ミラー）
        k = 1.0 if i == 9 else 1.6
        yaw = 0.6 * math.sin(t * 0.5) if i == 9 else 0.45 * math.sin(t * 1.3)
        cam, tgt, fov = camf(50 - (6 * u if i == 10 else 0), yaw, 34, 26, 40, 40, FY + 30)
        bg = space_bg(H // RS, W // RS, t, k)
        img, view = scene3d("void", cam, tgt, fov, [lambda c, m: man(c, m, FY + 30, "悟り", arms="front", phone=False, cz=40),
                                                  lambda c, m: halo(c, m, FY + 30, t * 2, cz=40)], bg=bg)
        ml = Image.new("RGBA", (W, H), (0, 0, 0, 0)); mandala(ml, t, 1.0, cy=H * 0.58)
        mm = np.asarray(ml).astype(f32) / 255
        al = mm[..., 3:4] * SKY[0][..., None]
        img = img * (1 - al) + mm[..., :3] * al
        if i == 10:
            mpos = proj(view, (40, FY + 30 + 21, 40 - 4))
            mouth_light(lay, t, 1.0, mpos)
    # 重ねる
    im = to_img(img)
    im = Image.alpha_composite(im, lay)
    img = from_img(im)
    if i == 10:
        img = hue(img, t * 2.5)
        img = rgbsplit(img, 6 + 10 * sp)
        img = kaleido(img, 1) if u > 0.4 else img
    elif i == 9:
        img = hue(img, t * 0.8)
        if u > 0.5:
            img = kaleido(img, 1)
    if not text:
        return img
    im = to_img(img); d = ImageDraw.Draw(im)
    hud(d, val, i, st, scol)
    txt, a = cap2(lines, u)
    caption(d, txt, a)
    return from_img(im)


def smooth_(a, b, x):
    x = min(1, max(0, (x - a) / (b - a)))
    return x * x * (3 - 2 * x)


_BG = {}


def scroll_frame(i, t, u):
    """深呼吸：目を閉じて「すぅーー」（吸う）→「はぁーー」（吐く、白い息）。吐き終わりで ×N に上がる"""
    prev, val = LV[i - 1][0], LV[i][0]
    FACE_OVR[0] = "悟り" if u < 0.55 else "恍惚"
    j = i - 1
    img = lvl_frame(j, 4.0 + t, min(1.0, 0.8 + 0.2 * u), 5.0, text=False)
    FACE_OVR[0] = None
    view = LASTVIEW[0]
    img = img * 0.82
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    mp = proj(view, (40, FY + 51, 36) if j >= 8 else (MX, FY + 21, MZ - 4))
    if u >= 0.5 and mp:                                                    # 白い息
        rg = np.random.default_rng(5)
        e = (u - 0.5) / 0.5
        for k in range(26):
            ph = (e * 1.4 - k * 0.04)
            if ph <= 0 or ph > 1: continue
            x = mp[0] + rg.normal(0, 40) * ph + 30 * math.sin(k)
            y = mp[1] + 40 + 520 * ph
            r = 20 + 70 * ph
            d.ellipse([x - r, y - r, x + r, y + r], fill=(245, 248, 255, int(120 * (1 - ph))))
    if u < 0.5 and mp:                                                     # 吸いこむ光の線
        rg = np.random.default_rng(int(t * 20))
        for k in range(18):
            ang = rg.uniform(0, 2 * math.pi); rr = 500 * (1 - (u * 2 + k * 0.05) % 1)
            x, y = mp[0] + rr * math.cos(ang), mp[1] + rr * math.sin(ang)
            d.line([(x, y), (x + 60 * math.cos(ang), y + 60 * math.sin(ang))], fill=(255, 255, 255, 140), width=5)
    im = Image.alpha_composite(to_img(img), lay); d = ImageDraw.Draw(im)
    d.text((W / 2, 150), f"深呼吸 {i}回目", font=ft(SANS, 32), fill=(255, 255, 255, 255), anchor="mm")
    sw = smooth_(0.72, 0.88, u)
    if sw < 1:
        d.text((W / 2, 260), num(prev), font=ft(SERIF, 150), fill=(170, 170, 180, int(255 * (1 - sw))), anchor="mm")
    if sw > 0:
        d.text((W / 2, 260), num(val), font=ft(SERIF, 150 + int(30 * (1 - sw))), fill=(255, 255, 255, int(255 * sw)), anchor="mm",
               stroke_width=3, stroke_fill=(0, 0, 0, 120))
    word = "すぅーーー" if u < 0.5 else "はぁーーー"
    a = min(1, (u % 0.5) / 0.08)
    d.text((W / 2, 520), word, font=ft(SANS, 96), fill=(255, 255, 255, int(255 * a)), anchor="mm", stroke_width=8, stroke_fill=(60, 120, 200, int(255 * a)))
    return from_img(im)


def glitch_frame(t, u):
    base = lvl_frame(10, 5.0, 0.99, 5.0)
    rg = np.random.default_rng(int(t * 30) + 7)
    o = base.copy()
    for _ in range(14):
        y0 = rg.integers(0, H - 120); hh = rg.integers(20, 160); dx = rg.integers(-300, 300)
        o[y0:y0 + hh] = np.roll(base[y0:y0 + hh], dx, axis=1)
        o[y0:y0 + hh, :, rg.integers(0, 3)] = rg.random()
    o = rgbsplit(o, 20 + 30 * rg.random())
    im = to_img(o); d = ImageDraw.Draw(im)
    big = "×" + "".join(str(rg.integers(0, 10)) for _ in range(6 + int(u * 7)))
    d.rectangle([0, 80, W, 345], fill=(0, 0, 0, 255))
    hud(d, 0, 10, "エラー", (255, 40, 40), big=big)
    return from_img(im)


def zero_frame(t, u, notif=0.0, k=0):
    """×0：真っ暗な部屋。床にへたりこんだまま動かない。スマホだけ床で光る"""
    if 'z' not in _BG:
        cam, tgt, fov = camf(50, 0.45, 34, 20, MX, 40)
        def fl(c, m):
            put(c, m, 50, 56, FY, FY + 1, 28, 38, (0.1, 0.1, 0.12), 1, 0.0)
        img, view = scene3d("room", cam, tgt, fov, [lambda c, m: man(c, m, FY, "無", arms="down", phone=False, cz=40), fl])
        g = img.mean(2, keepdims=True)
        img = (g * 0.55 + img * 0.1) * np.array([0.85, 0.9, 1.05], f32)
        _BG['z'] = (img, view)
    img, view = _BG['z']
    img = img.copy()
    if notif > 0:
        p = proj(view, (53, FY + 1, 33))
        if p:
            yy, xx = np.mgrid[0:H, 0:W]
            r = np.sqrt((xx - p[0]) ** 2 + ((yy - p[1]) * 2.2) ** 2)
            img = img + (np.exp(-r / 150) * 0.8 * notif)[..., None] * np.array([0.7, 0.85, 1.0], f32)
    im = to_img(img); d = ImageDraw.Draw(im)
    hud(d, 0, 10, "ただの温かい肉の塊", (90, 90, 100))
    if notif <= 0:
        caption(d, ZERO[k], min(1, u / 0.1) * (1 if u < 0.88 else (1 - u) / 0.12))
    else:
        a = notif
        bx0, by0, bx1, by1 = 70, 430, W - 70, 600
        d.rounded_rectangle([bx0, by0, bx1, by1], radius=40, fill=(240, 240, 245, int(235 * a)))
        d.rounded_rectangle([bx0 + 30, by0 + 34, bx0 + 90, by0 + 94], radius=14, fill=(250, 70, 60, int(255 * a)))
        d.text((bx0 + 60, by0 + 64), "17", font=ft(SANS, 28), fill=(255, 255, 255, int(255 * a)), anchor="mm")
        d.text((bx0 + 115, by0 + 50), "カレンダー", font=ft(SANS, 26), fill=(110, 110, 120, int(255 * a)), anchor="lm")
        d.text((bx1 - 30, by0 + 50), "いま", font=ft(SANS, 24), fill=(110, 110, 120, int(255 * a)), anchor="rm")
        d.text((bx0 + 115, by0 + 105), "明日 9:00　1限（小テスト）", font=ft(SANS, 40), fill=(20, 20, 25, int(255 * a)), anchor="lm")
    return from_img(im)


def frame(t):
    kind, i, tt, d = seg_at(t)
    u = tt / d
    if kind == "intro":
        img = lvl_frame(0, tt, 0.0, L0, text=False)
        im = to_img(img * 0.55); dr = ImageDraw.Draw(im)
        dr.rectangle([0, 80, W, 560], fill=(0, 0, 0, 0))
        a = min(1, tt / 0.3)
        im2 = to_img(img * 0.55)
        dd = ImageDraw.Draw(im2)
        for k, (s, col) in enumerate([("深呼吸するたびに", (255, 255, 255)), ("セロトニンが", (255, 255, 255))]):
            dd.text((W / 2, 300 + k * 110), s, font=ft(SERIF, 84), fill=col + (int(255 * a),), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, 150))
        f = ft(SERIF, 84); s1, s2 = "2倍", "になったら？"
        w1, w2 = dd.textlength(s1, font=f), dd.textlength(s2, font=f)
        x0 = W / 2 - (w1 + w2) / 2
        dd.text((x0, 520), s1, font=f, fill=(250, 220, 90, int(255 * a)), anchor="lm", stroke_width=5, stroke_fill=(0, 0, 0, 150))
        dd.text((x0 + w1, 520), s2, font=f, fill=(255, 255, 255, int(255 * a)), anchor="lm", stroke_width=5, stroke_fill=(0, 0, 0, 150))
        return from_img(im2)
    if kind == "lv":
        return lvl_frame(i, tt, u, d)
    if kind == "scroll":
        return scroll_frame(i, tt, u)
    if kind == "glitch":
        return glitch_frame(tt, u)
    if kind == "zero":
        return zero_frame(tt, u, k=i)
    if kind == "notif":
        img = zero_frame(tt, 1.0, notif=min(1, tt / 0.25))
        fade = smooth_(0.62, 0.92, u)
        return img * (1 - fade)


if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        ts = [float(x) for x in sys.argv[2].split(',')]
        ims = [Image.fromarray((np.clip(frame(t), 0, 1) * 255).astype(np.uint8)).resize((216, 384)) for t in ts]
        cols = min(8, len(ims))
        sh = Image.new('RGB', (216 * cols, 384 * ((len(ims) + cols - 1) // cols)))
        for k, im in enumerate(ims):
            sh.paste(im, ((k % cols) * 216, (k // cols) * 384))
        sh.save(sys.argv[3]); print('DUR', DUR)
    elif sys.argv[1] == 'render':
        a, b, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        n0, n1 = int(round(a * FPS)), int(round(b * FPS))
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                               '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out + '.part.mp4'], stdin=subprocess.PIPE)
        for n in range(n0, n1):
            ff.stdin.write((np.clip(frame(n / FPS), 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
            if n % 60 == 0: print(n, flush=True)
        ff.stdin.close()
        if ff.wait() == 0:
            os.replace(out + '.part.mp4', out); print('done', out, flush=True)
    else:
        print(DUR, list(zip([s[0] + str(s[1]) for s in SEG], [round(x, 2) for x in STARTS])))
