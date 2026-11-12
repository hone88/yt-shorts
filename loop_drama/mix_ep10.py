"""ガクチカ・ループ 第10話の音。python3 mix_ep10.py → out_ep10/ガクチカループ_第10話.mp4
転換音・環境音は6割（第8話以降の決まり）。"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep10 as V

OUT = V.OUT


def TR(*a):
    return A.sfx_transition(*a) * 0.6


def AMB_R(*a):
    return A.amb_room(*a) * 0.6


def AMB_C(*a):
    return A.amb_crowd(*a) * 0.6


def dark(sec):
    return A.bgm_dark(max(sec, 3.6))[:int(sec * A.SR)]


SH = V.SH
total = sum(s.dur for s in SH)
S = {s.name: s for s in SH}
voice = np.zeros(int(total * A.SR) + A.SR)
fx = np.zeros_like(voice)
music = np.zeros_like(voice)
for s in SH:
    for (t0, sid) in s.lines:
        A.put(voice, V.vo(sid), s.start + t0)
co, wa, ta, fi, se, ho, en = (S[k] for k in ("cold", "watch", "talk", "first", "second", "home", "end"))

# 0秒：ドン →「……なんで知ってんの？」→ 2.4秒でタイトル
A.put(fx, A.sfx_boom(0.9, 2.4), 0.02)
A.put(fx, A.sfx_heart(0.5), 1.0)
A.put(music, A.fade(dark(co.dur + 0.3), 0.05, 0.4), 0)
A.put(music, AMB_C(co.dur + wa.dur, 0.07), 0)
A.put(fx, TR(0.6), 2.4 - 0.45)

# 離れて見る：秒針 → 心臓
A.put(fx, TR(0.55), wa.start - 0.45)
A.put(fx, A.sfx_stopwatch(wa.dur - 0.5, 0.5, 0.18), wa.start + 0.2)
A.put(fx, A.sfx_heart(0.5), wa.start + 2.6); A.put(fx, A.sfx_heart(0.55), wa.start + 3.3)
A.put(music, A.fade(A.bgm_sparse(wa.dur + 0.3), 0.3, 0.3), wa.start)
A.put(fx, A.sfx_pop(0.3), wa.start + wa.lines[1][0] - 0.5)      # トケイ

# 声をかける：「なんで知ってんの？」で声を止めてドン →「なにそれ」でポン、明るいBGM
A.put(fx, TR(0.5), ta.start - 0.45)
t8 = ta.start + ta.lines[5][0]
hit = ta.start + ta.hit
A.put(music, A.fade(A.bgm_sparse(hit - ta.start + 0.2), 0.2, 0.2), ta.start)
A.put(music, AMB_C(ta.dur, 0.06), ta.start)
A.put(fx, A.sfx_boom(0.95, 2.6), hit + 0.05)
A.put(music, A.fade(dark(t8 - hit), 0.3, 0.3), hit + 0.3)
A.put(fx, A.sfx_pop(0.4), t8 + 0.1)
A.put(music, A.fade(A.bgm_morning(ta.start + ta.dur - t8 + 0.3), 0.3, 0.4), t8)

# 1次選考会：静か → ✓ でポン
A.put(fx, TR(0.5), fi.start - 0.45)
A.put(music, A.fade(A.bgm_sparse(fi.dur + 0.3), 0.3, 0.3), fi.start)
A.put(music, AMB_R(fi.dur + se.dur, 0.05), fi.start)
A.put(fx, A.sfx_pop(0.35), fi.start + fi.ok + 0.05)
A.put(fx, A.sfx_pop(0.3), fi.start + fi.ok + 0.4)

# 2次選考会 → 活動先決定：ストップウォッチ → ポン
A.put(fx, TR(0.5), se.start - 0.45)
A.put(fx, A.sfx_stopwatch(se.rev, 0.5, 0.2), se.start)
A.put(music, A.fade(A.bgm_morning(se.dur + 0.3), 0.2, 0.3), se.start)
A.put(fx, A.sfx_boom(0.7, 2.0), se.start + se.rev)
A.put(fx, A.sfx_pop(0.4), se.start + se.rev)

# 帰り道：明るいBGM、余韻
A.put(fx, TR(0.5), ho.start - 0.45)
A.put(music, A.fade(A.bgm_morning(ho.dur + en.dur + 0.3, bright=True), 0.4, 1.5), ho.start)
A.put(music, AMB_C(ho.dur, 0.05), ho.start)
A.put(fx, A.sfx_tick(0.25), en.start + 0.3)

music = A.duck(music, voice, 0.6)
mix = voice * 1.0 + fx * 0.8 + music * 0.9
mix = mix[:int(total * A.SR)]
mix /= np.abs(mix).max() / 0.95
p = f"{OUT}/mix.wav"
with wave.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = f"{OUT}/ガクチカループ_第10話.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
