"""Bozkurt (kimlik bengu_kurt: Bengü'nün ruh biçimi) — stil v2 "mürekkep-cel" (inkkit.py). v1: bozkurt.draw_bozkurt.

Aynı iskelet (K = 1.75; kalça/omuz/baş noktaları, wolfkit bacak eklemleri), pozlar (BOZKURT_ANIMS: idle 6, run 8,
bite 5, pounce 4, howl 4, hurt 2) ve 'head'/'mouth' çapaları. Ak kurt: mavi-mor gölgeli kar beyazı post (kıl
darbeleri, karın/göğüs/yanakta sivri tutamlar), derin göğüs, içe çekik bel, uzun bacaklar; kafa tepesinden omuz
tümseğine uzanan Kut alevi yelesi (üç kat: koyu turkuaz dış dil, camgöbeği orta, beyaz-sıcak göbek; hepsi ışır,
dış dilin dibinde ince mürekkep), kuyruk ucu ve topuklarda ruh alevi, kalçada ve omuzda ışıyan altın Göktürk tamgası,
boyunda tunç halka ve Kut taşı, geriye savrulan turkuaz atkı (Bengü'nün atkısı), yanakta kırmızı savaş boyası,
camgöbeği Kut gözü (arkaya ışık izi). Uluma/ısırıkta alev dilleri uzar.
"""
import math

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_leg, lerp2, chain
import wolfkit as wk
from bozkurt import BOZKURT_ANIMS

K = 1.75
TEX = 4.0
CELL = (640, 480)        # dünya 160 x 120 (v1: 160 x 112; uluma ve yele için üstte pay)
FEET = (288, 448)        # dünya (72, 112)

FUR = Ink('#eef1f6', '#8d97bb', '#ffffff', '#5c6690', kind='fur', name='ak post')
FUR_B = Ink('#b9c1d4', '#727c9e', '#d8deea', '#4a5276', kind='fur', name='uzak post')
FUR_D = Ink('#a6b0c8', '#646e94', '#c8d0e0', '#424a6c', kind='fur', name='karın/arka gölge')
CLAW = Ink('#3a3f52', '#1c1e2a', '#7a8098', name='pençe tırnağı')
NOSE = Ink('#26232c', '#141218', '#6a6a7a', name='burun')
GUM = (0.62, 0.16, 0.22)
TOOTH = Ink('#f4f0e2', '#a49c88', '#ffffff', name='diş')
TORC = Ink('#d0a050', '#7a4a22', '#fff0b0', kind='metal', name='tunç halka')
SCARF = Ink('#27c2b0', '#0e5a68', '#9ff6e2', '#0a3a48', name='turkuaz atkı')
SCARF_B = SCARF.darker(0.78)
PAINT = (0.86, 0.12, 0.16)
# Kut alevi (ışır): dış / orta / göbek
FL_OUT = (0.10, 0.62, 0.70)
FL_MID = (0.36, 0.94, 0.96)
FL_CORE = (0.90, 1.0, 1.0)
GL_OUT = (0.04, 0.42, 0.50)
GL_MID = (0.14, 0.78, 0.86)
GL_CORE = (0.55, 1.0, 1.0)
TAMGA = (1.0, 0.84, 0.40)
TAMGA_GL = (1.0, 0.62, 0.12)
EYE = (0.62, 1.0, 1.0)
EYE_GL = (0.3, 0.95, 1.0)


def _tufts(pts, ang, length, width):
    out = []
    for i, (x, y) in enumerate(pts):
        a = ang + math.sin(i * 2.3 + x * 0.1) * 0.25
        ln = length * (0.78 + 0.22 * math.cos(i * 1.7))
        tip = (x + math.cos(a) * ln, y + math.sin(a) * ln)
        nx_, ny_ = -math.sin(a) * width * 0.5, math.cos(a) * width * 0.5
        out.append([(x + nx_, y + ny_), (tip[0], tip[1], 0.0), (x - nx_, y - ny_)])
    return out


