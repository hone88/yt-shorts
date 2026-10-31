"""ループドラマ 第1話。python3 ep1.py still <shot> <t> | python3 ep1.py build"""
import math, os, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E
from engine import Person, lerp, ease
import scenes as SC

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, SR = 1080, 1920, 30, 24000
BLACK, BOLD = E.FONT_BLACK, E.FONT_BOLD
E.MATS["hoodie"] = ((214, 62, 62), (192, 50, 52), "flat")
E.MATS["navyp"] = ((44, 54, 92), (38, 46, 80), "flat")
E.MATS["night_road"] = ((60, 62, 72), (60, 62, 72), "noise")


def F(p, s):
    return E.font(p, s)


# ---------- 声 ----------
def wav(id_):
    p = f"{HERE}/voice/ep1/{id_}.wav"
    with wave.open(p) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a


VO = {}


def vo(id_):
    if id_ not in VO:
        VO[id_] = wav(id_)
    return VO[id_]


def L(id_):
    return len(vo(id_)) / SR


SPEAK = {"K": ("カナタ", (230, 90, 90)), "M": ("ミオ", (255, 138, 31)), "T": ("トケイ", (250, 204, 60))}
TEXT = {
    "01": ("K", "…え、[止まってる]？"),
    "03a": ("M", "今日10時から、ドットジェイピーの説明会あるよ。来る？"),
    "03b": ("K", "…[めんど]。"),
    "04": ("K", "春休みなんて、|まだ先だし。"),
    "05a": ("T", "今日も、|[なにもしなかった]のだ。"),
    "05b": ("K", "と、[時計]が|しゃべった！？"),
    "06a": ("T", "ルールを言うのだ。|なにもしない日は、[朝に戻る]。"),
    "06b": ("T", "抜け出す方法は|[広島県知事]に会うこと"),
    "06c": ("K", "[知事]！？|無理に決まってるだろ！"),
    "06d": ("T", "残りは、[18回]なのだ。"),
    "08": ("K", "…また、[12月5日]？"),
}


# ---------- 人と物 ----------
def kanata(x, y, facing="x"):
    return Person(x, y, 1, facing, "hoodie", "navyp", "hair", "skin")


def kanata_extras(p):
    """ヘッドホンと寝ぐせ"""
    bx = p.boxes()
    if not bx:
        return []
    hx, hy, hz, hs = bx[-1][:4]
    m = 0.11 * p.scale
    out = [(hx + hs / 2 - m / 2, hy + hs / 2 - m / 2, hz + hs, m * 1.3, "hair")]  # 寝ぐせ
    for dx, dy in ((-0.06, hs / 2 - m / 2), (hs - 0.04, hs / 2 - m / 2)) if p.facing in ("y", "-y") else ((hs / 2 - m / 2, -0.06), (hs / 2 - m / 2, hs - 0.04)):
        out.append((hx + dx, hy + dy, hz - 0.08, m * 1.4, "black"))
    return out


def tokei(cx, cy, cz, t, eyes=True):
    """宙に浮く目覚まし時計。cz は本体の下の高さ"""
    z = cz + 0.15 * math.sin(t * 3)
    m = 0.22
    out = []
    for i in range(3):
        for k in range(3):
            out.append((cx + i * m, cy, z + k * m, m, "yellow"))
            out.append((cx + i * m, cy - m, z + k * m, m, "yellow"))
    # 文字盤（+y 側に白い板）
    for i in range(3):
        for k in range(3):
            out.append((cx + i * m + 0.03, cy + m * 0.75, z + k * m + 0.03, m * 0.75, "paper"))
    out.append((cx + m + 0.07, cy + m * 1.35, z + m * 1.1, 0.09, "black"))
    out.append((cx + m + 0.07, cy + m * 1.35, z + m * 1.45, 0.09, "black"))
    if eyes:
        out.append((cx + 0.12, cy + m * 1.4, z + m * 1.75, 0.1, "black"))
        out.append((cx + m * 2.1, cy + m * 1.4, z + m * 1.75, 0.1, "black"))
    out.append((cx - 0.05, cy - m * 0.5, z + 3 * m, 0.26, "gold"))
    out.append((cx + 2 * m + 0.05, cy - m * 0.5, z + 3 * m, 0.26, "gold"))
    out.append((cx + 0.05, cy - m * 0.5, z - 0.12, 0.12, "black"))
    out.append((cx + 2 * m + 0.1, cy - m * 0.5, z - 0.12, 0.12, "black"))
    return out


