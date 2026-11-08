"""ガクチカ・ループ 第8話「それで、何を考えましたか？」
2周目のカナタは2月〜3月、言われた活動には行く。でも任意のイベントの通知は既読だけで、議会も「まあ、いっか」。
3月31日の夜が終わると面接の日へ（ルール④）。「議員インターンをしました」は言えるが、
「それで、何を考えましたか？」で答えられない。世界が止まり、残りループ 2→1。
python3 ep8.py still <shot> <t> | python3 ep8.py build"""
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
import case1 as K1
import ep7 as S7
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep8"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED = (255, 216, 77), (255, 90, 90)

# ---------- 声 ----------
VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep8/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("I", "それで、|[何を考えましたか]？"),
    "02": ("K", "…行ってるし、|これで[答えられる]。"),
    "03": ("T", "[時間]なのだ。"),
    "04": ("K", "[議員インターン]を、|しました。"),
    "05": ("I", "[具体的]には？"),
    "06": ("K", "あいさつ回りをしたり、|議会を見たり……。"),
    "08": ("T", "[経験しただけ]では、|答えにならないのだ。|残り、[1回]なのだ。"),
    "09": ("K", "待って…|[まだ]…！"),
    "10": ("K", "（…よく分からんけど、|[まあ、いっか]。）"),
    "11": ("K", "ど、どんなふうに、|[考えたか]…？"),
    "12": ("K", "[えっと]……。"),
    "13": ("K", "議会は…[むずかしくて]…|それで……。"),
}


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
    S.append(O.Shot("cold", max(t + 0.3, 4.5), ln))                      # つかみ → 2.4秒でタイトル
    ln, t = seq(["10"], 1.0)
    S.append(O.Shot("council", t + 0.3, ln))                             # 2月10日 議会傍聴（上から見下ろす）
    S.append(O.Shot("chat1", 3.2))                                       # オープンチャットの案内 → 既読だけ
    S.append(O.Shot("event", 2.8))                                       # 3月6日 地域のイベント（引きの画）
    S.append(O.Shot("office", 2.4))                                      # 3月12日 事務所でもスマホ
    S.append(O.Shot("chat2", 3.0))                                       # また既読だけ
    S.append(O.Shot("days", 2.2))                                        # 3/20 → 3/25 → 3/31 の早回し
    ln, t = seq(["02"], 1.5)
    S.append(O.Shot("d331", t + 0.4, ln))                                # 3月31日の夜「これで答えられる」
    ln, t = seq(["03"], 3.4)
    s = O.Shot("midnight", t + 0.8, ln); s.zero = 1.4; S.append(s)        # 23:59 → 0:00、ルール④
    ln, t = seq(["04", "05", "06", "01", "11", "12", "13"], 0.5,
                extra={"05": 0.2, "06": 0.2, "01": 0.5, "11": 0.9, "12": 0.5, "13": 0.6})
    s = O.Shot("iv", t + 1.0 + 0.6, ln); s.tf = t + 1.0; S.append(s)      # どもる → 1秒止めて → 世界が止まる
    ln, t = seq(["08"], 1.4)
    s = O.Shot("freeze", t + 0.8, ln); S.append(s)                        # 残りループ 2→1、トケイ
    ln, t = seq(["09"], 0.3)
    s = O.Shot("rewind", t + 2.2, ln); s.t0 = t; S.append(s)              # 2029 → 2026
    S.append(O.Shot("end", 5.0))
    t = 0
    for s in S:
        n = int(round(s.dur * FPS)); s.start, s.dur = t, n / FPS; t += s.dur
    return S


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


# ---------- 人物・セット ----------
def phone_parts(e="normal"):
    return C.kanata_parts(e, "suit") + [dict(bone="armR", off=(-0.12, 0.08, -0.66), size=(0.16, 0.03, 0.26), color=hexc("#1a1c24"))]


KANATA_PHONE_SUIT = dict(name="kanata", label="カナタ（スマホ）", parts=phone_parts)


def kanata_phone(pos, yaw, expr="normal", **pose):
    r = Rig(KANATA_PHONE_SUIT, pos, yaw, tag="kanata")
    r.set(armL=0.05, armR=1.0, head_pitch=0.3)
    r.set(**pose)
    r.expr = expr
    return r


