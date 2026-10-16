"""Gulyabani (kimlik surale; Karakoncolos aynı çizimi soğuk tonla kullanır) — stil v2 "mürekkep-cel" (inkkit.py).
v1: creatures.draw_gul / GUL_ANIMS (aynı iskelet ve pozlar: kalça, kambur omurga, 19+19 bacak, 20+20 kol).

Kefenli, kambur, sıska ölü: soğuk mavi-gri deri gergin kaburgalara ve omur çıkıntılarına yapışık, karın içe çökük,
düğüm dizler, yere değen çok uzun kollar ve sarı tırnaklı uzun parmaklar; yırtık, toprak lekeli kefen sırttan
başlık gibi kafayı örter ve dizlere iner (uçları çözülmüş şeritler), altından yağlı kara saç sarkar. Oyuk göz
çukurlarında soluk sarı ışık, aralık çenede iğne dişler. Telegraf: hazırlıkta kollar havada, ağız açılır, gözler
alevlenir; yakalamada pençeler ileri fırlar (parmaklar açık) sonra kapanır.
Animasyon adları/kare sayıları/fps v1 ile aynı; v1 json'unda çapa yok (yakalama noktası kodda).
"""
import math

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_leg, fk_arm, lerp2, chain
from bengu_ink import along
from creatures import GUL_ANIMS

TEX = 4.0
CELL = (512, 480)        # dünya 128 x 120 (v1: 128 x 104; hazırlıkta kaldırılan kollar için üstte pay)
FEET = (200, 464)        # dünya (50, 116)

SKIN = Ink('#b4c0c6', '#5c6680', '#e8f0f0', '#343a52', name='ölü ten')
SKIN_B = Ink('#86909e', '#454c64', '#a8b2bc', '#262a3c', name='uzak ten')
SHROUD = Ink('#9c8f78', '#4e4448', '#cfc3a6', '#2c262c', name='kefen')
SHROUD_B = SHROUD.darker(0.72)
HAIR = Ink('#2a2834', '#14131a', '#545266', name='kara saç')
CLAW = Ink('#cdb67a', '#76603a', '#f4e6b0', name='sarı tırnak')
BONE = Ink('#d6ccb0', '#7e725e', '#fbf6e2', name='kemik')
GUM = (0.30, 0.08, 0.12)
EYE = (0.98, 1.0, 0.62)
EYE_GLOW = (0.85, 0.95, 0.30)


def ground(p):
    def depth(a):
        return 19.0 * math.cos(a[0]) + 19.0 * math.cos(a[0] - a[1])
    return -max(depth(p.get('lb', (0.35, 0.7))), depth(p.get('lf', (0.1, 0.6))))


def _leg(cv, base, a, z, near):
    k, f = fk_leg(base, a[0], a[1], 19.0, 19.0)
    m = SKIN if near else SKIN_B
    thigh = cv.limb([base, lerp2(base, k, 0.4), k], [3.4, 2.6, 2.0])
    knee = cv.ellipse(k, 2.3, 2.1)
    shin = cv.limb([k, lerp2(k, f, 0.25), lerp2(k, f, 0.85), f], [1.9, 1.8, 1.25, 1.2])
    # ayak: uzun tarak + kıvrık parmaklar
    toe = (f[0] + 4.6, f[1] - 0.2)
    foot = cv.blob([(f[0] - 2.0, f[1] - 1.2), (f[0] + 1.0, f[1] - 2.2), (toe[0], toe[1] - 1.0), (toe[0] + 0.6, toe[1] + 0.2, 0.0), (f[0] - 1.8, f[1] + 0.3, 0.0)])
    leg = ik.union(thigh, knee, shin, foot)
    det = [('ink', [along(base, k, 0.25, 1.0), along(base, k, 0.6, 0.6), along(base, k, 0.9, 1.2)], 1.0, (0.2, 0.6)),
           ('ink', [along(k, f, 0.15, -0.6), along(k, f, 0.5, -0.9), along(k, f, 0.8, -0.5)], 1.0, (0.3, 0.5)),    # kaval kemiği
           ('ink', [(k[0] - 1.2, k[1] - 1.0), (k[0] + 0.4, k[1] - 1.6), (k[0] + 1.6, k[1] - 0.6)], 1.1, (0.2, 0.2))]
    cv.shape(leg, m, z=z, sd=1.6, hi=0.3 if near else 0.0, details=det if near else det[:1], bounce=0.25 if near else 0.0)
    for j in range(3):
        b0 = (toe[0] - 1.0 + j * 0.4, toe[1] - 0.6 + (j - 1) * 0.6)
        tip = (b0[0] + 2.0, b0[1] + 0.9)
        cv.shape(cv.blob([(b0[0], b0[1] - 0.45), (tip[0], tip[1], 0.0), (b0[0], b0[1] + 0.45)]), CLAW if near else CLAW.darker(0.7), z=z + 0.2, sd=0.4, ol=0.6)
    return k, f


