"""Kararan Ötüken v2 "mürekkep" oyun alanı: karo atlası (sanat + toprak kaplama maskesi), dünya uzayı toprak dokusu,
ön plan siluet şeritleri ve yaprak parçacığı.

Karo atlası v1 yerleşimini korur (16 sütun x 3 zemin satırı, örtü satırı, platform satırı); hücre mantıksal 48 piksel =
24 dünya birimi, çıktı inkkit.K (1,5) katı: 72 doku pikseli (v2 kamerası 1,5x yakın, 1080p'de 1:1). İki doku:
  otuken_v2.png       : RGBA sanat katmanı (ot bandı, mürekkep konturu, gömülü kayalar, ot öbekleri, tahta platform)
  otuken_v2_mask.png  : R = toprak kaplaması (dünya uzayı toprak dokusu burada görünür), G = kenar gölgesi (AO)
Oyunda ground_ink.gdshader: renk = sanat (alfa) ÜSTÜNE toprak(dünya konumu) x derinlik kararması; alfa = max(kaplama, sanat).
Maske CanvasTexture'ın normal yuvasında taşınır (v2 zemin normal haritası kullanmaz).
"""
import math
import numpy as np
from scipy import ndimage

import inkkit_ortam as ik

from inkkit_ortam import (INK, Layer, Sk, blade, blob, c01, fbm, leaf_shape, mix, noise, premul, ribbon, smooth_path,
                    smoothstep, bezier, poly_path)

C = 48                 # atlas hücresi (mantıksal piksel; çıktı ik.P(C))
COLS = 16
ROWS = 5
GRASS_COLS = 8
CEIL_COLS = [8, 9, 10]
OROW = 3
PROW = 4

# palet
GRASS_TIP = (132, 178, 132)
GRASS_TOP = (86, 128, 92)
GRASS_MID = (52, 84, 62)
GRASS_DARK = (30, 50, 42)
SOIL_A = (58, 50, 52)
SOIL_B = (74, 64, 60)
SOIL_C = (44, 38, 44)
RIM = (150, 196, 176)
WOOD = (104, 82, 64)
WOOD_D = (64, 48, 42)
WOOD_L = (150, 128, 100)
ROPE = (168, 150, 108)


def _edge_offset(t, rng, amp, ends=1.0):
    """Kenar boyunca düzensiz içe kayma; uçlarda sabit (komşu hücrelerle dikişsiz)."""
    k = rng.uniform(0, 10)
    v = (np.sin(t * math.pi * 2 * rng.uniform(1, 2.2) + k) * 0.5 + np.sin(t * math.pi * 2 * rng.uniform(3, 5) + 2 * k) * 0.3)
    env = np.sin(np.clip(t, 0, 1) * math.pi) ** 0.7
    return ends + (amp * (0.5 + 0.5 * v)) * env


