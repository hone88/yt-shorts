"""ガクチカ・ループ 第6話の音。python3 mix_ep6.py → out_ep6/ガクチカループ_第6話.mp4"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep6 as V

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
co, ru, hn, cd, gl, dr, gm, th, st, en = (S[k] for k in ("cold", "rule", "han", "card", "goal", "dream", "game", "think", "street", "end"))

# 0秒：名刺が逆さま。ドン＋会場のざわめき。2.4秒でタイトル
A.put(fx, A.sfx_boom(0.85, 2.4), 0.02)
A.put(fx, A.sfx_pop(0.35), 0.05)
A.put(fx, A.sfx_pop(0.35), 0.5)                         # 名刺のアップ
A.put(music, A.amb_crowd(co.dur + ru.dur + hn.dur + cd.dur, 0.1), 0)
A.put(music, A.fade(A.bgm_morning(co.dur + 0.3), 0.05, 0.4) * 0.8, 0)
A.put(fx, A.sfx_transition(0.6), 2.4 - 0.45)
# 名刺の渡し方
A.put(fx, A.sfx_transition(0.55), ru.start - 0.45)
A.put(music, A.fade(A.bgm_morning(ru.dur + hn.dur + cd.dur, bright=True), 0.3, 0.5), ru.start)
A.put(fx, A.sfx_pop(0.3), ru.start + 0.15)
A.put(fx, A.sfx_pop(0.3), ru.start + 0.65)
# 班分け：同じ班にハルト（ポン）
A.put(fx, A.sfx_transition(0.5), hn.start - 0.45)
A.put(fx, A.sfx_pop(0.3), hn.start + 0.15)
A.put(fx, A.sfx_ding(0.35), hn.start + hn.lines[0][0] + V.L("03") - 0.2)
# 名刺交換
A.put(fx, A.sfx_transition(0.5), cd.start - 0.45)
A.put(fx, A.sfx_pop(0.3), cd.start + 0.5)
A.put(fx, A.sfx_pop(0.3), cd.start + cd.lines[1][0] - 0.1)
# 目標シート：書く音・秒針
A.put(fx, A.sfx_transition(0.5), gl.start - 0.45)
A.put(music, A.amb_room(gl.dur + dr.dur, 0.05), gl.start)
for k in range(6):
    A.put(fx, A.sfx_tick(0.16), gl.start + 0.3 + k * 0.25)
A.put(fx, A.sfx_stopwatch(gl.dur - 1.9, 0.5, 0.16), gl.start + 1.9)
A.put(fx, A.sfx_boom(0.5, 1.6), gl.start + gl.lines[0][0] + V.L("06") * 0.8)   # …面接で答える
# ハルトの目標：キラキラ・静かに
A.put(music, A.fade(A.bgm_sparse(dr.dur + 0.3), 0.6, 0.6), dr.start)
A.put(fx, A.sfx_riser(0.6, 0.25), dr.start + dr.lines[0][0] - 0.6)
A.put(fx, A.sfx_ding(0.35), dr.start + dr.lines[0][0])
A.put(fx, A.sfx_boom(0.55, 1.8), dr.start + dr.lines[0][0] + V.L("09") + 0.2)   # 圧倒されるカナタ
# ミニゲーム：ハイタッチ
A.put(fx, A.sfx_transition(0.55), gm.start - 0.45)
A.put(music, A.amb_crowd(gm.dur + th.dur, 0.12), gm.start)
A.put(music, A.fade(A.bgm_morning(gm.dur, bright=True), 0.3, 0.5), gm.start)
A.put(fx, A.sfx_pop(0.4), gm.start + gm.lines[0][0] + 0.1)
A.put(fx, A.sfx_boom(0.7, 1.8), gm.start + gm.hi)
A.put(fx, A.sfx_pop(0.45), gm.start + gm.hi)
# カナタの心の声：静かに
A.put(music, A.fade(A.bgm_sparse(th.dur + 0.2), 0.3, 0.4) * 0.8, th.start)
A.put(fx, A.sfx_heart(0.4), th.start + 0.2)
# 帰り道：夕方・少しさみしい
A.put(fx, A.sfx_transition(0.55), st.start - 0.45)
A.put(music, A.amb_crowd(st.dur, 0.06), st.start)
A.put(music, A.fade(A.bgm_sparse(st.dur), 0.6, 1.0), st.start)
A.put(fx, A.sfx_whoosh(0.4, False, 0.25), st.start + st.lines[0][0] - 0.4)
# 終わり
A.put(fx, A.sfx_transition(0.6), en.start - 0.45)
A.put(music, A.fade(A.bgm_morning(en.dur, bright=True) * 1.1, 0.1, 1.5), en.start)
A.put(fx, A.sfx_chime_end(), en.start + 0.1)

music = A.duck(music, voice, 0.6)
mix = voice * 1.0 + fx * 0.8 + music * 0.9
mix = mix[:int(total * A.SR)]
mix /= np.abs(mix).max() / 0.95
p = f"{OUT}/mix.wav"
with wave.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = f"{OUT}/ガクチカループ_第6話.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
