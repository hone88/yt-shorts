"""ガクチカ・ループ　キャラクター定義書（ひな形）
ここの数値・色・模様だけを使って毎話描く。見た目を変えるときは、ここだけを直す。

寸法（1ドット = 1/16ブロック、身長2ブロック = 32ドット）
  頭 8×8×8 ／ 胴 8×4×12 ／ 腕 4×4×12 ／ 脚 4×4×12
模様は「正面から見た向き」で、上の行から書く。1文字 = 1ドット。
"""
from g3d import hexc

# ---------- 共通の部品 ----------


def humanoid(head, body, arm, leg, extras=()):
    """head/body/arm/leg: 面ごとの模様 dict（front, back, side, top, bottom, all）"""
    return [
        dict(bone="head", off=(-0.25, -0.25, 0), size=(0.5, 0.5, 0.5), tex=head, color=(0, 0, 0)),
        dict(bone="body", off=(-0.25, -0.125, 0), size=(0.5, 0.25, 0.75), tex=body, color=(0, 0, 0)),
        dict(bone="armL", off=(-0.125, -0.125, -0.625), size=(0.25, 0.25, 0.75), tex=arm, color=(0, 0, 0)),
        dict(bone="armR", off=(-0.125, -0.125, -0.625), size=(0.25, 0.25, 0.75), tex=arm, color=(0, 0, 0)),
        dict(bone="legL", off=(-0.125, -0.125, -0.75), size=(0.25, 0.25, 0.75), tex=leg, color=(0, 0, 0)),
        dict(bone="legR", off=(-0.125, -0.125, -0.75), size=(0.25, 0.25, 0.75), tex=leg, color=(0, 0, 0)),
        *extras,
    ]


def T(rows, pal):
    return (rows, pal)


def face_rows(base, expr, table):
    rows = list(base)
    for i, r in table.get(expr, {}).items():
        rows[i] = r
    return rows


# ====================================================================
# 宇野カナタ（主人公・大学1年／面接の場面は大学4年）
# ====================================================================
KANATA_PAL = {
    "H": hexc("#2b1d16"),  # 髪（黒に近い茶）
    "S": hexc("#f0c49c"),  # 肌
    "s": hexc("#d9a77e"),  # 肌の影
    "W": hexc("#ffffff"),  # 白目
    "E": hexc("#1e1e28"),  # 黒目
    "M": hexc("#a85a50"),  # 口
    "R": hexc("#d63e3e"),  # 赤いパーカー
    "D": hexc("#a82e30"),  # パーカーの影
    "w": hexc("#f2f2f2"),  # パーカーのひも
    "N": hexc("#2c365c"),  # 紺のズボン
    "K": hexc("#f4f4f4"),  # 白い靴
    "k": hexc("#c9c9c9"),  # 靴底
    "J": hexc("#232c4a"),  # スーツ（紺）
    "T": hexc("#c8283a"),  # ネクタイ
    "B": hexc("#111114"),  # 黒（ヘッドホン・革靴）
}
KANATA_FACE = [
    "HHHHHHHH",
    "HHHHHHHH",
    "HSSHSSSH",
    "SSSSSSSS",
    "SEESSEES",  # やる気のない半目
    "SSSSSSSS",
    "SSSMMSSS",
    "SSSSSSSS",
]
KANATA_EXPR = {
    "normal": {},
    "open": {4: "SWESSEWS"},                                  # ふつうに目を開ける
    "shock": {3: "SWWSSWWS", 4: "SWESSEWS", 6: "SSSMMSSS", 7: "SSSMMSSS"},   # 驚き（口が開く）
    "blank": {4: "SWESSEWS", 6: "SSSSSSSS", 5: "SsSSSSsS"},  # 固まる（口なし・汗）
    "smile": {4: "SWESSEWS", 6: "SSMSSMSS", 7: "SSSMMSSS"},
}
KANATA_SIDE = ["HHHHHHHH", "HHHHHHHH", "HHHHHHHS", "HHHHHSSS", "HHHHSSSE", "HHHHSSSS", "HHHSSSSS", "HHHSSSSS"]
KANATA_BACK = ["HHHHHHHH"] * 7 + ["HHSSSSHH"]

