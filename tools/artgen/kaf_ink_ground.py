"""Kaf Dağı v2 "mürekkep" oyun alanı: kar başlıklı zemin (yuvarlak dudak, mavi gölge, buz saçağı), arduvaz kaya (buz
damarlı, kırık yüzlü), kar örtüsü dokusu, örtü öbekleri (kırağılı kuru ot, kar tümseği, buz kristali, karlı ardıç,
kardelen), tavandan sarkan buz sarkıtları, karlı tahta platform (altında saçaklar), ön plan karlı çalı siluetleri ve
sarkan karlı ladin dalları. Işık soldan (ay / tan).
"""
import math

import numpy as np

import inkkit_ortam as ik
from hdpack import HD
from inkkit_ortam import (INK, Layer, Sk, bezier, blade, blade_tip, blob, c01, fbm, leaf_shape, mix, noise, poly_path,
                          premul, ribbon, smooth_path, smoothstep)
import ink_zemin as Z

C = Z.C
LIGHT = -1.0
SNOW_LIT = (240, 246, 255)
SNOW_MID = (194, 208, 240)
SNOW_SH = (124, 138, 198)
ICE = (176, 226, 246)
ICE_D = (84, 150, 200)

ST = dict(
    surface='snow', light=LIGHT,
    snow_lit=SNOW_LIT, snow_mid=SNOW_MID, snow_sh=SNOW_SH, snow_rim=(255, 255, 255), snow_shadow=(26, 26, 60),
    ice=ICE, rim=(176, 206, 255), rim_a=0.6, ceil_dark=(14, 14, 34), snow_th=11,
    grass_tip=(200, 196, 170), grass_top=(160, 150, 130), grass_mid=(110, 104, 110), grass_dark=(54, 52, 72),
    face_dark=(18, 16, 40), face_light=(190, 214, 255), face_hang=None,
)
ST['rock_fn'] = lambda seed, rx, ry: Z.rock_small(seed, rx, ry, base=(118, 126, 172), light=(-0.6, -0.8), cap=SNOW_LIT)

WOOD = (98, 78, 76)
WOOD_D = (54, 42, 50)
WOOD_L = (150, 130, 124)
ROPE = (150, 140, 120)


def _icicle(sk, x, y0, ln, w, a=1.0, ink_a=0.85):
    p = poly_path([(x - w, y0), (x + w, y0), (x + w * 0.25, y0 + ln * 0.75), (x, y0 + ln)])
    sk.path(p, ICE, 0.92 * a)
    sk.path(ribbon([(x - w * 0.5, y0 + 1), (x - w * 0.15, y0 + ln * 0.7)], [w * 0.5, 0.2]), (255, 255, 255), 0.85 * a)
    sk.path(ribbon([(x + w * 0.6, y0 + 1), (x + w * 0.2, y0 + ln * 0.6)], [w * 0.4, 0.2]), ICE_D, 0.7 * a)
    if ink_a > 0:
        sk.path(p, INK, ink_a, 0, 0.7)


def _snow_mound(sk, x, w, h, seed):
    p = smooth_path([(x - w, C + 1), (x - w * 0.6, C + 1 - h * 0.8), (x - w * 0.1, C + 1 - h), (x + w * 0.5, C + 1 - h * 0.75),
                     (x + w, C + 1)], True, 0.4)
    sk.path(p, SNOW_SH)
    sk.path(smooth_path([(x - w * 0.9, C + 1), (x - w * 0.6, C + 1 - h * 0.8), (x - w * 0.1, C + 1 - h), (x + w * 0.3, C + 1 - h * 0.7),
                         (x - w * 0.1, C + 1 - h * 0.35)], True, 0.4), SNOW_LIT)
    sk.path(p, INK, 0.8, 0, 0.9)


def _frost_grass(sk, rng, x, n, hmax):
    for _ in range(n):
        xx = x + rng.normal(0, 5)
        h = rng.uniform(6, hmax)
        ln, wd = rng.uniform(-0.45, 0.45), rng.uniform(1.2, 2.2)
        r = rng.random()
        c = ST['grass_dark'] if r < 0.35 else (ST['grass_tip'] if r < 0.6 else (ST['grass_top'] if r < 0.85 else ST['grass_mid']))
        sk.path(blade(xx, C + 1, h, ln, wd), c, 0.95)
        if rng.random() < 0.35:
            sk.path(blade_tip(xx, C + 1, h, ln, wd, 0.3), (240, 248, 255), 0.8)      # kırağı ucu
        elif rng.random() < 0.3:
            sk.path(blade_tip(xx, C + 1, h, ln, wd, 0.25), INK, 0.6)


