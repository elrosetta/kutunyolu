"""Tamu (Erlik'in Ülkesi) v2 "mürekkep" oyun alanı: karo atlası (bazalt + kül örtüsü + yan yüzde ışıyan lav
çatlağı), dünya uzayı sütunlu bazalt dokusu (altıgen eklemler, bazı eklemlerde lav damarı -> _soil_e), kül dokusu
(üst 2-3 karo), ön plan şeritleri (bazalt sivrileri, kemikler / sarkan zincirler, is) ve kül parçacığı.
Yerleşim ve ölçü Ötüken ile aynı (inkkit_zemin)."""
import math

import numpy as np
from scipy import ndimage

import inkkit_ortam as ik
from inkkit_ortam import (INK, Layer, Sk, blade, blob, c01, fbm, leaf_shape, mix, noise, poly_path, premul, ribbon,
                          smooth_path, smoothstep, bezier)
import inkkit_yeralti as Y
import inkkit_zemin as Z
from inkkit_zemin import C

ASH_TOP = (138, 124, 118)
ASH_MID = (92, 78, 78)
ASH_DARK = (44, 32, 36)
BAS_A = (40, 32, 38)
BAS_B = (58, 46, 52)
BAS_C = (26, 20, 26)
BAS_L = (120, 80, 72)
RIM = (255, 124, 56)
EMBER = (255, 150, 60)
LAVA = (255, 120, 36)
LAVA_HI = (255, 222, 150)
IRON = (62, 54, 58)
IRON_HI = (170, 116, 92)
BONE = (196, 178, 152)
BONE_SH = (110, 80, 70)
MEADOW_DEPTH = 0.45


def _crack(sk, se, pts, w0, glow_a=0.6):
    ws = np.linspace(w0, 0.4, len(pts))
    sk.path(ribbon(pts, ws * 2.0), INK, 0.95)
    sk.path(ribbon(pts, ws * 0.9), LAVA, 1.0)
    sk.path(ribbon(pts, ws * 0.35), LAVA_HI, 1.0)
    se.path(ribbon(pts, ws * 4), LAVA, glow_a * 0.35, 2.5)
    se.path(ribbon(pts, ws * 1.0), LAVA_HI, glow_a)


