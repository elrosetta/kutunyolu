"""Bengü — stil v2 "mürekkep-cel" (çizgi roman; bkz. inkkit.py). Piksel sanat değil: 3x doku yoğunluğu,
kenar yumuşatmalı vektör çizim, oyunda doğrusal süzgeç + mipmap.

İskelet ve çapalar bengu_v2 ile aynı (bacak 12 + 11.8, gövde 17, kol 10 + 9.4, kalça -23.6): Player.gd kol iskeleti,
silah tutuşu ve çarpışma kutuları değişmez. Kimlik: ak kurt başı (camgöbeği Kut gözü, kırmızı savaş boyası),
kırmızı kaftan (diz boyu, altın sırma), çelik lamel yelek + omuzluk + dizlik, geniş deri kemer ve altın plakalar,
çivit şalvar (çizme üstünde bollanır), uzun çizme, ak post yaka, iki kuyruklu turkuaz atkı.
"""
import math

import inkkit as ik
from inkkit import Ink, INK
import bengu_v2 as v2
from bengu import P, keyed
from rig import fk_leg, fk_arm, lerp2, chain

TEX = 3.0
CELL = (288, 240)        # dünya 96 x 80
FEET = (132, 222)        # dünya (44, 74)
L_THIGH, L_SHIN = 13.0, 12.6      # v2: 12 + 11.8; ninja oranı için uzun bacak (kalça yerden çözülür)
L_UP, L_FORE = v2.L_UP, v2.L_FORE
HIP_Y = v2.HIP_Y
TORSO = v2.TORSO
HEAD_K = 0.9            # baş ölçeği (küçük baş: ~7 baş boy)

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
    cv.shape(pants, pm, z=z, details=fold, sd=2.3 if near else 3.0, hi=0.0, hatch=0.55 if near else 0.0)
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
    km = KAFTAN if near else KAFTAN_B
    up = cv.limb([sh, lerp2(sh, e, 0.5), e], [3.5, 3.4, 2.7])
    det = cv.fold([along(sh, e, 0.45, -1.8), along(sh, e, 0.62, -0.2), along(sh, e, 0.78, 1.4)], 0.6, 1.3, 1) +         cv.fold([along(sh, e, 0.72, -2.2), along(sh, e, 0.86, -0.6)], 0.5, 1.2, 1)
    cv.shape(up, km, z=z, sd=2.6, details=det if near else ())


def _fore(cv, e, h, z, near=True):
    km = KAFTAN if near else KAFTAN_B
    fore = cv.limb([e, lerp2(e, h, 0.4), h], [2.7, 2.7, 2.0])
    cv.shape(fore, km, z=z, sd=2.3, details=cv.fold([along(e, h, 0.15, -2.0), along(e, h, 0.3, 0.0), along(e, h, 0.42, 1.8)], 0.5, 1.2, 1) if near else ())
    br = cv.limb([lerp2(e, h, 0.58), lerp2(e, h, 0.86)], [2.7, 2.3])
    bm = BRACER if near else BRACER.darker(0.72)
    a0, a1 = lerp2(e, h, 0.58), lerp2(e, h, 0.88)
    cv.shape(br, bm, z=z + 0.1, sd=1.4, hi=0.3 if near else 0.0,
             details=[('col', cv.limb([a0, a1], [0.55, 0.5]), (STEEL.base if near else STEEL_B.base)),
                      ('ink', [along(e, h, 0.9, -2.4), along(e, h, 0.9, 2.4)], 1.3, (0.1, 0.1))])


def _fist(cv, e, h, z, near=True):
    fist = cv.ellipse(h, 2.5, 2.6)
    cv.shape(fist, GLOVE if near else GLOVE.darker(0.8), z=z, sd=1.3, hi=0.35 if near else 0.0,
             details=[('ink', [along(e, h, 1.05, -1.4), along(e, h, 1.12, 0.0), along(e, h, 1.05, 1.4)], 1.2)] if near else ())


