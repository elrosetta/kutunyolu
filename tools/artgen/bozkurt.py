"""BOZKURT — Bengü'nün ruh biçimi (v5, "epik" yeniden tasarım).

Tasarım notları:
  * Siluet: derin göğüs, yüksek omuz tümseği, içe çekilmiş bel, uzun bacaklar, belirgin topuk (hock),
    büyük pençeler ve pençe tırnakları. Kafa kama biçimli; alın çıkıntılı, kulaklar geriye yatık.
  * Post: kül-beyazı; karın altı ve bacak arkaları koyu arduvaz-turkuaz gölgeli. Yumuşak elips yerine
    göğüs, karın, yanak ve bacak arkalarında sivri tüy öbekleri (poly).
  * Yele: dikenler değil — kafa tepesinden omuz tümseğine uzanan, rüzgârla geriye yatmış kut alevi dilleri
    (çekirdek beyaz-cam göbeği, dış kat turkuaz; ikisi de ışıltılı). Kuyruk ucu ve topuklarda ruh alevi.
  * Tamga: omuz ve kalçada ışıldayan altın Göktürk damgası çizgileri. Boyunda tunç halka + kut taşı,
    geriye savrulan yırtık turkuaz atkı (Bengü'nün atkısı — süreklilik).
  * Gözler: ince, parlak kut yarıkları; arkaya uzanan ışık izi.
Koordinatlar: ayak merkezi (0,0), yüz sağa, y aşağı pozitif.
"""
import math
import numpy as np
from raster import Mat, ramp
from materials import M
from rig import fk_leg, lerp2, chain

K = 1.75
CELL = (160, 112)
FEET = (72, 104)

SFUR = Mat(ramp(205, 0.10, 0.95, spread=0.32), outline='#16303c', name='kül postu')
SFUR_D = Mat(ramp(206, 0.30, 0.64, spread=0.36), outline='#16303c', name='kül postu gölgesi')
SFUR_DD = Mat(ramp(210, 0.40, 0.42, spread=0.36), outline='#16303c', name='kül postu derin')
SMANE = Mat(ramp(178, 0.78, 0.96, spread=0.25), emissive=0.75, outline='#0b4a52', name='kut yelesi')
SMANE_CORE = Mat(ramp(184, 0.22, 1.0, spread=0.15), emissive=1.0, outline='#0b4a52', name='kut yelesi göbeği')
SMANE_OUT = Mat(ramp(196, 0.72, 0.62, spread=0.3), emissive=0.35, outline='#0b3a48', name='kut yelesi dış')
TAMGA = Mat(ramp(44, 0.85, 1.0, spread=0.2), emissive=0.95, outline='#5a3a04', name='altın tamga')
CLAW = Mat(ramp(214, 0.28, 0.28, spread=0.3), name='pençe tırnağı')
TORC = Mat(ramp(36, 0.62, 0.70), spec=0.8, name='tunç halka')
EYE = Mat(ramp(176, 0.60, 1.0, spread=0.15), emissive=1.0, outline='#0b4a52', name='kut gözü')
SCARF = M['turq']
SCARF_D = Mat(ramp(176, 0.72, 0.5), name='turkuaz gölge')


def _tufts(c, pts, mat, z, length, ang, n=None, width=None, jitter=0.0):
    """Sivri tüy öbekleri: pts boyunca, verilen açıda (radyan, 0 sağ) uzanan üçgenler."""
    width = width or length * 0.55
    for i, (x, y) in enumerate(pts):
        a = ang + math.sin(i * 2.3) * jitter
        ln = length * (0.75 + 0.25 * math.cos(i * 1.7))
        tip = (x + math.cos(a) * ln, y + math.sin(a) * ln)
        nx_, ny_ = -math.sin(a) * width * 0.5, math.cos(a) * width * 0.5
        c.poly([(x + nx_, y + ny_), (x - nx_, y - ny_), tip], mat, z=z, bevel=1.2, height=1.2)


