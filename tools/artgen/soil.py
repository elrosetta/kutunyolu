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

HD (set_hd(N), N = 2 / 4): aynı tasarım N kat ince piksel ızgarasında YENİDEN ÇİZİLİR (büyütme değil).
TS, S, P mantıksal ölçüler olarak kalır; atlas hücresi 36N, toprak dokusu 768N olur. Konumlar, katmanlar,
kayalar, kökler, otlar, paletler ve anahtar renkler aynıdır; eğriler/kenarlar ince basamaklı, tane ve
titreşim ince pikseldedir, '1 piksellik' çizgiler mantıksal olarak biraz incelir (_lw). Rastgele
üreteçler her N'de aynı sırayla tüketilir; ince tane yalnızca yan üreteçten gelir. HD = 1 eski çıktının
aynısıdır.
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
HD = 1                          # çıktı çözünürlük çarpanı (set_hd)
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


# ------------------------------------------------------------------ HD (yeniden çizim) yardımcıları
def set_hd(n):
    """Çıktı çözünürlük çarpanı. 1 = taban (bayt bayt eski çıktı); 2/4 = '2K'/'4K'.

    HD = N iken her şey aynı mantıksal ölçüde (TS, S, P) tasarlanır ama N kat ince piksel ızgarasında
    yeniden çizilir: atlas ve toprak dokusu tam N kat büyür, yerleşim/renk/anahtarlar aynı kalır.
    Rastgele üreteçler her N'de aynı sırayla tüketilir (aynı tohum → aynı yerleşim)."""
    global HD
    n = int(n)
    if n < 1:
        raise ValueError('HD >= 1 olmalı')
    HD = n


def _lw():
    """HD'de '1 piksellik' çizgilerin mantıksal kalınlığı (N=1: 1, N=2: 0.75, N=4: 0.625)."""
    return 0.5 + 0.5 / HD


def _lwf():
    """_lw() ince piksel cinsinden (en az 1)."""
    return max(1, int(math.ceil(_lw() * HD - 1e-9)))


def _side_rng(seed):
    """İnce taneler için yan üreteç: ana üreteçlere dokunmaz, HD'ye göre belirlenimci."""
    return np.random.Generator(np.random.PCG64(seed * 7919 + 1013 * HD))


def _dil(m, shifts):
    """Sarmalı kaydırmaların birleşimi (ikili genişletme)."""
    out = np.zeros_like(m)
    for dy, dx in shifts:
        out |= roll(m, dy, dx)
    return out


def _vn_eval(g, gw, gh, w, h):
    """hdkit.vnoise'un örnekleme adımı (kafes g zaten çekilmiş): w x h ızgarada."""
    ys = np.arange(h) * gh / h
    xs = np.arange(w) * gw / w
    y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
    fy = ys - y0; fx = xs - x0
    fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
    y1, x1 = y0 + 1, x0 + 1
    a = g[y0][:, x0]; b = g[y0][:, x1]; c = g[y1][:, x0]; d = g[y1][:, x1]
    top = a * (1 - fx) + b * fx
    bot = c * (1 - fx) + d * fx
    return top * (1 - fy[:, None]) + bot * fy[:, None]


def _fbm2(size, cells, rng, gain=0.55):
    """hdkit.fbm(size, size, cells, rng) ile aynı kafesler (aynı rng tüketimi); hem mantıksal
    (size²) hem HD kat ince ((size*HD)²) örneklemeyi döndürür."""
    n = HD
    out_l = np.zeros((size, size)); out_f = np.zeros((size * n, size * n)); tot = 0.0; amp = 1.0
    for c in cells:
        cy = max(1.0, c)
        gw, gh = max(1, int(round(size / c))), max(1, int(round(size / cy)))
        g = rng.random((gh + 1, gw + 1))
        g[:, gw] = g[:, 0]
        g[gh, :] = g[0, :]
        out_l += _vn_eval(g, gw, gh, size, size) * amp
        out_f += _vn_eval(g, gw, gh, size * n, size * n) * amp
        tot += amp; amp *= gain
    return out_l / tot, out_f / tot


def _hash_np(*a):
    """_hash'in vektörel eşi (aynı sonuç)."""
    h = np.zeros(np.broadcast(*[np.asarray(v) for v in a]).shape, np.int64)
    for v in a:
        h = (h * 1000003 + np.asarray(v, np.int64) * 7919 + 12345) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0x5bd1e995) & 0xFFFFFFFF
    return (h ^ (h >> 15)) / 4294967295.0


_HT = {}


def _htab(salt):
    """_hash(u, salt), u = 0..P-1 tablosu."""
    t = _HT.get(salt)
    if t is None:
        t = _HT[salt] = np.array([_hash(u, salt) for u in range(P)])
    return t


def _dense(pts):
    """Çoklu çizgiyi ~1/(2*HD) adımlı örneklere böl."""
    p = np.asarray(pts, float).reshape(-1, 2)
    if len(p) == 1:
        return p
    out = []
    for a, b in zip(p[:-1], p[1:]):
        m = max(1, int(math.ceil(math.hypot(*(b - a)) * 2 * HD)))
        out.append(a + (b - a) * np.linspace(0, 1, m, endpoint=False)[:, None])
    out.append(p[-1:])
    return np.vstack(out)


def _lin(a, b, per=1.0):
    """[a, b] aralığında ~1/(2*HD) adımlı parametre dizisi."""
    return np.linspace(a, b, max(2, int(math.ceil(abs(b - a) * 2 * HD * per)) + 1))


class _FG:
    """İnce ızgara: mantıksal 'indeks' koordinatları (taban piksel merkezi = tam sayı) ile çizim.
    size mantıksal kenar, pad her yanda mantıksal dolgu."""

    def __init__(self, size, pad=0):
        self.n = n = HD
        self.pad = pad
        self.N = (size + 2 * pad) * n
        self.g = (np.arange(self.N) + 0.5) / n - 0.5 - pad

    def span(self, a0, a1):
        """[a0, a1] indeks aralığını kapsayan ince indeks dilimi (kırpılmış)."""
        n = self.n
        i0 = max(0, int(math.floor((a0 + 0.5 + self.pad) * n)))
        i1 = min(self.N, int(math.floor((a1 + 0.5 + self.pad) * n)) + 1)
        return i0, i1

    def stroke(self, pts, hw):
        """Örnek noktalar (K,2) ve yarı genişlikler: her pikselde en yakın (normalize) örnek.
        Döner: (iy, ix, örnek_no, ox, oy) — ox/oy pikselin o örneğe göre konumu."""
        p = np.asarray(pts, float).reshape(-1, 2)
        hw = np.broadcast_to(np.asarray(hw, float), (len(p),))
        mh = float(hw.max())
        i0, i1 = self.span(p[:, 1].min() - mh, p[:, 1].max() + mh)
        j0, j1 = self.span(p[:, 0].min() - mh, p[:, 0].max() + mh)
        if i0 >= i1 or j0 >= j1:
            e = np.zeros(0, int)
            return e, e, e, np.zeros(0), np.zeros(0)
        Y = self.g[i0:i1]; X = self.g[j0:j1]
        ox = X[None, None, :] - p[:, 0, None, None]
        oy = Y[None, :, None] - p[:, 1, None, None]
        d = (ox * ox + oy * oy) / (hw[:, None, None] ** 2)
        k = d.argmin(0)
        dm = np.take_along_axis(d, k[None], 0)[0]
        iy, ix = np.nonzero(dm < 1.0)
        kk = k[iy, ix]
        return iy + i0, ix + j0, kk, ox[kk, 0, ix], oy[kk, iy, 0]


def _grid():
    """Karo (TS) ince ızgarasının indeks koordinatları: (Y sütun, X satır vektörü)."""
    g = (np.arange(TS * HD) + 0.5) / HD - 0.5
    return g[:, None], g[None, :]


def _ovm(img, m, c):
    img[m, :3] = c
    img[m, 3] = 1


def _stroke_img(img, xs, ys, hw, cols):
    """Süs karosuna (TS*HD) kalınlığı değişen çizgi; cols (3,) ya da örnek başına (K,3)."""
    xs, ys = np.broadcast_arrays(np.asarray(xs, float), np.asarray(ys, float))
    iy, ix, k, _, _ = _FG(TS).stroke(np.stack([xs.ravel(), ys.ravel()], -1), hw)
    if len(iy) == 0:
        return
    cols = np.asarray(cols, float)
    img[iy, ix, :3] = cols[k] if cols.ndim == 2 else cols
    img[iy, ix, 3] = 1


def _dot(img, x, y, c, r=0.66):
    _stroke_img(img, [x], [y], r, c)


class _FCanvas(ShapeCanvas):
    """ShapeCanvas + pencereli (hızlı) tube: sonuç maskesi içinde özdeş."""

    def tube(self, pts, r0, r1, mat, z=0.0, rr=None):
        pts = np.asarray(pts, float)
        if len(pts) < 2:
            return
        seg = []
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            n = max(2, int(np.hypot(*(b - a)) * 2) + 1)
            for t in np.linspace(0, 1, n, endpoint=False):
                seg.append(a + (b - a) * t)
        seg.append(pts[-1])
        seg = np.array(seg)
        rads = np.linspace(r0, r1, len(seg)) if rr is None else np.interp(np.linspace(0, 1, len(seg)), np.linspace(0, 1, len(rr)), rr)
        R = max(r0, r1) + 1
        xs, ys = self._region(seg[:, 0].min() - R, seg[:, 1].min() - R, seg[:, 0].max() + R, seg[:, 1].max() + R)
        h, w = len(ys), len(xs)
        if h == 0 or w == 0:
            return
        best = np.full((h, w), 1e9); bdx = np.zeros((h, w)); bdy = np.zeros((h, w)); br = np.ones((h, w))
        bx0, by0 = int(xs[0]), int(ys[0])
        for (sx, sy), r in zip(seg, rads):
            r_ = max(r, 0.3)
            j0 = max(0, int(math.floor(sx - r_ - 1)) - bx0); j1 = min(w, int(math.ceil(sx + r_ + 1)) - bx0 + 1)
            i0 = max(0, int(math.floor(sy - r_ - 1)) - by0); i1 = min(h, int(math.ceil(sy + r_ + 1)) - by0 + 1)
            if j0 >= j1 or i0 >= i1:
                continue
            dx = (xs[j0:j1] + 0.5 - sx)[None, :]
            dy = (ys[i0:i1] + 0.5 - sy)[:, None]
            d = np.sqrt(dx * dx + dy * dy) / r_
            sb = best[i0:i1, j0:j1]
            upd = d < sb
            if not upd.any():
                continue
            sb[upd] = d[upd]
            bdx[i0:i1, j0:j1][upd] = np.broadcast_to(dx, d.shape)[upd]
            bdy[i0:i1, j0:j1][upd] = np.broadcast_to(dy, d.shape)[upd]
            br[i0:i1, j0:j1][upd] = r
        m = best < 1.0
        nx = bdx / np.maximum(br, 0.3); ny = bdy / np.maximum(br, 0.3)
        nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0.05, 1))
        nrm = np.stack([nx, ny, nz], -1)
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        self._put(xs, ys, m, nrm, z + (1 - best) * 0.5, mat, hgt=(1 - best) * br)


