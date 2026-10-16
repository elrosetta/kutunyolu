"""Stil v2 "mürekkep" yeraltı takımı: Şahmeran Mağaraları ve Tamu (Erlik'in Ülkesi) için ortak çizim parçaları.

inkkit_ortam üstüne kurulur (önçarpılmış float RGBA, skia yolları, mantıksal piksel x K). Burada yalnızca yeraltına
özgü biçimler var: sarkıt/dikit (analitik koni gölgesi), kristal kümesi (yüzeyli prizma + ışıma), su yansıması,
zincir (sarkan katener halkalar), bazalt prizması (altıgen sütun, üç yüz), kemik kaburga, lav şelalesi, duman.
Ötüken dosyalarına dokunmaz.
"""
import math

import numpy as np
from scipy import ndimage

import inkkit_ortam as ik
from inkkit_ortam import (INK, Layer, Sk, bezier, blob, c01, fbm, mix, noise, poly_path, premul, ribbon, smooth_path,
                          smoothstep, trunk)

H = 1080
WL = 3840


# ------------------------------------------------------------------ renk rampası / sis
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


def fog(arr, y0, sky, amount):
    """inkkit_ortam.apply_fog, satırlar ÇIKTI pikseli (K=1 paralaks)."""
    return ik.apply_fog(arr, y0, sky, amount)


def wrap_core(arr, pad, W):
    """pad'li çizimi W genişliğe sar: taşan kenarlar öbür uca."""
    core = arr[:, pad:pad + W].copy()
    l, r = arr[:, :pad], arr[:, pad + W:]
    core[:, W - pad:] = l + core[:, W - pad:] * (1 - l[..., 3:4])
    core[:, :pad] = r + core[:, :pad] * (1 - r[..., 3:4])
    return core


def tint_rows(arr, y0, k_top, k_bot, y_a, y_b):
    """parçayı satıra göre karart/aydınlat (önçarpılmış rgb çarpanı)."""
    h = arr.shape[0]
    ys = np.arange(y0, y0 + h, dtype=np.float32)
    k = k_top + (k_bot - k_top) * smoothstep(y_a, y_b, ys)
    arr[..., :3] *= k[:, None, None]
    return arr


# ------------------------------------------------------------------ sarkıt / dikit
def spike(base_y, x, length, width, seed, rock=(60, 70, 76), light=(120, 150, 150), rim=(120, 230, 200),
          ink_w=2.0, detail=0.7, hang=False, light_side=-1.0, taper=0.93, lean=0.0):
    """Dikit (yukarı sivrilen koni) ya da hang=True ile sarkıt. Ağaç gövdesi gölgelemesini kullanır (silindirik ışık,
    arkadan kenar ışığı, iki yanda değişken mürekkep, boyuna akıntı çizgileri). -> (arr, xl, yt) mantıksal konum."""
    arr, xl, yt = trunk(H, WL, base_y, x, width, seed, kind='pine', lean=lean, bend=0.0, top_y=base_y - length,
                        bark=rock, light=light, rim=rim, ink_w=ink_w, light_side=light_side, detail=detail,
                        taper=taper)
    if hang:
        arr = arr[::-1].copy()
        h = arr.shape[0] / ik.K
        # sarkıt: taban üstte (base_y yerine tavan çizgisi), uç aşağıda
        yt = base_y - (base_y - yt) - 0  # aynı kutu; çağıran yerleştirir
    return arr, xl, yt


