"""個人用の実験「深呼吸×セロトニン」：音（声・BGM・効果音を1本にまとめた mix.wav）。
SERO_VDIR に声（p/*.wav, dur.json）。python3 sero_sound.py taiyou_sound.py"""
import numpy as np, wave, sys, os
src = open(sys.argv[1], encoding="utf-8").read().split("# ------------------------------------------------------------ compose")[0]
exec(src)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sero_voxel as SVX

VID = SVX.DUR
N = int(SR * (VID + 0.5))
out = np.zeros((N, 2))
st = dict()
for (k, i, d), s0 in zip(SVX.SEG, SVX.STARTS):
    st[(k, i)] = (s0, s0 + d)


def tone(f0, f1, d, a=0.005, r=0.03):
    n = int(SR * d)
    return np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f1, n)) / SR) * env(n, a, r)


# 0. 導入：静かなドローン
put(out, pad(midi(45), 3.2), 0.0, 0.08)
put(out, bell(midi(81)), 0.4, 0.05)
# 1. ×1：締め切り。速いチクタク＋キーボード
a, b = st[("lv", 0)]
tt = a
while tt < b:
    put(out, hat(), tt, 0.25, pan=0.3)
    tt += 0.125
tt = a
while tt < b:
    put(out, lp(noise(0.03), 4000, 1) * env(int(0.03 * SR), 0.001, 0.02), tt, 0.25, pan=-0.2 + 0.4 * rng.random())
    tt += rng.uniform(0.06, 0.14)
put(out, pad(midi(40), b - a + 0.5), a, 0.07)
# 2. スクロールのたび：シュッ＋数字が上がる「チーン」（だんだん高く）
for i in range(1, 11):
    s0, s1 = st[("scroll", i)]
    sw = s0 + 0.78 * (s1 - s0)
    put(out, whoosh(0.5, True), sw - 0.4, 0.25)
    put(out, bell(midi(64 + 2 * i), 2.0), sw, 0.22)
    put(out, bell(midi(71 + 2 * i), 2.0), sw + 0.05, 0.12)
# 3. 段ごとの音：明るいパッドが、段を追うごとに高く・厚く
for i in range(1, 11):
    a, b = st[("lv", i)]
    root = 48 + i
    ch = [root, root + 4, root + 7, root + 11] if i < 7 else [root, root + 3, root + 7, root + 10, root + 14]
    for m in ch:
        put(out, pad(midi(m), b - a + 1.0), a, 0.035 + 0.004 * i)
    put(out, pad(midi(root - 12), b - a + 1.0), a, 0.06)
    if i >= 3:                                                         # キラキラ
        for k in range(int((b - a) * (1 + i * 0.6))):
            put(out, bell(midi(root + 24 + int(rng.integers(0, 12))), 0.8), a + rng.uniform(0, b - a - 0.3), 0.02 + 0.003 * i, pan=rng.uniform(-0.8, 0.8))
    if i in (5, 6):                                                    # ハト
        put(out, birds(b - a), a, 0.08)
    if i >= 7:                                                         # アルペジオ
        beat = 0.25 if i < 10 else 0.125
        k = 0; tt = a
        while tt < b - 0.1:
            put(out, keys(midi(ch[k % len(ch)] + 12), 0.4), tt, 0.06, pan=0.6 * np.sin(k))
            k += 1; tt += beat
    if i >= 8:
        put(out, sweep(80, 400 if i < 10 else 1600, b - a) * env(int((b - a) * SR), 0.5, 0.3), a, 0.05 + 0.03 * (i - 8))
    if i == 10:
        put(out, lp(noise(b - a), 2500) * np.linspace(0.1, 1, int((b - a) * SR)), a, 0.25)
        put(out, pad(midi(36), b - a), a, 0.12)                       # 「オーム」
# 4. バグる
a, b = st[("glitch", 0)]
put(out, crackle(b - a), a, 0.6)
for k in range(10):
    put(out, tone(rng.uniform(200, 3000), rng.uniform(100, 4000), 0.08), a + k * 0.13, 0.25)
# 5. ×0：ぶつっと無音 → かすかな冷蔵庫の音
a, b = st[("zero", 0)]
put(out, kick(), a, 0.9)
mus = out.copy(); out[:] = 0
put(out, lp(noise(VID - a), 120) * 0.6, a + 0.6, 0.05)
# 6. 通知：ピロン、ピロン
a, b = st[("notif", 0)]
for k in range(2):
    put(out, bell(1318, 0.6), a + k * 0.9, 0.25); put(out, bell(1760, 0.6), a + k * 0.9 + 0.12, 0.2)

# 声：のせて、声の間だけ音楽を下げる
mus = mus if 'mus' in dir() else np.zeros_like(out)
voice = np.zeros((N, 2))
VD = os.environ.get("SERO_VDIR", ".")
duck = np.ones(N)
for t0, k in SVX.VOICE:
    with wave.open(os.path.join(VD, "p", k + ".wav")) as w:
        v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
    put(voice, v, t0, 1.6)
    i0 = int(t0 * SR); i1 = min(N, i0 + len(v))
    duck[i0:i1] = 0.45
duck = lp(duck, 4, 1)
z0 = int(st[("zero", 0)][0] * SR)
out = mus * duck[:, None] + out * duck[:, None] + voice
fade = np.ones(N); fo = int(1.2 * SR); fade[-fo:] = np.linspace(1, 0, fo)
out *= fade[:, None]
x = out / max(1.0, np.abs(out).max() * 1.1)
with wave.open("mix.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
print("ok", VID)
