"""Ulu Kayın Yurdu (v13): şaşalı kutsal kamp için 1.5x yoğunluklu süsler.

Her süs dünya pikseli cinsinden tasarlanır, HC sarmalayıcısı koordinatları 1.5 ile çarparak Canvas'a çizer.
Oyunda 2/3 ölçekle gösterilir (decor.json "k": 1.5): 1080p'de her doku pikseli 2x2 ekran pikseli olur,
yeni karolar ve arka planlarla aynı yoğunluk.

  yh_otag      : han otağı (ak keçe, kilim kuşakları, altın kaburgalar, oyma kapı, tepede tuğ)
  yh_cadir     : süslü küçük yurt (mavi/ak)
  yh_kayin     : Umay'ın dilek kayını (çaputlar, kut yaprakları)
  yh_sunak     : Umay sunağı (ak örtü, süt kâseleri, mumlar, taş Umay heykeli)
  yh_pinar     : kutsal pınar (kayalık, çağlayan, taş havuz)
  yh_demirhane : demirci ocağı (taş körük ocağı, saçak, alet askısı, silah sehpası, su fıçısı)
  yh_ors       : kütük üstünde örs
  yh_kartal    : tünekte bürküt (altın kartal)
  yh_at        : eğerli at
  yh_hali_sergi: Ozan köşesi: gerili kilim, minderler, sehpa
  yh_hali_1/2  : yere serili kilimler
  yh_yol_1/2/3 : taş döşeme yol
  yh_mangal    : tunç ateş tası (üç ayaklı)
  yh_kandil    : uzun tunç kandil
  yh_fener     : kancalı direkte fener
  yh_tug_k/m   : tuğ (at kılı püskül, kırmızı / gök sancak)
  yh_balbal_1/2: balbal
  yh_kurgan    : dikili taş halkası (biri kut runlu)
  yh_kapi      : Kut Kapısı'nın taç kapısı (çini kuşaklar, ışıl runlar, koçboynuzu tepelik)
  yh_kazan     : sacayak üstünde kazan

Kullanım: python yurt_hd.py   (assets/decor'a yazar, decor.json'a "k" alanıyla ekler, ön izleme üretir)
"""
import json
import math
import os
import random
import sys

import numpy as np

from raster import Canvas, Mat, ramp, to_img
from materials import M

K = 1.5
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = os.path.join(ROOT, 'assets')

# ------------------------------------------------------------ malzemeler
FELT_W = Mat(ramp(40, 0.10, 0.93, spread=0.35), name='ak keçe')
FELT_C = Mat(ramp(36, 0.22, 0.80, spread=0.35), name='krem keçe')
FELT_DK = Mat(ramp(28, 0.35, 0.40), name='koyu keçe')
RED = Mat(ramp(356, 0.80, 0.66), name='kilim kızılı')
RED_D = Mat(ramp(350, 0.78, 0.40), name='koyu kızıl')
BLUE = Mat(ramp(224, 0.70, 0.50), name='kilim laciverti')
SKY = Mat(ramp(205, 0.55, 0.78), name='gök mavisi')
TURQ = M['turq']
GOLD = M['gold']
GOLD_D = Mat(ramp(38, 0.82, 0.66), spec=0.6, name='koyu altın')
BRONZE = Mat(ramp(28, 0.70, 0.64), spec=0.7, name='tunç')
WOOD = M['wood']
WOOD_D = Mat(ramp(20, 0.55, 0.34), name='koyu ahşap')
WOOD_R = Mat(ramp(8, 0.62, 0.48), name='boyalı ahşap')
STONE = M['stone']
STONE_W = Mat(ramp(40, 0.10, 0.70, spread=0.45), name='ak taş')
ROCK = M['rock']
MOSS = Mat(ramp(100, 0.45, 0.34), name='koyu yosun')
ROCK_D = Mat(ramp(218, 0.18, 0.40, spread=0.45), name='koyu kaya')
IRON = M['iron']
LEATHER = M['leather']
BLACK = Mat(ramp(250, 0.25, 0.16, spread=0.3), name='kara kıl')
HAIR_W = Mat(ramp(40, 0.06, 0.93, spread=0.3), name='ak kıl')
BIRCH = Mat(ramp(40, 0.06, 0.92, spread=0.3), name='ak kayın')
BIRCH_D = Mat(ramp(220, 0.12, 0.28, spread=0.3), name='kayın lekesi')
LEAF_A = Mat(ramp(70, 0.42, 0.50, spread=0.4), name='altın yaprak')
LEAF_B = Mat(ramp(118, 0.36, 0.36, spread=0.4), name='yaprak')
KUT = M['kut']
FIRE = Mat(ramp(30, 0.9, 1.0), emissive=1.0, outline='#7a2a04', name='ateş')
FIRE_C = Mat(ramp(50, 0.55, 1.0), emissive=1.0, outline='#7a2a04', name='ateş göbeği')
EMBER = Mat(ramp(16, 0.9, 0.95), emissive=1.0, outline='#4a1004', name='kor')
GLASS = Mat(ramp(40, 0.75, 1.0), emissive=1.0, outline='#6a3004', name='fener camı')
CANDLE = Mat(ramp(44, 0.15, 0.95), name='mum')
WATER = Mat(ramp(186, 0.55, 0.92), emissive=0.75, outline='#0b3a4a', name='pınar suyu')
WATER_D = Mat(ramp(196, 0.65, 0.62), emissive=0.35, outline='#0b2a3a', name='havuz suyu')
MILK = Mat(ramp(45, 0.06, 0.98), flat=True, name='süt')
BREAD = Mat(ramp(32, 0.60, 0.78), name='ekmek')
HORSE = Mat(ramp(22, 0.62, 0.52, spread=0.45), name='doru at')
HORSE_D = Mat(ramp(18, 0.55, 0.30), name='at gölgesi')
EAGLE = Mat(ramp(28, 0.55, 0.36, spread=0.45), name='kartal tüyü')
EAGLE_H = Mat(ramp(42, 0.40, 0.82), name='altın ense')
BEAK = Mat(ramp(48, 0.80, 0.92), name='gaga')
TILE = Mat(ramp(186, 0.70, 0.66), spec=0.4, name='çini')
TILE_D = Mat(ramp(226, 0.70, 0.40), name='koyu çini')


def _hash(px, py, s=1.0):
    h = np.sin(np.floor(px) * 12.9898 + np.floor(py) * 78.233 + s * 3.1) * 43758.5453
    return h - np.floor(h)


class HC:
    """Dünya pikseliyle çizim; içerde 1.5x Canvas."""

    def __init__(self, w, h, ox, oy):
        self.c = Canvas(int(round(w * K)), int(round(h * K)), int(round(ox * K)), int(round(oy * K)))

    @staticmethod
    def _wrap(paint, poly=False):
        if not paint:
            return None
        out = []
        for fn, m in paint:
            if poly:
                out.append((lambda lu, lv, px, py, fn=fn: fn(lu / K, lv / K, px / K, py / K), m))
            else:
                out.append((lambda lu, lv, px, py, fn=fn: fn(lu, lv, px / K, py / K), m))
        return out

    def capsule(self, p0, p1, r0, r1, mat, z=0.0, tone=0.0, flat=0.35, paint=None):
        self.c.capsule((p0[0] * K, p0[1] * K), (p1[0] * K, p1[1] * K), r0 * K, r1 * K, mat, z * K, tone, flat, self._wrap(paint))

    def ellipse(self, c, rx, ry, mat, z=0.0, rot=0.0, depth=1.0, tone=0.0, flat=0.35, paint=None):
        self.c.ellipse((c[0] * K, c[1] * K), rx * K, ry * K, mat, z * K, rot, depth, tone, flat, self._wrap(paint))

    def poly(self, pts, mat, z=0.0, bevel=1.6, height=1.5, tone=0.0, paint=None, tilt=(0.0, 0.0)):
        self.c.poly([(x * K, y * K) for x, y in pts], mat, z * K, bevel * K, height * K, tone, self._wrap(paint, True), tilt)

    def rect(self, x0, y0, x1, y1, mat, z=0.0, bevel=1.2, height=1.0, paint=None, tone=0.0):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], mat, z, bevel, height, tone, paint)

    def dot(self, p, mat, z=50.0, size=1):
        self.c.dot((p[0] * K, p[1] * K), mat, z * K, size)

    def line(self, p0, p1, w, mat, z=0.0):
        self.capsule(p0, p1, w, w, mat, z, flat=0.6)

    def flame(self, x, y, s, z=20.0):
        """Alev dili: dış turuncu, iç sarı."""
        self.poly([(x - 5 * s, y), (x + 5 * s, y), (x + 4 * s, y - 6 * s), (x + 1.5 * s, y - 13 * s), (x + 0.5 * s, y - 8 * s),
                   (x - 1.5 * s, y - 16 * s), (x - 3 * s, y - 9 * s), (x - 4.5 * s, y - 6 * s)], FIRE, z, bevel=1.2 * s, height=1)
        self.poly([(x - 2.5 * s, y), (x + 2.5 * s, y), (x + 1.5 * s, y - 5 * s), (x - 0.5 * s, y - 10 * s), (x - 1.8 * s, y - 5 * s)],
                  FIRE_C, z + 2, bevel=0.8 * s, height=0.8)


