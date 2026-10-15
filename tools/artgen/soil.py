"""Zemin: dünya koordinatında okunan dikişsiz toprak dokusu + anahtar renkli kenar karoları (1.5x yoğunluk).

Yoğunluk: dünya ölçüsü TS_WORLD = 24 px'tir; dokular 1.5 kat yoğun üretilir (karo hücresi 36 px, toprak
dokusu 384x384 = 256 dünya pikseli). Oyun karo katmanlarını 2/3 ölçekler ve ground.gdshader toprağı
dünya_konumu * 1.5 ile okur; 1080p'de her doku pikseli 2x2 ekran pikseline düşer, iki ızgara örtüşür.

Kenar karolarında toprak pikselleri ANAHTAR renklerle boyanır; ground.gdshader bunları toprak dokusuyla
değiştirir (karo tekrarı görünmez; katmanlar, kayalar, kökler karo sınırlarını aşar):
  macenta = toprak, camgöbeği = gölge bandı, sarı = ışık bandı, mavi = koyu kenar çizgisi,
  kırmızı = ışıyan piksel (lav / kristal; rengi biyomdan gelir).
Işık sağ üstten gelir. Kenar maskesi bitleri (1 = o yönde hava): 1 üst, 2 sağ, 4 alt, 8 sol.
Varyant v = (x + y) % 3: kenar profilleri P = 3 * TS pikselde bir tekrarlar, komşu karolar kesintisiz birleşir.
"""
import math
import random
import numpy as np

import hdkit as hk
from hdkit import ShapeCanvas, hramp, fbm, ridged, bayer, roll, normals_from_height, normal_rgba
from pixkit import pal, hexrgb

TS_WORLD = 24
DENSITY = 1.5
TS = int(TS_WORLD * DENSITY)   # 36
S = 768                         # toprak dokusu (512 dünya pikseli; tekrar ekranda zor seçilir)
AF = (S / 384.0) ** 2           # alan çarpanı: yoğunluklar 384'lük dokuya göre ayarlandı
P = 3 * TS
TAU = math.tau
LIGHT = hk.LIGHT

KEY_SOIL = np.array([1.0, 0.0, 1.0])
KEY_SHADE = np.array([0.0, 1.0, 1.0])
KEY_LIT = np.array([1.0, 1.0, 0.0])
KEY_EDGE = np.array([0.0, 0.0, 1.0])
KEY_GLOW = np.array([1.0, 0.0, 0.0])

# set_biome ile değişen paletler (varsayılan: Ötüken)
SOIL = CLAY = HUMUS = GRASS = ROOT = SPECK = WOOD = None
ROCK = []
ROOT_HSV = (25, 0.36, 0.38)
OUTLINE = hexrgb('#0f0b0d')
STYLE = {}


def set_biome(cfg):
    """Toprak paletlerini biyom tanımıyla değiştir (biomes.BIOMES[id]['soil'])."""
    global SOIL, CLAY, HUMUS, GRASS, ROOT, SPECK, WOOD, ROCK, ROOT_HSV, OUTLINE, STYLE
    SOIL, CLAY, HUMUS, GRASS, ROOT, SPECK, WOOD = (np.asarray(cfg[k], float) for k in ('SOIL', 'CLAY', 'HUMUS', 'GRASS', 'ROOT', 'SPECK', 'WOOD'))
    ROCK = list(cfg['ROCK'])
    ROOT_HSV = cfg['ROOT_MAT']
    OUTLINE = hexrgb(cfg.get('OUTLINE', '#0f0b0d'))
    STYLE = dict(cfg.get('STYLE', {}))
    STYLE.setdefault('cap', 'grass')
    STYLE.setdefault('bands', [('soil', 3), ('clay', 1), ('soil', 2), ('humus', 1)])
    STYLE.setdefault('roots', 8); STYLE.setdefault('bones', 0); STYLE.setdefault('cracks', 8)
    STYLE.setdefault('extra', None); STYLE.setdefault('ceil', 'roots'); STYLE.setdefault('glow', None)


def _rock_mat(cv, i, spec=0.0):
    h, s, v = ROCK[i % len(ROCK)]
    rp = hramp(h, s, v, n=6, lo=0.34, hi=1.35)
    return cv.add_mat(rp, outline=np.minimum(rp[0] * 0.7, OUTLINE * 0.5 + rp[0] * 0.5), spec=spec)


def _hash(*a):
    h = 0
    for v in a:
        h = (h * 1000003 + int(v) * 7919 + 12345) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0x5bd1e995) & 0xFFFFFFFF
    return (h ^ (h >> 15)) / 4294967295.0


def _wdist(ax, ay, bx, by):
    dx = abs(ax - bx); dy = abs(ay - by)
    return math.hypot(min(dx, S - dx), min(dy, S - dy))


