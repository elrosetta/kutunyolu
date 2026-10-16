"""Kaf Dağı v2 "mürekkep" süsleri (oyun alanı, dünya uzayı; 4 doku pikseli / dünya birimi).

Biyoma özgü ad "<süs>_kaf_v2" (Level._decor_v2 önce biyom adını arar):
  kaya_1/2   : kar başlıklı, buz damarlı arduvaz kaya
  cira       : taş sütun üstünde ateş kâsesi, başlığında kar (alev ayrı ışıma dokusu)
  kam_diregi : karlı kam direği (kartal, donmuş çaputlar, buz saçağı)
  ladin      : karla yüklü ladin (ek süs)
  kristal    : buz kristali kümesi (soluk turkuaz ışıma dokusu ile)
  kule_*     : koyu kütük kule parçaları (üstü karlı), donmuş halat bağı
Meta: assets/decor/decor_v2_kaf.json.
"""
import json
import math
import os

import numpy as np

import inkkit_ortam as ik
from inkkit_ortam import INK, Sk, Layer, blade, bezier, blob, c01, fbm, mix, poly_path, premul, ribbon, smooth_path
from otuken_ink import rock
from kaf_ink import crystal_cluster, shaman_pole, spruce, SNOW_LIT, SNOW_SH, LIGHT
import kaf_ink_ground as G


def _snow_base(sk, rng, x0, x1, base_y, h=6):
    xs = np.linspace(x0, x1, 10)
    up = [(x, base_y - h * np.sin(np.pi * (i / 9)) ** 0.8 * rng.uniform(0.6, 1.2) + 2) for i, x in enumerate(xs)]
    p = smooth_path(up + [(x1, base_y + 5), (x0, base_y + 5)], True, 0.4)
    sk.path(p, SNOW_SH)
    sk.path(smooth_path(up + [(q[0], q[1] + 2.5) for q in up[::-1]], True, 0.4), SNOW_LIT)
    sk.path(smooth_path(up, False, 0.4), INK, 0.7, 0, 1.0)


def kaya(seed, rx, ry):
    arr = rock(seed, rx, ry, base=(122, 130, 178), moss=SNOW_LIT, ink_w=3.0)
    h, w = arr.shape[:2]
    L = Layer(w / ik.K, h / ik.K)
    L.a = arr
    return L, (w, h), (w / ik.K / 2, h / ik.K - 8)


def cira(seed=31):
    """Taş sütun (üst üste yontulmuş taşlar), tepede demir ateş kâsesi; kâsenin kenarında ve taşlarda kar."""
    W, Hh = 64, 150
    sk = Sk(W, Hh)
    base_y = Hh - 3
    cx = 32
    rng = np.random.default_rng(seed)
    y = base_y
    k = 0
    while y > 48:
        hh = rng.uniform(14, 22)
        ww = 13 - k * 0.6 + rng.uniform(-1.5, 1.5)
        st = smooth_path([(cx - ww, y), (cx - ww * 1.05, y - hh * 0.5), (cx - ww * 0.95, y - hh), (cx + ww * 0.9, y - hh),
                          (cx + ww * 1.05, y - hh * 0.5), (cx + ww, y)], True, 0.25)
        sk.path(st, (92, 96, 136))
        sk.path(poly_path([(cx - ww, y), (cx - ww * 1.05, y - hh * 0.5), (cx - ww * 0.95, y - hh), (cx - ww * 0.3, y - hh), (cx - ww * 0.35, y)]), (128, 134, 176), 0.8)
        sk.path(st, INK, 1.0, 0, 1.4)
        sk.path(ribbon([(cx - ww * 0.9, y - hh + 1), (cx, y - hh - 1), (cx + ww * 0.6, y - hh + 1)], [2.5, 3.2, 1.5]), SNOW_LIT, 0.9)
        y -= hh
        k += 1
    bowl = smooth_path([(cx - 16, 32), (cx + 16, 32), (cx + 10, 48), (cx - 10, 48)], True, 0.2)
    sk.path(bowl, (52, 50, 66))
    sk.path(ribbon([(cx - 15, 35), (cx + 15, 35)], [1.6, 1.6]), (130, 132, 150))
    sk.path(bowl, INK, 1.0, 0, 1.6)
    sk.path(smooth_path([(cx - 17, 32), (cx - 14, 29), (cx - 8, 30), (cx - 11, 33)], True, 0.4), SNOW_LIT)
    sk.path(smooth_path([(cx + 9, 31), (cx + 14, 29), (cx + 17, 32), (cx + 13, 33)], True, 0.4), SNOW_LIT)
    for j in range(4):
        x = cx - 8 + j * 5
        sk.path(ribbon([(x, 34), (x + 2, 24)], [3, 2]), (90, 60, 40))
    L = Layer(W, Hh)
    L.a = sk.snap()
    se = Sk(W, Hh)
    fl = [(cx - 11, 32), (cx - 9, 15), (cx - 3, 2), (cx + 1, 10), (cx + 7, 0), (cx + 10, 16), (cx + 11, 32)]
    se.path(smooth_path(fl, True, 0.45), (255, 120, 40), 0.9, 2.0)
    se.path(smooth_path([(cx - 6, 32), (cx - 4, 18), (cx, 8), (cx + 4, 18), (cx + 6, 32)], True, 0.45), (255, 196, 90), 1.0, 1.2)
    se.path(smooth_path([(cx - 3, 32), (cx, 19), (cx + 3, 32)], True, 0.45), (255, 240, 200), 1.0)
    E = Layer(W, Hh)
    E.a = se.snap()
    return L, (W, Hh), (cx, base_y), E