class TamuSpec(Z.Spec):
    rim = RIM
    rim_a = 0.42
    ceil_dark = (18, 6, 8)
    ink_w = 3.2
    edge_amp = (1.4, 3.0, 3.5)

    def top_band(self, art, emit, cov, top_d, m, rng, seed):
        K = ik.K
        CP = ik.P(C)
        band_d = 9 + 4 * noise(C, 1, 2, seed + 2, wrap=False)[0][None, :] + rng.uniform(-1.5, 1.5)
        g_t = np.clip(top_d / band_d, 0, 1.4)
        gcol = mix(c01(ASH_TOP), c01(ASH_MID), smoothstep(0.0, 0.6, g_t)[..., None])
        gcol = mix(gcol, c01(ASH_DARK), smoothstep(0.55, 1.05, g_t)[..., None])
        gmask = (1 - smoothstep(0.85, 1.15, g_t)) * cov
        lay = Layer(C, C)
        lay.fill_mask(gmask, gcol)
        sk = Sk(C, C)
        se = Sk(C, C)
        # kül kabuğu: yassı açık lekeler ve kara cüruf taneleri
        for _ in range(int(60 * (1 if (m & 10) == 0 else 0.75))):
            x = rng.uniform(-2, C + 2)
            if (m & 8) and x < 5:
                continue
            if (m & 2) and x > C - 5:
                continue
            y = rng.uniform(-0.5, 9)
            r = rng.uniform(0.8, 2.6)
            if rng.random() < 0.3:
                sk.c.drawCircle(x, y + 1, r * 0.6, sk.paint((20, 14, 16), 0.9))
            else:
                c = mix(c01((170, 156, 148)), c01(ASH_MID), np.clip(y / 9, 0, 1)) * rng.uniform(0.85, 1.1)
                sk.c.drawOval(Y.skia_rect(x - r * 1.4, y - r * 0.5, x + r * 1.4, y + r * 0.5), sk.paint(tuple(np.clip(c, 0, 1) * 255), 0.9))
        # kömürleşmiş kısa ot sapları
        for _ in range(int(rng.integers(0, 5))):
            x = rng.uniform(4, C - 4)
            sk.path(blade(x, 2, rng.uniform(3, 7), rng.uniform(-0.5, 0.5), 1.0), (24, 16, 18), 0.95)
        bl = sk.snap()
        bl *= np.maximum(gmask, (top_d > -2).astype(np.float32) * (top_d < 3) * 0.9)[..., None] ** 0.5
        lay.a = bl + lay.a * (1 - bl[..., 3:4])
        tip = (1 - smoothstep(0.3, 2.0, top_d)) * cov
        lay.fill_mask(tip * 0.35, c01((220, 170, 140)))
        art.a = lay.a + art.a * (1 - lay.a[..., 3:4])
        # kor tanecikleri
        for _ in range(int(rng.integers(0, 4))):
            x, y = rng.uniform(4, C - 4), rng.uniform(1, 7)
            se.c.drawCircle(x, y, 1.8, se.paint(EMBER, 0.3, 1.2))
            se.c.drawCircle(x, y, 0.7, se.paint(LAVA_HI, 1.0))
        e = se.snap()
        emit.a = e + emit.a * (1 - e[..., 3:4])

    def embed(self, art, emit, cov, m, var, rng, seed):
        if var == 1 and (m & (2 | 8)) and not (m & 4):
            sk = Sk(C, C)
            se = Sk(C, C)
            right = bool(m & 2)
            x0 = C - 1 if right else 1
            y = rng.uniform(16, 36)
            pts = [(x0, y)]
            for k in range(int(rng.integers(3, 6))):
                pts.append((pts[-1][0] + (-1 if right else 1) * rng.uniform(4, 9), pts[-1][1] + rng.uniform(-5, 5)))
            _crack(sk, se, pts, rng.uniform(2.0, 3.2))
            a = sk.snap() * cov[..., None]
            art.a = a + art.a * (1 - a[..., 3:4])
            e = se.snap() * cov[..., None]
            emit.a = e + emit.a * (1 - e[..., 3:4])
        elif var == 2 and (m & 1) and not (m & 4) and rng.random() < 0.6:
            sk = Sk(C, C)
            se = Sk(C, C)
            x = rng.uniform(10, C - 10)
            pts = [(x, rng.uniform(10, 14))]
            for k in range(3):
                pts.append((pts[-1][0] + rng.uniform(-6, 6), pts[-1][1] + rng.uniform(4, 9)))
            _crack(sk, se, pts, 1.8, 0.5)
            a = sk.snap() * cov[..., None]
            art.a = a + art.a * (1 - a[..., 3:4])
            e = se.snap() * cov[..., None]
            emit.a = e + emit.a * (1 - e[..., 3:4])

    # ------------------------------------------------------------ örtü öbekleri
    def tuft(self, k, seed):
        rng = np.random.default_rng(seed)
        sk = Sk(C, C)
        se = Sk(C, C)
        base = C + 1
        kind = k % 8

        def ash_mound(cx, w, h):
            p = smooth_path([(cx - w, base), (cx - w * 0.5, base - h * 0.8), (cx, base - h), (cx + w * 0.6, base - h * 0.7), (cx + w, base)], True, 0.4)
            sk.path(p, ASH_MID)
            sk.path(smooth_path([(cx - w * 0.6, base - h * 0.6), (cx, base - h), (cx + w * 0.5, base - h * 0.7), (cx, base - h * 0.55)], True, 0.4), ASH_TOP, 0.9)
            sk.path(p, INK, 0.8, 0, 1.0)

        def stubs(n, hmax):
            for _ in range(n):
                x = rng.uniform(4, C - 4)
                h = rng.uniform(4, hmax)
                pts = [(x, base), (x + rng.uniform(-2, 2), base - h * 0.6), (x + rng.uniform(-4, 4), base - h)]
                sk.path(ribbon(pts, [2.2, 1.4, 0.4]), (22, 14, 16))
                if rng.random() < 0.4:
                    sk.c.drawCircle(pts[-1][0], pts[-1][1], 1.0, sk.paint(EMBER))
                    se.c.drawCircle(pts[-1][0], pts[-1][1], 2.2, se.paint(EMBER, 0.6, 1.2))

        def coals(cx, n):
            for _ in range(n):
                x = cx + rng.normal(0, 6)
                y = base - rng.uniform(1, 6)
                r = rng.uniform(2, 4.5)
                p = blob(x, y, r * 1.2, r, int(x * 10), 8, 0.2)
                sk.path(p, (30, 18, 18))
                sk.path(p, INK, 1.0, 0, 0.9)
                q = [(x - r * 0.6, y + rng.uniform(-1, 1)), (x, y + rng.uniform(-1.5, 1.5)), (x + r * 0.7, y + rng.uniform(-1, 1))]
                sk.path(ribbon(q, [0.4, 1.2, 0.4]), LAVA, 1.0)
                se.path(ribbon(q, [1.5, 3.0, 1.5]), LAVA, 0.5, 1.5)
                se.path(ribbon(q, [0.4, 1.0, 0.4]), LAVA_HI, 1.0)

        if kind == 0:
            ash_mound(24, 18, 6)
            stubs(7, 14)
        elif kind == 1:
            ash_mound(22, 14, 4)
            coals(24, 5)
        elif kind == 2:
            # kemikler + küçük kafatası
            for _ in range(3):
                x = rng.uniform(8, C - 8)
                a = rng.uniform(-0.5, 0.5)
                l = rng.uniform(10, 16)
                p0 = (x - math.cos(a) * l / 2, base - 2 - math.sin(a) * l / 2)
                p1 = (x + math.cos(a) * l / 2, base - 2 + math.sin(a) * l / 2)
                sk.path(ribbon([p0, p1], [2.6, 2.6]), BONE)
                for q in (p0, p1):
                    sk.c.drawCircle(q[0], q[1], 2.0, sk.paint(BONE))
                sk.path(ribbon([p0, p1], [2.6, 2.6]), INK, 0.9, 0, 0.8)
            hx, hy = rng.uniform(16, 32), base - 6
            skull = smooth_path([(hx - 6, hy + 5), (hx - 7, hy - 2), (hx - 3, hy - 7), (hx + 4, hy - 7), (hx + 8, hy - 1), (hx + 7, hy + 5)], True, 0.4)
            sk.path(skull, BONE)
            sk.path(smooth_path([(hx + 1, hy - 7), (hx + 8, hy - 1), (hx + 7, hy + 5), (hx + 2, hy + 5)], True, 0.4), BONE_SH, 0.5)
            sk.path(skull, INK, 1.0, 0, 1.0)
            for sx in (-2.5, 2.5):
                sk.c.drawCircle(hx + sx, hy - 1, 1.5, sk.paint((14, 6, 8)))
            se.c.drawCircle(hx - 2.5, hy - 1, 1.2, se.paint(EMBER, 0.8, 0.8))
            se.c.drawCircle(hx + 2.5, hy - 1, 1.2, se.paint(EMBER, 0.8, 0.8))
        elif kind == 3:
            # paslı demir kazıklar
            for _ in range(int(rng.integers(2, 4))):
                x = rng.uniform(8, C - 8)
                h = rng.uniform(16, 30)
                lean = rng.uniform(-0.15, 0.15)
                p = poly_path([(x - 2, base), (x + 2, base), (x + lean * h + 0.4, base - h), (x + lean * h - 0.4, base - h)])
                sk.path(p, IRON)
                sk.path(ribbon([(x - 1, base), (x + lean * h - 0.2, base - h)], [1.0, 0.3]), IRON_HI, 0.6)
                sk.path(p, INK, 1.0, 0, 0.9)
            ash_mound(24, 16, 3)
        elif kind == 4:
            # bazalt kıymıkları
            for _ in range(int(rng.integers(2, 4))):
                x = rng.uniform(10, C - 10)
                h = rng.uniform(8, 18)
                w = rng.uniform(5, 9)
                sl = rng.uniform(-3, 3)
                p = poly_path([(x - w / 2, base), (x - w / 2, base - h + sl), (x + w / 2, base - h - sl), (x + w / 2, base)])
                sk.path(p, BAS_B)
                sk.path(poly_path([(x - w / 2, base), (x - w / 2, base - h + sl), (x - w * 0.1, base - h), (x - w * 0.1, base)]), BAS_L, 0.6)
                sk.path(p, INK, 1.0, 0, 1.0)
        elif kind == 5:
            # çatlaktan yükselen alev dilleri
            coals(24, 2)
            for j in range(3):
                x = 16 + j * 8 + rng.uniform(-2, 2)
                h = rng.uniform(8, 16)
                fl = smooth_path([(x - 3, base - 2), (x - 2, base - h * 0.5), (x + rng.uniform(-1, 1), base - h), (x + 2, base - h * 0.5), (x + 3, base - 2)], True, 0.4)
                se.path(fl, LAVA, 0.9, 1.0)
                se.path(smooth_path([(x - 1.4, base - 2), (x, base - h * 0.6), (x + 1.4, base - 2)], True, 0.4), LAVA_HI, 1.0)
        elif kind == 6:
            # kömürleşmiş çalı
            x0 = rng.uniform(16, C - 16)
            for _ in range(6):
                a = rng.uniform(-1.2, 1.2) - math.pi / 2
                ln = rng.uniform(10, 22)
                pts = bezier((x0, base), (x0 + math.cos(a) * ln * 0.5, base + math.sin(a) * ln * 0.6),
                             (x0 + math.cos(a) * ln, base + math.sin(a) * ln), 8)
                sk.path(ribbon(pts, np.linspace(1.8, 0.4, 8)), (20, 12, 14))
                if rng.random() < 0.4:
                    se.c.drawCircle(pts[-1][0], pts[-1][1], 1.3, se.paint(EMBER, 0.9, 0.6))
            ash_mound(x0, 10, 3)
        else:
            ash_mound(22, 20, 5)
            Y.chain(sk, (6, base - 3), (C - 8, base - 2), -2, link=6, col=IRON, hi=IRON_HI, thick=1.6)
        return sk.snap(), se.snap()

    def ceiling(self, i, seed):
        rng = np.random.default_rng(seed)
        sk = Sk(C, C)
        se = Sk(C, C)
        if i == 0:
            for _ in range(int(rng.integers(2, 4))):
                x = rng.uniform(6, C - 6)
                ln = rng.uniform(10, 30)
                w = rng.uniform(4, 8)
                p = poly_path([(x - w / 2, -1), (x - w * 0.15, ln * 0.7), (x, ln), (x + w * 0.2, ln * 0.6), (x + w / 2, -1)])
                sk.path(p, BAS_B)
                sk.path(p, INK, 1.0, 0, 1.0)
                if rng.random() < 0.6:
                    sk.c.drawCircle(x, ln + 3, 1.4, sk.paint(LAVA))
                    se.c.drawCircle(x, ln + 3, 2.6, se.paint(LAVA, 0.6, 1.4))
                    se.c.drawCircle(x, ln + 3, 1.0, se.paint(LAVA_HI, 1.0))
        elif i == 1:
            for _ in range(2):
                x = rng.uniform(8, C - 8)
                ln = rng.uniform(16, 40)
                Y.chain(sk, (x, -2), (x + 0.3, ln), 0, link=6, col=IRON, hi=IRON_HI, thick=1.6)
                hk = bezier((x, ln + 2), (x + 6, ln + 10), (x - 1, ln + 13), 8)
                sk.path(ribbon(hk, np.linspace(2.2, 0.8, 8)), IRON)
                sk.path(ribbon(hk, np.linspace(2.2, 0.8, 8)), INK, 1.0, 0, 0.6)
        else:
            for _ in range(int(rng.integers(4, 8))):
                x = rng.uniform(3, C - 3)
                ln = rng.uniform(6, 24)
                pts = [(x + math.sin(k * 1.3 + x) * 1.5 * k / 4, -1 + ln * k / 4) for k in range(5)]
                sk.path(ribbon(pts, np.linspace(2.4, 0.4, 5)), (24, 14, 16))
                if rng.random() < 0.35:
                    se.c.drawCircle(pts[-1][0], pts[-1][1], 1.2, se.paint(EMBER, 0.9, 0.6))
        return sk.snap(), se.snap()

    # ------------------------------------------------------------ platform: demir kuşaklı bazalt levha
    def platform(self, kind, var, seed):
        rng = np.random.default_rng(seed)
        sk = Sk(C, C)
        se = Sk(C, C)
        top, beam_y0, beam_y1 = 0.5, 5.0, 16.0
        if kind in (0, 2):
            px = 9 if kind == 0 else C - 9
            post = poly_path([(px - 6, beam_y0), (px + 6, beam_y0), (px + 5.5, C + 1), (px - 5.5, C + 1)])
            sk.path(post, BAS_A)
            sk.path(poly_path([(px - 6, beam_y0), (px - 2.5, beam_y0), (px - 2.5, C + 1), (px - 5.5, C + 1)]), BAS_L, 0.45)
            sk.path(poly_path([(px + 2.5, beam_y0), (px + 6, beam_y0), (px + 5.5, C + 1), (px + 2.5, C + 1)]), (16, 10, 14), 0.7)
            for yy in (28, 40):
                sk.path(ribbon([(px - 5.5, yy), (px + 5.5, yy + 1)], [1.2, 1.2]), INK, 0.8)
            band = poly_path([(px - 7, 22), (px + 7, 22), (px + 7, 26), (px - 7, 26)])
            sk.path(band, IRON)
            sk.path(band, INK, 1.0, 0, 0.8)
            sk.path(post, INK, 1.0, 0, 2.0)
        x0 = 1.0 if kind == 0 else -2
        x1 = C - 1.0 if kind == 2 else C + 2
        beam = poly_path([(x0, beam_y0), (x1, beam_y0), (x1, beam_y1), (x0, beam_y1)])
        sk.path(beam, BAS_B)
        sk.path(poly_path([(x0, beam_y1 - 4), (x1, beam_y1 - 4), (x1, beam_y1), (x0, beam_y1)]), (150, 64, 40), 0.5)  # alttan lav ışığı
        # demir kuşaklar ve perçinler
        xx = rng.uniform(6, 14)
        while xx < C - 4:
            b = poly_path([(xx - 2.5, beam_y0 - 0.5), (xx + 2.5, beam_y0 - 0.5), (xx + 2.5, beam_y1 + 0.5), (xx - 2.5, beam_y1 + 0.5)])
            sk.path(b, IRON)
            sk.path(ribbon([(xx - 1.5, beam_y0), (xx - 1.5, beam_y1)], [0.8, 0.8]), IRON_HI, 0.6)
            sk.path(b, INK, 1.0, 0, 0.8)
            for yy in (beam_y0 + 2.5, beam_y1 - 2.5):
                sk.c.drawCircle(xx, yy, 0.9, sk.paint(IRON_HI))
            xx += rng.uniform(18, 26)
        if kind == 1 and var == 1:
            cx = C / 2
            sk_p = smooth_path([(cx - 5, beam_y1 - 1), (cx - 6, beam_y0 + 3), (cx, beam_y0 + 1), (cx + 6, beam_y0 + 3), (cx + 5, beam_y1 - 1)], True, 0.4)
            sk.path(sk_p, BONE)
            sk.path(sk_p, INK, 1.0, 0, 0.9)
            for sx in (-2.2, 2.2):
                sk.c.drawCircle(cx + sx, beam_y0 + 6, 1.4, sk.paint((14, 6, 8)))
                se.c.drawCircle(cx + sx, beam_y0 + 6, 2.2, se.paint(EMBER, 0.9, 1.0))
            for s_ in (-1, 1):
                horn = bezier((cx + s_ * 5, beam_y0 + 3), (cx + s_ * 12, beam_y0 + 2), (cx + s_ * 11, beam_y0 - 4), 8)
                sk.path(ribbon(horn, np.linspace(2.4, 0.5, 8)), BONE)
                sk.path(ribbon(horn, np.linspace(2.4, 0.5, 8)), INK, 0.9, 0, 0.6)
        deck = poly_path([(x0, top), (x1, top), (x1, beam_y0), (x0, beam_y0)])
        sk.path(deck, (80, 66, 68))
        for _ in range(int(rng.integers(6, 12))):
            x = rng.uniform(x0 + 2, x1 - 2)
            r = rng.uniform(1.2, 3)
            sk.c.drawOval(Y.skia_rect(x - r * 1.4, top - 0.4, x + r * 1.4, top + 1.6), sk.paint(ASH_TOP, 0.9))
        sk.path(poly_path([(x0, top), (x1, top), (x1, beam_y1), (x0, beam_y1)], closed=True) if kind != 1 else
                poly_path([(x0, top), (x1, top)], closed=False), INK, 1.0, 0, 2.2)
        sk.path(poly_path([(x0, beam_y1), (x1, beam_y1)], closed=False), INK, 1.0, 0, 2.4)
        sk.path(poly_path([(x0, beam_y0), (x1, beam_y0)], closed=False), INK, 0.8, 0, 1.2)
        if kind != 1 or var == 0:
            # alt kenardan sızan kor
            for _ in range(int(rng.integers(1, 3))):
                x = rng.uniform(6, C - 6)
                se.c.drawCircle(x, beam_y1 + 1, 2.0, se.paint(EMBER, 0.6, 1.4))
        return sk.snap(), se.snap()


