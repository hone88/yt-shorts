"""ガクチカ・ループ 第16話「聞きに行く」（見直し後のリメイク版台本・11/21 ゆうきさんOK）
3/13（土）9:00 事務所「…地方大会、負けました。」→「負けた政策ですけど、聞きに行きたいんです。」→ 森下議員「…よし、一緒に行こう。」
「前に、君が通学の費用を『きつい』って言ってくれただろう。…聞かなきゃ、分からないことばかりなんだよ。」（第11話の回収）
10:30 公園：お母さん「道が危ないけぇ」／子ども「放課後、行くとこないもん」／11:30 おじいさん「見守る大人が、減ったけぇね」→ メモ3つ
「…ぼくたち、子どもにしか聞いてなかった。」→ 夕方 森下議員「それが、現場だよ。」→ ひとりで「……ここに、あった。」（「答え」は言わない）
トケイ「聞きに行ったから、見つかったのだ。」→ ハルトから「NPOの人たちにも、聞いてみた。話そう。」
学生が1人で地域を回らない（森下議員に同行）。ハルト（NPO）は同行しない。最後の画面と投稿文にチームの※。
場面ごとに0.2秒の余韻、転換音・環境音6割、効果音7割。カメラは話し手が変わるときだけ切り替え。"""
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
import case1 as K1
import ep9 as S9
import ep11 as S11
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep16"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED = (255, 216, 77), (255, 90, 90)
O.SPEAK["Mo"] = ("森下議員", (170, 172, 182))
O.SPEAK["L"] = ("地域の方", (230, 160, 120))
O.SPEAK["KD"] = ("子ども", (255, 170, 190))
O.SPEAK["G"] = ("地域の方", (190, 170, 140))
PAD = 0.2
DATE = "2027年3月13日（土）"
MEMO = [("道が危ない", (40, 40, 50)), ("放課後に行ける場所がない", (40, 40, 50)), ("見守る大人がいない", (40, 40, 50))]

VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep16/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("K", "…地方大会、[負けました]。"),
    "02": ("Mo", "うん。聞いたよ。"),
    "03": ("K", "審査員の人に、|『[地域の人]には聞きましたか』|って言われて。|…何も、言えなくて。"),
    "04": ("K", "…負けた政策ですけど、|[聞きに行きたい]んです。"),
    "05": ("Mo", "…[よし]、一緒に行こう。"),
    "06": ("Mo", "前に、君が通学の費用を|『きつい』って言ってくれただろう。|…[聞かなきゃ]、|分からないことばかりなんだよ。"),
    "07": ("K", "あの…子どもだけで、|遊び場まで行ける街って、|[どう思いますか]？"),
    "08": ("L", "そうなったら、ええけどねぇ。|…でも[道が危ない]けぇ、|子どもだけでは行かせられんのよ。"),
    "09": ("KD", "放課後、[行くとこ]ないもん。"),
    "10": ("G", "昔は、近所の大人が|みんな[見とった]んよ。|今は、[見守る大人]が、|減ったけぇね。"),
    "11": ("K", "…ぼくたち、|子どもにしか[聞いてなかった]。"),
    "12": ("Mo", "どうだった？"),
    "13": ("K", "…道のこととか、|見守る人のこととか。|[地図の上]じゃ、|分からなかったです。"),
    "14": ("Mo", "それが、[現場]だよ。"),
    "15": ("K", "……[ここに]、あった。"),
    "16": ("T", "[聞きに行った]から、|見つかったのだ。"),
    "17": ("K", "…うん。"),
}


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


