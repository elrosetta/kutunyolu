"""Paralaks katmanları için yüksek yoğunluklu (1.5x) piksel sanat çizim ilkelleri.

Katman boyutu: gök 960x540, diğerleri 1920x540 (oyun 2/3 ölçekle çizer: 640x360 / 1280x360 ekran birimi).
Bütün katmanlar yatayda dikişsizdir (x % W). Tonlar rampadan seçilir, geçişler Bayer titreşimlidir;
bulanıklık yoktur. Atmosfer perspektifi: uzak katmanlar sis rengine karışır, kontrastı düşer.
"""
import math
import numpy as np

import hdkit as hk
from hdkit import hexrgb, pal, bayer, fbm, ridged, profile, BAYER8, mix

W, H = 1920, 540
SW, SH = 960, 540


def B(y, x):
    return BAYER8[int(y) % 8, int(x) % 8]


def norm(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def gradient(stops, w, h, steps=56, dither=0.95):
    """stops: [(0..1, '#hex'), ...] dikey gök geçişi, titreşimli basamaklar."""
    ys = np.arange(h) / (h - 1)
    col = np.zeros((h, 3))
    for (y0, c0), (y1, c1) in zip(stops, stops[1:]):
        m = (ys >= y0) & (ys <= y1)
        t = (ys[m] - y0) / max(1e-6, (y1 - y0))
        col[m] = hexrgb(c0) + (hexrgb(c1) - hexrgb(c0)) * t[:, None]
    img = np.broadcast_to(col[:, None, :], (h, w, 3)).copy()
    return img


def dq(img, steps=56, dither=0.95):
    h, w = img.shape[:2]
    return np.clip(np.floor(img * steps + (bayer(h, w)[..., None] - 0.5) * dither) / steps, 0, 1)


def ramp_pick(ramp, v, b, dither=0.7):
    """v (dizi) 0..1 → rampa rengi; b aynı şekilli Bayer eşiği."""
    n = len(ramp)
    idx = np.clip(np.floor(v * n + (b - 0.5) * dither), 0, n - 1).astype(int)
    return np.asarray(ramp)[idx]


class Layer:
    """Yatay sarmalı RGBA katman."""

    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.rgba = np.zeros((h, w, 4))

    # ---- temel
    def grid(self, x0, y0, x1, y1):
        xs = np.arange(int(math.floor(x0)), int(math.ceil(x1)) + 1)
        ys = np.arange(max(0, int(math.floor(y0))), min(self.h - 1, int(math.ceil(y1))) + 1)
        return xs, ys

    def put(self, xs, ys, mask, col, alpha=1.0):
        if len(xs) == 0 or len(ys) == 0:
            return
        X = xs % self.w
        yy, xx = np.nonzero(mask)
        if len(yy) == 0:
            return
        Y, Xi = ys[yy], X[xx]
        c = col if np.ndim(col) == 1 else col[yy, xx]
        a = alpha if np.isscalar(alpha) else alpha[yy, xx]
        if np.isscalar(a) and a >= 1.0:
            self.rgba[Y, Xi, :3] = c
            self.rgba[Y, Xi, 3] = 1.0
        else:
            a = np.asarray(a, float)
            if a.ndim == 0:
                a = np.full(len(Y), float(a))
            old = self.rgba[Y, Xi]
            na = a + old[:, 3] * (1 - a)
            self.rgba[Y, Xi, :3] = (np.asarray(c) * a[:, None] + old[:, :3] * old[:, 3:4] * (1 - a[:, None])) / np.maximum(na[:, None], 1e-6)
            self.rgba[Y, Xi, 3] = na

    def px(self, x, y, c, a=1.0):
        y = int(y)
        if 0 <= y < self.h:
            x = int(math.floor(x)) % self.w
            if a >= 1:
                self.rgba[y, x, :3] = c; self.rgba[y, x, 3] = 1
            else:
                o = self.rgba[y, x]
                na = a + o[3] * (1 - a)
                self.rgba[y, x, :3] = (np.asarray(c) * a + o[:3] * o[3] * (1 - a)) / max(na, 1e-6)
                self.rgba[y, x, 3] = na

    def over(self, other):
        a = other.rgba[..., 3:4]
        self.rgba[..., :3] = other.rgba[..., :3] * a + self.rgba[..., :3] * self.rgba[..., 3:4] * (1 - a)
        na = a[..., 0] + self.rgba[..., 3] * (1 - a[..., 0])
        self.rgba[..., :3] /= np.maximum(na[..., None], 1e-6)
        self.rgba[..., 3] = na

    # ---- şekiller
    def sphere(self, cx, cy, r, ramp, light, rough=0.0, rng=None, squash=1.0, dither=0.8, edge_cut=0.0, lift=0.0, cell=2.0,
               rim_col=None, alpha=1.0, flat=0.25):
        """Yaprak kümesi / kaya / bulut topağı: küre normaliyle tonlanır; kenar gürültüyle yırtılır."""
        R = r * (1 + rough) + 1
        xs, ys = self.grid(cx - R, cy - R * squash, cx + R, cy + R * squash)
        if len(ys) == 0:
            return None
        X, Y = np.meshgrid(xs + 0.5 - cx, ys + 0.5 - cy)
        u = X / r; v = Y / (r * squash)
        d = np.sqrt(u * u + v * v)
        if rough > 0 and rng is not None:
            n = rng.random(X.shape)
            # kaba + ince kenar yırtığı (yaprak dokusu)
            ang = np.arctan2(v, u)
            lob = np.zeros_like(ang)
            for k in range(5):
                lob += rng.uniform(-1, 1) * np.cos((k + 3) * ang + rng.uniform(0, 6.3)) / (k + 1.5)
            d = d * (1 + lob * rough * 0.7) + (n - 0.5) * rough * 0.35
        m = d < 1.0
        if not m.any():
            return None
        nz = np.sqrt(np.clip(1 - np.clip(d, 0, 1) ** 2, 0, 1))
        nx, ny = u * (1 - flat), v * (1 - flat)
        nn = np.stack([nx, ny, nz + 0.25], -1)
        nn /= np.linalg.norm(nn, axis=-1, keepdims=True)
        lam = np.clip(np.einsum('hwc,c->hw', nn, light) * 0.5 + 0.5 + lift, 0, 1)
        if edge_cut > 0 and rng is not None:
            # içeride küçük yaprak kümecikleri: hücre gürültüsüyle ton kırıkları
            g = rng.random((int(len(ys) / cell) + 2, int(len(xs) / cell) + 2))
            gi = g[(np.arange(len(ys)) / cell).astype(int)][:, (np.arange(len(xs)) / cell).astype(int)]
            lam = lam + (gi - 0.5) * edge_cut
        bb = BAYER8[ys[:, None] % 8, xs[None, :] % 8]
        col = ramp_pick(ramp, np.clip(lam, 0, 0.999), bb, dither)
        if rim_col is not None:
            rim = m & (d > 0.82) & ((u * light[0] + v * light[1]) > 0.35)
            col[rim] = rim_col
        self.put(xs, ys, m, col, alpha)
        return m

    def tube(self, pts, r0, r1, ramp, light, dither=0.6, bark=None, rng=None, rim_col=None, rr=None, flow=None):
        """Gövde/dal/kök: kesit boyunca silindir tonlaması (ışık tarafı açık)."""
        pts = np.asarray(pts, float)
        seg = []
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            n = max(2, int(np.hypot(*(b - a)) * 1.5) + 1)
            for t in np.linspace(0, 1, n, endpoint=False):
                seg.append(a + (b - a) * t)
        seg.append(pts[-1])
        seg = np.array(seg)
        if rr is not None:
            rads = np.interp(np.linspace(0, 1, len(seg)), np.linspace(0, 1, len(rr)), rr)
        else:
            rads = np.linspace(r0, r1, len(seg))
        R = max(rads.max(), 1) + 1
        xs, ys = self.grid(seg[:, 0].min() - R, seg[:, 1].min() - R, seg[:, 0].max() + R, seg[:, 1].max() + R)
        if len(ys) == 0:
            return
        X, Y = np.meshgrid(xs + 0.5, ys + 0.5)
        best = np.full(X.shape, 1e9); bdx = np.zeros(X.shape); bdy = np.zeros(X.shape)
        for (sx, sy), r in zip(seg, rads):
            dx = X - sx; dy = Y - sy
            d = np.sqrt(dx * dx + dy * dy) / max(r, 0.35)
            upd = d < best
            best = np.where(upd, d, best); bdx = np.where(upd, dx / max(r, 0.35), bdx); bdy = np.where(upd, dy / max(r, 0.35), bdy)
        m = best < 1.0
        nz = np.sqrt(np.clip(1 - bdx * bdx - bdy * bdy, 0, 1))
        lam = np.clip(bdx * light[0] + bdy * light[1] + nz * light[2], -1, 1) * 0.5 + 0.5
        if bark is not None and rng is not None:
            # kabuk çatlakları: dikey uzun gürültü
            hh, ww = X.shape
            bn = rng.random((hh // 6 + 2, ww + 2))
            bn = bn[(np.arange(hh) // 6)][:, np.arange(ww)]
            lam = lam - (bn > 1 - bark) * 0.28
        if flow is not None and rng is not None:
            # akıtma taşı (flowstone): yatay dalgalı perdeler
            hh, ww = X.shape
            ph = rng.uniform(0, 6.28)
            nn = rng.random((hh // 5 + 2, ww // 9 + 2))
            nn = nn[(np.arange(hh) // 5)][:, (np.arange(ww) // 9)]
            wav = np.sin(Y * 0.32 + np.sin(X * 0.13 + ph) * 1.2 + nn * 2.5)
            lam = lam + (wav > 0.8) * flow - (wav < -0.85) * flow
        bb = BAYER8[ys[:, None] % 8, xs[None, :] % 8]
        col = ramp_pick(ramp, np.clip(lam, 0, 0.999), bb, dither)
        if rim_col is not None:
            rim = m & (best > 0.7) & (bdx * light[0] + bdy * light[1] > 0.3)
            col[rim] = rim_col
        self.put(xs, ys, m, col)

    def poly(self, pts, col, alpha=1.0):
        pts = np.asarray(pts, float)
        xs, ys = self.grid(pts[:, 0].min() - 1, pts[:, 1].min() - 1, pts[:, 0].max() + 1, pts[:, 1].max() + 1)
        if len(ys) == 0:
            return None
        X, Y = np.meshgrid(xs + 0.5, ys + 0.5)
        inside = np.zeros(X.shape, bool)
        n = len(pts); j = n - 1
        for i in range(n):
            xi, yi = pts[i]; xj, yj = pts[j]
            inside ^= ((yi > Y) != (yj > Y)) & (X < (xj - xi) * (Y - yi) / (yj - yi + 1e-12) + xi)
            j = i
        self.put(xs, ys, inside, col if np.ndim(col) == 1 else col, alpha)
        return xs, ys, inside

    def line(self, x0, y0, x1, y1, col, a=1.0):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            self.px(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, col, a)


# ------------------------------------------------------------------ dağ sırası
def mountain_range(ridge, ramp, light, rng, snow_ramp=None, snow_line=0.35, haze=None, haze_amt=0.0, haze_bottom=0.0,
                   haze_from=None, gully=1.0, strata=0.0, w=W, h=H, lit_edge=None, fill_to=None, dither=0.8, snow_dither=0.6,
                   detail_cells=(96, 48, 24, 12)):
    """ridge: her sütunda sırt yüksekliği (piksel). Erozyon olukları (dallanan dikey ridged gürültü)
    yüzeyin x eğimini oluşturur: oluk duvarları ışığa göre aydınlık/gölge alır. Kar zirvelerde ve
    oluklarda tutunur. Dönüş: RGBA (h,w,4)."""
    yy = np.arange(h)[:, None].astype(float)
    below = yy - ridge[None, :]
    inside = below >= 0
    if fill_to is not None:
        inside &= yy <= fill_to
    # büyük ölçek yüzler: sırt eğiminden, aşağı indikçe yumuşar
    sl = np.roll(ridge, -3) - np.roll(ridge, 3)
    def blur(a, r):
        k = np.ones(2 * r + 1) / (2 * r + 1)
        return np.convolve(np.concatenate([a[-r:], a, a[:r]]), k, mode='valid')
    s1 = blur(sl, 4) / 6.0
    s2 = blur(sl, 22) / 6.0
    s3 = blur(sl, 60) / 6.0
    span = max(1.0, ridge.max() - ridge.min())
    f1 = np.clip(below / (span * 0.25 + 10), 0, 1)
    f2 = np.clip(below / (span * 0.9 + 30), 0, 1)
    facet = s1[None, :] * (1 - f1) + s2[None, :] * f1 * (1 - f2) + s3[None, :] * f2
    # erozyon olukları: dikeyde uzun, aşağı doğru genişleyen dallar (alanı bükerek)
    warp = fbm(w, h, [256, 128], rng, wrap_y=False)
    wx = (warp - 0.5) * 60 + below * 0.0
    g1 = ridged(w, h, [detail_cells[0], detail_cells[1]], rng, aspect=4.0, wrap_y=False)
    g2 = ridged(w, h, [detail_cells[2], detail_cells[3]], rng, aspect=3.0, wrap_y=False)
    g1 = hk.warp_sample(g1, wx, np.zeros_like(wx))
    G = g1 * 0.65 + g2 * 0.35
    dG = (np.roll(G, -1, 1) - np.roll(G, 1, 1)) * 0.5
    nx = np.tanh(facet * 1.2) * 0.7 - dG * 16.0 * gully
    ny = -0.35 + np.clip(below / 400.0, 0, 0.25)
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0.05, 1))
    lam = (nx * light[0] + ny * light[1] + nz * light[2])
    lam = lam / np.sqrt(nx * nx + ny * ny + nz * nz)
    lam = np.clip(lam * 0.78 + 0.32, 0, 1)
    # ince doku ve kaya katmanları
    det = fbm(w, h, [24, 12, 6], rng, wrap_y=False)
    lam = lam + (det - 0.5) * 0.14
    if strata > 0:
        st = (np.sin(yy * 0.42 + det * 7.0 + warp * 9) > 0.86)
        lam = lam - st * strata
    b = bayer(h, w)
    col = ramp_pick(ramp, np.clip(lam, 0, 0.999), b, dither)
    if snow_ramp is not None:
        # kar çizgisi: sabit bir yükseltinin üstü (dalgalı), oluklarda aşağı iner, dik yüzlerde tutunmaz
        sn = fbm(w, 1, [96, 48, 24], rng, wrap_y=False)[0][None, :]
        line_y = ridge.min() + span * snow_line + (sn - 0.5) * span * 0.18
        above = yy < line_y + (G - 0.5) * span * 0.35
        steep = np.abs(nx) > 0.62
        snow = inside & above & (~steep | (G > 0.7)) & (det > 0.3)
        streak = inside & (G > 0.82) & (yy < line_y + span * 0.32)
        snow |= streak
        scol = ramp_pick(snow_ramp, np.clip(lam * 1.05, 0, 0.999), b, snow_dither)
        col = np.where(snow[..., None], scol, col)
    if haze is not None:
        hz = np.full((h, w), haze_amt)
        if haze_bottom > 0:
            hf = ridge.min() if haze_from is None else haze_from
            hz = hz + np.clip((yy - hf) / max(1.0, h - hf), 0, 1) ** 1.3 * haze_bottom
        hz = np.clip(hz, 0, 1)
        hzq = np.clip(np.floor(hz * 10 + (b - 0.5) * 0.95) / 10, 0, 1)
        col = col * (1 - hzq[..., None]) + hexrgb(haze) * hzq[..., None] if isinstance(haze, str) else col * (1 - hzq[..., None]) + haze * hzq[..., None]
    rgba = np.zeros((h, w, 4))
    rgba[inside, :3] = col[inside]
    rgba[inside, 3] = 1
    if lit_edge is not None:
        top = inside & ~np.roll(inside, 1, 0)
        e = top & (sl > -0.5)[None, :]
        rgba[e, :3] = lit_edge
    return rgba


def ridge_line(w, base, amp, cells, rng, peaks=0.0, sharp=1.0):
    """Sırt profili: base - amp * p(x); peaks > 0 sivri (ridged) zirveler karıştırır, sharp > 1 vadileri genişletir."""
    p = profile(w, cells, rng)
    if peaks > 0:
        r = np.zeros(w)
        amp_ = 1.0
        for c in cells[1:4]:
            n = fbm(w, 1, [c], rng, wrap_y=False)[0]
            r += (1 - np.abs(n * 2 - 1)) ** 2 * amp_
            amp_ *= 0.5
        r = (r - r.min()) / (r.max() - r.min() + 1e-9)
        p = p * (1 - peaks) + r * peaks
        p = (p - p.min()) / (p.max() - p.min() + 1e-9)
    p = p ** sharp
    return base - p * amp


def apply_haze(rgba, col, amt, b=None):
    """Katmanı (opak kısımlarını) sis rengine karıştır — basamaklı."""
    h, w = rgba.shape[:2]
    if b is None:
        b = bayer(h, w)
    a = np.asarray(amt, float)
    if a.ndim == 0:
        a = np.full((h, w), float(a))
    q = np.clip(np.floor(a * 12 + (b - 0.5) * 0.9) / 12, 0, 1)
    c = hexrgb(col) if isinstance(col, str) else np.asarray(col)
    rgba[..., :3] = rgba[..., :3] * (1 - q[..., None]) + c * q[..., None]
    return rgba


# ------------------------------------------------------------------ bulutlar
def cloud_bank(w, h, rng, cy, thick, cell, thr, ramp, light, flat_bottom=True, stretch=0.42, rim=None, dens_gain=1.0,
               x_mask=None, dither=0.75, breakup=0.0):
    """Hacimli bulut: yoğunluk alanı + ışığa doğru örneklenen öz-gölge, tonlar rampadan.
    Dönüş: (rgb, mask)."""
    yy = np.arange(h)[:, None].astype(float)
    n = fbm(w, h, [cell, cell / 2, cell / 4, cell / 8, cell / 16], rng, aspect=stretch, gain=0.52, wrap_y=False)
    top_env = np.clip(1 - np.abs(yy - cy) / thick, 0, 1) ** 0.7
    base = cy + thick * (0.35 + 0.15 * (fbm(w, 1, [cell], rng, wrap_y=False)[0][None, :] - 0.5))
    D = n * (0.45 + 0.75 * top_env) * dens_gain
    if flat_bottom:
        D = D * np.clip((base - yy) / 6.0, 0, 1)
    if x_mask is not None:
        D = D * x_mask[None, :]
    if breakup > 0:
        bn = fbm(w, 1, [cell * 2, cell], rng, wrap_y=False)[0]
        bn = (bn - bn.min()) / (bn.max() - bn.min() + 1e-9)
        D = D * np.clip((bn - breakup) / 0.25, 0, 1)[None, :] ** 0.5
    m = D > thr
    # öz-gölge: ışığa doğru yoğunluk
    occ = np.zeros((h, w))
    lx, ly = light[0], light[1]
    for k, wt in ((3, 0.4), (7, 0.35), (14, 0.25)):
        occ += np.roll(np.roll(D, -int(round(ly * k)), 0), -int(round(lx * k)), 1) * wt
    lam = 0.85 - (occ - thr) * 2.4 + (D - thr) * 0.6
    # alt kısım gölgeli (düz taban)
    lam -= np.clip((yy - (base - thick * 0.5)) / (thick * 0.8), 0, 1) * 0.25
    b = bayer(h, w)
    col = ramp_pick(ramp, np.clip(lam, 0, 0.999), b, dither)
    if rim is not None:
        edge = m & ~(np.roll(np.roll(m, -int(np.sign(ly)), 0), -int(np.sign(lx)), 1))
        col[edge] = rim
    return col, m


def stars(img, rng, n, ymax, cols, avoid=None, w=None):
    h, ww = img.shape[:2]
    for _ in range(n):
        x, y = rng.integers(0, ww), int(rng.integers(0, ymax))
        if avoid is not None and avoid(x, y):
            continue
        bri = rng.random()
        c = hexrgb(cols[0]) if bri > 0.55 else (hexrgb(cols[1]) if bri > 0.2 else hexrgb(cols[2]))
        img[y, x, :3] = c
        if bri > 0.97 and 2 <= y < h - 2:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                img[y + dy, (x + dx) % ww, :3] = hexrgb(cols[1])
            for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                img[y + dy, (x + dx) % ww, :3] = hexrgb(cols[2])


def bird(L, x, y, col, span=3, flap=0):
    """Uzak kuş: kanat çırpma pozuna göre V / düz."""
    pts = [(-span, -1 + flap), (-span + 1, -1 + flap), (-1, 0), (0, 0), (1, 0), (span - 1, -1 + flap), (span, -1 + flap)]
    if span >= 4:
        pts += [(-span + 2, -1 + flap), (span - 2, -1 + flap)]
    for dx, dy in pts:
        L.px(x + dx, y + dy, col)


# ------------------------------------------------------------------ ağaçlar
def conifer(L, x, base, hgt, ramp, light, rng, trunk_ramp=None, snow_ramp=None, rim_col=None, width=0.36, tiers=None, droop=1.0):
    """Ladin/çam: kademeli, uçları sarkan dal katları; ışık tarafı açık, iğne dokulu kenar."""
    top = base - hgt
    if trunk_ramp is not None:
        L.tube([(x, base), (x, top + hgt * 0.2)], max(1.0, hgt * 0.035), 0.6, trunk_ramp, light)
    nt = tiers or max(4, int(hgt / (9 + hgt * 0.035)))
    for i in range(nt):
        t0 = i / nt
        ty = top + hgt * 0.9 * t0
        ln = hgt * 0.9 / nt * 1.9
        wv = (hgt * width) * (0.15 + 0.85 * ((i + 1) / nt) ** 0.9) * rng.uniform(0.85, 1.12)
        # bir kat: üst sivri, alt saçaklı (sarkan uçlar)
        xs, ys = L.grid(x - wv - 2, ty, x + wv + 2, ty + ln + 3)
        if len(ys) == 0:
            continue
        X, Y = np.meshgrid(xs + 0.5 - x, ys + 0.5 - ty)
        tt = np.clip(Y / ln, 0, 1)
        half = wv * tt ** 0.85
        saw = (np.abs(np.sin(X * 1.7 + i * 2.3)) * 2.0 + rng.random(X.shape) * 1.6) * (0.4 + tt)
        bottom = ln - np.abs(X) / max(wv, 1) * ln * 0.25 * droop + saw * 0.6
        m = (np.abs(X) < half + rng.random(X.shape) * 1.2 - 0.4) & (Y >= 0) & (Y < bottom)
        # tonlama: sağ (ışık) taraf açık, alt kısım gölgeli; iğne kırıkları
        side = X / max(wv, 1)
        lam = 0.5 + side * light[0] * 0.55 - (Y / ln) * 0.35 + 0.18 + (rng.random(X.shape) - 0.5) * 0.28
        lam -= (np.abs(np.sin(X * 0.9 + Y * 1.3 + i)) > 0.92) * 0.2
        bb = BAYER8[ys[:, None] % 8, xs[None, :] % 8]
        col = ramp_pick(ramp, np.clip(lam, 0, 0.999), bb, 0.7)
        if snow_ramp is not None:
            # kat üstünde kar yükü: üst yüzeyin ilk 1-3 pikseli
            topm = m & ~np.roll(m, 1, 0)
            sd = np.zeros(m.shape, bool)
            for k in range(rng.integers(2, 4)):
                sd |= np.roll(topm, k, 0) & m
            sd &= (rng.random(m.shape) > 0.12)
            scol = ramp_pick(snow_ramp, np.clip(0.55 + side * 0.4, 0, 0.999), bb, 0.7)
            col = np.where(sd[..., None], scol, col)
        if rim_col is not None:
            rim = m & ~np.roll(m, -1, 1) & (X > 0)
            col[rim] = rim_col
        L.put(xs, ys, m, col)


def deciduous(L, x, base, hgt, ramp, trunk_ramp, light, rng, crown_w=0.55, n_clusters=None, rim_col=None, sparse=0.0, lean=0.0,
              branch_r=None):
    """Yapraklı ağaç: dallanan gövde + küre yaprak kümeleri (ışık tarafı açık, gölge içte)."""
    tw = branch_r or max(1.4, hgt * 0.045)
    top = (x + lean * hgt * 0.3, base - hgt * 0.55)
    L.tube([(x, base), (x + lean * hgt * 0.15, base - hgt * 0.3), top], tw, tw * 0.6, trunk_ramp, light, bark=0.2, rng=rng)
    # ana dallar
    ends = []
    for k in range(rng.integers(3, 6)):
        a = -math.pi / 2 + rng.uniform(-1.1, 1.1)
        ln = hgt * rng.uniform(0.22, 0.38)
        mx, my = top[0] + math.cos(a) * ln * 0.5, top[1] + math.sin(a) * ln * 0.5 - 2
        ex, ey = top[0] + math.cos(a) * ln, top[1] + math.sin(a) * ln
        L.tube([top, (mx, my), (ex, ey)], tw * 0.55, tw * 0.25, trunk_ramp, light)
        ends.append((ex, ey))
    # yaprak kümeleri: arkadan öne, alttan üste
    cw = hgt * crown_w
    cy0 = base - hgt * 0.68
    nc = n_clusters or int(10 + hgt * 0.35)
    cl = []
    for k in range(nc):
        a = rng.uniform(0, math.tau)
        rr = rng.uniform(0, 1) ** 0.6
        cx = top[0] + math.cos(a) * cw * 0.5 * rr
        cy = cy0 + math.sin(a) * hgt * 0.26 * rr
        r = hgt * rng.uniform(0.09, 0.16)
        cl.append((cy + rng.uniform(-2, 2), cx, r))
    for ex, ey in ends:
        cl.append((ey, ex, hgt * rng.uniform(0.1, 0.15)))
    cl.sort(key=lambda c: -c[0] * 0.3 + (c[1] - top[0]) * light[0] * 0.1)
    for cy, cx, r in cl:
        if sparse > 0 and rng.random() < sparse:
            continue
        lift = -0.12 + (cy0 - cy) / hgt * 0.4
        L.sphere(cx, cy, r, ramp, light, rough=0.45, rng=rng, squash=0.85, edge_cut=0.32, lift=lift, cell=2.0, rim_col=rim_col)


def bare_tree(L, x, base, hgt, ramp, light, rng, depth=5, w0=None):
    """Kuru ağaç: özyinelemeli dallanma."""
    w0 = w0 or max(1.2, hgt * 0.04)

    def br(x0, y0, a, ln, w, d):
        x1, y1 = x0 + math.cos(a) * ln, y0 + math.sin(a) * ln
        mx, my = (x0 + x1) / 2 + rng.uniform(-ln, ln) * 0.12, (y0 + y1) / 2 + rng.uniform(-ln, ln) * 0.08
        L.tube([(x0, y0), (mx, my), (x1, y1)], w, max(0.4, w * 0.65), ramp, light)
        if d <= 0 or ln < 3:
            return
        for s in (-1, 1):
            if rng.random() < 0.85:
                br(x1, y1, a + s * rng.uniform(0.25, 0.7), ln * rng.uniform(0.6, 0.78), max(0.45, w * 0.62), d - 1)
    br(x, base, -math.pi / 2 + rng.uniform(-0.1, 0.1), hgt * 0.38, w0, depth)


def fill_ground(L, ytop, col_fn):
    """ytop[x] altını col_fn(ys, x) rengiyle doldur (opak)."""
    for x in range(L.w):
        y0 = int(max(0, ytop[x]))
        if y0 >= L.h:
            continue
        L.rgba[y0:, x, :3] = col_fn(np.arange(y0, L.h), x)
        L.rgba[y0:, x, 3] = 1


# ------------------------------------------------------------------ zirveli dağ kütlesi
def make_peaks(rng, n, ybase, hmin, hmax, w=W, smin=0.45, smax=1.05, jitter=0.35):
    """Arkadan öne sıralı zirveler: (px, py, sol eğim, sağ eğim). Yüksekler arkada."""
    pk = []
    for i in range(n):
        px = (i + 0.5 + rng.uniform(-jitter, jitter)) * w / n
        hh = rng.uniform(hmin, hmax)
        pk.append((px, ybase - hh, rng.uniform(smin, smax), rng.uniform(smin, smax)))
    pk.sort(key=lambda p: p[1])
    return pk


def massif(peaks, ramp, light, rng, snow_ramp=None, snow_y=None, haze=None, haze_amt=0.0, haze_bottom=0.0, haze_from=None,
           rough=5.0, spur=1.0, spur_period=34.0, lit_edge=None, back_haze=0.0, w=W, h=H, dither=0.8, gully_snow=26.0,
           crag=0.0):
    """Gerçekçi dağ kütlesi: her zirve iki yüzlü (ışık/gölge), yüzlerde sırta paralel inen mahmuz ve oluklar,
    kıvrımlı tepe ekseni, pürüzlü silüet, yükselti çizgisinin üstünde kar (oluklarda daha aşağı)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    b = bayer(h, w)
    out = np.zeros((h, w, 4))
    zbuf = np.zeros((h, w), bool)
    en = (fbm(w, 1, [64, 32, 16, 8, 4], rng, wrap_y=False)[0] - 0.5) * 2 * rough
    det = fbm(w, h, [32, 16, 8, 4], rng, wrap_y=False)
    stripe_n = fbm(w, h, [64, 32], rng, wrap_y=False)
    shoulder = fbm(w, 1, [96, 48, 24], rng, wrap_y=False)[0]
    shoulder = (1 - np.abs(shoulder * 2 - 1)) ** 2
    vax = fbm(1, h, [40, 20], rng, wrap_y=False)[:, 0] if False else (fbm(h, 1, [60, 30, 15], rng, wrap_y=False)[0])
    n = len(peaks)
    for i, (px, py, sl, sr) in enumerate(peaks):
        dx = ((xx - px + w / 2) % w) - w / 2
        dyp = yy - py
        ax = (vax[np.clip(yy.astype(int), 0, h - 1)] - 0.5) * np.clip(dyp, 0, 110) * 0.55
        rel = dx - ax
        slope = np.where(rel > 0, sr, sl)
        sh = shoulder[(xx.astype(int) + i * 211) % w]
        top = py + np.abs(rel) * slope + en[xx.astype(int) % w] * np.clip(np.abs(dx) / 25.0, 0, 1) - sh * np.clip(np.abs(rel) * 0.18, 0, 18)
        inside = yy >= top
        if not inside.any():
            continue
        side = np.sign(rel)
        # zirveden yelpaze gibi inen mahmuz/oluklar: sabit açı çizgileri, gürültüyle bükülmüş
        tq = rel / np.maximum(dyp, 4.0)
        q = tq * spur_period + (stripe_n - 0.5) * 1.1 + i * 7.3
        tbl = rng.random(4096)
        tbl = np.convolve(np.concatenate([tbl[-2:], tbl, tbl[:2]]), np.ones(3) / 3, mode='valid')
        qi = (q * 1.0) % 4000 + 10
        v0 = np.interp(qi, np.arange(len(tbl)), tbl)
        dv = np.interp(qi + 0.08, np.arange(len(tbl)), tbl) - np.interp(qi - 0.08, np.arange(len(tbl)), tbl)
        tri = 1 - np.abs(v0 * 2 - 1)               # 1 sırt, 0 oluk
        fan = np.clip(dyp / 18.0, 0, 1)
        nx = side * (0.36 + 0.16 * slope) + np.tanh(dv * 8) * 0.62 * spur * fan
        ny = -0.3 + np.clip(dyp / 300.0, 0, 0.25)
        nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0.05, 1))
        ln = np.sqrt(nx * nx + ny * ny + nz * nz)
        ml = norm([light[0] * 1.6, light[1] * 0.5, light[2] * 0.5])
        lam = (nx * ml[0] + ny * ml[1] + nz * ml[2]) / ln
        lam = np.clip(lam * 0.62 + 0.4, 0, 1) + (det - 0.5) * 0.18
        # oluk dipleri: ince koyu yarıklar
        lam -= ((tri < 0.12) & (fan > 0.5)) * 0.18
        # yatay kaya katmanları (hafif)
        lam -= (np.sin(yy * 0.21 + det * 9 + stripe_n * 6 + i) > 0.96) * 0.05
        tri = 1 - tri
        col = bk_ramp(ramp, lam, b, dither)
        if snow_ramp is not None and snow_y is not None:
            sy = snow_y + (det - 0.5) * 22
            snow = inside & ((yy < sy + (tri > 0.55) * gully_snow * (1 - np.clip(dyp / 160, 0, 1)) * 1.0) | (yy < py + 6 + det * 6))
            snow &= ~((np.abs(nx) > 0.82) & (det < 0.45))
            scol = bk_ramp(snow_ramp, np.clip(lam + 0.05, 0, 1), b, dither * 0.8)
            col = np.where(snow[..., None], scol, col)
        if lit_edge is not None:
            e = inside & ~np.roll(inside, 1, 0) & (rel > 0)
            col[e] = lit_edge
        if back_haze > 0 and n > 1:
            k = back_haze * (1 - i / (n - 1))
            q = np.clip(np.floor(k * 10 + (b - 0.5) * 0.9) / 10, 0, 1)
            col = col * (1 - q[..., None]) + np.asarray(haze if not isinstance(haze, str) else hexrgb(haze)) * q[..., None]
        out[inside, :3] = col[inside]
        out[inside, 3] = 1
        zbuf |= inside
    if haze is not None and (haze_amt > 0 or haze_bottom > 0):
        hz = np.full((h, w), haze_amt)
        if haze_bottom > 0:
            hf = min(p[1] for p in peaks) if haze_from is None else haze_from
            hz = hz + np.clip((yy - hf) / max(1.0, h - hf), 0, 1) ** 1.3 * haze_bottom
        apply_haze(out, haze, np.clip(hz, 0, 1) * zbuf, b)
    return out


def bk_ramp(ramp, v, b, dither):
    return ramp_pick(ramp, np.clip(v, 0, 0.999), b, dither)


def cumulus(L, cx, cy, width, height, ramp, light, rng, base_flat=True, puff=(0.18, 0.34), n=None, under=None, lift=0.0,
            rough=0.18, squash=0.8, alpha=1.0, rim_col=None):
    """Küme bulut: kubbe zarfına dizilmiş kürecik topakları (karnabahar), düz taban, alt kısım gölgeli.
    Arka (büyük, yüksek) topaklar önce, alçak/öndekiler sonra çizilir."""
    n = n or int(8 + width / 9)
    puffs = []
    for k in range(n):
        t = rng.uniform(-1, 1)
        env = (1 - t * t) ** 0.7
        r = height * rng.uniform(*puff) * (0.55 + 0.6 * env) * 2.2
        x = cx + t * width * 0.5
        y = cy - env * height * rng.uniform(0.45, 0.85) + r * 0.45
        puffs.append((y - r, x, y, r))
    puffs.sort(key=lambda p: p[0])
    base_y = cy + height * 0.12
    clip = Layer(L.w, L.h)
    for _, x, y, r in puffs:
        clip.sphere(x, y, r, ramp, light, rough=rough, rng=rng, squash=squash, dither=0.85, lift=lift + (base_y - y) / (height * 4), flat=0.1,
                    rim_col=rim_col)
    if base_flat:
        clip.rgba[int(base_y) + 1:, :, 3] = 0
        # taban: alt 2-4 satır koyu
        yb = int(base_y)
        for k, c in ((0, ramp[0]), (1, ramp[1]), (2, ramp[1])):
            row = clip.rgba[yb - k]
            m = row[:, 3] > 0
            if k == 2:
                m &= (BAYER8[(yb - k) % 8, np.arange(L.w) % 8] < 0.5)
            row[m, :3] = c
    if under is not None:
        under(clip)
    a = clip.rgba[..., 3:4] * alpha
    m = a[..., 0] > 0
    L.rgba[m, :3] = clip.rgba[m, :3] * a[m] + L.rgba[m, :3] * (1 - a[m])
    L.rgba[m, 3] = np.maximum(L.rgba[m, 3], a[m, 0])
    return clip


def hills(L, ridge, ramp, light, rng, grass=None, streaks=0.0, shadows=0.0, depth_dark=0.25, dither=0.8, tex=0.12):
    """Yuvarlak tepe sırası: sırt eğimine göre ışık, sırttan aşağı inildikçe hafif kararma, ot dokusu,
    rüzgâr dalgaları ve bulut gölgeleri. Sırtın altını opak doldurur."""
    h, w = L.h, L.w
    yy = np.arange(h)[:, None].astype(float)
    d = np.gradient(np.concatenate([ridge[-3:], ridge, ridge[:3]]))[3:-3]
    k = np.ones(9) / 9
    d = np.convolve(np.concatenate([d[-4:], d, d[:4]]), k, mode='valid')
    nx, ny = d, -np.ones_like(d)
    ln = np.sqrt(nx * nx + 1)
    slope_l = (nx * light[0] + ny * light[1]) / ln
    below = yy - ridge[None, :]
    inside = below >= 0
    lam = 0.5 + slope_l[None, :] * 0.55 - np.clip(below / 120.0, 0, 1) * depth_dark
    n1 = fbm(w, h, [16, 8, 4], rng, aspect=0.5, wrap_y=False)
    # ot dokusu: 2-4 piksellik dikey sap çizgileri (sütun başına kaydırılmış)
    g = rng.random((h // 3 + 3, w))
    co = rng.integers(0, 3, w)
    gi = g[((np.arange(h)[:, None] + co[None, :]) // 3), np.arange(w)[None, :]]
    lam = lam + (n1 - 0.5) * tex * 1.2 + (gi - 0.5) * tex * 1.6
    if streaks > 0:
        sw = fbm(w, h, [128, 64], rng, aspect=0.25, wrap_y=False)
        wave = np.sin((yy * 0.9 + sw * 40 + np.arange(w)[None, :] * 0.05) * 0.5)
        lam = lam + (wave > 0.75) * streaks
    if shadows > 0:
        cs = fbm(w, h, [300, 150, 75], rng, aspect=0.35, wrap_y=False)
        lam = lam - (cs > 0.58) * shadows
    b = bayer(h, w)
    col = ramp_pick(ramp, np.clip(lam, 0, 0.999), b, dither)
    L.rgba[inside, :3] = col[inside]
    L.rgba[inside, 3] = 1
    if grass is not None:
        # sırtta ot uçları: kısa dikey çizgiler (ışık tarafı açık)
        for x in range(0, w):
            if rng.random() < grass:
                hh = int(rng.integers(1, 5))
                y0 = int(ridge[x])
                for j in range(hh):
                    L.px(x, y0 - 1 - j, ramp[min(len(ramp) - 1, int(lam[min(h - 1, max(0, y0 + 2)), x] * len(ramp)) + (1 if j == hh - 1 else 0))])
    return inside


def kurgan(L, cx, base, rx, ry, ramp, light, rng, stones=None, grass_col=None):
    """Kurgan: geniş, basık höyük; ışık sağ üstten, eteğinde taş halkası."""
    xs, ys = L.grid(cx - rx - 1, base - ry - 2, cx + rx + 1, base + 1)
    X, Y = np.meshgrid(xs + 0.5 - cx, ys + 0.5 - base)
    u = X / rx; v = Y / ry
    m = (u * u + v * v <= 1) & (Y <= 0)
    nz = np.sqrt(np.clip(1 - u * u - v * v, 0, 1))
    lam = np.clip((u * light[0] + v * light[1] + nz * light[2]) * 0.55 + 0.45, 0, 1)
    lam += (rng.random(X.shape) - 0.5) * 0.12
    bb = BAYER8[ys[:, None] % 8, xs[None, :] % 8]
    col = ramp_pick(ramp, np.clip(lam, 0, 0.999), bb, 0.8)
    L.put(xs, ys, m, col)
    if stones is not None:
        for k in range(int(rx / 3)):
            t = rng.uniform(-1, 1)
            sx = cx + t * rx * 1.02
            sy = base - 1 + rng.uniform(-1, 1)
            L.px(sx, sy, stones[1]); L.px(sx + 1, sy, stones[2]); L.px(sx, sy - 1, stones[2]); L.px(sx - 1, sy, stones[0])


def balbal(L, x, base, hgt, ramp, face=True):
    """Balbal taşı: kaba yontulmuş, başlı dikili taş; sağ yüz aydınlık, sol yüz gölgede."""
    w = max(2, int(hgt * 0.32))
    for y in range(int(base - hgt), int(base) + 1):
        t = (y - (base - hgt)) / hgt
        head = t < 0.32
        ww = w * (0.8 if head else 1.0) if t > 0.05 else w * 0.5
        neck = 0.3 < t < 0.36
        if neck:
            ww = w * 0.65
        for dx in range(-int(ww), int(ww) + 1):
            side = dx / max(1, ww)
            c = ramp[1] if side < -0.35 else (ramp[3] if side > 0.4 else ramp[2])
            if dx == -int(ww):
                c = ramp[0]
            L.px(x + dx, y, c)
    if face and hgt >= 10:
        fy = base - hgt * 0.82
        L.px(x - 1, fy, ramp[0]); L.px(x + 1, fy, ramp[0])
        L.px(x, fy + 2, ramp[1]); L.px(x - 1, fy + hgt * 0.14, ramp[0]); L.px(x + 1, fy + hgt * 0.14, ramp[0])
        # elde kadeh (balbalların tipik duruşu)
        cy = base - hgt * 0.52
        for dx in range(-1, 2):
            L.px(x + dx, cy, ramp[3] if dx > 0 else ramp[1])


def yurt(L, x, base, s, felt, rng, smoke=None):
    """Uzak yurt: keçe gövde, kubbe, kapı, tünlük; isteğe bağlı duman."""
    w = s; hb = s * 0.42; hd = s * 0.34
    for y in range(int(base - hb - hd), int(base) + 1):
        if y > base - hb:
            half = w / 2
        else:
            t = (base - hb - y) / hd
            half = w / 2 * max(0.0, (1 - t * t)) ** 0.5
            if half < 1:
                half = 0.6
        for dx in range(-int(half), int(half) + 1):
            side = dx / max(1.0, half)
            c = felt[1] if side < -0.3 else (felt[3] if side > 0.35 else felt[2])
            if y <= base - hb and side > 0.0:
                c = felt[3] if y < base - hb - 1 else felt[2]
            L.px(x + dx, y, c)
    # kapı ve kuşak
    for y in range(int(base - hb * 0.7), int(base) + 1):
        L.px(x + 1, y, hexrgb('#7a2a1c')); L.px(x + 2, y, hexrgb('#5a1e14'))
    for dx in range(-int(w / 2), int(w / 2) + 1):
        L.px(x + dx, base - hb * 0.55, felt[1])
    L.px(x, base - hb - hd, felt[0])
    if smoke is not None:
        sx, sy = x, base - hb - hd - 1
        for k in range(int(s * 1.6)):
            sx += rng.uniform(-0.3, 0.9); sy -= 1
            L.px(sx, sy, smoke, 0.55 * (1 - k / (s * 1.6)))


def horse(L, x, y, col, rng, facing=1):
    """Uzak at silüeti (yaklaşık 7x5)."""
    pts = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (0, -1), (1, -1), (2, -1), (3, -1), (4, -1)]
    pts += [(5 * facing if facing > 0 else -1, -2), (5 if facing > 0 else -1, -1), (6 if facing > 0 else -2, -3), (5 if facing > 0 else -1, -3)]
    pts += [(0, 1), (0, 2), (4, 1), (4, 2), (1, 1), (3, 2)] if rng.random() < 0.5 else [(0, 1), (0, 2), (4, 1), (4, 2)]
    pts += [(-1, -1) if facing > 0 else (5, -1), (-1, 0) if facing > 0 else (5, 0)]
    for dx, dy in pts:
        L.px(x + dx, y + dy, col)


def spruce_big(L, x, base, hgt, ramp, light, rng, snow_ramp=None, trunk_ramp=None, width=0.32, rim_col=None):
    """Yakın plan ladin: gövdeden çıkan, önce sarkan sonra ucu kalkan dallar; dal kütlesi saçaklı iğne
    perdesi (alt kenardan sarkan iğne çizgileri), dallar arasında boşluk, üst yüzlerde kar yığını."""
    top = base - hgt
    if trunk_ramp is not None:
        L.tube([(x, base), (x, top + 10)], max(2.0, hgt * 0.022), 1.0, trunk_ramp, light)
    n = len(ramp)
    y = top + 2
    rows = []
    while y < base - hgt * 0.03:
        rows.append(y)
        t = (y - top) / hgt
        y += rng.uniform(16, 26) * (0.45 + t * 0.75)
    for ri, y0 in enumerate(rows):
        for side in (-1, 1):
            y = y0 + (0 if side < 0 else (rows[ri + 1] - y0) * rng.uniform(0.35, 0.65) if ri + 1 < len(rows) else 0)
            t = (y - top) / hgt
            wmax = hgt * width * (0.06 + 0.94 * min(1, t) ** 0.8)
            ln = wmax * rng.uniform(0.45, 1.1)
            droop = ln * rng.uniform(0.45, 0.8)
            lift = ln * rng.uniform(0.1, 0.22)
            th0 = max(3.5, hgt * 0.02) * rng.uniform(0.8, 1.2)
            steps = int(ln) + 1
            fr = rng.random(steps + 2)
            pts = []
            for k in range(steps):
                u = k / max(1, steps - 1)
                bx = x + side * k
                by = y + droop * (u ** 1.5) - lift * max(0.0, u - 0.7) * 3.3
                pts.append((bx, by, u))
                th = th0 * (1 - u * 0.5) + 1
                fringe = th * (0.3 + fr[k] * 0.7)
                for j in range(-int(th * 0.35), int(th + fringe) + 1):
                    if j > th and (k + j) % 2:
                        continue
                    lam = 0.36 + side * light[0] * 0.2 + (0.08 if j < 0 else -0.3 * min(1, j / max(1, th))) + u * 0.16
                    lam += (fr[(k + j) % (steps + 2)] - 0.5) * 0.2
                    L.px(bx, by + j, ramp[int(np.clip(lam * n, 0, n - 1))])
            if snow_ramp is not None and steps > 6:
                # kar topakları: dalın üstünde 1-3 öbek
                for _ in range(int(rng.integers(1, 4))):
                    a = int(rng.integers(0, max(1, steps - 4)))
                    cl = int(rng.integers(3, 9))
                    for k in range(a, min(steps, a + cl)):
                        bx, by, u = pts[k]
                        th = th0 * (1 - u * 0.5) + 1
                        sy = by - int(th * 0.35)
                        e = min(k - a, a + cl - 1 - k)
                        hh = 1 + (1 if e >= 1 else 0) + (1 if e >= 3 else 0)
                        for q in range(hh):
                            sc = snow_ramp[min(len(snow_ramp) - 1, 1 + q + (1 if side > 0 else 0))]
                            L.px(bx, sy - q, sc)
                        L.px(bx, sy + 1, snow_ramp[0])
            if rim_col is not None and side > 0:
                L.px(x + ln, y + droop, rim_col)
