import sys, render
from PIL import Image
reel = sys.argv[1]; fr = float(sys.argv[2]) if len(sys.argv) > 2 else 0.7
ids = [s["id"] for s in render.SCRIPT["reels"][reel]["scenes"]]
tw, th = 360, 640
sheet = Image.new("RGB", (tw * 4, th * ((len(ids) + 3) // 4)), "white")
for k, i in enumerate(ids):
    r = render.SceneRenderer(reel, i)
    im = r.frame(r.dur * fr).resize((tw, th), Image.LANCZOS)
    sheet.paste(im, ((k % 4) * tw, (k // 4) * th))
import os; os.makedirs("stills", exist_ok=True)
sheet.save(f"stills/sheet_{reel}_{int(fr*100)}.png")
