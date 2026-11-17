"""ガクチカ・ループ 第13話の音。python3 mix_ep13.py → out_ep13/ガクチカループ_第13話.mp4
転換音・環境音は6割（第8話以降の決まり）。ミュート中のカナタの声はこもらせて小さく。"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep13 as V

OUT = V.OUT


def TR(*a):
    return A.sfx_transition(*a) * 0.6


def AMB_R(*a):
    return A.amb_room(*a) * 0.6


def heavy(sec):
    return A.bgm_heavy(max(sec, 3.6))[:int(sec * A.SR)]


SH = V.SH
total = sum(s.dur for s in SH)
S = {s.name: s for s in SH}
voice = np.zeros(int(total * A.SR) + A.SR)
fx = np.zeros_like(voice)
music = np.zeros_like(voice)
for s in SH:
    for (t0, sid) in s.lines:
        y = V.vo(sid)
        if sid == "04":                      # ミュート：こもった小さい声
            y = A.lowpass(y, 0.06) * 0.55
        A.put(voice, y, s.start + t0)
co, ca, ff, mu, idea, bo, rm, en = (S[k] for k in ("cold", "call", "ff", "mute", "idea", "board", "room", "end"))

# 0秒：ドン（ミュートのカナタ）→ 2.4秒でタイトル
A.put(fx, A.sfx_boom(0.9, 2.4), 0.02)
A.put(voice, A.lowpass(V.vo("04"), 0.06) * 0.45, 0.35)
A.put(music, A.fade(A.bgm_sparse(co.dur + 0.3), 0.05, 0.4), 0)
A.put(music, AMB_R(total, 0.05), 0)
A.put(fx, TR(0.6), 2.4 - 0.45)

# 19:00 通話：カード → 声が重なる。重い低音
A.put(fx, TR(0.55), ca.start - 0.45)
A.put(fx, A.sfx_ding(0.3), ca.start + 0.1)
A.put(fx, A.sfx_pop(0.4), ca.start + 0.2)
A.put(music, A.fade(heavy(ca.dur + ff.dur + 0.3) * 0.8, 0.3, 0.4), ca.start + 2.6)
A.put(music, A.fade(A.bgm_sparse(2.9), 0.2, 0.3), ca.start)

# 早送り：吹き出しごとにポン、ストップウォッチ
A.put(fx, A.sfx_whoosh(0.5, True, 0.3), ff.start)
A.put(fx, A.sfx_stopwatch(ff.dur, 0.25, 0.18), ff.start)
for j in range(len(V.BUBBLES)):
    A.put(fx, A.sfx_pop(0.3), ff.start + 0.3 + j * 0.45)

# 21:31 整理しよう（秒針）→ ミュート →「えっ」でポン、くすっ
A.put(fx, TR(0.5), mu.start - 0.45)
A.put(fx, A.sfx_stopwatch(mu.lines[2][0], 0.5, 0.18), mu.start)
A.put(music, A.fade(A.bgm_sparse(mu.dur + 0.3), 0.3, 0.3), mu.start)
A.put(fx, A.sfx_pop(0.45), mu.start + mu.unmute)

# ひと言：声の前に間 → ドン → 1秒の静けさ →「それだ」→ 明るいBGM
A.put(fx, A.sfx_riser(0.8, 0.4), idea.start + idea.lines[0][0] - 0.85)
A.put(fx, A.sfx_heart(0.5), idea.start + 0.2)
A.put(fx, A.sfx_boom(1.0, 2.8), idea.start + idea.hit)
t8 = idea.start + idea.lines[1][0]
A.put(music, A.fade(A.bgm_morning(idea.start + idea.dur - t8 + bo.dur + 0.3), 0.2, 0.4), t8)

# ホワイトボード：ふせんごとにポン
A.put(fx, TR(0.5), bo.start - 0.45)
for j in range(5):
    A.put(fx, A.sfx_pop(0.3), bo.start + 0.6 + j * 0.45)

# 通話のあと：トケイ → 明るい締め
A.put(fx, TR(0.5), rm.start - 0.45)
A.put(fx, A.sfx_pop(0.3), rm.start + 0.3)
A.put(music, A.fade(A.bgm_morning(rm.dur + en.dur + 0.3, bright=True), 0.4, 1.5), rm.start)
A.put(fx, A.sfx_tick(0.25), en.start + 0.3)

music = A.duck(music, voice, 0.6)
FX_LEVEL = 0.7   # 11/17 ゆうきさん：効果音を7割に
mix = voice * 1.0 + fx * 0.8 * FX_LEVEL + music * 0.9
mix = mix[:int(total * A.SR)]
mix /= np.abs(mix).max() / 0.95
p = f"{OUT}/mix.wav"
with wave.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = f"{OUT}/ガクチカループ_第13話.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
