"""空気が10秒消えたら：BGM・効果音。使い方: python3 air_sound.py taiyou_sound.py <動画の長さ> <S1,...,S8> <空が黒くなる秒>"""
import numpy as np, wave, sys
src = open(sys.argv[1], encoding="utf-8").read().split("# ------------------------------------------------------------ compose")[0]
exec(src)

VID = float(sys.argv[2])
S = [float(x) for x in sys.argv[3].split(",")]
FL = float(sys.argv[4])
TAIL = 2.6
DUR = VID + TAIL
N = int(SR * DUR)
rng = np.random.default_rng(6)
bgm = np.zeros((N, 2)); sfx = np.zeros((N, 2))


def transition(at):
    put(sfx, whoosh(0.45, True), at - 0.45, 0.35)
    put(sfx, boom(1.6), at, 0.30)


def air_hiss(d):
    return lp(noise(d), 3000) * env(int(d * SR), 0.2, 0.6)


def tick():
    x = np.zeros(int(0.05 * SR)); x[:200] = rng.normal(0, 1, 200) * np.linspace(1, 0, 200)
    return lp(x, 4000)


# 1. 昼の街：明るいローファイ → 空が黒くなった瞬間「ブツッ」＋ドン → 不安なパッド
put(sfx, boom(2.0), 0.0, 0.45)
lofi(bgm, 0.0, FL, 0.8)
put(sfx, birds(FL), 0.0, 0.05)
put(sfx, shimmer(1.4, True), FL - 0.05, 0.14)
put(sfx, boom(2.4), FL, 0.75)
mystery(bgm, FL + 0.5, S[6] - 0.05, 0.85, arp=False)

# 2. 音が消える：パッドだけ残し、ピッという耳鳴り
transition(S[1])
t = t_(3.0); put(sfx, np.sin(2 * np.pi * 6000 * t) * env(len(t), 0.4, 1.5) * 0.15, S[1] + 0.6, 0.25)

# 3. 落ちる：下がっていく風切り音
transition(S[2])
put(sfx, whoosh(2.5, False), S[2] + 0.3, 0.30)

# 4. 肺の空気が出ていく：シューッ
transition(S[3])
put(sfx, air_hiss(2.5), S[3] + 0.4, 0.18)

# 5. つばがぶくぶく
transition(S[4])
tt = S[4] + 0.3
while tt < S[5] - 0.3:
    put(sfx, bubble(), tt, 0.12, pan=rng.uniform(-0.4, 0.4)); tt += rng.uniform(0.05, 0.18)

# 6. 海が泡立つ：ぶくぶく＋シュワー
transition(S[5])
tt = S[5] + 0.2
while tt < S[6] - 0.3:
    put(sfx, bubble(), tt, 0.10, pan=rng.uniform(-0.8, 0.8)); tt += rng.uniform(0.03, 0.12)
put(sfx, lp(noise(S[6] - S[5]), 2500) * 0.6, S[5] + 0.2, 0.06)

# 7. 空気が戻る：大きな風＋ドン → 明るいローファイと鳥
put(sfx, whoosh(0.8, True), S[6] - 0.3, 0.45)
put(sfx, boom(2.2), S[6] + 0.4, 0.55)
put(sfx, air_hiss(1.8), S[6] + 0.4, 0.22)
lofi(bgm, S[6] + 0.5, DUR, 1.0)
put(sfx, birds(S[7] - S[6]), S[6] + 0.8, 0.06, pan=0.4)

# 8. 問いかけ：チクタク10回 → 声のあとは音楽だけ
put(sfx, whoosh(0.45, True), S[7] - 0.45, 0.3)
put(sfx, sparkle(), S[7], 0.08)
for k in range(10):
    put(sfx, tick(), S[7] + 0.2 + k * 0.5, 0.25)
put(sfx, chime_end(), VID - 0.2, 0.12)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
