"""ESKİ (kayıt için): piksel v2 Ötüken. Yerini otuken_ink*.py "mürekkep" ortamı aldı (export_ink.py).
Kararan Ötüken — stil v2 örneği (karo atlası, toprak dokusu, bir paralaks katmanı). v1 dosyaları değişmez.

Toprak (v1: düz bantlar + her yere serpilmiş eş boy çakıl "konfeti"):
  * çarpıtılmış katmanlar (strata) ve her katmanın kendi sertliği: sert kil dışa taşar, humus içe çöker;
    yükseklikten normal + sağ üst ay ışığı ile 7 tonlu gölgelendirme; çıkıntı altında ortam kapanması,
  * az sayıda ama büyük, yontulmuş yüzlü (faset) gömülü kaya: üst kenarı ay ışığı, altında temas gölgesi,
  * seyrek çakıl (tek açık pikselli), ince kökler (koyu çekirdek + ışık tarafında açık kenar),
  * palet: 7 tonlu, gölgeler soğuk mora, ışıklar sıcak toprağa kayar; v1'den geniş değer aralığı.
Karo atlası: soil.py yerleşimi aynen (anahtar renkler, profiller), yalnızca v2 paleti (ay ışığında gümüşlenen ot
uçları, daha geniş tonlu kaya ve kökler).
Arka plan: otuken_3_mid_v2 — üç iç derinlikli orman (uzak sıra pusa gömülü, orta, ön siluet), ağaç kenarlarında
güçlü ay kenar ışığı, sıralar arasında yer sisi, eğik ay hüzmeleri; 96 renk.
"""
import math
import os
import json
import numpy as np
from PIL import Image

import soil
import biomes
from pixkit import pal, hexrgb, fbm
from hdkit import normals_from_height, normal_rgba
from style_v2 import tones
from raster import to_img

S = soil.S                     # 768
LIGHT = np.array([0.55, -0.62, 0.56]); LIGHT /= np.linalg.norm(LIGHT)   # ay sağ üstte (v1 ile aynı yön)

# ------------------------------------------------------------ v2 toprak paleti (karo atlası için soil.set_biome biçiminde)
SOIL_V2 = dict(biomes.BIOMES['otuken']['soil'])
SOIL_V2.update(
    SOIL=pal('#0e0b10', '#1a1419', '#2a2025', '#3a2d2e', '#4d3c38', '#625043'),
    CLAY=pal('#1a0f15', '#2c171d', '#422024', '#57302d', '#6d4136', '#835543'),
    HUMUS=pal('#09080c', '#110e13', '#1a1519', '#241d20', '#2f2627', '#3b312f'),
    GRASS=pal('#081612', '#0e231b', '#163225', '#204430', '#2e593d', '#4a7656', '#86a99a'),
    ROOT=pal('#1a120f', '#2e2119', '#473425', '#634a35'),
    SPECK=pal('#8b8c8c', '#5e6a78', '#a69a86'),
    WOOD=pal('#130e0b', '#221a13', '#33271b', '#463625', '#5b4730', '#73593d'),
    ROCK=[(224, 0.14, 0.50), (22, 0.20, 0.44), (234, 0.18, 0.38), (272, 0.20, 0.50)],
    OUTLINE='#0a080c')


def _ramp7(hexc, **kw):
    return np.array(tones(hexc, **kw))


# katman malzemeleri (7 ton) ve göreli sertlik (yükseklik ofseti)
MATS = {
    'soil': (_ramp7('#3c2e2e', spread=0.95), 0.0),
    'clay': (_ramp7('#5a2f2c', spread=0.95, light_hue=30), 1.4),
    'humus': (_ramp7('#231c20', spread=0.9), -1.2),
    'gravel': (_ramp7('#3a3436', spread=0.9, shadow_hue=240), 0.6),
}
STRATA = [('soil', 120), ('clay', 46), ('soil', 80), ('humus', 54), ('gravel', 40), ('soil', 96), ('clay', 34),
          ('soil', 110), ('humus', 70), ('soil', 118)]          # toplam 768
ROCKS = [_ramp7('#535a68', spread=1.0, shadow_hue=245, light_hue=200, sat_light=0.0, lift=0.7),
         _ramp7('#5c4e44', spread=1.0, light_hue=40, lift=0.6),
         _ramp7('#45485a', spread=1.0, shadow_hue=250, lift=0.7)]
ROOT7 = _ramp7('#5a4231', spread=1.0)


def _wrap_idx(c, r, n=S):
    return np.arange(int(c - r) - 1, int(c + r) + 2) % n