# ------------------------------------------------------------------ toprak dokusu
def soil_texture(seed=7):
    """(rgb, normal_rgba, emis_rgb | None) — 384x384, her iki yönde dikişsiz."""
    st = STYLE
    rng = np.random.default_rng(seed)
    pr = random.Random(seed)
    yy, xx = np.mgrid[0:S, 0:S]
    b = bayer(S, S)
    # ---- katmanlar (strata): dalgalı, kalınlığı değişen bantlar
    warp = fbm(S, S, [384, 192, 96, 48], rng)
    warp2 = fbm(S, S, [32, 16, 8], rng)
    phase = (yy / 384.0 + (warp - 0.5) * 0.4 + (warp2 - 0.5) * 0.02) % 1.0   # 384 px'lik katman dizisi, S'de tam sayı kez tekrarlar
    kinds = [k for k, _ in st['bands']]
    th = np.array([t for _, t in st['bands']], float)
    cum = np.cumsum(th) / th.sum()
    start = np.concatenate([[0.0], cum[:-1]])
    bi = np.clip(np.searchsorted(cum, phase, side='right'), 0, len(kinds) - 1)
    t_in = (phase - start[bi]) / (th[bi] / th.sum())
    # ---- tane: küçük kümeler (2-3 px) + ince kum
    grain = fbm(S, S, [24, 12, 6, 3, 2], rng, gain=0.72)
    fine = rng.random((S, S))
    val = 0.5 + (grain - 0.5) * 1.5 + (fine - 0.5) * 0.10
    val += (0.45 - t_in) * 0.22               # bandın üstü ışık alır
    # katman sınırı: ince koyu dikiş + altında açık dudak
    bnd = bi != roll(bi, 1, 0)
    val[bnd] -= 0.42
    val[roll(bnd, 1, 0) & ~bnd] += 0.14
    # kil ve kumda ince laminasyon çizgileri
    lam_kind = np.isin(np.array(kinds)[bi], ['clay', 'sand'])
    lam = ((phase * 384 / 5.0 + warp2 * 1.6) % 1.0) < 0.2
    val[lam & lam_kind] -= 0.16
    # kumda çapraz katmanlanma (eğik ince çizgiler)
    sand = np.array(kinds)[bi] == 'sand'
    cross = (((xx * 0.42 + yy) / 7.0 + warp * 4) % 1.0) < 0.12
    val[sand & cross & (fine > 0.3)] -= 0.1
    lvl = np.clip(np.floor(val * 4.0 + 0.9 + (b - 0.5) * 0.85), 0, 5).astype(int)
    rgb = np.zeros((S, S, 3))
    pals = {'soil': SOIL, 'clay': CLAY, 'humus': HUMUS, 'gravel': SOIL,
            'sand': np.vstack([SOIL[1:], np.minimum(1, SOIL[-1] * 1.1 + 0.03)])}
    for i, k in enumerate(kinds):
        m = bi == i
        Pk = pals.get(k, SOIL)
        rgb[m] = Pk[lvl[m]]
    hgt = (grain - 0.5) * 1.6
    # mikro tane: tek tük bir ton açık/koyu pikseller ve 2'li kırıntılar (gevrek doku)
    mic = rng.random((S, S))
    for i, k in enumerate(kinds):
        m = bi == i
        Pk = pals.get(k, SOIL)
        up_ = m & (mic < 0.018)
        dn_ = m & (mic > 0.975)
        rgb[up_] = Pk[np.clip(lvl[up_] + 1, 0, 5)]
        rgb[dn_] = Pk[np.clip(lvl[dn_] - 1, 0, 5)]
        dn2 = roll(dn_, 0, 1) & m
        rgb[dn2] = Pk[np.clip(lvl[dn2] - 1, 0, 5)]
    # ---- kesekler: sağ üstü aydınlık küçük topaklar (seyrek, yalnız toprak/humus bantlarında)
    for _ in range(int(1500 * AF)):
        cx, cy = pr.uniform(0, S), pr.uniform(0, S)
        kk = kinds[bi[int(cy) % S, int(cx) % S]]
        if kk not in ('soil', 'humus', 'gravel'):
            continue
        r = pr.choice([1.3, 1.6, 2.0, 2.4])
        R = int(math.ceil(r)) + 1
        base = lvl[int(cy) % S, int(cx) % S]
        Pk = pals[kk]
        for dy in range(-R, R + 1):
            for dx in range(-R, R + 1):
                d2 = dx * dx + dy * dy * 1.3
                if d2 > r * r:
                    continue
                x, y = int(cx + dx) % S, int(cy + dy) % S
                edge = d2 > (r - 1.0) ** 2
                v = base
                if edge and dx - dy > 0:
                    v += 1
                elif edge and dx - dy < -1:
                    v -= 1
                rgb[y, x] = Pk[int(np.clip(v, 0, 5))]
                hgt[y, x] = 1.0 + (r * r - d2) ** 0.5 * 0.4
    # ---- çatlaklar: koyu oyuk + alt duvarında ışık
    for _ in range(int(st['cracks'] * AF)):
        x, y = pr.uniform(0, S), pr.uniform(0, S)
        a = pr.uniform(0, TAU)
        for _k in range(pr.randint(8, 26)):
            a += pr.uniform(-0.55, 0.55)
            x += math.cos(a); y += math.sin(a)
            X, Y = int(x) % S, int(y) % S
            rgb[Y, X] = SOIL[0] * 0.85
            hgt[Y, X] -= 1.5
            Y2 = (Y + 1) % S
            if (rgb[Y2, X] != SOIL[0] * 0.85).any():
                rgb[Y2, X] = np.minimum(1, rgb[Y2, X] * 1.18 + 0.02)
            if pr.random() < 0.08:
                a += pr.choice([-1, 1]) * 1.1
    # ---- şekiller: kayalar, çakıllar, kökler, kemikler, kristaller
    cv = ShapeCanvas(S, S, wrap=True)
    spec = 0.6 if st['extra'] in ('crystal', 'lava') else 0.0
    rmats = [_rock_mat(cv, i, spec) for i in range(len(ROCK))]
    placed = []

    def free(x, y, r, pad=1.5):
        return all(_wdist(x, y, px, py) > r + pr_ + pad for px, py, pr_ in placed)

    nb = 0
    for count, rmin, rmax, facet in ((4, 9.0, 14.0, True), (16, 5.0, 8.0, True), (90, 2.6, 4.4, False), (380, 1.1, 2.2, False)):
        for _ in range(int(count * AF)):
            for _try in range(40):
                x, y = pr.uniform(0, S), pr.uniform(0, S)
                r = pr.uniform(rmin, rmax)
                if not free(x, y, r):
                    continue
                placed.append((x, y, r))
                mat = pr.choice(rmats)
                rx, ry = r * pr.uniform(1.0, 1.4), r * pr.uniform(0.6, 0.92)
                rot = pr.uniform(-0.5, 0.5)
                cv.blob(x, y, rx, ry, mat, z=2 + r * 0.1, rot=rot, rough=0.18 if facet else 0.1, rng=rng,
                        facets=pr.randint(5, 8) if facet else (4 if r > 2.4 and pr.random() < 0.5 else 0), flat=0.4)
                break
    # çakıl bantlarında yoğun çakıl
    gi = [i for i, k in enumerate(kinds) if k == 'gravel']
    if gi:
        ys, xs = np.nonzero(np.isin(bi, gi))
        for _ in range(int(260 * AF)):
            j = pr.randrange(len(xs))
            x, y = xs[j] + pr.random(), ys[j] + pr.random()
            r = pr.uniform(1.0, 2.4)
            if free(x, y, r, 0.6):
                placed.append((x, y, r))
                cv.blob(x, y, r * pr.uniform(1.0, 1.4), r * 0.8, pr.choice(rmats), z=1.5, rot=pr.uniform(-0.6, 0.6), rough=0.1, rng=rng)
    # kökler: yukarıdan aşağı kıvrılan, incelen, dallanan
    rh, rs, rv = ROOT_HSV
    root_mat = cv.add_mat(hramp(rh, rs, rv, n=5, lo=0.4, hi=1.3), outline=OUTLINE * 0.8 + 0.02)
    for _ in range(int(st['roots'] * AF)):
        x, y = pr.uniform(0, S), pr.uniform(0, S)
        a = math.pi / 2 + pr.uniform(-0.7, 0.7)
        pts = [(x, y)]
        n = pr.randint(10, 26)
        for _k in range(n):
            a += pr.uniform(-0.35, 0.35)
            a = a * 0.85 + (math.pi / 2) * 0.15
            x += math.cos(a) * 3.2; y += math.sin(a) * 3.2
            pts.append((x, y))
            if pr.random() < 0.16:
                ba = a + pr.choice([-1, 1]) * pr.uniform(0.6, 1.2)
                bx, by = x, y
                bp = [(bx, by)]
                for _j in range(pr.randint(2, 5)):
                    ba += pr.uniform(-0.4, 0.4)
                    bx += math.cos(ba) * 2.8; by += math.sin(ba) * 2.8
                    bp.append((bx, by))
                cv.tube(bp, 0.9, 0.45, root_mat, z=1.2)
        r0 = pr.uniform(1.4, 2.4)
        cv.tube(pts, r0, 0.5, root_mat, z=1.0)
    # kemikler
    if st['bones']:
        bone = cv.add_mat(hramp(38, 0.16, 0.62, n=5, lo=0.45, hi=1.2), outline=OUTLINE * 0.7 + 0.04)
        for _ in range(int(st['bones'] * AF * 0.5)):
            x, y = pr.uniform(0, S), pr.uniform(0, S)
            a = pr.uniform(-0.6, 0.6) + (math.pi if pr.random() < 0.5 else 0)
            ln = pr.uniform(6, 13)
            x2, y2 = x + math.cos(a) * ln, y + math.sin(a) * ln
            cv.tube([(x, y), (x2, y2)], 1.1, 1.1, bone, z=3)
            for ex, ey in ((x, y), (x2, y2)):
                for s_ in (-1, 1):
                    cv.blob(ex + math.cos(a + s_ * 1.57) * 0.9, ey + math.sin(a + s_ * 1.57) * 0.9, 1.4, 1.3, bone, z=3.2)
    # biyom ekleri
    emis = None
    extra = st['extra']
    if extra == 'chalk':
        chalk = cv.add_mat(hramp(42, 0.16, 0.78, n=4, lo=0.6, hi=1.1), outline=None)
        for _ in range(int(28 * AF)):
            x, y = pr.uniform(0, S), pr.uniform(0, S)
            r = pr.uniform(0.9, 2.2)
            if free(x, y, r, 0.5):
                placed.append((x, y, r))
                cv.blob(x, y, r * 1.3, r, chalk, z=1.4, rough=0.25, rng=rng)
    if extra == 'ice':
        ice = cv.add_mat(hramp(205, 0.28, 0.86, n=5, lo=0.55, hi=1.2), outline=hexrgb('#3a4a66'), spec=0.9)
        for _ in range(int(26 * AF)):
            x, y = pr.uniform(0, S), pr.uniform(0, S)
            r = pr.uniform(5, 13)
            if free(x, y, r * 0.5, 0.5):
                placed.append((x, y, r * 0.5))
                cv.blob(x, y, r, pr.uniform(1.4, 2.6), ice, z=1.6, rot=pr.uniform(-0.15, 0.15), rough=0.15, rng=rng, flat=0.6)
    if extra == 'crystal':
        cols = [(172, 0.55, 0.92), (282, 0.42, 0.95)]
        for ci in range(int(18 * AF)):
            h_, s_, v_ = cols[ci % 2]
            cm = cv.add_mat(hramp(h_, s_, v_, n=5, lo=0.35, hi=1.15), outline=hexrgb('#06100c'), spec=0.9,
                            emis=hk.hsv(h_, 0.7, 0.55))
            cx, cy = pr.uniform(0, S), pr.uniform(0, S)
            base_a = -math.pi / 2 + pr.uniform(-1.6, 1.6)
            for k in range(pr.randint(3, 6)):
                a = base_a + pr.uniform(-0.7, 0.7)
                ln = pr.uniform(5, 15) * (1.0 if k else 1.3)
                w = pr.uniform(1.5, 3.0)
                px_, py_ = math.cos(a + 1.5708) * w, math.sin(a + 1.5708) * w
                tipx, tipy = cx + math.cos(a) * ln, cy + math.sin(a) * ln
                midx, midy = cx + math.cos(a) * ln * 0.78, cy + math.sin(a) * ln * 0.78
                # iki yüz: ışığa bakan / bakmayan
                lnorm = (math.cos(a - 1.5708) * 0.7, math.sin(a - 1.5708) * 0.7, 0.6)
                rnorm = (math.cos(a + 1.5708) * 0.7, math.sin(a + 1.5708) * 0.7, 0.6)
                cv.poly([(cx, cy), (cx + px_, cy + py_), (midx + px_, midy + py_), (tipx, tipy), (midx, midy)], cm, z=5 + k * 0.1, normal=rnorm)
                cv.poly([(cx, cy), (midx, midy), (tipx, tipy), (midx - px_, midy - py_), (cx - px_, cy - py_)], cm, z=5 + k * 0.1, normal=lnorm)
    rocks, remis, rmask = cv.shade(light=LIGHT, dither=0.7)
    # gömülme: taşların sol altına düşen gölge + çevre kararması
    cast = (roll(rmask, 1, -1) | roll(rmask, 2, -2) | roll(rmask, 2, -1)) & ~rmask
    ao = (roll(rmask, 1, 0) | roll(rmask, -1, 0) | roll(rmask, 0, 1) | roll(rmask, 0, -1)) & ~rmask & ~cast
    rgb[cast] *= 0.58
    rgb[ao] *= 0.8
    rgb[rmask] = rocks[rmask, :3]
    hgt[rmask] += cv.hgt[rmask] + 1.0
    if extra == 'crystal' or remis.max() > 0:
        emis = remis * 0.55
        # kristallerin çevresi hafifçe aydınlanır
        em_m = remis.max(axis=2) > 0
        halo = (roll(em_m, 1, 0) | roll(em_m, -1, 0) | roll(em_m, 0, 1) | roll(em_m, 0, -1) | roll(em_m, 2, 0) | roll(em_m, 0, -2)) & ~em_m & ~rmask
        rgb[halo] = rgb[halo] * 0.7 + np.array(st['glow'] or [0.4, 1, 0.8]) * 0.12
    if extra == 'lava':
        emis = np.zeros((S, S, 3))
        veins = np.zeros((S, S)); core = np.zeros((S, S), bool)
        for _ in range(int(5 * AF)):
            x, y = pr.uniform(0, S), pr.uniform(0, S)
            a = pr.uniform(0, TAU)
            stack = [(x, y, a, pr.uniform(0.8, 1.5), pr.randint(25, 60))]
            while stack:
                x, y, a, w, n = stack.pop()
                for _k in range(n):
                    a += pr.uniform(-0.45, 0.45)
                    x += math.cos(a); y += math.sin(a)
                    R = int(math.ceil(w)) + 3
                    for dy in range(-R, R + 1):
                        for dx in range(-R, R + 1):
                            d = math.hypot(dx, dy)
                            X, Y = int(x + dx) % S, int(y + dy) % S
                            veins[Y, X] = max(veins[Y, X], np.clip(1 - (d - w) / 3.5, 0, 1) if d > w else 1.0 + (w - d))
                    w = max(0.5, w * 0.985)
                    if pr.random() < 0.04 and len(stack) < 6:
                        stack.append((x, y, a + pr.choice([-1, 1]) * pr.uniform(0.6, 1.2), w * 0.7, int(n * 0.5)))
        inside = veins >= 1.0
        hot = veins >= 1.6
        halo = (veins > 0) & ~inside
        # ısı halesi: toprak koyu kızıla döner (basamaklı)
        hk_ = np.clip(np.floor(veins * 3 + (b - 0.5)) / 3, 0, 1)
        rgb[halo] = rgb[halo] * (1 - hk_[halo, None] * 0.5) + hexrgb('#5a1206') * hk_[halo, None] * 0.5
        rgb[inside] = hexrgb('#ff7a1a')
        rgb[hot] = hexrgb('#ffd060')
        edge_v = inside & ~(roll(inside, 1, 0) & roll(inside, -1, 0) & roll(inside, 0, 1) & roll(inside, 0, -1))
        rgb[edge_v & ~hot] = hexrgb('#c8340c')
        emis[inside] = hexrgb('#ff5a10') * 0.3
        emis[hot] = hexrgb('#ffb040') * 0.5
        emis[halo] = hexrgb('#ff3a08') * (hk_[halo, None] * 0.06)
        hgt[inside] -= 1.0
        # obsidiyen kırıkları: keskin, parlak
    # ince kırıntılar / pırıltı
    for _ in range(int(260 * AF)):
        x, y = pr.randrange(S), pr.randrange(S)
        if rmask[y, x]:
            continue
        c = SPECK[pr.choice([0, 0, 1, 2])]
        rgb[y, x] = c
        if pr.random() < 0.4:
            rgb[(y + 1) % S, x] = rgb[(y + 1) % S, x] * 0.7
    nrm = normals_from_height(hgt, 0.55)
    nrm[rmask] = cv.n[rmask]
    return rgb, normal_rgba(nrm), emis


