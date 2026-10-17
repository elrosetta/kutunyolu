"""Stil v2 "mürekkep" biyom ortamları için ortak, biyomdan bağımsız çizim yardımcıları (Bozkır, Kaf Dağı ...).

otuken_ink.py'deki yardımcılar Ötüken'in gök rampasına (SKY) bağlıdır; buradakiler gök/sis rampasını parametre alır.
Hepsi önçarpılmış float RGBA (inkkit_ortam.Layer) üretir; yatay döşenen katmanlar kenarlardan sarılır.

İçerik: gök rampası, satır başına sis payı, sarma, dağ sırası (sırt çizgilerinden cel yüzey gölgesi + kar + mürekkep),
yumuşak tepe/kurgan siluetleri, boyalı bulut şeritleri, otluk, yer sisi / toz / kar tülü, hüzme, kar tanesi katmanı.
"""
import math

import numpy as np
import skia
from scipy import ndimage

import inkkit_ortam as ik
from inkkit_ortam import (INK, Layer, Sk, apply_fog, bezier, blade, blade_spine, blade_tip, blob, c01, fbm, mix,
                          noise, poly_path, premul, ribbon, smooth_path, smoothstep)

H = 1080
WL = 3840


# ------------------------------------------------------------------ gök / sis
def ramp(stops, n=H):
    ys = np.arange(n, dtype=np.float32)
    st = np.array([s[0] for s in stops], np.float32)
    cs = np.array([s[1] for s in stops], np.float32) / 255.0
    return np.stack([np.interp(ys, st, cs[:, k]) for k in range(3)], 1).astype(np.float32)


def fog_amount(base, band=0.0, center=610.0, width=80.0, top=0.0, top_end=380.0, n=H):
    ys = np.arange(n, dtype=np.float32)
    a = base + band * np.exp(-((ys - center) / width) ** 2)
    a += top * (1 - smoothstep(0, top_end, ys))
    return np.clip(a, 0, 0.97).astype(np.float32)


def fold(arr, pad, W):
    """pad'li (W + 2 pad) skia çiziminden döşenebilir çekirdek: taşan kenarlar öbür uca eklenir."""
    core = arr[:, pad:pad + W].copy()
    l, r = arr[:, :pad], arr[:, pad + W:]
    core[:, W - pad:] = l + core[:, W - pad:] * (1 - l[..., 3:4])
    core[:, :pad] = r + core[:, :pad] * (1 - r[..., 3:4])
    return core


def over(dst, src):
    return src + dst * (1 - src[..., 3:4])


def place(L, arr, x, y_base, sky=None, fog=None, sink=8):
    """Kökeni alt orta olan parçayı yerleştir (satır sisiyle)."""
    h, w = arr.shape[:2]
    a = arr.copy()
    yt = int(y_base - h / ik.K + sink)
    if fog is not None:
        apply_fog(a, int(yt * ik.K), sky, fog)
    L.over_wrap(a, int(x - w / ik.K / 2), yt)


# ------------------------------------------------------------------ dağ sırası
def _md_line(p0, p1, rough, seed, depth=6):
    """İki nokta arası orta nokta kaydırmalı kırık çizgi (dağ sırtı)."""
    rng = np.random.default_rng(seed)
    pts = [np.array(p0, np.float64), np.array(p1, np.float64)]
    amp = rough
    for _ in range(depth):
        out = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            m = (a + b) / 2
            d = b - a
            n = np.array([-d[1], d[0]]) / (np.hypot(*d) + 1e-6)
            m = m + n * rng.uniform(-amp, amp) * np.hypot(*d)
            out += [m, b]
        pts = out
        amp *= 0.62
    return np.array(pts)


