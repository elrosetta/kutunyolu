"""Stil v2 "mürekkep-cel" ortak dünya nesneleri (biyomdan bağımsız):

  DECOR (assets/decor/<ad>_v2.png, sus_v2.json; Level._decor_v2 / SusV2.gd):
    sunak         Tengri sunağı (lütuf): göğün dört yönü oyulu taş seki, altın ateş tası, iki küçük tuğ
    kut_kapi      Kut Kapısı: kayın kökleri sarılı taş kemer, ışıyan runlar, çaputlar (önü / arkası ayrı)
    kut_kapi_girdap  kapının içinde dönen kut girdabı (yalnızca ışıma, iki kat ters döner)
    totem / totem_tuy  Davul Totemi: oyma direk + kam davulu, tepede üç renk tüy (ayrı, salınır)
    ruh_tasi      gizli odanın ruh taşı kapağı (mor damarlı taş, ışıyan mühür runları)
    bulut_1..4    Ülgen'in altın bulut basamakları
  ATLAS (assets/fx/ink/sus_v2.png + _e + sus_v2.json): toplanabilirler ve mermiler
  HAZARDS (assets/tiles/hazards_v2.png + _e): diken / zehir / lav / buz, iki kare (karo 24 dünya birimi)

Doku yoğunluğu inkprop.TEX = 4 doku pikseli / dünya birimi; oyunda doğrusal süzgeç + mipmap.
"""
import json
import math
import os

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from inkprop import (Prop, TEX, FELT, FELT_C, RED, BLUE, SKYB, TURQ, GOLD, BRONZE, IRON, STEEL, WOOD, WOOD_D, WOOD_R, STONE,
                     STONE_W, STONE_D, MOSS, LEATHER, HAIR_K, HAIR_W, ROPE, BARK_W, LEAF, CLOTH_COLS, KUT, KUT_GLOW,
                     flame, ram_motif, diamond, tassel, grass_tufts)

AMETHYST = Ink('#7a54b0', '#3a2264', '#c8a8f0', '#20123a', name='ruh taşı moru')
SLATE = Ink('#4c4a62', '#24223a', '#7c7a98', '#14121e', name='kara taş')
CLOUD = Ink('#fbe7bc', '#d49a5c', '#fffaf0', '#a8643c', name='altın bulut')


# ------------------------------------------------------------------ süsler
def sunak():
    """Tengri sunağı: üç basamaklı taş seki, ortada dört yön haçlı (Tengri tamgası) oyma taş, üstünde altın ateş tası;
    iki yanında çaputlu küçük tuğ direkleri."""
    P = Prop(76, 84, 38, 80)
    cv = P.cv
    for k, (w, h) in enumerate(((34, 5), (28, 5), (22, 4))):
        y0 = -k * 5
        cv.shape(cv.blob([(-w, y0 + 0.5, 0.0), (-w, y0 - h, 0.0), (w, y0 - h, 0.0), (w, y0 + 0.5, 0.0)]), STONE_W if k != 1 else STONE, z=k * 0.1,
                 sd=2.4, hi=0.5, details=[('ink', [(-w + 3 + j * 9, y0 - h + 0.5), (-w + 3 + j * 9, y0)], 0.5) for j in range(int(w * 2 / 9))])
    stele = cv.blob([(-11, -14, 0.0), (-12, -40), (-9, -46, 0.0), (9, -46, 0.0), (12, -40), (11, -14, 0.0)])
    det = [('stroke', [(0, -42), (0, -18)], 1.6, INK, (0.1, 0.1)), ('stroke', [(-8, -30), (8, -30)], 1.6, INK, (0.1, 0.1)),
           ('ink', [(-5, -38), (-5, -35)], 0.8), ('ink', [(5, -38), (5, -35)], 0.8), ('ink', [(-5, -24), (-5, -21)], 0.8), ('ink', [(5, -24), (5, -21)], 0.8)]
    for _ in range(4):
        det.append(('col', cv.ellipse((np.random.uniform(-9, 9), np.random.uniform(-40, -16)), 1.8, 1.1), MOSS.base))
    cv.shape(stele, STONE_W, z=0.5, sd=4.5, hi=0.6, details=det, hatch=0.3)
    for (a, b) in (((0, -42), (0, -18)), ((-8, -30), (8, -30))):
        cv.stroke([a, b], 1.0, z=0.55, col=GOLD.hi, glow=(0.7, 0.45, 0.1), alpha=0.7, taper=(0.15, 0.15))
    bowl = cv.blob([(-12, -52, 0.0), (12, -52, 0.0), (8, -47), (0, -45.5), (-8, -47)])
    cv.shape(bowl, GOLD, z=0.6, sd=2.2, hi=0.5, details=[('stroke', [(-10, -51), (10, -51)], 1.0, GOLD.hi, (0.1, 0.1))])
    flame(cv, 0, -52, 22, 16, 0.7, seed=3)
    for f in (-1, 1):
        x = f * 28
        cv.shape(cv.capsule((x, -10), (x, -66), 1.2, 1.0), WOOD_D, z=-0.5, sd=0.6, hi=0.3)
        cv.shape(cv.blob([(x - 3, -66, 0.0), (x, -75, 0.0), (x + 3, -66, 0.0), (x, -64)]), GOLD, z=-0.45, sd=0.8, hi=0.3)
        tassel(cv, x, -63, 10, 5, HAIR_W if f < 0 else HAIR_K, -0.4, strands=4)
        for j, col in enumerate(CLOTH_COLS[:3]):
            y = -54 + j * 5
            cv.shape(cv.blob([(x, y, 0.0), (x - f * 7, y + 2), (x - f * 9, y + 9, 0.0), (x - f * 4, y + 4.5), (x, y + 2.6, 0.0)]), Ink(col), z=-0.4 + j * 0.01,
                     sd=0.8, ol=0.6)
    grass_tufts(cv, -36, 36, 0, 28, 1.0, 5, hmax=7)
    return P.done()


