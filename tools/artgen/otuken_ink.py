"""Kararan Ötüken, stil v2 "mürekkep" ortamı (Shinobi: Art of Vengeance yönü).

Sisli, katmanlı kutsal orman: huş ve çam/karaçam gövdeleri, aralarında teal-yeşil sis, yumuşak ışık hüzmeleri, yer sisi
şeritleri, otlu zemin; en önde koyu siluet otlar. Doku yoğunluğu: 1080p'de 1 doku pikseli = 1 ekran pikseli
(katman yüksekliği 1080; dünya biriminde 2 doku pikseli). Oyunda doğrusal süzgeç + mipmap.

Çıktılar (export): assets/bg/otuken_v2_*.png (paralaks), assets/bg/otuken_v2_fg_*.png (ön plan),
assets/tiles/otuken_v2{,_mask,_soil,_soil_n}.png + otuken_v2.json (zemin), assets/decor/*_v2.png + decor_v2.json.
"""
import math
import os
import numpy as np
from PIL import Image

import inkkit_ortam as ik
from inkkit_ortam import (INK, Layer, Sk, apply_fog, blade, blade_tip, blade_spine, facet_shade, blob, c01, fbm, leaf_shape, mix, noise, poly_path, premul,
                    ribbon, save_png, smooth_path, smoothstep, trunk, bezier)

H = 1080
WL = 3840            # döşenen paralaks katmanı genişliği (2 ekran)

# ------------------------------------------------------------------ palet (referans: teal-yeşil sis, mor-siyah koyular)
SKY_STOPS = [
    (0, (34, 30, 36)),
    (140, (44, 44, 44)),
    (300, (64, 72, 58)),
    (430, (100, 112, 84)),
    (520, (140, 154, 116)),
    (585, (178, 208, 168)),
    (630, (196, 230, 198)),
    (680, (152, 178, 140)),
    (760, (96, 110, 82)),
    (880, (56, 62, 50)),
    (1080, (32, 32, 30)),
]
FG_DARK = (30, 12, 30)        # en ön siluet (mor-siyah)
CANOPY = (40, 34, 46)         # tepe gölgesi
MINT = (206, 244, 216)        # en parlak sis


def sky_rgb():
    ys = np.arange(H, dtype=np.float32)
    st = np.array([s[0] for s in SKY_STOPS], np.float32)
    cs = np.array([s[1] for s in SKY_STOPS], np.float32) / 255.0
    out = np.stack([np.interp(ys, st, cs[:, k]) for k in range(3)], 1)
    return out.astype(np.float32)


SKY = sky_rgb()


def fog_amount(base, band=0.0, center=610.0, width=80.0, top=0.0, top_end=380.0):
    """Satır başına sis payı: sabit taban + yer sisi bandı (+ isteğe bağlı tepe pusu)."""
    ys = np.arange(H, dtype=np.float32)
    a = base + band * np.exp(-((ys - center) / width) ** 2)
    a += top * (1 - smoothstep(0, top_end, ys))
    return np.clip(a, 0, 0.97).astype(np.float32)


def wrap_x(arr, W=WL):
    return arr


# ------------------------------------------------------------------ 0) gök / uzak sis (sabit)
def layer_sky(seed=1):
    W = 1920
    L = Layer(W, H)
    rgb = np.repeat(ik.hd_lin(SKY)[:, None, :], L.w, 1).copy()
    ys = ik.axis(H)[:, None]
    xs = ik.axis(W)[None, :]
    # ay ışığının sise süzüldüğü kaynak: üst-orta solda yumuşak parıltı
    d = np.hypot((xs - 760) / 900.0, (ys + 140) / 620.0)
    glow = np.exp(-d * d * 2.2)
    rgb = mix(rgb, c01((150, 190, 168))[None, None, :], (glow * 0.45)[..., None])
    # boya dokusu: yumuşak lekeler + çok hafif dikey fırça izi (uzak gövde gölgeleri)
    n1 = fbm(W, H, [90, 40, 16], seed)
    n2 = noise(W, H, 1, seed + 7, sx=6, sy=120)
    rgb *= (1 + 0.05 * n1[..., None] + 0.035 * n2[..., None])
    # tepe: koyu yaprak örtüsü lekeleri
    can = smoothstep(0.1, 0.7, fbm(W, H, [60, 25, 10], seed + 11) * 0.8 + 0.25) * (1 - smoothstep(60, 330, ys))
    rgb = mix(rgb, c01(CANOPY)[None, None, :], (can * 0.55)[..., None])
    L.a = premul(rgb, np.ones((L.h, L.w), np.float32))
    return L


