"""ガクチカ・ループ 第11話「議会、むずかしすぎる」（リメイク版台本・11/12 ゆうきさんOK）
2/17 議会傍聴。前は「まあ、いっか」で流した「補正予算」を、今度は廊下で森下議員に聞く。メモは「？」だらけ →「…全部、聞いていいよ。」
事務所で「大学生の通学の費用、どう思う？」「…正直、きついです。」「それを、聞きたかったんだ。」
帰り道「…次は、通学のこと、調べてみる。」　場面ごとに0.2秒の余韻、転換音・環境音は6割。
カメラの寄りは場面の中で一方向、数コマだけの切り替えはしない（注意点8）。python3 ep11.py still <shot> <t> | plan | build"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import g3d as G
from g3d import Camera, Rig, render, hexc
import characters as C
import ep1b as O
import ep1c as P
import ep3 as R
import ep4 as F
import case1 as K1
import ep7 as S7
import ep8 as S8
import ep9 as S9
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep11"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED = (255, 216, 77), (255, 90, 90)
O.SPEAK["Mo"] = ("森下議員", (170, 172, 182))
PAD = 0.2
DATE = "2027年2月17日（水）"

VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep11/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("K", "（…[半分も]、分からん。）"),
    "02": ("K", "（…今度は、|[分からないまま]にしない。）"),
    "03": ("K", "あの…さっきの|『[補正予算]』って、|何ですか？"),
    "04": ("Mo", "お、[いい質問]だ。"),
    "05": ("Mo", "年度の途中で、予算を|[足したり、変えたり]|することだよ。"),
    "06": ("K", "…なるほど。"),
    "07": ("Mo", "…[全部]、聞いていいよ。"),
    "08": ("Mo", "大学生の[通学の費用]、|どう思う？"),
    "09": ("K", "…正直、[きついです]。"),
    "10": ("Mo", "それを、[聞きたかった]んだ。"),
    "11": ("T", "前のループでは、|[一度も]質問しなかったのだ。"),
    "12": ("K", "…うるさい。"),
    "13": ("K", "…次は、[通学のこと]、|調べてみる。"),
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
    S.append(O.Shot("cold", max(t + 0.6, 5.0), ln))                                     # つかみ → 2.4秒でタイトル
    ln, t = seq(["02"], 3.0)
    s = O.Shot("council", t + 0.9, ln); S.append(s)                                       # 傍聴席：メモに「補正予算？」
    ln, t = seq(["03", "04", "05", "06", "07"], 1.0, extra={"04": 0.3, "05": 0.1, "06": 0.2, "07": 2.4})
    s = O.Shot("hall", t + 1.2, ln); s.memo = ln[3][0] + L("06") + 0.3; S.append(s)       # 廊下で質問 →「？」だらけのメモ
    ln, t = seq(["08", "09", "10"], 2.6, extra={"09": 1.1, "10": 0.5})
    s = O.Shot("office", t + 1.8, ln); S.append(s)                                        # 事務所：「それを、聞きたかったんだ。」
    ln, t = seq(["11", "12", "13"], 1.0, extra={"12": 0.3, "13": 0.9})
    S.append(O.Shot("home", t + 1.8, ln))                                                 # 帰り道
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


def line_t(s, sid):
    return next(a for a, b in s.lines if b == sid)


# ---------- セット ----------
def hall_set():
    """議会の廊下（文字・ロゴなし）"""
    S = []
    S += P.blocks(-3, 9, -3, 5, -1, 0, hexc("#b8b0a2"), 0.04, 111)          # 床
    S += P.blocks(-3, 9, 5, 6, 0, 5, hexc("#e8e2d6"), 0.02, 112)             # 奥の壁
    for x in (-2.0, 1.2, 4.4, 7.0):                                           # 窓
        S.append(P.slab(x, 4.96, 1.3, 1.6, 0.05, 1.6, hexc("#a8cce8"), glow=True))
    S.append(P.slab(2.6, 4.6, 0, 1.6, 0.4, 0.45, hexc("#6a5a4a")))           # 長いす
    S += [P.slab(-1.2, 4.3, 0, 0.6, 0.6, 0.5, hexc("#6a4a30")), P.slab(-1.25, 4.25, 0.5, 0.7, 0.7, 1.1, hexc("#4a9a4a"))]
    return S


HALL = hall_set()
BG_HALL = E.sky((236, 232, 224), (246, 244, 240)).convert("RGB").resize((W * G.SS, H * G.SS))
BG_EVE = E.sky((236, 140, 90), (250, 208, 160)).convert("RGB").resize((W * G.SS, H * G.SS))
KH, MH = (2.0, 2.4, 0), (3.25, 2.4, 0)      # 廊下のカナタ・森下議員


def clock(img, time_):
    O.clock_big(img, DATE, time_, grade="大学1年")
    O.counter(img, 1)


def hook(img, t):
    if t < 2.4:
        im = E.fit_text(["前は『まあ、いっか』", "だった。"], 110, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={0: YEL})
        E.paste_center(img, im, 540, 1170, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["ガクチカ・ループ 第11話", "議会、むずかしすぎる"], 90, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1060, E.pop(t - 2.4))


def words(img, t, t0=0.2):
    for j, (w, x, y) in enumerate([("補正予算", 300, 900), ("付託", 800, 1000), ("採決", 420, 1110)]):
        if t > t0 + j * 0.35:
            im = E.fit_text([w], 66, 600, fill=(255, 255, 255), stroke=(8, 10, 24), sw=8)
            E.paste_center(img, im, x, y, E.pop(t - t0 - j * 0.35))


def memo(img, u, lines, y0=760):
    """カナタのメモ帳"""
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    h = 110 + 92 * len(lines)
    y = y0 + (1 - e) * 40
    d.rounded_rectangle([170, y, W - 170, y + h], radius=20, fill=(255, 252, 238, int(245 * e)), outline=(120, 110, 90, int(255 * e)), width=6)
    for j in range(len(lines)):
        d.line([200, y + 140 + j * 92, W - 200, y + 140 + j * 92], fill=(170, 200, 230, int(255 * e)), width=3)
    d.text((210, y + 24), "メモ", font=O.F(BOLD, 34), fill=(120, 110, 90, int(255 * e)))
    for j, (ln, col) in enumerate(lines):
        d.text((220, y + 70 + j * 92), ln, font=O.F(BLACK, 62), fill=col + (int(255 * e),))
    img.alpha_composite(lay)


def card(img, u, top, bottom):
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    y0 = 720
    d.rounded_rectangle([60, y0, W - 60, y0 + 330], radius=40, fill=(10, 12, 30, int(235 * e)), outline=(255, 216, 77, int(255 * e)), width=8)
    a = int(255 * e)
    fb = O.F(BLACK, 70)
    for j, (ln, col) in enumerate([(top, (255, 255, 255, a)), (bottom, (255, 216, 77, a))]):
        d.text((540 - fb.getlength(ln) / 2, y0 + 60 + j * 110), ln, font=fb, fill=col)
    img.alpha_composite(lay)


# ---------- 1コマ ----------
def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "cold":
        u = ease(t / s.dur)
        k = S8.kanata_phone((7.8, 3.0, 2.85), math.pi / 2 + 0.3, "blank", sit=True)
        cam = Camera((lerp(7.95, 7.9, u), lerp(-0.6, -0.3, u), 5.0), (7.6, 3.0, 4.5), 54)
        img, _ = render(S8.COUNCIL + S8.members(t) + k.boxes(), cam, S8.BG_COUNCIL)
        img = img.convert("RGBA")
        clock(img, "10:30")
        hook(img, t)
    elif n == "council":
        u = ease(t / s.dur)
        a = s.lines[0][0]
        k = S8.kanata_phone((7.8, 3.0, 2.85), math.pi / 2 + 0.3, "resolve" if t > a - 0.3 else "normal", sit=True)
        if t < 1.6:   # 傍聴席から議場を見下ろす
            cam = Camera((lerp(9.6, 9.55, u), lerp(5.6, 5.4, u), 5.6), (1.6, 4.4, 0.2), 60)
        else:         # 横から：座ってメモを取るカナタ
            cam = Camera((lerp(7.95, 7.9, u), lerp(-0.6, -0.3, u), 5.0), (7.6, 3.0, 4.5), 54)
        img, _ = render(S8.COUNCIL + S8.members(t) + k.boxes(), cam, S8.BG_COUNCIL)
        img = img.convert("RGBA")
        clock(img, "10:30")
        S9.bigbadge(img, "議会を傍聴中", (64, 110, 220))
        if t < 1.6:
            words(img, t)
        elif t < a - 0.1:
            memo(img, (t - 1.7) / 0.3, [("補正予算 ？", (40, 40, 50))], y0=1080)
    elif n == "hall":
        u = ease(t / s.dur)
        a = s.lines[0][0]
        walk = max(0.0, 1 - t / 0.9)
        k = K1.kanata(KH, -math.pi / 2, "open" if t < s.memo else "smile", armR=1.1 if s.memo - 0.2 < t else 0.05)
        mo = K1.morishita(MH, math.pi / 2, "normal", head_pitch=0.15 if s.memo + 0.4 < t else 0.0)
        S9.walk(k, t, walk); S9.walk(mo, t, walk)
        t7 = line_t(s, "07")
        last = None                          # 話し手が変わるまで同じ画を続ける（数コマだけの切り替えをしない）
        for (t0, i) in s.lines:
            if t >= t0 - 0.1:
                last = i
        if s.memo - 0.1 <= t < t7 - 0.1:
            last = None
        if last in ("04", "05", "07"):        # カナタの背中越しに森下議員
            cam = Camera((lerp(0.95, 1.0, u), lerp(0.95, 1.05, u), 1.95), (3.25, 2.4, 1.7), 42)
        elif last in ("03", "06"):           # 森下議員の背中越しにカナタ
            cam = Camera((lerp(4.3, 4.25, u), lerp(0.95, 1.05, u), 1.95), (2.0, 2.4, 1.75), 42)
        else:                                # 2人
            cam = Camera((lerp(2.6, 2.65, u), lerp(-4.2, -3.8, u), 1.9), (2.6, 2.4, 1.75), 40)
        img, _ = render(HALL + k.boxes() + mo.boxes(), cam, BG_HALL)
        img = img.convert("RGBA")
        clock(img, "11:40")
        S9.bigbadge(img, "議会の廊下", (110, 110, 130))
        t7 = line_t(s, "07")
        if s.memo < t < t7 - 0.1:
            memo(img, (t - s.memo) / 0.3, [("補正予算 ？", (40, 40, 50)), ("付託 ？　採決 ？", (40, 40, 50)), ("？？？？", RED)], y0=1060)
    elif n == "office":
        u = ease(t / s.dur)
        a, b, c = (x[0] for x in s.lines)
        mo = F.morishita_seat()
        mo.pos = (3.0, 5.5, 0)
        if sid in ("08", "10"):
            mo.set(head_pitch=0.04 * math.sin(t * 6))
        k = R.kanata_seat("smile" if t > c + 0.6 else ("normal" if t < b - 0.1 else "blank"))
        k.spec = C.KANATA_SUIT
        ot = S7.other((4.9, 4.2, 0), math.pi / 2 + 0.6, sit=True, armL=0.5, armR=0.5)
        if b - 1.0 < t < c - 0.1:            # 答えるカナタの顔（間ごと）
            cam = R.cam_kanata(t, s.dur)
        else:                                # カナタの背中越しに森下議員
            cam = R.cam_mio(t, s.dur)
        img, _ = render(R.MEET + mo.boxes() + k.boxes() + ot.boxes(), cam, R.BG_MEET)
        img = img.convert("RGBA")
        clock(img, "14:00")
        S9.bigbadge(img, "事務所で活動中", (200, 120, 40))
        if t < a - 0.1:
            card(img, (t - 0.3) / 0.3, "分からないことは、", "そのまま聞いていい")
    elif n == "home":
        u = ease(t / s.dur)
        a, b, c = (x[0] for x in s.lines)
        x = lerp(-1.0, 1.6, u)
        look = c - 0.3 < t < c + L("13") + 0.4
        k = S9.walk(K1.kanata((x, 1.2, 0), -math.pi / 2, "smile" if t > b - 0.1 else "normal",
                              armR=1.1 if look else 0.05, head_pitch=0.25 if look else 0.0), t, 0.6)
        tk = C.tokei_boxes((x + 0.75, 0.8, 1.85), t, "eyes", 0.45, math.pi + 0.3)
        cam = Camera((x + 0.25, -2.7, 1.95), (x + 0.3, 1.2, 1.72), 44)
        img, _ = render(K1.STREET + k.boxes() + tk, cam, BG_EVE)
        img = img.convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 150, 80, 28)))
        clock(img, "17:30")
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "分からないとき、", 600, t, size=84)
        O.caption(img, "あなたは聞ける？", 730, t, size=104, col=YEL)
        for txt, y, sz, col, path in ((["コメントで教えてね"], 900, 56, (255, 255, 255), BLACK),
                                      (["次回 第12話「自分から」"], 1030, 52, (255, 255, 255), BLACK),
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
