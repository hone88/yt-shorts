"""ガクチカ・ループ 第7話「名刺の渡し方」
2027年2月1日、議員インターン初日。森下議員に同行してあいさつ回り。
事件：キックオフで練習したのに、1か所目で名刺をまた逆さまに出す（相手はやさしく笑う）。
3〜5か所目は早回し（11:00 → 13:00 → 15:30）で、渡し方が少しずつ整う。17:00 事務所へ。
最後に「これで、面接で話せるな」→ トケイ「それで、何を話すのだ？」で第8話へ。
セット・人物は case1.py（旧「議員さんが、いない。」）のものを使う。
python3 ep7.py still <shot> <t> | python3 ep7.py build"""
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
import case1 as K1
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep7"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED, GRN = (255, 216, 77), (255, 90, 90), (90, 220, 120)
DATE = "2027年2月1日（月）"
O.SPEAK["Mo"] = ("森下議員", (170, 172, 182))
O.SPEAK["V"] = ("訪問先の方", (120, 150, 210))

# ---------- 声 ----------
VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep7/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("K", "う、[宇野カナタ]です！"),
    "02": ("Mo", "今日は、[あいさつ回り]だ。|1日で、[6〜7か所]|回ることもあるよ。"),
    "03": ("K", "…はい。"),
    "04": ("V", "ふふ、[逆さま]だね。"),
    "05": ("K", "（…[また、やった]…！）"),
    "06": ("Mo", "緊張するよな。|もう一回、[ゆっくり]。"),
    "07": ("K", "…宇野カナタです。|[よろしくお願いします]。"),
    "08": ("V", "はい、[よろしくね]。"),
    "09": ("T", "[練習でも]、|逆さまだったのだ。"),
    "10": ("K", "…うるさい。"),
    "11": ("Mo", "今日、[どうだった]？"),
    "12": ("K", "…最初、|めちゃくちゃ[緊張]しました。"),
    "13": ("Mo", "初日にしては、[よくやってた]よ。|[5か所目]の名刺、良かったぞ。"),
    "14": ("K", "名刺交換、5か所。|…これで、[面接で話せる]な。"),
    "15": ("T", "…それで、|[何を話す]のだ？"),
    "16": ("K", "え？…|[名刺を、渡した]って。"),
    "17": ("K", "…いよいよ今日から、|[議員インターン]だ。"),
    "18": ("Mo", "最初は、[緊張する]ものだよ。|気にせず、[次、行こう]。"),
    "19": ("K", "…はい。"),
    "20": ("T", "布団から、|[ちゃんと出てきた]のだ。"),
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
    S.append(O.Shot("cold", max(t + 0.3, 4.5), ln))                        # つかみ → 2.4秒でタイトル
    ln, t = seq(["17", "20"], 0.5, extra={"20": 0.3})
    S.append(O.Shot("morning", t + 0.3, ln))                               # 初日の朝、事務所の前
    ln, t = seq(["02", "03"], 0.5, extra={"03": 0.2})
    s = O.Shot("office", t + 0.4, ln); s.card = ln[0][0] + 0.4; S.append(s)
    ln, t = seq(["04", "05", "06", "07", "08"], 0.4, extra={"05": 0.2, "06": 0.3, "07": 0.5})
    s = O.Shot("visit", t + 0.4, ln); S.append(s)
    ln, t = seq(["09", "10", "18", "19"], 0.7, extra={"10": 0.15, "18": 0.5, "19": 0.3})
    S.append(O.Shot("car", t + 0.5, ln))                                   # 次の訪問先へ：森下議員の運転する車
    S.append(O.Shot("ff", 6.3))                                             # 3〜5か所目
    ln, t = seq(["11", "12", "13"], 0.5, extra={"13": 0.2})
    S.append(O.Shot("back", t + 0.6, ln))
    ln, t = seq(["14", "15", "16"], 0.6, extra={"15": 0.4, "16": 0.3})
    S.append(O.Shot("night", t + 1.8, ln))                                  # 最後は秒針だけの間
    S.append(O.Shot("end", 5.5))
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


# ---------- 文字 ----------
def clock(img, time_, extra=None, extra_col=YEL):
    O.clock_big(img, DATE, time_, grade="大学1年")
    O.counter(img, 2)
    if extra:
        d = ImageDraw.Draw(img)
        f = O.F(BLACK, 40)
        w = f.getlength(extra) + 48
        y = O.CLOCK_Y + 372
        d.rounded_rectangle([540 - w / 2, y, 540 + w / 2, y + 62], radius=31, fill=(20, 26, 56), outline=extra_col, width=4)
        d.text((540 - w / 2 + 24, y + 8), extra, font=f, fill=extra_col)


