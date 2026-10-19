"""Bozkır Kurganları v2 "mürekkep" süsleri (oyun alanı, dünya uzayı; 4 doku pikseli / dünya birimi).

Biyoma özgü ad: "<süs>_bozkir_v2" (Level._decor_v2 önce biyom adını arar, yoksa ortak "<süs>_v2"):
  kaya_1/2   : güneşte yanmış, turuncu likenli yontulmuş kaya
  cira       : ağarmış direk üstünde demir ocak sepeti (alev ayrı ışıma dokusu)
  kam_diregi : kurt başlı tuğ (at kılı püskül, kızıl sancak)
  cicek_1..3 : bozkır lalesi öbeği, deve dikeni, sorguçlu kılçık otu
  balbal     : bozkır balbalı (ışık sağdan)
  obo        : mavi-ak çaputlu oba taşı
  bitig      : Orhun yazılı bitig taşı (kaplumbağa kaideli)
  kule_*     : gözetleme kulesi parçaları (ağarmış kütük, ham deri bağ)
Meta: assets/decor/decor_v2_bozkir.json (Level ortak decor_v2.json ile birleştirir).
"""
import json
import math
import os

import numpy as np

import inkkit_ortam as ik
from hdpack import HD   # HD paketi: json'a temel (HD'siz) boyut / köken / doku yoğunluğu yazılır
from inkkit_ortam import INK, Sk, Layer, blade, bezier, blob, c01, fbm, mix, poly_path, premul, ribbon, smooth_path
from otuken_ink import balbal, rock
from bozkir_ink import LIGHT, mirrored, obo, tug, bitig_tasi
import bozkir_ink_ground as G

WOOD = G.WOOD
WOOD_D = G.WOOD_D
WOOD_L = G.WOOD_L
HIDE = G.HIDE
GR = [(92, 52, 46), (166, 108, 64), (226, 168, 88), (252, 214, 134)]


def _grass_base(sk, rng, x0, x1, base_y, n=30, hmax=20):
    for _ in range(n):
        x = rng.uniform(x0, x1)
        h = rng.uniform(5, hmax)
        sk.path(blade(x, base_y + 4, h, rng.uniform(-0.1, 0.6), rng.uniform(1.5, 2.6)), GR[int(rng.integers(4))], 0.95)


def kaya(seed, rx, ry):
    arr = rock(seed, rx, ry, base=(152, 112, 92), moss=(214, 140, 64), ink_w=3.0, light_dir=(0.6, -0.8))
    h, w = arr.shape[:2]
    L = Layer(w / ik.K, h / ik.K)
    L.a = arr
    return L, (w, h), (w / ik.K / 2, h / ik.K - 8)


def cira(seed=31):
    """Ağarmış direk, çapraz destek, tepede demir ocak sepeti; alev ayrı toplamalı doku."""
    W, Hh = 64, 150
    sk = Sk(W, Hh)
    base_y = Hh - 3
    cx = 32
    post = poly_path([(cx - 4.5, base_y), (cx + 4.5, base_y), (cx + 3.2, 42), (cx - 3.2, 42)])
    sk.path(post, WOOD)
    sk.path(poly_path([(cx + 0.5, base_y), (cx + 4.5, base_y), (cx + 3.2, 42), (cx + 0.5, 42)]), WOOD_L, 0.8)
    sk.path(post, INK, 1.0, 0, 1.6)
    for a, b in (((cx - 16, base_y), (cx - 2, base_y - 40)), ((cx + 16, base_y), (cx + 2, base_y - 40))):
        p = ribbon([a, b], [3.4, 2.6])
        sk.path(p, WOOD_D)
        sk.path(p, INK, 1.0, 0, 1.2)
    for y in (base_y - 40, 76):
        pts = [(cx - 6, y), (cx, y + 2), (cx + 6, y)]
        sk.path(ribbon(pts, [2.2, 3.0, 2.2]), HIDE)
        sk.path(ribbon(pts, [2.2, 3.0, 2.2]), INK, 0.8, 0, 0.7)
    # demir sepet (kafes)
    bowl = smooth_path([(cx - 14, 30), (cx + 14, 30), (cx + 9, 46), (cx - 9, 46)], True, 0.2)
    sk.path(bowl, (54, 46, 50))
    for k in range(5):
        x = cx - 11 + k * 5.5
        sk.path(ribbon([(x, 30), (x * 0.8 + cx * 0.2, 46)], [1.4, 1.2]), (120, 110, 104))
    sk.path(ribbon([(cx - 13, 33), (cx + 13, 33)], [1.4, 1.4]), (150, 130, 110))
    sk.path(bowl, INK, 1.0, 0, 1.6)
    for k in range(4):
        x = cx - 8 + k * 5
        sk.path(ribbon([(x, 32), (x + 2, 22)], [3, 2]), (96, 60, 40))
    # sarkan at kılı
    rng = np.random.default_rng(seed)
    for k in range(5):
        q = bezier((cx + 4, 78), (cx + 7, 90), (cx + 9 + k, 104 + k * 2), 6)
        sk.path(ribbon(q, np.linspace(1.2, 0.3, 6)), (40, 26, 30), 0.9)
    L = Layer(W, Hh)
    L.a = sk.snap()
    se = Sk(W, Hh)
    fl = [(cx - 11, 30), (cx - 9, 14), (cx - 3, 1), (cx + 1, 9), (cx + 7, -1), (cx + 10, 15), (cx + 11, 30)]
    se.path(smooth_path(fl, True, 0.45), (255, 120, 40), 0.9, 2.0)
    se.path(smooth_path([(cx - 6, 30), (cx - 4, 17), (cx, 7), (cx + 4, 17), (cx + 6, 30)], True, 0.45), (255, 196, 90), 1.0, 1.2)
    se.path(smooth_path([(cx - 3, 30), (cx, 18), (cx + 3, 30)], True, 0.45), (255, 240, 200), 1.0)
    E = Layer(W, Hh)
    E.a = se.snap()
    return L, (W, Hh), (cx, base_y), E


