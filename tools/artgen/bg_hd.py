"""Biyom paralaks katmanları, 1.5x piksel yoğunluğu (gök 960x540, diğerleri 1920x540; oyunda 2/3 ölçek).

Gerçekçilik araçları: atmosfer perspektifi (uzak = açık, mavimsi, düşük kontrast), erozyon oluklu dağ
yüzleri, öz-gölgeli hacimli bulutlar, gerçek taç yapılı ağaçlar, ışık hüzmeleri, biyom simgeleri.
Arka planlar oyun alanından daha düşük kontrastlıdır ki karakterler okunabilsin.

HD paketleri: bk.set_scale(N) ile aynı katmanlar N kat ince ızgarada yeniden çizilir (bkz. bgkit.py);
konumlar/boylar mantıksal pikselde, rastgele tüketim N'den bağımsız. bk.S == 1 dalları temel çıktıyı aynen korur.

  otuken   : gece; hasta ay, samanyolu, ay ışığında dağlar, sisli orman sıraları, meşe/çam/kayın, dilek ağacı
  bozkir   : gündüz; kümülüs, Altay silsilesi, uzak yurtlar ve dumanlar, kurganlar, balballar, at sürüsü
  sahmeran : mağara; sarkıt tavan, ışıldayan kristaller, yeraltı gölü ve yansımalar, yılan kabartmalı sütun
  kaf      : karlı şafak; dağ ışıltısı (alpenglow), Kaf'ın dev zirvesi, donmuş çağlayan, karlı ladinler
  tamu     : lav gecesi; alttan aydınlanan kül bulutları, lav çağlayanları, bazalt sütunlar, kaburga kemeri, zincirler
"""
import math
import numpy as np

import hdkit as hk
from hdkit import hexrgb, pal, hramp, bayer, fbm, ridged, profile, BAYER8, to_image, reduce_palette
import bgkit as bk
from bgkit import W, H, SW, SH, Layer, norm, lin, mgrid, bay, nfbm, nridged, upx, thin

PALN = 64   # katman başına renk sınırı


def _out(rgba, n=PALN, alpha_steps=4):
    if n == 0:
        return to_image(rgba)          # gök: zaten titreşimli basamaklı, palet indirme halka yapar
    return to_image(reduce_palette(rgba, n, alpha_steps))


