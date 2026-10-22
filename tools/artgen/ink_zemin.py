"""Stil v2 "mürekkep" oyun alanı zemini, biyomdan bağımsız kurucu (otuken_ink_ground.py genellemesi).

Atlas yerleşimi Ötüken ile birebir aynı (16 sütun x 3 zemin satırı, örtü satırı, platform satırı; hücre mantıksal 48 piksel =
24 dünya birimi, çıktı inkkit.K katı). Biyom modülü bir "üslup" sözlüğü ve örtü / tavan / platform çizicileri verir:

  st = dict(surface='grass' | 'snow', light=+1 | -1, palet ..., blade_lean=..., ...)
  build_atlas(st, tuft_fn, ceil_fn, platform_fn)  -> (sanat RGBA, maske)

Zemin kenarları: mürekkep konturu + ışık tarafında ince kenar ışığı; üst kenarda ot bandı (kuru altın ot) ya da kar
başlığı (yuvarlak dudaklı kar, altında mavi gölge, buz saçağı). Maske: R toprak kaplaması, G kenar gölgesi.
"""
import math

import numpy as np
from scipy import ndimage

import inkkit_ortam as ik
from inkkit_ortam import (INK, Layer, Sk, blade, blade_spine, blade_tip, blob, c01, facet_shade, fbm, mix, noise,
                          poly_path, premul, ribbon, smooth_path, smoothstep, bezier)

C = 48
COLS = 16
ROWS = 5
GRASS_COLS = 8
CEIL_COLS = [8, 9, 10]
OROW = 3
PROW = 4


def _edge_offset(t, rng, amp, ends=1.0):
    k = rng.uniform(0, 10)
    v = (np.sin(t * math.pi * 2 * rng.uniform(1, 2.2) + k) * 0.5 + np.sin(t * math.pi * 2 * rng.uniform(3, 5) + 2 * k) * 0.3)
    env = np.sin(np.clip(t, 0, 1) * math.pi) ** 0.7
    return ends + (amp * (0.5 + 0.5 * v)) * env


def _grass_band(art, m, top_d, cov, seed, rng, st):
    K = ik.K
    CP = ik.P(C)
    band_d = st.get('band', 16) + 6 * noise(C, 1, 2, seed + 2, wrap=False)[0][None, :] + rng.uniform(-2, 2)
    g_t = np.clip(top_d / band_d, 0, 1.4)
    gcol = mix(c01(st['grass_top']), c01(st['grass_mid']), smoothstep(0.0, 0.7, g_t)[..., None])
    gcol = mix(gcol, c01(st['grass_dark']), smoothstep(0.6, 1.1, g_t)[..., None])
    gmask = (1 - smoothstep(0.85, 1.15, g_t)) * cov
    art_g = Layer(C, C)
    art_g.fill_mask(gmask, gcol)
    sk = Sk(C, C)
    lean_b = st.get('blade_lean', 0.0)
    for _ in range(int(st.get('blades', 70) * (1 if (m & 10) == 0 else 0.7))):
        x = rng.uniform(-2, C + 2)
        if (m & 8) and x < 6:
            continue
        if (m & 2) and x > C - 6:
            continue
        base = rng.uniform(4, 26)
        h = rng.uniform(5, 14) * st.get('blade_h', 1.0)
        r = rng.random()
        c = st['grass_dark'] if r < 0.4 else (st['grass_tip'] if r < 0.68 else st['grass_mid'])
        ln = rng.uniform(-0.45, 0.45) + lean_b
        wd = rng.uniform(1.3, 2.4)
        sk.path(blade(x, base, h, ln, wd), c, rng.uniform(0.6, 0.95))
        if rng.random() < st.get('blade_ink', 0.0):
            sk.path(blade_tip(x, base, h, ln, wd, 0.3), INK, 0.6)
    bl = sk.snap()
    bl *= gmask[..., None] ** 0.5
    art_g.a = bl + art_g.a * (1 - bl[..., 3:4])
    tip = (1 - smoothstep(0.5, 3.5, top_d)) * cov
    art_g.fill_mask(tip * 0.5, c01(st['grass_tip']))
    sk2 = Sk(C, C)
    for _ in range(rng.integers(4, 9)):
        x = rng.uniform(2, C - 2)
        y0 = float(band_d[0, int(np.clip(x * K, 0, CP - 1))]) * rng.uniform(0.8, 1.0)
        pts = [(x + k * rng.uniform(-1.5, 1.5), y0 + k * rng.uniform(2, 4)) for k in range(4)]
        sk2.path(ribbon(pts, [1.4, 1.0, 0.6, 0.2]), st.get('root_col', st['grass_dark']), 0.85)
    rt = sk2.snap() * cov[..., None]
    art_g.a = rt + art_g.a * (1 - rt[..., 3:4])
    art.a = art_g.a + art.a * (1 - art_g.a[..., 3:4])