HOODIE_FRONT = ["RDSSSSDR", "RRwRRwRR", "RRwRRwRR", "RRRRRRRR", "RRRRRRRR", "RRRRRRRR",
                "RDDDDDDR", "RDRRRRDR", "RDRRRRDR", "RRRRRRRR", "DDDDDDDD", "DDDDDDDD"]
HOODIE_BACK = ["DDDDDDDD", "DDDDDDDD", "RDDDDDDR", "RRRRRRRR"] + ["RRRRRRRR"] * 6 + ["DDDDDDDD"] * 2
SUIT_FRONT = ["JJwSSwJJ", "JJwTTwJJ", "JJwTTwJJ", "JJJTTJJJ", "JJJTTJJJ", "JJJTTJJJ",
              "JJJJJJJJ", "JJJBJJJJ", "JJJJJJJJ", "JJJBJJJJ", "JJJJJJJJ", "JJJJJJJJ"]


def kanata_parts(expr="normal", outfit="hoodie"):
    p = KANATA_PAL
    face = face_rows(KANATA_FACE, expr, KANATA_EXPR)
    head = {"front": T(face, p), "side": T(KANATA_SIDE, p), "back": T(KANATA_BACK, p), "top": T(["HHHH"] * 4, p), "bottom": T(["SSSS"], p)}
    if outfit == "suit":
        body = {"front": T(SUIT_FRONT, p), "all": T(["JJJJJJJJ"] * 12, p), "top": T(["JJ"], p)}
        arm = {"all": T(["JJJJ"] * 9 + ["wwww"] + ["SSSS"] * 2, p), "top": T(["JJ"], p), "bottom": T(["SS"], p)}
        leg = {"all": T(["JJJJ"] * 11 + ["BBBB"], p), "bottom": T(["BB"], p)}
        extras = [dict(bone="head", off=(0.02, -0.06, 0.5), size=(0.07, 0.07, 0.11), color=p["H"])]
    else:
        body = {"front": T(HOODIE_FRONT, p), "back": T(HOODIE_BACK, p), "all": T(["RRRRRRRR"] * 12, p), "top": T(["RR"], p)}
        arm = {"all": T(["RRRR"] * 9 + ["DDDD"] + ["SSSS"] * 2, p), "top": T(["RR"], p), "bottom": T(["SS"], p)}
        leg = {"all": T(["NNNN"] * 10 + ["KKKK", "kkkk"], p), "bottom": T(["kk"], p)}
        extras = [
            dict(bone="head", off=(0.02, -0.06, 0.5), size=(0.07, 0.07, 0.11), color=p["H"]),       # 寝ぐせ
            dict(bone="body", off=(-0.29, 0.05, 0.63), size=(0.1, 0.12, 0.14), color=p["B"]),      # ヘッドホン（左）
            dict(bone="body", off=(0.19, 0.05, 0.63), size=(0.1, 0.12, 0.14), color=p["B"]),       # ヘッドホン（右）
            dict(bone="body", off=(-0.22, -0.17, 0.71), size=(0.44, 0.06, 0.06), color=p["B"]),    # バンド（首の後ろ）
        ]
    return humanoid(head, body, arm, leg, extras)


KANATA = dict(name="kanata", label="宇野カナタ", parts=lambda e="normal": kanata_parts(e, "hoodie"))
KANATA_SUIT = dict(name="kanata", label="宇野カナタ（面接）", parts=lambda e="normal": kanata_parts(e, "suit"))

# ====================================================================
# 宮路ミオ（大学2年・広島第一支部スタッフ）
# ====================================================================
MIO_PAL = {
    "h": hexc("#7a4a2a"), "S": hexc("#f3caa6"), "W": hexc("#ffffff"), "E": hexc("#3a2418"),
    "M": hexc("#c4646a"), "p": hexc("#f0a8a0"), "O": hexc("#ff8a1f"), "o": hexc("#d96f10"),
    "w": hexc("#fafafa"), "L": hexc("#7e9cc8"), "l2": hexc("#6a88b4"), "K": hexc("#f4f4f4"), "k": hexc("#c9c9c9"),
}
MIO_FACE = ["hhhhhhhh", "hhhhhhhh", "hhhhSSSh", "hSSSSSSh", "hWESSEWh", "hpSSSSph", "hSSMMSSh", "SSSSSSSS"]
MIO_EXPR = {"normal": {}, "smile": {6: "hSMSSMSh", 7: "SSSMMSSS"}, "wink": {4: "hWESSEEh", 6: "hSMSSMSh"}}


