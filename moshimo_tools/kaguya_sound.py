"""かぐや様パロディの回：BGM・効果音（シンプル版：BGMは最初から最後まで一定）。
python3 kaguya_sound.py taiyou_sound.py <動画長> <S1..S9>"""
import numpy as np, wave, sys
src = open(sys.argv[1], encoding="utf-8").read().split("# ------------------------------------------------------------ compose")[0]
exec(src)

VID = float(sys.argv[2])
S = [float(x) for x in sys.argv[3].split(",")]
TAIL = 2.6
DUR = VID + TAIL
N = int(SR * DUR)
rng = np.random.default_rng(21)
bgm = np.zeros((N, 2)); sfx = np.zeros((N, 2))


def transition(at):
    put(sfx, whoosh(0.4, True), at - 0.4, 0.3)


def rain_bed(d):  # 雨のサーッ
    return lp(noise(d), 2500) * 0.35


def pop():  # ポン（？ブロック）
    return np.sin(2 * np.pi * np.cumsum(np.linspace(500, 1100, int(SR * 0.12))) / SR) * env(int(SR * 0.12), 0.005, 0.08)


def don(d=1.6):  # ドン（オチ）
    return boom(d) * 1.2


# BGM：明るいローファイを最後まで同じ音量で
lofi(bgm, 0.0, DUR, 0.9)

put(sfx, boom(1.6), 0.0, 0.35)                 # 1コマ目
put(sfx, whoosh(1.2, False), 1.0, 0.25)        # 一気に引く
for k in range(1, 9):
    transition(S[k])
for j in range(3):                             # ？が3つポンポンポン
    put(sfx, pop(), S[1] + 0.3 + j * 0.35, 0.35, pan=(j - 1) * 0.4)
put(sfx, whoosh(0.6, True), S[2] + 0.3, 0.25)  # 画面の外から手
put(sfx, don(), S[3], 0.6)                     # 「2枚ともください」
put(sfx, sparkle(), S[3] + 0.2, 0.1)
r = rain_bed(S[6] - S[4])                      # 雨（昇降口の2場面だけ）
r[: int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR)); r[-int(0.3 * SR):] *= np.linspace(1, 0, int(0.3 * SR))
put(sfx, r, S[4], 0.5)
put(sfx, don(), S[5], 0.6)                     # 「傘、あげます！」
put(sfx, whoosh(2.0, True), S[5] + 0.3, 0.2)   # 雨の中へダッシュ
put(sfx, don(), S[7] + 1.4, 0.75)              # 「ナイフ」ドヤ顔で揺れる
put(sfx, chime_end(), S[8] + 0.2, 0.15)        # 0勝3敗
put(sfx, chime_end(), VID - 0.2, 0.1)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
