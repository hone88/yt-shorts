"""ガクチカ・ループ 第6話「キックオフ」（2周目・2027年1月30日）
冒頭の事件：名刺の練習で、カナタだけ片手で逆さまに渡す。（11/7 ゆうきさんの指示で作り直し：同じ班・距離・読み上げ・キラキラ・向かい合うハイタッチ・哀愁の帰り道・引きの画）
マナー研修（お辞儀・名刺）→ 目標づくり（カナタ「…面接で答える。」／ハルト「地元の子どもの、居場所をつくりたい。」）
→ ミニゲーム（共通点探し）でハイタッチ → 帰り道、トケイ「来週から、いよいよインターンなのだ。」
python3 ep6.py still <shot> <t> | python3 ep6.py build"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import g3d as G
from g3d import Camera, Rig, render, hexc
import characters as C
import ep1b as O
import ep1c as P
import ep2 as Q
import ep3 as R
import ep4 as F
import ep5 as V5
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep6"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED, GRN = (255, 216, 77), (255, 90, 90), (90, 220, 120)
DATE = "2027年1月30日（土）"
O.SPEAK["H"] = ("ハルト", (110, 200, 130))

# ---------- 声 ----------
VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep6/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("M", "カナタ、|名刺、[逆さま]！"),
    "02": ("M", "名刺は、[相手が読める向き]で、|[両手]でね。"),
    "03": ("M", "じゃあ次は、[班]のみんなと、|名刺交換してみよう。"),
    "04": ("H", "ハルトです。|よろしく。"),
    "05": ("K", "…宇野です。|よろしく。"),
    "06": ("H", "人前で自分の考えを、|伝えられるようになる。|…[面接で答える]。"),
    "07": ("H", "…[正直]だな。"),
    "08": ("K", "…お前は？"),
    "09": ("H", "俺は、地元の子どもの、|[居場所]をつくりたい。"),
    "10": ("H", "よし、[共通点]、|5個そろった！"),
    "11": ("K", "（…ちゃんと[目標]があるんだな、こいつ。|ぼくとは、[違う]。）"),
    "12": ("T", "来週から、いよいよ|[インターン]なのだ。"),
    "13": ("K", "…ぼくの目標、|[あれでよかった]のかな。"),
}
GOAL_K = ["人前で自分の考えを", "伝えられるようになる。", "面接で答える。"]
GOAL_H = ["地元の子どもの、", "居場所をつくりたい。"]


def subtitle(img, sid):
    who, text = TEXT[sid]
    name, col = O.SPEAK[who]
    lines = text.split("|")
    d = ImageDraw.Draw(img)
    f, fn = O.F(BLACK, 72), O.F(BLACK, 40)
    y = 1400 - (len(lines) - 1) * 90
    nw = fn.getlength(name) + 40
    d.rounded_rectangle([540 - nw / 2, y - 78, 540 + nw / 2, y - 18], radius=30, fill=col)
    d.text((540 - nw / 2 + 20, y - 74), name, font=fn, fill=(20, 20, 30))
    for i, ln in enumerate(lines):
        ff = f
        while ff.getlength(ln.replace("[", "").replace("]", "")) > 1000:
            ff = O.F(BLACK, ff.size - 4)
        O.rich_line(d, 540, y + i * 90, ln, ff)


# ---------- 割り付け ----------
def seq(ids, start=0.4, gap=0.22, extra=None):
    out, t = [], start
    for i in ids:
        t += (extra or {}).get(i, 0)
        out.append((t, i))
        t += L(i) + gap
    return out, t


def plan():
    S = []
    ln, t = seq(["01"], 0.35)
    S.append(O.Shot("cold", max(t + 0.5, 4.6), ln))
    ln, t = seq(["02"], 0.5)
    S.append(O.Shot("rule", t + 0.8, ln))
    ln, t = seq(["03"], 0.6)
    S.append(O.Shot("han", t + 1.4, ln))                  # 班分け：同じ班にハルト
    ln, t = seq(["04", "05"], 1.6, extra={"05": 0.7})     # 立って、向かい合って名刺交換（長め）
    S.append(O.Shot("card", t + 1.0, ln))
    ln, t = seq(["06", "07", "08"], 2.0, extra={"07": 0.5, "08": 0.4})   # 書く → ハルトが横から読み上げる
    S.append(O.Shot("goal", t + 0.4, ln))
    ln, t = seq(["09"], 1.0)                              # 声の前に間
    S.append(O.Shot("dream", t + 2.2, ln))                # キラキラ → 圧倒されるカナタ
    ln, t = seq(["10"], 0.5)
    s = O.Shot("game", t + 1.6, ln); s.hi = ln[0][0] + L("10") + 0.2; S.append(s)
    ln, t = seq(["11"], 0.6)
    S.append(O.Shot("think", t + 0.8, ln))
    ln, t = seq(["12", "13"], 1.2, extra={"13": 1.4})     # 哀愁：間をたっぷり
    S.append(O.Shot("street", t + 2.0, ln))
    S.append(O.Shot("end", 5.0))
    t = 0
    for s in S:
        n = int(round(s.dur * FPS)); s.start, s.dur = t, n / FPS; t += s.dur
    return S


SH = plan()


def shot(name):
    return next(s for s in SH if s.name == name)


def speaking(s, t):
    cur = None
    for (t0, sid) in s.lines:
        if t0 <= t <= t0 + L(sid) + 0.15:
            cur = sid
    return cur


# ---------- 会場（大部屋・テーブル6つ） ----------
TABLES = [(1.6, 3.0), (5.0, 3.0), (8.4, 3.0), (1.6, 6.4), (5.0, 6.4), (8.4, 6.4)]
SEATS = [(-0.45, -0.8), (0.45, -0.8), (-0.45, 0.8), (0.45, 0.8)]   # 1つのテーブルに4人（班）


def hall_set():
    S = []
    S += P.blocks(-1, 11, -3, 12, -1, 0, hexc("#c8b898"), 0.05, 61)          # 床
    S += P.blocks(-1, 11, 12, 13, 0, 4, hexc("#eef2f4"), 0.02, 62)            # 前の壁
    S += P.blocks(-2, -1, -3, 12, 0, 4, hexc("#e8eef2"), 0.02, 63)
    S += P.blocks(11, 12, -3, 12, 0, 4, hexc("#e8eef2"), 0.02, 64)
    S += P.blocks(-1, 11, -4, -3, 0, 4, hexc("#e8eef2"), 0.02, 65)
    S.append(P.slab(2.6, 11.92, 1.1, 4.8, 0.06, 2.2, hexc("#fafafa")))      # スクリーン
    S.append(P.slab(2.55, 11.9, 1.05, 4.9, 0.04, 0.05, hexc("#8a8a90")))
    S.append(P.slab(3.3, 11.88, 2.6, 3.4, 0.03, 0.4, hexc("#ff8a1f")))      # 帯（オレンジ）
    for (x, y) in TABLES:
        S.append(P.slab(x - 0.8, y - 0.5, 0.0, 1.6, 1.0, 0.72, hexc("#e8e2d6")))
        S.append(P.slab(x - 0.85, y - 0.55, 0.72, 1.7, 1.1, 0.05, hexc("#f2ede4")))
        for (dx, dy) in SEATS:
            S.append(P.slab(x + dx - 0.22, y + dy - 0.22, 0, 0.44, 0.44, 0.45, hexc("#3a4a6a")))   # いす
    return S


HALL = hall_set()
BG_HALL = R.BG_MEET
BG_EVE = E.sky((236, 140, 90), (250, 208, 160)).convert("RGB").resize((W * G.SS, H * G.SS))

MOB = V5.STUDENTS


def mob(i, pos, yaw, **pose):
    r = Rig(MOB[i % len(MOB)], pos, yaw, tag=f"st{i}")
    r.set(armL=0.05, armR=0.05)
    r.set(**pose)
    return r


def kanata(pos, yaw, expr="normal", **pose):
    r = Rig(C.KANATA, pos, yaw, tag="kanata")
    r.set(armL=0.05, armR=0.05)
    r.set(**pose)
    r.expr = expr
    return r


def haruto(pos, yaw, expr="normal", **pose):
    r = Rig(C.HARUTO, pos, yaw, tag="haruto")
    r.set(armL=0.05, armR=0.05)
    r.set(**pose)
    r.expr = expr
    return r


def mio_front(expr="smile", pos=(5.0, 10.2, 0), **pose):
    r = Rig(C.MIO, pos, math.pi, tag="mio")
    r.set(armL=0.05, armR=0.05)
    r.set(**pose)
    r.expr = expr
    return r


BACK, FRONT = (0, 1, 2), (3, 5)


def crowd(t, skip=(), tables=None):
    """班ごとにテーブルに座っている学生たち。skip=((テーブル番号, 席番号), ...)。tables=映すテーブル（手前をふさがないため）"""
    out = []
    k = 0
    for ti, (x, y) in enumerate(TABLES):
        for si, (dx, dy) in enumerate(SEATS):
            k += 1
            if (ti, si) in skip or (tables is not None and ti not in tables):
                continue
            yaw = 0.0 if dy < 0 else math.pi
            out += mob(k, (x + dx, y + dy, 0), yaw, sit=True, armL=0.5, armR=0.5, head_yaw=0.12 * math.sin(t * 1.3 + k)).boxes()
    return out


def sparkle(img, t, cx, cy, r=330):
    """ハルトのまわりのキラキラ"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(14):
        a = i * 2.39996 + t * 0.6
        rr = r * (0.55 + 0.45 * ((i * 37) % 10) / 10)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr * 1.2
        s_ = 10 + 16 * (0.5 + 0.5 * math.sin(t * 5 + i))
        al = int(230 * (0.5 + 0.5 * math.sin(t * 4 + i * 1.7)))
        d.polygon([(x, y - s_ * 2), (x + s_ * 0.45, y - s_ * 0.45), (x + s_ * 2, y), (x + s_ * 0.45, y + s_ * 0.45),
                   (x, y + s_ * 2), (x - s_ * 0.45, y + s_ * 0.45), (x - s_ * 2, y), (x - s_ * 0.45, y - s_ * 0.45)], fill=(255, 240, 160, al))
    img.alpha_composite(lay)


