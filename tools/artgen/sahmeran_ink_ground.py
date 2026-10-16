"""Şahmeran Mağaraları v2 "mürekkep" oyun alanı: karo atlası (ıslak kaya + yosun yastığı + kenarda kristal),
dünya uzayı kaya dokusu (tortul katmanlar, damla izleri, ışıyan kristal damarları), yosun dokusu (üst 2-3 karo),
ön plan siluet şeritleri (dikit uçları, kristaller / sarkıtlar, sarkan yosun) ve spor parçacığı.
Yerleşim ve ölçü Ötüken ile aynı (inkkit_zemin)."""
import math

import numpy as np

import inkkit_ortam as ik
from inkkit_ortam import (INK, Layer, Sk, blade, blade_tip, blade_spine, blob, c01, fbm, leaf_shape, mix, noise,
                          poly_path, premul, ribbon, smooth_path, smoothstep, bezier)
import inkkit_yeralti as Y
import inkkit_zemin as Z
from inkkit_zemin import C

MOSS_TIP = (120, 186, 116)
MOSS_TOP = (70, 132, 86)
MOSS_MID = (40, 92, 70)
MOSS_DARK = (20, 52, 46)
STONE_A = (40, 50, 56)
STONE_B = (56, 68, 72)
STONE_C = (28, 34, 42)
STONE_L = (110, 140, 138)
RIM = (110, 220, 196)
EMER = (40, 196, 150)
EMER_HI = (196, 255, 232)
EMER_D = (10, 64, 60)
AMETH = (150, 96, 214)
AMETH_HI = (232, 206, 255)
AMETH_D = (40, 20, 70)
AMBER = (236, 170, 70)
GLOW = (90, 255, 200)


def _snapL(sk):
    L = Layer(C, C)
    L.a = sk.snap()
    return L