def council_set():
    """議場（政党を思わせる色・旗・ロゴは出さない）。傍聴席は横の高いところ"""
    S = []
    S += P.blocks(-2, 7, -1, 10, -1, 0, hexc("#7a2e2e"), 0.03, 81)          # じゅうたん
    S += P.blocks(-2, 7, 10, 11, 0, 6, hexc("#d8ccb8"), 0.02, 82)           # 正面の壁
    S += P.blocks(-3, -2, -1, 11, 0, 6, hexc("#d8ccb8"), 0.02, 83)
    S += P.blocks(-2, 7, -2, -1, 0, 6, hexc("#d8ccb8"), 0.02, 84)
    S.append(P.slab(0.6, 8.4, 0, 3.8, 1.3, 0.9, hexc("#6a4a30")))           # 議長席の台
    S.append(P.slab(1.4, 8.8, 0.9, 2.2, 0.6, 0.5, hexc("#5a3c26")))
    S.append(P.slab(2.1, 7.3, 0, 0.8, 0.5, 1.1, hexc("#5a3c26")))           # 演台
    for r_ in range(3):                                                     # 議員席の机（演台のほうを向く）
        y = 1.6 + r_ * 1.2
        S.append(P.slab(-1.2, y + 0.55, 0, 6.6, 0.4, 0.75, hexc("#7a5a42")))
    # 傍聴席（右の壁ぎわ、高いところ）
    S.append(P.slab(7.0, -1.0, 2.6, 2.2, 11.0, 0.25, hexc("#5a4a3a")))       # 床
    S.append(P.slab(7.0, -1.0, 2.85, 0.15, 11.0, 0.75, hexc("#3a2c22")))     # 手すり
    for y in (3.0, 4.8, 6.6):                                          # 傍聴席のいす
        S.append(P.slab(7.55, y - 0.3, 2.85, 0.55, 0.6, 0.45, hexc("#4a4a52")))
        S.append(P.slab(8.1, y - 0.3, 2.85, 0.12, 0.6, 1.1, hexc("#4a4a52")))
    S += P.blocks(9, 10, -1, 11, 0, 6, hexc("#d8ccb8"), 0.02, 85)
    return S


COUNCIL = council_set()
BG_COUNCIL = E.sky((214, 204, 186), (236, 228, 214)).convert("RGB").resize((W * G.SS, H * G.SS))


def members(t):
    """議員さんたちは演台・議長席のほうを向いている（傍聴席には背中や横顔）"""
    out = []
    pos = [(-0.6, 1.4), (0.8, 1.4), (2.2, 1.4), (3.6, 1.4), (0.0, 2.6), (1.5, 2.6), (3.0, 2.6), (0.6, 3.8), (2.4, 3.8)]
    for i, (x, y) in enumerate(pos):
        r = Rig(S7.OTHER if i % 3 else C.MORISHITA, (x, y, 0), 0.0, tag=f"m{i}")
        r.set(sit=True, armL=0.5, armR=0.5, head_pitch=0.04 * math.sin(t * 2 + i))
        out += r.boxes()
    sp = Rig(S7.OTHER, (2.5, 7.1, 0), math.pi, tag="sp")                   # 演台で議員席に向かって話す人
    sp.set(armL=0.6 + 0.2 * math.sin(t * 6), armR=0.3)
    return out + sp.boxes()


def tents():
    S = []
    for x in (0.2, 3.6):
        S.append(P.slab(x, 4.6, 2.0, 2.0, 1.6, 0.12, hexc("#f4f4f4")))
        for dx in (0.05, 1.85):
            for dy in (0.05, 1.45):
                S.append(P.slab(x + dx, 4.6 + dy, 0, 0.1, 0.1, 2.0, hexc("#9a9ea6")))
        S.append(P.slab(x + 0.2, 4.7, 0, 1.6, 0.6, 0.8, hexc("#c8a878")))
    return S


# ---------- 文字 ----------
def clock(img, date, time_, n=2, grade="大学1年", flash=0.0, pulse=0.0):
    O.clock_big(img, date, time_, flash=flash, grade=grade)
    O.counter(img, n, pulse)


def badge(img, text, col=YEL):
    d = ImageDraw.Draw(img)
    f = O.F(BLACK, 40)
    w = f.getlength(text) + 48
    y = O.CLOCK_Y + 372
    d.rounded_rectangle([540 - w / 2, y, 540 + w / 2, y + 62], radius=31, fill=(20, 26, 56), outline=col, width=4)
    d.text((540 - w / 2 + 24, y + 8), text, font=f, fill=col)


