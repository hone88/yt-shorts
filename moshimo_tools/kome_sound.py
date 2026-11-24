"""26本目 お米（20261129）：BGM・効果音。BGMは最初から最後まで一定。
python3 kome_sound.py taiyou_sound.py <動画長> <S1..S8（場面の開始秒）>"""
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
CLIPS = [5.4, 7.3, 4.4, 9.8, 4.7, 4.7, 6.6, 11.2, 5.8, 5.5]


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
put(sfx, pop(1.0), S[0] + 0.15, 0.2)                        # お米と×100
put(sfx, whoosh(0.6, False), at(1, 0.3), 0.2)               # 1粒が大きくなる
put(sfx, sparkle(), at(2, 0.4), 0.12)                       # お茶碗がならぶ
put(sfx, pop(1.2), at(3, 3.4), 0.2)                         # 約200日
put(sfx, whoosh(0.4, True), at(5, 0.3), 0.22)               # くだけて粉に
put(sfx, pop(1.0), at(6, 1.6), 0.2)                         # 外はカリッ
put(sfx, pop(1.3), at(6, 3.6), 0.2)                         # 中はもっちり
put(sfx, sparkle(), at(7, 0.3), 0.14)                       # SANPO
put(sfx, chime_end(), VID - 0.2, 0.1)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
