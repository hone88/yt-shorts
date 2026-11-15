"""受託の見本 バッター×勝手に広島PR（20261122）：BGM・効果音。BGMは最初から最後まで一定。
python3 batter_sound.py taiyou_sound.py <動画長> <S1..S8（場面の開始秒）>"""
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
CLIPS = [7.6, 3.9, 5.4, 6.0, 6.4, 5.3, 4.2, 3.5, 7.7, 8.9]


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
    put(sfx, whoosh(0.4, True), S[k] - 0.4, 0.24)
put(sfx, boom(0.5), at(0, 1.75), 0.5)                      # カキーン（打球）
put(sfx, whoosh(1.0, False), at(0, 1.85), 0.3)
put(sfx, whoosh(1.2, False), S[1] + 0.1, 0.25)              # ふつうの打球
put(sfx, shimmer(1.2, True), S[2] + 0.2, 0.15)              # 光る
put(sfx, boom(1.6), at(2, 1.45), 0.8)                       # 100倍スイング
put(sfx, boom(0.7), at(3, 1.15), 0.5)                       # バットが折れる
put(sfx, sparkle(), at(3, 3.4), 0.14)                       # 鉄のバット
w = lp(noise(2.8), 2500) * 0.6                               # 燃える音
f_ = int(0.2 * SR); w[:f_] *= np.linspace(0, 1, f_); w[-f_:] *= np.linspace(1, 0, f_)
put(sfx, w, S[4], 0.35)
put(sfx, sparkle(), at(4, 3.6), 0.14)                       # 燃えないボール
put(sfx, whoosh(2.5, False), S[5] + 0.1, 0.3)               # 空高く
put(sfx, whoosh(1.5, True), S[6] + 0.1, 0.3)
put(sfx, boom(1.8), at(7, 0.9), 0.9)                        # ズドン
for f in (0.0, 0.25, 0.5, 0.75):
    put(sfx, pop(1.2), at(8, f * CLIPS[8]) + 0.05, 0.18)    # PRの切りかえ
put(sfx, chime_end(), VID - 0.2, 0.1)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
