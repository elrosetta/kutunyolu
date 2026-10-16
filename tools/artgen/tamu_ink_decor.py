"""Tamu (Erlik'in Ülkesi) v2 "mürekkep" süsleri (Level._decor_v2 önce "<ad>_tamu_v2" arar).

  dilek_agaci -> kara kayın: yanmış ölü ağaç, kabuk çatlaklarında kor, dallarda sarkan zincir ve demir kafes
  kam_diregi  -> Erlik ongunu: demir direk, tepesinde boynuzlu öküz kafatası (gözleri kor), zincir ve kızıl paçavra
  cira        -> demir mangal: üç ayaklı kazan, içinde alev (ışıma ayrı doku)
  kaya_1/2    -> bazalt kaya (kor çatlaklı)
  mantar_1/2  -> ateş mantarı (kızıl şapka, alt yüzü kor gibi ışır)
  cicek_1/2/3 -> kemik yığını, alev ağzı (çatlaktan çıkan alev), kömürleşmiş dikenli çalı
  balbal      -> kazık: demir kazıkta kafatası, dibinde kemikler
  kule_dikme  -> bazalt sütun parçası (dikeyde döşenir), kule_capraz -> zincir (yatayda döşenir), kule_bag -> demir kelepçe
"""
import json
import math
import os

import numpy as np

import inkkit_ortam as ik
from inkkit_ortam import INK, Sk, Layer, blade, bezier, blob, c01, leaf_shape, poly_path, premul, ribbon, smooth_path, fbm, mix, smoothstep, noise, trunk
import inkkit_yeralti as Y
import inkkit_zemin as Z
from tamu_ink_ground import (ASH_TOP, ASH_MID, ASH_DARK, BAS_A, BAS_B, BAS_C, BAS_L, EMBER, LAVA, LAVA_HI, IRON, IRON_HI,
                             BONE, BONE_SH, _crack)

BONE_HI = (236, 220, 196)
CLOTH = (150, 30, 26)


def _L(sk, w, h):
    L = Layer(w, h)
    L.a = sk.snap()
    return L


def _ash_base(sk, cx, base_y, w, rng, n=24, se=None):
    for _ in range(n):
        x = cx + rng.normal(0, w / 3)
        y = base_y + 2 - rng.uniform(0, 5) * (1 - min(1, abs(x - cx) / w))
        r = rng.uniform(1.4, 3.6)
        c = [ASH_DARK, ASH_MID, ASH_TOP, (22, 14, 16)][int(rng.choice(4, p=[0.3, 0.35, 0.2, 0.15]))]
        sk.c.drawOval(Y.skia_rect(x - r * 1.3, y - r * 0.6, x + r * 1.3, y + r * 0.6), sk.paint(c))
        if se is not None and rng.random() < 0.08:
            se.c.drawCircle(x, y, 1.6, se.paint(EMBER, 0.9, 0.8))