def kut_kapi(part='on'):
    """Kut Kapısı: iki yanda kayın kökü sarılı taş sütun, üstte runlu alınlık ve koçboynuzu, sarkan çaputlar.
    part 'on' = kemer (portalın önünde), 'arka' = kemerin iç yüzü ve karanlık eşik (portalın arkasında)."""
    P = Prop(98, 104, 49, 100)
    cv = P.cv
    rng = np.random.default_rng(7)
    if part == 'arka':
        hole = cv.blob([(-22, 0.5, 0.0), (-22, -58), (-14, -72), (0, -76), (14, -72), (22, -58), (22, 0.5, 0.0)])
        cv.shape(hole, Ink('#0c1420', '#060a12', '#18283a'), z=0, noshadow=True, ol=0.0)
        cv.fill(hole, (0.15, 0.6, 0.62), z=0.1, alpha=0.35, glow=(0.08, 0.32, 0.34))
        return P.done(outer=0.0, rim=0.0)
    for f in (-1, 1):
        x = f * 30
        col = cv.blob([(x - 9, 0.5, 0.0), (x - 9.5, -40), (x - 9, -74, 0.0), (x + 9, -74, 0.0), (x + 9.5, -40), (x + 9, 0.5, 0.0)])
        det = []
        for yy in np.arange(-70, -2, 11):
            det.append(('ink', [(x - 9, yy + rng.uniform(-1, 1)), (x + 9, yy + rng.uniform(-1, 1))], 0.6))
            det.append(('ink', [(x + rng.uniform(-4, 4), yy), (x + rng.uniform(-4, 4), yy + 11)], 0.5))
        for _ in range(5):
            det.append(('col', cv.ellipse((x + rng.uniform(-7, 7), -rng.uniform(4, 70)), rng.uniform(1.5, 3), rng.uniform(1, 2)), MOSS.base))
        det.append(('shade', cv.blob([(x + 3, 0.5, 0.0), (x + 3, -74, 0.0), (x + 9.5, -74, 0.0), (x + 9.5, 0.5, 0.0)])))
        cv.shape(col, STONE, z=0.2, noshadow=True, hi=0.5, details=det, hatch=0.3)
        # runlar (ışır)
        for k, yy in enumerate((-62, -50, -38, -26)):
            gl = [(x - 2.4, yy - 3), (x, yy + 3), (x + 2.4, yy - 3)] if k % 2 == 0 else [(x - 2, yy - 3.5), (x - 2, yy + 3.5), (x + 2.4, yy)]
            cv.stroke(gl, 1.3, z=0.3, col=KUT, glow=KUT_GLOW, taper=(0.1, 0.1))
        # kayın kökleri: sütunu saran ak kabuklu kökler
        for k in range(3):
            y0 = -rng.uniform(10, 60)
            pts = [(x - f * 12, y0 + 18), (x - f * 4, y0 + 8), (x + f * 6, y0), (x + f * 11, y0 - 8)]
            cv.shape(ik.taper_path([cv.W(p) for p in pts], cv.u(4.4), prof=lambda u: 0.5 + 0.5 * math.sin(math.pi * u)), BARK_W.darker(0.86), z=0.4 + k * 0.01,
                     sd=1.0, ol=0.8, details=[('ink', [pts[1], (pts[1][0] + 1.5, pts[1][1] - 0.3)], 0.9)])
        cv.shape(ik.taper_path([cv.W(p) for p in [(x - f * 6, 1), (x + f * 2, -6), (x + f * 14, -2), (x + f * 22, 1)]], cv.u(5.0), (0.2, 0.8)), BARK_W, z=0.45, sd=1.4, ol=0.8)
    # alınlık
    lint = cv.blob([(-44, -72, 0.0), (44, -72, 0.0), (42, -82, 0.0), (-42, -82, 0.0)])
    det = [('ink', [(-44, -77), (44, -77)], 0.6)]
    cv.shape(lint, STONE_W, z=0.6, sd=3.0, hi=0.6, details=det)
    for k in range(7):
        x = -30 + k * 10
        gl = [(x - 2.4, -78.5), (x, -74.5), (x + 2.4, -78.5)] if k % 2 else [(x - 2, -80), (x + 2, -80), (x, -75)]
        cv.stroke(gl, 1.2, z=0.65, col=KUT, glow=KUT_GLOW, taper=(0.1, 0.1))
    # koçboynuzu tepelik
    ram_motif(cv, 0, -88, 10, 3.6, 0.68, col=INK)
    ram_motif(cv, 0, -88, 10, 2.2, 0.7, col=GOLD.base)
    cv.shape(cv.blob(diamond(0, -93, 3.0, 4.0)), TURQ, z=0.75, sd=0.6, ol=0.7, glow=(0.3, 0.95, 0.9))
    # sarkan çaputlar
    for k in range(5):
        x = -36 + k * 18
        col = CLOTH_COLS[k % len(CLOTH_COLS)]
        ln = rng.uniform(10, 16)
        cv.shape(cv.blob([(x - 2, -72, 0.0), (x + 2, -72, 0.0), (x + 2.6, -72 + ln * 0.6), (x + 1, -72 + ln, 0.0), (x - 1.6, -72 + ln * 0.7)]), Ink(col),
                 z=0.8, sd=0.8, ol=0.6)
    grass_tufts(cv, -44, 44, 0, 34, 1.0, 9, hmax=8)
    return P.done()


def kut_kapi_girdap():
    """Dönen kut girdabı: firuze sarmal fırça darbeleri, merkezde beyaz çekirdek (yalnızca ışıma dokusu olarak kullanılır)."""
    P = Prop(52, 52, 26, 26)
    cv = P.cv
    rng = np.random.default_rng(11)
    for k in range(9):
        a0 = k * 2 * math.pi / 9
        pts = []
        for i in range(14):
            t = i / 13
            a = a0 + t * 2.4
            r = 23 * (1 - t) + 2
            pts.append((math.cos(a) * r, math.sin(a) * r * 1.0))
        c = (0.45 + 0.3 * rng.random(), 1.0, 0.92)
        cv.fill(ik.taper_path([cv.W(p) for p in pts], cv.px(rng.uniform(4, 9)), (0.5, 0.2)), c, z=k * 0.01, alpha=0.75)
    cv.fill(cv.ellipse((0, 0), 6, 6), (0.85, 1.0, 1.0), z=1, alpha=0.9)
    rgba, glow, org = P.done(outer=0.0, rim=0.0, grain=0.0)
    return rgba, glow, org


