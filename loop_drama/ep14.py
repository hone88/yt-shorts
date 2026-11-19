"""ガクチカ・ループ 第14話「目標、書き直していいですか」（見直し後のリメイク版台本・11/19 ゆうきさんOK）
2/27（土）ハーフタイム（キックオフと同じ会場）。3周目のキックオフで書いた目標シート（第6話と同じ文：人前で〜／面接で答える。）を見る。
「（…前のループでも、同じことを書いた。）」「（…でも今、書きたいのは、これじゃない。）」（第17話を先取りしないよう「答え」と言わない）
「……目標、書き直していいですか。」ミオ「もちろん。目標は、変わっていいんだよ。」→「面接で答える。」だけ線を引き「広島のことを、本気で考えたい」（はみ出す）
ハルト「…はみ出してる。でも、いい目標じゃん。」「…ハルトの真似。ちゃんと『やりたい』を書いてみた。」「3日の公開討論会、カナタも行くんだろ？」
帰り道 トケイ「前のループより、早くハルトと出会えたのだ。」…「ループしても、目標は、書き直せるんだな。」
場面ごとに0.2秒の余韻、転換音・環境音6割、効果音7割。カメラは話し手が変わるときだけ切り替え（注意点8）。"""
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
import ep6 as S6
import ep9 as S9
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep14"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED = (255, 216, 77), (255, 90, 90)
O.SPEAK["H"] = ("ハルト", (110, 200, 130))
PAD = 0.2
DATE = "2027年2月27日（土）"
TX, TY = S6.TABLES[4]
KP, HP = (TX - 0.45, TY - 0.8, 0), (TX + 0.45, TY - 0.95, 0)
NEW = "広島のことを、本気で考えたい"

VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep14/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("M", "キックオフで書いた目標、|もう一度[見てみよう]。"),
    "02": ("K", "（…前のループでも、|[同じこと]を書いた。）"),
    "03": ("K", "（…でも今、書きたいのは、|[これじゃない]。）"),
    "04": ("K", "……目標、|[書き直して]いいですか。"),
    "05": ("M", "もちろん。|目標は、[変わっていい]んだよ。"),
    "06": ("H", "…はみ出してる。|でも、[いい目標]じゃん。"),
    "07": ("K", "…ハルトの真似。|ちゃんと『[やりたい]』を|書いてみた。"),
    "08": ("H", "3日の[公開討論会]、|カナタも行くんだろ？"),
    "09": ("K", "…うん。"),
    "10": ("T", "前のループより、|[早く]ハルトと出会えたのだ。"),
    "11": ("K", "…うん。だから、|今日の目標も、書けた。"),
    "12": ("T", "目標を書き直したのは、|[初めて]なのだ。"),
    "13": ("K", "…ループしても、目標は、|[書き直せる]んだな。"),
}


def subtitle(img, sid):
    who, text = TEXT[sid]
    name, col = O.SPEAK[who]
    lines = text.split("|")
    d = ImageDraw.Draw(img)
    f, fn = O.F(BLACK, 72), O.F(BLACK, 40)
    y = 1450 - (len(lines) - 1) * 70
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
    S.append(O.Shot("cold", 5.0, []))                                                    # 線を引く瞬間 → 2.4秒でタイトル
    ln, t = seq(["01"], 1.2)
    s = O.Shot("open", t + 2.4, ln); s.sheet = t + 0.1; S.append(s)                       # ハーフタイム → キックオフの目標シート
    ln, t = seq(["02", "03"], 1.8, extra={"03": 1.1})
    S.append(O.Shot("stare", t + 0.8, ln))                                               # 見つめる（第6話の帰り道が重なる）
    ln, t = seq(["04", "05"], 1.2, extra={"05": 0.3})
    s = O.Shot("ask", t + 0.8, ln); s.hand = 0.6; S.append(s)                             # 書き直していいですか
    S.append(O.Shot("write", 6.4))                                                       # 線を引いて、新しく書く（はみ出す）
    ln, t = seq(["06", "07", "08", "09"], 0.6, extra={"07": 0.2, "08": 0.8})
    S.append(O.Shot("haruto", t + 0.8, ln))                                              # ハルトと2ショット
    ln, t = seq(["10", "11", "12", "13"], 1.4, extra={"12": 0.5, "13": 0.3})
    S.append(O.Shot("home", t + 2.2, ln))                                                # 帰り道（トケイ）
    S.append(O.Shot("end", 6.0))
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


# ---------- 絵 ----------
def clock(img, time_):
    O.clock_big(img, DATE, time_, grade="大学1年")
    O.counter(img, 1)


