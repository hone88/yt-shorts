"""18本目 地球の回（20261120）：BGM・効果音。BGMは最初から最後まで一定。
python3 earth_sound.py taiyou_sound.py <動画長> <S1..S8（場面の開始秒）>"""
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
CLIPS = [3.5, 7.0, 4.7, 6.4, 8.8, 6.7, 8.5, 4.4]


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
put(sfx, whoosh(1.4, True), 0.0, 0.25)                                 # 地球が速く回る
put(sfx, boom(1.8), at(0, 1.5), 0.8)                                    # 急停止
put(sfx, boom(1.2), at(1, 0.7), 0.6)                                    # ドン！で体が浮く
w = lp(noise(E[1] - at(1, 0.7)), 1400) * 0.7                            # 投げ出される風
f_ = int(0.3 * SR); w[:f_] *= np.linspace(0, 1, f_); w[-f_:] *= np.linspace(1, 0, f_)
put(sfx, w, at(1, 0.7), 0.45)
put(sfx, pop(1.2), at(2, 0.9), 0.3)                                     # 北極点の印
put(sfx, pop(1.5), at(2, 1.7), 0.3)                                     # 飛行機の印
put(sfx, sparkle(), S[3] + 0.2, 0.12)                                  # 北極点（何も起きない）
put(sfx, whoosh(0.5, True), at(4, 4.6) - 0.3, 0.2)                     # 機内へ
put(sfx, pop(0.7), at(4, 5.0), 0.15)                                    # 「ポーン」
w = lp(noise(E[5] - S[5]), 900) * 0.8                                   # 暴風
w[:f_] *= np.linspace(0, 1, f_); w[-f_:] *= np.linspace(1, 0, f_)
put(sfx, w, S[5], 0.6)
put(sfx, boom(0.8), S[6] + 0.5, 0.25)                                   # 恐竜の足音
put(sfx, boom(0.8), S[6] + 1.6, 0.25)
put(sfx, whoosh(1.0, False), at(7, 0.5), 0.25)
put(sfx, chime_end(), VID - 0.2, 0.1)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
