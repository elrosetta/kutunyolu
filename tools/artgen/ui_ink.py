"""ui_ink: Stil v2 mürekkep arayüzü dokuları (scripts/ui/InkUI.gd) -> assets/ui/ink/*.png

Hepsi beyaz maske (RGB beyaz/gri, alfa = mürekkep) ya da önceden boyanmış doku; oyunda renk modulate ile verilir.
Doku yoğunluğu: 3 doku pikseli = 1 arayüz birimi (menüler 960x540 x1,5 => 1080p'de 1 doku pikseli = 1 ekran pikseli).

  frame_ink.png   panel çerçevesi: köşelerde kesişip taşan dört kalın fırça darbesi (9 dilim, kenar 48 px)
  frame_line.png  ince kuru fırça iç çizgi (renkli vurgu; 9 dilim, kenar 48 px)
  fill.png        mürekkep yıkaması dolgu: kenarı pürüzlü, kenarda koyulaşan, fırça izli (9 dilim, kenar 32 px)
  swash.png       küçük rozet / satır zemini: yatay fırça sürmesi (uçları dağınık)
  stroke.png      çubuk: yatay kuru fırça darbesi (can, Kut, boss)
  seal.png        tuş mühürü: kenarı yenmiş kare damga (iç çerçeveli)
  enso.png        halka göstergesi zemini: fırça daire (ensō)
  splat.png       mürekkep sıçrantısı (kombo, başlık, kritik)
  band.png        yatay yıkama şeridi (bölüm başlığı, ekran başlıkları)
  horn.png        koçboynuzu süsü (fırçayla, simetrik)
  tamga.png       4 tamga (Kayı, ok-yay, dağ, güneş) şeridi
  paper.png       kenarı yanık parşömen (hikâye, Ozan, Ad töreni; 9 dilim, kenar 72 px)
  vignette.png    menü kenar karartması (fırça kenarlı)
  icons.png       arayüz simgeleri 128 px hücre: beyaz dolgu + siyah mürekkep kontur (modulate ile renklenir)

Kullanım: cd tools/artgen && python ui_ink.py
"""
import math
import os

import numpy as np
import skia
from PIL import Image
from scipy import ndimage

from hdpack import HD   # HD doku paketi (KY_HD=2): aynı doku HD kat çözünürlükte (iç ızgaralar HD kat, gürültü ızgaraları aynı)

OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'ui', 'ink')
ICONS = ['can', 'sise', 'altin', 'kut', 'kurt', 'kartal', 'ayi', 'kafatasi', 'zaman', 'kilic', 'tilsim', 'davul', 'ruh', 'kalkan']


# ------------------------------------------------------------------ gürültü
def noise1(n, scale, rng, octaves=4):
    out = np.zeros(n, np.float32)
    amp = 1.0
    tot = 0.0
    for o in range(octaves):
        k = max(2, int(n / scale * (2 ** o)) + 2)
        g = rng.standard_normal(k).astype(np.float32)
        xs = np.linspace(0, k - 1.001, n)
        i = xs.astype(int)
        f = xs - i
        f = f * f * (3 - 2 * f)
        out += amp * (g[i] * (1 - f) + g[i + 1] * f)
        tot += amp
        amp *= 0.5
    return out / tot


def fbm2(h, w, scale, rng, octaves=4, aniso=(1.0, 1.0)):
    """scale: temel piksel. HD paketinde h, w HD kat verilir; ölçek de HD kat -> aynı ızgara, aynı gürültü (2 kat örnek)."""
    scale = scale * HD
    out = np.zeros((h, w), np.float32)
    amp = 1.0
    tot = 0.0
    for o in range(octaves):
        gh = max(2, int(h / (scale * aniso[0]) * 2 ** o) + 2)
        gw = max(2, int(w / (scale * aniso[1]) * 2 ** o) + 2)
        g = rng.standard_normal((gh, gw)).astype(np.float32)
        z = ndimage.zoom(g, (h / gh, w / gw), order=3, mode='nearest')[:h, :w]
        if z.shape != (h, w):
            z = np.pad(z, ((0, h - z.shape[0]), (0, w - z.shape[1])), mode='edge')
        out += amp * z
        tot += amp
        amp *= 0.5
    return out / tot


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ fırça darbesi
def brush(L, H, width, seed, dry=0.35, taper=(0.06, 0.12), wobble=0.04, rough=0.08, ends=True, press=None):
    """Yatay fırça darbesi maskesi (H x L, float 0..1). width: darbenin kalınlığı (px).
    dry: kuru fırça boşluk oranı (kuyruğa doğru artar), rough: kenar pürüzü (genişliğe oran)."""
    rng = np.random.default_rng(seed)
    x = np.arange(L, dtype=np.float32)
    u = x / (L - 1)
    yc = H / 2 + noise1(L, L / 3, rng, 3) * width * wobble * 4
    prof = np.ones(L, np.float32)
    if ends:
        prof *= 0.35 + 0.65 * sstep(0, taper[0], u)
        prof *= 0.25 + 0.75 * sstep(1.0, 1.0 - taper[1], u)
    if press is not None:
        prof *= press(u)
    prof *= 1.0 + 0.08 * noise1(L, L / 4, rng, 2)
    hw = width / 2 * prof
    top = yc - hw + noise1(L, 18 * HD, rng, 4) * width * rough
    bot = yc + hw + noise1(L, 18 * HD, rng, 4) * width * rough
    y = np.arange(H, dtype=np.float32)[:, None]
    m = np.clip(np.minimum(y - top[None, :], bot[None, :] - y) + 0.5, 0, 1)
    # kıl izleri: x yönünde çok uzun gürültü (her satır bir kıl)
    rel = (y - top[None, :]) / np.maximum(1.0, (bot - top)[None, :])
    streak = fbm2(H, L, 6, rng, 3, aniso=(0.25, 30.0))
    streak = (streak - streak.mean()) / (streak.std() + 1e-6)
    th = 2.0 - dry * 2.6 * (0.3 + 0.7 * u[None, :] ** 1.5)
    edge = np.clip(1.0 - 4.0 * rel * (1 - rel), 0, 1) ** 2  # kenara yakın kıllar daha kuru
    gap = sstep(th - 0.2, th + 0.2, streak + edge * dry * 2.2)
    m = m * (1.0 - gap * 0.92)
    if ends:
        # dağınık kuyruk: satır başına rastgele kıl boyu
        cut = 1.0 - _rows(rng, H) ** 2 * taper[1] * 1.2
        m *= sstep(cut + 0.02, cut - 0.01, u[None, :])
        cut0 = _rows(rng, H) ** 3 * taper[0] * 0.6
        m *= sstep(cut0 - 0.01, cut0 + 0.02, u[None, :])
    return np.clip(m, 0, 1)