def notif(img, u, lines, read):
    """任意イベントのお知らせ → 既読"""
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    y0 = 760 + (1 - e) * 30
    h = 120 + 84 * len(lines)
    d.rounded_rectangle([100, y0, W - 100, y0 + h], radius=34, fill=(250, 250, 252, int(240 * e)))
    fh, f = O.F(BOLD, 40), O.F(BLACK, 64)
    d.text((140, y0 + 26), "お知らせ（参加は自由）", font=fh, fill=(64, 110, 220, int(255 * e)))
    for j, ln in enumerate(lines):
        d.text((140, y0 + 90 + j * 84), ln, font=f, fill=(40, 40, 50, int(255 * e)))
    img.alpha_composite(lay)
    if read:
        st = O.F(BLACK, 44)
        ImageDraw.Draw(img).text((W - 140 - st.getlength("既読"), y0 + h - 64), "既読", font=st, fill=(220, 60, 70))


def rule4(img, u):
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    y0 = 720
    d.rounded_rectangle([60, y0, W - 60, y0 + 380], radius=40, fill=(10, 12, 30, int(235 * e)), outline=(255, 216, 77, int(255 * e)), width=8)
    a = int(255 * e)
    ft, fb = O.F(BLACK, 56), O.F(BLACK, 66)
    d.text((540 - ft.getlength("ループのルール④") / 2, y0 + 34), "ループのルール④", font=ft, fill=(255, 216, 77, a))
    for j, ln in enumerate(["3月31日の夜が終わると、", "面接の日へ"]):
        d.text((540 - fb.getlength(ln) / 2, y0 + 140 + j * 96), ln, font=fb, fill=(255, 255, 255, a))
    img.alpha_composite(lay)


def bigbadge(img, text, col):
    """今どこで何をしているか、大きく"""
    f = O.F(BLACK, 66)
    w = f.getlength(text) + 80
    y = O.CLOCK_Y + 380
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle([540 - w / 2, y, 540 + w / 2, y + 100], radius=50, fill=col + (240,))
    img.alpha_composite(lay)
    ImageDraw.Draw(img).text((540 - w / 2 + 40, y + 10), text, font=f, fill=(255, 255, 255))


def phone_chat(t, msgs, read, close):
    """スマホのオープンチャット（アプリ名・ロゴは出さない）。close: 0→1 で画面を閉じる"""
    img = Image.new("RGBA", (W, H), (18, 20, 28, 255))
    if close >= 1:
        return img
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = 120, 640, 960, 1720
    d.rounded_rectangle([x0 - 14, y0 - 14, x1 + 14, y1 + 14], radius=70, fill=(10, 10, 14))
    d.rounded_rectangle([x0, y0, x1, y1], radius=56, fill=(214, 226, 240))
    d.rounded_rectangle([x0, y0, x1, y0 + 150], radius=56, fill=(6, 199, 85))
    d.rectangle([x0, y0 + 100, x1, y0 + 150], fill=(6, 199, 85))
    fh, fs = O.F(BLACK, 46), O.F(BOLD, 30)
    d.text((x0 + 50, y0 + 30), "春インターン生", font=fh, fill=(255, 255, 255))
    d.text((x0 + 50, y0 + 92), "オープンチャット", font=fs, fill=(230, 255, 236))
    fm, fm2, fn = O.F(BLACK, 46), O.F(BOLD, 36), O.F(BOLD, 32)
    for j, (m1, m2) in enumerate(msgs):
        tt = t - 0.3 - j * 0.5
        if tt <= 0:
            continue
        e = ease(min(1, tt / 0.25))
        y = y0 + 200 + j * 270 + (1 - e) * 30
        d.text((x0 + 40, y), "支部スタッフ", font=fn, fill=(90, 96, 110))
        d.rounded_rectangle([x0 + 40, y + 40, x1 - 60, y + 220], radius=30, fill=(255, 255, 255, int(255 * e)))
        d.text((x0 + 70, y + 66), m1, font=fm, fill=(30, 30, 40, int(255 * e)))
        d.text((x0 + 70, y + 136), m2, font=fm2, fill=(80, 84, 100, int(255 * e)))
    if read:
        fr = O.F(BLACK, 40)
        d.text((x1 - 60 - fr.getlength("既読"), y0 + 200 + 2 * 270 - 10), "既読", font=fr, fill=(220, 60, 70))
    img.alpha_composite(lay)
    if close > 0:   # パッと閉じる
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * min(1, close * 1.2)))))
    return img