def _flame(c, base, ang, length, width, sway, z, core=True):
    """Yele alev dili: geriye kıvrılan 5 köşeli dil, dış kat + çekirdek."""
    bx, by = base
    ca, sa = math.cos(ang), math.sin(ang)
    nx_, ny_ = -sa, ca
    # dış kat
    pts = [(bx + nx_ * width, by + ny_ * width),
           (bx - nx_ * width, by - ny_ * width),
           (bx - nx_ * width * 0.55 + ca * length * 0.45 + nx_ * sway * 0.4, by - ny_ * width * 0.55 + sa * length * 0.45 + ny_ * sway * 0.4),
           (bx + ca * length + nx_ * sway, by + sa * length + ny_ * sway),
           (bx + nx_ * width * 0.5 + ca * length * 0.5 + nx_ * sway * 0.5, by + ny_ * width * 0.5 + sa * length * 0.5 + ny_ * sway * 0.5)]
    c.poly(pts, SMANE, z=z, bevel=1.6, height=1.6)
    if core:
        w2 = width * 0.42
        l2 = length * 0.66
        pts2 = [(bx + nx_ * w2, by + ny_ * w2), (bx - nx_ * w2, by - ny_ * w2),
                (bx + ca * l2 + nx_ * sway * 0.6, by + sa * l2 + ny_ * sway * 0.6)]
        c.poly(pts2, SMANE_CORE, z=z + 1.5, bevel=1.0, height=0.8)


def _mane(c, a, b, ph, z, howl=0.0):
    """Yele: a (kafa tepesi) -> b (omuz tümseği) taban çizgisi; geriye-yukarı savrulan alev dilleri.
    Üç kat: dış (koyu turkuaz), orta (turkuaz), çekirdek (beyaz-cam). Her kat aynı tabandan, daha kısa dillerle."""
    n = 7
    lens = [6.5, 9.5, 12.0, 13.0, 12.5, 11.0, 8.5]
    d = (-0.62, -0.78)  # geri-yukarı
    dn = math.hypot(*d)
    d = (d[0] / dn, d[1] / dn)
    ux, uy = b[0] - a[0], b[1] - a[1]
    layers = ((SMANE_OUT, 1.0, 0.0, 3.5), (SMANE, 0.68, 0.6, 2.0), (SMANE_CORE, 0.34, 1.2, -1.5))
    for li, (mat, sc, zoff, sink) in enumerate(layers):
        pts = []
        for i in range(n):
            t = i / (n - 1)
            bx, by = a[0] + ux * t, a[1] + uy * t
            sway = math.sin(ph * 1.2 + i * 0.8 + li * 0.5) * (1.2 + 0.4 * i) * K * sc
            L = lens[i] * K * sc * (1.0 + howl * 0.25)
            tip = (bx + d[0] * L + sway * 0.9, by + d[1] * L + abs(sway) * 0.2)
            if i > 0:
                # dişler arası çukur
                pt = 0.5 * (t + (i - 1) / (n - 1))
                vx, vy = a[0] + ux * pt, a[1] + uy * pt
                Lv = min(lens[i], lens[i - 1]) * K * sc * 0.42
                pts.append((vx + d[0] * Lv, vy + d[1] * Lv))
            pts.append(tip)
        # taban: gövdenin içine 3K gömülü geri dönüş
        pts.append((b[0] + 1.0 * K, b[1] + sink * K))
        pts.append((a[0] + 1.5 * K, a[1] + sink * K))
        c.poly(pts, mat, z=z + zoff, bevel=2.2 * sc + 0.6, height=1.6)


def _tamga(c, p, z, scale=1.0, flip=1):
    """Göktürk damgası: üç çizgi (ok ucu + çizgi) — omuz/kalça işareti."""
    x, y = p
    s = scale * K
    c.capsule((x - 2.2 * s, y + 2.4 * s), (x + 0.4 * s, y - 2.6 * s), 0.55 * s, 0.55 * s, TAMGA, z=z)
    c.capsule((x + 0.4 * s, y - 2.6 * s), (x + 2.6 * s * flip, y + 1.6 * s), 0.55 * s, 0.55 * s, TAMGA, z=z)
    c.capsule((x - 1.4 * s, y + 0.2 * s), (x + 1.6 * s, y + 0.2 * s), 0.45 * s, 0.45 * s, TAMGA, z=z)


