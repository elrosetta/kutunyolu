"""Gulyabani (kimlik surale; Karakoncolos aynı çizimi soğuk tonla kullanır) — stil v2 "mürekkep-cel" (inkkit.py).
v1: creatures.draw_gul / GUL_ANIMS (aynı iskelet ölçüleri: kalça, kambur omurga, 19+19 bacak, 20+20 kol).

Kefenli, kambur, sıska ölü: soğuk mavi-gri deri gergin kaburgalara ve omur çıkıntılarına yapışık, karın içe çökük,
düğüm dizler, yere değen çok uzun kollar ve sarı tırnaklı uzun parmaklar; yırtık, toprak lekeli kefen sırttan
başlık gibi kafayı örter ve dizlere iner (uçları çözülmüş şeritler), altından yağlı kara saç sarkar. Oyuk göz
çukurlarında soluk sarı ışık, aralık çenede iğne dişler.

v29 tam gövde animasyonu (docs/TASARIM.md "v29: yer yaratıklarının tam gövde animasyonu"): iskelet artık AYAK ve EL
HEDEFLİ — iki ayağın yerdeki / havadaki yeri ve iki elin figür çerçevesindeki yeri yazılır, bacaklar (dizler önde) ve
kollar (dirsekler geride) ik2 ile çözülür. Gövde kalça çevresinde eğilir (pitch: + öne kapanma), kamburlaşır (arch),
omuzlar soluk alır (br); baş boyun dibinde döner (hr) ve önden gider (hd). Saç, kefen eteği ve yen şeritleri yerçekimine
göre sarkar, 'drag' ile geride sürüklenir / 'hairup' ile kabarır (ikincil hareket, 'ph' dalgası). Bütün figür gövde
merkezi çevresinde devrilir (roll), yatayda daralır (sx: dönüş), ayak noktasında ezilir-esner (sq).

Hücre 512x480 doku pikseli = dünya 128x120 (texel 4), ayak (50, 116). Satırlar (SEQS) ve yapay zekâ eşlemesi (DURUM):
grabber (Gulyabani) + mimic (Karakoncolos: kar yığını pusucu, kartopu).
"""
import math

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_arm, lerp2, chain
from bengu_ink import along
import yaratik_govde as yg
import yaratik_ink_kit as yk
from yaratik_govde import Seq, wave

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
SNOW = Ink('#eef3f8', '#93a2bc', '#ffffff', name='kar')
GUM = (0.30, 0.08, 0.12)
EYE = (0.98, 1.0, 0.62)
EYE_GLOW = (0.85, 0.95, 0.30)

L_LEG = 19.0
L_ARM = 20.0
H0 = -35.70                  # dinlenme kalça yüksekliği (v1 bacak açılarıyla yer)
HIP0 = (-2.0, H0)
C0 = (8.0, -40.0)            # figür dönüşüm merkezi (gövde ortası)


def _rest_hands():
    """v1 bekleme pozunun el noktaları (kollar düz, yere değen pençeler) — dinlenme görünüşü aynı kalsın."""
    lean = 0.12
    sh = (HIP0[0] + 13 + lean * 20, HIP0[1] - 21 + lean * 6)
    _e, hb = fk_arm((sh[0] - 3, sh[1] + 1), 0.32, 0.3, L_ARM, L_ARM)
    _e, hf = fk_arm((sh[0] + 2, sh[1] + 2), 0.18, 0.32, L_ARM, L_ARM)
    return (round(hf[0], 2), round(hf[1], 2)), (round(hb[0], 2), round(hb[1], 2))


AF0, AB0 = _rest_hands()

# dinlenme pozu: lf/lb yakın/uzak ayak (x, yerden yükseklik, parmak açısı), af/ab yakın/uzak el (x, y figür çerçevesi)
REST = dict(x=0.0, y=0.0, roll=0.0, sx=1.0, sq=0.0, hx=0.0, hy=0.0, bob=0.0, pitch=0.0, lean=0.12, arch=0.0, br=0.0,
            lf=(-6.7, 0.0, 0.0), lb=(-4.5, 0.0, 0.0), af=AF0, ab=AB0, ebf=1.0, ebb=1.0, wf=0.0, wb=0.0,
            gf=0.15, gb=0.15, hd=(0.0, 0.0), hr=0.0, jaw=0.15, flare=0.09, eyes=1.0, blink=0.0,
            drag=0.0, hairup=0.0, ph=0.0, ball=0.0)


def _foot(cv, f, toe_a, m, z, near):
    ca, sa = math.cos(toe_a), math.sin(toe_a)

    def R(x, y, *r):
        dx, dy = x - f[0], y - f[1]
        return (f[0] + dx * ca - dy * sa, f[1] + dx * sa + dy * ca) + r
    toe = R(f[0] + 4.6, f[1] - 0.2)
    foot = cv.blob([R(f[0] - 2.0, f[1] - 1.2), R(f[0] + 1.0, f[1] - 2.2), R(f[0] + 4.6, f[1] - 1.2), R(f[0] + 5.2, f[1] + 0.0, 0.0),
                    R(f[0] - 1.8, f[1] + 0.3, 0.0)])
    claws = []
    for j in range(3):
        b0 = R(f[0] + 3.6 + j * 0.4, f[1] - 0.8 + (j - 1) * 0.6)
        tip = R(f[0] + 5.6 + j * 0.4, f[1] + 0.1 + (j - 1) * 0.6)
        n = (-(tip[1] - b0[1]) * 0.22, (tip[0] - b0[0]) * 0.22)
        claws.append([(b0[0] - n[0], b0[1] - n[1]), (tip[0], tip[1], 0.0), (b0[0] + n[0], b0[1] + n[1])])
    return foot, claws, toe


def _leg(cv, base, f, toe_a, z, near):
    """Ayak hedefli bacak: kalça -> diz (önde) -> ayak bileği; erişilemeyen hedef kırpılır."""
    k, f = yg.ik2(base, f, L_LEG, L_LEG, -1)
    m = SKIN if near else SKIN_B
    thigh = cv.limb([base, lerp2(base, k, 0.4), k], [3.4, 2.6, 2.0])
    knee = cv.ellipse(k, 2.3, 2.1)
    shin = cv.limb([k, lerp2(k, f, 0.25), lerp2(k, f, 0.85), f], [1.9, 1.8, 1.25, 1.2])
    foot, claws, _toe = _foot(cv, f, toe_a, m, z, near)
    leg = ik.union(thigh, knee, shin, foot)
    det = [('ink', [along(base, k, 0.25, 1.0), along(base, k, 0.6, 0.6), along(base, k, 0.9, 1.2)], 1.0, (0.2, 0.6)),
           ('ink', [along(k, f, 0.15, -0.6), along(k, f, 0.5, -0.9), along(k, f, 0.8, -0.5)], 1.0, (0.3, 0.5)),    # kaval kemiği
           ('ink', [(k[0] - 1.2, k[1] - 1.0), (k[0] + 0.4, k[1] - 1.6), (k[0] + 1.6, k[1] - 0.6)], 1.1, (0.2, 0.2))]
    cv.shape(leg, m, z=z, sd=1.6, hi=0.3 if near else 0.0, details=det if near else det[:1], bounce=0.25 if near else 0.0)
    for c in claws:
        cv.shape(cv.blob(c), CLAW if near else CLAW.darker(0.7), z=z + 0.2, sd=0.4, ol=0.6)
    return k, f


