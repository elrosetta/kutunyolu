"""Ötüken zemini: dünya koordinatında okunan dikişsiz toprak dokusu + anahtar renkli kenar karoları.

Kenar karolarında toprak pikselleri ANAHTAR renklerle boyanır; Godot'daki ground.gdshader bu
pikselleri dünya koordinatından okunan 256x256 toprak dokusuyla değiştirir. Böylece karo tekrarı
görünmez, katmanlar ve kayalar karo sınırlarını aşar. Işık sağ üstten (güneş) gelir.

Kenar maskesi bitleri (1 = o yönde hava): 1 üst, 2 sağ, 4 alt, 8 sol. Varyant v = (x + y) % 3:
üst kenar profili 72 px'te bir tekrarlar, böylece yan yana karolar kesintisiz birleşir.
"""
import math
import random
import numpy as np

from raster import Canvas, Mat, ramp
from pixkit import pal, fbm, vnoise, quantize, shift, normals_from_height, normal_rgba, hexrgb

TS = 24
S = 256
TAU = math.tau
LIGHT = (0.55, -0.7, 0.5)  # sağ üstten

KEY_SOIL = np.array([1.0, 0.0, 1.0])
# Anahtarlar yalnızca 0/1 bileşenli: HDR'de sRGB→doğrusal dönüşümünden etkilenmez.
KEY_SHADE = np.array([0.0, 1.0, 1.0])
KEY_LIT = np.array([1.0, 1.0, 0.0])

# Kararan Ötüken paleti: soğuk, kurşuni-kahve toprak; kurumuş kan rengi kil; kapkara humus;
# solgun, mavimsi çimen; kemik rengi kırıntılar.
SOIL = pal('#100d0d', '#1a1515', '#251e1c', '#312924', '#3d342c', '#4a4035')
CLAY = pal('#181014', '#26171a', '#341e20', '#422727', '#50312d', '#5e3b34')
HUMUS = pal('#0c090b', '#130f11', '#1a1517', '#221b1c', '#2a2221', '#332927')
GRASS = pal('#0a1913', '#10251b', '#173223', '#1f422b', '#2a5435', '#386941', '#4d7f4f')
ROOT = pal('#1e1512', '#2e211a', '#413022', '#543f2c')
SPECK = pal('#6f6a5c', '#4f5761', '#8b8474')

ROCK_MATS = [
    Mat(ramp(222, 0.12, 0.40, spread=0.5), outline='#0f0b0d', name='gri taş'),
    Mat(ramp(20, 0.18, 0.36, spread=0.5), outline='#0f0b0d', name='sıcak taş'),
    Mat(ramp(232, 0.16, 0.30, spread=0.5), outline='#0b080a', name='çakmak taşı'),
    Mat(ramp(275, 0.20, 0.42, spread=0.5), outline='#0f0b0d', name='mor taş'),
]
ROOT_MAT = Mat(ramp(25, 0.36, 0.38, spread=0.45), outline='#0f0b0d', name='kök')


def set_biome(cfg):
    """Toprak paletlerini biyom tanımıyla değiştir (biomes.BIOMES[id]['soil'])."""
    global SOIL, CLAY, HUMUS, GRASS, ROOT, SPECK, WOOD, ROCK_MATS, ROOT_MAT
    SOIL, CLAY, HUMUS, GRASS, ROOT, SPECK, WOOD = cfg['SOIL'], cfg['CLAY'], cfg['HUMUS'], cfg['GRASS'], cfg['ROOT'], cfg['SPECK'], cfg['WOOD']
    ol = cfg.get('OUTLINE', '#0f0b0d')
    ROCK_MATS = [Mat(ramp(h, s, v, spread=0.5), outline=ol, name='taş') for (h, s, v) in cfg['ROCK']]
    rh, rs, rv = cfg['ROOT_MAT']
    ROOT_MAT = Mat(ramp(rh, rs, rv, spread=0.45), outline=ol, name='kök')


