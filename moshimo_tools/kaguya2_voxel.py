"""かぐや様パロディ・長尺版（6本勝負）。マイクラ風3D。
デザイン定義書のルール：画面に描くのは「僕」とオリジナルの舞台・小物だけ。
原作キャラクターは描かない（声・画面の外から伸びる手・小物・目線カメラで出す）。
参考動画（1〜2秒ごとに画角が変わる）に合わせ、1場面の中で2〜3回カットを切りかえる。
使い方:
  python3 kaguya2_voxel.py sheets           デザイン定義シート3枚
  python3 kaguya2_voxel.py stills [k:t,...] 確認用の静止画
  python3 kaguya2_voxel.py 0,1,2            クリップ書き出し（clips/01.mp4 …）"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import Scene, render, particles, smooth, ease, C, f32
from elevator_voxel import put, finish, shake

W, H, FPS, RS = 1080, 1920, 30, 4
import elevator_voxel as _EV
_EV.RS = RS   # 仕上げ（拡大）も同じ倍率に
CLIPS = [6.6, 3.3, 6.2, 4.9, 2.8, 6.5, 3.9, 2.7, 5.7, 4.3, 3.9, 3.3, 2.5, 5.0, 3.3, 3.4, 4.2, 3.8, 4.4, 4.8]
FY = 2
PX, PZ = 55, 60                     # 僕の立ち位置（顔は -z 向き）
EYE_Y = FY + 28                     # 目の高さ
HER = (63, 40)                      # 相手役（画面に出さない）の位置

# ---- 僕のデザイン（定義書と同じ値） ----
COL = {
    "髪": (0.16, 0.11, 0.08), "肌": (0.94, 0.77, 0.61), "シャツ": (0.93, 0.48, 0.12),
    "ズボン": (0.2, 0.3, 0.6), "靴": (0.95, 0.95, 0.95), "腕章": (0.98, 0.78, 0.12),
}
EYE_W, EYE_D, MOUTH, BROW = (0.97, 0.97, 0.97), (0.08, 0.07, 0.1), (0.62, 0.25, 0.22), (0.16, 0.11, 0.08)
# 相手役の手（制服っぽい無地の袖）
SLEEVE, CUFF, HANDC = (0.13, 0.14, 0.24), (0.95, 0.95, 0.95), (0.97, 0.83, 0.72)

# 顔 8×8（上の行から）。H=髪 S=肌 W=白目 E=黒目 M=口 B=まゆ
FACES = {
    "ふつう": ["HHHHHHHH", "HHHHHHHH", "HSSHSSSH", "SSSSSSSS", "SWESSEWS", "SSSSSSSS", "SSSMMSSS", "SSSSSSSS"],
    "きょとん": ["HHHHHHHH", "HHHHHHHH", "HSSHSSSH", "SSSSSSSS", "SSESSESS", "SSSSSSSS", "SSSSMSSS", "SSSSSSSS"],
    "驚き": ["HHHHHHHH", "HHHHHHHH", "HSSHSSSH", "SWWSSWWS", "SWESSEWS", "SSSSSSSS", "SSSMMSSS", "SSSMMSSS"],
    "笑顔": ["HHHHHHHH", "HHHHHHHH", "HSSHSSSH", "SSSSSSSS", "SWESSEWS", "SSSSSSSS", "SSMSSMSS", "SSSMMSSS"],
    "ドヤ": ["HHHHHHHH", "HHHHHHHH", "HBBHSBBH", "SSSSSSSS", "SEESSEES", "SSSSSSSS", "SSSSMMMS", "SSSSSSSS"],
}
FC = {"H": COL["髪"], "S": COL["肌"], "W": EYE_W, "E": EYE_D, "M": MOUTH, "B": BROW}


def lerp(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


def snap(t, t0, d=0.4):
    x = min(1.0, max(0.0, (t - t0) / d)); return 1 - (1 - x) ** 3


# ------------------------------------------------------------------ 僕
def boku(c, m, cx=PX, fy=FY, cz=PZ, face="ふつう", arms="down", legs="stand", wet=False, item=None):
    """頭8×8×8・胴8×4×12・腕4×4×12・脚4×4×12（身長32）。顔は -z 向き。
    arms: down / up / reach（右手を前へ）/ hold（両手を胸の前）/ phone
    legs: stand / run（走る）"""
    k = 0.75 if wet else 1.0
    col = {n: tuple(v * k for v in cc) for n, cc in COL.items()}
    # 脚
    if legs == "run":
        put(c, m, cx - 4, cx, fy + 2, fy + 12, cz - 4, cz, col["ズボン"]); put(c, m, cx - 4, cx, fy, fy + 2, cz - 5, cz - 1, col["靴"])
        put(c, m, cx, cx + 4, fy + 2, fy + 12, cz, cz + 4, col["ズボン"]); put(c, m, cx, cx + 4, fy, fy + 2, cz + 1, cz + 5, col["靴"])
    else:
        put(c, m, cx - 4, cx + 4, fy + 2, fy + 12, cz - 2, cz + 2, col["ズボン"], 1, 0.04)
        put(c, m, cx - 4, cx + 4, fy, fy + 2, cz - 2, cz + 2, col["靴"], 1, 0.02)
        put(c, m, cx - 0.5, cx + 0.5, fy, fy + 10, cz - 2, cz - 1.5, tuple(v * 0.8 for v in col["ズボン"]), 1, 0.0)
    by = fy + 12
    put(c, m, cx - 4, cx + 4, by, by + 12, cz - 2, cz + 2, col["シャツ"], 1, 0.04)        # 胴
    put(c, m, cx - 4, cx + 4, by, by + 1, cz - 2, cz + 2, tuple(v * 0.8 for v in col["シャツ"]), 1, 0.02)
    sy = by + 12                                                                         # 肩の高さ
    for side in (-1, 1):
        x0 = cx - 8 if side < 0 else cx + 4
        a = arms
        if a == "up":
            put(c, m, x0, x0 + 4, sy, sy + 10, cz - 2, cz + 2, col["シャツ"]); put(c, m, x0, x0 + 4, sy + 10, sy + 13, cz - 2, cz + 2, col["肌"])
            band_y = sy + 2
        elif (a == "reach" and side > 0) or a in ("hold", "phone"):
            # 腕を前へ（肘から先が水平）
            put(c, m, x0, x0 + 4, sy - 6, sy, cz - 2, cz + 2, col["シャツ"])
            fx0 = x0 if a == "reach" else (x0 + 1 if side < 0 else x0 - 1)
            yy = sy - 6 if a != "phone" else sy - 4
            put(c, m, fx0, fx0 + 4, yy - 3, yy + 1, cz - 9, cz - 2, col["シャツ"])
            put(c, m, fx0, fx0 + 4, yy - 3, yy + 1, cz - 12, cz - 9, col["肌"])
            band_y = sy - 4
        else:
            put(c, m, x0, x0 + 4, sy - 9, sy, cz - 2, cz + 2, col["シャツ"]); put(c, m, x0, x0 + 4, sy - 12, sy - 9, cz - 2, cz + 2, col["肌"])
            band_y = sy - 4
        if side < 0:  # 左腕（向かって左）に生徒会長の腕章
            put(c, m, x0 - 0.01, x0 + 4, band_y, band_y + 2, cz - 2.2, cz + 2.2, col["腕章"], 1, 0.02)
    hy = sy
    put(c, m, cx - 4, cx + 4, hy, hy + 8, cz - 4, cz + 4, col["肌"], 1, 0.03)            # 頭
    put(c, m, cx - 4, cx + 4, hy + 6, hy + 8, cz - 4, cz + 4, col["髪"], 1, 0.04)        # 髪（上）
    put(c, m, cx - 4, cx + 4, hy + 1, hy + 8, cz + 3, cz + 4, col["髪"], 1, 0.04)        # 後ろ
    put(c, m, cx - 4, cx - 3, hy + 3, hy + 8, cz - 4, cz + 4, col["髪"], 1, 0.04)        # 横
    put(c, m, cx + 3, cx + 4, hy + 3, hy + 8, cz - 4, cz + 4, col["髪"], 1, 0.04)
    put(c, m, cx, cx + 1, hy + 8, hy + 9, cz - 1, cz, col["髪"], 1, 0.04)               # 寝ぐせ1本
    put(c, m, cx - 1, cx, hy + 9, hy + 10, cz - 1, cz, col["髪"], 1, 0.04)
    for r, row in enumerate(FACES[face]):                                                 # 顔
        y = hy + 7 - r
        for i_, ch in enumerate(row):
            x = cx + 3 - i_   # 顔は -z 向きなので、向かって左が +x
            cc = FC[ch]
            cc = tuple(v * k for v in cc) if ch in "HS" else cc
            put(c, m, x, x + 1, y, y + 1, cz - 4, cz - 3, cc, 1, 0.02)
    if item:
        item(c, m)


def hand_in(c, m, p, d, length=16, item=None):
    """相手役の手：p（手の先）から d の向きの反対へ袖がのびる。d は 'x+', 'x-', 'z+' など。"""
    x, y, z = p
    ax, sg = d[0], (1 if d[1] == '+' else -1)
    def box(a0, a1, w, col):  # 手先からの距離 a0〜a1
        lo, hi = sorted((-sg * a0, -sg * a1))
        if ax == 'x':
            put(c, m, x + lo, x + hi, y - w, y + w, z - w, z + w, col, 1, 0.02)
        else:
            put(c, m, x - w, x + w, y - w, y + w, z + lo, z + hi, col, 1, 0.02)
    box(0, 3, 1.5, HANDC); box(3, 5, 1.8, CUFF); box(5, length, 1.8, SLEEVE)
    if item:
        item(c, m)


# ------------------------------------------------------------------ 小物
def ticket(c, m, x, y, z):
    """映画のペアチケット2枚（クリーム色の券、端に赤い帯、点線）"""
    for j, (ox, oz) in enumerate(((0, 0), (2, 2))):
        put(c, m, x - 4 + ox, x + 4 + ox, y + j, y + j + 1, z - 2 + oz, z + 2 + oz, (1.05, 0.98, 0.8), 1, 0.01)
        put(c, m, x + 2 + ox, x + 4 + ox, y + j, y + j + 1, z - 2 + oz, z + 2 + oz, (0.85, 0.15, 0.15), 1, 0.01)
        put(c, m, x + 1 + ox, x + 2 + ox, y + j, y + j + 1, z - 2 + oz, z + 2 + oz, (0.75, 0.7, 0.6), 1, 0.0)


def phone(c, m, x, y, z, frog=False, big=True):
    """スマホ（画面は -z 向き）。frog=True で謎のカエルのスタンプ。big=False は手に持った小さいスマホ"""
    if not big:
        put(c, m, x - 2, x + 2, y, y + 7, z, z + 1, (0.1, 0.1, 0.12), 1, 0.0)
        put(c, m, x - 1, x + 1, y + 1, y + 6, z - 1, z, (0.75, 0.88, 1.1), 4, 0.0)
        return
    put(c, m, x - 5, x + 5, y, y + 16, z, z + 1, (0.1, 0.1, 0.12), 1, 0.0)
    put(c, m, x - 4, x + 4, y + 1, y + 15, z - 1, z, (0.75, 0.88, 1.1), 4, 0.0)
    if frog:
        Fr = ["G.GG.G", "GWGGWG", "GGGGGG", "GRRRRG", ".GGGG."]
        for r, row in enumerate(Fr):
            for i_, ch in enumerate(row):
                cc = {"G": (0.25, 0.85, 0.3), "W": (0.05, 0.05, 0.05), "R": (0.9, 0.3, 0.35)}.get(ch)
                if cc:
                    put(c, m, x + 2 - i_, x + 3 - i_, y + 11 - r, y + 12 - r, z - 1, z, cc, 4, 0.0)
        put(c, m, x - 3, x + 3, y + 3, y + 5, z - 1, z, (0.3, 0.6, 1.1), 4, 0.0)   # 吹き出しの帯
    else:   # トーク画面（グループのメッセージ）
        for j, (a, b_, cc) in enumerate(((-3, 1, (1.0, 1.0, 1.0)), (-1, 3, (0.4, 0.9, 0.45)), (-3, 0, (1.0, 1.0, 1.0)), (-1, 3, (0.4, 0.9, 0.45)))):
            put(c, m, x - b_, x - a, y + 12 - j * 3, y + 14 - j * 3, z - 1.5, z - 0.5, cc, 4, 0.0)


def bento(c, m, x, y, z):
    put(c, m, x - 6, x + 6, y, y + 3, z - 4, z + 4, (0.15, 0.1, 0.1), 1, 0.0)
    put(c, m, x - 5, x, y + 2, y + 3.2, z - 3, z + 3, (1.0, 1.0, 0.95), 1, 0.02)          # ごはん
    put(c, m, x + 1, x + 5, y + 2, y + 3.4, z - 3, z, (1.1, 0.85, 0.2), 1, 0.02)          # 卵焼き
    put(c, m, x + 1, x + 5, y + 2, y + 3.0, z + 1, z + 3, (0.3, 0.6, 0.25), 1, 0.05)      # 野菜
    put(c, m, x - 1, x + 1, y + 3, y + 6, z - 1, z + 1, (1.25, 0.25, 0.2), 4, 0.0)        # たこさんウインナー
    for dx, dz in ((-1.5, 0), (1.5, 0), (0, -1.5), (0, 1.5)):
        put(c, m, x + dx - 0.5, x + dx + 0.5, y + 2.5, y + 3.5, z + dz - 0.5, z + dz + 0.5, (1.25, 0.25, 0.2), 4, 0.0)


def breads(c, m, x, y, z):
    for i_ in range(3):
        put(c, m, x - 5 + i_ * 3.5, x - 2 + i_ * 3.5, y + i_ % 2, y + 3 + i_ % 2, z - 3, z, (0.95, 0.72, 0.4), 1, 0.05)
        put(c, m, x - 5 + i_ * 3.5, x - 2 + i_ * 3.5, y + 3 + i_ % 2, y + 3.3 + i_ % 2, z - 3, z, (0.9, 0.9, 1.0), 1, 0.0)


def umbrella(c, m, x, y, z, open_=False, horiz=False):
    if horiz:   # 前へ差し出す（-z 向き）
        put(c, m, x - 1, x + 1, y - 1, y + 1, z - 14, z, (0.2, 0.35, 0.85), 1, 0.03)
        put(c, m, x - 0.5, x + 0.5, y - 0.5, y + 0.5, z - 16, z - 14, (0.3, 0.3, 0.3), 1, 0.0)
        return
    if open_:
        for r in range(6):
            put(c, m, x - 10 + r * 1.6, x + 10 - r * 1.6, y + r, y + r + 1, z - 10 + r * 1.6, z + 10 - r * 1.6, (0.2, 0.35, 0.85), 1, 0.03)
        put(c, m, x - 0.5, x + 0.5, y - 14, y, z - 0.5, z + 0.5, (0.3, 0.3, 0.3), 1, 0.0)
    else:
        put(c, m, x - 1, x + 1, y, y + 14, z - 1, z + 1, (0.2, 0.35, 0.85), 1, 0.03)
        put(c, m, x - 0.5, x + 0.5, y - 2, y, z - 0.5, z + 0.5, (0.35, 0.25, 0.2), 1, 0.0)


def bubble(c, m, x, y, z):
    """考えごとの吹き出し：無人島・ナイフ・魚（正面から見て左に島、右にナイフと魚）"""
    _p = globals()["put"]
    def put(c, m, x0, x1, *a):  # 左右を反転（正面から見たときの並び）
        _p(c, m, 2 * x - x1, 2 * x - x0, *a)
    put(c, m, x - 13, x + 13, y, y + 16, z, z + 1, (1.2, 1.2, 1.2), 4, 0.0)
    for i_, (bx, by_, s) in enumerate(((x - 6, y - 3, 2), (x - 9, y - 6, 1.4))):
        put(c, m, bx - s, bx + s, by_ - s, by_ + s, z, z + 1, (1.2, 1.2, 1.2), 4, 0.0)
    put(c, m, x - 11, x + 11, y + 2, y + 4, z - 0.3, z, (0.4, 0.75, 1.2), 4, 0.0)         # 海
    put(c, m, x - 9, x - 1, y + 4, y + 6, z - 0.3, z, (1.3, 1.1, 0.6), 4, 0.0)            # 島
    put(c, m, x - 6, x - 5, y + 6, y + 12, z - 0.3, z, (0.5, 0.33, 0.2), 4, 0.0)          # ヤシの木
    put(c, m, x - 9, x - 2, y + 12, y + 13, z - 0.3, z, (0.3, 0.8, 0.3), 4, 0.0)
    put(c, m, x + 1, x + 7, y + 9, y + 10.5, z - 0.3, z, (0.85, 0.88, 0.95), 4, 0.0)      # ナイフ
    put(c, m, x + 7, x + 10, y + 9, y + 10.5, z - 0.3, z, (0.5, 0.3, 0.15), 4, 0.0)
    put(c, m, x + 2, x + 8, y + 5, y + 7.5, z - 0.3, z, (0.3, 0.55, 1.2), 4, 0.0)         # 魚
    put(c, m, x + 8, x + 10, y + 4.5, y + 8, z - 0.3, z, (0.3, 0.55, 1.2), 4, 0.0)


def qmarks(c, m, x, y, z, n=3, t=0.0, col=(1.25, 0.82, 0.12)):
    Q = ["0110", "1001", "0001", "0010", "0100", "0000", "0100"]
    for q in range(n):
        ox = x + (q - (n - 1) / 2) * 7; oy = y + 1.2 * math.sin(t * 4 + q)
        for r, row in enumerate(Q):
            for k, ch in enumerate(row):
                if ch == "1":
                    put(c, m, ox + 2 - k, ox + 3 - k, oy + 7 - r, oy + 8 - r, z, z + 1, col, 4, 0.0)


def chalk_text(c, m, x, y, z0, text):
    """黒板（x の壁）にチョークの数字。z0 から +z 方向へ書く"""
    G = {"1": ["010", "110", "010", "010", "111"], "8": ["111", "101", "111", "101", "111"], "/": ["001", "001", "010", "100", "100"],
         "0": ["111", "101", "101", "101", "111"], "9": ["111", "101", "111", "001", "111"]}
    zz = z0   # +x 側から見ると -z が右なので、z を減らしながら書く
    for ch in text:
        for r, row in enumerate(G[ch]):
            for i_, b in enumerate(row):
                if b == "1":
                    put(c, m, x, x + 1, y + 4 - r, y + 5 - r, zz - i_, zz - i_ + 1, (1.2, 1.2, 1.15), 4, 0.0)
        zz -= 4


# ------------------------------------------------------------------ 舞台
def sunset_sky(d):
    y = np.clip(d[:, 1], -0.2, 1)
    t_ = np.clip(y / 0.5, 0, 1)
    return (C(1.35, 0.7, 0.35) * (1 - t_[:, None]) + C(0.35, 0.3, 0.6) * t_[:, None]).astype(f32)


def build_room():
    """夕方の生徒会室"""
    S = Scene(110, 64, 110)
    c, m = S.col, S.mat
    put(c, m, 0, 110, 0, FY, 0, 110, (0.55, 0.38, 0.22), 1, 0.06)
    for z in range(0, 110, 5):
        put(c, m, 0, 110, FY - 1, FY, z, z + 1, (0.46, 0.31, 0.18), 1, 0.03)
    put(c, m, 0, 110, FY, 60, 104, 106, (0.92, 0.9, 0.86), 1, 0.03)                 # 奥の壁
    put(c, m, 2, 4, FY, 60, 0, 106, (0.9, 0.88, 0.84), 1, 0.03)                    # 左の壁
    put(c, m, 106, 108, FY, 60, 0, 106, (0.9, 0.88, 0.84), 1, 0.03)                # 右の壁
    m[16:94, FY + 14:FY + 48, 104:106] = 0                                         # 大きな窓
    for x in range(16, 95, 13):
        put(c, m, x, x + 2, FY + 14, FY + 48, 104, 106, (0.45, 0.3, 0.2), 1, 0.0)
    put(c, m, 16, 94, FY + 30, FY + 32, 104, 106, (0.45, 0.3, 0.2), 1, 0.0)
    put(c, m, 4, 5, FY + 16, FY + 38, 30, 80, (0.12, 0.25, 0.18), 1, 0.04)          # 黒板
    put(c, m, 4, 6, FY + 15, FY + 16, 30, 80, (0.6, 0.45, 0.3), 1, 0.0)
    put(c, m, 98, 106, FY, FY + 34, 20, 50, (0.5, 0.33, 0.2), 1, 0.05)              # 本棚
    for y in range(FY + 3, FY + 33, 7):
        for z in range(21, 49, 2):
            put(c, m, 98, 99, y, y + 5, z, z + 1.6, [(0.8, 0.2, 0.2), (0.2, 0.45, 0.85), (0.9, 0.75, 0.2), (0.3, 0.65, 0.35)][(y + z) % 4], 1, 0.03)
    put(c, m, 98, 106, FY + 40, FY + 46, 70, 88, (0.55, 0.38, 0.22), 1, 0.03)      # 右の壁のドア枠
    put(c, m, 105, 106, FY, FY + 40, 72, 86, (0.6, 0.42, 0.26), 1, 0.03)           # ドア
    put(c, m, 30, 80, FY + 14, FY + 15, 74, 92, (0.62, 0.42, 0.25), 1, 0.04)       # 長机
    for x in (31, 78):
        for z in (75, 90):
            put(c, m, x, x + 1, FY, FY + 14, z, z + 1, (0.4, 0.27, 0.16), 1, 0.0)
    put(c, m, 46, 58, FY + 15, FY + 16, 80, 86, (0.95, 0.95, 0.95), 1, 0.0)
    put(c, m, 70, 76, FY + 15, FY + 21, 84, 86, (0.3, 0.3, 0.32), 1, 0.0)           # ペン立て
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sky = sunset_sky
    S.sun = np.array([0.1, 0.35, 0.93]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.3, 0.8, 0.5); S.amb = C(0.55, 0.5, 0.55)
    S.lights = [((55, FY + 50, 40), (0.55, 0.5, 0.45), 70)]
    S.fog0, S.fogk = 300, 500
    return S


def build_hall():
    """昼の廊下：左に窓、右に教室のドア"""
    S = Scene(110, 64, 110)
    c, m = S.col, S.mat
    put(c, m, 0, 110, 0, FY, 0, 110, (0.7, 0.72, 0.74), 1, 0.04)
    for z in range(0, 110, 8):
        put(c, m, 0, 110, FY - 1, FY, z, z + 1, (0.6, 0.62, 0.64), 1, 0.02)
    put(c, m, 30, 32, FY, 56, 0, 110, (0.92, 0.92, 0.9), 1, 0.03)                  # 左の壁（窓）
    for z in range(4, 100, 16):
        m[30:32, FY + 14:FY + 40, z:z + 12] = 0
    put(c, m, 30, 82, FY, 56, 104, 106, (0.9, 0.9, 0.88), 1, 0.03)                 # 突き当たりの壁
    m[46:66, FY + 18:FY + 40, 104:106] = 0
    put(c, m, 80, 82, FY, 56, 0, 110, (0.9, 0.88, 0.84), 1, 0.03)                  # 右の壁
    for z in (20, 70):
        put(c, m, 79, 80, FY, FY + 38, z, z + 16, (0.6, 0.45, 0.3), 1, 0.03)         # ドア
        put(c, m, 78.6, 79, FY + 22, FY + 32, z + 3, z + 13, (0.6, 0.75, 0.9), 3, 0.0)
    put(c, m, 30, 82, 56, 58, 0, 110, (0.95, 0.95, 0.95), 1, 0.02)                 # 天井
    for z in range(10, 110, 25):
        put(c, m, 50, 62, 55, 56, z, z + 3, (1.4, 1.4, 1.3), 4, 0.0)
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = np.array([-0.75, 0.45, 0.2]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.2, 1.1, 0.95); S.amb = C(0.7, 0.72, 0.78)
    S.hor = C(0.85, 0.92, 1.0); S.top = C(0.45, 0.65, 0.95)
    S.lights = []; S.fog0, S.fogk = 200, 400
    return S


def build_entrance():
    """雨の昇降口"""
    S = Scene(110, 64, 110)
    c, m = S.col, S.mat
    put(c, m, 0, 110, 0, FY, 0, 110, (0.62, 0.62, 0.64), 1, 0.05)
    put(c, m, 0, 110, FY, 52, 0, 2, (0.88, 0.88, 0.86), 1, 0.03)
    for x in (8, 22, 80, 94):
        put(c, m, x, x + 10, FY, FY + 30, 4, 22, (0.6, 0.45, 0.3), 1, 0.04)          # げた箱
        for y in range(FY + 3, FY + 30, 6):
            put(c, m, x, x + 10, y, y + 1, 3.5, 22, (0.45, 0.32, 0.2), 1, 0.0)
    for x in range(13, 100, 18):                                                    # ガラス戸
        put(c, m, x, x + 2, FY, FY + 38, 84, 86, (0.35, 0.35, 0.38), 1, 0.0)
    put(c, m, 13, 99, FY + 38, FY + 41, 84, 86, (0.35, 0.35, 0.38), 1, 0.0)
    put(c, m, 0, 110, FY + 41, 52, 84, 86, (0.88, 0.88, 0.86), 1, 0.03)
    put(c, m, 0, 110, 0, FY - 0.5, 86, 110, (0.3, 0.3, 0.33), 1, 0.05)
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = None; S.amb = C(0.62, 0.64, 0.7)
    S.lights = [((55, FY + 45, 40), (0.65, 0.65, 0.65), 60)]
    S.hor = C(0.55, 0.58, 0.62); S.top = C(0.42, 0.45, 0.5); S.fog0, S.fogk = 90, 160
    return S


def build_outside():
    """夕日の校舎"""
    S = Scene(140, 80, 160)
    c, m = S.col, S.mat
    put(c, m, 0, 140, 0, 2, 0, 160, (0.33, 0.55, 0.25), 1, 0.08)
    put(c, m, 15, 125, 2, 50, 90, 115, (0.93, 0.9, 0.84), 1, 0.03)
    for y in range(8, 48, 11):
        for x in range(20, 122, 11):
            lit = (x == 64 and y == 30)
            put(c, m, x, x + 7, y, y + 7, 89, 90, (1.6, 1.2, 0.6) if lit else (0.4, 0.5, 0.65), 4 if lit else 3, 0.0)
    put(c, m, 60, 80, 50, 66, 98, 108, (0.93, 0.9, 0.84), 1, 0.03)
    put(c, m, 65, 75, 54, 63, 97, 98, (0.95, 0.95, 0.9), 1, 0.0)
    put(c, m, 69.5, 70.5, 58, 62, 96.5, 97, (0.1, 0.1, 0.1), 1, 0.0)
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sky = sunset_sky
    S.sun = np.array([0.45, 0.45, -0.77]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.3, 0.75, 0.45); S.amb = C(0.5, 0.45, 0.55); S.lights = []
    S.fog0, S.fogk = 200, 400
    return S


_S = {}


def get(k):
    if k not in _S:
        _S[k] = {"room": build_room, "hall": build_hall, "ent": build_entrance, "out": build_outside}[k]()
    return _S[k]


def rain(img, depth, cam, tgt, fov, t, box, n=900, sp=60):
    rg = np.random.default_rng(3)
    x0, x1, y0, y1, z0, z1 = box
    p = np.stack([rg.uniform(x0, x1, n), (rg.uniform(0, 1, n) * (y1 - y0) - sp * t) % (y1 - y0) + y0, rg.uniform(z0, z1, n)], 1)
    for kk in range(3):
        particles(img, depth, cam, tgt, fov, p + np.array([0, kk * 0.8, 0]), np.tile(C(0.85, 0.9, 1.0) * (1 - kk / 3), (n, 1)), 0.12)


def roll(img, deg, zoom=1.12):
    """ななめの画角（ダッチアングル）"""
    if abs(deg) < 0.01:
        return img
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    w, h = im.size
    im = im.rotate(deg, resample=Image.BICUBIC).resize((int(w * zoom), int(h * zoom)), Image.BICUBIC)
    l, t = (im.size[0] - w) // 2, (im.size[1] - h) // 2
    return np.asarray(im.crop((l, t, l + w, t + h))).astype(f32) / 255


# ------------------------------------------------------------------ カメラの決まった位置
FACEP = (PX, EYE_Y - 0.5, PZ - 4)               # 顔の前


def face_cam(dist, side=0.0, up=0.0, aim=1.4):
    """顔のアップ。aim>0 で注視点を顔より上にして、顔を画面のやや下（字幕とタイトルの間）に置く"""
    dist = dist + 12   # 顔が画面の幅の半分くらいになる距離
    return ((PX + side, EYE_Y + up, PZ - 4 - dist), (PX + side * 0.2, EYE_Y + aim, PZ))


def pov_her(dist_k=0.0):
    """相手役の目線（少し低め＝見上げる）"""
    cam = lerp((HER[0], EYE_Y - 2, HER[1]), (PX + 3, EYE_Y - 1, PZ - 16), dist_k)
    return cam, (PX, EYE_Y + 1.5, PZ)


def ots_her():
    """相手役の肩ごし：手前に相手役の手、奥に僕"""
    return (HER[0] + 6, EYE_Y + 2, HER[1] - 10), (PX - 1, EYE_Y - 4, PZ)


def high_wide(a=0.0):
    """俯瞰（上から部屋ごと）"""
    return (PX + 30 * math.sin(a) + 5, FY + 58, PZ - 30 * math.cos(a) - 10), (PX, FY + 10, PZ + 4)


def low_up(a=0.0):
    """あおり（下から見上げる）"""
    return (PX + 10 * math.sin(a), FY + 4, PZ - 22 - 4 * math.cos(a)), (PX, EYE_Y + 6, PZ)


# ------------------------------------------------------------------ 場面ごとのカット
def shoot(set_, cam, tgt, fov, draw, grade=(1, 1, 1), rain_on=False, t=0.0, dutch=0.0, sh=0.0):
    S = get(set_)
    c, m = S.base_c.copy(), S.base_m.copy()
    draw(c, m)
    if sh > 0:
        cam, tgt = shake(cam, tgt, sh, t)
    img, depth = render(S, c, m, cam, tgt, fov, W // RS, H // RS)
    if rain_on:
        rain(img, depth, cam, tgt, fov, t, (0, 110, FY, 62, 0, 110))
    img = roll(img, dutch)
    return finish(img, grade=grade)


def cut(t, T, marks):
    """marks（割合）で区切ったカット番号と、そのカット内の 0→1"""
    b = [0] + [x * T for x in marks] + [T]
    for i in range(len(b) - 1):
        if t < b[i + 1] or i == len(b) - 2:
            return i, min(1.0, (t - b[i]) / max(1e-3, b[i + 1] - b[i]))


def frame(k, t):
    T = CLIPS[k]
    B = lambda **kw: (lambda c, m: boku(c, m, **kw))
    if k == 0:   # 目を覚ます → 一気に引く（俯瞰）→ 顔へ戻る
        i, u = cut(t, T, [0.45, 0.75])
        if i == 0:
            cam, tgt = face_cam(14 + 50 * snap(u, 0.35, 0.6), up=26 * snap(u, 0.35, 0.6), aim=1.4 - 20 * snap(u, 0.35, 0.6))
            return shoot("room", cam, tgt, 40 + 20 * snap(u, 0.35, 0.6), B(face="きょとん" if u < 0.35 else "驚き", arms="down"), t=t)
        if i == 1:
            a = -0.5 + 0.8 * ease(u)
            cam, tgt = high_wide(a)
            return shoot("room", cam, tgt, 64, B(face="驚き", arms="up"), t=t)
        cam, tgt = face_cam(30 - 12 * ease(u), side=-6 * (1 - u))
        return shoot("room", cam, tgt, 46, B(face="驚き", arms="down"), t=t, dutch=-6)
    if k == 1:   # ルール：あおりで「負け」→ 横顔
        i, u = cut(t, T, [0.5])
        if i == 0:
            cam, tgt = low_up(0.4 - 0.6 * u)
            return shoot("room", cam, tgt, 64, B(face="きょとん"), t=t, dutch=5)
        cam = (PX - 20 + 4 * u, EYE_Y + 2, PZ - 30); tgt = (PX, EYE_Y + 1.5, PZ)
        return shoot("room", cam, tgt, 44 - 6 * u, B(face="きょとん"), t=t)
    if k == 2:   # 相手は天才：机の上の書類ごしに → 相手役の目線で見下ろす → 僕「へー」
        i, u = cut(t, T, [0.35, 0.7])
        if i == 0:
            cam = (PX + 20 - 30 * ease(u), FY + 18, PZ + 40); tgt = (PX, FY + 16, PZ + 10)
            return shoot("room", cam, tgt, 58, B(face="ふつう"), t=t)
        if i == 1:
            cam, tgt = pov_her(0.6 * ease(u))
            return shoot("room", cam, tgt, 50, B(face="きょとん", item=lambda c, m: qmarks(c, m, PX, FY + 38, PZ, 3, t)), t=t)
        cam, tgt = face_cam(20 - 4 * u, side=3)
        return shoot("room", cam, tgt, 44, B(face="笑顔"), t=t)
    if k == 3:   # 映画チケット：肩ごしに手が入る → チケットの超アップ
        i, u = cut(t, T, [0.55])
        hz = PZ - 30 + 14 * snap(u, 0.1, 0.6)
        hand = lambda c, m: hand_in(c, m, (PX + 3, FY + 22, hz), 'z+', 20, lambda c2, m2: ticket(c2, m2, PX + 2, FY + 23.5, hz + 1))
        draw = lambda c, m: (boku(c, m, face="ふつう"), hand(c, m))
        if i == 0:
            cam, tgt = ots_her()
            return shoot("room", cam, tgt, 54, draw, t=t)
        cam = (PX + 26 - 4 * u, FY + 27, hz - 4); tgt = (PX + 2, FY + 24, hz + 1)
        return shoot("room", cam, tgt, 38 - 8 * ease(u), draw, t=t)
    if k == 4:   # 「弟と行ってきます！」：ジャンプ → 一気に引く
        i, u = cut(t, T, [0.45])
        held = lambda c, m: ticket(c, m, PX + 6, FY + 41, PZ)
        if i == 0:
            cam, tgt = face_cam(18, side=-4, aim=2.5)
            return shoot("room", cam, tgt, 48, B(face="笑顔", arms="up", item=held), t=t, sh=0.4)
        cam, tgt = lerp(face_cam(18), high_wide(0.6), snap(u, 0, 0.5)) if False else (lerp((PX, EYE_Y, PZ - 22), (PX + 34, FY + 56, PZ - 44), snap(u, 0, 0.6)), lerp((PX, EYE_Y + 1, PZ), (PX, FY + 10, PZ + 6), snap(u, 0, 0.6)))
        return shoot("room", cam, tgt, 46 + 18 * snap(u, 0, 0.6), B(face="笑顔", arms="up", item=held), t=t)
    if k == 5:   # 連絡先：廊下。相手役の目線 → スマホのアップ → 俯瞰
        i, u = cut(t, T, [0.4, 0.75])
        draw = B(face="ふつう", arms="phone", item=lambda c, m: phone(c, m, PX + 2, FY + 16, PZ - 13, big=False))
        if i == 0:
            cam, tgt = (PX + 8, EYE_Y - 2, PZ - 48 + 12 * ease(u)), (PX, EYE_Y + 1, PZ)
            return shoot("hall", cam, tgt, 50, draw, t=t)
        if i == 1:
            draw = B(face="ふつう", arms="phone", item=lambda c, m: phone(c, m, PX + 2, FY + 18, PZ - 12))
            cam = (PX - 2 + 4 * u, FY + 27, PZ - 44); tgt = (PX + 2, FY + 26, PZ - 12)
            return shoot("hall", cam, tgt, 34, draw, t=t)
        cam, tgt = (PX + 14, FY + 54, PZ - 24 - 8 * u), (PX, FY + 12, PZ + 4)
        return shoot("hall", cam, tgt, 60, draw, t=t)
    if k == 6:   # 「グループ、もう入ってますよ！」：ドヤ顔アップ → 横から
        i, u = cut(t, T, [0.5])
        draw = B(face="ドヤ", arms="phone", item=lambda c, m: phone(c, m, PX + 2, FY + 16, PZ - 13, big=False))
        if i == 0:
            cam, tgt = face_cam(22 - 8 * ease(u), side=5)
            return shoot("hall", cam, tgt, 42, draw, t=t)
        cam = (PX + 20, EYE_Y - 2, PZ - 30 + 6 * u); tgt = (PX, EYE_Y - 2, PZ - 4)
        return shoot("hall", cam, tgt, 46, draw, t=t, dutch=-4)
    if k == 7:   # 届いたのはカエルのスタンプ：画面の超アップ → 引く
        draw = B(face="笑顔", arms="phone", item=lambda c, m: phone(c, m, PX + 2, FY + 18, PZ - 12, frog=True))
        z = snap(t, T * 0.5, 0.6)
        cam = lerp((PX + 2, FY + 25, PZ - 46), (PX + 4, EYE_Y, PZ - 56), z); tgt = lerp((PX + 2, FY + 23, PZ - 12), (PX, EYE_Y - 4, PZ), z)
        return shoot("hall", cam, tgt, 30 + 26 * z, draw, t=t)
    if k == 8:   # お弁当：真上からお弁当 → 相手役の手がお弁当を差し出す → 僕の顔
        i, u = cut(t, T, [0.4, 0.75])
        bz = PZ - 14
        hand = lambda c, m: hand_in(c, m, (PX + 6, FY + 19, bz + 4), 'x-', 18, lambda c2, m2: bento(c2, m2, PX + 1, FY + 18, bz))
        draw = lambda c, m: (boku(c, m, face="きょとん"), hand(c, m))
        if i == 0:
            cam = (PX + 1 + 3 * u, FY + 44 - 8 * ease(u), bz - 1); tgt = (PX + 1, FY + 18, bz)
            return shoot("room", cam, tgt, 40, draw, t=t)
        if i == 1:
            cam, tgt = (PX + 22, FY + 26, bz - 26 + 4 * u), (PX + 1, FY + 20, bz + 4)
            return shoot("room", cam, tgt, 48, draw, t=t)
        cam, tgt = face_cam(16 + 4 * u, side=-3)
        return shoot("room", cam, tgt, 44, draw, t=t)
    if k == 9:   # パン3個：あおりでパンを掲げる → 一気に引く
        i, u = cut(t, T, [0.5])
        held = lambda c, m: breads(c, m, PX + 3, FY + 40, PZ - 2)
        if i == 0:
            cam, tgt = low_up(-0.3 + 0.3 * u)
            return shoot("room", cam, tgt, 60, B(face="笑顔", arms="up", item=held), t=t, dutch=6)
        z = snap(u, 0, 0.5)
        cam = lerp((PX, EYE_Y, PZ - 20), (PX - 30, FY + 50, PZ - 40), z); tgt = lerp((PX, EYE_Y + 3, PZ), (PX, FY + 12, PZ + 6), z)
        return shoot("room", cam, tgt, 48 + 14 * z, B(face="笑顔", arms="up", item=held), t=t)
    if k == 10:  # 大雨の昇降口：外から雨ごし → 相手役の目線
        i, u = cut(t, T, [0.45])
        draw = B(face="ふつう", item=lambda c, m: umbrella(c, m, PX + 8, FY + 10, PZ))
        if i == 0:
            cam, tgt = (PX + 20 - 20 * ease(u), FY + 20, 104), (PX, FY + 20, PZ)
            return shoot("ent", cam, tgt, 56, draw, rain_on=True, t=t, grade=(0.92, 0.96, 1.05))
        cam, tgt = pov_her(0.3 + 0.3 * u)
        return shoot("ent", cam, tgt, 50, draw, rain_on=True, t=t, grade=(0.92, 0.96, 1.05))
    if k == 11:  # 傘を押しつける → 雨の中へダッシュ（後ろ姿・俯瞰）
        i, u = cut(t, T, [0.45])
        if i == 0:
            draw = lambda c, m: boku(c, m, face="笑顔", arms="reach", item=lambda c2, m2: umbrella(c2, m2, PX + 6, FY + 19, PZ - 12, horiz=True))
            cam, tgt = ots_her()
            return shoot("ent", cam, tgt, 52, draw, rain_on=True, t=t, grade=(0.92, 0.96, 1.05))
        pz = PZ + 50 * ease(u)
        draw = lambda c, m: (umbrella(c, m, HER[0] - 4, FY + 20, HER[1] + 6), boku(c, m, cz=int(pz), face="笑顔", legs="run" if int(t * 8) % 2 else "stand"))
        cam, tgt = (PX + 10, FY + 46, PZ - 30), (PX, FY + 10, pz)
        return shoot("ent", cam, tgt, 56, draw, rain_on=True, t=t, grade=(0.92, 0.96, 1.05))
    if k == 12:  # ずぶぬれでくしゃみ
        i, u = cut(t, T, [0.5])
        draw = B(face="きょとん" if i == 0 else "驚き", wet=True)
        if i == 0:
            cam, tgt = (PX - 10, FY + 40, PZ - 40 + 10 * u), (PX, FY + 16, PZ)
            return shoot("ent", cam, tgt, 52, draw, rain_on=True, t=t, grade=(0.85, 0.92, 1.1))
        cam, tgt = face_cam(16, side=2)
        return shoot("ent", cam, tgt, 46, draw, rain_on=True, t=t, grade=(0.85, 0.92, 1.1), sh=0.8 * max(0, 1 - u * 2))
    if k == 13:  # 次の日：校舎 → 相手役の目線で「何か気づきません？」
        i, u = cut(t, T, [0.4])
        if i == 0:
            S_ = get("out")
            cam = (70, 14 + 6 * u, 20 - 12 * u); tgt = (70, 34, 100)
            img, _ = render(S_, S_.base_c, S_.base_m, cam, tgt, 62, W // RS, H // RS)
            return finish(img)
        cam, tgt = pov_her(0.5 * ease(u))
        return shoot("room", cam, tgt, 48, B(face="きょとん", item=lambda c, m: qmarks(c, m, PX, FY + 38, PZ, 1, t)), t=t)
    if k == 14:  # 「黒板の日付、まちがってますね！」：指さし → 黒板のアップ
        i, u = cut(t, T, [0.5])
        board = lambda c, m: chalk_text(c, m, 5, FY + 28, 60, "11/8")
        draw = lambda c, m: (board(c, m), boku(c, m, face="驚き", arms="reach"))
        if i == 0:
            cam, tgt = (PX + 30, EYE_Y, PZ - 26 + 6 * u), (PX - 4, EYE_Y - 2, PZ)
            return shoot("room", cam, tgt, 52, draw, t=t)
        cam = (52 - 10 * ease(u), FY + 31, 53); tgt = (5, FY + 30, 53)
        return shoot("room", cam, tgt, 46, draw, t=t)
    if k == 15:  # 心理テスト：顔へゆっくり寄る（ななめ）
        i, u = cut(t, T, [0.55])
        if i == 0:
            cam, tgt = pov_her(0.2 + 0.4 * u)
            return shoot("room", cam, tgt, 48, B(face="ふつう"), t=t, dutch=-5)
        cam, tgt = face_cam(24 - 8 * ease(u))
        return shoot("room", cam, tgt, 42, B(face="きょとん"), t=t)
    if k == 16:  # 「好きな人の名前を…」：考えごとの吹き出しがふくらむ
        i, u = cut(t, T, [0.4])
        if i == 0:
            cam = (PX + 18 - 4 * u, EYE_Y + 3, PZ - 30); tgt = (PX, EYE_Y + 1.5, PZ)
            return shoot("room", cam, tgt, 42, B(face="きょとん"), t=t)
        bub = lambda c, m: bubble(c, m, PX + 17, FY + 26, PZ - 6)
        cam, tgt = (PX + 9, EYE_Y + 2, PZ - 62 + 10 * ease(u)), (PX + 9, EYE_Y + 3, PZ)
        return shoot("room", cam, tgt, 50, B(face="ドヤ", item=bub), t=t)
    if k == 17:  # 「ナイフですね」→「もう知りません！」：ドアがバタン、画面が揺れる
        i, u = cut(t, T, [0.5])
        if i == 0:
            cam, tgt = face_cam(16 - 3 * u, side=-2)
            return shoot("room", cam, tgt, 44, B(face="ドヤ"), t=t)
        door = snap(u, 0.1, 0.25)
        def draw(c, m):
            boku(c, m, face="驚き")
            if door < 1:
                put(c, m, 92, 105, FY, FY + 40, 72, 73, (0.6, 0.42, 0.26), 1, 0.03)   # 開いていたドアが閉まる
        cam, tgt = (PX - 25, FY + 34, PZ - 34), (PX + 18, FY + 22, PZ + 12)
        return shoot("room", cam, tgt, 62, draw, t=t, sh=1.4 * max(0, 1 - u * 2.5) if u > 0.1 else 0)
    if k == 18:  # 0勝6敗：真上からぐるっと → 一人ぽつんと
        a = 0.3 + 1.2 * ease(t / T)
        cam, tgt = (PX + 40 * math.sin(a), FY + 62, PZ - 40 * math.cos(a)), (PX, FY, PZ)
        return shoot("room", cam, tgt, 56, B(face="きょとん", item=lambda c, m: qmarks(c, m, PX, FY + 38, PZ, 1, t)), t=t)
    if k == 19:  # 最後：顔のアップ → 校舎まで引く
        i, u = cut(t, T, [0.45])
        if i == 0:
            cam, tgt = face_cam(15 + 4 * u)
            return shoot("room", cam, tgt, 44, B(face="ドヤ"), t=t)
        S_ = get("out")
        cam = lerp((70, 20, 40), (70, 30, -10), ease(u)); tgt = (70, 34, 100)
        img, _ = render(S_, S_.base_c, S_.base_m, cam, tgt, 62, W // RS, H // RS)
        return finish(img)


# ------------------------------------------------------------------ デザイン定義シート
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


def F(sz):
    return ImageFont.truetype(FONT, sz)


def studio(draw, cam, tgt, fov, w, h, bg=(0.93, 0.94, 0.97)):
    S = Scene(110, 64, 110)
    S.sky = lambda d: np.tile(C(*bg), (len(d), 1)).astype(f32)
    S.sun = np.array([-0.4, 0.6, -0.7]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(0.75, 0.75, 0.75); S.amb = C(0.62, 0.62, 0.65); S.lights = []; S.fog0, S.fogk = 999, 999
    c, m = S.col, S.mat
    draw(c, m)
    img, _ = render(S, c, m, cam, tgt, fov, w, h)
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))


def hexs(col):
    return "#%02x%02x%02x" % tuple(int(min(1, v) * 255) for v in col)


def face_tile(name, px=29):
    im = Image.new("RGB", (8 * px, 8 * px))
    d = ImageDraw.Draw(im)
    for r, row in enumerate(FACES[name]):
        for i_, ch in enumerate(row):
            d.rectangle([i_ * px, r * px, i_ * px + px - 1, r * px + px - 1], fill=tuple(int(min(1, v) * 255) for v in FC[ch]))
    return im


def sheet_base(title, sub):
    im = Image.new("RGB", (2000, 1250), (249, 249, 251)); d = ImageDraw.Draw(im)
    d.text((50, 40), title, font=F(72), fill=(20, 20, 30))
    d.text((50 + d.textlength(title, font=F(72)) + 30, 66), sub, font=F(38), fill=(80, 85, 100))
    return im, d


def sheets():
    # ---- 1枚目：僕 ----
    im, d = sheet_base("僕", "主人公・生徒会長の役（中身はふつうの頭）")
    tgt = (PX, FY + 17, PZ); views = [("正面", 0.0), ("斜め", -0.6), ("横", -math.pi / 2), ("後ろ", math.pi)]
    for i_, (nm, a) in enumerate(views):
        cam = (PX + 120 * math.sin(a), FY + 20, PZ - 120 * math.cos(a))
        v = studio(lambda c, m: boku(c, m, face="ふつう"), cam, tgt, 17, 300, 450, (0.94, 0.95, 0.98))
        x = 50 + i_ * 317; im.paste(v, (x, 142))
        d.text((x + 150, 625), nm, font=F(30), fill=(40, 45, 60), anchor="mm")
    d.text((50, 670), "表情", font=F(40), fill=(20, 20, 30))
    for i_, nm in enumerate(FACES):
        x = 50 + i_ * 250; im.paste(face_tile(nm), (x, 725))
        d.text((x + 116, 990), nm, font=F(30), fill=(40, 45, 60), anchor="mm")
    d.text((1350, 150), "色", font=F(40), fill=(20, 20, 30))
    for i_, (nm, cc) in enumerate(COL.items()):
        y = 205 + i_ * 58
        d.rounded_rectangle([1350, y, 1395, y + 45], 6, fill=tuple(int(min(1, v) * 255) for v in cc), outline=(200, 200, 210))
        d.text((1415, y + 5), nm, font=F(30), fill=(30, 30, 40)); d.text((1600, y + 8), hexs(cc), font=F(26), fill=(90, 95, 110))
    d.text((1350, 590), "寸法", font=F(40), fill=(20, 20, 30))
    for i_, s in enumerate(["頭 8×8×8", "胴 8×4×12", "腕 4×4×12", "脚 4×4×12", "身長 32ドット＋寝ぐせ"]):
        d.text((1350, 645 + i_ * 38), s, font=F(26), fill=(60, 65, 80))
    d.text((50, 1060), "目印：オレンジの服／黄色い生徒会長の腕章／寝ぐせ1本。", font=F(36), fill=(200, 50, 50))
    d.text((50, 1110), "原作の制服・髪型には寄せない。役名だけ「会長」。", font=F(36), fill=(200, 50, 50))
    im.save("sheet1_boku.png")

    # ---- 2枚目：相手役の出し方と小物 ----
    im, d = sheet_base("相手役（かぐや）", "画面には描かない。声と手と小物だけ")
    rows = [("手（袖ごし）", lambda c, m: hand_in(c, m, (50, 30, 55), 'x-', 22), (40, 36, 30), (58, 30, 55), 34),
            ("チケット", lambda c, m: ticket(c, m, 55, 30, 55), (55, 40, 44), (55, 30, 55), 30),
            ("お弁当", lambda c, m: bento(c, m, 55, 28, 55), (55, 44, 42), (55, 29, 55), 34),
            ("傘", lambda c, m: umbrella(c, m, 55, 24, 55), (55, 36, 20), (55, 31, 55), 34),
            ("スマホとスタンプ", lambda c, m: phone(c, m, 55, 26, 55, frog=True), (55, 34, 22), (55, 34, 55), 34),
            ("心理テストの吹き出し", lambda c, m: bubble(c, m, 55, 24, 55), (55, 32, 10), (55, 32, 55), 40)]
    for i_, (nm, dr, cam, tgt, fov) in enumerate(rows):
        x = 50 + (i_ % 3) * 420; y = 150 + (i_ // 3) * 470
        im.paste(studio(dr, cam, tgt, fov, 400, 400), (x, y))
        d.text((x + 200, y + 425), nm, font=F(30), fill=(40, 45, 60), anchor="mm")
    d.text((1350, 150), "色", font=F(40), fill=(20, 20, 30))
    for i_, (nm, cc) in enumerate([("袖", SLEEVE), ("そで口", CUFF), ("手", HANDC)]):
        y = 205 + i_ * 58
        d.rounded_rectangle([1350, y, 1395, y + 45], 6, fill=tuple(int(min(1, v) * 255) for v in cc), outline=(200, 200, 210))
        d.text((1415, y + 5), nm, font=F(30), fill=(30, 30, 40)); d.text((1600, y + 8), hexs(cc), font=F(26), fill=(90, 95, 110))
    d.text((1350, 420), "出し方", font=F(40), fill=(20, 20, 30))
    for i_, s in enumerate(["声：四国めたん ノーマル", "手：画面の端から入る", "目線カメラ：少し低い位置", "  から僕を見上げる", "肩ごし：手前に手と小物、", "  奥に僕", "負け：ドアがバタン・揺れ"]):
        d.text((1350, 475 + i_ * 40), s, font=F(26), fill=(60, 65, 80))
    d.text((50, 1110), "目印：紺の袖＋白いそで口。原作の姿・配色・小物は再現しない。", font=F(36), fill=(200, 50, 50))
    im.save("sheet2_aite.png")

    # ---- 3枚目：舞台 ----
    im, d = sheet_base("舞台", "6本勝負で使う4つの場所")
    shots = [("生徒会室（夕方）", "room", (PX + 30, FY + 46, 12), (PX - 5, FY + 14, 70)),
             ("廊下（昼）", "hall", (56, FY + 30, 2), (56, FY + 20, 60)),
             ("昇降口（大雨）", "ent", (55, FY + 30, 104), (55, FY + 16, 40)),
             ("校舎（夕日）", "out", (70, 20, 20), (70, 34, 100))]
    for i_, (nm, st, cam, tgt) in enumerate(shots):
        S_ = get(st)
        img, _ = render(S_, S_.base_c, S_.base_m, cam, tgt, 62, 270, 480)
        x = 50 + i_ * 480
        im.paste(Image.fromarray((np.clip(finish(img), 0, 1) * 255).astype(np.uint8)).resize((450, 800)), (x, 150))
        d.text((x + 225, 985), nm, font=F(32), fill=(40, 45, 60), anchor="mm")
    d.text((50, 1060), "原作の建物は再現しない。どこの学校にもありそうな形で作る。", font=F(36), fill=(200, 50, 50))
    im.save("sheet3_butai.png")


# ------------------------------------------------------------------
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
        spec = sys.argv[2]
        ims = []
        for s_ in spec.split(','):
            k, t = s_.split(':')
            im = Image.fromarray((frame(int(k), float(t)) * 255).astype(np.uint8)).resize((180, 320))
            d = ImageDraw.Draw(im)
            for y in (int(320 * .36), int(320 * .43), int(320 * .68)):
                d.line([(0, y), (180, y)], fill=(255, 0, 0), width=1)
            ims.append(im)
        cols = min(8, len(ims))
        sheet = Image.new('RGB', (180 * cols, 320 * ((len(ims) + cols - 1) // cols)))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % cols) * 180, (i // cols) * 320))
        sheet.save('stills.png')
    else:
        os.makedirs('clips', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips/{k + 1:02d}.mp4')