def _arm(cv, sh, e, h, z, near=True, pauldron=True):
    _upper(cv, sh, e, z, near)
    _fore(cv, e, h, z + 0.1, near)
    _fist(cv, e, h, z + 0.4, near)
    if pauldron:
        _pauldron(cv, sh, e, z + 0.6, near)


# ------------------------------------------------------------ kol parçaları (oyunda Player.gd iskeletiyle sürülür)
ARM_CELL = (42, 51)       # doku pikseli (dünya 14 x 17)
ARM_PIVOT = (21, 10.5)    # omuz / dirsek (dünya 7, 3.5)
FIST_PIVOT = (21, 25.5)   # yumruk merkezi


def render_arm_parts(ss=4):
    """[upper, fore, fist, upper_b, fore_b, fist_b]: +y kemik yönü, pivot = kemik başı."""
    out = []
    for near in (True, False):
        for kind in ('upper', 'fore', 'fist'):
            piv = FIST_PIVOT if kind == 'fist' else ARM_PIVOT
            cv = ik.InkCanvas(ARM_CELL[0], ARM_CELL[1], piv[0], piv[1], k=TEX, ss=ss)
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
    pts = [along(sh, e, -0.28, -2.2), along(sh, e, -0.3, 1.6), along(sh, e, -0.05, 3.7), along(sh, e, 0.3, 3.6),
           along(sh, e, 0.45, 2.0), along(sh, e, 0.42, -1.4), along(sh, e, 0.2, -3.4)]
    path = cv.blob(pts)
    det = []
    for t in (0.0, 0.17, 0.32):
        det.append(('ink', [along(sh, e, t - 0.02, -3.4), along(sh, e, t + 0.04, 0.0), along(sh, e, t - 0.02, 3.6)], 1.15, (0.15, 0.15)))
    cv.shape(path, STEEL if near else STEEL_B, z=z, sd=1.5, hi=0.5 if near else 0.0, details=det)


def _scarf_tails(cv, root, pk, bp, z):
    if pk <= 0:
        u_ = max(0.0, min(1.0, 1.0 + pk)) * 0.5
        a0, bend = math.pi * (0.95 - 0.12 * u_), -(0.03 + 0.10 * u_)
    else:
        r_ = min(1.0, pk / 1.1)
        a0, bend = math.pi * (0.89 + 0.17 * r_), -0.09 + 0.15 * r_
    dr = max(0.0, min(1.0, 1.0 - abs(pk) / 0.7))
    a0 = a0 + (math.pi * 0.62 - a0) * dr * 0.85
    bend = bend + (-0.05 - bend) * dr * 0.85
    for k, (n, seg, w0, dph, da) in enumerate(((9, 3.3, 3.6, 0.0, 0.0), (7, 3.0, 2.8, 1.3, 0.22))):
        sc = chain(root, n, seg, a0 + da, bend * (1.0 + 0.5 * k), bp * 6.28 - 0.9 - dph, 0.75 + 0.15 * k)
        q = [cv.W(p) for p in sc]
        ph = bp * 6.28 * 0.5 + k * 0.7
        prof = lambda s, ph=ph: max(0.18, (1 - 0.55 * s) * (0.45 + 0.55 * abs(math.cos(s * 5.2 + ph))))
        path = ik.taper_path(q, cv.u(w0), prof=prof)
        m = SCARF if k == 0 else SCARF_B
        cv.shape(path, m, z=z - k * 0.5, sd=0.9, hi=0.3 if k == 0 else 0.0)
        ex, ey = sc[-1]
        # püskül + altın halka
        cv.shape(ik.union(*[cv.capsule((ex, ey), (ex - 1.0 + j * 0.7, ey + 2.8 + j * 0.15), 0.5, 0.3) for j in range(3)]),
                 KAFTAN, z=z + 0.2 - k * 0.5, sd=0.5, ol=0.7)
        cv.shape(cv.ellipse((ex, ey), 1.0, 1.0), GOLD, z=z + 0.3 - k * 0.5, sd=0.6, hi=0.3, ol=0.8)