# ---------- 場所 ----------
def build_room():
    S = []
    SC.island(S, 0, 0, 8, 8, top="wood", side_depth=1)
    for x in range(8):
        for z in range(1, 4):
            S.append((x, -1, z, 1, "glass" if (z == 2 and x in (2, 3)) else "cream"))
    for y in range(8):
        for z in range(1, 4):
            S.append((-1, y, z, 1, "cream"))
    for x in (4, 5, 6):
        for y in (0, 1):
            S.append((x, y, 1, 1, "white"))
    for x in (5, 6):
        for y in (0, 1):
            S.append((x, y, 2, 1, "blue"))
    S.append((4, 0, 2, 1, "white"))
    S += [(0, 3, 1, 1, "darkwood"), (0, 4, 1, 1, "darkwood"), (0, 3, 2, 1, "black"), (0, 4, 2, 1, "black")]
    S += [(6, 6, 1, 1, "leaves"), (6, 6, 2, 1, "leaves")]
    S.append((3, 0, 1, 1, "darkwood"))  # 目覚まし置き台
    return E.cull(S)


def build_street():
    S = []
    SC.island(S, -2, 0, 22, 11, top="sand", side_depth=1)
    for x in range(-2, 20):
        for y in (4, 5):
            S.append((x, y, 0, 1, "night_road"))
        if x % 3 == 0:
            S.append((x + 0.3, 4.8, 0.62, 0.4, "line"))
    rnd = random.Random(3)
    for x0 in range(-2, 18, 4):
        if x0 == 6:
            SC.building(S, x0, 0, 4, 3, 2, "white", "gray", "lamp")    # 店
        else:
            SC.building(S, x0, 0, 3, 3, rnd.randint(3, 5), rnd.choice(["gray", "brick", "cream"]), rnd.choice(["navy", "black", "gray"]), "lamp" if rnd.random() < 0.6 else "glass")
    for x in (-1, 5, 11, 17):
        S += [(x, 3, 1, 1, "gray"), (x, 3, 2, 1, "gray")]
    return E.cull(S)


ROOM = build_room()
STREET = build_street()


def street_people(t, tfreeze):
    te = min(t, tfreeze)
    ppl = []
    specs = [(3.3, -1, "t_red", "jeans", "hair2", 0.0), (6.6, 1, "coat_w", "skirt", "hair", 4.0), (3.0, 1, "suit", "suit", "hair3", 9.0), (7.7, -1, "t_green", "jeans", "hair", 2.0)]
    for i, (y, d, sh, pa, ha, off) in enumerate(specs):
        x = (off + d * te * 1.1) % 18 - 1 if d > 0 else (off + 18 - (te * 1.1) % 18) % 18 - 1
        p = Person(x, y, 1, "x" if d > 0 else "-x", sh, pa, ha, "skin", 1.0, pa == "skirt")
        p.walk = 1
        p.phase = te * 9 + i
        ppl.append(p)
    lamps = [((x + 0.2, 3.2, 3, 0.6, "lamp")) for x in (-1, 5, 11, 17)]
    return ppl, lamps


# ---------- 描画 ----------
SKY_NIGHT = E.sky((14, 18, 44), (52, 46, 96))
_rnd = random.Random(5)
STARS = [(_rnd.uniform(0, W), _rnd.uniform(0, 900), _rnd.uniform(1.5, 3.5)) for _ in range(70)]


def sky_for(hour):
    """部屋の窓の外＝背景。8時〜24時を昼→夕→夜に"""
    keys = [(8, (120, 190, 245), (205, 235, 255)), (15, (110, 180, 240), (200, 230, 255)), (18, (250, 150, 110), (255, 220, 170)), (20, (40, 44, 100), (110, 90, 150)), (24, (14, 18, 44), (52, 46, 96))]
    for (h0, a0, b0), (h1, a1, b1) in zip(keys, keys[1:]):
        if hour <= h1:
            u = (hour - h0) / (h1 - h0)
            return tuple(int(lerp(p, q, u)) for p, q in zip(a0, a1)), tuple(int(lerp(p, q, u)) for p, q in zip(b0, b1))
    return keys[-1][1], keys[-1][2]


