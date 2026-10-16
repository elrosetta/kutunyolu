"""Stil v2 "mürekkep" kare animasyonları: PVFX piksel efektlerinin (assets/fx/anim/<ad>.png) yerine geçen fırça çizimleri.

Aynı ad + "_v2" (assets/fx/anim/<ad>_v2.png, anim_v2.json); AnimFX v2'de bunu seçer, doğrusal süzgeç, "texel" 4
(hücre 384 doku pikseli = v1'in 96 dünya birimi hücresi). Kare sayısı, hız ve pivot v1 ile aynı: oynanış zamanlaması değişmez.
Renk oyunda modulate ile verilir (çizimler açık tonlu; mürekkep konturu koyu kalır).

  smoke_puff   dönen mürekkep-yıkama duman öbekleri, kıvrık fırça konturu, kenardan yenerek söner
  radiant_heal ayak halkası + yükselen yaprak / kıvılcım fırça darbeleri (şifa)
  hush_lock    susturma mührü: çizilen ensō, içinde dönen dört rün, kilitlenip dağılır
  focus_charge merkeze akan fırça darbeleri, büyüyen çekirdek (yük)
  splash_crown su tacı: yukarı açılan damla dilleri ve sıçrantı
  landing_dust iniş tozu: yana savrulan kuru fırça toz öbekleri
"""
import json
import math
import os

import numpy as np
import skia
from scipy import ndimage

K = 4.0
CELL = 384
INKC = (0.08, 0.085, 0.11)


def _surf():
    s = skia.Surface(CELL, CELL)
    c = s.getCanvas()
    c.clear(skia.Color4f(0, 0, 0, 0))
    c.scale(K, K)
    return s, c


def _paint(col, a=1.0, blur=0.0, stroke=0.0):
    p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(col[0], col[1], col[2], a))
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if stroke > 0:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
    return p


def _taper(pts, w, t0=0.3, t1=0.3):
    pts = np.asarray(pts, np.float64)
    if len(pts) < 2:
        return skia.Path()
    d = np.gradient(pts, axis=0)
    ln = np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-6)
    nrm = np.stack([-d[:, 1] / ln, d[:, 0] / ln], 1)
    s = np.linspace(0, 1, len(pts))
    a = np.clip(s / max(t0, 1e-3), 0, 1) if t0 > 0 else np.ones_like(s)
    b = np.clip((1 - s) / max(t1, 1e-3), 0, 1) if t1 > 0 else np.ones_like(s)
    wp = w * np.maximum(0.08, np.sin(a * math.pi / 2) * np.sin(b * math.pi / 2))
    left = pts + nrm * wp[:, None] * 0.5
    right = pts - nrm * wp[:, None] * 0.5
    poly = np.concatenate([left, right[::-1]])
    p = skia.Path()
    p.moveTo(*poly[0])
    for q in poly[1:]:
        p.lineTo(*q)
    p.close()
    return p


def _blob(cx, cy, r, seed, n=12, jit=0.18):
    rng = np.random.default_rng(seed)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * (1 + rng.uniform(-jit, jit))
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    p = skia.Path()
    m = len(pts)
    p.moveTo(*pts[0])
    for i in range(m):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        p.cubicTo(*c1, *c2, *p2)
    p.close()
    return p


def _arr(s):
    return s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType).astype(np.float32) / 255.0


_NZ = {}


def _erode(arr, t, seed, soft=0.12):
    """Kenardan ve gürültüyle yenerek söndürme (t 0 tam, 1 yok)."""
    if t <= 0:
        return arr
    key = seed
    if key not in _NZ:
        rng = np.random.default_rng(seed)
        nz = ndimage.gaussian_filter(rng.standard_normal((CELL, CELL)).astype(np.float32), 9)
        _NZ[key] = (nz - nz.min()) / (nz.max() - nz.min() + 1e-6)
    nz = _NZ[key]
    m = np.clip((nz - t * 1.1 + 0.05) / soft, 0, 1)
    return arr * m[..., None]


def _ease(t):
    return 1 - (1 - t) ** 2.2


# ------------------------------------------------------------------ efektler (dünya birimi; hücre 96x96, pivot v1)
def smoke_puff(i, n):
    t = i / (n - 1)
    s, c = _surf()
    rng = np.random.default_rng(5)
    cx, cy = 48, 48
    for k in range(7):
        a = k * 2 * math.pi / 7 + rng.uniform(-0.3, 0.3)
        d = 6 + 18 * _ease(t) * rng.uniform(0.7, 1.1)
        r = (7 + rng.uniform(0, 5)) * (0.6 + 0.8 * _ease(t))
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d * 0.8 - 8 * t
        path = _blob(x, y, r, 100 + k)
        c.drawPath(path, _paint((0.86, 0.86, 0.9), 0.85))
        c.drawPath(_blob(x + r * 0.25, y + r * 0.3, r * 0.7, 200 + k), _paint((0.6, 0.6, 0.68), 0.7))
        # kıvrık fırça konturu (çizgi roman dumanı)
        sp = [(x + math.cos(a + 3.6 + j * 0.45) * r * (0.55 - j * 0.04), y + math.sin(a + 3.6 + j * 0.45) * r * (0.55 - j * 0.04)) for j in range(10)]
        c.drawPath(_taper(sp, 1.4, 0.1, 0.8), _paint(INKC, 0.75))
    arr = _arr(s)
    return _erode(arr, max(0.0, (t - 0.35) / 0.65), 7)


