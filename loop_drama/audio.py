"""BGMと効果音をコードで作る（著作権の心配がない自作音源）。24kHz・モノラル。"""
import math
import numpy as np

SR = 24000


def t_(sec):
    return np.arange(int(sec * SR)) / SR


def env(n, a=0.01, r=0.2):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr and nr < n:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def note(f, sec, kind="sine", a=0.01, r=0.3, vol=0.3):
    x = t_(sec)
    if kind == "sine":
        y = np.sin(2 * np.pi * f * x)
    elif kind == "bell":   # オルゴール風
        y = (np.sin(2 * np.pi * f * x) + 0.4 * np.sin(2 * np.pi * f * 2.01 * x) + 0.2 * np.sin(2 * np.pi * f * 3.98 * x)) * np.exp(-x * 3.2)
    elif kind == "keys":   # エレピ風
        y = (np.sin(2 * np.pi * f * x) + 0.25 * np.sin(2 * np.pi * f * 2 * x)) * np.exp(-x * 1.6)
    elif kind == "pad":
        y = sum(np.sin(2 * np.pi * f * d * x) for d in (1, 1.004, 0.996)) / 3
    elif kind == "saw":
        y = 2 * ((f * x) % 1) - 1
    return y * env(len(x), a, r) * vol


def put(buf, y, at):
    i = int(at * SR)
    if i >= len(buf) or i + len(y) <= 0:
        return
    j = max(0, -i)
    y = y[j:]
    i = max(0, i)
    n = min(len(y), len(buf) - i)
    buf[i:i + n] += y[:n]


def lowpass(y, k=0.08):
    out = np.empty_like(y)
    acc = 0.0
    for i, v in enumerate(y):   # 1次の簡単なローパス
        acc += k * (v - acc)
        out[i] = acc
    return out


def noise(sec, seed=0):
    return np.random.RandomState(seed).randn(int(sec * SR))


MIDI = lambda m: 440 * 2 ** ((m - 69) / 12)

# ---------- 効果音 ----------


def sfx_tick(vol=0.25):
    x = t_(0.05)
    return (np.sin(2 * np.pi * 3200 * x) * np.exp(-x * 120) + noise(0.05, 7) * 0.3 * np.exp(-x * 200)) * vol


def sfx_heart(vol=0.6):
    out = np.zeros(int(0.6 * SR))
    for at, a in ((0, 1), (0.16, 0.7)):
        x = t_(0.18)
        put(out, np.sin(2 * np.pi * 55 * x) * np.exp(-x * 22) * a * vol, at)
    return out


def sfx_freeze():
    """世界が止まる：低い衝撃＋高い耳鳴り"""
    x = t_(2.2)
    hit = np.sin(2 * np.pi * 42 * x) * np.exp(-x * 3) * 0.9 + noise(2.2, 3) * np.exp(-x * 18) * 0.35
    ring = np.sin(2 * np.pi * 4200 * x) * 0.05 * np.minimum(1, x * 3) * np.exp(-x * 0.6)
    return hit + ring


def sfx_whoosh(sec=0.45, up=True, vol=0.35):
    n = noise(sec, 11)
    x = t_(sec)
    e = np.sin(np.pi * x / sec) ** 2
    y = lowpass(n, 0.05 + 0.25 * (x / sec if up else 1 - x / sec).mean())
    return y * e * vol * 3


def sfx_pop(vol=0.3):
    x = t_(0.12)
    f = 600 + 900 * np.exp(-x * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 30) * vol


def sfx_notify(vol=0.35):
    out = np.zeros(int(0.5 * SR))
    put(out, note(MIDI(84), 0.25, "bell", r=0.2, vol=vol), 0)
    put(out, note(MIDI(91), 0.35, "bell", r=0.3, vol=vol), 0.11)
    return out


def sfx_rewind():
    """巻き戻し：テープの逆回転"""
    x = t_(2.0)
    f = 180 + 1500 * (x / 2.0) ** 2
    y = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.08 + lowpass(noise(2.0, 5), 0.3) * 0.5
    return y * np.minimum(1, x * 4) * np.minimum(1, (2.0 - x) * 6)


def sfx_reverse_swell(sec=1.2):
    x = t_(sec)
    return lowpass(noise(sec, 9), 0.2) * (x / sec) ** 3 * 0.9


def sfx_glass():
    x = t_(0.7)
    y = sum(np.sin(2 * np.pi * f * x) for f in (2300, 3170, 4410)) * np.exp(-x * 9) * 0.12
    return y + noise(0.7, 4) * np.exp(-x * 25) * 0.4


