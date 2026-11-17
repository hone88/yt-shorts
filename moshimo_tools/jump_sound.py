"""20本目 摩擦ゼロでジャンプ（20261125）：BGM・効果音。BGMは最初から最後まで一定。
python3 jump_sound.py taiyou_sound.py <動画長> <S1..S11（場面の開始秒）>"""
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
CLIPS = [6.4, 3.2, 6.6, 8.0, 7.6, 11.1, 10.8, 11.0, 8.5, 8.2, 11.5]


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
for k in range(3):                                          # 足がすべる
    put(sfx, whoosh(0.3, False), S[0] + 0.5 + 1.1 * k, 0.12)
for tt in (0.5, 2.0, 3.5, 5.0):                             # ぴょん（真上にジャンプ）
    if S[2] + tt < E[2] - 0.2:
        put(sfx, tone(400, 900, 0.18), at(2, tt), 0.18)
put(sfx, shimmer(1.5, True), S[4] + 0.1, 0.12)             # 回る地球
put(sfx, whoosh(2.0, False), at(5, 0.6), 0.35)              # 地面が流れていく
for tt in (0.6, 2.4, 4.2, 6.0):                             # 同じ×に着地
    if S[6] + tt + 1.1 < E[6]:
        put(sfx, tone(400, 900, 0.18), at(6, tt), 0.15); put(sfx, pop(0.7), at(6, tt + 1.1), 0.15)
put(sfx, sparkle(), at(7, CLIPS[7] * 0.2), 0.12)            # 虫めがね
put(sfx, boom(0.5), at(7, CLIPS[7] * 0.42), 0.2)            # 0.025mm
put(sfx, tone(400, 900, 0.18), at(8, 0.6), 0.15)
w = lp(noise(max(0.5, E[8] - at(8, 1.6))), 1800) * 0.5     # すべり続ける音
f_ = int(0.3 * SR); w[:f_] *= np.linspace(0, 1, f_); w[-f_:] *= np.linspace(1, 0, f_)
put(sfx, w, at(8, 1.6), 0.25)
put(sfx, chime_end(), VID - 0.2, 0.1)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