# ------------------------------------------------------------ desen yardımcıları (dünya pikseli)
def zig(y0, amp, period, thick):
    def f(lu, lv, px, py):
        tri = np.abs(((px / period) % 2) - 1) * 2 - 1
        return np.abs(py - (y0 + tri * amp)) < thick
    return f


def hband(y0, y1):
    return lambda lu, lv, px, py: (py >= y0) & (py < y1)


def diamonds(cx_period, cy, size, thick=None, x0=0.0):
    def f(lu, lv, px, py):
        u = ((px - x0) % cx_period) - cx_period / 2
        d = np.abs(u) + np.abs(py - cy)
        return (d < size) if thick is None else ((d < size) & (d > size - thick))
    return f


def vstripes(period, width, x0=0.0):
    return lambda lu, lv, px, py: ((px - x0) % period) < width


def AND(*fs):
    def f(*a):
        r = fs[0](*a)
        for g in fs[1:]:
            r = r & g(*a)
        return r
    return f


# ------------------------------------------------------------ çadırlar
def _tent(c, R, wall_h, roof_h, felt, band, band2, trim, door_mat, crown=True, seed=1, rich=True):
    """Yan görünüş yurt. R: yarı genişlik, duvar yüksekliği wall_h, kubbe yüksekliği roof_h."""
    rng = random.Random(seed)
    eave = -wall_h
    # duvar (kerege üstü keçe): yanlara doğru bombe
    wall_paint = [
        (hband(eave + 10, eave + 24), band),
        (AND(hband(eave + 12, eave + 22), zig(eave + 17, 3.0, 6.0, 1.1)), trim),
        (AND(hband(eave + 9, eave + 10.2)), trim),
        (AND(hband(eave + 24, eave + 25.4)), trim),
        (hband(-7, 0.1), FELT_DK),
        (AND(hband(-6.5, -1.5), diamonds(12, -4, 2.6)), band2),
    ]
    if rich:
        wall_paint += [(AND(hband(eave + 28, -9), diamonds(26, (eave - 9) * 0.5 + 9, 6.5, 1.6, 13)), band2),
                       (AND(hband(eave + 28, -9), diamonds(26, (eave - 9) * 0.5 + 9, 2.2, None, 13)), trim)]
    c.poly([(-R, eave), (R, eave), (R + 1, 0), (-R - 1, 0)], felt, z=0, bevel=R * 0.28, height=2.5, paint=wall_paint)
    # kubbe: ak keçe, altın kaburgalar, saçak kuşağı
    RR = R + 7
    top = eave - roof_h

    def ytop(x):
        t = np.clip(1 - (x / RR) ** 2, 0, 1)
        return eave + 3 - (roof_h + 3) * t ** 0.62

    def ybot(x):
        return eave + 5 - 4 * (1 - (x / RR) ** 2)

    xs = np.linspace(-RR, RR, 40)
    pts = [(x, ytop(x)) for x in xs] + [(x, ybot(x)) for x in xs[::-1]]

    def hw(py):
        t = np.clip((eave + 3 - py) / (roof_h + 3), 0, 0.9999)
        return RR * np.sqrt(np.clip(1 - t ** (1 / 0.62), 1e-4, 1))

    rib = lambda lu, lv, px, py: (np.abs(((px / hw(py)) * 5.0 + 0.5) % 1.0 - 0.5) < 0.055) & (py < ybot(px) - 9)
    eave_band = lambda lu, lv, px, py: py > ybot(px) - 9
    eave_trim = lambda lu, lv, px, py: (np.abs(py - (ybot(px) - 9)) < 0.9) | (py > ybot(px) - 1.2)
    eave_zig = lambda lu, lv, px, py: (py > ybot(px) - 9) & (np.abs(py - (ybot(px) - 4.6 + (np.abs((px / 5.0) % 2 - 1) * 2 - 1) * 2.2)) < 0.8)
    crown_band = lambda lu, lv, px, py: (py < top + roof_h * 0.32) & (py > top + roof_h * 0.2)
    c.poly(pts, felt, z=4, bevel=R * 0.22, height=3,
           paint=[(eave_band, band), (eave_zig, trim), (eave_trim, trim), (crown_band, band2), (rib, GOLD_D)])
    # saçak püskülleri
    for k in range(int(RR * 2 / 9) + 1):
        x = -RR + 4 + k * 9
        if abs(x) > RR - 2:
            continue
        y = float(ybot(x))
        c.capsule((x, y), (x, y + 4.5), 0.9, 0.6, trim, z=12)
        c.dot((x, y + 5), trim, z=13, size=2)
    # tepe: şangırak halkası
    if crown:
        c.ellipse((0, top + 1), 11, 3.2, GOLD, z=14)
        c.ellipse((0, top - 2), 7, 2.6, felt, z=13)
        c.capsule((0, top - 2), (0, top - 10), 1.4, 1.0, GOLD_D, z=15)
        c.ellipse((0, top - 11), 2.6, 2.6, GOLD, z=16)
    # kapı: oyma, boyalı çift kanat
    dw = max(9, R * 0.17)
    dh = min(wall_h - 6, 44)
    c.rect(-dw - 3, -dh - 4, dw + 3, 0, WOOD_D, z=12, bevel=1.5, height=1.5)
    door_p = [(lambda lu, lv, px, py: np.abs(px) < 0.7, WOOD_D),
              (diamonds(dw, -dh * 0.62, dw * 0.38, 1.3, dw / 2), trim),
              (diamonds(dw, -dh * 0.25, dw * 0.3, 1.2, dw / 2), trim),
              (lambda lu, lv, px, py: (np.abs(np.abs(px) - dw + 1.6) < 0.7) | (np.abs(py + dh - 1.6) < 0.7), trim)]
    c.rect(-dw, -dh, dw, 0, door_mat, z=14, bevel=1.2, height=1.0, paint=door_p)
    c.dot((-2.2, -dh * 0.45), GOLD, z=20, size=2); c.dot((1.2, -dh * 0.45), GOLD, z=20, size=2)
    # kapı üstü saçak (kilim perde) + nazar levhası
    c.poly([(-dw - 7, -dh - 9), (dw + 7, -dh - 9), (dw + 7, -dh - 3), (-dw - 7, -dh - 3)], band, z=18, bevel=1, height=1,
           paint=[(zig(-dh - 6, 1.6, 4, 0.7), trim)])
    for k in range(int((2 * dw + 14) / 4) + 1):
        x = -dw - 6 + k * 4
        c.capsule((x, -dh - 3), (x, -dh - 1), 0.7, 0.5, trim, z=19)
    c.ellipse((0, -dh - 13), 4.2, 4.2, GOLD, z=20)
    c.ellipse((0, -dh - 13), 2.6, 2.6, M['nazar_b'], z=21)
    c.dot((-0.5, -dh - 13.5), M['nazar_w'], z=24, size=2)
    return top, dw, dh