# ------------------------------------------------------------------ toprak dokusu
def soil_texture(seed=7):
    rng = np.random.default_rng(seed)
    pyr = random.Random(seed)
    n = fbm(S, S, [64, 32, 16], [0.5, 0.32, 0.18], rng)
    # katmanlar: y yönünde 3 dalga (dikişsiz); kalınlık ve faz gürültüyle değişir
    yy = np.arange(S)[:, None]
    phase = fbm(S, S, [128, 64], [0.7, 0.3], rng) * 3.4
    thick = fbm(S, S, [64], [1.0], rng)
    st = np.sin(TAU * 3 * yy / S + phase)
    clay = st > 0.55 + thick * 0.2
    humus = st < -0.72 + thick * 0.15
    # temel ton: geniş ölçekli 3 kademe (2..4)
    th = np.percentile(n, [30, 72])
    lvl = 2 + np.digitize(n, th)
    hgt = n * 2.0
    # topaklar: sağ üstü aydınlık, sol altı gölgeli küçük kesekler (piksel sanatçının toprak tekniği)
    lvl_f = lvl.astype(float)
    order = list(range(1400))
    pyr.shuffle(order)
    for _ in order:
        cx, cy = pyr.uniform(0, S), pyr.uniform(0, S)
        r = pyr.choice([1.4, 1.8, 2.2, 2.6, 3.0, 3.6])
        base = int(lvl[int(cy) % S, int(cx) % S])
        delta = pyr.choice([0, 0, 0, 1, -1])
        R = int(math.ceil(r)) + 1
        for dy in range(-R, R + 1):
            for dx in range(-R, R + 1):
                d2 = dx * dx + dy * dy * 1.25
                if d2 > r * r:
                    continue
                x, y = int(cx + dx) % S, int(cy + dy) % S
                edge = d2 > (r - 1.0) ** 2
                v = base + delta
                if edge and dx - dy > 0:
                    v += 1          # sağ üst kenar: ışık
                elif edge and dx - dy < -1:
                    v -= 1          # sol alt kenar: gölge
                lvl_f[y, x] = v
                hgt[y, x] = 2.0 + (r * r - d2) ** 0.5 * 0.5
    lvl = np.clip(lvl_f.astype(int), 0, 5)
    rgb = SOIL[lvl].copy()
    rgb[clay] = CLAY[lvl[clay]]
    rgb[humus] = HUMUS[np.clip(lvl[humus] + 1, 0, 5)]
    # kum / kabuk kırıntıları (küçük kümeler)
    for _ in range(140):
        x, y = pyr.randrange(S), pyr.randrange(S)
        c = SPECK[pyr.choice([0, 0, 1, 2])]
        for dx, dy in [(0, 0)] + ([(1, 0)] if pyr.random() < 0.5 else []) + ([(0, 1)] if pyr.random() < 0.3 else []):
            rgb[(y + dy) % S, (x + dx) % S] = c
    # çatlaklar
    for _ in range(10):
        x, y = pyr.uniform(0, S), pyr.uniform(0, S)
        a = pyr.uniform(0, TAU)
        for k in range(pyr.randint(5, 12)):
            a += pyr.uniform(-0.6, 0.6)
            x += math.cos(a); y += math.sin(a)
            rgb[int(y) % S, int(x) % S] = SOIL[0]
            hgt[int(y) % S, int(x) % S] -= 1.5
    # taşlar ve kökler: cel gölgeli, dikişsiz (kenardan taşanlar karşı kenara da çizilir)
    c = Canvas(S, S)

    def wrapped(fn, x, y, r):
        for ox in (-S, 0, S):
            for oy in (-S, 0, S):
                if -r - 2 <= x + ox <= S + r + 2 and -r - 2 <= y + oy <= S + r + 2:
                    fn(x + ox, y + oy)

    placed = []
    for count, rmin, rmax in ((7, 5.0, 9.0), (30, 2.4, 4.2), (120, 1.0, 2.1)):
        for _ in range(count):
            for _try in range(30):
                x, y = pyr.uniform(0, S), pyr.uniform(0, S)
                r = pyr.uniform(rmin, rmax)
                ok = all(min(abs(x - px), S - abs(x - px)) ** 2 + min(abs(y - py), S - abs(y - py)) ** 2 > (r + pr + 1.5) ** 2 for px, py, pr in placed)
                if ok:
                    placed.append((x, y, r))
                    mat = pyr.choice(ROCK_MATS)
                    rx, ry, rot = r * pyr.uniform(0.9, 1.35), r * pyr.uniform(0.65, 0.95), pyr.uniform(-0.6, 0.6)
                    if r > 4.5:
                        k = pyr.randint(6, 8)
                        pts = [(math.cos(i / k * TAU + pyr.uniform(-0.2, 0.2)) * rx * pyr.uniform(0.85, 1.1), math.sin(i / k * TAU) * ry * pyr.uniform(0.85, 1.1)) for i in range(k)]
                        wrapped(lambda X, Y, pts=pts, mat=mat, r=r: c.poly([(X + px, Y + py) for px, py in pts], mat, z=2, bevel=r * 0.55, height=r * 0.6), x, y, r)
                    else:
                        wrapped(lambda X, Y, rx=rx, ry=ry, rot=rot, mat=mat: c.ellipse((X, Y), rx, ry, mat, z=2, rot=rot, flat=0.25), x, y, r)
                    break
    # kökler: yukarıdan aşağı kıvrılan, dallanan
    for _ in range(7):
        x, y = pyr.uniform(0, S), pyr.uniform(0, S)
        a = math.pi / 2 + pyr.uniform(-0.6, 0.6)
        rr_ = pyr.uniform(0.9, 1.3)
        for seg in range(pyr.randint(14, 26)):
            a += pyr.uniform(-0.35, 0.35)
            nx, ny = x + math.cos(a) * 3.0, y + math.sin(a) * 3.0
            wrapped(lambda X, Y, nx=nx - x, ny=ny - y, rr_=rr_: c.capsule((X, Y), (X + nx, Y + ny), rr_, rr_ * 0.92, ROOT_MAT, z=1), x, y, 4)
            if pyr.random() < 0.18:
                ba = a + pyr.choice([-1, 1]) * pyr.uniform(0.6, 1.1)
                bx, by = x, y
                for k in range(pyr.randint(2, 4)):
                    nbx, nby = bx + math.cos(ba) * 2.6, by + math.sin(ba) * 2.6
                    wrapped(lambda X, Y, dx=nbx - bx, dy=nby - by: c.capsule((X, Y), (X + dx, Y + dy), 0.55, 0.5, ROOT_MAT, z=1), bx, by, 4)
                    bx, by = nbx, nby
                    ba += pyr.uniform(-0.4, 0.4)
            x, y = nx % S, ny % S
            rr_ = max(0.55, rr_ * 0.97)
    rocks = c.shade(light=LIGHT, rim_amt=0.0, outline_mul=0.5)
    ra = rocks[..., 3] > 0
    # gömülme gölgesi: taşların sol altında toprak koyulaşır
    sock = shift(ra, 1, -1) & ~ra
    sock2 = shift(ra, 2, -2) & ~ra & ~sock
    rgb[sock] = rgb[sock] * 0.62
    rgb[sock2] = rgb[sock2] * 0.82
    rgb[ra] = rocks[ra, :3]
    nrm = normals_from_height(hgt, 0.9)
    nrm[ra] = c.n[ra]
    nrm[c.outline_mask & ~ra] = [0, 0, 1]
    return rgb, normal_rgba(nrm)


