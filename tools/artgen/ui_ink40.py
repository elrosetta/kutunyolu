"""ui_ink40: v40 arayüz cilası dokuları (scripts/ui/InkUI.gd "v40") -> assets/ui/ink/*.png

ui_ink.py'nin fırça / gürültü / skia yardımcılarını kullanır; aynı yoğunluk kuralı (3 doku pikseli = 1 arayüz birimi).
Hepsi beyaz maske (modulate ile renklenir) ya da önceden boyanmış parşömen.

  kilim.png       keçe / kilim kenar şeridi: koçboynuzlu eşkenar dörtgen dizisi (yatay döşenir; panel üst kenarı, boss ad levhası)
  orkhon.png      Orkhon (Köktürk) harfleri şeridi: süs aksanı (başlık ekranı, bölüm pankartı kenarları)
  scroll.png      parşömen tomar çerçevesi: iki yanda sarılı uçlar, ortada kâğıt (9 dilim, kenar 96 px; küçük harita)
  smoke.png       mürekkep dumanı lekesi (başlık ekranında süzülür)
  wipe.png        fırça perdesi: ekran açılış / kapanış sürmesi (geniş darbe, ön kenarı dağınık)
  seal_round.png  yuvarlak mühür (Başla damgası, seçim imi)
  pad.png         kol (gamepad) simgeleri 128 px hücre: A B X Y LB RB LT RT ↑ ↓ ← → LS RS ≡ ⧉
  icons2.png      v40 ek simgeler 128 px hücre: ates buz zehir kan damga nazar nisan harita ok yildiz hiz nakis muhur
  logo.png        "Kut'un Yolu" kuru fırça kaligrafisi (Kaushan Script tabanı, kenarı pürüzlü, kıl izli, sıçrantılı; 2048 px)

Kullanım: cd tools/artgen && python ui_ink40.py [ad ...]     HD: KY_HD=2 python ui_ink40.py (logo HD'de üretilmez)
"""
import math
import os
import sys

import numpy as np
import skia
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hdpack import HD
from ui_ink import (OUT, brush, fbm2, noise1, sstep, save_mask, down, sk_canvas, sk_mask, paint, poly, disk,
                    write_imports)

FONTS = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'ui', 'fonts')


def _dry(m, rng, amount=0.35, scale=6, aniso=(0.25, 30.0)):
    """Maskeye kuru fırça kıl boşlukları: uzun yatay gürültü eşiklenir."""
    h, w = m.shape
    streak = fbm2(h, w, scale, rng, 3, aniso=aniso)
    streak = (streak - streak.mean()) / (streak.std() + 1e-6)
    gap = sstep(1.1, 1.6, streak + (1.0 - amount) * 1.2)
    return m * (1.0 - gap * 0.85)


def _rough(m, rng, amp=1.6, scale=5):
    """Kenar pürüzü: işaretli uzaklığa gürültü eklenir."""
    h, w = m.shape
    inside = ndimage.distance_transform_edt(m > 0.5)
    outside = ndimage.distance_transform_edt(m <= 0.5)
    sd = inside - outside
    nz = fbm2(h, w, scale * HD, rng, 4)
    return sstep(-1.0, 1.0, sd + nz * amp * HD)


