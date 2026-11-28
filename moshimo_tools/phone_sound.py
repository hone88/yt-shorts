"""29本目 携帯（20261202）：BGM・効果音。ball_sound.py と同じ作り。
python3 phone_sound.py taiyou_sound.py <動画長> <S1..S8（場面の開始秒）>"""
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
CLIPS = [5.3, 4.5, 6.0, 6.0, 4.1, 6.7, 8.2, 4.1, 8.8, 3.8]
CUTS = {0: [0.5], 3: [0.45], 4: [0.55], 7: [0.45], 8: [0.45]}


def at(k, sec):
    L = E[k] - S[k]
    st = max(1.0, L / CLIPS[k])
    return S[k] + min(L, sec * st)


def tone(f0, f1, d, a=0.005, r=0.1):
    n = int(SR * d)
    return np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f1, n)) / SR) * env(n, a, r)


def pop(f=1.0):
    return tone(500 * f, 1100 * f, 0.12, 0.005, 0.08)


lofi(bgm, 0.0, DUR, 0.9)

for k in range(1, len(S)):
    put(sfx, whoosh(0.4, True), S[k] - 0.4, 0.26)
for k, fr in CUTS.items():
    for f in fr:
        if at(k, f * CLIPS[k]) < E[k] - 0.15:
            put(sfx, whoosh(0.25, True), at(k, f * CLIPS[k]) - 0.2, 0.12)
put(sfx, whoosh(2.0, False), at(0, 1.4), 0.3)               # はなす
w = lp(noise(E[3] - S[2]), 1200) * 0.6                      # 一定の風の音（2〜3場面）
f_ = int(0.3 * SR); w[:f_] *= np.linspace(0, 1, f_); w[-f_:] *= np.linspace(1, 0, f_)
put(sfx, w, S[2], 0.3)
put(sfx, pop(1.0), at(3, 0.3 * CLIPS[3]), 0.2)               # 時速50km
put(sfx, boom(0.3), at(4, 1.25), 0.25)                       # 手から落ちて地面
put(sfx, pop(0.9), at(4, 0.3 * CLIPS[4]), 0.18)
put(sfx, pop(1.2), at(5, 0.2 * CLIPS[5]), 0.2)               # くらべる
put(sfx, whoosh(2.5, False), S[6] + 0.3, 0.2)                # 飛行機から
put(sfx, sparkle(), S[7] + 0.5, 0.12)                        # 無事
put(sfx, boom(0.6), S[8] + 0.05, 0.35)                       # バキッ
put(sfx, sparkle(), S[9] + 0.4, 0.1)                         # もう一回？
put(sfx, chime_end(), VID - 0.2, 0.1)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