def decor_otag():
    """Han otağı: büyük ak keçe yurt, kızıl kilim kuşakları, altın kaburgalar; tepede tuğ, iki yanda asılı sancak."""
    c = HC(230, 220, 115, 216)
    top, dw, dh = _tent(c, 86, 70, 58, FELT_W, RED, BLUE, GOLD, WOOD_R, seed=3)
    # tepe tuğu: direk, altın tepelik (üç çatal), at kılı püskül, kızıl flama
    c.capsule((0, top - 10), (0, top - 62), 1.5, 1.2, WOOD_D, z=20)
    c.poly([(-1.8, top - 62), (1.8, top - 62), (0, top - 74)], GOLD, z=22, bevel=0.8, height=1)
    for s in (-1, 1):
        c.capsule((0, top - 61), (s * 5, top - 66), 0.9, 0.7, GOLD, z=22)
        c.capsule((s * 5, top - 66), (s * 5, top - 70), 0.8, 0.5, GOLD, z=22)
    c.ellipse((0, top - 60), 4, 1.6, GOLD_D, z=23)
    for k in range(9):
        a = (k - 4) / 4.0
        c.capsule((a * 3, top - 59), (a * 6 - 1, top - 40 + abs(a) * 3), 1.3, 0.7, BLACK if k % 3 else HAIR_W, z=21 + (k % 2))
    flag = [(1.5, top - 56), (34, top - 52), (28, top - 48), (36, top - 44), (1.5, top - 44)]
    c.poly(flag, RED, z=19, bevel=1.2, height=0.8, paint=[(lambda lu, lv, px, py: np.abs(py - (top - 50)) < 0.7, GOLD)])
    # iki yanda asılı sancak (gök, altın tamga)
    for s in (-1, 1):
        x0 = s * 60
        c.poly([(x0 - 7, -66), (x0 + 7, -66), (x0 + 7, -22), (x0, -16), (x0 - 7, -22)], BLUE, z=10, bevel=1.5, height=1.2,
               paint=[(lambda lu, lv, px, py, x0=x0: (np.abs(np.abs(px - x0) - 5.2) < 0.7), GOLD),
                      (lambda lu, lv, px, py, x0=x0: (np.abs(px - x0) + np.abs(py + 44) < 4.2) & (np.abs(px - x0) + np.abs(py + 44) > 2.6), GOLD),
                      (lambda lu, lv, px, py, x0=x0: (np.abs(px - x0) < 0.8) & (py > -56) & (py < -30), GOLD)])
        c.capsule((x0 - 9, -67), (x0 + 9, -67), 1.1, 1.1, GOLD_D, z=12)
        c.dot((x0 - 0.5, -17), GOLD, z=14, size=2)
    # kapı önü: iki altın başlı direk ve aralarında saçak
    for s in (-1, 1):
        x = s * (dw + 16)
        c.capsule((x, 0), (x, -dh - 18), 1.6, 1.4, WOOD_R, z=24, paint=[(lambda lu, lv, px, py: (py % 7) < 1.2, GOLD_D)])
        c.ellipse((x, -dh - 20), 2.6, 2.6, GOLD, z=26)
    sx = dw + 16
    c.poly([(-sx - 2, -dh - 18), (sx + 2, -dh - 18), (sx + 2, -dh - 11), (-sx - 2, -dh - 11)], RED, z=25, bevel=1.2, height=1,
           paint=[(zig(-dh - 14.5, 1.8, 5, 0.8), GOLD), (hband(-dh - 18, -dh - 17), GOLD), (hband(-dh - 12, -dh - 10), GOLD)])
    for k in range(int((2 * sx + 4) / 6) + 1):
        x = -sx + k * 6
        c.poly([(x - 3, -dh - 11), (x + 3, -dh - 11), (x, -dh - 7)], RED, z=25, bevel=0.8, height=0.6)
        c.dot((x - 0.5, -dh - 7), GOLD, z=27, size=2)
    return c.c


def decor_cadir():
    """Süslü küçük yurt: krem keçe, gök kuşak, kızıl kapı."""
    c = HC(140, 120, 70, 116)
    top, dw, dh = _tent(c, 52, 46, 40, FELT_C, BLUE, RED, GOLD, RED_D, seed=5, rich=False)
    # tünlükten tüten ince duman yok (parçacıkla); yan kazık ipleri
    for s in (-1, 1):
        c.capsule((s * 50, -38), (s * 64, 0), 0.5, 0.5, WOOD_D, z=-4)
        c.capsule((s * 64, 0), (s * 64, -3), 1.2, 1.0, WOOD, z=-3)
    return c.c


# ------------------------------------------------------------ Umay köşesi
def decor_kayin():
    """Dilek kayını: ak gövde, altın-yeşil taç, ışıl kut yaprakları, bol renkli çaput."""
    c = HC(200, 236, 100, 232)
    rng = random.Random(11)
    marks = lambda lu, lv, px, py: (np.floor(py * 0.16 + np.sin(px * 0.7) * 0.8) % 4 == 0) & (np.abs(lv) < 0.5) & (((px * 3 + py) % 7) < 3)
    c.capsule((0, 0), (-4, -120), 13, 7.5, BIRCH, z=0, paint=[(marks, BIRCH_D)])
    for x0, y0, x1, y1, r in ((-3, -84, -52, -146, 4.6), (-3, -96, 46, -156, 4.2), (-4, -118, -22, -178, 3.4), (-4, -118, 18, -184, 3.4),
                              (-36, -126, -74, -160, 2.4), (32, -138, 72, -166, 2.4), (-4, -110, 4, -150, 2.4)):
        c.capsule((x0, y0), (x1, y1), r, r * 0.5, BIRCH, z=1, paint=[(marks, BIRCH_D)])
    for dx in (-22, -10, 12, 24):
        c.capsule((dx * 0.3, -5), (dx * 1.4, 0), 4.5, 2.0, BIRCH, z=0.5, paint=[(marks, BIRCH_D)])
    # taç
    for k in range(240):
        a = rng.uniform(0, math.tau); r = rng.uniform(0, 1) ** 0.6
        x = math.cos(a) * r * 92 - 3
        y = -168 + math.sin(a) * r * 50
        c.ellipse((x, y), rng.uniform(4, 8), rng.uniform(3, 5.5), LEAF_A if rng.random() < 0.6 else LEAF_B, z=-3 + rng.uniform(0, 3) + (y + 168) * -0.02)
    for k in range(60):
        a = rng.uniform(0, math.tau); r = rng.uniform(0.1, 1) ** 0.7
        c.ellipse((math.cos(a) * r * 86 - 3, -166 + math.sin(a) * r * 46), rng.uniform(1.0, 1.8), rng.uniform(1.0, 1.4), KUT, z=3 + rng.uniform(0, 1))
    # çaputlar: dallardan sarkan, uzun, renkli
    cols = [RED, M['turq'], FELT_W, GOLD, BLUE, M['flower_y']]
    for k in range(34):
        bx = rng.uniform(-78, 78); by = -132 + abs(bx) * 0.18 + rng.uniform(-14, 8)
        ln = rng.uniform(9, 22)
        sw = rng.uniform(-2.5, 2.5)
        c.capsule((bx, by), (bx + sw, by + ln), 1.3, 1.0, cols[k % len(cols)], z=5 + rng.uniform(0, 1))
    # gövdeye dolanmış kızıl-ak ip ve nazar
    for k in range(7):
        y = -38 - k * 3.2
        c.capsule((-9.5, y + 1.6), (9.5, y - 1.6), 0.8, 0.8, RED if k % 2 else FELT_W, z=16)
    c.ellipse((-1, -26), 3.4, 3.4, M['nazar_b'], z=18)
    c.ellipse((-1, -26), 2.0, 2.0, M['nazar_l'], z=19)
    c.dot((-1.5, -26.5), M['black'], z=22, size=2)
    return c.c