SPEC = TamuSpec()


def soil_texture(seed=620, S=1024):
    """Sütunlu bazalt: dikeyde uzamış altıgen (Voronoi) hücreler, her hücre kendi tonunda, ışığa bakan kenar açık;
    eklemlerde mürekkep, bazı eklemlerde ışıyan lav damarı; yatay kırıklar, kül tozu."""
    rng = np.random.default_rng(seed)
    P = ik.P(S)
    ys, xs = (np.mgrid[0:P, 0:P].astype(np.float32) + 0.5) / ik.K
    n = 150
    pts = np.stack([rng.uniform(0, S, n), rng.uniform(0, S, n)], 1)
    stretch = 0.42
    best = np.full((P, P), 1e9, np.float32)
    second = np.full((P, P), 1e9, np.float32)
    idx = np.zeros((P, P), np.int32)
    for dx in (-S, 0, S):
        for dy in (-S, 0, S):
            for i, (px, py) in enumerate(pts):
                d = np.hypot(xs - px - dx, (ys - py - dy) * stretch)
                m = d < best
                second = np.where(m, best, np.minimum(second, d))
                idx = np.where(m, i, idx)
                best = np.where(m, d, best)
    edge = second - best
    tone = rng.uniform(0.75, 1.2, n)[idx]
    rgb = c01(BAS_A)[None, None, :] * tone[..., None]
    # hücre içinde sol kenar açık (eğik yüz), sağ koyu: yönlü kaba gölge
    gx = ndimage.sobel(best, axis=1)
    rgb *= (1 + 0.18 * np.tanh(-gx * 0.6))[..., None]
    nz = fbm(S, S, [30, 8, 2], seed + 1)
    rgb *= (1 + 0.1 * nz[..., None])
    ink = np.clip(1 - edge / 2.2, 0, 1)
    rgb = mix(rgb, c01(INK)[None, None, :], (ink * 0.9)[..., None])
    hi = np.clip(1 - np.abs(edge - 3.0) / 1.2, 0, 1) * (gx < 0)
    rgb = mix(rgb, c01(BAS_L)[None, None, :], (hi * 0.35)[..., None])
    L = Layer(S, S)
    L.a = premul(rgb.astype(np.float32), np.ones((P, P), np.float32))
    # ışıyan eklemler: hücre çiftinin kimliğine göre seçilen eklemler + yumuşak gürültü
    sel = smoothstep(0.55, 0.8, noise(S, S, 0, seed + 5, sx=50, sy=90))
    lava = np.clip(1 - edge / 1.1, 0, 1) * sel
    lava = ndimage.gaussian_filter(lava, 0.6 * ik.K)
    E = Layer(S, S)
    erg = mix(c01(LAVA)[None, None, :], c01(LAVA_HI)[None, None, :], np.clip(lava * 1.5 - 0.5, 0, 1)[..., None])
    halo = ndimage.gaussian_filter(lava, 3 * ik.K) * 0.8
    ea = np.clip(lava + halo * 0.6, 0, 1)
    E.a = premul(erg.astype(np.float32), ea.astype(np.float32))
    # art üzerinde de lav rengi (ışıma katmanı kapalıyken bile okunsun)
    L.a[..., :3] = mix(L.a[..., :3], c01(LAVA)[None, None, :] * 0.8, (lava * 0.55)[..., None])
    sk = Sk(S, S)
    for _ in range(50):   # yatay kırıklar
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        ln = rng.uniform(10, 30)
        Z.tile_wrap_draw(sk, S, x, y, 40, lambda dx, dy, x=x, y=y, ln=ln: sk.path(
            ribbon([(x + dx, y + dy), (x + dx + ln * 0.5, y + dy + 1), (x + dx + ln, y + dy - 0.5)], [0.3, 1.4, 0.3]), INK, 0.6))
    dec = sk.snap()
    L.a = dec + L.a * (1 - dec[..., 3:4])
    return L, E