def _snow_cap(art, m, top_d, cov, xs, ys, seed, rng, st):
    """Kar başlığı: üst kenarda kalın, yuvarlak kar; alt sınırında mavi gölge + mürekkep; üstte ışık, kristal parıltıları;
    yan açık kenarlarda (m & 2/8) dudaktan sarkan küçük buz saçakları."""
    K = ik.K
    env = np.sin(np.clip(xs[0:1, :] / C, 0, 1) * math.pi) ** 0.7
    th = st.get('snow_th', 11) + 3.5 * noise(C, 1, 3, seed + 4, wrap=False)[0][None, :] * env
    # yanlarda kar inceltilir (kenar köşesinde yuvarlanır)
    if m & 8:
        th = th * smoothstep(0, 10, xs) + 2.5 * (1 - smoothstep(0, 10, xs))
    if m & 2:
        th = th * smoothstep(0, 10, C - xs) + 2.5 * (1 - smoothstep(0, 10, C - xs))
    s_t = top_d / th
    smask = np.clip((th - top_d) * K + 0.5, 0, 1) * cov
    nz = noise(C, C, 2, seed + 6, wrap=False)
    # gölgelendirme: üst parlak, alta doğru mavi gölge; ışık tarafında daha açık
    lit = c01(st['snow_lit'])
    mid = c01(st['snow_mid'])
    sh = c01(st['snow_sh'])
    col = mix(lit[None, None, :], mid[None, None, :], smoothstep(0.15, 0.6, s_t)[..., None])
    col = mix(col, sh[None, None, :], smoothstep(0.55, 1.0, s_t)[..., None])
    col *= (1 + 0.035 * nz)[..., None]
    art.fill_mask(smask, col)
    # alt sınır mürekkebi (kesik, değişken kalınlık) + altında karın düşürdüğü gölge şeridi
    under = np.clip(1 - np.abs(top_d - th - 1.6) / 2.2, 0, 1) * cov * (top_d > th - 0.5)
    art.fill_mask(under * 0.45, c01(st.get('snow_shadow', (40, 40, 70))))
    inkm = np.clip(1 - np.abs(top_d - th) / (0.55 + 0.45 * (nz * 0.5 + 0.5)), 0, 1) * cov
    inkm *= smoothstep(-0.2, 0.3, noise(C, 1, 5, seed + 8, wrap=False)[0][None, :] * env + 0.3)
    art.fill_mask(inkm * 0.85, c01(INK))
    # üst kenarda soğuk ışık ve parıltı noktaları
    tip = (1 - smoothstep(0.3, 2.2, top_d)) * cov
    art.fill_mask(tip * 0.7, c01(st.get('snow_rim', (255, 255, 255))))
    sk = Sk(C, C)
    for _ in range(int(rng.integers(3, 8))):
        x = rng.uniform(3, C - 3)
        y = rng.uniform(1.5, 6)
        r = rng.uniform(0.5, 1.1)
        sk.c.drawCircle(x, y, r, sk.paint((255, 255, 255), rng.uniform(0.5, 0.9)))
    # rüzgâr dalga izleri (ince yatay mavi çizgiler)
    for _ in range(int(rng.integers(1, 3))):
        x = rng.uniform(0, C - 16)
        y = rng.uniform(4, 8)
        sk.path(ribbon([(x, y), (x + 8, y - 0.8), (x + 16, y + 0.2)], [0.2, 0.9, 0.2]), st['snow_sh'], 0.6)
    sp = sk.snap() * smask[..., None]
    art.a = sp + art.a * (1 - sp[..., 3:4])
    # buz saçakları: yan kenar köşesinde
    if (m & 1) and (m & 10):
        sk2 = Sk(C, C)
        sides = []
        if m & 8:
            sides.append(3.0)
        if m & 2:
            sides.append(C - 3.0)
        for sx in sides:
            for k in range(int(rng.integers(2, 4))):
                x = sx + (k * 3.5 if sx < C / 2 else -k * 3.5) + rng.uniform(-0.8, 0.8)
                y0 = 6 + rng.uniform(0, 3)
                ln = rng.uniform(6, 16) * (1 - k * 0.25)
                p = poly_path([(x - 1.6, y0), (x + 1.6, y0), (x + rng.uniform(-0.4, 0.4), y0 + ln)])
                sk2.path(p, st.get('ice', (196, 232, 246)), 0.95)
                sk2.path(ribbon([(x - 0.6, y0 + 1), (x - 0.2, y0 + ln * 0.7)], [0.7, 0.2]), (255, 255, 255), 0.8)
                sk2.path(p, INK, 0.8, 0, 0.7)
        ic = sk2.snap()
        art.a = ic + art.a * (1 - ic[..., 3:4])