def _juniper(sk, rng, x, s):
    """Karlı ardıç çalısı: alçak, yayvan koyu iğne yaprak kümesi, üstünde kar yığını."""
    body = blob(x, C + 1 - s * 0.45, s, s * 0.5, int(rng.integers(1 << 20)), n=14, jitter=0.2, flat_bottom=True)
    sk.path(body, (80, 120, 130))
    sk.path(blob(x + s * 0.35, C + 1 - s * 0.3, s * 0.6, s * 0.32, int(rng.integers(1 << 20)), n=10, jitter=0.2), (52, 84, 100), 0.85)
    for _ in range(int(s * 3)):
        a = rng.uniform(math.pi * 0.95, 2.05 * math.pi)
        r = rng.uniform(0.3, 1.0)
        px, py = x + math.cos(a) * s * r, C + 1 - s * 0.45 + math.sin(a) * s * 0.5 * r
        c = (130, 172, 170) if (px - x) < 0 else (60, 96, 110)
        sk.path(ribbon([(px, py), (px + math.cos(a) * 3.5, py + math.sin(a) * 3.5 + 1)], [1.1, 0.3]), c, 0.9)
    sk.path(body, INK, 0.9, 0, 1.0)
    cap = smooth_path([(x - s * 0.8, C + 1 - s * 0.6), (x - s * 0.3, C + 1 - s * 0.98), (x + s * 0.4, C + 1 - s * 0.9),
                       (x + s * 0.7, C + 1 - s * 0.55), (x, C + 1 - s * 0.7)], True, 0.4)
    sk.path(cap, SNOW_SH)
    sk.path(smooth_path([(x - s * 0.8, C + 1 - s * 0.6), (x - s * 0.3, C + 1 - s * 0.98), (x + s * 0.1, C + 1 - s * 0.92), (x - s * 0.2, C + 1 - s * 0.75)], True, 0.4), SNOW_LIT)
    sk.path(cap, INK, 0.7, 0, 0.7)


def _snowdrop(sk, rng, x):
    """Kardelen: karı delip çıkan ince sap, sarkık ak çan çiçek, yeşil uç lekesi."""
    for k in range(int(rng.integers(2, 4))):
        xx = x + k * rng.uniform(4, 7)
        h = rng.uniform(12, 20)
        stem = bezier((xx, C + 1), (xx + 1, C + 1 - h), (xx + 4, C + 1 - h + 2), 8)
        sk.path(ribbon(stem, np.linspace(1.3, 0.8, 8)), (80, 120, 90))
        sk.path(leaf_shape(xx, C, 10, 2.4, -math.pi / 2 - 0.2), (70, 110, 84))
        fx, fy = stem[-1]
        bell = smooth_path([(fx - 2.6, fy + 1), (fx - 1.8, fy + 6), (fx, fy + 8), (fx + 1.8, fy + 6), (fx + 2.6, fy + 1), (fx, fy)], True, 0.4)
        sk.path(bell, (250, 252, 255))
        sk.c.drawCircle(fx, fy + 6.5, 0.9, sk.paint((100, 170, 110)))
        sk.path(bell, INK, 0.8, 0, 0.7)


def _mini_crystals(sk, rng, x, s):
    from kaf_ink import ice_crystal
    for k in range(int(rng.integers(3, 6))):
        ang = rng.uniform(-0.7, 0.7)
        h = s * rng.uniform(0.5, 1.0)
        ice_crystal(sk, x + rng.uniform(-s * 0.2, s * 0.2), C + 1, h, h * 0.26, ang, int(rng.integers(1 << 20)), ink_w=0.8)


