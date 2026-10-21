"""v39: Tepegöz Yavrusu (kimlik tepegoz_yavrusu; Bozkır, yapay zekâ "slammer", ağır) — mürekkep-cel tam gövde.

Tepegöz devinin yavrusu: babasının (tepegoz_ink.py) dev derisi, kehribar TEK GÖZÜ ve koyun postu aynen; ama çocuk
oranlarında — iri yuvarlak kel baş (gövdenin üçte biri), ağır kaş çıkıntısı, alında iki küçük boynuz tomurcuğu, seyrek
dişli geniş ağız, tombul ama güçlü gövde ve yuvarlak göbek. Omzundan çaprazlama yırtık koyun postu sarar, belinde
ip kuşak ve kemik muska, ayakları çıplak ve iri. Elinde budaklı ağaç kökünden, taş gömülü bir gürz.

Hücre 352x448 doku pikseli = dünya 88 x 112 (doku 4), ayak (30, 106). Gövde 36 x 60 (baş tepesi -61).
Satırlar: idle 8 (ağır soluk, gürz omuzda), move 8 (yeri döven paytak yürüyüş, vx 55), hurt 3,
  atk_slam 10 (çömelir -> YÜKSEĞE sıçrar (gövde ~20 birim havada, gürz ve iki kol baş üstünde) -> göbek ve gürzle
  yere çakılır: şok halkası, toz, çatlaklar -> saplanıp ağır ağır doğrulur),
  atk_flurry 10 (üç hızlı gürz vuruşu: baş üstü / yan / baş üstü, darbe izleriyle),
  atk_boulder 8 (yerden kaya söker, iki eliyle baş üstüne kaldırır, ileri fırlatır; gürz sırtta).
Çapa 'hand' = gürz başı (kaya satırında kaya merkezi) her karede.
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_arm, lerp2
import bosskit as bk
import yaratik_govde as yg
import yaratik_ink_kit as yk
import ucan_v29 as u29
from ucan_v29 import pose_at

TEX = 4.0
CELL = (352, 448)       # dünya 88 x 112 (sıçrayışta baş üstü gürz için üstte pay)
FEET = (120, 424)       # dünya (30, 106)

# ------------------------------------------------------------ malzemeler (babasından: dev derisi, koyun postu, kehribar göz)
SKIN = Ink('#c68c60', '#5c3042', '#eebc90', '#2e1626', name='yavru dev derisi')
SKIN_B = SKIN.darker(0.74, 'uzak deri')
SKIN_D = Ink('#9a6248', '#4e2a38', '#c48c6c', '#28121e', name='dudak/göz kapağı')
NAIL = Ink('#e0cfa8', '#8e7a5c', '#fff6dc', name='tırnak')
WOOL = Ink('#c4b18c', '#6a5e6c', '#ecdcb6', '#3a3242', kind='fur', name='koyun postu')
WOOL_B = WOOL.darker(0.78)
ROPE = Ink('#b8965e', '#6a5034', '#e6cc90', name='ip kuşak')
BONE = Ink('#ece0c2', '#9a8a6c', '#fffaea', '#5e4e3c', name='kemik')
ROOT = Ink('#7c5636', '#3a221c', '#a88052', '#1e1210', name='ağaç kökü')
STONE = Ink('#8e9096', '#4a4a5a', '#c6c8cc', '#2a2a36', name='taş')
ROCK = Ink('#8a8274', '#463e48', '#bcb2a0', '#26202a', name='kaya')
DUST = Ink('#a89a80', '#5e5460', '#d4c8ac', name='toz')
EYE_W = Ink('#f2e6bc', '#b89a70', '#fffbea', name='göz akı')
MOUTH_IN = (0.34, 0.08, 0.10)
IRIS = (1.0, 0.68, 0.16)
IRIS_HOT = (1.0, 0.93, 0.55)
IRIS_GLOW = (1.0, 0.52, 0.08)
SMEAR = (0.98, 0.92, 0.78)


def add(p, v, k=1.0):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


def polar(p, a, r):
    return (p[0] + math.cos(a) * r, p[1] + math.sin(a) * r)


# ------------------------------------------------------------ poz
REST = dict(hx=0.0, hy=0.0, bob=0.0, lean=0.0, sx=1.0, sy=1.0, breath=0.0,
            ff=(7.0, 0.0), fb=(-6.0, 0.0), tuck=0.0,
            a1=-0.35, a2=-2.2, b1=0.25, b2=-0.6,            # yakın kol (gürz) / uzak kol açıları (fk_arm)
            ca=-2.35, cz=8.0, club=1.0, az=20.0, shr=0.0, rup=0.0,                     # gürz yönü (yerel), z, görünür
            ht=0.0, jaw=0.15, brow=0.0, lid=0.0, glow=0.6,
            rock=0.0, rx=0.0, ry=0.0, rfree=0.0,            # kaya: 1 = elde (rx, ry = serbest uçuşta yerel konum)
            slam=0.0, crack=0.0, dust=0.0, smear=0.0, sm_a=(0.0, 0.0), debris=0.0, jit=(0.0, 0.0), sweat=0.0)

HIP = (0.0, -15.0)
SH_N = (6.5, -37.0)
SH_F = (-5.0, -38.0)
L_UP, L_FO = 10.0, 9.5
CLUB_L = 22.0 * 1.2
CK = 1.2   # gürz ölçeği


def _xf(p):
    """Gövde dönüşümü (kalça çevresinde eğilme + ezilme + öteleme): yerel -> dünya."""
    c, s = math.cos(p['lean']), math.sin(p['lean'])
    off = (p['hx'] + p['jit'][0], p['hy'] + p['bob'] + p['jit'][1])

    def f(q):
        x = (q[0] - HIP[0]) * p['sx']
        y = (q[1] - HIP[1]) * p['sy']
        return (HIP[0] + off[0] + x * c - y * s, HIP[1] + off[1] + x * s + y * c)
    return f


def _sh(p, s):
    return (s[0] - p['shr'] * 0.8, s[1] - p['shr'] * 5.0)


def _hand(p):
    e, h = fk_arm(_sh(p, SH_N), p['a1'], p['a2'], L_UP, L_FO)
    return e, h


def _club_head(p):
    _, h = _hand(p)
    return polar(h, p['ca'], CLUB_L - 3.0)


# ------------------------------------------------------------ parçalar
def _leg(cv, hip, foot, z, near, tuck):
    m = SKIN if near else SKIN_B
    ank = (foot[0], foot[1] - 2.6)
    knee, ank = yg.ik2(hip, ank, 7.6, 7.0, -1)
    thigh = bk.muscle(cv, hip, knee, 5.4, 4.2, front=1.0, back=0.8, at=0.4, knob=0.4)
    shin = bk.muscle(cv, knee, ank, 4.2, 3.0, front=0.2, back=1.2, at=0.3)
    det = []
    if near:
        det += [('ink', [lerp2(knee, ank, 0.1), lerp2(knee, ank, 0.5)], 1.1, (0.3, 0.7))]
    cv.shape(ik.union(thigh, shin), m, z=z, sd=2.2, hi=0.35 if near else 0.0, details=det, bounce=0.3 if near else 0.0)
    # iri çıplak ayak: tombul, kısa kalın parmaklar (havada parmaklar aşağı sarkar)
    f = (ank[0], ank[1] + 2.6)
    dn = tuck * 1.5
    fpts = [(f[0] - 4.0, f[1] - 3.6), (f[0] - 0.5, f[1] - 4.6), (f[0] + 4.0, f[1] - 3.0 + dn * 0.3), (f[0] + 7.5, f[1] - 1.8 + dn),
            (f[0] + 8.6, f[1] - 0.2 + dn, 0.0), (f[0] + 7.8, f[1] + 0.5 + dn), (f[0] - 4.2, f[1] + 0.5, 0.0), (f[0] - 5.0, f[1] - 1.6)]
    fdet = [('ink', [(f[0] + 4.6 + k * 1.3, f[1] - 2.0 + dn * 0.6), (f[0] + 4.9 + k * 1.3, f[1] + 0.3 + dn)], 0.9, (0.2, 0.5)) for k in range(3)]
    cv.shape(cv.blob(fpts), m, z=z + 0.3, sd=1.6, hi=0.3 if near else 0.0, details=fdet)
    if near:
        for k in range(3):
            cv.shape(cv.ellipse((f[0] + 5.6 + k * 1.2, f[1] - 0.5 + dn * 0.9 + k * 0.15), 0.6, 0.45), NAIL, z=z + 0.4, sd=0.2, ol=0.5, flat=True)


def _club(cv, h, ca, z, ph):
    """Budaklı ağaç kökü gürz: ince sap, kıvrık gövde, başta yumru kök topuzu, gömülü taşlar ve kök filizleri."""
    d = (math.cos(ca), math.sin(ca))
    n = (-d[1], d[0])

    def P(t, o):
        t, o = t * CK, o * CK
        return (h[0] + d[0] * t + n[0] * o, h[1] + d[1] * t + n[1] * o)
    # sap (hafif kıvrık) + topuz
    up = [(-5.0, 1.3), (0.0, 1.4), (6.0, 1.8 + 0.3), (11.0, 2.4), (14.0, 3.4), (16.5, 5.2), (19.0, 6.0), (21.5, 5.4), (23.0, 3.4)]
    lo = [(23.4, -1.0), (22.0, -4.4), (19.5, -5.8), (16.5, -5.0), (14.0, -3.2), (11.0, -2.0), (6.0, -1.5), (0.0, -1.3), (-5.0, -1.2)]
    pts = [P(t, o + 0.35 * math.sin(t * 0.7)) for t, o in up] + [P(t, o + 0.35 * math.sin(t * 0.7)) for t, o in lo]
    pts[8] = pts[8] + (1.0,)
    pts[9] = pts[9] + (1.0,)
    det = [('ink', [P(1, 0.4), P(7, -0.4), P(12, 0.6)], 0.9, (0.3, 0.4)),
           ('ink', [P(15, 2.5), P(18, 3.5), P(21, 2.2)], 1.0, (0.3, 0.3)),
           ('ink', [P(15.5, -2.0), P(19, -3.2)], 1.0, (0.3, 0.3)),
           ('deep', cv.ellipse(P(9.0, 1.6), 1.0, 0.7, ca))]
    cv.shape(cv.blob(pts), ROOT, z=z, sd=2.0, hi=0.4, details=det, hatch=0.4, bounce=0.3)
    # kök filizleri (topuzdan dışa kıvrılan sivri kökler)
    for k, (t, o, a, L) in enumerate(((17.0, 5.0, 1.9, 3.4), (21.0, 5.0, 1.1, 3.0), (23.0, 0.5, 0.15, 2.8), (21.0, -5.0, -0.9, 3.2), (16.0, -4.8, -1.7, 2.6))):
        b = P(t, o)
        aa = ca + a
        tip = polar(polar(b, aa, L * 0.6), aa + 0.5, L * 0.5)
        cv.shape(ik.taper_path([cv.W(b), cv.W(polar(b, aa, L * 0.6)), cv.W(tip)], cv.u(1.4), (0.0, 0.9)), ROOT, z=z - 0.05, sd=0.5, ol=0.8)
    # gömülü taşlar
    for k, (t, o, r) in enumerate(((18.5, 2.4, 1.9), (20.6, -2.6, 1.7), (15.5, -1.0, 1.4), (22.2, 1.4, 1.2))):
        c = P(t, o)
        cv.shape(cv.blob([polar(c, ca + a, r * (0.8 + 0.25 * math.sin(a * 3 + k))) for a in [j * 1.05 for j in range(6)]]), STONE, z=z + 0.1 + k * 0.01,
                 sd=0.7, hi=0.3, ol=0.8, details=[('ink', [polar(c, ca + 2.2, r * 0.5), polar(c, ca - 0.6, r * 0.3)], 0.8)])
    # sap sargısı
    cv.shape(ik.isect(cv.blob(pts), cv.poly([P(-5.5, -3), P(-1.2, -3), P(-1.2, 3), P(-5.5, 3)])), ROPE, z=z + 0.05, sd=0.5, ol=0.6,
             details=[('ink', [P(-4.6 + k * 1.1, -1.5), P(-4.2 + k * 1.1, 1.5)], 0.8, (0.1, 0.1)) for k in range(4)])
    return P(19.0, 0.0)


def _fist(cv, h, ang, m, z, open_=0.0):
    """Kalın parmaklı tombul yumruk (gürzü kavrar)."""
    cv.shape(cv.ellipse(h, 3.2, 2.8, ang), m, z=z, sd=1.2, hi=0.3, ol=1.0,
             details=[('ink', [polar(h, ang + 1.9, 1.6), polar(polar(h, ang + 1.9, 1.6), ang, 2.0)], 0.9, (0.2, 0.5)),
                      ('ink', [polar(h, ang + 2.6, 1.0), polar(polar(h, ang + 2.6, 1.0), ang, 1.8)], 0.8, (0.2, 0.5))])
    cv.shape(cv.ellipse(polar(h, ang - 1.4, 2.2), 1.4, 1.1, ang), m, z=z + 0.05, sd=0.5, ol=0.8)   # başparmak


def _rock(cv, c, r, z, ph=0.0):
    pts = []
    for k in range(9):
        a = k / 9 * math.tau + 0.2
        rr = r * (0.86 + 0.18 * math.sin(k * 2.7 + 1.0))
        pts.append(polar(c, a, rr) + ((0.3,) if k == 6 else ()))
    det = [('ink', [polar(c, 2.6, r * 0.7), polar(c, 2.0, r * 0.1), polar(c, 0.4, r * 0.5)], 1.1, (0.3, 0.4)),
           ('ink', [polar(c, -1.0, r * 0.2), polar(c, -1.4, r * 0.75)], 0.9, (0.2, 0.5)),
           ('col', cv.ellipse(polar(c, -2.4, r * 0.45), r * 0.35, r * 0.2, -0.5), (0.42, 0.5, 0.3))]   # yosun lekesi
    cv.shape(cv.blob(pts), ROCK, z=z, sd=r * 0.55, hi=r * 0.12, details=det, hatch=0.4, bounce=0.3, cast=0.8)


def _smear(cv, c, r0, r1, a0, a1, z, alpha=0.7):
    """Vuruş izi: c çevresinde a0 -> a1 hilal (sona doğru kalınlaşır), açık renk + mürekkep kenar."""
    n = 12
    out, inn = [], []
    for i in range(n + 1):
        u = i / n
        a = a0 + (a1 - a0) * u
        w = (r1 - r0) * (u ** 1.3)
        out.append(polar(c, a, r1))
        inn.append(polar(c, a, r1 - w))
    path = cv.blob(out + inn[::-1], closed=True)
    yk.wash(cv, path, SMEAR, alpha, z=z)
    cv.stroke(out[2:], 1.4, z=z + 0.01, col=INK, taper=(0.9, 0.1), alpha=0.8)
    for k in range(3):
        rr = r1 - (r1 - r0) * (0.25 + 0.2 * k)
        cv.stroke([polar(c, a0 + (a1 - a0) * (0.35 + 0.1 * k), rr), polar(c, a1, rr)], 0.9, z=z + 0.02, col=INK, taper=(0.9, 0.2), alpha=0.55)


def _ground_fx(cv, p, c):
    """Çakılma: şok halkası, toz topakları, yer çatlakları, savrulan taş parçaları (dünya, yer y = 0)."""
    k = p['dust']
    if p['crack'] > 0:
        rng = np.random.default_rng(5)
        for i in range(6):
            a = (-1 if i % 2 else 1) * rng.uniform(0.2, 1.0)
            L = (6 + rng.uniform(4, 12)) * p['crack']
            pts = [c]
            x = c[0]
            for j in range(4):
                x += math.copysign(L / 4, a) * rng.uniform(0.7, 1.2)
                pts.append((x, c[1] + rng.uniform(-0.6, 1.2)))
            cv.stroke(pts, 2.2, z=30 + i * 0.01, col=INK, taper=(0.1, 0.9))
            cv.stroke(pts[:3], 0.9, z=30.05, col=(1.0, 0.62, 0.3), taper=(0.2, 0.9), glow=(0.5, 0.22, 0.05), alpha=0.6 * p['crack'])
    if k > 0:
        rr = 8 + 26 * k
        ring = [(c[0] + math.cos(t) * rr, c[1] - 1.2 + math.sin(t) * rr * 0.16) for t in np.linspace(math.pi * 1.05, math.pi * 1.95, 9)]
        cv.stroke(ring, 3.4 * (1.15 - k), z=-30, col=DUST.hi, taper=(0.6, 0.6), alpha=0.9 * (1.1 - k))
        ring2 = [(c[0] + math.cos(t) * rr, c[1] - 0.5 + math.sin(t) * rr * 0.22) for t in np.linspace(0.15, math.pi - 0.15, 9)]
        cv.stroke(ring2, 3.0 * (1.15 - k), z=40, col=DUST.hi, taper=(0.6, 0.6), alpha=0.85 * (1.1 - k))
        for i in range(7):
            s = -1 if i % 2 else 1
            x = c[0] + s * (4 + i * 2.6) * (0.5 + k)
            r = (4.4 + (i % 3) * 1.2) * (0.6 + 0.6 * k) * (1.0 - 0.06 * i)
            yk.puff(cv, (x, c[1] - r * 0.7 - k * i * 0.3), r, DUST, z=(41 if i % 3 == 0 else -28) + i * 0.01, seed=i + 3, alpha=1.0)
    if p['debris'] > 0:
        rng = np.random.default_rng(9)
        d = p['debris']
        for i in range(7):
            vx = rng.uniform(-1.0, 1.0)
            q = (c[0] + vx * 22 * d, c[1] - (rng.uniform(8, 20) * d - 14 * d * d))
            r = rng.uniform(0.6, 1.4)
            cv.shape(cv.blob([polar(q, a + i, r * (1.0 if j % 2 else 0.7)) for j, a in enumerate(np.linspace(0, math.tau, 6, endpoint=False))]),
                     ROCK, z=42 + i * 0.01, sd=0.4, ol=0.7)


def draw(cv, p, ph):
    T = _xf(p)
    hipw = T(HIP)
    # ---------------- arka plan efektleri
    if p['dust'] > 0 or p['crack'] > 0 or p['debris'] > 0:
        _ground_fx(cv, p, (T((14.0, 0.0))[0] + 6, 0.0))
    # ---------------- bacaklar (dünyada; kalça gövdeyle gelir, ayaklar yerde ya da havada toplanmış)
    for side, foot in ((-1, p['fb']), (1, p['ff'])):
        hp = T((HIP[0] + side * 4.0, HIP[1] + 1.5))
        f = (foot[0] + p['hx'], foot[1] + p['hy'])
        _leg(cv, hp, f, -12 if side < 0 else -6, side > 0, p['tuck'])
    u29.body_xf(cv, HIP, p['lean'], p['sx'], p['sy'], (p['hx'] + p['jit'][0], p['hy'] + p['bob'] + p['jit'][1]))
    br = p['breath']
    # ---------------- uzak kol
    shf = _sh(p, SH_F)
    eb, hb = fk_arm(shf, p['b1'], p['b2'], L_UP, L_FO)
    cv.shape(ik.union(bk.muscle(cv, shf, eb, 4.2, 3.4, front=0.8, back=0.6), bk.muscle(cv, eb, hb, 3.4, 2.8, front=0.6, back=0.4)), SKIN_B, z=-20, sd=1.6)
    _fist(cv, hb, p['b1'] + p['b2'] - math.pi / 2 if False else math.atan2(hb[1] - eb[1], hb[0] - eb[0]), SKIN_B, -19.5)
    # ---------------- gürz sırtta (kaya satırı)
    if p['club'] < 0.5:
        _club(cv, (-9.0, -22.0), -1.25, -24, ph)
    # ---------------- gövde: tombul göğüs + yuvarlak göbek
    bx = 1.0 + br * 0.6
    torso = cv.blob([(-8.0, -40.5), (0.0, -43.0), (8.5, -41.0), (12.5 + br * 0.3, -35.0), (15.5 * bx / 1.0 if False else 15.0 + br * 0.9, -27.0),
                     (14.5 + br * 0.9, -19.0), (9.0 + br * 0.4, -12.5), (0.0, -11.0), (-8.5, -12.5), (-12.5, -19.0), (-12.8, -30.0), (-11.5, -37.0)])
    det = [('ink', [(9.5, -33.5), (11.5 + br * 0.6, -27.0), (12.5 + br * 0.8, -21.0)], 1.0, (0.3, 0.6)),            # göbek yayı
           ('ink', [(2.5, -36.0), (6.5, -35.4), (9.5, -36.6)], 1.0, (0.4, 0.4)),                                 # göğüs altı
           ('deep', cv.ellipse((11.6 + br * 0.7, -22.5), 0.7, 0.9)),                                            # göbek deliği
           ('ink', [(-9.0, -24.0), (-7.5, -18.0), (-4.0, -14.0)], 1.0, (0.4, 0.6))]
    cv.shape(torso, SKIN, z=0, sd=3.6, hi=0.6, details=det, bounce=0.35, hatch=0.3, cast=0.8)
    # ---------------- yırtık koyun postu: uzak omuzdan göğse çapraz + kalçada etek
    sash = cv.blob([(-9.5, -41.0), (-3.0, -43.5), (2.0, -40.5), (9.0, -29.0), (10.5, -20.5), (6.0, -19.0), (-1.0, -30.0), (-8.0, -35.5)])
    sdet = [('ink', [(-4.5, -40.0), (1.5, -32.0), (6.0, -23.0)], 0.9, (0.3, 0.5))]
    cv.shape(sash, WOOL, z=3, sd=1.8, hi=0.4, details=sdet)
    hem = yk.ragged((14.5, -7.0), (-12.5, -7.5), 6, 2.6, seed=7, side=-1.0)
    skirt = cv.blob([(-12.8, -18.5), (-4.0, -16.5), (6.0, -16.0), (14.0 + br * 0.5, -17.5), (15.5, -11.0), (14.5, -7.0, 0.0)] + hem +
                    [(-12.5, -7.5, 0.0), (-13.5, -12.0)])
    kdet = cv.fold([(2.0, -15.5), (1.5, -11.0), (0.5, -7.5)], 0.8, 1.0, 1) + cv.fold([(9.0, -15.5), (9.5, -11.0), (10.0, -7.5)], 0.7, 1.0, -1)
    for k in range(6):   # yün kıvırcıkları
        x = -9.0 + k * 4.0
        kdet.append(('ink', [(x, -12.5 + (k % 2)), (x + 1.0, -13.4 + (k % 2)), (x + 1.8, -12.4 + (k % 2))], 0.8, (0.3, 0.3)))
    cv.shape(skirt, WOOL, z=4, sd=2.0, hi=0.4, details=kdet)
    # ip kuşak + kemik muska
    belt = ik.union(cv.capsule((-12.6, -17.0), (2.0, -16.0), 1.15, 1.15), cv.capsule((2.0, -16.0), (14.6 + br * 0.6, -17.6), 1.15, 1.15))
    cv.shape(belt, ROPE, z=5, sd=0.8, hi=0.3, details=[('ink', [(-11.0 + k * 2.2, -18.0), (-10.0 + k * 2.2, -16.0)], 0.8, (0.1, 0.1)) for k in range(12)])
    sw = math.sin(ph) * 0.4 - p['lean'] * 1.5
    knot = (8.5, -16.4)
    cv.stroke([knot, (knot[0] + sw * 0.5, knot[1] + 2.5), (knot[0] + sw, knot[1] + 4.0)], 1.1, z=5.5, col=ROPE.shadow)
    cv.stroke([knot, (knot[0] - 1.0 + sw * 0.5, knot[1] + 3.0)], 1.1, z=5.5, col=ROPE.shadow)
    bc = (knot[0] + sw, knot[1] + 5.8)
    charm = cv.blob([(bc[0] - 1.5, bc[1] - 1.8), (bc[0] + 1.5, bc[1] - 1.8), (bc[0] + 1.8, bc[1] + 0.2), (bc[0] + 0.8, bc[1] + 1.8, 0.0), (bc[0] - 0.8, bc[1] + 1.8, 0.0), (bc[0] - 1.8, bc[1] + 0.2)])
    cv.shape(charm, BONE, z=6, sd=0.6, hi=0.3, ol=0.85, details=[('deep', cv.ellipse((bc[0] - 0.6, bc[1] - 0.4), 0.45, 0.5)), ('deep', cv.ellipse((bc[0] + 0.6, bc[1] - 0.4), 0.45, 0.5))])
    cv.shape(cv.ellipse((knot[0], knot[1]), 1.5, 1.3), ROPE, z=5.6, sd=0.5, ol=0.8)
    # ---------------- baş
    _head(cv, p, ph)
    # ---------------- kaya (elde iken iki elin arasında)
    e, h = _hand(p)
    rk = None
    if p['rock'] > 0.5:
        rk = (p['rx'], p['ry']) if p['rfree'] > 0.5 else add(lerp2(h, hb, 0.5), (0.0, -p['rup'] * 1.4))
        if p['rfree'] > 0.5:
            u29.speed_lines(cv, rk, (1.0, 0.25), n=5, L=12, spread=8, w=1.6, col=DUST.shadow, alpha=0.6, z=-8, seed=3)
        _rock(cv, rk, 11.5, 7.5 if p['rup'] > 2 else (15 if p['rfree'] < 0.5 else 30))
    # ---------------- gürz + yakın kol
    if p['club'] > 0.5:
        _club(cv, h, p['ca'], p['cz'], ph)
    if p['smear'] > 0:
        a0, a1 = p['sm_a']
        _smear(cv, h, CLUB_L - 11, CLUB_L + 3.5, a0, a1, p['cz'] - 0.5, alpha=0.65 * p['smear'])
    shn = _sh(p, SH_N)
    az = p['az']
    arm = ik.union(bk.muscle(cv, shn, e, 4.6, 3.8, front=1.2, back=0.8, at=0.4), bk.muscle(cv, e, h, 3.8, 3.0, front=0.9, back=0.4))
    cv.shape(arm, SKIN, z=az, sd=2.0, hi=0.4, bounce=0.3,
             details=[('ink', [lerp2(shn, e, 0.3), lerp2(shn, e, 0.7)], 1.0, (0.3, 0.6))])
    cv.shape(cv.ellipse(lerp2(e, h, 0.82), 2.9, 3.2, math.atan2(h[1] - e[1], h[0] - e[0])), WOOL, z=az + 0.2, sd=0.8, ol=0.8)   # bilekte post bilezik
    _fist(cv, h, p['ca'] if p['club'] > 0.5 else math.atan2(h[1] - e[1], h[0] - e[0]), SKIN, az + 3)
    if p['sweat'] > 0:   # yorgun: ter damlaları
        for k in range(2):
            q = (-4.0 + k * 3.0, -58.0 + k * 1.5 + 3 * p['sweat'])
            cv.shape(cv.blob([(q[0], q[1] - 1.3, 0.0), (q[0] + 0.7, q[1] + 0.2), (q[0], q[1] + 0.8), (q[0] - 0.7, q[1] + 0.2)]), Ink('#bfe0f0', '#6a8cb0', '#ffffff'),
                     z=40 + k * 0.01, sd=0.3, ol=0.6)
    if p['club'] > 0.5:
        anc = u29.to_world(cv, _club_head(p))
    elif rk is not None:
        anc = u29.to_world(cv, rk)
    else:
        anc = u29.to_world(cv, h)
    mouth = u29.to_world(cv, (15.0, -41.0))
    cv.pop()
    return {'hand': anc, 'mouth': mouth}


def _head(cv, p, ph):
    ht = p['ht']
    hc = (5.0, -49.0)
    ca_, sa_ = math.cos(ht), math.sin(ht)
    piv = (4.0, -41.0)

    def Q(u, v, *t):
        x, y = hc[0] + u - piv[0], hc[1] + v - piv[1]
        return (piv[0] + x * ca_ - y * sa_, piv[1] + x * sa_ + y * ca_) + tuple(t)
    jaw = p['jaw']
    ja = jaw * 0.5

    def J(u, v):   # alt çene: menteşe (-3, 5) çevresinde açılır
        uu, vv = u + 3.0, v - 5.0
        return Q(-3.0 + uu * math.cos(ja) - vv * math.sin(ja), 5.0 + uu * math.sin(ja) + vv * math.cos(ja))
    # ağız içi + dil
    if jaw > 0.1:
        cv.fill(cv.blob([Q(2, 6.0), Q(12.5, 6.5), J(12, 8.5), J(4, 10), J(-1, 8)]), MOUTH_IN, z=9.2)
        cv.fill(cv.blob([J(2, 9.2), J(8, 9.8), J(10.5, 8.6), J(5, 8.2)]), (0.66, 0.24, 0.26), z=9.25)
    # alt çene (tombul, geniş) + iki seyrek alt diş
    lower = cv.blob([J(-7, 4), J(2, 7.0), J(11, 7.2), J(14.0, 8.2), J(13.0, 11.0), J(8, 12.8), J(0, 12.4), J(-6, 9.5)])
    cv.shape(lower, SKIN, z=9.3, sd=1.8, hi=0.25, bounce=0.3, details=[('ink', [J(4, 11), J(8, 11.6), J(11, 10.4)], 0.9, (0.3, 0.5))])
    for u in (4.5, 10.5):
        cv.shape(cv.blob(bk.spike_pts(J(u - 1.1, 7.6), J(u + 1.1, 7.6), J(u + 0.3, 5.0), 0.3)), BONE, z=9.6, sd=0.5, hi=0.2, ol=0.8)
    # kafatası: iri, yuvarlak, kel
    skull = cv.blob([Q(-12, 1), Q(-12.5, -6), Q(-9, -11), Q(-2, -13.0), Q(6, -12.5), Q(11, -9.5), Q(13.0, -5), Q(13.2, -1.5),
                     Q(15.0, 1.5), Q(15.2, 3.6, 0.6), Q(13.0, 5.2), Q(10, 6.0), Q(2, 5.8), Q(-4, 7.0), Q(-9.5, 5.5)])
    det = [('deep', cv.blob([Q(0.0, -6.5), Q(6, -9.0), Q(11.5, -6.5), Q(12.0, -1.5), Q(9, 1.4), Q(2, 1.4), Q(-0.5, -2)])),
           ('ink', [Q(12.4, 1.5), Q(11.0, 3.4), Q(12.0, 5.0)], 1.2, (0.2, 0.4)),
           ('ink', [Q(9, 3.2), Q(5, 4.5), Q(1.5, 3.8)], 0.9, (0.3, 0.6)),
           ('ink', [Q(-8, -1), Q(-7, 2.5), Q(-4.5, 5)], 1.0, (0.3, 0.3)),
           ('hi', cv.ellipse(Q(-3.5, -9.8), 3.0, 1.2, ht - 0.25)),
           ('col', cv.ellipse(Q(11.0, 2.2), 1.6, 1.0, ht), (0.86, 0.48, 0.40))]   # al yanak
    cv.shape(skull, SKIN, z=9.5, sd=3.0, hi=0.55, details=det, cast=1.0, bounce=0.35, hatch=0.3)
    # boynuz tomurcukları
    for (u, v, a, s, zz) in ((-1.5, -12.6, -1.85, 0.85, 9.4), (5.5, -12.8, -1.45, 1.0, 9.8)):
        b0, b1 = Q(u - 1.5 * s, v + 0.6), Q(u + 1.5 * s, v + 0.6)
        tip = Q(u + math.cos(a) * 3.6 * s, v + math.sin(a) * 3.6 * s)
        cv.shape(cv.blob(bk.spike_pts(b0, b1, tip, 0.5)), BONE, z=zz, sd=0.6, hi=0.3, ol=0.9,
                 details=[('ink', [lerp2(b0, tip, 0.4), lerp2(b1, tip, 0.4)], 0.8, (0.1, 0.1))])
    # kulak (küçük, yuvarlak)
    cv.shape(cv.blob([Q(-7.5, -3.5), Q(-10.5, -5.5), Q(-12.0, -2.0), Q(-10.0, 1.5), Q(-7.5, 0.5)]), SKIN_D, z=9.6, sd=1.0, hi=0.2,
             details=[('ink', [Q(-9.0, -3.2), Q(-10.0, -0.8)], 0.9)])
    # üst dişler: seyrek (aralıklı, biri eksik)
    if jaw > 0.1:
        for k, u in enumerate((3.5, 8.0, 11.0)):
            ln = 2.4 if k != 1 else 1.6
            cv.fill(cv.blob([Q(u - 1.0, 5.8), Q(u + 1.0, 5.8), Q(u + 0.2, 5.8 + ln)]), BONE.base, z=9.55)
    # TEK GÖZ: iri, kehribar, ışıyan
    ec = Q(6.0, -3.2)
    lid = p['lid']
    er = 5.6
    eye = cv.ellipse(ec, er, er * (1.0 - 0.8 * lid), ht)
    vein = [('stroke', [Q(1.0 + k * 0.3, -3.6 + (k - 1.5) * 2.0), Q(2.6, -3.4 + (k - 1.5) * 1.2)], 0.7, (0.8, 0.24, 0.2), (0.1, 0.8)) for k in range(4)]
    cv.shape(eye, EYE_W, z=10.0, sd=1.2, hi=0.0, ol=1.1, details=vein)
    if lid < 0.85:
        g = 0.45 + 0.6 * p['glow']
        ic = Q(7.4 + 0.5 * p['glow'], -3.0)
        ir = 3.4 * (1.0 - 0.5 * lid)
        yk.glow_soft(cv, ic, 6.0 + 3.0 * p['glow'], IRIS_GLOW, z=10.04, alpha=0.45 * g)
        cv.fill(cv.ellipse(ic, 3.4, ir, ht), IRIS, z=10.05, glow=tuple(c * g for c in IRIS_GLOW))
        cv.fill(cv.ellipse(add(ic, (-0.5, -0.5)), 2.0, ir * 0.6, ht), IRIS_HOT, z=10.06, glow=tuple(c * g for c in IRIS_HOT))
        cv.fill(cv.ellipse(add(ic, (0.4, 0.1)), 0.9, ir * 0.8, ht), (0.08, 0.04, 0.03), z=10.07)
        cv.fill(cv.ellipse(add(ic, (-1.4, -1.5)), 0.8, 0.6), (1.0, 1.0, 0.95), z=10.08, glow=(0.6, 0.55, 0.4))
    # göz kapağı + AĞIR kaş çıkıntısı
    br = p['brow']
    upper = cv.blob([Q(0.5, -4.6 + 1.5 * lid), Q(6, -8.6 + br * 1.4 + 5.6 * lid), Q(11.6, -5.0 + br * 1.8 + 2.0 * lid),
                     Q(11.4, -7.0 + br * 1.2), Q(6, -10.2 + br * 1.2), Q(0.0, -6.6)])
    cv.shape(upper, SKIN_D, z=10.2, sd=0.8, ol=1.0)
    brow = cv.blob([Q(-2.0, -7.6 + br * 0.4), Q(3.5, -11.6 + br * 1.0), Q(10, -10.8 + br * 2.0), Q(14.2, -6.8 + br * 2.0),
                    Q(13.4, -5.2 + br * 1.8), Q(8.5, -8.6 + br * 2.0), Q(2.5, -9.2 + br * 0.8)])
    cv.shape(brow, SKIN, z=10.3, sd=1.4, hi=0.4, cast=0.9, details=[('ink', [Q(2.5, -10.6 + br), Q(8, -10.0 + br * 1.8), Q(12.5, -7.4 + br * 2.0)], 0.9, (0.2, 0.4))])
    cv.fill(cv.ellipse(Q(14.0, 2.6), 1.0, 0.6, ht + 0.3), INK, z=10.4)   # burun deliği


# ------------------------------------------------------------ animasyon tabloları
S2 = math.tau


def _k(t, keys):
    return pose_at(t, keys, base=REST)


def _idle(t):
    s = math.sin(S2 * t)
    blink = 1.0 if int(round(t * 8)) == 5 else 0.0
    return dict(REST, bob=0.8 + 0.8 * s, breath=0.5 + 0.5 * s, sy=1.0 - 0.015 * s, sx=1.0 + 0.012 * s, lean=0.03 + 0.02 * s,
                a1=-0.35 + 0.05 * s, a2=-2.2 - 0.04 * s, ca=-2.35 + 0.05 * s, b1=0.2 - 0.06 * s, jaw=0.22 + 0.18 * max(0.0, s),
                ht=0.03 * s, lid=0.85 * blink, glow=0.55 + 0.25 * s)


def _move(t):
    """Paytak, yeri döven yürüyüş: her adımda gövde basan ayağa yatar (yan sallantı), topuk vuruşunda çöker."""
    S = 8.8

    def foot(phv, home):
        phv %= 1.0
        st = 0.58
        if phv < st:
            return (home + S - 2 * S * phv / st, 0.0)
        u = (phv - st) / (1 - st)
        e = u * u * (3 - 2 * u)
        return (home - S + 2 * S * e, -math.sin(math.pi * u) * 5.0)
    ff, fb = foot(t, 3.0), foot(t + 0.5, -2.0)
    w = math.cos(4 * math.pi * (t - 0.06))
    sw = math.cos(S2 * t)
    return dict(REST, bob=1.6 + 1.6 * w, lean=0.12 + 0.07 * sw, sy=1.0 - 0.03 * w, sx=1.0 + 0.025 * w, ff=ff, fb=fb, hx=0.0,
                a1=-0.25 - 0.18 * sw, a2=-2.15, ca=-2.3 - 0.12 * sw, b1=0.25 + 0.45 * sw, b2=-0.6, jaw=0.3 + 0.15 * max(0.0, w),
                breath=0.5 + 0.4 * w, ht=0.04 * sw, glow=0.7, brow=0.3)


_HURT = [(0.0, dict(lean=-0.28, hx=-2.5, bob=1.5, sx=1.05, sy=0.95, ht=-0.22, jaw=0.75, lid=0.55, brow=-0.6, a1=0.3, a2=-1.6, ca=-1.9, b1=-0.4, b2=-0.8,
                    jit=(-1.2, 0.0), glow=0.3), 'l'),
         (0.5, dict(lean=-0.18, hx=-3.5, bob=1.0, sx=1.0, sy=1.0, ht=-0.12, jaw=0.5, lid=0.3, brow=-0.3, a1=0.0, a2=-1.9, ca=-2.1, b1=-0.1, jit=(-0.6, 0.0)), 'o'),
         (1.0, dict(lean=-0.04, hx=-3.0, bob=0.6, ht=0.0, jaw=0.25, lid=0.0, brow=0.0, a1=-0.3, a2=-2.2, ca=-2.35, b1=0.2, b2=-0.6, jit=(0.0, 0.0), glow=0.6), 'io')]

# atk_slam: çömel -> sıçra (havada, gürz + iki kol baş üstünde) -> göbek ve gürzle çakıl -> saplan, ağır doğrul
TUCK_F, TUCK_B = (8.0, -6.0), (-6.0, -7.0)
_SLAM_TS = [0.0, 0.07, 0.15, 0.24, 0.34, 0.44, 0.5, 0.6, 0.75, 0.88]
_SLAM = [
    (0.0, dict(), 'l'),
    (0.07, dict(bob=4.0, lean=0.22, sy=0.92, sx=1.06, a1=0.6, a2=-1.6, ca=-2.6, b1=0.7, b2=-0.9, jaw=0.4, brow=0.6, glow=0.8, ht=0.1), 'o'),
    (0.15, dict(bob=7.5, lean=0.32, sy=0.84, sx=1.12, a1=1.4, a2=-1.2, ca=-2.9, cz=7, b1=1.2, b2=-0.8, jaw=0.55, brow=1.0, glow=1.0, ht=0.16), 'o'),
    # kalkış: yukarı uzar, ayaklar yerden kesilir
    (0.24, dict(bob=0.0, hy=-12.0, lean=-0.05, sy=1.1, sx=0.93, ff=(9.0, -8.0), fb=(-5.0, -6.0), tuck=0.6, a1=3.0, a2=-0.4, ca=-2.5, cz=7,
                az=8, shr=1.2, b1=3.0, b2=-0.4, jaw=0.85, brow=1.0, glow=1.0, ht=-0.12), 'o'),
    # DORUK (W, "!" süresince tutulur): ~20 birim havada, iki kol ve gürz baş üstünde, bacaklar toplanmış
    (0.34, dict(hy=-18.0, lean=-0.12, sy=1.04, sx=0.97, ff=(9.0, -19.0), fb=(-5.0, -18.0), tuck=1.0, a1=3.6, a2=-0.3, ca=-2.55, cz=7, az=8, shr=0.8,
                b1=3.4, b2=-0.15,
                jaw=1.0, brow=1.0, glow=1.0, ht=-0.18), 'o'),
    # düşüş: gövde öne kapanır, gürz başın üstünden öne iner
    (0.44, dict(hy=-11.0, lean=0.35, sy=1.08, sx=0.95, ff=(12.0, -10.0), fb=(-2.0, -11.0), tuck=0.8, a1=2.3, a2=-0.2, ca=-0.9, cz=22, az=20, shr=0.6,
                b1=2.3, b2=-0.3,
                jaw=0.9, ht=0.1, smear=1.0, sm_a=(-2.6, -0.9)), 'i'),
    # TEMAS (C): göbek ve gürz yere çakılır, gövde ezilir; şok halkası, toz, çatlak
    (0.5, dict(hy=0.0, bob=9.0, lean=0.62, shr=0.0, sy=0.82, sx=1.16, ff=(13.0, 0.0), fb=(-7.0, 0.0), tuck=0.0, a1=1.1, a2=0.1, ca=-0.6, cz=22, b1=1.3, b2=0.2,
               jaw=1.0, brow=1.0, ht=0.2, smear=0.6, sm_a=(-1.6, -0.4), dust=0.5, crack=0.7, debris=0.3, glow=1.0, jit=(0.6, 0.0)), 'i'),
    (0.6, dict(bob=10.0, lean=0.66, sy=0.86, sx=1.12, a1=0.95, ca=-0.95, smear=0.0, dust=0.75, crack=1.0, debris=0.75, jaw=0.7, jit=(0.0, 0.0)), 'o'),
    # saplanmış: göbek yerde, ağır soluk
    (0.75, dict(bob=9.0, lean=0.6, sy=0.9, sx=1.08, dust=0.95, crack=1.0, debris=0.0, jaw=0.5, brow=0.4, lid=0.4, glow=0.5, sweat=0.4, breath=1.0), 'o'),
    (0.88, dict(bob=5.0, lean=0.38, sy=0.96, sx=1.03, a1=0.6, a2=-1.0, ca=-0.6, cz=8, b1=0.6, b2=-0.6, dust=1.0, crack=0.8, jaw=0.4, brow=0.2, lid=0.2,
                sweat=0.8, ff=(10.0, 0.0), fb=(-6.0, 0.0)), 'io'),
    (1.0, dict(bob=1.0, lean=0.05, sy=1.0, sx=1.0, a1=-0.35, a2=-2.2, ca=-2.35, b1=0.25, b2=-0.6, dust=0.0, crack=0.0, jaw=0.15, lid=0.0, sweat=0.0,
               ff=(7.0, 0.0), fb=(-6.0, 0.0)), 'io')]

# atk_flurry: baş üstü -> yan -> baş üstü üç hızlı gürz vuruşu
_FLURRY_TS = [0.0, 0.14, 0.28, 0.32, 0.42, 0.5, 0.6, 0.68, 0.82, 0.91]
_OVER = dict(a1=3.45, a2=-0.2, ca=-2.75, cz=7, az=8, shr=1.4, lean=-0.18, bob=1.5, b1=3.2, b2=-0.3, jaw=0.7, brow=1.0, glow=1.0, ht=-0.12)
_HIT_DOWN = dict(a1=1.15, a2=0.1, ca=-0.1, cz=22, az=20, shr=0.0, lean=0.38, bob=5.0, b1=0.6, b2=-0.3, jaw=1.0, brow=1.0, ht=0.12, ff=(10.0, 0.0), fb=(-7.0, 0.0))
_FLURRY = [
    (0.0, dict(), 'l'),
    (0.14, dict(a1=2.4, a2=-1.0, ca=-2.5, cz=7, az=20, shr=0.6, lean=-0.08, bob=2.0, b1=1.0, b2=-0.8, jaw=0.4, brow=0.6, glow=0.8, sy=0.97, sx=1.03), 'o'),
    (0.28, dict(_OVER, sy=1.04, sx=0.97), 'o'),                                                   # derin kurulma (W)
    (0.32, dict(_HIT_DOWN, smear=1.0, sm_a=(-2.4, -0.15), sy=0.94, sx=1.06), 'i'),                  # 1. vuruş: baş üstünden (C)
    (0.42, dict(a1=0.9, a2=-2.0, ca=-2.95, cz=-16, lean=-0.1, bob=2.5, b1=0.9, jaw=0.6, smear=0.0, ht=-0.05, sy=1.0, sx=1.0), 'o'),   # yana kurul
    (0.5, dict(a1=1.4, a2=0.0, ca=0.05, cz=22, lean=0.25, bob=3.5, b1=0.4, b2=-0.4, jaw=1.0, ht=0.08, smear=1.0, sm_a=(-3.0, 0.1),
               ff=(11.0, 0.0), fb=(-6.0, 0.0)), 'i'),                                              # 2. vuruş: yandan savuruş
    (0.6, dict(_OVER, smear=0.0, sy=1.05, sx=0.96), 'o'),
    (0.68, dict(_HIT_DOWN, bob=6.0, lean=0.45, smear=1.0, sm_a=(-2.4, -0.15), dust=0.35, sy=0.92, sx=1.08), 'i'),   # 3. vuruş: en ağır
    (0.82, dict(a1=1.0, a2=-0.3, ca=0.0, cz=22, lean=0.3, bob=3.5, smear=0.0, dust=0.75, jaw=0.5, brow=0.4, sy=1.0, sx=1.0), 'o'),
    (1.0, dict(a1=-0.35, a2=-2.2, ca=-2.35, cz=8, lean=0.0, bob=0.5, b1=0.25, b2=-0.6, dust=0.0, jaw=0.15, brow=0.0, ht=0.0, ff=(7.0, 0.0),
               fb=(-6.0, 0.0)), 'io')]

# atk_boulder: yerden kaya sök -> baş üstüne kaldır -> ileri fırlat (gürz sırtta)
_BOULDER_TS = [0.0, 0.12, 0.26, 0.4, 0.52, 0.58, 0.7, 0.85]
_BOULDER = [
    (0.0, dict(club=0.0, rock=0.0, a1=0.3, a2=-0.4, b1=0.1, b2=-0.4), 'l'),
    # eğilip kayayı kavrar (yerden toz, kopan kesekler)
    (0.12, dict(club=0.0, rock=1.0, bob=6.0, lean=0.7, sy=0.92, sx=1.06, a1=0.15, a2=0.25, b1=0.0, b2=0.25, jaw=0.5, brow=0.8, glow=0.8, dust=0.15,
                debris=0.25, ht=0.25), 'o'),
    # söker: göğse çeker
    (0.26, dict(bob=3.0, lean=0.15, sy=1.0, sx=1.0, a1=1.3, a2=-1.3, b1=1.35, b2=-1.1, jaw=0.8, brow=1.0, glow=1.0, dust=0.45, debris=0.6, ht=-0.05), 'o'),
    # baş üstüne kaldırır (W, derin kurulma): geriye yaslanır
    (0.4, dict(bob=1.0, lean=-0.14, sy=1.05, sx=0.97, a1=3.3, a2=-0.1, b1=3.3, b2=-0.1, az=8, shr=1.6, rup=6.0, jaw=1.0, brow=1.0, ht=-0.2, dust=0.8, debris=0.0,
               ff=(9.0, 0.0), fb=(-8.0, 0.0)), 'o'),
    (0.52, dict(bob=2.0, lean=0.05, a1=2.6, a2=-0.2, b1=2.6, b2=-0.2, az=20, shr=0.8, rup=4.0, ht=-0.05, dust=0.0), 'i'),
    # TEMAS (C): fırlatır — kaya ellerden ayrılır, kollar öne uzanır
    (0.58, dict(rfree=1.0, rx=29.0, ry=-50.0, shr=0.0, rup=0.0, bob=4.0, lean=0.42, sy=0.95, sx=1.05, a1=1.75, a2=-0.05, b1=1.65, b2=-0.05, jaw=1.0, ht=0.12,
                ff=(12.0, 0.0), fb=(-7.0, 0.0)), 'i'),
    (0.7, dict(rock=0.0, rfree=0.0, bob=3.5, lean=0.36, a1=1.3, a2=0.0, b1=1.2, b2=0.0, jaw=0.6, brow=0.5), 'o'),
    (1.0, dict(bob=0.5, lean=0.05, sy=1.0, sx=1.0, a1=0.3, a2=-0.4, b1=0.1, b2=-0.4, jaw=0.2, brow=0.0, ht=0.0, ff=(7.0, 0.0), fb=(-6.0, 0.0)), 'io')]


def _row(frames, fps, loop, pose, ts=None, mk=None, vx=None):
    d = dict(frames=frames, fps=fps, loop=loop, pose=pose, ts=ts, mk=mk)
    if vx:
        d['vx'] = vx
    return d


def _nl(keys):
    return lambda t: _k(t, keys)


ROWS = None


def anims_for(var='tepegoz_yavrusu'):
    global ROWS
    if ROWS is None:
        ROWS = {
            'idle': _row(8, 8, True, _idle),
            'move': _row(8, 14, True, _move, vx=55.0),
            'hurt': _row(3, 12, False, _nl(_HURT)),
            'atk_slam': _row(10, 10, False, _nl(_SLAM), ts=_SLAM_TS, mk=[0.34, 0.5, 0.62]),
            'atk_flurry': _row(10, 11, False, _nl(_FLURRY), ts=_FLURRY_TS, mk=[0.28, 0.32, 0.82]),
            'atk_boulder': _row(8, 9, False, _nl(_BOULDER), ts=_BOULDER_TS, mk=[0.4, 0.58, 0.7]),
        }
    return ROWS


def durum_for(var='tepegoz_yavrusu'):
    d = {"idle": "idle", "chase": "move", "recover": "idle", "evade": "move", "_hurt": "hurt", "_hurt_big": "hurt", "_break": "hurt"}
    for m in ('slam', 'flurry', 'boulder'):
        for ph in ('windup', 'act', 'recover'):
            d[ph + '/' + m] = 'atk_' + m
    return d


def frame_time(row, i):
    if row['ts']:
        return row['ts'][i]
    if row['loop']:
        return i / row['frames']
    return i / max(1, row['frames'] - 1)


SHADE = dict(outer=0.55, rim=0.65, rim_col=(0.72, 0.8, 1.0), rim_dir=(0.6, -0.8), rim_w=1.4, form=(5.0, (0.78, 0.74, 0.88)))


def render_frame(anim, i, var='tepegoz_yavrusu', ss=3):
    row = anims_for(var)[anim]
    tt = frame_time(row, i)
    p = dict(row['pose'](tt))
    ph = tt * math.tau * (2 if row['loop'] else 1) + i * 0.9
    cv = yg.bake_xf(u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss))
    info = draw(cv, p, ph)
    rgba, _nm, em = cv.finish(**SHADE)
    return rgba, None, em, info
