import numpy as np, subprocess, sys, math
from PIL import Image

f32 = np.float32
R = np.random.default_rng(11)
W, H, FPS, RS, SHOT = 720, 1280, 30, 2, 5.0


def C(*c):
    return np.array(c, f32)


def vnoise(h, w, cell, octs=4, pers=0.5, seed=None):
    rg = np.random.default_rng(seed) if seed is not None else R
    tot = np.zeros((h, w), f32); amp = 1.0; norm = 0.0
    for _ in range(octs):
        gh, gw = int(h / cell) + 3, int(w / cell) + 3
        g = rg.random((gh, gw)).astype(f32)
        im = Image.fromarray(g, "F").resize((int(gw * cell), int(gh * cell)), Image.BICUBIC)
        tot += np.asarray(im)[:h, :w] * amp
        norm += amp; amp *= pers; cell = max(1.0, cell / 2)
    return tot / norm


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def ease(x):
    x = min(max(x, 0.0), 1.0); return 0.5 - 0.5 * math.cos(math.pi * x)


def hsh(*a):
    h = np.zeros(np.shape(a[0]), dtype=np.int64)
    K = [73856093, 19349663, 83492791, 2654435761, 40503, 912367]
    for i, v in enumerate(a):
        h = h ^ (np.asarray(v).astype(np.int64) * K[i])
        h = (h * 2246822519) & 0xFFFFFFFF
        h ^= h >> 13
    return (h & 0xFFFF) / 65535.0


class Scene:
    def __init__(s, nx, ny, nz):
        s.col = np.zeros((nx, ny, nz, 3), f32); s.mat = np.zeros((nx, ny, nz), np.uint8)
        s.dims = np.array([nx, ny, nz])
        s.sun = None; s.sunc = C(1, 1, 1); s.amb = C(0.5, 0.5, 0.5); s.lights = []
        s.hor = C(1, 1, 1); s.top = C(0.4, 0.6, 0.9); s.fog0, s.fogk = 40, 300
        s.sundisk = 1.0

    def put(s, sl, c, m=1, var=0.06):
        shp = s.mat[sl].shape
        v = (1 + R.uniform(-var, var, shp)).astype(f32)[..., None]
        s.col[sl] = np.clip(C(*c) * v, 0, 2); s.mat[sl] = m

    def sky(s, d):
        y = np.clip(d[:, 1], -0.2, 1)
        t = np.clip(y / 0.6, 0, 1) ** 0.7
        out = s.hor * (1 - t[:, None]) + s.top * t[:, None]
        if s.sun is not None:
            sd = np.clip(d @ s.sun, 0, 1)
            out = out + (sd ** 500 * 6 + sd ** 14 * 0.4)[:, None] * C(1.0, 0.85, 0.6) * s.sundisk
        return out.astype(f32)


# ---------------- mammoth ----------------
FUR = np.array([[0.64, 0.31, 0.15], [0.52, 0.23, 0.11], [0.76, 0.42, 0.22], [0.4, 0.17, 0.08]], f32)
IVORY = C(1.35, 1.27, 1.1)


def ell(cx, cy, cz, rx, ry, rz):
    x0, y0, z0 = int(math.floor(cx - rx - 1)), int(math.floor(cy - ry - 1)), int(math.floor(cz - rz - 1))
    xs, ys, zs = np.meshgrid(np.arange(x0, int(cx + rx + 2)), np.arange(y0, int(cy + ry + 2)), np.arange(z0, int(cz + rz + 2)), indexing="ij")
    return (((xs + 0.5 - cx) / rx) ** 2 + ((ys + 0.5 - cy) / ry) ** 2 + ((zs + 0.5 - cz) / rz) ** 2) <= 1, x0, y0, z0