def card_insert(img, u, flip=True):
    """名刺のアップ（逆さま）"""
    if u <= 0:
        return
    c = Image.new("RGBA", (520, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle([0, 0, 519, 299], radius=14, fill=(252, 252, 250), outline=(60, 64, 80), width=6)
    d.text((40, 40), "〇〇大学 1年", font=O.F(BOLD, 34), fill=(90, 94, 110))
    d.text((40, 120), "宇野 カナタ", font=O.F(BLACK, 76), fill=(30, 30, 40))
    if flip:
        c = c.rotate(180)
    E.paste_center(img, c, 760, 1040, E.pop(u))


# ---------- 文字 ----------
def clock(img, time_):
    O.clock_big(img, DATE, time_, grade="大学1年")
    O.counter(img, 2)


def hook(img, t):
    if t < 2.4:
        im = E.fit_text(["名刺の練習。", "ぼくだけ、逆さま。"], 120, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={1: RED})
        E.paste_center(img, im, 540, 1180, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["ガクチカ・ループ 第6話", "キックオフ"], 96, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1180, E.pop(t - 2.4))


def sheet(img, u, title, lines, col=(40, 40, 50), y0=700, fs=62):
    """目標シート（大きく見せる）"""
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a = int(255 * e)
    y0 = y0 + (1 - e) * 40
    h = 150 + int(fs * 1.35) * len(lines)
    d.rounded_rectangle([90, y0, W - 90, y0 + h], radius=26, fill=(252, 250, 242, int(248 * e)), outline=(60, 64, 80, a), width=6)
    d.rounded_rectangle([90, y0, W - 90, y0 + 84], radius=26, fill=(255, 138, 31, a))
    fh, fl = O.F(BLACK, 46), O.F(BLACK, fs)
    d.text((540 - fh.getlength(title) / 2, y0 + 16), title, font=fh, fill=(255, 255, 255, a))
    for j, ln in enumerate(lines):
        c = RED if (ln.startswith("面接") and col is None) else (col or (40, 40, 50))
        d.text((140, y0 + 112 + j * int(fs * 1.35)), ln, font=fl, fill=c + (a,))
    img.alpha_composite(lay)


# ---------- 1コマ ----------
def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    tx, ty = TABLES[4]   # カナタとハルトの班（前の真ん中のテーブル。前から引きで撮る）
    if n == "cold":
        # 隣の班で名刺の練習。カナタが片手で、しかも逆さまに差し出す
        x0, y0 = TABLES[0]
        give = ease(min(1, max(0, t - 0.1) / 0.35))
        k = kanata((x0 + 0.45, y0 - 0.8, 0), 0.0, "normal" if t < 0.9 else "shock", sit=True, armL=0.5, armR=0.5 + 0.9 * give)
        other = mob(9, (x0 - 0.45, y0 + 0.8, 0), math.pi, sit=True, armL=0.5, armR=0.5, head_pitch=0.15)
        u = ease(t / s.dur)
        cam = Camera((lerp(3.3, 3.2, u), lerp(5.2, 4.8, u), 2.0), (x0 + 0.2, y0 - 0.2, 1.1), 48)
        img, _ = render(HALL + crowd(t, skip=((0, 1), (0, 2))) + k.boxes() + other.boxes()
                        + [P.slab(x0 + 0.1, y0 - 0.2, 0.86, 0.26, 0.02, 0.15, hexc("#fcfcfa"))], cam, BG_HALL)
        img = img.convert("RGBA")
        clock(img, "13:10")
        card_insert(img, (t - 0.5) / 0.3)
        hook(img, t)
    elif n == "rule":
        u = ease(t / s.dur)
        cam = Camera((5.0, lerp(0.2, 0.8, u), 2.6), (5.0, 9.8, 1.3), 48)
        img, _ = render(HALL + crowd(t) + mio_front("smile", armL=1.3, armR=1.3).boxes(), cam, BG_HALL)
        img = img.convert("RGBA")
        clock(img, "13:12")
        F.pill(img, "マナー研修：名刺の渡し方", 1000, 46, (64, 110, 220), u=(t - 0.1) / 0.3)
        F.pill(img, "相手が読める向きで・両手で", 1090, 46, (230, 170, 30), (20, 20, 30), u=(t - 0.6) / 0.3)
    elif n == "han":
        # 班分け：カナタの班に、ハルト
        a = s.lines[0][0]
        u = ease(t / s.dur)
        sitdown = ease(min(1, max(0, t - a - L("03") + 0.2) / 0.6))
        k = kanata((tx - 0.45, ty - 0.8, 0), 0.0, "normal", sit=True, armL=0.5, armR=0.5, head_yaw=0.3 * sitdown)
        h = haruto((tx - 0.45, ty + 0.8, 0), math.pi, "smile", sit=sitdown > 0.5, armL=0.5, armR=0.5 + 0.8 * (1 - sitdown))
        cam = Camera((lerp(7.8, 7.6, u), lerp(9.9, 9.5, u), 2.7), (tx - 0.1, ty, 1.0), 50)
        img, _ = render(HALL + crowd(t, tables=BACK + (3,)) + k.boxes() + h.boxes() + mio_front("smile", pos=(8.6, 10.2, 0)).boxes(), cam, BG_HALL)
        img = img.convert("RGBA")
        clock(img, "13:20")
        F.pill(img, "班分け", 1000, 46, (64, 110, 220), u=(t - 0.1) / 0.3)
        if t > a + L("03") - 0.2:
            F.pill(img, "同じ班：宇野カナタ ／ ハルト", 1090, 50, (40, 140, 80), u=(t - a - L("03") + 0.2) / 0.3)
    elif n == "card":
        # テーブルをはさんで立ち、両手で名刺交換（距離をとる）
        a, b = (x[0] for x in s.lines)
        hg = ease(min(1, max(0, t - 0.4) / 0.5))
        kg = ease(min(1, max(0, t - b + 0.1) / 0.5))
        k = kanata((tx - 0.2, ty - 0.95, 0), 0.0, "open" if t < b else "normal", armL=0.05 + 1.35 * kg, armR=0.05 + 1.35 * kg, lean=0.2 * kg)
        h = haruto((tx - 0.2, ty + 0.95, 0), math.pi, "smile", armL=0.05 + 1.35 * hg, armR=0.05 + 1.35 * hg, lean=0.25 * hg)
        u = ease(t / s.dur)
        cam = Camera((lerp(9.2, 8.9, u), lerp(6.0, 6.2, u), 1.9), (tx - 0.2, ty, 1.3), 52)   # 真横から：テーブルをはさんで向かい合う2人
        img, _ = render(HALL + crowd(t, tables=BACK) + k.boxes() + h.boxes(), cam, BG_HALL)
        img = img.convert("RGBA")
        clock(img, "13:25")
        F.pill(img, "同じ班のハルト", 1000, 46, (40, 140, 80), u=(t - 0.1) / 0.3)
    elif n == "goal":
        # カナタが書く。ハルトが横からのぞいて、読み上げる
        a, b, c = (x[0] for x in s.lines)
        k = kanata((tx - 0.45, ty - 0.8, 0), 0.0, "normal" if t < b else ("blank" if t < c else "open"), sit=True,
                   armL=0.6, armR=0.6 + 0.15 * math.sin(t * 9) * (t < a), head_pitch=0.25)
        peek = ease(min(1, max(0, t - a + 0.6) / 0.5))
        h = haruto((tx + 0.45, ty - 0.95, 0), lerp(0.0, 0.55, peek), "normal" if t < b else "smile", lean=0.3 * peek, armL=0.05, armR=0.05)
        cam = Camera((lerp(4.8, 4.9, ease(t / s.dur)), lerp(10.0, 9.6, ease(t / s.dur)), 2.2), (tx, ty - 0.8, 1.55), 46)
        img, _ = render(HALL + crowd(t, tables=BACK) + k.boxes() + h.boxes(), cam, BG_HALL)
        img = img.convert("RGBA")
        clock(img, "14:00")
        F.pill(img, "目標づくり", 1000, 46, (64, 110, 220), u=(t - 0.1) / 0.3) if t < a else None
        if t < a - 0.1:   # 書いているあいだだけシートを見せ、読み上げは横からのぞくハルトを見せる
            nl = max(0, min(3, int((t - 0.3) / 0.45) + 1))
            sheet(img, (t - 0.2) / 0.3, "目標シート　宇野カナタ", GOAL_K[:nl], None, y0=650, fs=54)
    elif n == "dream":
        # ハルトの目標。まぶしく見える（キラキラ）→ 圧倒されるカナタ
        a = s.lines[0][0]
        e9 = a + L("09")
        h = haruto((tx + 0.45, ty - 0.95, 0), 0.55, "smile" if t > e9 else "normal", armL=0.05, armR=0.05)
        k = kanata((tx - 0.45, ty - 0.8, 0), 0.0, "open" if t < e9 else "shock", sit=True, armL=0.5, armR=0.5, head_yaw=-0.5, lean=-0.12 * (t > e9))
        if t < e9 + 0.2:
            u = ease(min(1, t / (e9 + 0.2)))
            cam = Camera((lerp(4.1, 4.2, u), lerp(7.2, 7.0, u), 1.05), (tx + 0.45, ty - 0.95, 1.95), lerp(50, 44, u))   # 見上げる
        else:
            u = ease(min(1, (t - e9 - 0.2) / 1.4))
            cam = Camera((lerp(4.6, 4.65, u), lerp(9.8, 9.3, u), 2.0), (tx - 0.2, ty - 0.85, 1.5), 44)
        img, _ = render(HALL + crowd(t, tables=BACK) + k.boxes() + h.boxes(), cam, BG_HALL)
        img = img.convert("RGBA")
        clock(img, "14:05")
        if t > a - 0.3:
            glow = min(1, (t - a + 0.3) / 0.6)
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 236, 170, int(40 * glow))))
            if t < e9 + 0.2:
                sparkle(img, t, 560, 760)
            else:
                sparkle(img, t, 700, 560, 220)
        if t > e9 + 0.3:
            sheet(img, (t - e9 - 0.3) / 0.3, "目標シート　ハルト", GOAL_H, (40, 120, 60), y0=980)
    elif n == "game":
        # 向かい合ってハイタッチ
        hi = ease(min(1, max(0, t - s.hi + 0.25) / 0.25))
        k = kanata((tx - 0.5, ty - 1.1, 0), -math.pi / 2, "smile" if t > s.hi else "open", armL=0.2 + 2.2 * hi, armR=0.2 + 2.2 * hi)
        h = haruto((tx + 0.4, ty - 1.1, 0), math.pi / 2, "smile", armL=0.2 + 2.2 * hi, armR=0.2 + 2.2 * hi)
        m1 = mob(3, (tx - 1.1, ty - 1.9, 0), 0.3, armL=0.2 + 2.2 * hi, armR=0.1)
        m2 = mob(4, (tx + 1.0, ty - 1.9, 0), -0.3, armL=0.1, armR=0.2 + 2.2 * hi)
        u = ease(t / s.dur)
        cam = Camera((tx - 0.05, lerp(10.0, 9.6, u), 2.0), (tx - 0.05, ty - 1.1, 1.5), 46)
        img, _ = render(HALL + crowd(t, tables=BACK) + k.boxes() + h.boxes() + m1.boxes() + m2.boxes(), cam, BG_HALL)
        img = img.convert("RGBA")
        clock(img, "15:30")
        F.pill(img, "ミニゲーム：班で共通点さがし", 1000, 46, (64, 110, 220), u=(t - 0.1) / 0.3)
        if s.hi - 0.05 < t < s.hi + 0.9:
            Q.big_word(img, "パンッ！", t - s.hi + 0.05, YEL, y=720, size=120)
    elif n == "think":
        # 笑うハルトを見るカナタ（少し寄る）
        u = ease(t / s.dur)
        k = kanata((tx - 0.5, ty - 1.1, 0), -math.pi / 2 - 0.3, "normal", armL=0.05, armR=0.05, head_pitch=0.05)
        h = haruto((tx + 0.4, ty - 1.1, 0), math.pi / 2 + 0.6, "smile", armL=0.05, armR=0.05)
        cam = Camera((lerp(3.0, 3.2, u), lerp(8.6, 8.2, u), 1.85), (tx - 0.3, ty - 1.1, 1.6), 46)
        img, _ = render(HALL + crowd(t, tables=BACK) + k.boxes() + h.boxes(), cam, BG_HALL)
        img = img.convert("RGBA")
        clock(img, "15:35")
    elif n == "street":
        # 夕方の帰り道。ハルトが先で手をふって帰っていく。少しさみしい
        a, b = (x[0] for x in s.lines)
        k = R.kanata_stand("normal" if t < b else "blank")
        k.set(head_pitch=-0.05 if t < b else 0.18)
        hx = lerp(3.4, 4.6, ease(min(1, t / s.dur)))
        hr = haruto((hx, 7.6, 0), math.pi, "smile", armR=2.6 + 0.3 * math.sin(t * 8) if t < a else 0.05, armL=0.05)
        u = ease(t / s.dur)
        cam = Camera((lerp(3.1, 2.95, u), lerp(-0.6, 0.3, u), 1.7), (2.7, 4.6, 1.5), 50)
        tk = Q.tokei_near(t, "eyes", t + 0.4, (3.25, 3.3, 1.75))
        img, _ = render(R.OUTSIDE + k.boxes() + hr.boxes() + tk, cam, BG_EVE)
        img = img.convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 130, 60, 40)))
        if t > b:
            img.alpha_composite(Image.new("RGBA", (W, H), (30, 20, 60, int(60 * min(1, (t - b) / 2.0)))))
        clock(img, "17:30")
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "あなたなら、", 560, t, size=84)
        O.caption(img, "目標に何て書く？", 680, t, size=96, col=YEL)
        for txt, y, sz, col, path in ((["コメントで教えてね"], 860, 60, (255, 255, 255), BLACK),
                                      (["次回 第7話「名刺の渡し方」"], 990, 52, (255, 255, 255), BLACK),
                                      (["ドットジェイピー広島第一支部", "春インターン申込は12月31日まで"], 1140, 48, YEL, BLACK),
                                      (["この動画は「勇気を出して一歩を踏み出そう」という", "メッセージを伝えるための創作ドラマです"], 1300, 32, (220, 226, 245), BOLD)):
            E.paste_center(img, E.fit_text(txt, sz, 1000, fill=col, sw=6, path=path), 540, y, E.pop(t - 0.3))
    if sid:
        subtitle(img, sid)
    return img


def render_shot(i):
    s = SH[i]
    n = int(round(s.dur * FPS))
    out = f"{OUT}/{i:02d}_{s.name}.mp4"
    tmp = out[:-4] + ".part.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for k in range(n):
        p.stdin.write(frame(s, k / FPS).convert("RGB").tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, out)
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "still":
        frame(shot(sys.argv[2]), float(sys.argv[3])).convert("RGB").save(f"{OUT}/still_{sys.argv[2]}_{sys.argv[3]}.png")
    elif sys.argv[1] == "build":
        import glob
        for f in glob.glob(f"{OUT}/[0-9][0-9]_*.mp4"):
            os.remove(f)
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(2) as ex:
            res = list(ex.map(render_shot, range(len(SH))))
        open(f"{OUT}/list.txt", "w").write("".join(f"file '{o}'\n" for o in res))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{OUT}/list.txt", "-c", "copy", f"{OUT}/video.mp4"], check=True)
        print("video", round(sum(s.dur for s in SH), 2))
