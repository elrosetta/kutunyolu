"""Bozkır Kurganları v2 "mürekkep" oyun alanı: kuru altın ot bandı, çatlak kuru toprak (lös), örtü öbekleri (sorguçlu
kılçık otu, deve dikeni, yavşan / pelin, bozkır lalesi), sarkan kuru kökler, ağartılmış tahta platform (ham deri bağlı,
koçboynuzu desenli keçe), ön plan siluet otlar ve savrulan ot kırıntısı. Işık sağdan (alçak güneş).

ink_zemin.py kurucusunu kullanır; atlas yerleşimi ve dünya ölçüsü Ötüken ile aynı.
"""
import math

import numpy as np

import inkkit_ortam as ik
from inkkit_ortam import (INK, Layer, Sk, bezier, blade, blade_spine, blade_tip, blob, c01, fbm, leaf_shape, mix, noise,
                          poly_path, premul, ribbon, smooth_path, smoothstep)
import ink_zemin as Z

C = Z.C
LIGHT = 1.0

ST = dict(
    surface='grass', light=LIGHT,
    grass_tip=(252, 214, 134), grass_top=(226, 168, 88), grass_mid=(166, 108, 64), grass_dark=(92, 52, 46),
    rim=(255, 198, 130), rim_a=0.6, root_col=(74, 42, 38), ceil_dark=(34, 18, 24), blade_lean=0.32, blade_ink=0.12,
    blade_h=1.15, blades=80, band=15,
)
ST['rock_fn'] = lambda seed, rx, ry: Z.rock_small(seed, rx, ry, base=(150, 112, 92), light=(0.6, -0.8))

WOOD = (168, 136, 104)       # güneşte ağarmış tahta
WOOD_D = (98, 70, 58)
WOOD_L = (222, 196, 160)
HIDE = (214, 184, 136)       # ham deri bağ
FELT_R = (164, 44, 40)
FELT_W = (232, 220, 196)


# ------------------------------------------------------------------ örtü öbekleri
def _stipa(sk, rng, x, n, hmax, wind=1.0, plumes=0.5):
    for _ in range(n):
        xx = x + rng.normal(0, 4)
        h = rng.uniform(8, hmax)
        ln = rng.uniform(0.0, 0.5) * wind
        wd = rng.uniform(1.3, 2.4)
        r = rng.random()
        c = ST['grass_dark'] if r < 0.35 else (ST['grass_tip'] if r < 0.62 else (ST['grass_top'] if r < 0.85 else ST['grass_mid']))
        if rng.random() < 0.35:
            sk.path(blade(xx + 0.8, C + 1, h, ln, wd), ST['rim'], 0.6)
        sk.path(blade(xx, C + 1, h, ln, wd, curl=0.45), c, rng.uniform(0.85, 1.0))
        q_ = rng.random()
        if q_ < 0.25:
            sk.path(blade_tip(xx, C + 1, h, ln, wd, rng.uniform(0.2, 0.4)), INK, rng.uniform(0.5, 0.85))
        elif q_ < 0.45:
            sk.path(blade_spine(xx, C + 1, h, ln, wd, side=-1.0), INK, rng.uniform(0.4, 0.7))
        if h > hmax * 0.55 and rng.random() < plumes:
            tip = (xx + ln * h, C + 1 - h)
            pl = rng.uniform(8, 16)
            q = bezier(tip, (tip[0] + wind * pl * 0.6, tip[1] - pl * 0.1), (tip[0] + wind * pl, tip[1] + pl * 0.35), 8)
            sk.path(ribbon(q, np.sin(np.linspace(0.2, math.pi * 0.95, 8)) * 1.8 + 0.3), (250, 232, 196), 0.85)