def totem():
    """Davul Totemi gövdesi: oyma direk (kurt başı), üstünde kam davulu (gerili deri, kızıl tamgalar, tunç kasnak)."""
    P = Prop(34, 54, 17, 52)
    cv = P.cv
    cv.shape(cv.blob([(-3.2, 0.5, 0.0), (-3.4, -28, 0.0), (3.4, -28, 0.0), (3.2, 0.5, 0.0)]), WOOD, z=0, sd=1.6, hi=0.4,
             details=[('ink', [(-3, -8), (3, -9)], 0.7), ('ink', [(-3, -18), (3, -19)], 0.7),
                      ('col', cv.blob(diamond(0, -13.5, 1.6, 2.2)), RED.base)])
    cv.shape(cv.blob([(-5, 0.5, 0.0), (-4, -3), (4, -3), (5, 0.5, 0.0)]), STONE, z=0.1, sd=1.0, ol=0.7)
    # davul: yan görünüş (elips yüz + gövde)
    body = cv.blob([(-11, -27, 0.0), (-11.5, -32), (-11, -38, 0.0), (11, -38, 0.0), (11.5, -32), (11, -27, 0.0)])
    det = [('stroke', [(-10, -33), (-4, -31), (4, -33), (10, -31)], 1.2, RED.base, (0.1, 0.1))]
    for x in (-7, 0, 7):
        det.append(('ink', [(x, -37), (x + 1, -28)], 0.6))
    cv.shape(body, LEATHER, z=0.5, sd=3.0, hi=0.5, details=det)
    for y in (-38, -27):
        cv.shape(cv.ellipse((0, y), 11.6, 1.6), BRONZE, z=0.6 + (0.1 if y > -30 else 0), sd=0.6, hi=0.3)
    face = cv.ellipse((0, -38.5), 10.6, 2.6)
    cv.shape(face, Ink('#d8c09a', '#8a7058', '#f4e4c4'), z=0.55, sd=0.8, ol=0.7,
             details=[('ink', [(-5, -38.5), (5, -38.5)], 0.7), ('ink', [(0, -40.4), (0, -36.6)], 0.7)])
    return P.done()


def totem_tuy():
    """Totemin tepesindeki üç tüy (kızıl / ak / gök): ayrı doku, oyunda salınır. Köken tüylerin dibi."""
    P = Prop(20, 20, 10, 18)
    cv = P.cv
    for k, (col, a) in enumerate(((RED, -0.35), (FELT, 0.0), (SKYB, 0.35))):
        tip = (math.sin(a) * 15, -math.cos(a) * 15)
        cv.shape(cv.blob([(math.sin(a) * 1 - 1, 0), (tip[0] * 0.5 - 2.4 * math.cos(a), tip[1] * 0.5), (tip[0], tip[1], 0.0),
                          (tip[0] * 0.5 + 2.4 * math.cos(a), tip[1] * 0.5), (math.sin(a) * 1 + 1, 0)]), col, z=k * 0.1, sd=1.2, ol=0.7,
                 details=[('ink', [(0, 0), (tip[0] * 0.9, tip[1] * 0.9)], 0.6)])
    cv.shape(cv.ellipse((0, 0), 2.6, 1.8), GOLD, z=1, sd=0.5, ol=0.6)
    return P.done()


def ruh_tasi():
    """Ruh taşı kapak: 3 karo (72 dünya birimi) geniş, kalın kara taş levha; mor damarlar, ortada Erlik mührü runları
    (ışıma ayrı: oyunda nabız gibi atar). Köken üst orta (zemin yüzeyi)."""
    P = Prop(80, 30, 40, 4)
    cv = P.cv
    rng = np.random.default_rng(5)
    slab = cv.blob([(-37, -2, 0.0), (-36, -3.5), (-20, -4.2), (0, -3.6), (20, -4.4), (36, -3.4), (37, -2, 0.0), (37.5, 20), (36, 24, 0.0),
                    (-36, 24, 0.0), (-37.5, 20)])
    det = []
    for _ in range(6):
        x0 = rng.uniform(-34, 34)
        pts = [(x0, rng.uniform(-3, 4))]
        for k in range(4):
            pts.append((pts[-1][0] + rng.uniform(-6, 6), pts[-1][1] + rng.uniform(3, 6)))
        det.append(('stroke', pts, 1.4, AMETHYST.base, (0.2, 0.6)))
        det.append(('ink', pts[1:], 0.5, (0.3, 0.7)))
    det.append(('col', cv.blob([(-37, -2, 0.0), (37, -2, 0.0), (37, 0.5, 0.0), (-37, 0.5, 0.0)]), SLATE.hi))
    cv.shape(slab, SLATE, z=0, sd=5.0, hi=0.6, details=det, hatch=0.35)
    for f in (-1, 1):
        cv.shape(cv.blob([(f * 37.5, -2.5, 0.0), (f * 33, -4.5), (f * 31, -1, 0.0)]), MOSS, z=0.1, sd=0.6, ol=0.6)
    # mühür runları (ışır)
    for i in range(3):
        cx = -24 + i * 24
        cv.stroke([(cx - 4, 4), (cx, 11), (cx + 4, 4)], 1.6, z=0.5, col=(0.82, 0.58, 1.0), glow=(0.6, 0.3, 0.95), taper=(0.1, 0.1))
        cv.stroke([(cx - 2.5, 1.8), (cx + 2.5, 1.8)], 1.6, z=0.5, col=(0.82, 0.58, 1.0), glow=(0.6, 0.3, 0.95), taper=(0.1, 0.1))
        cv.stroke([(cx, 11), (cx, 16)], 1.2, z=0.5, col=(0.82, 0.58, 1.0), glow=(0.6, 0.3, 0.95), taper=(0.1, 0.4))
    return P.done()


def bulut(seed):
    """Ülgen'in altın bulut basamağı: öbekli üst, düz alt, cel gölgeli, kıvrık mürekkep sarmallı (çizgi roman bulutu).
    Köken üst orta (basılan yüzey); 84 dünya birimi geniş."""
    P = Prop(94, 34, 47, 8)
    cv = P.cv
    rng = np.random.default_rng(seed)
    lobes = []
    x = -38
    while x < 38:
        r = rng.uniform(7, 12) * (1 - abs(x) / 70)
        lobes.append((x, -1 + rng.uniform(-2, 2) + abs(x) * 0.05, r))
        x += r * rng.uniform(0.9, 1.3)
    paths = [cv.ellipse((lx, ly + 4), r * 1.15, r * 0.85) for lx, ly, r in lobes]
    base = cv.blob([(-40, 6, 0.0), (40, 6, 0.0), (36, 14), (0, 16), (-36, 14)])
    body = ik.union(base, *paths)
    det = []
    for lx, ly, r in lobes[1:-1]:
        if rng.random() < 0.6:
            sp = []
            for i in range(12):
                t = i / 11
                a = math.pi * 1.1 + t * 2.4 * math.pi
                rr = r * 0.55 * (1 - 0.7 * t)
                sp.append((lx + math.cos(a) * rr, ly + 4 + math.sin(a) * rr * 0.8))
            det.append(('stroke', sp, 1.2, CLOUD.shadow, (0.1, 0.8)))
    det.append(('deep', cv.blob([(-38, 11, 0.0), (38, 11, 0.0), (34, 15), (0, 17), (-34, 15)])))
    cv.shape(body, CLOUD, z=0, sd=6.0, hi=1.2, details=det, bounce=0.35)
    return P.done(rim=0.4, rim_col=(1.0, 0.95, 0.8))


