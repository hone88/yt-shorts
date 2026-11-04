"""ガクチカ・ループ 第4話「布団から、出られない。」
2次選考会（受け入れ先の方と日程を合わせて行う）に、こわくて行けなかった「大やらかしの日」。
議員さん・活動先の方は怒らせない。空いた席と静けさ、代わりに頭を下げるミオで重さを出す。
何もしない一日 → 面接へ → 残りループ 3→2 → 12月5日に戻る。
python3 ep4.py still <shot> <t> | python3 ep4.py build"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw
import g3d as G
from g3d import Camera, Rig, render, hexc, add
import characters as C
import ep1b as O
import ep1c as P
import ep2 as Q
import ep3 as R
from engine import lerp, ease
import engine as E

W, H, FPS, SR = 1080, 1920, 30, 24000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_ep4"
BLACK, BOLD = O.BLACK, O.BOLD
YEL, RED = (255, 216, 77), (255, 90, 90)
DAY = "2026年12月10日（木）"
O.SPEAK["Mo"] = ("森下議員", (170, 172, 182))

# ---------- 声 ----------
VO = {}


def vo(i):
    if i not in VO:
        with wave.open(f"{HERE}/voice/ep4/{i}.wav") as w:
            VO[i] = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return VO[i]


def L(i):
    return len(vo(i)) / SR


TEXT = {
    "01": ("K", "…むり。|[行けない]…。"),
    "02": ("Mo", "…[学生さん]は、|まだかな。"),
    "03": ("M", "す、すみません！|いま、[連絡]してます…！"),
    "04": ("M", "話すのは、1次選考会でも話した|カナタの[興味あること]と[やりたいこと]。|[なぜやりたいのか]も、|そのまま話せばいいんだよ。"),
    "05": ("K", "…分かってる。|分かってるけど…[こわい]んだって。"),
    "06": ("T", "布団から出ないなら、|[何もしない一日]なのだ。"),
    "07": ("K", "…あと、[5分]だけ。"),
    "08": ("M", "本当に、|[申し訳ありません]。"),
    "09": ("T", "…[時間切れ]なのだ。"),
    "10": ("I", "学生時代に、|[力を入れたこと]は？"),
    "11": ("K", "…また、[12月5日]。"),
    "12": ("K", "みんな、|[来てくれてた]のに…。"),
    "13": ("K", "次は、[布団から出る]。"),
    "14": ("T", "残りは、[2回]なのだ。"),
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
def seq(ids, start=0.4, gap=0.25, extra=None):
    out, t = [], start
    for i in ids:
        t += (extra or {}).get(i, 0)
        out.append((t, i))
        t += L(i) + gap
    return out, t


def plan():
    S = []
    ln, t = seq(["01"], 0.35)
    S.append(O.Shot("cold", max(t + 0.3, 4.6), ln))
    ln, t = seq(["02", "03"], 1.4, extra={"03": 0.3})          # 空いた席を見せる間
    S.append(O.Shot("room2", t + 0.5, ln))
    ln, t = seq(["04", "05"], 0.9, extra={"05": 0.4})
    s = O.Shot("bed", t + 0.3, ln); S.append(s)
    ln, t = seq(["06", "07"], 0.7, extra={"07": 0.3})
    S.append(O.Shot("tokei", t + 0.4, ln))
    ln, t = seq(["08"], 1.3)
    S.append(O.Shot("bow", t + 1.4, ln))
    ln, t = seq(["09"], 4.2)                                    # 早回しのあと「時間切れ」
    S.append(O.Shot("ff", t + 0.5, ln))
    ln, t = seq(["10"], 0.5)
    s = O.Shot("iv", t + 3.4, ln); s.rev = t + 0.7; S.append(s)
    ln, t = seq(["11", "12", "13", "14"], 0.8, extra={"13": 0.4, "14": 0.2})
    S.append(O.Shot("wake", t + 0.5, ln))
    S.append(O.Shot("end", 6.0))
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


# ---------- 人物 ----------
def morishita_seat():
    r = Rig(C.MORISHITA, (2.6, 5.5, 0), math.pi, tag="mo")
    r.set(sit=True, armL=0.55, armR=0.55)
    return r


def host_seat():
    """活動先の方（セリフなし）"""
    r = Rig(C.RECEPTION, (3.6, 5.5, 0), math.pi, tag="host")
    r.set(sit=True, armL=0.55, armR=0.55)
    return r


def mio_stand(pos=(4.7, 3.4, 0), yaw=math.pi * 0.75, **pose):
    r = Rig(C.MIO, pos, yaw, tag="mio")
    r.set(armL=0.05, armR=0.05)
    r.set(**pose)
    return r


def room2_set():
    S = list(R.MEET)
    S.append(P.slab(3.75, 5.25, 0, 0.5, 0.5, 0.5, hexc("#3a4a6a")))    # 活動先の方の椅子
    return S


ROOM2 = room2_set()


def kanata_phone_bed(expr="normal"):
    k = Q.kanata_bed(expr)
    k.spec = P.KANATA_PHONE
    k.set(head_pitch=0.3)
    return k


BL, BD = hexc("#3a68c8"), hexc("#2f58ae")


def blanket():
    """布団にくるまる（顔だけ出す）"""
    return [P.slab(1.85, 3.3, 0.5, 1.3, 0.85, 1.05, BL),        # 体（肩まで）
            P.slab(2.12, 3.5, 1.96, 0.76, 0.6, 0.12, BD),       # 頭の上
            P.slab(2.12, 3.5, 1.3, 0.12, 0.6, 0.7, BD),         # 左
            P.slab(2.76, 3.5, 1.3, 0.12, 0.6, 0.7, BD),         # 右
            P.slab(2.12, 3.98, 1.3, 0.76, 0.12, 0.78, BD)]      # 後ろ


def bed_img(t, dur, expr, dark=0.0, extra=(), push=0.25):
    img = Q.room_img(kanata_phone_bed(expr), Q.face_cam(t, dur, push), list(extra) + blanket())
    if dark > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 40, int(170 * dark))))
    return img


# ---------- 文字 ----------
def clock(img, time_, n=3, date=DAY, grade="大学1年", pulse=0.0):
    O.clock_big(img, date, time_, grade=grade)
    O.counter(img, n, pulse)


def pill(img, text, y, size, bg, fg=(255, 255, 255), u=1.0):
    if u <= 0:
        return
    f = O.F(BLACK, size)
    w = f.getlength(text) + size
    bd = Image.new("RGBA", (int(w), int(size * 1.5)), (0, 0, 0, 0))
    ImageDraw.Draw(bd).rounded_rectangle([0, 0, w - 1, size * 1.5 - 1], radius=int(size * 0.75), fill=bg)
    ImageDraw.Draw(bd).text((size / 2, size * 0.14), text, font=f, fill=fg)
    E.paste_center(img, bd, 540, y, E.pop(u))


def note(img, text, y=1530):
    f = O.F(BOLD, 30)
    w = f.getlength(text) + 36
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle([540 - w / 2, y, 540 + w / 2, y + 48], radius=12, fill=(0, 0, 0, 150))
    img.alpha_composite(lay)
    ImageDraw.Draw(img).text((540 - w / 2 + 18, y + 6), text, font=f, fill=(235, 238, 245))


def msg_card(img, u, head, lines, y0=700):
    """スマホのメッセージ（ミオから）"""
    if u <= 0:
        return
    e = ease(min(1, u))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    f, fh = O.F(BLACK, 46), O.F(BOLD, 32)
    h = 90 + 64 * len(lines)
    y0 = y0 + (1 - e) * 30
    d.rounded_rectangle([90, y0, W - 90, y0 + h], radius=36, fill=(250, 250, 252, int(240 * e)))
    d.text((130, y0 + 24), head, font=fh, fill=(255, 138, 31, int(255 * e)))
    for j, ln in enumerate(lines):
        d.text((130, y0 + 76 + j * 64), ln, font=f, fill=(40, 40, 50, int(255 * e)))
    img.alpha_composite(lay)


def hook(img, t):
    if t < 2.4:
        im = E.fit_text(["2次選考会の時間。", "ぼくは、布団の中。"], 110, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={1: RED})
        E.paste_center(img, im, 540, 1000, E.pop(t))
    elif t < 4.4:
        im = E.fit_text(["ガクチカ・ループ 第4話", "布団から、出られない。"], 90, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=10, hl={1: YEL})
        E.paste_center(img, im, 540, 1000, E.pop(t - 2.4))


# ---------- 1コマ ----------
def room2_img(cam, mio, mo_talk=False, t=0.0):
    mo = morishita_seat()
    if mo_talk:
        mo.set(head_pitch=0.04 * math.sin(t * 6))
    img, _ = render(ROOM2 + mo.boxes() + host_seat().boxes() + mio.boxes(), cam, R.BG_MEET)
    return img.convert("RGBA")


def frame(s, t):
    n = s.name
    sid = speaking(s, t)
    if n == "cold":
        img = bed_img(t, s.dur, "blank", dark=0.35, push=0.4)
        if int(t * 6) % 3 == 0:   # スマホが震える光
            img.alpha_composite(Image.new("RGBA", (W, H), (120, 170, 255, 26)))
        clock(img, "10:00")
        hook(img, t)
    elif n == "room2":
        a, b = (x[0] for x in s.lines)
        u = ease(t / s.dur)
        mio = mio_stand(armR=1.9 if t > b - 0.2 else 0.05, head_pitch=0.2 if t > b - 0.2 else 0.0)
        if t < b - 0.1:   # 空いた席の後ろから、議員さんと活動先の方
            cam = Camera((lerp(3.4, 3.35, u), lerp(0.3, 0.7, u), 1.55), (3.0, 5.5, 0.85), 50)
        else:             # 電話をかけるミオ
            cam = Camera((3.3, 1.6, 1.6), (4.7, 3.4, 1.55), 40)
        img = room2_img(cam, mio, sid == "02", t)
        clock(img, "10:00")
        if t < b - 0.1:
            pill(img, "2次選考会", 1010, 46, (64, 110, 220), u=(t - 0.2) / 0.3)
            pill(img, "カナタの席だけ、空いている。", 1105, 50, (200, 50, 60), u=(t - 0.7) / 0.3)
        note(img, "※2次選考会は、受け入れ先の方と日程を合わせて行います")
    elif n == "bed":
        a, b = (x[0] for x in s.lines)
        img = bed_img(t, s.dur, "normal" if t < b else "shock", dark=0.3, push=0.2)
        clock(img, "10:05")
        if t < b - 0.2:
            msg_card(img, (t - 0.2) / 0.3, "ミオ（昨日 21:30）",
                     ["2次選考会で話すのは、", "1次選考会でも話した", "興味あること・やりたいこと。", "なぜやりたいのかも、", "そのまま話せばいいんだよ"], y0=640)
    elif n == "tokei":
        a, b = (x[0] for x in s.lines)
        tk = Q.tokei_near(t, "angry" if sid == "06" else "eyes", t - 0.2)
        k = kanata_phone_bed("normal" if t < b else "sleep")
        img = Q.room_img(k, Q.face_cam(t, s.dur, 0.2), list(tk) + blanket())
        img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 40, 50)))
        clock(img, "10:20")
    elif n == "bow":
        u = ease(t / s.dur)
        bow = ease(min(1, max(0, t - 0.6) / 0.6))
        mio = mio_stand((4.9, 4.2, 0), 0.9, lean=0.5 * bow, head_pitch=0.4 * bow)
        cam = Camera((lerp(6.3, 6.2, u), lerp(0.9, 1.1, u), 1.9), (3.5, 5.0, 1.0), 52)
        img = room2_img(cam, mio)
        clock(img, "10:40")
        O.caption(img, "カナタの代わりに、\nミオが頭を下げた。", 1070, t - 0.8, size=68)
    elif n == "ff":
        # 早回し：10:40 → 18:00。部屋が暗くなり、伏せたスマホに未読が増える
        a = s.lines[0][0]
        p = min(1, t / (a - 0.3))
        mins = int(lerp(10 * 60 + 40, 18 * 60, ease(p)))
        img = bed_img(t, s.dur, "sleep", dark=0.25 + 0.6 * p, push=0.1)
        clock(img, f"{mins // 60}:{mins % 60:02d}")
        if t > 0.3:
            Q.big_word(img, "何もしない一日", t - 0.3, RED, y=900, size=110)
        if t > 0.8:
            pill(img, f"未読 {min(9, 1 + int(p * 9))}", 1080, 50, (200, 50, 60), u=(t - 0.8) / 0.3)
        if t > a - 0.2:
            img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(200 * min(1, (t - a + 0.2) / 0.8)))))
    elif n == "iv":
        iv, k = P.iv_rig(), P.kanata_suit_rig()
        k.expr = "blank"
        if sid == "10":
            iv.set(armL=0.55 + 0.25 * math.sin(t * 7))
        u = ease(t / s.dur)
        if t < s.rev - 0.4:
            cam = Camera((lerp(3.75, 3.6, u), lerp(0.55, 1.0, u), 1.62), (3.0, 5.5, 1.38), 48)
        else:
            cam = Camera((3.4, 4.1, 1.52), (3.0, 2.1, 1.42), 44)
        img, _ = render(P.OFFICE + iv.boxes() + k.boxes(), cam, P.BG_OFFICE)
        img = img.convert("RGBA")
        after = t > s.rev
        if after:
            img.alpha_composite(Image.new("RGBA", (W, H), (20, 0, 10, int(120 * min(1, (t - s.rev) / 0.4)))))
        O.clock_big(img, "2029年6月1日（金）", "10:00", grade="大学4年")
        O.counter(img, 2 if after else 3, 1.0 if after else 0.0)
        if after:
            im = E.fit_text(["残りループ", "3 → 2"], 140, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=14, hl={1: RED})
            E.paste_center(img, im, 540, 1000, E.pop(t - s.rev))
        if s.rev - 0.9 < t < s.rev:
            Q.big_word(img, "……", t - s.rev + 0.9, (255, 255, 255), y=1060, size=120)
    elif n == "wake":
        a, b, c, d_ = (x[0] for x in s.lines)
        k = kanata_phone_bed("shock" if t < b else ("normal" if t < c else "resolve"))   # 最後は笑わず、決心の顔
        tk = Q.tokei_near(t, "eyes", t - d_ + 0.6, (2.93, 3.2, 1.55)) if t > d_ - 0.6 else []
        img = Q.room_img(k, Q.face_cam(t, s.dur, 0.3), tk)
        O.clock_big(img, "2026年12月5日（土）", "8:00", grade="大学1年")
        O.counter(img, 2, 1.0 if t < 1.0 else 0.0)
    elif n == "end":
        img = P.end_scene(s, t)
        O.caption(img, "あなたなら、", 560, t, size=84)
        O.caption(img, "こわい日、どうする？", 680, t, size=96, col=YEL)
        for txt, y, sz, col, path in ((["コメントで教えてね"], 860, 64, (255, 255, 255), BLACK),
                                      (["2次選考会：受け入れ先の方と日程を合わせて行います"], 1000, 38, (200, 210, 235), BOLD),
                                      (["次回 第5話「自己PRが空欄」"], 1130, 50, (255, 255, 255), BLACK),
                                      (["ドットジェイピー広島第一支部", "春インターン申込は12月31日まで"], 1270, 48, YEL, BLACK),
                                      (["この物語はフィクションです"], 1400, 28, (180, 186, 210), BOLD)):
            E.paste_center(img, E.fit_text(txt, sz, 1000, fill=col, sw=6, path=path), 540, y, E.pop(t - 0.3))
    if sid and sid != "04":   # 04はメッセージ画面で読ませる
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