def radiant_heal(i, n):
    t = i / (n - 1)
    s, c = _surf()
    rng = np.random.default_rng(9)
    cx, cy = 48, 67
    # ayak halkası (yatay elips fırça)
    rx = 10 + 16 * _ease(min(1, t * 1.6))
    a_r = max(0.0, 1 - t * 1.2)
    pts = [(cx + math.cos(a) * rx, cy + math.sin(a) * rx * 0.28) for a in np.linspace(0.2, 2 * math.pi + 0.1, 40)]
    c.drawPath(_taper(pts, 2.4, 0.4, 0.4), _paint((1, 1, 1), a_r))
    # yükselen yapraklar / ışık dilleri
    for k in range(9):
        ph = rng.uniform(0, 0.35)
        tt = np.clip((t - ph) / 0.6, 0, 1)
        if tt <= 0 or tt >= 1:
            continue
        x = cx + rng.uniform(-14, 14)
        y = cy - 4 - tt * rng.uniform(28, 44)
        ln = rng.uniform(5, 9) * math.sin(tt * math.pi)
        ang = -math.pi / 2 + rng.uniform(-0.4, 0.4)
        p0 = (x - math.cos(ang) * ln * 0.5, y - math.sin(ang) * ln * 0.5)
        p1 = (x + math.cos(ang) * ln * 0.5, y + math.sin(ang) * ln * 0.5)
        leaf = _taper([p0, ((p0[0] + p1[0]) / 2 + 1.2, (p0[1] + p1[1]) / 2), p1], 3.2, 0.5, 0.5)
        c.drawPath(leaf, _paint((1, 1, 1), 0.95))
        c.drawPath(_taper([p0, p1], 0.6, 0.2, 0.6), _paint(INKC, 0.5))
    for k in range(10):
        x = cx + rng.uniform(-18, 18)
        y = cy - rng.uniform(4, 40) * t
        c.drawCircle(x, y, rng.uniform(0.5, 1.1) * (1 - t * 0.6), _paint((1, 1, 1), 0.9))
    return _arr(s)


def hush_lock(i, n):
    t = i / (n - 1)
    s, c = _surf()
    cx, cy = 48, 48
    draw = min(1.0, t / 0.25)
    fade = max(0.0, (t - 0.7) / 0.3)
    r = 16 + 2 * math.sin(t * 9)
    a0 = -math.pi * 0.6
    pts = [(cx + math.cos(a) * r, cy + math.sin(a) * r) for a in np.linspace(a0, a0 + 2 * math.pi * 0.93 * draw, max(3, int(44 * draw)))]
    c.drawPath(_taper(pts, 3.6, 0.15, 0.5), _paint((1, 1, 1), 1.0))
    c.drawPath(_taper(pts, 1.2, 0.15, 0.6), _paint(INKC, 0.7))
    rot = t * 2.2
    for k in range(4):
        a = rot + k * math.pi / 2
        x, y = cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55
        sc = min(1.0, max(0.0, (t - 0.15 - k * 0.04) / 0.15))
        if sc <= 0:
            continue
        g = [(x - 2.4 * sc, y - 2.6 * sc), (x, y + 2.6 * sc), (x + 2.4 * sc, y - 2.6 * sc)]
        c.drawPath(_taper(g, 1.6, 0.1, 0.1), _paint((1, 1, 1), 1.0))
    if 0.3 < t < 0.75:
        k = (t - 0.3) / 0.45
        c.drawPath(_taper([(cx - r * 0.9, cy), (cx + r * 0.9, cy)], 2.0 * (1 - k * 0.5), 0.3, 0.3), _paint((1, 1, 1), 0.9))
        c.drawPath(_taper([(cx, cy - r * 0.9), (cx, cy + r * 0.9)], 2.0 * (1 - k * 0.5), 0.3, 0.3), _paint((1, 1, 1), 0.9))
    arr = _arr(s)
    return _erode(arr, fade, 13)


