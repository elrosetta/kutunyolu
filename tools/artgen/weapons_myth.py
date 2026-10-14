"""Türk mitolojisi silah, kalkan ve teçhizat sprite'ları (her malzeme için ayrı renk).

Silahlar sağa bakar, kabza/tutamak (0,0) noktasındadır. Oyun bu noktayı kahramanın
el çapasına yerleştirip el açısıyla döndürür.
"""
import json
import math
import os
import numpy as np
from raster import Canvas, Mat, ramp, hx
from materials import M

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ITEMS = json.load(open(os.path.join(ROOT, 'data', 'items.json'), encoding='utf-8'))
MATS = {m['id']: m for m in ITEMS['materials']}


def mats_for(mid):
    m = MATS[mid]
    blade = Mat(ramp(m['hue'], m['sat'], m['val'], spread=0.45), spec=m['spec'], emissive=m['glow'])
    accent = M['gold'] if mid not in ('altin', 'tunc') else M['iron']
    glow = {'od_tasi': M['amber'], 'ayaz': M['kut'], 'gok_demiri': M['corrupt'], 'ruh': M['kut'], 'yesim': M['kut']}.get(mid, M['nazar_b'])
    return {'b': blade, 'a': accent, 'g': M['leather'], 'w': M['wood'], 'glow': glow, 'red': M['red_paint'], 'turq': M['turq'], 'white': M['fur']}


def _arc(c, pts, r, mat, z=0):
    for a, b in zip(pts, pts[1:]):
        c.capsule(a, b, r, r, mat, z=z)


BOWS = ('turk_yayi', 'akinci_yayi', 'saganak_yayi', 'tufan_yayi', 'od_oklari')


def _limb_pts(half, depth, recurve, grip_x=3.5, n=16):
    """Kurulu kompozit yay profili: tutamaktan geriye kıvrılan kollar, uçlarda (siyah) öne kırılma."""
    pts = []
    for i in range(-n, n + 1):
        t = i / n
        x = grip_x - depth * t * t + recurve * (abs(t) ** 6)
        pts.append((x, half * t, t))
    return pts


def _limbs(c, pts, mat, r0, z=1, tip_mat=None, band=None):
    for (x0, y0, t0), (x1, y1, t1) in zip(pts, pts[1:]):
        tt = max(abs(t0), abs(t1))
        m = tip_mat if (tip_mat is not None and tt > 0.8) else mat
        if band is not None and 0.38 < tt < 0.52:
            m = band
        r = r0 * (1.0 - 0.3 * tt)
        c.capsule((x0, y0), (x1, y1), r, r, m, z=z)


def _arrow(c, a, length, shaft, head, fletch, z=6, tip_mat=None):
    x0, y0 = 3.0, 0.0
    x1, y1 = x0 + math.cos(a) * length, math.sin(a) * length
    c.capsule((x0 - 2, y0 + 0.3), (x1, y1 + 0.3), 0.65, 0.6, shaft, z=z)
    hx, hy = x1 + math.cos(a) * 3.2, y1 + math.sin(a) * 3.2
    nx, ny = -math.sin(a), math.cos(a)
    c.poly([(x1 + nx * 1.2, y1 + ny * 1.2), (hx, hy), (x1 - nx * 1.2, y1 - ny * 1.2)], tip_mat or head, z=z + 1, bevel=0.5, height=0.5)
    c.capsule((x0 - 2, y0), (x0 - 4, y0 - 1.5), 0.6, 0.4, fletch, z=z)
    c.capsule((x0 - 2, y0), (x0 - 4, y0 + 1.5), 0.6, 0.4, fletch, z=z)


