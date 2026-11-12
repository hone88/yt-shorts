"""ガクチカ・ループ 第10話「今度は、こっちから」（リメイク版台本・11/12 ゆうきさんOK）
12/8 大学の中庭。今度はカナタから、ハルトをインターンに誘う。「……なんで知ってんの？」→「顔に書いてある、みたいな…？」
ハルト「説明会、一緒に出てくれる？」。1次選考会で自分から希望を話し、2次選考会 → 活動先決定。
帰り道「今度は、答えのためじゃなくて…気になるほうで、選んだ。」
場面ごとに0.2秒の余韻、転換音・環境音は6割。python3 ep10.py still <shot> <t> | plan | build"""
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
import ep6 as S6
import ep9 as S9
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep10"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED = (255, 216, 77), (255, 90, 90)
O.SPEAK["H"] = ("ハルト", (110, 200, 130))
PAD = 0.2

VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep10/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("H", "……なんで|[知ってんの]？"),
    "02": ("K", "（…今度は、[ぼくから]。）"),
    "03": ("T", "[声]、かけるのだ。"),
    "04": ("K", "あの…春休み、|[インターン]とか……|興味ない？"),
    "05": ("H", "…なんで、[俺]？"),
    "06": ("K", "子どもの[居場所]とか、|興味ありそうだから。"),
    "07": ("K", "えっ、あ…|[顔に、書いてある]、|みたいな…？"),
    "08": ("H", "[なにそれ]。"),
    "09": ("H", "…でも、ちょっと気になる。|一人だと迷うし、|[説明会]、一緒に出てくれる？"),
    "10": ("K", "…うん。オンラインだから、|[家から]でいいよ。"),
    "11": ("M", "最近、[気になってること]|ある？"),
    "12": ("K", "大学の[学費]とか、|若い人の生活のこと。|そういうことに取り組んでる"),
    "12b": ("K", "[議員さん]のところで、|やってみたいです。"),
    "13": ("M", "…[はっきり]してるね。"),
    "14": ("T", "前と、[同じ議員さん]なのだ。"),
    "15": ("K", "うん。でも今度は、|答えのためじゃなくて…|[気になるほう]で、選んだ。"),
    "16": ("T", "…[いい顔]なのだ。"),
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


def seq(ids, start=0.4, gap=0.32, extra=None):
    out, t = [], start
    for i in ids:
        t += (extra or {}).get(i, 0)
        out.append((t, i))
        t += L(i) + gap
    return out, t


def plan():
    S = []
    ln, t = seq(["01"], 0.5)
    S.append(O.Shot("cold", max(t + 0.6, 5.0), ln))                                  # つかみ → 2.4秒でタイトル
    ln, t = seq(["02", "03"], 1.4, extra={"03": 0.4})
    S.append(O.Shot("watch", t + 0.6, ln))                                             # 離れてハルトを見る。深呼吸
    ln, t = seq(["04", "05", "06", "01", "07", "08", "09", "10"], 1.3,
                extra={"05": 0.3, "06": 0.2, "01": 0.4, "07": 1.0, "08": 0.2, "09": 0.5, "10": 0.3})
    s = O.Shot("talk", t + 1.0, ln); s.hit = ln[3][0] + L("01"); S.append(s)          # 声をかける
    ln, t = seq(["11", "12", "13"], 0.9, extra={"12": 0.2, "13": 0.5})
    s = O.Shot("first", t + 1.6, ln); s.ok = t + 0.1; S.append(s)                      # 1次選考会
    s = O.Shot("second", 5.0); s.rev = 2.8; S.append(s)                                 # 2次選考会 → 活動先決定
    ln, t = seq(["14", "15", "16"], 1.0, extra={"15": 0.3, "16": 1.0})
    S.append(O.Shot("home", t + 1.8, ln))                                              # 帰り道
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
    if cur == "12" and t - [a for a, b in s.lines if b == "12"][0] > L("12") * 0.55:
        cur = "12b"
    return cur


SH = plan()
NOSUB = False


def shot(name):
    return next(s for s in SH if s.name == name)


# ---------- 絵 ----------
HB, KB = S9.HB, S9.KB
BG_EVE = S6.BG_EVE


