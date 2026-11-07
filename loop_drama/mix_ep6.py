"""ガクチカ・ループ 第6話の音。python3 mix_ep6.py → out_ep6/ガクチカループ_第6話.mp4"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep6 as V

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
bw, hl, cd, gl, dr, gm, st, en = (S[k] for k in ("bow", "hall", "card", "goal", "dream", "game", "street", "end"))

# 0秒：お辞儀。ドン＋会場のざわめき。2.4秒でタイトル
A.put(fx, A.sfx_boom(0.85, 2.4), 0.02)
A.put(fx, A.sfx_pop(0.35), 0.05)
A.put(music, A.amb_crowd(bw.dur + hl.dur + cd.dur, 0.1), 0)
A.put(music, A.fade(A.bgm_morning(bw.dur + 0.3), 0.05, 0.4) * 0.8, 0)
A.put(fx, A.sfx_transition(0.6), 2.4 - 0.45)
# 会場：明るく
A.put(fx, A.sfx_transition(0.55), hl.start - 0.45)
A.put(music, A.fade(A.bgm_morning(hl.dur + cd.dur, bright=True), 0.3, 0.4), hl.start)
A.put(fx, A.sfx_pop(0.3), hl.start + 0.15)
A.put(fx, A.sfx_pop(0.28), hl.start + 0.45)
# 名刺の練習
A.put(fx, A.sfx_transition(0.5), cd.start - 0.45)
A.put(fx, A.sfx_pop(0.32), cd.start + 0.45)
# 目標シート：秒針
A.put(fx, A.sfx_transition(0.5), gl.start - 0.45)
A.put(music, A.amb_room(gl.dur + dr.dur, 0.05), gl.start)
A.put(fx, A.sfx_pop(0.35), gl.start + 0.2)
A.put(fx, A.sfx_stopwatch(gl.dur - 0.3, 0.5, 0.18), gl.start + 0.3)
A.put(fx, A.sfx_boom(0.5, 1.6), gl.start + gl.lines[0][0] + V.L("05") * 0.65)   # 面接で答える…
# ハルトの目標：静かに
A.put(music, A.fade(A.bgm_sparse(dr.dur + 0.3), 0.6, 0.6), dr.start)
A.put(fx, A.sfx_ding(0.3), dr.start + dr.lines[0][0] + V.L("07") + 0.1)
# ミニゲーム：ポン、ハイタッチ
A.put(fx, A.sfx_transition(0.55), gm.start - 0.45)
A.put(music, A.amb_crowd(gm.dur, 0.12), gm.start)
A.put(music, A.fade(A.bgm_morning(gm.dur, bright=True), 0.3, 0.5), gm.start)
A.put(fx, A.sfx_pop(0.4), gm.start + gm.lines[0][0] + 0.1)
A.put(fx, A.sfx_boom(0.7, 1.8), gm.start + gm.hi)
A.put(fx, A.sfx_pop(0.45), gm.start + gm.hi)
# 帰り道：街のざわめき
A.put(fx, A.sfx_transition(0.55), st.start - 0.45)
A.put(music, A.amb_crowd(st.dur, 0.07), st.start)
A.put(music, A.fade(A.bgm_sparse(st.dur), 0.4, 0.5), st.start)
A.put(fx, A.sfx_whoosh(0.4, False, 0.3), st.start + st.lines[0][0] - 0.4)
A.put(fx, A.sfx_ding(0.3), st.start + st.lines[1][0] + 0.1)
# 終わり
A.put(fx, A.sfx_transition(0.6), en.start - 0.45)
A.put(music, A.fade(A.bgm_morning(en.dur, bright=True) * 1.1, 0.1, 1.5), en.start)
A.put(fx, A.sfx_chime_end(), en.start + 0.1)

music = A.duck(music, voice, 0.6)
mix = voice * 1.0 + fx * 0.8 + music * 0.9
mix = mix[:int(total * A.SR)]
mix /= np.abs(mix).max() / 0.95
p = f"{OUT}/mix.wav"
with wave.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = f"{OUT}/ガクチカループ_第6話.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
