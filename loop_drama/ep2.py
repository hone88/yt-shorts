"""ガクチカ・ループ 第2話「説明会」（オンライン説明会。カメラはオフのままでもOK）。
python3 ep2.py still <shot> <t> [A|B] | python3 ep2.py build [A|B]
A：第1話の投票で「説明会に出る」が勝った版。B：「もう一度寝る」が勝った版（冒頭だけ違う）"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import g3d as G
from g3d import Camera, Rig, render, hexc, add
import characters as C
import ep1b as O   # 時計・残りループ・字幕の部品
import ep1c as P   # 面接室・部屋のセット
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
VAR = "A"
for a in sys.argv[1:]:
    if a in ("A", "B"):
        VAR = a
OUT = f"{HERE}/out_ep2{VAR}"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED = (255, 216, 77), (255, 90, 90)


# ---------- 声 ----------
VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep2/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("K", "…カメラは、[オフ]で|いいか。"),
    "02": ("M", "カナタ、|[来てくれてありがとう]！"),
    "03": ("M", "これは、|[広島の大学1、2年生向け]の、|[春休みのインターン]。"),
    "04": ("M", "行き先は、[議員]さんか、[NPO]。|2月から3月の、|[2か月]だよ。"),
    "05": ("M", "議員さんは[朝10時]から。|[午前だけ・午後だけ]も|OK。"),
    "06": ("K", "…それなら、|[行けるかも]。"),
    "07": ("T", "寝たら、[何もしない一日]。|面接に[飛ばす]のだ！"),
    "08": ("K", "お、起きてる！|起きてる！"),
    "09": ("M", "…[誰と]話してるの？"),
    "10": ("M", "カナタは、|[やりたいこと]、ある？"),
    "11": ("K", "…[何も]、ないです。"),
    "12": ("M", "私も最初は、[何もなかった]よ。|でも、[大丈夫]だよ。"),
    "13": ("M", "3月は政策コンテストの|[未来自治体]。予定が合えば、|[知事面談]もあるよ。"),
    "14": ("K", "…[知事]と！？"),
    "15": ("M", "次は[1次選考会]。|[伸ばしたい力]を、|一緒に考えよう。"),
    "16": ("K", "選考会って…|[落とされる]やつ？"),
    "17": ("T", "ちょっとは、|[進んだ]のだ。"),
    "18": ("K", "…[ちょっとだけ]、な。"),
    "b1": ("T", "また[寝た]のだ？|何もしない一日は、|面接に[飛ばす]のだ。"),
    "b2": ("I", "[学生時代に力を入れたこと]は？"),
    "b3": ("K", "わ、わかった！|出る！[出るから]！"),
}


def subtitle(img, sid):
    who, text = TEXT[sid]
    name, col = O.SPEAK[who]
    lines = text.split("|")
    d = ImageDraw.Draw(img)
    f, fn = O.F(BLACK, 76), O.F(BLACK, 40)
    y = 1400 - (len(lines) - 1) * 96
    nw = fn.getlength(name) + 40
    d.rounded_rectangle([540 - nw / 2, y - 78, 540 + nw / 2, y - 18], radius=30, fill=col)
    d.text((540 - nw / 2 + 20, y - 74), name, font=fn, fill=(20, 20, 30))
    for i, ln in enumerate(lines):
        ff = f
        while ff.getlength(ln.replace("[", "").replace("]", "")) > 1000:
            ff = O.F(BLACK, ff.size - 4)
        O.rich_line(d, 540, y + i * 96, ln, ff)


# ---------- 場面の割り付け ----------
def seq(ids, start=0.4, gap=0.25, extra=None):
    """セリフを順に並べる。extra: {id: そのセリフの前に足す間}"""
    out, t = [], start
    for i in ids:
        t += (extra or {}).get(i, 0)
        out.append((t, i))
        t += L(i) + gap
    return out, t


def plan():
    S = []
    if VAR == "A":
        S.append(O.Shot("open", 3.3))
    else:
        S.append(O.Shot("sleep", 1.6 + L("b1") + 0.4, [(1.6, "b1")]))
        S.append(O.Shot("flash", 0.3 + L("b2") + 0.7, [(0.3, "b2")]))
        S.append(O.Shot("wake", 0.25 + L("b3") + 0.4, [(0.25, "b3")]))
    ln, t = seq(["02", "03"], 0.5, extra={"03": 0.3})
    s = O.Shot("one", t + 0.3, ln); s.rev = ln[1][0]; S.append(s)
    ln, t = seq(["04", "05"], 0.4)
    S.append(O.Shot("info", t + 0.3, ln))
    ln, t = seq(["07", "08"], 1.6)
    s = O.Shot("doze", t + 0.3, ln); s.tk = 1.0; S.append(s)
    ln, t = seq(["10"], 0.3)
    S.append(O.Shot("ask", t + 0.2, ln))
    S.append(O.Shot("none", 0.3 + L("11") + 0.8, [(0.3, "11")]))   # 答えのあとに間
    ln, t = seq(["12"], 0.3)
    s = O.Shot("okay", t + 1.5, ln); s.camon = t + 0.1; S.append(s)   # カナタが自分からカメラON
    ln, t = seq(["13", "14"], 0.3, extra={"14": 0.1})
    S.append(O.Shot("list", t + 0.4, ln))
    ln, t = seq(["15", "16"], 0.3)
    S.append(O.Shot("next", t + 1.1, ln))
    ln, t = seq(["17", "18"], 0.9)
    S.append(O.Shot("after", t + 0.6, ln))
    S.append(O.Shot("end", 6.0))
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


def line_t(s, sid):
    return next(t0 for t0, i in s.lines if i == sid)


# ---------- 部屋 ----------
def laptop():
    return [P.slab(2.22, 3.05, 0.57, 0.56, 0.38, 0.03, hexc("#3a3e48")),
            P.slab(2.22, 3.05, 0.6, 0.56, 0.03, 0.38, hexc("#2e323a"))]


def kanata_bed(expr="normal"):
    r = Rig(C.KANATA, (2.5, 3.75, 0.2), math.pi, tag="kanata")
    r.set(sit=True, armL=0.9, armR=0.9, head_pitch=0.18)
    r.expr = expr
    return r


def room_img(k, cam, extra=(), glow=0.0):
    img, _ = render(P.ROOM + k.boxes() + laptop() + list(extra), cam, P.BG_ROOM)
    img = img.convert("RGBA")
    if glow > 0:   # 画面の青い光
        img.alpha_composite(Image.new("RGBA", (W, H), (90, 150, 255, int(42 * glow))))
    return img


def face_cam(t, dur, push=0.25):
    u = ease(t / max(dur, 0.01))
    return Camera((lerp(2.9, 2.85, u), lerp(1.2, 1.2 + push, u), 1.7), (2.55, 3.75, 1.5), 46)


def tokei_near(t, expr="angry", drop_t=None, pos=(2.93, 3.2, 1.55)):
    dz = 0.0
    if drop_t is not None:
        dz = (1 - ease(min(1, max(0, drop_t) / 0.45))) * 1.4
    return C.tokei_boxes(add(pos, (0, 0, dz)), t, expr, 0.5, math.pi + 0.45)


# ---------- ビデオ通話 ----------
MIO_SET = P.blocks(-3, 4, 1, 2, -1, 3, hexc("#e9e4d8"), 0.03, 31) + [
    P.slab(1.3, 0.9, -1, 0.9, 0.3, 2.2, hexc("#7a5434")),
    P.slab(1.32, 0.86, 0.1, 0.86, 0.04, 0.3, hexc("#d8584a")),
    P.slab(1.32, 0.86, 0.6, 0.86, 0.04, 0.3, hexc("#4a8ad8")),
    P.slab(-1.9, 0.85, -1, 0.5, 0.5, 1.4, hexc("#4a9a4a")),
]
BG_MIO = Image.new("RGB", (W * G.SS, H * G.SS), (233, 228, 216))


def mio_tile(t, talking, expr=None):
    r = Rig(C.MIO, (0, 0, -1.0), math.pi, tag="mio")
    r.expr = expr or (("smile" if int(t * 7) % 2 else "normal") if talking else "smile")
    r.set(head_yaw=0.06 * math.sin(t * 1.3), head_pitch=0.03 * math.sin(t * 2.1), armL=0.3, armR=0.3)
    cam = Camera((0.1, -2.9, 0.95), (0.04, 0, 0.66), 40)
    img, _ = render(MIO_SET + r.boxes(), cam, BG_MIO)
    return img.convert("RGB").crop((0, 700, 1080, 1208))


def self_view(t, expr):
    """カナタ側のカメラ（右下の小窓）"""
    k = kanata_bed(expr)
    k.set(head_pitch=0.05)
    img = room_img(k, Camera((2.55, 1.9, 1.75), (2.5, 3.75, 1.45), 44), glow=0.6)
    return img.convert("RGB").crop((0, 520, 1080, 1218))


TX, TY, TW, TH = 40, 560, 1000, 470   # ミオの枠


def call_ui(s, t, cam_on=False, kexpr="open", mexpr=None):
    img = Image.new("RGBA", (W, H), (24, 26, 34, 255))
    d = ImageDraw.Draw(img)
    sid = speaking(s, t)
    mio_talk = sid is not None and TEXT[sid][0] == "M"
    img.paste(mio_tile(s.start + t, mio_talk, mexpr).resize((TW, TH)), (TX, TY))
    d.rounded_rectangle([TX, TY, TX + TW, TY + TH], radius=6, outline=(90, 220, 120) if mio_talk else (60, 64, 80), width=8)
    d.rounded_rectangle([TX + 20, TY + TH - 66, TX + 330, TY + TH - 14], radius=12, fill=(0, 0, 0))
    d.text((TX + 38, TY + TH - 60), "宮路ミオ（スタッフ）", font=O.F(BOLD, 34), fill=(255, 255, 255))
    # 右下の小窓：カナタ
    sw, sh = 300, 194
    sx, sy = TX + TW - sw - 18, TY + TH - sh - 18
    if cam_on:
        img.paste(self_view(s.start + t, kexpr).resize((sw, sh)), (sx, sy))
    else:
        d.rectangle([sx, sy, sx + sw, sy + sh], fill=(12, 12, 16))
        f = O.F(BLACK, 30)
        d.text((sx + sw / 2 - f.getlength("カメラOFF") / 2, sy + 80), "カメラOFF", font=f, fill=(150, 156, 175))
    d.rectangle([sx, sy, sx + sw, sy + sh], outline=(255, 216, 77), width=4)
    d.rounded_rectangle([sx + 8, sy + sh - 44, sx + 108, sy - 6 + sh], radius=8, fill=(0, 0, 0))
    d.text((sx + 18, sy + sh - 42), "カナタ", font=O.F(BOLD, 28), fill=YEL)
    # 参加者の数
    f = O.F(BLACK, 34)
    return img


def slide(img, u, cards, y=600):
    """画面共有のカード。cards: [(大きい字, 小さい字, 色)]"""
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    n = len(cards)
    w = (TW - 40 - (n - 1) * 20) / n
    for i, (big, small, col) in enumerate(cards):
        bx = TX + 20 + i * (w + 20)
        by = y + (1 - e) * 40
        dl.rounded_rectangle([bx, by, bx + w, by + 230], radius=28, fill=col + (int(242 * e),))
        fb = O.F(BLACK, 60 if n <= 2 else 46)
        while fb.getlength(big) > w - 30:
            fb = O.F(BLACK, fb.size - 4)
        dl.text((bx + w / 2 - fb.getlength(big) / 2, by + 50), big, font=fb, fill=(255, 255, 255, int(255 * e)))
        fs = O.F(BLACK, 38)
        while fs.getlength(small) > w - 30:
            fs = O.F(BLACK, fs.size - 2)
        dl.text((bx + w / 2 - fs.getlength(small) / 2, by + 150), small, font=fs, fill=(255, 255, 255, int(255 * e)))
    img.alpha_composite(lay)


def list_cards(img, t0, t):
    """春にできること（1つずつ出る）"""
    items = [("未来自治体", "政策コンテスト（3月）", (64, 110, 220)),
             ("企業訪問・地域のイベント", "参加は自由", (40, 160, 110)),
             ("知事面談", "予定が合えば", (220, 120, 40)),
             ("修了認定証", "履歴書に書ける", (150, 80, 190))]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle([TX, TY, TX + TW, TY + TH], radius=6, fill=(14, 16, 30, int(235 * ease(min(1, (t - t0) / 0.3)))))
    fh = O.F(BLACK, 46)
    dl.text((540 - fh.getlength("春のインターンでできること") / 2, TY + 22), "春のインターンでできること", font=fh, fill=YEL)
    for i, (big, small, col) in enumerate(items):
        u = ease(min(1, (t - t0 - 0.25 - i * 0.55) / 0.25))
        if u <= 0:
            continue
        bx = TX + 30 + (i % 2) * 480
        by = TY + 100 + (i // 2) * 180 + (1 - u) * 30
        dl.rounded_rectangle([bx, by, bx + 460, by + 160], radius=24, fill=col + (int(245 * u),))
        fb = O.F(BLACK, 50)
        while fb.getlength(big) > 420:
            fb = O.F(BLACK, fb.size - 4)
        dl.text((bx + 230 - fb.getlength(big) / 2, by + 22), big, font=fb, fill=(255, 255, 255, int(255 * u)))
        fs = O.F(BLACK, 34)
        dl.text((bx + 230 - fs.getlength(small) / 2, by + 98), small, font=fs, fill=(255, 240, 200, int(255 * u)))
    img.alpha_composite(lay)


def big_word(img, word, t, col=YEL, y=780, size=200):
    if t <= 0:
        return
    im = E.fit_text([word], size, 1000, fill=col, stroke=(8, 10, 24), sw=14)
    E.paste_center(img, im, 540, y, E.pop(t))


def card3(img, u):
    """ルール③のカード"""
    if u <= 0:
        return
    e = ease(u)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    y0 = 650 + (1 - e) * 40
    a = int(255 * e)
    d.rounded_rectangle([40, y0, W - 40, y0 + 330], radius=40, fill=(10, 12, 30, int(235 * e)), outline=(255, 216, 77, a), width=8)
    ft, fb = O.F(BLACK, 54), O.F(BLACK, 70)
    d.text((540 - ft.getlength("ループのルール③") / 2, y0 + 28), "ループのルール③", font=ft, fill=(255, 216, 77, a))
    for j, ln in enumerate(("[何もしない一日]は", "面接に[飛ばされる]")):
        x, y = 100, y0 + 110 + j * 96
        cur, on = "", False
        for ch in ln + "\0":
            if ch in "[]\0":
                if cur:
                    d.text((x, y), cur, font=fb, fill=(255, 90, 90, a) if on else (255, 255, 255, a))
                    x += fb.getlength(cur)
                cur, on = "", ch == "["
            else:
                cur += ch
    img.alpha_composite(lay)


def vote_card(img, t, lab, txt, col):
    u = ease(min(1, t / 0.25))
    card = Image.new("RGBA", (900, 470), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, 899, 469], radius=46, fill=(10, 12, 30, 235), outline=col, width=10)
    f0, f1, f2 = O.F(BLACK, 56), O.F(BLACK, 170), O.F(BLACK, 76)
    d.text((450 - f0.getlength("前回のみんなの答え") / 2, 34), "前回のみんなの答え", font=f0, fill=(255, 255, 255))
    d.rounded_rectangle([60, 130, 280, 390], radius=30, fill=col)
    d.text((170 - f1.getlength(lab) / 2, 158), lab, font=f1, fill=(255, 255, 255))
    d.text((320, 210), txt, font=f2, fill=col)
    E.paste_center(img, card, 540, 1060, 1.3 - 0.3 * u)


def recap(img, t):
    if t <= 0:
        return
    im = E.fit_text(["前回：面接で答えられず、", "大学1年の12月5日に戻された"], 60, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=9, hl={1: YEL})
    E.paste_center(img, im, 540, 1420, E.pop(t))


def clock(img, time_, counter=True):
    O.clock_big(img, "2026年12月5日（土）", time_, grade="大学1年")
    if counter:
        O.counter(img, 3)


# ---------- 1コマ ----------
def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "open":
        img = room_img(kanata_bed("normal"), face_cam(t, s.dur, 0.15), glow=0.6)
        clock(img, "9:59")
        vote_card(img, t, "A", "説明会に出る", (255, 138, 31))
    elif n == "sleep":
        k = kanata_bed("sleep" if t < 1.6 else "shock")
        k.set(head_pitch=0.45 if t < 1.6 else 0.05)
        tk = tokei_near(t, "angry", t - 1.0) if t > 1.0 else []
        img = room_img(k, face_cam(t, s.dur, 0.1), tk, glow=0.25)
        clock(img, "9:58")
        if t < 1.5:
            vote_card(img, t, "B", "もう一度寝る", (110, 116, 140))
    elif n == "flash":
        src = P.shot("interview")
        img = O.desat(P.frame(src, src.tf + 0.3, raw=True), 0.9)
        img = O.glitch(img, 0.5 if t < 0.25 or t > s.dur - 0.25 else 0.12, int(t * 30))
        O.clock_big(img, "2029年6月1日（金）", "10:00", flash=1, grade="大学4年")
        big_word(img, "※トケイが見せた予告", t, YEL, y=1150, size=70)
    elif n == "wake":
        k = kanata_bed("shock"); k.set(head_pitch=0.0, lean=-0.06)
        img = room_img(k, face_cam(t, s.dur, 0.3), tokei_near(t + 3, "normal"), glow=0.6)
        clock(img, "9:59")
    elif n == "join":
        img = room_img(kanata_bed("normal"), face_cam(t, s.dur, 0.35), glow=1.0)
        clock(img, "10:00")
        if t > 0.2:
            f = O.F(BLACK, 56)
            lab = "● カメラ OFF"
            w = f.getlength(lab) + 70
            im = Image.new("RGBA", (int(w), 100), (0, 0, 0, 0))
            dd = ImageDraw.Draw(im)
            dd.rounded_rectangle([0, 0, w - 1, 99], radius=50, fill=(200, 40, 50))
            dd.text((35, 14), lab, font=f, fill=(255, 255, 255))
            E.paste_center(img, im, 540, 1090, E.pop(t - 0.2))
    elif n == "one":
        img = call_ui(s, t, cam_on=False)
        clock(img, "10:00", counter=False)
        if t > s.rev - 0.1:
            slide(img, (t - s.rev + 0.1) / 0.3, [("広島の大学1・2年生向け", "春休みのインターン", (220, 120, 40))])
    elif n == "info":
        img = call_ui(s, t, cam_on=False)
        clock(img, "10:05", counter=False)
        a, b = (x[0] for x in s.lines)
        if t < b:
            slide(img, (t - a - 0.2) / 0.3, [("議員インターン", "2月1日〜3月31日", (64, 110, 220)), ("NPOインターン", "2月1日〜3月31日", (40, 160, 110))])
        else:
            slide(img, (t - b - 0.1) / 0.3, [("朝10時スタート", "議員インターンの目安", (220, 120, 40)), ("午前だけ・午後だけ", "もOK", (150, 80, 190))])
    elif n == "doze":
        a, b = (x[0] for x in s.lines)
        asleep = t < s.tk + 0.5
        k = kanata_bed("sleep" if 0.6 < t and asleep else ("normal" if asleep else "shock"))
        k.set(head_pitch=0.18 + 0.35 * ease(min(1, t / 1.2)) if asleep else 0.0, lean=0 if asleep else -0.08)
        tk = tokei_near(t, "angry", t - s.tk) if t > s.tk else []
        img = room_img(k, face_cam(t, s.dur, 0.2), tk, glow=0.8)
        clock(img, f"10:{20 + min(5, int(t * 4)) if asleep else 25:02d}")
        if a + 0.3 < t < b + 0.2:
            card3(img, (t - a - 0.3) / 0.3)
    elif n == "ask":
        img = call_ui(s, t, cam_on=False)
        clock(img, "10:30", counter=False)
    elif n == "none":
        k = kanata_bed("blank"); k.set(head_pitch=0.25)
        img = room_img(k, face_cam(t, s.dur, 0.45), glow=0.7)
        clock(img, "10:30")
    elif n == "okay":
        img = call_ui(s, t, cam_on=t > s.camon, kexpr="smile", mexpr="smile" if t > s.lines[0][0] + L("12") * 0.6 else None)
        clock(img, "10:31", counter=False)
    elif n == "list":
        a, b = (x[0] for x in s.lines)
        img = call_ui(s, t, cam_on=True, kexpr="shock" if t > b else "open")
        clock(img, "10:35", counter=False)
        list_cards(img, a, t)
    elif n == "next":
        a, b = (x[0] for x in s.lines)
        grin = t > b + L("16")
        img = call_ui(s, t, cam_on=True, kexpr="shock" if t > b else "normal", mexpr="wink" if grin else None)
        clock(img, "10:45", counter=False)
        if grin:
            big_word(img, "…にやっ", t - b - L("16"), (255, 138, 31), y=1150, size=90)
    elif n == "after":
        a, b = (x[0] for x in s.lines)
        k = kanata_bed("smile" if t > b else "normal"); k.set(head_pitch=0.1)
        tk = tokei_near(t, "eyes", t - 0.2, (3.12, 3.35, 1.62))
        cam = Camera((lerp(3.2, 3.15, ease(t / s.dur)), 1.95, 1.62), (2.75, 3.6, 1.5), 50)
        img = room_img(k, cam, tk, glow=0.2)
        clock(img, "11:00")
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "あなたなら、", 560, t, size=84)
        O.caption(img, "説明会で何を聞く？", 680, t, size=96, col=YEL)
        for txt, y, sz, col, path in ((["コメントで教えてね"], 860, 64, (255, 255, 255), BLACK),
                                      (["説明会はオンラインでも対面でもOK"], 1000, 44, (200, 210, 235), BOLD),
                                      (["次回 第3話「落とす場じゃない」"], 1130, 50, (255, 255, 255), BLACK),
                                      (["あなたの「力を入れたこと」は、まだ作れる。"], 1250, 44, (255, 255, 255), BOLD),
                                      (["ドットジェイピー広島第一支部", "春インターン申込は12月31日まで"], 1380, 48, YEL, BLACK),
                                      (["この物語はフィクションです"], 1500, 28, (180, 186, 210), BOLD)):
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