def grass_tuft(seed, kind):
    rng = np.random.default_rng(seed)
    sk = Sk(C, C)
    if kind == 0:
        _frost_grass(sk, rng, C * 0.5, 22, 22)
        _snow_mound(sk, C * 0.5, 14, 5, seed)
    elif kind == 1:
        _snow_mound(sk, C * 0.45, 20, 9, seed)
        _frost_grass(sk, rng, C * 0.65, 8, 14)
    elif kind == 2:
        _mini_crystals(sk, rng, C * 0.5, 30)
        _snow_mound(sk, C * 0.5, 12, 4, seed)
    elif kind == 3:
        _juniper(sk, rng, C * 0.5, 17)
    elif kind == 4:
        _frost_grass(sk, rng, C * 0.35, 14, 30)
        _frost_grass(sk, rng, C * 0.7, 10, 18)
    elif kind == 5:
        r = Z.rock_small(seed + 3, 11, 7, base=(118, 126, 172), light=(-0.6, -0.8), cap=SNOW_LIT)
        out = sk.snap()
        h, w = r.shape[:2]
        x, y = ik.P(C * 0.5) - w // 2, ik.P(C) - h + ik.P(3)
        sub = out[y:y + h, x:x + w]
        hh, ww = sub.shape[:2]
        out[y:y + hh, x:x + ww] = r[:hh, :ww] + sub * (1 - r[:hh, :ww, 3:4])
        sk2 = Sk(C, C)
        _frost_grass(sk2, rng, C * 0.2, 6, 12)
        o2 = sk2.snap()
        return o2 + out * (1 - o2[..., 3:4])
    elif kind == 6:
        _snow_mound(sk, C * 0.5, 18, 5, seed)
        _snowdrop(sk, rng, C * 0.4)
    else:
        _frost_grass(sk, rng, C * 0.5, 30, 40)
    return sk.snap()


def ceiling_roots(seed):
    """Tavandan sarkan buz sarkıtları (uzun-kısa, mürekkep konturlu, içten parlayan)."""
    rng = np.random.default_rng(seed)
    sk = Sk(C, C)
    for _ in range(int(rng.integers(4, 9))):
        x = rng.uniform(4, C - 4)
        ln = rng.uniform(8, 44) if rng.random() < 0.7 else rng.uniform(4, 10)
        _icicle(sk, x, -1, ln, rng.uniform(1.8, 3.6))
    sk.path(ribbon([(0, 0.5), (C, 0.8)], [3, 3]), (210, 236, 250), 0.9)
    return sk.snap()


