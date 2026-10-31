"""ガクチカ・ループ 第1話（寄りのカメラ版）。python3 ep1c.py still <shot> <t> | build"""
import math, os, random, subprocess, sys
from PIL import Image, ImageDraw
import g3d as G
from g3d import Camera, Rig, render, box_aabb, hexc, add
import characters as C
import ep1b as O  # 文字・音・タイミングを流用
from engine import lerp, ease
import engine as E

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))


def jit(c, seed, amt=0.05):
    r = random.Random(seed)
    k = 1 + r.uniform(-amt, amt)
    return tuple(max(0, min(255, int(v * k))) for v in c)


def blocks(x0, x1, y0, y1, z0, z1, color, amt=0.04, seed=0):
    """整数グリッドの1ブロックずつ（色を少しずつ変える）"""
    out = []
    for x in range(x0, x1):
        for y in range(y0, y1):
            for z in range(z0, z1):
                out.append(box_aabb(x, y, z, 1, 1, 1, jit(color, hash((x, y, z, seed)) & 0xffff, amt)))
    return out


def slab(x, y, z, w, d, h, color, tag=None, glow=False, tex=None):
    return box_aabb(x, y, z, w, d, h, color, tex, tag, glow)


# ---------- 面接室 ----------
WALL = hexc("#eef0f2")
FLOOR = hexc("#9aa0a8")
WOOD = hexc("#7a5434")
GLASS = hexc("#bcdcf2")


def office():
    S = []
    S += blocks(-1, 7, -2, 8, -1, 0, FLOOR, 0.05, 1)                 # 床
    S += blocks(-1, 7, 8, 9, 0, 4, WALL, 0.025, 2)                   # 奥の壁
    S += blocks(-2, -1, -2, 8, 0, 4, WALL, 0.025, 3)                 # 左の壁
    S += blocks(7, 8, -2, 8, 0, 4, WALL, 0.025, 4)                   # 右の壁
    S += blocks(-1, 7, -3, -2, 0, 4, WALL, 0.025, 5)                 # 手前の壁
    S += blocks(-1, 7, -2, 8, 4, 5, hexc("#f6f6f6"), 0.02, 6)        # 天井
    for x in (0.6, 4.6):                                             # 奥の窓
        S.append(slab(x, 7.96, 1.2, 1.6, 0.05, 1.5, GLASS, glow=True))
    S.append(slab(-1.04, 1.0, 0.0, 0.05, 1.0, 2.1, hexc("#8a6a4a")))   # 左のドア
    S.append(slab(1.8, 4.3, 0.0, 2.4, 0.6, 0.75, WOOD))              # 机
    S.append(slab(1.75, 4.25, 0.72, 2.5, 0.7, 0.06, hexc("#6a4628")))
    S.append(slab(2.2, 4.4, 0.78, 0.35, 0.25, 0.01, hexc("#ffffff")))  # 書類
    S.append(slab(3.4, 4.45, 0.78, 0.3, 0.22, 0.01, hexc("#ffffff")))
    S.append(slab(2.75, 5.25, 0, 0.5, 0.5, 0.5, hexc("#2a2a30")))     # 面接官の椅子
    S.append(slab(2.75, 1.85, 0, 0.5, 0.5, 0.5, hexc("#2a2a30")))     # カナタの椅子
    S.append(slab(5.6, 7.2, 0, 0.6, 0.6, 0.5, hexc("#6a4a30")))       # 観葉植物
    S.append(slab(5.55, 7.15, 0.5, 0.7, 0.7, 1.0, hexc("#4a9a4a")))
    return S


OFFICE = office()


def iv_rig():
    r = Rig(C.INTERVIEWER, (3.0, 5.5, 0), math.pi, tag="iv")
    r.set(sit=True)
    return r


def kanata_suit_rig():
    r = Rig(C.KANATA_SUIT, (3.0, 2.1, 0), 0.0, tag="kanata")
    r.set(sit=True, armL=0.5, armR=0.5)
    return r


# ---------- カナタの部屋 ----------
def phone_parts(e="normal"):
    return C.kanata_parts(e, "hoodie") + [
        dict(bone="body", off=(-0.13, 0.3, 0.12), size=(0.26, 0.035, 0.38), color=hexc("#16161a"),
             tex={"back": (["l"], {"l": hexc("#cfe6ff")})})]


KANATA_PHONE = dict(name="kanata", label="カナタ（スマホ）", parts=phone_parts)


