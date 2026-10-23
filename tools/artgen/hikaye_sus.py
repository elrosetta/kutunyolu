"""v42 Güneş Ana hikâyesi: bölümlere kurulan anlatı sahnesi süsleri (stil v2 mürekkep-cel, inkprop.Prop).

* gun_sunagi: kırık güneş kursu sunağı — taş kaide, ikiye yarılmış ışınlı taş disk (bir yarısı yere düşmüş), yarığından
  altın ışık sızar (ışıma). Tan töreninin sunağı; Erlik'in geldiği gece kırıldı.
* bitig_tasi: bitig taşı (yazıt / kaya resmi) — ak taş dikilitaş, üstüne kazınmış mit: ışınlı kadın, zincir, ağaç,
  davulcu kız; kazıklar ışır (okunabilir: Level yanına gelince yazıt satırını gösterir).
* zincirli_kus: zincirli tan kuşu — kara kazığa zincirle bağlı, kanatları yarı açık altın ruh kuşu (ışıma).
* tan_halkasi: yanmış tan töreni çemberi — taş halka, kül, kömürleşmiş kazıklar, yarık kam davulu, söndürülmüş ocak.
* altin_yaprak: Ulu Kayın'ın altın yaprağı (yurtta her örgüyle bir küme; düşen yaprak parçacığı).

    python export_sus.py --hikaye     (assets/decor/<ad>_v2.png + _e, sus_v2.json)
"""
import math

import numpy as np

from inkprop import (Prop, STONE, STONE_W, STONE_D, WOOD_D, IRON, GOLD, LEATHER, FELT_C, RED, INK, grass_tufts)
from inkkit import Ink

ASH = Ink('#5a5658', '#2e2a34', '#86828a', name='kül')
CHAR = Ink('#2c2626', '#141016', '#4a4040', name='kömür')
SUNG = (1.0, 0.78, 0.36)
SUNG_GL = (1.0, 0.62, 0.2)
CARVE = (0.95, 0.74, 0.38)


def gun_sunagi():
    P = Prop(110, 96, 55, 92)
    cv = P.cv
    # kaide: iki basamaklı taş
    cv.shape(cv.blob([(-40, 0.5, 0.0), (-38, -9), (38, -9.5), (41, 0.5, 0.0)]), STONE_D, z=0.0, sd=1.6, hi=0.3)
    cv.shape(cv.blob([(-28, -8, 0.0), (-27, -18), (27, -18.5), (29, -8, 0.0)]), STONE, z=0.1, sd=1.8, hi=0.4,
             details=[('ink', [(-20, -13), (-6, -13.5)], 0.6, (0.3, 0.3)), ('ink', [(8, -12), (20, -12.5)], 0.6, (0.3, 0.3))])
    # ayakta kalan yarım disk (sol), ışınlı kenar
    cx, cy, r = -2.0, -48.0, 28.0
    half = [(cx + math.cos(a) * r, cy + math.sin(a) * r) for a in np.linspace(math.pi * 0.42, math.pi * 1.62, 18)]
    crack = [(cx + 6, cy - 27), (cx + 2, cy - 14), (cx + 7, cy - 4), (cx + 1, cy + 8), (cx + 5, cy + 20), (cx + 2, cy + 27)]
    cv.shape(cv.poly(half + crack[::-1][1:]), STONE_W, z=0.2, sd=2.2, hi=0.5)
    for a in np.linspace(math.pi * 0.55, math.pi * 1.5, 7):
        p0 = (cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55)
        p1 = (cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.9)
        cv.stroke([p0, p1], 1.6, z=0.25, col=(0.42, 0.4, 0.5), taper=(0.2, 0.5))
    cv.stroke([(cx + math.cos(a) * r * 0.42, cy + math.sin(a) * r * 0.42) for a in np.linspace(math.pi * 0.5, math.pi * 1.55, 10)], 1.4, z=0.25,
              col=(0.42, 0.4, 0.5))
    # yarıktan sızan altın ışık
    cv.stroke(crack, 2.6, z=0.3, col=SUNG, taper=(0.3, 0.3), glow=SUNG_GL)
    # düşmüş öbür yarı (sağda yere yaslı)
    fx, fy = 26.0, -10.0
    fall = [(fx + math.cos(a) * 20 * 0.95, fy + math.sin(a) * 20 * 0.6) for a in np.linspace(-math.pi * 0.95, -math.pi * 0.05, 14)]
    cv.shape(cv.poly(fall + [(fx + 19, fy + 1), (fx - 19, fy + 1)]), STONE, z=0.35, sd=2.0, hi=0.45)
    for a in np.linspace(-math.pi * 0.85, -math.pi * 0.15, 5):
        cv.stroke([(fx + math.cos(a) * 9, fy + math.sin(a) * 6), (fx + math.cos(a) * 17, fy + math.sin(a) * 10.5)], 1.3, z=0.4, col=(0.4, 0.38, 0.48))
    cv.stroke([(fx - 17, fy - 1), (fx - 6, fy - 3), (fx + 6, fy - 2), (fx + 17, fy - 1)], 1.8, z=0.42, col=SUNG, glow=SUNG_GL)
    # sunakta sönmüş kandil ve çaput
    cv.shape(cv.ellipse((-20, -20), 4.5, 2.2), GOLD, z=0.5, sd=0.8, hi=0.6)
    cv.stroke([(-34, -9), (-38, -24), (-36, -36)], 1.0, z=0.05, col=RED.base, taper=(0.1, 0.5))
    grass_tufts(cv, -46, 48, 0, 22, 3.0, 41)
    return P.done(outer=1.1, rim=0.3)


