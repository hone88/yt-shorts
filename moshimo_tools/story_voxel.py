"""Instagram向けの長い物語「もしも、あと何回会えるかが頭の上に見えたら？」（台本 20261121）。マイクラ風3D。
登場人物はすべてオリジナル：
  僕   …大学1年。グレーのパーカー・ジーンズ・白いスニーカー・黒い短髪
  母さん…ベージュの服・ピンクのエプロン・うしろでまとめた髪（おだんご）
  友だち…緑のTシャツ・つんつん頭
  店員さん…青白しまの制服・青い帽子
頭の上の数字は、3D の位置を画面に写して、あとから文字で重ねる（字がつぶれないように）。
参考動画（172秒の物語ショート）にならい、約2.4秒ごとにカットを切りかえる。
使い方:
  python3 story_voxel.py stills k:t,... [out.png]
  python3 story_voxel.py 0,2,4"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import render, particles, ease, C, f32, Scene, camera
from elevator_voxel import put, shake
import car_voxel as CV
from kaguya2_voxel import roll, cut, snap, lerp

W, H, FPS, RS = 1080, 1920, 30, 4
FY = 2
_est = [3.1, 3.5, 2.9, 2.1, 2.0, 3.4, 2.9, 2.5, 3.2, 1.8, 4.4, 2.2, 3.3, 2.1, 2.6, 2.0, 3.8, 3.4, 1.9, 2.9]
CLIPS = [round(x * 1.27 * 1.15, 1) for x in _est]
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts', 'NotoSansCJK-Black.ttc')
SEPIA = (1.08, 0.93, 0.72)

# ---------------------------------------------------------------- デザイン
SKIN, EYE, MOUTH, WHITE, TEAR, BLUSH = (0.95, 0.77, 0.62), (0.08, 0.07, 0.1), (0.62, 0.25, 0.22), (0.97, 0.97, 0.97), (0.5, 0.8, 1.3), (1.0, 0.58, 0.6)
P_BOKU = {"髪": (0.12, 0.09, 0.07), "服": (0.55, 0.58, 0.63), "服2": (0.45, 0.48, 0.53), "下": (0.24, 0.34, 0.6), "靴": (0.95, 0.95, 0.95)}
P_MOM = {"髪": (0.22, 0.14, 0.1), "服": (0.86, 0.76, 0.6), "服2": (0.95, 0.6, 0.6), "下": (0.45, 0.33, 0.25), "靴": (0.35, 0.25, 0.2)}
P_FRIEND = {"髪": (0.3, 0.2, 0.12), "服": (0.3, 0.68, 0.35), "服2": (0.25, 0.58, 0.3), "下": (0.15, 0.15, 0.18), "靴": (0.85, 0.3, 0.25)}
P_CLERK = {"髪": (0.1, 0.08, 0.07), "服": (0.25, 0.45, 0.85), "服2": (0.95, 0.95, 0.95), "下": (0.2, 0.2, 0.24), "靴": (0.2, 0.2, 0.22)}
P_KID = {"髪": (0.12, 0.09, 0.07), "服": (0.95, 0.95, 0.95), "服2": (0.2, 0.4, 0.85), "下": (0.2, 0.3, 0.7), "靴": (0.95, 0.95, 0.95)}

# 顔 8×8（上の行から、見る人から見た並び）。H=髪 S=肌 W=白目 E=黒目 M=口 P=赤み T=なみだ
FACES = {
    "ふつう": ["HHHHHHHH", "HHHHHHHH", "HSSSSSSH", "SSSSSSSS", "SWESSEWS", "SSSSSSSS", "SSSMMSSS", "SSSSSSSS"],
    "笑顔": ["HHHHHHHH", "HHHHHHHH", "HSSSSSSH", "SSSSSSSS", "SEESSEES", "SPSSSSPS", "SSMSSMSS", "SSSMMSSS"],
    "驚き": ["HHHHHHHH", "HHHHHHHH", "HSSSSSSH", "SWWSSWWS", "SWESSEWS", "SSSSSSSS", "SSSMMSSS", "SSSMMSSS"],
    "泣き": ["HHHHHHHH", "HHHHHHHH", "HSSSSSSH", "SSSSSSSS", "SEESSEES", "STSSSSTS", "STSMMSTS", "STSSSSTS"],
    "決意": ["HHHHHHHH", "HHHHHHHH", "HHSSSSHH", "SSSSSSSS", "SWESSEWS", "SSSSSSSS", "SSMMMMSS", "SSSSSSSS"],
}


def hito(c, m, cx, fy, cz, P, face="ふつう", arms="down", f=-1, kid=False, bun=False, apron=False, cap=False,
         stripe=False, spiky=False, sit=False, step=0.0):
    """ブロックの人。顔は f=-1 で -z 向き、f=+1 で +z 向き。cx,cz は体の中心。"""
    Z = lambda a, b: (cz - f * a, cz - f * b)          # a,b は「前が負・うしろが正」の奥行き

    def B(x0, x1, y0, y1, a, b, col, var=0.04):
        z0, z1 = Z(a, b)
        put(c, m, x0, x1, y0, y1, min(z0, z1), max(z0, z1), col, 1, var)
    leg = 6 if kid else 12
    body = 8 if kid else 12
    hw = 3 if kid else 4
    y = fy
    if sit:
        B(cx - hw, cx + hw, y + 6, y + 8, -8, 2, P["下"])                # もも（前へ）
        B(cx - hw, cx + hw, y, y + 8, -10, -8, P["下"])                     # すね
        by = y + 8
    else:
        sw = int(round(2 * math.sin(step * 2 * math.pi))) if step else 0
        B(cx - hw, cx, y + 2, y + leg, -2 + sw, 2 + sw, P["下"]); B(cx - hw, cx, y, y + 2, -3 + sw, 2 + sw, P["靴"], 0.02)
        B(cx, cx + hw, y + 2, y + leg, -2 - sw, 2 - sw, P["下"]); B(cx, cx + hw, y, y + 2, -3 - sw, 2 - sw, P["靴"], 0.02)
        by = y + leg
    B(cx - hw, cx + hw, by, by + body, -2, 2, P["服"])
    if stripe:
        for yy in range(by + 1, by + body, 3):
            B(cx - hw, cx + hw, yy, yy + 1, -2, 2, P["服2"], 0.0)
    if apron:
        B(cx - hw + 1, cx + hw - 1, by - (0 if sit else 4), by + body - 2, -3, -2, P["服2"], 0.02)
    sy = by + body
    for side in (-1, 1):
        x0 = cx - hw - 3 if side < 0 else cx + hw
        if arms == "up":
            B(x0, x0 + 3, sy, sy + body - 2, -1.5, 1.5, P["服"]); B(x0, x0 + 3, sy + body - 2, sy + body + 1, -1.5, 1.5, SKIN)
        elif arms == "face":       # 両手で顔をおおう
            B(x0, x0 + 3, sy - 6, sy, -1.5, 1.5, P["服"])
            B(cx - hw + (0 if side < 0 else hw), cx + (0 if side < 0 else hw), sy + 1, sy + 5, -5, -4, SKIN)
        elif arms == "wave" and side > 0:
            B(x0, x0 + 3, sy, sy + body - 2, -1.5, 1.5, P["服"]); B(x0, x0 + 3, sy + body - 2, sy + body + 1, -1.5, 1.5, SKIN)
        elif arms == "front":     # 両手を前に（お弁当をわたす・ハンドル）
            B(x0, x0 + 3, sy - 5, sy, -1.5, 1.5, P["服"]); B(x0, x0 + 3, sy - 7, sy - 4, -8, -1.5, P["服"]); B(x0, x0 + 3, sy - 7, sy - 4, -10, -8, SKIN)
        else:
            B(x0, x0 + 3, sy - body + 2, sy, -1.5, 1.5, P["服"]); B(x0, x0 + 3, sy - body, sy - body + 2, -1.5, 1.5, SKIN)
    hy = sy
    B(cx - 4, cx + 4, hy, hy + 8, -4, 4, SKIN, 0.03)
    B(cx - 4, cx + 4, hy + 6, hy + 8, -4, 4, P["髪"])
    B(cx - 4, cx + 4, hy + 1, hy + 8, 3, 4, P["髪"])
    B(cx - 4, cx - 3, hy + 3, hy + 8, -4, 4, P["髪"]); B(cx + 3, cx + 4, hy + 3, hy + 8, -4, 4, P["髪"])
    if bun:
        B(cx - 2, cx + 2, hy + 4, hy + 8, 4, 7, P["髪"])
    if spiky:
        for x in range(cx - 4, cx + 4, 2):
            B(x, x + 1, hy + 8, hy + 10, -2, 2, P["髪"])
    if cap:
        B(cx - 4, cx + 4, hy + 7, hy + 9, -4, 4, P["服"]); B(cx - 4, cx + 4, hy + 7, hy + 8, -7, -4, P["服"])
    tbl = {"H": P["髪"], "S": SKIN, "W": WHITE, "E": EYE, "M": MOUTH, "P": BLUSH, "T": TEAR}
    for r, row in enumerate(FACES[face]):
        yy = hy + 7 - r
        for i_, ch in enumerate(row):
            x = (cx + 3 - i_) if f < 0 else (cx - 4 + i_)
            col = tbl[ch]
            B(x, x + 1, yy, yy + 1, -4, -3, col, 0.0 if ch in "WEMT" else 0.02)
    return (cx, hy + 8 + (3 if spiky or cap else 1), cz)


def H_(**kw):
    return lambda c, m: hito(c, m, **kw)


# ---------------------------------------------------------------- 背景（セット）
def sky_day(S):
    S.sun = np.array([0.35, 0.8, -0.45]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.15, 1.05, 0.92); S.amb = C(0.58, 0.62, 0.72)
    S.hor = C(0.8, 0.88, 1.0); S.top = C(0.32, 0.55, 0.95); S.fog0, S.fogk = 120, 300


def build_street(night=False):
    S = Scene(120, 70, 140)
    c, m = S.col, S.mat
    put(c, m, 0, 120, 0, FY, 0, 140, (0.36, 0.36, 0.38), 1, 0.04)               # 道
    for z in range(4, 140, 14):
        put(c, m, 59, 61, FY - 1, FY, z, z + 6, (0.95, 0.95, 0.9), 1, 0.0)
    put(c, m, 0, 28, 0, FY + 1, 0, 140, (0.7, 0.68, 0.64), 1, 0.04)             # 歩道
    put(c, m, 92, 120, 0, FY + 1, 0, 140, (0.7, 0.68, 0.64), 1, 0.04)
    rg = np.random.default_rng(3)
    for side, x0, x1 in (("L", 0, 16), ("R", 104, 120)):
        z = 0
        while z < 140:
            d = int(rg.integers(16, 26)); h = int(rg.integers(30, 62))
            col = [(0.86, 0.82, 0.74), (0.72, 0.75, 0.8), (0.8, 0.62, 0.5), (0.9, 0.88, 0.84), (0.6, 0.64, 0.7)][int(rg.integers(0, 5))]
            put(c, m, x0, x1, FY, FY + h, z, z + d - 1, col, 1, 0.03)
            fx = x1 - 1 if side == "L" else x0
            for y in range(FY + 6, FY + h - 4, 7):
                for zz in range(z + 2, z + d - 4, 5):
                    lit = night and rg.random() < 0.6
                    put(c, m, fx, fx + 1, y, y + 4, zz, zz + 3, (1.6, 1.25, 0.7) if lit else (0.35, 0.45, 0.6), 4 if lit else 3, 0.0)
            z += d
    for z in range(10, 140, 30):     # 街灯
        for x in (26, 93):
            put(c, m, x, x + 1, FY, FY + 30, z, z + 1, (0.3, 0.3, 0.32), 1, 0.0)
            put(c, m, x - 1, x + 2, FY + 30, FY + 31, z - 1, z + 2, (1.6, 1.4, 1.0) if night else (0.85, 0.85, 0.8), 4 if night else 1, 0.0)
    S.base_c, S.base_m = c.copy(), m.copy()
    sky_day(S)
    if night:
        S.sun = np.array([0.3, 0.6, -0.5]); S.sun /= np.linalg.norm(S.sun); S.sunc = C(0.25, 0.28, 0.45); S.amb = C(0.3, 0.32, 0.45)
        S.hor = C(0.12, 0.14, 0.28); S.top = C(0.02, 0.03, 0.1); S.sundisk = 0.0
        S.lights = [((60, FY + 40, z), (0.5, 0.42, 0.3), 40) for z in (30, 70, 110)]
    return S


def build_konbini():
    S = Scene(110, 60, 110)
    c, m = S.col, S.mat
    put(c, m, 0, 110, 0, FY, 0, 110, (0.9, 0.9, 0.88), 1, 0.02)
    for x in range(0, 110, 6):
        put(c, m, x, x + 1, FY - 1, FY, 0, 110, (0.8, 0.8, 0.78), 1, 0.0)
    put(c, m, 0, 110, FY, 56, 100, 102, (0.95, 0.95, 0.94), 1, 0.02)          # 奥の壁
    put(c, m, 0, 110, FY + 40, FY + 44, 99, 100, (0.2, 0.6, 0.35), 1, 0.0)     # 緑と青のライン
    put(c, m, 0, 110, FY + 44, FY + 47, 99, 100, (0.2, 0.45, 0.85), 1, 0.0)
    put(c, m, 40, 80, FY, FY + 14, 60, 70, (0.75, 0.75, 0.78), 1, 0.03)         # レジカウンター
    put(c, m, 40, 80, FY + 14, FY + 15, 59, 71, (0.95, 0.95, 0.95), 1, 0.0)
    put(c, m, 66, 74, FY + 15, FY + 21, 63, 68, (0.25, 0.25, 0.28), 1, 0.0)     # レジ
    rg = np.random.default_rng(5)
    for x0 in (4, 86):                                                          # 棚
        put(c, m, x0, x0 + 18, FY, FY + 30, 20, 90, (0.85, 0.85, 0.85), 1, 0.02)
        for y in range(FY + 4, FY + 30, 7):
            for z in range(21, 89, 3):
                col = [(0.9, 0.3, 0.25), (0.95, 0.8, 0.25), (0.3, 0.6, 0.9), (0.35, 0.75, 0.4), (0.95, 0.55, 0.2)][int(rg.integers(0, 5))]
                xf = x0 + 18 if x0 < 50 else x0 - 1
                put(c, m, xf, xf + 1, y, y + 5, z, z + 2, col, 1, 0.03)
    put(c, m, 0, 110, 56, 58, 0, 110, (0.97, 0.97, 0.97), 1, 0.0)
    for z in range(10, 110, 22):
        put(c, m, 20, 90, 55, 56, z, z + 2, (1.6, 1.6, 1.55), 4, 0.0)
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = None; S.amb = C(0.85, 0.86, 0.9); S.lights = [((55, 50, 40), (0.6, 0.6, 0.6), 80)]
    S.hor = C(0.85, 0.9, 1.0); S.top = C(0.5, 0.65, 0.95); S.fog0, S.fogk = 200, 400
    return S


def build_room1():
    """一人暮らしの部屋：ベッド・机・段ボール"""
    S = Scene(80, 60, 80)
    c, m = S.col, S.mat
    put(c, m, 0, 80, 0, FY, 0, 80, (0.7, 0.55, 0.38), 1, 0.05)
    put(c, m, 0, 80, FY, 56, 74, 76, (0.93, 0.92, 0.9), 1, 0.02)
    put(c, m, 2, 4, FY, 56, 0, 76, (0.9, 0.9, 0.88), 1, 0.02)
    m[2:4, FY + 18:FY + 40, 30:56] = 0                                          # 窓
    put(c, m, 2, 4, FY + 28, FY + 29, 30, 56, (0.9, 0.9, 0.88), 1, 0.0)
    put(c, m, 4, 30, FY, FY + 8, 50, 74, (0.85, 0.85, 0.9), 1, 0.02)           # ベッド
    put(c, m, 4, 30, FY + 8, FY + 10, 50, 74, (0.35, 0.55, 0.85), 1, 0.03)
    put(c, m, 4, 12, FY + 10, FY + 12, 64, 72, (0.97, 0.97, 0.97), 1, 0.0)
    put(c, m, 50, 76, FY + 14, FY + 16, 56, 72, (0.6, 0.42, 0.25), 1, 0.03)    # 机
    for x in (51, 74):
        put(c, m, x, x + 1, FY, FY + 14, 57, 71, (0.5, 0.35, 0.2), 1, 0.0)
    put(c, m, 58, 70, FY + 16, FY + 24, 66, 68, (0.15, 0.15, 0.18), 1, 0.0)    # ノートPC
    for (x, z, h) in ((56, 16, 8), (64, 14, 12), (60, 26, 7)):                  # 段ボール
        put(c, m, x, x + 9, FY, FY + h, z, z + 8, (0.72, 0.55, 0.35), 1, 0.04)
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = np.array([-0.8, 0.5, 0.1]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.2, 1.1, 0.95); S.amb = C(0.62, 0.62, 0.68); S.lights = []
    S.hor = C(0.85, 0.9, 1.0); S.top = C(0.4, 0.6, 0.95); S.fog0, S.fogk = 200, 400
    return S


def build_home():
    """実家の玄関：ドア・土間・上がりかまち・廊下。家の中は +z。"""
    S = Scene(100, 64, 110)
    c, m = S.col, S.mat
    put(c, m, 0, 100, 0, FY, 0, 110, (0.55, 0.53, 0.5), 1, 0.05)                # 土間
    put(c, m, 0, 100, FY, FY + 4, 40, 110, (0.72, 0.52, 0.32), 1, 0.04)         # 廊下（一段高い）
    for x in range(0, 100, 5):
        put(c, m, x, x + 1, FY + 3, FY + 4, 40, 110, (0.62, 0.44, 0.27), 1, 0.0)
    put(c, m, 0, 100, FY, 60, 2, 4, (0.92, 0.9, 0.85), 1, 0.02)                # 玄関ドアの壁
    put(c, m, 38, 62, FY, FY + 44, 3, 4, (0.45, 0.3, 0.2), 1, 0.03)             # ドア
    put(c, m, 58, 60, FY + 20, FY + 23, 4, 5, (0.85, 0.75, 0.3), 1, 0.0)
    put(c, m, 0, 4, FY, 60, 0, 110, (0.93, 0.91, 0.86), 1, 0.02)
    put(c, m, 96, 100, FY, 60, 0, 110, (0.93, 0.91, 0.86), 1, 0.02)
    put(c, m, 4, 20, FY, FY + 26, 10, 36, (0.6, 0.42, 0.26), 1, 0.04)           # げた箱
    put(c, m, 8, 14, FY + 26, FY + 32, 20, 26, (0.3, 0.55, 0.3), 1, 0.08)       # 花
    for (x, z) in ((26, 20), (34, 24), (66, 22)):                               # くつ
        put(c, m, x, x + 4, FY, FY + 2, z, z + 7, (0.3, 0.3, 0.35), 1, 0.04)
    put(c, m, 0, 100, 58, 60, 0, 110, (0.95, 0.95, 0.93), 1, 0.0)
    put(c, m, 44, 56, 57, 58, 50, 60, (1.6, 1.4, 1.0), 4, 0.0)
    put(c, m, 0, 100, FY, 60, 104, 106, (0.93, 0.91, 0.86), 1, 0.02)
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = None; S.amb = C(0.85, 0.8, 0.72); S.lights = [((50, 54, 30), (0.85, 0.7, 0.5), 80)]
    S.hor = C(0.85, 0.9, 1.0); S.top = C(0.45, 0.62, 0.95); S.fog0, S.fogk = 300, 500
    return S


def build_field():
    """運動会のグラウンド：土・白線・万国旗・テント"""
    S = Scene(140, 70, 140)
    c, m = S.col, S.mat
    put(c, m, 0, 140, 0, FY, 0, 140, (0.72, 0.58, 0.4), 1, 0.06)
    for z in (50, 62, 74):
        put(c, m, 0, 140, FY - 1, FY, z, z + 1, (0.97, 0.97, 0.95), 1, 0.0)
    put(c, m, 100, 101, FY - 1, FY, 50, 75, (0.97, 0.97, 0.95), 1, 0.0)          # ゴール
    for x in (100,):
        put(c, m, x, x + 1, FY, FY + 16, 48, 49, (0.9, 0.9, 0.9), 1, 0.0); put(c, m, x, x + 1, FY, FY + 16, 76, 77, (0.9, 0.9, 0.9), 1, 0.0)
        put(c, m, x, x + 1, FY + 10, FY + 11, 49, 76, (1.2, 0.3, 0.3), 1, 0.0)
    cols = [(0.95, 0.25, 0.25), (0.25, 0.5, 0.95), (0.95, 0.8, 0.2), (0.3, 0.75, 0.35), (0.97, 0.97, 0.97)]
    for i, x in enumerate(range(0, 140, 4)):                                     # 万国旗
        y = FY + 44 - int(5 * math.sin((x / 140) * math.pi))
        put(c, m, x, x + 3, y - 3, y, 90, 91, cols[i % 5], 1, 0.0)
    for x0 in (10, 50):                                                         # テント
        put(c, m, x0, x0 + 30, FY + 26, FY + 28, 92, 118, (0.97, 0.97, 0.97), 1, 0.0)
        for xx in (x0, x0 + 29):
            for zz in (92, 117):
                put(c, m, xx, xx + 1, FY, FY + 26, zz, zz + 1, (0.6, 0.6, 0.62), 1, 0.0)
    put(c, m, 0, 140, FY, FY + 20, 132, 136, (0.85, 0.82, 0.75), 1, 0.03)       # 校舎の塀
    S.base_c, S.base_m = c.copy(), m.copy()
    sky_day(S)
    return S


def build_kitchen():
    S = Scene(90, 60, 90)
    c, m = S.col, S.mat
    put(c, m, 0, 90, 0, FY, 0, 90, (0.75, 0.6, 0.42), 1, 0.04)
    put(c, m, 0, 90, FY, 58, 80, 82, (0.95, 0.93, 0.88), 1, 0.02)
    put(c, m, 10, 80, FY, FY + 16, 66, 80, (0.88, 0.86, 0.8), 1, 0.02)           # 流し台
    put(c, m, 10, 80, FY + 16, FY + 17, 66, 80, (0.75, 0.76, 0.8), 1, 0.0)
    put(c, m, 58, 70, FY + 17, FY + 18, 68, 76, (0.25, 0.25, 0.28), 1, 0.0)      # コンロ
    put(c, m, 60, 68, FY + 18, FY + 21, 70, 74, (0.55, 0.56, 0.6), 1, 0.0)       # フライパン
    m[30:52, FY + 26:FY + 46, 80:82] = 0                                          # 窓（朝の光）
    put(c, m, 20, 70, FY + 14, FY + 15, 30, 48, (0.6, 0.42, 0.25), 1, 0.03)       # テーブル
    for x in (21, 68):
        for z in (31, 46):
            put(c, m, x, x + 1, FY, FY + 14, z, z + 1, (0.5, 0.35, 0.2), 1, 0.0)
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = np.array([0.2, 0.55, 0.8]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.35, 1.15, 0.85); S.amb = C(0.6, 0.58, 0.58); S.lights = []
    S.hor = C(1.0, 0.95, 0.85); S.top = C(0.55, 0.7, 0.95); S.fog0, S.fogk = 200, 400
    return S


def bento(c, m, x, y, z):
    put(c, m, x, x + 8, y, y + 3, z, z + 6, (0.2, 0.25, 0.55), 1, 0.02)
    put(c, m, x + 1, x + 4, y + 3, y + 4, z + 1, z + 5, (0.98, 0.98, 0.96), 1, 0.02)
    put(c, m, x + 4, x + 6, y + 3, y + 4, z + 1, z + 3, (0.95, 0.85, 0.2), 1, 0.02)
    put(c, m, x + 6, x + 7, y + 3, y + 4, z + 1, z + 5, (0.85, 0.3, 0.25), 1, 0.02)
    put(c, m, x + 4, x + 6, y + 3, y + 4, z + 3, z + 5, (0.3, 0.65, 0.3), 1, 0.02)


def build_station():
    S = Scene(130, 64, 130)
    c, m = S.col, S.mat
    put(c, m, 0, 130, 0, FY, 0, 130, (0.38, 0.38, 0.4), 1, 0.04)
    put(c, m, 0, 130, FY, FY + 1, 80, 130, (0.7, 0.68, 0.64), 1, 0.03)
    put(c, m, 20, 110, FY, FY + 34, 96, 124, (0.9, 0.88, 0.82), 1, 0.03)        # 駅舎
    put(c, m, 16, 114, FY + 34, FY + 38, 92, 128, (0.45, 0.32, 0.25), 1, 0.03)
    put(c, m, 45, 85, FY + 24, FY + 31, 95, 96, (0.2, 0.35, 0.7), 1, 0.0)       # 駅名の看板
    put(c, m, 50, 80, FY + 26, FY + 29, 94.6, 95, (0.97, 0.97, 0.97), 1, 0.0)
    m[54:76, FY:FY + 20, 96:97] = 0
    c[54:76, FY:FY + 20, 97] = C(0.15, 0.15, 0.18)
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = np.array([0.6, 0.3, -0.7]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.4, 1.05, 0.7); S.amb = C(0.6, 0.6, 0.66)
    S.hor = C(1.0, 0.9, 0.75); S.top = C(0.45, 0.62, 0.92); S.fog0, S.fogk = 160, 360
    return S


def build_train():
    """電車の中（夕方）：両側に長いいす・窓。x が進む向き。"""
    S = Scene(120, 50, 50)
    c, m = S.col, S.mat
    put(c, m, 0, 120, 0, FY, 0, 50, (0.45, 0.42, 0.4), 1, 0.04)
    put(c, m, 0, 120, FY, 46, 0, 2, (0.88, 0.88, 0.86), 1, 0.02)
    put(c, m, 0, 120, FY, 46, 48, 50, (0.88, 0.88, 0.86), 1, 0.02)
    put(c, m, 0, 120, 44, 46, 0, 50, (0.93, 0.93, 0.92), 1, 0.0)
    for x in range(4, 120, 22):
        m[x:x + 16, FY + 18:FY + 34, 0:2] = 0; m[x:x + 16, FY + 18:FY + 34, 48:50] = 0
    for zz in ((2, 10), (40, 48)):
        put(c, m, 0, 120, FY, FY + 8, zz[0], zz[1], (0.25, 0.42, 0.3), 1, 0.03)
        b = (2, 4) if zz[0] == 2 else (46, 48)
        put(c, m, 0, 120, FY + 8, FY + 18, b[0], b[1], (0.25, 0.42, 0.3), 1, 0.03)
    for x in range(10, 120, 12):                                                   # つり革
        for z in (16, 34):
            put(c, m, x, x + 1, 36, 44, z, z + 1, (0.85, 0.85, 0.85), 1, 0.0)
            put(c, m, x - 1, x + 2, 34, 36, z - 1, z + 2, (0.95, 0.85, 0.3), 1, 0.0)
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = np.array([0.15, 0.25, -0.95]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.5, 0.85, 0.45); S.amb = C(0.72, 0.62, 0.62); S.lights = [((60, 40, 30), (0.7, 0.55, 0.45), 60)]
    S.hor = C(1.4, 0.75, 0.4); S.top = C(0.45, 0.35, 0.6); S.fog0, S.fogk = 300, 500
    return S


_S = {}
SETS = {"street": build_street, "night": lambda: build_street(True), "konbini": build_konbini, "room1": build_room1,
        "home": build_home, "field": build_field, "kitchen": build_kitchen, "station": build_station, "train": build_train}


def get(k):
    if k not in _S:
        _S[k] = SETS[k]()
    return _S[k]


# ---------------------------------------------------------------- 頭の上の数字（画面に重ねる）
_font = {}


def font(sz):
    if sz not in _font:
        _font[sz] = ImageFont.truetype(FONT, sz)
    return _font[sz]


def project(cam, tgt, fov, p):
    cam_, fw, rt, up, th = camera(cam, tgt, fov)
    rel = np.array(p, float) - cam_
    z = rel @ fw
    if z <= 1:
        return None
    x = (rel @ rt) / (z * th * W / H); y = (rel @ up) / (z * th)
    return ((x + 1) / 2 * W, (1 - y) / 2 * H, z)


def tags(img, cam, tgt, fov, items):
    """items: [(3D位置, 文字, 濃さ0〜1, 大きさ倍率, 色)]"""
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for p, text, a, k, col in items:
        if a <= 0.01:
            continue
        pr = project(cam, tgt, fov, (p[0], p[1] + 3, p[2]))
        if pr is None:
            continue
        x, y, z = pr
        sz = int(np.clip(4000 / z * k, 34, 240))
        f = font(sz)
        bb = d.textbbox((0, 0), text, font=f, anchor="mm")
        tw, th_ = bb[2] - bb[0], bb[3] - bb[1]
        pad = sz * 0.28
        d.rounded_rectangle([x - tw / 2 - pad, y - th_ / 2 - pad * 0.8, x + tw / 2 + pad, y + th_ / 2 + pad * 0.8], radius=int(sz * 0.4),
                            fill=(15, 23, 42, int(170 * a)), outline=col + (int(255 * a),), width=max(2, sz // 14))
        d.text((x, y), text, font=f, fill=col + (int(255 * a),), anchor="mm")
    im = Image.alpha_composite(im, lay).convert("RGB")
    return np.asarray(im).astype(f32) / 255


GOLD, CYAN, PINK = (255, 214, 90), (110, 231, 249), (255, 160, 170)


# ---------------------------------------------------------------- 撮影
def tone(img, expo=1.1):
    img = np.clip(img, 0, None)
    return np.clip(img / (1 + 0.25 * img) * expo, 0, 1)


def shoot(set_, cam, tgt, fov, draws, grade=(1, 1, 1), t=0.0, sh=0.0, fx=None, tg=(), dutch=0.0, vign=0.0):
    S = get(set_)
    c, m = S.base_c.copy(), S.base_m.copy()
    for d in draws:
        d(c, m)
    if sh > 0:
        cam, tgt = shake(cam, tgt, sh, t)
    img, depth = render(S, c, m, cam, tgt, fov, W // RS, H // RS)
    if fx:
        fx(img, depth, cam, tgt, fov)
    img = tone(img) * C(*grade)
    img = np.repeat(np.repeat(img, RS, 0), RS, 1)
    if vign > 0:
        yy, xx = np.mgrid[0:H, 0:W]
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        img = img * (1 - vign * np.clip(r - 0.6, 0, 1))[..., None]
    if tg:
        img = tags(img, cam, tgt, fov, tg)
    img = roll(img, dutch)
    return np.clip(img, 0, 1)


def crowd(n, seed, x0, x1, z0, z1, t, walk=True, kinds=None):
    """通行人。返り値：(描く関数のリスト, 頭の位置と数字)"""
    rg = np.random.default_rng(seed)
    draws, heads = [], []
    shirts = [(0.85, 0.35, 0.3), (0.3, 0.5, 0.85), (0.95, 0.85, 0.4), (0.4, 0.4, 0.45), (0.9, 0.9, 0.9), (0.55, 0.35, 0.6)]
    for i in range(n):
        P = {"髪": [(0.1, 0.08, 0.07), (0.35, 0.22, 0.12), (0.55, 0.5, 0.48)][int(rg.integers(0, 3))], "服": shirts[int(rg.integers(0, 6))],
             "服2": (0.9, 0.9, 0.9), "下": [(0.2, 0.25, 0.4), (0.3, 0.3, 0.32), (0.45, 0.35, 0.25)][int(rg.integers(0, 3))], "靴": (0.25, 0.25, 0.28)}
        f = -1 if rg.random() < 0.5 else 1
        sp = rg.uniform(4, 7) if walk else 0
        cx = int(rg.integers(x0, x1)); cz = int(rg.integers(z0, z1) + (-f) * 0)
        cz = int(cz + f * (-1) * sp * t) if walk else cz
        num = [str(int(rg.integers(1, 9))), str(int(rg.integers(10, 99))), str(int(rg.integers(100, 999))), str(int(rg.integers(1, 5)))][int(rg.integers(0, 4))]
        draws.append(H_(cx=cx, fy=FY, cz=cz, P=P, f=f, step=(t * 1.6 + rg.random()) if walk else 0.0))
        heads.append(((cx, FY + 34, cz), num))
    return draws, heads


def tears(img, depth, cam, tgt, fov, t, x, y, z, f=-1):
    rg = np.random.default_rng(2); n = 6
    for side in (-2.5, 2.5):
        ph = (np.arange(n) / n + t * 0.8) % 1
        p = np.stack([np.full(n, x + side), y - 3 - ph * 5, np.full(n, z + f * 4.8)], 1)
        particles(img, depth, cam, tgt, fov, p, np.tile(C(*TEAR) * 1.2, (n, 1)), 0.6)


# ---------------------------------------------------------------- 場面
def aim(head, f, d, yaw=0.0, up=4.0, fov=46, frac=0.26):
    """顔（head）を画面の上から frac の高さに置くカメラ。f=顔の向き（-1:-z / +1:+z）、yaw で横へ回り込む。"""
    hx, hy, hz = head
    d = d * 1.6; frac = 0.24
    cam = (hx + d * math.sin(yaw), hy + up, hz + f * d * math.cos(yaw))
    dist = math.hypot(d, up)
    dy = (0.5 - frac) * 2 * dist * math.tan(math.radians(fov) / 2)
    return cam, (hx, hy - dy, hz), fov


def HEAD(cx, fy, cz, kid=False, sit=False):
    return (cx, fy + (18 if kid else 24 if sit else 28), cz)


MOMX, MOMZ, ME_Z = 50, 56, 22


def frame(k, t):
    T = CLIPS[k]
    u = t / T
    BK = dict(P=P_BOKU)
    MOM = lambda face="笑顔", **kw: H_(cx=MOMX, fy=FY + 4, cz=MOMZ, P=P_MOM, face=face, f=-1, bun=True, apron=True, **kw)
    mom_h = HEAD(MOMX, FY + 4, MOMZ)
    tagp = lambda h: (h[0], h[1] + 3, h[2])
    if k == 0:   # もしも：にぎやかな通り。顔のアップ → 一気に上へ引くと、全員の頭の上に数字
        dr, hd = crowd(16, 1, 34, 86, 10, 130, t)
        me = H_(cx=60, fy=FY, cz=50, face="驚き", **BK)
        z = snap(t, 0.9, 1.0)
        c1, t1, _ = aim(HEAD(60, FY, 50), -1, 20, 0.0, 2, 44, 0.24)
        cam = lerp(c1, (60 + 30, FY + 95, 50 - 62), z); tgt = lerp(t1, (60, FY + 10, 76), z)
        a = min(1, max(0, (t - 0.9) * 2))
        return shoot("street", cam, tgt, 44 + 18 * z, dr + [me], t=t, tg=[(p, s, a, 1.0, GOLD) for p, s in hd])
    if k == 1:   # この世界では：通りを横から流し撮り → 反対側から
        dr, hd = crowd(14, 2, 34, 86, 10, 130, t)
        c_, uu = cut(t, T, [0.5])
        if c_ == 0:
            cam = (20, FY + 34, 20 + 30 * uu); tgt = (60, FY + 22, 60 + 30 * uu)
        else:
            cam = (100, FY + 30, 110 - 20 * uu); tgt = (60, FY + 20, 70 - 20 * uu)
        return shoot("street", cam, tgt, 52, dr, t=t, tg=[(p, s, 1.0, 1.0, GOLD) for p, s in hd])
    if k == 2:   # ルール：ひとりの頭の上の数字に、ぐっと寄る
        P = {"髪": (0.35, 0.22, 0.12), "服": (0.85, 0.35, 0.3), "服2": (0.9, 0.9, 0.9), "下": (0.2, 0.25, 0.4), "靴": (0.25, 0.25, 0.28)}
        h = HEAD(60, FY, 60)
        z = ease(u)
        c1, t1, _ = aim(h, -1, 60, 0.0, 6, 46, 0.4)
        c2, t2, _ = aim(h, -1, 24, 0.0, 6, 46, 0.42)
        return shoot("street", lerp(c1, c2, z), lerp(t1, t2, z), 46, [H_(cx=60, fy=FY, cz=60, P=P)], t=t,
                     tg=[(tagp(h), "?", 1.0, 1.0, GOLD)])
    if k == 3:   # 友だち：1200（2人の引き → 友だちのアップ）
        fr = H_(cx=54, fy=FY, cz=60, P=P_FRIEND, face="笑顔", arms="wave", spiky=True)
        me = H_(cx=68, fy=FY, cz=64, P=P_BOKU, face="笑顔", f=-1)
        hf = HEAD(54, FY, 60)
        c_, uu = cut(t, T, [0.45])
        if c_ == 0:
            cam, tgt, fov = aim((61, FY + 28, 62), -1, 52 - 4 * uu, 0.3, 4, 50, 0.32)
        else:
            cam, tgt, fov = aim(hf, -1, 26 - 2 * uu, -0.3, 2, 46, 0.3)
        return shoot("street", cam, tgt, fov, [fr, me], t=t, tg=[(tagp(hf), "1200", 1.0, 1.0, GOLD)])
    if k == 4:   # 店員さん：3（店の中の引き → 顔）
        cl = H_(cx=58, fy=FY, cz=76, P=P_CLERK, face="笑顔", f=-1, stripe=True, cap=True)
        h = HEAD(58, FY, 76)
        c_, uu = cut(t, T, [0.4])
        if c_ == 0:
            cam, tgt, fov = aim(h, -1, 56, 0.5, 8, 52, 0.3)
        else:
            cam, tgt, fov = aim(h, -1, 26 - 2 * uu, -0.15, 2, 46, 0.3)
        return shoot("konbini", cam, tgt, fov, [cl], t=t, tg=[(tagp(h), "3", 1.0, 1.0, GOLD)])
    if k == 5:   # みんな気にしない：真上から → 横から
        dr, hd = crowd(22, 3, 30, 90, 0, 140, t)
        c_, uu = cut(t, T, [0.5])
        if c_ == 0:
            cam = (60.5, FY + 120 - 10 * uu, 70.5 - 6); tgt = (60, FY, 70)
        else:
            cam = (100, FY + 18, 20 + 30 * uu); tgt = (60, FY + 22, 70 + 30 * uu)
        return shoot("street", cam, tgt, 54, dr, t=t, tg=[(p, s, 0.85, 1.0, GOLD) for p, s in hd])
    if k == 6:   # 一人暮らし：段ボールの部屋で、のびをする僕
        me = H_(cx=40, fy=FY, cz=40, face="笑顔", arms="up" if t > 1.2 else "down", **BK)
        h = HEAD(40, FY, 40)
        c_, uu = cut(t, T, [0.5])
        if c_ == 0:
            cam, tgt, fov = aim(h, -1, 36, 0.2 + 0.2 * uu, 10, 56, 0.3)
        else:
            cam, tgt, fov = aim(h, -1, 22, -0.6, 2, 48, 0.28)
        return shoot("room1", cam, tgt, fov, [me], t=t)
    if k == 7:   # 夏休み、実家へ：通りを歩く（夕方）。うしろ姿 → 横顔
        zz = int(30 + 5 * t)
        me = H_(cx=60, fy=FY, cz=zz, face="ふつう", f=1, step=t * 1.4, **BK)
        h = HEAD(60, FY, zz)
        c_, uu = cut(t, T, [0.5])
        if c_ == 0:
            cam, tgt, fov = aim(h, -1, 30, 0.0, 4, 52, 0.3)       # うしろから
        else:
            cam, tgt, fov = aim(h, 1, 30, 1.1, 0, 50, 0.3)
        return shoot("street", cam, tgt, fov, [me], t=t, grade=(1.08, 0.98, 0.88))
    if k == 8:   # 玄関：「おかえり」。僕の肩ごし → 母さんの顔
        me = H_(cx=54, fy=FY, cz=ME_Z, face="ふつう", f=1, **BK)
        c_, uu = cut(t, T, [0.45])
        if c_ == 0:
            cam = (66, FY + 34, ME_Z - 16 + 2 * uu); tgt = (50, FY + 24, MOMZ)
            return shoot("home", cam, tgt, 48, [MOM(), me], t=t)
        cam, tgt, fov = aim(mom_h, -1, 26 - 2 * uu, 0.15, 0, 46, 0.3)
        return shoot("home", cam, tgt, fov, [MOM()], t=t)
    if k == 9:   # 母さんの頭の上に「60」がふわっと出る
        z = ease(u)
        c1, t1, _ = aim(mom_h, -1, 40, 0.0, 2, 46, 0.36)
        c2, t2, _ = aim(mom_h, -1, 28, 0.0, 2, 46, 0.4)
        a = min(1, t / 0.6)
        return shoot("home", lerp(c1, c2, z), lerp(t1, t2, z), 46, [MOM()], t=t, tg=[(tagp(mom_h), "60", a, 1.0, PINK)])
    if k == 10:  # 計算：僕の顔（驚き）→ 数字ごしに母さん
        me = H_(cx=54, fy=FY, cz=ME_Z, face="驚き", f=1, **BK)
        c_, uu = cut(t, T, [0.5])
        if c_ == 0:
            cam, tgt, fov = aim(HEAD(54, FY, ME_Z), 1, 22 - 3 * uu, 0.1, 2, 46, 0.26)
            return shoot("home", cam, tgt, fov, [me], t=t, vign=0.5)
        cam = (64, FY + 33, ME_Z - 14); tgt = (50, FY + 28, MOMZ)
        return shoot("home", cam, tgt, 42, [me, MOM()], t=t, vign=0.5, tg=[(tagp(mom_h), "60", 1.0, 1.0, PINK)])
    if k == 11:  # むかし：小さな僕と母さん、手をつないで歩く（セピア）
        zz = int(40 + 4 * t)
        mom = H_(cx=54, fy=FY, cz=zz, P=P_MOM, face="笑顔", f=1, bun=True, step=t * 1.2)
        kid = H_(cx=64, fy=FY, cz=zz, P=P_KID, face="笑顔", f=1, kid=True, step=t * 1.6)
        cam, tgt, fov = aim((59, FY + 26, zz), 1, 44, 0.5 - 0.3 * u, 2, 50, 0.32)
        return shoot("street", cam, tgt, fov, [mom, kid], t=t, grade=SEPIA, vign=0.6)
    if k == 12:  # 運動会：走る小さな僕 → 両手を上げて応援する母さん（セピア）
        c_, uu = cut(t, T, [0.5])
        if c_ == 0:
            xk = int(40 + 18 * t)
            kid = H_(cx=xk, fy=FY, cz=62, P=P_KID, face="決意", f=-1, kid=True, step=t * 3)
            cam, tgt, fov = aim(HEAD(xk, FY, 62, kid=True), -1, 30, 0.35, 0, 50, 0.32)
            return shoot("field", cam, tgt, fov, [kid], t=t, grade=SEPIA, vign=0.6)
        mom = H_(cx=64, fy=FY, cz=86, P=P_MOM, face="笑顔", f=-1, bun=True, arms="up" if int(t * 4) % 2 == 0 else "down")
        cam, tgt, fov = aim(HEAD(64, FY, 86), -1, 30 - 3 * uu, -0.2, 2, 50, 0.3)
        return shoot("field", cam, tgt, fov, [mom], t=t, grade=SEPIA, vign=0.6)
    if k == 13:  # お弁当：朝のキッチン。母さん → お弁当に寄る（セピア）
        mom = H_(cx=45, fy=FY, cz=56, P=P_MOM, face="笑顔", f=-1, bun=True, apron=True, arms="front")
        bd = lambda c, m: bento(c, m, 41, FY + 15, 40)
        c_, uu = cut(t, T, [0.5])
        if c_ == 0:
            cam, tgt, fov = aim(HEAD(45, FY, 56), -1, 40, 0.25, 4, 50, 0.3)
        else:
            cam = (45 + 3 * uu, FY + 30, 22); tgt = (45, FY + 16, 43)
            fov = 44
        return shoot("kitchen", cam, tgt, fov, [mom, bd], t=t, grade=SEPIA, vign=0.6)
    if k == 14:  # 駅まで送ってくれた朝：車と、手をふる僕（セピア）
        def car(c, m):
            CV.car_s(c, m, 66, FY + 7, 66, 14, rot=0.0)
        me = H_(cx=40, fy=FY + 1, cz=82, face="笑顔", f=-1, arms="wave", **BK)
        c_, uu = cut(t, T, [0.5])
        if c_ == 0:
            cam = (50 - 10 * uu, FY + 34, 14); tgt = (54, FY + 14, 72)
            fov = 52
        else:
            cam, tgt, fov = aim(HEAD(40, FY + 1, 82), -1, 26, 0.3, 2, 46, 0.3)
        return shoot("station", cam, tgt, fov, [car, me], t=t, grade=SEPIA, vign=0.6)
    sh_ = HEAD(60, FY, 8, sit=True)
    if k == 15:  # 帰りの電車で泣く（夕日）
        me = H_(cx=60, fy=FY, cz=8, face="泣き", f=1, sit=True, **BK)
        fx = lambda img, dp, cm, tg_, fv: tears(img, dp, cm, tg_, fv, t, 60, sh_[1] + 4, 8, f=1)
        c_, uu = cut(t, T, [0.45])
        if c_ == 0:
            cam, tgt, fov = aim(sh_, 1, 24, 0.7 - 0.2 * uu, 4, 54, 0.32)
        else:
            cam, tgt, fov = aim(sh_, 1, 22 - 3 * uu, 0.0, 0, 46, 0.28)
        return shoot("train", cam, tgt, fov, [me], t=t, fx=fx)
    if k == 16:  # 決めた：顔をあげる（決意）→ 窓の外の夕日と横顔
        me = H_(cx=60, fy=FY, cz=8, face="決意", f=1, sit=True, **BK)
        c_, uu = cut(t, T, [0.5])
        if c_ == 0:
            cam, tgt, fov = aim(sh_, 1, 22 - 3 * uu, -0.1, 0, 46, 0.28)
        else:
            cam, tgt, fov = aim(sh_, 1, 30, 1.2, 2, 50, 0.3)
        return shoot("train", cam, tgt, fov, [me], t=t)
    if k == 17:  # 次に帰った日：「60」→「360」に数字が増える
        me = H_(cx=54, fy=FY, cz=ME_Z, face="笑顔", f=1, **BK)
        c_, uu = cut(t, T, [0.35])
        if c_ == 0:
            cam = (66, FY + 34, ME_Z - 16 + 2 * uu); tgt = (50, FY + 24, MOMZ)
            return shoot("home", cam, tgt, 48, [MOM(), me], t=t)
        cam, tgt, fov = aim(mom_h, -1, 30 - 2 * uu, 0.0, 2, 46, 0.4)
        v = 60 + int(300 * ease(min(1, max(0, (uu - 0.15) / 0.55))))
        return shoot("home", cam, tgt, fov, [MOM()], t=t,
                     tg=[(tagp(mom_h), str(v), 1.0, 1.0 + 0.15 * (v == 360), GOLD if v == 360 else PINK)])
    if k == 18:  # 数字は、変えられる：夜の通りで空を見上げる僕（下から）
        me = H_(cx=60, fy=FY, cz=60, face="笑顔", f=-1, **BK)
        z = ease(u)
        cam = lerp((60, FY + 10, 60 - 26), (60, FY + 6, 60 - 40), z); tgt = (60, FY + 30, 60)
        return shoot("night", cam, tgt, 52, [me], t=t)
    if k == 19:  # あなたは？：夜の通り、たくさんの数字。上へ引いていく
        dr, hd = crowd(18, 7, 34, 86, 10, 130, t)
        me = H_(cx=60, fy=FY, cz=60, face="ふつう", f=-1, **BK)
        z = ease(u)
        c1, t1, _ = aim(HEAD(60, FY, 60), -1, 34, 0.0, 6, 52, 0.3)
        cam = lerp(c1, (80, FY + 110, 60 - 70), z); tgt = lerp(t1, (60, FY, 80), z)
        return shoot("night", cam, tgt, 52, dr + [me], t=t, tg=[(p, s, 1.0, 1.0, CYAN) for p, s in hd])


def render_clip(k, out):
    n = int(round(CLIPS[k] * FPS))
    tmp = out[:-4] + '.part.mp4'
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write((np.clip(frame(k, i / FPS), 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
        if i % 30 == 0: print(k, i, flush=True)
    ff.stdin.close()
    if ff.wait() == 0:
        os.replace(tmp, out); print('done', out, flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        ims = []
        for s_ in sys.argv[2].split(','):
            k, t = s_.split(':')
            im = Image.fromarray((np.clip(frame(int(k), float(t)), 0, 1) * 255).astype(np.uint8)).resize((180, 320))
            d = ImageDraw.Draw(im)
            for y in (int(320 * .36), int(320 * .43), int(320 * .68)):
                d.line([(0, y), (180, y)], fill=(255, 0, 0), width=1)
            ims.append(im)
        cols = min(8, len(ims))
        sheet = Image.new('RGB', (180 * cols, 320 * ((len(ims) + cols - 1) // cols)))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % cols) * 180, (i // cols) * 320))
        sheet.save(sys.argv[3] if len(sys.argv) > 3 else 'story_stills.png')
    else:
        os.makedirs('clips_story', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips_story/{k + 1:02d}.mp4')