_sky_cache = {}


def sky_img(hour):
    k = round(hour * 4) / 4
    if k not in _sky_cache:
        _sky_cache[k] = E.sky(*sky_for(k))
    return _sky_cache[k]


def render_boxes(bg, boxes, cam):
    img = bg.copy()
    E.draw_boxes(img, boxes, cam)
    return img


def desat(img, k, keep=None):
    if k <= 0:
        return img
    g = ImageOps.grayscale(img.convert("RGB")).convert("RGBA")
    g = Image.blend(img, g, min(1, k))
    if keep is not None:
        g.paste(img, (0, 0), keep)
    return g


def keep_mask(boxes, cam):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    E.draw_boxes(lay, boxes, cam)
    return lay.getchannel("A")


def badge(img, text, x, y, bg=(20, 26, 56), fg=(255, 255, 255), size=40, anchor="l"):
    f = F(BLACK, size)
    w = f.getlength(text) + 44
    h = size + 26
    if anchor == "r":
        x = x - w
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=bg)
    d.text((x + 22, y + 9), text, font=f, fill=fg)
    return w


def clock_big(img, date, time_, flash=0.0):
    """上中央に大きく日付と時刻。タイムリープを意識させる"""
    d = ImageDraw.Draw(img)
    fd, ft = F(BLACK, 58), F(BLACK, 170)
    wd, wt = fd.getlength(date), ft.getlength(time_)
    w = max(wd, wt) + 80
    x0, y0 = 540 - w / 2, 150
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle([x0, y0, x0 + w, y0 + 300], radius=40, fill=(10, 12, 30, 200))
    img.alpha_composite(lay)
    d.text((540 - wd / 2, y0 + 18), date, font=fd, fill=(255, 255, 255))
    col = (255, 216, 77) if flash <= 0 else (255, 80, 80)
    d.text((540 - wt / 2, y0 + 78), time_, font=ft, fill=col, stroke_width=6, stroke_fill=(10, 12, 30))


def counter(img, n, pulse=0.0):
    f = F(BLACK, 40)
    txt = f"残りループ {n}"
    w = f.getlength(txt) + 96
    x1, y = 1024, 128
    x = x1 - w
    d = ImageDraw.Draw(img)
    col = (250, 204, 60)
    d.rounded_rectangle([x, y, x1, y + 66], radius=33, fill=(20, 26, 56), outline=col if pulse > 0 else None, width=int(3 + 5 * pulse))
    d.rounded_rectangle([x + 18, y + 15, x + 54, y + 51], radius=6, fill=col)
    d.ellipse([x + 24, y + 21, x + 48, y + 45], fill=(250, 250, 245))
    d.line([x + 36, y + 33, x + 36, y + 24], fill=(30, 30, 30), width=3)
    d.line([x + 36, y + 33, x + 43, y + 33], fill=(30, 30, 30), width=3)
    d.text((x + 68, y + 9), txt, font=f, fill=col if pulse > 0 else (255, 255, 255))


def caption(img, text, y=430, t=1.0, size=92, col=(255, 255, 255)):
    im = E.fit_text(text.split("\n"), size, 980, fill=col, stroke=(8, 10, 24), sw=10)
    E.paste_center(img, im, 540, y, E.pop(t))


def rich_line(d, cx, y, line, font, base=(255, 255, 255), hl=(255, 216, 77)):
    parts, cur, on = [], "", False
    for ch in line:
        if ch in "[]":
            if cur:
                parts.append((cur, on))
            cur, on = "", ch == "["
        else:
            cur += ch
    if cur:
        parts.append((cur, on))
    w = sum(font.getlength(p) for p, _ in parts)
    x = cx - w / 2
    for p, on in parts:
        d.text((x, y), p, font=font, fill=hl if on else base, stroke_width=10, stroke_fill=(8, 8, 18))
        x += font.getlength(p)


