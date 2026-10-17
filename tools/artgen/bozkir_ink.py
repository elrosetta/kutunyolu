"""Bozkır Kurganları, stil v2 "mürekkep" ortamı: alacakaranlıkta uçsuz bucaksız bozkır.

Büyük gök (mor-indigo tepeden yanık turuncu ve altın ufka), ufukta batan güneş, alttan yanan uzun bulut şeritleri;
uzakta Altay karlı sıradağları, dalgalı tepelerde kurganlar, balbal dizileri, keçe yurtlar (kapılarında ocak ışığı,
tepelerinden duman), at sürüsü; ortada büyük kurgan, Orhun yazılı bitig taşı (kaplumbağa kaideli), kurt başlı tuğ,
mavi-ak çaputlu oba taşı (obo); önde rüzgârda yatan altın kılçık otu, iri balballar, yalnız kuru karaağaç.
Hava: savrulan toz tülleri, alçak güneşten yelpaze hüzmeler, hızlı rüzgâr çizgileri. Işık sağdan (güneş).

Çıktılar (export_ink_biyom.py bozkir): assets/bg/bozkir_v2_*.png. Tümü yordamsal.
"""
import math

import numpy as np

import inkkit_ortam as ik
from inkkit_ortam import (INK, Layer, Sk, apply_fog, bezier, blade, blob, c01, fbm, leaf_shape, mix, noise,
                          poly_path, premul, ribbon, smooth_path, smoothstep, trunk)
from ink_biyom import (H, WL, cloud_bands, cloud_masses, fold, fog_amount, grass_field, hills, over, place, ramp, range_layer, rays,
                       veil)
from otuken_ink import balbal, rock

LIGHT = 1.0          # güneş sağda: sırtların / gövdelerin sağ yüzü aydınlık

SKY_STOPS = [
    (0, (38, 28, 60)),
    (170, (62, 40, 82)),
    (320, (112, 62, 98)),
    (430, (176, 92, 88)),
    (510, (222, 136, 86)),
    (565, (246, 182, 112)),
    (612, (252, 214, 150)),
    (650, (236, 178, 118)),
    (720, (190, 128, 92)),
    (840, (132, 84, 76)),
    (1080, (70, 44, 54)),
]
SKY = ramp(SKY_STOPS)
SUN = (1230, 598)            # sabit gök katmanında güneş merkezi (ekran pikseli)
GOLD = (252, 214, 150)
DUST = (238, 190, 132)

GRASS_LIT = (230, 182, 98)
GRASS_MID = (184, 128, 72)
GRASS_SH = (104, 64, 70)
FG_DARK = (34, 16, 30)


# ------------------------------------------------------------------ 0) gök
def layer_sky(seed=1):
    W = 1920
    L = Layer(W, H)
    rgb = np.repeat(ik.hd_lin(SKY)[:, None, :], L.w, 1).copy()
    ys = ik.axis(H)[:, None]
    xs = ik.axis(W)[None, :]
    sx, sy = SUN
    # güneş parıltısı: geniş sıcak hale + ufuk boyunca yayılan şerit
    d = np.hypot((xs - sx) / 760.0, (ys - sy) / 300.0)
    rgb = mix(rgb, c01((255, 200, 128))[None, None, :], (np.exp(-d * d * 2.0) * 0.55)[..., None])
    hb = np.exp(-((ys - sy) / 34.0) ** 2) * np.exp(-((xs - sx) / 1400.0) ** 2)
    rgb = mix(rgb, c01((255, 226, 168))[None, None, :], (hb * 0.6)[..., None])
    # boya dokusu: yumuşak lekeler + yatay fırça izi
    n1 = fbm(W, H, [110, 40, 14], seed)
    n2 = noise(W, H, 0, seed + 7, sx=90, sy=2.5)
    rgb *= (1 + 0.04 * n1[..., None] + 0.03 * n2[..., None])
    L.a = premul(rgb.astype(np.float32), np.ones((L.h, L.w), np.float32))
    # güneş kursu (yarısı uzak dağların ardında kalır) + ince kızıl hale
    s = Sk(W, H)
    s.c.drawCircle(sx, sy, 92, s.paint((255, 214, 150), 0.35, 30))
    s.c.drawCircle(sx, sy, 52, s.paint((255, 236, 196), 1.0, 1.2))
    s.c.drawCircle(sx, sy, 52, s.paint((255, 170, 96), 0.6, 0, 2.5))
    L.over(s.snap())
    # bulutlar: büyük alacakaranlık kümeleri (üstleri gökle karışan mor, altları güneşle yanan turuncu-altın) +
    # ufka yakın ince tabaka şeritleri
    cloud_masses(L, SKY, seed + 3, [(380, 250, 760, 120), (1050, 170, 900, 150), (1720, 280, 620, 100),
                                    (760, 420, 520, 60), (1560, 470, 420, 44)],
                 (70, 44, 90), (128, 72, 110), (232, 120, 92), (255, 210, 150), sun=(0.25, 0.97), alpha=0.97,
                 wrap=False, under_d=(8, 30), billow=0.55, top_fade=0.55)
    cloud_bands(L, SKY, seed + 5, (500, 570), 7, (196, 116, 98), (252, 196, 140), (255, 232, 190), length=(300, 800),
                thick=(5, 11), alpha=0.7, W=W)
    # uzakta süzülen kartallar (ince mürekkep "v")
    s2 = Sk(W, H)
    rng = np.random.default_rng(seed + 11)
    for _ in range(5):
        bx, by = rng.uniform(200, 1700), rng.uniform(220, 460)
        sp = rng.uniform(8, 16)
        fl = rng.uniform(-0.3, 0.3)
        pts = [(bx - sp, by - sp * (0.25 + fl)), (bx - sp * 0.4, by - sp * 0.05), (bx, by + sp * 0.12),
               (bx + sp * 0.4, by - sp * 0.05), (bx + sp, by - sp * (0.25 - fl))]
        s2.path(ribbon(pts, [0.3, 1.6, 1.8, 1.6, 0.3]), (60, 34, 52), 0.8)
    L.over(s2.snap())
    return L