def ground_cell(m, var, seed):
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
    # dış köşe yuvarlatma
    R = 14.0
    for need, cx, cy in ((1 | 8, R, R), (1 | 2, C - R, R), (4 | 8, R, C - R), (4 | 2, C - R, C - R)):
        if (m & need) == need:
            inq = ((xs - cx) * (1 if cx > C / 2 else -1) > 0) & ((ys - cy) * (1 if cy > C / 2 else -1) > 0)
            dd = np.hypot(xs - cx, ys - cy)
            cov = np.where(inq, cov * np.clip((R - 1 - dd) * K + 0.5, 0, 1), cov)
    # mesafe: açık kenara uzaklık (gölgeleme bantları için)
    edge = np.full((CP, CP), 99.0, np.float32)
    for d in (d_left, d_right, d_bot):
        if d is not None:
            edge = np.minimum(edge, d)
    top_d = d_top if d_top is not None else np.full((CP, CP), 99.0, np.float32)
    art = Layer(C, C)
    # --- kenar AO + mürekkep (yan ve alt)
    ao = np.zeros((CP, CP), np.float32)
    if edge.min() < 90:
        ao = (1 - smoothstep(0, 12, edge)) * 0.55
        ink_w = 3.2 + 1.2 * noise(C, C, 4, seed + 1, wrap=False)
        ink = np.clip((ink_w - edge) * K + 0.5, 0, 1) * cov
        # ışık sol üstten: sola bakan kenarlarda ince soğuk kenar ışığı (mürekkebin hemen içinde)
        rim = np.zeros((CP, CP), np.float32)
        if d_left is not None:
            rim = np.maximum(rim, np.clip(1 - np.abs(d_left - ink_w - 1.6) / 1.4, 0, 1))
        rimc = rim * cov * 0.55
        art.fill_mask(rimc, c01(RIM))
        art.fill_mask(ink, c01(INK))
    if m & 1:
        # --- ot bandı (üst kenar)
        band_d = 16 + 6 * noise(C, 1, 2, seed + 2, wrap=False)[0][None, :] + rng.uniform(-2, 2)
        g_t = np.clip(top_d / band_d, 0, 1.4)
        gcol = mix(c01(GRASS_TOP), c01(GRASS_MID), smoothstep(0.0, 0.7, g_t)[..., None])
        gcol = mix(gcol, c01(GRASS_DARK), smoothstep(0.6, 1.1, g_t)[..., None])
        gmask = (1 - smoothstep(0.85, 1.15, g_t)) * cov
        art_g = Layer(C, C)
        art_g.fill_mask(gmask, gcol)
        # yaprak darbeleri: band içinde yukarı bakan, koyu ve açık
        sk = Sk(C, C)
        for _ in range(int(70 * (1 if (m & 10) == 0 else 0.7))):
            x = rng.uniform(-2, C + 2)
            if (m & 8) and x < 6:
                continue
            if (m & 2) and x > C - 6:
                continue
            base = rng.uniform(4, 26)
            h = rng.uniform(5, 14)
            r = rng.random()
            c = GRASS_DARK if r < 0.45 else (GRASS_TIP if r < 0.7 else GRASS_MID)
            sk.path(blade(x, base, h, rng.uniform(-0.5, 0.5), rng.uniform(1.4, 2.6)), c, rng.uniform(0.6, 0.95))
        bl = sk.snap()
        bl *= gmask[..., None] ** 0.5
        art_g.a = bl + art_g.a * (1 - bl[..., 3:4])
        # ay ışığı üst kenarda: en üst 2-3 piksel açık uçlar
        tip = (1 - smoothstep(0.5, 3.5, top_d)) * cov
        art_g.fill_mask(tip * 0.5, c01(GRASS_TIP))
        # band altındaki kök saçakları (toprağa sarkan koyu ince çizgiler)
        sk2 = Sk(C, C)
        for _ in range(rng.integers(4, 9)):
            x = rng.uniform(2, C - 2)
            y0 = float(band_d[0, int(np.clip(x * K, 0, CP - 1))]) * rng.uniform(0.8, 1.0)
            pts = [(x + k * rng.uniform(-1.5, 1.5), y0 + k * rng.uniform(2, 4)) for k in range(4)]
            sk2.path(ribbon(pts, [1.4, 1.0, 0.6, 0.2]), GRASS_DARK, 0.85)
        rt = sk2.snap() * cov[..., None]
        art_g.a = rt + art_g.a * (1 - rt[..., 3:4])
        art.a = art_g.a + art.a * (1 - art_g.a[..., 3:4])
        ao = np.maximum(ao, 0.0)
    if m & 4:
        # tavan altı: koyu bant
        bd = d_bot
        dark = (1 - smoothstep(0, 10, bd)) * cov * 0.5
        art.fill_mask(dark, c01((20, 18, 26)))
    # --- gömülü kaya (değişkene göre, kenarda)
    if var == 1 and (m & (2 | 8)) and not (m & 4):
        side = 2 if (m & 2) else 8
        rr = rock_small(seed + 5, rng.uniform(9, 13), rng.uniform(7, 10))
        h_, w_ = rr.shape[:2]
        px = C - w_ / ik.K + 2 if side == 2 else -2
        py = int(rng.uniform(18, C - h_ / ik.K - 2))
        _blit(art, rr, px, py, cov)
    if False and var == 2 and (m & 1) and not (m & 10):
        rr = rock_small(seed + 6, rng.uniform(8, 12), rng.uniform(6, 8))
        h_, w_ = rr.shape[:2]
        _blit(art, rr, int(rng.uniform(4, C - w_ - 4)), int(rng.uniform(10, 20)), cov)
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


