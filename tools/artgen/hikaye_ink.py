"""v42 Güneş Ana hikâyesi: sumi-e sinema panelleri ve görüm silüeti (sumi.py fırça takımı).

    python hikaye_ink.py                 hepsi -> assets/hikaye/<ad>.jpg (+ <ad>_isik.png ışıma), paneller.json
    python hikaye_ink.py giris_2 son_4   yalnızca bunlar
    python hikaye_ink.py --onizleme out.png   panellerin temas sayfası

Paneller 1600x900 (oyunda 960x540 mantıksal ekrana gerilir; 1080p'de 1,2 kat — mürekkep yıkaması yumuşak, fark okunmaz),
opak JPG; altın varak / kor ışıması yarım çözünürlükte ayrı PNG (Sinema.gd toplamalı karıştırır, nabız verir).
Kompozisyonlarda alt beşte bir sakin bırakılır: anlatı yazısı oraya fırçayla yazılır.
"""
import json
import math
import os
import sys

import numpy as np

from sumi import Sumi, save_rgb_jpg, save_rgba_png, fbm, catmull

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'assets', 'hikaye')
W, H = 1600, 900

NIGHT = (0.72, 0.74, 0.8)        # gece kâğıdı (soğuk gri)
DAWN = (0.97, 0.86, 0.72)        # tan kâğıdı (sıcak)
INDIGO = (0.36, 0.4, 0.58)
ROSE = (0.95, 0.55, 0.42)
SAFFRON = (0.98, 0.72, 0.32)
TEAL = (0.48, 0.72, 0.78)
BRAID_COLS = {'al': (0.86, 0.22, 0.16), 'ak': (0.97, 0.95, 0.9), 'gok': (0.28, 0.56, 0.86), 'sari': (0.96, 0.8, 0.2), 'altin': (0.93, 0.66, 0.22)}


# ====================================================================== motifler
def mountains(S, ridge, base, dens=0.5, blur=5.0, texture=True, seed=1, layer='D', col=None):
    """Sırt çizgisinden aşağı yıkama + sırt boyunca kuru fırça (ts'un) dokusu."""
    pts = list(ridge) + [(ridge[-1][0], base), (ridge[0][0], base)]
    m = S.path_mask(pts, smooth=True)
    S.wash(m, dens=dens, blur=blur, bleed=0.45, gran=0.45, seed=seed, layer=layer, col=col)
    if texture:
        rs = np.random.default_rng(seed)
        R = catmull(ridge, 6)
        for i in range(0, len(R) - 3, 3):
            a, b = R[i], R[i + 3]
            if rs.random() < 0.6:
                d = rs.uniform(8, 30)
                S.stroke([a, ((a[0] + b[0]) / 2 + rs.uniform(-4, 4), (a[1] + b[1]) / 2 + d * 0.3), (b[0], b[1] + d)], rs.uniform(3, 7),
                         load=0.55 * dens / 0.5, dry=0.75, taper=(0.1, 0.8), layer=layer, col=col)


def tree(S, x, yb, h, spread=1.0, seed=3, load=1.0, gold_leaves=0, roots=True, root_depth=160, leaves=True, gold_k=0.0, dark_leaves=1.0):
    """Ulu Kayın: kuru fırça gövde, dallanan kollar, uçlarda fırça yaprak kümeleri, aşağı kökler."""
    rs = np.random.default_rng(seed)
    top = yb - h
    # gövde: iki kenar darbesi (gölge yanı koyu ve kalın) + ortada tek geniş, düşük yüklü ıslak darbe
    bend = rs.uniform(-1, 1) * h * 0.02
    for side, wd, ld, dr in ((-1, 0.06, 1.0, 0.45), (1, 0.035, 0.85, 0.7)):
        off = side * h * 0.028
        S.stroke([(x + off * 2.6, yb + 10), (x + off * 1.4 + bend, yb - h * 0.22), (x + off + h * 0.02, yb - h * 0.5), (x + off * 0.4 - h * 0.012, yb - h * 0.76)],
                 h * wd, load=load * ld, dry=dr, taper=(0.12, 0.5))
    S.stroke([(x, yb + 4), (x + bend, yb - h * 0.25), (x + h * 0.02, yb - h * 0.5), (x - h * 0.012, yb - h * 0.72)], h * 0.075, load=load * 0.38, dry=0.75,
             taper=(0.02, 0.6))
    # kayın kabuğu: yatay kısa koyu çizgiler
    for k in range(14):
        yy = yb - rs.uniform(0.05, 0.62) * h
        S.stroke([(x - h * 0.03, yy), (x + rs.uniform(-0.01, 0.02) * h, yy + rs.uniform(-3, 3)), (x + h * 0.03, yy + rs.uniform(-2, 2))],
                 rs.uniform(2.5, 5), load=0.8, dry=0.5, taper=(0.3, 0.4))
    tips = []

    def branch(p, ang, ln, w, depth):
        if depth == 0 or ln < 12:
            tips.append(p)
            return
        bend = rs.uniform(-0.35, 0.35)
        q1 = (p[0] + math.cos(ang) * ln * 0.5, p[1] + math.sin(ang) * ln * 0.5)
        q = (p[0] + math.cos(ang + bend) * ln, p[1] + math.sin(ang + bend) * ln)
        S.stroke([p, q1, q], w, load=load * 0.9, dry=0.5, taper=(0.03, 0.7))
        n = 2 if depth > 1 else 3
        for i in range(n):
            na = ang + bend + rs.uniform(-0.65, 0.65) + (i - (n - 1) / 2) * 0.35
            branch(q, na, ln * rs.uniform(0.6, 0.78), w * 0.62, depth - 1)
        if depth <= 2:
            tips.append(q)

    starts = [0.5, 0.58, 0.66, 0.72, 0.78]
    for i, f in enumerate(starts):
        side = -1 if i % 2 == 0 else 1
        p = (x + side * h * 0.01, yb - h * f)
        ang = -math.pi / 2 + side * rs.uniform(0.55, 1.0) * spread
        branch(p, ang, h * rs.uniform(0.22, 0.3) * spread, h * 0.03, 4)
    branch((x, yb - h * 0.72), -math.pi / 2 + rs.uniform(-0.1, 0.1), h * 0.22, h * 0.03, 4)
    # yaprak kümeleri
    if leaves:
        for (tx, ty) in tips:
            for j in range(rs.integers(3, 7)):
                lx, ly = tx + rs.normal(0, h * 0.025), ty + rs.normal(0, h * 0.02)
                S.leaf(lx, ly, rs.uniform(h * 0.012, h * 0.03), rs.uniform(-math.pi, 0) - 0.3, load=0.75 * dark_leaves)
        # altın yapraklar
        gi = rs.permutation(len(tips))[:gold_leaves]
        for i in gi:
            tx, ty = tips[i]
            for j in range(4):
                m = S.leaf(tx + rs.normal(0, h * 0.02), ty + rs.normal(0, h * 0.02), rs.uniform(h * 0.015, h * 0.03), rs.uniform(-math.pi, 0), ret=True)
                S.put(m, 'G', k=1.0)
    if roots:
        for k in range(7):
            side = (k - 3) / 3.0
            pts = [(x + side * h * 0.02, yb - 4), (x + side * h * 0.12, yb + root_depth * 0.25), (x + side * h * 0.28 + rs.uniform(-20, 20), yb + root_depth * 0.6),
                   (x + side * h * 0.42 + rs.uniform(-30, 30), yb + root_depth)]
            S.stroke(pts, h * rs.uniform(0.02, 0.035), load=load, dry=0.6, taper=(0.05, 0.9))
    return tips


