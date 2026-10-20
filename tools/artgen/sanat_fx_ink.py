"""sanat_fx_ink: v28 Savaş Sanatları mürekkep dokuları (sumi-e fırça darbesi, sıçrantı, yıkama, "GÜM!" damgası,
altın varak, yer yarığı, mühür, hilal). Renk YOK: dokular veri taşır, renk oyunda paletten gelir.

assets/fx/ink/sanat_firca.png  1024x512: 8 satır x 64 px fırça darbesi (u yatay = darbe boyunca 0 baş .. 1 kuyruk,
    v dikey = enine). shaders/sanat_firca.gdshader okur (scripts/core/SanatFX.gd fırça şeritleri).
    R  mürekkep yükü: baş dolu ve ıslak, kuyruğa doğru kıllar ayrışır (kuru fırça / "uçan ak"), kenar pürüzlü
    G  koyu birikim: mürekkebin kenarda ve başta toplanması (sumi-e "kenar halesi"), kıl boyu koyu çizgiler
    B  kıl kimliği (erime ve kuruma sırası)
    A  kâğıt tanesi (lif + ince tane)
    Satırlar: 0 ıslak ağır, 1 orta, 2 kuru, 3 çok kuru (yarılan), 4 sulu kenarlı, 5 hızlı ince, 6 kalın kuru, 7 sıçratan
assets/fx/ink/sanat_fx.png  1024x1024 atlas (sanat_fx.json), InkFX atlas kodlamasıyla aynı (ink_fx.gdshader):
    R işaretli uzaklık (0,5 kenar)  G koyu mürekkep  B çizim sırası  A erime gürültüsü
    Şekiller: splat_a, splat_b (büyük sıçrantı), wash (mürekkep yıkaması), gum ("GÜM!" fırça yazısı), varak (altın
    varak pulları), crack (yer yarığı, taban y = 0,8h); v31 yansıma sözcükleri (256x128, aynı fırça yazısı): cit "ÇIT!",
    viz "VIZ!", tam "TAM!" (eski kullanılmayan seal hücresi ve iki boş hücre); v32: kut / vus / cat hücrelerinde
    pat "PAT!" (Pehlivan Savurması), hayt "HAYT!" (Tulpar Dörtnalı), cak "ÇAK!" (Yıldırım Ağı)

Kullanım: cd tools/artgen && python sanat_fx_ink.py [--onizleme out.png]
HD (2 kat): KY_HD=2 python sanat_fx_ink.py  ardından  python hd_paket.py --paketle
"""
import json
import math
import os
import sys

import numpy as np
import skia
from PIL import Image
from scipy import ndimage

from hdpack import HD
from inkfx import (SS, _ax, _arr, _paint, _surface, blob, down, drop, fft_noise, field, grid, periodic_1d, polar,
                   radial_streaks, smoothstep, taper, IMPORT)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'assets', 'fx', 'ink')