# ------------------------------------------------------------------ öğeler
def mirrored(sk, x, fn, *a, **kw):
    """Ötüken çizicilerini (ışık soldan) x çevresinde aynalayarak çiz: bozkırda ışık sağdan."""
    sk.c.save()
    sk.c.translate(2 * x, 0)
    sk.c.scale(-1, 1)
    fn(sk, x, *a, **kw)
    sk.c.restore()


def yurt(sk, x, base_y, r, felt=(206, 178, 150), shade=(120, 86, 98), band=(80, 44, 46), door=(255, 170, 80),
         ink_a=1.0, ink_w=1.8, light=LIGHT, smoke=True, door_side=0.25):
    """Keçe yurt (otağ): silindir duvar + basık kubbe, kubbe ve duvarda kolan bağları, açık kapıdan ocak ışığı, tepeden
    (tünlükten) ince duman."""
    hw = r * 0.62
    roof = r * 0.58
    wall = [(x - r, base_y), (x - r, base_y - hw), (x + r, base_y - hw), (x + r, base_y)]
    dome = [(x - r * 1.03, base_y - hw)] + [(x + r * 1.03 * math.cos(t), base_y - hw - roof * math.sin(t) ** 0.85)
                                           for t in np.linspace(math.pi, 0, 14)]
    body = smooth_path(dome[:1] + dome[1:-1] + [(x + r * 1.03, base_y - hw), (x + r, base_y), (x - r, base_y)], True, 0.25)
    sk.path(body, felt)
    # gölge tarafı (ışığın tersi)
    sh = [(x - light * r * 0.15, base_y - hw - roof * 0.98)]
    sh += [(x - light * r * 1.03 * abs(math.cos(t)), base_y - hw - roof * math.sin(t) ** 0.85) for t in np.linspace(math.pi / 2 + 0.1, math.pi, 8)]
    sh += [(x - light * r, base_y), (x - light * r * 0.15, base_y)]
    sk.path(smooth_path(sh, True, 0.3), shade, 0.85)
    # kubbe/duvar ayrımı ve kolanlar
    for yy, th in ((base_y - hw, 0.07), (base_y - hw * 0.45, 0.05)):
        sk.path(ribbon([(x - r, yy), (x, yy + r * 0.03), (x + r, yy)], [r * th] * 3), band)
    for k in range(-2, 3):
        t = k / 3.2
        p0 = (x + t * r * 0.3, base_y - hw - roof * 0.96)
        p1 = (x + t * r * 1.05, base_y - hw)
        sk.path(ribbon([p0, ((p0[0] + p1[0]) / 2 + t * r * 0.08, (p0[1] + p1[1]) / 2), p1], [r * 0.02, r * 0.03, r * 0.035]), band, 0.8)
    # tünlük (tepe halkası)
    sk.path(smooth_path([(x - r * 0.2, base_y - hw - roof * 0.95), (x, base_y - hw - roof * 1.06),
                         (x + r * 0.2, base_y - hw - roof * 0.95)], True, 0.4), band)
    # kapı: ışık saçan açık kapı
    dx = x + door_side * r
    dw, dh = r * 0.26, hw * 0.78
    sk.path(poly_path([(dx - dw / 2, base_y), (dx - dw / 2, base_y - dh), (dx + dw / 2, base_y - dh), (dx + dw / 2, base_y)]), door)
    sk.path(poly_path([(dx - dw / 2, base_y), (dx - dw / 2, base_y - dh), (dx + dw / 2, base_y - dh), (dx + dw / 2, base_y)]), door, 0.35, r * 0.18)
    if ink_a > 0:
        sk.path(body, INK, ink_a, 0, ink_w)
    if smoke:
        rng = np.random.default_rng(int(x * 7) % 9999)
        sx0, sy0 = x, base_y - hw - roof * 1.05
        pts = [(sx0 + rng.uniform(-1, 1) + (k ** 1.4) * r * 0.08, sy0 - k * r * 0.35) for k in range(10)]
        sk.path(ribbon(pts, np.linspace(r * 0.06, r * 0.32, 10)), (226, 196, 176), 0.3, r * 0.06)


def kurgan(sk, x, base_y, rx, ry, lit, sh, stones=(118, 104, 100), ink_a=1.0, ink_w=2.2, light=LIGHT, seed=0,
           stele=True, grass=None, rim=None):
    """Kurgan: basık kubbe toprak yığını, tabanında taş halka (kerpiç gibi dizili taşlar), tepesinde küçük dikili taş."""
    rng = np.random.default_rng(seed)
    pts = [(x + rx * math.cos(t), base_y - ry * math.sin(t) ** 0.9) for t in np.linspace(math.pi, 0, 24)]
    body = smooth_path(pts + [(x + rx, base_y + 4), (x - rx, base_y + 4)], True, 0.3)
    sk.path(body, lit)
    shp = [(x - light * rx * 0.05, base_y - ry)] + [(x - light * rx * abs(math.cos(t)), base_y - ry * math.sin(t) ** 0.9)
                                                    for t in np.linspace(math.pi / 2, math.pi, 12)] + [(x - light * rx, base_y + 4), (x, base_y + 4)]
    sk.path(smooth_path(shp, True, 0.3), sh, 0.85, rx * 0.05)
    # ot dokusu: yamaç boyunca kısa darbeler
    gcol = grass or tuple(np.array(lit) * 1.12)
    for _ in range(int(rx * 1.2)):
        t = rng.uniform(0.05, 0.95) * math.pi
        rr = math.sqrt(rng.uniform(0.0, 1.0))
        px = x + rx * math.cos(t) * rr
        py = base_y - ry * (math.sin(t) ** 0.9) * rr ** 0.4 + rng.uniform(0, 4)
        c = gcol if (px - x) * light > 0 else sh
        sk.path(blade(px, py, rng.uniform(3, 9) * rx / 120, rng.uniform(-0.3, 0.6), 1.4 * rx / 160 + 0.5), c, 0.6)
    # taş halka
    for t in np.linspace(math.pi * 1.0, 0.0, int(rx / 7)):
        sx = x + rx * 1.02 * math.cos(t)
        r = rng.uniform(3, 6) * rx / 160 + 1.2
        sk.path(blob(sx, base_y + 1, r * 1.3, r, int(rng.integers(1 << 20)), n=8, jitter=0.2), stones)
        if ink_a > 0:
            sk.path(blob(sx, base_y + 1, r * 1.3, r, int(rng.integers(1 << 20)), n=8, jitter=0.2), INK, ink_a * 0.7, 0, 0.8)
    if stele:
        sw, shh = rx * 0.06 + 1.5, ry * 0.32
        tx = x + rx * 0.08
        ty = base_y - ry * 0.99
        sp = poly_path([(tx - sw, ty + 2), (tx - sw * 0.9, ty - shh), (tx, ty - shh * 1.1), (tx + sw * 0.9, ty - shh), (tx + sw, ty + 2)])
        sk.path(sp, stones)
        if ink_a > 0:
            sk.path(sp, INK, ink_a, 0, ink_w * 0.7)
    if rim is not None:
        # ters ışık: kubbenin güneşe bakan sırtında parlak kenar
        q = np.array([(x + rx * math.cos(t), base_y - ry * math.sin(t) ** 0.9 + 1.5) for t in np.linspace(0.12, 1.45, 18)])
        if light < 0:
            q[:, 0] = 2 * x - q[:, 0]
        sk.path(ribbon(q, np.sin(np.linspace(0, math.pi, 18)) * rx * 0.012 + 0.6), rim, 0.9)
    if ink_a > 0:
        sk.path(smooth_path(pts, False, 0.3), INK, ink_a, 0, ink_w)


