"""ガクチカ・ループ 第17話「最終報告会」（見直し後のリメイク版台本・11/24 ゆうきさんOK）
冒頭「最初は、答えるために来た。」→ 3/27（土）13:00 控え室：ハルト「NPOの人たちに聞いた話、入れてくれた？」（第16話の回収）
トケイ「最初に書いた自己PR、覚えてるのだ？」→「人前で、自分の考えを、伝えられるようになりたい」（第5・14話の回収）→ ミオ「カナタ、次だよ。」
発表「最初は、面接で答えるために、参加しました。」…「だから、聞きに行きました。」（第16話のメモ3つ）→ トケイ「…伝えられたのだ。」
森下議員への手紙 → 修了認定証、ミオ「カナタ、変わったね。」「説明会のときは、ほとんどしゃべらなかったのに。」（3周目の第9話）
気づく：第10話の声「答えのためじゃなくて…気になるほうで、選んだ。」→「あのときは、選び方だけだった」→「…答えのためじゃ、なかったんだ。」
→ トケイ「じゃあ、何のためだったのだ？」→「……知りたかったんだ。この街の人が、何を思ってるか。」（第10話＝選び方、第17話＝理由そのもの）
3/31（水）23:59：第8話の声「…行ってるし、これで答えられる。」→「前は、これで答えられるって、思ってた」→ トケイ「行くのだ。」→ 0:00
場面ごとに0.2秒の余韻、転換音・環境音6割、効果音7割。最後の画面と投稿文にチームの※。"""
import math, os, shutil, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import g3d as G
from g3d import Camera, Rig, render, hexc
import characters as C
import ep1b as O
import ep1c as P
import ep2 as Q
import ep3 as R
import ep4 as F
import ep6 as S6
import ep9 as S9
import ep11 as S11
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep17"
BLACK, BOLD = O.BLACK, O.BOLD
YEL = (255, 216, 77)
O.SPEAK["H"] = ("ハルト", (110, 200, 130))
PAD = 0.2
DATE = "2027年3月27日（土）"

# 振り返りの声（前の話の声をそのまま使う）
FLASH = {"f10": f"{HERE}/voice/ep10/15.wav", "f8": f"{HERE}/voice/ep8/02.wav"}
VO = {}


def vo(i):
    if i not in VO:
        p = FLASH.get(i, f"{HERE}/voice/ep17/{i}.wav")
        with wave.open(p) as w:
            assert w.getframerate() == SR
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("H", "緊張してる？"),
    "02": ("K", "…してる。|でも、[地方大会]ほどじゃない。"),
    "03": ("H", "NPOの人たちに聞いた話、|[入れてくれた]？"),
    "04": ("K", "うん。『[送り迎え]できる大人が、|足りない』って。"),
    "05": ("K", "…公園で聞いた|『[見守る大人]が減った』と、|同じだった。"),
    "06": ("H", "…[つながった]な。"),
    "07": ("T", "カナタ。最初に書いた|[自己PR]、覚えてるのだ？"),
    "08": ("K", "…人前で、自分の考えを、|[伝えられるように]なりたい。"),
    "09": ("T", "[今日が]、その日なのだ。"),
    "10": ("M", "カナタ、[次だよ]。"),
    "11": ("K", "宇野カナタです。|森下議員の事務所で、|2か月、インターンをしました。"),
    "12": ("K", "…最初は、|[面接で答えるため]に、|参加しました。"),
    "13": ("K", "議会は、[分からない言葉]|ばかりでした。|でも、聞いたら、教えてもらえました。"),
    "14": ("K", "地方大会では、[負けました]。|『地域の人には聞きましたか』|と聞かれて、何も言えませんでした。"),
    "15": ("K", "…だから、[聞きに行きました]。"),
    "16": ("K", "道が危ない。行く場所がない。|見守る大人が、減った。|…[地図の上]では、|分からないことでした。"),
    "17": ("T", "…[伝えられた]のだ。"),
    "18": ("K", "森下さんへ。"),
    "19": ("K", "一緒に、聞きに行ってくれて"),
    "20": ("M", "カナタ、[変わった]ね。"),
    "21": ("K", "…そうですか？"),
    "22": ("M", "説明会のときは、|[ほとんど]しゃべらなかったのに。"),
    "23": ("K", "（…あのときは、|[選び方]だけだった。）"),
    "24": ("K", "（でも本当は、[最初から]…）"),
    "25": ("K", "…[答えのためじゃ]、|なかったんだ。"),
    "26": ("T", "じゃあ、|[何のため]だったのだ？"),
    "27": ("K", "……[知りたかった]んだ。|この街の人が、|何を思ってるか。"),
    "28": ("K", "前は、『[これで答えられる]』って、|思ってた。"),
    "29": ("T", "…[今は]？"),
    "30": ("K", "…分かんない。|でも、[話したいこと]が、ある。"),
    "31": ("T", "[怖く]ないのだ？"),
    "32": ("K", "…[怖い]よ。"),
    "33": ("T", "[行く]のだ。"),
    "34": ("K", "…うん。"),
}
NOSUB_IDS = {"18", "19", "f10", "f8"}          # 手紙は便せんの文字で見せる／振り返りは前の話の字幕のまま