def hook(img, t):
    if t < 2.4:
        im = E.fit_text(["本番でも、", "名刺が逆さま。"], 124, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={1: RED})
        E.paste_center(img, im, 540, 1040, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["ガクチカ・ループ 第7話", "名刺の渡し方"], 96, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1040, E.pop(t - 2.4))


def checks(img, n, u):
    """名刺の渡し方のチェック（だんだん増える）"""
    items = ["両手で", "相手が読める向き", "ゆっくり"]
    f = O.F(BLACK, 46)
    for j, it in enumerate(items):
        ok = j < n
        txt = ("✓ " if ok else "　 ") + it
        w = 560
        y = 1040 + j * 80
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        dl.rounded_rectangle([540 - w / 2, y, 540 + w / 2, y + 66], radius=33,
                             fill=(30, 120, 70, 230) if ok else (20, 24, 40, 170))
        img.alpha_composite(lay)
        ImageDraw.Draw(img).text((540 - w / 2 + 36, y + 6), txt, font=f, fill=(255, 255, 255) if ok else (150, 156, 175))


# ---------- ほかのインターン生・車 ----------
def other_char():
    """同じ事務所のインターン生（1つの事務所に2〜3名）。カナタの体に色ちがいのスーツ"""
    pal = dict(C.KANATA_PAL)
    pal["H"], pal["J"], pal["T"] = hexc("#6a4428"), hexc("#2e3036"), hexc("#3a6ac8")

    def parts(e="normal"):
        old = C.KANATA_PAL
        C.KANATA_PAL = pal
        try:
            return C.kanata_parts("open", "suit")
        finally:
            C.KANATA_PAL = old
    return dict(name="other", label="インターン生", parts=parts)


OTHER = other_char()


def other(pos, yaw, **pose):
    r = Rig(OTHER, pos, yaw, tag="other")
    r.set(armL=0.05, armR=0.05)
    r.set(**pose)
    return r


def car_set():
    """車の中（前から見る）。運転席に森下議員、助手席にカナタ、後ろにインターン生"""
    S = []
    S.append(P.slab(1.6, 1.9, 0.0, 2.8, 3.4, 0.35, hexc("#3a3a40")))           # 床
    for x in (1.95, 3.05):                                                       # 前の座席の背もたれ
        S.append(P.slab(x, 3.05, 0.35, 0.8, 0.25, 1.15, hexc("#4a4a52")))
        S.append(P.slab(x + 0.15, 3.0, 1.5, 0.5, 0.2, 0.3, hexc("#4a4a52")))
    S.append(P.slab(1.8, 4.45, 0.35, 2.4, 0.25, 1.1, hexc("#4a4a52")))          # 後ろの座席
    S.append(P.slab(1.6, 1.85, 0.75, 2.8, 0.45, 0.45, hexc("#2a2a30")))         # ダッシュボード
    S.append(P.slab(2.12, 2.25, 0.85, 0.5, 0.08, 0.32, hexc("#1a1a1e")))          # ハンドル（顔にかからない高さ）
    S.append(P.slab(1.55, 1.9, 2.15, 2.9, 3.4, 0.12, hexc("#d8d8dc")))          # 天井
    for x in (1.5, 4.4):                                                         # 横の窓（外の光）
        S.append(P.slab(x, 2.2, 1.25, 0.06, 2.4, 0.75, hexc("#a8d0f0"), glow=True))
        S.append(P.slab(x, 2.0, 0.35, 0.06, 2.8, 0.9, hexc("#e6e6ea")))
    return S


CAR = car_set()


# ---------- 1コマ ----------
def visit_img(t, dur, mode, kexpr="normal", vexpr="normal", talk_v=False, talk_mo=False, card=True, both=False):
    """訪問先の受付。森下議員の隣にカナタ"""
    k = K1.kanata((3.0, 2.2, 0), 0.0, kexpr, card, armR=1.25 if card else 0.05, armL=1.25 if both else 0.05)
    mo = K1.morishita((2.05, 2.5, 0), 0.15, "normal", armL=0.2 + (0.25 * math.sin(t * 6) if talk_mo else 0))
    rc = K1.reception(("smile" if int(t * 7) % 2 else "normal") if talk_v else vexpr)
    ot = other((1.35, 2.35, 0), 0.25)
    u = ease(t / max(dur, 0.01))
    if mode == "over":        # カナタの背中越しに訪問先の方
        cam = Camera((lerp(3.55, 3.5, u), lerp(0.7, 1.0, u), 1.8), (2.9, 5.4, 1.45), 46)
    elif mode == "face":      # 訪問先の方の側からカナタの顔
        cam = Camera((lerp(3.5, 3.45, u), lerp(4.1, 3.85, u), 1.72), (3.0, 2.2, 1.55), 46)
    else:                     # 森下議員とカナタ（2人）
        cam = Camera((lerp(2.9, 2.85, u), lerp(5.0, 4.8, u), 1.75), (2.5, 2.3, 1.45), 56)
    img, _ = render(K1.LOBBY + k.boxes() + mo.boxes() + rc.boxes() + ot.boxes(), cam, K1.BG_LOBBY)
    return img.convert("RGBA")