def bitig_tasi():
    P = Prop(60, 104, 30, 100)
    cv = P.cv
    slab = cv.blob([(-17, 0.5, 0.0), (-19, -40), (-16, -78), (-8, -92), (4, -95), (14, -86), (18, -60), (17, -20), (18, 0.5, 0.0)])
    cv.shape(slab, STONE_W, z=0.0, sd=3.0, hi=0.55, bounce=0.2)
    gl = (0.5, 0.32, 0.1)
    # kazı: ışınlı kadın (üstte), beş ışın
    cv.stroke([(-1, -80), (-1, -66)], 1.6, z=0.2, col=CARVE, glow=gl)
    cv.fill(cv.ellipse((-1, -83), 2.6, 3.0), CARVE, z=0.2, glow=gl)
    for i, a in enumerate(np.linspace(-2.6, -0.55, 5)):
        cv.stroke([(-1 + math.cos(a) * 4, -84 + math.sin(a) * 4), (-1 + math.cos(a) * 10, -84 + math.sin(a) * 9)], 1.2, z=0.2, col=CARVE, glow=gl)
    cv.stroke([(-9, -70), (-1, -74), (7, -70)], 1.3, z=0.2, col=CARVE, glow=gl)
    cv.stroke([(-6, -58), (-1, -66), (4, -58)], 1.3, z=0.2, col=CARVE, glow=gl)
    # zincir: kadının altında halkalar
    for k in range(4):
        cv.stroke([(-10 + k * 6, -52), (-7 + k * 6, -54), (-4 + k * 6, -52), (-7 + k * 6, -50), (-10 + k * 6, -52)], 1.0, z=0.2, col=(0.3, 0.28, 0.36))
    # ağaç: gövde ve üç dal
    cv.stroke([(-2, -18), (-2, -40)], 1.6, z=0.2, col=(0.32, 0.3, 0.38))
    for dx in (-8, 0, 8):
        cv.stroke([(-2, -34), (-2 + dx, -44)], 1.1, z=0.2, col=(0.32, 0.3, 0.38))
    for dx in (-6, 2):
        cv.stroke([(-2, -18), (-2 + dx, -10)], 1.0, z=0.2, col=(0.32, 0.3, 0.38))
    # davulcu kız (sağ altta)
    cv.fill(cv.ellipse((10, -24), 1.6, 1.8), (0.32, 0.3, 0.38), z=0.2)
    cv.stroke([(10, -22), (10, -15), (8, -9)], 1.0, z=0.2, col=(0.32, 0.3, 0.38))
    cv.fill(cv.ellipse((6, -18), 3.0, 3.0), (0.32, 0.3, 0.38), z=0.21, alpha=0.6)
    # yosun / çatlak
    cv.stroke([(13, -70), (9, -60), (12, -50)], 0.8, z=0.25, col=(0.4, 0.38, 0.46))
    grass_tufts(cv, -22, 22, 0, 12, 3.0, 42)
    return P.done(outer=1.1, rim=0.3)