def _thistle(sk, rng, x):
    """Deve dikeni: dikenli gümüşi yapraklar, mor püsküllü baş."""
    stem = bezier((x, C + 1), (x + rng.uniform(-2, 2), C - 14), (x + rng.uniform(-3, 3), C - 26), 8)
    sk.path(ribbon(stem, np.linspace(2.4, 1.4, 8)), (128, 116, 90))
    sk.path(ribbon(stem, np.linspace(2.4, 1.4, 8)), INK, 0.6, 0, 0.6)
    for j in (2, 4, 5):
        q = stem[j]
        for sgn in (-1, 1):
            a = -math.pi / 2 + sgn * rng.uniform(0.9, 1.3)
            ln = rng.uniform(6, 10)
            pts = [(q[0], q[1])]
            for k in range(1, 4):
                t = k / 3
                pts.append((q[0] + math.cos(a) * ln * t, q[1] + math.sin(a) * ln * t + (1.5 if k % 2 else -1.0)))
            sk.path(ribbon(pts, [1.8, 1.4, 1.0, 0.3]), (150, 152, 120))
            sk.path(ribbon(pts, [1.8, 1.4, 1.0, 0.3]), INK, 0.7, 0, 0.6)
    hx, hy = stem[-1]
    bulb = smooth_path([(hx - 3.5, hy + 1), (hx - 3, hy - 3), (hx + 3, hy - 3), (hx + 3.5, hy + 1), (hx, hy + 4)], True, 0.4)
    sk.path(bulb, (126, 132, 96))
    for k in range(9):
        a = -math.pi / 2 + (k - 4) * 0.22
        sk.path(ribbon([(hx, hy - 2), (hx + math.cos(a) * 7, hy - 2 + math.sin(a) * 7)], [1.4, 0.6]), (170, 72, 150))
    sk.path(bulb, INK, 0.9, 0, 0.8)


def _tulip(sk, rng, x):
    """Bozkır lalesi: ince sap, kızıl kadeh çiçek (lale bozkırın çiçeğidir)."""
    for k in range(int(rng.integers(1, 3))):
        xx = x + k * rng.uniform(6, 10)
        h = rng.uniform(14, 24)
        stem = bezier((xx, C + 1), (xx + rng.uniform(-2, 2), C + 1 - h * 0.6), (xx + rng.uniform(-2, 2), C + 1 - h), 8)
        sk.path(ribbon(stem, np.linspace(1.6, 1.1, 8)), (96, 112, 66))
        sk.path(leaf_shape(xx, C, 12, 3.2, -math.pi / 2 - 0.4), (110, 128, 74))
        fx, fy = stem[-1]
        cup = smooth_path([(fx - 3.6, fy - 1), (fx - 3.2, fy - 7), (fx - 1, fy - 5), (fx, fy - 8), (fx + 1, fy - 5),
                           (fx + 3.2, fy - 7), (fx + 3.6, fy - 1), (fx, fy + 2)], True, 0.35)
        sk.path(cup, (206, 44, 40))
        sk.path(smooth_path([(fx + 0.5, fy - 6), (fx + 3, fy - 6.5), (fx + 3.2, fy - 1), (fx + 1, fy)], True, 0.4), (255, 120, 80), 0.7)
        sk.path(cup, INK, 0.9, 0, 0.8)


def _wormwood(sk, rng, x):
    """Yavşan / pelin: gümüşi yeşil, tüy gibi ince yapraklı alçak çalı."""
    for k in range(int(rng.integers(5, 9))):
        a = math.radians(-90 + rng.uniform(-55, 55))
        ln = rng.uniform(8, 18)
        p2 = (x + math.cos(a) * ln, C + 1 + math.sin(a) * ln)
        pts = bezier((x, C + 1), ((x + p2[0]) / 2, (C + 1 + p2[1]) / 2 - 2), p2, 7)
        col = (150, 148, 116) if rng.random() < 0.6 else (196, 190, 156)
        sk.path(ribbon(pts, np.linspace(1.4, 0.4, 7)), col)
        for j in range(1, 7):
            q = pts[j]
            for sgn in (-1, 1):
                sk.path(leaf_shape(q[0], q[1], 3.5, 1.0, a + sgn * 0.9), col, 0.9)