def room():
    S = []
    S += blocks(-1, 6, -2, 6, -1, 0, hexc("#a87a4e"), 0.07, 11)      # 木の床
    S += blocks(-1, 6, 6, 7, 0, 4, hexc("#efe2c4"), 0.03, 12)        # 奥の壁
    S += blocks(-2, -1, -2, 6, 0, 4, hexc("#efe2c4"), 0.03, 13)      # 左の壁
    S += blocks(6, 7, -2, 6, 0, 4, hexc("#efe2c4"), 0.03, 14)        # 右の壁
    S += blocks(-1, 6, -3, -2, 0, 4, hexc("#efe2c4"), 0.03, 15)
    S += blocks(-1, 6, -2, 6, 4, 5, hexc("#f4ecd8"), 0.02, 16)
    S.append(slab(0.8, 5.96, 1.3, 1.6, 0.05, 1.3, hexc("#9fd0f4"), glow=True))   # 窓（朝）
    S.append(slab(1.2, 3.3, 0, 2.6, 2.7, 0.45, hexc("#f2f2f2")))                 # ベッド
    S.append(slab(1.15, 4.3, 0.45, 2.7, 1.75, 0.12, hexc("#3a68c8")))            # 掛け布団
    S.append(slab(1.6, 5.4, 0.45, 1.8, 0.5, 0.18, hexc("#ffffff")))              # 枕
    S.append(slab(4.2, 4.6, 0, 0.7, 0.7, 0.6, hexc("#6a4628")))                  # ベッド横の台
    S.append(slab(-0.9, 1.0, 0, 0.6, 1.6, 0.5, hexc("#3a2a20")))                 # テレビ台
    S.append(slab(-0.85, 1.1, 0.5, 0.15, 1.4, 0.85, hexc("#121216")))            # テレビ
    S.append(slab(4.9, 0.6, 0, 0.6, 0.6, 0.4, hexc("#6a4a30")))                  # 観葉植物
    S.append(slab(4.85, 0.55, 0.4, 0.7, 0.7, 0.9, hexc("#4a9a4a")))
    return S


ROOM = room()


def alarm(t, ring):
    """ベッド横の目覚まし（光る）"""
    j = 0.02 if ring and int(t * 10) % 2 else 0
    return [slab(4.35 + j, 4.75, 0.6, 0.35, 0.25, 0.32, hexc("#facc3c")),
            slab(4.4 + j, 4.74, 0.65, 0.25, 0.02, 0.22, hexc("#fff6c0") if ring else hexc("#fbfbf6"), glow=ring)]


def kanata_room_rig():
    r = Rig(KANATA_PHONE, (2.5, 3.75, 0), math.pi, tag="kanata")
    r.set(sit=True, armL=0.75, armR=0.75, head_pitch=0.3)
    r.pos = (2.5, 3.75, 0.2)
    return r


# ---------- 描画 ----------
BG_OFFICE = E.sky((220, 228, 240), (240, 244, 250)).convert("RGB").resize((W * G.SS, H * G.SS))
BG_ROOM = E.sky((120, 190, 245), (205, 235, 255)).convert("RGB").resize((W * G.SS, H * G.SS))
BG_DARK = Image.new("RGB", (W * G.SS, H * G.SS), (12, 14, 32))


def desat_keep(img, k, mask):
    img = img.convert("RGBA")
    return O.desat(img, k, mask)


SH = O.plan()


def shot(name):
    return next(s for s in SH if s.name == name)


def interview_scene(s, t):
    iv, k = iv_rig(), kanata_suit_rig()
    sid = O.speaking(s, t)
    tf = s.tf
    frozen = t >= tf
    tt = min(t, tf)
    if sid == "01" and not frozen:
        iv.set(armL=0.55 + 0.25 * math.sin(tt * 7), head_pitch=0.05 * math.sin(tt * 3))
    l2 = s.lines[1][0]
    if t < l2:
        k.expr = "open"
        cam_from = (3.75, 0.55, 1.62)
        cam_to = (3.6, 1.0, 1.6)
        u = ease(t / l2)
        cam = Camera(tuple(lerp(a, b, u) for a, b in zip(cam_from, cam_to)), (3.0, 5.5, 1.38), 48)
    else:
        k.expr = "blank"
        k.set(head_pitch=-0.05)
        u = ease((t - l2) / (s.dur - l2))
        cam = Camera((lerp(3.42, 3.36, u), lerp(4.25, 3.95, u), 1.52), (3.0, 2.1, 1.42), 44)
    boxes = OFFICE + iv.boxes() + k.boxes()
    img, mask = render(boxes, cam, BG_OFFICE, keep={"kanata"})
    if frozen:
        dk = ease((t - tf) / 0.9)
        img = desat_keep(img, dk * 0.95, mask)
        if t - tf < 0.25:
            img = Image.blend(img, Image.new("RGBA", (W, H), (255, 255, 255, 255)), 0.35 * (1 - (t - tf) / 0.25))
    return img.convert("RGBA")


