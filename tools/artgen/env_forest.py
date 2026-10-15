"""Ötüken Ormanı: 24 px zemin karoları (16 kenar maskesi × varyasyon), çimen üst katmanı,
ahşap platformlar ve oyun katmanı süsleri (dilek ağacı, kam direği, mantarlar...).

Kenar maskesi bitleri (1 = o yönde HAVA var): 1 üst, 2 sağ, 4 alt, 8 sol.
"""
import math
import random
import numpy as np
from raster import Canvas, Mat, ramp
from materials import M

TS = 24
EARTH_DEEP = Mat(ramp(345, 0.32, 0.34, spread=0.35), name='derin toprak')
ROOT = Mat(ramp(28, 0.45, 0.40), name='kök')
TAU = math.tau


def pnoise(x, seed, amp, period=TS):
    """Karo genişliğinde periyodik gürültü: komşu karolar dikişsiz birleşir."""
    s = (np.sin(TAU * x / period + seed) * 1.0 + np.sin(TAU * 2 * x / period + seed * 2.3) * 0.5 + np.sin(TAU * 3 * x / period + seed * 0.7) * 0.3) / 1.8
    return amp * s


def ground_tile(mask, var, deep=False):
    """3x3 bağlamda çiz, ortadaki 24x24 karoyu kes."""
    rng = random.Random(mask * 31 + var * 7 + (100 if deep else 0))
    N = TS * 3
    c = Canvas(N, N)
    up, rt, dn, lf = bool(mask & 1), bool(mask & 2), bool(mask & 4), bool(mask & 8)
    solid = np.zeros((3, 3), bool)
    solid[1, 1] = True
    solid[0, 1], solid[1, 2], solid[2, 1], solid[1, 0] = not up, not rt, not dn, not lf
    solid[0, 0] = solid[0, 1] and solid[1, 0]; solid[0, 2] = solid[0, 1] and solid[1, 2]
    solid[2, 0] = solid[2, 1] and solid[1, 0]; solid[2, 2] = solid[2, 1] and solid[1, 2]
    ys, xs = np.mgrid[0:N, 0:N]
    px, py = xs + 0.5, ys + 0.5
    pm = np.zeros((N, N), bool)
    for j in range(3):
        for i in range(3):
            if solid[j, i]:
                pm[j * TS:(j + 1) * TS, i * TS:(i + 1) * TS] = True
    # organik kenarlar (merkez karonun açık kenarlarında)
    lx = px % TS; ly = py % TS
    if up:
        top = TS - 1.2 - pnoise(lx, 1.0, 1.6) - 0.8
        pm |= (xs >= TS) & (xs < 2 * TS) & (py >= top) & (py < TS + 2)
    if dn:
        bot = 2 * TS + 0.5 + pnoise(lx, 2.0, 1.8)
        pm &= ~((xs >= TS) & (xs < 2 * TS) & (py > bot))
        pm |= (xs >= TS) & (xs < 2 * TS) & (py > 2 * TS - 3) & (py <= bot)
    if lf:
        lft = TS + 0.5 + pnoise(ly, 3.0, 1.4)
        pm &= ~((ys >= TS) & (ys < 2 * TS) & (px < lft) & (px > TS - 3))
    if rt:
        rgt = 2 * TS - 0.5 + pnoise(ly, 4.0, 1.4)
        pm &= ~((ys >= TS) & (ys < 2 * TS) & (px > rgt) & (px < 2 * TS + 3))
    base = EARTH_DEEP if deep else M['earth']
    speck = lambda lu, lv, x, y: (np.sin(x * 2.7 + y * 1.3) * np.sin(y * 3.1 - x * 0.7) > 0.72)
    c.region(pm, base, z=0, bevel=4, slope=0.6, tone=-0.05 if deep else 0.0, paint=[(speck, EARTH_DEEP if not deep else ROOT)])
    if not deep:
        # taşlar ve kökler (karonun içinde)
        for _ in range(rng.randint(1, 3)):
            sx = TS + rng.uniform(4, 20); sy = TS + rng.uniform(9 if up else 3, 21)
            c.ellipse((sx, sy), rng.uniform(1.8, 3.4), rng.uniform(1.4, 2.4), M['rock'], z=4, rot=rng.uniform(0, 3))
        if rng.random() < 0.6:
            y0 = TS + rng.uniform(10, 18)
            pts = [(TS + rng.uniform(0, 6), y0)]
            for k in range(3):
                pts.append((pts[-1][0] + rng.uniform(4, 7), pts[-1][1] + rng.uniform(-2, 2.5)))
            for a, b in zip(pts, pts[1:]):
                c.capsule(a, b, 1.0, 0.7, ROOT, z=3.5)
        # çimen kapağı
        if up:
            gtop = TS - 1.2 - pnoise(lx, 1.0, 1.6) - 0.8
            gm = pm & (py < gtop + 5.5 + pnoise(lx, 5.0, 1.2)) & (xs >= TS - 4) & (xs < 2 * TS + 4)
            if lf:
                gm &= ~((px < TS + 0.5 + pnoise(ly, 3.0, 1.4)))
            blades = lambda lu, lv, x, y: (np.floor(x) % 3 == 0) & (y < gtop + 2.5)
            c.region(gm, M['grass'], z=5, bevel=2, slope=0.5, paint=[(blades, M['grass_hi'])])
            if lf:
                c.capsule((TS + 0.5, TS + 2), (TS + 0.2, TS + 7), 1.2, 0.6, M['grass'], z=7)
            if rt:
                c.capsule((2 * TS - 0.5, TS + 2), (2 * TS - 0.2, TS + 7), 1.2, 0.6, M['grass'], z=7)
    rgba = c.shade(light=(-0.45, -0.8, 0.5), rim_amt=0.0)
    nm = c.normal_map(rgba[..., 3])
    return rgba[TS:2 * TS, TS:2 * TS], nm[TS:2 * TS, TS:2 * TS]