def tug(sk, x, base_y, h, wind=1.0, pole=(98, 70, 52), metal=(222, 176, 92), hair=(30, 20, 26), flag=(176, 40, 40),
        ink_a=1.0, ink_w=1.6, seed=0):
    """Kurt başlı tuğ: uzun sırık, tepede altın kurt başı ve mızrak ucu, altında rüzgârda savrulan at kılı püskül ve uzun
    kızıl sancak."""
    rng = np.random.default_rng(seed)
    top = base_y - h
    w = max(2.0, h * 0.018)
    p = poly_path([(x - w, base_y), (x + w, base_y), (x + w * 0.7, top), (x - w * 0.7, top)])
    sk.path(p, pole)
    if ink_a > 0:
        sk.path(p, INK, ink_a, 0, ink_w * 0.8)
    s = h / 220.0
    # sancak (sırığın üst üçte birinden rüzgâra doğru dalgalanır)
    fy = top + 34 * s
    n = 14
    fl = []
    for k in range(n):
        t = k / (n - 1)
        fl.append((x + wind * t * 120 * s, fy + t * 22 * s + math.sin(t * 7 + seed) * 6 * s * t))
    lower = [(px_, py_ + (34 - 22 * t) * s) for (px_, py_), t in zip(fl, np.linspace(0, 1, n))]
    fp = smooth_path(fl + lower[::-1], True, 0.35)
    sk.path(fp, flag)
    sk.path(smooth_path(fl + [(q[0], q[1] + 6 * s) for q in fl[::-1]], True, 0.35), tuple(np.minimum(np.array(flag) * 1.35, 255)), 0.6)
    if ink_a > 0:
        sk.path(fp, INK, ink_a, 0, ink_w)
    # at kılı püskülü: diskten sarkan, rüzgârla savrulan ince koyu iplikler
    dy = top + 18 * s
    for k in range(int(28 * max(0.5, s))):
        a0 = rng.uniform(-1, 1)
        ln = rng.uniform(40, 80) * s
        q = bezier((x + a0 * 6 * s, dy), (x + a0 * 8 * s + wind * ln * 0.25, dy + ln * 0.55),
                   (x + wind * ln * rng.uniform(0.45, 0.8), dy + ln * rng.uniform(0.6, 0.9)), 8)
        sk.path(ribbon(q, np.linspace(2.4 * s + 0.4, 0.3, 8)), hair, rng.uniform(0.75, 1.0))
    disc = smooth_path([(x - 9 * s, dy), (x, dy - 5 * s), (x + 9 * s, dy), (x, dy + 4 * s)], True, 0.4)
    sk.path(disc, metal)
    # kurt başı (yana bakan, ağzı açık) + mızrak ucu
    hx, hy = x, top
    head = smooth_path([(hx - 6 * s, hy + 4 * s), (hx - 7 * s, hy - 8 * s), (hx - 4 * s, hy - 16 * s), (hx - 1 * s, hy - 12 * s),
                        (hx + 4 * s, hy - 13 * s), (hx + 14 * s, hy - 9 * s), (hx + 18 * s, hy - 6 * s), (hx + 10 * s, hy - 4 * s),
                        (hx + 15 * s, hy - 1 * s), (hx + 6 * s, hy + 1 * s), (hx + 2 * s, hy + 6 * s)], True, 0.35)
    sk.path(head, metal)
    sk.path(smooth_path([(hx - 5 * s, hy - 6 * s), (hx + 3 * s, hy - 11 * s), (hx + 12 * s, hy - 8 * s), (hx + 2 * s, hy - 7 * s)], True, 0.4),
            (255, 232, 170), 0.7)
    spear = poly_path([(hx - 2 * s, hy - 12 * s), (hx, hy - 34 * s), (hx + 2 * s, hy - 12 * s)])
    sk.path(spear, (200, 200, 196))
    if ink_a > 0:
        sk.path(head, INK, ink_a, 0, ink_w * 0.8)
        sk.path(spear, INK, ink_a, 0, ink_w * 0.6)
        sk.c.drawCircle(hx + 7 * s, hy - 9 * s, 1.0 * s + 0.3, sk.paint(INK))
        sk.path(disc, INK, ink_a, 0, ink_w * 0.6)