# ------------------------------------------------------------------ fırça darbesi dokusu
def brush_row(W, H, seed, wet=0.7, dry=0.6, split=0.4, nb=46, edge=0.07, pool=0.7, spatter=0.0):
    """Bir fırça darbesi: u (W) boyunca baştan kuyruğa, v (H) enine."""
    rng = np.random.default_rng(seed)
    u = (_ax(W) / W)[None, :]
    v = (_ax(H) / H)[:, None]
    # pürüzlü kenar zarfı (iki kenar ayrı gürültü), kuyrukta daralır
    et = edge + 0.05 * periodic_1d(W, seed + 1, kmax=14, up=HD)[None, :] + 0.03 * periodic_1d(W, seed + 2, kmax=40, up=HD)[None, :]
    eb = edge + 0.05 * periodic_1d(W, seed + 3, kmax=14, up=HD)[None, :] + 0.03 * periodic_1d(W, seed + 4, kmax=40, up=HD)[None, :]
    env = smoothstep(et, et + 0.05, v) * smoothstep(eb, eb + 0.05, 1.0 - v)
    # kıllar: enine dar şeritler; kuyruğa doğru (u büyüdükçe) yük azalır ve kopar
    bri = np.zeros((H * HD, W * HD))
    dark = np.zeros((H * HD, W * HD))
    for j in range(nb):
        v0 = rng.uniform(0.02, 0.98)
        wid = rng.uniform(0.008, 0.03) * (1.8 if rng.random() < 0.12 else 1.0)
        load = rng.uniform(0.5, 1.0)
        m = periodic_1d(W, seed * 977 + j, kmax=11, up=HD)[None, :]
        g = periodic_1d(W, seed * 977 + j + 300, kmax=6, up=HD)[None, :]
        # kuruma eşiği: kıl başına farklı uzunlukta biter (uçan ak)
        life = rng.uniform(0.6, 1.2) - dry * rng.uniform(0.0, 0.45)
        fade = 1.0 - smoothstep(life - 0.18, life, u)
        brk = smoothstep(-0.7 + split * 1.1 * u, -0.45 + split * 1.1 * u, g)   # kopukluk kuyrukta artar
        a = np.clip(0.9 + 0.3 * m, 0, 1) * (0.75 + 0.25 * load) * fade * (0.15 + 0.85 * brk)
        prof = np.exp(-((v - v0) / wid) ** 2)
        bri = np.maximum(bri, prof * a)
        if rng.random() < 0.3:
            dark = np.maximum(dark, prof * a * smoothstep(0.55, 0.85, m) * 0.7)
    # ıslak gövde: başta dolu, kuyrukta kurur
    wet_u = wet * (1.0 - (smoothstep(0.05, 1.0, u) ** 0.8) * dry)
    nz = fft_noise(H, W, beta=1.9, seed=seed + 7, fx=2.5, fy=0.12, up=HD)     # boyuna uzamış (fx büyük = u boyunca yavaş)
    # kıllar arası dolgu: ıslakken kıllar birleşir, kurudukça aralar açılır (kıl yapısı gövdede de seçilir)
    body = np.clip(wet_u * (0.55 + 0.6 * nz) + 0.25 * bri * wet_u, 0, 1)
    R = np.clip(np.maximum(body, bri) * env, 0, 1)
    # başın basışı: ilk %6 tamamen dolu ve yuvarlak (geometri inceltir), hafif taşma
    head = 1.0 - smoothstep(0.0, 0.07, u)
    R = np.clip(np.maximum(R, head * env * 0.95), 0, 1)
    if spatter > 0:
        # kenardan sıçrayan küçük damlalar (kenar zarfının dışında)
        for k in range(int(40 * spatter)):
            uu = rng.uniform(0.05, 0.9)
            vv = rng.choice([rng.uniform(0.0, 0.12), rng.uniform(0.88, 1.0)])
            r = rng.uniform(0.004, 0.012)
            d = np.hypot((u - uu) * W / H, v - vv)
            R = np.maximum(R, smoothstep(r * 1.4, r * 0.6, d) * 0.9)
    # koyu birikim (G): kenarda toplanan mürekkep + başta havuz + kıl boyu koyu çizgiler
    dist_edge = np.minimum(v - et, (1 - v) - eb)
    rim = smoothstep(0.12, 0.0, dist_edge) * smoothstep(-0.02, 0.02, dist_edge)
    G = np.clip(rim * 0.75 * (0.6 + 0.4 * nz) + pool * head * 0.9 + dark, 0, 1) * (R > 0.2)
    # kıl kimliği (B): enine satır başına rastgele + boyuna sıra (kuyruk önce erir)
    row = ndimage.uniform_filter1d(rng.random(H), 2, mode='nearest')
    if HD > 1:
        row = np.repeat(row, HD)
    B = np.clip(0.65 * row[:, None] + 0.35 * u, 0, 1) * np.ones_like(R)
    # kâğıt tanesi (A): lif (boyuna uzamış) + ince tane
    fib = fft_noise(H, W, beta=1.2, seed=seed + 9, fx=1.5, fy=0.25, up=HD)
    gr = fft_noise(H, W, beta=0.6, seed=seed + 10, up=HD)
    A = np.clip(0.55 * fib + 0.45 * gr, 0, 1)
    return np.dstack([R, G, B, A])


def brush_atlas():
    W, H = 1024, 64
    rows = [
        dict(seed=101, wet=0.95, dry=0.25, split=0.15, nb=56, edge=0.06, pool=0.8),          # 0 ıslak ağır
        dict(seed=113, wet=0.8, dry=0.5, split=0.35, nb=50, edge=0.07, pool=0.6),            # 1 orta
        dict(seed=127, wet=0.6, dry=0.85, split=0.6, nb=44, edge=0.08, pool=0.5),            # 2 kuru
        dict(seed=131, wet=0.45, dry=1.0, split=0.9, nb=38, edge=0.09, pool=0.45),           # 3 çok kuru
        dict(seed=149, wet=0.9, dry=0.35, split=0.2, nb=52, edge=0.05, pool=0.9, spatter=0.6),  # 4 sulu kenar
        dict(seed=151, wet=0.75, dry=0.7, split=0.5, nb=30, edge=0.1, pool=0.5),             # 5 hızlı ince
        dict(seed=163, wet=0.7, dry=0.75, split=0.7, nb=64, edge=0.05, pool=0.6),            # 6 kalın kuru
        dict(seed=173, wet=0.85, dry=0.45, split=0.3, nb=48, edge=0.06, pool=0.7, spatter=1.0),  # 7 sıçratan
    ]
    out = np.zeros((H * len(rows) * HD, W * HD, 4))
    for i, r in enumerate(rows):
        out[i * H * HD:(i + 1) * H * HD] = brush_row(W, H, **r)
    return out