class SahmeranSpec(Z.Spec):
    rim = RIM
    rim_a = 0.32
    ceil_dark = (8, 18, 22)
    ink_w = 3.0
    edge_amp = (1.2, 3.0, 4.0)

    def top_band(self, art, emit, cov, top_d, m, rng, seed):
        K = ik.K
        CP = ik.P(C)
        band_d = 12 + 5 * noise(C, 1, 2, seed + 2, wrap=False)[0][None, :] + rng.uniform(-2, 2)
        g_t = np.clip(top_d / band_d, 0, 1.4)
        gcol = mix(c01(MOSS_TOP), c01(MOSS_MID), smoothstep(0.0, 0.6, g_t)[..., None])
        gcol = mix(gcol, c01(MOSS_DARK), smoothstep(0.55, 1.05, g_t)[..., None])
        gmask = (1 - smoothstep(0.85, 1.15, g_t)) * cov
        lay = Layer(C, C)
        lay.fill_mask(gmask, gcol)
        sk = Sk(C, C)
        # yosun yastığı: yuvarlak küçük lekeler (açık üstte, koyu altta), kenarda hafif taşar
        for _ in range(int(90 * (1 if (m & 10) == 0 else 0.75))):
            x = rng.uniform(-2, C + 2)
            if (m & 8) and x < 5:
                continue
            if (m & 2) and x > C - 5:
                continue
            y = rng.uniform(-1.5, 13) ** 1.0
            r = rng.uniform(1.0, 3.2)
            t = np.clip(y / 13, 0, 1)
            c = mix(c01(MOSS_TIP), c01(MOSS_DARK), t) * rng.uniform(0.8, 1.15)
            sk.c.drawOval(Y.skia_rect(x - r, y - r * 0.7, x + r, y + r * 0.7), sk.paint(tuple(np.clip(c, 0, 1) * 255), rng.uniform(0.7, 1.0)))
        # birkaç kısa yosun sapı (sporlu)
        for _ in range(int(rng.integers(4, 10))):
            x = rng.uniform(3, C - 3)
            h = rng.uniform(3, 8)
            sk.path(blade(x, 2.5, h, rng.uniform(-0.4, 0.4), 1.0), MOSS_TIP, 0.9)
        bl = sk.snap()
        bl *= np.maximum(gmask, (top_d > -3).astype(np.float32) * (top_d < 3) * 0.9)[..., None] ** 0.5
        lay.a = bl + lay.a * (1 - bl[..., 3:4])
        # üst kenarda kristal ışığının vurduğu açık çizgi
        tip = (1 - smoothstep(0.3, 2.5, top_d)) * cov
        lay.fill_mask(tip * 0.45, c01((150, 230, 170)))
        # bandın altından sarkan ince yosun saçakları ve su damlası
        sk2 = Sk(C, C)
        for _ in range(int(rng.integers(3, 8))):
            x = rng.uniform(2, C - 2)
            y0 = float(band_d[0, int(np.clip(x * K, 0, CP - 1))]) * rng.uniform(0.75, 1.0)
            ln = rng.uniform(4, 12)
            pts = [(x + k * rng.uniform(-0.8, 0.8), y0 + ln * k / 3) for k in range(4)]
            sk2.path(ribbon(pts, [1.6, 1.1, 0.7, 0.3]), MOSS_DARK, 0.9)
        rt = sk2.snap() * cov[..., None]
        lay.a = rt + lay.a * (1 - rt[..., 3:4])
        art.a = lay.a + art.a * (1 - lay.a[..., 3:4])
        # ışık sporları (ışıma katmanı)
        se = Sk(C, C)
        for _ in range(int(rng.integers(0, 4))):
            x, y = rng.uniform(4, C - 4), rng.uniform(0, 6)
            se.c.drawCircle(x, y, 1.6, se.paint(GLOW, 0.2, 1.0))
            se.c.drawCircle(x, y, 0.8, se.paint((210, 255, 235), 0.9))
        e = se.snap()
        emit.a = e + emit.a * (1 - e[..., 3:4])

    def embed(self, art, emit, cov, m, var, rng, seed):
        if var == 1 and (m & (2 | 8)) and not (m & 4):
            side = 2 if (m & 2) else 8
            sk = Sk(C, C)
            se = Sk(C, C)
            y = rng.uniform(22, 38)
            x = C - 3 if side == 2 else 3
            # yan yüzden dışa doğru büyüyen küme: döndürülmüş tuval
            sk.c.save()
            se.c.save()
            ang = 70 if side == 2 else -70
            for s_ in (sk, se):
                s_.c.translate(x, y)
                s_.c.rotate(ang)
            body, hi, dk = (AMETH, AMETH_HI, AMETH_D) if rng.random() < 0.25 else (EMER, EMER_HI, EMER_D)
            Y.crystal_cluster(sk, 0, 4, rng.uniform(14, 20), seed + 3, body, hi, dk, ink_w=1.0, glow=se, glow_a=0.7, n=4,
                              spread=0.8, halo=0.3)
            sk.c.restore()
            se.c.restore()
            a = sk.snap()
            art.a = a + art.a * (1 - a[..., 3:4])
            e = se.snap()
            emit.a = e + emit.a * (1 - e[..., 3:4])
        elif var == 2 and (m & 1) and not (m & 4) and rng.random() < 0.5:
            # yosun yastığında su birikintisi parıltısı / küçük kaya
            from otuken_ink_ground import rock_small
            rr = rock_small(seed + 6, rng.uniform(6, 9), rng.uniform(4, 6), base=(76, 94, 96))
            Z.blit(art.a, rr, rng.uniform(8, C - 22), rng.uniform(4, 9), cov)

    # ------------------------------------------------------------ örtü öbekleri
    def tuft(self, k, seed):
        rng = np.random.default_rng(seed)
        sk = Sk(C, C)
        se = Sk(C, C)
        base = C + 1
        kind = k % 8

        def moss_clump(cx, w, h):
            for _ in range(int(w * 1.6)):
                x = cx + rng.normal(0, w / 3)
                y = base - rng.uniform(0, h) * (1 - abs(x - cx) / (w * 1.2))
                r = rng.uniform(1.4, 3.4)
                t = (base - y) / max(h, 1)
                c = mix(c01(MOSS_DARK), c01(MOSS_TIP), t * rng.uniform(0.6, 1.1))
                sk.c.drawOval(Y.skia_rect(x - r, y - r * 0.75, x + r, y + r * 0.75), sk.paint(tuple(np.clip(c, 0, 1) * 255)))

        def grass(n, hmax, cols):
            for _ in range(n):
                x = rng.uniform(3, C - 3)
                h = rng.uniform(5, hmax)
                ln_, wd_ = rng.uniform(-0.6, 0.6), rng.uniform(1.2, 2.4)
                sk.path(blade(x, base, h, ln_, wd_), cols[int(rng.integers(len(cols)))], rng.uniform(0.8, 1.0))
                if rng.random() < 0.35:
                    sk.path(blade_tip(x, base, h, ln_, wd_, 0.3), INK, 0.7)

        def shroom(x, h, r, cap, glow_c):
            lean = rng.uniform(-0.15, 0.15)
            stem = ribbon([(x, base), (x + lean * h * 0.5, base - h * 0.5), (x + lean * h, base - h)], [r * 0.4, r * 0.32, r * 0.28])
            sk.path(stem, (176, 190, 176))
            sk.path(stem, INK, 0.9, 0, 0.9)
            tx, ty = x + lean * h, base - h
            capp = smooth_path([(tx - r, ty + 1.5), (tx - r * 0.75, ty - r * 0.5), (tx, ty - r * 0.75), (tx + r * 0.75, ty - r * 0.5),
                                (tx + r, ty + 1.5), (tx, ty + r * 0.15)], True, 0.4)
            sk.path(capp, cap)
            sk.path(capp, INK, 1.0, 0, 1.1)
            se.path(capp, glow_c, 0.4 if kind == 2 else 0.22, 1.2)
            se.c.drawCircle(tx, ty - r * 0.2, r * 1.3, se.paint(glow_c, 0.12, r * 0.8))
            for _ in range(3):
                sx, sy = tx + rng.uniform(-r * 0.6, r * 0.6), ty - rng.uniform(r * 0.05, r * 0.45)
                sk.c.drawCircle(sx, sy, 0.9, sk.paint((230, 255, 240)))
                se.c.drawCircle(sx, sy, 0.9, se.paint((230, 255, 240), 0.9))

        if kind in (0, 4, 7):
            moss_clump(rng.uniform(16, 32), rng.uniform(10, 18), rng.uniform(5, 10))
            grass(10 if kind != 7 else 4, 14, [MOSS_TOP, MOSS_MID, MOSS_TIP])
            if kind == 0:   # eğrelti filizi
                x0 = rng.uniform(14, C - 14)
                for j in range(4):
                    ang = math.radians(rng.uniform(-60, 60)) - math.pi / 2
                    ln = rng.uniform(10, 18)
                    p2 = (x0 + math.cos(ang) * ln, base + math.sin(ang) * ln)
                    pts = bezier((x0, base), ((x0 + p2[0]) / 2, (base + p2[1]) / 2 - 3), p2, 8)
                    sk.path(ribbon(pts, np.linspace(1.6, 0.4, 8)), MOSS_MID)
                    for jj in range(2, 8):
                        q = pts[jj]
                        for sgn in (-1, 1):
                            sk.path(leaf_shape(q[0], q[1], 4, 1.6, ang + sgn * 1.0), MOSS_TOP if sgn < 0 else MOSS_MID)
            if kind == 4:
                Y.crystal_cluster(sk, rng.uniform(14, 34), base - 1, 12, seed + 4, AMETH, AMETH_HI, AMETH_D, ink_w=0.9,
                                  glow=se, glow_a=0.45, n=3, halo=0.0)
            if kind == 7:
                for _ in range(4):   # su damlaları
                    x, y = rng.uniform(6, C - 6), base - rng.uniform(2, 8)
                    sk.c.drawCircle(x, y, 1.3, sk.paint((170, 240, 225), 0.9))
        elif kind == 1:
            grass(5, 8, [MOSS_TOP, MOSS_MID])
            for cx in sorted(rng.uniform(10, C - 10, 2)):
                Y.crystal_cluster(sk, cx, base - 1, rng.uniform(12, 20), int(cx * 31) + seed, EMER, EMER_HI, EMER_D,
                                  ink_w=1.0, glow=se, glow_a=0.7, n=int(rng.integers(3, 5)), halo=0.3)
        elif kind in (2, 6):
            moss_clump(24, 16, 5)
            cap, gc = ((60, 170, 150), GLOW) if kind == 2 else ((150, 110, 200), (190, 140, 255))
            for j in range(int(rng.integers(3, 5))):
                shroom(rng.uniform(10, C - 10), rng.uniform(6, 16), rng.uniform(3, 6), cap, gc)
        elif kind == 3:
            grass(26, 24, [(96, 150, 120), (60, 110, 90), (140, 190, 150), MOSS_DARK])
        elif kind == 5:
            # yılan iskeleti kalıntısı: kafatası + omurga
            moss_clump(30, 12, 4)
            pts = bezier((6, base - 2), (20, base - 9), (34, base - 3), 14)
            for j in range(0, 14):
                q = pts[j]
                sk.c.drawCircle(q[0], q[1], 1.4, sk.paint((214, 206, 184)))
                sk.path(ribbon([(q[0], q[1] - 3.2), (q[0] + 0.6, q[1] + 3.0)], [0.6, 0.4]), (200, 192, 170), 0.9)
            sk.path(ribbon(pts, [1.0] * 14), INK, 0.5, 0, 0.6)
            hx, hy = 38, base - 3
            skull = smooth_path([(hx - 4, hy + 1), (hx - 3, hy - 3), (hx + 3, hy - 3.5), (hx + 8, hy - 1), (hx + 7, hy + 1.5)], True, 0.4)
            sk.path(skull, (224, 216, 194))
            sk.path(skull, INK, 1.0, 0, 0.9)
            sk.c.drawCircle(hx + 1.5, hy - 1.4, 1.1, sk.paint(INK))
        return sk.snap(), se.snap()

    def ceiling(self, i, seed):
        rng = np.random.default_rng(seed)
        sk = Sk(C, C)
        se = Sk(C, C)
        if i == 0:
            for _ in range(int(rng.integers(2, 4))):
                x = rng.uniform(6, C - 6)
                ln = rng.uniform(12, 34)
                w = rng.uniform(4, 8)
                pts = [(x - w / 2, -1), (x - w * 0.15, ln * 0.6), (x, ln), (x + w * 0.15, ln * 0.6), (x + w / 2, -1)]
                p = smooth_path(pts, True, 0.4)
                sk.path(p, STONE_B)
                sk.path(smooth_path([(x - w / 2 + 1, -1), (x - w * 0.12, ln * 0.55), (x - w * 0.05, ln * 0.85), (x - w * 0.05, -1)], True, 0.4), STONE_L, 0.6)
                sk.path(p, INK, 1.0, 0, 1.0)
                sk.c.drawCircle(x, ln + 2.5, 1.3, sk.paint((170, 240, 225), 0.95))
        elif i == 1:
            for _ in range(int(rng.integers(4, 8))):
                x = rng.uniform(3, C - 3)
                ln = rng.uniform(8, 30)
                pts = [(x + math.sin(k * 0.9 + x) * 1.5 * k / 5, -1 + ln * k / 5) for k in range(6)]
                sk.path(ribbon(pts, np.linspace(2.6, 0.5, 6)), MOSS_MID, 1.0)
            # ışıl böceği iplikleri: ince ipek, uçlarda ve boyunca ışıyan damlalar
            for _ in range(int(rng.integers(3, 6))):
                x = rng.uniform(4, C - 4)
                ln = rng.uniform(14, 44)
                sk.path(ribbon([(x, 0), (x + 0.3, ln)], [0.4, 0.3]), (150, 200, 190), 0.5)
                for k in range(int(rng.integers(2, 5))):
                    y = ln * rng.uniform(0.3, 1.0)
                    se.c.drawCircle(x, y, 2.0, se.paint(GLOW, 0.3, 1.5))
                    se.c.drawCircle(x, y, 0.8, se.paint((220, 255, 240), 1.0))
                    sk.c.drawCircle(x, y, 0.8, sk.paint((200, 255, 230)))
        else:
            x = rng.uniform(16, C - 16)
            Y.crystal_cluster(sk, x, 0, rng.uniform(14, 22), seed + 2, EMER, EMER_HI, EMER_D, ink_w=1.0, glow=se,
                              glow_a=0.6, n=4, up=False, halo=0.25)
            for _ in range(3):
                xx = rng.uniform(4, C - 4)
                ln = rng.uniform(6, 16)
                sk.path(ribbon([(xx, -1), (xx + 0.5, ln)], [2.2, 0.4]), MOSS_MID)
        return sk.snap(), se.snap()

    # ------------------------------------------------------------ platform: oymalı taş levha
    def platform(self, kind, var, seed):
        rng = np.random.default_rng(seed)
        sk = Sk(C, C)
        se = Sk(C, C)
        top, beam_y0, beam_y1 = 0.5, 5.5, 17.0
        if kind in (0, 2):
            px = 9 if kind == 0 else C - 9
            post = poly_path([(px - 5.5, beam_y0), (px + 5.5, beam_y0), (px + 5, C + 1), (px - 5, C + 1)])
            sk.path(post, STONE_A)
            sk.path(poly_path([(px - 5.5, beam_y0), (px - 2, beam_y0), (px - 2, C + 1), (px - 5, C + 1)]), STONE_L, 0.55)
            for yy in (24, 36):
                sk.path(poly_path([(px - 6.5, yy), (px + 6.5, yy), (px + 6.5, yy + 3), (px - 6.5, yy + 3)]), STONE_B)
                sk.path(poly_path([(px - 6.5, yy), (px + 6.5, yy), (px + 6.5, yy + 3), (px - 6.5, yy + 3)]), INK, 0.9, 0, 0.9)
            sk.path(post, INK, 1.0, 0, 2.0)
        x0 = 1.0 if kind == 0 else -2
        x1 = C - 1.0 if kind == 2 else C + 2
        beam = poly_path([(x0, beam_y0), (x1, beam_y0), (x1, beam_y1), (x0, beam_y1)])
        sk.path(beam, STONE_B)
        sk.path(poly_path([(x0, beam_y1 - 3.5), (x1, beam_y1 - 3.5), (x1, beam_y1), (x0, beam_y1)]), STONE_C)
        # pul frizi: iki sıra kemer (yılan pulu)
        for row, yy in enumerate((8.5, 12.0)):
            xx = x0 + (2.0 if row else 0.0)
            while xx < x1 - 1:
                sk.path(smooth_path([(xx, yy + 2.6), (xx + 2, yy), (xx + 4, yy + 2.6)], False, 0.5), INK, 0.65, 0, 0.8)
                sk.path(ribbon([(xx + 0.8, yy + 1.0), (xx + 2, yy + 0.4)], [0.6, 0.2]), STONE_L, 0.6)
                xx += 4.0
        if kind == 1 and var == 1:
            # ortada kehribar taşlı yılan başı kabartması
            cx = C / 2
            head = smooth_path([(cx - 6, beam_y1 - 1), (cx - 6.5, beam_y0 + 3), (cx, beam_y0 + 0.5), (cx + 6.5, beam_y0 + 3), (cx + 6, beam_y1 - 1)], True, 0.4)
            sk.path(head, (64, 96, 80))
            sk.path(head, INK, 1.0, 0, 1.0)
            for sd in (-1, 1):   # oyma gözler (ışımasız; platform sırası boncuk gibi parlamasın)
                sk.c.drawCircle(cx + sd * 2.4, beam_y0 + 6, 0.9, sk.paint((150, 120, 60)))
        deck = poly_path([(x0, top), (x1, top), (x1, beam_y0), (x0, beam_y0)])
        sk.path(deck, (84, 108, 108))
        sk.path(poly_path([(x0, top), (x1, top), (x1, top + 1.6), (x0, top + 1.6)]), (150, 196, 180), 0.8)
        # üstte yosun lekeleri
        for _ in range(int(rng.integers(3, 8))):
            x = rng.uniform(x0 + 2, x1 - 2)
            r = rng.uniform(1.5, 4)
            sk.c.drawOval(Y.skia_rect(x - r, top - 0.6, x + r, top + 2.2), sk.paint(MOSS_TOP, 0.9))
        # kesik derzler
        xx = rng.uniform(6, 16)
        while xx < C - 2:
            sk.path(ribbon([(xx, top), (xx + 0.3, beam_y1)], [1.1, 1.1]), INK, 0.6)
            xx += rng.uniform(16, 26)
        sk.path(poly_path([(x0, top), (x1, top), (x1, beam_y1), (x0, beam_y1)], closed=True) if kind != 1 else
                poly_path([(x0, top), (x1, top)], closed=False), INK, 1.0, 0, 2.2)
        sk.path(poly_path([(x0, beam_y1), (x1, beam_y1)], closed=False), INK, 1.0, 0, 2.4)
        sk.path(poly_path([(x0, beam_y0), (x1, beam_y0)], closed=False), INK, 0.8, 0, 1.2)
        # alttan sarkan yosun
        for _ in range(int(rng.integers(2, 5))):
            x = rng.uniform(4, C - 4)
            ln = rng.uniform(4, 14)
            sk.path(ribbon([(x, beam_y1), (x + rng.uniform(-1, 1), beam_y1 + ln)], [2.0, 0.4]), MOSS_MID, 0.95)
        return sk.snap(), se.snap()


