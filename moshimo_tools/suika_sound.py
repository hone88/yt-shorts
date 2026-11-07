"""すいかの回：BGM・効果音（シンプル版：BGMは途切れさせない）。
python3 suika_sound.py taiyou_sound.py <動画長> <S1..S8> <落ちはじめ秒> <×の秒> <車がぶつかる秒> <すいかが割れる秒>"""
import numpy as np, wave, sys
src = open(sys.argv[1], encoding="utf-8").read().split("# ------------------------------------------------------------ compose")[0]
exec(src)

VID = float(sys.argv[2])
S = [float(x) for x in sys.argv[3].split(",")]
FALL, XT, CAR, SPLAT = (float(x) for x in sys.argv[4:8])
TAIL = 2.6
DUR = VID + TAIL
N = int(SR * DUR)
rng = np.random.default_rng(12)
bgm = np.zeros((N, 2)); sfx = np.zeros((N, 2))


def transition(at):
    put(sfx, whoosh(0.45, True), at - 0.45, 0.35)
    put(sfx, boom(1.6), at, 0.30)


def splat(d=0.9):
    t = t_(d)
    wet = (lp(noise(d), 2500) - lp(noise(d), 300)) * np.exp(-t * 7) * 1.6
    return wet + boom(d) * 0.6


def crash(d=0.8):
    t = t_(d)
    return lp(noise(d), 1800) * np.exp(-t * 9) * 1.5 + boom(d) * 0.7


def buzz(d):
    t = t_(d)
    return lp(np.sign(np.sin(2 * np.pi * 220 * t)), 1500) * 0.35 * env(len(t), 0.02, 0.1)


# BGM：明るいローファイを最後まで。注意の場面だけ不思議な曲を重ねる
lofi(bgm, 0.0, DUR, 0.9)
mystery(bgm, S[6], S[7] + 0.3, 0.5, arp=False)

put(sfx, boom(2.0), 0.0, 0.4)
put(sfx, whoosh(3.0, False), FALL, 0.35)
put(sfx, boom(2.0), FALL, 0.45)
transition(S[1])
put(sfx, boom(2.0), XT, 0.5)
for k in range(2, 8):
    transition(S[k])
put(sfx, whoosh(3.5, True), S[3] + 0.2, 0.35)          # 加速
put(sfx, crash(), CAR, 0.6)                           # 車がドン
put(sfx, splat(), SPLAT, 0.75)                        # グシャッ
put(sfx, buzz(0.5), S[6] + 0.3, 0.2)
put(sfx, buzz(0.5), S[6] + 1.0, 0.2)
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
