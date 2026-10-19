"""silah_fx_ink: v31 profesyonel silah mürekkebi dokuları (savuruş hilali fırçası + vuruş / menzil efekt atlası).
Renk YOK: dokular veri taşır, renk oyunda paletten gelir (InkFX.PALETTES, unsur paletleri).

assets/fx/ink/silah_firca.png  1024x512: 8 satır x 64 px hilal fırçası. shaders/ink_brush.gdshader (v31 hilal dalı) okur.
    u (yatay) = darbe boyunca 0 baş (bıçağın taze ucu) .. 1 kuyruk;  v (dikey) = enine 0 iç kenar (kabza yanı) .. 1 dış
    kenar (bıçak ağzı). Bir hilal fırçası İKİ YANLI: bıçak ağzı (v = 1) keskin, düz ve dolu; iç kenar (v = 0) kıl
    uçlarına ayrılan kuru fırça ("uçan ak" / hihaku); kuyruğa doğru kıllar tek tek kopar.
    R  mürekkep yükü (eşik 0,5)       G  koyu sumi (iç yarıda kıl boyu koyu çizgiler + baştaki basış havuzu)
    B  kıl kimliği (erime sırası)      A  kâğıt tanesi
    Satırlar: 0 kılıç (temiz hat), 1 hançer (ince hızlı), 2 ağır (kalın kuru, yarılan), 3 mızrak (uzun basılı),
    4 kırbaç (kurdele: iki kenar düzgün), 5 uzun sap (sulu kenarlı yıkama), 6 duman / yıkama (arka katman),
    7 hız telleri (yalnız kıllar)
assets/fx/ink/silah_fx.png  1024x1024 atlas (silah_fx.json), InkFX atlas kodlaması (shaders/ink_fx.gdshader):
    R işaretli uzaklık (0,5 kenar)  G koyu mürekkep / sıcak çekirdek  B çizim sırası  A erime gürültüsü
    Şekiller (hepsi +x yönlü: oyunda vuruş yönüne döndürülür):
      splash_a, splash_b   yönlü fırça sıçrantısı (kökte sumi, öne fırlayan fırça dili + yelpaze damlalar)
      blunt                küt darbe: ezik leke + kısa kalın dikenler
      drops_dir            yön konisinde damlalar (uzamış, irili ufaklı)
      cut_thin, cut_split  iğne uçlu ince kesik (sıcak çekirdek G), yarık çeşidi
      stroke_crit          kritik: basılmış başlı, kuyruğu kuru kıllara ayrılan tek kalın sumi darbesi (hat)
      flash                tek karelik darbe parlaması: uzun yatay iğne + kısa dik iğne + ince ışınlar
      twin_cut             hançer: iki paralel ince fiske
      seal                 kritik mührü (hanko): pürüzlü kare, oyulmuş tamga (negatif)
      ring_thin            saplama halkası: kuru kopuklu ince elips fırça
      flick_a, flick_b     tek kıvrık mürekkep fiskesi + uç damlası (savuruş sonu sıçrantısı)
      mist                 yumuşak sulu yıkama (yay bırakışı, duman)
      burst_ink            küçük sumi patlaması (ok saplanma)
      glint                ok ucu / parıltı: dört uçlu ince yıldız
      release              yay bırakışı: öne açılan kısa fırça telleri yelpazesi

Kullanım: cd tools/artgen && python silah_fx_ink.py [--onizleme out.png]
HD (2 kat): KY_HD=2 python silah_fx_ink.py  ardından  python hd_paket.py --paketle
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


# ------------------------------------------------------------------ hilal fırçası
def trail_row(W, H, seed, wet=0.8, dry=0.55, split=0.4, nb=70, inner=0.18, edge_k=1.0, dark=0.6, pool=0.7,
              ribbon=False, wash=False, strands=False):
    """Bir hilal fırçası satırı: u (W) baş -> kuyruk, v (H) iç -> bıçak ağzı."""
    rng = np.random.default_rng(seed)
    u = (_ax(W) / W)[None, :]
    v = (_ax(H) / H)[:, None]
    # bıçak ağzı: keskin, hafif basınç dalgası; iç kenar: kıl uçlarıyla pürüzlü, kuyrukta içten yenilir
    eo = 0.035 + 0.012 * periodic_1d(W, seed + 1, kmax=9, up=HD)[None, :]
    ei = inner * edge_k * (0.6 + 0.8 * smoothstep(0.0, 1.0, u)) + 0.05 * periodic_1d(W, seed + 2, kmax=24, up=HD)[None, :]
    if ribbon:
        ei = 0.05 + 0.012 * periodic_1d(W, seed + 2, kmax=9, up=HD)[None, :]
    env_o = smoothstep(eo, eo + 0.025, 1.0 - v)
    env_i = smoothstep(ei, ei + (0.03 if ribbon else 0.14), v)
    # kıllar: enine dar şeritler; iç tarafta ve kuyrukta kopar (uçan ak), bıçak tarafında dolu
    bri = np.zeros((H * HD, W * HD))
    drk = np.zeros((H * HD, W * HD))
    for j in range(nb):
        v0 = rng.uniform(0.0, 1.0)
        wid = rng.uniform(0.006, 0.024) * (1.7 if rng.random() < 0.1 else 1.0)
        m = periodic_1d(W, seed * 977 + j, kmax=13, up=HD)[None, :]
        g = periodic_1d(W, seed * 977 + j + 300, kmax=7, up=HD)[None, :]
        # kılın bittiği yer: iç kıllar erken biter (hilalin içi kuru), bıçak tarafı kuyruğa dek taşır
        life = rng.uniform(0.75, 1.25) - dry * rng.uniform(0.0, 0.5) * (1.25 - v0)
        fade = 1.0 - smoothstep(life - 0.2, life, u)
        brk = smoothstep(-0.75 + split * (1.25 - v0) * u * 1.4, -0.5 + split * (1.25 - v0) * u * 1.4, g)
        a = np.clip(0.88 + 0.3 * m, 0, 1) * fade * (0.1 + 0.9 * brk)
        prof = np.exp(-((v - v0) / wid) ** 2)
        bri = np.maximum(bri, prof * a)
        if v0 < 0.72 and rng.random() < 0.45:
            drk = np.maximum(drk, prof * a * smoothstep(0.5, 0.85, m))
    nz = fft_noise(H, W, beta=1.9, seed=seed + 7, fx=2.5, fy=0.12, up=HD)
    # ıslak gövde: bıçak tarafında ve başta dolu; içe ve kuyruğa doğru kurur
    wet_uv = wet * (1.0 - dry * smoothstep(0.1, 1.0, u) ** 0.9) * (0.55 + 0.45 * smoothstep(0.1, 0.75, v))
    body = np.clip(wet_uv * (0.5 + 0.65 * nz) + 0.3 * bri * wet_uv, 0, 1)
    if strands:
        body *= 0.0
    R = np.maximum(body, bri)
    # bıçak ağzı bandı her zaman dolu (keskin hat), kuyrukta incelir
    blade = smoothstep(0.86 + 0.08 * u, 0.93 + 0.05 * u, v) * (1.0 - smoothstep(0.75, 1.0, u)) * (0.0 if strands else 1.0)
    R = np.maximum(R, blade * 0.95)
    head = 1.0 - smoothstep(0.0, 0.06, u)
    R = np.maximum(R, head * 0.95 * (0.0 if strands else 1.0))
    # ıslak öz: gövdenin bıçağa yakın yarısı başta ve ortada boşluksuz (delikler yalnız iç kenarda ve kuyrukta)
    solid = smoothstep(0.3 + 0.25 * u, 0.55 + 0.2 * u, v) * (1.0 - smoothstep(0.3, 0.85, u)) * wet * (0.0 if strands else 1.0)
    R = np.maximum(R, solid * 0.9)
    # tek piksellik tane kırıntısı (karşıya kum gibi okunur) boyuna yumuşatılarak silinir
    R = ndimage.gaussian_filter(R, (0.45 * HD, 1.6 * HD), mode='nearest')
    # iç kenar: gövde zarfta biter, tek tek kıllar zarfın biraz içine taşar (kıl uçlu pürüzlü kenar)
    env_i2 = smoothstep(ei - 0.1, ei - 0.05, v) if not ribbon else env_i
    R = np.clip(np.maximum(R * env_i, ndimage.gaussian_filter(bri, (0.45 * HD, 1.6 * HD)) * env_i2 * 0.97) * env_o, 0, 1)
    if wash:
        # sulu yıkama: yumuşak, kenarda kuruma halkası (G), içinde granül
        gran = fft_noise(H, W, beta=1.1, seed=seed + 12, up=HD)
        R = np.clip((0.62 + 0.3 * nz - 0.25 * u) * env_o * env_i + 0.08 * (gran - 0.5), 0, 1)
    # koyu birikim (G): iç yarıda kıl boyu sumi çizgileri + iç kenarda toplanan mürekkep + baş havuzu; bıçak tarafında yok
    in_rim = smoothstep(0.16, 0.0, v - ei) * smoothstep(-0.03, 0.02, v - ei)
    side = 1.0 - smoothstep(0.45, 0.8, v)
    G = np.clip((drk * 0.85 + in_rim * 0.55 * (0.6 + 0.4 * nz)) * side * dark + pool * head * 0.8 * side, 0, 1) * (R > 0.2)
    if wash:
        o_rim = smoothstep(0.1, 0.0, (1.0 - v) - eo) + in_rim
        G = np.clip(o_rim * 0.6, 0, 1) * (R > 0.2)
    row = ndimage.uniform_filter1d(rng.random(H), 2, mode='nearest')
    if HD > 1:
        row = np.repeat(row, HD)
    B = np.clip(0.6 * row[:, None] + 0.4 * u, 0, 1) * np.ones_like(R)
    fib = fft_noise(H, W, beta=1.2, seed=seed + 9, fx=1.5, fy=0.25, up=HD)
    gr = fft_noise(H, W, beta=0.6, seed=seed + 10, up=HD)
    A = np.clip(0.55 * fib + 0.45 * gr, 0, 1)
    return np.dstack([R, G, B, A])


def trail_atlas():
    W, H = 1024, 64
    rows = [
        dict(seed=301, wet=0.9, dry=0.45, split=0.35, nb=78, inner=0.16, dark=0.55, pool=0.7),           # 0 kılıç
        dict(seed=311, wet=0.75, dry=0.6, split=0.55, nb=60, inner=0.2, dark=0.45, pool=0.5),            # 1 hançer
        dict(seed=317, wet=0.65, dry=0.85, split=0.8, nb=90, inner=0.24, dark=0.9, pool=0.8),            # 2 ağır
        dict(seed=331, wet=0.95, dry=0.35, split=0.25, nb=70, inner=0.1, dark=0.5, pool=0.9),            # 3 mızrak
        dict(seed=337, wet=0.85, dry=0.4, split=0.3, nb=56, ribbon=True, dark=0.35, pool=0.4),           # 4 kırbaç
        dict(seed=347, wet=0.9, dry=0.5, split=0.4, nb=64, inner=0.14, dark=0.4, pool=0.6),              # 5 uzun sap
        dict(seed=349, wet=0.8, dry=0.5, split=0.3, nb=40, inner=0.12, dark=0.0, pool=0.0, wash=True),   # 6 yıkama
        dict(seed=353, wet=0.0, dry=0.9, split=0.9, nb=26, inner=0.02, dark=0.0, pool=0.0, strands=True),  # 7 teller
    ]
    out = np.zeros((H * len(rows) * HD, W * HD, 4))
    for i, r in enumerate(rows):
        out[i * H * HD:(i + 1) * H * HD] = trail_row(W, H, **r)
    return out


# ------------------------------------------------------------------ vuruş / menzil şekilleri
def _B_dir(w, h, x0, y0, L):
    ys, xs = grid(h, w)
    return np.clip(np.hypot(xs - x0, (ys - y0) * 1.3) / L, 0, 1)


def shape_splash(S, seed, n_side=6, n_drop=26, curl=0.0):
    """Yönlü fırça sıçrantısı (+x): kökte küçük sumi göl, öne fırlayan ana fırça dili (basılı baş, incelen, ucu
    damlaya kopan), iki yanda daha kısa ikincil diller, koni içinde irili ufaklı uzamış damlalar."""
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    dark = _surface(S, S)
    x0, y0 = S * 0.2, S * 0.5
    blob(c, x0, y0, S * 0.085, rng, k=7, jit=0.3)
    blob(dark[1], x0, y0, S * 0.075, rng, k=9, jit=0.3)
    # ana dil
    L = S * 0.62
    b = rng.uniform(-0.12, 0.12) + curl
    pts = [(x0 + math.cos(b * t * t) * L * t, y0 + math.sin(b * t * t) * L * t) for t in np.linspace(0.0, 1.0, 6)]
    taper(c, pts, S * 0.11, S * 0.008, wmid=S * 0.075)
    taper(dark[1], pts[:4], S * 0.075, S * 0.01)
    drop(c, x0 + math.cos(b) * L * 1.07, y0 + math.sin(b) * L * 1.07, S * 0.016, b, 1.9)
    drop(c, x0 + math.cos(b) * L * 1.17, y0 + math.sin(b) * L * 1.17, S * 0.009, b, 1.6)
    for i in range(n_side):
        sg = 1 if i % 2 == 0 else -1
        a = sg * rng.uniform(0.25, 0.75)
        Ls = S * rng.uniform(0.22, 0.44) * (1.0 - 0.35 * abs(a))
        bb = rng.uniform(-0.25, 0.25)
        p = [(x0 + math.cos(a + bb * t * t) * Ls * t, y0 + math.sin(a + bb * t * t) * Ls * t) for t in np.linspace(0.15, 1.0, 5)]
        taper(c, p, S * rng.uniform(0.03, 0.055), 0.5, wmid=S * 0.03)
        if rng.random() < 0.8:
            drop(c, x0 + math.cos(a + bb) * Ls * 1.1, y0 + math.sin(a + bb) * Ls * 1.1, S * rng.uniform(0.007, 0.014), a, 1.7)
    for i in range(n_drop):
        a = rng.normal(0.0, 0.42)
        rr = S * rng.uniform(0.2, 0.74)
        if x0 + math.cos(a) * rr > S * 0.96 or abs(math.sin(a) * rr) > S * 0.44:
            continue
        drop(c, x0 + math.cos(a) * rr, y0 + math.sin(a) * rr, S * rng.uniform(0.004, 0.015) * (1.2 - rr / S), a, rng.uniform(1.4, 2.6))
    cov = _arr(s)
    nz = radial_streaks(S * SS, S * SS, x0 * SS, y0 * SS, seed + 3)
    R = field(cov, 4.0, nz)
    G = np.clip(down(_arr(dark[0])) * 0.9 + smoothstep(0.72, 0.88, down(nz)) * smoothstep(0.58, 0.72, R) * 0.35, 0, 1)
    B = np.clip(_B_dir(S, S, x0, y0, S * 0.8) * 0.9 + 0.1 * down(nz), 0, 1)
    A = fft_noise(S, S, beta=1.6, seed=seed + 9, up=HD)
    return np.dstack([R, G, B, A])


def shape_blunt(S, seed):
    """Küt darbe: ezik, loblu sumi lekesi + kısa kalın dikenler (ön yarıda uzun) + kenar damlaları."""
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    dark = _surface(S, S)
    cx, cy = S * 0.42, S * 0.5
    blob(c, cx, cy, S * 0.13, rng, k=9, jit=0.32)
    blob(dark[1], cx, cy, S * 0.09, rng, k=7, jit=0.35)
    for i in range(11):
        a = rng.uniform(0, 6.28)
        fw = 0.55 + 0.45 * math.cos(a)
        Ls = S * rng.uniform(0.18, 0.3) * (0.6 + 0.7 * fw)
        p = [(cx + math.cos(a) * Ls * t, cy + math.sin(a) * Ls * t) for t in np.linspace(0.3, 1.0, 4)]
        taper(c, p, S * rng.uniform(0.05, 0.08), 0.6, wmid=S * 0.045)
        if rng.random() < 0.6:
            drop(c, cx + math.cos(a) * Ls * 1.15, cy + math.sin(a) * Ls * 1.15, S * rng.uniform(0.008, 0.016), a, 1.5)
    for i in range(16):
        a = rng.normal(0, 0.9)
        rr = S * rng.uniform(0.25, 0.48)
        drop(c, cx + math.cos(a) * rr, cy + math.sin(a) * rr, S * rng.uniform(0.005, 0.013), a, rng.uniform(1.2, 2.0))
    cov = _arr(s)
    nz = radial_streaks(S * SS, S * SS, cx * SS, cy * SS, seed + 2)
    R = field(cov, 5.0, nz)
    G = np.clip(down(_arr(dark[0])) * 0.9, 0, 1)
    r, _ = polar(S, S, cx, cy)
    B = np.clip(r / (S * 0.5) * 0.9 + 0.1 * down(nz), 0, 1)
    A = fft_noise(S, S, beta=1.5, seed=seed + 4, up=HD)
    return np.dstack([R, G, B, A])


def shape_drops_dir(S, seed):
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    x0, y0 = S * 0.12, S * 0.5
    for i in range(34):
        a = rng.normal(0.0, 0.38)
        rr = S * rng.uniform(0.12, 0.84)
        x, y = x0 + math.cos(a) * rr, y0 + math.sin(a) * rr
        if x > S * 0.97 or abs(y - y0) > S * 0.45:
            continue
        drop(c, x, y, S * rng.uniform(0.006, 0.024) * (1.15 - 0.6 * rr / S), a, rng.uniform(1.6, 3.0))
    cov = _arr(s)
    R = field(cov, 0.0, None, spread=6.0)
    B = _B_dir(S, S, x0, y0, S * 0.86)
    A = fft_noise(S, S, beta=1.5, seed=seed + 2, up=HD)
    return np.dstack([R, np.zeros_like(R), B, A])


def shape_cut(w, h, seed, split=False):
    """İğne uçlu ince kesik: %30'da en kalın, iki uç kıl inceliğinde; sıcak çekirdek (G) ortada ince."""
    rng = np.random.default_rng(seed)
    s, c = _surface(w, h)
    core = _surface(w, h)
    y0 = h * 0.5
    pts = [(w * 0.02, y0 + h * 0.08), (w * 0.3, y0 + h * 0.01), (w * 0.66, y0 - h * 0.04), (w * 0.98, y0 - h * 0.1)]
    taper(c, pts, 0.4, 0.3, wmid=h * 0.13, cap=False)
    taper(core[1], pts, 0.25, 0.2, wmid=h * 0.045, cap=False)
    if split:
        p2 = [(w * 0.22, y0 + h * 0.22), (w * 0.5, y0 + h * 0.16), (w * 0.8, y0 + h * 0.08)]
        taper(c, p2, 0.3, 0.3, wmid=h * 0.04, cap=False)
    for i in range(7):
        x = w * rng.uniform(0.45, 0.97)
        drop(c, x, y0 + h * rng.uniform(-0.3, 0.3), h * rng.uniform(0.01, 0.022), rng.uniform(-0.3, 0.3), 2.4)
    cov = _arr(s)
    nz = fft_noise(h * SS, w * SS, beta=1.6, seed=seed + 1, fx=0.1, fy=1.5, up=HD)
    R = field(cov, 2.5, nz, spread=5.0)
    G = down(_arr(core[0]))
    ys, xs = grid(h, w)
    B = np.clip(xs / w, 0, 1)
    A = fft_noise(h, w, beta=1.5, seed=seed + 2, up=HD)
    return np.dstack([R, G, B, A])