SPEC = SahmeranSpec()


# ------------------------------------------------------------------ dünya uzayı dokular
def soil_texture(seed=610, S=1024):
    """Islak kaya: dalgalı tortul katmanlar, dikey damla izleri, mürekkepli çakıl; ışıyan kristal damarları ve
    küçük kristal cepleri. -> (sanat Layer, ışıma Layer)."""
    rng = np.random.default_rng(seed)
    ys = (np.arange(ik.P(S), dtype=np.float32)[:, None] + 0.5) / ik.K
    warp = noise(S, S, 40, seed, sx=110, sy=30) * 30
    yy = ys + warp
    bands = np.sin(yy / S * 2 * math.pi * 9) * 0.5 + np.sin(yy / S * 2 * math.pi * 23 + 1.3) * 0.3
    nz = fbm(S, S, [60, 20, 6], seed + 1)
    t = np.clip(0.5 + 0.35 * bands + 0.3 * nz, 0, 1)
    rgb = mix(c01(STONE_C), c01(STONE_A), smoothstep(0.1, 0.55, t)[..., None])
    rgb = mix(rgb, c01(STONE_B), smoothstep(0.6, 0.95, t)[..., None])
    drip = noise(S, S, 0, seed + 3, sx=2.5, sy=60)
    rgb *= (1 + 0.1 * drip[..., None])
    br = noise(S, S, 0, seed + 4, sx=24, sy=2.0)
    rgb *= (1 + 0.06 * br[..., None])
    L = Layer(S, S)
    L.a = premul(rgb.astype(np.float32), np.ones(rgb.shape[:2], np.float32))
    E = Layer(S, S)
    sk = Sk(S, S)
    se = Sk(S, S)
    # katman sınırı çizgileri (mürekkep, kesik)
    for _ in range(60):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        ln = rng.uniform(40, 160)
        pts = [(x + ln * s_, y + 4 * math.sin(s_ * 3 + x)) for s_ in np.linspace(0, 1, 6)]
        Z.tile_wrap_draw(sk, S, x, y, 200, lambda dx, dy: sk.path(ribbon([(p[0] + dx, p[1] + dy) for p in pts],
                                                                         [0.3, 1.4, 1.8, 1.4, 1.0, 0.3]), INK, 0.45))
    # kristal damarları (zikzak, ışıyan)
    for _ in range(14):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        pts = [(x, y)]
        ang = rng.uniform(-0.6, 0.6)
        for k in range(int(rng.integers(5, 10))):
            ang += rng.uniform(-0.8, 0.8)
            ln = rng.uniform(8, 22)
            pts.append((pts[-1][0] + math.cos(ang) * ln, pts[-1][1] + math.sin(ang) * ln * 0.7))
        ws = np.linspace(rng.uniform(1.2, 2.6), 0.4, len(pts))

        def dv(dx, dy, pts=pts, ws=ws):
            q = [(p[0] + dx, p[1] + dy) for p in pts]
            sk.path(ribbon(q, ws * 1.8), INK, 0.8)
            sk.path(ribbon(q, ws), (120, 230, 200), 1.0)
            se.path(ribbon(q, ws * 3), GLOW, 0.25, 3)
            se.path(ribbon(q, ws * 0.8), (200, 255, 235), 0.9)
        Z.tile_wrap_draw(sk, S, x, y, 260, dv)
    # kristal cepleri (geod)
    for _ in range(9):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        r = rng.uniform(10, 20)
        ame = rng.random() < 0.3

        def gd(dx, dy, x=x, y=y, r=r, ame=ame):
            sk.path(blob(x + dx, y + dy, r * 1.15, r * 0.8, int(x), 10, 0.15), (14, 20, 26))
            body, hi, dk = (AMETH, AMETH_HI, AMETH_D) if ame else (EMER, EMER_HI, EMER_D)
            Y.crystal_cluster(sk, x + dx, y + dy + r * 0.55, r * 1.1, int(x * 7), body, hi, dk, ink_w=1.0, glow=se,
                              glow_a=0.6, n=4, spread=0.9, halo=0.5)
            sk.path(blob(x + dx, y + dy, r * 1.15, r * 0.8, int(x), 10, 0.15), INK, 1.0, 0, 1.6)
        Z.tile_wrap_draw(sk, S, x, y, 40, gd)
    # çakıl
    for _ in range(22):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        rx = rng.uniform(4, 14)
        ry = rx * rng.uniform(0.5, 0.8)
        cc = np.array(STONE_B) * rng.uniform(0.8, 1.1)

        def pb(dx, dy, x=x, y=y, rx=rx, ry=ry, cc=cc):
            q = blob(x + dx, y + dy, rx, ry, int(x * 1000) % 100000, n=8, jitter=0.2)
            sk.path(q, tuple(cc))
            sk.path(blob(x + dx - rx * 0.15, y + dy - ry * 0.3, rx * 0.6, ry * 0.4, 7, n=8, jitter=0.1), tuple(np.minimum(cc * 1.35, 255)), 0.8)
            sk.path(q, INK, 0.9, 0, 1.4)
        Z.tile_wrap_draw(sk, S, x, y, 20, pb)
    dec = sk.snap()
    L.a = dec + L.a * (1 - dec[..., 3:4])
    E.a = se.snap()
    return L, E