# ------------------------------------------------------------------ gövde sırası
def trunk_row(L, seed, n, wmin, wmax, base_y, fog, kinds=('pine', 'pine', 'birch'), ink_k=1.0, detail=1.0,
              lean_max=0.03, ink_mix=0.0, bark_pine=(66, 58, 62), bark_birch=(150, 160, 148), light=(150, 180, 158),
              rim=(190, 232, 210), dark_top=0.0, xs=None, base_jit=14, birch_light=(178, 190, 176),
              branches=0.0, leaf_col=(46, 58, 48), leaf_hi=(120, 150, 118), ws=None):
    rng = np.random.default_rng(seed)
    if xs is None:
        xs = np.sort(rng.uniform(0, L.w / ik.K, n))
        # aralık düzenle: kümelenme olsun ama üst üste binmesin
    if branches > 0:
        _branches_for(L, seed + 77, xs, (wmin + wmax) / 2, base_y, fog, branches, bark_pine, leaf_col, leaf_hi,
                      ink_k, dark_top)
    for i, x in enumerate(xs):
        w = rng.uniform(wmin, wmax) if ws is None else ws[i]
        kind = kinds[rng.integers(len(kinds))]
        lean = rng.uniform(-lean_max, lean_max)
        if rng.random() < 0.15:
            lean *= 3.0
        bark = bark_birch if kind == 'birch' else bark_pine
        ink = tuple(mix(INK, bark, ink_mix)) if ink_mix > 0 else INK
        lt = birch_light if kind == 'birch' else light
        arr, xl, yt = trunk(H, L.w, base_y + rng.uniform(-base_jit, base_jit), x, w, int(rng.integers(1 << 30)), kind=kind,
                            lean=lean, bend=rng.uniform(-0.15, 0.15), top_y=-60, bark=bark, light=lt, rim=rim,
                            ink=ink, ink_w=max(1.2, w * 0.06) * ink_k, light_side=-1.0, detail=detail,
                            taper=rng.uniform(0.15, 0.35))
        if dark_top > 0:
            ys = yt + ik.axis_px(arr.shape[0])
            k = 1 - dark_top * (1 - smoothstep(0, 520, ys))
            arr[..., :3] *= k[:, None, None]
        apply_fog(arr, ik.P(yt), SKY, fog)
        L.over_wrap(arr, xl, yt)


def foliage(sk, cx, cy, r, seed, col, hi=None, n=40, leaf=(9, 17), droop=0.5, ink_a=0.0):
    """Huş/kavak yaprak öbeği: elips içinde çok sayıda küçük mızrak yaprak, aşağı sarkık."""
    rng = np.random.default_rng(seed)
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        rr = r * math.sqrt(rng.random())
        x = cx + math.cos(a) * rr
        y = cy + math.sin(a) * rr * 0.7
        ln = rng.uniform(*leaf)
        ang = math.pi / 2 + rng.uniform(-1.2, 1.2) * (1 - droop) + rng.uniform(-0.5, 0.5)
        c = col
        if hi is not None and rng.random() < 0.22 and y < cy:
            c = hi
        else:
            c = tuple(np.array(col) * rng.uniform(0.8, 1.15))
        sk.path(leaf_shape(x, y, ln, ln * 0.38, ang), c, 1.0)
        if ink_a > 0 and rng.random() < 0.55:
            sk.path(leaf_shape(x, y, ln, ln * 0.38, ang), INK, ink_a, 0, 0.8)
            if ln > 11 and rng.random() < 0.6:   # orta damar
                ca, sa = math.cos(ang), math.sin(ang)
                sk.path(ribbon([(x + ca * ln * 0.1, y + sa * ln * 0.1), (x + ca * ln * 0.5, y + sa * ln * 0.5),
                                (x + ca * ln * 0.85, y + sa * ln * 0.85)], [0.9, 0.7, 0.2]), INK, ink_a * 0.8)


def _branches_for(L, seed, xs, w_avg, base_y, fog, amount, bark, leaf_col, leaf_hi, ink_k, dark_top):
    """Gövdelerden çıkan eğik dallar ve uçlarında yaprak öbekleri (gövdelerin arkasında)."""
    rng = np.random.default_rng(seed)
    pad = 400
    LW = L.w / ik.K
    sk = Sk(LW + 2 * pad, H)
    for x in xs:
        nb = int(rng.poisson(amount * 2.2))
        for _ in range(nb):
            y0 = rng.uniform(40, base_y - 220)
            side = -1 if rng.random() < 0.5 else 1
            ln = rng.uniform(70, 210) * (w_avg / 60) ** 0.5
            ang = math.radians(rng.uniform(25, 60))
            x0 = x + pad + side * w_avg * 0.05   # gövdenin içinden başlar (gövde üstüne çizilir)
            p2 = (x0 + side * math.sin(ang) * ln, y0 - math.cos(ang) * ln * 0.55 + rng.uniform(-10, 30))
            p1 = ((x0 + p2[0]) / 2, (y0 + p2[1]) / 2 - rng.uniform(0, 18))
            pts = bezier((x0, y0), p1, p2, 12)
            wd = np.linspace(rng.uniform(5, 9) * (w_avg / 60) ** 0.6, 1.2, 12)
            k = 1 - dark_top * (1 - smoothstep(0, 520, y0))
            bc = tuple(np.array(bark) * k)
            twigs = []
            for _t in range(int(rng.integers(2, 5))):
                j = int(rng.integers(3, 10))
                tq = pts[j]
                ta = math.atan2(pts[j + 1][1] - pts[j - 1][1], pts[j + 1][0] - pts[j - 1][0]) + rng.choice([-1, 1]) * rng.uniform(0.5, 1.0)
                tl = rng.uniform(16, 40)
                te = (tq[0] + math.cos(ta) * tl, tq[1] + math.sin(ta) * tl)
                twigs.append((bezier(tq, ((tq[0] + te[0]) / 2, (tq[1] + te[1]) / 2 - 4), te, 6), wd[j] * 0.45))
            for dx in (0, LW, -LW):
                q = pts + np.array([dx, 0])
                sk.path(ribbon(q, wd), bc, 1.0)
                if ink_k > 0.3:
                    sk.path(ribbon(q, wd), INK, 0.9, 0, 1.2 * ink_k)
                for tp, tw in twigs:
                    sk.path(ribbon(tp + np.array([dx, 0]), np.linspace(max(1.0, tw), 0.4, 6)), bc if ink_k <= 0.3 else INK, 0.9)
            # yaprak öbekleri
            for t in (0.6, 1.0):
                q = pts[int(t * 11)]
                lc = tuple(np.array(leaf_col) * k)
                for dx in (0, LW, -LW):
                    foliage(sk, q[0] + dx, q[1] + 6, rng.uniform(18, 34), int(rng.integers(1 << 30)), lc,
                            tuple(np.array(leaf_hi) * k), n=int(rng.uniform(26, 46)), ink_a=0.5 * ink_k)
    arr = sk.snap()[:, ik.P(pad):ik.P(pad) + L.w].copy()
    apply_fog(arr, 0, SKY, fog)
    L.over(arr)