# ------------------------------------------------------------------ kenar profilleri (P'de periyodik)
def _pn(seed, cells):
    rng = np.random.default_rng(seed)
    return hk.profile(P, cells, rng)


def _profiles():
    cap = STYLE['cap']
    u = np.arange(P)
    n1, n2, n3, n4, n5 = _pn(11, [27, 9, 3]), _pn(12, [36, 12, 4]), _pn(13, [27, 9]), _pn(14, [18, 6, 3]), _pn(15, [12, 4])
    if cap == 'snow':
        surf = 0.9 + 0.7 * np.sin(TAU * u / P + 0.7) + (n1 - 0.5) * 1.2
        th = 7.5 + 1.6 * np.sin(TAU * 2 * u / P + 1.3) + (n2 - 0.5) * 3.0
    elif cap == 'moss':
        surf = 2.4 + 1.0 * np.sin(TAU * u / P + 0.7) + (n1 - 0.5) * 1.6 + np.abs(np.sin(TAU * 9 * u / P + n4 * 3)) * -1.6 + 0.8
        th = 5.0 + 1.5 * np.sin(TAU * 2 * u / P + 1.3) + (n2 - 0.5) * 2.4
    elif cap == 'ash':
        surf = 2.0 + 0.9 * np.sin(TAU * u / P + 0.7) + (n1 - 0.5) * 1.8
        th = 3.6 + 1.0 * np.sin(TAU * 3 * u / P + 1.3) + (n2 - 0.5) * 2.0
    elif cap == 'dry':
        surf = 2.6 + 1.0 * np.sin(TAU * u / P + 0.7) + (n1 - 0.5) * 1.6
        th = 3.4 + 0.8 * np.sin(TAU * 2 * u / P + 1.3) + (n2 - 0.5) * 1.8
    else:
        surf = 3.4 + 1.2 * np.sin(TAU * u / P + 0.7) + 0.5 * np.sin(TAU * 3 * u / P + 2.1) + (n1 - 0.5) * 1.4
        th = 5.6 + 1.4 * np.sin(TAU * 2 * u / P + 1.3) + (n2 - 0.5) * 2.4
    side = 1.8 + 1.3 * np.sin(TAU * u / P + 0.4) + 0.7 * np.sin(TAU * 4 * u / P + 1.1) + (n3 - 0.5) * 2.2
    bot = 1.8 + 1.2 * np.sin(TAU * u / P + 2.4) + (n4 - 0.5) * 2.4
    corner = 6.0 + (n5 - 0.5) * 3.0
    return dict(surf=np.clip(surf, 0, 6), th=np.clip(th, 2, 10), side=np.clip(side, 0.3, 5), bot=np.clip(bot, 0.3, 5), corner=corner)