DECOR = {
    'sunak': sunak,
    'kut_kapi': lambda: kut_kapi('on'),
    'kut_kapi_arka': lambda: kut_kapi('arka'),
    'kut_kapi_girdap': kut_kapi_girdap,
    'totem': totem,
    'totem_tuy': totem_tuy,
    'ruh_tasi': ruh_tasi,
    'bulut_1': lambda: bulut(1),
    'bulut_2': lambda: bulut(2),
    'bulut_3': lambda: bulut(3),
    'bulut_4': lambda: bulut(4),
}


# ------------------------------------------------------------------ atlas: toplanabilirler
def _pv(w, h, ox, oy):
    return Prop(w, h, ox, oy, ss=4)


def altin():
    """Altın sikke (yandan hafif açılı): kare delikli, kenarı tırtıklı, tamgalı."""
    P = _pv(10, 10, 5, 5)
    cv = P.cv
    cv.shape(cv.ellipse((0, 0), 3.6, 3.6), GOLD, z=0, sd=1.2, hi=0.5, ol=0.8)
    cv.shape(cv.blob([(-1, -1, 0.0), (1, -1, 0.0), (1, 1, 0.0), (-1, 1, 0.0)]), Ink('#5a3a1c'), z=0.1, noshadow=True, ol=0.5)
    return P.done(outer=0.9)


def kut():
    """Kut tanesi: firuze ışık damlası (kristal), mürekkep konturlu; ışıma ayrı."""
    P = _pv(12, 14, 6, 10)
    cv = P.cv
    drop = cv.blob([(0, -7.5, 0.0), (2.6, -3), (3.2, 0), (0, 3), (-3.2, 0), (-2.6, -3)])
    cv.shape(drop, Ink('#58e0d4', '#1e7c8c', '#e8fffc'), z=0, sd=1.4, hi=0.6, ol=0.8, glow=(0.2, 0.85, 0.85))
    cv.fill(cv.ellipse((-0.8, -2), 0.9, 1.6), (1, 1, 1), z=0.1, glow=(0.6, 1.0, 1.0))
    return P.done(outer=0.9)


def sifa():
    """Şifa otu: üç yaprak demeti, ortada ışıyan tohum."""
    P = _pv(18, 18, 9, 16)
    cv = P.cv
    for k, a in enumerate((-0.8, 0.0, 0.8)):
        tip = (math.sin(a) * 9, -2 - math.cos(a) * 9)
        leaf = cv.blob([(0, -1), (tip[0] * 0.5 - 2.4 * math.cos(a), (tip[1] - 1) * 0.5), (tip[0], tip[1], 0.0), (tip[0] * 0.5 + 2.4 * math.cos(a), (tip[1] - 1) * 0.5)])
        cv.shape(leaf, LEAF if k != 1 else Ink('#5c9a5a', '#264a3c', '#a4d890'), z=k * 0.1, sd=1.4, hi=0.3, ol=0.8,
                 details=[('ink', [(0, -1), (tip[0] * 0.85, tip[1] * 0.85)], 0.6)])
    cv.shape(cv.ellipse((0, -6), 2.2, 2.2), Ink('#d8ffb0', '#6ab050', '#ffffff'), z=1, sd=0.6, ol=0.7, glow=(0.45, 0.95, 0.4))
    cv.shape(cv.blob([(-2.4, 0.5, 0.0), (-1.6, -2), (1.6, -2), (2.4, 0.5, 0.0)]), Ink('#6a4a30'), z=0.5, sd=0.5, ol=0.6)
    return P.done(outer=0.9)


def tilsim_kaide():
    P = _pv(24, 10, 12, 8)
    cv = P.cv
    cv.shape(cv.blob([(-10, 0.5, 0.0), (-10, -3, 0.0), (-8, -5.5, 0.0), (8, -5.5, 0.0), (10, -3, 0.0), (10, 0.5, 0.0)]), STONE_W, z=0, sd=1.6, hi=0.4,
             details=[('col', cv.blob([(-7, -4.2, 0.0), (7, -4.2, 0.0), (7, -3.2, 0.0), (-7, -3.2, 0.0)]), TURQ.base)])
    return P.done(outer=0.9)


def tilsim_muska():
    """Kam tılsımı: tunç halkalı deri muska, üç renk taş (kurt kızılı, kartal mavisi, ayı yeşili), alt püskül."""
    P = _pv(18, 24, 9, 9)
    cv = P.cv
    cv.stroke([(0, -8.5), (0, -6)], 0.9, z=0, col=INK)
    cv.shape(cv.ellipse((0, 0), 6, 6), BRONZE, z=0.1, sd=1.4, hi=0.5, ol=0.9)
    cv.shape(cv.ellipse((0, 0), 4.4, 4.4), LEATHER, z=0.2, sd=1.2, ol=0.6)
    for k, col in enumerate(((1.0, 0.42, 0.3), (0.37, 0.78, 1.0), (0.61, 0.88, 0.4))):
        a = -math.pi / 2 + k * 2 * math.pi / 3
        cv.shape(cv.ellipse((math.cos(a) * 2.2, math.sin(a) * 2.2), 1.3, 1.3), Ink(col), z=0.3, sd=0.4, ol=0.5, glow=tuple(c * 0.6 for c in col))
    tassel(cv, 0, 6, 8, 4, RED, -0.1, strands=4)
    return P.done(outer=0.9)


