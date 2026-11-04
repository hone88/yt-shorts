"""1円玉の回：BGM・効果音（シンプル版：明るい曲を最後まで途切れさせない）。
python3 coin_sound.py taiyou_sound.py <動画長> <S1..S8> <コインが当たる秒> <デコピンの秒>"""
import numpy as np, wave, sys
src = open(sys.argv[1], encoding="utf-8").read().split("# ------------------------------------------------------------ compose")[0]
exec(src)

VID = float(sys.argv[2])
S = [float(x) for x in sys.argv[3].split(",")]
HIT, FLICK = float(sys.argv[4]), float(sys.argv[5])
TAIL = 2.6
DUR = VID + TAIL
N = int(SR * DUR)
rng = np.random.default_rng(3)
bgm = np.zeros((N, 2)); sfx = np.zeros((N, 2))


def transition(at):
    put(sfx, whoosh(0.45, True), at - 0.45, 0.35)
    put(sfx, boom(1.6), at, 0.30)


def clink(f=3100):  # チャリン（金属の小さな音）
    d = 0.6; t = t_(d)
    x = sum(np.sin(2 * np.pi * f * k * t) * np.exp(-t * (9 + 3 * k)) for k in (1, 1.51, 2.27))
    return x * 0.5


def tap():  # コツン
    d = 0.25; t = t_(d)
    return (np.sin(2 * np.pi * 900 * t) * np.exp(-t * 40) + lp(noise(d), 3000) * np.exp(-t * 60) * 0.6)


def flick():  # ピン
    d = 0.3; t = t_(d)
    return np.sin(2 * np.pi * np.cumsum(np.linspace(1400, 700, len(t))) / SR) * np.exp(-t * 25)


def buzz(d):  # ブー（注意）
    t = t_(d)
    return lp(np.sign(np.sin(2 * np.pi * 220 * t)), 1500) * 0.35 * env(len(t), 0.02, 0.1)


# BGM：明るいローファイを最初から最後まで。注意の場面だけ不思議な曲を重ねる
lofi(bgm, 0.0, DUR, 0.9)
mystery(bgm, S[6], S[7] + 0.3, 0.5, arp=False)

put(sfx, boom(2.0), 0.0, 0.4)
put(sfx, clink(), 0.3, 0.18)
put(sfx, whoosh(1.2, False), 0.4, 0.15)
# 2. 「いいえ」でコツン＋キラッ
transition(S[1])
put(sfx, tap(), HIT, 0.5)
put(sfx, clink(2600), HIT + 0.05, 0.15)
put(sfx, sparkle(), HIT + 0.05, 0.08)
# 3〜8
for k in range(2, 8):
    transition(S[k])
for k in range(4):  # ひらひら
    put(sfx, whoosh(0.7, k % 2 == 0), S[2] + 0.3 + k * 0.9, 0.12, pan=0.5 if k % 2 else -0.5)
t = t_(1.6)  # 針が上がる音
put(sfx, np.sin(2 * np.pi * np.cumsum(np.linspace(300, 900, len(t))) / SR) * env(len(t), 0.05, 0.2) * 0.25, S[3] + 0.2, 0.3)
put(sfx, clink(2000), S[3] + 1.8, 0.12)
put(sfx, flick(), FLICK, 0.5)
put(sfx, buzz(0.5), S[6] + 0.3, 0.2)
put(sfx, buzz(0.5), S[6] + 1.0, 0.2)
put(sfx, clink(), S[7] + 0.4, 0.12)
put(sfx, chime_end(), VID - 0.2, 0.12)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
