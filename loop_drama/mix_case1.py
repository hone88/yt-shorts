"""インターン生、事件です。#1 の音。python3 mix_case1.py → out_case1/インターン生事件です_1.mp4"""
import os, subprocess, wave
import numpy as np
import audio as A
import case1 as V

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
co, of, st, wa, gr, tk, bk, en = (S[k] for k in ("cold", "office", "street", "wait", "greet", "talk", "back", "end"))

# 0秒：ピンチの真っ最中。ドン＋心臓＋秒針。2.4秒でタイトル
A.put(fx, A.sfx_boom(0.85, 2.4), 0.02)
A.put(fx, A.sfx_pop(0.35), 0.05)
A.put(music, A.amb_room(co.dur, 0.05), 0)
A.put(music, A.fade(A.bgm_heavy(co.dur + 0.3), 0.05, 0.4), 0)
A.put(fx, A.sfx_heart(0.55), 0.6); A.put(fx, A.sfx_heart(0.6), 1.3)
A.put(fx, A.sfx_transition(0.6), 2.4 - 0.45)
# 2時間前：明るい日常
A.put(fx, A.sfx_rewind(), of.start - 0.6)
A.put(music, A.amb_room(of.dur, 0.05), of.start)
A.put(music, A.fade(A.bgm_morning(of.dur + 0.3), 0.4, 0.4), of.start)
A.put(fx, A.sfx_pop(0.35), of.start + of.card)
A.put(fx, A.sfx_boom(0.5, 1.8), of.start + of.lines[1][0])
# 11:40 電話→急用：不安な持続音
A.put(fx, A.sfx_transition(0.55), st.start - 0.45)
A.put(music, A.amb_crowd(st.dur, 0.1), st.start)
for k in range(3):
    A.put(fx, A.sfx_notify(0.35), st.start + 0.1 + k * 0.35)
A.put(music, A.fade(A.bgm_dark(st.dur + wa.dur), 0.8, 0.4), st.start + 0.6)
A.put(fx, A.sfx_riser(0.6, 0.35), st.start + st.lines[1][0] - 0.6)
A.put(fx, A.sfx_boom(0.9, 2.4), st.start + st.lines[1][0])
# 11:50 残り10分：秒針と心臓
A.put(fx, A.sfx_transition(0.5), wa.start - 0.45)
A.put(fx, A.sfx_stopwatch(wa.dur, 0.5, 0.22), wa.start)
A.put(fx, A.sfx_heart(0.5), wa.start + 0.3); A.put(fx, A.sfx_heart(0.55), wa.start + 1.2)
# 12:00 あいさつ：逆さま→名乗る瞬間にドン
A.put(music, A.amb_room(gr.dur + tk.dur + bk.dur, 0.05), gr.start)
A.put(music, A.fade(A.bgm_sparse(gr.dur + tk.dur), 0.4, 0.4), gr.start)
A.put(fx, A.sfx_pop(0.4), gr.start + gr.flip)
A.put(fx, A.sfx_whoosh(0.4, True, 0.3), gr.start + gr.lines[0][0] - 0.3)
A.put(fx, A.sfx_boom(0.7, 2.2), gr.start + gr.lines[0][0])
A.put(fx, A.sfx_heart(0.45), tk.start + tk.lines[1][0] - 0.3)
# 12:30 議員さんが戻る：明るく
A.put(fx, A.sfx_transition(0.55), bk.start - 0.45)
A.put(music, A.fade(A.bgm_morning(bk.dur, bright=True), 0.4, 0.4), bk.start)
A.put(fx, A.sfx_ding(0.35), bk.start + bk.lines[2][0])
# 終わり
A.put(fx, A.sfx_transition(0.55), en.start - 0.45)
A.put(music, A.fade(A.bgm_morning(en.dur, bright=True) * 1.1, 0.2, 1.5), en.start)
A.put(fx, A.sfx_chime_end(), en.start + 0.05)
A.put(fx, A.sfx_pop(0.3), en.start + 0.3)

music = A.duck(music, voice, 0.6)
mix = voice * 1.0 + fx * 0.8 + music * 0.9
mix = mix[:int(total * A.SR)]
mix /= np.abs(mix).max() / 0.95
p = f"{OUT}/mix.wav"
with wave.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = f"{OUT}/インターン生事件です_1.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
