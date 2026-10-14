"""Kararan Ötüken: paralaks katmanları, piksel sanat teknikleriyle (karanlık tema).
  * gökyüzü: gece; soluk, hasta renkli bir ay (Erlik'in Gözü), ay halesi, kara bulutlar, sönük yıldızlar, karga sürüsü
  * dağlar: ay ışığında kurşuni kayalar, zirvelerde donuk kar, koyu mavi pus
  * uzak orman: sisin içinde kademeli siluet sıraları (uzak = açık/puslu, yakın = koyu)
  * orta orman: solgun meşe ve çamlar, kurumuş çıplak ağaçlar, kararmış gövdeler, ruh ışıkları, solgun mantarlar
  * yakın: kabuk dokulu kapkara gövdeler, kurumuş sarmaşıklar
  * sis: zeminde sürünen, zamanla kayan yarı saydam sis bandı
Işık her yerde sağ üstten (aydan) gelir. Katmanlar yatayda dikişsizdir (W = 1280).
"""
import math
import random
import numpy as np
from PIL import Image

from pixkit import hexrgb, pal, vnoise, fbm, ridged, profile, BAYER4

W, H = 1280, 360
MOON = (470, 118)
MOON_R = 21
L3 = np.array([0.62, -0.55, 0.56]); L3 /= np.linalg.norm(L3)


def bayer(h, w):
    return np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]


def to_image(rgba):
    return Image.fromarray((np.clip(rgba, 0, 1) * 255).astype(np.uint8), 'RGBA')


def run_depth(mask, from_top=True):
    """Her sütunda, maskenin başladığı yerden itibaren kaç piksel içeride olduğumuz."""
    h = mask.shape[0]
    d = np.zeros(mask.shape, int)
    rng_ = range(h) if from_top else range(h - 1, -1, -1)
    prev = np.zeros(mask.shape[1], int)
    for y in rng_:
        prev = np.where(mask[y], prev + 1, 0)
        d[y] = prev
    return d