def parsomen():
    """Rulo parşömen: iki ahşap uç, ortada mavi mühür ve ip."""
    P = _pv(22, 12, 11, 6)
    cv = P.cv
    cv.shape(cv.blob([(-7, -3.6, 0.0), (7, -3.6, 0.0), (7.5, 3.6, 0.0), (-7.5, 3.6, 0.0)]), Ink('#e4d4ac', '#9a8462', '#fff6dc'), z=0, sd=1.6, hi=0.4,
             details=[('ink', [(-4, -1), (4, -1.2)], 0.6), ('ink', [(-4, 1.2), (2, 1.0)], 0.6)])
    for f in (-1, 1):
        cv.shape(cv.ellipse((f * 8, 0), 1.8, 4.6), WOOD, z=0.2, sd=0.8, hi=0.3, ol=0.8)
        cv.shape(cv.ellipse((f * 8, -4.8), 1.0, 0.8), GOLD, z=0.25, sd=0.3, ol=0.5)
        cv.shape(cv.ellipse((f * 8, 4.8), 1.0, 0.8), GOLD, z=0.25, sd=0.3, ol=0.5)
    cv.stroke([(0, -3.6), (0, 3.6)], 1.0, z=0.3, col=RED.base)
    cv.shape(cv.ellipse((0, 1), 1.8, 1.8), Ink('#3c7ad0', '#1a3a80', '#a8d0ff'), z=0.4, sd=0.5, ol=0.6, glow=(0.2, 0.5, 0.9))
    return P.done(outer=0.9)


def kaide():
    """Eşya kaidesi: yontma taş sütuncuk, firuze kuşak, üstünde ince altın halka."""
    P = _pv(30, 16, 15, 1)
    cv = P.cv
    cv.shape(cv.blob([(-11, 13, 0.0), (-11, 4, 0.0), (11, 4, 0.0), (11, 13, 0.0)]), STONE, z=0, sd=2.0, hi=0.4,
             details=[('ink', [(-4, 5), (-4, 12)], 0.5), ('ink', [(5, 5), (5, 12)], 0.5)])
    cv.shape(cv.blob([(-13, 4.5, 0.0), (-13, 1, 0.0), (13, 1, 0.0), (13, 4.5, 0.0)]), STONE_W, z=0.1, sd=1.2, hi=0.4,
             details=[('col', cv.blob([(-12, 3.4, 0.0), (12, 3.4, 0.0), (12, 2.6, 0.0), (-12, 2.6, 0.0)]), TURQ.base)])
    return P.done(outer=0.9)


def don():
    """Seçkinin ruhu (don): mor ruh alevi, iki boş göz, kıvrık kuyruk (ışıma ağırlıklı)."""
    P = _pv(22, 26, 11, 14)
    cv = P.cv
    body = cv.blob([(0, -11, 0.0), (4, -6), (6.5, 0), (5, 5), (1, 8), (-2, 11, 0.0), (-3, 7), (-6, 4), (-6.5, -1), (-4, -6)])
    cv.shape(body, Ink('#9a74e0', '#4a2a90', '#e4d4ff'), z=0, sd=2.6, hi=0.6, ol=0.8, glow=(0.45, 0.25, 0.85))
    cv.shape(cv.ellipse((0, 0), 3.2, 3.6), Ink('#f0e8ff'), z=0.1, noshadow=True, ol=0.0, glow=(0.8, 0.7, 1.0))
    for f in (-1, 1):
        cv.fill(cv.ellipse((f * 1.6, -1.4), 0.8, 1.2), INK, z=0.2)
    return P.done(outer=0.8)


def ruh_kusu(frame):
    """Ülgen'in ruh kuşu: altın serçe silueti, kanatlar yukarı (0) / aşağı (1); ışıma ağırlıklı."""
    P = _pv(22, 16, 11, 9)
    cv = P.cv
    up = frame == 0
    for f in (-1, 1):
        tip = (f * 10, -7 if up else 5)
        wing = cv.blob([(f * 1, -1), (f * 5, -3 if up else 1), (tip[0], tip[1], 0.0), (f * 6, 0 if up else 2.5), (f * 2, 1)])
        cv.shape(wing, Ink('#ffd77a', '#c88a30', '#fff6d8'), z=0.1 if f > 0 else -0.1, sd=1.0, ol=0.7, glow=(0.9, 0.6, 0.18))
    cv.shape(cv.ellipse((0, 0), 3.2, 2.2), Ink('#ffe8a8', '#d09a40', '#ffffff'), z=0.2, sd=0.8, ol=0.7, glow=(1.0, 0.8, 0.4))
    cv.shape(cv.blob([(2.6, -1.6), (4.6, -0.6, 0.0), (2.6, 0.4)]), Ink('#e08a30'), z=0.3, sd=0.3, ol=0.5)
    cv.shape(cv.blob([(-2.6, -0.4), (-6, -1.8, 0.0), (-5.4, 1.6, 0.0)]), Ink('#ffd77a', '#c88a30', '#fff6d8'), z=0.0, sd=0.5, ol=0.6, glow=(0.9, 0.6, 0.18))
    return P.done(outer=0.8)


# ------------------------------------------------------------------ atlas: mermiler (sağa bakar, köken merkez)
def ok(variant):
    """Ok: ahşap gövde, çelik temren, kızıl-ak tüy; türler: normal, altin, od, sel, kizil, dusman."""
    P = _pv(30, 9, 17, 4.5)
    cv = P.cv
    head = {'altin': GOLD, 'od': Ink('#ff9a3a', '#c4421c', '#fff0b0'), 'dusman': IRON}.get(variant, STEEL)
    shaft = {'dusman': WOOD_D, 'kizil': WOOD_R}.get(variant, WOOD)
    fl = {'sel': (SKYB, FELT), 'kizil': (RED, RED), 'dusman': (HAIR_K, Ink('#5a4a40')), 'altin': (GOLD, FELT)}.get(variant, (RED, FELT))
    cv.shape(cv.capsule((-12, 0), (6, 0), 0.6, 0.6), shaft, z=0, sd=0.4, hi=0.2, ol=0.7)
    glow = {'od': (1.0, 0.5, 0.12), 'altin': (0.9, 0.65, 0.2), 'sel': None}.get(variant)
    cv.shape(cv.blob([(5, -1.8, 0.0), (11.5, 0, 0.0), (5, 1.8, 0.0), (6.2, 0)]), head, z=0.2, sd=0.6, hi=0.3, ol=0.8, glow=glow)
    for k, (m, sy) in enumerate(((fl[0], -1), (fl[1], 1))):
        cv.shape(cv.blob([(-6, 0), (-9, sy * 2.6), (-14, sy * 2.9, 0.0), (-12, 0)]), m, z=0.1 + k * 0.01, sd=0.5, ol=0.6)
    return P.done(outer=0.7, rim=0.0)


