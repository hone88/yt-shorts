"""シーンごとの背景画像を作る（use_images が true のチャンネルだけ）。
OPENAI_API_KEY があれば画像生成APIで作り、なければ色のグラデーションで代わりの背景を作る。"""
import base64, json, os, sys, pathlib, urllib.request, hashlib, shutil
from PIL import Image, ImageDraw, ImageFilter

IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "gpt-image-1")
STYLE = "cinematic still, dramatic natural lighting, highly detailed, no text, no letters, no logos, no people's faces in close-up"


def generate(prompt: str, path: pathlib.Path) -> None:
    body = json.dumps({"model": IMAGE_MODEL, "prompt": f"{prompt}. {STYLE}",
                       "size": "1024x1536", "n": 1}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/images/generations", data=body,
                                 headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.load(r)["data"][0]
    path.write_bytes(base64.b64decode(data["b64_json"]))


def placeholder(prompt: str, path: pathlib.Path, i: int) -> None:
    """APIがないとき用。プロンプトから色を決めた抽象的な背景。"""
    h = hashlib.md5(prompt.encode()).digest()
    c1 = (20 + h[0] % 40, 30 + h[1] % 60, 60 + h[2] % 90)
    c2 = (h[3] % 120 + 60, h[4] % 90 + 40, h[5] % 60 + 30)
    W, H = 1024, 1536
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(c1[k] * (1 - t) + c2[k] * t) for k in range(3)))
    for k in range(6):
        x, y, r = h[6 + k] * 4, h[(10 + k) % 16] * 6, 120 + h[(4 + k) % 16]
        d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(min(255, v + 40) for v in c2))
    img.filter(ImageFilter.GaussianBlur(60)).save(path)


def main():
    script_path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "out/script.json")
    script = json.loads(script_path.read_text(encoding="utf-8"))
    style = json.loads((pathlib.Path("channels") / script["channel"] / "style.json").read_text(encoding="utf-8"))
    # 自分で作った動画クリップ（channels/<名前>/clips/<台本ID>/01.mp4 ...）があればそれを使う
    clip_src = pathlib.Path("channels") / script["channel"] / "clips" / str(script.get("id", ""))
    own_images = {}
    if script.get("id") and clip_src.is_dir():
        dst = script_path.parent / "clips"; dst.mkdir(exist_ok=True)
        n = 0
        for f in sorted(clip_src.iterdir()):
            if f.suffix.lower() in (".mp4", ".mov", ".webm"):
                shutil.copy(f, dst / f.name.lower()); n += 1
            elif f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp") and f.stem.isdigit():
                # 画像を置いた場合は、ゆっくりズームする背景として使う（01.jpg → シーン1）
                own_images[int(f.stem) - 1] = f
        print(f"自作クリップ {n} 本・自作画像 {len(own_images)} 枚を背景に使います（足りないシーンは仮の背景）")
    if not style.get("use_images") and not own_images:
        print("このチャンネルは背景画像なし")
        return
    out = script_path.parent / "images"; out.mkdir(exist_ok=True)
    use_api = bool(os.environ.get("OPENAI_API_KEY"))
    for i, s in enumerate(script["scenes"]):
        p = out / f"{i:02d}.png"
        if i in own_images:
            Image.open(own_images[i]).convert("RGB").save(p)
            continue
        prompt = s.get("image_prompt", s["caption"])
        if use_api:
            try:
                generate(prompt, p)
                continue
            except Exception as e:
                print(f"シーン{i + 1}の画像生成に失敗したので代わりの背景を使います: {e}")
        placeholder(prompt, p, i)
    script["ai_images"] = use_api
    script_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"背景画像 {len(script['scenes'])} 枚（AI画像: {'あり' if use_api else 'なし（仮の背景）'}）")


if __name__ == "__main__":
    main()
