"""ガクチカ・ループ 第7話の音。python3 mix_ep7.py → out_ep7/ガクチカループ_第7話.mp4"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep7 as V

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
co, of, vi, wa, ff, bk, ni, en = (S[k] for k in ("cold", "office", "visit", "walk", "ff", "back", "night", "end"))


def dark(sec):
    return A.bgm_dark(max(sec, 3.0))[:int(sec * A.SR)]


# 0秒：名刺が逆さま。ドン → 2.4秒でタイトル
A.put(fx, A.sfx_boom(0.85, 2.4), 0.02)
A.put(fx, A.sfx_pop(0.35), 0.05)
A.put(music, A.amb_room(co.dur, 0.06), 0)
A.put(music, A.fade(dark(co.dur + 0.3), 0.05, 0.4), 0)
A.put(fx, A.sfx_heart(0.55), 0.8); A.put(fx, A.sfx_heart(0.6), 1.5)
A.put(fx, A.sfx_transition(0.6), 2.4 - 0.45)
# 9:50 事務所：朝の明るいBGM
A.put(fx, A.sfx_rewind(), of.start - 0.4)
A.put(music, A.amb_room(of.dur, 0.05), of.start)
A.put(music, A.fade(A.bgm_morning(of.dur + 0.2), 0.3, 0.4), of.start)
A.put(fx, A.sfx_pop(0.35), of.start + of.card)
# 1か所目：逆さま（ドン）→ また、やった → 出し直し → よろしくね（キラッ）
A.put(fx, A.sfx_transition(0.55), vi.start - 0.45)
a, b, c, d, e = (x[0] for x in vi.lines)
A.put(music, A.amb_room(vi.dur, 0.06), vi.start)
A.put(fx, A.sfx_boom(0.8, 2.2), vi.start + 0.1)
A.put(fx, A.sfx_heart(0.55), vi.start + b - 0.3); A.put(fx, A.sfx_heart(0.6), vi.start + b + 0.4)
A.put(music, A.fade(dark(c + 0.2), 0.2, 0.4), vi.start)
A.put(music, A.fade(A.bgm_sparse(d - c + 0.2), 0.4, 0.4), vi.start + c)
A.put(fx, A.sfx_riser(0.6, 0.3), vi.start + d - 0.6)
A.put(music, A.fade(A.bgm_morning(vi.dur - d + 0.2, bright=True), 0.2, 0.5), vi.start + d)
A.put(fx, A.sfx_ding(0.4), vi.start + e)
# 移動中：トケイ
A.put(fx, A.sfx_transition(0.5), wa.start - 0.45)
A.put(music, A.amb_crowd(wa.dur, 0.08), wa.start)
A.put(fx, A.sfx_whoosh(0.5, False, 0.3), wa.start + 0.05)
A.put(music, A.fade(A.bgm_morning(wa.dur + 0.2), 0.3, 0.4), wa.start)
# 早回し：3〜5か所目。チェックが増えるたびにポン
A.put(fx, A.sfx_whoosh(0.6, True, 0.3), ff.start)
A.put(fx, A.sfx_stopwatch(ff.dur - 0.3, 0.25, 0.2), ff.start + 0.1)
A.put(music, A.fade(A.bgm_morning(ff.dur + 0.2, bright=True), 0.2, 0.4), ff.start)
for k in range(3):
    A.put(fx, A.sfx_pop(0.35), ff.start + k * 2.1 + 0.15)
A.put(fx, A.sfx_ding(0.35), ff.start + 4.2)
# 17:00 事務所：ほっとする
A.put(fx, A.sfx_transition(0.55), bk.start - 0.45)
A.put(music, A.amb_room(bk.dur, 0.05), bk.start)
A.put(music, A.fade(A.bgm_sparse(bk.dur + 0.2), 0.4, 0.5), bk.start)
A.put(fx, A.sfx_ding(0.3), bk.start + bk.lines[2][0] + V.L("13") * 0.7)
# 夜：得意げ → 「それで、何を話すのだ？」→ 秒針だけ
A.put(fx, A.sfx_transition(0.55), ni.start - 0.45)
A.put(music, A.amb_room(ni.dur, 0.04), ni.start)
A.put(music, A.fade(A.bgm_sparse(ni.lines[1][0] + 0.2), 0.3, 0.4), ni.start)
A.put(fx, A.sfx_boom(0.7, 2.0), ni.start + ni.lines[1][0] + V.L("15") * 0.6)
A.put(music, A.fade(dark(ni.dur - ni.lines[1][0]), 0.3, 0.4), ni.start + ni.lines[1][0])
A.put(fx, A.sfx_stopwatch(ni.dur - ni.lines[1][0] - 0.2, 0.5, 0.25), ni.start + ni.lines[1][0] + 0.2)
# 終わり
A.put(fx, A.sfx_transition(0.6), en.start - 0.45)
A.put(fx, A.sfx_boom(0.8, 2.2), en.start + 0.05)
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
final = f"{OUT}/ガクチカループ_第7話.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