def _tongue(cv, base, ang, length, width, ph, curl=-0.16, wave=0.32):
    """Tek alev dili (cihaz yolu): tabanda dolgun, ortada S kıvrımlı, ucu sivri; yanından kısa bir yalım ayrılır."""
    pts = chain(base, 6, length / 6, ang, curl, ph, wave)
    q = [cv.W(p) for p in pts]
    prof = lambda s, ph=ph: max(0.03, (math.sin(math.pi * min(1.0, s * 2.4 + 0.12)) ** 0.5 if s < 0.2 else 1.0)
                                * max(0.0, 1.0 - s) ** 1.15 * (0.88 + 0.12 * math.sin(s * 11.0 + ph)))
    path = ik.taper_path(q, cv.u(width * 2), prof=prof)
    # yan yalım: ortadan dışa (yukarı) ayrılan kısa dil
    mid = pts[2]
    a2 = ang + 0.55 + math.sin(ph * 1.3) * 0.15
    lick = chain(mid, 4, length * 0.11, a2, curl * 1.5, ph + 1.7, wave)
    lp = ik.taper_path([cv.W(p) for p in lick], cv.u(width * 0.9), prof=lambda s: max(0.03, max(0.0, 1.0 - s) ** 1.2))
    return ik.union(path, lp)


def _flames(cv, specs, z, layers=3, ol=True):
    """Alev kütlesi: specs = [(taban, açı, uzunluk, genişlik, faz)]. Önce bütün dış diller, sonra orta, sonra göbek
    (diller tek bir alev kütlesi gibi kaynaşır). Hepsi ışıma sayfasına da yazılır."""
    lay = ((1.0, 1.0, FL_OUT, GL_OUT, 0.0), (0.76, 0.6, FL_MID, GL_MID, 0.3), (0.5, 0.3, FL_CORE, GL_CORE, 0.55))
    for li, (ls, ws, col, gl, sink) in enumerate(lay[:layers]):
        paths = []
        for (b, a, L, W, ph) in specs:
            bb = (b[0] - math.cos(a) * sink * W, b[1] - math.sin(a) * sink * W)
            paths.append(_tongue(cv, bb, a, L * ls, W * ws, ph - li * 0.35))
        u = ik.union(*paths)
        if li == 0 and ol:
            cv.shape(u, Ink(col, mix_(col, (0.02, 0.2, 0.3), 0.45), (0.7, 1.0, 1.0)), z=z, sd=1.0, hi=0.0, ol=0.5, soft=0.0, glow=gl, grad=0.0)
        else:
            cv.fill(u, col, z=z + li * 0.1, glow=gl)


def _flame(cv, base, ang, length, width, ph, z, layers=3, curl=-0.16, wave=0.32, ol=True):
    _flames(cv, [(base, ang, length, width, ph)], z, layers, ol)


def _sparks(cv, c, ph, n, spread, z):
    """Kut kıvılcımları: yükselen küçük eşkenar dörtgenler (ışır)."""
    for i in range(n):
        t = (ph / math.tau * 0.7 + i / n) % 1.0
        x = c[0] - spread * (0.3 + 0.7 * ((i * 0.618) % 1.0)) - t * spread * 0.4
        y = c[1] - t * spread * 0.9 - 2.0
        r = 0.9 * (1.0 - t) + 0.3
        cv.fill(cv.blob([(x, y - r * 1.6, 0.0), (x + r, y, 0.0), (x, y + r * 1.6, 0.0), (x - r, y, 0.0)]), FL_CORE, z=z, glow=GL_MID)