def skull(sk, se, x, y, s, eye=EMBER, horns=False, ink_k=1.0):
    head = smooth_path([(x - 9 * s, y + 6 * s), (x - 11 * s, y - 4 * s), (x - 5 * s, y - 12 * s), (x + 5 * s, y - 12 * s),
                        (x + 11 * s, y - 4 * s), (x + 9 * s, y + 6 * s), (x + 5 * s, y + 12 * s), (x - 5 * s, y + 12 * s)], True, 0.4)
    if horns:
        for sd in (-1, 1):
            hn = bezier((x + sd * 8 * s, y - 6 * s), (x + sd * 26 * s, y - 10 * s), (x + sd * 22 * s, y - 30 * s), 12)
            sk.path(ribbon(hn, np.linspace(7 * s, 0.8, 12)), BONE)
            sk.path(ribbon(hn + np.array([sd * 1.5 * s, 2 * s]), np.linspace(3 * s, 0.5, 12)), BONE_SH, 0.6)
            sk.path(ribbon(hn, np.linspace(7 * s, 0.8, 12)), INK, ink_k, 0, 1.2)
    sk.path(head, BONE)
    sk.c.save()
    sk.c.clipPath(head, doAntiAlias=True)
    sk.path(blob(x + 7 * s, y + 4 * s, 9 * s, 12 * s, 3, 10, 0.1), BONE_SH, 0.55)
    sk.path(blob(x - 4 * s, y - 7 * s, 4 * s, 3 * s, 4, 10, 0.1), BONE_HI, 0.6)
    sk.c.restore()
    for sd in (-1, 1):
        ep = smooth_path([(x + sd * 1.5 * s, y - 2 * s), (x + sd * 5 * s, y - 5 * s), (x + sd * 8 * s, y - 1 * s), (x + sd * 4.5 * s, y + 2 * s)], True, 0.4)
        sk.path(ep, (14, 4, 6))
        sk.c.drawCircle(x + sd * 4.6 * s, y - 1.5 * s, 1.3 * s, sk.paint(eye))
        if se is not None:
            se.c.drawCircle(x + sd * 4.6 * s, y - 1.5 * s, 3.2 * s, se.paint(eye, 0.6, 2 * s))
            se.c.drawCircle(x + sd * 4.6 * s, y - 1.5 * s, 1.0 * s, se.paint(LAVA_HI, 1.0))
    sk.path(poly_path([(x - 1.5 * s, y + 6 * s), (x, y + 3 * s), (x + 1.5 * s, y + 6 * s)]), (14, 4, 6))
    for k in range(5):
        tx = x - 4 * s + k * 2 * s
        sk.path(ribbon([(tx, y + 9 * s), (tx, y + 12 * s)], [0.6 * s, 0.6 * s]), INK, 0.8)
    sk.path(head, INK, ink_k, 0, 1.4)


