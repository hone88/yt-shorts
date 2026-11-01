import numpy as np, wave

SR = 44100
DUR = 50.575
N = int(SR * DUR)
rng = np.random.default_rng(11)

# scene starts in the built video
S1, S2, S3, S4, S5, S6, S7 = 0.0, 5.056, 11.893, 18.36, 26.733, 33.733, 41.306
BLACK = 1.22


def t_(d):
    return np.arange(int(SR * d)) / SR


def lp(x, cut, n=2):
    k = max(1, int(SR / cut / 2))
    for _ in range(n):
        c = np.cumsum(np.concatenate([[0.0], x]))
        x = np.concatenate([(c[k:] - c[:-k]) / k, np.zeros(k - 1)])
    return x


def env(n, a, r):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr)
    return e


def put(buf, x, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= len(buf): return
    x = x[: len(buf) - i]
    l = np.cos((pan + 1) * np.pi / 4) * 1.414; r = np.sin((pan + 1) * np.pi / 4) * 1.414
    buf[i:i + len(x), 0] += x * gain * l; buf[i:i + len(x), 1] += x * gain * r


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


def sweep(f0, f1, d):
    t = t_(d); f = f0 * (f1 / f0) ** (t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def noise(d):
    return rng.normal(0, 1, int(SR * d))


# ------------------------------------------------------------ instruments
def keys(f, d=0.9):
    t = t_(d)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 3.2) * env(len(t), 0.005, 0.1)


def bell(f, d=1.8):
    t = t_(d)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.01 * t) + 0.2 * np.sin(2 * np.pi * f * 3.98 * t)) * np.exp(-t * 2.6)


def pad(f, d):
    t = t_(d)
    x = sum(np.sin(2 * np.pi * f * k * t + rng.uniform(0, 6)) / k ** 1.8 for k in (1, 2, 3)) + 0.6 * np.sin(2 * np.pi * f * 1.005 * t)
    return x * (1 + 0.12 * np.sin(2 * np.pi * 0.2 * t)) * env(len(t), 0.8, 1.0)


def kick():
    t = t_(0.3); f = 50 + 80 * np.exp(-t * 25)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 10)


def hat():
    t = t_(0.05); n = rng.normal(0, 1, len(t)); n -= lp(n, 3500, 1)
    return n * np.exp(-t * 70)


def lofi(buf, t0, t1, gain=1.0):
    """bright everyday loop C-Am-F-G, 92 bpm"""
    beat = 60 / 92; bar = 4 * beat
    prog = [[60, 64, 67, 71], [57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 65]]
    b = 0
    while t0 + b * bar < t1:
        ts = t0 + b * bar; ch = prog[b % 4]
        for i, m in enumerate(ch):
            put(buf, keys(midi(m), bar), ts + i * 0.02, 0.07 * gain, pan=-0.3 + 0.2 * i)
        put(buf, keys(midi(ch[0] - 24), bar) * 1.2, ts, 0.10 * gain)
        for k in range(4):
            tk = ts + k * beat
            if tk >= t1: break
            if k in (0, 2): put(buf, kick(), tk, 0.18 * gain)
            put(buf, hat(), tk + beat / 2, 0.05 * gain)
            if k % 2 == 1:
                put(buf, keys(midi(ch[(k + b) % 4] + 12), 0.4), tk, 0.05 * gain, pan=0.4)
        b += 1


def mystery(buf, t0, t1, gain=1.0, arp=True, warm_from=None):
    """cold minor ambience: Am - F - Dm - E, music-box arpeggio"""
    beat = 60 / 70; bar = 4 * beat
    prog = [[57, 60, 64], [53, 57, 60], [50, 53, 57], [52, 56, 59]]
    warm = [[53, 57, 60, 64], [55, 59, 62], [60, 64, 67, 71]]
    b = 0
    while t0 + b * bar < t1:
        ts = t0 + b * bar
        d = min(bar + 1.0, t1 - ts + 1.2)
        is_warm = warm_from is not None and ts >= warm_from
        ch = warm[b % 3] if is_warm else prog[b % 4]
        for m in ch:
            put(buf, pad(midi(m - 12), d), ts, 0.045 * gain)
        put(buf, pad(midi(ch[0] - 24), d), ts, 0.06 * gain)
        if arp:
            for k in range(8):
                tk = ts + k * beat / 2
                if tk >= t1 - 0.3: break
                put(buf, bell(midi(ch[[0, 1, 2, 1, 2, 0, 1, 2][k] % len(ch)] + 12 + (12 if k == 6 else 0))), tk, 0.035 * gain, pan=-0.5 + 0.14 * k)
        b += 1


# ------------------------------------------------------------ SFX
def birds(d):
    out = np.zeros(int(SR * d))
    tt = 0.05
    while tt < d - 0.3:
        n = int(rng.integers(2, 5))
        for j in range(n):
            ch = sweep(rng.uniform(2800, 3600), rng.uniform(4200, 5200), 0.07) * env(int(0.07 * SR), 0.01, 0.04)
            i = int((tt + j * 0.1) * SR); out[i:i + len(ch)] += ch[: len(out) - i]
        tt += rng.uniform(0.6, 1.4)
    return out


def power_down():
    d = 1.2; t = t_(d)
    hum = sweep(420, 40, d) * np.exp(-t * 2.2)
    click = np.zeros(len(t)); click[:400] = rng.normal(0, 1, 400) * np.linspace(1, 0, 400)
    return hum * 0.7 + click * 0.8


def boom(d=2.2):
    t = t_(d); f = 32 + 50 * np.exp(-t * 6)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6) + lp(noise(d), 600, 1) * np.exp(-t * 4) * 0.5