def mammoth(c, m, cx, gy, cz, f=-1, drop=0.0, sway=0.0, mode="normal", walk=None, reach=1.0):
    NX_, NY_, NZ_ = m.shape
    Zw = lambda a: cz + f * a
    Yw = lambda y: gy - 1 + y

    def stamp(mask, x0, y0, z0, kind="fur"):
        xs, ys, zs = np.nonzero(mask)
        xs = xs + x0; ys = ys + y0; zs = zs + z0
        ok = (xs >= 0) & (xs < NX_) & (ys >= 1) & (ys < NY_) & (zs >= 0) & (zs < NZ_)
        xs, ys, zs = xs[ok], ys[ok], zs[ok]
        if isinstance(kind, str):
            r = hsh(xs - cx, ys - gy, (zs - cz) * f)
            idx = np.where(r < 0.45, 0, np.where(r < 0.75, 1, np.where(r < 0.92, 2, 3)))
            c[xs, ys, zs] = FUR[idx]; m[xs, ys, zs] = 2
        else:
            c[xs, ys, zs] = kind; m[xs, ys, zs] = 1

    def E(x, y, a, rx, ry, ra, kind="fur"):
        mk, x0, y0, z0 = ell(x, Yw(y), Zw(a), rx, ry, ra); stamp(mk, x0, y0, z0, kind)

    # legs
    for lx in (-5, 5):
        for la in (8, -11):
            ph = 0 if (lx < 0) == (la > 0) else math.pi
            swing, lift = 0.0, 0.0
            if walk is not None:
                swing = 2.2 * math.sin(walk + ph); lift = max(0.0, math.cos(walk + ph)) * 1.6
            for y in range(1, 17):
                if y < 1 + lift: continue
                r = 2.6 if y < 4 else (3.0 if y < 11 else 3.6)
                E(cx + lx, y + 0.5, la + swing * (1 - y / 17), r, 0.5, r)
    for args in [(cx, 22, -3, 9.5, 8, 15), (cx, 27, 5, 8.5, 7, 8), (cx, 22, -12, 8.5, 7, 7)]:
        E(*args)
    # shaggy fringe
    for x in range(cx - 9, cx + 10):
        if not (0 <= x < NX_): continue
        for a in range(-18, 12):
            z = Zw(a)
            if not (0 <= z < NZ_): continue
            col_ = m[x, Yw(10):Yw(30), z]
            ys = np.nonzero(col_ == 2)[0]
            if len(ys) == 0: continue
            yb = Yw(10) + ys[0]
            if yb < Yw(13): continue
            L = 1 + int(hsh(x - cx, a, 7) * 5)
            for y in range(max(yb - L, Yw(2)), yb):
                if m[x, y, z] == 0:
                    c[x, y, z] = FUR[1] if hsh(x - cx, y - gy, a) < 0.6 else FUR[3]; m[x, y, z] = 2
    hy = 27 - drop; ha = 13 - drop * 0.3
    E(cx, hy, ha, 6.5, 7, 6); E(cx, hy + 5, ha - 1, 4.5, 4, 4.5)
    for sx in (-1, 1):
        E(cx + sx * 6.5, hy + 1, ha - 2, 1.2, 3, 2.5)
    for sx in (-1, 1):
        ex, ey, ez = int(cx + sx * 5.2), int(Yw(hy + 1)), int(Zw(ha + 4))
        if 0 <= ex < NX_ and 0 <= ey < NY_ and 0 <= ez < NZ_:
            c[ex, ey, ez] = C(0.05, 0.03, 0.02); m[ex, ey, ez] = 1
    # trunk
    ty0, ta0 = hy - 2, ha + 5.5
    n = 60
    for i in range(n + 1):
        s = i / n
        if mode == "reach":
            a = ta0 + 3 * s + 3 * math.sin(math.pi * s * 0.8)
            y = ty0 - 3 * math.sin(math.pi * s) * (1 - s) + 9 * reach * s ** 1.4
            x = cx + sway * s ** 2
        else:
            y = ty0 - s * (ty0 - 2.5)
            a = ta0 + 3.5 * math.sin(s * math.pi * 0.9) + 2 * s
            x = cx + sway * s ** 1.5
            if s > 0.88:
                a -= (s - 0.88) * 18; y += (s - 0.88) * 10
        r = 2.4 - 1.1 * s
        E(x, max(y, 1.6), a, r, r, r)
    for sx in (-1, 1):
        for i in range(50):
            s = i / 49
            x = cx + sx * (3.5 + 8 * s - 5 * s ** 3)
            y = hy - 3 - 7 * math.sin(s * math.pi * 0.6) + 10 * s ** 2.5
            a = ha + 5 + 15 * s - 3 * s ** 3
            rr = 1.0 - 0.35 * s
            E(x, y, a, rr, rr, rr, IVORY)
    for i in range(10):
        E(cx, 24 - i * 0.9, -19 - i * 0.25, 1, 1, 1)


# ---------------- renderer ----------------
def trace(o, d, occ, dims, maxit=700):
    N = len(d)
    G = dims.astype(np.float64)
    inv = 1.0 / np.where(np.abs(d) < 1e-9, 1e-9, d)
    t1 = (0 - o) * inv; t2 = (G - o) * inv
    tmin = np.max(np.minimum(t1, t2), 1); tmax = np.min(np.maximum(t1, t2), 1)
    t0 = np.maximum(tmin, 0) + 1e-5
    alive = tmax > t0
    p = o + d * t0[:, None]
    idx = np.clip(np.floor(p).astype(np.int64), 0, dims - 1)
    step = np.where(d > 0, 1, -1).astype(np.int64)
    tD = np.abs(inv)
    tM = t0[:, None] + (idx + (step > 0) - p) * inv
    axis = np.where(tmin > 0, np.argmax(np.minimum(t1, t2), 1), -1)
    hit = np.zeros(N, bool); hidx = np.zeros((N, 3), np.int64); hax = np.full(N, -1); ht = np.full(N, np.inf)
    act = np.nonzero(alive)[0]
    I, Tm, S, TD, A, TC = idx[act], tM[act], step[act], tD[act], axis[act], t0[act]
    sh = np.array([dims[1] * dims[2], dims[2], 1], np.int64)
    for _ in range(maxit):
        if len(act) == 0: break
        h = occ[(I * sh).sum(1)] > 0
        if h.any():
            a = act[h]
            hit[a] = True; hidx[a] = I[h]; hax[a] = A[h]; ht[a] = TC[h]
            k = ~h
            act, I, Tm, S, TD, A, TC = act[k], I[k], Tm[k], S[k], TD[k], A[k], TC[k]
            if len(act) == 0: break
        mm = np.argmin(Tm, 1); r = np.arange(len(act))
        TC = Tm[r, mm]; I[r, mm] += S[r, mm]; Tm[r, mm] += TD[r, mm]; A = mm
        ok = (I[r, mm] >= 0) & (I[r, mm] < dims[mm])
        if not ok.all():
            act, I, Tm, S, TD, A, TC = act[ok], I[ok], Tm[ok], S[ok], TD[ok], A[ok], TC[ok]
    return hit, hidx, hax, ht


