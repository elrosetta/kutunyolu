"""Stil v2 "mürekkep" tehlike karoları (biyoma özgü): assets/tiles/hazards_<biyom>_v2.png.

Yerleşim v1 hazards.png ile aynı (2 kare x 4 satır: diken, zehir, lav, buz; hazards.json "rows"), hücre mantıksal 48 =
24 dünya birimi (çıktı inkkit.K = 2: 96 doku pikseli). Yalnızca biyomun kendi satırı çizilir, diğerleri saydam.
Tehlike karosu yüzeyde 1 karo derinliğinde bir çukurdur (LevelGen._hazard_patches); çizim çukuru doldurur, yatayda dikişsiz.
  bozkir (diken): sivri uçlu, ham deriyle bağlı eski kazıklar, aralarında kemik ve kuru diken; uçlarda kurumuş kan.
  kaf (buz)     : çukurda donmuş göl: parlak, yarı saydam buz tabakası, içinde hava kabarcıkları ve çatlaklar, kenarda kırağı.
"""
import math

import numpy as np

import inkkit_ortam as ik
from inkkit_ortam import INK, Sk, bezier, blade, blob, c01, poly_path, ribbon, smooth_path

C = 48




def stakes_cell(seed, frame):
    rng = np.random.default_rng(seed)
    sk = Sk(C, C)
    base = C + 1
    # dip: koyu toprak ve kuru diken çalısı
    sk.path(poly_path([(-2, C - 7), (C + 2, C - 7), (C + 2, C + 2), (-2, C + 2)]), (74, 42, 40))
    for _ in range(12):
        x = rng.uniform(0, C)
        for dx in (-C, 0, C):
            sk.path(blade(x + dx, base, rng.uniform(5, 12), rng.uniform(-0.2, 0.6), 1.5), (120, 76, 52), 0.9)
    # kazıklar
    xs = np.linspace(3, C - 3, 5) + rng.uniform(-1.5, 1.5, 5)
    for i, x in enumerate(xs):
        h = rng.uniform(28, 40)
        ang = rng.uniform(-0.22, 0.22)
        w = rng.uniform(3.2, 4.4)
        tipx = x + math.sin(ang) * h
        tipy = base - math.cos(ang) * h
        for dx in (-C, 0, C):
            body = poly_path([(x - w + dx, base), (x + w + dx, base), (tipx + w * 0.8 + dx, tipy + 7), (tipx + dx, tipy), (tipx - w * 0.8 + dx, tipy + 7)])
            sk.path(body, (150, 114, 84))
            lit = poly_path([(x + w * 0.1 + dx, base), (x + w + dx, base), (tipx + w * 0.8 + dx, tipy + 7), (tipx + dx, tipy), (tipx + w * 0.1 + dx, tipy + 7)])
            sk.path(lit, (212, 176, 128), 0.85)
            sk.path(poly_path([(tipx - w * 0.6 + dx, tipy + 6), (tipx + dx, tipy), (tipx + w * 0.6 + dx, tipy + 6)]), (108, 26, 26), 0.75)
            for k in range(2):
                yy = base - h * (0.3 + 0.08 * k)
                xx = x + math.sin(ang) * (base - yy) + dx
                sk.path(ribbon([(xx - w - 0.5, yy), (xx, yy + 1), (xx + w + 0.5, yy)], [1.2, 1.8, 1.2]), (214, 184, 136))
            sk.path(body, INK, 1.0, 0, 1.3)
            if frame == 1 and i % 2 == 0:
                sk.c.drawCircle(tipx + dx + 0.6, tipy + 2.5, 0.9, sk.paint((255, 236, 200), 0.9))
    # kemik
    bx = rng.uniform(10, C - 10)
    for dx in (-C, 0, C):
        sk.path(ribbon([(bx - 7 + dx, base - 3), (bx + 7 + dx, base - 5)], [2.4, 2.0]), (220, 206, 176))
        for p in ((bx - 7, base - 3), (bx + 7, base - 5)):
            sk.c.drawCircle(p[0] + dx, p[1], 2.2, sk.paint((220, 206, 176)))
        sk.path(ribbon([(bx - 7 + dx, base - 3), (bx + 7 + dx, base - 5)], [2.4, 2.0]), INK, 0.8, 0, 0.8)
    return sk.snap()


def ice_cell(seed, frame):
    rng = np.random.default_rng(seed)
    sk = Sk(C, C)
    top = C - 13
    # buz tabakası
    sk.path(poly_path([(-2, top), (C + 2, top), (C + 2, C + 2), (-2, C + 2)]), (112, 176, 222))
    sk.path(poly_path([(-2, top + 4), (C + 2, top + 4), (C + 2, C + 2), (-2, C + 2)]), (74, 128, 188), 0.8)
    # derin turkuaz damar ve kabarcıklar
    for _ in range(6):
        x = rng.uniform(0, C)
        y = rng.uniform(top + 5, C - 2)
        r = rng.uniform(0.6, 1.6)
        for dx in (-C, 0, C):
            sk.c.drawCircle(x + dx, y, r, sk.paint((220, 246, 255), 0.75))
            sk.c.drawCircle(x + dx, y, r, sk.paint(INK, 0.35, 0, 0.4))
    for _ in range(3):
        x = rng.uniform(0, C)
        pts = [(x, top + 1)]
        for k in range(4):
            pts.append((pts[-1][0] + rng.uniform(-4, 4), pts[-1][1] + rng.uniform(2, 4)))
        for dx in (-C, 0, C):
            sk.path(ribbon([(p[0] + dx, p[1]) for p in pts], [0.9, 0.7, 0.5, 0.3, 0.2]), (230, 248, 255), 0.8)
            sk.path(ribbon([(p[0] + dx + 0.6, p[1] + 0.4) for p in pts], [0.6, 0.5, 0.4, 0.2, 0.1]), INK, 0.5)
    # üst yüzey: parlak ışık şeridi (iki karede yansıma kayar), kırağı
    off = 6 if frame else 0
    for dx in (-C, 0, C):
        sk.path(ribbon([(-2 + dx, top + 0.6), (C + 2 + dx, top + 0.6)], [1.6, 1.6]), (236, 250, 255))
        for k in range(3):
            x = (k * 17 + 4 + off) % C
            sk.path(ribbon([(x + dx, top + 2.5), (x + 6 + dx, top + 2.0)], [0.3, 1.4]), (255, 255, 255), 0.8)
        sk.path(ribbon([(-2 + dx, top), (C + 2 + dx, top)], [1.2, 1.2]), INK, 0.9)
    for _ in range(10):
        x = rng.uniform(0, C)
        for dx in (-C, 0, C):
            sk.c.drawCircle(x + dx, top - 0.3, rng.uniform(0.6, 1.3), sk.paint((248, 252, 255), 0.9))
    return sk.snap()


def build(biome):
    CP = ik.P(C)
    out = np.zeros((4 * CP, 2 * CP, 4), np.float32)
    if biome == 'bozkir':
        for f in range(2):
            out[0:CP, f * CP:(f + 1) * CP] = stakes_cell(71, f)
    elif biome == 'kaf':
        for f in range(2):
            out[3 * CP:4 * CP, f * CP:(f + 1) * CP] = ice_cell(73, f)
    return out
