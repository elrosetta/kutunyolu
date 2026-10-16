"""Kararan Ötüken v2 "mürekkep" süsleri: dilek ağacı (çaputlu huş), kam direği (kartal başlı oyma direk),
kayalar, mantarlar, çiçekler, çıra (alevi ayrı ışıma dokusu), balbal ve gözetleme kulesi parçaları.

Doku yoğunluğu 2 doku pikseli / dünya birimi (1080p'de 1:1); oyunda Sprite2D ölçeği 0.5. decor_v2.json: boyut ve
köken (doku pikseli). Level._decor --stil=v2 mürekkep ortamında "<ad>_v2" dokusunu kullanır.
"""
import json
import math
import os

import numpy as np

import inkkit_ortam as ik
from inkkit_ortam import INK, Sk, Layer, blade, bezier, blob, c01, leaf_shape, poly_path, premul, ribbon, smooth_path, fbm, mix, smoothstep, trunk
from otuken_ink import rock, foliage, balbal

BARK_B = (150, 156, 142)
BARK_L = (186, 192, 176)
CLOTH = [(168, 52, 46), (220, 214, 196), (70, 98, 160), (200, 160, 70), (90, 140, 96)]
WOOD = (104, 82, 64)
WOOD_D = (64, 48, 42)
WOOD_L = (150, 128, 100)


def _canvas(w, h):
    return Layer(w, h)


def dilek_agaci(seed=11):
    """Dilek ağacı: yaşlı, hafif eğik huş; alçak dallara bağlanmış renkli çaputlar, tepede yaprak öbekleri."""
    W, Hh = 260, 330
    L = _canvas(W, Hh)
    base_y = Hh - 6
    rng = np.random.default_rng(seed)
    # dallar ve yapraklar (gövdenin arkasında)
    sk = Sk(W, Hh)
    tips = []
    for k, (y0, side, ln) in enumerate([(120, -1, 95), (96, 1, 100), (70, -1, 80), (52, 1, 70), (160, 1, 80), (180, -1, 70)]):
        x0 = 130 + side * 6
        ang = math.radians(rng.uniform(30, 55))
        p2 = (x0 + side * math.sin(ang) * ln, y0 - math.cos(ang) * ln * 0.6)
        p1 = ((x0 + p2[0]) / 2, (y0 + p2[1]) / 2 - 8)
        pts = bezier((x0, y0), p1, p2, 12)
        sk.path(ribbon(pts, np.linspace(9, 2, 12)), BARK_B)
        sk.path(ribbon(pts, np.linspace(9, 2, 12)), INK, 1.0, 0, 1.6)
        tips.append(pts)
    for pts in tips[:4]:
        q = pts[-1]
        foliage(sk, q[0], q[1] - 6, 30, int(rng.integers(1 << 30)), (58, 84, 56), (126, 160, 112), n=55, ink_a=0.5)
        q = pts[7]
        foliage(sk, q[0], q[1] - 4, 20, int(rng.integers(1 << 30)), (52, 74, 50), (118, 150, 104), n=26, ink_a=0.5)
    foliage(sk, 130, 30, 46, seed + 3, (56, 80, 54), (128, 164, 114), n=90, ink_a=0.5)
    back = sk.snap()
    L.a = back
    arr, xl, yt = trunk(Hh, W, base_y, 130, 30, seed, kind='birch', lean=0.04, bend=0.25, top_y=10,
                        bark=BARK_B, light=BARK_L, rim=(200, 230, 210), ink_w=2.6, taper=0.45)
    L.over(arr, xl, yt)
    # çaputlar: alçak dallardan sarkan şeritler (bağ düğümü + rüzgârda kıvrılan uç)
    sk2 = Sk(W, Hh)
    for pts in tips:
        for t in (0.35, 0.55, 0.75, 0.92):
            if rng.random() < 0.25:
                continue
            q = pts[int(t * 11)]
            col = CLOTH[int(rng.integers(len(CLOTH)))]
            ln = rng.uniform(26, 52)
            sw = rng.uniform(-8, 10)
            cp = [(q[0], q[1]), (q[0] + sw * 0.4, q[1] + ln * 0.5), (q[0] + sw, q[1] + ln)]
            cpts = bezier(*cp, n=10)
            wd = np.linspace(rng.uniform(5, 8), rng.uniform(3, 5), 10)
            sk2.path(ribbon(cpts, wd), col)
            sk2.path(ribbon(cpts[:4], wd[:4] * 0.6), tuple(np.array(col) * 0.7), 0.8)
            sk2.path(ribbon(cpts, wd), INK, 1.0, 0, 1.3)
            sk2.c.drawCircle(q[0], q[1] + 1, 3.0, sk2.paint(tuple(np.array(col) * 0.8)))
    L.over(sk2.snap())
    # dibinde küçük adak taşı ve ot
    sk3 = Sk(W, Hh)
    for _ in range(60):
        x = rng.uniform(70, 190)
        sk3.path(blade(x, base_y + 4, rng.uniform(8, 26), rng.uniform(-0.5, 0.5), rng.uniform(1.6, 3)),
                 (52, 84, 58) if rng.random() < 0.6 else (110, 150, 104))
    L.over(sk3.snap())
    return L, (W, Hh), (130, base_y)


