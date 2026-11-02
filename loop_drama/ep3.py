"""ガクチカ・ループ 第3話「落とす場じゃない」（1次選考会）。
python3 ep3.py still <shot> <t> | python3 ep3.py build"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import g3d as G
from g3d import Camera, Rig, render, hexc, add
import characters as C
import ep1b as O   # 時計・残りループ・字幕の部品
import ep1c as P   # セットの部品・部屋
import ep2 as Q    # 部屋のカナタ・トケイ・大きな文字・カード
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep3"
BLACK, BOLD = O.BLACK, O.BOLD
YEL = (255, 216, 77)

# ---------- 声 ----------
VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep3/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("K", "[落とされたら]、|どうしよ…。"),
    "02": ("T", "落ちても、|[ループは減らない]のだ。"),
    "03": ("M", "今日は、[落とす場じゃない]よ。|カナタが[伸ばしたい力]を、|一緒に考える場。"),
    "04": ("K", "…え、[落とさない]の？"),
    "05": ("M", "最近、ちょっとでも|[気になったニュース]、ある？"),
    "06": ("K", "…大学の[学費]が、|上がるって話、とか。"),
    "07": ("M", "それ、[いいじゃん]。"),
    "08": ("M", "じゃあ、この辺りから、|[活動先]を探そう。"),
    "09": ("M", "次は[2次選考会]。|実際の活動先を、|[カナタが選ぶ]番だよ。"),
    "10": ("K", "選ぶのは…|[こっち側]？"),
    "11": ("T", "2次選考会は、|[早いほど選べる]のだ。"),
    "12": ("K", "…[来週]で、いっか。"),
    "13": ("T", "…その[来週]、|[危ない]のだ。"),
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
    ln, t = seq(["01", "02"], 0.35)                 # 1コマ目から声とつかみ（おさらいは付けない）
    S.append(O.Shot("outside", t + 0.3, ln))
    ln, t = seq(["03", "04"], 0.5, extra={"04": 1.5})   # ミオのセリフのあと、カードを見せる間
    s = O.Shot("intro", t + 0.4, ln); s.rev = ln[0][0] + L("03") + 0.1; S.append(s)
    S.append(O.Shot("ask", 0.3 + L("05") + 0.4, [(0.3, "05")]))
    ln, t = seq(["06"], 0.3)
    S.append(O.Shot("news", t + 0.3, ln))
    ln, t = seq(["07", "08"], 0.3)
    s = O.Shot("board", t + 1.6, ln); s.b0 = ln[1][0]; S.append(s)
    ln, t = seq(["09", "10"], 0.3, extra={"10": 0.6})   # 「こっち側？」の前に間
    s = O.Shot("next", t + 1.0, ln); s.rev = ln[1][0] + L("10") - 0.2; S.append(s)
    ln, t = seq(["11", "12", "13"], 0.9, extra={"13": 0.5})
    S.append(O.Shot("night", t + 0.6, ln))
    S.append(O.Shot("end", 13.5))   # 第4話「扉が閉まる」への橋渡し
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
def outside_set():
    """広島市青少年センターの前（建物はブロックで簡単に）"""
    S = []
    S += P.blocks(-2, 8, -3, 9, -1, 0, hexc("#9a9ea6"), 0.05, 41)          # 歩道
    S += P.blocks(-2, 8, 6, 7, 0, 5, hexc("#d8d2c4"), 0.03, 42)            # 建物の壁
    for x in (-1.5, 0.7, 4.3, 6.5):                                        # 窓
        for z in (1.0, 2.8):
            S.append(P.slab(x, 5.96, z, 1.1, 0.05, 1.0, hexc("#9fc8e8"), glow=True))
    S.append(P.slab(1.9, 5.95, 0, 1.6, 0.06, 2.2, hexc("#5a6a7a")))       # 入口
    S.append(P.slab(1.4, 5.9, 2.5, 2.6, 0.08, 0.5, hexc("#1e3a6a")))      # 看板
    S += [P.slab(-1.6, 4.2, 0, 0.8, 0.8, 0.6, hexc("#6a4a30")), P.slab(-1.7, 4.1, 0.6, 1.0, 1.0, 1.2, hexc("#4a9a4a"))]
    return S


OUTSIDE = outside_set()
BG_SKY = E.sky((120, 180, 240), (220, 236, 250)).convert("RGB").resize((W * G.SS, H * G.SS))


def meet_set():
    """選考会の部屋（机をはさんでミオと向かい合う）"""
    S = []
    S += P.blocks(-1, 7, -2, 8, -1, 0, hexc("#b8a88e"), 0.05, 51)          # 床
    S += P.blocks(-1, 7, 8, 9, 0, 4, hexc("#e6eef2"), 0.025, 52)           # 奥の壁
    S += P.blocks(-2, -1, -2, 8, 0, 4, hexc("#e6eef2"), 0.025, 53)
    S += P.blocks(7, 8, -2, 8, 0, 4, hexc("#e6eef2"), 0.025, 54)
    S += P.blocks(-1, 7, -3, -2, 0, 4, hexc("#e6eef2"), 0.025, 55)
    S += P.blocks(-1, 7, -2, 8, 4, 5, hexc("#f6f6f6"), 0.02, 56)
    S.append(P.slab(1.4, 7.94, 1.0, 3.2, 0.06, 1.6, hexc("#fafafa")))     # ホワイトボード
    S.append(P.slab(1.35, 7.9, 0.95, 3.3, 0.04, 0.05, hexc("#8a8a90")))
    S.append(P.slab(1.8, 3.4, 0.0, 2.4, 1.4, 0.72, hexc("#e8e2d6")))      # 机
    S.append(P.slab(1.75, 3.35, 0.72, 2.5, 1.5, 0.05, hexc("#f2ede4")))
    S.append(P.slab(2.6, 4.0, 0.77, 0.4, 0.3, 0.01, hexc("#ffffff")))     # 紙
    S.append(P.slab(2.75, 5.25, 0, 0.5, 0.5, 0.5, hexc("#3a4a6a")))      # 椅子
    S.append(P.slab(2.75, 1.85, 0, 0.5, 0.5, 0.5, hexc("#3a4a6a")))
    S += [P.slab(5.6, 7.2, 0, 0.6, 0.6, 0.5, hexc("#6a4a30")), P.slab(5.55, 7.15, 0.5, 0.7, 0.7, 1.0, hexc("#4a9a4a"))]
    return S


MEET = meet_set()
BG_MEET = E.sky((226, 234, 240), (244, 248, 250)).convert("RGB").resize((W * G.SS, H * G.SS))


def kanata_stand(expr="normal"):
    r = Rig(C.KANATA, (2.5, 3.6, 0), math.pi, tag="kanata")
    r.set(armL=0.05, armR=0.05)
    r.expr = expr
    return r


def mio_seat(expr="normal"):
    r = Rig(C.MIO, (3.0, 5.5, 0), math.pi, tag="mio")
    r.set(sit=True, armL=0.55, armR=0.55)
    r.expr = expr
    return r


def kanata_seat(expr="normal"):
    r = Rig(C.KANATA, (3.0, 2.1, 0), 0.0, tag="kanata")
    r.set(sit=True, armL=0.5, armR=0.5)
    r.expr = expr
    return r


def cam_mio(t, dur):
    """カナタの背中越しにミオ"""
    u = ease(t / max(dur, 0.01))
    return Camera((lerp(3.72, 3.68, u), lerp(1.55, 1.8, u), 1.55), (3.0, 5.5, 1.42), 38)


def cam_kanata(t, dur):
    """ミオの側からカナタの顔"""
    u = ease(t / max(dur, 0.01))
    return Camera((lerp(3.4, 3.35, u), lerp(4.25, 4.0, u), 1.52), (3.0, 2.1, 1.42), 44)


def meet_img(cam, mexpr="normal", kexpr="normal", talk=None, t=0.0):
    m, k = mio_seat(mexpr), kanata_seat(kexpr)
    if talk == "M":
        m.expr = "smile" if int(t * 7) % 2 else mexpr
        m.set(armL=0.55 + 0.15 * math.sin(t * 6))
    img, _ = render(MEET + m.boxes() + k.boxes(), cam, BG_MEET)
    return img.convert("RGBA")


def clock(img, date, time_, counter=True):
    O.clock_big(img, date, time_, grade="大学1年")
    if counter:
        O.counter(img, 3)


def hook(img, t):
    """1コマ目のつかみ（2.4秒まで）→ 第3話のタイトル（2.4〜4.4秒）"""
    if t < 2.4:
        im = E.fit_text(["選考会＝", "落とされる場所。"], 120, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={1: (255, 90, 90)})
        E.paste_center(img, im, 540, 1050, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["第3話", "落とす場じゃない"], 70, 900, fill=(255, 255, 255), stroke=(8, 10, 24), sw=8, hl={1: YEL})
        E.paste_center(img, im, 540, 1080, E.pop(t - 2.4))


def sign(img):
    """建物の看板の文字（3Dの看板に重ねる）"""
    pass


def card_mid(img, u, title, lines, y0=640):
    """真ん中のカード（1次選考会とは）"""
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a = int(255 * e)
    hgt = 130 + len(lines) * 92
    y0 = y0 + (1 - e) * 40
    d.rounded_rectangle([40, y0, W - 40, y0 + hgt], radius=40, fill=(10, 12, 30, int(235 * e)), outline=(255, 216, 77, a), width=8)
    ft, fb = O.F(BLACK, 54), O.F(BLACK, 64)
    d.text((540 - ft.getlength(title) / 2, y0 + 26), title, font=ft, fill=(255, 216, 77, a))
    for j, ln in enumerate(lines):
        x = 540 - fb.getlength(ln.replace("[", "").replace("]", "")) / 2
        y = y0 + 108 + j * 92
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


def board_cards(img, t):
    """ホワイトボードに出てくる3段のカード"""
    rows = [("興味", "学費・若者のお金", (64, 110, 220)),
            ("伸ばしたい力", "人に話を聞く力", (40, 160, 110)),
            ("ジャンル", "議員（教育・若者）／NPO（学習支援）", (220, 120, 40))]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i, (lab, txt, col) in enumerate(rows):
        u = ease(min(1, (t - i * 0.7) / 0.25))
        if u <= 0:
            continue
        y = 650 + i * 150 + (1 - u) * 30
        d.rounded_rectangle([60, y, W - 60, y + 128], radius=26, fill=col + (int(242 * u),))
        fl, fx = O.F(BLACK, 40), O.F(BLACK, 50)
        while fx.getlength(txt) > 640:
            fx = O.F(BLACK, fx.size - 2)
        d.text((90, y + 40), lab, font=fl, fill=(255, 240, 200, int(255 * u)))
        d.text((360, y + 34), txt, font=fx, fill=(255, 255, 255, int(255 * u)))
        if i < 2:
            d.text((530, y + 122), "▼", font=O.F(BLACK, 30), fill=(255, 216, 77, int(255 * u)))
    img.alpha_composite(lay)


# ---------- 1コマ ----------
def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "outside":
        k = kanata_stand("open" if t < s.lines[1][0] else "normal")
        k.set(head_pitch=-0.05)
        u = ease(t / s.dur)
        cam = Camera((lerp(2.95, 2.9, u), lerp(0.2, 0.55, u), 1.6), (2.65, 4.2, 1.6), 50)
        tk = Q.tokei_near(t, "eyes" if sid == "02" else "normal", t - 0.5, (3.25, 3.3, 1.75)) if t > 0.5 else []
        img, _ = render(OUTSIDE + k.boxes() + tk, cam, BG_SKY)
        img = img.convert("RGBA")
        clock(img, "2026年12月9日（水）", "15:55")
        f = O.F(BLACK, 40)
        lab = "広島市青少年センター"
        w = f.getlength(lab) + 50
        d = ImageDraw.Draw(img)
        if t > 4.4:
            d.rounded_rectangle([540 - w / 2, 1060, 540 + w / 2, 1126], radius=14, fill=(30, 58, 106))
            d.text((540 - w / 2 + 25, 1068), lab, font=f, fill=(255, 255, 255))
        hook(img, t)
    elif n == "intro":
        a, b = (x[0] for x in s.lines)
        if t < b - 0.1:
            img = meet_img(cam_mio(t, s.dur), talk="M" if sid == "03" else None, t=s.start + t)
        else:
            img = meet_img(cam_kanata(t - b, s.dur - b), kexpr="shock")
        clock(img, "2026年12月9日（水）", "16:00")
        if s.rev < t < b - 0.1:
            card_mid(img, (t - s.rev) / 0.3, "1次選考会", ["[落とす場]じゃない。", "伸ばしたい力を", "一緒に考える場"], y0=760)
    elif n == "ask":
        img = meet_img(cam_mio(t, s.dur), talk="M" if sid else None, t=s.start + t)
        clock(img, "2026年12月9日（水）", "16:10")
    elif n == "news":
        img = meet_img(cam_kanata(t, s.dur), kexpr="normal")
        clock(img, "2026年12月9日（水）", "16:12")
    elif n == "board":
        img = meet_img(cam_mio(t, s.dur), mexpr="smile", talk="M" if sid else None, t=s.start + t)
        clock(img, "2026年12月9日（水）", "16:20")
        if t > s.b0 - 0.2:
            board_cards(img, t - s.b0 + 0.2)
    elif n == "next":
        a, b = (x[0] for x in s.lines)
        if t < b - 0.1:
            img = meet_img(Camera((3.25, 3.05, 1.55), (3.0, 5.5, 1.45), 42), talk="M" if sid == "09" else None, t=s.start + t)
        else:
            img = meet_img(cam_kanata(t - b, s.dur - b), kexpr="open")
        clock(img, "2026年12月9日（水）", "16:30")
        if t > s.rev:
            Q.big_word(img, "選ぶのは、こっち側", t - s.rev, YEL, y=1080, size=96)
    elif n == "night":
        k = Q.kanata_bed("normal")
        k.spec = P.KANATA_PHONE
        k.set(head_pitch=0.3)
        tk = Q.tokei_near(t, "angry" if sid == "13" else "eyes", t - 0.2, (2.88, 3.05, 1.5))
        img = Q.room_img(k, Q.face_cam(t, s.dur, 0.25), tk, glow=0.0)
        img.alpha_composite(Image.new("RGBA", (W, H), (10, 16, 50, 110)))    # 夜
        clock(img, "2026年12月9日（水）", "21:00")
    elif n == "end":
        # 第4話「扉が閉まる」への橋渡し（カナタに寄る → 予約画面を閉じる → 活動先が次々に受付終了 → 大きなタイトル）
        def night_face(tt, dur, expr, push):
            k = Q.kanata_bed(expr)
            k.spec = P.KANATA_PHONE
            k.set(head_pitch=0.28)
            im = Q.room_img(k, Camera((2.72, lerp(1.35, 1.35 + push * 0.6, ease(tt / dur)), 1.75), (2.5, 3.75, 1.58), 44))
            im.alpha_composite(Image.new("RGBA", (W, H), (10, 16, 50, 120)))
            im.alpha_composite(Image.new("RGBA", (W, H), (120, 170, 255, 30)))   # スマホの光
            return im
        if t < 2.6:
            img = night_face(t, 2.6, "normal", 0.5)
            O.caption(img, "その夜、カナタは——", 1330, t - 0.2, size=92)
        elif t < 5.2:
            u = t - 2.6
            img = night_face(2.6 + u, 5.2, "normal" if u < 1.3 else "smile", 0.5)
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(lay)
            fh, fb, fs = O.F(BLACK, 44), O.F(BLACK, 54), O.F(BLACK, 40)
            if u < 1.5:
                d.rounded_rectangle([250, 560, 830, 1180], radius=50, fill=(250, 250, 252, 245), outline=(30, 30, 36), width=14)
                d.text((540 - fh.getlength("2次選考会 予約") / 2, 630), "2次選考会 予約", font=fh, fill=(40, 40, 50))
                d.rounded_rectangle([320, 790, 760, 900], radius=55, fill=(255, 138, 31))
                d.text((540 - fb.getlength("予約する") / 2, 815), "予約する", font=fb, fill=(255, 255, 255))
                tap = u > 0.9
                d.rounded_rectangle([370, 950, 710, 1040], radius=45, fill=(120, 124, 140) if tap else (225, 227, 235))
                d.text((540 - fs.getlength("あとで") / 2, 970), "あとで", font=fs, fill=(255, 255, 255) if tap else (90, 92, 105))
            img.alpha_composite(lay)
            if u > 1.5:
                O.caption(img, "…閉じた。", 1330, u - 1.5, size=150, col=YEL)
        elif t < 7.6:
            # 扉が閉まっていく：気になっていた活動先が、1つずつ受付終了
            u = t - 5.2
            img = Image.new("RGBA", (W, H), (14, 10, 22, 255))
            d = ImageDraw.Draw(img)
            O.caption(img, "1週間後——", 500, u, size=80)
            O.caption(img, "行きたかった活動先", 590, u - 0.1, size=52)
            f = O.F(BLACK, 52)
            for k_ in range(3):
                y = 660 + k_ * 190
                d.rounded_rectangle([170, y, 910, y + 150], radius=30, fill=(40, 42, 60))
                d.text((220, y + 45), f"活動先 {'ABC'[k_]}", font=f, fill=(200, 204, 220))
                if u > 0.5 + k_ * 0.55:
                    st = Image.new("RGBA", (330, 110), (0, 0, 0, 0))
                    sd = ImageDraw.Draw(st)
                    sd.rounded_rectangle([0, 0, 329, 109], radius=18, outline=(235, 60, 70), width=10, fill=(40, 10, 16, 200))
                    fs2 = O.F(BLACK, 56)
                    sd.text((165 - fs2.getlength("受付終了") / 2, 20), "受付終了", font=fs2, fill=(235, 60, 70))
                    st = st.rotate(-8, expand=True)
                    E.paste_center(img, st, 700, y + 75, E.pop(u - 0.5 - k_ * 0.55))
            if u > 1.9:
                O.caption(img, "扉が、閉まっていく。", 1330, u - 1.9, size=88, col=(235, 60, 70))
        else:
            # 次回予告：ガクチカ・ループ 第4話（整理して大きく）
            u = t - 7.6
            img = Image.new("RGBA", (W, H), (12, 14, 30, 255))
            d = ImageDraw.Draw(img)
            def pill(text, y, size, bg, fg=(255, 255, 255), delay=0.0):
                if u < delay:
                    return
                f = O.F(BLACK, size)
                w = f.getlength(text) + size
                bd = Image.new("RGBA", (int(w), int(size * 1.5)), (0, 0, 0, 0))
                ImageDraw.Draw(bd).rounded_rectangle([0, 0, w - 1, size * 1.5 - 1], radius=int(size * 0.75), fill=bg)
                ImageDraw.Draw(bd).text((size / 2, size * 0.14), text, font=f, fill=fg)
                E.paste_center(img, bd, 540, y, E.pop(u - delay))
            pill("ガクチカ・ループ", 440, 64, (60, 70, 110), (220, 228, 245))
            O.caption(img, "第4話", 610, u - 0.1, size=120)
            O.caption(img, "扉が、", 790, u - 0.2, size=150)
            O.caption(img, "閉まる。", 955, u - 0.35, size=190, col=YEL)
            pill("明日公開", 1165, 96, (220, 50, 60), delay=0.6)
            if u > 1.0:
                d.line([(140, 1270), (940, 1270)], fill=(90, 96, 130), width=3)
            for txt, y, sz, col, path in ((["春インターン申込は12月31日まで"], 1360, 56, YEL, BLACK),
                                          (["ドットジェイピー広島第一支部"], 1450, 46, (255, 255, 255), BLACK),
                                          (["この物語はフィクションです"], 1540, 30, (170, 176, 200), BOLD)):
                E.paste_center(img, E.fit_text(txt, sz, 1000, fill=col, sw=5, path=path), 540, y, E.pop(u - 1.0))
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
