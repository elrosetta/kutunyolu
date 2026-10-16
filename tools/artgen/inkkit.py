"""Stil v2 "mürekkep" çizim takımı: el çizimi çizgi roman / animasyon görünümü (piksel sanat DEĞİL).

Her şey kenar yumuşatmalı, doku yoğunluğu 1080p'de 1 doku pikseli = 1 ekran pikseli (dünya biriminde 2 doku pikseli;
oyun 960x540 dünya birimi gösterir). Oyunda doğrusal süzgeç + mipmap ile çizilir.

Yapı: numpy float32 ÖNÇARPILMIŞ RGBA katmanlar (Layer). Karmaşık şekiller skia-python ile maske/renkli çizim olarak
üretilir, gövde gölgelemesi (silindirik ağaç gövdesi, kaya hacmi, sis) numpy ile hesaplanır.
"""
import math
import numpy as np
import skia
from scipy import ndimage

INK = (21, 22, 29)          # mavi-siyah mürekkep #15161d


# ------------------------------------------------------------------ renk yardımcıları
def c01(c):
    return np.array(c[:3], np.float32) / 255.0


def mix(a, b, t):
    a = np.asarray(a, np.float32)
    b = np.asarray(b, np.float32)
    return a + (b - a) * t


def sk_col(c, a=1.0):
    c = [float(v) for v in c]
    if max(c[:3]) > 1.0:
        c = [v / 255.0 for v in c[:3]] + c[3:]
    return skia.Color4f(c[0], c[1], c[2], a)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ gürültü
def noise(w, h, sigma, seed, wrap=True, sx=None, sy=None):
    """Döşenebilir yumuşak gürültü, yaklaşık [-1, 1]. sx/sy ile yönlü (yatay sis şeritleri vb.)."""
    rng = np.random.default_rng(seed)
    f = rng.standard_normal((h, w)).astype(np.float32)
    sg = (sy if sy is not None else sigma, sx if sx is not None else sigma)
    f = ndimage.gaussian_filter(f, sg, mode='wrap' if wrap else 'reflect')
    f /= (f.std() * 2.2 + 1e-6)
    return np.clip(f, -1, 1)


def fbm(w, h, sigmas, seed, wrap=True, weights=None):
    out = np.zeros((h, w), np.float32)
    weights = weights or [0.5 ** i for i in range(len(sigmas))]
    for i, (s, wt) in enumerate(zip(sigmas, weights)):
        out += noise(w, h, s, seed + 101 * i, wrap) * wt
    return out / sum(weights)


# ------------------------------------------------------------------ katman
class Layer:
    """Önçarpılmış float RGBA tuval."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.float32)

    def over(self, src, x=0, y=0):
        """src (önçarpılmış) bu katmanın ÜSTÜNE, (x, y) konumuna."""
        sh, sw = src.shape[:2]
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + sw), min(self.h, y + sh)
        if x1 <= x0 or y1 <= y0:
            return
        s = src[y0 - y:y1 - y, x0 - x:x1 - x]
        d = self.a[y0:y1, x0:x1]
        self.a[y0:y1, x0:x1] = s + d * (1.0 - s[..., 3:4])

    def over_wrap(self, src, x, y):
        """Yatay döşenen katman için: kenardan taşan parça öbür uçtan girer."""
        sw = src.shape[1]
        for dx in (-self.w, 0, self.w):
            if x + dx < self.w and x + dx + sw > 0:
                self.over(src, x + dx, y)

    def fill_mask(self, mask, color, alpha=1.0):
        """mask (h, w) kaplama, color (3,) ya da (h, w, 3) 0..1."""
        m = (mask * alpha)[..., None]
        col = np.asarray(color, np.float32)
        src_rgb = col * m if col.ndim == 1 else col * m
        self.a[..., :3] = src_rgb + self.a[..., :3] * (1 - m)
        self.a[..., 3:4] = m + self.a[..., 3:4] * (1 - m)

    def rgba8(self):
        a = self.a[..., 3:4]
        rgb = np.where(a > 1e-5, self.a[..., :3] / np.maximum(a, 1e-5), 0.0)
        out = np.concatenate([rgb, a], -1)
        return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


def premul(rgb, a):
    return np.concatenate([rgb * a[..., None], a[..., None]], -1).astype(np.float32)


# ------------------------------------------------------------------ skia köprüsü
class Sk:
    """skia yüzeyi; çizim sonrası önçarpılmış float dizi (snap) verir."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.s = skia.Surface(w, h)
        self.c = self.s.getCanvas()
        self.c.clear(skia.ColorTRANSPARENT)

    def paint(self, col, a=1.0, blur=0.0, stroke=0.0, blend=None):
        p = skia.Paint(AntiAlias=True, Color=sk_col(col, a))
        if blur > 0:
            p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
        if stroke > 0:
            p.setStyle(skia.Paint.kStroke_Style)
            p.setStrokeWidth(stroke)
            p.setStrokeCap(skia.Paint.kRound_Cap)
            p.setStrokeJoin(skia.Paint.kRound_Join)
        if blend is not None:
            p.setBlendMode(blend)
        return p

    def path(self, path, col, a=1.0, blur=0.0, stroke=0.0, blend=None):
        self.c.drawPath(path, self.paint(col, a, blur, stroke, blend))

    def snap(self):
        arr = self.s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
        return arr.astype(np.float32) / 255.0

    def mask(self):
        return self.snap()[..., 3]