def draw_bow(c, iid, mm):
    """Her yay ayrı bir kimlik: siluet, renk ve süsleme farklı; malzeme rengi kuşak/uç süslerinde."""
    B, A, G = mm['b'], mm['a'], mm['g']
    string = M['bone']
    if iid == 'turk_yayi':
        # kırmızı laklı derin kompozit yay, kemik siyahlar, altın çiçek benekleri
        lac = Mat(ramp(356, 0.72, 0.55), spec=0.6, name='kırmızı lak')
        pts = _limb_pts(14.5, 9.0, 7.5)
        _limbs(c, pts, lac, 1.6, z=1, tip_mat=M['bone'], band=B)
        c.capsule((pts[0][0], pts[0][1]), (pts[-1][0], pts[-1][1]), 0.32, 0.32, string, z=0)
        for t in (-0.62, -0.3, 0.3, 0.62):
            p = pts[int((t + 1) * 16)]
            c.dot((p[0] - 0.5, p[1]), M['gold'], z=5)
        c.capsule((3.4, -2.4), (3.4, 2.4), 1.8, 1.8, M['leather'], z=3)
        c.capsule((3.4, -2.6), (3.4, -2.2), 1.9, 1.9, M['gold'], z=4)
        c.capsule((3.4, 2.2), (3.4, 2.6), 1.9, 1.9, M['gold'], z=4)
    elif iid == 'akinci_yayi':
        # kısa akıncı yayı: siyah lak, altın şeritler, tutamaktan sarkan kızıl at kılı püskül
        lac = Mat(ramp(250, 0.25, 0.2), spec=0.8, name='siyah lak')
        pts = _limb_pts(11.5, 7.0, 5.6)
        _limbs(c, pts, lac, 1.5, z=1, tip_mat=B)
        for i in range(3, len(pts) - 3, 4):
            c.dot((pts[i][0] - 0.4, pts[i][1]), M['gold'], z=5)
        c.capsule((pts[0][0], pts[0][1]), (pts[-1][0], pts[-1][1]), 0.32, 0.32, string, z=0)
        c.capsule((3.4, -2.0), (3.4, 2.0), 1.7, 1.7, M['red_paint'], z=3)
        tas = [(3.0, 2.2), (2.2, 5.0), (1.6, 8.0), (1.4, 10.5)]
        for a, b in zip(tas, tas[1:]):
            c.capsule(a, b, 0.9, 0.7, M['red_paint'], z=4)
        c.ellipse((1.4, 11.0), 1.3, 1.6, M['red_paint'], z=4)
    elif iid == 'saganak_yayi':
        # çift katlı mavi yay: iki kol katmanı, üç ok yelpaze halinde kurulu
        blue = Mat(ramp(212, 0.6, 0.58), spec=0.5, name='mavi lak')
        back = _limb_pts(15.0, 9.0, 6.4, grip_x=1.6)
        front = _limb_pts(14.0, 8.4, 6.2, grip_x=4.4)
        _limbs(c, back, B, 1.3, z=0)
        _limbs(c, front, blue, 1.5, z=1, tip_mat=M['bone'])
        c.capsule((front[0][0], front[0][1]), (front[-1][0], front[-1][1]), 0.32, 0.32, string, z=0)
        for a in (-0.22, 0.0, 0.22):
            _arrow(c, a, 14, M['wood'], M['iron'], M['nazar_w'], z=6)
        c.capsule((3.4, -2.4), (3.4, 2.4), 1.8, 1.8, M['leather'], z=8)
    elif iid == 'tufan_yayi':
        # büyük tufan yayı: turkuaz, kartal başlı uçlar, beş ok
        tq = Mat(ramp(178, 0.6, 0.6), spec=0.6, name='turkuaz lak')
        pts = _limb_pts(17.0, 10.5, 7.8)
        _limbs(c, pts, tq, 1.8, z=1, band=B)
        for end in (pts[0], pts[-1]):
            sgn = 1 if end[1] > 0 else -1
            c.ellipse((end[0] + 0.8, end[1]), 2.0, 1.7, M['gold'], z=3)
            c.poly([(end[0] + 2.2, end[1] - 0.6), (end[0] + 4.6, end[1] + sgn * 0.4), (end[0] + 2.2, end[1] + 0.9)], M['amber'], z=4, bevel=0.4, height=0.4)
            c.dot((end[0] + 1.2, end[1] - 0.6), M['black'], z=6)
        c.capsule((pts[0][0], pts[0][1]), (pts[-1][0], pts[-1][1]), 0.32, 0.32, string, z=0)
        for a in (-0.4, -0.2, 0.0, 0.2, 0.4):
            _arrow(c, a, 15, M['wood'], M['gold'], M['nazar_l'], z=6)
        c.capsule((3.4, -2.6), (3.4, 2.6), 2.0, 2.0, M['gold'], z=8)
    elif iid == 'od_oklari':
        # od yayı: koyu ahşap, alev biçimli uçlar (ışıldar), tutamakta kor taşı, kurulu ateş oku
        wood = Mat(ramp(18, 0.45, 0.32), name='kömür ahşap')
        pts = _limb_pts(13.5, 8.2, 6.0)
        _limbs(c, pts, wood, 1.5, z=1)
        for end in (pts[0], pts[-1]):
            sgn = 1 if end[1] > 0 else -1
            c.poly([(end[0] - 1.2, end[1] - sgn * 2.5), (end[0] + 1.6, end[1] - sgn * 2.0), (end[0] + 2.8, end[1] + sgn * 3.0)], M['amber'], z=3, bevel=0.8, height=0.8)
        c.capsule((pts[0][0], pts[0][1]), (pts[-1][0], pts[-1][1]), 0.32, 0.32, string, z=0)
        _arrow(c, 0.0, 15, M['wood'], M['amber'], M['red_paint'], z=6, tip_mat=M['amber'])
        c.ellipse((20.5, 0), 2.2, 1.6, M['amber'], z=8)
        c.capsule((3.4, -2.2), (3.4, 2.2), 1.7, 1.7, M['leather'], z=8)
        c.ellipse((3.4, 0), 1.4, 1.4, M['amber'], z=9)