def shape_stroke(w, h, seed):
    """Kritik hat darbesi: sol başta basılmış (yuvarlak, hafif taşkın) baş, ortada dolgun, kuyrukta kuru kıllara
    ayrılan tek kalın sumi darbesi; hafif yay. G: başta sumi havuzu + kıl çizgileri (oyunda koyu biçem)."""
    rng = np.random.default_rng(seed)
    s, c = _surface(w, h)
    y0 = h * 0.52
    pts = [(w * 0.06, y0 + h * 0.06), (w * 0.3, y0 - h * 0.02), (w * 0.62, y0 - h * 0.06), (w * 0.95, y0 - h * 0.02)]
    taper(c, pts, h * 0.42, h * 0.04, wmid=h * 0.36, cap=True)
    blob(c, w * 0.06, y0 + h * 0.04, h * 0.25, rng, jit=0.18)
    cov = _arr(s)
    ys, xs = grid(h * SS, w * SS)
    # kuru fırça: kuyruğa doğru boyuna kıl boşlukları (kapsamadan oyulur)
    st = fft_noise(h * SS, w * SS, beta=1.5, seed=seed + 1, fx=0.06, fy=2.2, up=HD)
    t = np.clip(xs / (w * SS), 0, 1)
    cov = cov * (st > (0.18 + 0.55 * smoothstep(0.35, 1.0, t)))
    R = field(cov, 2.0, st, spread=5.0)
    G = np.clip(0.75 + 0.25 * down(st), 0, 1)
    ys1, xs1 = grid(h, w)
    B = np.clip(xs1 / w, 0, 1)
    A = fft_noise(h, w, beta=1.5, seed=seed + 2, up=HD)
    return np.dstack([R, G, B, A])