def hall(t, kexpr="normal", hand=0.0, hexpr="normal", peek=0.0, mio_talk=False, cam=None, write=False, stand=False):
    k = S6.kanata(KP, 0.0, kexpr, sit=True, armL=0.6, armR=(0.6 + 0.15 * math.sin(t * 9) * write) * (1 - hand) + (-2.95) * hand,
                  armR_out=-0.25 * hand, head_pitch=0.25 if write else 0.0)
    h = S6.haruto(HP, lerp(0.0, 0.55, peek), hexpr, lean=0.3 * peek, sit=not stand, armL=0.05 if stand else 0.5, armR=0.05 if stand else 0.5)
    m = S6.mio_front("smile" if not mio_talk or int(t * 7) % 2 else "normal", armL=0.05, armR=0.4 + (0.2 * math.sin(t * 6) if mio_talk else 0))
    img, _ = render(S6.HALL + S6.crowd(t, tables=S6.BACK) + k.boxes() + h.boxes() + m.boxes(), cam, S6.BG_HALL)
    return img.convert("RGBA")


def cam_mio(t, dur):
    """カナタの背中越しに、前のミオ"""
    u = ease(t / max(dur, 0.01))
    return Camera((lerp(TX - 1.25, TX - 1.2, u), lerp(TY - 3.9, TY - 3.6, u), 2.45), (4.9, 10.2, 1.45), 40)


def cam_kface(t, dur, push=0.3):
    """テーブルの向こうから、カナタの顔"""
    u = ease(t / max(dur, 0.01))
    return Camera((lerp(KP[0] + 0.25, KP[0] + 0.2, u), lerp(TY + 1.9, TY + 1.9 - push, u), 1.62), (KP[0], KP[1], 1.45), 44)


def cam_two(t, dur):
    u = ease(t / max(dur, 0.01))
    return Camera((lerp(4.85, 4.9, u), lerp(9.9, 9.5, u), 2.2), (TX, TY - 0.85, 1.5), 44)


def sheet(img, u, strike=0.0, write=0.0, y0=700):
    """3周目のキックオフで書いた目標シート（第6話と同じ文）。strike：「面接で答える。」に線、write：新しい目標を書く（0→1）"""
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a = int(255 * e)
    y0 = y0 + (1 - e) * 40
    fs = 54
    rows = S6.GOAL_K + [""]
    h = 150 + int(fs * 1.35) * len(rows) + 30
    d.rounded_rectangle([90, y0, W - 90, y0 + h], radius=26, fill=(252, 250, 242, int(248 * e)), outline=(60, 64, 80, a), width=6)
    d.rounded_rectangle([90, y0, W - 90, y0 + 84], radius=26, fill=(255, 138, 31, a))
    fh, fl = O.F(BLACK, 40), O.F(BLACK, fs)
    title = "1月30日 キックオフ　目標シート　宇野カナタ"
    d.text((540 - fh.getlength(title) / 2, y0 + 20), title, font=fh, fill=(255, 255, 255, a))
    for j, ln in enumerate(S6.GOAL_K):
        y = y0 + 112 + j * int(fs * 1.35)
        d.text((140, y), ln, font=fl, fill=(40, 40, 50, a))
        if ln.startswith("面接") and strike > 0:
            x1 = 140 + fl.getlength(ln) * ease(min(1, strike))
            d.line([130, y + fs * 0.6, x1, y + fs * 0.6], fill=(220, 40, 50, a), width=10)
    img.alpha_composite(lay)
    if write > 0:   # 新しい目標（大きく書きすぎて「たい」が枠からはみ出す）
        n = int(len(NEW) * min(1, write))
        f2 = O.F(BLACK, 64)   # 枠（右端990）から少しはみ出し、画面（1080）には収まる大きさ
        dd = ImageDraw.Draw(img)
        dd.text((132, y0 + 112 + 3 * int(fs * 1.35) + 4), NEW[:n], font=f2, fill=(30, 70, 180, a))


def hook(img, t):
    if t < 2.4:
        im = E.fit_text(["その目標、", "もう違う。"], 120, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={1: YEL})
        E.paste_center(img, im, 540, 1450, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["ガクチカ・ループ 第14話", "目標、書き直していいですか"], 84, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1450, E.pop(t - 2.4))


def old_street(t):
    """前のループ（第6話）の帰り道。色を抜いて重ねる"""
    k = R.kanata_stand("blank")
    k.set(head_pitch=0.18)
    cam = Camera((3.0, 0.0, 1.7), (2.7, 4.6, 1.5), 50)
    img, _ = render(R.OUTSIDE + k.boxes(), cam, S6.BG_EVE)
    img = img.convert("RGBA")
    g = img.convert("L").convert("RGBA")
    img = Image.blend(img, g, 0.75)
    O.caption(img, "前のループ　1月30日", 1600, 1.0, size=56, col=(220, 224, 236))
    return img


