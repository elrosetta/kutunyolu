"""Şahmeran Mağaraları v2 "mürekkep" süsleri. Ötüken süs adlarının biyoma özgü karşılıkları
(Level._decor_v2 önce "<ad>_sahmeran_v2" arar): oyunun süs yerleşimi değişmez, yalnızca görünüş biyomlaşır.

  dilek_agaci -> Şahmeran heykeli (taçlı kadın gövdesi, sarmal yılan kuyruğu, kristal taç)
  kam_diregi  -> yılan ongunu (kukuletalı yılan sarılı taş dikme, kehribar gözler)
  cira        -> kristal kandil (taş kaide üstünde ışıyan büyük kristal kümesi)
  kaya_1/2    -> ıslak yosunlu kaya (+ küçük kristal)
  mantar_1/2  -> ışıyan mağara mantarları (teal / kehribar)
  cicek_1/2/3 -> kristal filizleri, mağara zambağı, damlalı eğrelti
  balbal      -> yılan yuvası (yosunlu taş çanakta damarlı yılan yumurtaları)
  kule_dikme  -> sarmal yılan kabartmalı taş sütun parçası (dikeyde döşenir, sarmal adımı = doku boyu / 4)
  kule_bag    -> taş bilezik
Işıma (_e) dokuları oyunda ADD + gölgesiz çizilir. decor_v2_sahmeran.json: boyut, köken, texel, glow.
"""
import json
import math
import os

import numpy as np

import inkkit_ortam as ik
from inkkit_ortam import INK, Sk, Layer, blade, blade_tip, bezier, blob, c01, leaf_shape, poly_path, premul, ribbon, smooth_path, fbm, mix, smoothstep, noise
import inkkit_yeralti as Y
from otuken_ink import rock
from sahmeran_ink_ground import (MOSS_TIP, MOSS_TOP, MOSS_MID, MOSS_DARK, STONE_A, STONE_B, STONE_C, STONE_L, EMER,
                                 EMER_HI, EMER_D, AMETH, AMETH_HI, AMETH_D, AMBER, GLOW)

STATUE = (92, 112, 108)
STATUE_L = (160, 188, 176)
STATUE_D = (44, 56, 60)
SNAKE = (52, 92, 72)
COIL = (74, 98, 92)         # heykelin taş yılan gövdesi (yosun yeşiline çalan taş)
COIL_L = (128, 160, 148)
COIL_B = (96, 112, 100)
SNAKE_L = (126, 182, 140)


def _L(sk, w, h):
    L = Layer(w, h)
    L.a = sk.snap()
    return L


def _moss_base(sk, cx, base_y, w, rng, n=30):
    for _ in range(n):
        x = cx + rng.normal(0, w / 3)
        y = base_y + 2 - rng.uniform(0, 6) * (1 - min(1, abs(x - cx) / w))
        r = rng.uniform(1.6, 4)
        c = [MOSS_DARK, MOSS_MID, MOSS_TOP, MOSS_TIP][int(rng.choice(4, p=[0.3, 0.35, 0.25, 0.1]))]
        sk.c.drawOval(Y.skia_rect(x - r, y - r * 0.7, x + r, y + r * 0.7), sk.paint(c))


def _shade_clip(sk, path, light_poly, dark_poly, light, dark, la=0.55, da=0.6):
    """yolun içine ışık ve gölge lekeleri (kırpılarak) — cel ton bantları"""
    sk.c.save()
    sk.c.clipPath(path, doAntiAlias=True)
    if light_poly is not None:
        sk.path(light_poly, light, la)
    if dark_poly is not None:
        sk.path(dark_poly, dark, da)
    sk.c.restore()