def subtitle(img, sid):
    who, text = TEXT[sid]
    name, col = O.SPEAK[who]
    lines = text.split("|")
    d = ImageDraw.Draw(img)
    f, fn = O.F(BLACK, 70), O.F(BLACK, 40)
    y = 1470 - (len(lines) - 1) * 60
    nw = fn.getlength(name) + 40
    d.rounded_rectangle([540 - nw / 2, y - 78, 540 + nw / 2, y - 18], radius=30, fill=col)
    d.text((540 - nw / 2 + 20, y - 74), name, font=fn, fill=(20, 20, 30))
    for i, ln in enumerate(lines):
        ff = f
        while ff.getlength(ln.replace("[", "").replace("]", "")) > 1000:
            ff = O.F(BLACK, ff.size - 4)
        O.rich_line(d, 540, y + i * 86, ln, ff)


def seq(ids, start=0.4, gap=0.32, extra=None):
    out, t = [], start
    for i in ids:
        t += (extra or {}).get(i, 0)
        out.append((t, i))
        t += L(i) + gap
    return out, t


def at(s, i):
    return next(t0 for t0, j in s.lines if j == i)


def plan():
    S = []
    S.append(O.Shot("cold", 5.0, []))                                                     # 最初は、答えるために来た。→ 2.4秒でタイトル
    ln, t = seq(["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"], 1.2,
                extra={"02": 0.4, "03": 0.6, "04": 0.3, "05": 0.4, "06": 0.6, "07": 0.8, "08": 0.6, "09": 0.6, "10": 1.0})
    S.append(O.Shot("green", t + 1.0, ln))                                                # 13:00 控え室
    ln, t = seq(["11", "12", "13", "14", "15"], 1.4, extra={"12": 0.6, "13": 0.9, "14": 0.5, "15": 0.8})
    S.append(O.Shot("talk", t + 0.8, ln))                                                 # 13:20 発表（前半）
    ln, t = seq(["16", "17"], 0.8, extra={"17": 2.6})
    s = O.Shot("talk2", t + 1.4, ln); s.clap = at_(ln, "16") + L("16") + 0.5; S.append(s)    # スライドのメモ → 拍手 → トケイ
    ln, t = seq(["18", "19"], 1.0, extra={"19": 0.8})
    s = O.Shot("letter", t + 1.6, ln); S.append(s)                                        # 手紙
    ln, t = seq(["20", "21", "22"], 2.4, extra={"20": 0.4, "21": 0.6, "22": 0.4})
    s = O.Shot("cert", t + 1.8, ln); S.append(s)                                          # 修了認定証
    ln, t = seq(["f10", "23", "24", "25", "26", "27"], 1.6, extra={"23": 1.0, "24": 0.6, "25": 1.6, "26": 1.1, "27": 1.1})
    s = O.Shot("realize", t + 2.6, ln); s.hit = at_(ln, "25") + L("25") + 0.05; S.append(s)   # 気づく
    ln, t = seq(["f8", "28", "29", "30", "31", "32", "33", "34"], 2.2,
                extra={"28": 1.0, "29": 0.6, "30": 0.6, "31": 0.9, "32": 0.5, "33": 1.4, "34": 0.6})
    s = O.Shot("night", t + 2.4, ln); s.zero = t + 1.0; S.append(s)                       # 3/31 23:59 → 0:00
    S.append(O.Shot("end", 6.5))
    t = 0
    for s in S:
        s.dur += PAD
        n = int(round(s.dur * FPS)); s.start, s.dur = t, n / FPS; t += s.dur
    return S


