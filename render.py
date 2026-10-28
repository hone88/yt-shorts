"""シーンごとの縦長画像(1080x1920)を作り、音声と合わせてショート動画にする。
背景画像（out/images）があれば全面に敷き、なければ単色の背景にする。"""
import json, os, sys, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

W, H = 1080, 1920
BG, PANEL, INK, QUIET = "#0F172A", "#16294A", "#F8FAFC", "#94A3B8"
FONT = os.environ.get("JP_FONT", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")


def font(size):
    return ImageFont.truetype(FONT, size, index=0)


def wrap(draw, text, f, max_w):
    lines, line = [], ""
    for ch in text:
        if draw.textlength(line + ch, font=f) > max_w:
            lines.append(line); line = ch
        else:
            line += ch
    if line:
        lines.append(line)
    # 最後の行が1〜2文字だけ（「ら？」など）にならないよう、前の行から文字を回す
    while len(lines) > 1 and len(lines[-1]) <= 3 and len(lines[-2]) > 6:
        lines[-1] = lines[-2][-2:] + lines[-1]
        lines[-2] = lines[-2][:-2]
    return lines


def cover(path):
    """画像を縦長に切り抜き、文字が読めるよう少し暗くする。"""
    im = Image.open(path).convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    l, t = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((l, t, l + W, t + H))
    return ImageEnhance.Brightness(im).enhance(0.62)


def outlined(d, xy, text, f, fill, anchor="mm", width=6):
    d.text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=width, stroke_fill="#000000")


def background(bg_path):
    if bg_path and bg_path.exists():
        return cover(bg_path)
    img = Image.new("RGB", (W, H), BG)
    ImageDraw.Draw(img).ellipse([W - 700, -300, W + 500, 900], fill="#13213B")
    return img