# ------------------------------------------------------------------ atlas şekilleri
def shape_splat(size, seed, n_lobe=7, n_flick=9, n_drop=34):
    """Büyük mürekkep sıçrantısı: loblu ağır leke + uzun ince fışkırma kılları + uydu damlalar (Ralph Steadman değil,
    sumi-e: az ama ağır)."""
    rng = np.random.default_rng(seed)
    S = size
    s, c = _surface(S, S)
    dark = _surface(S, S)
    cx = cy = S * 0.5
    blob(c, cx, cy, S * 0.16, rng, k=7, jit=0.3)
    blob(dark[1], cx, cy, S * 0.1, rng, k=9, jit=0.35)
    for i in range(n_lobe):
        a = rng.uniform(0, 6.28)
        rr = S * rng.uniform(0.1, 0.2)
        blob(c, cx + math.cos(a) * rr, cy + math.sin(a) * rr, S * rng.uniform(0.04, 0.08), rng, jit=0.3)
    for i in range(n_flick):
        a = rng.uniform(0, 6.28)
        L = S * rng.uniform(0.26, 0.46)
        w0 = S * rng.uniform(0.025, 0.06)
        bend = rng.uniform(-0.2, 0.2)
        pts = [(cx + math.cos(a + bend * t * t) * L * t, cy + math.sin(a + bend * t * t) * L * t) for t in np.linspace(0.1, 1.0, 5)]
        taper(c, pts, w0, 0.6, wmid=w0 * 0.6)
        drop(c, cx + math.cos(a + bend) * L * 1.06, cy + math.sin(a + bend) * L * 1.06, S * rng.uniform(0.008, 0.016), a, 1.6)
    for i in range(n_drop):
        a = rng.uniform(0, 6.28)
        rr = S * (0.2 + 0.27 * math.sqrt(rng.random()))
        drop(c, cx + math.cos(a) * rr, cy + math.sin(a) * rr, S * rng.uniform(0.004, 0.018), a, rng.uniform(1.0, 2.2))
    cov = _arr(s)
    nz = radial_streaks(S * SS, S * SS, cx * SS, cy * SS, seed + 3)
    R = field(cov, 6.0, nz)
    G = np.clip(down(_arr(dark[0])) * 0.85 + smoothstep(0.7, 0.85, down(nz)) * smoothstep(0.58, 0.72, R) * 0.4, 0, 1)
    r, _ = polar(S, S, cx, cy)
    B = np.clip(r / (S * 0.48) * 0.88 + 0.12 * down(nz), 0, 1)
    A = fft_noise(S, S, beta=1.6, seed=seed + 9, up=HD)
    return np.dstack([R, G, B, A])


def shape_wash(size, seed):
    """Mürekkep yıkaması: yumuşak, granüllü, kenarı koyulaşan (kuruyan su halkası) geniş leke."""
    rng = np.random.default_rng(seed)
    S = size
    s, c = _surface(S, S)
    cx = cy = S * 0.5
    blob(c, cx, cy, S * 0.3, rng, k=6, jit=0.2)
    for i in range(5):
        a = rng.uniform(0, 6.28)
        blob(c, cx + math.cos(a) * S * 0.16, cy + math.sin(a) * S * 0.16, S * rng.uniform(0.1, 0.16), rng, jit=0.25)
    cov = _arr(s)
    nz = fft_noise(S * SS, S * SS, beta=2.2, seed=seed + 1, up=HD)
    R = field(cov, 14.0, nz, spread=16.0)
    gran = fft_noise(S, S, beta=0.9, seed=seed + 2, up=HD)
    # kuruma halkası: kenarda koyu (G), içte granül
    G = np.clip(smoothstep(0.5, 0.56, R) * (1 - smoothstep(0.58, 0.68, R)) * 0.9 + smoothstep(0.6, 0.8, gran) * 0.35, 0, 1)
    r, _ = polar(S, S, cx, cy)
    B = np.clip(r / (S * 0.47), 0, 1)
    A = np.clip(0.5 * gran + 0.5 * fft_noise(S, S, beta=1.4, seed=seed + 3, up=HD), 0, 1)
    return np.dstack([R, G, B, A])


