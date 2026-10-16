"""Stil v2 "mürekkep" zemin atlası kurucusu (biyomdan bağımsız; Şahmeran ve Tamu kullanır, Ötüken kendi
otuken_ink_ground.py'sini kullanmayı sürdürür).

Atlas yerleşimi Ötüken ile birebir aynı (16 sütun x 3 zemin satırı, örtü satırı, platform satırı; hücre mantıksal 48 =
24 dünya birimi, çıktı ik.K katı). Biyom bir `Spec` verir: üst bant boyacısı, yan kenar ışığı, gömülü süs, örtü
öbekleri, tavan sarkıntıları, platform hücreleri. Üç doku çıkar:
  <id>.png       sanat RGBA (önçarpılmış -> düz)
  <id>_mask.png  R = toprak kaplaması, G = kenar gölgesi
  <id>_e.png     ışıma (kristal, kor, lav çatlağı); oyunda ADD + gölgesiz ayrı karo katmanında çizilir
"""
import math

import numpy as np

import inkkit_ortam as ik
from inkkit_ortam import INK, Layer, Sk, c01, noise, smoothstep
from otuken_ink_ground import _edge_offset

C = 48
COLS = 16
ROWS = 5
GRASS_COLS = 8
CEIL_COLS = [8, 9, 10]
OROW = 3
PROW = 4


class Spec:
    rim = (150, 196, 176)          # sola bakan yar yüzü ince soğuk kenar ışığı
    rim_a = 0.55
    ceil_dark = (20, 18, 26)
    ink_w = 3.2
    edge_amp = (1.5, 3.0, 4.0)     # üst, alt, yan kenar düzensizliği

    def top_band(self, art, emit, cov, top_d, m, rng, seed):
        """üst kenar bandı (ot, yosun, kül): art/emit Layer'larına çizer"""

    def embed(self, art, emit, cov, m, var, rng, seed):
        """gömülü süs (kaya, kristal, lav çatlağı)"""

    def tuft(self, k, seed):
        """örtü satırı öbeği -> (sanat, ışıma) önçarpılmış dizi"""
        return np.zeros((ik.P(C), ik.P(C), 4), np.float32), None

    def ceiling(self, i, seed):
        return np.zeros((ik.P(C), ik.P(C), 4), np.float32), None

    def platform(self, kind, var, seed):
        return np.zeros((ik.P(C), ik.P(C), 4), np.float32), None


def ground_cell(spec, m, var, seed):
    """-> (sanat, kaplama, ao, ışıma). m: 1 üst, 2 sağ, 4 alt, 8 sol hava."""
    rng = np.random.default_rng(seed)
    K = ik.K
    CP = ik.P(C)
    ys, xs = (np.mgrid[0:CP, 0:CP].astype(np.float32) + 0.5) / K
    t_x = xs / C
    t_y = ys / C
    cov = np.ones((CP, CP), np.float32)
    d_top = d_right = d_bot = d_left = None
    a_t, a_b, a_s = spec.edge_amp
    if m & 1:
        off = _edge_offset(t_x[0], rng, a_t, 0.5)
        d_top = ys - off[None, :]
        cov *= np.clip(d_top * K + 0.5, 0, 1)
    if m & 4:
        off = _edge_offset(t_x[0], rng, a_b, 1.0)
        d_bot = (C - ys) - off[None, :]
        cov *= np.clip(d_bot * K + 0.5, 0, 1)
    if m & 8:
        off = _edge_offset(t_y[:, 0], rng, a_s, 1.0)
        d_left = xs - off[:, None]
        cov *= np.clip(d_left * K + 0.5, 0, 1)
    if m & 2:
        off = _edge_offset(t_y[:, 0], rng, a_s, 1.0)
        d_right = (C - xs) - off[:, None]
        cov *= np.clip(d_right * K + 0.5, 0, 1)
    R = 14.0
    for need, cx, cy in ((1 | 8, R, R), (1 | 2, C - R, R), (4 | 8, R, C - R), (4 | 2, C - R, C - R)):
        if (m & need) == need:
            inq = ((xs - cx) * (1 if cx > C / 2 else -1) > 0) & ((ys - cy) * (1 if cy > C / 2 else -1) > 0)
            dd = np.hypot(xs - cx, ys - cy)
            cov = np.where(inq, cov * np.clip((R - 1 - dd) * K + 0.5, 0, 1), cov)
    edge = np.full((CP, CP), 99.0, np.float32)
    for d in (d_left, d_right, d_bot):
        if d is not None:
            edge = np.minimum(edge, d)
    top_d = d_top if d_top is not None else np.full((CP, CP), 99.0, np.float32)
    art = Layer(C, C)
    emit = Layer(C, C)
    ao = np.zeros((CP, CP), np.float32)
    if edge.min() < 90:
        ao = (1 - smoothstep(0, 12, edge)) * 0.55
        ink_w = spec.ink_w + 1.2 * noise(C, C, 4, seed + 1, wrap=False)
        ink = np.clip((ink_w - edge) * K + 0.5, 0, 1) * cov
        rim = np.zeros((CP, CP), np.float32)
        if d_left is not None:
            rim = np.maximum(rim, np.clip(1 - np.abs(d_left - ink_w - 1.6) / 1.4, 0, 1))
        art.fill_mask(rim * cov * spec.rim_a, c01(spec.rim))
        art.fill_mask(ink, c01(INK))
    if m & 1:
        spec.top_band(art, emit, cov, top_d, m, rng, seed)
    if m & 4:
        dark = (1 - smoothstep(0, 10, d_bot)) * cov * 0.5
        art.fill_mask(dark, c01(spec.ceil_dark))
    spec.embed(art, emit, cov, m, var, rng, seed)
    return art.a, cov, ao, emit.a