# ------------------------------------------------------------------ kilim şeridi
def kilim(W=1024, H=96, seed=301):
    S = 4
    n_w, n_h = W * S * HD, H * S * HD
    surf, c = sk_canvas(n_w, n_h)
    P = paint()
    period = n_w / 8.0
    cy = n_h * 0.5
    lw = n_h * 0.07
    pl = paint(lw)
    for i in range(8):
        cx = period * (i + 0.5)
        # eşkenar dörtgen (elibelinde gövdesi) ve içinde boş dörtgen
        d = n_h * 0.3
        c.drawPath(poly([(cx / n_h, (cy - d) / n_h), ((cx + d * 0.8) / n_h, cy / n_h), (cx / n_h, (cy + d) / n_h), ((cx - d * 0.8) / n_h, cy / n_h)], n_h), P)
        clr = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kClear)
        d2 = d * 0.42
        c.drawPath(poly([(cx / n_h, (cy - d2) / n_h), ((cx + d2 * 0.8) / n_h, cy / n_h), (cx / n_h, (cy + d2) / n_h), ((cx - d2 * 0.8) / n_h, cy / n_h)], n_h), clr)
        c.drawCircle(cx, cy, n_h * 0.045, P)
        # koçboynuzu kancaları: dörtgenin iki yanında dışa kıvrılan çengeller
        for f in (-1, 1):
            x0 = cx + f * d * 0.95
            path = skia.Path()
            path.moveTo(x0, cy)
            path.lineTo(x0 + f * n_h * 0.14, cy)
            path.lineTo(x0 + f * n_h * 0.14, cy - n_h * 0.2)
            path.lineTo(x0 + f * n_h * 0.04, cy - n_h * 0.2)
            c.drawPath(path, pl)
            path = skia.Path()
            path.moveTo(x0 + f * n_h * 0.14, cy)
            path.lineTo(x0 + f * n_h * 0.14, cy + n_h * 0.2)
            path.lineTo(x0 + f * n_h * 0.04, cy + n_h * 0.2)
            c.drawPath(path, pl)
    # üst / alt ince şeritler ve küçük zikzak (su yolu)
    for yy in (n_h * 0.1, n_h * 0.9):
        c.drawRect(skia.Rect(0, yy - lw * 0.45, n_w, yy + lw * 0.45), P)
    zz = skia.Path()
    step = n_w / 64.0
    for k, yy in enumerate((n_h * 0.19, n_h * 0.81)):
        zz = skia.Path()
        zz.moveTo(0, yy)
        for i in range(65):
            zz.lineTo(i * step, yy + (n_h * 0.035 if (i + k) % 2 == 0 else -n_h * 0.035))
        c.drawPath(zz, paint(lw * 0.55))
    m = sk_mask(surf)
    rng = np.random.default_rng(seed)
    m *= 1.0 - sstep(0.5, 0.95, fbm2(n_h, n_w, 5 * S, rng, 3, aniso=(1, 2))) * 0.5   # keçe dokusu
    save_mask(down(m, S), 'kilim.png')


# ------------------------------------------------------------------ Orkhon harf şeridi
# Köktürk harflerinin basit çizgi yorumları (birim kare; süs amaçlı, okunurluk aranmaz)
ORKHON = [
    [[(0.5, 0.1), (0.5, 0.9)], [(0.5, 0.5), (0.85, 0.2)]],                                  # ı / i
    [[(0.2, 0.15), (0.8, 0.5), (0.2, 0.85)]],                                                 # o / u
    [[(0.5, 0.9), (0.5, 0.45)], [(0.5, 0.45), (0.2, 0.1)], [(0.5, 0.45), (0.8, 0.1)]],        # l
    [[(0.25, 0.1), (0.25, 0.9)], [(0.25, 0.1), (0.75, 0.5), (0.25, 0.9)]],                    # y (D)
    [[(0.2, 0.9), (0.5, 0.1), (0.8, 0.9)], [(0.35, 0.55), (0.65, 0.55)]],                     # a (üçgen)
    [[(0.3, 0.1), (0.3, 0.9)], [(0.3, 0.5), (0.75, 0.5)], [(0.75, 0.1), (0.75, 0.9)]],        # h / t
    [[(0.5, 0.1), (0.5, 0.9)], [(0.25, 0.3), (0.5, 0.1), (0.75, 0.3)], [(0.25, 0.7), (0.5, 0.9), (0.75, 0.7)]],   # ŋ
    [[(0.2, 0.2), (0.8, 0.8)], [(0.8, 0.2), (0.2, 0.8)]],                                     # q (çarpı)
    [[(0.5, 0.1), (0.5, 0.9)], [(0.2, 0.9), (0.8, 0.9)], [(0.3, 0.35), (0.7, 0.35)]],         # s / ş
    [[(0.25, 0.9), (0.25, 0.1), (0.75, 0.5), (0.25, 0.5)]],                                   # k
    [[(0.2, 0.1), (0.5, 0.9), (0.8, 0.1)]],                                                   # r (V)
    [[(0.3, 0.1), (0.3, 0.9)], [(0.3, 0.1), (0.7, 0.1), (0.7, 0.4), (0.3, 0.4)]],             # b
]


