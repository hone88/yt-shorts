"""ガクチカ・ループ 第5話「自己PRが、空欄。」
第4話の決意（次は、布団から出る）を受けて、2周目のカナタが今度はちゃんと動く回。
ES・IS（自己PRが空欄 → ミオと話して「人前で自分の考えを伝えられるようになりたい」）
→ 1次選考会・2次選考会は短いダイジェスト（第4話で空いていた席に、今度は座っている）
→ 活動先決定 → 2027年1月末、キックオフへ。
流れ：説明会 → ES・IS → 1次選考会 → スタッフがES・ISを活動先へ提出 → 2次選考会 → 活動先決定 → キックオフ
python3 ep5.py still <shot> <t> | python3 ep5.py build"""
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
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep5"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED, GRN = (255, 216, 77), (255, 90, 90), (90, 220, 120)
O.SPEAK["Mo"] = ("森下議員", (170, 172, 182))

# ---------- 声 ----------
VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep5/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("K", "……また、[12月5日]。"),
    "02": ("K", "今度は……[行く]。"),
    "03": ("K", "[ES・IS]……？"),
    "04": ("K", "……書くこと、[ない]。"),
    "05": ("T", "また、[空欄]なのだ。"),
    "06": ("K", "うるさい。"),
    "07": ("M", "自己PRって、|[すごい経験]を書く必要ないよ。"),
    "08": ("K", "でも、ぼく……|[何もしてない]し。"),
    "09": ("M", "じゃあ、この春で、|[何を変えたい]？"),
    "10": ("K", "……人前で、自分の考えを、|[伝えられるように]なりたい。"),
    "11": ("M", "それ、[書ける]じゃん。"),
    "12": ("K", "……[書けた]。"),
    "13": ("T", "[最初の一歩]なのだ。"),
    "14": ("M", "[興味があること]、|話してみて。"),
    "15": ("K", "……[地域のこと]を、|もっと知ってみたいです。"),
    "16": ("Mo", "どんなことを、|[やってみたい]？"),
    "17": ("K", "人と話して、自分の考えを、|[伝えられるように]なりたいです。"),
    "18": ("K", "……[ここから]か。"),
    "19": ("T", "ここから、[本当のインターン]が|始まるのだ。"),
    "20": ("K", "……うん。"),
}
PR = "人前で自分の考えを伝えられるようになりたい。"


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
    ln, t = seq(["01", "02"], 0.4, extra={"02": 0.5})
    S.append(O.Shot("wake", max(t + 0.3, 4.6), ln))
    ln, t = seq(["03", "04", "05", "06"], 1.5, extra={"04": 0.9, "05": 0.1})   # メッセージ → ES・IS の画面
    s = O.Shot("esis", t + 0.2, ln); s.form = ln[0][0] + L("03") + 0.15; S.append(s)
    ln, t = seq(["07", "08", "09", "10", "11"], 0.5, extra={"10": 0.35})
    S.append(O.Shot("call", t + 0.1, ln))
    ln, t = seq(["12", "13"], 1.9)                                         # 入力するあいだ
    S.append(O.Shot("type", t + 0.3, ln))
    ln, t = seq(["14", "15"], 0.5)
    S.append(O.Shot("first", t + 0.9, ln))                                 # 最後に「ES・ISを活動先へ」
    ln, t = seq(["16", "17"], 1.1)
    s = O.Shot("second", t + 1.6, ln); s.rev = t + 0.1; S.append(s)        # rev：活動先決定
    ln, t = seq(["18", "19", "20"], 1.3, extra={"20": 0.2})
    S.append(O.Shot("kick", t + 0.4, ln))
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


# ---------- 文字・部品 ----------
def clock(img, date, time_):
    O.clock_big(img, date, time_, grade="大学1年")
    O.counter(img, 2)


def hook(img, t):
    if t < 2.4:
        im = E.fit_text(["2周目の、", "12月5日。"], 130, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={1: YEL})
        E.paste_center(img, im, 540, 1110, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["ガクチカ・ループ 第5話", "自己PRが、空欄。"], 90, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1110, E.pop(t - 2.4))