def lathe(y0, y1, cx_fn, hw_fn, seed, rock=(60, 70, 76), light=(120, 150, 150), rim=(120, 230, 200), ink_w=2.0,
          detail=0.8, light_side=-1.0, rings=0.5, wet=0.5, ink=INK, hatch=True):
    """Dönel katı (sarkıt, dikit, kum saati sütun): her satırda merkez cx_fn(y) ve yarı genişlik hw_fn(y) (mantıksal,
    y dizisi alır). Silindirik ışık, arkadan kenar ışığı, ıslak parlak şerit, boyuna akıntı çizgileri ve halka
    çıkıntıları, iki yanda değişken mürekkep, gölge tarafında tarama. -> (önçarpılmış dizi, x sol, y üst) mantıksal."""
    rng = np.random.default_rng(seed)
    hh = y1 - y0
    HP = ik.P(hh)
    ys = y0 + (np.arange(HP, dtype=np.float32) + 0.5) / ik.K
    cx = np.asarray(cx_fn(ys), np.float32)
    hw = np.maximum(np.asarray(hw_fn(ys), np.float32), 0.0)
    xl = int(np.floor((cx - hw).min())) - 6
    xr = int(np.ceil((cx + hw).max())) + 6
    ww = xr - xl
    xs = xl + (np.arange(ik.P(ww), dtype=np.float32)[None, :] + 0.5) / ik.K
    dx = xs - cx[:, None]
    hwc = hw[:, None]
    cov = np.clip((hwc - np.abs(dx)) * ik.K + 0.5, 0, 1)
    u = np.clip(dx / np.maximum(hwc, 0.5), -1, 1)
    sz = np.sqrt(np.clip(1 - u * u, 0, 1))
    lam = np.clip(0.5 + 0.55 * (-u * light_side) * 0.8 + 0.3 * sz, 0, 1.25)
    col = c01(rock)[None, None, :] * (0.5 + 0.62 * lam[..., None])
    nz = noise(ww, hh, 1.4, seed + 3, wrap=False, sx=1.0, sy=10.0)
    nz2 = noise(ww, hh, 3, seed + 5, wrap=False, sx=4, sy=26)
    col *= (1 + (0.14 * nz[..., None] + 0.08 * nz2[..., None]) * detail)
    # halka çıkıntıları: yatay açık/koyu bantlar
    if rings > 0:
        rp = noise(1, hh, 0, seed + 7, wrap=False, sx=0.01, sy=5)[:, 0]
        ring = np.clip(rp * 1.8, -1, 1)[:, None]
        col *= (1 + 0.12 * rings * ring * sz)[..., None]
    rimb = smoothstep(0.6, 0.93, u * (-light_side)) * (1 - smoothstep(0.93, 1.0, u * (-light_side)))
    col = mix(col, c01(rim)[None, None, :], (rimb * 0.6)[..., None])
    hl = smoothstep(0.25, 0.6, -u * light_side) * (1 - smoothstep(0.62, 0.85, -u * light_side))
    col = mix(col, c01(light)[None, None, :] * 1.1, (hl * (0.25 + 0.35 * wet) * (0.7 + 0.3 * nz2))[..., None])
    # ıslak parıltı: ışık tarafında ince, kesik dikey parlak çizgi
    if wet > 0:
        sp = smoothstep(0.5, 0.55, -u * light_side) * (1 - smoothstep(0.6, 0.66, -u * light_side)) * np.clip(nz2 * 2, 0, 1)
        col = mix(col, c01(light)[None, None, :] * 1.5, (sp * wet * 0.7)[..., None])
    iw = ink_w * (0.75 + 0.5 * (noise(1, hh, 14, seed + 9, wrap=False)[:, 0] * 0.5 + 0.5))
    edge_d = hwc - np.abs(dx)
    iwc = np.where(dx * light_side > 0, iw[:, None] * 0.8, iw[:, None] * 1.2)
    ink_m = np.clip((iwc - edge_d) * ik.K + 0.5, 0, 1) * cov
    col = mix(col, c01(ink)[None, None, :], ink_m[..., None])
    out = premul(col, cov)
    sk = Sk(ww, hh)
    # boyuna akıntı darbeleri
    for _ in range(int(hh / 7 * detail)):
        yy = rng.uniform(0, hh)
        iy = int(np.clip(yy * ik.K, 0, HP - 1))
        w_here = hw[iy]
        if w_here < 2:
            continue
        off = rng.uniform(-0.85, 0.85)
        xa = cx[iy] - xl + off * w_here
        ln = rng.uniform(6, 24)
        pts = [(xa + rng.uniform(-0.5, 0.5), yy + ln * s) for s in np.linspace(0, 1, 4)]
        ws = np.sin(np.linspace(0, 1, 4) * math.pi) * rng.uniform(0.6, 1.8) * (0.5 + 0.7 * abs(off)) + 0.2
        sk.path(ribbon(pts, ws), ink, rng.uniform(0.25, 0.6) * detail)
    if hatch and detail > 0.45:
        yy = rng.uniform(0, 20)
        while yy < hh:
            if rng.random() < 0.6:
                for k in range(int(rng.integers(3, 7))):
                    y_ = yy + k * rng.uniform(4.5, 7)
                    iy = int(np.clip(y_ * ik.K, 0, HP - 1))
                    w_here = hw[iy]
                    if w_here < 4:
                        continue
                    edge_x = cx[iy] - xl - light_side * w_here
                    ln = w_here * rng.uniform(0.3, 0.6)
                    x_in = edge_x + light_side * ln
                    sk.path(ribbon([(edge_x, y_ + ln * 0.3), ((edge_x + x_in) / 2, y_ + ln * 0.12), (x_in, y_)], [1.2, 0.9, 0.2]),
                            ink, rng.uniform(0.3, 0.55) * detail)
            yy += rng.uniform(30, 90)
    m = sk.snap() * cov[..., None]
    out = m + out * (1 - m[..., 3:4])
    return out, xl, y0