def camera(cam, tgt, fov):
    cam = np.array(cam, float); fw = np.array(tgt, float) - cam; fw /= np.linalg.norm(fw)
    rt = np.cross(fw, [0, 1, 0]); rt /= np.linalg.norm(rt); up = np.cross(rt, fw)
    return cam, fw, rt, up, math.tan(math.radians(fov) / 2)


def render(S, c, m, cam, tgt, fov, w, h):
    cam, fw, rt, up, th = camera(cam, tgt, fov)
    j, i = np.mgrid[0:h, 0:w]
    u = ((i + 0.5) / w * 2 - 1) * th * w / h; v = (1 - (j + 0.5) / h * 2) * th
    d = fw[None] + u.reshape(-1, 1) * rt[None] + v.reshape(-1, 1) * up[None]
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    o = np.broadcast_to(cam, d.shape).copy()
    occ = (m.reshape(-1) > 0).astype(np.uint8)
    hit, hidx, hax, ht = trace(o, d, occ, S.dims)
    out = S.sky(d)
    hi = np.nonzero(hit)[0]
    if len(hi):
        I = hidx[hi]; ax = hax[hi]; dd = d[hi]; t = ht[hi]
        ax = np.where(ax < 0, np.argmax(np.abs(dd), 1), ax)
        r = np.arange(len(hi)); n = np.zeros((len(hi), 3)); n[r, ax] = -np.sign(dd[r, ax])
        P = o[hi] + dd * t[:, None]
        base = c[I[:, 0], I[:, 1], I[:, 2]]; mm = m[I[:, 0], I[:, 1], I[:, 2]]
        t1 = (ax + 1) % 3; t2 = (ax + 2) % 3
        fu = np.clip(P[r, t1] - np.floor(P[r, t1]), 0, 0.9999); fv = np.clip(P[r, t2] - np.floor(P[r, t2]), 0, 0.9999)
        tu, tv = (fu * 8).astype(int), (fv * 8).astype(int)
        fur = mm == 2
        key = (base * 997).astype(np.int64)
        kx = np.where(fur, key[:, 0], I[:, 0]); ky = np.where(fur, key[:, 1], I[:, 1]); kz = np.where(fur, key[:, 2], I[:, 2])
        nz = hsh(kx, ky, kz, tu, tv, ax)
        amp = np.where(fur, 0.42, np.where(mm == 4, 0.06, 0.14))
        tex = 1 + (nz - 0.5) * amp
        tex = tex * np.where(fur, 0.85 + 0.3 * hsh(kx, kz, tu, ax), 1.0)
        ao = np.ones(len(hi)); nb = I + n.astype(np.int64)
        e1 = np.zeros((len(hi), 3), np.int64); e1[r, t1] = 1
        e2 = np.zeros((len(hi), 3), np.int64); e2[r, t2] = 1
        for e, wg in [(e1, fu), (-e1, 1 - fu), (e2, fv), (-e2, 1 - fv)]:
            q = np.clip(nb + e, 0, S.dims - 1)
            ao -= 0.22 * (m[q[:, 0], q[:, 1], q[:, 2]] > 0) * wg ** 3
        ao = np.clip(ao, 0.45, 1)
        light = S.amb[None] * ((0.65 + 0.35 * n[:, 1]) * ao)[:, None]
        lit = np.zeros(len(hi))
        if S.sun is not None:
            ndl = n @ S.sun; need = ndl > 0
            if need.any():
                so = P[need] + n[need] * 1e-3
                sh_hit, _, _, _ = trace(so, np.broadcast_to(S.sun, so.shape).copy(), occ, S.dims, 500)
                lit[need] = (~sh_hit) * ndl[need]
            light = light + S.sunc[None] * (lit * (0.6 + 0.4 * ao))[:, None]
        for (lp, lc, lr) in S.lights:
            L = np.array(lp) - P; dist = np.linalg.norm(L, axis=1); L /= dist[:, None]
            light = light + C(*lc)[None] * (np.clip((n * L).sum(1), 0, 1) / (1 + (dist / lr) ** 2))[:, None]
        cc = base * tex[:, None] * light
        em = mm == 4
        cc[em] = base[em] * tex[em, None] * 1.25
        gl = mm == 3
        if gl.any():
            rd = dd[gl] - 2 * (dd[gl] * n[gl]).sum(1, keepdims=True) * n[gl]
            cc[gl] = cc[gl] * 0.7 + S.sky(rd) * 0.35 * (0.5 + 0.5 * lit[gl, None])
        fog = (1 - np.exp(-np.maximum(t - S.fog0, 0) / S.fogk))[:, None]
        cc = cc * (1 - fog) + S.sky(dd * np.array([1, 0, 1]) + np.array([0, 0.04, 0])) * fog
        out[hi] = cc
    depth = np.full(len(d), np.inf); depth[hi] = ht[hi]
    return out.reshape(h, w, 3), depth.reshape(h, w)