def es_form(img, u, pr_text="", cursor=True, warn=False):
    """パソコンのES・IS画面。自己PRの欄だけ空欄"""
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a = int(255 * e)
    x0, y0, x1 = 70, 690 + (1 - e) * 40, W - 70
    d.rounded_rectangle([x0, y0, x1, y0 + 560], radius=28, fill=(248, 249, 252, int(245 * e)), outline=(40, 44, 60, a), width=6)
    d.rounded_rectangle([x0, y0, x1, y0 + 78], radius=28, fill=(64, 110, 220, a))
    fh, fl, fv = O.F(BLACK, 46), O.F(BLACK, 34), O.F(BOLD, 34)
    d.text((540 - fh.getlength("ES・IS") / 2, y0 + 12), "ES・IS", font=fh, fill=(255, 255, 255, a))
    rows = [("名前", "宇野カナタ"), ("大学", "〇〇大学 1年"), ("興味のあること", "地域のこと"), ("やってみたいこと", "人と話すこと")]
    for j, (k, v) in enumerate(rows):
        y = y0 + 100 + j * 76
        d.text((x0 + 36, y + 6), k, font=fl, fill=(110, 114, 130, a))
        d.rounded_rectangle([x0 + 330, y, x1 - 36, y + 58], radius=10, fill=(236, 238, 244, a))
        d.text((x0 + 350, y + 10), v, font=fv, fill=(40, 40, 50, a))
    y = y0 + 100 + 4 * 76
    d.text((x0 + 36, y + 6), "自己PR", font=fl, fill=(220, 60, 70, a) if warn else (110, 114, 130, a))
    d.rounded_rectangle([x0 + 36, y + 56, x1 - 36, y + 150], radius=12, fill=(255, 255, 255, a),
                        outline=(220, 60, 70, a) if warn else (190, 194, 206, a), width=5)
    ft = O.F(BOLD, 34)
    d.text((x0 + 60, y + 82), pr_text, font=ft, fill=(30, 30, 40, a))
    if cursor:
        cx = x0 + 62 + ft.getlength(pr_text)
        d.rectangle([cx, y + 80, cx + 4, y + 124], fill=(30, 30, 40, a))
    img.alpha_composite(lay)


def bed_cam(t, dur, push=0.25):
    u = ease(t / max(dur, 0.01))
    return Camera((lerp(2.9, 2.85, u), lerp(1.1, 1.1 + push, u), 1.8), (2.55, 3.75, 1.62), 46)


def kanata_pc(expr="normal"):
    k = Q.kanata_bed(expr)
    k.set(head_pitch=0.22)
    return k


def call_img(t, talking):
    """ミオとのオンライン通話（第2話と同じ画面。カナタはカメラOFFのまま）"""
    img = Image.new("RGBA", (W, H), (24, 26, 34, 255))
    d = ImageDraw.Draw(img)
    TX, TY, TW, TH = Q.TX, 720, Q.TW, Q.TH   # 時計にかからないよう下げる
    img.paste(Q.mio_tile(t, talking).resize((TW, TH)), (TX, TY))
    d.rounded_rectangle([TX, TY, TX + TW, TY + TH], radius=6, outline=GRN if talking else (60, 64, 80), width=8)
    d.rounded_rectangle([TX + 20, TY + TH - 66, TX + 330, TY + TH - 14], radius=12, fill=(0, 0, 0))
    d.text((TX + 38, TY + TH - 60), "宮路ミオ（スタッフ）", font=O.F(BOLD, 34), fill=(255, 255, 255))
    sw, sh = 300, 194
    sx, sy = TX + TW - sw - 18, TY + TH - sh - 18
    d.rectangle([sx, sy, sx + sw, sy + sh], fill=(12, 12, 16))
    f = O.F(BLACK, 30)
    d.text((sx + sw / 2 - f.getlength("カメラOFF") / 2, sy + 80), "カメラOFF", font=f, fill=(150, 156, 175))
    d.rectangle([sx, sy, sx + sw, sy + sh], outline=YEL, width=4)
    d.rounded_rectangle([sx + 8, sy + sh - 44, sx + 108, sy - 6 + sh], radius=8, fill=(0, 0, 0))
    d.text((sx + 18, sy + sh - 42), "カナタ", font=O.F(BOLD, 28), fill=YEL)
    return img