def platform_cell(kind, var, seed):
    """Karlı koyu tahta platform: üstte kar yastığı (ışık tarafı parlak), ön kirişin altından buz saçakları, uç dikmeleri
    donmuş halatla bağlı."""
    rng = np.random.default_rng(seed)
    sk = Sk(C, C)
    top, beam_y0, beam_y1 = 0.5, 6.0, 16.0
    if kind in (0, 2):
        px = 9 if kind == 0 else C - 9
        post = poly_path([(px - 5, beam_y0), (px + 5, beam_y0), (px + 5.5, C + 1), (px - 5.5, C + 1)])
        sk.path(post, WOOD_D)
        sk.path(poly_path([(px - 5, beam_y0), (px - 1.5, beam_y0), (px - 2, C + 1), (px - 5.5, C + 1)]), WOOD)
        sk.path(post, INK, 1.0, 0, 2.2)
        sk.path(ribbon([(px - 5, beam_y1 + 14), (px - 1, beam_y1 + 13), (px + 5, beam_y1 + 14)], [1.6, 2.2, 1.6]), SNOW_LIT, 0.8)
    x0 = 1.0 if kind == 0 else -2
    x1 = C - 1.0 if kind == 2 else C + 2
    beam = poly_path([(x0, beam_y0), (x1, beam_y0), (x1, beam_y1), (x0, beam_y1)])
    sk.path(beam, WOOD)
    sk.path(poly_path([(x0, beam_y1 - 4), (x1, beam_y1 - 4), (x1, beam_y1), (x0, beam_y1)]), WOOD_D)
    for k in range(4):
        xx = rng.uniform(2, C - 8)
        yy = rng.uniform(beam_y0 + 3, beam_y1 - 3)
        sk.path(ribbon([(xx, yy), (xx + 4, yy + 0.4), (xx + 9, yy - 0.3)], [0.3, 1.2, 0.3]), INK, 0.6)
    deck = poly_path([(x0, top + 3), (x1, top + 3), (x1, beam_y0), (x0, beam_y0)])
    sk.path(deck, WOOD_L)
    xx = 0.0 if kind != 0 else 2.0
    while xx < C:
        wpl = rng.uniform(7, 11)
        if xx + wpl > C and kind == 2:
            break
        sk.path(ribbon([(xx, top + 3), (xx + rng.uniform(-0.5, 0.5), beam_y0)], [1.3, 1.3]), INK, 0.8)
        xx += wpl
    sk.path(poly_path([(x0, top + 3), (x1, top + 3), (x1, beam_y1), (x0, beam_y1)], closed=True) if kind != 1 else
            poly_path([(x0, beam_y1), (x1, beam_y1)], closed=False), INK, 1.0, 0, 2.2)
    # kar yastığı (üstte; uçlarda yuvarlanır)
    xa = x0 + (2 if kind == 0 else 0)
    xb = x1 - (2 if kind == 2 else 0)
    n = 12
    xs = np.linspace(xa, xb, n)
    th = 3.6 + rng.uniform(-0.6, 0.6, n)
    if kind == 0:
        th *= np.clip((xs - xa) / 8, 0.3, 1)
    if kind == 2:
        th *= np.clip((xb - xs) / 8, 0.3, 1)
    upper = [(x_, top + 3.4 - t_) for x_, t_ in zip(xs, th)]
    lower = [(x_, top + 4.6 + rng.uniform(0, 1.2)) for x_ in xs[::-1]]
    cap = smooth_path(upper + lower, True, 0.35)
    sk.path(cap, SNOW_MID)
    sk.path(smooth_path(upper + [(q[0], q[1] + 1.6) for q in upper[::-1]], True, 0.35), SNOW_LIT)
    sk.path(smooth_path(upper, False, 0.35), INK, 0.9, 0, 1.2)
    # kirişin altından saçaklar
    for _ in range(int(rng.integers(2, 6))):
        xx = rng.uniform(3, C - 3)
        if kind in (0, 2) and abs(xx - (9 if kind == 0 else C - 9)) < 7:
            continue
        _icicle(sk, xx, beam_y1 - 0.5, rng.uniform(4, 14), rng.uniform(1.2, 2.2))
    if kind in (0, 2) or var == 1:
        px = 9 if kind == 0 else (C - 9 if kind == 2 else C / 2)
        for k in range(4):
            yy = beam_y0 + k * 3.0
            pts = [(px - 7, yy), (px, yy + 1.4), (px + 7, yy + 0.3)]
            sk.path(ribbon(pts, [1.4, 2.2, 1.4]), ROPE)
            sk.path(ribbon(pts, [1.4, 2.2, 1.4]), INK, 0.9, 0, 0.7)
        sk.path(ribbon([(px - 7, beam_y0 - 0.5), (px + 7, beam_y0)], [1.2, 1.2]), SNOW_LIT, 0.9)
    return sk.snap()