def shape_flash(S, seed):
    """Tek karelik darbe parlaması: uzun yatay iğne + kısa dik iğne + iki ince çapraz ışın; G = sıcak çekirdek."""
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    core = _surface(S, S)
    cx = cy = S * 0.5
    for a, L, wd in ((0, 0.48, 0.05), (math.pi, 0.48, 0.05), (math.pi / 2, 0.24, 0.04), (-math.pi / 2, 0.24, 0.04),
                     (0.5, 0.17, 0.018), (math.pi + 0.5, 0.17, 0.018), (-0.6, 0.14, 0.016), (math.pi - 0.6, 0.14, 0.016)):
        taper(c, [(cx, cy), (cx + math.cos(a) * S * L, cy + math.sin(a) * S * L)], S * wd, 0.3)
        taper(core[1], [(cx, cy), (cx + math.cos(a) * S * L * 0.75, cy + math.sin(a) * S * L * 0.75)], S * wd * 0.45, 0.2)
    c.drawCircle(cx, cy, S * 0.035, _paint())
    core[1].drawCircle(cx, cy, S * 0.03, _paint())
    cov = _arr(s)
    R = field(cov, 0.0, None, spread=5.0)
    G = down(_arr(core[0]))
    r, _ = polar(S, S, cx, cy)
    B = np.clip(r / (S * 0.5), 0, 1)
    A = fft_noise(S, S, beta=1.5, seed=seed + 2, up=HD)
    return np.dstack([R, G, B, A])