def subtitle(img, sid):
    who, text = TEXT[sid]
    name, col = SPEAK[who]
    lines = text.split("|")
    d = ImageDraw.Draw(img)
    f = F(BLACK, 76)
    fn = F(BLACK, 40)
    y = 1380 - (len(lines) - 1) * 96
    nw = fn.getlength(name) + 40
    d.rounded_rectangle([540 - nw / 2, y - 78, 540 + nw / 2, y - 18], radius=30, fill=col)
    d.text((540 - nw / 2 + 20, y - 74), name, font=fn, fill=(20, 20, 30))
    for i, ln in enumerate(lines):
        ff = f
        while ff.getlength(ln.replace("[", "").replace("]", "")) > 1000:
            ff = F(BLACK, ff.size - 4)
        rich_line(d, 540, y + i * 96, ln, ff)


def subtitle_old(img, sid):
    who, text = TEXT[sid]
    name, col = SPEAK[who]
    lines = text.split("|")
    f = F(BOLD, 50)
    fn = F(BLACK, 34)
    y = 1470 - (len(lines) - 1) * 34
    d = ImageDraw.Draw(img)
    nw = fn.getlength(name) + 34
    d.rounded_rectangle([540 - nw / 2, y - 62, 540 + nw / 2, y - 12], radius=25, fill=col)
    d.text((540 - nw / 2 + 17, y - 59), name, font=fn, fill=(20, 20, 30))
    for i, ln in enumerate(lines):
        size = 50
        while F(BOLD, size).getlength(ln) > 990:
            size -= 2
        ff = F(BOLD, size)
        d.text((540 - ff.getlength(ln) / 2, y + i * 68), ln, font=ff, fill="white", stroke_width=7, stroke_fill=(5, 5, 15))


def phone_bubble(img, u):
    """ミオのメッセージ。u: 0→1 でせり上がる"""
    if u <= 0:
        return
    e = ease(u)
    x0, y0 = 120, 1060 + (1 - e) * 120
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([x0, y0, W - 120, y0 + 250], radius=36, fill=(250, 250, 250, int(240 * e)))
    d.ellipse([x0 + 28, y0 + 28, x0 + 96, y0 + 96], fill=(255, 138, 31, int(255 * e)))
    d.text((x0 + 50, y0 + 38), "ミ", font=F(BLACK, 36), fill=(255, 255, 255, int(255 * e)))
    d.text((x0 + 116, y0 + 36), "ミオ", font=F(BLACK, 36), fill=(40, 40, 50, int(255 * e)))
    d.text((x0 + 116, y0 + 96), "今日10時から、ドットジェイピー", font=F(BOLD, 40), fill=(40, 40, 50, int(255 * e)))
    d.text((x0 + 116, y0 + 150), "の説明会あるよ。来る？", font=F(BOLD, 40), fill=(40, 40, 50, int(255 * e)))
    img.alpha_composite(lay)


def rule_card(img, n_lines, u):
    if u <= 0:
        return
    e = ease(u)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    y0 = 500
    d.rounded_rectangle([40, y0, W - 40, y0 + 640], radius=44, fill=(10, 12, 30, int(235 * e)), outline=(255, 216, 77, int(255 * e)), width=8)
    a = int(255 * e)
    ft, fb = F(BLACK, 64), F(BLACK, 66)
    d.text((540 - ft.getlength("ループのルール") / 2, y0 + 34), "ループのルール", font=ft, fill=(255, 216, 77, a))
    rows = [("①", ["なにもしない日は", "[朝に戻る]"]), ("②", ["春休み中に", "[広島県知事]に会え"])]
    for i in range(n_lines):
        mk, ls = rows[i]
        y = y0 + 150 + i * 240
        d.text((90, y), mk, font=F(BLACK, 80), fill=(255, 216, 77, a))
        for j, ln in enumerate(ls):
            x = 190
            on = False
            cur = ""
            for ch in ln + "\0":
                if ch in "[]\0":
                    if cur:
                        d.text((x, y + j * 92), cur, font=fb, fill=((255, 90, 90, a) if on else (255, 255, 255, a)))
                        x += fb.getlength(cur)
                    cur = ""
                    on = ch == "["
                else:
                    cur += ch
    img.alpha_composite(lay)


