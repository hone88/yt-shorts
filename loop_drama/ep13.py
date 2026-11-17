"""ガクチカ・ループ 第13話「30年後の広島」（リメイク版台本・11/17 ゆうきさんOK）
2/25（木）19:00 未来自治体の準備。チーム4人のビデオ通話（メンバー2人は架空）。「交通でしょ」「子育てだって」でまとまらない → 21:30
ハルト「…一回、整理しよう。」→ カナタが話すがミュート →「…カナタ、ミュートになってる。」
→「子どもが、子どもだけで遊び場まで行ける街。…それなら、交通も子育ても入る。」→「…それだ。」→ ホワイトボード「テーマ：子どもの遊び場」
通話のあと、トケイ「ハルトのやりたいことと、カナタの調べたことが、つながったのだ。」
場面ごとに0.2秒の余韻、転換音・環境音は6割。カメラ（画面）は話し手が変わるときだけ切り替え（注意点8）。"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import g3d as G
from g3d import Camera, Rig, render, hexc
import characters as C
import ep1b as O
import ep1c as P
import ep2 as Q
import ep9 as S9
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep13"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED, GRN = (255, 216, 77), (255, 90, 90), (90, 220, 120)
O.SPEAK["H"] = ("ハルト", (110, 200, 130))
O.SPEAK["A"] = ("メンバー", (200, 150, 230))
O.SPEAK["B"] = ("メンバー", (120, 190, 240))
PAD = 0.2
DATE = "2027年2月25日（木）"

VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep13/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("A", "やっぱり、[交通]でしょ。"),
    "02": ("B", "いや、[子育て]だって。"),
    "03": ("H", "…一回、[整理]しよう。"),
    "04": ("K", "通学のこと調べてて、|思ったんだけど…"),
    "05": ("H", "…カナタ、[ミュート]に|なってる。"),
    "06": ("K", "[えっ]"),
    "07": ("K", "子どもが、[子どもだけで]|遊び場まで行ける街。"),
    "07b": ("K", "…それなら、|[交通も子育ても]入る。"),
    "08": ("H", "…[それだ]。"),
    "09": ("T", "ハルトのやりたいことと、|カナタの[調べたこと]が、|つながったのだ。"),
    "10": ("K", "…うん。"),
}


def subtitle(img, sid):
    who, text = TEXT[sid]
    name, col = O.SPEAK[who]
    lines = text.split("|")
    d = ImageDraw.Draw(img)
    f, fn = O.F(BLACK, 72), O.F(BLACK, 40)
    y = 1560 - (len(lines) - 1) * 80
    nw = fn.getlength(name) + 40
    d.rounded_rectangle([540 - nw / 2, y - 78, 540 + nw / 2, y - 18], radius=30, fill=col)
    d.text((540 - nw / 2 + 20, y - 74), name, font=fn, fill=(20, 20, 30))
    for i, ln in enumerate(lines):
        ff = f
        while ff.getlength(ln.replace("[", "").replace("]", "")) > 1000:
            ff = O.F(BLACK, ff.size - 4)
        O.rich_line(d, 540, y + i * 90, ln, ff)


def seq(ids, start=0.4, gap=0.32, extra=None):
    out, t = [], start
    for i in ids:
        t += (extra or {}).get(i, 0)
        out.append((t, i))
        t += L(i) + gap
    return out, t


def plan():
    S = []
    S.append(O.Shot("cold", 5.0, []))                                                   # つかみ（ミュート）→ 2.4秒でタイトル
    a = 2.8
    ln = [(a, "01"), (a + L("01") * 0.7, "02")]                                          # 声が重なる
    t = ln[1][0] + L("02") + 0.6
    S.append(O.Shot("call", t, ln))                                                      # 19:00 意見がまとまらない
    S.append(O.Shot("ff", 3.4))                                                          # 早送り → 21:30
    ln, t = seq(["03", "04", "05", "06"], 0.5, extra={"04": 0.5, "05": 0.9, "06": 0.2})
    s = O.Shot("mute", t + 0.8, ln); s.unmute = ln[3][0] + 0.1; S.append(s)             # ミュート
    ln, t = seq(["07", "08"], 0.9, extra={"08": 1.1})
    s = O.Shot("idea", t + 1.2, ln); s.hit = ln[0][0] + L("07") + 0.05; S.append(s)     # 子どもが、子どもだけで
    S.append(O.Shot("board", 4.6))                                                       # ホワイトボード
    ln, t = seq(["09", "10"], 1.0, extra={"10": 0.4})
    S.append(O.Shot("room", t + 2.2, ln))                                                # 通話のあと、トケイ
    S.append(O.Shot("end", 6.0))
    t = 0
    for s in S:
        s.dur += PAD
        n = int(round(s.dur * FPS)); s.start, s.dur = t, n / FPS; t += s.dur
    return S


def speaking(s, t):
    cur = None
    for (t0, sid) in s.lines:
        if t0 <= t <= t0 + L(sid) + 0.15:
            cur = sid
    if cur == "07" and t - next(a for a, b in s.lines if b == "07") > L("07") * 0.58:
        cur = "07b"
    return cur


SH = plan()
NOSUB = False


def shot(name):
    return next(s for s in SH if s.name == name)


# ---------- ビデオ通話 ----------
PEOPLE = {   # tag: (定義, 名前札, 部屋の壁の色)
    "K": (C.KANATA, "カナタ", (226, 214, 196)),
    "H": (C.HARUTO, "ハルト", (206, 226, 210)),
    "A": (C.TEAM_A, "メンバー", (232, 218, 236)),
    "B": (C.TEAM_B, "メンバー", (210, 224, 240)),
}
_BG = {}


def wall(col):
    if col not in _BG:
        _BG[col] = E.sky(tuple(max(0, c - 18) for c in col), col).convert("RGB").resize((W * G.SS, H * G.SS))
    return _BG[col]


def face(who, t, talk=False, expr=None):
    """通話の1人分（胸から上）。1080×725"""
    spec, _, col = PEOPLE[who]
    r = Rig(spec, (0, 0, -1.0), math.pi, tag=who)
    r.expr = expr or (("smile" if who != "K" else "open") if talk and int(t * 7) % 2 else "normal")
    if expr and talk and int(t * 7) % 2 and expr != "shock":
        r.expr = "open" if who == "K" else "smile"
    r.set(head_yaw=0.06 * math.sin(t * 1.3 + hash(who) % 5), head_pitch=0.03 * math.sin(t * 2.1), armL=0.3, armR=0.3)
    tz = 0.62 + (spec.get("scale", 1.0) - 1.0) * 1.8          # 背の高さに合わせて頭を真ん中に
    cam = Camera((0.1, -3.3, tz + 0.25), (0.04, 0, tz), 40)
    img, _ = render(Q.MIO_SET + r.boxes(), cam, wall(col))
    return img.convert("RGB").crop((0, 600, 1080, 1240))


def mic_off(d, x, y, s=1.0):
    r = int(26 * s)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(220, 50, 60))
    d.rounded_rectangle([x - 7 * s, y - 15 * s, x + 7 * s, y + 6 * s], radius=int(7 * s), fill=(255, 255, 255))
    d.line([x - 16 * s, y + 16 * s, x + 16 * s, y - 16 * s], fill=(255, 255, 255), width=int(5 * s))


def nameplate(d, x, y, name, muted=False, s=1.0):
    f = O.F(BOLD, int(30 * s))
    w = f.getlength(name) + 30 * s + (50 * s if muted else 0)
    d.rounded_rectangle([x, y, x + w, y + 46 * s], radius=10, fill=(0, 0, 0))
    d.text((x + 15 * s, y + 6 * s), name, font=f, fill=(255, 255, 255))
    if muted:
        mic_off(d, x + w - 30 * s, y + 23 * s, 0.75 * s)


def grid(t, talk=(), muted=("K",), expr=None, glitch=0.0):
    """2×2の通話画面（y 640〜1300）"""
    img = Image.new("RGBA", (W, H), (24, 26, 34, 255))
    d = ImageDraw.Draw(img)
    tw, th = 510, 302
    for j, who in enumerate(("K", "H", "A", "B")):
        x, y = 20 + (j % 2) * 530, 770 + (j // 2) * 322
        tile = face(who, t + j * 0.7, who in talk, (expr or {}).get(who)).resize((tw, th))
        img.paste(tile, (x, y))
        d.rounded_rectangle([x, y, x + tw, y + th], radius=6, outline=GRN if who in talk else (60, 64, 80), width=7)
        nameplate(d, x + 12, y + th - 58, PEOPLE[who][1], who in muted)
    return img


def speaker(t, who, talk=False, muted=False, expr=None):
    """話している人を大きく（y 620〜1320）"""
    img = Image.new("RGBA", (W, H), (24, 26, 34, 255))
    d = ImageDraw.Draw(img)
    tile = face(who, t, talk, expr).resize((1040, 616))
    img.paste(tile, (20, 770))
    d.rounded_rectangle([20, 770, 1060, 1386], radius=6, outline=GRN if talk and not muted else (60, 64, 80), width=8)
    nameplate(d, 40, 1310, PEOPLE[who][1], muted, 1.3)
    return img


def clock(img, time_):
    O.clock_big(img, DATE, time_, grade="大学1年")
    O.counter(img, 1)


def card(img, u):
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    y0 = 760
    d.rounded_rectangle([50, y0, W - 50, y0 + 400], radius=40, fill=(10, 12, 30, int(240 * e)), outline=(255, 216, 77, int(255 * e)), width=8)
    a = int(255 * e)
    for j, (ln, sz, col) in enumerate([("未来自治体", 92, (255, 216, 77, a)), ("30年後の自治体の政策を", 58, (255, 255, 255, a)),
                                       ("考えるコンテスト", 58, (255, 255, 255, a))]):
        f = O.F(BLACK, sz)
        d.text((540 - f.getlength(ln) / 2, y0 + 50 + [0, 140, 230][j]), ln, font=f, fill=col)
    img.alpha_composite(lay)


def hook(img, t):
    if t < 2.4:
        im = E.fit_text(["一番いいこと言ったのに、", "ミュート。"], 96, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={1: RED})
        E.paste_center(img, im, 540, 1520, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["ガクチカ・ループ 第13話", "30年後の広島"], 96, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1520, E.pop(t - 2.4))


BUBBLES = [("交通！", 200, 700), ("子育てだって", 760, 760), ("予算は？", 300, 1010), ("でも…", 820, 1060), ("バスが…", 520, 880), ("公園は？", 240, 1230)]


# ---------- 1コマ ----------
def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "cold":
        img = speaker(t, "K", talk=True, muted=True, expr="resolve")
        clock(img, "21:31")
        hook(img, t)
    elif n == "call":
        talk = {TEXT[x][0] for (a, x) in s.lines if a <= t <= a + L(x) + 0.1}
        img = grid(t, talk, expr={"A": "normal", "B": "normal"})
        clock(img, "19:00")
        if t < s.lines[0][0] - 0.1:
            card(img, (t - 0.2) / 0.3)
        else:
            S9.bigbadge(img, "未来自治体の準備", (40, 120, 200))
    elif n == "ff":
        u = t / s.dur
        talk = {("A", "B", "H", "K")[int(t * 4) % 4]}
        img = O.glitch(grid(t, talk), 0.15, int(t * 30))
        hh, mm = divmod(int(19 * 60 + 150 * u), 60)
        clock(img, f"{hh}:{mm:02d}")
        for j, (w, x, y) in enumerate(BUBBLES):
            if t > 0.3 + j * 0.45:
                E.paste_center(img, E.fit_text([w], 60, 600, fill=(255, 255, 255), stroke=(8, 10, 24), sw=8), x, y, E.pop(t - 0.3 - j * 0.45))
        O.caption(img, "▶▶ 早送り", 1520, 1.0, size=90, col=(255, 255, 255))
    elif n == "mute":
        a, b, c, d_ = (x[0] for x in s.lines)
        last = None
        for (t0, i) in s.lines:
            if t >= t0 - 0.1:
                last = i
        if last == "03" or last is None:
            img = speaker(t, "H", talk=sid == "03")
        elif last == "04":                                   # 真剣に話すカナタ。でも、ミュート
            img = speaker(t, "K", talk=sid == "04", muted=True, expr="resolve")
        else:                                                # 4人：「ミュートになってる」→「えっ」→ くすっ
            smile = t > d_ + 0.3
            img = grid(t, {"H"} if sid == "05" else ({"K"} if sid == "06" else set()),
                       muted=("K",) if t < s.unmute else (),
                       expr={"K": "shock" if t < d_ + L("06") + 0.3 else "smile", "A": "smile" if smile else "normal",
                             "B": "smile" if smile else "normal", "H": "smile" if smile else "normal"})
        clock(img, "21:31")
    elif n == "idea":
        a, b = (x[0] for x in s.lines)
        if t < b - 0.1:                                      # カナタの顔（間 → 一言）
            img = speaker(t, "K", talk=sid in ("07", "07b"), expr="resolve")
        else:
            img = speaker(t, "H", talk=sid == "08", expr="smile")
        clock(img, "21:32")
    elif n == "board":
        img = Image.new("RGBA", (W, H), (24, 26, 34, 255))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([40, 640, 1040, 1380], radius=20, fill=(250, 250, 248))
        d.text((70, 660), "画面共有：ホワイトボード", font=O.F(BOLD, 32), fill=(120, 124, 140))
        E.paste_center(img, E.fit_text(["テーマ：子どもの遊び場"], 76, 920, fill=(30, 40, 70), stroke=(250, 250, 248), sw=2), 540, 790, E.pop(t))
        notes = [("交通", (255, 226, 120), 230, 960), ("子育て", (160, 220, 255), 540, 980), ("公園", (180, 240, 180), 850, 960),
                 ("バス・歩道", (255, 190, 200), 330, 1180), ("30年後は？", (230, 210, 255), 750, 1190)]
        for j, (w, col, x, y) in enumerate(notes):
            tt = t - 0.6 - j * 0.45
            if tt > 0:
                im = Image.new("RGBA", (250, 150), col + (255,))
                ImageDraw.Draw(im).text((125 - O.F(BLACK, 46).getlength(w) / 2, 46), w, font=O.F(BLACK, 46), fill=(40, 40, 50))
                E.paste_center(img, im.rotate((j % 3 - 1) * 4, expand=True), x, y, E.pop(tt))
        hh, mm = divmod(int(21 * 60 + 40 + 20 * t / s.dur), 60)
        clock(img, f"{hh}:{mm:02d}")
    elif n == "room":
        a, b = (x[0] for x in s.lines)
        k = Q.kanata_bed("normal" if t < b - 0.1 else "smile")
        k.set(head_pitch=0.15)
        tk = Q.tokei_near(t, "eyes", drop_t=t - 0.3)
        img = Q.room_img(k, Q.face_cam(t, s.dur, 0.35), list(tk), glow=0.5)
        img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 50, 90)))
        clock(img, "22:05")
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "あなたなら、", 600, t, size=84)
        O.caption(img, "どんな政策を出す？", 730, t, size=100, col=YEL)
        for txt, y, sz, col, path in ((["コメントで教えてね"], 900, 56, (255, 255, 255), BLACK),
                                      (["次回 第14話「目標、書き直していいですか」"], 1030, 48, (255, 255, 255), BLACK),
                                      (["ドットジェイピー広島第一支部", "春インターン申込は12月31日まで"], 1180, 48, YEL, BLACK),
                                      (["この動画は「勇気を出して一歩を踏み出そう」という", "メッセージを伝えるための創作ドラマです"], 1340, 32, (220, 226, 245), BOLD)):
            E.paste_center(img, E.fit_text(txt, sz, 1000, fill=col, sw=6, path=path), 540, y, E.pop(t - 0.3))
    if sid and not NOSUB:
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