def moss_texture(seed=660, S=512):
    """Üst 2-3 karonun dünya uzayı dokusu: ıslak koyu kaya üstünde boyalı yosun yamaları (yumuşak kenarlı
    lekeler, üstleri açık), seyrek kısa saplar ve su damlası parıltısı. Fazla benekli olmasın: az sayıda iri leke."""
    rng = np.random.default_rng(seed)
    nz = fbm(S, S, [40, 12], seed + 1)
    base = mix(c01((24, 34, 38)), c01((34, 48, 50)), (0.5 + 0.5 * nz)[..., None])
    patch = fbm(S, S, [36, 14, 5], seed + 7)
    pm = smoothstep(-0.05, 0.25, patch)
    tone = fbm(S, S, [20, 6], seed + 9)
    moss = mix(c01((22, 52, 44)), c01((52, 104, 74)), smoothstep(-0.4, 0.6, tone)[..., None])
    # yamanın üst kenarı açık (yukarıdan gelen kristal ışığı): dikey türev
    gy = np.gradient(ndimage_blur(pm, 2.0), axis=0) * ik.K
    moss = mix(moss, c01((96, 160, 104)), np.clip(-gy * 5, 0, 0.6)[..., None])
    moss = mix(moss, c01((14, 30, 30)), np.clip(gy * 5, 0, 0.5)[..., None])
    rgb = mix(base, moss, pm[..., None])
    br = noise(S, S, 0, seed + 4, sx=10, sy=2.0)
    rgb *= (1 + 0.08 * br[..., None])
    L = Layer(S, S)
    L.a = premul(rgb.astype(np.float32), np.ones(rgb.shape[:2], np.float32))
    sk = Sk(S, S)
    for _ in range(900):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        if patch[int(y * ik.K) % patch.shape[0], int(x * ik.K) % patch.shape[1]] < 0.1:
            continue
        r = rng.uniform(1.6, 3.6)
        c = [(30, 70, 54), (48, 96, 70), (74, 132, 90)][int(rng.choice(3, p=[0.4, 0.4, 0.2]))]
        Z.tile_wrap_draw(sk, S, x, y, 8, lambda dx, dy, x=x, y=y, r=r, c=c: sk.c.drawOval(
            Y.skia_rect(x + dx - r, y + dy - r * 0.6, x + dx + r, y + dy + r * 0.6), sk.paint(c, 0.55)))
    for _ in range(260):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        if patch[int(y * ik.K) % patch.shape[0], int(x * ik.K) % patch.shape[1]] < 0.15:
            continue
        h = rng.uniform(4, 10)
        Z.tile_wrap_draw(sk, S, x, y, 20, lambda dx, dy, x=x, y=y, h=h: sk.path(
            blade(x + dx, y + dy, h, rng.uniform(-0.4, 0.4), 1.1), (90, 150, 100) if rng.random() < 0.4 else (44, 90, 66), 0.8))
    for _ in range(40):   # kaya üstünde mürekkep çatlak / taş kenarı
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        ln = rng.uniform(10, 40)
        Z.tile_wrap_draw(sk, S, x, y, 50, lambda dx, dy, x=x, y=y, ln=ln: sk.path(
            ribbon([(x + dx, y + dy), (x + dx + ln * 0.5, y + dy + rng.uniform(-3, 3)), (x + dx + ln, y + dy)], [0.3, 1.3, 0.3]), INK, 0.45))
    for _ in range(50):
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        Z.tile_wrap_draw(sk, S, x, y, 4, lambda dx, dy, x=x, y=y: sk.c.drawCircle(x + dx, y + dy, 1.0, sk.paint((170, 240, 220), 0.6)))
    bl = sk.snap()
    L.a = bl + L.a * (1 - bl[..., 3:4])
    return L


