"""ガクチカ・ループ 第12話「自分から」（リメイク版台本・11/14 ゆうきさんOK）
2/19 21:00 第8話と同じ任意イベントのお知らせ。前は既読だけ →「…行きます。」2つとも「参加する」。
2/24 企業訪問（架空の会社・社名ロゴなし）。人事「面接では、経験より、そこで何を考えたかを聞きます。」
手を挙げるのが早すぎる →「質問は、最後に受け付けますね。」→ 質問の時間に「地元の会社が、若い人に来てほしい理由って、何ですか？」
帰り道「3/3 公開討論会：参加予定」。場面ごとに0.2秒の余韻、転換音・環境音は6割。
カメラは話し手が変わるときだけ切り替え、寄りは一方向（注意点8）。python3 ep12.py still <shot> <t> | plan | build"""
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
import ep8 as S8
import ep9 as S9
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep12"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED, GRN = (255, 216, 77), (255, 90, 90), (90, 220, 120)
O.SPEAK["HR"] = ("人事の方", (120, 150, 210))
PAD = 0.2

VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep12/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("K", "あの、[質問]いいですか。"),
    "02": ("T", "前は、[既読だけ]だったのだ。"),
    "03": ("K", "…前は、|[全部スルー]したんだよな。"),
    "04": ("K", "…[行きます]。"),
    "05": ("HR", "面接では、経験より、|そこで[何を考えたか]を|聞きます。"),
    "06": ("K", "（…知ってる。[痛いほど]。）"),
    "07": ("HR", "質問は、[最後に]|受け付けますね。"),
    "08": ("HR", "では、[質問]のある方。"),
    "09": ("K", "地元の会社が、|[若い人]に来てほしい理由って、|何ですか？"),
    "10": ("HR", "いい質問ですね。…町に|若い人がいないと、|[続かない]からです。"),
    "11": ("T", "今日は、[自分から]|手を挙げたのだ。"),
    "12": ("K", "…最初は、[早すぎた]けどな。"),
}
MSGS = [("2/24（水）企業訪問を行います！", "参加は自由です。申し込みはこちら"), ("3/3（水）公開討論会があります！", "大学生が登壇します")]


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
    ln, t = seq(["02", "03"], 3.8, extra={"03": 0.2})
    ph2 = t + 0.2
    ln2, t = seq(["04"], ph2 + 0.6)
    s = O.Shot("room", t + 0.5 + 0.5 + 1.4, ln + ln2)
    s.ph2, s.tap1 = ph2, t + 0.1
    s.tap2 = s.tap1 + 0.55
    S.append(s)                                                                           # 2/19 お知らせ → 参加する
    ln, t = seq(["05", "06"], 0.8, extra={"06": 0.4})
    s = O.Shot("visit", 0, ln); s.raise_t = t + 0.3
    ln2, t = seq(["07"], s.raise_t + 0.7)
    s.lines += ln2; s.dur = t + 1.4; S.append(s)                                          # 企業訪問：手を挙げるのが早すぎる
    ln, t = seq(["08", "01", "09", "10"], 0.8, extra={"01": 0.2, "09": 0.9, "10": 0.4})
    s = O.Shot("qa", t + 2.0, ln); s.hand = ln[1][0] - 0.25; S.append(s)                  # 質問の時間
    ln, t = seq(["11", "12"], 1.0, extra={"12": 0.3})
    s = O.Shot("home", t + 2.6, ln); s.plan = t + 0.2; S.append(s)                        # 帰り道 → 3/3 参加予定
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


def last_line(s, t):
    last = None
    for (t0, i) in s.lines:
        if t >= t0 - 0.1:
            last = i
    return last


# ---------- 絵 ----------
BG_EVE = E.sky((236, 140, 90), (250, 208, 160)).convert("RGB").resize((W * G.SS, H * G.SS))


def clock(img, date, time_):
    O.clock_big(img, date, time_, grade="大学1年")
    O.counter(img, 1)


def hook(img, t):
    if t < 2.4:
        im = E.fit_text(["前は、", "全部スルーした。"], 108, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={1: YEL})
        E.paste_center(img, im, 540, 760, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["ガクチカ・ループ 第12話", "自分から"], 96, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 760, E.pop(t - 2.4))