def at_(ln, i):
    return next(t0 for t0, j in ln if j == i)


SH = plan()
NOSUB = False


def shot(name):
    return next(s for s in SH if s.name == name)


def speaking(s, t):
    cur = None
    for (t0, sid) in s.lines:
        if t0 <= t <= t0 + L(sid) + 0.15:
            cur = sid
    return cur


def last_line(s, t):
    last = None
    for (t0, i) in s.lines:
        if t >= t0 - 0.1:
            last = i
    return last


# ---------- セット：最終報告会の会場（文字・ロゴなし） ----------
def stage_set():
    S = []
    S += P.blocks(-3, 9, -5, 10, -1, 0, hexc("#5a4a42"), 0.04, 171)
    S += P.blocks(-3, 9, 9, 10, 0, 6, hexc("#2e3446"), 0.02, 172)
    S += P.blocks(-4, -3, -5, 10, 0, 6, hexc("#d8d2c8"), 0.02, 173)
    S += P.blocks(9, 10, -5, 10, 0, 6, hexc("#d8d2c8"), 0.02, 174)
    S.append(P.slab(-1.0, 5.2, 0, 8.0, 3.8, 0.6, hexc("#7a5a42")))
    S.append(P.slab(0.9, 8.85, 1.6, 4.2, 0.1, 2.6, hexc("#f4f6fa"), glow=True))
    S.append(P.slab(2.65, 5.7, 0.6, 0.7, 0.5, 1.05, hexc("#4a3a30")))
    S.append(P.slab(2.6, 5.75, 1.65, 0.8, 0.4, 0.05, hexc("#f2c94c")))     # 演台の花（黄色）
    return S


STAGE = stage_set()
SEATS = [(x, y) for y in (2.4, 0.9, -0.6, -2.1) for x in (-1.6, 0.0, 1.6, 4.4, 6.0, 7.6)]
BG_HALL = E.sky((60, 64, 80), (90, 94, 110)).convert("RGB").resize((W * G.SS, H * G.SS))
BG_NIGHT = P.BG_ROOM
KS = (3.0, 6.55, 0.6)


def kanata(pos, yaw, expr="normal", **pose):
    r = Rig(C.KANATA_SUIT, pos, yaw, tag="kanata")
    r.set(armL=0.05, armR=0.05)
    r.set(**pose)
    r.expr = expr
    return r


def audience(t, clap=0.0):
    """客席（インターン生・関係者。後ろ姿か、舞台を向く）"""
    out = []
    mob = S6.MOB
    for i, (x, y) in enumerate(SEATS):
        if (i * 7) % 5 == 3:
            continue
        r = Rig(mob[i % len(mob)], (x, y, 0), 0.0, tag=f"au{i}")
        c = clap * (0.35 + 0.35 * abs(math.sin(t * 14 + i)))
        r.set(sit=True, armL=0.5 + c, armR=0.5 + c, head_pitch=-0.05)
        out += r.boxes()
    for x, y in SEATS:
        out.append(P.slab(x - 0.35, y - 0.05, 0, 0.7, 0.25, 0.9, hexc("#3a3a44")))   # いすの背もたれ
    return out