def plan():
    S = []
    S.append(O.Shot("cold", 5.0, []))                                                    # メモが増えていく → 2.4秒でタイトル
    ln, t = seq(["01", "02", "03", "04", "05", "06"], 1.4, extra={"02": 0.4, "03": 0.4, "04": 1.0, "05": 0.6, "06": 0.5})
    s = O.Shot("office", t + 1.0, ln); s.yosh = ln[4][0]; S.append(s)                   # 9:00 事務所
    ln, t = seq(["07", "08", "09"], 1.2, extra={"08": 0.4, "09": 0.5})
    s = O.Shot("park", t + 2.0, ln); s.m1 = ln[1][0] + L("08") + 0.2; s.m2 = ln[2][0] + L("09") + 0.2; S.append(s)   # 10:30 公園
    ln, t = seq(["10", "11"], 1.0, extra={"11": 1.4})
    s = O.Shot("elder", t + 1.2, ln); s.m3 = ln[0][0] + L("10") + 0.2; S.append(s)     # 11:30 おじいさん
    ln, t = seq(["12", "13", "14"], 1.0, extra={"13": 1.0, "14": 0.4})
    S.append(O.Shot("walk", t + 1.4, ln))                                                # 16:30 帰り道
    ln, t = seq(["15", "16"], 2.0, extra={"16": 0.8})
    ln2, t = seq(["17"], t + 1.6)
    s = O.Shot("alone", t + 2.4, ln + ln2); s.msg = ln2[0][0] - 1.4; S.append(s)        # 17:30 ひとりで
    S.append(O.Shot("end", 6.5))
    t = 0
    for s in S:
        s.dur += PAD
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


def last_line(s, t):
    last = None
    for (t0, i) in s.lines:
        if t >= t0 - 0.1:
            last = i
    return last


# ---------- セット：小さな公園（名前・看板の文字なし） ----------
def park_set():
    S = []
    S += P.blocks(-3, 9, -4, 10, -1, 0, hexc("#86b85e"), 0.06, 161)          # 芝生
    S += P.blocks(-3, 9, -1, 1, -1, 0, hexc("#c9bca6"), 0.04, 162)           # 歩道
    S += P.blocks(-3, 9, -4, -1, -1, 0, hexc("#5a5e66"), 0.03, 163)          # 車道
    S.append(P.slab(5.0, 6.0, 0, 0.15, 0.15, 2.0, hexc("#c8402a")))          # すべり台
    S.append(P.slab(6.2, 6.0, 0, 0.15, 0.15, 2.0, hexc("#c8402a")))
    S.append(P.slab(5.0, 6.0, 1.9, 1.35, 0.9, 0.12, hexc("#f0c040")))
    S.append(P.slab(5.3, 3.6, 0.2, 0.7, 2.5, 0.12, hexc("#f0c040")))
    for x in (1.0, 2.6):                                                       # ぶらんこ
        S.append(P.slab(x, 7.4, 0, 0.12, 0.12, 2.2, hexc("#4a6aa8")))
    S.append(P.slab(1.0, 7.4, 2.2, 1.72, 0.12, 0.12, hexc("#4a6aa8")))
    S.append(P.slab(1.5, 7.3, 0.45, 0.6, 0.3, 0.06, hexc("#3a3a42")))
    S.append(P.slab(-1.6, 3.3, 0.38, 2.0, 0.6, 0.08, hexc("#a8744a")))      # ベンチ
    S.append(P.slab(-1.6, 3.85, 0.46, 2.0, 0.08, 0.6, hexc("#a8744a")))
    for x in (-1.5, 0.2):
        S.append(P.slab(x, 3.35, 0, 0.1, 0.5, 0.38, hexc("#3a3a42")))
    for (x, y) in ((-2.4, 7.0), (7.4, 8.0), (7.6, 2.4)):                       # 木
        S.append(P.slab(x + 0.35, y + 0.35, 0, 0.3, 0.3, 1.6, hexc("#6a4a30")))
        S.append(P.slab(x, y, 1.6, 1.0, 1.0, 1.0, hexc("#4a9a4a")))
    return S


PARK = park_set()
BG_SKY = E.sky((120, 180, 240), (220, 236, 250)).convert("RGB").resize((W * G.SS, H * G.SS))
BG_EVE = E.sky((236, 140, 90), (250, 208, 160)).convert("RGB").resize((W * G.SS, H * G.SS))


def clock(img, time_):
    O.clock_big(img, DATE, time_, grade="大学1年")
    O.counter(img, 1)