def peak(W, sky, fog_y, ax, ay, by, wl, wr, seed, rock_lit, rock_sh, snow_lit, snow_sh, snow_line=0.35,
         ink_a=0.8, ink_w=2.2, n_ridges=6, rough=0.18, hatch=0.5, crease=0.35, rim=None, snow_amt=1.0,
         light=-1.0, streak=0.12, lit_k=1.0, gully_snow=0.6, sil_rim=None, sil_rim_w=2.0, sil_rim_a=0.9):
    """Tek dağ (cel gölgeli): siluet + tepeden inen sırtlar. Bir sırtın ışık tarafındaki yüz aydınlık, öbür yüz gölgede;
    sırtlar arası derede koyu kıvrım, gölge yüzlerde fırça taraması, kar çizgisinin üstünde (ve derelerde aşağı uzanan)
    kar. -> (önçarpılmış parça, x0, y0) çıktı pikseli."""
    rng = np.random.default_rng(seed)
    K = ik.K
    left = _md_line((ax - wl, by), (ax, ay), rough, seed + 1)
    right = _md_line((ax, ay), (ax + wr, by), rough, seed + 2)
    # tepe hep en yüksek nokta kalsın (masa dağı olmasın); siluet yamaç boyunca yalnızca aşağı iner
    left[:, 1] = np.maximum(left[:, 1], ay + (by - ay) * np.clip((ax - left[:, 0]) / max(wl, 1), 0, 1) * 0.55)
    right[:, 1] = np.maximum(right[:, 1], ay + (by - ay) * np.clip((right[:, 0] - ax) / max(wr, 1), 0, 1) * 0.55)
    sil = np.concatenate([left, right[1:], [(ax + wr, by + 40), (ax - wl, by + 40)]])
    x0 = int(ax - wl - 4)
    x1 = int(ax + wr + 4)
    y0 = int(min(sil[:, 1].min(), ay) - 4)
    y1 = int(by + 40)
    w, h = x1 - x0, y1 - y0
    s = Sk(w, h)
    s.path(poly_path(sil - [x0, y0]), (255, 255, 255))
    cov = s.mask()
    hp, wp = cov.shape
    ys = y0 + (np.arange(hp, dtype=np.float32) + 0.5) / K
    xs = x0 + (np.arange(wp, dtype=np.float32) + 0.5) / K
    # sırtlar: tepeden tabana (y'ye göre x), tabanda yayılır
    ridges = []
    bxs = np.sort(rng.uniform(ax - wl * 0.85, ax + wr * 0.85, n_ridges))
    for i, bx in enumerate(bxs):
        s0 = 0.0 if i % 2 == 0 or rng.random() < 0.4 else rng.uniform(0.1, 0.4)    # bazıları omuzdan başlar
        sa = np.clip((ys - ay) / max(1.0, by - ay), 0, 1)
        nz = noise(1, h, 10, seed + 10 + i, wrap=False)[:, 0] * (w * 0.035)
        xr = ax + (bx - ax) * sa ** rng.uniform(0.8, 1.3) + nz * sa
        valid = sa >= s0
        ridges.append((xr.astype(np.float32), valid))
    R = np.stack([r[0] for r in ridges], 0)                       # (n, hp)
    V = np.stack([r[1] for r in ridges], 0)
    dx = xs[None, None, :] - R[:, :, None]                        # (n, hp, wp)
    dist = np.where(V[:, :, None], np.abs(dx), 1e9)
    k = np.argmin(dist, 0)
    dmin = np.take_along_axis(dist, k[None], 0)[0]
    sgn = np.take_along_axis(dx, k[None], 0)[0]
    # ikinci en yakın sırta uzaklık -> dere (iki sırtın ortası)
    srt = np.sort(dist, 0)
    d2 = srt[1] if dist.shape[0] > 1 else np.full_like(dmin, 1e9)
    gap = np.minimum(dmin + d2, w)
    vt = np.clip(dmin / np.maximum(gap * 0.5, 1), 0, 1)              # 0 sırt, 1 dere
    # yokuşun ışık yönü: sırtın ışık tarafı (light=-1: ışık soldan -> sırtın solu aydınlık)
    lit = (sgn * light > 0).astype(np.float32)
    lit = ndimage.gaussian_filter(lit, 0.7 * K)
    # yamaç dokusu: yokuş boyunca uzayan fırça izi
    st = noise(w, h, 0, seed + 5, wrap=False, sx=3.0, sy=16)
    st2 = fbm(w, h, [24, 8], seed + 6, wrap=False)
    tone = lit * (0.92 + 0.12 * (1 - vt)) * lit_k + (1 - lit) * (0.95 - 0.1 * vt)
    rock = mix(c01(rock_sh)[None, None, :], c01(rock_lit)[None, None, :], lit[..., None])
    rock = rock * (tone * (1 + streak * st + 0.05 * st2))[..., None]
    # dere kıvrımı koyusu
    cr = smoothstep(0.75, 1.0, vt) * crease
    rock = rock * (1 - cr[..., None] * 0.6)
    # kar: tepe çizgisinin altına doğru azalır, derelerde aşağı uzar, gölge yüzlerde daha az
    sa = np.clip((ys - ay) / max(1.0, by - ay), 0, 1)[:, None]
    line = snow_line + 0.12 * st2 + 0.02 * st
    gl = snow_line + gully_snow * smoothstep(0.55, 1.0, vt) * (0.5 + 0.5 * st2)
    snow = np.maximum(1 - smoothstep(line - 0.04, line + 0.04, sa), 1 - smoothstep(gl - 0.05, gl, sa) * 1.0)
    snow *= np.clip(0.55 + 0.6 * lit + 0.2 * st, 0, 1)
    snow = np.clip(snow * snow_amt, 0, 1)
    snow = ndimage.gaussian_filter(snow, 0.5 * K)
    scol = mix(c01(snow_sh)[None, None, :], c01(snow_lit)[None, None, :], lit[..., None])
    scol = scol * (1 + 0.04 * st)[..., None]
    rgb = mix(rock, scol, snow[..., None])
    if rim is not None:
        # sırt üstünde ince ışık kenarı (ışık tarafında)
        rr = (1 - smoothstep(0.0, 2.2, dmin * K / K)) * lit * 0.8
        rgb = mix(rgb, c01(rim)[None, None, :], rr[..., None])
    arr = premul(rgb.astype(np.float32), cov)
    # mürekkep: siluet, kesik sırt çizgileri, gölge taraması
    sk = Sk(w, h)
    if ink_a > 0:
        lp = left - [x0, y0]
        rp = right - [x0, y0]
        for line_pts in (lp, rp):
            wd = ink_w * (0.6 + 0.8 * np.abs(ik.noise_base(1, len(line_pts), 3, seed + 20, wrap=False)[:, 0]))
            sk.path(ribbon(line_pts, wd), INK, ink_a)
        for (xr, valid), i in zip(ridges, range(len(ridges))):
            idx = np.nonzero(valid)[0]
            if len(idx) < 8:
                continue
            j0 = idx[0]
            seg_len = len(idx)
            pos = j0
            while pos < j0 + seg_len - 4:
                ln = int(rng.uniform(0.08, 0.3) * seg_len)
                if rng.random() < 0.6:
                    q = np.arange(pos, min(pos + ln, j0 + seg_len - 1))
                    if len(q) > 3:
                        pts = np.stack([xr[q] - x0, ys[q] - y0], 1)
                        wd = np.sin(np.linspace(0, math.pi, len(q))) * ink_w * rng.uniform(0.5, 1.0) + 0.2
                        sk.path(ribbon(pts[::max(1, len(q) // 10)], wd[::max(1, len(q) // 10)]), INK, ink_a * 0.8)
                pos += ln + int(rng.uniform(0.05, 0.2) * seg_len)
        if hatch > 0:
            for _ in range(int(w * h / 900 * hatch)):
                px_ = rng.uniform(0, w)
                py_ = rng.uniform(0, h)
                iy, ix = int(py_ * K), int(px_ * K)
                if iy >= hp or ix >= wp or cov[iy, ix] < 0.9 or lit[iy, ix] > 0.3 or snow[iy, ix] > 0.5:
                    continue
                ln = rng.uniform(5, 14)
                pts = [(px_, py_), (px_ + light * -ln * 0.25, py_ + ln * 0.5), (px_ + light * -ln * 0.45, py_ + ln)]
                sk.path(ribbon(pts, [0.2, 1.0, 0.2]), INK, ink_a * rng.uniform(0.3, 0.55))
    if sil_rim is not None:
        # güneşe bakan siluet kenarında parlak ışık çizgisi (ters ışıkta dağı gökten koparır)
        rl = (right if light > 0 else left) - [x0, y0]
        wd = sil_rim_w * (0.4 + 0.9 * np.abs(ik.noise_base(1, len(rl), 4, seed + 31, wrap=False)[:, 0]))
        sk.path(ribbon(rl + [-light * sil_rim_w * 0.4, sil_rim_w * 0.5], wd), sil_rim, sil_rim_a)
    marks = sk.snap() * cov[..., None]
    arr = over(arr, marks)
    yy = int(y0 * K)
    apply_fog(arr, yy, sky, fog_y)
    return arr, int(x0 * K), yy


def range_layer(L, sky, peaks, fog_fn, seed, **kw):
    """Dağ listesini (ax, ay, by, wl, wr) sırayla (arkadan öne) katmana çiz; her dağın sisi fog_fn(i) ile."""
    rng = np.random.default_rng(seed)
    for i, p in enumerate(peaks):
        args = dict(kw)
        if len(p) > 5:
            args.update(p[5])
        arr, x0, y0 = peak(L.w, sky, fog_fn(i), *p[:5], seed=int(rng.integers(1 << 30)), **args)
        for dx in (-L.w, 0, L.w):
            if x0 + dx < L.w and x0 + dx + arr.shape[1] > 0:
                L.over(arr, x0 + dx, y0, px=True)


# ------------------------------------------------------------------ yumuşak tepe / kurgan
def hills(L, sky, seed, base_y, amp, n_waves, col_lit, col_sh, fog, light=-1.0, ink_a=0.0, ink_w=2.0, tex=0.08,
          grass=None, rim=None, bottom=H + 10):
    """Yuvarlak bozkır tepeleri: dalgalı üst kenar, ışık tarafına bakan yamaç açık, öbür yamaç gölgede (cel)."""
    W = L.w / ik.K
    rng = np.random.default_rng(seed)
    xs = np.linspace(0, W, 600)
    prof = np.zeros_like(xs)
    for k in range(n_waves):
        f = rng.uniform(1, 5) * 2 * math.pi / W
        f = round(f * W / (2 * math.pi)) * 2 * math.pi / W   # döşenebilir frekans
        prof += np.sin(xs * f + rng.uniform(0, 6.28)) * rng.uniform(0.4, 1.0) / (1 + k * 0.6)
    prof = prof / (np.abs(prof).max() + 1e-6)
    top = base_y - amp * (0.5 + 0.5 * prof)
    slope = np.gradient(top, xs)
    pts = list(zip(xs, top)) + [(W, bottom), (0, bottom)]
    s = Sk(W, H)
    s.path(poly_path(pts), (255, 255, 255))
    cov = s.mask()
    px = (np.arange(L.w, dtype=np.float32) + 0.5) / ik.K
    sl = np.interp(px, xs, slope)
    tp = np.interp(px, xs, top)
    ys = (np.arange(L.h, dtype=np.float32)[:, None] + 0.5) / ik.K
    depth = np.clip((ys - tp[None, :]) / 60.0, 0, 1)
    # yamaç yönü: ışık soldan (light=-1) -> sol yamaç (yükselen, slope<0) aydınlık
    litv = smoothstep(-0.05, 0.25, sl * light)
    lit = np.broadcast_to(litv[None, :], cov.shape) * (1 - 0.5 * depth)
    nz = fbm(W, H, [40, 12], seed + 3)
    st = noise(W, H, 0, seed + 4, sx=10, sy=1.5)
    rgb = mix(c01(col_sh)[None, None, :], c01(col_lit)[None, None, :], lit[..., None])
    rgb *= (1 + tex * nz + 0.5 * tex * st)[..., None]
    if rim is not None:
        r = (1 - smoothstep(0, 3.0, ys - tp[None, :])) * (0.4 + 0.6 * litv[None, :])
        rgb = mix(rgb, c01(rim)[None, None, :], (r * 0.7)[..., None])
    arr = premul(rgb.astype(np.float32), cov)
    if ink_a > 0:
        sk = Sk(W, H)
        tpts = np.array(list(zip(xs, top)))
        wd = ink_w * (0.5 + 0.9 * np.abs(ik.noise_base(1, len(tpts), 6, seed + 9, wrap=False)[:, 0]))
        i = 0
        while i < len(tpts) - 3:
            ln = int(rng.integers(12, 60))
            seg = slice(i, min(len(tpts), i + ln))
            q = tpts[seg]
            if len(q) > 3:
                ww = wd[seg] * np.sin(np.linspace(0.15, math.pi - 0.15, len(q))) ** 0.5
                for dx in (-W, 0, W):
                    sk.path(ribbon(q + [dx, 0], ww), INK, ink_a)
            i += ln + int(rng.integers(2, 25))
        arr = over(arr, sk.snap())
    apply_fog(arr, 0, sky, fog)
    L.over(arr)
    return top, xs


def cloud_bands(L, sky, seed, y_rng, n, col_top, col_under, col_rim, fog=None, ink_a=0.0, length=(400, 1100),
                thick=(18, 46), alpha=0.95, W=None):
    """Boyalı uzun bulut şeritleri (alacakaranlık): üstleri gökle karışan koyu, altları güneşle yanan; ince mürekkep
    alt kenar. Yatayda döşenir."""
    W = W or L.w / ik.K
    rng = np.random.default_rng(seed)
    pad = 600
    s = Sk(W + 2 * pad, H)
    ink_sk = Sk(W + 2 * pad, H)
    for _ in range(n):
        cx = rng.uniform(0, W) + pad
        cy = rng.uniform(*y_rng)
        ln = rng.uniform(*length)
        th = rng.uniform(*thick)
        # alt kenar: düz ve uzun, üst kenar kabarık
        nb = 18
        bx = np.linspace(cx - ln / 2, cx + ln / 2, nb)
        by = cy + np.sin(np.linspace(0, math.pi, nb)) * th * 0.15 + rng.uniform(-2, 2, nb)
        tx = np.linspace(cx + ln / 2, cx - ln / 2, nb)
        ty = cy - th * (np.sin(np.linspace(0, math.pi, nb)) ** 0.6) * rng.uniform(0.5, 1.1, nb)
        pts = list(zip(bx, by)) + list(zip(tx, ty))
        p = smooth_path(pts, True, 0.45)
        s.path(p, col_top, alpha, 1.5)
        # altın alt kenar (güneş alttan)
        und = list(zip(bx, by)) + list(zip(bx[::-1], by[::-1] - th * rng.uniform(0.18, 0.35)))
        s.path(smooth_path(und, True, 0.4), col_under, alpha, 1.0)
        s.path(ribbon(np.stack([bx, by - 1.2], 1), np.sin(np.linspace(0, math.pi, nb)) * 2.2 + 0.3), col_rim, alpha * 0.9)
        # iç fırça izleri (yatay)
        for k in range(int(ln / 60)):
            yy = cy - rng.uniform(0.2, 0.8) * th
            xx = rng.uniform(cx - ln * 0.4, cx + ln * 0.3)
            l2 = rng.uniform(40, 140)
            s.path(ribbon([(xx, yy), (xx + l2 * 0.5, yy + rng.uniform(-2, 2)), (xx + l2, yy + rng.uniform(-1, 3))],
                          [0.3, rng.uniform(2, 5), 0.3]), tuple(np.array(col_under) * 0.85 + np.array(col_top) * 0.15), 0.45)
        if ink_a > 0:
            q = np.stack([bx, by + 0.6], 1)
            ink_sk.path(ribbon(q[2:-2], np.sin(np.linspace(0, math.pi, nb - 4)) * 1.6 + 0.2), INK, ink_a)
    arr = fold(s.snap(), int(pad * ik.K), L.w)
    if ink_a > 0:
        arr = over(arr, fold(ink_sk.snap(), int(pad * ik.K), L.w))
    if fog is not None:
        apply_fog(arr, 0, sky, fog)
    L.over(arr)


def _shift(m, dx, dy):
    """maskeyi (dx, dy) piksel kaydırılmış konumdan oku (dışarısı 0)."""
    out = np.zeros_like(m)
    h, w = m.shape
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    out[ys0:ys1, xs0:xs1] = m[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return out


def cloud_masses(L, sky, seed, clouds, col_top, col_mid, col_under, col_rim, sun=(0.6, 0.8), fog=None, ink_a=0.0,
                 alpha=1.0, wrap=True, under_d=(10, 26), rim_w=0.12, soft=1.2, **_):
    """Boyalı kümülüs / tabaka bulut kütleleri (çizgi roman bulutu): düz, hafif dalgalı taban üstünde arkadan öne üst üste
    binen kabarcıklar. Her kabarcık kendi küresel cel gölgesiyle boyanır (güneşe bakan yanı turuncu, en dış kenarı
    altın ışık, sırtı gökle karışan mor); taban şeridi alttan güneşle yanar. clouds: [(cx, cy_taban, genişlik, yükseklik)]."""
    rng = np.random.default_rng(seed)
    K = ik.K
    W = L.w / ik.K
    ux, uy = sun
    nrm = math.hypot(ux, uy)
    ux, uy = ux / nrm, uy / nrm
    acc = np.zeros((L.h, L.w, 4), np.float32)
    ct, cm, cu, cr = (c01(c) for c in (col_top, col_mid, col_under, col_rim))
    for cx, cy, cw, ch in clouds:
        n = int(max(5, cw / ch * 3.0))
        blobs = []
        for i in range(n):
            t = (i + 0.5) / n
            env = math.sin(math.pi * t) ** 0.7
            r = ch * (0.32 + 0.6 * env) * rng.uniform(0.65, 1.0)
            blobs.append((cx - cw / 2 + t * cw + rng.uniform(-0.3, 0.3) * cw / n, cy - r * rng.uniform(0.3, 0.7), r, 1))
        for i in range(max(2, n // 2)):
            t = rng.uniform(0.15, 0.85)
            env = math.sin(math.pi * t)
            r = ch * 0.5 * env * rng.uniform(0.6, 1.0) + ch * 0.12
            blobs.insert(0, (cx - cw / 2 + t * cw, cy - ch * 0.55 * env - r * 0.25, r, 0))
        # tabanın altı kesilir (hafif dalgalı)
        x0 = int((cx - cw / 2 - ch) * K)
        x1 = int((cx + cw / 2 + ch) * K)
        y0 = int((cy - ch * 1.6) * K)
        y1 = int((cy + 4) * K)
        xs = (np.arange(x0, x1, dtype=np.float32) + 0.5) / K
        ys = (np.arange(y0, y1, dtype=np.float32) + 0.5) / K
        X, Y = np.meshgrid(xs, ys)
        base = cy + 2.5 * np.sin(X / 37.0 + cx) + 1.5 * np.sin(X / 13.0)
        cut = np.clip((base - Y) * K / soft + 0.5, 0, 1)
        patch = np.zeros(X.shape + (4,), np.float32)
        for bx, by, r, row in blobs:
            dx_ = (X - bx) / r
            dy_ = (Y - by) / r
            d = np.sqrt(dx_ * dx_ + dy_ * dy_)
            cov = np.clip((1 - d) * r * K / soft + 0.5, 0, 1) * cut
            if cov.max() <= 0:
                continue
            ndl = dx_ * ux + dy_ * uy                     # güneşe bakış (-1..1)
            tone = smoothstep(-0.1, 0.25, ndl)
            rim = smoothstep(0.62, 0.9, ndl) * smoothstep(0.6, 0.92, d)
            top = smoothstep(0.1, 0.9, -dy_) * (1 - tone)
            rgb = mix(cm[None, None, :], ct[None, None, :], (top * 0.7)[..., None])
            rgb = mix(rgb, cu[None, None, :], (tone * (0.75 if row else 0.55))[..., None])
            rgb = mix(rgb, cr[None, None, :], (rim * 0.9)[..., None])
            src = premul(rgb.astype(np.float32), cov)
            patch = over(patch, src)
        # alttan yanan taban şeridi
        und = smoothstep(base - ch * 0.22, base - 1.0, Y) * patch[..., 3]
        pr = patch[..., :3] / np.maximum(patch[..., 3:4], 1e-5)
        pr = mix(pr, cu[None, None, :] * 1.05, (und * 0.7)[..., None])
        pr = mix(pr, cr[None, None, :], (smoothstep(base - 3.5, base - 0.5, Y) * patch[..., 3] * 0.8)[..., None])
        patch = premul(pr.astype(np.float32), patch[..., 3])
        if ink_a > 0:
            sk = Sk((x1 - x0) / K, (y1 - y0) / K)
            q = np.stack([np.linspace(cw * 0.1, cw * 0.9, 14) + ch, cy - y0 / K + 1 + rng.uniform(-0.6, 0.6, 14)], 1)
            sk.path(ribbon(q, np.sin(np.linspace(0, math.pi, 14)) * 1.5 + 0.2), INK, ink_a)
            patch = over(patch, sk.snap()[:patch.shape[0], :patch.shape[1]])
        patch *= alpha
        for dx in ((-L.w, 0, L.w) if wrap else (0,)):
            xa, xb = max(0, x0 + dx), min(L.w, x1 + dx)
            ya, yb = max(0, y0), min(L.h, y1)
            if xb <= xa or yb <= ya:
                continue
            sub = patch[ya - y0:yb - y0, xa - x0 - dx:xb - x0 - dx]
            acc[ya:yb, xa:xb] = over(acc[ya:yb, xa:xb], sub)
    if fog is not None:
        apply_fog(acc, 0, sky, fog)
    L.over(acc)


def grass_field(L, sky, seed, y0, y1, density, col_top, col_bot, hmin, hmax, wmin=2.0, wmax=4.5, fog=None,
                lean=0.35, lean_bias=0.0, dark_strokes=0.25, light_strokes=0.2, fill=True, fill_blur=3, ink_tips=0.0,
                rim=None, rim_p=0.0, plumes=0.0, plume_col=(230, 210, 170)):
    """Otluk (otuken_ink.grass_field genellemesi): rüzgâr eğimi (lean_bias), ışık kenarlı yapraklar (rim), sorguç başlı
    kılçık otu (plumes: bozkırın "ak otu" / sorguçlu kılçık otu)."""
    rng = np.random.default_rng(seed)
    W = L.w / ik.K
    pad = 80
    out = np.zeros((L.h, L.w, 4), np.float32)
    if fill:
        sk = Sk(W + 2 * pad, H)
        top = [(x + pad, y0 + 8 + rng.uniform(-6, 6)) for x in np.linspace(-pad, W + pad, 120)]
        pts = top + [(W + 2 * pad, H + 10), (0, H + 10)]
        sk.path(smooth_path(pts, True, 0.3), (255, 255, 255), 1.0, fill_blur)
        fillm = sk.mask()[:, int(pad * ik.K):int(pad * ik.K) + L.w]
        ys = (np.arange(L.h, dtype=np.float32) + 0.5) / ik.K
        grad = mix(c01(col_top)[None, :], c01(col_bot)[None, :], smoothstep(y0, y1, ys)[:, None])
        rgb = np.repeat(grad[:, None, :], L.w, 1)
        nz = fbm(W, H, [30, 10], seed + 1)
        rgb *= (1 + 0.07 * nz[..., None])
        out = premul(rgb, fillm)
    sk2 = Sk(W + 2 * pad, H)
    count = int(density * W)
    for _ in range(count):
        x = rng.uniform(-pad, W + pad) + pad
        y = rng.uniform(y0, y1 + 30)
        depth = smoothstep(y0, y1, y)
        h = rng.uniform(hmin, hmax) * (0.7 + 0.6 * depth)
        r = rng.random()
        base_c = mix(c01(col_top), c01(col_bot), depth)
        if r < dark_strokes:
            c = base_c * rng.uniform(0.45, 0.7)
        elif r < dark_strokes + light_strokes:
            c = np.minimum(base_c * rng.uniform(1.18, 1.45) + 0.03, 1)
        else:
            c = base_c * rng.uniform(0.85, 1.1)
        ln_, wd_ = rng.uniform(-lean, lean) + lean_bias, rng.uniform(wmin, wmax)
        if rim is not None and rng.random() < rim_p:
            sk2.path(blade(x - 1.0, y, h, ln_, wd_), rim, rng.uniform(0.6, 0.9))
        sk2.path(blade(x, y, h, ln_, wd_), tuple(c * 255), rng.uniform(0.75, 1.0))
        if ink_tips > 0 and rng.random() < ink_tips:
            sk2.path(blade_tip(x, y, h, ln_, wd_, rng.uniform(0.18, 0.4)), INK, rng.uniform(0.5, 0.85))
        elif ink_tips > 0 and rng.random() < ink_tips * 0.6:
            sk2.path(blade_spine(x, y, h, ln_, wd_, side=1.0 if ln_ < 0 else -1.0), INK, rng.uniform(0.4, 0.7))
        if plumes > 0 and rng.random() < plumes:
            # sorguç: yaprağın ucundan rüzgâr yönüne savrulan tüylü kılçık
            tip = (x + ln_ * h, y - h)
            pl = rng.uniform(0.5, 1.0) * h * 0.7
            q = bezier(tip, (tip[0] + lean_bias * pl * 1.4 + pl * 0.3 * np.sign(lean_bias + 1e-3), tip[1] - pl * 0.1),
                       (tip[0] + np.sign(lean_bias + 1e-3) * pl, tip[1] + pl * 0.35), 8)
            pc = np.array(plume_col, np.float32) / 255 * (0.8 + 0.3 * (1 - depth))
            sk2.path(ribbon(q, np.sin(np.linspace(0.2, math.pi * 0.95, 8)) * wd_ * 1.1 + 0.3), tuple(pc * 255), 0.8)
    bl = sk2.snap()[:, int(pad * ik.K):int(pad * ik.K) + L.w]
    out = over(out, bl)
    if fog is not None:
        apply_fog(out, 0, sky, fog)
    L.over(out)


# ------------------------------------------------------------------ hava katmanları
def veil(W, sky, seed, bands, col_mix, tint, alpha, sx=(140, 50), sy=(16, 8), streaks=0.0, streak_sx=260):
    """Sis / toz / kar tülü: yatayda uzun gürültü şeritleri. bands: [(merkez, genişlik, ağırlık)]."""
    ys = ik.axis(H)[:, None]
    n1 = noise(W, H, 0, seed, sx=sx[0], sy=sy[0])
    n2 = noise(W, H, 0, seed + 1, sx=sx[1], sy=sy[1])
    band = sum(wt * np.exp(-((ys - c) / wd) ** 2) for c, wd, wt in bands)
    a = band * np.clip(0.55 + 0.6 * n1 + 0.25 * n2, 0, 1)
    if streaks > 0:
        n3 = noise(W, H, 0, seed + 2, sx=streak_sx, sy=1.2)
        a = a * (1 - streaks) + band * np.clip(n3 * 2.2 - 0.6, 0, 1) * streaks
    a = np.clip(a * alpha, 0, 0.92).astype(np.float32)
    rgb = np.repeat(ik.hd_lin(sky)[:, None, :], ik.P(W), 1) * (1 - col_mix) + c01(tint)[None, None, :] * col_mix
    L = Layer(W, H)
    L.a = premul(rgb, a)
    return L


def rays(W, seed, ang_deg, col, n=7, wid=(50, 170), inten=(0.25, 0.6), fade=(0.0, 0.1, 0.5, 0.74), origin=None,
         blend=200):
    """Toplamalı ışık hüzmeleri. origin=(x, y) verilirse hüzmeler o noktadan yelpaze açılır (alçak güneş)."""
    out = np.zeros((ik.P(H), ik.P(W)), np.float32)
    rng = np.random.default_rng(seed)
    ys = ik.axis(H)[:, None]
    xs = ik.axis(W)[None, :]
    if origin is None:
        ang = math.radians(ang_deg)
        u_all = xs * math.cos(ang) + ys * math.sin(ang)
        # aralık temel piksel ızgarasından (HD'de aynı hüzme konumları)
        ub = np.arange(W, dtype=np.float32)[None, :] * math.cos(ang) + np.arange(H, dtype=np.float32)[:, None] * math.sin(ang)
        umin, umax = float(ub.min()), float(ub.max())
        for _ in range(n):
            u0 = rng.uniform(umin + 200, umax - 100)
            out += np.exp(-((u_all - u0) / rng.uniform(*wid)) ** 2) * rng.uniform(*inten)
        streak = np.interp(u_all, np.linspace(umin, umax, 4096), ik.noise_base(4096, 1, 0, seed + 3, sx=3.0, sy=0.01)[0])
        v = ys / H
        f = smoothstep(fade[0], fade[1], v) * (1 - smoothstep(fade[2], fade[3], v))
    else:
        ox, oy = origin
        th = np.arctan2(ys - oy, xs - ox)
        rr = np.hypot(xs - ox, ys - oy)
        for _ in range(n):
            t0 = rng.uniform(-math.pi * 0.95, math.pi * 0.95)
            dt = np.angle(np.exp(1j * (th - t0)))
            out += np.exp(-(dt / rng.uniform(*wid)) ** 2) * rng.uniform(*inten)
        streak = np.interp(th, np.linspace(-math.pi, math.pi, 4096), ik.noise_base(4096, 1, 0, seed + 3, sx=4.0, sy=0.01)[0])
        f = smoothstep(fade[0], fade[1], rr) * (1 - smoothstep(fade[2], fade[3], rr))
    brk = np.clip(0.75 + 0.5 * noise(W, H, 0, seed + 5, sx=60, sy=90), 0.3, 1.0)
    out *= f * (0.85 + 0.25 * streak) * brk
    out = np.clip(out, 0, 1)
    if blend:
        bp = ik.P(blend)
        t = np.clip(ik.axis(blend) / (blend - 1), 0, 1)[None, :]
        out[:, :bp] = out[:, :bp] * t + out[:, -bp:] * (1 - t)
        out = out[:, :out.shape[1] - bp]
    rgb = c01(col)[None, None, :] * out[..., None]
    L = Layer(W - (blend or 0), H)
    L.a = np.concatenate([rgb, out[..., None]], -1).astype(np.float32)
    return L


def snowfall(W, Hh, seed, n, rmin, rmax, col=(240, 246, 255), blur=0.0, streak=0.0, ang=0.35, alpha=(0.5, 1.0),
             ink_p=0.0):
    """Döşenebilir (yatay + dikey) kar tanesi katmanı; streak > 0 rüzgârda çizgi gibi uzar."""
    rng = np.random.default_rng(seed)
    s = Sk(W, Hh)
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(0, Hh)
        r = rng.uniform(rmin, rmax) ** 1.0
        a = rng.uniform(*alpha)
        for dx in (-W, 0, W):
            for dy in (-Hh, 0, Hh):
                xx, yy = x + dx, y + dy
                if -40 < xx < W + 40 and -40 < yy < Hh + 40:
                    if streak > 0:
                        ln = r * streak
                        p = ribbon([(xx - math.cos(ang) * ln, yy - math.sin(ang) * ln), (xx, yy)], [r * 0.4, r * 1.6])
                        s.path(p, col, a, blur)
                    else:
                        s.c.drawCircle(xx, yy, r, s.paint(col, a, blur))
                        if ink_p > 0 and rng.random() < ink_p:
                            s.c.drawCircle(xx, yy, r, s.paint(INK, 0.35, 0, 0.6))
    L = Layer(W, Hh)
    L.a = s.snap()
    return L