def rock_small(seed, rx, ry, base=(108, 112, 104)):
    """Küçük mürekkep konturlu, 3 tonlu taş."""
    w, h = int(rx * 2 + 6), int(ry * 2 + 6)
    cx, cy = w / 2, h / 2
    path = blob(cx, cy, rx, ry, seed, n=10, jitter=0.15)
    s = Sk(w, h)
    s.path(path, (255, 255, 255))
    cov = s.mask()
    ys, xs = (np.mgrid[0:cov.shape[0], 0:cov.shape[1]].astype(np.float32) + 0.5) / ik.K
    u = (xs - cx) / rx
    v = (ys - cy) / ry
    ndl = -0.55 * u - 0.75 * v + 0.35 * np.sqrt(np.clip(1 - u * u - v * v, 0, 1))
    tone = np.where(ndl > 0.45, 1.2, np.where(ndl > 0.0, 0.92, 0.62)).astype(np.float32)
    tone = ndimage.gaussian_filter(tone, 0.6)
    rgb = c01(base)[None, None, :] * tone[..., None]
    out = premul(rgb, cov)
    ink = Sk(w, h)
    ink.path(path, INK, 1.0, 0, 2.2)
    i = ink.snap()
    return i + out * (1 - i[..., 3:4])


def grass_tuft(seed, kind):
    """Örtü satırı ot öbeği (zeminin bir üst hücresi; taban hücre altında)."""
    rng = np.random.default_rng(seed)
    sk = Sk(C, C)
    n = [18, 26, 12, 34, 20, 14, 24, 30][kind % 8]
    hmax = [22, 30, 16, 36, 26, 18, 28, 40][kind % 8]
    for _ in range(n):
        x = rng.uniform(3, C - 3)
        h = rng.uniform(6, hmax)
        r = rng.random()
        c = GRASS_DARK if r < 0.4 else (GRASS_TOP if r < 0.65 else (GRASS_TIP if r < 0.78 else GRASS_MID))
        sk.path(blade(x, C + 1, h, rng.uniform(-0.6, 0.6), rng.uniform(1.6, 3.0)), c, rng.uniform(0.8, 1.0))
    if kind in (2, 5):
        # küçük eğrelti filizi
        x0, y0 = rng.uniform(14, C - 14), C + 1
        for k in range(4):
            ang = math.radians(rng.uniform(-60, 60)) - math.pi / 2
            ln = rng.uniform(12, 20)
            p2 = (x0 + math.cos(ang) * ln, y0 + math.sin(ang) * ln)
            pts = bezier((x0, y0), ((x0 + p2[0]) / 2, (y0 + p2[1]) / 2 - 3), p2, 8)
            sk.path(ribbon(pts, np.linspace(1.8, 0.5, 8)), GRASS_MID)
            for j in range(2, 8):
                q = pts[j]
                for sgn in (-1, 1):
                    sk.path(leaf_shape(q[0], q[1], 4.5, 1.8, ang + sgn * 1.0), GRASS_TOP if sgn < 0 else GRASS_MID)
    if kind == 6:
        # birkaç küçük soluk çiçek (ak / mavi, Ötüken'in tek renk noktaları)
        for _ in range(3):
            x, y = rng.uniform(8, C - 8), rng.uniform(C - 22, C - 10)
            sk.path(blade(x, C + 1, C + 1 - y, 0.05, 1.2), GRASS_MID)
            c = (196, 214, 226) if rng.random() < 0.6 else (130, 160, 210)
            for k in range(5):
                a = k * 2 * math.pi / 5
                sk.c.drawCircle(x + math.cos(a) * 1.8, y + math.sin(a) * 1.8, 1.5, sk.paint(c))
            sk.c.drawCircle(x, y, 1.0, sk.paint((230, 210, 140)))
    return sk.snap()


