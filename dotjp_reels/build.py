"""python3 build.py r1 [r2 ...]  → out/<reel>.mp4, out/<reel>.srt, out/<reel>_clips.zip"""
import os, subprocess, sys, wave, zipfile
from concurrent.futures import ProcessPoolExecutor
import render

OUT = os.path.join(render.HERE, "out")


def one(args):
    reel, idx, path = args
    render.scene_mp4(reel, idx, path)
    return path


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def build(reel):
    os.makedirs(f"{OUT}/{reel}", exist_ok=True)
    sc = render.SCRIPT["reels"][reel]["scenes"]
    jobs = [(reel, s["id"], f"{OUT}/{reel}/{s['id']}.mp4") for s in sc]
    with ProcessPoolExecutor(2) as ex:
        list(ex.map(one, jobs))
    # 映像をつなぐ
    lst = f"{OUT}/{reel}/list.txt"
    open(lst, "w").write("".join(f"file '{j[2]}'\n" for j in jobs))
    video = f"{OUT}/{reel}/video.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video], check=True)
    # 音声：各場面のフレーム数ちょうどの長さにそろえてつなぐ
    durs = render.durations(reel)
    frames = []
    params = None
    srt, t0, n_srt = [], 0.0, 1
    for s, d in zip(sc, durs):
        n = int(round(d * render.FPS))
        L = n / render.FPS
        with wave.open(f"{render.HERE}/voice/{reel}/{s['id']}.wav") as w:
            params = w.getparams()
            data = w.readframes(w.getnframes())
        need = int(round(L * params.framerate)) * params.sampwidth * params.nchannels
        data = (data + b"\0" * need)[:need]
        frames.append(data)
        cards, cts = render.card_times(s["say"], d - render.TAIL, s.get("sub"))
        for k, (c, ts) in enumerate(zip(cards, cts)):
            te = cts[k + 1] if k + 1 < len(cts) else d - render.TAIL + 0.1
            srt.append(f"{n_srt}\n{srt_time(t0 + ts)} --> {srt_time(t0 + te)}\n" + "\n".join(c) + "\n")
            n_srt += 1
        t0 += L
    raw = f"{OUT}/{reel}/voice.wav"
    with wave.open(raw, "wb") as w:
        w.setparams(params)
        w.writeframes(b"".join(frames))
    final = f"{OUT}/{reel}.mp4"
    tmp = final[:-4] + ".part.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", raw, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, final)
    open(f"{OUT}/{reel}.srt", "w", encoding="utf-8").write("\n".join(srt))
    with zipfile.ZipFile(f"{OUT}/{reel}_clips.zip", "w") as z:
        for j in jobs:
            z.write(j[2], f"{reel}_{os.path.basename(j[2])}")
    print(reel, "done", round(t0, 2), "s")


if __name__ == "__main__":
    for r in sys.argv[1:]:
        build(r)
