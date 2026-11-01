import numpy as np, wave

SR = 44100
DUR = 41.09
N = int(SR * DUR)
rng = np.random.default_rng(7)


def t_(d):
    return np.arange(int(SR * d)) / SR


def lp(x, cut):
    a = np.exp(-2 * np.pi * cut / SR)
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)):  # small signals only
        s = (1 - a) * x[i] + a * s; y[i] = s
    return y


def lp_fast(x, cut, n=2):
    # repeated moving average ~ low-pass (fast, for long buffers)
    k = max(1, int(SR / cut / 2))
    for _ in range(n):
        c = np.cumsum(np.concatenate([[0.0], x]))
        x = (c[k:] - c[:-k]) / k
        x = np.concatenate([x, np.zeros(k - 1)])
    return x


def env(n, a, r):
    e = np.ones(n)
    na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def put(buf, x, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= len(buf): return
    x = x[: len(buf) - i]
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * gain * l * 1.414
    buf[i:i + len(x), 1] += x * gain * r * 1.414


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


# ---------------------------------------------------------------- BGM
bgm = np.zeros((N, 2))
BPM = 100; beat = 60 / BPM; bar = 4 * beat
chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
arp_pat = [0, 1, 2, 1, 0, 2, 1, 2]


def pad_note(f, d):
    t = t_(d)
    x = sum(np.sin(2 * np.pi * f * k * t + rng.uniform(0, 6)) / k ** 1.6 for k in (1, 2, 3))
    x += 0.5 * np.sin(2 * np.pi * f * 1.004 * t)
    trem = 1 + 0.15 * np.sin(2 * np.pi * 0.25 * t)
    return x * trem * env(len(t), 0.6, 0.8)


def pluck(f, d=0.5):
    t = t_(d)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 7)


def kick():
    t = t_(0.35)
    f = 50 + 90 * np.exp(-t * 25)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def hat():
    t = t_(0.06)
    n = rng.normal(0, 1, len(t)); n = n - lp_fast(n, 3000, 1)
    return n * np.exp(-t * 60)


bars = int(np.ceil(DUR / bar)) + 1
for b in range(bars):
    t0 = b * bar
    ch = chords[b % 4]
    intensity = 1.0
    for m in ch:
        put(bgm, pad_note(midi(m), bar + 0.6), t0, 0.06, pan=-0.3 + 0.3 * ch.index(m))
    put(bgm, pad_note(midi(ch[0] - 12), bar + 0.6), t0, 0.07)
    for k in range(8):
        tt = t0 + k * beat / 2
        if tt > 34.0: break                     # last scene: pad only
        note = ch[arp_pat[k]] + 12
        put(bgm, pluck(midi(note)), tt, 0.05, pan=0.4 if k % 2 else -0.4)
    for k in range(4):
        tt = t0 + k * beat
        if 2.6 < tt < 34.0:
            if k in (0, 2):
                put(bgm, kick(), tt, 0.22 if tt > 28.1 else 0.15)
            put(bgm, hat(), tt + beat / 2, 0.05)
# fade in/out
fade = np.ones(N); fi = int(0.3 * SR); fo = int(2.0 * SR)
fade[:fi] = np.linspace(0.3, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]

# ---------------------------------------------------------------- SFX
sfx = np.zeros((N, 2))


def noise(d):
    return rng.normal(0, 1, int(SR * d))


def sweep(f0, f1, d, wave_='sine'):
    t = t_(d)
    f = f0 * (f1 / f0) ** (t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) if wave_ == 'sine' else np.sign(np.sin(ph))


def whoosh(d, up=True, bright=1.0):
    n = noise(d)
    t = t_(d)
    lo = lp_fast(n, 600 * bright); hi = lp_fast(n, 2500 * bright)
    band = hi - lo
    shape = np.sin(np.pi * t / d) ** 2
    mix = (t / d) if up else (1 - t / d)
    return (band * (0.4 + 0.6 * mix) + lo * 0.3) * shape


def glitch():
    d = 0.32
    x = sweep(900, 120, d, 'square') * 0.5 + noise(d) * 0.4
    x = np.round(x * 4) / 4                                    # crunchy
    gate = (np.floor(t_(d) * 40) % 2 == 0).astype(float)
    return x * gate * np.exp(-t_(d) * 6)