def _rows(rng, H):
    """Satır (kıl) başına rastgele (H, 1): HD paketinde temel satır sayısı kadar çekilip HD kat tekrarlanır (aynı kıllar)."""
    if HD == 1:
        return rng.random((H, 1)).astype(np.float32)
    r = rng.random((-(-H // HD), 1)).astype(np.float32)
    return np.repeat(r, HD, axis=0)[:H]


def _ax(n):
    """np.arange(n) (float32) temel piksel ekseni; HD paketinde n*HD örnek (HD piksel merkezleri, birim temel piksel)."""
    if HD == 1:
        return np.arange(n, dtype=np.float32)
    return (np.arange(n * HD, dtype=np.float32) + 0.5) / HD - 0.5


def paste_max(dst, src, x, y):
    h, w = src.shape
    H, W = dst.shape
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    dst[y0:y1, x0:x1] = np.maximum(dst[y0:y1, x0:x1], src[y0 - y:y1 - y, x0 - x:x1 - x])


def down(a, k):
    """k kat süper örneklemeden küçült (alan ortalaması)"""
    if k == 1:
        return a
    h, w = a.shape[:2]
    a = a[:h // k * k, :w // k * k]
    return a.reshape(h // k, k, w // k, k, *a.shape[2:]).mean(axis=(1, 3))


def save_mask(m, name, rgb=None):
    h, w = m.shape
    out = np.zeros((h, w, 4), np.float32)
    if rgb is None:
        out[..., :3] = 1.0
    else:
        out[..., :3] = rgb
    out[..., 3] = np.clip(m, 0, 1)
    # alfası sıfır piksellerin rengi komşudan: doğrusal süzgeçte kenar halesi olmasın
    a = np.clip(np.rint(out * 255), 0, 255).astype(np.uint8)
    Image.fromarray(a, 'RGBA').save(os.path.join(OUT, name))
    print('yazıldı', name, a.shape)


# ------------------------------------------------------------------ çerçeve
def frame(W=1024, H=512, seed=3):
    S = 2
    Q = S * HD       # HD paketi: iç ızgara pikseli (temel çıktı pikseli başına)
    w, h = W * Q, H * Q
    ink = np.zeros((h, w), np.float32)
    line = np.zeros((h, w), np.float32)
    th = 15 * Q          # kalın darbe
    off = 20 * Q         # kenardan içeri
    # yatay: üst / alt (köşelerden taşar)
    for i, (yy, sd) in enumerate([(off, seed), (h - off, seed + 1)]):
        L = w - 6 * Q
        b = brush(L, th * 3, th * (1.0 if i == 0 else 0.9), sd, dry=0.42, taper=(0.03, 0.05), wobble=0.006, rough=0.07)
        paste_max(ink, b, 3 * Q, int(yy - th * 1.5))
    for i, (xx, sd) in enumerate([(off, seed + 2), (w - off, seed + 3)]):
        L = h - 6 * Q
        b = brush(L, th * 3, th * (0.95 if i == 0 else 0.85), sd, dry=0.42, taper=(0.06, 0.1), wobble=0.006, rough=0.07).T
        paste_max(ink, b, int(xx - th * 1.5), 3 * Q)
    # ince iç çizgi (renkli)
    tl = 3.6 * Q
    ins = 32 * Q
    for i, (yy, sd) in enumerate([(ins, seed + 7), (h - ins, seed + 8)]):
        b = brush(w - 2 * ins + 8 * Q, int(tl * 5), tl, sd, dry=0.5, taper=(0.04, 0.08), wobble=0.004, rough=0.12)
        paste_max(line, b, ins - 4 * Q, int(yy - tl * 2.5))
    for i, (xx, sd) in enumerate([(ins, seed + 9), (w - ins, seed + 10)]):
        b = brush(h - 2 * ins + 8 * Q, int(tl * 5), tl, sd, dry=0.5, taper=(0.06, 0.1), wobble=0.004, rough=0.12).T
        paste_max(line, b, int(xx - tl * 2.5), ins - 4 * Q)
    save_mask(down(ink, S), 'frame_ink.png')
    save_mask(down(line, S), 'frame_line.png')


def fill(W=512, H=256, seed=5):
    rng = np.random.default_rng(seed)
    S = 2
    Q = S * HD       # HD paketi: iç ızgara pikseli (temel çıktı pikseli başına)
    w, h = W * Q, H * Q
    y = np.arange(h, dtype=np.float32)[:, None]
    x = np.arange(w, dtype=np.float32)[None, :]
    mrg = 22 * Q
    d = np.minimum(np.minimum(x, w - 1 - x), np.minimum(y, h - 1 - y))
    nz = fbm2(h, w, 30, rng, 5)
    edge = d - mrg * 0.55 + nz * 9 * Q
    a = sstep(0, 4 * Q, edge)
    # kenarda havuzlanan mürekkep (daha koyu), içte fırça izleri
    pool = 1.0 - sstep(0, 14 * Q, edge)
    streak = fbm2(h, w, 10, rng, 3, aniso=(0.3, 12.0))
    lum = 0.76 + 0.06 * streak + 0.12 * fbm2(h, w, 50, rng, 4) - 0.3 * pool
    grain = rng.standard_normal((h, w)).astype(np.float32)
    lum += 0.05 * HD * ndimage.gaussian_filter(grain, 0.8 * HD)   # tane: aynı fiziksel boy ve genlik
    lum = down(np.clip(lum, 0.3, 1.0), S)
    out = down(a, S)
    save_mask(out, 'fill.png', rgb=lum[..., None])


def swash(W=512, H=96, seed=21):
    S = 2
    Q = S * HD       # HD paketi: iç ızgara pikseli (temel çıktı pikseli başına)
    b = brush(W * Q, H * Q, H * Q * 0.62, seed, dry=0.3, taper=(0.05, 0.16), wobble=0.01, rough=0.07)
    save_mask(down(b, S), 'swash.png')


def stroke(W=1024, H=96, seed=31):
    S = 2
    Q = S * HD       # HD paketi: iç ızgara pikseli (temel çıktı pikseli başına)
    b = brush(W * Q, H * Q, H * Q * 0.7, seed, dry=0.38, taper=(0.02, 0.05), wobble=0.006, rough=0.06,
              press=lambda u: 0.9 + 0.1 * np.sin(u * 3.0 + 0.4))
    save_mask(down(b, S), 'stroke.png')


def seal(N=160, seed=41):
    rng = np.random.default_rng(seed)
    S = 2
    Q = S * HD       # HD paketi: iç ızgara pikseli (temel çıktı pikseli başına)
    n = N * Q
    y = np.arange(n, dtype=np.float32)[:, None]
    x = np.arange(n, dtype=np.float32)[None, :]
    c = n / 2
    r = n * 0.42
    # yuvarlatılmış kare, kenarı yenmiş
    q = np.maximum(np.abs(x - c), np.abs(y - c))
    rr = np.hypot(np.maximum(np.abs(x - c) - r * 0.8, 0), np.maximum(np.abs(y - c) - r * 0.8, 0))
    d = r * 0.2 - rr
    nz = fbm2(n, n, 14, rng, 5)
    m = sstep(-1.5, 1.5, d + nz * 7 * Q)
    # iç çerçeve (boşluk)
    inner = np.hypot(np.maximum(np.abs(x - c) - r * 0.62, 0), np.maximum(np.abs(y - c) - r * 0.62, 0))
    ring = sstep(2.0 * Q, 0.8 * Q, np.abs(inner - r * 0.1 - 2 * Q) + nz * 2 * Q)
    m *= 1.0 - ring * 0.9
    # damga dokusu: mürekkebin tutmadığı benekler
    sp = fbm2(n, n, 4, rng, 3)
    m *= 1.0 - sstep(0.75, 1.1, sp) * 0.6
    save_mask(down(m, S), 'seal.png')


def enso(N=256, seed=51):
    rng = np.random.default_rng(seed)
    S = 2
    Q = S * HD       # HD paketi: iç ızgara pikseli (temel çıktı pikseli başına)
    L = int(math.pi * 2 * N * 0.38 * Q)
    b = brush(L, 60 * Q, 34 * Q, seed, dry=0.4, taper=(0.03, 0.2), wobble=0.01, rough=0.05)
    # yatay darbeyi daireye sar
    n = N * Q
    y = np.arange(n, dtype=np.float32)[:, None] - n / 2
    x = np.arange(n, dtype=np.float32)[None, :] - n / 2
    ang = (np.arctan2(y, x) + math.pi * 0.5) % (2 * math.pi)  # tepeden başla
    rad = np.hypot(x, y)
    R = N * 0.38 * Q
    u = ang / (2 * math.pi) * (L - 1)
    v = (rad - R) + 30 * Q
    m = ndimage.map_coordinates(b, [v.ravel(), u.ravel()], order=1, mode='constant').reshape(n, n)
    # kuyruğun başı örtsün: ikinci küçük geçiş
    save_mask(down(m, S), 'enso.png')


def splat(N=512, seed=61):
    rng = np.random.default_rng(seed)
    S = 2
    Q = S * HD       # HD paketi: iç ızgara pikseli (temel çıktı pikseli başına)
    n = N * Q
    y = np.arange(n, dtype=np.float32)[:, None] - n / 2
    x = np.arange(n, dtype=np.float32)[None, :] - n / 2
    ang = np.arctan2(y, x)
    rad = np.hypot(x, y)
    # çevresel diken profili
    k = 720
    sp = np.abs(noise1(k, 6, rng, 4))
    sp = sp / sp.max()
    spikes = sp[((ang + math.pi) / (2 * math.pi) * (k - 1)).astype(int)]
    R = n * 0.26 * (0.8 + 0.5 * spikes ** 2.2) + fbm2(n, n, 40, rng, 4) * n * 0.035
    m = sstep(1.5, -1.5, rad - R)
    # damlalar
    for i in range(46):
        a = rng.random() * 2 * math.pi
        d = n * (0.27 + rng.random() ** 1.6 * 0.2)
        rr = n * (0.004 + rng.random() ** 2 * 0.022)
        cx, cy = math.cos(a) * d, math.sin(a) * d
        m = np.maximum(m, sstep(1.5, -1.5, np.hypot(x - cx, y - cy) - rr))
    # iç doku
    tex = fbm2(n, n, 20, rng, 4)
    m *= 1.0 - sstep(0.5, 0.9, tex) * 0.25
    save_mask(down(m, S), 'splat.png')


def band(W=1024, H=192, seed=71):
    rng = np.random.default_rng(seed)
    S = 2
    Q = S * HD       # HD paketi: iç ızgara pikseli (temel çıktı pikseli başına)
    w, h = W * Q, H * Q
    b = brush(w, h, h * 0.55, seed, dry=0.22, taper=(0.12, 0.14), wobble=0.01, rough=0.09)
    b = ndimage.gaussian_filter(b, 2.0 * Q)
    b2 = brush(w, h, h * 0.18, seed + 1, dry=0.5, taper=(0.2, 0.25), wobble=0.02, rough=0.1)
    m = np.clip(b * 0.85 + b2 * 0.3, 0, 1)
    u = np.linspace(0, 1, w)[None, :]
    m *= sstep(0.0, 0.18, u) * sstep(1.0, 0.82, u)
    save_mask(down(m, S), 'band.png')


def vignette(W=512, H=288, seed=81):
    rng = np.random.default_rng(seed)
    W, H = W * HD, H * HD
    y = np.arange(H, dtype=np.float32)[:, None] / H
    x = np.arange(W, dtype=np.float32)[None, :] / W
    d = np.minimum(np.minimum(x, 1 - x) * W / H, np.minimum(y, 1 - y))
    nz = fbm2(H, W, 18, rng, 5)
    m = 1.0 - sstep(0.02, 0.2, d + nz * 0.05)
    m = 0.15 + 0.85 * m
    save_mask(m, 'vignette.png')


# ------------------------------------------------------------------ skia ile vektör şekiller
def sk_canvas(w, h):
    surf = skia.Surface(w, h)
    c = surf.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    return surf, c


def sk_mask(surf):
    a = surf.makeImageSnapshot().toarray()  # BGRA/RGBA u8
    return a[..., 3].astype(np.float32) / 255.0


def paint(stroke_w=0.0, aa=True):
    p = skia.Paint(AntiAlias=aa, Color=skia.ColorWHITE)
    if stroke_w > 0:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke_w)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def tapered(c, pts, w0, w1, n=48):
    """Uçları incelen fırça çizgisi: pts Catmull-Rom eğrisi boyunca daireler (değişken kalınlık)"""
    pts = np.array(pts, np.float32)
    seg = []
    for i in range(len(pts) - 1):
        p0 = pts[max(0, i - 1)]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[min(len(pts) - 1, i + 2)]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            q = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
            seg.append(q)
    seg.append(pts[-1])
    seg = np.array(seg)
    # yay uzunluğuna göre sık örnekle (fırça boncuklanmasın)
    dl = np.r_[0, np.cumsum(np.hypot(*np.diff(seg, axis=0).T))]
    tt = np.linspace(0, dl[-1], max(2, int(dl[-1] / max(1.0, min(w0, w1) * 0.12))))
    seg = np.stack([np.interp(tt, dl, seg[:, 0]), np.interp(tt, dl, seg[:, 1])], 1)
    m = len(seg)
    p = paint()
    for i, q in enumerate(seg):
        u = i / (m - 1)
        w = w0 + (w1 - w0) * u
        w *= 0.35 + 0.65 * min(1.0, u * 6) if w0 >= w1 else 1.0
        c.drawCircle(float(q[0]), float(q[1]), max(0.5, w / 2), p)


def horn(N=256):
    """Koçboynuzu (kilim motifi): ortada gövde, iki yana dışa-aşağı kıvrılıp içe sarılan boynuz."""
    S = 4
    n = N * S * HD
    surf, c = sk_canvas(n, n)
    cx = n / 2
    for f in (1, -1):
        C = (cx + f * n * 0.2, n * 0.4)
        pts = [(cx, n * 0.94), (cx, n * 0.62)]
        for i in range(40):
            t = i / 39
            a = math.pi + t * math.pi * 1.7
            r = n * (0.2 - 0.135 * t)
            pts.append((C[0] + f * math.cos(a) * r * (1 if f > 0 else 1), C[1] + math.sin(a) * r))
        # f = -1: x aynalanır (cos işareti)
        if f < 0:
            pts = [(2 * cx - x, y) for (x, y) in [(cx, n * 0.94), (cx, n * 0.62)]] +                   [(2 * cx - (cx + n * 0.2 + math.cos(math.pi + i / 39 * math.pi * 1.7) * n * (0.2 - 0.135 * i / 39)),
                    n * 0.4 + math.sin(math.pi + i / 39 * math.pi * 1.7) * n * (0.2 - 0.135 * i / 39)) for i in range(40)]
        tapered(c, pts, n * 0.07, n * 0.022, n=24)
    c.drawCircle(cx, n * 0.97, n * 0.035, paint())
    m = sk_mask(surf)
    rng = np.random.default_rng(91)
    m *= 1.0 - sstep(0.55, 0.9, fbm2(n, n, 6 * S, rng, 3, aniso=(1, 3))) * 0.45
    save_mask(down(m, S), 'horn.png')


def tamga(N=128):
    S = 4
    n = N * S * HD
    W = n * 4
    surf, c = sk_canvas(W, n)
    lw = n * 0.085
    p = paint(lw)

    def L(x0, y0, x1, y1, ox):
        c.drawLine(ox + x0 * n, y0 * n, ox + x1 * n, y1 * n, p)
    # 0: Kayı tamgası (ok ve iki yay)
    o = 0
    L(0.5, 0.12, 0.5, 0.9, o)
    path = skia.Path()
    path.moveTo(o + 0.18 * n, 0.2 * n)
    path.quadTo(o + 0.5 * n, 0.72 * n, o + 0.82 * n, 0.2 * n)
    c.drawPath(path, p)
    path = skia.Path()
    path.moveTo(o + 0.22 * n, 0.9 * n)
    path.quadTo(o + 0.5 * n, 0.55 * n, o + 0.78 * n, 0.9 * n)
    c.drawPath(path, p)
    # 1: ok-yay
    o = n
    path = skia.Path()
    path.moveTo(o + 0.3 * n, 0.12 * n)
    path.quadTo(o + 0.95 * n, 0.5 * n, o + 0.3 * n, 0.88 * n)
    c.drawPath(path, p)
    L(0.3, 0.12, 0.3, 0.88, o)
    L(0.12, 0.5, 0.86, 0.5, o)
    L(0.72, 0.4, 0.86, 0.5, o)
    L(0.72, 0.6, 0.86, 0.5, o)
    # 2: dağ / ağaç (üç dallı)
    o = 2 * n
    L(0.5, 0.1, 0.5, 0.9, o)
    L(0.5, 0.45, 0.18, 0.18, o)
    L(0.5, 0.45, 0.82, 0.18, o)
    L(0.2, 0.9, 0.8, 0.9, o)
    # 3: güneş (daire ve ışın)
    o = 3 * n
    c.drawCircle(o + 0.5 * n, 0.5 * n, 0.2 * n, p)
    for k in range(8):
        a = k * math.pi / 4
        L(0.5 + math.cos(a) * 0.3, 0.5 + math.sin(a) * 0.3, 0.5 + math.cos(a) * 0.42, 0.5 + math.sin(a) * 0.42, o)
    m = sk_mask(surf)
    rng = np.random.default_rng(93)
    m *= 1.0 - sstep(0.4, 0.8, fbm2(n, W, 5 * S, rng, 3)) * 0.55
    save_mask(down(m, S), 'tamga.png')


def paper(W=1024, H=768, seed=101):
    rng = np.random.default_rng(seed)
    y = _ax(H)[:, None]
    x = _ax(W)[None, :]
    d = np.minimum(np.minimum(x, W - 1 - x), np.minimum(y, H - 1 - y))
    W, H = W * HD, H * HD    # HD paketi: dizi boyu; uzaklık ve eşikler temel piksel
    nz = fbm2(H, W, 26, rng, 6)
    edge = d - 26 + nz * 22
    a = sstep(0, 3, edge)
    burn = 1.0 - sstep(0, 46, edge)
    fib = fbm2(H, W, 3, rng, 3, aniso=(0.4, 6.0))
    blot = fbm2(H, W, 90, rng, 4)
    base = np.array([0.86, 0.79, 0.65], np.float32)
    lum = 1.0 + 0.05 * fib + 0.07 * blot
    rgb = base[None, None, :] * lum[..., None]
    # yanık / is: kenarda kahve-siyah
    sienna = np.array([0.36, 0.22, 0.12], np.float32)
    rgb = rgb * (1 - burn[..., None] * 0.75) + sienna * burn[..., None] * 0.55
    rgb = rgb * (1 - (burn ** 3)[..., None] * 0.7)
    grain = ndimage.gaussian_filter(rng.standard_normal((H, W)).astype(np.float32), 0.7 * HD) * HD
    rgb += 0.025 * grain[..., None]
    out = np.zeros((H, W, 4), np.float32)
    out[..., :3] = np.clip(rgb, 0, 1)
    out[..., 3] = a
    Image.fromarray(np.clip(np.rint(out * 255), 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'paper.png'))
    print('yazıldı paper.png')


# ------------------------------------------------------------------ simgeler
def heart_path(n):
    p = skia.Path()
    pts = []
    for i in range(120):
        t = i / 120 * 2 * math.pi
        xx = 16 * math.sin(t) ** 3
        yy = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((n / 2 + xx * n / 40, n * 0.47 - yy * n / 40))
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    return p


def poly(pts, n):
    p = skia.Path()
    p.moveTo(pts[0][0] * n, pts[0][1] * n)
    for q in pts[1:]:
        p.lineTo(q[0] * n, q[1] * n)
    p.close()
    return p


def icon_shape(name, c, n):
    """Beyaz dolgu şekli (delikler kClear ile)"""
    P = paint()
    clr = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kClear)
    clr_s = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kClear, Style=skia.Paint.kStroke_Style,
                       StrokeWidth=n * 0.05, StrokeCap=skia.Paint.kRound_Cap)
    if name == 'can':
        c.drawPath(heart_path(n), P)
        c.drawCircle(n * 0.36, n * 0.33, n * 0.06, clr)  # parlama oyuğu
    elif name == 'sise':
        # kımız matarası: geniş gövde, boyun, tıpa, kayış
        c.drawOval(skia.Rect(n * 0.2, n * 0.38, n * 0.8, n * 0.9), P)
        c.drawRect(skia.Rect(n * 0.41, n * 0.18, n * 0.59, n * 0.45), P)
        c.drawRoundRect(skia.Rect(n * 0.36, n * 0.1, n * 0.64, n * 0.22), n * 0.04, n * 0.04, P)
        c.drawLine(n * 0.24, n * 0.58, n * 0.76, n * 0.58, clr_s)
    elif name == 'altin':
        c.drawCircle(n / 2, n / 2, n * 0.38, P)
        c.drawRect(skia.Rect(n * 0.43, n * 0.43, n * 0.57, n * 0.57), clr)
        ring = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kClear, Style=skia.Paint.kStroke_Style, StrokeWidth=n * 0.03)
        c.drawCircle(n / 2, n / 2, n * 0.29, ring)
    elif name == 'kut':
        # Kut alevi: yukarı kıvrılan damla + iç girdap
        p = skia.Path()
        p.moveTo(n * 0.52, n * 0.06)
        p.cubicTo(n * 0.62, n * 0.3, n * 0.84, n * 0.45, n * 0.8, n * 0.66)
        p.cubicTo(n * 0.76, n * 0.86, n * 0.6, n * 0.94, n * 0.48, n * 0.94)
        p.cubicTo(n * 0.3, n * 0.94, n * 0.18, n * 0.8, n * 0.2, n * 0.62)
        p.cubicTo(n * 0.22, n * 0.44, n * 0.42, n * 0.36, n * 0.52, n * 0.06)
        p.close()
        c.drawPath(p, P)
        sw = skia.Path()
        sw.moveTo(n * 0.5, n * 0.84)
        sw.cubicTo(n * 0.3, n * 0.8, n * 0.36, n * 0.56, n * 0.52, n * 0.6)
        sw.cubicTo(n * 0.64, n * 0.63, n * 0.6, n * 0.75, n * 0.52, n * 0.73)
        c.drawPath(sw, clr_s)
    elif name == 'kurt':
        c.drawPath(poly([(0.16, 0.06), (0.36, 0.3), (0.64, 0.3), (0.84, 0.06), (0.86, 0.45), (0.74, 0.62),
                         (0.6, 0.94), (0.4, 0.94), (0.26, 0.62), (0.14, 0.45)], n), P)
        c.drawPath(poly([(0.3, 0.46), (0.44, 0.5), (0.32, 0.53)], n), clr)
        c.drawPath(poly([(0.7, 0.46), (0.56, 0.5), (0.68, 0.53)], n), clr)
        c.drawPath(poly([(0.25, 0.14), (0.33, 0.3), (0.27, 0.3)], n), clr)
        c.drawPath(poly([(0.75, 0.14), (0.67, 0.3), (0.73, 0.3)], n), clr)
    elif name == 'kartal':
        # açık kanatlı kartal (ön görünüş)
        c.drawPath(poly([(0.5, 0.32), (0.04, 0.16), (0.1, 0.3), (0.06, 0.36), (0.14, 0.46), (0.12, 0.52),
                         (0.38, 0.58), (0.42, 0.72), (0.3, 0.92), (0.5, 0.84), (0.7, 0.92), (0.58, 0.72), (0.62, 0.58),
                         (0.88, 0.52), (0.86, 0.46), (0.94, 0.36), (0.9, 0.3), (0.96, 0.16)], n), P)
        c.drawCircle(n * 0.5, n * 0.24, n * 0.11, P)
        c.drawPath(poly([(0.56, 0.2), (0.7, 0.26), (0.58, 0.3)], n), P)
        c.drawCircle(n * 0.47, n * 0.22, n * 0.025, clr)
    elif name == 'ayi':
        c.drawCircle(n * 0.26, n * 0.26, n * 0.13, P)
        c.drawCircle(n * 0.74, n * 0.26, n * 0.13, P)
        c.drawOval(skia.Rect(n * 0.12, n * 0.2, n * 0.88, n * 0.92), P)
        c.drawCircle(n * 0.36, n * 0.48, n * 0.045, clr)
        c.drawCircle(n * 0.64, n * 0.48, n * 0.045, clr)
        c.drawOval(skia.Rect(n * 0.38, n * 0.6, n * 0.62, n * 0.8), clr)
        c.drawOval(skia.Rect(n * 0.45, n * 0.62, n * 0.55, n * 0.69), P)
    elif name == 'kafatasi':
        c.drawCircle(n * 0.5, n * 0.42, n * 0.34, P)
        c.drawRoundRect(skia.Rect(n * 0.3, n * 0.55, n * 0.7, n * 0.9), n * 0.06, n * 0.06, P)
        c.drawOval(skia.Rect(n * 0.27, n * 0.38, n * 0.45, n * 0.58), clr)
        c.drawOval(skia.Rect(n * 0.55, n * 0.38, n * 0.73, n * 0.58), clr)
        c.drawPath(poly([(0.5, 0.6), (0.45, 0.7), (0.55, 0.7)], n), clr)
        for k in range(3):
            xx = 0.4 + k * 0.1
            c.drawRect(skia.Rect(n * (xx - 0.015), n * 0.78, n * (xx + 0.015), n * 0.9), clr)
    elif name == 'zaman':
        c.drawPath(poly([(0.24, 0.14), (0.76, 0.14), (0.54, 0.5), (0.76, 0.86), (0.24, 0.86), (0.46, 0.5)], n), P)
        c.drawRoundRect(skia.Rect(n * 0.16, n * 0.06, n * 0.84, n * 0.15), n * 0.03, n * 0.03, P)
        c.drawRoundRect(skia.Rect(n * 0.16, n * 0.85, n * 0.84, n * 0.94), n * 0.03, n * 0.03, P)
        c.drawPath(poly([(0.33, 0.24), (0.67, 0.24), (0.5, 0.45)], n), clr)
    elif name == 'kilic':
        p = skia.Path()
        p.moveTo(n * 0.2, n * 0.82)
        p.cubicTo(n * 0.45, n * 0.62, n * 0.7, n * 0.4, n * 0.92, n * 0.06)
        p.cubicTo(n * 0.82, n * 0.42, n * 0.58, n * 0.66, n * 0.28, n * 0.9)
        p.close()
        c.drawPath(p, P)
        g = paint(n * 0.07)
        c.drawLine(n * 0.12, n * 0.7, n * 0.36, n * 0.94, g)
        c.drawLine(n * 0.22, n * 0.84, n * 0.08, n * 0.98, paint(n * 0.08))
    elif name == 'tilsim':
        # üçgen muska: askı halkası, iç üçgen, püskül
        c.drawPath(poly([(0.5, 0.2), (0.88, 0.82), (0.12, 0.82)], n), P)
        c.drawCircle(n * 0.5, n * 0.12, n * 0.08, paint(n * 0.05))
        c.drawPath(poly([(0.5, 0.42), (0.68, 0.72), (0.32, 0.72)], n), clr)
        c.drawCircle(n * 0.5, n * 0.63, n * 0.05, P)
        c.drawLine(n * 0.5, n * 0.82, n * 0.5, n * 0.96, paint(n * 0.05))
    elif name == 'davul':
        # kam davulu (tüngür): oval deri, ortada çarmıh ve dört nokta
        c.drawOval(skia.Rect(n * 0.12, n * 0.08, n * 0.88, n * 0.92), P)
        s = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kClear, Style=skia.Paint.kStroke_Style, StrokeWidth=n * 0.045)
        c.drawOval(skia.Rect(n * 0.22, n * 0.18, n * 0.78, n * 0.82), s)
        c.drawLine(n * 0.5, n * 0.24, n * 0.5, n * 0.76, s)
        c.drawLine(n * 0.28, n * 0.5, n * 0.72, n * 0.5, s)
        for (a, b) in [(0.36, 0.36), (0.64, 0.36), (0.36, 0.64), (0.64, 0.64)]:
            c.drawCircle(n * a, n * b, n * 0.035, clr)
    elif name == 'ruh':
        # ruh: kuyruklu yükselen sis (don)
        p = skia.Path()
        p.moveTo(n * 0.5, n * 0.1)
        p.cubicTo(n * 0.82, n * 0.12, n * 0.86, n * 0.5, n * 0.64, n * 0.62)
        p.cubicTo(n * 0.56, n * 0.7, n * 0.7, n * 0.82, n * 0.6, n * 0.94)
        p.cubicTo(n * 0.5, n * 0.84, n * 0.4, n * 0.8, n * 0.36, n * 0.66)
        p.cubicTo(n * 0.1, n * 0.56, n * 0.16, n * 0.12, n * 0.5, n * 0.1)
        p.close()
        c.drawPath(p, P)
        c.drawOval(skia.Rect(n * 0.34, n * 0.32, n * 0.44, n * 0.44), clr)
        c.drawOval(skia.Rect(n * 0.56, n * 0.32, n * 0.66, n * 0.44), clr)
    elif name == 'kalkan':
        c.drawCircle(n * 0.5, n * 0.5, n * 0.4, P)
        c.drawCircle(n * 0.5, n * 0.5, n * 0.1, clr)
        c.drawCircle(n * 0.5, n * 0.5, n * 0.06, P)