def _letters_gum(c, w, h, rng, dark):
    """'GÜM!' fırça yazısı (hafif eğik, kalın-ince). Koordinatlar temel piksel."""
    sk = 0.18   # eğiklik
    base = h * 0.8
    top = h * 0.2

    def P(x, y):
        return (x + (base - y) * sk, y)

    def st(pts, w0, w1, wm=None, cap=True):
        q = [P(*p) for p in pts]
        taper(c, q, w0, w1, wmid=wm, cap=cap)
        taper(dark[1], q, w0 * 0.55, w1 * 0.4, wmid=(wm or w0) * 0.55, cap=cap)

    W = h * 0.17
    # G
    gx, gy, gr = w * 0.15, (top + base) * 0.5, (base - top) * 0.5
    arc = [(gx + math.cos(a) * gr * 0.85, gy + math.sin(a) * gr) for a in np.linspace(-0.7, -0.7 - 4.9, 14)]
    st(arc, W * 0.45, W * 0.7, W * 1.15)
    st([(gx + gr * 0.05, gy + gr * 0.1), (gx + gr * 0.78, gy + gr * 0.12), (gx + gr * 0.7, gy + gr * 0.85)], W * 0.8, W * 0.35, W * 0.9)
    # Ü
    ux = w * 0.4
    st([(ux - gr * 0.55, top + h * 0.02), (ux - gr * 0.6, gy + gr * 0.4), (ux - gr * 0.1, base), (ux + gr * 0.45, gy + gr * 0.45), (ux + gr * 0.52, top + h * 0.03)],
       W * 1.0, W * 0.5, W * 1.1)
    for dx in (-0.35, 0.3):
        blob(c, *P(ux + gr * dx, top - h * 0.1), W * 0.42, rng, jit=0.25)
        blob(dark[1], *P(ux + gr * dx, top - h * 0.1), W * 0.25, rng, jit=0.25)
    # M
    mx = w * 0.66
    st([(mx - gr * 0.62, base), (mx - gr * 0.55, top)], W * 0.7, W * 1.05)
    st([(mx - gr * 0.55, top), (mx, gy + gr * 0.2)], W * 0.9, W * 0.55)
    st([(mx, gy + gr * 0.2), (mx + gr * 0.55, top)], W * 0.55, W * 0.95)
    st([(mx + gr * 0.55, top), (mx + gr * 0.68, base)], W * 1.05, W * 0.45)
    # !
    ex = w * 0.86
    st([(ex, top - h * 0.04), (ex - gr * 0.05, gy + gr * 0.45)], W * 1.25, W * 0.25)
    blob(c, *P(ex - gr * 0.1, base - h * 0.02), W * 0.5, rng, jit=0.2)
    blob(dark[1], *P(ex - gr * 0.1, base - h * 0.02), W * 0.3, rng, jit=0.2)
    # sıçrantı damlaları
    for i in range(30):
        x = rng.uniform(0.05, 0.95) * w
        y = rng.uniform(0.05, 0.98) * h
        drop(c, x, y, h * rng.uniform(0.006, 0.02), rng.uniform(-0.5, 0.5), rng.uniform(1.0, 2.0))