def glitch(img, k, seed):
    """横線ノイズと色ずれ"""
    if k <= 0:
        return img
    rnd = random.Random(seed)
    r, g, b, a = img.split()
    s = int(14 * k)
    r = r.transform(img.size, Image.AFFINE, (1, 0, s, 0, 1, 0))
    b = b.transform(img.size, Image.AFFINE, (1, 0, -s, 0, 1, 0))
    out = Image.merge("RGBA", (r, g, b, a))
    d = ImageDraw.Draw(out)
    for _ in range(int(14 * k)):
        y = rnd.uniform(0, H)
        d.rectangle([0, y, W, y + rnd.uniform(2, 10)], fill=(255, 255, 255, int(rnd.uniform(40, 120) * k)))
    for _ in range(int(5 * k)):
        y = int(rnd.uniform(0, H - 60))
        hgt = int(rnd.uniform(20, 70))
        band = out.crop((0, y, W, y + hgt))
        out.paste(band, (int(rnd.uniform(-60, 60) * k), y))
    return out


def cracks(img, k, seed=7):
    if k <= 0:
        return
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img)
    cx, cy = 560, 980
    for i in range(11):
        a = i / 11 * 2 * math.pi + rnd.uniform(-0.2, 0.2)
        x, y = cx, cy
        L_ = 900 * k
        n = 6
        for j in range(n):
            nx = x + math.cos(a + rnd.uniform(-0.5, 0.5)) * L_ / n
            ny = y + math.sin(a + rnd.uniform(-0.5, 0.5)) * L_ / n
            d.line([x, y, nx, ny], fill=(255, 255, 255), width=max(2, int(7 - j)))
            x, y = nx, ny


# ---------- ショット ----------
class Shot:
    def __init__(self, name, dur, lines=(), sfx=()):
        self.name, self.dur, self.lines, self.sfx = name, dur, list(lines), list(sfx)


def plan():
    P = []
    # 1 つかみ
    t1 = 0.95
    P.append(Shot("cold", t1 + L("01") + 0.45, [(t1, "01")], [(0.3, "thud")]))
    P.append(Shot("rewind1", 1.6, [], [(0.0, "rewind")]))
    a = 1.4
    b = a + L("03a") + 0.35
    P.append(Shot("room", b + L("03b") + 0.7, [(a, "03a"), (b, "03b")], [(0.15, "alarm")]))
    P.append(Shot("lapse", 0.4 + L("04") + 1.6, [(0.4, "04")], []))
    a = 1.45
    b = a + L("05a") + 0.3
    P.append(Shot("tokei", b + L("05b") + 0.5, [(a, "05a"), (b, "05b")], [(0.35, "thud"), (1.0, "chime")]))
    t = 0.2
    lines = []
    for i in ("06a", "06b", "06c", "06d"):
        lines.append((t, i))
        t += L(i) + (0.35 if i != "06c" else 0.25)
    P.append(Shot("rules", t + 0.9, lines, [(lines[-1][0] + 0.2, "ding")]))
    P.append(Shot("rewind2", 2.4, [], [(0.0, "crack"), (0.35, "rewind")]))
    a = 1.4
    b = a + L("03a") + 0.6
    P.append(Shot("room2", b + L("08") + 1.2, [(a, "03a"), (b, "08")], [(0.15, "alarm")]))
    P.append(Shot("end", 4.6, [], [(0.1, "chime")]))
    t = 0
    for s in P:
        s.start = t
        t += s.dur
    return P


SH = None


def shot(name):
    return next(s for s in SH if s.name == name)


def speaking(s, t):
    cur = None
    for (t0, sid) in s.lines:
        if t0 <= t <= t0 + L(sid) + 0.15:
            cur = sid
    return cur