def top_texture(seed=670, S=512):
    """Üst 2-3 karo: kül tabakası (yumuşak tümsekli açık gri-kahve), kara cüruf taneleri, kömür parçaları, seyrek kor."""
    rng = np.random.default_rng(seed)
    nz = fbm(S, S, [40, 12, 4], seed + 1)
    base = mix(c01((36, 28, 32)), c01((74, 62, 62)), smoothstep(-0.5, 0.6, nz)[..., None])
    rip = noise(S, S, 0, seed + 3, sx=30, sy=3)
    base *= (1 + 0.08 * rip[..., None])
    L = Layer(S, S)
    L.a = premul(base.astype(np.float32), np.ones(base.shape[:2], np.float32))
    sk = Sk(S, S)
    for _ in range(1200):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        r = rng.uniform(1.0, 3.2)
        if rng.random() < 0.35:
            c, a = (22, 14, 16), 0.9
        else:
            c, a = tuple(np.array((124, 110, 104)) * rng.uniform(0.7, 1.05)), 0.45
        Z.tile_wrap_draw(sk, S, x, y, 8, lambda dx, dy, x=x, y=y, r=r, c=c, a=a: sk.c.drawOval(
            Y.skia_rect(x + dx - r * 1.3, y + dy - r * 0.6, x + dx + r * 1.3, y + dy + r * 0.6), sk.paint(c, a)))
    for _ in range(60):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        Z.tile_wrap_draw(sk, S, x, y, 4, lambda dx, dy, x=x, y=y: sk.c.drawCircle(x + dx, y + dy, 1.0, sk.paint((255, 150, 70), 0.85)))
    for _ in range(30):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        ln = rng.uniform(10, 30)
        Z.tile_wrap_draw(sk, S, x, y, 40, lambda dx, dy, x=x, y=y, ln=ln: sk.path(
            ribbon([(x + dx, y + dy), (x + dx + ln * 0.5, y + dy + rng.uniform(-2, 2)), (x + dx + ln, y + dy)], [0.3, 1.2, 0.3]), INK, 0.5))
    bl = sk.snap()
    L.a = bl + L.a * (1 - bl[..., 3:4])
    return L