def tas(big=False):
    P = _pv(18 if big else 9, 18 if big else 9, 9 if big else 4.5, 9 if big else 4.5)
    cv = P.cv
    r = 6.2 if big else 2.8
    rng = np.random.default_rng(3 if big else 4)
    pts = [(math.cos(a) * r * rng.uniform(0.82, 1.08), math.sin(a) * r * rng.uniform(0.82, 1.08)) for a in np.linspace(0, 2 * math.pi, 9)[:-1]]
    cv.shape(cv.blob(pts), STONE if big else STONE_W, z=0, sd=r * 0.5, hi=r * 0.12, ol=0.8,
             details=[('ink', [(-r * 0.3, -r * 0.1), (r * 0.2, r * 0.3)], 0.6)] if big else ())
    if big:
        cv.shape(cv.blob(diamond(1.8, -1.8, 1.6, 2.2)), Ink('#9ae0ff', '#3a80b0', '#ffffff'), z=0.2, sd=0.4, ol=0.6, glow=(0.3, 0.7, 0.9))
    return P.done(outer=0.8)


def buz():
    """Buz sarkıtı (sağa doğru sivri)."""
    P = _pv(22, 10, 11, 5)
    cv = P.cv
    ice = Ink('#b4e6ff', '#4a8ac8', '#ffffff', name='buz')
    cv.shape(cv.blob([(10, 0, 0.0), (-2, -3.4), (-8, -2.4), (-9.5, 0, 0.0), (-8, 2.4), (-2, 3.4)]), ice, z=0, sd=1.4, hi=0.6, ol=0.8,
             details=[('stroke', [(-6, -0.8), (7, -0.2)], 0.9, (1, 1, 1), (0.2, 0.6))], glow=(0.15, 0.35, 0.5))
    return P.done(outer=0.8)


def ates_topu():
    """Ateş topu: mürekkep konturlu alev başı, geriye savrulan alev dilleri (ışıma ağırlıklı)."""
    P = _pv(30, 18, 20, 9)
    cv = P.cv
    tail = cv.blob([(4, -5.5), (-6, -6), (-16, -3, 0.0), (-9, -1.5), (-18, 1.5, 0.0), (-8, 2.6), (-14, 6, 0.0), (-2, 5.5), (5, 5)])
    cv.shape(tail, Ink('#ff7a26', '#b8301a', '#ffd070'), z=0, sd=2.0, ol=0.8, glow=(1.0, 0.4, 0.08))
    cv.shape(cv.ellipse((2, 0), 5.6, 5.0), Ink('#ffb04a', '#d0501c', '#fff4c0'), z=0.1, sd=1.6, hi=0.4, ol=0.8, glow=(1.0, 0.6, 0.15))
    cv.fill(cv.ellipse((3, -0.5), 2.6, 2.4), (1.0, 0.97, 0.82), z=0.2, glow=(1.0, 0.9, 0.6))
    return P.done(outer=0.8, rim=0.0)


def spor():
    """Zehirli spor: kabarık yeşil küre, koyu benekler, çevresinde dikenli tüyler."""
    P = _pv(16, 16, 8, 8)
    cv = P.cv
    for k in range(10):
        a = k * 2 * math.pi / 10
        cv.stroke([(math.cos(a) * 3.8, math.sin(a) * 3.8), (math.cos(a) * 6.8, math.sin(a) * 6.8)], 1.0, z=-0.1, col=(0.55, 0.85, 0.3), taper=(0.1, 0.9))
    cv.shape(cv.ellipse((0, 0), 4.4, 4.4), Ink('#8ad04a', '#3a7030', '#e0ffa0'), z=0, sd=1.6, hi=0.5, ol=0.8, glow=(0.4, 0.8, 0.15),
             details=[('col', cv.ellipse((1.4, 1.2), 0.9, 0.8), (0.24, 0.42, 0.18)), ('col', cv.ellipse((-1.6, 1.8), 0.6, 0.6), (0.24, 0.42, 0.18))])
    return P.done(outer=0.8)


def lanet():
    """Kam laneti: mor ruh alevi içinde kafatası izi (ışıma ağırlıklı)."""
    P = _pv(18, 16, 9, 8)
    cv = P.cv
    body = cv.blob([(6, 0, 0.0), (2, -5), (-4, -5.5), (-8, -2, 0.0), (-5, 0), (-8, 3, 0.0), (-3, 5), (3, 4.5)])
    cv.shape(body, Ink('#a060e0', '#502090', '#f0d0ff'), z=0, sd=1.6, ol=0.8, glow=(0.6, 0.25, 0.9))
    cv.shape(cv.ellipse((1, -0.4), 2.8, 2.6), Ink('#f0e4ff'), z=0.1, noshadow=True, ol=0.5, glow=(0.85, 0.7, 1.0))
    cv.fill(cv.ellipse((0.2, -0.8), 0.6, 0.8), INK, z=0.2)
    cv.fill(cv.ellipse((2.0, -0.8), 0.6, 0.8), INK, z=0.2)
    return P.done(outer=0.8, rim=0.0)


def tuy():
    """Kartal tüyü (fırlatılan): ak, uçta koyu bant."""
    P = _pv(20, 8, 10, 4)
    cv = P.cv
    f = cv.blob([(8, 0, 0.0), (2, -2.4), (-6, -2), (-9, 0, 0.0), (-6, 2), (2, 2.4)])
    cv.shape(f, FELT, z=0, sd=0.9, hi=0.3, ol=0.8,
             details=[('col', cv.blob([(4, -2.4, 0.0), (6, -2, 0.0), (6, 2, 0.0), (4, 2.4, 0.0)]), (0.22, 0.2, 0.26)),
                      ('ink', [(-9, 0), (7, 0)], 0.6)] + [('ink', [(x, 0), (x - 1.6, -1.8)], 0.4) for x in (-4, -1, 2)])
    return P.done(outer=0.8)


