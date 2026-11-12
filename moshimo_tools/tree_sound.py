"""17本目 木の回（20261119）：BGM・効果音。BGMは最初から最後まで一定。
python3 tree_sound.py taiyou_sound.py <動画長> <S1..S8（場面の開始秒）>"""
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
CLIPS = [5.4, 7.7, 5.3, 6.7, 8.6, 5.3, 4.8, 6.9]


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
put(sfx, pop(0.8), at(0, 1.1), 0.3)                                    # 木がかたむく
put(sfx, whoosh(1.6, False), at(0, 1.6), 0.35)                         # 落ちる→一気に引く
put(sfx, boom(0.8), S[1] + 0.1, 0.22)                                  # 1トン
put(sfx, whoosh(1.2, True), at(2, 0.3), 0.35)                          # くるっと回る
put(sfx, sparkle(), at(3, 0.4), 0.15)                                  # 羽根と同じ
w = lp(noise(E[5] - S[4]), 900) * 0.6                                   # 風（ブレーキ〜散る）
f_ = int(0.4 * SR); w[:f_] *= np.linspace(0, 1, f_); w[-f_:] *= np.linspace(1, 0, f_)
put(sfx, w, S[4], 0.5)
for j in range(6):
    put(sfx, pop(1.6 + 0.15 * j), at(5, 0.4) + 0.35 * j, 0.12)        # 葉っぱがちぎれる
put(sfx, boom(1.6), at(6, 1.0), 0.75)                                   # ドスン
put(sfx, whoosh(1.0, False), at(7, 0.4), 0.25)
put(sfx, chime_end(), VID - 0.2, 0.1)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
