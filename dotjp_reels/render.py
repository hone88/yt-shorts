"""使い方:
  python3 render.py still r1 03 0.6 a.png  # r1 の場面03 を、長さの 60% の時点で静止画に
  python3 render.py scene r1 03 out.mp4    # 場面を1本の MP4 に
"""
import json, math, os, random, re, subprocess, sys, wave
from PIL import Image, ImageDraw
import engine as E
import scenes

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = json.load(open(os.path.join(HERE, "script.json"), encoding="utf-8"))
FPS = 30
TAIL = 0.35   # セリフのあとの間
BADGE = E.rounded_badge("ドットジェイピー 広島第一支部", 34)
SERIES = {"r1": "1/4", "r2": "2/4", "r3": "3/4", "r4": "4/4"}


def wav_len(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def durations(reel):
    out = []
    for s in SCRIPT["reels"][reel]["scenes"]:
        p = os.path.join(HERE, "voice", reel, s["id"] + ".wav")
        d = wav_len(p) if os.path.exists(p) else max(2.5, len(s["say"]) * 0.12)
        out.append(d + TAIL)
    return out


BREAK_AFTER = "はがをにでとものへやかね"


def split_phrase(p, maxlen=16):
    """長い句を、真ん中に近い助詞の後ろで割る。"""
    if len(p) <= maxlen:
        return [p]
    mid = len(p) / 2
    best, best_score = None, 1e9
    for i in range(3, len(p) - 2):
        if p[i - 1] in BREAK_AFTER and p[i] not in "ぁぃぅぇぉっゃゅょーゎ、。？！":
            score = abs(i - mid) + (0.8 if p[i - 1] in "がかやねへ" else 0)
            if best is None or score <= best_score:
                best, best_score = i, score
    if best is None or len(p[:best]) > maxlen + 2 or len(p[best:]) > maxlen + 2:
        best = int(mid)
    return split_phrase(p[:best], maxlen) + split_phrase(p[best:], maxlen)


def chunks(text):
    """字幕用に、読点・句点で区切り、1枚あたり2行（1行16文字前後）にまとめる。"""
    parts = [p for p in re.split(r"(?<=[、。？！])", text) if p.strip()]
    lines = []
    for p in parts:
        p = p.rstrip("、")
        for q in split_phrase(p):
            if lines and len(lines[-1]) + len(q) <= 16 and not lines[-1].endswith(("。", "？", "！")) and not split_needed(lines[-1]):
                lines[-1] += q
            else:
                lines.append(q)
    cards = [lines[i:i + 2] for i in range(0, len(lines), 2)]
    return cards


def split_needed(line):
    return False


def card_times(text, speech, sub=None):
    cards = [c.split("|") for c in sub.split("/")] if sub else chunks(text)
    n = [sum(len(l) for l in c) for c in cards]
    tot = sum(n)
    ts, acc = [], 0.0
    for k in n:
        ts.append(acc)
        acc += speech * k / tot
    return cards, ts


class SceneRenderer:
    def __init__(self, reel, idx):
        self.reel = reel
        sd = SCRIPT["reels"][reel]["scenes"]
        self.i = [s["id"] for s in sd].index(idx)
        self.s = sd[self.i]
        self.dur = durations(reel)[self.i]
        self.speech = self.dur - TAIL
        variant = list(SCRIPT["reels"]).index(reel)
        self.split = "top" in self.s
        if self.split:
            self.sc = scenes.make(self.s["top"], self.dur, variant)
            self.sc2 = scenes.make(self.s["bottom"], self.dur, variant)
            self.bg = E.sky(*self.sc.sky)
            self.bg2 = E.sky(*self.sc2.sky)
            self.tag1 = E.rounded_badge("なんとなくの春", 32, bg=(110, 116, 130))
            self.tag2 = E.rounded_badge("インターンの春", 32, bg=(255, 138, 31))
        else:
            self.sc = scenes.make(self.s["scene"], self.dur, variant)
            self.bg = E.sky(*self.sc.sky)
        self.timeb = E.rounded_badge(self.s["time"], 64, bg=(22, 30, 58), fg=(255, 216, 77), pad=(30, 12)) if self.s.get("time") else None
        lines = self.s["cap"].split("\n")
        self.cap = E.fit_text(lines, 96, 960, hl={len(lines) - 1: (255, 216, 77)} if len(lines) > 1 else None)
        self.cards, self.cts = card_times(self.s["say"], self.speech, self.s.get("sub"))
        self.card_imgs = [E.fit_text(c, 54, 980, sw=7, path=E.FONT_BOLD, stroke=(10, 10, 20), gap=1.25) for c in self.cards]
        self.note = None
        if self.s.get("note"):
            self.note = E.fit_text(self.s["note"].split("\n"), 34, 980, sw=6, path=E.FONT_BOLD, stroke=(10, 10, 20))
        self.labels = {}
        self.series = E.rounded_badge(SERIES[reel], 30, bg=(255, 255, 255), fg=(255, 120, 20)) if reel in SERIES else None
        rnd = random.Random(self.i)
        self.flakes = [(rnd.uniform(0, 1080), rnd.uniform(0, 1920), rnd.uniform(60, 140), rnd.uniform(4, 9)) for _ in range(90)]

    def world(self, sc, t, img, sy=None, zoom=1.0, seed=0):
        if sc.clouds:
            E.clouds(img, t, seed=seed)
        sc.update(t)
        k = sc.cam(t)
        cam = E.Cam(k[0] * zoom, k[1], k[2], k[3], 540, sy or 1010)
        boxes = list(sc.static)
        for p in sc.people:
            boxes += p.boxes()
        boxes += sc.dyn(t)
        E.draw_boxes(img, boxes, cam)

    def frame(self, t):
        if self.split:
            return self.frame_split(t)
        img = self.bg.copy()
        sc = self.sc
        if sc.clouds:
            E.clouds(img, t, seed=self.i + 3)
        sc.update(t)
        k = sc.cam(t)
        cam = E.Cam(*k)
        boxes = list(sc.static)
        for p in sc.people:
            boxes += p.boxes()
        boxes += sc.dyn(t)
        E.draw_boxes(img, boxes, cam)
        if sc.snow:
            d = ImageDraw.Draw(img)
            for (x, y, sp, sz) in self.flakes:
                yy = (y + t * sp) % 1920
                xx = x + math.sin(t + y) * 20
                d.rectangle([xx, yy, xx + sz, yy + sz], fill=(255, 255, 255, 220))
        # 上：団体名バッジ・シリーズ番号・見出し
        img.alpha_composite(BADGE, (56, 150))
        if self.series:
            img.alpha_composite(self.series, (56 + BADGE.width + 14, 150 + (BADGE.height - self.series.height) // 2))
        if self.timeb:
            img.alpha_composite(self.timeb, (1024 - self.timeb.width, 128))
        E.paste_center(img, self.cap, 540, 410, E.pop(t))
        # 下：字幕
        ci = 0
        for j, ts in enumerate(self.cts):
            if t >= ts:
                ci = j
        if t < self.speech + 0.1:
            im = self.card_imgs[ci]
            E.paste_center(img, im, 540, 1520)
        if self.note:
            E.paste_center(img, self.note, 540, 1385)
        lab = getattr(sc, "label", None)
        if lab:
            txt = lab(t)
            if txt not in self.labels:
                self.labels[txt] = E.rounded_badge(txt, 52, bg=(255, 255, 255), fg=(255, 120, 20), pad=(34, 14))
            E.paste_center(img, self.labels[txt], 540, 640)
        return img.convert("RGB")


def _overlay(self, img, t):
    img.alpha_composite(BADGE, (56, 150))
    E.paste_center(img, self.cap, 540, 395, E.pop(t))
    ci = 0
    for j, ts in enumerate(self.cts):
        if t >= ts:
            ci = j
    if t < self.speech + 0.1:
        E.paste_center(img, self.card_imgs[ci], 540, 1540)


def _frame_split(self, t):
    Y = 1035
    top = self.bg.copy()
    self.world(self.sc, t, top, sy=820, zoom=0.7 if self.s['top'].startswith('bedroom') else 0.74, seed=self.i + 3)
    bot = self.bg2.copy()
    self.world(self.sc2, t, bot, sy=1290, zoom=0.7 if self.s['bottom'].startswith('bedroom') else 0.74, seed=self.i + 7)
    img = top
    img.paste(bot.crop((0, Y, 1080, 1920)), (0, Y))
    d = ImageDraw.Draw(img)
    d.rectangle([0, Y - 4, 1080, Y + 4], fill=(255, 255, 255))
    img.alpha_composite(self.tag1, (40, 560))
    img.alpha_composite(self.tag2, (40, Y + 22))
    _overlay(self, img, t)
    return img.convert("RGB")


SceneRenderer.frame_split = _frame_split


def still(reel, idx, frac, out):
    r = SceneRenderer(reel, idx)
    r.frame(r.dur * float(frac)).save(out)


def scene_mp4(reel, idx, out):
    r = SceneRenderer(reel, idx)
    n = int(round(r.dur * FPS))
    tmp = out[:-4] + ".part.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        pr.stdin.write(r.frame(f / FPS).tobytes())
    pr.stdin.close()
    if pr.wait() == 0:
        os.replace(tmp, out)
    else:
        sys.exit("ffmpeg failed")


if __name__ == "__main__":
    if sys.argv[1] == "still":
        still(*sys.argv[2:6])
    elif sys.argv[1] == "scene":
        scene_mp4(*sys.argv[2:5])
