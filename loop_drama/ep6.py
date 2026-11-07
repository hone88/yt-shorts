"""ガクチカ・ループ 第6話「キックオフ」（2周目・2027年1月30日）
冒頭の事件：お辞儀の練習で、カナタだけ浅い。
マナー研修（お辞儀・名刺）→ 目標づくり（カナタ「…面接で答える。」／ハルト「地元の子どもの、居場所をつくりたい。」）
→ ミニゲーム（共通点探し）でハイタッチ → 帰り道、トケイ「来週から、いよいよインターンなのだ。」
python3 ep6.py still <shot> <t> | python3 ep6.py build"""
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
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep6"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED, GRN = (255, 216, 77), (255, 90, 90), (90, 220, 120)
DATE = "2027年1月30日（土）"
O.SPEAK["H"] = ("ハルト", (110, 200, 130))

# ---------- 声 ----------
VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep6/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("M", "カナタ、|もうちょっと[深く]。"),
    "02": ("M", "今日は、[マナー研修]と、|[目標づくり]。"),
    "03": ("H", "ハルトです。|よろしく。"),
    "04": ("K", "…宇野です。"),
    "05": ("H", "目標、人前で自分の考えを…|[面接で答える]…。|[正直]だな。"),
    "06": ("K", "…お前は？"),
    "07": ("H", "地元の子どもの、|[居場所]をつくりたい。"),
    "11": ("H", "よし、[共通点]、|5個そろった！"),
    "08": ("K", "（…[ちゃんとしてる]な、|こいつ。）"),
    "09": ("T", "来週から、いよいよ|[インターン]なのだ。"),
    "10": ("K", "…うん。"),
}
GOAL_K = ["人前で自分の考えを", "伝えられるようになる。", "面接で答える。"]
GOAL_H = ["地元の子どもの、", "居場所をつくりたい。"]


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
    S.append(O.Shot("bow", max(t + 0.4, 4.6), ln))
    ln, t = seq(["02"], 0.6)
    S.append(O.Shot("hall", t + 0.6, ln))
    ln, t = seq(["03", "04"], 0.7, extra={"04": 0.2})
    S.append(O.Shot("card", t + 0.4, ln))
    ln, t = seq(["05", "06"], 1.1, extra={"06": 0.3})
    S.append(O.Shot("goal", t + 0.2, ln))
    ln, t = seq(["07"], 0.9)                          # 声の前に間
    S.append(O.Shot("dream", t + 0.9, ln))
    ln, t = seq(["11", "08"], 0.5, extra={"08": 1.0})  # ハイタッチの間
    s = O.Shot("game", t + 0.5, ln); s.hi = ln[0][0] + L("11") + 0.15; S.append(s)
    ln, t = seq(["09", "10"], 0.8, extra={"10": 0.3})
    S.append(O.Shot("street", t + 0.6, ln))
    S.append(O.Shot("end", 5.0))
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


# ---------- 会場（大部屋・テーブル6つ） ----------
TABLES = [(1.6, 3.0), (5.0, 3.0), (8.4, 3.0), (1.6, 6.4), (5.0, 6.4), (8.4, 6.4)]


def hall_set():
    S = []
    S += P.blocks(-1, 11, -3, 12, -1, 0, hexc("#c8b898"), 0.05, 61)          # 床
    S += P.blocks(-1, 11, 12, 13, 0, 4, hexc("#eef2f4"), 0.02, 62)            # 前の壁
    S += P.blocks(-2, -1, -3, 12, 0, 4, hexc("#e8eef2"), 0.02, 63)
    S += P.blocks(11, 12, -3, 12, 0, 4, hexc("#e8eef2"), 0.02, 64)
    S += P.blocks(-1, 11, -4, -3, 0, 4, hexc("#e8eef2"), 0.02, 65)
    S.append(P.slab(2.6, 11.92, 1.1, 4.8, 0.06, 2.2, hexc("#fafafa")))      # スクリーン
    S.append(P.slab(2.55, 11.9, 1.05, 4.9, 0.04, 0.05, hexc("#8a8a90")))
    S.append(P.slab(3.3, 11.88, 2.6, 3.4, 0.03, 0.4, hexc("#ff8a1f")))      # 帯（オレンジ）
    for (x, y) in TABLES:
        S.append(P.slab(x - 0.8, y - 0.5, 0.0, 1.6, 1.0, 0.72, hexc("#e8e2d6")))
        S.append(P.slab(x - 0.85, y - 0.55, 0.72, 1.7, 1.1, 0.05, hexc("#f2ede4")))
    return S


HALL = hall_set()
BG_HALL = R.BG_MEET
BG_EVE = E.sky((236, 140, 90), (250, 208, 160)).convert("RGB").resize((W * G.SS, H * G.SS))

MOB = V5.STUDENTS


def mob(i, pos, yaw, **pose):
    r = Rig(MOB[i % len(MOB)], pos, yaw, tag=f"st{i}")
    r.set(armL=0.05, armR=0.05)
    r.set(**pose)
    return r


