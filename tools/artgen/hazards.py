"""Tehlike karoları (24x24, 2'şer kare animasyon) ve sunak süsü:
  diken  (Ötüken: kara çalı dikenleri)     zehir (Şahmeran: zehir gölü)
  lav    (Tamu: kor/lav)                   buz   (Kaf: kaygan buz; zararsız)
Çıktı: assets/tiles/hazards.png (4 satır x 2 kare) + hazards.json."""
import os
import json
import math
import numpy as np
from PIL import Image
from raster import Canvas, Mat, ramp
from materials import M

TS = 24
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'tiles')


def tile_diken(f):
    c = Canvas(TS, TS, 0, 0)
    thorn = Mat(ramp(262, 0.25, 0.22, spread=0.4), name='kara diken')
    tip = Mat(ramp(350, 0.8, 0.7, spread=0.3), name='kanlı uç')
    rng = np.random.default_rng(3 + f)
    c.capsule((0, 22), (24, 22), 2.0, 2.0, Mat(ramp(20, 0.45, 0.3)), z=0)
    for i in range(7):
        x = 2 + i * 3.2 + rng.uniform(-0.6, 0.6)
        h = rng.uniform(9, 16) + (1.0 if (i + f) % 2 else 0)
        c.poly([(x - 1.6, 22), (x + 1.6, 22), (x + rng.uniform(-1.5, 1.5), 22 - h)], thorn, z=2 + i * 0.1, bevel=0.8, height=1.0)
        c.dot((x + rng.uniform(-1, 1), 22 - h + 1), tip, z=10)
    return c


def tile_liquid(f, col_h, col_d, glow=False, name='sıvı'):
    c = Canvas(TS, TS, 0, 0)
    liq = Mat(ramp(col_h[0], col_h[1], col_h[2], spread=0.3), emissive=(0.9 if glow else 0.35), outline=col_d, name=name)
    liq_d = Mat(ramp(col_h[0] - 10, col_h[1], col_h[2] * 0.6, spread=0.3), emissive=(0.4 if glow else 0.1), outline=col_d, name=name + ' koyu')
    wave = lambda lu, lv, px, py: (np.sin(px * 0.8 + f * 1.8) * 1.2 + py) < 7.5
    c.poly([(0, 6), (24, 6), (24, 24), (0, 24)], liq_d, z=0, bevel=0.5, height=0.2, paint=[(wave, liq)])
    for i in range(3):
        x = 4 + i * 7 + (3 if f else 0)
        c.dot((x, 9 + (i % 2) * 2), liq, z=5, size=2)
    return c


def tile_buz(f):
    c = Canvas(TS, TS, 0, 0)
    ice = Mat(ramp(200, 0.35, 0.92, spread=0.3), spec=1.2, name='buz')
    ice_d = Mat(ramp(205, 0.45, 0.7, spread=0.3), name='buz gölge')
    cracks = lambda lu, lv, px, py: (np.abs(py - 12 - np.sin(px * 0.9 + f) * 3) < 0.6) | (np.abs(px - 15 + np.sin(py * 0.7) * 2) < 0.5)
    c.poly([(0, 2), (24, 2), (24, 24), (0, 24)], ice, z=0, bevel=1.5, height=1.0, paint=[(cracks, ice_d)])
    return c


def decor_sunak():
    """Tanrı sunağı: taş kaide, üstte üç kam direği ve ortada kut taşı; çaputlar."""
    c = Canvas(64, 72, 32, 70)
    c.poly([(-18, 0), (18, 0), (16, -8), (-16, -8)], M['stone'], z=0, bevel=1.8, height=2)
    c.poly([(-12, -8), (12, -8), (11, -14), (-11, -14)], Mat(ramp(216, 0.15, 0.4)), z=1, bevel=1.2, height=1.5)
    for dx in (-9, 0, 9):
        c.capsule((dx, -14), (dx, -44 - (6 if dx == 0 else 0)), 1.8, 1.4, M['wood'], z=2)
        c.ellipse((dx, -46 - (6 if dx == 0 else 0)), 3.0, 2.2, M['bone'], z=3)
        for k in range(2):
            col = [M['red_paint'], M['turq'], M['gold']][(k + abs(dx) // 9) % 3]
            c.capsule((dx + 2, -36 + k * 6), (dx + 5, -29 + k * 7), 0.9, 0.7, col, z=4)
    c.ellipse((0, -24), 4.5, 4.5, M['kut'], z=8)
    return c


def main():
    rows = [('diken', [tile_diken(0), tile_diken(1)]),
            ('zehir', [tile_liquid(0, (96, 0.8, 0.75), '#143a10', False, 'zehir'), tile_liquid(1, (96, 0.8, 0.75), '#143a10', False, 'zehir')]),
            ('lav', [tile_liquid(0, (22, 0.95, 1.0), '#4a1004', True, 'lav'), tile_liquid(1, (22, 0.95, 1.0), '#4a1004', True, 'lav')]),
            ('buz', [tile_buz(0), tile_buz(1)])]
    alb = np.zeros((TS * len(rows), TS * 2, 4))
    nrm = np.zeros_like(alb)
    glo = np.zeros_like(alb)
    meta = {'cell': [TS, TS], 'rows': {}}
    for r, (name, tiles) in enumerate(rows):
        for f, c in enumerate(tiles):
            rgba = c.shade(rim_amt=0.2)
            alb[r * TS:(r + 1) * TS, f * TS:(f + 1) * TS] = rgba
            nrm[r * TS:(r + 1) * TS, f * TS:(f + 1) * TS] = c.normal_map(rgba[..., 3])
            glo[r * TS:(r + 1) * TS, f * TS:(f + 1) * TS, :3] = np.clip(c.emis, 0, 1)
            glo[r * TS:(r + 1) * TS, f * TS:(f + 1) * TS, 3] = (c.emis.max(axis=2) > 0)
        meta['rows'][name] = r
    def save(a, p):
        Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), 'RGBA').save(p)
    save(alb, os.path.join(OUT, 'hazards.png'))
    save(nrm, os.path.join(OUT, 'hazards_n.png'))
    save(glo, os.path.join(OUT, 'hazards_e.png'))
    json.dump(meta, open(os.path.join(OUT, 'hazards.json'), 'w'), indent=1)
    print('hazards', alb.shape)


if __name__ == '__main__':
    main()
