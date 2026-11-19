"""ガクチカ・ループ 第14話の音。python3 mix_ep14.py → out_ep14/ガクチカループ_第14話.mp4
転換音・環境音は6割、効果音は7割（第13話から）。"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep14 as V

OUT = V.OUT
FX_LEVEL = 0.7


def TR(*a):
    return A.sfx_transition(*a) * 0.6


def AMB_C(*a):
    return A.amb_crowd(*a) * 0.6


SH = V.SH
total = sum(s.dur for s in SH)
S = {s.name: s for s in SH}
voice = np.zeros(int(total * A.SR) + A.SR)
fx = np.zeros_like(voice)
music = np.zeros_like(voice)
for s in SH:
    for (t0, sid) in s.lines:
        A.put(voice, V.vo(sid), s.start + t0)
co, op, st, ak, wr, ha, ho, en = (S[k] for k in ("cold", "open", "stare", "ask", "write", "haruto", "home", "end"))


def pen(sec):
    """ペンの音（短いノイズのこすれ）"""
    y = A.lowpass(A.noise(sec, 7), 0.35) * 0.25
    return y * (0.6 + 0.4 * np.sin(np.linspace(0, sec * 40, len(y))) ** 2)


# 0秒：ドン＋線を引くペンの音 → 2.4秒でタイトル
A.put(fx, A.sfx_boom(0.9, 2.4), 0.02)
A.put(fx, pen(0.5), 0.2)
A.put(music, A.fade(A.bgm_sparse(co.dur + 0.3), 0.05, 0.4), 0)
A.put(music, AMB_C(total, 0.05), 0)
A.put(fx, TR(0.6), 2.4 - 0.45)

# ハーフタイム → 目標シート
A.put(fx, TR(0.55), op.start - 0.45)
A.put(music, A.fade(A.bgm_morning(op.dur + 0.3), 0.3, 0.6), op.start)
A.put(fx, A.sfx_whoosh(0.4, True, 0.25), op.start + op.sheet)

# 見つめる：静かなピアノ、前のループ（ガラス）
A.put(fx, TR(0.5), st.start - 0.45)
A.put(music, A.fade(A.bgm_sparse(st.dur + ak.dur + 0.3) * 1.3, 0.5, 0.5), st.start)
A.put(fx, A.sfx_glass(), st.start + 0.5)
A.put(fx, A.sfx_reverse_swell(0.9), st.start + 0.55)

# 書き直していいですか：声の前に間（心臓）→ ミオ
A.put(fx, A.sfx_heart(0.45), ak.start + 0.2); A.put(fx, A.sfx_heart(0.5), ak.start + 0.8)

# 書く：線 → ペンの音 → 書き終わりでドン
A.put(fx, TR(0.5), wr.start - 0.45)
A.put(fx, pen(0.6), wr.start + 0.3)
A.put(fx, pen(2.6), wr.start + 1.3)
A.put(fx, A.sfx_boom(1.0, 2.8), wr.start + 3.95)
A.put(music, A.fade(A.bgm_sparse(wr.dur + 0.3), 0.3, 0.3), wr.start)

# ハルト：明るいBGM
A.put(fx, A.sfx_pop(0.35), ha.start + 0.2)
A.put(music, A.fade(A.bgm_morning(ha.dur + 0.3), 0.3, 0.5), ha.start)

# 帰り道：明るい締め
A.put(fx, TR(0.5), ho.start - 0.45)
A.put(fx, A.sfx_pop(0.3), ho.start + ho.lines[0][0] - 0.5)
A.put(music, A.fade(A.bgm_morning(ho.dur + en.dur + 0.3, bright=True), 0.4, 1.5), ho.start)
A.put(fx, A.sfx_tick(0.25), en.start + 0.3)

music = A.duck(music, voice, 0.6)
mix = voice * 1.0 + fx * 0.8 * FX_LEVEL + music * 0.9
mix = mix[:int(total * A.SR)]
mix /= np.abs(mix).max() / 0.95
p = f"{OUT}/mix.wav"
with wave.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = f"{OUT}/ガクチカループ_第14話.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
