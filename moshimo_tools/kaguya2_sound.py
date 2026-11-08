"""かぐや様パロディ・長尺版（6本勝負）：BGM・効果音。BGMは最初から最後まで一定。
python3 kaguya2_sound.py taiyou_sound.py <動画長> <S1..S20（場面の開始秒）>"""
import numpy as np, wave, sys
src = open(sys.argv[1], encoding="utf-8").read().split("# ------------------------------------------------------------ compose")[0]
exec(src)

VID = float(sys.argv[2])
S = [float(x) for x in sys.argv[3].split(",")]
E = S[1:] + [VID]
TAIL = 2.6
DUR = VID + TAIL
N = int(SR * DUR)
bgm = np.zeros((N, 2)); sfx = np.zeros((N, 2))
# 場面の中でカットが切りかわる位置（kaguya2_voxel.py の cut() と同じ割合）
CUTS = {0: [0.45, 0.75], 1: [0.5], 2: [0.35, 0.7], 3: [0.55], 4: [0.45], 5: [0.4, 0.75], 6: [0.5], 8: [0.4, 0.75], 9: [0.5],
        10: [0.45], 11: [0.45], 12: [0.5], 13: [0.4], 14: [0.5], 15: [0.55], 16: [0.4], 17: [0.5], 19: [0.45]}


def at(k, f):
    return S[k] + (E[k] - S[k]) * f


def tone(f0, f1, d, a=0.005, r=0.1):
    n = int(SR * d)
    return np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f1, n)) / SR) * env(n, a, r)


def pop():
    return tone(500, 1100, 0.12, 0.005, 0.08)


def ping():   # スマホの通知
    return tone(1320, 1320, 0.15) * 0.6 + np.pad(tone(1760, 1760, 0.25), (int(0.12 * SR), 0))[:int(0.25 * SR)] * 0.6


def don(d=1.6):
    return boom(d) * 1.2


def door():   # バタン
    return lp(noise(0.25), 1500) * np.exp(-t_(0.25) * 18) * 2.0 + boom(0.9) * 0.8


lofi(bgm, 0.0, DUR, 0.9)

put(sfx, boom(1.6), 0.0, 0.35)
for k in range(1, len(S)):
    put(sfx, whoosh(0.4, True), S[k] - 0.4, 0.28)
for k, fr in CUTS.items():
    for f in fr:
        put(sfx, whoosh(0.25, True), at(k, f) - 0.2, 0.14)
put(sfx, whoosh(1.0, False), at(0, 0.45 * 0.35), 0.25)                # 1場面目：一気に引く
for j in range(3):
    put(sfx, pop(), at(2, 0.38) + j * 0.3, 0.3, pan=(j - 1) * 0.4)    # ？が3つ
put(sfx, sparkle(), at(3, 0.15), 0.1)                                 # チケット
put(sfx, don(), S[4], 0.6)                                            # 弟と行ってきます
put(sfx, ping(), at(5, 0.45), 0.3)
put(sfx, don(), S[6], 0.55)                                           # グループで十分です
put(sfx, pop(), S[7] + 0.15, 0.45)                                    # カエルのスタンプ
put(sfx, sparkle(), at(8, 0.05), 0.08)                                # お弁当
put(sfx, don(), S[9], 0.6)                                            # パン3個
r = lp(noise(E[12] - S[10]), 2500) * 0.35                              # 雨（昇降口の3場面）
f_ = int(0.3 * SR); r[:f_] *= np.linspace(0, 1, f_); r[-f_:] *= np.linspace(1, 0, f_)
put(sfx, r, S[10], 0.5)
put(sfx, don(), S[11], 0.6)                                           # 傘あげます
put(sfx, whoosh(2.0, True), at(11, 0.45), 0.2)                        # ダッシュ
put(sfx, don(), S[14], 0.55)                                          # 黒板の日付
put(sfx, pop(), at(16, 0.42), 0.35)                                   # 吹き出し
put(sfx, door(), at(17, 0.5) + 0.1 * (E[17] - S[17]) * 0.5, 0.8)      # バタン
put(sfx, chime_end(), S[18] + 0.2, 0.15)                              # 0勝6敗
put(sfx, chime_end(), VID - 0.2, 0.1)

fade = np.ones(N); fo = int(1.5 * SR); fade[-fo:] = np.linspace(1, 0, fo)
bgm *= fade[:, None]; sfx *= fade[:, None]


def write(name, x):
    x = x / max(1.0, np.abs(x).max() * 1.05)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


write("bgm.wav", bgm); write("sfx.wav", sfx); print("ok", DUR)