# v31 kombo sanatlarının yansıma sözcükleri: harf başına fırça darbeleri (birim kutu: x 0..gen, y 0 üst .. 1 taban)
# [noktalar, w0, w1, wmid]; ("nokta", x, y, r): yuvarlak damla (Ü noktaları, ünlem)
_HARF = {
    'I': (0.42, [([(0.5, 0.0), (0.49, 0.55), (0.47, 1.0)], 1.2, 0.6, 1.25)]),
    'T': (0.82, [([(0.0, 0.04), (0.5, -0.01), (1.0, 0.02)], 0.62, 0.42, 0.95),
                 ([(0.52, 0.02), (0.5, 0.55), (0.47, 1.0)], 1.05, 0.45, 1.1)]),
    '!': (0.36, [([(0.52, -0.04), (0.47, 0.7)], 1.3, 0.22, None), ('nokta', 0.44, 0.95, 0.52)]),
    'Ç': (0.9, [('yay', 0.55, 0.5, 0.5, -0.75, -0.75 - 4.75, 0.45, 0.7, 1.15),
                ([(0.52, 1.0), (0.62, 1.1), (0.44, 1.2)], 0.55, 0.2, 0.6)]),
    'K': (0.86, [([(0.16, 0.0), (0.14, 0.55), (0.12, 1.0)], 0.75, 1.05, 1.0),
                 ([(0.88, 0.02), (0.5, 0.3), (0.2, 0.56)], 0.9, 0.5, 0.75),
                 ([(0.36, 0.44), (0.66, 0.72), (0.95, 1.0)], 0.6, 0.95, 0.85)]),
    'Ü': (0.9, [([(0.05, 0.03), (0.0, 0.7), (0.5, 1.0), (0.95, 0.72), (0.98, 0.04)], 1.0, 0.5, 1.1),
                ('nokta', 0.22, -0.2, 0.45), ('nokta', 0.75, -0.2, 0.45)]),
    'U': (0.9, [([(0.05, 0.03), (0.0, 0.7), (0.5, 1.0), (0.95, 0.72), (0.98, 0.04)], 1.0, 0.5, 1.1)]),
    'V': (0.92, [([(0.0, 0.0), (0.26, 0.5), (0.5, 1.0)], 1.05, 0.4, 1.0),
                 ([(0.5, 1.0), (0.75, 0.5), (1.0, 0.0)], 0.4, 0.95, 0.75)]),
    'Ş': (0.84, [([(0.9, 0.14), (0.55, 0.0), (0.14, 0.16), (0.24, 0.42), (0.7, 0.56), (0.9, 0.8), (0.55, 1.0), (0.08, 0.86)], 0.5, 0.75, 1.1),
                 ([(0.5, 1.0), (0.6, 1.1), (0.42, 1.2)], 0.55, 0.2, 0.6)]),
    'A': (0.96, [([(0.0, 1.0), (0.26, 0.5), (0.5, 0.0)], 0.8, 0.6, 0.9),
                 ([(0.5, 0.0), (0.76, 0.5), (1.0, 1.0)], 0.6, 1.0, 1.05),
                 ([(0.2, 0.64), (0.82, 0.6)], 0.7, 0.4, 0.7)]),
    'Z': (0.86, [([(0.04, 0.03), (0.5, 0.0), (0.96, 0.01)], 0.7, 0.55, 0.9),
                 ([(0.94, 0.04), (0.5, 0.5), (0.06, 0.98)], 0.6, 0.8, 1.15),
                 ([(0.05, 1.0), (0.5, 0.99), (1.0, 0.96)], 0.8, 0.4, 1.0)]),
    'M': (1.12, [([(0.0, 1.0), (0.04, 0.0)], 0.7, 1.05, None), ([(0.04, 0.0), (0.5, 0.62)], 0.9, 0.55, None),
                 ([(0.5, 0.62), (0.96, 0.0)], 0.55, 0.95, None), ([(0.96, 0.0), (1.06, 1.0)], 1.05, 0.45, None)]),
    # v32
    'P': (0.84, [([(0.16, 0.0), (0.14, 0.55), (0.12, 1.0)], 0.75, 1.05, 1.0),
                 ('yay', 0.44, 0.28, 0.3, -1.75, 1.75, 0.5, 0.8, 1.1)]),
    'H': (0.92, [([(0.1, 0.0), (0.08, 0.55), (0.06, 1.0)], 0.8, 1.05, 1.0),
                 ([(0.88, 0.0), (0.9, 0.55), (0.92, 1.0)], 0.7, 1.0, 0.95),
                 ([(0.1, 0.52), (0.5, 0.5), (0.9, 0.5)], 0.7, 0.45, 0.8)]),
    'Y': (0.92, [([(0.0, 0.0), (0.25, 0.28), (0.5, 0.55)], 1.0, 0.5, 0.9),
                 ([(1.0, 0.0), (0.75, 0.28), (0.5, 0.55)], 0.45, 0.9, 0.75),
                 ([(0.5, 0.55), (0.49, 0.78), (0.47, 1.0)], 0.9, 0.5, 1.0)]),
}