def stalactite_profile(top, length, width, seed, hang=True, bumps=0.18, drip=True):
    """Sarkıt (hang) / dikit yarı genişlik profili: kökte geniş, uca doğru incelir, düzensiz şişkinlikler; sarkıtın
    ucunda damla kalınlaşması."""
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 6, 3)
    fr = rng.uniform(2, 7, 3)

    def hw(ys):
        t = np.clip((ys - top) / length, 0, 1) if hang else np.clip((top + length - ys) / length, 0, 1)
        base = (1 - t) ** rng.uniform(0.7, 1.1)
        b = 1 + bumps * (np.sin(t * fr[0] + ph[0]) * 0.6 + np.sin(t * fr[1] * 2 + ph[1]) * 0.4) * (1 - t * 0.5)
        w = width / 2 * base * b + 0.6
        if drip and hang:
            w += np.exp(-((t - 0.97) / 0.03) ** 2) * min(3.0, width * 0.06)
        flare = np.exp(-(t / 0.08) ** 2) * width * 0.18
        return w + flare
    return hw


def place_arr(L, arr, x_px, y_px, wrap=True):
    if wrap:
        sw = arr.shape[1]
        for dx in (-L.w, 0, L.w):
            if x_px + dx < L.w and x_px + dx + sw > 0:
                L.over(arr, x_px + dx, y_px, px=True)
    else:
        L.over(arr, x_px, y_px, px=True)


# ------------------------------------------------------------------ kristal kümesi
def crystal_cluster(sk, x, y, size, seed, body=(40, 190, 150), hi=(190, 255, 230), dark=(14, 70, 70), ink_a=1.0,
                    ink_w=1.6, n=None, spread=1.0, glow=None, glow_a=0.5, up=True, halo=1.0):
    """Kristal kümesi: tabandan yelpaze gibi açılan altıgen prizmalar. Her prizma iki yüz (ışık / gölge) + parlak
    sırt + sivri uç; mürekkep konturu. glow: ayrı Sk (ışıma katmanı) verilirse yumuşak hale ve parlak çekirdek çizilir."""
    rng = np.random.default_rng(seed)
    n = n or int(rng.integers(4, 8))
    sgn = -1 if up else 1
    order = sorted(range(n), key=lambda i: abs(i - (n - 1) / 2), reverse=True)   # yandakiler arkada
    angs = np.linspace(-0.75, 0.75, n) * spread + rng.normal(0, 0.12, n)
    for i in order:
        a = angs[i]
        ln = size * rng.uniform(0.45, 1.0) * (1.0 - 0.45 * abs(a) / (0.75 * spread + 1e-3))
        w = size * rng.uniform(0.13, 0.22)
        bx = x + (i - (n - 1) / 2) * size * 0.11 + rng.uniform(-1, 1) * size * 0.03
        by = y + rng.uniform(0, size * 0.06)
        dx, dy = math.sin(a), sgn * math.cos(a)
        nx, ny = -dy, dx
        tip_len = w * rng.uniform(0.9, 1.6)
        sh = ln - tip_len
        p0l = (bx - nx * w / 2, by - ny * w / 2)
        p0r = (bx + nx * w / 2, by + ny * w / 2)
        p1l = (p0l[0] + dx * sh, p0l[1] + dy * sh)
        p1r = (p0r[0] + dx * sh, p0r[1] + dy * sh)
        ridge_off = rng.uniform(-0.15, 0.25)
        p1m = (bx + nx * w * ridge_off + dx * (sh + tip_len * 0.18), by + ny * w * ridge_off + dy * (sh + tip_len * 0.18))
        tip = (bx + dx * ln + nx * w * 0.08, by + dy * ln + ny * w * 0.08)
        p0m = (bx + nx * w * ridge_off, by + ny * w * ridge_off)
        c_b = tuple(np.clip(np.array(body) * rng.uniform(0.85, 1.12), 0, 255))
        left = poly_path([p0l, p1l, tip, p1m, p0m])
        right = poly_path([p0m, p1m, tip, p1r, p0r])
        # ışık soldan üstten: sol yüz açık, sağ yüz koyu (aşağı bakan kümede tersine)
        sk.path(left, tuple(np.clip(np.array(c_b) * 1.25 + 12, 0, 255)))
        sk.path(right, tuple(np.array(c_b) * 0.55 + np.array(dark) * 0.45))
        # iç parıltı bandı ve sırt çizgisi
        sk.path(ribbon([p0m, ((p0m[0] + p1m[0]) / 2, (p0m[1] + p1m[1]) / 2), p1m], [w * 0.05, w * 0.16, w * 0.1]), hi, 0.85)
        sk.path(ribbon([p1m, tip], [w * 0.12, 0.3]), hi, 0.9)
        # yüzeyde ince kırılma çizgileri
        for _ in range(int(rng.integers(0, 3))):
            t = rng.uniform(0.25, 0.8)
            q = (p0l[0] + (p1l[0] - p0l[0]) * t, p0l[1] + (p1l[1] - p0l[1]) * t)
            q2 = (q[0] + nx * w * 0.45 + dx * w * 0.3, q[1] + ny * w * 0.45 + dy * w * 0.3)
            sk.path(ribbon([q, q2], [0.6, 0.2]), hi, 0.6)
        out = poly_path([p0l, p1l, tip, p1r, p0r])
        if ink_a > 0:
            sk.path(out, INK, ink_a, 0, ink_w)
            sk.path(ribbon([p0m, p1m], [ink_w * 0.35, ink_w * 0.25]), INK, ink_a * 0.5)
        if glow is not None:
            glow.path(out, hi, glow_a * 0.55, size * 0.06)
            glow.path(ribbon([p0m, p1m, tip], [w * 0.25, w * 0.2, 0.5]), (255, 255, 255), glow_a * 0.6, 0.6)
    if glow is not None and halo > 0:
        glow.c.drawCircle(x, y + sgn * size * 0.35, size * 0.9 * halo, glow.paint(body, glow_a * 0.35, size * 0.45 * halo))