def braid(S, pts, w, layer='G', col=None, load=1.0, k=1.0):
    """Örgü: eğri boyunca sivrilen pürüzsüz şerit; üstüne sık, ters yönlü kama izleri (saç örgüsü dokusu) şeridi kısmen
    söndürerek kazınır."""
    P = np.array(catmull(pts, 12))
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    tot = L[-1]
    acc = S.stroke(pts, w, load=load, dry=0.12, taper=(0.06, 0.85), ret=True, bristles=10)
    n = int(tot / (w * 0.5))
    cut = np.zeros_like(acc)
    for i in range(n):
        s = (i + 0.5) / n * tot
        j = min(max(np.searchsorted(L, s), 1), len(P) - 1)
        p = P[j]
        tg = P[j] - P[j - 1]
        tg = tg / max(1e-6, np.linalg.norm(tg))
        nr = np.array([-tg[1], tg[0]])
        ww = w * (1.0 - 0.8 * (s / tot) ** 1.2)
        if ww < 3.0:
            break
        side = 1 if i % 2 == 0 else -1
        a = p + nr * side * ww * 0.45
        b = p - tg * ww * 0.35
        m = S.stroke([tuple(a), tuple(b)], max(1.0, ww * 0.12), load=1.0, dry=0.0, taper=(0.1, 0.5), ret=True, n=3, bristles=2, smooth=False)
        cut = np.maximum(cut, m)
    acc = acc * (1 - 0.55 * cut)
    S.put(acc, layer, col, k)
    return acc


def figure_gun_ana(S, cx, cy, s, layer_body='D', body_dens=0.85, braids=True, halo=True, braid_layer='G', braid_cols=None, arms='open', wind=0.35):
    """Gün Ana: önden, kollar açık; başından ışın gibi beş örgü yayılır; ardında altın enso (güneş). Gövde birkaç geniş,
    savrulan fırça darbesiyle çizilir (sumi-e figürü: çok az darbe, çok boşluk). s: baş-göğüs ölçüsü; wind: etek savrulması."""
    hx, hy = cx, cy - s * 0.98
    if halo:
        S.enso(hx, hy + s * 0.05, s * 1.0, s * 0.17, load=1.0, dry=0.4, layer='G', a0=-2.3, span=5.8)
        S.enso(hx, hy + s * 0.05, s * 1.24, s * 0.045, load=0.7, dry=0.75, layer='G', a0=0.7, span=4.4)
    if braids:
        ids = ['al', 'ak', 'gok', 'sari', 'altin']
        for i, a in enumerate(np.linspace(-2.65, -0.5, 5)):
            base = (hx + math.cos(a) * s * 0.08, hy - s * 0.06 + math.sin(a) * s * 0.08)
            ln = s * (1.7 + 0.25 * math.sin(i * 1.7))
            pts = [base]
            for k in range(1, 7):
                t = k / 6
                aa = a + 0.22 * math.sin(t * math.pi * 1.6 + i)
                pts.append((base[0] + math.cos(aa) * ln * t, base[1] + math.sin(aa) * ln * t))
            if braid_cols:
                braid(S, pts, s * 0.15, layer='C', col=braid_cols[ids[i]], k=0.95)
                braid(S, pts, s * 0.08, layer='G', k=0.5)
            else:
                braid(S, pts, s * 0.15, layer=braid_layer)
    L = dict(layer=layer_body)
    # silüet: boyun dibi kökenli birimlerde (y aşağı) sağ yarı; sol yarı aynası (rüzgâr eteği sağa savurur)
    R = [(0.035, -0.05), (0.16, 0.05), (0.27, 0.15), (0.42, 0.3), (0.56, 0.44), (0.67, 0.56), (0.74, 0.74), (0.77, 0.98), (0.7, 1.2),
         (0.6, 1.0), (0.52, 0.78), (0.4, 0.62), (0.33, 0.66), (0.38, 1.0), (0.5, 1.4), (0.66, 1.84), (0.86, 2.24)]
    ox, oy = hx, hy + s * 0.2

    def tp(q, side):
        x, y = q
        sway = wind * max(0.0, y - 0.6) ** 1.4 * 0.35
        return (ox + (side * x + sway) * s, oy + y * s)
    out = [tp(q, 1) for q in R] + [(ox + (0.3 + wind * 0.9) * s, oy + 2.32 * s), (ox + (-0.2 + wind * 0.7) * s, oy + 2.3 * s)] + [tp(q, -1) for q in reversed(R)]
    m = S.path_mask(out)
    # dikey geçiş: göğüs koyu, etek sise doğru açılır
    yy = np.arange(S.h, dtype=np.float32)[:, None]
    fade = np.clip(1.15 - (yy - oy) / (s * 2.4), 0.12, 1.0)
    S.wash(m * fade, dens=0.78 * body_dens, blur=2.2, bleed=0.55, gran=0.12, **L)
    hd = S.ellipse_mask(hx, hy, s * 0.1, s * 0.125)
    S.wash(hd, dens=0.95 * body_dens, blur=1.0, bleed=0.25, gran=0.1, **L)
    S.dots([(hx + s * 0.02, hy - s * 0.13, s * 0.07)], 0, layer=layer_body, k=0.95 * body_dens)
    S.stroke([(hx - s * 0.035, hy + s * 0.08), (hx - s * 0.03, hy + s * 0.2)], s * 0.05, load=body_dens * 0.9, dry=0.2, **L)
    # gölge yanı konturu (sol) ve yen altları: kuru fırça
    lt = [tp(q, -1) for q in R[:8]]
    S.stroke(lt, s * 0.06, load=body_dens, dry=0.5, taper=(0.1, 0.6), **L)
    S.stroke([tp(q, -1) for q in R[12:]], s * 0.07, load=body_dens * 0.9, dry=0.55, taper=(0.05, 0.9), **L)
    S.stroke([tp(q, 1) for q in R[12:]], s * 0.035, load=body_dens * 0.7, dry=0.75, taper=(0.05, 0.9), **L)
    # kıvrımlar ve kuşak
    for f in (-0.18, 0.04, 0.24):
        S.stroke([tp((abs(f) * 0.6, 0.62), 1 if f > 0 else -1), tp((abs(f) * 0.9, 1.3), 1 if f > 0 else -1), tp((abs(f) * 1.4, 2.0), 1 if f > 0 else -1)],
                 s * 0.03, load=body_dens * 0.6, dry=0.7, taper=(0.1, 0.9), **L)
    S.stroke([tp((0.33, 0.56), -1), tp((0.0, 0.6), 1), tp((0.33, 0.56), 1)], s * 0.05, load=body_dens, dry=0.35, taper=(0.2, 0.3), **L)
    for side in (-1, 1):
        S.dots([(*tp((0.66, 0.62), side), s * 0.04)], 0, layer=layer_body, k=0.95 * body_dens)
    return (hx, hy)