# ------------------------------------------------------------------ dünya uzayı dokular
def soil_texture(seed=600, S=1024):
    """Arduvaz kaya: eğik tabakalı mavi-mor taş, buz damarları (turkuaz, ince parlak), kırık yüzler ve mürekkep çatlaklar,
    gömülü buz kristalleri."""
    ys = (np.arange(ik.P(S), dtype=np.float32)[:, None] + 0.5) / ik.K
    xs = (np.arange(ik.P(S), dtype=np.float32)[None, :] + 0.5) / ik.K
    warp = noise(S, S, 50, seed, sx=120, sy=40) * 30
    yy = ys + warp + xs * 0.0
    bands = np.sin(yy / S * 2 * math.pi * 8) * 0.5 + np.sin(yy / S * 2 * math.pi * 19 + 1.3) * 0.3
    nz = fbm(S, S, [60, 20, 6], seed + 1)
    t = np.clip(0.5 + 0.35 * bands + 0.3 * nz, 0, 1)
    A, B, Cc = (62, 64, 100), (84, 88, 128), (40, 40, 70)
    rgb = mix(c01(Cc), c01(A), smoothstep(0.1, 0.55, t)[..., None])
    rgb = mix(rgb, c01(B), smoothstep(0.6, 0.95, t)[..., None])
    # kırık yüzler (Voronoi, iri)
    from scipy import ndimage
    k0 = ik.K
    ik.K = 0.5
    edge, cid = Z.crack_net(S, seed + 4, n=150)
    ik.K = k0
    zf = ik.P(S) // HD / edge.shape[0]
    edge = ndimage.zoom(edge, zf, order=1)
    cid = ndimage.zoom(cid, zf, order=0)
    if HD > 1:   # HD paketi: aynı çatlak ağı temel boyutta büyütülür, sonra HD'ye doğrusal örneklenir
        edge = ik.hd_lin(ik.hd_lin(edge, 0), 1)
        cid = np.repeat(np.repeat(cid, HD, 0), HD, 1)
    tone = np.random.default_rng(seed + 9).uniform(0.86, 1.16, 80)[cid % 80]
    rgb = rgb * tone[..., None]
    crack = np.clip((1.2 - edge) * ik.K * 0.5 + 0.5, 0, 1)
    lip = np.clip(1 - np.abs(edge - 2.6) / 1.4, 0, 1)
    rgb = mix(rgb, c01((130, 140, 190)), (lip * 0.3)[..., None])
    rgb = mix(rgb, c01((14, 14, 30)), (crack * 0.8)[..., None])
    # buz damarları: ince, dalgalı, parlak turkuaz
    vn = noise(S, S, 0, seed + 12, sx=26, sy=14) + 0.35 * noise(S, S, 0, seed + 14, sx=6, sy=6)
    vein = np.clip(1 - np.abs(vn) / 0.03, 0, 1) * smoothstep(0.15, 0.5, noise(S, S, 0, seed + 13, sx=90, sy=90))
    rgb = mix(rgb, c01((140, 220, 245)), (vein * 0.32)[..., None])
    br = noise(S, S, 0, seed + 3, sx=24, sy=2.2)
    rgb *= (1 + 0.05 * br[..., None])

    def draw(sk, S_, rng, put):
        for _ in range(26):
            x, y = rng.uniform(0, S_), rng.uniform(0, S_)
            s = rng.uniform(8, 18)
            sd = int(rng.integers(1 << 20))

            def cr(X, Y, s=s, sd=sd):
                r2 = np.random.default_rng(sd)
                for k in range(int(r2.integers(2, 5))):
                    a = r2.uniform(-0.7, 0.7) - math.pi / 2
                    h = s * r2.uniform(0.5, 1.0)
                    w = h * 0.3
                    tip = (X + math.cos(a) * h, Y + math.sin(a) * h)
                    nx_, ny_ = -math.sin(a) * w / 2, math.cos(a) * w / 2
                    p = poly_path([(X - nx_, Y - ny_), (X + nx_, Y + ny_), (tip[0] + nx_ * 0.6 - math.cos(a) * w * 0.3, tip[1] + ny_ * 0.6 - math.sin(a) * w * 0.3), tip,
                                   (tip[0] - nx_ * 0.6 - math.cos(a) * w * 0.3, tip[1] - ny_ * 0.6 - math.sin(a) * w * 0.3)])
                    sk.path(p, (120, 200, 230), 0.8)
                    sk.path(ribbon([(X - nx_ * 0.4, Y - ny_ * 0.4), (tip[0] - nx_ * 0.2, tip[1] - ny_ * 0.2)], [w * 0.25, 0.2]), (230, 250, 255), 0.7)
                    sk.path(p, INK, 0.8, 0, 1.0)
            put(cr, x, y)
        for _ in range(60):
            x, y = rng.uniform(0, S_), rng.uniform(0, S_)
            rx = rng.uniform(3, 10)
            ry = rx * rng.uniform(0.5, 0.8)
            cc = np.array([110, 116, 160]) * rng.uniform(0.8, 1.15)
            sd = int(rng.integers(1 << 20))

            def peb(X, Y, rx=rx, ry=ry, cc=cc, sd=sd):
                q = blob(X, Y, rx, ry, sd, n=8, jitter=0.2)
                sk.path(q, tuple(cc))
                sk.path(blob(X - rx * 0.15, Y - ry * 0.3, rx * 0.6, ry * 0.45, 7, n=8, jitter=0.1), tuple(np.minimum(cc * 1.3, 255)), 0.8)
                sk.path(q, INK, 0.9, 0, 1.3)
            put(peb, x, y)

    return Z.tile_texture(S, seed + 11, draw, rgb)