def more_people(t):
    """イベントに来ている地域の人"""
    out = []
    for i, (x, y, yaw) in enumerate([(0.9, 3.4, 0.3), (1.9, 3.0, -0.4), (3.2, 3.6, 2.8), (0.2, 2.6, 1.2)]):
        r = Rig(S7.OTHER if i % 2 else C.MORISHITA, (x, y, 0), yaw, tag=f"p{i}")
        r.set(armL=0.3 + 0.2 * math.sin(t * 3 + i), armR=0.1)
        out += r.boxes()
    return out


def hook(img, t):
    if t < 2.4:
        im = E.fit_text(["経験は、ある。", "なのに、", "答えられない。"], 112, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={2: RED})
        E.paste_center(img, im, 540, 1040, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["ガクチカ・ループ 第8話", "それで、何を考えましたか？"], 84, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1040, E.pop(t - 2.4))


# ---------- 1コマ ----------
def iv_img(t, kexpr, cam_mode, u, iv_talk=False, tk=(), freeze=0.0, head=0.0):
    iv, k = P.iv_rig(), P.kanata_suit_rig()
    k.expr = kexpr
    if head:
        k.set(head_yaw=head)
    if iv_talk:
        iv.set(armL=0.55 + 0.25 * math.sin(t * 7))
    if cam_mode == "iv":
        cam = Camera((lerp(3.75, 3.6, u), lerp(0.55, 1.0, u), 1.62), (3.0, 5.5, 1.38), 48)
    elif cam_mode == "k":
        cam = Camera((lerp(3.42, 3.36, u), lerp(4.25, 4.0, u), 1.52), (3.0, 2.1, 1.42), 44)
    elif cam_mode == "close":
        cam = Camera((lerp(3.35, 3.2, u), lerp(4.1, 3.65, u), 1.5), (3.0, 2.1, 1.44), lerp(44, 42, u))
    else:   # トケイと2人
        cam = Camera((3.45, 4.75, 1.62), (3.3, 2.05, 1.45), 44)
    img, mask = render(P.OFFICE + iv.boxes() + k.boxes() + list(tk), cam, P.BG_OFFICE, keep={"kanata", "tokei"})
    img = img.convert("RGBA")
    if freeze > 0:
        img = O.desat(img, 0.95 * freeze, mask)
    return img