def ring(d=2.5):
    t = t_(d)
    return np.sin(2 * np.pi * 3700 * t) * env(len(t), 0.05, 1.5) * 0.4


def buzz_on():
    d = 0.08; t = t_(d)
    return (np.sign(np.sin(2 * np.pi * 120 * t)) * 0.3 + lp(noise(d), 3000, 1)) * env(len(t), 0.002, 0.03)


def shimmer(d=1.4, down=True):
    t = t_(d)
    f = np.linspace(2400, 900, len(t)) if down else np.linspace(900, 2400, len(t))
    x = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) for k in (1, 1.5, 2.01)) / 3
    return x * np.sin(np.pi * t / d) ** 2


def whoosh(d, up=True):
    n = noise(d); t = t_(d)
    band = lp(n, 2200) - lp(n, 500)
    return band * np.sin(np.pi * t / d) ** 2 * ((t / d) if up else (1 - t / d) + 0.2)


def crackle(d):
    out = np.zeros(int(SR * d))
    k = int(d * 18)
    for _ in range(k):
        i = int(rng.uniform(0, d - 0.05) * SR)
        c = rng.normal(0, 1, 300) * np.exp(-np.arange(300) / 40)
        out[i:i + 300] += c * rng.uniform(0.3, 1)
    return out - lp(out, 1500, 1)


def creak(d=1.3):
    t = t_(d); f = 70 + 25 * np.sin(2 * np.pi * 0.7 * t)
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * (0.5 + 0.5 * (rng.random(len(t)) < 0.3))
    return lp(x, 800, 2) * np.sin(np.pi * t / d) ** 2


def water_hum(d):
    t = t_(d)
    return lp(noise(d), 300, 2) * 3 * env(len(t), 1.0, 1.5) + np.sin(2 * np.pi * 55 * t) * 0.2 * env(len(t), 1.0, 1.5)


def bubble():
    d = 0.09; t = t_(d); f = np.linspace(500, 1300, len(t)) * rng.uniform(0.8, 1.3)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d)


def sparkle():
    f = midi(int(rng.choice([84, 88, 91, 93, 96])))
    return bell(f, 1.0)


def chime_end():
    out = np.zeros(int(SR * 2.4))
    for i, m in enumerate([72, 76, 79, 84]):
        b = bell(midi(m), 2.0); s = int(i * 0.12 * SR); out[s:s + len(b)] += b[: len(out) - s]
    return out


# ------------------------------------------------------------ compose
bgm = np.zeros((N, 2)); sfx = np.zeros((N, 2))

# scene 1: bright noon, cut by the blackout
lofi(bgm, 0.0, BLACK, 1.0)
put(sfx, birds(BLACK + 0.2), 0.0, 0.05, pan=0.5)
put(sfx, power_down(), BLACK - 0.02, 0.5)
put(sfx, boom(), BLACK, 0.55)
put(sfx, ring(2.4), BLACK + 0.1, 0.05)
for dt in (0.34, 0.43, 0.51, 0.61):           # street lamps flicker on (0.25..0.45 clip s x1.357)
    put(sfx, buzz_on(), BLACK + dt, 0.25, pan=0.3)
mystery(bgm, BLACK + 1.4, S2 - 0.1, 0.9, arp=False)

# scene 2: flashback to the normal afternoon (0 s)
put(sfx, whoosh(0.7, False), S2 - 0.35, 0.35)
put(sfx, shimmer(0.9, False), S2 - 0.2, 0.08)
lofi(bgm, S2, S3 - 0.15, 0.9)
put(sfx, birds(S3 - S2), S2, 0.05, pan=-0.4)

# scene 3: 8 min 20 s later -> dark, the moon goes out
put(sfx, power_down(), S3 - 0.05, 0.4)
put(sfx, boom(1.8), S3, 0.45)
moon_out = S3 + 1.9 * 1.195
put(sfx, shimmer(1.4, True), moon_out - 0.2, 0.12)
mystery(bgm, S3 + 0.8, 50.0, 1.0, arp=True, warm_from=S7 + 2.5)

# scene 4: earth leaves its orbit
put(sfx, whoosh(1.2, True), S4 - 0.3, 0.35)
put(sfx, sweep(110, 70, 6.0) * env(int(6.0 * SR), 1.0, 2.0), S4 + 0.5, 0.10)

# scene 5: frost spreads
put(sfx, crackle(S6 - S5 - 0.3) * np.linspace(0.4, 1, int((S6 - S5 - 0.3) * SR)), S5 + 0.2, 0.12, pan=0.2)
put(sfx, whoosh(1.5, False) * 0.6, S5 + 0.1, 0.25)

# scene 6: frozen sea, a lid of ice
put(sfx, creak(1.6), S6 + 0.4, 0.22)
put(sfx, creak(1.2), S6 + 3.6, 0.18, pan=-0.3)
put(sfx, water_hum(S7 - S6), S6 + 1.2, 0.20)

# scene 7: deep sea vent, life survives
put(sfx, water_hum(DUR - S7), S7, 0.18)
tt = S7 + 0.2
while tt < DUR - 1.0:
    put(sfx, bubble(), tt, 0.12, pan=rng.uniform(-0.5, 0.5)); tt += rng.uniform(0.12, 0.45)
for k in range(9):
    put(sfx, sparkle(), S7 + 0.6 + k * 0.85, 0.03, pan=rng.uniform(-0.7, 0.7))
put(sfx, chime_end(), DUR - 2.5, 0.10)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


print(np.abs(bgm).max(), np.abs(sfx).max())
write('bgm.wav', bgm); write('sfx.wav', sfx)
