"""Yeni biyomların paralaks katmanları (bg_otuken ilkelleriyle):
  bozkir   : gündüz; sıcak güneş, kümülüs bulutlar, mor-mavi uzak dağlar, altın ot tepeleri, kurganlar ve balballar
  sahmeran : mağara; gökyüzü yok, uzak karanlık kaya + ışıldayan kristal kümeleri, sarkıt sütunlar, asılı kökler
  kaf      : karlı şafak; pembe-turuncu gök, alçak güneş, buzlu zirveler, karlı çamlar, buz sivrileri
  tamu     : lav gecesi; kara-kızıl gök, kor bulutları, lav denizi, kara kaya dişleri, kemik kemerler, zincirler
Her katman yatayda dikişsizdir (W = 1280). Her biyom 6 katman verir: sky, far, mid1, mid2, near, fog.
"""
import math
import random
import numpy as np
from PIL import Image

from pixkit import hexrgb, pal, fbm, ridged, profile, BAYER4
import bg_otuken as bo
from bg_otuken import Canvas2, canopy, big_canopy, trunk, dead_tree, pine, bush, fern, bayer, to_image, run_depth, _range_layer

W, H = bo.W, bo.H


def _sky(stops, w=640, h=360, dither=40):
    ys = np.arange(h)
    col = np.zeros((h, 3))
    for (y0, c0), (y1, c1) in zip(stops, stops[1:]):
        m = (ys >= y0) & (ys <= y1)
        t = (ys[m] - y0) / (y1 - y0)
        col[m] = hexrgb(c0) + (hexrgb(c1) - hexrgb(c0)) * t[:, None]
    img = np.broadcast_to(col[:, None, :], (h, w, 3)).copy()
    return img


def _dither(img, steps=40):
    h, w = img.shape[:2]
    return np.clip(np.floor(img * steps + (bayer(h, w)[..., None] - 0.5) * 0.9) / steps, 0, 1)