def ceiling_roots(seed):
    rng = np.random.default_rng(seed)
    sk = Sk(C, C)
    for _ in range(rng.integers(3, 7)):
        x = rng.uniform(3, C - 3)
        ln = rng.uniform(10, 40)
        pts = [(x + math.sin(k * 0.9 + x) * 2.2 * k / 5, -1 + ln * k / 5) for k in range(6)]
        sk.path(ribbon(pts, np.linspace(2.6, 0.4, 6)), (36, 30, 34), 1.0)
    for _ in range(rng.integers(2, 5)):
        x = rng.uniform(3, C - 3)
        ln = rng.uniform(6, 18)
        pts = [(x + rng.uniform(-1, 1), -1 + ln * k / 4) for k in range(5)]
        sk.path(ribbon(pts, np.linspace(3.0, 0.6, 5)), GRASS_MID, 0.9)
    return sk.snap()


def platform_cell(kind, var, seed):
    """Tahta platform: üstte tahta döşeme (üst yüz açık, ön kiriş koyu), uçlarda dikme + halat bağı."""
    rng = np.random.default_rng(seed)
    sk = Sk(C, C)
    top, beam_y0, beam_y1 = 0.5, 5.5, 17.0
    # uç dikmesi (aşağı iner; kule ayakları Level'da devam eder)
    if kind in (0, 2):
        px = 9 if kind == 0 else C - 9
        post = poly_path([(px - 5, beam_y0), (px + 5, beam_y0), (px + 5.5, C + 1), (px - 5.5, C + 1)])
        sk.path(post, WOOD_D)
        sk.path(poly_path([(px - 5, beam_y0), (px - 1.5, beam_y0), (px - 2, C + 1), (px - 5.5, C + 1)]), WOOD)
        for k in range(3):
            yy = 22 + k * 8 + rng.uniform(-2, 2)
            sk.path(ribbon([(px - 3, yy), (px - 1, yy + 3), (px + 1, yy + 6)], [0.4, 1.3, 0.3]), INK, 0.7)
        sk.path(post, INK, 1.0, 0, 2.2)
    # ön kiriş (kabuklu kütük)
    x0 = 1.0 if kind == 0 else -2
    x1 = C - 1.0 if kind == 2 else C + 2
    beam = poly_path([(x0, beam_y0), (x1, beam_y0), (x1, beam_y1), (x0, beam_y1)])
    sk.path(beam, WOOD)
    sk.path(poly_path([(x0, beam_y1 - 4), (x1, beam_y1 - 4), (x1, beam_y1), (x0, beam_y1)]), WOOD_D)
    sk.path(poly_path([(x0, beam_y0), (x1, beam_y0), (x1, beam_y0 + 2.5), (x0, beam_y0 + 2.5)]), WOOD_L, 0.8)
    for k in range(4):
        xx = rng.uniform(2, C - 8)
        yy = rng.uniform(beam_y0 + 3, beam_y1 - 3)
        sk.path(ribbon([(xx, yy), (xx + 4, yy + 0.4), (xx + 9, yy - 0.3)], [0.3, 1.2, 0.3]), INK, 0.6)
    # üst döşeme: tahta uçları (ön yüzde kesit çizgileri) ve üst yüz
    deck = poly_path([(x0, top), (x1, top), (x1, beam_y0), (x0, beam_y0)])
    sk.path(deck, WOOD_L)
    xx = 0.0 if kind != 0 else 2.0
    while xx < C:
        wpl = rng.uniform(7, 11)
        if xx + wpl > C and kind == 2:
            break
        sk.path(ribbon([(xx, top), (xx + rng.uniform(-0.5, 0.5), beam_y0)], [1.3, 1.3]), INK, 0.8)
        xx += wpl
    # mürekkep konturu
    sk.path(poly_path([(x0, top), (x1, top), (x1, beam_y1), (x0, beam_y1)], closed=True) if kind != 1 else
            poly_path([(x0, top), (x1, top)], closed=False), INK, 1.0, 0, 2.4)
    if kind == 1:
        sk.path(poly_path([(x0, beam_y1), (x1, beam_y1)], closed=False), INK, 1.0, 0, 2.6)
        sk.path(poly_path([(x0, beam_y0), (x1, beam_y0)], closed=False), INK, 0.8, 0, 1.4)
    else:
        sk.path(poly_path([(x0, beam_y0), (x1, beam_y0)], closed=False), INK, 0.8, 0, 1.4)
    # halat bağı
    if kind in (0, 2) or var == 1:
        px = 9 if kind == 0 else (C - 9 if kind == 2 else C / 2)
        for k in range(4):
            yy = beam_y0 - 1 + k * 3.6
            pts = [(px - 7, yy), (px, yy + 1.6), (px + 7, yy + 0.4)]
            sk.path(ribbon(pts, [1.6, 2.6, 1.6]), ROPE)
            sk.path(ribbon(pts, [1.6, 2.6, 1.6]), INK, 0.9, 0, 0.8)
        if kind != 1:
            # sarkan halat ucu
            pts = [(px + 5, beam_y1), (px + 6, beam_y1 + 6), (px + 5, beam_y1 + 12)]
            sk.path(ribbon(pts, [2.0, 1.8, 1.2]), ROPE)
    return sk.snap()


