"""Bengü — stil v2 "mürekkep-cel" (çizgi roman; bkz. inkkit.py). Piksel sanat değil: 4x doku yoğunluğu (v2 kamerası
2,0 yakın: 1080p'de 1 doku pikseli = 1 ekran pikseli), kenar yumuşatmalı vektör çizim, oyunda doğrusal süzgeç + mipmap.

İskelet ve çapalar bengu_v2 ile aynı (bacak 12 + 11.8, gövde 17, kol 10 + 9.4, kalça -23.6): Player.gd kol iskeleti,
silah tutuşu ve çarpışma kutuları değişmez. v20 kimlik: kurt başlıklı kadın savaşçı (Asena soyu): ak kurt başlığı
(camgöbeği ışıyan kurt gözü, köpek dişleri, kırmızı tamga), altında insan yüzü (savaş boyası), gri kurt postu pelerin +
göğüse sarkan pençe ve altın toka, kırmızı kaftan (diz boyu, altın sırma), çelik lamel yelek + omuzluk + dizlik, geniş deri
kemer ve altın plakalar, belde iki kat turkuaz kuşak (iki kuyruklu), çivit şalvar, uzun çizme. Uzun saç ve örgüler sprite'ta
yok: oyunda çizilir (scripts/core/BenguSac.gd; çapalar 'sac', 'sac_d', 'neck', 'hip'). Bkz. docs/TASARIM.md "Bengü v20".
"""
import math

import inkkit as ik
from inkkit import Ink, INK
import bengu_v2 as v2
from bengu import P, keyed
from rig import fk_leg, fk_arm, lerp2, chain

TEX = 4.0
CELL = (384, 320)        # dünya 96 x 80 (texel 4)
FEET = (176, 296)        # dünya (44, 74)
L_THIGH, L_SHIN = 13.0, 12.6      # v2: 12 + 11.8; ninja oranı için uzun bacak (kalça yerden çözülür)
L_UP, L_FORE = v2.L_UP, v2.L_FORE
HIP_Y = v2.HIP_Y
TORSO = v2.TORSO
HEAD_K = 1.05           # baş ölçeği (insan başı + başlık; ~7 baş boy, oyun yakınlığında yüz okunsun)

# ------------------------------------------------------------ malzemeler
KAFTAN = Ink('#d23138', '#6c1838', '#ff6a50', '#3a0f2a', name='kırmızı kaftan')
KAFTAN_B = Ink('#93202f', '#4a122e', '#b83a3a', '#2a0b20', name='kaftan arka/astar')
LINING = Ink('#4a1630', '#2a0d22', '#6a2440', name='astar')
EMBR = Ink('#e2ac4a', '#8e4f24', '#fff0b4', kind='metal', name='altın sırma')
PANTS = Ink('#5266a2', '#262e58', '#7a90c8', '#161a34', name='çivit şalvar')
PANTS_B = PANTS.darker(0.72)
BOOT = Ink('#96553a', '#40201c', '#cc8a5c', name='çizme')
BOOT_B = BOOT.darker(0.72)
SOLE = Ink('#2a2024', '#17121a', '#4a3a3a', name='taban')
STEEL = Ink('#aeb8ca', '#535c78', '#f4f8ff', '#3a4058', kind='metal', name='çelik')
STEEL_B = STEEL.darker(0.7)
BELT = Ink('#6e3e26', '#2c1612', '#a06a44', name='kemer')
GOLD = Ink('#eab64e', '#94561e', '#fff4c0', kind='metal', name='altın')
BRACER = Ink('#76432c', '#30180f', '#a8704a', name='bilek siperi')
GLOVE = Ink('#5a3e34', '#24161a', '#8e6a5a', name='eldiven')
SCARF = Ink('#27c2b0', '#0e5a68', '#9ff6e2', '#0a3a48', name='turkuaz atkı')
SCARF_B = SCARF.darker(0.78)
FUR = Ink('#f1f3f7', '#8e98ba', '#ffffff', '#5f6a8c', kind='fur', name='ak post')
FUR_B = Ink('#c4cadb', '#7d87a6', '#e6eaf2', '#4f5878', kind='fur', name='uzak post')
EAR_IN = Ink('#a0606c', '#5e3044', '#c88890', name='kulak içi')
NOSE = Ink('#26232c', '#141218', '#6a6a7a', name='burun')
PAINT = (0.86, 0.12, 0.16)
EYE = (0.55, 0.98, 1.0)
EYE_GLOW = (0.35, 0.95, 1.0)
SKIN = Ink('#e9b48e', '#a65d58', '#ffdcb8', '#6a3040', name='ten')
HAIR = Ink('#2e2636', '#16121d', '#6e74a0', '#0c0a12', name='kuzgun saç')     # BenguSac.gd ile aynı renkler
PELT = Ink('#b9c0d2', '#6b7394', '#e9edf5', '#4a5274', kind='fur', name='kurt postu (sırt)')
TOOTH = Ink('#f2efe4', '#a8a6b0', '#ffffff', name='kurt dişi')


def _T(hip, ax, pe):
    def f(u, v):
        return (hip[0] + ax[0] * u + pe[0] * v, hip[1] + ax[1] * u + pe[1] * v)
    return f