def kam_diregi(seed=21):
    W, Hh = 130, 240
    sk = Sk(W, Hh)
    base_y = Hh - 4
    rng = np.random.default_rng(seed)
    shaman_pole(sk, 65, base_y, 200, seed)
    _snow_base(sk, rng, 40, 92, base_y, 7)
    L = Layer(W, Hh)
    L.a = sk.snap()
    return L, (W, Hh), (65, base_y)


def ladin(seed=71, h=200):
    W, Hh = int(h * 0.8), h + 14
    sk = Sk(W, Hh)
    base_y = Hh - 5
    rng = np.random.default_rng(seed)
    spruce(sk, W / 2, base_y, h, seed, ink_w=1.8, needle=(80, 122, 146), needle_d=(48, 80, 112), snow_amt=1.8,
           trunk_col=(70, 54, 58), width_k=1.5)
    _snow_base(sk, rng, W * 0.2, W * 0.8, base_y, 7)
    L = Layer(W, Hh)
    L.a = sk.snap()
    return L, (W, Hh), (W / 2, base_y)


def kristal(seed=81):
    W, Hh = 120, 120
    sk = Sk(W, Hh)
    base_y = Hh - 6
    rng = np.random.default_rng(seed)
    crystal_cluster(sk, 60, base_y, 92, seed, ink_w=1.6)
    _snow_base(sk, rng, 26, 94, base_y, 6)
    L = Layer(W, Hh)
    L.a = sk.snap()
    se = Sk(W, Hh)
    se.c.drawCircle(60, base_y - 40, 40, se.paint((90, 220, 255), 0.35, 18))
    se.c.drawCircle(60, base_y - 30, 18, se.paint((180, 245, 255), 0.4, 8))
    E = Layer(W, Hh)
    E.a = se.snap()
    return L, (W, Hh), (60, base_y), E


def kule_dikme():
    W, Hh = 16, 256
    ys, xs = (np.mgrid[0:ik.P(Hh), 0:ik.P(W)].astype(np.float32) + 0.5) / ik.K
    u = (xs - W / 2) / 5.5
    cov = np.clip((5.5 - np.abs(xs - W / 2)) * ik.K + 0.5, 0, 1)
    tone = np.where(u < -0.3, 1.25, np.where(u < 0.35, 1.0, 0.66))
    n = fbm(W, Hh, [1.2, 6], 5, wrap=True)
    col = c01(G.WOOD)[None, None, :] * (tone * (1 + 0.1 * n))[..., None]
    # kırağı: soğuk taraf (sol, ay ışığı) hafif mavi-beyaz damarlar
    col = mix(col, c01((180, 196, 230))[None, None, :], (np.clip(n * 1.5 - 0.4, 0, 1) * (u < -0.2) * 0.4)[..., None])
    ink = np.clip(1.6 - (5.5 - np.abs(xs - W / 2)) + 0.5, 0, 1) * cov
    col = mix(col, c01(INK)[None, None, :], ink[..., None])
    L = Layer(W, Hh)
    L.a = premul(col.astype(np.float32), cov.astype(np.float32))
    sk = Sk(W, Hh)
    rng = np.random.default_rng(3)
    for _ in range(14):
        y = rng.uniform(0, Hh - 20)
        x = rng.uniform(4, W - 4)
        sk.path(ribbon([(x, y), (x + 0.5, y + 10), (x, y + 18)], [0.3, 1.2, 0.3]), INK, 0.6)
    L.over(sk.snap())
    return L