def frame(s, t, raw=False):
    """raw=True は巻き戻し用：文字や吹き出しを付けない"""
    n = s.name
    img = None
    if n in ("cold", "tokei", "rules"):
        tf = {"cold": 0.3, "tokei": 0.35, "rules": -1}[n]
        frozen = t >= tf if tf >= 0 else True
        ppl, lamps = street_people((t if n == "cold" else 5 + t) if not frozen else 0, 0 if n == "rules" else (tf if n == "cold" else 5 + tf))
        k = kanata(4.3, 6.5, "x")
        if n == "cold":
            k.facing = "x" if (t % 1.6) < 0.8 or t < tf else "y"
        elif n == "tokei":
            k.x = 4.3 + min(t, tf) * 1.1
            k.walk = 1 if t < tf else 0
            k.phase = t * 9
            if s.lines and t > s.lines[1][0]:
                k.jump = max(0, math.sin((t - s.lines[1][0]) * 8)) * 0.4 if t - s.lines[1][0] < 0.4 else 0
                k.facing = "y"
        else:
            k.x = 4.3 + 0.35 * 1.1
            k.facing = "y"
            sid = speaking(s, t)
            if sid == "06c":
                k.arm_up = (0.9, 0.9)
                k.jump = abs(math.sin(t * 9)) * 0.15
        boxes = list(STREET)
        for p in ppl:
            boxes += p.boxes()
        boxes += lamps
        kb = k.boxes() + kanata_extras(k) + [(k.x + 0.25, k.y - 0.1, 1.4, 0.3, "white")]
        tk = []
        if n == "tokei" and t > 1.0:
            tk = tokei(k.x + 1.4, k.y + 0.4, 2.2 + (1 - ease((t - 1.0) / 0.4)) * 1.2, t, eyes=speaking(s, t) == "05a")
        if n == "rules":
            tk = tokei(k.x + 1.4, k.y + 0.4, 2.2, t + 5, eyes=speaking(s, t) in ("06a", "06b", "06d"))
        boxes += kb + tk
        if n == "cold":
            cam = E.Cam(lerp(84, 104, ease(t / s.dur)), 4.6, 6.7, 1.7)
            dk = ease((t - tf) / 1.0) if frozen else 0
        elif n == "tokei":
            cam = E.Cam(lerp(88, 104, ease(t / s.dur)), k.x + 0.8, 6.8, 1.9)
            dk = ease((t - tf) / 0.4) if frozen else 0
        else:
            cam = E.Cam(118, k.x + 0.85, 6.8, 2.0)
            dk = 1
        bg = SKY_NIGHT.copy()
        d = ImageDraw.Draw(bg)
        for (x, y, r) in STARS:
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 230))
        img = render_boxes(bg, boxes, cam)
        if dk > 0:
            img = desat(img, dk * 0.92, keep_mask(kb + tk, cam))
            if 0 < t - tf < 0.25:
                img = Image.blend(img, Image.new("RGBA", (W, H), (255, 255, 255, 255)), 0.35 * (1 - (t - tf) / 0.25))
    elif n in ("room", "room2", "lapse"):
        if n == "lapse":
            hour = lerp(10, 23.9, t / s.dur)
        else:
            hour = 8
        k = kanata(3.3, 2.6, "x")
        tvon = n == "lapse"
        if n in ("room", "room2"):
            first = s.lines[0][0]
            k.facing = "x"
            k.arm_up = (0.35, 0)
            if n == "room" and t > s.lines[1][0]:
                k.facing = "-x"
                k.arm_up = (0, 0)
            if n == "room2" and t > s.lines[1][0] - 0.3:
                k.arm_up = (0.35, 0)
                k.bob = 0
        else:
            k.x, k.y = 2.0, 3.6
            k.facing = "-x"
            k.arm_up = (0.3, 0.3)
            k.bob = 0.02 * math.sin(t * 6)
        boxes = list(ROOM) + k.boxes() + kanata_extras(k)
        if n != "lapse":
            ring = (int(t * 8) % 2 == 0) and t < 1.6
            boxes.append((3.2, 0.2, 2.0 + (0.05 if ring else 0), 0.5, "yellow"))
            boxes.append((3.32, 0.62, 2.12, 0.26, "lamp" if ring else "paper"))
            if k.arm_up[0] > 0:
                boxes.append((k.x + 0.12, k.y - 0.45, 1.78, 0.22, "black"))
        else:
            c = ["blue", "red", "green", "yellow"][int(t * 3) % 4]
            boxes += [(0.55, 3.1, 2.1, 0.5, c), (0.55, 3.9, 2.1, 0.5, c)]
            boxes += [(1.4, 4.4, 1.0, 0.3, "red"), (1.6, 2.7, 1.0, 0.3, "yellow")]
        if n == "lapse":
            cam = E.Cam(60, 3.6, 3.6, 1.2)
        else:
            cam = E.Cam(lerp(56, 66, ease(t / s.dur)), 3.6, 2.8, 1.4)
        img = render_boxes(sky_img(hour), boxes, cam)
    elif n == "end":
        img = Image.new("RGBA", (W, H), (12, 14, 32, 255))
        cam = E.Cam(150, 0.4, 0.2, 1.6, 540, 820)
        E.draw_boxes(img, tokei(0, 0, 1.0, t, eyes=True), cam)
    elif n in ("rewind1", "rewind2"):
        if n == "rewind1":
            src = shot("cold")
            u = ease(t / s.dur)
            base = frame(src, src.dur * (1 - u), raw=True)
            base = desat(base, 0.9)
            img = glitch(base, 0.9, int(t * 30))
        else:
            seq = [shot("rules"), shot("tokei"), shot("lapse"), shot("room")]
            if t < 0.35:
                img = frame(shot("rules"), shot("rules").dur - 0.05, raw=True)
                img = desat(img, 1)
                cracks(img, ease(t / 0.35))
            else:
                u = (t - 0.35) / (s.dur - 0.6)
                if u < 1:
                    idx = min(3, int(u * 4))
                    v = u * 4 - idx
                    src = seq[idx]
                    img = frame(src, src.dur * (1 - v), raw=True)
                    img = glitch(desat(img, 1), 1.0, int(t * 30))
                else:
                    w = (t - (s.dur - 0.25)) / 0.25
                    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
                    if w > 0:
                        img = Image.blend(img, frame(shot("room2"), 0, raw=True), min(1, w))
    if raw:
        return img
    # ---- 文字 ----
    d = ImageDraw.Draw(img)
    if n == "cold":
        clock_big(img, "12月5日（土）", "23:59", flash=1 if t > 0.3 else 0)
        caption(img, "世界が、止まった。", 560, t - 0.2, size=96)
    elif n == "rewind1":
        caption(img, "16時間前", 900, t, size=140, col=(255, 255, 255))
    elif n in ("room", "room2"):
        clock_big(img, "12月5日（土）", "8:00")
        if n == "room2":
            counter(img, 18)
        first = s.lines[0][0]
        phone_bubble(img, (t - (first - 0.25)) / 0.3)
    elif n == "lapse":
        hour = lerp(10, 23.9, t / s.dur)
        clock_big(img, "12月5日（土）", f"{int(hour)}:{int((hour % 1) * 60):02d}")
        caption(img, "なにもしない一日", 560, t)
    elif n in ("tokei", "rules"):
        if n == "tokei":
            clock_big(img, "12月5日（土）", "23:59", flash=1)
        if n == "rules":
            t6b = s.lines[1][0]
            nl = 1 if t < t6b else 2
            fade = 1 - ease((t - (s.lines[2][0] - 0.2)) / 0.3)
            rule_card(img, nl, min(ease((t - 0.25) / 0.3), fade))
            t6d = s.lines[3][0]
            if t > t6d:
                counter(img, 18, pulse=max(0, 1 - (t - t6d) / 0.8))
    elif n == "rewind2":
        if 0.35 < t < s.dur - 0.25:
            caption(img, "◀◀", 960, 1.0, size=160)
    elif n == "end":
        caption(img, "次回", 300, t, size=56, col=(250, 204, 60))
        caption(img, "第2話\n「知事って、どうやって会うの？」", 470, t - 0.15, size=74)
        im = E.fit_text(["あなたの春休みは、まだ巻き戻せる。"], 50, 980, sw=6, path=BOLD)
        E.paste_center(img, im, 540, 1180)
        im = E.fit_text(["ドットジェイピー広島第一支部", "春インターン申込は12月31日まで"], 46, 980, sw=6, path=BOLD, fill=(255, 216, 77))
        E.paste_center(img, im, 540, 1320)
        im = E.fit_text(["この物語はフィクションです"], 28, 980, sw=4, path=BOLD, fill=(180, 186, 210))
        E.paste_center(img, im, 540, 1450)
    sid = speaking(s, t)
    if sid and n != "end" and sid != "03a":
        subtitle(img, sid)
    return img