def shape_twin(S, seed):
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    core = _surface(S, S)
    for k, off in enumerate((-0.09, 0.09)):
        p = [(S * 0.08, S * (0.62 + off)), (S * 0.5, S * (0.5 + off) - S * 0.03), (S * 0.94, S * (0.36 + off))]
        taper(c, p, 0.4, 0.3, wmid=S * (0.05 if k == 0 else 0.04), cap=False)
        taper(core[1], p, 0.2, 0.2, wmid=S * 0.016, cap=False)
    for i in range(6):
        drop(c, S * rng.uniform(0.6, 0.95), S * rng.uniform(0.25, 0.65), S * rng.uniform(0.006, 0.012), -0.3, 2.2)
    cov = _arr(s)
    nz = fft_noise(S * SS, S * SS, beta=1.6, seed=seed + 1, fx=0.1, fy=1.4, up=HD)
    R = field(cov, 2.0, nz, spread=5.0)
    G = down(_arr(core[0]))
    ys, xs = grid(S, S)
    B = np.clip(xs / S, 0, 1)
    A = fft_noise(S, S, beta=1.5, seed=seed + 2, up=HD)
    return np.dstack([R, G, B, A])


# Kayı tamgası benzeri oyma (mühür içinde negatif): iki ok ucu + dik çizgi
def shape_seal(S, seed):
    """Kritik mührü: pürüzlü kenarlı kare hanko, içinde oyulmuş tamga (kapsama dışı = kâğıt rengi görünür)."""
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    m = S * 0.2
    path = skia.Path()
    n = 64
    pts = []
    for i in range(n):
        t = i / n
        side = int(t * 4)
        f = t * 4 - side
        x, y = [(m + f * (S - 2 * m), m), (S - m, m + f * (S - 2 * m)), (S - m - f * (S - 2 * m), S - m), (m, S - m - f * (S - 2 * m))][side]
        j = S * 0.012
        pts.append((x + rng.uniform(-j, j), y + rng.uniform(-j, j)))
    path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    path.close()
    c.drawPath(path, _paint())
    # tamga: oyma (Clear karışımı)
    cut = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kClear)
    cx = S * 0.5
    stroke = S * 0.055

    def line(a, b, w=stroke):
        p = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kClear, StrokeWidth=w, Style=skia.Paint.kStroke_Style,
                       StrokeCap=skia.Paint.kRound_Cap)
        c.drawLine(a[0], a[1], b[0], b[1], p)

    line((cx, S * 0.3), (cx, S * 0.72))
    line((cx - S * 0.17, S * 0.36), (cx, S * 0.5))
    line((cx + S * 0.17, S * 0.36), (cx, S * 0.5))
    line((cx - S * 0.13, S * 0.68), (cx + S * 0.13, S * 0.68), stroke * 0.8)
    cov = _arr(s)
    nz = fft_noise(S * SS, S * SS, beta=1.4, seed=seed + 1, up=HD)
    # mühür mürekkebi düzensiz basılır: tanede boşluklar
    cov = cov * (nz > 0.22)
    R = field(cov, 2.0, nz, spread=4.0)
    r, _ = polar(S, S, S * 0.5, S * 0.5)
    B = np.clip(r / (S * 0.45), 0, 1)
    A = fft_noise(S, S, beta=1.5, seed=seed + 2, up=HD)
    return np.dstack([R, np.zeros_like(R), B, A])