def _blade_color(lean, t, tip):
    if tip:
        return GRASS[6] if lean >= 0 else GRASS[5]
    return GRASS[min(6, 2 + int(t * 3.4) + (1 if lean > 0 else 0))]


def ground_tile(mask, var, PR):
    up, rt, dn, lf = bool(mask & 1), bool(mask & 2), bool(mask & 4), bool(mask & 8)
    cap = STYLE['cap']
    off = var * TS
    PADW = 8
    N = TS + 2 * PADW
    ly, lx = np.mgrid[0:N, 0:N] - PADW
    u = (off + lx) % P
    v = (off + ly) % P
    solid = np.ones((N, N), bool)
    # tile dışı: açık yönlerde hava
    if up:
        solid &= ly >= PR['surf'][u] if cap == 'snow' else ly >= np.floor(PR['surf'][u] + PR['th'][u] * 0.5)
    if dn:
        solid &= ly <= TS - 1 - PR['bot'][u]
    if lf:
        solid &= lx >= PR['side'][v]
    if rt:
        solid &= lx <= TS - 1 - PR['side'][(v + 53) % P]
    # dış köşe yuvarlatma
    for cx, cy, on, sx, sy in ((0, 0, up and lf, 1, 1), (TS - 1, 0, up and rt, -1, 1), (0, TS - 1, dn and lf, 1, -1), (TS - 1, TS - 1, dn and rt, -1, -1)):
        if not on:
            continue
        rc = PR['corner'][(off + cx) % P]
        ccx, ccy = cx + sx * rc, cy + sy * rc
        inq = ((lx - ccx) * sx < 0) & ((ly - ccy) * sy < 0)
        solid &= ~(inq & ((lx - ccx) ** 2 + (ly - ccy) ** 2 > rc * rc))
    kind = np.zeros((N, N), int)  # 0 hava 1 toprak 2 gölge 3 ışık 4 kenar 5 renkli 6 ışıma
    kind[solid] = 1
    air = ~solid

    def air_at(dy, dx):
        return hk.shift_nw(air, -dy, -dx, True)
    # gölge tarafı (sol/alt), ışık tarafı (sağ)
    shade = np.zeros((N, N), bool)
    for k in range(1, 5):
        shade |= air_at(0, -k) | air_at(k, 0) | air_at(k, -k)
    lit = np.zeros((N, N), bool)
    for k in range(1, 4):
        lit |= air_at(0, k)
    edge = air_at(0, -1) | air_at(1, 0) | air_at(1, -1)
    kind[solid & lit] = 3
    kind[solid & shade] = 2
    kind[solid & edge] = 4
    col = np.zeros((N, N, 3))
    hgt = np.zeros((N, N))
    rng = random.Random(mask * 131 + var * 7 + 3)

    def put(y, x, c, k=5):
        if 0 <= y + PADW < N and 0 <= x + PADW < N:
            kind[y + PADW, x + PADW] = k
            if c is not None:
                col[y + PADW, x + PADW] = c

    def get(y, x):
        if 0 <= y + PADW < N and 0 <= x + PADW < N:
            return kind[y + PADW, x + PADW]
        return 0

    # ---- yüzey kapağı
    if up:
        _cap(kind, col, hgt, solid, lx, ly, u, off, PR, put, get, lf, rt, N, PADW)
    # ---- tavan: sarkanlar
    if dn:
        _ceiling_edge(PR, off, put, get, solid)
    # ---- yan yüzlerde çıkıntı taşları / kökler / buz / lav çatlakları
    _side_details(mask, var, PR, put, get, kind, col, solid, lf, rt, up, dn, N, PADW, rng)
    # kırp: yalnızca karo içi
    kind = kind[PADW:PADW + TS, PADW:PADW + TS]
    col = col[PADW:PADW + TS, PADW:PADW + TS]
    hgt = hgt[PADW:PADW + TS, PADW:PADW + TS]
    rgba = np.zeros((TS, TS, 4))
    rgba[kind == 1, :3] = KEY_SOIL
    rgba[kind == 2, :3] = KEY_SHADE
    rgba[kind == 3, :3] = KEY_LIT
    rgba[kind == 4, :3] = KEY_EDGE
    rgba[kind == 5, :3] = col[kind == 5]
    rgba[kind == 6, :3] = KEY_GLOW
    rgba[kind > 0, 3] = 1.0
    nm = normal_rgba(normals_from_height(hgt, 0.6, wrap=False), (kind > 0).astype(float))
    return rgba, nm