def chat(t, joined=(0.0, 0.0), old=False):
    """オープンチャット＋「参加する」ボタン。joined: 押した度合い（0→1）"""
    img = S8.phone_chat(t, MSGS, read=old, close=0)
    d = ImageDraw.Draw(img)
    x1, y0 = 960, 640
    fb = O.F(BLACK, 40)
    if not old:
        for j, u in enumerate(joined):
            if t < 0.4 + j * 0.7 + 0.25:
                continue
            y = y0 + 200 + j * 270
            on = u > 0
            col = GRN if on else (255, 138, 31)
            txt = "✓ 参加" if on else "参加する"
            w = fb.getlength(txt) + 60
            sc = 1 + 0.15 * math.sin(min(1, u) * math.pi) if on else 1
            bx0, by0 = x1 - 80 - w * sc, y + 230
            d.rounded_rectangle([bx0, by0, bx0 + w * sc, by0 + 70 * sc], radius=35, fill=col)
            d.text((bx0 + 30, by0 + 10), txt, font=fb, fill=(255, 255, 255))
    if old:   # 前のループの記憶：色を抜いて「前のループ」
        g = img.convert("L").convert("RGBA")
        img = Image.blend(img, g, 0.7)
        O.caption(img, "前のループ", 1800, 1.0, size=70, col=(200, 204, 220))
    return img


def tap(img, x, y, u):
    """押す指（丸い波紋）"""
    if not (0 < u < 1):
        return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    r = 30 + 60 * u
    ImageDraw.Draw(lay).ellipse([x - r, y - r, x + r, y + r], outline=(255, 255, 255, int(255 * (1 - u))), width=10)
    img.alpha_composite(lay)


def cam_k(t, dur):
    """人事の側からカナタ（上げた手まで入る、少し引いた画）"""
    u = ease(t / max(dur, 0.01))
    return Camera((lerp(3.45, 3.4, u), lerp(5.3, 5.0, u), 1.95), (3.0, 2.1, 1.85), 50)


def meeting(t, cam, kexpr="normal", hand=0.0, hrexpr="normal", hr_talk=False, laugh=False):
    hr = Rig(C.HR, (3.0, 5.5, 0), math.pi, tag="hr")
    hr.set(sit=True, armL=0.55, armR=0.55 + (0.15 * math.sin(t * 6) if hr_talk else 0))
    hr.expr = ("smile" if int(t * 7) % 2 else hrexpr) if hr_talk else hrexpr
    k = R.kanata_seat(kexpr)
    k.spec = C.KANATA_SUIT
    k.set(armR=0.5 + (-3.65) * hand, armR_out=-0.25 * hand)
    st = []
    for i, x in enumerate((1.75, 4.25)):
        r = Rig(V5.STUDENTS[i + 1], (x, 2.1, 0), 0.0, tag=f"st{i}")
        r.set(sit=True, armL=0.5, armR=0.5, head_yaw=(0.35 if x < 3 else -0.35) * (1 if laugh else 0))
        r.expr = "smile" if laugh else "normal"
        st += r.boxes()
    img, _ = render(R.MEET + hr.boxes() + k.boxes() + st, cam, R.BG_MEET)
    return img.convert("RGBA")


