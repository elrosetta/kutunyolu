"""v44 Ata Kurganı / Silah Küpleri: yurdun girişindeki silah koleksiyonu duvarı (Dead Cells'in kavanoz odası gibi),
stil v2 "mürekkep-cel" süsleri (export_sus.py --kupler; sus_v2.json).

Pazırık kurganlarının karaçam kütüklü mezar odası: yarı gömülü toprak höyük, kütük duvar, raf tahtaları, oyma dikmeler,
koçboynuzlu baş tahtası (yazısı oyunda: KupGaleri.gd). Küpler ayrı sprite: arka (cam arkası + Kut sıvısı) ve ön (cam
parlaması, tunç kuşaklar, keçe kapak); silah ikisinin arasına oyunda çizilir (weapons_v2 atlası), böylece camın içinde
"yüzer". Mühür (sağlam / çatlak) ve parşömen etiketi küçük ek sprite'lar.

  kup_duvar          kurgan duvarı: 14 sütun x 4 raf (yerleşim sabitleri KupGaleri.gd ile aynı: SUTUN, ARALIK, RAF_Y)
  kup_a_arka / _on   omuzlu ruh kavanozu (kılıç, çift, kamçı)
  kup_b_arka / _on   geniş karınlı tunç kulplu küp (ağır, kalkan)
  kup_c_arka / _on   ince uzun tüp (mızrak, yay, atma, büyü)
  kup_muhur / kup_muhur_catlak   kırmızı balmumu tamga mühür / çatlamış, sönük mühür
  kup_parsomen       küpe bağlı dürülü parşömen (Demirci'de açılmayı bekleyen)
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from inkprop import (Prop, FELT_C, FELT_DK, RED, RED_D, GOLD, BRONZE, WOOD, WOOD_D, STONE, STONE_D, MOSS,
                     ROPE, KUT, KUT_GLOW, diamond, ram_motif, grass_tufts)

# ---- yerleşim (dünya birimi; köken duvarın sol alt köşesi, y yukarı eksi) — KupGaleri.gd ile aynı
SUTUN = 14
ARALIK = 26.5
X0 = 14.0                       # ilk sütunun sol kenarı
RAF_Y = [-144, -98, -52, -6]    # raf üst yüzleri (küplerin oturduğu çizgi), üstten alta
GEN = 400.0

LARCH = Ink('#5a3e30', '#2a1c22', '#7e5a42', '#1a1016', name='karaçam')
LARCH_D = Ink('#3e2c26', '#1c1218', '#5a4034', name='koyu karaçam')
EARTH = Ink('#4a3e3a', '#241e26', '#6a5a50', name='höyük toprağı')
GLASS_EDGE = (0.62, 0.86, 0.9)


def _log(cv, x0, x1, y, h, mat, z, rng):
    """Yatay kütük: hafif eğri, uçlarda halkalı kesit, damar çizgileri."""
    pts = [(x0, y, 0.0), (x1, y + rng.uniform(-0.6, 0.6), 0.0), (x1, y + h, 0.0), (x0, y + h + rng.uniform(-0.5, 0.5), 0.0)]
    det = []
    for _ in range(int((x1 - x0) / 22)):
        sx = rng.uniform(x0 + 4, x1 - 20)
        sy = y + rng.uniform(2, h - 2)
        det.append(('ink', [(sx, sy), (sx + rng.uniform(8, 18), sy + rng.uniform(-0.8, 0.8))], 0.6, (0.4, 0.6)))
    cv.shape(cv.blob(pts), mat, z=z, sd=h * 0.45, hi=0.6, details=det, soft=0.3)


def duvar():
    P = Prop(GEN + 16, 236, 8, 222)
    cv = P.cv
    rng = np.random.default_rng(44)
    # --- höyük: yarı gömülü toprak tümsek, otlu sırt
    mound = cv.blob([(-8, 6, 0.0), (-8, -150), (40, -196), (130, -214), (200, -218), (270, -214), (360, -196),
                     (GEN + 8, -150), (GEN + 8, 6, 0.0)])
    det = []
    for _ in range(26):
        x, y = rng.uniform(0, GEN), rng.uniform(-205, -150)
        det.append(('col', cv.ellipse((x, y), rng.uniform(4, 10), rng.uniform(1.5, 3)), MOSS.shadow))
    for _ in range(14):
        x, y = rng.uniform(10, GEN - 10), rng.uniform(-200, -160)
        det.append(('col', cv.ellipse((x, y), rng.uniform(2.5, 5), rng.uniform(2, 3.5)), STONE_D.base))
    cv.shape(mound, EARTH, z=-3.0, sd=10.0, hi=1.2, details=det, hatch=0.25, bounce=0.2)
    for k in range(9):
        a = k / 8
        x = 10 + a * (GEN - 20)
        y = -150 - 64 * math.sin(math.pi * (0.1 + 0.8 * a)) + 6
        grass_tufts(cv, x - 22, x + 22, y, 10, -2.9, 300 + k, hmin=3.0, hmax=8.5)
    # --- kütük duvar (mezar odasının iç yüzü): koyu, küpler öne çıksın
    wall = cv.blob([(6, -2, 0.0), (6, -186, 0.0), (GEN - 6, -186, 0.0), (GEN - 6, -2, 0.0)])
    cv.fill(wall, (0.1, 0.08, 0.1), z=-2.5)
    y = -186.0
    i = 0
    while y < -2:
        h = min(11.5, -2 - y)
        _log(cv, 6, GEN - 6, y, h, LARCH_D.darker(0.62) if i % 2 else LARCH.darker(0.5), -2.4, rng)
        y += h
        i += 1
    # kütük duvarın üstüne düşen raf gölgeleri ve tavan karanlığı (küplerin arkası derin)
    cv.fill(cv.blob([(6, -186, 0.0), (GEN - 6, -186, 0.0), (GEN - 6, -170, 0.0), (6, -170, 0.0)]), (0.04, 0.03, 0.06), z=-2.3, alpha=0.55)
    for ry in RAF_Y:
        cv.fill(cv.blob([(8, ry + 4, 0.0), (GEN - 8, ry + 4, 0.0), (GEN - 8, ry + 12, 0.0), (8, ry + 12, 0.0)]), (0.03, 0.02, 0.05), z=-2.2, alpha=0.45)
    # keçe kuşak: baş tahtasının altında kızıl keçe, koçboynuzu motifleri
    band = cv.blob([(8, -170, 0.0), (GEN - 8, -170, 0.0), (GEN - 8, -158, 0.0), (8, -158, 0.0)])
    bdet = [('col', cv.blob([(8, -161, 0.0), (GEN - 8, -161, 0.0), (GEN - 8, -159.6, 0.0), (8, -159.6, 0.0)]), GOLD.shadow)]
    for k in range(17):
        x = 20 + k * 22.5
        bdet.append(('col', cv.blob(diamond(x, -165, 3.6, 3.0)), GOLD.base))
        bdet.append(('col', cv.blob(diamond(x, -165, 1.5, 1.3)), RED_D.base))
    cv.shape(band, RED_D, z=-2.0, sd=3.0, hi=0.5, details=bdet)
    for k in range(34):
        x = 10 + k * 11.5
        cv.stroke([(x, -158), (x + 0.3, -155.5)], 0.8, z=-1.95, col=GOLD.base, taper=(0.1, 0.7))
    # --- raflar: kalın karaçam tahta, oyma destekler
    for ri, ry in enumerate(RAF_Y):
        plank = cv.blob([(4, ry - 1.2, 0.0), (GEN - 4, ry - 1.2, 0.0), (GEN - 4, ry + 5.0, 0.0), (4, ry + 5.0, 0.0)])
        det = [('col', cv.blob([(4, ry - 1.2, 0.0), (GEN - 4, ry - 1.2, 0.0), (GEN - 4, ry + 0.6, 0.0), (4, ry + 0.6, 0.0)]), WOOD.hi),
               ('stroke', [(6, ry + 1.2), (GEN - 6, ry + 1.2)], 0.7, WOOD.shadow, (0.05, 0.05))]
        for _ in range(10):
            sx = rng.uniform(8, GEN - 30)
            det.append(('ink', [(sx, ry + 2.6), (sx + rng.uniform(10, 24), ry + 2.4)], 0.5, (0.4, 0.6)))
        cv.shape(plank, WOOD, z=-1.0 + ri * 0.01, sd=2.6, hi=0.5, details=det, cast=2.0)
        if ri < 3:
            for bx in (20, 106, 200, 294, 380):
                br = cv.blob([(bx - 3.5, ry + 4.5, 0.0), (bx + 3.5, ry + 4.5, 0.0), (bx + 1.5, ry + 12), (bx, ry + 14, 0.0), (bx - 1.5, ry + 12)])
                cv.shape(br, LARCH, z=-1.05, sd=1.2, hi=0.3, details=[('ink', [(bx - 1.6, ry + 7), (bx + 1.6, ry + 7)], 0.6)])
    # taban: taş seki (alt raf ona oturur)
    for k in range(12):
        x = 4 + k * (GEN - 8) / 12
        st = cv.blob([(x + 0.6, 6, 0.0), (x + 0.4, -1.5), (x + (GEN - 8) / 12 - 0.6, -1.4), (x + (GEN - 8) / 12 - 0.4, 6, 0.0)])
        cv.shape(st, STONE if k % 2 else STONE_D, z=-1.2, sd=2.0, hi=0.4)
    # --- dikmeler: iki yanda oyma karaçam direk, tepede koçboynuzu başlık
    for px, flip in ((6, 1.0), (GEN - 6, -1.0)):
        post = cv.blob([(px - 6, 6, 0.0), (px - 6, -190, 0.0), (px + 6, -190, 0.0), (px + 6, 6, 0.0)])
        det = []
        for k in range(7):
            yy = -20 - k * 25
            det.append(('col', cv.blob(diamond(px, yy, 3.0, 4.2)), RED_D.base))
            det.append(('ink', [(px - 5, yy + 8), (px + 5, yy + 8)], 0.7))
        det.append(('stroke', [(px - 3.5, 2), (px - 3.5, -186)], 1.0, LARCH.hi, (0.1, 0.1)))
        cv.shape(post, LARCH, z=0.5, sd=4.0, hi=0.8, details=det, bounce=0.3)
        cap = cv.blob([(px - 8, -190, 0.0), (px - 9, -196, 0.0), (px + 9, -196, 0.0), (px + 8, -190, 0.0)])
        cv.shape(cap, LARCH_D, z=0.55, sd=1.5, hi=0.4)
        ram_motif(cv, px, -203, 6.5, 1.8, 0.6, col=GOLD.base)
    # üst kiriş (lento)
    lint = cv.blob([(0, -186, 0.0), (GEN, -186, 0.0), (GEN, -178, 0.0), (0, -178, 0.0)])
    det = [('stroke', [(2, -185), (GEN - 2, -185)], 1.0, LARCH.hi, (0.05, 0.05))]
    for k in range(40):
        x = 6 + k * 9.8
        det.append(('ink', [(x, -181), (x + 4, -183), (x + 8, -181)], 0.6, (0.2, 0.2)))
    cv.shape(lint, LARCH, z=0.4, sd=2.6, hi=0.6, details=det, cast=1.5)
    # --- baş tahtası: yazı (oyunda) için boş, altın kenarlı, iki ucunda koçboynuzu
    cx = GEN / 2
    def _plq(m):
        return cv.poly([(cx - 92 + m, -178 - m * 0.6), (cx - 99 + m * 1.2, -192), (cx - 92 + m, -206 + m * 0.6),
                        (cx + 92 - m, -206 + m * 0.6), (cx + 99 - m * 1.2, -192), (cx + 92 - m, -178 - m * 0.6)])
    cv.shape(_plq(0), LARCH_D, z=1.0, sd=3.0, hi=0.6, cast=1.6)
    cv.shape(_plq(4), GOLD, z=1.05, sd=0.8, hi=0.4, ol=0.6)
    cv.shape(_plq(5.6), Ink('#140e12', '#08060a', '#2a2026'), z=1.1, sd=1.5, ol=0.5, flat=True)
    for f in (-1, 1):
        ram_motif(cv, cx + f * 108, -190, 6.0, 1.6, 1.2, col=GOLD.base)
        cv.shape(cv.blob(diamond(cx + f * 96, -192, 2.6, 3.4)), Ink('#2fb2a8', '#17606a', '#8cf0e0'), z=1.2, sd=0.6, ol=0.7,
                 glow=(0.25, 0.8, 0.8))
    return P.done(rim=0.25)


# ------------------------------------------------------------------ küpler
def _body_a():
    return [(-8.5, 0, 0.0), (-10.5, -6), (-11, -18), (-9.5, -26), (-5.5, -30.5, 0.0), (5.5, -30.5, 0.0), (9.5, -26), (11, -18), (10.5, -6), (8.5, 0, 0.0)]


def _body_b():
    return [(-8, 0, 0.0), (-12.5, -6), (-13.5, -15), (-12, -24), (-7.5, -29, 0.0), (7.5, -29, 0.0), (12, -24), (13.5, -15), (12.5, -6), (8, 0, 0.0)]


def _body_c():
    return [(-7, 0, 0.0), (-7.4, -12), (-7.2, -28), (-6.4, -32.5, 0.0), (6.4, -32.5, 0.0), (7.2, -28), (7.4, -12), (7, 0, 0.0)]


BODIES = {'a': (_body_a, -30.5, 6.0), 'b': (_body_b, -29, 7.6), 'c': (_body_c, -32.5, 6.4)}


def kup_arka(kind):
    """Cam arkası: koyu yeşilimsi cam iç yüzü + alt yarıda Kut sıvısı (oyunda duruma göre renklenir)."""
    fn, top, _ = BODIES[kind]
    P = Prop(32, 40, 16, 37)
    cv = P.cv
    body = cv.blob(fn())
    cv.fill(body, (0.1, 0.2, 0.22), z=0.0, alpha=0.7)
    # iç yüzün eğriliği: kenarlarda koyu, ortada hafif aydınlık
    cv.fill(ik.isect(body, cv.ellipse((0, top * 0.55), 7, -top * 0.42)), (0.16, 0.3, 0.3), z=0.1, alpha=0.5)
    # sıvı: alt %40, üst yüzü elips
    lv = top * 0.36
    liq = ik.isect(body, cv.blob([(-16, lv, 0.0), (16, lv, 0.0), (16, 2, 0.0), (-16, 2, 0.0)]))
    cv.fill(liq, (0.22, 0.6, 0.6), z=0.2, alpha=0.38, glow=(0.08, 0.3, 0.3))
    cv.fill(ik.isect(body, cv.ellipse((0, lv), 14, 1.2)), (0.6, 1.0, 0.95), z=0.25, alpha=0.45, glow=(0.2, 0.6, 0.6))
    # dipte kabarcıklar
    rng = np.random.default_rng(len(kind) * 7 + ord(kind))
    for _ in range(5):
        q = (rng.uniform(-6, 6), rng.uniform(lv + 1, -2))
        cv.stroke([(q[0] - 0.4, q[1]), (q[0] + 0.4, q[1])], 0.9, z=0.3, col=(0.8, 1.0, 1.0), alpha=0.6, taper=(0.1, 0.1))
    return P.done(outer=0.0, rim=0.0, grain=0.0)


def kup_on(kind):
    """Cam önü: kontur, parlama şeritleri, tunç dip halkası ve boyun kuşağı, keçe kapak + kıl ip, (b) kulplar."""
    fn, top, nw = BODIES[kind]
    P = Prop(34, 44, 17, 39)
    cv = P.cv
    pts = fn()
    body = cv.blob(pts)
    # camın ön yüzündeki çok hafif buğu (kenarlara doğru)
    cv.fill(ik.diff(body, cv.blob([(x * 0.84, y * 0.94 - 1.0) + ((p[2],) if len(p) > 2 else ()) for p in pts for x, y in [p[:2]]])),
            GLASS_EDGE, z=0.0, alpha=0.18)
    # mürekkep cam konturu
    outline = [(x, y) for x, y, *_ in pts]
    cv.stroke(outline + [outline[0]], 1.3, z=0.1, col=INK, taper=(0.05, 0.05))
    # parlamalar (ışık sol üstten)
    hx = -nw - (2.0 if kind != 'c' else 0.5)
    cv.stroke([(hx, top + 6), (hx - 1.2, top * 0.55), (hx - 0.4, -6)], 1.6, z=0.2, col=(0.92, 1.0, 1.0), alpha=0.75, taper=(0.5, 0.6))
    cv.stroke([(hx + 2.6, top + 8), (hx + 2.2, top * 0.6)], 0.8, z=0.2, col=(0.92, 1.0, 1.0), alpha=0.5, taper=(0.5, 0.6))
    cv.stroke([(nw + 2.5, top * 0.7), (nw + 3.2, -8)], 0.7, z=0.2, col=(0.7, 0.95, 1.0), alpha=0.35, taper=(0.5, 0.5))
    # tunç dip halkası
    bw = abs(pts[0][0]) + 1.2
    cv.shape(cv.blob([(-bw, 1.2, 0.0), (-bw - 0.6, -2.4), (bw + 0.6, -2.4), (bw, 1.2, 0.0)]), BRONZE, z=0.3, sd=0.8, hi=0.3, ol=0.8)
    # boyun: tunç kuşak
    cv.shape(cv.blob([(-nw - 0.6, top + 1.2, 0.0), (-nw - 0.6, top - 1.8, 0.0), (nw + 0.6, top - 1.8, 0.0), (nw + 0.6, top + 1.2, 0.0)]),
             BRONZE, z=0.4, sd=0.8, hi=0.3, ol=0.8, details=[('col', cv.blob(diamond(0, top - 0.3, 1.2, 1.0)), GOLD.hi)])
    # keçe kapak: kubbe + bağ ipi + tepede düğüm
    if kind == 'b':
        lid = cv.blob([(-nw - 1.8, top - 1.6, 0.0), (-nw, top - 4.6), (0, top - 6.2), (nw, top - 4.6), (nw + 1.8, top - 1.6, 0.0)])
        cv.shape(lid, BRONZE, z=0.5, sd=1.2, hi=0.4, ol=0.9)
        cv.shape(cv.ellipse((0, top - 6.8), 1.6, 1.2), GOLD, z=0.55, sd=0.4, ol=0.7)
        for f in (-1, 1):   # tunç halka kulplar
            cv.stroke([(f * 12.4, -22), (f * 15.5, -20), (f * 15.5, -15), (f * 13.3, -13)], 1.5, z=0.35, col=BRONZE.base, taper=(0.1, 0.1))
            cv.stroke([(f * 12.4, -22), (f * 15.5, -20), (f * 15.5, -15), (f * 13.3, -13)], 0.5, z=0.36, col=BRONZE.hi, taper=(0.1, 0.1))
    else:
        lid = cv.blob([(-nw - 1.6, top - 1.4, 0.0), (-nw - 0.4, top - 5.0), (0, top - 6.6), (nw + 0.4, top - 5.0), (nw + 1.6, top - 1.4, 0.0)])
        cv.shape(lid, FELT_C if kind == 'a' else RED, z=0.5, sd=1.2, hi=0.3, ol=0.9,
                 details=[('ink', [(-nw * 0.6, top - 2.4), (-nw * 0.2, top - 5.4)], 0.5), ('ink', [(nw * 0.5, top - 2.6), (nw * 0.2, top - 5.2)], 0.5)])
        cv.stroke([(-nw - 1.2, top - 2.0), (0, top - 2.6), (nw + 1.2, top - 2.0)], 0.9, z=0.55, col=ROPE.base, taper=(0.1, 0.1))
        cv.shape(cv.ellipse((0, top - 7.0), 1.4, 1.1), ROPE, z=0.56, sd=0.4, ol=0.7)
        cv.stroke([(nw + 1.0, top - 2.0), (nw + 2.6, top + 1.8), (nw + 2.2, top + 4.0)], 0.7, z=0.57, col=ROPE.base, taper=(0.1, 0.6))
    return P.done(outer=0.6, rim=0.0, grain=0.0)


def muhur(catlak=False):
    """Küpün boynundan sarkan balmumu tamga mühür. Çatlak: sönük, ortasından yarılmış (kilitli küp)."""
    P = Prop(12, 14, 6, 3)
    cv = P.cv
    cv.stroke([(0, -2.5), (-0.4, 2.0)], 0.8, z=0.0, col=ROPE.base if not catlak else ROPE.shadow, taper=(0.1, 0.1))
    wax = Ink('#a82a2a', '#561428', '#e05a48') if not catlak else Ink('#5a3a3e', '#2a1a22', '#7a5a5a')
    disc = cv.blob([(-3.6, 5.5), (-2.8, 3.0), (0, 2.2), (2.8, 3.0), (3.8, 5.6), (3.0, 8.4), (0, 9.4), (-3.0, 8.4)])
    cv.shape(disc, wax, z=0.1, sd=1.2, hi=0.4, ol=0.9)
    gold = GOLD.base if not catlak else (0.42, 0.36, 0.3)
    # tamga (Kayı benzeri ok-yay işareti)
    cv.stroke([(-1.6, 4.4), (0, 6.2), (1.6, 4.4)], 0.8, z=0.2, col=gold, taper=(0.1, 0.1))
    cv.stroke([(0, 6.2), (0, 8.2)], 0.8, z=0.2, col=gold, taper=(0.1, 0.1))
    if catlak:
        cv.stroke([(-1.0, 2.4), (0.6, 4.6), (-0.4, 6.4), (1.0, 9.2)], 0.9, z=0.3, col=INK, taper=(0.1, 0.1))
        cv.fill(cv.blob([(0.6, 4.6, 0.0), (4.2, 5.4, 0.0), (3.4, 8.6, 0.0), (1.0, 9.2, 0.0), (-0.4, 6.4, 0.0)]), (0.0, 0.0, 0.0), z=0.25, alpha=0.25)
    return P.done(outer=0.8, rim=0.0)


def parsomen():
    """Küpe kıl iple bağlı dürülü parşömen (Demirci Kam Kuzgun'da açılmayı bekleyen silah)."""
    P = Prop(16, 10, 8, 5)
    cv = P.cv
    PARCH = Ink('#e2d0a2', '#9a8060', '#fff2cc', name='parşömen')
    roll = cv.capsule((-5.5, 0), (5.5, 0), 2.6, 2.6)
    cv.shape(roll, PARCH, z=0.1, sd=1.4, hi=0.4, ol=0.9, details=[('ink', [(-4, -0.6), (3, -0.8)], 0.5), ('ink', [(-3, 1.0), (4, 0.8)], 0.5)])
    for x in (-5.5, 5.5):
        cv.shape(cv.ellipse((x, 0), 1.2, 2.6), PARCH.darker(0.8), z=0.15, sd=0.4, ol=0.7)
    cv.stroke([(-0.6, -2.8), (-0.6, 2.8)], 1.2, z=0.2, col=RED.base, taper=(0.05, 0.05))
    cv.stroke([(-0.6, 2.6), (-1.6, 4.2)], 0.7, z=0.2, col=RED.base, taper=(0.05, 0.6))
    cv.stroke([(-0.6, 2.6), (0.6, 4.4)], 0.7, z=0.2, col=RED.base, taper=(0.05, 0.6))
    return P.done(outer=0.8, rim=0.0)


ALL = {
    'kup_duvar': duvar,
    'kup_a_arka': lambda: kup_arka('a'), 'kup_a_on': lambda: kup_on('a'),
    'kup_b_arka': lambda: kup_arka('b'), 'kup_b_on': lambda: kup_on('b'),
    'kup_c_arka': lambda: kup_arka('c'), 'kup_c_on': lambda: kup_on('c'),
    'kup_muhur': lambda: muhur(False), 'kup_muhur_catlak': lambda: muhur(True),
    'kup_parsomen': parsomen,
}


if __name__ == '__main__':
    # önizleme: python kup_ink.py [ad...] cikti.png (koyu zemin üstünde arka + ön üst üste)
    import sys
    from PIL import Image
    names = [a for a in sys.argv[1:] if a in ALL] or list(ALL)
    if '--kompozit' in sys.argv:
        ALL2 = {}
        for k in 'abc':
            def mk(k=k):
                b, bg_, ob = kup_arka(k)
                f, fg, of = kup_on(k)
                H_, W_ = f.shape[:2]
                out_ = np.zeros_like(f)
                gl = np.zeros_like(f)
                dx, dy = int(of[0] - ob[0]), int(of[1] - ob[1])
                out_[dy:dy + b.shape[0], dx:dx + b.shape[1]] = b
                gl[dy:dy + b.shape[0], dx:dx + b.shape[1]] = bg_
                a = f[..., 3:4]
                out_[..., :3] = out_[..., :3] * out_[..., 3:4] * (1 - a) + f[..., :3] * a
                out_[..., 3:4] = np.maximum(out_[..., 3:4], a)
                out_[..., :3] /= np.maximum(out_[..., 3:4], 1e-4)
                return out_, gl, of
            ALL2['k' + k] = mk
        ALL.update(ALL2)
        names = list(ALL2)
    out = []
    for n in names:
        rgba, glow, org = ALL[n]()
        out.append((n, rgba, glow))
    sc = 2
    W = sum(r.shape[1] for _, r, _ in out) + 20 * len(out) + 20
    H = max(r.shape[0] for _, r, _ in out) + 40
    bg = np.zeros((H, W, 3), np.float32)
    bg[:] = (0.09, 0.1, 0.16)
    x = 20
    for n, r, g in out:
        h, w = r.shape[:2]
        y = H - 20 - h
        a = r[..., 3:4]
        bg[y:y + h, x:x + w] = bg[y:y + h, x:x + w] * (1 - a) + r[..., :3] * a
        bg[y:y + h, x:x + w] += g[..., :3] * g[..., 3:4] * 0.8
        x += w + 20
    Image.fromarray((np.clip(bg, 0, 1) * 255).astype(np.uint8)).save(sys.argv[-1] if sys.argv[-1].endswith('.png') else 'kup_ink_on.png')