def mio_parts(expr="normal"):
    p = MIO_PAL
    head = {"front": T(face_rows(MIO_FACE, expr, MIO_EXPR), p), "side": T(["hhhhhhhh", "hhhhhhhh", "hhhhhhhS", "hhhhhSSS", "hhhhSSSE", "hhhhSSSS", "hhhSSSSS", "hhhSSSSS"], p),
            "back": T(["hhhhhhhh"] * 8, p), "top": T(["hhhh"] * 4, p), "bottom": T(["SS"], p)}
    body = {"front": T(["OOwSSwOO"] + ["OOwwwwOO"] * 9 + ["oooooooo"] * 2, p), "all": T(["OOOOOOOO"] * 11 + ["oooooooo"], p), "top": T(["OO"], p)}
    arm = {"all": T(["OOOO"] * 9 + ["oooo"] + ["SSSS"] * 2, p), "top": T(["OO"], p), "bottom": T(["SS"], p)}
    leg = {"all": T(["LLLL"] * 10 + ["KKKK", "kkkk"], p), "bottom": T(["kk"], p)}
    extras = [
        dict(bone="head", off=(-0.09, -0.36, 0.12), size=(0.18, 0.12, 0.3), color=p["h"]),          # ポニーテール
        dict(bone="head", off=(-0.06, -0.27, 0.36), size=(0.12, 0.04, 0.06), color=p["O"]),          # 髪ゴム
        dict(bone="body", off=(0.02, 0.125, 0.18), size=(0.2, 0.04, 0.28), color=hexc("#ffffff")),    # 白いバインダー
    ]
    return humanoid(head, body, arm, leg, extras)


MIO = dict(name="mio", label="宮路ミオ", parts=mio_parts)

# ====================================================================
# 面接官（架空の会社の人事）
# ====================================================================
IV_PAL = {"k": hexc("#18181c"), "S": hexc("#e8bc94"), "G": hexc("#101014"), "W": hexc("#ffffff"), "E": hexc("#1e1e28"),
          "M": hexc("#8a4a44"), "J": hexc("#1c2440"), "w": hexc("#f2f2f2"), "b": hexc("#3a5aa8"), "B": hexc("#0c0c10")}
IV_FACE = ["kkkkkkkk", "kkkkkkkk", "kSSSSSSk", "GGGSSGGG", "GWEGGEWG", "GGGSSGGG", "SSSMMSSS", "SSSSSSSS"]


def interviewer_parts(expr="normal"):
    p = IV_PAL
    head = {"front": T(IV_FACE, p), "side": T(["kkkkkkkk", "kkkkkkkk", "kkkkkkSS", "kkkkGGGG", "kkkkSSSS", "kkkSSSSS", "kkSSSSSS", "kkSSSSSS"], p),
            "back": T(["kkkkkkkk"] * 7 + ["kkSSSSkk"], p), "top": T(["kk"], p), "bottom": T(["SS"], p)}
    body = {"front": T(["JJwSSwJJ", "JJwbbwJJ", "JJwbbwJJ"] + ["JJJbbJJJ"] * 3 + ["JJJJJJJJ"] * 6, p), "all": T(["JJJJJJJJ"] * 12, p), "top": T(["JJ"], p)}
    arm = {"all": T(["JJJJ"] * 9 + ["wwww"] + ["SSSS"] * 2, p), "top": T(["JJ"], p), "bottom": T(["SS"], p)}
    leg = {"all": T(["JJJJ"] * 11 + ["BBBB"], p), "bottom": T(["BB"], p)}
    return humanoid(head, body, arm, leg)


INTERVIEWER = dict(name="interviewer", label="面接官", parts=interviewer_parts)

# ====================================================================
# 森下議員（架空の市議会議員）※政党を思わせる色・バッジは付けない
# ====================================================================
MO_PAL = {"g": hexc("#c9c9cc"), "d": hexc("#8a8a90"), "S": hexc("#ecc29a"), "W": hexc("#ffffff"), "E": hexc("#1e1e28"),
          "M": hexc("#8a4a44"), "J": hexc("#4a4c54"), "w": hexc("#f2f2f2"), "b": hexc("#6a6c74"), "B": hexc("#0c0c10")}