def meadow_texture(seed=650, S=512):
    """Kar örtüsü (zeminin üst 2-3 karosu): yumuşak yığıntılar, rüzgâr oyuğu çizgileri (sastrugi), mavi gölgeli
    çukurlar, ışıltılar, yer yer karı delen kuru ot."""
    nz = fbm(S, S, [50, 16, 5], seed + 1)
    rip = noise(S, S, 0, seed + 2, sx=40, sy=3)
    ys = (np.arange(ik.P(S), dtype=np.float32)[:, None] + 0.5) / ik.K
    warp = noise(S, S, 0, seed + 3, sx=120, sy=30) * 14
    lay = np.sin((ys + warp) / S * 2 * math.pi * 9) * 0.5 + 0.5          # rüzgârla sıkışmış kar katmanları
    t = np.clip(0.35 + 0.35 * nz + 0.25 * rip + 0.2 * (lay - 0.5), 0, 1)
    base = mix(c01((96, 108, 170)), c01((166, 182, 228)), smoothstep(0.1, 0.65, t)[..., None])
    base = mix(base, c01((214, 224, 248)), smoothstep(0.7, 0.95, t)[..., None])
    edge = np.clip(1 - np.abs(lay - 0.92) / 0.05, 0, 1)
    base = mix(base, c01((70, 80, 140)), (edge * 0.35)[..., None])

    def draw(sk, S_, rng, put):
        for _ in range(140):
            x, y = rng.uniform(0, S_), rng.uniform(0, S_)
            ln = rng.uniform(20, 70)
            dy_ = rng.uniform(-3, 3)

            def sas(X, Y, ln=ln, dy_=dy_):
                q = [(X, Y), (X + ln * 0.5, Y + dy_), (X + ln, Y + dy_ * 0.3)]
                sk.path(ribbon(q, [0.3, 1.6, 0.3]), (120, 136, 196), 0.55)
                sk.path(ribbon([(p[0], p[1] - 1.4) for p in q], [0.3, 1.0, 0.3]), (255, 255, 255), 0.6)
            put(sas, x, y)
        for _ in range(500):
            x, y = rng.uniform(0, S_), rng.uniform(0, S_)
            r = rng.uniform(0.4, 1.1)
            a = rng.uniform(0.4, 1.0)
            put(lambda X, Y, r=r, a=a: sk.c.drawCircle(X, Y, r, sk.paint((255, 255, 255), a)), x, y, 4)
        for _ in range(120):
            x, y = rng.uniform(0, S_), rng.uniform(0, S_)
            h = rng.uniform(5, 14)
            ln = rng.uniform(-0.4, 0.4)
            c = (110, 104, 110) if rng.random() < 0.5 else (160, 150, 130)
            put(lambda X, Y, h=h, ln=ln, c=c: sk.path(blade(X, Y, h, ln, 1.3), c, 0.85), x, y)

    return Z.tile_texture(S, seed, draw, base)


# ------------------------------------------------------------------ ön plan
FG_COL = (14, 16, 36)
FG_SNOW = (150, 162, 214)
FG_SNOW_SH = (64, 72, 124)