# ------------------------------------------------------------------ su yansıması
def reflect(L, y_water, depth, seed, tint=(20, 50, 52), k_dark=0.55, ripple=3.0, fade=1.0, shine=(150, 240, 220),
            shine_n=90, x0=0, x1=None):
    """Katmanın su çizgisinin üstündeki içeriğini aşağıya ayna gibi yansıt (mantıksal y_water). Yansıma satır satır
    yatay dalgalanır, uzaklaştıkça solar ve suyun rengine kararır; yüzeye ince parlak çizgiler eklenir."""
    rng = np.random.default_rng(seed)
    yw = ik.P(y_water)
    d = ik.P(depth)
    src = L.a[max(0, yw - d):yw][::-1].copy()
    d = src.shape[0]
    if d <= 0:
        return
    rows = np.arange(d, dtype=np.float32)
    shift = (np.sin(rows * 0.9 + rng.uniform(0, 6)) * 0.6 + np.sin(rows * 0.23 + 1.0) * 0.4) * ripple * (0.4 + rows / d)
    out = np.empty_like(src)
    for r in range(d):
        out[r] = np.roll(src[r], int(round(shift[r])), axis=0)
    # dikey sıkıştırma hissi: satırları seyrek atla
    a = out[..., 3:4]
    rgb = out[..., :3]
    tcol = c01(tint)
    t = smoothstep(0, d, rows)[:, None, None]
    rgb = rgb * k_dark * (1 - 0.6 * t) + tcol[None, None, :] * a * (0.35 + 0.4 * t)
    fa = (1 - t * 0.85) * fade
    out = np.concatenate([rgb, a], -1) * fa
    # su gövdesi: koyu düz renk (yansıma altında) — mevcut katmanın üstüne değil, yalnızca su bandına
    band = L.a[yw:yw + d]
    hh = min(band.shape[0], out.shape[0])
    x1 = L.w if x1 is None else ik.P(x1)
    x0 = ik.P(x0)
    o = out[:hh, x0:x1]
    band[:hh, x0:x1] = o + band[:hh, x0:x1] * (1 - o[..., 3:4])
    # yüzey parıltı çizgileri
    sk = Sk(L.w / ik.K, (d + 8) / ik.K)
    for _ in range(shine_n):
        x = rng.uniform(x0 / ik.K, x1 / ik.K)
        y = rng.uniform(0, depth) ** 1.6 / depth ** 0.6
        ln = rng.uniform(10, 60) * (1 - y / depth * 0.6)
        sk.path(ribbon([(x, y), (x + ln * 0.5, y + 0.3), (x + ln, y)], [0.3, rng.uniform(0.8, 1.8), 0.3]), shine,
                rng.uniform(0.15, 0.5) * (1 - y / depth))
    sh = sk.snap()[:hh]
    band[:hh] = sh + band[:hh] * (1 - sh[..., 3:4])
    L.a[yw:yw + hh] = band[:hh]