# ------------------------------------------------------------------ kara kayın
def kara_kayin(seed=12):
    W, Hh = 260, 330
    rng = np.random.default_rng(seed)
    base_y = Hh - 8
    L = Layer(W, Hh)
    sk = Sk(W, Hh)
    se = Sk(W, Hh)
    tips = []
    for (y0, side, ln) in [(120, -1, 100), (92, 1, 110), (66, -1, 80), (48, 1, 74), (150, 1, 70), (170, -1, 64), (30, -1, 50)]:
        x0 = 130 + side * 4
        ang = math.radians(rng.uniform(30, 60))
        p2 = (x0 + side * math.sin(ang) * ln, y0 - math.cos(ang) * ln * 0.7 + rng.uniform(-10, 10))
        p1 = ((x0 + p2[0]) / 2 + rng.uniform(-10, 10), (y0 + p2[1]) / 2 + rng.uniform(-12, 4))
        pts = bezier((x0, y0), p1, p2, 12)
        sk.path(ribbon(pts, np.linspace(10, 1.5, 12)), (34, 24, 26))
        sk.path(ribbon(pts, np.linspace(10, 1.5, 12)), INK, 1.0, 0, 1.4)
        # ince kırık sürgünler
        for j in (5, 8, 10):
            q = pts[j]
            a = math.atan2(pts[j + 1][1] - pts[j - 1][1], pts[j + 1][0] - pts[j - 1][0]) + rng.choice([-1, 1]) * rng.uniform(0.6, 1.1)
            e = (q[0] + math.cos(a) * rng.uniform(12, 26), q[1] + math.sin(a) * rng.uniform(12, 26))
            sk.path(ribbon([q, e], [2.4, 0.4]), (30, 20, 22))
        tips.append(pts)
    L.a = sk.snap()
    arr, xl, yt = trunk(Hh, W, base_y, 130, 34, seed, kind='pine', lean=0.03, bend=0.35, top_y=20, bark=(40, 30, 32),
                        light=(110, 70, 60), rim=(255, 120, 60), ink_w=2.6, taper=0.55, light_side=1.0)
    L.over(arr, xl, yt)
    sk2 = Sk(W, Hh)
    # kabukta kor çatlakları
    for _ in range(5):
        y = rng.uniform(150, base_y - 20)
        x = 130 + rng.uniform(-8, 8)
        pts = [(x, y)]
        for k in range(4):
            pts.append((pts[-1][0] + rng.uniform(-3, 3), pts[-1][1] + rng.uniform(5, 10)))
        _crack(sk2, se, pts, rng.uniform(1.4, 2.4), 0.8)
    # sarkan zincirler ve demir kafes
    for i, pts in enumerate(tips[:4]):
        q = pts[int(rng.integers(6, 10))]
        ln = rng.uniform(40, 110)
        end = Y.chain(sk2, q, (q[0] + rng.uniform(-4, 4), q[1] + ln), 4, link=7, col=(70, 60, 62), hi=IRON_HI, thick=1.8)
        if i == 1:
            cx, cy = q[0], q[1] + ln + 24
            cage = [(cx - 14, cy - 20), (cx + 14, cy - 20), (cx + 16, cy + 20), (cx - 16, cy + 20)]
            sk2.path(smooth_path([(cx - 14, cy - 20), (cx, cy - 30), (cx + 14, cy - 20)], False, 0.5), IRON, 1.0, 0, 2.2)
            for k in range(6):
                t = k / 5
                sk2.path(ribbon([(cx - 14 + 28 * t, cy - 20), (cx - 16 + 32 * t, cy + 20)], [1.6, 1.6]), IRON)
            for yy in (cy - 20, cy + 2, cy + 20):
                sk2.path(ribbon([(cx - 16, yy), (cx + 16, yy)], [2.0, 2.0]), IRON)
            skull(sk2, se, cx, cy + 10, 0.7)
            sk2.path(poly_path(cage), INK, 1.0, 0, 1.0)
        elif i == 2:
            hk = bezier((q[0], q[1] + ln + 2), (q[0] + 10, q[1] + ln + 14), (q[0] - 2, q[1] + ln + 18), 8)
            sk2.path(ribbon(hk, np.linspace(3, 1, 8)), IRON)
            sk2.path(ribbon(hk, np.linspace(3, 1, 8)), INK, 1.0, 0, 0.8)
    # kızıl paçavralar
    for pts in tips[4:6]:
        q = pts[int(rng.integers(4, 8))]
        cp = bezier(q, (q[0] + 6, q[1] + 20), (q[0] + rng.uniform(-6, 12), q[1] + rng.uniform(36, 54)), 10)
        sk2.path(ribbon(cp, np.linspace(6, 3, 10)), CLOTH)
        sk2.path(ribbon(cp, np.linspace(6, 3, 10)), INK, 0.9, 0, 1.1)
    _ash_base(sk2, 130, base_y, 80, rng, 60, se)
    L.over(sk2.snap())
    return L, (W, Hh), (130, base_y), _L(se, W, Hh)


def erlik_ongun(seed=22):
    W, Hh = 130, 250
    rng = np.random.default_rng(seed)
    sk = Sk(W, Hh)
    se = Sk(W, Hh)
    base_y = Hh - 4
    cx = 65
    post = poly_path([(cx - 6, base_y), (cx + 6, base_y), (cx + 5, 70), (cx - 5, 70)])
    sk.path(post, IRON)
    sk.path(poly_path([(cx - 6, base_y), (cx - 2, base_y), (cx - 2, 70), (cx - 5, 70)]), IRON_HI, 0.45)
    for y in (110, 150, 190):
        b = poly_path([(cx - 8, y), (cx + 8, y), (cx + 8, y + 5), (cx - 8, y + 5)])
        sk.path(b, (44, 36, 40))
        sk.path(b, INK, 1.0, 0, 1.0)
        for sd in (-1, 1):   # dikenler
            sk.path(poly_path([(cx + sd * 8, y), (cx + sd * 16, y + 2.5), (cx + sd * 8, y + 5)]), (44, 36, 40))
    sk.path(post, INK, 1.0, 0, 1.8)
    # çapraz kol + sarkan zincir ve paçavra
    arm = poly_path([(cx - 34, 92), (cx + 34, 92), (cx + 34, 98), (cx - 34, 98)])
    sk.path(arm, IRON)
    sk.path(arm, INK, 1.0, 0, 1.2)
    for sd in (-1, 1):
        Y.chain(sk, (cx + sd * 30, 98), (cx + sd * 31, 150 + rng.uniform(-10, 10)), 0, link=6, col=(70, 60, 62), hi=IRON_HI, thick=1.6)
        cp = bezier((cx + sd * 20, 98), (cx + sd * 24, 120), (cx + sd * rng.uniform(16, 26), 140), 8)
        sk.path(ribbon(cp, np.linspace(5, 3, 8)), CLOTH)
        sk.path(ribbon(cp, np.linspace(5, 3, 8)), INK, 0.9, 0, 0.9)
    skull(sk, se, cx, 60, 2.0, horns=True)
    _ash_base(sk, cx, base_y, 30, rng, 26, se)
    return _L(sk, W, Hh), (W, Hh), (cx, base_y), _L(se, W, Hh)