def canopy(L, seed, y_max, col, hi, fog, n=14, size=(60, 140)):
    """Tepeden sarkan koyu yapraklı dal kümeleri (sahnenin üst kenarı loş, referanstaki gibi)."""
    rng = np.random.default_rng(seed)
    pad = 300
    LW = L.w / ik.K
    sk = Sk(LW + 2 * pad, H)
    for _ in range(n):
        x = rng.uniform(0, LW) + pad
        y = rng.uniform(-30, y_max)
        r = rng.uniform(*size)
        # sarkan ince saplar
        for k in range(rng.integers(3, 7)):
            sx = x + rng.uniform(-r, r)
            ln = rng.uniform(40, 140)
            pts = bezier((sx, -10), (sx + rng.uniform(-20, 20), y * 0.5), (sx + rng.uniform(-30, 30), y + ln * 0.4), 10)
            for dx in (0, LW, -LW):
                sk.path(ribbon(pts + np.array([dx, 0]), np.linspace(3, 1, 10)), col, 1.0)
            for j in range(3, 10, 2):
                q = pts[j]
                for dx in (0, LW, -LW):
                    foliage(sk, q[0] + dx, q[1], rng.uniform(10, 22), int(rng.integers(1 << 30)), col, hi,
                            n=int(rng.uniform(10, 22)), leaf=(10, 20), droop=0.8)
        for dx in (0, LW, -LW):
            foliage(sk, x + dx, y, r, int(rng.integers(1 << 30)), col, hi, n=int(r * 1.3), leaf=(12, 24), droop=0.6)
    arr = sk.snap()[:, ik.P(pad):ik.P(pad) + L.w].copy()
    apply_fog(arr, 0, SKY, fog)
    L.over(arr)


def watchtower(sk, x, base_y, h, w, col, ink_a=1.0, ink_w=2.0, rope=(150, 136, 100)):
    """Ahşap gözetleme kulesi siluet çizimi: dört ayak (ikisi görünür), çapraz destekler, üstte tahta döşeme ve
    korkuluk, halat bağları. Referanstaki bambu kuleye karşılık Türk yaylası ahşap gözcü kulesi."""
    top = base_y - h
    legs = [(x - w / 2, x - w / 2 + w * 0.06), (x + w / 2, x + w / 2 - w * 0.06)]
    lw = max(6, w * 0.07)
    for (xb, xt) in legs:
        p = poly_path([(xb - lw / 2, base_y), (xb + lw / 2, base_y), (xt + lw / 2 * 0.8, top), (xt - lw / 2 * 0.8, top)])
        sk.path(p, col)
        if ink_a > 0:
            sk.path(p, INK, ink_a, 0, ink_w)
    # çapraz destekler (iki kat X) ve yatay kirişler
    for lv in range(2):
        y0 = base_y - h * (0.1 + 0.45 * lv)
        y1 = base_y - h * (0.5 + 0.45 * lv) + h * 0.02
        for a, b in (((x - w / 2 + 4, y0), (x + w / 2 - 4, y1)), ((x + w / 2 - 4, y0), (x - w / 2 + 4, y1))):
            p = ribbon([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 3), b], [lw * 0.55] * 3)
            sk.path(p, col)
            if ink_a > 0:
                sk.path(p, INK, ink_a, 0, ink_w * 0.8)
        yb = y1
        p = poly_path([(x - w / 2 - 6, yb - lw * 0.35), (x + w / 2 + 6, yb - lw * 0.35), (x + w / 2 + 6, yb + lw * 0.35), (x - w / 2 - 6, yb + lw * 0.35)])
        sk.path(p, col)
        if ink_a > 0:
            sk.path(p, INK, ink_a, 0, ink_w * 0.8)
    # döşeme ve korkuluk
    deck = poly_path([(x - w / 2 - 22, top - 4), (x + w / 2 + 22, top - 4), (x + w / 2 + 18, top + 10), (x - w / 2 - 18, top + 10)])
    sk.path(deck, col)
    if ink_a > 0:
        sk.path(deck, INK, ink_a, 0, ink_w)
    for xx in np.linspace(x - w / 2 - 14, x + w / 2 + 14, 6):
        p = poly_path([(xx - 2.5, top - 4), (xx + 2.5, top - 4), (xx + 2, top - 40), (xx - 2, top - 40)])
        sk.path(p, col)
    rail = poly_path([(x - w / 2 - 18, top - 42), (x + w / 2 + 18, top - 42), (x + w / 2 + 18, top - 36), (x - w / 2 - 18, top - 36)])
    sk.path(rail, col)
    if ink_a > 0:
        sk.path(rail, INK, ink_a, 0, ink_w * 0.8)
    for (xb, xt) in legs:
        for yy in (top + 18, base_y - h * 0.55):
            k = (base_y - yy) / h
            xx = xb + (xt - xb) * k
            for j in range(3):
                sk.path(ribbon([(xx - lw * 0.7, yy + j * 4), (xx, yy + j * 4 + 2), (xx + lw * 0.7, yy + j * 4)], [2, 3, 2]), rope, 0.9)