def coil_band(sk, pts, w, col, col_l, belly, ink_k=1.0, scales=True):
    """yılan gövdesi şeridi: gövde + karın + sırt ışığı + pul + mürekkep"""
    pts = np.asarray(pts, np.float64)
    n = len(pts)
    ws = np.asarray(w if np.ndim(w) else [w] * n, np.float64)
    d = np.gradient(pts, axis=0)
    ln = np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-6)
    nrm = np.stack([-d[:, 1] / ln, d[:, 0] / ln], 1)
    sk.path(ribbon(pts, ws), col)
    sk.path(ribbon(pts + nrm * ws[:, None] * 0.3, ws * 0.32), belly, 0.85)
    sk.path(ribbon(pts - nrm * ws[:, None] * 0.25, ws * 0.22), col_l, 0.8)
    if scales:
        for j in range(1, n - 1, 2):
            q = pts[j]
            t = d[j] / ln[j]
            s_ = ws[j] * 0.22
            a = q - t * s_ + nrm[j] * s_ * 0.9
            b = q + t * s_ * 0.5
            c = q - t * s_ - nrm[j] * s_ * 0.9
            sk.path(ribbon([a, b, c], [0.3, 0.9, 0.3]), INK, 0.4 * ink_k)
    sk.path(ribbon(pts, ws), INK, ink_k, 0, 1.5)


