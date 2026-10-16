"""inkfx: stil v2 mürekkep fırçası efekt dokuları (savuruş izi, vuruş sıçrantısı, kesik izi, yer sıçrantısı, ensō).

Renk YOK: dokular veri taşır, renk oyunda `shaders/ink_brush.gdshader` / `ink_fx.gdshader` paletinden gelir
(kızıl mürekkep, od, ayaz, zehir, ruh ...). Hepsi yordamsal (numpy + scipy + skia), dışarıdan doku yok.

assets/fx/ink/bristle.png  512x128, u (yatay) = fırça boyunca (sarar), v (dikey) = fırça enine (0 iç, 1 dış)
    R  kıl yükü: enine dar kıl şeritleri, boyuna yavaş değişen yük ve kuru fırça boşlukları (eşik yükseldikçe
       fırça şeritlere ayrılır)
    G  koyu mürekkep çizgileri: kalın baş + incelen kuyruklu kısa koyu darbeler (referanstaki siyah fırça izleri)
    B  kıl kimliği: her enine satırın rastgele değeri (kuyrukta kılların farklı boyda bitmesi, erime sırası)
    A  ince tane (kâğıt / mürekkep tanesi), kenar pürüzü
assets/fx/ink/ink_fx.png  1024x1024 atlas (ink_fx.json: ad -> [x, y, w, h] piksel)
    R  işaretli uzaklık alanı (0,5 = kenar, ±10 px geçiş): her ölçekte temiz kenar; eşik kaydırılınca şekil
       incelir ve parçalanır (mürekkebin çekilmesi)
    G  koyu mürekkep maskesi (gövdede siyah çekirdek / çizgiler)
    B  çizim sırası (0 önce .. 1 sonra): açılış animasyonu (patlama merkezden dışa, kesik bir uçtan öbürüne,
       ensō açı boyunca)
    A  erime gürültüsü

Kullanım: cd tools/artgen && python inkfx.py [--onizleme out.png]
"""
import json
import math
import os
import sys

import numpy as np
import skia
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'assets', 'fx', 'ink')


# ------------------------------------------------------------------ gürültü
def fft_noise(h, w, beta=2.0, seed=0, fx=1.0, fy=1.0):
    """Her iki eksende sarmalı (periyodik) 1/f^beta gürültüsü, [0,1]. fx/fy > 1: o eksende daha ince yapı."""
    rng = np.random.default_rng(seed)
    wn = rng.standard_normal((h, w))
    F = np.fft.fft2(wn)
    ky = np.fft.fftfreq(h)[:, None] * fy
    kx = np.fft.fftfreq(w)[None, :] * fx
    k = np.sqrt(kx * kx + ky * ky)
    k[0, 0] = 1.0
    F *= 1.0 / (k ** (beta * 0.5))
    F[0, 0] = 0
    n = np.real(np.fft.ifft2(F))
    n = (n - n.min()) / (n.max() - n.min() + 1e-9)
    return n