def decor_sunak():
    """Umay sunağı: taş Umay heykeli (boynuzlu taç, ışıl gözler), ak örtülü taş sunak, süt kâseleri, ekmek, mumlar."""
    c = HC(84, 92, 42, 88)
    # heykel (arka)
    c.poly([(-9, -30), (9, -30), (11, -56), (6, -66), (-6, -66), (-11, -56)], STONE_W, z=0, bevel=3, height=3,
           paint=[(lambda lu, lv, px, py: (np.abs(px) < 0.8) & (py > -50), STONE), (zig(-44, 1.5, 3, 0.6), STONE)])
    c.ellipse((0, -71), 6, 6.5, STONE_W, z=2)
    c.dot((-2.6, -72), KUT, z=30, size=2); c.dot((1.4, -72), KUT, z=30, size=2)
    for s in (-1, 1):
        c.capsule((s * 4, -76), (s * 10, -86), 1.4, 0.8, STONE_W, z=1)
        c.capsule((s * 8, -82), (s * 14, -84), 0.9, 0.6, STONE_W, z=1)
        c.capsule((s * 9, -84), (s * 9, -90), 0.9, 0.5, STONE_W, z=1)
    c.ellipse((0, -78), 2, 2, KUT, z=6)
    # kucakta çocuk / kut topu
    c.ellipse((0, -50), 4.2, 4.2, KUT, z=8)
    # sunak taşı
    c.rect(-30, -26, 30, -18, STONE, z=6, bevel=2, height=2)
    c.rect(-26, -18, -14, 0, STONE, z=4, bevel=2, height=2)
    c.rect(14, -18, 26, 0, STONE, z=4, bevel=2, height=2)
    c.rect(-12, -14, 12, 0, ROCK, z=2, bevel=2, height=1.5)
    # ak örtü, gök nakışlı, püsküllü
    c.poly([(-32, -27), (32, -27), (32, -16), (24, -12), (-24, -12), (-32, -16)], FELT_W, z=10, bevel=1.5, height=1.2,
           paint=[(hband(-20, -18.5), SKY), (AND(hband(-18, -14), diamonds(8, -16, 1.6)), RED)])
    for k in range(13):
        x = -24 + k * 4
        c.capsule((x, -12.5), (x, -9.5), 0.6, 0.5, RED if k % 2 else SKY, z=11)
    # adaklar
    for x, r in ((-20, 4.5), (18, 4)):
        c.ellipse((x, -29), r, 2.4, BRONZE, z=14)
        c.ellipse((x, -31), r - 1, 1.0, MILK, z=16)
    c.ellipse((-3, -30), 6, 3.4, BREAD, z=13, paint=[(lambda lu, lv, px, py: (np.abs(px + 3) % 3 < 0.6) & (py < -31), Mat(ramp(28, 0.6, 0.55)))])
    for x, h in ((-27, 8), (8, 11), (26, 7), (-11, 6)):
        c.capsule((x, -28), (x, -28 - h), 1.3, 1.2, CANDLE, z=18)
        c.ellipse((x, -31 - h), 1.2, 2.2, FIRE, z=22)
        c.dot((x - 0.4, -30.5 - h), FIRE_C, z=24, size=1)
    # yerde geyik boynuzu ve çiçekler
    c.capsule((-36, -2), (-28, -10), 1.2, 0.8, M['bone'], z=12)
    c.capsule((-32, -6), (-36, -12), 0.9, 0.6, M['bone'], z=12)
    for x, m in ((32, M['flower_y']), (36, M['flower_r']), (-38, M['flower_b'])):
        c.capsule((x, 0), (x, -6), 0.5, 0.4, M['grass'], z=11)
        c.ellipse((x, -7), 1.8, 1.6, m, z=12)
    return c.c


def decor_pinar():
    """Kutsal pınar: yosunlu kayalık, yarıktan dökülen ışıl çağlayan, taş çevreli havuz."""
    c = HC(130, 120, 65, 116)
    rng = random.Random(21)
    # kayalık: üst üste bloklar (arka)
    rocks = [(-34, -18, 30, 20), (-8, -30, 34, 30), (22, -24, 26, 24), (-20, -62, 26, 22), (14, -66, 28, 26), (-2, -92, 22, 18), (28, -50, 18, 20)]
    for x, y, rx, ry in rocks:
        c.ellipse((x, y), rx, ry, ROCK_D, z=-ry * 0.3 + rng.uniform(0, 2), paint=[(lambda lu, lv, px, py: lv < -0.72, MOSS)])
    # yarık ve çağlayan
    c.poly([(-6, -88), (4, -88), (5, -24), (-7, -24)], Mat(ramp(220, 0.3, 0.16)), z=20, bevel=1, height=0.5)
    wf = lambda lu, lv, px, py: ((px * 0.7 + py * 0.25 + np.sin(py * 0.4) * 1.2) % 3.0) < 0.9
    c.poly([(-4.5, -88), (3, -88), (4, -30), (6, -12), (-8, -12), (-5.5, -30)], WATER, z=24, bevel=1.5, height=1, paint=[(wf, FELT_W)])
    # havuz
    c.ellipse((-2, -6), 46, 7, STONE, z=26)
    c.ellipse((-2, -8), 40, 4.6, WATER_D, z=30, depth=0.2, paint=[(lambda lu, lv, px, py: (np.abs(lv) < 0.18) & (np.abs(lu) < 0.75) & ((px % 9) < 4), WATER)])
    for k in range(13):
        a = math.pi * (k / 12)
        x = -2 + math.cos(a) * 44
        c.ellipse((x, -3 + math.sin(a) * 1.5), rng.uniform(4, 6), rng.uniform(3, 4), STONE, z=34 + rng.uniform(0, 1))
    # köpük
    for k in range(10):
        c.ellipse((-1 + rng.uniform(-9, 9), -9 + rng.uniform(-1.5, 1)), rng.uniform(1.2, 2.4), 1.2, FELT_W, z=38)
    # eğrelti ve çiçek
    for x in (-50, -40, 40, 48):
        for j in range(4):
            a = -math.pi / 2 + (j - 1.5) * 0.45
            c.capsule((x, -2), (x + math.cos(a) * 12, -2 + math.sin(a) * 12), 1.2, 0.5, M['grass'], z=36)
    # kayaya kazınmış ışıl Umay damgası
    c.poly([(26, -60), (31, -60), (28.5, -66)], KUT, z=40, bevel=0.5, height=0.5)
    c.capsule((28.5, -59), (28.5, -52), 0.7, 0.7, KUT, z=40)
    return c.c


# ------------------------------------------------------------ Demirci köşesi
def decor_demirhane():
    """Demirci ocağı: taş körük ocağı (kor ağızlı), deri körük, saçak, asılı aletler, silah sehpası, su fıçısı."""
    c = HC(160, 124, 80, 120)
    # saçak direkleri ve çatı (arka)
    for x in (-70, 62):
        c.capsule((x, 0), (x, -88), 2.4, 2.0, WOOD_D, z=-10)
    c.poly([(-80, -86), (72, -96), (74, -88), (-78, -78)], WOOD, z=-8, bevel=2, height=2,
           paint=[(vstripes(9, 1.2), WOOD_D)])
    c.poly([(-82, -80), (76, -90), (76, -84), (-82, -74)], RED_D, z=-7, bevel=1, height=1,
           paint=[(zig(-80, 1.4, 4, 0.6), GOLD_D)])
    # asılı aletler: maşa, çekiç, nal, orak
    for x, kind in ((-58, 'masa'), (-48, 'cekic'), (-38, 'nal'), (-30, 'cekic'), (40, 'nal'), (50, 'masa')):
        y0 = -80 + x * -0.06
        c.capsule((x, y0), (x, y0 + 6), 0.4, 0.4, BLACK, z=-5)
        if kind == 'masa':
            c.capsule((x, y0 + 6), (x - 2, y0 + 24), 0.8, 0.6, IRON, z=-4)
            c.capsule((x, y0 + 6), (x + 2, y0 + 24), 0.8, 0.6, IRON, z=-4)
        elif kind == 'cekic':
            c.capsule((x, y0 + 6), (x, y0 + 20), 0.9, 0.9, WOOD, z=-4)
            c.rect(x - 4, y0 + 19, x + 4, y0 + 23, IRON, z=-3)
        else:
            c.ellipse((x, y0 + 10), 3.6, 4.2, IRON, z=-4)
            c.ellipse((x, y0 + 10.5), 2.0, 2.8, BLACK, z=-3.5)
    # ocak: taş kubbe + baca
    for k in range(26):
        a = math.pi * (k / 25)
        r = 30
        c.ellipse((8 + math.cos(a) * r * 0.95, -4 - math.sin(a) * r * 0.85), 6, 5, STONE, z=8 + k % 3, depth=0.4)
    c.ellipse((8, -24), 30, 24, ROCK_D, z=0, depth=0.15)
    c.rect(-1, -84, 17, -40, ROCK, z=-3, bevel=3, height=1, paint=[(lambda lu, lv, px, py: ((py % 8) < 1) | ((((px + np.floor(py / 8) * 5) % 10) < 1)), ROCK_D)])
    c.rect(-3, -88, 19, -82, STONE, z=-2, bevel=1.5, height=1)
    c.ellipse((8, -86), 7, 1.6, EMBER, z=-1, depth=0.2)
    # kor ağzı
    c.ellipse((8, -14), 14, 11, Mat(ramp(10, 0.6, 0.18)), z=12, depth=0.1)
    c.ellipse((8, -12), 11, 8.5, EMBER, z=14, depth=0.1)
    c.ellipse((8, -9), 7, 5, FIRE_C, z=16, depth=0.1)
    c.flame(4, -6, 0.6, z=17); c.flame(11, -6, 0.75, z=17)
    c.poly([(-8, -4), (24, -4), (24, 0), (-8, 0)], STONE, z=20, bevel=1, height=1)
    for k in range(7):
        c.ellipse((-6 + k * 5, -5), 2.8, 2.2, EMBER if k % 2 else ROCK_D, z=21)
    # körük (sol)
    c.poly([(-42, -24), (-14, -18), (-14, -10), (-42, -6)], LEATHER, z=22, bevel=3, height=3, paint=[(vstripes(5, 1, 1), Mat(ramp(20, 0.5, 0.3)))])
    c.rect(-46, -27, -40, -3, WOOD_D, z=26)
    c.capsule((-46, -15), (-58, -24), 1.2, 1.2, WOOD, z=27)
    c.capsule((-14, -14), (-6, -12), 2.0, 1.6, IRON, z=27)
    # silah sehpası (sağ): kılıç, mızrak, kalkan
    c.rect(36, -46, 40, 0, WOOD_D, z=4)
    c.rect(54, -46, 58, 0, WOOD_D, z=4)
    c.rect(34, -40, 60, -37, WOOD, z=5)
    for x, ln in ((41, 58), (46, 50), (51, 64)):
        c.capsule((x, -2), (x, -ln), 0.9, 0.9, IRON if x != 51 else WOOD, z=6)
        if x == 51:
            c.poly([(x - 2, -ln), (x + 2, -ln), (x, -ln - 8)], IRON, z=7, bevel=0.8, height=0.8)
        else:
            c.rect(x - 3, -18, x + 3, -16, GOLD_D, z=7)
    c.ellipse((64, -22), 11, 12, WOOD_R, z=8, paint=[(lambda lu, lv, px, py: np.abs(np.sqrt(lu * lu + lv * lv) - 0.8) < 0.1, GOLD_D)])
    c.ellipse((64, -22), 3, 3, GOLD, z=12)
    # su fıçısı (sol önde)
    c.rect(-70, -22, -52, 0, WOOD, z=12, bevel=4, height=3, paint=[(lambda lu, lv, px, py: (np.abs(py + 5) < 1) | (np.abs(py + 17) < 1), IRON)])
    c.ellipse((-61, -22), 9, 2, WATER_D, z=16)
    return c.c


