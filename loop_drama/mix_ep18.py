"""ガクチカ・ループ 第18話の音。python3 mix_ep18.py → out_ep18/ガクチカループ_第18話.mp4
秒針は面接のあいだ止めない（第1話との対比）。転換音・環境音は6割、効果音は7割。"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep18 as V

OUT = V.OUT
FX_LEVEL = 0.7


def TR(*a):
    return A.sfx_transition(*a) * 0.6


def AMB_R(*a):
    return A.amb_room(*a) * 0.6


def AMB_C(*a):
    return A.amb_crowd(*a) * 0.6


def sparse(sec):
    return A.bgm_sparse(max(sec, 3.6))[:int(sec * A.SR)]


SH = V.SH
total = sum(s.dur for s in SH)
S = {s.name: s for s in SH}
voice = np.zeros(int(total * A.SR) + A.SR)
fx = np.zeros_like(voice)
music = np.zeros_like(voice)
for s in SH:
    for (t0, sid) in s.lines:
        A.put(voice, V.vo(sid) * (0.85 if sid == "f1" else 1.0), s.start + t0)
rw, l1, l2, co, q, an, de, th, ou, lo, en, inv = (S[k] for k in ("rewind", "loop1", "loop2", "cold", "q", "answer", "deep", "thanks", "outside", "look", "end", "invite"))
at = V.at


def vo_from(path, t0, t1=None):
    with wave.open(path) as w:
        y = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return y[int(max(0, t0) * A.SR):None if t1 is None else int(t1 * A.SR)]


# 巻き戻し：「3回、やり直した。」ドン ＋ テープの逆回転（だんだん速く）
A.put(fx, A.sfx_boom(1.0, 2.6), 0.02)
rew = A.sfx_rewind()
k = 0
while k * len(rew) / A.SR < rw.dur - 0.2:
    A.put(fx, rew * 0.8, 0.1 + k * len(rew) / A.SR)
    k += 1
A.put(music, A.fade(A.bgm_mystery(rw.dur + 0.3) * 0.5, 0.1, 0.4), 0)

# 1回目（第1話）：質問の終わり →「…え、っと……」→ 止まる
import ep1c as P1
s1 = next(x for x in P1.SH if x.name == "interview")
a1, b1 = s1.lines[0][0], s1.lines[1][0]
A.put(fx, TR(0.4), l1.start - 0.3)
A.put(voice, vo_from(f"{V.HERE}/voice/ep1/01.wav", V.L1[0] - a1) * 0.9, l1.start)
A.put(voice, vo_from(f"{V.HERE}/voice/ep1/02.wav", 0) * 0.9, l1.start + b1 - V.L1[0])
A.put(fx, A.sfx_stopwatch(s1.tf - V.L1[0], 0.5, 0.15), l1.start)
A.put(fx, A.sfx_freeze() * 0.8, l1.start + s1.tf - V.L1[0])

# 2回目（第8話）：「それで、何を考えましたか？」→ 沈黙 → 止まる
import ep8 as V8
s8 = next(x for x in V8.SH if x.name == "iv")
q8 = s8.lines[3][0]
A.put(fx, TR(0.4), l2.start - 0.3)
A.put(voice, vo_from(f"{V.HERE}/voice/ep8/01.wav", V.L2A[0] - q8) * 0.9, l2.start + max(0, q8 - V.L2A[0]))
a = V.L2A[1] - V.L2A[0]
A.put(fx, A.sfx_heart(0.5), l2.start + a + 0.2)
A.put(fx, A.sfx_heart(0.55), l2.start + a + 1.0)
A.put(fx, A.sfx_freeze() * 0.8, l2.start + a + (s8.tf - V.L2B[0]))

A.put(music, AMB_R(l1.dur + l2.dur, 0.05), l1.start)                       # 面接室の空気（無音にしない）
# 3回目：「最後の、面接。」→ タイトル
A.put(fx, A.sfx_boom(0.9, 2.4), co.start + 0.02)
A.put(music, AMB_R(co.dur, 0.05), co.start)
A.put(music, A.fade(A.bgm_tension(co.dur + 0.3) * 0.5, 0.2, 0.4), co.start)
A.put(fx, TR(0.6), co.start + 1.6 - 0.45)

# 面接：秒針は最後まで（質問 → 礼まで）、止まらない
iv_end = th.start + th.dur
A.put(fx, TR(0.5), q.start - 0.45)
A.put(fx, A.sfx_boom(0.8, 2.2), q.start + 0.02)
A.put(fx, A.sfx_stopwatch(iv_end - q.start, 0.5, 0.15), q.start + 0.2)
A.put(music, AMB_R(iv_end - q.start, 0.04), q.start)
for k in range(2):
    A.put(fx, A.sfx_heart(0.45), q.start + q.wait + 0.2 + k * 0.8)
A.put(music, A.fade(sparse(an.dur + de.dur + 0.4) * 1.1, 1.0, 0.8), an.start - 0.4)    # 答え：静かなピアノ
A.put(fx, A.sfx_reverse_swell(0.8) * 0.6, de.start + de.fb - 0.6)                         # 第8話の画
A.put(music, A.fade(A.bgm_morning(th.dur + 0.3) * 0.7, 0.4, 0.6), th.start)               # 明るく
A.put(fx, A.sfx_chime_end(), th.start + at(th, "12") + V.L("12") + 0.3)

# 建物の外：トケイとの別れ → きらめき
A.put(fx, TR(0.5), ou.start - 0.45)
A.put(music, AMB_C(ou.dur + lo.dur, 0.03), ou.start)
A.put(music, A.fade(sparse(ou.dur + 0.3) * 1.1, 0.8, 0.8), ou.start)
A.put(fx, A.sfx_pop(0.3), ou.start + at(ou, "13") - 0.9)
A.put(fx, A.sfx_reverse_swell(0.8) * 0.6, ou.start + at(ou, "f1") - 0.7)
A.put(fx, A.sfx_ding(0.3), ou.start + ou.vanish - 0.1)
A.put(fx, A.sfx_ding(0.4), ou.start + ou.vanish + 0.15)
A.put(fx, A.sfx_ding(0.3), ou.start + ou.vanish + 0.45)

# 画面を見る：声の前の間 → ドン
A.put(fx, TR(0.45), lo.start - 0.45)
A.put(fx, A.sfx_boom(1.0, 2.8), lo.start + lo.hit)

# 終わり：明るい締め、音楽だけで4秒
A.put(music, A.fade(A.bgm_morning(en.dur + 0.3), 0.3, 1.6), en.start)
A.put(fx, A.sfx_chime_end(), en.start + 0.2)

# 最後の案内：明るいまま
A.put(music, A.fade(A.bgm_morning(inv.dur + 0.3), 0.6, 1.6), inv.start)
A.put(fx, A.sfx_pop(0.3), inv.start + 0.7)

music = A.duck(music, voice, 0.6)
mix = voice * 1.0 + fx * 0.8 * FX_LEVEL + music * 0.9
mix = mix[:int(total * A.SR)]
mix /= np.abs(mix).max() / 0.95
p = f"{OUT}/mix.wav"
with wave.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = f"{OUT}/ガクチカループ_第18話.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