def obo(sk, x, base_y, r, stone=(150, 130, 118), stone_sh=(92, 72, 82), ribbons=((80, 130, 200), (232, 228, 214), (90, 150, 210)),
        wind=1.0, ink_a=1.0, ink_w=1.6, seed=0, light=LIGHT):
    """Oba taşı (obo): üst üste yığılmış taşlardan konik höyük, tepesinde dal demeti ve rüzgârda uçuşan mavi-ak çaputlar
    (yolcular bir taş ekler, Gök Tengri'ye dua bağlar)."""
    rng = np.random.default_rng(seed)
    h = r * 1.15
    cone = smooth_path([(x - r, base_y), (x - r * 0.55, base_y - h * 0.55), (x - r * 0.18, base_y - h),
                        (x + r * 0.2, base_y - h * 0.98), (x + r * 0.6, base_y - h * 0.5), (x + r, base_y)], True, 0.35)
    sk.path(cone, stone_sh)
    # taşlar
    for k in range(int(r * 1.6)):
        t = rng.random()
        yy = base_y - t ** 0.8 * h * 0.95
        half = r * (1 - (base_y - yy) / h) * 0.95
        xx = x + rng.uniform(-half, half)
        rr = rng.uniform(0.09, 0.16) * r * (1.1 - t * 0.4)
        lit_side = (xx - x) * light > -half * 0.2
        c = tuple(np.array(stone) * rng.uniform(0.85, 1.12)) if lit_side else tuple(np.array(stone_sh) * rng.uniform(0.9, 1.15))
        p = blob(xx, yy, rr * 1.3, rr, int(rng.integers(1 << 20)), n=8, jitter=0.2)
        sk.path(p, c)
        if ink_a > 0:
            sk.path(p, INK, ink_a * 0.6, 0, 0.7)
    # dal demeti ve çaput ipleri
    top = (x, base_y - h)
    for k in range(5):
        a = math.radians(-90 + (k - 2) * 12 + rng.uniform(-4, 4))
        ln = h * rng.uniform(0.5, 0.8)
        p2 = (top[0] + math.cos(a) * ln, top[1] + math.sin(a) * ln)
        sk.path(ribbon([top, p2], [max(1.0, r * 0.05), 0.5]), (74, 52, 46))
    for k in range(4):
        a = math.radians(-90 + (k - 1.5) * 18)
        p2 = (top[0] + math.cos(a) * h * 0.65, top[1] + math.sin(a) * h * 0.65)
        end = (x + wind * r * rng.uniform(1.2, 2.0), base_y - rng.uniform(0.05, 0.3) * h)
        line = bezier(p2, ((p2[0] + end[0]) / 2, (p2[1] + end[1]) / 2 + h * 0.12), end, 12)
        sk.path(ribbon(line, [0.6] * 12), (70, 54, 50), 0.8)
        for j in range(1, 11, 2):
            q = line[j]
            col = ribbons[(j + k) % len(ribbons)]
            fl = bezier(q, (q[0] + wind * 5, q[1] + 4), (q[0] + wind * rng.uniform(8, 13), q[1] + rng.uniform(5, 11)), 6)
            sk.path(ribbon(fl, np.linspace(r * 0.07 + 1, r * 0.04 + 0.6, 6)), col)
    if ink_a > 0:
        sk.path(cone, INK, ink_a, 0, ink_w)


RUNES = [  # Orhun (Göktürk) yazısından esinli yalın işaretler: (x, y) birim kare içinde kırık çizgiler
    [[(0.5, 0), (0.5, 1)], [(0.5, 0.35), (0.1, 0.05)], [(0.5, 0.35), (0.9, 0.05)]],
    [[(0.2, 0), (0.2, 1)], [(0.2, 0.2), (0.8, 0.5), (0.2, 0.8)]],
    [[(0.5, 0), (0.5, 1)], [(0.15, 0.3), (0.5, 0.55), (0.85, 0.3)]],
    [[(0.2, 1), (0.5, 0), (0.8, 1)]],
    [[(0.8, 0), (0.2, 0.5), (0.8, 1)]],
    [[(0.3, 0), (0.3, 1)], [(0.7, 0), (0.7, 1)], [(0.3, 0.5), (0.7, 0.5)]],
    [[(0.2, 0.2), (0.5, 0.0), (0.8, 0.2), (0.5, 0.45), (0.5, 1)]],
    [[(0.5, 0), (0.5, 0.6)], [(0.15, 1), (0.5, 0.6), (0.85, 1)]],
    [[(0.2, 0), (0.8, 1)], [(0.8, 0), (0.2, 1)]],
    [[(0.2, 0), (0.2, 1), (0.8, 1)], [(0.2, 0.4), (0.7, 0.4)]],
]


