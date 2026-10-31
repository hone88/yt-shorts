"""キャラクター定義書の設定画（1キャラ1枚・横長）"""
import math, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E
import g3d as G
from g3d import Camera, Rig, render
import characters as C
F = lambda s, b=True: E.font(E.FONT_BLACK if b else E.FONT_BOLD, s)

def bgimg():
    return Image.new("RGB", (G.W * G.SS, G.H * G.SS), (238, 241, 247))

def full(spec, yaw, expr="normal"):
    r = Rig(spec, (0, 0, 0), yaw); r.expr = expr
    img, _ = render(r.boxes(), Camera((0, -4.6, 1.1), (0, 0, 1.0), 38), bgimg())
    return img.crop((140, 360, 940, 1560))  # 800x1200

def face(spec, expr):
    r = Rig(spec, (0, 0, 0), math.pi); r.expr = expr
    img, _ = render(r.boxes(), Camera((0, -2.3, 1.78), (0, 0, 1.74), 26), bgimg())
    return img.crop((40, 440, 1040, 1440)).resize((380, 380))

def tk(expr, yaw=math.pi):
    img, _ = render(C.tokei_boxes((0, 0, 0), 0, expr, 1.0, yaw), Camera((0, -2.8, 0.1), (0, 0, 0.0), 38), bgimg())
    return img.crop((140, 360, 940, 1560))

def make(key):
    info = {
        "kanata": (C.KANATA, "宇野カナタ", "主人公・大学1年（ふだん）", ["normal", "open", "shock", "blank", "smile"], ["半目（基本）", "目を開く", "驚き", "固まる", "笑顔"],
                   [("髪", "#2b1d16"), ("肌", "#f0c49c"), ("パーカー", "#d63e3e"), ("ズボン", "#2c365c"), ("靴", "#f4f4f4"), ("ヘッドホン", "#111114")],
                   "目印：赤いパーカー／頭の寝ぐせ1つ／首の黒いヘッドホン。止まった灰色の世界で、カナタだけ色が残る。"),
        "suit": (C.KANATA_SUIT, "宇野カナタ（面接）", "大学4年・面接の場面だけ", ["normal", "open", "shock", "blank"], ["半目", "目を開く", "驚き", "固まる"],
                 [("髪", "#2b1d16"), ("肌", "#f0c49c"), ("スーツ", "#232c4a"), ("ネクタイ", "#c8283a"), ("シャツ", "#f2f2f2")],
                 "目印：赤いネクタイ（パーカーの赤と同じ系統）。寝ぐせは面接でも残す。"),
        "mio": (C.MIO, "宮路ミオ", "大学2年・広島第一支部スタッフ", ["normal", "smile", "wink"], ["ふつう", "笑顔", "ウインク"],
                [("髪", "#7a4a2a"), ("肌", "#f3caa6"), ("ジャケット", "#ff8a1f"), ("シャツ", "#fafafa"), ("ジーンズ", "#7e9cc8")],
                "目印：オレンジのジャケット／ポニーテール／白いバインダー。ほおに赤み。"),
        "iv": (C.INTERVIEWER, "面接官", "架空の会社の人事（40代）", ["normal"], ["ふつう"],
               [("髪", "#18181c"), ("肌", "#e8bc94"), ("スーツ", "#1c2440"), ("ネクタイ", "#3a5aa8"), ("メガネ", "#101014")],
               "目印：黒いメガネ。会社名・ロゴは出さない。"),
        "mo": (C.MORISHITA, "森下議員", "架空の市議会議員（50代）", ["normal"], ["笑顔（基本）"],
               [("髪", "#c9c9cc"), ("肌", "#ecc29a"), ("スーツ", "#4a4c54"), ("ネクタイ", "#6a6c74")],
               "目印：白髪まじり・灰色のスーツ。政党を思わせる色・バッジ・ポスターは付けない。"),
    }
    out = Image.new("RGB", (2400, 1500), (250, 250, 252))
    d = ImageDraw.Draw(out)
    if key == "tokei":
        name, role = "トケイ", "ループの案内役・宙に浮く目覚まし時計"
        views = [tk("normal"), tk("eyes", math.pi + 0.7), tk("eyes", math.pi / 2), tk("normal", 0)]
        faces, flabels = [], []
        pal = [("本体", "#facc3c"), ("文字盤", "#fbfbf6"), ("針・目", "#151515"), ("ベル", "#ffd650")]
        note = "目印：黄色い四角・金のベル2つ。話すときだけ文字盤に目が出る。ゆっくり上下に浮く。語尾「〜のだ」。"
        size = "本体 9.6×4.8×9.6ドット／人物の頭とほぼ同じ大きさ"
    else:
        spec, name, role, exprs, flabels, pal, note = info[key]
        views = [full(spec, math.pi), full(spec, math.pi + 0.7), full(spec, math.pi / 2), full(spec, 0)]
        faces = [face(spec, e) for e in exprs]
        size = "頭 8×8×8／胴 8×4×12／腕 4×4×12／脚 4×4×12／身長 32ドット（2ブロック）"
    d.text((60, 40), name, font=F(80), fill=(20, 22, 40))
    d.text((60 + F(80).getlength(name) + 30, 74), role, font=F(40, False), fill=(90, 96, 120))
    for i, (v, lab) in enumerate(zip(views, ["正面", "斜め", "横", "後ろ"])):
        im = v.resize((360, 540))
        out.paste(im, (60 + i * 380, 170))
        d.text((60 + i * 380 + 180 - F(34).getlength(lab) / 2, 720), lab, font=F(34), fill=(60, 64, 90))
    x0 = 1620
    d.text((x0, 170), "色", font=F(44), fill=(20, 22, 40))
    for j, (lab, hx) in enumerate(pal):
        y = 240 + j * 70
        d.rounded_rectangle([x0, y, x0 + 54, y + 54], radius=10, fill=G.hexc(hx), outline=(180, 184, 200), width=2)
        d.text((x0 + 76, y + 4), f"{lab}", font=F(36), fill=(30, 32, 50))
        d.text((x0 + 300, y + 8), hx, font=F(32, False), fill=(110, 116, 140))
    yb = 240 + len(pal) * 70 + 30
    d.text((x0, yb), "寸法", font=F(44), fill=(20, 22, 40))
    for k, line in enumerate(size.split("／") if "／" in size else [size[i:i + 19] for i in range(0, len(size), 19)]):
        d.text((x0, yb + 64 + k * 46), line, font=F(32, False), fill=(60, 64, 90))
    if faces:
        d.text((60, 800), "表情", font=F(44), fill=(20, 22, 40))
        for i, (f, lab) in enumerate(zip(faces, flabels)):
            out.paste(f.resize((280, 280)), (60 + i * 300, 870))
            d.text((60 + i * 300 + 140 - F(32).getlength(lab) / 2, 1160), lab, font=F(32), fill=(60, 64, 90))
    lines = [note[i:i + 36] for i in range(0, len(note), 36)]
    for k, line in enumerate(lines):
        d.text((60, 1280 + k * 56), line, font=F(40), fill=(200, 60, 60))
    out.save(f"定義書_{name}.png")

if __name__ == "__main__":
    for k in sys.argv[1:]:
        make(k)
