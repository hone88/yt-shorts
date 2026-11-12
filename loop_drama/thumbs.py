"""ガクチカ・ループ 第1〜9話のサムネイル（1080×1920）。python3 thumbs.py [話数...] → out_thumbs/第N話_サムネ.png
共通：上は動画と同じ時計パネル（2026年12月5日（土）20:00・大学1年・残りループ n）、下に大きな「第N話／タイトル」。
絵は各話の動画と同じ3D（キャラクター定義書）で、その話を象徴する場面。"""
import math, os, sys
from PIL import Image
import characters as C
import ep1b as O
import ep2 as Q
import ep3 as R
import ep4 as F
import ep5 as V5
import ep6 as S6
import ep7 as S7
import ep8 as S8
import ep9 as S9
import engine as E
from g3d import Camera, render

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f"{HERE}/out_thumbs"
W, H = 1080, 1920

EP = {   # 話: (タイトル, 残りループ)
    1: ("ガクチカ、ゼロ", 3), 2: ("説明会", 3), 3: ("何、聞かれるんだ", 3), 4: ("布団から、出られない。", 3),
    5: ("自己PRが、空欄。", 2), 6: ("キックオフ", 2), 7: ("名刺の渡し方", 2), 8: ("それで、何を考えましたか？", 2),
    9: ("全部、消えた。", 1), 10: ("今度は、こっちから", 1),
}


def scene(n):
    if n == 1:    # 面接で答えられず、世界が止まる。トケイ登場
        tk = C.tokei_boxes((3.62, 2.05, 1.62), 0.4, "eyes", 0.75, 0.35)
        return S8.iv_img(0.0, "shock", "two", 0, tk=tk, freeze=1.0)
    if n == 2:    # 説明会の案内。ベッドでノートパソコン
        return Q.room_img(Q.kanata_bed("open"), Q.face_cam(1.0, 2.0, 0.35), glow=0.6)
    if n == 3:    # 1次選考会。緊張するカナタ
        return R.meet_img(R.cam_kanata(1.0, 2.0), kexpr="blank")
    if n == 4:    # 布団から出られない
        return F.bed_img(1.0, 2.0, "blank", dark=0.0)
    if n == 5:    # 自己PR欄が空白
        return Q.room_img(V5.kanata_pc("blank"), V5.bed_cam(1.0, 2.0, 0.2))
    if n == 6:    # キックオフ：同じ班のハルトとハイタッチ
        tx, ty = S6.TABLES[4]
        k = S6.kanata((tx - 0.2, ty - 0.95, 0), 0.0, "smile", armL=1.4, armR=1.4, lean=0.2)
        h = S6.haruto((tx - 0.2, ty + 0.95, 0), math.pi, "smile", armL=1.4, armR=1.4, lean=0.25)
        cam = Camera((11.2, ty, 2.0), (tx - 0.2, ty, 1.15), 46)
        img, _ = render(S6.HALL + S6.crowd(1.0, tables=S6.BACK) + k.boxes() + h.boxes(), cam, S6.BG_HALL)
        return img.convert("RGBA")
    if n == 7:    # 名刺をまた逆さまに
        return S7.visit_img(1.0, 2.0, "face", "shock", card=True)
    if n == 8:    # 深掘りに答えられない
        return S8.iv_img(1.0, "blank", "close", 0.7)
    if n == 9:    # ハルトに「…えっと、誰？」
        h = S9.haruto(S9.HB, math.pi + 0.5, "normal", sit=True, head_yaw=-0.35)
        k = S9.kanata(S9.KB, -math.pi / 2 + 0.25, "shock")
        img, _ = S9.campus_img(h.boxes() + k.boxes(), S9.cam_k_face(0.5))
        return img
    if n == 10:   # カナタから、ハルトを誘う
        h = S9.haruto(S9.HB, math.pi + 0.5, "normal", sit=True, head_yaw=-0.35, head_pitch=0.08)
        k = S9.kanata(S9.KB, -math.pi / 2 + 0.25, "open", armR=0.5)
        img, _ = S9.campus_img(h.boxes() + k.boxes(), Camera((2.7, -1.4, 2.05), (2.6, 3.7, 1.3), 40))
        return img


def title(img, n, name):
    f1 = E.fit_text([f"第{n}話"], 170, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=16)
    lines = [name]
    size = 150
    natural = E.text_block(lines, size, fill=(255, 255, 255), stroke=(8, 10, 24), sw=16)
    if natural.width > 1000 * 150 / 118 and "、" in name:   # 1行だと小さくなりすぎる長いタイトルは「、」で2行に
        a, b = name.split("、", 1)
        lines = [a + "、", b]
    im2 = E.fit_text(lines, size, 1000, fill=(255, 255, 255), stroke=(8, 10, 24), sw=16)
    y2 = 1560 if len(lines) == 1 else 1500        # Instagramのグリッド（3:4）で切れない高さに収める
    y1 = y2 - im2.height // 2 - f1.height // 2 + 10
    E.paste_center(img, f1, 540, y1, 1.0)
    E.paste_center(img, im2, 540, y2, 1.0)


def make(n):
    name, loop = EP[n]
    img = scene(n).convert("RGBA")
    O.clock_big(img, "2026年12月5日（土）", "20:00", grade="大学1年")
    O.counter(img, loop)
    title(img, n, name)
    os.makedirs(OUT, exist_ok=True)
    p = f"{OUT}/第{n}話_サムネ.png"
    img.convert("RGB").save(p)
    return p


if __name__ == "__main__":
    ns = [int(a) for a in sys.argv[1:]] or list(EP)
    for n in ns:
        print(make(n))