def grass_tuft(seed, kind):
    rng = np.random.default_rng(seed)
    sk = Sk(C, C)
    if kind in (0, 1, 3, 7):
        _stipa(sk, rng, C / 2, [26, 20, 34, 30][[0, 1, 3, 7].index(kind)], [28, 22, 30, 42][[0, 1, 3, 7].index(kind)])
        _stipa(sk, rng, rng.uniform(8, C - 8), 8, 14, plumes=0.0)
    elif kind == 2:
        _stipa(sk, rng, C * 0.3, 10, 16, plumes=0.0)
        _thistle(sk, rng, C * 0.6)
    elif kind == 4:
        _wormwood(sk, rng, C * 0.45)
        _stipa(sk, rng, C * 0.7, 8, 18)
    elif kind == 5:
        _stipa(sk, rng, C * 0.5, 12, 18, plumes=0.2)
        _tulip(sk, rng, C * 0.35)
    else:
        _stipa(sk, rng, C * 0.4, 12, 20)
        r = Z.rock_small(seed + 3, 7, 5, base=(150, 112, 92), light=(0.6, -0.8))
        h, w = r.shape[:2]
        out = sk.snap()
        x, y = ik.P(C * 0.62), ik.P(C) - h + ik.P(3)
        sub = out[y:y + h, x:x + w]
        hh, ww = sub.shape[:2]
        out[y:y + hh, x:x + ww] = r[:hh, :ww] + sub * (1 - r[:hh, :ww, 3:4])
        return out
    return sk.snap()


def ceiling_roots(seed):
    rng = np.random.default_rng(seed)
    sk = Sk(C, C)
    for _ in range(rng.integers(3, 7)):
        x = rng.uniform(3, C - 3)
        ln = rng.uniform(10, 36)
        pts = [(x + math.sin(k * 0.9 + x) * 2.0 * k / 5, -1 + ln * k / 5) for k in range(6)]
        sk.path(ribbon(pts, np.linspace(2.4, 0.4, 6)), (110, 74, 58), 1.0)
        sk.path(ribbon(pts, np.linspace(2.4, 0.4, 6)), INK, 0.6, 0, 0.6)
    for _ in range(rng.integers(2, 5)):
        x = rng.uniform(3, C - 3)
        ln = rng.uniform(6, 16)
        pts = [(x + rng.uniform(-1, 1), -1 + ln * k / 4) for k in range(5)]
        sk.path(ribbon(pts, np.linspace(2.6, 0.5, 5)), ST['grass_mid'], 0.9)
    for _ in range(rng.integers(2, 4)):       # düşmek üzere toprak kırıntısı
        sk.c.drawCircle(rng.uniform(4, C - 4), rng.uniform(2, 8), rng.uniform(0.8, 1.6), sk.paint((120, 80, 60)))
    return sk.snap()


def _ramhorn(sk, cx, cy, s, col):
    """Koçboynuzu motifi (keçe nakışı): ortadan iki yana kıvrılan sarmal."""
    for sgn in (-1, 1):
        pts = [(cx, cy + s * 0.6), (cx, cy - s * 0.2)]
        for t in np.linspace(0, 1.6 * math.pi, 9):
            r = s * (0.55 - 0.28 * t / (1.6 * math.pi))
            pts.append((cx + sgn * (s * 0.5 - r * math.cos(t)), cy - s * 0.2 - r * math.sin(t) * 0.9))
        sk.path(ribbon(pts, [s * 0.16] * len(pts)), col)


