"""完成版の音を作る：声＋BGM＋効果音。BGMは最初から最後まで一定の音量（声で下げない）。
使い方: python3 mix.py short.mp4 bgm.wav sfx.wav out.mp4 [BGMを声より何dB小さくするか(既定12)]
最後に2.6秒、音楽だけの余韻をつける（bgm.wav/sfx.wav はその長さ込みで作っておく）。"""
import sys, subprocess, json, re

TAIL = 2.6


def lufs(path, extra=""):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path] + (["-af", extra + ",ebur128=framelog=quiet"] if extra else ["-af", "ebur128=framelog=quiet"]) +
                       ["-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])


def main():
    short, bgm, sfx, out = sys.argv[1:5]
    gap = float(sys.argv[5]) if len(sys.argv) > 5 else 12.0
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", short],
                               capture_output=True, text=True).stdout)
    voice = lufs(short)                 # 声（完成前の動画の音）の大きさ
    music = lufs(bgm)                   # BGMだけの大きさ
    gain = (voice - gap) - music        # BGMを「声より gap dB 小さい」一定の音量にする
    fc = (f"[0:v]tpad=stop_mode=clone:stop_duration={TAIL}[vo];"
          f"[0:a]apad=pad_dur={TAIL}[v];"
          f"[1:a]volume={gain:.2f}dB[b];[2:a]volume=0.9[s];"
          f"[v][b][s]amix=inputs=3:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", short, "-i", bgm, "-i", sfx, "-filter_complex", fc,
                    "-map", "[vo]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", "-t", f"{dur + TAIL:.2f}", out], check=True)
    print(json.dumps({"voice_lufs": voice, "bgm_lufs": music, "bgm_gain_db": round(gain, 2), "gap_db": gap, "out": out}))


if __name__ == "__main__":
    main()
