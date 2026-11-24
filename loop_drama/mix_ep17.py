"""ガクチカ・ループ 第17話の音。python3 mix_ep17.py → out_ep17/ガクチカループ_第17話.mp4
転換音・環境音は6割、効果音は7割。"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep17 as V

OUT = V.OUT
FX_LEVEL = 0.7


def TR(*a):
    return A.sfx_transition(*a) * 0.6


def AMB_C(*a):
    return A.amb_crowd(*a) * 0.6


def AMB_R(*a):
    return A.amb_room(*a) * 0.6


def sparse(sec):
    return A.bgm_sparse(max(sec, 3.6))[:int(sec * A.SR)]


def claps(sec, vol=0.5, seed=7, people=24):
    """会場の拍手：一人ずつの「パン」（中高域の短い破裂音）を何十人分も重ね、響きと、ざわっとした厚みを足す"""
    rng = np.random.default_rng(seed)
    n = int(sec * A.SR)
    y = np.zeros(n)
    for p in range(people):
        rate = rng.uniform(3.6, 5.2)                    # 1人あたり1秒に4〜5回
        tone = rng.uniform(0.6, 1.4)                    # 手の大きさで音色が少し違う
        amp = rng.uniform(0.4, 1.0) * (0.5 if p % 3 == 0 else 1.0)   # 遠い席は小さく
        t = rng.uniform(0, 0.25)
        while t < sec - 0.05:
            L_ = int((0.008 + 0.01 * rng.random()) * tone * A.SR)
            g = rng.standard_normal(L_) * np.exp(-np.linspace(0, 5.5, L_))
            k = int(t * A.SR)
            y[k:k + L_] += g[:n - k] * amp * rng.uniform(0.7, 1.0)
            t += 1 / rate * rng.uniform(0.85, 1.15)
    # 帯域を 700〜5000Hz に（「コツコツ」した低い音を消して、拍手らしい「パチパチ」に）
    F_ = np.fft.rfft(y)
    f = np.fft.rfftfreq(n, 1 / A.SR)
    F_ *= np.clip((f - 500) / 400, 0, 1) * np.clip((6500 - f) / 2000, 0, 1) * (1 + 0.6 * np.exp(-((f - 2200) / 900) ** 2))
    y = np.fft.irfft(F_, n)
    y = A.reverb(y, 0.35)[:n]
    env = np.minimum(1, np.minimum(np.linspace(0, sec / 0.35, n), np.linspace(sec / 1.0, 0, n)))
    y = y * env
    y = y / (np.sqrt((y ** 2).mean()) + 1e-9) * vol * 0.16       # 大きさは平均（RMS）でそろえる
    return np.clip(y, -0.6, 0.6)


SH = V.SH
total = sum(s.dur for s in SH)
S = {s.name: s for s in SH}
voice = np.zeros(int(total * A.SR) + A.SR)
fx = np.zeros_like(voice)
music = np.zeros_like(voice)
for s in SH:
    for (t0, sid) in s.lines:
        g = 0.85 if sid in V.FLASH else 1.0
        A.put(voice, V.vo(sid) * g, s.start + t0)
co, gr, ta, t2, le, ce, re, ni, en = (S[k] for k in ("cold", "green", "talk", "talk2", "letter", "cert", "realize", "night", "end"))
at = V.at

# 冒頭：会場の背中越し → ドン → タイトル
A.put(fx, A.sfx_boom(0.9, 2.4), 0.02)
A.put(music, AMB_C(co.dur, 0.07), 0)
A.put(music, A.fade(sparse(co.dur + 0.3), 0.1, 0.4), 0)
A.put(fx, TR(0.6), 2.4 - 0.45)

# 控え室：静かな緊張と、少し明るい音
A.put(fx, TR(0.5), gr.start - 0.45)
A.put(music, AMB_R(gr.dur, 0.05), gr.start)
A.put(music, A.fade(A.bgm_tension(gr.dur + 0.3) * 0.45, 0.4, 0.6), gr.start)
A.put(music, A.fade(A.bgm_morning(gr.dur + 0.3) * 0.45, 0.8, 0.6), gr.start)
A.put(fx, A.sfx_pop(0.3), gr.start + at(gr, "07") - 0.8)

# 発表：心臓 → 静かなピアノ、ざわめき
A.put(fx, TR(0.5), ta.start - 0.45)
A.put(fx, A.sfx_heart(0.5), ta.start + 0.3)
A.put(fx, A.sfx_heart(0.45), ta.start + 1.0)
A.put(music, AMB_C(ta.dur, 0.05), ta.start)
A.put(music, A.fade(sparse(ta.dur + t2.dur + 0.3) * 1.2, 0.8, 0.8), ta.start)
A.put(music, AMB_C(1.6, 0.1), ta.start + at(ta, "12") + V.L("12") + 0.1)          # 「面接で答えるために」→ ざわめき
A.put(fx, A.sfx_whoosh(0.4, True, 0.25), t2.start + 0.3)
A.put(music, claps(3.6), t2.start + t2.clap)
A.put(fx, A.sfx_pop(0.3), t2.start + at(t2, "17") - 0.8)

# 手紙：やさしく
A.put(fx, TR(0.45), le.start - 0.45)
A.put(music, A.fade(A.bgm_morning(le.dur + 0.3) * 0.6, 0.6, 0.6), le.start)

# 修了認定証 → チャイム
A.put(fx, TR(0.5), ce.start - 0.45)
A.put(music, AMB_C(ce.dur, 0.04), ce.start)
A.put(fx, A.sfx_ding(0.35), ce.start + 0.8)
A.put(fx, A.sfx_chime_end(), ce.start + at(ce, "22") + V.L("22") + 0.3)

# 気づく：第10話がよみがえる → 1秒の間 → 一番大きいドン → 静かなピアノ
A.put(fx, TR(0.45), re.start - 0.45)
A.put(fx, A.sfx_reverse_swell(1.2) * 0.7, re.start + at(re, "f10") - 1.2)
A.put(music, AMB_C(re.dur, 0.035), re.start)                                     # 間のあいだも、会場の空気を薄く
A.put(music, A.fade(sparse(re.hit - 0.3) * 0.8, 0.5, 0.8), re.start)
A.put(fx, A.sfx_boom(1.0, 3.0), re.start + re.hit)
A.put(music, A.fade(sparse(re.dur - re.hit + 0.3) * 1.3, 1.2, 1.0), re.start + re.hit + 0.6)

# 3/31 23:59：第8話がよみがえる → 秒針 → 0:00でドン
A.put(fx, TR(0.5), ni.start - 0.45)
A.put(fx, A.sfx_reverse_swell(1.2) * 0.7, ni.start + at(ni, "f8") - 1.2)
A.put(music, AMB_R(ni.dur, 0.04), ni.start)
A.put(music, A.fade(A.bgm_mystery(ni.zero + 0.3) * 0.5, 0.8, 0.6), ni.start)
A.put(fx, A.sfx_stopwatch(ni.zero - at(ni, "33") + 1.0, 0.5, 0.18), ni.start + at(ni, "33") - 1.0)
A.put(fx, A.sfx_boom(1.0, 2.8), ni.start + ni.zero)

# 終わり
A.put(music, A.fade(sparse(en.dur + 0.3), 0.5, 1.5), en.start)
A.put(fx, A.sfx_tick(0.25), en.start + 0.3)

music = A.duck(music, voice, 0.6)
mix = voice * 1.0 + fx * 0.8 * FX_LEVEL + music * 0.9
mix = mix[:int(total * A.SR)]
mix /= np.abs(mix).max() / 0.95
p = f"{OUT}/mix.wav"
with wave.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = f"{OUT}/ガクチカループ_第17話.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