def shape_ring_thin(S, seed):
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    cx = cy = S * 0.5
    a0 = rng.uniform(0, 6.28)
    pts = [(cx + math.cos(a0 + 2 * math.pi * 0.92 * t) * S * 0.43, cy + math.sin(a0 + 2 * math.pi * 0.92 * t) * S * 0.43)
           for t in np.linspace(0, 1, 56)]
    taper(c, pts, S * 0.045, S * 0.004, wmid=S * 0.028)
    cov = _arr(s)
    rr, aa = polar(S * SS, S * SS, cx * SS, cy * SS)
    nz2 = fft_noise(512, 64, beta=1.7, seed=seed + 3, fx=1.0, fy=0.12)
    st = ndimage.map_coordinates(nz2, [np.clip(rr / (S * SS * 0.5) * 511, 0, 511), ((aa / (2 * math.pi)) % 1.0) * 64], order=1, mode='wrap')
    R = field(cov, 4.0, st, spread=4.0)
    r1, a1 = polar(S, S, cx, cy)
    B = ((a1 - a0) % (2 * math.pi)) / (2 * math.pi)
    A = fft_noise(S, S, beta=1.5, seed=seed + 5, up=HD)
    return np.dstack([R, np.zeros_like(R), B, A])


def shape_flick(w, h, seed):
    """Tek kıvrık fiske: kökte kalın, kıvrılarak incelen dil + uçtan kopan iki damla (+x yönü)."""
    rng = np.random.default_rng(seed)
    s, c = _surface(w, h)
    y0 = h * 0.62
    bend = rng.uniform(0.35, 0.55)
    L = w * 0.78
    pts = [(w * 0.05 + math.cos(-bend * t * t) * L * t, y0 + math.sin(-bend * t * t) * L * t) for t in np.linspace(0, 1, 6)]
    taper(c, pts, h * 0.16, 0.6, wmid=h * 0.1)
    ex, ey = pts[-1]
    drop(c, ex + w * 0.06, ey - h * 0.05, h * 0.04, -bend, 1.8)
    drop(c, ex + w * 0.12, ey - h * 0.1, h * 0.025, -bend, 1.6)
    cov = _arr(s)
    nz = fft_noise(h * SS, w * SS, beta=1.6, seed=seed + 1, fx=0.12, fy=1.4, up=HD)
    R = field(cov, 2.5, nz, spread=5.0)
    ys, xs = grid(h, w)
    B = np.clip(xs / w, 0, 1)
    G = np.clip(1.0 - smoothstep(0.0, 0.5, B), 0, 1) * 0.8
    A = fft_noise(h, w, beta=1.5, seed=seed + 2, up=HD)
    return np.dstack([R, G, B, A])