def _cap(kind, col, hgt, solid, lx, ly, u, off, PR, put, get, lf, rt, N, PADW):
    cap = STYLE['cap']
    surf, th = PR['surf'], PR['th']
    b8 = hk.BAYER8
    side = PR['side']

    def inside_x(x, y):
        """Yan kenarlara taşma kontrolü (kar biraz taşabilir)."""
        allow = 1.6 if cap == 'snow' else 0.0
        vv = (off + y) % P
        if lf and x < side[vv] - allow:
            return False
        if rt and x > TS - 1 - side[(vv + 53) % P] + allow:
            return False
        return True

    for x in range(-2, TS + 2):
        uu = (off + x) % P
        s = surf[uu]; t_ = th[uu]
        y0 = int(math.floor(s)); y1 = int(math.floor(s + t_))
        if cap == 'snow':
            # kar yastığı: üstte bembeyaz, altta mavi gölge, alt kenar dalgalı
            for y in range(y0, y1 + 1):
                if not inside_x(x, y):
                    continue
                t = (y - s) / max(1.0, t_)
                bv = b8[y % 8, x % 8]
                if y == y0:
                    c = GRASS[6]
                elif t < 0.3:
                    c = GRASS[6] if bv < 0.5 - t else GRASS[5]
                elif t < 0.65:
                    c = GRASS[5] if bv < 0.75 - t else GRASS[4]
                elif y < y1:
                    c = GRASS[4] if bv < 0.9 - t else GRASS[3]
                else:
                    c = GRASS[2]
                # sol kenarda kar gölgeli
                if lf and x < side[(off + y) % P] + 2:
                    c = GRASS[3] if y > y0 else GRASS[5]
                put(y, x, c)
            if _hash(uu, 41) < 0.12:
                put(y0, x, SPECK[0])
        elif cap == 'moss':
            # yosun minderi: tümsekli, tümsek eğimine göre ışık
            dsl = surf[(uu + 1) % P] - surf[(uu - 1) % P]
            for y in range(y0, y1 + 1):
                if not inside_x(x, y) or get(y, x) == 0 and y > s + 2:
                    continue
                t = (y - s) / max(1.0, t_)
                bv = b8[y % 8, x % 8]
                lvl = 5 - t * 4.2 + (0.8 if dsl < -0.2 else (-0.8 if dsl > 0.2 else 0)) + (bv - 0.5) * 1.1
                c = GRASS[int(np.clip(lvl, 1, 6))]
                if y == y1:
                    c = GRASS[1]
                put(y, x, c)
            if _hash(uu, 42) < 0.07:
                put(y0 + 1, x, SPECK[0])
            if _hash(uu, 43) < 0.03:
                put(y0, x, None, 6)
            # altına sarkan yosun lifleri
            if _hash(uu, 44) < 0.2:
                for k in range(int(1 + _hash(uu, 45) * 4)):
                    if get(y1 + 1 + k, x) in (1, 2, 3, 4):
                        put(y1 + 1 + k, x, GRASS[1] if k else GRASS[2])
        elif cap == 'ash':
            for y in range(y0, y1 + 1):
                if not inside_x(x, y):
                    continue
                t = (y - s) / max(1.0, t_)
                bv = b8[y % 8, x % 8]
                ash = ASH_PAL()
                lvl = 4.6 - t * 4.2 + (bv - 0.5) * 1.2
                c = ash[int(np.clip(lvl, 0, 5))]
                if y == y1:
                    c = ash[0]
                put(y, x, c)
            # kömür parçaları ve közler
            h1 = _hash(uu, 51)
            if h1 < 0.06:
                put(y0 + 1, x, None, 6)
            elif h1 < 0.14:
                put(y0, x, GRASS[4])
            elif h1 < 0.24:
                put(y0 + 1, x, ASH_PAL()[0])
        else:
            # çimen / kuru ot turbası
            for y in range(y0, y1 + 1):
                if not inside_x(x, y):
                    continue
                t = (y - s) / max(1.0, t_)
                bv = b8[y % 8, x % 8]
                if y == y0:
                    c = GRASS[5] if _hash(uu, 61) < 0.6 else GRASS[6]
                else:
                    lvl = 4.8 - t * 4.0 + (bv - 0.5) * 1.3
                    if (x + int(_hash(uu, 62) * 3)) % 5 == 0:
                        lvl -= 1          # ot sapı çizgileri
                    c = GRASS[int(np.clip(lvl, 1, 5))]
                if y == y1:
                    c = GRASS[1] if cap == 'grass' else SOIL[1]
                put(y, x, c)
            # turbanın altından sarkan kılcal kökler
            if _hash(uu, 63) < (0.26 if cap == 'grass' else 0.14):
                for k in range(int(1 + _hash(uu, 64) * 5)):
                    if get(y1 + 1 + k, x) in (1, 2, 3, 4):
                        put(y1 + 1 + k, x, GRASS[1] if k < 1 else ROOT[1 + (k % 2)])
            if cap == 'dry' and _hash(uu, 65) < 0.08:
                put(y0, x, SPECK[0])
        # kapağın altında gölge bandı
        for y in range(y1 + 1, y1 + 3):
            if get(y, x) in (1, 3):
                put(y, x, None, 2)
    # yaprak/ot tutamları: kapak yüzeyinin üstünde (karo içinde kalan kısa kısım)
    if cap in ('grass', 'dry', 'moss'):
        for uu0 in range(off - 6, off + TS + 6):
            uu = uu0 % P
            pt = 0.3 if cap == 'grass' else (0.22 if cap == 'dry' else 0.1)
            if _hash(uu, 71) >= pt:
                continue
            x0 = uu0 - off
            base = int(math.floor(surf[uu])) + 1
            nbl = 2 + int(_hash(uu, 72) * 4)
            for j in range(nbl):
                lean = (j - (nbl - 1) / 2) * (0.5 + _hash(uu, 73 + j) * 0.6)
                hh = 2 + int(_hash(uu, 80 + j) * (base + 3))
                for k in range(hh):
                    yy_ = base - 1 - k
                    if yy_ < 0:
                        break
                    tt = k / max(1, hh - 1)
                    xx_ = x0 + int(round(lean * tt * tt * 2.2))
                    if not inside_x(xx_, yy_):
                        continue
                    if cap == 'moss':
                        c = GRASS[4] if k < hh - 1 else SPECK[0]
                    else:
                        c = _blade_color(lean, tt, k == hh - 1)
                    put(yy_, xx_, c)
    # yüzey taşları (kuru bozkır / kül): toprağa yarı gömülü
    if cap in ('dry', 'ash', 'snow'):
        for uu0 in range(off - 6, off + TS + 6):
            uu = uu0 % P
            if _hash(uu, 91) >= 0.035:
                continue
            x0 = uu0 - off
            r = 1.6 + _hash(uu, 92) * 1.8
            y0 = surf[uu] + th[uu] * 0.4
            _stone(put, get, x0, y0, r, r * 0.75, int(_hash(uu, 93) * 4), snow=(cap == 'snow'))


_ASH = None


def ASH_PAL():
    global _ASH
    if _ASH is None:
        _ASH = pal('#141012', '#241d1e', '#372d2d', '#4d4241', '#675a57', '#857673')
    return _ASH


def _stone(put, get, cx, cy, rx, ry, mi, snow=False, rough_seed=0):
    """Kenara gömülü küçük taş: üst sağ ışık, alt sol kontur."""
    h, s, v = ROCK[mi % len(ROCK)]
    rp = hramp(h, s, v, n=6, lo=0.34, hi=1.35)
    R = int(math.ceil(max(rx, ry))) + 1
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            q = (dx / rx) ** 2 + (dy / ry) ** 2
            if q > 1.0:
                continue
            x, y = int(math.floor(cx + dx)), int(math.floor(cy + dy))
            nx, ny = dx / rx, dy / ry
            lam = (nx * LIGHT[0] + ny * LIGHT[1]) * 0.6 + (1 - q) ** 0.5 * LIGHT[2] * 0.8
            lvl = int(np.clip(1.5 + lam * 4.2, 1, 5))
            c = rp[lvl]
            if q > 0.55 and (nx - ny) < -0.6:
                c = rp[0]
            if snow and ny < -0.45:
                c = GRASS[6] if nx > -0.2 else GRASS[5]
            put(y, x, c)


def _ceiling_edge(PR, off, put, get, solid):
    ceil = STYLE['ceil']
    bot = PR['bot']
    for x in range(0, TS):
        uu = (off + x) % P
        y0 = int(TS - 1 - bot[uu])
        hsh = _hash(uu, 101)
        if ceil == 'roots':
            if hsh < 0.18:
                ln = 2 + int(_hash(uu, 102) * 6)
                for k in range(ln):
                    if get(y0 + 1 + k, x) == 0:
                        put(y0 + 1 + k, x, ROOT[2] if k < ln - 1 else ROOT[3])
        elif ceil == 'moss':
            if hsh < 0.45:
                ln = 1 + int(_hash(uu, 102) * (5 if hsh < 0.15 else 2))
                for k in range(ln):
                    put(y0 + k, x, GRASS[2] if k < ln - 1 else GRASS[3])
                if hsh < 0.05:
                    put(y0 + ln, x, None, 6)
        elif ceil == 'ice':
            if hsh < 0.22:
                ln = 2 + int(_hash(uu, 102) * 6)
                w = 1 + (1 if _hash(uu, 103) < 0.4 else 0)
                for k in range(ln):
                    for j in range(w if k < ln * 0.5 else 1):
                        put(y0 + k, x + j, GRASS[5] if j else (GRASS[4] if k < ln - 1 else GRASS[6]))
            else:
                put(y0, x, GRASS[4])
        elif ceil == 'drip':
            if hsh < 0.12:
                ln = 2 + int(_hash(uu, 102) * 4)
                h, s, v = ROCK[0]
                rp = hramp(h, s, v, n=6)
                for k in range(ln):
                    put(y0 + k, x, rp[2] if k < ln - 1 else rp[1])
                    if k < ln * 0.4:
                        put(y0 + k, x + 1, rp[3])
                if _hash(uu, 104) < 0.5:
                    put(y0 + ln, x, None, 6)