def kartal_ruhu():
    """Hayalet kartal: kanatları açık, firuze ruh (ışıma ağırlıklı)."""
    P = _pv(24, 22, 12, 11)
    cv = P.cv
    for s in (-1, 1):
        w = cv.blob([(2, 0), (-2, s * 3), (-8, s * 9.5, 0.0), (-6, s * 5), (-10, s * 6.5, 0.0), (-5, s * 2)])
        cv.shape(w, Ink('#7ee8f0', '#2a8ab0', '#e8ffff'), z=0.1 * s, sd=1.4, ol=0.7, glow=(0.3, 0.8, 0.95))
    cv.shape(cv.blob([(10, 0, 0.0), (6, -2.2), (-4, -2), (-9, 0, 0.0), (-4, 2), (6, 2.2)]), Ink('#a8f4ff', '#3a90b8', '#ffffff'), z=0.3, sd=1.0, ol=0.7,
             glow=(0.45, 0.9, 1.0))
    return P.done(outer=0.7, rim=0.0)


def dalga():
    """Yel dalgası: üç iç içe mürekkep hilali (beyaz; oyunda renklendirilir)."""
    P = _pv(26, 26, 13, 13)
    cv = P.cv
    for k in range(3):
        r = 6 + k * 3.6
        pts = [(math.cos(a) * r - r + 8, math.sin(a) * r) for a in np.linspace(-0.85, 0.85, 12)]
        cv.fill(ik.taper_path([cv.W(p) for p in pts], cv.px(5.0 - k * 1.2), (0.5, 0.5)), (1, 1, 1), z=k * 0.1, alpha=1.0 - k * 0.22,
                glow=(0.6, 0.6, 0.6))
    return P.done(outer=0.0, rim=0.0, grain=0.0)


def yer_dalgasi():
    """Yerden yükselen dalga: sivri toprak/enerji dilleri (beyaz-gri; oyunda renklendirilir). Köken alt orta (zemin)."""
    P = _pv(30, 30, 15, 28)
    cv = P.cv
    rng = np.random.default_rng(9)
    for k in range(6):
        x = -11 + k * 4.4 + rng.uniform(-1, 1)
        h = rng.uniform(12, 24) * (1 - abs(k - 2.5) * 0.12)
        cv.shape(cv.blob([(x - 3.2, 0.5, 0.0), (x - 1.0, -h * 0.6), (x + rng.uniform(-1, 1), -h, 0.0), (x + 1.4, -h * 0.55), (x + 3.2, 0.5, 0.0)]),
                 Ink('#f4f0e8', '#a09ab0', '#ffffff'), z=k * 0.01, sd=1.4, ol=0.8, glow=(0.5, 0.5, 0.5))
    cv.shape(cv.blob([(-14, 1, 0.0), (-12, -2), (12, -2), (14, 1, 0.0)]), Ink('#d8d0c4'), z=0.2, sd=0.8, ol=0.7)
    return P.done(outer=0.8, rim=0.0)


def kok():
    P = _pv(10, 14, 5, 13)
    cv = P.cv
    cv.shape(cv.blob([(-2.6, 0.5, 0.0), (-0.8, -6), (0.4, -11, 0.0), (1.4, -6), (2.6, 0.5, 0.0)]), WOOD, z=0, sd=1.0, hi=0.3, ol=0.8)
    return P.done(outer=0.8)


ATLAS = {
    'altin': altin, 'kut': kut, 'sifa': sifa, 'tilsim_kaide': tilsim_kaide, 'tilsim_muska': tilsim_muska, 'parsomen': parsomen,
    'kaide': kaide, 'don': don, 'ruh_kusu_0': lambda: ruh_kusu(0), 'ruh_kusu_1': lambda: ruh_kusu(1),
    'ok_normal': lambda: ok('normal'), 'ok_altin': lambda: ok('altin'), 'ok_od': lambda: ok('od'), 'ok_sel': lambda: ok('sel'),
    'ok_kizil': lambda: ok('kizil'), 'ok_dusman': lambda: ok('dusman'),
    'tas': tas, 'tas_buyuk': lambda: tas(True), 'buz': buz, 'ates_topu': ates_topu, 'spor': spor, 'lanet': lanet, 'tuy': tuy,
    'kartal_ruhu': kartal_ruhu, 'dalga': dalga, 'yer_dalgasi': yer_dalgasi, 'kok': kok,
}


def export_atlas(save, to8, A):
    """Raf paketleme: tek sayfa (genişlik 1024). json: {texel, sprites: {ad: {rect, pivot}}}; _e aynı yerleşimde ışıma."""
    items = []
    for n, fn in ATLAS.items():
        rgba, glow, org = fn()
        items.append((n, rgba, glow, org))
    items.sort(key=lambda t: -t[1].shape[0])
    W = 1024
    x = y = rowh = 0
    pos = {}
    pad = 4
    for n, r, g, o in items:
        h, w = r.shape[:2]
        if x + w + pad > W:
            x = 0
            y += rowh + pad
            rowh = 0
        pos[n] = (x, y)
        x += w + pad
        rowh = max(rowh, h)
    Hh = y + rowh
    Hh = int(math.ceil(Hh / 4.0) * 4)
    alb = np.zeros((Hh, W, 4), np.float32)
    glo = np.zeros((Hh, W, 4), np.float32)
    meta = {"texel": TEX, "filter": "linear", "sprites": {}}
    for n, r, g, o in items:
        px, py = pos[n]
        h, w = r.shape[:2]
        alb[py:py + h, px:px + w] = r
        glo[py:py + h, px:px + w] = g
        meta["sprites"][n] = {"rect": [px, py, w, h], "pivot": [round(o[0], 2), round(o[1], 2)], "glow": bool(g[..., 3].max() > 0.02)}
    save(to8(alb), 'fx/ink', 'sus_v2.png')
    save(to8(glo), 'fx/ink', 'sus_v2_e.png')
    json.dump(meta, open(os.path.join(A, 'fx', 'ink', 'sus_v2.json'), 'w', encoding='utf-8', newline='\n'), indent=1, ensure_ascii=False)
    print('  atlas', W, Hh, len(items))