def zincirli_kus():
    P = Prop(76, 84, 38, 80)
    cv = P.cv
    # kazık
    cv.shape(cv.capsule((-12, 0), (-12, -46), 2.6, 2.0), WOOD_D, z=0.0, sd=1.0, hi=0.2)
    cv.shape(cv.blob([(-16, -46), (-12, -50), (-8, -46), (-12, -44)]), WOOD_D, z=0.05, sd=0.5)
    # zincir: kazıktan kuşun ayağına sarkık
    pts = [(-12 + t * 22, -40 + math.sin(t * math.pi) * 9 - t * 8) for t in np.linspace(0, 1, 9)]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        cv.stroke([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - (1.2 if i % 2 else -1.2)), b], 1.3, z=0.3 + i * 0.001, col=(0.2, 0.2, 0.26))
    # kuş: altın, kanatlar yarı açık, kuyruk uzun
    bx, by = 12.0, -54.0
    cv.fill(cv.blob([(bx - 9, by + 4), (bx - 2, by - 3), (bx + 7, by - 2), (bx + 9, by + 2), (bx + 2, by + 6)]), SUNG, z=0.5, glow=SUNG_GL)
    cv.fill(cv.ellipse((bx + 8, by - 4), 3.0, 2.6), SUNG, z=0.52, glow=SUNG_GL)
    cv.fill(cv.poly([(bx + 10.5, by - 4.5), (bx + 14, by - 3.5), (bx + 10.5, by - 2.6)]), (0.9, 0.5, 0.2), z=0.53)
    for side, sw in ((-1, 1.0), (1, 0.75)):
        wing = [(bx - 2, by - 2), (bx - 8, by - 14 * sw), (bx - 18, by - 22 * sw), (bx - 12, by - 10 * sw), (bx - 6, by - 2)]
        cv.fill(cv.blob(wing), (1.0, 0.86, 0.5), z=0.48 + side * 0.01, glow=SUNG_GL, alpha=0.95)
    for k in range(3):
        cv.stroke([(bx - 8, by + 3), (bx - 18 - k * 3, by + 10 + k * 3), (bx - 26 - k * 2, by + 6 + k * 6)], 1.6, z=0.46, col=SUNG, glow=SUNG_GL, taper=(0.1, 0.9))
    cv.fill(cv.ellipse((bx + 9, by - 4.6), 0.6, 0.6), INK, z=0.6)
    # ayakta demir halka
    cv.stroke([(bx - 2, by + 6), (bx - 2, by + 12), (bx, by + 14)], 1.2, z=0.55, col=(0.2, 0.2, 0.26))
    cv.shape(cv.ellipse((bx - 1, by + 14), 2.4, 1.6), IRON, z=0.56, sd=0.4, ol=0.6)
    # yerde düşmüş altın tüyler
    for x in (-24, 4, 22):
        cv.stroke([(x, -1), (x + 3, -3), (x + 7, -2)], 1.4, z=0.2, col=SUNG, glow=(0.4, 0.25, 0.08))
    grass_tufts(cv, -30, 30, 0, 16, 3.0, 43)
    return P.done(outer=1.1, rim=0.3)