def face_strokes(art, m, cov, d_left, d_right, d_top, rng, st, light=-1.0):
    """v40: yar yüzü fırça dokusu. Yana açık kenarın (m & 8 sol, m & 2 sağ) hemen içinde kısa yatay tortul / çatlak
    darbeleri (mürekkep, düşük alfa; ışık tarafında ince açık darbe), tepe köşesinden yüze sarkan birkaç ot / kök.
    Tek renkli toprak dokusunun üstüne "çizilmiş kaya yüzü" hissi verir; kaplama maskesi değişmez."""
    K = ik.K
    sides = []
    if m & 8 and d_left is not None:
        sides.append((-1.0, d_left))
    if m & 2 and d_right is not None:
        sides.append((1.0, d_right))
    if not sides:
        return
    sk = Sk(C, C)
    dark = st.get('face_dark', INK)
    lite = st.get('face_light', st.get('rim', (200, 200, 200)))
    hang = st.get('face_hang', None)        # (renk, sayı): sarkan ot / kök; None = yok
    for sgn, dd in sides:
        x_edge = 0.0 if sgn < 0 else float(C)
        lit = (sgn * light) > 0      # ışığa bakan yüz
        n = int(rng.integers(3, 6))
        for _ in range(n):
            y = rng.uniform(5, C - 3)
            ln = rng.uniform(7, 20)
            x0 = x_edge - sgn * rng.uniform(1.0, 3.5)
            pts = [(x0, y), (x0 - sgn * ln * 0.5, y + rng.uniform(-1.2, 1.2)), (x0 - sgn * ln, y + rng.uniform(-2, 2))]
            # tortul basamağı: üstte açık çizgi (ışık), hemen altında koyu gölge çizgisi
            sk.path(ribbon(pts, [1.6, 1.2, 0.3]), lite, rng.uniform(0.3, 0.5) * (1.0 if lit else 0.6))
            sk.path(ribbon([(p[0], p[1] + 1.6) for p in pts], [2.0, 1.4, 0.3]), dark, rng.uniform(0.45, 0.7))
        # kısa dikey çatlak
        for _ in range(int(rng.integers(1, 3))):
            y = rng.uniform(8, C - 14)
            x0 = x_edge - sgn * rng.uniform(4, 12)
            sk.path(ribbon([(x0, y), (x0 + rng.uniform(-1.5, 1.5), y + 5), (x0 + rng.uniform(-2, 2), y + rng.uniform(8, 16))], [0.2, 1.2, 0.2]), dark, 0.6)
        # tepe köşesinden sarkan ot / kök (yalnızca üst kenar da açıksa)
        if hang is not None and (m & 1) and d_top is not None:
            col, cnt = hang
            for k in range(int(rng.integers(cnt[0], cnt[1] + 1))):
                y0 = rng.uniform(3, 9)
                ln = rng.uniform(6, 16)
                x0 = x_edge - sgn * rng.uniform(2.5, 6.0)
                pts = [(x0, y0), (x0 + sgn * rng.uniform(0.5, 2.0), y0 + ln * 0.5), (x0 + sgn * rng.uniform(-1.0, 2.5), y0 + ln)]
                sk.path(ribbon(pts, [1.6, 1.1, 0.3]), col, rng.uniform(0.7, 0.95))
    s = sk.snap() * cov[..., None]
    art.a = s + art.a * (1 - s[..., 3:4])


