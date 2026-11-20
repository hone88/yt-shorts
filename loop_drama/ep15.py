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
import ep3 as R
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
    "09": ("K", "（…今日は、|[未来自治体]の地方大会。）"),
    "10": ("T", "ここまで来たのは、|[初めて]なのだ。"),
    "11": ("K", "…1回目は、[布団から]出られなかった。|2回目は、来ても、|[何も考えてなかった]。"),
    "12": ("A", "スライド、最後に|[もう一回]見よう。"),
    "13": ("H", "…NPOでさ、放課後に|子どもと遊んでて、思ったんだ。|『行きたいけど、[遠い]』って|言う子が、多くて。"),
    "14": ("K", "…議員さんの事務所でも、|[通学]の話、聞いたな。|森下さん、『それを、|聞きたかったんだ』って。"),
    "15": ("B", "…交通も、子育ても、居場所も。|[ちゃんと]つながってる。"),
    "16": ("K", "…うん。"),
    "17": ("K", "30年後、広島の子どもが、|[自分の足で]遊びに行ける街に。"),
    "18": ("H", "あ、NPOで、|子どもたちには…"),
    "19": ("J", "子どもたち[以外の]、|地域の方には？"),
    "20": ("A", "…あの質問、|[何も]返せなかったね。"),
    "21": ("K", "…1回目も、2回目も、|[悔しくなかった]。|…何も、してなかったから。"),
}
O.SPEAK["A"] = ("メンバー", (200, 150, 230))
O.SPEAK["B"] = ("メンバー", (120, 190, 240))


def subtitle(img, sid):
    who, text = TEXT[sid]
    name, col = O.SPEAK[who]
    lines = text.split("|")
    d = ImageDraw.Draw(img)
    f, fn = O.F(BLACK, 72), O.F(BLACK, 40)
    y = 1450 - (len(lines) - 1) * 60
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


def V_L(i):
    return L(i)