def hand_img(t, tint, step):
    """名刺を渡す手のアップ（早回し）"""
    k = K1.kanata((3.0, 2.2, 0), 0.0, "normal", True, armR=1.25, armL=1.25 if step >= 1 else 0.05)
    rc = K1.reception("smile" if step >= 2 else "normal")
    cam = Camera((3.9 - 0.05 * t, 3.9, 1.6), (3.0, 2.9, 1.25), 44)
    img, _ = render(K1.LOBBY + k.boxes() + rc.boxes(), cam, K1.BG_LOBBY)
    img = img.convert("RGBA")
    img.alpha_composite(Image.new("RGBA", (W, H), tint))
    return img


def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "cold":
        img = visit_img(t, s.dur, "face", "open")
        clock(img, "10:30", "1か所目", RED)
        hook(img, t)
    elif n == "office":
        a, b = (x[0] for x in s.lines)
        mo = K1.morishita((3.0, 5.2, 0), math.pi, "normal", armL=0.2 + (0.3 * math.sin(t * 6) if sid == "02" else 0))
        k = K1.kanata((3.0, 2.4, 0), 0.0, "open" if t > b - 0.1 else "normal")
        u = ease(t / s.dur)
        if t < b - 0.1:
            cam = Camera((lerp(3.7, 3.65, u), lerp(1.4, 1.7, u), 1.75), (3.0, 5.2, 1.6), 42)
        else:
            cam = Camera((3.45, 4.3, 1.72), (3.0, 2.4, 1.6), 46)
        img, _ = render(R.MEET + mo.boxes() + k.boxes(), cam, R.BG_MEET)
        img = img.convert("RGBA")
        clock(img, "9:50", "40分前")
        if s.card < t < b - 0.1:
            K1.card_info(img, (t - s.card) / 0.3, ["議員インターン 初日", "あいさつ回り"])
    elif n == "visit":
        a, b, c, d_, e_ = (x[0] for x in s.lines)
        clock_t = "10:30"
        if t < b - 0.1:                     # 「ふふ、逆さまだね」
            img = visit_img(t, b, "over", vexpr="smile", talk_v=sid == "04")
            if t > 0.1:
                Q.big_word(img, "逆さま", t - 0.1, RED, y=1060, size=110)
        elif t < c - 0.1:                   # （…また、やった…！）
            img = visit_img(t - b, c - b, "face", "shock")
            if int(t * 3) % 2 == 0:
                img.alpha_composite(Image.new("RGBA", (W, H), (255, 60, 60, 26)))
        elif t < d_ - 0.1:                  # 森下議員「もう一回、ゆっくり」
            img = visit_img(t - c, d_ - c, "two", "open", talk_mo=sid == "06")
        elif t < e_ - 0.1:                  # 両手で、相手が読める向きに
            img = visit_img(t - d_, e_ - d_, "over", "normal", both=True)
        else:
            img = visit_img(t - e_, s.dur - e_, "over", "normal", vexpr="smile", talk_v=sid == "08", both=True)
        clock(img, clock_t, "1か所目")
    elif n == "car":
        a, b, c, d_ = (x[0] for x in s.lines)
        bob = 0.012 * math.sin(t * 13)
        mo = K1.morishita((2.35, 2.95, 0), math.pi, "normal", sit=True, armL=1.2, armR=1.2,
                          head_yaw=0.35 if sid in ("18",) else 0.0)
        k = K1.kanata((3.45, 2.95, 0), math.pi, "blank" if t < c else ("normal" if t < d_ + 0.3 else "smile"), sit=True,
                      armL=0.5, armR=0.5, head_yaw=-0.25 if sid == "10" else (-0.35 if c - 0.1 < t < d_ + 0.6 else 0.0))
        ot = other((2.9, 4.35, 0), math.pi, sit=True, armL=0.5, armR=0.5)
        tk = C.tokei_boxes((3.9, 2.55, lerp(1.9, 1.4, ease(min(1, t / 0.5)))), t, "eyes", 0.45, math.pi - 0.3, tag="tokei") if t < c - 0.2 else []
        u = ease(t / s.dur)
        if t < c - 0.15:          # 助手席のカナタとトケイ
            cam = Camera((lerp(3.75, 3.7, u), 0.75 + bob, 1.6), (3.6, 3.0, 1.45), 48)
        else:                     # 運転する森下議員と、助手席のカナタ（後ろにインターン生）
            cam = Camera((2.9, 0.35 + bob, 1.7), (2.9, 3.4, 1.35), 60)
        img, _ = render(CAR + mo.boxes() + k.boxes() + ot.boxes() + tk, cam, K1.BG_SKY)
        img = img.convert("RGBA")
        clock(img, "10:50", "移動中")
        if sid == "10":
            F_ = O.F(BOLD, 34)
            ImageDraw.Draw(img).text((540 - F_.getlength("（小声）") / 2, 1180), "（小声）", font=F_, fill=(230, 232, 240))
    elif n == "morning":
        a, b = (x[0] for x in s.lines)
        k = K1.kanata((2.5, 3.6, 0), math.pi, "normal" if t < b else "blank")
        k.set(head_pitch=-0.05)
        u = ease(t / s.dur)
        cam = Camera((lerp(2.95, 2.9, u), lerp(0.2, 0.7, u), 1.6), (2.6, 4.2, 1.6), 50)
        tk = Q.tokei_near(t, "eyes", t - b + 0.5, (3.25, 3.3, 1.75)) if t > b - 0.5 else []
        img, _ = render(R.OUTSIDE + k.boxes() + tk, cam, R.BG_SKY)
        img = img.convert("RGBA")
        clock(img, "9:30", "インターン初日")
    elif n == "ff":
        # 3〜5か所目：11:00 → 13:00 → 15:30。チェックが1つずつ増える
        seg = min(2, int(t / 2.1))
        tt = t - seg * 2.1
        tint = [(0, 0, 0, 0), (255, 200, 120, 22), (255, 160, 80, 34)][seg]
        img = hand_img(tt, tint, seg)
        clock(img, ["11:00", "13:00", "15:30"][seg], f"{seg + 3}か所目")
        checks(img, seg + 1, tt)
        if t > 4.2:
            O.caption(img, "少しずつ、慣れていく。", 1330, t - 4.2, size=80, col=YEL)
    elif n == "back":
        a, b, c = (x[0] for x in s.lines)
        mo = K1.morishita((3.0, 5.2, 0), math.pi, "normal", armL=0.2 + (0.3 * math.sin(t * 6) if sid in ("11", "13") else 0))
        k = K1.kanata((3.0, 2.4, 0), 0.0, "normal" if t < c + 1.0 else "smile")
        u = ease(t / s.dur)
        if sid == "12" or (b - 0.1 < t < c - 0.1) or t > c + L("13") * 0.8:
            cam = Camera((lerp(3.45, 3.4, u), lerp(4.3, 4.1, u), 1.72), (3.0, 2.4, 1.6), 46)
        else:
            cam = Camera((lerp(3.7, 3.65, u), lerp(1.4, 1.7, u), 1.75), (3.0, 5.2, 1.6), 42)
        img, _ = render(R.MEET + mo.boxes() + k.boxes(), cam, R.BG_MEET)
        img = img.convert("RGBA")
        clock(img, "17:00", "事務所")
    elif n == "night":
        a, b, c = (x[0] for x in s.lines)
        u = ease(t / s.dur)
        k = K1.kanata((3.3, 1.7, 0), math.pi * 1.15, "smile" if t < b else ("normal" if t < c else "blank"))
        tk = C.tokei_boxes((2.8, 1.3, 1.5), t, "eyes", 0.55, math.pi + 0.35, tag="tokei") if t > b - 0.5 else []
        cam = Camera((lerp(3.05, 3.1, u), lerp(-0.4, 0.2, u), 1.75), (3.1, 1.6, 1.6), lerp(48, 40, u))
        img, _ = render(K1.STREET + k.boxes() + tk, cam, K1.BG_SKY)
        img = img.convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 50, 150)))
        clock(img, "18:30")
        if t > c + L("16") + 0.3:
            Q.big_word(img, "……", t - c - L("16") - 0.3, (255, 255, 255), y=1060, size=120)
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "あなたなら、", 560, t, size=80)
        O.caption(img, "初めての名刺交換、", 680, t, size=88, col=YEL)
        O.caption(img, "緊張する？", 790, t, size=88, col=YEL)
        for txt, y, sz, col, path in ((["コメントで教えてね"], 920, 56, (255, 255, 255), BLACK),
                                      (["次回 第8話「それで、何を考えましたか？」"], 1040, 48, (255, 255, 255), BLACK),
                                      (["ドットジェイピー広島第一支部", "春インターン申込は12月31日まで"], 1190, 48, YEL, BLACK),
                                      (["この動画は「勇気を出して一歩を踏み出そう」という", "メッセージを伝えるための創作ドラマです"], 1350, 32, (220, 226, 245), BOLD)):
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