def platform_cell(kind, var, seed):
    """Ağarmış tahta platform: üst döşeme, ön kiriş, uçlarda dikme + ham deri bağ; ortada (var 1) sarkan koçboynuzu
    desenli kızıl keçe."""
    rng = np.random.default_rng(seed)
    sk = Sk(C, C)
    top, beam_y0, beam_y1 = 0.5, 5.5, 16.0
    if kind in (0, 2):
        px = 9 if kind == 0 else C - 9
        post = poly_path([(px - 5, beam_y0), (px + 5, beam_y0), (px + 5.5, C + 1), (px - 5.5, C + 1)])
        sk.path(post, WOOD_D)
        sk.path(poly_path([(px + 1.5, beam_y0), (px + 5, beam_y0), (px + 5.5, C + 1), (px + 2, C + 1)]), WOOD)
        for k in range(3):
            yy = 22 + k * 8 + rng.uniform(-2, 2)
            sk.path(ribbon([(px - 3, yy), (px - 1, yy + 3), (px + 1, yy + 6)], [0.4, 1.3, 0.3]), INK, 0.7)
        sk.path(post, INK, 1.0, 0, 2.2)
    x0 = 1.0 if kind == 0 else -2
    x1 = C - 1.0 if kind == 2 else C + 2
    if var == 1 and kind in (0, 2):
        # sarkan keçe: kirişin önünden aşağı, koçboynuzu nakışlı, alt ucu püsküllü
        fcx = 28 if kind == 0 else C - 28
        fx0, fx1 = fcx - 9, fcx + 9
        fy1 = 33 + rng.uniform(-2, 2)
        felt = smooth_path([(fx0, beam_y0 + 2), (fx1, beam_y0 + 2), (fx1 + 0.5, fy1 - 6), (fcx, fy1 + 1), (fx0 - 0.5, fy1 - 6)], True, 0.2)
        sk.path(felt, FELT_R)
        _ramhorn(sk, fcx, 18.5, 8, FELT_W)
        for k in range(4):
            xx = fx0 + 2 + k * (fx1 - fx0 - 4) / 3
            yb = fy1 - 6 + (1 - abs(xx - fcx) / 9) * 7
            sk.path(ribbon([(xx, yb), (xx + 0.6, yb + 5)], [1.3, 0.5]), (226, 190, 120))
        sk.path(felt, INK, 1.0, 0, 1.4)
    beam = poly_path([(x0, beam_y0), (x1, beam_y0), (x1, beam_y1), (x0, beam_y1)])
    sk.path(beam, WOOD)
    sk.path(poly_path([(x0, beam_y1 - 4), (x1, beam_y1 - 4), (x1, beam_y1), (x0, beam_y1)]), WOOD_D)
    sk.path(poly_path([(x0, beam_y0), (x1, beam_y0), (x1, beam_y0 + 2.5), (x0, beam_y0 + 2.5)]), WOOD_L, 0.85)
    for k in range(4):
        xx = rng.uniform(2, C - 8)
        yy = rng.uniform(beam_y0 + 3, beam_y1 - 3)
        sk.path(ribbon([(xx, yy), (xx + 4, yy + 0.4), (xx + 9, yy - 0.3)], [0.3, 1.2, 0.3]), INK, 0.6)
    deck = poly_path([(x0, top), (x1, top), (x1, beam_y0), (x0, beam_y0)])
    sk.path(deck, WOOD_L)
    xx = 0.0 if kind != 0 else 2.0
    while xx < C:
        wpl = rng.uniform(7, 11)
        if xx + wpl > C and kind == 2:
            break
        sk.path(ribbon([(xx, top), (xx + rng.uniform(-0.5, 0.5), beam_y0)], [1.3, 1.3]), INK, 0.8)
        xx += wpl
    sk.path(poly_path([(x0, top), (x1, top), (x1, beam_y1), (x0, beam_y1)], closed=True) if kind != 1 else
            poly_path([(x0, top), (x1, top)], closed=False), INK, 1.0, 0, 2.4)
    if kind == 1:
        sk.path(poly_path([(x0, beam_y1), (x1, beam_y1)], closed=False), INK, 1.0, 0, 2.6)
    sk.path(poly_path([(x0, beam_y0), (x1, beam_y0)], closed=False), INK, 0.8, 0, 1.4)
    if kind in (0, 2) or var == 1:
        px = 9 if kind == 0 else (C - 9 if kind == 2 else C / 2)
        if not (var == 1 and kind == 1):
            for k in range(4):
                yy = beam_y0 - 1 + k * 3.4
                pts = [(px - 7, yy), (px, yy + 1.4), (px + 7, yy + 0.3)]
                sk.path(ribbon(pts, [1.5, 2.4, 1.5]), HIDE)
                sk.path(ribbon(pts, [1.5, 2.4, 1.5]), INK, 0.9, 0, 0.8)
        if kind != 1:
            # at kılı püskülü
            for k in range(6):
                q = bezier((px + 5, beam_y1), (px + 6 + k * 0.4, beam_y1 + 6), (px + 7 + k * 0.9, beam_y1 + 13 + k), 6)
                sk.path(ribbon(q, np.linspace(1.0, 0.3, 6)), (40, 26, 30), 0.9)
    return sk.snap()