def mask_of(w, h, paths, blur=0.0):
    s = Sk(w, h)
    for p in paths:
        s.path(p, (255, 255, 255), 1.0, blur)
    return s.mask()


# ------------------------------------------------------------------ yol yardımcıları
def poly_path(pts, closed=True):
    p = skia.Path()
    p.moveTo(float(pts[0][0]), float(pts[0][1]))
    for q in pts[1:]:
        p.lineTo(float(q[0]), float(q[1]))
    if closed:
        p.close()
    return p


def smooth_path(pts, closed=True, tension=0.5):
    """Catmull-Rom -> kübik Bezier, yumuşak organik kontur."""
    pts = [tuple(map(float, q)) for q in pts]
    n = len(pts)
    p = skia.Path()
    p.moveTo(*pts[0])
    rng_ = range(n) if closed else range(n - 1)
    for i in rng_:
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else p2
        k = tension / 3.0 * 2.0
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 2, p1[1] + (p2[1] - p0[1]) * k / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 2, p2[1] - (p3[1] - p1[1]) * k / 2)
        p.cubicTo(*c1, *c2, *p2)
    if closed:
        p.close()
    return p


def ribbon(pts, widths, cap=True):
    """Değişken kalınlıklı fırça darbesi: merkez çizgisi + her noktada kalınlık -> kapalı çokgen."""
    pts = np.asarray(pts, np.float64)
    widths = np.asarray(widths, np.float64)
    d = np.gradient(pts, axis=0)
    ln = np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-6)
    nrm = np.stack([-d[:, 1] / ln, d[:, 0] / ln], 1)
    left = pts + nrm * (widths[:, None] * 0.5)
    right = pts - nrm * (widths[:, None] * 0.5)
    poly = np.concatenate([left, right[::-1]], 0)
    return smooth_path(poly, True, 0.35) if len(poly) > 6 else poly_path(poly)


def bezier(p0, p1, p2, n=12):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = (np.asarray(p, np.float64) for p in (p0, p1, p2))
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2


def blade(x, y, h, lean, w, curl=0.35, n=10):
    """Ot yaprağı: tabandan (x, y) yukarı, uca doğru incelen kavisli darbe."""
    tip = (x + lean * h, y - h)
    ctrl = (x + lean * h * curl, y - h * 0.62)
    pts = bezier((x, y), ctrl, tip, n)
    ws = w * (1 - np.linspace(0, 1, n) ** 1.3) + 0.35
    return ribbon(pts, ws)


def leaf_shape(cx, cy, length, width, ang):
    """Mızrak biçimli yaprak (söğüt/huş/bambu benzeri), açı radyan."""
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for t in np.linspace(0, 1, 9):
        wv = math.sin(math.pi * t) ** 0.8 * width * 0.5
        pts.append((t * length, wv))
    for t in np.linspace(1, 0, 9)[1:-1]:
        wv = math.sin(math.pi * t) ** 0.8 * width * 0.5
        pts.append((t * length, -wv * 0.8))
    out = [(cx + px * ca - py * sa, cy + px * sa + py * ca) for px, py in pts]
    return smooth_path(out, True, 0.4)


def blob(cx, cy, rx, ry, seed, n=14, jitter=0.12, flat_bottom=False):
    """Organik kapalı kontur (kaya, çalı kümesi, taş)."""
    rng = np.random.default_rng(seed)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1 + rng.uniform(-jitter, jitter)
        px, py = cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r
        if flat_bottom and py > cy:
            py = cy + (py - cy) * 0.25
        pts.append((px, py))
    return smooth_path(pts, True, 0.5)