# ------------------------------------------------------------------ tehlike karoları (karo 24 dünya birimi, 2 kare)
def _haz_cell(kind, frame):
    P = Prop(24, 24, 12, 24, ss=3)   # köken: karonun alt ortası; karo 0..24 x, -24..0 y
    cv = P.cv
    rng = np.random.default_rng(31 + frame * 7 + sum(map(ord, kind)))
    if kind == 'diken':
        # kemik-demir kazık dikenleri, dipte koyu toprak
        for k in range(5):
            x = -10 + k * 5 + rng.uniform(-0.6, 0.6)
            h = rng.uniform(13, 19) + (1.5 if (k + frame) % 2 else 0)
            cv.shape(cv.blob([(x - 2.4, 0.5, 0.0), (x - 0.7, -h * 0.55), (x + rng.uniform(-0.5, 0.5), -h, 0.0), (x + 0.9, -h * 0.5), (x + 2.4, 0.5, 0.0)]),
                     Ink('#c8bfa8', '#6a6070', '#f4ecd8') if k % 2 else IRON, z=k * 0.01, sd=1.2, hi=0.2, ol=0.8)
        cv.shape(cv.blob([(-12, 0.5, 0.0), (-12, -4, 0.0), (12, -4, 0.0), (12, 0.5, 0.0)]), Ink('#3a2c30', '#1c1418', '#5a4848'), z=0.2, noshadow=True, ol=0.0)
        cv.fill(cv.blob([(-12, -4, 0.0), (12, -4, 0.0), (12, -3, 0.0), (-12, -3, 0.0)]), (0.45, 0.12, 0.12), z=0.3, alpha=0.7)
    elif kind == 'zehir':
        cv.shape(cv.blob([(-12, 0.5, 0.0), (-12, -9, 0.0), (12, -9, 0.0), (12, 0.5, 0.0)]), Ink('#2e5a2a', '#173018', '#5aa040'), z=0, noshadow=True, ol=0.0,
                 glow=(0.15, 0.45, 0.08))
        for k in range(4):
            x = -9 + k * 6 + rng.uniform(-1, 1)
            r = rng.uniform(1.4, 2.8) * (1.2 if (k + frame) % 2 else 0.8)
            cv.shape(cv.ellipse((x, -9 - r * 0.6), r, r), Ink('#7ad050', '#3a7a2a', '#d8ffa0'), z=0.2, sd=0.8, hi=0.3, ol=0.6, glow=(0.3, 0.75, 0.15))
        cv.fill(cv.blob([(-12, -9.5, 0.0), (12, -9.5, 0.0), (12, -8, 0.0), (-12, -8, 0.0)]), (0.65, 1.0, 0.45), z=0.3, glow=(0.4, 0.9, 0.2))
    elif kind == 'lav':
        cv.shape(cv.blob([(-12, 0.5, 0.0), (-12, -10, 0.0), (12, -10, 0.0), (12, 0.5, 0.0)]), Ink('#c0401a', '#5a1210', '#ff9a40'), z=0, noshadow=True, ol=0.0,
                 glow=(0.9, 0.3, 0.05))
        for k in range(3):
            x = -8 + k * 8 + (2 if frame else -1)
            cv.shape(cv.blob([(x - 4, -7), (x, -9), (x + 4, -6.5), (x + 1, -4.5)]), Ink('#3a1a18', '#1a0a0c', '#5a2a20'), z=0.1, noshadow=True, ol=0.6)
        cv.fill(cv.blob([(-12, -10.5, 0.0), (12, -10.5, 0.0), (12, -9, 0.0), (-12, -9, 0.0)]), (1.0, 0.85, 0.4), z=0.3, glow=(1.0, 0.65, 0.2))
        for k in range(2):
            x = rng.uniform(-8, 8)
            cv.fill(cv.ellipse((x, -11 - frame * 2), 1.2, 1.4), (1.0, 0.8, 0.3), z=0.4, glow=(1.0, 0.6, 0.15))
    else:  # buz
        ice = Ink('#a8dcf8', '#4a7ab8', '#ffffff', name='buz')
        for k in range(4):
            x = -9 + k * 6
            h = rng.uniform(10, 17)
            cv.shape(cv.blob([(x - 3.2, 0.5, 0.0), (x - 1.2, -h * 0.5), (x, -h, 0.0), (x + 1.4, -h * 0.55), (x + 3.2, 0.5, 0.0)]), ice, z=k * 0.01, sd=1.6, hi=0.4, ol=0.8,
                     details=[('stroke', [(x - 1.2, -2), (x - 0.3, -h * 0.8)], 0.8, (1, 1, 1), (0.2, 0.6))])
        if frame:
            cv.fill(cv.ellipse((rng.uniform(-6, 6), -12), 0.9, 0.9), (1, 1, 1), z=0.5, glow=(0.6, 0.85, 1.0))
    return P.done(outer=0.9, rim=0.2)


def export_hazards(save, to8, A):
    rows = ['diken', 'zehir', 'lav', 'buz']
    C = int(24 * TEX)
    alb = np.zeros((C * 4, C * 2, 4), np.float32)
    glo = np.zeros_like(alb)
    for r, kind in enumerate(rows):
        for f in range(2):
            rgba, glow, org = _haz_cell(kind, f)
            alb[r * C:(r + 1) * C, f * C:(f + 1) * C] = rgba[:C, :C]
            glo[r * C:(r + 1) * C, f * C:(f + 1) * C] = glow[:C, :C]
    save(to8(alb), 'tiles', 'hazards_v2.png')
    save(to8(glo), 'tiles', 'hazards_v2_e.png')
    json.dump({"cell": [C, C], "texel": TEX, "rows": {k: i for i, k in enumerate(rows)}, "filter": "linear"},
              open(os.path.join(A, 'tiles', 'hazards_v2.json'), 'w', encoding='utf-8', newline='\n'), indent=1)
    print('  hazards_v2', C * 2, C * 4)


if __name__ == '__main__':
    import sys
    from PIL import Image
    which = sys.argv[1] if len(sys.argv) > 1 else 'decor'
    out = sys.argv[2] if len(sys.argv) > 2 else 'sus_on.png'
    src = DECOR if which == 'decor' else ATLAS
    res = [(n, fn()) for n, fn in src.items()]
    sc = 1 if which == 'decor' else 2
    W = sum(r[0].shape[1] * sc + 20 for _, r in res) + 20
    H = max(r[0].shape[0] * sc for _, r in res) + 40
    bg = np.zeros((H, W, 3), np.float32)
    bg[:] = (0.09, 0.1, 0.16)
    x = 20
    for n, (r, g, o) in res:
        if sc != 1:
            r = np.repeat(np.repeat(r, sc, 0), sc, 1)
            g = np.repeat(np.repeat(g, sc, 0), sc, 1)
        h, w = r.shape[:2]
        y = H - 20 - h
        a = r[..., 3:4]
        bg[y:y + h, x:x + w] = bg[y:y + h, x:x + w] * (1 - a) + r[..., :3] * a + g[..., :3] * g[..., 3:4] * 0.8
        x += w + 20
    Image.fromarray((np.clip(bg, 0, 1) * 255).astype(np.uint8)).save(out)