# ------------------------------------------------------------------ zincir
def chain(sk, p0, p1, sag, link=9.0, col=(70, 62, 66), hi=(150, 120, 110), ink_a=1.0, ink_w=1.3, thick=2.4):
    """Sarkan zincir: p0'dan p1'e katener benzeri eğri boyunca sırayla yüzü dönük halka / yandan çubuk."""
    p0 = np.asarray(p0, np.float64)
    p1 = np.asarray(p1, np.float64)
    ln = np.hypot(*(p1 - p0)) + abs(sag) * 1.2
    n = max(2, int(ln / (link * 0.78)))
    t = np.linspace(0, 1, n * 8)
    pts = p0[None, :] + (p1 - p0)[None, :] * t[:, None]
    pts[:, 1] += sag * 4 * t * (1 - t)
    seg = np.cumsum(np.r_[0, np.hypot(*np.diff(pts, axis=0).T)])
    for k in range(n):
        s = (k + 0.5) / n * seg[-1]
        j = int(np.searchsorted(seg, s).clip(1, len(pts) - 1))
        c = pts[j]
        tg = pts[j] - pts[j - 1]
        ang = math.atan2(tg[1], tg[0])
        ca, sa = math.cos(ang), math.sin(ang)
        if k % 2 == 0:
            # yüzü dönük halka: elips oval
            rx, ry = link * 0.62, link * 0.36
            pts_e = [(c[0] + ca * rx * math.cos(q) - sa * ry * math.sin(q), c[1] + sa * rx * math.cos(q) + ca * ry * math.sin(q))
                     for q in np.linspace(0, 2 * math.pi, 16, endpoint=False)]
            pth = smooth_path(pts_e, True, 0.5)
            sk.path(pth, col, 1.0, 0, thick)
            if ink_a > 0:
                sk.path(pth, INK, ink_a * 0.9, 0, thick * 0.35 + ink_w * 0.3)
            # üst kenarda parıltı
            q0 = (c[0] - ca * rx * 0.5 - sa * -ry * 0.9, c[1] - sa * rx * 0.5 + ca * -ry * 0.9)
            q1 = (c[0] + ca * rx * 0.3 - sa * -ry * 1.0, c[1] + sa * rx * 0.3 + ca * -ry * 1.0)
            sk.path(ribbon([q0, q1], [0.8, 0.3]), hi, 0.8)
        else:
            a0 = (c[0] - ca * link * 0.6, c[1] - sa * link * 0.6)
            a1 = (c[0] + ca * link * 0.6, c[1] + sa * link * 0.6)
            r = ribbon([a0, c, a1], [thick * 1.15, thick * 1.25, thick * 1.15])
            sk.path(r, col)
            if ink_a > 0:
                sk.path(r, INK, ink_a, 0, ink_w)
            sk.path(ribbon([(a0[0] + sa, a0[1] - ca), (a1[0] + sa, a1[1] - ca)], [0.7, 0.7]), hi, 0.7)
    return pts