def student_char(hood, hair, seed):
    """キックオフ会場の学生（カナタの体に色ちがいの服）"""
    pal = dict(C.KANATA_PAL)
    pal["R"], pal["D"], pal["H"] = hexc(hood), hexc(hood), hexc(hair)

    def parts(e="normal"):
        old = C.KANATA_PAL
        C.KANATA_PAL = pal
        try:
            return C.kanata_parts("open" if seed % 2 else "normal", "hoodie")
        finally:
            C.KANATA_PAL = old
    return dict(name=f"st{seed}", label="学生", parts=parts)


STUDENTS = [student_char(h, hr, i) for i, (h, hr) in enumerate(
    [("#3a78c8", "#2b1d16"), ("#4aa36a", "#5a3a22"), ("#e08a2a", "#1e1a18"), ("#8a5ac8", "#2b1d16"), ("#d8d8d8", "#3a2a20")])]
ST_POS = [(1.2, 4.9, 0.4), (1.9, 5.3, 2.6), (3.6, 5.0, -2.8), (4.4, 5.4, 3.0), (0.4, 5.4, 0.2)]


def students(t):
    out = []
    for i, (ch, (x, y, yaw)) in enumerate(zip(STUDENTS, ST_POS)):
        r = Rig(ch, (x, y, 0), yaw, tag=f"st{i}")
        r.set(armL=0.05, armR=0.05, head_yaw=0.15 * math.sin(t * 1.2 + i))
        out += r.boxes()
    return out


