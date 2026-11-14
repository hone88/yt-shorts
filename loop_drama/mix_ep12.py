"""ガクチカ・ループ 第12話の音。python3 mix_ep12.py → out_ep12/ガクチカループ_第12話.mp4
転換音・環境音は6割（第8話以降の決まり）。"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep12 as V

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
co, rm, vi, qa, ho, en = (S[k] for k in ("cold", "room", "visit", "qa", "home", "end"))

# 0秒：ドン → 2.4秒でタイトル
A.put(fx, A.sfx_boom(0.9, 2.4), 0.02)
A.put(music, A.fade(A.bgm_sparse(co.dur + 0.3), 0.05, 0.4), 0)
A.put(music, AMB_R(co.dur, 0.06), 0)
A.put(fx, TR(0.6), 2.4 - 0.45)

# 2/19 夜：通知 → 前のループ（ガラス）→ トケイ →「行きます」→ 押す瞬間にドン
A.put(fx, TR(0.55), rm.start - 0.45)
A.put(fx, A.sfx_notify(0.4), rm.start + 0.4); A.put(fx, A.sfx_notify(0.35), rm.start + 1.1)
A.put(fx, A.sfx_glass(), rm.start + 2.1)
A.put(fx, A.sfx_reverse_swell(0.8), rm.start + 2.2)
A.put(music, A.fade(A.bgm_mystery(rm.dur + 0.3) * 0.8, 0.4, 0.4), rm.start)
A.put(music, AMB_R(rm.dur, 0.06), rm.start)
A.put(fx, A.sfx_pop(0.3), rm.start + 3.4)
A.put(fx, A.sfx_boom(0.95, 2.6), rm.start + rm.tap1)
A.put(fx, A.sfx_pop(0.45), rm.start + rm.tap1)
A.put(fx, A.sfx_pop(0.45), rm.start + rm.tap2)

# 企業訪問：秒針と心臓 → 早すぎる手 → くすっと
A.put(fx, TR(0.5), vi.start - 0.45)
A.put(music, AMB_C(vi.dur + qa.dur, 0.05), vi.start)
t5, t6, t7 = (vi.start + a for a, _ in vi.lines)
A.put(music, A.fade(A.bgm_sparse(vi.dur + 0.3), 0.3, 0.3), vi.start)
A.put(fx, A.sfx_stopwatch(t6 - t5 + 1.5, 0.5, 0.18), t5 + 1.0)
A.put(fx, A.sfx_heart(0.5), t6 - 0.4); A.put(fx, A.sfx_heart(0.55), t6 + 0.3)
A.put(fx, A.sfx_whoosh(0.4, True, 0.25), vi.start + vi.raise_t)
A.put(fx, A.sfx_pop(0.4), t7 + V.L("07") + 0.1)

# 質問の時間：手を挙げる → 低いドン → 明るいBGM、余韻
A.put(fx, TR(0.5), qa.start - 0.45)
t8, t1, t9, t10 = (qa.start + a for a, _ in qa.lines)
A.put(music, A.fade(A.bgm_sparse(t9 - qa.start + 0.3), 0.3, 0.3), qa.start)
A.put(fx, A.sfx_boom(0.9, 2.6), t1 + V.L("01") + 0.05)
A.put(music, A.fade(A.bgm_morning(qa.start + qa.dur - t9 + 0.3), 0.4, 0.4), t9)
A.put(fx, A.sfx_ding(0.3), t10 + V.L("10") + 0.2)

# 帰り道：明るい締め
A.put(fx, TR(0.5), ho.start - 0.45)
A.put(music, A.fade(A.bgm_morning(ho.dur + en.dur + 0.3, bright=True), 0.4, 1.5), ho.start)
A.put(music, AMB_C(ho.dur, 0.05), ho.start)
A.put(fx, A.sfx_pop(0.35), ho.start + ho.plan)
A.put(fx, A.sfx_tick(0.25), en.start + 0.3)

music = A.duck(music, voice, 0.6)
mix = voice * 1.0 + fx * 0.8 + music * 0.9
mix = mix[:int(total * A.SR)]
mix /= np.abs(mix).max() / 0.95
p = f"{OUT}/mix.wav"
with wave.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = f"{OUT}/ガクチカループ_第12話.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