def clock(img, date, time_, n=1):
    O.clock_big(img, date, time_, grade="大学1年")
    O.counter(img, n)


def badge(img, text, col):
    S9.bigbadge(img, text, col)


def hook(img, t):
    if t < 2.4:
        im = E.fit_text(["初対面なのに、", "知りすぎた。"], 116, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={1: YEL})
        E.paste_center(img, im, 540, 1090, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["ガクチカ・ループ 第10話", "今度は、こっちから"], 90, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1060, E.pop(t - 2.4))


def checks(img, items, t0, t):
    """選考会の ✓ 札"""
    for j, (txt, col) in enumerate(items):
        u = (t - t0 - j * 0.35) / 0.3
        if u > 0:
            F.pill(img, txt, 1200 + j * 110, 52, col, u=u)


def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "cold":
        u = ease(t / s.dur)
        h = S9.haruto(HB, math.pi + 0.5, "normal", sit=True, head_yaw=-0.35, head_pitch=0.08)
        k = S9.kanata(KB, -math.pi / 2 + 0.25, "shock")
        if t < 2.4:
            img, _ = S9.campus_img(h.boxes() + k.boxes(), S9.cam_over_k(u, 1.3))
        else:
            img, _ = S9.campus_img(h.boxes() + k.boxes(), S9.cam_k_face(ease((t - 2.4) / (s.dur - 2.4))))
        clock(img, "2026年12月8日（火）", "12:25")
        hook(img, t)
    elif n == "watch":
        u = ease(t / s.dur)
        a, b = (x[0] for x in s.lines)
        h = S9.haruto(HB, math.pi, "normal", sit=True, head_pitch=0.25)          # スマホを見ている
        k = S9.kanata((0.3, 1.6, 0), -0.75, "resolve" if t > a else "normal")
        k.set(bob=0.02 * math.sin(t * 2.2))                                       # 深呼吸
        tk = C.tokei_boxes((0.6, 1.25, 1.95 + (1 - ease(min(1, max(0, t - b + 0.6) / 0.5))) * 1.4), t, "eyes", 0.45, -2.0) \
            if t > b - 0.6 else []
        if t < a - 0.1:   # 背中越しに、遠くのハルト
            cam = Camera((lerp(-0.6, -0.5, u), lerp(-0.4, -0.2, u), 2.0), (2.6, 4.2, 1.0), 46)
        else:             # カナタの顔（決心）
            cam = Camera((lerp(3.7, 3.5, u), lerp(2.95, 2.85, u), 1.8), (0.3, 1.6, 1.78), 44)
        img, _ = S9.campus_img(h.boxes() + k.boxes() + list(tk), cam)
        clock(img, "2026年12月8日（火）", "12:20")
        badge(img, "大学の中庭", (40, 150, 90))
    elif n == "talk":
        ln = s.lines
        t4, t5, t6, t1, t7, t8, t9, t10 = (x[0] for x in ln)
        if t < 1.1:                                                               # 歩いて近づく
            v = ease(min(1, t / 1.1))
            k = S9.walk(S9.kanata((lerp(0.6, KB[0], v), lerp(1.9, KB[1], v), 0), -math.pi / 2 + 0.25, "normal"), t, 1 - v)
            h = S9.haruto(HB, math.pi, "normal", sit=True, head_pitch=0.25)
            img, _ = S9.campus_img(h.boxes() + k.boxes(), S9.cam_two(ease(t / 3)))
        else:
            who = TEXT[sid][0] if sid else None
            hx = "smile" if t > t8 - 0.1 else "normal"
            kx = "open"
            if t > t6 - 0.1:
                kx = "normal"
            if t > s.hit:
                kx = "shock"
            if t > t8 - 0.1:
                kx = "smile"
            h = S9.haruto(HB, math.pi + 0.5, hx, sit=True, head_yaw=-0.35, head_pitch=0.08 if t5 - 0.1 < t < t8 else 0.0)
            k = S9.kanata(KB, -math.pi / 2 + 0.25, kx, armR=0.6 * abs(math.sin(t * 5)) if t7 < t < t8 else 0.05,
                          armL=0.6 * abs(math.sin(t * 5 + 1)) if t7 < t < t8 else 0.05)
            hshot = who == "H" or (sid is None and (t5 - 0.3 < t < t6 - 0.2 or s.hit - 0.2 < t < s.hit + 0.1 or t8 - 0.3 < t < t10 - 0.2))
            if hshot:
                img, _ = S9.campus_img(h.boxes() + k.boxes(), S9.cam_over_k(ease(((t - t4) % 4) / 4), 1.75))
            else:
                img, _ = S9.campus_img(h.boxes() + k.boxes(), S9.cam_k_face(ease(((t - t4) % 4) / 4)))
            if s.hit < t < t7 - 0.1:
                Q.big_word(img, "しまった", t - s.hit - 0.1, RED, y=1180, size=140)
        clock(img, "2026年12月8日（火）", "12:25")
        badge(img, "大学の中庭", (40, 150, 90))
    elif n == "first":
        a, b, c = (x[0] for x in s.lines)
        if sid in ("11", "13") or t < a - 0.1 or b + L("12") < t < c - 0.1:
            img = R.meet_img(R.cam_mio(t, s.dur), mexpr="smile" if t > c - 0.1 else "normal", kexpr="normal",
                             talk="M" if sid in ("11", "13") else None, t=t)
        else:
            img = R.meet_img(R.cam_kanata(t, s.dur), kexpr="resolve" if sid else "normal")
        clock(img, "2026年12月12日（土）", "14:00")
        badge(img, "1次選考会", (64, 110, 220))
        if t > s.ok:
            checks(img, [("1次選考会 ✓", (40, 150, 90)), ("ハルトも：NPOインターン希望", (110, 200, 130))], s.ok, t)
    elif n == "second":
        k = R.kanata_seat("smile" if t > s.rev else "resolve")
        k.pos = (3.0, 2.1, 0)
        bow = ease(min(1, max(0, t - 1.0) / 0.4)) * (1 - ease(min(1, max(0, t - 2.0) / 0.4)))
        k.set(lean=0.45 * bow)
        u = ease(t / s.dur)
        cam = Camera((lerp(3.95, 3.9, u), lerp(0.2, 0.6, u), 2.0), (3.0, 5.2, 0.95), 50)
        img, _ = render(F.ROOM2 + F.morishita_seat().boxes() + F.host_seat().boxes() + k.boxes(), cam, R.BG_MEET)
        img = img.convert("RGBA")
        clock(img, "2026年12月17日（木）", "10:00")
        if t < s.rev:
            F.pill(img, "2次選考会", 1010, 46, (64, 110, 220), u=(t - 0.1) / 0.3)
            F.pill(img, "今度は、自分の言葉で。", 1105, 54, (230, 170, 30), (20, 20, 30), u=(t - 0.5) / 0.3)
        else:
            img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(90 * min(1, (t - s.rev) / 0.3)))))
            V5.stamp(img, t - s.rev)
    elif n == "home":
        u = ease(t / s.dur)
        a, b, c = (x[0] for x in s.lines)
        x = lerp(-1.0, 1.4, u)
        k = S9.walk(S9.kanata((x, 2.0, 0), -math.pi / 2, "smile" if t > c else "resolve"), t, 0.6)
        k.set(head_yaw=-0.5 if a - 0.2 < t < c + 1.0 else 0.0)
        tk = C.tokei_boxes((x + 0.75, 1.6, 1.85), t, "eyes", 0.45, math.pi + 0.3)
        cam = Camera((x + 0.25, -1.9, 1.95), (x + 0.3, 2.0, 1.72), 44)
        img, _ = render(S9.CAMPUS + k.boxes() + tk, cam, BG_EVE)
        img = img.convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 150, 80, 28)))
        clock(img, "2026年12月17日（木）", "17:00")
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "誘いたい友達、", 600, t, size=84)
        O.caption(img, "いる？", 730, t, size=110, col=YEL)
        for txt, y, sz, col, path in ((["コメントで教えてね"], 900, 56, (255, 255, 255), BLACK),
                                      (["次回 第11話「議会、むずかしすぎる」"], 1030, 52, (255, 255, 255), BLACK),
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