def periodic_1d(n, seed, kmax=7, amp_pow=1.2):
    """Periyodik 1B gürültü (tam sayı frekanslı sinüsler), [-1, 1]."""
    rng = np.random.default_rng(seed)
    x = np.arange(n) / n
    out = np.zeros(n)
    for k in range(1, kmax + 1):
        out += rng.standard_normal() / k ** amp_pow * np.sin(2 * math.pi * k * x + rng.uniform(0, 2 * math.pi))
    out /= np.abs(out).max() + 1e-9
    return out


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ kıl dokusu
def bristle(W=512, H=128, seed=11):
    rng = np.random.default_rng(seed)
    y = np.arange(H)[:, None] + 0.5
    R = np.zeros((H, W))
    # kıllar: enine dar Gauss şeritleri, boyuna yük değişimi ve kuru boşluklar
    nb = 120
    for j in range(nb):
        v0 = rng.uniform(-2, H + 2)
        wid = rng.uniform(0.7, 3.2) * (1.6 if rng.random() < 0.15 else 1.0)
        load = rng.uniform(0.35, 1.0)
        m = periodic_1d(W, seed * 1000 + j, kmax=9)
        g = periodic_1d(W, seed * 1000 + j + 500, kmax=5)
        a = np.clip(0.62 + 0.5 * m, 0, 1) * load
        gap = smoothstep(-0.55, -0.25, g)          # kuru boşluk: yük sıfıra iner
        a = a * (0.15 + 0.85 * gap)
        prof = np.exp(-((y - v0) / wid) ** 2)
        R = np.maximum(R, prof * a[None, :])
    base = fft_noise(H, W, beta=2.4, seed=seed + 1, fx=0.35, fy=2.0)  # boyuna uzamış yumuşak taban
    R = np.clip(0.30 * base + 0.85 * R, 0, 1)
    # koyu mürekkep darbeleri (G): kalın sivri baş (u büyük = fırçanın taze ucu yönü), uzun incelen kuyruk;
    # az sayıda ve kalın (referanstaki koyu kızıl fırça izleri), boyuna sarar
    G = np.zeros((H, W))
    xs = np.arange(W)[None, :] + 0.5
    for j in range(9):
        u0 = rng.uniform(0, W)
        v0 = rng.uniform(0.22, 0.78) * H
        L = rng.uniform(70, 210)
        th = rng.uniform(4.0, 11.0)
        bend = rng.uniform(-10, 10)
        for wrap in (-W, 0, W):
            t = ((u0 + wrap) - xs) / L          # 0 baş .. 1 kuyruk (u azalan yönde)
            inside_t = (t >= -0.08) & (t <= 1.0)
            tc = np.clip(t, 0, 1)
            prof = np.where(t < 0, np.clip(1 + t / 0.08, 0, 1) ** 0.5, (1 - tc) ** 1.3 * np.clip(tc * 6 + 0.35, 0, 1)) * th
            yc = v0 + bend * tc * tc
            d = np.abs(y - yc)
            G = np.maximum(G, np.where(inside_t, smoothstep(prof + 0.9, prof - 0.5, d), 0))
    # ince koyu kıl çizgileri (seyrek)
    for j in range(12):
        v0 = rng.uniform(0.15, 0.85) * H
        m = periodic_1d(W, seed * 77 + j, kmax=6)
        G = np.maximum(G, 0.45 * np.exp(-((y - v0) / 0.9) ** 2) * smoothstep(0.45, 0.8, m)[None, :])
    G = np.clip(G, 0, 1)
    # kıl kimliği (B): satır başına rastgele, hafif boyuna kayma
    row = rng.random(H)
    row = ndimage.uniform_filter1d(row, 2, mode='wrap')
    drift = periodic_1d(W, seed + 9, kmax=3)[None, :] * 0.08
    B = np.clip(row[:, None] + drift, 0, 1)
    A = fft_noise(H, W, beta=1.3, seed=seed + 3, fx=0.6, fy=1.0)
    return np.dstack([R, G, B, A])


# ------------------------------------------------------------------ şekil araçları (skia, 2x süper örnekleme)
SS = 2


def _surface(w, h):
    s = skia.Surface(w * SS, h * SS)
    c = s.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    c.scale(SS, SS)
    return s, c


def _paint(a=1.0):
    p = skia.Paint(AntiAlias=True, Color=skia.Color4f(1, 1, 1, a))
    return p


def _arr(s):
    img = s.makeImageSnapshot()
    a = np.asarray(img.toarray())[..., 3].astype(float) / 255.0
    return a