def figure_bengu(S, cx, cy, s, pose='stand', load=1.0, hair='braid', sword=True, seed=5, layer='D', col=None):
    """Bengü: birkaç kalın kuru fırça darbesi. pose: stand (yandan, yola bakar), fall (sırtüstü düşüş), kneel, sit."""
    rs = np.random.default_rng(seed)
    L = dict(layer=layer, col=col)
    if pose == 'stand':
        hd = (cx, cy - s * 1.62)
        S.dots([(hd[0], hd[1], s * 0.11)], 0, k=load, **L)
        S.stroke([(cx, cy - s * 1.5), (cx - s * 0.04, cy - s * 1.0), (cx - s * 0.02, cy - s * 0.55)], s * 0.22, load=load, dry=0.35, taper=(0.1, 0.3), **L)
        # kaftan eteği
        S.wash(S.path_mask([(cx - s * 0.12, cy - s * 0.75), (cx + s * 0.14, cy - s * 0.75), (cx + s * 0.3, cy - s * 0.15), (cx - s * 0.28, cy - s * 0.12)]),
               dens=0.8 * load, blur=1.5, bleed=0.4, gran=0.3, **L)
        S.stroke([(cx - s * 0.08, cy - s * 0.2), (cx - s * 0.14, cy - s * 0.02), (cx - s * 0.18, cy)], s * 0.09, load=load, dry=0.4, **L)
        S.stroke([(cx + s * 0.08, cy - s * 0.2), (cx + s * 0.12, cy - s * 0.02), (cx + s * 0.16, cy)], s * 0.09, load=load, dry=0.4, **L)
        if hair == 'braid':
            S.stroke([(hd[0] - s * 0.06, hd[1]), (hd[0] - s * 0.22, hd[1] + s * 0.4), (hd[0] - s * 0.3, hd[1] + s * 0.8), (hd[0] - s * 0.42, hd[1] + s * 1.05)],
                     s * 0.07, load=load, dry=0.3, taper=(0.1, 0.8), **L)
        elif hair == 'short':
            S.stroke([(hd[0] - s * 0.05, hd[1] - s * 0.05), (hd[0] - s * 0.2, hd[1] + s * 0.08), (hd[0] - s * 0.3, hd[1] + s * 0.12)], s * 0.08, load=load, dry=0.4,
                     taper=(0.1, 0.9), **L)
        if sword:
            S.stroke([(cx + s * 0.1, cy - s * 0.85), (cx + s * 0.25, cy - s * 0.5), (cx + s * 0.5, cy + s * 0.02)], s * 0.035, load=load, dry=0.2, taper=(0.02, 0.9), **L)
        S.stroke([(cx + s * 0.02, cy - s * 1.35), (cx + s * 0.1, cy - s * 1.05), (cx + s * 0.12, cy - s * 0.85)], s * 0.07, load=load, dry=0.4, **L)
    elif pose == 'fall':
        J = {'pel': (0, 0), 'ch': (-0.45, 0.25), 'nk': (-0.6, 0.33), 'hd': (-0.74, 0.42), 'sh': (-0.52, 0.27), 'el1': (-0.74, -0.05), 'ha1': (-0.62, -0.42),
             'el2': (-0.36, 0.62), 'ha2': (-0.08, 0.76), 'kn1': (0.4, -0.36), 'ft1': (0.56, -0.8), 'kn2': (0.52, -0.06), 'ft2': (0.96, -0.28)}
        segs = [('pel', 'ch', 0.3, 0.28), ('ch', 'nk', 0.16, 0.1), ('sh', 'el1', 0.1, 0.08), ('el1', 'ha1', 0.08, 0.05), ('sh', 'el2', 0.1, 0.08),
                ('el2', 'ha2', 0.08, 0.05), ('pel', 'kn1', 0.15, 0.11), ('kn1', 'ft1', 0.1, 0.07), ('pel', 'kn2', 0.15, 0.11), ('kn2', 'ft2', 0.1, 0.07)]
        skirt = [(-0.12, 0.12), (0.12, -0.28), (0.5, -0.4), (0.62, -0.12), (0.3, 0.1)]
        P = silhouette(S, cx, cy, s, J, segs, polys=[skirt], dens=0.95 * load, **L)
        S.dots([(P['hd'][0], P['hd'][1], s * 0.13)], 0, k=load, **L)
        hd = P['hd']
        braid(S, [(hd[0] - s * 0.06, hd[1] - s * 0.06), (hd[0] - s * 0.22, hd[1] - s * 0.45), (hd[0] - s * 0.05, hd[1] - s * 0.85), (hd[0] - s * 0.25, hd[1] - s * 1.25)],
              s * 0.12, layer=layer, col=col, k=load)
    elif pose == 'kneel':
        J = {'pel': (0, -0.45), 'ch': (0.03, -0.95), 'nk': (0.05, -1.08), 'hd': (0.07, -1.2), 'sh': (0.05, -0.93), 'el1': (0.3, -0.78), 'ha1': (0.4, -1.0),
             'el2': (0.22, -0.7), 'ha2': (0.34, -0.93), 'kn1': (0.38, -0.42), 'ft1': (0.4, 0.0), 'kn2': (-0.08, 0.0), 'ft2': (-0.5, 0.0)}
        segs = [('pel', 'ch', 0.3, 0.27), ('ch', 'nk', 0.15, 0.1), ('sh', 'el1', 0.1, 0.08), ('el1', 'ha1', 0.08, 0.06), ('sh', 'el2', 0.1, 0.08),
                ('el2', 'ha2', 0.08, 0.06), ('pel', 'kn1', 0.16, 0.12), ('kn1', 'ft1', 0.11, 0.08), ('pel', 'kn2', 0.16, 0.12), ('kn2', 'ft2', 0.11, 0.06)]
        skirt = [(-0.18, -0.62), (0.16, -0.62), (0.4, -0.3), (0.1, -0.12), (-0.3, -0.1)]
        P = silhouette(S, cx, cy, s, J, segs, polys=[skirt], dens=0.95 * load, **L)
        hd = P['hd']
        S.dots([(hd[0], hd[1], s * 0.12)], 0, k=load, **L)
        # kesilmiş kısa saç: ensede bir tutam
        S.stroke([(hd[0] - s * 0.06, hd[1] - s * 0.08), (hd[0] - s * 0.17, hd[1] + s * 0.02), (hd[0] - s * 0.21, hd[1] + s * 0.1)], s * 0.08, load=load, dry=0.4,
                 taper=(0.1, 0.9), **L)
    elif pose == 'sit':
        hd = (cx, cy - s * 0.95)
        S.dots([(hd[0], hd[1], s * 0.11)], 0, k=load, **L)
        S.stroke([(cx, cy - s * 0.82), (cx - s * 0.03, cy - s * 0.5), (cx, cy - s * 0.2)], s * 0.22, load=load, dry=0.35, taper=(0.1, 0.3), **L)
        S.stroke([(cx, cy - s * 0.2), (cx + s * 0.3, cy - s * 0.15), (cx + s * 0.35, cy + s * 0.25), (cx + s * 0.32, cy + s * 0.55)], s * 0.1, load=load, dry=0.45, **L)
        S.stroke([(cx - s * 0.02, cy - s * 0.18), (cx + s * 0.2, cy - s * 0.05), (cx + s * 0.18, cy + s * 0.35), (cx + s * 0.25, cy + s * 0.6)], s * 0.09, load=load, dry=0.5, **L)
        S.stroke([(hd[0] - s * 0.05, hd[1] - s * 0.05), (hd[0] - s * 0.22, hd[1] + s * 0.05), (hd[0] - s * 0.34, hd[1] + s * 0.02)], s * 0.08, load=load, dry=0.4,
                 taper=(0.1, 0.9), **L)