def _letters_word(word, c, w, h, rng, dark):
    """Sözcüğü GÜM! ile aynı fırça diliyle yazar (hafif eğik, kalın-ince, sıçrantı damlaları)."""
    sk = 0.18
    top, base = h * 0.22, h * 0.78
    L = base - top
    gap = 0.26
    tot = sum(_HARF[ch][0] for ch in word) + gap * (len(word) - 1)
    k = min(L * 0.95, w * 0.8 / tot)
    x0 = (w - tot * k) * 0.5 - (base - top) * sk * 0.5
    W = L * 0.31
    jy = 0.0

    def P(x, y):
        return (x + (base - y) * sk, y + jy)

    for ch in word:
        jy = rng.uniform(-0.04, 0.04) * L   # el yazısı: harf başına taban oynar
        gen, parts = _HARF[ch]
        for part in parts:
            if part[0] == 'nokta':
                _, px, py, r = part
                q = P(x0 + px * k, top + py * L)
                blob(c, *q, W * r, rng, jit=0.22)
                blob(dark[1], *q, W * r * 0.6, rng, jit=0.22)
            elif part[0] == 'yay':
                _, cx, cy, rr, a0, a1, w0, w1, wm = part
                pts = [(x0 + (cx + math.cos(a) * rr * 0.86) * k, top + (cy + math.sin(a) * rr) * L) for a in np.linspace(a0, a1, 16)]
                q = [P(*pt) for pt in pts]
                taper(c, q, W * w0, W * w1, wmid=W * wm)
                taper(dark[1], q, W * w0 * 0.55, W * w1 * 0.4, wmid=W * wm * 0.55)
            else:
                pts, w0, w1, wm = part
                q = [P(x0 + px * k, top + py * L) for px, py in pts]
                taper(c, q, W * w0, W * w1, wmid=(W * wm) if wm else None)
                taper(dark[1], q, W * w0 * 0.55, W * w1 * 0.4, wmid=(W * wm * 0.55) if wm else W * w0 * 0.55)
        x0 += (gen + gap) * k
    for i in range(16):
        drop(c, rng.uniform(0.05, 0.95) * w, rng.uniform(0.08, 0.95) * h, h * rng.uniform(0.006, 0.018), rng.uniform(-0.5, 0.5), rng.uniform(1.0, 2.0))


def shape_word(word, w, h, seed):
    rng = np.random.default_rng(seed)
    s, c = _surface(w, h)
    dark = _surface(w, h)
    _letters_word(word, c, w, h, rng, dark)
    cov = _arr(s)
    nz = fft_noise(h * SS, w * SS, beta=1.7, seed=seed + 1, fx=0.4, fy=1.0, up=HD)
    R = field(cov, 3.0, nz, spread=5.0)
    G = np.clip(down(_arr(dark[0])) * 0.95, 0, 1)
    ys, xs = grid(h, w)
    B = np.clip(xs / w * 0.9 + 0.1 * fft_noise(h, w, beta=1.5, seed=seed + 2, up=HD), 0, 1)
    A = fft_noise(h, w, beta=1.5, seed=seed + 3, up=HD)
    return np.dstack([R, G, B, A])


def shape_gum(w, h, seed):
    rng = np.random.default_rng(seed)
    s, c = _surface(w, h)
    dark = _surface(w, h)
    _letters_gum(c, w, h, rng, dark)
    cov = _arr(s)
    nz = fft_noise(h * SS, w * SS, beta=1.7, seed=seed + 1, fx=0.4, fy=1.0, up=HD)
    R = field(cov, 4.0, nz, spread=7.0)
    G = np.clip(down(_arr(dark[0])) * 0.95, 0, 1)
    ys, xs = grid(h, w)
    B = np.clip(xs / w * 0.9 + 0.1 * fft_noise(h, w, beta=1.5, seed=seed + 2, up=HD), 0, 1)
    A = fft_noise(h, w, beta=1.5, seed=seed + 3, up=HD)
    return np.dstack([R, G, B, A])


def shape_varak(size, seed, n=22):
    """Altın varak pulları: yırtık kenarlı küçük dörtgen / üçgen yapraklar, merkezden dışa saçılmış."""
    rng = np.random.default_rng(seed)
    S = size
    s, c = _surface(S, S)
    hot = _surface(S, S)
    cx = cy = S * 0.5
    for i in range(n):
        a = rng.uniform(0, 6.28)
        rr = S * (0.06 + 0.38 * math.sqrt(rng.random()))
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        sz = S * rng.uniform(0.018, 0.05) * (1.2 - rr / S)
        k = rng.integers(3, 6)
        ang = np.sort(rng.uniform(0, 6.28, k))
        path = skia.Path()
        for j, aa in enumerate(ang):
            q = (x + math.cos(aa) * sz * rng.uniform(0.6, 1.3), y + math.sin(aa) * sz * rng.uniform(0.6, 1.3))
            if j == 0:
                path.moveTo(*q)
            else:
                path.lineTo(*q)
        path.close()
        c.drawPath(path, _paint())
        if rng.random() < 0.45:
            hot[1].drawCircle(x, y, sz * 0.35, _paint())
    cov = _arr(s)
    R = field(cov, 0.0, None, spread=4.0)
    G = down(_arr(hot[0])) * 0.0          # varak: koyu yok
    r, _ = polar(S, S, cx, cy)
    B = np.clip(r / (S * 0.46), 0, 1)
    A = fft_noise(S, S, beta=1.0, seed=seed + 2, up=HD)
    return np.dstack([R, G, B, A])