def kam_diregi(seed=21):
    """Kam direği: oyma halkalı ahşap direk, tepede kanat açmış kartal, sarkan şeritler ve çıngıraklar."""
    W, Hh = 120, 240
    L = _canvas(W, Hh)
    base_y = Hh - 4
    cx = 60
    sk = Sk(W, Hh)
    post = poly_path([(cx - 8, base_y), (cx + 8, base_y), (cx + 6.5, 54), (cx - 6.5, 54)])
    sk.path(post, WOOD)
    sk.path(poly_path([(cx - 8, base_y), (cx - 2, base_y), (cx - 2, 54), (cx - 6.5, 54)]), WOOD_L, 0.7)
    sk.path(poly_path([(cx + 3, base_y), (cx + 8, base_y), (cx + 6.5, 54), (cx + 3, 54)]), WOOD_D, 0.8)
    for y in (90, 120, 150, 180):
        r = poly_path([(cx - 9, y), (cx + 9, y), (cx + 9, y + 6), (cx - 9, y + 6)])
        sk.path(r, WOOD_D)
        sk.path(r, INK, 1.0, 0, 1.4)
        sk.path(ribbon([(cx - 5, y + 14), (cx, y + 18), (cx + 5, y + 14)], [0.5, 1.6, 0.5]), INK, 0.8)
    sk.path(post, INK, 1.0, 0, 2.2)
    # kartal: gövde + açık kanatlar
    body = smooth_path([(cx, 26), (cx + 8, 34), (cx + 6, 52), (cx, 58), (cx - 6, 52), (cx - 8, 34)], True, 0.4)
    for side in (-1, 1):
        wing = smooth_path([(cx + side * 4, 36), (cx + side * 26, 22), (cx + side * 46, 12), (cx + side * 42, 22),
                            (cx + side * 48, 26), (cx + side * 38, 32), (cx + side * 42, 38), (cx + side * 22, 42)], True, 0.35)
        sk.path(wing, WOOD)
        sk.path(wing, INK, 1.0, 0, 1.8)
        for k in range(3):
            sk.path(ribbon([(cx + side * (14 + k * 9), 30 - k * 3), (cx + side * (20 + k * 9), 36 - k * 2)], [1.2, 0.3]), INK, 0.8)
    sk.path(body, WOOD_D)
    sk.path(body, INK, 1.0, 0, 1.8)
    head = smooth_path([(cx - 4, 28), (cx, 18), (cx + 7, 20), (cx + 11, 24), (cx + 4, 28)], True, 0.4)
    sk.path(head, WOOD_L)
    sk.path(head, INK, 1.0, 0, 1.6)
    sk.c.drawCircle(cx + 3, 22.5, 1.3, sk.paint(INK))
    # şeritler
    rng = np.random.default_rng(seed)
    for k in range(6):
        y0 = 62 + k * 4
        side = -1 if k % 2 == 0 else 1
        col = CLOTH[k % len(CLOTH)]
        q = bezier((cx + side * 7, y0), (cx + side * 14, y0 + 30), (cx + side * rng.uniform(10, 22), y0 + rng.uniform(50, 80)), 10)
        sk.path(ribbon(q, np.linspace(4.5, 3, 10)), col)
        sk.path(ribbon(q, np.linspace(4.5, 3, 10)), INK, 0.9, 0, 1.0)
    L.a = sk.snap()
    return L, (W, Hh), (cx, base_y)