def balbal(sk, x, base_y, h, col, hi, seed, ink_a=1.0):
    """Balbal: yuvarlak başlı dikili taş insan figürü; oyulmuş yüz, bıyık, göğüste kap tutan eller."""
    rng = np.random.default_rng(seed)
    w = h * rng.uniform(0.34, 0.42)
    pts = [(x - w / 2, base_y), (x - w / 2 * 1.05, base_y - h * 0.55), (x - w / 2 * 0.92, base_y - h * 0.8),
           (x - w * 0.3, base_y - h * 0.97), (x, base_y - h), (x + w * 0.3, base_y - h * 0.97),
           (x + w / 2 * 0.92, base_y - h * 0.8), (x + w / 2 * 1.02, base_y - h * 0.5), (x + w / 2, base_y)]
    body = smooth_path(pts, True, 0.35)
    sk.path(body, col)
    sk.path(smooth_path([(x - w / 2 * 0.95, base_y - h * 0.6), (x - w * 0.35, base_y - h * 0.92), (x, base_y - h * 0.98),
                         (x - w * 0.1, base_y - h * 0.7), (x - w * 0.38, base_y - h * 0.3)], True, 0.4), hi, 0.55)
    if ink_a > 0:
        sk.path(body, INK, ink_a, 0, 2.4)
        fy = base_y - h * 0.78
        for sx in (-1, 1):
            sk.path(ribbon([(x + sx * w * 0.08, fy), (x + sx * w * 0.22, fy - 2), (x + sx * w * 0.3, fy + 1)], [0.6, 1.8, 0.6]), INK, ink_a * 0.9)
        sk.path(ribbon([(x, fy + 2), (x - 1, fy + h * 0.07)], [1.4, 1.0]), INK, ink_a * 0.8)
        my = fy + h * 0.1
        sk.path(ribbon([(x - w * 0.24, my + 3), (x - w * 0.1, my), (x, my + 1), (x + w * 0.1, my), (x + w * 0.24, my + 3)], [0.5, 1.6, 1.2, 1.6, 0.5]), INK, ink_a * 0.9)
        cy_ = base_y - h * 0.42
        sk.path(ribbon([(x - w * 0.38, cy_ - 10), (x - w * 0.12, cy_), (x + w * 0.05, cy_ - 2)], [0.6, 2.0, 1.0]), INK, ink_a * 0.8)
        sk.path(smooth_path([(x - w * 0.06, cy_ - 8), (x + w * 0.14, cy_ - 8), (x + w * 0.11, cy_ + 4), (x - w * 0.03, cy_ + 4)], True, 0.3), INK, ink_a * 0.7, 0, 1.4)


def mounds(L, seed, base_y, n, rx, ry, col, fog, blur=6.0, jit=20):
    """Gövde diplerinde çalılık / toprak tümsekleri (yumuşak kenarlı siluet)."""
    rng = np.random.default_rng(seed)
    sk = Sk(L.w / ik.K + 2 * 300, H)
    for _ in range(n):
        x = rng.uniform(0, L.w / ik.K) + 300
        y = base_y + rng.uniform(-jit, jit)
        p = blob(x, y, rx * rng.uniform(0.6, 1.4), ry * rng.uniform(0.6, 1.3), int(rng.integers(1 << 30)), n=16, jitter=0.18)
        sk.path(p, col, 1.0, blur)
    arr = sk.snap()
    # sarma: taşan kenarlar öbür uca
    p3 = ik.P(300)
    core = arr[:, p3:p3 + L.w].copy()
    left = arr[:, :p3]
    right = arr[:, p3 + L.w:]
    core[:, L.w - p3:] = left + core[:, L.w - p3:] * (1 - left[..., 3:4])
    core[:, :p3] = right + core[:, :p3] * (1 - right[..., 3:4])
    apply_fog(core, 0, SKY, fog)
    L.over(core)


