"""ガクチカ・ループ 第8話「それで、何を考えましたか？」
2周目のカナタは2月〜3月、言われた活動には行く。でも任意のイベントの通知は既読だけで、議会も「まあ、いっか」。
3月31日の夜が終わると面接の日へ（ルール④）。「議員インターンをしました」は言えるが、
「それで、何を考えましたか？」で答えられない。世界が止まり、残りループ 2→1。
python3 ep8.py still <shot> <t> | python3 ep8.py build"""
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
import case1 as K1
import ep7 as S7
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep8"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED = (255, 216, 77), (255, 90, 90)

# ---------- 声 ----------
VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep8/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("I", "それで、|[何を考えましたか]？"),
    "02": ("K", "…行ってるし、|これで[答えられる]。"),
    "03": ("T", "[時間]なのだ。"),
    "04": ("K", "[議員インターン]を、|しました。"),
    "05": ("I", "[具体的]には？"),
    "06": ("K", "あいさつ回りをしたり、|議会を見たり……。"),
    "08": ("T", "[経験しただけ]では、|答えにならないのだ。|残り、[1回]なのだ。"),
    "09": ("K", "待って…|[まだ]…！"),
    "10": ("K", "（…よく分からんけど、|[まあ、いっか]。）"),
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
    S.append(O.Shot("cold", max(t + 0.3, 4.5), ln))                      # つかみ → 2.4秒でタイトル
    ln, t = seq(["10"], 0.9)
    S.append(O.Shot("council", t + 0.3, ln))                             # 2月 議会傍聴
    S.append(O.Shot("notice1", 2.6))                                     # 任意イベントの通知 → 既読だけ
    S.append(O.Shot("event", 2.4))                                       # 3月 地域イベント
    ln, t = seq(["02"], 1.3)
    S.append(O.Shot("notice2", t + 0.4, ln))                             # また既読。「これで答えられる」
    ln, t = seq(["03"], 3.4)
    s = O.Shot("midnight", t + 0.8, ln); s.zero = 1.4; S.append(s)        # 23:59 → 0:00、ルール④
    ln, t = seq(["04", "05", "06", "01"], 0.5, extra={"05": 0.2, "06": 0.2, "01": 0.5})
    s = O.Shot("iv", t + 1.0 + 0.6, ln); s.tf = t + 1.0; S.append(s)      # 1秒止めて → 世界が止まる
    ln, t = seq(["08"], 1.4)
    s = O.Shot("freeze", t + 0.8, ln); S.append(s)                        # 残りループ 2→1、トケイ
    ln, t = seq(["09"], 0.3)
    s = O.Shot("rewind", t + 2.2, ln); s.t0 = t; S.append(s)              # 2029 → 2026
    S.append(O.Shot("end", 5.0))
    t = 0
    for s in S:
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


# ---------- 人物・セット ----------
def phone_parts(e="normal"):
    return C.kanata_parts(e, "suit") + [dict(bone="armR", off=(-0.12, 0.08, -0.66), size=(0.16, 0.03, 0.26), color=hexc("#1a1c24"))]


KANATA_PHONE_SUIT = dict(name="kanata", label="カナタ（スマホ）", parts=phone_parts)


def kanata_phone(pos, yaw, expr="normal", **pose):
    r = Rig(KANATA_PHONE_SUIT, pos, yaw, tag="kanata")
    r.set(armL=0.05, armR=1.0, head_pitch=0.3)
    r.set(**pose)
    r.expr = expr
    return r


def council_set():
    """議場（政党を思わせる色・旗・ロゴは出さない）"""
    S = []
    S += P.blocks(-2, 8, -3, 10, -1, 0, hexc("#7a2e2e"), 0.03, 81)          # じゅうたん
    S += P.blocks(-2, 8, 10, 11, 0, 5, hexc("#d8ccb8"), 0.02, 82)           # 奥の壁
    S += P.blocks(-3, -2, -3, 11, 0, 5, hexc("#d8ccb8"), 0.02, 83)
    S += P.blocks(8, 9, -3, 11, 0, 5, hexc("#d8ccb8"), 0.02, 84)
    S.append(P.slab(1.0, 8.6, 0, 4.0, 1.2, 0.9, hexc("#6a4a30")))           # 議長席の台
    S.append(P.slab(1.6, 8.9, 0.9, 2.8, 0.6, 0.5, hexc("#5a3c26")))
    S.append(P.slab(2.6, 7.6, 0, 0.8, 0.6, 1.1, hexc("#5a3c26")))           # 演台
    for r_ in range(3):                                                     # 議員席の机
        y = 4.2 + r_ * 1.1
        S.append(P.slab(-1.0 + r_ * 0.3, y, 0, 7.4 - r_ * 0.6, 0.45, 0.75, hexc("#7a5a42")))
    S.append(P.slab(-1.5, 1.2, 0, 9.0, 0.5, 0.95, hexc("#5a3c26")))         # 傍聴席の手すり
    S.append(P.slab(-1.5, -0.6, 0, 9.0, 1.4, 0.45, hexc("#4a4a52")))        # 傍聴席のいす
    return S