def orkhon(W=1024, H=96, seed=311):
    S = 4
    n_w, n_h = W * S * HD, H * S * HD
    surf, c = sk_canvas(n_w, n_h)
    cell = n_w / 16.0
    pl = paint(n_h * 0.075)
    for i in range(16):
        g = ORKHON[i % len(ORKHON)]
        ox = cell * i + cell * 0.2
        gw = cell * 0.6
        gh = n_h * 0.62
        oy = n_h * 0.19
        for seg in g:
            path = skia.Path()
            path.moveTo(ox + seg[0][0] * gw, oy + seg[0][1] * gh)
            for (x, y) in seg[1:]:
                path.lineTo(ox + x * gw, oy + y * gh)
            c.drawPath(path, pl)
        # harf arası nokta (Orkhon yazıtlarında sözcük ayracı ':')
        c.drawCircle(cell * (i + 1), n_h * 0.4, n_h * 0.035, paint())
        c.drawCircle(cell * (i + 1), n_h * 0.6, n_h * 0.035, paint())
    m = sk_mask(surf)
    rng = np.random.default_rng(seed)
    m = _dry(m, rng, 0.3, 5 * S)
    m *= 1.0 - sstep(0.55, 0.95, fbm2(n_h, n_w, 4 * S, rng, 3)) * 0.4
    save_mask(down(m, S), 'orkhon.png')


# ------------------------------------------------------------------ parşömen tomar (9 dilim, kenar 96)
def scroll(W=1024, H=512, seed=321):
    rng = np.random.default_rng(seed)
    w, h = W * HD, H * HD
    M = 96 * HD   # kenar
    y = np.arange(h, dtype=np.float32)[:, None]
    x = np.arange(w, dtype=np.float32)[None, :]
    base = np.array([0.87, 0.80, 0.64], np.float32)
    fib = fbm2(h, w, 3, rng, 3, aniso=(0.4, 6.0))
    blot = fbm2(h, w, 70, rng, 4)
    lum = 1.0 + 0.05 * fib + 0.08 * blot
    rgb = base[None, None, :] * lum[..., None]
    grain = ndimage.gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), 0.7 * HD) * HD
    rgb += 0.025 * grain[..., None]
    # kâğıt: üst / alt kenar yırtık, kenarda hafif is
    nz = fbm2(h, w, 22, rng, 5)
    dy = np.minimum(y, h - 1 - y)
    edge = dy - 10 * HD + nz * 12 * HD
    a = sstep(0, 2.5 * HD, edge)
    burn = 1.0 - sstep(0, 26 * HD, edge)
    sienna = np.array([0.4, 0.25, 0.13], np.float32)
    rgb = rgb * (1 - burn[..., None] * 0.6) + sienna * burn[..., None] * 0.45
    # sarılı uçlar: dikey silindir (sol / sağ 0..M): yatay kosinüs gölgelemesi, kenarda koyu mürekkep çizgi
    roll_w = M * 0.78
    for side in (0, 1):
        xs = x if side == 0 else (w - 1 - x)
        u = np.clip(xs / roll_w, 0, 1)            # 0 dış kenar .. 1 iç kenar (kâğıda bağlanır)
        inroll = (xs < roll_w).astype(np.float32)
        shade = 0.55 + 0.5 * np.abs(np.sin(u * math.pi)) ** 0.8    # ortası aydınlık, iki kenar koyu
        shade = shade * (1.0 - 0.35 * sstep(0.8, 1.0, u))   # kâğıda değdiği yerde gölge
        col = np.array([0.80, 0.70, 0.52], np.float32)[None, None, :] * shade[..., None] * (1.0 + 0.04 * fib[..., None])
        rgb = rgb * (1 - inroll[..., None]) + col * inroll[..., None]
        a = np.maximum(a, inroll * 1.0)
        # silindir kapakları (üst / alt köşe): elips, içinde spiral çizgi
        for cap in (0, 1):
            cy = (M * 0.5) if cap == 0 else (h - 1 - M * 0.5)
            cx = roll_w * 0.5 if side == 0 else (w - 1 - roll_w * 0.5)
            ex = (x - cx) / (roll_w * 0.5)
            ey = (y - cy) / (M * 0.34)
            r = np.hypot(ex, ey)
            disc = sstep(1.02, 0.96, r)
            ring = sstep(0.06, 0.0, np.abs(r - 1.0))
            spiral = sstep(0.05, 0.0, np.abs(r - (0.33 + 0.55 * ((np.arctan2(ey, ex) + math.pi) / (2 * math.pi)))))
            capcol = np.array([0.90, 0.84, 0.70], np.float32)[None, None, :] * (0.85 + 0.15 * (1 - r))[..., None]
            rgb = rgb * (1 - disc[..., None]) + capcol * disc[..., None]
            ink = np.clip(np.maximum(ring, spiral * 0.8) * disc, 0, 1)
            rgb = rgb * (1 - 0.8 * ink[..., None])
            # kapak bölgesinde kâğıt yırtığı alfa yok: kapak tam
            a = np.maximum(a, disc)
            # kapağın dışı (silindir dışı köşe boşluğu) saydam
            corner = ((xs < roll_w) & (np.abs(y - cy) < M * 0.5) & (r > 1.0)).astype(np.float32)
            a = a * (1 - corner)
        # silindir kenarı: ince mürekkep çizgi (dış kenar)
        edge_l = sstep(2.5 * HD, 0.5 * HD, xs) * inroll
        rgb = rgb * (1 - 0.7 * edge_l[..., None])
    out = np.zeros((h, w, 4), np.float32)
    out[..., :3] = np.clip(rgb, 0, 1)
    out[..., 3] = np.clip(a, 0, 1)
    Image.fromarray(np.clip(np.rint(out * 255), 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'scroll.png'))
    print('yazıldı scroll.png')


