"""ガクチカ・ループ 第18話（最終回）「最後の面接」（見直し後のリメイク版台本・11/25 ゆうきさんOK）
2029/6/1（金）10:00 第1話と同じ面接室・同じ質問（第1話の面接官の声をそのまま使う）→ 1.5秒の間、秒針は止まらない →「…はい。」
答え：議員インターン／最初は面接で答えるため／議会は分からない言葉ばかり、地方大会で負けた／「地域の人には聞きましたか」→ 悔しかった／議員さんと地域へ
第8話と同じ深掘り「それで、何を考えましたか？」（第8話の声をそのまま使い、第8話で固まった画を一瞬重ねる）
→「自分の考えは、聞いてみないと、分からないんだって、思いました。」「…だから今も、分からないことは、聞きに行くようにしています。」
→ 面接官「……ありがとうございます。」（合否は見せない）→ 建物の外：トケイ「時計、止まらなかったのだ。」「もう、戻らなくていいのだ。」
→「トケイ。…ありがとう。」→「お礼なら、あの日、説明会に出た自分に言うのだ。」（第1話の声「家からなら…出て、みるか？」）→ トケイが消える
→ カナタが画面を見る「君の、力を入れたことは、何？」→ 終わり「あなたの『力を入れたこと』は、まだ作れる。」「ガクチカ・ループ 完」
時計は最後まで止めない（第1話との対比）。場面ごとに0.2秒の余韻、転換音・環境音6割、効果音7割。"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import g3d as G
from g3d import Camera, Rig, render
import characters as C
import ep1b as O
import ep1c as P
import ep3 as R
import ep4 as F
import ep9 as S9
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep18"
BLACK, BOLD = O.BLACK, O.BOLD
YEL = (255, 216, 77)
PAD = 0.2
DATE = "2029年6月1日（金）"

FLASH = {"q1": f"{HERE}/voice/ep1/01.wav", "q8": f"{HERE}/voice/ep8/01.wav", "f1": f"{HERE}/voice/ep1/10.wav"}
VO = {}


def vo(i):
    if i not in VO:
        p = FLASH.get(i, f"{HERE}/voice/ep18/{i}.wav")
        with wave.open(p) as w:
            assert w.getframerate() == SR
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "q1": ("I", "では、[学生時代に力を入れたこと]を、|教えてください。"),
    "02": ("K", "…はい。"),
    "03": ("K", "大学1年の春、|[議員インターン]をしました。"),
    "04": ("K", "…最初は、|[面接で答えるため]に、行きました。"),
    "05": ("K", "議会は、分からない言葉ばかりで。|政策コンテストの地方大会では、|[負けました]。"),
    "06": ("K", "『地域の人には聞きましたか』と|聞かれて、何も言えなくて…|[悔しかった]です。"),
    "07": ("K", "それで、議員さんと一緒に、|地域の人に[話を聞きに]行きました。"),
    "q8": ("I", "それで、|[何を考えましたか]？"),
    "09": ("K", "自分の考えは、[聞いてみないと]、|分からないんだって、思いました。"),
    "10": ("K", "道が危ないことも、|見守る大人が減ったことも、|[地図の上]では、分からなかったので。"),
    "11": ("K", "…だから今も、分からないことは、|[聞きに行く]ようにしています。"),
    "12": ("I", "……[ありがとうございます]。"),
    "13": ("T", "時計、[止まらなかった]のだ。"),
    "14": ("K", "…うん。"),
    "15": ("T", "もう、[戻らなくていい]のだ。"),
    "16": ("K", "トケイ。…[ありがとう]。"),
    "17": ("T", "お礼なら、あの日、|[説明会に出た自分]に言うのだ。"),
    "18": ("K", "君の『[力を入れたこと]』は、|何？"),
}
NOSUB_IDS = {"f1"}                 # 第1話の画は、第1話の字幕のまま


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


def at(s, i):
    return next(t0 for t0, j in s.lines if j == i)


# 前の話の画（ep1b の interview、ep8 の iv）から使う区間（各話の場面内の秒）
L1 = (2.75, 6.95)          # 第1話：「…教えてください。」→「…え、っと……」→ 止まる
L2A = (7.95, 10.95)        # 第8話：「それで、何を考えましたか？」
L2B = (21.45, 23.45)       # 第8話：沈黙 → 止まる
RW_DUR = [0.62 * 0.87 ** k for k in range(17)]   # 巻き戻し：だんだん速く（第17話→第1話）


def plan():
    S = []
    S.append(O.Shot("rewind", 5.0, []))                                  # 第17話→第1話を巻き戻す「3回、やり直した。」
    S.append(O.Shot("loop1", L1[1] - L1[0], []))                          # 1回目（第1話）：同じ質問で止まる
    S.append(O.Shot("loop2", (L2A[1] - L2A[0]) + (L2B[1] - L2B[0]), []))  # 2回目（第8話）：深掘りで止まる
    S.append(O.Shot("cold", 4.0, []))                                     # 3回目 → タイトル
    ln, t = seq(["q1", "02"], 0.6, extra={"02": 2.6})                     # 同じ質問 → 秒針は止まらない →「…はい。」
    s = O.Shot("q", t + 0.6, ln); s.wait = ln[0][0] + L("q1") + 0.3; S.append(s)
    ln, t = seq(["03", "04", "05", "06", "07"], 0.5, extra={"04": 0.5, "05": 0.6, "06": 0.6, "07": 0.6})
    S.append(O.Shot("answer", t + 0.6, ln))
    ln, t = seq(["q8", "09", "10", "11"], 0.5, extra={"09": 2.3, "10": 0.5, "11": 0.9})
    s = O.Shot("deep", t + 1.0, ln); s.fb = ln[0][0] + L("q8") + 0.2; S.append(s)   # 第8話の画を一瞬
    ln, t = seq(["12"], 0.8)
    S.append(O.Shot("thanks", t + 2.0, ln))                                 # 礼 → チャイム
    ln, t = seq(["13", "14", "15", "16", "17", "f1"], 1.4, extra={"14": 0.5, "15": 0.9, "16": 1.0, "17": 0.8, "f1": 0.5})
    s = O.Shot("outside", t + 2.6, ln); s.vanish = t + 0.2; S.append(s)      # トケイが消える
    ln, t = seq(["18"], 1.6)
    s = O.Shot("look", t + 1.8, ln); s.hit = ln[0][0] + L("18") + 0.05; S.append(s)
    S.append(O.Shot("end", 8.0))
    S.append(O.Shot("invite", 7.0))                                       # 最後の案内（カナタとハルト）
    t = 0
    for s in S:
        s.dur += PAD
        n = int(round(s.dur * FPS)); s.start, s.dur = t, n / FPS; t += s.dur
    return S


SH = plan()
QSTART = next(s for s in SH if s.name == "q").start          # 時計の 10:00:00（ここから止まらずに進む）


def shot(name):
    return next(s for s in SH if s.name == name)


def speaking(s, t):
    cur = None
    for (t0, sid) in s.lines:
        if t0 <= t <= t0 + L(sid) + 0.15:
            cur = sid
    return cur


# ---------- 面接室（第1・8話と同じ） ----------
def iv_img(t, kexpr, cam_mode, u, iv_expr="normal", iv_talk=False, head=0.0, bow=0.0, tk=()):
    iv, k = P.iv_rig(), P.kanata_suit_rig()
    k.expr = kexpr
    k.set(head_yaw=head, head_pitch=0.35 * bow, lean=0.25 * bow)
    iv.expr = iv_expr
    if iv_talk:
        iv.set(armL=0.55 + 0.25 * math.sin(t * 7))
    if cam_mode == "ivfast":                       # 「何を考えましたか？」：少し速く寄る
        cam = Camera((lerp(3.75, 3.35, u), lerp(0.55, 2.5, u), lerp(1.62, 1.55, u)), (3.0, 5.5, lerp(1.38, 1.5, u)), lerp(48, 40, u))
    elif cam_mode == "iv":
        cam = Camera((lerp(3.75, 3.6, u), lerp(0.55, 1.0, u), 1.62), (3.0, 5.5, 1.38), 48)
    elif cam_mode == "k":
        cam = Camera((lerp(3.42, 3.36, u), lerp(4.25, 4.0, u), 1.52), (3.0, 2.1, 1.42), 44)
    elif cam_mode == "close":
        cam = Camera((lerp(3.35, 3.2, u), lerp(4.1, 3.65, u), 1.5), (3.0, 2.1, 1.44), lerp(44, 42, u))
    else:   # 2人（カナタの斜め後ろから、面接官まで）
        cam = Camera((lerp(4.3, 4.2, u), lerp(-0.5, -0.1, u), 2.5), (3.0, 4.6, 1.15), 52)
    img, _ = render(P.OFFICE + iv.boxes() + k.boxes() + list(tk), cam, P.BG_OFFICE)
    return img.convert("RGBA")


def gclock(img, s, t, loop=True, alpha=1.0):
    """面接が始まってからの時間で、時計を進める（止まらない）。建物の外は面接の約20分後"""
    g = max(0.0, s.start + t - QSTART) + (19 * 60 if s.name in ("outside", "look") else 0)
    sec = int(g)
    O.clock_big(img, DATE, f"10:{sec // 60:02d}:{sec % 60:02d}", grade="大学4年")
    if loop:
        O.counter(img, 1)


_RW = {}


def rw_still(n):
    if n not in _RW:
        _RW[n] = Image.open(f"{OUT}/rw/{n:02d}.png").convert("RGB").resize((W, H))
    return _RW[n]


def loop_tag(img, text, t):
    """左上の「1回目／2回目／3回目」"""
    a = min(1, t / 0.25)
    d = ImageDraw.Draw(img)
    f = O.F(BLACK, 54)
    w = f.getlength(text) + 60
    d.rounded_rectangle([540 - w / 2, 1690, 540 + w / 2, 1780], radius=20, fill=(200, 50, 50, int(235 * a)) if text != "3回目" else (40, 140, 90, int(235 * a)))
    d.text((540 - w / 2 + 30, 1702), text, font=f, fill=(255, 255, 255, int(255 * a)))


def hook(img, t):
    if t < 1.6:
        im = E.fit_text(["最後の、面接。"], 130, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={0: YEL})
        E.paste_center(img, im, 540, 1450, E.pop(t))
    elif t < 4.6:
        im = E.fit_text(["ガクチカ・ループ 第18話", "最後の面接"], 96, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1450, E.pop(t - 1.6))


def flash_img(src, label):
    im = src.convert("RGB")
    im = Image.blend(im, im.convert("L").convert("RGB"), 0.55)
    im = Image.blend(im, Image.new("RGB", (W, H), (120, 96, 60)), 0.18).convert("RGBA")
    F.pill(im, label, 1700, 48, (90, 80, 70))
    return im


def flash_src(key, t):
    if key == "q8":
        import ep8 as V8
        s = next(x for x in V8.SH if x.name == "iv")
        f_ = s.lines[5][0]
        return V8.frame(s, f_ + 0.4 + t * 0.5)
    s = next(x for x in P.SH if x.name == "phone")
    return P.frame(s, 0.3 + min(t, O.L("10") - 0.05))


def kanata_out(expr, yaw=math.pi, **pose):
    r = Rig(C.KANATA_SUIT, (2.5, 3.4, 0), yaw, tag="kanata")
    r.set(armL=0.05, armR=0.05)
    r.set(**pose)
    r.expr = expr
    return r


def name_pills(img, t):
    a = max(0.0, min(1.0, (t - 0.7) / 0.3))
    if a <= 0:
        return
    d = ImageDraw.Draw(img)
    f = O.F(BLACK, 50)
    for txt, x, col in (("議員インターン", 300, (40, 120, 200)), ("NPOインターン", 780, (40, 150, 90))):
        w = f.getlength(txt) + 56
        d.rounded_rectangle([x - w / 2, 1270, x + w / 2, 1350], radius=40, fill=col + (int(245 * a),))
        d.text((x - w / 2 + 28, 1280), txt, font=f, fill=(255, 255, 255, int(255 * a)))


# ---------- 1コマ ----------
def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    u = ease(t / s.dur)
    if n == "rewind":                                     # 巻き戻し：第17話 → 第1話
        acc, k = 0.0, 0
        while k < 16 and t >= acc + RW_DUR[k]:
            acc += RW_DUR[k]; k += 1
        ep = 17 - k
        v = (t - acc) / RW_DUR[k]
        im = rw_still(ep)
        z = 1.06 - 0.06 * v                                 # 逆再生のように少しずつ引く
        w2, h2 = int(W * z), int(H * z)
        im = im.resize((w2, h2)).crop(((w2 - W) // 2, (h2 - H) // 2, (w2 - W) // 2 + W, (h2 - H) // 2 + H))
        img = O.glitch(im.convert("RGBA"), 0.35, int(t * 30))
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 70)))
        d = ImageDraw.Draw(img)
        y = int((t * 900) % H)                              # テープのノイズの線
        d.rectangle([0, y, W, y + 14], fill=(255, 255, 255, 60))
        F.pill(img, f"◀◀ 第{ep}話", 1700, 52, (30, 30, 40))
        im2 = E.fit_text(["3回、", "やり直した。"], 130, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=14, hl={1: YEL})
        E.paste_center(img, im2, 540, 1020, E.pop(t))
    elif n in ("loop1", "loop2"):
        if n == "loop1":
            src = next(x for x in P.SH if x.name == "interview")   # 投稿した第1話（寄りのカメラ版）
            img = P.frame(src, L1[0] + t).convert("RGBA")
            lab = "1回目"
        else:
            import ep8 as V8
            src = next(x for x in V8.SH if x.name == "iv")
            a = L2A[1] - L2A[0]
            tt = L2A[0] + t if t < a else L2B[0] + (t - a)
            img = V8.frame(src, tt).convert("RGBA")
            lab = "2回目"
            if a - 0.05 < t < a + 0.12:                     # つなぎ目：ノイズで飛ばす
                img = O.glitch(img, 0.5, int(t * 30))
        loop_tag(img, lab, t)
    elif n == "cold":                                     # 3回目：第1話と同じ構図の面接室
        img = iv_img(t, "normal", "two", u)
        O.clock_big(img, DATE, "10:00:00", grade="大学4年")
        O.counter(img, 1)
        hook(img, t)
        loop_tag(img, "3回目", t)
    elif n == "q":
        if t < s.wait:                                    # 面接官：同じ質問
            img = iv_img(t, "normal", "iv", ease(t / s.wait), iv_talk=sid == "q1")
        else:                                             # 間：時計を見る → 秒針は止まらない
            v = (t - s.wait) / (s.dur - s.wait)
            look = ease(min(1, max(0, (t - s.wait - 0.3) / 0.5))) * (1 - ease(min(1, max(0, (t - s.wait - 1.6) / 0.5))))
            img = iv_img(t, "open" if t < at(s, "02") - 0.3 else "resolve", "k", ease(v), head=0.45 * look)
            if s.wait + 0.8 < t < at(s, "02") - 0.1:
                O.caption(img, "…秒針が、動いてる。", 1500, t - s.wait - 0.8, size=84, col=YEL)
        gclock(img, s, t)
    elif n == "answer":                                   # 答える：顔にゆっくり寄る
        img = iv_img(t, "normal" if sid != "06" else "resolve", "close", u * 0.75)
        gclock(img, s, t)
    elif n == "deep":
        t9 = at(s, "09")
        if t < s.fb - 0.1:                                # 第8話と同じ深掘り
            img = iv_img(t, "normal", "ivfast", ease(min(1, t / (at(s, "q8") + L("q8")))), iv_talk=sid == "q8")
        else:
            v = ease((t - s.fb) / (s.dur - s.fb))
            img = iv_img(t, "smile" if s.fb + 1.0 < t < t9 + 0.2 else "resolve", "k", v)
            if s.fb - 0.1 < t < s.fb + 0.9:               # 一瞬、第8話で固まったカナタ
                a = min(1, (t - s.fb + 0.1) / 0.15, (s.fb + 0.9 - t) / 0.2)
                img = Image.blend(img, flash_img(flash_src("q8", t - s.fb), "2回目のループ"), max(0, a))
        gclock(img, s, t)
    elif n == "thanks":
        t12 = at(s, "12")
        bow = ease(min(1, max(0, (t - t12 - L("12") - 0.2) / 0.5))) * (1 - ease(min(1, max(0, (t - t12 - L("12") - 1.3) / 0.5))))
        img = iv_img(t, "smile", "two", u, iv_expr="smile", iv_talk=sid == "12", bow=bow)
        gclock(img, s, t)
    elif n == "outside":                                  # 建物の外：トケイとの別れ
        vt = t - s.vanish
        sc = 0.5 * (1 - ease(min(1, max(0, vt) / 0.8)))
        tk = []
        if sc > 0.01:
            drop = (1 - ease(min(1, max(0, t - at(s, "13") + 0.9) / 0.5))) * 1.4
            tk = C.tokei_boxes((3.2, 3.05, 1.85 + drop + max(0, vt) * 0.5), t, "eyes", sc, math.pi + 0.45) if t > at(s, "13") - 0.9 else []
        k = kanata_out("smile" if t > at(s, "16") else "normal", math.pi - 0.35, head_yaw=-0.25)
        cam = Camera((lerp(2.95, 2.9, u), lerp(0.2, 0.6, u), 1.75), (2.75, 4.2, 1.7), 50)
        img, _ = render(R.OUTSIDE + k.boxes() + list(tk), cam, R.BG_SKY)
        img = img.convert("RGBA")
        if 0 < vt < 1.2:                                  # きらめき
            d = ImageDraw.Draw(img)
            for j in range(14):
                ang = j * 0.9 + vt * 2
                rr = 60 + vt * 260 + (j % 3) * 30
                x, y = 760 + math.cos(ang) * rr, 820 + math.sin(ang) * rr * 0.8 - vt * 120
                a = int(255 * (1 - vt / 1.2))
                d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(255, 236, 140, a))
        gclock(img, s, t, loop=t < at(s, "15") + L("15") + 0.3)
        tf = at(s, "f1")
        if tf - 0.3 < t < tf + L("f1") + 0.3:
            a = min(1, (t - tf + 0.3) / 0.25, (tf + L("f1") + 0.3 - t) / 0.25)
            img = Image.blend(img, flash_img(flash_src("f1", t - tf), "第1話　大学1年の12月"), max(0, a))
    elif n == "look":                                     # カナタが画面を見る
        k = kanata_out("normal" if t < s.lines[0][0] else "smile")
        cam = Camera((2.5, lerp(0.95, 1.2, u), 1.72), (2.5, 3.4, 1.6), 40)
        img, _ = render(R.OUTSIDE + k.boxes(), cam, R.BG_SKY)
        img = img.convert("RGBA")
        if t > s.hit:
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(150 * max(0, 1 - (t - s.hit) / 0.8)))))
        gclock(img, s, t, loop=False)
    elif n == "end":
        k = kanata_out("smile")
        bg, _ = render(R.OUTSIDE + k.boxes(), Camera((2.5, 1.6, 1.72), (2.5, 3.4, 1.72), 40), R.BG_SKY)
        img = bg.convert("RGBA").filter(ImageFilter.GaussianBlur(12))
        img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 40, 150)))
        O.caption(img, "あなたの『力を入れたこと』は、", 560, t, size=72)
        O.caption(img, "まだ作れる。", 690, t - 0.3, size=130, col=YEL)
        for txt, y, sz, col, path, d0 in ((["ガクチカ・ループ　完"], 880, 64, (255, 255, 255), BLACK, 1.2),
                                          (["ドットジェイピー広島第一支部", "春インターン（2月1日〜3月31日）", "申込は12月31日まで"], 1070, 50, YEL, BLACK, 1.6),
                                          (["この動画は「勇気を出して一歩を踏み出そう」という", "メッセージを伝えるための創作ドラマです", "インターンの内容は受け入れ先によって異なります"], 1290, 32, (220, 226, 245), BOLD, 1.8)):
            E.paste_center(img, E.fit_text(txt, sz, 1000, fill=col, sw=6, path=path), 540, y, E.pop(t - d0))
    elif n == "invite":                                   # 最後の案内：カナタとハルト
        k = kanata_out("smile")
        k.pos = (1.85, 3.4, 0)
        h = Rig(C.HARUTO, (3.25, 3.4, 0), math.pi, tag="haruto")
        h.set(armL=0.05, armR=0.05)
        h.expr = "smile"
        u2 = ease(min(1, t / 6.5))
        bg, _ = render(R.OUTSIDE + k.boxes() + h.boxes(), Camera((2.55, lerp(-2.6, -2.3, u2), 1.9), (2.55, 3.4, 1.7), 44), R.BG_SKY)
        img = bg.convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 40, 70)))
        E.paste_center(img, E.fit_text(["最後まで見てくれて、", "ありがとうございました。"], 60, 1000, fill=(255, 255, 255), sw=8, path=BLACK), 540, 560, E.pop(t))
        for txt, x, col in (("カナタが参加した", 300, (40, 120, 200)), ("ハルトが参加した", 780, (40, 150, 90))):
            E.paste_center(img, E.fit_text([txt], 36, 440, fill=(255, 255, 255), sw=6, path=BOLD), x, 1235, E.pop(t - 0.6))
        name_pills(img, t)
        E.paste_center(img, E.fit_text(["どちらも", "12月31日まで募集中"], 76, 1000, fill=YEL, sw=8, path=BLACK, hl={0: (255, 255, 255)}), 540, 1520, E.pop(t - 1.4))
        E.paste_center(img, E.fit_text(["気になった人は、DMで気軽に聞いてね"], 50, 1000, fill=(255, 255, 255), sw=6, path=BLACK), 540, 1700, E.pop(t - 2.0))
    if sid and sid not in NOSUB_IDS:
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
    if sys.argv[1] == "plan":
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