def icons(N=128):
    S = 4
    n = N * S * HD
    cols = len(ICONS)
    N = N * HD               # HD paketi: hücre HD kat (çizim n'ye göreli)
    out = np.zeros((N, N * cols, 4), np.float32)
    for i, nm in enumerate(ICONS):
        surf, c = sk_canvas(n, n)
        c.translate(n * 0.1, n * 0.1)
        c.scale(0.8, 0.8)
        icon_shape(nm, c, n)
        F = sk_mask(surf)
        # mürekkep kontur: dış (kalın, alt-sağda kalın) + iç kenar
        r = int(n * 0.045)
        st = ndimage.generate_binary_structure(2, 1)
        D = ndimage.grey_dilation(F, footprint=disk(r))
        D2 = ndimage.grey_dilation(ndimage.shift(F, (n * 0.012, n * 0.012), order=1), footprint=disk(r))
        O = np.clip(np.maximum(D, D2), 0, 1)
        Ein = ndimage.grey_erosion(F, footprint=disk(max(1, r // 3)))
        lineIn = np.clip(F - Ein, 0, 1)
        # gölge: alt-sağ hilal
        Fs = ndimage.shift(F, (-n * 0.05, -n * 0.05), order=1)
        shade = np.clip(F - Fs, 0, 1)
        lum = 1.0 - 0.32 * ndimage.gaussian_filter(shade, n * 0.01)
        # parlama: üst-sol ince hilal
        Fh = ndimage.shift(F, (n * 0.035, n * 0.035), order=1)
        hi = np.clip(F - Fh, 0, 1) * 0.0
        rgb = np.clip(lum + hi, 0, 1)
        ink = np.clip(O - F + lineIn * 0.85, 0, 1)
        alpha = np.clip(np.maximum(O, F), 0, 1)
        col = rgb * (1 - ink) + 0.02 * ink
        rng = np.random.default_rng(200 + i)
        col *= 1.0 - 0.06 * fbm2(n, n, 10 * S, rng, 3, aniso=(1, 4))
        a = down(alpha, S)
        cc = down(col * alpha, S) / np.maximum(a, 1e-4)
        out[:, i * N:(i + 1) * N, 0] = cc
        out[:, i * N:(i + 1) * N, 1] = cc
        out[:, i * N:(i + 1) * N, 2] = cc
        out[:, i * N:(i + 1) * N, 3] = a
    Image.fromarray(np.clip(np.rint(out * 255), 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'icons.png'))
    print('yazıldı icons.png', ICONS)


def disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


IMPORT = """[remap]

importer="texture"
type="CompressedTexture2D"

[params]

compress/mode=0
mipmaps/generate=true
process/fix_alpha_border=true
"""


def write_imports():
    for f in os.listdir(OUT):
        if f.endswith('.png') and not os.path.exists(os.path.join(OUT, f + '.import')):
            with open(os.path.join(OUT, f + '.import'), 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(IMPORT)


if __name__ == '__main__':
    import sys
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:]
    for fn in [frame, fill, swash, stroke, seal, enso, splat, band, vignette, horn, tamga, paper, icons]:
        if not only or fn.__name__ in only:
            fn()
    write_imports()