# ------------------------------------------------------------------ gövde (huş / çam / karaçam)
def trunk(H, W, base_y, x0, width, seed, kind='pine', lean=0.0, bend=0.0, top_y=-40,
          bark=(70, 62, 60), light=(150, 175, 150), rim=(190, 230, 205), ink=INK, ink_w=3.0,
          light_side=-1.0, detail=1.0, taper=0.35):
    """Analitik ağaç gövdesi -> (önçarpılmış RGBA parça, x konumu, y konumu).

    Kesit silindirik gölgelenir (ışık tarafı açık, ters taraf koyu, arkadan sis kenar ışığı), iki yanda değişken
    kalınlıkta mürekkep konturu, kabuk deseni: çam = dikey kırık sırtlar ve levhalar, huş = açık kabuk üzerinde
    yatay kara mercimek izleri ve dal yaraları."""
    rng = np.random.default_rng(seed)
    y_top = int(max(top_y, -200))
    hh = int(base_y - y_top + 4)
    ys = np.arange(y_top, y_top + hh, dtype=np.float32)
    t = np.clip((base_y - ys) / max(1.0, base_y - y_top), 0, 1)        # 0 taban, 1 tepe
    cx = x0 + lean * (base_y - ys) + bend * np.sin(t * math.pi) * width
    cx += noise(1, hh, 18, seed, wrap=False)[:, 0] * width * 0.06
    hw = width * 0.5 * (1 - taper * t)
    # taban genişlemesi (kök boğazı)
    flare = np.exp(-((base_y - ys) / (width * 0.9)) ** 2) * width * 0.35
    hw = hw + flare
    pad = int(width * 0.9 + 8 + abs(lean) * hh * 0 + abs(bend) * width)
    xl = int(np.floor((cx - hw).min())) - 6
    xr = int(np.ceil((cx + hw).max())) + 6
    ww = xr - xl
    xs = np.arange(xl, xr, dtype=np.float32)[None, :] + 0.5
    dx = xs - cx[:, None]
    hwc = hw[:, None]
    cov = np.clip(hwc - np.abs(dx) + 0.5, 0, 1)
    u = np.clip(dx / np.maximum(hwc, 1), -1, 1)                        # -1 sol kenar, 1 sağ kenar
    # silindirik gölgeleme: ışık tarafı (light_side) açık
    lam = np.clip(0.55 + 0.6 * (-u * light_side) * 0.8 + 0.25 * np.sqrt(np.clip(1 - u * u, 0, 1)), 0, 1.2)
    bark_c = c01(bark)
    light_c = c01(light)
    rim_c = c01(rim)
    col = bark_c[None, None, :] * (0.55 + 0.6 * lam[..., None])
    # boyuna kabuk dokusu
    nz = noise(ww, hh, 1.5, seed + 3, wrap=False, sx=1.2, sy=9.0)
    nz2 = noise(ww, hh, 3, seed + 5, wrap=False, sx=3, sy=22)
    if kind == 'birch':
        col = mix(col, light_c[None, None, :] * (0.6 + 0.5 * lam[..., None]), 0.75)
        col *= (1 + 0.05 * nz2[..., None])
    else:
        ridge = np.clip(nz * 1.6, -1, 1)
        col *= (1 + 0.16 * ridge[..., None] * detail + 0.08 * nz2[..., None])
    # sisten gelen kenar ışığı (ışığın tersi tarafında ince açık şerit)
    rim_band = smoothstep(0.55, 0.92, u * (-light_side)) * (1 - smoothstep(0.92, 1.0, u * (-light_side)))
    col = mix(col, rim_c[None, None, :], (rim_band * 0.55)[..., None])
    # ışık tarafında ay vurgusu
    hl = smoothstep(0.35, 0.75, -u * light_side) * (1 - smoothstep(0.8, 0.98, -u * light_side))
    col = mix(col, light_c[None, None, :] * 1.08, (hl * 0.35)[..., None])
    rgb = col
    # mürekkep konturu (değişken kalınlık, ara ara incelir)
    iw = ink_w * (0.75 + 0.5 * (noise(1, hh, 14, seed + 9, wrap=False)[:, 0] * 0.5 + 0.5))
    iw_l = iw * (1.15 if light_side > 0 else 0.8)
    iw_r = iw * (0.8 if light_side > 0 else 1.15)
    edge_d = hwc - np.abs(dx)
    iwc = np.where(dx < 0, iw_l[:, None], iw_r[:, None])
    ink_m = np.clip(iwc - edge_d + 0.5, 0, 1) * cov
    rgb = mix(rgb, c01(ink)[None, None, :], ink_m[..., None])
    out = premul(rgb, cov)
    # kabuk işaretleri skia ile (gövdenin içine kırpılır)
    sk = Sk(ww, hh)
    n_marks = int(hh / (14 if kind == 'birch' else 6) * detail)
    for _ in range(n_marks):
        yy = rng.uniform(0, hh)
        iy = int(np.clip(yy, 0, hh - 1))
        ccx = cx[iy] - xl
        w_here = hw[iy]
        if kind == 'birch':
            # yatay mercimek izi: kısa, uçları sivri koyu çizgi
            ln = rng.uniform(0.25, 0.8) * w_here * 2
            off = rng.uniform(-w_here * 0.6, w_here * 0.6)
            x_a = ccx + off - ln / 2
            pts = [(x_a + ln * s, yy + math.sin(s * math.pi) * rng.uniform(-1.2, 1.2)) for s in np.linspace(0, 1, 6)]
            ws = np.sin(np.linspace(0, 1, 6) * math.pi) * rng.uniform(1.2, 3.2) + 0.3
            sk.path(ribbon(pts, ws), ink, rng.uniform(0.55, 0.9))
            if rng.random() < 0.12:
                # dal yarası: koyu üçgen "kaş"
                r = w_here * rng.uniform(0.25, 0.45)
                cxx = ccx + rng.uniform(-w_here * 0.3, w_here * 0.3)
                pts = [(cxx - r * 1.4, yy), (cxx, yy - r * 0.55), (cxx + r * 1.4, yy), (cxx, yy + r * 0.35)]
                sk.path(smooth_path(pts, True, 0.4), ink, 0.85)
        else:
            # çam: dikey kırık sırt çizgisi
            ln = rng.uniform(8, 26)
            off = rng.uniform(-0.85, 0.85)
            xa = ccx + off * w_here
            pts = [(xa + rng.uniform(-0.8, 0.8), yy + ln * s) for s in np.linspace(0, 1, 5)]
            ws = np.sin(np.linspace(0, 1, 5) * math.pi) * rng.uniform(0.8, 2.2) * (0.6 + 0.6 * abs(off)) + 0.2
            sk.path(ribbon(pts, ws), ink, rng.uniform(0.35, 0.75) * detail)
            if rng.random() < 0.35:
                # levha arası yatay kısa çatlak
                yb = yy + ln * rng.uniform(0.3, 1.0)
                xb = xa + rng.uniform(-0.4, 0.4) * w_here
                sk.path(ribbon([(xb - 4, yb), (xb, yb + 0.8), (xb + 5, yb - 0.4)], [0.3, 1.4, 0.3]), ink, 0.5 * detail)
    # gölge tarafında çizgi roman taraması (kısa eğik darbeler, öbekler halinde)
    if detail > 0.45:
        yy = rng.uniform(0, 30)
        while yy < hh:
            if rng.random() < 0.55:
                n_h = rng.integers(3, 8)
                for k in range(n_h):
                    y_ = yy + k * rng.uniform(4.5, 7.5)
                    iy = int(np.clip(y_, 0, hh - 1))
                    ccx = cx[iy] - xl
                    w_here = hw[iy]
                    edge_x = ccx - light_side * w_here
                    ln = w_here * rng.uniform(0.35, 0.7)
                    x_in = edge_x + light_side * ln
                    pts = [(edge_x, y_ + ln * 0.35), ((edge_x + x_in) / 2, y_ + ln * 0.15), (x_in, y_)]
                    sk.path(ribbon(pts, [1.3, 1.0, 0.2]), ink, rng.uniform(0.3, 0.55) * detail)
            yy += rng.uniform(40, 110)
    # kök boğazında koyu, pürüzlü taban (huşun kara alt kabuğu, çamın kalın kabuğu)
    if detail > 0.45:
        for _ in range(int(6 + 10 * detail)):
            y_ = hh - rng.uniform(4, width * (1.4 if kind == 'birch' else 0.9))
            iy = int(np.clip(y_, 0, hh - 1))
            ccx = cx[iy] - xl
            w_here = hw[iy]
            xa = ccx + rng.uniform(-0.9, 0.9) * w_here
            ln = rng.uniform(8, 22)
            pts = [(xa + rng.uniform(-1, 1), y_ - ln * s) for s in np.linspace(0, 1, 4)]
            sk.path(ribbon(pts, [0.4, rng.uniform(1.5, 3.5), rng.uniform(1.0, 2.5), 0.3]), ink, rng.uniform(0.5, 0.85))
    marks = sk.snap()
    marks *= cov[..., None]
    out = marks + out * (1 - marks[..., 3:4])
    return out, xl, y_top


def apply_fog(arr, y0, fog_rgb_y, amount_y):
    """Önçarpılmış parçaya (arr, üst kenarı y0) satıra göre sis karıştır: fog_rgb_y (H,3), amount_y (H,)."""
    h = arr.shape[0]
    H = fog_rgb_y.shape[0]
    rows = np.clip(np.arange(y0, y0 + h), 0, H - 1)
    f = amount_y[rows][:, None, None]
    fc = fog_rgb_y[rows][:, None, :]
    a = arr[..., 3:4]
    arr[..., :3] = arr[..., :3] * (1 - f) + fc * a * f
    return arr


def save_png(path, rgba8):
    from PIL import Image
    Image.fromarray(rgba8, 'RGBA').save(path, optimize=True)