def tokei_scene(s, t, rules=False):
    iv, k = iv_rig(), kanata_suit_rig()
    sid = O.speaking(s, t)
    tkpos = (3.62, 2.05, 1.62)
    if not rules:
        drop = (1 - ease((t - 0.3) / 0.5)) * 1.6 if t > 0.3 else None
        k.expr = "blank"
        b = s.lines[1][0]
        if t > b:
            k.expr = "shock"
            k.set(head_yaw=-0.55, lean=-0.08)
        tk = C.tokei_boxes(add(tkpos, (0, 0, drop)), t, "eyes" if sid == "03" else "normal", 0.75, 0.35) if drop is not None else []
        cam = Camera((3.45, 4.75, 1.62), (3.3, 2.05, 1.45), 44)
    else:
        k.expr = "shock"
        k.set(head_yaw=-0.55)
        tk = C.tokei_boxes(tkpos, t + 5, "eyes" if sid in ("05", "06") else "normal", 0.75, 0.3)
        cam = Camera((3.62, 3.9, 1.75), (3.55, 2.05, 1.3), 50)
    boxes = OFFICE + iv.boxes() + k.boxes() + tk
    img, mask = render(boxes, cam, BG_OFFICE, keep={"kanata", "tokei"})
    img = desat_keep(img, 0.95, mask)
    return img.convert("RGBA")


def room_scene(s, t):
    k = kanata_room_rig()
    sid = O.speaking(s, t)
    if s.name == "room":
        ring = t < 1.6
        k.expr = "normal" if t < s.lines[1][0] else "open"
        u = ease(t / s.dur)
        cam = Camera((lerp(2.9, 2.8, u), lerp(0.45, 0.8, u), 1.6), (2.5, 3.75, 1.38), 46)
    else:
        ring = False
        k.expr = "open" if t > 0.3 else "normal"
        k.set(head_pitch=0.12)
        u = ease(t / s.dur)
        cam = Camera((lerp(2.98, 2.9, u), lerp(1.6, 1.85, u), 1.62), (2.5, 3.75, 1.78), 44)
    boxes = ROOM + k.boxes() + alarm(t, ring)
    img, _ = render(boxes, cam, BG_ROOM)
    return img.convert("RGBA")


def end_scene(s, t):
    cam = Camera((0, -3.4, 0.0), (0, 0, -0.9), 40)
    img, _ = render(C.tokei_boxes((0, 0, 0), t, "eyes", 1.0, math.pi), cam, BG_DARK)
    return img.convert("RGBA")