def particles(img, depth, cam, tgt, fov, pts, cols, size):
    cam, fw, rt, up, th = camera(cam, tgt, fov)
    h, w = depth.shape
    rel = pts - cam
    z = rel @ fw
    ok = z > 1
    x = (rel @ rt)[ok] / (z[ok] * th * w / h); y = (rel @ up)[ok] / (z[ok] * th)
    px = ((x + 1) / 2 * w); py = ((1 - y) / 2 * h)
    sz = np.maximum(1, size * (h / 2) / (z[ok] * th)).astype(int)
    cl = cols[ok]; zz = z[ok]
    for k in range(len(px)):
        x0, y0 = int(px[k] - sz[k] / 2), int(py[k] - sz[k] / 2)
        x1, y1 = x0 + sz[k], y0 + sz[k]
        if x1 <= 0 or y1 <= 0 or x0 >= w or y0 >= h: continue
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, w), min(y1, h)
        msk = depth[y0:y1, x0:x1] > zz[k]
        img[y0:y1, x0:x1][msk] = cl[k]


def tone(img, expo=1.12):
    img = np.clip(img, 0, None)
    img = img / (1 + 0.25 * img) * expo
    return np.clip(img, 0, 1)


def box1d(a, r, axis):
    a = np.moveaxis(a, axis, 0)
    p = np.concatenate([np.repeat(a[:1], r + 1, 0), a, np.repeat(a[-1:], r, 0)], 0)
    cs = np.cumsum(p, 0, dtype=np.float64)
    return np.moveaxis(((cs[2 * r + 1:] - cs[:-2 * r - 1]) / (2 * r + 1)).astype(f32), 0, axis)


def blur(a, r):
    for _ in range(2):
        a = box1d(a, r, 0); a = box1d(a, r, 1)
    return a


