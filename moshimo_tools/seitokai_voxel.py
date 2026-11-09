"""オリジナル版「生徒会6本勝負」（台本 20261117）。マイクラ風3D。
登場人物はすべてオリジナル：
  僕（ハルト）…ふつうの頭の生徒会長。紺ブレザー・赤ネクタイ・黄色の会長腕章・寝ぐせ1本
  九条ルリ   …天才副会長。栗色のロングヘア・青いカチューシャ・丸メガネ・水色リボン
参考リール（2026-11-09 ゆうき提供の9本）から取り入れたこと：
  ・1コマ目から派手に動く（紙吹雪＋一気に引く）
  ・2人を同じ画面に入れる（3/4の2ショット、肩ごし、目線カメラを往復）
  ・1場面の中で2〜3回カットを切りかえる
  ・最後は短いひねり（第7戦）で終える
使い方:
  python3 seitokai_voxel.py sheets           デザイン定義シート3枚
  python3 seitokai_voxel.py stills k:t,...   確認用の静止画（赤線＝見出し36/43%・字幕68%）
  python3 seitokai_voxel.py 0,2,4            クリップ書き出し（clips/01.mp4 …）"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kaguya2_voxel as K
from kaguya2_voxel import (ticket, phone, bento, breads, umbrella, bubble, qmarks, chalk_text, get, render, finish,
                           shake, rain, roll, cut, snap, lerp, studio, F, hexs, sheet_base)
from voxel import particles, ease, C
from elevator_voxel import put

W, H, FPS, RS = 1080, 1920, 30, 4
K.RS = RS
_est = [5.9, 3.4, 7.5, 4.9, 3.1, 6.6, 3.9, 3.6, 5.8, 3.6, 4.1, 3.3, 2.6, 5.2, 3.5, 3.4, 4.2, 3.9, 4.9, 6.4]
CLIPS = [round(x * 1.27, 1) for x in _est]       # 声は目安の約1.27倍（前回の109秒版の実測から）
FY = K.FY
PX, PZ = 50, 60          # 僕（顔は -z 向き）
RX, RZ = 70, 40          # ルリ（顔は +z 向き＝僕のほう）
EYE_Y = FY + 28

# ---------------------------------------------------------------- デザイン（定義シートと同じ値）
BOKU = {"髪": (0.13, 0.1, 0.08), "肌": (0.94, 0.77, 0.61), "ブレザー": (0.17, 0.2, 0.38), "シャツ": (0.95, 0.95, 0.95),
        "ネクタイ": (0.82, 0.16, 0.2), "ズボン": (0.42, 0.44, 0.5), "靴": (0.95, 0.95, 0.95), "会長の腕章": (0.98, 0.78, 0.12)}
RURI = {"髪": (0.6, 0.37, 0.2), "肌": (0.97, 0.8, 0.68), "カチューシャ": (0.2, 0.5, 1.0), "メガネ": (0.5, 0.18, 0.22),
        "ブレザー": (0.17, 0.2, 0.38), "リボン": (0.35, 0.78, 1.0), "スカート": (0.42, 0.44, 0.5), "ソックス": (0.1, 0.1, 0.12),
        "靴": (0.38, 0.24, 0.15)}
EYE_W, MOUTH = (0.97, 0.97, 0.97), (0.62, 0.25, 0.22)
BLUSH = (1.0, 0.55, 0.6)

# 顔 8×8（上の行から・見る人から見た並び）
BF = {   # 僕：H=髪 S=肌 W=白目 E=黒目 M=口 B=まゆ P=赤み
    "ふつう": ["HHHHHHHH", "HHHHHHHH", "HSSHSSSH", "SSSSSSSS", "SWESSEWS", "SSSSSSSS", "SSSMMSSS", "SSSSSSSS"],
    "きょとん": ["HHHHHHHH", "HHHHHHHH", "HSSHSSSH", "SSSSSSSS", "SSESSESS", "SSSSSSSS", "SSSSMSSS", "SSSSSSSS"],
    "驚き": ["HHHHHHHH", "HHHHHHHH", "HSSHSSSH", "SWWSSWWS", "SWESSEWS", "SSSSSSSS", "SSSMMSSS", "SSSMMSSS"],
    "笑顔": ["HHHHHHHH", "HHHHHHHH", "HSSHSSSH", "SSSSSSSS", "SWESSEWS", "SPSSSSPS", "SSMSSMSS", "SSSMMSSS"],
    "ドヤ": ["HHHHHHHH", "HHHHHHHH", "HBBHSBBH", "SSSSSSSS", "SEESSEES", "SSSSSSSS", "SSSSMMMS", "SSSSSSSS"],
}
RF = {   # ルリ：G=メガネ（メガネなしのときは肌）
    "すまし": ["HHHHHHHH", "HHHHHHHH", "HHSSSSHH", "HGGSSGGH", "HWEGGEWH", "HGGSSGGH", "HSSMMSSH", "HSSSSSSH"],
    "ドヤ": ["HHHHHHHH", "HHHHHHHH", "HHSSSSHH", "HGGSSGGH", "HSEGGESH", "HGGSSGGH", "HSSSMMSH", "HSSSSSSH"],
    "驚き": ["HHHHHHHH", "HHHHHHHH", "HHSSSSHH", "HGGSSGGH", "HWEGGEWH", "HGGSSGGH", "HSSMMSSH", "HSSMMSSH"],
    "照れ": ["HHHHHHHH", "HHHHHHHH", "HHSSSSHH", "HGGSSGGH", "HSEGGESH", "HGGSSGGH", "HPSMMSPH", "HPSSSSPH"],
    "怒り": ["HHHHHHHH", "HHHHHHHH", "HHBSSBHH", "HGGSSGGH", "HWEGGEWH", "HGGSSGGH", "HSMMMMSH", "HSSSSSSH"],
}


def _fc(col, ch, glasses=True, eye=(0.08, 0.07, 0.1)):
    return {"H": col["髪"], "S": col["肌"], "W": EYE_W, "E": eye, "M": MOUTH, "B": col["髪"], "P": BLUSH,
            "G": col.get("メガネ", col["肌"]) if glasses else col["肌"]}[ch]


# ---------------------------------------------------------------- 僕（ハルト）
def boku(c, m, cx=PX, fy=FY, cz=PZ, face="ふつう", arms="down", legs="stand", wet=False, item=None, jump=0.0):
    k = 0.75 if wet else 1.0
    col = {n: tuple(v * k for v in cc) for n, cc in BOKU.items()}
    fy = fy + jump
    if legs == "run":
        put(c, m, cx - 4, cx, fy + 2, fy + 12, cz - 4, cz, col["ズボン"]); put(c, m, cx - 4, cx, fy, fy + 2, cz - 5, cz - 1, col["靴"])
        put(c, m, cx, cx + 4, fy + 2, fy + 12, cz, cz + 4, col["ズボン"]); put(c, m, cx, cx + 4, fy, fy + 2, cz + 1, cz + 5, col["靴"])
    else:
        put(c, m, cx - 4, cx + 4, fy + 2, fy + 12, cz - 2, cz + 2, col["ズボン"], 1, 0.04)
        put(c, m, cx - 4, cx + 4, fy, fy + 2, cz - 2, cz + 2, col["靴"], 1, 0.02)
        put(c, m, cx - 0.5, cx + 0.5, fy, fy + 10, cz - 2, cz - 1.5, tuple(v * 0.75 for v in col["ズボン"]), 1, 0.0)
    by = fy + 12
    put(c, m, cx - 4, cx + 4, by, by + 12, cz - 2, cz + 2, col["ブレザー"], 1, 0.04)
    put(c, m, cx - 2, cx + 2, by + 5, by + 12, cz - 3, cz - 2, col["シャツ"], 1, 0.0)          # 胸元のシャツ
    put(c, m, cx - 1, cx + 1, by + 3, by + 11, cz - 3, cz - 2, col["ネクタイ"], 1, 0.02)       # 赤ネクタイ
    sy = by + 12
    for side in (-1, 1):
        x0 = cx - 8 if side < 0 else cx + 4
        if arms == "up":
            put(c, m, x0, x0 + 4, sy, sy + 10, cz - 2, cz + 2, col["ブレザー"]); put(c, m, x0, x0 + 4, sy + 10, sy + 13, cz - 2, cz + 2, col["肌"])
            band_y = sy + 2
        elif (arms == "reach" and side > 0) or arms in ("hold", "phone") or (arms == "point" and side > 0):
            put(c, m, x0, x0 + 4, sy - 6, sy, cz - 2, cz + 2, col["ブレザー"])
            fx0 = x0 if arms in ("reach", "point") else (x0 + 1 if side < 0 else x0 - 1)
            yy = sy - 6 if arms != "phone" else sy - 4
            if arms == "point":
                yy = sy - 2
            put(c, m, fx0, fx0 + 4, yy - 3, yy + 1, cz - 9, cz - 2, col["ブレザー"])
            put(c, m, fx0, fx0 + 4, yy - 3, yy + 1, cz - 12, cz - 9, col["肌"])
            if arms == "point":
                put(c, m, fx0 + 1, fx0 + 2, yy - 1, yy, cz - 15, cz - 12, col["肌"])
            band_y = sy - 4
        else:
            put(c, m, x0, x0 + 4, sy - 9, sy, cz - 2, cz + 2, col["ブレザー"]); put(c, m, x0, x0 + 4, sy - 12, sy - 9, cz - 2, cz + 2, col["肌"])
            band_y = sy - 4
        if side < 0:
            put(c, m, x0 - 1, x0, band_y, band_y + 2, cz - 2, cz + 2, col["会長の腕章"], 1, 0.02)
            put(c, m, x0, x0 + 4, band_y, band_y + 2, cz - 3, cz - 2, col["会長の腕章"], 1, 0.02)
    hy = sy
    put(c, m, cx - 4, cx + 4, hy, hy + 8, cz - 4, cz + 4, col["肌"], 1, 0.03)
    put(c, m, cx - 4, cx + 4, hy + 6, hy + 8, cz - 4, cz + 4, col["髪"], 1, 0.04)
    put(c, m, cx - 4, cx + 4, hy + 1, hy + 8, cz + 3, cz + 4, col["髪"], 1, 0.04)
    put(c, m, cx - 4, cx - 3, hy + 3, hy + 8, cz - 4, cz + 4, col["髪"], 1, 0.04)
    put(c, m, cx + 3, cx + 4, hy + 3, hy + 8, cz - 4, cz + 4, col["髪"], 1, 0.04)
    put(c, m, cx, cx + 1, hy + 8, hy + 9, cz - 1, cz, col["髪"], 1, 0.04)      # 寝ぐせ1本
    put(c, m, cx - 1, cx, hy + 9, hy + 10, cz - 1, cz, col["髪"], 1, 0.04)
    for r, row in enumerate(BF[face]):
        y = hy + 7 - r
        for i_, ch in enumerate(row):
            x = cx + 3 - i_
            cc = _fc(col, ch)
            put(c, m, x, x + 1, y, y + 1, cz - 4, cz - 3, cc, 1, 0.02)
    if item:
        item(c, m)


# ---------------------------------------------------------------- 九条ルリ
def ruri(c, m, cx=RX, fy=FY, cz=RZ, face="すまし", arms="down", glasses=True, item=None, back=False, wet=False):
    """顔は +z 向き（back=True で -z 向き）。座標はすべて整数のマス。
    arms: down / reach（向かって左の手を前へ）/ hold（両手で胸の前）/ cheek（両手をほおへ）/ cross（腕組み）"""
    def P(x0, x1, y0, y1, z0, z1, cc, mat=1, var=0.03):
        if back:
            z0, z1 = 2 * cz - z1, 2 * cz - z0
        put(c, m, x0, x1, y0, y1, z0, z1, cc, mat, var)
    k = 0.75 if wet else 1.0
    col = {n: tuple(v * k for v in cc) for n, cc in RURI.items()}
    for x0 in (cx - 4, cx + 1):                                         # 脚
        P(x0, x0 + 3, fy, fy + 1, cz - 1, cz + 3, col["靴"])
        P(x0, x0 + 3, fy + 1, fy + 8, cz - 1, cz + 2, col["ソックス"])
        P(x0, x0 + 3, fy + 8, fy + 10, cz - 1, cz + 2, col["肌"])
    P(cx - 5, cx + 5, fy + 9, fy + 14, cz - 3, cz + 3, col["スカート"], 1, 0.04)        # スカート
    for x in range(cx - 4, cx + 5, 2):
        P(x, x + 1, fy + 9, fy + 13, cz + 2, cz + 3, tuple(v * 0.72 for v in col["スカート"]), 1, 0.0)
    by = fy + 13
    P(cx - 4, cx + 4, by, by + 11, cz - 2, cz + 2, col["ブレザー"], 1, 0.04)
    P(cx - 2, cx + 2, by + 5, by + 11, cz + 2, cz + 3, (0.95, 0.95, 0.95), 1, 0.0)      # シャツ
    P(cx - 2, cx + 2, by + 9, by + 10, cz + 2, cz + 3, col["リボン"], 4, 0.0)           # 水色リボン
    P(cx - 1, cx + 1, by + 7, by + 9, cz + 2, cz + 3, col["リボン"], 4, 0.0)
    sy = by + 11
    BL = col["ブレザー"]; SK = col["肌"]
    if arms == "cross":
        for x0 in (cx - 7, cx + 4):
            P(x0, x0 + 3, sy - 6, sy, cz - 1, cz + 2, BL)
        P(cx - 6, cx + 6, sy - 9, sy - 6, cz + 2, cz + 5, BL)
        P(cx - 1, cx + 1, sy - 9, sy - 6, cz + 5, cz + 6, SK)
    else:
        for side, x0 in ((-1, cx - 7), (1, cx + 4)):
            if (arms == "reach" and side < 0) or arms in ("hold", "cheek"):
                P(x0, x0 + 3, sy - 6, sy, cz - 1, cz + 2, BL)
                if arms == "reach":
                    P(x0, x0 + 3, sy - 9, sy - 6, cz + 1, cz + 8, BL); P(x0, x0 + 3, sy - 9, sy - 6, cz + 8, cz + 10, SK)
                elif arms == "hold":
                    fx = x0 + 1 if side < 0 else x0 - 1
                    P(fx, fx + 3, sy - 9, sy - 6, cz + 1, cz + 6, BL); P(fx, fx + 3, sy - 9, sy - 6, cz + 6, cz + 8, SK)
                else:   # cheek：両手をほおへ
                    fx = x0 + 1 if side < 0 else x0 - 1
                    P(fx, fx + 3, sy - 5, sy + 2, cz + 2, cz + 5, BL); P(fx, fx + 3, sy + 2, sy + 5, cz + 4, cz + 6, SK)
            else:
                P(x0, x0 + 3, sy - 9, sy, cz - 1, cz + 2, BL); P(x0, x0 + 3, sy - 11, sy - 9, cz - 1, cz + 2, SK)
        P(cx + 7, cx + 8, sy - 4, sy - 2, cz - 1, cz + 2, col["リボン"], 1, 0.0)           # 副会長の腕章（水色）
    hy = sy
    P(cx - 4, cx + 4, hy, hy + 8, cz - 4, cz + 4, SK, 1, 0.03)                       # 頭
    P(cx - 4, cx + 4, hy + 6, hy + 9, cz - 4, cz + 4, col["髪"], 1, 0.04)            # 上
    P(cx - 4, cx + 4, hy, hy + 8, cz - 4, cz - 3, col["髪"], 1, 0.04)                # 後頭部
    P(cx - 5, cx + 5, hy - 10, hy + 9, cz - 5, cz - 4, col["髪"], 1, 0.04)           # 後ろ髪（腰まで）
    for xs in (cx - 5, cx + 4):
        P(xs, xs + 1, hy - 5, hy + 9, cz - 4, cz + 3, col["髪"], 1, 0.04)            # 横の髪
    P(cx - 5, cx + 5, hy + 8, hy + 9, cz + 1, cz + 2, col["カチューシャ"], 4, 0.0)     # 青いカチューシャ
    for xs in (cx - 5, cx + 4):
        P(xs, xs + 1, hy + 4, hy + 9, cz + 1, cz + 2, col["カチューシャ"], 4, 0.0)
    for r, row in enumerate(RF[face]):
        y = hy + 7 - r
        for i_, ch in enumerate(row):
            x = cx - 4 + i_
            cc = _fc(col, ch, glasses, eye=(0.12, 0.2, 0.5))
            P(x, x + 1, y, y + 1, cz + 3, cz + 4, cc, 1, 0.0)
            if ch == "G" and glasses:
                P(x, x + 1, y, y + 1, cz + 4, cz + 5, cc, 1, 0.0)                        # メガネのふちは1マス前へ
    if item:
        item(c, m)


def tablet(c, m, x, y, z):
    """作戦ノートのタブレット（画面は -z 向き＝僕のほうではなくルリのほう）"""
    put(c, m, x - 4, x + 4, y, y + 6, z - 0.5, z + 0.5, (0.12, 0.12, 0.14), 1, 0.0)
    put(c, m, x - 3.5, x + 3.5, y + 0.5, y + 5.5, z - 0.8, z - 0.5, (0.45, 0.8, 1.3), 4, 0.0)


def glint(img, depth, cam, tgt, fov, t, x, y, z):
    s = 0.5 + 0.5 * math.sin(t * 9)
    particles(img, depth, cam, tgt, fov, np.array([[x, y, z]]), np.array([C(1.6, 1.6, 1.6) * s]), 0.9)


def confetti(img, depth, cam, tgt, fov, t, box, n=500):
    rg = np.random.default_rng(5)
    x0, x1, y0, y1, z0, z1 = box
    p = np.stack([rg.uniform(x0, x1, n) + 2 * np.sin(t * 3 + rg.uniform(0, 6, n)), (rg.uniform(0, 1, n) * (y1 - y0) - 14 * t) % (y1 - y0) + y0, rg.uniform(z0, z1, n)], 1)
    pal = np.array([C(1.3, 0.3, 0.3), C(1.3, 1.1, 0.2), C(0.3, 0.7, 1.4), C(0.4, 1.2, 0.5), C(1.3, 0.6, 1.1)])
    particles(img, depth, cam, tgt, fov, p, pal[rg.integers(0, 5, n)], 0.35)


# ---------------------------------------------------------------- カメラ
def cam_boku(dist, side=0.0, up=0.0, aim=3.0, cx=PX, cz=PZ, fy=FY):
    ey = fy + 28
    return ((cx + side, ey + up, cz - 4 - dist - 12), (cx + side * 0.2, ey + aim, cz))


def cam_ruri(dist, side=0.0, up=0.0, aim=3.0, cx=RX, cz=RZ, fy=FY):
    ey = fy + 27
    return ((cx + side, ey + up, cz + 4 + dist + 16), (cx + side * 0.2, ey + aim, cz))


def two_shot(a=0.0, who="boku", up=8):
    """斜め上からの2ショット。who="boku"：ルリの後ろ（左）から僕の顔、who="ruri"：僕の後ろ（右）からルリの顔"""
    mx = (PX + RX) / 2
    if who == "boku":
        return (RX - 6 + 6 * a, EYE_Y + up, RZ - 22), (mx - 4, EYE_Y - 7, PZ - 4)
    return (PX + 6 + 6 * a, EYE_Y + up, PZ + 22), (mx + 4, EYE_Y - 7, RZ + 4)


def ots_ruri(u=0.0):
    """ルリの肩ごしに僕を見る"""
    return (RX + 4 - 2 * u, EYE_Y + 16, RZ - 14 + 2 * u), (PX + 1, EYE_Y - 2, PZ)


def ots_boku(u=0.0):
    """僕の肩ごしにルリを見る"""
    return (PX - 4 + 2 * u, EYE_Y + 16, PZ + 14 - 2 * u), (RX - 1, EYE_Y - 3, RZ)


def pov_ruri(k=0.0):
    """ルリの目線（少し低い位置から僕を見上げる）"""
    return lerp((RX - 2, EYE_Y - 2, RZ + 7), (PX + 6, EYE_Y - 1, PZ - 18), k), (PX, EYE_Y + 1.5, PZ)


def pov_boku(k=0.0):
    """僕の目線（ルリを見る）"""
    return lerp((PX + 2, EYE_Y + 1, PZ - 7), (RX - 4, EYE_Y, RZ + 18), k), (RX, EYE_Y - 0.5, RZ)


def high_wide(a=0.0, h=50, r=0.0):
    """斜め上からの俯瞰（2人と部屋）"""
    mx, mz = (PX + RX) / 2, (PZ + RZ) / 2
    return (mx + 16 * math.sin(a) + 8, FY + h, mz - 26 - r), (mx, FY + 10, mz + 4)


# ---------------------------------------------------------------- 撮影
def shoot(set_, cam, tgt, fov, draws, grade=(1, 1, 1), t=0.0, dutch=0.0, sh=0.0, fx=None, rain_on=False):
    S = get(set_)
    c, m = S.base_c.copy(), S.base_m.copy()
    for d in draws:
        d(c, m)
    if sh > 0:
        cam, tgt = shake(cam, tgt, sh, t)
    img, depth = render(S, c, m, cam, tgt, fov, W // RS, H // RS)
    if rain_on:
        rain(img, depth, cam, tgt, fov, t, (0, 110, FY, 62, 0, 110))
    if fx:
        fx(img, depth, cam, tgt, fov)
    img = roll(img, dutch)
    return finish(img, grade=grade)


def B(**kw):
    return lambda c, m: boku(c, m, **kw)


def R(**kw):
    return lambda c, m: ruri(c, m, **kw)


RAIN_G = (0.92, 0.96, 1.05)


def frame(k, t):
    T = CLIPS[k]
    if k == 0:   # 紙吹雪の中で会長に → 一気に引いて2人 → 僕の驚き顔
        i, u = cut(t, T, [0.38, 0.72])
        conf = lambda img, d, cam, tgt, fov: confetti(img, d, cam, tgt, fov, t, (20, 95, FY, 62, 10, 100))
        if i == 0:
            z = snap(u, 0.25, 0.7)
            cam, tgt = cam_boku(10 + 44 * z, up=20 * z, aim=1.4 - 14 * z)
            return shoot("room", cam, tgt, 44 + 16 * z, [B(face="驚き", arms="up"), R(face="すまし", arms="cross")], t=t, fx=conf)
        if i == 1:
            cam, tgt = two_shot(-1 + 2 * ease(u), who="boku", up=12)
            return shoot("room", cam, tgt, 58, [B(face="驚き", arms="up"), R(face="ドヤ", arms="cross")], t=t, fx=conf)
        cam, tgt = cam_boku(16 - 4 * ease(u), side=-3)
        return shoot("room", cam, tgt, 44, [B(face="驚き"), R(face="ドヤ", arms="cross")], t=t, dutch=-5, fx=conf)
    if k == 1:   # ルール：2ショット → ルリのドヤ顔
        i, u = cut(t, T, [0.5])
        if i == 0:
            cam, tgt = high_wide(-0.6 + 0.5 * u)
            return shoot("room", cam, tgt, 60, [B(face="きょとん"), R(face="すまし", arms="cross")], t=t)
        cam, tgt = cam_ruri(16 - 4 * ease(u), side=4)
        return shoot("room", cam, tgt, 44, [B(face="きょとん"), R(face="ドヤ", arms="cross")], t=t, dutch=4)
    if k == 2:   # 天才副会長：あおりでメガネが光る → タブレット → 僕「へー」
        i, u = cut(t, T, [0.4, 0.75])
        tab = lambda c, m: tablet(c, m, RX, FY + 15, RZ + 8)
        if i == 0:
            cam = (RX - 2 + 4 * u, FY + 10, RZ + 24); tgt = (RX, EYE_Y + 5, RZ)
            gl = lambda img, d, cam, tgt, fov: glint(img, d, cam, tgt, fov, t, RX + 2.5, FY + 28.5, RZ + 4.8)
            return shoot("room", cam, tgt, 52, [B(face="ふつう"), R(face="ドヤ", arms="cross")], t=t, dutch=6, fx=gl)
        if i == 1:
            cam, tgt = cam_ruri(6 - 2 * ease(u), side=-3)
            gl = lambda img, d, cam, tgt, fov: glint(img, d, cam, tgt, fov, t, RX + 2.5, FY + 28.5, RZ + 5)
            return shoot("room", cam, tgt, 42, [B(face="ふつう"), R(face="ドヤ", arms="hold", item=tab)], t=t, fx=gl)
        cam, tgt = cam_boku(18 - 4 * u, side=3)
        return shoot("room", cam, tgt, 44, [B(face="笑顔"), R(face="ドヤ", arms="hold", item=tab)], t=t)
    if k == 3:   # 映画チケット：僕の肩ごしにルリ → チケットの超アップ → ルリの目線
        i, u = cut(t, T, [0.4, 0.72])
        tk = lambda c, m: ticket(c, m, RX - 5.5, FY + 18, RZ + 11)
        dr = [B(face="きょとん"), R(face="すまし", arms="reach", item=tk)]
        if i == 0:
            cam, tgt = ots_boku(u)
            return shoot("room", cam, tgt, 48, dr, t=t)
        if i == 1:
            cam = (RX + 10 - 3 * u, FY + 30, RZ + 30); tgt = (RX - 5, FY + 20, RZ + 11)
            return shoot("room", cam, tgt, 40 - 6 * ease(u), dr, t=t)
        cam, tgt = pov_ruri(0.2 + 0.3 * u)
        return shoot("room", cam, tgt, 48, dr, t=t)
    if k == 4:   # 「弟と行ってきます！」：ジャンプ → ルリの驚き → 一気に引く
        i, u = cut(t, T, [0.35, 0.65])
        held = lambda c, m: ticket(c, m, PX + 6, FY + 41 + 3 * abs(math.sin(t * 6)), PZ)
        jp = 3 * abs(math.sin(t * 6))
        if i == 0:
            cam, tgt = cam_boku(18, side=-4, aim=3)
            return shoot("room", cam, tgt, 48, [B(face="笑顔", arms="up", item=held, jump=jp), R(face="驚き")], t=t)
        if i == 1:
            cam, tgt = cam_ruri(12, side=-2)
            return shoot("room", cam, tgt, 42, [B(face="笑顔", arms="up", item=held, jump=jp), R(face="驚き")], t=t, sh=0.5)
        z = snap(u, 0, 0.6)
        cam, tgt = high_wide(0.7 * z, h=30 + 28 * z, r=20 + 16 * z)
        return shoot("room", cam, tgt, 50 + 10 * z, [B(face="笑顔", arms="up", item=held, jump=jp), R(face="驚き")], t=t)
    if k == 5:   # 連絡先：廊下の2ショット → ルリの手元のスマホ → ルリの目線
        i, u = cut(t, T, [0.38, 0.7])
        ph = lambda c, m: phone(c, m, RX - 5.5, FY + 17, RZ + 10.5, big=False)
        dr = [B(face="ふつう"), R(face="すまし", arms="reach", item=ph)]
        if i == 0:
            cam, tgt = two_shot(1 - 2 * ease(u), who="ruri", up=6)
            return shoot("hall", cam, tgt, 64, dr, t=t)
        if i == 1:
            cam = (RX - 10, FY + 28, RZ - 4 - 2 * u); tgt = (RX - 5.5, FY + 21, RZ + 10)
            return shoot("hall", cam, tgt, 38, dr, t=t)
        cam, tgt = pov_ruri(0.1 + 0.4 * ease(u))
        return shoot("hall", cam, tgt, 48, dr, t=t)
    if k == 6:   # 「グループ、もう入ってますよ！」：ドヤ顔 → 横からルリがむっとする
        i, u = cut(t, T, [0.5])
        dr = [B(face="ドヤ", arms="phone", item=lambda c, m: phone(c, m, PX + 2, FY + 16, PZ - 13, big=False)), R(face="怒り")]
        if i == 0:
            cam, tgt = cam_boku(20 - 8 * ease(u), side=5)
            return shoot("hall", cam, tgt, 42, dr, t=t)
        cam, tgt = ots_boku(0.5 + 0.5 * u)
        return shoot("hall", cam, tgt, 44, dr, t=t, dutch=-4)
    if k == 7:   # カエルのスタンプ：ルリのスマホ画面 → ルリの固まった顔
        i, u = cut(t, T, [0.5])
        ph = lambda c, m: phone(c, m, RX, FY + 17, RZ + 8, frog=True)
        flip = lambda c, m: None
        if i == 0:
            cam = (RX - 18, FY + 27, RZ + 2 - 3 * u); tgt = (RX, FY + 24, RZ + 8)
            # 画面はルリのほう（-z）を向いている → ルリの後ろから見る
            return shoot("hall", cam, tgt, 30 + 8 * u, [B(face="笑顔"), R(face="驚き", arms="hold", item=ph)], t=t)
        cam, tgt = cam_ruri(8 + 6 * ease(u), side=2)
        sp = lambda c, m: phone(c, m, RX, FY + 15, RZ + 8, big=False)
        return shoot("hall", cam, tgt, 44, [B(face="笑顔"), R(face="驚き", arms="hold", item=sp)], t=t, sh=0.3)
    if k == 8:   # お弁当：真上 → 2ショット（差し出す）→ 僕のきょとん
        i, u = cut(t, T, [0.35, 0.7])
        bz = RZ + 11
        bt = lambda c, m: bento(c, m, RX - 5, FY + 16, bz)
        dr = [B(face="きょとん"), R(face="ドヤ", arms="reach", item=bt)]
        if i == 0:
            cam = (RX - 5 + 2 * u, FY + 44 - 10 * ease(u), bz - 1); tgt = (RX - 5, FY + 17, bz)
            return shoot("room", cam, tgt, 40, dr, t=t)
        if i == 1:
            cam, tgt = two_shot(-1 + 2 * u, who="ruri")
            return shoot("room", cam, tgt, 56, dr, t=t)
        cam, tgt = cam_boku(16 + 4 * u, side=-3)
        return shoot("room", cam, tgt, 44, dr, t=t)
    if k == 9:   # パン3個：あおり → ルリの無表情 → 一気に引く
        i, u = cut(t, T, [0.4, 0.7])
        held = lambda c, m: breads(c, m, PX + 3, FY + 40, PZ - 2)
        dr = [B(face="笑顔", arms="up", item=held), R(face="すまし", arms="reach", item=lambda c, m: bento(c, m, RX - 5, FY + 16, RZ + 11))]
        if i == 0:
            cam = (PX + 6 * math.sin(u), FY + 4, PZ - 24); tgt = (PX, EYE_Y + 7, PZ)
            return shoot("room", cam, tgt, 62, dr, t=t, dutch=6)
        if i == 1:
            cam, tgt = cam_ruri(14, side=-2)
            return shoot("room", cam, tgt, 44, dr, t=t)
        z = snap(u, 0, 0.6)
        cam, tgt = high_wide(-0.6 * z, h=24 + 32 * z, r=18 + 18 * z)
        return shoot("room", cam, tgt, 48 + 12 * z, dr, t=t)
    if k == 10:  # 大雨の昇降口：外から雨ごし2人 → ルリの困り顔（わざと）
        i, u = cut(t, T, [0.5])
        dr = [B(face="ふつう", item=lambda c, m: umbrella(c, m, PX + 8, FY + 10, PZ)), R(face="すまし", arms="cheek")]
        if i == 0:
            cam, tgt = (104 - 14 * ease(u), FY + 22, 52 - 6 * u), ((PX + RX) / 2, FY + 18, 50)
            return shoot("ent", cam, tgt, 54, dr, t=t, grade=RAIN_G, rain_on=True)
        cam, tgt = cam_ruri(14 - 3 * u, side=3)
        return shoot("ent", cam, tgt, 44, dr, t=t, grade=RAIN_G, rain_on=True)
    if k == 11:  # 傘を押しつける（ルリの肩ごし）→ 雨の中へダッシュ
        i, u = cut(t, T, [0.45])
        if i == 0:
            dr = [B(face="笑顔", arms="reach", item=lambda c, m: umbrella(c, m, PX + 6, FY + 19, PZ - 12, horiz=True)), R(face="驚き")]
            cam, tgt = ots_ruri(u)
            return shoot("ent", cam, tgt, 50, dr, t=t, grade=RAIN_G, rain_on=True)
        pz = PZ + 40 * ease(u)
        dr = [R(face="驚き", arms="hold", item=lambda c, m: umbrella(c, m, RX, FY + 15, RZ + 7)),
              B(cz=int(pz), face="笑顔", legs="run" if int(t * 8) % 2 else "stand")]
        cam, tgt = (RX + 8, FY + 44, RZ - 22), (PX, FY + 10, pz)
        return shoot("ent", cam, tgt, 58, dr, t=t, grade=RAIN_G, rain_on=True)
    if k == 12:  # ずぶぬれでくしゃみ → ルリはあきれ顔
        i, u = cut(t, T, [0.5])
        if i == 0:
            cam, tgt = cam_boku(16, side=2)
            return shoot("ent", cam, tgt, 46, [B(face="驚き", wet=True), R(face="すまし", arms="hold")], t=t, grade=(0.85, 0.92, 1.1),
                         rain_on=True, sh=0.9 * max(0, 1 - u * 2))
        cam, tgt = cam_ruri(14, side=-3)
        return shoot("ent", cam, tgt, 44, [B(face="きょとん", wet=True), R(face="怒り", item=lambda c, m: umbrella(c, m, RX - 9, FY + 6, RZ + 1))],
                     t=t, grade=(0.85, 0.92, 1.1), rain_on=True)
    if k == 13:  # 次の日：校舎 → メガネを外したルリ（照れ）→ ルリの目線で僕
        i, u = cut(t, T, [0.3, 0.7])
        if i == 0:
            S_ = get("out")
            cam = (70, 14 + 6 * u, 20 - 12 * u); tgt = (70, 34, 100)
            img, _ = render(S_, S_.base_c, S_.base_m, cam, tgt, 62, W // RS, H // RS)
            return finish(img)
        dr = [B(face="きょとん"), R(face="照れ", glasses=False)]
        if i == 1:
            cam, tgt = cam_ruri(18 - 6 * ease(u), side=-2)
            return shoot("room", cam, tgt, 44, dr, t=t)
        cam, tgt = pov_ruri(0.3 * ease(u))
        return shoot("room", cam, tgt, 48, [B(face="きょとん", item=lambda c, m: qmarks(c, m, PX, FY + 38, PZ, 1, t)), R(face="照れ", glasses=False)], t=t)
    if k == 14:  # 「黒板の日付、まちがってますね！」：指さし → 黒板 → ルリの怒り
        i, u = cut(t, T, [0.4, 0.7])
        board = lambda c, m: chalk_text(c, m, 5, FY + 28, 60, "11/8")
        dr = [board, B(face="驚き", arms="point"), R(face="怒り", glasses=False)]
        if i == 0:
            cam, tgt = (PX - 14, EYE_Y - 2, PZ - 30 + 4 * u), (PX + 3, EYE_Y + 2, PZ)
            return shoot("room", cam, tgt, 52, dr, t=t)
        if i == 1:
            cam = (52 - 10 * ease(u), FY + 31, 53); tgt = (5, FY + 30, 53)
            return shoot("room", cam, tgt, 46, dr, t=t)
        cam, tgt = cam_ruri(12, side=3)
        return shoot("room", cam, tgt, 42, dr, t=t, sh=0.4)
    if k == 15:  # 心理テスト：ルリへゆっくり寄る（ななめ）→ 僕
        i, u = cut(t, T, [0.55])
        tab = lambda c, m: tablet(c, m, RX, FY + 15, RZ + 8)
        if i == 0:
            cam, tgt = cam_ruri(22 - 8 * ease(u), side=-3)
            return shoot("room", cam, tgt, 44, [B(face="ふつう"), R(face="ドヤ", arms="hold", item=tab)], t=t, dutch=-5)
        cam, tgt = cam_boku(22 - 6 * ease(u))
        return shoot("room", cam, tgt, 42, [B(face="きょとん"), R(face="ドヤ", arms="hold", item=tab)], t=t)
    if k == 16:  # 「好きな人の名前を…」：ルリの照れ顔 → 僕の頭の中（吹き出し）
        i, u = cut(t, T, [0.45])
        if i == 0:
            cam, tgt = cam_ruri(14 - 3 * u, side=2)
            return shoot("room", cam, tgt, 42, [B(face="きょとん"), R(face="照れ", arms="cheek")], t=t)
        bub = lambda c, m: bubble(c, m, PX + 17, FY + 26, PZ - 6)
        cam, tgt = (PX + 9, EYE_Y + 2, PZ - 62 + 10 * ease(u)), (PX + 9, EYE_Y + 3, PZ)
        return shoot("room", cam, tgt, 50, [B(face="ドヤ", item=bub)], t=t)
    if k == 17:  # 「ナイフですね」→ ルリの怒り → ドアがバタン
        i, u = cut(t, T, [0.4, 0.7])
        if i == 0:
            cam, tgt = cam_boku(16 - 3 * u, side=-2)
            return shoot("room", cam, tgt, 44, [B(face="ドヤ"), R(face="怒り")], t=t)
        if i == 1:
            cam, tgt = cam_ruri(10 - 2 * u, side=1)
            return shoot("room", cam, tgt, 42, [B(face="ドヤ"), R(face="怒り")], t=t, sh=0.6, dutch=6)
        door = snap(u, 0.15, 0.25)
        def dr_door(c, m):
            if door < 1:
                put(c, m, 92, 105, FY, FY + 40, 72, 73, (0.6, 0.42, 0.26), 1, 0.03)
        cam, tgt = (PX - 25, FY + 34, PZ - 34), (PX + 18, FY + 22, PZ + 12)
        return shoot("room", cam, tgt, 62, [B(face="驚き"), dr_door], t=t, sh=1.4 * max(0, 1 - u * 2.5) if u > 0.15 else 0)
    if k == 18:  # 0勝6敗・帰り道：夕日の校舎の前、ルリが先を歩く → 僕の顔
        i, u = cut(t, T, [0.55])
        ox, oz = 70, 60
        if i == 0:
            rz = oz - 6 - 6 * u
            dr = [lambda c, m: ruri(c, m, cx=ox + 6, cz=rz, face="怒り", back=True), lambda c, m: boku(c, m, cx=ox - 4, cz=int(oz + 8 - 6 * u), face="きょとん")]
            cam, tgt = (ox + 30 * math.sin(0.4 + 0.3 * u), FY + 34 - 6 * u, oz - 64 + 8 * u), (ox, FY + 16, oz)
            return shoot("out", cam, tgt, 56, dr, t=t)
        dr = [lambda c, m: ruri(c, m, cx=ox + 6, cz=oz - 12, face="怒り", back=True), lambda c, m: boku(c, m, cx=ox - 4, cz=oz + 2, face="きょとん", item=lambda c2, m2: qmarks(c2, m2, ox - 4, FY + 38, oz + 2, 1, t))]
        cam, tgt = cam_boku(18 - 4 * u, side=2, cx=ox - 4, cz=oz + 2)
        return shoot("out", cam, tgt, 44, dr, t=t)
    if k == 19:  # 第7戦：僕の笑顔 → ルリの照れ（真っ赤）→ 夕日へ引く
        i, u = cut(t, T, [0.35, 0.65])
        ox, oz = 70, 60
        rz = oz - 12
        dr_r = lambda face: (lambda c, m: ruri(c, m, cx=ox + 6, cz=rz, face=face, arms="cheek" if face == "照れ" else "down"))
        dr_b = lambda c, m: boku(c, m, cx=ox - 4, cz=oz + 2, face="笑顔")
        if i == 0:
            cam, tgt = cam_boku(16 - 3 * ease(u), side=-2, cx=ox - 4, cz=oz + 2)
            return shoot("out", cam, tgt, 44, [dr_r("驚き"), dr_b], t=t)
        if i == 1:
            cam, tgt = cam_ruri(12 - 3 * ease(u), side=2, cx=ox + 6, cz=rz)
            return shoot("out", cam, tgt, 42, [dr_r("照れ"), dr_b], t=t, grade=(1.08, 0.96, 0.92), sh=0.25)
        z = ease(u)
        cam = lerp((ox + 28, FY + 20, oz - 6), (ox + 66, FY + 36, oz - 14), z); tgt = lerp((ox + 1, FY + 18, oz - 5), (ox, FY + 24, oz + 6), z)
        return shoot("out", cam, tgt, 50 + 10 * z, [dr_r("照れ"), dr_b], t=t)


# ---------------------------------------------------------------- デザイン定義シート
def face_tile(grid, colfn, px=29):
    im = Image.new("RGB", (8 * px, 8 * px)); d = ImageDraw.Draw(im)
    for r, row in enumerate(grid):
        for i_, ch in enumerate(row):
            d.rectangle([i_ * px, r * px, i_ * px + px - 1, r * px + px - 1], fill=tuple(int(min(1, v) * 255) for v in colfn(ch)))
    return im


def char_sheet(name, sub, drawf, center, faces, colfn, cols, sizes, mark, out, fz=-1):
    im, d = sheet_base(name, sub)
    cx, cz = center
    tgt = (cx, FY + 16, cz)
    for i_, (nm, a) in enumerate([("正面", 0.0), ("斜め", 0.6), ("横", math.pi / 2), ("後ろ", math.pi)]):
        cam = (cx - fz * 120 * math.sin(a), FY + 20, cz + fz * 120 * math.cos(a))
        v = studio(drawf, cam, tgt, 17, 300, 450, (0.94, 0.95, 0.98))
        x = 50 + i_ * 317; im.paste(v, (x, 142))
        d.text((x + 150, 625), nm, font=F(30), fill=(40, 45, 60), anchor="mm")
    d.text((50, 670), "表情", font=F(40), fill=(20, 20, 30))
    for i_, (nm, g) in enumerate(faces.items()):
        x = 50 + i_ * 250; im.paste(face_tile(g, colfn), (x, 725))
        d.text((x + 116, 990), nm, font=F(30), fill=(40, 45, 60), anchor="mm")
    d.text((1350, 150), "色", font=F(40), fill=(20, 20, 30))
    for i_, (nm, cc) in enumerate(cols.items()):
        y = 205 + i_ * 52
        d.rounded_rectangle([1350, y, 1393, y + 42], 6, fill=tuple(int(min(1, v) * 255) for v in cc), outline=(200, 200, 210))
        d.text((1410, y + 3), nm, font=F(28), fill=(30, 30, 40)); d.text((1640, y + 6), hexs(cc), font=F(26), fill=(90, 95, 110))
    y0 = 225 + len(cols) * 52
    d.text((1350, y0), "寸法", font=F(40), fill=(20, 20, 30))
    for i_, s in enumerate(sizes):
        d.text((1350, y0 + 55 + i_ * 38), s, font=F(26), fill=(60, 65, 80))
    for i_, line in enumerate(mark):
        d.text((50, 1060 + i_ * 50), line, font=F(36), fill=(200, 50, 50))
    im.save(out)


def sheets():
    bfc = lambda ch: _fc(BOKU, ch)
    char_sheet("ハルト（僕）", "主人公・生徒会長（中身はふつうの頭）", lambda c, m: boku(c, m, face="ふつう"), (PX, PZ), BF, bfc, BOKU,
               ["頭 8×8×8", "胴 8×4×12", "腕 4×4×12", "脚 4×4×12", "身長 32ドット＋寝ぐせ"],
               ["目印：赤ネクタイ／黄色い会長の腕章（左腕）／頭の寝ぐせ1本。", "声：白上虎太郎 ふつう。いつも笑顔で、作戦に気づかない。"], "sheet1_haruto.png")
    rfc = lambda ch: _fc(RURI, ch, True, eye=(0.12, 0.2, 0.5))
    char_sheet("九条ルリ", "副会長・全国模試1位の天才", lambda c, m: ruri(c, m, cx=PX, cz=PZ, face="すまし", back=True), (PX, PZ), RF, rfc, RURI,
               ["頭 8×8×8", "胴 8×4×11", "腕 3.5×3.5×11", "脚 3×3×10＋スカート", "髪は腰まで（後ろ）"],
               ["目印：青いカチューシャ／赤ぶちメガネ／水色リボンと腕章／栗色のロングヘア。", "声：四国めたん ノーマル。作戦5だけメガネを外す。"], "sheet2_ruri.png")
    # 3枚目：舞台とカメラの決まりごと
    im, d = sheet_base("舞台と画角", "4つの場所・2人の立ち位置・カットの切りかえ方")
    shots = [("生徒会室（夕方）", "room", two_shot(0.0, "ruri"), [B(face="ふつう"), R(face="すまし")]),
             ("廊下（昼）", "hall", two_shot(0.0, "boku"), [B(face="ふつう"), R(face="すまし")]),
             ("昇降口（大雨）", "ent", ((100, FY + 22, 52), ((PX + RX) / 2, FY + 18, 50)), [B(face="ふつう"), R(face="すまし", arms="cheek")]),
             ("帰り道（夕日）", "out", ((112, 30, 58), (71, 18, 55)), [lambda c, m: ruri(c, m, cx=76, cz=48, face="照れ", arms="cheek"), lambda c, m: boku(c, m, cx=66, cz=62, face="笑顔")])]
    for i_, (nm, st, (cam, tgt), dr) in enumerate(shots):
        S_ = get(st); c, m = S_.base_c.copy(), S_.base_m.copy()
        for f in dr:
            f(c, m)
        img, _ = render(S_, c, m, cam, tgt, 58, 270, 480)
        x = 50 + i_ * 330
        im.paste(Image.fromarray((np.clip(finish(img), 0, 1) * 255).astype(np.uint8)).resize((300, 533)), (x, 150))
        d.text((x + 150, 715), nm, font=F(28), fill=(40, 45, 60), anchor="mm")
    d.text((1390, 150), "画角のルール", font=F(40), fill=(20, 20, 30))
    for i_, s in enumerate(["1場面で2〜3回カットを切りかえる", "2人を同じ画面に（3/4の2ショット）", "肩ごし：僕ごしにルリ／ルリごしに僕", "目線カメラ：ルリは少し低い位置から",
                            "顔は見出しと字幕の間（43〜68%）", "1コマ目は紙吹雪＋一気に引く", "最後は夕日の帰り道で短く"]):
        d.text((1390, 210 + i_ * 44), s, font=F(26), fill=(60, 65, 80))
    d.text((50, 790), "作戦の順番", font=F(40), fill=(20, 20, 30))
    for i_, s in enumerate(["1 映画チケット（生徒会室）", "2 連絡先（廊下）", "3 お弁当（生徒会室）", "4 相合い傘（昇降口・大雨）", "5 メガネを外す（生徒会室）", "6 心理テスト（生徒会室）", "第7戦 帰り道（夕日）"]):
        d.text((50 + (i_ % 4) * 470, 850 + (i_ // 4) * 46), s, font=F(28), fill=(60, 65, 80))
    d.text((50, 1060), "登場人物・舞台・セリフはすべてオリジナル。実在の作品のキャラクターや建物には寄せない。", font=F(32), fill=(200, 50, 50))
    im.save("sheet3_butai.png")


def render_clip(k, out):
    n = int(round(CLIPS[k] * FPS))
    tmp = out[:-4] + '.part.mp4'
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write((frame(k, i / FPS) * 255 + 0.5).astype(np.uint8).tobytes())
        if i % 30 == 0: print(k, i, flush=True)
    ff.stdin.close()
    if ff.wait() == 0:
        os.replace(tmp, out); print('done', out, flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'sheets':
        sheets()
    elif sys.argv[1] == 'stills':
        ims = []
        for s_ in sys.argv[2].split(','):
            k, t = s_.split(':')
            im = Image.fromarray((frame(int(k), float(t)) * 255).astype(np.uint8)).resize((180, 320))
            d = ImageDraw.Draw(im)
            for y in (int(320 * .36), int(320 * .43), int(320 * .68)):
                d.line([(0, y), (180, y)], fill=(255, 0, 0), width=1)
            ims.append(im)
        cols = min(8, len(ims))
        sh = Image.new('RGB', (180 * cols, 320 * ((len(ims) + cols - 1) // cols)))
        for i, im in enumerate(ims):
            sh.paste(im, ((i % cols) * 180, (i // cols) * 320))
        sh.save(sys.argv[3] if len(sys.argv) > 3 else 'stills.png')
    else:
        os.makedirs('clips', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips/{k + 1:02d}.mp4')