def kanata(pos, yaw, expr="normal", **pose):
    r = Rig(C.KANATA, pos, yaw, tag="kanata")
    r.set(armL=0.05, armR=0.05)
    r.set(**pose)
    r.expr = expr
    return r


def haruto(pos, yaw, expr="normal", **pose):
    r = Rig(C.HARUTO, pos, yaw, tag="haruto")
    r.set(armL=0.05, armR=0.05)
    r.set(**pose)
    r.expr = expr
    return r


def mio_front(expr="smile", **pose):
    r = Rig(C.MIO, (5.0, 10.2, 0), math.pi, tag="mio")
    r.set(armL=0.05, armR=0.05)
    r.set(**pose)
    r.expr = expr
    return r


def crowd(t, lean=0.0, skip=()):
    """テーブルのまわりに立つ学生たち"""
    out = []
    k = 0
    for ti, (x, y) in enumerate(TABLES):
        for j, dx in enumerate((-0.55, 0.55)):
            if (ti, j) in skip:
                continue
            out += mob(k, (x + dx, y - 0.85, 0), 0.0, lean=lean, head_yaw=0.1 * math.sin(t * 1.3 + k)).boxes()
            k += 1
    return out


# ---------- 文字 ----------
def clock(img, time_):
    O.clock_big(img, DATE, time_, grade="大学1年")
    O.counter(img, 2)


def hook(img, t):
    if t < 2.4:
        im = E.fit_text(["お辞儀の練習。", "ぼくだけ、浅い。"], 120, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={1: RED})
        E.paste_center(img, im, 540, 1100, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["ガクチカ・ループ 第6話", "キックオフ"], 96, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1100, E.pop(t - 2.4))


def sheet(img, u, title, lines, col=(40, 40, 50), y0=700):
    """目標シート（大きく見せる）"""
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a = int(255 * e)
    y0 = y0 + (1 - e) * 40
    h = 150 + 84 * len(lines)
    d.rounded_rectangle([90, y0, W - 90, y0 + h], radius=26, fill=(252, 250, 242, int(248 * e)), outline=(60, 64, 80, a), width=6)
    d.rounded_rectangle([90, y0, W - 90, y0 + 84], radius=26, fill=(255, 138, 31, a))
    fh, fl = O.F(BLACK, 46), O.F(BLACK, 62)
    d.text((540 - fh.getlength(title) / 2, y0 + 16), title, font=fh, fill=(255, 255, 255, a))
    for j, ln in enumerate(lines):
        c = RED if (ln.startswith("面接") and col is None) else (col or (40, 40, 50))
        d.text((140, y0 + 112 + j * 84), ln, font=fl, fill=c + (a,))
    img.alpha_composite(lay)