# ------------------------------------------------------------------ bazalt prizması
def basalt_prism(top_y, base_y, x, width, seed, col=(44, 38, 44), lit=(120, 70, 56), rim=(255, 130, 60),
                 ink_w=2.0, top_col=(78, 68, 72), detail=1.0, rim_side=1.0, joints=True, cap=True, ink=INK):
    """Altıgen bazalt sütunu (önden): sol yüz / ön yüz / sağ yüz düz tonlu, lavdan gelen sıcak kenar ışığı bir yanda,
    yatay kırık eklemler, eğik kesik tepe. -> (önçarpılmış dizi, x sol, y üst) mantıksal."""
    rng = np.random.default_rng(seed)
    hh = base_y - top_y + 12
    ww = width + 10
    xl = x - ww / 2
    yt = top_y - 8
    HP, WP = ik.P(hh), ik.P(ww)
    ys, xs = (np.mgrid[0:HP, 0:WP].astype(np.float32) + 0.5) / ik.K
    u = (xs - ww / 2) / (width / 2)                       # -1..1
    # eğik tepe (kesik), sütun boyu
    slope = rng.uniform(-0.55, 0.55) * width
    ytop = 8 + slope * (u * 0.5 + 0.5) - slope * 0.5 + abs(slope) * 0.5
    jag = noise(ww, 1, 3, seed + 1, wrap=False)[0] * 1.5
    cov = np.clip((1 - np.abs(u)) * width / 2 * ik.K + 0.5, 0, 1) * np.clip((ys - ytop) * ik.K + 0.5, 0, 1)
    cov *= np.clip((hh - 2 - ys) * ik.K + 0.5, 0, 1)
    f1, f2 = -0.42 + rng.uniform(-0.08, 0.08), 0.38 + rng.uniform(-0.08, 0.08)
    face = np.where(u < f1, 0, np.where(u < f2, 1, 2))
    tone = np.array([0.8, 1.18, 0.5], np.float32)
    if rim_side < 0:
        tone = np.array([0.5, 1.18, 0.8], np.float32)
    rgb = c01(col)[None, None, :] * tone[face][..., None]
    nz = noise(ww, hh, 2.0, seed + 3, wrap=False, sx=1.5, sy=6)
    rgb *= (1 + 0.08 * nz[..., None] * detail)
    # alttan lav ışığı (aşağı doğru ısınır)
    warm = smoothstep(hh * 0.15, hh, ys) ** 1.3
    rgb = mix(rgb, c01(lit)[None, None, :] * tone[face][..., None], (warm * 0.7)[..., None])
    # is-karası tepe (yukarı doğru kararır), yüzlerde dikey boya izi
    rgb *= (0.8 + 0.2 * smoothstep(0, hh * 0.5, ys))[..., None]
    # kenar ışığı (dış yüzün kenarında ince sıcak şerit)
    edge_u = u * rim_side
    rimb = smoothstep(0.74, 0.88, edge_u) * (1 - smoothstep(0.95, 1.0, edge_u))
    rgb = mix(rgb, c01(rim)[None, None, :], (rimb * (0.3 + 0.7 * warm))[..., None])
    # ön yüzün lava bakan kenarında ikinci, geniş ve sönük sıcak bant
    fb = smoothstep(0.0, 0.3, u * rim_side) * (1 - smoothstep(0.3, 0.42, u * rim_side)) * (face == 1)
    rgb = mix(rgb, c01(lit)[None, None, :] * 1.3, (fb * warm * 0.35)[..., None])
    # tepe yüzü
    tb = (ys - ytop < 5.5 + 2.5 * (1 - np.abs(u))) & (ys - ytop >= 0)
    rgb = np.where(tb[..., None], c01(top_col)[None, None, :] * (1.05 - 0.2 * u[..., None] * rim_side), rgb)
    # yüz sınırlarında mürekkep, dış konturda değişken mürekkep
    fe = np.minimum(np.abs(u - f1), np.abs(u - f2)) * width / 2
    ink_f = np.clip(0.9 - fe, 0, 1) * 0.65 * detail
    edge_d = (1 - np.abs(u)) * width / 2
    ink_e = np.clip(ink_w - edge_d + 0.5, 0, 1)
    top_line = np.clip(1.4 - np.abs(ys - ytop - 5.5 - 2.5 * (1 - np.abs(u))), 0, 1) * 0.7
    top_out = np.clip(1.6 - np.abs(ys - ytop), 0, 1)
    inkm = np.maximum.reduce([ink_f, ink_e, top_line, top_out])
    rgb = mix(rgb, c01(ink)[None, None, :], inkm[..., None])
    out = premul(rgb, cov.astype(np.float32))
    if joints:
        sk = Sk(ww, hh)
        y = 8 + rng.uniform(18, 50)
        while y < hh - 10:
            # yatay eklem: hafif kavisli, yüz sınırlarında kırılan çizgi
            xa = ww / 2 + f1 * width / 2
            xb = ww / 2 + f2 * width / 2
            pts = [(ww / 2 - width / 2, y + rng.uniform(-1, 1)), (xa, y + 2.5), (xb, y + 2.0 + rng.uniform(-1, 1)),
                   (ww / 2 + width / 2, y - 1.5)]
            sk.path(ribbon(pts, [1.6, 1.3, 1.2, 1.6]), ink, 0.85 * detail)
            # eklemin hemen altında açık kenar (kesik yüzey)
            sk.path(ribbon([(p[0], p[1] + 1.6) for p in pts], [0.6, 0.5, 0.5, 0.6]), lit, 0.5 * detail)
            y += rng.uniform(30, 80)
        # kısa dikey çatlaklar
        for _ in range(int(hh / 40 * detail)):
            xx = ww / 2 + rng.uniform(-0.8, 0.8) * width / 2
            yy = rng.uniform(12, hh - 20)
            sk.path(ribbon([(xx, yy), (xx + rng.uniform(-1, 1), yy + rng.uniform(6, 16))], [0.9, 0.2]), ink, 0.6 * detail)
        m = sk.snap() * cov[..., None]
        out = m + out * (1 - m[..., 3:4])
    return out, xl, yt