def mangal(seed=32):
    W, Hh = 80, 120
    sk = Sk(W, Hh)
    se = Sk(W, Hh)
    base_y = Hh - 3
    cx = 40
    for sd in (-1, 0, 1):
        leg = ribbon([(cx + sd * 6, 60), (cx + sd * 14, base_y - 10), (cx + sd * 18, base_y)], [3.4, 3, 2.6])
        sk.path(leg, IRON)
        sk.path(leg, INK, 1.0, 0, 1.0)
    bowl = smooth_path([(cx - 22, 46), (cx + 22, 46), (cx + 16, 64), (cx, 68), (cx - 16, 64)], True, 0.35)
    sk.path(bowl, (52, 42, 46))
    sk.path(ribbon([(cx - 20, 50), (cx + 20, 50)], [2, 2]), IRON_HI, 0.6)
    for sd in (-1, 1):   # kulp halkaları
        sk.c.drawCircle(cx + sd * 22, 52, 3.5, sk.paint(IRON, 1.0, 0, 1.6))
    sk.path(bowl, INK, 1.0, 0, 1.8)
    for k in range(5):
        x = cx - 12 + k * 6
        sk.path(ribbon([(x, 47), (x + 2, 40)], [3, 2]), (40, 22, 18))
    # alev (ışıma)
    fl = [(cx - 18, 48), (cx - 14, 30), (cx - 6, 14), (cx - 2, 24), (cx + 4, 6), (cx + 10, 22), (cx + 16, 30), (cx + 18, 48)]
    se.path(smooth_path(fl, True, 0.45), (255, 100, 30), 0.9, 2.5)
    se.path(smooth_path([(cx - 10, 48), (cx - 6, 30), (cx + 2, 16), (cx + 8, 30), (cx + 10, 48)], True, 0.45), (255, 176, 70), 1.0, 1.4)
    se.path(smooth_path([(cx - 5, 48), (cx, 30), (cx + 5, 48)], True, 0.45), (255, 236, 190), 1.0)
    se.c.drawCircle(cx, 40, 24, se.paint((255, 110, 40), 0.18, 12))
    return _L(sk, W, Hh), (W, Hh), (cx, base_y), _L(se, W, Hh)


def bazalt_kaya(seed, rx, ry):
    from otuken_ink import rock
    a = rock(seed, rx, ry, base=(64, 52, 58), moss=(110, 96, 92), ink_w=3.0, light_dir=(0.5, 0.8))
    h, w = a.shape[:2]
    L = Layer(w / ik.K, h / ik.K)
    L.a = a
    sk = Sk(w / ik.K, h / ik.K)
    se = Sk(w / ik.K, h / ik.K)
    rng = np.random.default_rng(seed)
    x = w / ik.K * rng.uniform(0.35, 0.6)
    pts = [(x, h / ik.K - 10)]
    for k in range(4):
        pts.append((pts[-1][0] + rng.uniform(-5, 7), pts[-1][1] - rng.uniform(4, 8)))
    _crack(sk, se, pts, 2.2, 0.8)
    m = Sk(w / ik.K, h / ik.K)
    cov = (a[..., 3] > 0.5).astype(np.float32)
    s = sk.snap() * cov[..., None]
    L.a = s + L.a * (1 - s[..., 3:4])
    E = Layer(w / ik.K, h / ik.K)
    E.a = se.snap() * cov[..., None]
    return L, (w, h), (w / ik.K / 2, h / ik.K - 8), E