def plan():
    S = []
    S.append(O.Shot("cold", 5.0, []))                                                    # 名前が、ない。→ 2.4秒でタイトル
    ln, t = seq(["01"], 1.3)
    S.append(O.Shot("debate", t + 1.4, ln))                                              # 3/3 公開討論会
    ln, t = seq(["09", "10", "11"], 2.2, extra={"10": 1.0, "11": 0.4})
    S.append(O.Shot("gate", t + 1.2, ln))                                               # 9:30 会場の入口（カナタとトケイ）
    ln, t = seq(["12", "13", "14", "15", "02", "16"], 0.6, extra={"13": 0.3, "14": 0.5, "15": 0.4, "02": 1.0, "16": 0.3})
    S.append(O.Shot("green", t + 1.0, ln))                                              # 10:30 控え室（4人）
    ln, t = seq(["03", "17"], 0.8, extra={"17": 1.2})
    s = O.Shot("talk", t + 1.2, ln); s.slides = ln[0][0] + V_L("03") + 0.1; S.append(s)   # 13:30 発表
    ln, t = seq(["04", "18", "19", "05"], 0.9, extra={"18": 0.6, "19": 0.2, "05": 1.6})
    s = O.Shot("q", t + 2.2, ln); s.hit = ln[0][0] + V_L("04") + 0.05; S.append(s)       # 審査員の質問 → 言葉が出ない
    ln, t = seq(["20", "06", "07"], 2.4, extra={"06": 0.3, "07": 1.5})
    s = O.Shot("result", t + 2.2, ln); S.append(s)                                      # 16:00 張り出し → 悔しい
    ln, t = seq(["21", "08"], 2.2, extra={"08": 1.5})
    S.append(O.Shot("bench", t + 3.8, ln))                                              # 17:30 夕方のベンチ（余韻を長く）
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
    elif n == "gate":                                    # 会場の入口（カナタとトケイだけ）
        u = ease(t / s.dur)
        a, b, c = (x[0] for x in s.lines)
        k = kanata((2.5, 3.6, 0), math.pi, "normal" if t < c else "blank", head_pitch=-0.05)
        tk = Q.tokei_near(t, "eyes", t - b + 0.6, (3.25, 3.3, 1.75)) if t > b - 0.6 else []
        cam = Camera((lerp(3.1, 2.95, u), lerp(-0.6, 0.0, u), 1.75), (2.7, 4.6, 1.55), 50)
        img, _ = render(R.OUTSIDE + k.boxes() + list(tk), cam, R.BG_SKY)
        img = img.convert("RGBA")
        clock(img, "2027年3月10日（水）", "9:30")
        if t < a + L("09") + 0.3:
            F.pill(img, "未来自治体 地方大会", 760, 60, (40, 120, 200), u=(t - 0.2) / 0.3)
            F.pill(img, "勝てば：オンライン準決勝 → 東京の決勝", 880, 44, (230, 170, 30), (20, 20, 30), u=(t - 0.6) / 0.3)
    elif n == "green":                                   # 控え室：4人（話し手が変わるときだけ切り替え）
        u = ease(t / s.dur)
        last = None
        for (t0, i) in s.lines:
            if t >= t0 - 0.1:
                last = i
        t02 = [x for x, i in s.lines if i == "02"][0]
        k = R.kanata_seat("resolve" if t > t02 else "normal")
        k.spec = C.KANATA_SUIT
        h = Rig(C.HARUTO, (3.0, 5.5, 0), math.pi, tag="haruto")
        h.set(sit=True, armL=0.55, armR=0.55 + (0.5 if t02 - 0.2 < t < t02 + 1.2 else 0))
        h.expr = "smile" if last in ("02", "16") else "normal"
        ra = Rig(C.TEAM_A, (1.55, 3.8, 0), -math.pi / 2, tag="ta"); ra.set(sit=True, armL=0.5, armR=0.5)
        rb = Rig(C.TEAM_B, (4.45, 3.8, 0), math.pi / 2, tag="tb"); rb.set(sit=True, armL=0.5, armR=0.5)
        rb.expr = "smile" if last == "15" else "normal"
        if last in ("13", "02"):                         # カナタの背中越しにハルト
            cam = R.cam_mio(t, s.dur)
        elif last in ("14", "16"):                       # ハルトの側からカナタ
            cam = R.cam_kanata(t, s.dur)
        else:                                            # 4人（上から少し引いて）
            cam = Camera((lerp(5.6, 5.5, u), lerp(-1.6, -1.3, u), 3.7), (3.0, 3.8, 0.8), 46)
        img, _ = render(R.MEET + k.boxes() + h.boxes() + ra.boxes() + rb.boxes(), cam, R.BG_MEET)
        img = img.convert("RGBA")
        clock(img, "2027年3月10日（水）", "10:30")
        S9.bigbadge(img, "控え室", (110, 110, 130))
    elif n == "talk":
        u = ease(t / s.dur)
        cam = Camera((lerp(3.2, 3.15, u), lerp(1.4, 2.0, u), 1.9), (3.0, 6.6, 1.85), 44)   # 審査員の頭越しに、前で話すカナタ
        img = stage_img(t, cam, "resolve", talk=sid in ("03", "17"))
        clock(img, "2027年3月10日（水）", "13:30")
        S9.bigbadge(img, "発表", (40, 120, 200))
        if s.slides < t < s.lines[1][0] - 0.2:
            slide(img, (t - s.slides) / 0.3, 0 if t < s.slides + 1.3 else 1)
    elif n == "q":
        a, b, c, d_ = (x[0] for x in s.lines)
        if t < b - 0.1 or c - 0.1 <= t < c + L("19") + 0.3:   # 審査員（後ろ姿）の質問
            u = ease(t / s.dur)
            cam = Camera((lerp(3.55, 3.5, u), lerp(-0.5, -0.3, u), 1.9), (3.0, 6.6, 1.95), 42)
            img = stage_img(t, cam, "normal" if t < b else "blank")
            if a < t < b - 0.1:
                E.paste_center(img, E.fit_text(["地域の人には、", "聞きましたか？"], 96, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={0: YEL}),
                               540, 800, E.pop(t - a))
            if t >= c - 0.1:
                E.paste_center(img, E.fit_text(["子どもたち以外の、", "地域の方には？"], 90, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={0: YEL}),
                               540, 800, E.pop(t - c + 0.1))
        elif t < c - 0.1:                                  # あわてて答えるハルト（舞台の後ろ）
            u = ease((t - b) / max(0.1, c - b))
            cam = Camera((lerp(4.3, 4.35, u), lerp(3.4, 3.6, u), 2.2), (4.6, 7.4, 2.25), 44)
            img = stage_img(t, cam, "blank")
        else:                                              # 第8話の面接と同じ：止まるカナタの顔
            u = ease((t - c - L("19") - 0.3) / max(0.1, s.dur - c - L("19") - 0.3))
            cam = Camera((lerp(3.15, 3.1, u), lerp(3.6, 3.85, u), 2.1), (3.0, 6.55, 2.2), 44)
            img = stage_img(t, cam, "blank")
            img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 40, 50)))
        clock(img, "2027年3月10日（水）", "13:44")
    elif n == "result":
        a, b, c = (x[0] for x in s.lines)
        u = ease(t / s.dur)
        k = kanata((2.35, 1.4, 0), 0.0, "blank" if t < c - 0.1 else "resolve", head_pitch=0.1)
        h = Rig(C.HARUTO, (3.2, 1.4, 0), 0.0, tag="haruto")
        h.set(armL=0.05, armR=0.05, head_pitch=0.2 if t > b else 0.0)
        ra = Rig(C.TEAM_A, (1.65, 0.9, 0), 0.0, tag="ta"); ra.set(armL=0.05, armR=0.05, head_pitch=0.15 if t > a else 0)
        rb = Rig(C.TEAM_B, (3.9, 0.9, 0), 0.0, tag="tb"); rb.set(armL=0.05, armR=0.05, head_pitch=0.15)
        people = k.boxes() + h.boxes() + ra.boxes() + rb.boxes()
        if t < a - 0.1:                                  # 4人の背中越しに張り出し
            cam = Camera((lerp(2.75, 2.75, u), lerp(-1.9, -1.6, u), 2.0), (2.75, 5.0, 1.9), 44)
            img, _ = render(S11.HALL + people, cam, S11.BG_HALL)
            img = img.convert("RGBA")
            board(img, (t - 0.3) / 0.3)
        else:                                            # 4人の顔（張り出しの側から）
            cam = Camera((lerp(2.75, 2.75, u), lerp(4.85, 4.7, u), 1.9), (2.75, 1.5, 1.6), 64)
            img, _ = render(S11.HALL + people, cam, S11.BG_HALL)
            img = img.convert("RGBA")
        clock(img, "2027年3月10日（水）", "16:00")
        S9.bigbadge(img, "結果発表", (110, 110, 130))
    elif n == "bench":
        u = ease(t / s.dur)
        a, b = (x[0] for x in s.lines)
        k = Rig(C.KANATA_SUIT, (2.6, 4.3, 0), math.pi, tag="kanata")
        k.set(sit=True, armL=0.6, armR=0.6, head_pitch=lerp(0.42, 0.32, ease(min(1, max(0, t - b - L("08")) / 1.0))))
        k.expr = "blank"
        tk = C.tokei_boxes((3.45, 4.0, 1.4 + (1 - ease(min(1, max(0, t - b + 0.8) / 0.5))) * 1.2), t, "eyes", 0.45, math.pi + 0.3) if t > b - 0.8 else []
        cam = Camera((lerp(2.95, 2.9, u), lerp(0.3, 0.7, u), 1.6), (2.9, 4.3, 1.05), 44)
        img, _ = render(S9.CAMPUS + k.boxes() + list(tk), cam, BG_EVE)
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
                                      (["この動画は「勇気を出して一歩を踏み出そう」という", "メッセージを伝えるための創作ドラマです"], 1340, 32, (220, 226, 245), BOLD),
                                      (["※実際の未来自治体では、NPOインターンと議員インターンの参加者が", "同じチームになることはありません。", "同じ活動先ごとのチーム（例：森下議員事務所チーム）で出場します"], 1460, 28, (220, 226, 245), BOLD)):
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
