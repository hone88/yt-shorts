"""ガクチカ・ループ 第15話「地方大会」（見直し後のリメイク版台本・11/20 ゆうきさんOK）
冒頭：結果の張り出しに名前がない。3/3 公開討論会で手を挙げて「ぼくは、通学の費用が、きついと思ってて…」（第12・14話の回収）
3/10（水）13:00 未来自治体 地方大会（勝てばオンライン準決勝 → 東京の決勝）。ハルト「…カナタ、頼んだ。」
発表「私たちは、子どもだけで行ける遊び場を提案します。」→ 審査員（後ろ姿）「その政策、地域の人には、聞きましたか？」
→ 第8話の面接と同じ構図で「（…言葉が、出ない。）」→ 張り出しに「チームあそびば」がない → ハルト「…悪い。俺も、何も言えなかった。」
→「…悔しい。今までで、一番。」→ 夕方のベンチ、トケイ「悔しいのは、本気だったからなのだ。」（笑顔・決心の顔にしない）
「答え」という言葉は使わない（第17話の先取りをしない）。場面ごとに0.2秒の余韻、転換音・環境音6割、効果音7割。"""
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
import ep6 as S6
import ep9 as S9
import ep11 as S11
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep15"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED = (255, 216, 77), (255, 90, 90)
O.SPEAK["H"] = ("ハルト", (110, 200, 130))
O.SPEAK["J"] = ("審査員", (170, 172, 182))
PAD = 0.2
TEAM = "チームあそびば"

VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep15/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("K", "ぼくは、[通学の費用]が、|きついと思ってて…"),
    "02": ("H", "…カナタ、[頼んだ]。"),
    "03": ("K", "私たちは、|[子どもだけで行ける遊び場]を|提案します。"),
    "04": ("J", "その政策、[地域の人]には、|聞きましたか？"),
    "05": ("K", "（…[言葉が]、出ない。）"),
    "06": ("H", "…[悪い]。|俺も、何も言えなかった。"),
    "07": ("K", "…[悔しい]。|今までで、一番。"),
    "08": ("T", "悔しいのは、|[本気だった]からなのだ。"),
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
    S.append(O.Shot("cold", 5.0, []))                                                    # 名前が、ない。→ 2.4秒でタイトル
    ln, t = seq(["01"], 1.3)
    S.append(O.Shot("debate", t + 1.4, ln))                                              # 3/3 公開討論会
    ln, t = seq(["02"], 2.6)
    S.append(O.Shot("wings", t + 1.0, ln))                                               # 3/10 舞台そで
    ln, t = seq(["03"], 0.8)
    s = O.Shot("talk", t + 2.6, ln); s.slides = t + 0.1; S.append(s)                      # 発表 → スライド
    ln, t = seq(["04", "05"], 0.9, extra={"05": 1.6})
    s = O.Shot("q", t + 1.8, ln); s.hit = ln[0][0] + L("04") + 0.05; S.append(s)         # 審査員の質問 → 言葉が出ない
    ln, t = seq(["06", "07"], 2.4, extra={"07": 1.1})
    s = O.Shot("result", t + 2.2, ln); S.append(s)                                       # 張り出し → 悔しい
    ln, t = seq(["08"], 2.2)
    S.append(O.Shot("bench", t + 3.6, ln))                                               # 夕方のベンチ（余韻を長く）
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


# ---------- セット：大会の会場（大会名・ロゴ以外の文字は出さない） ----------
def stage_set():
    S = []
    S += P.blocks(-3, 9, -4, 10, -1, 0, hexc("#5a4a42"), 0.04, 151)          # 床
    S += P.blocks(-3, 9, 9, 10, 0, 6, hexc("#2e3446"), 0.02, 152)            # 奥の壁（暗め）
    S += P.blocks(-4, -3, -4, 10, 0, 6, hexc("#d8d2c8"), 0.02, 153)
    S += P.blocks(9, 10, -4, 10, 0, 6, hexc("#d8d2c8"), 0.02, 154)
    S.append(P.slab(-1.0, 5.2, 0, 8.0, 3.8, 0.6, hexc("#7a5a42")))           # 舞台
    S.append(P.slab(0.9, 8.85, 1.6, 4.2, 0.1, 2.6, hexc("#f4f6fa"), glow=True))  # スクリーン
    S.append(P.slab(2.65, 5.7, 0.6, 0.7, 0.5, 1.05, hexc("#4a3a30")))       # 演台
    S.append(P.slab(1.2, 1.6, 0, 3.6, 0.7, 0.72, hexc("#e8e4dc")))           # 審査員の机
    for x in (-1.5, 0.5, 2.5, 4.5, 6.5):                                       # 客席（いす）
        for y in (-1.6, -3.0):
            S.append(P.slab(x, y, 0, 0.8, 0.6, 0.45, hexc("#3a3a44")))
    return S