def decor_ors():
    """Kütük üstünde örs, yanında çekiç ve kızgın demir."""
    c = HC(48, 40, 24, 37)
    c.poly([(-10, 0), (10, 0), (8, -16), (-8, -16)], WOOD, z=0, bevel=2, height=2, paint=[(lambda lu, lv, px, py: (py < -14.5), Mat(ramp(34, 0.45, 0.72)))])
    c.poly([(-15, -16), (12, -16), (16, -19), (13, -24), (-6, -24), (-16, -22), (-20, -21)], IRON, z=4, bevel=1.4, height=1.4)
    c.rect(-6, -19, 6, -16, IRON, z=3)
    c.capsule((-4, -25), (9, -26), 1.0, 0.8, EMBER, z=8)
    c.capsule((16, -2), (20, -14), 0.9, 0.9, WOOD, z=6)
    c.rect(16, -18, 23, -13, IRON, z=7)
    return c.c


def decor_kartal():
    """Tünekte bürküt: T tüneği, deri bağ, altın enseli kartal (sola bakar)."""
    c = HC(54, 96, 27, 92)
    c.capsule((0, 0), (0, -66), 1.8, 1.4, WOOD_D, z=0)
    c.capsule((-14, -66), (14, -66), 1.6, 1.6, WOOD, z=2)
    c.capsule((-3, 0), (0, -8), 1.6, 1.2, WOOD_D, z=1); c.capsule((3, 0), (0, -8), 1.6, 1.2, WOOD_D, z=1)
    c.capsule((0, -60), (8, -50), 0.6, 0.6, RED, z=3)
    # kartal
    c.capsule((4, -76), (12, -62), 6.0, 3.0, EAGLE, z=6)            # gövde
    c.poly([(9, -80), (16, -74), (20, -60), (14, -58), (6, -68)], Mat(ramp(24, 0.5, 0.26)), z=8, bevel=2, height=2,
           paint=[(lambda lu, lv, px, py: ((px + py * 0.5) % 4) < 0.8, EAGLE)])   # kanat
    c.poly([(14, -60), (20, -60), (22, -50), (12, -52)], EAGLE, z=5, bevel=1, height=1)  # kuyruk
    c.ellipse((0, -84), 4.6, 4.2, EAGLE_H, z=10)
    c.poly([(-4, -86), (-9, -84), (-8, -81), (-4, -82)], BEAK, z=12, bevel=0.6, height=0.6)
    c.dot((-1.5, -86), M['black'], z=20, size=2)
    c.dot((-2, -85), BEAK, z=21, size=1)
    for s in (-1, 1):
        c.capsule((3 + s * 1.5, -68), (2 + s * 2, -65), 0.9, 0.7, BEAK, z=9)
    return c.c


def decor_at():
    """Eğerli doru at: sola bakar; kara yele, kızıl kilim eğer örtüsü, altın koşum."""
    c = HC(110, 84, 55, 80)
    legs = [((14, -38), (16, -20), (15, 0), -6), ((22, -40), (26, -22), (24, 0), 2), ((-16, -38), (-18, -20), (-17, 0), -6), ((-22, -40), (-21, -20), (-23, 0), 2)]
    for hip, knee, foot, z in legs:
        mat = HORSE_D if z < 0 else HORSE
        c.capsule(hip, knee, 4.4, 2.8, mat, z=z)
        c.capsule(knee, foot, 2.6, 2.1, mat, z=z)
        c.ellipse((foot[0] - 0.5, foot[1] - 1.5), 2.4, 1.8, BLACK, z=z + 1)
    c.ellipse((2, -44), 28, 13, HORSE, z=4)
    c.ellipse((22, -44), 11, 11, HORSE, z=5)
    c.ellipse((-18, -44), 11, 11.5, HORSE, z=5)
    c.capsule((-20, -48), (-33, -68), 10, 6.4, HORSE, z=6)
    c.capsule((-34, -71), (-47, -57), 6.4, 4.2, HORSE, z=8)
    c.dot((-37, -68), M['black'], z=30, size=2)
    c.capsule((-31, -74), (-30, -80), 1.5, 0.7, HORSE, z=7)
    c.capsule((-46, -58), (-47, -56), 1.6, 1.6, BLACK, z=9)
    # yele ve kuyruk
    for k in range(9):
        t = k / 8
        x = -24 - t * 10; y = -56 - t * 18
        c.capsule((x, y), (x + 3.5, y + 5), 2.0, 1.0, BLACK, z=10)
    c.capsule((29, -50), (36, -40), 3.0, 2.4, BLACK, z=3)
    c.capsule((36, -40), (36, -18), 2.4, 1.2, BLACK, z=3)
    # koşum: dizgin ve alın bandı (altın)
    c.capsule((-38, -71), (-44, -61), 0.8, 0.8, GOLD, z=42)
    c.capsule((-42, -60), (-24, -52), 0.5, 0.5, LEATHER, z=42)
    c.capsule((-29, -55), (-20, -42), 0.9, 0.9, RED, z=41)
    for k in range(3):
        c.dot((-27 + k * 2.5, -50 + k * 3), GOLD, z=44, size=2)
    # eğer örtüsü (kilim) + eğer
    c.poly([(-10, -56), (16, -56), (18, -34), (-12, -34)], RED, z=42, bevel=1.5, height=1.2,
           paint=[(lambda lu, lv, px, py: (np.abs(px + 10) < 1.4) | (np.abs(px - 17) < 1.4) | (py > -36.4), GOLD),
                  (diamonds(9, -45, 3.2, 1.0, -1), BLUE)])
    for k in range(8):
        c.capsule((-10 + k * 4, -34), (-10 + k * 4, -31), 0.6, 0.5, GOLD, z=43)
    c.poly([(-8, -60), (12, -60), (15, -55), (-11, -55)], LEATHER, z=44, bevel=1.5, height=2)
    c.capsule((-9, -61), (-11, -66), 1.6, 1.2, LEATHER, z=45)
    c.capsule((12, -61), (14, -65), 1.6, 1.2, LEATHER, z=45)
    c.capsule((2, -55), (2, -30), 0.5, 0.5, LEATHER, z=46)
    c.ellipse((2, -28), 2.4, 1.6, GOLD, z=47)
    return c.c