def _head(cv, head, neck, p, z):
    hx_, hy_ = head
    jaw = p.get('jaw', 0.0)
    bp = p.get('bp', 0.0)
    lean = p['lean']
    # uzak kulak (başın arkasında)
    ear = p.get('ear', 0.0) + max(0.0, lean - 0.1) * 0.7 + math.sin(bp * 6.28 - 1.4) * 0.05
    for (ox, mat, zz, ln, near) in ((-2.4, FUR_B, z - 0.5, 5.0, False), (-0.2, FUR, z + 1.5, 5.4, True)):
        b0 = (hx_ + ox - 2.4, hy_ - 1.8)
        b1 = (hx_ + ox + 2.3, hy_ - 3.1)
        a = -math.pi * 0.5 - 0.3 - ear
        tip = (hx_ + ox + math.cos(a) * ln, hy_ - 3.0 + math.sin(a) * ln)
        e_path = cv.blob([b0, (lerp2(b0, tip, 0.5)[0] - 0.5, lerp2(b0, tip, 0.5)[1]), (tip[0], tip[1], 0.0), (lerp2(b1, tip, 0.5)[0] + 0.3, lerp2(b1, tip, 0.5)[1]), b1])
        det = []
        if near:
            inner = cv.blob([lerp2(b0, b1, 0.3), lerp2(lerp2(b0, b1, 0.35), tip, 0.75), (lerp2(lerp2(b0, b1, 0.5), tip, 0.88)[0], lerp2(lerp2(b0, b1, 0.5), tip, 0.88)[1], 0.0), lerp2(b0, b1, 0.85)])
            det.append(('col', inner, EAR_IN.shadow))
        cv.shape(e_path, mat, z=zz, sd=1.6, details=det)
    # kafa: kafatası + güçlü burun + yanak yelesi (tek kontur)
    jw = jaw * 2.0
    skull = cv.blob([(hx_ - 3.6, hy_ + 0.4), (hx_ - 3.3, hy_ - 2.4), (hx_ - 1.3, hy_ - 4.0), (hx_ + 1.6, hy_ - 4.1),
                     (hx_ + 3.8, hy_ - 3.0), (hx_ + 5.0, hy_ - 2.0), (hx_ + 7.4, hy_ - 1.6), (hx_ + 9.2, hy_ - 1.2),
                     (hx_ + 9.9, hy_ - 0.6, 0.5), (hx_ + 9.9, hy_ + 0.9, 0.5), (hx_ + 9.0, hy_ + 1.9), (hx_ + 6.2, hy_ + 2.4),
                     (hx_ + 3.4, hy_ + 3.1), (hx_ + 1.0, hy_ + 3.9)])
    ruff = cv.blob(fur_ring((hx_ - 0.6, hy_ + 1.3), 3.9, 3.3, 0.3, math.pi * 0.2, math.pi * 1.12, 5, 0.45, 0.05, 0.95, 0.4)
                   + [(hx_ + 0.6, hy_ - 0.8)])
    head_p = ik.union(skull, ruff)
    lower = cv.blob([(hx_ + 2.8, hy_ + 2.4), (hx_ + 8.4, hy_ + 2.0 + jw * 0.5), (hx_ + 8.0, hy_ + 3.0 + jw * 0.9, 0.3),
                     (hx_ + 4.8, hy_ + 4.0 + jw), (hx_ + 2.0, hy_ + 4.2 + jw * 0.4)])
    if jaw > 0.25:
        mouth = cv.blob([(hx_ + 3.0, hy_ + 2.1), (hx_ + 8.6, hy_ + 1.6), (hx_ + 7.4, hy_ + 2.4 + jw * 0.8), (hx_ + 3.4, hy_ + 3.0 + jw * 0.5)])
        cv.fill(mouth, (0.38, 0.07, 0.12), z=z + 1.9)
        for tx in (5.2, 7.0):
            cv.fill(cv.blob([(hx_ + tx - 0.4, hy_ + 1.75), (hx_ + tx + 0.4, hy_ + 1.75), (hx_ + tx, hy_ + 2.7, 0.0)]), (0.96, 0.94, 0.86), z=z + 1.95)
    cv.shape(lower, FUR_B, z=z + 1.8, sd=1.0)
    eye_c = (hx_ + 2.7, hy_ - 1.1)
    det = [
        ('deep', cv.wedge([(hx_ + 0.6, hy_ - 1.9), (hx_ + 2.6, hy_ - 2.2), (hx_ + 4.6, hy_ - 1.5)], 0.9, -1.0)),
        ('ink', [(hx_ + 0.4, hy_ - 2.3), (hx_ + 2.6, hy_ - 2.4), (hx_ + 4.7, hy_ - 1.4)], 2.6, (0.15, 0.7)),
        ('ink', [(hx_ + 5.0, hy_ - 1.3), (hx_ + 7.0, hy_ - 1.0), (hx_ + 8.8, hy_ - 0.7)], 1.2, (0.3, 0.6)),
        ('ink', [(hx_ + 9.4, hy_ + 1.9), (hx_ + 6.6, hy_ + 2.4), (hx_ + 4.0, hy_ + 2.7), (hx_ + 3.1, hy_ + 2.2)], 1.8, (0.1, 0.5)),
        ('stroke', [(hx_ + 3.4, hy_ + 0.0), (hx_ + 2.2, hy_ + 0.6), (hx_ + 0.8, hy_ + 1.6)], 2.6, PAINT, (0.1, 0.8)),
        ('stroke', [(hx_ + 4.2, hy_ + 0.5), (hx_ + 3.0, hy_ + 1.1), (hx_ + 1.8, hy_ + 2.0)], 2.0, PAINT, (0.1, 0.8)),
        ('ink', [(hx_ - 1.8, hy_ - 1.8), (hx_ - 0.7, hy_ - 0.3), (hx_ - 1.3, hy_ + 1.4)], 1.3, (0.4, 0.4)),
        ('ink', [(hx_ - 2.6, hy_ + 0.6), (hx_ - 1.3, hy_ + 2.1)], 1.2, (0.4, 0.4)),
    ]
    cv.shape(head_p, FUR, z=z + 1.6, sd=2.4, hi=0.35, details=det, cast=1.0)
    # burun ucu
    cv.shape(cv.blob([(hx_ + 8.8, hy_ - 1.1), (hx_ + 10.1, hy_ - 0.7), (hx_ + 10.4, hy_ + 0.5, 0.4), (hx_ + 9.2, hy_ + 0.9)]), NOSE, z=z + 2.2, sd=0.5, hi=0.25, ol=0.7)
    # göz: burna doğru eğik badem, camgöbeği ve ışıyan
    eye = cv.blob([(eye_c[0] - 1.2, eye_c[1] - 0.25, 0.0), (eye_c[0] + 0.2, eye_c[1] - 0.45), (eye_c[0] + 1.3, eye_c[1] + 0.25, 0.0),
                   (eye_c[0] + 0.0, eye_c[1] + 0.45)])
    cv.fill(eye, EYE, z=z + 2.3, glow=EYE_GLOW)
    cv.fill(cv.ellipse((eye_c[0] + 0.45, eye_c[1] + 0.05), 0.3, 0.38), (0.05, 0.25, 0.32), z=z + 2.35)