def sfx_ding(vol=0.35):
    return note(MIDI(88), 1.0, "bell", r=0.6, vol=vol)


def sfx_alarm():
    out = []
    for _ in range(3):
        for _ in range(4):
            x = t_(0.07)
            out.append(np.sign(np.sin(2 * np.pi * 1800 * x)) * 0.14)
            out.append(np.zeros(int(0.05 * SR)))
        out.append(np.zeros(int(0.22 * SR)))
    return np.concatenate(out)


def sfx_chime_end():
    out = np.zeros(int(1.6 * SR))
    for i, m in enumerate((72, 76, 79, 84)):
        put(out, note(MIDI(m), 0.9, "bell", r=0.6, vol=0.22), i * 0.09)
    return out

# ---------- BGM ----------


def bgm_tension(sec):
    """面接：低い持続音＋ゆっくりした不安なベース"""
    out = np.zeros(int(sec * SR))
    put(out, note(MIDI(33), sec, "pad", a=1.0, r=0.3, vol=0.16), 0)
    put(out, note(MIDI(40), sec, "pad", a=1.5, r=0.3, vol=0.07), 0)
    beat = 0.0
    while beat < sec:
        put(out, note(MIDI(45), 0.5, "sine", a=0.005, r=0.4, vol=0.12), beat)
        beat += 1.0
    return out


def bgm_mystery(sec):
    """トケイ：オルゴールの短調アルペジオ＋低い持続音"""
    out = np.zeros(int(sec * SR))
    put(out, note(MIDI(38), sec, "pad", a=0.8, r=0.5, vol=0.12), 0)
    seq = [69, 72, 76, 72, 68, 71, 76, 71, 65, 69, 72, 69, 64, 68, 71, 68]
    step = 0.21
    i = 0
    tt = 0.0
    while tt < sec:
        put(out, note(MIDI(seq[i % len(seq)]), 0.6, "bell", r=0.4, vol=0.11), tt)
        i += 1
        tt += step
    return out


def bgm_morning(sec, bright=False):
    """朝の部屋：ゆるいローファイ（C–Am–F–G）"""
    out = np.zeros(int(sec * SR))
    chords = [(60, 64, 67, 71), (57, 60, 64, 67), (53, 57, 60, 64), (55, 59, 62, 65)]
    bar = 2.0
    tt, k = 0.0, 0
    while tt < sec:
        ch = chords[k % 4]
        for m in ch:
            put(out, note(MIDI(m), bar, "keys", a=0.01, r=0.5, vol=0.06), tt)
        put(out, note(MIDI(ch[0] - 24), bar, "sine", a=0.01, r=0.4, vol=0.12), tt)
        for b in range(4):
            bt = tt + b * bar / 4
            x = t_(0.25)
            put(out, np.sin(2 * np.pi * (50 + 60 * np.exp(-x * 30)) * x) * np.exp(-x * 14) * (0.28 if b % 2 == 0 else 0.0), bt)  # キック
            put(out, noise(0.05, b) * np.exp(-t_(0.05) * 90) * 0.05, bt + bar / 8)                                              # ハイハット
            if bright:
                put(out, note(MIDI(ch[(b + 1) % 4] + 12), 0.4, "bell", r=0.3, vol=0.05), bt + bar / 8)
        tt += bar
        k += 1
    return out


def duck(music, voice, amount=0.55, attack=0.05, release=0.35):
    """声が出ている間だけ音楽を下げる"""
    lvl = np.abs(voice)
    win = int(0.03 * SR)
    lvl = np.convolve(lvl, np.ones(win) / win, mode="same")
    gate = (lvl > 0.01).astype(float)
    g = np.empty_like(gate)
    acc = 0.0
    a, r = 1 / (attack * SR), 1 / (release * SR)
    for i, v in enumerate(gate):
        acc = min(v, acc + a) if v > acc else max(v, acc - r)
        g[i] = acc
    return music * (1 - amount * g)


# ====================================================================
# 参考リールの分析から足した部品（2026-10-31）
# ====================================================================
def reverb(y, decay=0.5, delays=(0.031, 0.047, 0.071, 0.097, 0.13), tail=1.2):
    """簡単な残響（余韻）"""
    out = np.concatenate([y, np.zeros(int(tail * SR))])
    src = out.copy()
    for i, d in enumerate(delays):
        n = int(d * SR)
        for k in range(1, 8):
            sh = n * k
            if sh >= len(out):
                break
            out[sh:] += src[:-sh] * (decay ** (k + i * 0.5)) * 0.35
    return out