def frame(s, t, raw=False):
    n = s.name
    if n == "interview":
        img = interview_scene(s, t)
    elif n == "tokei":
        img = tokei_scene(s, t)
    elif n == "rules":
        img = tokei_scene(s, t, rules=True)
    elif n in ("room", "phone"):
        img = room_scene(s, t)
    elif n == "end":
        img = end_scene(s, t)
    elif n == "rewind":
        t0 = s.lines[0][0] + O.L("07")
        rs = shot("rules")
        if t < t0:
            img = frame(rs, rs.dur - 0.05, raw=True)
        elif t < t0 + 0.35:
            img = O.desat(frame(rs, rs.dur - 0.05, raw=True), 1)
            O.cracks(img, ease((t - t0) / 0.35))
        else:
            u = (t - t0 - 0.35) / (s.dur - t0 - 0.6)
            if u < 1:
                seq = [shot("rules"), shot("tokei"), shot("interview")]
                idx = min(2, int(u * 3))
                v = u * 3 - idx
                src = seq[idx]
                img = O.glitch(O.desat(frame(src, src.dur * (1 - v), raw=True), 1), 1.0, int(t * 30))
            else:
                w = (t - (s.dur - 0.25)) / 0.25
                img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
                if w > 0:
                    img = Image.blend(img, frame(shot("room"), 0, raw=True), min(1, w))
    if raw:
        return img
    # ---- 文字 ----
    tf = shot("interview").tf
    if n == "interview":
        frozen = t >= s.tf
        sec = int(t) if not frozen else int(s.tf)
        O.clock_big(img, "2029年6月1日（金）", f"10:00:{sec:02d}", flash=1 if frozen else 0, grade="大学4年")
        if t < s.lines[1][0]:
            im = E.fit_text(["学生時代に", "力を入れたことは？"], 112, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=12, hl={1: (255, 216, 77)})
            E.paste_center(img, im, 540, 1380, E.pop(t))
        if frozen and t > s.tf + 0.5:
            O.caption(img, "…あなたは、答えられる？", 1300, t - s.tf - 0.5, size=92, col=(255, 216, 77))
    elif n == "tokei":
        O.clock_big(img, "2029年6月1日（金）", f"10:00:{int(tf):02d}", flash=1, grade="大学4年")
    elif n == "rules":
        tb = s.lines[1][0]
        O.rule_card(img, 1 if t < s.lines[0][0] + O.L("05") * 0.5 else 2, ease((t - 0.2) / 0.3))
        if t > tb:
            O.counter(img, 3, pulse=max(0, 1 - (t - tb) / 0.8))
    elif n == "rewind":
        t0 = s.lines[0][0] + O.L("07")
        if t0 + 0.35 < t < s.dur - 0.25:
            u = (t - t0 - 0.35) / (s.dur - t0 - 0.6)
            year = 2029 - min(3, int(u * 4))
            O.caption(img, f"{year}", 900, 1.0, size=230, col=(255, 216, 77))
            O.caption(img, "◀◀ 巻き戻し中", 1120, 1.0, size=70)
    elif n in ("room", "phone"):
        O.clock_big(img, "2026年12月5日（土）", "8:00", grade="大学1年")
        O.counter(img, 3)
        if n == "room" and t < s.lines[1][0]:
            O.phone_bubble(img, (t - (s.lines[0][0] - 0.25)) / 0.3)
    elif n == "end":
        d = ImageDraw.Draw(img)
        O.caption(img, "次のループ、どうする？", 620, t, size=84)
        fa, fb = O.F(O.BLACK, 120), O.F(O.BLACK, 50)
        for i, (lab, txt, col) in enumerate((("A", "説明会に出る", (255, 138, 31)), ("B", "もう一度寝る", (110, 116, 140)))):
            x0 = 70 + i * 485
            u = ease((t - 0.3 - i * 0.15) / 0.3)
            if u <= 0:
                continue
            y0 = 760 + (1 - u) * 60
            d.rounded_rectangle([x0, y0, x0 + 455, y0 + 300], radius=40, fill=col)
            d.text((x0 + 227 - fa.getlength(lab) / 2, y0 + 20), lab, font=fa, fill=(255, 255, 255))
            d.text((x0 + 227 - fb.getlength(txt) / 2, y0 + 200), txt, font=fb, fill=(255, 255, 255))
        for txt, y, sz, col, path in ((["コメントで AかB を書いてね"], 1150, 56, (255, 216, 77), O.BLACK),
                                      (["あなたの「力を入れたこと」は、まだ作れる。"], 1290, 46, (255, 255, 255), O.BOLD),
                                      (["ドットジェイピー広島第一支部", "春インターン申込は12月31日まで"], 1420, 48, (255, 216, 77), O.BLACK),
                                      (["この物語はフィクションです"], 1530, 28, (180, 186, 210), O.BOLD)):
            E.paste_center(img, E.fit_text(txt, sz, 1000, fill=col, sw=6, path=path), 540, y)
    sid = O.speaking(s, t)
    if sid and n != "end" and sid not in ("08", "01"):
        O.subtitle(img, sid)
    return img


def render_shot(i):
    s = SH[i]
    n = int(round(s.dur * FPS))
    out = f"{HERE}/out3/{i:02d}_{s.name}.mp4"
    tmp = out[:-4] + ".part.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for k in range(n):
        p.stdin.write(frame(s, k / FPS).convert("RGB").tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, out)
    return out, n


if __name__ == "__main__":
    os.makedirs(f"{HERE}/out3", exist_ok=True)
    if sys.argv[1] == "still":
        frame(shot(sys.argv[2]), float(sys.argv[3])).convert("RGB").save(f"{HERE}/s3_{sys.argv[2]}_{sys.argv[3]}.png")
    elif sys.argv[1] == "build":
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(2) as ex:
            res = list(ex.map(render_shot, range(len(SH))))
        t = 0
        for s, (_, n) in zip(SH, res):
            s.start, s.dur = t, n / FPS
            t += s.dur
        open(f"{HERE}/out3/list.txt", "w").write("".join(f"file '{o}'\n" for o, _ in res))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{HERE}/out3/list.txt", "-c", "copy", f"{HERE}/out3/video.mp4"], check=True)
        a = O.mix(SH)
        final = f"{HERE}/out3/ガクチカループ_第1話.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{HERE}/out3/video.mp4", "-i", a, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "160k", "-shortest", final + ".part.mp4"], check=True)
        os.replace(final + ".part.mp4", final)
        print("done", round(t, 2))