# ------------------------------------------------------------------ kemik kaburga
def rib(sk, p0, p1, p2, width, col=(196, 178, 150), shade=(110, 88, 80), hi=(236, 224, 196), ink_a=1.0, ink_w=2.2,
        n=24):
    """Dev kaburga kemiği: p0 (kök) -> p2 (uç) kavisli, uca doğru incelen; alt kenarı gölgeli, üst kenarda açık
    vurgu, yer yer çatlak."""
    pts = bezier(p0, p1, p2, n)
    t = np.linspace(0, 1, n)
    ws = width * (1.0 - 0.65 * t ** 1.4) * (1 + 0.12 * np.sin(t * 9))
    body = ribbon(pts, ws)
    sk.path(body, col)
    d = np.gradient(pts, axis=0)
    ln = np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-6)
    nrm = np.stack([-d[:, 1] / ln, d[:, 0] / ln], 1)
    # gölge yarısı (normalin bir yanı)
    sh_pts = pts + nrm * (ws[:, None] * 0.22)
    sk.path(ribbon(sh_pts, ws * 0.55), shade, 0.85)
    hi_pts = pts - nrm * (ws[:, None] * 0.28)
    sk.path(ribbon(hi_pts[2:-3], ws[2:-3] * 0.18), hi, 0.8)
    if ink_a > 0:
        sk.path(body, INK, ink_a, 0, ink_w)
        rng = np.random.default_rng(int(p0[0] * 7 + p2[1]))
        for _ in range(4):
            j = int(rng.integers(3, n - 4))
            q = pts[j] + nrm[j] * ws[j] * 0.45
            q2 = pts[j] + nrm[j] * ws[j] * rng.uniform(-0.1, 0.2) + d[j] / ln[j] * rng.uniform(3, 8)
            sk.path(ribbon([q, q2], [ink_w * 0.7, 0.2]), INK, ink_a * 0.7)
    return pts, ws