def buzzer():
    out = []
    for _ in range(2):
        t = t_(0.16)
        out.append((np.sign(np.sin(2 * np.pi * 155 * t)) * 0.6 + np.sign(np.sin(2 * np.pi * 157 * t)) * 0.4) * env(len(t), 0.005, 0.03))
        out.append(np.zeros(int(0.05 * SR)))
    return lp_fast(np.concatenate(out), 2500, 1)


def chime(f=1318.5, d=1.6):
    t = t_(d)
    return sum(np.sin(2 * np.pi * f * k * t) * np.exp(-t * (3 + 2 * k)) / k for k in (1, 2.01, 3.03))


def boom():
    t = t_(1.4)
    f = 40 + 60 * np.exp(-t * 8)
    low = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.5)
    crack = lp_fast(noise(1.4), 1800, 1) * np.exp(-t * 10)
    return low * 1.0 + crack * 0.6


def thud():
    t = t_(0.5)
    f = 60 + 80 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 10) + lp_fast(noise(0.5), 900, 1) * np.exp(-t * 18) * 0.8


def tick():
    t = t_(0.05)
    return np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 120)


# scene 1 / 7: gravity vanishes (glitch)
put(sfx, glitch(), 0.70, 0.35)
put(sfx, sweep(300, 1400, 0.9) * env(int(0.9 * SR), 0.05, 0.6), 0.75, 0.06)    # floaty shimmer
put(sfx, glitch(), 34.70, 0.35)
put(sfx, sweep(300, 1400, 0.9) * env(int(0.9 * SR), 0.05, 0.6), 34.75, 0.06)
# scene 2: flies to space?  -> buzzer
put(sfx, whoosh(0.7, True, 1.4), 2.66, 0.55, pan=0.2)
put(sfx, buzzer(), 3.27, 0.22)
# scene 3: to earth, then close-up and the 2cm ruler
put(sfx, whoosh(1.0, False, 0.8), 6.6, 0.4)
put(sfx, whoosh(0.6, True, 1.2), 12.3, 0.35)
for i in range(16):
    put(sfx, tick(), 12.6 + i * 0.23, 0.10 + 0.01 * i, pan=0.3)
put(sfx, chime(), 16.26, 0.18)
# scene 4: jump keeps rising
put(sfx, whoosh(0.4, False, 1.0), 18.25, 0.25)
put(sfx, sweep(180, 700, 0.45) * env(int(0.45 * SR), 0.01, 0.2), 18.55, 0.18)
rise = sweep(500, 1100, 4.8) * env(int(4.8 * SR), 0.6, 1.5) * (1 + 0.3 * np.sin(2 * np.pi * 5 * t_(4.8)))
put(sfx, rise, 18.9, 0.035)
# scene 5: throw, then the fountain
put(sfx, whoosh(0.5, True, 1.6), 23.75, 0.45, pan=0.4)
spray = lp_fast(noise(2.3), 4000, 1) - lp_fast(noise(2.3), 500, 1) * 0
put(sfx, spray * env(len(spray), 0.15, 0.5), 25.85, 0.10)
put(sfx, whoosh(0.4, True, 1.0), 25.75, 0.2)
# scene 6: gravity returns -> boom, falling whistle, landing
put(sfx, whoosh(0.9, True, 1.0) * np.linspace(0.2, 1, int(0.9 * SR)), 27.55, 0.35)
put(sfx, boom(), 28.43, 0.55)
fall = sweep(1500, 380, 3.1) * env(int(3.1 * SR), 0.2, 0.15)
put(sfx, fall, 30.05, 0.06)
put(sfx, thud(), 33.20, 0.55)
# scene 7: the question
put(sfx, chime(987.8, 2.5), 34.15, 0.10)


def write(name, x):
    x = np.clip(x, -1, 1)
    with wave.open(name, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())


print('bgm peak', np.abs(bgm).max(), 'sfx peak', np.abs(sfx).max())
write('bgm.wav', bgm / max(1.0, np.abs(bgm).max() * 1.1))
write('sfx.wav', sfx / max(1.0, np.abs(sfx).max() * 1.1))