COUNCIL = council_set()
BG_COUNCIL = E.sky((214, 204, 186), (236, 228, 214)).convert("RGB").resize((W * G.SS, H * G.SS))


def members(t):
    out = []
    for i, (x, y) in enumerate([(0.2, 4.9), (1.6, 4.9), (3.4, 4.9), (4.8, 4.9), (0.8, 6.0), (2.6, 6.0), (4.2, 6.0)]):
        r = Rig(S7.OTHER if i % 3 else C.MORISHITA, (x, y, 0), math.pi, tag=f"m{i}")
        r.set(sit=True, armL=0.5, armR=0.5, head_pitch=0.05 * math.sin(t * 2 + i))
        out += r.boxes()
    sp = Rig(S7.OTHER, (3.0, 8.0, 0), math.pi, tag="sp")                 # 演台で話す人
    sp.set(armL=0.6 + 0.2 * math.sin(t * 6), armR=0.3)
    return out + sp.boxes()


def tents():
    S = []
    for x in (0.2, 3.6):
        S.append(P.slab(x, 4.6, 2.0, 2.0, 1.6, 0.12, hexc("#f4f4f4")))
        for dx in (0.05, 1.85):
            for dy in (0.05, 1.45):
                S.append(P.slab(x + dx, 4.6 + dy, 0, 0.1, 0.1, 2.0, hexc("#9a9ea6")))
        S.append(P.slab(x + 0.2, 4.7, 0, 1.6, 0.6, 0.8, hexc("#c8a878")))
    return S


# ---------- 文字 ----------
def clock(img, date, time_, n=2, grade="大学1年", flash=0.0, pulse=0.0):
    O.clock_big(img, date, time_, flash=flash, grade=grade)
    O.counter(img, n, pulse)


def badge(img, text, col=YEL):
    d = ImageDraw.Draw(img)
    f = O.F(BLACK, 40)
    w = f.getlength(text) + 48
    y = O.CLOCK_Y + 372
    d.rounded_rectangle([540 - w / 2, y, 540 + w / 2, y + 62], radius=31, fill=(20, 26, 56), outline=col, width=4)
    d.text((540 - w / 2 + 24, y + 8), text, font=f, fill=col)


def notif(img, u, lines, read):
    """任意イベントのお知らせ → 既読"""
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    y0 = 760 + (1 - e) * 30
    h = 120 + 84 * len(lines)
    d.rounded_rectangle([100, y0, W - 100, y0 + h], radius=34, fill=(250, 250, 252, int(240 * e)))
    fh, f = O.F(BOLD, 40), O.F(BLACK, 64)
    d.text((140, y0 + 26), "お知らせ（参加は自由）", font=fh, fill=(64, 110, 220, int(255 * e)))
    for j, ln in enumerate(lines):
        d.text((140, y0 + 90 + j * 84), ln, font=f, fill=(40, 40, 50, int(255 * e)))
    img.alpha_composite(lay)
    if read:
        st = O.F(BLACK, 44)
        ImageDraw.Draw(img).text((W - 140 - st.getlength("既読"), y0 + h - 64), "既読", font=st, fill=(220, 60, 70))


def rule4(img, u):
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    y0 = 720
    d.rounded_rectangle([60, y0, W - 60, y0 + 380], radius=40, fill=(10, 12, 30, int(235 * e)), outline=(255, 216, 77, int(255 * e)), width=8)
    a = int(255 * e)
    ft, fb = O.F(BLACK, 56), O.F(BLACK, 66)
    d.text((540 - ft.getlength("ループのルール④") / 2, y0 + 34), "ループのルール④", font=ft, fill=(255, 216, 77, a))
    for j, ln in enumerate(["3月31日の夜が終わると、", "面接の日へ"]):
        d.text((540 - fb.getlength(ln) / 2, y0 + 140 + j * 96), ln, font=fb, fill=(255, 255, 255, a))
    img.alpha_composite(lay)


