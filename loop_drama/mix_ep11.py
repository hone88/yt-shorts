"""ガクチカ・ループ 第11話の音。python3 mix_ep11.py → out_ep11/ガクチカループ_第11話.mp4
転換音・環境音は6割（第8話以降の決まり）。"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep11 as V

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
co, cn, ha, of, ho, en = (S[k] for k in ("cold", "council", "hall", "office", "home", "end"))

# 0秒：ドン → 2.4秒でタイトル
A.put(fx, A.sfx_boom(0.9, 2.4), 0.02)
A.put(music, A.fade(dark(co.dur + 0.3), 0.05, 0.4), 0)
A.put(music, AMB_C(co.dur + cn.dur, 0.08), 0)
A.put(fx, TR(0.6), 2.4 - 0.45)

# 傍聴席：ざわめき、用語ごとにポン、メモ
A.put(fx, TR(0.55), cn.start - 0.45)
for j in range(3):
    A.put(fx, A.sfx_pop(0.35), cn.start + 0.2 + j * 0.35)
A.put(fx, A.sfx_whoosh(0.35, True, 0.2), cn.start + 1.7)
A.put(music, A.fade(A.bgm_sparse(cn.dur + 0.3), 0.3, 0.3), cn.start)
A.put(fx, A.sfx_boom(0.55, 2.0), cn.start + cn.lines[0][0] + V.L("02") + 0.1)

# 廊下：質問 → 明るいBGM →「？」だらけのメモ
A.put(fx, TR(0.5), ha.start - 0.45)
A.put(music, AMB_R(ha.dur + of.dur, 0.05), ha.start)
t4 = ha.start + V.line_t(ha, "04")
A.put(music, A.fade(A.bgm_sparse(t4 - ha.start + 0.2), 0.3, 0.2), ha.start)
A.put(fx, A.sfx_pop(0.4), t4)
A.put(music, A.fade(A.bgm_morning(ha.start + ha.dur - t4 + 0.3), 0.3, 0.4), t4)
A.put(fx, A.sfx_whoosh(0.4, True, 0.25), ha.start + ha.memo)
for j in range(4):
    A.put(fx, A.sfx_pop(0.3), ha.start + ha.memo + 0.4 + j * 0.15)

# 事務所：カード → 間 →「聞きたかったんだ」で低いドン → 余韻
A.put(fx, TR(0.5), of.start - 0.45)
A.put(fx, A.sfx_pop(0.35), of.start + 0.3)
t9, t10 = (of.start + V.line_t(of, k) for k in ("09", "10"))
A.put(music, A.fade(A.bgm_sparse(t10 - of.start + 0.3), 0.3, 0.3), of.start)
A.put(fx, A.sfx_heart(0.45), t9 - 0.8)
A.put(fx, A.sfx_boom(0.95, 2.8), t10 + V.L("10") * 0.6)
A.put(music, A.fade(A.bgm_sparse(of.start + of.dur - t10 + 0.3) * 1.3, 0.3, 0.4), t10)

# 帰り道：明るいBGM
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
final = f"{OUT}/ガクチカループ_第11話.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