def draw_bozkurt(c, p):
    bob, tilt, jaw = p.get('bob', 0.0), p.get('tilt', 0.0), p.get('jaw', 0.0)
    howl = p.get('howl', 0.0)
    crouch = p.get('crouch', 0.0)
    stretch = p.get('stretch', 0.0)
    ph = p.get('ph', 0.0)
    snarl = p.get('snarl', 0.3)
    hipp = ((-10.5 - stretch * 2.5) * K, (-19.5 + bob - tilt * 6) * K + crouch * 7)
    shp = ((9.0 + stretch * 2.0) * K, (-22.0 + bob + tilt * 6) * K + crouch * 7)
    back_dark = lambda lu, lv, px, py: lv < -0.42
    belly_dark = lambda lu, lv, px, py: lv > 0.55
    fur_s = lambda lu, lv, px, py: (np.floor(px * 0.45 - py * 0.85 + lu * 3) % 9 == 0) & (lv < 0.1) & (lv > -0.35)

    # ------------------------------------------------------------ bacaklar
    def leg(base, a, z, front):
        l1 = (9.0 if front else 8.6) * K
        l2 = (9.6 if front else 10.2) * K
        k, f = fk_leg(base, a[0], a[1], l1, l2)
        mat = SFUR if z > 0 else SFUR_D
        mat_sh = SFUR_D if z > 0 else SFUR_DD
        # uyluk: kalın, kalçaya yapışık; ön bacakta omuz kası
        c.capsule(base, k, (4.4 if not front else 3.8) * K, 2.5 * K, mat, z=z, paint=[(belly_dark, mat_sh)])
        # kaval + topuk
        c.capsule(k, f, 2.3 * K, 1.7 * K, mat, z=z + 0.2, paint=[(belly_dark, mat_sh)])
        c.ellipse(k, 2.7 * K, 2.4 * K, mat, z=z + 0.3)
        # bacak arkası tüy öbekleri
        _tufts(c, [lerp2(base, k, 0.45), lerp2(base, k, 0.8)], mat_sh, z - 0.5, 3.2 * K, math.pi * 0.9, jitter=0.2)
        # pençe: geniş, tırnaklı
        paw = (f[0] + 1.6 * K, f[1] - 0.9 * K)
        c.ellipse(paw, 3.0 * K, 1.7 * K, mat, z=z + 0.4)
        for i in range(3):
            tx = paw[0] + (1.4 + i * 1.1) * K
            ty = paw[1] + (0.2 + i * 0.35) * K
            c.poly([(tx - 0.8 * K, ty - 0.6 * K), (tx - 0.8 * K, ty + 0.6 * K), (tx + 1.6 * K, ty + 0.9 * K)], CLAW, z=z + 1.5, bevel=0.6, height=0.5)
        # topuk ruh alevi (küçük)
        _flame(c, (k[0] - 1.2 * K, k[1]), math.pi * 1.05 + math.sin(ph + z) * 0.15, 4.2 * K, 1.3 * K, 0.8, z - 0.2, core=False)
        return f

    leg(hipp, p['hb'], -8, False)
    leg(shp, p['fb'], -8, True)

    # ------------------------------------------------------------ kuyruk: kalın, uçta kut alevi
    tl = chain((hipp[0] - 4.5 * K, hipp[1] - 3.0 * K), 7, 3.5 * K, math.pi * 1.08 + p.get('tw', 0.0), -0.16, ph, 0.28)
    for i, (a, b) in enumerate(zip(tl, tl[1:])):
        r0 = (3.3 - i * 0.28) * K
        mat = SFUR if i < 4 else (SMANE_OUT if i == 4 else SMANE)
        c.capsule(a, b, r0, r0 - 0.25 * K, mat, z=-6, paint=[(back_dark, SFUR_D)] if i < 4 else None)
    _tufts(c, [tl[1], tl[2], tl[3]], SFUR_D, -6.5, 3.4 * K, math.pi * 1.35, jitter=0.25)
    _flame(c, tl[-2], math.pi * 1.12 + p.get('tw', 0.0) + math.sin(ph) * 0.2, 7.0 * K, 2.2 * K, 1.5, -5.5)
    _flame(c, tl[-1], math.pi * 1.25 + p.get('tw', 0.0) + math.cos(ph) * 0.2, 5.0 * K, 1.6 * K, -1.0, -5.6)

    # ------------------------------------------------------------ gövde
    # kalça
    c.ellipse((hipp[0], hipp[1] + 0.5 * K), 7.4 * K, 7.0 * K, SFUR, z=0, paint=[(back_dark, SFUR_D), (fur_s, SFUR_D)])
    # bel: içe çekilmiş (ince kapsül, üstte)
    c.capsule((hipp[0] + 2 * K, hipp[1] - 1.5 * K), (shp[0] - 3 * K, shp[1] - 1.5 * K), 5.6 * K, 6.8 * K, SFUR, z=1,
              paint=[(back_dark, SFUR_D), (fur_s, SFUR_D)])
    # göğüs: derin ve öne çıkık
    c.ellipse((shp[0] + 0.5 * K, shp[1] + 2.5 * K), 8.2 * K, 9.6 * K, SFUR, z=2, rot=-0.25, paint=[(back_dark, SFUR_D), (belly_dark, SFUR_D)])
    # omuz tümseği
    c.ellipse((shp[0] - 2.0 * K, shp[1] - 5.5 * K), 6.0 * K, 3.6 * K, SFUR, z=2.5, paint=[(back_dark, SFUR_D)])
    # karın altı tüy öbekleri
    belly_pts = [lerp2((hipp[0] + 1 * K, hipp[1] + 5.0 * K), (shp[0] - 1 * K, shp[1] + 9.0 * K), t) for t in (0.1, 0.35, 0.6, 0.85)]
    _tufts(c, belly_pts, SFUR_D, 17.8, 4.2 * K, math.pi * 0.68, jitter=0.2)
    chest_pts = [(shp[0] + 7.5 * K, shp[1] + 1.0 * K), (shp[0] + 8.0 * K, shp[1] + 5.0 * K), (shp[0] + 6.5 * K, shp[1] + 9.0 * K)]
    _tufts(c, chest_pts, SFUR, 17.9, 3.8 * K, math.pi * 0.18, jitter=0.25)
    # tamga: kalçada ince altın damga
    _tamga(c, (hipp[0] - 1.5 * K, hipp[1] - 0.5 * K), 19.0, 0.8, -1)

    # ------------------------------------------------------------ yele: kafa tepesinden omuz tümseğine, geriye yatmış kut alevi (3 kat)
    hy_off = p.get('hy', 0.0) * K - howl * 11
    head = (shp[0] + 11.0 * K - howl * 3.5, shp[1] - 7.0 * K + hy_off)
    mane_a = (head[0] - 2.5 * K, head[1] - 3.0 * K)
    mane_b = (shp[0] - 7.5 * K, shp[1] - 4.5 * K)
    _mane(c, mane_a, mane_b, ph, 24.0, howl)

    # ------------------------------------------------------------ boyun halkası + atkı
    neck0 = (shp[0] + 2.5 * K, shp[1] - 3.0 * K)
    c.capsule((neck0[0] - 2.0 * K, neck0[1] + 5.0 * K), (neck0[0] + 4.5 * K, neck0[1] + 0.5 * K), 0.9 * K, 0.9 * K, M['leather'], z=21.0)
    c.capsule((neck0[0] - 1.0 * K, neck0[1] + 4.2 * K), (neck0[0] + 3.8 * K, neck0[1] + 0.6 * K), 0.35 * K, 0.35 * K, TORC, z=21.5)
    c.dot((neck0[0] + 1.0 * K, neck0[1] + 2.4 * K), M['kut'], z=30, size=3)
    sc = chain((neck0[0] - 2.5 * K, neck0[1] + 1.0 * K), 6, 4.2 * K, math.pi * 0.92 + p.get('tw', 0.0) * 0.4, 0.04, ph, 0.4)
    for i, (a, b) in enumerate(zip(sc, sc[1:])):
        c.capsule(a, b, (2.1 - i * 0.22) * K, (1.9 - i * 0.22) * K, SCARF if i % 2 == 0 else SCARF_D, z=-5)
    ex, ey = sc[-1]
    c.poly([(ex, ey - 1.2 * K), (ex, ey + 1.2 * K), (ex - 3.5 * K, ey + 2.2 * K), (ex - 2.0 * K, ey), (ex - 4.0 * K, ey - 1.8 * K)], SCARF, z=-5, bevel=0.8, height=0.6)

    # ------------------------------------------------------------ boyun + baş
    c.capsule((shp[0] + 2.0 * K, shp[1] - 2.5 * K), (head[0] - 2 * K, head[1] + 1 * K), 6.2 * K, 5.0 * K, SFUR, z=4, paint=[(back_dark, SFUR_D), (belly_dark, SFUR_D)])
    hx_, hy_ = head
    # yanak tüyleri (ruff)
    _tufts(c, [(hx_ - 3.5 * K, hy_ + 2.5 * K), (hx_ - 4.5 * K, hy_ + 0.5 * K), (hx_ - 2.0 * K, hy_ + 4.2 * K)], SFUR, 16.0, 4.2 * K, math.pi * 0.8, jitter=0.3)
    # kafatası: kama
    c.ellipse(head, 5.8 * K, 4.6 * K, SFUR, z=6, rot=-0.15, paint=[(back_dark, SFUR_D)])
    # alın çıkıntısı (kaş kemeri)
    c.poly([(hx_ - 1.0 * K, hy_ - 2.2 * K), (hx_ + 4.8 * K, hy_ - 1.4 * K), (hx_ + 4.0 * K, hy_ - 3.6 * K), (hx_ - 0.5 * K, hy_ - 3.8 * K)], SFUR, z=18.0, bevel=1.2, height=1.0)
    # kulaklar: geriye yatık
    ear_a = -0.55 - p.get('ears', 0.6) * 0.9
    for (ox, oy, mat, zz) in ((-2.6, -3.4, SFUR_D, 15.5), (0.2, -4.0, SFUR, 17.0)):
        ex0, ey0 = hx_ + ox * K, hy_ + oy * K
        tip = (ex0 + math.cos(math.pi * 1.5 + ear_a) * 7.5 * K, ey0 + math.sin(math.pi * 1.5 + ear_a) * 7.5 * K)
        c.poly([(ex0 - 2.2 * K, ey0 + 0.8 * K), (ex0 + 1.8 * K, ey0 + 0.4 * K), tip], mat, z=zz, bevel=1.3, height=1.5)
        if mat is SFUR:
            c.poly([(ex0 - 0.8 * K, ey0 + 0.3 * K), (ex0 + 0.8 * K, ey0 + 0.1 * K), lerp2((ex0, ey0), tip, 0.62)], SFUR_DD, z=zz + 0.3, bevel=0.6, height=0.4)
    # burun: uzun kama; ulurken yukarı kalkar
    ang = -howl * 0.95
    sn0 = (hx_ + 3.0 * K, hy_ + 0.4 * K)
    sn1 = (sn0[0] + math.cos(ang) * 10.0 * K, sn0[1] + math.sin(ang) * 10.0 * K)
    c.capsule(sn0, sn1, 3.3 * K, 2.0 * K, SFUR, z=19, paint=[(belly_dark, SFUR_D)])
    # burun sırtı kırışığı (hırlama)
    if snarl > 0.2:
        c.capsule(lerp2(sn0, sn1, 0.25), lerp2(sn0, sn1, 0.55), 0.5 * K, 0.4 * K, SFUR_DD, z=26.0)
    c.ellipse((sn1[0] + 0.6 * K, sn1[1] - 0.5 * K), 1.4 * K, 1.1 * K, M['black'], z=27)
    # üst dişler (sabit görünür): iki uzun köpek dişi + küçük dişler
    for i, (t, ln) in enumerate(((0.55, 2.6), (0.72, 1.6), (0.86, 1.3))):
        fx, fy = lerp2(sn0, sn1, t)
        fy += 1.9 * K
        c.poly([(fx - 0.7 * K, fy - 0.3 * K), (fx + 0.7 * K, fy - 0.3 * K), (fx + 0.1 * K, fy + ln * K)], M['bone'], z=28, bevel=0.5, height=0.4)
    # alt çene
    jd = (jaw + howl * 0.55) * 4.0 * K
    jaw0 = (hx_ + 2.6 * K, hy_ + 3.4 * K)
    jaw1 = (jaw0[0] + math.cos(ang + 0.18) * 8.0 * K, jaw0[1] + math.sin(ang + 0.18) * 8.0 * K + jd)
    c.capsule(jaw0, jaw1, 2.0 * K, 1.2 * K, SFUR_D, z=18.5)
    if jaw + howl > 0.15:
        c.poly([(hx_ + 4.0 * K, hy_ + 2.6 * K), (sn1[0] - 1.5 * K, sn1[1] + 2.4 * K), (jaw1[0], jaw1[1] - 1.0 * K), (hx_ + 4.0 * K, hy_ + 3.6 * K + jd * 0.5)],
               M['red_paint'], z=18.4, bevel=0.5, height=0.3)
        for i in range(2):
            fx = jaw0[0] + (2.5 + i * 3.0) * K
            fy = jaw0[1] + jd * (0.35 + i * 0.2)
            c.poly([(fx - 0.6 * K, fy + 0.4 * K), (fx + 0.6 * K, fy + 0.4 * K), (fx, fy - 1.8 * K)], M['bone'], z=28, bevel=0.5, height=0.4)
    # göz: ince kut yarığı + geriye ışık izi; kaş gölgesi
    c.capsule((hx_ + 0.8 * K, hy_ - 1.9 * K), (hx_ + 4.2 * K, hy_ - 1.2 * K), 1.0 * K, 0.7 * K, EYE, z=30)
    c.capsule((hx_ - 0.5 * K, hy_ - 2.4 * K), (hx_ - 4.0 * K, hy_ - 3.2 * K), 0.6 * K, 0.2 * K, SMANE, z=29)
    c.capsule((hx_ + 0.5 * K, hy_ - 2.9 * K), (hx_ + 4.6 * K, hy_ - 2.2 * K), 0.55 * K, 0.5 * K, SFUR_DD, z=31)
    # savaş boyası: yanakta üç çizgi
    for i in range(3):
        c.capsule((hx_ - 0.5 * K + i * 1.4 * K, hy_ + 0.6 * K), (hx_ + 0.6 * K + i * 1.4 * K, hy_ + 3.0 * K), 0.45 * K, 0.4 * K, M['red_paint'], z=27)

    leg(hipp, p['hf'], 8, False)
    leg(shp, p['ff'], 8, True)
    return {'mouth': (sn1[0], sn1[1] + 2.2 * K), 'head': head}