STAGE = stage_set()
BG_HALL = E.sky((60, 64, 80), (90, 94, 110)).convert("RGB").resize((W * G.SS, H * G.SS))
BG_EVE = E.sky((236, 140, 90), (250, 208, 160)).convert("RGB").resize((W * G.SS, H * G.SS))
KS = (3.0, 6.55, 0.6)        # 発表するカナタ（舞台、客席を向く）


def clock(img, date, time_):
    O.clock_big(img, date, time_, grade="大学1年")
    O.counter(img, 1)


def kanata(pos, yaw, expr="normal", **pose):
    r = Rig(C.KANATA_SUIT, pos, yaw, tag="kanata")
    r.set(armL=0.05, armR=0.05)
    r.set(**pose)
    r.expr = expr
    return r


def team(t, on_stage=True, haruto_expr="normal"):
    """ハルト・メンバー2人（舞台の後ろに並ぶ）"""
    out = []
    for spec, tag, x in ((C.HARUTO, "haruto", 4.6), (C.TEAM_A, "ta", 5.4), (C.TEAM_B, "tb", 6.2)):
        r = Rig(spec, (x, 7.4, 0.6) if on_stage else (x - 6.0, 6.0, 0), math.pi, tag=tag)
        r.set(armL=0.05, armR=0.05, head_pitch=0.04 * math.sin(t * 1.5 + x))
        r.expr = haruto_expr if tag == "haruto" else "normal"
        out += r.boxes()
    return out


def judges(t):
    out = []
    for i, x in enumerate((1.8, 3.0, 4.2)):
        r = Rig(C.JUDGE if i == 1 else S6.MOB[i] if hasattr(S6, "MOB") else C.JUDGE, (x, 1.25, 0), 0.0, tag=f"j{i}")
        r.set(sit=True, armL=0.5, armR=0.5)
        out += r.boxes()
    return out


def stage_img(t, cam, kexpr="normal", talk=False):
    k = kanata(KS, math.pi, kexpr, armL=0.5, armR=0.5 + (0.2 * math.sin(t * 6) if talk else 0))
    img, _ = render(STAGE + k.boxes() + team(t) + judges(t), cam, BG_HALL)
    return img.convert("RGBA")


def board(img, u, highlight=False):
    """結果の張り出し（準決勝進出チーム）。自分たちの名前はない"""
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a = int(255 * e)
    y0 = 720 + (1 - e) * 30
    d.rounded_rectangle([110, y0, W - 110, y0 + 640], radius=16, fill=(250, 250, 246, int(250 * e)), outline=(60, 64, 80, a), width=6)
    f1, f2 = O.F(BLACK, 54), O.F(BLACK, 58)
    d.text((540 - f1.getlength("準決勝 進出チーム") / 2, y0 + 36), "準決勝 進出チーム", font=f1, fill=(200, 40, 50, a))
    d.line([170, y0 + 120, W - 170, y0 + 120], fill=(60, 64, 80, a), width=4)
    for j, nm in enumerate(("チームみらい", "チームまちづくり", "チームつなぐ", "チームひろしま")):
        d.text((200, y0 + 160 + j * 112), f"{j + 1}．{nm}", font=f2, fill=(40, 40, 50, a))
    img.alpha_composite(lay)


