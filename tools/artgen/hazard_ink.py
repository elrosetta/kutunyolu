"""Stil v2 sıvı tehlike dokusu (liquid_ink.gdshader için): döşenebilir veri dokusu, görüntü değil.
R = geniş akış gürültüsü, G = Voronoi hücre kenarı (lav kabuğu çatlakları / zehir köpük ağı), B = ince ayrıntı,
A = 1. Renk, ışıma, yüzey çizgisi ve kabarcıklar gölgelendiricide üretilir."""
import numpy as np

import inkkit_ortam as ik
from inkkit_ortam import noise, fbm

KINDS = {'sahmeran': {'zehir': 'liquid_zehir'}, 'tamu': {'lav': 'liquid_lav'}}


def _voronoi_edge(S, n, seed, stretch=1.0):
    rng = np.random.default_rng(seed)
    pts = rng.uniform(0, S, (n, 2))
    g = ik.axis(S)                      # K = 1 temel: np.arange(S); HD'de aynı hücreler 2 kat sık örneklenir
    ys, xs = np.meshgrid(g, g, indexing='ij')
    best = np.full(ys.shape, 1e9, np.float32)
    second = np.full(ys.shape, 1e9, np.float32)
    for dx in (-S, 0, S):
        for dy in (-S, 0, S):
            for (px, py) in pts:
                d = np.hypot((xs - px - dx) * stretch, ys - py - dy)
                m = d < best
                second = np.where(m, best, np.minimum(second, d))
                best = np.where(m, d, best)
    e = second - best
    return np.clip(1 - e / 6.0, 0, 1)


def _tex(seed, cells, stretch):
    S = 256
    r = fbm(S, S, [40, 14], seed) * 0.5 + 0.5
    g = _voronoi_edge(S, cells, seed + 1, stretch)
    b = noise(S, S, 2.5, seed + 2) * 0.5 + 0.5
    out = np.stack([r, g, b, np.ones_like(r)], -1)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


def liquid_lav():
    return _tex(901, 26, 0.8)


def liquid_zehir():
    return _tex(902, 18, 1.0)