def _arm(cv, shp, tgt, bend, wrist, z, near, grab, ph, drag, ball=0.0):
    """El hedefli kol: omuz -> dirsek -> bilek (ik2); avuç ön kol doğrultusunda (+ bilek açısı), dört uzun parmak."""
    e, h = yg.ik2(shp, tgt, L_ARM, L_ARM, 1 if bend >= 0 else -1)
    m = SKIN if near else SKIN_B
    upper = cv.limb([shp, lerp2(shp, e, 0.35), e], [2.7, 2.2, 1.7])
    elbow = cv.ellipse(e, 1.9, 1.8)
    fore = cv.limb([e, lerp2(e, h, 0.3), h], [1.75, 1.6, 1.25])
    # el: uzun avuç
    ang = math.atan2(h[1] - e[1], h[0] - e[0]) + wrist
    palm_c = (h[0] + math.cos(ang) * 1.8, h[1] + math.sin(ang) * 1.8)
    palm = cv.ellipse(palm_c, 2.6, 1.8, ang)
    arm = ik.union(upper, elbow, fore, palm)
    det = [('ink', [along(shp, e, 0.2, -1.5), along(shp, e, 0.6, -1.0)], 1.0, (0.3, 0.5)),
           ('ink', [along(e, h, 0.1, 0.9), along(e, h, 0.5, 0.7), along(e, h, 0.85, 0.5)], 0.9, (0.3, 0.5)),
           ('ink', [along(e, h, 0.25, -0.8), along(e, h, 0.7, -0.6)], 0.8, (0.3, 0.5))]
    cv.shape(arm, m, z=z, sd=1.5, hi=0.25 if near else 0.0, details=det if near else (), bounce=0.25 if near else 0.0)
    if ball > 0.02:   # kartopu (Karakoncolos): avuçta, parmakların arasında
        bc = (palm_c[0] + math.cos(ang) * 3.4, palm_c[1] + math.sin(ang) * 3.4)
        cv.shape(cv.ellipse(bc, 3.0 * ball, 2.7 * ball, 0.3), SNOW, z=z + 0.1, sd=0.8, hi=0.4, ol=0.8,
                 details=[('ink', [(bc[0] - 1.2, bc[1] + 0.6), (bc[0] + 0.2, bc[1] + 1.2), (bc[0] + 1.4, bc[1] + 0.4)], 0.7, (0.3, 0.3))])
    # parmaklar: dört uzun, eklemli; grab açıklığı (0 kıvrık, 1 açık / gergin)
    tip0 = palm_c
    for k in range(4):
        fa = ang + (k - 1.5) * (0.26 + 0.30 * grab)
        m1 = (palm_c[0] + math.cos(fa) * 4.6, palm_c[1] + math.sin(fa) * 4.6)
        fb = fa + (1.0 - 0.85 * grab) * 0.9
        m2 = (m1[0] + math.cos(fb) * 3.6, m1[1] + math.sin(fb) * 3.6)
        fc = fb + (1.0 - 0.8 * grab) * 0.6
        tip = (m2[0] + math.cos(fc) * 2.6, m2[1] + math.sin(fc) * 2.6)
        if k == 2:
            tip0 = tip
        cv.shape(cv.limb([palm_c, m1, m2], [0.85, 0.65, 0.55]), m, z=z + 0.2 + k * 0.01, sd=0.5, ol=0.8)
        cv.shape(cv.blob([(m2[0] - math.sin(fc) * 0.55, m2[1] + math.cos(fc) * 0.55), (tip[0], tip[1], 0.0),
                          (m2[0] + math.sin(fc) * 0.55, m2[1] - math.cos(fc) * 0.55)]), CLAW if near else CLAW.darker(0.7),
                 z=z + 0.25 + k * 0.01, sd=0.4, ol=0.7)
    # başparmak
    ta = ang - 1.2 - 0.3 * grab
    t1 = (palm_c[0] + math.cos(ta) * 3.0, palm_c[1] + math.sin(ta) * 3.0)
    t2 = (t1[0] + math.cos(ta + 0.6) * 2.4, t1[1] + math.sin(ta + 0.6) * 2.4)
    cv.shape(cv.limb([palm_c, t1, t2], [0.9, 0.7, 0.45]), m, z=z + 0.15, sd=0.5, ol=0.8)
    if near:   # yenden sarkan kefen şeritleri (yerçekimi + sürüklenme)
        for j in range(2):
            q = lerp2(shp, e, 0.35 + j * 0.35)
            st = chain(q, 4, 2.2, math.pi * 0.55 + math.sin(ph + j) * 0.2 - 0.06 + drag * 0.8, 0.08, ph + j, 0.3)
            cv.shape(ik.taper_path([cv.W(s) for s in st], cv.u(1.8 - j * 0.3), (0.05, 0.85)), SHROUD, z=z + 0.4, sd=0.6, ol=0.75)
    return e, h, tip0, palm_c