def build_atlas(seed=500):
    CPX = ik.P(C)           # çıktı hücresi (piksel); çizim fonksiyonları mantıksal C ile çalışır
    W, Hh = COLS * CPX, ROWS * CPX
    art = np.zeros((Hh, W, 4), np.float32)
    mask = np.zeros((Hh, W, 4), np.float32)
    mask[..., 3] = 1.0
    for v in range(3):
        for m in range(16):
            a, cov, ao = ground_cell(m, v, seed + m * 7 + v * 131)
            art[v * CPX:(v + 1) * CPX, m * CPX:(m + 1) * CPX] = a
            mask[v * CPX:(v + 1) * CPX, m * CPX:(m + 1) * CPX, 0] = cov
            mask[v * CPX:(v + 1) * CPX, m * CPX:(m + 1) * CPX, 1] = ao
    for k in range(GRASS_COLS):
        art[OROW * CPX:(OROW + 1) * CPX, k * CPX:(k + 1) * CPX] = grass_tuft(seed + 900 + k, k)
    for i, col in enumerate(CEIL_COLS):
        art[OROW * CPX:(OROW + 1) * CPX, col * CPX:(col + 1) * CPX] = ceiling_roots(seed + 950 + i)
    for var in range(2):
        for kind in range(3):
            cx = (kind + 3 * var) * CPX
            art[PROW * CPX:(PROW + 1) * CPX, cx:cx + CPX] = platform_cell(kind, var, seed + 980 + kind + 10 * var)
    return art, mask


def soil_texture(seed=600, S=1024):
    """Dünya uzayı toprak dokusu: yumuşak boya katmanları (tortul bantlar), fırça izleri, seyrek mürekkepli çakıl ve kök."""
    rng = np.random.default_rng(seed)
    ys = (np.arange(ik.P(S), dtype=np.float32)[:, None] + 0.5) / ik.K
    warp = noise(S, S, 40, seed, sx=90, sy=30) * 26
    yy = ys + warp
    bands = np.sin(yy / S * 2 * math.pi * 7) * 0.5 + np.sin(yy / S * 2 * math.pi * 17 + 1.3) * 0.3
    nz = fbm(S, S, [60, 20, 6], seed + 1)
    t = np.clip(0.5 + 0.35 * bands + 0.3 * nz, 0, 1)
    rgb = mix(c01(SOIL_C), c01(SOIL_A), smoothstep(0.1, 0.55, t)[..., None])
    rgb = mix(rgb, c01(SOIL_B), smoothstep(0.6, 0.95, t)[..., None])
    # yatay fırça darbeleri (boya hissi)
    br = noise(S, S, 0, seed + 3, sx=24, sy=2.2)
    rgb *= (1 + 0.07 * br[..., None])
    L = Layer(S, S)
    L.a = premul(rgb, np.ones(rgb.shape[:2], np.float32))
    sk = Sk(S, S)
    # kökler
    for _ in range(46):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        pts = [(x, y)]
        ang = rng.uniform(0.2, 1.2) * (1 if rng.random() < 0.5 else -1) + math.pi / 2
        for k in range(8):
            ang += rng.uniform(-0.4, 0.4)
            ln = rng.uniform(6, 16)
            pts.append((pts[-1][0] + math.cos(ang) * ln, pts[-1][1] + math.sin(ang) * ln * 0.6))
        ws = np.linspace(rng.uniform(2, 4), 0.4, len(pts))
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                sk.path(ribbon([(p[0] + dx, p[1] + dy) for p in pts], ws), (30, 24, 30), 0.7)
    # çakıllar (mürekkep konturlu, küçük)
    for _ in range(70):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        rx = rng.uniform(3, 14) if rng.random() < 0.8 else rng.uniform(14, 24)
        ry = rx * rng.uniform(0.5, 0.8)
        p = blob(x, y, rx, ry, int(rng.integers(1 << 30)), n=8, jitter=0.2)
        cc = np.array([96, 92, 90]) * rng.uniform(0.75, 1.15)
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                if -20 < x + dx < S + 20 and -20 < y + dy < S + 20:
                    q = blob(x + dx, y + dy, rx, ry, int(x * 1000) % 100000, n=8, jitter=0.2)
                    sk.path(q, tuple(cc), 1.0)
                    # üst kenar açık
                    sk.path(blob(x + dx - rx * 0.15, y + dy - ry * 0.3, rx * 0.6, ry * 0.45, 7, n=8, jitter=0.1), tuple(np.minimum(cc * 1.3, 255)), 0.8)
                    sk.path(q, INK, 0.9, 0, 1.6)
    dec = sk.snap()
    L.a = dec + L.a * (1 - dec[..., 3:4])
    return L