# ---------- 音 ----------
def sfx(kind):
    def tt(sec):
        return np.arange(int(sec * SR)) / SR
    if kind == "thud":
        x = tt(0.9)
        y = np.sin(2 * np.pi * 55 * x) * np.exp(-x * 5) + np.random.RandomState(1).randn(len(x)) * 0.15 * np.exp(-x * 25)
        return y * 0.9
    if kind == "alarm":
        out = []
        for _ in range(3):
            for _ in range(4):
                x = tt(0.07)
                out.append(np.sign(np.sin(2 * np.pi * 1800 * x)) * 0.18)
                out.append(np.zeros(int(0.05 * SR)))
            out.append(np.zeros(int(0.22 * SR)))
        return np.concatenate(out)
    if kind == "rewind":
        x = tt(1.4)
        f = 1400 * np.exp(-x * 1.6) + 120
        ph = 2 * np.pi * np.cumsum(f) / SR
        n = np.random.RandomState(2).randn(len(x))
        return (0.25 * np.sin(ph) + 0.18 * n * np.linspace(1, 0.2, len(x))) * np.minimum(1, x * 20)
    if kind == "crack":
        x = tt(0.5)
        n = np.random.RandomState(3).randn(len(x))
        return n * np.exp(-x * 12) * 0.6
    if kind in ("chime", "ding"):
        x = tt(1.6 if kind == "chime" else 1.0)
        base = 880 if kind == "chime" else 1320
        y = sum(np.sin(2 * np.pi * base * r * x) / (i + 1) for i, r in enumerate((1, 2.0, 3.0)))
        return y * np.exp(-x * 3) * 0.25
    raise ValueError(kind)