def focus_charge(i, n):
    t = i / (n - 1)
    s, c = _surf()
    rng = np.random.default_rng(17)
    cx, cy = 48, 48
    for k in range(12):
        a = k * 2 * math.pi / 12 + rng.uniform(-0.2, 0.2)
        ph = (t * 1.4 + rng.uniform(0, 1)) % 1.0
        d0 = 30 * (1 - ph) + 4
        ln = 8 * (1 - ph * 0.5)
        p0 = (cx + math.cos(a) * d0, cy + math.sin(a) * d0)
        p1 = (cx + math.cos(a + 0.25) * (d0 + ln), cy + math.sin(a + 0.25) * (d0 + ln))
        c.drawPath(_taper([p1, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2), p0], 2.2, 0.8, 0.1), _paint((1, 1, 1), 0.4 + 0.6 * ph))
    r = 3 + 5 * t
    c.drawCircle(cx, cy, r * 1.8, _paint((1, 1, 1), 0.25, blur=r))
    c.drawCircle(cx, cy, r, _paint((1, 1, 1), 0.95))
    c.drawPath(_taper([(cx + math.cos(a) * (r + 1.5), cy + math.sin(a) * (r + 1.5)) for a in np.linspace(t * 6, t * 6 + 4.5, 20)], 1.2, 0.2, 0.7), _paint(INKC, 0.6))
    return _arr(s)


def splash_crown(i, n):
    t = i / (n - 1)
    s, c = _surf()
    rng = np.random.default_rng(23)
    cx, cy = 48, 70
    for k in range(9):
        a = -math.pi / 2 + (k - 4) * 0.28
        h = rng.uniform(14, 24) * math.sin(min(1, t * 1.4) * math.pi * 0.5) * (1 - t * 0.4)
        x0 = cx + (k - 4) * 2.4
        tip = (x0 + math.cos(a) * h, cy + math.sin(a) * h + 10 * t * t)
        c.drawPath(_taper([(x0, cy), ((x0 + tip[0]) / 2, (cy + tip[1]) / 2 - 2), tip], 3.0, 0.1, 0.8), _paint((1, 1, 1), 0.95))
        c.drawCircle(tip[0], tip[1] - 1, 1.3, _paint((1, 1, 1), 0.95))
    c.drawPath(_taper([(cx - 16 - 6 * t, cy + 1), (cx, cy + 2.5), (cx + 16 + 6 * t, cy + 1)], 2.6, 0.4, 0.4), _paint((1, 1, 1), 0.8))
    arr = _arr(s)
    return _erode(arr, max(0.0, (t - 0.5) / 0.5), 29)


def landing_dust(i, n):
    t = i / (n - 1)
    s, c = _surf()
    rng = np.random.default_rng(31)
    cx, cy = 48, 70
    for side in (-1, 1):
        for k in range(4):
            d = (6 + k * 6) * _ease(t) + 3
            r = (3 + k * 1.2) * (0.6 + 0.9 * _ease(t))
            x, y = cx + side * d, cy - r * 0.55 - k * 1.2 * t
            c.drawPath(_blob(x, y, r, 300 + k + side * 10), _paint((0.9, 0.88, 0.86), 0.85))
            sp = [(x + side * math.cos(j * 0.5) * r * 0.5, y - math.sin(j * 0.5) * r * 0.5) for j in range(7)]
            c.drawPath(_taper(sp, 1.0, 0.1, 0.8), _paint(INKC, 0.55))
    arr = _arr(s)
    return _erode(arr, max(0.0, (t - 0.3) / 0.7), 37)


FX = {'smoke_puff': smoke_puff, 'radiant_heal': radiant_heal, 'hush_lock': hush_lock, 'focus_charge': focus_charge,
      'splash_crown': splash_crown, 'landing_dust': landing_dust}


def export(save, to8, A, only=None):
    v1 = json.load(open(os.path.join(A, 'fx', 'anim', 'anim.json'), encoding='utf-8'))
    mp = os.path.join(A, 'fx', 'anim', 'anim_v2.json')
    meta = json.load(open(mp, encoding='utf-8')) if os.path.exists(mp) else {}
    for name, fn in FX.items():
        if only and name not in only:
            continue
        m = v1[name]
        n = int(m['frames'])
        cols = int(m['cols'])
        rows = (n + cols - 1) // cols
        sheet = np.zeros((rows * CELL, cols * CELL, 4), np.float32)
        for i in range(n):
            a = fn(i, n)
            al = a[..., 3:4]
            straight = np.concatenate([np.where(al > 1e-4, a[..., :3] / np.maximum(al, 1e-4), 0), al], -1)
            r, cc = divmod(i, cols)
            sheet[r * CELL:(r + 1) * CELL, cc * CELL:(cc + 1) * CELL] = straight
        save(to8(sheet), 'fx/anim', name + '_v2.png', vram=False)
        meta[name] = {'frames': n, 'cols': cols, 'cell': CELL, 'fps': m.get('fps', 20), 'pivot': [p * K for p in m.get('pivot', [48, 64])],
                      'loop': m.get('loop', False), 'texel': K}
        print('  efekt', name, n)
    json.dump(meta, open(mp, 'w', encoding='utf-8', newline='\n'), indent=1)