# ------------------------------------------------------------ animasyonlar
def _gallop(t):
    """Dörtnal: arka bacaklar iter (toplanma), ön bacaklar uzanır (uçuş); gövde uzayıp kısalır."""
    ph = t * math.tau
    s = math.sin(ph)
    s2 = math.sin(ph + 0.45)
    fs = math.sin(ph + math.pi * 0.95)
    fs2 = math.sin(ph + math.pi * 0.95 + 0.45)
    stretch = 0.6 * math.cos(ph + 0.4)
    return dict(bob=-abs(math.cos(ph * 0.5 + 0.3)) * 2.6 + 0.9, tilt=0.16 * math.sin(ph + 0.3), stretch=stretch,
                hb=(1.05 * s, 0.95 - 0.45 * s), hf=(1.05 * s2, 0.95 - 0.45 * s2),
                fb=(-1.0 * fs + 0.15, 0.25 + 0.85 * max(0, fs)), ff=(-1.0 * fs2 + 0.15, 0.25 + 0.85 * max(0, fs2)),
                tw=-0.25 + 0.1 * s, ph=ph, jaw=0.25, ears=0.9, snarl=0.6)


def _idle(t):
    s = math.sin(t * math.tau)
    return dict(bob=0.6 * s, tilt=0.02 * s, hb=(0.28, 0.95), hf=(0.12, 0.85), fb=(-0.06, 0.12), ff=(0.1, 0.12),
                tw=0.12 * s, ph=t * math.tau, jaw=0.12 + 0.05 * s, ears=0.4, snarl=0.3, hy=0.3 * s)


