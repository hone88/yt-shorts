"""ガクチカ・ループ 第15話の音。python3 mix_ep15.py → out_ep15/ガクチカループ_第15話.mp4
転換音・環境音は6割、効果音は7割。"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep15 as V

OUT = V.OUT
FX_LEVEL = 0.7


def TR(*a):
    return A.sfx_transition(*a) * 0.6


def AMB_C(*a):
    return A.amb_crowd(*a) * 0.6


def AMB_R(*a):
    return A.amb_room(*a) * 0.6


def L_END(s, j):
    return V.L(s.lines[j][1])


def dark(sec):
    return A.bgm_dark(max(sec, 3.6))[:int(sec * A.SR)]


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
        A.put(voice, V.vo(sid), s.start + t0)
co, de, ga, gr, ta, q, re, be, en = (S[k] for k in ("cold", "debate", "gate", "green", "talk", "q", "result", "bench", "end"))

# 0秒：張り出し（名前が、ない）ドン → 2.4秒でタイトル
A.put(fx, A.sfx_boom(1.0, 2.6), 0.02)
A.put(music, A.fade(dark(co.dur + 0.3), 0.05, 0.4), 0)
A.put(music, AMB_C(co.dur, 0.06), 0)
A.put(fx, TR(0.6), 2.4 - 0.45)

# 3/3 公開討論会：手を挙げる → 明るいBGMを少し
A.put(fx, TR(0.55), de.start - 0.45)
A.put(music, AMB_C(de.dur, 0.08), de.start)
A.put(fx, A.sfx_pop(0.4), de.start + de.lines[0][0] - 0.3)
A.put(music, A.fade(A.bgm_morning(de.dur + 0.3), 0.3, 0.5), de.start)

# 3/10 入口：ドン、秒針・心臓（カナタとトケイ）
A.put(fx, TR(0.55), ga.start - 0.45)
A.put(fx, A.sfx_boom(0.9, 2.4), ga.start + 0.05)
A.put(fx, A.sfx_stopwatch(ga.dur - 0.4, 0.5, 0.16), ga.start + 0.2)
A.put(music, A.fade(A.bgm_sparse(ga.dur + 0.3), 0.4, 0.4), ga.start)
A.put(music, AMB_C(ga.dur, 0.05), ga.start)
A.put(fx, A.sfx_pop(0.3), ga.start + ga.lines[1][0] - 0.5)
for k in range(3):
    A.put(fx, A.sfx_heart(0.45), ga.start + ga.lines[2][0] + L_END(ga, 2) + 0.2 + k * 0.8)

# 控え室：緊張の下に静かに明るい音 →「頼んだ」
A.put(fx, TR(0.5), gr.start - 0.45)
A.put(music, A.fade(A.bgm_tension(gr.dur + 0.3) * 0.55, 0.4, 0.4), gr.start)
A.put(music, A.fade(A.bgm_morning(gr.dur + 0.3) * 0.5, 0.6, 0.5), gr.start)
A.put(music, AMB_R(gr.dur, 0.05), gr.start)
t02 = gr.start + [x for x, i in gr.lines if i == "02"][0]
A.put(fx, A.sfx_pop(0.35), t02 - 0.2)

# 発表：緊張のBGM、心臓 → スライド
A.put(fx, TR(0.5), ta.start - 0.45)
A.put(music, A.fade(A.bgm_tension(ta.dur + q.dur + 0.3), 0.2, 0.6), ta.start)
A.put(music, AMB_C(ta.dur, 0.04), ta.start)
A.put(fx, A.sfx_heart(0.5), ta.start + 0.3)
A.put(fx, A.sfx_whoosh(0.4, True, 0.25), ta.start + ta.slides)
A.put(fx, A.sfx_whoosh(0.4, True, 0.25), ta.start + ta.slides + 1.2)

# 質問：声を止めて → ドン → 心臓だけ
A.put(fx, TR(0.5), q.start - 0.45)
A.put(fx, A.sfx_boom(1.0, 2.8), q.start + q.hit)
for k in range(5):
    A.put(fx, A.sfx_heart(0.55 + 0.04 * k), q.start + q.hit + 0.8 + k * 0.8)

# 結果：静かなピアノ
A.put(fx, TR(0.5), re.start - 0.45)
A.put(fx, A.sfx_boom(0.7, 2.2), re.start + 0.35)
A.put(music, A.fade(A.bgm_sparse(re.dur + be.dur + 0.3) * 1.3, 0.4, 0.6), re.start)
A.put(music, AMB_C(re.dur, 0.04), re.start)

# 夕方のベンチ：静かな締め
A.put(fx, TR(0.5), be.start - 0.45)
A.put(music, A.fade(A.bgm_sparse(be.dur + en.dur + 0.3), 0.6, 1.5), be.start)
A.put(fx, A.sfx_tick(0.25), en.start + 0.3)

music = A.duck(music, voice, 0.6)
mix = voice * 1.0 + fx * 0.8 * FX_LEVEL + music * 0.9
mix = mix[:int(total * A.SR)]
mix /= np.abs(mix).max() / 0.95
p = f"{OUT}/mix.wav"
with wave.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = f"{OUT}/ガクチカループ_第15話.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