def mix(P):
    total = sum(s.dur for s in P)
    buf = np.zeros(int(total * SR) + SR)
    for s in P:
        for (t0, sid) in s.lines:
            a = vo(sid)
            i = int((s.start + t0) * SR)
            buf[i:i + len(a)] += a
        for (t0, k) in s.sfx:
            a = sfx(k)
            i = int((s.start + t0) * SR)
            buf[i:i + len(a)] += a * 0.8
    buf = buf[:int(total * SR)]
    buf /= max(1e-6, np.abs(buf).max()) / 0.95
    p = f"{HERE}/out/mix.wav"
    with wave.open(p, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((buf * 32767).astype(np.int16).tobytes())
    return p


def render_shot(i):
    s = SH[i]
    n = int(round(s.dur * FPS))
    out = f"{HERE}/out/{i:02d}_{s.name}.mp4"
    tmp = out[:-4] + ".part.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for k in range(n):
        p.stdin.write(frame(s, k / FPS).convert("RGB").tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, out)
    return out, n


SH = plan()

if __name__ == "__main__":
    os.makedirs(f"{HERE}/out", exist_ok=True)
    if sys.argv[1] == "still":
        s = shot(sys.argv[2])
        frame(s, float(sys.argv[3])).convert("RGB").save(f"{HERE}/still_{sys.argv[2]}.png")
    elif sys.argv[1] == "build":
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(2) as ex:
            res = list(ex.map(render_shot, range(len(SH))))
        # 各ショットのフレーム数に合わせて start を補正
        t = 0
        for s, (_, n) in zip(SH, res):
            s.start = t
            s.dur = n / FPS
            t += s.dur
        open(f"{HERE}/out/list.txt", "w").write("".join(f"file '{o}'\n" for o, _ in res))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{HERE}/out/list.txt", "-c", "copy", f"{HERE}/out/video.mp4"], check=True)
        a = mix(SH)
        final = f"{HERE}/out/残りループ18回_第1話.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{HERE}/out/video.mp4", "-i", a, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "160k", "-shortest", final + ".part.mp4"], check=True)
        os.replace(final + ".part.mp4", final)
        print("done", round(t, 2))