def draw_item(c, iid, mm):
    B, A, G, W = mm['b'], mm['a'], mm['g'], mm['w']
    if iid in BOWS:
        draw_bow(c, iid, mm)
        return
    if iid == 'alp_kilici':
        c.capsule((-6, 0), (0, 0), 1.5, 1.5, G); c.ellipse((-7.2, 0), 1.9, 1.9, A, z=1)
        c.capsule((1, -4.5), (1, 4.5), 1.4, 1.4, A, z=2); c.ellipse((1, 0), 1.2, 1.2, mm['glow'], z=6)
        c.poly([(2, -1.9), (27, -1.5), (31, 0), (27, 1.5), (2, 1.9)], B, z=1, bevel=1.7, height=2,
               paint=[(lambda lu, lv, px, py: np.abs(py) < 0.5, M['fur_dark'])])
    elif iid == 'pala':
        c.capsule((-6, 0), (0, 0), 1.5, 1.5, G); c.ellipse((-7.2, 0.3), 1.9, 1.9, A, z=1)
        c.capsule((1, -3.8), (1, 3.8), 1.3, 1.3, A, z=2)
        pts = [(2, -1.8), (14, -2.2), (22, -3.4), (28, -6.2), (25, -2.0), (16, 1.4), (2, 1.8)]
        c.poly(pts, B, z=1, bevel=1.7, height=2)
    elif iid == 'yatagan':
        c.capsule((-5, 0), (0, 0), 1.4, 1.4, G)
        c.poly([(-7.5, -2.5), (-5, -0.5), (-5, 0.5), (-7.5, 2.5), (-6, 0)], M['bone'], z=1, bevel=1, height=1)
        pts = [(1, -1.5), (12, -0.6), (22, -1.8), (27, -3.2), (24, 0.2), (12, 1.6), (1, 1.5)]
        c.poly(pts, B, z=1, bevel=1.5, height=1.8)
    elif iid == 'gurz':
        c.capsule((-7, 0), (15, 0), 1.6, 1.6, W); c.ellipse((-8, 0), 2.0, 2.0, A, z=1)
        for k in range(6):
            a = k / 6 * math.tau
            c.poly([(18, 0), (18 + math.cos(a) * 6.5, math.sin(a) * 6.5 - 1.2), (18 + math.cos(a) * 6.5, math.sin(a) * 6.5 + 1.2)], B, z=2 + abs(math.sin(a)), bevel=1.4, height=2)
        c.ellipse((18, 0), 4.6, 4.6, B, z=3)
        c.ellipse((18, 0), 1.6, 1.6, A, z=9)
    elif iid == 'teber':
        c.capsule((-10, 0), (26, 0), 1.3, 1.3, W)
        c.capsule((22, -0.5), (22, 0.5), 1.8, 1.8, A, z=2)
        c.poly([(20, -1), (24, -11), (31, -12), (29, -4), (29, 4), (31, 10), (24, 9), (20, 1)], B, z=1, bevel=2, height=2)
        c.poly([(26, -1.5), (34, 0), (26, 1.5)], B, z=1, bevel=1, height=1)
        for k in range(3):
            c.capsule((20 - k * 1.2, 1.5), (18 - k * 1.5, 6 + k * 0.5), 0.7, 0.5, mm['red'], z=3)
    elif iid == 'kargi':
        c.capsule((-12, 0), (30, 0), 1.2, 1.2, W)
        for x in (-6, 4, 14):
            c.capsule((x, -1.4), (x, 1.4), 0.8, 0.8, A, z=2)
        c.poly([(30, -2.6), (38, -1.4), (44, 0), (38, 1.4), (30, 2.6), (32, 0)], B, z=2, bevel=1.5, height=2)
        for k in range(5):
            c.capsule((29, 0), (25 - k * 0.6, 2 + k * 1.6), 0.6, 0.5, mm['white'] if k % 2 else mm['red'], z=3)
    elif iid == 'ikiz_bicak':
        for (ox, oy), z0 in (((3, 4.5), -6), ((0, 0), 0)):
            c.capsule((-4 + ox, oy), (0 + ox, oy), 1.3, 1.3, G, z=z0)
            c.capsule((0.6 + ox, -2.6 + oy), (0.6 + ox, 2.6 + oy), 1.0, 1.0, A, z=z0 + 1)
            c.poly([(1 + ox, -1.4 + oy), (11 + ox, -1.7 + oy), (16 + ox, 0.4 + oy), (11 + ox, 1.0 + oy), (1 + ox, 1.2 + oy)], B, z=z0 + 1, bevel=1.2, height=1.5)
    elif iid in ('turk_yayi', 'akinci_yayi'):
        k = 1.0 if iid == 'turk_yayi' else 0.85
        pts = []
        for i in range(-8, 9):
            t = i / 8
            x = 3.5 - 5.5 * (t * t) + (2.4 * (abs(t) ** 6)) * 2.0
            pts.append((x * k + (1.5 if abs(t) > 0.85 else 0), 14 * t * k))
        _arc(c, pts, 1.3, B if iid == 'turk_yayi' else W, 1)
        c.capsule((pts[0][0], pts[0][1]), (pts[-1][0], pts[-1][1]), 0.35, 0.35, M['bone'], z=0)
        c.capsule((3.2, -2.2), (3.2, 2.2), 1.6, 1.6, G, z=3)
        for y in (-7, 7):
            c.ellipse((1.8 * k, y * k), 1.0, 1.0, A, z=4)
    elif iid == 'cirit':
        c.capsule((-10, 0), (26, 0), 1.0, 1.0, W)
        c.poly([(26, -2.0), (33, 0), (26, 2.0), (27.5, 0)], B, z=2, bevel=1.2, height=1.5)
        c.capsule((-10, 0), (-13, -2), 0.8, 0.6, mm['red'], z=2); c.capsule((-10, 0), (-13, 2), 0.8, 0.6, mm['turq'], z=2)
    elif iid == 'coban_sapani':
        c.capsule((-7, 0), (2, 0), 1.5, 1.5, W)
        c.capsule((2, 0), (8, -5.5), 1.2, 1.1, W, z=1); c.capsule((2, 0), (8, 5.5), 1.2, 1.1, W, z=1)
        c.capsule((8, -5.5), (5, 0), 0.4, 0.4, G, z=2); c.capsule((8, 5.5), (5, 0), 0.4, 0.4, G, z=2)
        c.ellipse((4.5, 0), 2.0, 2.0, G, z=3); c.ellipse((4.3, -0.4), 1.2, 1.2, M['rock'], z=6)
    elif iid in ('yuvarlak_kalkan', 'kartal_kalkani', 'ayna_kalkan'):
        rim_ = A if iid != 'ayna_kalkan' else B
        c.ellipse((0, 0), 11, 11, rim_, z=0)
        face = B if iid != 'ayna_kalkan' else Mat(ramp(200, 0.15, 0.98), spec=1.4)
        if iid == 'yuvarlak_kalkan':
            c.ellipse((0, 0), 9, 9, W, z=12, paint=[(lambda lu, lv, px, py: (np.floor(np.arctan2(py, px) * 8 / math.pi) % 2 == 0), mm['red'])])
        else:
            c.ellipse((0, 0), 9, 9, face, z=12)
        if iid == 'kartal_kalkani':
            c.poly([(-7, -1), (-1, -5), (0, -1), (1, -5), (7, -1), (2, 2), (0, 6), (-2, 2)], A, z=24, bevel=1, height=1)
        c.ellipse((0, 0), 2.6, 2.6, A, z=26)
        for k in range(8):
            a = k / 8 * math.tau
            c.ellipse((math.cos(a) * 10, math.sin(a) * 10), 0.8, 0.8, M['iron'], z=16)
    elif iid == 'kara_barut':
        c.ellipse((0, 2), 7, 6.5, M['leather'], z=0, paint=[(lambda lu, lv, px, py: np.abs(py + 1.5) < 0.6, mm['red'])])
        c.capsule((0, -4), (0, -7), 2.4, 1.6, M['leather'], z=1)
        c.capsule((0, -7), (3, -10), 0.6, 0.5, M['bone'], z=2); c.ellipse((3.2, -10.5), 1.4, 1.4, M['amber'], z=4)
    elif iid == 'bozkurt_cagrisi':
        c.ellipse((0, 0), 8, 8, mm['white'], z=0)
        c.poly([(-6, -4), (-4, -11), (-1, -5)], mm['white'], z=2, bevel=1, height=1); c.poly([(1, -5), (4, -11), (6, -4)], mm['white'], z=2, bevel=1, height=1)
        c.capsule((0, 1), (0, 6), 2.6, 1.6, M['fur_dark'], z=12)
        c.ellipse((0, 6.2), 1.1, 0.9, M['black'], z=16)
        c.dot((-3, -1), M['kut'], z=20, size=2); c.dot((2, -1), M['kut'], z=20, size=2)
    elif iid == 'nazar_boncugu':
        c.ellipse((0, 0), 8, 8, M['nazar_b'], z=0, flat=0.7); c.ellipse((0, 0), 5.6, 5.6, M['nazar_w'], z=4)
        c.ellipse((0, 0), 3.8, 3.8, M['nazar_l'], z=6); c.ellipse((0, 0), 1.8, 1.8, M['black'], z=8)
    elif iid == 'od_testisi':
        c.ellipse((0, 2), 6.5, 7, Mat(ramp(18, 0.6, 0.62)), z=0, paint=[(lambda lu, lv, px, py: np.abs(py - 2) < 0.8, M['turq'])])
        c.capsule((0, -4), (0, -8), 2.2, 2.6, Mat(ramp(18, 0.6, 0.62)), z=1)
        c.poly([(-2, -8), (2, -8), (1, -13), (-1, -11)], M['amber'], z=3, bevel=1, height=1)
    # ------------------------------------------------------------ yeni silahlar
    elif iid == 'yildirim_kilici':
        # Tengri'nin kılıcı: hafif kavisli tek ağızlı uzun kılıç (kılıç/katana), kabzada mavi şimşek taşı, püskül
        c.capsule((-8, 0), (0, 0), 1.4, 1.4, G); c.ellipse((-9.2, 0), 1.8, 1.8, A, z=1)
        c.capsule((1, -3.2), (1, 3.2), 1.2, 1.2, A, z=2); c.ellipse((1, 0), 1.3, 1.3, M['kut'], z=6)
        pts = [(2, -1.4), (14, -1.6), (26, -2.6), (36, -4.6), (34, -1.2), (24, 0.8), (12, 1.3), (2, 1.5)]
        c.poly(pts, B, z=1, bevel=1.5, height=1.8, paint=[(lambda lu, lv, px, py: np.abs(py + 0.6) < 0.4, M['nazar_w'])])
        for k in range(3):
            c.capsule((-9, 0), (-12 - k, 3 + k * 1.2), 0.5, 0.4, [mm['red'], mm['turq'], M['gold']][k], z=2)
    elif iid == 'ulu_kilic':
        # devasa iki el kılıcı: uzun kabza, geniş siper, kalın bıçak; ortada kut oyuğu
        c.capsule((-14, 0), (0, 0), 1.8, 1.8, G); c.ellipse((-15.5, 0), 2.4, 2.4, A, z=1)
        c.capsule((1, -6.5), (1, 6.5), 1.8, 1.8, A, z=2); c.ellipse((1, 0), 2.2, 2.2, mm['glow'], z=6)
        c.poly([(2, -3.6), (30, -3.9), (41, -2.6), (47, 0), (41, 2.6), (30, 3.9), (2, 3.6)], B, z=1, bevel=2.4, height=3,
               paint=[(lambda lu, lv, px, py: np.abs(py) < 0.7, mm['glow'])])
    elif iid == 'dag_cekici':
        # dağ çekici: uzun sap, dev taş-demir başlık, kemik dişler
        c.capsule((-14, 0), (18, 0), 1.9, 1.9, W); c.ellipse((-15, 0), 2.4, 2.4, A, z=1)
        c.poly([(16, -9), (34, -10), (36, -4), (36, 4), (34, 10), (16, 9)], B, z=2, bevel=2.6, height=3.5)
        c.poly([(34, -8), (41, -6), (41, 6), (34, 8)], M['stone'], z=3, bevel=1.5, height=2)
        for y in (-5, 0, 5):
            c.capsule((36, y), (43, y), 0.9, 0.5, M['bone'], z=4)
        c.capsule((22, -11), (22, 11), 1.1, 1.1, A, z=4)
    elif iid == 'ruh_kilici':
        # ruh kılıcı: kabza katı, bıçak yarı saydam kut ışığı; kenarda dalga çentikleri
        c.capsule((-6, 0), (0, 0), 1.5, 1.5, G); c.ellipse((-7.2, 0), 1.9, 1.9, A, z=1)
        c.capsule((1, -4.0), (1, 4.0), 1.3, 1.3, A, z=2)
        spirit = Mat(ramp(172, 0.6, 0.95, spread=0.25), emissive=0.8, outline='#0b4a52', name='ruh bıçak')
        c.poly([(2, -2.0), (12, -2.6), (20, -1.8), (28, -3.4), (34, 0), (28, 3.4), (20, 1.8), (12, 2.6), (2, 2.0)], spirit, z=1, bevel=1.6, height=1.5)
        for x in (9, 17, 25):
            c.dot((x, 0), M['nazar_w'], z=5)
    elif iid == 'ay_palasi':
        # ay palası: iki hilal bıçak, altın hilal tokalar
        moon = Mat(ramp(48, 0.35, 0.9), spec=0.9, name='ay gümüşü')
        for (ox, oy), z0 in (((3, 4.5), -6), ((0, 0), 0)):
            c.capsule((-4 + ox, oy), (0 + ox, oy), 1.3, 1.3, G, z=z0)
            pts = [(1 + ox, -1.4 + oy), (8 + ox, -4.5 + oy), (15 + ox, -5.5 + oy), (19 + ox, -3 + oy), (15 + ox, -2.5 + oy), (9 + ox, -0.8 + oy), (1 + ox, 1.2 + oy)]
            c.poly(pts, moon if z0 == 0 else B, z=z0 + 1, bevel=1.2, height=1.5)
            c.ellipse((0.6 + ox, oy), 1.4, 1.4, A, z=z0 + 2)
    elif iid == 'yilan_kilici':
        # yılan kılıcı (Şahmeran): dalgalı yeşim bıçak, yılan başı siper, zehir damlası
        venom = Mat(ramp(96, 0.8, 0.85, spread=0.4), spec=0.9, emissive=0.35, outline='#163a14', name='zehir yeşimi')
        c.capsule((-6, 0), (0, 0), 1.5, 1.5, G); c.ellipse((-7.4, 0), 2.0, 2.0, A, z=1)
        c.ellipse((1.5, 0), 2.8, 2.2, venom, z=2); c.dot((2.5, -0.8), M['eye_red'], z=8)
        pts = [(3, -1.6)] + [(4 + k * 3.2, -1.7 + 2.0 * math.sin(k * 1.1)) for k in range(9)] + [(34, 0)] + [(4 + k * 3.2, 1.7 + 2.0 * math.sin(k * 1.1)) for k in range(8, -1, -1)] + [(3, 1.6)]
        c.poly(pts, B, z=1, bevel=1.5, height=1.8, paint=[(lambda lu, lv, px, py: np.abs(py - 2.0 * np.sin((px - 4) / 3.2 * 1.1)) < 0.5, venom)])
        c.dot((30, 3), venom, z=7, size=2)
    elif iid == 'kor_cekici':
        # kor çekici (Tamu): kara taş başlık, içinden sızan kor çatlakları, kısa kalın sap
        ember = Mat(ramp(22, 0.95, 1.0, spread=0.3), emissive=1.0, outline='#5a1a04', name='kor')
        c.capsule((-12, 0), (16, 0), 1.9, 1.9, W); c.ellipse((-13, 0), 2.3, 2.3, A, z=1)
        c.poly([(14, -8), (30, -9), (33, -3), (33, 3), (30, 9), (14, 8)], M['rock'], z=2, bevel=2.4, height=3,
               paint=[(lambda lu, lv, px, py: (np.abs(py - 2.5 * np.sin(px * 0.9)) < 0.6) & (px > 16) & (px < 31), ember)])
        for x in (18, 24, 29):
            c.dot((x, -6 + (x % 3)), ember, z=6, size=2)
        c.poly([(30, -2), (37, 0), (30, 2)], ember, z=4, bevel=1, height=1)
    elif iid == 'ruzgar_kilici':
        # rüzgâr kılıcı (Kaf): ince, uzun, hafif kavisli; bıçakta hava oyukları, tüy püskül
        c.capsule((-7, 0), (0, 0), 1.3, 1.3, G); c.ellipse((-8.2, 0), 1.7, 1.7, A, z=1)
        c.capsule((1, -3.2), (1, 3.2), 1.1, 1.1, A, z=2)
        pts = [(2, -1.5), (14, -1.9), (26, -3.0), (36, -5.0), (33, -1.8), (24, 0.6), (12, 1.3), (2, 1.5)]
        c.poly(pts, B, z=1, bevel=1.3, height=1.6)
        for x in (10, 17, 24):
            c.capsule((x, -0.8), (x + 3.5, -1.4), 0.5, 0.4, M['nazar_w'], z=4)
        c.capsule((-8, 0), (-13, 4), 0.5, 0.4, M['bone'], z=2); c.poly([(-12, 3), (-16, 7), (-13, 8), (-10, 5)], M['fur'], z=2, bevel=0.6, height=0.5)
    elif iid == 'savas_baltasi':
        c.capsule((-10, 0), (16, 0), 1.3, 1.3, W); c.capsule((-10, 0), (-7, 0), 1.6, 1.6, G, z=1)
        c.poly([(14, -2), (16, -12), (26, -13), (24, -3), (24, 3), (26, 13), (16, 12), (14, 2)], B, z=2, bevel=2, height=2)
        c.capsule((15, -1), (15, 1), 1.8, 1.8, A, z=3)
    elif iid == 'kement':
        c.capsule((-6, 0), (4, 0), 1.3, 1.3, W); c.ellipse((-7, 0), 1.6, 1.6, A, z=1)
        pts = [(4, 0), (10, -3), (17, -2), (23, -5), (29, -3), (34, -6)]
        _arc(c, pts, 0.9, G, 1)
        c.ellipse((36, -8), 3.2, 3.2, G, z=1); c.ellipse((36, -8), 1.8, 1.8, Mat(ramp(30, 0.1, 0.0)), z=2)
    elif iid == 'od_kamcisi':
        c.capsule((-6, 0), (4, 0), 1.3, 1.3, W); c.ellipse((-7, 0), 1.6, 1.6, A, z=1)
        pts = [(4, 0), (11, -4), (18, -1), (25, -5), (32, -2), (38, -6)]
        _arc(c, pts, 0.9, G, 1)
        for k, (x, y) in enumerate(pts[1:]):
            c.ellipse((x, y - 1.5), 1.4 + k * 0.2, 1.8 + k * 0.2, M['amber'], z=3)
    elif iid == 'civili_topuz':
        c.capsule((-7, 0), (14, 0), 1.6, 1.6, W); c.ellipse((-8, 0), 2.0, 2.0, A, z=1)
        c.ellipse((18, 0), 5.0, 5.0, B, z=3)
        for k in range(8):
            a = k / 8 * math.tau
            c.poly([(18 + math.cos(a) * 4, math.sin(a) * 4 - 1), (18 + math.cos(a) * 4, math.sin(a) * 4 + 1), (18 + math.cos(a) * 9, math.sin(a) * 9)], M['iron'], z=4 + abs(math.sin(a)), bevel=0.8, height=1)
    elif iid == 'erlik_tirpani':
        c.capsule((-12, 2), (18, -2), 1.3, 1.3, W)
        c.capsule((17, -2), (17, -7), 1.5, 1.5, A, z=2)
        pts = [(17, -8), (26, -11), (35, -9), (40, -3), (36, -7), (28, -8), (19, -6)]
        c.poly(pts, B, z=2, bevel=1.6, height=1.8)
        c.ellipse((16, -3), 1.6, 1.6, M['corrupt'], z=5)
        for k in range(3):
            c.capsule((-8 + k * 3, 1.5 - k * 0.4), (-9 + k * 3, 6), 0.6, 0.5, M['red_paint'] if k % 2 else M['bone'], z=3)
    elif iid == 'kurt_pencesi':
        for (ox, oy), z0 in (((2, 4), -6), ((0, 0), 0)):
            c.capsule((-5 + ox, oy), (1 + ox, oy), 1.6, 1.6, M['leather'], z=z0)
            for k in range(3):
                c.poly([(1 + ox, -2.6 + k * 2.4 + oy), (3 + ox, -2.2 + k * 2.4 + oy), (14 + ox, -5 + k * 3 + oy), (12 + ox, -3.6 + k * 3 + oy)], B, z=z0 + 1 + k * 0.1, bevel=1, height=1.2)
    elif iid == 'ayaz_kilici':
        c.capsule((-6, 0), (0, 0), 1.5, 1.5, G); c.ellipse((-7.2, 0), 1.9, 1.9, A, z=1)
        c.capsule((1, -4.5), (1, 4.5), 1.4, 1.4, A, z=2)
        ice = Mat(ramp(196, 0.45, 0.98, spread=0.4), spec=1.2, emissive=0.25, outline='#1a3a5a')
        c.poly([(2, -2.2), (12, -2.6), (20, -2.0), (30, -0.8), (33, 0), (30, 0.8), (20, 2.0), (12, 2.6), (2, 2.2)], ice, z=1, bevel=1.8, height=2)
        for x in (10, 18, 26):
            c.poly([(x, -2.4), (x + 2, -2.4), (x + 1, -5.5)], ice, z=2, bevel=0.6, height=0.6)
    elif iid in ('saganak_yayi', 'tufan_yayi'):
        k = 1.1 if iid == 'saganak_yayi' else 1.25
        pts = []
        for i in range(-8, 9):
            t = i / 8
            x = 3.5 - 6.0 * (t * t) + (2.4 * (abs(t) ** 6)) * 2.0
            pts.append((x * k + (1.5 if abs(t) > 0.85 else 0), 15 * t * k))
        _arc(c, pts, 1.4, B, 1)
        c.capsule((pts[0][0], pts[0][1]), (pts[-1][0], pts[-1][1]), 0.35, 0.35, M['bone'], z=0)
        c.capsule((3.5, -2.4), (3.5, 2.4), 1.7, 1.7, G, z=3)
        n = 3 if iid == 'saganak_yayi' else 5
        for i in range(n):
            a = (i - (n - 1) / 2) * 0.22
            c.capsule((3, 0), (3 + math.cos(a) * 12, math.sin(a) * 12), 0.5, 0.4, W, z=4)
            c.poly([(3 + math.cos(a) * 12, math.sin(a) * 12 - 1), (3 + math.cos(a) * 15, math.sin(a) * 15), (3 + math.cos(a) * 12, math.sin(a) * 12 + 1)], M['iron'], z=5, bevel=0.5, height=0.5)
    elif iid == 'od_oklari':
        k = 0.9
        pts = []
        for i in range(-8, 9):
            t = i / 8
            x = 3.5 - 5.5 * (t * t) + (2.4 * (abs(t) ** 6)) * 2.0
            pts.append((x * k + (1.5 if abs(t) > 0.85 else 0), 14 * t * k))
        _arc(c, pts, 1.3, W, 1)
        c.capsule((pts[0][0], pts[0][1]), (pts[-1][0], pts[-1][1]), 0.35, 0.35, M['bone'], z=0)
        c.capsule((3.2, -2.2), (3.2, 2.2), 1.6, 1.6, G, z=3)
        c.capsule((2, 0), (16, 0), 0.5, 0.4, W, z=4)
        c.ellipse((17.5, 0), 2.6, 1.8, M['amber'], z=5); c.ellipse((19, 0), 1.2, 0.9, M['flower_y'], z=6)
    elif iid == 'kam_kopuzu':
        c.ellipse((4, 0), 7.5, 5.5, W, z=0); c.ellipse((4, 0), 3.0, 2.4, Mat(ramp(30, 0.5, 0.2)), z=2)
        c.capsule((10, -1), (26, -4), 1.2, 1.0, W, z=1)
        for y in (-1.2, 0.0, 1.2):
            c.capsule((-2, y), (25, y - 3), 0.25, 0.25, M['bone'], z=3)
        for x in (22, 25):
            c.ellipse((x, -6), 1.0, 1.0, A, z=4)
        for k in range(3):
            c.capsule((-3, 0), (-6 - k, 3 + k), 0.5, 0.4, [mm['red'], mm['turq'], M['gold']][k], z=2)
    elif iid == 'gok_asasi':
        c.capsule((-12, 2), (20, -2), 1.3, 1.3, W)
        for k in range(3):
            a = -1.2 + k * 1.2
            c.capsule((20, -2), (20 + math.cos(a) * 6, -2 + math.sin(a) * 6 - 4), 1.0, 0.6, M['bark'], z=1)
        c.ellipse((23, -6), 3.4, 3.4, M['kut'], z=4)
        c.poly([(23, -12), (21, -6), (24, -7), (22, -1)], M['nazar_w'], z=6, bevel=0.5, height=0.5)
    elif iid == 'yel_borusu':
        c.capsule((-6, 0), (18, 0), 1.6, 2.6, W)
        c.ellipse((20, 0), 3.2, 4.2, W, z=1); c.ellipse((20.5, 0), 1.8, 2.6, Mat(ramp(30, 0.5, 0.2)), z=2)
        for x in (0, 5, 10):
            c.ellipse((x, -1.5), 0.8, 0.8, Mat(ramp(30, 0.5, 0.2)), z=3)
        for k in range(3):
            c.capsule((-6, 0), (-9 - k, 2 + k * 1.5), 0.5, 0.4, [mm['red'], mm['turq'], M['gold']][k], z=2)
    elif iid == 'kartal_tuyleri':
        for k in range(3):
            y = -5 + k * 5
            c.capsule((-6, y), (16, y - 2), 0.5, 0.4, M['bone'], z=k)
            c.poly([(-4, y - 2), (14, y - 4.5), (18, y - 2), (14, y + 0.5), (-4, y + 2)], M['fur_dark'] if k % 2 else M['fur'], z=k + 0.5, bevel=1, height=0.8)
    elif iid == 'mancinik_tasi':
        c.ellipse((6, 0), 9, 8, M['rock'], z=0, paint=[(lambda lu, lv, px, py: (np.sin(px * 1.7 + py) > 0.7), Mat(ramp(205, 0.1, 0.35)))])
        c.capsule((-3, -5), (14, -6), 0.7, 0.7, G, z=2); c.capsule((-3, 5), (14, 6), 0.7, 0.7, G, z=2)
    elif iid in ('dikenli_kalkan', 'kut_kalkani', 'ejder_kalkani', 'ulu_kayin_kalkani', 'tas_kalkan'):
        rim_ = A
        base_ = {'dikenli_kalkan': M['iron'], 'kut_kalkani': M['nazar_b'], 'ejder_kalkani': Mat(ramp(4, 0.8, 0.6)), 'ulu_kayin_kalkani': M['bark'], 'tas_kalkan': M['stone']}[iid]
        c.ellipse((0, 0), 11, 11, rim_ if iid != 'tas_kalkan' else Mat(ramp(216, 0.15, 0.40)), z=0)
        c.ellipse((0, 0), 9, 9, base_, z=12)
        if iid == 'dikenli_kalkan':
            for k in range(8):
                a = k / 8 * math.tau
                c.poly([(math.cos(a) * 9 - 1, math.sin(a) * 9), (math.cos(a) * 9 + 1, math.sin(a) * 9), (math.cos(a) * 14, math.sin(a) * 14)], M['iron'], z=20, bevel=0.6, height=0.8)
        elif iid == 'kut_kalkani':
            c.ellipse((0, 0), 4.2, 4.2, M['kut'], z=24)
            for k in range(6):
                a = k / 6 * math.tau
                c.capsule((math.cos(a) * 5, math.sin(a) * 5), (math.cos(a) * 8, math.sin(a) * 8), 0.6, 0.6, M['kut'], z=23)
        elif iid == 'ejder_kalkani':
            c.poly([(-6, 3), (-2, -5), (1, -1), (4, -6), (7, 2), (2, 5)], M['amber'], z=22, bevel=1, height=1)
            c.dot((-1, 0), M['black'], z=30); c.dot((3, -1), M['black'], z=30)
        elif iid == 'ulu_kayin_kalkani':
            for k in range(5):
                a = -1.4 + k * 0.7
                c.capsule((0, 4), (math.sin(a) * 7, 4 - math.cos(a) * 9), 0.9, 0.5, M['moss'], z=22)
            c.ellipse((0, 4), 2.0, 2.0, M['bark'], z=23)
        else:
            c.poly([(-5, -5), (5, -5), (6, 4), (-6, 4)], Mat(ramp(216, 0.15, 0.40)), z=20, bevel=1.2, height=1.2)
            c.dot((-2, -2), M['eye_red'], z=30); c.dot((2, -2), M['eye_red'], z=30)
        c.ellipse((0, 0), 2.4, 2.4, A, z=26) if iid in ('dikenli_kalkan', 'tas_kalkan') else None
    elif iid == 'sifa_muskasi':
        c.poly([(-7, -8), (7, -8), (7, 6), (0, 10), (-7, 6)], M['leather'], z=0, bevel=1.5, height=1.5)
        c.capsule((-3, -10), (3, -10), 0.6, 0.6, M['gold'], z=2)
        c.ellipse((0, -1), 3.0, 3.0, M['kut'], z=4); c.capsule((0, -4), (0, 2), 0.7, 0.7, M['nazar_w'], z=6); c.capsule((-3, -1), (3, -1), 0.7, 0.7, M['nazar_w'], z=6)
    elif iid == 'ayaz_tilsimi':
        ice = Mat(ramp(196, 0.45, 0.98, spread=0.4), spec=1.2, emissive=0.4, outline='#1a3a5a')
        c.poly([(0, -11), (5, -3), (9, 0), (5, 3), (0, 11), (-5, 3), (-9, 0), (-5, -3)], ice, z=0, bevel=2, height=2)
        c.ellipse((0, 0), 2.2, 2.2, M['nazar_w'], z=6)
    elif iid == 'yel_tilsimi':
        c.ellipse((0, 0), 8, 8, M['turq'], z=0)
        for k in range(3):
            a0 = k * math.tau / 3
            pts = [(math.cos(a0 + t * 0.9) * (2 + t * 5), math.sin(a0 + t * 0.9) * (2 + t * 5)) for t in range(4)]
            _arc(c, pts, 0.9, M['nazar_w'], 4)
    elif iid == 'davul_totemi':
        c.capsule((0, 4), (0, 11), 1.4, 1.4, W, z=0)
        c.ellipse((0, -2), 8.5, 5.5, M['leather'], z=2)
        c.ellipse((0, -2), 8.5, 5.5, M['leather'], z=2, paint=[(lambda lu, lv, px, py: np.abs(np.hypot(px, (py + 2) * 1.5) - 6.5) < 0.8, M['red_paint'])])
        for k in range(3):
            c.capsule((-4 + k * 4, -7), (-4 + k * 4 + 1, -12), 0.6, 0.4, [mm['red'], M['nazar_w'], mm['turq']][k], z=4)
    elif iid == 'ok_yagmuru':
        c.ellipse((0, 2), 7, 6, M['leather'], z=0)
        for k in range(5):
            x = -6 + k * 3
            c.capsule((x, -2), (x + 1.5, -12 + (k % 2) * 2), 0.45, 0.4, W, z=2)
            c.poly([(x + 1.5, -12 + (k % 2) * 2), (x + 0.3, -10 + (k % 2) * 2), (x + 2.8, -10.5 + (k % 2) * 2)], M['iron'], z=3, bevel=0.4, height=0.4)
    elif iid == 'kartal_cagrisi':
        c.ellipse((0, 0), 8, 8, M['nazar_b'], z=0)
        c.poly([(-9, 0), (-3, -5), (0, -1), (3, -5), (9, 0), (4, 2), (0, 7), (-4, 2)], M['gold'], z=4, bevel=1, height=1)
        c.dot((0, -2), M['black'], z=10)
    elif iid == 'ruh_kusu':
        c.ellipse((0, 1), 6, 5, M['kut'], z=0)
        c.poly([(-10, -2), (-3, -4), (-2, 1), (-8, 3)], M['kut'], z=1, bevel=1, height=1); c.poly([(10, -2), (3, -4), (2, 1), (8, 3)], M['kut'], z=1, bevel=1, height=1)
        c.ellipse((4, -3), 2.6, 2.6, M['nazar_w'], z=3); c.dot((5, -3.5), M['black'], z=6)
        c.poly([(6, -3), (9, -2.2), (6, -1.4)], M['amber'], z=5, bevel=0.3, height=0.3)
    elif iid == 'umay_tuyu':
        c.capsule((-6, 8), (6, -8), 0.6, 0.5, M['gold'], z=2)
        c.poly([(-6, 6), (-2, -4), (4, -10), (7, -6), (3, 2), (-3, 8)], M['nazar_w'], z=1, bevel=1.5, height=1.2, paint=[(lambda lu, lv, px, py: np.abs(px - py * -0.75) < 0.5, M['gold'])])
        c.ellipse((5, -9), 1.6, 1.6, M['kut'], z=4)
    elif iid == 'erlik_zinciri':
        for k in range(5):
            a = k * 0.5 - 1.0
            c.ellipse((-8 + k * 4, math.sin(a) * 3), 2.4, 1.6, M['iron'] if k % 2 else Mat(ramp(222, 0.16, 0.45)), z=k % 2, rot=a)
        c.ellipse((10, 0), 2.0, 2.0, M['corrupt'], z=4)