def silhouette(S, cx, cy, s, J, segs, polys=(), dens=0.93, edge=True, layer='D', col=None):
    """Gölge oyunu (Karagöz) gibi tek parça silüet: eklemler arası sivrilen kapsüller + çokgenler birleşir, ıslak
    yıkamayla doldurulur; gölge yanına kuru fırça kontur. J: ad -> (x, y) (s birimi), segs: (a, b, w0, w1)."""
    import skia
    P = {k: (cx + v[0] * s, cy + v[1] * s) for k, v in J.items()}

    def fn(c):
        paint = skia.Paint(AntiAlias=True, Color=skia.ColorWHITE)
        for a, b, w0, w1 in segs:
            p0, p1 = np.array(P[a]), np.array(P[b])
            d = p1 - p0
            ln = max(1e-3, np.linalg.norm(d))
            nrm = np.array([-d[1], d[0]]) / ln
            r0, r1 = w0 * s * 0.5, w1 * s * 0.5
            pa = skia.Path()
            q = [p0 + nrm * r0, p1 + nrm * r1, p1 - nrm * r1, p0 - nrm * r0]
            pa.moveTo(*q[0])
            for qq in q[1:]:
                pa.lineTo(*qq)
            pa.close()
            c.drawPath(pa, paint)
            c.drawCircle(float(p0[0]), float(p0[1]), float(r0), paint)
            c.drawCircle(float(p1[0]), float(p1[1]), float(r1), paint)
        for poly in polys:
            pts = catmull([(cx + x * s, cy + y * s) for x, y in poly], 6)
            pa = skia.Path()
            pa.moveTo(*pts[0])
            for qq in pts[1:]:
                pa.lineTo(*qq)
            pa.close()
            c.drawPath(pa, paint)
    m = S.raster(fn)
    S.wash(m, dens=dens, blur=0.9, bleed=0.25, gran=0.08, layer=layer, col=col)
    if edge:
        for a, b, w0, w1 in segs:
            if w0 > 0.08:
                p0, p1 = np.array(P[a]), np.array(P[b])
                d = p1 - p0
                nrm = np.array([-d[1], d[0]]) / max(1e-3, np.linalg.norm(d))
                o = nrm * w0 * s * 0.5
                S.stroke([tuple(p0 + o), tuple((p0 + p1) / 2 + o * 1.05), tuple(p1 + nrm * w1 * s * 0.5)], s * 0.035, load=0.9, dry=0.65, taper=(0.1, 0.6),
                         layer=layer, col=col)
    return P


def chain(S, pts, link, w, load=1.0, broken=None, layer='D', col=None, gap_glow=False):
    """Zincir: eğri boyunca dönüşümlü elips halkalar (biri yüzden, biri yandan). broken: kırık halka dizini."""
    P = np.array(catmull(pts, 12))
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    Lc = np.concatenate([[0], np.cumsum(seg)])
    n = int(Lc[-1] / (link * 0.78))
    for i in range(n):
        s = (i + 0.5) / n * Lc[-1]
        j = min(max(np.searchsorted(Lc, s), 1), len(P) - 1)
        p = P[j]
        tg = P[j] - P[j - 1]
        a = math.atan2(tg[1], tg[0])
        if broken is not None and abs(i - broken) <= 0:
            continue
        if i % 2 == 0:
            rx, ry = link * 0.55, link * 0.3
            pts2 = [(p[0] + math.cos(a) * rx * math.cos(t) - math.sin(a) * ry * math.sin(t),
                     p[1] + math.sin(a) * rx * math.cos(t) + math.cos(a) * ry * math.sin(t)) for t in np.linspace(-2.9, 2.9, 22)]
            S.stroke(pts2, w, load=load, dry=0.3, taper=(0.15, 0.25), layer=layer, col=col, n=3)
        else:
            q0 = (p[0] - math.cos(a) * link * 0.5, p[1] - math.sin(a) * link * 0.5)
            q1 = (p[0] + math.cos(a) * link * 0.5, p[1] + math.sin(a) * link * 0.5)
            S.stroke([q0, p, q1], w * 1.25, load=load, dry=0.25, taper=(0.2, 0.2), layer=layer, col=col, n=3)


def seal(S, x, y, s, seed=0):
    """Sanatçı mührü: kızıl kare, içinde kâğıt rengi tamga (Kayı: iki ok + yay)."""
    m = S.path_mask([(x, y), (x + s, y + s * 0.02), (x + s * 0.98, y + s), (x + s * 0.01, y + s * 0.97)], smooth=False)
    n = fbm(S.h, S.w, 3.0, 400 + seed, octaves=2)
    S.put(m * (0.75 + 0.3 * n), 'R')
    # tamga (silinir)
    t = S.stroke([(x + s * 0.5, y + s * 0.2), (x + s * 0.5, y + s * 0.8)], s * 0.1, load=1.0, dry=0.1, taper=(0.1, 0.1), ret=True)
    t = np.maximum(t, S.stroke([(x + s * 0.22, y + s * 0.42), (x + s * 0.5, y + s * 0.62), (x + s * 0.78, y + s * 0.42)], s * 0.09, load=1.0, dry=0.1, taper=(0.1, 0.1), ret=True))
    S.R *= 1 - np.clip(t * 0.9, 0, 1)


def leaves_fall(S, n, box, seed, gold=0.3, k=0.8):
    rs = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    for i in range(n):
        x, y = rs.uniform(x0, x1), rs.uniform(y0, y1)
        m = S.leaf(x, y, rs.uniform(8, 18), rs.uniform(0, math.tau), ret=True)
        S.put(m, 'G' if rs.random() < gold else 'D', k=k)


