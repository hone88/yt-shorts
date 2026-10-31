"""各場面のブロックの世界と動き。make(name, dur) で Scene を返す。"""
import math, random
from engine import Person, lerp, ease, cull

SKY_DAY = ((120, 190, 245), (205, 235, 255))
SKY_WARM = ((255, 190, 140), (255, 236, 200))
SKY_SNOW = ((170, 200, 230), (230, 240, 250))
SKY_ROOM = ((52, 64, 104), (100, 120, 170))
SKY_NIGHT = ((30, 36, 80), (90, 80, 150))


class Scene:
    def __init__(self, dur):
        self.dur = dur
        self.static = []
        self.people = []
        self.sky = SKY_DAY
        self.clouds = True
        self.snow = False
        self.keys = []          # [(時刻 0..1, (s, cx, cy, cz))]
        self.dyn = lambda t: []
        self.update = lambda t: None

    def cam(self, t):
        u = t / self.dur
        ks = self.keys
        if u <= ks[0][0]:
            return ks[0][1]
        for (t0, k0), (t1, k1) in zip(ks, ks[1:]):
            if u <= t1:
                if t1 - t0 < 1e-6:
                    return k1
                e = ease((u - t0) / (t1 - t0))
                return tuple(lerp(a, b, e) for a, b in zip(k0, k1))
        return ks[-1][1]

    def finish(self):
        self.static = cull(self.static)
        return self


# ---------- 部品 ----------
def island(S, x0, y0, w, d, top="grass", side_depth=2, z=0):
    for x in range(x0, x0 + w):
        for y in range(y0, y0 + d):
            S.append((x, y, z, 1, top))
            for k in range(1, side_depth + 1):
                S.append((x, y, z - k, 1, "dirt" if top == "grass" else ("stone" if top not in ("snow",) else "snow")))


def setb(S, x, y, z, mat, sz=1):
    S.append((x, y, z, sz, mat))


def box(S, x0, y0, z0, w, d, h, mat):
    for x in range(x0, x0 + w):
        for y in range(y0, y0 + d):
            for z in range(z0, z0 + h):
                S.append((x, y, z, 1, mat))


def replace_top(S, x, y, mat, z=0):
    for i, b in enumerate(S):
        if b[0] == x and b[1] == y and b[2] == z:
            S[i] = (x, y, z, 1, mat)


def building(S, x0, y0, w, d, h, wall="white", roof="gray", win="glass", z0=1):
    for z in range(z0, z0 + h):
        for x in range(x0, x0 + w):
            for y in range(y0, y0 + d):
                edge_x = x == x0 + w - 1
                edge_y = y == y0 + d - 1
                if not (x in (x0, x0 + w - 1) or y in (y0, y0 + d - 1)):
                    continue
                m = wall
                if (edge_x and 0 < y - y0 < d - 1 and (y - y0) % 2 == 1 and z % 2 == 0) or \
                   (edge_y and 0 < x - x0 < w - 1 and (x - x0) % 2 == 1 and z % 2 == 0):
                    m = win
                S.append((x, y, z, 1, m))
    for x in range(x0, x0 + w):
        for y in range(y0, y0 + d):
            S.append((x, y, z0 + h, 1, roof))


def tree(S, x, y, h=2, z0=1, leaves="leaves"):
    for z in range(z0, z0 + h):
        S.append((x, y, z, 1, "log"))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            S.append((x + dx, y + dy, z0 + h, 1, leaves))
    S.append((x, y, z0 + h + 1, 1, leaves))


def glyph(rows, x, y, z, mat="yellow", px=0.22, plane="x"):
    """文字の形をブロックで（? や ! などの記号だけ）。plane='x' なら x 方向に並べる。"""
    out = []
    n = len(rows)
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            if ch == "#":
                if plane == "x":
                    out.append((x + c * px, y, z + (n - 1 - r) * px, px, mat))
                else:
                    out.append((x, y + c * px, z + (n - 1 - r) * px, px, mat))
    return out


QMARK = [" ## ", "#  #", "   #", "  # ", "    ", "  # "]
EXCL = ["#", "#", "#", "#", " ", "#"]
ARROW_UP = ["  #  ", " ### ", "#####", " ### ", " ### ", " ### "]


def walk_to(p, a, b, t, t0, t1, speed_phase=9.0):
    """t0〜t1 の間に a→b へ歩かせる。"""
    if t <= t0:
        p.x, p.y = a
        p.walk = 0
    elif t >= t1:
        p.x, p.y = b
        p.walk = 0
    else:
        u = (t - t0) / (t1 - t0)
        p.x, p.y = lerp(a[0], b[0], u), lerp(a[1], b[1], u)
        p.walk = 1
        p.phase = t * speed_phase
    dx, dy = b[0] - a[0], b[1] - a[1]
    if t0 < t < t1:
        if abs(dx) >= abs(dy):
            p.facing = "x" if dx > 0 else "-x"
        else:
            p.facing = "y" if dy > 0 else "-y"


STUDENT_STYLES = [
    ("t_orange", "jeans", "hair", "skin", False),
    ("t_blue", "jeans", "hair2", "skin", False),
    ("t_pink", "skirt", "hair", "skin", True),
    ("t_green", "jeans", "hair", "skin2", False),
    ("t_purple", "skirt", "hair2", "skin", True),
    ("t_yellow", "jeans", "hair", "skin", False),
]


def student(x, y, i=0, facing="x", scale=1.0, z=1):
    sh, pa, ha, sk, sr = STUDENT_STYLES[i % len(STUDENT_STYLES)]
    return Person(x, y, z, facing, sh, pa, ha, sk, scale, sr)


def politician(x, y, facing="x", z=1, hair="hair3"):
    return Person(x, y, z, facing, "suit", "suit", hair, "skin", 1.0)


def kid(x, y, i=0, facing="x", z=1):
    cols = ["t_red", "t_yellow", "t_green", "t_blue", "t_pink", "t_purple", "t_orange"]
    p = Person(x, y, z, facing, cols[i % len(cols)], "jeans" if i % 2 == 0 else "skirt", "hair" if i % 3 else "hair2", "skin" if i % 4 else "skin2", 0.62, i % 2 == 1)
    return p


def town(S, n=16, seed=3, road_y=(7, 8), tall=False, front=True):
    rnd = random.Random(seed)
    island(S, 0, 0, n, n)
    for x in range(n):
        for y in road_y:
            replace_top(S, x, y, "road")
    for x in range(0, n, 3):
        replace_top(S, x, road_y[0], "line")
    walls = ["white", "cream", "brick", "gray", "white", "cream"]
    roofs = ["red", "navy", "darkwood", "gray", "blue"]
    for x0 in range(1, n - 3, 4):
        h = rnd.randint(3, 6 if tall else 4)
        building(S, x0, 1, 3, 3, h, rnd.choice(walls), rnd.choice(roofs))
        h = rnd.randint(2, 4)
        if x0 + 3 < n and front and road_y[1] + 5 <= n:
            building(S, x0, road_y[1] + 2, 3, 3, h, rnd.choice(walls), rnd.choice(roofs))
    for x in (0, n - 2):
        tree(S, x + 1, road_y[1] + 6 if road_y[1] + 6 < n - 1 else n - 2, 2)