def slide(img, u, page=0):
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a = int(255 * e)
    y0 = 720
    d.rounded_rectangle([60, y0, W - 60, y0 + 560], radius=14, fill=(250, 252, 255, int(250 * e)), outline=(40, 60, 120, a), width=8)
    d.text((100, y0 + 24), TEAM, font=O.F(BOLD, 34), fill=(90, 96, 120, a))
    if page == 0:
        for j, (ln, sz, col) in enumerate((("子どもだけで行ける", 76, (30, 50, 120)), ("遊び場", 110, (220, 90, 40)))):
            f = O.F(BLACK, sz)
            d.text((540 - f.getlength(ln) / 2, y0 + 150 + j * 140), ln, font=f, fill=col + (a,))
    else:
        f = O.F(BLACK, 60)
        for j, (ln, col) in enumerate((("交通", (255, 200, 80)), ("子育て", (120, 190, 240)), ("居場所", (120, 210, 140)))):
            x = 120 + j * 300
            d.rounded_rectangle([x, y0 + 170, x + 260, y0 + 400], radius=30, fill=col + (a,))
            d.text((x + 130 - f.getlength(ln) / 2, y0 + 250), ln, font=f, fill=(30, 30, 40, a))
    img.alpha_composite(lay)


def hook(img, t):
    if t < 2.4:
        im = E.fit_text(["名前が、ない。"], 130, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={0: RED})
        E.paste_center(img, im, 540, 1500, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["ガクチカ・ループ 第15話", "地方大会"], 96, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1500, E.pop(t - 2.4))