def ndimage_blur(a, s):
    from scipy import ndimage
    return ndimage.gaussian_filter(a, s * ik.K, mode='wrap')


# ------------------------------------------------------------------ ön plan
FG_COL = (6, 16, 20)
FG_RIM = (60, 150, 130)


def fg_bottom_strip(seed=710, W=3840, Hs=260):
    """Alt kenar: koyu kaya sırtı, dikit uçları ve kristal siluetleri (teal kenar ışıklı)."""
    rng = np.random.default_rng(seed)
    pad = 160
    sk = Sk(W + 2 * pad, Hs)
    base = Hs - 40
    pts = [(x, base + 20 + 16 * math.sin(x / 160.0 + 1) + 8 * math.sin(x / 47.0) + rng.uniform(-4, 4))
           for x in np.linspace(0, W + 2 * pad, 120)]
    sk.path(ribbon([(p[0], p[1] - 1.5) for p in pts], [3.0] * len(pts)), FG_RIM, 0.6)
    sk.path(smooth_path(pts + [(W + 2 * pad, Hs + 4), (0, Hs + 4)], True, 0.3), FG_COL)
    for _ in range(26):
        x = rng.uniform(0, W) + pad
        h = rng.uniform(40, 170)
        w = rng.uniform(18, 50)
        y0 = base + 30
        p = smooth_path([(x - w / 2, y0), (x - w * 0.25, y0 - h * 0.5), (x + rng.uniform(-3, 3), y0 - h), (x + w * 0.25, y0 - h * 0.5),
                         (x + w / 2, y0)], True, 0.4)
        sk.path(p, FG_RIM, 0.5, 0, 3.0)
        sk.path(p, FG_COL)
    for _ in range(14):
        x = rng.uniform(0, W) + pad
        Y.crystal_cluster(sk, x, base + 26, rng.uniform(30, 70), int(x), FG_COL, (40, 110, 100), FG_COL, ink_a=0.0,
                          n=int(rng.integers(3, 6)))
    for _ in range(int(W * 0.25)):
        x = rng.uniform(0, W) + pad
        h = rng.uniform(8, 40)
        sk.path(blade(x, base + rng.uniform(16, 40), h, rng.uniform(-0.5, 0.5), rng.uniform(2.5, 5)), FG_COL)
    L = Layer(W, Hs)
    L.a = Y.wrap_core(sk.snap(), pad, W)
    return L