def stage_img(t, cam, kexpr="normal", talk=False, shake=0.0, clap=0.0, tk=()):
    k = kanata(KS, math.pi, kexpr, armL=0.5 + shake * 0.05 * math.sin(t * 37),
               armR=0.5 + (0.18 * math.sin(t * 5) if talk else 0) + shake * 0.05 * math.sin(t * 41 + 1))
    img, _ = render(STAGE + k.boxes() + audience(t, clap) + list(tk), cam, BG_HALL)
    return img.convert("RGBA")


def clock(img, date, time_, flash=0.0):
    O.clock_big(img, date, time_, flash=flash, grade="大学1年")
    O.counter(img, 1)


def slide_memo(img, u):
    """発表スライド：地域で聞いた声（第16話のメモ）"""
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a = int(255 * e)
    y0 = 740 + (1 - e) * 30
    d.rounded_rectangle([70, y0, W - 70, y0 + 470], radius=14, fill=(250, 252, 255, int(250 * e)), outline=(40, 60, 120, a), width=8)
    ft = O.F(BOLD, 40)
    d.text((540 - ft.getlength("地域で、聞いたこと") / 2, y0 + 28), "地域で、聞いたこと", font=ft, fill=(90, 96, 120, a))
    for j, (ln, col) in enumerate((("道が危ない", (200, 70, 50)), ("放課後に行ける場所がない", (40, 90, 170)), ("見守る大人が減った", (40, 130, 80)))):
        f = O.F(BLACK, 62)
        while f.getlength(ln) > W - 260:
            f = O.F(BLACK, f.size - 2)
        uu = min(1, max(0, u * 3 - j * 0.6))
        d.text((540 - f.getlength(ln) / 2, y0 + 110 + j * 112), ln, font=f, fill=col + (int(255 * ease(min(1, uu))),))
    img.alpha_composite(lay)


LETTER = [("森下さんへ", "18", 0.0), ("分からないことを、", "18", 0.25), ("聞いていいと教えてくれて、", "18", 0.5), ("ありがとうございました。", "18", 0.78),
          ("一緒に、聞きに行ってくれて、", "19", 0.0), ("ありがとうございました。", "19", 0.55), ("宇野カナタ", "19", 0.95)]


def letter(img, s, t):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x0, y0 = 110, 700
    d.rounded_rectangle([x0, y0, W - x0, y0 + 900], radius=10, fill=(255, 253, 244, 255), outline=(200, 190, 160, 255), width=4)
    for j in range(8):
        y = y0 + 150 + j * 96
        d.line([x0 + 50, y, W - x0 - 50, y], fill=(200, 214, 232, 255), width=3)
    for j, (ln, sid, frac) in enumerate(LETTER):
        t0 = at(s, sid) + frac * L(sid)
        if t < t0 - 0.05:
            continue
        a = int(255 * min(1, (t - t0 + 0.05) / 0.3))
        f = O.F(BOLD, 54 if j else 58)
        y = y0 + 80 + j * 96 + (24 if j >= 4 else 0) + (24 if j == 6 else 0)
        x = x0 + 70 if j < 6 else W - x0 - 70 - f.getlength(ln)
        d.text((x, y), ln, font=f, fill=(50, 44, 40, a))
    img.alpha_composite(lay)


def cert(img, u, y0=640):
    """修了認定証"""
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a = int(255 * e)
    y = y0 + (1 - e) * 40
    d.rectangle([150, y, W - 150, y + 520], fill=(255, 252, 240, int(250 * e)))
    d.rectangle([150, y, W - 150, y + 520], outline=(200, 160, 60, a), width=10)
    d.rectangle([172, y + 22, W - 172, y + 498], outline=(220, 190, 110, a), width=3)
    f1, f2, f3 = O.F(BLACK, 76), O.F(BLACK, 58), O.F(BOLD, 34)
    d.text((540 - f1.getlength("修了認定証") / 2, y + 70), "修了認定証", font=f1, fill=(60, 50, 40, a))
    d.text((540 - f2.getlength("宇野 カナタ 殿") / 2, y + 210), "宇野 カナタ 殿", font=f2, fill=(40, 40, 50, a))
    for j, ln in enumerate(("春期インターンシップの", "全課程を修了したことを認めます")):
        d.text((540 - f3.getlength(ln) / 2, y + 330 + j * 52), ln, font=f3, fill=(70, 70, 80, a))
    img.alpha_composite(lay)