FG_COL = (10, 4, 6)
FG_RIM = (170, 60, 30)


def fg_bottom_strip(seed=712, W=3840, Hs=260):
    rng = np.random.default_rng(seed)
    pad = 160
    sk = Sk(W + 2 * pad, Hs)
    base = Hs - 40
    pts = [(x, base + 20 + 14 * math.sin(x / 150.0 + 1) + 8 * math.sin(x / 41.0) + rng.uniform(-4, 4))
           for x in np.linspace(0, W + 2 * pad, 120)]
    sk.path(ribbon([(p[0], p[1] - 1.5) for p in pts], [3.0] * len(pts)), FG_RIM, 0.6)
    sk.path(smooth_path(pts + [(W + 2 * pad, Hs + 4), (0, Hs + 4)], True, 0.3), FG_COL)
    for _ in range(18):   # bazalt sivrileri (eğik kesik)
        x = rng.uniform(0, W) + pad
        h = rng.uniform(40, 160)
        w = rng.uniform(20, 46)
        sl = rng.uniform(-0.5, 0.5) * w
        p = poly_path([(x - w / 2, base + 30), (x - w / 2, base + 30 - h + sl), (x + w / 2, base + 30 - h - sl), (x + w / 2, base + 30)])
        sk.path(p, FG_RIM, 0.5, 0, 3.0)
        sk.path(p, FG_COL)
    for _ in range(12):   # kemik / boynuz siluetleri
        x = rng.uniform(0, W) + pad
        p0 = (x, base + 30)
        p2 = (x + rng.uniform(-60, 60), base + 30 - rng.uniform(60, 140))
        q = bezier(p0, ((p0[0] + p2[0]) / 2 + rng.uniform(-30, 30), (p0[1] + p2[1]) / 2), p2, 12)
        sk.path(ribbon(q, np.linspace(14, 2, 12)), FG_RIM, 0.45, 0, 2.5)
        sk.path(ribbon(q, np.linspace(14, 2, 12)), FG_COL)
    L = Layer(W, Hs)
    L.a = Y.wrap_core(sk.snap(), pad, W)
    return L