def edge_fade(arr, margin):
    """ışıma dokusunu kenarlara doğru söndür (karo / doku sınırında kare hale görünmesin); margin çıktı pikseli."""
    h, w = arr.shape[:2]
    fy = np.clip(np.minimum(np.arange(h), h - 1 - np.arange(h)) / max(margin, 1), 0, 1)
    fx = np.clip(np.minimum(np.arange(w), w - 1 - np.arange(w)) / max(margin, 1), 0, 1)
    k = (smoothstep(0, 1, fy)[:, None] * smoothstep(0, 1, fx)[None, :]).astype(np.float32)
    return arr * k[..., None]


def blit(dst, src, x, y, clip=None):
    """dst/src önçarpılmış (piksel dizileri), x/y mantıksal."""
    h, w = src.shape[:2]
    x, y = ik.P(x), ik.P(y)
    Hd, Wd = dst.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(Wd, x + w), min(Hd, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    if clip is not None:
        s = s * clip[y0:y1, x0:x1, None]
    d = dst[y0:y1, x0:x1]
    dst[y0:y1, x0:x1] = s + d * (1 - s[..., 3:4])


def build_atlas(spec, seed=500):
    CPX = ik.P(C)
    W, Hh = COLS * CPX, ROWS * CPX
    art = np.zeros((Hh, W, 4), np.float32)
    emit = np.zeros((Hh, W, 4), np.float32)
    mask = np.zeros((Hh, W, 4), np.float32)
    mask[..., 3] = 1.0
    emit_cells = []

    def put(arr, e, cx, cy):
        art[cy * CPX:(cy + 1) * CPX, cx * CPX:(cx + 1) * CPX] = arr
        if e is not None and e[..., 3].max() > 0.02:
            e = edge_fade(e, ik.P(7))
            emit[cy * CPX:(cy + 1) * CPX, cx * CPX:(cx + 1) * CPX] = e
            emit_cells.append([cx, cy])

    for v in range(3):
        for m in range(16):
            a, cov, ao, e = ground_cell(spec, m, v, seed + m * 7 + v * 131)
            put(a, e, m, v)
            mask[v * CPX:(v + 1) * CPX, m * CPX:(m + 1) * CPX, 0] = cov
            mask[v * CPX:(v + 1) * CPX, m * CPX:(m + 1) * CPX, 1] = ao
    for k in range(GRASS_COLS):
        a, e = spec.tuft(k, seed + 900 + k)
        put(a, e, k, OROW)
    for i, col in enumerate(CEIL_COLS):
        a, e = spec.ceiling(i, seed + 950 + i)
        put(a, e, col, OROW)
    for var in range(2):
        for kind in range(3):
            a, e = spec.platform(kind, var, seed + 980 + kind + 10 * var)
            put(a, e, kind + 3 * var, PROW)
    return art, mask, emit, emit_cells


def tile_wrap_draw(sk, S, x, y, r, fn):
    """Döşenen dokuda kenara yakın şekli 3x3 kopyayla çiz (fn(dx, dy))."""
    for dx in (-S, 0, S):
        for dy in (-S, 0, S):
            if -r < x + dx < S + r and -r < y + dy < S + r:
                fn(dx, dy)