# ------------------------------------------------------------------ Şahmeran heykeli
def sahmeran_statue(seed=11):
    W, Hh = 240, 330
    rng = np.random.default_rng(seed)
    sk = Sk(W, Hh)
    se = Sk(W, Hh)
    base_y = Hh - 8
    cx = 120
    # kaide
    plinth = poly_path([(cx - 90, base_y), (cx - 84, base_y - 18), (cx + 84, base_y - 18), (cx + 90, base_y)])
    sk.path(plinth, STATUE_D)
    sk.path(poly_path([(cx - 84, base_y - 18), (cx + 84, base_y - 18), (cx + 86, base_y - 12), (cx - 86, base_y - 12)]), STATUE, 0.9)
    sk.path(plinth, INK, 1.0, 0, 2.0)
    for k in range(9):
        xx = cx - 72 + k * 18
        sk.path(smooth_path([(xx - 6, base_y - 4), (xx, base_y - 10), (xx + 6, base_y - 4)], False, 0.5), INK, 0.6, 0, 1.0)
    # sarmal kuyruk: üç kat halka (arkadan öne), en önde kuyruk ucu
    rings = [(base_y - 32, 74, 22), (base_y - 62, 60, 20), (base_y - 88, 44, 18)]
    for (yy, rx, w) in rings:
        back = np.array([(cx + rx * math.cos(a), yy - 10 * math.sin(a)) for a in np.linspace(0, math.pi, 22)])
        coil_band(sk, back, w * 0.9, tuple(np.array(COIL) * 0.7), tuple(np.array(COIL_L) * 0.7), tuple(np.array(COIL_B) * 0.7), 0.8)
        front = np.array([(cx + rx * math.cos(a), yy + 12 * math.sin(a)) for a in np.linspace(math.pi, 2 * math.pi, 22)])[::-1]
        front = np.array([(cx + rx * math.cos(a), yy + 12 * math.sin(-a)) for a in np.linspace(0, -math.pi, 22)])
        coil_band(sk, np.array([(cx + rx * math.cos(a), yy + 12 * math.sin(a)) for a in np.linspace(0, math.pi, 22)]),
                  w, COIL, COIL_L, COIL_B)
    # kuyruk ucu öne kıvrılır
    tail = bezier((cx + 74, base_y - 32), (cx + 104, base_y - 22), (cx + 92, base_y - 6), 14)
    coil_band(sk, tail, np.linspace(18, 3, 14), COIL, COIL_L, COIL_B)
    # gövdeden insan beline geçiş (yükselen yılan boynu)
    rise = bezier((cx, base_y - 96), (cx - 6, base_y - 130), (cx, base_y - 158), 14)
    coil_band(sk, rise, np.linspace(30, 24, 14), COIL, COIL_L, COIL_B)
    # kadın gövdesi (taş)
    ty = base_y - 158
    torso = smooth_path([(cx - 13, ty + 6), (cx - 18, ty - 20), (cx - 24, ty - 46), (cx - 30, ty - 58), (cx - 12, ty - 66),
                         (cx, ty - 68), (cx + 12, ty - 66), (cx + 30, ty - 58), (cx + 24, ty - 46), (cx + 18, ty - 20), (cx + 13, ty + 6)], True, 0.4)
    sk.path(torso, STATUE)
    _shade_clip(sk, torso, smooth_path([(cx - 30, ty - 60), (cx - 6, ty - 66), (cx - 10, ty - 20), (cx - 16, ty + 4)], True, 0.4),
                smooth_path([(cx + 6, ty - 60), (cx + 32, ty - 58), (cx + 20, ty + 6), (cx + 6, ty + 6)], True, 0.4), STATUE_L, STATUE_D)
    sk.path(torso, INK, 1.0, 0, 2.0)
    # göğüs süsü (gerdanlık) ve kemer
    sk.path(smooth_path([(cx - 16, ty - 58), (cx, ty - 44), (cx + 16, ty - 58)], False, 0.5), INK, 0.9, 0, 1.6)
    sk.c.drawCircle(cx, ty - 44, 3.5, sk.paint(AMBER))
    sk.c.drawCircle(cx, ty - 44, 3.5, sk.paint(INK, 1.0, 0, 1.0))
    se.c.drawCircle(cx, ty - 44, 7, se.paint(AMBER, 0.4, 3))
    sk.path(ribbon([(cx - 15, ty - 4), (cx, ty - 1), (cx + 15, ty - 4)], [3, 4, 3]), STATUE_D)
    # kollar: göğüs önünde kavuşan eller, avuçta kristal
    for s in (-1, 1):
        arm = ribbon([(cx + s * 28, ty - 56), (cx + s * 30, ty - 34), (cx + s * 12, ty - 24)], [9, 8, 7])
        sk.path(arm, STATUE)
        _shade_clip(sk, arm, None, ribbon([(cx + s * 30, ty - 56), (cx + s * 33, ty - 34), (cx + s * 14, ty - 20)], [5, 5, 4]),
                    STATUE_L, STATUE_D, da=0.6 if s > 0 else 0.25)
        sk.path(arm, INK, 1.0, 0, 1.6)
    Y.crystal_cluster(sk, cx, ty - 22, 20, seed + 4, EMER, EMER_HI, EMER_D, ink_w=1.0, glow=se, glow_a=0.9, n=3, spread=0.5)
    # baş, saç, taç
    hy = ty - 84
    hair = smooth_path([(cx - 17, hy - 6), (cx - 14, hy - 20), (cx, hy - 26), (cx + 14, hy - 20), (cx + 17, hy - 6), (cx + 26, hy + 30),
                        (cx + 22, hy + 44), (cx + 12, hy + 18), (cx - 12, hy + 18), (cx - 22, hy + 44), (cx - 26, hy + 30)], True, 0.4)
    sk.path(hair, STATUE_D)
    for s in (-1, 1):
        for k in range(3):
            sk.path(ribbon([(cx + s * (12 + k * 3), hy - 4), (cx + s * (16 + k * 3), hy + 18), (cx + s * (18 + k * 2), hy + 36)], [0.4, 1.2, 0.4]), INK, 0.6)
    sk.path(hair, INK, 1.0, 0, 1.8)
    face = smooth_path([(cx - 11, hy - 10), (cx, hy - 16), (cx + 11, hy - 10), (cx + 10, hy + 6), (cx, hy + 14), (cx - 10, hy + 6)], True, 0.45)
    sk.path(face, STATUE_L)
    _shade_clip(sk, face, None, smooth_path([(cx + 3, hy - 14), (cx + 12, hy - 10), (cx + 10, hy + 6), (cx + 2, hy + 14)], True, 0.4), STATUE_L, STATUE, da=0.8)
    sk.path(face, INK, 1.0, 0, 1.6)
    for s in (-1, 1):   # kapalı gözler, kaşlar
        sk.path(ribbon([(cx + s * 2.5, hy - 2), (cx + s * 5.5, hy - 1), (cx + s * 8.5, hy - 2.5)], [0.4, 1.3, 0.4]), INK, 0.9)
        sk.path(ribbon([(cx + s * 2, hy - 6.5), (cx + s * 6, hy - 8), (cx + s * 9.5, hy - 6.5)], [0.4, 1.0, 0.4]), INK, 0.7)
    sk.path(ribbon([(cx, hy - 1), (cx - 1, hy + 5), (cx + 0.5, hy + 6)], [0.6, 1.0, 0.6]), INK, 0.6)
    sk.path(ribbon([(cx - 3, hy + 9), (cx, hy + 10), (cx + 3, hy + 9)], [0.4, 1.2, 0.4]), INK, 0.8)
    # taç: üç sivri, ortada kristal
    crown = poly_path([(cx - 14, hy - 12), (cx - 15, hy - 24), (cx - 8, hy - 18), (cx, hy - 34), (cx + 8, hy - 18), (cx + 15, hy - 24), (cx + 14, hy - 12)])
    sk.path(crown, (180, 150, 80))
    sk.path(crown, INK, 1.0, 0, 1.4)
    Y.crystal_cluster(sk, cx, hy - 16, 14, seed + 7, EMER, EMER_HI, EMER_D, ink_w=0.8, glow=se, glow_a=1.0, n=3, spread=0.6)
    # omuzlardan yükselen iki yılan başı (koruyucular)
    for s in (-1, 1):
        neck = bezier((cx + s * 26, ty - 58), (cx + s * 50, ty - 80), (cx + s * 44, ty - 108), 12)
        coil_band(sk, neck, np.linspace(13, 10, 12), COIL, COIL_L, COIL_B)
        hx, hy2 = neck[-1]
        head = smooth_path([(hx - 9, hy2 + 2), (hx - 8, hy2 - 8), (hx + s * 4, hy2 - 13), (hx + s * 15, hy2 - 6), (hx + s * 16, hy2 - 1), (hx, hy2 + 5)], True, 0.4)
        sk.path(head, SNAKE)
        sk.path(head, INK, 1.0, 0, 1.4)
        sk.c.drawCircle(hx + s * 5, hy2 - 6, 1.8, sk.paint(AMBER))
        se.c.drawCircle(hx + s * 5, hy2 - 6, 4, se.paint(AMBER, 0.5, 2))
        sk.path(ribbon([(hx + s * 16, hy2 - 1), (hx + s * 22, hy2 + 1), (hx + s * 25, hy2 - 1)], [0.8, 0.6, 0.3]), (190, 60, 60))
    _moss_base(sk, cx, base_y, 100, rng, 70)
    return _L(sk, W, Hh), (W, Hh), (cx, base_y), _L(se, W, Hh)