def _arm(cv, shp, a, z, near, grab, ph, lean):
    e, h = fk_arm(shp, a[0], a[1], 20.0, 20.0)
    m = SKIN if near else SKIN_B
    upper = cv.limb([shp, lerp2(shp, e, 0.35), e], [2.7, 2.2, 1.7])
    elbow = cv.ellipse(e, 1.9, 1.8)
    fore = cv.limb([e, lerp2(e, h, 0.3), h], [1.75, 1.6, 1.25])
    # el: uzun avuç
    ang = math.atan2(h[1] - e[1], h[0] - e[0])
    palm_c = (h[0] + math.cos(ang) * 1.8, h[1] + math.sin(ang) * 1.8)
    palm = cv.ellipse(palm_c, 2.6, 1.8, ang)
    arm = ik.union(upper, elbow, fore, palm)
    det = [('ink', [along(shp, e, 0.2, -1.5), along(shp, e, 0.6, -1.0)], 1.0, (0.3, 0.5)),
           ('ink', [along(e, h, 0.1, 0.9), along(e, h, 0.5, 0.7), along(e, h, 0.85, 0.5)], 0.9, (0.3, 0.5)),
           ('ink', [along(e, h, 0.25, -0.8), along(e, h, 0.7, -0.6)], 0.8, (0.3, 0.5))]
    cv.shape(arm, m, z=z, sd=1.5, hi=0.25 if near else 0.0, details=det if near else (), bounce=0.25 if near else 0.0)
    # parmaklar: dört uzun, eklemli; grab açıklığı
    for k in range(4):
        fa = ang + (k - 1.5) * (0.26 + 0.30 * grab)
        m1 = (palm_c[0] + math.cos(fa) * 4.6, palm_c[1] + math.sin(fa) * 4.6)
        fb = fa + (1.0 - 0.85 * grab) * 0.9
        m2 = (m1[0] + math.cos(fb) * 3.6, m1[1] + math.sin(fb) * 3.6)
        fc = fb + (1.0 - 0.8 * grab) * 0.6
        tip = (m2[0] + math.cos(fc) * 2.6, m2[1] + math.sin(fc) * 2.6)
        cv.shape(cv.limb([palm_c, m1, m2], [0.85, 0.65, 0.55]), m, z=z + 0.2 + k * 0.01, sd=0.5, ol=0.8)
        cv.shape(cv.blob([(m2[0] - math.sin(fc) * 0.55, m2[1] + math.cos(fc) * 0.55), (tip[0], tip[1], 0.0),
                          (m2[0] + math.sin(fc) * 0.55, m2[1] - math.cos(fc) * 0.55)]), CLAW if near else CLAW.darker(0.7),
                 z=z + 0.25 + k * 0.01, sd=0.4, ol=0.7)
    # başparmak
    ta = ang - 1.2 - 0.3 * grab
    t1 = (palm_c[0] + math.cos(ta) * 3.0, palm_c[1] + math.sin(ta) * 3.0)
    t2 = (t1[0] + math.cos(ta + 0.6) * 2.4, t1[1] + math.sin(ta + 0.6) * 2.4)
    cv.shape(cv.limb([palm_c, t1, t2], [0.9, 0.7, 0.45]), m, z=z + 0.15, sd=0.5, ol=0.8)
    if near:   # yenden sarkan kefen şeritleri
        for j in range(2):
            q = lerp2(shp, e, 0.35 + j * 0.35)
            st = chain(q, 4, 2.2, math.pi * 0.55 + math.sin(ph + j) * 0.2 - lean * 0.5, 0.08, ph + j, 0.3)
            cv.shape(ik.taper_path([cv.W(s) for s in st], cv.u(1.8 - j * 0.3), (0.05, 0.85)), SHROUD, z=z + 0.4, sd=0.6, ol=0.75)
    return e, h