def cta_world(S, sc, accent="orange"):
    island(S, 0, 0, 12, 12)
    for (x, y) in ((1, 1), (10, 2), (2, 10)):
        tree(S, x, y, 2, leaves="pink" if (x + y) % 2 else "leaves")
    for x in range(3, 9):
        for y in range(3, 9):
            if (x + y) % 2 == 0:
                replace_top(S, x, y, "sand")
    ppl = [student(4.5 + i * 1.2, 7.0 - i * 0.4, i, "x" if i % 2 else "y") for i in range(5)]
    sc.people += ppl

    def upd(t):
        for i, p in enumerate(ppl):
            ph = t * 6 + i
            p.jump = max(0, math.sin(ph)) * 0.35
            p.arm_up = (0.9 if i % 2 else max(0, math.sin(ph * 0.5)), 0.0 if i % 2 else 0.9)
    sc.update = upd

    def dyn(t):
        bob = math.sin(t * 4) * 0.3
        out = []
        cx, cy, z0, m = 6.6, 5.6, 3.6 + bob, 0.4
        for k in range(4):
            for dx in (0, 1):
                for dy in (0, 1):
                    out.append((cx + (dx - 0.5) * m, cy + (dy - 0.5) * m, z0 + k * m, m, accent))
        for lvl, r_ in enumerate((2, 1, 0)):
            for dx in range(-r_, r_ + 2):
                for dy in range(-r_, r_ + 2):
                    out.append((cx + (dx - 0.5) * m, cy + (dy - 0.5) * m, z0 + (4 + lvl) * m, m, accent))
        return out
    sc.dyn = dyn