def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "cold":
        u = ease(t / s.dur)
        img = meeting(t, cam_k(t, s.dur), "resolve", hand=1.0)
        clock(img, "2027年2月24日（水）", "15:20")
        hook(img, t)
    elif n == "room":
        a, b = s.lines[0][0], s.lines[1][0]
        if t < 3.4:                                              # お知らせ → 前のループの「既読だけ」が重なる
            img = chat(t)
            if 2.1 < t < 3.0:
                img = O.glitch(chat(t, old=True), 0.2, int(t * 30)) if t < 2.25 or t > 2.85 else chat(t, old=True)
        elif t < s.ph2:                                          # ベッドでスマホ。トケイ
            k = F.kanata_phone_bed("normal" if t < b else "resolve")
            tk = Q.tokei_near(t, "eyes", drop_t=t - 3.4)
            img = Q.room_img(k, F.bed_cam(t - 3.4, s.ph2 - 3.4, 0.3), list(tk))
            img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 50, 90)))
        else:                                                    # 「参加する」を押す
            j1 = (t - s.tap1) / 0.3 if t > s.tap1 else 0
            j2 = (t - s.tap2) / 0.3 if t > s.tap2 else 0
            img = chat(5.0, (j1, j2))
            tap(img, 820, 640 + 200 + 230 + 35, (t - s.tap1) / 0.4)
            tap(img, 820, 640 + 200 + 270 + 230 + 35, (t - s.tap2) / 0.4)
        clock(img, "2027年2月19日（金）", "21:00")
    elif n in ("visit", "qa"):
        u = ease(t / s.dur)
        last = last_line(s, t)
        if n == "visit":
            hand = ease(min(1, max(0, t - s.raise_t) / 0.2)) * (1 - ease(min(1, max(0, t - s.lines[2][0] - L("07")) / 0.4)))
            laugh = t > s.lines[2][0] + 0.3
            kx = "resolve" if t < s.raise_t else ("open" if t < s.lines[2][0] + L("07") else "smile")
            on_k = last == "06" or s.raise_t - 0.1 < t < s.lines[2][0] - 0.1
            hrx = "smile" if t > s.lines[2][0] - 0.1 else "normal"
        else:
            hand = ease(min(1, max(0, t - s.hand) / 0.25)) * (1 - ease(min(1, max(0, t - s.lines[2][0] + 0.2) / 0.4)))
            laugh = False
            kx = "resolve" if t < s.lines[3][0] else "open"
            on_k = last in ("01", "09")
            hrx = "smile" if t > s.lines[3][0] - 0.1 else "normal"
        cam = cam_k(t, s.dur) if on_k else R.cam_mio(t, s.dur)
        img = meeting(t, cam, kx, hand, hrx, hr_talk=sid in ("05", "07", "08", "10"), laugh=laugh)
        clock(img, "2027年2月24日（水）", "14:00" if n == "visit" else "15:20")
        S9.bigbadge(img, "企業訪問" if n == "visit" else "質問の時間", (40, 120, 200))
    elif n == "home":
        u = ease(t / s.dur)
        x = lerp(-1.0, 1.6, u)
        look = t > s.plan - 0.4
        k = S9.walk(K1.kanata((x, 1.2, 0), -math.pi / 2, "smile" if t > s.lines[1][0] - 0.1 else "normal",
                              armR=1.1 if look else 0.05, head_pitch=0.25 if look else 0.0), t, 0.6)
        tk = C.tokei_boxes((x + 0.75, 0.8, 1.85), t, "eyes", 0.45, math.pi + 0.3)
        cam = Camera((x + 0.25, -2.7, 1.95), (x + 0.3, 1.2, 1.72), 44)
        img, _ = render(K1.STREET + k.boxes() + tk, cam, BG_EVE)
        img = img.convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 150, 80, 28)))
        clock(img, "2027年2月24日（水）", "17:30")
        if t > s.plan:
            F.pill(img, "3/3 公開討論会：参加予定", 1100, 54, (40, 150, 90), u=(t - s.plan) / 0.3)
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "あなたなら、", 560, t, size=84)
        O.caption(img, "どれに行ってみたい？", 690, t, size=96, col=YEL)
        for txt, y, sz, col, path in ((["企業訪問 ／ 議員交流会 ／ 公開討論会"], 830, 48, (255, 255, 255), BLACK),
                                      (["コメントで教えてね"], 930, 52, (255, 255, 255), BLACK),
                                      (["次回 第13話「30年後の広島」"], 1050, 52, (255, 255, 255), BLACK),
                                      (["ドットジェイピー広島第一支部", "春インターン申込は12月31日まで"], 1190, 48, YEL, BLACK),
                                      (["この動画は「勇気を出して一歩を踏み出そう」という", "メッセージを伝えるための創作ドラマです"], 1350, 32, (220, 226, 245), BOLD)):
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