def overlay(scene, i, n, style):
    """文字・時刻バッジ・字幕だけを透明な画像に描く（背景が静止画でも動画でも重ねられる）。"""
    accent = style.get("accent", "#22D3EE")
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # channel name + progress
    outlined(d, (W / 2, 170), style["channel_name"], font(40), QUIET, width=3)
    gap = 34
    x0 = W / 2 - gap * (n - 1) / 2
    for k in range(n):
        r = 9 if k == i else 6
        d.ellipse([x0 + gap * k - r, 230 - r, x0 + gap * k + r, 230 + r], fill=accent if k <= i else "#334155")
    # time badge (moshimo)
    if scene.get("time"):
        f_t = font(64)
        tw = d.textlength(scene["time"], font=f_t)
        d.rounded_rectangle([W / 2 - tw / 2 - 40, 330, W / 2 + tw / 2 + 40, 430], 50, fill=accent)
        d.text((W / 2, 380), scene["time"], font=f_t, fill="#0F172A", anchor="mm")
    # caption: shrink to one line, else split in half
    cap = scene["caption"]
    size = 120
    while size > 80 and d.textlength(cap, font=font(size)) > W - 140:
        size -= 4
    f_cap = font(size)
    cap_lines = [cap] if d.textlength(cap, font=f_cap) <= W - 140 else [cap[:(len(cap) + 1) // 2], cap[(len(cap) + 1) // 2:]]
    y = 760 - (len(cap_lines) - 1) * 70
    for ln in cap_lines:
        outlined(d, (W / 2, y), ln, f_cap, accent if i == 0 else INK, width=8)
        y += 140
    # subtitle panel
    f_sub = font(50)
    sub_lines = wrap(d, scene["narration"], f_sub, W - 200)
    top = 1300
    d.rounded_rectangle([70, top, W - 70, top + 80 + 76 * len(sub_lines)], 32, fill=(15, 23, 42, 215))
    yy = top + 78
    for ln in sub_lines:
        d.text((W / 2, yy), ln, font=f_sub, fill=INK, anchor="mm")
        yy += 76
    return img


def find_clip(base, i):
    for ext in ("mp4", "mov", "webm"):
        p = base / "clips" / f"{i + 1:02d}.{ext}"
        if p.exists():
            return p
    return None


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duration(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout)


def main():
    script_path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "out/script.json")
    base = script_path.parent
    script = json.loads(script_path.read_text(encoding="utf-8"))
    style = json.loads((pathlib.Path("channels") / script["channel"] / "style.json").read_text(encoding="utf-8"))
    scenes = script["scenes"]
    seg_dir = base / "segments"; seg_dir.mkdir(exist_ok=True)
    img_dir = base / "slides"; img_dir.mkdir(exist_ok=True)
    segs = []
    enc = ["-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2"]
    for i, s in enumerate(scenes):
        ov = overlay(s, i, len(scenes), style)
        wav = base / "audio" / f"{i:02d}.wav"
        secs = duration(wav)
        seg = seg_dir / f"{i:02d}.mp4"
        clip = find_clip(base, i)
        if clip:
            # 自分で作った動画クリップを背景に敷き、文字を重ねる。
            # 声より短いクリップはループさせず（ループすると冒頭に戻る瞬間がチラついて見える）、
            # ゆっくり再生にして声の長さに合わせる。長いクリップは途中で切る。
            ov_png = img_dir / f"{i:02d}_overlay.png"
            ov.save(ov_png)
            stretch = max(1.0, (secs + 0.1) / max(duration(clip), 0.1))
            vf = (f"[0:v]setpts={stretch:.4f}*(PTS-STARTPTS),"
                  f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                  f"eq=brightness=-0.12,fps=30,setsar=1,tpad=stop_mode=clone:stop_duration=1[bg];"
                  f"[bg][1:v]overlay=0:0[v]")
            run(["ffmpeg", "-y", "-i", str(clip), "-i", str(ov_png), "-i", str(wav),
                 "-filter_complex", vf, "-map", "[v]", "-map", "2:a", "-t", f"{secs:.3f}", *enc, str(seg)])
        else:
            png = img_dir / f"{i:02d}.png"
            bg = background(base / "images" / f"{i:02d}.png").convert("RGBA")
            Image.alpha_composite(bg, ov).convert("RGB").save(png)
            frames = int(secs * 30) + 1
            zoom = f"scale=2160:-1,zoompan=z='min(zoom+0.0005,1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=30"
            run(["ffmpeg", "-y", "-i", str(png), "-i", str(wav), "-vf", zoom, *enc, "-shortest", str(seg)])
        segs.append(seg)
    lst = base / "segments.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in segs), encoding="utf-8")
    out = base / "short.mp4"
    # 声が小さくならないよう、ショート動画の標準的な音量（-14 LUFS）にそろえる
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:v", "copy",
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
         "-movflags", "+faststart", str(out)])
    dur = duration(out)
    tags = " ".join("#" + t for t in script.get("tags", []))
    checks = "\n".join(f"- シーン{c.get('scene')}: {c.get('problem')} → {c.get('fix')}" for c in script.get("factcheck", [])) or "- なし"
    memo = f"""【タイトル】
{script['title']} #Shorts

【概要欄】
{script['description']}
{('▶ ほかの「もしも」はこちら ' + style['handle']) if style.get('handle') else ''}

{tags}

{style['voice_credit']}

【メモ（投稿しない）】
チャンネル: {style['channel_name']}
テーマ: {script.get('topic', '')}
長さ: {dur:.1f}秒 / 音声: {'VOICEVOX' if script.get('voiced') else 'なし（プレビュー）'} / AI画像: {'あり' if script.get('ai_images') else 'なし'}
AIのファクトチェックで直した点:
{checks}
投稿前に、言い過ぎや事実の間違いがないか一度見てください。
"""
    (base / "upload_memo.txt").write_text(memo, encoding="utf-8")
    print(f"動画: {out}（{dur:.1f}秒）")


if __name__ == "__main__":
    main()