def hook(img, t):
    if t < 2.4:
        im = E.fit_text(["経験は、ある。", "なのに、", "答えられない。"], 112, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={2: RED})
        E.paste_center(img, im, 540, 1040, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["ガクチカ・ループ 第8話", "それで、何を考えましたか？"], 84, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1040, E.pop(t - 2.4))


# ---------- 1コマ ----------
def iv_img(t, kexpr, cam_mode, u, iv_talk=False, tk=(), freeze=0.0):
    iv, k = P.iv_rig(), P.kanata_suit_rig()
    k.expr = kexpr
    if iv_talk:
        iv.set(armL=0.55 + 0.25 * math.sin(t * 7))
    if cam_mode == "iv":
        cam = Camera((lerp(3.75, 3.6, u), lerp(0.55, 1.0, u), 1.62), (3.0, 5.5, 1.38), 48)
    elif cam_mode == "k":
        cam = Camera((lerp(3.42, 3.36, u), lerp(4.25, 4.0, u), 1.52), (3.0, 2.1, 1.42), 44)
    elif cam_mode == "close":
        cam = Camera((lerp(3.35, 3.2, u), lerp(4.1, 3.65, u), 1.5), (3.0, 2.1, 1.44), lerp(44, 42, u))
    else:   # トケイと2人
        cam = Camera((3.45, 4.75, 1.62), (3.3, 2.05, 1.45), 44)
    img, mask = render(P.OFFICE + iv.boxes() + k.boxes() + list(tk), cam, P.BG_OFFICE, keep={"kanata", "tokei"})
    img = img.convert("RGBA")
    if freeze > 0:
        img = O.desat(img, 0.95 * freeze, mask)
    return img