def grass_field(L, seed, y0, y1, density, col_top, col_bot, hmin, hmax, wmin=2.0, wmax=4.5, fog=None, lean=0.35,
                dark_strokes=0.25, light_strokes=0.2, fill=True, fill_blur=3, ink_tips=0.0):
    """Otluk: dolgu gradyanı + binlerce kavisli yaprak darbesi (koyu ve açık)."""
    rng = np.random.default_rng(seed)
    W = L.w / ik.K
    pad = 80
    sk = Sk(W + 2 * pad, H)
    if fill:
        # dolgu: üst kenar dalgalı
        top = []
        for x in np.linspace(-pad, W + pad, 120):
            top.append((x + pad, y0 + 8 + rng.uniform(-6, 6)))
        pts = top + [(W + 2 * pad, H + 10), (0, H + 10)]
        # dikey gradyan dolgu: skia gradyan gölgelendiricisi yerine iki aşamalı numpy boyama yapılır (aşağıda)
        sk.path(smooth_path(pts, True, 0.3), (255, 255, 255), 1.0, fill_blur)
    fillm = sk.mask()[:, ik.P(pad):ik.P(pad) + L.w] if fill else None
    ys = ik.axis(H)
    grad = mix(c01(col_top)[None, :], c01(col_bot)[None, :], smoothstep(y0, y1, ys)[:, None])
    layer_rgb = np.repeat(grad[:, None, :], L.w, 1)
    nz = fbm(W, H, [30, 10], seed + 1)
    layer_rgb *= (1 + 0.07 * nz[..., None])
    out = Layer(W, H)
    if fill:
        out.a = premul(layer_rgb, fillm)
    # yapraklar
    sk2 = Sk(W + 2 * pad, H)
    count = int(density * W)
    for _ in range(count):
        x = rng.uniform(-pad, W + pad) + pad
        y = rng.uniform(y0, y1 + 30)
        depth = smoothstep(y0, y1, y)
        h = rng.uniform(hmin, hmax) * (0.7 + 0.6 * depth)
        r = rng.random()
        t_y = smoothstep(y0, y1, y)
        base_c = mix(c01(col_top), c01(col_bot), t_y)
        if r < dark_strokes:
            c = base_c * rng.uniform(0.45, 0.7)
        elif r < dark_strokes + light_strokes:
            c = np.minimum(base_c * rng.uniform(1.18, 1.45) + 0.03, 1)
        else:
            c = base_c * rng.uniform(0.85, 1.1)
        ln_, wd_ = rng.uniform(-lean, lean), rng.uniform(wmin, wmax)
        sk2.path(blade(x, y, h, ln_, wd_), tuple(c * 255), rng.uniform(0.75, 1.0))
        if ink_tips > 0 and rng.random() < ink_tips:
            sk2.path(blade_tip(x, y, h, ln_, wd_, rng.uniform(0.18, 0.4)), INK, rng.uniform(0.5, 0.85))
        elif ink_tips > 0 and rng.random() < ink_tips * 0.6:
            sk2.path(blade_spine(x, y, h, ln_, wd_, side=1.0 if ln_ < 0 else -1.0), INK, rng.uniform(0.4, 0.7))
    bl = sk2.snap()[:, ik.P(pad):ik.P(pad) + L.w]
    # kenar sarması (blade'ler pad içinde tekrar çizilmedi; yatay döşemede kenar farkı ince ot çizgisi kadardır)
    out.a = bl + out.a * (1 - bl[..., 3:4])
    if fog is not None:
        apply_fog(out.a, 0, SKY, fog)
    L.over(out.a)


def ferns(L, seed, base_y, n, size, col, fog, jit=10, dark=False):
    """Eğrelti / genç fidan kümeleri: merkezden kavisli saplar, iki yana yaprakçıklar."""
    rng = np.random.default_rng(seed)
    pad = 200
    sk = Sk(L.w / ik.K + 2 * pad, H)
    for _ in range(n):
        x0 = rng.uniform(0, L.w / ik.K) + pad
        y0 = base_y + rng.uniform(-jit, jit)
        s = size * rng.uniform(0.6, 1.3)
        for k in range(rng.integers(3, 7)):
            ang = math.radians(rng.uniform(-75, 75)) - math.pi / 2
            ln = s * rng.uniform(0.6, 1.0)
            bend = rng.uniform(0.2, 0.5) * np.sign(math.cos(ang) + 1e-3)
            p0 = np.array([x0, y0])
            p2 = p0 + np.array([math.cos(ang), math.sin(ang)]) * ln + np.array([bend * ln * 0.5, ln * 0.25])
            p1 = p0 + np.array([math.cos(ang), math.sin(ang)]) * ln * 0.6
            pts = bezier(p0, p1, p2, 14)
            cc = np.array(col, np.float32) / 255 * rng.uniform(0.8, 1.15)
            sk.path(ribbon(pts, np.linspace(2.4, 0.6, 14)), tuple(cc * 255), 1.0)
            for j in range(2, 13, 1):
                q = pts[j]
                tan = pts[j + 1] - pts[j - 1]
                ta = math.atan2(tan[1], tan[0])
                ll = s * 0.16 * (1 - j / 16)
                for sgn in (-1, 1):
                    sk.path(leaf_shape(q[0], q[1], ll, ll * 0.32, ta + sgn * 1.0), tuple(cc * 255 * rng.uniform(0.85, 1.1)), 1.0)
    arr = sk.snap()
    pp = ik.P(pad)
    core = arr[:, pp:pp + L.w].copy()
    l, r = arr[:, :pp], arr[:, pp + L.w:]
    core[:, L.w - pp:] = l + core[:, L.w - pp:] * (1 - l[..., 3:4])
    core[:, :pp] = r + core[:, :pp] * (1 - r[..., 3:4])
    apply_fog(core, 0, SKY, fog)
    L.over(core)