def meadow_texture(seed=650, S=512):
    """Dünya uzayı çayır dokusu (zeminin üst 2-3 karosu): sık, üst üste binen ot darbeleri; referanstaki oyun alanı
    otluğu. Dikişsiz döşenir (kenarlardan taşan darbeler öbür uçta da çizilir)."""
    rng = np.random.default_rng(seed)
    nz = fbm(S, S, [40, 12], seed + 1)
    base = mix(c01((44, 70, 52)), c01((58, 90, 62)), (0.5 + 0.5 * nz)[..., None])
    L = Layer(S, S)
    L.a = premul(base.astype(np.float32), np.ones(base.shape[:2], np.float32))
    sk = Sk(S, S)
    cols = [(30, 50, 40), (36, 58, 44), (70, 106, 72), (88, 128, 86), (112, 152, 104), (52, 84, 60)]
    wts = np.array([0.22, 0.2, 0.2, 0.16, 0.08, 0.14])
    for _ in range(5200):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        h = rng.uniform(10, 30)
        c = cols[int(rng.choice(len(cols), p=wts / wts.sum()))]
        pth_args = (rng.uniform(-0.45, 0.45), rng.uniform(1.4, 3.0))
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                xx, yy = x + dx, y + dy
                if -40 < xx < S + 40 and -10 < yy < S + 40:
                    sk.path(blade(xx, yy, h, pth_args[0], pth_args[1]), c, 0.9)
    bl = sk.snap()
    L.a = bl + L.a * (1 - bl[..., 3:4])
    return L


# ------------------------------------------------------------------ ön plan
FG_COL = (26, 10, 26)
FG_RIM = (92, 76, 96)