# ------------------------------------------------------------ Ozan köşesi
def _kilim(c, x0, y0, x1, y1, field, z, seed=1):
    """Asılı / gerili kilim deseni: kenar kuşakları, göbek madalyonları."""
    cx = (x0 + x1) / 2; cy = (y0 + y1) / 2
    border = lambda lu, lv, px, py: (px < x0 + 5) | (px > x1 - 5) | (py < y0 + 5) | (py > y1 - 5)
    border_line = lambda lu, lv, px, py: (np.abs(px - (x0 + 5)) < 0.7) | (np.abs(px - (x1 - 5)) < 0.7) | (np.abs(py - (y0 + 5)) < 0.7) | (np.abs(py - (y1 - 5)) < 0.7)
    bz = lambda lu, lv, px, py: border(lu, lv, px, py) & ((((px + py) % 5) < 1.0) | (((px - py) % 5) < 1.0))
    w = (x1 - x0 - 10)
    n = max(1, int(round(w / 26)))
    per = w / n
    med = lambda lu, lv, px, py: (np.abs(((px - x0 - 5) % per) - per / 2) * (y1 - y0) / per * 0.9 + np.abs(py - cy)) < (y1 - y0) * 0.32
    med_in = lambda lu, lv, px, py: (np.abs(((px - x0 - 5) % per) - per / 2) * (y1 - y0) / per * 0.9 + np.abs(py - cy)) < (y1 - y0) * 0.2
    med_c = lambda lu, lv, px, py: (np.abs(((px - x0 - 5) % per) - per / 2) * (y1 - y0) / per * 0.9 + np.abs(py - cy)) < (y1 - y0) * 0.08
    hooks = lambda lu, lv, px, py: (~border(lu, lv, px, py)) & ((((px - x0) % 7) < 1) & (((py - y0) % 7) < 1))
    c.rect(x0, y0, x1, y1, field, z=z, bevel=1.2, height=0.8,
           paint=[(border, BLUE), (bz, GOLD), (border_line, FELT_W), (med, BLUE), (med_in, GOLD), (med_c, RED), (hooks, GOLD_D)])


def decor_hali_sergi():
    """Ozan köşesi: iki direk arasında gerili büyük kilim, önünde minderler, alçak sehpa, kımız testisi."""
    c = HC(130, 96, 65, 92)
    for x in (-54, 54):
        c.capsule((x, 0), (x, -84), 2.0, 1.7, WOOD_R, z=0)
        c.ellipse((x, -86), 2.8, 2.8, GOLD, z=2)
    c.capsule((-56, -80), (56, -80), 1.6, 1.6, WOOD_D, z=1)
    _kilim(c, -48, -78, 48, -22, RED, z=2)
    for k in range(25):
        x = -46 + k * 4
        c.capsule((x, -22), (x, -18), 0.6, 0.5, FELT_C, z=3)
    # minderler
    for x, m, rx in ((-30, BLUE, 16), (0, RED, 18), (30, M['turq'], 15)):
        c.ellipse((x, -6), rx, 6, m, z=10 + (x == 0) * 2, paint=[(lambda lu, lv, px, py: np.abs(lv) < 0.14, GOLD)])
        for s in (-1, 1):
            c.dot((x + s * (rx - 1), -6), GOLD, z=20, size=2)
    # sehpa + testi + kâseler
    c.rect(36, -14, 60, -11, WOOD_R, z=14)
    c.rect(38, -11, 40, 0, WOOD_D, z=13); c.rect(56, -11, 58, 0, WOOD_D, z=13)
    c.ellipse((48, -20), 5, 6, BRONZE, z=16)
    c.capsule((48, -26), (48, -29), 2, 1.6, BRONZE, z=17)
    c.capsule((52, -24), (55, -18), 0.8, 0.8, BRONZE, z=17)
    c.ellipse((40, -15.5), 3, 1.6, WOOD, z=18); c.ellipse((57, -15.5), 3, 1.6, WOOD, z=18)
    return c.c


def decor_hali(seed=1):
    """Yere serili kilim (yandan, hafif üstten): ince şerit + saçak."""
    c = HC(96, 12, 48, 8)
    f = RED if seed == 1 else BLUE
    b = BLUE if seed == 1 else RED
    pat = [(lambda lu, lv, px, py: (np.abs(px) > 40) | (py < -4.6) | (py > 1.6), b),
           (lambda lu, lv, px, py: (np.abs(np.abs(px) - 40) < 0.6) | (np.abs(py + 4.6) < 0.5) | (np.abs(py - 1.6) < 0.5), GOLD),
           (AND(lambda lu, lv, px, py: np.abs(px) < 39, diamonds(13, -1.5, 2.6, 0.9, 6.5)), GOLD),
           (AND(lambda lu, lv, px, py: np.abs(px) < 39, diamonds(13, -1.5, 1.0, None, 6.5)), FELT_W)]
    c.poly([(-44, -6), (44, -6), (46, 3), (-46, 3)], f, z=0, bevel=0.8, height=0.5, paint=pat)
    for s in (-1, 1):
        for k in range(5):
            y = -5 + k * 2
            c.capsule((s * 45, y), (s * 47.5, y + 0.5), 0.5, 0.4, FELT_C, z=1)
    return c.c


def decor_yol(seed=1):
    """Taş döşeme: yassı, düzensiz yassı taşlar (yandan, hafif üstten), aralarda ot."""
    c = HC(76, 12, 38, 6)
    rng = random.Random(seed * 17)
    x = -36.0
    while x < 34:
        w = rng.uniform(8, 14)
        h = rng.uniform(3.2, 4.6)
        m = STONE if rng.random() < 0.7 else STONE_W
        c.poly([(x, -h + 1), (x + w - 1.5, -h + rng.uniform(0, 1.2)), (x + w, 3), (x - 0.5, 3)], m, z=rng.uniform(0, 1), bevel=1.5, height=1.2,
               paint=[(lambda lu, lv, px, py, s=rng.random(): _hash(px * 0.5, py * 0.5, s) < 0.12, ROCK)])
        if rng.random() < 0.5:
            c.capsule((x + w + 0.5, 2), (x + w + 1, -2), 0.6, 0.4, M['grass'], z=4)
        x += w + rng.uniform(1.2, 2.5)
    return c.c


# ------------------------------------------------------------ ateş ve ışık
def decor_mangal():
    """Tunç ateş tası: üç kıvrık ayak, süslü kâse, yüksek alev."""
    c = HC(36, 56, 18, 52)
    for s in (-1, 0, 1):
        c.capsule((s * 10, 0), (s * 5, -18), 1.3, 1.1, BRONZE, z=2 - abs(s))
        c.ellipse((s * 10.5, -1), 2.0, 1.2, BRONZE, z=3)
    c.poly([(-14, -22), (14, -22), (10, -15), (-10, -15)], BRONZE, z=6, bevel=2, height=2,
           paint=[(zig(-18.5, 1.2, 3, 0.6), GOLD), (hband(-22, -20.8), GOLD)])
    c.ellipse((0, -14), 3, 2, GOLD, z=8)
    c.ellipse((0, -23), 12, 2.6, EMBER, z=7, depth=0.3)
    c.flame(0, -23, 1.25, z=12)
    c.flame(-6, -22, 0.7, z=11)
    c.flame(6, -22, 0.75, z=11)
    return c.c


def decor_kandil():
    """Uzun tunç kandil: ince gövde, düğümlü sap, tepede ateş tası."""
    c = HC(30, 100, 15, 96)
    c.ellipse((0, -2), 9, 2.6, BRONZE, z=0)
    c.capsule((0, -3), (0, -70), 1.5, 1.2, BRONZE, z=2)
    for y in (-20, -44, -66):
        c.ellipse((0, y), 3.2, 2.2, GOLD, z=4)
    c.poly([(-10, -76), (10, -76), (6, -69), (-6, -69)], BRONZE, z=6, bevel=1.5, height=1.5, paint=[(hband(-76, -75), GOLD)])
    c.ellipse((0, -76.5), 8.6, 1.8, EMBER, z=7, depth=0.3)
    c.flame(0, -76, 1.0, z=12)
    return c.c


