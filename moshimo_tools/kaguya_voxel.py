"""もしも「かぐや様は告らせたい」の白銀会長に、ふつうの頭の僕がなったら（パロディ）
マイクラ風3D。原作キャラクターの姿は描かない：相手は声と、画面の外から伸びる手・物だけで出す。
主役（僕）にぐっと寄る／一気に引く を全場面で使う。
使い方: python3 kaguya_voxel.py stills / python3 kaguya_voxel.py 0,1,2"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voxel import Scene, render, particles, smooth, ease, C, f32
from elevator_voxel import person, put, finish, shake

W, H, FPS, RS = 1080, 1920, 30, 3
CLIPS = [5.7, 6.0, 5.5, 3.9, 5.9, 3.1, 6.1, 3.4, 5.1]
FY = 2                  # 床の高さ
PX, PZ = 32, 40         # 僕の立ち位置
R = np.random.default_rng(15)
SLEEVE = (0.12, 0.12, 0.16); HAND = (0.96, 0.8, 0.68)


def lerp(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


def snap(t, t0, d=0.4):
    x = min(1.0, max(0.0, (t - t0) / d)); return 1 - (1 - x) ** 3


def build_room():
    """夕方の生徒会室：木の床、白い壁、大きな窓（夕日）、長机、黒板、本棚。"""
    S = Scene(64, 40, 70)
    c, m = S.col, S.mat
    put(c, m, 0, 64, 0, FY, 0, 70, (0.55, 0.38, 0.22), 1, 0.06)                  # 床
    for z in range(0, 70, 4):
        put(c, m, 0, 64, FY - 1, FY, z, z + 1, (0.48, 0.32, 0.18), 1, 0.03)
    put(c, m, 0, 64, FY, 34, 66, 68, (0.92, 0.9, 0.86), 1, 0.03)                # 奥の壁
    put(c, m, 2, 3, FY, 34, 0, 66, (0.9, 0.88, 0.84), 1, 0.03)                   # 左の壁
    put(c, m, 61, 62, FY, 34, 0, 66, (0.9, 0.88, 0.84), 1, 0.03)                 # 右の壁
    # 奥の大きな窓（夕日）
    m[10:54, FY + 8:FY + 28, 66:68] = 0
    for x in range(10, 54, 11):
        put(c, m, x, x + 1, FY + 8, FY + 28, 66, 68, (0.45, 0.3, 0.2), 1, 0.0)
    put(c, m, 10, 54, FY + 17, FY + 18, 66, 68, (0.45, 0.3, 0.2), 1, 0.0)
    # 黒板（左の壁）
    put(c, m, 3, 4, FY + 10, FY + 22, 20, 46, (0.12, 0.25, 0.18), 1, 0.04)
    # 本棚（右の壁）
    put(c, m, 56, 61, FY, FY + 20, 14, 30, (0.5, 0.33, 0.2), 1, 0.05)
    for y in range(FY + 2, FY + 19, 5):
        for z in range(15, 29, 2):
            put(c, m, 56, 57, y, y + 3, z, z + 1.6, [(0.8, 0.2, 0.2), (0.2, 0.45, 0.85), (0.9, 0.75, 0.2), (0.3, 0.65, 0.35)][(y + z) % 4], 1, 0.03)
    # 長机と椅子
    put(c, m, 18, 46, FY + 7, FY + 8, 48, 58, (0.62, 0.42, 0.25), 1, 0.04)
    for x in (19, 44):
        for z in (49, 56):
            put(c, m, x, x + 1, FY, FY + 7, z, z + 1, (0.4, 0.27, 0.16), 1, 0.0)
    put(c, m, 28, 36, FY + 8, FY + 9, 52, 55, (0.95, 0.95, 0.95), 1, 0.0)          # 書類
    S.base_c, S.base_m = c.copy(), m.copy()

    def sky(d):
        y = np.clip(d[:, 1], -0.2, 1)
        top, hor = C(0.35, 0.3, 0.6), C(1.35, 0.7, 0.35)
        t_ = np.clip(y / 0.5, 0, 1)
        return (hor * (1 - t_[:, None]) + top * t_[:, None]).astype(f32)
    S.sky = sky
    S.sun = np.array([0.1, 0.35, 0.93]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.3, 0.8, 0.5); S.amb = C(0.55, 0.5, 0.55)
    S.lights = [((32, FY + 30, 30), (0.5, 0.45, 0.4), 50)]
    S.fog0, S.fogk = 200, 400
    return S


def build_entrance():
    """雨の昇降口：げた箱、ガラス戸、外は灰色の雨。"""
    S = Scene(64, 40, 70)
    c, m = S.col, S.mat
    put(c, m, 0, 64, 0, FY, 0, 70, (0.62, 0.62, 0.64), 1, 0.05)
    put(c, m, 0, 64, FY, 30, 0, 2, (0.88, 0.88, 0.86), 1, 0.03)
    for x in (6, 14, 50):
        put(c, m, x, x + 6, FY, FY + 18, 4, 14, (0.6, 0.45, 0.3), 1, 0.04)        # げた箱
        for y in range(FY + 2, FY + 18, 4):
            put(c, m, x, x + 6, y, y + 0.5, 3.6, 14, (0.45, 0.32, 0.2), 1, 0.0)
    for x in range(10, 54, 9):                                                     # ガラス戸の枠
        put(c, m, x, x + 1, FY, FY + 22, 50, 51, (0.35, 0.35, 0.38), 1, 0.0)
    put(c, m, 10, 54, FY + 22, FY + 24, 50, 51, (0.35, 0.35, 0.38), 1, 0.0)
    put(c, m, 0, 64, FY + 24, 30, 50, 51, (0.88, 0.88, 0.86), 1, 0.03)
    put(c, m, 0, 64, 0, FY - 0.5, 51, 70, (0.3, 0.3, 0.33), 1, 0.05)               # 外のぬれた地面
    S.base_c, S.base_m = c.copy(), m.copy()
    S.sun = None; S.amb = C(0.6, 0.62, 0.68)
    S.lights = [((32, FY + 26, 25), (0.6, 0.6, 0.6), 40)]
    S.hor = C(0.55, 0.58, 0.62); S.top = C(0.42, 0.45, 0.5); S.fog0, S.fogk = 60, 120
    return S


def build_outside():
    """夕日の校舎を外から：大きな校舎と窓。"""
    S = Scene(90, 60, 110)
    c, m = S.col, S.mat
    put(c, m, 0, 90, 0, 2, 0, 110, (0.33, 0.55, 0.25), 1, 0.08)
    put(c, m, 10, 80, 2, 34, 60, 80, (0.93, 0.9, 0.84), 1, 0.03)
    for y in range(6, 32, 8):
        for x in range(14, 78, 8):
            lit = (x == 38 and y == 22)
            put(c, m, x, x + 5, y, y + 5, 59, 60, (1.6, 1.2, 0.6) if lit else (0.4, 0.5, 0.65), 4 if lit else 3, 0.0)
    put(c, m, 40, 50, 34, 44, 66, 74, (0.93, 0.9, 0.84), 1, 0.03)                 # 時計台
    put(c, m, 43, 47, 38, 42, 65, 66, (0.95, 0.95, 0.9), 1, 0.0)
    S.base_c, S.base_m = c.copy(), m.copy()

    def sky(d):
        y = np.clip(d[:, 1], -0.2, 1)
        t_ = np.clip(y / 0.6, 0, 1)
        return (C(1.4, 0.65, 0.3) * (1 - t_[:, None]) + C(0.3, 0.25, 0.55) * t_[:, None]).astype(f32)
    S.sky = sky
    S.sun = np.array([0.45, 0.45, -0.77]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.3, 0.75, 0.45); S.amb = C(0.5, 0.45, 0.55); S.lights = []
    S.fog0, S.fogk = 120, 300
    return S


_S = {}


def get(k, fn):
    if k not in _S:
        _S[k] = fn()
    return _S[k]


def hand(c, m, x, y, z, item=None):
    """画面の外（右）から伸びてくる手。item='ticket' / None"""
    put(c, m, x, x + 14, y, y + 2.2, z - 1, z + 1, SLEEVE, 1, 0.02)
    put(c, m, x - 2, x, y, y + 2.2, z - 1.2, z + 1.2, HAND, 1, 0.02)
    if item == 'ticket':
        put(c, m, x - 6, x - 1.5, y + 0.8, y + 1.2, z - 2.5, z + 2.5, (1.3, 1.1, 0.4), 4, 0.0)


def qblocks(c, m, x, y, z, n=3, t=0.0):
    Q = ["0110", "1001", "0001", "0010", "0100", "0000", "0100"]
    for q in range(n):
        ox = x + (q - (n - 1) / 2) * 7; oy = y + 1.2 * math.sin(t * 4 + q)
        for r, row in enumerate(Q):
            for k, ch in enumerate(row):
                if ch == "1":
                    put(c, m, ox + 2 - k, ox + 3 - k, oy + 7 - r, oy + 8 - r, z, z + 1, (1.25, 0.82, 0.12), 4, 0.0)


def rain(img, depth, cam, tgt, fov, t, box, n=500, sp=40):
    rg = np.random.default_rng(3)
    x0, x1, y0, y1, z0, z1 = box
    p = np.stack([rg.uniform(x0, x1, n), (rg.uniform(0, 1, n) * (y1 - y0) - sp * t) % (y1 - y0) + y0, rg.uniform(z0, z1, n)], 1)
    for kk in range(3):
        particles(img, depth, cam, tgt, fov, p + np.array([0, kk * 0.6, 0]), np.tile(C(0.85, 0.9, 1.0) * (1 - kk / 3), (n, 1)), 0.1)


def room_shot(t, cam, tgt, fov, pose="stand", look=0, extra=None, grade=(1, 1, 1)):
    S = get('room', build_room)
    c, m = S.base_c.copy(), S.base_m.copy()
    person(c, m, PX, FY, PZ, pose, look=look)
    if extra:
        extra(c, m)
    img, depth = render(S, c, m, cam, tgt, fov, W // RS, H // RS)
    return finish(img, grade=grade)


FACE = (PX, FY + 21, PZ)   # 顔の中心あたり


def frame(k, t):
    T = CLIPS[k]; p = ease(t / T)
    if k == 0:   # 生徒会室で目を覚ます：顔の超アップ → 一気に引いて部屋全体
        z = snap(t, 1.0, 1.6)
        cam = lerp((PX + 0.5, FY + 22, PZ - 28), (PX + 14, FY + 24, PZ - 34), z)
        tgt = lerp((PX, FY + 23, PZ), (PX, FY + 15, PZ + 8), z)
        return room_shot(t, cam, tgt, 46 + 22 * z, look=int(round(math.sin(t * 3))) if t < 1.0 else 0)
    if k == 1:   # ルールを知らない：頭の上に「？」が3つ。まわりを回りながら寄る
        a = -0.6 + 1.0 * p
        d = 30 - 10 * p
        cam = (PX + d * math.sin(a), FY + 24, PZ - d * math.cos(a)); tgt = (PX, FY + 25, PZ)
        return room_shot(t, cam, tgt, 56, extra=lambda c, m: qblocks(c, m, PX, FY + 27, PZ, 3, t))
    if k == 2:   # 画面の外からチケットを持った手 → 僕の顔へズーム
        hx = PX + 22 - 14 * snap(t, 0.3, 0.8)
        z = snap(t, 2.4, 0.9)
        cam = lerp((PX - 4, FY + 20, PZ - 30), (PX - 1, FY + 22, PZ - 30), z); tgt = lerp((PX + 3, FY + 17, PZ - 2), (PX, FY + 23, PZ), z)
        return room_shot(t, cam, tgt, 58 - 12 * z, extra=lambda c, m: hand(c, m, hx, FY + 15, PZ - 4, 'ticket'))
    if k == 3:   # 「弟と行ってきます！」：チケットを受け取ってにっこり → 一気に引く
        z = snap(t, 1.6, 0.6)
        cam = lerp((PX, FY + 21, PZ - 30), (PX + 6, FY + 22, PZ - 44), z); tgt = lerp((PX, FY + 23, PZ), (PX, FY + 14, PZ + 6), z)

        def ex(c, m):
            put(c, m, PX + 4, PX + 9, FY + 18, FY + 18.4, PZ - 2, PZ + 2, (1.3, 1.1, 0.4), 4, 0.0)
        return room_shot(t, cam, tgt, 50 + 14 * z, pose="jump", extra=ex)
    if k == 4 or k == 5:   # 雨の昇降口
        S = get('ent', build_entrance)
        c, m = S.base_c.copy(), S.base_m.copy()
        if k == 4:   # 僕のまわりをぐるっと回る。画面の外から傘を持たない手がそっと見える
            person(c, m, PX, FY, 40, "stand", look=int(round(math.sin(t * 2))))
            a = 0.9 - 1.6 * p
            cam = (PX + 24 * math.sin(a), FY + 22, 40 - 24 * math.cos(a)); tgt = (PX, FY + 21.5, 40)
            fov = 58
        else:        # 傘を押しつけて、雨の中へ全力ダッシュ。残された傘を残して一気に引く
            run = smooth(0.3, T, t)
            pz = 40 + 30 * run
            put(c, m, PX - 7, PX - 6, FY, FY + 12, 38, 39, (0.25, 0.3, 0.6), 1, 0.0)           # 立てかけた傘
            put(c, m, PX - 10, PX - 3, FY + 11, FY + 12, 35, 42, (0.25, 0.3, 0.6), 1, 0.0)
            if pz < 69:
                person(c, m, PX, FY, int(pz), "jump" if int(t * 8) % 2 else "float", look=0)
            z = snap(t, 0.2, 1.2)
            cam = lerp((PX - 4, FY + 20, 12), (PX - 6, FY + 26, 4), z); tgt = lerp((PX, FY + 16, 40), (PX - 2, FY + 12, 50), z)
            fov = 54 + 14 * z
        img, depth = render(S, c, m, cam, tgt, fov, W // RS, H // RS)
        rain(img, depth, cam, tgt, fov, t, (0, 64, FY, 30, 52, 70))
        return finish(img, grade=(0.92, 0.96, 1.05))
    if k == 6:   # 心理テスト：真剣な顔の超アップ（ゆっくり寄る）
        cam = lerp((PX + 3, FY + 22, PZ - 40), (PX + 0.5, FY + 22, PZ - 28), p); tgt = (PX, FY + 23, PZ)
        return room_shot(t, cam, tgt, 52, look=0)
    if k == 7:   # 「ナイフですね」：ドヤ顔 → 画面が揺れて一気に引く
        z = snap(t, 1.4, 0.5)
        cam = lerp((PX, FY + 22, PZ - 28), (PX - 10, FY + 26, PZ - 46), z); tgt = lerp((PX, FY + 23, PZ), (PX, FY + 14, PZ + 8), z)
        if t > 1.4:
            cam, tgt = shake(cam, tgt, 1.2 * max(0.0, 1 - (t - 1.4) / 0.8), t)
        return room_shot(t, cam, tgt, 50 + 16 * z, pose="jump" if t > 1.4 else "stand")
    if k == 8:   # 夕日の校舎を外から：ゆっくり引く
        S = get('out', build_outside)
        c, m = S.base_c.copy(), S.base_m.copy()
        cam = lerp((45, 24, 30), (45, 30, -10), p); tgt = (45, 26, 70)
        img, depth = render(S, c, m, cam, tgt, 62, W // RS, H // RS)
        return finish(img)


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
    if sys.argv[1] == 'stills':
        spec = sys.argv[2] if len(sys.argv) > 2 else '0:0.3,0:4.5,1:3.0,2:1.5,2:5.0,3:0.8,3:3.5,4:3.0,5:0.2,5:2.8,6:4.0,7:0.8,7:3.0,8:3.0'
        ims = []
        for s_ in spec.split(','):
            k, t = s_.split(':')
            im = Image.fromarray((frame(int(k), float(t)) * 255).astype(np.uint8)).resize((180, 320))
            d = ImageDraw.Draw(im)
            for y in (int(320 * .36), int(320 * .43), int(320 * .68)):
                d.line([(0, y), (180, y)], fill=(255, 0, 0), width=1)
            ims.append(im)
        sheet = Image.new('RGB', (180 * 7, 320 * ((len(ims) + 6) // 7)))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % 7) * 180, (i // 7) * 320))
        sheet.save('kaguya_stills.png')
    else:
        os.makedirs('clips', exist_ok=True)
        for k in [int(x) for x in sys.argv[1].split(',')]:
            render_clip(k, f'clips/{k + 1:02d}.mp4')
