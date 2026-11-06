"""ガクチカ・ループ 第5話の音。python3 mix_ep5.py → out_ep5/ガクチカループ_第5話.mp4"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep5 as V

OUT = V.OUT
SH = V.SH
total = sum(s.dur for s in SH)
S = {s.name: s for s in SH}
voice = np.zeros(int(total * A.SR) + A.SR)
fx = np.zeros_like(voice)
music = np.zeros_like(voice)
for s in SH:
    for (t0, sid) in s.lines:
        A.put(voice, V.vo(sid), s.start + t0)
wk, es, ca, ty, f1, f2, kc, en = (S[k] for k in ("wake", "esis", "call", "type", "first", "second", "kick", "end"))


def dark(sec):
    return A.bgm_dark(max(sec, 3.0))[:int(sec * A.SR)]


# 0秒：2周目の12月5日。ドン → 2.4秒でタイトル
A.put(fx, A.sfx_boom(0.85, 2.4), 0.02)
A.put(fx, A.sfx_pop(0.35), 0.05)
A.put(fx, A.sfx_tick(0.25), 0.3)
A.put(music, A.amb_room(wk.dur, 0.05), 0)
A.put(music, A.fade(A.bgm_sparse(wk.dur + 0.3), 0.05, 0.4), 0)
A.put(fx, A.sfx_transition(0.6), 2.4 - 0.45)
A.put(fx, A.sfx_riser(0.6, 0.3), wk.lines[1][0] - 0.6)
A.put(fx, A.sfx_ding(0.35), wk.lines[1][0] + V.L("02"))
# ES・IS：メッセージ → 画面 → 空欄（ドン）→ トケイ
A.put(fx, A.sfx_transition(0.5), es.start - 0.45)
A.put(music, A.amb_room(es.dur + ca.dur + ty.dur, 0.04), es.start)
A.put(fx, A.sfx_notify(0.35), es.start + 0.2)
A.put(fx, A.sfx_pop(0.35), es.start + es.form)
A.put(music, A.fade(A.bgm_morning(es.lines[1][0] + 0.2), 0.3, 0.4), es.start)
A.put(fx, A.sfx_boom(0.7, 2.0), es.start + es.lines[1][0] + 0.2)
A.put(music, A.fade(dark(es.dur - es.lines[1][0]), 0.2, 0.4), es.start + es.lines[1][0])
A.put(fx, A.sfx_whoosh(0.5, False, 0.3), es.start + es.lines[2][0] - 0.5)
# 通話：やわらかく。「それ、書けるじゃん」でキラッ
A.put(fx, A.sfx_transition(0.5), ca.start - 0.45)
A.put(fx, A.sfx_ding(0.3), ca.start + 0.1)
A.put(music, A.fade(A.bgm_sparse(ca.lines[3][0]), 0.4, 0.5), ca.start)
A.put(fx, A.sfx_riser(0.6, 0.3), ca.start + ca.lines[4][0] - 0.6)
A.put(music, A.fade(A.bgm_morning(ca.dur - ca.lines[4][0] + ty.dur + 0.2, bright=True), 0.2, 0.6), ca.start + ca.lines[4][0])
A.put(fx, A.sfx_ding(0.4), ca.start + ca.lines[4][0])
# 入力：キーの音
for k in range(10):
    A.put(fx, A.sfx_tick(0.18), ty.start + 0.25 + k * 0.15)
A.put(fx, A.sfx_pop(0.35), ty.start + 1.75)
A.put(fx, A.sfx_ding(0.35), ty.start + ty.lines[1][0])
# ダイジェスト：テンポよく
A.put(fx, A.sfx_transition(0.6), f1.start - 0.45)
A.put(music, A.amb_room(f1.dur + f2.dur, 0.05), f1.start)
A.put(music, A.fade(A.bgm_morning(f1.dur + f2.rev, bright=False), 0.3, 0.4), f1.start)
A.put(fx, A.sfx_heart(0.4), f1.start + f1.lines[1][0] - 0.3)
A.put(fx, A.sfx_pop(0.3), f1.start + f1.dur - 0.85)
A.put(fx, A.sfx_transition(0.55), f2.start - 0.45)
A.put(fx, A.sfx_boom(0.6, 1.8), f2.start + 0.5)                  # 今度は、ここにいる。
A.put(fx, A.sfx_heart(0.45), f2.start + f2.lines[1][0] - 0.3)
A.put(fx, A.sfx_riser(0.6, 0.3), f2.start + f2.rev - 0.6)
A.put(fx, A.sfx_boom(0.9, 2.4), f2.start + f2.rev)               # 活動先 決定
A.put(fx, A.sfx_chime_end(), f2.start + f2.rev + 0.05)
# キックオフ会場へ
A.put(fx, A.sfx_transition(0.6), kc.start - 0.45)
A.put(music, A.amb_crowd(kc.dur, 0.1), kc.start)
A.put(music, A.fade(A.bgm_morning(kc.dur, bright=True), 0.4, 0.5), kc.start)
A.put(fx, A.sfx_whoosh(0.5, False, 0.3), kc.start + kc.lines[1][0] - 0.5)
A.put(fx, A.sfx_ding(0.35), kc.start + kc.lines[2][0])
# 終わり
A.put(fx, A.sfx_transition(0.6), en.start - 0.45)
A.put(fx, A.sfx_boom(0.9, 2.4), en.start + 0.05)
A.put(music, A.fade(A.bgm_morning(en.dur, bright=True) * 1.1, 0.1, 1.5), en.start)
A.put(fx, A.sfx_chime_end(), en.start + 0.3)

music = A.duck(music, voice, 0.6)
mix = voice * 1.0 + fx * 0.8 + music * 0.9
mix = mix[:int(total * A.SR)]
mix /= np.abs(mix).max() / 0.95
p = f"{OUT}/mix.wav"
with wave.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = f"{OUT}/ガクチカループ_第5話.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
