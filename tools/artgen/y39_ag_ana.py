"""v39: Ağ Ana (kimlik ag_ana) — Şahmeran mağaralarının dev mağara örümceği anası (yapay zekâ: ağ atıcı / webber).

Kemik beyazı / fildişi zırhlı kabuk (baş-göğüs + iri karın), karnın yanında Erlik moru ışıyan run damgası, ön üstte
6-8 zehir yeşili ışıyan göz kümesi (ışıma sayfası), koyu kitin kıllı bacaklar (8 bacak; yan görünüşte yakın 4'ü belirgin,
uzak 4'ü koyu ve arkada), yeşil zehir damlatan iri çeneler / zehir dişleri, ağ memelerinden arkaya sarkan ipek tel.
Alçak ve geniş siluet.

Satırlar (hücre 88 x 56 dünya, ayak (44, 52), doku 4):
  idle 6 (bacaklar esner, dişler seğirir), move 8 (koşuşturma: dönüşümlü dörtlü yürüyüş, vx 88), hurt 3,
  atk_web 8 (mk: karnı bacakların arasından yukarı-öne kaldırır, ağ memeleri ışır; temas = ağ yumağı fırlatır, ağ teli
             patlaması; toparlanma),
  atk_bite 7 (mk: ön bacakları kaldırıp şahlanır, dişler açılır; temas = aşağı-öne atılan ısırık; toparlanma),
  atk_leap 8 (mk: derin çömelme, bacaklar kurulur; temas = havada sıçrayış, bacaklar öne açılmış; toparlanma = iniş).
Çapalar her karede: 'mouth' (zehir dişleri), 'hand' (ağ memesi / karın ucu: ağın çıkış noktası).
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import lerp2
import yaratik_govde as yg
import yaratik_ink_kit as yk
import ucan_v29 as u29
from ucan_v29 import pose_at

TEX = 4.0
CELL = (352, 224)       # dünya 88 x 56
FEET = (176, 208)       # dünya (44, 52)

IVORY = Ink('#e6dac0', '#857868', '#fff8e8', '#4a3e44', name='fildişi kabuk')
IVORY_D = Ink('#c4b69c', '#6a5c56', '#e4d8c0', '#3a3036', name='kabuk ek yeri')
CHITIN = Ink('#3e3446', '#18121e', '#6e5e7a', '#0a070c', kind='fur', name='kitin bacak')
CHITIN_B = Ink('#2a2232', '#110c16', '#463c50', '#07050a', name='uzak bacak')
FANG = Ink('#1e1a22', '#0a080c', '#5a5060', name='zehir dişi')
RUNE = (0.82, 0.45, 1.0)
RUNE_HOT = (0.96, 0.85, 1.0)
RUNE_GLOW = (0.6, 0.15, 1.0)
EYE = (0.55, 1.0, 0.22)
EYE_HOT = (0.95, 1.0, 0.75)
EYE_GLOW = (0.35, 1.0, 0.1)
VENOM = (0.6, 1.0, 0.3)
SILK = (0.92, 0.94, 0.96)

PED = (-3.0, -12.5)       # bel (pedicel): karın bu noktada döner
CEPH = (5.5, -12.0)       # baş-göğüs merkezi
# bacak kökleri (baş-göğüs üstünde, yerel) ve dinlenme ayak hedefleri (x, yerden yükseklik)
ROOTS = [(9.5, -11.0), (7.0, -11.5), (4.5, -11.5), (2.0, -11.0)]
REST_N = [(27.0, 0.0), (15.0, 0.0), (-9.0, 0.0), (-22.0, 0.0)]
REST_F = [(30.0, 0.0), (19.0, 0.0), (-5.0, 0.0), (-18.0, 0.0)]
LENS = [(15.0, 19.0), (13.0, 15.0), (12.0, 14.0), (14.5, 18.0)]


def _B(p, q):
    """Gövde yereli -> dünya: pitch (CEPH çevresinde) + öteleme."""
    c, s = math.cos(p['pitch']), math.sin(p['pitch'])
    x, y = q[0] - CEPH[0], q[1] - CEPH[1]
    return (CEPH[0] + p['x'] + x * c - y * s, CEPH[1] + p['y'] + x * s + y * c)


def _A(p, q):
    """Karın yereli -> dünya: bel çevresinde ab kadar döner, sonra gövde dönüşümü."""
    c, s = math.cos(p['ab']), math.sin(p['ab'])
    x, y = q[0] - PED[0], q[1] - PED[1]
    return _B(p, (PED[0] + x * c - y * s, PED[1] + x * s + y * c))


# ------------------------------------------------------------------ bacaklar
def _leg(cv, p, i, near):
    rx, ry = ROOTS[i]
    if not near:
        rx += 1.2
        ry -= 0.8
    root = _B(p, (rx, ry))
    ft = p['n%d' % (i + 1)] if near else p['f%d' % (i + 1)]
    f = (ft[0] + p['x'] * 0.0, -ft[1])
    l1, l2 = LENS[i]
    s = 1.0 if near else 0.92
    bend = -1 if f[0] > root[0] else 1
    kn, f = yg.ik2(root, f, l1 * s, l2 * s, bend)
    m = CHITIN if near else CHITIN_B
    z = 8.0 + i * 0.1 if near else -10.0 - i * 0.1
    mid = lerp2(kn, f, 0.55)
    # diz yukarı çıkık; üç parça: uyluk, kaval, ayak ucu (incelir)
    leg = ik.union(cv.limb([root, lerp2(root, kn, 0.5), kn], [1.7, 1.6, 1.3]), cv.limb([kn, mid, f], [1.3, 1.0, 0.45]))
    det = []
    if near:
        det = [('stroke', [lerp2(root, kn, 0.15), lerp2(root, kn, 0.85)], 1.4, CHITIN.hi, (0.3, 0.3))]
    cv.shape(leg, m, z=z, sd=0.9, hi=0.25 if near else 0.0, details=det, fur=0.8 if near else 0.0, ol=0.9)
    # fildişi eklem halkaları
    for q, r in ((kn, 1.35), (mid, 1.0)):
        cv.shape(cv.ellipse(q, r, r), IVORY if near else IVORY_D.darker(0.6), z=z + 0.05, sd=0.4, hi=0.2, ol=0.7)
    # tırnak
    d = u29.norm2((f[0] - mid[0], f[1] - mid[1]))
    cv.shape(cv.blob([u29.add(f, (-d[1], d[0]), 0.4), u29.add(f, d, 1.6), u29.add(f, (d[1], -d[0]), 0.4)]), FANG, z=z + 0.1, sd=0.2, ol=0.5)
    return f


# ------------------------------------------------------------------ karın, baş-göğüs
def _abdomen(cv, p):
    """İri zırhlı karın: plaka dilimleri, run damgası, ağ memeleri. Döner: ağ memesi ucu (dünya)."""
    A = lambda x, y, *r: _A(p, (x, y)) + r
    pts = [A(-2.0, -15.5), A(-6.0, -21.0), A(-14.0, -24.0), A(-22.0, -22.5), A(-27.5, -17.0), A(-28.5, -11.5), A(-25.0, -7.0),
           A(-17.0, -4.5), A(-8.0, -6.0), A(-2.5, -9.5)]
    det = []
    # zırh plakası dilimleri (yay çizgileri)
    for k, x in enumerate((-8.0, -13.0, -18.0, -23.0)):
        det.append(('ink', [A(x + 1.5, -22.5 + k * 0.4), A(x - 0.5, -15.0), A(x + 1.0, -6.0 - k * 0.2)], 1.1, (0.15, 0.15)))
        det.append(('stroke', [A(x + 0.6, -21.5 + k * 0.4), A(x - 1.2, -15.0), A(x + 0.2, -7.0)], 2.0, IVORY.hi, (0.3, 0.3)))
    # alt yan koyu karın şeridi
    det.append(('stroke', [A(-4.0, -7.0), A(-12.0, -4.8), A(-21.0, -5.5), A(-27.0, -9.5)], 7.0, IVORY_D.shadow, (0.1, 0.2)))
    cv.shape(cv.blob(pts), IVORY, z=0, sd=3.0, hi=0.55, details=det, bounce=0.35)
    # run damgası: Erlik moru ışıyan Göktürk işaretleri (karın yanında)
    g = p['rune']
    rc = (-15.5, -14.5)
    S_ = 1.45
    strokes = [[(rc[0] - 3.0 * S_, rc[1] - 3.5 * S_), (rc[0] - 3.0 * S_, rc[1] + 3.5 * S_)],
               [(rc[0] - 3.0 * S_, rc[1] - 1.0 * S_), (rc[0] + 0.5 * S_, rc[1] - 3.8 * S_)], [(rc[0] - 3.0 * S_, rc[1] - 1.0 * S_), (rc[0] + 0.5 * S_, rc[1] + 1.8 * S_)],
               [(rc[0] + 2.2 * S_, rc[1] - 3.6 * S_), (rc[0] + 4.2 * S_, rc[1]), (rc[0] + 2.2 * S_, rc[1] + 3.6 * S_)],
               [(rc[0] - 1.0 * S_, rc[1] + 3.6 * S_), (rc[0] + 1.6 * S_, rc[1] + 3.6 * S_)]]
    yk.glow_soft(cv, A(*rc), 8.0 + 3.0 * g, RUNE_GLOW, z=1.3, blur=0.6, alpha=0.35 + 0.4 * g)
    for k, st in enumerate(strokes):
        cv.stroke([A(*q) for q in st], 5.0, z=1.1 + k * 0.01, col=(0.2, 0.06, 0.28), taper=(0.1, 0.1))
        cv.stroke([A(*q) for q in st], 2.6 + 0.8 * g, z=1.2 + k * 0.01, col=RUNE if g < 0.6 else RUNE_HOT, taper=(0.15, 0.15), glow=RUNE_GLOW)
    # ağ memeleri
    sp = A(-29.0, -12.0)
    for k, (dx, dy) in enumerate(((-0.6, -1.0), (0.3, 0.6))):
        q = A(-28.2 + dx, -12.0 + dy)
        cv.shape(cv.ellipse(q, 1.2, 0.8, p['ab'] + p['pitch']), IVORY_D, z=0.5 + k * 0.01, sd=0.3, ol=0.7)
    gl = p['spin']
    if gl > 0.05:
        yk.glow_soft(cv, sp, 2.5 + 3.0 * gl, (0.8, 1.0, 0.85), z=0.8, blur=0.6, alpha=0.6 * gl)
        cv.fill(cv.ellipse(sp, 0.7 + 0.6 * gl, 0.7 + 0.6 * gl), (0.95, 1.0, 0.95), z=0.9, glow=(0.6, 0.9, 0.7))
    return sp


def _ceph(cv, p):
    """Baş-göğüs kalkanı + göz kümesi + çeneler / zehir dişleri. Döner: diş ucu (dünya)."""
    Bq = lambda x, y, *r: _B(p, (x, y)) + r
    shell = cv.blob([Bq(-3.5, -12.5), Bq(-1.0, -16.0), Bq(5.0, -18.0), Bq(10.5, -17.0), Bq(14.0, -14.0), Bq(14.5, -10.5),
                     Bq(11.0, -8.0), Bq(4.0, -7.5), Bq(-2.0, -9.0)])
    det = [('ink', [Bq(1.0, -16.5), Bq(4.0, -13.5), Bq(4.0, -9.0)], 1.0, (0.2, 0.3)),
           ('stroke', [Bq(0.0, -15.5), Bq(6.0, -17.0), Bq(11.0, -16.0)], 2.4, IVORY.hi, (0.3, 0.5)),
           ('stroke', [Bq(-1.0, -9.5), Bq(5.0, -8.2), Bq(11.0, -8.6)], 5.0, IVORY_D.shadow, (0.2, 0.3))]
    # kabuk dikenleri (sırt)
    for (x, y, a) in ((2.0, -17.0, -1.9), (6.0, -18.0, -1.7)):
        b = Bq(x, y)
        aa = a + p['pitch']
        tip = (b[0] + math.cos(aa) * 2.6, b[1] + math.sin(aa) * 2.6)
        cv.shape(cv.blob([(b[0] - 0.9, b[1] + 0.3), (tip[0], tip[1], 0.0), (b[0] + 0.9, b[1] + 0.3)]), IVORY, z=1.9, sd=0.4, ol=0.8)
    cv.shape(shell, IVORY, z=2, sd=2.2, hi=0.5, details=det, bounce=0.3)
    # göz kümesi: 8 göz (iki iri ön, altı küçük)
    ey = p['eye']
    sq = p['squint']
    eyes = [(12.0, -14.6, 1.25), (9.6, -16.0, 1.05), (12.8, -12.4, 0.75), (10.4, -12.8, 0.7), (7.6, -16.8, 0.65), (13.4, -16.0, 0.55),
            (8.2, -14.4, 0.5), (11.0, -17.3, 0.5)]
    yk.glow_soft(cv, Bq(11.0, -14.8), 4.2 + 2.5 * ey, EYE_GLOW, z=3.0, blur=0.6, alpha=0.35 + 0.35 * ey)
    for k, (x, y, r) in enumerate(eyes):
        c = Bq(x, y)
        cv.fill(cv.ellipse(c, r * 1.25, r * 1.2), INK, z=3.1 + k * 0.01)
        rr = r * (1.0 - 0.6 * sq)
        cv.fill(cv.ellipse(c, rr * 0.8, rr * 0.8), EYE if ey < 0.5 else EYE_HOT, z=3.2 + k * 0.01, glow=EYE_GLOW)
        if r > 0.9:
            cv.fill(cv.ellipse((c[0] - rr * 0.25, c[1] - rr * 0.3), rr * 0.22, rr * 0.22), (0.9, 1.0, 0.85), z=3.3 + k * 0.01)
        yk.glow_soft(cv, c, r * 1.8, EYE_GLOW, z=3.35, blur=0.5, alpha=0.5 + 0.3 * ey)
    # çeneler (chelicerae): yakın / uzak; dişler fang ile açılır
    fg = p['fang']
    tips = []
    for k, (ox, oy, m, zz) in enumerate(((1.0, -0.6, IVORY_D.darker(0.75), 1.5), (0.0, 0.0, IVORY, 10.0))):
        base = Bq(12.0 + ox, -9.8 + oy)
        a = 1.25 - fg * 0.9 - p['pitch'] * 0.0 + p['pitch']   # kök doğrultusu (aşağı-öne)
        bt = (base[0] + math.cos(a) * 4.8, base[1] + math.sin(a) * 4.8)
        ch = cv.limb([base, lerp2(base, bt, 0.5), bt], [2.5, 2.4, 1.8])
        cv.shape(ch, m, z=zz, sd=0.8, hi=0.3 if k else 0.0, ol=0.9, fur=0.3,
                 details=[('stroke', [lerp2(base, bt, 0.3), bt], 1.6, (0.3, 0.25, 0.3), (0.2, 0.3))] if k else ())
        # diş: içe kıvrık kara çengel; açıkken öne savrulur
        fa = a + 1.6 - fg * 1.6
        f1 = u29.add(bt, (math.cos(fa), math.sin(fa)), 3.0)
        f2 = u29.add(f1, (math.cos(fa + 0.9), math.sin(fa + 0.9)), 2.6)
        cv.shape(cv.blob([u29.add(bt, (-math.sin(a), math.cos(a)), 0.9), f1, (f2[0], f2[1], 0.0), u29.add(f1, (math.cos(fa - 1.6), math.sin(fa - 1.6)), 0.5),
                          u29.add(bt, (math.sin(a), -math.cos(a)), 0.9)]), FANG, z=zz + 0.1, sd=0.4, hi=0.2, ol=0.8)
        tips.append(f2)
    # zehir damlası: yakın diş ucundan sarkıp düşer
    dr = p['drip']
    tq = tips[1]
    hang = 0.8 + 2.2 * dr
    d0 = (tq[0], tq[1] + hang)
    cv.stroke([tq, d0], 1.0, z=10.4, col=VENOM, taper=(0.0, 0.5), glow=(0.25, 0.6, 0.05))
    cv.fill(cv.blob([(d0[0] - 0.55, d0[1]), (d0[0], d0[1] - 0.9), (d0[0] + 0.55, d0[1]), (d0[0], d0[1] + 0.8)]), VENOM, z=10.5, glow=(0.3, 0.7, 0.05))
    if p['venom'] > 0.05:   # ısırıkta saçılan zehir
        yk.sparks(cv, tq, 5, 0.5, 3.5, VENOM, 10.6, seed=4, w=1.3, glow=(0.3, 0.7, 0.05), ang=1.2, spread=2.0)
    # dokunaçlar (pedipalp)
    pa = p['palp']
    for k, (m, zz) in enumerate(((CHITIN_B, 1.4), (CHITIN, 10.2))):
        b = Bq(12.5 - k * 0.5, -11.5)
        e = (b[0] + 3.0 + pa * 1.5, b[1] - 1.0 - pa * 2.0)
        t = (e[0] + 1.5, e[1] + 2.4 - pa * 1.5)
        cv.shape(cv.limb([b, e, t], [0.9, 0.8, 0.55]), m, z=zz - 0.05, sd=0.4, ol=0.7, fur=0.4)
    return lerp2(tips[0], tips[1], 0.7)


def _silk(cv, sp, p):
    """Ağ memesinden arkaya / yere sarkan ipek tel (sarkma eğrisi)."""
    k = p['silk']
    if k <= 0.02:
        return
    end = (sp[0] - 14.0 - p['x'], -0.2)
    pts = []
    for i in range(9):
        u = i / 8
        q = lerp2(sp, end, u)
        sag = 3.0 * math.sin(math.pi * u) * (1.0 if end[1] > sp[1] else -1.0)
        pts.append((q[0], q[1] + sag * 0.3 + math.sin(p['ph'] + u * 5) * 0.4 * u))
    cv.stroke(pts, 0.9, z=-15, col=SILK, taper=(0.0, 0.3), alpha=0.75 * k)


def _web_burst(cv, sp, p):
    """Ağ yumağı: memeden hedefe uzanan kalın tel + ucunda kıvrık ipek yumağı ve dağılan tel patlaması."""
    k = p['web']
    if k <= 0.02:
        return
    d = u29.norm2(p['wdir'])
    dist = 8.0 + 26.0 * min(1.0, k)
    c = u29.add(sp, d, dist)
    n = (-d[1], d[0])
    # ana tel (hafif dalgalı)
    pts = [u29.add(u29.add(sp, d, dist * u), n, math.sin(u * 9 + p['ph']) * 0.6 * u) for u in np.linspace(0, 1, 9)]
    cv.stroke(pts, 1.8, z=40, col=SILK, taper=(0.2, 0.0), glow=(0.25, 0.3, 0.25), alpha=0.9)
    # yumak: üst üste kıvrık halkalar
    r = 2.6 + 2.0 * min(1.0, k)
    yk.glow_soft(cv, c, r * 1.8, (0.7, 0.85, 0.75), z=40.5, blur=0.6, alpha=0.35)
    cv.shape(cv.ellipse(c, r, r * 0.85), Ink('#e8ecee', '#9098a8', '#ffffff', '#5a6070', name='ağ yumağı'), z=41, sd=0.8, hi=0.3, ol=0.8, grad=0.0)
    for j in range(4):
        a0 = j * 1.6 + p['ph']
        ring = [(c[0] + math.cos(a0 + t) * r * (0.35 + 0.15 * j), c[1] + math.sin(a0 + t) * r * 0.8 * (0.35 + 0.15 * j)) for t in np.linspace(0, 4.4, 8)]
        cv.stroke(ring, 0.8, z=41.2, col=(0.45, 0.48, 0.56), taper=(0.3, 0.3))
    # tel patlaması: dışa saçılan ince teller + ara bağlar (örümcek ağı parçası)
    burst = min(1.0, k * 1.2)
    spokes = []
    for j in range(9):
        a = j / 9 * math.tau + 0.2
        L = r + (4.0 + 5.0 * ((j * 7) % 3) / 2) * burst
        e = (c[0] + math.cos(a) * L, c[1] + math.sin(a) * L * 0.85)
        cv.stroke([(c[0] + math.cos(a) * r * 0.8, c[1] + math.sin(a) * r * 0.7), e], 0.9, z=40.8, col=SILK, taper=(0.0, 0.7), alpha=0.85)
        spokes.append(e)
    for j in range(9):
        a, b = spokes[j], spokes[(j + 1) % 9]
        q0 = lerp2(c, a, 0.7)
        q1 = lerp2(c, b, 0.7)
        cv.stroke([q0, lerp2(lerp2(q0, q1, 0.5), c, 0.1), q1], 0.7, z=40.7, col=SILK, taper=(0.2, 0.2), alpha=0.6 * burst)


def draw(cv, p):
    for i in range(4):
        _leg(cv, p, i, False)
    sp = _abdomen(cv, p)
    mouth = _ceph(cv, p)
    for i in range(4):
        _leg(cv, p, i, True)
    _silk(cv, sp, p)
    _web_burst(cv, sp, p)
    if p['streak'] > 0.02:
        u29.speed_lines(cv, (p['x'] - 8.0, -12.0 + p['y']), p.get('sdir', (1.0, -0.2)), n=5, L=14.0 * p['streak'], spread=14.0, w=1.5,
                        col=(0.6, 0.55, 0.65), alpha=0.5, z=-30, seed=7)
    if p['dust'] > 0.05:
        DUST = Ink('#8a8478', '#5a5450', '#b4ac9c', name='mağara tozu')
        for i, (x, r) in enumerate(((-20.0, 2.0), (-8.0, 2.6), (8.0, 2.4), (22.0, 2.0))):
            rr = r * p['dust']
            yk.puff(cv, (x + p['x'] * 0.8, -rr * 0.6), rr, DUST, z=20 + i * 0.1, seed=5 + i, n=6, ol=0.35, sd=rr * 0.2)
    if p['zirh'] > 0:
        u29.armor_aura(cv, (p['x'] - 6, -14 + p['y']), 24.0, p['zirh'], z=-45, seed=4)
    return {'mouth': mouth, 'hand': sp}


# ================================================================== animasyon
REST = dict(t=0.0, ph=0.0, x=0.0, y=0.0, pitch=0.0, ab=0.0, fang=0.1, palp=0.0, eye=0.2, squint=0.0, rune=0.3, spin=0.0, drip=0.3, venom=0.0,
            silk=1.0, web=0.0, wdir=(1.0, -0.15), streak=0.0, dust=0.0, zirh=0.0)
for _i in range(4):
    REST['n%d' % (_i + 1)] = REST_N[_i]
    REST['f%d' % (_i + 1)] = REST_F[_i]


def _idle(t):
    s = math.sin(math.tau * t)
    p = dict(REST, t=t)
    p.update(y=0.5 + 0.6 * s, pitch=0.02 * math.sin(math.tau * t + 0.6), ab=-0.03 * math.sin(math.tau * t + 1.2),
             fang=0.1 + 0.25 * max(0.0, math.sin(math.tau * t * 2)), palp=0.3 * math.sin(math.tau * t * 2 + 0.5), drip=t, rune=0.35 + 0.2 * s)
    # bacak esnemesi: ön çift hafifçe kalkıp iner
    p['n1'] = (27.0 + 0.6 * s, max(0.0, 1.2 * math.sin(math.tau * t)))
    p['f1'] = (30.0 - 0.6 * s, max(0.0, -1.0 * math.sin(math.tau * t)))
    return p


def _foot_cycle(phi, home, S, duty, lift):
    phi %= 1.0
    if phi < duty:
        u = phi / duty
        return (home + S * (0.5 - u), 0.0)
    u = (phi - duty) / (1.0 - duty)
    e = u * u * (3 - 2 * u)
    return (home - S * 0.5 + S * e, lift * math.sin(math.pi * u))


RUN_S, RUN_DUTY, RUN_FPS = 16.0, 0.5, 22


def _run(t):
    p = dict(REST, t=t)
    # dönüşümlü dörtlü: yakın 1-3 + uzak 2-4 birlikte, yakın 2-4 + uzak 1-3 yarım evre sonra
    for i in range(4):
        ph_n = 0.0 if i in (0, 2) else 0.5
        ph_f = 0.5 if i in (0, 2) else 0.0
        p['n%d' % (i + 1)] = _foot_cycle(t + ph_n, REST_N[i][0], RUN_S, RUN_DUTY, 4.0)
        p['f%d' % (i + 1)] = _foot_cycle(t + ph_f, REST_F[i][0], RUN_S, RUN_DUTY, 3.5)
    a = math.tau * t
    p.update(y=-0.5 + 0.6 * math.cos(2 * a), pitch=0.02 * math.sin(2 * a), ab=0.05 * math.sin(2 * a + 0.8), fang=0.15, palp=0.4 * math.sin(2 * a), drip=0.5, eye=0.3)
    return p


def _K(keys):
    return lambda t: pose_at(t, keys, base=REST)


def _legs(**kw):
    """Ayak hedefi kısaltması: n=[...], f=[...] listelerini anahtar sözlüğüne aç."""
    d = {}
    for side in ('n', 'f'):
        if side in kw:
            for i, v in enumerate(kw.pop(side)):
                d['%s%d' % (side, i + 1)] = v
    d.update(kw)
    return d


# ağ: 8 kare
_WEB_TS = [0.0, 0.12, 0.24, 0.36, 0.48, 0.56, 0.7, 0.85]
_WEB = [
    (0.0, dict(ab=0.0, spin=0.0), 'l'),
    (0.12, _legs(ab=0.6, pitch=0.06, y=0.8, spin=0.3, rune=0.6, eye=0.4, silk=0.6, n=[(25.0, 0.0), (14.0, 0.0), (-6.0, 0.0), (-17.0, 0.0)],
                 f=[(28.0, 0.0), (18.0, 0.0), (-3.0, 0.0), (-14.0, 0.0)]), 'o'),
    (0.24, dict(ab=1.35, pitch=0.12, y=1.6, spin=0.8, rune=1.0, eye=0.8, silk=0.0), 'o'),
    (0.36, dict(ab=1.55, pitch=0.14, y=2.0, spin=1.0, rune=1.1, eye=1.0), 'io'),
    (0.48, dict(ab=1.75, pitch=0.08, y=1.2, spin=1.2, web=0.35, wdir=(1.0, -0.1)), 'i'),
    (0.56, dict(ab=1.8, pitch=0.04, y=0.8, spin=0.8, web=1.0, x=-1.5), 'o'),
    (0.7, dict(ab=1.5, pitch=0.04, y=0.8, spin=0.4, web=1.2, x=-1.0, rune=0.7), 'o'),
    (0.85, _legs(ab=0.5, pitch=0.02, y=0.4, spin=0.1, web=0.0, x=0.0, rune=0.4, eye=0.3, silk=0.5, n=REST_N, f=REST_F), 'io'),
    (1.0, dict(ab=0.0, pitch=0.0, y=0.0, spin=0.0, silk=1.0, eye=0.2, rune=0.3), 'io'),
]

# ısırık: 7 kare
_BI_TS = [0.0, 0.14, 0.28, 0.42, 0.54, 0.68, 0.84]
_BITE = [
    (0.0, dict(fang=0.1), 'l'),
    (0.14, _legs(pitch=-0.14, y=-1.0, x=-1.5, ab=0.15, fang=0.6, palp=0.8, eye=0.5, n=[(22.0, 7.0), (17.0, 3.5), (-10.0, 0.0), (-23.0, 0.0)],
                 f=[(25.0, 8.0), (20.0, 4.0), (-6.0, 0.0), (-19.0, 0.0)]), 'o'),
    (0.28, _legs(pitch=-0.3, y=-3.0, x=-3.0, ab=0.3, fang=1.0, palp=1.0, eye=1.0, drip=0.8, n=[(18.0, 14.0), (17.0, 7.0), (-11.0, 0.0), (-24.0, 0.0)],
                 f=[(21.0, 15.0), (20.0, 8.0), (-7.0, 0.0), (-20.0, 0.0)]), 'o'),
    (0.42, _legs(pitch=-0.34, y=-3.5, x=-3.4, ab=0.32, fang=1.05, n=[(17.0, 15.0), (17.0, 7.5), (-11.5, 0.0), (-24.5, 0.0)],
                 f=[(20.0, 16.0), (20.0, 8.5), (-7.5, 0.0), (-20.5, 0.0)]), 'io'),
    (0.54, _legs(pitch=0.34, y=3.0, x=7.0, ab=-0.15, fang=0.0, palp=0.2, venom=1.0, streak=1.0, eye=1.0, sdir=(1.0, 0.3), n=[(34.0, 0.0), (24.0, 0.0), (-3.0, 0.0), (-17.0, 0.0)],
                 f=[(36.0, 0.0), (27.0, 0.0), (0.0, 0.0), (-13.0, 0.0)]), 'i'),
    (0.68, dict(pitch=0.16, y=1.6, x=5.0, fang=0.2, venom=0.4, streak=0.0, drip=0.2), 'o'),
    (0.84, _legs(pitch=0.02, y=0.4, x=1.5, ab=0.0, fang=0.25, palp=0.0, venom=0.0, eye=0.3, n=[(28.0, 0.0), (16.0, 0.0), (-8.0, 0.0), (-21.0, 0.0)],
                 f=[(31.0, 0.0), (20.0, 0.0), (-4.0, 0.0), (-17.0, 0.0)]), 'io'),
    (1.0, _legs(pitch=0.0, y=0.0, x=0.0, fang=0.1, eye=0.2, n=REST_N, f=REST_F), 'io'),
]

# sıçrayış: 8 kare
_LE_TS = [0.0, 0.12, 0.24, 0.36, 0.48, 0.58, 0.72, 0.86]
_CROUCH_N = [(25.0, 0.0), (13.0, 0.0), (-7.0, 0.0), (-19.0, 0.0)]
_CROUCH_F = [(28.0, 0.0), (17.0, 0.0), (-3.0, 0.0), (-15.0, 0.0)]
_LEAP = [
    (0.0, dict(y=0.0), 'l'),
    (0.12, _legs(y=2.5, pitch=0.05, eye=0.5, fang=0.3, n=_CROUCH_N, f=_CROUCH_F), 'o'),
    (0.24, dict(y=4.8, pitch=0.08, x=-1.5, eye=1.0, fang=0.6, palp=0.6, rune=0.8, ab=0.12), 'o'),
    (0.36, dict(y=5.4, pitch=0.1, x=-2.0, eye=1.0, fang=0.7, ab=0.15), 'io'),
    (0.48, _legs(y=-12.0, pitch=-0.18, x=6.0, fang=1.0, palp=1.0, ab=0.25, silk=0.0, streak=0.8, sdir=(1.0, -0.6), n=[(36.0, 16.0), (28.0, 10.0), (-10.0, 6.0), (-24.0, 9.0)],
                 f=[(38.0, 17.0), (30.0, 11.0), (-6.0, 7.0), (-20.0, 10.0)]), 'i'),
    (0.58, _legs(y=-14.0, pitch=-0.05, x=6.0, ab=0.1, streak=0.5, sdir=(1.0, 0.0), n=[(38.0, 12.0), (28.0, 9.0), (-8.0, 8.0), (-21.0, 10.0)],
                 f=[(40.0, 13.0), (30.0, 10.0), (-4.0, 9.0), (-17.0, 11.0)]), 'o'),
    (0.72, _legs(y=-4.0, pitch=0.12, x=7.0, ab=-0.05, fang=0.5, streak=0.0, n=[(34.0, 2.0), (23.0, 1.5), (-4.0, 3.0), (-15.0, 4.0)],
                 f=[(36.0, 2.0), (26.0, 2.0), (-1.0, 3.0), (-12.0, 4.0)]), 'i'),
    (0.86, _legs(y=3.5, pitch=0.08, x=6.0, ab=0.0, fang=0.3, palp=0.2, dust=1.0, n=[(31.0, 0.0), (19.0, 0.0), (-4.0, 0.0), (-16.0, 0.0)],
                 f=[(33.0, 0.0), (23.0, 0.0), (0.0, 0.0), (-12.0, 0.0)]), 'o'),
    (1.0, dict(y=0.5, pitch=0.0, x=3.0, dust=1.3, eye=0.2, fang=0.1, silk=0.6, rune=0.3), 'io'),
]

_HURT = [
    (0.0, _legs(x=-3.0, y=-1.5, pitch=-0.2, ab=0.3, fang=1.0, palp=1.0, squint=1.0, eye=0.0, n=[(24.0, 6.0), (16.0, 3.0), (-10.0, 0.0), (-23.0, 1.0)],
                f=[(27.0, 6.0), (20.0, 3.0), (-6.0, 0.0), (-19.0, 1.0)]), 'l'),
    (0.5, _legs(x=-4.0, y=0.5, pitch=-0.06, ab=0.12, fang=0.6, palp=0.5, squint=0.6, n=[(25.0, 1.5), (15.0, 0.5), (-10.0, 0.0), (-23.0, 0.0)],
                f=[(28.0, 1.5), (19.0, 0.5), (-6.0, 0.0), (-19.0, 0.0)]), 'o'),
    (1.0, _legs(x=-3.0, y=0.2, pitch=0.0, ab=0.0, fang=0.2, palp=0.0, squint=0.2, eye=0.2, n=REST_N, f=REST_F), 'io'),
]


def _row(frames, fps, loop, pose, ts=None, mk=None, vx=None):
    return dict(frames=frames, fps=fps, loop=loop, pose=pose, ts=ts, mk=mk, vx=vx)


ROWS = {
    'idle': _row(6, 8, True, _idle),
    'move': _row(8, RUN_FPS, True, _run, vx=round(RUN_S / (RUN_DUTY * 8 / RUN_FPS), 1)),
    'hurt': _row(3, 14, False, _K(_HURT)),
    'atk_web': _row(8, 12, False, _K(_WEB), ts=_WEB_TS, mk=[0.46, 0.56, 0.76]),
    'atk_bite': _row(7, 12, False, _K(_BITE), ts=_BI_TS, mk=[0.5, 0.54, 0.7]),
    'atk_leap': _row(8, 12, False, _K(_LEAP), ts=_LE_TS, mk=[0.46, 0.48, 0.74]),
}


def _durum():
    d = {"idle": "idle", "chase": "move", "recover": "idle", "evade": "move", "_hurt": "hurt", "_hurt_big": "hurt", "_break": "hurt"}
    for m in ('web', 'bite', 'leap'):
        for ph in ('windup', 'act', 'recover'):
            d['%s/%s' % (ph, m)] = 'atk_' + m
    d['hold/web'] = 'atk_bite'
    return d


DURUM = _durum()


def anims_for(var='ag_ana'):
    return {k: {kk: vv for kk, vv in r.items() if kk != 'pose'} for k, r in ROWS.items()}


def durum_for(var='ag_ana'):
    return dict(DURUM)


def _frame_time(row, i):
    if row['ts']:
        return row['ts'][i]
    if row['loop']:
        return i / row['frames']
    return i / max(1, row['frames'] - 1)


SHADE = dict(outer=0.6, rim=0.8, rim_col=(0.72, 0.8, 1.0), rim_dir=(0.6, -0.8), rim_w=1.4, form=(5.0, (0.74, 0.72, 0.86)))


def render_frame(anim, i, var='ag_ana', ss=3):
    row = ROWS[anim]
    tt = _frame_time(row, i)
    p = dict(row['pose'](tt))
    p['t'] = tt
    p['ph'] = tt * math.tau * (1 if row['loop'] else 1.5) + i * 0.6
    if 'sdir' not in p:
        p['sdir'] = (1.0, 0.0)
    cv = u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