def sfx_boom(vol=0.9, sec=2.4):
    """冒頭・劇的な場面の低い「ドン」（長い余韻）"""
    x = t_(sec)
    f = 38 + 30 * np.exp(-x * 9)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 1.6)
    y += lowpass(noise(sec, 21), 0.06) * np.exp(-x * 6) * 1.2
    return y * vol


def sfx_transition(vol=0.8):
    """場面転換の決まった音：シュッ（0.45秒）→ドン＋余韻。シリーズ全話で同じ音を使う"""
    out = np.zeros(int(2.4 * SR))
    sw = 0.45
    x = t_(sw)
    n = noise(sw, 31)
    sweep = np.zeros_like(n)
    acc, k0 = 0.0, 0.02
    for i, v in enumerate(n):
        k = k0 + 0.5 * (i / len(n)) ** 2
        acc += k * (v - acc)
        sweep[i] = acc
    put(out, sweep * (x / sw) ** 2 * 0.9, 0)
    hit = sfx_boom(1.0, 1.9)
    hit[: int(0.08 * SR)] += noise(0.08, 32) * np.exp(-t_(0.08) * 40) * 0.6
    put(out, hit, sw)
    tail = lowpass(noise(1.8, 33), 0.25) * np.exp(-t_(1.8) * 2.2) * 0.25
    put(out, tail, sw)
    return out * vol


def sfx_stopwatch(sec, interval=0.5, vol=0.2):
    """時間を数える場面の秒針（ストップウォッチ）"""
    out = np.zeros(int(sec * SR))
    t = 0.0
    while t < sec:
        put(out, sfx_tick(vol), t)
        t += interval
    return out


def sfx_riser(sec=1.2, vol=0.45):
    """答えの直前の盛り上がり（声を止めた間に鳴らす）"""
    x = t_(sec)
    f = 200 + 1600 * (x / sec) ** 2
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25 + lowpass(noise(sec, 41), 0.15) * 0.8
    return y * (x / sec) ** 2.5 * vol


def amb_radio(sec, vol=0.18):
    """無線・電話のノイズ"""
    n = noise(sec, 51)
    hi = n - lowpass(n, 0.3)
    crackle = (np.random.RandomState(52).rand(len(n)) > 0.9993) * np.random.RandomState(53).randn(len(n)) * 3
    return (hi * 0.6 + crackle) * vol


def amb_crowd(sec, vol=0.12):
    """街・会場のざわめき"""
    n = lowpass(noise(sec, 61), 0.12)
    mod = 1 + 0.4 * np.sin(2 * np.pi * 0.7 * t_(sec)) * np.sin(2 * np.pi * 0.23 * t_(sec))
    return n * mod * vol * 2


def amb_room(sec, vol=0.05):
    """部屋の空気（無音にしないための薄い音）"""
    return (lowpass(noise(sec, 71), 0.02) * 3 + np.sin(2 * np.pi * 50 * t_(sec)) * 0.1) * vol


def bgm_dark(sec):
    """暗い持続音（ドラマの土台。ずっと鳴らしておく）"""
    out = np.zeros(int(sec * SR))
    put(out, note(MIDI(31), sec, "pad", a=1.2, r=0.8, vol=0.2), 0)
    put(out, note(MIDI(38), sec, "pad", a=2.0, r=0.8, vol=0.08), 0)
    put(out, note(MIDI(43), sec, "pad", a=3.0, r=0.8, vol=0.04), 0)
    return out


def bgm_heavy(sec, bpm=100):
    """重い低音（緊張が高まる場面）"""
    out = bgm_dark(sec) * 0.7
    beat = 60 / bpm
    t = 0.0
    while t < sec:
        x = t_(0.4)
        put(out, np.sin(2 * np.pi * (45 + 40 * np.exp(-x * 25)) * x) * np.exp(-x * 7) * 0.45, t)
        t += beat
    return out


def bgm_sparse(sec):
    """静かな場面：ぽつぽつピアノ"""
    out = np.zeros(int(sec * SR))
    seq = [64, 67, 71, 69, 64, 62]
    t, i = 0.3, 0
    while t < sec:
        put(out, note(MIDI(seq[i % len(seq)]), 2.0, "keys", r=1.2, vol=0.07), t)
        t += 1.6
        i += 1
    return out


def fade(y, fin=0.0, fout=0.0):
    y = y.copy()
    n = len(y)
    if fin:
        k = min(n, int(fin * SR)); y[:k] *= np.linspace(0, 1, k)
    if fout:
        k = min(n, int(fout * SR)); y[-k:] *= np.linspace(1, 0, k)
    return y