def fg_grass_strip(seed=700, W=3840, Hs=260):
    """Ekranın alt kenarındaki mor-siyah siluet otlar (aktörlerin önünde). Altı dolu, üstü seyrek uzun yapraklar."""
    rng = np.random.default_rng(seed)
    pad = 120
    sk = Sk(W + 2 * pad, Hs)
    base = Hs - 34
    # dolgu tabanı (dalgalı)
    pts = [(x, base + 18 + 14 * math.sin(x / 140.0 + 1) + rng.uniform(-6, 6)) for x in np.linspace(0, W + 2 * pad, 90)]
    pts += [(W + 2 * pad, Hs + 4), (0, Hs + 4)]
    sk.path(smooth_path(pts, True, 0.3), FG_COL)
    # ot yaprakları: çoğu kısa, kümeler halinde uzun
    clumps = rng.uniform(0, W, 34)
    for _ in range(int(W * 0.9)):
        if rng.random() < 0.45:
            x = rng.choice(clumps) + rng.normal(0, 40)
            hm = 150
        else:
            x = rng.uniform(0, W)
            hm = 72
        x += pad
        h = rng.uniform(18, hm) * (0.6 + 0.4 * rng.random())
        c = np.array(FG_COL, np.float32) * rng.uniform(0.8, 1.5)
        by, ln, wd = base + rng.uniform(10, 50), rng.uniform(-0.55, 0.55), rng.uniform(3.0, 6.5)
        # arkadaki sisten ince soluk kenar (siluet koyu zeminde de okunsun), üstüne koyu yaprak
        if h > 40 and rng.random() < 0.6:
            sk.path(blade(x - 1.6, by, h, ln, wd, curl=0.4), FG_RIM, 0.55)
        sk.path(blade(x, by, h, ln, wd, curl=0.4), tuple(c), 1.0)
    # yapraklı saplar (eğrelti / kır otu başakları)
    for _ in range(16):
        x0 = rng.uniform(0, W) + pad
        y0 = base + 20
        hgt = rng.uniform(80, 170)
        lean = rng.uniform(-0.25, 0.25)
        pts = bezier((x0, y0), (x0 + lean * hgt * 0.3, y0 - hgt * 0.6), (x0 + lean * hgt, y0 - hgt), 16)
        sk.path(ribbon(pts, np.linspace(4, 1, 16)), FG_COL)
        for j in range(3, 16, 2):
            q = pts[j]
            for sgn in (-1, 1):
                ln = rng.uniform(16, 34) * (1 - j / 22)
                sk.path(leaf_shape(q[0], q[1], ln, ln * 0.36, -math.pi / 2 + sgn * rng.uniform(0.6, 1.2) + lean), FG_COL)
    arr = sk.snap()
    core = arr[:, pad:pad + W].copy()
    l, r = arr[:, :pad], arr[:, pad + W:]
    core[:, W - pad:] = l + core[:, W - pad:] * (1 - l[..., 3:4])
    core[:, :pad] = r + core[:, :pad] * (1 - r[..., 3:4])
    L = Layer(W, Hs)
    L.a = core
    return L


def fg_top_strip(seed=720, W=3840, Hs=300):
    """Üst kenardan sarkan seyrek koyu ince dallar ve yaprak salkımları (köşeleri çerçeveler, oynanışa inmez)."""
    rng = np.random.default_rng(seed)
    pad = 300
    sk = Sk(W + 2 * pad, Hs)
    for cx in (260, 1180, 1460, 2480, 3300):
        x0 = cx + rng.uniform(-80, 80) + pad
        for k in range(rng.integers(2, 5)):
            sx = x0 + rng.uniform(-90, 90)
            ln = rng.uniform(70, 200)
            sway = rng.uniform(-50, 50)
            pts = bezier((sx, -12), (sx + sway * 0.3, ln * 0.5), (sx + sway, ln), 16)
            sk.path(ribbon(pts, np.linspace(5, 1.5, 16)), FG_COL)
            for j in range(2, 16):
                q = pts[j]
                for _ in range(2):
                    side = -1 if rng.random() < 0.5 else 1
                    ang = math.pi / 2 + side * rng.uniform(0.25, 0.9)
                    lnl = rng.uniform(18, 38) * (0.6 + 0.4 * j / 16)
                    c = FG_COL if rng.random() < 0.8 else FG_RIM
                    sk.path(leaf_shape(q[0], q[1], lnl, lnl * 0.34, ang), c, 1.0 if c == FG_COL else 0.5)
        # kök dal: üst kenarda yatay kalın dal parçası
        pts = bezier((x0 - 200, -6), (x0, 18), (x0 + 180, -4), 14)
        sk.path(ribbon(pts, np.linspace(14, 6, 14)), FG_COL)
    arr = sk.snap()
    core = arr[:, pad:pad + W].copy()
    l, r = arr[:, :pad], arr[:, pad + W:]
    core[:, W - pad:] = l + core[:, W - pad:] * (1 - l[..., 3:4])
    core[:, :pad] = r + core[:, :pad] * (1 - r[..., 3:4])
    L = Layer(W, Hs)
    L.a = core
    return L


def leaf_particle():
    sk = Sk(32, 16)
    sk.path(leaf_shape(2, 8, 28, 10, 0.0), (255, 255, 255))
    sk.path(ribbon([(2, 8), (28, 8)], [1.0, 0.4]), (170, 170, 170), 0.8)
    return sk.snap()
