"""動画をコマ単位で調べる：逆戻り・カクつき（同じコマの重なり）・急な飛び。
使い方: python3 check_motion.py video.mp4 [--from 秒 --to 秒]
判定（下の3つ。字幕や見出しの帯は除いて、絵の部分だけで比べる）
  逆戻り : コマ i が 1つ前より 2つ前に近い（i-1 → i で前に戻った）
  重なり : 動いている場面の途中で、前のコマとほぼ同じ（ゆっくり再生で同じコマが続く）
  飛び   : 前後よりずっと大きい変化（場面転換・カット以外で起きたら瞬間移動の疑い）"""
import sys, subprocess
import numpy as np

W, H = 135, 240


def frames(path, t0=None, t1=None):
    cmd = ["ffmpeg", "-v", "error"]
    if t0 is not None:
        cmd += ["-ss", str(t0)]
    cmd += ["-i", path]
    if t1 is not None:
        cmd += ["-t", str(t1 - (t0 or 0))]
    cmd += ["-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
    # 文字の帯（見出し 30〜48%、字幕 62〜80%）と上の進捗バーを除く
    keep = np.ones(H, bool)
    for y0, y1 in ((0.0, 0.14), (0.30, 0.48), (0.62, 0.80)):
        keep[int(H * y0):int(H * y1)] = False
    return a[:, keep, :]


def main():
    path = sys.argv[1]
    t0 = float(sys.argv[sys.argv.index("--from") + 1]) if "--from" in sys.argv else None
    t1 = float(sys.argv[sys.argv.index("--to") + 1]) if "--to" in sys.argv else None
    f = frames(path, t0, t1)
    n = len(f)
    d1 = np.array([np.abs(f[i] - f[i - 1]).mean() for i in range(1, n)])            # i-1 → i
    d2 = np.array([np.abs(f[i] - f[i - 2]).mean() for i in range(2, n)])            # i-2 → i
    base = t0 or 0
    back, dup, jump = [], [], []
    med = np.median(d1[d1 > 0.05]) if (d1 > 0.05).any() else 1
    for i in range(2, n):
        a, b = d1[i - 1], d2[i - 2]           # a: i-1→i、b: i-2→i
        prev = d1[i - 2]                       # i-2→i-1
        if prev > 0.6 and a > 0.6 and b < 0.5 * min(a, prev):
            back.append(round(base + i / 30, 2))
        if a < 0.08 and prev > 0.5 and (i < n - 1 and d1[i] > 0.5):
            dup.append(round(base + i / 30, 2))
        if a > 6 * med and a > 8:
            jump.append(round(base + i / 30, 2))
    print(f"コマ数 {n}  動きの中央値 {med:.2f}")
    print("逆戻りの疑い:", back[:30], f"({len(back)})")
    print("重なり（カクつき）の疑い:", dup[:30], f"({len(dup)})")
    print("大きな飛び（カット含む）:", jump[:40], f"({len(jump)})")


if __name__ == "__main__":
    main()