def soil_texture_v2(seed=7):
    rng = np.random.default_rng(seed)
    N = S
    yy, xx = np.mgrid[0:N, 0:N].astype(float)
    # çarpıtılmış katman koordinatı (dikişsiz: gürültü periyodik, katman dizisi N'de döner)
    warp = (fbm(N, N, [384, 192, 96], [1.0, 0.5, 0.25], rng) - 0.5) * 70 + (fbm(N, N, [48, 24], [1.0, 0.5], rng) - 0.5) * 10
    sy = np.mod(yy + warp, N)
    edges = np.cumsum([0] + [t for _, t in STRATA])
    band = np.searchsorted(edges, sy, side='right') - 1
    band = np.clip(band, 0, len(STRATA) - 1)
    # yükseklik: katman sertliği + kenara yakın yuvarlatma + ince kabartı
    hgt = np.zeros((N, N))
    mat_id = np.zeros((N, N), int)
    names = list(MATS.keys())
    for b, (nm, th) in enumerate(STRATA):
        m = band == b
        hgt[m] = MATS[nm][1]
        mat_id[m] = names.index(nm)
    # katman sınırında basamak yumuşaması (2 px) -> belirgin çıkıntı çizgisi
    rel = np.minimum(sy - edges[band], edges[band + 1] - sy)
    hgt -= np.clip(1.0 - rel / 3.0, 0, 1) * 0.8
    relief = fbm(N, N, [96, 48, 24, 12], [1.0, 0.6, 0.35, 0.2], rng)
    hgt += (relief - 0.5) * 3.2
    grit = fbm(N, N, [8, 4], [1.0, 0.6], rng)
    hgt += (grit - 0.5) * np.where(mat_id == names.index('gravel'), 2.0, 0.7)
    # kayalar: yontulmuş yüzlü kubbeler (faset normalleri), az ve büyük
    rock = np.full((N, N), -1)
    rock_h = np.zeros((N, N))
    placed = []
    tries = 0
    while len(placed) < 60 and tries < 1200:
        tries += 1
        cx, cy = rng.uniform(0, N), rng.uniform(0, N)
        r = rng.choice([5, 6, 8, 10, 12, 15, 19], p=[0.18, 0.2, 0.18, 0.16, 0.12, 0.1, 0.06])
        ok = True
        for (px_, py_, pr) in placed:
            dx = min(abs(cx - px_), N - abs(cx - px_)); dy = min(abs(cy - py_), N - abs(cy - py_))
            if math.hypot(dx, dy) < r + pr + 6:
                ok = False
                break
        if not ok:
            continue
        placed.append((cx, cy, r))
        ry = r * rng.uniform(0.62, 0.85)
        rot = rng.uniform(-0.5, 0.5)
        ix = _wrap_idx(cx, r); iy = _wrap_idx(cy, r)
        gx = (np.arange(int(cx - r) - 1, int(cx + r) + 2) + 0.5 - cx)
        gy = (np.arange(int(cy - r) - 1, int(cy + r) + 2) + 0.5 - cy)
        GX, GY = np.meshgrid(gx, gy)
        u = GX * math.cos(rot) + GY * math.sin(rot); v = -GX * math.sin(rot) + GY * math.cos(rot)
        # düzensiz kenar: açıya bağlı yarıçap
        ang = np.arctan2(v, u)
        k = 1.0 + 0.12 * np.sin(ang * 3 + rng.uniform(0, 6)) + 0.07 * np.sin(ang * 5 + rng.uniform(0, 6))
        q = (u / (r * k)) ** 2 + (v / (ry * k)) ** 2
        ins = q <= 1.0
        dome = np.sqrt(np.clip(1 - q, 0, 1))
        flat = np.clip(1 - q * 0.9, 0, 1) ** 0.5
        h = (0.55 * dome + 0.45 * flat) * ry * 0.55 + 2.0
        ri = int(rng.integers(0, len(ROCKS)))
        sub_r = rock[np.ix_(iy, ix)]; sub_h = rock_h[np.ix_(iy, ix)]
        sub_r[ins] = ri * 100 + len(placed)
        sub_h[ins] = h[ins]
        rock[np.ix_(iy, ix)] = sub_r; rock_h[np.ix_(iy, ix)] = sub_h
    # faset normali: kaya içinde yükseklik gradyanını dilimlere yuvarla
    is_rock = rock >= 0
    hgt = np.where(is_rock, np.maximum(hgt, 0) + rock_h, hgt)
    n = normals_from_height(hgt, strength=0.55)
    # kaya normallerini 6 yöne nicemle (yontulmuş taş)
    ra = np.arctan2(n[..., 1], n[..., 0])
    rq = np.round(ra / (math.pi / 3)) * (math.pi / 3)
    rl = np.hypot(n[..., 0], n[..., 1])
    rl = np.where(rl > 0.12, np.clip(rl, 0.35, 0.8), rl * 0.5)
    nr = np.stack([np.cos(rq) * rl, np.sin(rq) * rl, np.sqrt(np.clip(1 - rl * rl, 0.05, 1))], -1)
    n = np.where(is_rock[..., None], nr, n)
    sh = n @ LIGHT
    # ortam kapanması: yakındaki daha yüksek komşular (çıkıntı altı, kaya dibi)
    hb = hgt.copy()
    occ = np.zeros((N, N))
    for dy, dx, w in ((-2, 2, 1.0), (-3, 1, 0.8), (-4, 3, 0.6), (-1, 1, 1.0), (-2, 0, 0.7), (0, 2, 0.5)):
        occ += np.clip(np.roll(np.roll(hb, -dy, 0), -dx, 1) - hb - 0.6, 0, 3) * w
    occ = np.clip(occ / 6.0, 0, 1)
    # tortul çizgileri: katman içinde dalgalı ince bantlar (1 ton koyu/açık), büyük ölçekli ışık lekeleri
    sed = np.mod(sy + (fbm(N, N, [96, 48], [1.0, 0.5], rng) - 0.5) * 14, 15.0)
    brk = fbm(N, N, [64, 32], [1.0, 0.5], rng) > 0.52          # çizgiler kesik kesik görünsün
    sed_t = np.where(sed < 1.0, -1.0, np.where(sed < 2.0, 0.6, 0.0)) * (mat_id != names.index('humus')) * brk
    big = (fbm(N, N, [384, 192, 96], [1.0, 0.6, 0.3], rng) - 0.5) * 2.6
    # ton indeksi
    tone = 3.0 + (sh - 0.62) * 7.5 - occ * 2.4 + (relief - 0.5) * 1.2 + sed_t * 0.9 + big
    out = np.zeros((N, N, 3))
    for i, nm in enumerate(names):
        R = MATS[nm][0]
        m = (mat_id == i) & ~is_rock
        idx = np.clip(np.round(tone[m]).astype(int), 0, 6)
        out[m] = R[idx]
    rid = np.where(is_rock, rock // 100, -1)
    for i, R in enumerate(ROCKS):
        m = rid == i
        t2 = 3.0 + (sh[m] - 0.55) * 8.0 - occ[m] * 1.5
        out[m] = R[np.clip(np.round(t2).astype(int), 0, 6)]
    # kaya kenarı: 1 px koyu kontur (yalnızca alt/sol, ışığa ters), üst/sağ kenara ay parıltısı
    edge = is_rock & ~(np.roll(is_rock, 1, 0) & np.roll(is_rock, -1, 0) & np.roll(is_rock, 1, 1) & np.roll(is_rock, -1, 1))
    up_open = is_rock & ~np.roll(is_rock, 1, 0)
    right_open = is_rock & ~np.roll(is_rock, -1, 1)
    out[edge] *= 0.55
    for i, R in enumerate(ROCKS):
        m = (rid == i) & (up_open | right_open)
        out[m] = R[6] * 0.85 + hexrgb('#b8c8e0') * 0.15
    # temas gölgesi: kaya altında ve sol-altında 2-3 px toprak kararır
    cs = np.zeros((N, N), bool)
    for dy, dx in ((1, 0), (2, -1), (2, 0), (3, -1), (1, -1)):
        cs |= np.roll(np.roll(is_rock, dy, 0), dx, 1)
    cs &= ~is_rock
    out[cs] *= 0.58
    # çakıl: seyrek, 1-2 px, tek açık piksel
    for _ in range(int(700 * (N / 768) ** 2)):
        x, y = int(rng.integers(0, N)), int(rng.integers(0, N))
        if is_rock[y, x]:
            continue
        R = ROCKS[int(rng.integers(0, 3))]
        s2 = int(rng.choice([2, 2, 3, 3, 4]))
        ys_ = np.arange(y, y + s2) % N; xs_ = np.arange(x, x + s2) % N
        out[np.ix_(ys_, xs_)] = R[2]
        out[y % N, (x + s2 - 1) % N] = R[5]
        out[(y + s2) % N, xs_] *= 0.6
    # kökler: yukarıdan aşağı kıvrılan ince çizgiler, ışık tarafında açık kenar
    for _ in range(14):
        x, y = rng.uniform(0, N), rng.uniform(0, N)
        a = math.pi / 2 + rng.uniform(-0.4, 0.4)
        ln = rng.uniform(50, 140)
        w = rng.uniform(2.0, 3.0)
        steps = int(ln)
        for s_ in range(steps):
            a += rng.normal(0, 0.12)
            a = min(max(a, math.pi * 0.25), math.pi * 0.75)
            x += math.cos(a); y += math.sin(a)
            ww = w * (1 - s_ / steps) + 0.4
            xi, yi = int(x) % N, int(y) % N
            if is_rock[yi, xi]:
                break
            out[yi, xi] = ROOT7[1]
            if ww > 1.2:
                out[yi, (xi + 1) % N] = ROOT7[4]
                out[yi, (xi - 1) % N] = ROOT7[0]
            if rng.random() < 0.05:   # yan kök
                bx, by, ba = x, y, a + rng.choice([-1, 1]) * rng.uniform(0.6, 1.1)
                for _k in range(int(rng.uniform(6, 18))):
                    bx += math.cos(ba); by += math.sin(ba); ba += rng.normal(0, 0.15)
                    out[int(by) % N, int(bx) % N] = ROOT7[2]
    # çatlaklar: kayalardan/katman sınırlarından inen kırık çizgiler (koyu yarık + sağda açık dudak)
    for _ in range(9):
        x, y = rng.uniform(0, N), rng.uniform(0, N)
        a = math.pi / 2 + rng.uniform(-0.6, 0.6)
        for s_ in range(int(rng.uniform(25, 70))):
            if rng.random() < 0.18:
                a = math.pi / 2 + rng.uniform(-0.8, 0.8)
            x += math.cos(a); y += math.sin(a)
            xi, yi = int(x) % N, int(y) % N
            if is_rock[yi, xi]:
                break
            out[yi, xi] *= 0.42
            out[yi, (xi + 1) % N] = np.minimum(out[yi, (xi + 1) % N] * 1.35 + 0.02, 1)
    nrm = normal_rgba(n)
    return np.clip(out, 0, 1), nrm, None


# ------------------------------------------------------------ arka plan katmanı: orta orman (v2)
def otuken_mid_v2(seed=10):
    import bgkit as bk
    from bg_hd import _out, OT_L, _wish_tree
    from bgkit import W, H, Layer, mgrid, bay, upx
    rng = np.random.default_rng(seed)

    def r9(h, **kw):
        return np.array(tones(h, n=9, **kw))

    # üç iç derinlik: uzak (pusa gömülü, açık-mavi, düşük kontrast), orta, ön (koyu siluet + güçlü kenar ışığı)
    depths = [
        dict(base=440, n=(18, 36), h=(70, 125), G=r9('#2a3c48', spread=0.4, lift=0.2), T=r9('#222a34', spread=0.35, lift=0.2),
             rim='#5f7d90', fog=0.6, pine=0.55),
        dict(base=462, n=(34, 70), h=(115, 175), G=r9('#16292a', spread=0.7, lift=0.3), T=r9('#191518', spread=0.6, lift=0.3),
             rim='#6f97a6', fog=0.3, pine=0.4),
        dict(base=488, n=(90, 170), h=(190, 270), G=r9('#0d1a16', spread=0.9, lift=0.38), T=r9('#100c0e', spread=0.9, lift=0.4),
             rim='#86b2c2', fog=0.0, pine=0.35),
    ]
    haze = hexrgb('#2a3a4c')
    acc = Layer()
    for di, D in enumerate(depths):
        L = Layer()
        gl = bk.ridge_line(W, D['base'], 10 + di * 4, [480, 240, 120], rng)
        x = rng.uniform(0, 30)
        while x < W:
            b = gl[int(x) % W] + 4
            hgt = rng.uniform(*D['h'])
            if di == 2 and abs(x - 980) < 90:
                x += rng.uniform(*D['n'])
                continue
            rim = hexrgb(D['rim'])
            if rng.random() < D['pine']:
                bk.conifer(L, x, b, hgt, D['G'], OT_L, rng, trunk_ramp=D['T'], rim_col=rim, width=rng.uniform(0.22, 0.3))
            else:
                bk.deciduous(L, x, b, hgt * 0.85, D['G'], D['T'], OT_L, rng, crown_w=rng.uniform(0.5, 0.68), rim_col=rim)
            x += rng.uniform(*D['n'])
        if di == 2:
            _wish_tree(L, 980, gl[980] + 4, rng)
        bk.fill_ground(L, gl + 2, lambda ys, x, c=D['G'][1]: np.broadcast_to(c, (len(ys), 3)))
        # ot yeleleri: ay ışığında gümüşlenen uçlar
        for xg in range(0, W, 2):
            if rng.random() < 0.55:
                hh = int(rng.integers(2, 7 + di * 2))
                s_ = 1 if xg % 4 else -1
                for k in range(hh):
                    c = D['G'][3] if k < hh - 2 else (D['G'][6] if k == hh - 1 else D['G'][5])
                    L.px(xg + (k // 3) * s_, gl[xg] + 1 - k, c)
        rgba = L.rgba
        if D['fog'] > 0:
            m = rgba[..., 3] > 0
            rgba[m, :3] = rgba[m, :3] * (1 - D['fog']) + haze * D['fog']
        # alttan üste: önceki birikim + bu sıra; sıralar arasına yer sisi şeridi
        if di > 0:
            yy, xx = mgrid(H, W)
            fog_y = D['base'] - 18
            a = np.clip(1 - np.abs(yy - fog_y) / 46.0, 0, 1) ** 1.6 * 0.42
            a = np.clip(np.floor(a * 10 + (bay(H, W) - 0.5)) / 10, 0, 1)
            fm = acc.rgba[..., 3] > 0
            acc.rgba[fm, :3] = acc.rgba[fm, :3] * (1 - a[fm, None]) + hexrgb('#4a6074') * a[fm, None]
        top = L.rgba
        res = acc.rgba
        ta = top[..., 3:4]
        res[..., :3] = np.where(ta > 0, top[..., :3], res[..., :3])
        res[..., 3] = np.maximum(res[..., 3], top[..., 3])
    res = acc.rgba
    # ay hüzmeleri: eğik, çok saydam; ağaçların önünde ve arasında
    yy, xx = mgrid(H, W)
    beam = np.zeros((H, W))
    for bx in (260, 720, 1180, 1660):
        t = (xx - bx) + yy * 0.55
        wdt = rng.uniform(18, 34)
        beam = np.maximum(beam, np.clip(1 - np.abs(t) / wdt, 0, 1) * (1 - yy / H) * 0.22)
    beam = np.clip(np.floor(beam * 12 + (bay(H, W) - 0.5)) / 12, 0, 1)
    bc = hexrgb('#9ec0d4')
    vis = res[..., 3] > 0
    res[vis, :3] = res[vis, :3] * (1 - beam[vis, None] * 0.55) + bc * beam[vis, None] * 0.55
    nb = ~vis & (beam > 0)
    res[nb, :3] = bc; res[nb, 3] = beam[nb] * 0.8
    # ruh ışıkları
    for _ in range(22):
        x, y = rng.uniform(0, W), rng.uniform(300, 470)
        acc.px(x, y, hexrgb('#b8fff0')); acc.px(x + 1, y, hexrgb('#5fb8a8'), 0.6); acc.px(x, y + 1, hexrgb('#3f7a72'), 0.5)
    # oyun alanından koyu ve düşük kontrastlı kalsın (v1 kuralı): değer x0.78, hafif soğuk pus
    m = res[..., 3] > 0
    res[m, :3] = res[m, :3] * 0.78 + hexrgb('#1c2232') * 0.08
    return _out(res, n=96)


# ------------------------------------------------------------ dışa aktarım
def export(A):
    from export_assets import save
    # karo atlası: v1 yerleşimi + v2 paleti
    soil.set_biome(SOIL_V2)
    Al, Nm, tmeta = soil.build_ground_atlas()
    soil.set_biome(biomes.BIOMES['otuken']['soil'])
    save(Al, os.path.join(A, 'tiles', 'otuken_v2.png')); save(Nm, os.path.join(A, 'tiles', 'otuken_v2_n.png'))
    json.dump(tmeta, open(os.path.join(A, 'tiles', 'otuken_v2.json'), 'w', encoding='utf-8'), indent=1)
    st, sn, _ = soil_texture_v2()
    save(np.dstack([st, np.ones(st.shape[:2])]), os.path.join(A, 'tiles', 'otuken_v2_soil.png'))
    save(sn, os.path.join(A, 'tiles', 'otuken_v2_soil_n.png'))
    print('tiles otuken_v2', Al.shape, st.shape)
    otuken_mid_v2().save(os.path.join(A, 'bg', 'otuken_3_mid_v2.png'))
    print('bg otuken_3_mid_v2')