def soul_bird(S, cx, cy, s, layer='G', k=1.0):
    """Ruh kuşu: iki kanat fırçası + gövde damlası (altın)."""
    for side in (-1, 1):
        m = S.stroke([(cx, cy), (cx + side * s * 0.5, cy - s * 0.45), (cx + side * s * 1.1, cy - s * 0.35)], s * 0.28, load=1.0, dry=0.3, taper=(0.05, 0.85), ret=True)
        S.put(m, layer, k=k)
    m = S.stroke([(cx - s * 0.15, cy - s * 0.05), (cx + s * 0.1, cy + s * 0.08), (cx + s * 0.45, cy + s * 0.3)], s * 0.22, load=1.0, dry=0.2, taper=(0.1, 0.9), ret=True)
    S.put(m, layer, k=k)


def sun_glow(S, cx, cy, r, col=(1.0, 0.75, 0.35), k=1.0):
    yy, xx = np.mgrid[0:S.h, 0:S.w].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    g = np.exp(-(d / r) ** 2)
    S.put(g, 'E', col=col, k=k)
    return g


# ====================================================================== paneller
def giris_1():
    """Üç kat dünya ve Ulu Kayın: gök (yıldız tozu), yer (ufuk dağları), yeraltı (kökler koyu yıkamada)."""
    S = Sumi(W, H, 101)
    S.grad_wash(0, 380, 0.42, 0.05, seed=11, gran=0.5)       # gece göğü üstten
    S.grad_wash(560, 900, 0.0, 0.9, seed=12, gran=0.55, wobble=60)   # yeraltı alttan
    mountains(S, [(0, 560), (180, 520), (330, 545), (520, 470), (700, 530), (880, 500), (1080, 540), (1260, 480), (1440, 535), (1600, 510)], 620, dens=0.32, seed=13)
    S.mist(600, 40, 0.8, seed=14)
    tree(S, 800, 600, 520, spread=1.15, seed=15, load=1.0, gold_leaves=0, root_depth=230)
    # Kut damarı: gövdeden yukarı ince altın iplik
    S.stroke([(800, 760), (796, 600), (806, 420), (798, 260), (808, 140)], 5, load=1.0, dry=0.55, layer='G', taper=(0.1, 0.4))
    rs = np.random.default_rng(16)
    S.dots([(rs.uniform(0, W), rs.uniform(0, 300), rs.uniform(0.8, 2.2)) for _ in range(140)], 0, layer='G', k=0.7)
    # ay: kâğıt boşluğu + ince enso
    S.erase(S.ellipse_mask(1300, 140, 54, 54), 0.95)
    S.enso(1300, 140, 58, 5, load=0.6, dry=0.6, a0=0.4, span=4.8)
    seal(S, 1500, 60, 44, 1)
    return S, {'koyu': True}


def giris_2():
    """Gün Ana, Kaf'ın ardından doğar: ardında altın enso (güneş), başından beş örgü ışın gibi yayılır."""
    S = Sumi(W, H, 102)
    S.grad_wash(0, 900, 0.0, 0.0)
    S.wash(S.path_mask([(0, 0), (1600, 0), (1600, 900), (0, 900)]), dens=0.0)
    sun_glow(S, 800, 330, 420, col=(1.0, 0.7, 0.35), k=0.55)
    S.put(sun_glow(S, 800, 330, 380, col=(0, 0, 0), k=0.0) * 0.55, 'C', col=SAFFRON)
    figure_gun_ana(S, 800, 470, 210, body_dens=0.9)
    # Kaf dağları önde: koyu, keskin
    mountains(S, [(0, 640), (160, 560), (300, 610), (430, 520), (560, 600), (650, 640), (760, 690), (900, 700), (1010, 620), (1150, 540), (1290, 600),
                  (1420, 520), (1600, 600)], 900, dens=0.68, blur=3.0, seed=21)
    mountains(S, [(0, 760), (220, 700), (480, 740), (800, 780), (1100, 730), (1380, 760), (1600, 720)], 900, dens=0.4, blur=6.0, seed=22, texture=False)
    S.mist(705, 30, 0.6, seed=23)
    seal(S, 60, 60, 44, 2)
    return S, {'koyu': False}


def giris_3():
    """Erlik köklerden çıkar: koyu gece; boynuzlu dev gölge soldan, kara kırkı; dokuz gecenin zinciri çaprazlama;
    kesilmiş örgüler altın kırıklar hâlinde düşer; zincirli Gün Ana sağ altta, solgun."""
    S = Sumi(W, H, 103)
    S.grad_wash(0, 900, 0.82, 0.92, seed=31, gran=0.6, wobble=80)
    # Erlik: soldan yükselen boynuzlu gölge (daha koyu yıkama, kenarında koyu halka)
    body = [(0, 900), (0, 160), (120, 120), (230, 170), (330, 280), (420, 430), (470, 620), (520, 900)]
    S.wash(S.path_mask(body), dens=0.6, blur=10, bleed=0.6, gran=0.4, seed=32)
    for side, base in ((-1, (150, 150)), (1, (260, 170))):
        S.stroke([base, (base[0] + side * 30, base[1] - 70), (base[0] + side * 10 + 40, base[1] - 130), (base[0] + 90, base[1] - 120)], 26, load=1.0, dry=0.3, taper=(0.02, 0.9))
    S.dots([(210, 235, 9), (270, 240, 8)], 0, layer='R', k=1.0)
    S.put(sun_glow(S, 240, 238, 30, col=(1.0, 0.2, 0.1), k=0.0), 'D', k=0.0)
    S.put(np.zeros((H, W), np.float32), 'D')
    sun_glow(S, 240, 238, 26, col=(1.0, 0.25, 0.12), k=0.9)
    # kara kırkı (makas): iki uzun bıçak
    S.stroke([(380, 420), (560, 360), (760, 330)], 18, load=1.0, dry=0.15, taper=(0.05, 0.95))
    S.stroke([(390, 470), (570, 400), (770, 345)], 14, load=1.0, dry=0.15, taper=(0.05, 0.95))
    # zincir: sağ üstten sol alta
    chain(S, [(1650, 80), (1300, 260), (1150, 520), (1180, 760), (1250, 950)], 70, 14, load=1.0)
    # zincirli Gün Ana (kâğıt boşluğu: silinmiş silüet, içi soluk altın)
    m = S.path_mask([(1150, 520), (1110, 560), (1095, 700), (1060, 900), (1340, 900), (1300, 700), (1285, 560), (1245, 520)])
    S.erase(np.clip(m, 0, 1) * 0.0, 0.0)
    S.erase(S.ellipse_mask(1197, 485, 30, 36), 0.85)
    S.erase(ndimage_blur(m, 6), 0.72)
    # kesilmiş örgüler: kıvrılarak düşen altın teller, uçlarında kırık ışık
    rs = np.random.default_rng(34)
    for i in range(5):
        x0 = 790 + i * 62 + rs.uniform(-15, 15)
        y0 = 300 + rs.uniform(-25, 25) + i * 12
        ang = 0.5 + rs.uniform(-0.5, 0.5)
        pts = [(x0, y0)]
        for k in range(1, 5):
            ang += rs.uniform(-0.7, 0.7)
            pts.append((pts[-1][0] + math.cos(ang) * 22 + rs.uniform(-25, 25), pts[-1][1] + 55 + rs.uniform(0, 25)))
        braid(S, pts, 20 - i, layer='G')
        S.splatter(pts[0][0], pts[0][1], 18, 10, size=(1, 3), layer='G', k=0.9)
    seal(S, 1500, 790, 44, 3)
    return S, {'koyu': True}