def draw(cv, p, front_arm=True, back_arm=True):
    bob, lean = p['bob'], p['lean']
    sk, pk, bp = p.get('sk', 0.0), p.get('pk', 0.0), p.get('bp', 0.0)
    br = p.get('br', 0.0)
    tw = p.get('tw', 0.0)
    hip = (p.get('hx', 0.0), HIP_Y + bob * 1.1)
    tl = TORSO + br * 0.3
    neck = (hip[0] + math.sin(lean) * tl, hip[1] - math.cos(lean) * tl)
    sx = p.get('sx', 0.0)
    sh_f = (neck[0] + 1.4 + sx + tw * 0.7, neck[1] + 3.2)
    sh_b = (neck[0] - 2.8 - sx * 0.5 - tw * 0.7, neck[1] + 3.0)
    head = (neck[0] + 1.6 + math.sin(lean) * 1.6 + p.get('hdx', 0.0), neck[1] - 4.6 + p.get('hdy', 0.0))
    out = {'sh_f': sh_f}
    nx_, ny_ = neck
    ax = (math.sin(lean), -math.cos(lean))
    pe = (math.cos(lean), math.sin(lean))
    T = _T(hip, ax, pe)

    # ---- atkı kuyrukları (en arkada)
    _scarf_tails(cv, (nx_ - 1.6, ny_ + 1.2), pk, bp, -14)

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
    torso = cv.blob([T(-1.0, -5.6), T(5.0, -5.4), T(10.5, -6.5 - br * 0.1), T(15.0, -6.0), T(17.8, -3.0), T(18.6, 0.6),
                     T(16.8, 4.4), T(12.4, 6.6 + br * 0.25), T(7.6, 6.0), T(3.0, 5.4), T(-1.0, 5.6)])
    tdet = cv.fold([T(13.0, -4.8), T(9.0, -3.4), T(5.0, -3.8)], 0.7, 1.4, 1)
    for v in (-4.0, -2.0):   # kemer üstünde kumaş bolluğu
        tdet += cv.fold([T(4.4, v), T(3.0, v + 0.8), T(2.6, v + 1.6)], 0.5, 1.2, 1)
    cv.shape(torso, KAFTAN, z=0, sd=4.6, hatch=0.45, deep=0.3, details=tdet)
    # lamel yelek (göğüs + karın; arka kenarı deri şeritli)
    vest = cv.blob([T(1.8, -2.6), T(8.6, -3.0), T(14.6, -2.2), T(16.2, 1.0), T(15.4, 4.6), T(11.8, 6.5 + br * 0.2),
                    T(7.2, 5.9), T(2.0, 5.4)])
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

    # ---- ön etek (diz boyu; önü açık kaftan dizleri izler: adım açılınca etek uyluğun üstünden gerilir)
    kf, _ = fk_leg((hip[0] + 1, hip[1]), p['lf'][0], p['lf'][1], L_THIGH, L_SHIN)
    kb, _ = fk_leg(hip, p['lb'][0], p['lb'][1], L_THIGH, L_SHIN)
    F = (max(hip[0] + 5.6, kf[0] + 2.6) + sk * 1.6, min(bot, kf[1] + 1.6))
    B = (min(hip[0] - 6.4, kb[0] - 2.4) + sk * 2.8, min(bot, kb[1] + 1.8) - 0.6)
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
    cv.shape(skirt, KAFTAN, z=2.0, sd=3.2, shadows=sh_paths, details=sdet, hatch=0.45, deep=0.3)
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
    k, f = _leg(cv, (hip[0] + 1, hip[1]), p['lf'], 1.0, True, kz=2.6)
    out['foot_f'] = f

    # ---- ak post yaka (omuzları saran)
    collar = cv.blob(fur_ring((nx_ - 0.3, ny_ + 1.2), 6.2, 3.4, lean * 0.6, -math.pi * 1.05, math.pi * 0.08, 7, 0.38, 0.32, 1.0, bp * 3.0)
                     + [(nx_ + 3.0, ny_ - 0.6), (nx_ - 1.0, ny_ - 1.6)])
    cv.shape(collar, FUR, z=9.0, sd=1.8, hi=0.25, cast=0.8,
             details=[('ink', [(nx_ - 3.6, ny_ + 0.8), (nx_ - 2.4, ny_ + 2.6)], 1.1), ('ink', [(nx_ - 0.4, ny_ + 1.6), (nx_ + 0.4, ny_ + 3.4)], 1.1)])

    # ---- boyun + baş
    neckp = cv.capsule((nx_ - 0.6, ny_ + 0.4), (head[0] - 1.0, head[1] + 1.4), 3.0, 2.8)
    cv.shape(neckp, FUR, z=9.6, sd=1.6, ol=1.0)
    hs = HEAD_K
    cv.push(lambda q, c0=head: (c0[0] + (q[0] - c0[0]) * hs, c0[1] + (q[1] - c0[1]) * hs))
    _head(cv, head, neck, p, 10.0)
    cv.pop()
    out['head'] = head

    # ---- atkı düğümü
    knot = ik.union(cv.capsule((nx_ - 1.6, ny_ + 0.4), (nx_ + 2.6, ny_ + 1.9), 1.8, 1.8), cv.ellipse((nx_ + 2.2, ny_ + 1.7), 2.0, 1.7))
    cv.shape(knot, SCARF, z=14.6, sd=1.1, hi=0.3, cast=0.6,
             details=[('ink', [(nx_ - 0.6, ny_ + 0.2), (nx_ + 1.0, ny_ + 1.6)], 1.2)])
    cv.shape(cv.capsule((nx_ + 2.5, ny_ + 2.4), (nx_ + 3.3 + sk * 0.4, ny_ + 5.8), 1.1, 0.75), SCARF, z=14.8, sd=0.6)

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


