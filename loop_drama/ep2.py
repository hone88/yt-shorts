"""ガクチカ・ループ 第2話「説明会」。
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
    "01": ("K", "…カメラは、[オフ]で、|いいよな。"),
    "02": ("M", "こんにちは！|ドットジェイピー広島第一支部の、|[宮路ミオ]です。"),
    "03": ("M", "大学生が春休みに、|[議員]さんや[NPO]のもとで、|インターンをします。"),
    "04": ("T", "寝たら、[何もしない一日]なのだ。|面接に[飛ばす]のだ！"),
    "05": ("K", "お、起きてる！|起きてる！"),
    "06": ("M", "それから春は、|[知事と話せる]、|知事面談もあります。"),
    "07": ("K", "…[知事]と、|話せるの？"),
    "08": ("M", "カナタ、見てたでしょ。|カメラオフでも、|[名前でバレてる]よ。"),
    "09": ("K", "…[ちょっとだけ]、|気になった。"),
    "10": ("T", "ちょっとは、|[進んだ]のだ。"),
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
def plan():
    S = []
    if VAR == "A":
        S.append(O.Shot("open", 3.3))
    else:
        s = O.Shot("sleep", 1.6 + L("b1") + 0.4, [(1.6, "b1")]); S.append(s)
        S.append(O.Shot("flash", 0.3 + L("b2") + 0.7, [(0.3, "b2")]))
        S.append(O.Shot("wake", 0.25 + L("b3") + 0.4, [(0.25, "b3")]))
    S.append(O.Shot("join", 0.5 + L("01") + 0.6, [(0.5, "01")]))
    a = 0.6; b = a + L("02") + 0.35
    S.append(O.Shot("call", b + L("03") + 0.8, [(a, "02"), (b, "03")]))
    a = 2.2; b = a + L("04") + 0.3
    s = O.Shot("doze", b + L("05") + 0.6, [(a, "04"), (b, "05")]); s.tk = a - 0.6; S.append(s)
    s = O.Shot("chiji", 0.4 + L("06") + 2.2, [(0.4, "06")]); s.rev = 0.4 + L("06") + 0.9; S.append(s)
    S.append(O.Shot("react", 0.3 + L("07") + 0.7, [(0.3, "07")]))
    a = 1.0; b = a + L("08") + 0.4; c = b + L("09") + 0.3
    S.append(O.Shot("after", c + L("10") + 0.7, [(a, "08"), (b, "09"), (c, "10")]))
    S.append(O.Shot("end", 6.8))
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


# ---------- セット ----------
def laptop(glow=True):
    """ベッドの上のノートパソコン（画面はカメラと反対の、カナタ側を向く）"""
    return [P.slab(2.22, 3.05, 0.57, 0.56, 0.38, 0.03, hexc("#3a3e48")),
            P.slab(2.22, 3.05, 0.6, 0.56, 0.03, 0.38, hexc("#2e323a"))]


def kanata_bed(expr="normal"):
    r = Rig(C.KANATA, (2.5, 3.75, 0.2), math.pi, tag="kanata")
    r.set(sit=True, armL=0.9, armR=0.9, head_pitch=0.18)
    r.expr = expr
    return r


def room_img(k, cam, extra=(), keep=None, glow=0.0):
    img, mask = render(P.ROOM + k.boxes() + laptop() + list(extra), cam, P.BG_ROOM, keep=keep)
    img = img.convert("RGBA")
    if glow > 0:   # 画面の青い光
        lay = Image.new("RGBA", (W, H), (90, 150, 255, int(42 * glow)))
        img.alpha_composite(lay)
    return img, mask


def face_cam(t, dur, push=0.25):
    u = ease(t / max(dur, 0.01))
    return Camera((lerp(2.9, 2.85, u), lerp(1.2, 1.2 + push, u), 1.7), (2.55, 3.75, 1.5), 46)


# ミオのカメラ映像（ビデオ通話の枠）
MIO_SET = P.blocks(-3, 4, 1, 2, -1, 3, hexc("#e9e4d8"), 0.03, 31) + [
    P.slab(1.3, 0.9, -1, 0.9, 0.3, 2.2, hexc("#7a5434")),       # 本棚
    P.slab(1.32, 0.86, 0.1, 0.86, 0.04, 0.3, hexc("#d8584a")),
    P.slab(1.32, 0.86, 0.6, 0.86, 0.04, 0.3, hexc("#4a8ad8")),
    P.slab(-1.9, 0.85, -1, 0.5, 0.5, 1.4, hexc("#4a9a4a")),     # 観葉植物
]
BG_MIO = Image.new("RGB", (W * G.SS, H * G.SS), (233, 228, 216))


def mio_tile(t, talking):
    r = Rig(C.MIO, (0, 0, -1.0), math.pi, tag="mio")
    r.expr = ("smile" if int(t * 7) % 2 else "normal") if talking else "smile"
    r.set(head_yaw=0.06 * math.sin(t * 1.3), head_pitch=0.03 * math.sin(t * 2.1), armL=0.3, armR=0.3)
    cam = Camera((0.1, -2.9, 0.95), (0.04, 0, 0.66), 40)
    img, _ = render(MIO_SET + r.boxes(), cam, BG_MIO)
    return img.convert("RGB").crop((0, 700, 1080, 1208))


def call_ui(t, s, slide=0.0, chiji=0.0):
    """ビデオ通話の画面（全面）"""
    img = Image.new("RGBA", (W, H), (24, 26, 34, 255))
    d = ImageDraw.Draw(img)
    sid = speaking(s, t)
    tile = mio_tile(s.start + t, sid is not None).resize((1000, 470))
    x0, y0 = 40, 552
    img.paste(tile, (x0, y0))
    d.rounded_rectangle([x0, y0, x0 + 1000, y0 + 470], radius=6, outline=(90, 220, 120) if sid else (60, 64, 80), width=8)
    d.rounded_rectangle([x0 + 20, y0 + 404, x0 + 330, y0 + 456], radius=12, fill=(0, 0, 0, 170))
    d.text((x0 + 38, y0 + 410), "宮路ミオ（スタッフ）", font=O.F(BOLD, 34), fill=(255, 255, 255))
    # 説明のスライド（画面共有）
    if slide > 0:
        e = ease(slide)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        for i, (lab, col) in enumerate((("議員インターン", (64, 110, 220)), ("NPOインターン", (40, 160, 110)))):
            bx = 80 + i * 470
            by = y0 + 40 + (1 - e) * 40
            dl.rounded_rectangle([bx, by, bx + 450, by + 200], radius=30, fill=col + (int(240 * e),))
            f = O.F(BLACK, 58)
            dl.text((bx + 225 - f.getlength(lab) / 2, by + 66), lab, font=f, fill=(255, 255, 255, int(255 * e)))
        img.alpha_composite(lay)
    # 下に参加者の枠（みんなカメラオフ）
    names = ["カナタ", "参加者", "参加者", "参加者"]
    for i, nm in enumerate(names):
        bx, by = 40 + i * 255, 1036
        d.rounded_rectangle([bx, by, bx + 235, by + 76], radius=14, fill=(48, 52, 66), outline=(255, 216, 77) if i == 0 else None, width=5)
        f = O.F(BLACK, 34 if i == 0 else 30)
        d.text((bx + 117 - f.getlength(nm) / 2, by + 18), nm, font=f, fill=(255, 216, 77) if i == 0 else (180, 186, 205))
    if chiji > 0:   # 「知事面談」のカード
        e = ease(min(1, chiji / 0.25))
        sc = 1.25 - 0.25 * e
        card = Image.new("RGBA", (920, 360), (0, 0, 0, 0))
        dc = ImageDraw.Draw(card)
        dc.rounded_rectangle([0, 0, 919, 359], radius=44, fill=(10, 12, 30, 235), outline=(255, 216, 77), width=10)
        f1, f2 = O.F(BLACK, 54), O.F(BLACK, 150)
        dc.text((460 - f1.getlength("春のインターンでは") / 2, 34), "春のインターンでは", font=f1, fill=(255, 255, 255))
        dc.text((460 - f2.getlength("知事面談") / 2, 120), "知事面談", font=f2, fill=(255, 216, 77))
        E.paste_center(img, card, 540, 790, sc)
    return img


def tokei_near(t, expr="angry", drop_t=None, pos=(2.93, 3.2, 1.55)):
    dz = 0.0
    if drop_t is not None:
        dz = (1 - ease(min(1, max(0, drop_t) / 0.45))) * 1.4
    return C.tokei_boxes(add(pos, (0, 0, dz)), t, expr, 0.5, math.pi + 0.45)


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
    for j, ln in enumerate((("[何もしない一日]", "は"), ("面接に[飛ばされる]", ""))):
        x = 100
        y = y0 + 110 + j * 96
        for part in "".join(ln).replace("]", "[").split("["):
            pass
        cur, on = "", False
        for ch in "".join(ln) + "\0":
            if ch in "[]\0":
                if cur:
                    d.text((x, y), cur, font=fb, fill=(255, 90, 90, a) if on else (255, 255, 255, a))
                    x += fb.getlength(cur)
                cur, on = "", ch == "["
            else:
                cur += ch
    img.alpha_composite(lay)


def vote_card(img, t, lab, txt, col):
    """前回の投票の結果"""
    u = ease(min(1, t / 0.25))
    sc = 1.3 - 0.3 * u
    card = Image.new("RGBA", (900, 470), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, 899, 469], radius=46, fill=(10, 12, 30, 235), outline=col, width=10)
    f0, f1, f2 = O.F(BLACK, 56), O.F(BLACK, 170), O.F(BLACK, 76)
    d.text((450 - f0.getlength("前回のみんなの答え") / 2, 34), "前回のみんなの答え", font=f0, fill=(255, 255, 255))
    d.rounded_rectangle([60, 130, 280, 390], radius=30, fill=col)
    d.text((170 - f1.getlength(lab) / 2, 158), lab, font=f1, fill=(255, 255, 255))
    d.text((320, 210), txt, font=f2, fill=col)
    E.paste_center(img, card, 540, 1060, sc)


def recap(img, t):
    if t <= 0:
        return
    im = E.fit_text(["前回：面接で答えられず、", "大学1年の12月5日に戻された"], 60, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=9, hl={1: (255, 216, 77)})
    E.paste_center(img, im, 540, 1420, E.pop(t))


# ---------- 1コマ ----------
def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "open":
        k = kanata_bed("normal")
        img, _ = room_img(k, face_cam(t, s.dur, 0.15), glow=0.6)
        O.clock_big(img, "2026年12月5日（土）", "9:59", grade="大学1年")
        O.counter(img, 3)
        vote_card(img, t, "A", "説明会に出る", (255, 138, 31))
        recap(img, t - 1.2)
    elif n == "sleep":
        k = kanata_bed("sleep" if t < 1.6 else "shock")
        k.set(head_pitch=0.45 if t < 1.6 else 0.05)
        tk = tokei_near(t, "angry", t - 1.0) if t > 1.0 else []
        img, _ = room_img(k, face_cam(t, s.dur, 0.1), tk, glow=0.25)
        O.clock_big(img, "2026年12月5日（土）", "9:58", grade="大学1年")
        O.counter(img, 3)
        if t < 1.5:
            vote_card(img, t, "B", "もう一度寝る", (110, 116, 140))
    elif n == "flash":
        src = P.shot("interview")
        img = P.frame(src, src.tf + 0.3, raw=True)
        img = O.desat(img, 0.9)
        img = O.glitch(img, 0.5 if t < 0.25 or t > s.dur - 0.25 else 0.12, int(t * 30))
        O.clock_big(img, "2029年6月1日（金）", "10:00", flash=1, grade="大学4年")
    elif n == "wake":
        k = kanata_bed("shock"); k.set(head_pitch=0.0, lean=-0.06)
        img, _ = room_img(k, face_cam(t, s.dur, 0.3), tokei_near(t + 3, "normal"), glow=0.6)
        O.clock_big(img, "2026年12月5日（土）", "9:59", grade="大学1年")
        O.counter(img, 3)
    elif n == "join":
        k = kanata_bed("normal")
        img, _ = room_img(k, face_cam(t, s.dur, 0.35), glow=1.0)
        O.clock_big(img, "2026年12月5日（土）", "10:00", grade="大学1年")
        O.counter(img, 3)
        if t > 0.2:   # カメラオフの札
            f = O.F(BLACK, 56)
            lab = "● カメラ OFF"
            w = f.getlength(lab) + 70
            im = Image.new("RGBA", (int(w), 100), (0, 0, 0, 0))
            dd = ImageDraw.Draw(im)
            dd.rounded_rectangle([0, 0, w - 1, 99], radius=50, fill=(200, 40, 50))
            dd.text((35, 14), lab, font=f, fill=(255, 255, 255))
            E.paste_center(img, im, 540, 1090, E.pop(t - 0.2))
    elif n == "call":
        b = s.lines[1][0]
        img = call_ui(t, s, slide=(t - b) / 0.35 if t > b else 0)
        O.clock_big(img, "2026年12月5日（土）", "10:02", grade="大学1年")
    elif n == "doze":
        nod = min(1, t / 1.6)
        frozen_sleep = t < s.tk + 0.6
        k = kanata_bed("sleep" if t > 0.8 and frozen_sleep else ("normal" if frozen_sleep else "shock"))
        k.set(head_pitch=0.18 + 0.35 * ease(nod) if frozen_sleep else 0.0, lean=0 if frozen_sleep else -0.08)
        tk = tokei_near(t, "angry", t - s.tk) if t > s.tk else []
        img, _ = room_img(k, face_cam(t, s.dur, 0.2), tk, glow=0.8)
        mins = 20 + min(5, int(t * 3)) if frozen_sleep else 25
        O.clock_big(img, "2026年12月5日（土）", f"10:{mins:02d}", grade="大学1年")
        O.counter(img, 3)
        a = s.lines[0][0]
        if a + 0.3 < t < s.lines[1][0] + 0.2:
            card3(img, (t - a - 0.3) / 0.3)
    elif n == "chiji":
        img = call_ui(t, s, chiji=(t - s.rev) if t > s.rev else 0)
        O.clock_big(img, "2026年12月5日（土）", "10:45", grade="大学1年")
    elif n == "react":
        k = kanata_bed("open")
        k.set(head_pitch=0.05, lean=-0.1)
        img, _ = room_img(k, face_cam(t, s.dur, 0.5), glow=1.0)
        O.clock_big(img, "2026年12月5日（土）", "10:45", grade="大学1年")
        O.counter(img, 3)
    elif n == "after":
        a, b, c = (x[0] for x in s.lines)
        k = kanata_bed("smile" if t > b else "open")
        k.set(head_pitch=0.1)
        tk = tokei_near(t, "eyes" if t > c - 0.1 else "normal", t - (c - 0.7), (3.12, 3.35, 1.62)) if t > c - 0.7 else []
        cam = Camera((lerp(3.2, 3.15, ease(t / s.dur)), 1.95, 1.62), (2.75, 3.6, 1.5), 50)
        img, _ = room_img(k, cam, tk, glow=0.3)
        O.clock_big(img, "2026年12月5日（土）", "11:30", grade="大学1年")
        O.counter(img, 3)
        if t < b:
            u = ease((t - 0.2) / 0.3)
            if u > 0:
                lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                d = ImageDraw.Draw(lay)
                x0, y0 = 70, 700 + (1 - u) * 100
                al = int(255 * u)
                d.rounded_rectangle([x0, y0, W - 70, y0 + 300], radius=40, fill=(250, 250, 250, int(245 * u)))
                d.ellipse([x0 + 30, y0 + 28, x0 + 110, y0 + 108], fill=(255, 138, 31, al))
                d.text((x0 + 52, y0 + 38), "ミ", font=O.F(BLACK, 44), fill=(255, 255, 255, al))
                d.text((x0 + 130, y0 + 42), "ミオ", font=O.F(BLACK, 46), fill=(40, 40, 50, al))
                d.text((x0 + 40, y0 + 130), "見てたでしょ笑", font=O.F(BLACK, 56), fill=(40, 40, 50, al))
                d.text((x0 + 40, y0 + 205), "カメラオフでも名前でバレてる", font=O.F(BLACK, 50), fill=(255, 120, 20, al))
                lay.putalpha(lay.getchannel("A"))
                img.alpha_composite(lay)
    elif n == "end":
        img = P.end_scene(s, t)
        d = ImageDraw.Draw(img)
        O.caption(img, "あなたは説明会、", 560, t, size=80)
        O.caption(img, "カメラ どっち派？", 660, t, size=80, col=(255, 216, 77))
        fa, fb = O.F(BLACK, 110), O.F(BLACK, 48)
        for i, (lab, txt, col) in enumerate((("ON", "顔を出す", (255, 138, 31)), ("OFF", "名前だけ", (110, 116, 140)))):
            x0 = 70 + i * 485
            u = ease((t - 0.3 - i * 0.15) / 0.3)
            if u <= 0:
                continue
            y0 = 760 + (1 - u) * 60
            d.rounded_rectangle([x0, y0, x0 + 455, y0 + 290], radius=40, fill=col)
            d.text((x0 + 227 - fa.getlength(lab) / 2, y0 + 30), lab, font=fa, fill=(255, 255, 255))
            d.text((x0 + 227 - fb.getlength(txt) / 2, y0 + 200), txt, font=fb, fill=(255, 255, 255))
        for txt, y, sz, col, path in ((["コメントで教えてね"], 1130, 56, (255, 216, 77), BLACK),
                                      (["次回 第3話「選ぶのは、こっち側」"], 1225, 46, (255, 255, 255), BLACK),
                                      (["あなたの「力を入れたこと」は、まだ作れる。"], 1320, 44, (255, 255, 255), BOLD),
                                      (["ドットジェイピー広島第一支部", "春インターン申込は12月31日まで"], 1440, 48, (255, 216, 77), BLACK),
                                      (["この物語はフィクションです"], 1550, 28, (180, 186, 210), BOLD)):
            E.paste_center(img, E.fit_text(txt, sz, 1000, fill=col, sw=6, path=path), 540, y)
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
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(2) as ex:
            res = list(ex.map(render_shot, range(len(SH))))
        open(f"{OUT}/list.txt", "w").write("".join(f"file '{o}'\n" for o in res))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{OUT}/list.txt", "-c", "copy", f"{OUT}/video.mp4"], check=True)
        print("video", round(sum(s.dur for s in SH), 2))