def decor_fener():
    """Kancalı direkte fener: ahşap direk, kıvrık demir kol, tunç kafesli kehribar fener."""
    c = HC(40, 104, 12, 100)
    c.capsule((0, 0), (0, -94), 1.8, 1.4, WOOD_D, z=0)
    c.capsule((0, -90), (14, -94), 0.9, 0.9, IRON, z=2)
    c.capsule((14, -94), (20, -88), 0.9, 0.9, IRON, z=2)
    c.capsule((20, -88), (20, -82), 0.4, 0.4, IRON, z=2)
    c.poly([(15, -82), (25, -82), (23, -79), (17, -79)], BRONZE, z=4, bevel=0.8, height=0.8)
    c.rect(16.5, -79, 23.5, -66, GLASS, z=3, bevel=1, height=1)
    for x in (16.8, 20, 23.2):
        c.capsule((x, -79), (x, -66), 0.45, 0.45, BRONZE, z=6)
    c.poly([(15, -66), (25, -66), (23, -63), (17, -63)], BRONZE, z=4, bevel=0.8, height=0.8)
    c.dot((19.5, -61.5), GOLD, z=8, size=2)
    # direkte bağlı çaputlar
    for k, m in enumerate((RED, SKY, FELT_W)):
        c.capsule((0, -60 + k * 3), (-4 - k, -50 + k * 4), 0.9, 0.7, m, z=5)
    return c.c


def decor_tug(red=True):
    """Tuğ: uzun direk, altın mızrak tepelik + hilal, at kılı püskül halkası, çatallı uzun sancak."""
    c = HC(56, 170, 12, 166)
    f = RED if red else BLUE
    c.capsule((0, 0), (0, -150), 1.9, 1.5, WOOD_D, z=0)
    c.capsule((-3, 0), (3, 0), 2.6, 2.6, STONE, z=1)
    # tepelik
    c.poly([(-2.2, -150), (2.2, -150), (0, -166)], GOLD, z=6, bevel=0.9, height=1)
    c.ellipse((0, -150), 3.4, 1.6, GOLD_D, z=7)
    for s in (-1, 1):
        c.capsule((0, -151), (s * 5, -156), 0.9, 0.7, GOLD, z=6)
        c.capsule((s * 5, -156), (s * 5.5, -161), 0.8, 0.5, GOLD, z=6)
    # püskül
    for k in range(13):
        a = (k - 6) / 6.0
        c.capsule((a * 3.5, -148), (a * 8, -124 + abs(a) * 5), 1.4, 0.7, BLACK if (k % 4) else HAIR_W, z=4 + (k % 3) * 0.5)
    c.ellipse((0, -147), 4.5, 2.2, f, z=8)
    # sancak: direkten sağa çatallı uzun bez
    yb = -118
    flag = [(1.5, yb), (44, yb + 3), (36, yb + 13), (44, yb + 23), (1.5, yb + 28)]
    c.poly(flag, f, z=3, bevel=1.6, height=1.0,
           paint=[(lambda lu, lv, px, py: (py < yb + 2.6 + px * 0.07) | (py > yb + 25.4 - px * 0.07), GOLD),
                  (lambda lu, lv, px, py: (np.abs(px - 16) + np.abs(py - (yb + 14)) < 6.5) & (np.abs(px - 16) + np.abs(py - (yb + 14)) > 4.6), GOLD),
                  (lambda lu, lv, px, py: (np.abs(px - 16) < 0.9) & (np.abs(py - (yb + 14)) < 4), GOLD)])
    c.capsule((0, yb + 1), (5, yb + 1), 1.0, 1.0, GOLD_D, z=6)
    return c.c


# ------------------------------------------------------------ taşlar
def decor_balbal(seed=1):
    """Balbal: kaba yontulmuş taş insan, elinde kadeh, bıyıklı yüz."""
    c = HC(30, 60, 15, 56)
    m = STONE if seed == 1 else STONE_W
    c.poly([(-9, 0), (9, 0), (10, -30), (8, -38), (-8, -38), (-10, -30)], m, z=0, bevel=4, height=3,
           paint=[(lambda lu, lv, px, py: (np.abs(py + 22) < 0.7) & (np.abs(px) < 7), ROCK), (lambda lu, lv, px, py: _hash(px, py, seed) < 0.025, MOSS)])
    c.ellipse((0, -46), 7, 8.5, m, z=1, paint=[(lambda lu, lv, px, py: _hash(px, py, seed + 3) < 0.02, MOSS)])
    # yüz: kaş, göz, bıyık
    c.capsule((-5, -49), (-1, -48.5), 0.6, 0.6, ROCK, z=12)
    c.capsule((1, -48.5), (5, -49), 0.6, 0.6, ROCK, z=12)
    c.dot((-3.5, -47), Mat(ramp(220, 0.2, 0.2)), z=14, size=2); c.dot((2.0, -47), Mat(ramp(220, 0.2, 0.2)), z=14, size=2)
    c.capsule((-4.5, -41.5), (-0.5, -43), 0.6, 0.6, ROCK, z=12)
    c.capsule((0.5, -43), (4.5, -41.5), 0.6, 0.6, ROCK, z=12)
    # kollar ve kadeh (kabartma)
    c.capsule((-8, -34), (-2, -26), 1.6, 1.4, m, z=8)
    c.capsule((8, -34), (3, -22), 1.6, 1.4, m, z=8)
    c.poly([(-4, -30), (2, -30), (1, -25), (-3, -25)], m, z=10, bevel=1, height=1)
    if seed == 2:
        c.ellipse((-1, -31), 2.6, 1.0, KUT, z=14)
    return c.c


def decor_kurgan():
    """Dikili taş halkası: farklı boylarda yassı taşlar, yosun; ortadaki taşta ışıl Göktürk runları."""
    c = HC(120, 64, 60, 60)
    rng = random.Random(31)
    stones = [(-48, 20, 6), (-32, 34, 7), (-14, 26, 6), (2, 52, 9), (20, 30, 7), (36, 38, 7), (50, 18, 6)]
    for x, h, w in stones:
        z = 0 if abs(x) > 30 else 4
        c.poly([(x - w, 0), (x + w, 0), (x + w * 0.8, -h * 0.85), (x + w * 0.2, -h), (x - w * 0.7, -h * 0.9)], STONE if rng.random() < 0.6 else ROCK,
               z=z, bevel=w * 0.6, height=w * 0.4, paint=[(lambda lu, lv, px, py: _hash(px, py, x) < 0.08, MOSS)])
    # runlar (Orhun yazısından basit biçimler)
    rx = 2
    for k, ry in enumerate((-44, -36, -28, -20, -12)):
        sh = k % 3
        if sh == 0:
            c.capsule((rx - 2.5, ry - 3), (rx + 2.5, ry + 3), 0.6, 0.6, KUT, z=30)
            c.capsule((rx + 2.5, ry - 3), (rx - 2.5, ry + 3), 0.6, 0.6, KUT, z=30)
        elif sh == 1:
            c.capsule((rx, ry - 3.5), (rx, ry + 3.5), 0.6, 0.6, KUT, z=30)
            c.capsule((rx, ry - 3.5), (rx + 3, ry - 1), 0.6, 0.6, KUT, z=30)
        else:
            c.capsule((rx - 2.5, ry + 3), (rx, ry - 3), 0.6, 0.6, KUT, z=30)
            c.capsule((rx, ry - 3), (rx + 2.5, ry + 3), 0.6, 0.6, KUT, z=30)
    for x in range(-56, 58, 5):
        c.capsule((x, 0), (x + rng.uniform(-2, 2), -rng.uniform(3, 7)), 0.6, 0.4, M['grass'], z=20)
    return c.c


