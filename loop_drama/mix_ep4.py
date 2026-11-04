"""ガクチカ・ループ 第4話の音。python3 mix_ep4.py → out_ep4/ガクチカループ_第4話.mp4"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep4 as V

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
co, rm, bd, tk, bw, ff, iv, wk, en = (S[k] for k in ("cold", "room2", "bed", "tokei", "bow", "ff", "iv", "wake", "end"))


def dark(sec):
    return A.bgm_dark(max(sec, 3.0))[:int(sec * A.SR)]


# 0秒：布団の中。ドン＋スマホの振動。2.4秒でタイトル
A.put(fx, A.sfx_boom(0.85, 2.4), 0.02)
A.put(fx, A.sfx_pop(0.35), 0.05)
for k in range(6):
    A.put(fx, A.sfx_notify(0.22), 0.3 + k * 0.7)
A.put(music, A.fade(dark(co.dur + 0.3), 0.05, 0.4), 0)
A.put(fx, A.sfx_heart(0.55), 0.7); A.put(fx, A.sfx_heart(0.6), 1.4)
A.put(fx, A.sfx_transition(0.6), 2.4 - 0.45)
# 2次選考会の部屋：静けさ。秒針だけ
A.put(fx, A.sfx_transition(0.55), rm.start - 0.45)
A.put(music, A.amb_room(rm.dur + 0.2, 0.06), rm.start)
A.put(fx, A.sfx_stopwatch(rm.dur, 0.5, 0.22), rm.start + 0.2)
A.put(fx, A.sfx_boom(0.55, 1.8), rm.start + 0.75)                     # 空いた席
A.put(fx, A.sfx_notify(0.3), rm.start + rm.lines[1][0] - 0.3)          # ミオが電話
# 布団：ミオのメッセージ
A.put(fx, A.sfx_transition(0.5), bd.start - 0.45)
A.put(music, A.amb_room(bd.dur + tk.dur, 0.04), bd.start)
A.put(music, A.fade(A.bgm_sparse(bd.dur + 0.2), 0.4, 0.5), bd.start)
A.put(fx, A.sfx_notify(0.35), bd.start + 0.2)
A.put(fx, A.sfx_heart(0.5), bd.start + bd.lines[1][0] - 0.2)
# トケイ
A.put(fx, A.sfx_whoosh(0.5, False, 0.35), tk.start + 0.05)
A.put(fx, A.sfx_alarm(), tk.start + 0.4)
A.put(music, A.fade(dark(tk.dur), 0.3, 0.4), tk.start)
A.put(fx, A.sfx_boom(0.7, 2.0), tk.start + tk.lines[0][0] + V.L("06") * 0.7)
# ミオが頭を下げる：音をほとんど消す
A.put(fx, A.sfx_transition(0.5), bw.start - 0.45)
A.put(music, A.amb_room(bw.dur, 0.06), bw.start)
A.put(fx, A.sfx_heart(0.45), bw.start + 0.6)
A.put(music, A.fade(A.bgm_sparse(bw.dur), 0.8, 0.6) * 0.7, bw.start)
# 早回し：秒針が速くなる → 時間切れ
A.put(fx, A.sfx_whoosh(0.6, True, 0.3), ff.start)
A.put(fx, A.sfx_stopwatch(ff.lines[0][0], 0.18, 0.2), ff.start + 0.1)
A.put(music, A.fade(dark(ff.dur), 0.2, 0.3), ff.start)
A.put(fx, A.sfx_boom(0.8, 2.2), ff.start + 0.3)                       # 何もしない一日
for k in range(5):
    A.put(fx, A.sfx_notify(0.18), ff.start + 0.9 + k * 0.6)
A.put(fx, A.sfx_boom(0.9, 2.4), ff.start + ff.lines[0][0] + V.L("09"))
# 面接：凍る → 残りループ 3→2（一番大きいドン）
A.put(fx, A.sfx_rewind(), iv.start - 0.5)
A.put(fx, A.sfx_heart(0.45), iv.start + iv.lines[1][0] - 0.3)
A.put(fx, A.sfx_heart(0.5), iv.start + iv.lines[2][0] - 0.3)
A.put(fx, A.sfx_stopwatch(iv.lines[4][0] - iv.lines[1][0], 0.5, 0.2), iv.start + iv.lines[1][0])
A.put(fx, A.sfx_heart(0.6), iv.start + iv.lines[4][0] - 0.6); A.put(fx, A.sfx_heart(0.65), iv.start + iv.lines[4][0] - 0.1)
A.put(fx, A.sfx_boom(0.7, 2.0), iv.start + iv.lines[4][0] + V.L("18"))   # 答えられない。
A.put(fx, A.sfx_freeze(), iv.start + iv.rev - 0.9)
A.put(fx, A.sfx_riser(0.8, 0.4), iv.start + iv.rev - 0.8)
A.put(fx, A.sfx_boom(1.0, 2.8), iv.start + iv.rev)
A.put(fx, A.sfx_glass(), iv.start + iv.rev)
A.put(music, A.fade(A.bgm_heavy(max(iv.dur, 3.0))[:int(iv.dur * A.SR)], 0.3, 0.4), iv.start)
# 12月5日の朝
A.put(fx, A.sfx_reverse_swell(1.0), wk.start - 0.9)
A.put(music, A.amb_room(wk.dur, 0.05), wk.start)
A.put(fx, A.sfx_tick(0.25), wk.start + 0.2)
A.put(music, A.fade(A.bgm_sparse(wk.lines[2][0]), 0.5, 0.6), wk.start)
A.put(fx, A.sfx_riser(0.6, 0.3), wk.start + wk.lines[2][0] - 0.6)
A.put(music, A.fade(A.bgm_morning(wk.dur - wk.lines[2][0] + 0.2), 0.3, 0.5), wk.start + wk.lines[2][0])
A.put(fx, A.sfx_ding(0.35), wk.start + wk.lines[3][0])
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
final = f"{OUT}/ガクチカループ_第4話.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