def _perp(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1.0
    return (-dy / d, dx / d), (dx / d, dy / d)


def along(a, b, t, off=0.0):
    n, _ = _perp(a, b)
    return (a[0] + (b[0] - a[0]) * t + n[0] * off, a[1] + (b[1] - a[1]) * t + n[1] * off)


def fur_ring(c, rx, ry, rot, a0, a1, n, depth, tuft_from=0.0, tuft_to=1.0, phase=0.0):
    """Kenarı tutamlı (sivri uçlu) post şekli: elips yayı, [tuft_from, tuft_to] aralığında dişli."""
    pts = []
    cr, sr = math.cos(rot), math.sin(rot)
    m = n * 2
    for i in range(m + 1):
        t = i / m
        a = a0 + (a1 - a0) * t
        tip = (i % 2 == 0) and tuft_from <= t <= tuft_to
        r = 1.0 + (depth * (0.75 + 0.25 * math.sin(i * 2.1 + phase)) if tip else 0.0)
        x, y = math.cos(a) * rx * r, math.sin(a) * ry * r
        pts.append((c[0] + x * cr - y * sr, c[1] + x * sr + y * cr, 0.0 if tip else 0.8))
    return pts


AW = 0.88       # kol kalınlığı (kadın savaşçı: atletik ama daha ince kol, bilek ve yumruk; kemik boyları aynı)
AWP = 0.86      # omuzluk


def _al(a, b, t, off=0.0):
    return along(a, b, t, off * AW)


def _alp(a, b, t, off=0.0):
    return along(a, b, t, off * AWP)


# ------------------------------------------------------------ parçalar
def _leg(cv, hip, a, z, near, kz=None):
    k, f = fk_leg(hip, a[0], a[1], L_THIGH, L_SHIN)
    pm = PANTS if near else PANTS_B
    bm = BOOT if near else BOOT_B
    bt = lerp2(k, f, 0.5)             # çizme ağzı (baldır ortası; üstünde bol şalvar)
    mid = lerp2(hip, k, 0.45)
    n, d = _perp(hip, k)
    # bol şalvar: kalçada geniş, uyluk ortasında şişkin, dizde toplanır, çizme üstünde yeniden bollanır
    mid_b = (mid[0] + n[0] * -0.5, mid[1] + n[1] * -0.5)
    pants = cv.limb([hip, mid_b, k, lerp2(k, f, 0.2), bt], [4.2, 4.5, 3.5, 3.4, 3.9])
    fold = []
    # uyluk: kalçadan dize inen çapraz kıvrımlar (gölge kaması + mürekkep)
    for t0, t1, o0, o1, sd_ in ((0.12, 0.6, -2.8, 0.2, 1), (0.38, 0.9, -3.2, -0.8, 1), (0.5, 0.95, 2.8, 1.0, -1)):
        pts = [along(hip, k, t0, o0), along(hip, k, (t0 + t1) / 2, (o0 + o1) / 2 + 0.5), along(hip, k, t1, o1)]
        fold += cv.fold(pts, 0.8, 1.4, sd_)
    # çizme üstündeki bolluk: zikzak kıvrımlar
    for t, o, sd_ in ((0.2, -2.6, 1), (0.26, 1.8, -1), (0.31, -0.6, 1)):
        fold += cv.fold([along(k, f, t - 0.07, o - 1.1), along(k, f, t, o), along(k, f, t + 0.03, o + 1.3)], 0.6, 1.3, sd_)
    cv.shape(pants, pm, z=z, details=fold, sd=2.3 if near else 3.0, hi=0.0, hatch=0.55 if near else 0.0, bounce=0.3 if near else 0.0)
    # çizme: konç + ayak tek parça
    toe = (f[0] + 4.9, f[1] + 0.4)
    heel = (f[0] - 2.2, f[1] + 1.2)
    boot = ik.union(cv.limb([bt, lerp2(bt, f, 0.6), f], [3.4, 2.8, 2.6]),
                    cv.blob([(f[0] - 2.3, f[1] - 1.0), (f[0] + 1.2, f[1] - 1.6), (f[0] + 3.6, f[1] - 0.4), (toe[0], toe[1] - 0.5),
                             (toe[0] + 0.3, toe[1] + 0.9, 0.0), (heel[0] + 0.2, heel[1] + 0.7, 0.0), (heel[0] - 0.3, f[1] - 0.2)]))
    bdet = [('ink', [along(bt, f, 0.62, -2.2), along(bt, f, 0.7, 0.0), along(bt, f, 0.66, 2.0)], 1.3, (0.4, 0.4)),
            ('ink', [along(bt, f, 0.08, -2.8), along(bt, f, 0.1, 2.8)], 1.8, (0.15, 0.15))]
    cv.shape(boot, bm, z=z + 0.4, details=bdet, sd=1.6, hi=0.35 if near else 0.0)
    sole = cv.blob([(heel[0] - 0.4, heel[1] - 0.2), (toe[0] + 0.3, toe[1] + 0.2), (toe[0] + 0.1, toe[1] + 1.1, 0.0), (heel[0] - 0.2, heel[1] + 1.1, 0.0)])
    cv.shape(sole, SOLE, z=z + 0.5, flat=True, ol=0.8)
    if near:      # çelik dizlik
        kk = along(k, f, 0.06, 1.2)
        kp = cv.blob([along(k, f, -0.18, 0.4), along(k, f, -0.02, 3.2), along(k, f, 0.22, 2.6), along(k, f, 0.32, 0.6),
                      along(k, f, 0.12, -1.2), along(k, f, -0.12, -1.0)])
        cv.shape(kp, STEEL, z=(kz if kz is not None else z + 1.0), sd=1.0, hi=0.55, details=[('ink', [along(k, f, 0.12, -0.6), along(k, f, 0.14, 2.6)], 1.2)])
        _ = kk
    return k, f


def _upper(cv, sh, e, z, near=True):
    """Üst kol (kaftan kolu): omuz kası şişkin, dirseğe incelir; bol kumaş dirsek içinde zikzak kıvrım yapar."""
    km = KAFTAN if near else KAFTAN_B
    # iki yanı farklı profilli: dış yan (ön, +) omuz kasıyla şişkin, iç yan (arka, -) düz ve dirsekte kumaş birikir
    pts = []
    prof_o = [(0.0, 3.3), (0.18, 3.75), (0.4, 3.45), (0.7, 3.0), (0.92, 2.75), (1.04, 2.2)]
    prof_i = [(1.04, -2.2), (0.9, -3.05), (0.72, -3.15), (0.45, -2.95), (0.15, -3.2), (0.0, -3.1)]
    for t, o in prof_o + prof_i:
        pts.append(_al(sh, e, t, o))
    up = ik.union(cv.blob(pts), cv.capsule(sh, sh, 3.2 * AW, 3.2 * AW))
    det = []
    if near:
        # dirsek içinde toplanan kumaş: üç kısa zikzak kıvrım (gölge kaması + incelen çizgi)
        det += cv.fold([_al(sh, e, 0.62, -3.0), _al(sh, e, 0.7, -1.4), _al(sh, e, 0.8, -0.2)], 0.55, 1.25, 1, (0.1, 0.7))
        det += cv.fold([_al(sh, e, 0.78, -3.0), _al(sh, e, 0.86, -1.6)], 0.45, 1.15, 1, (0.1, 0.7))
        det += cv.fold([_al(sh, e, 0.35, 2.9), _al(sh, e, 0.5, 1.4), _al(sh, e, 0.56, 0.2)], 0.5, 1.1, -1, (0.1, 0.8))
        # kas çizgisi (deltoid alt sınırı): kısa, ince iç kontur
        det.append(('ink', [_al(sh, e, 0.3, 3.2), _al(sh, e, 0.42, 2.2), _al(sh, e, 0.46, 1.0)], 1.0, (0.1, 0.9)))
    cv.shape(up, km, z=z, sd=2.6, details=det, bounce=0.3 if near else 0.0)


def _fore(cv, e, h, z, near=True):
    """Ön kol: dirsek çıkıntısı, kas şişkinliği bileğe incelir; kol ağzı (altın sırma), deri bağcıklı siper + çelik şerit."""
    km = KAFTAN if near else KAFTAN_B
    prof_o = [(-0.05, 2.6), (0.12, 3.0), (0.3, 3.05), (0.55, 2.6), (0.8, 2.15), (1.0, 1.95)]
    prof_i = [(1.0, -1.9), (0.8, -2.05), (0.5, -2.55), (0.22, -2.95), (0.04, -2.75), (-0.08, -2.0)]
    fore = cv.blob([_al(e, h, t, o) for t, o in prof_o + prof_i])
    fore = ik.union(fore, cv.capsule(e, e, 2.55 * AW, 2.55 * AW))
    det = []
    if near:
        det += cv.fold([_al(e, h, 0.08, -2.4), _al(e, h, 0.2, -0.6), _al(e, h, 0.3, 1.2)], 0.5, 1.15, 1, (0.1, 0.7))
        det += cv.fold([_al(e, h, 0.28, -2.6), _al(e, h, 0.38, -1.2)], 0.4, 1.05, 1, (0.1, 0.7))
    cv.shape(fore, km, z=z, sd=2.3, details=det, bounce=0.3 if near else 0.0)
    # kol ağzı: sırma bant (kumaşın üstünde, siperin hemen üstü)
    cuff = ik.isect(fore, cv.poly([_al(e, h, 0.44, -4.0), _al(e, h, 0.44, 4.0), _al(e, h, 0.53, 4.0), _al(e, h, 0.53, -4.0)]))
    cv.shape(cuff, EMBR if near else EMBR.darker(0.75), z=z + 0.05, sd=0.8, hi=0.25 if near else 0.0, ol=0.7, spec=0.6,
             details=[('ink', [_al(e, h, 0.48, -2.8), _al(e, h, 0.48, 2.8)], 0.8, (0.05, 0.05))])
    br = cv.blob([_al(e, h, 0.54, 2.75), _al(e, h, 0.72, 2.45), _al(e, h, 0.9, 2.2), _al(e, h, 0.95, 1.6),
                  _al(e, h, 0.95, -1.6), _al(e, h, 0.9, -2.1), _al(e, h, 0.72, -2.3), _al(e, h, 0.54, -2.6)])
    bm = BRACER if near else BRACER.darker(0.72)
    bdet = []
    if near:
        # çapraz bağcık + çelik şerit + perçinler
        for tt in (0.6, 0.7, 0.8):
            bdet.append(('stroke', [_al(e, h, tt, -1.6), _al(e, h, tt + 0.08, 1.6)], 0.9, (0.86, 0.74, 0.52), (0.1, 0.1)))
            bdet.append(('stroke', [_al(e, h, tt, 1.6), _al(e, h, tt + 0.08, -1.6)], 0.9, (0.74, 0.6, 0.4), (0.1, 0.1)))
        bdet.append(('col', cv.limb([_al(e, h, 0.57, 2.0), _al(e, h, 0.9, 1.7)], [0.55, 0.45]), STEEL.base))
        bdet.append(('stroke', [_al(e, h, 0.6, 1.85), _al(e, h, 0.84, 1.6)], 0.8, (1.0, 1.0, 1.0), (0.3, 0.6)))
        bdet.append(('ink', [_al(e, h, 0.93, -2.0), _al(e, h, 0.93, 2.0)], 1.2, (0.1, 0.1)))
    cv.shape(br, bm, z=z + 0.1, sd=1.4, hi=0.3 if near else 0.0, details=bdet)


def _fist(cv, e, h, z, near=True):
    """Eldivenli yumruk: köşeli-yuvarlak kütle, sarılı başparmak, parmak araları ve boğum parlaması."""
    gm = GLOVE if near else GLOVE.darker(0.8)
    fist = cv.blob([_al(e, h, 0.86, -2.1), _al(e, h, 0.86, 2.0), _al(e, h, 0.97, 2.75), _al(e, h, 1.1, 2.7),
                    _al(e, h, 1.2, 2.2, ), _al(e, h, 1.25, 0.6), _al(e, h, 1.24, -1.4), _al(e, h, 1.14, -2.4),
                    _al(e, h, 0.98, -2.5)])
    det = []
    if near:
        for o in (-1.2, 0.2, 1.5):    # parmak araları (yumruğun ucuna doğru)
            det.append(('ink', [_al(e, h, 1.14, o), _al(e, h, 1.25, o + 0.1)], 1.0, (0.05, 0.8)))
        det.append(('ink', [_al(e, h, 1.0, 2.6), _al(e, h, 1.05, 1.0), _al(e, h, 1.03, -0.6)], 1.15, (0.1, 0.6)))
        det.append(('hi', cv.blob([_al(e, h, 1.15, 2.2), _al(e, h, 1.21, 1.6), _al(e, h, 1.19, 0.4), _al(e, h, 1.14, 1.2)])))
    cv.shape(fist, gm, z=z, sd=1.3, hi=0.35 if near else 0.0, details=det)
    # başparmak: yumruğun önünden sarılır
    th = cv.blob([_al(e, h, 0.92, 1.8), _al(e, h, 1.0, 2.95), _al(e, h, 1.12, 2.6), _al(e, h, 1.08, 1.4)])
    cv.shape(th, gm, z=z + 0.05, sd=0.8, hi=0.25 if near else 0.0, ol=0.8)


def _arm(cv, sh, e, h, z, near=True, pauldron=True):
    _upper(cv, sh, e, z, near)
    _fore(cv, e, h, z + 0.1, near)
    _fist(cv, e, h, z + 0.4, near)
    if pauldron:
        _pauldron(cv, sh, e, z + 0.6, near)


# ------------------------------------------------------------ kol parçaları (oyunda Player.gd iskeletiyle sürülür)
ARM_CELL = (56, 68)       # doku pikseli (dünya 14 x 17, texel 4)
ARM_PIVOT = (28, 14)      # omuz / dirsek (dünya 7, 3.5)
FIST_PIVOT = (28, 34)     # yumruk merkezi


def render_arm_parts(ss=4, mirror=False):
    """[upper, fore, fist, upper_b, fore_b, fist_b]: +y kemik yönü, pivot = kemik başı.
    mirror=True: ışık parçanın ekseninde aynalanır (sağ üstten). Oyunda ink_char.gdshader iki satırı parçanın ekrandaki
    açısı ve aynalanmasına göre karıştırır: kol başın üstüne kalksa da gölge hep dünya ışığının tersinde kalır."""
    out = []
    light = (-ik.LIGHT[0], ik.LIGHT[1]) if mirror else ik.LIGHT
    for near in (True, False):
        for kind in ('upper', 'fore', 'fist'):
            piv = FIST_PIVOT if kind == 'fist' else ARM_PIVOT
            cv = ik.InkCanvas(ARM_CELL[0], ARM_CELL[1], piv[0], piv[1], k=TEX, ss=ss, light=light)
            if kind == 'upper':
                _upper(cv, (0, 0), (0, L_UP), 0, near)
                _pauldron(cv, (0, 0), (0, L_UP), 1, near)
            elif kind == 'fore':
                _fore(cv, (0, 0), (0, L_FORE), 0, near)
            else:
                _fist(cv, (0, -L_FORE), (0, 0), 0, near)
            rgba, nm, em = cv.finish(outer=0.4)
            out.append(rgba)
    return out


def _pauldron(cv, sh, e, z, near):
    """Lamel omuzluk: üç sıra plaka, kolun üstüne biner."""
    n, d = _perp(sh, e)
    pts = [_alp(sh, e, -0.28, -2.2), _alp(sh, e, -0.3, 1.6), _alp(sh, e, -0.05, 3.7), _alp(sh, e, 0.3, 3.6),
           _alp(sh, e, 0.45, 2.0), _alp(sh, e, 0.42, -1.4), _alp(sh, e, 0.2, -3.4)]
    path = cv.blob(pts)
    det = []
    for t in (0.0, 0.17, 0.32):
        det.append(('ink', [_alp(sh, e, t - 0.02, -3.4), _alp(sh, e, t + 0.04, 0.0), _alp(sh, e, t - 0.02, 3.6)], 1.15, (0.15, 0.15)))
    cv.shape(path, STEEL if near else STEEL_B, z=z, sd=1.5, hi=0.5 if near else 0.0, details=det)


def _scarf_tails(cv, root, pk, bp, z, k=1.0):
    if pk <= 0:
        u_ = max(0.0, min(1.0, 1.0 + pk)) * 0.5
        a0, bend = math.pi * (0.95 - 0.12 * u_), -(0.03 + 0.10 * u_)
    else:
        r_ = min(1.0, pk / 1.1)
        a0, bend = math.pi * (0.89 + 0.17 * r_), -0.09 + 0.15 * r_
    dr = max(0.0, min(1.0, 1.0 - abs(pk) / 0.7))
    a0 = a0 + (math.pi * 0.62 - a0) * dr * 0.85
    bend = bend + (-0.05 - bend) * dr * 0.85
    ks = k
    for k, (n, seg, w0, dph, da) in enumerate(((9, 3.3, 3.6, 0.0, 0.0), (7, 3.0, 2.8, 1.3, 0.22))):
        sc = chain(root, n, seg * ks, a0 + da + (1.0 - ks) * 0.9, bend * (1.0 + 0.5 * k), bp * 6.28 - 0.9 - dph, 0.75 + 0.15 * k)
        q = [cv.W(p) for p in sc]
        ph = bp * 6.28 * 0.5 + k * 0.7
        prof = lambda s, ph=ph: max(0.18, (1 - 0.55 * s) * (0.45 + 0.55 * abs(math.cos(s * 5.2 + ph))))
        path = ik.taper_path(q, cv.u(w0 * (0.6 + 0.4 * ks)), prof=prof)
        m = SCARF if k == 0 else SCARF_B
        cv.shape(path, m, z=z - k * 0.5, sd=0.9, hi=0.3 if k == 0 else 0.0)
        ex, ey = sc[-1]
        # püskül + altın halka
        cv.shape(ik.union(*[cv.capsule((ex, ey), (ex - 1.0 + j * 0.7, ey + 2.8 + j * 0.15), 0.5, 0.3) for j in range(3)]),
                 KAFTAN, z=z + 0.2 - k * 0.5, sd=0.5, ol=0.7)
        cv.shape(cv.ellipse((ex, ey), 1.0, 1.0), GOLD, z=z + 0.3 - k * 0.5, sd=0.6, hi=0.3, ol=0.8)


def _xf(cv, p):
    """Tuvalin dünya->dünya dönüşüm yığınını (yuvarlanma vb.) bir noktaya uygula (çapa kaydı için; cihaz ölçeği yok)."""
    x, y = p[0], p[1]
    for f in reversed(cv.xf):
        x, y = f((x, y))
    return (x, y)


def _head(cv, head, neck, p, z):
    """Bengü'nün başı: insan yüzü (yandan, sağa bakan) + ak kurt başlığı (Asena soyu). Kurdun üst kafatası başın üstüne
    oturur: kalın burnu alnın üstünden öne uzanır, kulakları dik, üst çenenin iki köpek dişi alnın önünde sarkar; yan
    postu başın arkasını örtüp boyunda omuz postuna (pelerin) bağlanır. Yüz kurt burnunun gölgesinde: badem göz (Kut
    ışığı: camgöbeği bebek), kalın kaş, kırmızı savaş boyası (elmacık kemiği), ince dudak; yüzü şakaktan inen bir saç
    tutamı çerçeveler. Uzun saç oyunda çizilir (scripts/core/BenguSac.gd): başlığın arka kenarının altından ('sac')."""
    hx_, hy_ = head
    jaw = p.get('jaw', 0.0)
    bp = p.get('bp', 0.0)
    lean = p['lean']
    ear = p.get('ear', 0.0) + max(0.0, lean - 0.1) * 0.6 + math.sin(bp * 6.28 - 1.4) * 0.05

    def H(x, y, *k):       # başlık koordinatı (baş merkezine göre)
        return (hx_ + x, hy_ + y - 0.3) + tuple(k)

    FS, FX0, FY0 = 1.18, 0.4, 0.8

    def F(x, y, *k):       # yüz koordinatı: yüz başlığa göre 1,18 büyük (oyun yakınlığında okunsun)
        return (hx_ + FX0 + (x - FX0) * FS, hy_ + FY0 + (y - FY0) * FS) + tuple(k)

    # ---- kulaklar: uzak kulak başlığın arkasında, yakın kulak önünde (iç kulak gölgesi + kıl çizgisi)
    for near in (False, True):
        if near:
            b0, b1, ln, a_ = H(-0.1, -4.9), H(2.5, -4.6), 5.2, -math.pi * 0.5 - 0.22 - ear
            mat, zz = FUR, z + 2.2
            org = H(0.9, -4.9)
        else:
            b0, b1, ln, a_ = H(-2.9, -4.0), H(-0.3, -5.1), 4.7, -math.pi * 0.5 - 0.42 - ear
            mat, zz = FUR_B, z - 0.8
            org = H(-1.7, -4.7)
        tip = (org[0] + math.cos(a_) * ln, org[1] + math.sin(a_) * ln)
        m0, m1 = lerp2(b0, tip, 0.55), lerp2(b1, tip, 0.55)
        e_path = cv.blob([b0, (m0[0] - 0.45, m0[1]), (tip[0], tip[1], 0.0), (m1[0] + 0.35, m1[1] + 0.1), b1])
        det = []
        if near:
            i0, i1 = lerp2(b0, b1, 0.28), lerp2(b0, b1, 0.8)
            itip = lerp2(lerp2(b0, b1, 0.5), tip, 0.8)
            det.append(('col', cv.blob([i0, lerp2(i0, itip, 0.6), (itip[0], itip[1], 0.0), lerp2(i1, itip, 0.5), i1]), EAR_IN.shadow))
            det.append(('ink', [lerp2(b0, tip, 0.2), lerp2(b0, tip, 0.75)], 1.0, (0.2, 0.8)))
        cv.shape(e_path, mat, z=zz, sd=1.5, details=det, fur=0.4)

    # ---- yüz (ten): profil alından çeneye; arka yarısı başlığın yan postunun altında kalır
    jw = jaw * 0.9
    face = cv.blob([F(-1.2, -3.2), F(1.4, -3.4), F(2.75, -2.6), F(3.2, -1.65), F(3.0, -1.0), F(3.62, 0.15, 0.4),
                    F(3.45, 0.55, 0.5), F(3.05, 0.7), F(3.22, 1.12), F(2.98, 1.42 + jw * 0.35), F(3.12, 1.8 + jw),
                    F(2.92, 2.4 + jw), F(2.62, 2.95 + jw, 0.6), F(1.6, 3.12 + jw * 0.6), F(0.2, 2.6), F(-1.3, 0.6)])
    fdet = [
        # kurt burnunun yüze düşen gölgesi (alnın üstü)
        ('shade', cv.blob([F(-1.0, -3.6), F(3.6, -3.6), F(3.15, -2.2), F(2.2, -1.95), F(1.0, -2.05), F(-1.0, -1.8)])),
        # kaş: kalın, hafif kavisli; göz: badem, üst kirpik çizgisi geriye kuyruklu
        ('ink', [F(1.05, -1.45), F(2.0, -1.72), F(3.0, -1.55)], 2.0, (0.2, 0.45)),
        ('col', cv.blob([F(2.78, -0.88, 0.0), F(2.15, -1.16), F(1.3, -1.0), F(1.42, -0.55, 0.0), F(2.2, -0.52)]), (0.97, 0.94, 0.9)),
        ('col', cv.ellipse(F(2.2, -0.84), 0.42 * FS, 0.44 * FS), (0.05, 0.3, 0.36)),
        ('col', cv.ellipse(F(2.3, -0.92), 0.16 * FS, 0.16 * FS), (0.62, 1.0, 1.0)),
        ('ink', [F(2.85, -0.95), F(2.1, -1.22), F(1.25, -1.05), F(0.8, -0.85)], 1.7, (0.12, 0.7)),
        ('ink', [F(2.6, -0.55), F(1.7, -0.5)], 0.8, (0.4, 0.4)),
        # burun kanadı + ağız çizgisi + dudak rengi
        ('ink', [F(3.0, 0.38), F(2.72, 0.52), F(2.75, 0.7)], 0.9, (0.3, 0.3)),
        ('col', cv.blob([F(3.3, 1.02), F(3.0, 1.38 + jw * 0.3), F(3.18, 1.85 + jw), F(2.7, 1.72 + jw * 0.8), F(2.72, 1.18)]), (0.74, 0.3, 0.32)),
        ('ink', [F(3.06, 1.42 + jw * 0.35), F(2.55, 1.5 + jw * 0.4)], 1.0, (0.1, 0.7)),
        # savaş boyası: elmacık kemiği boyunca kalın kırmızı çizgi + altında ince ikinci çizgi; çenede dikey çizgi
        ('stroke', [F(2.75, -0.12), F(1.9, 0.02), F(0.4, 0.15)], 2.4, PAINT, (0.12, 0.7)),
        ('stroke', [F(2.45, 0.5), F(1.7, 0.6), F(0.7, 0.7)], 1.3, PAINT, (0.12, 0.7)),
        ('stroke', [F(2.45, 2.3 + jw), F(2.4, 3.0 + jw)], 1.2, PAINT, (0.2, 0.3)),
        # elmacık/çene gölge kaması
        ('shade', cv.wedge([F(0.8, 1.0), F(1.5, 2.0), F(2.5, 2.75)], 0.45, -1.0)),
    ]
    if jaw > 0.3:   # savaş narası: açık ağız
        fdet.append(('col', cv.blob([F(3.05, 1.3), F(2.5, 1.45), F(2.65, 1.75 + jw), F(3.1, 1.75 + jw)]), (0.3, 0.06, 0.1)))
    cv.shape(face, SKIN, z=z + 0.4, sd=0.75, hi=0.25, details=fdet, bounce=0.35, soft=0.25)
    # boyun (ince, uzun)
    cv.shape(cv.capsule(F(0.6, 2.4), (neck[0] + 0.6, neck[1] + 0.6), 1.5, 1.8), SKIN, z=z - 0.2, sd=1.0, ol=0.9)

    # ---- yüzü çerçeveleyen saç tutamı (şakaktan çene altına; başlığın kenarının önünde)
    lock = ik.taper_path([cv.W(F(1.0, -2.6)), cv.W(F(0.45, -0.8)), cv.W(F(0.35, 1.4)), cv.W(F(0.75, 3.6 + jw * 0.5))],
                         cv.u(1.15), prof=lambda s: max(0.2, max(0.0, 1.0 - s) ** 0.7) * (0.6 + 0.4 * min(1.0, s * 6.0)))
    cv.shape(lock, HAIR, z=z + 1.95, sd=0.6, hi=0.0, ol=0.7,
             details=[('stroke', [F(0.85, -2.0), F(0.55, -0.4), F(0.5, 1.2)], 0.8, HAIR.hi, (0.3, 0.6))])
    # alına düşen kısa kâkül (kurt burnunun altından)
    bang = ik.taper_path([cv.W(F(2.0, -2.7)), cv.W(F(2.55, -2.05)), cv.W(F(2.8, -1.7))], cv.u(0.85), (0.1, 0.9))
    cv.shape(bang, HAIR, z=z + 0.6, sd=0.4, ol=0.6)

    # ---- kurt başlığı: kafatası + kalın burun + yüzü çevreleyen yan post (tek kontur)
    hood = cv.blob([H(-4.2, 1.9), H(-4.5, -1.4), H(-3.6, -3.9), H(-1.6, -5.5), H(1.1, -5.9), H(3.0, -5.5), H(4.0, -4.8),
                    H(5.4, -4.6), H(6.9, -4.35), H(7.9, -4.05), H(8.4, -3.5, 0.5), H(8.35, -2.8, 0.5), H(7.75, -2.3),
                    H(6.8, -1.75), H(5.6, -1.6), H(4.4, -1.75), H(3.4, -1.95), H(2.4, -2.35, 0.5), H(1.1, -2.1),
                    H(0.2, -0.7), H(-0.15, 1.3), H(0.25, 3.3), H(-0.1, 4.7), H(-1.8, 5.1), H(-3.5, 4.0)])
    hdet = [
        # kaş çıkıntısı (gölge kaması + mürekkep), burun sırtı, üst dudak (sarkık) çizgisi ve altındaki gölge
        ('deep', cv.wedge([H(3.3, -4.65), H(4.6, -4.4), H(5.9, -4.05)], 0.5, 1.0)),
        ('ink', [H(3.2, -4.8), H(4.6, -4.55), H(6.0, -4.15)], 2.0, (0.15, 0.7)),
        ('ink', [H(6.2, -4.2), H(7.2, -4.0), H(7.7, -3.85)], 1.0, (0.3, 0.6)),
        ('ink', [H(7.9, -2.5), H(7.0, -2.25), H(6.0, -2.3), H(5.6, -1.95)], 1.4, (0.2, 0.5)),
        ('shade', cv.wedge([H(7.7, -2.25), H(5.8, -1.7), H(3.6, -1.95)], 0.5, 1.0)),
        # yan postun yüz kenarı: içe dönük kıl tutamları (gölge) + kalın iç kontur
        ('shade', cv.wedge([H(1.3, -2.2), H(0.4, -0.6), H(0.05, 1.4), H(0.35, 3.4)], 0.75, -1.0)),
        ('ink', [H(-0.4, -1.8), H(-1.0, -0.2), H(-0.8, 1.2)], 1.1, (0.4, 0.4)),
        ('ink', [H(-1.9, 0.8), H(-2.5, 2.4), H(-1.9, 3.8)], 1.1, (0.4, 0.4)),
        ('ink', [H(-2.9, -2.6), H(-1.7, -1.6)], 1.0, (0.4, 0.4)),
        # kurt yüzünün ak-gri maskesi: alnın gerisi koyu eyer lekesi
        ('col', cv.blob([H(-3.6, -3.4), H(-1.4, -5.2), H(1.6, -5.5), H(0.8, -4.2), H(-1.2, -2.6), H(-3.4, -1.4)]), FUR_B.base),
        # Kut damgası: kurt alnında kırmızı tamga, burun yanında boya (eski kurt başının boyası)
        ('stroke', [H(2.4, -5.3), H(3.2, -4.95), H(3.8, -5.05)], 1.6, PAINT, (0.2, 0.4)),
        ('stroke', [H(6.6, -2.95), H(5.3, -2.85), H(4.2, -3.05)], 1.8, PAINT, (0.15, 0.6)),
    ]
    cv.shape(hood, FUR, z=z + 1.6, sd=1.7, hi=0.35, details=hdet, cast=0.5, bounce=0.35, fur=0.7)
    # kurdun gözü: dar, camgöbeği ışıyan (Kut gözü kimliği başlıkta yaşar)
    cv.fill(cv.blob([H(4.25, -3.75, 0.0), H(4.95, -4.1), H(5.75, -3.88, 0.0), H(5.0, -3.58)]), EYE, z=z + 1.9, glow=EYE_GLOW)
    cv.fill(cv.ellipse(H(5.1, -3.84), 0.18, 0.21), (0.05, 0.25, 0.32), z=z + 1.95)
    # burun ucu (iri, siyah, parlak)
    cv.shape(cv.blob([H(7.55, -4.2), H(8.45, -3.95), H(8.6, -3.25, 0.4), H(7.95, -3.05)]), NOSE, z=z + 2.0, sd=0.5, hi=0.3, ol=0.7)
    # üst çenenin köpek dişleri (alnın önünde sarkar)
    for fx_, fy_, ln in ((6.7, -1.85, 1.25), (4.6, -1.8, 1.0)):
        cv.shape(cv.blob([H(fx_ + 0.34, fy_), H(fx_ - 0.32, fy_), H(fx_ + 0.02, fy_ + ln, 0.0)]), TOOTH, z=z + 1.5, sd=0.3, ol=0.6, hi=0.0)


def draw(cv, p, front_arm=True, back_arm=True):
    bob, lean = p['bob'], p['lean']
    sk, pk, bp = p.get('sk', 0.0), p.get('pk', 0.0), p.get('bp', 0.0)
    br = p.get('br', 0.0)
    tw = p.get('tw', 0.0)
    hip = (p.get('hx', 0.0), HIP_Y + bob * 1.1)
    curl = p.get('curl', 0.0)       # yuvarlanma topu: sırt kıvrılır, gövde ekseni kısalır
    tl = TORSO * (1.0 - 0.32 * curl) + br * 0.3
    neck = (hip[0] + math.sin(lean) * tl, hip[1] - math.cos(lean) * tl)
    sx = p.get('sx', 0.0)
    sh_f = (neck[0] + 1.4 + sx + tw * 0.7, neck[1] + 3.2)
    sh_b = (neck[0] - 2.8 - sx * 0.5 - tw * 0.7, neck[1] + 3.0)
    head = (neck[0] + 1.6 + math.sin(lean) * 1.6 + p.get('hdx', 0.0), neck[1] - 4.6 + p.get('hdy', 0.0))
    out = {'sh_f': sh_f}
    nx_, ny_ = neck
    ts_ = tl / (TORSO + br * 0.3) if curl else 1.0
    ax = (math.sin(lean) * ts_, -math.cos(lean) * ts_)
    pe = (math.cos(lean), math.sin(lean))
    T = _T(hip, ax, pe)

    # ---- turkuaz kuşağın iki kuyruğu (belin arkasından sarkar; en arkada). Uzun saç ve post oyunda (BenguSac.gd).
    _scarf_tails(cv, T(4.6, -5.2), pk, bp, -14, k=0.62)

    # ---- arka kol
    e, h = fk_arm(sh_b, p['ab'][0], p['ab'][1], L_UP, L_FORE)
    if back_arm:
        _arm(cv, sh_b, e, h, -12.5, near=False)
    out['hand_b'] = h
    out['ang_b'] = p['ab'][0] + p['ab'][1]
    out['sh_b'] = sh_b
    out['arm_b'] = (p['ab'][0], p['ab'][1])

    # ---- kaftan arka eteği (astar)
    bot = hip[1] + 7.8     # uyluk ortası: bol şalvar görünür (Shinobi siluetine yakın)
    flap = sk * 2.4
    back_sk = cv.blob([(hip[0] - 5.8, hip[1] - 1.0), (hip[0] - 0.5, hip[1] - 1.0), (hip[0] - 1.6 + flap * 0.6, bot + 0.4, 0.0),
                       (hip[0] - 5.0 + flap * 1.1, bot + 0.1), (hip[0] - 9.2 + flap * 1.6, bot - 0.9, 0.0)])
    cv.shape(back_sk, KAFTAN_B, z=-11, sd=2.4,
             details=[('ink', [(hip[0] - 3.0, hip[1] + 1.0), (hip[0] - 3.8 + flap, bot - 0.5)], 1.3)])

    # ---- arka bacak
    _leg(cv, hip, p['lb'], -10, False)

    # ---- gövde (kaftan)
    # kadın savaşçı gövdesi: omuzlar biraz dar, bel ince (kuşakla sıkılı), kalça hafif geniş; göğüs lamel yeleğin altında
    torso = cv.blob([T(-1.0, -5.9), T(3.4, -5.0), T(7.2, -4.6), T(11.0, -5.5 - br * 0.1), T(15.0, -5.5), T(17.6, -3.0),
                     T(18.4, 0.4), T(16.8, 4.0), T(14.2, 5.8 + br * 0.25), T(11.4, 5.5), T(8.0, 4.4), T(4.4, 4.5),
                     T(1.0, 5.5), T(-1.0, 5.9)])
    tdet = cv.fold([T(13.0, -4.8), T(9.0, -3.4), T(5.0, -3.8)], 0.7, 1.4, 1)
    for v in (-4.0, -2.0):   # kemer üstünde kumaş bolluğu
        tdet += cv.fold([T(4.4, v), T(3.0, v + 0.8), T(2.6, v + 1.6)], 0.5, 1.2, 1)
    cv.shape(torso, KAFTAN, z=0, sd=4.6, hatch=0.45, deep=0.3, details=tdet, bounce=0.35)
    # lamel yelek (göğüs + karın; arka kenarı deri şeritli)
    vest = cv.blob([T(1.8, -2.6), T(8.6, -2.7), T(14.6, -2.2), T(16.2, 1.0), T(15.4, 4.3), T(13.6, 5.7 + br * 0.2),
                    T(11.0, 5.3), T(7.6, 4.3), T(2.0, 5.0)])
    vdet = []
    rows = (2.8, 5.4, 8.0, 10.6, 13.2)
    for i, u in enumerate(rows):
        vdet.append(('shade', cv.wedge([T(u + 2.6, -3.4), T(u + 2.4, 1.0), T(u + 2.6, 6.0)], 0.45, 1.0)))
        vdet.append(('ink', [T(u, -3.4), T(u - 0.3, 1.0), T(u, 6.0)], 1.25, (0.06, 0.06)))
        for j, v in enumerate((-2.0, 0.2, 2.4, 4.6)):
            vv = v + (1.1 if i % 2 else 0.0)
            vdet.append(('ink', [T(u + 0.2, vv), T(u + 2.4, vv)], 1.1, (0.1, 0.25)))
        vdet.append(('stroke', [T(u + 0.6, -1.6), T(u + 0.55, -0.6)], 1.1, STEEL.hi, (0.2, 0.2)))
    vdet.append(('stroke', [T(1.8, -2.6), T(8.6, -3.0), T(14.6, -2.2)], 2.4, BELT.base, (0.0, 0.0)))
    vdet.append(('ink', [T(1.8, -1.7), T(8.6, -2.1), T(14.6, -1.3)], 1.0, (0.0, 0.0)))
    cv.shape(vest, STEEL, z=3.0, sd=3.0, hi=0.5, details=vdet, cast=0.6)
    # turkuaz kuşak: belde iki kat sarılı (yeleğin üstünde, kemerin üstünde), arkada düğüm
    sash_pts = [T(4.5 - 0.5 * math.cos(math.pi * 0.5 * v / 5.6) ** 2, v) for v in (-5.4, -3.2, -1.0, 1.2, 3.4, 4.9)]
    sash = ik.union(*[cv.capsule(a_, b_, 1.35, 1.35) for a_, b_ in zip(sash_pts, sash_pts[1:])])
    cv.shape(sash, SCARF, z=4.6, sd=1.0, hi=0.3, cast=0.5,
             details=[('ink', [T(4.2, -5.0), T(4.6, -1.0), T(4.4, 4.4)], 0.9, (0.2, 0.2)),
                      ('stroke', [T(5.2, -3.8), T(5.4, 0.0), T(5.2, 3.6)], 0.8, SCARF.hi, (0.3, 0.3))])
    cv.shape(cv.ellipse(T(4.5, -5.4), 1.7, 1.5, lean), SCARF, z=4.8, sd=0.8, hi=0.3, ol=0.9,
             details=[('ink', [T(3.6, -5.8), T(5.4, -5.0)], 1.0)])

    # ---- ön etek (diz boyu; önü açık kaftan dizleri izler: adım açılınca etek uyluğun üstünden gerilir)
    kf, _ = fk_leg((hip[0] + 1, hip[1]), p['lf'][0], p['lf'][1], L_THIGH, L_SHIN)
    raised = p['lf'][0] > 0.95       # diz göğse çekilmiş (sıçrama, tekme): ön bacak açık kaftanın önünden çıkar
    if raised:
        kf = (hip[0] + 4.0, hip[1] + 9.0)
    kb, _ = fk_leg(hip, p['lb'][0], p['lb'][1], L_THIGH, L_SHIN)
    # dizler kalçaya yaklaşınca (sıçrama, yuvarlanma) etek kutulaşmasın: uç en az kalçanın 5 birim altında
    F = (min(hip[0] + 11.0, max(hip[0] + 5.6, kf[0] + 2.6)) + sk * 1.6, max(hip[1] + 5.0, min(bot, kf[1] + 1.6)))
    B = (max(hip[0] - 11.0, min(hip[0] - 6.4, kb[0] - 2.4)) + sk * 2.8, max(hip[1] + 4.6, min(bot, kb[1] + 1.8) - 0.6))
    wav = [(F[0], F[1], 0.0)]
    for j, t in enumerate((0.2, 0.4, 0.6, 0.8)):
        q = lerp2(F, B, t)
        wav.append((q[0] + sk * 0.4 * t, q[1] + (0.75 if j % 2 == 0 else 0.15) + 0.6 * math.sin(math.pi * t)))
    wav.append((B[0], B[1], 0.0))
    hem_y = bot
    skirt = cv.blob([(hip[0] - 6.0, hip[1] - 2.2, 0.6), (hip[0] + 5.8, hip[1] - 2.2, 0.6)] + wav)
    sdet = []
    sh_paths = []
    for j, (u0, t) in enumerate(((-4.6, 0.9), (-2.6, 0.72), (-0.6, 0.55), (1.4, 0.4), (3.2, 0.24), (4.9, 0.1))):
        top_ = (hip[0] + u0, hip[1] + 1.2)
        q = lerp2(F, B, t)
        bt_ = (q[0], q[1] + 0.3)
        mid_ = (lerp2(top_, bt_, 0.5)[0] - 0.3, lerp2(top_, bt_, 0.5)[1])
        sdet += cv.fold([top_, mid_, bt_], 0.9 if j % 2 else 0.6, 1.4 if j % 2 else 1.1, -1, taper=(0.7, 0.05))
    cv.shape(skirt, KAFTAN, z=2.0, sd=3.2, shadows=sh_paths, details=sdet, hatch=0.45, deep=0.3, bounce=0.3)
    # altın sırma: etek ucuna paralel bant (eteğe kırpılır)
    hem_pts = [(x, y) for (x, y, *_) in wav]
    strip = ik.union(*[cv.capsule((x, y - 1.25), (x2, y2 - 1.25), 1.3, 1.3) for (x, y), (x2, y2) in zip(hem_pts, hem_pts[1:])])
    hem_strip = ik.isect(skirt, strip)
    cv.shape(hem_strip, EMBR, z=2.2, sd=0.8, hi=0.25, ol=0.6,
             details=[('ink', [(x, y - 1.25) for (x, y) in hem_pts], 0.9, (0.0, 0.0))])

    # ---- kemer: geniş deri, altın plakalar, sarkan kayışlar
    belt_pts = [T(1.6 - 0.8 * math.cos(math.pi * 0.5 * v / 6.0) ** 2, v) for v in (-5.6, -3.5, -1.2, 1.2, 3.5, 5.6)]
    belt = ik.union(*[cv.capsule(a, b, 1.6, 1.6) for a, b in zip(belt_pts, belt_pts[1:])])
    cv.shape(belt, BELT, z=5.0, sd=1.2, hi=0.3, cast=0.6)
    for q in belt_pts[1:-1]:
        cv.shape(cv.ellipse(q, 0.95, 1.1, lean), GOLD, z=7.4, sd=0.7, hi=0.35, ol=0.8)
    buck = T(1.0, 5.4)
    cv.shape(cv.ellipse(buck, 1.5, 1.7, lean), GOLD, z=8.2, sd=0.8, hi=0.4, ol=0.9)
    for dv, ln in ((2.8, 6.0), (4.4, 4.6)):
        a = T(0.6, dv)
        b = (a[0] + sk * 0.8 + 0.4, a[1] + ln)
        cv.shape(cv.capsule(a, b, 0.7, 0.55), BELT, z=8.4, sd=0.5, ol=0.8)
        cv.shape(cv.ellipse(b, 0.75, 0.85), GOLD, z=8.6, sd=0.5, hi=0.3, ol=0.8)
    pc = T(-0.6, -4.8)     # kese
    cv.shape(cv.blob([(pc[0] - 1.8, pc[1] - 1.6), (pc[0] + 1.8, pc[1] - 1.6), (pc[0] + 1.6, pc[1] + 2.0), (pc[0] - 1.4, pc[1] + 2.2)]),
             BOOT, z=6.0, sd=1.0, hi=0.25, details=[('ink', [(pc[0] - 1.6, pc[1] - 0.4), (pc[0] + 1.6, pc[1] - 0.6)], 1.2)])

    # ---- ön bacak
    k, f = _leg(cv, (hip[0] + 1, hip[1]), p['lf'], 6.0 if raised else 1.0, True, kz=7.0 if raised else 2.6)
    out['foot_f'] = f

    # ---- kurt postu pelerini: başlığın devamı, omuzları sarar ve sırtta kürek kemiğine dek iner; alt kenarı tutamlı
    edge = []
    nt = 9
    for i in range(nt + 1):
        t_ = i / nt
        q = lerp2(T(12.0, -6.4), T(15.2, 4.9), t_)
        if i % 2 == 1:
            dd = 0.95 + 0.35 * math.sin(i * 1.7 + bp * 6.28)
            q = (q[0] - ax[0] * dd + pe[0] * 0.2, q[1] - ax[1] * dd + pe[1] * 0.2, 0.0)
        edge.append(q)
    mantle = cv.blob([T(18.0, 3.8), T(19.1, 1.2), T(19.2, -2.2), T(17.9, -5.0), T(15.6, -6.3), T(12.8, -6.7) + (0.0,)] + edge)
    mdet = [('ink', [T(17.4, -4.6), T(14.8, -5.2), T(12.8, -4.6)], 1.0, (0.4, 0.4)),
            ('ink', [T(17.8, -1.0), T(15.6, -1.4)], 1.0, (0.4, 0.4)),
            ('shade', cv.wedge([T(13.0, -6.6), T(14.0, -2.0), T(15.0, 3.6)], 0.8, -1.0))]
    cv.shape(mantle, PELT, z=9.0, sd=1.9, hi=0.25, cast=0.8, details=mdet, fur=0.7)
    # ön pençe: postun ön ayağı omuzdan göğse sarkar (kısa, uca doğru genişleyen gri post, üç siyah tırnak); altın tokayla
    # (turkuaz taş) karşı pençeye bağlı
    pw0, pw1 = T(17.6, 3.0), T(14.4, 4.7)
    paw = ik.union(cv.capsule(pw0, pw1, 1.2, 1.35), cv.ellipse(T(13.8, 5.0), 1.55, 1.3, lean + 0.4))
    cv.shape(paw, PELT, z=14.4, sd=1.0, hi=0.25, cast=0.6, fur=0.6,
             details=[('ink', [T(16.6, 2.6), T(15.0, 3.6)], 0.9, (0.4, 0.4)),
                      ('ink', [T(13.2, 4.0), T(13.0, 5.0)], 0.8, (0.3, 0.3)), ('ink', [T(13.1, 5.4), T(12.9, 6.0)], 0.8, (0.3, 0.3))])
    for dv in (-0.7, 0.2, 1.1):
        c0 = T(12.6, 4.8 + dv)
        c1 = T(11.6, 5.2 + dv)
        cv.stroke([c0, c1], 1.3, z=14.6, taper=(0.1, 0.9))
    cv.shape(cv.ellipse(T(16.2, 3.9), 1.25, 1.25), GOLD, z=14.8, sd=0.7, hi=0.4, ol=0.9)
    cv.shape(cv.ellipse(T(16.2, 3.9), 0.6, 0.6), SCARF, z=14.9, sd=0.4, hi=0.3, ol=0.6)

    # ---- baş (boyun _head içinde)
    hs = HEAD_K
    cv.push(lambda q, c0=head: (c0[0] + (q[0] - c0[0]) * hs, c0[1] + (q[1] - c0[1]) * hs))
    _head(cv, head, neck, p, 10.0)
    cv.pop()
    out['head'] = head
    # çalışma zamanı saç çapaları (BenguSac.gd): 'sac' = saçın başlığın arka kenarından çıktığı ense noktası, 'sac_d' =
    # kökün ilk doğrultusu (ekran açısı, aşağı-geri), 'neck' / 'hip' = sırt çizgisi (saç gövdenin içine girmesin).
    # Tuval dönüşümü (yuvarlanma) uygulanmış hâlleri: saç topla birlikte döner.
    sac = (head[0] - 3.3, head[1] + 2.2)
    s0 = _xf(cv, sac)
    s1 = _xf(cv, (sac[0] - 0.5, sac[1] + 0.87))
    out['sac'] = s0
    out['sac_d'] = math.atan2(s1[1] - s0[1], s1[0] - s0[0])
    out['neck'] = _xf(cv, neck)
    out['hip'] = _xf(cv, hip)

    # ---- ön kol
    a1, a2 = p['af']
    e, h = fk_arm(sh_f, a1, a2, L_UP, L_FORE * p.get('ext', 1.0))
    if front_arm:
        _arm(cv, sh_f, e, h, 16.5, near=True)
    out['hand_f'] = h
    out['ang_f'] = a1 + a2
    out['arm'] = (a1, a2)
    return out


# ------------------------------------------------------------ pozlar (v2 iskeleti; Shinobi tarzı geniş, alçak, dinamik)
# Zamanlama (kare sayısı, fps, saldırı evreleri) v1/v2 ile aynı: Player.SWINGS kol iskeleti aynı karelerde sürülür.
# Yere basan pozlarda kalça yüksekliği ayaklardan çözülür (ground): bacak açıları büyüdükçe ayak yerden kalkmaz/gömülmez.
FOOT_Y = -2.1          # ayak ekleminin yerdeki yüksekliği (taban altı ~ +0.3: çimene hafif gömülü)


def foot_y(p):
    hip_y = HIP_Y + p['bob'] * 1.1
    ys = []
    for a in (p['lf'], p['lb']):
        ys.append(hip_y + math.cos(a[0]) * L_THIGH + math.cos(a[0] - a[1]) * L_SHIN)
    return max(ys)


def ground(p, lift=0.0):
    """Alttaki ayak yere değsin diye bob ayarı; lift > 0 gövdeyi havaya kaldırır (dünya birimi)."""
    q = dict(p)
    q['bob'] = p['bob'] + (FOOT_Y - lift - foot_y(p)) / 1.1
    return q


def grounded(fn, keep_air=True):
    """Poz fonksiyonunu yere basar hale getirir. keep_air: özgün pozda gövde v1'e göre kalkıyorsa (bob < -1) o kadar havada."""
    def g(t):
        p = fn(t)
        lift = max(0.0, -(p['bob'] + 1.0)) * 1.1 if keep_air else 0.0
        return ground(p, lift)
    return g


def dynamic(fn, k_leg=1.25, k_lean=1.15, k_hx=1.25):
    """v1 saldırı gövdelerini Shinobi duruşuna çevirir: daha açık adım, daha derin diz, daha çok eğilme."""
    def g(t):
        p = dict(fn(t))
        lf, lb = p['lf'], p['lb']
        p['lf'] = (lf[0] * k_leg + 0.08, lf[1] * 1.15 + 0.18)
        p['lb'] = (lb[0] * k_leg - 0.06, lb[1] * 1.1 + 0.12)
        p['lean'] = p['lean'] * k_lean + 0.04
        p['hx'] = p.get('hx', 0.0) * k_hx
        p['sk'] = p.get('sk', 0.0) * 1.1
        return p
    return g


ANIMS = dict(v2.ANIMS)


def _idle(t):
    s = math.sin(t * 6.28)
    # alçak, geniş savaş duruşu: dizler kırık, ağırlık arkada; nefesle omuz/göğüs; baş, etek, atkı gecikmeli
    return P(bob=1.4 + 0.35 * s, lean=0.16 + 0.02 * s, lf=(0.56, 0.78), lb=(-0.46, 0.36),
             af=(0.3 + 0.04 * s, 1.6 + 0.06 * s), ab=(-0.3 - 0.03 * s, 0.9 + 0.05 * s),
             sk=0.2 * math.sin(t * 6.28 - 0.6), pk=0.3 * s, bp=t, jaw=0.0, br=s, hdy=0.3 * math.sin(t * 6.28 - 0.8),
             sx=0.4)


def _idle_g(t):
    p = _idle(t)
    q = ground(dict(p, bob=0.0))
    q['bob'] += 0.35 * math.sin(t * 6.28)      # nefes: kalça hafifçe iner/kalkar (dizler esner)
    return q


def _run(t):
    ph = t * 6.28

    def legp(q):
        th = 0.98 * math.sin(q) + 0.08
        sw = max(0.0, math.cos(q))
        st = max(0.0, -math.cos(q))
        return (th, 0.22 + 1.85 * sw ** 1.4 + 0.36 * st ** 2)
    bob = 1.5 * math.cos(2 * ph) - 0.2
    return P(bob=bob, lean=0.34 + 0.04 * math.cos(2 * ph), lf=legp(ph), lb=legp(ph + math.pi),
             af=(-0.95 * math.sin(ph) + 0.2, 1.65 - 0.3 * math.sin(ph)), ab=(0.95 * math.sin(ph) + 0.1, 1.55 + 0.3 * math.sin(ph)),
             sk=-0.9 + 0.3 * math.sin(2 * ph - 1.2), pk=-1.1, bp=t * 2, tw=0.7 * math.sin(ph),
             hdy=0.4 * math.sin(2 * ph - 0.9), sx=0.3)


def _sprint(t):
    # ninja koşusu: gövde öne yatık, kollar geride savrulur, uzun adım, uçuş evresi belirgin
    ph = t * 6.28

    def legp(q):
        th = 1.18 * math.sin(q) + 0.12
        sw = max(0.0, math.cos(q))
        st = max(0.0, -math.cos(q))
        return (th, 0.25 + 2.1 * sw ** 1.3 + 0.4 * st ** 2)
    bob = 1.9 * math.cos(2 * ph) + 0.4
    return P(bob=bob, lean=0.62 + 0.04 * math.cos(2 * ph), lf=legp(ph), lb=legp(ph + math.pi),
             af=(-1.05 + 0.12 * math.sin(ph), 0.35), ab=(-1.25 - 0.12 * math.sin(ph), 0.25),
             sk=-1.2, pk=-1.5, bp=t * 2.5, tw=0.4 * math.sin(ph), hdy=0.6 + 0.3 * math.sin(2 * ph - 0.9), sx=-0.6)


JUMP = keyed((0.0, P(bob=-1.0, lean=0.5, lf=(1.15, 1.35), lb=(-0.95, 0.25), af=(-1.1, 0.6), ab=(-1.4, 0.4), sk=-1.1, pk=-1.4, hdy=-0.2, sx=-0.5)),
             (1.0, P(bob=-2.0, lean=0.42, lf=(1.4, 1.9), lb=(-0.6, 0.9), af=(-0.7, 1.2), ab=(-1.1, 0.7), sk=-1.2, pk=-1.5, hdy=-0.4)))
FALL = keyed((0.0, P(bob=-1.0, lean=0.12, lf=(0.85, 1.0), lb=(-0.1, 1.4), af=(1.4, 1.0), ab=(-1.3, 0.5), sk=0.7, pk=0.9)),
             (1.0, P(bob=0.0, lean=0.0, lf=(0.5, 0.4), lb=(-0.4, 0.9), af=(1.8, 0.7), ab=(-1.7, 0.4), sk=1.1, pk=1.25, hdy=0.3)))
LAND = keyed((0.0, P(bob=3.0, lean=0.42, lf=(1.05, 1.9), lb=(-0.75, 1.3), af=(0.7, 1.0), ab=(-0.7, 0.9), sk=0.5, pk=0.6, hdy=0.6)),
             (1.0, P(bob=1.4, lean=0.24, lf=(0.65, 0.95), lb=(-0.55, 0.6), af=(0.3, 0.9), ab=(-0.4, 0.7), sk=0.2, pk=0.3)))
HURT = keyed((0.0, P(lean=-0.5, af=(-1.3, 1.0), ab=(-1.6, 0.6), lf=(0.6, 0.5), lb=(-0.65, 0.5), sk=1.0, pk=1.2, jaw=0.9, hdy=-0.6, hdx=-0.8)),
             (1.0, P(lean=-0.25, af=(-0.7, 0.8), ab=(-0.9, 0.6), lf=(0.5, 0.6), lb=(-0.5, 0.5), sk=0.6, pk=0.8, jaw=0.3)))


def _smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def _roll(t):
    tuck = _smooth(0.02, 0.22, t) * (1.0 - _smooth(0.74, 0.92, t))
    turn = _smooth(0.04, 0.9, t)
    # dalış: gövde öne uzanır, kollar yere doğru
    ext = P(curl=0.0, bob=7.0, lean=0.95, lf=(1.2, 1.55), lb=(-0.35, 1.2), af=(1.25, 0.35), ab=(1.0, 0.5), sk=0.6, pk=-0.9,
            hdy=0.8, sx=-0.3)
    # top: uyluklar göğüse (gövde ekseni boyunca), baldırlar katlı, kollar baldırları sarar, baş içeri
    tk = P(bob=7.0, lean=1.45, lf=(1.85, 3.0), lb=(1.65, 2.95), af=(-0.6, 0.6), ab=(-0.85, 0.7), sk=0.7, pk=-1.1,
           hdy=2.4, hdx=-2.6, sx=-0.8, jaw=0.0, curl=1.0)
    # kalkış: çömelik, gövde dikleşiyor, kollar dengede
    rise = P(curl=0.0, bob=6.0, lean=0.5, lf=(1.15, 1.95), lb=(-0.55, 1.5), af=(0.7, 1.2), ab=(0.2, 1.0), sk=0.5, pk=-0.5, hdy=0.5)
    u = _smooth(0.74, 0.97, t)
    p = {}
    for k_, va in ext.items():
        vb = tk.get(k_, va)
        vr = rise.get(k_, va)
        if isinstance(va, tuple):
            q = tuple(x + (y - x) * tuck for x, y in zip(va, vb))
            p[k_] = tuple(x + (y - x) * u for x, y in zip(q, vr)) if t > 0.5 else q
        else:
            q = va + (vb - va) * tuck
            p[k_] = q + (vr - q) * u if t > 0.5 else q
    p['roll'] = turn
    p['tuck'] = tuck
    p['bp'] = t
    return p


def _crouch(t):
    return P(bob=9.0, lean=0.42, lf=(1.35, 2.35), lb=(-0.55, 2.0), af=(0.7, 1.3), ab=(0.3, 1.0), sk=0.5, pk=0.4, hdy=0.8 - 0.25 * t, sx=0.3)


def _crouch_atk(t):
    return P(bob=9.0, lean=0.5, lf=(1.35, 2.35), lb=(-0.55, 2.0), ab=(0.6, 0.6), sx=-1.0, sk=0.4, pk=0.3, hdy=0.8)


ANIMS['idle'] = (8, _idle_g, True, True)
ANIMS['run'] = (8, grounded(_run), True, True)
ANIMS['sprint'] = (8, grounded(_sprint), True, True)
ANIMS['jump'] = (3, JUMP, False, True)
ANIMS['fall'] = (3, FALL, False, True)
ANIMS['land'] = (2, grounded(LAND, False), False, True)
ANIMS['hurt'] = (3, grounded(HURT, False), False, True)
ANIMS['crouch'] = (2, grounded(_crouch, False), True, True)
ANIMS['crouch_atk'] = (1, grounded(_crouch_atk, False), False, False)
ANIMS['roll'] = (8, _roll, False, True)
for _an in ('atk_down', 'atk_up', 'atk_horiz', 'atk_thrust', 'atk_heavy', 'atk_spin', 'atk_lunge', 'atk_overhead_2h',
            'atk_backstep', 'atk_sweep_low', 'atk_uppercut', 'atk_lunge_long', 'atk_spin_2h', 'atk_dual', 'atk_whip',
            'atk_slam_jump', 'atk_throw_axe'):
    _n, _fn, _loop, _ar = v2.ANIMS[_an]
    ANIMS[_an] = (_n, grounded(dynamic(_fn)), _loop, _ar)
for _an in ('bow', 'throw', 'block', 'cast', 'drink'):
    _n, _fn, _loop, _ar = v2.ANIMS[_an]
    ANIMS[_an] = (_n, grounded(dynamic(_fn, 1.2, 1.1, 1.0), False), _loop, _ar)

SHADE = dict(outer=0.5, rim=0.0, form=(6.0, (0.8, 0.78, 0.9)))


def render_frame(anim, i, cell=CELL, feet=FEET, ss=3):
    n, fn, loop, arm = ANIMS[anim]
    t = (i / n) if loop else (min(0.999, i / n + 0.5 / n) if n > 1 else 0.0)
    p = fn(t)
    cv = ik.InkCanvas(cell[0], cell[1], feet[0], feet[1], k=TEX, ss=ss)
    if 'roll' in p:
        ang = p['roll'] * math.tau
        # dönme merkezi: topun ağırlık merkezi (kalça ile göğüs arası); top yere değer (yarıçap ~11, açık pozda ayaklar yerde)
        tk = p.get('tuck', 1.0)
        hip_y = HIP_Y + p['bob'] * 1.1
        piv = (5.0 * tk + 1.0, hip_y - 3.0 * tk)
        off = (piv[0] * (1 - tk) + 1.0 * tk, piv[1] * (1 - tk) + (-13.0) * tk)
        ca, sa = math.cos(ang), math.sin(ang)
        sq = 1.0 - 0.14 * tk       # topta hafif büzülme (çizgi film abartısı)

        def rot(q):
            x, y = (q[0] - piv[0]) * sq, (q[1] - piv[1]) * sq
            return (off[0] + x * ca - y * sa, off[1] + x * sa + y * ca)
        cv.push(rot)
        info = draw(cv, p, True)
        cv.pop()
    else:
        info = draw(cv, p, arm, arm)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