# ------------------------------------------------------------------ mürekkep dumanı
def smoke(N=512, seed=331):
    rng = np.random.default_rng(seed)
    n = N * HD
    y = (np.arange(n, dtype=np.float32)[:, None] - n / 2) / (n / 2)
    x = (np.arange(n, dtype=np.float32)[None, :] - n / 2) / (n / 2)
    r = np.hypot(x, y * 1.15)
    nz = fbm2(n, n, 60, rng, 5)
    nz2 = fbm2(n, n, 18, rng, 4)
    m = sstep(1.0, 0.25, r + nz * 0.35) * (0.55 + 0.45 * sstep(-0.6, 0.8, nz2 + nz))
    m = ndimage.gaussian_filter(m, 3.0 * HD)
    save_mask(np.clip(m, 0, 1) * 0.9, 'smoke.png')


# ------------------------------------------------------------------ fırça perdesi
def wipe(W=1024, H=512, seed=341):
    S = 2
    Q = S * HD
    b = brush(W * Q, H * Q, H * Q * 0.92, seed, dry=0.28, taper=(0.01, 0.3), wobble=0.004, rough=0.05)
    # ön kenar (sağ) daha dağınık: satır başına kuyruk uzunluğu zaten rastgele; ek olarak uzun kıl izleri
    rng = np.random.default_rng(seed + 1)
    hairs = fbm2(H * Q, W * Q, 4, rng, 2, aniso=(0.2, 60.0))
    u = np.linspace(0, 1, W * Q)[None, :]
    tail = sstep(0.62, 0.98, u) * sstep(0.2, 0.9, (hairs - hairs.mean()) / (hairs.std() + 1e-6))
    b = np.clip(np.maximum(b, tail * sstep(1.0, 0.7, u) * 0.9), 0, 1)
    save_mask(down(b, S), 'wipe.png')


# ------------------------------------------------------------------ yuvarlak mühür
def seal_round(N=256, seed=351):
    rng = np.random.default_rng(seed)
    S = 2
    Q = S * HD
    n = N * Q
    y = np.arange(n, dtype=np.float32)[:, None] - n / 2
    x = np.arange(n, dtype=np.float32)[None, :] - n / 2
    r = np.hypot(x, y)
    R = n * 0.44
    nz = fbm2(n, n, 12, rng, 5)
    m = sstep(1.5 * Q, -1.5 * Q, r - R + nz * 5 * Q)
    ring = sstep(2.2 * Q, 0.6 * Q, np.abs(r - R * 0.8) + nz * 2 * Q)
    m *= 1.0 - ring * 0.9
    sp = fbm2(n, n, 4, rng, 3)
    m *= 1.0 - sstep(0.7, 1.1, sp) * 0.55
    save_mask(down(m, S), 'seal_round.png')


