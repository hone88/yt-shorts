"""ガクチカ・ループ 第9話の音。python3 mix_ep9.py → out_ep9/ガクチカループ_第9話.mp4
転換音・環境音は6割（第8話以降の決まり）。"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep9 as V

OUT = V.OUT


def TR(*a):     # 画面切り替えの「ふっ」は6割
    return A.sfx_transition(*a) * 0.6


def AMB_R(*a):  # 環境音も6割
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
co, mo, ca, be, ru, ni, rs, en = (S[k] for k in ("cold", "morning", "call", "bench", "rule", "night", "resolve", "end"))

# 0秒：ドン →「…えっと、誰？」→ 2.4秒でタイトル
A.put(fx, A.sfx_boom(0.9, 2.4), 0.02)
A.put(fx, A.sfx_heart(0.55), 0.9); A.put(fx, A.sfx_heart(0.6), 1.6)
A.put(music, A.fade(dark(co.dur + 0.3), 0.05, 0.4), 0)
A.put(fx, TR(0.6), 2.4 - 0.45)
A.put(music, AMB_C(co.dur, 0.08), 0)

# 12/5 朝：目覚まし・通知（第1話と同じメッセージ）
A.put(fx, TR(0.55), mo.start - 0.45)
A.put(fx, A.sfx_alarm(), mo.start + 0.05)
A.put(fx, A.sfx_notify(0.4), mo.start + 0.5)
A.put(music, A.fade(A.bgm_mystery(mo.dur + 0.3) * 0.8, 0.4, 0.4), mo.start)
A.put(music, AMB_R(mo.dur + ca.dur, 0.06), mo.start)
A.put(fx, A.sfx_pop(0.3), mo.start + mo.lines[1][0] - 0.5)      # トケイが出る

# 説明会：「はじめまして」で小さいドン
A.put(fx, TR(0.5), ca.start - 0.45)
A.put(fx, A.sfx_ding(0.3), ca.start + 0.15)
A.put(music, A.fade(A.bgm_sparse(ca.dur + 0.3), 0.3, 0.4), ca.start)
A.put(fx, A.sfx_boom(0.45, 1.8), ca.start + ca.lines[0][0] + 0.2)

# 12/7 大学：明るい → 「…えっと、誰？」でドン → 0.5秒の無音 → 暗い持続音
A.put(fx, TR(0.55), be.start - 0.45)
hit = be.start + be.lines[1][0] + V.L("01")
A.put(music, A.fade(A.bgm_morning(hit - be.start + 0.1), 0.3, 0.12), be.start)
A.put(music, A.fade(AMB_C(hit - be.start, 0.1), 0.2, 0.1), be.start)
A.put(fx, A.sfx_boom(1.0, 2.8), hit + 0.05)
A.put(fx, A.sfx_freeze(), hit + 0.05)
after = be.start + be.dur - (hit + 0.6)
A.put(music, A.fade(dark(after + ru.dur + 0.3), 0.4, 0.5), hit + 0.6)
A.put(music, AMB_C(after + 0.3, 0.06), hit + 0.6)

# ルール⑤
A.put(fx, A.sfx_whoosh(0.45, True, 0.3), ru.start + 0.2)
A.put(fx, A.sfx_boom(0.7, 2.2), ru.start + 0.35)
A.put(fx, A.sfx_pop(0.3), ru.start + 0.2)

# 夜の部屋：静かなピアノ
A.put(fx, TR(0.5), ni.start - 0.45)
A.put(music, A.fade(A.bgm_sparse(ni.dur + rs.lines[1][0] + 0.3) * 1.3, 0.6, 0.5), ni.start)
A.put(music, AMB_R(ni.dur + rs.dur, 0.06), ni.start)
A.put(fx, A.sfx_tick(0.2), ni.start + 0.3)

# 決める：上げ → ドン → 明るいBGM
r_at = rs.start + rs.lines[1][0]
A.put(fx, A.sfx_riser(0.9, 0.45), r_at - 0.9)
A.put(fx, A.sfx_boom(1.0, 2.8), rs.start + rs.up)
A.put(music, A.fade(A.bgm_morning(rs.start + rs.dur - (rs.start + rs.up) + en.dur + 0.3, bright=True), 0.1, 1.5), rs.start + rs.up)
A.put(fx, A.sfx_tick(0.25), en.start + 0.3)

music = A.duck(music, voice, 0.6)
mix = voice * 1.0 + fx * 0.8 + music * 0.9
mix = mix[:int(total * A.SR)]
mix /= np.abs(mix).max() / 0.95
p = f"{OUT}/mix.wav"
with wave.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = f"{OUT}/ガクチカループ_第9話.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