def ground_cell(m, var, seed, st):
    """Bir zemin karosu: (sanat RGBA önçarpılmış, kaplama, ao). m: 1 üst, 2 sağ, 4 alt, 8 sol hava."""
    rng = np.random.default_rng(seed)
    K = ik.K
    CP = ik.P(C)
    ys, xs = (np.mgrid[0:CP, 0:CP].astype(np.float32) + 0.5) / K
    t_x = xs / C
    t_y = ys / C
    cov = np.ones((CP, CP), np.float32)
    d_top = d_right = d_bot = d_left = None
    if m & 1:
        off = _edge_offset(t_x[0], rng, 1.5, 0.5)
        d_top = ys - off[None, :]
        cov *= np.clip(d_top * K + 0.5, 0, 1)
    if m & 4:
        off = _edge_offset(t_x[0], rng, 3.0, 1.0)
        d_bot = (C - ys) - off[None, :]
        cov *= np.clip(d_bot * K + 0.5, 0, 1)
    if m & 8:
        off = _edge_offset(t_y[:, 0], rng, 4.0, 1.0)
        d_left = xs - off[:, None]
        cov *= np.clip(d_left * K + 0.5, 0, 1)
    if m & 2:
        off = _edge_offset(t_y[:, 0], rng, 4.0, 1.0)
        d_right = (C - xs) - off[:, None]
        cov *= np.clip(d_right * K + 0.5, 0, 1)
    R = st.get('corner_r', 14.0)
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
    if d_top is not None and R > 0:
        # köşede yuvarlanan üst yüzey: üst uzaklığı köşe yayına göre
        for need, cx in ((1 | 8, R), (1 | 2, C - R)):
            if (m & need) == need:
                inq = ((xs - cx) * (1 if cx > C / 2 else -1) > 0) & (ys < R)
                dd = R - 1 - np.hypot(xs - cx, ys - R)
                top_d = np.where(inq, np.minimum(top_d, dd), top_d)
    art = Layer(C, C)
    ao = np.zeros((CP, CP), np.float32)
    light = st.get('light', -1.0)
    if edge.min() < 90:
        ao = (1 - smoothstep(0, 12, edge)) * 0.55
        ink_w = 3.2 + 1.2 * noise(C, C, 4, seed + 1, wrap=False)
        ink = np.clip((ink_w - edge) * K + 0.5, 0, 1) * cov
        rim = np.zeros((CP, CP), np.float32)
        d_lit = d_left if light < 0 else d_right
        if d_lit is not None:
            rim = np.maximum(rim, np.clip(1 - np.abs(d_lit - ink_w - 1.6) / 1.4, 0, 1))
        art.fill_mask(rim * cov * st.get('rim_a', 0.55), c01(st['rim']))
        art.fill_mask(ink, c01(INK))
    if m & 1:
        if st.get('surface', 'grass') == 'snow':
            _snow_cap(art, m, top_d, cov, xs, ys, seed, rng, st)
        else:
            _grass_band(art, m, top_d, cov, seed, rng, st)
    if m & 4:
        bd = d_bot
        dark = (1 - smoothstep(0, 10, bd)) * cov * 0.5
        art.fill_mask(dark, c01(st.get('ceil_dark', (20, 18, 26))))
    if st.get('face_strokes', True):
        face_strokes(art, m, cov, d_left, d_right, d_top, rng, st, light)
    if var == 1 and (m & (2 | 8)) and not (m & 4) and st.get('rock_fn') is not None:
        side = 2 if (m & 2) else 8
        rr = st['rock_fn'](seed + 5, rng.uniform(9, 13), rng.uniform(7, 10))
        h_, w_ = rr.shape[:2]
        px = C - w_ / ik.K + 2 if side == 2 else -2
        py = int(rng.uniform(18, C - h_ / ik.K - 2))
        _blit(art, rr, px, py, cov)
    return art.a, cov, ao


def _blit(art, src, x, y, clip):
    h, w = src.shape[:2]
    x, y = ik.P(x), ik.P(y)
    CP = ik.P(C)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(CP, x + w), min(CP, y + h)
    s = src[y0 - y:y1 - y, x0 - x:x1 - x] * clip[y0:y1, x0:x1, None]
    d = art.a[y0:y1, x0:x1]
    art.a[y0:y1, x0:x1] = s + d * (1 - s[..., 3:4])