def decor_kapi():
    """Taç kapı: Kut Kapısı'nın arkasında; çini kuşaklı taş ayaklar, ışıl runlu kemer, koçboynuzu tepelik, güneş kursu."""
    c = HC(170, 176, 85, 172)
    ip = 44          # iç açıklık yarı genişliği
    pw = 16          # ayak genişliği
    for s in (-1, 1):
        x0, x1 = (ip, ip + pw) if s > 0 else (-ip - pw, -ip)
        c.rect(x0, -112, x1, 0, STONE_W, z=0, bevel=3, height=3,
               paint=[(lambda lu, lv, px, py, x0=x0, x1=x1: (py > -96) & (py < -16) & (px > x0 + 3) & (px < x1 - 3), TILE),
                      (lambda lu, lv, px, py, x0=x0, x1=x1: (py > -96) & (py < -16) & (px > x0 + 3) & (px < x1 - 3) &
                       ((np.abs(((px - x0 - pw / 2) % 10) - 5) + np.abs(((py + 16) % 10) - 5)) < 2.2), FELT_W),
                      (lambda lu, lv, px, py, x0=x0, x1=x1: (py > -96) & (py < -16) & ((np.abs(px - x0 - 3) < 0.8) | (np.abs(px - x1 + 3) < 0.8)), GOLD_D),
                      (lambda lu, lv, px, py: (np.abs(py + 96) < 0.8) | (np.abs(py + 16) < 0.8), GOLD_D),
                      (hband(-8, 0.1), STONE)])
        c.rect(x0 - 3, -10, x1 + 3, 0, STONE, z=2, bevel=2, height=2)
        c.rect(x0 - 3, -118, x1 + 3, -108, STONE, z=2, bevel=2, height=2)
    # kemer (yarım daire) ve üst kuşak
    pts_o = [(math.cos(a) * (ip + pw + 2), -112 - math.sin(a) * 34) for a in np.linspace(0, math.pi, 30)]
    pts_i = [(math.cos(a) * ip, -112 - math.sin(a) * 22) for a in np.linspace(math.pi, 0, 30)]
    c.poly(pts_o + pts_i, STONE_W, z=1, bevel=3, height=3,
           paint=[(lambda lu, lv, px, py: (py < -118) & (((px * px) / ((ip + pw * 0.5) ** 2) + ((py + 112) ** 2) / (28 ** 2)) > 0.86) &
                   (((px * px) / ((ip + pw * 0.5) ** 2) + ((py + 112) ** 2) / (28 ** 2)) < 1.08), TILE_D)])
    # runlar kemer üzerinde (ışıl)
    for k in range(9):
        a = math.pi * (0.12 + 0.76 * k / 8)
        rx = math.cos(a) * (ip + pw * 0.5); ry = -112 - math.sin(a) * 28
        if k % 2:
            c.capsule((rx - 1.6, ry - 2), (rx + 1.6, ry + 2), 0.55, 0.55, KUT, z=30)
            c.capsule((rx + 1.6, ry - 2), (rx - 1.6, ry + 2), 0.55, 0.55, KUT, z=30)
        else:
            c.capsule((rx, ry - 2.4), (rx, ry + 2.4), 0.55, 0.55, KUT, z=30)
            c.capsule((rx, ry - 2.4), (rx + 2, ry - 0.5), 0.55, 0.55, KUT, z=30)
    # güneş kursu ve koçboynuzu
    c.ellipse((0, -150), 10, 10, GOLD, z=10)
    c.ellipse((0, -150), 6, 6, KUT, z=12)
    for k in range(12):
        a = k * math.tau / 12
        c.capsule((math.cos(a) * 10.5, -150 + math.sin(a) * 10.5), (math.cos(a) * 14, -150 + math.sin(a) * 14), 1.0, 0.5, GOLD, z=9)
    for s in (-1, 1):
        pts = [(s * (12 + 10 * math.sin(t)), -142 - 12 * math.cos(t) + t * 2) for t in np.linspace(0, 1.25 * math.pi, 14)]
        for p0, p1 in zip(pts, pts[1:]):
            c.capsule(p0, p1, 2.2, 2.0, GOLD_D, z=8)
    # ayak dibinde tunç kandil kâseleri (ışık Level'den)
    for s in (-1, 1):
        x = s * (ip + pw / 2)
        c.ellipse((x, -119), 7, 2, BRONZE, z=6)
        c.flame(x, -120, 0.75, z=14)
    return c.c


def decor_kazan():
    """Sacayak üstünde kazan, altında ateş."""
    c = HC(56, 64, 28, 60)
    for s in (-1, 1):
        c.capsule((s * 20, 0), (0, -54), 1.3, 1.1, WOOD_D, z=0 if s < 0 else 8)
    c.capsule((0, -54), (0, -40), 0.6, 0.6, IRON, z=6)
    c.ellipse((0, -28), 15, 12, IRON, z=4, paint=[(lambda lu, lv, px, py: np.abs(py + 36) < 0.8, BRONZE)])
    c.ellipse((0, -38), 14, 2.6, Mat(ramp(30, 0.4, 0.75)), z=7, depth=0.2)
    c.capsule((-14, -38), (14, -38), 1.0, 1.0, BRONZE, z=9)
    for k in range(5):
        c.capsule((-10 + k * 5, -2), (-8 + k * 4, -6), 1.6, 1.4, WOOD if k % 2 else Mat(ramp(24, 0.5, 0.3)), z=10)
    c.flame(0, -4, 1.0, z=12)
    c.flame(-6, -3, 0.6, z=11)
    c.flame(6, -3, 0.6, z=11)
    return c.c


def decor_seki():
    """Kapı sekisinin yüzü: yontma taş bloklar, çini kuşak, altın pervaz (1 karoluk basamağın toprak yüzünü örter)."""
    c = HC(34, 30, 4, 28)
    c.rect(-4, -26, 30, 2, STONE_W, z=0, bevel=1.5, height=1.5,
           paint=[(lambda lu, lv, px, py: (np.abs(py + 13) < 0.6) | ((np.abs(((px + (np.floor((py + 26) / 13) % 2) * 7) % 14)) < 0.7) & (py > -24)), STONE),
                  (lambda lu, lv, px, py: (py > -9) & (py < -4), TILE),
                  (lambda lu, lv, px, py: (py > -9) & (py < -4) & ((np.abs((px % 6) - 3) + np.abs(py + 6.5)) < 1.6), FELT_W),
                  (lambda lu, lv, px, py: py < -23.5, GOLD_D)])
    return c.c


DECOR = {
    'yh_seki': decor_seki,
    'yh_otag': decor_otag,
    'yh_cadir': decor_cadir,
    'yh_kayin': decor_kayin,
    'yh_sunak': decor_sunak,
    'yh_pinar': decor_pinar,
    'yh_demirhane': decor_demirhane,
    'yh_ors': decor_ors,
    'yh_kartal': decor_kartal,
    'yh_at': decor_at,
    'yh_hali_sergi': decor_hali_sergi,
    'yh_hali_1': lambda: decor_hali(1),
    'yh_hali_2': lambda: decor_hali(2),
    'yh_yol_1': lambda: decor_yol(1),
    'yh_yol_2': lambda: decor_yol(2),
    'yh_yol_3': lambda: decor_yol(3),
    'yh_mangal': decor_mangal,
    'yh_kandil': decor_kandil,
    'yh_fener': decor_fener,
    'yh_tug_k': lambda: decor_tug(True),
    'yh_tug_m': lambda: decor_tug(False),
    'yh_balbal_1': lambda: decor_balbal(1),
    'yh_balbal_2': lambda: decor_balbal(2),
    'yh_kurgan': decor_kurgan,
    'yh_kapi': decor_kapi,
    'yh_kazan': decor_kazan,
}


def export(dmeta, only=(), save_fn=None):
    """Süsleri assets/decor'a yaz; dmeta'ya ("k": 1.5) ekle."""
    def save(arr, path):
        to_img(arr).save(path)
    for k, fn in DECOR.items():
        if only and k not in only:
            continue
        cv = fn()
        rgba = cv.shade(rim_amt=0.25)
        save(rgba, os.path.join(A, 'decor', k + '.png'))
        save(cv.normal_map(rgba[..., 3]), os.path.join(A, 'decor', k + '_n.png'))
        has_glow = bool(cv.emis.max() > 0)
        gp = os.path.join(A, 'decor', k + '_e.png')
        if has_glow:
            g = np.zeros((cv.h, cv.w, 4)); g[..., :3] = np.clip(cv.emis, 0, 1); g[..., 3] = (cv.emis.max(axis=2) > 0)
            save(g, gp)
        elif os.path.exists(gp):
            os.remove(gp)
        dmeta[k] = {'size': [cv.w, cv.h], 'origin': [cv.ox, cv.oy], 'glow': has_glow, 'k': K}
    return dmeta


def preview(names, path, scale=2, bg=(34, 30, 44)):
    from PIL import Image
    ims = [Image.open(os.path.join(A, 'decor', n + '.png')) for n in names]
    W_ = sum(i.width for i in ims) + 8 * (len(ims) + 1)
    H_ = max(i.height for i in ims) + 16
    sheet = Image.new('RGBA', (W_, H_), bg + (255,))
    x = 8
    for im in ims:
        sheet.alpha_composite(im, (x, H_ - 8 - im.height))
        x += im.width + 8
    sheet = sheet.resize((W_ * scale, H_ * scale), Image.NEAREST)
    sheet.save(path)


if __name__ == '__main__':
    only = [a for a in sys.argv[1:] if not a.startswith('-')]
    mp = os.path.join(A, 'decor', 'decor.json')
    dmeta = json.load(open(mp, encoding='utf-8'))
    export(dmeta, only)
    json.dump(dmeta, open(mp, 'w', encoding='utf-8'), indent=1)
    print('yurt_hd', len(DECOR), 'süs')