def kaya(seed, rx, ry):
    arr = rock(seed, rx, ry, base=(100, 104, 96), moss=(86, 124, 80), ink_w=3.0)
    h, w = arr.shape[:2]
    L = _canvas(w / ik.K, h / ik.K)
    L.a = arr
    return L, (w, h), (w / ik.K / 2, h / ik.K - 8)


def mantar(seed, n):
    """Mantar öbeği: kalın saplı, soluk kırmızımsı şapkalar, alt yüzde açık lameller."""
    W, Hh = 90, 70
    rng = np.random.default_rng(seed)
    sk = Sk(W, Hh)
    base_y = Hh - 4
    for k in range(n):
        x = 45 + (k - (n - 1) / 2) * rng.uniform(14, 20) + rng.uniform(-3, 3)
        h = rng.uniform(16, 40) * (1.0 if k == n // 2 else 0.75)
        r = h * rng.uniform(0.45, 0.65)
        lean = rng.uniform(-0.15, 0.15)
        stem = ribbon([(x, base_y), (x + lean * h * 0.5, base_y - h * 0.5), (x + lean * h, base_y - h)], [r * 0.42, r * 0.36, r * 0.3])
        sk.path(stem, (196, 190, 168))
        sk.path(stem, INK, 1.0, 0, 1.4)
        tx = x + lean * h
        ty = base_y - h
        cap = smooth_path([(tx - r, ty + 2), (tx - r * 0.8, ty - r * 0.45), (tx, ty - r * 0.7), (tx + r * 0.8, ty - r * 0.45), (tx + r, ty + 2), (tx, ty + r * 0.18)], True, 0.4)
        col = (150, 70, 56) if rng.random() < 0.6 else (176, 128, 84)
        sk.path(cap, col)
        sk.path(smooth_path([(tx - r * 0.7, ty - r * 0.3), (tx - r * 0.2, ty - r * 0.62), (tx + r * 0.1, ty - r * 0.5), (tx - r * 0.4, ty - r * 0.2)], True, 0.4), tuple(min(255, c * 1.35) for c in col), 0.8)
        for _ in range(3):
            sx, sy = tx + rng.uniform(-r * 0.6, r * 0.6), ty - rng.uniform(r * 0.1, r * 0.5)
            sk.c.drawCircle(sx, sy, rng.uniform(1.2, 2.4), sk.paint((226, 214, 190)))
        sk.path(cap, INK, 1.0, 0, 1.8)
    for _ in range(18):
        x = rng.uniform(10, W - 10)
        sk.path(blade(x, base_y + 4, rng.uniform(6, 16), rng.uniform(-0.5, 0.5), 2.0), (52, 84, 58))
    L = _canvas(W, Hh)
    L.a = sk.snap()
    return L, (W, Hh), (45, base_y)


def cicek(seed, kind):
    """Küçük bitki: 0 mavi çan çiçekleri, 1 ak papatya öbeği, 2 eğrelti filizi."""
    W, Hh = 90, 60
    rng = np.random.default_rng(seed)
    sk = Sk(W, Hh)
    base_y = Hh - 3
    for _ in range(14):
        x = rng.uniform(14, W - 14)
        sk.path(blade(x, base_y + 3, rng.uniform(8, 22), rng.uniform(-0.5, 0.5), 2.2), (50, 82, 56) if rng.random() < 0.5 else (98, 136, 92))
    if kind == 2:
        x0 = 45
        for k in range(5):
            ang = math.radians(-90 + (k - 2) * 26 + rng.uniform(-8, 8))
            ln = rng.uniform(30, 44)
            p2 = (x0 + math.cos(ang) * ln, base_y + math.sin(ang) * ln)
            pts = bezier((x0, base_y), ((x0 + p2[0]) / 2, (base_y + p2[1]) / 2 - 6), p2, 12)
            sk.path(ribbon(pts, np.linspace(2.6, 0.8, 12)), (60, 96, 62))
            for j in range(2, 12):
                q = pts[j]
                for sgn in (-1, 1):
                    sk.path(leaf_shape(q[0], q[1], 7 * (1 - j / 14), 3, ang + sgn * 1.0), (84, 124, 80) if sgn < 0 else (60, 94, 60))
    else:
        for k in range(rng.integers(3, 6)):
            x = rng.uniform(22, W - 22)
            h = rng.uniform(18, 36)
            stem = bezier((x, base_y), (x + rng.uniform(-4, 4), base_y - h * 0.6), (x + rng.uniform(-6, 6), base_y - h), 8)
            sk.path(ribbon(stem, np.linspace(1.8, 1.0, 8)), (58, 92, 60))
            fx, fy = stem[-1]
            if kind == 0:
                bell = smooth_path([(fx - 4, fy), (fx - 3, fy - 6), (fx + 3, fy - 6), (fx + 4, fy), (fx + 2, fy + 2), (fx, fy), (fx - 2, fy + 2)], True, 0.4)
                sk.path(bell, (96, 120, 196))
                sk.path(bell, INK, 0.9, 0, 1.0)
            else:
                for j in range(8):
                    a = j * math.pi / 4
                    sk.path(leaf_shape(fx, fy, 6, 2.6, a), (232, 230, 216))
                sk.c.drawCircle(fx, fy, 2.2, sk.paint((222, 186, 80)))
                sk.c.drawCircle(fx, fy, 6.2, sk.paint(INK, 0.6, 0, 0.8))
    L = _canvas(W, Hh)
    L.a = sk.snap()
    return L, (W, Hh), (45, base_y)


def cira(seed=31):
    """Çıra: ahşap direk, demir kova, içinde reçineli odun; alev ayrı ışıma dokusunda (toplamalı)."""
    W, Hh = 56, 140
    sk = Sk(W, Hh)
    base_y = Hh - 3
    cx = 28
    post = poly_path([(cx - 4, base_y), (cx + 4, base_y), (cx + 3, 40), (cx - 3, 40)])
    sk.path(post, WOOD)
    sk.path(poly_path([(cx + 1, base_y), (cx + 4, base_y), (cx + 3, 40), (cx + 1, 40)]), WOOD_D)
    sk.path(post, INK, 1.0, 0, 1.6)
    for y in (70, 100):
        sk.path(ribbon([(cx - 5, y), (cx, y + 2), (cx + 5, y)], [2, 3, 2]), (168, 150, 108))
    bowl = smooth_path([(cx - 13, 30), (cx + 13, 30), (cx + 9, 44), (cx - 9, 44)], True, 0.2)
    sk.path(bowl, (58, 58, 64))
    sk.path(ribbon([(cx - 12, 33), (cx + 12, 33)], [1.4, 1.4]), (120, 122, 128))
    sk.path(bowl, INK, 1.0, 0, 1.6)
    for k in range(4):
        x = cx - 8 + k * 5
        sk.path(ribbon([(x, 32), (x + 2, 22)], [3, 2]), (90, 60, 40))
    L = _canvas(W, Hh)
    L.a = sk.snap()
    # alev (ışıma): sıcak katmanlı damla
    se = Sk(W, Hh)
    fl = [(cx - 10, 30), (cx - 8, 14), (cx - 2, 2), (cx + 1, 10), (cx + 6, 0), (cx + 9, 16), (cx + 10, 30)]
    se.path(smooth_path(fl, True, 0.45), (255, 120, 40), 0.9, 2.0)
    se.path(smooth_path([(cx - 6, 30), (cx - 4, 18), (cx, 8), (cx + 4, 18), (cx + 6, 30)], True, 0.45), (255, 196, 90), 1.0, 1.2)
    se.path(smooth_path([(cx - 3, 30), (cx, 18), (cx + 3, 30)], True, 0.45), (255, 240, 200), 1.0)
    E = _canvas(W, Hh)
    E.a = se.snap()
    return L, (W, Hh), (cx, base_y), E


def balbal_decor(seed=41):
    W, Hh = 80, 120
    sk = Sk(W, Hh)
    base_y = Hh - 4
    balbal(sk, 40, base_y, 104, (112, 116, 106), (150, 158, 142), seed)
    rng = np.random.default_rng(seed)
    for _ in range(20):
        x = rng.uniform(14, W - 14)
        sk.path(blade(x, base_y + 4, rng.uniform(6, 18), rng.uniform(-0.5, 0.5), 2.2), (52, 84, 58) if rng.random() < 0.6 else (104, 142, 98))
    L = _canvas(W, Hh)
    L.a = sk.snap()
    return L, (W, Hh), (40, base_y)


def kule_dikme():
    """Gözetleme kulesi ayağı: dikeyde döşenen kabuklu kütük (genişlik 12 doku pikseli + kontur)."""
    W, Hh = 16, 256
    ys, xs = (np.mgrid[0:ik.P(Hh), 0:ik.P(W)].astype(np.float32) + 0.5) / ik.K
    u = (xs - W / 2) / 5.5
    cov = np.clip((5.5 - np.abs(xs - W / 2)) * ik.K + 0.5, 0, 1)
    tone = np.where(u < -0.3, 1.25, np.where(u < 0.35, 1.0, 0.68))
    n = fbm(W, Hh, [1.2, 6], 5, wrap=True)
    col = c01(WOOD)[None, None, :] * (tone * (1 + 0.1 * n))[..., None]
    ink = np.clip(1.6 - (5.5 - np.abs(xs - W / 2)) + 0.5, 0, 1) * cov
    col = mix(col, c01(INK)[None, None, :], ink[..., None])
    L = _canvas(W, Hh)
    L.a = premul(col.astype(np.float32), cov.astype(np.float32))
    sk = Sk(W, Hh)
    rng = np.random.default_rng(3)
    for _ in range(14):
        y = rng.uniform(0, Hh - 20)
        x = rng.uniform(4, W - 4)
        sk.path(ribbon([(x, y), (x + 0.5, y + 10), (x, y + 18)], [0.3, 1.2, 0.3]), INK, 0.6)
    L.over(sk.snap())
    return L


def kule_capraz():
    """Çapraz destek / kiriş: yatay döşenen ince kütük (yükseklik 10 + kontur)."""
    W, Hh = 256, 14
    ys, xs = (np.mgrid[0:ik.P(Hh), 0:ik.P(W)].astype(np.float32) + 0.5) / ik.K
    cov = np.clip((4.5 - np.abs(ys - Hh / 2)) * ik.K + 0.5, 0, 1)
    v = (ys - Hh / 2) / 4.5
    tone = np.where(v < -0.3, 1.22, np.where(v < 0.35, 0.95, 0.66))
    n = fbm(W, Hh, [6, 1.2], 7, wrap=True)
    col = c01(WOOD)[None, None, :] * (tone * (1 + 0.1 * n))[..., None]
    ink = np.clip(1.4 - (4.5 - np.abs(ys - Hh / 2)) + 0.5, 0, 1) * cov
    col = mix(col, c01(INK)[None, None, :], ink[..., None])
    L = _canvas(W, Hh)
    L.a = premul(col.astype(np.float32), cov.astype(np.float32))
    return L


def kule_bag():
    """Halat bağı (dikme ile kirişin kesiştiği yere)."""
    W, Hh = 22, 18
    sk = Sk(W, Hh)
    for k in range(4):
        y = 3 + k * 3.6
        pts = [(2, y), (11, y + 1.8), (20, y + 0.4)]
        sk.path(ribbon(pts, [2.0, 3.0, 2.0]), (168, 150, 108))
        sk.path(ribbon(pts, [2.0, 3.0, 2.0]), INK, 0.9, 0, 0.8)
    L = _canvas(W, Hh)
    L.a = sk.snap()
    return L


def export(save, to8, A):
    meta = {}

    tex = 2.0 * ik.K   # doku pikseli / dünya birimi

    def put(name, res):
        L, origin = res[0], res[2]
        save(to8(L.a), 'decor', name + '.png')
        h, w = L.a.shape[:2]
        meta[name] = {"size": [int(w), int(h)], "origin": [int(round(origin[0] * ik.K)), int(round(origin[1] * ik.K))], "texel": tex}
        if len(res) > 3:
            save(to8(res[3].a), 'decor', name + '_e.png')
            meta[name]["glow"] = True

    put('dilek_agaci_v2', dilek_agaci())
    put('kam_diregi_v2', kam_diregi())
    put('kaya_1_v2', kaya(101, 42, 26))
    put('kaya_2_v2', kaya(202, 30, 22))
    put('mantar_1_v2', mantar(301, 3))
    put('mantar_2_v2', mantar(302, 2))
    put('cicek_1_v2', cicek(401, 0))
    put('cicek_2_v2', cicek(402, 1))
    put('cicek_3_v2', cicek(403, 2))
    put('cira_v2', cira())
    put('balbal_v2', balbal_decor())
    for nm, fn in (('kule_dikme_v2', kule_dikme), ('kule_capraz_v2', kule_capraz), ('kule_bag_v2', kule_bag)):
        L = fn()
        save(to8(L.a), 'decor', nm + '.png')
        meta[nm] = {"size": [L.w, L.h], "origin": [0, 0], "texel": tex}
    json.dump(meta, open(os.path.join(A, 'decor', 'decor_v2.json'), 'w', encoding='utf-8'), indent=1)
