"""sumi: v42 hikâye panelleri için sumi-e (mürekkep yıkama) fırça takımı.

Karakter / süs takımından (inkkit: cel gölge + kontur) farklı olarak burada her şey kâğıda emilen mürekkeptir:
  * kâğıt: sıcak kemik rengi, lif gürültüsü, düşük frekanslı lekeler, kenar kararması
  * fırça darbesi (stroke): kıl kıl çizilir; her kılın mürekkebi darbe boyunca azalır, kuru fırçada kıl kopar (kuru fırça
    "hihaku" dokusu), baskı başta ve ortada güçlü, uçlar sivrilir
  * yıkama (wash): yumuşak maske, gaussian yayılma, granülasyon (pigment tanesi) ve kenarda biriken koyu halka
    (mürekkep kururken kenara çekilir)
  * sıçratma, enso (tek fırça çember), altın varak katmanı (ayrı ışıma dokusu üretir)
Katmanlar: D (kara mürekkep yoğunluğu), C (renkli yıkama: RGB + yoğunluk), G (altın), R (kızıl mühür / kor).
Çıktı: opak panel (JPG) + ışıma (altın / kor, yarım çözünürlük PNG; oyunda toplamalı nabız).
"""
import math

import numpy as np
import skia
from scipy import ndimage

PAPER = np.array([0.925, 0.885, 0.795], np.float32)
INK = np.array([0.055, 0.05, 0.075], np.float32)
GOLD = np.array([0.93, 0.68, 0.26], np.float32)
GOLD_HI = np.array([1.0, 0.9, 0.58], np.float32)
VERM = np.array([0.74, 0.16, 0.1], np.float32)