def bitig_tasi(sk, x, base_y, h, stone=(150, 140, 128), stone_sh=(96, 82, 92), ink_a=1.0, ink_w=1.8, seed=0, light=LIGHT,
               turtle=True, rune_a=0.85):
    """Bitig taşı: Orhun yazıtları gibi uzun dikili taş, sivri kemerli tepe, yüzünde dikey satırlarda oyma işaretler;
    kaplumbağa biçimli kaide üstünde."""
    rng = np.random.default_rng(seed)
    w = h * 0.3
    by = base_y - (h * 0.12 if turtle else 0)
    if turtle:
        tb = smooth_path([(x - w * 1.0, base_y), (x - w * 0.95, base_y - h * 0.08), (x - w * 0.4, base_y - h * 0.14),
                          (x + w * 0.5, base_y - h * 0.14), (x + w * 1.05, base_y - h * 0.07), (x + w * 1.35, base_y - h * 0.1),
                          (x + w * 1.45, base_y - h * 0.04), (x + w * 1.2, base_y)], True, 0.35)
        sk.path(tb, stone_sh)
        sk.path(smooth_path([(x - w * 0.6, base_y - h * 0.12), (x + w * 0.4, base_y - h * 0.135), (x + w * 0.9, base_y - h * 0.07),
                             (x - w * 0.6, base_y - h * 0.06)], True, 0.4), stone, 0.7)
        for k in range(5):
            cx_ = x - w * 0.6 + k * w * 0.32
            sk.path(ribbon([(cx_, base_y - h * 0.13), (cx_ + w * 0.12, base_y - h * 0.07)], [0.8, 0.4]), INK, ink_a * 0.6)
        if ink_a > 0:
            sk.path(tb, INK, ink_a, 0, ink_w)
    body = smooth_path([(x - w / 2, by), (x - w / 2 * 1.04, by - h * 0.7), (x - w * 0.42, by - h * 0.82), (x, by - h * 0.88),
                        (x + w * 0.42, by - h * 0.82), (x + w / 2 * 1.04, by - h * 0.7), (x + w / 2, by)], True, 0.2)
    sk.path(body, stone)
    side = poly_path([(x + light * w * 0.5, by), (x + light * w * 0.52, by - h * 0.7), (x + light * w * 0.36, by - h * 0.84),
                      (x + light * w * 0.32, by - h * 0.7), (x + light * w * 0.34, by)])
    sk.path(side, tuple(np.minimum(np.array(stone) * 1.18, 255)), 0.7)
    sh = poly_path([(x - light * w * 0.5, by), (x - light * w * 0.52, by - h * 0.7), (x - light * w * 0.3, by - h * 0.84),
                    (x - light * w * 0.28, by - h * 0.7), (x - light * w * 0.3, by)])
    sk.path(sh, stone_sh, 0.8)
    # kemer tepesinde oyma (iki ejder / kurt kıvrımı yerine yalın kıvrım)
    if ink_a > 0:
        sk.path(smooth_path([(x - w * 0.3, by - h * 0.74), (x, by - h * 0.82), (x + w * 0.3, by - h * 0.74), (x, by - h * 0.77)], True, 0.4),
                INK, ink_a * 0.6, 0, max(0.6, ink_w * 0.5))
        # satırlar
        cols = 4
        cw = w * 0.7 / cols
        gh = cw * 0.8
        for c in range(cols):
            cx_ = x - w * 0.35 + (c + 0.5) * cw
            yy = by - h * 0.7
            while yy < by - gh * 1.5:
                g = RUNES[int(rng.integers(len(RUNES)))]
                for strokes in [g]:
                    for st in strokes:
                        pts = [(cx_ - cw * 0.35 + px_ * cw * 0.7, yy + py_ * gh) for px_, py_ in st]
                        if len(pts) >= 2:
                            sk.path(ribbon(pts, [max(0.5, cw * 0.09)] * len(pts)), INK, ink_a * rune_a * rng.uniform(0.7, 1.0))
                yy += gh * 1.35
        sk.path(body, INK, ink_a, 0, ink_w)


def horses(sk, x, base_y, n, s, col=(70, 44, 52), seed=0):
    """Uzak at sürüsü: küçük siluetler (otlayan / yürüyen)."""
    rng = np.random.default_rng(seed)
    for k in range(n):
        hx = x + k * s * rng.uniform(1.6, 3.2) + rng.uniform(-s, s)
        hy = base_y + rng.uniform(-s * 0.3, s * 0.3)
        f = 1 if rng.random() < 0.5 else -1
        graze = rng.random() < 0.5
        body = smooth_path([(hx - s, hy - s * 0.9), (hx + s, hy - s * 0.95), (hx + s * 1.1, hy - s * 0.6), (hx - s * 1.0, hy - s * 0.55)], True, 0.4)
        sk.path(body, col)
        for lx in (-0.8, -0.5, 0.6, 0.9):
            sk.path(ribbon([(hx + lx * s, hy - s * 0.6), (hx + lx * s + rng.uniform(-0.15, 0.15) * s, hy)], [s * 0.18, s * 0.12]), col)
        if graze:
            nk = [(hx + f * s * 0.9, hy - s * 0.85), (hx + f * s * 1.4, hy - s * 0.4), (hx + f * s * 1.55, hy - s * 0.15)]
        else:
            nk = [(hx + f * s * 0.9, hy - s * 0.85), (hx + f * s * 1.35, hy - s * 1.5), (hx + f * s * 1.7, hy - s * 1.45)]
        sk.path(ribbon(nk, [s * 0.4, s * 0.3, s * 0.22]), col)
        sk.path(ribbon([(hx - f * s, hy - s * 0.85), (hx - f * s * 1.35, hy - s * 0.4)], [s * 0.2, s * 0.08]), col)