MO_FACE = ["gdgggdgg", "gggggggg", "gSSSSSSg", "SddSSddS", "SWESSEWS", "SSSSSSSS", "SSMSSMSS", "SSSMMSSS"]


def morishita_parts(expr="normal"):
    p = MO_PAL
    head = {"front": T(MO_FACE, p), "side": T(["gggggggg", "gggggggg", "ggggggSS", "ggggSSSS", "ggggSSSE", "gggSSSSS", "ggSSSSSS", "ggSSSSSS"], p),
            "back": T(["gggggggg"] * 7 + ["ggSSSSgg"], p), "top": T(["gg"], p), "bottom": T(["SS"], p)}
    body = {"front": T(["JJwSSwJJ", "JJwbbwJJ", "JJwbbwJJ"] + ["JJJbbJJJ"] * 3 + ["JJJJJJJJ"] * 6, p), "all": T(["JJJJJJJJ"] * 12, p), "top": T(["JJ"], p)}
    arm = {"all": T(["JJJJ"] * 9 + ["wwww"] + ["SSSS"] * 2, p), "top": T(["JJ"], p), "bottom": T(["SS"], p)}
    leg = {"all": T(["JJJJ"] * 11 + ["BBBB"], p), "bottom": T(["BB"], p)}
    return humanoid(head, body, arm, leg)


MORISHITA = dict(name="morishita", label="森下議員", parts=morishita_parts)

# ====================================================================
# トケイ（ループの案内役。宙に浮く目覚まし時計）
# ====================================================================
TK_PAL = {"Y": hexc("#facc3c"), "y": hexc("#d9a820"), "W": hexc("#fbfbf6"), "B": hexc("#151515"), "E": hexc("#151515"), "G": hexc("#ffd650")}
TK_DIAL = ["YYYYYYYY", "YWWWWWWY", "YWWWBWWY", "YWWWBWWY", "YWWWBBWY", "YWWWWWWY", "YWWWWWWY", "YYYYYYYY"]
TK_EXPR = {"normal": {}, "eyes": {2: "YWEWBEWY", 3: "YWEWBEWY"}, "angry": {1: "YWEWWEWY", 2: "YWWEBWWY", 3: "YWEWBEWY"}}


def tokei_boxes(center, t=0.0, expr="eyes", scale=1.0, yaw=0.0, tag="tokei"):
    """center: 本体の中心。上下にゆっくり浮く"""
    from g3d import Box, rz
    import math
    p = TK_PAL
    cx, cy, cz = center
    cz += 0.06 * math.sin(t * 3)
    s = scale
    dial = face_rows(TK_DIAL, expr, TK_EXPR)

    def part(off, size, tex=None, color=p["Y"], glow=False):
        def xf(q, off=off, size=size):
            lp = (off[0] + q[0] * size[0], off[1] + q[1] * size[1], off[2] + q[2] * size[2])
            r = rz(lp, yaw)
            return (cx + r[0] * s, cy + r[1] * s, cz + r[2] * s)
        return Box(xf, color, tex, tag, glow)
    return [
        part((-0.3, -0.15, -0.3), (0.6, 0.3, 0.6), {"front": (dial, p), "all": (["YYYYYY"] * 6, p), "top": (["yyy"] * 3, p)}),
        part((-0.32, -0.08, 0.28), (0.2, 0.16, 0.14), color=p["G"]),   # ベル（左）
        part((0.12, -0.08, 0.28), (0.2, 0.16, 0.14), color=p["G"]),    # ベル（右）
        part((-0.03, -0.03, 0.3), (0.06, 0.06, 0.12), color=p["B"]),   # ベルの軸
        part((-0.25, -0.06, -0.4), (0.1, 0.12, 0.12), color=p["B"]),   # 足（左）
        part((0.15, -0.06, -0.4), (0.1, 0.12, 0.12), color=p["B"]),    # 足（右）
    ]


CAST = [KANATA, KANATA_SUIT, MIO, INTERVIEWER, MORISHITA]
