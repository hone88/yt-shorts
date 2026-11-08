"""摩擦の回：BGM・効果音（シンプル版：BGMは途切れさせない）。
python3 friction_sound.py taiyou_sound.py <動画長> <S1..S8> <すべる秒> <×の秒> <棚が崩れる秒> <ガツンと止まる秒>"""
import numpy as np, wave, sys
src = open(sys.argv[1], encoding="utf-8").read().split("# ------------------------------------------------------------ compose")[0]
exec(src)

VID = float(sys.argv[2])
S = [float(x) for x in sys.argv[3].split(",")]
SLIP, XT, SHELF, STOP = (float(x) for x in sys.argv[4:8])
TAIL = 2.6
DUR = VID + TAIL
N = int(SR * DUR)
rng = np.random.default_rng(13)
bgm = np.zeros((N, 2)); sfx = np.zeros((N, 2))


def transition(at):
    put(sfx, whoosh(0.45, True), at - 0.45, 0.35)
    put(sfx, boom(1.6), at, 0.30)


def squeak(d=0.35):  # キュッ（すべる音）
    t = t_(d)
    return np.sin(2 * np.pi * np.cumsum(np.linspace(1800, 900, len(t))) / SR) * env(len(t), 0.01, 0.15) * 0.6


def clatter(d=1.2):  # ガラガラ（物が崩れる）
    out = np.zeros(int(SR * d)); tt = 0.0
    while tt < d - 0.1:
        x = lp(noise(0.08), 3000) * np.exp(-t_(0.08) * 40) * rng.uniform(0.5, 1.2)
        i = int(tt * SR); out[i:i + len(x)] += x[:len(out) - i]; tt += rng.uniform(0.03, 0.12)
    return out


def crash(d=0.8):
    t = t_(d)
    return lp(noise(d), 1800) * np.exp(-t * 9) * 1.5 + boom(d) * 0.7


# BGM：明るいローファイを最後まで（摩擦が消えている間は、不思議な曲を重ねる）
lofi(bgm, 0.0, DUR, 0.9)
mystery(bgm, SLIP, STOP, 0.45, arp=True)

put(sfx, boom(2.0), 0.0, 0.4)
put(sfx, shimmer(1.2, True), SLIP - 0.05, 0.14)      # キラッ（地面が氷のように）
put(sfx, squeak(), SLIP, 0.5)
put(sfx, boom(2.0), SLIP + 0.35, 0.45)               # ドテッ
transition(S[1])
put(sfx, boom(2.0), XT, 0.5)
for k in range(2, 8):
    transition(S[k])
for j in range(6):                                    # 足が空回りするキュッキュッ
    put(sfx, squeak(0.2), S[2] + 0.4 + j * 0.45, 0.25, pan=0.3 if j % 2 else -0.3)
put(sfx, whoosh(2.0, False), S[3] + 1.5, 0.2)         # ひもがするする
put(sfx, whoosh(3.5, True), S[4] + 0.2, 0.3)          # 車が滑っていく
put(sfx, sparkle(), SHELF - 0.2, 0.06)                # ネジがポン
put(sfx, clatter(), SHELF, 0.5)                       # ガラガラ
put(sfx, crash(), STOP, 0.7)                          # ガツン
put(sfx, sparkle(), S[7], 0.08)
put(sfx, chime_end(), VID - 0.2, 0.12)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