def rock(seed, rx, ry, base=(92, 98, 90), moss=(84, 120, 82), ink_w=3.0, light_dir=(-0.6, -0.8)):
    """Mürekkep konturlu, hücre gölgeli yuvarlak kaya (üstü yosunlu, altı toprağa gömülü).
    -> önçarpılmış dizi; kökeni alt orta (place ile y_base'e oturur)."""
    rng = np.random.default_rng(seed)
    ry = max(ry, rx * 0.55)
    cut = 0.55                                   # elipsin alt %22'si toprakta
    w, h = int(rx * 2 + 16), int(ry * (1 + cut) + 16)
    cx, cy = w / 2, ry + 8
    pts = []
    for i in range(14):
        a = 2 * math.pi * i / 14
        r = 1 + rng.uniform(-0.09, 0.09)
        px, py = cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r
        py = min(py, cy + ry * cut)
        pts.append((px, py))
    path = smooth_path(pts, True, 0.5)
    m = Sk(w, h)
    m.path(path, (255, 255, 255))
    cov = m.mask()
    import inkkit_ortam as ik
    ys, xs = (np.mgrid[0:cov.shape[0], 0:cov.shape[1]].astype(np.float32) + 0.5) / ik.K
    u = (xs - cx) / rx
    v = (ys - cy) / ry
    nzf = fbm(w, h, [5, 2], seed + 2, wrap=False)
    # yontulmuş yüzeyler (Voronoi düz normalleri) + hafif küre gölgesi
    ndl, fedge, fid = facet_shade(u, v, seed + 4, n=max(6, int(rx / 7)), light=light_dir)
    ndl = ndl + 0.08 * nzf
    tone = np.where(ndl > 0.8, 1.24, np.where(ndl > 0.5, 1.0, np.where(ndl > 0.18, 0.74, 0.5))).astype(np.float32)
    from scipy import ndimage
    tone = ndimage.gaussian_filter(tone, ik.hd_sigma(0.6))
    # yüz kenarları: gölgeye bakan yüzlerin kenarında mürekkep, ışıktakilerde açık yontu çizgisi
    ew = np.clip(1.0 - fedge * rx * ik.K / (1.3 * ik.K), 0, 1) * cov
    tone = np.where(ndl > 0.55, tone * (1 + 0.22 * ew), tone)
    col = c01(base)[None, None, :] * tone[..., None]
    col *= (1 + 0.06 * nzf[..., None])
    # yosun: tepede, düzensiz alt sınır
    mossm = smoothstep(-0.05, 0.12, -v - 0.35 + 0.25 * nzf) * cov
    col = mix(col, c01(moss)[None, None, :] * (0.75 + 0.35 * tone[..., None]), (mossm * 0.85)[..., None])
    ink_e = ew * np.clip((0.5 - ndl) * 2.5, 0, 1) * 0.85
    col = mix(col, c01(INK)[None, None, :], ink_e[..., None])
    out = premul(col, cov)
    sk = Sk(w, h)
    sk.path(path, INK, 1.0, 0, ink_w)
    # gölge tarafı tarama + çatlaklar
    for _ in range(rng.integers(2, 5)):
        x0 = rng.uniform(cx - rx * 0.6, cx + rx * 0.5)
        y0 = rng.uniform(cy - ry * 0.2, cy + ry * 0.4)
        q = [(x0 + k * rng.uniform(4, 9), y0 + k * rng.uniform(-3, 5)) for k in range(4)]
        sk.path(ribbon(q, [0.4, 1.8, 1.4, 0.3]), INK, 0.75)
    for k in range(int(rx / 6)):
        y0 = cy + rng.uniform(-0.1, 0.5) * ry
        x0 = cx + rx * rng.uniform(0.35, 0.8)
        sk.path(ribbon([(x0, y0), (x0 + 5, y0 - 7)], [1.2, 0.3]), INK, 0.45)
    ink = sk.snap() * (cov[..., None] > 0.02)
    out = ink + out * (1 - ink[..., 3:4])
    return out


def place(L, arr, x, y_base, fog=None):
    """Kökeni alt orta olan parçayı yerleştir (sisle)."""
    h, w = arr.shape[:2]
    a = arr.copy()
    yt = int(y_base - h / ik.K + 8)
    if fog is not None:
        apply_fog(a, ik.P(yt), SKY, fog)
    L.over_wrap(a, int(x - w / ik.K / 2), yt)


# ------------------------------------------------------------------ paralaks katmanları
def layer_far(seed=20):
    L = Layer(WL, H)
    canopy(L, seed + 4, 160, (58, 70, 62), (80, 96, 82), fog_amount(0.55, 0.0, top=0.1), n=16, size=(80, 160))
    fog = fog_amount(0.6, 0.3, 600, 120, top=0.14)
    trunk_row(L, seed, 76, 6, 16, 600, fog, ink_k=0.0, detail=0.3, ink_mix=1.0, bark_pine=(66, 76, 68),
              bark_birch=(110, 124, 108), lean_max=0.05)
    mounds(L, seed + 1, 600, 26, 220, 50, (72, 94, 74), fog_amount(0.55, 0.3, 610, 60), blur=10)
    return L