# ---------- 1コマ ----------
def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "cold":
        img, _ = render(S11.HALL, Camera((2.6, -1.0, 1.8), (2.6, 5.0, 1.8), 44), S11.BG_HALL)
        img = img.convert("RGBA")
        board(img, 1.0)
        clock(img, "2027年3月10日（水）", "16:00")
        hook(img, t)
    elif n == "debate":
        u = ease(t / s.dur)
        tx, ty = S6.TABLES[4]
        down = ease(min(1, max(0, t - s.lines[0][0] + 0.1) / 0.35))          # 話し始めたら、手をゆっくり下ろす
        k = S6.kanata((tx - 0.45, ty - 0.8, 0), 0.0, "resolve" if sid else "open", armR=lerp(-2.95, 0.05, down), armR_out=lerp(-0.25, 0, down))
        cam = Camera((lerp(tx - 0.2, tx - 0.25, u), lerp(ty + 2.3, ty + 2.0, u), 1.85), (tx - 0.45, ty - 0.8, 1.6), 46)
        img, _ = render(S6.HALL + S6.crowd(t, tables=S6.BACK) + k.boxes(), cam, S6.BG_HALL)
        img = img.convert("RGBA")
        clock(img, "2027年3月3日（水）", "15:00")
        S9.bigbadge(img, "公開討論会", (40, 120, 200))
    elif n == "wings":
        u = ease(t / s.dur)
        k = kanata((-0.2, 6.6, 0.6), math.pi / 2 + 0.35, "blank", armL=0.05, armR=0.05)
        h = Rig(C.HARUTO, (-1.3, 6.6, 0.6), -math.pi / 2 - 0.35, tag="haruto")
        h.set(armL=0.05, armR=0.6 if t > s.lines[0][0] else 0.05)
        cam = Camera((lerp(-0.75, -0.75, u), lerp(-0.4, 0.0, u), 2.3), (-0.75, 6.6, 1.85), 40)
        img, _ = render(STAGE + k.boxes() + h.boxes(), cam, BG_HALL)
        img = img.convert("RGBA")
        clock(img, "2027年3月10日（水）", "13:00")
        if t < s.lines[0][0] - 0.1:
            F.pill(img, "未来自治体 地方大会", 760, 60, (40, 120, 200), u=(t - 0.1) / 0.3)
            F.pill(img, "勝てば：オンライン準決勝 → 東京の決勝", 880, 44, (230, 170, 30), (20, 20, 30), u=(t - 0.5) / 0.3)
    elif n == "talk":
        u = ease(t / s.dur)
        cam = Camera((lerp(3.2, 3.15, u), lerp(1.4, 2.0, u), 1.9), (3.0, 6.6, 1.85), 44)   # 審査員の頭越しに、前で話すカナタ
        img = stage_img(t, cam, "resolve", talk=sid == "03")
        clock(img, "2027年3月10日（水）", "13:40")
        S9.bigbadge(img, "発表", (40, 120, 200))
        if t > s.slides:
            slide(img, (t - s.slides) / 0.3, 0 if t < s.slides + 1.2 else 1)
    elif n == "q":
        a, b = (x[0] for x in s.lines)
        if t < s.hit + 0.6:                             # 審査員（後ろ姿）の質問
            u = ease(t / (s.hit + 0.6))
            cam = Camera((lerp(3.55, 3.5, u), lerp(-0.5, -0.3, u), 1.9), (3.0, 6.6, 1.95), 42)
            img = stage_img(t, cam, "normal")
            if t > a:
                E.paste_center(img, E.fit_text(["地域の人には、", "聞きましたか？"], 96, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={0: YEL}),
                               540, 800, E.pop(t - a))
        else:                                           # 第8話の面接と同じ：止まるカナタの顔
            u = ease((t - s.hit - 0.6) / max(0.1, s.dur - s.hit - 0.6))
            cam = Camera((lerp(3.15, 3.1, u), lerp(3.6, 3.85, u), 2.1), (3.0, 6.55, 2.2), 44)
            img = stage_img(t, cam, "blank")
            img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 40, 50)))
        clock(img, "2027年3月10日（水）", "13:44")
    elif n == "result":
        a, b = (x[0] for x in s.lines)
        u = ease(t / s.dur)
        k = kanata((2.2, 1.4, 0), 0.0, "blank" if t < b - 0.1 else "resolve", head_pitch=0.1)
        h = Rig(C.HARUTO, (3.3, 1.4, 0), 0.0, tag="haruto")
        h.set(armL=0.05, armR=0.05, head_pitch=0.2 if t > a else 0.0)
        if t < a - 0.1:                                  # 2人の背中越しに張り出し
            cam = Camera((lerp(2.75, 2.75, u), lerp(-1.6, -1.3, u), 2.0), (2.75, 5.0, 1.9), 44)
            img, _ = render(S11.HALL + k.boxes() + h.boxes(), cam, S11.BG_HALL)
            img = img.convert("RGBA")
            board(img, (t - 0.3) / 0.3)
        else:                                            # 2人の顔（張り出しの側から）
            cam = Camera((lerp(2.75, 2.75, u), lerp(4.8, 4.6, u), 1.95), (2.75, 1.4, 1.85), 46)
            img, _ = render(S11.HALL + k.boxes() + h.boxes(), cam, S11.BG_HALL)
            img = img.convert("RGBA")
        clock(img, "2027年3月10日（水）", "16:00")
        S9.bigbadge(img, "結果発表", (110, 110, 130))
    elif n == "bench":
        u = ease(t / s.dur)
        k = Rig(C.KANATA_SUIT, (2.6, 4.3, 0), math.pi, tag="kanata")
        k.set(sit=True, armL=0.6, armR=0.6, head_pitch=0.42 if t < s.lines[0][0] + L("08") + 0.4 else 0.3)
        k.expr = "blank"
        tk = C.tokei_boxes((3.45, 4.0, 1.4), t, "eyes", 0.45, math.pi + 0.3)
        cam = Camera((lerp(2.95, 2.9, u), lerp(0.3, 0.7, u), 1.6), (2.9, 4.3, 1.05), 44)
        img, _ = render(S9.CAMPUS + k.boxes() + tk, cam, BG_EVE)
        img = img.convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 130, 60, 30)))
        img.alpha_composite(Image.new("RGBA", (W, H), (30, 20, 60, int(50 * u))))
        clock(img, "2027年3月10日（水）", "17:30")
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "本気で悔しかったこと、", 600, t, size=76)
        O.caption(img, "ある？", 730, t, size=110, col=YEL)
        for txt, y, sz, col, path in ((["コメントで教えてね"], 900, 56, (255, 255, 255), BLACK),
                                      (["次回 第16話「聞きに行く」"], 1030, 52, (255, 255, 255), BLACK),
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
