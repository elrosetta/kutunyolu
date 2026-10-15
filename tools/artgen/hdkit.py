"""Yüksek yoğunluklu (1.5x) piksel sanat araçları: zemin dokuları ve paralaks katmanları için ortak.

Dünya ölçüsü değişmez; dokular 1.5 kat yoğun üretilip oyunda 2/3 ölçekle çizilir (1080p'de her doku
pikseli 2x2 ekran pikseli). Buradaki her şey sert kenarlı, sınırlı paletli ve sıralı titreşimlidir:
yumuşak geçiş yerine ton basamakları + Bayer deseni.

Işık her yerde sağ üstten gelir (görüntü koordinatı: x sağa, y aşağı, z ekrandan dışarı).
"""
import colorsys
import math
import numpy as np
from PIL import Image

K = 1.5
LIGHT = np.array([0.62, -0.62, 0.48]); LIGHT = LIGHT / np.linalg.norm(LIGHT)

BAYER8 = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]]) / 64.0


def hexrgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255.0


def pal(*hexes):
    return np.array([hexrgb(h) for h in hexes])


def bayer(h, w, ox=0, oy=0):
    return np.tile(BAYER8, (h // 8 + 2, w // 8 + 2))[oy % 8:oy % 8 + h, ox % 8:ox % 8 + w]


def hsv(h, s, v):
    return np.array(colorsys.hsv_to_rgb((h % 360) / 360.0, min(1, max(0, s)), min(1, max(0, v))))


def hramp(hue, sat, val, n=6, lo=0.32, hi=1.25, hue_sh=-22, hue_hi=14, sat_lo=1.18, sat_hi=0.8):
    """Ton kaydırmalı rampa: koyular soğuğa (mor/maviye), açıklar sıcağa (sarıya) kayar."""
    out = []
    for i in range(n):
        t = i / (n - 1)
        if t < 0.5:
            k = (0.5 - t) * 2
            h = hue + _hd(hue, 250) * 0.18 * k
            s = sat * (1 + (sat_lo - 1) * k)
            v = val * (1 - (1 - lo) * k)
        else:
            k = (t - 0.5) * 2
            h = hue + _hd(hue, 55) * 0.16 * k
            s = sat * (1 + (sat_hi - 1) * k)
            v = min(1.0, val * (1 + (hi - 1) * k))
        out.append(hsv(h, s, v))
    return np.array(out)


def _hd(a, b):
    return ((b - a + 180) % 360) - 180


def mix(a, b, t):
    return a * (1 - t) + b * t


# ------------------------------------------------------------------ gürültü (dikişsiz)
def vnoise(w, h, cx, cy, rng, wrap_x=True, wrap_y=True):
    gw, gh = max(1, int(round(w / cx))), max(1, int(round(h / cy)))
    g = rng.random((gh + 1, gw + 1))
    if wrap_x:
        g[:, gw] = g[:, 0]
    if wrap_y:
        g[gh, :] = g[0, :]
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


def fbm(w, h, cells, rng, aspect=1.0, gain=0.55, wrap_y=True):
    out = np.zeros((h, w)); tot = 0.0; amp = 1.0
    for c in cells:
        out += vnoise(w, h, c, max(1.0, c * aspect), rng, True, wrap_y) * amp
        tot += amp; amp *= gain
    return out / tot


def ridged(w, h, cells, rng, aspect=1.0, gain=0.5, wrap_y=True):
    out = np.zeros((h, w)); tot = 0.0; amp = 1.0
    for c in cells:
        n = vnoise(w, h, c, max(1.0, c * aspect), rng, True, wrap_y)
        out += (1 - np.abs(n * 2 - 1)) ** 2 * amp
        tot += amp; amp *= gain
    return out / tot


def profile(w, cells, rng, gain=0.5):
    """1B periyodik profil 0..1."""
    p = fbm(w, 1, cells, rng, gain=gain, wrap_y=False)[0]
    return (p - p.min()) / (p.max() - p.min() + 1e-9)


def warp_sample(a, dx, dy):
    """a'yı (dx, dy) piksel kaydırma alanıyla örnekle (sarmalı, en yakın komşu)."""
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    return a[(yy + np.round(dy).astype(int)) % h, (xx + np.round(dx).astype(int)) % w]


def roll(a, dy, dx):
    return np.roll(np.roll(a, dy, 0), dx, 1)


def shift_nw(a, dy, dx, fill=0):
    out = np.full_like(a, fill)
    h, w = a.shape[:2]
    ys = slice(max(dy, 0), h + min(dy, 0)); yd = slice(max(-dy, 0), h + min(-dy, 0))
    xs = slice(max(dx, 0), w + min(dx, 0)); xd = slice(max(-dx, 0), w + min(-dx, 0))
    out[ys, xs] = a[yd, xd]
    return out


def run_depth(mask, from_top=True):
    h = mask.shape[0]
    d = np.zeros(mask.shape, int)
    prev = np.zeros(mask.shape[1], int)
    for y in (range(h) if from_top else range(h - 1, -1, -1)):
        prev = np.where(mask[y], prev + 1, 0)
        d[y] = prev
    return d


def dist_inside(mask, maxd=8, wrap=False):
    """Maskenin içinde kenara (4-komşu) uzaklık, maxd'de kesilir."""
    d = np.where(mask, maxd, 0).astype(int)
    cur = mask.copy()
    for k in range(1, maxd):
        if wrap:
            nb = roll(cur, 1, 0) & roll(cur, -1, 0) & roll(cur, 0, 1) & roll(cur, 0, -1)
        else:
            nb = shift_nw(cur, 1, 0, False) & shift_nw(cur, -1, 0, False) & shift_nw(cur, 0, 1, False) & shift_nw(cur, 0, -1, False)
        edge = cur & ~nb
        d[edge] = k
        cur = cur & nb
    return d


# ------------------------------------------------------------------ ton seçimi
def tone(val, n, dither=0.5, b=None):
    """0..1 değeri n basamağa çevir; dither sıralı titreşim genişliği (basamak cinsinden)."""
    if b is None:
        b = bayer(*val.shape)
    return np.clip(np.floor(val * n + (b - 0.5) * dither), 0, n - 1).astype(int)


def quant_rgb(img, steps=48, dither=0.9):
    h, w = img.shape[:2]
    return np.clip(np.floor(img * steps + (bayer(h, w)[..., None] - 0.5) * dither) / steps, 0, 1)


def reduce_palette(rgba, n=48, alpha_steps=4):
    """Katmanı sınırlı palete indir (titreşimsiz; titreşim zaten çizimde). Alfa basamaklı."""
    a = rgba[..., 3]
    vis = a > 0.02
    rgb = (np.clip(rgba[..., :3], 0, 1) * 255).astype(np.uint8)
    im = Image.fromarray(rgb, 'RGB')
    if vis.any():
        # yalnızca görünen piksellerden palet çıkar
        ys, xs = np.nonzero(vis)
        sel = rgb[ys, xs][None, :, :]
        pim = Image.fromarray(sel, 'RGB').quantize(n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        q = im.quantize(palette=pim, dither=Image.Dither.NONE).convert('RGB')
        rgb = np.asarray(q).astype(float) / 255.0
    else:
        rgb = rgb.astype(float) / 255.0
    if alpha_steps:
        h, w = a.shape
        a = np.clip(np.floor(a * alpha_steps + (bayer(h, w) - 0.5) * 0.9) / alpha_steps, 0, 1)
        a[rgba[..., 3] >= 0.999] = 1.0
    out = np.dstack([rgb, a])
    out[out[..., 3] <= 0] = 0
    return out


def to_image(rgba):
    return Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA')


def normals_from_height(hgt, strength=1.0, wrap=True):
    if wrap:
        gx = (roll(hgt, 0, -1) - roll(hgt, 0, 1)) * 0.5 * strength
        gy = (roll(hgt, -1, 0) - roll(hgt, 1, 0)) * 0.5 * strength
    else:
        gx = (shift_nw(hgt, 0, -1) - shift_nw(hgt, 0, 1)) * 0.5 * strength
        gy = (shift_nw(hgt, -1, 0) - shift_nw(hgt, 1, 0)) * 0.5 * strength
    n = np.stack([-gx, -gy, np.ones_like(hgt)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def normal_rgba(n, alpha=None):
    out = np.zeros(n.shape[:2] + (4,))
    out[..., 0] = n[..., 0] * 0.5 + 0.5
    out[..., 1] = -n[..., 1] * 0.5 + 0.5
    out[..., 2] = n[..., 2] * 0.5 + 0.5
    out[..., 3] = 1.0 if alpha is None else alpha
    return out


# ------------------------------------------------------------------ şekil tuvali
class ShapeCanvas:
    """Malzeme + normal + yükseklik tamponlu tuval. Şekiller (kaya, kök, kristal, kemik) buraya
    z-sıralı çizilir; sonra ışığa göre ton basamaklarına ayrılır. wrap=True ise dikişsizdir."""

    def __init__(self, w, h, wrap=True):
        self.w, self.h, self.wrap = w, h, wrap
        self.mat = np.full((h, w), -1, int)
        self.n = np.zeros((h, w, 3)); self.n[..., 2] = 1
        self.z = np.full((h, w), -1e9)
        self.hgt = np.zeros((h, w))
        self.spec = np.zeros((h, w))
        self.mats = []

    def add_mat(self, ramp, outline=None, spec=0.0, emis=None, bands=None):
        """ramp: koyudan açığa renkler (n,3). emis: ışıma rengi (ya da None)."""
        self.mats.append(dict(ramp=np.asarray(ramp, float), outline=outline, spec=spec, emis=emis, bands=bands))
        return len(self.mats) - 1

    def _region(self, x0, y0, x1, y1):
        xs = np.arange(int(math.floor(x0)), int(math.ceil(x1)) + 1)
        ys = np.arange(int(math.floor(y0)), int(math.ceil(y1)) + 1)
        if not self.wrap:
            xs = xs[(xs >= 0) & (xs < self.w)]
            ys = ys[(ys >= 0) & (ys < self.h)]
        return xs, ys

    def _put(self, xs, ys, m, nrm, z, mat, hgt=None, spec=None):
        if len(xs) == 0 or len(ys) == 0:
            return
        X = xs % self.w; Y = ys % self.h
        sub_z = self.z[np.ix_(Y, X)]
        ok = m & (z > sub_z)
        if not ok.any():
            return
        yy, xx = np.nonzero(ok)
        Yi, Xi = Y[yy], X[xx]
        zz = z if np.isscalar(z) else z[yy, xx]
        self.z[Yi, Xi] = zz
        self.mat[Yi, Xi] = mat
        self.n[Yi, Xi] = nrm[yy, xx]
        if hgt is not None:
            self.hgt[Yi, Xi] = hgt[yy, xx]
        if spec is not None:
            self.spec[Yi, Xi] = spec[yy, xx]

    def blob(self, cx, cy, rx, ry, mat, z=0.0, rot=0.0, rough=0.0, rng=None, facets=0, flat=0.35, zh=1.0):
        """Kaya/çakıl: düzensiz kenarlı, isteğe bağlı yüzeyli (facet) kubbe."""
        R = max(rx, ry) * (1 + rough) + 2
        xs, ys = self._region(cx - R, cy - R, cx + R, cy + R)
        X, Y = np.meshgrid(xs + 0.5 - cx, ys + 0.5 - cy)
        c, s = math.cos(rot), math.sin(rot)
        u = (X * c + Y * s) / rx
        v = (-X * s + Y * c) / ry
        ang = np.arctan2(v, u)
        rad = np.ones_like(ang)
        if rough > 0 and rng is not None:
            k = 7
            amps = rng.uniform(-rough, rough, k)
            phs = rng.uniform(0, math.tau, k)
            for i in range(k):
                rad = rad + amps[i] * np.cos((i + 2) * ang + phs[i]) / (1 + i * 0.6)
        d = np.sqrt(u * u + v * v) / rad
        m = d < 1.0
        if not m.any():
            return
        dome = np.sqrt(np.clip(1 - d * d, 0, 1))
        # kubbe normali: düzleştirilmiş (üst yüzey düz, kenarlar döner)
        nx = u / rad * (1 - flat * (1 - d))
        ny = v / rad * (1 - flat * (1 - d))
        if facets and rng is not None:
            # yüzeyler: açı dilimlerine göre sabit normal (yontulmuş taş görünümü)
            k = facets
            off = rng.uniform(0, math.tau)
            sl = np.floor((ang - off) / (math.tau / k))
            mid = (sl + 0.5) * (math.tau / k) + off
            tilt = rng.uniform(0.55, 0.85, k + 2)
            ti = tilt[(sl.astype(int)) % k]
            fx = np.cos(mid) * ti; fy = np.sin(mid) * ti
            top = d < rng.uniform(0.3, 0.5)
            nx = np.where(top, nx * 0.3, fx * np.clip(d * 1.6, 0.4, 1))
            ny = np.where(top, ny * 0.3, fy * np.clip(d * 1.6, 0.4, 1))
        # yerel eksenden dünyaya döndür
        wx = nx * c - ny * s
        wy = nx * s + ny * c
        nz = np.sqrt(np.clip(1 - wx * wx - wy * wy, 0.05, 1))
        nrm = np.stack([wx, wy, nz], -1)
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        self._put(xs, ys, m, nrm, z + dome * zh, mat, hgt=dome * max(rx, ry) * 0.5)

    def tube(self, pts, r0, r1, mat, z=0.0, rr=None):
        """Kalınlığı azalan boru (kök, dal, kemik): her piksel en yakın merkez noktasına göre gölgelenir."""
        pts = np.asarray(pts, float)
        if len(pts) < 2:
            return
        # yoğun örnekleme
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
        X, Y = np.meshgrid(xs + 0.5, ys + 0.5)
        best = np.full(X.shape, 1e9); bdx = np.zeros(X.shape); bdy = np.zeros(X.shape); br = np.ones(X.shape)
        for (sx, sy), r in zip(seg, rads):
            dx = X - sx; dy = Y - sy
            d = np.sqrt(dx * dx + dy * dy) / max(r, 0.3)
            upd = d < best
            best = np.where(upd, d, best); bdx = np.where(upd, dx, bdx); bdy = np.where(upd, dy, bdy); br = np.where(upd, r, br)
        m = best < 1.0
        nx = bdx / np.maximum(br, 0.3); ny = bdy / np.maximum(br, 0.3)
        nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0.05, 1))
        nrm = np.stack([nx, ny, nz], -1)
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        self._put(xs, ys, m, nrm, z + (1 - best) * 0.5, mat, hgt=(1 - best) * br)

    def poly(self, pts, mat, z=0.0, normal=(0, 0, 1)):
        """Düz yüzeyli çokgen (kristal yüzü, keskin kaya)."""
        pts = np.asarray(pts, float)
        xs, ys = self._region(pts[:, 0].min() - 1, pts[:, 1].min() - 1, pts[:, 0].max() + 1, pts[:, 1].max() + 1)
        X, Y = np.meshgrid(xs + 0.5, ys + 0.5)
        inside = np.zeros(X.shape, bool)
        n = len(pts)
        j = n - 1
        for i in range(n):
            xi, yi = pts[i]; xj, yj = pts[j]
            cond = ((yi > Y) != (yj > Y)) & (X < (xj - xi) * (Y - yi) / (yj - yi + 1e-12) + xi)
            inside ^= cond
            j = i
        nv = np.asarray(normal, float); nv = nv / np.linalg.norm(nv)
        nrm = np.broadcast_to(nv, X.shape + (3,)).copy()
        self._put(xs, ys, inside, nrm, z, mat, hgt=np.full(X.shape, 1.0))

    def shade(self, light=LIGHT, ambient=0.0, dither=0.6, rim=True, outline=True):
        """Ton basamaklarına ayır: (rgba, emis_rgb, mask)."""
        h, w = self.h, self.w
        rgba = np.zeros((h, w, 4)); emis = np.zeros((h, w, 3))
        m_all = self.mat >= 0
        if not m_all.any():
            return rgba, emis, m_all
        ndl = np.einsum('hwc,c->hw', self.n, light)
        lam = np.clip(ndl * 0.5 + 0.5, 0, 1)
        b = bayer(h, w)
        for mi, M in enumerate(self.mats):
            m = self.mat == mi
            if not m.any():
                continue
            rp = M['ramp']; n = len(rp)
            v = lam[m]
            bands = M['bands']
            if bands is None:
                idx = np.clip(np.floor((v - 0.12) / 0.86 * n + (b[m] - 0.5) * dither), 0, n - 1).astype(int)
            else:
                idx = np.digitize(v + (b[m] - 0.5) * dither * 0.1, bands)
                idx = np.clip(idx, 0, n - 1)
            col = rp[idx]
            rgba[m, :3] = col
            rgba[m, 3] = 1
            if M['spec'] > 0:
                # ıslak/cam parlaması: ışığa en dönük küçük bölge
                hl = m & (ndl > 0.93 - (1 - M['spec']) * 0.1)
                rgba[hl, :3] = np.minimum(1, rp[-1] * 1.15 + 0.12)
            if M['emis'] is not None:
                emis[m] = np.asarray(M['emis']) * (0.55 + 0.45 * lam[m])[:, None]
        if outline or rim:
            if self.wrap:
                sh = lambda a, dy, dx: roll(a, dy, dx)
            else:
                sh = lambda a, dy, dx: shift_nw(a, dy, dx, -1 if a.dtype != bool else False)
            for mi, M in enumerate(self.mats):
                m = self.mat == mi
                if not m.any():
                    continue
                # gölge tarafı (sol/alt) kenar: kontur
                if outline and M['outline'] is not None:
                    e = m & ((sh(self.mat, -1, 0) < 0) | (sh(self.mat, 0, 1) < 0))
                    rgba[e, :3] = M['outline']
                if rim:
                    r_ = m & ((sh(self.mat, 1, 0) < 0) | (sh(self.mat, 0, -1) < 0)) & ~((sh(self.mat, -1, 0) < 0) | (sh(self.mat, 0, 1) < 0))
                    rgba[r_, :3] = np.minimum(1, M['ramp'][-1] * 1.04)
        return rgba, emis, m_all