# ================= SCENE 1: quiet avenue, trunk in roadside tree =================
def build1():
    S = Scene(200, 90, 140)
    NX, NY, NZ = 200, 90, 140
    X, Z = np.meshgrid(np.arange(NX), np.arange(NZ), indexing="ij")
    road = (Z >= 60) & (Z <= 93)
    g = np.where(road[..., None], C(0.22, 0.22, 0.24), C(0.6, 0.58, 0.55)).astype(f32)
    tile = ((X // 2 + Z // 2) % 2 == 0) & ~road
    g[tile] *= 0.9
    lane = road & (Z == 77) & ((X // 5) % 2 == 0)
    g[lane] = C(0.85, 0.85, 0.82)
    edge = road & ((Z == 62) | (Z == 91))
    g[edge] = C(0.8, 0.8, 0.78)
    g *= (1 + R.uniform(-0.07, 0.07, (NX, NZ, 1))).astype(f32)
    S.col[:, 0, :] = g; S.mat[:, 0, :] = 1
    side = ~road
    S.col[:, 1, :][side] = g[side]; S.mat[:, 1, :][side] = 1
    FAC = [(0.72, 0.42, 0.32), (0.82, 0.76, 0.64), (0.62, 0.6, 0.58), (0.88, 0.86, 0.8), (0.55, 0.38, 0.3)]
    for zr in [(0, 40), (113, 140)]:
        x = 0
        while x < NX:
            wdt = int(R.integers(16, 30)); h = int(R.integers(24, 52))
            x1 = min(NX, x + wdt)
            fc = FAC[int(R.integers(0, len(FAC)))]
            S.put((slice(x + 1, x1 - 1), slice(2, h), slice(*zr)), fc, 1, 0.05)
            xs, ys, zs = np.meshgrid(np.arange(x + 1, x1 - 1), np.arange(2, h), np.arange(*zr), indexing="ij")
            win = ((ys % 5 == 2) | (ys % 5 == 3)) & ((xs % 4) != 0) & (ys > 6) & (ys < h - 2)
            sl = (slice(x + 1, x1 - 1), slice(2, h), slice(*zr))
            sc, sm = S.col[sl], S.mat[sl]
            sc[win] = C(0.25, 0.32, 0.4); sm[win] = 3
            shop = (ys >= 2) & (ys <= 5) & ((xs % 6) != 0)
            sc[shop] = C(0.3, 0.36, 0.42); sm[shop] = 3
            sc[ys == h - 1] *= 0.75
            x = x1
    trees = []
    for zt in (49, 104):
        for xt in range(10, NX, 30):
            xt2 = xt + (15 if zt == 104 else 0)
            if xt2 >= NX: continue
            trees.append((xt2, zt))
    trees.append((100, 49))
    trees = list({(a, b) for a, b in trees if not (abs(a - 100) < 22 and b == 49) or a == 100})
    for (xt, zt) in trees:
        big = xt == 100
        th_ = 17 if big else 14
        S.put((slice(xt - 1, xt + 1), slice(2, 2 + th_), slice(zt - 1, zt + 1)), (0.35, 0.25, 0.17), 1, 0.1)
        rr = 12 if big else 8
        cyl = 2 + th_ + rr * 0.55
        xs, ys, zs = np.meshgrid(np.arange(xt - rr - 1, xt + rr + 2), np.arange(int(cyl - rr), int(cyl + rr) + 1), np.arange(zt - rr - 1, zt + rr + 2), indexing="ij")
        nz_ = hsh(xs, ys, zs)
        blob = (((xs + .5 - xt) / rr) ** 2 + ((ys + .5 - cyl) / (rr * 0.8)) ** 2 + ((zs + .5 - zt) / rr) ** 2) < 1 - 0.25 * nz_
        blob &= hsh(xs, ys, zs, 3) < 0.85
        ok = (xs >= 0) & (xs < NX) & (zs >= 0) & (zs < NZ) & (ys < NY)
        blob &= ok
        xs, ys, zs = xs[blob], ys[blob], zs[blob]
        k = hsh(xs, ys, zs, 5)
        lc = np.where(k[:, None] < 0.5, C(0.22, 0.45, 0.14), np.where(k[:, None] < 0.85, C(0.3, 0.55, 0.18), C(0.5, 0.62, 0.2)))
        S.col[xs, ys, zs] = lc; S.mat[xs, ys, zs] = 1
    # street lamps
    for xl in range(25, NX, 30):
        for zl in (57, 96):
            S.put((slice(xl, xl + 1), slice(2, 16), slice(zl, zl + 1)), (0.25, 0.27, 0.28))
            S.put((slice(xl, xl + 1), slice(16, 17), slice(zl - 1 if zl > 70 else zl, zl + 2 if zl < 70 else zl + 1)), (0.25, 0.27, 0.28))
    # a few parked cars far down the avenue
    for xc, cc in [(20, (0.7, 0.72, 0.75)), (160, (0.15, 0.25, 0.5)), (182, (0.9, 0.9, 0.9))]:
        S.put((slice(xc, xc + 9), slice(1, 3), slice(87, 91)), cc, 1, 0.03)
        S.put((slice(xc + 2, xc + 7), slice(3, 5), slice(87, 91)), (0.12, 0.15, 0.2), 3, 0.03)
    S.sun = np.array([0.5, 0.75, 0.43]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.25, 1.05, 0.82); S.amb = C(0.52, 0.56, 0.66)
    S.hor = C(0.88, 0.9, 0.92); S.top = C(0.4, 0.6, 0.88); S.fog0, S.fogk = 60, 300
    return S


# ================= SCENE 2: herd on snowy northern grassland, aerial =================
def build2():
    NX, NY, NZ = 320, 56, 320
    S = Scene(NX, NY, NZ)
    hmap = (3 + 9 * vnoise(NX, NZ, 120, 4, seed=5)).astype(int)
    snowy = vnoise(NX, NZ, 18, 4, seed=6)
    Yg = np.arange(NY)[None, :, None]
    solid = Yg < hmap[:, None, :]
    S.mat[solid] = 1
    top = Yg == (hmap[:, None, :] - 1)
    v = (1 + R.uniform(-0.04, 0.04, (NX, NZ))).astype(f32)
    snow = (C(0.9, 0.92, 0.96)[None, None] * v[..., None])
    grass = (C(0.62, 0.55, 0.32)[None, None] * v[..., None])
    topcol = np.where((snowy < 0.42)[..., None], grass, snow)
    rock = (hsh(*np.meshgrid(np.arange(NX), np.arange(NZ), indexing="ij")) < 0.004)
    topcol[rock] = C(0.3, 0.3, 0.32)
    S.col[:] = C(0.45, 0.38, 0.3)
    xs, zs = np.meshgrid(np.arange(NX), np.arange(NZ), indexing="ij")
    S.col[xs, hmap - 1, zs] = topcol
    # sparse grass tufts / dark shrubs on top
    tuft = (hsh(xs, zs, 9) < 0.03) & (snowy < 0.55)
    S.col[xs[tuft], hmap[tuft], zs[tuft]] = C(0.5, 0.43, 0.24); S.mat[xs[tuft], hmap[tuft], zs[tuft]] = 1
    # few conifers
    for k in range(26):
        x, z = int(R.integers(5, NX - 5)), int(R.integers(5, NZ - 5))
        if 70 < x < 260 and 60 < z < 300: continue
        gy = hmap[x, z]; th_ = int(R.integers(14, 26))
        S.put((slice(x, x + 1), slice(gy, gy + 4), slice(z, z + 1)), (0.3, 0.22, 0.15))
        for y in range(gy + 3, min(gy + th_, NY)):
            rr = int((gy + th_ - y) * 0.3) + 1
            sl = (slice(max(x - rr, 0), x + rr + 1), slice(y, y + 1), slice(max(z - rr, 0), z + rr + 1))
            S.put(sl, (0.12, 0.25, 0.16) if y % 3 else (0.85, 0.88, 0.92), 1, 0.08)
    S.hmap = hmap
    S.sun = np.array([-0.55, 0.42, 0.72]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.05, 0.95, 0.85); S.amb = C(0.62, 0.66, 0.76)
    S.hor = C(0.86, 0.88, 0.92); S.top = C(0.55, 0.64, 0.78); S.fog0, S.fogk = 140, 180
    S.sundisk = 0.4
    return S


HERD = [(150, 210), (186, 228), (118, 240), (210, 262), (160, 262), (128, 284), (196, 296)]


# ================= SCENE 3: empty road toward snowy mountains, sunrise =================
def build3():
    NX, NY, NZ = 220, 120, 440
    S = Scene(NX, NY, NZ)
    xs, zs = np.meshgrid(np.arange(NX), np.arange(NZ), indexing="ij")
    tund = 1 + (vnoise(NX, NZ, 30, 3, seed=8) * 3).astype(int)
    mnt = (smooth(250, 360, zs) * (35 + 80 * vnoise(NX, NZ, 70, 5, seed=9) * (0.6 + 0.4 * np.cos((xs - 110) / 60)))).astype(int)
    hmap = np.maximum(tund, mnt)
    road = (np.abs(xs - 110) <= 8) & (zs < 270)
    hmap[road] = 1
    hmap = np.minimum(hmap, NY - 2)
    Yg = np.arange(NY)[None, :, None]
    S.mat[Yg < hmap[:, None, :]] = 1
    S.col[:] = C(0.32, 0.3, 0.32)
    v = (1 + R.uniform(-0.06, 0.06, (NX, NZ))).astype(f32)[..., None]
    snowline = 55 + 14 * vnoise(NX, NZ, 15, 3, seed=10)
    patches = vnoise(NX, NZ, 10, 3, seed=11)
    topc = np.where((patches < 0.45)[..., None], C(0.85, 0.87, 0.92), C(0.5, 0.45, 0.3)) * v
    rockc = C(0.36, 0.36, 0.4) * v
    mntc = np.where((hmap > snowline)[..., None] | ((hmap > 30) & (patches < 0.5))[..., None], C(0.92, 0.93, 0.97) * v, rockc)
    topc = np.where((mnt > tund)[..., None], mntc, topc)
    asph = C(0.25, 0.25, 0.27) * v
    topc = np.where(road[..., None], asph, topc)
    line = road & (xs == 110) & ((zs // 5) % 2 == 0)
    topc[line] = C(0.8, 0.78, 0.6)
    edge = road & ((xs == 103) | (xs == 117))
    topc[edge] = C(0.75, 0.75, 0.72)
    S.col[xs, hmap - 1, zs] = topc
    # also color the rock faces below snow on mountains
    # poles along the road
    for z in range(30, 260, 26):
        x = 122
        S.put((slice(x, x + 1), slice(1, 13), slice(z, z + 1)), (0.35, 0.27, 0.2))
        S.put((slice(x - 2, x + 3), slice(12, 13), slice(z, z + 1)), (0.3, 0.24, 0.18))
    # snow banks along shoulders
    for z in range(0, 270):
        for x in (101, 119):
            if hsh(x, z, 2) < 0.5:
                S.col[x, 1, z] = C(0.88, 0.9, 0.95); S.mat[x, 1, z] = 1
    S.sun = np.array([-0.12, 0.3, 0.95]); S.sun /= np.linalg.norm(S.sun)
    S.sunc = C(1.5, 0.95, 0.55); S.amb = C(0.42, 0.42, 0.58)
    S.hor = C(1.05, 0.62, 0.42); S.top = C(0.26, 0.34, 0.6); S.fog0, S.fogk = 120, 260
    S.sundisk = 1.4
    return S


# ================= SCENE 4: softly lit modern lab =================
def silhouette():
    T = Scene(40, 40, 60)
    mammoth(T.col, T.mat, 20, 1, 30, f=-1)
    side = (T.mat > 0).any(0)  # (y, z)
    return side[::-1, ::-1].T[::-1].T  # rows: y top->bottom, cols: z


def build4():
    NX, NY, NZ = 110, 48, 110
    S = Scene(NX, NY, NZ)
    xs, zs = np.meshgrid(np.arange(NX), np.arange(NZ), indexing="ij")
    fl = np.where(((xs // 4 + zs // 4) % 2 == 0)[..., None], C(0.78, 0.8, 0.82), C(0.72, 0.74, 0.77))
    S.col[:, 0, :] = fl; S.mat[:, 0, :] = 1
    wall = C(0.86, 0.88, 0.9)
    S.put((slice(0, 2), slice(0, NY), slice(0, NZ)), (0.86, 0.88, 0.9), 1, 0.02)
    S.put((slice(NX - 2, NX), slice(0, NY), slice(0, NZ)), (0.86, 0.88, 0.9), 1, 0.02)
    S.put((slice(0, NX), slice(0, NY), slice(NZ - 2, NZ)), (0.82, 0.85, 0.88), 1, 0.02)
    S.put((slice(0, NX), slice(NY - 2, NY), slice(0, NZ)), (0.9, 0.91, 0.93), 1, 0.02)
    for x in range(10, NX - 10, 20):
        for z in range(10, NZ - 10, 22):
            S.put((slice(x, x + 8), slice(NY - 2, NY - 1), slice(z, z + 4)), (1.0, 1.0, 1.02), 4, 0.0)
    # wall panel seams
    for x in range(0, NX, 12):
        S.col[x, 1:NY - 2, NZ - 2] *= 0.92
    # big display on back wall
    x0, x1, y0, y1 = 25, 85, 9, 41
    S.put((slice(x0 - 1, x1 + 1), slice(y0 - 1, y1 + 1), slice(NZ - 3, NZ - 2)), (0.1, 0.1, 0.12), 1, 0.0)
    Wd, Hd = x1 - x0, y1 - y0
    yy, xx = np.mgrid[0:Hd, 0:Wd]
    scr = C(0.02, 0.06, 0.12) + (C(0.03, 0.1, 0.18) * (1 - yy / Hd)[..., None])
    grid = (xx % 6 == 0) | (yy % 6 == 0)
    scr[grid] += C(0.02, 0.07, 0.1)
    sil = silhouette()
    im = Image.fromarray((sil * 255).astype(np.uint8))
    bb = im.getbbox(); im = im.crop(bb)
    sw = int(Wd * 0.72); shh = int(sw * im.size[1] / im.size[0])
    if shh > Hd - 6: shh = Hd - 6; sw = int(shh * im.size[0] / im.size[1])
    sm = np.asarray(im.resize((sw, shh), Image.BOX), dtype=f32) / 255 > 0.45
    oy, ox = (Hd - shh) // 2 + 1, (Wd - sw) // 2
    mask = np.zeros((Hd, Wd), bool); mask[oy:oy + shh, ox:ox + sw] = sm
    from_edge = mask & ~(np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1))
    scr[mask] = C(0.25, 0.75, 0.95)
    scr[from_edge] = C(0.75, 1.0, 1.1)
    for yv in range(Hd):
        for xv in range(Wd):
            S.col[x0 + xv, y1 - 1 - yv, NZ - 3] = scr[yv, xv]; S.mat[x0 + xv, y1 - 1 - yv, NZ - 3] = 4
    S.scr_mask = mask
    # benches
    for zb in (40, 70):
        S.put((slice(12, 98), slice(1, 7), slice(zb, zb + 7)), (0.62, 0.64, 0.68), 1, 0.02)
        S.put((slice(12, 98), slice(7, 8), slice(zb, zb + 7)), (0.95, 0.95, 0.96), 1, 0.01)
        for xi in range(16, 94, 7):
            k = hsh(xi, zb)
            if k < 0.3:   # tube rack
                S.put((slice(xi, xi + 4), slice(8, 9), slice(zb + 2, zb + 4)), (0.85, 0.86, 0.88))
                for j in range(4):
                    cc = [(0.2, 0.6, 0.9), (0.9, 0.3, 0.4), (0.4, 0.85, 0.5), (0.95, 0.8, 0.3)][j]
                    S.put((slice(xi + j, xi + j + 1), slice(9, 11), slice(zb + 3, zb + 4)), cc, 4, 0.0)
            elif k < 0.55:  # microscope
                S.put((slice(xi, xi + 3), slice(8, 9), slice(zb + 2, zb + 5)), (0.2, 0.21, 0.24))
                S.put((slice(xi + 1, xi + 2), slice(9, 13), slice(zb + 4, zb + 5)), (0.9, 0.9, 0.92))
                S.put((slice(xi + 1, xi + 2), slice(12, 13), slice(zb + 2, zb + 4)), (0.2, 0.21, 0.24))
            elif k < 0.8:  # small monitor
                S.put((slice(xi, xi + 5), slice(8, 12), slice(zb + 5, zb + 6)), (0.15, 0.15, 0.17))
                S.put((slice(xi, xi + 5), slice(9, 11), slice(zb + 4, zb + 5)), (0.2, 0.55, 0.8), 4, 0.05)
            else:  # box device
                S.put((slice(xi, xi + 5), slice(8, 11), slice(zb + 1, zb + 6)), (0.92, 0.93, 0.95))
                S.put((slice(xi + 1, xi + 4), slice(10, 11), slice(zb + 1, zb + 2)), (0.3, 0.9, 0.6), 4, 0.0)
    # tall freezers on the side wall
    for z in range(20, 90, 12):
        S.put((slice(2, 10), slice(1, 30), slice(z, z + 10)), (0.9, 0.91, 0.93), 1, 0.02)
        S.put((slice(9, 10), slice(24, 26), slice(z + 2, z + 4)), (0.3, 0.7, 1.0), 4, 0.0)
    # plants
    for (x, z) in [(100, 95), (100, 25)]:
        S.put((slice(x - 2, x + 2), slice(1, 5), slice(z - 2, z + 2)), (0.85, 0.85, 0.86))
        for k in range(40):
            dx, dy, dz = R.integers(-3, 4), R.integers(5, 12), R.integers(-3, 4)
            S.col[x + dx, dy, z + dz] = C(0.2, 0.5, 0.25) * R.uniform(0.8, 1.2); S.mat[x + dx, dy, z + dz] = 1
    S.sun = None
    S.amb = C(0.95, 0.98, 1.05)
    S.lights = [((55, 25, NZ - 6), (0.25, 0.75, 1.0), 22), ((55, 44, 55), (0.35, 0.35, 0.36), 40)]
    S.hor = C(0.9, 0.9, 0.9); S.top = C(0.9, 0.9, 0.9); S.fog0, S.fogk = 200, 2000
    return S


# ================= shots =================
_S = {}


def scene(k):
    if k not in _S:
        _S[k] = [build1, build2, build3, build4][k]()
    return _S[k]


LEAF_N = 140
LR = np.random.default_rng(99)
leaf_p = np.stack([100 + LR.uniform(-10, 10, LEAF_N), LR.uniform(22, 34, LEAF_N), 52 + LR.uniform(-9, 9, LEAF_N)], 1)
leaf_t0 = LR.uniform(-6, 5, LEAF_N)
leaf_c = np.where(LR.random(LEAF_N)[:, None] < 0.7, C(0.3, 0.55, 0.18), C(0.75, 0.62, 0.2)).astype(f32)
leaf_ph = LR.uniform(0, 6.28, LEAF_N)


def shot(t):
    k = min(int(t // SHOT), 3); tl = t - k * SHOT; p = ease((tl + 0.3) / (SHOT + 0.6))
    S = scene(k)
    c, m = S.col.copy(), S.mat.copy()
    parts = None
    grade = C(1, 1, 1); expo = 1.12
    if k == 0:
        mammoth(c, m, 100, 1, 78, f=-1, mode="reach", sway=1.5 * math.sin(tl * 1.4), reach=0.85 + 0.15 * math.sin(tl * 1.1))
        cam = (100 + 88 - 8 * p, 6.0, 60 + 3 * p); tgt = (100, 23, 57); fov = 60
        age = tl - leaf_t0
        ok = age > 0
        pos = leaf_p.copy()
        pos[:, 1] -= 4.0 * np.maximum(age, 0)
        pos[:, 0] += 1.5 * np.sin(age * 2 + leaf_ph); pos[:, 2] += 1.5 * np.cos(age * 1.6 + leaf_ph) + 0.6 * age
        ok &= pos[:, 1] > 1.2
        parts = (pos[ok], leaf_c[ok], 1.0)
        grade = C(1.02, 1.0, 0.97)
    elif k == 1:
        hm = S.hmap
        for i, (hx, hz) in enumerate(HERD):
            z = int(round(hz - 9 * p * 1.0 - 0.0))
            gy = int(hm[hx - 4:hx + 5, max(z - 12, 0):z + 12].mean())
            for zz in range(z + 14, min(z + 70, S.dims[2])):
                for xx_ in (hx - 5, hx + 5):
                    if hsh(xx_, zz, 4) < 0.7:
                        yy_ = hm[xx_, zz] - 1
                        c[xx_, yy_, zz] = c[xx_, yy_, zz] * C(0.82, 0.85, 0.92)
            mammoth(c, m, hx, gy, z, f=-1, walk=tl * 2 * math.pi * 0.55 + i * 1.3, sway=0.8 * math.sin(tl + i))
        cam = (50 + 20 * p, 115, 330 - 30 * p); tgt = (168, 6, 240 - 14 * p); fov = 50
        grade = C(0.96, 0.99, 1.04)
    elif k == 2:
        z = int(round(96 + 16 * tl / SHOT))
        mammoth(c, m, 110, 1, z, f=1, walk=tl * 2 * math.pi * 0.55, sway=0.6 * math.sin(tl * 1.2))
        cam = (110, 6.5, 10 + 2 * p); tgt = (110, 24, 220); fov = 60
        grade = C(1.04, 0.98, 0.94)
    else:
        cam = (55, 14, 10 + 12 * p); tgt = (55, 24, 109); fov = 58
        grade = C(0.98, 1.0, 1.03); expo = 1.0
    w, h = W // RS, H // RS
    img, depth = render(S, c, m, cam, tgt, fov, w, h)
    if parts is not None and len(parts[0]):
        particles(img, depth, cam, tgt, fov, parts[0], parts[1], parts[2])
    img = tone(img, expo) * grade
    img = np.repeat(np.repeat(img, RS, 0), RS, 1)
    bright = np.clip(img - 0.82, 0, None)
    img = img + blur(bright, 10) * (1.6 if k == 3 else 0.9)
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.25 * (((xx - W / 2) / (W / 2)) ** 2 * 0.6 + ((yy - H / 2) / (H / 2)) ** 2 * 0.4)
    img = img * vig[..., None]
    img = img * min(1, t / 0.4) * min(1, (20.0 - t) / 0.5)
    return np.clip(img, 0, 1)


if __name__ == "__main__":
    if "--stills" in sys.argv:
        ts = [float(a) for a in sys.argv[2].split(",")]
        sheet = Image.new("RGB", (240 * len(ts), 427))
        for i, t in enumerate(ts):
            a = shot(t)
            sheet.paste(Image.fromarray((a * 255).astype(np.uint8)).resize((240, 427)), (i * 240, 0))
        sheet.save(sys.argv[3]); sys.exit()
    out, a0, a1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                           "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(a0, a1):
        a = shot(i / FPS)
        ff.stdin.write((a * 255 + 0.5).astype(np.uint8).tobytes())
        if i % 30 == 0: print("frame", i, flush=True)
    ff.stdin.close(); ff.wait(); print("done", out, flush=True)
