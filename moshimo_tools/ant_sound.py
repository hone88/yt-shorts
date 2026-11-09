"""16本目 アリの回（20261118）：BGM・効果音。BGMは最初から最後まで一定。
python3 ant_sound.py taiyou_sound.py <動画長> <S1..S8（場面の開始秒）>"""
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
CLIPS = [4.4, 4.4, 5.6, 8.4, 5.7, 5.3, 6.7, 5.1]


def at(k, sec):
    """クリップの sec 秒の位置が、完成版の何秒か（短いクリップはゆっくり再生、長いクリップは途中で切れる）"""
    L = E[k] - S[k]
    st = max(1.0, L / CLIPS[k])
    return S[k] + min(L, sec * st)


def tone(f0, f1, d, a=0.005, r=0.1):
    n = int(SR * d)
    return np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f1, n)) / SR) * env(n, a, r)


def pop(f=1.0):
    return tone(500 * f, 1100 * f, 0.12, 0.005, 0.08)


def buzz():   # ブブー
    x = np.sign(np.sin(2 * np.pi * 180 * t_(0.45))) * env(int(0.45 * SR), 0.01, 0.1) * 0.5
    return lp(x, 2500)


lofi(bgm, 0.0, DUR, 0.9)

for k in range(1, len(S)):
    put(sfx, whoosh(0.4, True), S[k] - 0.4, 0.26)
put(sfx, pop(1.4), at(0, 0.3), 0.25)                                   # アリがちょこちょこ
put(sfx, whoosh(1.4, False), at(0, 1.3), 0.3)                          # ふちから落ちる→一気に引く
put(sfx, boom(1.0), S[1] + 0.05, 0.3)                                  # ぺしゃんこの車
put(sfx, buzz(), at(1, 4.4 * 0.38), 0.35)                              # ×
put(sfx, pop(1.6), at(1, 4.4 * 0.58), 0.35)                            # いいえ、平気
put(sfx, whoosh(1.0, True), at(2, 0.5), 0.45)                          # 車がビューンと通りすぎる
for j in range(int((E[3] - S[3]) / 0.3)):                              # ジョギングの足音
    put(sfx, lp(noise(0.05), 900) * env(int(0.05 * SR), 0.002, 0.04), S[3] + 0.15 + j * 0.3, 0.18, pan=0.3 if j % 2 else -0.3)
w = lp(noise(E[4] - S[4]), 700) * 0.6                                   # 風
f_ = int(0.4 * SR); w[:f_] *= np.linspace(0, 1, f_); w[-f_:] *= np.linspace(1, 0, f_)
put(sfx, w, S[4], 0.55)
put(sfx, pop(0.9), at(5, 1.1), 0.6)                                    # ポン！
for j in range(3):
    put(sfx, pop(1.8 + 0.2 * j), at(5, 1.8) + 0.25 * j, 0.15)          # 歩きだす
put(sfx, sparkle(), at(6, 0.8), 0.15)                                  # くるっと向きを変える
put(sfx, whoosh(1.6, True), at(6, 1.4), 0.2)                           # 滑空
put(sfx, pop(1.2), at(6, 6.7 * 0.75), 0.3)                             # 幹にとまる
put(sfx, whoosh(1.0, False), at(7, 0.4), 0.25)                         # 最後：一気に引く
put(sfx, chime_end(), VID - 0.2, 0.1)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