def grass_overlay(var):
    """Çimenli zeminin üstündeki hava karosu: ot tutamları, ara sıra çiçek."""
    rng = random.Random(500 + var)
    c = Canvas(TS, TS, 0, 0)
    for _ in range(rng.randint(5, 9)):
        x = rng.uniform(1, TS - 1); h = rng.uniform(3, 9); lean = rng.uniform(-2.5, 2.5)
        c.capsule((x, TS + 1), (x + lean, TS - h), 0.9, 0.4, M['grass'] if rng.random() < 0.6 else M['grass_hi'], z=rng.uniform(0, 2))
    if var % 3 == 0:
        x = rng.uniform(5, 19); h = rng.uniform(7, 11)
        c.capsule((x, TS + 1), (x + 1, TS - h), 0.5, 0.4, M['leaf'], z=3)
        col = [M['flower_r'], M['flower_y'], M['flower_b']][var // 3 % 3]
        for k in range(5):
            a = k / 5 * TAU
            c.ellipse((x + 1 + math.cos(a) * 1.5, TS - h + math.sin(a) * 1.3), 1.3, 1.1, col, z=5)
        c.dot((x + 1, TS - h), M['flower_y'] if col is not M['flower_y'] else M['flower_r'], z=8)
    rgba = c.shade(rim_amt=0.0)
    return rgba, c.normal_map(rgba[..., 3])


def platform_tile(kind):
    """Ahşap tek yönlü platform: 0 sol uç, 1 orta, 2 sağ uç."""
    c = Canvas(TS, TS, 0, 0)
    grain = lambda lu, lv, x, y: (np.floor(y) == 3) & (np.floor(x) % 7 < 4)
    x0 = 1 if kind == 0 else -1
    x1 = TS - 1 if kind == 2 else TS + 1
    c.poly([(x0, 1), (x1, 1), (x1, 7), (x0, 7)], M['wood'], z=2, bevel=1.5, height=1.5, paint=[(grain, Mat(ramp(22, 0.6, 0.38)))])
    for nx_ in (5, 19):
        c.ellipse((nx_, 4), 0.9, 0.9, M['iron'], z=6)
    if kind in (0, 2):
        bx = 4 if kind == 0 else TS - 4
        c.capsule((bx, 7), (bx + (5 if kind == 0 else -5), 16), 1.2, 1.0, M['wood'], z=1)
        c.capsule((bx, 2), (bx, 0), 0.6, 0.6, M['leather'], z=4)
    rgba = c.shade(rim_amt=0.0)
    return rgba, c.normal_map(rgba[..., 3])


def build_ground_atlas(variations=4):
    """Satır 0..3: 16 maske × 4 varyasyon. Satır 4..5: derin toprak.
    Satır 6: çimen üst katmanı (16 varyasyon). Satır 7: platformlar (sol/orta/sağ ×2)."""
    rows = variations + 2 + 1 + 1
    A = np.zeros((rows * TS, 16 * TS, 4)); Nm = np.zeros_like(A)
    for v in range(variations):
        for m in range(16):
            a, n = ground_tile(m, v)
            A[v * TS:(v + 1) * TS, m * TS:(m + 1) * TS] = a; Nm[v * TS:(v + 1) * TS, m * TS:(m + 1) * TS] = n
    for v in range(2):
        for k in range(16):
            a, n = ground_tile(0, k + v * 16, deep=True)
            r = variations + v
            A[r * TS:(r + 1) * TS, k * TS:(k + 1) * TS] = a; Nm[r * TS:(r + 1) * TS, k * TS:(k + 1) * TS] = n
    r = variations + 2
    for k in range(16):
        a, n = grass_overlay(k)
        A[r * TS:(r + 1) * TS, k * TS:(k + 1) * TS] = a; Nm[r * TS:(r + 1) * TS, k * TS:(k + 1) * TS] = n
    r += 1
    for k in range(6):
        a, n = platform_tile(k % 3)
        A[r * TS:(r + 1) * TS, k * TS:(k + 1) * TS] = a; Nm[r * TS:(r + 1) * TS, k * TS:(k + 1) * TS] = n
    return A, Nm, {'tile': TS, 'cols': 16, 'ground_rows': variations, 'deep_rows': [variations, variations + 1], 'grass_row': variations + 2, 'platform_row': variations + 3}


# ------------------------------------------------------------ süsler (oyun katmanı)
CLOTHS = [M['red_paint'], M['nazar_w'], M['cloth_blue'], M['flower_y'], M['grass_hi'], M['turq']]


def decor_wishtree():
    c = Canvas(96, 120, 48, 116)
    rng = random.Random(3)
    c.capsule((0, 0), (-2, -60), 5.0, 3.4, M['bark'], z=0)
    for x0, y0, x1, y1, r in ((-1, -40, -26, -62, 2.2), (-2, -52, 22, -74, 2.0), (-2, -60, -10, -88, 1.8), (-1, -30, 24, -44, 1.8), (-2, -70, 8, -96, 1.4)):
        c.capsule((x0, y0), (x1, y1), r, r * 0.55, M['bark'], z=1)
        for k in range(rng.randint(3, 5)):
            t = rng.uniform(0.25, 0.95)
            bx, by = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            ln = rng.uniform(5, 11)
            col = rng.choice(CLOTHS)
            c.capsule((bx, by), (bx + rng.uniform(-1.5, 1.5), by + ln), 1.1, 0.9, col, z=4 + k * 0.1)
    for k in range(18):
        a = rng.uniform(0, TAU); r = rng.uniform(4, 22)
        c.ellipse((math.cos(a) * r * 1.2 - 2, -78 + math.sin(a) * r * 0.6), rng.uniform(3, 5.5), rng.uniform(2.4, 4), rng.choice([M['leaf'], M['moss'], M['leaf']]), z=-2 + rng.uniform(0, 2))
    for dx, a in ((-6, -0.7), (6, 0.6)):
        c.capsule((dx * 0.3, -4), (dx + math.sin(a) * 4, 0), 2.4, 1.2, M['bark'], z=0.5)
    return c


def decor_totem():
    """Kam direği: oyma ahşap direk, tepesinde kanat açmış kuş, boyalı yüzler, kurdeleler."""
    c = Canvas(56, 104, 28, 100)
    c.poly([(-5, 0), (5, 0), (4.4, -70), (-4.4, -70)], M['wood'], z=0, bevel=2.4, height=2.5)
    for k, y in enumerate((-12, -32, -52)):
        face = [M['red_paint'], M['turq'], M['flower_y']][k]
        c.poly([(-6, y + 8), (6, y + 8), (6.5, y - 6), (-6.5, y - 6)], M['wood'], z=2, bevel=2, height=2)
        c.capsule((-3.2, y - 1), (-1.0, y - 1), 1.0, 1.0, M['black'], z=8)
        c.capsule((1.0, y - 1), (3.2, y - 1), 1.0, 1.0, M['black'], z=8)
        c.capsule((-4.5, y + 3.5), (4.5, y + 3.5), 1.0, 1.0, face, z=8)
        c.capsule((-6.6, y - 6), (6.6, y - 6), 0.9, 0.9, face, z=7)
    # kuş
    c.ellipse((0, -76), 4.0, 3.2, M['wood'], z=3)
    c.poly([(-2, -78), (-22, -86), (-18, -80), (-24, -78), (-2, -74)], M['wood'], z=2, bevel=1.5, height=1.5, paint=[(lambda lu, lv, x, y: (np.floor(x) % 4 == 0), M['turq'])])
    c.poly([(2, -78), (22, -86), (18, -80), (24, -78), (2, -74)], M['wood'], z=2, bevel=1.5, height=1.5, paint=[(lambda lu, lv, x, y: (np.floor(x) % 4 == 0), M['turq'])])
    c.capsule((1, -79), (5.5, -80), 1.2, 0.5, M['gold'], z=6)
    c.dot((1.6, -78.5), M['black'], z=10)
    for sx in (-5, 5):
        for k in range(3):
            c.capsule((sx, -60 + k * 3), (sx * 1.3, -50 + k * 4), 0.8, 0.7, CLOTHS[(k + (sx > 0) * 3) % 6], z=9)
    return c


def decor_mushrooms(var=0):
    c = Canvas(40, 32, 20, 30)
    rng = random.Random(70 + var)
    for k in range(rng.randint(2, 4)):
        x = rng.uniform(-12, 12); h = rng.uniform(4, 12); r = rng.uniform(2.5, 5.5)
        c.capsule((x, 0), (x + rng.uniform(-1, 1), -h), r * 0.32, r * 0.28, M['bone'], z=k)
        dots = lambda lu, lv, px, py: (np.sin(px * 5.3) * np.sin(py * 4.7) > 0.55) & (lv < 0.2)
        c.ellipse((x, -h), r, r * 0.62, M['amanita'], z=k + 2, paint=[(dots, M['nazar_w'])])
    for k in range(6):
        c.capsule((rng.uniform(-14, 14), 1), (rng.uniform(-15, 15), -rng.uniform(2, 6)), 0.6, 0.4, M['grass_hi'], z=6)
    return c


def decor_flowers(var=0):
    c = Canvas(40, 24, 20, 23)
    rng = random.Random(90 + var)
    cols = [M['flower_r'], M['flower_r'], M['flower_y'], M['flower_b']]
    for k in range(9):
        x = rng.uniform(-16, 16); h = rng.uniform(4, 13)
        c.capsule((x, 1), (x + rng.uniform(-1.5, 1.5), -h), 0.5, 0.4, M['leaf'], z=k * 0.1)
        if rng.random() < 0.7:
            col = rng.choice(cols)
            c.ellipse((x, -h - 1), 2.0, 1.6, col, z=3 + k * 0.1)
            c.dot((x, -h - 1), M['black'] if col is M['flower_r'] else M['flower_y'], z=8)
    return c


def decor_rock(var=0):
    c = Canvas(48, 32, 24, 31)
    rng = random.Random(110 + var)
    c.ellipse((0, -9), 15, 10, M['rock'], z=0, rot=rng.uniform(-0.2, 0.2))
    c.ellipse((rng.uniform(-9, 9), -14), 7, 5, M['rock'], z=3)
    c.ellipse((-4, -16), 6, 2.5, M['moss'], z=8)
    c.ellipse((7, -6), 3.5, 2.2, M['lichen'], z=8)
    return c


def decor_torch():
    """Çıra: direk üstünde yanan reçineli odun (ışık kaynağı)."""
    c = Canvas(24, 64, 12, 62)
    c.capsule((0, 0), (0, -40), 1.8, 1.5, M['wood'], z=0)
    c.capsule((-3, -40), (3, -40), 1.4, 1.4, M['iron'], z=2)
    c.poly([(-3.5, -40), (3.5, -40), (2.5, -46), (-2.5, -46)], M['bark'], z=1, bevel=1.2, height=1)
    fire = Mat(ramp(30, 0.9, 1.0), emissive=1.0, outline='#7a2a04')
    core = Mat(ramp(50, 0.6, 1.0), emissive=1.0, outline='#7a2a04')
    c.poly([(-4, -46), (4, -46), (2, -54), (0.5, -59), (-1, -53), (-2.5, -55)], fire, z=4, bevel=1.5, height=1)
    c.poly([(-2, -46), (2, -46), (0.6, -52), (-0.8, -50)], core, z=6, bevel=1, height=1)
    return c


DECOR = {
    'dilek_agaci': decor_wishtree, 'kam_diregi': decor_totem, 'mantar_1': lambda: decor_mushrooms(0), 'mantar_2': lambda: decor_mushrooms(1),
    'cicek_1': lambda: decor_flowers(0), 'cicek_2': lambda: decor_flowers(1), 'cicek_3': lambda: decor_flowers(2),
    'kaya_1': lambda: decor_rock(0), 'kaya_2': lambda: decor_rock(1), 'cira': decor_torch,
}


# ---- temas kararması (v16): süsün yere değdiği alt bölüm basamaklı olarak kararır (ortam kapanması).
# Kâğıt çıkartması gibi yüzmesin; zemindeki toprak AO'suyla aynı dil: 3 sert bant, titreşim yok.
# Işıyan pikseller (çıra alevi) dokunulmaz. Yükseklik oranla: HD'de aynı mantıksal bant.
CONTACT_AO = ((0.05, 0.6), (0.1, 0.74), (0.17, 0.87))   # (alttan yükseklik payı, renk çarpanı)


def _contact_ao(rgba, emis=None):
    a = rgba[..., 3] > 0
    if not a.any():
        return rgba
    rows = np.where(a.any(1))[0]
    y0, y1 = rows[0], rows[-1]
    hgt = max(1, y1 - y0 + 1)
    yy = np.arange(rgba.shape[0])[:, None]
    d = (y1 - yy) / hgt                                  # 0 = en alt satır
    mul = np.ones(d.shape)
    for frac, k in reversed(CONTACT_AO):
        mul = np.where(d <= frac, k, mul)
    m = a & (mul < 1)
    if emis is not None:
        m &= emis.max(-1) <= 0
    rgba[..., :3] = np.where(m[..., None], rgba[..., :3] * mul.repeat(rgba.shape[1], 1)[..., None], rgba[..., :3])
    return rgba


def _with_contact_ao(fn):
    def run():
        c = fn()
        orig = c.shade

        def shade(*a, **kw):
            out = orig(*a, **kw)
            return _contact_ao(out, getattr(c, 'emis', None))
        c.shade = shade
        return c
    return run


DECOR = {k: _with_contact_ao(f) for k, f in DECOR.items()}
