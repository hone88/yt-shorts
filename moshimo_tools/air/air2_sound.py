"""空気の回（作り直し）：BGMで展開を作る版。
python3 air2_sound.py taiyou_sound.py <動画長> <S1..S8> <空が黒くなる秒> <いいえの直前の間> <もしの直前の間>"""
import numpy as np, wave, sys
src = open(sys.argv[1], encoding="utf-8").read().split("# ------------------------------------------------------------ compose")[0]
exec(src)

VID = float(sys.argv[2])
S = [float(x) for x in sys.argv[3].split(",")]
FL, NO, Q = float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
TAIL = 2.6
DUR = VID + TAIL
N = int(SR * DUR)
rng = np.random.default_rng(7)
bgm = np.zeros((N, 2)); sfx = np.zeros((N, 2))
I = lambda s: int(s * SR)


def transition(at, g=1.0):
    put(sfx, whoosh(0.45, True), at - 0.45, 0.32 * g)
    put(sfx, boom(1.6), at, 0.28 * g)


def riser(d):
    t = t_(d)
    return (whoosh(d, True) * 1.5 + np.sin(2 * np.pi * np.cumsum(np.linspace(200, 900, len(t))) / SR) * 0.25) * (t / d) ** 2


def tick():
    x = np.zeros(int(0.05 * SR)); x[:200] = rng.normal(0, 1, 200) * np.linspace(1, 0, 200)
    return lp(x, 4000)


def heartbeat(buf, t0, t1, bpm, gain):
    b = 60 / bpm; tt = t0
    while tt < t1:
        put(buf, kick(), tt, 0.22 * gain); put(buf, kick(), tt + 0.22, 0.14 * gain); tt += b


def drums(buf, t0, t1, bpm, gain, hats=True):
    b = 60 / bpm; tt = t0; k = 0
    while tt < t1:
        put(buf, kick(), tt, 0.20 * gain)
        if hats:
            put(buf, hat(), tt + b / 2, 0.06 * gain)
        tt += b; k += 1


# --- 1. 明るい日常のBGMが0秒から鳴る → 空が黒くなった瞬間にテープが止まるように「ヒュウン」と止まる
L = np.zeros((N, 2)); lofi(L, 0.0, FL + 2, 1.1)
D = 0.5; n = np.arange(I(D)); pos = I(FL) + np.cumsum(1 - n / len(n))
stop = np.stack([np.interp(pos, np.arange(N), L[:, c]) for c in (0, 1)], 1) * np.linspace(1, 0.3, len(n))[:, None]
L[I(FL):] = 0; L[I(FL):I(FL) + len(n)] = stop
bgm += L
put(sfx, boom(2.0), 0.0, 0.45)
put(sfx, boom(2.4), FL + 0.05, 0.7)
put(sfx, shimmer(1.2, True), FL, 0.12)

# --- 2. 不安なパッド＋心臓の音がだんだん速く → 「……」でほぼ無音 → 「いいえ」でドン
mystery(bgm, FL + 0.4, NO, 0.9, arp=False)
heartbeat(sfx, S[1] + 0.1, NO - 0.2, 80, 0.9)
put(sfx, riser(NO - S[1] - 0.2), S[1], 0.22)
put(sfx, boom(2.6), NO + 0.35, 0.75)
put(sfx, shimmer(1.4, False), NO + 0.35, 0.10)

# --- 3〜6. 本編のテーマ：オルゴールの不思議なメロディ。シーンが進むたびに楽器が増えていく
mystery(bgm, NO + 0.35, S[6] - 0.05, 1.0, arp=True)
# 3. 音が消える：BGMを「こもった音」に（空気がなく音が届かない感じ）＋耳鳴り
a, b = I(S[2]), I(S[3])
for c in (0, 1):
    bgm[a:b, c] = lp(bgm[a:b, c], 350, 2) * 1.4
t = t_(3.0); put(sfx, np.sin(2 * np.pi * 6000 * t) * env(len(t), 0.4, 1.5) * 0.12, S[2] + 0.6, 0.25)
transition(S[2])
# 4. 落ちる：キックが入る＋下がる風切り音
transition(S[3])
drums(bgm, S[3], S[5], 70, 0.9, hats=False)
put(sfx, whoosh(2.5, False), S[3] + 0.3, 0.28)
# 5. 肺：ハイハットも入ってテンポ感アップ＋シューッ
transition(S[4])
drums(bgm, S[4], S[5], 140, 0.5, hats=True)
put(sfx, lp(noise(2.5), 3000) * env(I(2.5), 0.2, 0.6), S[4] + 0.4, 0.16)
# 6. つば：ぶくぶく＋上がっていく音で「10秒」へためる
transition(S[5])
drums(bgm, S[5], S[6] - 0.6, 140, 0.8, hats=True)
tt = S[5] + 0.3
while tt < S[6] - 0.4:
    put(sfx, bubble(), tt, 0.11, pan=rng.uniform(-0.5, 0.5)); tt += rng.uniform(0.05, 0.16)
put(sfx, riser(S[6] - S[5]), S[5], 0.30)

# --- 7. 空気が戻る：一瞬の無音 → 大きなドンと風 → 明るいBGMが全開で戻る
put(sfx, boom(2.6), S[6], 0.8)
put(sfx, whoosh(1.2, False), S[6], 0.5)
lofi(bgm, S[6] + 0.05, Q, 1.25)
put(sfx, birds(Q - S[6]), S[6] + 0.6, 0.06, pan=0.4)

# --- 8. 「……もし」でBGMがぶつっと止まる → 低い不安な音とチクタク → 声のあとは音楽だけで余韻
put(sfx, shimmer(1.0, True), Q - 0.1, 0.10)
mystery(bgm, Q + 0.3, DUR, 0.9, arp=True)
for k in range(int((VID - Q) / 0.5)):
    put(sfx, tick(), Q + 0.3 + k * 0.5, 0.22)
put(sfx, boom(2.0), Q + 0.3, 0.4)
put(sfx, chime_end(), VID - 0.2, 0.12)

fade = np.ones(N); fo = I(1.5); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