# ------------------------------------------------------------------ dünya uzayı dokular
def soil_texture(seed=600, S=1024):
    """Kuru çatlak toprak (lös): kızıl-toprak tortul bantlar, çokgen kuruma çatlakları (mürekkep), her çokgen kendi
    tonunda, çakıl ve seyrek kemik kırığı, ince kök."""
    rng = np.random.default_rng(seed)
    ys = (np.arange(ik.P(S), dtype=np.float32)[:, None] + 0.5) / ik.K
    warp = noise(S, S, 40, seed, sx=90, sy=30) * 26
    yy = ys + warp
    bands = np.sin(yy / S * 2 * math.pi * 6) * 0.5 + np.sin(yy / S * 2 * math.pi * 15 + 1.3) * 0.3
    nz = fbm(S, S, [60, 20, 6], seed + 1)
    t = np.clip(0.5 + 0.35 * bands + 0.3 * nz, 0, 1)
    A, B, Cc = (128, 78, 60), (160, 106, 72), (88, 50, 54)
    rgb = mix(c01(Cc), c01(A), smoothstep(0.1, 0.55, t)[..., None])
    rgb = mix(rgb, c01(B), smoothstep(0.6, 0.95, t)[..., None])
    # çatlak ağı (düşük çözünürlükte hesaplanıp büyütülür)
    from scipy import ndimage
    k0 = ik.K
    ik.K = 0.5
    edge, cid = Z.crack_net(S, seed + 4, n=190)
    ik.K = k0
    zf = ik.P(S) / edge.shape[0]
    edge = ndimage.zoom(edge, zf, order=1)
    cid = ndimage.zoom(cid, zf, order=0)
    tone = (np.random.default_rng(seed + 9).uniform(0.9, 1.1, 200))[cid % 200]
    rgb = rgb * tone[..., None]
    ew = 0.9 + 0.7 * noise(S, S, 6, seed + 7)
    crack = np.clip((ew - edge * 1.0) * ik.K * 0.5 + 0.5, 0, 1)
    lip = np.clip(1 - np.abs(edge - ew - 1.5) / 1.2, 0, 1)        # çatlak kenarında ışık alan dudak
    rgb = mix(rgb, c01((200, 146, 98)), (lip * 0.35)[..., None])
    rgb = mix(rgb, c01((40, 22, 26)), (crack * 0.85)[..., None])
    br = noise(S, S, 0, seed + 3, sx=24, sy=2.2)
    rgb *= (1 + 0.06 * br[..., None])

    def draw(sk, S_, rng_, put):
        for _ in range(40):
            x, y = rng_.uniform(0, S_), rng_.uniform(0, S_)
            pts = [(x, y)]
            ang = rng_.uniform(0.2, 1.2) * (1 if rng_.random() < 0.5 else -1) + math.pi / 2
            for k in range(7):
                ang += rng_.uniform(-0.4, 0.4)
                ln = rng_.uniform(6, 14)
                pts.append((pts[-1][0] + math.cos(ang) * ln, pts[-1][1] + math.sin(ang) * ln * 0.6))
            ws = np.linspace(rng_.uniform(1.6, 3), 0.4, len(pts))
            put(lambda X, Y, pts=pts, ws=ws: sk.path(ribbon([(p[0] - x + X, p[1] - y + Y) for p in pts], ws), (52, 30, 30), 0.6), x, y, 140)
        for _ in range(80):
            x, y = rng_.uniform(0, S_), rng_.uniform(0, S_)
            rx = rng_.uniform(3, 11) if rng_.random() < 0.85 else rng_.uniform(12, 20)
            ry = rx * rng_.uniform(0.5, 0.8)
            cc = np.array([168, 132, 104]) * rng_.uniform(0.75, 1.15)
            sd = int(rng_.integers(1 << 20))

            def peb(X, Y, rx=rx, ry=ry, cc=cc, sd=sd):
                q = blob(X, Y, rx, ry, sd, n=8, jitter=0.2)
                sk.path(q, tuple(cc))
                sk.path(blob(X + rx * 0.15, Y - ry * 0.3, rx * 0.6, ry * 0.45, 7, n=8, jitter=0.1), tuple(np.minimum(cc * 1.3, 255)), 0.8)
                sk.path(q, INK, 0.9, 0, 1.4)
            put(peb, x, y)
        for _ in range(7):       # kemik kırıkları (eski savaşların izi)
            x, y = rng_.uniform(0, S_), rng_.uniform(0, S_)
            a = rng_.uniform(0, math.pi)
            ln = rng_.uniform(14, 28)

            def bone(X, Y, a=a, ln=ln):
                p0 = (X - math.cos(a) * ln / 2, Y - math.sin(a) * ln / 2)
                p1 = (X + math.cos(a) * ln / 2, Y + math.sin(a) * ln / 2)
                sk.path(ribbon([p0, p1], [3.0, 2.4]), (214, 200, 172))
                for p in (p0, p1):
                    sk.c.drawCircle(p[0], p[1], 2.6, sk.paint((214, 200, 172)))
                sk.path(ribbon([p0, p1], [3.0, 2.4]), INK, 0.8, 0, 1.0)
            put(bone, x, y)

    return Z.tile_texture(S, seed + 11, draw, rgb)