# ------------------------------------------------------------------ simge boru hattı (ui_ink.icons ile aynı görünüm)
def _render_icons(names, shape_fn, outname, N=128, S=4):
    n = N * S * HD
    cols = len(names)
    NN = N * HD
    out = np.zeros((NN, NN * cols, 4), np.float32)
    for i, nm in enumerate(names):
        surf, c = sk_canvas(n, n)
        c.translate(n * 0.1, n * 0.1)
        c.scale(0.8, 0.8)
        shape_fn(nm, c, n)
        F = sk_mask(surf)
        r = int(n * 0.045)
        D = ndimage.grey_dilation(F, footprint=disk(r))
        D2 = ndimage.grey_dilation(ndimage.shift(F, (n * 0.012, n * 0.012), order=1), footprint=disk(r))
        O = np.clip(np.maximum(D, D2), 0, 1)
        Ein = ndimage.grey_erosion(F, footprint=disk(max(1, r // 3)))
        lineIn = np.clip(F - Ein, 0, 1)
        Fs = ndimage.shift(F, (-n * 0.05, -n * 0.05), order=1)
        shade = np.clip(F - Fs, 0, 1)
        lum = 1.0 - 0.32 * ndimage.gaussian_filter(shade, n * 0.01)
        rgb = np.clip(lum, 0, 1)
        ink = np.clip(O - F + lineIn * 0.85, 0, 1)
        alpha = np.clip(np.maximum(O, F), 0, 1)
        col = rgb * (1 - ink) + 0.02 * ink
        rng = np.random.default_rng(300 + i)
        col *= 1.0 - 0.06 * fbm2(n, n, 10 * S, rng, 3, aniso=(1, 4))
        a = down(alpha, S)
        cc = down(col * alpha, S) / np.maximum(a, 1e-4)
        for ch in range(3):
            out[:, i * NN:(i + 1) * NN, ch] = cc
        out[:, i * NN:(i + 1) * NN, 3] = a
    Image.fromarray(np.clip(np.rint(out * 255), 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, outname))
    print('yazıldı', outname, names)


def _font(name, size):
    tf = skia.Typeface.MakeFromFile(os.path.join(FONTS, name))
    return skia.Font(tf, size)


def _center_text(c, s, cx, cy, font, p):
    w = font.measureText(s)
    m = font.getMetrics()
    c.drawString(s, cx - w / 2, cy - (m.fAscent + m.fDescent) / 2, font, p)


PAD = ['a', 'b', 'x', 'y', 'lb', 'rb', 'lt', 'rt', 'yukari', 'asagi', 'sol', 'sag', 'ls', 'rs', 'start', 'back']


def pad_shape(name, c, n):
    P = paint()
    clr = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kClear)
    f = _font('AlegreyaSans-Bold.ttf', n * 0.5)
    fs = _font('AlegreyaSans-Bold.ttf', n * 0.34)
    if name in ('a', 'b', 'x', 'y'):
        c.drawCircle(n * 0.5, n * 0.5, n * 0.42, P)
        _center_text(c, name.upper(), n * 0.5, n * 0.5, f, clr)
    elif name in ('lb', 'rb'):
        c.drawRoundRect(skia.Rect(n * 0.06, n * 0.26, n * 0.94, n * 0.74), n * 0.16, n * 0.16, P)
        _center_text(c, name.upper(), n * 0.5, n * 0.5, fs, clr)
    elif name in ('lt', 'rt'):
        path = skia.Path()
        path.moveTo(n * 0.14, n * 0.9)
        path.lineTo(n * 0.14, n * 0.36)
        path.quadTo(n * 0.14, n * 0.1, n * 0.5, n * 0.1)
        path.quadTo(n * 0.86, n * 0.1, n * 0.86, n * 0.36)
        path.lineTo(n * 0.86, n * 0.9)
        path.close()
        c.drawPath(path, P)
        _center_text(c, name.upper(), n * 0.5, n * 0.56, fs, clr)
    elif name in ('yukari', 'asagi', 'sol', 'sag'):
        # artı biçimli yön kümesi, basılı kol dolu
        arm = n * 0.16
        c.drawRoundRect(skia.Rect(n * 0.5 - arm, n * 0.08, n * 0.5 + arm, n * 0.92), n * 0.05, n * 0.05, P)
        c.drawRoundRect(skia.Rect(n * 0.08, n * 0.5 - arm, n * 0.92, n * 0.5 + arm), n * 0.05, n * 0.05, P)
        tri = {'yukari': [(0.5, 0.16), (0.62, 0.34), (0.38, 0.34)], 'asagi': [(0.5, 0.84), (0.62, 0.66), (0.38, 0.66)],
               'sol': [(0.16, 0.5), (0.34, 0.38), (0.34, 0.62)], 'sag': [(0.84, 0.5), (0.66, 0.38), (0.66, 0.62)]}[name]
        c.drawPath(poly(tri, n), clr)
    elif name in ('ls', 'rs'):
        c.drawCircle(n * 0.5, n * 0.5, n * 0.42, P)
        c.drawCircle(n * 0.5, n * 0.5, n * 0.3, clr)
        c.drawCircle(n * 0.5, n * 0.5, n * 0.2, P)
        _center_text(c, 'L' if name == 'ls' else 'R', n * 0.5, n * 0.5, fs, clr)
    elif name == 'start':
        c.drawCircle(n * 0.5, n * 0.5, n * 0.42, P)
        for k in range(3):
            yy = n * (0.36 + 0.14 * k)
            c.drawRect(skia.Rect(n * 0.3, yy - n * 0.035, n * 0.7, yy + n * 0.035), clr)
    elif name == 'back':
        c.drawCircle(n * 0.5, n * 0.5, n * 0.42, P)
        c.drawRect(skia.Rect(n * 0.3, n * 0.38, n * 0.62, n * 0.66), clr)
        c.drawRect(skia.Rect(n * 0.38, n * 0.3, n * 0.7, n * 0.58), clr)
        c.drawRect(skia.Rect(n * 0.42, n * 0.42, n * 0.58, n * 0.54), P)


def pad():
    _render_icons(PAD, pad_shape, 'pad.png')


ICONS2 = ['ates', 'buz', 'zehir', 'kan', 'damga', 'nazar', 'nisan', 'harita', 'ok', 'yildiz', 'hiz', 'nakis', 'muhur']


def icon2_shape(name, c, n):
    P = paint()
    clr = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kClear)
    clr_s = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kClear, Style=skia.Paint.kStroke_Style,
                       StrokeWidth=n * 0.05, StrokeCap=skia.Paint.kRound_Cap)
    if name == 'ates':
        p = skia.Path()
        p.moveTo(n * 0.5, n * 0.04)
        p.cubicTo(n * 0.58, n * 0.3, n * 0.9, n * 0.4, n * 0.84, n * 0.68)
        p.cubicTo(n * 0.8, n * 0.88, n * 0.62, n * 0.96, n * 0.5, n * 0.96)
        p.cubicTo(n * 0.3, n * 0.96, n * 0.14, n * 0.82, n * 0.16, n * 0.62)
        p.cubicTo(n * 0.18, n * 0.46, n * 0.32, n * 0.4, n * 0.3, n * 0.24)
        p.cubicTo(n * 0.42, n * 0.3, n * 0.46, n * 0.2, n * 0.5, n * 0.04)
        p.close()
        c.drawPath(p, P)
        q = skia.Path()
        q.moveTo(n * 0.5, n * 0.5)
        q.cubicTo(n * 0.66, n * 0.62, n * 0.66, n * 0.84, n * 0.5, n * 0.86)
        q.cubicTo(n * 0.36, n * 0.84, n * 0.34, n * 0.66, n * 0.5, n * 0.5)
        q.close()
        c.drawPath(q, clr)
    elif name == 'buz':
        s = skia.Paint(AntiAlias=True, Color=skia.ColorWHITE, Style=skia.Paint.kStroke_Style, StrokeWidth=n * 0.09, StrokeCap=skia.Paint.kRound_Cap)
        for k in range(3):
            a = k * math.pi / 3
            dx, dy = math.cos(a) * n * 0.42, math.sin(a) * n * 0.42
            c.drawLine(n * 0.5 - dx, n * 0.5 - dy, n * 0.5 + dx, n * 0.5 + dy, s)
            for sg in (-1, 1):
                for t in (0.55, 0.85):
                    px, py = n * 0.5 + sg * dx * t, n * 0.5 + sg * dy * t
                    for b in (-1, 1):
                        ba = a + b * math.pi / 3
                        c.drawLine(px, py, px + sg * math.cos(ba) * n * 0.11, py + sg * math.sin(ba) * n * 0.11, s)
        c.drawCircle(n * 0.5, n * 0.5, n * 0.1, P)
    elif name in ('zehir', 'kan'):
        p = skia.Path()
        p.moveTo(n * 0.5, n * 0.04)
        p.cubicTo(n * 0.6, n * 0.3, n * 0.88, n * 0.46, n * 0.86, n * 0.66)
        p.cubicTo(n * 0.84, n * 0.86, n * 0.68, n * 0.96, n * 0.5, n * 0.96)
        p.cubicTo(n * 0.32, n * 0.96, n * 0.16, n * 0.86, n * 0.14, n * 0.66)
        p.cubicTo(n * 0.12, n * 0.46, n * 0.4, n * 0.3, n * 0.5, n * 0.04)
        p.close()
        c.drawPath(p, P)
        if name == 'zehir':
            c.drawCircle(n * 0.4, n * 0.6, n * 0.06, clr)
            c.drawCircle(n * 0.6, n * 0.6, n * 0.06, clr)
            c.drawRect(skia.Rect(n * 0.42, n * 0.72, n * 0.58, n * 0.78), clr)
        else:
            c.drawOval(skia.Rect(n * 0.3, n * 0.5, n * 0.42, n * 0.72), clr)
    elif name == 'damga':
        c.drawCircle(n * 0.5, n * 0.5, n * 0.42, P)
        c.drawCircle(n * 0.5, n * 0.5, n * 0.3, clr)
        c.drawCircle(n * 0.5, n * 0.5, n * 0.12, P)
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            c.drawLine(n * 0.5 + math.cos(a) * n * 0.16, n * 0.5 + math.sin(a) * n * 0.16, n * 0.5 + math.cos(a) * n * 0.28, n * 0.5 + math.sin(a) * n * 0.28, paint(n * 0.06))
    elif name == 'nazar':
        c.drawOval(skia.Rect(n * 0.04, n * 0.28, n * 0.96, n * 0.72), P)
        c.drawCircle(n * 0.5, n * 0.5, n * 0.16, clr)
        c.drawCircle(n * 0.5, n * 0.5, n * 0.09, P)
        c.drawCircle(n * 0.46, n * 0.46, n * 0.03, clr)
    elif name == 'nisan':
        c.drawPath(poly([(0.5, 0.04), (0.9, 0.5), (0.5, 0.96), (0.1, 0.5)], n), P)
        c.drawPath(poly([(0.5, 0.26), (0.72, 0.5), (0.5, 0.74), (0.28, 0.5)], n), clr)
        c.drawPath(poly([(0.5, 0.4), (0.6, 0.5), (0.5, 0.6), (0.4, 0.5)], n), P)
    elif name == 'harita':
        c.drawPath(poly([(0.06, 0.2), (0.36, 0.1), (0.64, 0.2), (0.94, 0.1), (0.94, 0.8), (0.64, 0.9), (0.36, 0.8), (0.06, 0.9)], n), P)
        c.drawLine(n * 0.36, n * 0.1, n * 0.36, n * 0.8, clr_s)
        c.drawLine(n * 0.64, n * 0.2, n * 0.64, n * 0.9, clr_s)
        c.drawCircle(n * 0.5, n * 0.5, n * 0.07, clr)
    elif name == 'ok':
        s = skia.Paint(AntiAlias=True, Color=skia.ColorWHITE, Style=skia.Paint.kStroke_Style, StrokeWidth=n * 0.08, StrokeCap=skia.Paint.kRound_Cap)
        c.drawLine(n * 0.12, n * 0.88, n * 0.84, n * 0.16, s)
        c.drawPath(poly([(0.92, 0.08), (0.62, 0.16), (0.84, 0.38)], n), P)
        c.drawLine(n * 0.12, n * 0.88, n * 0.3, n * 0.86, s)
        c.drawLine(n * 0.12, n * 0.88, n * 0.14, n * 0.7, s)
    elif name == 'yildiz':
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            r = 0.46 if k % 2 == 0 else 0.2
            pts.append((0.5 + math.cos(a) * r, 0.5 + math.sin(a) * r))
        c.drawPath(poly(pts, n), P)
    elif name == 'hiz':
        for k in range(3):
            ox = 0.08 + k * 0.26
            c.drawPath(poly([(ox, 0.2), (ox + 0.3, 0.5), (ox, 0.8), (ox + 0.1, 0.5)], n), P)
    elif name == 'nakis':
        # nakış: iğne ve iplik ilmeği
        s = skia.Paint(AntiAlias=True, Color=skia.ColorWHITE, Style=skia.Paint.kStroke_Style, StrokeWidth=n * 0.07, StrokeCap=skia.Paint.kRound_Cap)
        c.drawLine(n * 0.2, n * 0.8, n * 0.8, n * 0.2, s)
        c.drawOval(skia.Rect(n * 0.7, n * 0.1, n * 0.9, n * 0.3), s)
        path = skia.Path()
        path.moveTo(n * 0.2, n * 0.8)
        path.cubicTo(n * 0.0, n * 0.6, n * 0.5, n * 0.3, n * 0.3, n * 0.92)
        c.drawPath(path, s)
    elif name == 'muhur':
        c.drawRoundRect(skia.Rect(n * 0.1, n * 0.1, n * 0.9, n * 0.9), n * 0.08, n * 0.08, P)
        c.drawRoundRect(skia.Rect(n * 0.24, n * 0.24, n * 0.76, n * 0.76), n * 0.04, n * 0.04, clr)
        c.drawPath(poly([(0.5, 0.34), (0.64, 0.5), (0.5, 0.66), (0.36, 0.5)], n), P)