# ---------- 1コマ ----------
def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "cold":
        img = hall(t, "resolve", cam=cam_two(t, s.dur), write=True)
        sheet(img, 1.0, strike=(t - 0.2) / 0.5, y0=760)
        clock(img, "13:20")
        hook(img, t)
    elif n == "open":
        a = s.lines[0][0]
        if t < s.sheet - 0.1:                          # 前のミオ（カナタの背中越し）
            img = hall(t, "normal", mio_talk=sid == "01", cam=cam_mio(t, s.dur))
            S9.bigbadge(img, "ハーフタイム：中間の振り返り", (64, 110, 220))
        else:                                          # 手元の目標シート
            img = hall(t, "normal", cam=cam_two(t, s.dur))
            img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 70)))
            sheet(img, (t - s.sheet) / 0.3, y0=760)
        clock(img, "13:00")
    elif n == "stare":
        a, b = (x[0] for x in s.lines)
        if 0.5 < t < 1.5:                              # 第6話の帰り道が一瞬重なる
            img = old_street(t) if 0.62 < t < 1.38 else O.glitch(old_street(t), 0.25, int(t * 30))
        else:
            img = hall(t, "blank" if t < b - 0.2 else "resolve", cam=cam_kface(t, s.dur, 0.45))
            img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 40, 40)))
        clock(img, "13:05")
    elif n == "ask":
        a, b = (x[0] for x in s.lines)
        hand = ease(min(1, max(0, t - s.hand) / 0.25)) * (1 - ease(min(1, max(0, t - b - L("05") + 0.2) / 0.4)))
        if t < b - 0.1:                                # 手を挙げる（背中越しに前のミオ）
            img = hall(t, "resolve", hand=hand, cam=cam_mio(t, s.dur))
        else:                                          # ミオ「もちろん」
            u = ease((t - b) / max(0.1, s.dur - b))
            img = hall(t, "resolve", hand=hand, mio_talk=sid == "05",
                       cam=Camera((lerp(4.9, 4.9, u), lerp(7.0, 7.3, u), 1.9), (5.0, 10.2, 1.72), 44))
        clock(img, "13:06")
    elif n == "write":
        img = hall(t, "resolve", cam=cam_two(t, s.dur), write=True)
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 70)))
        sheet(img, 1.0, strike=(t - 0.3) / 0.6, write=(t - 1.3) / 2.6, y0=760)
        clock(img, "13:08")
    elif n == "haruto":
        a, b, c, d_ = (x[0] for x in s.lines)
        peek = ease(min(1, t / 0.6)) * (1 - ease(min(1, max(0, t - c + 0.3) / 0.6)))
        img = hall(t, "smile" if t > b - 0.1 else "normal", hexpr="smile", peek=peek, cam=cam_two(t, s.dur), stand=True)
        clock(img, "13:10" if t < c - 0.3 else "16:30")
        if c - 0.3 <= t:
            S9.bigbadge(img, "ハーフタイム 終了", (110, 110, 130))
    elif n == "home":
        a = s.lines[0][0]
        k = R.kanata_stand("normal" if t < s.lines[3][0] else "smile")
        k.set(head_pitch=-0.05)
        hx = lerp(3.4, 5.0, ease(min(1, t / 2.5)))
        hr = S6.haruto((hx, 7.6, 0), math.pi, "smile", armR=2.6 + 0.3 * math.sin(t * 8) if t < 1.2 else 0.05, armL=0.05)
        u = ease(t / s.dur)
        cam = Camera((lerp(3.1, 2.95, u), lerp(-0.6, 0.3, u), 1.7), (2.7, 4.6, 1.5), 50)
        tk = Q.tokei_near(t, "eyes", t - a + 0.6, (3.25, 3.3, 1.75)) if t > a - 0.6 else []
        img, _ = render(R.OUTSIDE + k.boxes() + hr.boxes() + list(tk), cam, S6.BG_EVE)
        img = img.convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 130, 60, 30)))
        clock(img, "17:30")
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "今の目標、", 600, t, size=84)
        O.caption(img, "書き直すなら？", 730, t, size=104, col=YEL)
        for txt, y, sz, col, path in ((["コメントで教えてね"], 900, 56, (255, 255, 255), BLACK),
                                      (["次回 第15話「地方大会」"], 1030, 52, (255, 255, 255), BLACK),
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