def shape_crack(w, h, seed):
    """Yer yarığı: temas noktasından iki yana dallanan kırık çizgiler + yukarı kalkan kıymıklar. Taban y = 0,8h."""
    rng = np.random.default_rng(seed)
    s, c = _surface(w, h)
    dark = _surface(w, h)
    gy = h * 0.8
    cx = w * 0.5

    def branch(x, y, ang, L, wd, depth):
        pts = [(x, y)]
        n = 5
        for k in range(n):
            ang += rng.uniform(-0.45, 0.45)
            x += math.cos(ang) * L / n
            y += math.sin(ang) * L / n * 0.35
            y = min(max(y, gy - h * 0.25), gy + h * 0.15)
            pts.append((x, y))
        taper(c, pts, wd, 0.4, cap=True)
        taper(dark[1], pts, wd * 0.6, 0.3, cap=True)
        if depth > 0:
            for k in range(rng.integers(1, 3)):
                i = rng.integers(1, len(pts) - 1)
                branch(pts[i][0], pts[i][1], ang + rng.choice([-1, 1]) * rng.uniform(0.4, 0.9), L * 0.5, wd * 0.55, depth - 1)

    blob(c, cx, gy, h * 0.09, rng, jit=0.35)
    blob(dark[1], cx, gy, h * 0.06, rng, jit=0.35)
    for side in (-1, 1):
        for k in range(3):
            a = (0 if side > 0 else math.pi) + rng.uniform(-0.25, 0.25)
            branch(cx, gy + rng.uniform(-3, 3), a, w * rng.uniform(0.3, 0.45), h * rng.uniform(0.06, 0.1), 2)
    # yukarı kalkan kıymıklar (taş parçası)
    for i in range(10):
        x = cx + rng.uniform(-w * 0.25, w * 0.25)
        y = gy - h * rng.uniform(0.15, 0.6) * (1 - abs(x - cx) / (w * 0.5))
        sz = h * rng.uniform(0.02, 0.05)
        a0 = rng.uniform(0, 6.28)
        path = skia.Path()
        for j in range(4):
            aa = a0 + j * 1.57 + rng.uniform(-0.4, 0.4)
            q = (x + math.cos(aa) * sz, y + math.sin(aa) * sz * 0.8)
            path.moveTo(*q) if j == 0 else path.lineTo(*q)
        path.close()
        c.drawPath(path, _paint())
        dark[1].drawPath(path, _paint())
    cov = _arr(s)
    nz = fft_noise(h * SS, w * SS, beta=1.6, seed=seed + 1, up=HD)
    R = field(cov, 2.0, nz, spread=5.0)
    G = np.clip(down(_arr(dark[0])), 0, 1)
    ys, xs = grid(h, w)
    B = np.clip(np.abs(xs - cx) / (w * 0.5) * 0.9 + 0.1 * np.abs(ys - gy) / h, 0, 1)
    A = fft_noise(h, w, beta=1.5, seed=seed + 2, up=HD)
    return np.dstack([R, G, B, A])


def shape_seal(size, seed):
    """Mühür (hanko): kaba kenarlı yuvarlatılmış kare, içi dolu, kenarında baskı boşlukları."""
    rng = np.random.default_rng(seed)
    S = size
    s, c = _surface(S, S)
    m = S * 0.16
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(m, m, S - m, S - m), S * 0.06, S * 0.06)
    c.drawRRect(rr, _paint())
    cov = _arr(s)
    nz = fft_noise(S * SS, S * SS, beta=1.2, seed=seed + 1, up=HD)
    R = field(cov, 9.0, nz, spread=8.0)
    # baskı boşlukları (içte açık lekeler)
    holes = smoothstep(0.72, 0.8, fft_noise(S, S, beta=1.6, seed=seed + 2, up=HD))
    R = np.clip(R - holes * 0.3 * (R > 0.5), 0, 1)
    G = np.zeros_like(R)
    ys, xs = grid(S, S)
    B = np.clip((xs + ys) / (2 * S), 0, 1)
    A = fft_noise(S, S, beta=1.5, seed=seed + 3, up=HD)
    return np.dstack([R, G, B, A])


