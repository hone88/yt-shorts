"""19本目 公転の回（20261123）：BGM・効果音。11/17 冒頭を「自転→北極点→公転は？」の2場面に変更（全9場面）。
python3 kouten_sound.py taiyou_sound.py <動画長> <S1..S9（場面の開始秒）>"""
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
CLIPS = [7.0, 6.1, 5.4, 8.5, 7.2, 4.2, 11.8, 7.0, 4.5]


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
put(sfx, boom(1.2), at(0, 0.6), 0.6)                        # 自転が止まって投げ出される
put(sfx, boom(0.6), S[1] + 3.9, 0.35)                       # 「公転も止まったら？」
put(sfx, shimmer(1.5, True), S[2] + 0.1, 0.12)             # 公転
put(sfx, boom(1.8), at(3, 0.8), 0.8)                        # 北極点でも吹き飛ぶ
w = lp(noise(E[3] - at(3, 0.8)), 1400) * 0.7
f_ = int(0.3 * SR); w[:f_] *= np.linspace(0, 1, f_); w[-f_:] *= np.linspace(1, 0, f_)
put(sfx, w, at(3, 0.8), 0.45)
put(sfx, whoosh(2.5, False), S[4] + 0.2, 0.35)              # 宇宙へ飛び出す
w = lp(noise(E[5] - S[5]), 900) * 0.8
w[:f_] *= np.linspace(0, 1, f_); w[-f_:] *= np.linspace(1, 0, f_)
put(sfx, w, S[5], 0.5)                                      # 全部飛んでいく
put(sfx, sparkle(), S[6] + 1.0, 0.12)                       # 宇宙ステーション
put(sfx, whoosh(3.0, True), S[7] + 0.2, 0.3)                # 太陽へ落ちる
put(sfx, chime_end(), VID - 0.2, 0.1)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