def mix_(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _tamga(cv, c, s, z, flip=1):
    x, y = c
    strokes = [[(x - 2.2 * s, y + 2.4 * s), (x + 0.4 * s, y - 2.6 * s), (x + 2.6 * s * flip, y + 1.6 * s)],
               [(x - 1.4 * s, y + 0.2 * s), (x + 1.6 * s, y + 0.2 * s)]]
    for st in strokes:
        cv.stroke(st, 2.6, z=z, col=TAMGA, taper=(0.12, 0.25), glow=TAMGA_GL)


def _hind(cv, hip, a, z, near):
    s = K
    _, foot = fk_leg(hip, a[0], a[1], 8.6 * s, 10.2 * s)
    up = wk.norm((hip[0] - foot[0], hip[1] - foot[1]))
    hock = wk.add(foot, wk.rot(up, -0.55), 5.4 * s)
    knee, hock = wk.ik(hip, hock, 7.6 * s, 7.2 * s, -1)
    m = FUR if near else FUR_B
    th = lerp2(hip, knee, 0.42)
    thigh = ik.union(cv.ellipse(th, 6.0 * s, 4.6 * s, math.atan2(knee[1] - hip[1], knee[0] - hip[0])),
                     cv.limb([hip, knee], [4.2 * s, 2.3 * s]),
                     cv.blob([q for t in _tufts([lerp2(hip, knee, 0.5), lerp2(hip, knee, 0.78)], math.pi * 0.8, 3.0 * s, 2.0 * s) for q in t]))
    lower = cv.limb([knee, hock, foot], [2.3 * s, 1.5 * s, 1.3 * s])
    paw = cv.blob([(foot[0] - 1.3 * s, foot[1] - 1.5 * s), (foot[0] + 1.8 * s, foot[1] - 2.0 * s), (foot[0] + 3.7 * s, foot[1] - 0.8 * s),
                   (foot[0] + 3.5 * s, foot[1] + 0.3, 0.0), (foot[0] - 1.1 * s, foot[1] + 0.3, 0.0)])
    leg = ik.union(thigh, lower, paw)
    det = [('ink', [lerp2(hip, knee, 0.3), lerp2(hip, knee, 0.6), lerp2(hip, knee, 0.82)], 1.3, (0.3, 0.5))] if near else []
    det.append(('ink', [(foot[0] + 0.8 * s, foot[1] - 1.6 * s), (foot[0] + 1.6 * s, foot[1] - 0.2)], 1.0, (0.2, 0.2)))
    cv.shape(leg, m, z=z, sd=2.4 * s, hi=0.35 if near else 0.0, details=det, bounce=0.3 if near else 0.0, fur=0.8)
    for i in range(2):
        x, y = foot[0] + (3.3 + i * 0.3) * s, foot[1] - (1.0 - i * 0.8) * s
        cv.shape(cv.blob([(x - 0.4 * s, y - 0.45 * s), (x + 1.3 * s, y + 0.4 * s, 0.0), (x - 0.4 * s, y + 0.45 * s)]), CLAW, z=z + 0.3, sd=0.4, ol=0.6)
    return hock


def _front(cv, sh, a, z, near):
    s = K
    _, foot = fk_leg(sh, a[0], a[1], 9.0 * s, 9.6 * s)
    up = wk.norm((sh[0] - foot[0], sh[1] - foot[1]))
    wrist = wk.add(foot, wk.rot(up, 0.32), 3.2 * s)
    elbow, wrist = wk.ik(sh, wrist, 7.6 * s, 8.4 * s, 1)
    m = FUR if near else FUR_B
    blade = cv.ellipse(lerp2(sh, elbow, 0.35), 5.2 * s, 3.4 * s, math.atan2(elbow[1] - sh[1], elbow[0] - sh[0]))
    leg = ik.union(blade, cv.limb([sh, elbow, wrist, foot], [3.1 * s, 2.2 * s, 1.45 * s, 1.3 * s]),
                   cv.blob(_tufts([lerp2(elbow, wrist, 0.12)], math.pi * 0.86, 2.6 * s, 1.6 * s)[0]),
                   cv.blob([(foot[0] - 1.3 * s, foot[1] - 1.5 * s), (foot[0] + 1.8 * s, foot[1] - 2.0 * s), (foot[0] + 3.7 * s, foot[1] - 0.8 * s),
                            (foot[0] + 3.5 * s, foot[1] + 0.3, 0.0), (foot[0] - 1.1 * s, foot[1] + 0.3, 0.0)]))
    det = [('ink', [lerp2(elbow, wrist, 0.2), lerp2(elbow, wrist, 0.8)], 1.1, (0.3, 0.4))] if near else []
    cv.shape(leg, m, z=z, sd=2.0 * s, hi=0.35 if near else 0.0, details=det, bounce=0.3 if near else 0.0, fur=0.8)
    for i in range(2):
        x, y = foot[0] + (3.3 + i * 0.3) * s, foot[1] - (1.0 - i * 0.8) * s
        cv.shape(cv.blob([(x - 0.4 * s, y - 0.45 * s), (x + 1.3 * s, y + 0.4 * s, 0.0), (x - 0.4 * s, y + 0.45 * s)]), CLAW, z=z + 0.3, sd=0.4, ol=0.6)
    return wrist


def draw(cv, p):
    bob, tilt, jaw = p.get('bob', 0.0), p.get('tilt', 0.0), p.get('jaw', 0.0)
    howl = p.get('howl', 0.0)
    crouch = p.get('crouch', 0.0)
    stretch = p.get('stretch', 0.0)
    ph = p.get('ph', 0.0)
    snarl = p.get('snarl', 0.3)
    hipp = ((-10.5 - stretch * 2.5) * K, (-19.5 + bob - tilt * 6) * K + crouch * 7)
    shp = ((9.0 + stretch * 2.0) * K, (-22.0 + bob + tilt * 6) * K + crouch * 7)
    fl = 1.0 + 0.35 * howl + 0.15 * (jaw > 0.6)          # alev uzunluğu (uluma/ısırıkta büyür)

    # ---- uzak bacaklar + topuk alevleri
    for leg_fn, base, key in ((_hind, hipp, 'hb'), (_front, shp, 'fb')):
        j = leg_fn(cv, base, p[key], -8, False)
        _flame(cv, (j[0] - 0.6 * K, j[1]), math.pi * 1.05 + math.sin(ph - 0.8) * 0.18, 3.8 * K, 1.0 * K, ph, -8.5, layers=2)

    # ---- atkı (arkada)
    neck0 = (shp[0] + 2.5 * K, shp[1] - 3.0 * K)
    for k_, (n, seg, w0, dph, da) in enumerate(((7, 3.4, 2.6, 0.0, 0.0), (6, 3.2, 2.1, 1.2, -0.2))):
        sc = chain((neck0[0] - 1.5 * K, neck0[1] + 0.5 * K), n, seg * K, math.pi * 1.16 + p.get('tw', 0.0) * 0.3 + da, -0.06, ph - dph, 0.5)
        prof = lambda s_, ph=ph, k_=k_: max(0.3, (1 - 0.45 * s_) * (0.55 + 0.45 * abs(math.cos(s_ * 4.0 + ph + k_))))
        cv.shape(ik.taper_path([cv.W(q) for q in sc], cv.u(w0 * K), prof=prof), SCARF if k_ == 0 else SCARF_B, z=(19.0 if k_ == 0 else -6.0),
                 sd=1.4, hi=0.3 if k_ == 0 else 0.0)

    # ---- kuyruk: kalın gür kuyruk, uçta Kut alevi
    tw = p.get('tw', 0.0)
    tl = chain((hipp[0] - 4.5 * K, hipp[1] - 3.0 * K), 6, 3.4 * K, math.pi * 1.08 + tw, -0.16, ph, 0.28)
    tail = ik.union(ik.taper_path([cv.W(q) for q in tl], cv.u(6.4 * K),
                                  prof=lambda u: max(0.25, 0.6 + 0.5 * math.sin(math.pi * min(1.0, u * 1.25)) - 0.45 * u)),
                    *[cv.blob(t) for t in _tufts(tl[1:6], math.pi * 1.35 + tw, 3.4 * K, 2.2 * K)])
    cv.shape(tail, FUR_B, z=-6, sd=2.2 * K, hi=0.3, fur=0.9,
             details=[('ink', [tl[1], tl[2], tl[3]], 1.2, (0.3, 0.5))])
    _flames(cv, [(tl[-3], math.pi * 1.1 + tw + math.sin(ph) * 0.2, 9.0 * K * fl, 2.4 * K, ph),
                 (tl[-2], math.pi * 1.26 + tw + math.cos(ph) * 0.2, 6.5 * K * fl, 1.8 * K, ph + 1.0),
                 (tl[-2], math.pi * 0.95 + tw + math.cos(ph) * 0.2, 5.0 * K * fl, 1.4 * K, ph + 2.0)], -5.5)

    # ---- gövde: kalça + bel + göğüs + omuz tümseği (tek kontur), karın ve göğüs tutamları
    body = ik.union(cv.ellipse((hipp[0], hipp[1] + 0.5 * K), 7.4 * K, 7.0 * K),
                    cv.capsule((hipp[0] + 2 * K, hipp[1] - 1.5 * K), (shp[0] - 3 * K, shp[1] - 1.5 * K), 5.4 * K, 6.8 * K),
                    cv.ellipse((shp[0] + 0.5 * K, shp[1] + 2.5 * K), 8.2 * K, 9.6 * K, -0.25),
                    cv.ellipse((shp[0] - 2.0 * K, shp[1] - 5.5 * K), 6.0 * K, 3.6 * K))
    bp = [lerp2((hipp[0] + 1 * K, hipp[1] + 3.6 * K), (shp[0] - 1 * K, shp[1] + 7.6 * K), t) for t in (0.1, 0.35, 0.6, 0.85)]
    belly = [cv.blob(t) for t in _tufts(bp, math.pi * 0.68, 4.0 * K, 2.4 * K)]
    chest = [cv.blob(t) for t in _tufts([(shp[0] + 7.5 * K, shp[1] + 1.0 * K), (shp[0] + 8.0 * K, shp[1] + 5.0 * K), (shp[0] + 6.5 * K, shp[1] + 9.0 * K)],
                                        math.pi * 0.18, 3.8 * K, 2.4 * K)]
    body = ik.union(body, *belly, *chest)
    bdet = []
    # kas/post akış çizgileri: kalça, böğür, kürek
    bdet.append(('ink', [(hipp[0] + 3.0 * K, hipp[1] - 4.0 * K), (hipp[0] + 5.6 * K, hipp[1] + 0.0), (hipp[0] + 4.6 * K, hipp[1] + 4.0 * K)], 1.4, (0.2, 0.6)))
    bdet.append(('ink', [(shp[0] - 5.0 * K, shp[1] - 2.0 * K), (shp[0] - 3.4 * K, shp[1] + 2.4 * K), (shp[0] - 4.2 * K, shp[1] + 6.0 * K)], 1.3, (0.2, 0.6)))
    for i in range(3):
        cx = shp[0] - 6.5 * K - i * 2.4 * K
        bdet.append(('ink', [(cx, shp[1] + 2.2 * K), (cx - 0.4 * K, shp[1] + 4.6 * K)], 1.0, (0.3, 0.4)))
    bdet += cv.fold([(hipp[0] + 6 * K, hipp[1] + 3 * K), (hipp[0] + 9 * K, hipp[1] + 4.2 * K), (shp[0] - 4 * K, shp[1] + 6.5 * K)], 1.0, 1.3, -1)
    cv.shape(body, FUR, z=0, sd=4.0 * K, hi=0.5, details=bdet, bounce=0.4, fur=1.0, hatch=0.15)
    # tamgalar: kalça + kürek
    _tamga(cv, (hipp[0] - 1.5 * K, hipp[1] - 0.5 * K), 0.85 * K, 1.0, -1)

    # ---- yele: kafa tepesinden omuz tümseğine Kut alevi dilleri (arkaya-yukarı savrulur)
    hy_off = p.get('hy', 0.0) * K - howl * 11
    head = (shp[0] + 11.0 * K - howl * 3.5, shp[1] - 7.0 * K + hy_off)
    ma = (head[0] - 2.5 * K, head[1] - 3.0 * K)
    mb = (shp[0] - 7.5 * K, shp[1] - 4.5 * K)
    lens = (8.0, 12.0, 15.0, 16.5, 15.5, 13.0, 10.0, 7.0)
    specs = []
    for i in range(8):
        t = i / 7
        b = lerp2(ma, mb, t)
        ang = math.atan2(-0.86, -0.52) + 0.22 * t + howl * 0.3 + math.sin(ph * 1.2 - i * 0.9) * 0.06
        specs.append(((b[0], b[1] + 1.0 * K), ang, lens[i] * K * fl * (0.9 + 0.12 * math.sin(i * 2.7)), (3.3 - 0.9 * abs(t - 0.45)) * K,
                      ph * 1.2 - i * 0.7))
    _flames(cv, specs, 24)
    _sparks(cv, lerp2(ma, mb, 0.4), ph, 4, 9.0 * K, 27)

    # ---- boyun halkası + Kut taşı
    na, nb_ = (shp[0] + 2.0 * K, shp[1] - 2.5 * K), None
    # ---- boyun + baş
    hx_, hy_ = head
    neck = cv.capsule((shp[0] + 2.0 * K, shp[1] - 2.5 * K), (hx_ - 2 * K, hy_ + 1 * K), 6.2 * K, 5.0 * K)
    ruff = [cv.blob(t) for t in _tufts([(hx_ - 3.5 * K, hy_ + 2.5 * K), (hx_ - 4.5 * K, hy_ + 0.5 * K), (hx_ - 2.0 * K, hy_ + 4.2 * K)],
                                       math.pi * 0.8, 4.2 * K, 2.6 * K)]
    skull = cv.ellipse(head, 5.8 * K, 4.6 * K, -0.15)
    brow = cv.blob([(hx_ - 1.0 * K, hy_ - 2.2 * K), (hx_ + 4.8 * K, hy_ - 1.4 * K), (hx_ + 4.0 * K, hy_ - 3.6 * K), (hx_ - 0.5 * K, hy_ - 4.2 * K)])
    ang = -howl * 0.95
    sn0 = (hx_ + 3.0 * K, hy_ + 0.4 * K)
    sn1 = (sn0[0] + math.cos(ang) * 10.0 * K, sn0[1] + math.sin(ang) * 10.0 * K)
    snout = cv.capsule(sn0, sn1, 3.2 * K, 1.9 * K)
    # kulaklar (geriye yatık)
    ear_a = -0.55 - p.get('ears', 0.6) * 0.9
    for (ox, oy, m, zz) in ((-2.6, -3.4, FUR_B, 6.5), (0.2, -4.0, FUR, 16.5)):
        e0 = (hx_ + ox * K, hy_ + oy * K)
        tip = (e0[0] + math.cos(math.pi * 1.5 + ear_a) * 7.5 * K, e0[1] + math.sin(math.pi * 1.5 + ear_a) * 7.5 * K)
        det = []
        if m is FUR:
            det = [('col', cv.blob([(e0[0] - 0.8 * K, e0[1] + 0.3 * K), (e0[0] + 0.8 * K, e0[1] + 0.1 * K),
                                     (lerp2(e0, tip, 0.62)[0], lerp2(e0, tip, 0.62)[1], 0.0)]), (0.62, 0.42, 0.5))]
        cv.shape(cv.blob([(e0[0] - 2.2 * K, e0[1] + 0.8 * K), (tip[0], tip[1], 0.0), (e0[0] + 1.8 * K, e0[1] + 0.4 * K)]), m, z=zz, sd=1.6 * K,
                 details=det, fur=0.6)
    # alt çene + ağız içi + dişler
    jd = (jaw + howl * 0.55) * 4.0 * K
    jaw0 = (hx_ + 2.6 * K, hy_ + 3.4 * K)
    jaw1 = (jaw0[0] + math.cos(ang + 0.18) * 8.0 * K, jaw0[1] + math.sin(ang + 0.18) * 8.0 * K + jd)
    if jaw + howl > 0.15:
        cv.fill(cv.blob([(hx_ + 3.6 * K, hy_ + 2.4 * K), (sn1[0] - 1.2 * K, sn1[1] + 2.2 * K), (jaw1[0] - 0.4 * K, jaw1[1] - 0.8 * K),
                         (hx_ + 3.6 * K, hy_ + 3.6 * K + jd * 0.5)]), GUM, z=7.0)
        cv.fill(cv.blob([(hx_ + 4.2 * K, hy_ + 2.9 * K), (sn1[0] - 3.0 * K, sn1[1] + 2.4 * K), (jaw1[0] - 2.0 * K, jaw1[1] - 1.0 * K),
                         (hx_ + 4.4 * K, hy_ + 3.4 * K + jd * 0.4)]), (0.25, 0.04, 0.1), z=7.05)
        for i in range(2):
            fx = jaw0[0] + (2.5 + i * 3.0) * K
            fy = jaw0[1] + jd * (0.35 + i * 0.2)
            cv.shape(cv.blob([(fx - 0.6 * K, fy + 0.4 * K), (fx + 0.6 * K, fy + 0.4 * K), (fx, fy - 1.8 * K, 0.0)]), TOOTH, z=7.1, sd=0.3, ol=0.5)
    cv.shape(cv.capsule(jaw0, jaw1, 2.0 * K, 1.2 * K), FUR_D, z=7.2, sd=1.0 * K, fur=0.4)
    for i, (t, ln) in enumerate(((0.55, 2.6), (0.72, 1.6), (0.86, 1.3))):
        fx, fy = lerp2(sn0, sn1, t)
        fy += 1.9 * K
        cv.shape(cv.blob([(fx - 0.7 * K, fy - 0.3 * K), (fx + 0.7 * K, fy - 0.3 * K), (fx + 0.1 * K, fy + ln * K, 0.0)]), TOOTH, z=7.15, sd=0.3, ol=0.55)
    headp = ik.union(neck, skull, brow, snout, *ruff)
    hdet = [
        ('deep', cv.wedge([(hx_ + 0.4 * K, hy_ - 2.4 * K), (hx_ + 2.6 * K, hy_ - 2.6 * K), (hx_ + 4.6 * K, hy_ - 2.0 * K)], 0.6 * K, -1.0)),
        ('ink', [(hx_ + 0.2 * K, hy_ - 2.7 * K), (hx_ + 2.6 * K, hy_ - 2.9 * K), (hx_ + 5.0 * K, hy_ - 2.1 * K)], 2.6, (0.15, 0.7)),     # kaş
        ('ink', [(sn1[0] - 0.4 * K, sn1[1] + 1.8 * K), lerp2(sn0, sn1, 0.5), (hx_ + 3.6 * K, hy_ + 3.0 * K)], 1.8, (0.1, 0.5)),      # dudak çizgisi
        ('stroke', [(hx_ + 1.2 * K, hy_ + 0.2 * K), (hx_ + 0.2 * K, hy_ + 1.6 * K)], 3.2, PAINT, (0.1, 0.8)),
        ('stroke', [(hx_ + 2.4 * K, hy_ + 0.5 * K), (hx_ + 1.4 * K, hy_ + 2.0 * K)], 2.6, PAINT, (0.1, 0.8)),
        ('ink', [(hx_ - 2.4 * K, hy_ - 1.6 * K), (hx_ - 1.2 * K, hy_ + 0.2 * K), (hx_ - 2.0 * K, hy_ + 2.0 * K)], 1.4, (0.4, 0.4)),
    ]
    if snarl > 0.2:
        for k_ in range(2):
            a_ = lerp2(sn0, sn1, 0.22 + k_ * 0.12)
            hdet.append(('ink', [(a_[0], a_[1] - 1.8 * K), (a_[0] + 0.5 * K, a_[1] - 1.0 * K)], 1.2, (0.2, 0.3)))
    cv.shape(headp, FUR, z=8, sd=2.6 * K, hi=0.45, details=hdet, cast=1.0, bounce=0.35, fur=0.8)
    cv.shape(cv.ellipse((sn1[0] + 0.6 * K, sn1[1] - 0.5 * K), 1.4 * K, 1.1 * K), NOSE, z=9, sd=0.5 * K, hi=0.25, ol=0.7)
    # göz: Kut yarığı + arkaya ışık izi
    ec = (hx_ + 2.4 * K, hy_ - 1.5 * K)
    cv.fill(cv.blob([(ec[0] - 1.8 * K, ec[1] - 0.3 * K, 0.0), (ec[0], ec[1] - 0.7 * K), (ec[0] + 1.8 * K, ec[1] + 0.2 * K, 0.0), (ec[0], ec[1] + 0.5 * K)]),
            EYE, z=9.2, glow=EYE_GL)
    cv.stroke([(ec[0] - 1.6 * K, ec[1] - 0.2 * K), (ec[0] - 4.0 * K, ec[1] - 0.9 * K), (ec[0] - 6.5 * K, ec[1] - 1.2 * K)], 2.4, z=9.1,
              col=FL_MID, taper=(0.1, 0.95), glow=GL_MID)
    # tunç halka (boynu saran yay) + Kut taşı (gırtlakta)
    hn = (hx_ - 2 * K, hy_ + 1 * K)
    cc = lerp2(na, hn, 0.42)
    ax_ = math.atan2(hn[1] - na[1], hn[0] - na[0])
    nx, ny = -math.sin(ax_), math.cos(ax_)        # boyna dik (aşağı-ön)
    tx, ty = math.cos(ax_), math.sin(ax_)
    arc = [(cc[0] + nx * 5.9 * K * math.sin(a) + tx * 1.3 * K * math.cos(a), cc[1] + ny * 5.9 * K * math.sin(a) + ty * 1.3 * K * math.cos(a))
           for a in [(-0.5 + 1.0 * j / 8) * math.pi for j in range(9)]]
    band = ik.taper_path([cv.W(q) for q in arc], cv.u(1.5 * K), prof=lambda s_: 1.0)
    cv.shape(band, TORC, z=20, sd=0.5 * K, hi=0.4, ol=0.8,
             details=[('ink', [lerp2(arc[j], arc[j + 1], 0.5), lerp2(arc[j], arc[j + 1], 0.55)], 0.9) for j in range(1, 8, 2)])
    st_c = arc[-2]
    cv.shape(cv.ellipse(st_c, 1.3 * K, 1.3 * K), TORC, z=20.4, sd=0.4 * K, ol=0.8)
    cv.fill(cv.ellipse(st_c, 0.9 * K, 0.9 * K), FL_MID, z=20.5, glow=GL_CORE)
    cv.fill(cv.ellipse((st_c[0] - 0.3 * K, st_c[1] - 0.3 * K), 0.35 * K, 0.35 * K), FL_CORE, z=20.6)
    # omuz tamgası
    _tamga(cv, (shp[0] - 3.8 * K, shp[1] + 1.0 * K), 0.75 * K, 21.0, 1)

    # ---- yakın bacaklar + topuk alevleri
    for leg_fn, base, key in ((_hind, hipp, 'hf'), (_front, shp, 'ff')):
        j = leg_fn(cv, base, p[key], 12, True)
        _flame(cv, (j[0] - 0.6 * K, j[1]), math.pi * 1.05 + math.sin(ph - 0.8 + 8) * 0.18, 4.0 * K, 1.1 * K, ph + 2.0, 11.5, layers=3)
    return {'mouth': (sn1[0], sn1[1] + 2.2 * K), 'head': head}


ANIMS = {k: (v[0], v[1], k in ('idle', 'run'), True) for k, v in BOZKURT_ANIMS.items()}
SHADE = dict(outer=0.5, rim=0.7, rim_col=(0.62, 0.95, 1.0), rim_dir=(0.55, -0.85), rim_w=1.6, form=(8.0, (0.84, 0.84, 0.95)))


def render_frame(anim, i, ss=3):
    n, fn, loop, arm = ANIMS[anim]
    p = fn(i / n)
    cv = ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