# ------------------------------------------------------------------ kenar karoları
def _hash(*a):
    h = 0
    for v in a:
        h = (h * 1000003 + int(v) * 7919 + 12345) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0x5bd1e995) & 0xFFFFFFFF
    return (h ^ (h >> 15)) / 4294967295.0


def top_y(u):
    """Çimenli üst kenarın toprak sınırı (karo üstünden aşağı px), 72 px'te bir tekrarlar."""
    return 2.0 + 1.1 * math.sin(TAU * u / 72 + 0.7) + 0.6 * math.sin(TAU * 3 * u / 72 + 2.1) + (_hash(u, 1) - 0.5) * 0.8


def cap_h(u):
    return 5.0 + 1.3 * math.sin(TAU * 2 * u / 72 + 1.3) + (_hash(u, 2) - 0.5) * 1.6


def blade_h(u):
    r = _hash(u, 3)
    return 0 if r < 0.35 else (1 if r < 0.62 else (2 if r < 0.82 else (3 if r < 0.94 else 4)))


def side_x(v):
    return 1.3 + 0.9 * math.sin(TAU * v / 72 + 0.4) + 0.5 * math.sin(TAU * 4 * v / 72 + 1.1) + (_hash(v, 4) - 0.5) * 0.9


def bottom_y(u):
    return 1.6 + 1.0 * math.sin(TAU * u / 72 + 2.4) + (_hash(u, 5) - 0.5) * 1.2