def rock_small(seed, rx, ry, base=(108, 112, 104), light=(-0.6, -0.8), cap=None):
    """Küçük yontulmuş, mürekkep konturlu taş (cap: üstüne kar başlığı rengi)."""
    w, h = int(rx * 2 + 6), int(ry * 2 + 6)
    cx, cy = w / 2, h / 2
    path = blob(cx, cy, rx, ry, seed, n=10, jitter=0.15)
    s = Sk(w, h)
    s.path(path, (255, 255, 255))
    cov = s.mask()
    ys, xs = (np.mgrid[0:cov.shape[0], 0:cov.shape[1]].astype(np.float32) + 0.5) / ik.K
    u = (xs - cx) / rx
    v = (ys - cy) / ry
    ndl, fedge, _ = facet_shade(u, v, seed + 9, n=max(4, int(rx / 3)), tilt=0.45, sphere=0.25, light=light)
    tone = np.where(ndl > 0.72, 1.22, np.where(ndl > 0.4, 0.95, np.where(ndl > 0.12, 0.72, 0.55))).astype(np.float32)
    tone = ndimage.gaussian_filter(tone, ik.hd_sigma(0.5))
    rgb = c01(base)[None, None, :] * tone[..., None]
    ew = np.clip(1.0 - fedge * rx * ik.K / (1.1 * ik.K), 0, 1)
    rgb = mix(rgb, c01(INK)[None, None, :], (ew * np.clip((0.45 - ndl) * 3.0, 0, 1) * 0.8)[..., None])
    if cap is not None:
        capm = smoothstep(-0.1, 0.1, -v - 0.25 + 0.2 * np.sin(u * 5 + seed)) * cov
        rgb = mix(rgb, c01(cap)[None, None, :] * (0.85 + 0.2 * smoothstep(-1, 0, -v))[..., None], capm[..., None])
    out = premul(rgb, cov)
    ink = Sk(w, h)
    ink.path(path, INK, 1.0, 0, 2.2)
    i = ink.snap()
    return i + out * (1 - i[..., 3:4])


def build_atlas(st, tuft_fn, ceil_fn, platform_fn, seed=500):
    CPX = ik.P(C)
    W, Hh = COLS * CPX, ROWS * CPX
    art = np.zeros((Hh, W, 4), np.float32)
    mask = np.zeros((Hh, W, 4), np.float32)
    mask[..., 3] = 1.0
    for v in range(3):
        for m in range(16):
            a, cov, ao = ground_cell(m, v, seed + m * 7 + v * 131, st)
            art[v * CPX:(v + 1) * CPX, m * CPX:(m + 1) * CPX] = a
            mask[v * CPX:(v + 1) * CPX, m * CPX:(m + 1) * CPX, 0] = cov
            mask[v * CPX:(v + 1) * CPX, m * CPX:(m + 1) * CPX, 1] = ao
    for k in range(GRASS_COLS):
        art[OROW * CPX:(OROW + 1) * CPX, k * CPX:(k + 1) * CPX] = tuft_fn(seed + 900 + k, k)
    for i, col in enumerate(CEIL_COLS):
        art[OROW * CPX:(OROW + 1) * CPX, col * CPX:(col + 1) * CPX] = ceil_fn(seed + 950 + i)
    for var in range(2):
        for kind in range(3):
            cx = (kind + 3 * var) * CPX
            art[PROW * CPX:(PROW + 1) * CPX, cx:cx + CPX] = platform_fn(kind, var, seed + 980 + kind + 10 * var)
    return art, mask


def tile_texture(S, seed, draw, base_rgb):
    """Dikişsiz döşenen dünya uzayı doku: base_rgb (h, w, 3) üstüne draw(sk, S, rng, put) ile işaretler; put(fn) her
    şekli 3x3 sarmalı çizer."""
    L = Layer(S, S)
    L.a = premul(base_rgb.astype(np.float32), np.ones(base_rgb.shape[:2], np.float32))
    sk = Sk(S, S)
    rng = np.random.default_rng(seed)

    def put(fn, x, y, margin=40):
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                if -margin < x + dx < S + margin and -margin < y + dy < S + margin:
                    fn(x + dx, y + dy)

    draw(sk, S, rng, put)
    dec = sk.snap()
    L.a = dec + L.a * (1 - dec[..., 3:4])
    return L


def crack_net(S, seed, n=60, jitter=0.35):
    """Döşenebilir kuru toprak çatlak ağı: Voronoi hücre kenarları -> (kenar uzaklığı (mantıksal), hücre kimliği)."""
    rng = np.random.default_rng(seed)
    pts = rng.uniform(0, S, (n, 2))
    P = ik.P(S)
    ys, xs = (np.mgrid[0:P, 0:P].astype(np.float32) + 0.5) / ik.K
    best = np.full((P, P), 1e9, np.float32)
    second = np.full((P, P), 1e9, np.float32)
    idx = np.zeros((P, P), np.int32)
    for i, (px, py) in enumerate(pts):
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                d = (xs - px - dx) ** 2 + ((ys - py - dy) * 1.6) ** 2
                upd = d < best
                second = np.where(upd, best, np.minimum(second, d))
                idx = np.where(upd, i, idx)
                best = np.where(upd, d, best)
    edge = np.sqrt(second) - np.sqrt(best)
    return edge, idx