def _clouds(rgba, rng, bands, lit, body1, body2, shad, sun_k=None, w=640, h=360):
    yy, xx = np.mgrid[0:h, 0:w]
    for cy, thick, cell, thr, op in bands:
        n = fbm(w, h, [cell, cell // 2, cell // 4, cell // 8], [0.5, 0.27, 0.15, 0.08], rng, aspect=0.45)
        base_line = cy + thick * 0.35 + (fbm(w, 1, [cell // 2], [1.0], rng, wrap_y=False)[0] - 0.5) * 6
        top_env = np.clip(1 - np.abs(yy - cy) / thick, 0, 1)
        mask = (n * (0.55 + 0.6 * top_env) > thr) & (yy <= base_line[None, :]) & (yy > cy - thick)
        dtop = run_depth(mask, True)
        dbot = run_depth(mask, False)
        c = np.where((dtop <= 2)[..., None], hexrgb(lit), np.where((dtop <= 6)[..., None], hexrgb(body1), hexrgb(body2)))
        c = np.where((dbot <= 2)[..., None] & (dtop > 2)[..., None], hexrgb(shad), c)
        rgba[mask, :3] = rgba[mask, :3] * (1 - op) + c[mask] * op
    return rgba


def _fill_below(cv, base, col):
    fill = cv.rgba[int(base):, :, 3] == 0
    cv.rgba[int(base):, :, :3][fill] = col
    cv.rgba[int(base):, :, 3][fill] = 1.0


def _fog(col, seed=12, y0=232, amt=0.62):
    rng = np.random.default_rng(seed)
    n = fbm(W, H, [320, 160, 80, 40], [0.45, 0.3, 0.15, 0.1], rng, aspect=0.35)
    yy = np.arange(H)[:, None].astype(float)
    band = np.clip((yy - y0) / 95.0, 0, 1) ** 1.4
    a = band * np.clip((n - 0.32) / 0.5, 0, 1) * amt
    a = np.clip(np.floor(a * 10 + (bayer(H, W) - 0.5) * 0.9) / 10, 0, 1)
    rgba = np.zeros((H, W, 4))
    rgba[..., :3] = hexrgb(col)
    rgba[..., 3] = a
    return to_image(rgba)


# =============================================================== BOZKIR (gündüz)
def bozkir_sky(seed=21):
    rng = np.random.default_rng(seed)
    w, h = 640, 360
    img = _sky([(0, '#2f6fc9'), (90, '#4f93de'), (170, '#7fb6ea'), (240, '#b7d6f0'), (300, '#e3dcc0'), (360, '#f0d9a8')], w, h)
    yy, xx = np.mgrid[0:h, 0:w]
    SUN = (520, 96)
    d = np.sqrt((xx - SUN[0]) ** 2 + (yy - SUN[1]) ** 2)
    glow = np.clip(1 - d / 260, 0, 1) ** 2.0
    img = img + glow[..., None] * (hexrgb('#fff0c0') - img) * 0.6
    img = _dither(img, 36)
    for r, c in ((26, '#fff4cc'), (20, '#fffbe8'), (15, '#ffffff')):
        img[d < r] = hexrgb(c)
    rgba = np.dstack([img, np.ones((h, w))])
    rgba = _clouds(rgba, rng, [(70, 30, 160, 0.56, 1.0), (140, 36, 128, 0.52, 1.0), (205, 20, 96, 0.57, 0.9)],
                   '#ffffff', '#eef3f8', '#cdd9e6', '#9fb2c8', None, w, h)
    # uzak kuşlar
    pr = random.Random(seed)
    for _ in range(9):
        x, y = pr.randint(60, 600), pr.randint(60, 200)
        for dx, dy in ((-2, -1), (-1, 0), (0, 0), (1, 0), (2, -1)):
            rgba[y + dy, x + dx, :3] = hexrgb('#2a3448')
    return to_image(rgba)


def bozkir_far(seed=22):
    """Uzak mor dağlar + altın ot tepeleri (üç sıra)."""
    rng = np.random.default_rng(seed)
    p_far = profile(W, [320, 160, 80, 40], [0.5, 0.26, 0.14, 0.1], rng)
    ridge = 232 - (p_far - p_far.min()) / (p_far.max() - p_far.min()) * 60
    far = _range_layer(ridge, pal('#9c8fd0', '#8277b8', '#6b62a0', '#574f88'), pal('#f6f0ff', '#d2c8ec'), '#c9c0e8', 220, rng, 8)
    cv = Canvas2(W, H)
    cv.rgba[...] = far
    rows = [(262, pal('#7a6a2a', '#9a8a32', '#b9a63c', '#d6c04a', '#e9d56a', '#f6e58e')),
            (282, pal('#6a5a22', '#8a7628', '#a98f30', '#c5a83a', '#d9bd50', '#e8cf70')),
            (300, pal('#5a4a1c', '#786220', '#957828', '#ae8e30', '#c3a240', '#d4b458'))]
    yy = np.arange(H)[:, None]
    for base, P in rows:
        prof = profile(W, [200, 100, 50], [0.5, 0.3, 0.2], rng)
        top = base - (prof - prof.min()) / (prof.max() - prof.min() + 1e-6) * 18
        for x in range(W):
            t = int(top[x])
            for y in range(t, H):
                k = (y - t)
                i = 4 if k < 2 else (3 if k < 6 else 2)
                cv.px(x, y, P[i])
        # ot dokusu: dikey kısa çizgiler
        for x in range(0, W, 3):
            t = int(top[x])
            if rng.random() < 0.6:
                cv.px(x, t - 1, P[5]); cv.px(x, t - 2, P[4])
    return to_image(cv.rgba)


def bozkir_mid(seed=23):
    """Kurgan tepeleri, balballar, tek tük ağaçlar, ot bandı."""
    rng = random.Random(seed)
    cv = Canvas2(W, H)
    GRASS = pal('#8a7a2c', '#a89434', '#c4ad3e', '#dcc44e', '#eed665', '#f8e68c')
    STONE = pal('#5a5660', '#7a7684', '#9a96a4', '#b8b4c2')
    TREE = pal('#2e4a22', '#3f6430', '#55803c', '#6f9c4a', '#8ab85c', '#aad070')
    base = 318
    # kurganlar: yarım elips tepeler, üstü ot, yanında balbal
    x = rng.uniform(20, 80)
    while x < W:
        rx, ry = rng.uniform(36, 70), rng.uniform(16, 30)
        for dy in range(-int(ry), 1):
            for dx in range(-int(rx), int(rx) + 1):
                if dx * dx / (rx * rx) + dy * dy / (ry * ry) <= 1.0:
                    lam = (-dx / rx * 0.5 + (-dy / ry)) * 0.5 + 0.5
                    i = int(np.clip(np.digitize(lam + rng.uniform(-0.05, 0.05), [0.25, 0.45, 0.65, 0.85]), 0, 5))
                    cv.px(x + dx, base + dy, GRASS[i])
        # balbal (taş heykel) kurganın tepesinde
        bx, by = x + rng.uniform(-rx * 0.4, rx * 0.4), base - ry - 1
        for k in range(14):
            w = 3 if k < 10 else 2
            for j in range(-w, w + 1):
                cv.px(bx + j, by - k, STONE[2 if j > 0 else 1])
        cv.px(bx - 1, by - 11, STONE[0]); cv.px(bx + 1, by - 11, STONE[0])
        x += rx * 2 + rng.uniform(40, 120)
    # tek tük ağaçlar
    x = rng.uniform(0, 200)
    while x < W:
        top = base - rng.uniform(55, 80)
        trunk(cv, x, base, top + 14, 5.0, bo.TRUNK, rng, branches=2)
        big_canopy(cv, x, top, rng.uniform(22, 34), rng.uniform(16, 24), TREE, rng, sparse=0.1)
        x += rng.uniform(180, 340)
    # ot bandı
    for k in range(260):
        gx = rng.uniform(0, W)
        hh = rng.uniform(6, 16)
        d = rng.choice([-3, 3])
        for s in range(int(hh)):
            cv.px(gx + (s / hh) ** 2 * d, base - s, GRASS[3] if s < hh * 0.6 else GRASS[5])
    for yy in range(base, H):
        row = cv.rgba[yy]
        m = row[:, 3] == 0
        row[m, :3] = GRASS[1] if yy > base + 8 else GRASS[2]
        row[m, 3] = 1.0
    return to_image(cv.rgba)


def bozkir_near(seed=24):
    """Ön plan: uzun altın ot öbekleri ve bir iki kaya."""
    rng = random.Random(seed)
    cv = Canvas2(W, H)
    GRASS = pal('#6a5a1e', '#8a7626', '#a8922e', '#c6ae3c', '#e0c850', '#f4de74')
    for k in range(60):
        gx = rng.uniform(0, W)
        for b in range(rng.randint(4, 9)):
            hh = rng.uniform(22, 48)
            d = rng.uniform(-10, 10)
            for s in range(int(hh)):
                cv.px(gx + b * 2 + (s / hh) ** 2 * d, H - 1 - s, GRASS[1 + int(s / hh * 3)])
    return to_image(cv.rgba)


# =============================================================== ŞAHMERAN (mağara)
def cave_sky(seed=31):
    """Gökyüzü yerine karanlık mağara duvarı: koyu kaya dokusu, yukarıdan sızan hafif ışıldama."""
    rng = np.random.default_rng(seed)
    w, h = 640, 360
    n = fbm(w, h, [160, 80, 40, 20], [0.45, 0.3, 0.15, 0.1], rng)
    base = _sky([(0, '#0a1210'), (200, '#0c1714'), (360, '#101f1a')], w, h)
    img = base * (0.75 + 0.5 * n[..., None])
    img = _dither(img, 24)
    rgba = np.dstack([img, np.ones((h, w))])
    # uzak kristal ışıltıları (sönük)
    pr = random.Random(seed)
    for _ in range(40):
        x, y = pr.randrange(w), pr.randrange(h)
        c = pr.choice(['#2f7a5a', '#5a3a7a', '#6a5a2a'])
        rgba[y, x, :3] = hexrgb(c)
    return to_image(rgba)


def _crystal(cv, x, y, hgt, w, P, rng, up=True):
    sgn = -1 if up else 1
    for k in range(int(hgt)):
        t = k / hgt
        ww = max(1, int(w * (1 - t)))
        for j in range(-ww, ww + 1):
            i = 4 if j > ww * 0.4 else (3 if j > -ww * 0.3 else 2)
            if k == int(hgt) - 1:
                i = 5
            cv.px(x + j + rng.uniform(-0.3, 0.3), y + sgn * k, P[i])


def cave_far(seed=32):
    """Uzak mağara: koyu kaya sıraları, aralarında ışıldayan büyük kristal kümeleri."""
    rng = random.Random(seed)
    cv = Canvas2(W, H)
    ROCK = pal('#0f1a16', '#15231e', '#1b2d26', '#22382f')
    CRY = {'g': pal('#0f3a2a', '#1a6a48', '#27a06c', '#3fd08c', '#7cf0b4', '#d8fff0'),
           'p': pal('#2a1a40', '#4a2e6e', '#6a46a0', '#8e66cc', '#b494ea', '#e6d8ff'),
           'a': pal('#4a3010', '#7a4e14', '#aa7220', '#d49a30', '#f0c050', '#fff0b0')}
    nrng = np.random.default_rng(seed)
    prof = profile(W, [240, 120, 60, 30], [0.5, 0.26, 0.14, 0.1], nrng)
    top = 190 - (prof - prof.min()) / (prof.max() - prof.min() + 1e-6) * 70
    for x in range(W):
        t = int(top[x])
        for y in range(t, H):
            cv.px(x, y, ROCK[1 if (y - t) < 3 else 0])
    x = rng.uniform(0, 40)
    while x < W:
        P = CRY[rng.choice('gpa')]
        base_y = int(top[int(x) % W]) + rng.uniform(0, 30)
        for k in range(rng.randint(3, 6)):
            _crystal(cv, x + rng.uniform(-14, 14), base_y + rng.uniform(-4, 6), rng.uniform(14, 42), rng.uniform(2, 5), P, rng)
        x += rng.uniform(70, 160)
    _fill_below(cv, 300, ROCK[0])
    return to_image(cv.rgba)


def cave_mid(seed=33):
    """Sarkıt ve dikit sütunlar, mantar kümeleri, küçük kristaller."""
    rng = random.Random(seed)
    cv = Canvas2(W, H)
    ROCK = pal('#121e19', '#1a2a23', '#24372e', '#2f453a', '#3b5346')
    MUSH = pal('#1a4a3a', '#2a7a5a', '#48b080', '#8ae0b0')
    base = 322
    x = rng.uniform(0, 60)
    while x < W:
        w = rng.uniform(8, 18)
        hgt = rng.uniform(80, 200)
        for y in range(int(base - hgt), base + 1):
            t = (y - (base - hgt)) / hgt
            ww = w * (0.35 + 0.65 * t)
            for j in range(int(-ww), int(ww) + 1):
                rel = (j + ww) / (2 * ww + 1e-6)
                i = 3 if rel > 0.7 else (1 if rel < 0.25 else 2)
                cv.px(x + j, y, ROCK[i])
        # tepeden sarkan sarkıtlar
        for k in range(rng.randint(2, 4)):
            sx = x + rng.uniform(-w, w)
            for s in range(int(rng.uniform(16, 50))):
                ww2 = max(0, 3 - s * 0.07)
                for j in range(int(-ww2), int(ww2) + 1):
                    cv.px(sx + j, s, ROCK[2 if j > 0 else 1])
        x += rng.uniform(90, 200)
    # dikitler
    for k in range(40):
        sx = rng.uniform(0, W)
        hh = rng.uniform(10, 40)
        for s in range(int(hh)):
            ww2 = max(0, (hh - s) * 0.12)
            for j in range(int(-ww2), int(ww2) + 1):
                cv.px(sx + j, base - s, ROCK[3 if j > 0 else 2])
    for k in range(50):
        mx, my = rng.uniform(0, W), base - rng.uniform(0, 6)
        for c in range(rng.randint(2, 4)):
            hx = mx + c * 3
            cv.px(hx, my - 1, MUSH[1]); cv.px(hx, my - 2, MUSH[2]); cv.px(hx + 1, my - 2, MUSH[2]); cv.px(hx, my - 3, MUSH[3])
    for yy in range(base, H):
        row = cv.rgba[yy]
        m = row[:, 3] == 0
        row[m, :3] = ROCK[1] if yy > base + 6 else ROCK[2]
        row[m, 3] = 1.0
    # küçük ışıldayan kristaller
    CRY = pal('#1a6a48', '#27a06c', '#3fd08c', '#7cf0b4', '#b8ffd8', '#ffffff')
    for k in range(30):
        _crystal(cv, rng.uniform(0, W), base - rng.uniform(0, 4), rng.uniform(6, 16), rng.uniform(1.5, 3), CRY, rng)
    return to_image(cv.rgba)


def cave_near(seed=34):
    """Ön plan: tavandan sarkan kökler ve kalın karanlık sütunlar."""
    rng = random.Random(seed)
    cv = Canvas2(W, H)
    ROCK = pal('#070d0b', '#0d1612', '#142019', '#1b2a22', '#243529')
    ROOTC = pal('#1e2a22', '#2c3c30', '#3c4e40')
    for k in range(2):
        xx = k * W / 2 + rng.uniform(0, W / 4)
        w = rng.uniform(12, 18)
        for y in range(H):
            ww = w + 10 * max(0, (y - 300)) / 60
            for j in range(int(ww * 2)):
                rel = j / (ww * 2)
                i = 1 if rel < 0.25 else (3 if rel > 0.78 else 2)
                if math.sin(y * 0.15 + j * 0.9) > 0.85:
                    i = max(0, i - 1)
                cv.px(xx - ww + j, y, ROCK[i])
    for j in range(14):
        vx = rng.uniform(0, W)
        ln = rng.uniform(40, 150)
        for s in range(int(ln)):
            px_ = vx + math.sin(s * 0.08 + j) * 2.5
            cv.px(px_, s, ROOTC[1])
            if s % 12 == 0:
                cv.blob(px_ + 2, s, 2.0, ROOTC[1], ROOTC[2], ROOTC[0])
    return to_image(cv.rgba)


# =============================================================== KAF (karlı şafak)
def kaf_sky(seed=41):
    rng = np.random.default_rng(seed)
    w, h = 640, 360
    img = _sky([(0, '#2b2f6e'), (60, '#4a4a90'), (130, '#8c6aa8'), (190, '#d48aa0'), (240, '#f4b08a'), (290, '#ffd4a0'), (360, '#ffe8c8')], w, h)
    yy, xx = np.mgrid[0:h, 0:w]
    SUN = (470, 262)
    d = np.sqrt((xx - SUN[0]) ** 2 + ((yy - SUN[1]) * 1.3) ** 2)
    glow = np.clip(1 - d / 260, 0, 1) ** 1.8
    img = img + glow[..., None] * (hexrgb('#ffc890') - img) * 0.6
    img = _dither(img, 40)
    for r, c in ((34, '#ffd8a8'), (26, '#ffecc8'), (18, '#fff8ea')):
        img[d < r] = hexrgb(c)
    rgba = np.dstack([img, np.ones((h, w))])
    rgba = _clouds(rgba, rng, [(50, 22, 160, 0.6, 0.9), (120, 26, 128, 0.58, 1.0)], '#ffe6d0', '#e8b8c0', '#b88aa8', '#7a5a90', None, w, h)
    pr = random.Random(seed)
    for _ in range(90):
        x, y = pr.randrange(w), pr.randrange(0, 110)
        if rgba[y, x, 0] < 0.4:
            rgba[y, x, :3] = hexrgb('#e8ecff') if pr.random() > 0.5 else hexrgb('#9aa0d8')
    return to_image(rgba)


def kaf_far(seed=42):
    rng = np.random.default_rng(seed)
    p_far = profile(W, [320, 160, 80, 40, 20], [0.5, 0.26, 0.14, 0.07, 0.03], rng)
    ridge_far = 200 - (p_far - p_far.min()) / (p_far.max() - p_far.min()) * 110
    far = _range_layer(ridge_far, pal('#c8b8e8', '#a898d0', '#8878b8', '#6c5ea0'), pal('#fff6f8', '#e6d4f0'), '#f0c0c0', 190, rng, 60)
    p_near = profile(W, [256, 128, 64, 32, 16], [0.5, 0.26, 0.14, 0.07, 0.03], rng)
    ridge_near = 250 - (p_near - p_near.min()) / (p_near.max() - p_near.min()) * 80
    near = _range_layer(ridge_near, pal('#a090c8', '#8070b0', '#645896', '#4c4278'), pal('#ffffff', '#dcd0f4'), '#e8b0b8', 236, rng, 40)
    a = near[..., 3:4]
    far[..., :3] = far[..., :3] * (1 - a) + near[..., :3] * a
    far[..., 3] = np.maximum(far[..., 3], near[..., 3])
    return to_image(far)


def _snow_pine(cv, x, base_y, height, P, SNOW, rng):
    pine(cv, x, base_y, height, P, rng)
    tiers = max(4, int(height / 9))
    for i in range(tiers):
        ty = base_y - height + i * (height * 0.86 / tiers)
        half = 3 + i * (height * 0.045)
        for k in range(int(half * 2 + 1)):
            dx = -half + k
            if rng.random() < 0.8:
                cv.px(x + dx, ty + abs(dx) * 0.9, SNOW[1 if dx < 0 else 2])
                if abs(dx) < half * 0.5:
                    cv.px(x + dx, ty + abs(dx) * 0.9 + 1, SNOW[0])


def kaf_mid(seed=43):
    rng = random.Random(seed)
    cv = Canvas2(W, H)
    PINE = pal('#16302c', '#1f4238', '#2a5648', '#366a58', '#44806a', '#56987e')
    SNOW = pal('#c8d4f0', '#e6eefc', '#ffffff')
    ICE = pal('#6a90c0', '#8ab0dc', '#aed0f0', '#d4ecff', '#f0f8ff', '#ffffff')
    base = 320
    x = rng.uniform(0, 30)
    while x < W:
        _snow_pine(cv, x, base, rng.uniform(90, 170), PINE, SNOW, rng)
        x += rng.uniform(34, 90)
    # buz sivrileri
    for k in range(18):
        sx = rng.uniform(0, W)
        _crystal(cv, sx, base, rng.uniform(16, 44), rng.uniform(2, 5), ICE, rng)
    # kar tümsekleri ve zemin
    for yy in range(base - 2, H):
        row = cv.rgba[yy]
        m = row[:, 3] == 0
        row[m, :3] = SNOW[2] if yy < base + 2 else (SNOW[1] if yy < base + 10 else SNOW[0])
        row[m, 3] = 1.0
    for k in range(60):
        mx = rng.uniform(0, W)
        r = rng.uniform(6, 18)
        for dx in range(int(-r), int(r) + 1):
            hgt = int(math.sqrt(max(0, r * r - dx * dx)) * 0.35)
            for s in range(hgt):
                cv.px(mx + dx, base - 1 - s, SNOW[2] if dx > -r * 0.3 else SNOW[1])
    return to_image(cv.rgba)


def kaf_near(seed=44):
    rng = random.Random(seed)
    cv = Canvas2(W, H)
    ICE = pal('#2a4a70', '#3c6490', '#5a86b4', '#88b0d8', '#c0e0f8', '#ffffff')
    for k in range(2):
        xx = k * W / 2 + rng.uniform(0, W / 4)
        for s in range(3):
            _crystal(cv, xx + s * 14 - 14, H + 10, rng.uniform(120, 240), rng.uniform(8, 16), ICE, rng)
    for k in range(50):
        sx = rng.uniform(0, W)
        hh = rng.uniform(8, 24)
        for s in range(int(hh)):
            cv.px(sx + (s / hh) * rng.choice([-2, 2]), H - 1 - s, ICE[4] if s > hh * 0.7 else ICE[3])
    return to_image(cv.rgba)


# =============================================================== TAMU (lav)
def tamu_sky(seed=51):
    rng = np.random.default_rng(seed)
    w, h = 640, 360
    img = _sky([(0, '#050204'), (120, '#120408'), (220, '#2a0a0c'), (300, '#5a1a10'), (360, '#8a2e14')], w, h)
    yy, xx = np.mgrid[0:h, 0:w]
    glow = np.clip(1 - np.abs(yy - 340) / 160, 0, 1) ** 2
    img = img + glow[..., None] * (hexrgb('#ff6a20') - img) * 0.35
    img = _dither(img, 28)
    rgba = np.dstack([img, np.ones((h, w))])
    rgba = _clouds(rgba, rng, [(80, 34, 160, 0.56, 1.0), (170, 30, 128, 0.55, 1.0)], '#6a2418', '#2e0c0c', '#1a0608', '#0a0204', None, w, h)
    pr = random.Random(seed)
    for _ in range(120):
        x, y = pr.randrange(w), pr.randrange(h)
        if rgba[y, x, 0] < 0.25:
            rgba[y, x, :3] = hexrgb('#ff9a40') if pr.random() > 0.6 else hexrgb('#8a3020')
    return to_image(rgba)


def tamu_far(seed=52):
    """Lav denizi ve ardında kara kaya dişleri."""
    rng = np.random.default_rng(seed)
    cv = Canvas2(W, H)
    ROCK = pal('#0a0506', '#140a0c', '#1e1012', '#2a1618')
    prof = profile(W, [256, 128, 64, 32], [0.5, 0.26, 0.14, 0.1], rng)
    top = 236 - (prof - prof.min()) / (prof.max() - prof.min() + 1e-6) * 90
    pr = random.Random(seed)
    for x in range(W):
        t = int(top[x])
        for y in range(t, 300):
            cv.px(x, y, ROCK[2 if (y - t) < 2 else 1])
    # lav denizi: dalgalı parlak bantlar
    LAVA = pal('#5a1408', '#9a2c10', '#d85018', '#ff7a24', '#ffb040', '#fff0a0')
    n = fbm(W, 60, [160, 80, 40, 20], [0.5, 0.3, 0.12, 0.08], rng)
    for y in range(300, H):
        for x in range(W):
            v = n[y - 300, x] + math.sin(x * 0.05 + y * 0.3) * 0.08
            i = int(np.clip(np.digitize(v, [0.35, 0.45, 0.55, 0.65, 0.78]), 0, 5))
            if y < 303:
                i = max(i, 3)
            cv.px(x, y, LAVA[i])
    # kaya dişleri lav önünde
    for k in range(30):
        sx = pr.uniform(0, W)
        hh = pr.uniform(10, 40)
        for s in range(int(hh)):
            ww = max(0, (hh - s) * 0.18)
            for j in range(int(-ww), int(ww) + 1):
                cv.px(sx + j, 300 - s, ROCK[2 if j > 0 else 0])
    return to_image(cv.rgba)


def tamu_mid(seed=53):
    """Kemik kemerler, kara sütunlar, zincirler, kor çatlaklı zemin."""
    rng = random.Random(seed)
    cv = Canvas2(W, H)
    ROCK = pal('#0c0608', '#160c0e', '#221214', '#2e1a1c', '#3a2224')
    BONE = pal('#5a4a40', '#8a7868', '#b8a898', '#dcd0c0')
    LAVA = pal('#9a2c10', '#d85018', '#ff7a24', '#ffb040')
    base = 322
    x = rng.uniform(0, 80)
    while x < W:
        w = rng.uniform(10, 20)
        hgt = rng.uniform(90, 210)
        for y in range(int(base - hgt), base + 1):
            for j in range(int(-w), int(w) + 1):
                rel = (j + w) / (2 * w)
                i = 3 if rel > 0.7 else (1 if rel < 0.25 else 2)
                cv.px(x + j, y, ROCK[i])
        if rng.random() < 0.6:
            # kemik kaburga kemeri
            cx = x + w + rng.uniform(40, 70)
            r = rng.uniform(30, 55)
            for a in np.linspace(0, math.pi, int(r * 2)):
                px_, py_ = cx + math.cos(a) * r, base - math.sin(a) * r * 1.3
                cv.blob(px_, py_, 2.2, BONE[2], BONE[3], BONE[1])
        x += rng.uniform(140, 260)
    for k in range(10):
        vx = rng.uniform(0, W)
        ln = rng.uniform(60, 160)
        for s in range(int(ln)):
            if s % 6 < 3:
                cv.px(vx + math.sin(s * 0.05) * 3, s, ROCK[4])
                cv.px(vx + math.sin(s * 0.05) * 3 + 1, s, ROCK[3])
    for yy in range(base, H):
        row = cv.rgba[yy]
        m = row[:, 3] == 0
        row[m, :3] = ROCK[1]
        row[m, 3] = 1.0
    for k in range(70):
        sx, sy = rng.uniform(0, W), base + rng.uniform(2, 36)
        for s in range(rng.randint(3, 9)):
            cv.px(sx + s, sy + rng.choice([-1, 0, 0, 1]), LAVA[rng.randint(1, 3)])
    return to_image(cv.rgba)


def tamu_near(seed=54):
    rng = random.Random(seed)
    cv = Canvas2(W, H)
    IRON = pal('#0a0608', '#1a1012', '#2a1a1c', '#3a2426')
    for k in range(3):
        xx = k * W / 3 + rng.uniform(0, W / 5)
        for s in range(H):
            w = 3 + (s % 10 < 5) * 2
            for j in range(-w, w + 1):
                cv.px(xx + j + math.sin(s * 0.03 + k) * 6, s, IRON[1 if j < 0 else 2])
    return to_image(cv.rgba)


BIOME_BG = {
    'bozkir': [bozkir_sky, bozkir_far, bozkir_mid, bozkir_near, lambda: _fog('#f0e0b0', 25, 250, 0.3)],
    'sahmeran': [cave_sky, cave_far, cave_mid, cave_near, lambda: _fog('#2a5a48', 35, 226, 0.55)],
    'kaf': [kaf_sky, kaf_far, kaf_mid, kaf_near, lambda: _fog('#e8e0f8', 45, 236, 0.5)],
    'tamu': [tamu_sky, tamu_far, tamu_mid, tamu_near, lambda: _fog('#4a1008', 55, 230, 0.55)],
}