def ates_mantari(seed, n):
    W, Hh = 90, 76
    rng = np.random.default_rng(seed)
    sk = Sk(W, Hh)
    se = Sk(W, Hh)
    base_y = Hh - 4
    _ash_base(sk, 45, base_y, 30, rng, 24)
    for k in range(n):
        x = 45 + (k - (n - 1) / 2) * rng.uniform(13, 18)
        h = rng.uniform(16, 38) * (1.0 if k == n // 2 else 0.75)
        r = h * rng.uniform(0.4, 0.55)
        lean = rng.uniform(-0.2, 0.2)
        stem = ribbon([(x, base_y), (x + lean * h * 0.5, base_y - h * 0.5), (x + lean * h, base_y - h)], [r * 0.36, r * 0.28, r * 0.24])
        sk.path(stem, (60, 40, 40))
        sk.path(stem, INK, 1.0, 0, 1.2)
        tx, ty = x + lean * h, base_y - h
        capp = smooth_path([(tx - r, ty + 2), (tx - r * 0.7, ty - r * 0.55), (tx, ty - r * 0.75), (tx + r * 0.7, ty - r * 0.55), (tx + r, ty + 2), (tx, ty + r * 0.15)], True, 0.4)
        sk.path(capp, (120, 24, 20))
        sk.path(smooth_path([(tx - r * 0.7, ty - r * 0.35), (tx - r * 0.2, ty - r * 0.65), (tx + r * 0.1, ty - r * 0.55), (tx - r * 0.4, ty - r * 0.15)], True, 0.4), (200, 70, 40), 0.8)
        sk.path(capp, INK, 1.0, 0, 1.6)
        gill = smooth_path([(tx - r * 0.9, ty + 2), (tx + r * 0.9, ty + 2), (tx, ty + r * 0.15)], True, 0.4)
        sk.path(gill, LAVA)
        se.path(gill, LAVA_HI, 0.9, 1.0)
        se.c.drawCircle(tx, ty + 3, r * 1.3, se.paint(LAVA, 0.25, r * 0.8))
        for _ in range(3):
            sx, sy = tx + rng.uniform(-r * 0.5, r * 0.5), ty - rng.uniform(r * 0.1, r * 0.5)
            sk.c.drawCircle(sx, sy, rng.uniform(1, 1.8), sk.paint((40, 10, 10)))
    return _L(sk, W, Hh), (W, Hh), (45, base_y), _L(se, W, Hh)


def cicek(seed, kind):
    W, Hh = 90, 64
    rng = np.random.default_rng(seed)
    sk = Sk(W, Hh)
    se = Sk(W, Hh)
    base_y = Hh - 3
    if kind == 0:
        _ash_base(sk, 45, base_y, 30, rng, 20)
        for _ in range(5):
            x = rng.uniform(22, 68)
            a = rng.uniform(-0.6, 0.6)
            l = rng.uniform(16, 26)
            p0 = (x - math.cos(a) * l / 2, base_y - 4 - math.sin(a) * l / 2)
            p1 = (x + math.cos(a) * l / 2, base_y - 4 + math.sin(a) * l / 2)
            sk.path(ribbon([p0, p1], [3.6, 3.6]), BONE)
            for q in (p0, p1):
                sk.c.drawCircle(q[0], q[1], 2.8, sk.paint(BONE))
            sk.path(ribbon([p0, p1], [3.6, 3.6]), INK, 0.9, 0, 1.0)
        skull(sk, se, 50, base_y - 14, 1.0)
    elif kind == 1:
        _ash_base(sk, 45, base_y, 26, rng, 16)
        crater = smooth_path([(26, base_y), (34, base_y - 8), (56, base_y - 8), (64, base_y)], True, 0.4)
        sk.path(crater, BAS_B)
        sk.path(crater, INK, 1.0, 0, 1.4)
        sk.path(ribbon([(36, base_y - 7), (54, base_y - 7)], [3, 3]), LAVA)
        for j in range(3):
            x = 38 + j * 7
            h = rng.uniform(18, 34)
            fl = smooth_path([(x - 5, base_y - 6), (x - 3, base_y - h * 0.5), (x + rng.uniform(-2, 2), base_y - h), (x + 3, base_y - h * 0.5), (x + 5, base_y - 6)], True, 0.4)
            se.path(fl, (255, 100, 30), 0.9, 1.5)
            se.path(smooth_path([(x - 2.5, base_y - 6), (x, base_y - h * 0.6), (x + 2.5, base_y - 6)], True, 0.4), LAVA_HI, 1.0)
        se.c.drawCircle(45, base_y - 16, 20, se.paint((255, 110, 40), 0.2, 10))
    else:
        x0 = 45
        for k in range(7):
            a = math.radians(-90 + (k - 3) * 22 + rng.uniform(-8, 8))
            ln = rng.uniform(24, 40)
            p2 = (x0 + math.cos(a) * ln, base_y + math.sin(a) * ln)
            pts = bezier((x0, base_y), ((x0 + p2[0]) / 2 + rng.uniform(-5, 5), (base_y + p2[1]) / 2), p2, 10)
            sk.path(ribbon(pts, np.linspace(2.6, 0.6, 10)), (24, 14, 16))
            for j in range(2, 10, 2):   # dikenler
                q = pts[j]
                sd = rng.choice([-1, 1])
                sk.path(ribbon([q, (q[0] + sd * 4, q[1] - 3)], [1.0, 0.2]), (24, 14, 16))
            if rng.random() < 0.5:
                se.c.drawCircle(p2[0], p2[1], 1.5, se.paint(EMBER, 0.9, 0.8))
        _ash_base(sk, 45, base_y, 26, rng, 18, se)
    return _L(sk, W, Hh), (W, Hh), (45, base_y), _L(se, W, Hh)


def kazik(seed=42):
    W, Hh = 70, 130
    rng = np.random.default_rng(seed)
    sk = Sk(W, Hh)
    se = Sk(W, Hh)
    base_y = Hh - 4
    cx = 35
    st = poly_path([(cx - 3.5, base_y), (cx + 3.5, base_y), (cx + 1, 18), (cx - 1, 18)])
    sk.path(st, IRON)
    sk.path(ribbon([(cx - 2, base_y), (cx - 0.5, 20)], [1.4, 0.4]), IRON_HI, 0.5)
    sk.path(st, INK, 1.0, 0, 1.2)
    skull(sk, se, cx, 44, 1.5)
    for _ in range(4):
        x = rng.uniform(16, 54)
        a = rng.uniform(-0.6, 0.6)
        l = rng.uniform(12, 20)
        p0 = (x - math.cos(a) * l / 2, base_y - 3 - math.sin(a) * l / 2)
        p1 = (x + math.cos(a) * l / 2, base_y - 3 + math.sin(a) * l / 2)
        sk.path(ribbon([p0, p1], [3, 3]), BONE)
        sk.path(ribbon([p0, p1], [3, 3]), INK, 0.9, 0, 0.9)
    _ash_base(sk, cx, base_y, 26, rng, 20, se)
    return _L(sk, W, Hh), (W, Hh), (cx, base_y), _L(se, W, Hh)


def kule_dikme():
    """bazalt sütun parçası (dikeyde döşenir): üç yüzlü altıgen prizma, 64 mantıksal birimde bir yatay eklem."""
    W, Hh = 30, 256
    ys, xs = (np.mgrid[0:ik.P(Hh), 0:ik.P(W)].astype(np.float32) + 0.5) / ik.K
    hw = 10.0
    u = (xs - W / 2) / hw
    cov = np.clip((hw - np.abs(xs - W / 2)) * ik.K + 0.5, 0, 1)
    face = np.where(u < -0.4, 0, np.where(u < 0.38, 1, 2))
    tone = np.array([0.75, 1.15, 0.5], np.float32)[face]
    n = fbm(W, Hh, [1.2, 6], 7, wrap=True)
    col = c01(BAS_B)[None, None, :] * (tone * (1 + 0.1 * n))[..., None]
    rim = smoothstep(0.75, 0.9, u) * (1 - smoothstep(0.95, 1.0, u))
    col = mix(col, c01((255, 120, 56))[None, None, :], (rim * 0.45)[..., None])
    fe = np.minimum(np.abs(u + 0.4), np.abs(u - 0.38)) * hw
    ink = np.maximum(np.clip(1.6 - (hw - np.abs(xs - W / 2)) + 0.5, 0, 1), np.clip(0.9 - fe, 0, 1) * 0.6) * cov
    col = mix(col, c01(INK)[None, None, :], ink[..., None])
    L = Layer(W, Hh)
    L.a = premul(col.astype(np.float32), cov.astype(np.float32))
    sk = Sk(W, Hh)
    for y in (30, 94, 158, 222):
        sk.path(ribbon([(W / 2 - hw, y), (W / 2 - 4, y + 2), (W / 2 + 4, y + 1.5), (W / 2 + hw, y - 1)], [1.6, 1.3, 1.3, 1.6]), INK, 0.9)
        sk.path(ribbon([(W / 2 - hw, y + 1.6), (W / 2 - 4, y + 3.6), (W / 2 + 4, y + 3.1)], [0.6, 0.5, 0.5]), BAS_L, 0.5)
    L.over(sk.snap())
    return L


def kule_capraz():
    """zincir (yatayda döşenir, 256 mantıksal birimde tam sayıda halka)."""
    W, Hh = 256, 16
    sk = Sk(W, Hh)
    Y.chain(sk, (-8, Hh / 2), (W + 8, Hh / 2), 0, link=8.0, col=(70, 60, 62), hi=IRON_HI, thick=2.0)
    return _L(sk, W, Hh)


def kule_bag():
    W, Hh = 28, 14
    sk = Sk(W, Hh)
    p = poly_path([(1, 2), (W - 1, 2), (W - 1, Hh - 2), (1, Hh - 2)])
    sk.path(p, IRON)
    sk.path(poly_path([(1, 2), (W - 1, 2), (W - 1, 4.5), (1, 4.5)]), IRON_HI, 0.6)
    for x in (5, W - 5):
        sk.c.drawCircle(x, Hh / 2, 1.3, sk.paint(IRON_HI))
    sk.path(p, INK, 1.0, 0, 1.2)
    return _L(sk, W, Hh)


def export(save, to8, A, biome='tamu'):
    meta = {}
    tex = 2.0 * ik.K

    def put(name, res):
        L, origin = res[0], res[2]
        nm = '%s_%s_v2' % (name, biome)
        save(to8(L.a), 'decor', nm + '.png')
        h, w = L.a.shape[:2]
        meta[nm] = {"size": [int(w), int(h)], "origin": [int(round(origin[0] * ik.K)), int(round(origin[1] * ik.K))], "texel": tex}
        if len(res) > 3 and res[3] is not None:
            save(to8(Z.edge_fade(res[3].a, int(min(res[3].a.shape[:2]) * 0.28))), 'decor', nm + '_e.png')
            meta[nm]["glow"] = True

    put('dilek_agaci', kara_kayin())
    put('kam_diregi', erlik_ongun())
    put('cira', mangal())
    put('kaya_1', bazalt_kaya(121, 42, 26))
    put('kaya_2', bazalt_kaya(222, 30, 22))
    put('mantar_1', ates_mantari(321, 3))
    put('mantar_2', ates_mantari(322, 2))
    put('cicek_1', cicek(421, 0))
    put('cicek_2', cicek(422, 1))
    put('cicek_3', cicek(423, 2))
    put('balbal', kazik())
    for nm, fn in (('kule_dikme', kule_dikme), ('kule_capraz', kule_capraz), ('kule_bag', kule_bag)):
        L = fn()
        full = '%s_%s_v2' % (nm, biome)
        save(to8(L.a), 'decor', full + '.png')
        meta[full] = {"size": [L.w, L.h], "origin": [0, 0], "texel": tex}
    json.dump(meta, open(os.path.join(A, 'decor', 'decor_v2_%s.json' % biome), 'w', encoding='utf-8'), indent=1)