def draw(cv, p):
    yg.bake_xf(cv)
    q = dict(REST)
    q.update(p)
    p = q
    lean = p['lean']
    ph = p['ph']
    drag = p['drag']
    hup = p['hairup']
    flare = p['flare']
    sq = p['sq']
    sqx, sqy = 1.0 + 0.06 * sq, 1.0 - 0.08 * sq
    # ---- bütün figür: öteleme + devrilme + yatay daralma (dönüş), ayak noktasında ezilme
    yg.xf_push(cv, C0, p['roll'], p['x'], p['y'], p['sx'], 1.0)
    cv.push(lambda q_: (q_[0] * sqx, q_[1] * sqy))

    def F(t):
        """dünya ayak hedefi (x, yükseklik) -> figür çerçevesi (dönüşümün tersi; roll = 0 iken aynen kalır)"""
        w = (t[0] - p['x'], -t[1] - p['y'])
        w = yg.rot_about(w, C0, -p['roll'])
        w = (C0[0] + (w[0] - C0[0]) / max(0.05, abs(p['sx'])), w[1])
        return (w[0] / sqx, w[1] / sqy)

    gy = (-0.4 - p['y']) / sqy      # figür çerçevesinde yer çizgisi (devrilme yok sayılır): saç / kefen yere yığılır

    def G(pts):
        return [(x_, min(y_, gy)) + tuple(r_) for (x_, y_, *r_) in pts]

    # ---- iskelet: kalça, bel, omuz (pitch: kalça çevresinde öne kapanma; arch: kambur), baş
    hip = (HIP0[0] + p['hx'], HIP0[1] + p['hy'])
    by = p['bob'] * 0.8
    arch = p['arch']
    mid = (hip[0] + 6 + lean * 10 - arch * 0.8, hip[1] - 15 + lean * 2 + by * 0.5 - arch * 1.2)
    sh = (hip[0] + 13 + lean * 20, hip[1] - 21 + lean * 6 + by)
    mid = yg.rot_about(mid, hip, p['pitch'])
    sh = yg.rot_about(sh, hip, p['pitch'])
    br = p['br']
    sh = (sh[0], sh[1] - br * 0.6)
    hoff = yg.rot((7 + lean * 3, 4 + lean * 2), p['pitch'] * 0.6)
    hd = (sh[0] + hoff[0] + p['hd'][0], sh[1] + hoff[1] + p['hd'][1])
    nb = (sh[0] + 1, sh[1] - 1)
    hr = p['hr']

    def R(pt):   # baş yereli -> figür (boyun dibinde dönüş)
        return yg.rot_about(pt, nb, hr)

    # ---- arka kol + arka bacak
    _arm(cv, (sh[0] - 3, sh[1] + 1), p['ab'][:2], p['ebb'], p['wb'], -12, False, p['gb'], ph, drag)
    _leg(cv, (hip[0] - 2.5, hip[1]), F(p['lb']), p['lb'][2], -8, False)

    # ---- arkada sarkan saç (kökler başla döner; tutamlar yerçekimiyle sarkar, drag ile geride, hairup ile kabarır)
    hx, hy = hd
    for k in range(8):
        root = R((hx - 3.0 + k * 0.45, hy - 3.5))
        a0 = math.pi * 0.62 + k * 0.05 - 0.06 + drag + hup * (0.55 + k * 0.09)
        st = G(chain(root, 7, (2.6 + (k % 3) * 0.3) * (1.0 - 0.15 * hup), a0, 0.04 - hup * 0.05, ph + k * 0.8, 0.22 + hup * 0.15))
        cv.shape(ik.taper_path([cv.W(q_) for q_ in st], cv.u(1.6 + (k % 2) * 0.5), (0.05, 0.9)), HAIR, z=-4 + k * 0.01, sd=0.6, hi=0.0, ol=0.7)

    # ---- gövde: leğen + çökük karın + kaburga kafesi (tek kontur), omur çıkıntıları
    torso = ik.union(cv.capsule(hip, mid, 4.6, 6.6 + br * 0.3), cv.capsule(mid, sh, 7.4 + br * 0.5, 6.0),
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
        c2 = (c0[0] + nx * (8.6 + br * 0.4) - ux * 2.2, c0[1] + ny * (8.6 + br * 0.4) - uy * 2.2)
        ribs.append(('stroke', [(c0[0] + 0.4, c0[1] - 0.6), (c1[0] + 0.4, c1[1] - 0.6), (c2[0] + 0.4, c2[1] - 0.6)], 1.6, SKIN.hi, (0.3, 0.6)))
        ribs.append(('ink', [c0, c1, c2], 1.25, (0.2, 0.7)))
    # çökük karın gölgesi + göbek çizgisi
    ribs.append(('deep', cv.wedge([lerp2(hip, mid, 0.2), lerp2(hip, mid, 0.6), lerp2(mid, sh, 0.1)], 2.0, 1.0)))
    bx_ = yg.rot((4.0, -3.0), p['pitch'] * 0.5)
    ribs.append(('ink', [(hip[0] + bx_[0], hip[1] + bx_[1]), (mid[0] + 4.0, mid[1] + 2.0)], 1.0, (0.3, 0.5)))
    cv.shape(torso, SKIN, z=0, sd=3.6, hi=0.4, details=ribs, bounce=0.35, hatch=0.3)
    for k in range(3):
        qq = lerp2(hip, sh, 0.2 + k * 0.17)
        off = yg.rot((-4.2 - k * 0.5, -5.4 - k * 0.5 - arch * 0.5), p['pitch'] * 0.7)
        cv.shape(cv.ellipse((qq[0] + off[0], qq[1] + off[1]), 1.3, 1.0, 0.6 + p['pitch']), BONE, z=0.5, sd=0.5, hi=0.25, ol=0.7)

    # ---- kefen: sırttan dizlere, yırtık etek + çözülmüş şeritler (etek kalçaya bağlı; drag ile geride savrulur)
    hx0, hy0 = hip
    sw = math.sin(ph) * 0.6
    dgx, dgy = -drag * 5.0, -abs(drag) * 2.0
    back = yg.rot((-1.5, -8.6), p['pitch'] * 0.5)
    shroud = cv.blob(G([(sh[0] + 3, sh[1] - 5.5), (mid[0] + back[0], mid[1] + back[1]), (hx0 - 6.5, hy0 - 6.5),
                      (hx0 - 10.0 + sw + dgx * 1.3, hy0 + 13 + dgy * 1.3, 0.0),
                      (hx0 - 6.5 + sw + dgx * 0.8, hy0 + 8.5 + dgy * 0.8), (hx0 - 4.5 + sw + dgx, hy0 + 16.5 + dgy, 0.0),
                      (hx0 - 1.2 + dgx * 0.5, hy0 + 8.0), (hx0 + 2.4 + sw * 0.5 + dgx * 0.8, hy0 + 14.5 + dgy * 0.8, 0.0),
                      (hx0 + 4.2, hy0 + 5.0), (mid[0] + 0.5, mid[1] + 2.0), (sh[0] - 1.5, sh[1] + 2.0)]))
    sdet = []
    for (a_, b_) in (((sh[0] - 2, sh[1] - 4.0), (hx0 - 7.5 + sw + dgx, hy0 + 10.5 + dgy)),
                     ((mid[0] - 1, mid[1] - 5.6), (hx0 - 3.0 + sw + dgx, hy0 + 12.5 + dgy)),
                     ((mid[0] + 1.5, mid[1] - 1.0), (hx0 + 1.5 + dgx * 0.6, hy0 + 10.0))):
        m_ = lerp2(a_, b_, 0.5)
        sdet += cv.fold([a_, (m_[0] - 0.8, m_[1]), b_], 1.0, 1.3, 1, (0.5, 0.2))
    # toprak lekeleri
    sdet.append(('col', cv.blob([(hx0 - 6.0, hy0 + 4.0), (hx0 - 3.0, hy0 + 3.0), (hx0 - 2.4, hy0 + 7.4), (hx0 - 5.6, hy0 + 8.4)]), (0.42, 0.36, 0.30)))
    cv.shape(shroud, SHROUD, z=6, sd=3.0, hi=0.3, details=sdet, hatch=0.4, bounce=0.3, cast=0.8)
    for j in range(4):
        qq = (hx0 - 8.5 + j * 4.0 + dgx * 0.9, hy0 + 10 + (j % 2) * 3.5 + dgy * 0.9)
        st = G(chain(qq, 4, 2.4, math.pi * 0.5 + 0.2 + math.sin(ph + j * 1.7) * 0.25 - 0.07 + drag * 1.1, 0.0, ph + j, 0.3))
        cv.shape(ik.taper_path([cv.W(s) for s in st], cv.u(1.6), (0.05, 0.85)), SHROUD_B, z=5.9, sd=0.5, ol=0.7)

    # ---- boyun + baş: öne sarkık iri kafatası, çökük yanak, oyuk gözler, açılan çene (baş grubu boyun dibinde döner)
    neck_a = (sh[0] + 1, sh[1] - 1)
    hdw = R(hd)
    neck = cv.limb([neck_a, lerp2(neck_a, hdw, 0.5), hdw], [2.6, 2.0, 2.4])
    cv.shape(neck, SKIN, z=8, sd=1.2, details=[('ink', [lerp2(neck_a, hdw, 0.2), lerp2(neck_a, hdw, 0.8)], 1.0, (0.3, 0.3))])
    yg.xf_push(cv, nb, hr)
    jaw = 0.8 + p['jaw'] * 3.2
    skull = cv.blob([(hx - 4.8, hy - 2.0), (hx - 2.6, hy - 5.8), (hx + 1.6, hy - 6.4), (hx + 5.0, hy - 4.4), (hx + 6.6, hy - 1.6),
                     (hx + 7.2, hy + 1.2), (hx + 6.6, hy + 2.6), (hx + 2.0, hy + 3.0), (hx - 1.8, hy + 3.6), (hx - 4.4, hy + 1.6)])
    hdet = [('deep', cv.blob([(hx + 0.4, hy + 0.4), (hx + 3.0, hy + 0.0), (hx + 4.4, hy + 2.0), (hx + 1.4, hy + 3.0)])),   # çökük yanak
            ('ink', [(hx + 0.2, hy + 0.4), (hx + 2.4, hy + 1.6), (hx + 4.6, hy + 1.8)], 1.1, (0.2, 0.6)),
            ('deep', cv.blob([(hx + 6.2, hy - 0.4), (hx + 7.3, hy + 0.6), (hx + 6.4, hy + 1.2, 0.0)]))]
    if p['jaw'] > 0.6:   # çığlık: yanakta gerilme çizgisi
        hdet.append(('ink', [(hx + 6.0, hy + 1.6), (hx + 5.0, hy + 3.4), (hx + 4.6, hy + 4.4)], 0.9, (0.3, 0.5)))
    cv.shape(skull, SKIN, z=12, sd=1.5, hi=0.4, details=hdet, bounce=0.4, cast=0.6, soft=0.25)
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
    mouth_pt = yg.world(cv, (hx + 6.4, hy + 3.4 + jaw * 0.6))
    # göz çukurları + soluk ışık (flare ile büyür, blink ile kısılır, eyes ile söner)
    for (ex, ey, rx, ry) in ((hx + 1.8, hy - 1.6, 1.9, 1.7), (hx + 5.0, hy - 1.5, 1.3, 1.6)):
        cv.fill(cv.ellipse((ex, ey), rx, ry), INK, z=13)
    eo = p['eyes'] * (1.0 - 0.7 * p['blink'])
    if eo > 0.05:
        er = (0.55 + 0.3 * flare) * eo
        cv.fill(cv.ellipse((hx + 2.0, hy - 1.5), er * 1.2, er * (1.0 - 0.5 * p['blink'])), EYE, z=13.2, glow=EYE_GLOW)
        cv.fill(cv.ellipse((hx + 5.0, hy - 1.4), er * 0.7, er * 0.9 * (1.0 - 0.5 * p['blink'])), EYE, z=13.2, glow=EYE_GLOW)
        if flare > 0.3:
            cv.fill(cv.ellipse((hx + 3.4, hy - 1.5), 4.6 * flare, 3.0 * flare), (0, 0, 0), z=-99, glow=(0.3 * flare, 0.34 * flare, 0.1 * flare), alpha=0.0)
        if flare > 0.7:   # "!!": göz ışığı geriye doğru iz bırakır
            yk.glow_soft(cv, (hx + 2.2, hy - 1.5), 2.0 + 2.6 * flare, EYE_GLOW, z=13.3, blur=0.6, alpha=0.45 * flare)
            cv.stroke([(hx + 2.8, hy - 1.5), (hx + 2.8 - 4.5 * flare, hy - 2.2 - 0.8 * flare)], 0.8 + 0.6 * flare, z=13.25, col=EYE,
                      taper=(0.1, 0.9), glow=EYE_GLOW)
    cv.pop()
    # yüzün önüne düşen yağlı saç tutamları (gözleri kapatmaz; kökler başla, uçlar yerçekimiyle)
    for k, (dx, ln) in enumerate(((-0.6, 7), (0.6, 6), (6.4, 4))):
        root = R((hx + dx, hy - 4.4))
        st = G(chain(root, ln, 1.5, math.pi * 0.5 + 0.04 - 0.04 + drag * 0.8 + hup * 0.3 + math.sin(ph + k * 2) * 0.06, 0.0, ph + k, 0.1))
        cv.shape(ik.taper_path([cv.W(q_) for q_ in st], cv.u(0.9 + 0.25 * (k % 2)), (0.05, 0.9)), HAIR, z=13.6 + k * 0.01, sd=0.4, ol=0.6, hi=0.0)
    # kefen başlığı altından sarkan saç perdesi
    for k, dx in enumerate((-4.6, -3.2, -1.6, -0.2)):
        root = R((hx + dx, hy - 3.8))
        st = G(chain(root, 6, 2.6 * (1.0 - 0.1 * hup), math.pi * 0.5 + 0.08 + math.sin(ph + k) * 0.1 - 0.05 + drag * 0.9 + hup * (0.5 + k * 0.08),
                     0.03, ph + k, 0.15 + hup * 0.1))
        cv.shape(ik.taper_path([cv.W(q_) for q_ in st], cv.u(1.5), (0.05, 0.85)), HAIR, z=30 + k * 0.1, sd=0.5, ol=0.7, hi=0.0,
                 details=[('stroke', [st[1], st[3]], 0.8, HAIR.hi, (0.3, 0.6))])
    # kefen başlığı: kafayı arkadan örter, yüzü çerçeveler
    yg.xf_push(cv, nb, hr)
    hood = cv.blob([yg.rot_about((sh[0] + 3, sh[1] - 5.5), nb, -hr * 0.6), (hx - 6.8 - hup * 1.5, hy - 3 - hup), (hx - 4.2, hy - 8.8 - hup * 0.8),
                    (hx + 1.5, hy - 9.8), (hx + 6.2, hy - 7.2),
                    (hx + 7.6, hy - 4.0, 0.0), (hx + 4.5, hy - 4.8), (hx + 1.0, hy - 5.4), (hx - 2.2, hy - 3.0), (hx - 3.5, hy + 2.5),
                    (hx - 5.5, hy + 4.5), yg.rot_about((sh[0] - 1, sh[1] + 2), nb, -hr * 0.6)])
    hdt = cv.fold([(hx - 4.0, hy - 6.0), (hx - 4.6, hy - 1.0), (hx - 5.2, hy + 3.0)], 0.9, 1.2, 1)
    hdt += cv.fold([(hx + 1.0, hy - 8.4), (hx + 3.2, hy - 6.6), (hx + 5.6, hy - 5.6)], 0.5, 1.0, -1)
    cv.shape(hood, SHROUD, z=36, sd=2.6, hi=0.35, details=hdt, hatch=0.3, cast=0.8, bounce=0.3)
    cv.pop()

    # ---- ön bacak + ön kol
    _leg(cv, (hip[0] + 2.5, hip[1]), F(p['lf']), p['lf'][2], 8, True)
    _e, _h, tip, palm = _arm(cv, (sh[0] + 2, sh[1] + 2), p['af'][:2], p['ebf'], p['wf'], 40, True, p['gf'], ph, drag, p['ball'])
    hand_pt = yg.world(cv, palm)
    cv.pop()   # ezilme
    cv.pop()   # figür
    return {'hand': hand_pt, 'mouth': mouth_pt}


SHADE = dict(outer=0.5, rim=0.6, rim_col=(0.7, 0.85, 1.0), rim_dir=(0.55, -0.85), rim_w=1.4, form=(7.0, (0.74, 0.72, 0.88)))


# ====================================================================== anahtar pozlar (yaratik_govde.Seq)
# Koordinatlar dünya birimi, ayak noktası (0, 0); +x ileri, -y yukarı. Eller (af / ab) figür çerçevesinde mutlak nokta,
# ayaklar (lf / lb) dünya hedefi (x, yükseklik, parmak açısı). Dinlenme: kalça (-2, -35,7), omuz ~(13, -56), eller yerde.
def _foot_cycle(phi, home, S, duty, lift, toe_up=0.5, toe_push=0.5):
    """Döngüsel ayak yolu: basma (duty) boyunca +S/2 -> -S/2 (sabit hız), salınımda yayla öne (yükseklik lift)."""
    phi %= 1.0
    if phi < duty:
        u = phi / duty
        toe = toe_push * max(0.0, (u - 0.7) / 0.3)          # itişte topuk kalkar
        return (home + S * (0.5 - u), 0.0, toe)
    u = (phi - duty) / (1.0 - duty)
    e = u * u * (3 - 2 * u)
    return (home - S * 0.5 + S * e, lift * math.sin(math.pi * u) ** 0.8, toe_up * math.sin(math.pi * u) - 0.25 * max(0.0, u - 0.75) / 0.25)


def _hand_cycle(phi, home, S, duty, lift, y0):
    """Pençe sürüyüşü: yere değen boğumlar gövdeyle aynı hızda geri kayar, sonra kol sarkaç gibi öne savrulur."""
    phi %= 1.0
    if phi < duty:
        u = phi / duty
        return (home + S * (0.5 - u), y0)
    u = (phi - duty) / (1.0 - duty)
    e = u * u * (3 - 2 * u)
    return (home - S * 0.5 + S * e, y0 - lift * math.sin(math.pi * u))


WALK_S, WALK_DUTY, WALK_VX = 22.0, 0.62, 60.0
WALK_FPS = 8 * WALK_VX * WALK_DUTY / WALK_S      # 8 kare = bir döngü; basan ayak gövdeye göre vx hızında kayar


def _walk(t):
    """Sinsi, uzun bacaklı sokulma: diz yüksek kalkar, kalça basışta çöker; boğumlar / pençeler yerde sürünür (kol, karşı
    bacakla aynı evrede); baş her adımda öne uzanır (önden giden baş), kefen ve saç geride dalgalanır."""
    p = {}
    p['lf'] = _foot_cycle(t, -1.5, WALK_S, WALK_DUTY, 7.0)
    p['lb'] = _foot_cycle(t - 0.5, -0.5, WALK_S, WALK_DUTY, 7.0)
    hs = WALK_S * 0.5 / WALK_DUTY
    p['af'] = _hand_cycle(t - 0.5, 27.0, hs, 0.5, 9.0, -14.5)
    p['ab'] = _hand_cycle(t, 26.0, hs, 0.5, 8.0, -16.0)
    c2 = math.cos(4 * math.pi * (t - 0.06))
    p.update(hy=1.8 + 1.5 * c2, hx=0.6 * math.sin(2 * math.pi * t), pitch=0.15 + 0.04 * c2, bob=-0.6 * c2,
             hd=(1.2 + 1.4 * math.sin(4 * math.pi * (t - 0.12)), 0.6 + 0.8 * c2), hr=0.06 + 0.06 * math.sin(4 * math.pi * (t + 0.1)),
             gf=0.05, gb=0.05, wf=0.25, wb=0.25, jaw=0.25, flare=0.15, drag=0.18 + 0.05 * c2, ph=t * math.tau * 2, arch=0.6)
    return p


def _idle_proc(p, t):
    """Bekleme: kaburgalarda soluk, omuzlarda sallantı, saçta / kefende gecikmeli dalga."""
    p = dict(p)
    s = math.sin(t * math.tau)
    p['br'] = p.get('br', 0.0) + 0.5 * s
    p['bob'] = p.get('bob', 0.0) + 0.9 * s
    p['ph'] = t * math.tau
    a, b = p.get('af', AF0), p.get('ab', AB0)
    p['af'] = (a[0], a[1] + 0.5 * s)
    p['ab'] = (b[0], b[1] + 0.5 * math.sin(t * math.tau - 0.6))
    return p


SEQS = {}

# ---- bekleme (8 kare, ~1,2 sn): kambur sallantı, parmak seğirmesi, ani baş tiki (kafa yukarı kırılıp düşer), saç savrulur
SEQS['idle'] = Seq([
    (0.0, dict(), 'io'),
    (0.25, dict(hx=0.6, pitch=0.03, hd=(0.6, 0.4), gf=0.2, gb=0.1), 'io'),
    (0.375, dict(hx=0.5, pitch=0.02, hd=(0.5, 0.3), gf=0.75, gb=0.3, wf=-0.15), 'o'),
    (0.5, dict(hx=0.2, gf=0.05, gb=0.15, wf=0.05), 'io'),
    (0.6, dict(hx=0.0, hr=0.0, hd=(0.0, 0.0)), 'io'),
    (0.64, dict(hr=-0.34, hd=(-0.6, -1.4), jaw=0.55, flare=0.45, hairup=0.25, gf=0.5, gb=0.5, sq=-0.15), 'i2'),
    (0.76, dict(hr=0.2, hd=(0.8, 0.6), jaw=0.3, flare=0.25, hairup=0.05, gf=0.2, gb=0.3, sq=0.1), 'o'),
    (0.9, dict(hr=0.04, hd=(0.2, 0.1)), 'io'),
    (1.0, dict(), 'io'),
], n=8, fps=7, loop=True, proc=_idle_proc, rest=REST)

# ---- yürüyüş (8 kare, adım 22 birim): vx 60 px/sn'de 1x
SEQS['walk'] = Seq([(i / 8, _walk(i / 8), 'l') for i in range(9)], n=8, fps=round(WALK_FPS, 2), loop=True, rest=REST,
                   extra={'vx': WALK_VX})

# ---- dönüş (4 kare, 0,2 sn): yeni yöne dönmüş ama gövde daralmış (yarı dönük), baş önden gider, kollar geride savrulur
SEQS['turn'] = Seq([
    (0.0, dict(sx=0.5, hd=(4.0, -1.0), hr=-0.15, af=(10.0, -18.0), ab=(4.0, -20.0), drag=0.6, jaw=0.4, flare=0.4, pitch=0.05), 'l'),
    (0.35, dict(sx=0.72, hd=(2.5, 0.0), hr=-0.05, af=(20.0, -16.0), ab=(16.0, -18.0), drag=0.45, jaw=0.3), 'o'),
    (0.7, dict(sx=1.06, hx=0.8, hd=(1.0, 0.6), af=(30.0, -15.0), ab=(29.0, -18.0), drag=0.1), 'o'),
    (1.0, dict(), 'io'),
], frames=[(0.0, 0.0), (0.35, 0.25), (0.7, 0.5), (1.0, 0.75)], rest=REST, fps=14)

# ---- yakalama hazırlığı "!!" (4 kare; st 0,5 / intikam 0,4): baş geri kırılır, kollar örümcek gibi açılır, yere sinik
# geniş duruş (DERİN KURULMA uzun tutulur: çene sonuna dek açık, saç kabarık, gözler alev), son kare fırlayış (0,05 sn)
GW_DEEP = dict(hy=9.0, hx=-2.0, pitch=0.38, arch=3.0, af=(40.0, -72.0), ab=(-14.0, -64.0), wf=-0.5, wb=0.4, gf=1.0, gb=1.0,
               jaw=1.25, hd=(2.5, 2.0), hr=-0.22, flare=1.0, hairup=1.0, br=1.0, lf=(8.0, 0.0, 0.0), lb=(-16.0, 0.0, 0.45), drag=-0.15)
GW_LEAD = dict(hy=3.0, hx=4.0, pitch=0.62, arch=0.5, af=(58.0, -44.0), ab=(54.0, -50.0), gf=1.0, gb=1.0, jaw=1.1, hd=(4.0, 1.0),
               hr=0.05, flare=1.0, hairup=0.45, drag=0.6, lf=(14.0, 3.5, 0.3), lb=(-15.0, 0.0, 0.9), sq=-0.4)
SEQS['windup'] = Seq([
    (0.0, dict(hd=(-1.5, -2.0), hr=-0.3, jaw=0.55, pitch=-0.05, af=(34.0, -40.0), ab=(24.0, -44.0), gf=0.6, gb=0.6, flare=0.55,
               hairup=0.25, sq=-0.15), 'o'),
    (0.3, dict(hy=4.0, pitch=0.16, arch=2.0, af=(42.0, -66.0), ab=(-8.0, -60.0), gf=0.9, gb=0.9, jaw=0.85, flare=0.8, hairup=0.55,
               hd=(1.0, 0.5), hr=-0.12, lf=(4.0, 0.0, 0.0), lb=(-12.0, 0.0, 0.3), br=0.6), 'o'),
    (0.62, GW_DEEP, 'o'),
    (1.0, GW_LEAD, 'i'),
], frames=[(0.0, 0.0), (0.3, 0.2), (0.62, 0.45), (1.0, 0.0)], seg=[('windup', 4)], lead={'windup': 0.05}, rest=REST, fps=10)

# ---- pençe tırmığı "!" (windup 0,3 / strike 0,3 / recover 0,45; 3 + 2 + 3 kare): yakın kol başın arkasına kurulur,
# baş önden uzanır; kol tepeden kırbaç gibi iner (temas: kol 56 birim önde, kutu 60), pençeler yerde sürünerek geri gelir
SEQS['claw'] = Seq([
    (0.08, dict(hx=-1.0, pitch=-0.1, lean=0.06, af=(-2.0, -76.0), ab=(34.0, -24.0), gf=0.8, jaw=0.5, hd=(1.5, -1.0), hr=-0.1,
                flare=0.4, drag=0.15, arch=1.0, lb=(-8.0, 0.0, 0.2)), 'o'),
    (0.22, dict(hx=-2.0, hy=1.5, pitch=-0.18, lean=0.04, arch=1.6, af=(-10.0, -80.0), ab=(32.0, -30.0), gf=1.0, jaw=0.75, hd=(2.0, -0.5),
                hr=-0.14, flare=0.55, hairup=0.2, drag=0.2, lb=(-9.0, 0.0, 0.3)), 'o'),
    (0.36, dict(hx=1.0, pitch=0.12, af=(26.0, -92.0), ab=(26.0, -34.0), gf=1.0, jaw=0.8, hd=(2.5, 0.0), hr=-0.05, flare=0.5,
                drag=0.35, lf=(5.0, 4.0, 0.3), lb=(-8.0, 0.0, 0.5)), 'i'),
    (0.45, dict(hx=4.0, hy=2.0, pitch=0.46, af=(56.0, -36.0), wf=0.25, gf=1.0, ab=(8.0, -36.0), gb=0.5, lf=(12.0, 0.0, 0.0),
                lb=(-10.0, 0.0, 0.55), jaw=0.85, hd=(4.0, 2.0), hr=0.1, drag=0.55, sq=-0.3, flare=0.5), 'i'),
    (0.56, dict(hx=4.0, hy=4.5, pitch=0.56, af=(44.0, -12.0), wf=0.3, gf=0.6, ab=(2.0, -30.0), gb=0.4, lf=(12.0, 0.0, 0.0),
                lb=(-10.0, 0.0, 0.3), jaw=0.5, hd=(4.0, 4.0), hr=0.2, drag=0.3, sq=0.3, flare=0.3), 'o'),
    (0.66, dict(hx=3.5, hy=4.0, pitch=0.5, af=(36.0, -11.0), wf=0.4, gf=0.3, ab=(10.0, -24.0), lf=(12.0, 0.0, 0.0),
                lb=(-9.0, 0.0, 0.2), jaw=0.35, hd=(3.0, 3.0), hr=0.15, drag=0.15, sq=0.1), 'io'),
    (0.83, dict(hx=1.5, hy=2.0, pitch=0.24, af=(32.0, -15.0), ab=(22.0, -18.0), lf=(5.0, 0.0, 0.0), lb=(-7.0, 0.0, 0.0),
                jaw=0.25, hd=(1.0, 1.0), hr=0.05), 'io'),
    (1.0, dict(), 'io'),
], frames=[(0.08, 0.0), (0.22, 0.3), (0.36, 0.0), (0.45, 0.0), (0.56, 0.4), (0.66, 0.0), (0.83, 0.4), (1.0, 0.75)],
    seg=[('windup', 3), ('strike', 2), ('recover', 3)], lead={'windup': 0.05}, rest=REST, fps=10)

# ---- yakalama atılışı (st ileri sayar, en çok 0,35 sn; 3 kare): iki kol sonuna dek uzanır (kutu 6..70), gövde yatay,
# arka ayak parmak ucunda; yavaşlarken pençeler ŞAK diye kapanır
SEQS['grab'] = Seq([
    (0.0, dict(x=6.0, hy=2.0, pitch=0.75, af=(58.0, -40.0), ab=(55.0, -47.0), gf=1.0, gb=1.0, jaw=1.25, hd=(5.0, 2.0), hr=-0.12,
               flare=1.0, drag=0.85, hairup=0.3, lf=(16.0, 0.0, 0.0), lb=(-16.0, 2.0, 0.9), sq=-0.5), 'o'),
    (0.5, dict(x=5.0, hy=2.5, pitch=0.68, af=(54.0, -37.0), ab=(51.0, -42.0), gf=0.75, gb=0.75, jaw=1.0, hd=(4.5, 2.0), hr=-0.05,
               flare=0.9, drag=0.5, hairup=0.2, lf=(16.0, 0.0, 0.0), lb=(-14.0, 0.0, 0.6), sq=-0.2), 'o'),
    (1.0, dict(x=4.0, hy=3.0, pitch=0.6, af=(50.0, -34.0), ab=(47.0, -38.0), gf=0.0, gb=0.0, jaw=0.6, hd=(4.0, 2.5), hr=0.05,
               flare=0.8, drag=0.15, lf=(15.0, 0.0, 0.0), lb=(-13.0, 0.0, 0.4), sq=0.25), 'i'),
], frames=[(0.0, 0.0), (0.5, 0.35), (1.0, 0.7)], rest=REST, fps=10)


# ---- tutuş (döngü 4 kare, 0,36 sn = sıkma darbesi): kurban (34, -10)'da havada; kollar onu göğse bastırır, her darbede
# omuzlar kamburlaşır, gövde ezilir, çene kurbana saldırır
def _hold(t):
    s = math.cos(t * math.tau)          # 1 = sıkma anı
    k = max(0.0, s) ** 2
    return dict(x=2.0, hy=1.0 + 1.5 * k, pitch=0.16 + 0.06 * k, lean=0.04, arch=1.0 + 1.6 * k, br=0.4 + 0.8 * k,
                af=(37.0 - 3.0 * k, -38.0 + 2.0 * k), ab=(33.0 - 3.0 * k, -24.0 - 2.0 * k), ebf=1.0, ebb=1.0, wf=0.5, wb=-0.3,
                gf=0.05, gb=0.05, hd=(3.0 + 1.5 * k, 0.5 + 1.5 * k), hr=-0.08 + 0.26 * k, jaw=0.55 + 0.6 * k, flare=0.65 + 0.3 * k,
                hairup=0.15 + 0.25 * k, sq=0.55 * k - 0.15 * max(0.0, -s), lf=(7.0, 0.0, 0.0), lb=(-10.0, 0.0, 0.3), drag=-0.1 * k,
                ph=t * math.tau)


SEQS['hold'] = Seq([(i / 8, _hold(i / 8), 'l') for i in range(9)], n=4, fps=11, loop=True, rest=REST)

# ---- fırlatış (hold>recover, st 0,7; 3 kare): kollar kurbanı öne-yukarı savurur (bırakış), takip: kollar aşağı iner,
# gövde öne kapanır, sonra kambura oturur
SEQS['throw'] = Seq([
    (0.0, dict(x=4.0, pitch=0.22, lean=0.02, af=(52.0, -74.0), ab=(48.0, -78.0), gf=1.0, gb=1.0, jaw=1.0, hd=(3.0, -2.0), hr=-0.28,
               drag=-0.35, hairup=0.3, lf=(12.0, 0.0, 0.0), lb=(-12.0, 1.0, 0.8), sq=-0.4, flare=0.8), 'o'),
    (0.4, dict(x=3.0, hy=2.0, pitch=0.5, af=(54.0, -18.0), ab=(50.0, -26.0), gf=0.6, gb=0.6, jaw=0.6, hd=(4.0, 2.0), hr=0.1,
               drag=0.3, lf=(12.0, 0.0, 0.0), lb=(-11.0, 0.0, 0.3), sq=0.2, flare=0.5), 'o'),
    (1.0, dict(), 'io'),
], frames=[(0.0, 0.0), (0.4, 0.25), (1.0, 0.65)], rest=REST, fps=10)

# ---- ıskalama (grab>recover, st 1,0 — uzun ceza penceresi; 3 kare): fazla uzanmış gövde öne yığılır, pençeler yere çarpar,
# ayak sendeleyerek öne basar; baş yukarı kırılıp bakar, kollarını sürüyerek doğrulur
SEQS['miss'] = Seq([
    (0.0, dict(x=7.0, hy=6.0, pitch=0.95, af=(57.0, -6.0), ab=(61.0, -4.0), gf=1.0, gb=1.0, jaw=0.9, hd=(3.0, 2.0), hr=0.3, flare=0.6,
               drag=0.7, lf=(15.0, 4.0, 0.4), lb=(-16.0, 0.0, 1.0), sq=0.4), 'o'),
    (0.3, dict(x=6.0, hy=5.0, pitch=0.8, af=(50.0, -7.0), ab=(54.0, -5.0), gf=0.3, gb=0.3, jaw=0.5, hd=(2.0, -1.0), hr=-0.3,
               flare=0.7, drag=-0.25, lf=(16.0, 0.0, 0.0), lb=(-14.0, 0.0, 0.6), sq=0.1), 'o'),
    (1.0, dict(x=2.0, hy=2.0, pitch=0.3, af=(36.0, -14.0), ab=(34.0, -16.0), gf=0.2, gb=0.2, hd=(1.0, 1.0), hr=0.05,
               lf=(3.0, 0.0, 0.0), lb=(-8.0, 0.0, 0.1)), 'io'),
], frames=[(0.0, 0.0), (0.3, 0.25), (1.0, 0.6)], rest=REST, fps=10)

# ---- pusu (Karakoncolos; 1 kare): kıpırtısız, kefene sarılı kar yığını gibi büzülmüş; baş göğse gömülü
LURK = dict(hy=22.0, hx=-3.0, pitch=1.0, arch=4.0, lf=(2.0, 0.0, 0.2), lb=(-4.0, 0.0, 0.3), af=(14.0, -3.0), ab=(18.0, -2.0),
            gf=0.0, gb=0.0, hd=(-2.0, -3.0), hr=0.6, jaw=0.0, flare=0.0, eyes=0.5)
SEQS['lurk'] = Seq([(0.0, LURK, 'l'), (1.0, LURK, 'l')], n=1, fps=1, loop=True, rest=REST)

# ---- pusudan fırlayış (lurk>windup, st 0,3; 4 kare): yığın silkinir, gövde patlarcasına açılır, kollar savrulur ->
# yakalama hazırlığının derin pozu -> atılış
SEQS['emerge'] = Seq([
    (0.0, dict(LURK, hairup=0.35, flare=0.7, eyes=1.0, hr=0.35, sq=0.35), 'o'),
    (0.35, dict(hy=10.0, pitch=0.5, arch=3.0, af=(30.0, -58.0), ab=(8.0, -56.0), gf=0.8, gb=0.8, hd=(1.0, 0.0), hr=-0.2, jaw=0.9,
                flare=0.9, hairup=0.85, sq=-0.4, drag=-0.3, lf=(6.0, 0.0, 0.0), lb=(-12.0, 0.0, 0.4)), 'o'),
    (0.65, GW_DEEP, 'o'),
    (1.0, GW_LEAD, 'i'),
], frames=[(0.0, 0.0), (0.35, 0.25), (0.65, 0.5), (1.0, 0.0)], seg=[('windup', 4)], lead={'windup': 0.05}, rest=REST, fps=10)

# ---- kartopu (Karakoncolos; windup 0,45 / strike 0,35; 3 + 2 kare): yerden kar avuçlar, topu başının arkasına kurar,
# ön ayağı kalkar; bırakış (temas karesi = mermi çıkışı), kol öne-aşağı takip eder
SEQS['snow'] = Seq([
    (0.0, dict(hy=7.0, pitch=0.6, af=(34.0, -2.0), gf=0.9, ball=0.6, ab=(22.0, -14.0), hd=(2.0, 3.0), hr=0.15, jaw=0.3,
               lf=(4.0, 0.0, 0.0), lb=(-10.0, 0.0, 0.3)), 'o'),
    (0.25, dict(hy=3.0, pitch=0.1, af=(-4.0, -52.0), ball=1.0, gf=0.2, ab=(32.0, -38.0), gb=0.8, hd=(1.0, -1.0), hr=-0.1, jaw=0.5,
                lf=(6.0, 0.0, 0.0), lb=(-10.0, 0.0, 0.2), flare=0.3), 'o'),
    (0.5, dict(hy=2.0, hx=-2.0, pitch=-0.15, lean=0.05, arch=1.0, af=(-18.0, -70.0), ball=1.0, gf=0.2, ab=(34.0, -46.0), gb=1.0,
               hd=(0.5, -2.0), hr=-0.15, jaw=0.7, flare=0.5, lf=(10.0, 3.0, 0.3), lb=(-10.0, 0.0, 0.2), drag=0.2), 'o'),
    (0.62, dict(x=3.0, pitch=0.35, af=(50.0, -66.0), gf=1.0, ball=0.0, ab=(2.0, -30.0), gb=0.5, lf=(12.0, 0.0, 0.0),
                lb=(-12.0, 1.0, 0.8), hd=(3.0, 0.0), hr=0.0, jaw=0.9, drag=0.4, sq=-0.3, flare=0.5), 'i'),
    (0.85, dict(x=3.0, hy=3.0, pitch=0.55, af=(44.0, -10.0), gf=0.5, ab=(10.0, -26.0), lf=(12.0, 0.0, 0.0), lb=(-11.0, 0.0, 0.3),
                hd=(3.0, 2.0), hr=0.15, jaw=0.4, drag=0.2, sq=0.2), 'o'),
], frames=[(0.0, 0.0), (0.25, 0.3), (0.5, 0.6), (0.62, 0.0), (0.85, 0.45)], seg=[('windup', 3), ('strike', 2)], rest=REST, fps=10)

# ---- hafif sarsılma (3 kare, 0,22 sn): baş geri kırılır, gözler kısılır, kollar gevşekçe savrulur, saç öne çarpar
SEQS['hurt'] = Seq([
    (0.0, dict(x=-3.0, hy=1.0, pitch=-0.25, hd=(-2.0, -2.0), hr=-0.4, jaw=0.9, blink=1.0, af=(18.0, -30.0), ab=(12.0, -34.0),
               gf=0.9, gb=0.9, drag=-0.5, hairup=0.3, sq=-0.2), 'o'),
    (0.5, dict(x=-1.5, hy=0.5, pitch=-0.1, hd=(-1.0, 0.0), hr=-0.15, jaw=0.6, blink=0.5, af=(24.0, -22.0), ab=(22.0, -26.0),
               gf=0.5, gb=0.5, drag=-0.2), 'o'),
    (1.0, dict(jaw=0.3), 'o'),
], frames=[(0.0, 0.0), (0.5, 0.35), (1.0, 0.7)], rest=REST, fps=12)

# ---- ağır sendeleme (4 kare, 0,45 sn): gövde geriye bükülür, kollar havaya fırlar, arka ayak geri basar; öne düşüp pençelerle tutunur
SEQS['hurt_big'] = Seq([
    (0.0, dict(x=-5.0, pitch=-0.45, arch=-1.0, hd=(-3.0, -3.0), hr=-0.6, jaw=1.25, blink=1.0, af=(10.0, -62.0), ab=(0.0, -60.0),
               gf=1.0, gb=1.0, drag=-0.7, hairup=0.5, lb=(-14.0, 4.0, 0.6), sq=-0.3, flare=0.2), 'o'),
    (0.35, dict(x=-5.0, hy=3.0, pitch=-0.2, hd=(-2.0, 0.0), hr=-0.3, jaw=0.8, blink=0.8, af=(14.0, -34.0), ab=(8.0, -36.0),
                gf=0.6, gb=0.6, lb=(-16.0, 0.0, 0.3), drag=-0.3, sq=0.3), 'io'),
    (0.7, dict(x=-2.0, hy=4.0, pitch=0.22, hd=(1.0, 3.0), hr=0.2, jaw=0.5, blink=0.3, af=(26.0, -10.0), ab=(22.0, -12.0),
               gf=0.3, gb=0.3, lb=(-14.0, 0.0, 0.2), drag=0.1), 'o'),
    (1.0, dict(hy=1.0, lb=(-8.0, 0.0, 0.0), jaw=0.3), 'io'),
], frames=[(0.0, 0.0), (0.35, 0.25), (0.7, 0.55), (1.0, 0.8)], rest=REST, fps=10)


# ---- sersem / duruş kırık (6 kare döngü): dizler bükük sallanır, baş yuvarlanır, kollar yere sarkıp gevşekçe savrulur
def _stun(t):
    s = math.sin(t * math.tau)
    c = math.cos(t * math.tau)
    return dict(hx=1.5 * s, hy=5.0 + 1.0 * c, pitch=0.3 + 0.06 * c, roll=0.03 * s, hd=(0.5 * s, 3.0 + 1.0 * c), hr=0.45 + 0.15 * s,
                jaw=0.7, blink=0.6, flare=0.0, eyes=0.6, af=(25.0 + 4.0 * s, -9.0 + 1.5 * c), ab=(21.0 + 4.0 * math.sin(t * math.tau - 0.8), -8.0),
                gf=0.2, gb=0.2, lb=(-8.0 + 1.2 * c, 0.0, 0.2), lf=(2.0, 0.8 * max(0.0, s), 0.2), drag=0.3 * s, ph=t * math.tau)


SEQS['stun'] = Seq([(i / 12, _stun(i / 12), 'l') for i in range(13)], n=6, fps=6, loop=True, rest=REST)

# ---- havaya savrulma (dikey hız evresi; 4 kare): geriye devrilerek döner, uzun uzuvlar çırpınır, saç ve kefen yukarı savrulur
SEQS['launch'] = Seq([
    (0.0, dict(y=-6.0, roll=-0.35, pitch=-0.3, hd=(-2.0, -2.0), hr=-0.5, jaw=1.0, blink=1.0, af=(10.0, -62.0), ab=(-4.0, -60.0),
               gf=1.0, gb=1.0, lf=(2.0, 12.0, 0.5), lb=(-10.0, 14.0, 0.8), drag=-0.6, hairup=0.8, sq=-0.3), 'o'),
    (0.4, dict(y=-8.0, roll=-0.8, pitch=-0.1, hd=(-1.0, 0.0), hr=-0.2, jaw=0.9, blink=0.9, af=(2.0, -50.0), ab=(-12.0, -46.0),
               gf=1.0, gb=0.8, lf=(-2.0, 16.0, 0.6), lb=(-14.0, 12.0, 0.9), drag=-0.9, hairup=1.0), 'io'),
    (0.7, dict(y=-6.0, roll=-0.6, pitch=0.1, hd=(0.0, 1.0), hr=0.0, jaw=0.8, blink=0.5, af=(20.0, -30.0), ab=(8.0, -34.0),
               gf=0.7, gb=0.7, lf=(6.0, 12.0, 0.3), lb=(-6.0, 14.0, 0.5), drag=0.4, hairup=0.6), 'io'),
    (1.0, dict(y=-2.0, roll=-0.25, pitch=0.25, hd=(1.0, 2.0), hr=0.15, jaw=0.6, blink=0.3, af=(30.0, -14.0), ab=(24.0, -16.0),
               gf=0.5, gb=0.5, lf=(6.0, 4.0, 0.1), lb=(-8.0, 5.0, 0.3), drag=0.6, hairup=0.3), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.25), (0.65, 0.55), (1.0, 0.82)], seg=[('air', 4)], rest=REST, fps=10)

# ---- kalkış (savrulma sonrası; 4 kare, 0,5 sn): boğumlar üstünde büzülmüş beden doğrulur, baş yukarı kırılır
SEQS['getup'] = Seq([
    (0.0, dict(hy=18.0, pitch=0.9, arch=3.0, af=(34.0, -3.0), ab=(30.0, -2.0), gf=0.2, gb=0.2, hd=(1.0, -1.0), hr=0.4, blink=0.7,
               lf=(3.0, 0.0, -0.1), lb=(-6.0, 0.0, 0.2), eyes=0.7), 'o'),
    (0.35, dict(hy=11.0, pitch=0.6, arch=2.0, af=(32.0, -6.0), ab=(28.0, -5.0), hd=(2.0, 1.0), hr=0.1, jaw=0.5, blink=0.3,
                lf=(3.0, 0.0, 0.0), lb=(-7.0, 0.0, 0.2)), 'io'),
    (0.65, dict(hy=4.0, pitch=0.3, hd=(1.0, -1.0), hr=-0.3, jaw=0.7, flare=0.5, hairup=0.3, af=(30.0, -14.0), ab=(28.0, -16.0)), 'o'),
    (1.0, dict(), 'io'),
], frames=[(0.0, 0.0), (0.35, 0.3), (0.65, 0.6), (1.0, 0.85)], rest=REST, fps=10)

# ---- ölüm (8 kare, 0,9 sn): göğe çığlık (kollar havada, saç kabarık), geriye sendeler, dizler kırılır, dizüstü çöker,
# gövde öne yığılır, yüzüstü yere serilir; son bir pençe seğirmesi, gözlerin ışığı söner, kefen yatışır
SEQS['death'] = Seq([
    (0.0, dict(x=-2.0, pitch=-0.4, lean=0.05, hd=(-2.0, -3.0), hr=-0.65, jaw=1.45, flare=1.0, af=(16.0, -72.0), ab=(2.0, -70.0),
               gf=1.0, gb=1.0, hairup=1.0, drag=-0.4, sq=-0.4, lb=(-10.0, 0.0, 0.3)), 'o'),
    (0.16, dict(x=-4.0, hy=2.0, pitch=-0.5, arch=-1.0, hd=(-3.0, -3.0), hr=-0.8, jaw=1.3, flare=0.8, af=(6.0, -62.0), ab=(-6.0, -58.0),
                gf=0.9, gb=0.9, lb=(-14.0, 3.0, 0.5), drag=-0.3, hairup=0.7, sq=-0.2), 'io'),
    (0.32, dict(x=-3.0, hy=10.0, pitch=0.0, hd=(-1.0, 0.0), hr=-0.3, jaw=1.0, flare=0.5, af=(14.0, -30.0), ab=(6.0, -28.0),
                gf=0.6, gb=0.6, lb=(-13.0, 0.0, 0.4), lf=(-4.0, 0.0, 0.0), drag=0.2, hairup=0.2, sq=0.3), 'i2'),
    (0.46, dict(x=-3.0, hy=16.5, pitch=0.45, arch=2.0, hd=(1.0, 2.0), hr=0.3, jaw=0.8, flare=0.3, af=(24.0, -6.0), ab=(18.0, -4.0),
                gf=0.3, gb=0.3, lf=(-19.0, 1.0, -0.5), lb=(-21.0, 1.0, -0.4), drag=0.3, eyes=0.8), 'i'),
    (0.6, dict(x=-3.0, hy=19.5, pitch=0.85, arch=2.5, hd=(4.0, -3.5), hr=0.1, jaw=1.0, af=(38.0, -7.0), ab=(30.0, -6.0),
               gf=0.7, gb=0.7, lf=(-21.0, 1.0, -0.8), lb=(-22.0, 1.0, -0.7), drag=0.4, eyes=0.6), 'i2'),
    (0.72, dict(x=-3.0, hy=22.0, pitch=1.0, arch=1.5, hd=(7.0, -7.0), hr=-0.25, wf=0.5, wb=0.5, jaw=0.6, af=(44.0, -7.0), ab=(37.0, -6.0),
                gf=0.6, gb=0.6, lf=(-23.0, 1.5, -1.0), lb=(-24.0, 1.5, -0.9), drag=0.2, eyes=0.4), 'o'),
    (0.84, dict(x=-3.0, hy=22.0, pitch=1.0, arch=2.6, hd=(7.0, -7.0), hr=-0.25, wf=0.5, wb=0.5, jaw=0.7, af=(40.0, -14.0), ab=(37.0, -6.0),
                gf=0.15, gb=1.0, lf=(-23.0, 1.5, -1.0), lb=(-24.0, 3.5, -0.7), drag=0.1, eyes=0.5, hairup=0.15), 'o'),
    (1.0, dict(x=-3.0, hy=22.5, pitch=1.02, arch=1.2, hd=(7.0, -7.0), hr=-0.25, wf=0.5, wb=0.5, jaw=0.5, af=(44.0, -7.0), ab=(37.0, -6.0),
               gf=0.8, gb=0.9, lf=(-23.0, 1.5, -1.0), lb=(-24.0, 1.5, -0.9), drag=0.0, eyes=0.0), 'o'),
], frames=[(0.0, 0.0), (0.16, 0.1), (0.32, 0.22), (0.46, 0.34), (0.6, 0.46), (0.72, 0.58), (0.84, 0.72), (1.0, 0.88)], rest=REST, fps=10)

# ---- çığlık (seçkin kükremesi; 5 kare, 0,8 sn): sinip boy verir, kollar örümcek gibi açılır, göğe ince bir çığlık
SEQS['roar'] = Seq([
    (0.0, dict(), 'io'),
    (0.25, dict(hy=4.0, pitch=0.3, hd=(1.0, 2.0), hr=0.25, jaw=0.2, af=(30.0, -12.0), ab=(28.0, -14.0), gf=0.6, gb=0.6), 'o'),
    (0.5, dict(hy=-1.0, pitch=-0.35, lean=0.0, arch=-1.0, hd=(-2.0, -3.0), hr=-0.7, jaw=1.5, flare=1.0, hairup=1.0, af=(34.0, -78.0),
               ab=(-12.0, -74.0), gf=1.0, gb=1.0, br=1.0, sq=-0.3, lb=(-10.0, 0.0, 0.2), lf=(4.0, 0.0, 0.0), wf=-0.4, wb=0.4), 'o'),
    (0.78, dict(hy=0.0, pitch=-0.3, lean=0.02, arch=-0.6, hd=(-1.5, -2.5), hr=-0.6, jaw=1.4, flare=1.0, hairup=0.85, af=(36.0, -74.0),
                ab=(-10.0, -70.0), gf=1.0, gb=1.0, br=0.6, sq=-0.2, lb=(-10.0, 0.0, 0.2), lf=(4.0, 0.0, 0.0), ph=1.5), 'io'),
    (1.0, dict(), 'io'),
], frames=[(0.1, 0.0), (0.28, 0.15), (0.5, 0.35), (0.76, 0.65), (1.0, 0.9)], rest=REST, fps=8)

DURUM = {
    # ---- tepkiler (Enemy._anim_tick öncelikli anahtarları)
    '_hurt': {'a': 'hurt', 'u': 'up', 'd': 0.22},
    '_hurt_big': {'a': 'hurt_big', 'u': 'up', 'd': 0.45},
    '_break': {'a': 'stun', 'u': 'loop'},
    '_launch': {'a': 'launch', 'u': 'vy'},
    '_getup': {'a': 'getup', 'u': 'up', 'd': 0.5},
    '_death': {'a': 'death', 'u': 'up', 'd': 0.9},
    '_turn': {'a': 'turn', 'u': 'up', 'd': 0.2},
    '_roar': {'a': 'roar', 'u': 'up', 'd': 0.8},
    # ---- grabber: pençe tırmığı "!"
    'windup/claw': {'a': 'claw', 's': 'windup', 'u': 'st'},
    'windup/claw!!': {'a': 'claw', 's': 'windup', 'u': 'st'},
    'strike/claw': {'a': 'claw', 's': 'strike', 'u': 'st'},
    'recover/claw': {'a': 'claw', 's': 'recover', 'u': 'st'},
    # ---- grabber: yakalama "!!" (intikam yakalaması da aynı anahtar)
    'windup/grab!!': {'a': 'windup', 's': 'windup', 'u': 'st'},
    'windup/grab': {'a': 'windup', 's': 'windup', 'u': 'st'},
    'grab': {'a': 'grab', 'u': 'up', 'd': 0.35},
    'hold': {'a': 'hold', 'u': 'loop'},
    'hold>recover': {'a': 'throw', 'u': 'st'},
    'grab>recover': {'a': 'miss', 'u': 'st'},
    'recover/grab': {'a': 'miss', 'u': 'st'},
    # ---- mimic (Karakoncolos): pusu, fırlayış, kartopu
    'lurk': {'a': 'lurk', 'u': 'loop'},
    'lurk>windup': {'a': 'emerge', 's': 'windup', 'u': 'st'},
    'windup/snow': {'a': 'snow', 's': 'windup', 'u': 'st'},
    'strike/snow': {'a': 'snow', 's': 'strike', 'u': 'st'},
    'recover/snow': {'a': 'claw', 's': 'recover', 'u': 'st'},
    # ---- genel geri dönüşler
    'windup!!': {'a': 'windup', 's': 'windup', 'u': 'st'},
    'windup': {'a': 'claw', 's': 'windup', 'u': 'st'},
    'strike': {'a': 'claw', 's': 'strike', 'u': 'st'},
    'rev': {'a': 'claw', 's': 'strike', 'u': 'st'},
    'recover': {'a': 'claw', 's': 'recover', 'u': 'st'},
}


def render_frame(anim, i, ss=3):
    p = SEQS[anim].pose(i)
    cv = ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