def icons2():
    _render_icons(ICONS2, icon2_shape, 'icons2.png')


# ------------------------------------------------------------------ kaligrafi logo
def logo(W=2048, H=768, seed=401):
    if HD > 1:
        print('logo: HD paketine girmez (temel 2048 px yeter)')
        return
    S = 2
    n_w, n_h = W * S, H * S
    surf, c = sk_canvas(n_w, n_h)
    f = _font('KaushanScript-Regular.ttf', n_h * 0.5)
    s = "Kut'un Yolu"
    w = f.measureText(s)
    m = f.getMetrics()
    x0 = (n_w - w) / 2
    y0 = n_h * 0.5 - (m.fAscent + m.fDescent) / 2
    c.drawString(s, x0, y0, f, paint())
    F = sk_mask(surf)
    rng = np.random.default_rng(seed)
    # kenar pürüzü: işaretli uzaklık + gürültü (kalın yerlerde biraz ıslak taşma)
    inside = ndimage.distance_transform_edt(F > 0.5)
    outside = ndimage.distance_transform_edt(F <= 0.5)
    sd = inside - outside
    nz = fbm2(n_h, n_w, 7, rng, 4)
    nz2 = fbm2(n_h, n_w, 40, rng, 3)
    M = sstep(-1.2, 1.2, sd + nz * 3.0 * S + nz2 * 1.5 * S)
    # kuru fırça: darbe yönünde (hafif eğik) kıl boşlukları, kalın gövdede daha az
    streak = fbm2(n_h, n_w, 5, rng, 3, aniso=(0.3, 28.0))
    streak = (streak - streak.mean()) / (streak.std() + 1e-6)
    # gövde dolu kalır; kıl boşlukları yalnızca ince uçlarda ve kenara yakın şeritte (kuru fırça kuyruğu)
    thick = np.clip(inside / (n_h * 0.022), 0, 1)
    gap = sstep(1.35, 1.9, streak) * (1.0 - thick * 0.85)
    M = M * (1.0 - gap * 0.9)
    # ince kıl uzantıları harf uçlarında: dış tarafa doğru uzun gürültü
    hairs = sstep(1.3, 2.0, streak) * sstep(4.0 * S, 0.0, outside) * (F < 0.5)
    M = np.clip(np.maximum(M, hairs * 0.8), 0, 1)
    # mürekkep havuzlanması: iç kenarlar daha koyu (lum), orta hafif açık
    lum = 1.0 - 0.18 * sstep(3.0 * S, 0.0, inside) * F - 0.08 * sstep(0.3, 0.9, nz2)
    # sıçrantılar: harf çevresine küçük damlalar
    y = np.arange(n_h, dtype=np.float32)[:, None]
    x = np.arange(n_w, dtype=np.float32)[None, :]
    for i in range(70):
        px = x0 + rng.random() * w
        py = n_h * (0.2 + rng.random() * 0.6)
        if F[int(np.clip(py, 0, n_h - 1)), int(np.clip(px, 0, n_w - 1))] > 0.5:
            continue
        rr = S * (1.2 + rng.random() ** 2.5 * 7.0)
        M = np.maximum(M, sstep(1.5, -1.5, np.hypot(x - px, y - py) - rr))
    # hafif taşma halesi (ıslak kâğıt)
    halo = ndimage.gaussian_filter(M, 6.0 * S) * 0.18
    A = np.clip(np.maximum(M, halo), 0, 1)
    out = np.zeros((n_h, n_w, 4), np.float32)
    rgb = np.clip(lum, 0, 1)
    for ch in range(3):
        out[..., ch] = rgb
    out[..., 3] = A
    o = down(out, S)
    Image.fromarray(np.clip(np.rint(o * 255), 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'logo.png'))
    print('yazıldı logo.png', o.shape)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:]
    for fn in [kilim, orkhon, scroll, smoke, wipe, seal_round, pad, icons2, logo]:
        if not only or fn.__name__ in only:
            fn()
    write_imports()