def snake_idol(seed=21):
    W, Hh = 110, 230
    sk = Sk(W, Hh)
    se = Sk(W, Hh)
    base_y = Hh - 4
    cx = 55
    post = poly_path([(cx - 10, base_y), (cx + 10, base_y), (cx + 8, 60), (cx - 8, 60)])
    sk.path(post, STONE_B)
    _shade_clip(sk, post, poly_path([(cx - 10, base_y), (cx - 4, base_y), (cx - 3, 60), (cx - 8, 60)]),
                poly_path([(cx + 4, base_y), (cx + 10, base_y), (cx + 8, 60), (cx + 3, 60)]), STONE_L, STONE_C)
    sk.path(post, INK, 1.0, 0, 2.0)
    # sarmal yılan (ön yarı kıvrımlar)
    for k in range(4):
        y0 = base_y - 20 - k * 38
        pts = np.array([(cx + 12 * math.sin(a), y0 - 38 * (a + math.pi / 2) / (2 * math.pi)) for a in np.linspace(-math.pi / 2, math.pi / 2, 14)])
        coil_band(sk, pts, 10, SNAKE, SNAKE_L, (150, 160, 120))
    # kukuletalı baş
    hy = 60
    hood = smooth_path([(cx - 22, hy + 10), (cx - 26, hy - 22), (cx - 12, hy - 44), (cx, hy - 50), (cx + 12, hy - 44), (cx + 26, hy - 22),
                        (cx + 22, hy + 10), (cx, hy)], True, 0.4)
    sk.path(hood, SNAKE)
    _shade_clip(sk, hood, smooth_path([(cx - 14, hy + 2), (cx - 18, hy - 22), (cx, hy - 42), (cx + 18, hy - 22), (cx + 14, hy + 2), (cx, hy - 10)], True, 0.4),
                None, SNAKE_L, SNAKE, la=0.45)
    sk.path(hood, INK, 1.0, 0, 2.0)
    for s in (-1, 1):
        sk.path(smooth_path([(cx + s * 10, hy - 26), (cx + s * 16, hy - 18), (cx + s * 11, hy - 10), (cx + s * 6, hy - 18)], True, 0.4), INK, 0.7)
    head = smooth_path([(cx - 7, hy - 30), (cx, hy - 46), (cx + 7, hy - 30), (cx + 3, hy - 20), (cx - 3, hy - 20)], True, 0.4)
    sk.path(head, tuple(np.array(SNAKE_L) * 0.85))
    sk.path(head, INK, 1.0, 0, 1.2)
    for s in (-1, 1):
        sk.c.drawCircle(cx + s * 3.5, hy - 35, 1.8, sk.paint(AMBER))
        se.c.drawCircle(cx + s * 3.5, hy - 35, 4.5, se.paint(AMBER, 0.55, 2.5))
        se.c.drawCircle(cx + s * 3.5, hy - 35, 1.2, se.paint((255, 236, 170), 1.0))
    sk.path(ribbon([(cx, hy - 20), (cx, hy - 12), (cx - 2, hy - 8)], [0.8, 0.6, 0.3]), (190, 60, 60))
    sk.path(ribbon([(cx, hy - 12), (cx + 2, hy - 8)], [0.6, 0.3]), (190, 60, 60))
    # adak kurdeleleri (soluk yeşil, mor)
    rng = np.random.default_rng(seed)
    for k, col in enumerate([(70, 140, 110), (130, 90, 170), (200, 170, 90), (70, 140, 110)]):
        s = -1 if k % 2 == 0 else 1
        q = bezier((cx + s * 9, 100 + k * 6), (cx + s * 16, 130 + k * 6), (cx + s * rng.uniform(10, 18), 160 + k * 8), 10)
        sk.path(ribbon(q, np.linspace(4, 2.6, 10)), col)
        sk.path(ribbon(q, np.linspace(4, 2.6, 10)), INK, 0.9, 0, 0.9)
    _moss_base(sk, cx, base_y, 30, rng, 24)
    return _L(sk, W, Hh), (W, Hh), (cx, base_y), _L(se, W, Hh)


