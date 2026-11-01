"""空気の回（作り直し版の映像）に、前のシンプルな音の付け方を合わせる。
BGMは途切れさせない。効果音は場面の切り替わり（シュッ→ドン）と、短い効果音だけ。"""
import numpy as np, wave, sys
src = open(sys.argv[1], encoding="utf-8").read().split("# ------------------------------------------------------------ compose")[0]
exec(src)

VID = float(sys.argv[2])
S = [float(x) for x in sys.argv[3].split(",")]
FL, NO, RT = float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
TAIL = 2.6
DUR = VID + TAIL
N = int(SR * DUR)
rng = np.random.default_rng(6)
bgm = np.zeros((N, 2)); sfx = np.zeros((N, 2))


def transition(at):
    put(sfx, whoosh(0.45, True), at - 0.45, 0.35)
    put(sfx, boom(1.6), at, 0.30)


# BGM：明るい曲 → 空が黒くなったら不思議な曲（自然につなぐ）→ 空が戻ったら明るい曲 → 最後は不思議な曲
lofi(bgm, 0.0, FL + 0.6, 0.8)
for m in (48, 52, 55):
    put(bgm, pad(midi(m), FL + 1.2), 0.0, 0.05)
mystery(bgm, FL, RT + 0.3, 0.85, arp=True)
lofi(bgm, RT, S[7] + 0.5, 1.0)
beat = 60 / 92; bar = 4 * beat; prog = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]
b = 0
while RT + b * bar < S[7] + 0.5:   # 明るい曲の下に、音が途切れないよう柔らかい和音を敷く
    for m in prog[b % 4]:
        put(bgm, pad(midi(m - 12), bar + 0.8), RT + b * bar, 0.05)
    b += 1
lofi(bgm, 0.0, 0.0, 0)
mystery(bgm, S[7], DUR, 0.85, arp=True)

# 1. 0秒：ドン＋空が黒くなる瞬間のキラッ
put(sfx, boom(2.0), 0.0, 0.45)
put(sfx, shimmer(1.2, True), FL - 0.05, 0.14)
put(sfx, boom(2.4), FL, 0.6)
# 2. 破裂する？→「いいえ」でドン
transition(S[1])
put(sfx, boom(2.0), NO, 0.5)
# 3〜6. 場面ごとのシュッ→ドンと、短い効果音
for k in (2, 3, 4, 5, 6, 7):
    transition(S[k])
put(sfx, whoosh(2.5, False), S[3] + 0.3, 0.25)                       # 落ちる
put(sfx, lp(noise(2.0), 3000) * env(int(2.0 * SR), 0.2, 0.6), S[4] + 0.4, 0.12)  # 息
tt = S[5] + 0.3
while tt < S[6] - 0.3:                                                 # ぶくぶく
    put(sfx, bubble(), tt, 0.10, pan=rng.uniform(-0.4, 0.4)); tt += rng.uniform(0.06, 0.2)
# 7. 空が戻る：風とドン
put(sfx, whoosh(1.0, False), RT, 0.35)
put(sfx, boom(2.0), RT, 0.45)
# 8. 終わりのチーン
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