class _Dual:
    """HD şekil tuvali: ince tuval (koordinatlar x HD) + mantıksal eş tuval.
    Her çağrı önce ince tuvale (rng durumu kaydedilip geri yüklenerek), sonra mantıksal tuvale
    gider; böylece rng tam tabandaki gibi tüketilir ve mantıksal kaya maskesi (kırıntı
    döngüsünün kararları için) birebir elde edilir."""

    def __init__(self, k):
        self.k = k
        self.f = _FCanvas(S * k, S * k, wrap=True)
        self.l = ShapeCanvas(S, S, wrap=True)

    @property
    def n(self):
        return self.f.n

    @property
    def hgt(self):
        return self.f.hgt

    def add_mat(self, *a, **kw):
        self.l.add_mat(*a, **kw)
        return self.f.add_mat(*a, **kw)

    def _twice(self, rng, ff, lf):
        st = rng.bit_generator.state if rng is not None else None
        ff()
        if rng is not None:
            rng.bit_generator.state = st
        lf()

    def blob(self, cx, cy, rx, ry, mat, rng=None, **kw):
        k = self.k
        self._twice(rng, lambda: self.f.blob(cx * k, cy * k, rx * k, ry * k, mat, rng=rng, **kw),
                    lambda: self.l.blob(cx, cy, rx, ry, mat, rng=rng, **kw))

    def tube(self, pts, r0, r1, mat, z=0.0):
        k = self.k
        self.f.tube([(x * k, y * k) for x, y in pts], r0 * k, r1 * k, mat, z=z)
        self.l.tube(pts, r0, r1, mat, z=z)

    def poly(self, pts, mat, z=0.0, normal=(0, 0, 1)):
        k = self.k
        self.f.poly([(x * k, y * k) for x, y in pts], mat, z=z, normal=normal)
        self.l.poly(pts, mat, z=z, normal=normal)

    def shade(self, **kw):
        return self.f.shade(**kw)


def _wrap_poly(pts, hw, F, extra=0):
    """Sarmalı doku için: çoklu çizgiye hw (mantıksal) uzaklıktaki ince pikseller.
    Döner (m, i0, j0): yerel pencere maskesi (alta extra satır pay) ve köşesi (sarılmamış)."""
    n = HD
    p = np.asarray(pts, float).reshape(-1, 2)
    i0 = int(math.floor((p[:, 1].min() - hw) * n)) - 1; i1 = int(math.ceil((p[:, 1].max() + hw) * n)) + 1 + extra
    j0 = int(math.floor((p[:, 0].min() - hw) * n)) - 1; j1 = int(math.ceil((p[:, 0].max() + hw) * n)) + 1
    Y = ((np.arange(i0, i1) + 0.5) / n)[:, None]
    X = ((np.arange(j0, j1) + 0.5) / n)[None, :]
    d2 = np.full((i1 - i0, j1 - j0), np.inf)
    if len(p) == 1:
        d2 = (X - p[0, 0]) ** 2 + (Y - p[0, 1]) ** 2
    for a, b in zip(p[:-1], p[1:]):
        ab = b - a
        L2 = ab @ ab + 1e-12
        t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1]) / L2, 0, 1)
        d2 = np.minimum(d2, (X - a[0] - t * ab[0]) ** 2 + (Y - a[1] - t * ab[1]) ** 2)
    return d2 <= hw * hw, i0, j0


def _thick_outline(cv, rgba, w):
    """ShapeCanvas.shade'in 1 piksellik kontur/kenar ışığını w ince piksele kalınlaştır
    (taban '1 piksel' konturuyla aynı oran; şekiller tabandaki gibi okunur)."""
    empty = cv.mat < 0
    sh_o = [(-k, 0) for k in range(1, w + 1)] + [(0, k) for k in range(1, w + 1)]
    sh_r = [(k, 0) for k in range(1, w + 1)] + [(0, -k) for k in range(1, w + 1)]
    e = _dil(empty, sh_o) & ~empty
    rim = _dil(empty, sh_r) & ~empty & ~e
    oc = np.zeros((len(cv.mats), 3)); has_o = np.zeros(len(cv.mats), bool)
    rc = np.zeros((len(cv.mats), 3))
    for i, M in enumerate(cv.mats):
        if M['outline'] is not None:
            oc[i] = M['outline']; has_o[i] = True
        rc[i] = np.minimum(1, M['ramp'][-1] * 1.04)
    iy, ix = np.nonzero(rim)
    rgba[iy, ix, :3] = rc[cv.mat[iy, ix]]
    iy, ix = np.nonzero(e)
    mi = cv.mat[iy, ix]
    ok = has_o[mi]
    rgba[iy[ok], ix[ok], :3] = oc[mi[ok]]


def _clod_hd(rgb, hgt, lvl, Pk, cx, cy, r, sg):
    """Kesek (HD): sağ üstü aydınlık, düzensiz kenarlı topak (biçim yan üreteçten)."""
    n = HD; F = rgb.shape[0]
    base = lvl[int(cy * n) % F, int(cx * n) % F]
    R = r + 0.6
    j0 = int(math.floor((cx - R) * n)); j1 = int(math.ceil((cx + R) * n))
    i0 = int(math.floor((cy - R) * n)); i1 = int(math.ceil((cy + R) * n))
    X = ((np.arange(j0, j1) + 0.5) / n - cx)[None, :]
    Y = ((np.arange(i0, i1) + 0.5) / n - cy)[:, None]
    ph = sg.uniform(0, TAU, 3)
    ang = np.arctan2(Y * 1.14, X)
    rr = r * (1 + 0.16 * np.sin(2 * ang + ph[0]) + 0.1 * np.sin(3 * ang + ph[1]) + 0.06 * np.sin(5 * ang + ph[2]))
    d2 = (X * X + Y * Y * 1.3) * (r / rr) ** 2
    m = d2 <= r * r
    edge = d2 > (r - _lw()) ** 2
    v = base + np.where(edge & (X - Y > 0.5), 1, np.where(edge & (X - Y < -1.5), -1, 0))
    iy, ix = np.nonzero(m)
    Yi = (iy + i0) % F; Xi = (ix + j0) % F
    rgb[Yi, Xi] = Pk[np.clip(v[iy, ix], 0, 5)]
    hgt[Yi, Xi] = 1.0 + np.sqrt(r * r - d2[iy, ix]) * 0.4


def _crack_hd(rgb, hgt, pts):
    """Çatlak (HD): koyu oyuk + alt duvarında ışık, ince ızgarada düzgün çizgi."""
    if not pts:
        return
    F = rgb.shape[0]
    w = _lwf()
    m, i0, j0 = _wrap_poly(pts, _lw() * 0.5, F, extra=w)
    lip = np.zeros_like(m)
    for k in range(1, w + 1):
        lip[k:] |= m[:-k]
    lip &= ~m
    dark = SOIL[0] * 0.85
    iy, ix = np.nonzero(m)
    Yi = (iy + i0) % F; Xi = (ix + j0) % F
    rgb[Yi, Xi] = dark
    hgt[Yi, Xi] -= 1.5
    iy, ix = np.nonzero(lip)
    Yi = (iy + i0) % F; Xi = (ix + j0) % F
    c = rgb[Yi, Xi]
    ok = (c != dark).any(-1)
    rgb[Yi[ok], Xi[ok]] = np.minimum(1, c[ok] * 1.18 + 0.02)


def _veins_seg(veins, x0, y0, x1, y1, w):
    """Lav damarı adımı (HD): (x0,y0)→(x1,y1) parçasına sürekli damga, ince ızgarada.
    Uzaklıktan 0.1 düşülür: tabandaki piksel nicelemesinin (merkez piksel d=0) yaklaşık eşdeğeri."""
    n = HD; F = veins.shape[0]
    R = w + 3.5
    j0 = int(math.floor((min(x0, x1) - R) * n)); j1 = int(math.ceil((max(x0, x1) + R) * n))
    i0 = int(math.floor((min(y0, y1) - R) * n)); i1 = int(math.ceil((max(y0, y1) + R) * n))
    X = ((np.arange(j0, j1) + 0.5) / n)[None, :]
    Y = ((np.arange(i0, i1) + 0.5) / n)[:, None]
    abx, aby = x1 - x0, y1 - y0
    t = np.clip(((X - x0) * abx + (Y - y0) * aby) / (abx * abx + aby * aby + 1e-12), 0, 1)
    d = np.maximum(0.0, np.sqrt((X - x0 - t * abx) ** 2 + (Y - y0 - t * aby) ** 2) - 0.1)
    val = np.where(d > w, np.clip(1 - (d - w) / 3.5, 0, 1), 1.0 + (w - d))
    I = np.arange(i0, i1) % F; J = np.arange(j0, j1) % F
    sub = veins[np.ix_(I, J)]
    veins[np.ix_(I, J)] = np.maximum(sub, val)


