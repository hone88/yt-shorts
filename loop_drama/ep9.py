"""ガクチカ・ループ 第9話「全部、消えた。」（リメイク版台本・11/9 ゆうきさんOK）
3周目（残りループ 1）。12/5の朝、第1話と同じメッセージ。説明会のミオは「はじめまして」。
12/7 大学でハルトに声をかけると「…えっと、誰？」。ルール⑤：ループすると、会った人は覚えていない。
夜の部屋「…意味、なかったのかな。」→ トケイ「全部消えても、カナタの中には残ってるのだ。」→「今度は、自分から。」
場面ごとに0.2秒ずつ長くして余韻を持たせる（11/9 指示）。
python3 ep9.py still <shot> <t> | python3 ep9.py build"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import g3d as G
from g3d import Camera, Rig, render, hexc
import characters as C
import ep1b as O
import ep1c as P
import ep2 as Q
import ep4 as F
import ep5 as V5
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep9"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED = (255, 216, 77), (255, 90, 90)
O.SPEAK["H"] = ("ハルト", (110, 200, 130))
PAD = 0.2   # 場面ごとに足す余韻

# ---------- 声 ----------
VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep9/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("H", "…えっと、[誰]？"),
    "02": ("K", "…また、|この[メッセージ]。"),
    "03": ("T", "残り、[1回]なのだ。"),
    "04": ("K", "…分かってる。"),
    "05": ("M", "[はじめまして]。|宮路ミオです。"),
    "06": ("K", "（…[はじめまして]、か。）"),
    "07": ("K", "[ハルト]！"),
    "08": ("K", "キックオフで…|いや、[なんでもない]。"),
    "09": ("H", "え？ …じゃあ。"),
    "10": ("T", "前のループのことは、|誰も[覚えてない]のだ。"),
    "11": ("K", "…[森下さん]も？"),
    "12": ("T", "…そうなのだ。"),
    "13": ("K", "…[意味]、|なかったのかな。"),
    "14": ("T", "全部消えても、|[カナタの中]には|残ってるのだ。"),
    "15": ("K", "…もう一回、[やる]。"),
    "16": ("K", "今度は、[自分から]。"),
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
    S.append(O.Shot("cold", max(t + 0.6, 5.0), ln))                         # つかみ → 2.4秒でタイトル
    ln, t = seq(["02", "03", "04"], 2.0, extra={"03": 0.3, "04": 0.2})
    S.append(O.Shot("morning", t + 0.8, ln))                                  # 12/5 8:00 第1話と同じメッセージ
    ln, t = seq(["05", "06"], 0.7, extra={"06": 0.5})
    S.append(O.Shot("call", t + 0.9, ln))                                     # 説明会：ミオ「はじめまして」
    ln, t = seq(["07", "01", "08", "09"], 1.0, extra={"01": 0.4, "08": 1.1, "09": 0.3})
    s = O.Shot("bench", t + 2.0, ln); s.who = ln[1][0]; s.leave = t; S.append(s)   # 12/7 大学：「…えっと、誰？」→ 去る
    ln, t = seq(["10", "11", "12"], 1.2, extra={"11": 0.6, "12": 0.4})
    S.append(O.Shot("rule", t + 1.0, ln))                                     # ルール⑤
    ln, t = seq(["13", "14"], 1.2, extra={"14": 2.0})
    S.append(O.Shot("night", t + 1.6, ln))                                    # 夜の部屋（余韻を長く）
    ln, t = seq(["15", "16"], 0.8, extra={"16": 0.9})
    s = O.Shot("resolve", t + 2.0, ln); s.up = ln[1][0] + L("16"); S.append(s)    # 顔を上げる → 明るく
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


# ---------- セット：大学の中庭 ----------
def campus_set():
    S = []
    S += P.blocks(-3, 9, -4, 10, -1, 0, hexc("#7fb65a"), 0.06, 91)           # 芝生
    S += P.blocks(-3, 9, 1, 3, -1, 0, hexc("#c9c0ae"), 0.04, 92)             # 通路
    S += P.blocks(-3, 9, 8, 9, 0, 6, hexc("#e2d9c8"), 0.03, 93)              # 校舎の壁
    for x in (-2.2, 0.2, 2.6, 5.0, 7.0):                                       # 窓
        for z in (1.2, 3.2):
            S.append(P.slab(x, 7.95, z, 1.3, 0.06, 1.2, hexc("#9fc8e8"), glow=True))
    for (x, y) in ((-1.6, 5.6), (6.6, 5.2)):                                  # 木
        S.append(P.slab(x + 0.35, y + 0.35, 0, 0.3, 0.3, 1.6, hexc("#6a4a30")))
        S.append(P.slab(x, y, 1.6, 1.0, 1.0, 1.0, hexc("#4a9a4a")))
        S.append(P.slab(x + 0.15, y + 0.15, 2.6, 0.7, 0.7, 0.5, hexc("#5aaa52")))
    # ベンチ（座面の高さ0.45）
    S.append(P.slab(1.9, 4.0, 0.38, 2.2, 0.6, 0.08, hexc("#a8744a")))
    S.append(P.slab(1.9, 4.55, 0.46, 2.2, 0.08, 0.6, hexc("#a8744a")))
    for x in (2.0, 3.9):
        S.append(P.slab(x, 4.05, 0, 0.1, 0.5, 0.38, hexc("#3a3a42")))
    return S


CAMPUS = campus_set()
BG_SKY = E.sky((120, 180, 240), (220, 236, 250)).convert("RGB").resize((W * G.SS, H * G.SS))
BG_NIGHT = E.sky((10, 14, 40), (34, 44, 86)).convert("RGB").resize((W * G.SS, H * G.SS))
HB = (3.3, 4.3, 0)      # ハルトが座る位置
KB = (1.9, 3.1, 0)      # カナタが立つ位置


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


def walk(r, t, k=1.0):
    a = 0.5 * math.sin(t * 9) * k
    r.set(legL=a, legR=-a, armL=-a * 0.7, armR=a * 0.7, bob=0.03 * abs(math.sin(t * 9)) * k)
    return r


def campus_img(boxes, cam, keep=None):
    img, mask = render(CAMPUS + boxes, cam, BG_SKY, keep=keep or set())
    return img.convert("RGBA"), mask


def cam_over_k(u, tz=1.35):
    """カナタの背中越しにハルト"""
    return Camera((lerp(1.6, 1.7, u), lerp(1.3, 1.5, u), 1.95), (3.3, 4.3, tz), 40)


def cam_k_face(u, push=0.25):
    """ハルトの側からカナタの顔"""
    return Camera((lerp(4.15, 3.85, u * push * 4), lerp(2.45, 2.6, u * push * 4), 1.8), (1.9, 3.1, 1.6), 44)


def cam_two(u):
    return Camera((lerp(2.75, 2.8, u), lerp(-3.6, -3.2, u), 2.3), (2.8, 3.6, 0.95), 50)


# ---------- 部屋（夜） ----------
def night_room(k, cam, extra=(), dark=0.35):
    img, _ = render(P.ROOM + k.boxes() + Q.laptop() + list(extra), cam, BG_NIGHT)
    img = img.convert("RGBA")
    img.alpha_composite(Image.new("RGBA", (W, H), (8, 10, 40, int(255 * dark))))
    return img


# ---------- 文字 ----------
def clock(img, date, time_, n=1, grade="大学1年", flash=0.0, pulse=0.0):
    O.clock_big(img, date, time_, flash=flash, grade=grade)
    O.counter(img, n, pulse)


def bigbadge(img, text, col):
    f = O.F(BLACK, 66)
    w = f.getlength(text) + 80
    y = O.CLOCK_Y + 380
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle([540 - w / 2, y, 540 + w / 2, y + 100], radius=50, fill=col + (240,))
    img.alpha_composite(lay)
    ImageDraw.Draw(img).text((540 - w / 2 + 40, y + 10), text, font=f, fill=(255, 255, 255))


def rule5(img, u):
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    y0 = 700
    d.rounded_rectangle([60, y0, W - 60, y0 + 400], radius=40, fill=(10, 12, 30, int(235 * e)), outline=(255, 216, 77, int(255 * e)), width=8)
    a = int(255 * e)
    ft, fb = O.F(BLACK, 56), O.F(BLACK, 70)
    d.text((540 - ft.getlength("ループのルール⑤") / 2, y0 + 34), "ループのルール⑤", font=ft, fill=(255, 216, 77, a))
    for j, (ln, col) in enumerate([("ループすると、会った人は", (255, 255, 255, a)), ("覚えていない", (255, 90, 90, a))]):
        d.text((540 - fb.getlength(ln) / 2, y0 + 140 + j * 104), ln, font=fb, fill=col)
    img.alpha_composite(lay)


def hook(img, t):
    if t < 2.4:
        im = E.fit_text(["仲間が、", "ぼくを", "覚えていない。"], 112, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={2: RED})
        E.paste_center(img, im, 540, 1090, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["ガクチカ・ループ 第9話", "全部、消えた。"], 96, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1000, E.pop(t - 2.4))


MSG = ["今日10時から、オンラインの", "説明会あるよ。家からでいいから、", "出てみない？"]


# ---------- 1コマ ----------
def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "cold":
        u = ease(t / s.dur)
        if t < 2.4:
            h = haruto(HB, math.pi + 0.5, "normal", sit=True, head_yaw=-0.35, head_pitch=-0.05)
            k = kanata(KB, -math.pi / 2 + 0.25, "shock", armL=0.4)
            img, _ = campus_img(h.boxes() + k.boxes(), cam_over_k(u, 1.3))
        else:
            h = haruto(HB, math.pi + 0.5, "normal", sit=True, head_yaw=-0.35)
            k = kanata(KB, -math.pi / 2 + 0.25, "shock", armL=0.4)
            img, _ = campus_img(h.boxes() + k.boxes(), cam_k_face(ease((t - 2.4) / (s.dur - 2.4))))
        clock(img, "2026年12月7日（月）", "12:30")
        hook(img, t)
    elif n == "morning":
        k = F.kanata_phone_bed("normal" if t < s.lines[2][0] else "blank")
        tk = Q.tokei_near(t, "eyes", drop_t=t - s.lines[1][0] + 0.5) if t > s.lines[1][0] - 0.5 else []
        img = Q.room_img(k, F.bed_cam(t, s.dur, 0.3), list(tk))
        clock(img, "2026年12月5日（土）", "8:00")
        if 0.5 < t < s.lines[1][0] - 0.2:
            F.msg_card(img, (t - 0.5) / 0.3, "宮路ミオ", MSG, y0=760)
    elif n == "call":
        img = V5.call_img(s.start + t, sid == "05")
        clock(img, "2026年12月5日（土）", "10:00")
        bigbadge(img, "オンライン説明会", (64, 110, 220))
        if t > s.lines[1][0] - 0.1:
            img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 50, 90)))
    elif n == "bench":
        a, b, c, d_ = (x[0] for x in s.lines)
        u = ease(t / s.dur)
        if t < b - 0.15:                                       # 「ハルト！」笑顔でかけよる
            v = ease(min(1, t / 1.2))
            k = walk(kanata((lerp(0.2, KB[0], v), lerp(2.2, KB[1], v), 0), -math.pi / 2 + 0.25, "smile", ), t, 1 - v)
            k.set(armR=-1.6 if a - 0.1 < t < a + 0.9 else 0.05)
            h = haruto(HB, math.pi, "normal", sit=True, head_pitch=0.25 if t < a + 0.3 else 0.0, head_yaw=0.0 if t < a + 0.3 else -0.4)
            img, _ = campus_img(h.boxes() + k.boxes(), cam_two(u))
        elif t < b + L("01") + 0.1:                           # 「…えっと、誰？」
            h = haruto(HB, math.pi + 0.5, "normal", sit=True, head_yaw=-0.35, head_pitch=-0.05)
            k = kanata(KB, -math.pi / 2 + 0.25, "smile")
            img, _ = campus_img(h.boxes() + k.boxes(), cam_over_k(ease((t - b) / 2.0), 1.75))
        elif t < d_ - 0.1:                                     # 固まる → 「…いや、なんでもない」
            v = ease(min(1, (t - b - L("01")) / 1.0))
            ex = "shock" if t < c - 0.2 else "blank"
            h = haruto(HB, math.pi + 0.5, "normal", sit=True, head_yaw=-0.35)
            k = kanata(KB, -math.pi / 2 + 0.25, ex)
            img, _ = campus_img(h.boxes() + k.boxes(), cam_k_face(v))
            if t < c - 0.3:
                Q.big_word(img, "…え？", t - b - L("01"), RED, y=1180, size=150)
        else:                                                  # ハルトが去っていく
            w_ = max(0.0, t - s.leave)
            hx = HB[0] + 0.8 * w_
            h = haruto((hx, HB[1] - 0.6 * min(1, w_ * 2), 0), -math.pi / 2 if w_ > 0 else math.pi + 0.5, "normal",
                       sit=w_ <= 0, head_yaw=-0.35 if w_ <= 0 else 0.0)
            if w_ > 0:
                walk(h, t)
            k = kanata(KB, -math.pi / 2 + 0.25, "blank")
            img, _ = campus_img(h.boxes() + k.boxes(), cam_two(u))
        clock(img, "2026年12月7日（月）", "12:30")
        bigbadge(img, "大学の中庭", (40, 150, 90))
    elif n == "rule":
        u = ease(t / s.dur)
        a = s.lines[0][0]
        drop = (1 - ease(min(1, max(0, t - 0.2) / 0.5))) * 1.4
        k = kanata(KB, math.pi - 0.2, "blank", head_pitch=0.15)
        tk = C.tokei_boxes((KB[0] + 0.85, KB[1] - 0.35, 1.75 + drop), t, "eyes", 0.5, math.pi + 0.3)
        img, mask = campus_img(k.boxes() + tk, Camera((lerp(2.45, 2.4, u), lerp(0.2, 0.55, u), 1.72), (2.25, 3.0, 1.55), 46),
                               keep={"kanata", "tokei"})
        img = O.desat(img, 0.6, mask)
        clock(img, "2026年12月7日（月）", "12:40")
        if t < s.lines[1][0] - 0.1:
            rule5(img, (t - 0.3) / 0.3)
    elif n == "night":
        u = ease(t / s.dur)
        k = Q.kanata_bed("blank" if t < s.lines[1][0] else "normal")
        k.set(head_pitch=lerp(0.38, 0.3, u))
        tk = C.tokei_boxes((2.93, 3.2, 1.55), t, "eyes", 0.5, math.pi + 0.45) if t > s.lines[1][0] - 1.2 else []
        img = night_room(k, Q.face_cam(t, s.dur, 0.35), tk)
        clock(img, "2026年12月7日（月）", "23:00")
    elif n == "resolve":
        u = ease(t / s.dur)
        b = s.lines[1][0]
        up = ease(min(1, max(0, t - 0.2) / 0.6))
        k = Q.kanata_bed("resolve")
        k.set(head_pitch=lerp(0.3, -0.02, up))
        tk = C.tokei_boxes((2.93, 3.2, 1.55), t, "eyes", 0.5, math.pi + 0.45)
        dark = 0.35 if t < s.up else lerp(0.35, 0.12, ease(min(1, (t - s.up) / 0.6)))
        img = night_room(k, Q.face_cam(t, s.dur, 0.45), tk, dark=dark)
        clock(img, "2026年12月7日（月）", "23:05")
        if t > s.up:
            im = E.fit_text(["今度は、自分から。"], 120, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=14, hl={0: YEL})
            E.paste_center(img, im, 540, 1260, E.pop(t - s.up))
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "あなたなら、", 600, t, size=84)
        O.caption(img, "もう一度やる？", 730, t, size=110, col=YEL)
        for txt, y, sz, col, path in ((["コメントで教えてね"], 900, 56, (255, 255, 255), BLACK),
                                      (["次回 第10話「今度は、こっちから」"], 1030, 52, (255, 255, 255), BLACK),
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