def meadow_texture(seed=650, S=512):
    """Kuru altın çayır (zeminin üst 2-3 karosu): sık, rüzgâra yatık ot darbeleri; aralarda çatlak toprak görünür."""
    nz = fbm(S, S, [40, 12], seed + 1)
    base = mix(c01((64, 36, 36)), c01((104, 64, 46)), (0.5 + 0.5 * nz)[..., None])
    cols = [(62, 36, 34), (96, 58, 42), (142, 92, 58), (190, 136, 76), (236, 188, 108), (120, 76, 50)]
    wts = np.array([0.22, 0.24, 0.2, 0.15, 0.05, 0.14])

    def draw(sk, S_, rng, put):
        for _ in range(4200):
            x, y = rng.uniform(0, S_), rng.uniform(0, S_)
            h = rng.uniform(8, 22)
            c = cols[int(rng.choice(len(cols), p=wts / wts.sum()))]
            ln, wd = rng.uniform(-0.1, 0.8), rng.uniform(1.3, 2.6)
            tip = rng.random()

            def g(X, Y, h=h, c=c, ln=ln, wd=wd, tip=tip):
                sk.path(blade(X, Y, h, ln, wd), c, 0.9)
                if tip < 0.16:
                    sk.path(blade_tip(X, Y, h, ln, wd, 0.28), INK, 0.65)
            put(g, x, y)

    return Z.tile_texture(S, seed, draw, base)


# ------------------------------------------------------------------ ön plan
FG_COL = (40, 16, 30)
FG_RIM = (150, 84, 70)


