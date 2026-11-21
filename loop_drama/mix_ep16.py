"""ガクチカ・ループ 第16話の音。python3 mix_ep16.py → out_ep16/ガクチカループ_第16話.mp4
転換音・環境音は6割、効果音は7割。公園は屋外の環境音（街のざわめき・子どもの声の代わりに amb_crowd を小さく）。"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep16 as V

OUT = V.OUT
FX_LEVEL = 0.7


def TR(*a):
    return A.sfx_transition(*a) * 0.6


def AMB_C(*a):
    return A.amb_crowd(*a) * 0.6


def AMB_R(*a):
    return A.amb_room(*a) * 0.6


def pen(sec):
    y = A.lowpass(A.noise(sec, 7), 0.35) * 0.25
    return y * (0.6 + 0.4 * np.sin(np.linspace(0, sec * 40, len(y))) ** 2)


SH = V.SH
total = sum(s.dur for s in SH)
S = {s.name: s for s in SH}
voice = np.zeros(int(total * A.SR) + A.SR)
fx = np.zeros_like(voice)
music = np.zeros_like(voice)
for s in SH:
    for (t0, sid) in s.lines:
        A.put(voice, V.vo(sid), s.start + t0)
co, of, pa, el, wa, al, en = (S[k] for k in ("cold", "office", "park", "elder", "walk", "alone", "end"))

# 0秒：ドン＋メモ（ポン×3）→ 2.4秒でタイトル
A.put(fx, A.sfx_boom(0.9, 2.4), 0.02)
for k in range(3):
    A.put(fx, A.sfx_pop(0.35), 0.05 + k * 0.6)
A.put(fx, pen(1.6), 0.1)
A.put(music, A.fade(A.bgm_sparse(co.dur + 0.3), 0.05, 0.4), 0)
A.put(music, AMB_C(co.dur, 0.05), 0)
A.put(fx, TR(0.6), 2.4 - 0.45)

# 事務所：静か →「よし」でドン → 明るいBGM
A.put(fx, TR(0.55), of.start - 0.45)
A.put(music, AMB_R(of.dur, 0.05), of.start)
yo = of.start + of.yosh
A.put(music, A.fade(A.bgm_sparse(yo - of.start + 0.3), 0.4, 0.3), of.start)
A.put(fx, A.sfx_boom(0.9, 2.4), yo + 0.05)
A.put(music, A.fade(A.bgm_morning(of.start + of.dur - yo + 0.3), 0.3, 0.4), yo)

# 公園：屋外の環境音、メモでペンとポン
A.put(fx, TR(0.5), pa.start - 0.45)
A.put(music, AMB_C(pa.dur + el.dur, 0.05), pa.start)
A.put(music, A.fade(A.bgm_morning(pa.dur + el.dur + 0.3) * 0.8, 0.4, 0.5), pa.start)
for m in (pa.m1, pa.m2):
    A.put(fx, pen(0.6), pa.start + m - 0.1)
    A.put(fx, A.sfx_pop(0.4), pa.start + m + 0.3)
A.put(fx, TR(0.5), el.start - 0.45)
A.put(fx, pen(0.6), el.start + el.m3 - 0.1)
A.put(fx, A.sfx_pop(0.4), el.start + el.m3 + 0.3)
A.put(fx, A.sfx_heart(0.4), el.start + el.lines[1][0] - 0.6)

# 夕方の帰り道
A.put(fx, TR(0.5), wa.start - 0.45)
A.put(music, A.fade(A.bgm_sparse(wa.dur + 0.3), 0.4, 0.4), wa.start)
A.put(music, AMB_C(wa.dur, 0.05), wa.start)

# ひとりで：静か →「ここに、あった」→ トケイ → ハルトの通知 → 明るい締め
A.put(fx, TR(0.5), al.start - 0.45)
A.put(music, AMB_C(al.dur + 0.3, 0.05), al.start)          # 屋外の空気を下に敷く（無音にしない）
A.put(music, A.fade(A.bgm_sparse(al.msg + 0.3) * 1.2, 0.5, 0.4), al.start)
A.put(fx, A.sfx_pop(0.3), al.start + al.lines[1][0] - 0.8)
A.put(fx, A.sfx_notify(0.4), al.start + al.msg)
A.put(music, A.fade(A.bgm_morning(al.dur - al.msg + en.dur + 0.3, bright=True), 0.3, 1.5), al.start + al.msg)
A.put(fx, A.sfx_tick(0.25), en.start + 0.3)

music = A.duck(music, voice, 0.6)
mix = voice * 1.0 + fx * 0.8 * FX_LEVEL + music * 0.9
mix = mix[:int(total * A.SR)]
mix /= np.abs(mix).max() / 0.95
p = f"{OUT}/mix.wav"
with wave.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = f"{OUT}/ガクチカループ_第16話.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