def tug_decor(seed=21):
    W, Hh = 170, 250
    sk = Sk(W, Hh)
    base_y = Hh - 4
    rng = np.random.default_rng(seed)
    tug(sk, 34, base_y, 210, wind=1.0, seed=seed, ink_w=1.8)
    _grass_base(sk, rng, 18, 54, base_y, 18, 16)
    L = Layer(W, Hh)
    L.a = sk.snap()
    return L, (W, Hh), (34, base_y)


def cicek(seed, kind):
    W, Hh = 90, 70
    rng = np.random.default_rng(seed)
    sk = Sk(W, Hh)
    base_y = Hh - 3
    # örtü çizicileri 48'lik hücreye göre (C + 1 tabanı); kaydırarak kullan
    sk.c.save()
    sk.c.translate(0, base_y - (G.C + 1))
    if kind == 0:
        G._stipa(sk, rng, 30, 10, 16, plumes=0.0)
        G._tulip(sk, rng, 32)
        G._tulip(sk, rng, 52)
    elif kind == 1:
        G._stipa(sk, rng, 30, 10, 14, plumes=0.0)
        G._thistle(sk, rng, 46)
        G._wormwood(sk, rng, 62)
    else:
        G._stipa(sk, rng, 45, 34, 40, plumes=0.7)
    sk.c.restore()
    L = Layer(W, Hh)
    L.a = sk.snap()
    return L, (W, Hh), (45, base_y)


def balbal_decor(seed=41):
    W, Hh = 80, 124
    sk = Sk(W, Hh)
    base_y = Hh - 4
    mirrored(sk, 40, balbal, base_y, 106, (128, 98, 92), (214, 166, 128), seed)
    rng = np.random.default_rng(seed)
    _grass_base(sk, rng, 14, W - 14, base_y, 22, 16)
    L = Layer(W, Hh)
    L.a = sk.snap()
    return L, (W, Hh), (40, base_y)


def obo_decor(seed=51):
    W, Hh = 150, 110
    sk = Sk(W, Hh)
    base_y = Hh - 4
    obo(sk, 60, base_y, 40, seed=seed, ink_w=1.8)
    rng = np.random.default_rng(seed)
    _grass_base(sk, rng, 14, 110, base_y, 26, 14)
    L = Layer(W, Hh)
    L.a = sk.snap()
    return L, (W, Hh), (60, base_y)


def bitig_decor(seed=61):
    W, Hh = 110, 200
    sk = Sk(W, Hh)
    base_y = Hh - 4
    bitig_tasi(sk, 46, base_y, 170, stone=(166, 142, 126), stone_sh=(102, 78, 88), seed=seed, ink_w=2.0)
    rng = np.random.default_rng(seed)
    _grass_base(sk, rng, 10, 100, base_y, 30, 14)
    L = Layer(W, Hh)
    L.a = sk.snap()
    return L, (W, Hh), (50, base_y)


