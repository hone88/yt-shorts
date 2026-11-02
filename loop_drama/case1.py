"""インターン生、事件です。#1「議員さんが、いない。」
python3 case1.py still <shot> <t> | python3 case1.py build"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import g3d as G
from g3d import Camera, Rig, render, hexc, add
import characters as C
import ep1b as O   # 時計・字幕の部品
import ep1c as P   # セットの部品
import ep2 as Q    # 大きな文字
import ep3 as R    # 事務所（選考会の部屋）
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_case1"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED = (255, 216, 77), (255, 90, 90)
DATE = "2027年2月3日（水）"
O.SPEAK["Mo"] = ("森下議員", (170, 172, 182))
O.SPEAK["R"] = ("受付の人", (120, 150, 210))

# ---------- 声 ----------
VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/case1/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("K", "…え、ここから、|[1人]？"),
    "02": ("Mo", "今日は、[あいさつ回り]だ。|[7か所]、回るぞ。"),
    "03": ("K", "な、[7か所]…。"),
    "04": ("Mo", "…すまん、[急な用事]だ。|次の1か所、|[先に行っててくれる]か？"),
    "05": ("K", "え、ぼく[1人]で！？"),
    "06": ("K", "落ち着け。|[名刺]を出して、[名前]を言う。|それだけ。"),
    "07": ("K", "[森下事務所]で、|インターンをしている、|[宇野カナタ]です。"),
    "08": ("R", "学生さんが、1人で？|[えらいね]。|何を勉強してるの？"),
    "09": ("K", "え、えっと…[まだ、何も]。|…だから、|[ここに来てます]。"),
    "10": ("Mo", "すまん！|[どうだった]？"),
    "11": ("K", "…名刺、|[逆さま]に出しかけました。"),
    "12": ("Mo", "はっはっは。|[上出来]だ。"),
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
    out, t = [], start
    for i in ids:
        t += (extra or {}).get(i, 0)
        out.append((t, i))
        t += L(i) + gap
    return out, t


def plan():
    S = []
    ln, t = seq(["01"], 0.35)
    S.append(O.Shot("cold", max(t + 0.3, 4.4), ln))                 # 0〜2.4秒つかみ、2.4〜4.4秒タイトル
    ln, t = seq(["02", "03"], 0.6)
    s = O.Shot("office", t + 0.6, ln); s.card = ln[0][0] + L("02") * 0.5; S.append(s)
    ln, t = seq(["04", "05"], 0.9, extra={"05": 0.3})
    s = O.Shot("street", t + 0.5, ln); s.ring = 0.1; S.append(s)
    ln, t = seq(["06"], 1.0)
    S.append(O.Shot("wait", t + 0.4, ln))
    ln, t = seq(["07"], 1.1)                                       # 名刺を逆さまに出しかける間
    s = O.Shot("greet", t + 0.4, ln); s.flip = 0.3; S.append(s)
    ln, t = seq(["08", "09"], 0.3, extra={"09": 0.2})
    S.append(O.Shot("talk", t + 0.5, ln))
    ln, t = seq(["10", "11", "12"], 0.6, extra={"11": 0.2, "12": 0.3})
    S.append(O.Shot("back", t + 0.8, ln))
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


# ---------- 人物 ----------
def card_parts(e="normal"):
    """スーツのカナタ＋右手の名刺"""
    return C.kanata_parts(e, "suit") + [dict(bone="armR", off=(-0.13, 0.1, -0.68), size=(0.26, 0.02, 0.16), color=hexc("#ffffff"))]


KANATA_CARD = dict(name="kanata", label="カナタ（名刺）", parts=card_parts)


def kanata(pos, yaw, expr="normal", card=False, **pose):
    r = Rig(KANATA_CARD if card else C.KANATA_SUIT, pos, yaw, tag="kanata")
    r.set(armL=0.05, armR=0.05)
    r.set(**pose)
    r.expr = expr
    return r


def morishita(pos, yaw, expr="normal", **pose):
    r = Rig(C.MORISHITA, pos, yaw, tag="mo")
    r.set(armL=0.05, armR=0.05)
    r.set(**pose)
    r.expr = expr
    return r


def reception(expr="normal"):
    r = Rig(C.RECEPTION, (3.0, 5.4, 0), math.pi, tag="rc")
    r.set(armL=0.4, armR=0.4)
    r.expr = expr
    return r


# ---------- セット ----------
def lobby_set():
    """会社の受付（会社名・ロゴは出さない）"""
    S = []
    S += P.blocks(-1, 7, -2, 8, -1, 0, hexc("#c8c4bc"), 0.04, 61)
    S += P.blocks(-1, 7, 8, 9, 0, 4, hexc("#ece8e0"), 0.02, 62)
    S += P.blocks(-2, -1, -2, 8, 0, 4, hexc("#ece8e0"), 0.02, 63)
    S += P.blocks(7, 8, -2, 8, 0, 4, hexc("#ece8e0"), 0.02, 64)
    S += P.blocks(-1, 7, -3, -2, 0, 4, hexc("#ece8e0"), 0.02, 65)
    S += P.blocks(-1, 7, -2, 8, 4, 5, hexc("#f8f8f8"), 0.02, 66)
    S.append(P.slab(1.4, 4.7, 0, 3.2, 0.5, 1.05, hexc("#7a5a42")))       # 受付の台
    S.append(P.slab(1.35, 4.65, 1.05, 3.3, 0.6, 0.06, hexc("#e8e2d6")))
    S.append(P.slab(1.6, 7.94, 2.2, 2.8, 0.05, 0.7, hexc("#3a4a6a")))     # 奥の壁の板（文字なし）
    S += [P.slab(5.6, 7.2, 0, 0.6, 0.6, 0.5, hexc("#6a4a30")), P.slab(5.55, 7.15, 0.5, 0.7, 0.7, 1.2, hexc("#4a9a4a"))]
    S += [P.slab(-0.6, 6.6, 0, 0.6, 0.6, 0.5, hexc("#6a4a30")), P.slab(-0.65, 6.55, 0.5, 0.7, 0.7, 1.0, hexc("#4a9a4a"))]
    return S


LOBBY = lobby_set()
BG_LOBBY = E.sky((236, 232, 224), (246, 244, 240)).convert("RGB").resize((W * G.SS, H * G.SS))


def street_set():
    S = []
    S += P.blocks(-3, 9, -3, 3, -1, 0, hexc("#9a9ea6"), 0.05, 71)          # 歩道
    S += P.blocks(-3, 9, 3, 7, -1, 0, hexc("#4a4e58"), 0.03, 72)           # 車道
    S += P.blocks(-3, 9, 8, 9, 0, 5, hexc("#d8cfc0"), 0.03, 73)            # 向かいのビル
    for x in (-2.2, 0.4, 3.0, 5.6):
        S.append(P.slab(x, 7.96, 1.2, 1.4, 0.05, 1.2, hexc("#9fc8e8"), glow=True))
    S.append(P.slab(3.6, 3.2, 0.25, 2.4, 1.3, 0.7, hexc("#f2f2f4")))       # 白い車
    S.append(P.slab(3.85, 3.3, 0.95, 1.7, 1.1, 0.55, hexc("#e6e6ea")))
    S.append(P.slab(3.9, 3.25, 1.0, 1.6, 0.05, 0.45, hexc("#6a8aa8"), glow=True))   # 窓
    for x in (3.8, 5.6):
        S.append(P.slab(x, 3.1, 0, 0.45, 0.25, 0.45, hexc("#1a1a1e")))     # タイヤ
        S.append(P.slab(x, 4.4, 0, 0.45, 0.25, 0.45, hexc("#1a1a1e")))
    return S


STREET = street_set()
BG_SKY = E.sky((120, 180, 240), (220, 236, 250)).convert("RGB").resize((W * G.SS, H * G.SS))


# ---------- 文字 ----------
def clock(img, time_, extra=None, extra_col=YEL):
    O.clock_big(img, DATE, time_, grade="議員インターン 3日目")
    if extra:
        d = ImageDraw.Draw(img)
        f = O.F(BLACK, 40)
        w = f.getlength(extra) + 48
        y = O.CLOCK_Y + 296
        d.rounded_rectangle([540 - w / 2, y, 540 + w / 2, y + 62], radius=31, fill=(20, 26, 56), outline=extra_col, width=4)
        d.text((540 - w / 2 + 24, y + 8), extra, font=f, fill=extra_col)


def note(img, text, y=1505):
    """読み上げなしの小さな注記"""
    f = O.F(BOLD, 30)
    w = f.getlength(text) + 36
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle([540 - w / 2, y, 540 + w / 2, y + 48], radius=12, fill=(0, 0, 0, 150))
    img.alpha_composite(lay)
    ImageDraw.Draw(img).text((540 - w / 2 + 18, y + 6), text, font=f, fill=(235, 238, 245))


def hook_title(img, t):
    if t < 2.4:
        im = E.fit_text(["議員さんが、", "いない。"], 128, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={1: RED})
        E.paste_center(img, im, 540, 1020, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["インターン生、", "事件です。#1"], 96, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1020, E.pop(t - 2.4))


def card_info(img, u, lines):
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    f = O.F(BLACK, 56)
    w = max(f.getlength(x) for x in lines) + 80
    y0 = 650 + (1 - e) * 30
    d.rounded_rectangle([540 - w / 2, y0, 540 + w / 2, y0 + 40 + 76 * len(lines)], radius=30, fill=(220, 120, 40, int(240 * e)))
    for j, ln in enumerate(lines):
        d.text((540 - f.getlength(ln) / 2, y0 + 22 + j * 76), ln, font=f, fill=(255, 255, 255, int(255 * e)))
    img.alpha_composite(lay)


# ---------- 1コマ ----------
def lobby_kanata_face(t, dur, expr, card=False, push=0.2, **pose):
    k = kanata((3.0, 2.2, 0), 0.0, expr, card, **pose)
    u = ease(t / max(dur, 0.01))
    cam = Camera((lerp(3.55, 3.5, u), lerp(4.1, 4.1 - push, u), 1.72), (3.0, 2.2, 1.55), 46)
    img, _ = render(LOBBY + k.boxes() + reception().boxes(), cam, BG_LOBBY)
    return img.convert("RGBA")


def lobby_over(t, dur, rexpr="normal", talk=False, card=False):
    """カナタの背中越しに受付の人"""
    k = kanata((3.0, 2.2, 0), 0.0, "normal", card, armR=1.25 if card else 0.05)
    rc = reception(rexpr if not talk else ("smile" if int(t * 7) % 2 else "normal"))
    u = ease(t / max(dur, 0.01))
    cam = Camera((lerp(3.75, 3.7, u), lerp(1.2, 1.45, u), 1.75), (3.0, 5.4, 1.5), 40)
    img, _ = render(LOBBY + k.boxes() + rc.boxes(), cam, BG_LOBBY)
    return img.convert("RGBA")


def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "cold":
        img = lobby_kanata_face(t, s.dur, "blank", push=0.35)
        clock(img, "11:50", "1人", RED)
        hook_title(img, t)
    elif n == "office":
        mo = morishita((3.0, 5.2, 0), math.pi, "normal", armL=0.2 + (0.3 * math.sin(t * 6) if sid == "02" else 0))
        k = kanata((3.0, 2.4, 0), 0.0, "shock" if t > s.lines[1][0] else "normal")
        u = ease(t / s.dur)
        if t < s.lines[1][0] - 0.1:
            cam = Camera((lerp(3.7, 3.65, u), lerp(1.4, 1.7, u), 1.75), (3.0, 5.2, 1.6), 42)
        else:
            cam = Camera((3.45, 4.3, 1.72), (3.0, 2.4, 1.6), 46)
        img, _ = render(R.MEET + mo.boxes() + k.boxes(), cam, R.BG_MEET)
        img = img.convert("RGBA")
        clock(img, "10:00", "2時間前")
        if t > s.card and t < s.lines[1][0] - 0.1:
            card_info(img, (t - s.card) / 0.3, ["あいさつ回り", "1日6〜7か所のことも"])
    elif n == "street":
        a, b = (x[0] for x in s.lines)
        mo = morishita((2.4, 2.1, 0), math.pi * 0.85, "normal", armR=1.9 if t > 0.3 else 0.05)
        k = kanata((3.3, 1.7, 0), math.pi * 1.15, "shock" if t > b - 0.1 else "normal")
        if t < b - 0.1:
            cam = Camera((2.6, -0.4, 1.7), (2.85, 1.9, 1.55), 46)
        else:
            cam = Camera((3.0, -0.2, 1.75), (3.3, 1.7, 1.62), 38)
        img, _ = render(STREET + mo.boxes() + k.boxes(), cam, BG_SKY)
        img = img.convert("RGBA")
        clock(img, "11:40")
        if t < a:
            Q.big_word(img, "プルルルル…", t, (255, 255, 255), y=1060, size=80)
        if t > a:
            note(img, "※実際には、学生が1人で訪問先へ行くことはほとんどありません")
    elif n == "wait":
        img = lobby_kanata_face(t, s.dur, "blank", card=True, push=0.3, armR=1.0)
        clock(img, "11:50", "残り10分", RED)
    elif n == "greet":
        img = lobby_over(t, s.dur, card=True)
        clock(img, "12:00")
        if s.flip < t < s.lines[0][0] - 0.1:
            Q.big_word(img, "名刺、逆さま…！", t - s.flip, RED, y=1060, size=80)
    elif n == "talk":
        a, b = (x[0] for x in s.lines)
        if t < b - 0.1:
            img = lobby_over(t, s.dur, "smile", talk=sid == "08")
        else:
            img = lobby_kanata_face(t - b, s.dur - b, "open", push=0.3)
        clock(img, "12:10")
    elif n == "back":
        a, b, c = (x[0] for x in s.lines)
        laugh = t > c
        mo = morishita((3.6, 3.4, 0), math.pi * 1.1, "normal", armR=0.6 if laugh else 0.05)
        k = kanata((2.6, 3.2, 0), math.pi * 0.85, "smile" if laugh else "normal", head_yaw=-0.3)
        u = ease(t / s.dur)
        cam = Camera((lerp(3.15, 3.1, u), lerp(0.3, 0.6, u), 1.72), (3.1, 3.3, 1.55), 48)
        img, _ = render(LOBBY + mo.boxes() + k.boxes(), cam, BG_LOBBY)
        img = img.convert("RGBA")
        clock(img, "12:30")
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "あなたなら、", 560, t, size=84)
        O.caption(img, "1人で行ける？", 680, t, size=100, col=YEL)
        for txt, y, sz, col, path in ((["コメントで教えてね"], 860, 64, (255, 255, 255), BLACK),
                                      (["議員インターン：あいさつ回りは1日6〜7か所のことも"], 1000, 40, (200, 210, 235), BOLD),
                                      (["次の事件 #2「名刺が、あと2枚。」"], 1130, 50, (255, 255, 255), BLACK),
                                      (["ドットジェイピー広島第一支部", "春インターン申込は12月31日まで"], 1270, 48, YEL, BLACK),
                                      (["この物語はフィクションです"], 1400, 28, (180, 186, 210), BOLD)):
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