def flash_img(src, t, label):
    """振り返り：前の話の画を、色あせさせて重ねる"""
    im = src.convert("RGB")
    g = im.convert("L").convert("RGB")
    im = Image.blend(im, g, 0.55)
    im = Image.blend(im, Image.new("RGB", (W, H), (120, 96, 60)), 0.18).convert("RGBA")
    im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 40)))
    F.pill(im, label, 1700, 48, (90, 80, 70))
    return im


_FL = {}


def flash_src(key, t):
    if key == "f10":
        import ep10 as V10
        s = next(x for x in V10.SH if x.name == "home")
        t0 = next(a for a, i in s.lines if i == "15")
        return V10.frame(s, t0 + min(t, V10.L("15") - 0.05))
    import ep8 as V8
    s = next(x for x in V8.SH if x.name == "d331")
    t0 = next(a for a, i in s.lines if i == "02")
    return V8.frame(s, t0 + min(t, V8.L("02") - 0.05))


def hook(img, t):
    if t < 2.4:
        im = E.fit_text(["最初は、", "答えるために来た。"], 112, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={1: YEL})
        E.paste_center(img, im, 540, 1500, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["ガクチカ・ループ 第17話", "最終報告会"], 96, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1500, E.pop(t - 2.4))


# ---------- 1コマ ----------
def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    last = last_line(s, t)
    u = ease(t / s.dur)
    if n == "cold":                                     # 舞台の上、カナタの背中越しに客席
        cam = Camera((lerp(3.65, 3.6, u), lerp(8.6, 8.4, u), 3.0), (2.2, 0.0, 0.9), 54)
        img = stage_img(t, cam, "resolve")
        clock(img, DATE, "13:00")
        hook(img, t)
    elif n == "green":                                  # 控え室：カナタとハルト、トケイ、ミオが呼びに来る
        k = R.kanata_seat("resolve" if t > at(s, "08") else "normal")
        k.spec = C.KANATA_SUIT
        k.set(head_pitch=0.25 if at(s, "07") - 0.2 < t < at(s, "08") else 0.0)
        h = Rig(C.HARUTO, (3.0, 5.5, 0), math.pi, tag="haruto")
        h.set(sit=True, armL=0.55, armR=0.55)
        h.expr = "smile" if last in ("06",) or (last == "10" or t > at(s, "10")) else "normal"
        t10 = at(s, "10")
        wu = ease(min(1, max(0, (t - (t10 - 1.6)) / 1.3)))
        mio = Rig(C.MIO, (lerp(-0.8, 1.6, wu), 2.4, 0), -math.pi / 2, tag="mio")
        mio.set(armL=0.05, armR=0.05)
        if 0 < wu < 1:
            S9.walk(mio, t, 1 - wu * 0.3)
        mio.expr = "smile"
        t7 = at(s, "07")
        tk = list(C.tokei_boxes((2.4, 2.6, 1.35 + (1 - ease(min(1, max(0, t - t7 + 0.8) / 0.5))) * 1.2), t, "eyes", 0.42, -0.3)) \
            if t7 - 0.8 < t < at(s, "10") - 0.3 else []
        if last in ("01", "03", "06"):                  # カナタの背中越しにハルト
            cam = R.cam_mio(t, s.dur)
        elif last in ("10",):                           # ミオ（入口）とカナタ
            cam = Camera((lerp(3.95, 3.9, u), lerp(1.5, 1.55, u), 2.15), (1.6, 2.5, 1.55), 46)
        else:                                           # ハルトの側からカナタ（トケイも）
            cam = Camera((lerp(3.25, 3.2, u), lerp(4.7, 4.5, u), 1.75), (2.75, 2.3, 1.55), 50)
        img, _ = render(R.MEET + k.boxes() + h.boxes() + mio.boxes() + tk, cam, R.BG_MEET)
        img = img.convert("RGBA")
        clock(img, DATE, "13:00")
        S9.bigbadge(img, "控え室", (110, 110, 130))
    elif n == "talk":                                   # 客席から、前で話すカナタ（ゆっくり寄る）
        cam = Camera((lerp(3.25, 3.15, u), lerp(1.0, 2.6, u), 1.95), (3.0, 6.6, 1.9), 44)
        img = stage_img(t, cam, "normal" if t < at(s, "15") else "resolve", talk=sid is not None, shake=1.0)
        clock(img, DATE, "13:20")
        S9.bigbadge(img, "最終報告会", (40, 120, 200))
    elif n == "talk2":
        t17 = at(s, "17")
        clap = ease(min(1, max(0, t - s.clap) / 0.3)) * (1 - ease(min(1, max(0, t - s.clap - 2.6) / 0.6)))
        tk = C.tokei_boxes((3.55, 6.0, 2.0 + (1 - ease(min(1, max(0, t - t17 + 0.8) / 0.5))) * 1.2), t, "eyes", 0.42, math.pi - 0.3) if t > t17 - 0.8 else []
        cam = Camera((lerp(3.15, 3.1, u), lerp(2.6, 3.2, u), 1.95), (3.1, 6.6, 1.95), 44)
        img = stage_img(t, cam, "resolve" if t < s.clap else "smile", talk=sid == "16", shake=1.0 if t < s.clap + 1.0 else 0.4, clap=clap, tk=tk)
        clock(img, DATE, "13:24")
        S9.bigbadge(img, "最終報告会", (40, 120, 200))
        if 0.3 < t < s.clap + 0.2:
            slide_memo(img, (t - 0.3) / 1.2)
    elif n == "letter":                                 # 便せん（後ろは、ぼかした会場）
        cam = Camera((3.2, 2.8, 1.95), (3.0, 6.6, 1.9), 44)
        bg = stage_img(t, cam, "smile").filter(ImageFilter.GaussianBlur(14))
        bg.alpha_composite(Image.new("RGBA", (W, H), (20, 16, 10, 120)))
        img = bg
        letter(img, s, t)
        clock(img, DATE, "14:10")
        S9.bigbadge(img, "森下議員への手紙", (200, 120, 40))
    elif n in ("cert", "realize"):                      # 会場の廊下
        if n == "cert":
            k = kanata(S11.KH, -math.pi / 2, "smile" if t > at(s, "21") + 0.4 else "open",
                       armL=1.1 if t > 1.0 else 0.05, armR=1.1 if t > 1.0 else 0.05)
            mio = Rig(C.MIO, S11.MH, math.pi / 2, tag="mio")
            give = ease(min(1, max(0, t - 0.3) / 0.6))
            mio.set(armL=lerp(1.3, 0.05, give), armR=lerp(1.3, 0.05, give))
            mio.expr = "smile"
            people = k.boxes() + mio.boxes()
            if last in ("20", "22"):                    # カナタの背中越しにミオ
                cam = Camera((lerp(0.95, 1.0, u), lerp(0.95, 1.05, u), 1.95), (3.25, 2.4, 1.7), 42)
            elif last == "21":                          # ミオの背中越しにカナタ
                cam = Camera((lerp(4.3, 4.25, u), lerp(0.95, 1.05, u), 1.95), (2.0, 2.4, 1.75), 42)
            else:                                       # 2人
                cam = Camera((lerp(2.6, 2.65, u), lerp(-4.2, -3.8, u), 1.9), (2.6, 2.4, 1.75), 40)
            img, _ = render(S11.HALL + people, cam, S11.BG_HALL)
            img = img.convert("RGBA")
            clock(img, DATE, "15:00")
            if 0.8 < t < at(s, "20") - 0.1:
                cert(img, (t - 0.8) / 0.4)
                F.pill(img, "修了認定証（履歴書に書ける）", 1240, 50, (200, 150, 40), (20, 20, 30), u=(t - 1.2) / 0.3)
        else:
            t26 = at(s, "26")
            k = kanata(S11.KH, -math.pi / 2, "normal" if t < s.hit - 0.05 else "resolve", armL=1.1, armR=1.1,
                       head_pitch=0.3 if t < at(s, "23") else lerp(0.3, 0.0, ease(min(1, max(0, t - s.hit + 1.2) / 1.0))))
            tk = C.tokei_boxes((2.6, 2.68, 1.8 + (1 - ease(min(1, max(0, t - t26 + 0.8) / 0.5))) * 1.2), t, "eyes", 0.4, -math.pi / 2 + 0.3) if t > t26 - 0.8 else []
            cam = Camera((lerp(4.4, 4.15, u), lerp(2.25, 2.3, u), 1.9), (2.0, 2.45, 1.78), 44)
            img, _ = render(S11.HALL + k.boxes() + list(tk), cam, S11.BG_HALL)
            img = img.convert("RGBA")
            if t > s.hit:
                img.alpha_composite(Image.new("RGBA", (W, H), (255, 240, 200, int(60 * max(0, 1 - (t - s.hit) / 1.5)))))
            clock(img, DATE, "15:05")
            tf = at(s, "f10")
            if tf - 0.4 < t < tf + L("f10") + 0.4:
                fl = flash_img(flash_src("f10", t - tf), t, "12月　活動先を選んだ日")
                a = min(1, (t - tf + 0.4) / 0.3, (tf + L("f10") + 0.4 - t) / 0.3)
                img = Image.blend(img, fl, max(0, a))
    elif n == "night":                                  # 3/31 23:59 部屋
        k = Q.kanata_bed("normal" if t < at(s, "30") else "resolve")
        k.set(head_pitch=0.25 if t < at(s, "28") else 0.12)
        tk = Q.tokei_near(t, "eyes", None, (2.93, 3.2, 1.55))
        img = Q.room_img(k, Q.face_cam(t, s.dur, 0.35), extra=tk)
        img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 50, 120)))
        if t < s.zero:
            clock(img, "2027年3月31日（水）", "23:59")
        else:
            clock(img, "2027年4月1日（木）", "0:00", flash=1.0)
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(220 * max(0, 1 - (t - s.zero) / 1.2)))))
        tf = at(s, "f8")
        if tf - 0.4 < t < tf + L("f8") + 0.4:
            fl = flash_img(flash_src("f8", t - tf), t, "前のループの、3月31日")
            a = min(1, (t - tf + 0.4) / 0.3, (tf + L("f8") + 0.4 - t) / 0.3)
            img = Image.blend(img, fl, max(0, a))
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "あなたの春は、", 600, t, size=86)
        O.caption(img, "何のため？", 730, t, size=110, col=YEL)
        for txt, y, sz, col, path in ((["コメントで教えてね"], 900, 56, (255, 255, 255), BLACK),
                                      (["次回 最終回「最後の面接」"], 1030, 52, (255, 255, 255), BLACK),
                                      (["ドットジェイピー広島第一支部", "春インターン申込は12月31日まで"], 1180, 48, YEL, BLACK),
                                      (["この動画は「勇気を出して一歩を踏み出そう」という", "メッセージを伝えるための創作ドラマです"], 1340, 32, (220, 226, 245), BOLD),
                                      (["※実際の未来自治体では、NPOインターンと議員インターンの参加者が", "同じチームになることはありません。", "同じ活動先ごとのチーム（例：森下議員事務所チーム）で出場します"], 1460, 28, (220, 226, 245), BOLD)):
            E.paste_center(img, E.fit_text(txt, sz, 1000, fill=col, sw=6, path=path), 540, y, E.pop(t - 0.3))
    if sid and sid not in NOSUB_IDS and not NOSUB:
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
    elif sys.argv[1] == "plan":
        for s in SH:
            print(s.name, round(s.start, 2), round(s.dur, 2), [(round(a, 2), b) for a, b in s.lines])
        print("total", round(sum(s.dur for s in SH), 2))
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