def shape_mist(S, seed):
    """Yumuşak sulu yıkama: loblu, kenarda kuruma halkası (G), granüllü (A)."""
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    cx = cy = S * 0.5
    blob(c, cx, cy, S * 0.26, rng, k=6, jit=0.25)
    for i in range(5):
        a = rng.uniform(0, 6.28)
        blob(c, cx + math.cos(a) * S * 0.16, cy + math.sin(a) * S * 0.12, S * rng.uniform(0.1, 0.16), rng, jit=0.3)
    cov = _arr(s)
    nz = fft_noise(S * SS, S * SS, beta=2.0, seed=seed + 1, up=HD)
    R = field(cov, 14.0, nz, spread=12.0)
    G = np.clip(smoothstep(0.62, 0.5, R) * smoothstep(0.46, 0.5, R), 0, 1) * 0.7
    r, _ = polar(S, S, cx, cy)
    B = np.clip(r / (S * 0.48), 0, 1)
    A = fft_noise(S, S, beta=1.1, seed=seed + 2, up=HD)
    return np.dstack([R, G, B, A])


def shape_burst_ink(S, seed):
    """Küçük sumi patlaması (ok saplanması): sıkı çekirdek, 7 kısa sivri diken (biri uzun, geri yönde), damlalar."""
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    dark = _surface(S, S)
    cx = cy = S * 0.5
    blob(c, cx, cy, S * 0.08, rng, jit=0.3)
    blob(dark[1], cx, cy, S * 0.06, rng, jit=0.3)
    for i in range(7):
        a = math.pi + rng.normal(0, 0.9) if i < 5 else rng.uniform(0, 6.28)
        Ls = S * rng.uniform(0.18, 0.4)
        taper(c, [(cx, cy), (cx + math.cos(a) * Ls * 0.6, cy + math.sin(a) * Ls * 0.6), (cx + math.cos(a + 0.1) * Ls, cy + math.sin(a + 0.1) * Ls)],
              S * rng.uniform(0.035, 0.06), 0.4)
        drop(c, cx + math.cos(a) * Ls * 1.14, cy + math.sin(a) * Ls * 1.14, S * rng.uniform(0.008, 0.015), a, 1.7)
    cov = _arr(s)
    nz = radial_streaks(S * SS, S * SS, cx * SS, cy * SS, seed + 1)
    R = field(cov, 3.0, nz)
    G = down(_arr(dark[0])) * 0.9
    r, _ = polar(S, S, cx, cy)
    B = np.clip(r / (S * 0.45), 0, 1)
    A = fft_noise(S, S, beta=1.5, seed=seed + 2, up=HD)
    return np.dstack([R, G, B, A])