def fbm(h, w, scale, seed, octaves=4, gain=0.5):
    """Düşük maliyetli fraktal gürültü (0..1): her oktav küçük rastgele ızgaranın büyütülmesi."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    s = scale
    for _ in range(octaves):
        gh, gw = max(2, int(h / s) + 2), max(2, int(w / s) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        z = ndimage.zoom(g, (h / (gh - 1) * 1.0001, w / (gw - 1) * 1.0001), order=3)[:h, :w]
        out += z * amp
        tot += amp
        amp *= gain
        s = max(1.0, s / 2.0)
    out /= tot
    lo, hi = np.percentile(out, 1), np.percentile(out, 99)
    return np.clip((out - lo) / max(1e-5, hi - lo), 0, 1)


def catmull(pts, n=10):
    pts = [np.array(p, np.float64) for p in pts]
    if len(pts) < 3:
        a, b = pts[0], pts[-1]
        return [a + (b - a) * t for t in np.linspace(0, 1, n * 2)]
    P = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return out


class Sumi:
    def __init__(self, w, h, seed=1):
        self.w, self.h = w, h
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.D = np.zeros((h, w), np.float32)      # kara mürekkep
        self.C = np.zeros((h, w, 3), np.float32)   # renkli yıkama (önçarpılmış)
        self.Ca = np.zeros((h, w), np.float32)
        self.G = np.zeros((h, w), np.float32)      # altın varak
        self.R = np.zeros((h, w), np.float32)      # kızıl
        self.E = np.zeros((h, w, 3), np.float32)   # ek ışıma (kor, ruh ışığı) — yalnızca ışıma dokusuna
        self._grain = fbm(h, w, 3.0, seed + 91, octaves=2)
        self._fiber = None

    # ---------------------------------------------------------------- tarama
    def raster(self, fn, aa=True):
        """fn(canvas) skia ile gri tonlu maske çizer -> float32 (0..1)."""
        surf = skia.Surface(self.w, self.h)
        c = surf.getCanvas()
        c.clear(skia.ColorBLACK)
        fn(c)
        img = surf.makeImageSnapshot().toarray()
        return img[..., 0].astype(np.float32) / 255.0

    def path_mask(self, pts, closed=True, smooth=True):
        P = catmull(pts, 8) if smooth else [np.array(p) for p in pts]

        def fn(c):
            pa = skia.Path()
            pa.moveTo(*P[0])
            for q in P[1:]:
                pa.lineTo(*q)
            if closed:
                pa.close()
            paint = skia.Paint(AntiAlias=True, Color=skia.ColorWHITE)
            c.drawPath(pa, paint)
        return self.raster(fn)

    def ellipse_mask(self, cx, cy, rx, ry):
        def fn(c):
            c.drawOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry), skia.Paint(AntiAlias=True, Color=skia.ColorWHITE))
        return self.raster(fn)

    # ---------------------------------------------------------------- fırça darbesi
    def stroke(self, pts, w, load=1.0, dry=0.35, taper=(0.18, 0.55), press=None, bristles=None, layer='D', seed=None,
               col=None, smooth=True, n=10, wobble=0.0, ret=False):
        """Kuru / ıslak fırça darbesi. w: en kalın yerdeki genişlik (px). load: mürekkep yükü (0..1+). dry: kuru fırça
        oranı (0 ıslak, 1 çok kuru). taper: (baş, son) sivrilme payı. press: kalınlık profili fonksiyonu t -> 0..1."""
        rs = np.random.default_rng(self.rng.integers(1 << 30) if seed is None else seed)
        P = catmull(pts, n) if smooth else [np.array(p, np.float64) for p in pts]
        P = np.array(P)
        if wobble > 0:
            P = P + rs.normal(0, wobble, P.shape).cumsum(0) * 0.12
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        L = np.concatenate([[0], np.cumsum(seg)])
        tot = max(1e-3, L[-1])
        t = L / tot
        tg = np.gradient(P, axis=0)
        tg /= np.maximum(1e-6, np.linalg.norm(tg, axis=1, keepdims=True))
        nr = np.stack([-tg[:, 1], tg[:, 0]], 1)
        a0, a1 = taper
        if press is None:
            prof = np.minimum(1.0, np.minimum(t / max(1e-3, a0), (1 - t) / max(1e-3, a1)))
            prof = np.clip(prof, 0, 1) ** 0.6
            prof = 0.22 + 0.78 * prof if a0 < 0.05 else prof
        else:
            prof = np.array([press(x) for x in t])
        width = w * np.maximum(0.04, prof)
        nb = bristles or max(5, int(w / 1.6))
        offs = np.sort(rs.uniform(-0.5, 0.5, nb))
        loads = rs.uniform(0.75, 1.15, nb)
        # kılın mürekkebi darbe boyunca azalır; kuru fırçada kenar kılları önce kurur
        fade = 1.0 - dry * 0.75 * t
        noise_len = max(4, int(tot / 14))

        def fn(c):
            paint = skia.Paint(AntiAlias=True, StrokeCap=skia.Paint.kButt_Cap, Style=skia.Paint.kStroke_Style)
            # gövde: ıslak orta kısım (kılların altında yumuşak dolgu)
            core = 0.86 * (1.0 - dry * 0.55)
            if core > 0.05:
                for i in range(len(P) - 1):
                    paint.setStrokeWidth(float(max(0.6, width[i] * 0.86)))
                    paint.setColor(skia.Color4f(1, 1, 1, float(np.clip(core * load * fade[i], 0, 1))))
                    c.drawLine(float(P[i, 0]), float(P[i, 1]), float(P[i + 1, 0]), float(P[i + 1, 1]), paint)
            for b in range(nb):
                o = offs[b]
                edge = abs(o) * 2.0
                bn = np.interp(np.linspace(0, 1, len(P)), np.linspace(0, 1, noise_len), rs.random(noise_len))
                bn = ndimage.gaussian_filter1d(bn, 1.2)
                bw = max(0.7, w / nb * 2.6)
                for i in range(len(P) - 1):
                    # kuru fırça: kenar kılları ve darbenin sonu gürültüyle kopar
                    thr = dry * (0.35 + 0.65 * edge) * (0.45 + 0.85 * t[i])
                    a = (bn[i] - thr * 0.9) * 2.2
                    a = float(np.clip(a, 0, 1)) * loads[b] * load * fade[i]
                    if a < 0.02:
                        continue
                    q0 = P[i] + nr[i] * o * width[i]
                    q1 = P[i + 1] + nr[i + 1] * o * width[i + 1]
                    paint.setStrokeWidth(float(bw * (0.55 + 0.45 * prof[i])))
                    paint.setColor(skia.Color4f(1, 1, 1, min(1.0, a)))
                    c.drawLine(float(q0[0]), float(q0[1]), float(q1[0]), float(q1[1]), paint)

        m = self.raster(fn)
        if ret:
            return m
        self.put(m, layer, col)
        return m

    def put(self, m, layer='D', col=None, k=1.0):
        if layer == 'D':
            self.D = 1 - (1 - self.D) * (1 - np.clip(m * k, 0, 1))
        elif layer == 'G':
            self.G = np.maximum(self.G, np.clip(m * k, 0, 1))
        elif layer == 'R':
            self.R = 1 - (1 - self.R) * (1 - np.clip(m * k, 0, 1))
        elif layer == 'C':
            a = np.clip(m * k, 0, 1)
            cc = np.array(col, np.float32)
            self.C = self.C * (1 - a[..., None]) + cc * a[..., None]
            self.Ca = 1 - (1 - self.Ca) * (1 - a)
        elif layer == 'E':
            cc = np.array(col, np.float32)
            self.E += cc * m[..., None] * k

    # ---------------------------------------------------------------- yıkama
    def wash(self, m, dens=0.5, blur=6.0, bleed=0.5, gran=0.35, layer='D', col=None, seed=None, edge_blur=None):
        """Yumuşak mürekkep yıkaması: maske yayılır, pigment tanelenir, kenarda koyu halka toplanır."""
        s = seed if seed is not None else int(self.rng.integers(1 << 30))
        b = ndimage.gaussian_filter(m, blur) if blur > 0 else m
        # kenar halkası: kuruyan mürekkep sınıra çekilir
        eb = edge_blur or blur * 2.2
        ring = np.clip(b - ndimage.gaussian_filter(b, eb), 0, 1) * 2.0
        n = fbm(self.h, self.w, max(8.0, blur * 6), s, octaves=3)
        # sınırı gürültüyle bük (mürekkep kâğıtta düzensiz yayılır)
        bb = np.clip(b + (n - 0.5) * 0.9 * np.clip(b * (1 - b) * 4.0, 0, 1), 0, 1)
        val = bb * (1 - gran * 0.25 + gran * 0.3 * self._grain) * (0.9 + 0.18 * n) + ring * bleed
        self.put(np.clip(val, 0, 1.2) * dens, layer, col)
        return val

    def grad_wash(self, y0, y1, d0, d1, layer='D', col=None, gran=0.3, seed=3, wobble=40.0):
        """Dikey geçişli yıkama (gök / yer bandı): y0'da d0, y1'de d1; yatayda gürültüyle dalgalanır."""
        yy = np.arange(self.h, dtype=np.float32)[:, None]
        n = fbm(self.h, self.w, 120.0, seed, octaves=3)
        yw = yy + (n - 0.5) * wobble
        t = np.clip((yw - y0) / max(1.0, (y1 - y0)), 0, 1)
        t = t * t * (3 - 2 * t)
        v = d0 + (d1 - d0) * t
        v = v * (1 - gran * 0.22 + gran * 0.3 * self._grain) * (0.93 + 0.14 * fbm(self.h, self.w, 160.0, seed + 1, 3))
        self.put(np.clip(v, 0, 1), layer, col)

    def mist(self, y, h, k=0.6, seed=5):
        """Sis bandı: mürekkebi siler (kâğıt geri gelir) — sumi-e'de 'boşluk'."""
        yy = np.arange(self.h, dtype=np.float32)[:, None]
        n = fbm(self.h, self.w, 90.0, seed, octaves=3)
        band = np.exp(-((yy - y + (n - 0.5) * h * 0.9) / h) ** 2)
        f = 1 - np.clip(band * k * (0.7 + 0.5 * n), 0, 1)
        self.D *= f
        self.Ca *= f
        self.C *= f[..., None]

    def erase(self, m, k=1.0):
        f = 1 - np.clip(m * k, 0, 1)
        self.D *= f
        self.Ca *= f
        self.C *= f[..., None]

    # ---------------------------------------------------------------- küçükler
    def splatter(self, cx, cy, n, r, size=(1.0, 5.0), layer='D', col=None, k=1.0, seed=None):
        rs = np.random.default_rng(seed if seed is not None else int(self.rng.integers(1 << 30)))

        def fn(c):
            p = skia.Paint(AntiAlias=True)
            for _ in range(n):
                a = rs.uniform(0, math.tau)
                d = abs(rs.normal(0, r))
                s = rs.uniform(*size) * (1.2 - min(1.0, d / (r * 2.5)))
                p.setColor(skia.Color4f(1, 1, 1, float(rs.uniform(0.5, 1.0))))
                c.drawCircle(float(cx + math.cos(a) * d), float(cy + math.sin(a) * d * 0.8), float(max(0.4, s)), p)
        m = self.raster(fn)
        self.put(m, layer, col, k)
        return m

    def enso(self, cx, cy, r, w, a0=-1.9, span=5.6, load=1.0, dry=0.5, layer='D', col=None, seed=None, squash=1.0):
        pts = [(cx + math.cos(a0 + span * i / 40.0) * r, cy + math.sin(a0 + span * i / 40.0) * r * squash) for i in range(41)]
        return self.stroke(pts, w, load=load, dry=dry, taper=(0.04, 0.45), layer=layer, col=col, seed=seed, n=4)

    def dots(self, pts, r, layer='D', k=1.0, col=None):
        def fn(c):
            p = skia.Paint(AntiAlias=True, Color=skia.ColorWHITE)
            for (x, y, *rr) in pts:
                c.drawCircle(float(x), float(y), float(rr[0] if rr else r), p)
        m = self.raster(fn)
        self.put(m, layer, col, k)
        return m

    def leaf(self, x, y, s, ang, layer='D', load=0.9, col=None, ret=False):
        """Tek fırça yaprağı (bas-kaldır): kalından inceye."""
        dx, dy = math.cos(ang), math.sin(ang)
        pts = [(x, y), (x + dx * s * 0.5 - dy * s * 0.12, y + dy * s * 0.5 + dx * s * 0.12), (x + dx * s, y + dy * s)]
        return self.stroke(pts, s * 0.42, load=load, dry=0.15, taper=(0.15, 0.85), layer=layer, col=col, n=6, ret=ret)

    # ---------------------------------------------------------------- bitiriş
    def paper(self, tone=None, stain=0.035, vign=0.22, seed=7):
        h, w = self.h, self.w
        base = PAPER if tone is None else np.array(tone, np.float32)
        fib = fbm(h, w, 1.5, seed, octaves=2)
        fib2 = ndimage.gaussian_filter1d(self.rng.random((h, w)).astype(np.float32), 6, axis=1)
        low = fbm(h, w, 420.0, seed + 3, octaves=2)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
        v = 1 - vign * np.clip(r - 0.55, 0, 1) ** 1.6
        col = base[None, None, :] * (1 - stain * (low - 0.5) * 2)[..., None]
        col = col * (0.975 + 0.035 * fib[..., None]) * (0.99 + 0.03 * (fib2[..., None] - 0.5)) * v[..., None]
        # sıcak lekeler (çay rengi)
        col = col * (1 - 0.05 * np.clip(low - 0.7, 0, 1)[..., None] * np.array([0.2, 0.6, 1.2]))
        return col.astype(np.float32)

    def compose(self, tone=None, ink=None, gold_k=1.0, seal=None):
        col = self.paper(tone)
        # renkli yıkama: çarpma (kâğıda emilir)
        ca = np.clip(self.Ca, 0, 1)[..., None]
        cc = np.where(ca > 1e-4, self.C / np.maximum(ca, 1e-4), 0)
        col = col * (1 - ca) + col * cc * ca
        # kara mürekkep: yoğunlukla doğrusal olmayan koyulaşma (ince yıkama gri, üst üste binen koyu)
        d = np.clip(self.D, 0, 1)
        d = 1 - (1 - d) ** 1.25
        ic = INK if ink is None else np.array(ink, np.float32)
        col = col * (1 - d[..., None]) + ic * d[..., None]
        # kızıl
        r = np.clip(self.R, 0, 1)[..., None]
        col = col * (1 - r) + VERM * r
        # altın varak: tanecikli, ışıltılı
        g = np.clip(self.G * gold_k, 0, 1)
        sp = fbm(self.h, self.w, 2.0, self.seed + 55, octaves=2)
        gc = GOLD[None, None, :] * (0.78 + 0.32 * sp[..., None]) + (GOLD_HI - GOLD)[None, None, :] * np.clip(sp - 0.72, 0, 1)[..., None] * 2.2
        col = col * (1 - g[..., None]) + gc * g[..., None]
        return np.clip(col, 0, 1)

    def glow(self, scale=0.5, rad=18.0, gold_k=1.0):
        """Işıma dokusu (RGBA, düz): altın + ek ışıma, yayılmış; oyunda toplamalı ve nabızlı."""
        g = np.clip(self.G * gold_k, 0, 1)
        e = self.E.copy()
        e += GOLD_HI[None, None, :] * g[..., None] * 0.9
        small = ndimage.zoom(e, (scale, scale, 1), order=1)
        bl = np.zeros_like(small)
        for rr, kk in ((rad * scale * 0.25, 0.55), (rad * scale, 0.5), (rad * scale * 3.0, 0.35)):
            for ch in range(3):
                bl[..., ch] += ndimage.gaussian_filter(small[..., ch], rr) * kk
        a = np.clip(bl.max(axis=2), 0, 1)
        rgb = np.where(a[..., None] > 1e-4, bl / np.maximum(a[..., None], 1e-4), 0)
        return np.concatenate([np.clip(rgb, 0, 1), a[..., None]], -1)


def save_rgb_jpg(arr, path, q=90):
    from PIL import Image
    Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, quality=q, subsampling=0, optimize=True)


def save_rgba_png(arr, path):
    from PIL import Image
    Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(path, optimize=True)