def _side_details(mask, var, PR, put, get, kind, col, solid, lf, rt, up, dn, N, PADW, rng):
    cap = STYLE['cap']
    side = PR['side']
    off = var * TS
    for s_, on in (('l', lf), ('r', rt)):
        if not on:
            continue
        for k in range(2):
            if rng.random() > (0.75 if k == 0 else 0.35):
                continue
            sy = rng.randint(10, TS - 8)
            vv = (off + sy) % P
            sx = side[vv] + 0.5 if s_ == 'l' else TS - 1 - side[(vv + 53) % P] - 0.5
            if up and sy < PR['surf'][(off + int(sx)) % P] + PR['th'][(off + int(sx)) % P] + 3:
                continue
            r = rng.uniform(2.2, 4.0)
            _stone(put, get, sx, sy, r * rng.uniform(1.0, 1.3), r * rng.uniform(0.75, 1.0), rng.randrange(4), snow=(cap == 'snow'))
            # taşın sol altına gölge (toprakta)
            for dy in range(1, int(r) + 3):
                for dx in range(-int(r) - 2, 1):
                    yy_, xx_ = int(sy + dy), int(sx + dx)
                    if get(yy_, xx_) in (1, 3) and (dx * dx + dy * dy) < (r + 1.5) ** 2:
                        put(yy_, xx_, None, 2)
        # biyoma göre yan yüz süsü
        if cap == 'grass' and rng.random() < 0.5:
            # yandan çıkan kök
            sy = rng.randint(12, TS - 6)
            vv = (off + sy) % P
            x = int(side[vv]) if s_ == 'l' else int(TS - 1 - side[(vv + 53) % P])
            d = -1 if s_ == 'l' else 1
            for k in range(rng.randint(3, 6)):
                put(sy + k // 2, x + d * k, ROOT[2] if k % 2 else ROOT[1])
        if cap == 'moss':
            for y in range(4, TS):
                vv = (off + y) % P
                x = int(math.ceil(side[vv])) if s_ == 'l' else int(TS - 1 - side[(vv + 53) % P])
                if _hash(vv, 7 if s_ == 'l' else 8) < 0.35:
                    put(y, x, GRASS[2] if s_ == 'l' else GRASS[3])
        if cap == 'snow' and s_ == 'r':
            for y in range(4, TS):
                vv = (off + y) % P
                x = int(TS - 1 - side[(vv + 53) % P])
                if _hash(vv, 9) < 0.18:
                    put(y, x, GRASS[5])
        if cap == 'ash' and rng.random() < 0.6:
            # lav çatlağı: yan yüzde ışıyan ince damar
            sy = rng.randint(8, TS - 10)
            vv = (off + sy) % P
            x = int(side[vv]) + 1 if s_ == 'l' else int(TS - 1 - side[(vv + 53) % P]) - 1
            d = 1 if s_ == 'l' else -1
            for k in range(rng.randint(4, 9)):
                if get(sy + k, x) in (1, 2, 3, 4):
                    put(sy + k, x, None, 6)
                if rng.random() < 0.4:
                    x += d


# ------------------------------------------------------------------ üst/tavan süs karoları (overlay)
def _line(img, x0, y0, x1, y1, c):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / max(1, n)
        x = int(round(x0 + (x1 - x0) * t)); y = int(round(y0 + (y1 - y0) * t))
        if 0 <= x < TS and 0 <= y < TS:
            img[y, x, :3] = c; img[y, x, 3] = 1


def _px(img, x, y, c):
    x, y = int(x), int(y)
    if 0 <= x < TS and 0 <= y < TS:
        img[y, x, :3] = c; img[y, x, 3] = 1


def _blade(img, x0, y0, h, lean, base_c, mid_c, tip_c, curve=2.2):
    """Kıvrık ot yaprağı: tabandan uca, uca doğru eğilir (karesel eğri)."""
    pts = []
    for k in range(h):
        t = k / max(1, h - 1)
        x = x0 + lean * t * t * curve * h / 8.0
        y = y0 - k
        pts.append((x, y))
    for k, (x, y) in enumerate(pts):
        t = k / max(1, h - 1)
        c = base_c if t < 0.35 else (mid_c if t < 0.85 else tip_c)
        _px(img, round(x), y, c)


def grass_overlay(var):
    rng = random.Random(900 + var * 17 + sum(map(ord, STYLE['cap'])) % 97)
    cap = STYLE['cap']
    img = np.zeros((TS, TS, 4))
    B = TS - 1
    if cap in ('grass', 'dry'):
        x = rng.randint(0, 2)
        while x < TS:
            if rng.random() < (0.62 if cap == 'grass' else 0.42):
                nbl = rng.randint(3, 6)
                tall = rng.random() < 0.25
                for j in range(nbl):
                    lean = (j - (nbl - 1) / 2) * rng.uniform(0.6, 1.4) + rng.uniform(-0.5, 0.5)
                    h = rng.randint(3, 9) + (rng.randint(4, 11) if tall else 0)
                    lit = lean > 0
                    _blade(img, x + j * 0.5, B, h, lean, GRASS[2], GRASS[4] if lit else GRASS[3], GRASS[6] if lit else GRASS[5])
                x += rng.randint(2, 5)
            else:
                x += rng.randint(1, 3)
        if cap == 'grass':
            # eğreltiotu ya da soluk mantar kümesi / solgun çiçek
            k = var % 4
            if k == 0:
                fx = rng.randint(8, 26); fh = rng.randint(12, 20)
                for i in range(fh):
                    t = i / fh
                    xx = fx + int(round(t * t * 4))
                    _px(img, xx, B - i, GRASS[2])
                    if i > 2 and i % 2 == 0:
                        ln = int((1 - t) * 5) + 1
                        for j in range(1, ln + 1):
                            _px(img, xx - j, B - i + j // 2, GRASS[3])
                            _px(img, xx + j, B - i - j // 3, GRASS[4] if j < ln else GRASS[5])
            elif k == 1:
                for m in range(rng.randint(2, 3)):
                    mx = rng.randint(6, 28); mh = rng.randint(3, 6); mw = rng.randint(2, 3)
                    for i in range(mh):
                        _px(img, mx, B - i, hexrgb('#b8b0a0'))
                    for dx in range(-mw, mw + 1):
                        c = hexrgb('#8a8f8c') if dx < 0 else hexrgb('#c2c8bc')
                        _px(img, mx + dx, B - mh, c)
                        if abs(dx) < mw:
                            _px(img, mx + dx, B - mh - 1, hexrgb('#d6dccf') if dx >= 0 else hexrgb('#9aa29b'))
                    _px(img, mx - mw, B - mh + 1, hexrgb('#5c615e')); _px(img, mx + mw, B - mh + 1, hexrgb('#6c726e'))
            elif k == 2:
                fx = rng.randint(6, 28); fh = rng.randint(10, 16)
                _blade(img, fx, B, fh, 1.0, GRASS[2], GRASS[3], GRASS[3])
                cy = B - fh
                petal = [hexrgb('#9fb4c8'), hexrgb('#b9a7c9'), hexrgb('#c9c3a4')][var % 3]
                for dx, dy, m in ((-1, 0, 0.75), (1, 0, 1.05), (0, -1, 1.1), (0, 1, 0.6), (0, 0, 1.25)):
                    _px(img, fx + 1 + dx, cy + dy, np.clip(petal * m, 0, 1))
        else:
            k = var % 4
            if k in (0, 2):
                # sorguçlu otu (Stipa): uzun ince sap + sarkan gümüşi tüy
                for m in range(rng.randint(2, 4)):
                    fx = rng.randint(3, 32); fh = rng.randint(14, 28)
                    lean = rng.uniform(0.5, 2.5)
                    _blade(img, fx, B, fh, lean, GRASS[2], GRASS[4], GRASS[5], curve=1.4)
                    tx = fx + lean * 1.4 * fh / 8.0
                    for j in range(rng.randint(4, 8)):
                        _px(img, round(tx + j * 0.8), B - fh + 1 + j, SPECK[0] if j % 2 else SPECK[2])
            elif k == 1:
                # gelincikler
                for m in range(rng.randint(2, 3)):
                    fx = rng.randint(4, 30); fh = rng.randint(6, 12)
                    _blade(img, fx, B, fh, 0.6, GRASS[1], GRASS[2], GRASS[3])
                    cy = B - fh
                    for dx, dy, c in ((-1, 0, '#a8221c'), (1, 0, '#e8463a'), (0, -1, '#f0584a'), (0, 0, '#2a0c0a'), (-1, -1, '#c8302a'), (1, -1, '#ff7a64')):
                        _px(img, fx + 1 + dx, cy + dy, hexrgb(c))
            else:
                for m in range(rng.randint(3, 5)):
                    fx = rng.randint(4, 30); fh = rng.randint(5, 10)
                    _blade(img, fx, B, fh, 0.4, GRASS[1], GRASS[2], GRASS[3])
                    _px(img, fx + 1, B - fh, hexrgb('#ffd84a')); _px(img, fx, B - fh, hexrgb('#e0a82a')); _px(img, fx + 1, B - fh - 1, hexrgb('#fff0a0'))
    elif cap == 'moss':
        x = 0
        while x < TS:
            if rng.random() < 0.5:
                h = rng.randint(1, 3)
                for k in range(h):
                    _px(img, x, B - k, GRASS[3 + min(k, 3)])
            x += 1
        k = var % 4
        if k in (0, 2):
            # ışıldayan mantarlar
            for m in range(rng.randint(2, 4)):
                mx = rng.randint(4, 31); mh = rng.randint(3, 9); mw = rng.randint(1, 3)
                for i in range(mh):
                    _px(img, mx, B - i, hexrgb('#9ec8b8') if i % 3 else hexrgb('#7aa898'))
                for dx in range(-mw, mw + 1):
                    _px(img, mx + dx, B - mh, hexrgb('#3fd0a8') if dx < 0 else hexrgb('#8af0d0'))
                    if abs(dx) < mw:
                        _px(img, mx + dx, B - mh - 1, hexrgb('#c0fff0') if dx >= 0 else hexrgb('#60e0bc'))
                _px(img, mx - mw, B - mh + 1, hexrgb('#1a6a58'))
        elif k == 1:
            # küçük kristal kümesi
            cx = rng.randint(8, 27)
            c1 = [hexrgb('#3a2a5a'), hexrgb('#7a5ab8'), hexrgb('#b89af0'), hexrgb('#f0e0ff')]
            for j, (dx, h, lean) in enumerate(((0, rng.randint(7, 12), 0), (-3, rng.randint(4, 7), -1), (3, rng.randint(4, 8), 1))):
                for i in range(h):
                    w = 1 if i > h - 3 else 2
                    xx = cx + dx + int(lean * i / h * 2)
                    for q in range(-w + 1, w):
                        _px(img, xx + q, B - i, c1[1] if q < 0 else c1[2])
                    _px(img, xx - w, B - i, c1[0])
                _px(img, cx + dx + lean, B - h, c1[3])
        else:
            for m in range(rng.randint(3, 6)):
                fx = rng.randint(2, 33)
                _blade(img, fx, B, rng.randint(4, 9), rng.uniform(-1.5, 1.5), GRASS[2], GRASS[4], SPECK[0])
    elif cap == 'snow':
        # karın içinden çıkan donmuş ot uçları, kar topakları, buz kristali
        for m in range(rng.randint(4, 9)):
            fx = rng.randint(1, 34)
            _blade(img, fx, B, rng.randint(2, 8), rng.uniform(-1.5, 1.5), hexrgb('#5a6680'), hexrgb('#8a96b0'), hexrgb('#d8e4f4'))
        for m in range(rng.randint(1, 3)):
            cx = rng.randint(3, 32); w = rng.randint(2, 5); h = rng.randint(1, 3)
            for dy in range(h):
                for dx in range(-w + dy, w - dy + 1):
                    _px(img, cx + dx, B - dy, GRASS[6] if dy == h - 1 or dx > 0 else GRASS[5])
        if var % 3 == 0:
            # kar yüklü küçük çalı
            cx = rng.randint(8, 27)
            for i in range(rng.randint(5, 9)):
                a = -math.pi / 2 + rng.uniform(-1.0, 1.0)
                ln = rng.randint(4, 9)
                _line(img, cx, B, cx + math.cos(a) * ln, B + math.sin(a) * ln, hexrgb('#3a3448'))
                _px(img, cx + math.cos(a) * ln, B + math.sin(a) * ln - 1, GRASS[6])
    elif cap == 'ash':
        for m in range(rng.randint(3, 6)):
            fx = rng.randint(1, 34)
            _blade(img, fx, B, rng.randint(2, 6), rng.uniform(-1, 1), hexrgb('#1a1214'), hexrgb('#2a1e1e'), GRASS[4] if rng.random() < 0.4 else hexrgb('#3a2c2a'))
        k = var % 4
        if k == 0:
            # kafatası
            cx = rng.randint(8, 26)
            bone = [hexrgb('#4a4038'), hexrgb('#8a7e6e'), hexrgb('#b8ab96'), hexrgb('#d8ccb6')]
            for dy in range(5):
                for dx in range(-3, 4):
                    if (dx / 3.4) ** 2 + ((dy - 2.5) / 2.8) ** 2 <= 1:
                        _px(img, cx + dx, B - dy, bone[2] if dx > -1 else bone[1])
            _px(img, cx - 1, B - 2, bone[0]); _px(img, cx + 1, B - 2, bone[0]); _px(img, cx + 2, B - 3, bone[3]); _px(img, cx, B, bone[0])
        elif k == 1:
            # obsidiyen dikenleri
            for m in range(rng.randint(2, 3)):
                cx = rng.randint(4, 31); h = rng.randint(4, 10)
                for i in range(h):
                    w = max(0, int((1 - i / h) * 2.2))
                    for q in range(-w, w + 1):
                        _px(img, cx + q, B - i, hexrgb('#0c0a10') if q < 0 else hexrgb('#2a2638'))
                    _px(img, cx + w, B - i, hexrgb('#6a6688') if i % 3 == 0 else hexrgb('#3a364a'))
        elif k == 2:
            # yanmış kütük
            cx = rng.randint(8, 24)
            for i in range(rng.randint(5, 9)):
                for q in range(0, 4):
                    _px(img, cx + q, B - i, hexrgb('#140e0e') if q == 0 else (hexrgb('#2e2220') if q < 3 else hexrgb('#4a3632')))
            _px(img, cx + 1, B - 2, GRASS[5]); _px(img, cx + 2, B - 4, GRASS[4])
    nm = normal_rgba(np.dstack([np.zeros((TS, TS)), np.zeros((TS, TS)), np.ones((TS, TS))]), img[..., 3])
    return img, nm


def ceiling_overlay(var):
    rng = random.Random(950 + var * 13)
    ceil = STYLE['ceil']
    img = np.zeros((TS, TS, 4))
    for _ in range(rng.randint(2, 5)):
        x = rng.randint(1, TS - 2)
        ln = rng.randint(6, 26)
        if ceil == 'roots':
            xx = float(x)
            for k in range(ln):
                xx += rng.uniform(-0.45, 0.45)
                c = ROOT[2] if k < ln - 2 else ROOT[3]
                _px(img, round(xx), k, c)
                if k < ln * 0.3:
                    _px(img, round(xx) + 1, k, ROOT[1])
                if rng.random() < 0.08:
                    d = rng.choice([-1, 1])
                    for j in range(1, rng.randint(2, 5)):
                        _px(img, round(xx) + d * j, k + j, ROOT[2])
        elif ceil == 'moss':
            xx = float(x)
            for k in range(ln):
                xx += rng.uniform(-0.3, 0.3)
                _px(img, round(xx), k, GRASS[2] if k % 3 else GRASS[3])
                if k % 4 == 1:
                    _px(img, round(xx) + 1, k, GRASS[4])
            if rng.random() < 0.6:
                _px(img, round(xx), ln, hexrgb('#9af0d0')); _px(img, round(xx), ln + 1, hexrgb('#3fd0a8'))
        elif ceil == 'ice':
            w = rng.randint(1, 3)
            for k in range(ln):
                ww = max(0, int(round(w * (1 - k / ln))))
                for q in range(-ww, ww + 1):
                    c = GRASS[4] if q < 0 else (GRASS[6] if q == ww and k % 2 == 0 else GRASS[5])
                    _px(img, x + q, k, c)
            _px(img, x, ln, GRASS[6])
        elif ceil == 'drip':
            h, s, v = ROCK[0]
            rp = hramp(h, s, v, n=6, lo=0.4, hi=1.4)
            w = rng.randint(1, 3)
            ln = min(ln, 18)
            for k in range(ln):
                ww = max(0, int(round(w * (1 - k / ln))))
                for q in range(-ww, ww + 1):
                    _px(img, x + q, k, rp[1] if q < 0 else (rp[3] if q == ww else rp[2]))
            if rng.random() < 0.7:
                _px(img, x, ln, hexrgb('#ff9a30')); _px(img, x, ln + 1, hexrgb('#ffd060'))
    nm = normal_rgba(np.dstack([np.zeros((TS, TS)), np.zeros((TS, TS)), np.ones((TS, TS))]), img[..., 3])
    return img, nm


def platform_tile(kind, var):
    """Tahta tek yönlü platform: kind 0 sol uç, 1 orta, 2 sağ uç. Çarpışma üst %25 (9 px)."""
    rng = random.Random(70 + kind * 5 + var)
    cap = STYLE['cap']
    img = np.zeros((TS, TS, 4))
    x0 = 1 if kind == 0 else 0
    x1 = TS - 2 if kind == 2 else TS - 1
    TOP = 1 if cap == 'snow' else 0
    for y in range(TOP, 11):
        for x in range(x0, x1 + 1):
            g = math.sin((x + var * TS) * 0.33 + y * 1.9 + math.sin(x * 0.11) * 2) + (_hash(x + var * TS, y) - 0.5) * 0.9
            if y == TOP:
                lvl = 5 if (x + var * 7) % 9 != 4 else 4
            elif y == TOP + 1:
                lvl = 4
            elif y >= 9:
                lvl = 0 if y == 10 else 1
            else:
                lvl = 3 if g > 0.5 else 2
                if g < -1.0:
                    lvl = 1
            if (x + var * TS) % 18 == 0 and TOP < y < 10:
                lvl = 0        # tahta ek yeri
            if (x + var * TS) % 18 == 1 and TOP < y < 10:
                lvl = 4
            img[y, x, :3] = WOOD[lvl]; img[y, x, 3] = 1
    # çiviler / demir kuşak
    for nx in (7, 25):
        if x0 <= nx <= x1:
            img[4, nx, :3] = hexrgb('#4a525e'); img[3, nx, :3] = hexrgb('#9aa2ac'); img[5, nx, :3] = hexrgb('#2a2e36')
    if cap == 'snow':
        for x in range(x0, x1 + 1):
            img[0, x, :3] = GRASS[6]; img[0, x, 3] = 1
            img[1, x, :3] = GRASS[5] if _hash(x, var) < 0.7 else WOOD[5]
            if _hash(x, 3, var) < 0.12:
                for k in range(1, 4):
                    img[10 + k, x, :3] = GRASS[5] if k < 3 else GRASS[6]; img[10 + k, x, 3] = 1
    elif cap == 'moss':
        mx = rng.randint(2, 20)
        for k in range(rng.randint(5, 12)):
            if x0 <= mx + k <= x1:
                img[0, mx + k, :3] = GRASS[4 if k % 2 else 5]
                if k % 3 == 0:
                    img[11, mx + k, :3] = GRASS[2]; img[11, mx + k, 3] = 1
    elif cap in ('grass', 'dry'):
        if rng.random() < 0.6:
            mx = rng.randint(3, 25)
            for k in range(rng.randint(3, 7)):
                if x0 <= mx + k <= x1:
                    img[0, mx + k, :3] = GRASS[4 if k % 2 else 3]
    elif cap == 'ash':
        for x in range(x0, x1 + 1):
            if _hash(x, var, 5) < 0.25:
                img[TOP, x, :3] = ASH_PAL()[3]
            if _hash(x, var, 6) < 0.04:
                img[9, x, :3] = hexrgb('#ff8a30')
    if kind in (0, 2):
        # dikme + çapraz destek
        bx = 5 if kind == 0 else TS - 6
        d = 1 if kind == 0 else -1
        for k in range(15):
            yy, xx = 11 + k, bx + d * int(k * 0.6)
            if 0 <= yy < TS and 0 <= xx < TS:
                img[yy, xx, :3] = WOOD[2] if k % 4 else WOOD[1]; img[yy, xx, 3] = 1
                if 0 <= xx + d < TS:
                    img[yy, xx + d, :3] = WOOD[1]; img[yy, xx + d, 3] = 1
                if 0 <= xx - d < TS:
                    img[yy, xx - d, :3] = WOOD[3]; img[yy, xx - d, 3] = 1
        # ip sargısı
        for k in range(1, 9):
            img[k, bx, :3] = hexrgb('#8a7a58') if k % 2 else hexrgb('#5a4c34')
            img[k, bx + d, :3] = hexrgb('#6e6046') if k % 2 else hexrgb('#4a3e2a')
    nm = normal_rgba(np.dstack([np.zeros((TS, TS)), np.zeros((TS, TS)), np.ones((TS, TS))]), img[..., 3])
    return img, nm


def build_ground_atlas():
    rows = 5
    A = np.zeros((rows * TS, 16 * TS, 4)); N = np.zeros_like(A)
    PR = _profiles()

    def put(r, c, img):
        a, n = img
        A[r * TS:(r + 1) * TS, c * TS:(c + 1) * TS] = a
        N[r * TS:(r + 1) * TS, c * TS:(c + 1) * TS] = n

    for v in range(3):
        for m in range(16):
            put(v, m, ground_tile(m, v, PR))
    for k in range(8):
        put(3, k, grass_overlay(k))
    for k in range(3):
        put(3, 8 + k, ceiling_overlay(k))
    for k in range(6):
        put(4, k, platform_tile(k % 3, k // 3))
    meta = {'tile': TS, 'world_tile': TS_WORLD, 'density': DENSITY, 'cols': 16, 'ground_rows': 3, 'overlay_row': 3, 'grass_cols': 8,
            'ceiling_cols': [8, 9, 10], 'platform_row': 4,
            'keys': {'soil': list(KEY_SOIL), 'shade': list(KEY_SHADE), 'lit': list(KEY_LIT), 'edge': list(KEY_EDGE), 'glow': list(KEY_GLOW)},
            'glow': STYLE.get('glow'), 'soil_size': S}
    return A, N, meta


# varsayılan biyom
import biomes as _biomes  # noqa: E402
set_biome(_biomes.BIOMES['otuken']['soil'])