def crystal_lamp(seed=31):
    W, Hh = 90, 150
    sk = Sk(W, Hh)
    se = Sk(W, Hh)
    base_y = Hh - 3
    cx = 45
    rng = np.random.default_rng(seed)
    # dikit kaide (lathe)
    arr, xl, yt = Y.lathe(70, base_y + 2, lambda ys: np.full_like(ys, cx),
                          lambda ys: 6 + (ys - 70) / (base_y - 70) * 12 + 2 * np.sin(ys * 0.3), seed, rock=STONE_B,
                          light=STONE_L, rim=(110, 230, 200), ink_w=1.6, detail=0.8)
    L = Layer(W, Hh)
    L.over(arr, xl, yt)
    Y.crystal_cluster(sk, cx, 78, 50, seed + 1, EMER, EMER_HI, EMER_D, ink_w=1.4, glow=se, glow_a=1.0, n=6, spread=0.9)
    Y.crystal_cluster(sk, cx + 10, 82, 22, seed + 2, AMETH, AMETH_HI, AMETH_D, ink_w=1.0, glow=se, glow_a=0.7, n=3, spread=0.6)
    _moss_base(sk, cx, base_y, 26, rng, 20)
    L.over(sk.snap())
    se.c.drawCircle(cx, 56, 20, se.paint(GLOW, 0.2, 9))
    return L, (W, Hh), (cx, base_y), _L(se, W, Hh)


def kaya(seed, rx, ry, crystal=False):
    a = rock(seed, rx, ry, base=(68, 84, 88), moss=(56, 112, 80), ink_w=3.0)
    h, w = a.shape[:2]
    L = Layer(w / ik.K, h / ik.K)
    L.a = a
    E = None
    if crystal:
        sk = Sk(w / ik.K, h / ik.K)
        se = Sk(w / ik.K, h / ik.K)
        Y.crystal_cluster(sk, w / ik.K * 0.7, h / ik.K - 10, ry * 0.9, seed + 3, EMER, EMER_HI, EMER_D, ink_w=1.0, glow=se, glow_a=0.8, n=3)
        L.over(sk.snap())
        E = _L(se, w / ik.K, h / ik.K)
    res = (L, (w, h), (w / ik.K / 2, h / ik.K - 8))
    return res + ((E,) if E is not None else ())


