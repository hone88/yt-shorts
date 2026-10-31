"""第1話の音（声＋効果音＋BGM）を作り、映像はそのまま差し替える"""
import subprocess, wave, os
import numpy as np
import audio as A
import ep1b as O

HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(f"{HERE}/out3", exist_ok=True)
FPS = 30
SH = O.plan()
# 書き出した映像のフレーム数に合わせる
t = 0
for s in SH:
    n = int(round(s.dur * FPS)); s.start, s.dur = t, n / FPS; t += s.dur
total = t
S = {s.name: s for s in SH}
voice = np.zeros(int(total * A.SR) + A.SR)
fx = np.zeros_like(voice)
music = np.zeros_like(voice)

for s in SH:
    for (t0, sid) in s.lines:
        A.put(voice, O.vo(sid), s.start + t0)

iv = S["interview"]; tf = iv.start + iv.tf
# 1) 冒頭0.5秒以内に強い一撃。ここから最後まで音を途切れさせない
A.put(fx, A.sfx_boom(0.7, 2.4), iv.start + 0.02)
A.put(music, A.fade(A.bgm_tension(iv.tf + 0.05), 0.15, 0.05), iv.start)
A.put(music, A.amb_room(iv.tf, 0.04), iv.start)
for sec in range(int(iv.tf) + 1):
    A.put(fx, A.sfx_tick(0.22), iv.start + sec)
l2 = iv.start + iv.lines[1][0]
A.put(fx, A.sfx_heart(0.5), l2 - 0.1); A.put(fx, A.sfx_heart(0.6), l2 + 0.7); A.put(fx, A.sfx_heart(0.7), l2 + 1.4)
# 2) 止まる瞬間だけ0.6秒の無音 → 暗い持続音で再開
A.put(fx, A.sfx_freeze(), tf)
tk, ru, rw = S["tokei"], S["rules"], S["rewind"]
dark_len = (rw.start + rw.dur) - (tf + 0.6)
A.put(music, A.fade(A.bgm_dark(dark_len), 1.0, 0.4), tf + 0.6)
A.put(music, A.fade(A.bgm_mystery(tk.dur + ru.dur - 0.6), 1.2, 0.6), tk.start + 0.6)
# 3) 劇的な場面に低い「ドン」
A.put(fx, A.sfx_whoosh(0.5, False, 0.3), tk.start + 0.25)
A.put(fx, A.sfx_boom(0.55, 2.0), tk.start + 0.8)
A.put(fx, A.sfx_pop(0.25), tk.start + tk.lines[1][0])
A.put(fx, A.sfx_whoosh(0.4, True, 0.35), ru.start + 0.15)
A.put(fx, A.sfx_pop(0.3), ru.start + ru.lines[0][0] + O.L("05") * 0.5)
# 4) 「あと3回」の直前に盛り上げて、数字でドン
t3 = ru.start + ru.lines[1][0]
A.put(fx, A.sfx_riser(0.9, 0.4), t3 - 0.9)
A.put(fx, A.sfx_boom(0.6, 2.0), t3 + 0.25)
A.put(fx, A.sfx_ding(0.4), t3 + 0.25)
t0 = rw.start + rw.lines[0][0] + O.L("07")
A.put(fx, A.sfx_glass(), t0)
A.put(fx, A.sfx_rewind(), t0 + 0.35)
A.put(fx, A.sfx_reverse_swell(1.0), rw.start + rw.dur - 1.0)
rm, ph, en = S["room"], S["phone"], S["end"]
# 5) 場面転換はシリーズ共通の転換音（シュッ＋ドン）。ドンが切り替わりの瞬間に来るように0.45秒前から
A.put(fx, A.sfx_transition(0.7), rm.start - 0.45)
A.put(fx, A.sfx_alarm(), rm.start + 0.25)
A.put(fx, A.sfx_notify(0.35), rm.start + rm.lines[0][0] - 0.25)
A.put(music, A.amb_room(rm.dur + ph.dur, 0.05), rm.start)
mm = A.bgm_morning(rm.dur + ph.dur)
A.put(music, A.fade(mm, 1.0, 0.3), rm.start)
A.put(fx, A.sfx_transition(0.55), en.start - 0.45)
# 6) 終わりは声のない音楽だけ。最後1.5秒でフェードアウト
A.put(music, A.fade(A.bgm_morning(en.dur, bright=True) * 1.1, 0.2, 1.5), en.start)
A.put(fx, A.sfx_chime_end(), en.start + 0.05)
A.put(fx, A.sfx_pop(0.3), en.start + 0.3); A.put(fx, A.sfx_pop(0.3), en.start + 0.45)

music = A.duck(music, voice, 0.6)
mix = voice * 1.0 + fx * 0.8 + music * 0.9
mix = mix[:int(total * A.SR)]
mix /= np.abs(mix).max() / 0.95
p = f"{HERE}/out3/mix_bgm.wav"
with wave.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = f"{HERE}/out3/ガクチカループ_第1話_BGM.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{HERE}/out3/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
