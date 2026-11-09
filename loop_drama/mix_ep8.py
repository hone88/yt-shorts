"""ガクチカ・ループ 第8話の音。python3 mix_ep8.py → out_ep8/ガクチカループ_第8話.mp4"""
import os, subprocess, wave
import numpy as np
import audio as A
import ep8 as V

OUT = V.OUT


def TR(*a):     # 画面切り替えの「ふっ」は6割の大きさ（11/9）
    return A.sfx_transition(*a) * 0.6


def AMB_R(*a):  # 環境音も6割
    return A.amb_room(*a) * 0.6


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
co, cn, c1, ev, of, c2, dy, d3, mn, iv, fz, rw, en = (S[k] for k in ("cold", "council", "chat1", "event", "office", "chat2", "days", "d331", "midnight", "iv", "freeze", "rewind", "end"))


def dark(sec):
    return A.bgm_dark(max(sec, 3.0))[:int(sec * A.SR)]


# 0秒：面接の深掘り。ドン → 2.4秒でタイトル
A.put(fx, A.sfx_boom(0.85, 2.4), 0.02)
A.put(fx, A.sfx_pop(0.35), 0.05)
A.put(music, A.fade(dark(co.dur + 0.3), 0.05, 0.4), 0)
A.put(fx, A.sfx_heart(0.55), 0.8); A.put(fx, A.sfx_heart(0.6), 1.5)
A.put(fx, TR(0.6), 2.4 - 0.45)
# 2月〜3月31日の早回し：ストップウォッチがずっと鳴る
mont = mn.start - cn.start
A.put(fx, A.sfx_rewind(), cn.start - 0.4)
A.put(fx, A.sfx_stopwatch(mont, 0.35, 0.18), cn.start)
A.put(music, A.fade(A.bgm_sparse(mont + 0.2), 0.3, 0.5), cn.start)
A.put(music, AMB_R(mont, 0.05), cn.start)
A.put(music, AMB_C(cn.dur + 0.3, 0.08), cn.start)
for j_ in range(3):
    A.put(fx, A.sfx_pop(0.3), cn.start + 0.2 + j_ * 0.3)
for s_ in (c1, c2):
    A.put(fx, TR(0.45), s_.start - 0.4)
    A.put(fx, A.sfx_notify(0.4), s_.start + 0.4); A.put(fx, A.sfx_notify(0.35), s_.start + 1.1)
    A.put(fx, A.sfx_tick(0.35), s_.start + 2.0)           # 既読
    A.put(fx, A.sfx_whoosh(0.4, True, 0.2), s_.start + 2.45)  # パッと閉じる
    A.put(fx, A.sfx_boom(0.6, 1.8), s_.start + 2.85)      # 既読、だけ。
for s_ in (ev, of):
    A.put(fx, TR(0.45), s_.start - 0.4)
    A.put(fx, A.sfx_pop(0.35), s_.start + 0.1)
A.put(music, AMB_C(ev.dur, 0.12), ev.start)
A.put(fx, A.sfx_whoosh(0.6, True, 0.3), dy.start)
for j_ in range(3):
    A.put(fx, A.sfx_tick(0.3), dy.start + j_ * 1.1)
A.put(fx, TR(0.5), d3.start - 0.45)
A.put(fx, A.sfx_boom(0.8, 2.2), d3.start + 0.05)          # 3月31日
# 3月31日 23:59 → 0:00：秒針 → 盛り上げ → ドン
A.put(fx, TR(0.5), mn.start - 0.45)
A.put(fx, A.sfx_stopwatch(mn.zero, 0.5, 0.3), mn.start)
A.put(fx, A.sfx_riser(0.9, mn.zero), mn.start)
A.put(fx, A.sfx_boom(0.95, 2.6), mn.start + mn.zero)
A.put(music, A.fade(dark(mn.dur - mn.zero + iv.dur), 0.1, 0.4), mn.start + mn.zero)
# 面接：秒針と心臓。「何を考えましたか？」のあと声を1秒止めて → 一番大きいドン
A.put(fx, TR(0.55), iv.start - 0.45)
A.put(fx, A.sfx_stopwatch(iv.tf, 0.5, 0.2), iv.start)
A.put(fx, A.sfx_heart(0.5), iv.start + iv.lines[2][0] - 0.3)
for k_ in range(4):
    A.put(fx, A.sfx_heart(0.55 + 0.05 * k_), iv.start + iv.lines[4][0] + k_ * 0.9)
A.put(fx, A.sfx_boom(0.5, 1.8), iv.start + iv.lines[4][0] - 0.1)
A.put(fx, A.sfx_freeze(), iv.start + iv.tf)
A.put(fx, A.sfx_boom(1.0, 2.8), iv.start + iv.tf)
# 世界が止まる：0.6秒の無音 → 暗い持続音。残りループ 2→1
A.put(music, A.fade(A.bgm_heavy(max(fz.dur + 0.6, 3.0))[:int((fz.dur - 0.6 + iv.dur - iv.tf) * A.SR)], 0.3, 0.4), iv.start + iv.tf + 0.6)
A.put(fx, A.sfx_whoosh(0.5, False, 0.3), fz.start)
A.put(fx, A.sfx_boom(0.9, 2.4), fz.start + 0.6)
A.put(fx, A.sfx_glass(), fz.start + 0.6)
# 巻き戻し：ガラス → 逆回転
A.put(fx, A.sfx_glass(), rw.start + rw.t0)
A.put(fx, A.sfx_rewind(), rw.start + rw.t0 + 0.3)
A.put(fx, A.sfx_reverse_swell(1.2), rw.start + rw.dur - 1.3)
A.put(music, A.fade(dark(rw.dur + 0.3), 0.2, 0.3), rw.start)
A.put(music, AMB_R(rw.dur + en.dur, 0.06), rw.start)
# 終わり：静かな締め
A.put(music, A.fade(A.bgm_sparse(en.dur + 0.3) * 1.4, 0.2, 1.2), en.start - 0.3)
A.put(fx, A.sfx_tick(0.25), en.start + 0.3)

music = A.duck(music, voice, 0.6)
mix = voice * 1.0 + fx * 0.8 + music * 0.9
mix = mix[:int(total * A.SR)]
mix /= np.abs(mix).max() / 0.95
p = f"{OUT}/mix.wav"
with wave.open(p, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(A.SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
final = f"{OUT}/ガクチカループ_第8話.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/video.mp4", "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", final + ".part.mp4"], check=True)
os.replace(final + ".part.mp4", final)
print("ok", round(total, 2))