def ground_tile(mask, var):
    up, rt, dn, lf = bool(mask & 1), bool(mask & 2), bool(mask & 4), bool(mask & 8)
    rgba = np.zeros((TS, TS, 4))
    hgt = np.zeros((TS, TS))
    kind = np.zeros((TS, TS), int)  # 0 hava, 1 toprak, 2 gölge, 3 ışık, 4 renkli
    col = np.zeros((TS, TS, 3))
    for ly in range(TS):
        for lx in range(TS):
            u = var * TS + lx
            v = var * TS + ly
            solid = True
            if up and ly < top_y(u):
                solid = False
            if dn and ly > TS - 1 - bottom_y(u):
                solid = False
            if lf and lx < side_x(v):
                solid = False
            if rt and lx > TS - 1 - side_x(v + 37):
                solid = False
            # dış köşe yuvarlatma
            for cx, cy, on in ((0, 0, up and lf), (TS - 1, 0, up and rt), (0, TS - 1, dn and lf), (TS - 1, TS - 1, dn and rt)):
                if on and (lx - cx) ** 2 + (ly - cy) ** 2 < 4.5 ** 2 and abs(lx - cx) < 4.5 and abs(ly - cy) < 4.5:
                    d = math.hypot(lx - (cx + (4.5 if cx == 0 else -4.5)), ly - (cy + (4.5 if cy == 0 else -4.5)))
                    if d > 4.5:
                        solid = False
            if solid:
                kind[ly, lx] = 1
    # kenar bantları
    for ly in range(TS):
        for lx in range(TS):
            if kind[ly, lx] == 0:
                continue
            u = var * TS + lx
            v = var * TS + ly
            if lf and lx < side_x(v) + 2.2:
                kind[ly, lx] = 2
            if rt and lx > TS - 1 - side_x(v + 37) - 2.2:
                kind[ly, lx] = 3
            if dn and ly > TS - 1 - bottom_y(u) - 3.0:
                kind[ly, lx] = 2
    # çimen kapağı
    if up:
        for lx in range(TS):
            u = var * TS + lx
            ty = top_y(u)
            ch = cap_h(u)
            bh = blade_h(u)
            for ly in range(TS):
                if ly >= ty - bh and ly < ty + ch:
                    inside_side = not (lf and lx < side_x(var * TS + ly) - 0.5) and not (rt and lx > TS - 1 - side_x(var * TS + ly + 37) + 0.5)
                    if not inside_side:
                        continue
                    t = (ly - (ty - bh)) / max(1.0, ch + bh)
                    if ly < ty:
                        level = 6 if (_hash(u, ly, 9) < 0.5 or blade_h(u + 1) < bh) else 5
                    else:
                        level = int(np.clip(5 - t * 5.2 + (_hash(u, 7) - 0.5) * 1.3, 1, 5))
                        if (lx + int(_hash(u, 8) * 3)) % 4 == 0 and level > 1:
                            level -= 1
                    kind[ly, lx] = 4
                    col[ly, lx] = GRASS[level]
                    hgt[ly, lx] = 3.0 - t * 2.0
            # kapağın altında gölge bandı ve sarkan otlar/kökçükler
            for ly in range(int(ty + ch), min(TS, int(ty + ch) + 3)):
                if kind[ly, lx] in (1, 3):
                    kind[ly, lx] = 2
            if _hash(u, 11) < 0.22:
                y0 = int(ty + ch)
                for k in range(int(1 + _hash(u, 12) * 3)):
                    if y0 + k < TS and kind[y0 + k, lx] != 0:
                        kind[y0 + k, lx] = 4
                        col[y0 + k, lx] = GRASS[1] if k == 0 else ROOT[1]
        # köşelerde çimen yanlara kıvrılsın
        for side, on in (('l', lf), ('r', rt)):
            if not on:
                continue
            for ly in range(TS):
                depth = int(top_y(var * TS + (0 if side == 'l' else TS - 1)) + cap_h(var * TS) + 4)
                if ly > depth:
                    break
                for k in range(2):
                    lx = int(math.ceil(side_x(var * TS + ly))) + k if side == 'l' else int(TS - 1 - side_x(var * TS + ly + 37)) - k
                    if 0 <= lx < TS and kind[ly, lx] != 0 and kind[ly, lx] != 4:
                        kind[ly, lx] = 4
                        col[ly, lx] = GRASS[3 if side == 'r' else 2] if k == 0 else GRASS[2]
    # tavan: sarkan kökler
    if dn:
        for lx in range(TS):
            u = var * TS + lx
            if _hash(u, 21) < 0.2:
                y0 = int(TS - 1 - bottom_y(u))
                ln = int(2 + _hash(u, 22) * 6)
                for k in range(ln):
                    yy = y0 + k
                    if 0 <= yy < TS:
                        kind[yy, lx] = 4
                        col[yy, lx] = ROOT[2] if k < ln - 1 else ROOT[3]
    # yan yüzlerde çıkıntı taşları
    rng = random.Random(mask * 13 + var)
    for side, on in (('l', lf), ('r', rt)):
        if on and rng.random() < 0.8:
            sy = rng.randint(8, 19)
            sx0 = int(side_x(var * TS + sy)) if side == 'l' else int(TS - 1 - side_x(var * TS + sy + 37))
            rad = rng.uniform(1.6, 2.6)
            for yy in range(TS):
                for xx in range(TS):
                    if (xx - sx0) ** 2 + (yy - sy) ** 2 <= rad * rad:
                        lit_px = (xx - sx0) + -(yy - sy) > 0
                        kind[yy, xx] = 4
                        col[yy, xx] = hexrgb('#5c6472') if lit_px else hexrgb('#353b47')
                        hgt[yy, xx] = 2.0
    # renklendir
    rgba[kind == 1, :3] = KEY_SOIL
    rgba[kind == 2, :3] = KEY_SHADE
    rgba[kind == 3, :3] = KEY_LIT
    rgba[kind == 4, :3] = col[kind == 4]
    rgba[kind > 0, 3] = 1.0
    nrm = normals_from_height(hgt, 0.8, wrap=False)
    nm = normal_rgba(nrm, (kind > 0).astype(float))
    return rgba, nm