def person(spec, pos, yaw, tag, expr="normal", **pose):
    r = Rig(spec, pos, yaw, tag=tag)
    r.set(armL=0.05, armR=0.05)
    r.set(**pose)
    r.expr = expr
    return r


def memo(img, n, y0=640, u=1.0):
    if n <= 0:
        return
    S11.memo(img, u, MEMO[:n], y0=y0)


def hook(img, t):
    if t < 2.4:
        im = E.fit_text(["負けたあとで、", "聞きに行った。"], 112, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={1: YEL})
        E.paste_center(img, im, 540, 1500, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["ガクチカ・ループ 第16話", "聞きに行く"], 96, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1500, E.pop(t - 2.4))


# ---------- 1コマ ----------
def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    last = last_line(s, t)
    if n == "cold":
        k = K1.kanata((2.4, 2.0, 0), -0.65, "resolve", armR=1.1, head_pitch=0.25)
        img, _ = render(PARK + k.boxes(), Camera((3.6, 4.6, 1.85), (2.4, 2.0, 1.45), 46), BG_SKY)
        img = img.convert("RGBA")
        memo(img, min(3, 1 + int(t / 0.6)), y0=1020)
        clock(img, "11:40")
        hook(img, t)
    elif n == "office":
        mo = F.morishita_seat()
        mo.pos = (3.0, 5.5, 0)
        if sid in ("02", "05", "06"):
            mo.set(head_pitch=0.04 * math.sin(t * 6))
        mo.expr = "normal"
        k = R.kanata_seat("blank" if t < s.yosh else "resolve")
        k.spec = C.KANATA_SUIT
        k.set(head_pitch=0.3 if t < s.lines[3][0] else 0.05)
        if last in ("02", "05", "06"):
            cam = R.cam_mio(t, s.dur)
        else:
            cam = R.cam_kanata(t, s.dur)
        img, _ = render(R.MEET + mo.boxes() + k.boxes(), cam, R.BG_MEET)
        img = img.convert("RGBA")
        clock(img, "9:00")
        S9.bigbadge(img, "事務所で活動中", (200, 120, 40))
    elif n in ("park", "elder"):
        u = ease(t / s.dur)
        k = K1.kanata((2.2, 1.6, 0), -0.65, "open" if sid in ("07",) else "normal", armR=1.1 if n == "elder" or t > s.m1 - 0.5 else 0.05,
                      head_pitch=0.2 if (n == "park" and (s.m1 - 0.3 < t < s.m1 + 0.8 or s.m2 - 0.3 < t < s.m2 + 0.8)) else 0.0)
        mo = K1.morishita((1.35, 1.0, 0), -0.75, "normal")
        if n == "park":
            mom = person(C.RECEPTION, (3.4, 3.1, 0), math.pi - 0.67, "mom", "smile" if sid == "08" and int(t * 7) % 2 else "normal")
            kid = person(C.KID, (4.05, 2.75, 0), math.pi - 0.9, "kid", "smile" if sid == "09" else "normal", armL=0.3, armR=0.3)
            others = mom.boxes() + kid.boxes()
            if last == "07":
                cam = Camera((lerp(1.85, 1.8, u), lerp(4.7, 4.5, u), 1.9), (2.2, 1.6, 1.6), 42)     # お母さんの肩越しにカナタ
            elif last in ("08", "09"):
                cam = Camera((lerp(0.3, 0.45, u), lerp(2.8, 2.75, u), 2.0), (3.6, 3.0, 1.75), 44)    # カナタの肩越しに親子
            else:
                cam = Camera((lerp(5.9, 5.8, u), lerp(-0.2, 0.0, u), 1.95), (2.7, 2.2, 1.25), 46)     # 横から：みんな
            tm = "10:30"
            nmemo = (1 if t > s.m1 else 0) + (1 if t > s.m2 else 0)
        else:
            gp = person(C.LOCAL, (3.4, 3.1, 0), math.pi - 0.67, "gp", "smile" if sid == "10" and int(t * 7) % 2 else "normal")
            others = gp.boxes()
            if last == "11":
                cam = Camera((lerp(1.85, 1.8, u), lerp(4.7, 4.5, u), 1.9), (2.2, 1.6, 1.6), 42)
            else:
                cam = Camera((lerp(0.3, 0.45, u), lerp(2.8, 2.75, u), 2.0), (3.4, 3.1, 1.85), 44)
            tm = "11:30"
            nmemo = 2 + (1 if t > s.m3 else 0)
        img, _ = render(PARK + k.boxes() + mo.boxes() + others, cam, BG_SKY)
        img = img.convert("RGBA")
        clock(img, tm)
        S9.bigbadge(img, "地域の声を聞きに", (40, 150, 90))
        show = (n == "park" and t > s.m1 and t < s.m1 + 1.6) or (n == "park" and s.m2 < t < s.m2 + 1.8) or (n == "elder" and s.m3 < t < s.m3 + 1.8)
        if show:
            tt = t - (s.m3 if n == "elder" else (s.m2 if t > s.m2 else s.m1))
            memo(img, nmemo, y0=760, u=min(1, tt / 0.3) if nmemo == 1 else 1.0)
    elif n == "walk":
        u = ease(t / s.dur)
        x = lerp(-1.0, 1.6, u)
        k = S9.walk(K1.kanata((x, 1.0, 0), -math.pi / 2, "normal" if last != "13" else "resolve",
                              head_yaw=-0.4 if last in ("12", "14") else 0.0), t, 0.6)
        mo = S9.walk(K1.morishita((x + 0.9, 1.0, 0), -math.pi / 2, "normal", head_yaw=0.4 if last in ("12", "14") else 0.0), t, 0.6)
        cam = Camera((x + 0.6, -3.4, 2.0), (x + 0.5, 1.0, 1.55), 44)
        img, _ = render(K1.STREET + k.boxes() + mo.boxes(), cam, BG_EVE)
        img = img.convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 140, 70, 30)))
        clock(img, "16:30")
    elif n == "alone":
        u = ease(t / s.dur)
        a, b, c = (x[0] for x in s.lines)
        k = Rig(C.KANATA_SUIT, (-0.6, 3.55, 0), math.pi, tag="kanata")
        k.set(sit=True, armL=0.6, armR=1.0, head_pitch=0.35 if t < a + L("15") + 0.4 else (0.1 if t < s.msg else 0.25))
        k.expr = "resolve" if t < c else "smile"
        tk = C.tokei_boxes((0.35, 3.25, 1.4 + (1 - ease(min(1, max(0, t - b + 0.8) / 0.5))) * 1.2), t, "eyes", 0.45, math.pi + 0.3) if t > b - 0.8 else []
        cam = Camera((lerp(-0.2, -0.15, u), lerp(0.0, 0.35, u), 1.6), (-0.3, 3.55, 1.15), 44)
        img, _ = render(PARK + k.boxes() + list(tk), cam, BG_EVE)
        img = img.convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 130, 60, 32)))
        clock(img, "17:30")
        if t < a - 0.1:
            memo(img, 3, y0=1040, u=min(1, t / 0.3))
        if t > s.msg:
            F.msg_card(img, (t - s.msg) / 0.3, "ハルト", ["NPOの人たちにも、聞いてみた。", "話そう。"], y0=1050)
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "あなたが、話を", 600, t, size=84)
        O.caption(img, "聞きに行きたい人は？", 730, t, size=96, col=YEL)
        for txt, y, sz, col, path in ((["コメントで教えてね"], 900, 56, (255, 255, 255), BLACK),
                                      (["次回 第17話「最終報告会」"], 1030, 52, (255, 255, 255), BLACK),
                                      (["ドットジェイピー広島第一支部", "春インターン申込は12月31日まで"], 1180, 48, YEL, BLACK),
                                      (["この動画は「勇気を出して一歩を踏み出そう」という", "メッセージを伝えるための創作ドラマです"], 1340, 32, (220, 226, 245), BOLD),
                                      (["※実際の未来自治体では、NPOインターンと議員インターンの参加者が", "同じチームになることはありません。",
                                        "同じ活動先ごとのチーム（例：森下議員事務所チーム）で出場します"], 1460, 28, (220, 226, 245), BOLD)):
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
