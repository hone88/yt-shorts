"""第2話の音（声＋効果音＋BGM）。python3 mix2.py A|B → out_ep2<A|B>/ガクチカループ_第2話_<A|B>.mp4"""
import os, subprocess, sys, wave
import numpy as np
import audio as A
import ep2 as V   # sys.argv の A/B で版が決まる

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

jo, on, inf, dz, ask, no, ok, li, nx, af, en = (S[k] for k in ("join", "one", "info", "doze", "ask", "none", "okay", "list", "next", "after", "end"))

# 1) 冒頭0.5秒以内にドン（投票結果）
A.put(fx, A.sfx_boom(0.75, 2.4), 0.02)
A.put(fx, A.sfx_pop(0.35), 0.05)
if V.VAR == "A":
    op = S["open"]
    A.put(music, A.amb_room(op.dur, 0.05), 0)
    A.put(music, A.fade(A.bgm_morning(op.dur), 0.05, 0.3), 0)
    A.put(fx, A.sfx_whoosh(0.4, True, 0.3), 1.15)
else:
    sl, fl, wk = S["sleep"], S["flash"], S["wake"]
    A.put(music, A.amb_room(sl.dur, 0.05), 0)
    A.put(music, A.fade(A.bgm_dark(sl.dur + 0.2), 0.05, 0.2), 0)
    A.put(fx, A.sfx_whoosh(0.5, False, 0.3), sl.start + 1.0)
    A.put(fx, A.sfx_boom(0.5, 2.0), sl.start + 1.45)
    # 面接の一瞬：止まった世界の音
    A.put(fx, A.sfx_glass(), fl.start)
    A.put(music, A.fade(A.bgm_tension(fl.dur), 0.05, 0.1), fl.start)
    A.put(fx, A.sfx_heart(0.6), fl.start + 0.3); A.put(fx, A.sfx_heart(0.7), fl.start + 1.0)
    A.put(fx, A.sfx_rewind(), fl.start + fl.dur - 0.5)
    A.put(fx, A.sfx_transition(0.7), wk.start - 0.45)
    A.put(music, A.amb_room(wk.dur, 0.05), wk.start)
    A.put(music, A.fade(A.bgm_sparse(wk.dur), 0.1, 0.2), wk.start)

# 2) 説明会に入る：日常のBGMを切らさずに
A.put(fx, A.sfx_transition(0.6), jo.start - 0.45)
A.put(fx, A.sfx_pop(0.3), jo.start + 0.2)                 # カメラOFFの札
call_end = dz.start
A.put(music, A.amb_room(call_end - jo.start, 0.05), jo.start)
A.put(music, A.fade(A.bgm_morning(on.start + on.rev - jo.start - 0.6), 0.4, 0.5), jo.start)
A.put(fx, A.sfx_ding(0.3), on.start + 0.05)               # 通話に入った音
# 「カメラOFFでもOK」：やわらかく見せる
A.put(fx, A.sfx_pop(0.35), on.start + on.rev)
A.put(fx, A.sfx_ding(0.3), on.start + on.rev + 0.05)
A.put(fx, A.sfx_boom(0.45, 1.8), on.start + on.rev)
A.put(music, A.fade(A.bgm_morning(dz.start - on.start - on.rev + 0.3), 0.8, 0.4), on.start + on.rev + 0.5)
A.put(fx, A.sfx_whoosh(0.4, True, 0.3), inf.start + inf.lines[0][0])
A.put(fx, A.sfx_whoosh(0.4, True, 0.3), inf.start + inf.lines[1][0] - 0.1)

# 3) うたた寝：秒針→トケイがドンで乱入
A.put(fx, A.sfx_transition(0.5), dz.start - 0.45)
A.put(music, A.amb_room(dz.dur, 0.05), dz.start)
A.put(music, A.fade(A.bgm_sparse(dz.tk + 0.4), 0.3, 0.3), dz.start)
A.put(fx, A.sfx_stopwatch(dz.tk, 0.33, 0.22), dz.start)
A.put(fx, A.sfx_whoosh(0.45, False, 0.35), dz.start + dz.tk)
A.put(fx, A.sfx_boom(0.7, 2.2), dz.start + dz.tk + 0.4)
A.put(fx, A.sfx_alarm(), dz.start + dz.tk + 0.45)
A.put(music, A.fade(A.bgm_mystery(dz.dur - dz.tk), 0.6, 0.4), dz.start + dz.tk + 0.2)
A.put(fx, A.sfx_pop(0.3), dz.start + dz.lines[0][0] + 0.3)

# 4) やりたいこと：静かなピアノ。答えのあとに間
A.put(fx, A.sfx_transition(0.45), ask.start - 0.45)
A.put(music, A.amb_room(ask.dur + no.dur + ok.dur, 0.05), ask.start)
A.put(music, A.fade(A.bgm_sparse(ask.dur + no.dur + ok.dur), 0.5, 0.6), ask.start)
A.put(fx, A.sfx_heart(0.45), no.start + 0.2); A.put(fx, A.sfx_heart(0.5), no.start + 1.2)
A.put(fx, A.sfx_riser(0.6, 0.25), ok.start + ok.camon - 0.6)   # 自分からカメラON
A.put(fx, A.sfx_pop(0.4), ok.start + ok.camon)
A.put(fx, A.sfx_chime_end(), ok.start + ok.camon + 0.05)

# 5) 春にできること：カードが1つずつ
A.put(fx, A.sfx_transition(0.55), li.start - 0.45)
A.put(music, A.amb_room(li.dur + nx.dur, 0.04), li.start)
A.put(music, A.fade(A.bgm_morning(li.dur + nx.dur, bright=True), 0.4, 0.5), li.start)
for i in range(4):
    A.put(fx, A.sfx_pop(0.3), li.start + li.lines[0][0] + 0.25 + i * 0.55)
A.put(fx, A.sfx_boom(0.55, 2.0), li.start + li.lines[1][0])
A.put(fx, A.sfx_riser(0.6, 0.3), nx.start + nx.lines[1][0] + V.L("16") - 0.4)
A.put(fx, A.sfx_boom(0.6, 2.0), nx.start + nx.lines[1][0] + V.L("16") + 0.2)

# 6) 説明会のあと
A.put(fx, A.sfx_transition(0.6), af.start - 0.45)
A.put(music, A.amb_room(af.dur, 0.05), af.start)
A.put(music, A.fade(A.bgm_morning(af.dur), 0.6, 0.4), af.start)
A.put(fx, A.sfx_pop(0.3), af.start + 0.2)

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
final = f"{OUT}/ガクチカループ_第2話_{V.VAR}.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