def dead_tree(L, x, base_y, h, seed, bark=(84, 58, 60), light=(196, 140, 98), rim=(255, 200, 140), fog=None, ink_w=3.0,
              detail=1.0):
    """Yalnız kuru karaağaç: rüzgârın yatırdığı kalın gövde, çatallanan çıplak dallar (mürekkep ağırlıklı)."""
    rng = np.random.default_rng(seed)
    wid = h * 0.09
    arr, xl, yt = trunk(H, L.w, base_y, x, wid, seed, kind='pine', lean=-0.08, bend=0.4, top_y=base_y - h * 0.62,
                        bark=bark, light=light, rim=rim, ink_w=ink_w, light_side=LIGHT, detail=detail, taper=0.5)
    pad = 300
    sk = Sk(L.w / ik.K + 2 * pad, H)

    def branch(p, ang, ln, wd, depth):
        if depth == 0 or ln < 8:
            return
        n = 8
        end = (p[0] + math.cos(ang) * ln, p[1] + math.sin(ang) * ln)
        mid = ((p[0] + end[0]) / 2 + rng.uniform(-ln, ln) * 0.15, (p[1] + end[1]) / 2 + rng.uniform(-ln, ln) * 0.12)
        q = bezier(p, mid, end, n)
        segs.append((q, np.linspace(wd, wd * 0.55, n)))
        for _ in range(2 if depth > 1 else 3):
            t = rng.uniform(0.5, 1.0)
            j = int(t * (n - 1))
            branch(tuple(q[j]), ang + rng.uniform(-0.75, 0.75), ln * rng.uniform(0.45, 0.7), wd * 0.6, depth - 1)

    segs = []
    ty = base_y - h * 0.6
    cx_top = x + pad + (-0.08) * (base_y - ty) + 0.4 * wid * 0
    for a in (-2.2, -1.75, -1.25, -0.8):
        branch((cx_top, ty + rng.uniform(0, h * 0.08)), a + rng.uniform(-0.15, 0.15), h * rng.uniform(0.28, 0.42), wid * 0.55, 4)
    for _ in range(2):
        y0 = ty + rng.uniform(h * 0.12, h * 0.3)
        branch((cx_top + (y0 - ty) * 0.08, y0), rng.choice([-2.6, -0.5]) + rng.uniform(-0.2, 0.2), h * 0.22, wid * 0.4, 3)
    # önce bütün dalların mürekkebi (kalın), sonra dolgu: çatallar dikişsiz birleşir
    for q, ws in segs:
        sk.path(ribbon(q, ws + 2.4 + ws * 0.12), INK, 0.95)
    for q, ws in segs:
        sk.path(ribbon(q, ws), bark)
    for q, ws in segs:
        sk.path(ribbon(q + [LIGHT * ws[0] * 0.3, 0], np.linspace(ws[0] * 0.25, 0.3, len(q))), rim, 0.45)
    br = sk.snap()
    br = fold(br, int(pad * ik.K), L.w)
    if fog is not None:
        apply_fog(br, 0, SKY, fog)
        apply_fog(arr, int(yt * ik.K), SKY, fog)
    L.over(br)
    L.over_wrap(arr, xl, yt)


def stipa_clumps(sk, y, n, W, s, col, rim=None, seed=0, wind=1.0, pad=0, lean=0.55):
    """Kılçık otu (sorguçlu bozkır otu) öbekleri: ince uzun yapraklar, uçlarında rüzgâra savrulan ak sorguçlar."""
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x0 = rng.uniform(0, W) + pad
        y0 = y + rng.uniform(-6, 10)
        for k in range(int(rng.integers(10, 26))):
            x = x0 + rng.normal(0, 10 * s)
            h = rng.uniform(30, 90) * s
            ln = wind * rng.uniform(0.15, lean)
            if rim is not None and rng.random() < 0.5:
                sk.path(blade(x + 1.2, y0, h, ln, rng.uniform(1.4, 2.6) * s), rim, 0.7)
            sk.path(blade(x, y0, h, ln, rng.uniform(1.4, 2.6) * s, curl=0.5), tuple(np.array(col) * rng.uniform(0.85, 1.2)))
            if rng.random() < 0.45:
                tip = (x + ln * h, y0 - h)
                pl = rng.uniform(18, 40) * s
                q = bezier(tip, (tip[0] + wind * pl * 0.6, tip[1] - pl * 0.05), (tip[0] + wind * pl, tip[1] + pl * 0.3), 8)
                pc = rim if rim is not None else col
                sk.path(ribbon(q, np.sin(np.linspace(0.2, math.pi * 0.95, 8)) * 2.2 * s + 0.4), pc, 0.75)


# ------------------------------------------------------------------ paralaks katmanları
def layer_far(seed=20):
    """Uzak Altay sıradağları: ufukta, güneşin önünde ters ışıkta; güneşe bakan sırtlar ve kar başlıkları kızıl-altın yanar."""
    L = Layer(WL, H)
    rng = np.random.default_rng(seed)
    peaks = []
    x = 0.0
    while x < WL:
        x += rng.uniform(260, 520)
        main_h = rng.uniform(410, 520)
        if abs((x % 1920) - SUN[0]) < 160:
            main_h = rng.uniform(540, 575)      # güneşin önü alçak: güneş kursu yarı görünür
        wl, wr = rng.uniform(240, 420), rng.uniform(240, 420)
        peaks.append((x, main_h, 642, wl, wr))
        for _ in range(int(rng.integers(1, 3))):     # omuz tepeler
            sx = x + rng.uniform(-1, 1) * wl * 0.8
            peaks.append((sx, main_h + rng.uniform(40, 90), 642, wl * rng.uniform(0.5, 0.8), wr * rng.uniform(0.5, 0.8)))
    order = sorted(range(len(peaks)), key=lambda i: peaks[i][1])
    peaks = [peaks[i] for i in order]
    n = len(peaks)
    range_layer(L, SKY, peaks, lambda i: fog_amount(0.6 - 0.2 * i / n, 0.3, 640, 40, top=0.0), seed + 1,
                rock_lit=(128, 86, 120), rock_sh=(96, 68, 110), snow_lit=(255, 200, 170), snow_sh=(150, 122, 168), streak=0.06,
                snow_line=0.2, ink_a=0.0, n_ridges=7, hatch=0.0, rim=None, light=LIGHT, rough=0.3,
                sil_rim=(255, 214, 160), sil_rim_w=2.4, crease=0.5, gully_snow=0.15)
    hills(L, SKY, seed + 2, 652, 26, 4, (186, 126, 104), (136, 90, 104), fog_amount(0.5, 0.2, 640, 30), light=LIGHT)
    return L