def grass_overlay(var):
    rng = random.Random(900 + var)
    rgba = np.zeros((TS, TS, 4))
    hgt = np.zeros((TS, TS))
    x = 0
    while x < TS:
        if rng.random() < 0.55:
            h = rng.randint(2, 7) + (rng.randint(3, 8) if rng.random() < 0.2 else 0)
            lean = rng.choice([-1, 0, 0, 1])
            for k in range(h):
                yy = TS - 1 - k
                xx = x + (lean if k > h * 0.6 else 0)
                if 0 <= xx < TS and 0 <= yy < TS:
                    t = k / max(1, h - 1)
                    lvl = 2 + int(t * 3.6)
                    if k == h - 1:
                        lvl = 6 if lean >= 0 else 5
                    rgba[yy, xx, :3] = GRASS[min(6, lvl)]
                    rgba[yy, xx, 3] = 1
        x += 1
    if var % 3 == 0:
        fx = rng.randint(5, 18)
        fh = rng.randint(8, 13)
        for k in range(fh):
            rgba[TS - 1 - k, fx, :3] = GRASS[2]
            rgba[TS - 1 - k, fx, 3] = 1
        # çiçek yerine solgun mantar / kurumuş tohum başı
        petal = [hexrgb('#8fa69c'), hexrgb('#7f8ca0'), hexrgb('#a3a08a'), hexrgb('#6e7d86')][var // 3 % 4]
        dark = petal * 0.6
        cy = TS - 1 - fh
        for dx, dy, c in ((-1, 0, petal), (1, 0, petal * 1.1), (0, -1, petal * 1.15), (0, 1, dark), (0, 0, hexrgb('#1a1412') if var % 2 else hexrgb('#c9d3c6'))):
            if 0 <= cy + dy < TS:
                rgba[cy + dy, fx + dx, :3] = np.clip(c, 0, 1)
                rgba[cy + dy, fx + dx, 3] = 1
        rgba[TS - 4, fx + 1, :3] = GRASS[4]; rgba[TS - 4, fx + 1, 3] = 1
        rgba[TS - 6, fx - 1, :3] = GRASS[3]; rgba[TS - 6, fx - 1, 3] = 1
    nm = normal_rgba(normals_from_height(hgt, 1.0, wrap=False), rgba[..., 3])
    return rgba, nm


def ceiling_overlay(var):
    rng = random.Random(950 + var)
    rgba = np.zeros((TS, TS, 4))
    for _ in range(rng.randint(2, 4)):
        x = rng.randint(1, TS - 2)
        ln = rng.randint(4, 16)
        moss = rng.random() < 0.4
        for k in range(ln):
            xx = x + (1 if k > ln * 0.5 and rng.random() < 0.3 else 0)
            c = (GRASS[2] if k % 3 else GRASS[3]) if moss else (ROOT[2] if k < ln - 1 else ROOT[3])
            rgba[k, min(TS - 1, xx), :3] = c
            rgba[k, min(TS - 1, xx), 3] = 1
    return rgba, normal_rgba(np.dstack([np.zeros((TS, TS)), np.zeros((TS, TS)), np.ones((TS, TS))]), rgba[..., 3])


WOOD = pal('#15100c', '#221a12', '#312619', '#413321', '#52412b', '#645036')


def platform_tile(kind, var):
    """Ahşap tek yönlü platform: kind 0 sol uç, 1 orta, 2 sağ uç."""
    rng = random.Random(70 + kind * 5 + var)
    rgba = np.zeros((TS, TS, 4))
    x0 = 1 if kind == 0 else 0
    x1 = TS - 2 if kind == 2 else TS - 1
    for y in range(0, 7):
        for x in range(x0, x1 + 1):
            if y == 0:
                lvl = 5 if x % 7 != 3 else 4
            elif y == 6:
                lvl = 0
            elif y == 5:
                lvl = 1
            else:
                g = math.sin((x + var * 24) * 0.45 + y * 1.7) + (_hash(x + var * 24, y) - 0.5) * 0.8
                lvl = 3 if g > 0.6 else (2 if g > -0.4 else 3)
            if (x + var * 24) % 12 == 0 and 0 < y < 6:
                lvl = 1
            rgba[y, x, :3] = WOOD[lvl]
            rgba[y, x, 3] = 1
    for nx in (5, 17):
        if x0 <= nx <= x1:
            rgba[3, nx, :3] = hexrgb('#59616c'); rgba[2, nx, :3] = hexrgb('#8a929c')
    if rng.random() < 0.5:
        mx = rng.randint(3, 18)
        for k in range(rng.randint(3, 6)):
            if x0 <= mx + k <= x1:
                rgba[0, mx + k, :3] = GRASS[4 if k % 2 else 3]
    if kind in (0, 2):
        bx = 4 if kind == 0 else TS - 5
        d = 1 if kind == 0 else -1
        for k in range(10):
            yy, xx = 7 + k, bx + d * int(k * 0.55)
            if 0 <= yy < TS and 0 <= xx < TS:
                rgba[yy, xx, :3] = WOOD[2] if k % 3 else WOOD[1]; rgba[yy, xx, 3] = 1
                if 0 <= xx + d < TS:
                    rgba[yy, xx + d, :3] = WOOD[1]; rgba[yy, xx + d, 3] = 1
        for k in range(4):
            rgba[1 + k, bx, :3] = hexrgb('#6e6248') if k % 2 else hexrgb('#4a4232')
    return rgba, normal_rgba(np.dstack([np.zeros((TS, TS)), np.zeros((TS, TS)) - 0.0, np.ones((TS, TS))]), rgba[..., 3])


def build_ground_atlas():
    rows = 5
    A = np.zeros((rows * TS, 16 * TS, 4)); N = np.zeros_like(A)

    def put(r, c, img):
        a, n = img
        A[r * TS:(r + 1) * TS, c * TS:(c + 1) * TS] = a
        N[r * TS:(r + 1) * TS, c * TS:(c + 1) * TS] = n

    for v in range(3):
        for m in range(16):
            put(v, m, ground_tile(m, v))
    for k in range(8):
        put(3, k, grass_overlay(k))
    for k in range(3):
        put(3, 8 + k, ceiling_overlay(k))
    for k in range(6):
        put(4, k, platform_tile(k % 3, k // 3))
    meta = {'tile': TS, 'cols': 16, 'ground_rows': 3, 'overlay_row': 3, 'grass_cols': 8, 'ceiling_cols': [8, 9, 10], 'platform_row': 4,
            'keys': {'soil': list(KEY_SOIL), 'shade': list(KEY_SHADE), 'lit': list(KEY_LIT)}, 'soil_size': S}
    return A, N, meta