def ndimage_blur(m, r):
    from scipy import ndimage
    return ndimage.gaussian_filter(m, r)


def giris_4():
    """Bengü'nün düşüşü: sönen tören ateşi (kor), yarık kam davulu, havada savrulan beden, kılıç ayrı düşer."""
    S = Sumi(W, H, 104)
    S.grad_wash(0, 900, 0.55, 0.3, seed=41, gran=0.55, wobble=60)
    S.grad_wash(620, 900, 0.0, 0.6, seed=42, gran=0.5)
    # sönen ateş: kor yıkaması (renkli) + duman fırçası
    S.wash(S.ellipse_mask(380, 700, 170, 60), dens=0.75, blur=14, bleed=0.3, gran=0.6, layer='C', col=(0.95, 0.42, 0.2), seed=43)
    sun_glow(S, 380, 690, 120, col=(1.0, 0.42, 0.12), k=0.85)
    S.splatter(380, 640, 120, 90, size=(1.0, 3.5), layer='R', k=0.9, seed=44)
    S.splatter(380, 600, 80, 120, size=(0.8, 2.4), layer='E', col=(1.0, 0.5, 0.15), k=1.0, seed=45)
    for k in range(4):
        S.stroke([(330 + k * 30, 680), (310 + k * 40, 520), (360 + k * 20, 380), (300 + k * 50, 200)], 26 - k * 4, load=0.35, dry=0.85, taper=(0.1, 0.9))
    # odunlar
    for a, b in (((280, 730), (470, 690)), ((300, 690), (480, 740))):
        S.stroke([a, b], 20, load=1.0, dry=0.6, taper=(0.1, 0.2))
    # yarık kam davulu (sağ altta, yere düşmüş)
    S.enso(1200, 760, 70, 12, load=1.0, dry=0.4, squash=0.45, a0=-2.6, span=5.2)
    S.stroke([(1150, 745), (1200, 770), (1235, 752)], 6, load=0.9, dry=0.3)
    S.stroke([(1290, 740), (1330, 690)], 6, load=0.9, dry=0.3)
    # Bengü düşüyor
    figure_bengu(S, 860, 420, 170, pose='fall', load=1.0)
    # kılıç ayrı: dönerek
    S.stroke([(1080, 300), (1180, 250), (1290, 205)], 8, load=1.0, dry=0.1, taper=(0.02, 0.95))
    S.stroke([(1070, 290), (1095, 318)], 10, load=1.0, dry=0.1, taper=(0.2, 0.2))
    # kan / mürekkep sıçrantısı
    S.splatter(760, 460, 60, 70, size=(1.0, 6.0), layer='R', k=0.85, seed=46)
    S.splatter(780, 470, 40, 60, size=(1.0, 4.0), layer='D', k=0.9, seed=47)
    seal(S, 60, 60, 44, 4)
    return S, {'koyu': True}


def giris_5():
    """Umay Ana'nın kanatları: soluk turkuaz yıkamayla iki dev kanat, ortada altın ruh kuşu; çapraz Ulu Kayın dalı."""
    S = Sumi(W, H, 105)
    S.grad_wash(0, 900, 0.18, 0.28, seed=51, gran=0.5)
    sun_glow(S, 800, 420, 140, col=(1.0, 0.85, 0.5), k=0.9)
    for side in (-1, 1):
        # kanat: üst üste dizilmiş uzun tüy darbeleri (renkli yıkama + koyu uç)
        for i in range(9):
            a0 = -0.9 + i * 0.18
            ln = 520 - i * 28
            base = (800 + side * 60, 420 + i * 8)
            tip = (800 + side * (60 + math.cos(a0) * ln), 420 + math.sin(a0) * ln * 0.75 + 180)
            mid = ((base[0] + tip[0]) / 2 + side * 20, (base[1] + tip[1]) / 2 - 60)
            m = S.stroke([base, mid, tip], 70 - i * 3, load=0.85, dry=0.35, taper=(0.05, 0.8), ret=True)
            S.put(m, 'C', col=TEAL, k=0.55)
            S.stroke([(mid[0], mid[1]), tip], 6, load=0.6, dry=0.6, taper=(0.1, 0.9))
        S.stroke([(800 + side * 60, 400), (800 + side * 260, 250), (800 + side * 560, 210)], 14, load=0.95, dry=0.45, taper=(0.05, 0.9))
    soul_bird(S, 800, 430, 70, layer='G')
    sun_glow(S, 800, 425, 60, col=(1.0, 0.9, 0.55), k=1.0)
    # Ulu Kayın dalı: sol üstten
    S.stroke([(-20, 120), (300, 150), (560, 230), (700, 320)], 34, load=1.0, dry=0.5, taper=(0.02, 0.95))
    S.stroke([(300, 150), (360, 80), (420, 40)], 14, load=1.0, dry=0.5, taper=(0.05, 0.9))
    rs = np.random.default_rng(52)
    for j in range(26):
        S.leaf(rs.uniform(60, 680), rs.uniform(60, 300), rs.uniform(12, 26), rs.uniform(-math.pi, 0.3), load=0.8)
    leaves_fall(S, 14, (200, 300, 1500, 760), 53, gold=0.0, k=0.6)
    seal(S, 1500, 790, 44, 5)
    return S, {'koyu': False}


def giris_6():
    """Yol aşağı iner: solgun ay, Ulu Kayın'ın kökleri kemer olur; küçük Bengü kemerin ağzında aşağı bakar."""
    S = Sumi(W, H, 106)
    S.grad_wash(0, 900, 0.5, 0.95, seed=61, gran=0.55, wobble=40)
    S.erase(S.ellipse_mask(1180, 170, 70, 70), 0.96)
    S.enso(1180, 170, 74, 4, load=0.5, dry=0.6, a0=1.0, span=4.0)
    sun_glow(S, 1180, 170, 160, col=(0.55, 0.65, 0.85), k=0.35)
    # kök kemeri: iki yandan kalın kuru kökler, ortada boşluk (kâğıt)
    S.erase(S.path_mask([(560, 900), (600, 560), (700, 430), (800, 400), (900, 430), (1000, 560), (1040, 900)]), 0.55)
    for side in (-1, 1):
        for k in range(5):
            x0 = 800 + side * (220 + k * 40)
            S.stroke([(x0, -10), (x0 - side * 30, 250), (800 + side * (140 + k * 22), 470), (800 + side * (200 + k * 30), 900)], 30 - k * 4, load=1.0, dry=0.55,
                     taper=(0.02, 0.6))
    # aşağı inen yol: basamak fırçaları
    for i in range(7):
        y = 560 + i * 48
        w = 150 + i * 34
        S.stroke([(800 - w / 2, y), (800, y + 6), (800 + w / 2, y)], 9 - i * 0.5, load=0.6, dry=0.7, taper=(0.3, 0.3))
    S.mist(860, 60, 0.4, seed=62)
    figure_bengu(S, 800, 540, 95, pose='stand', load=1.0)
    seal(S, 60, 60, 44, 6)
    return S, {'koyu': True}