def kule_dikme():
    """Ağarmış kütük ayak (dikeyde döşenir)."""
    W, Hh = 16, 256
    ys, xs = (np.mgrid[0:ik.P(Hh), 0:ik.P(W)].astype(np.float32) + 0.5) / ik.K
    u = (xs - W / 2) / 5.5
    cov = np.clip((5.5 - np.abs(xs - W / 2)) * ik.K + 0.5, 0, 1)
    tone = np.where(u > 0.3, 1.22, np.where(u > -0.35, 1.0, 0.66))
    n = fbm(W, Hh, [1.2, 6], 5, wrap=True)
    col = c01(WOOD)[None, None, :] * (tone * (1 + 0.1 * n))[..., None]
    ink = np.clip(1.6 - (5.5 - np.abs(xs - W / 2)) + 0.5, 0, 1) * cov
    col = mix(col, c01(INK)[None, None, :], ink[..., None])
    L = Layer(W, Hh)
    L.a = premul(col.astype(np.float32), cov.astype(np.float32))
    sk = Sk(W, Hh)
    rng = np.random.default_rng(3)
    for _ in range(16):
        y = rng.uniform(0, Hh - 20)
        x = rng.uniform(4, W - 4)
        sk.path(ribbon([(x, y), (x + 0.5, y + 10), (x, y + 18)], [0.3, 1.1, 0.3]), INK, 0.55)
    L.over(sk.snap())
    return L


def kule_capraz():
    W, Hh = 256, 14
    ys, xs = (np.mgrid[0:ik.P(Hh), 0:ik.P(W)].astype(np.float32) + 0.5) / ik.K
    cov = np.clip((4.5 - np.abs(ys - Hh / 2)) * ik.K + 0.5, 0, 1)
    v = (ys - Hh / 2) / 4.5
    tone = np.where(v < -0.3, 1.25, np.where(v < 0.35, 0.95, 0.66))
    n = fbm(W, Hh, [6, 1.2], 7, wrap=True)
    col = c01(WOOD)[None, None, :] * (tone * (1 + 0.1 * n))[..., None]
    ink = np.clip(1.4 - (4.5 - np.abs(ys - Hh / 2)) + 0.5, 0, 1) * cov
    col = mix(col, c01(INK)[None, None, :], ink[..., None])
    L = Layer(W, Hh)
    L.a = premul(col.astype(np.float32), cov.astype(np.float32))
    return L


def kule_bag():
    W, Hh = 22, 18
    sk = Sk(W, Hh)
    for k in range(4):
        y = 3 + k * 3.6
        pts = [(2, y), (11, y + 1.8), (20, y + 0.4)]
        sk.path(ribbon(pts, [2.0, 3.0, 2.0]), HIDE)
        sk.path(ribbon(pts, [2.0, 3.0, 2.0]), INK, 0.9, 0, 0.8)
    L = Layer(W, Hh)
    L.a = sk.snap()
    return L


def export(save, to8, A, biome='bozkir'):
    meta = {}
    tex = 2.0 * ik.KB()

    def put(name, res):
        L, origin = res[0], res[2]
        key = '%s_%s_v2' % (name, biome)
        save(to8(L.a), 'decor', key + '.png')
        h, w = L.a.shape[:2]
        meta[key] = {"size": [int(w) // HD, int(h) // HD], "origin": [int(round(origin[0] * ik.KB())), int(round(origin[1] * ik.KB()))], "texel": tex,
                     "noflip": True}
        if len(res) > 3:
            save(to8(res[3].a), 'decor', key + '_e.png')
            meta[key]["glow"] = True

    put('kaya_1', kaya(1101, 40, 26))
    put('kaya_2', kaya(1202, 28, 20))
    put('cira', cira())
    put('kam_diregi', tug_decor())
    put('cicek_1', cicek(1401, 0))
    put('cicek_2', cicek(1402, 1))
    put('cicek_3', cicek(1403, 2))
    put('balbal', balbal_decor())
    put('obo', obo_decor())
    put('bitig', bitig_decor())
    for nm, fn in (('kule_dikme', kule_dikme), ('kule_capraz', kule_capraz), ('kule_bag', kule_bag)):
        L = fn()
        key = '%s_%s_v2' % (nm, biome)
        save(to8(L.a), 'decor', key + '.png')
        meta[key] = {"size": [L.w // HD, L.h // HD], "origin": [0, 0], "texel": tex}
    json.dump(meta, open(os.path.join(A, 'decor', 'decor_v2_%s.json' % biome), 'w', encoding='utf-8'), indent=1)