def shape_glint(S, seed):
    s, c = _surface(S, S)
    core = _surface(S, S)
    cx = cy = S * 0.5
    for a, L in ((0, 0.46), (math.pi, 0.46), (math.pi / 2, 0.3), (-math.pi / 2, 0.3)):
        taper(c, [(cx, cy), (cx + math.cos(a) * S * L, cy + math.sin(a) * S * L)], S * 0.07, 0.2)
        taper(core[1], [(cx, cy), (cx + math.cos(a) * S * L * 0.6, cy + math.sin(a) * S * L * 0.6)], S * 0.035, 0.2)
    cov = _arr(s)
    R = field(cov, 0.0, None, spread=4.0)
    G = down(_arr(core[0]))
    r, _ = polar(S, S, cx, cy)
    B = np.clip(r / (S * 0.46), 0, 1)
    A = fft_noise(S, S, beta=1.5, seed=seed + 2, up=HD)
    return np.dstack([R, G, B, A])


def shape_release(S, seed):
    """Yay bırakışı: kökten öne (+x) açılan 9 kısa fırça teli + iki yanda kıvrık tel; G kökte."""
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    x0, y0 = S * 0.18, S * 0.5
    for i in range(9):
        a = rng.uniform(-0.8, 0.8)
        L = S * rng.uniform(0.3, 0.7) * (1.0 - 0.45 * abs(a))
        bb = rng.uniform(-0.2, 0.2)
        p = [(x0 + math.cos(a + bb * t * t) * L * t, y0 + math.sin(a + bb * t * t) * L * t) for t in np.linspace(0.25, 1.0, 5)]
        taper(c, p, S * rng.uniform(0.018, 0.035), 0.3, wmid=S * 0.02)
    for sg in (-1, 1):
        p = [(x0 + S * 0.05, y0 + sg * S * 0.05), (x0 + S * 0.2, y0 + sg * S * 0.2), (x0 + S * 0.42, y0 + sg * S * 0.24)]
        taper(c, p, S * 0.03, 0.3, wmid=S * 0.022)
    cov = _arr(s)
    nz = fft_noise(S * SS, S * SS, beta=1.6, seed=seed + 1, fx=0.15, fy=1.3, up=HD)
    R = field(cov, 2.0, nz, spread=5.0)
    B = _B_dir(S, S, x0, y0, S * 0.75)
    G = np.clip(1.0 - smoothstep(0.0, 0.35, B), 0, 1) * 0.7
    A = fft_noise(S, S, beta=1.5, seed=seed + 2, up=HD)
    return np.dstack([R, G, B, A])