# ---------- 場面 ----------
def make(name, dur, variant=0):
    sc = Scene(dur)
    S = sc.static
    P = sc.people

    if name == "city_walk":
        town(S, 16)
        p = student(1, 7.5, 0, "x")
        P.append(p)
        def upd(t):
            walk_to(p, (1, 7.6), (1 + dur * 1.4, 7.6), t, 0, dur, 7)
        sc.update = upd
        sc.keys = [(0, (42, 6, 8, 3)), (1, (56, 1 + dur * 1.4, 7.6, 2.6))]
        def dyn(t):
            ph = (t * 1.2) % 1
            return glyph(QMARK, p.x + 0.1, p.y - 0.4, 3.0 + 0.15 * math.sin(t * 5), "white", 0.16)
        sc.dyn = dyn

    elif name in ("two_paths", "two_doors"):
        island(S, 0, 0, 16, 16)
        # 道：真ん中から左右へ
        for k in range(8):
            replace_top(S, 7 + 0, 15 - k, "sand")
        for k in range(8):
            replace_top(S, 7 - k, 8, "sand")
            replace_top(S, 7, 8 - k, "sand")
        # 議会っぽい白い建物（左奥）
        building(S, 0, 4, 5, 4, 4, "white", "gray", "glass")
        box(S, 1, 5, 5, 3, 2, 1, "gold")
        for x in (0, 2, 4):
            setb(S, x, 8, 1, "white"); setb(S, x, 8, 2, "white")
        # NPOの木の家（右奥）
        building(S, 5, 0, 4, 4, 3, "wood", "red", "glass")
        tree(S, 11, 2, 2)
        tree(S, 13, 9, 2, leaves="pink")
        tree(S, 2, 13, 2)
        st = student(7.5, 13.5, 0, "-y")
        pol = politician(3.5, 9.5, "x")
        kids = [kid(9.5 + i * 0.9, 4.5 + (i % 2) * 0.8, i, "y") for i in range(3)]
        npo = Person(10.6, 6.4, 1, "-x", "t_green", "jeans", "hair2", "skin", 1.0)
        P += [st, pol, npo] + kids
        if name == "two_paths":
            def upd(t):
                walk_to(st, (7.5, 13.8), (7.5, 9.6), t, 0, dur * 0.8, 8)
                pol.arm_up = (0.8 if (t % 1.2) < 0.6 else 0.4, 0)
                npo.arm_up = (0, 0.8 if (t % 1.2) > 0.6 else 0.4)
                for i, k in enumerate(kids):
                    k.jump = max(0, math.sin(t * 7 + i)) * 0.25
            sc.update = upd
            sc.keys = [(0, (70, 7.5, 12.5, 1.5)), (0.75, (40, 7.5, 8, 1.6)), (1, (38, 7.5, 8, 1.6))]
        else:
            def upd(t):
                h = dur / 2
                if t < h:
                    walk_to(st, (6.2, 8.5), (3.8, 8.5), t, 0, h * 0.8, 8)
                    walk_to(pol, (3.5, 9.5), (3.5, 9.5), t, 0, 1)
                    pol.facing = "y"; pol.arm_up = (0.7, 0)
                else:
                    walk_to(st, (7.5, 6.5), (8.6, 5.6), t, h, h + h * 0.6, 8)
                    for i, k in enumerate(kids):
                        k.jump = max(0, math.sin(t * 7 + i)) * 0.3
                    npo.arm_up = (0.8, 0)
            sc.update = upd
            sc.keys = [(0, (58, 3.8, 8.0, 3.2)), (0.48, (60, 3.8, 8.0, 3.2)), (0.5, (60, 9.0, 5.0, 2.4)), (1, (66, 9.2, 5.0, 2.2))]

    elif name == "map_japan":
        sc.sky = ((70, 150, 230), (170, 220, 250))
        # 海
        for x in range(0, 19):
            for y in range(0, 21):
                S.append((x, y, -1, 1, "water"))
        # 日本っぽい島の並び（斜め）
        rnd = random.Random(7)
        spots = []
        chain = [(2, 17, 2, 2), (4, 14, 3, 3), (7, 11, 4, 3), (10, 8, 3, 3), (12, 5, 2, 3), (14, 1, 4, 3)]
        for (x0, y0, w, d) in chain:
            island(S, x0, y0, w, d, side_depth=1)
            for x in range(x0, x0 + w):
                for y in range(y0, y0 + d):
                    spots.append((x, y))
        rnd.shuffle(spots)
        spots = spots[:32]
        def dyn(t):
            out = []
            for i, (x, y) in enumerate(spots):
                tt = t - 0.1 - i * (dur * 0.6 / 32)
                if tt <= 0:
                    continue
                h = min(1, tt / 0.3)
                out.append((x + 0.25, y + 0.25, 1, 0.5 * h + 0.01, "gold"))
                out.append((x + 0.3, y + 0.3, 1 + 0.5 * h, 0.4, "lamp"))
            return out
        sc.dyn = dyn
        sc.keys = [(0, (66, 9, 9.5, 0)), (1, (52, 9, 9.5, 0))]

    elif name == "hiroshima":
        sc.sky = SKY_DAY
        n = 18
        for x in range(n):
            for y in range(n):
                river = (x in (5,) or x in (11, 12) or y == 12)
                S.append((x, y, 0, 1, "water" if river else "grass"))
                S.append((x, y, -1, 1, "water" if river else "dirt"))
        for y in range(n):
            pass
        # 橋
        for x in (5, 11, 12):
            setb(S, x, 6, 1, "darkwood")
        for y in (12,):
            setb(S, 3, y, 1, "darkwood"); setb(S, 8, y, 1, "darkwood"); setb(S, 15, y, 1, "darkwood")
        rnd = random.Random(11)
        for (x0, y0) in ((0, 0), (1, 7), (7, 1), (13, 1), (14, 7), (0, 14), (7, 14), (14, 14)):
            building(S, x0 + (0 if x0 else 1), y0 + 1, 3, 3, rnd.randint(2, 4) if y0 < 14 else 1, rnd.choice(["white", "cream", "gray"]), rnd.choice(["navy", "red", "gray"]))
        tree(S, 2, 5, 2)
        ppl = [student(6.5 + i * 0.8, 9.5 + (i % 2) * 0.6, i, "x") for i in range(3)]
        pol = politician(9.6, 9.0, "-x")
        npo = Person(9.6, 10.4, 1, "-x", "t_green", "jeans", "hair2", "skin")
        P += ppl + [pol, npo]
        def upd(t):
            for i, p in enumerate(ppl):
                p.arm_up = (0.6 if (t * 2 + i) % 2 < 1 else 0, 0)
            pol.arm_up = (0, 0.7 if t % 1.4 < 0.7 else 0)
        sc.update = upd
        def dyn(t):
            out = []
            # つなぐ光の線（学生⇄議員・NPO）
            for k in range(6):
                u = ((t * 0.8 + k / 6) % 1)
                out.append((lerp(7.4, 9.4, u), lerp(9.8, 9.7, u), 3.0 + math.sin(u * math.pi) * 0.8, 0.22, "gold"))
            return out
        sc.dyn = dyn
        sc.keys = [(0, (36, 9, 9, 0.5)), (0.5, (40, 9, 9, 0.5)), (1, (52, 8.4, 9.8, 1.6))]

    elif name in ("calendar", "calendar_free"):
        sc.sky = SKY_WARM if name == "calendar" else SKY_DAY
        # 2月(4週)と3月(5週) = 9行×7列
        cols, rows = 7, 9
        island(S, -1, -1, cols + 2, rows + 3, top="grass", side_depth=1)
        tiles = [(c, r) for r in range(rows) for c in range(cols)]
        for (c, r) in tiles:
            setb(S, c, r, 1, "white" if r < 4 else "cream")
        p = student(0.5, 0.5, 0, "x", z=2)
        P.append(p)
        rnd = random.Random(5)
        if name == "calendar":
            lit = tiles[:59]
            def dyn(t):
                k = int(min(1, t / (dur * 0.85)) * len(lit))
                return [(c, r, 1.0, 1, "orange" if r < 4 else "yellow") for (c, r) in lit[:k]]
            def upd(t):
                k = min(1, t / (dur * 0.85)) * (len(lit) - 1)
                i = int(k)
                c, r = lit[i]
                p.x, p.y = c + 0.5, r + 0.5
                p.facing = "x"
                p.jump = abs(math.sin(k * math.pi)) * 0.4
            sc.keys = [(0, (68, 2, 2, 1)), (1, (50, 3.5, 4.5, 1))]
        else:
            # 週に3〜4日だけ光る
            visits = []
            for r in range(rows):
                days = sorted(rnd.sample(range(cols), 3 if r % 2 else 4))
                visits += [(c, r) for c in days]
            def dyn(t):
                k = int(min(1, t / (dur * 0.9)) * len(visits))
                return [(c, r, 1.0, 1, "orange") for (c, r) in visits[:k]]
            def upd(t):
                k = min(1, t / (dur * 0.9)) * (len(visits) - 1)
                i = int(k)
                c0, r0 = visits[i]
                c1, r1 = visits[min(i + 1, len(visits) - 1)]
                u = k - i
                p.x, p.y = lerp(c0, c1, u) + 0.5, lerp(r0, r1, u) + 0.5
                p.jump = math.sin(u * math.pi) * 0.6
                p.facing = "x" if c1 >= c0 else "-x"
            sc.keys = [(0, (52, 3.5, 4.5, 1)), (1, (56, 3.5, 5.0, 1))]
        sc.update = upd
        sc.dyn = dyn

    elif name == "cta":
        cta_world(S, sc, "orange" if variant % 2 == 0 else "yellow")
        sc.sky = SKY_WARM
        sc.keys = [(0, (70, 6, 6, 2)), (1, (60, 6, 6, 2))]

    elif name == "car_ride":
        island(S, 0, 0, 22, 9)
        for x in range(22):
            for y in (3, 4, 5):
                replace_top(S, x, y, "road")
            if x % 3 == 0:
                replace_top(S, x, 4, "line")
        rnd = random.Random(2)
        for x0 in range(0, 20, 4):
            building(S, x0, 0, 3, 2, rnd.randint(2, 4), rnd.choice(["white", "cream", "brick"]), rnd.choice(["navy", "red"]))
            for k in range(2):
                setb(S, x0 + 1 + k, 7, 1, "leaves")
        drv = politician(0, 0, "x", z=1.15)
        stu = student(0, 0, 0, "x", z=1.15)
        P += [drv, stu]
        def car_x(t):
            return 1 + t * 2.2
        def upd(t):
            x = car_x(t)
            drv.x, drv.y = x + 0.9, 3.95
            stu.x, stu.y = x + 0.9, 4.75
            stu.arm_up = (0, 0.8 if (t % 1.6) < 0.8 else 0)
        sc.update = upd
        def dyn(t):
            x = car_x(t)
            out = []
            # 車体（0.5ブロック単位）
            for i in range(5):
                for j in range(3):
                    out.append((x + i * 0.5, 3.6 + j * 0.5, 1.15, 0.5, "navy"))
                    if i in (0, 4):
                        out.append((x + i * 0.5, 3.6 + j * 0.5, 1.65, 0.5, "navy"))
            for j in range(3):
                out.append((x + 2.0, 3.6 + j * 0.5, 2.15, 0.5, "glass"))
            for (wx, wy) in ((0.2, 3.5), (1.9, 3.5), (0.2, 4.95), (1.9, 4.95)):
                out.append((x + wx, wy, 1.0, 0.35, "black"))
            out.append((x + 2.45, 3.7, 1.4, 0.2, "lamp"))
            out.append((x + 2.45, 4.6, 1.4, 0.2, "lamp"))
            return out
        sc.dyn = dyn
        sc.keys = [(0, (58, car_x(0) + 1.5, 4.5, 2.2)), (1, (64, car_x(dur) + 1.5, 4.5, 2.2))]

    elif name in ("assembly_alone", "assembly_guide"):
        sc.sky = SKY_ROOM
        sc.clouds = False
        n = 14
        island(S, 0, 0, n, n, top="wood", side_depth=1)
        for x in range(n):
            for z in range(1, 6):
                setb(S, x, -1, z, "cream" if z < 5 else "darkwood")
        for y in range(n):
            for z in range(1, 6):
                setb(S, -1, y, z, "cream" if z < 5 else "darkwood")
        # 議長席・演台（奥）
        box(S, 4, 0, 1, 6, 1, 2, "darkwood")
        setb(S, 6, 2, 1, "darkwood"); setb(S, 6, 2, 2, "darkwood")
        # 議席（手前に段々）
        for row in range(3):
            y = 5 + row * 2
            for x in range(1, 12):
                if x == 6:
                    continue
                setb(S, x, y, 1, "darkwood")
                for z in range(row):
                    setb(S, x, y + 1, 1 + z, "wood") if False else None
        # 傍聴席（いちばん手前・一段高い）
        box(S, 0, 11, 1, n, 3, 1, "carpet")
        for x in range(n):
            setb(S, x, 11, 2, "darkwood")
        speaker = politician(6.5, 3.4, "y", hair="hair")
        members = []
        for row in range(3):
            for i, x in enumerate((1.5, 3.5, 8.5, 10.5)):
                members.append(Person(x, 5.0 + row * 2 + 1.0, 1, "-y", "suit", "suit", ["hair", "hair3", "hair2"][(row + i) % 3], "skin"))
        st = student(5.5, 12.6, 0, "-y", z=2)
        P += [speaker, st] + members
        guide = None
        if name == "assembly_guide":
            guide = politician(6.6, 12.6, "-x", z=2)
            P.append(guide)
        def upd(t):
            speaker.arm_up = (0.6 + 0.3 * math.sin(t * 5), 0)
            for i, m_ in enumerate(members):
                m_.bob = 0.03 * math.sin(t * 3 + i)
            if guide:
                guide.facing = "-x" if (t % 2) < 1.2 else "-y"
                guide.arm_up = (0.7 if guide.facing == "-y" else 0, 0)
                st.facing = "x" if (t % 2) < 1.2 else "-y"
                st.arm_up = (0, 0.8) if t > dur * 0.55 else (0, 0)
        sc.update = upd
        def dyn(t):
            if name == "assembly_alone":
                out = []
                for k in range(3):
                    tt = t - k * 0.6
                    if tt > 0:
                        out += glyph(QMARK, 5.3 + (k - 1) * 0.8, 12.4, 3.4 + (k % 2) * 0.4 + 0.1 * math.sin(t * 4 + k), "yellow", 0.13)
                return out
            if t > dur * 0.4:
                return glyph(EXCL, 5.55, 12.4, 3.6 + 0.1 * math.sin(t * 6), "yellow", 0.15)
            return []
        sc.dyn = dyn
        if name == "assembly_alone":
            sc.keys = [(0, (38, 6, 7, 1)), (1, (60, 5.5, 11, 2))]
        else:
            sc.keys = [(0, (66, 6, 12.2, 2.5)), (0.48, (66, 6, 12.2, 2.5)), (0.5, (44, 6, 8, 1.5)), (1, (40, 6, 7.5, 1.5))]

    elif name == "company":
        island(S, 0, 0, 16, 14)
        for y in range(14):
            for x in (8, 9):
                replace_top(S, x, y, "stone")
        building(S, 2, 1, 6, 5, 9, "glass", "gray", "white")
        building(S, 10, 1, 5, 4, 6, "gray", "navy", "glass")
        tree(S, 2, 11, 2); tree(S, 4, 12, 2, leaves="pink")
        exe = Person(8.0, 6.6, 1, "y", "suit", "suit", "hair3", "skin")
        hr = Person(7.1, 6.8, 1, "y", "coat_w", "skirt", "hair", "skin", 1.0, True)
        st = student(8.5, 13, 0, "-y")
        pol = politician(9.4, 13, "-y")
        P += [exe, hr, st, pol]
        def upd(t):
            walk_to(st, (8.5, 13.2), (8.4, 8.0), t, 0, dur * 0.55, 8)
            walk_to(pol, (9.5, 13.4), (9.5, 8.4), t, 0, dur * 0.55, 8)
            if t > dur * 0.6:
                st.facing = "-y"
                k = 0.5 + 0.5 * math.sin(t * 9)
                st.arm_up = (0.35 * k + 0.25, 0)
                exe.arm_up = (0, 0.35 * k + 0.25)
                hr.bob = 0.04 * math.sin(t * 4)
        sc.update = upd
        sc.keys = [(0, (38, 8, 7, 4)), (0.5, (44, 8.5, 9, 3)), (1, (64, 8.3, 7.8, 2.2))]

    elif name == "greeting_route":
        island(S, 0, 0, 18, 18)
        path = [(1, 16), (1, 9), (8, 9), (8, 2), (16, 2), (16, 9), (11, 9), (11, 16), (16, 16)]
        cells = []
        for (a, b) in zip(path, path[1:]):
            steps = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
            for k in range(steps + 1):
                x = a[0] + (b[0] - a[0]) * k // steps
                y = a[1] + (b[1] - a[1]) * k // steps
                cells.append((x, y))
                replace_top(S, x, y, "sand")
        offices = [(2, 11), (3, 6), (5, 0), (10, 3), (13, 4), (12, 11), (13, 13)]
        rnd = random.Random(4)
        for (x0, y0) in offices:
            building(S, x0, y0, 2, 2, rnd.randint(2, 3), rnd.choice(["white", "cream", "brick"]), rnd.choice(["red", "navy", "darkwood"]))
        tree(S, 5, 14, 2); tree(S, 15, 6, 1, leaves="pink")
        st = student(1.5, 16.5, 0, "-y")
        pol = politician(1.5, 16.5, "-y")
        P += [st, pol]
        L = len(cells)
        def pos(u):
            k = u * (L - 1)
            i = int(k)
            j = min(i + 1, L - 1)
            f = k - i
            return (lerp(cells[i][0], cells[j][0], f) + 0.5, lerp(cells[i][1], cells[j][1], f) + 0.5), cells[j], cells[i]
        def upd(t):
            u = min(1, t / (dur * 0.95))
            for p_, lag in ((pol, 0.0), (st, 0.03)):
                (x, y), c1, c0 = pos(max(0, u - lag))
                p_.x, p_.y = x, y
                p_.walk = 1 if u < 1 else 0
                p_.phase = t * 11
                dx, dy = c1[0] - c0[0], c1[1] - c0[1]
                if dx or dy:
                    p_.facing = ("x" if dx > 0 else "-x") if dx else ("y" if dy > 0 else "-y")
        sc.update = upd
        def dyn(t):
            u = min(1, t / (dur * 0.95))
            out = []
            for i, (x0, y0) in enumerate(offices):
                lit = u > (i + 0.6) / (len(offices) + 0.3)
                out.append((x0 + 0.5, y0 + 0.5, 5.2 if True else 0, 0.8, "gold" if lit else "gray"))
            return out
        sc.dyn = dyn
        sc.keys = [(0, (36, 9, 9, 1)), (1, (38, 9, 9, 1))]

    elif name in ("talk_table", "advisors", "team_desk"):
        sc.sky = SKY_ROOM if name != "team_desk" else ((60, 90, 150), (140, 170, 220))
        sc.clouds = False
        island(S, 0, 0, 12, 12, top="wood", side_depth=1)
        for x in range(12):
            for z in range(1, 5):
                setb(S, x, -1, z, "cream" if not (z in (2, 3) and x % 3 == 1) else "glass")
        for y in range(12):
            for z in range(1, 5):
                setb(S, -1, y, z, "cream")
        box(S, 3, 4, 1, 6, 3, 1, "white")   # 机
        setb(S, 1, 1, 1, "leaves"); setb(S, 1, 1, 2, "leaves")
        papers = [(3.3 + i * 1.3, 4.6 + (i % 2) * 0.9) for i in range(4)]
        if name == "talk_table":
            left = [politician(5.5, 3.2, "y")]
            right = [student(3.8 + i * 1.5, 7.9, i, "-y") for i in range(3)]
        elif name == "advisors":
            left = [politician(4.8, 3.2, "y"), Person(6.6, 3.2, 1, "y", "t_green", "jeans", "hair2", "skin")]
            right = [student(3.8 + i * 1.5, 7.9, i + 1, "-y") for i in range(3)]
        else:
            left = [student(4.4, 3.2, 3, "y"), student(6.6, 3.2, 4, "y")]
            right = [student(5.5, 7.9, 0, "-y")]
        P += left + right
        def upd(t):
            for i, p_ in enumerate(left):
                p_.arm_up = (max(0, math.sin(t * 3 + i * 1.7)) * 0.6, 0)
                p_.bob = 0.02 * math.sin(t * 5 + i)
            for i, p_ in enumerate(right):
                p_.bob = 0.03 * abs(math.sin(t * 4 + i))
                if name != "talk_table" or i == 1:
                    p_.arm_up = (0, 0.8 if (t + i) % 3 < 1 else 0)
        sc.update = upd
        def dyn(t):
            out = []
            for i, (x, y) in enumerate(papers):
                tt = t - i * 0.35 if name == "team_desk" else 1
                if tt > 0:
                    out.append((x, y, 2 + max(0, 0.15 - tt) * 3, 0.5, "paper"))
            if name in ("team_desk", "advisors"):
                for i, p_ in enumerate(right if name == "advisors" else left + right):
                    if (t * 1.5 + i) % 3 < 1.2:
                        out.append((p_.x - 0.18, p_.y - 0.18, 3.2 + 0.1 * math.sin(t * 6), 0.36, "lamp"))
            return out
        sc.dyn = dyn
        sc.keys = [(0, (60, 6, 5.5, 1.8)), (1, (74, 6, 5.6, 2))]

    elif name in ("kids_listen", "gakudo"):
        sc.sky = SKY_DAY if name == "kids_listen" else ((250, 210, 150), (255, 240, 210))
        sc.clouds = name == "kids_listen"
        if name == "kids_listen":
            island(S, 0, 0, 12, 12)
            tree(S, 1, 1, 2); tree(S, 10, 2, 2, leaves="pink")
        else:
            island(S, 0, 0, 12, 12, top="wood", side_depth=1)
            for x in range(12):
                for z in range(1, 4):
                    setb(S, x, -1, z, "cream" if z < 3 else "yellow")
            for y in range(12):
                for z in range(1, 4):
                    setb(S, -1, y, z, "cream" if z < 3 else "yellow")
            for (x, y, m) in ((1, 1, "red"), (2, 1, "blue"), (1, 2, "yellow"), (9, 9, "green"), (10, 9, "red")):
                setb(S, x, y, 1, m)
        st = student(6, 3.5, 0, "y")
        kids = []
        rnd = random.Random(8)
        for i in range(6):
            a = math.pi * (0.15 + 0.7 * i / 5)
            tx, ty = 6 + math.cos(a) * 3.2, 4 + math.sin(a) * 3.2
            sx_, sy_ = rnd.uniform(1, 11), rnd.uniform(6, 11)
            kids.append((kid(tx, ty, i, "-y"), (sx_, sy_), (tx, ty)))
        P.append(st)
        P += [k[0] for k in kids]
        def upd(t):
            st.arm_up = (max(0, math.sin(t * 3)) * 0.7, max(0, math.sin(t * 3 + 2)) * 0.5)
            for i, (k, a, b) in enumerate(kids):
                if name == "gakudo":
                    walk_to(k, a, b, t, 0.2 + i * 0.25, dur * 0.55 + i * 0.1, 12)
                    if t > dur * 0.55 + i * 0.1:
                        k.facing = "-y"
                k.jump = 0 if (name == "gakudo" and t < dur * 0.6) else max(0, math.sin(t * 5 + i)) * 0.15
                if name == "kids_listen" or t > dur * 0.7:
                    k.arm_up = (0.9 if (t * 1.3 + i) % 3 < 1 else 0, 0)
        sc.update = upd
        sc.keys = [(0, (82, 6, 5, 1.4)), (1, (70, 6, 5.5, 1.2))] if name == "kids_listen" else [(0, (56, 6, 6, 1.2)), (1, (66, 6, 5, 1.2))]

    elif name == "park_event":
        island(S, 0, 0, 14, 14)
        tree(S, 1, 1, 2); tree(S, 12, 1, 2, leaves="pink"); tree(S, 1, 12, 2)
        # すべり台
        box(S, 10, 9, 1, 1, 1, 3, "red")
        for k in range(3):
            setb(S, 9 - k, 9, 3 - k, "yellow")
        # レジャーシート
        for x in range(3, 7):
            for y in range(8, 11):
                replace_top(S, x, y, "sand" if (x + y) % 2 else "white")
        st = student(4.5, 4.5, 0, "y")
        kids = [kid(5 + i * 1.1, 6.5 + (i % 2), i, "-y") for i in range(5)]
        P += [st] + kids
        def upd(t):
            st.arm_up = (0.6, 0)
            for i, k in enumerate(kids):
                k.jump = max(0, math.sin(t * 6 + i * 1.3)) * 0.4
                k.arm_up = (0.9 if i % 2 else 0, 0)
        sc.update = upd
        def dyn(t):
            out = [(st.x + 0.3, st.y + 0.25, 1.75, 0.35, "paper")]   # クリップボード
            bx = 7 + math.sin(t * 2) * 3
            out.append((bx, 7.5, 1 + abs(math.sin(t * 5)) * 1.5, 0.4, "red"))
            for k in range(3):
                if (t * 2 + k) % 2 < 1.3:
                    out.append((3 + k * 0.6, 3.4, 3.2 + k * 0.2, 0.3, "lamp"))
            return out
        sc.dyn = dyn
        sc.keys = [(0, (58, 6.5, 6.5, 1.4)), (1, (68, 6, 6, 1.4))]

    elif name in ("snow", "ski"):
        sc.sky = SKY_SNOW
        sc.snow = True
        if name == "snow":
            island(S, 0, 0, 14, 14, top="snow")
            # かまくら（半球の殻＋入口）
            for x in range(1, 8):
                for y in range(1, 8):
                    for z in range(1, 5):
                        dx, dy, dz = x - 4, y - 4, z - 1
                        r = math.sqrt(dx * dx + dy * dy + dz * dz)
                        door = (x == 4 and y >= 6 and z <= 2)
                        if r <= 2.9 and not door and not (r < 1.9 and z <= 2):
                            setb(S, x, y, z, "snow")
            # 雪だるま
            setb(S, 10, 4, 1, "snow"); setb(S, 10, 4, 2, "snow")
            # 陶芸の机
            box(S, 9, 9, 1, 3, 2, 1, "darkwood")
            ppl = [Person(8.6, 11.6, 1, "-y", "coat_w", "jeans", "hair3", "skin"), student(10.5, 12, 0, "-y")] + [kid(5 + i, 9 + (i % 2), i, "x") for i in range(3)]
            P += ppl
            def upd(t):
                for i, p_ in enumerate(ppl):
                    p_.bob = 0.02 * math.sin(t * 4 + i)
                    if i >= 2:
                        p_.jump = max(0, math.sin(t * 6 + i)) * 0.3
                ppl[1].arm_up = (0.7, 0)
            sc.update = upd
            def dyn(t):
                return [(10.1, 4.1, 3, 0.8, "snow"), (10.35, 4.95, 3.3, 0.15, "black"), (10.6, 4.95, 3.3, 0.15, "black"), (10.4, 4.95, 3.05, 0.2, "orange"),
                        (10.2, 9.4, 2, 0.5, "brick"), (10.9, 9.5, 2, 0.4, "brick")]
            sc.dyn = dyn
            sc.keys = [(0, (52, 7, 7.5, 1.4)), (1, (60, 7, 8, 1.4))]
        else:
            # 斜面（奥ほど高い）
            for x in range(16):
                for y in range(10):
                    h = max(0, (15 - x) // 3)
                    for z in range(-1, h + 1):
                        S.append((x, y, z, 1, "snow"))
            for x in range(0, 16, 4):
                h = max(0, (15 - x) // 3)
                for z in range(h + 1, h + 4):
                    setb(S, x, 0, z, "gray")
            tree(S, 2, 9, 2, z0=(15 - 2) // 3 + 1)
            st = Person(14.5, 5, 1, "-x", "t_orange", "jeans", "hair", "skin")
            kids = [kid(0, 0, i, "x") for i in range(4)]
            P += [st] + kids
            def upd(t):
                st.arm_up = (0.8 if t % 1.5 < 0.75 else 0.3, 0)
                for i, k in enumerate(kids):
                    u = ((t * 0.28 + i / 4) % 1)
                    x = 1 + u * 12
                    k.x, k.y = x, 2.5 + i * 1.4 + 0.6 * math.sin(u * 8)
                    k.z = max(0, (15 - int(x)) // 3) + 1 - ((15 - x) / 3 - (15 - int(x)) // 3) * 0
                    k.z = max(1, (15 - x) / 3 + 1 - 0.3)
                    k.facing = "x"
                    k.arm_up = (0.5, 0.5)
            sc.update = upd
            def dyn(t):
                out = []
                for i in range(4):
                    for j in range(2):
                        k = kids[i]
                        out.append((k.x - 0.2 + j * 0.0, k.y - 0.25 + j * 0.3, k.z - 0.08, 0.25, "red" if i % 2 else "blue"))
                return out
            sc.dyn = dyn
            sc.keys = [(0, (46, 8, 5, 3.2)), (1, (54, 9, 5, 2.4))]

    elif name == "study":
        sc.sky = ((90, 130, 110), (170, 210, 180))
        sc.clouds = False
        island(S, 0, 0, 12, 12, top="wood", side_depth=1)
        for x in range(12):
            for z in range(1, 5):
                setb(S, x, -1, z, "board" if (2 <= x <= 9 and 2 <= z <= 3) else "cream")
        for y in range(12):
            for z in range(1, 5):
                setb(S, -1, y, z, "cream" if not (z in (2, 3) and y % 3 == 1) else "glass")
        desks = [(2 + c * 3, 5 + r * 3) for r in range(2) for c in range(3)]
        for (x, y) in desks:
            setb(S, x, y, 1, "wood")
        st = student(5.5, 1.5, 0, "y")
        scales = [0.55, 0.62, 0.7, 0.78, 0.86, 0.94]
        learners = []
        for i, (x, y) in enumerate(desks):
            k = kid(x + 0.5, y + 1.4, i, "-y")
            k.scale = scales[i]
            learners.append(k)
        P += [st] + learners
        def upd(t):
            st.facing = "-x" if (t % 3) < 1.2 else "y"
            st.arm_up = (0.8 if st.facing == "-x" else 0.3, 0)
            for i, k in enumerate(learners):
                k.bob = 0.02 * math.sin(t * 3 + i)
                k.arm_up = (0.9 if (t * 0.9 + i * 0.7) % 4 < 0.8 else 0, 0)
        sc.update = upd
        def dyn(t):
            # 黒板に書かれていく線（文字ではなく線）
            out = []
            n = int(min(1, t / (dur * 0.8)) * 14)
            for i in range(n):
                out.append((2.4 + (i % 7) * 1.0, -0.15, 3.4 - (i // 7) * 0.7, 0.18, "white"))
            return out
        sc.dyn = dyn
        sc.keys = [(0, (54, 6, 6, 1.8)), (1, (62, 5.5, 5, 1.8))]

    elif name == "new_world":
        sc.sky = SKY_WARM
        island(S, 0, 0, 8, 8)
        island(S, 11, 3, 7, 7, side_depth=1)
        island(S, 4, 12, 6, 5, top="sand", side_depth=1)
        island(S, 13, 13, 5, 5, top="snow", side_depth=1)
        for x in range(8, 11):
            setb(S, x, 5, 0, "darkwood")
        building(S, 1, 1, 3, 3, 3, "white", "gray")
        building(S, 13, 4, 3, 2, 2, "wood", "red")
        tree(S, 16, 8, 2); tree(S, 6, 14, 1, leaves="pink"); tree(S, 15, 15, 1)
        st = student(3, 5.5, 0, "x")
        others = [politician(14, 7.2, "-x"), Person(15, 6.2, 1, "-x", "t_green", "jeans", "hair2", "skin")] + [kid(12.5 + i * 0.9, 8.6, i, "-x") for i in range(3)]
        P += [st] + others
        def upd(t):
            walk_to(st, (3, 5.5), (12.2, 5.5), t, 0, dur * 0.75, 9)
            for i, o in enumerate(others):
                o.arm_up = (0.8 if (t * 1.5 + i) % 2 < 1 else 0, 0)
        sc.update = upd
        sc.keys = [(0, (62, 4, 5.5, 1.5)), (0.6, (44, 9, 6.5, 1)), (1, (32, 10, 9, 0))]

    elif name == "mayor":
        sc.sky = SKY_WARM
        town(S, 18, seed=9, road_y=(12, 13), tall=True, front=False)
        # 市役所（大きく白い）
        building(S, 6, 3, 6, 5, 6, "white", "gray", "glass")
        for k in range(4):
            setb(S, 9, 3, 7 + k, "gray")
        box(S, 9, 3, 10, 1, 1, 1, "orange")
        setb(S, 10, 3, 10, "orange")
        st = Person(9.2, 8.7, 1, "y", "suit", "suit", "hair", "skin")
        crowd = [student(5 + i * 1.3, 11 + (i % 2) * 0.6, i, "-y") for i in range(6)]
        P += [st] + crowd
        def upd(t):
            st.arm_up = (0.9, 0.5 + 0.4 * math.sin(t * 5))
            for i, c in enumerate(crowd):
                c.jump = max(0, math.sin(t * 6 + i)) * 0.3
                c.arm_up = (0.9 if i % 2 else 0, 0 if i % 2 else 0.9)
        sc.update = upd
        sc.keys = [(0, (34, 9, 9, 4)), (1, (52, 9.0, 10, 3.2))]

    elif name == "stage":
        sc.sky = SKY_NIGHT
        sc.clouds = False
        island(S, 0, 0, 14, 14, top="carpet", side_depth=1)
        box(S, 2, 0, 1, 10, 4, 1, "darkwood")        # 舞台
        for x in range(2, 12):
            for z in range(2, 6):
                setb(S, x, -1, z, "blue" if 3 <= x <= 10 and 3 <= z <= 5 else "navy")
        for x in (2, 11):
            for z in range(2, 7):
                setb(S, x, 0, z, "black")
            setb(S, x, 0, 7, "lamp")
        presenters = [student(4.5 + i * 2.2, 2.2, i, "y", z=2) for i in range(3)]
        aud = [student(1.5 + (i % 6) * 2, 8 + (i // 6) * 2.2, i + 1, "-y") for i in range(12)]
        P += presenters + aud
        def upd(t):
            for i, p_ in enumerate(presenters):
                p_.arm_up = (0.8 if (t * 1.2 + i) % 2 < 0.9 else 0.2, 0)
            for i, a in enumerate(aud):
                a.arm_up = (0.9 if (t * 2 + i * 0.37) % 3 < 0.5 else 0, 0)
                a.bob = 0.03 * math.sin(t * 4 + i)
        sc.update = upd
        def dyn(t):
            out = []
            # 画面に光る四角（グラフ風）
            for i in range(4):
                h = 0.4 + 0.25 * i * min(1, t / 1.2)
                out.append((4 + i * 1.6, -0.6, 2.4, h, "gold"))
            for i in range(10):
                a = t * 1.5 + i
                out.append((6 + 5 * math.sin(a * 0.7 + i), 5 + 4 * math.cos(a * 0.5 + i), 6 + math.sin(a) * 0.5, 0.18, "lamp"))
            return out
        sc.dyn = dyn
        sc.keys = [(0, (40, 7, 6, 1.5)), (1, (50, 7, 3.5, 2))]

    elif name == "pools":
        sc.sky = SKY_DAY
        island(S, 0, 0, 18, 18)
        pools = [(1, 1), (7, 1), (13, 1), (1, 7), (13, 7)]
        stages_ = [(6, 7), (1, 13), (12, 13)]
        sc.static += []
        swimmers = []
        for i, (x0, y0) in enumerate(pools):
            for j in range(2):
                swimmers.append(kid(x0 + 1.3 + j * 1.4, y0 + 1.8, i + j, "x", z=0.45))
        audience = [student(7.6 + (i % 4) * 0.8, 10.8 + (i // 4) * 0.9, i, "-y") for i in range(8)]
        P += swimmers + audience
        T_pool = [0.1 + i * 0.09 for i in range(5)]
        T_stage = [0.6 + i * 0.1 for i in range(3)]
        def upd(t):
            u = t / dur
            for i, s_ in enumerate(swimmers):
                s_.visible = u > T_pool[i // 2] + 0.05
                s_.bob = 0.08 * math.sin(t * 4 + i)
                s_.arm_up = (0.9 if (t * 2 + i) % 2 < 1 else 0, 0)
            for i, a in enumerate(audience):
                a.visible = u > T_stage[0]
                a.jump = max(0, math.sin(t * 7 + i)) * 0.3
                a.arm_up = (0.9, 0.9 if i % 2 else 0)
        sc.update = upd
        def dyn(t):
            u = t / dur
            out = []
            for i, (x0, y0) in enumerate(pools):
                k = min(1, max(0, (u - T_pool[i]) / 0.05))
                if k <= 0:
                    continue
                cells = [(x, y) for y in range(y0, y0 + 4) for x in range(x0, x0 + 4)]
                for j, (x, y) in enumerate(cells[:int(k * 16)]):
                    edge = x in (x0, x0 + 3) or y in (y0, y0 + 3)
                    out.append((x, y, 0.002, 1, "white" if edge else "pool"))
            for i, (x0, y0) in enumerate(stages_):
                k = min(1, max(0, (u - T_stage[i]) / 0.06))
                if k <= 0:
                    continue
                hh = ease(k)
                for x in range(x0, x0 + 4):
                    for y in range(y0, y0 + 2):
                        out.append((x, y, 1 - (1 - hh), 1, "darkwood"))
                for xx in (x0, x0 + 3):
                    out.append((xx, y0, 2 * hh + 0.0, 1, "black"))
                    out.append((xx, y0, 3 * hh, 1, "lamp" if (int(t * 4) + xx) % 2 else "gold"))
            return out
        sc.dyn = dyn
        sc.keys = [(0, (42, 9, 9, 1)), (1, (46, 9, 9, 1))]

    elif name == "growth":
        sc.sky = SKY_DAY
        island(S, 0, 0, 16, 16)
        for x in range(16):
            replace_top(S, x, 8, "road")
        for y in range(16):
            replace_top(S, 8, y, "road")
        lots = [(1, 1), (5, 1), (10, 1), (13, 4), (1, 5), (10, 10), (13, 13), (1, 10), (4, 13), (10, 5)]
        rnd = random.Random(21)
        heights = [[rnd.randint(1, 2), rnd.randint(2, 4), rnd.randint(4, 8)] for _ in lots]
        walls = [rnd.choice(["white", "cream", "glass", "gray", "brick"]) for _ in lots]
        roofs = [rnd.choice(["red", "navy", "gray", "green"]) for _ in lots]
        P += [student(8.5, 9.5, i, "x" if i % 2 else "y") for i in range(2)]
        def phase(t):
            u = t / dur
            return 0 if u < 0.3 else (1 if u < 0.62 else 2)
        sc.phase = phase
        sc.label = lambda t: ["10年後", "20年後", "30年後"][phase(t)]
        def dyn(t):
            u = t / dur
            out = []
            for i, (x0, y0) in enumerate(lots):
                ph = phase(t)
                t0 = [0.0, 0.3, 0.62][ph]
                prev = heights[i][ph - 1] if ph else 0
                k = min(1, (u - t0) / 0.1)
                h = prev + (heights[i][ph] - prev) * ease(k)
                hi = int(math.ceil(h))
                for z in range(hi):
                    top = min(1.0, h - z)
                    for x in range(x0, x0 + 2):
                        for y in range(y0, y0 + 2):
                            out.append((x, y, 1 + z, top, walls[i] if z < hi - 1 else roofs[i] if top > 0.99 else walls[i]))
            if phase(t) >= 1:
                for k in range(4):
                    out.append((2 + k * 3, 14.5, 1, 0.5, "pink"))
            return out
        sc.dyn = dyn
        sc.keys = [(0, (36, 8, 8, 1)), (1, (34, 8, 8, 2))]

    elif name.startswith("bedroom"):
        night = name in ("bedroom_night", "bedroom_game", "bedroom_q")
        sc.sky = SKY_NIGHT if night else ((150, 180, 220), (210, 225, 245))
        sc.clouds = False
        island(S, 0, 0, 8, 8, top="wood", side_depth=1)
        for x in range(8):
            for z in range(1, 4):
                setb(S, x, -1, z, "glass" if (z == 2 and x in (2, 3)) else "cream")
        for y in range(8):
            for z in range(1, 4):
                setb(S, -1, y, z, "cream")
        box(S, 4, 0, 1, 3, 2, 1, "white")      # ベッド
        box(S, 5, 0, 2, 2, 2, 1, "blue") if False else None
        for x in (5, 6):
            for y in (0, 1):
                setb(S, x, y, 2, "blue")
        setb(S, 4, 0, 2, "white")
        setb(S, 0, 3, 1, "darkwood"); setb(S, 0, 4, 1, "darkwood")   # テレビ台
        setb(S, 0, 3, 2, "black"); setb(S, 0, 4, 2, "black")
        setb(S, 6, 6, 1, "leaves")
        st = student(3.2, 3.6, 0, "-x" if name == "bedroom_game" else "x")
        P.append(st)
        def upd(t):
            st.bob = 0.02 * math.sin(t * 2)
            st.arm_up = (0.35 if name != "bedroom_game" else 0.3, 0.3 if name == "bedroom_game" else 0)
            if name == "bedroom":
                st.facing = "x" if (t % 4) < 2.5 else "y"
        sc.update = upd
        def dyn(t):
            out = []
            if name != "bedroom_game":
                out.append((st.x + 0.15, st.y - 0.45, 1.75, 0.22, "black"))   # スマホ
            if name == "bedroom_game":
                c = ["blue", "red", "green", "yellow"][int(t * 3) % 4]
                out += [(0.55, 3.1, 2.1, 0.5, c), (0.55, 3.9, 2.1, 0.5, c)]
            if night:
                out.append((6.2, 6.2, 2.0, 0.5, "lamp"))
            if name == "bedroom_q":
                out += glyph(QMARK, st.x - 0.3, st.y - 0.2, 3.2 + 0.1 * math.sin(t * 4), "white", 0.14)
            return out
        sc.dyn = dyn
        sc.keys = [(0, (52, 4, 4, 1)), (1, (58, 4, 4, 1))]

    elif name == "walk_pol":
        town(S, 16, seed=12, front=False)
        st = student(1, 7.4, 0, "x")
        pol = politician(1, 8.4, "x")
        P += [st, pol]
        def upd(t):
            walk_to(st, (1.6, 7.4), (1.6 + dur * 1.3, 7.4), t, 0, dur, 8)
            walk_to(pol, (1.6, 8.5), (1.6 + dur * 1.3, 8.5), t, 0, dur, 8)
            pol.arm_up = (0, 0.5 if (t % 2) < 1 else 0)
        sc.update = upd
        sc.keys = [(0, (46, 3, 8, 2)), (1, (50, 1.6 + dur * 1.3, 8, 2))]

    elif name == "meishi":
        sc.sky = SKY_ROOM
        sc.clouds = False
        island(S, 0, 0, 12, 12, top="carpet", side_depth=1)
        for x in range(12):
            for z in range(1, 4):
                setb(S, x, -1, z, "cream" if z < 3 else "gold")
        for y in range(12):
            for z in range(1, 4):
                setb(S, -1, y, z, "cream" if z < 3 else "gold")
        for (x, y) in ((2, 2), (8, 2), (2, 8), (8, 8)):
            box(S, x, y, 1, 2, 2, 1, "white")
        guests = [Person(x, y, 1, f, "suit", "suit", h, "skin") for (x, y, f, h) in
                  ((1.5, 4.6, "-y", "hair3"), (4.6, 2.5, "-x", "hair"), (7.5, 4.6, "-y", "hair2"), (10.6, 3.0, "-x", "hair3"),
                   (1.4, 7.4, "y", "hair"), (10.5, 9.0, "-x", "hair3"))]
        st = student(5.2, 6.0, 0, "x")
        pol = politician(5.2, 7.2, "x", hair="hair")
        ceo = Person(6.8, 6.0, 1, "-x", "suit", "suit", "hair3", "skin")
        P += guests + [st, pol, ceo]
        def upd(t):
            k = (t % 2.4) / 2.4
            st.arm_up = (0.4 if k < 0.5 else 0.1, 0)
            ceo.arm_up = (0, 0.4 if 0.2 < k < 0.7 else 0.1)
            st.bob = 0.06 * max(0, math.sin(t * 2.6)) * -1
            for i, g in enumerate(guests):
                g.arm_up = (0.4 if (t + i) % 3 < 1 else 0, 0)
        sc.update = upd
        def dyn(t):
            k = (t % 2.4) / 2.4
            u = min(1, k / 0.5)
            out = [(lerp(5.5, 6.4, u), 6.0, 1.95, 0.22, "paper")]
            if k > 0.3:
                u2 = min(1, (k - 0.3) / 0.4)
                out.append((lerp(6.5, 5.6, u2), 5.9, 2.0, 0.22, "paper"))
            return out
        sc.dyn = dyn
        sc.keys = [(0, (50, 6, 6, 1.4)), (1, (62, 6, 6.2, 1.6))]

    elif name == "network":
        sc.sky = SKY_WARM
        island(S, 0, 0, 12, 12)
        for (x, y) in ((1, 1), (10, 1), (1, 10)):
            tree(S, x, y, 2, leaves="pink" if x > 5 else "leaves")
        st = student(6, 6, 0, "x")
        ring = []
        kinds = [lambda x, y: politician(x, y, "x"), lambda x, y: Person(x, y, 1, "x", "t_green", "jeans", "hair2", "skin"),
                 lambda x, y: kid(x, y, 1), lambda x, y: Person(x, y, 1, "x", "suit", "suit", "hair3", "skin"),
                 lambda x, y: student(x, y, 2), lambda x, y: kid(x, y, 3), lambda x, y: Person(x, y, 1, "x", "coat_w", "skirt", "hair", "skin", 1.0, True),
                 lambda x, y: student(x, y, 4)]
        for i, f in enumerate(kinds):
            a = 2 * math.pi * i / len(kinds)
            p = f(6 + math.cos(a) * 3.4, 6 + math.sin(a) * 3.4)
            p.facing = "x" if math.cos(a) < 0 else "-x"
            ring.append(p)
        P += [st] + ring
        def upd(t):
            st.arm_up = (0.9, 0.9 if (t % 1.2) < 0.6 else 0.5)
            for i, p in enumerate(ring):
                p.visible = t > 0.15 + i * 0.22
                p.jump = max(0, math.sin(t * 5 + i)) * 0.2
        sc.update = upd
        def dyn(t):
            out = []
            for i, p in enumerate(ring):
                if not p.visible:
                    continue
                for k in range(3):
                    u = (t * 0.7 + k / 3 + i * 0.13) % 1
                    out.append((lerp(6, p.x, u) - 0.1, lerp(6, p.y, u) - 0.1, 2.6, 0.2, "gold"))
            return out
        sc.dyn = dyn
        sc.keys = [(0, (56, 6, 6, 1)), (1, (50, 6, 6, 1))]

    elif name == "office":
        sc.sky = ((160, 200, 240), (230, 240, 250))
        sc.clouds = False
        island(S, 0, 0, 10, 10, top="wood", side_depth=1)
        for x in range(10):
            for z in range(1, 5):
                setb(S, x, -1, z, "glass" if (z in (2, 3) and x in (1, 2, 6, 7)) else "white")
        for y in range(10):
            for z in range(1, 5):
                setb(S, -1, y, z, "board" if (z in (2, 3) and 3 <= y <= 6) else "white")
        box(S, 3, 2, 1, 3, 2, 1, "darkwood")   # 議員さんの机
        setb(S, 8, 1, 1, "leaves"); setb(S, 8, 1, 2, "leaves")
        box(S, 7, 6, 1, 2, 3, 1, "gray")       # 棚
        pol = politician(4.5, 1.2, "y")
        st = student(4.5, 5.2, 0, "-y")
        staff = Person(1.2, 6.5, 1, "-x", "shirt_w", "suit", "hair", "skin")
        P += [pol, st, staff]
        def upd(t):
            pol.arm_up = (0.5 + 0.3 * math.sin(t * 4), 0)
            st.arm_up = (0, 0.35)
            st.bob = 0.03 * abs(math.sin(t * 3))
            staff.arm_up = (0.6, 0)
        sc.update = upd
        def dyn(t):
            out = [(st.x - 0.1, st.y - 0.5, 1.8, 0.3, "paper")]
            n = int(min(1, t / max(1, dur * 0.7)) * 8)
            for i in range(n):
                out.append((-0.15, 3.2 + (i % 4) * 0.9, 3.3 - (i // 4) * 0.8, 0.3, "paper"))
            out += [(3.4, 2.3, 2, 0.4, "paper"), (4.4, 2.6, 2, 0.4, "paper")]
            return out
        sc.dyn = dyn
        sc.keys = [(0, (56, 4.5, 4.5, 1.6)), (1, (66, 4.5, 4, 1.6))]

    elif name == "festival":
        sc.sky = SKY_NIGHT
        sc.clouds = False
        island(S, 0, 0, 14, 14)
        for x in range(14):
            for y in (6, 7):
                replace_top(S, x, y, "sand")
        for (x0, y0, c) in ((1, 2, "red"), (5, 2, "white"), (9, 2, "red"), (3, 10, "white"), (8, 10, "red")):
            box(S, x0, y0, 1, 3, 2, 1, "darkwood")
            for x in range(x0, x0 + 3):
                for y in range(y0, y0 + 2):
                    setb(S, x, y, 3, c)
            setb(S, x0, y0, 2, "log"); setb(S, x0 + 2, y0, 2, "log")
        posts = [(0, 5), (4, 5), (8, 5), (12, 5), (2, 9), (6, 9), (11, 9)]
        for (x, y) in posts:
            setb(S, x, y, 1, "log"); setb(S, x, y, 2, "log")
        pol = politician(6.2, 6.4, "y", hair="hair")
        st = student(5.0, 6.6, 0, "y")
        locals_ = [Person(7.4, 7.6, 1, "-x", "coat_w", "jeans", "hair3", "skin"), Person(8.3, 7.0, 1, "-x", "t_purple", "skirt", "hair3", "skin", 1.0, True)] + \
                  [kid(2 + i * 2.2, 7.3 + (i % 2) * 0.4, i, "x") for i in range(4)]
        P += [pol, st] + locals_
        def upd(t):
            pol.facing = "x" if (t % 3) < 1.8 else "y"
            pol.arm_up = (0.6 if pol.facing == "x" else 0.9, 0)
            st.arm_up = (0, 0.3)
            for i, l in enumerate(locals_):
                l.bob = 0.03 * math.sin(t * 3 + i)
                if i >= 2:
                    l.x = 2 + (i - 2) * 2.2 + math.sin(t * 1.5 + i) * 0.8
                    l.walk = 1; l.phase = t * 9
                    l.facing = "x" if math.cos(t * 1.5 + i) > 0 else "-x"
                    if l.x > 5.5 and l.x < 9 and l.y < 8:
                        l.y = 8.2
        sc.update = upd
        def dyn(t):
            out = []
            for i, (x, y) in enumerate(posts):
                out.append((x + 0.15, y + 0.15, 3, 0.7, "lamp" if (int(t * 3) + i) % 3 else "gold"))
            return out
        sc.dyn = dyn
        sc.keys = [(0, (46, 6.5, 7, 1.4)), (1, (56, 6.6, 6.8, 1.6))]

    else:
        raise ValueError(name)

    if not sc.keys:
        sc.keys = [(0, (44, 6, 6, 1)), (1, (50, 6, 6, 1))]
    return sc.finish()