def fg_grass_strip(seed=700, W=3840, Hs=260):
    """Ekranın alt kenarı: karla örtülü koyu çalı ve kırağılı kuru ot siluetleri (aktörlerin önünde)."""
    rng = np.random.default_rng(seed)
    pad = 160
    sk = Sk(W + 2 * pad, Hs)
    base = Hs - 40
    pts = [(x, base + 18 + 16 * math.sin(x / 180.0 + 1) + rng.uniform(-5, 5)) for x in np.linspace(0, W + 2 * pad, 90)]
    pts += [(W + 2 * pad, Hs + 4), (0, Hs + 4)]
    sk.path(smooth_path(pts, True, 0.3), FG_COL)
    # karlı çalı tümsekleri
    for _ in range(28):
        x = rng.uniform(0, W) + pad
        s = rng.uniform(40, 110)
        y = base + rng.uniform(16, 34)
        body = blob(x, y - s * 0.3, s, s * 0.55, int(rng.integers(1 << 20)), n=16, jitter=0.25)
        sk.path(body, FG_COL)
        for _k in range(int(s * 0.5)):
            a = rng.uniform(math.pi * 1.05, math.pi * 1.95)
            px, py = x + math.cos(a) * s * rng.uniform(0.8, 1.05), y - s * 0.3 + math.sin(a) * s * 0.55 * rng.uniform(0.8, 1.05)
            sk.path(ribbon([(px, py), (px + math.cos(a) * 9, py + math.sin(a) * 9)], [2.4, 0.4]), FG_COL)
        cap = smooth_path([(x - s * 0.85, y - s * 0.45), (x - s * 0.4, y - s * 0.8), (x + s * 0.3, y - s * 0.78),
                           (x + s * 0.8, y - s * 0.45), (x + s * 0.2, y - s * 0.6), (x - s * 0.4, y - s * 0.55)], True, 0.4)
        sk.path(cap, FG_SNOW_SH)
        sk.path(smooth_path([(x - s * 0.85, y - s * 0.45), (x - s * 0.4, y - s * 0.8), (x, y - s * 0.79), (x - s * 0.3, y - s * 0.62)], True, 0.4), FG_SNOW, 0.85)
    for _ in range(int(W * 0.45)):
        x = rng.uniform(0, W) + pad
        h = rng.uniform(20, 110) * (0.6 + 0.4 * rng.random())
        by, ln, wd = base + rng.uniform(12, 46), rng.uniform(-0.5, 0.5), rng.uniform(2.6, 5.0)
        sk.path(blade(x, by, h, ln, wd, curl=0.4), FG_COL)
        if rng.random() < 0.25:
            sk.path(blade_tip(x, by, h, ln, wd, 0.25), FG_SNOW_SH, 0.8)
    arr = sk.snap()
    from ink_biyom import fold
    L = Layer(W, Hs)
    L.a = fold(arr, ik.P(pad), ik.P(W))
    return L


def fg_top_strip(seed=720, W=3840, Hs=300):
    """Üst kenardan sarkan karla yüklü ladin dalları ve buz saçakları (köşeleri çerçeveler)."""
    rng = np.random.default_rng(seed)
    pad = 300
    sk = Sk(W + 2 * pad, Hs)
    for cx in (220, 1240, 2380, 3260):
        x0 = cx + rng.uniform(-80, 80) + pad
        main = bezier((x0 - 260, -10), (x0, 40 + rng.uniform(0, 30)), (x0 + 240, 60 + rng.uniform(0, 50)), 20)
        sk.path(ribbon(main, np.linspace(16, 4, 20)), FG_COL)
        for j in range(1, 19):
            q = main[j]
            for sgn in (-1, 1):
                ln = rng.uniform(26, 60) * (1 - j / 26)
                a = math.pi / 2 + sgn * rng.uniform(0.3, 0.9) - 0.25
                tip = (q[0] + math.cos(a) * ln, q[1] + math.sin(a) * ln)
                twig = bezier(q, ((q[0] + tip[0]) / 2, (q[1] + tip[1]) / 2 - 4), tip, 8)
                sk.path(ribbon(twig, np.linspace(5, 0.8, 8)), FG_COL)
                for k in range(2, 8):
                    p = twig[k]
                    for s2 in (-1, 1):
                        sk.path(ribbon([p, (p[0] + s2 * 4, p[1] + 6)], [1.6, 0.3]), FG_COL)
        # kar yükü (dalın üstünde)
        up = [(p[0], p[1] - rng.uniform(5, 11)) for p in main[2:18]]
        lo = [(p[0], p[1] + 2) for p in main[2:18]][::-1]
        sk.path(smooth_path(up + lo, True, 0.4), FG_SNOW_SH)
        sk.path(smooth_path(up + [(q[0], q[1] + 3) for q in up[::-1]], True, 0.4), FG_SNOW, 0.9)
        for _ in range(8):
            p = main[int(rng.integers(3, 18))]
            ln = rng.uniform(10, 34)
            sk.path(poly_path([(p[0] - 3, p[1] + 4), (p[0] + 3, p[1] + 4), (p[0], p[1] + 4 + ln)]), (120, 150, 200), 0.85)
    arr = sk.snap()
    from ink_biyom import fold
    L = Layer(W, Hs)
    L.a = fold(arr, ik.P(pad), ik.P(W))
    return L


def flake_particle():
    """İri, yumuşak kar tanesi (ekranda süzülen yakın kar)."""
    sk = Sk(24, 24)
    sk.c.drawCircle(12, 12, 7, sk.paint((255, 255, 255), 0.55, 3.0))
    sk.c.drawCircle(12, 12, 4, sk.paint((255, 255, 255), 1.0, 1.0))
    return sk.snap()
