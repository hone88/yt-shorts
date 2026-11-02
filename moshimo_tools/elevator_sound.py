"""7本目エレベーターのBGM・効果音（シンプル版：BGMは途切れさせない）。
python3 elevator_sound.py taiyou_sound.py <動画長> <S1..S8> <落ちはじめ秒> <×の秒> <ブレーキで止まる秒>"""
import numpy as np, wave, sys
src = open(sys.argv[1], encoding="utf-8").read().split("# ------------------------------------------------------------ compose")[0]
exec(src)

VID = float(sys.argv[2])
S = [float(x) for x in sys.argv[3].split(",")]
FALL, XT, STOP = float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
TAIL = 2.6
DUR = VID + TAIL
N = int(SR * DUR)
rng = np.random.default_rng(9)
bgm = np.zeros((N, 2)); sfx = np.zeros((N, 2))


def transition(at):
    put(sfx, whoosh(0.45, True), at - 0.45, 0.35)
    put(sfx, boom(1.6), at, 0.30)


def ding():
    return bell(midi(84), 1.2) * 0.8 + bell(midi(79), 1.2) * 0.5


def screech(d):
    t = t_(d)
    f = 2400 + 300 * np.sin(2 * np.pi * 7 * t)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4 + (lp(noise(d), 6000) - lp(noise(d), 1500)) * 0.8) * env(len(t), 0.05, 0.3)


# BGM：最初は明るい日常 → 落ちたら不思議な曲 → ブレーキで止まったら明るい曲に戻る（最後まで続ける）
lofi(bgm, 0.0, FALL + 0.5, 0.8)
for m_ in (48, 52, 55):
    put(bgm, pad(midi(m_), FALL + 1.2), 0.0, 0.05)
mystery(bgm, FALL, STOP + 0.5, 0.9, arp=True)
lofi(bgm, STOP, DUR, 0.9)

# 1. 「チン」→ 落ちはじめにドン＋下がる風の音
put(sfx, ding(), 0.0, 0.12)
put(sfx, boom(2.0), 0.0, 0.4)
put(sfx, boom(2.4), FALL, 0.6)
put(sfx, whoosh(2.4, False), FALL, 0.3)
# 2. 「いいえ」で×と同時にドン
transition(S[1])
put(sfx, boom(2.0), XT, 0.5)
# 3〜8. 場面の切り替わり
for k in range(2, 8):
    transition(S[k])
put(sfx, whoosh(3.0, False), S[3] + 0.2, 0.3)          # 4. 速く落ちる
put(sfx, whoosh(2.0, False), S[3] + 3.2, 0.25)
# 6. ブレーキ：キーッ＋火花 → 止まった瞬間にガコン
put(sfx, screech(STOP - S[5]), S[5] + 0.2, 0.18)
put(sfx, crackle(STOP - S[5]), S[5] + 0.2, 0.12)
put(sfx, boom(2.0), STOP, 0.55)
# 8. 最後
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