def taper(c, pts, w0, w1, wmid=None, n=48, cap=True):
    """Çoklu nokta boyunca incelen fırça darbesi (dolu yol). w(t): w0 -> (wmid) -> w1."""
    P = np.array(pts, float)
    # Catmull-Rom yumuşatma
    if len(P) > 2:
        Q = []
        for i in range(len(P) - 1):
            p0 = P[max(0, i - 1)]; p1 = P[i]; p2 = P[i + 1]; p3 = P[min(len(P) - 1, i + 2)]
            for t in np.linspace(0, 1, 10, endpoint=False):
                t2 = t * t; t3 = t2 * t
                Q.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
        Q.append(P[-1])
        P = np.array(Q)
    seg = np.hypot(*(P[1:] - P[:-1]).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    t = cum / max(cum[-1], 1e-6)
    if wmid is None:
        w = w0 + (w1 - w0) * t
    else:
        w = np.where(t < 0.4, w0 + (wmid - w0) * smoothstep(0, 0.4, t), wmid + (w1 - wmid) * smoothstep(0.4, 1.0, t))
    tg = np.gradient(P, axis=0)
    tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-9
    nrm = np.stack([-tg[:, 1], tg[:, 0]], 1)
    L = P + nrm * (w[:, None] * 0.5)
    R = P - nrm * (w[:, None] * 0.5)
    path = skia.Path()
    path.moveTo(*L[0])
    for q in L[1:]:
        path.lineTo(*q)
    for q in R[::-1]:
        path.lineTo(*q)
    path.close()
    c.drawPath(path, _paint())
    if cap:
        c.drawCircle(P[0][0], P[0][1], w[0] * 0.5, _paint())


def blob(c, cx, cy, r, rng, k=9, jit=0.22):
    """Düzensiz yuvarlak leke."""
    n = 36
    ang = np.linspace(0, 2 * math.pi, n, endpoint=False)
    ph = rng.uniform(0, 6.28, 3)
    rr = r * (1 + jit * (0.6 * np.sin(3 * ang + ph[0]) + 0.3 * np.sin(5 * ang + ph[1]) + 0.25 * np.sin(k * ang + ph[2])))
    pts = np.stack([cx + rr * np.cos(ang), cy + rr * np.sin(ang)], 1)
    path = skia.Path()
    # yumuşak kapalı yol (orta noktalar arası quad)
    m = (pts + np.roll(pts, -1, 0)) * 0.5
    path.moveTo(*m[-1])
    for i in range(n):
        path.quadTo(*pts[i], *m[i])
    path.close()
    c.drawPath(path, _paint())


def drop(c, x, y, r, ang=0.0, stretch=1.0):
    """Damla: hareket yönünde uzamış elips (kuyruklu)."""
    c.save()
    c.translate(x, y)
    c.rotate(math.degrees(ang))
    c.drawOval(skia.Rect.MakeLTRB(-r * stretch, -r, r * stretch * 0.8, r), _paint())
    c.restore()


def field(cov_hi, noise_amp=0.0, noise=None, spread=9.0):
    """Yüksek çözünürlüklü kaplamadan işaretli uzaklık alanı -> 1x, [0,1] (0,5 kenar)."""
    inside = cov_hi > 0.5
    d_in = ndimage.distance_transform_edt(inside)
    d_out = ndimage.distance_transform_edt(~inside)
    sd = (d_in - d_out) / SS
    if noise is not None:
        sd = sd + noise_amp * (noise - 0.5)
    sd = sd.reshape(sd.shape[0] // SS, SS, sd.shape[1] // SS, SS).mean(axis=(1, 3))
    return np.clip(0.5 + sd / (2 * spread), 0, 1)


def down(a):
    return a.reshape(a.shape[0] // SS, SS, a.shape[1] // SS, SS).mean(axis=(1, 3))


def polar(w, h, cx, cy):
    ys, xs = np.mgrid[0:h, 0:w] + 0.5
    dx, dy = xs - cx, ys - cy
    return np.hypot(dx, dy), np.arctan2(dy, dx)


def radial_streaks(w, h, cx, cy, seed, n_ang=90):
    """Açıda ince, yarıçapta yavaş değişen gürültü (ışınsal kıl çizgileri)."""
    r, a = polar(w, h, cx, cy)
    nz = fft_noise(64, 512, beta=1.8, seed=seed, fx=0.25, fy=1.0)  # satır = yarıçap, sütun = açı
    ai = ((a / (2 * math.pi)) % 1.0) * 512
    ri = np.clip(r / max(w, h) * 64 * 1.6, 0, 63)
    return ndimage.map_coordinates(nz, [ri, ai], order=1, mode='wrap')


# ------------------------------------------------------------------ şekiller
def shape_burst(size, seed, n_spk=9, len_r=(0.26, 0.47), wid=(0.05, 0.11), core=0.15, drops=True, dirk=0.0):
    """Mürekkep patlama yıldızı: düzensiz çekirdek + incelen ışınsal fırça dikenleri + damlalar.
    dirk > 0: dikenler +x yönünde uzar (yönlü sıçrama)."""
    rng = np.random.default_rng(seed)
    S = size
    s, c = _surface(S, S)
    cx = cy = S * 0.5
    blob(c, cx, cy, S * core, rng, jit=0.28)
    ang0 = rng.uniform(0, 6.28)
    dark = _surface(S, S)
    for i in range(n_spk):
        a = ang0 + i * 2 * math.pi / n_spk + rng.uniform(-0.25, 0.25)
        dirw = 1 + dirk * math.cos(a)
        L = S * rng.uniform(*len_r) * dirw
        L = min(L, S * 0.49)
        w0 = S * rng.uniform(*wid) * (0.8 + 0.4 * dirw)
        bend = rng.uniform(-0.18, 0.18)
        pts = []
        for t in np.linspace(0.0, 1.0, 5):
            aa = a + bend * t * t
            pts.append((cx + math.cos(aa) * L * t, cy + math.sin(aa) * L * t))
        taper(c, pts, w0, 0.6, wmid=w0 * 0.75)
        if drops and rng.random() < 0.85:
            for k in range(rng.integers(1, 4)):
                rr = L + S * rng.uniform(0.02, 0.07) * (k + 1)
                if rr > S * 0.47:
                    break
                dr = S * rng.uniform(0.008, 0.022) / (1 + 0.5 * k)
                drop(c, cx + math.cos(a) * rr, cy + math.sin(a) * rr, dr, a, 1.5)
        # koyu çekirdek darbesi (dikenin iç yarısı)
        taper(dark[1], [(cx, cy), (cx + math.cos(a) * L * 0.55, cy + math.sin(a) * L * 0.55)], w0 * 0.45, 0.4)
    blob(dark[1], cx, cy, S * core * 0.7, rng, jit=0.35)
    cov = _arr(s)
    nz = radial_streaks(S * SS, S * SS, cx * SS, cy * SS, seed + 5)
    R = field(cov, 5.0, nz)
    G = down(_arr(dark[0]))
    G = np.clip(G * (0.55 + 0.6 * down(nz)), 0, 1)
    r, _ = polar(S, S, cx, cy)
    B = np.clip(r / (S * 0.48) * 0.85 + 0.15 * down(nz), 0, 1)
    A = fft_noise(S, S, beta=1.6, seed=seed + 9)
    return np.dstack([R, G, B, A])


def shape_stamp(size, seed):
    """Kritik mürekkep damgası: ağır, kaba kenarlı büyük leke + birkaç kalın diken + sıçrantı noktaları."""
    rng = np.random.default_rng(seed)
    S = size
    s, c = _surface(S, S)
    cx = cy = S * 0.5
    blob(c, cx, cy, S * 0.23, rng, k=11, jit=0.2)
    for i in range(7):
        a = rng.uniform(0, 6.28)
        L = S * rng.uniform(0.3, 0.46)
        w0 = S * rng.uniform(0.07, 0.13)
        taper(c, [(cx, cy), (cx + math.cos(a) * L * 0.5, cy + math.sin(a) * L * 0.5), (cx + math.cos(a + 0.1) * L, cy + math.sin(a + 0.1) * L)], w0, 0.8, wmid=w0 * 0.8)
    for i in range(22):
        a = rng.uniform(0, 6.28)
        rr = S * rng.uniform(0.28, 0.47)
        drop(c, cx + math.cos(a) * rr, cy + math.sin(a) * rr, S * rng.uniform(0.006, 0.02), a, rng.uniform(1, 2.2))
    cov = _arr(s)
    nz = radial_streaks(S * SS, S * SS, cx * SS, cy * SS, seed + 2)
    R = field(cov, 7.0, nz)
    r, _ = polar(S, S, cx, cy)
    G = np.clip(1.0 - smoothstep(S * 0.3, S * 0.45, r) * 0.6, 0, 1)   # hemen hepsi siyah, uçlar renkli
    B = np.clip(r / (S * 0.48) * 0.9 + 0.1 * down(nz), 0, 1)
    A = fft_noise(S, S, beta=1.5, seed=seed + 4)
    return np.dstack([R, G, B, A])


def shape_dab(size, seed):
    """Fırça dokunuşu: yuvarlak dolu baş + kıvrık incelen kuyruk, kuru kıl çizgileri."""
    rng = np.random.default_rng(seed)
    S = size
    s, c = _surface(S, S)
    a = rng.uniform(-0.3, 0.3)
    p0 = np.array([S * 0.22, S * 0.55])
    pts = [p0]
    for t in (0.33, 0.66, 1.0):
        pts.append(p0 + np.array([math.cos(a + 0.5 * t * t), math.sin(a + 0.5 * t * t)]) * S * 0.62 * t)
    taper(c, pts, S * 0.26, S * 0.01, wmid=S * 0.2)
    cov = _arr(s)
    # boyuna kıl çizgileri: yaklaşık x yönünde uzamış gürültü
    nz = fft_noise(S * SS, S * SS, beta=1.6, seed=seed + 1, fx=0.12, fy=1.6)
    R = field(cov, 9.0, nz)
    G = np.clip(smoothstep(0.62, 0.8, down(nz)) * smoothstep(0.55, 0.75, R), 0, 1)
    ys, xs = np.mgrid[0:S, 0:S] + 0.5
    B = np.clip((xs - S * 0.1) / (S * 0.8), 0, 1)
    A = fft_noise(S, S, beta=1.5, seed=seed + 2)
    return np.dstack([R, G, B, A])


def shape_drops(size, seed):
    rng = np.random.default_rng(seed)
    S = size
    s, c = _surface(S, S)
    for i in range(26):
        a = rng.uniform(0, 6.28)
        rr = S * 0.42 * math.sqrt(rng.random())
        x, y = S * 0.5 + math.cos(a) * rr, S * 0.5 + math.sin(a) * rr
        drop(c, x, y, S * rng.uniform(0.008, 0.035), a, rng.uniform(1.0, 2.0))
    cov = _arr(s)
    R = field(cov, 0.0, None, spread=6.0)
    r, _ = polar(S, S, S * 0.5, S * 0.5)
    B = np.clip(r / (S * 0.45), 0, 1)
    A = fft_noise(S, S, beta=1.5, seed=seed + 2)
    G = np.zeros_like(R)
    return np.dstack([R, G, B, A])


def shape_enso(size, seed):
    """Ensō: açı boyunca kalınlaşıp incelen, kuru boşluklu daire fırça darbesi (savuşturma / kusursuz kaçış)."""
    rng = np.random.default_rng(seed)
    S = size
    s, c = _surface(S, S)
    cx = cy = S * 0.5
    R0 = S * 0.37
    a0 = math.radians(-70)
    span = math.radians(330)
    pts = []
    for t in np.linspace(0, 1, 40):
        a = a0 + span * t
        rr = R0 * (1 + 0.04 * math.sin(t * 7 + 1) + 0.03 * t)
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    taper(c, pts, S * 0.085, S * 0.008, wmid=S * 0.075)
    cov = _arr(s)
    rr, aa = polar(S * SS, S * SS, cx * SS, cy * SS)
    nz = radial_streaks(S * SS, S * SS, cx * SS, cy * SS, seed)
    # açı boyunca kıl çizgileri: yarıçapta ince, açıda uzun
    nz2 = fft_noise(512, 64, beta=1.7, seed=seed + 3, fx=1.0, fy=0.12)
    ri = np.clip(rr / (S * SS * 0.5) * 511, 0, 511)
    ai = ((aa / (2 * math.pi)) % 1.0) * 64
    st = ndimage.map_coordinates(nz2, [ri, ai], order=1, mode='wrap')
    R = field(cov, 7.0, st)
    G = down(smoothstep(0.66, 0.8, st)) * 0.8
    r1, a1 = polar(S, S, cx, cy)
    B = ((a1 - a0) % (2 * math.pi)) / span
    B = np.clip(B, 0, 1)
    A = fft_noise(S, S, beta=1.5, seed=seed + 5)
    return np.dstack([R, G, B, A])


def shape_cut(w, h, seed, split=True):
    """Kesik izi: iki ucu iğne gibi incelen, %35'te en kalın mercek çizgi + ince yan yarık + kopan zerreler.
    Yatay: x 0 -> 1 kesiğin çizim yönü."""
    rng = np.random.default_rng(seed)
    s, c = _surface(w, h)
    y0 = h * 0.5
    pts = [(w * 0.03, y0 + h * 0.06), (w * 0.35, y0), (w * 0.7, y0 - h * 0.03), (w * 0.97, y0 - h * 0.08)]
    taper(c, pts, 0.6, 0.5, wmid=h * 0.16, cap=False)
    core = _surface(w, h)
    taper(core[1], pts, 0.3, 0.3, wmid=h * 0.05, cap=False)
    if split:
        p2 = [(w * 0.18, y0 + h * 0.2), (w * 0.45, y0 + h * 0.13), (w * 0.72, y0 + h * 0.1)]
        taper(c, p2, 0.4, 0.4, wmid=h * 0.045, cap=False)
    for i in range(10):
        x = w * rng.uniform(0.3, 0.95)
        drop(c, x, y0 + h * rng.uniform(-0.32, 0.32), h * rng.uniform(0.012, 0.03), rng.uniform(-0.4, 0.4), 2.2)
    cov = _arr(s)
    nz = fft_noise(h * SS, w * SS, beta=1.6, seed=seed + 1, fx=0.1, fy=1.5)
    R = field(cov, 3.0, nz, spread=6.0)
    G = down(_arr(core[0]))          # burada G = sıcak çekirdek (oyunda beyaz-sıcak)
    ys, xs = np.mgrid[0:h, 0:w] + 0.5
    B = np.clip(xs / w, 0, 1)
    A = fft_noise(h, w, beta=1.5, seed=seed + 2)
    return np.dstack([R, G, B, A])


def shape_claw(size, seed):
    """Üç paralel kısa kesik (pençe / ikiz bıçak)."""
    rng = np.random.default_rng(seed)
    S = size
    s, c = _surface(S, S)
    core = _surface(S, S)
    for k in range(3):
        off = (k - 1) * S * 0.17
        p = [(S * 0.12 + off * 0.4, S * 0.78 + off), (S * 0.5 + off * 0.2, S * 0.5 + off), (S * 0.9, S * 0.2 + off)]
        taper(c, p, 0.5, 0.5, wmid=S * (0.075 if k == 1 else 0.055), cap=False)
        taper(core[1], p, 0.3, 0.3, wmid=S * 0.02, cap=False)
    cov = _arr(s)
    nz = fft_noise(S * SS, S * SS, beta=1.6, seed=seed + 1)
    R = field(cov, 3.0, nz, spread=6.0)
    G = down(_arr(core[0]))
    ys, xs = np.mgrid[0:S, 0:S] + 0.5
    B = np.clip(((xs - ys) / S + 1) * 0.5, 0, 1)
    B = (B - B.min()) / (B.max() - B.min())
    A = fft_noise(S, S, beta=1.5, seed=seed + 2)
    return np.dstack([R, G, B, A])


def shape_ground(w, h, seed):
    """Yer sıçrantısı: zemin boyunca kuru fırça sürtmesi + yukarı yelpaze damlalar ve dikenler. Taban y = 0,82h."""
    rng = np.random.default_rng(seed)
    s, c = _surface(w, h)
    dark = _surface(w, h)
    gy = h * 0.82
    cx = w * 0.5
    # yassı ana leke
    blob(c, cx, gy - h * 0.02, h * 0.1, rng, jit=0.3)
    c.drawOval(skia.Rect.MakeLTRB(cx - w * 0.16, gy - h * 0.06, cx + w * 0.16, gy + h * 0.05), _paint())
    # koyu: temas noktasından yukarı fırlayan dikenlerin kökü (çukur gibi okunan yatay leke değil)
    for i in range(6):
        a = -math.pi / 2 + rng.uniform(-0.9, 0.9)
        taper(dark[1], [(cx, gy), (cx + math.cos(a) * h * 0.25, gy + math.sin(a) * h * 0.25)], h * 0.05, 0.4)
    # iki yana sürtme (incelen)
    for side in (-1, 1):
        for k in range(3):
            yy = gy + h * rng.uniform(-0.05, 0.05)
            taper(c, [(cx, yy), (cx + side * w * 0.25, yy + h * 0.01), (cx + side * w * rng.uniform(0.38, 0.47), yy - h * 0.01)],
                  h * rng.uniform(0.06, 0.1), 0.6, cap=False)
    # yukarı dikenler / yelpaze
    for i in range(13):
        a = -math.pi / 2 + rng.uniform(-1.25, 1.25)
        L = h * rng.uniform(0.3, 0.72) * (1 - 0.35 * abs(math.sin(a + math.pi / 2)))
        x0 = cx + rng.uniform(-w * 0.1, w * 0.1)
        taper(c, [(x0, gy), (x0 + math.cos(a) * L * 0.6, gy + math.sin(a) * L * 0.6), (x0 + math.cos(a) * L, gy + math.sin(a) * L)],
              h * rng.uniform(0.04, 0.075), 0.5, wmid=h * 0.035)
        for k in range(rng.integers(0, 3)):
            rr = L * (1.12 + 0.18 * k)
            drop(c, x0 + math.cos(a) * rr, gy + math.sin(a) * rr, h * rng.uniform(0.008, 0.02), a, 1.6)
    for i in range(7):
        x = cx + w * rng.uniform(-0.46, 0.46)
        drop(c, x, gy - h * rng.uniform(0.02, 0.4) * (1 - abs(x - cx) / w), h * rng.uniform(0.006, 0.018), -math.pi / 2, 1.3)
    cov = _arr(s)
    nz = fft_noise(h * SS, w * SS, beta=1.6, seed=seed + 1, fx=0.15, fy=1.4)
    R = field(cov, 6.0, nz)
    G = np.clip(down(_arr(dark[0])) * 0.9 + smoothstep(0.7, 0.85, down(nz)) * smoothstep(0.6, 0.75, R) * 0.6, 0, 1)
    ys, xs = np.mgrid[0:h, 0:w] + 0.5
    B = np.clip(np.hypot((xs - cx) / (w * 0.5), (ys - gy) / (h * 0.8)), 0, 1)
    A = fft_noise(h, w, beta=1.5, seed=seed + 2)
    return np.dstack([R, G, B, A])


def shape_spray(size, seed):
    """Yönlü sıçrantı: soldan sağa yelpaze çizgiler + uçlarında damlalar (ağır vuruşta düşmanın arkasına)."""
    rng = np.random.default_rng(seed)
    S = size
    s, c = _surface(S, S)
    x0, y0 = S * 0.06, S * 0.5
    for i in range(16):
        a = rng.uniform(-0.55, 0.55)
        L = S * rng.uniform(0.4, 0.86)
        bend = rng.uniform(-0.1, 0.25)
        pts = [(x0 + math.cos(a + bend * t * t) * L * t, y0 + math.sin(a + bend * t * t) * L * t) for t in np.linspace(0.1, 1, 4)]
        taper(c, pts, S * rng.uniform(0.02, 0.05), 0.5, wmid=S * 0.03)
        for k in range(rng.integers(1, 3)):
            rr = L * (1.06 + 0.08 * k)
            if rr < S * 0.9:
                drop(c, x0 + math.cos(a + bend) * rr, y0 + math.sin(a + bend) * rr, S * rng.uniform(0.006, 0.016), a, 1.8)
    blob(c, x0 + S * 0.06, y0, S * 0.07, rng)
    cov = _arr(s)
    nz = fft_noise(S * SS, S * SS, beta=1.6, seed=seed + 1, fx=0.15, fy=1.3)
    R = field(cov, 3.0, nz, spread=6.0)
    ys, xs = np.mgrid[0:S, 0:S] + 0.5
    B = np.clip((xs - x0) / (S * 0.9), 0, 1)
    G = np.clip(smoothstep(0.55, 0.0, B) * smoothstep(0.55, 0.7, R), 0, 1)
    A = fft_noise(S, S, beta=1.5, seed=seed + 2)
    return np.dstack([R, G, B, A])


def shape_shard(size, seed):
    """Savuşturma kıvılcımı: dört uçlu keskin fırça yıldızı (yatay uzun) + ince ara ışınlar."""
    rng = np.random.default_rng(seed)
    S = size
    s, c = _surface(S, S)
    cx = cy = S * 0.5
    for a, L, w in ((0, 0.47, 0.07), (math.pi, 0.47, 0.07), (math.pi / 2, 0.3, 0.06), (-math.pi / 2, 0.3, 0.06)):
        taper(c, [(cx, cy), (cx + math.cos(a) * S * L, cy + math.sin(a) * S * L)], S * w, 0.4)
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2 + rng.uniform(-0.1, 0.1)
        taper(c, [(cx, cy), (cx + math.cos(a) * S * 0.2, cy + math.sin(a) * S * 0.2)], S * 0.035, 0.3)
    blob(c, cx, cy, S * 0.06, rng)
    cov = _arr(s)
    R = field(cov, 0.0, None, spread=6.0)
    r, _ = polar(S, S, cx, cy)
    G = np.clip(1 - r / (S * 0.12), 0, 1)
    B = np.clip(r / (S * 0.47), 0, 1)
    A = fft_noise(S, S, beta=1.5, seed=seed + 2)
    return np.dstack([R, G, B, A])


def shape_ring(size, seed):
    """Kuru fırça halkası (şok / savuşturma dalgası): ince, boşluklu, bir yanda kalın."""
    rng = np.random.default_rng(seed)
    S = size
    s, c = _surface(S, S)
    cx = cy = S * 0.5
    pts = []
    a0 = rng.uniform(0, 6.28)
    for t in np.linspace(0, 1, 48):
        a = a0 + 2 * math.pi * 0.97 * t
        pts.append((cx + math.cos(a) * S * 0.44, cy + math.sin(a) * S * 0.44))
    taper(c, pts, S * 0.03, S * 0.006, wmid=S * 0.035)
    cov = _arr(s)
    rr, aa = polar(S * SS, S * SS, cx * SS, cy * SS)
    nz2 = fft_noise(512, 64, beta=1.7, seed=seed + 3, fx=1.0, fy=0.12)
    st = ndimage.map_coordinates(nz2, [np.clip(rr / (S * SS * 0.5) * 511, 0, 511), ((aa / (2 * math.pi)) % 1.0) * 64], order=1, mode='wrap')
    R = field(cov, 4.0, st, spread=5.0)
    r1, a1 = polar(S, S, cx, cy)
    B = ((a1 - a0) % (2 * math.pi)) / (2 * math.pi)
    G = np.zeros_like(R)
    A = fft_noise(S, S, beta=1.5, seed=seed + 5)
    return np.dstack([R, G, B, A])


# ------------------------------------------------------------------ atlas
def build_atlas():
    C = 256
    atlas = np.zeros((1024, 1024, 4))
    meta = {}

    def put(name, arr, x, y):
        h, w = arr.shape[:2]
        atlas[y:y + h, x:x + w] = arr
        meta[name] = [x, y, w, h]

    put('burst_a', shape_burst(C, 3, n_spk=8, len_r=(0.28, 0.47), wid=(0.07, 0.12)), 0, 0)
    put('burst_b', shape_burst(C, 7, n_spk=13, len_r=(0.22, 0.48), wid=(0.035, 0.07), core=0.12), C, 0)
    put('burst_dir', shape_burst(C, 19, n_spk=11, len_r=(0.18, 0.34), wid=(0.04, 0.09), core=0.11, dirk=0.75), 2 * C, 0)
    put('stamp', shape_stamp(C, 23), 3 * C, 0)
    put('dab_a', shape_dab(C, 31), 0, C)
    put('dab_b', shape_dab(C, 37), C, C)
    put('drops', shape_drops(C, 41), 2 * C, C)
    put('enso', shape_enso(C, 43), 3 * C, C)
    put('cut_a', shape_cut(2 * C, C // 2, 47), 0, 2 * C)
    put('cut_b', shape_cut(2 * C, C // 2, 53, split=False), 0, 2 * C + C // 2)
    put('spray', shape_spray(C, 59), 2 * C, 2 * C)
    put('shard', shape_shard(C, 61), 3 * C, 2 * C)
    put('ground', shape_ground(2 * C, C, 67), 0, 3 * C)
    put('ring', shape_ring(C, 71), 2 * C, 3 * C)
    put('claw', shape_claw(C, 73), 3 * C, 3 * C)
    return atlas, meta


def save_rgba(arr, path):
    a = (np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(a, 'RGBA').save(path, optimize=True)


IMPORT = """[remap]

importer="texture"
type="CompressedTexture2D"

[deps]

source_file="res://assets/fx/ink/{name}"

[params]

compress/mode=0
compress/high_quality=false
compress/lossy_quality=0.7
compress/hdr_compression=1
compress/normal_map=2
compress/channel_pack=0
mipmaps/generate=true
mipmaps/limit=-1
roughness/mode=0
roughness/src_normal=""
process/channel_remap/red=0
process/channel_remap/green=1
process/channel_remap/blue=2
process/channel_remap/alpha=3
process/fix_alpha_border=false
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_as_srgb=false
process/hdr_clamp_exposure=false
process/size_limit=0
detect_3d/compress_to=0
"""


def preview(atlas, br, path):
    """Veri dokularını kızıl paletle boyayıp görselleştirir (geliştirme için)."""
    def col(R, G, th=0.5):
        a = smoothstep(th - 0.04, th + 0.04, R)
        body = np.array([0.89, 0.09, 0.06]); ink = np.array([0.06, 0.02, 0.03]); rim = np.array([1.0, 0.42, 0.1])
        c = body[None, None] * smoothstep(0.5, 0.62, R)[..., None] + rim[None, None] * (1 - smoothstep(0.5, 0.62, R))[..., None]
        c = c * (1 - G[..., None]) + ink[None, None] * G[..., None]
        bg = np.array([0.35, 0.42, 0.33])
        return c * a[..., None] + bg[None, None] * (1 - a[..., None])
    A = col(atlas[..., 0], atlas[..., 1])
    Bv = np.dstack([br[..., 0], br[..., 1], br[..., 2]])
    Bv = np.kron(Bv, np.ones((2, 1, 1)))
    out = np.zeros((1024 + 256 + 8, 1024, 3))
    out[:1024] = A
    out[1032:1032 + 256, :512] = Bv
    out[1032:1032 + 256, 512:] = np.kron(br[..., 3:4].repeat(3, 2), np.ones((2, 1, 1)))
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    br = bristle()
    save_rgba(br, os.path.join(OUT, 'bristle.png'))
    atlas, meta = build_atlas()
    save_rgba(atlas, os.path.join(OUT, 'ink_fx.png'))
    with open(os.path.join(OUT, 'ink_fx.json'), 'w', encoding='utf-8') as f:
        json.dump({'size': [1024, 1024], 'shapes': meta}, f, indent=1)
    for nm in ('bristle.png', 'ink_fx.png'):
        ip = os.path.join(OUT, nm + '.import')
        if not os.path.exists(ip):
            with open(ip, 'w', encoding='utf-8') as f:
                f.write(IMPORT.format(name=nm))
    if '--onizleme' in sys.argv:
        preview(atlas, br, sys.argv[sys.argv.index('--onizleme') + 1])
    print('inkfx: bristle.png, ink_fx.png (%d şekil)' % len(meta))


if __name__ == '__main__':
    main()
