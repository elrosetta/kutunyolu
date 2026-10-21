"""v39: Kor Solucanı (kimlik kor_solucani; Tamu / Erlik'in tamu katı, yapay zekâ "burrower") — mürekkep-cel.

Dev lav solucanı: kara bazalt / obsidyen halka zırh plakaları, plakaların arasındaki eklemlerde ışıyan erimiş turuncu
kor (ışır), öne bakan halka biçimli ağız (içe dönük dişler, ateşli gırtlak), başın arkasında körelmiş boynuz dikenleri,
sırtta küçük diken sırası, yükselen sıcak kıvılcımları. Çoğu zaman yarı yarıya topraktan çıkmıştır: gövdenin kökü
AYAK ORİJİNİNDE yerin içine girer (yer çizgisinin altı silinir, kökte kızgın çatlaklı moloz halkası).

Gövde: kökten başa kübik Bezier omurga (kök dik çıkar, baş `ha` doğrultusuna bakar); halkalar eşit yay aralığıyla
dizilir, üstüne dalga (yılankavi kıvrım) biner. Satırlar ve durum yer_cucesi ile aynıdır:
  idle 6, move 8 (toprağı yararak kayar, vx 60), hurt 3, atk_pick 8 (yer boyunca ileri atılan ısırık; mk),
  atk_throw 8 (ağızdan kavisli lav topu tükürür; top TEMAS karesinde ağızdan çıkar; mk), dig 6 (döngüsüz: baş önde
  toprağa dalar; son kareler yalnızca kızgın çatlaklı tümsek), burrow 4 (döngü: ilerleyen ışıyan çatlaklı tümsek),
  atk_emerge 8 (mk; tümsek şişer ve kızarır, temas = ağız önde yerden fışkırır, lav sıçrar, taşlar uçar).
Çapalar: 'mouth' = ağız merkezi (her karede), 'hand' = aynı nokta.
Hücre 88 x 64 dünya, ayak (36, 58), doku 4.
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import lerp2
import yaratik_ink_kit as yk
import ucan_v29 as u29
import y39_yer_cucesi as yc

TEX = 4.0
CELL = (352, 256)       # dünya 88 x 64
FEET = (144, 232)       # dünya (36, 58)

OBS = Ink('#3e353e', '#18131a', '#7c6c7a', '#0a080c', name='obsidyen plaka')
OBS_H = Ink('#4a3c42', '#1e161c', '#8e7c84', '#0c090c', name='baş plakası')
BASALT = Ink('#4a4044', '#221c20', '#76686a', '#110d10', name='bazalt')
TOOTH = Ink('#eadcc0', '#8e7a5e', '#fff8e0', '#4a3a2a', name='diş')
HORN = Ink('#2a2228', '#100c10', '#6a5a62', '#060406', name='boynuz')
LAVA = (1.0, 0.52, 0.12)
LAVA_HOT = (1.0, 0.88, 0.45)
LAVA_G = (1.0, 0.34, 0.03)
THROAT = (0.62, 0.08, 0.03)
ASH = Ink('#5a4a46', '#2a2022', '#86726a', '#140e0e', name='kül toprağı')
ASH_D = Ink('#3e3234', '#1c1418', '#5e4e4c', '#0c080a', name='koyu kül')


def _d(a):
    return (math.cos(a), math.sin(a))


def _bez(p0, p1, p2, p3, t):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


def spine(p):
    """Omurga noktaları (kökten başa), eşit yay aralıklı; dalga dikine eklenir. Döner: [(nokta, teğet, u)]."""
    B0 = (p['bx'], 6.0)
    H = p['H']
    D = _d(p['ha'])
    b1 = _d(p['ba'])
    P1 = (B0[0] + b1[0] * p['k1'], B0[1] + b1[1] * p['k1'])
    P2 = (H[0] - D[0] * p['k2'], H[1] - D[1] * p['k2'])
    ts = np.linspace(0, 1, 200)
    pts = np.array([_bez(B0, P1, P2, H, t) for t in ts])
    seg = np.hypot(*(pts[1:] - pts[:-1]).T)
    L = np.concatenate([[0], np.cumsum(seg)])
    step = 0.62 * p['r0'] * p['rs']
    n = max(3, int(L[-1] / step))
    out = []
    for k in range(n + 1):
        s = L[-1] * k / n
        j = min(len(ts) - 2, int(np.searchsorted(L, s)))
        q = pts[j]
        tg = pts[j + 1] - pts[max(0, j - 1)]
        tg = tg / (np.hypot(*tg) + 1e-9)
        u = k / n
        nrm = (-tg[1], tg[0])
        w = p['wave'] * math.sin(p['ph'] * 1.0 + u * 5.0) * math.sin(math.pi * u)
        out.append(((q[0] + nrm[0] * w, q[1] + nrm[1] * w), (tg[0], tg[1]), u))
    return out, L[-1] / n


def plate(cv, P, T, r, hl, z, mat, glow_k, seed, crack=False):
    """Halka zırh plakası: teğete dik basık fıçı; ön kenarda mürekkep halka çizgisi, sırtta küçük diken."""
    N = (-T[1], T[0])
    Q = lambda a, b, *e: (P[0] + T[0] * a + N[0] * b, P[1] + T[1] * a + N[1] * b) + e
    path = cv.blob([Q(-hl, -r * 0.92), Q(hl * 0.2, -r), Q(hl, -r * 0.88), Q(hl * 1.25, 0.0), Q(hl, r * 0.88), Q(hl * 0.2, r), Q(-hl, r * 0.92), Q(-hl * 1.1, 0.0)])
    det = [('ink', [Q(hl * 0.55, -r * 0.85), Q(hl * 0.85, 0.0), Q(hl * 0.55, r * 0.85)], 0.8, (0.2, 0.2)),
           ('stroke', [Q(-hl * 0.4, -r * 0.75), Q(hl * 0.3, -r * 0.82)], 1.0, mat.hi, (0.3, 0.5))]
    if crack:   # plakada ışıyan çatlak
        rng = np.random.default_rng(seed)
        b = Q(rng.uniform(-0.4, 0.2) * hl, rng.uniform(-0.3, 0.5) * r)
        e1 = (b[0] + rng.uniform(-1.5, 1.5), b[1] + rng.uniform(-1.5, 1.5))
        e2 = (e1[0] + rng.uniform(-1.5, 1.5), e1[1] + rng.uniform(0.5, 2.0))
        det.append(('stroke', [b, e1, e2], 1.6, (0.06, 0.04, 0.05), (0.2, 0.8)))
        det.append(('stroke', [b, e1, e2], 0.8, LAVA, (0.2, 0.8)))
        cv.stroke([b, e1, e2], 0.7, z=z + 0.05, col=LAVA, taper=(0.2, 0.8), glow=LAVA_G, alpha=0.0)
    cv.shape(path, mat, z=z, sd=r * 0.5, hi=0.4, ol=1.0, details=det, bounce=0.25)
    # sırt dikeni (dorsal yan = teğetin -90°'si)
    Dn = (T[1], -T[0])
    if Dn[1] > 0:   # sırt aşağı bakıyorsa diken öbür yanda
        Dn = (-Dn[0], -Dn[1])
    sb = (P[0] + Dn[0] * r * 0.85, P[1] + Dn[1] * r * 0.85)
    st = (P[0] + Dn[0] * (r + 2.2) - T[0] * 1.2, P[1] + Dn[1] * (r + 2.2) - T[1] * 1.2)
    cv.shape(cv.blob([(sb[0] - T[0] * 1.2, sb[1] - T[1] * 1.2, 0.0), (st[0], st[1], 0.0), (sb[0] + T[0] * 1.2, sb[1] + T[1] * 1.2, 0.0)]),
             HORN, z=z - 0.02, sd=0.3, hi=0.2, ol=0.8)


def head(cv, H, D, r, jaw, z, glow_k, ph):
    """Baş: arkada boynuzlu kafa plakası, önde halka ağız (içe dönük dişler, ateşli gırtlak). Döner ağız merkezi."""
    N = (-D[1], D[0])
    Q = lambda a, b, *e: (H[0] + D[0] * a + N[0] * b, H[1] + D[1] * a + N[1] * b) + e
    # kafa: geriye doğru genişleyen yüzük plaka
    skull = cv.blob([Q(-6.5, -r * 1.0), Q(-2.0, -r * 1.08), Q(0.6, -r * 1.0), Q(1.2, 0.0), Q(0.6, r * 1.0), Q(-2.0, r * 1.08), Q(-6.5, r * 1.0), Q(-7.2, 0.0)])
    sdet = [('ink', [Q(-4.4, -r * 0.95), Q(-4.0, 0.0), Q(-4.4, r * 0.95)], 0.9, (0.2, 0.2)),
            ('stroke', [Q(-5.5, -r * 0.82), Q(-0.8, -r * 0.9)], 1.1, OBS_H.hi, (0.3, 0.5))]
    for k in range(3):   # körelmiş kor gözcükler
        q = Q(-2.6 + k * 0.4, -r * (0.55 - k * 0.35))
        sdet.append(('col', cv.ellipse(q, 0.55, 0.45), LAVA_HOT))
    cv.shape(skull, OBS_H, z=z, sd=r * 0.5, hi=0.45, ol=1.0, details=sdet)
    for k in range(3):
        q = Q(-2.6 + k * 0.4, -r * (0.55 - k * 0.35))
        yk.glow_soft(cv, q, 1.2, LAVA_G, z=z + 0.05, alpha=0.6 * glow_k)
        cv.fill(cv.ellipse(q, 0.4, 0.35), LAVA_HOT, z=z + 0.06, glow=LAVA_G)
    # körelmiş boynuz dikenleri (sırt yanında, geriye kıvrık)
    Dn = (D[1], -D[0])
    if Dn[1] > 0.2:
        Dn = (-Dn[0], -Dn[1])
    for k, (a, ln, zz) in enumerate(((-5.4, 4.6, z - 0.2), (-2.8, 3.6, z + 0.2), (-0.8, 2.4, z + 0.2))):
        b = (H[0] + D[0] * a + Dn[0] * r * 0.9, H[1] + D[1] * a + Dn[1] * r * 0.9)
        tip = (b[0] + Dn[0] * ln - D[0] * ln * 0.8, b[1] + Dn[1] * ln - D[1] * ln * 0.8)
        mid = lerp2(b, tip, 0.5)
        mid = (mid[0] + D[0] * 0.6, mid[1] + D[1] * 0.6)
        cv.shape(ik.taper_path([cv.W(b), cv.W(mid), cv.W(tip)], cv.u(1.9), prof=lambda u: max(0.06, 1 - 0.94 * u)), HORN, z=zz, sd=0.4, hi=0.3, ol=0.85)
    # halka ağız: izleyiciye yarı dönük elips (açıldıkça genişler)
    mc = Q(1.0 + 0.6 * jaw, 0.0)
    ry = r * (0.82 + 0.2 * jaw)
    rx = r * (0.22 + 0.45 * jaw)
    ang = math.atan2(N[1], N[0])
    lip = cv.ellipse(mc, ry, rx + 1.1, ang)
    cv.shape(lip, BASALT, z=z + 0.5, sd=0.8, hi=0.3, ol=1.0)
    inner = cv.ellipse(mc, ry - 1.1, rx, ang)
    cv.fill(inner, THROAT, z=z + 0.6, glow=(0.5, 0.08, 0.0))
    # gırtlak ateşi: içeride (geride) parlak çekirdek
    gc = (mc[0] - D[0] * 0.6, mc[1] - D[1] * 0.6)
    cv.fill(cv.ellipse(gc, (ry - 1.1) * 0.62, rx * 0.6, ang), LAVA, z=z + 0.65, glow=LAVA_G)
    cv.fill(cv.ellipse(gc, (ry - 1.1) * 0.3, max(0.3, rx * 0.3), ang), LAVA_HOT, z=z + 0.7, glow=LAVA_HOT)
    yk.glow_soft(cv, gc, ry * (1.0 + 0.6 * jaw), LAVA_G, z=z + 0.72, alpha=(0.45 + 0.35 * jaw) * glow_k)
    # içe dönük dişler halkada
    nt = 12
    for k in range(nt):
        a = k / nt * math.tau + 0.13
        ca, sa = math.cos(a), math.sin(a)
        rim = (mc[0] + N[0] * ca * (ry - 0.9) + D[0] * sa * (rx - 0.2), mc[1] + N[1] * ca * (ry - 0.9) + D[1] * sa * (rx - 0.2))
        tip = lerp2(rim, gc, 0.45 + 0.1 * (k % 2))
        side = (N[0] * -sa * 0.9 + D[0] * ca * 0.4, N[1] * -sa * 0.9 + D[1] * ca * 0.4)
        far = sa < 0
        m = TOOTH.darker(0.7) if far else TOOTH
        cv.shape(cv.blob([(rim[0] + side[0], rim[1] + side[1], 0.0), (tip[0], tip[1], 0.0), (rim[0] - side[0], rim[1] - side[1], 0.0)]),
                 m, z=z + (0.66 if far else 0.8) + k * 0.001, sd=0.2, hi=0.15, ol=0.6)
    return mc


def glob(cv, c, r, z, ph, vel=(1.0, 0.0)):
    """Lav topu: kabuklu parlak damla + arkasında damla izi."""
    v = u29.norm2(vel)
    for k in range(3):
        q = (c[0] - v[0] * (2.2 + k * 1.8) * r * 0.5, c[1] - v[1] * (2.2 + k * 1.8) * r * 0.5)
        rr = r * (0.45 - k * 0.12)
        cv.fill(cv.ellipse(q, rr, rr), LAVA, z=z - 0.1, glow=LAVA_G)
    cv.shape(cv.ellipse(c, r, r * 0.9, math.atan2(v[1], v[0])), Ink('#ff8a24', '#c23a08', '#ffe08a', '#6a1404'), z=z, sd=r * 0.4, hi=0.4, ol=0.9,
             glow=LAVA_G, details=[('col', cv.blob([(c[0] - r * 0.6, c[1] + r * 0.1), (c[0] - r * 0.1, c[1] - r * 0.3), (c[0] + r * 0.1, c[1] + r * 0.4)]), (0.25, 0.1, 0.08)),
                                    ('col', cv.ellipse((c[0] + r * 0.2, c[1] - r * 0.25), r * 0.35, r * 0.28), LAVA_HOT)])
    yk.glow_soft(cv, c, r * 2.4, LAVA_G, z=z + 0.1, alpha=0.7)


# ------------------------------------------------------------------ çizim
def draw_body(cv, p):
    ph = p['ph']
    sp, step = spine(p)
    n = len(sp)
    gk = p['glow']
    R = p['r0']
    # eklem koru: plakaların arasındaki ışıyan bantlar (hepsinin altında)
    for i, (P, T, u) in enumerate(sp[:-1]):
        r = R * (1.0 - 0.15 * u)
        q = (P[0] + T[0] * step * 0.5, P[1] + T[1] * step * 0.5)
        N = (-T[1], T[0])
        cv.fill(cv.blob([(q[0] + N[0] * r * 0.9 - T[0] * step * 0.5, q[1] + N[1] * r * 0.9 - T[1] * step * 0.5),
                         (q[0] + N[0] * r * 0.9 + T[0] * step * 0.5, q[1] + N[1] * r * 0.9 + T[1] * step * 0.5),
                         (q[0] - N[0] * r * 0.9 + T[0] * step * 0.5, q[1] - N[1] * r * 0.9 + T[1] * step * 0.5),
                         (q[0] - N[0] * r * 0.9 - T[0] * step * 0.5, q[1] - N[1] * r * 0.9 - T[1] * step * 0.5)]), (0.92, 0.36, 0.06), z=-5, glow=(0.7, 0.22, 0.02))
        yk.glow_soft(cv, q, r * 0.9, LAVA_G, z=-4.9 + i * 0.01, alpha=0.35 * gk * (0.8 + 0.4 * math.sin(ph * 2 + i)))
        cv.stroke([(q[0] + N[0] * r * 0.8, q[1] + N[1] * r * 0.8), (q[0] - N[0] * r * 0.8, q[1] - N[1] * r * 0.8)], 0.9, z=-4.8, col=LAVA_HOT,
                  taper=(0.4, 0.4), glow=LAVA, alpha=0.7)
    for i, (P, T, u) in enumerate(sp[:-1]):
        r = R * (1.0 - 0.15 * u)
        plate(cv, P, T, r, step * 0.45, i * 0.2, OBS, gk, seed=i * 7 + 3, crack=(i % 3 == 1))
    Hp, Ht, _ = sp[-1]
    D = _d(p['ha'])
    mc = head(cv, p['H'], D, R * 1.08, p['jaw'], n * 0.2 + 1.0, gk, ph)
    # yükselen sıcak kıvılcımları
    yk.sparks(cv, (p['H'][0] - 4, p['H'][1] - 4), 4, 2.0, 9.0, LAVA_HOT, 40, seed=p['seed'] + int(ph * 3) % 17, w=1.0, glow=LAVA_G, ang=-math.pi / 2, spread=1.6)
    if p['glob'] is not None:
        gx, gy, gr = p['glob']
        glob(cv, (mc[0] + gx, mc[1] + gy), gr, 45, ph, vel=p['gv'])
    if p['streak'] > 0:   # atılış hız çizgileri (gövde boyunca)
        u29.speed_lines(cv, (p['H'][0] - 6, p['H'][1]), D, n=5, L=16 * p['streak'], spread=10, w=1.6, col=INK, alpha=0.5, z=-30, seed=p['seed'])
    if p['drip'] > 0:   # ağızdan damlayan lav
        for k in range(2):
            q = (mc[0] + k * 0.8 - 0.4, mc[1] + 3.0 + k * 1.5 + p['drip'] * 2)
            cv.fill(cv.ellipse(q, 0.6, 0.9), LAVA, z=44, glow=LAVA_G)
    return {'mouth': mc}


def draw_fx(cv, p):
    """Kök çevresinde kızgın moloz halkası, tümsek, lav sıçraması, taşlar."""
    out = {}
    ph = p['ph']
    if p['body'] > 0 and p['hole'] > 0:
        bx = p['bx'] + 1.0
        w = p['hole'] * p['r0'] * 1.5
        yc.mound(cv, bx, w, 2.6, 5, mat=ASH, mat2=ASH_D, seed=p['seed'] + 1, crack=0.6, crack_col=LAVA, crack_glow=LAVA_G, ph=ph, lumps=4)
        yk.glow_soft(cv, (bx, -1.0), w * 1.1, LAVA_G, z=4, blur=0.7, alpha=0.4, ry=3.0)
    m = p['mound']
    if m is not None:
        cx, w, h, cr = m
        yc.mound(cv, cx, w, h, 5, mat=ASH, mat2=ASH_D, seed=p['seed'], crack=cr, crack_col=LAVA, crack_glow=LAVA_G, ph=ph, lumps=6)
        yk.glow_soft(cv, (cx, -h * 0.5), w * 0.9, LAVA_G, z=6, blur=0.7, alpha=0.3 + 0.4 * cr, ry=h)
        yk.sparks(cv, (cx, -h), 4, 1.0, 6.0 + 4 * cr, LAVA_HOT, 7, seed=p['seed'] + int(ph * 5) % 13, w=1.0, glow=LAVA_G, ang=-math.pi / 2, spread=1.4)
        out['mouth'] = (cx + w * 0.3, -h * 0.9)
    if p['spray'] > 0:
        k = p['spray']
        c = p['sprc']
        yc.debris(cv, c, 14, 6.0, 22.0, 30, seed=p['seed'] + 3, k=k, cone=p['cone'], ang=p['sang'], fall=0.4, mats=(ASH, BASALT, ASH_D))
        for i in range(6):   # lav damlaları
            rng = np.random.default_rng(p['seed'] + 40 + i)
            a = p['sang'] + rng.uniform(-0.5, 0.5) * p['cone']
            dist = 18 * k * rng.uniform(0.3, 1.0)
            q = (c[0] + math.cos(a) * dist, c[1] + math.sin(a) * dist + 6 * k * k)
            rr = rng.uniform(0.4, 0.9)
            cv.fill(cv.ellipse(q, rr, rr), (0.95, 0.4, 0.08), z=31 + i * 0.01, glow=LAVA_G)
    if p['rocks'] > 0:
        yc.debris(cv, (p['sprc'][0], 0.0), 12, 12.0, 30.0, 31, seed=p['seed'] + 9, k=p['rocks'], cone=2.2, mats=(BASALT, ASH, OBS), s0=0.9, s1=2.2, fall=0.6)
    if p['crater'] > 0:
        w = p['crater']
        cx = p['sprc'][0]
        cv.shape(cv.blob([(cx - w, 0.4, 0.0), (cx - w * 0.75, -2.0), (cx - w * 0.3, -1.0), (cx + w * 0.3, -1.1), (cx + w * 0.8, -2.2), (cx + w, 0.4, 0.0)]),
                 ASH, z=28, sd=0.6, hi=0.3, ol=0.9, details=[('stroke', [(cx - w * 0.6, -0.4), (cx + w * 0.6, -0.4)], 1.4, LAVA, (0.3, 0.3))])
        yk.glow_soft(cv, (cx, -0.5), w, LAVA_G, z=28.1, alpha=0.5, ry=2.0)
    if p['plow'] > 0:   # kayarken önde yarılan toprak
        yc.debris(cv, (p['bx'] + 6.0, -0.5), 6, 3.0, 8.0 * p['plow'], 29, seed=p['seed'] + 17, k=1.0, cone=0.9, ang=-math.pi * 0.3, s0=0.5, s1=1.1,
                  mats=(ASH, BASALT))
    return out


# ================================================================== pozlar
REST = dict(bx=-12.0, H=(12.0, -20.0), ha=0.25, ba=-math.pi / 2, k1=15.0, k2=11.0, r0=7.2, rs=1.0, wave=0.0, jaw=0.25, glow=1.0,
            body=1.0, gl=0.6, hole=1.0, mound=None, glob=None, gv=(1.0, -0.4), streak=0.0, drip=0.0, spray=0.0, sprc=(0.0, 0.0), sang=-math.pi / 2, cone=1.2,
            rocks=0.0, crater=0.0, plow=0.0, seed=1)


def _idle(t):
    a = math.tau * t
    return dict(H=(12.0 + 0.8 * math.sin(a), -20.0 + 1.0 * math.cos(a)), ha=0.25 + 0.08 * math.sin(a + 0.6), wave=0.8 * math.sin(a), jaw=0.25 + 0.15 * math.sin(a * 2),
                glow=1.0 + 0.25 * math.sin(a * 2), seed=1 + int(t * 6), ph=a)


def _move(t):
    a = math.tau * t
    return dict(bx=-12.0, H=(14.0 + 1.0 * math.sin(a), -17.0 + 1.6 * math.sin(2 * a)), ha=0.35 + 0.12 * math.sin(2 * a), ba=-math.pi / 2 + 0.35,
                wave=1.8 * math.sin(a), jaw=0.3, plow=0.8 + 0.2 * math.sin(a * 2), seed=3 + int(t * 8) * 2, ph=a * 2, k1=10.0)


_HURT = [dict(H=(4.0, -22.0), ha=-0.5, jaw=0.9, wave=2.0, glow=1.6, ph=0.5),
         dict(H=(5.0, -20.5), ha=-0.25, jaw=0.6, wave=-1.2, glow=1.3, ph=1.5),
         dict(H=(8.0, -19.0), ha=0.1, jaw=0.35, wave=0.4, glow=1.1, ph=2.5)]

# ısırık atılışı: geri kalkar (ağız kapalı, kor alevlenir), yer boyunca ileri fırlar, ağzı sonuna dek açık, geri çekilir
_BITE = [dict(H=(6.0, -21.0), ha=0.0, jaw=0.15, glow=1.2, wave=0.5),
         dict(H=(1.0, -26.0), ha=-0.35, jaw=0.1, glow=1.5, wave=1.2, k2=8.0),
         dict(H=(-3.0, -29.0), ha=-0.25, jaw=0.35, glow=1.8, wave=1.6, k2=7.0, drip=0.5),
         dict(H=(-5.0, -30.0), ha=-0.15, jaw=0.55, glow=2.0, wave=1.8, k2=6.0, drip=1.0),
         dict(H=(18.0, -14.0), ha=0.25, jaw=0.9, glow=1.8, wave=0.6, k2=14.0, streak=0.6),
         dict(H=(38.0, -7.0), ha=0.12, jaw=1.1, glow=2.0, wave=0.2, k1=10.0, k2=20.0, ba=-math.pi / 2 + 0.5, streak=1.0, rs=1.05),
         dict(H=(36.0, -6.0), ha=0.18, jaw=0.4, glow=1.6, wave=-0.4, k1=10.0, k2=19.0, ba=-math.pi / 2 + 0.5, streak=0.3, spray=0.5, sprc=(34.0, 0.0),
              sang=-math.pi * 0.6, cone=1.4),
         dict(H=(16.0, -15.0), ha=0.2, jaw=0.25, glow=1.2, wave=0.4, k2=12.0)]
_BITE_TS = [0.0, 0.13, 0.25, 0.36, 0.46, 0.52, 0.66, 0.82]
_BITE_MK = [0.36, 0.52, 0.82]

# lav tükürüğü: geri kasılır, gırtlak kızarır, ağız öne-yukarı açılır, top TEMAS karesinde ağızdan çıkar
_SPIT = [dict(H=(8.0, -20.0), ha=0.1, jaw=0.25, glow=1.2),
         dict(H=(3.0, -24.0), ha=-0.2, jaw=0.15, glow=1.6, wave=1.0, k2=8.0),
         dict(H=(-1.0, -27.0), ha=-0.05, jaw=0.6, glow=2.0, wave=1.6, k2=7.0, glob=(-0.4, 0.0, 1.4), drip=0.6),
         dict(H=(-2.5, -28.0), ha=0.0, jaw=0.9, glow=2.3, wave=1.8, k2=6.5, glob=(-0.4, 0.0, 1.8), drip=1.0),
         dict(H=(9.0, -25.0), ha=-0.45, jaw=1.1, glow=2.2, wave=0.8, k2=10.0, glob=(1.0, -0.6, 2.0)),
         dict(H=(14.0, -23.0), ha=-0.35, jaw=1.1, glow=2.0, wave=0.4, k2=12.0, glob=(7.0, -3.4, 2.6), gv=(1.0, -0.5), streak=0.4),
         dict(H=(13.0, -21.0), ha=-0.1, jaw=0.7, glow=1.5, wave=-0.4, k2=12.0, drip=0.5),
         dict(H=(10.0, -19.0), ha=0.15, jaw=0.35, glow=1.2, wave=0.2)]
_SPIT_TS = [0.0, 0.14, 0.27, 0.38, 0.47, 0.53, 0.68, 0.84]
_SPIT_MK = [0.38, 0.53, 0.84]

# dalış: baş yükselir, kavis çizer, baş önde toprağa girer; en sonda yalnızca tümsek
_DIG = [dict(H=(6.0, -26.0), ha=-0.6, jaw=0.2, glow=1.3, wave=0.6),
        dict(H=(14.0, -22.0), ha=0.6, jaw=0.4, k1=16.0, k2=10.0, glow=1.4),
        dict(H=(20.0, -6.0), ha=1.3, jaw=0.3, k1=16.0, k2=12.0, spray=0.3, sprc=(21.0, 0.0), cone=1.5, seed=5),
        dict(H=(22.0, 6.0), ha=1.45, jaw=0.2, k1=12.0, k2=14.0, bx=-4.0, spray=0.6, sprc=(21.0, 0.0), cone=1.8, seed=5, mound=(21.0, 6.0, 3.0, 0.4)),
        dict(H=(22.0, 14.0), ha=1.5, k1=6.0, k2=10.0, bx=12.0, hole=0.6, spray=0.9, sprc=(18.0, 0.0), cone=2.0, seed=5, mound=(19.0, 11.0, 6.0, 0.6)),
        dict(body=0.0, spray=1.0, sprc=(16.0, 0.0), cone=2.2, seed=5, mound=(14.0, 14.0, 8.0, 0.7))]


def _burrow(t):
    a = math.tau * t
    return dict(body=0.0, mound=(0.5 * math.sin(a), 14.0 + 0.6 * math.sin(2 * a), 8.5 + 0.6 * math.cos(2 * a), 0.7 + 0.2 * math.sin(a * 2)),
                spray=0.45 + 0.2 * math.sin(a), sprc=(-9.0, 0.0), sang=-math.pi * 0.72, cone=0.9, seed=10 + int(t * 4) * 3, ph=a)


_EMERGE = [dict(body=0.0, mound=(6.0, 13.0, 7.0, 0.5), seed=21),
           dict(body=0.0, mound=(6.0, 14.0, 8.5, 0.8), seed=22, spray=0.15, sprc=(6.0, -4.0), cone=2.4),
           dict(body=0.0, mound=(6.0, 15.0, 10.0, 1.0), seed=23, spray=0.25, sprc=(6.0, -5.0), cone=2.6),
           dict(body=0.0, mound=(6.0, 16.0, 11.0, 1.2), seed=24, spray=0.3, sprc=(6.0, -6.0), cone=2.6),
           dict(bx=4.0, H=(7.0, -12.0), ha=-1.45, ba=-math.pi / 2, k1=4.0, k2=6.0, jaw=1.0, glow=2.2, hole=0.0, crater=11.0, sprc=(6.0, 0.0),
                rocks=0.35, spray=0.5, cone=2.2, seed=25),
           dict(bx=4.0, H=(9.0, -38.0), ha=-1.35, ba=-math.pi / 2, k1=12.0, k2=10.0, jaw=1.15, glow=2.4, hole=0.0, crater=12.0, sprc=(6.0, 0.0),
                rocks=0.7, spray=1.0, cone=2.0, seed=25, streak=0.8),
           dict(bx=4.0, H=(12.0, -36.0), ha=-0.9, ba=-math.pi / 2, k1=14.0, k2=10.0, jaw=0.8, glow=2.0, hole=0.0, crater=11.0, sprc=(6.0, 0.0),
                rocks=1.0, spray=0.8, cone=2.0, seed=25, wave=1.0),
           dict(bx=-6.0, H=(13.0, -22.0), ha=0.0, k1=14.0, k2=10.0, jaw=0.4, glow=1.4, crater=8.0, sprc=(6.0, 0.0), wave=0.6, seed=26)]
_EMERGE_TS = [0.0, 0.14, 0.27, 0.38, 0.47, 0.53, 0.68, 0.84]
_EMERGE_MK = [0.38, 0.53, 0.84]


def _row(frames, fps, loop, pose, ts=None, mk=None, vx=None):
    return dict(frames=frames, fps=fps, loop=loop, pose=pose, ts=ts, mk=mk, vx=vx)


ROWS = {
    'idle': _row(6, 7, True, _idle),
    'move': _row(8, 11, True, _move, vx=60.0),
    'hurt': _row(3, 14, False, _HURT),
    'atk_pick': _row(8, 12, False, _BITE, ts=_BITE_TS, mk=_BITE_MK),
    'atk_throw': _row(8, 12, False, _SPIT, ts=_SPIT_TS, mk=_SPIT_MK),
    'dig': _row(6, 12, False, _DIG),
    'burrow': _row(4, 10, True, _burrow),
    'atk_emerge': _row(8, 12, False, _EMERGE, ts=_EMERGE_TS, mk=_EMERGE_MK),
}

DURUM = yc._durum(('pick', 'throw', 'emerge'), {"windup/dig": "dig", "act/dig": "dig", "burrow": "burrow"})


def anims_for(var='kor_solucani'):
    return {k: {kk: vv for kk, vv in r.items() if kk != 'pose'} for k, r in ROWS.items()}


def durum_for(var='kor_solucani'):
    return DURUM


def pose_of(anim, i):
    r = ROWS[anim]
    src = r['pose'](i / r['frames']) if callable(r['pose']) else r['pose'][i]
    p = dict(REST, **src)
    if 'ph' not in src:
        p['ph'] = i * 0.9
    return p


SHADE = dict(outer=0.5, rim=0.8, rim_col=(1.0, 0.55, 0.25), rim_dir=(0.3, 0.95), rim_w=1.5, form=(4.0, (0.74, 0.7, 0.84)))


def render_frame(anim, i, var='kor_solucani', ss=3):
    p = pose_of(anim, i)
    W, H = CELL
    info = {}
    rgba = em = None
    if p['body'] > 0:
        cv = u29.canvas(W, H, FEET[0], FEET[1], TEX, ss=ss)
        info = draw_body(cv, p)
        rgba, _nm, em = cv.finish(**SHADE)
        rgba, em = yc._clip_ground(rgba, em, cv, p['gl'])
    cf = u29.canvas(W, H, FEET[0], FEET[1], TEX, ss=ss)
    fi = draw_fx(cf, p)
    fr, _n, fe = cf.finish(outer=0.45, form=None)
    if rgba is None:
        rgba, em = fr, fe
    else:
        rgba, em = u29.over(fr, fe, rgba, em)
    if 'mouth' not in info or info['mouth'][1] > -1.0:
        info['mouth'] = fi.get('mouth', (p['sprc'][0], -3.0))
    if p['glob'] is not None and anim == 'atk_throw' and i == 5:
        pass
    m = (round(float(info['mouth'][0]), 2), round(float(min(-1.0, info['mouth'][1])), 2))
    return rgba.astype(np.float32), None, em.astype(np.float32), {'mouth': m, 'hand': m}
