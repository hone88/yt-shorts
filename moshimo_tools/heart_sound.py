"""28本目「心臓の回数」（20261201）：BGM・効果音。tousan_sound.py と同じ作り。
前半は軽いピアノ、「最初の1回は？」（6場面目）から、やさしいピアノとパッドに切りかえる。心臓の音（どくん）を入れる。
python3 heart_sound.py taiyou_sound.py <動画長> <S1..S16（場面の開始秒）>"""
import numpy as np, wave, sys
src = open(sys.argv[1], encoding="utf-8").read().split("# ------------------------------------------------------------ compose")[0]
exec(src)

VID = float(sys.argv[2])
S = [float(x) for x in sys.argv[3].split(",")]
E = S[1:] + [VID]
TAIL = 2.6
DUR = VID + TAIL
N = int(SR * DUR)
bgm = np.zeros((N, 2)); sfx = np.zeros((N, 2))
CLIPS = [6.3, 3.7, 6.3, 4.7, 8.2, 3.2, 5.5, 4.7, 6.0, 4.1]
CUTS = {0: [0.45], 1: [0.4], 2: [0.5], 3: [0.45], 4: [0.55], 5: [0.5], 6: [0.45], 7: [0.5], 8: [0.45]}


def at(k, f):
    L = E[k] - S[k]
    st = max(1.0, L / CLIPS[k])
    return S[k] + min(L, f * CLIPS[k] * st)


def tone(f0, f1, d, a=0.005, r=0.1):
    n = int(SR * d)
    return np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f1, n)) / SR) * env(n, a, r)


def pop(f=1.0):
    return tone(500 * f, 1100 * f, 0.12, 0.005, 0.08)


def soft_keys(f, d):
    t = t_(d)
    return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 1.4) * env(len(t), 0.01, 0.4)


def light(buf, t0, t1, gain=1.0):
    """前半：軽いピアノ（F-G-Em-Am、96bpm、ドラムなし）"""
    beat = 60 / 96; bar = 4 * beat
    prog = [[53, 57, 60, 64], [55, 59, 62, 65], [52, 55, 59, 62], [57, 60, 64, 67]]
    b = 0
    while t0 + b * bar < t1:
        ts = t0 + b * bar; ch = prog[b % 4]
        put(buf, keys(midi(ch[0] - 12), bar) * 1.1, ts, 0.11 * gain)
        for k in range(8):
            tk = ts + k * beat / 2
            if tk >= t1: break
            put(buf, keys(midi(ch[(k * 2 + b) % 4] + 12), 0.5), tk, 0.06 * gain, pan=-0.3 + 0.08 * k)
        b += 1


def ballad(buf, t0, t1, gain=1.0):
    """後半：やさしいピアノとパッド（C-G-Am-F、70bpm）"""
    beat = 60 / 70; bar = 4 * beat
    prog = [[48, 55, 60, 64], [43, 50, 55, 59], [45, 52, 57, 60], [41, 48, 53, 57]]
    mel = [76, 74, 72, 74, 72, 71, 69, 71, 72, 69, 67, 69, 65, 67, 69, 72]
    b = 0
    while t0 + b * bar < t1:
        ts = t0 + b * bar; ch = prog[b % 4]
        put(buf, pad(midi(ch[0]), bar + 0.8), ts, 0.05 * gain)
        put(buf, pad(midi(ch[2]), bar + 0.8), ts, 0.035 * gain, pan=0.2)
        for k in range(4):
            tk = ts + k * beat
            if tk >= t1: break
            put(buf, soft_keys(midi(ch[k % 4] + 12), beat * 2), tk, 0.07 * gain, pan=-0.2 + 0.1 * k)
        if b >= 1:
            for j in range(2):
                tm = ts + j * 2 * beat
                if tm < t1:
                    put(buf, soft_keys(midi(mel[(b * 2 + j) % 16]), beat * 2.5), tm, 0.06 * gain, pan=0.15)
        b += 1


def lub(at_, g=0.3):
    """どくん（低い2つの音）"""
    put(sfx, tone(70, 45, 0.16, 0.003, 0.12), at_, g)
    put(sfx, tone(60, 40, 0.14, 0.003, 0.1), at_ + 0.22, g * 0.75)


light(bgm, 0.0, S[5], 0.9)
ballad(bgm, S[5], DUR, 1.0)

for k in range(1, len(S)):
    put(sfx, whoosh(0.4, True), S[k] - 0.4, 0.2)
for k, fr in CUTS.items():
    for f in fr:
        if at(k, f) < E[k] - 0.15:
            put(sfx, whoosh(0.25, True), at(k, f) - 0.2, 0.1)
for i in range(3):
    lub(S[1] + 0.1 + i * 0.86, 0.32)                                  # 一生 30億回
put(sfx, pop(1.0), at(1, 0.45), 0.22)
put(sfx, pop(0.9), S[2] + 0.2, 0.2)                                   # 10万回
for i in range(6):
    lub(S[3] + at(3, 0.45) - S[3] + i * 0.43, 0.28)                   # ドキドキ（速い）
put(sfx, sparkle(), S[5] + 0.6, 0.12)                                 # 最初の1回？
put(sfx, shimmer(1.2, False), at(6, 0.5), 0.12)                       # 妊娠5〜6週
tt = S[7]
while tt < E[7]:
    lub(tt, 0.4); tt += 60 / 70                                       # どくん、どくん
put(sfx, shimmer(1.4, False), S[8] + 0.2, 0.14)                       # お母さんの心臓
put(sfx, chime_end(), VID - 0.2, 0.1)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
