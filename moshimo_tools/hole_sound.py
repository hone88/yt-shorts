"""穴の回：BGM・効果音（シンプル版：BGMは途切れさせない）。
python3 hole_sound.py taiyou_sound.py <動画長> <S1..S8> <飛び込む秒> <×の秒> <海から出る秒>"""
import numpy as np, wave, sys
src = open(sys.argv[1], encoding="utf-8").read().split("# ------------------------------------------------------------ compose")[0]
exec(src)

VID = float(sys.argv[2])
S = [float(x) for x in sys.argv[3].split(",")]
JUMP, XT, POP = float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
TAIL = 2.6
DUR = VID + TAIL
N = int(SR * DUR)
rng = np.random.default_rng(10)
bgm = np.zeros((N, 2)); sfx = np.zeros((N, 2))


def transition(at):
    put(sfx, whoosh(0.45, True), at - 0.45, 0.35)
    put(sfx, boom(1.6), at, 0.30)


def splash(d=1.2):
    t = t_(d)
    return (lp(noise(d), 4000) - lp(noise(d), 500)) * np.exp(-t * 4) * 1.4


def steps(t0, t1):
    tt = t0
    while tt < t1:
        x = lp(noise(0.08), 900) * np.exp(-t_(0.08) * 50) * 1.5
        put(sfx, x, tt, 0.25, pan=0.2 if int(tt * 4) % 2 else -0.2); tt += 0.28


# BGM：明るい曲 → 落ちはじめたら不思議な曲 → 海から出たら明るい曲 → 最後は不思議な曲（ずっと途切れない）
lofi(bgm, 0.0, JUMP + 0.6, 0.85)
for m_ in (48, 52, 55):
    put(bgm, pad(midi(m_), JUMP + 1.2), 0.0, 0.05)
mystery(bgm, JUMP, POP + 0.4, 0.9, arp=True)
lofi(bgm, POP, S[6] + 0.5, 1.0)
mystery(bgm, S[6], DUR, 0.85, arp=True)

put(sfx, boom(2.0), 0.0, 0.4)
steps(0.05, JUMP - 0.1)
put(sfx, whoosh(0.5, True), JUMP - 0.2, 0.4)
put(sfx, boom(2.4), JUMP + 0.2, 0.55)
put(sfx, whoosh(3.0, False), JUMP + 0.3, 0.3)
transition(S[1])
put(sfx, boom(2.0), XT, 0.5)
for k in range(2, 8):
    transition(S[k])
put(sfx, whoosh(3.5, True), S[2] + 0.2, 0.35)                      # 加速
put(sfx, shimmer(1.4, True), S[3] + 0.4, 0.12)                    # 中心へ
put(sfx, crackle(S[5] - S[4]), S[4] + 0.2, 0.15)                   # 熱
put(sfx, splash(), POP, 0.6)                                       # ポン！
put(sfx, boom(1.6), POP, 0.35)
for k in range(4):                                                 # 行ったり来たり
    put(sfx, whoosh(0.9, k % 2 == 0), S[6] + 0.3 + k * 1.1, 0.18, pan=0.5 if k % 2 else -0.5)
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