def fg_top_strip(seed=732, W=3840, Hs=320):
    rng = np.random.default_rng(seed)
    pad = 200
    sk = Sk(W + 2 * pad, Hs)
    pts = [(x, 8 + 8 * math.sin(x / 130.0) + rng.uniform(-3, 3)) for x in np.linspace(0, W + 2 * pad, 100)]
    sk.path(smooth_path([(0, -10)] + pts + [(W + 2 * pad, -10)], True, 0.3), FG_COL)
    for cx in rng.uniform(0, W, 16):
        x = cx + pad
        ln = rng.uniform(30, 120)
        w = rng.uniform(20, 50)
        p = poly_path([(x - w / 2, 0), (x - w * 0.2, ln * 0.7), (x, ln), (x + w * 0.25, ln * 0.6), (x + w / 2, 0)])
        sk.path(p, FG_RIM, 0.4, 0, 2.5)
        sk.path(p, FG_COL)
    for _ in range(14):   # sarkan zincirler (siluet)
        x = rng.uniform(0, W) + pad
        ln = rng.uniform(80, 300)
        Y.chain(sk, (x, -10), (x + 0.5, ln), 0, link=18, col=FG_COL, hi=(80, 30, 20), ink_a=0.0, thick=4.0)
        hk = bezier((x, ln + 6), (x + 22, ln + 36), (x - 3, ln + 46), 10)
        sk.path(ribbon(hk, np.linspace(6, 2, 10)), FG_COL)
    for _ in range(6):    # zincirden zincire sarkan kavis
        x = rng.uniform(0, W) + pad
        Y.chain(sk, (x, 20), (x + rng.uniform(200, 420), 30), rng.uniform(60, 130), link=16, col=FG_COL, hi=(80, 30, 20), ink_a=0.0, thick=3.6)
    L = Layer(W, Hs)
    L.a = Y.wrap_core(sk.snap(), pad, W)
    return L


def ash_particle():
    sk = Sk(16, 12)
    sk.path(smooth_path([(2, 6), (5, 2), (11, 3), (14, 7), (10, 10), (4, 9)], True, 0.4), (255, 255, 255), 1.0)
    return sk.snap()


def ember_particle():
    sk = Sk(16, 16)
    sk.c.drawCircle(8, 8, 6, sk.paint((255, 255, 255), 0.3, 3))
    sk.c.drawCircle(8, 8, 2.0, sk.paint((255, 255, 255), 1.0, 0.5))
    return sk.snap()


PARTICLES = {'ash': 'ash_particle', 'ember': 'ember_particle'}
