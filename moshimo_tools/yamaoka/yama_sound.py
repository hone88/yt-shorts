"""山岡家（作り直し版）のBGM・効果音。taiyou_sound.py の部品を使う。"""
import numpy as np, wave, sys
src = open(sys.argv[1], encoding="utf-8").read().split("# ------------------------------------------------------------ compose")[0]
exec(src)  # SR, put, lofi, mystery, boom, whoosh, shimmer, bubble, birds, chime_end, ... を読み込む

VID = 45.265                     # 完成版の長さ
TAIL = 2.6                       # 声のあとの余韻
DUR = VID + TAIL
N = int(SR * DUR)
S = [0.0, 5.956, 14.564, 21.198, 28.131, 34.031, 40.367]   # 各シーンの開始
VAN = 0.99                       # ラーメンが消える瞬間
rng = np.random.default_rng(5)

bgm = np.zeros((N, 2)); sfx = np.zeros((N, 2))


def room(d):  # 夜の店内の空気（途切れさせないための下地）
    t = t_(d)
    return lp(noise(d), 400, 2) * 2.2 * env(len(t), 0.3, 0.8) + np.sin(2 * np.pi * 60 * t) * 0.05


def cut_click():
    x = np.zeros(int(0.03 * SR)); x[:250] = rng.normal(0, 1, 250) * np.linspace(1, 0, 250)
    return x


def transition(at):  # シリーズ共通の転換音：シュッ（0.45秒前から）→ドン
    put(sfx, whoosh(0.45, True), at - 0.45, 0.35)
    put(sfx, boom(1.6), at, 0.30)


def engine(d):
    t = t_(d); f = 38 + 6 * np.sin(2 * np.pi * 0.5 * t)
    return lp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)), 300, 2) * env(len(t), 0.6, 1.0)


def car_pass(d=2.2):
    t = t_(d)
    return (lp(noise(d), 900) * 2 + engine(d) * 0.6) * np.sin(np.pi * t / d) ** 2


# 1. 深夜のカウンター：0秒からドン＋静かなローファイ → 消えた瞬間に音楽が「ブツッ」と止まる
put(sfx, boom(2.0), 0.0, 0.45)
put(sfx, room(DUR), 0.0, 0.10)
lofi(bgm, 0.0, VAN, 0.8)
put(sfx, cut_click(), VAN - 0.01, 0.5)
put(sfx, boom(2.4), VAN, 0.75)
put(sfx, shimmer(1.2, True), VAN + 0.05, 0.12)
mystery(bgm, VAN + 0.8, S[1] - 0.05, 0.9, arp=False)

# 2. 1988年・牛久：なつかしい空気
transition(S[1])
lofi(bgm, S[1] + 0.3, S[3] - 0.1, 0.75)

# 3. 深夜の駐車場：トラックのエンジン
transition(S[2])
put(sfx, engine(S[3] - S[2] - 0.5), S[2] + 0.3, 0.10)

# 4. 大鍋：ぐつぐつ・火の音
transition(S[3])
mystery(bgm, S[3] + 0.2, S[4] - 0.05, 0.7, arp=True)
tt = S[3] + 0.3
while tt < S[4] - 0.3:
    put(sfx, bubble(), tt, 0.10, pan=rng.uniform(-0.4, 0.4)); tt += rng.uniform(0.08, 0.25)
put(sfx, lp(noise(S[4] - S[3]), 2500) * 0.6, S[3] + 0.2, 0.05)

# 5. ラーメン難民：不安なパッド＋車が通り過ぎる
transition(S[4])
mystery(bgm, S[4] + 0.2, S[5] - 0.05, 1.0, arp=False)
put(sfx, car_pass(2.4), S[4] + 0.4, 0.22, pan=-0.6)
put(sfx, car_pass(2.4), S[4] + 2.6, 0.22, pan=0.6)

# 6. 朝6時：明るいローファイ＋鳥
transition(S[5])
lofi(bgm, S[5] + 0.2, DUR, 1.0)
put(sfx, birds(S[6] - S[5]), S[5] + 0.3, 0.05, pan=0.4)

# 7. あなたは？：問いかけの前に「チーン」、声のあとは音楽だけで余韻
put(sfx, whoosh(0.45, True), S[6] - 0.45, 0.3)
put(sfx, sparkle(), S[6], 0.08)
put(sfx, chime_end(), VID - 0.2, 0.12)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