# ------------------------------------------------------------------ toprak dokusu
def soil_texture(seed=7):
    """(rgb, normal_rgba, emis_rgb | None) — (S*HD)², her iki yönde dikişsiz.

    HD > 1: aynı tohum → aynı resim, HD kat ince ızgarada. Alanlar aynı gürültü kafeslerinden ince
    örneklenir; rastgele kararlar (kesek/çakıl türü, kırıntılar) mantıksal alanlardan verilir."""
    st = STYLE
    n = HD
    F = S * n
    rng = np.random.default_rng(seed)
    pr = random.Random(seed)
    sg = _side_rng(seed)
    if n == 1:
        yy, xx = np.mgrid[0:S, 0:S]
    else:
        yy, xx = np.mgrid[0:F, 0:F] / n
    b = bayer(F, F)
    # ---- katmanlar (strata): dalgalı, kalınlığı değişen bantlar
    if n == 1:
        warp = fbm(S, S, [384, 192, 96, 48], rng)
        warp2 = fbm(S, S, [32, 16, 8], rng)
    else:
        warp_l, warp = _fbm2(S, [384, 192, 96, 48], rng)
        warp2_l, warp2 = _fbm2(S, [32, 16, 8], rng)
    phase = (yy / 384.0 + (warp - 0.5) * 0.4 + (warp2 - 0.5) * 0.02) % 1.0   # 384 px'lik katman dizisi, S'de tam sayı kez tekrarlar
    kinds = [k for k, _ in st['bands']]
    th = np.array([t for _, t in st['bands']], float)
    cum = np.cumsum(th) / th.sum()
    start = np.concatenate([[0.0], cum[:-1]])
    bi = np.clip(np.searchsorted(cum, phase, side='right'), 0, len(kinds) - 1)
    t_in = (phase - start[bi]) / (th[bi] / th.sum())
    if n == 1:
        bil = bi
    else:
        # rastgele kararlar için mantıksal bant haritası (taban ile birebir)
        yl = np.mgrid[0:S, 0:S][0]
        phase_l = (yl / 384.0 + (warp_l - 0.5) * 0.4 + (warp2_l - 0.5) * 0.02) % 1.0
        bil = np.clip(np.searchsorted(cum, phase_l, side='right'), 0, len(kinds) - 1)
        del yl, phase_l, warp_l, warp2_l
    # ---- tane: küçük kümeler (2-3 px) + ince kum
    if n == 1:
        grain = fbm(S, S, [24, 12, 6, 3, 2], rng, gain=0.72)
    else:
        grain = _fbm2(S, [24, 12, 6, 3, 2], rng, gain=0.72)[1]
    fine = rng.random((S, S))
    if n > 1:
        fine = sg.random((F, F))      # ince kum ince pikselde
    val = 0.5 + (grain - 0.5) * 1.5 + (fine - 0.5) * 0.10
    val += (0.45 - t_in) * 0.22               # bandın üstü ışık alır
    # katman sınırı: ince koyu dikiş + altında açık dudak
    if n == 1:
        bnd = bi != roll(bi, 1, 0)
        val[bnd] -= 0.42
        val[roll(bnd, 1, 0) & ~bnd] += 0.14
    else:
        w_ = _lwf()
        bnd = _dil(bi != roll(bi, 1, 0), [(k, 0) for k in range(w_)])
        val[bnd] -= 0.42
        val[_dil(bnd, [(k, 0) for k in range(1, w_ + 1)]) & ~bnd] += 0.14
    # kil ve kumda ince laminasyon çizgileri
    lam_kind = np.isin(np.array(kinds)[bi], ['clay', 'sand'])
    lam = ((phase * 384 / 5.0 + warp2 * 1.6) % 1.0) < 0.2
    val[lam & lam_kind] -= 0.16
    # kumda çapraz katmanlanma (eğik ince çizgiler)
    sand = np.array(kinds)[bi] == 'sand'
    cross = (((xx * 0.42 + yy) / 7.0 + warp * 4) % 1.0) < 0.12
    val[sand & cross & (fine > 0.3)] -= 0.1
    lvl = np.clip(np.floor(val * 4.0 + 0.9 + (b - 0.5) * 0.85), 0, 5).astype(int)
    del val
    rgb = np.zeros((F, F, 3))
    pals = {'soil': SOIL, 'clay': CLAY, 'humus': HUMUS, 'gravel': SOIL,
            'sand': np.vstack([SOIL[1:], np.minimum(1, SOIL[-1] * 1.1 + 0.03)])}
    for i, k in enumerate(kinds):
        m = bi == i
        Pk = pals.get(k, SOIL)
        rgb[m] = Pk[lvl[m]]
    hgt = (grain - 0.5) * 1.6
    # mikro tane: tek tük bir ton açık/koyu pikseller ve 2'li kırıntılar (gevrek doku)
    mic = rng.random((S, S))
    if n > 1:
        mic = sg.random((F, F))
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
        kk = kinds[bil[int(cy) % S, int(cx) % S]]
        if kk not in ('soil', 'humus', 'gravel'):
            continue
        r = pr.choice([1.3, 1.6, 2.0, 2.4])
        if n > 1:
            _clod_hd(rgb, hgt, lvl, pals[kk], cx, cy, r, sg)
            continue
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
        cpts = []
        for _k in range(pr.randint(8, 26)):
            a += pr.uniform(-0.55, 0.55)
            x += math.cos(a); y += math.sin(a)
            if n > 1:
                cpts.append((x, y))
            else:
                X, Y = int(x) % S, int(y) % S
                rgb[Y, X] = SOIL[0] * 0.85
                hgt[Y, X] -= 1.5
                Y2 = (Y + 1) % S
                if (rgb[Y2, X] != SOIL[0] * 0.85).any():
                    rgb[Y2, X] = np.minimum(1, rgb[Y2, X] * 1.18 + 0.02)
            if pr.random() < 0.08:
                a += pr.choice([-1, 1]) * 1.1
        if n > 1:
            _crack_hd(rgb, hgt, cpts)
    # ---- şekiller: kayalar, çakıllar, kökler, kemikler, kristaller
    cv = ShapeCanvas(S, S, wrap=True) if n == 1 else _Dual(n)
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
        ys, xs = np.nonzero(np.isin(bil, gi))
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
        nseg = pr.randint(10, 26)
        for _k in range(nseg):
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
        cmats = {}
        for ci in range(int(18 * AF)):
            h_, s_, v_ = cols[ci % 2]
            if n > 1 and ci % 2 in cmats:
                cm = cmats[ci % 2]       # HD: özdeş malzemeyi paylaş (çıktı aynı, shade çok daha hızlı)
            else:
                cm = cmats[ci % 2] = cv.add_mat(hramp(h_, s_, v_, n=5, lo=0.35, hi=1.15), outline=hexrgb('#06100c'), spec=0.9,
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
    rmask_l = rmask if n == 1 else cv.l.mat >= 0      # kırıntı kararları mantıksal maskeden
    if n > 1:
        _thick_outline(cv.f, rocks, _lwf())
    # gömülme: taşların sol altına düşen gölge + çevre kararması
    if n == 1:
        cast = (roll(rmask, 1, -1) | roll(rmask, 2, -2) | roll(rmask, 2, -1)) & ~rmask
        ao = (roll(rmask, 1, 0) | roll(rmask, -1, 0) | roll(rmask, 0, 1) | roll(rmask, 0, -1)) & ~rmask & ~cast
    else:
        cast = _dil(rmask, [(dy, -dx) for dy in range(1, 2 * n + 1) for dx in range((dy + 1) // 2, dy + 1)]) & ~rmask
        w_ = _lwf()
        ao = _dil(rmask, [s for k in range(1, w_ + 1) for s in ((k, 0), (-k, 0), (0, k), (0, -k))]) & ~rmask & ~cast
    rgb[cast] *= 0.58
    rgb[ao] *= 0.8
    del cast, ao
    rgb[rmask] = rocks[rmask, :3]
    del rocks
    hgt[rmask] += (cv.hgt[rmask] if n == 1 else cv.hgt[rmask] / n) + 1.0
    if extra == 'crystal' or remis.max() > 0:
        emis = remis * 0.55
        # kristallerin çevresi hafifçe aydınlanır
        em_m = remis.max(axis=2) > 0
        if n == 1:
            halo = (roll(em_m, 1, 0) | roll(em_m, -1, 0) | roll(em_m, 0, 1) | roll(em_m, 0, -1) | roll(em_m, 2, 0) | roll(em_m, 0, -2)) & ~em_m & ~rmask
        else:
            sh = [s for k in range(1, n + 1) for s in ((k, 0), (-k, 0), (0, k), (0, -k))]
            sh += [s for k in range(n + 1, 2 * n + 1) for s in ((k, 0), (0, -k))]
            halo = _dil(em_m, sh) & ~em_m & ~rmask
        rgb[halo] = rgb[halo] * 0.7 + np.array(st['glow'] or [0.4, 1, 0.8]) * 0.12
    del remis
    if extra == 'lava':
        emis = np.zeros((F, F, 3))
        veins = np.zeros((F, F))
        for _ in range(int(5 * AF)):
            x, y = pr.uniform(0, S), pr.uniform(0, S)
            a = pr.uniform(0, TAU)
            stack = [(x, y, a, pr.uniform(0.8, 1.5), pr.randint(25, 60))]
            while stack:
                x, y, a, w, cnt = stack.pop()
                for _k in range(cnt):
                    a += pr.uniform(-0.45, 0.45)
                    px0, py0 = x, y
                    x += math.cos(a); y += math.sin(a)
                    if n > 1:
                        _veins_seg(veins, px0, py0, x, y, w)
                    else:
                        R = int(math.ceil(w)) + 3
                        for dy in range(-R, R + 1):
                            for dx in range(-R, R + 1):
                                d = math.hypot(dx, dy)
                                X, Y = int(x + dx) % S, int(y + dy) % S
                                veins[Y, X] = max(veins[Y, X], np.clip(1 - (d - w) / 3.5, 0, 1) if d > w else 1.0 + (w - d))
                    w = max(0.5, w * 0.985)
                    if pr.random() < 0.04 and len(stack) < 6:
                        stack.append((x, y, a + pr.choice([-1, 1]) * pr.uniform(0.6, 1.2), w * 0.7, int(cnt * 0.5)))
        inside = veins >= 1.0
        hot = veins >= 1.6
        halo = (veins > 0) & ~inside
        # ısı halesi: toprak koyu kızıla döner (basamaklı)
        hk_ = np.clip(np.floor(veins * 3 + (b - 0.5)) / 3, 0, 1)
        rgb[halo] = rgb[halo] * (1 - hk_[halo, None] * 0.5) + hexrgb('#5a1206') * hk_[halo, None] * 0.5
        rgb[inside] = hexrgb('#ff7a1a')
        rgb[hot] = hexrgb('#ffd060')
        if n == 1:
            edge_v = inside & ~(roll(inside, 1, 0) & roll(inside, -1, 0) & roll(inside, 0, 1) & roll(inside, 0, -1))
        else:
            core = inside.copy()
            for k in range(1, _lwf() + 1):
                core &= roll(inside, k, 0) & roll(inside, -k, 0) & roll(inside, 0, k) & roll(inside, 0, -k)
            edge_v = inside & ~core
        rgb[edge_v & ~hot] = hexrgb('#c8340c')
        emis[inside] = hexrgb('#ff5a10') * 0.3
        emis[hot] = hexrgb('#ffb040') * 0.5
        emis[halo] = hexrgb('#ff3a08') * (hk_[halo, None] * 0.06)
        hgt[inside] -= 1.0
        # obsidiyen kırıkları: keskin, parlak
    # ince kırıntılar / pırıltı
    ds = max(1, n // 2)
    for _ in range(int(260 * AF)):
        x, y = pr.randrange(S), pr.randrange(S)
        if rmask_l[y, x]:
            continue
        c = SPECK[pr.choice([0, 0, 1, 2])]
        if n == 1:
            rgb[y, x] = c
            if pr.random() < 0.4:
                rgb[(y + 1) % S, x] = rgb[(y + 1) % S, x] * 0.7
            continue
        # HD: mantıksal pikselin içinde rastgele konumlu küçük kırıntı (kaya üstüne düşmez)
        oy, ox = sg.integers(0, n - ds + 1, 2)
        Y0, X0 = y * n + int(oy), x * n + int(ox)
        sub = rgb[Y0:Y0 + ds, X0:X0 + ds]
        sub[~rmask[Y0:Y0 + ds, X0:X0 + ds]] = c
        if pr.random() < 0.4:
            Yb = (Y0 + ds + np.arange(ds)) % F
            rgb[np.ix_(Yb, np.arange(X0, X0 + ds))] *= 0.7
    nrm = normals_from_height(hgt if n == 1 else hgt * n, 0.55)
    del hgt
    nrm[rmask] = cv.n[rmask]
    return rgb, normal_rgba(nrm), emis


# ------------------------------------------------------------------ kenar profilleri (P'de periyodik)
def _pn(seed, cells):
    rng = np.random.default_rng(seed)
    return hk.profile(P, cells, rng)


def _pn_eval(seed, cells, gain=0.5):
    """_pn'nin sürekli eşi: aynı kafes ve aynı normalleştirme, kesirli u'da (HD kenarları)."""
    rng = np.random.default_rng(seed)
    lats = []
    for c in cells:
        gw = max(1, int(round(P / c)))
        gh = max(1, int(round(1 / max(1.0, c))))
        g = rng.random((gh + 1, gw + 1))
        g[:, gw] = g[:, 0]
        lats.append((g[0].copy(), gw))

    def raw(u):
        u = np.mod(u, P)
        out = 0.0; tot = 0.0; amp = 1.0
        for g0, gw in lats:
            xs = u * gw / P
            x0 = np.minimum(np.floor(xs).astype(int), gw - 1)
            fx = xs - x0
            fx = fx * fx * (3 - 2 * fx)
            out = out + (g0[x0] * (1 - fx) + g0[x0 + 1] * fx) * amp
            tot += amp; amp *= gain
        return out / tot
    b = raw(np.arange(P, dtype=float))
    lo, hi = b.min(), b.max()
    return lambda u: (raw(u) - lo) / (hi - lo + 1e-9)


def _prof_fields(u, n1, n2, n3, n4, n5, names=None):
    cap = STYLE['cap']
    d = {}
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


def _profiles():
    u = np.arange(P)
    n1, n2, n3, n4, n5 = _pn(11, [27, 9, 3]), _pn(12, [36, 12, 4]), _pn(13, [27, 9]), _pn(14, [18, 6, 3]), _pn(15, [12, 4])
    PR = _prof_fields(u, n1, n2, n3, n4, n5)
    if HD > 1:
        # HD: profiller kesirli u'da sürekli değerlendirilir (tam sayılarda mantıksal dizilerle aynı)
        ev = [_pn_eval(11, [27, 9, 3]), _pn_eval(12, [36, 12, 4]), _pn_eval(13, [27, 9]), _pn_eval(14, [18, 6, 3]), _pn_eval(15, [12, 4])]
        PR['f'] = lambda name, uu: _prof_fields(uu, *(e(uu) for e in ev))[name]
    return PR


def _blade_color(lean, t, tip):
    if tip:
        return GRASS[6] if lean >= 0 else GRASS[5]
    return GRASS[min(6, 2 + int(t * 3.4) + (1 if lean > 0 else 0))]



_B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
# Ortam kapanması halkaları (mantıksal piksel uzaklığı, gölge olasılığı): düz gölge bandının (1-4 px) ötesinde
# toprak, düzenli (Bayer) bir desenle gölge anahtarına geçer; gölge yüzü / çıkıntı altı içeri doğru yumuşakça kararır.
# Çıkıntı altı (tavan) daha geniş ve koyu: üstteki kütle ışığı keser.
AO_SIDE = ((5, 0.5), (6, 0.5), (7, 0.25), (8, 0.25), (9, 0.125))
AO_CEIL = ((5, 0.75), (6, 0.5), (7, 0.5), (8, 0.375), (9, 0.25), (10, 0.25), (11, 0.125), (12, 0.125))


def _ao_dither(kind, air, n, yi, xi):
    """kind==1 (toprak) piksellerini sol/alt havaya uzaklığa göre titreşimli gölgeye (2) çevirir.
    n: HD çarpanı (kayma ince pikselde), yi/xi: mantıksal tam sayı koordinatlar (desen karo sınırında dikişsiz).
    Dizi dışı hava SAYILMAZ (dolgu payını aşan halkalar kapalı karoda ızgara çizgisi bırakıyordu)."""
    def air_at(dy, dx):
        return hk.shift_nw(air, -dy, -dx, False)
    thr = _B4[yi % 4, xi % 4]
    for k, p in AO_SIDE:
        ring = air_at(0, -k * n) | air_at(k * n, -k * n)
        kind[(kind == 1) & ring & (thr < p)] = 2
    for k, p in AO_CEIL:
        kind[(kind == 1) & air_at(k * n, 0) & (thr < p)] = 2


def ground_tile(mask, var, PR):
    if HD > 1:
        return _ground_tile_hd(mask, var, PR)
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
    _ao_dither(kind, air, 1, ly, lx)
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


def _stone_hd(fg, cx, cy, rx, ry, mi, snow=False):
    """_stone'un HD eşi: aynı merkez (taban pikseli), ince ızgarada elips. Döner (iy, ix, renk)."""
    h, s, v = ROCK[mi % len(ROCK)]
    rp = hramp(h, s, v, n=6, lo=0.34, hi=1.35)
    R = int(math.ceil(max(rx, ry))) + 1
    ccx, ccy = math.floor(cx), math.floor(cy)
    i0, i1 = fg.span(ccy - R, ccy + R)
    j0, j1 = fg.span(ccx - R, ccx + R)
    X, Y = np.meshgrid(fg.g[j0:j1] - ccx, fg.g[i0:i1] - ccy)
    nx, ny = X / rx, Y / ry
    q = nx * nx + ny * ny
    lam = (nx * LIGHT[0] + ny * LIGHT[1]) * 0.6 + np.sqrt(np.clip(1 - q, 0, None)) * LIGHT[2] * 0.8
    c = rp[np.clip(1.5 + lam * 4.2, 1, 5).astype(int)]
    ol = max(0.55, (1 - _lw() / max(rx, ry)) ** 2)
    c[(q > ol) & (nx - ny < -0.6)] = rp[0]
    if snow:
        sm = ny < -0.45
        c[sm] = np.where((nx[sm] > -0.2)[:, None], GRASS[6], GRASS[5])
    iy, ix = np.nonzero(q <= 1.0)
    return iy + i0, ix + j0, c[iy, ix]


def _ground_tile_hd(mask, var, PR):
    """ground_tile'ın HD yeniden çizimi: aynı profiller (sürekli), aynı karma/rastgele kararlar,
    HD kat ince ızgara. Kenarlar düzgün eğri, '1 piksellik' bantlar _lw kalınlığında."""
    n = HD
    up, rt, dn, lf = bool(mask & 1), bool(mask & 2), bool(mask & 4), bool(mask & 8)
    cap = STYLE['cap']
    off = var * TS
    PADW = 8
    fg = _FG(TS, PADW)
    NF = fg.N
    LY, LX = np.meshgrid(fg.g, fg.g, indexing='ij')
    pf = PR['f']
    U = off + LX
    V = off + LY
    surf, th, bot = pf('surf', U), pf('th', U), pf('bot', U)
    sideL, sideR = pf('side', V), pf('side', V + 53)
    lw = _lw()
    solid = np.ones((NF, NF), bool)
    # tile dışı: açık yönlerde hava (taban: tam sayı satırda floor → burada ortalama eşdeğeri)
    if up:
        solid &= LY >= (surf if cap == 'snow' else surf + th * 0.5 - 1)
    if dn:
        solid &= LY <= TS - 1 - bot
    if lf:
        solid &= LX >= sideL
    if rt:
        solid &= LX <= TS - 1 - sideR
    # dış köşe yuvarlatma
    for cx, cy, on, sx, sy in ((0, 0, up and lf, 1, 1), (TS - 1, 0, up and rt, -1, 1), (0, TS - 1, dn and lf, 1, -1), (TS - 1, TS - 1, dn and rt, -1, -1)):
        if not on:
            continue
        rc = PR['corner'][(off + cx) % P]
        ccx, ccy = cx + sx * rc, cy + sy * rc
        inq = ((LX - ccx) * sx < 0) & ((LY - ccy) * sy < 0)
        solid &= ~(inq & ((LX - ccx) ** 2 + (LY - ccy) ** 2 > rc * rc))
    kind = np.zeros((NF, NF), int)
    kind[solid] = 1
    air = ~solid

    def air_at(dy, dx):
        return hk.shift_nw(air, -dy, -dx, True)
    shade = np.zeros((NF, NF), bool)
    for k in range(1, 4 * n + 1):
        shade |= air_at(0, -k) | air_at(k, 0) | air_at(k, -k)
    lit = np.zeros((NF, NF), bool)
    for k in range(1, 3 * n + 1):
        lit |= air_at(0, k)
    edge = np.zeros((NF, NF), bool)
    for k in range(1, _lwf() + 1):
        edge |= air_at(0, -k) | air_at(k, 0) | air_at(k, -k)
    kind[solid & lit] = 3
    kind[solid & shade] = 2
    kind[solid & edge] = 4
    col = np.zeros((NF, NF, 3))
    rng = random.Random(mask * 131 + var * 7 + 3)
    XI = np.floor(LX + 0.5).astype(int)
    YI = np.floor(LY + 0.5).astype(int)
    _ao_dither(kind, air, n, np.floor(LY).astype(int), np.floor(LX).astype(int))
    UU = (off + XI) % P
    VV = (off + YI) % P
    colc = np.abs(LX - XI) < lw * 0.5          # mantıksal sütunun ortasındaki ince şerit

    def paint(m, c, k=5):
        kind[m] = k
        if c is not None:
            col[m] = c

    def paint_px(iy, ix, c, k=5, where=None):
        if where is not None:
            ok = where[iy, ix]
            iy, ix = iy[ok], ix[ok]
            if c is not None and np.ndim(c) == 2:
                c = c[ok]
        kind[iy, ix] = k
        if c is not None:
            col[iy, ix] = c

    # ---- yüzey kapağı
    if up:
        allow = 1.6 if cap == 'snow' else 0.0
        inside = np.ones((NF, NF), bool)
        if lf:
            inside &= LX >= sideL - allow
        if rt:
            inside &= LX <= TS - 1 - sideR + allow
        XR = (LX >= -2.5) & (LX < TS + 1.5)
        top = surf - 1.0
        bt = surf + th
        capm = XR & inside & (LY >= top) & (LY < bt)
        t = (LY - surf) / np.maximum(1.0, th)
        toprow = (LY >= top) & (LY < top + lw)
        botrow = (LY >= bt - lw) & (LY < bt)
        row2 = (LY >= top + 1) & (LY < top + 1 + lw)
        dot = XR & colc
        bv = bayer(NF, NF)

        def H(salt):
            return _htab(salt)[UU]

        def hang(sel, L, cfn):
            kk = np.floor(LY - bt)
            m = sel & dot & (LY >= bt) & (kk < L) & (kind >= 1) & (kind <= 4)
            paint(m, cfn(kk)[m])

        if cap == 'snow':
            I = np.where(t < 0.3, np.where(bv < 0.5 - t, 6, 5),
                         np.where(t < 0.65, np.where(bv < 0.75 - t, 5, 4),
                                  np.where(~botrow, np.where(bv < 0.9 - t, 4, 3), 2)))
            I = np.where(toprow, 6, I)
            if lf:
                I = np.where(LX < sideL + 2, np.where(toprow, 5, 3), I)
            paint(capm, GRASS[I[capm]])
            paint(dot & toprow & (H(41) < 0.12), SPECK[0])
        elif cap == 'moss':
            dsl = pf('surf', U + 1) - pf('surf', U - 1)
            cm = capm & ~((kind == 0) & (LY > surf + 2))
            lv = 5 - t * 4.2 + np.where(dsl < -0.2, 0.8, np.where(dsl > 0.2, -0.8, 0.0)) + (bv - 0.5) * 1.1
            I = np.where(botrow, 1, np.clip(lv, 1, 6).astype(int))
            paint(cm, GRASS[I[cm]])
            paint(dot & row2 & (H(42) < 0.07), SPECK[0])
            paint(dot & toprow & (H(43) < 0.03), None, 6)
            hang(H(44) < 0.2, (1 + H(45) * 4).astype(int), lambda kk: np.where((kk >= 1)[..., None], GRASS[1], GRASS[2]))
        elif cap == 'ash':
            ash = ASH_PAL()
            I = np.where(botrow, 0, np.clip(4.6 - t * 4.2 + (bv - 0.5) * 1.2, 0, 5).astype(int))
            paint(capm, ash[I[capm]])
            h1 = H(51)
            paint(dot & row2 & (h1 < 0.06), None, 6)
            paint(dot & toprow & (h1 >= 0.06) & (h1 < 0.14), GRASS[4])
            paint(dot & row2 & (h1 >= 0.14) & (h1 < 0.24), ash[0])
        else:
            lv = 4.8 - t * 4.0 + (bv - 0.5) * 1.3
            lv = np.where(((XI + (H(62) * 3).astype(int)) % 5 == 0) & colc, lv - 1, lv)    # ot sapı çizgileri
            I = np.where(toprow, np.where(H(61) < 0.6, 5, 6), np.clip(lv, 1, 5).astype(int))
            C = GRASS[I]
            C[botrow] = GRASS[1] if cap == 'grass' else SOIL[1]
            paint(capm, C[capm])
            hang(H(63) < (0.26 if cap == 'grass' else 0.14), (1 + H(64) * 5).astype(int),
                 lambda kk: np.where((kk < 1)[..., None], GRASS[1], ROOT[1 + (kk.astype(int) % 2)]))
            if cap == 'dry':
                paint(dot & toprow & (H(65) < 0.08), SPECK[0])
        # kapağın altında gölge bandı
        kind[XR & (LY >= bt) & (LY < bt + 2) & ((kind == 1) | (kind == 3))] = 2
        # yaprak/ot tutamları (ince ızgarada kıvrık yapraklar)
        if cap in ('grass', 'dry', 'moss'):
            okb = inside & (LY >= -0.5)
            pt = 0.3 if cap == 'grass' else (0.22 if cap == 'dry' else 0.1)
            for uu0 in range(off - 6, off + TS + 6):
                uu = uu0 % P
                if _hash(uu, 71) >= pt:
                    continue
                x0 = uu0 - off
                base = int(math.floor(PR['surf'][uu])) + 1
                yb = PR['surf'][uu] - 0.5
                nbl = 2 + int(_hash(uu, 72) * 4)
                for j in range(nbl):
                    lean = (j - (nbl - 1) / 2) * (0.5 + _hash(uu, 73 + j) * 0.6)
                    hh = 2 + int(_hash(uu, 80 + j) * (base + 3))
                    ks = _lin(0, hh - 1)
                    tt = ks / max(1, hh - 1)
                    kr = np.floor(ks + 0.5).astype(int)
                    if cap == 'moss':
                        cols = np.where((kr < hh - 1)[:, None], GRASS[4], SPECK[0])
                    else:
                        cols = np.array([_blade_color(lean, k_ / max(1, hh - 1), k_ == hh - 1) for k_ in kr])
                    iy, ix, kk, _, _ = fg.stroke(np.stack([x0 + lean * tt * tt * 2.2, yb - ks], -1), 0.5 * (1.1 - 0.55 * tt))
                    paint_px(iy, ix, cols[kk], where=okb)
        # yüzey taşları (kuru bozkır / kül / kar): toprağa yarı gömülü
        if cap in ('dry', 'ash', 'snow'):
            for uu0 in range(off - 6, off + TS + 6):
                uu = uu0 % P
                if _hash(uu, 91) >= 0.035:
                    continue
                x0 = uu0 - off
                r = 1.6 + _hash(uu, 92) * 1.8
                y0 = PR['surf'][uu] + PR['th'][uu] * 0.4
                iy, ix, cc = _stone_hd(fg, x0, y0, r, r * 0.75, int(_hash(uu, 93) * 4), snow=(cap == 'snow'))
                paint_px(iy, ix, cc)
    # ---- tavan: sarkanlar (sütun sütun, tabandaki sırayla)
    if dn:
        ceil = STYLE['ceil']
        Bg = TS - 1 - bot
        for x in range(TS):
            uu = (off + x) % P
            hsh = _hash(uu, 101)
            h2 = _hash(uu, 102)
            j0, j1 = fg.span(x - 0.5, x + 1.5)
            Xs = LX[:, j0:j1]; Ys = LY[:, j0:j1]; Bs = Bg[:, j0:j1]
            Ks = kind[:, j0:j1]; Cs = col[:, j0:j1]
            dxc = Xs - x
            k2 = Ys - (Bs - 1)                    # son katı satırdan aşağı

            def pm(m, c, k=5):
                Ks[m] = k
                if c is not None:
                    Cs[m] = c if np.ndim(c) == 1 else c[m]
            if ceil == 'roots':
                if hsh < 0.18:
                    L = 2 + int(h2 * 6)
                    kk = Ys - Bs
                    m = (kk >= 0) & (kk < L) & (np.abs(dxc) < lw * 0.5 * (1.1 - 0.5 * kk / L)) & (Ks == 0)
                    pm(m, np.where((kk < L - 1)[..., None], ROOT[2], ROOT[3]))
            elif ceil == 'moss':
                if hsh < 0.45:
                    L = 1 + int(h2 * (5 if hsh < 0.15 else 2))
                    m = (k2 >= 0) & (k2 < L) & (np.abs(dxc) < 0.5 * (1 - 0.55 * k2 / L))
                    pm(m, np.where((k2 < L - 1)[..., None], GRASS[2], GRASS[3]))
                    if hsh < 0.05:
                        pm((k2 >= L) & (k2 < L + lw) & (np.abs(dxc) < lw * 0.5), None, 6)
            elif ceil == 'ice':
                if hsh < 0.22:
                    L = 2 + int(h2 * 6)
                    w = 1 + (1 if _hash(uu, 103) < 0.4 else 0)
                    f = np.clip(1 - k2 / L, 0, 1)
                    cxm = x + (w - 1) * 0.5 * f
                    m = (k2 >= 0) & (k2 < L) & (np.abs(Xs - cxm) < np.maximum(w * 0.5 * f, 0.18))
                    pm(m, np.where((Xs >= x + 0.5)[..., None], GRASS[5], np.where((k2 >= L - 1)[..., None], GRASS[6], GRASS[4])))
                else:
                    pm((Ys >= Bs - lw) & (Ys <= Bs) & (np.abs(dxc) <= 0.5), GRASS[4])
            elif ceil == 'drip':
                if hsh < 0.12:
                    L = 2 + int(h2 * 4)
                    h_, s_, v_ = ROCK[0]
                    rp = hramp(h_, s_, v_, n=6)
                    a_ = 0.4 * L
                    hw_ = np.where(k2 < a_, 1 - 0.5 * k2 / a_, 0.5 * np.clip((L - k2) / (L - a_), 0, 1))
                    hw_ = np.maximum(hw_, 0.18)
                    m = (k2 >= 0) & (k2 < L) & (np.abs(Xs - (x - 0.5 + hw_)) < hw_)
                    pm(m, np.where((Xs >= x + 0.5)[..., None], rp[3], np.where((k2 >= L - 1)[..., None], rp[1], rp[2])))
                    if _hash(uu, 104) < 0.5:
                        pm((k2 >= L) & (k2 < L + lw) & (np.abs(dxc) < lw * 0.5), None, 6)
    # ---- yan yüzlerde çıkıntı taşları / kökler / buz / lav çatlakları (rng tabandaki sırayla)
    side = PR['side']
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
            rx_ = r * rng.uniform(1.0, 1.3)
            ry_ = r * rng.uniform(0.75, 1.0)
            iy, ix, cc = _stone_hd(fg, sx, sy, rx_, ry_, rng.randrange(4), snow=(cap == 'snow'))
            paint_px(iy, ix, cc)
            # taşın sol altına gölge (toprakta)
            ir = int(r); fx_ = math.floor(sx)
            i0, i1 = fg.span(sy + 0.5, sy + ir + 2.5)
            j0, j1 = fg.span(fx_ - ir - 2.5, fx_ + 0.5)
            dxs = LX[i0:i1, j0:j1] - fx_; dys = LY[i0:i1, j0:j1] - sy
            Ks = kind[i0:i1, j0:j1]
            Ks[(dys >= 0.5) & (dys < ir + 2.5) & (dxs >= -ir - 2.5) & (dxs < 0.5) & (dxs * dxs + dys * dys < (r + 1.5) ** 2) & ((Ks == 1) | (Ks == 3))] = 2
        # biyoma göre yan yüz süsü
        if cap == 'grass' and rng.random() < 0.5:
            # yandan çıkan kök
            sy = rng.randint(12, TS - 6)
            vv = (off + sy) % P
            x = int(side[vv]) if s_ == 'l' else int(TS - 1 - side[(vv + 53) % P])
            d = -1 if s_ == 'l' else 1
            K = rng.randint(3, 6)
            ks = _lin(0, K - 1)
            kr = np.floor(ks + 0.5).astype(int)
            iy, ix, kk, _, _ = fg.stroke(np.stack([x + d * ks, sy + ks * 0.5 - 0.25], -1), lw * 0.6 * (1 - 0.35 * ks / max(1, K - 1)))
            paint_px(iy, ix, np.where((kr % 2 == 1)[:, None], ROOT[2], ROOT[1])[kk])
        rows = (YI >= 4) & (YI < TS)
        if cap == 'moss':
            hm = rows & (_htab(7 if s_ == 'l' else 8)[VV] < 0.35)
            if s_ == 'l':
                paint(hm & (LX >= sideL) & (LX < sideL + lw), GRASS[2])
            else:
                paint(hm & (LX <= TS - 1 - sideR) & (LX > TS - 1 - sideR - lw), GRASS[3])
        if cap == 'snow' and s_ == 'r':
            hm = rows & (_htab(9)[VV] < 0.18)
            paint(hm & (LX <= TS - 1 - sideR) & (LX > TS - 1 - sideR - lw), GRASS[5])
        if cap == 'ash' and rng.random() < 0.6:
            # lav çatlağı: yan yüzde ışıyan ince damar
            sy = rng.randint(8, TS - 10)
            vv = (off + sy) % P
            x = int(side[vv]) + 1 if s_ == 'l' else int(TS - 1 - side[(vv + 53) % P]) - 1
            d = 1 if s_ == 'l' else -1
            pts = []
            for k in range(rng.randint(4, 9)):
                pts.append((x, sy + k))
                if rng.random() < 0.4:
                    x += d
            iy, ix, _, _, _ = fg.stroke(_dense(pts), lw * 0.45)
            kv = kind[iy, ix]
            ok = (kv >= 1) & (kv <= 4)
            kind[iy[ok], ix[ok]] = 6
    # kırp: yalnızca karo içi
    p0 = PADW * n; T = TS * n
    kind = kind[p0:p0 + T, p0:p0 + T]
    col = col[p0:p0 + T, p0:p0 + T]
    rgba = np.zeros((T, T, 4))
    rgba[kind == 1, :3] = KEY_SOIL
    rgba[kind == 2, :3] = KEY_SHADE
    rgba[kind == 3, :3] = KEY_LIT
    rgba[kind == 4, :3] = KEY_EDGE
    rgba[kind == 5, :3] = col[kind == 5]
    rgba[kind == 6, :3] = KEY_GLOW
    rgba[kind > 0, 3] = 1.0
    nm = normal_rgba(normals_from_height(np.zeros((T, T)), 0.6, wrap=False), (kind > 0).astype(float))
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
    if HD > 1:
        _stroke_img(img, *_dense([(x0, y0), (x1, y1)]).T, _lw() * 0.5, c)
        return
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / max(1, n)
        x = int(round(x0 + (x1 - x0) * t)); y = int(round(y0 + (y1 - y0) * t))
        if 0 <= x < TS and 0 <= y < TS:
            img[y, x, :3] = c; img[y, x, 3] = 1


def _px(img, x, y, c):
    if HD > 1:
        _dot(img, x, y, c)          # HD: yuvarlatılmış nokta (kesirli konum korunur)
        return
    x, y = int(x), int(y)
    if 0 <= x < TS and 0 <= y < TS:
        img[y, x, :3] = c; img[y, x, 3] = 1


def _blade(img, x0, y0, h, lean, base_c, mid_c, tip_c, curve=2.2):
    """Kıvrık ot yaprağı: tabandan uca, uca doğru eğilir (karesel eğri)."""
    if HD > 1:
        # HD: sürekli eğri, uca doğru incelir
        ks = _lin(0, h - 1)
        t = ks / max(1, h - 1)
        cols = np.where((t < 0.35)[:, None], base_c, np.where((t < 0.85)[:, None], mid_c, tip_c))
        _stroke_img(img, x0 + lean * t * t * curve * h / 8.0, y0 - ks, 0.5 * (1.1 - 0.55 * t), cols)
        return
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


def _mush_hd(img, mx, mh, mw, stem_cols, cap_lo, cap_hi, gill):
    """Mantar (HD): sap + yarım elips şapka; sol koyu, sağ açık; alt kenarda lamel noktaları."""
    B = TS - 1
    Y, X = _grid()
    lw = _lw()
    i = np.clip(np.floor(B - Y + 0.5).astype(int), 0, mh - 1)
    stem = (np.abs(X - mx) < 0.42) & (Y <= B + 0.5) & (Y > B - mh + 0.5)
    _ovm(img, stem, np.asarray(stem_cols)[np.broadcast_to(i, stem.shape)[stem]])
    cy = B - mh + 0.5
    q = ((X - mx) / (mw + 0.5)) ** 2 + ((Y - cy) / 2.0) ** 2
    capm = (q <= 1) & (Y <= cy)
    left = np.broadcast_to(X < mx - 0.5 + lw * 0.3, capm.shape)
    hi = np.broadcast_to(Y < cy - 1.0, capm.shape)
    c = np.where(hi[..., None], np.where(left[..., None], cap_hi[0], cap_hi[1]), np.where(left[..., None], cap_lo[0], cap_lo[1]))
    _ovm(img, capm, c[capm])
    for g_, gx in zip(gill, (mx - mw, mx + mw)):
        if g_ is not None:
            _dot(img, gx, B - mh + 1, g_, 0.5)


def _shard_hd(img, x0, h, lean, c1):
    """Kristal sütunu (HD): eğik, uca doğru incelen; sol kontur, iki yüz, parlak uç."""
    B = TS - 1
    Y, X = _grid()
    i = B - Y
    xc = x0 + lean * np.clip(i, 0, None) / h * 2
    w = np.where(i < h - 3, 2.0, np.clip(2.0 - (i - (h - 3)) / 3.0 * 1.5, 0.5, 2.0))
    m = (i >= -0.5) & (i <= h - 0.5) & (X >= xc - w - 0.5) & (X <= xc + w - 0.5)
    c = np.where((X < xc - w - 0.5 + _lw())[..., None], c1[0], np.where((X < xc - 0.5)[..., None], c1[1], c1[2]))
    _ovm(img, m, c[m])
    _dot(img, x0 + lean, B - h, c1[3], 0.55)


def grass_overlay(var):
    rng = random.Random(900 + var * 17 + sum(map(ord, STYLE['cap'])) % 97)
    cap = STYLE['cap']
    hd = HD > 1
    img = np.zeros((TS * HD, TS * HD, 4))
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
                if hd:
                    lw = _lw()
                    ii = _lin(0, fh - 1)
                    _stroke_img(img, fx + (ii / fh) ** 2 * 4, B - ii, lw * 0.6, GRASS[2])
                    for i in range(4, fh, 2):
                        t = i / fh
                        xx = fx + t * t * 4
                        ln = int((1 - t) * 5) + 1
                        s = _lin(0.3, ln)
                        hw = lw * 0.5 * (1.1 - 0.5 * s / ln)
                        _stroke_img(img, xx - s, B - i + s * 0.5, hw, GRASS[3])
                        _stroke_img(img, xx + s, B - i - s / 3.0, hw, np.where((s > ln - 0.5)[:, None], GRASS[5], GRASS[4]))
                else:
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
                    if hd:
                        _mush_hd(img, mx, mh, mw, [hexrgb('#b8b0a0')] * mh, (hexrgb('#8a8f8c'), hexrgb('#c2c8bc')),
                                 (hexrgb('#9aa29b'), hexrgb('#d6dccf')), (hexrgb('#5c615e'), hexrgb('#6c726e')))
                        continue
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
                    J = rng.randint(4, 8)
                    if hd:
                        s = _lin(0, J - 1)
                        _stroke_img(img, tx + s * 0.8, B - fh + 1 + s, _lw() * 0.5 * (1.1 - 0.4 * s / max(1, J - 1)),
                                    np.where((np.floor(s + 0.5) % 2 == 1)[:, None], SPECK[0], SPECK[2]))
                        continue
                    for j in range(J):
                        _px(img, round(tx + j * 0.8), B - fh + 1 + j, SPECK[0] if j % 2 else SPECK[2])
            elif k == 1:
                # gelincikler
                for m in range(rng.randint(2, 3)):
                    fx = rng.randint(4, 30); fh = rng.randint(6, 12)
                    _blade(img, fx, B, fh, 0.6, GRASS[1], GRASS[2], GRASS[3])
                    cy = B - fh
                    for dx, dy, c in ((-1, 0, '#a8221c'), (1, 0, '#e8463a'), (0, -1, '#f0584a'), (0, 0, '#2a0c0a'), (-1, -1, '#c8302a'), (1, -1, '#ff7a64')):
                        _px(img, fx + 1 + dx, cy + dy, hexrgb(c))
                    if hd:
                        _dot(img, fx + 1, cy, hexrgb('#2a0c0a'), 0.4)     # göbek
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
                if hd:
                    s = _lin(0, h - 0.6)
                    _stroke_img(img, x + 0.25 * s * (_hash(x, var, 5) - 0.5), B - s, 0.5 * (1.1 - 0.4 * s / h),
                                GRASS[3 + np.minimum(np.floor(s + 0.5).astype(int), 3)])
                else:
                    for k in range(h):
                        _px(img, x, B - k, GRASS[3 + min(k, 3)])
            x += 1
        k = var % 4
        if k in (0, 2):
            # ışıldayan mantarlar
            for m in range(rng.randint(2, 4)):
                mx = rng.randint(4, 31); mh = rng.randint(3, 9); mw = rng.randint(1, 3)
                if hd:
                    _mush_hd(img, mx, mh, mw, [hexrgb('#9ec8b8') if i % 3 else hexrgb('#7aa898') for i in range(mh)],
                             (hexrgb('#3fd0a8'), hexrgb('#8af0d0')), (hexrgb('#60e0bc'), hexrgb('#c0fff0')), (hexrgb('#1a6a58'), None))
                    continue
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
                if hd:
                    _shard_hd(img, cx + dx, h, lean, c1)
                    continue
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
            if hd:
                # kar topağı: yuvarlatılmış tümsek, üst ve sağ yüz aydınlık
                Y, X = _grid()
                dx = X - cx
                hg = np.clip(np.minimum(h, w + 1 - np.abs(dx)), 0, None)
                hg = hg * (1 - 0.15 * (dx / (w + 0.5)) ** 2)
                topy = B + 0.5 - hg
                mm = (Y >= topy) & (Y <= B + 0.5) & (hg > 0) & (np.abs(dx) <= w + 0.5)
                c = np.where(((Y < topy + _lw()) | (dx > 0))[..., None], GRASS[6], GRASS[5])
                _ovm(img, mm, c[mm])
                continue
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
            if hd:
                Y, X = _grid()
                dx = X - cx; dy = B - Y
                mm = ((dx / 3.4) ** 2 + ((dy - 2.5) / 2.8) ** 2 <= 1) & (dy >= -0.5) & (dy <= 4.5)
                c = np.where((dx > -0.5)[..., None], bone[2], bone[1])
                c = np.where(((dx > 0.8) & (dy > 2.2) & ((dx - 1.6) ** 2 + (dy - 3.4) ** 2 < 1.2))[..., None], bone[3], c)
                _ovm(img, mm, np.broadcast_to(c, mm.shape + (3,))[mm])
                _dot(img, cx - 1, B - 2, bone[0], 0.62); _dot(img, cx + 1, B - 2, bone[0], 0.62)
                _dot(img, cx + 2, B - 3, bone[3], 0.45)
                _stroke_img(img, *_dense([(cx - 0.8, B + 0.1), (cx + 0.8, B + 0.1)]).T, _lw() * 0.45, bone[0])
            else:
                for dy in range(5):
                    for dx in range(-3, 4):
                        if (dx / 3.4) ** 2 + ((dy - 2.5) / 2.8) ** 2 <= 1:
                            _px(img, cx + dx, B - dy, bone[2] if dx > -1 else bone[1])
                _px(img, cx - 1, B - 2, bone[0]); _px(img, cx + 1, B - 2, bone[0]); _px(img, cx + 2, B - 3, bone[3]); _px(img, cx, B, bone[0])
        elif k == 1:
            # obsidiyen dikenleri
            for m in range(rng.randint(2, 3)):
                cx = rng.randint(4, 31); h = rng.randint(4, 10)
                if hd:
                    Y, X = _grid()
                    i = B - Y
                    ext = np.maximum(0.3, (1 - np.clip(i, 0, None) / h) * 2.2)
                    mm = (i >= -0.5) & (i <= h - 0.5) & (np.abs(X - cx) <= ext)
                    hl = np.where((np.floor(i + 0.5) % 3 == 0)[..., None], hexrgb('#6a6688'), hexrgb('#3a364a'))
                    c = np.where((X > cx + ext - _lw())[..., None], hl, np.where((X < cx - 0.5)[..., None], hexrgb('#0c0a10'), hexrgb('#2a2638')))
                    _ovm(img, mm, c[mm])
                    continue
                for i in range(h):
                    w = max(0, int((1 - i / h) * 2.2))
                    for q in range(-w, w + 1):
                        _px(img, cx + q, B - i, hexrgb('#0c0a10') if q < 0 else hexrgb('#2a2638'))
                    _px(img, cx + w, B - i, hexrgb('#6a6688') if i % 3 == 0 else hexrgb('#3a364a'))
        elif k == 2:
            # yanmış kütük
            cx = rng.randint(8, 24)
            cnt = rng.randint(5, 9)
            if hd:
                Y, X = _grid()
                q = X - cx; i = B - Y
                topi = cnt - 0.5 - 0.55 * np.abs(np.sin(q * 2.1 + cx))       # kömürleşmiş, kırık üst
                mm = (q >= -0.5) & (q <= 3.5) & (i >= -0.5) & (i <= topi)
                c = np.where((q < 0.5)[..., None], hexrgb('#140e0e'), np.where((q < 2.5)[..., None], hexrgb('#2e2220'), hexrgb('#4a3632')))
                crack = (np.abs(q - 1.5 - 0.35 * np.sin(i * 1.3 + cx)) < _lw() * 0.3) & (i < topi - 0.8)
                c = np.where(crack[..., None], hexrgb('#140e0e'), c)
                _ovm(img, mm, c[mm])
            else:
                for i in range(cnt):
                    for q in range(0, 4):
                        _px(img, cx + q, B - i, hexrgb('#140e0e') if q == 0 else (hexrgb('#2e2220') if q < 3 else hexrgb('#4a3632')))
            _px(img, cx + 1, B - 2, GRASS[5]); _px(img, cx + 2, B - 4, GRASS[4])
    T = TS * HD
    nm = normal_rgba(np.dstack([np.zeros((T, T)), np.zeros((T, T)), np.ones((T, T))]), img[..., 3])
    return img, nm


def _icicle_hd(img, x, ln, w, c_left, c_mid, c_edge, c_tip=None, dashed=True):
    """Sarkıt (HD): tepede w genişlik, uca doğru sivrilen; sol yüz koyu, sağ kenarda parıltı."""
    Y, X = _grid()
    L = ln + (1 if c_tip is not None else 0)
    e = (w + 0.5) * np.clip(1 - (Y + 0.5) / (L + 0.2), 0, 1) + 0.12
    m = (Y >= -0.5) & (Y <= L - 0.5) & (np.abs(X - x) <= e)
    c = np.where((X < x - 0.5)[..., None], c_left, c_mid)
    edge = (X > x + e - _lw()) & (e > _lw())
    if dashed:
        edge &= np.floor(Y + 0.5) % 2 == 0
    c = np.where(edge[..., None], c_edge, c)
    if c_tip is not None:
        c = np.where((Y > ln - 0.5)[..., None], c_tip, c)
    _ovm(img, m, c[m])


def ceiling_overlay(var):
    rng = random.Random(950 + var * 13)
    ceil = STYLE['ceil']
    hd = HD > 1
    lw = _lw()
    img = np.zeros((TS * HD, TS * HD, 4))
    for _ in range(rng.randint(2, 5)):
        x = rng.randint(1, TS - 2)
        ln = rng.randint(6, 26)
        if ceil == 'roots':
            xx = float(x)
            path, branches = [], []
            for k in range(ln):
                xx += rng.uniform(-0.45, 0.45)
                if hd:
                    path.append((xx, k))
                else:
                    c = ROOT[2] if k < ln - 2 else ROOT[3]
                    _px(img, round(xx), k, c)
                    if k < ln * 0.3:
                        _px(img, round(xx) + 1, k, ROOT[1])
                if rng.random() < 0.08:
                    d = rng.choice([-1, 1])
                    J = rng.randint(2, 5)
                    if hd:
                        branches.append((xx, k, d, J))
                    else:
                        for j in range(1, J):
                            _px(img, round(xx) + d * j, k + j, ROOT[2])
            if hd:
                p = _dense(path)
                k_ = p[:, 1]
                s = np.clip(1 - k_ / (ln * 0.3), 0, 1)          # üstte kalın (iki piksel) kök
                iy, ix, kk, ox, _ = _FG(TS).stroke(np.stack([p[:, 0] + 0.5 * s, k_], -1), lw * 0.5 + 0.5 * s)
                c = np.where((k_[kk] >= ln - 2 - 0.5)[:, None], ROOT[3], ROOT[2])
                c = np.where(((ox > 0.15) & (s[kk] > 0.2))[:, None], ROOT[1], c)
                img[iy, ix, :3] = c; img[iy, ix, 3] = 1
                for bx, by, d, J in branches:
                    q = _dense([(bx, by), (bx + d * (J - 1), by + J - 1)])
                    _stroke_img(img, q[:, 0], q[:, 1], lw * 0.45, ROOT[2])
        elif ceil == 'moss':
            xx = float(x)
            path = []
            for k in range(ln):
                xx += rng.uniform(-0.3, 0.3)
                if hd:
                    path.append((xx, k))
                    continue
                _px(img, round(xx), k, GRASS[2] if k % 3 else GRASS[3])
                if k % 4 == 1:
                    _px(img, round(xx) + 1, k, GRASS[4])
            glow = rng.random() < 0.6
            if hd:
                p = _dense(path)
                cols = np.where((np.floor(p[:, 1] + 0.5) % 3 == 0)[:, None], GRASS[3], GRASS[2])
                _stroke_img(img, p[:, 0], p[:, 1], 0.45, cols)
                for px_, k in path:
                    if k % 4 == 1:
                        q = _dense([(px_ + 0.3, k), (px_ + 1.4, k - 0.35)])
                        _stroke_img(img, q[:, 0], q[:, 1], lw * 0.45, GRASS[4])
                if glow:
                    _dot(img, xx, ln, hexrgb('#9af0d0'), 0.55); _dot(img, xx, ln + 1, hexrgb('#3fd0a8'), 0.45)
            elif glow:
                _px(img, round(xx), ln, hexrgb('#9af0d0')); _px(img, round(xx), ln + 1, hexrgb('#3fd0a8'))
        elif ceil == 'ice':
            w = rng.randint(1, 3)
            if hd:
                _icicle_hd(img, x, ln, w, GRASS[4], GRASS[5], GRASS[6], GRASS[6])
                continue
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
            if hd:
                _icicle_hd(img, x, ln, w, rp[1], rp[2], rp[3], None, dashed=False)
            else:
                for k in range(ln):
                    ww = max(0, int(round(w * (1 - k / ln))))
                    for q in range(-ww, ww + 1):
                        _px(img, x + q, k, rp[1] if q < 0 else (rp[3] if q == ww else rp[2]))
            if rng.random() < 0.7:
                if hd:
                    _dot(img, x, ln - 0.1, hexrgb('#ff9a30'), 0.55); _dot(img, x, ln + 0.9, hexrgb('#ffd060'), 0.5)
                else:
                    _px(img, x, ln, hexrgb('#ff9a30')); _px(img, x, ln + 1, hexrgb('#ffd060'))
    T = TS * HD
    nm = normal_rgba(np.dstack([np.zeros((T, T)), np.zeros((T, T)), np.ones((T, T))]), img[..., 3])
    return img, nm


def _platform_hd(kind, var, rng, cap, x0, x1, TOP):
    """platform_tile'ın HD eşi: aynı tahta düzeni, ince ızgarada lif dokusu ve ince çizgiler."""
    n = HD
    T = TS * n
    lw = _lw()
    img = np.zeros((T, T, 4))
    Y, X = _grid()
    fy = np.arange(T)[:, None]; fx = np.arange(T)[None, :]
    XI = np.floor(X + 0.5).astype(int)
    xin = (X >= x0 - 0.5) & (X < x1 + 0.5)
    plank = xin & (Y >= TOP - 0.5) & (Y < 10.5)
    # lif: yatay uzun çizgiler + ince tane
    g = (np.sin((X + var * TS) * 0.33 + Y * 1.9 + np.sin(X * 0.11) * 2)
         + (_hash_np(np.floor((X + var * TS) * 0.5).astype(int), fy, 31) - 0.5) * 0.6
         + (_hash_np(fx + var * T, fy, 32) - 0.5) * 0.4)
    ry = Y - (TOP - 0.5)
    lvl = np.where(g > 0.5, 3, 2)
    lvl = np.where(g < -1.0, 1, lvl)
    lvl = np.where(Y >= 8.5, 1, lvl)
    lvl = np.where(Y >= 10.5 - lw, 0, lvl)
    lvl = np.where(ry < 2 * lw, 4, lvl)
    lvl = np.where(ry < lw, np.where((XI + var * 7) % 9 != 4, 5, 4), lvl)
    dj = ((X + var * TS + 0.5) % 18) - 0.5           # tahta ek yeri
    mid = (Y >= TOP + 0.5) & (Y < 9.5)
    lvl = np.where(mid & (np.abs(dj) < lw * 0.5), 0, lvl)
    lvl = np.where(mid & (dj >= lw * 0.5) & (dj < lw * 1.5), 4, lvl)
    _ovm(img, plank, WOOD[lvl[plank]])
    # çiviler: yuvarlak baş, sağ üstü parlak
    for nx in (7, 25):
        if x0 <= nx <= x1:
            q = (X - nx) ** 2 + (Y - 4) ** 2
            s_ = (Y - 4) - (X - nx)
            m = q <= 0.95 ** 2
            c = np.where((s_ < -0.45)[..., None], hexrgb('#9aa2ac'), np.where((s_ > 0.45)[..., None], hexrgb('#2a2e36'), hexrgb('#4a525e')))
            img[m, :3] = c[m]
    if cap == 'snow':
        a = _hash_np(np.floor(X).astype(int), var)
        b = _hash_np(np.floor(X).astype(int) + 1, var)
        f = X - np.floor(X); f = f * f * (3 - 2 * f)
        hv = a * (1 - f) + b * f
        depth = 0.5 + np.clip((0.75 - hv) * 5, 0, 1)
        sm = xin & (Y >= -0.5) & (Y < depth)
        _ovm(img, sm, np.broadcast_to(np.where((Y < 0.5)[..., None], GRASS[6], GRASS[5]), sm.shape + (3,))[sm])
        for x in range(x0, x1 + 1):
            if _hash(x, 3, var) < 0.12:
                hw_ = 0.46 * np.clip(1 - (Y - 10.5) / 3.2, 0, 1) ** 0.8 + 0.08
                m = (Y >= 10.5) & (Y <= 13.5) & (np.abs(X - x) <= hw_)
                _ovm(img, m, np.broadcast_to(np.where((Y > 12.5)[..., None], GRASS[6], GRASS[5]), m.shape + (3,))[m])
    elif cap == 'moss':
        mx = rng.randint(2, 20)
        cnt = rng.randint(5, 12)
        a0, a1 = max(mx, x0), min(mx + cnt - 1, x1)
        if a0 <= a1:
            th_ = 0.5 + 0.5 * (0.5 + 0.5 * np.sin(X * 2.6 + var * 1.7))
            m = (X >= a0 - 0.5) & (X < a1 + 0.5) & (Y >= -0.5) & (Y < -0.5 + th_)
            c = np.where((_hash_np(fx, fy, 41 + var) < 0.5)[..., None], GRASS[5], GRASS[4])
            img[m, :3] = c[m]
        for k in range(cnt):
            if x0 <= mx + k <= x1 and k % 3 == 0:
                _stroke_img(img, mx + k + np.zeros(5), np.linspace(10.6, 11.6, 5), lw * 0.5 * np.linspace(1.1, 0.6, 5), GRASS[2])
    elif cap in ('grass', 'dry'):
        if rng.random() < 0.6:
            mx = rng.randint(3, 25)
            cnt = rng.randint(3, 7)
            a0, a1 = max(mx, x0), min(mx + cnt - 1, x1)
            if a0 <= a1:
                th_ = 0.45 + 0.45 * (0.5 + 0.5 * np.sin(X * 3.1 + var))
                m = (X >= a0 - 0.5) & (X < a1 + 0.5) & (Y >= -0.5) & (Y < -0.5 + th_)
                c = np.where((_hash_np(fx, fy, 43 + var) < 0.5)[..., None], GRASS[4], GRASS[3])
                img[m, :3] = c[m]
    elif cap == 'ash':
        for x in range(x0, x1 + 1):
            if _hash(x, var, 5) < 0.25:
                m = (np.abs(X - x) <= 0.5) & (Y >= TOP - 0.5) & (Y < TOP - 0.5 + lw * 1.3)
                img[m, :3] = ASH_PAL()[3]
            if _hash(x, var, 6) < 0.04:
                m = (X - x) ** 2 + (Y - 9) ** 2 <= 0.5 ** 2
                img[m, :3] = hexrgb('#ff8a30')
    if kind in (0, 2):
        # dikme + çapraz destek
        bx = 5 if kind == 0 else TS - 6
        d = 1 if kind == 0 else -1
        xc = bx + d * ((Y - 11) * 0.6 - 0.3)
        o = (X - xc) * d
        m = (Y >= 10.5) & (Y < 25.5) & (np.abs(o) <= 1.5)
        notch = ((Y - 10.5) % 4) < lw
        c = np.where((o > 0.5)[..., None], WOOD[1], np.where((o < -0.5)[..., None], WOOD[3], np.where(notch[..., None], WOOD[1], WOOD[2])))
        _ovm(img, m, c[m])
        # ip sargısı: eğik sarım çizgileri
        lo_, hi_ = min(bx, bx + d) - 0.5, max(bx, bx + d) + 0.5
        m = (X >= lo_) & (X < hi_) & (Y >= 0.5) & (Y < 8.5)
        ph = np.floor(Y + (X - bx) * d * 0.5) % 2 == 1
        near = np.abs(X - bx) <= 0.5
        c = np.where(near[..., None], np.where(ph[..., None], hexrgb('#8a7a58'), hexrgb('#5a4c34')),
                     np.where(ph[..., None], hexrgb('#6e6046'), hexrgb('#4a3e2a')))
        img[m, :3] = c[m]
    nm = normal_rgba(np.dstack([np.zeros((T, T)), np.zeros((T, T)), np.ones((T, T))]), img[..., 3])
    return img, nm


def platform_tile(kind, var):
    """Tahta tek yönlü platform: kind 0 sol uç, 1 orta, 2 sağ uç. Çarpışma üst %25 (9 px)."""
    rng = random.Random(70 + kind * 5 + var)
    cap = STYLE['cap']
    img = np.zeros((TS, TS, 4))
    x0 = 1 if kind == 0 else 0
    x1 = TS - 2 if kind == 2 else TS - 1
    TOP = 1 if cap == 'snow' else 0
    if HD > 1:
        return _platform_hd(kind, var, rng, cap, x0, x1, TOP)
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
    T = TS * HD                     # hücre (piksel); yerleşim/meta mantıksal TS ile aynı
    A = np.zeros((rows * T, 16 * T, 4)); N = np.zeros_like(A)
    PR = _profiles()

    def put(r, c, img):
        a, n = img
        A[r * T:(r + 1) * T, c * T:(c + 1) * T] = a
        N[r * T:(r + 1) * T, c * T:(c + 1) * T] = n

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