def son_1():
    """Beş örgüyü avucunda örer: diz çökmüş Bengü, elinde renkli beş örgü, kısa kesilmiş kendi örgüsü altıncı tel."""
    S = Sumi(W, H, 111)
    S.grad_wash(0, 900, 0.62, 0.8, seed=71, gran=0.55)
    sun_glow(S, 820, 520, 260, col=(1.0, 0.7, 0.35), k=0.6)
    figure_bengu(S, 700, 800, 250, pose='kneel', load=1.0)
    # eller ve örgüler: elden yukarı, ışık gibi yükselir
    ids = ['al', 'ak', 'gok', 'sari', 'altin']
    for i, bid in enumerate(ids):
        a = -1.9 + i * 0.22
        base = (795, 560)
        pts = [base, (base[0] + 60 + i * 12, base[1] - 120), (base[0] + 40 + math.cos(a) * 120 + i * 30, base[1] - 260), (base[0] + 120 + i * 50, base[1] - 420)]
        braid(S, pts, 26, layer='C', col=BRAID_COLS[bid], k=0.95)
        braid(S, pts, 14, layer='G', k=0.5)
    # altıncı tel: Bengü'nün kara örgüsü (kesik ucu)
    braid(S, [(795, 565), (830, 430), (930, 330), (1100, 240)], 22, layer='D', k=0.95)
    S.splatter(900, 330, 60, 90, size=(1, 3), layer='G', k=0.9, seed=72)
    seal(S, 1500, 790, 44, 7)
    return S, {'koyu': True}


def son_2():
    """Zincir kırılır: ortadaki halka çatlar, içinden altın ışık patlar; mürekkep kırıkları savrulur."""
    S = Sumi(W, H, 112)
    S.grad_wash(0, 900, 0.75, 0.85, seed=81, gran=0.6)
    chain(S, [(-60, 520), (300, 470), (620, 440)], 90, 18)
    chain(S, [(980, 440), (1300, 470), (1660, 520)], 90, 18)
    # kırık halka iki yarım
    S.stroke([(640, 470), (690, 380), (760, 360)], 22, load=1.0, dry=0.25, taper=(0.1, 0.6))
    S.stroke([(960, 410), (910, 500), (840, 520)], 22, load=1.0, dry=0.25, taper=(0.1, 0.6))
    # ışık patlaması
    S.erase(sun_glow(S, 800, 440, 160, col=(0, 0, 0), k=0.0), 0.0)
    g = sun_glow(S, 800, 440, 220, col=(1.0, 0.8, 0.4), k=1.2)
    S.erase(g, 0.9)
    rs = np.random.default_rng(82)
    for i in range(26):
        a = rs.uniform(0, math.tau)
        r0, r1 = rs.uniform(40, 90), rs.uniform(260, 620)
        m = S.stroke([(800 + math.cos(a) * r0, 440 + math.sin(a) * r0), (800 + math.cos(a) * r1, 440 + math.sin(a) * r1 * 0.8)], rs.uniform(4, 14), load=1.0, dry=0.6,
                     taper=(0.05, 0.95), ret=True)
        S.put(m, 'G', k=0.9)
    for i in range(30):
        a = rs.uniform(0, math.tau)
        d = rs.uniform(150, 600)
        x, y = 800 + math.cos(a) * d, 440 + math.sin(a) * d * 0.7
        S.stroke([(x, y), (x + math.cos(a) * 24, y + math.sin(a) * 18)], rs.uniform(6, 16), load=1.0, dry=0.3, taper=(0.2, 0.7))
    seal(S, 60, 790, 44, 8)
    return S, {'koyu': True}


def son_3():
    """Gün Ana köklerden yükselir: dikey gövde, ışıklı figür gövdeye sarılı yükselir, dallar altınla tutuşur."""
    S = Sumi(W, H, 113)
    S.grad_wash(0, 900, 0.3, 0.75, seed=91, gran=0.5)
    sun_glow(S, 800, 300, 360, col=(1.0, 0.72, 0.36), k=0.7)
    S.erase(sun_glow(S, 800, 300, 300, col=(0, 0, 0), k=0.0), 0.55)
    tree(S, 800, 960, 1000, spread=1.3, seed=92, load=1.0, gold_leaves=18, roots=False)
    # yükselen figür: altın
    figure_gun_ana(S, 800, 520, 150, layer_body='G', body_dens=0.8, halo=False, braids=True, braid_cols=BRAID_COLS)
    S.enso(800, 380, 190, 18, load=1.0, dry=0.4, layer='G', a0=-1.4, span=5.6)
    leaves_fall(S, 22, (200, 80, 1400, 820), 93, gold=0.8, k=0.85)
    seal(S, 1500, 60, 44, 9)
    return S, {'koyu': True}


def son_4():
    """Ve tan söktü: ufukta Ulu Kayın silüeti, devasa güneş diski doğar; gök al-safran yıkama; altın yapraklar."""
    S = Sumi(W, H, 114)
    S.grad_wash(0, 640, 0.0, 0.0)
    # gök: üstte soluk çivit, ufka doğru gül ve safran
    yy = np.arange(H, dtype=np.float32)[:, None] * np.ones((1, W), np.float32)
    t = np.clip(yy / 600.0, 0, 1)
    S.put(np.clip(1 - t * 1.6, 0, 1) * 0.35, 'C', col=INDIGO)
    S.put(np.exp(-((yy - 470) / 160) ** 2) * 0.7, 'C', col=ROSE)
    S.put(np.exp(-((yy - 560) / 90) ** 2) * 0.8, 'C', col=SAFFRON)
    # güneş: büyük disk, ufkun arkasından (kâğıt ışığı + altın enso)
    sun_glow(S, 800, 600, 420, col=(1.0, 0.62, 0.3), k=0.9)
    disk = S.ellipse_mask(800, 600, 230, 230)
    S.put(disk * 0.9, 'C', col=(0.98, 0.5, 0.2))
    S.enso(800, 600, 236, 16, load=1.0, dry=0.45, layer='G', a0=-3.1, span=3.3)
    # ufuk: koyu bozkır tepeleri
    mountains(S, [(0, 640), (220, 610), (420, 630), (640, 600), (800, 615), (980, 590), (1200, 625), (1400, 600), (1600, 630)], 900, dens=0.9, blur=3.0, seed=95)
    # Ulu Kayın silüeti tepede, güneşin önünde
    tree(S, 800, 612, 470, spread=1.25, seed=96, load=1.0, gold_leaves=26, roots=False)
    # kuşlar
    rs = np.random.default_rng(97)
    for i in range(9):
        x, y = rs.uniform(250, 1350), rs.uniform(120, 330)
        s = rs.uniform(10, 22)
        S.stroke([(x - s, y - s * 0.3), (x, y), (x + s, y - s * 0.35)], 3.5, load=0.9, dry=0.3, taper=(0.2, 0.6))
    leaves_fall(S, 26, (100, 250, 1500, 800), 98, gold=0.9, k=0.9)
    seal(S, 1500, 60, 44, 10)
    return S, {'koyu': False}