JUMP = keyed((0.0, P(bob=-1.0, lean=0.4, lf=(1.35, 2.0), lb=(-0.75, 0.45), af=(-0.6, 1.5), ab=(-1.1, 0.5), sk=-1.0, pk=-1.3, hdy=-0.2)),
             (1.0, P(bob=-2.0, lean=0.46, lf=(1.6, 2.4), lb=(-0.45, 1.2), af=(-0.8, 1.8), ab=(-1.4, 0.7), sk=-1.2, pk=-1.5, hdy=-0.4)))
FALL = keyed((0.0, P(bob=-1.0, lean=0.12, lf=(0.85, 1.0), lb=(-0.1, 1.4), af=(1.4, 1.0), ab=(-1.3, 0.5), sk=0.7, pk=0.9)),
             (1.0, P(bob=0.0, lean=0.0, lf=(0.5, 0.4), lb=(-0.4, 0.9), af=(1.8, 0.7), ab=(-1.7, 0.4), sk=1.1, pk=1.25, hdy=0.3)))
LAND = keyed((0.0, P(bob=3.0, lean=0.42, lf=(1.05, 1.9), lb=(-0.75, 1.3), af=(0.7, 1.0), ab=(-0.7, 0.9), sk=0.5, pk=0.6, hdy=0.6)),
             (1.0, P(bob=1.4, lean=0.24, lf=(0.65, 0.95), lb=(-0.55, 0.6), af=(0.3, 0.9), ab=(-0.4, 0.7), sk=0.2, pk=0.3)))
HURT = keyed((0.0, P(lean=-0.5, af=(-1.3, 1.0), ab=(-1.6, 0.6), lf=(0.6, 0.5), lb=(-0.65, 0.5), sk=1.0, pk=1.2, jaw=0.9, hdy=-0.6, hdx=-0.8)),
             (1.0, P(lean=-0.25, af=(-0.7, 0.8), ab=(-0.9, 0.6), lf=(0.5, 0.6), lb=(-0.5, 0.5), sk=0.6, pk=0.8, jaw=0.3)))


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
        piv, off = (0.0, -23.0), (0.0, -19.0)
        ca, sa = math.cos(ang), math.sin(ang)

        def rot(q):
            x, y = q[0] - piv[0], q[1] - piv[1]
            return (off[0] + x * ca - y * sa, off[1] + x * sa + y * ca)
        cv.push(rot)
        info = draw(cv, p, True)
        cv.pop()
    else:
        info = draw(cv, p, arm, arm)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
