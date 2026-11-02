"""第3話の音（声＋効果音＋BGM）。python3 mix3.py → out_ep3/ガクチカループ_第3話.mp4"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep3 as V

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

ou, it, ak, nw, bd, nx, ni, en = (S[k] for k in ("outside", "intro", "ask", "news", "board", "next", "night", "end"))

# 1) 冒頭：つかみの文字と同時にドン。不安な心臓と街の音
A.put(fx, A.sfx_boom(0.8, 2.4), 0.02)
A.put(fx, A.sfx_pop(0.35), 0.05)
A.put(music, A.amb_crowd(ou.dur, 0.1), 0)
A.put(music, A.fade(A.bgm_dark(ou.dur + 0.3), 0.05, 0.4), 0)
A.put(fx, A.sfx_heart(0.5), 0.9); A.put(fx, A.sfx_heart(0.55), 1.6)
A.put(fx, A.sfx_whoosh(0.5, False, 0.3), 0.5)                     # トケイが降りてくる

# 2) 選考会：やわらかいBGM。「落とす場じゃない」のカードでドン
A.put(fx, A.sfx_transition(0.6), it.start - 0.45)
room_len = ni.start - it.start
A.put(music, A.amb_room(room_len, 0.05), it.start)
A.put(music, A.fade(A.bgm_morning(it.rev + 0.2), 0.4, 0.4), it.start)
A.put(fx, A.sfx_riser(0.6, 0.3), it.start + it.rev - 0.6)
A.put(fx, A.sfx_boom(0.85, 2.4), it.start + it.rev)
A.put(fx, A.sfx_pop(0.35), it.start + it.rev)
A.put(music, A.fade(A.bgm_morning(ak.start + ak.dur - it.start - it.rev), 0.8, 0.3), it.start + it.rev + 0.4)

# 3) 気になったニュース：静かに
A.put(music, A.fade(A.bgm_sparse(nw.dur + 0.4), 0.3, 0.4), nw.start - 0.2)
A.put(fx, A.sfx_heart(0.4), nw.start + 0.1)

# 4) ホワイトボード：カードが1枚ずつ
A.put(fx, A.sfx_transition(0.45), bd.start - 0.45)
A.put(music, A.fade(A.bgm_morning(bd.dur + nx.dur, bright=True), 0.4, 0.4), bd.start)
for i in range(3):
    A.put(fx, A.sfx_pop(0.32), bd.start + bd.b0 - 0.2 + i * 0.7)

# 5) 「選ぶのは…こっち側？」：声の前に間を置き、明かす瞬間に一番大きいドン
A.put(fx, A.sfx_riser(0.8, 0.4), nx.start + nx.lines[1][0] - 0.8)
A.put(fx, A.sfx_boom(0.95, 2.6), nx.start + nx.rev)
A.put(fx, A.sfx_ding(0.35), nx.start + nx.rev)

# 6) 夜：不安な持続音と秒針。「危ないのだ」でドン
A.put(fx, A.sfx_transition(0.55), ni.start - 0.45)
A.put(music, A.amb_room(ni.dur, 0.04), ni.start)
A.put(music, A.fade(A.bgm_dark(ni.dur), 0.6, 0.4), ni.start)
A.put(fx, A.sfx_stopwatch(ni.dur - 0.5, 0.5, 0.18), ni.start + 0.3)
A.put(fx, A.sfx_boom(0.6, 2.2), ni.start + ni.lines[2][0] + V.L("13") * 0.6)

# 7) 終わり：音楽だけで締め、最後1.5秒でフェードアウト
A.put(fx, A.sfx_transition(0.55), en.start - 0.45)
A.put(music, A.fade(A.bgm_morning(en.dur, bright=True) * 1.1, 0.2, 1.5), en.start)
A.put(fx, A.sfx_chime_end(), en.start + 0.05)
A.put(fx, A.sfx_pop(0.3), en.start + 0.3)

music = A.duck(music, voice, 0.6)
mix = voice * 1.0 + fx * 0.8 + music * 0.9
mix = mix[:int(total * A.SR)]
mix /= np.abs(mix).max() / 0.95
p = f"{OUT}/mix.wav"
with wave.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = f"{OUT}/ガクチカループ_第3話_本編.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