def layer_farmid(seed=30):
    L = Layer(WL, H)
    canopy(L, seed + 4, 190, (44, 50, 46), (72, 90, 72), fog_amount(0.4, 0.0, top=0.1), n=14, size=(70, 140))
    fog = fog_amount(0.32, 0.44, 615, 90, top=0.1)
    trunk_row(L, seed, 52, 12, 28, 620, fog, ink_k=0.5, detail=0.5, ink_mix=0.6, bark_pine=(60, 62, 58),
              bark_birch=(122, 132, 118), dark_top=0.3, lean_max=0.05, branches=0.25, leaf_col=(52, 62, 52))
    mounds(L, seed + 1, 625, 30, 140, 46, (62, 86, 64), fog_amount(0.35, 0.35, 620, 50), blur=5)
    ferns(L, seed + 2, 628, 26, 46, (60, 84, 62), fog_amount(0.42, 0.3, 625, 40))
    return L


def layer_mid(seed=40):
    L = Layer(WL, H)
    canopy(L, seed + 4, 200, (36, 36, 40), (66, 84, 66), fog_amount(0.22, 0.0, top=0.06), n=12, size=(70, 130))
    fog = fog_amount(0.2, 0.42, 640, 80, top=0.08)
    # gözetleme kulesi ve balballar (sise gömülü)
    pad = 300
    sk = Sk(WL + 2 * pad, H)
    watchtower(sk, 2620 + pad, 652, 330, 120, (70, 62, 56), ink_a=0.8, ink_w=2.0)
    rng = np.random.default_rng(seed + 8)
    for k, xb in enumerate((900, 960, 3300)):
        balbal(sk, xb + pad, 660 + rng.uniform(-3, 3), rng.uniform(70, 92), (104, 110, 100), (140, 150, 134), seed + k, ink_a=0.7)
    arr = sk.snap()[:, ik.P(pad):ik.P(pad + WL)].copy()
    apply_fog(arr, 0, SKY, fog_amount(0.28, 0.34, 640, 60, top=0.08))
    L.over(arr)
    trunk_row(L, seed, 34, 20, 44, 650, fog, ink_k=0.8, detail=0.8, ink_mix=0.25, bark_pine=(50, 42, 48),
              bark_birch=(118, 124, 108), dark_top=0.5, lean_max=0.04, branches=0.5, leaf_col=(44, 52, 44),
              leaf_hi=(104, 128, 100))
    mounds(L, seed + 1, 655, 24, 120, 40, (58, 84, 60), fog_amount(0.25, 0.3, 650, 40), blur=3)
    rng = np.random.default_rng(seed + 5)
    for _ in range(9):
        r = rock(int(rng.integers(1 << 30)), rng.uniform(26, 50), rng.uniform(18, 32), base=(96, 102, 92))
        place(L, r, rng.uniform(0, WL), 664 + rng.uniform(-6, 8), fog_amount(0.32, 0.2, 650, 40))
    ferns(L, seed + 2, 662, 34, 60, (58, 88, 60), fog_amount(0.25, 0.25, 655, 40))
    grass_field(L, seed + 3, 652, 760, 0.45, (112, 150, 110), (52, 72, 54), 10, 28, 1.6, 3.2,
                fog=fog_amount(0.12, 0.38, 650, 26), ink_tips=0.18)
    return L


def layer_near(seed=50):
    L = Layer(WL, H)
    canopy(L, seed + 4, 150, (30, 26, 34), (62, 78, 62), fog_amount(0.0, 0.0), n=10, size=(80, 150))
    fog = fog_amount(0.05, 0.42, 690, 60, top=0.0)
    xs = np.array([150, 520, 610, 1180, 1690, 1760, 2300, 2840, 3330, 3420], np.float32)
    xs += np.random.default_rng(seed).uniform(-40, 40, xs.size)
    wsz = np.array([84, 60, 48, 92, 72, 50, 80, 66, 88, 52], np.float32)
    trunk_row(L, seed, len(xs), 46, 92, 700, fog, ink_k=1.0, detail=1.0, ink_mix=0.0, bark_pine=(46, 36, 44),
              bark_birch=(108, 112, 100), dark_top=0.65, xs=xs, base_jit=8, lean_max=0.02, birch_light=(140, 146, 128),
              rim=(206, 236, 200),
              branches=0.6, leaf_col=(36, 40, 38), leaf_hi=(92, 116, 90), ws=wsz)
    pad = 300
    sk = Sk(WL + 2 * pad, H)
    rng = np.random.default_rng(seed + 8)
    for k, xb in enumerate((1460, 3060)):
        balbal(sk, xb + pad, 712, rng.uniform(100, 120), (98, 104, 94), (138, 148, 130), seed + 30 + k)
    arr = sk.snap()[:, ik.P(pad):ik.P(pad + WL)].copy()
    apply_fog(arr, 0, SKY, fog_amount(0.04, 0.3, 700, 40))
    L.over(arr)
    rng = np.random.default_rng(seed + 9)
    for _ in range(7):
        r = rock(int(rng.integers(1 << 30)), rng.uniform(40, 80), rng.uniform(28, 46), base=(86, 92, 82))
        place(L, r, rng.uniform(0, WL), 712 + rng.uniform(-4, 10), fog_amount(0.05, 0.25, 700, 30))
    ferns(L, seed + 2, 712, 30, 90, (50, 80, 54), fog_amount(0.05, 0.22, 700, 40))
    grass_field(L, seed + 3, 700, 900, 1.1, (104, 140, 98), (40, 54, 42), 16, 46, 2.0, 4.2,
                fog=fog_amount(0.22, 0.32, 705, 50), dark_strokes=0.35, ink_tips=0.3)
    return L