def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "cold":
        img = iv_img(t, "blank", "close", ease(t / s.dur), freeze=0.0)
        clock(img, "2029年6月1日（金）", "10:05", grade="大学4年")
        hook(img, t)
    elif n == "council":
        u = ease(t / s.dur)
        k = kanata_phone((7.8, 3.0, 2.85), math.pi / 2 + 0.3, "blank" if sid else "normal", sit=True)   # 議場（左）のほうを向いて座る
        if t < 1.3:   # 傍聴席から議場を見下ろす
            cam = Camera((lerp(9.6, 9.5, u), lerp(5.6, 5.3, u), 5.6), (1.6, 4.4, 0.2), 60)
        else:         # 傍聴席のカナタ：議会はそっちのけでスマホ
            cam = Camera((lerp(7.95, 7.9, u), lerp(-0.4, -0.1, u), 4.75), (7.6, 3.0, 4.05), 54)   # 横から：左（議場）を向いて座るカナタ
        img, _ = render(COUNCIL + members(t) + k.boxes(), cam, BG_COUNCIL)
        img = img.convert("RGBA")
        clock(img, "2027年2月10日（水）", "10:30")
        bigbadge(img, "議会を傍聴中", (64, 110, 220))
        for j, (w, x, y) in enumerate([("補正予算", 300, 900), ("付託", 780, 980), ("採決", 420, 1090)]):
            if t > 0.2 + j * 0.3:
                im = E.fit_text([w], 64, 600, fill=(255, 255, 255), stroke=(8, 10, 24), sw=8)
                E.paste_center(img, im, x, y, E.pop(t - 0.2 - j * 0.3))
    elif n in ("chat1", "chat2"):
        first = n == "chat1"
        msgs = ([("2/24（水）企業訪問を行います！", "参加は自由です。申し込みはこちら"), ("3/3（水）公開討論会があります！", "大学生が登壇します")]
                if first else [("3/22（月）議員交流会を行います！", "参加は自由です"), ("3/26（金）公開討論会 第2回", "ぜひ来てください！")])
        date, tm = ("2027年2月19日（金）", "21:00") if first else ("2027年3月18日（木）", "22:00")
        if t < 2.1:
            img = phone_chat(t, msgs, read=t > 1.45, close=max(0, (t - 1.8) / 0.3))
        else:
            k = F.kanata_phone_bed("blank")
            img = Q.room_img(k, F.bed_cam(t - 2.1, s.dur - 2.1, 0.25))
            img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 50, 80)))
            O.caption(img, "既読、だけ。", 1100, t - 2.15, size=120, col=RED)
        clock(img, date, tm)
    elif n == "event":
        u = ease(t / s.dur)
        k = kanata_phone((2.7, 0.6, 0), math.pi, "blank")
        cam = Camera((lerp(2.8, 2.85, u), lerp(-3.8, -3.4, u), 2.6), (2.6, 3.0, 1.0), 56)
        img, _ = render(R.OUTSIDE + tents() + V5.students(t) + more_people(t) + k.boxes(), cam, R.BG_SKY)
        img = img.convert("RGBA")
        clock(img, "2027年3月6日（土）", "13:00")
        bigbadge(img, "地域のイベントに参加中", (40, 150, 90))
        if t > 0.9:
            O.caption(img, "…でも、スマホ。", 1300, t - 0.9, size=96, col=YEL)
    elif n == "office":
        u = ease(t / s.dur)
        k = kanata_phone((3.0, 2.4, 0), 0.0, "blank", sit=True)
        cam = Camera((lerp(3.5, 3.45, u), lerp(4.3, 4.0, u), 1.75), (3.0, 2.4, 1.3), 48)
        img, _ = render(R.MEET + k.boxes(), cam, R.BG_MEET)
        img = img.convert("RGBA")
        clock(img, "2027年3月12日（金）", "15:00")
        bigbadge(img, "事務所で活動中", (200, 120, 40))
        if t > 0.6:
            O.caption(img, "いつも、スマホ。", 1300, t - 0.6, size=96, col=YEL)
    elif n == "days":
        # 3/20 → 3/25 → 3/31 の早回し
        seg = min(2, int(t / 0.75))
        dd = [("2027年3月20日（土）", "8:00"), ("2027年3月25日（木）", "12:00"), ("2027年3月31日（水）", "18:00")][seg]
        src = [shot("office"), shot("event"), shot("council")][seg]
        img = O.glitch(frame_raw(src, 1.2), 0.25, int(t * 30))
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 90)))
        clock(img, *dd)
        O.caption(img, "▶▶ 早送り", 1100, 1.0, size=90, col=(255, 255, 255))
    elif n == "d331":
        k = F.kanata_phone_bed("normal" if not sid else "smile")
        img = Q.room_img(k, F.bed_cam(t, s.dur, 0.3))
        img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 50, 110)))
        clock(img, "2027年3月31日（水）", "22:00")
        im = E.fit_text(["3月31日", "春インターン、最終日。"], 150, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=14, hl={0: YEL})
        E.paste_center(img, im, 540, 960, E.pop(t))
    elif n == "midnight":
        k = F.kanata_phone_bed("sleep")
        img = Q.room_img(k, F.bed_cam(t, s.dur, 0.3))
        img.alpha_composite(Image.new("RGBA", (W, H), (6, 8, 30, 150)))
        if t < s.zero:
            clock(img, "2027年3月31日（水）", "23:59")
        else:
            clock(img, "2027年4月1日（木）", "0:00", flash=1.0)
            rule4(img, (t - s.zero - 0.1) / 0.3)
    elif n == "iv":
        a, b, c, d_, e_, f_, g_ = (x[0] for x in s.lines)
        u = ease(t / s.dur)
        frozen = t >= s.tf
        if t < b - 0.1:
            img = iv_img(t, "open", "k", u)
        elif t < c - 0.1:
            img = iv_img(t, "open", "iv", u, iv_talk=sid == "05")
        elif t < d_ - 0.1:
            img = iv_img(t, "normal", "k", u)
        elif t < e_ - 0.1:                                       # 「それで、何を考えましたか？」
            img = iv_img(t, "normal", "iv", u, iv_talk=sid == "01")
        elif t < g_ + L("13"):                                   # どもる：だんだん顔に寄る
            v = ease(min(1, (t - e_ + 0.1) / (g_ + L("13") - e_)))
            ex = "open" if t < f_ else ("blank" if t < g_ else "shock")
            img = iv_img(t, ex, "close", v * 0.7, head=(0.15 * math.sin(t * 4) if t < g_ else 0.0))
            if t > f_:   # 汗
                img.alpha_composite(Image.new("RGBA", (W, H), (255, 60, 60, int(14 * (1 + math.sin(t * 9))))))
        else:                                                    # 1秒の沈黙 → 世界が止まる
            v = ease(min(1, (t - g_ - L("13")) / 1.0))
            img = iv_img(t, "blank", "close", 0.7 + 0.3 * v, freeze=ease(min(1, (t - s.tf) / 0.5)) if frozen else 0.0)
            if frozen and t - s.tf < 0.25:
                img = Image.blend(img, Image.new("RGBA", (W, H), (255, 255, 255, 255)), 0.35 * (1 - (t - s.tf) / 0.25))
        sec = min(59, 12 + int(t)) if not frozen else min(59, 12 + int(s.tf))
        clock(img, "2029年6月1日（金）", f"10:05:{sec:02d}", grade="大学4年", flash=1.0 if frozen else 0.0)
        if e_ - 0.1 < t < f_ - 0.1:
            Q.big_word(img, "考えた…こと？", t - e_ - 0.2, RED, y=1060, size=96)
        if frozen:
            O.caption(img, "経験しただけでは、\n答えにならない。", 1080, t - s.tf - 0.1, size=86, col=YEL)
    elif n == "freeze":
        a = s.lines[0][0]
        drop = (1 - ease(min(1, t / 0.5))) * 1.6
        tk = C.tokei_boxes((3.62, 2.05, 1.62 + drop), t, "eyes", 0.75, 0.35)
        k_ = "shock"
        img = iv_img(t, k_, "two", 0, tk=tk, freeze=1.0)
        O.clock_big(img, "2029年6月1日（金）", "10:05", flash=1.0, grade="大学4年")
        pulse = max(0, 1 - (t - 0.6) / 0.8) if t > 0.6 else 0.0
        O.counter(img, 1 if t > 0.6 else 2, pulse)
        if 0.6 < t < a - 0.1:
            im = E.fit_text(["残りループ", "2 → 1"], 140, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=14, hl={1: RED})
            E.paste_center(img, im, 540, 1000, E.pop(t - 0.6))
    elif n == "rewind":
        t0 = s.t0
        fz = shot("freeze")
        if t < t0:
            img = iv_img(fz.dur, "shock", "close", 1.0, freeze=1.0)
            O.clock_big(img, "2029年6月1日（金）", "10:05", flash=1.0, grade="大学4年")
            O.counter(img, 1)
        elif t < t0 + 0.35:
            img = O.desat(iv_img(fz.dur, "shock", "close", 1.0), 1)
            O.cracks(img, ease((t - t0) / 0.35))
        else:
            u = (t - t0 - 0.35) / (s.dur - t0 - 0.6)
            if u < 1:
                src = [shot("iv"), shot("d331"), shot("event"), shot("council")][min(3, int(u * 4))]
                img = O.glitch(O.desat(frame_raw(src, src.dur * (1 - (u * 4 % 1))), 1), 1.0, int(t * 30))
                year = 2029 - min(3, int(u * 4))
                O.caption(img, f"{year}", 900, 1.0, size=230, col=YEL)
                O.caption(img, "◀◀ 巻き戻し中", 1120, 1.0, size=70)
            else:
                img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "あなたなら、", 600, t, size=84)
        O.caption(img, "何て答える？", 730, t, size=110, col=YEL)
        for txt, y, sz, col, path in ((["コメントで教えてね"], 900, 56, (255, 255, 255), BLACK),
                                      (["次回 第9話「全部、消えた。」"], 1030, 52, (255, 255, 255), BLACK),
                                      (["ドットジェイピー広島第一支部", "春インターン申込は12月31日まで"], 1180, 48, YEL, BLACK),
                                      (["この動画は「勇気を出して一歩を踏み出そう」という", "メッセージを伝えるための創作ドラマです"], 1340, 32, (220, 226, 245), BOLD)):
            E.paste_center(img, E.fit_text(txt, sz, 1000, fill=col, sw=6, path=path), 540, y, E.pop(t - 0.3))
    if sid and not NOSUB:
        subtitle(img, sid)
    return img


def frame_raw(s, t):
    """巻き戻し用：字幕なしの絵"""
    global NOSUB
    NOSUB = True
    try:
        return frame(s, t)
    finally:
        NOSUB = False


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