def _pt(L, x, y, c, a=1.0):
    """Işık/kıvılcım noktası: temelde tek piksel, HD'de alt piksel konumlu ince nokta."""
    if bk.S == 1:
        return L.px(x, y, c, a)
    L.dot(x, y, c, a, r=max(1, bk.S // 2))


def _star(L, x, y, c, cross=None):
    """Yıldız (+ isteğe bağlı artı şeklinde ışıltı): temelde px, HD'de ince nokta ve ince ışınlar."""
    if bk.S == 1:
        L.px(x, y, c)
        if cross is not None:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                L.px(x + dx, y + dy, cross)
        return
    if cross is not None:
        cx, cy = math.floor(x) + 0.5, math.floor(y) + 0.5
        w_ = thin() / bk.S
        L.stroke([(cx - 1.6, cy - w_ / 2), (cx + 1.6, cy - w_ / 2)], cross, wid=w_, gap=1e9)
        L.stroke([(cx - w_ / 2, cy - 1.6), (cx - w_ / 2, cy + 1.6)], cross, wid=w_, gap=1e9)
    L.star(x, y, c)


def _fog_layer(col, seed, y0, amt, cells=(480, 240, 120, 60), rise=140.0, top_wisps=0.0):
    rng = np.random.default_rng(seed)
    n = nfbm(W, H, list(cells), rng, aspect=0.32, wrap_y=False)
    yy = lin(H)[:, None].astype(float)
    band = np.clip((yy - y0) / rise, 0, 1) ** 1.3
    a = band * np.clip((n - 0.3) / 0.45, 0, 1) * amt
    if top_wisps > 0:
        n2 = nfbm(W, H, [240, 120, 60], rng, aspect=0.18, wrap_y=False)
        wb = np.exp(-((yy - (y0 - 40)) / 26.0) ** 2)
        a = np.maximum(a, wb * np.clip((n2 - 0.55) / 0.3, 0, 1) * top_wisps)
    rgba = np.zeros((H * bk.S, W * bk.S, 4))
    rgba[..., :3] = hexrgb(col) if isinstance(col, str) else col
    b = bay(H, W)
    rgba[..., 3] = np.clip(np.floor(a * 8 + (b - 0.5) * 0.95) / 8, 0, 1)
    return to_image(rgba)


# =============================================================== ÖTÜKEN (gece)
OT_L = norm([0.55, -0.6, 0.58])      # ay sağ üstte
OT_MOON = (705, 168)


def otuken_sky(seed=5):
    rng = np.random.default_rng(seed)
    img = bk.gradient([(0, '#020309'), (0.18, '#060914'), (0.42, '#0c1424'), (0.62, '#132036'), (0.8, '#1b2c40'), (1.0, '#24394b')], SW, SH)
    yy, xx = mgrid(SH, SW)
    Sx = bk.S
    mx, my = OT_MOON
    d = np.sqrt((xx - mx) ** 2 + ((yy - my) * 1.08) ** 2)
    # samanyolu: ayın karşı tarafında çapraz, soluk, düğümlü bant
    t = (xx * 0.42 - yy) / 1.0
    band = np.exp(-((t - 30) / 70.0) ** 2)
    mw = nfbm(SW, SH, [96, 48, 24, 12], rng, wrap_y=False)
    img += (band * np.clip(mw - 0.38, 0, 1) * 0.16)[..., None] * hexrgb('#8a9cc8')
    dark_lane = band * (np.clip(nfbm(SW, SH, [64, 32, 16], rng, wrap_y=False) - 0.55, 0, 1) * 0.18)
    img -= dark_lane[..., None] * 0.35
    # ay halesi: hasta yeşilimsi gri, iki katman
    glow = np.clip(1 - d / 300, 0, 1) ** 2.2 * 0.42 + np.clip(1 - d / 90, 0, 1) ** 1.5 * 0.25
    img = img + glow[..., None] * (hexrgb('#8ea6a8') - img)
    img = bk.dq(img, 64)
    L = Layer(SW, SH)
    L.rgba[..., :3] = img; L.rgba[..., 3] = 1
    # yıldızlar (ay halesinin dışında, samanyolunda yoğun)
    for _ in range(900):
        x, y = int(rng.integers(0, SW)), int(rng.integers(0, int(SH * 0.62)))
        if d[y * Sx, x * Sx] < 150:
            continue
        p = rng.random()
        if p > band[y * Sx, x * Sx] * 0.8 + 0.35:
            continue
        br = rng.random()
        c = hexrgb('#c9d4ee') if br > 0.8 else (hexrgb('#8a98bb') if br > 0.35 else hexrgb('#4d5a7a'))
        _star(L, x, y, c, hexrgb('#6e7ca0') if br > 0.985 else None)
    # ay: kenar kararması, denizler, kraterler
    R = 34
    mm = d < R
    nd = np.clip(d / R, 0, 1)
    maria = nfbm(SW, SH, [16, 8, 4], rng, wrap_y=False)
    mlum = 0.97 - nd ** 3 * 0.35 - np.clip(maria - 0.47, 0, 1) * 1.5
    mramp = pal('#5d6966', '#76837e', '#919d96', '#aeb8ae', '#c8d0c4', '#dfe5d8', '#eef2e6')
    mc = bk.ramp_pick(mramp, np.clip(mlum, 0, 0.999) * 0.999, bay(SH, SW), 0.8)
    L.rgba[mm, :3] = mc[mm]
    pr = np.random.default_rng(seed + 1)
    for _ in range(14):
        a, rr = pr.uniform(0, math.tau), pr.uniform(0, R * 0.8)
        cx, cy = mx + math.cos(a) * rr, my + math.sin(a) * rr
        cr = pr.uniform(1.5, 4.5)
        dd = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        ring_dark = (dd < cr) & (dd > cr - 1.3) & ((xx - cx) + (yy - cy) < 0) & mm
        ring_lit = (dd < cr + 0.6) & (dd > cr - 0.7) & ((xx - cx) + (yy - cy) > 1) & mm
        L.rgba[ring_dark, :3] = hexrgb('#7c8884')
        L.rgba[ring_lit, :3] = hexrgb('#eef3e8')
    rim = (d < R) & (d > R - 1.2)
    L.rgba[rim, :3] = hexrgb('#b8c2b8')
    # bulutlar: ay ışığında kubbeli küme bulutları (üstü gümüşi), uzakta ince ve soluk
    cl_ramp = pal('#141c2b', '#192235', '#1f2a3f', '#26324a', '#2f3c55', '#3b4a63', '#4f5f78', '#6f8299')
    for (cx, cy, wd, ht, al) in ((190, 120, 230, 34, 0.9), (470, 92, 150, 24, 0.75), (900, 300, 260, 46, 0.95), (300, 300, 200, 30, 0.85),
                                 (620, 372, 300, 24, 0.7), (60, 402, 160, 18, 0.6)):
        near = max(0.0, 1 - math.hypot(cx - mx, cy - my) / 420)
        bk.cumulus(L, cx, cy, wd, ht, cl_ramp, OT_L, rng, puff=(0.12, 0.34), rough=0.3, lift=-0.12 + near * 0.25, alpha=al, squash=0.75,
                   rim_col=hexrgb('#a3b4c2') if near > 0.25 else None)
    # karga sürüsü ayın önünde
    for _ in range(14):
        x, y = pr.integers(560, 840), pr.integers(110, 260)
        bk.bird(L, x, y, hexrgb('#03040a'), span=int(pr.integers(2, 5)), flap=int(pr.integers(-1, 2)))
    return _out(L.rgba, 0)


def otuken_mountains(seed=8):
    rng = np.random.default_rng(seed)
    out = Layer()
    far_ramp = pal('#141c2c', '#1b2538', '#232f45', '#2c3a53', '#374763', '#465674', '#586988')
    far_snow = pal('#3c4862', '#4a5772', '#5a6883', '#6d7b95', '#8290a8', '#98a5ba')
    pk = bk.make_peaks(rng, 9, 400, 90, 230, smin=0.55, smax=1.15)
    far = bk.massif(pk, far_ramp, OT_L, rng, snow_ramp=far_snow, snow_y=250, haze='#1b2738', haze_amt=0.12, haze_bottom=0.6,
                    haze_from=300, rough=4, spur_period=38, lit_edge=hexrgb('#8a98b0'), back_haze=0.45)
    out.rgba[...] = far
    near_ramp = pal('#0c111c', '#111826', '#172031', '#1e293d', '#26334a', '#303f58')
    near_snow = pal('#2c3850', '#36435c', '#424f6a', '#52607a')
    pk2 = bk.make_peaks(rng, 12, 470, 50, 120, smin=0.5, smax=0.9)
    near = bk.massif(pk2, near_ramp, OT_L, rng, snow_ramp=near_snow, snow_y=372, haze='#16212f', haze_amt=0.08, haze_bottom=0.55,
                     haze_from=400, rough=3, spur_period=30, lit_edge=hexrgb('#4c5a72'), back_haze=0.3, gully_snow=12)
    nl = Layer(); nl.rgba[...] = near
    out.over(nl)
    # vadi sisi: dağların eteğinde yatay pus bantları
    yy = lin(H)[:, None]
    n = nfbm(W, H, [320, 160, 80], rng, aspect=0.2, wrap_y=False)
    mist = np.clip((yy - 420) / 90.0, 0, 1) * np.clip((n - 0.25) / 0.5, 0, 1) * 0.6
    bk.apply_haze(out.rgba, '#273647', mist * (out.rgba[..., 3] > 0))
    return _out(out.rgba)


def _treeline(L, base_fn, hmin, hmax, density, ramp, light, rng, kind='mix', rim=None, snow_ramp=None, xstep=(5, 12)):
    x = 0.0
    while x < W:
        h = rng.uniform(hmin, hmax)
        b = base_fn(int(x) % W)
        if kind == 'conifer' or (kind == 'mix' and rng.random() < 0.55):
            bk.conifer(L, x, b + 2, h, ramp, light, rng, rim_col=rim, snow_ramp=snow_ramp, width=rng.uniform(0.26, 0.36))
        else:
            L.sphere(x, b - h * 0.5, h * 0.42, ramp, light, rough=0.55, rng=rng, squash=1.1, edge_cut=0.25, rim_col=rim, lift=-0.05)
            L.sphere(x + h * 0.2, b - h * 0.3, h * 0.36, ramp, light, rough=0.55, rng=rng, squash=1.0, edge_cut=0.25, rim_col=rim, lift=-0.1)
        x += rng.uniform(*xstep) * density


def otuken_far(seed=9):
    """Sisin içinde kademeli orman sıraları: arka sıra açık/puslu, ön sıra koyu."""
    rng = np.random.default_rng(seed)
    out = Layer()
    rows = [
        (378, 26, 46, pal('#25344a', '#2b3b52', '#31435a', '#3a4c63'), '#4a5d74', 0.0),
        (408, 30, 54, pal('#1a2638', '#1f2c40', '#253348', '#2d3c52'), '#3d4e66', 0.0),
        (440, 34, 62, pal('#121b29', '#162030', '#1b2738', '#213041'), '#33445a', 0.0),
    ]
    for i, (base, hmin, hmax, ramp, rim, _) in enumerate(rows):
        L = Layer()
        p = bk.ridge_line(W, base, 22, [480, 240, 120], rng)
        _treeline(L, lambda x, p=p: p[x], hmin, hmax, 0.9, ramp, OT_L, rng, rim=hexrgb(rim))
        bk.fill_ground(L, p + 4, lambda ys, x, c=ramp[0]: np.broadcast_to(c, (len(ys), 3)))
        out.over(L)
        # sıralar arası sis
        yy = lin(H)[:, None]
        n = nfbm(W, H, [240, 120, 60], rng, aspect=0.25, wrap_y=False)
        mist = np.exp(-((yy - (base + 18)) / 22.0) ** 2) * np.clip((n - 0.2) / 0.5, 0, 1) * 0.5
        bk.apply_haze(out.rgba, '#344a5e', mist * (out.rgba[..., 3] > 0))
    # uzak balbal taşları ve kam direği siluetleri bir açıklıkta
    for x in (420, 1460):
        for k in range(3):
            xx = x + k * 14
            out.poly([(xx - 3, 452), (xx - 3, 438), (xx - 1, 434), (xx + 2, 434), (xx + 3, 438), (xx + 3, 452)], hexrgb('#0f1724'))
            out.px(xx + 2, 436, hexrgb('#3a4c62')); out.px(xx + 2, 437, hexrgb('#2c3b50'))
    return _out(out.rgba)


def _wish_tree(L, x, base, rng):
    """Dilek ağacı: yaşlı kayın, dallarına bağlanmış renkli çaputlar."""
    trunk = pal('#0c0a0b', '#171214', '#221a1a', '#2e2421', '#3b2f29', '#4a3c32')
    leaf = pal('#09130f', '#0e1c16', '#14261d', '#1b3226', '#244030', '#30503b')
    bk.deciduous(L, x, base, 150, leaf, trunk, OT_L, rng, crown_w=0.75, sparse=0.35, rim_col=hexrgb('#5c7a74'))
    cols = [hexrgb(c) for c in ('#8a2a2a', '#c8a032', '#2a5a9a', '#e8e0d0', '#3a8a5a', '#a03a7a')]
    for _ in range(26):
        cx = x + rng.uniform(-50, 50); cy = base - 150 * 0.55 + rng.uniform(-30, 10)
        c = cols[int(rng.integers(0, len(cols)))] * 0.62
        ln = int(rng.integers(4, 9))
        if bk.S == 1:
            for k in range(ln):
                L.px(cx + (k // 3), cy + k, c * (0.85 if k % 2 else 1.0))
                L.px(cx + 1 + (k // 3), cy + k, c * 0.7)
        else:
            # HD: rüzgârda hafif kıvrılan bez şerit
            pts = [(cx + k / 3 + math.sin(k * 0.9) * 0.2, cy + k) for k in range(ln)]
            L.stroke([(px_ + 1, py_) for px_, py_ in pts], c * 0.7, gap=1e9)
            L.stroke(pts, [c * (0.85 if k % 2 else 1.0) for k in range(ln)], gap=1e9)


def otuken_mid(seed=10):
    rng = np.random.default_rng(seed)
    out = Layer()
    G = pal('#060d0a', '#0a1510', '#0f1e17', '#15291f', '#1d3628', '#284432', '#35553f')
    TEAL = pal('#061011', '#0a1a1a', '#0f2424', '#15302f', '#1d3d3b', '#284c49')
    RUST = pal('#130b08', '#1f120c', '#2d1a10', '#3c2415', '#4d301b', '#5f3e24')
    TRUNK = pal('#070607', '#0e0b0b', '#161111', '#1f1817', '#2a211e', '#372b26')
    BIRCH = pal('#16161a', '#3a3c42', '#55585e', '#6f7278', '#8a8d92')
    PINE = pal('#050c0a', '#08130f', '#0c1b15', '#11241b', '#183022', '#213d2b')
    rim = hexrgb('#4f6f70')
    gl = bk.ridge_line(W, 478, 16, [480, 240, 120], rng)
    trees = []
    x = 10.0
    while x < W:
        r = rng.random()
        trees.append((x, r))
        x += rng.uniform(36, 80)
    for x, r in trees:
        b = gl[int(x) % W] + 4
        if abs(x - 980) < 90:
            continue
        if r < 0.32:
            bk.conifer(out, x, b, rng.uniform(110, 190), PINE, OT_L, rng, trunk_ramp=TRUNK, rim_col=rim * 0.8, width=rng.uniform(0.24, 0.32))
        elif r < 0.75:
            P = [G, TEAL, RUST][int(rng.integers(0, 3)) if rng.random() < 0.6 else 0]
            bk.deciduous(out, x, b, rng.uniform(100, 165), P, TRUNK, OT_L, rng, crown_w=rng.uniform(0.5, 0.7), rim_col=rim)
        elif r < 0.88:
            # kayın: beyaz gövde, kara halkalar
            h = rng.uniform(120, 170)
            out.tube([(x, b), (x + rng.uniform(-4, 4), b - h * 0.8)], 2.4, 1.4, BIRCH, OT_L)
            for k in range(int(h / 9)):
                yk = b - rng.uniform(5, h * 0.75)
                out.line(x - 2, yk, x + 1, yk + rng.uniform(-1, 1), BIRCH[0])
            bk.deciduous(out, x, b - h * 0.35, h * 0.7, G, BIRCH, OT_L, rng, crown_w=0.45, sparse=0.3, rim_col=rim, branch_r=1.2)
        else:
            bk.bare_tree(out, x, b, rng.uniform(80, 140), TRUNK, OT_L, rng)
    _wish_tree(out, 980, gl[980] + 4, rng)
    # zemin: koyu ot, çalı, eğrelti
    for x in range(0, W, 3):
        b = gl[x]
        if rng.random() < 0.45:
            out.sphere(x + rng.uniform(-1, 1), b - rng.uniform(2, 6), rng.uniform(4, 9), G, OT_L, rough=0.6, rng=rng, squash=0.7, edge_cut=0.3, lift=-0.15)
    bk.fill_ground(out, gl + 2, lambda ys, x: np.broadcast_to(hexrgb('#08100c'), (len(ys), 3)))
    for x in range(0, W):
        if rng.random() < 0.5:
            hh = int(rng.integers(2, 8))
            if bk.S == 1:
                for k in range(hh):
                    out.px(x + (k // 4) * (1 if x % 2 else -1), gl[x] + 1 - k, G[3 if k < hh - 1 else 5])
            else:
                s_ = 1 if x % 2 else -1
                out.stroke([(x + k / 4 * s_, gl[x] + 1 - k) for k in range(hh)], [G[3 if k < hh - 1 else 5] for k in range(hh)],
                           wid=0.75, gap=1e9)
    # ruh ışıkları
    for _ in range(18):
        x, y = rng.uniform(0, W), rng.uniform(300, 460)
        if bk.S == 1:
            out.px(x, y, hexrgb('#9df2e0')); out.px(x + 1, y, hexrgb('#5fb8a8'), 0.6); out.px(x, y + 1, hexrgb('#3f7a72'), 0.5)
        else:
            _glow(out, x + 0.7, y + 0.7, 2.4, '#3f7a72', 0.7)
            _pt(out, x + 0.5, y + 0.5, hexrgb('#9df2e0'))
    # ay hüzmesi: ağaçların arasından soğuk, eğik, çok saydam ışık bantları
    beams = Layer()
    yy, xx = mgrid(H, W)
    for bx in (300, 760, 1240, 1700):
        t = (xx - bx) + (yy - 0) * 0.55
        m = (np.abs(t) < rng.uniform(16, 30)) & (yy < upx(gl)[None, :] - 4)
        a = (1 - yy / H) * 0.14
        beams.rgba[m, :3] = hexrgb('#7fa2b0')
        beams.rgba[m, 3] = a[m]
    beams.rgba[..., 3] = np.clip(np.floor(beams.rgba[..., 3] * 16 + (bay(H, W) - 0.5)) / 16, 0, 1)
    base_ = Layer(); base_.rgba[...] = beams.rgba
    base_.over(out)
    # hüzmeyi ağaçların önüne de hafifçe
    res = out.rgba.copy()
    bm = beams.rgba[..., 3:4]
    vis = res[..., 3:4] > 0
    res[..., :3] = np.where(vis, res[..., :3] * (1 - bm * 0.6) + beams.rgba[..., :3] * bm * 0.6, base_.rgba[..., :3])
    res[..., 3] = np.maximum(res[..., 3], base_.rgba[..., 3])
    # gece mesafesi: hafif soğuk pus, oyun alanından düşük kontrast
    bk.apply_haze(res, '#1a2833', 0.2)
    return _out(res)


def otuken_near(seed=11):
    """Yakın plan: kabuk dokulu kapkara dev gövdeler, sarkan yosun, eğrelti; düşük kontrast."""
    rng = np.random.default_rng(seed)
    out = Layer()
    TR = pal('#030304', '#070607', '#0c0a0b', '#121010', '#191617', '#221e1e', '#2c2828')
    MOSS = pal('#050a08', '#08100c', '#0c1610', '#111d16', '#17261c')
    for x in (120, 760, 1350):
        w = rng.uniform(16, 26)
        pts = [(x + rng.uniform(-3, 3), 560), (x, 400), (x + rng.uniform(-6, 6), 200), (x + rng.uniform(-8, 8), -10)]
        out.tube(pts, w, w * 0.8, TR, OT_L, bark=0.45, rng=rng, rim_col=hexrgb('#34424a'))
        # kırık dal kütükleri
        for k in range(3):
            yk = rng.uniform(60, 330); s_ = rng.choice([-1, 1])
            out.tube([(x + s_ * w * 0.6, yk), (x + s_ * (w + rng.uniform(10, 26)), yk - rng.uniform(6, 20))], w * 0.28, w * 0.14, TR, OT_L)
        # kök yayılımı
        for s in (-1, 1):
            out.tube([(x, 500), (x + s * w * 1.2, 525), (x + s * w * 2.2, 545)], w * 0.5, 2, TR, OT_L)
        # yosun saçakları
        for k in range(8):
            yk = rng.uniform(40, 420)
            xk = x + rng.uniform(-w * 0.7, w * 0.7)
            nj = int(rng.integers(6, 24))
            out.stroke([(xk + math.sin(j * 0.4) * 1.2, yk + j) for j in range(nj)], [MOSS[2 if j % 3 else 3] for j in range(nj)], wid=0.75, gap=1e9)
    # alt kenar: eğrelti ve ot siluetleri
    for x in range(0, W, 2):
        if rng.random() < 0.6:
            hh = int(rng.integers(6, 30))
            lean = rng.uniform(-0.5, 0.5)
            out.stroke([(x + lean * k * k / hh, H - 1 - k) for k in range(hh)], [MOSS[1 if k < hh * 0.6 else 2] for k in range(hh)],
                       wid=0.75, gap=1e9)
    for _ in range(8):
        cx = rng.uniform(0, W)
        for j in range(5):
            a = -math.pi / 2 + (j - 2) * 0.45
            fr_ = []
            for k in range(28):
                t = k / 28
                xx_ = cx + math.cos(a) * k * 1.4 + t * t * 10 * (j - 2)
                yy_ = H - 4 + math.sin(a) * k * 1.4 + t * t * 14
                if bk.S == 1:
                    out.px(xx_, yy_, MOSS[2])
                    if k % 3 == 0:
                        out.px(xx_ + 1, yy_ + 2, MOSS[1]); out.px(xx_ - 1, yy_ + 2, MOSS[1])
                else:
                    fr_.append((xx_, yy_))
            if fr_:
                # HD: eğrelti yaprağı: ince orta damar + iki yana inen yaprakçıklar
                for k in range(0, 28, 3):
                    xx_, yy_ = fr_[k]
                    out.stroke([(xx_, yy_), (xx_ + 1.2, yy_ + 2.2)], MOSS[1], wid=0.6, gap=1e9)
                    out.stroke([(xx_, yy_), (xx_ - 1.2, yy_ + 2.2)], MOSS[1], wid=0.6, gap=1e9)
                out.stroke(fr_, MOSS[2], wid=0.75, gap=1e9)
    return _out(out.rgba, 32)


def otuken_fog(seed=12):
    return _fog_layer('#3f5363', seed, 360, 0.6, rise=150, top_wisps=0.25)


# =============================================================== BOZKIR (gündüz)
BZ_L = norm([0.6, -0.62, 0.5])
BZ_SUN = (790, 118)


def bozkir_sky(seed=21):
    rng = np.random.default_rng(seed)
    img = bk.gradient([(0, '#2459b4'), (0.25, '#3d7bcf'), (0.5, '#6aa5e0'), (0.7, '#a2c9ea'), (0.85, '#d4e2e6'), (1.0, '#ecdcb6')], SW, SH)
    yy, xx = mgrid(SH, SW)
    sx, sy = BZ_SUN
    d = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2)
    glow = np.clip(1 - d / 360, 0, 1) ** 2.3 * 0.7 + np.clip(1 - d / 70, 0, 1) ** 1.2 * 0.4
    img = img + glow[..., None] * (hexrgb('#fff3cf') - img)
    img = bk.dq(img, 64)
    L = Layer(SW, SH)
    L.rgba[..., :3] = img; L.rgba[..., 3] = 1
    for r, c in ((22, '#fff6d8'), (18, '#fffbea'), (14, '#ffffff')):
        L.rgba[d < r, :3] = hexrgb(c)
    # yüksek sirrus çizgileri
    cir = nfbm(SW, SH, [240, 120, 60, 30], rng, aspect=0.08, wrap_y=False)
    band = np.exp(-((yy - 70) / 40.0) ** 2) + np.exp(-((yy - 150) / 25.0) ** 2) * 0.6
    ca = np.clip((cir - 0.56) / 0.2, 0, 1) * band * 0.55
    ca = np.clip(np.floor(ca * 6 + (bay(SH, SW) - 0.5)) / 6, 0, 1)
    L.rgba[..., :3] = L.rgba[..., :3] * (1 - ca[..., None]) + hexrgb('#f4f8fc') * ca[..., None]
    cl = pal('#7d93b5', '#93a8c6', '#aabcd6', '#c2d1e4', '#d9e4f0', '#ebf1f7', '#f8fbfd', '#ffffff')
    for (cx, cy, wd, ht) in ((150, 210, 240, 70), (520, 150, 200, 52), (880, 250, 280, 80), (360, 330, 340, 44), (700, 380, 220, 30),
                             (40, 400, 180, 26)):
        near = max(0.0, 1 - math.hypot(cx - sx, cy - sy) / 500)
        bk.cumulus(L, cx, cy, wd, ht, cl, BZ_L, rng, puff=(0.14, 0.32), rough=0.28, lift=0.05 + near * 0.12, squash=0.8,
                   rim_col=hexrgb('#ffffff'))
    # bozkır kartalı ve uzak kuşlar
    for _ in range(9):
        bk.bird(L, rng.integers(80, 900), rng.integers(80, 300), hexrgb('#2c3550'), span=int(rng.integers(2, 4)), flap=int(rng.integers(-1, 2)))
    ex, ey = 300, 120
    if bk.S == 1:
        for dx in range(-9, 10):
            dy = int(abs(dx) * 0.35) - (1 if abs(dx) > 6 else 0)
            L.px(ex + dx, ey + dy, hexrgb('#2a2620'))
            if abs(dx) < 6:
                L.px(ex + dx, ey + dy + 1, hexrgb('#3e3426'))
        L.px(ex, ey + 2, hexrgb('#2a2620')); L.px(ex + 1, ey - 1, hexrgb('#4a3a28'))
    else:
        # HD: süzülen kartal; aynı kanat açıklığı, uçlarda ayrık birincil tüyler
        def wy(dx):
            ad = abs(dx)
            return ey + 0.5 + ad * 0.35 - max(0.0, ad - 5.5) * 0.45
        dxs = np.linspace(-9.4, 9.4, 39)
        L.stroke([(ex + 0.5 + d, wy(d) + 0.6) for d in dxs if abs(d) < 6.2], hexrgb('#3e3426'), wid=1.1, gap=1e9)
        L.stroke([(ex + 0.5 + d, wy(d)) for d in dxs], hexrgb('#2a2620'), wid=0.9, gap=1e9)
        for s_ in (-1, 1):
            for f_ in range(3):
                bx_ = ex + 0.5 + s_ * (8.0 + f_ * 0.6)
                L.stroke([(bx_, wy(8.0 + f_ * 0.6)), (bx_ + s_ * 1.2, wy(8.0 + f_ * 0.6) - 0.7 + f_ * 0.5)], hexrgb('#2a2620'), wid=0.45, gap=1e9)
        L.stroke([(ex + 0.5, ey + 1.0), (ex + 0.5, ey + 2.9)], hexrgb('#2a2620'), wid=1.0, gap=1e9)
        L.stroke([(ex + 1.2, ey - 0.2), (ex + 1.9, ey - 0.6)], hexrgb('#4a3a28'), wid=0.8, gap=1e9)
    return _out(L.rgba, 0)


def bozkir_far(seed=22):
    """Altay silsilesi (puslu, karlı) + uzak bozkır tepeleri, yurtlar, kurganlar, at sürüsü."""
    rng = np.random.default_rng(seed)
    out = Layer()
    m_ramp = pal('#6f78a8', '#7a84b3', '#8690bd', '#939dc6', '#a0aace', '#aeb7d5')
    m_snow = pal('#c2c9e2', '#d0d6ea', '#dde2f1', '#e8ecf6', '#f4f6fb')
    pk = bk.make_peaks(rng, 13, 385, 50, 150, smin=0.55, smax=1.0)
    mt = bk.massif(pk, m_ramp, BZ_L, rng, snow_ramp=m_snow, snow_y=280, haze='#b7c3dc', haze_amt=0.3, haze_bottom=0.55, haze_from=300,
                   rough=6, spur_period=30, back_haze=0.35, gully_snow=30)
    out.rgba[...] = mt
    # uzak tepeler: üç sıra, uzak olan daha mavi/soluk
    rows = [(372, 22, pal('#9fa486', '#a8ac8c', '#b1b392', '#bab998', '#c3c09e'), 0.36),
            (392, 26, pal('#989469', '#a49d6e', '#afa674', '#baaf7a', '#c4b882'), 0.22),
            (414, 30, pal('#8c8252', '#9a8d58', '#a8985e', '#b4a364', '#c0ad6c'), 0.1)]
    for k, (base, amp, ramp, hz) in enumerate(rows):
        ridge = bk.ridge_line(W, base, amp, [480, 240, 120, 60], rng)
        L = Layer()
        bk.hills(L, ridge, ramp, BZ_L, rng, grass=None, shadows=0.12, depth_dark=0.1, tex=0.06)
        if k == 0:
            for x in rng.uniform(0, W, 5):
                bk.kurgan(L, x, ridge[int(x) % W] + 3, rng.uniform(10, 18), rng.uniform(4, 7), ramp, BZ_L, rng)
        if k == 1:
            felt = pal('#a39b88', '#c2b9a4', '#ddd4bf', '#f1ead8')
            for cx in (330, 1210):
                for j in range(int(rng.integers(2, 4))):
                    xx = cx + j * rng.uniform(16, 24)
                    bk.yurt(L, xx, ridge[int(xx) % W] + 3, rng.uniform(8, 11), felt, rng, smoke=hexrgb('#e8eaee'))
            for _ in range(10):
                hx = 760 + rng.uniform(-60, 60)
                bk.horse(L, hx, ridge[int(hx) % W] + 8 + rng.uniform(0, 6), hexrgb('#4a3a2a'), rng, facing=1 if rng.random() < 0.5 else -1)
        if k == 2:
            for x in rng.uniform(0, W, 4):
                bk.kurgan(L, x, ridge[int(x) % W] + 3, rng.uniform(16, 26), rng.uniform(6, 10), ramp, BZ_L, rng)
        bk.apply_haze(L.rgba, '#c9d2e0', hz * (L.rgba[..., 3] > 0))
        out.over(L)
    return _out(out.rgba)


def bozkir_mid(seed=23):
    """Altın ot tepeleri, büyük kurganlar, sırtta balbal dizisi, rüzgâr yontmuş karaağaç, bulut gölgeleri."""
    rng = np.random.default_rng(seed)
    out = Layer()
    G1 = pal('#6e5e2c', '#806d32', '#937c38', '#a68c40', '#b89c48', '#c9ad54', '#d8be62', '#e6cf78')
    G2 = pal('#5c4e24', '#6c5c2a', '#7d6a30', '#8f7936', '#a1883e', '#b29846', '#c2a852')
    STONE = pal('#5a5650', '#7a756c', '#9a948a', '#bab4a8', '#d4cfc4')
    r1 = bk.ridge_line(W, 440, 44, [640, 320, 160, 80], rng)
    L1 = Layer()
    bk.hills(L1, r1, G1, BZ_L, rng, grass=0.5, streaks=0.0, shadows=0.16, depth_dark=0.22, tex=0.14)
    for x in (260, 1100, 1650):
        bk.kurgan(L1, x, r1[int(x)] + 6, rng.uniform(46, 64), rng.uniform(16, 22), G1, BZ_L, rng, stones=STONE)
    for k in range(7):
        x = 640 + k * 15 + rng.uniform(-3, 3)
        bk.balbal(L1, x, r1[int(x) % W] + 2, rng.uniform(11, 16), STONE)
    LEAF = pal('#2e3a1a', '#3a4a20', '#4a5c28', '#5c6e30', '#70823a', '#879846')
    TRK = pal('#2a1e14', '#3a2a1c', '#4c3824', '#5e472e')
    tx = 1420
    bk.deciduous(L1, tx, r1[tx] + 3, 92, LEAF, TRK, BZ_L, rng, crown_w=0.95, lean=0.25, rim_col=hexrgb('#a8b060'))
    out.over(L1)
    r2 = bk.ridge_line(W, 490, 26, [480, 240, 120], rng)
    L2 = Layer()
    bk.hills(L2, r2, G2, BZ_L, rng, grass=0.7, streaks=0.0, shadows=0.14, depth_dark=0.2, tex=0.16)
    if bk.S == 1:
        for x in range(0, W):
            t = x / W * math.tau
            y = r2[x] + 18 + math.sin(t * 2) * 8
            for k in range(3):
                L2.px(x, y + k, hexrgb('#9a7a4a') if k else hexrgb('#b8955c'))
    else:
        # HD: aynı patika eğrisi, sürekli kenar; tekerlek izleri ince
        road = [(x, r2[x] + 18 + math.sin(x / W * math.tau * 2) * 8) for x in range(0, W)] + [(W, r2[0] + 18)]
        L2.stroke([(x, y + 1) for x, y in road], hexrgb('#9a7a4a'), wid=2.0, gap=1e9)
        L2.stroke(road, hexrgb('#b8955c'), wid=1.0, gap=1e9)
        L2.stroke([(x, y + 1.9) for x, y in road], hexrgb('#8a6c40'), wid=thin() / bk.S, gap=1e9)
    out.over(L2)
    bk.apply_haze(out.rgba, '#dccfa8', 0.06 * (out.rgba[..., 3] > 0))
    return _out(out.rgba)


def bozkir_near(seed=24):
    """Ön plan: sorguçlu otu (Stipa) öbekleri, oyma yüzlü büyük balbal, mavi çaputlu oba (taş yığını)."""
    rng = np.random.default_rng(seed)
    out = Layer()
    GR = pal('#4a3e1c', '#5e4f22', '#74622a', '#8a7432', '#a0863a', '#b49844')
    PLUME = pal('#c8bc9a', '#dcd2b4', '#ece6d2')
    STONE = pal('#46423c', '#5e5a52', '#78736a', '#938d82', '#aaa498')
    for x in range(0, W, 2):
        if rng.random() < 0.55:
            hh = int(rng.integers(10, 44))
            lean = rng.uniform(0.2, 1.2) * (1 if rng.random() < 0.8 else -1)
            out.stroke([(x + lean * (k / hh) * (k / hh) * hh * 0.35, H - 1 - k) for k in range(hh)], [GR[1 + int(k / hh * 3.5)] for k in range(hh)],
                       wid=0.75, gap=1e9)
            if rng.random() < 0.3:
                tx = x + lean * hh * 0.35
                nj = int(rng.integers(5, 12))
                out.stroke([(tx + j * 0.7 * np.sign(lean), H - hh + j) for j in range(nj)], [PLUME[j % 3] for j in range(nj)], wid=0.75, gap=1e9)
    for cx in (500, 1500):
        hgt = 70
        base = H - 4
        bk.balbal(out, cx, base, hgt, pal('#3a3732', '#57534b', '#737066', '#8e897e'))
        out.line(cx - 4, base - hgt * 0.84, cx - 1, base - hgt * 0.83, hexrgb('#2a2824'))
        out.line(cx + 1, base - hgt * 0.83, cx + 4, base - hgt * 0.84, hexrgb('#2a2824'))
        out.line(cx - 3, base - hgt * 0.7, cx + 3, base - hgt * 0.7, hexrgb('#2a2824'))
    ox = 1000
    for k in range(26):
        r = rng.uniform(4, 8)
        out.sphere(ox + rng.uniform(-22, 22) * (1 - k / 30), H - 4 - k * 1.2, r, STONE, BZ_L, rough=0.2, rng=rng, squash=0.7)
    out.tube([(ox, H - 30), (ox + 2, H - 110)], 1.6, 1.0, pal('#3a2a1a', '#5a4026', '#7a5834', '#946e42'), BZ_L)
    # hadaklar: direğe bağlı, rüzgârda sağa savrulan mavi/beyaz bez şeritleri
    for k in range(6):
        y0 = H - 104 + k * 5
        c1 = hexrgb('#2f6ab8') if k % 3 else hexrgb('#e8e4d8')
        c2 = c1 * 0.72
        ln = int(rng.integers(12, 22))
        if bk.S == 1:
            for j in range(ln):
                yy_ = y0 + j * 0.35 + math.sin(j * 0.45 + k) * 1.4
                out.px(ox + 3 + j, yy_, c1); out.px(ox + 3 + j, yy_ + 1, c2)
        else:
            rib = [(ox + 3 + j, y0 + j * 0.35 + math.sin(j * 0.45 + k) * 1.4) for j in range(ln)]
            out.stroke([(x, y + 1) for x, y in rib], c2, gap=1e9)
            out.stroke(rib, c1, gap=1e9)
    bk.apply_haze(out.rgba, '#c8b88e', 0.2 * (out.rgba[..., 3] > 0))
    return _out(out.rgba, 40)


def bozkir_fog(seed=25):
    return _fog_layer('#e6d8b4', seed, 380, 0.38, rise=160, top_wisps=0.15)


# =============================================================== ortak: ışıma, yansıma, sarkıt
def _glow(L, cx, cy, r, col, amt=0.5, steps=6):
    """Basamaklı, titreşimli ışık halesi: opak piksellere eklenir, boşlukta yarı saydam hale olur."""
    xs, ys = L.grid(cx - r, cy - r, cx + r, cy + r)
    if len(ys) == 0:
        return
    X, Y = np.meshgrid(L.c(xs) - cx, L.c(ys) - cy)
    d = np.sqrt(X * X + Y * Y) / r
    a = np.clip(1 - d, 0, 1) ** 2 * amt
    bb = BAYER8[ys[:, None] % 8, xs[None, :] % 8]
    a = np.clip(np.floor(a * steps + (bb - 0.5) * 0.95) / steps, 0, 1)
    c = hexrgb(col) if isinstance(col, str) else np.asarray(col)
    Xi = xs % L.pw
    sub = L.rgba[np.ix_(ys, Xi)]
    op = sub[..., 3:4]
    rgb = np.where(op > 0, np.minimum(1, sub[..., :3] + c * a[..., None]), c)
    alpha = np.where(op[..., 0] > 0, op[..., 0], np.maximum(op[..., 0], a * 0.85))
    sub[..., :3] = rgb
    sub[..., 3] = alpha
    L.rgba[np.ix_(ys, Xi)] = sub


def _stalactite(L, x, top, ln, w, ramp, light, rng, up=False, wet=None):
    """Sarkıt (ya da up=True ise dikit): konik, halkalı, ışık tarafı açık, ıslak parıltı."""
    n = max(3, int(ln / 3))
    pts = []
    for k in range(n + 1):
        t = k / n
        y = top + (ln * t if not up else -ln * t)
        pts.append((x + math.sin(t * 3 + x) * w * 0.15, y))
    L.tube(pts, w, 0.5, ramp, light)
    if wet is not None:
        wp = []
        for k in range(int(ln * 0.6)):
            t = k / ln
            yy = top + (k if not up else -k)
            if rng.random() < 0.55:
                wp.append((x + w * (1 - t) * 0.45, yy))
        L.stroke(wp, wet, wid=0.6, gap=1.05)


def _crystals(L, cx, cy, size, cols, light, rng, n=None, glow=None):
    """Kristal kümesi: altıgen prizmalar, iki yüzlü (ışık/gölge), parlak uç; isteğe bağlı hale."""
    n = n or int(rng.integers(3, 7))
    if glow is not None:
        _glow(L, cx, cy - size * 0.5, size * 2.6, glow, 0.45)
    shard = []
    for k in range(n):
        a = -math.pi / 2 + rng.uniform(-0.75, 0.75)
        ln = size * rng.uniform(0.5, 1.15) * (1.25 if k == 0 else 1.0)
        w = size * rng.uniform(0.12, 0.2)
        shard.append((ln, a, w))
    shard.sort(key=lambda s: -s[0])
    for ln, a, w in shard:
        ca, sa = math.cos(a), math.sin(a)
        px_, py_ = -sa * w, ca * w
        tip = (cx + ca * ln, cy + sa * ln)
        mid = (cx + ca * ln * 0.78, cy + sa * ln * 0.78)
        L.poly([(cx, cy), (mid[0], mid[1]), tip, (mid[0] - px_, mid[1] - py_), (cx - px_, cy - py_)], cols[1])
        L.poly([(cx, cy), (cx + px_, cy + py_), (mid[0] + px_, mid[1] + py_), tip, (mid[0], mid[1])], cols[2])
        L.line(cx, cy, tip[0], tip[1], cols[3])
        L.px(tip[0], tip[1], cols[3]); L.px(tip[0], tip[1] + 1, cols[3])
        L.line(cx - px_, cy - py_, mid[0] - px_, mid[1] - py_, cols[0])


def _reflect(L, y_water, ramp_water, rng, glow_cols=(), strength=0.45, ripple=0.9):
    """Yeraltı gölü: su çizgisinin üstünü ters çevirip kısar, yatay dalga kaymalarıyla bozar."""
    h, w = L.h, L.w
    yw = int(y_water)
    if L.S > 1:
        return _reflect_hd(L, yw, ramp_water, rng, strength, ripple)
    above = L.rgba[:yw].copy()
    for y in range(yw, h):
        k = y - yw
        src = yw - 1 - k
        if src < 0:
            break
        sh = int(round(math.sin(y * 0.9 + k * 0.15) * ripple * (1 + k * 0.02)))
        row = np.roll(above[src], sh, 0)
        base = ramp_water[min(len(ramp_water) - 1, 1 + k // 40)]
        a = row[:, 3:4] * strength * max(0.2, 1 - k / 120)
        L.rgba[y, :, :3] = base * (1 - a) + row[:, :3] * a
        L.rgba[y, :, 3] = 1
        # yatay parıltı çizgileri
        if (y + int(rng.integers(0, 3))) % 5 == 0:
            m = rng.random(w) < 0.12
            L.rgba[y, m, :3] = np.minimum(1, L.rgba[y, m, :3] + 0.05)
    L.rgba[yw, :, :3] = np.minimum(1, L.rgba[yw, :, :3] * 1.3 + 0.03)


def _reflect_hd(L, yw, ramp_water, rng, strength, ripple):
    """_reflect HD sürümü: aynı dalga kaymaları ince satırlarda (alt piksel kayma), parıltılar ince."""
    S_ = L.S
    h, w = L.h, L.w
    above = L.rgba[:yw * S_].copy()
    for y in range(yw, h):
        k = y - yw
        if yw - 1 - k < 0:
            break
        for q in range(S_):
            yp = y * S_ + q
            srcp = yw * S_ - 1 - (yp - yw * S_)
            if srcp < 0:
                break
            kk = (yp - yw * S_) / S_
            yl = yp / S_
            sh = int(round(math.sin(yl * 0.9 + kk * 0.15) * ripple * (1 + kk * 0.02) * S_))
            row = np.roll(above[srcp], sh, 0)
            base = ramp_water[min(len(ramp_water) - 1, 1 + k // 40)]
            a = row[:, 3:4] * strength * max(0.2, 1 - kk / 120)
            L.rgba[yp, :, :3] = base * (1 - a) + row[:, :3] * a
            L.rgba[yp, :, 3] = 1
        if (y + int(rng.integers(0, 3))) % 5 == 0:
            m = rng.random(w) < 0.12
            mf = bk.side(m.astype(float) + 0.5).random(w * S_) < 0.12
            for q in range(thin()):
                yp = y * S_ + q
                L.rgba[yp, mf, :3] = np.minimum(1, L.rgba[yp, mf, :3] + 0.05)
    for q in range(thin()):
        L.rgba[yw * S_ + q, :, :3] = np.minimum(1, L.rgba[yw * S_ + q, :, :3] * 1.3 + 0.03)


# =============================================================== ŞAHMERAN (mağara)
SH_L = norm([0.45, -0.72, 0.55])
SH_ROCK = pal('#030807', '#06100d', '#0a1713', '#0f1f1a', '#152922', '#1c342c', '#25403a')
SH_CRY_T = [hexrgb(c) for c in ('#0e5a50', '#1fae94', '#62e8c8', '#d8fff4')]
SH_CRY_P = [hexrgb(c) for c in ('#3a1e6a', '#7a4ac8', '#b48af0', '#f2e2ff')]


def sahmeran_sky(seed=31):
    rng = np.random.default_rng(seed)
    img = bk.gradient([(0, '#020504'), (0.35, '#06100d'), (0.7, '#0a1915'), (1.0, '#0e211c')], SW, SH)
    # uzak kaya duvarı: katmanlı çatlaklar, çok düşük kontrast
    r = nridged(SW, SH, [96, 48, 24, 12], rng, aspect=0.35, wrap_y=False)
    img = img * (0.82 + r[..., None] * 0.36)
    yy, xx = mgrid(SH, SW)
    # tavandaki yarıktan inen soluk ışık
    hx_ = 300
    shaft = np.clip(1 - np.abs((xx - hx_) - (yy) * 0.18) / 46.0, 0, 1) * np.clip(1 - yy / 520, 0, 1)
    img = img + shaft[..., None] * hexrgb('#2a5a50') * 0.55
    # uzak kristal ışımaları
    for _ in range(9):
        gx, gy, gr = rng.uniform(0, SW), rng.uniform(200, 520), rng.uniform(20, 60)
        d = np.sqrt((xx - gx) ** 2 + (yy - gy) ** 2)
        c = hexrgb('#1a6a5a') if rng.random() < 0.6 else hexrgb('#3a2a6a')
        img = img + (np.clip(1 - d / gr, 0, 1) ** 2 * 0.35)[..., None] * c
    img = bk.dq(img, 64)
    L = Layer(SW, SH)
    L.rgba[..., :3] = img; L.rgba[..., 3] = 1
    # yarık: tepede parlak ağız
    for k in range(30):
        _pt(L, hx_ + rng.uniform(-18, 18), rng.uniform(0, 6), hexrgb('#8ad8c0'))
    # ışıl böcekleri (tavanda yıldız gibi)
    for _ in range(260):
        x, y = rng.uniform(0, SW), rng.uniform(0, 260)
        _pt(L, x, y, hexrgb('#5ad8b0') if rng.random() < 0.3 else hexrgb('#2a7a68'))
    return _out(L.rgba, 0)


def sahmeran_far(seed=32):
    """Uzak mağara: sarkıt perdesi, dikitli kaya sekileri, ışıldayan kristal kümeleri, yansımalı yeraltı gölü."""
    rng = np.random.default_rng(seed)
    out = Layer()
    R = pal('#08130f', '#0c1a15', '#11221c', '#162b24', '#1c352d', '#244038')
    # tavan bandı + sarkıtlar
    top = bk.ridge_line(W, 70, 50, [480, 240, 120, 60], rng)
    if bk.S == 1:
        for x in range(W):
            out.rgba[:int(top[x]), x, :3] = R[1]; out.rgba[:int(top[x]), x, 3] = 1
    else:
        ceil_ = lin(H)[:, None] < upx(top)[None, :] - 0.5
        out.rgba[ceil_, :3] = R[1]; out.rgba[ceil_, 3] = 1
    x = 0.0
    while x < W:
        _stalactite(out, x, top[int(x) % W] - 2, rng.uniform(20, 150) * rng.random() ** 0.5, rng.uniform(3, 9), R, SH_L, rng)
        x += rng.uniform(8, 30)
    # zemin sekileri + dikitler
    fl = bk.ridge_line(W, 400, 60, [480, 240, 120, 60], rng)
    bk.hills(out, fl, R, SH_L, rng, grass=None, depth_dark=0.3, tex=0.08)
    x = 0.0
    while x < W:
        _stalactite(out, x, fl[int(x) % W] + 4, rng.uniform(14, 70), rng.uniform(3, 8), R, SH_L, rng, up=True)
        x += rng.uniform(20, 70)
    cxs = []
    for _ in range(14):
        cx = rng.uniform(0, W)
        cols = SH_CRY_T if rng.random() < 0.6 else SH_CRY_P
        _crystals(out, cx, fl[int(cx) % W] + 6, rng.uniform(14, 28), [c * 0.85 for c in cols], SH_L, rng, glow=cols[1] * 0.7)
        cxs.append((cx, cols[2]))
    bk.apply_haze(out.rgba, '#1a3a33', 0.3 * (out.rgba[..., 3] > 0))
    yw = 432
    _reflect(out, yw, pal('#030a09', '#05110e', '#071613', '#0a1c18'), rng, strength=0.6)
    # kristal ışıklarının sudaki titrek yansıması
    for cx, c in cxs:
        for y in range(yw + 2, min(H, yw + 70)):
            if rng.random() < 0.55 - (y - yw) / 160:
                ww = int(rng.integers(1, 6))
                out.line(cx - ww + rng.uniform(-2, 2), y, cx + ww + rng.uniform(-2, 2), y, c * 0.55)
    return _out(out.rgba)


def _snake_relief(L, cx, y0, y1, ramp, rng):
    """Sütuna oyulmuş yılan kabartması: dolanan gövde (oyuk + ışık kenarı), taçlı baş (Şahmeran)."""
    n = int((y1 - y0) / 2)
    pts = []
    for k in range(n):
        t = k / n
        y = y1 - (y1 - y0) * t
        x = cx + math.sin(t * math.tau * 2.2) * 11
        pts.append((x, y))
    if L.S == 1:
        for (x, y) in pts:
            L.px(x - 2, y, ramp[0]); L.px(x - 1, y, ramp[1]); L.px(x, y, ramp[4]); L.px(x + 1, y, ramp[3]); L.px(x + 2, y, ramp[2])
    else:
        # HD: aynı dolanan gövde; beş tonlu kabartma şeridi, temeldeki gibi satır satır (aralıklı) ama ince satırlarla
        S_ = L.S
        for k in range(len(pts) - 1):
            (xa, ya), (xb, yb) = pts[k], pts[k + 1]
            for q in range(0, int(abs(yb - ya) * S_), 2):
                t = q / max(1.0, abs(yb - ya) * S_)
                x, y = xa + (xb - xa) * t, ya + (yb - ya) * t
                for off, ci in ((-2, 0), (-1, 1), (0, 4), (1, 3), (2, 2)):
                    L.dot(x + off, y, ramp[ci], r=1)
                    for r_ in range(1, S_):
                        L.dot(x + off + r_ / S_, y, ramp[ci], r=1)
    hx_, hy = pts[-1]
    L.sphere(hx_, hy - 4, 5, ramp, SH_L, squash=0.8)
    for dx in (-3, 0, 3):
        L.line(hx_ + dx, hy - 9, hx_ + dx * 1.3, hy - 14, hexrgb('#c8a032'))
    _pt(L, hx_ + 2, hy - 5, hexrgb('#62e8c8')); _pt(L, hx_ - 1, hy - 5, hexrgb('#62e8c8'))


def sahmeran_mid(seed=33):
    """Sütunlar (sarkıt+dikit birleşmesi), ıslak parlama, yılan kabartması, kristaller, yosun."""
    rng = np.random.default_rng(seed)
    out = Layer()
    R = pal('#040a08', '#07110e', '#0b1914', '#10221b', '#162c24', '#1e382e', '#28463a', '#355848')
    WET = hexrgb('#6aa894')
    MOSS = pal('#0a2418', '#12341f', '#1a4628', '#245a32', '#33703e')
    fl = bk.ridge_line(W, 470, 26, [480, 240, 120], rng)
    cols_x = [180, 620, 1060, 1520]
    for i, cx in enumerate(cols_x):
        cx = cx + rng.uniform(-40, 40)
        wtop, wmid, wbot = rng.uniform(26, 40), rng.uniform(10, 18), rng.uniform(28, 44)
        pts = [(cx + rng.uniform(-6, 6), -10), (cx, 120), (cx + rng.uniform(-4, 4), 250), (cx, 380), (cx + rng.uniform(-6, 6), fl[int(cx) % W] + 8)]
        rads = [wtop, wtop * 0.7, wmid, wmid * 1.4, wbot]
        out.tube(pts, 0, 0, R, SH_L, rng=rng, rim_col=WET * 0.8, rr=rads, flow=0.1)
        # ıslak damla izleri
        for k in range(40):
            yy = rng.uniform(0, 440)
            if bk.S == 1:
                out.px(cx + rng.uniform(0.2, 0.7) * wmid, yy, WET)
            else:
                xw = cx + rng.uniform(0.2, 0.7) * wmid
                out.stroke([(xw, yy), (xw, yy + 1.6)], WET, wid=thin() / bk.S, gap=1e9)
        if i == 1:
            _snake_relief(out, cx, 170, 360, R[2:], rng)
        for k in range(int(rng.integers(2, 5))):
            my = rng.uniform(150, 420)
            for j in range(int(rng.integers(6, 16))):
                out.px(cx - wmid * 0.9 + rng.uniform(-2, 2), my + j, MOSS[1 + (j % 3)])
    bk.hills(out, fl, R[:5], SH_L, rng, grass=None, depth_dark=0.35, tex=0.05)
    # ıslak zemin parıltısı ve yosun öbekleri
    for x in range(0, W):
        if rng.random() < 0.25:
            if bk.S == 1:
                out.px(x, fl[x] + rng.uniform(1, 4), WET * 0.7)
            else:
                yw_ = fl[x] + rng.uniform(1, 4)
                out.stroke([(x, yw_), (x + 1.4, yw_)], WET * 0.7, wid=thin() / bk.S, gap=1e9)
    for x in range(0, W, 6):
        if rng.random() < 0.3:
            for j in range(int(rng.integers(3, 9))):
                out.px(x + j, fl[(x + j) % W] - (1 if j % 3 else 0), MOSS[2 + (j % 2)])
    for _ in range(10):
        cx = rng.uniform(0, W)
        cols = SH_CRY_T if rng.random() < 0.55 else SH_CRY_P
        _crystals(out, cx, fl[int(cx) % W] + 5, rng.uniform(26, 48), cols, SH_L, rng, glow=cols[1] * 0.9)
    # tavandan sarkan ışıl iplikleri
    for _ in range(40):
        x = rng.uniform(0, W)
        ln = rng.uniform(20, 120)
        if bk.S == 1:
            for k in range(int(ln)):
                if k % 6 == 0:
                    out.px(x, k, hexrgb('#5ad8b0'))
                elif k % 2 == 0:
                    out.px(x, k, hexrgb('#1a3a32'), 0.6)
        else:
            # HD: sürekli ince iplik, üstünde ışıl damlacıklar
            out.stroke([(x + 0.5, 0), (x + 0.5, int(ln) - 1)], hexrgb('#1a3a32'), 0.6, wid=thin() / bk.S, gap=1e9)
            for k in range(0, int(ln), 6):
                _pt(out, x + 0.5 - 0.25, k + 0.25, hexrgb('#5ad8b0'))
    bk.apply_haze(out.rgba, '#123028', 0.12 * (out.rgba[..., 3] > 0))
    return _out(out.rgba)


def sahmeran_near(seed=34):
    rng = np.random.default_rng(seed)
    out = Layer()
    R = pal('#010302', '#030705', '#050b08', '#08100c', '#0c1611', '#111d17')
    for x in (90, 700, 1240, 1760):
        _stalactite(out, x + rng.uniform(-30, 30), -6, rng.uniform(120, 240), rng.uniform(22, 36), R, SH_L, rng, wet=hexrgb('#1e3a32'))
        for k in range(3):
            _stalactite(out, x + rng.uniform(-70, 70), -6, rng.uniform(40, 110), rng.uniform(8, 14), R, SH_L, rng)
    # alt kenar: yuvarlak, ıslak kaya yığınları
    for x in (400, 1000, 1500):
        for k in range(5):
            out.sphere(x + rng.uniform(-50, 50), H + rng.uniform(-10, 14), rng.uniform(16, 34), R, SH_L, rough=0.25, rng=rng, squash=0.7,
                       rim_col=hexrgb('#16302a'))
    # kökler ve ışıyan spor damlaları
    for _ in range(14):
        x = rng.uniform(0, W)
        ln = rng.uniform(40, 200)
        xx = x
        rp = []
        for k in range(int(ln)):
            xx += rng.uniform(-0.4, 0.4)
            if bk.S == 1:
                out.px(xx, k, R[3]); out.px(xx + 1, k, R[2])
            else:
                rp.append((xx, k))
        if rp:
            out.stroke([(a + 1, b) for a, b in rp], R[2], gap=1e9)
            out.stroke(rp, R[3], gap=1e9)
        if bk.S == 1:
            out.px(xx, ln, hexrgb('#3fd0a8')); out.px(xx, ln + 1, hexrgb('#1a6a58'))
        else:
            _glow(out, xx + 0.5, ln + 1.0, 2.2, '#1a6a58', 0.8)
            out.stroke([(xx + 0.2, ln), (xx + 0.2, ln + 1.2)], hexrgb('#3fd0a8'), wid=0.6, gap=1e9)
    return _out(out.rgba, 24)


def sahmeran_fog(seed=35):
    return _fog_layer('#2a6458', seed, 360, 0.45, rise=150, top_wisps=0.2)


# =============================================================== KAF DAĞI (karlı şafak)
KF_L = norm([0.8, -0.38, 0.46])
KF_SUN = (640, 440)


def kaf_sky(seed=41):
    rng = np.random.default_rng(seed)
    img = bk.gradient([(0, '#151a3e'), (0.25, '#2c2c5e'), (0.48, '#5a4880'), (0.66, '#a0628c'), (0.8, '#e08a84'), (0.92, '#f6b886'), (1.0, '#ffd8a4')], SW, SH)
    yy, xx = mgrid(SH, SW)
    sx, sy = KF_SUN
    d = np.sqrt((xx - sx) ** 2 + ((yy - sy) * 1.3) ** 2)
    glow = np.clip(1 - d / 420, 0, 1) ** 2.2 * 0.6
    img = img + glow[..., None] * (hexrgb('#ffe2b0') - img)
    img = bk.dq(img, 72)
    L = Layer(SW, SH)
    L.rgba[..., :3] = img; L.rgba[..., 3] = 1
    for r, c in ((30, '#ffe8c0'), (25, '#fff2d8'), (20, '#fffaf0')):
        L.rgba[np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2) < r, :3] = hexrgb(c)
    # sönmekte olan yıldızlar
    for _ in range(200):
        x, y = int(rng.integers(0, SW)), int(rng.integers(0, 170))
        _star(L, x, y, hexrgb('#c8c8f0') if rng.random() < 0.3 else hexrgb('#7a7ab0'))
    # alttan aydınlanan bulutlar: güneş tarafı pembe-altın
    cl = pal('#3a3268', '#4e3e78', '#6a4c88', '#8c5a90', '#b8708e', '#e0908a', '#f8b890', '#ffe0b8')
    for (cx, cy, wd, ht) in ((140, 160, 260, 44), (560, 110, 300, 40), (860, 230, 220, 50), (330, 300, 360, 36), (760, 360, 280, 28)):
        bk.cumulus(L, cx, cy, wd, ht, cl, norm([0.3, 0.6, 0.6]), rng, puff=(0.14, 0.3), rough=0.3, lift=0.0, squash=0.7)
    return _out(L.rgba, 0)


def kaf_far(seed=42):
    """Kaf Dağı: devasa ana zirve + silsile; ışık yüzleri pembe-altın (dağ ışıltısı), gölgeler mavi-mor; bulut kuşağı."""
    rng = np.random.default_rng(seed)
    out = Layer()
    rock = pal('#2e2a52', '#3a3462', '#4a4072', '#5c4e80', '#76608c', '#946e90')
    snow = pal('#6a6aa8', '#8480bc', '#a49ad0', '#c8b4dc', '#f0c4c8', '#ffd8c4', '#fff0e0')
    pk = bk.make_peaks(rng, 10, 430, 80, 190, smin=0.6, smax=1.15)
    pk.insert(0, (980.0, 40.0, 0.95, 0.85))       # Kaf'ın ana zirvesi (en arkada, en yüksek)
    mt = bk.massif(pk, rock, KF_L, rng, snow_ramp=snow, snow_y=380, haze='#b88aa8', haze_amt=0.06, haze_bottom=0.55, haze_from=330,
                   rough=5, spur_period=32, back_haze=0.12, gully_snow=40, lit_edge=hexrgb('#ffe8d8'))
    out.rgba[...] = mt
    # ana zirvenin belinde bulut kuşağı
    cl = pal('#8a7aa8', '#a08cb8', '#bc9ec4', '#d8b2c8', '#f0c8cc', '#ffe0d8')
    for k in range(5):
        bk.cumulus(out, 980 + (k - 2) * 120 + rng.uniform(-20, 20), 250 + rng.uniform(-10, 10), 180, 26, cl, KF_L, rng, puff=(0.15, 0.32),
                   rough=0.3, squash=0.7, alpha=0.85)
    return _out(out.rgba)


def kaf_mid(seed=43):
    """Karlı yamaçlar, karla yüklü ladin ormanı, uçurumdan sarkan donmuş çağlayan."""
    rng = np.random.default_rng(seed)
    out = Layer()
    SN = pal('#5a5a92', '#6e6ca4', '#8682b6', '#a29ac6', '#c2b4d4', '#e2cede', '#f6e6ea')
    SP = pal('#0e1a26', '#122230', '#182c3a', '#1e3644', '#26424e', '#305058')
    SPS = pal('#8a8ac0', '#b0aad4', '#d8cce4', '#f4eaf2')
    ROCK = pal('#1e1c34', '#2a2642', '#363050', '#443c5e', '#544a6c', '#6a5a7a')
    ICE = pal('#4a6aa8', '#6a8cc4', '#8eb0dc', '#b4d0ee', '#daeefa', '#ffffff')
    r1 = bk.ridge_line(W, 420, 70, [640, 320, 160, 80], rng)
    # düz tepeli uçurum + donmuş çağlayan
    cx = 1300
    xs_ = np.arange(W)
    dxs = ((xs_ - cx + W / 2) % W) - W / 2
    plateau = 228 + np.clip(np.abs(dxs) - 95, 0, None) * 1.6 + (fbm(W, 1, [24, 12, 6], rng, wrap_y=False)[0] - 0.5) * 10
    plateau = np.where(np.abs(dxs) < 200, plateau, H + 10)
    CL = Layer()
    bk.hills(CL, plateau, ROCK, KF_L, rng, grass=None, depth_dark=0.1, tex=0.14)
    # tepede kar örtüsü
    if bk.S == 1:
        for x in range(W):
            if plateau[x] < H:
                for k in range(int(3 + (x * 7 % 5))):
                    CL.px(x, plateau[x] + k, SN[6 - min(k, 3)])
    else:
        # HD: aynı kalınlıkta kar örtüsü, kalınlık sütundan sütuna yumuşak değişir
        S_ = bk.S
        pu = upx(plateau)
        dep = upx(np.array([3 + (x * 7 % 5) for x in range(W)], float))
        sn = np.asarray(SN)
        for xp in range(W * S_):
            x = xp // S_
            if plateau[x] >= H or pu[xp] >= H:
                continue
            y0p = int(math.floor(pu[xp] * S_))
            r = np.arange(int(dep[xp] * S_))
            k = np.minimum(r // S_, 3)
            rows = y0p + r
            ok = (rows >= 0) & (rows < H * S_)
            CL.rgba[rows[ok], xp, :3] = sn[6 - k[ok]]
            CL.rgba[rows[ok], xp, 3] = 1
    # uçurum yüzünde dikey çatlaklar ve kaya sütunları
    for _ in range(40):
        x0 = cx + rng.uniform(-150, 150)
        if plateau[int(x0) % W] >= H:
            continue
        y0 = plateau[int(x0) % W] + rng.uniform(4, 30)
        ln = rng.uniform(20, 120)
        if bk.S == 1:
            for k in range(int(ln)):
                xx_ = x0 + math.sin(k * 0.2) * 0.8
                if CL.rgba[int(min(H - 1, y0 + k)), int(xx_) % W, 3] > 0:
                    CL.px(xx_, y0 + k, ROCK[0]); CL.px(xx_ + 1, y0 + k, ROCK[4])
        else:
            # HD: ince çatlak (koyu) + sağında ince ışık dudağı; yalnızca kaya üstünde
            S_ = bk.S
            ks = np.arange(int(ln) * S_) / S_
            cp = [(x0 + math.sin(k * 0.2) * 0.8, y0 + k) for k in ks]
            cp = [(a, b) for a, b in cp if CL.rgba[int(min(H * S_ - 1, b * S_)), int(a * S_) % (W * S_), 3] > 0]
            w_ = thin() / S_
            CL.stroke([(a + w_, b) for a, b in cp], ROCK[4], wid=w_, gap=2.0 / S_)
            CL.stroke(cp, ROCK[0], wid=w_, gap=2.0 / S_)
    out.over(CL)
    for k in range(22):
        x0 = cx - 34 + k * 3.1 + rng.uniform(-1, 1)
        ln = rng.uniform(70, 200) * (1 - abs(k - 11) / 16)
        out.tube([(x0, plateau[int(x0) % W] + 2), (x0 + rng.uniform(-2, 2), plateau[int(x0) % W] + 2 + ln)], rng.uniform(2.0, 3.6), 0.7, ICE, KF_L)
    # çağlayan dibinde buz birikintisi
    for k in range(14):
        out.sphere(cx + rng.uniform(-50, 50), 420 + rng.uniform(-6, 6), rng.uniform(6, 14), ICE, KF_L, rough=0.2, rng=rng, squash=0.5)
    bk.hills(out, r1, SN, KF_L, rng, grass=None, depth_dark=0.25, tex=0.06, shadows=0.08)
    x = 0.0
    while x < W:
        if abs(((x - cx + W / 2) % W) - W / 2) > 60:
            hgt = rng.uniform(40, 100)
            bk.conifer(out, x, r1[int(x) % W] + rng.uniform(6, 40), hgt, SP, KF_L, rng, snow_ramp=SPS, width=0.3, rim_col=hexrgb('#f0b8b0'))
        x += rng.uniform(14, 42)
    r2 = bk.ridge_line(W, 488, 22, [480, 240, 120], rng)
    L2 = Layer()
    bk.hills(L2, r2, SN, KF_L, rng, grass=None, depth_dark=0.2, tex=0.05)
    for x in range(0, W, 3):
        if rng.random() < 0.08:
            L2.sphere(x, r2[x] + 2, rng.uniform(4, 9), ROCK, KF_L, rough=0.3, rng=rng, squash=0.6)
    out.over(L2)
    bk.apply_haze(out.rgba, '#a888b4', 0.1 * (out.rgba[..., 3] > 0))
    return _out(out.rgba)


def kaf_near(seed=44):
    rng = np.random.default_rng(seed)
    out = Layer()
    SP = pal('#0e1222', '#13182c', '#191f36', '#1f2740', '#262f4a')
    SPS = pal('#56568a', '#6e6ca0', '#8a86b6', '#a8a2c8')
    for x in (60, 820, 1380):
        bk.spruce_big(out, x + rng.uniform(-40, 40), H + 30, rng.uniform(420, 560), SP, KF_L, rng, snow_ramp=SPS, width=0.3,
                      trunk_ramp=pal('#0a0a14', '#14121e', '#1e1a28', '#2a2432'))
    ICE = pal('#2a3a64', '#3a5084', '#5270a4', '#7494c4', '#a0bce0')
    for x in (500, 1100, 1700):
        for k in range(4):
            out.tube([(x + k * 9 + rng.uniform(-3, 3), H + 2), (x + k * 9 + rng.uniform(-6, 6), H - rng.uniform(40, 110))], rng.uniform(4, 7), 0.6, ICE, KF_L)
    # kar birikintisi
    yy = np.arange(H)[:, None]
    dr = bk.ridge_line(W, H - 6, 16, [240, 120, 60], rng)
    bk.hills(out, dr, pal('#3a3a64', '#4a4878', '#5c588a', '#706a9c', '#8680ae'), KF_L, rng, grass=None, tex=0.04)
    return _out(out.rgba, 32)


def kaf_fog(seed=45):
    return _fog_layer('#d8cce8', seed, 360, 0.42, rise=170, top_wisps=0.3)


# =============================================================== TAMU (Erlik'in ülkesi)
TM_L = norm([0.25, 0.7, 0.6])            # ışık alttan (lav)
TM_LS = norm([0.7, -0.3, 0.6])           # yüzey yönleri için yan ışık


def tamu_sky(seed=51):
    rng = np.random.default_rng(seed)
    img = bk.gradient([(0, '#040102'), (0.3, '#0b0304'), (0.55, '#170605'), (0.78, '#300c07'), (0.92, '#5a1a0a'), (1.0, '#7a2a0e')], SW, SH)
    yy, xx = mgrid(SH, SW)
    # tutulmuş kara güneş: kapkara disk, ince kor halka, dışa taşan kızıl taç
    ex, ey = 240, 160
    d = np.sqrt((xx - ex) ** 2 + (yy - ey) ** 2)
    corona = np.clip(1 - (d - 28) / 120, 0, 1) ** 2.4 * (d > 28) * 0.55
    ray = (np.sin(np.arctan2(yy - ey, xx - ex) * 9) * 0.5 + 0.5) * np.clip(1 - (d - 28) / 60, 0, 1) * (d > 28) * 0.25
    img = img + (corona + ray)[..., None] * (hexrgb('#c8401a') - img)
    img = bk.dq(img, 64)
    L = Layer(SW, SH)
    L.rgba[..., :3] = img; L.rgba[..., 3] = 1
    L.rgba[d < 28, :3] = hexrgb('#050102')
    L.rgba[(d < 29.5) & (d >= 27.5), :3] = hexrgb('#ff9a40')
    L.rgba[(d < 31) & (d >= 29.5), :3] = hexrgb('#c8401a')
    # kül bulutları: koyu gövde, alt yüzleri lav ışığıyla turuncu
    cl = pal('#070303', '#0e0505', '#160807', '#200b08', '#2e100a', '#44180c', '#6a2810', '#9a4214')
    for (cx, cy, wd, ht) in ((120, 270, 300, 46), (520, 220, 360, 54), (860, 310, 260, 40), (380, 380, 420, 34), (760, 430, 300, 28),
                             (40, 120, 200, 26), (640, 90, 240, 26)):
        bk.cumulus(L, cx, cy, wd, ht, cl, TM_L, rng, puff=(0.14, 0.32), rough=0.3, lift=-0.18 + cy / 1400, squash=0.75, base_flat=False)
    for _ in range(160):
        x, y = rng.uniform(0, SW), rng.uniform(0, SH)
        _pt(L, x, y, hexrgb('#ff8a30') if rng.random() < 0.4 else hexrgb('#a83a10'))
    return _out(L.rgba, 0)


def _lava_line(L, pts, w, rng):
    core = hexrgb('#ffd060'); mid = hexrgb('#ff7a1a'); edge = hexrgb('#a02a08')
    if L.S > 1:
        # HD: aynı akış yolu, 1/S adımlı; her örnekte ince yatay kesit (çekirdek / orta / kenar)
        S_ = L.S
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            n = int(max(abs(x1 - x0), abs(y1 - y0)) * S_) + 1
            for k in range(n + 1):
                t = k / n
                x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t
                xa = int(math.floor((x - w - 1) * S_)); xb = int(math.ceil((x + w + 2) * S_))
                xp = np.arange(xa, xb)
                dx = np.abs((xp + 0.5) / S_ - 0.5 - x)
                ok = dx <= int(w) + 1.5
                cols = np.where((dx < w * 0.4)[:, None], core, np.where((dx <= w + 0.5)[:, None], mid, edge))
                yp = int(math.floor(y * S_))
                for q in range(max(1, S_ // 2)):
                    if 0 <= yp + q < L.ph:
                        L.rgba[yp + q, xp[ok] % L.pw, :3] = cols[ok]
                        L.rgba[yp + q, xp[ok] % L.pw, 3] = 1
        return
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for k in range(n + 1):
            t = k / n
            x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t
            for dx in range(-int(w) - 1, int(w) + 2):
                c = core if abs(dx) < w * 0.4 else (mid if abs(dx) <= w else edge)
                L.px(x + dx, y, c)


def _lava_sea(L, y0, rng, h=H):
    """Lav gölü: kararmış kabuk plakaları, aralarında ışıyan çatlaklar; kıyıda daha parlak."""
    w = L.w
    if L.S > 1:
        S_ = L.S
        n = nfbm(w, h, [48, 24, 12], rng, aspect=0.35, wrap_y=False)
        cr = nridged(w, h, [40, 20], rng, aspect=0.4, wrap_y=False)
        b = bay(h, w)
        rows = np.arange(int(y0) * S_, h * S_)
        k = (rows / S_ - y0) / max(1, h - y0)
        crk = cr[rows] > (0.72 - k * 0.1)[:, None]
        hot = cr[rows] > 0.86
        plate = (n[rows] + (b[rows] - 0.5) * 0.08)[..., None]
        base = np.where(plate > 0.55, hexrgb('#1a0806'), np.where(plate > 0.45, hexrgb('#2e0e08'), hexrgb('#4a160a')))
        c = np.where(crk[..., None], hexrgb('#e8561a'), base)
        c = np.where(hot[..., None], hexrgb('#ffc050'), c)
        L.rgba[rows, :, :3] = c
        L.rgba[rows, :, 3] = 1
        L.rgba[int(y0) * S_:int(y0) * S_ + S_, :, :3] = hexrgb('#ffd060')
        L.rgba[int(y0) * S_ + S_:int(y0) * S_ + 2 * S_, :, :3] = hexrgb('#ff8a2a')
        return
    n = fbm(w, h, [48, 24, 12], rng, aspect=0.35, wrap_y=False)
    cr = ridged(w, h, [40, 20], rng, aspect=0.4, wrap_y=False)
    b = bayer(h, w)
    for y in range(int(y0), h):
        k = (y - y0) / max(1, h - y0)
        crack = cr[y] > 0.72 - k * 0.1
        hot = cr[y] > 0.86
        plate = (n[y] + (b[y] - 0.5) * 0.08)[:, None]
        base = np.where(plate > 0.55, hexrgb('#1a0806'), np.where(plate > 0.45, hexrgb('#2e0e08'), hexrgb('#4a160a')))
        c = np.where(crack[:, None], hexrgb('#e8561a'), base)
        c = np.where(hot[:, None], hexrgb('#ffc050'), c)
        L.rgba[y, :, :3] = c
        L.rgba[y, :, 3] = 1
    L.rgba[int(y0), :, :3] = hexrgb('#ffd060')
    L.rgba[int(y0) + 1, :, :3] = hexrgb('#ff8a2a')


def _chain(L, x0, y0, x1, y1, sag, ramp):
    """İki nokta arasında sarkan zincir: dönüşümlü halka (yan/ön)."""
    n = int(math.hypot(x1 - x0, y1 - y0) / 3) + 1
    if L.S > 1:
        # HD: dönüşümlü halkalar; yandan görünen halka ince oval, önden görünen kısa çubuk
        for k in range(n + 1):
            t = k / n
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
            if k % 2 == 0:
                cx, cy = x + 1.0, y - 0.5
                ang = np.linspace(0, math.tau, 25)
                pts = [(cx + math.cos(a) * 1.6, cy + math.sin(a) * 1.55) for a in ang]
                cols = [ramp[3] if math.cos(a) > 0.35 else (ramp[0] if math.sin(a) > 0.5 else (ramp[1] if math.cos(a) < -0.35 else ramp[2])) for a in ang]
                L.stroke(pts, cols, wid=0.75, gap=1e9)
            else:
                L.stroke([(x - 1, y + 0.4), (x + 0.6, y + 0.4)], ramp[2], wid=1.0, gap=1e9)
                L.stroke([(x + 0.6, y + 0.4), (x + 2.6, y + 0.4)], ramp[3], wid=1.0, gap=1e9)
                L.stroke([(x - 0.6, y + 1.2), (x + 1.6, y + 1.2)], ramp[0], wid=thin() / L.S, gap=1e9)
        return
    for k in range(n + 1):
        t = k / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
        if k % 2 == 0:
            for dx, dy, c in ((-1, 0, ramp[1]), (-1, -1, ramp[1]), (2, 0, ramp[3]), (2, -1, ramp[3]), (0, -2, ramp[2]), (1, -2, ramp[3]),
                              (0, 1, ramp[0]), (1, 1, ramp[1])):
                L.px(x + dx, y + dy, c)
        else:
            L.px(x - 1, y, ramp[2]); L.px(x, y, ramp[2]); L.px(x + 1, y, ramp[3]); L.px(x + 2, y, ramp[3]); L.px(x, y + 1, ramp[0])


def tamu_far(seed=52):
    """Volkanik dişli dağlar, yamaçlardan inen lav ırmakları, krater ışıması, duman sütunları, lav denizi."""
    rng = np.random.default_rng(seed)
    out = Layer()
    rock = pal('#060304', '#0b0606', '#110908', '#180c0a', '#21100c', '#2c150f', '#3a1b12')
    pk = bk.make_peaks(rng, 9, 470, 90, 230, smin=0.75, smax=1.35)
    mt = bk.massif(pk, rock, TM_LS, rng, haze='#2a0c08', haze_amt=0.05, haze_bottom=0.0, rough=9, spur_period=30, back_haze=0.25)
    # eteklerde alttan lav ışığı
    yy = lin(H)[:, None].astype(float)
    glow = np.clip((yy - 360) / 120.0, 0, 1) ** 1.5 * 0.45
    bk.apply_haze(mt, '#8a2a0c', glow * (mt[..., 3] > 0))
    out.rgba[...] = mt
    for (px, py, sl, sr) in pk[:5]:
        _glow(out, px, py + 4, 46, '#c83a10', 0.5)
        for s in (-1, 1):
            if rng.random() < 0.75:
                x, y = px, py + 3
                pts = [(x, y)]
                for k in range(int(rng.integers(12, 34))):
                    x += s * rng.uniform(0.6, 2.4) / (sl if s < 0 else sr); y += rng.uniform(3, 6)
                    pts.append((x, y))
                _lava_line(out, pts, rng.uniform(0.6, 1.4), rng)
        sx, sy = px, py - 2
        for k in range(26):
            sx += rng.uniform(-2, 5); sy -= rng.uniform(6, 9)
            out.sphere(sx, sy, 6 + k * 0.9, pal('#0e0808', '#160c0b', '#20100e', '#2c1612', '#3c1e16'), TM_L, rough=0.4, rng=rng,
                       alpha=max(0.15, 0.7 - k * 0.025))
    _lava_sea(out, 486, rng)
    return _out(out.rgba)


def _basalt_hd(out, x0, cw, t, tilt, BAS, rng):
    """tamu_mid bazalt sütununun HD çizimi: aynı yüz bantları ve lav ışığı, eğik tepe sürekli, derzler ince."""
    S_ = bk.S
    Hp = H * S_
    xp = np.arange(int(x0) * S_, int(x0 + cw) * S_)
    f = ((xp + 0.5) / S_ - 0.5 - x0) / cw
    yl = (np.arange(Hp) + 0.5) / S_ - 0.5
    lowk = np.clip((yl - 330) / 160.0, 0, 1)
    BAS = np.asarray(BAS)
    for j, x in enumerate(xp):
        fj = f[j]
        tt = t + tilt * (fj - 0.5) * 2
        r0 = max(0, int(math.floor(tt * S_)))
        if fj < 0.1:
            ci = np.zeros(Hp - r0, int)
        elif fj < 0.4:
            ci = 2 + (lowk[r0:] * 2).astype(int)
        elif fj < 0.8:
            ci = 3 + (lowk[r0:] * 2).astype(int)
        else:
            ci = 4 + (lowk[r0:] * 3).astype(int)
        out.rgba[r0:, x % (W * S_), :3] = BAS[ci]
        out.rgba[r0:, x % (W * S_), 3] = 1
        out.rgba[r0:r0 + 2 * S_ - 1, x % (W * S_), :3] = BAS[5] if fj > 0.3 else BAS[3]
    for _ in range(int(rng.integers(2, 6))):
        yk = int(rng.uniform(t + 10, H - 2))
        for x in xp:
            fj = ((x + 0.5) / S_ - 0.5 - x0) / cw
            for q in range(thin()):
                out.rgba[yk * S_ + q, x % (W * S_), :3] = BAS[0]
                out.rgba[yk * S_ + thin() + q, x % (W * S_), :3] = BAS[5] if fj > 0.4 else BAS[3]
                out.rgba[yk * S_ + q, x % (W * S_), 3] = 1
                out.rgba[yk * S_ + thin() + q, x % (W * S_), 3] = 1


def _lavafall_hd(out, lx):
    """tamu_mid lav çağlayanının HD çizimi: aynı genişleyen akış ve salınım, çapraz parlak akıntı çizgileri ince."""
    S_ = bk.S
    for yp in range(240 * S_, 482 * S_):
        y = yp / S_
        w = 3 + (y - 240) * 0.035
        wob = math.sin(y * 0.15) * 0.8
        xa = int(math.floor((lx + wob - w - 1) * S_)); xb = int(math.ceil((lx + wob + w + 2) * S_))
        xp = np.arange(xa, xb)
        dx = (xp + 0.5) / S_ - 0.5 - (lx + wob)
        adx = np.abs(dx)
        ok = adx <= int(w) + 1.5
        c = np.where((adx < w * 0.35)[:, None], hexrgb('#ffe080'), np.where((adx <= w + 0.5)[:, None], hexrgb('#ff8a24'), hexrgb('#a02a08')))
        streak = (adx > w * 0.35) & (((yp + np.round(dx * S_).astype(int) * 3) % (7 * S_)) < thin())
        c[streak] = hexrgb('#ffb040')
        out.rgba[yp, xp[ok] % (W * S_), :3] = c[ok]
        out.rgba[yp, xp[ok] % (W * S_), 3] = 1


def tamu_mid(seed=53):
    """Bazalt sütun kayalıkları (altıgen kesitli, lavla alttan aydınlanan), lav çağlayanı, dev kaburga kemeri,
    iki yana gerilmiş zincirler, lav ırmağı."""
    rng = np.random.default_rng(seed)
    out = Layer()
    BAS = pal('#050303', '#0b0606', '#130a08', '#1c0e0b', '#27140e', '#341a12', '#462216', '#5c2c18')
    BONE = pal('#3a2a22', '#5a463a', '#7a6654', '#a08a72', '#c4ae92')
    IRON = pal('#0a0707', '#1c1515', '#2e2422', '#463832')
    for gx in (160, 760, 1400):
        gx += rng.uniform(-50, 50)
        top0 = rng.uniform(230, 300)
        ncol = int(rng.integers(9, 15))
        for k in range(ncol):
            cw = rng.uniform(10, 16)
            x0 = gx + k * cw * 0.92 - ncol * cw * 0.45
            t = top0 + abs(k - ncol / 2) * rng.uniform(5, 14) + rng.uniform(-10, 10)
            tilt = rng.uniform(-3, 3)
            if bk.S > 1:
                _basalt_hd(out, x0, cw, t, tilt, BAS, rng)
                continue
            for x in range(int(x0), int(x0 + cw)):
                f = (x - x0) / cw
                tt = int(t + tilt * (f - 0.5) * 2)
                for y in range(tt, H):
                    lowk = np.clip((y - 330) / 160.0, 0, 1)       # aşağıda lav ışığı
                    if f < 0.1:
                        c = BAS[0]
                    elif f < 0.4:
                        c = BAS[2 + int(lowk * 2)]
                    elif f < 0.8:
                        c = BAS[3 + int(lowk * 2)]
                    else:
                        c = BAS[4 + int(lowk * 3)]
                    out.rgba[y, x % W, :3] = c
                    out.rgba[y, x % W, 3] = 1
                out.rgba[tt:tt + 2, x % W, :3] = BAS[5] if f > 0.3 else BAS[3]
            for _ in range(int(rng.integers(2, 6))):
                yk = int(rng.uniform(t + 10, H - 2))
                for x in range(int(x0), int(x0 + cw)):
                    out.px(x, yk, BAS[0]); out.px(x, yk + 1, BAS[5] if (x - x0) / cw > 0.4 else BAS[3])
        _glow(out, gx, 480, 110, '#b8360c', 0.35)
    # lav çağlayanı
    lx = 760 + 10
    if bk.S > 1:
        _lavafall_hd(out, lx)
    for y in (range(240, 482) if bk.S == 1 else ()):
        w = 3 + (y - 240) * 0.035
        wob = math.sin(y * 0.15) * 0.8
        for dx in range(-int(w) - 1, int(w) + 2):
            c = hexrgb('#ffe080') if abs(dx) < w * 0.35 else (hexrgb('#ff8a24') if abs(dx) <= w else hexrgb('#a02a08'))
            if abs(dx) > w * 0.35 and (y + dx * 3) % 7 == 0:
                c = hexrgb('#ffb040')
            out.px(lx + dx + wob, y, c)
    _glow(out, lx, 475, 80, '#ff6a1a', 0.55)
    # dev kaburga kemeri
    bx, by = 1060, 480
    for k in range(7):
        r = 150 - k * 10
        ang0 = math.pi * (1.05 + k * 0.01); ang1 = math.pi * 1.6
        pts = [(bx - 40 + k * 14 + math.cos(a) * r * 0.6, by + math.sin(a) * r) for a in np.linspace(ang0, ang1, 14)]
        out.tube(pts, 4.5 - k * 0.3, 2.5, BONE, TM_LS, rim_col=hexrgb('#e8a070'))
    out.tube([(bx - 140, by - 20), (bx + 80, by - 150)], 5, 4, BONE, TM_LS, rim_col=hexrgb('#e8a070'))
    # sütun kümeleri arasında gerilmiş zincirler
    for (a, b) in ((220, 700), (820, 1340), (1460, 2060)):
        _chain(out, a, rng.uniform(250, 290), b, rng.uniform(250, 290), rng.uniform(40, 90), IRON)
    _lava_sea(out, 492, rng)
    bk.apply_haze(out.rgba, '#2a0c08', 0.1 * (out.rgba[..., 3] > 0))
    return _out(out.rgba)


def tamu_near(seed=54):
    rng = np.random.default_rng(seed)
    out = Layer()
    R = pal('#020101', '#060303', '#0a0505', '#100807', '#170b09')
    rim = hexrgb('#7a240c')
    for x in (150, 820, 1450):
        x += rng.uniform(-40, 40)
        for k in range(5):
            xx = x + rng.uniform(-60, 60)
            hgt = rng.uniform(60, 190)
            w = rng.uniform(14, 30)
            pts = [(xx - w, H + 2), (xx - w * 0.55, H - hgt * 0.35), (xx - w * 0.3, H - hgt * 0.62), (xx + rng.uniform(-6, 6), H - hgt),
                   (xx + w * 0.25, H - hgt * 0.7), (xx + w * 0.5, H - hgt * 0.4), (xx + w, H + 2)]
            out.poly(pts, R[2 + k % 3])
            # alttan lav ışığıyla kızaran kenarlar
            for i in range(len(pts) - 1):
                (ax, ay), (bx_, by_) = pts[i], pts[i + 1]
                if bx_ > ax:
                    out.line(ax, ay, bx_, by_, rim if i >= 3 else R[4])
    IRON = pal('#050404', '#0e0a0a', '#181212', '#241c1a')
    _chain(out, -40, 30, 700, 60, 160, IRON)
    _chain(out, 1100, 20, 1800, 40, 140, IRON)
    return _out(out.rgba, 24)


def tamu_fog(seed=55):
    return _fog_layer('#4a1c12', seed, 340, 0.5, rise=170, top_wisps=0.25)


# ---- katman listesi (dosya adı ekleri world.json'daki "bg" alanıyla aynı)
_NAMES = {'otuken': ['0_sky', '1_mountains', '2_far', '3_mid', '4_near', '5_fog']}
_DEFAULT = ['0_sky', '1_far', '2_mid', '3_near', '4_fog']
BIOME_LAYERS = {}
for _bid in ('otuken', 'bozkir', 'sahmeran', 'kaf', 'tamu'):
    _fns = [(nm, globals().get(_bid + '_' + nm.split('_', 1)[1])) for nm in _NAMES.get(_bid, _DEFAULT)]
    if all(f is not None for _, f in _fns):
        BIOME_LAYERS[_bid] = _fns


# ---- pozlama dengesi (v16): gündüz biyomlarının arka planı oyun alanından parlak ve doygundu (göz yakıyordu).
# Her katman, çizildikten SONRA noktasal bir renk düzeltmesinden geçer: doygunluk kısılır, değer çarpılır, açık
# tonlar yumuşak dizle sıkıştırılır (beyaz patlama yok), sonra biyomun pus rengine çekilir. Noktasal olduğu için
# palet sayısı ve piksel kenarları aynı kalır. Kural: arka plan oyun alanının aydınlık zemininden koyu ve düşük
# kontrastlı; yakın katmanlar (siluet) uzaktakilerden koyu, uzaklar pusa yakın (atmosfer perspektifi).
# katman adı -> (değer, doygunluk, diz, pus payı); 'haze' biyomun pus rengi
GRADE = {
    'bozkir': {'haze': '#a8a4a8',
               '0_sky': (0.8, 0.7, 0.66, 0.1), '1_far': (0.76, 0.7, 0.62, 0.16), '2_mid': (0.7, 0.74, 0.62, 0.08),
               '3_near': (0.56, 0.78, 0.6, 0.0), '4_fog': (0.72, 0.7, 0.6, 0.0)},
    'kaf': {'haze': '#6a6888',
            '0_sky': (0.9, 0.86, 0.7, 0.06), '1_far': (0.82, 0.84, 0.66, 0.1), '2_mid': (0.78, 0.86, 0.66, 0.06),
            '3_near': (0.8, 0.9, 0.64, 0.0), '4_fog': (0.76, 0.84, 0.62, 0.0)},
    # gece biyomları zaten koyu: yalnızca tepe parlaklıkları (ay, kristal, lav) sıkıştırılır
    'otuken': {'haze': '#1c2232', '0_sky': (1.0, 0.95, 0.8, 0.0)},
    'sahmeran': {'haze': '#0c1a18', '2_mid': (0.92, 0.92, 0.72, 0.0)},
    # tamu: arka duvarlar oyun alanından ayrışsın diye bir tık koyu; lav tepeleri sıkıştırılır
    'tamu': {'haze': '#1a0806', '1_far': (0.78, 0.92, 0.68, 0.08), '2_mid': (0.8, 0.95, 0.7, 0.04)},
}


def grade_image(img, val, sat, knee, haze_amt, haze):
    a = np.asarray(img.convert('RGBA')).astype(float) / 255.0
    rgb = a[..., :3]
    lum = (rgb * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True)
    rgb = lum + (rgb - lum) * sat
    rgb = np.clip(rgb, 0, None) * val
    mx = rgb.max(-1, keepdims=True)
    # yumuşak diz: diz üstü değerler 1'e asimptotik yaklaşır (tavan = diz + (1-diz)*0.6)
    top = knee + (1 - knee) * 0.6
    comp = np.where(mx > knee, knee + (top - knee) * (1 - np.exp(-(mx - knee) / max(1e-3, top - knee))), mx)
    rgb = rgb * (comp / np.maximum(mx, 1e-6))
    rgb = rgb * (1 - haze_amt) + hexrgb(haze) * haze_amt
    a[..., :3] = np.clip(rgb, 0, 1)
    return to_image(a)


def _graded(bid, nm, fn):
    g = GRADE.get(bid, {}).get(nm)
    if g is None:
        return fn

    def run():
        return grade_image(fn(), *g, GRADE[bid]['haze'])
    return run


for _bid, _fns in BIOME_LAYERS.items():
    BIOME_LAYERS[_bid] = [(nm, _graded(_bid, nm, f)) for nm, f in _fns]