def _keys(frames, n):
    return lambda t: frames[min(n - 1, int(t * n))]


BOZKURT_ANIMS = {
    'idle': (6, _idle),
    'run': (8, _gallop),
    'bite': (5, _keys([
        dict(bob=2.4, tilt=-0.14, hb=(0.55, 1.5), hf=(0.45, 1.4), fb=(0.45, 1.0), ff=(0.55, 1.1), tw=0.45, jaw=1.0, hy=1.8, ph=0.0, ears=1.0, snarl=1.0, stretch=-0.6),
        dict(bob=-1.6, tilt=0.0, hb=(-0.85, 0.3), hf=(-0.75, 0.4), fb=(1.05, 0.2), ff=(1.15, 0.3), tw=-0.3, jaw=1.0, hy=0.6, ph=1.0, ears=1.0, snarl=1.0, stretch=0.8),
        dict(bob=-2.2, tilt=0.06, hb=(-1.05, 0.2), hf=(-0.95, 0.3), fb=(1.25, 0.2), ff=(1.35, 0.3), tw=-0.5, jaw=0.0, hy=0.0, ph=2.0, ears=1.0, snarl=1.0, stretch=1.0),
        dict(bob=-1.0, tilt=0.04, hb=(-0.6, 0.4), hf=(-0.5, 0.5), fb=(0.9, 0.3), ff=(1.0, 0.3), tw=-0.4, jaw=0.1, hy=0.0, ph=3.0, ears=0.9, snarl=0.8, stretch=0.4),
        dict(bob=0.0, tilt=0.0, hb=(0.2, 0.9), hf=(0.1, 0.8), fb=(0.0, 0.2), ff=(0.1, 0.2), tw=0.0, jaw=0.2, hy=0.0, ph=4.0, ears=0.6, snarl=0.4, stretch=0.0)], 5)),
    'pounce': (4, _keys([
        dict(bob=3.8, tilt=-0.22, crouch=1.0, hb=(0.75, 1.75), hf=(0.65, 1.65), fb=(0.65, 1.35), ff=(0.75, 1.45), tw=0.55, jaw=0.45, hy=2.6, ears=1.0, snarl=0.8, stretch=-0.8),
        dict(bob=-2.2, tilt=-0.12, hb=(-1.15, 0.3), hf=(-1.05, 0.4), fb=(1.35, 0.2), ff=(1.45, 0.3), tw=-0.55, jaw=1.0, hy=0.0, ears=1.0, snarl=1.0, stretch=1.2),
        dict(bob=-2.7, tilt=0.02, hb=(-1.25, 0.2), hf=(-1.15, 0.3), fb=(1.45, 0.2), ff=(1.55, 0.3), tw=-0.65, jaw=1.0, hy=0.0, ears=1.0, snarl=1.0, stretch=1.3),
        dict(bob=0.6, tilt=0.12, hb=(0.3, 1.0), hf=(0.2, 0.9), fb=(0.4, 0.6), ff=(0.5, 0.7), tw=0.2, jaw=0.3, hy=0.5, ears=0.7, snarl=0.5, stretch=-0.3)], 4)),
    'howl': (4, lambda t: dict(bob=0.4, tilt=-0.28, hb=(0.45, 1.0), hf=(0.35, 0.9), fb=(0.2, 0.3), ff=(0.3, 0.3), tw=0.65,
                               howl=[0.45, 1.0, 1.0, 0.7][min(3, int(t * 4))], ph=t * math.tau, ears=0.2, snarl=0.0, jaw=0.0)),
    'hurt': (2, lambda t: dict(bob=1, tilt=0.2, hb=(0.3, 0.9), hf=(0.2, 0.8), fb=(-0.3, 0.3), ff=(-0.2, 0.2), tw=0.6, jaw=0.5, hy=-1, ears=0.3, snarl=0.5)),
}