# ------------------------------------------------------------------ lav şelalesi
def lava_fall(L, x, y_top, y_bot, width, seed, glow_L=None, core=(255, 226, 150), mid=(255, 130, 40),
              crust=(120, 24, 18), fog_k=0.0, fog_col=(60, 20, 20), splash=True):
    """Dikey lav akıntısı: ortada beyazımsı-sarı çekirdek, kenarlara doğru turuncu ve kabuklaşmış kızıl; boyuna
    akış çizgileri (gerilmiş gürültü), tabanda sıçrama ve buhar. glow_L verilirse ışıma halesi oraya çizilir."""
    rng = np.random.default_rng(seed)
    hh = y_bot - y_top
    pad = width * 2.2
    ww = width + 2 * pad
    HP, WP = ik.P(hh + 30), ik.P(ww)
    ys, xs = (np.mgrid[0:HP, 0:WP].astype(np.float32) + 0.5) / ik.K
    wob = noise(1, hh + 30, 30, seed, wrap=False)[:, 0] * width * 0.25
    cx = ww / 2 + wob[:, None] + (ys / max(hh, 1)) * rng.uniform(-0.3, 0.3) * width
    widen = 1 + 0.35 * smoothstep(0, hh, ys)
    hw = width / 2 * widen
    u = (xs - cx) / hw
    cov = np.clip((1 - np.abs(u)) * hw * ik.K * 0.8, 0, 1) * smoothstep(0, 6, ys) * (1 - smoothstep(hh + 8, hh + 26, ys))
    streak = noise(ww, hh + 30, 0, seed + 1, wrap=False, sx=1.2, sy=40)
    streak2 = noise(ww, hh + 30, 0, seed + 2, wrap=False, sx=4, sy=16)
    heat = np.clip(1 - np.abs(u) ** 1.6 + 0.35 * streak + 0.15 * streak2, 0, 1)
    rgb = mix(c01(crust)[None, None, :], c01(mid)[None, None, :], smoothstep(0.1, 0.55, heat)[..., None])
    rgb = mix(rgb, c01(core)[None, None, :], smoothstep(0.6, 0.95, heat)[..., None])
    # kenarlarda kara kabuk parçaları
    crst = smoothstep(0.55, 0.9, np.abs(u) + 0.25 * streak2) * smoothstep(0.1, 0.6, streak2 + 0.4)
    rgb = mix(rgb, c01((40, 14, 14))[None, None, :], (crst * 0.7)[..., None])
    if fog_k > 0:
        rgb = mix(rgb, c01(fog_col)[None, None, :], fog_k)
    arr = premul(rgb.astype(np.float32), cov.astype(np.float32))
    xl = x - ww / 2
    place_arr(L, arr, ik.P(xl), ik.P(y_top))
    if glow_L is not None:
        g = np.exp(-(u * 0.45) ** 2) * (0.5 + 0.5 * smoothstep(0, hh * 0.3, ys)) * (1 - smoothstep(hh, hh + 30, ys))
        g = ndimage.gaussian_filter(g, ik.K * width * 0.4)
        gc = c01(mid)
        ga = np.clip(g * 0.55, 0, 1).astype(np.float32)
        place_arr(glow_L, np.concatenate([gc[None, None, :] * ga[..., None], ga[..., None]], -1).astype(np.float32),
                  ik.P(xl), ik.P(y_top))
    if splash:
        sk = Sk(width * 6, 60)
        cxs = width * 3
        for _ in range(26):
            a = rng.uniform(-math.pi * 0.95, -math.pi * 0.05)
            r = rng.uniform(4, width * 1.6)
            px, py = cxs + math.cos(a) * r * 1.4, 40 + math.sin(a) * r * 0.5
            sk.c.drawCircle(px, py, rng.uniform(0.8, 2.4), sk.paint(core if rng.random() < 0.5 else mid, rng.uniform(0.5, 1)))
        sk.c.drawOval(skia_rect(cxs - width * 1.6, 34, cxs + width * 1.6, 48), sk.paint(mid, 0.6, 4))
        place_arr(L, sk.snap(), ik.P(x - width * 3), ik.P(y_bot - 40))


def skia_rect(x0, y0, x1, y1):
    import skia
    return skia.Rect.MakeLTRB(x0, y0, x1, y1)


# ------------------------------------------------------------------ duman / pus
def smoke_layer(W, Hh, seed, centers, col_top, col_bot, under=None, alpha=0.6, sx=160, sy=40, rise=0.0):
    """Yatay sürüklenen kalın duman bulutu katmanı (önçarpılmış). centers: [(y, genişlik, güç)];
    under: altta ışıyan renk (lavla aydınlanan alt yüz)."""
    ys = np.arange(ik.P(Hh), dtype=np.float32)[:, None] / ik.K
    n1 = noise(W, Hh, 0, seed, sx=sx, sy=sy)
    n2 = noise(W, Hh, 0, seed + 1, sx=sx * 0.35, sy=sy * 0.5)
    n3 = noise(W, Hh, 0, seed + 2, sx=sx * 0.1, sy=sy * 0.25)
    band = np.zeros_like(n1)
    for (cy, wd, k) in centers:
        band += np.exp(-((ys - cy) / wd) ** 2) * k
    dens = np.clip(band * (0.45 + 0.65 * n1 + 0.35 * n2 + 0.15 * n3), 0, 1)
    a = smoothstep(0.08, 0.75, dens) * alpha
    t = smoothstep(0, Hh, ys)
    rgb = mix(c01(col_top)[None, None, :], c01(col_bot)[None, None, :], t[..., None])
    # yoğunluk kenarlarında açık (ışık geçen) / içte koyu: kabarık bulut hissi
    rgb = rgb * (0.75 + 0.45 * (1 - smoothstep(0.2, 0.8, dens)))[..., None]
    if under is not None:
        # yoğunluk gradyanı aşağı bakıyorsa (bulutun alt yüzü) sıcak ışık
        gy = np.gradient(dens, axis=0) * ik.K
        rgb = mix(rgb, c01(under)[None, None, :], np.clip(-gy * 6, 0, 0.7)[..., None])
    return premul(rgb.astype(np.float32), a.astype(np.float32))