def layer_farmid(seed=30):
    """Dalgalı uzak tepeler: kurgan sırtları, balbal dizileri, keçe yurt obası (kapılarında ocak ışığı), at sürüsü."""
    L = Layer(WL, H)
    fog = fog_amount(0.36, 0.3, 650, 40)
    top, xs = hills(L, SKY, seed, 668, 52, 5, (216, 156, 96), (128, 84, 96), fog, light=LIGHT, rim=(255, 214, 150),
                    ink_a=0.35, ink_w=1.4, tex=0.06)
    pad = 300
    sk = Sk(WL + 2 * pad, H)
    rng = np.random.default_rng(seed + 5)
    ty = lambda x: float(np.interp(x % WL, xs, top))
    for kx in (420, 1760, 2900):
        kurgan(sk, kx + pad, ty(kx) + 6, rng.uniform(70, 110), rng.uniform(24, 34), (204, 146, 92), (124, 82, 94),
               ink_a=0.4, ink_w=1.2, seed=int(kx))
    # yurt obası
    for k, (yx, r) in enumerate(((1120, 22), (1172, 17), (1216, 24), (1268, 15), (3290, 20), (3336, 16))):
        yurt(sk, yx + pad, ty(yx) + 4, r, felt=(222, 192, 160), shade=(140, 100, 112), ink_a=0.45, ink_w=1.0,
             door_side=0.3 if k % 2 else -0.3)
    for k in range(6):
        bx = 2050 + k * 26 + rng.uniform(-4, 4)
        mirrored(sk, bx + pad, balbal, ty(bx) + 4, rng.uniform(18, 24), (104, 74, 88), (190, 140, 120), seed + k, ink_a=0.4)
    horses(sk, 640 + pad, ty(640) + 2, 7, 5.5, col=(98, 62, 76), seed=seed)
    horses(sk, 2500 + pad, ty(2500) + 2, 5, 5.0, col=(98, 62, 76), seed=seed + 1)
    arr = fold(sk.snap(), ik.P(pad), ik.P(WL))
    apply_fog(arr, 0, SKY, fog_amount(0.32, 0.2, 650, 40))
    L.over(arr)
    grass_field(L, SKY, seed + 3, 650, 720, 0.25, (226, 168, 100), (150, 96, 90), 4, 10, 1.0, 2.0,
                fog=fog_amount(0.3, 0.2, 660, 30), lean_bias=0.3, fill=False)
    return L


def layer_mid(seed=40):
    """Orta: büyük kurgan, bitig taşı, tuğ, oba taşı, balbal sırası; rüzgârda yatan altın ot."""
    L = Layer(WL, H)
    fog = fog_amount(0.08, 0.16, 700, 30)
    top, xs = hills(L, SKY, seed, 712, 46, 4, (176, 112, 84), (110, 66, 82), fog, light=LIGHT, rim=(255, 214, 150),
                    ink_a=0.7, ink_w=1.8, tex=0.07)
    ty = lambda x: float(np.interp(x % WL, xs, top))
    pad = 400
    sk = Sk(WL + 2 * pad, H)
    rng = np.random.default_rng(seed + 8)
    kurgan(sk, 900 + pad, ty(900) + 8, 330, 128, (150, 96, 80), (92, 56, 74), stones=(120, 92, 96), ink_a=0.85,
           ink_w=2.4, seed=seed + 1, rim=(255, 210, 146), grass=(214, 156, 92))
    for k in range(7):
        bx = 1220 + k * 44 + rng.uniform(-6, 6)
        mirrored(sk, bx + pad, balbal, ty(bx) + 6, rng.uniform(40, 54), (98, 70, 84), (214, 160, 124), seed + 20 + k, ink_a=0.8)
    bitig_tasi(sk, 2140 + pad, ty(2140) + 8, 170, stone=(132, 108, 108), stone_sh=(84, 60, 78), ink_a=0.85, seed=seed + 2)
    tug(sk, 2420 + pad, ty(2420) + 6, 220, wind=1.0, ink_a=0.75, seed=seed + 3)
    tug(sk, 2470 + pad, ty(2470) + 6, 190, wind=1.0, flag=(48, 86, 150), ink_a=0.75, seed=seed + 4)
    obo(sk, 3150 + pad, ty(3150) + 6, 56, ink_a=0.75, seed=seed + 5)
    yurt(sk, 3560 + pad, ty(3560) + 6, 48, ink_a=0.7, ink_w=1.6, door_side=-0.25)
    arr = fold(sk.snap(), ik.P(pad), ik.P(WL))
    apply_fog(arr, 0, SKY, fog_amount(0.1, 0.14, 690, 30))
    L.over(arr)
    for _ in range(8):
        r = rock(int(rng.integers(1 << 30)), rng.uniform(18, 34), rng.uniform(12, 22), base=(120, 86, 90),
                 moss=(196, 140, 90), ink_w=2.2, light_dir=(0.6, -0.8))
        x = rng.uniform(0, WL)
        place(L, r, x, ty(x) + 10, SKY, fog_amount(0.2, 0.2, 700, 30))
    grass_field(L, SKY, seed + 3, 704, 800, 0.5, (226, 166, 96), (110, 66, 76), 5, 16, 1.4, 2.8,
                fog=fog_amount(0.1, 0.25, 705, 26), lean_bias=0.35, ink_tips=0.16, fill=False, rim=(255, 220, 160),
                rim_p=0.25, plumes=0.08)
    return L