def mantar(seed, n, cap=(60, 170, 150), glow_c=GLOW):
    W, Hh = 90, 76
    rng = np.random.default_rng(seed)
    sk = Sk(W, Hh)
    se = Sk(W, Hh)
    base_y = Hh - 4
    _moss_base(sk, 45, base_y, 34, rng, 30)
    for k in range(n):
        x = 45 + (k - (n - 1) / 2) * rng.uniform(13, 18) + rng.uniform(-3, 3)
        h = rng.uniform(18, 44) * (1.0 if k == n // 2 else 0.72)
        r = h * rng.uniform(0.32, 0.45)
        lean = rng.uniform(-0.2, 0.2)
        stem = ribbon([(x, base_y), (x + lean * h * 0.5, base_y - h * 0.5), (x + lean * h, base_y - h)], [r * 0.34, r * 0.26, r * 0.22])
        sk.path(stem, (176, 196, 186))
        sk.path(stem, INK, 1.0, 0, 1.3)
        tx, ty = x + lean * h, base_y - h
        capp = smooth_path([(tx - r, ty + 3), (tx - r * 0.85, ty - r * 0.4), (tx, ty - r * 0.8), (tx + r * 0.85, ty - r * 0.4), (tx + r, ty + 3), (tx, ty + r * 0.1)], True, 0.4)
        sk.path(capp, cap)
        _shade_clip(sk, capp, smooth_path([(tx - r * 0.8, ty - r * 0.3), (tx - r * 0.2, ty - r * 0.72), (tx + r * 0.1, ty - r * 0.6), (tx - r * 0.5, ty - r * 0.1)], True, 0.4),
                    smooth_path([(tx - r, ty + 3), (tx + r, ty + 3), (tx + r, ty - r * 0.1), (tx - r, ty - r * 0.1)], True, 0.2),
                    tuple(min(255, c * 1.5 + 20) for c in cap), tuple(c * 0.5 for c in cap))
        # alt yüz lamelleri (ışık saçar)
        for j in range(7):
            lx = tx - r * 0.8 + j * r * 0.27
            sk.path(ribbon([(lx, ty + 1.5), (tx, ty + r * 0.12)], [0.5, 0.2]), INK, 0.5)
        sk.path(capp, INK, 1.0, 0, 1.7)
        se.path(capp, glow_c, 0.5, 2)
        se.c.drawCircle(tx, ty, r * 2.0, se.paint(glow_c, 0.2, r))
        for _ in range(4):
            sx, sy = tx + rng.uniform(-r * 0.6, r * 0.6), ty - rng.uniform(r * 0.1, r * 0.5)
            sk.c.drawCircle(sx, sy, rng.uniform(1, 2), sk.paint((230, 255, 240)))
            se.c.drawCircle(sx, sy, 1.6, se.paint((230, 255, 240), 0.9))
    return _L(sk, W, Hh), (W, Hh), (45, base_y), _L(se, W, Hh)


def cicek(seed, kind):
    W, Hh = 90, 64
    rng = np.random.default_rng(seed)
    sk = Sk(W, Hh)
    se = Sk(W, Hh)
    base_y = Hh - 3
    _moss_base(sk, 45, base_y, 30, rng, 22)
    if kind == 0:
        for cx in (32, 52, 62):
            Y.crystal_cluster(sk, cx + rng.uniform(-4, 4), base_y, rng.uniform(14, 26), int(cx * 9) + seed, EMER, EMER_HI, EMER_D,
                              ink_w=1.0, glow=se, glow_a=0.8, n=int(rng.integers(3, 5)))
    elif kind == 1:
        # mağara zambağı: uzun sap, sarkık ışıyan çan
        for k in range(4):
            x = rng.uniform(22, W - 22)
            h = rng.uniform(26, 48)
            st = bezier((x, base_y), (x + rng.uniform(-4, 4), base_y - h * 0.7), (x + rng.uniform(6, 12) * (1 if k % 2 else -1), base_y - h), 10)
            sk.path(ribbon(st, np.linspace(1.8, 1.0, 10)), MOSS_MID)
            fx, fy = st[-1]
            bell = smooth_path([(fx - 4.5, fy + 1), (fx - 3.5, fy + 8), (fx - 5, fy + 11), (fx, fy + 9), (fx + 5, fy + 11), (fx + 3.5, fy + 8), (fx + 4.5, fy + 1)], True, 0.4)
            sk.path(bell, (180, 230, 220))
            sk.path(bell, INK, 0.9, 0, 0.9)
            se.path(bell, (140, 255, 220), 0.6, 1.5)
            se.c.drawCircle(fx, fy + 10, 7, se.paint(GLOW, 0.25, 4))
            for sgn in (-1, 1):
                sk.path(leaf_shape(x, base_y - 4, 16, 4, -math.pi / 2 + sgn * 0.6), MOSS_TOP)
    else:
        x0 = 45
        for k in range(5):
            ang = math.radians(-90 + (k - 2) * 26 + rng.uniform(-8, 8))
            ln = rng.uniform(30, 44)
            p2 = (x0 + math.cos(ang) * ln, base_y + math.sin(ang) * ln)
            pts = bezier((x0, base_y), ((x0 + p2[0]) / 2, (base_y + p2[1]) / 2 - 6), p2, 12)
            sk.path(ribbon(pts, np.linspace(2.6, 0.8, 12)), (48, 100, 76))
            for j in range(2, 12):
                q = pts[j]
                for sgn in (-1, 1):
                    sk.path(leaf_shape(q[0], q[1], 7 * (1 - j / 14), 3, ang + sgn * 1.0), (72, 136, 96) if sgn < 0 else (44, 96, 72))
            sk.c.drawCircle(p2[0], p2[1] + 2, 1.4, sk.paint((180, 250, 230), 0.95))
    return _L(sk, W, Hh), (W, Hh), (45, base_y), _L(se, W, Hh)


def snake_nest(seed=41):
    W, Hh = 90, 70
    rng = np.random.default_rng(seed)
    sk = Sk(W, Hh)
    se = Sk(W, Hh)
    base_y = Hh - 4
    bowl = smooth_path([(8, base_y - 18), (82, base_y - 18), (76, base_y - 4), (45, base_y + 1), (14, base_y - 4)], True, 0.4)
    eggs = [(30, 22, 11, 14), (50, 26, 12, 15), (40, 32, 10, 13), (62, 30, 10, 12)]
    for (ex, eh, rx, ry) in eggs:
        ey = base_y - eh
        egg = blob(ex, ey, rx, ry, int(ex), 14, 0.03)
        sk.path(egg, (196, 206, 180))
        _shade_clip(sk, egg, blob(ex - rx * 0.3, ey - ry * 0.35, rx * 0.4, ry * 0.4, 3, 10, 0.05),
                    blob(ex + rx * 0.5, ey + ry * 0.3, rx * 0.8, ry * 0.9, 5, 10, 0.05), (236, 244, 224), (110, 130, 116), 0.8, 0.5)
        for _ in range(4):   # damarlar (içten ışıyan)
            pts = [(ex + rng.uniform(-rx, rx) * 0.6, ey + rng.uniform(-ry, ry) * 0.6)]
            for k in range(3):
                pts.append((pts[-1][0] + rng.uniform(-4, 4), pts[-1][1] + rng.uniform(-4, 4)))
            sk.path(ribbon(pts, [0.9, 0.7, 0.5, 0.2]), (70, 180, 150), 0.8)
            se.path(ribbon(pts, [1.6, 1.2, 0.8, 0.3]), GLOW, 0.45, 0.8)
        sk.path(egg, INK, 1.0, 0, 1.4)
    sk.path(bowl, STONE_B)
    _shade_clip(sk, bowl, None, smooth_path([(45, base_y - 18), (82, base_y - 18), (76, base_y), (45, base_y)], True, 0.3), STONE_L, STONE_C)
    for k in range(6):
        xx = 16 + k * 11
        sk.path(smooth_path([(xx - 4, base_y - 8), (xx, base_y - 13), (xx + 4, base_y - 8)], False, 0.5), INK, 0.6, 0, 0.9)
    sk.path(bowl, INK, 1.0, 0, 1.8)
    _moss_base(sk, 45, base_y, 40, rng, 26)
    return _L(sk, W, Hh), (W, Hh), (45, base_y), _L(se, W, Hh)


def kule_dikme():
    """taş sütun parçası, dikeyde döşenir: 256 mantıksal boyda tam 4 sarmal yılan kıvrımı (dikişsiz)."""
    W, Hh = 30, 256
    ys, xs = (np.mgrid[0:ik.P(Hh), 0:ik.P(W)].astype(np.float32) + 0.5) / ik.K
    hw = 9.0
    u = (xs - W / 2) / hw
    cov = np.clip((hw - np.abs(xs - W / 2)) * ik.K + 0.5, 0, 1)
    sz = np.sqrt(np.clip(1 - u * u, 0, 1))
    lam = np.clip(0.55 + 0.45 * (-u) + 0.25 * sz, 0, 1.3)
    n = fbm(W, Hh, [1.2, 6], 5, wrap=True)
    col = c01(STONE_B)[None, None, :] * (0.55 + 0.6 * lam * (1 + 0.1 * n))[..., None]
    ink = np.clip(1.6 - (hw - np.abs(xs - W / 2)) + 0.5, 0, 1) * cov
    col = mix(col, c01(INK)[None, None, :], ink[..., None])
    L = Layer(W, Hh)
    L.a = premul(col.astype(np.float32), cov.astype(np.float32))
    sk = Sk(W, Hh)
    pitch = Hh / 4
    for k in range(-1, 5):
        y0 = Hh - k * pitch
        pts = np.array([(W / 2 + (hw + 1.5) * math.sin(a), y0 - pitch * (a + math.pi / 2) / (2 * math.pi)) for a in np.linspace(-math.pi / 2, math.pi / 2, 14)])
        coil_band(sk, pts, 7.5, SNAKE, SNAKE_L, (130, 140, 108), ink_k=0.9)
    L.over(sk.snap())
    return L


def kule_bag():
    W, Hh = 26, 12
    sk = Sk(W, Hh)
    p = poly_path([(1, 1), (W - 1, 1), (W - 1, Hh - 1), (1, Hh - 1)])
    sk.path(p, STONE_B)
    sk.path(poly_path([(1, 1), (W - 1, 1), (W - 1, 4), (1, 4)]), STONE_L, 0.7)
    for k in range(4):
        xx = 4 + k * 6
        sk.path(smooth_path([(xx - 2.5, 9), (xx, 5), (xx + 2.5, 9)], False, 0.5), INK, 0.7, 0, 0.8)
    sk.path(p, INK, 1.0, 0, 1.4)
    return _L(sk, W, Hh)


def export(save, to8, A, biome='sahmeran'):
    meta = {}
    tex = 2.0 * ik.K

    def put(name, res):
        L, origin = res[0], res[2]
        nm = '%s_%s_v2' % (name, biome)
        save(to8(L.a), 'decor', nm + '.png')
        h, w = L.a.shape[:2]
        meta[nm] = {"size": [int(w), int(h)], "origin": [int(round(origin[0] * ik.K)), int(round(origin[1] * ik.K))], "texel": tex}
        if len(res) > 3 and res[3] is not None:
            import inkkit_zemin as Z
            save(to8(Z.edge_fade(res[3].a, int(min(res[3].a.shape[:2]) * 0.28))), 'decor', nm + '_e.png')
            meta[nm]["glow"] = True

    put('dilek_agaci', sahmeran_statue())
    put('kam_diregi', snake_idol())
    put('cira', crystal_lamp())
    put('kaya_1', kaya(111, 42, 26, crystal=True))
    put('kaya_2', kaya(212, 30, 22))
    put('mantar_1', mantar(311, 3))
    put('mantar_2', mantar(312, 2, cap=(150, 110, 200), glow_c=(190, 140, 255)))
    put('cicek_1', cicek(411, 0))
    put('cicek_2', cicek(412, 1))
    put('cicek_3', cicek(413, 2))
    put('balbal', snake_nest())
    for nm, fn in (('kule_dikme', kule_dikme), ('kule_bag', kule_bag)):
        L = fn()
        full = '%s_%s_v2' % (nm, biome)
        save(to8(L.a), 'decor', full + '.png')
        meta[full] = {"size": [L.w, L.h], "origin": [0, 0], "texel": tex}
    json.dump(meta, open(os.path.join(A, 'decor', 'decor_v2_%s.json' % biome), 'w', encoding='utf-8'), indent=1)
