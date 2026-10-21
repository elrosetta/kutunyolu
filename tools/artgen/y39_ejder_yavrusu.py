"""v39: Ak Ejder Yavrusu (kimlik ejder_yavrusu) — Kaf Dağı'nın genç ayaz ejderi (yapay zekâ: soluyucu / breather; yerde,
dört ayaklı, küçük kanatlı).

İnci beyazı ve buz mavisi pullar, koyu kurşuni karın plakaları; uzun S kıvrımlı boyun, geriye yatık kristal boynuzlu baş,
ışıyan camgöbeği gözler ve ayazla ışıyan gırtlak (ışıma sayfası; soluk alırken alevlenir), yırtık kenarlı küçük zar
kanatlar (ucan_v29.bat_wing), sırt boyunca buz kristali dikenler, ucunda kristal bıçak yüzgeç taşıyan uzun kuyruk.
Soğuk ortamda okunsun diye kalın mürekkep kontur, kurşuni gölge bantları ve hafif sıcak kenar ışığı (rim) kullanılır.

Satırlar (hücre 96 x 64 dünya, ayak (44, 60), doku 4):
  idle 8 (nefes, kuyruk salınımı, kanat seğirmesi), move 8 (dört ayak sinsi yürüyüş, vx 70), hurt 3,
  atk_breath 10 (mk: şahlanır, boyun geriye kıvrılır, göğüs / gırtlak şişip ışır; temas = baş öne atılır, çene ardına
               kadar açık, ağzın önünde ayaz soluğu konisi + buz kristalleri; toparlanma),
  atk_tail 8 (mk: kalça döner, kuyruk sırtın üstüne kurulur; temas = kuyruk baştan öne süpürülür, buz ışıltısı yayı),
  atk_hop 8 (mk: çömelir, kanatlar yukarı; temas = kanat destekli havada atılış, pençeler önde; toparlanma = iniş
             çömelmesi + kar tozu).
Çapa her karede: 'mouth' (ağız / soluk çıkışı).
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import lerp2, chain
import yaratik_govde as yg
import yaratik_ink_kit as yk
import ucan_v29 as u29
from ucan_v29 import pose_at

TEX = 4.0
CELL = (384, 256)       # dünya 96 x 64
FEET = (176, 240)       # dünya (44, 60)

PEARL = Ink('#e8eef4', '#7084ae', '#ffffff', '#38426c', name='inci pul')
PEARL_B = Ink('#aeb8cc', '#525e86', '#ccd4e2', '#2a3052', name='uzak pul')
ICE = Ink('#9ad2ee', '#4474a8', '#e0f6ff', '#223a68', name='buz mavisi pul')
SLATE = Ink('#56647e', '#2a3146', '#8290ac', '#161b28', name='kurşuni karın')
CRYST = Ink('#a8f0ff', '#3c8cc0', '#f0ffff', '#1e4a78', name='buz kristali')
MEM = Ink('#7ea6cc', '#3e5c8e', '#bcdcf2', '#22345e', name='kanat zarı')
CLAW = Ink('#2c3244', '#12141e', '#6a7490', name='pençe')
FROST = (0.55, 0.95, 1.0)
FROST_HOT = (0.9, 1.0, 1.0)
FROST_GLOW = (0.15, 0.7, 1.0)
EYE = (0.7, 1.0, 1.0)
EYE_GLOW = (0.1, 0.8, 1.0)

C0 = (-1.0, -16.0)        # gövde merkezi (pitch pivotu)
HIP = (-11.0, -15.0)
SHO = (8.0, -15.5)


def _B(p, q):
    """Gövde yereli -> dünya: pitch (C0 çevresinde) + öteleme."""
    c, s = math.cos(p['pitch']), math.sin(p['pitch'])
    x, y = q[0] - C0[0], q[1] - C0[1]
    return (C0[0] + p['x'] + x * c - y * s, C0[1] + p['y'] + x * s + y * c)


def _crystal(cv, b, a, ln, w, z, mat=CRYST, glow=(0.03, 0.22, 0.35)):
    tip = (b[0] + math.cos(a) * ln, b[1] + math.sin(a) * ln)
    nx, ny = -math.sin(a) * w, math.cos(a) * w
    m = lerp2(b, tip, 0.55)
    cv.shape(cv.blob([(b[0] + nx, b[1] + ny, 0.0), (m[0] + nx * 0.8, m[1] + ny * 0.8, 0.0), (tip[0], tip[1], 0.0), (m[0] - nx * 0.7, m[1] - ny * 0.7, 0.0),
                      (b[0] - nx, b[1] - ny, 0.0)]), mat, z=z, sd=0.5, hi=0.35, ol=0.75, glow=glow,
             details=[('stroke', [lerp2(b, tip, 0.2), lerp2(b, tip, 0.75)], 0.8, (1.0, 1.0, 1.0), (0.2, 0.6))])
    return tip


# ------------------------------------------------------------------ bacaklar
def _paw(cv, f, m, cm, z, toe=0.0, spread=0.0):
    ca, sa = math.cos(-toe), math.sin(-toe)

    def R(x, y, *r):
        dx, dy = x - f[0], y - f[1]
        return (f[0] + dx * ca - dy * sa, f[1] + dx * sa + dy * ca) + r
    cv.shape(cv.blob([R(f[0] - 2.0, f[1] - 1.8), R(f[0] + 1.6, f[1] - 2.0), R(f[0] + 3.0, f[1] - 0.6), R(f[0] + 2.6, f[1] + 0.3, 0.0), R(f[0] - 2.0, f[1] + 0.3, 0.0)]),
             m, z=z, sd=0.8, hi=0.25, ol=0.85)
    for i in range(3):
        x, y = f[0] + 2.2 + i * 0.25, f[1] - 1.5 + i * 0.75 - spread * (1 - i) * 0.6
        cv.shape(cv.blob([R(x - 0.5, y - 0.4), R(x + 1.7 + spread * 0.5, y + 0.5 + spread * 0.3, 0.0), R(x - 0.4, y + 0.5)]), cm, z=z + 0.2 + i * 0.01, sd=0.3, ol=0.6)


def _legs(cv, p, near):
    m = PEARL if near else PEARL_B
    cm = CLAW if near else CLAW.darker(0.8)
    z = 8.0 if near else -10.0
    dx = 0.0 if near else 2.2
    # arka bacak: kalın uyluk, ayak bileği yerden kalkık (parmak üstü)
    hip = _B(p, (HIP[0] + dx, HIP[1] + 1.0))
    hf = p['hf'] if near else p['hb']
    f = (hf[0] + dx * 0.5, -hf[1])
    ank = (f[0] - 2.6, f[1] - 3.6 + hf[1] * 0.1)
    kn, ank = yg.ik2(hip, ank, 7.8, 6.4, -1)
    leg = ik.union(cv.limb([hip, lerp2(hip, kn, 0.45), kn], [5.4, 4.8, 2.6]), cv.limb([kn, ank, f], [2.6, 1.8, 1.6]))
    det = []
    if near:
        det = [('ink', [lerp2(hip, kn, 0.35), lerp2(hip, kn, 0.7), lerp2(kn, ank, 0.2)], 1.0, (0.3, 0.5)),
               ('stroke', [lerp2(kn, ank, 0.2), lerp2(kn, ank, 0.9)], 3.0, ICE.base, (0.2, 0.4))]
    cv.shape(leg, m, z=z, sd=2.0, hi=0.35 if near else 0.0, details=det, bounce=0.25)
    _paw(cv, f, m, cm, z + 0.3, hf[2], p['claw'])
    # ön bacak: dirsek geride
    sh = _B(p, (SHO[0] + dx, SHO[1] + 0.5))
    ff = p['ff'] if near else p['fb']
    f2 = (ff[0] + dx * 0.5, -ff[1])
    wr = (f2[0] - 0.6, f2[1] - 2.4)
    el, wr = yg.ik2(sh, wr, 6.8, 6.6, 1)
    fore = ik.union(cv.limb([sh, lerp2(sh, el, 0.4), el], [4.2, 3.6, 2.2]), cv.limb([el, wr, f2], [2.2, 1.6, 1.5]))
    det = [('ink', [lerp2(sh, el, 0.4), lerp2(el, wr, 0.3)], 0.9, (0.3, 0.5))] if near else []
    cv.shape(fore, m, z=z + 0.6, sd=1.8, hi=0.35 if near else 0.0, details=det, bounce=0.25)
    _paw(cv, f2, m, cm, z + 0.9, ff[2], p['claw'])
    if near:   # dirsek dikeni
        _crystal(cv, el, math.atan2(el[1] - sh[1], el[0] - sh[0]) + 0.9, 2.6, 0.7, z + 0.7)


# ------------------------------------------------------------------ kuyruk
def _tail_pts(p):
    root = _B(p, (-14.0, -17.0))
    a0 = p['ta'] - p['pitch'] * 0.5
    return chain(root, 11, 2.3, a0, p['tb'], p['ph'] - 0.6, p['tw'])


def _tail(cv, p):
    pts = _tail_pts(p)
    W = [cv.W(q) for q in pts]
    path = ik.taper_path(W, cv.u(6.4), prof=lambda u: max(0.12, (1.0 - min(1.0, u)) ** 0.75))
    det = []
    # karın şeridi (alt yan) + segment çizgileri
    for i in range(1, len(pts) - 2):
        a, b = pts[i], pts[i + 1]
        d = u29.norm2((b[0] - a[0], b[1] - a[1]))
        n = (-d[1], d[0])          # sağ el normali: tail geriye bakarken alt yan
        r = 3.0 * (1.0 - i / len(pts)) ** 0.75
        det.append(('stroke', [u29.add(a, n, r * 0.8), u29.add(b, n, r * 0.8)], 3.2 * (1.0 - i / len(pts)) + 1.0, SLATE.base, (0.0, 0.0)))
        det.append(('ink', [u29.add(a, n, r * 0.3), u29.add(a, n, r * 1.1)], 0.7, (0.2, 0.2)))
    tz = 18.0 * p['tz'] - 6.0
    cv.shape(path, PEARL, z=tz, sd=1.8, hi=0.35, details=det, bounce=0.25)
    # sırt kristalleri (kök tarafında)
    for i in range(1, 7):
        a, b = pts[i], pts[i + 1]
        d = u29.norm2((b[0] - a[0], b[1] - a[1]))
        n = (d[1], -d[0])
        r = 3.0 * (1.0 - i / len(pts)) ** 0.75
        base = u29.add(lerp2(a, b, 0.5), n, r * 0.7)
        _crystal(cv, base, math.atan2(n[1], n[0]) - 0.5 * (1 if d[0] < 0 else -1), 2.6 - i * 0.25, 0.7, tz - 0.5 + i * 0.01)
    # uçta kristal bıçak yüzgeç
    e, e1 = pts[-1], pts[-3]
    d = u29.norm2((e[0] - e1[0], e[1] - e1[1]))
    n = (-d[1], d[0])
    tip = u29.add(e, d, 5.5)
    blade = cv.blob([u29.add(e1, n, 0.6), u29.add(lerp2(e, tip, 0.1), n, 3.0), (tip[0], tip[1], 0.0), u29.add(lerp2(e, tip, 0.35), n, -2.4),
                     (u29.add(e, d, -0.5)[0] + n[0] * -1.8, u29.add(e, d, -0.5)[1] + n[1] * -1.8, 0.0), u29.add(e1, n, -0.6)])
    cv.shape(blade, CRYST, z=tz + 0.5, sd=0.9, hi=0.5, ol=0.9, glow=(0.05, 0.35, 0.5),
             details=[('stroke', [lerp2(e1, e, 0.6), lerp2(e, tip, 0.8)], 1.0, (1, 1, 1), (0.2, 0.6)), ('ink', [e, lerp2(e, tip, 0.6)], 0.6, (0.2, 0.6))])
    yk.glow_soft(cv, lerp2(e, tip, 0.4), 3.0 + 2.0 * p['spark'], FROST_GLOW, z=tz + 0.6, alpha=0.35 + 0.4 * p['spark'])
    return pts, tip


# ------------------------------------------------------------------ gövde, boyun, baş
def _body(cv, p):
    br = p['br']
    L = [(-15.0, -18.5), (-12.0, -22.5), (-5.0, -24.5), (2.0, -24.0), (8.0, -22.5), (12.0, -19.0), (12.5 + br * 0.3, -14.0),
         (9.0, -9.5 - br * 0.3), (2.0, -8.5 - br * 0.2), (-6.0, -9.0), (-12.0, -10.5), (-16.0, -14.0)]
    body = cv.blob([_B(p, q) for q in L])
    bp = [_B(p, q) for q in ((12.0, -14.5), (8.0, -10.0), (2.0, -9.0), (-6.0, -9.5), (-12.5, -11.0))]
    det = [('stroke', bp, 9.0 + br * 2.0, SLATE.base, (0.1, 0.3))]
    for i in range(6):   # karın plakası ayrımları
        q = lerp2((11.0, -13.5), (-11.0, -10.5), i / 5)
        det.append(('ink', [_B(p, (q[0] + 0.6, q[1] - 2.2)), _B(p, (q[0] - 0.2, q[1] + 1.5))], 0.9, (0.1, 0.1)))
    # sırtta buz mavisi şerit + pul yayları
    det.append(('stroke', [_B(p, q) for q in ((-13.0, -20.0), (-5.0, -22.5), (3.0, -22.0), (9.0, -20.0))], 8.0, ICE.base, (0.2, 0.3)))
    for r in range(2):
        for i in range(5):
            x = -10.0 + i * 4.5 + r * 2.2
            y = -19.0 + r * 3.0 - math.sin(i / 4 * math.pi) * 1.4
            det.append(('ink', [_B(p, (x - 1.4, y)), _B(p, (x, y + 1.1)), _B(p, (x + 1.4, y))], 0.8, (0.2, 0.2)))
    det += cv.fold([_B(p, (-9.0, -19.0)), _B(p, (-10.5, -14.0)), _B(p, (-9.0, -10.5))], 0.8, 1.2, 1)
    cv.shape(body, PEARL, z=0, sd=3.2, hi=0.55, details=det, bounce=0.35)
    # sırt kristalleri
    for i, (x, y, ln) in enumerate(((-13.0, -21.5, 2.6), (-9.0, -23.6, 3.6), (-4.5, -24.6, 4.4), (0.0, -24.6, 4.8), (4.5, -23.8, 4.2), (8.5, -22.0, 3.4))):
        b = _B(p, (x, y + 0.8))
        _crystal(cv, b, -math.pi / 2 - 0.55 + p['pitch'] - p['hack'] * 0.2, ln * (1.0 + 0.25 * p['hack']), 1.0, 1.5 + i * 0.01)
    # ayaz gırtlak / göğüs ışıması
    fr = p['frost']
    if fr > 0.05:
        c = _B(p, (10.0, -15.0))
        yk.glow_soft(cv, c, 4.0 + 4.0 * fr, FROST_GLOW, z=1.2, blur=0.6, alpha=0.6 * fr)
        for k in range(3):
            q0 = _B(p, (8.0 + k * 1.2, -17.0 + k * 1.6))
            q1 = _B(p, (11.5 + k * 0.6, -14.5 + k * 1.8))
            cv.stroke([q0, q1], 1.2 + fr, z=1.3, col=FROST_HOT, taper=(0.3, 0.6), glow=FROST_GLOW, alpha=min(1.0, fr * 1.3))


def _bez(a, b, c, d, n=9):
    out = []
    for i in range(n):
        t = i / (n - 1)
        u = 1 - t
        out.append((u ** 3 * a[0] + 3 * u * u * t * b[0] + 3 * u * t * t * c[0] + t ** 3 * d[0],
                    u ** 3 * a[1] + 3 * u * u * t * b[1] + 3 * u * t * t * c[1] + t ** 3 * d[1]))
    return out


def _neck_head(cv, p):
    """S kıvrımlı boyun (Bezier) + baş. Döner: ağız (dünya), baş yönü."""
    N0 = _B(p, (8.5, -19.0))
    hx, hy = p['hd']
    H = (N0[0] + 10.5 + hx, N0[1] - 14.0 + hy)
    ha = p['ha']
    d_h = (math.cos(ha), math.sin(ha))
    c1 = u29.add(N0, u29.rot2((0.3, -1.0), p['pitch']), 6.0 + p['coil'] * 2.0)
    c2 = u29.add(H, d_h, -5.0 - p['coil'] * 3.0)
    c2 = (c2[0] - p['coil'] * 4.0, c2[1] + 2.0 + p['coil'] * 2.0)
    pts = _bez(N0, c1, c2, H)
    W = [cv.W(q) for q in pts]
    neck = ik.taper_path(W, cv.u(7.0 + p['br'] * 0.6), prof=lambda u: 1.0 - 0.42 * u * (2.0 - u))
    det = []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        d = u29.norm2((b[0] - a[0], b[1] - a[1]))
        n = (d[1], -d[0])   # ön / alt yan (boyun yukarı giderken sağ)
        r = 4.0 * (1.0 - 0.45 * i / (len(pts) - 1))
        det.append(('stroke', [u29.add(a, n, -r * 0.75), u29.add(b, n, -r * 0.75)], 7.0 * (1 - 0.4 * i / len(pts)), SLATE.base, (0.0, 0.0)))
        det.append(('ink', [u29.add(a, n, -r * 0.4), u29.add(a, n, -r * 1.1)], 0.8, (0.2, 0.2)))
    det.append(('stroke', [u29.add(q, (0.0, 0.0), 0.0) for q in pts[1:-1]], 3.0, ICE.base, (0.3, 0.3)))
    cv.shape(neck, PEARL, z=10, sd=2.2, hi=0.45, details=det, cast=0.7)
    fr = p['frost']
    if fr > 0.05:   # gırtlak boyunca ışık
        for i in range(2, len(pts) - 1, 2):
            a, b = pts[i], pts[i + 1]
            d = u29.norm2((b[0] - a[0], b[1] - a[1]))
            n = (d[1], -d[0])
            q = u29.add(a, n, -2.2)
            yk.glow_soft(cv, q, 2.6 + 1.6 * fr, FROST_GLOW, z=10.5, alpha=0.5 * fr)
            cv.stroke([u29.add(q, d, -1.0), u29.add(q, d, 1.0)], 1.4, z=10.6, col=FROST_HOT, taper=(0.3, 0.3), glow=FROST_GLOW, alpha=min(1.0, fr * 1.4))
    # boyun kristalleri
    for i in range(1, len(pts) - 2, 2):
        a, b = pts[i], pts[i + 1]
        d = u29.norm2((b[0] - a[0], b[1] - a[1]))
        n = (-d[1], d[0])
        base = u29.add(a, n, -3.0 * (1.0 - 0.4 * i / len(pts)))
        n2 = (d[1], -d[0])
        _crystal(cv, base, math.atan2(-n2[1], -n2[0]) - 0.6, 3.0 - i * 0.18, 0.8, 9.6 + i * 0.01)
    # ---- baş (yerel çerçeve: H çevresinde ha kadar döner)
    u29.body_xf(cv, H, ha, 1.0, 1.0, (0.0, 0.0))
    hx0, hy0 = H
    P = lambda x, y, *r: (hx0 + x, hy0 + y) + r
    # boynuzlar: geriye yatık kristal
    for (bx, a, ln, w, zz, m) in ((-0.5, -2.85, 8.5, 1.3, 13.0, CRYST.darker(0.8)), (1.2, -2.7, 10.0, 1.5, 16.5, CRYST), (2.6, -2.35, 4.0, 0.8, 16.6, CRYST)):
        b = P(bx, -2.4)
        tip = (b[0] + math.cos(a) * ln, b[1] + math.sin(a) * ln)
        mid = lerp2(b, tip, 0.5)
        mid = (mid[0], mid[1] - ln * 0.1)
        nx, ny = -math.sin(a) * w, math.cos(a) * w
        cv.shape(cv.blob([(b[0] + nx, b[1] + ny), (mid[0] + nx * 0.6, mid[1] + ny * 0.6), (tip[0], tip[1], 0.0), (mid[0] - nx * 0.6, mid[1] - ny * 0.6), (b[0] - nx, b[1] - ny)]),
                 m, z=zz, sd=0.6, hi=0.4, ol=0.85, glow=(0.04, 0.3, 0.45),
                 details=[('stroke', [lerp2(b, tip, 0.15), lerp2(mid, tip, 0.6)], 0.9, (1, 1, 1), (0.2, 0.6))])
    jaw = p['jaw']
    hinge = P(0.6, 1.4)
    jw = [u29.add(hinge, u29.rot2((q[0] - hinge[0], q[1] - hinge[1]), jaw * 0.75)) for q in
          (P(0.0, 1.0), P(5.0, 1.6), P(8.6, 1.8), P(8.0, 2.6), P(4.0, 3.4), P(0.0, 3.2))]
    if jaw > 0.1:   # ağız içi + dişler + soluk ışığı
        cv.fill(cv.blob([P(0.4, 1.2), P(9.0, 0.9), jw[2], jw[4], jw[5]]), (0.2, 0.3, 0.5), z=14.2, glow=FROST_GLOW if p['breath'] > 0.05 or p['frost'] > 0.4 else None)
        for i in range(3):
            x = 3.0 + i * 2.0
            cv.fill(cv.blob([P(x - 0.45, 1.0), P(x + 0.45, 1.0), P(x + 0.1, 2.2, 0.0)]), (0.95, 0.98, 1.0), z=14.4)
            q = lerp2(jw[1], jw[2], 0.1 + i * 0.3) if i else lerp2(jw[0], jw[1], 0.7)
            cv.fill(cv.blob([(q[0] - 0.4, q[1] + 0.1), (q[0] + 0.4, q[1] + 0.1), (q[0], q[1] - 1.1, 0.0)]), (0.95, 0.98, 1.0), z=14.4)
    cv.shape(cv.blob([jw[0], jw[1], (jw[2][0], jw[2][1], 0.0), jw[3], jw[4], jw[5]]), PEARL_B, z=14.5, sd=0.8, hi=0.2, ol=0.9,
             details=[('stroke', [lerp2(jw[5], jw[4], 0.2), lerp2(jw[4], jw[3], 0.8)], 2.6, SLATE.base, (0.2, 0.4))])
    skull = cv.blob([P(-2.4, -0.6), P(-1.0, -3.0), P(2.0, -3.6), P(5.0, -2.6), P(8.6, -0.8), P(10.0, 0.6, 0.0), P(8.4, 1.4), P(3.0, 1.6), P(-1.0, 2.6), P(-2.6, 1.4)])
    sdet = [('stroke', [P(-1.0, -2.6), P(3.0, -3.0), P(7.5, -1.2)], 3.0, ICE.base, (0.3, 0.6)),
            ('ink', [P(1.0, 1.2), P(5.0, 1.0), P(9.0, 0.7)], 0.9, (0.2, 0.4)),
            ('col', cv.ellipse(P(8.6, -0.2), 0.55, 0.35, 0.3), INK)]
    cv.shape(skull, PEARL, z=15, sd=1.6, hi=0.5, details=sdet)
    # yanak dikenleri
    for (x, y, a, ln) in ((-1.8, 1.0, 2.6, 3.2), (-0.8, 2.4, 2.3, 2.6)):
        _crystal(cv, P(x, y), a, ln, 0.6, 14.8, mat=PEARL_B, glow=None)
    # göz: kaş altında camgöbeği ışık
    ey = p['eye']
    sq = p['squint']
    ec = P(3.4, -1.4)
    cv.fill(cv.blob([P(1.8, -1.0), P(3.4, -2.2 + sq * 0.8), P(5.0, -1.6, 0.0), P(3.4, -0.5)]), INK, z=17)
    yk.eye_glow(cv, (ec[0] + 0.1, ec[1] + 0.1), 1.0, 0.55 * (1 - 0.7 * sq), -0.15, EYE if ey < 0.5 else FROST_HOT, EYE_GLOW, 17.5, halo=2.2 + 1.5 * ey,
                halo_a=0.4 + 0.4 * ey)
    cv.stroke([P(1.4, -2.0), P(3.6, -2.7 + sq * 0.6), P(5.6, -1.8)], 1.3, z=18, col=INK, taper=(0.2, 0.8))
    mouth = u29.to_world(cv, P(10.0, 1.4 + jaw * 0.6))
    cv.pop()
    return mouth, (math.cos(ha), math.sin(ha))


def _wing(cv, p, near):
    S = _B(p, (2.0, -22.5) if near else (4.0, -24.0))
    s = p['ws'] if near else max(-1.0, min(1.0, p['ws'] * 0.9 + 0.05))
    mats = (MEM, PEARL, (0.25, 0.4, 0.62)) if near else (MEM.darker(0.62), PEARL_B, (0.2, 0.3, 0.5))
    fl = _B(p, (-6.0, -20.0) if near else (-4.0, -21.0))
    w = u29.bat_wing(cv, S, s, p['wf'], 21.0 if near else 18.0, p['wl'], mats, z=6.0 if near else -20.0, near=near, sweep=0.45, flank=fl, ph=p['ph'] + (0 if near else 0.7))
    # yırtık zar: parmak aralarında küçük çentikler (mürekkep)
    tips = w['tips']
    for j in range(1, 3):
        q = lerp2(lerp2(tips[j - 1], tips[j], 0.5), w['wrist'], 0.32)
        cv.fill(cv.blob([u29.add(q, (0.7, 0.0)), u29.add(q, (-0.4, -0.7)), u29.add(lerp2(q, w['wrist'], 0.25), (0, 0), 0.0)]), (0.1, 0.12, 0.2), z=(6.05 if near else -19.95))
    return w


# ------------------------------------------------------------------ efektler
def _breath(cv, M, d, k, ph):
    """Ayaz soluğu konisi: ağızdan öne genişleyen yarı saydam katmanlar + buz kristalleri + sarmal mürekkep çizgileri."""
    if k <= 0.02:
        return
    L = 22.0 * min(1.0, k)
    n = (-d[1], d[0])
    rng = np.random.default_rng(5 + int(ph * 3) % 7)
    for (ang, a, col, z) in ((0.44, 0.34, (0.6, 0.85, 1.0), 30.0), (0.3, 0.52, (0.8, 0.96, 1.0), 30.5), (0.15, 0.78, (0.96, 1.0, 1.0), 31.0)):
        e = u29.add(M, d, L)
        pts = [M, u29.add(u29.add(M, d, L * 0.5), n, L * 0.5 * math.tan(ang)), u29.add(u29.add(e, n, L * math.tan(ang)), d, 0.0),
               u29.add(e, d, L * 0.08), u29.add(e, n, -L * math.tan(ang)), u29.add(u29.add(M, d, L * 0.5), n, -L * 0.5 * math.tan(ang))]
        path = cv.blob(pts)
        yk.wash(cv, path, col, a * min(1.0, k * 1.5), z=z, blur=0.8, glow=FROST_GLOW, glow_a=0.35 * a)
    # sarmal çizgiler
    for j in range(3):
        o = (j - 1) * 0.5
        pts = []
        for i in range(7):
            u = i / 6
            r = L * u * math.tan(0.3) * (o + 0.35 * math.sin(ph * 2 + u * 7 + j))
            pts.append(u29.add(u29.add(M, d, L * u), n, r))
        cv.stroke(pts, 1.2, z=31.5, col=(0.2, 0.38, 0.6), taper=(0.4, 0.4), alpha=0.75)
    # buz kristalleri
    for i in range(9):
        u = rng.uniform(0.25, 1.0)
        q = u29.add(u29.add(M, d, L * u), n, L * u * math.tan(0.36) * rng.uniform(-1, 1))
        a = rng.uniform(0, math.tau)
        s = rng.uniform(0.7, 1.5)
        cv.shape(cv.blob([u29.add(q, (math.cos(a), math.sin(a)), s * 1.6), u29.add(q, (math.cos(a + 1.6), math.sin(a + 1.6)), s * 0.6),
                          u29.add(q, (math.cos(a + math.pi), math.sin(a + math.pi)), s * 1.4), u29.add(q, (math.cos(a + 4.7), math.sin(a + 4.7)), s * 0.6)]),
                 CRYST, z=32 + i * 0.01, sd=0.3, hi=0.3, ol=0.6, glow=(0.1, 0.45, 0.6))
    yk.glow_soft(cv, M, 3.5, FROST_GLOW, z=32.5, alpha=0.8)
    cv.fill(cv.ellipse(M, 1.4, 1.2), FROST_HOT, z=32.6, glow=FROST_HOT)


def _sweep_arc(cv, pts_hist, k):
    """Kuyruk süpürmesi: kuyruk ucunun izlediği yay boyunca buz ışıltısı (ince parlak şerit + kıvılcımlar)."""
    if k <= 0.02 or len(pts_hist) < 3:
        return
    cv.stroke(pts_hist, 9.0 * k + 2.0, z=-7.5, col=(0.75, 0.95, 1.0), taper=(0.9, 0.05), glow=FROST_GLOW, alpha=0.55)
    cv.stroke(pts_hist, 3.5 * k + 1.0, z=-7.4, col=(1.0, 1.0, 1.0), taper=(0.9, 0.05), glow=FROST_HOT, alpha=0.85)
    for i, q in enumerate(pts_hist[1::2]):
        yk.sparks(cv, q, 3, 0.5, 2.6, FROST_HOT, -7.3, seed=11 + i, w=1.0, glow=FROST_GLOW)


def draw(cv, p):
    fl = p['flip']
    cv.push(lambda q: (q[0] * fl, q[1]))    # yarım dönüş (kuyruk süpürmesi)
    # süpürme yayı: kuyruk ucunun önceki konumları (ta / tb geçmişinden)
    if p['sweep'] > 0.02:
        hist = []
        for j in range(7):
            q = dict(p, ta=p['ta'] - p['sweep_da'] * (1 - j / 6), tb=p['tb'] - p['sweep_db'] * (1 - j / 6))
            pts = _tail_pts(q)
            e, e1 = pts[-1], pts[-3]
            dd = u29.norm2((e[0] - e1[0], e[1] - e1[1]))
            hist.append(u29.add(e, dd, 5.0))
        _sweep_arc(cv, hist, p['sweep'])
    _wing(cv, p, False)
    _legs(cv, p, False)
    _tail(cv, p)
    _body(cv, p)
    _wing(cv, p, True)
    _legs(cv, p, True)
    mouth, d = _neck_head(cv, p)
    _breath(cv, mouth, d, p['breath'], p['ph'])
    if p['dust'] > 0.05:   # kar tozu
        SNOW = Ink('#dfeaf4', '#8a9cc0', '#ffffff', name='kar tozu')
        for i, (x, r) in enumerate(((-16.0, 2.2), (-10.0, 2.8), (6.0, 2.6), (13.0, 2.0), (-21.0, 1.6))):
            rr = r * p['dust']
            yk.puff(cv, (x + p['x'] + (i - 2) * p['dust'] * 1.5, -rr * 0.6), rr, SNOW, z=20 + i * 0.1, seed=3 + i, n=6, ol=0.35, sd=rr * 0.2)
    if p['zirh'] > 0:
        u29.armor_aura(cv, (p['x'], -16 + p['y']), 24.0, p['zirh'], z=-45, seed=3)
    cv.pop()
    return {'mouth': mouth}


# ================================================================== animasyon
REST = dict(t=0.0, ph=0.0, x=0.0, y=0.0, pitch=0.0, hd=(0.0, 0.0), ha=0.12, coil=0.0, jaw=0.05, eye=0.0, squint=0.0, frost=0.0, br=0.0,
            ws=-0.35, wf=0.75, wl=0.0, ta=math.pi * 0.97, tb=0.065, tw=0.18, spark=0.0, hack=0.0, claw=0.0,
            hf=(-11.0, 0.0, 0.0), hb=(-9.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0), fb=(11.0, 0.0, 0.0),
            breath=0.0, sweep=0.0, sweep_da=0.0, sweep_db=0.0, dust=0.0, zirh=0.0, tz=0.0, flip=1.0)


def _idle(t):
    s = math.sin(math.tau * t)
    tw = 1.0 if int(t * 8) in (3,) else 0.0
    return dict(REST, t=t, br=0.6 + 0.6 * s, y=-0.3 * s, pitch=-0.01 * s, hd=(0.4 * s, -0.6 * s), ha=0.12 + 0.04 * math.sin(math.tau * t + 0.8),
                ws=-0.35 - 0.35 * tw, wf=0.75 - 0.3 * tw, frost=0.12 + 0.08 * s, tw=0.25, eye=0.1)


def _foot_cycle(phi, home, S, duty, lift, toe_up=0.6, toe_push=0.3):
    phi %= 1.0
    if phi < duty:
        u = phi / duty
        return (home + S * (0.5 - u), 0.0, -toe_push * max(0.0, (u - 0.75) / 0.25) * 0.6)
    u = (phi - duty) / (1.0 - duty)
    e = u * u * (3 - 2 * u)
    return (home - S * 0.5 + S * e, lift * math.sin(math.pi * u) ** 0.8, toe_up * math.sin(math.pi * min(1.0, u * 1.3)))


WALK_S, WALK_DUTY = 16.0, 0.55
WALK_FPS = 19


def _walk(t):
    S, duty = WALK_S, WALK_DUTY
    p = dict(REST, t=t)
    for k, home, off in (('hf', -11.0, 0.0), ('ff', 9.5, 0.25), ('hb', -9.0, 0.5), ('fb', 11.5, 0.75)):
        p[k] = _foot_cycle(t - off, home, S, duty, 3.4 if k[0] == 'h' else 3.8)
    a = math.tau * t
    p.update(y=0.5 + 0.6 * math.cos(2 * a), pitch=0.03 * math.sin(a + 0.4), x=0.5 * math.sin(a), hd=(1.5 + 0.6 * math.sin(a), 3.0 + 0.8 * math.cos(2 * a + 0.6)),
             ha=0.2 + 0.05 * math.sin(2 * a), tw=0.35, ws=-0.25, wf=0.8, br=0.3 * math.sin(2 * a), eye=0.2)
    return p


def _K(keys):
    return lambda t: pose_at(t, keys, base=REST)


# soluk: 10 kare
_BR_TS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.48, 0.58, 0.68, 0.8, 0.9]
_BREATH = [
    (0.0, dict(y=0.0, pitch=0.0, hd=(0.0, 0.0), ha=0.12, frost=0.2), 'l'),
    (0.1, dict(y=-1.0, pitch=-0.12, hd=(-3.0, -2.0), ha=-0.05, coil=0.4, br=1.2, frost=0.5, ws=-0.6, wf=0.5, ff=(10.0, 1.0, 0.2), fb=(12.0, 0.8, 0.2), eye=0.4, jaw=0.15), 'o'),
    (0.2, dict(y=-2.0, pitch=-0.26, hd=(-6.0, -3.5), ha=-0.25, coil=0.85, br=2.0, frost=0.85, ws=-0.85, wf=0.3, ff=(9.0, 3.0, 0.4), fb=(11.0, 2.5, 0.4),
               eye=0.8, jaw=0.25, hack=0.6, tw=0.1), 'o'),
    (0.3, dict(y=-2.4, pitch=-0.32, hd=(-7.5, -4.0), ha=-0.35, coil=1.0, br=2.6, frost=1.0, ws=-0.95, wf=0.2, ff=(8.5, 3.6, 0.5), fb=(10.5, 3.0, 0.5),
               eye=1.0, jaw=0.35, hack=1.0), 'io'),
    (0.4, dict(y=-2.5, pitch=-0.34, hd=(-8.0, -4.2), ha=-0.38, coil=1.05, br=2.8, frost=1.1), 'io'),
    (0.48, dict(y=0.5, pitch=0.08, hd=(4.0, 3.0), ha=0.3, coil=-0.3, br=1.0, frost=1.0, jaw=1.0, ws=-0.2, wf=0.4, ff=(10.5, 0.0, 0.0), fb=(12.5, 0.0, 0.0),
                breath=0.45, eye=1.0, hack=0.6), 'i'),
    (0.58, dict(y=1.0, pitch=0.12, hd=(6.0, 5.0), ha=0.34, coil=-0.45, br=0.4, frost=0.8, jaw=1.0, breath=1.0, ws=0.1), 'o'),
    (0.68, dict(y=1.0, pitch=0.12, hd=(6.2, 5.2), ha=0.32, br=0.2, frost=0.6, jaw=0.95, breath=1.0), 'l'),
    (0.8, dict(y=0.5, pitch=0.05, hd=(3.0, 2.0), ha=0.2, coil=-0.1, br=0.2, frost=0.3, jaw=0.4, breath=0.35, ws=-0.3, wf=0.7, eye=0.4, hack=0.2), 'o'),
    (0.9, dict(y=0.0, pitch=0.0, hd=(0.5, 0.5), ha=0.14, coil=0.0, br=0.4, frost=0.2, jaw=0.1, breath=0.0, eye=0.15, hack=0.0), 'io'),
    (1.0, dict(hd=(0.0, 0.0), ha=0.12), 'io'),
]

# kuyruk süpürmesi: 8 kare. Yan görünüşte "önden süpürme" için ejder yarım döner (flip: 1 sağa bakar .. -1 sola; arada
# daralarak döner): hazırlıkta kalçasını çevirir, kuyruğu yukarı kurar; temasta arkası dönük, kuyruk önden aşağı süpürülür.
_TA_TS = [0.0, 0.12, 0.25, 0.38, 0.5, 0.58, 0.72, 0.86]
_TAIL = [
    (0.0, dict(ta=math.pi * 0.97, tb=0.065, flip=1.0), 'l'),
    (0.12, dict(ta=math.pi * 1.12, tb=0.08, tw=0.05, flip=0.82, pitch=0.06, y=0.8, hd=(-1.0, 3.0), ha=0.35, eye=0.4,
                hf=(-12.0, 0.0, 0.0), hb=(-10.5, 0.0, 0.0), ff=(10.0, 0.0, 0.0), fb=(12.0, 0.0, 0.0)), 'o'),
    (0.25, dict(ta=math.pi * 1.3, tb=0.1, flip=0.62, pitch=0.1, y=1.8, hd=(-3.0, 5.0), ha=0.5, eye=0.8, hack=0.7, spark=0.8, ws=-0.7, wf=0.5), 'o'),
    (0.38, dict(ta=math.pi * 1.36, tb=0.1, flip=0.55, pitch=0.12, y=2.2, hd=(-3.5, 5.6), ha=0.55, eye=1.0, hack=1.0, spark=1.0), 'io'),
    (0.5, dict(ta=math.pi * 1.15, tb=0.04, flip=-0.6, pitch=0.12, y=2.2, hd=(-2.0, 5.0), sweep=0.6, sweep_da=-0.65, sweep_db=-0.06, ws=-0.2, wf=0.4), 'i'),
    (0.58, dict(ta=math.pi * 0.9, tb=-0.01, flip=-1.0, pitch=0.1, y=2.0, hd=(-1.0, 4.0), ha=0.4, sweep=1.0, sweep_da=-1.45, sweep_db=-0.11, spark=1.0, tw=0.0), 'o'),
    (0.72, dict(ta=math.pi * 0.84, tb=-0.02, flip=-0.95, pitch=0.08, y=1.6, sweep=0.55, sweep_da=-0.6, sweep_db=-0.04, hack=0.5, eye=0.6), 'o'),
    (0.86, dict(ta=math.pi * 0.95, tb=0.05, flip=0.5, pitch=0.04, y=0.8, hd=(-0.5, 2.0), ha=0.25, sweep=0.0, sweep_da=0.0, sweep_db=0.0, spark=0.2, hack=0.1,
                eye=0.2, ws=-0.35, wf=0.75, tw=0.15), 'io'),
    (1.0, dict(ta=math.pi * 0.97, tb=0.065, flip=1.0, pitch=0.0, y=0.0, x=0.0, hd=(0.0, 0.0), ha=0.12, spark=0.0, hack=0.0, eye=0.0), 'io'),
]

# sıçrayış: 8 kare
_HOP_TS = [0.0, 0.12, 0.25, 0.38, 0.5, 0.6, 0.74, 0.87]
_HOP = [
    (0.0, dict(y=0.0), 'l'),
    (0.12, dict(y=2.5, pitch=0.06, hd=(-1.0, 3.5), ha=0.25, ws=-0.7, wf=0.4, eye=0.5, hf=(-10.0, 0.0, 0.3), hb=(-8.0, 0.0, 0.3), claw=0.3, tw=0.1), 'o'),
    (0.25, dict(y=4.2, pitch=0.1, x=-1.5, hd=(-2.0, 5.0), ha=0.3, ws=-1.0, wf=0.15, eye=1.0, hack=0.8, hf=(-9.0, 0.0, 0.5), hb=(-7.0, 0.0, 0.5),
                ff=(10.0, 0.0, 0.0), fb=(12.0, 0.0, 0.0), claw=0.6), 'o'),
    (0.38, dict(y=4.6, pitch=0.12, x=-2.0, hd=(-2.2, 5.4), ws=-1.0, wf=0.1, hack=1.0), 'io'),
    (0.5, dict(y=-7.0, pitch=-0.16, x=4.0, hd=(3.0, -1.0), ha=0.15, ws=0.5, wf=0.0, wl=1.0, jaw=0.8, claw=1.0, hack=0.5, ta=math.pi * 0.98, tb=0.02,
               hf=(-16.0, 4.0, 1.0), hb=(-14.0, 5.0, 1.0), ff=(16.0, 10.0, -0.5), fb=(18.0, 10.0, -0.5)), 'i'),
    (0.6, dict(y=-9.0, pitch=-0.1, x=5.0, hd=(4.0, 0.5), ha=0.25, ws=0.9, wl=0.6, jaw=1.0, hf=(-14.0, 7.0, 1.0), hb=(-12.0, 8.0, 1.0),
               ff=(20.0, 8.5, -0.6), fb=(22.0, 8.0, -0.6)), 'o'),
    (0.74, dict(y=-3.0, pitch=0.08, x=5.0, hd=(2.0, 2.5), ha=0.3, ws=-0.4, wf=0.5, wl=-0.6, jaw=0.4, hf=(-4.0, 4.0, 0.5), hb=(-2.0, 3.5, 0.5),
                ff=(17.0, 1.0, 0.0), fb=(19.0, 1.0, 0.0), claw=0.6, dust=0.3), 'i'),
    (0.87, dict(y=3.5, pitch=0.12, x=4.0, hd=(0.0, 4.0), ha=0.3, ws=-0.6, wf=0.6, wl=0.0, jaw=0.2, hf=(-1.0, 0.0, 0.3), hb=(1.0, 0.0, 0.3),
                ff=(17.0, 0.0, 0.0), fb=(19.0, 0.0, 0.0), claw=0.3, dust=1.0, hack=0.2), 'o'),
    (1.0, dict(y=0.5, pitch=0.02, x=2.0, hd=(0.0, 1.0), ha=0.15, ws=-0.35, wf=0.75, hf=(-3.0, 0.0, 0.0), hb=(-1.0, 0.0, 0.0), ff=(17.0, 0.0, 0.0), fb=(19.0, 0.0, 0.0),
               dust=1.4, eye=0.1, claw=0.0, hack=0.0), 'io'),
]

_HURT = [
    (0.0, dict(x=-2.5, y=-1.0, pitch=-0.18, hd=(-5.0, -3.0), ha=-0.3, coil=0.5, jaw=0.7, squint=1.0, ws=-0.9, wf=0.2, ff=(8.0, 2.0, 0.3), fb=(10.0, 1.5, 0.3),
               tw=0.5, hack=0.8), 'l'),
    (0.5, dict(x=-3.5, y=0.0, pitch=-0.08, hd=(-3.0, -1.0), ha=-0.1, coil=0.3, jaw=0.4, squint=0.7, ws=-0.6, wf=0.5, ff=(8.5, 0.5, 0.0), fb=(10.5, 0.4, 0.0), hack=0.4), 'o'),
    (1.0, dict(x=-3.0, y=0.0, pitch=0.0, hd=(-0.5, 0.0), ha=0.1, coil=0.0, jaw=0.1, squint=0.2, ws=-0.35, wf=0.75, ff=(9.0, 0.0, 0.0), fb=(11.0, 0.0, 0.0), hack=0.0), 'io'),
]


def _row(frames, fps, loop, pose, ts=None, mk=None, vx=None):
    return dict(frames=frames, fps=fps, loop=loop, pose=pose, ts=ts, mk=mk, vx=vx)


ROWS = {
    'idle': _row(8, 8, True, _idle),
    'move': _row(8, WALK_FPS, True, _walk, vx=round(WALK_S / (WALK_DUTY * 8 / WALK_FPS), 1)),
    'hurt': _row(3, 14, False, _K(_HURT)),
    'atk_breath': _row(10, 12, False, _K(_BREATH), ts=_BR_TS, mk=[0.45, 0.48, 0.76]),
    'atk_tail': _row(8, 12, False, _K(_TAIL), ts=_TA_TS, mk=[0.46, 0.5, 0.7]),
    'atk_hop': _row(8, 12, False, _K(_HOP), ts=_HOP_TS, mk=[0.46, 0.5, 0.72]),
}


def _durum():
    d = {"idle": "idle", "chase": "move", "recover": "idle", "evade": "move", "_hurt": "hurt", "_hurt_big": "hurt", "_break": "hurt"}
    for m in ('breath', 'tail', 'hop'):
        for ph in ('windup', 'act', 'recover'):
            d['%s/%s' % (ph, m)] = 'atk_' + m
    return d


DURUM = _durum()


def anims_for(var='ejder_yavrusu'):
    return {k: {kk: vv for kk, vv in r.items() if kk != 'pose'} for k, r in ROWS.items()}


def durum_for(var='ejder_yavrusu'):
    return dict(DURUM)


def _frame_time(row, i):
    if row['ts']:
        return row['ts'][i]
    if row['loop']:
        return i / row['frames']
    return i / max(1, row['frames'] - 1)


SHADE = dict(outer=0.75, rim=1.0, rim_col=(1.0, 0.86, 0.66), rim_dir=(0.6, -0.8), rim_w=1.5, form=(5.0, (0.74, 0.76, 0.9)))


def render_frame(anim, i, var='ejder_yavrusu', ss=3):
    row = ROWS[anim]
    tt = _frame_time(row, i)
    p = dict(row['pose'](tt))
    p['t'] = tt
    p['ph'] = tt * math.tau * (1 if row['loop'] else 1.5) + i * 0.6
    cv = u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
