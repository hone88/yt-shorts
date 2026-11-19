"""20本目 野球ボール（20261126）：BGM・効果音。BGMは最初から最後まで一定。
python3 jump_sound.py taiyou_sound.py <動画長> <S1..S8（場面の開始秒）>"""
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
CLIPS = [8.6, 3.9, 9.8, 6.6, 2.6, 15.2, 8.2, 2.6]


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
put(sfx, whoosh(2.0, False), S[0] + 0.6, 0.3)               # 落ちはじめる
w = lp(noise(E[2] - S[2]), 1200) * 0.6                      # 一定の風の音
f_ = int(0.3 * SR); w[:f_] *= np.linspace(0, 1, f_); w[-f_:] *= np.linspace(1, 0, f_)
put(sfx, w, S[2], 0.35)
put(sfx, whoosh(0.5, True), S[3] + 0.8, 0.35)               # 投げる
put(sfx, pop(1.2), S[3] + 0.9, 0.2)
put(sfx, sparkle(), S[4] + 0.3, 0.12)                       # 捕れる？
put(sfx, whoosh(2.5, False), S[5] + 0.5, 0.25)              # 1908年 落ちてくる
put(sfx, boom(0.6), S[5] + CLIPS[5] * 0.62, 0.35)            # パシッ
put(sfx, pop(1.4), S[5] + CLIPS[5] * 0.62, 0.3)
put(sfx, chime_end(), VID - 0.2, 0.1)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