def fg_grass_strip(seed=700, W=3840, Hs=280):
    """Ekranın alt kenarında rüzgârda yatan koyu kılçık otu ve sorguçları, deve dikeni siluetleri (aktörlerin önünde)."""
    rng = np.random.default_rng(seed)
    pad = 160
    sk = Sk(W + 2 * pad, Hs)
    base = Hs - 34
    pts = [(x, base + 18 + 14 * math.sin(x / 160.0 + 1) + rng.uniform(-6, 6)) for x in np.linspace(0, W + 2 * pad, 90)]
    pts += [(W + 2 * pad, Hs + 4), (0, Hs + 4)]
    sk.path(smooth_path(pts, True, 0.3), FG_COL)
    clumps = rng.uniform(0, W, 30)
    for _ in range(int(W * 0.8)):
        if rng.random() < 0.5:
            x = rng.choice(clumps) + rng.normal(0, 46)
            hm = 170
        else:
            x = rng.uniform(0, W)
            hm = 70
        x += pad
        h = rng.uniform(18, hm) * (0.6 + 0.4 * rng.random())
        c = np.array(FG_COL, np.float32) * rng.uniform(0.8, 1.5)
        by, ln, wd = base + rng.uniform(10, 50), rng.uniform(0.05, 0.75), rng.uniform(3.0, 6.0)
        if h > 40 and rng.random() < 0.55:
            sk.path(blade(x + 1.8, by, h, ln, wd, curl=0.5), FG_RIM, 0.6)
        sk.path(blade(x, by, h, ln, wd, curl=0.5), tuple(c), 1.0)
        if h > 90 and rng.random() < 0.5:
            tip = (x + ln * h, by - h)
            pl = rng.uniform(30, 60)
            q = bezier(tip, (tip[0] + pl * 0.6, tip[1] - pl * 0.1), (tip[0] + pl, tip[1] + pl * 0.35), 10)
            sk.path(ribbon(q, np.sin(np.linspace(0.2, math.pi * 0.95, 10)) * 4 + 0.5), FG_RIM, 0.8)
    for _ in range(10):        # deve dikeni siluetleri
        x0 = rng.uniform(0, W) + pad
        y0 = base + 22
        hgt = rng.uniform(90, 150)
        stem = bezier((x0, y0), (x0 + rng.uniform(-8, 8), y0 - hgt * 0.6), (x0 + rng.uniform(-10, 10), y0 - hgt), 12)
        sk.path(ribbon(stem, np.linspace(5, 2.5, 12)), FG_COL)
        for j in range(2, 11, 2):
            q = stem[j]
            for sgn in (-1, 1):
                a = -math.pi / 2 + sgn * rng.uniform(0.8, 1.3)
                ln = rng.uniform(18, 32) * (1 - j / 16)
                p = [(q[0], q[1])] + [(q[0] + math.cos(a) * ln * t, q[1] + math.sin(a) * ln * t + (4 if k % 2 else -3)) for k, t in enumerate((0.35, 0.65, 1.0))]
                sk.path(ribbon(p, [4, 3, 2, 0.4]), FG_COL)
        hx, hy = stem[-1]
        sk.path(blob(hx, hy, 9, 8, int(x0), n=10, jitter=0.15), FG_COL)
        for k in range(11):
            a = -math.pi / 2 + (k - 5) * 0.2
            sk.path(ribbon([(hx, hy - 4), (hx + math.cos(a) * 18, hy - 4 + math.sin(a) * 18)], [3, 1]), FG_COL)
            sk.path(ribbon([(hx + math.cos(a) * 9, hy - 4 + math.sin(a) * 9), (hx + math.cos(a) * 18, hy - 4 + math.sin(a) * 18)], [1.4, 0.6]), FG_RIM, 0.5)
    arr = sk.snap()
    from ink_biyom import fold
    L = Layer(W, Hs)
    L.a = fold(arr, pad, W)
    return L


def chaff_particle():
    """Savrulan kuru ot kırıntısı (parçacık): ince, hafif kıvrık sap."""
    sk = Sk(32, 12)
    sk.path(ribbon([(2, 7), (12, 5), (22, 5.5), (30, 4)], [0.8, 2.0, 1.6, 0.4]), (255, 255, 255))
    sk.path(ribbon([(14, 5), (20, 1), (24, 0.5)], [1.0, 0.8, 0.3]), (220, 220, 220), 0.9)
    return sk.snap()