def kule_capraz():
    W, Hh = 256, 16
    ys, xs = (np.mgrid[0:ik.P(Hh), 0:ik.P(W)].astype(np.float32) + 0.5) / ik.K
    cy = Hh / 2 + 1
    cov = np.clip((4.5 - np.abs(ys - cy)) * ik.K + 0.5, 0, 1)
    v = (ys - cy) / 4.5
    tone = np.where(v < -0.3, 1.22, np.where(v < 0.35, 0.95, 0.66))
    n = fbm(W, Hh, [6, 1.2], 7, wrap=True)
    col = c01(G.WOOD)[None, None, :] * (tone * (1 + 0.1 * n))[..., None]
    ink = np.clip(1.4 - (4.5 - np.abs(ys - cy)) + 0.5, 0, 1) * cov
    col = mix(col, c01(INK)[None, None, :], ink[..., None])
    L = Layer(W, Hh)
    L.a = premul(col.astype(np.float32), cov.astype(np.float32))
    # kirişin üstünde ince kar şeridi (döşenebilir)
    sk = Sk(W, Hh)
    xs_ = np.linspace(-8, W + 8, 40)
    up = [(x, cy - 4.5 - 1.6 - 1.0 * math.sin(x / 9.0) ** 2) for x in xs_]
    sk.path(smooth_path(up + [(W + 8, cy - 3.5), (-8, cy - 3.5)], True, 0.3), SNOW_LIT, 0.95)
    sk.path(smooth_path(up, False, 0.3), INK, 0.6, 0, 0.7)
    L.over(sk.snap())
    return L


def kule_bag():
    W, Hh = 22, 18
    sk = Sk(W, Hh)
    for k in range(4):
        y = 3 + k * 3.6
        pts = [(2, y), (11, y + 1.8), (20, y + 0.4)]
        sk.path(ribbon(pts, [2.0, 3.0, 2.0]), G.ROPE)
        sk.path(ribbon(pts, [2.0, 3.0, 2.0]), INK, 0.9, 0, 0.8)
    sk.path(ribbon([(2, 2.4), (11, 3.6), (20, 2.6)], [1.4, 2.0, 1.2]), SNOW_LIT, 0.9)
    L = Layer(W, Hh)
    L.a = sk.snap()
    return L


def export(save, to8, A, biome='kaf'):
    meta = {}
    tex = 2.0 * ik.K

    def put(name, res):
        L, origin = res[0], res[2]
        key = '%s_%s_v2' % (name, biome)
        save(to8(L.a), 'decor', key + '.png')
        h, w = L.a.shape[:2]
        meta[key] = {"size": [int(w), int(h)], "origin": [int(round(origin[0] * ik.K)), int(round(origin[1] * ik.K))], "texel": tex,
                     "noflip": True}
        if len(res) > 3:
            save(to8(res[3].a), 'decor', key + '_e.png')
            meta[key]["glow"] = True

    put('kaya_1', kaya(2101, 40, 26))
    put('kaya_2', kaya(2202, 28, 20))
    put('cira', cira())
    put('kam_diregi', kam_diregi())
    put('ladin', ladin())
    put('kristal', kristal())
    meta['kristal_%s_v2' % biome]['glow_pulse'] = 1.6
    for nm, fn in (('kule_dikme', kule_dikme), ('kule_capraz', kule_capraz), ('kule_bag', kule_bag)):
        L = fn()
        key = '%s_%s_v2' % (nm, biome)
        save(to8(L.a), 'decor', key + '.png')
        meta[key] = {"size": [L.w, L.h], "origin": [0, 0], "texel": tex}
    json.dump(meta, open(os.path.join(A, 'decor', 'decor_v2_%s.json' % biome), 'w', encoding='utf-8'), indent=1)