ORDER = ['alp_kilici', 'pala', 'yatagan', 'gurz', 'teber', 'kargi', 'ikiz_bicak', 'turk_yayi', 'akinci_yayi', 'cirit', 'coban_sapani',
         'yuvarlak_kalkan', 'kartal_kalkani', 'ayna_kalkan', 'kara_barut', 'bozkurt_cagrisi', 'nazar_boncugu', 'od_testisi',
         'yildirim_kilici', 'savas_baltasi', 'kement', 'od_kamcisi', 'civili_topuz', 'erlik_tirpani', 'kurt_pencesi', 'ayaz_kilici',
         'saganak_yayi', 'tufan_yayi', 'od_oklari', 'kam_kopuzu', 'gok_asasi', 'yel_borusu', 'kartal_tuyleri', 'mancinik_tasi',
         'dikenli_kalkan', 'kut_kalkani', 'ejder_kalkani', 'ulu_kayin_kalkani', 'tas_kalkan',
         'sifa_muskasi', 'ayaz_tilsimi', 'yel_tilsimi', 'davul_totemi', 'ok_yagmuru', 'kartal_cagrisi', 'ruh_kusu', 'umay_tuyu', 'erlik_zinciri',
         'ulu_kilic', 'dag_cekici', 'ruh_kilici', 'ay_palasi', 'yilan_kilici', 'kor_cekici', 'ruzgar_kilici']