def layer_haze(seed=65):
    """Orta derinlik pusu (v15): uzak-orta ile orta katman arasında yükselen, kopuk sis tülleri. Gövdelerin alt yarısını
    yer yer yutar, derinlik katmanları arasında hava boşluğu hissi verir (yavaş sürüklenir, nefes alır)."""
    W = WL
    ys = ik.axis(H)[:, None]
    n1 = noise(W, H, 0, seed, sx=220, sy=40)
    n2 = noise(W, H, 0, seed + 1, sx=70, sy=24)
    n3 = noise(W, H, 0, seed + 2, sx=18, sy=60)      # dikey tüller
    band = np.exp(-((ys - 560) / 120.0) ** 2) * 0.8 + np.exp(-((ys - 430) / 90.0) ** 2) * 0.3
    a = band * np.clip(0.35 + 0.7 * n1 + 0.3 * n2 + 0.2 * n3, 0, 1)
    a = np.clip(a * 0.42, 0, 0.5).astype(np.float32)
    rgb = np.repeat(ik.hd_lin(SKY)[:, None, :], ik.P(W), 1) * 0.75 + c01(MINT)[None, None, :] * 0.25
    L = Layer(W, H)
    L.a = premul(rgb, a)
    return L


def layer_fogband(seed=60):
    """Sürüklenen yer sisi (ayrı katman, saydam): yatayda uzun, düşeyde ince şeritler."""
    W = WL
    ys = ik.axis(H)[:, None]
    n1 = noise(W, H, 0, seed, sx=140, sy=16)
    n2 = noise(W, H, 0, seed + 1, sx=50, sy=8)
    band = np.exp(-((ys - 640) / 70.0) ** 2) * 0.9 + np.exp(-((ys - 560) / 40.0) ** 2) * 0.35 + np.exp(-((ys - 730) / 40.0) ** 2) * 0.4
    a = band * np.clip(0.55 + 0.6 * n1 + 0.25 * n2, 0, 1)
    a = np.clip(a * 0.75, 0, 0.85).astype(np.float32)
    rgb = np.repeat(ik.hd_lin(SKY)[:, None, :], ik.P(W), 1) * 0.6 + c01(MINT)[None, None, :] * 0.4
    L = Layer(W, H)
    L.a = premul(rgb, a)
    return L


def layer_shafts(seed=70):
    """Işık hüzmeleri (toplamalı): üstten çapraz, geniş ve yumuşak; içleri hüzme boyunca ince çizgili."""
    W = 2880
    out = np.zeros((ik.P(H), ik.P(W)), np.float32)
    rng = np.random.default_rng(seed)
    ys = ik.axis(H)[:, None]
    xs = ik.axis(W)[None, :]
    ang = math.radians(24)     # düşeyden sapma
    s_, c_ = math.sin(ang), math.cos(ang)
    u_all = xs * c_ + ys * s_  # hüzme kesitine dik eksen (sağ üstten sol alta)
    # aralık temel piksel ızgarasından (HD'de aynı hüzme konumları)
    ub = np.arange(W, dtype=np.float32)[None, :] * c_ + np.arange(H, dtype=np.float32)[:, None] * s_
    umin, umax = float(ub.min()), float(ub.max())
    ugrid = np.linspace(umin, umax, 4096)
    streak1 = ik.noise_base(4096, 1, 0, seed + 3, sx=3.0, sy=0.01)[0]
    streak = np.interp(u_all, ugrid, streak1)
    for k in range(7):
        u0 = rng.uniform(umin + 200, umax - 100)
        wid = rng.uniform(50, 170)
        inten = rng.uniform(0.25, 0.6)
        out += np.exp(-((u_all - u0) / wid) ** 2) * inten
    v = ys / H
    fade = smoothstep(0.0, 0.1, v) * (1 - smoothstep(0.5, 0.74, v))
    # boyuna kırılma: hüzmeler yer yer kesilir (yaprak gölgesi)
    brk = np.clip(0.75 + 0.5 * noise(W, H, 0, seed + 5, sx=60, sy=90), 0.3, 1.0)
    out *= fade * (0.85 + 0.25 * streak) * brk
    out = np.clip(out, 0, 1)
    bl = 200
    blp = ik.P(bl)
    t = np.clip(ik.axis(bl) / (bl - 1), 0, 1)[None, :]
    out[:, :blp] = out[:, :blp] * t + out[:, -blp:] * (1 - t)
    out = out[:, :out.shape[1] - blp]
    col = c01((176, 226, 192))
    rgb = col[None, None, :] * out[..., None]
    L = Layer(W - bl, H)
    L.a = np.concatenate([rgb, out[..., None]], -1).astype(np.float32)
    return L