def tan_halkasi():
    P = Prop(150, 56, 75, 50)
    cv = P.cv
    rs = np.random.default_rng(44)
    # kül yatağı
    cv.fill(cv.ellipse((0, -2), 52, 7), (0.28, 0.26, 0.3), z=0.0, alpha=0.85)
    cv.fill(cv.ellipse((0, -3), 26, 4), (0.4, 0.38, 0.42), z=0.05, alpha=0.8)
    # söndürülmüş ocak: kömür, son bir kor
    for a in (-0.4, 0.3, 0.05):
        cv.shape(cv.capsule((-11 * math.cos(a), -3 + 3 * math.sin(a)), (11 * math.cos(a), -3 - 3 * math.sin(a)), 1.8, 1.6), CHAR, z=0.1, sd=0.8)
    cv.fill(cv.ellipse((3, -4), 1.6, 0.9), (1.0, 0.45, 0.12), z=0.15, glow=(1.0, 0.35, 0.08))
    # taş halka (arka sıra küçük, ön sıra büyük)
    for i in range(14):
        a = math.pi + i / 13 * math.pi
        x, y = math.cos(a) * 54, -3 + math.sin(a) * 6
        w = rs.uniform(3.5, 5.5)
        cv.shape(cv.blob([(x - w, y + 1, 0.0), (x - w * 0.7, y - 4.5), (x + w * 0.6, y - 5), (x + w, y + 1, 0.0)]), STONE_D, z=-0.5 + i * 0.001, sd=1.0, hi=0.25)
    for i in range(9):
        x = -48 + i * 12 + rs.uniform(-2, 2)
        w = rs.uniform(4.5, 6.5)
        cv.shape(cv.blob([(x - w, 0.5, 0.0), (x - w * 0.8, -5.5), (x + w * 0.6, -6.2), (x + w, 0.5, 0.0)]), STONE, z=0.5 + i * 0.001, sd=1.3, hi=0.4)
    # kömürleşmiş tören kazıkları (dört yön), biri kırık
    for x, h, tilt in ((-62, 34, -0.1), (-30, 42, 0.05), (34, 40, -0.05), (64, 22, 0.25)):
        cv.shape(cv.capsule((x, -2), (x + tilt * h, -2 - h), 2.2, 1.6), CHAR, z=-0.3, sd=0.8, hi=0.15)
        cv.stroke([(x + tilt * h, -2 - h), (x + tilt * h + 3, -2 - h - 4)], 1.2, z=-0.29, col=CHAR.shadow, taper=(0.1, 0.9))
    # kazıklardan sarkan yanık çaputlar
    cv.stroke([(-30 + 2, -40), (-27, -32), (-29, -24)], 1.6, z=-0.2, col=(0.5, 0.2, 0.16), taper=(0.1, 0.8))
    cv.stroke([(34 - 2, -38), (36, -30), (33, -22)], 1.6, z=-0.2, col=(0.86, 0.82, 0.7), taper=(0.1, 0.8))
    # yarık kam davulu (sağ önde, yan yatmış)
    cv.shape(cv.ellipse((44, -6), 11, 6), LEATHER, z=0.7, sd=1.6, hi=0.35)
    cv.shape(cv.ellipse((44, -7), 8.5, 4.2), FELT_C, z=0.72, sd=0.8, hi=0.3)
    cv.stroke([(39, -9), (44, -6), (48, -9), (51, -6)], 1.0, z=0.74, col=INK)
    grass_tufts(cv, -72, 72, 0, 18, 2.5, 45)
    return P.done(outer=1.1, rim=0.3)


def altin_yaprak():
    P = Prop(14, 10, 7, 6)
    cv = P.cv
    leaf = cv.blob([(-5.5, 0.5), (-1, -3.2), (5.5, -1.5), (1, 2.6)])
    cv.fill(leaf, (1.0, 0.8, 0.34), z=0.0, glow=(1.0, 0.65, 0.2))
    cv.stroke([(-5, 0.3), (5, -1.2)], 0.5, z=0.1, col=(0.7, 0.45, 0.15))
    return P.done(outer=0.8, rim=0.0)


ALL = {'gun_sunagi': gun_sunagi, 'bitig_tasi': bitig_tasi, 'zincirli_kus': zincirli_kus, 'tan_halkasi': tan_halkasi, 'altin_yaprak': altin_yaprak}

if __name__ == '__main__':
    import sys
    from PIL import Image
    out = sys.argv[-1] if sys.argv[-1].endswith('.png') else 'hikaye_sus_on.png'
    res = [fn() for fn in ALL.values()]
    Wd = sum(r[0].shape[1] for r in res) + 20 * (len(res) + 1)
    Hd = max(r[0].shape[0] for r in res) + 40
    bg = np.zeros((Hd, Wd, 3), np.float32)
    bg[:] = (0.12, 0.13, 0.2)
    x = 20
    for rgba, glow, org in res:
        h, w = rgba.shape[:2]
        y = Hd - 20 - h
        a = rgba[..., 3:4]
        bg[y:y + h, x:x + w] = bg[y:y + h, x:x + w] * (1 - a) + rgba[..., :3] * a + glow[..., :3] * glow[..., 3:4] * 0.7
        x += w + 20
    Image.fromarray((np.clip(bg, 0, 1) * 255).astype(np.uint8)).save(out)
    print('önizleme', out)