CELL = (64, 40)
PIVOT = (16, 20)


def centered(iid):
    return iid in ('yuvarlak_kalkan', 'kartal_kalkani', 'ayna_kalkan', 'kara_barut', 'bozkurt_cagrisi', 'nazar_boncugu', 'od_testisi',
                   'dikenli_kalkan', 'kut_kalkani', 'ejder_kalkani', 'ulu_kayin_kalkani', 'tas_kalkan', 'mancinik_tasi', 'kartal_tuyleri',
                   'sifa_muskasi', 'ayaz_tilsimi', 'yel_tilsimi', 'davul_totemi', 'ok_yagmuru', 'kartal_cagrisi', 'ruh_kusu', 'umay_tuyu', 'erlik_zinciri')


def render_item(iid, mid):
    pv = (32, 20) if centered(iid) else PIVOT
    c = Canvas(CELL[0], CELL[1], pv[0], pv[1])
    draw_item(c, iid, mats_for(mid))
    rgba = c.shade(light=(-0.4, -0.75, 0.55), rim_amt=0.3)
    return c, rgba, c.normal_map(rgba[..., 3]), pv


def build_atlas():
    mids = [m['id'] for m in ITEMS['materials']]
    H, Wd = len(ORDER) * CELL[1], len(mids) * CELL[0]
    alb = np.zeros((H, Wd, 4)); nrm = np.zeros_like(alb); glo = np.zeros_like(alb)
    meta = {'cell': list(CELL), 'materials': mids, 'items': {}}
    for r, iid in enumerate(ORDER):
        for k, mid in enumerate(mids):
            c, rgba, nm, pv = render_item(iid, mid)
            ys, xs = slice(r * CELL[1], (r + 1) * CELL[1]), slice(k * CELL[0], (k + 1) * CELL[0])
            alb[ys, xs] = rgba; nrm[ys, xs] = nm
            em = c.emis
            glo[ys, xs, :3] = np.clip(em, 0, 1); glo[ys, xs, 3] = (em.max(axis=2) > 0)
        meta['items'][iid] = {'row': r, 'pivot': list((32, 20) if centered(iid) else PIVOT)}
    return alb, nrm, glo, meta