# ---------- 1コマ ----------
def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "bow":
        # 横一列でお辞儀。みんな深いのに、カナタだけ浅い
        b = ease(min(1, max(0, t - 0.15) / 0.4))
        boxes = []
        xs = [2.6, 3.4, 4.2, 5.0, 5.8, 6.6, 7.4]
        for i, x in enumerate(xs):
            if i == 3:
                boxes += kanata((x, 5.0, 0), 0.0, "blank", lean=0.16 * b).boxes()
            else:
                boxes += mob(i, (x, 5.0, 0), 0.0, lean=0.75 * b).boxes()
        u = ease(t / s.dur)
        cam = Camera((5.0, lerp(9.4, 8.8, u), 1.45), (5.0, 5.0, 1.42), 50)   # 前から：みんなの頭が下がり、カナタだけ起きている
        img, _ = render(HALL + boxes, cam, BG_HALL)
        img = img.convert("RGBA")
        clock(img, "13:10")
        hook(img, t)
    elif n == "hall":
        u = ease(t / s.dur)
        cam = Camera((5.0, lerp(0.6, 1.4, u), 2.3), (5.0, 9.6, 1.4), 46)
        boxes = crowd(t) + mio_front("smile", armR=1.3 + 0.2 * math.sin(t * 6) if sid else 0.05).boxes()
        img, _ = render(HALL + boxes, cam, BG_HALL)
        img = img.convert("RGBA")
        clock(img, "13:00")
        F.pill(img, "キックオフ会場", 1010, 46, (30, 58, 106), u=(t - 0.1) / 0.3)
        F.pill(img, "春インターン生が全員集まる、最初のイベント", 1100, 42, (40, 44, 60), u=(t - 0.4) / 0.3)
    elif n == "card":
        a, b = (x[0] for x in s.lines)
        give = ease(min(1, max(0, t - 0.3) / 0.4))
        k = kanata((4.55, 3.0, 0), -math.pi / 2, "open" if t < b else "normal",
                   armL=1.2 * give, armR=0.9 * give, head_pitch=0.15)
        h = haruto((5.55, 3.0, 0), math.pi / 2, "smile", armL=1.45 * give, armR=1.45 * give, lean=0.25 * give)
        cam = Camera((5.05, -0.2, 1.9), (5.05, 3.0, 1.4), 46) if t < b - 0.1 else Camera((6.7, 4.7, 1.8), (4.55, 3.0, 1.62), 40)
        img, _ = render(HALL + crowd(t, skip=((1, 0), (1, 1))) + k.boxes() + h.boxes(), cam, BG_HALL)
        img = img.convert("RGBA")
        clock(img, "13:25")
        F.pill(img, "マナー研修：名刺の練習", 1010, 46, (64, 110, 220), u=(t - 0.1) / 0.3)
    elif n == "goal":
        a, b = (x[0] for x in s.lines)
        k = kanata((4.55, 2.35, 0), 0.0, "normal" if t < b else "open", sit=True, armL=0.55, armR=0.55, head_pitch=0.2)
        h = haruto((5.5, 2.35, 0), 0.0, "normal", sit=True, armL=0.55, armR=0.55, head_yaw=0.5)
        cam = Camera((5.6, 0.2, 1.8), (5.0, 2.6, 1.3), 44)
        img, _ = render(HALL + crowd(t, skip=((1, 0), (1, 1))) + k.boxes() + h.boxes(), cam, BG_HALL)
        img = img.convert("RGBA")
        clock(img, "14:00")
        sheet(img, (t - 0.2) / 0.3, "目標シート　宇野カナタ", GOAL_K, None, y0=720)
    elif n == "dream":
        u = ease(t / s.dur)
        h = haruto((5.5, 2.35, 0), 0.0, "normal", sit=True, armL=0.55, armR=0.55, head_yaw=0.35)
        k = kanata((4.55, 2.35, 0), 0.0, "open", sit=True, armL=0.55, armR=0.55, head_yaw=-0.4)
        cam = Camera((lerp(4.9, 5.0, u), lerp(5.6, 5.2, u), 1.5), (5.3, 2.35, 1.55), lerp(42, 38, u))
        img, _ = render(HALL + k.boxes() + h.boxes(), cam, BG_HALL)
        img = img.convert("RGBA")
        clock(img, "14:05")
        e7 = s.lines[0][0] + L("07")
        if t > e7 + 0.1:   # 言い終わってから、ハルトの目標シート
            sheet(img, (t - e7 - 0.1) / 0.3, "目標シート　ハルト", GOAL_H, (40, 120, 60), y0=760)
    elif n == "game":
        a, b = (x[0] for x in s.lines)
        hi = ease(min(1, max(0, t - s.hi) / 0.25)) if t < s.hi + 1.2 else ease(max(0, 1 - (t - s.hi - 1.2) / 0.4))
        k = kanata((4.55, 2.2, 0), math.pi * 0.8, "smile" if t > s.hi else "open", armR=0.6 + 2.2 * hi, armL=0.1)
        h = haruto((5.45, 2.2, 0), -math.pi * 0.8, "smile", armL=0.6 + 2.2 * hi, armR=0.1)
        m1 = mob(1, (4.1, 3.5, 0), math.pi, armL=0.4 + 1.4 * hi)
        m2 = mob(2, (5.9, 3.5, 0), math.pi, armR=0.4 + 1.4 * hi)
        u = ease(t / s.dur)
        cam = Camera((5.0, lerp(-0.9, -0.5, u), 1.95), (5.0, 2.8, 1.55), 46)
        img, _ = render(HALL + k.boxes() + h.boxes() + m1.boxes() + m2.boxes(), cam, BG_HALL)
        img = img.convert("RGBA")
        clock(img, "15:30")
        F.pill(img, "ミニゲーム：チームで共通点さがし", 1010, 46, (64, 110, 220), u=(t - 0.1) / 0.3)
        if s.hi - 0.05 < t < s.hi + 0.9:
            Q.big_word(img, "パンッ！", t - s.hi + 0.05, YEL, y=820, size=120)
    elif n == "street":
        a, b = (x[0] for x in s.lines)
        k = R.kanata_stand("normal")
        k.set(head_pitch=-0.05, head_yaw=0.25 if t > a else 0.0)
        u = ease(t / s.dur)
        cam = Camera((lerp(2.95, 2.9, u), lerp(0.2, 0.7, u), 1.62), (2.65, 4.4, 1.55), 48)
        tk = Q.tokei_near(t, "eyes", t + 0.4, (3.25, 3.3, 1.75))
        img, _ = render(R.OUTSIDE + k.boxes() + tk, cam, BG_EVE)
        img = img.convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 140, 60, 36)))
        clock(img, "17:30")
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "あなたなら、", 560, t, size=84)
        O.caption(img, "目標に何て書く？", 680, t, size=96, col=YEL)
        for txt, y, sz, col, path in ((["コメントで教えてね"], 860, 60, (255, 255, 255), BLACK),
                                      (["次回 第7話「名刺の渡し方」"], 990, 52, (255, 255, 255), BLACK),
                                      (["ドットジェイピー広島第一支部", "春インターン申込は12月31日まで"], 1140, 48, YEL, BLACK),
                                      (["この動画は「勇気を出して一歩を踏み出そう」という", "メッセージを伝えるための創作ドラマです"], 1300, 32, (220, 226, 245), BOLD)):
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