def son_5():
    """Dalda oturan Bengü, kısa saç; ardında güneş, öbür yanda soluk ay: gece de gelecek, sabah da."""
    S = Sumi(W, H, 115)
    S.put(np.ones((H, W), np.float32) * 0.15, 'C', col=SAFFRON)
    sun_glow(S, 1150, 380, 300, col=(1.0, 0.68, 0.32), k=0.8)
    S.put(S.ellipse_mask(1150, 380, 150, 150) * 0.8, 'C', col=(0.98, 0.55, 0.25))
    S.enso(1150, 380, 156, 10, load=0.9, dry=0.5, layer='G', a0=-2.0, span=5.5)
    # ay: sol üstte ince hilal
    S.enso(250, 150, 40, 9, load=0.6, dry=0.4, a0=1.2, span=2.6)
    # dal: soldan sağa kalın
    S.stroke([(-40, 640), (300, 600), (700, 585), (1000, 610), (1250, 680)], 48, load=1.0, dry=0.5, taper=(0.02, 0.9))
    S.stroke([(500, 595), (560, 520), (650, 470)], 16, load=1.0, dry=0.5, taper=(0.05, 0.9))
    rs = np.random.default_rng(116)
    for j in range(30):
        m = S.leaf(rs.uniform(300, 1300), rs.uniform(470, 660), rs.uniform(12, 26), rs.uniform(-math.pi, 0.3), ret=True)
        S.put(m, 'G' if rs.random() < 0.6 else 'D', k=0.9)
    figure_bengu(S, 780, 590, 120, pose='sit', load=1.0)
    leaves_fall(S, 14, (300, 650, 1500, 850), 117, gold=0.8, k=0.8)
    seal(S, 60, 790, 44, 11)
    return S, {'koyu': False}


PANELLER = {'giris_1': giris_1, 'giris_2': giris_2, 'giris_3': giris_3, 'giris_4': giris_4, 'giris_5': giris_5, 'giris_6': giris_6,
            'son_1': son_1, 'son_2': son_2, 'son_3': son_3, 'son_4': son_4, 'son_5': son_5}
TONE = {'giris_1': NIGHT, 'giris_3': NIGHT, 'giris_4': NIGHT, 'giris_6': NIGHT, 'son_1': NIGHT, 'son_2': NIGHT, 'son_3': NIGHT,
        'giris_2': DAWN, 'son_4': DAWN, 'son_5': DAWN}


def gorum_siluet():
    """Görüm silüeti (saydam RGBA): Gün Ana, ardında enso, başından beş örgü; gövde kor, örgüler / hale altın.
    Oyunda (Gorum.gd) altın ışımayla, kenardan dağılan mürekkep gibi belirir."""
    S = Sumi(640, 900, 120)
    figure_gun_ana(S, 320, 470, 175, body_dens=0.9, wind=0.25)
    d = np.clip(S.D, 0, 1)
    g = np.clip(S.G, 0, 1)
    # toplamalı çizilir (Gorum.gd): gövde sıcak kor ışığı, örgüler / hale açık altın; örgüler gövdeden sönük ki silüet okunsun
    from scipy import ndimage
    d = np.clip(ndimage.gaussian_filter(d, 1.2) * 1.1, 0, 1)
    g = g * 0.55
    a = np.clip(np.maximum(d * 0.85, g), 0, 1)
    ink = np.array([1.0, 0.62, 0.3], np.float32)
    gold = np.array([1.0, 0.86, 0.55], np.float32)
    rgb = (ink[None, None, :] * (d * (1 - g))[..., None] + gold[None, None, :] * g[..., None]) / np.maximum(a, 1e-4)[..., None]
    out = np.concatenate([np.clip(rgb, 0, 1), a[..., None]], -1)
    save_rgba_png(out, os.path.join(OUT, 'gun_ana_gorum.png'))
    print('görüm silüeti', out.shape)


def render(name):
    S, meta = PANELLER[name]()
    rgb = S.compose(tone=TONE.get(name))
    glow = S.glow(scale=0.5, rad=22.0)
    # yazı rengi: anlatının yazıldığı alt bant koyuysa kemik rengi, açıksa sumi mürekkebi (Sinema.gd)
    lum = rgb[int(H * 0.76):, int(W * 0.15):int(W * 0.85)] @ np.array([0.299, 0.587, 0.114], np.float32)
    meta['koyu'] = bool(lum.mean() < 0.5)
    return rgb, glow, meta


def main(args):
    os.makedirs(OUT, exist_ok=True)
    gd = os.path.join(OUT, '.gdignore')
    if '--gorum' in args:
        gorum_siluet()
        return
    names = [a for a in args if a in PANELLER] or list(PANELLER)
    prev = None
    if '--onizleme' in args:
        prev = args[args.index('--onizleme') + 1]
    mp = os.path.join(OUT, 'paneller.json')
    meta_all = json.load(open(mp, encoding='utf-8')) if os.path.exists(mp) else {}
    thumbs = []
    for n in names:
        rgb, glow, meta = render(n)
        save_rgb_jpg(rgb, os.path.join(OUT, n + '.jpg'), q=88)
        save_rgba_png(glow, os.path.join(OUT, n + '_isik.png'))
        meta_all[n] = meta
        print('panel', n, rgb.shape)
        if prev:
            g = glow[..., :3] * glow[..., 3:4]
            from scipy import ndimage
            gg = ndimage.zoom(g, (2, 2, 1), order=1)[:H, :W]
            thumbs.append(np.clip(rgb + gg * 0.6, 0, 1))
    with open(mp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(meta_all, f, ensure_ascii=False, indent=1, sort_keys=True)
    if prev and thumbs:
        from PIL import Image
        cols = 3
        tw, th = 640, 360
        rows = (len(thumbs) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * tw + (cols + 1) * 10, rows * th + (rows + 1) * 10), (20, 18, 24))
        for i, t in enumerate(thumbs):
            im = Image.fromarray((t * 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
            sheet.paste(im, (10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + 10)))
        sheet.save(prev)
        print('önizleme', prev)


if __name__ == '__main__':
    main(sys.argv[1:])