def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "cold":
        img = iv_img(t, "blank", "close", ease(t / s.dur), freeze=0.0)
        clock(img, "2029年6月1日（金）", "10:05", grade="大学4年")
        hook(img, t)
    elif n == "council":
        u = ease(t / s.dur)
        k = kanata_phone((3.6, -0.2, 0), 0.0, "blank" if sid else "normal", sit=True)
        cam = Camera((lerp(4.6, 4.4, u), lerp(-1.6, -1.2, u), 1.9), (3.0, 4.5, 1.0), 52)
        img, _ = render(COUNCIL + members(t) + k.boxes(), cam, BG_COUNCIL)
        img = img.convert("RGBA")
        clock(img, "2027年2月10日（水）", "10:30")
        badge(img, "議会傍聴")
        for j, (w, x, y) in enumerate([("補正予算", 300, 800), ("付託", 760, 900), ("採決", 420, 1040)]):
            if t > 0.2 + j * 0.3:
                im = E.fit_text([w], 62, 600, fill=(255, 255, 255), stroke=(8, 10, 24), sw=8)
                E.paste_center(img, im, x, y, E.pop(t - 0.2 - j * 0.3))
    elif n in ("notice1", "notice2"):
        k = F.kanata_phone_bed("blank" if n == "notice1" else ("smile" if sid else "normal"))
        img = Q.room_img(k, F.bed_cam(t, s.dur, 0.2))
        img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 50, 90)))
        if n == "notice1":
            clock(img, "2027年2月19日（金）", "21:00")
            notif(img, (t - 0.2) / 0.3, ["企業訪問", "公開討論会"], t > 1.4)
        else:
            clock(img, "2027年3月20日（土）", "22:00")
            if t < s.lines[0][0] - 0.1:
                notif(img, (t - 0.1) / 0.3, ["議員交流会", "地域の勉強会"], t > 0.8)
    elif n == "event":
        u = ease(t / s.dur)
        k = kanata_phone((2.9, 2.6, 0), math.pi * 0.9, "blank")
        k.spec = KANATA_PHONE_SUIT
        cam = Camera((lerp(3.5, 3.4, u), lerp(0.3, 0.6, u), 1.7), (2.7, 4.4, 1.3), 50)
        img, _ = render(R.OUTSIDE + tents() + V5.students(t) + k.boxes(), cam, R.BG_SKY)
        img = img.convert("RGBA")
        clock(img, "2027年3月6日（土）", "13:00")
        badge(img, "地域のイベント")
        if t > 0.8:
            O.caption(img, "いつも、スマホ。", 1330, t - 0.8, size=84, col=YEL)
    elif n == "midnight":
        k = F.kanata_phone_bed("sleep")
        img = Q.room_img(k, F.bed_cam(t, s.dur, 0.3))
        img.alpha_composite(Image.new("RGBA", (W, H), (6, 8, 30, 150)))
        if t < s.zero:
            clock(img, "2027年3月31日（水）", "23:59")
        else:
            clock(img, "2027年4月1日（木）", "0:00", flash=1.0)
            rule4(img, (t - s.zero - 0.1) / 0.3)
    elif n == "iv":
        a, b, c, d_ = (x[0] for x in s.lines)
        u = ease(t / s.dur)
        frozen = t >= s.tf
        if t < b - 0.1:
            img = iv_img(t, "open", "k", u)
        elif t < c - 0.1:
            img = iv_img(t, "open", "iv", u, iv_talk=sid == "05")
        elif t < d_ - 0.1:
            img = iv_img(t, "normal", "k", u)
        elif t < d_ + L("01") + 0.1:
            img = iv_img(t, "normal", "iv", u, iv_talk=True)
        else:   # 1秒の沈黙 → 世界が止まる
            v = ease(min(1, (t - d_ - L("01") - 0.1) / 1.0))
            img = iv_img(t, "blank", "close", v, freeze=ease(min(1, (t - s.tf) / 0.5)) if frozen else 0.0)
            if frozen and t - s.tf < 0.25:
                img = Image.blend(img, Image.new("RGBA", (W, H), (255, 255, 255, 255)), 0.35 * (1 - (t - s.tf) / 0.25))
        clock(img, "2029年6月1日（金）", "10:05", grade="大学4年", flash=1.0 if frozen else 0.0)
        if frozen:
            O.caption(img, "経験しただけでは、\n答えにならない。", 1080, t - s.tf - 0.1, size=86, col=YEL)
    elif n == "freeze":
        a = s.lines[0][0]
        drop = (1 - ease(min(1, t / 0.5))) * 1.6
        tk = C.tokei_boxes((3.62, 2.05, 1.62 + drop), t, "eyes", 0.75, 0.35)
        k_ = "shock"
        img = iv_img(t, k_, "two", 0, tk=tk, freeze=1.0)
        O.clock_big(img, "2029年6月1日（金）", "10:05", flash=1.0, grade="大学4年")
        pulse = max(0, 1 - (t - 0.6) / 0.8) if t > 0.6 else 0.0
        O.counter(img, 1 if t > 0.6 else 2, pulse)
        if 0.6 < t < a - 0.1:
            im = E.fit_text(["残りループ", "2 → 1"], 140, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=14, hl={1: RED})
            E.paste_center(img, im, 540, 1000, E.pop(t - 0.6))
    elif n == "rewind":
        t0 = s.t0
        fz = shot("freeze")
        if t < t0:
            img = iv_img(fz.dur, "shock", "close", 1.0, freeze=1.0)
            O.clock_big(img, "2029年6月1日（金）", "10:05", flash=1.0, grade="大学4年")
            O.counter(img, 1)
        elif t < t0 + 0.35:
            img = O.desat(iv_img(fz.dur, "shock", "close", 1.0), 1)
            O.cracks(img, ease((t - t0) / 0.35))
        else:
            u = (t - t0 - 0.35) / (s.dur - t0 - 0.6)
            if u < 1:
                src = [shot("iv"), shot("midnight"), shot("event"), shot("council")][min(3, int(u * 4))]
                img = O.glitch(O.desat(frame_raw(src, src.dur * (1 - (u * 4 % 1))), 1), 1.0, int(t * 30))
                year = 2029 - min(3, int(u * 4))
                O.caption(img, f"{year}", 900, 1.0, size=230, col=YEL)
                O.caption(img, "◀◀ 巻き戻し中", 1120, 1.0, size=70)
            else:
                img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "あなたなら、", 600, t, size=84)
        O.caption(img, "何て答える？", 730, t, size=110, col=YEL)
        for txt, y, sz, col, path in ((["コメントで教えてね"], 900, 56, (255, 255, 255), BLACK),
                                      (["次回 第9話「全部、消えた。」"], 1030, 52, (255, 255, 255), BLACK),
                                      (["ドットジェイピー広島第一支部", "春インターン申込は12月31日まで"], 1180, 48, YEL, BLACK),
                                      (["この動画は「勇気を出して一歩を踏み出そう」という", "メッセージを伝えるための創作ドラマです"], 1340, 32, (220, 226, 245), BOLD)):
            E.paste_center(img, E.fit_text(txt, sz, 1000, fill=col, sw=6, path=path), 540, y, E.pop(t - 0.3))
    if sid and not NOSUB:
        subtitle(img, sid)
    return img


def frame_raw(s, t):
    """巻き戻し用：字幕なしの絵"""
    global NOSUB
    NOSUB = True
    try:
        return frame(s, t)
    finally:
        NOSUB = False


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