def fg_top_strip(seed=730, W=3840, Hs=300):
    """Üst kenar: koyu sarkıt siluetleri ve sarkan yosun (uçlarında parlak damla)."""
    rng = np.random.default_rng(seed)
    pad = 200
    sk = Sk(W + 2 * pad, Hs)
    pts = [(x, 10 + 10 * math.sin(x / 130.0) + rng.uniform(-3, 3)) for x in np.linspace(0, W + 2 * pad, 100)]
    sk.path(smooth_path([(0, -10)] + pts + [(W + 2 * pad, -10)], True, 0.3), FG_COL)
    for cx in rng.uniform(0, W, 22):
        x = cx + pad
        ln = rng.uniform(50, 240) if rng.random() < 0.6 else rng.uniform(20, 60)
        w = rng.uniform(18, 60) * (0.5 + ln / 240)
        p = smooth_path([(x - w / 2, 0), (x - w * 0.3, ln * 0.4), (x - w * 0.08, ln * 0.85), (x, ln), (x + w * 0.1, ln * 0.8),
                         (x + w * 0.3, ln * 0.4), (x + w / 2, 0)], True, 0.4)
        sk.path(p, FG_RIM, 0.45, 0, 3.0)
        sk.path(p, FG_COL)
        if rng.random() < 0.6:
            sk.c.drawCircle(x, ln + 6, 2.2, sk.paint((150, 240, 220), 0.8))
    for _ in range(30):
        x0 = rng.uniform(0, W) + pad
        for k in range(int(rng.integers(3, 8))):
            sx = x0 + rng.normal(0, 18)
            ln = rng.uniform(30, 130)
            q = bezier((sx, 0), (sx + rng.uniform(-8, 8), ln * 0.5), (sx + rng.uniform(-14, 14), ln), 10)
            sk.path(ribbon(q, np.linspace(4, 0.8, 10)), FG_COL)
    L = Layer(W, Hs)
    L.a = Y.wrap_core(sk.snap(), pad, W)
    return L


def spore_particle():
    sk = Sk(16, 16)
    sk.c.drawCircle(8, 8, 6, sk.paint((255, 255, 255), 0.35, 3))
    sk.c.drawCircle(8, 8, 2.4, sk.paint((255, 255, 255), 1.0, 0.6))
    return sk.snap()


def drip_particle():
    sk = Sk(8, 24)
    sk.path(smooth_path([(4, 1), (5.2, 14), (6, 19), (4, 22.5), (2, 19), (2.8, 14)], True, 0.4), (255, 255, 255), 1.0)
    sk.path(ribbon([(3.5, 15), (3.2, 20)], [0.8, 0.4]), (255, 255, 255), 0.6)
    return sk.snap()


PARTICLES = {'spore': 'spore_particle', 'drip': 'drip_particle'}