def layer_near(seed=50):
    """Yakın: iri balballar, kuru karaağaç, eski kazıklar, at kafatası dikilmiş sırık, kayalar; yoğun kılçık otu."""
    L = Layer(WL, H)
    top, xs = hills(L, SKY, seed, 740, 30, 3, (128, 78, 70), (70, 40, 54), fog_amount(0.02, 0.1, 740, 30),
                    light=LIGHT, rim=(255, 206, 140), ink_a=0.9, ink_w=2.4, tex=0.08)
    ty = lambda x: float(np.interp(x % WL, xs, top))
    dead_tree(L, 2780, ty(2780) + 10, 520, seed + 1, bark=(70, 44, 52), light=(150, 96, 84), fog=fog_amount(0.03, 0.08, 700, 60))
    pad = 400
    sk = Sk(WL + 2 * pad, H)
    rng = np.random.default_rng(seed + 8)
    for k, xb in enumerate((640, 700, 1980, 3420)):
        mirrored(sk, xb + pad, balbal, ty(xb) + 8, rng.uniform(96, 128), (76, 50, 64), (220, 150, 110), seed + 30 + k)
    # eski çit kazıkları ve at kafatası dikilmiş sırık
    for k in range(5):
        px = 1340 + k * 38 + rng.uniform(-6, 6)
        ph = rng.uniform(46, 80)
        pw = rng.uniform(4.5, 7)
        p = poly_path([(px - pw, ty(px) + 8), (px + pw, ty(px) + 8), (px + pw * 0.8, ty(px) - ph), (px, ty(px) - ph - 8), (px - pw * 0.8, ty(px) - ph)])
        sk.path(p, (92, 64, 58))
        sk.path(poly_path([(px + pw * 0.1, ty(px) + 8), (px + pw, ty(px) + 8), (px + pw * 0.8, ty(px) - ph), (px + pw * 0.1, ty(px) - ph)]), (186, 128, 90), 0.6)
        sk.path(p, INK, 1.0, 0, 2.0)
    sx = 3700
    sp = poly_path([(sx - 4, ty(sx) + 8), (sx + 4, ty(sx) + 8), (sx + 3, ty(sx) - 150), (sx - 3, ty(sx) - 150)])
    sk.path(sp, (96, 66, 56))
    sk.path(sp, INK, 1.0, 0, 2.0)
    hy = ty(sx) - 150
    skull = smooth_path([(sx - 10, hy + 8), (sx - 12, hy - 12), (sx - 6, hy - 22), (sx + 6, hy - 20), (sx + 10, hy - 8),
                         (sx + 7, hy + 22), (sx + 2, hy + 30), (sx - 3, hy + 28)], True, 0.35)
    sk.path(skull, (226, 214, 190))
    sk.path(skull, INK, 1.0, 0, 2.0)
    for ex in (-5, 5):
        sk.path(blob(sx + ex, hy - 6, 3, 4, 3, n=8), INK, 0.9)
    sk.path(ribbon([(sx - 2, hy + 12), (sx + 2, hy + 12)], [1.2, 1.2]), INK, 0.8)
    for k in range(3):
        q = bezier((sx, hy + 4), (sx + 14, hy + 30), (sx + 20 + k * 8, hy + 58 + k * 6), 8)
        sk.path(ribbon(q, np.linspace(4, 2, 8)), [(170, 40, 40), (230, 226, 210), (60, 100, 170)][k])
    arr = fold(sk.snap(), ik.P(pad), ik.P(WL))
    apply_fog(arr, 0, SKY, fog_amount(0.04, 0.12, 720, 30))
    L.over(arr)
    for _ in range(7):
        r = rock(int(rng.integers(1 << 30)), rng.uniform(36, 70), rng.uniform(24, 40), base=(106, 72, 78),
                 moss=(176, 120, 80), ink_w=3.0, light_dir=(0.6, -0.8))
        x = rng.uniform(0, WL)
        place(L, r, x, ty(x) + 14, SKY, fog_amount(0.04, 0.15, 730, 30))
    sk2 = Sk(WL + 2 * pad, H)
    ys_ = [ty(x) for x in np.linspace(0, WL, 30)]
    stipa_clumps(sk2, float(np.mean(ys_)) + 18, 26, WL, 1.1, (96, 56, 58), rim=(255, 206, 136), seed=seed + 4, pad=pad)
    arr = fold(sk2.snap(), ik.P(pad), ik.P(WL))
    apply_fog(arr, 0, SKY, fog_amount(0.04, 0.1, 730, 30))
    L.over(arr)
    grass_field(L, SKY, seed + 3, 742, 960, 1.0, (150, 92, 70), (70, 40, 54), 8, 26, 2.0, 4.0,
                fog=fog_amount(0.03, 0.12, 745, 40), dark_strokes=0.32, ink_tips=0.3, lean_bias=0.4, rim=(255, 216, 150),
                rim_p=0.3, plumes=0.03)
    return L


def layer_haze(seed=65):
    """Orta derinlik toz pusu: ufuktaki sıcak toz perdesi, tepeleri yer yer yutar."""
    return veil(WL, SKY, seed, [(640, 70, 0.8), (560, 60, 0.3)], 0.35, DUST, 0.4, sx=(240, 70), sy=(30, 14))


def layer_dust(seed=60):
    """Rüzgârla savrulan alçak toz (sürüklenir): yatay uzun şeritler + ince rüzgâr çizgileri."""
    return veil(WL, SKY, seed, [(720, 60, 0.9), (650, 40, 0.35), (820, 50, 0.4)], 0.45, DUST, 0.45, sx=(160, 50),
                sy=(14, 7), streaks=0.35, streak_sx=300)


def layer_shafts(seed=70):
    """Alçak güneşten yelpaze gibi açılan sıcak hüzmeler (toplamalı)."""
    return rays(1920, seed, 0, (255, 190, 120), n=12, wid=(0.06, 0.16), inten=(0.04, 0.12), origin=SUN,
                fade=(60, 260, 300, 1100), blend=0)


def layer_wind(seed=75):
    """Hızlı rüzgâr çizgileri ve savrulan ot kırıntıları (ince, seyrek, sürüklenir)."""
    W = WL
    rng = np.random.default_rng(seed)
    s = Sk(W, H)
    for _ in range(140):
        x, y = rng.uniform(0, W), rng.uniform(380, 900)
        ln = rng.uniform(80, 340)
        wv = rng.uniform(-6, 6)
        pts = [(x + t * ln, y + math.sin(t * 3.1 + x) * wv) for t in np.linspace(0, 1, 9)]
        for dx in (-W, 0, W):
            s.path(ribbon([(p[0] + dx, p[1]) for p in pts], np.sin(np.linspace(0, math.pi, 9)) * rng.uniform(0.8, 2.2) + 0.1),
                   (255, 226, 176), rng.uniform(0.12, 0.3))
    for _ in range(260):
        x, y = rng.uniform(0, W), rng.uniform(420, 980)
        a = rng.uniform(-0.6, 0.6)
        ln = rng.uniform(4, 11)
        c = (230, 182, 110) if rng.random() < 0.6 else (90, 54, 56)
        for dx in (-W, 0, W):
            s.path(ribbon([(x + dx, y), (x + dx + math.cos(a) * ln, y + math.sin(a) * ln)], [1.2, 0.4]), c, rng.uniform(0.5, 0.9))
    L = Layer(W, H)
    L.a = s.snap()
    return L