def draw(cv, p):
    bob, lean = p.get('bob', 0.0), p.get('lean', 0.0)
    grab = p.get('grab', 0.0)
    ph = p.get('ph', 0.0)
    flare = p.get('flare', grab * 0.6)
    hip = (-2.0, ground(p))
    by = bob * 0.8
    mid = (hip[0] + 6 + lean * 10, hip[1] - 15 + lean * 2 + by * 0.5)
    sh = (hip[0] + 13 + lean * 20, hip[1] - 21 + lean * 6 + by)
    hd = (sh[0] + 7 + lean * 3, sh[1] + 4 + lean * 2 - p.get('hup', 0.0))

    # ---- arka kol + arka bacak
    _arm(cv, (sh[0] - 3, sh[1] + 1), p.get('ab', (0.3, 0.3)), -12, False, grab, ph, lean)
    _leg(cv, (hip[0] - 2.5, hip[1]), p.get('lb', (0.35, 0.7)), -8, False)

    # ---- arkada sarkan saç
    for k in range(8):
        st = chain((hd[0] - 3.0 + k * 0.45, hd[1] - 3.5), 7, 2.6 + (k % 3) * 0.3, math.pi * 0.62 + k * 0.05 - lean * 0.5, 0.04, ph + k * 0.8, 0.22)
        cv.shape(ik.taper_path([cv.W(q) for q in st], cv.u(1.6 + (k % 2) * 0.5), (0.05, 0.9)), HAIR, z=-4 + k * 0.01, sd=0.6, hi=0.0, ol=0.7)

    # ---- gövde: leğen + çökük karın + kaburga kafesi (tek kontur), omur çıkıntıları
    torso = ik.union(cv.capsule(hip, mid, 4.6, 6.6), cv.capsule(mid, sh, 7.4, 6.0),
                     cv.ellipse((hip[0] + 0.5, hip[1] - 0.5), 5.4, 4.2, 0.3))
    ribs = []
    ax = (sh[0] - mid[0], sh[1] - mid[1])
    al = math.hypot(*ax)
    ux, uy = ax[0] / al, ax[1] / al
    nx, ny = uy, -ux       # öne/aşağı (karın yanı)
    for i in range(5):
        t = 0.05 + i * 0.2
        c0 = (mid[0] + ax[0] * t - nx * 4.5, mid[1] + ax[1] * t - ny * 4.5)
        c1 = (c0[0] + nx * 4.0 - ux * 1.6, c0[1] + ny * 4.0 - uy * 1.6)
        c2 = (c0[0] + nx * 8.6 - ux * 2.2, c0[1] + ny * 8.6 - uy * 2.2)
        ribs.append(('stroke', [(c0[0] + 0.4, c0[1] - 0.6), (c1[0] + 0.4, c1[1] - 0.6), (c2[0] + 0.4, c2[1] - 0.6)], 1.6, SKIN.hi, (0.3, 0.6)))
        ribs.append(('ink', [c0, c1, c2], 1.25, (0.2, 0.7)))
    # çökük karın gölgesi + göbek çizgisi
    ribs.append(('deep', cv.wedge([lerp2(hip, mid, 0.2), lerp2(hip, mid, 0.6), lerp2(mid, sh, 0.1)], 2.0, 1.0)))
    ribs.append(('ink', [(hip[0] + 4.0, hip[1] - 3.0), (mid[0] + 4.0, mid[1] + 2.0)], 1.0, (0.3, 0.5)))
    cv.shape(torso, SKIN, z=0, sd=3.6, hi=0.4, details=ribs, bounce=0.35, hatch=0.3)
    for k in range(3):
        q = lerp2(hip, sh, 0.2 + k * 0.17)
        bump = (q[0] - 4.2 - k * 0.5, q[1] - 5.4 - k * 0.5)
        cv.shape(cv.ellipse(bump, 1.3, 1.0, 0.6), BONE, z=0.5, sd=0.5, hi=0.25, ol=0.7)

    # ---- kefen: sırttan dizlere, yırtık etek + çözülmüş şeritler
    hx0, hy0 = hip
    sw = math.sin(ph) * 0.6
    shroud = cv.blob([(sh[0] + 3, sh[1] - 5.5), (mid[0] - 1.5, mid[1] - 8.6), (hx0 - 6.5, hy0 - 6.5), (hx0 - 10.0 + sw, hy0 + 13, 0.0),
                      (hx0 - 6.5 + sw, hy0 + 8.5), (hx0 - 4.5 + sw, hy0 + 16.5, 0.0), (hx0 - 1.2, hy0 + 8.0), (hx0 + 2.4 + sw * 0.5, hy0 + 14.5, 0.0),
                      (hx0 + 4.2, hy0 + 5.0), (mid[0] + 0.5, mid[1] + 2.0), (sh[0] - 1.5, sh[1] + 2.0)])
    sdet = []
    for (a_, b_) in (((sh[0] - 2, sh[1] - 4.0), (hx0 - 7.5 + sw, hy0 + 10.5)), ((mid[0] - 1, mid[1] - 5.6), (hx0 - 3.0 + sw, hy0 + 12.5)),
                     ((mid[0] + 1.5, mid[1] - 1.0), (hx0 + 1.5, hy0 + 10.0))):
        m_ = lerp2(a_, b_, 0.5)
        sdet += cv.fold([a_, (m_[0] - 0.8, m_[1]), b_], 1.0, 1.3, 1, (0.5, 0.2))
    # toprak lekeleri
    sdet.append(('col', cv.blob([(hx0 - 6.0, hy0 + 4.0), (hx0 - 3.0, hy0 + 3.0), (hx0 - 2.4, hy0 + 7.4), (hx0 - 5.6, hy0 + 8.4)]), (0.42, 0.36, 0.30)))
    cv.shape(shroud, SHROUD, z=6, sd=3.0, hi=0.3, details=sdet, hatch=0.4, bounce=0.3, cast=0.8)
    for j in range(4):
        q = (hx0 - 8.5 + j * 4.0, hy0 + 10 + (j % 2) * 3.5)
        st = chain(q, 4, 2.4, math.pi * 0.5 + 0.2 + math.sin(ph + j * 1.7) * 0.25 - lean * 0.6, 0.0, ph + j, 0.3)
        cv.shape(ik.taper_path([cv.W(s) for s in st], cv.u(1.6), (0.05, 0.85)), SHROUD_B, z=5.9, sd=0.5, ol=0.7)

    # ---- boyun + baş: öne sarkık iri kafatası, çökük yanak, oyuk gözler, açılan çene
    hx, hy = hd
    K = 1.2
    neck = cv.limb([(sh[0] + 1, sh[1] - 1), lerp2((sh[0] + 1, sh[1] - 1), hd, 0.5), hd], [2.6, 2.0, 2.4])
    cv.shape(neck, SKIN, z=8, sd=1.2, details=[('ink', [lerp2((sh[0] + 1, sh[1] - 1), hd, 0.2), lerp2((sh[0] + 1, sh[1] - 1), hd, 0.8)], 1.0, (0.3, 0.3))])
    jaw = 0.8 + grab * 3.2 + p.get('jaw', 0.0) * 3.0
    skull = cv.blob([(hx - 4.8, hy - 2.0), (hx - 2.6, hy - 5.8), (hx + 1.6, hy - 6.4), (hx + 5.0, hy - 4.4), (hx + 6.6, hy - 1.6),
                     (hx + 7.2, hy + 1.2), (hx + 6.6, hy + 2.6), (hx + 2.0, hy + 3.0), (hx - 1.8, hy + 3.6), (hx - 4.4, hy + 1.6)])
    hdet = [('deep', cv.blob([(hx + 0.4, hy + 0.4), (hx + 3.0, hy + 0.0), (hx + 4.4, hy + 2.0), (hx + 1.4, hy + 3.0)])),   # çökük yanak
            ('ink', [(hx + 0.2, hy + 0.4), (hx + 2.4, hy + 1.6), (hx + 4.6, hy + 1.8)], 1.1, (0.2, 0.6)),
            ('deep', cv.blob([(hx + 6.2, hy - 0.4), (hx + 7.3, hy + 0.6), (hx + 6.4, hy + 1.2, 0.0)]))]
    cv.shape(skull, SKIN, z=12, sd=1.5, hi=0.4, details=hdet, bounce=0.4, cast=0.6, soft=0.25)
    # yüzün önüne düşen yağlı saç tutamları (gözleri kapatmaz)
    for k, (dx, ln) in enumerate(((-0.6, 7), (0.6, 6), (6.4, 4))):
        st = chain((hx + dx, hy - 4.4), ln, 1.5, math.pi * 0.5 + 0.04 - lean * 0.3 + math.sin(ph + k * 2) * 0.06, 0.0, ph + k, 0.1)
        cv.shape(ik.taper_path([cv.W(q) for q in st], cv.u(0.9 + 0.25 * (k % 2)), (0.05, 0.9)), HAIR, z=13.6 + k * 0.01, sd=0.4, ol=0.6, hi=0.0)
    # ağız (kara boşluk) + iğne dişler + alt çene
    mouth = cv.blob([(hx + 0.6, hy + 2.2), (hx + 6.8, hy + 2.6), (hx + 6.0, hy + 3.8 + jaw), (hx + 0.8, hy + 3.6 + jaw * 0.7)])
    cv.fill(mouth, GUM, z=12.4)
    cv.fill(cv.blob([(hx + 1.6, hy + 2.8), (hx + 5.6, hy + 3.0), (hx + 5.0, hy + 3.2 + jaw * 0.8), (hx + 1.8, hy + 3.2 + jaw * 0.5)]), INK, z=12.45)
    for i in range(5):
        x = hx + 1.4 + i * 1.15
        cv.fill(cv.blob([(x - 0.35, hy + 2.3), (x + 0.35, hy + 2.3), (x + 0.05, hy + 3.6 + (0.4 if i % 2 else 0.0), 0.0)]), BONE.base, z=12.5)
        if jaw > 1.4:
            cv.fill(cv.blob([(x - 0.3, hy + 3.4 + jaw * 0.75), (x + 0.3, hy + 3.4 + jaw * 0.78), (x, hy + 2.4 + jaw * 0.7, 0.0)]), BONE.base, z=12.5)
    jw = cv.blob([(hx - 1.0, hy + 3.2 + jaw * 0.5), (hx + 5.8, hy + 3.6 + jaw), (hx + 5.4, hy + 5.0 + jaw), (hx + 0.6, hy + 5.0 + jaw * 0.7), (hx - 1.2, hy + 4.2 + jaw * 0.5)])
    cv.shape(jw, SKIN_B, z=12.6, sd=0.9, hi=0.2)
    # göz çukurları + soluk ışık (flare ile büyür)
    for (ex, ey, rx, ry) in ((hx + 1.8, hy - 1.6, 1.9, 1.7), (hx + 5.0, hy - 1.5, 1.3, 1.6)):
        cv.fill(cv.ellipse((ex, ey), rx, ry), INK, z=13)
    er = 0.55 + 0.3 * flare
    cv.fill(cv.ellipse((hx + 2.0, hy - 1.5), er * 1.2, er), EYE, z=13.2, glow=EYE_GLOW)
    cv.fill(cv.ellipse((hx + 5.0, hy - 1.4), er * 0.7, er * 0.9), EYE, z=13.2, glow=EYE_GLOW)
    if flare > 0.3:
        cv.fill(cv.ellipse((hx + 3.4, hy - 1.5), 4.6 * flare, 3.0 * flare), (0, 0, 0), z=-99, glow=(0.3 * flare, 0.34 * flare, 0.1 * flare), alpha=0.0)
    # kefen başlığı: kafayı arkadan örter, yüzü çerçeveler; altından saç sarkar
    for k, dx in enumerate((-4.6, -3.2, -1.6, -0.2)):
        st = chain((hx + dx, hy - 3.8), 6, 2.6, math.pi * 0.5 + 0.08 + math.sin(ph + k) * 0.1 - lean * 0.4, 0.03, ph + k, 0.15)
        cv.shape(ik.taper_path([cv.W(q) for q in st], cv.u(1.5), (0.05, 0.85)), HAIR, z=30 + k * 0.1, sd=0.5, ol=0.7, hi=0.0,
                 details=[('stroke', [st[1], st[3]], 0.8, HAIR.hi, (0.3, 0.6))])
    hood = cv.blob([(sh[0] + 3, sh[1] - 5.5), (hx - 6.8, hy - 3), (hx - 4.2, hy - 8.8), (hx + 1.5, hy - 9.8), (hx + 6.2, hy - 7.2),
                    (hx + 7.6, hy - 4.0, 0.0), (hx + 4.5, hy - 4.8), (hx + 1.0, hy - 5.4), (hx - 2.2, hy - 3.0), (hx - 3.5, hy + 2.5),
                    (hx - 5.5, hy + 4.5), (sh[0] - 1, sh[1] + 2)])
    hdt = cv.fold([(hx - 4.0, hy - 6.0), (hx - 4.6, hy - 1.0), (hx - 5.2, hy + 3.0)], 0.9, 1.2, 1)
    hdt += cv.fold([(hx + 1.0, hy - 8.4), (hx + 3.2, hy - 6.6), (hx + 5.6, hy - 5.6)], 0.5, 1.0, -1)
    cv.shape(hood, SHROUD, z=36, sd=2.6, hi=0.35, details=hdt, hatch=0.3, cast=0.8, bounce=0.3)

    # ---- ön bacak + ön kol
    _leg(cv, (hip[0] + 2.5, hip[1]), p.get('lf', (0.1, 0.6)), 8, True)
    _arm(cv, (sh[0] + 2, sh[1] + 2), p.get('af', (0.2, 0.3)), 40, True, grab, ph, lean)
    return {}


ANIMS = {k: (v[0], v[1], k in ('idle', 'walk'), True) for k, v in GUL_ANIMS.items()}
SHADE = dict(outer=0.5, rim=0.6, rim_col=(0.7, 0.85, 1.0), rim_dir=(0.55, -0.85), rim_w=1.4, form=(7.0, (0.74, 0.72, 0.88)))


def render_frame(anim, i, ss=3):
    n, fn, loop, arm = ANIMS[anim]
    p = fn(i / n)
    cv = ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