# ------------------------------------------------------------------ gökyüzü
def sky(w=640, h=360, seed=5):
    rng = np.random.default_rng(seed)
    stops = [(0, '#04050c'), (60, '#080b18'), (120, '#0d1426'), (175, '#131d33'), (225, '#1a2840'), (270, '#223447'), (320, '#2a3d4c'), (360, '#30444f')]
    ys = np.arange(h)
    col = np.zeros((h, 3))
    for (y0, c0), (y1, c1) in zip(stops, stops[1:]):
        m = (ys >= y0) & (ys <= y1)
        t = (ys[m] - y0) / (y1 - y0)
        col[m] = hexrgb(c0) + (hexrgb(c1) - hexrgb(c0)) * t[:, None]
    img = np.broadcast_to(col[:, None, :], (h, w, 3)).copy()
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - MOON[0]) ** 2 + ((yy - MOON[1]) * 1.1) ** 2)
    # ay halesi: soğuk, hasta yeşilimsi gri
    glow = np.clip(1 - d / 210, 0, 1) ** 2.4
    img = img + glow[..., None] * (hexrgb('#8fa6ad') - img) * 0.42
    steps = 40
    img = np.clip(np.floor(img * steps + (bayer(h, w)[..., None] - 0.5) * 0.9) / steps, 0, 1)
    # ay: soluk disk, kenarı hafif aydınlık, üstünde koyu lekeler
    for r, c, dith in ((MOON_R + 8, '#5f717a', 0.35), (MOON_R + 3, '#8c9ca1', 0.6), (MOON_R, '#d9e0d8', 1.0)):
        m = d < r
        if dith < 1.0:
            m &= (bayer(h, w) < dith) | (d < r - 4)
        img[m] = hexrgb(c)
    pr = random.Random(seed)
    for _ in range(9):
        a, rr = pr.uniform(0, math.tau), pr.uniform(0, MOON_R * 0.75)
        cx, cy = MOON[0] + math.cos(a) * rr, MOON[1] + math.sin(a) * rr
        sr = pr.uniform(1.5, 4.5)
        mm = (xx - cx) ** 2 + (yy - cy) ** 2 < sr * sr
        img[mm & (d < MOON_R - 1)] = hexrgb('#b4bfb9')
    # ayın alt sol kenarı gölgeli (hilalimsi derinlik)
    edge = (d < MOON_R) & (d > MOON_R - 3) & ((xx - MOON[0]) - (yy - MOON[1]) < -6)
    img[edge] = hexrgb('#9fa9a4')
    rgba = np.dstack([img, np.ones((h, w))])
    moon_k = np.clip(1 - np.sqrt((xx - MOON[0]) ** 2 + (yy - MOON[1]) ** 2) / 380, 0, 1)
    # kara bulutlar: alt kenarı düz, üstü kabarık; ay tarafında üst kenar gümüşi
    bands = [(52, 26, 160, 0.60, 0.9), (138, 32, 128, 0.57, 1.0), (206, 18, 96, 0.58, 1.0)]
    for cy, thick, cell, thr, op in bands:
        n = fbm(w, h, [cell, cell // 2, cell // 4, cell // 8], [0.5, 0.27, 0.15, 0.08], rng, aspect=0.45)
        base_line = cy + thick * 0.35 + (fbm(w, 1, [cell // 2], [1.0], rng, wrap_y=False)[0] - 0.5) * 6
        top_env = np.clip(1 - np.abs(yy - cy) / thick, 0, 1)
        mask = (n * (0.55 + 0.6 * top_env) > thr) & (yy <= base_line[None, :]) & (yy > cy - thick)
        dtop = run_depth(mask, True)
        dbot = run_depth(mask, False)
        k = moon_k[..., None]
        lit = hexrgb('#3a4860') * (1 - k) + hexrgb('#7d8fa3') * k
        body1 = hexrgb('#1f2838') * (1 - k) + hexrgb('#3b4860') * k
        body2 = hexrgb('#161d2b') * (1 - k) + hexrgb('#262f44') * k
        shad = hexrgb('#0d1119') * (1 - k) + hexrgb('#171d2c') * k
        c = np.where((dtop <= 2)[..., None], lit, np.where((dtop <= 6)[..., None], body1, body2))
        c = np.where((dbot <= 2)[..., None] & (dtop > 2)[..., None], shad, c)
        right = mask & ~np.roll(mask, -1, 1) & (moon_k > 0.35)
        c = np.where(right[..., None], hexrgb('#a9b8c6'), c)
        rgba[mask, :3] = rgba[mask, :3] * (1 - op) + c[mask] * op
    # yıldızlar: sönük, çoğu küçük
    for _ in range(170):
        x, y = pr.randrange(w), pr.randrange(0, 150)
        if rgba[y, x, 2] < 0.2 and np.sqrt((x - MOON[0]) ** 2 + (y - MOON[1]) ** 2) > MOON_R + 10:
            b = pr.random()
            rgba[y, x, :3] = hexrgb('#aebbd6') if b > 0.4 else hexrgb('#6c7a9c')
            if b > 0.95:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rgba[y + dy, x + dx, :3] = hexrgb('#5d6a8c')
    # karga sürüsü: ayın önünden geçen siluetler
    for _ in range(11):
        x, y = pr.randint(380, 600), pr.randint(90, 175)
        for dx, dy in ((-2, -1), (-1, 0), (0, 0), (1, 0), (2, -1)):
            rgba[y + dy, x + dx, :3] = hexrgb('#05060a')
    return to_image(rgba)


# ------------------------------------------------------------------ dağlar
def _blur1d(a, r):
    k = np.ones(2 * r + 1) / (2 * r + 1)
    p = np.concatenate([a[-r:], a, a[:r]])
    return np.convolve(p, k, mode='valid')


def _range_layer(ridge, pal_rock, pal_snow, haze, haze_from, rng, snow_depth=18.0):
    rgba = np.zeros((H, W, 4))
    yy = np.arange(H)[:, None].astype(float)
    below = yy - ridge[None, :]
    inside = below >= 0
    sl = np.roll(ridge, -2) - np.roll(ridge, 2)
    s_small = _blur1d(sl, 3)
    s_big = _blur1d(sl, 14)
    frac = np.clip(below / 70.0, 0, 1)
    facet = s_small[None, :] * (1 - frac) + s_big[None, :] * frac
    gully = ridged(W, H, [32, 16], [0.7, 0.3], rng, aspect=3.0)
    detail = fbm(W, H, [40, 20, 10], [0.5, 0.3, 0.2], rng)
    lam = 0.5 + np.tanh(facet * 0.45) * 0.38 + (gully - 0.6) * 0.22 + (detail - 0.5) * 0.12
    b = bayer(H, W)
    lvl = np.digitize(lam + (b - 0.5) * 0.06, [0.3, 0.47, 0.64])
    col = pal_rock[3 - lvl]
    strata = (np.sin(yy * 0.55 + detail * 6.0) > 0.93) & (lvl < 2)
    col = np.where(strata[..., None], pal_rock[3], col)
    peakiness = np.clip((ridge.max() - ridge) / (ridge.max() - ridge.min() + 1e-6), 0, 1)[None, :]
    pk = np.clip((peakiness - 0.38) / 0.62, 0, 1) ** 1.3
    sd = snow_depth * pk + (gully - 0.55) * 7
    streak = (gully > 0.78) & (below < sd * 2.2 + 4) & (pk > 0.05)
    snow = inside & ((below < sd) | streak)
    scol = np.where((facet > 0)[..., None], pal_snow[0], pal_snow[1])
    col = np.where(snow[..., None], scol, col)
    hz = np.clip((yy - haze_from) / 70.0, 0, 1) ** 1.2
    hz = np.clip(np.floor(hz * 12 + (b - 0.5)) / 12, 0, 1)
    col = col * (1 - hz[..., None] * 0.8) + hexrgb(haze) * hz[..., None] * 0.8
    rgba[inside, :3] = col[inside]
    rgba[inside, 3] = 1.0
    edge = inside & ~np.roll(inside, 1, 0)
    lit_edge = edge & (sl > 0)[None, :]
    rgba[lit_edge, :3] = np.where(snow[lit_edge][:, None], pal_snow[0], pal_rock[0])
    return rgba


def mountains(seed=8):
    rng = np.random.default_rng(seed)
    p_far = profile(W, [320, 160, 80, 40, 20], [0.5, 0.26, 0.14, 0.07, 0.03], rng)
    ridge_far = 210 - (p_far - p_far.min()) / (p_far.max() - p_far.min()) * 86
    far = _range_layer(ridge_far, pal('#3d4760', '#303a50', '#262e42', '#1e2536'), pal('#7f8ca6', '#5c6882'), '#1f2a3d', 200, rng, 16)
    p_near = profile(W, [256, 128, 64, 32, 16], [0.5, 0.26, 0.14, 0.07, 0.03], rng)
    ridge_near = 244 - (p_near - p_near.min()) / (p_near.max() - p_near.min()) * 64
    near = _range_layer(ridge_near, pal('#2a3248', '#20273a', '#181d2e', '#121626'), pal('#66718c', '#48516b'), '#161d2c', 228, rng, 10)
    a = near[..., 3:4]
    far[..., :3] = far[..., :3] * (1 - a) + near[..., :3] * a
    far[..., 3] = np.maximum(far[..., 3], near[..., 3])
    return to_image(far)


# ------------------------------------------------------------------ ağaç çizimi
GREEN = pal('#0b1510', '#122018', '#192d21', '#213b29', '#2b4a32', '#385a3c')
TEAL = pal('#0a1515', '#10201d', '#162c28', '#1e3933', '#28483f', '#34584c')
RUST = pal('#1c110c', '#2b1a12', '#3b2518', '#4d321f', '#5f4027', '#704e31')
WINE = pal('#1a0d10', '#291317', '#391b1f', '#4a2528', '#5b3030', '#6d3c3b')
PALE = pal('#1a190f', '#292713', '#3a371a', '#4b4722', '#5c572b', '#6e6936')
TRUNK = pal('#0a0808', '#130f0f', '#1c1615', '#261f1c', '#322924')
BIRCH = pal('#0f0f11', '#45474b', '#5e6165', '#75787d')
HAZE = hexrgb('#283847')
WISP = (hexrgb('#9df2e0'), hexrgb('#3f7a72'))


def fade(P, k, col=HAZE):
    return P * (1 - k) + col * k


class Canvas2:
    """Yatay sarmalı RGBA tuval (genişlik W): sağdan taşan, soldan girer → dikişsiz."""
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.rgba = np.zeros((h, w, 4))

    def px(self, x, y, c, a=1.0):
        y = int(y)
        if 0 <= y < self.h:
            x = int(math.floor(x)) % self.w
            if a >= 1.0:
                self.rgba[y, x, :3] = c
                self.rgba[y, x, 3] = 1.0
            else:
                old_a = self.rgba[y, x, 3]
                self.rgba[y, x, :3] = self.rgba[y, x, :3] * (1 - a) + np.asarray(c) * a if old_a > 0 else c
                self.rgba[y, x, 3] = max(old_a, a)

    def blob(self, cx, cy, r, c_mid, c_lit, c_shad):
        R = int(math.ceil(r)) + 1
        for dy in range(-R, R + 1):
            for dx in range(-R, R + 1):
                d2 = dx * dx + dy * dy
                if d2 > r * r:
                    continue
                edge = d2 > (r - 1.0) ** 2
                c = c_mid
                if edge and dx - dy > 0:
                    c = c_lit
                elif edge and dx - dy < -1:
                    c = c_shad
                self.px(cx + dx, cy + dy, c)


def canopy(cv, cx, cy, rx, ry, P, rng, spacing=3.2, rmin=1.8, rmax=3.0, sparse=0.0):
    pts = []
    y = cy - ry
    while y <= cy + ry:
        x = cx - rx
        while x <= cx + rx:
            jx, jy = x + rng.uniform(-1.4, 1.4), y + rng.uniform(-1.4, 1.4)
            ux, uy = (jx - cx) / rx, (jy - cy) / ry
            if ux * ux + uy * uy <= rng.uniform(0.78, 1.05) and rng.random() >= sparse:
                pts.append((jx, jy, ux, uy))
            x += spacing
        y += spacing
    pts.sort(key=lambda p: (p[3] * 0.6 - p[2] * 0.4))
    for jx, jy, ux, uy in pts:
        nz = math.sqrt(max(0.0, 1 - min(1.0, ux * ux + uy * uy)))
        lam = max(0.0, ux * L3[0] + uy * L3[1] + nz * L3[2])
        v = lam - 0.22 * (1 - nz) + rng.uniform(-0.07, 0.07)
        i = int(np.clip(np.digitize(v, [0.12, 0.3, 0.48, 0.66, 0.82]), 0, 5))
        cv.blob(jx, jy, rng.uniform(rmin, rmax), P[i], P[min(5, i + 1)], P[max(0, i - 1)])
        if i >= 4 and rng.random() < 0.12:
            cv.px(jx + 1, jy - 1, P[5])


def big_canopy(cv, cx, cy, rx, ry, P, rng, sparse=0.0):
    """Ana taç + çevresinde 3-5 alt küme: daha doğal, düzensiz siluet."""
    subs = [(cx, cy, rx, ry)]
    for k in range(rng.randint(3, 5)):
        a = rng.uniform(-math.pi, 0.2)
        d = rng.uniform(0.45, 0.75)
        subs.append((cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d, rx * rng.uniform(0.45, 0.6), ry * rng.uniform(0.45, 0.6)))
    subs.sort(key=lambda s: s[1])
    for sx, sy, srx, sry in subs:
        canopy(cv, sx, sy, srx, sry, P, rng, sparse=sparse)


def trunk(cv, x, base_y, top_y, w, P, rng, birch=False, branches=2):
    for y in range(int(top_y), int(base_y) + 1):
        t = (y - top_y) / max(1, base_y - top_y)
        ww = w * (0.72 + 0.35 * t) + (3.0 * (t - 0.86) / 0.14 if t > 0.86 else 0)
        x0 = x - ww / 2
        n = int(math.ceil(ww))
        for k in range(n):
            rel = k / max(1, n - 1)
            if birch:
                c = BIRCH[1] if rel < 0.25 else (BIRCH[3] if rel > 0.7 else BIRCH[2])
                if math.sin(y * 0.9 + x * 0.3) > 0.86 and 0.15 < rel < 0.9:
                    c = BIRCH[0]
            else:
                c = P[1] if rel < 0.3 else (P[3] if rel > 0.72 else P[2])
                if (int(y * 0.5 + k * 3 + x) % 6 == 0) and 0.2 < rel < 0.75:
                    c = P[1]
            cv.px(x0 + k, y, c)
    for b in range(branches):
        side = rng.choice([-1, 1])
        by = top_y + rng.uniform(4, 24)
        ln = rng.uniform(10, 22)
        for s in range(int(ln)):
            for th in range(2 if s < ln * 0.6 else 1):
                cv.px(x + side * (w * 0.3 + s), by - s * 0.75 - th, P[2] if th == 0 else P[1])


def _bare_branch(cv, x, y, ang, ln, w, P, rng, depth):
    """Kurumuş dal: kıvrılarak incelir, 2-3 kez çatallanır."""
    for s in range(int(ln)):
        ang += rng.uniform(-0.09, 0.09)
        x += math.cos(ang); y += math.sin(ang)
        ww = max(1, int(round(w * (1 - s / ln))))
        for k in range(ww):
            cv.px(x + k - ww / 2, y, P[1] if k == ww - 1 else P[2])
    if depth > 0:
        for side in (-1, 1):
            if rng.random() < 0.8:
                _bare_branch(cv, x, y, ang + side * rng.uniform(0.35, 0.9), ln * rng.uniform(0.5, 0.75), w * 0.6, P, rng, depth - 1)


def dead_tree(cv, x, base_y, height, P, rng):
    """Yaprağını dökmüş, kıvrık dallı ölü ağaç."""
    top = base_y - height * 0.55
    trunk(cv, x, base_y, top, 6.0, P, rng, branches=0)
    for k in range(rng.randint(3, 5)):
        a = -math.pi / 2 + rng.uniform(-1.1, 1.1)
        _bare_branch(cv, x + rng.uniform(-2, 2), top + rng.uniform(0, 10), a, height * rng.uniform(0.25, 0.42), 3.0, P, rng, 2)


def pine(cv, x, base_y, height, P, rng):
    trunk(cv, x, base_y, base_y - height * 0.95, 3.4, TRUNK, rng, branches=0)
    tiers = max(4, int(height / 9))
    for i in range(tiers):
        ty = base_y - height + i * (height * 0.86 / tiers)
        half = 3 + i * (height * 0.045)
        for k in range(int(half * 2 + 1)):
            dx = -half + k
            yb = ty + 7 + abs(dx) / max(1.0, half) * 3.5 + (1 if k % 2 else 0)
            for yy in range(int(ty + abs(dx) * 0.9), int(yb) + 1):
                side = dx / max(1.0, half)
                v = 0.55 + side * 0.35 - (yy - ty) / 14.0 * 0.25 + rng.uniform(-0.08, 0.08)
                cv.px(x + dx, yy, P[int(np.clip(np.digitize(v, [0.15, 0.35, 0.55, 0.72, 0.88]), 0, 5))])


def bush(cv, x, y, r, P, rng):
    canopy(cv, x, y, r * 1.5, r, P, rng, spacing=2.6, rmin=1.4, rmax=2.4)


def fern(cv, x, base_y, P, rng):
    for k in range(rng.randint(3, 6)):
        a = -math.pi / 2 + rng.uniform(-1.2, 1.2)
        ln = rng.uniform(6, 13)
        for s in range(int(ln)):
            px_, py_ = x + math.cos(a) * s, base_y + math.sin(a) * s + s * s * 0.025
            cv.px(px_, py_, P[3] if s < ln * 0.6 else P[4])
            if s % 2 == 0 and s > 1:
                cv.px(px_ - 1, py_ + 1, P[2])
                cv.px(px_ + 1, py_ + 1, P[3])


def wisp(cv, x, y, rng):
    """Ruh ışığı: parlak çekirdek + soluk hale (arka planda sönük yanar)."""
    core, halo = WISP
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        cv.px(x + dx, y + dy, halo)
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        if rng.random() < 0.5:
            cv.px(x + dx, y + dy, halo, 0.5)
    cv.px(x, y, core)


def fungus(cv, x, y, rng):
    """Solgun mantar kümesi: gri-yeşil şapkalar, hafif aydınlık uçlar."""
    cap = rng.choice([hexrgb('#8fa69c'), hexrgb('#7f8ca0'), hexrgb('#a3a08a')])
    for k in range(rng.randint(2, 4)):
        hx, hy = x + k * 2 + rng.uniform(-1, 1), y - rng.randint(1, 4)
        cv.px(hx, hy + 1, cap * 0.55)
        cv.px(hx, hy, cap)
        cv.px(hx + 1, hy, cap * 0.8)
        cv.px(hx, hy - 1, cap * 1.15)


# ------------------------------------------------------------------ uzak orman
def forest_far(seed=9):
    rng = random.Random(seed)
    cv = Canvas2(W, H)
    rows = [(240, pal('#2c3b4b', '#344450', '#3d4e59', '#475964', '#52646e', '#5d6f78'), 0.5),
            (252, pal('#253441', '#2c3c47', '#34454f', '#3d5059', '#475b63', '#51656d'), 0.65),
            (265, pal('#1e2c36', '#24333c', '#2b3c45', '#33464d', '#3c5057', '#455a60'), 0.8),
            (280, pal('#18222a', '#1d2930', '#233139', '#2a3b42', '#32454b', '#3a4e54'), 1.0),
            (296, pal('#121b21', '#162027', '#1b272e', '#213036', '#28393f', '#2f4247'), 1.2)]
    for base, P, scale in rows:
        x = rng.uniform(0, 6)
        while x < W:
            hgt = rng.uniform(16, 32) * scale
            r_kind = rng.random()
            if r_kind < 0.55:
                half = hgt * 0.3
                for yy in range(int(base - hgt), int(base) + 1):
                    t = (yy - (base - hgt)) / hgt
                    ww = half * t * (1.0 if int(yy) % 3 else 0.82)
                    for dx in range(-int(ww), int(ww) + 1):
                        side = dx / max(1.0, ww)
                        i_c = 3 if side > 0.3 else (1 if side < -0.35 else 2)
                        if yy == int(base - hgt):
                            i_c = 4
                        cv.px(x + dx, yy, P[i_c])
            elif r_kind < 0.72:
                # kuru ağaç silueti
                for yy in range(int(base - hgt * 0.8), int(base) + 1):
                    cv.px(x, yy, P[1]); cv.px(x + 1, yy, P[1])
                for b in range(3):
                    a = -math.pi / 2 + rng.uniform(-1.0, 1.0)
                    for s in range(int(hgt * 0.35)):
                        cv.px(x + math.cos(a) * s, base - hgt * 0.75 + math.sin(a) * s, P[1])
            else:
                r = hgt * 0.45
                cy = base - r * 0.9
                for dy in range(-int(r), int(r) + 1):
                    for dx in range(-int(r * 1.15), int(r * 1.15) + 1):
                        ang = math.atan2(dy, dx)
                        rr = r * (0.86 + 0.14 * math.sin(ang * 5 + x))
                        if dx * dx / 1.3 + dy * dy <= rr * rr:
                            side = (dx - dy * 0.6) / max(1.0, r)
                            i_c = 4 if side > 0.75 else (3 if side > 0.25 else (1 if side < -0.45 else 2))
                            cv.px(x + dx, cy + dy, P[i_c])
            x += rng.uniform(5, 11) * scale
        fill = cv.rgba[int(base):, :, 3] == 0
        cv.rgba[int(base):, :, :3][fill] = P[1]
        cv.rgba[int(base):, :, 3][fill] = 1.0
        b = bayer(H, W)
        yy = np.arange(H)[:, None]
        hz = np.clip(1 - np.abs(yy - (base + 2)) / 10.0, 0, 1) * 0.36
        hz = np.floor(hz * 14 + (b - 0.5) * 0.8) / 14
        m = cv.rgba[..., 3] > 0
        mixc = cv.rgba[..., :3] * (1 - hz[..., None]) + hexrgb('#3b4f5e') * hz[..., None]
        cv.rgba[m, :3] = mixc[m]
    return to_image(cv.rgba)


# ------------------------------------------------------------------ orta orman
def forest_mid(seed=10):
    rng = random.Random(seed)
    cv = Canvas2(W, H)
    # arka sıra: daha küçük, puslu
    x = rng.uniform(0, 20)
    while x < W:
        kind = rng.choice(['oak', 'oak', 'dead', 'pine', 'pine', 'birch', 'dead'])
        k = 0.42
        base = 312
        if kind == 'pine':
            pine(cv, x, base, rng.uniform(70, 110), fade(TEAL, k), rng)
        elif kind == 'dead':
            dead_tree(cv, x, base, rng.uniform(70, 100), fade(TRUNK, k), rng)
        else:
            P = fade({'oak': GREEN, 'birch': PALE}[kind], k)
            top = base - rng.uniform(60, 85)
            trunk(cv, x, base, top + 14, 3.6, fade(TRUNK, k), rng, birch=(kind == 'birch'), branches=1)
            canopy(cv, x, top, rng.uniform(16, 24), rng.uniform(13, 19), P, rng, spacing=3.0, rmin=1.6, rmax=2.6, sparse=0.2)
        x += rng.uniform(22, 48)
    # ön sıra: büyük, gruplanmış ağaçlar; aralarda ölü ağaçlar
    x = rng.uniform(0, 30)
    while x < W:
        group = rng.randint(1, 3)
        for g in range(group):
            gx = x + g * rng.uniform(26, 40)
            kind = rng.choice(['oak', 'oak', 'rust', 'wine', 'birch', 'pine', 'dead', 'dead'])
            base = 322
            if kind == 'pine':
                pine(cv, gx, base, rng.uniform(130, 175), TEAL, rng)
            elif kind == 'dead':
                dead_tree(cv, gx, base, rng.uniform(120, 170), TRUNK, rng)
            else:
                P = {'oak': GREEN, 'rust': RUST, 'wine': WINE, 'birch': PALE}[kind]
                cy = base - rng.uniform(78, 108)
                rx, ry = rng.uniform(30, 46), rng.uniform(24, 34)
                trunk(cv, gx, base, cy + ry * 0.4, 7.0 if kind != 'birch' else 4.8, TRUNK, rng, birch=(kind == 'birch'), branches=3)
                big_canopy(cv, gx, cy, rx, ry, P, rng, sparse=0.28)
        x += group * 34 + rng.uniform(60, 130)
    # çalılık bandı, eğreltiler, solgun mantarlar
    x = 0.0
    while x < W:
        P = rng.choice([GREEN, GREEN, TEAL, PALE, GREEN])
        bush(cv, x, 314 + rng.uniform(-4, 3), rng.uniform(6, 13), P, rng)
        x += rng.uniform(8, 16)
    for k in range(60):
        fern(cv, rng.uniform(0, W), 324, GREEN, rng)
    for k in range(26):
        fungus(cv, rng.uniform(0, W), rng.uniform(318, 330), rng)
    for yy in range(318, H):
        row = cv.rgba[yy]
        m = row[:, 3] == 0
        row[m, :3] = GREEN[1] if yy > 326 else GREEN[2]
        row[m, 3] = 1.0
    # ruh ışıkları: ağaçların arasında süzülen soluk ışıklar
    for k in range(22):
        wisp(cv, rng.uniform(0, W), rng.uniform(190, 318), rng)
    return to_image(cv.rgba)


# ------------------------------------------------------------------ yakın katman
def forest_near(seed=11):
    rng = random.Random(seed)
    cv = Canvas2(W, H)
    BARK = pal('#070607', '#0e0c0c', '#161212', '#1e1917', '#2a231f')
    MOSS = pal('#0a1710', '#112116', '#182d1c', '#213b24')
    VINE = pal('#1a1512', '#262019', '#332b20')
    for k in range(2):
        xx = k * W / 2 + rng.uniform(0, W / 4)
        w = rng.uniform(9, 14)
        for y in range(H):
            ww = w + 14 * max(0, (y - 300)) / 60
            n = int(ww * 2)
            for j in range(n):
                rel = j / n
                i_c = 1 if rel < 0.25 else (3 if rel > 0.78 else 2)
                if math.sin(y * 0.15 + j * 0.9) > 0.85:
                    i_c = max(0, i_c - 1)
                if rel > 0.88 and math.sin(y * 0.2) > 0.2:
                    i_c = 4
                cv.px(xx - ww + j, y, BARK[i_c])
        for j in range(4):
            my = rng.uniform(30, 300)
            for dy in range(-10, 11):
                for dx in range(-5, 6):
                    if dx * dx / 25 + dy * dy / 100 <= rng.uniform(0.7, 1.0):
                        cv.px(xx - w * 0.5 + dx, my + dy, MOSS[2 if dx > 1 else 1])
        # kurumuş sarmaşıklar: gövdeden sarkan, yer yer düğümlü
        for j in range(4):
            vx = xx + rng.uniform(-w, w)
            ln = rng.uniform(60, 170)
            for s in range(int(ln)):
                px_ = vx + math.sin(s * 0.08 + j) * 2.0
                cv.px(px_, s, VINE[1])
                if s % 11 == 0:
                    cv.blob(px_ + 2, s, 2.0, VINE[1], VINE[2], VINE[0])
    for k in range(140):
        gx = rng.uniform(0, W)
        hh = rng.uniform(10, 36)
        d = rng.choice([-4, 4])
        for s in range(int(hh)):
            cv.px(gx + (s / hh) ** 2 * d, H - 1 - s, MOSS[1] if s < hh * 0.6 else MOSS[2])
    return to_image(cv.rgba)


# ------------------------------------------------------------------ sis
def fog(seed=12):
    """Zeminde sürünen sis: alt banda doğru yoğunlaşan, dikişsiz, dithered yarı saydam katman."""
    rng = np.random.default_rng(seed)
    n = fbm(W, H, [320, 160, 80, 40], [0.45, 0.3, 0.15, 0.1], rng, aspect=0.35)
    yy = np.arange(H)[:, None].astype(float)
    band = np.clip((yy - 232) / 95.0, 0, 1) ** 1.4
    a = band * np.clip((n - 0.32) / 0.5, 0, 1) * 0.62
    b = bayer(H, W)
    a = np.clip(np.floor(a * 10 + (b - 0.5) * 0.9) / 10, 0, 1)
    rgba = np.zeros((H, W, 4))
    rgba[..., :3] = hexrgb('#3f5262')
    rgba[..., 3] = a
    return to_image(rgba)