def build_atlas():
    C = 256
    atlas = np.zeros((1024 * HD, 1024 * HD, 4))
    meta = {}

    def put(name, arr, x, y):
        h, w = arr.shape[:2]
        atlas[y * HD:y * HD + h, x * HD:x * HD + w] = arr
        meta[name] = [x, y, w // HD, h // HD]

    put('splat_a', shape_splat(C, 201), 0, 0)
    put('splat_b', shape_splat(C, 211, n_lobe=5, n_flick=13, n_drop=46), C, 0)
    put('wash', shape_wash(C, 223), 2 * C, 0)
    put('varak', shape_varak(C, 227), 3 * C, 0)
    put('gum', shape_gum(2 * C, C, 229), 0, C)
    # v31: kullanılmayan seal hücresi ve iki boş hücre: yansıma sözcükleri (256x128); v32: kut / vus / cat -> pat / hayt / cak
    for i, (nm, wd) in enumerate([('cit', 'ÇIT!'), ('pat', 'PAT!'), ('viz', 'VIZ!'), ('tam', 'TAM!'), ('hayt', 'HAYT!'), ('cak', 'ÇAK!')]):
        cx, cy = [(3 * C, C), (3 * C, C), (2 * C, C), (2 * C, C), (3 * C, 3 * C), (3 * C, 3 * C)][i]
        put(nm, shape_word(wd, C, C // 2, 271 + 7 * i), cx, cy + (C // 2) * (i % 2))
    put('crack', shape_crack(4 * C, C, 241), 0, 2 * C)
    put('wash_b', shape_wash(C, 251), 0, 3 * C)
    put('varak_b', shape_varak(C, 257, n=34), C, 3 * C)
    put('splat_c', shape_splat(C, 263, n_lobe=9, n_flick=6, n_drop=24), 2 * C, 3 * C)
    return atlas, meta


def save_rgba(arr, path):
    a = (np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(a, 'RGBA').save(path, optimize=True)


def preview(atlas, br, path):
    def col(R, G, th=0.5):
        a = smoothstep(th - 0.04, th + 0.04, R)
        body = np.array([0.9, 0.62, 0.12]); ink = np.array([0.04, 0.03, 0.02]); rim = np.array([1.0, 0.88, 0.5])
        c = body[None, None] * smoothstep(0.5, 0.62, R)[..., None] + rim[None, None] * (1 - smoothstep(0.5, 0.62, R))[..., None]
        c = c * (1 - G[..., None]) + ink[None, None] * G[..., None]
        bg = np.array([0.93, 0.9, 0.82])
        return c * a[..., None] + bg[None, None] * (1 - a[..., None])
    A = col(atlas[..., 0], atlas[..., 1])
    # fırça: kâğıt üstünde siyah mürekkep (R eşik 0,5, G koyu, A tane)
    R, G, Ag = br[..., 0], br[..., 1], br[..., 3]
    a = smoothstep(0.42, 0.55, R) * (0.8 + 0.2 * Ag)
    ink = np.array([0.05, 0.04, 0.05]); mid = np.array([0.25, 0.22, 0.24])
    c = mid[None, None] * (1 - G[..., None]) + ink[None, None] * G[..., None]
    Bv = c * a[..., None] + np.array([0.93, 0.9, 0.82])[None, None] * (1 - a[..., None])
    hh = A.shape[0]
    out = np.zeros((hh + Bv.shape[0] + 8, max(A.shape[1], Bv.shape[1]), 3))
    out[:hh, :A.shape[1]] = A
    out[hh + 8:, :Bv.shape[1]] = Bv
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    br = brush_atlas()
    save_rgba(br, os.path.join(OUT, 'sanat_firca.png'))
    atlas, meta = build_atlas()
    save_rgba(atlas, os.path.join(OUT, 'sanat_fx.png'))
    with open(os.path.join(OUT, 'sanat_fx.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'size': [1024, 1024], 'shapes': meta}, f, indent=1)
    for nm in ('sanat_firca.png', 'sanat_fx.png'):
        ip = os.path.join(OUT, nm + '.import')
        if not os.path.exists(ip):
            with open(ip, 'w', encoding='utf-8', newline='\n') as f:
                f.write(IMPORT.format(name=nm))
    if '--onizleme' in sys.argv:
        preview(atlas, br, sys.argv[sys.argv.index('--onizleme') + 1])
    print('sanat_fx_ink: sanat_firca.png (8 fırça), sanat_fx.png (%d şekil), HD=%d' % (len(meta), HD))


if __name__ == '__main__':
    main()