def build_atlas():
    C = 256
    atlas = np.zeros((1024 * HD, 1024 * HD, 4))
    meta = {}

    def put(name, arr, x, y):
        h, w = arr.shape[:2]
        atlas[y * HD:y * HD + h, x * HD:x * HD + w] = arr
        meta[name] = [x, y, w // HD, h // HD]

    put('splash_a', shape_splash(C, 401), 0, 0)
    put('splash_b', shape_splash(C, 409, n_side=8, n_drop=34, curl=0.15), C, 0)
    put('blunt', shape_blunt(C, 419), 2 * C, 0)
    put('drops_dir', shape_drops_dir(C, 421), 3 * C, 0)
    put('cut_thin', shape_cut(2 * C, C // 4, 431), 0, C)
    put('cut_split', shape_cut(2 * C, C // 4, 433, split=True), 0, C + C // 4)
    put('stroke_crit', shape_stroke(2 * C, C // 2, 439), 0, C + C // 2)
    put('flash', shape_flash(C, 443), 2 * C, C)
    put('twin_cut', shape_twin(C, 449), 3 * C, C)
    put('seal', shape_seal(C, 457), 0, 2 * C)
    put('ring_thin', shape_ring_thin(C, 461), C, 2 * C)
    put('flick_a', shape_flick(C, C // 2, 463), 2 * C, 2 * C)
    put('flick_b', shape_flick(C, C // 2, 467), 2 * C, 2 * C + C // 2)
    put('mist', shape_mist(C, 479), 3 * C, 2 * C)
    put('burst_ink', shape_burst_ink(C, 487), 0, 3 * C)
    put('glint', shape_glint(C, 491), C, 3 * C)
    put('release', shape_release(C, 499), 2 * C, 3 * C)
    return atlas, meta


def save_rgba(arr, path):
    a = (np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(a, 'RGBA').save(path, optimize=True)


def preview(atlas, br, path):
    def col(R, G, th=0.5):
        a = smoothstep(th - 0.03, th + 0.03, R)
        body = np.array([0.85, 0.06, 0.06]); ink = np.array([0.04, 0.02, 0.03])
        c = body[None, None] * (1 - G[..., None]) + ink[None, None] * G[..., None]
        bg = np.array([0.93, 0.89, 0.8])
        return c * a[..., None] + bg[None, None] * (1 - a[..., None])
    s = HD
    A = col(atlas[..., 0], atlas[..., 1])
    Bv = col(br[..., 0], br[..., 1])
    out = np.ones((A.shape[0] + 8 * s + Bv.shape[0], A.shape[1], 3)) * 0.2
    out[:A.shape[0]] = A
    out[A.shape[0] + 8 * s:] = Bv
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    br = trail_atlas()
    save_rgba(br, os.path.join(OUT, 'silah_firca.png'))
    atlas, meta = build_atlas()
    save_rgba(atlas, os.path.join(OUT, 'silah_fx.png'))
    if HD == 1:
        with open(os.path.join(OUT, 'silah_fx.json'), 'w', encoding='utf-8') as f:
            json.dump({'size': [1024, 1024], 'shapes': meta}, f, indent=1)
        for nm in ('silah_firca.png', 'silah_fx.png'):
            ip = os.path.join(OUT, nm + '.import')
            if not os.path.exists(ip):
                with open(ip, 'w', encoding='utf-8') as f:
                    f.write(IMPORT.format(name=nm))
    if '--onizleme' in sys.argv:
        preview(atlas, br, sys.argv[sys.argv.index('--onizleme') + 1])
    print('silah_fx_ink: silah_firca.png, silah_fx.png (%d şekil), HD=%d' % (len(meta), HD))


if __name__ == '__main__':
    main()