def stamp(img, u, text="活動先 決定"):
    if u <= 0:
        return
    f = O.F(BLACK, 96)
    w = f.getlength(text) + 100
    st = Image.new("RGBA", (int(w), 190), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rounded_rectangle([0, 0, w - 1, 189], radius=28, outline=GRN, width=14, fill=(12, 40, 24, 215))
    sd.text((50, 34), text, font=f, fill=GRN)
    st = st.rotate(-6, expand=True)
    E.paste_center(img, st, 540, 1020, E.pop(u))


# ---------- 1コマ ----------
def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "wake":
        a, b = (x[0] for x in s.lines)
        k = Q.kanata_bed("shock" if t < b - 0.3 else "resolve")
        img = Q.room_img(k, Q.face_cam(t, s.dur, 0.35))
        clock(img, "2026年12月5日（土）", "8:00")
        hook(img, t)
    elif n == "esis":
        a, b, c, d_ = (x[0] for x in s.lines)
        tk = Q.tokei_near(t, "eyes", t - c + 0.5) if t > c - 0.5 else []
        k = kanata_pc("open" if t < b else ("blank" if t < d_ else "normal"))
        img = Q.room_img(k, bed_cam(t, s.dur, 0.2), tk)
        clock(img, "2026年12月5日（土）", "20:00")
        if t < s.form:
            F.msg_card(img, (t - 0.2) / 0.3, "ミオ", ["選考会前に、", "ES・ISを書いておいてね！"], y0=760)
        else:
            blink = int(t * 2.5) % 2 == 0
            es_form(img, (t - s.form) / 0.3, "", blink, warn=t > b)
            if b + 0.2 < t < c:
                Q.big_word(img, "空欄", t - b - 0.2, RED, y=1580, size=110)
    elif n == "call":
        talking = sid is not None and TEXT[sid][0] == "M"
        img = call_img(s.start + t, talking)
        clock(img, "2026年12月5日（土）", "20:15")
    elif n == "type":
        a, b = (x[0] for x in s.lines)
        tk = Q.tokei_near(t, "eyes", t - b + 0.5) if t > b - 0.5 else []
        k = kanata_pc("resolve" if t < a else "smile")
        img = Q.room_img(k, bed_cam(t, s.dur, 0.15), tk)
        clock(img, "2026年12月5日（土）", "20:30")
        p = min(1, max(0, (t - 0.2) / 1.5))
        es_form(img, 1, PR[:int(len(PR) * p)], p < 1 or int(t * 2.5) % 2 == 0)
    elif n == "first":
        a, b = (x[0] for x in s.lines)
        if t < b - 0.1:
            img = R.meet_img(R.cam_mio(t, s.dur), talk="M" if sid == "14" else None, t=s.start + t)
        else:
            img = R.meet_img(R.cam_kanata(t - b, s.dur - b), kexpr="open")
        clock(img, "2026年12月9日（水）", "16:00")
        F.pill(img, "1次選考会", 1040, 54, (64, 110, 220), u=(t - 0.1) / 0.3)
        if t > s.dur - 0.85:
            F.pill(img, "ES・ISは、スタッフから活動先へ", 1150, 46, (40, 44, 60), u=(t - s.dur + 0.85) / 0.3)
    elif n == "second":
        a, b = (x[0] for x in s.lines)
        k = R.kanata_seat("smile" if t > s.rev else "open")
        k.pos = (3.0, 2.1, 0)
        if t < b - 0.1:   # 第4話で空いていた席に、今度は座っている（背中越し）
            u = ease(t / max(b, 0.1))
            cam = Camera((lerp(3.95, 3.9, u), lerp(0.2, 0.6, u), 2.0), (3.0, 5.2, 0.95), 50)
        else:
            u = ease((t - b) / max(0.1, s.dur - b))
            cam = Camera((lerp(3.4, 3.35, u), lerp(4.2, 4.0, u), 1.52), (3.0, 2.1, 1.42), 44)
        mo = F.morishita_seat()
        if sid == "16":
            mo.set(head_pitch=0.04 * math.sin(t * 6))
        img, _ = render(F.ROOM2 + mo.boxes() + F.host_seat().boxes() + k.boxes(), cam, R.BG_MEET)
        img = img.convert("RGBA")
        clock(img, "2026年12月10日（木）", "10:00")
        if t < b - 0.1:
            F.pill(img, "2次選考会", 1010, 46, (64, 110, 220), u=(t - 0.1) / 0.3)
            F.pill(img, "今度は、ここにいる。", 1105, 54, (230, 170, 30), (20, 20, 30), u=(t - 0.5) / 0.3)
        if t > s.rev:
            img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(90 * min(1, (t - s.rev) / 0.3)))))
            stamp(img, t - s.rev)
    elif n == "kick":
        a, b, c = (x[0] for x in s.lines)
        k = R.kanata_stand("resolve" if t < b else ("normal" if t < c else "resolve"))
        k.set(head_pitch=-0.05)
        u = ease(t / s.dur)
        cam = Camera((lerp(2.95, 2.9, u), lerp(0.1, 0.6, u), 1.6), (2.65, 4.4, 1.55), 50)
        tk = Q.tokei_near(t, "eyes", t - b + 0.5, (3.25, 3.3, 1.75)) if t > b - 0.5 else []
        img, _ = render(R.OUTSIDE + students(t) + k.boxes() + tk, cam, R.BG_SKY)
        img = img.convert("RGBA")
        clock(img, "2027年1月30日（土）", "13:00")
        F.pill(img, "キックオフ会場", 1060, 46, (30, 58, 106), u=(t - 0.2) / 0.3)
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "次回", 580, t, size=80)
        O.caption(img, "キックオフ", 720, t - 0.1, size=150, col=YEL)
        for txt, y, sz, col, path in ((["あなたなら、自己PRに何を書く？"], 900, 56, (255, 255, 255), BLACK),
                                      (["コメントで教えてね"], 990, 44, (220, 226, 245), BLACK),
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
