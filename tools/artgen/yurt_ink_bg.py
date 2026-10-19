"""Ulu Kayın Yurdu, stil v2 "mürekkep" paralaks katmanları (yurt_0_sky ... yurt_3_mid piksel sürümlerinin yerini alır).

Kutsal gece: çivit gök, Tengri'nin yeşil-mor kuzey ışıkları (kut perdeleri), Ülker ve Demir Kazık yıldızları, hilal ay;
dağların ardında göğü tutan Ulu Kayın (Bai-Terek: ak gövde, ışıyan kut yaprakları), uzak bozkırda fenerli oba, en yakında
huş korusu, balballar ve fener dizili çit. Katman yüksekliği 1080 (1080p'de 1:1), gövde/kaya çizimi otuken_ink ile aynı
takım (inkkit_ortam), sis rengi gecenin çivit-firuze rampası.
"""
import math

import numpy as np

import inkkit_ortam as ko
from inkkit_ortam import (INK, Layer, Sk, apply_fog, blade, blob, c01, fbm, leaf_shape, mix, noise, poly_path, premul,
                          ribbon, smooth_path, smoothstep, trunk, bezier)

H = 1080
WL = 3840

SKY_STOPS = [
    (0, (10, 10, 30)),
    (180, (18, 20, 50)),
    (360, (30, 38, 78)),
    (500, (40, 62, 98)),
    (580, (52, 96, 112)),
    (640, (66, 124, 126)),
    (690, (50, 92, 104)),
    (760, (30, 48, 70)),
    (880, (18, 24, 40)),
    (1080, (12, 12, 22)),
]


def sky_rgb():
    ys = np.arange(H, dtype=np.float32)
    st = np.array([s[0] for s in SKY_STOPS], np.float32)
    cs = np.array([s[1] for s in SKY_STOPS], np.float32) / 255.0
    return np.stack([np.interp(ys, st, cs[:, k]) for k in range(3)], 1).astype(np.float32)


SKY = sky_rgb()
FOG_C = (110, 170, 176)


def fog_amount(base, band=0.0, center=640.0, width=80.0, top=0.0, top_end=380.0):
    ys = np.arange(H, dtype=np.float32)
    a = base + band * np.exp(-((ys - center) / width) ** 2)
    a += top * (1 - smoothstep(0, top_end, ys))
    return np.clip(a, 0, 0.97).astype(np.float32)


def _wrap(arr, pad, W):
    core = arr[:, pad:pad + W].copy()
    left = arr[:, :pad]
    right = arr[:, pad + W:]
    core[:, W - pad:] = left + core[:, W - pad:] * (1 - left[..., 3:4])
    core[:, :pad] = right + core[:, :pad] * (1 - right[..., 3:4])
    return core


# ------------------------------------------------------------------ 0) gök (sabit)
def layer_sky(seed=1):
    W = 1920
    L = Layer(W, H)
    rng = np.random.default_rng(seed)
    rgb = np.repeat(ko.hd_lin(SKY)[:, None, :], L.w, 1).copy()
    ys = ko.axis(H)[:, None]
    xs = ko.axis(W)[None, :]
    # boya lekeleri
    n1 = fbm(W, H, [120, 50, 18], seed)
    rgb *= (1 + 0.06 * n1[..., None])
    # samanyolu: çapraz soluk bant
    u = (xs * 0.42 - ys * 0.9 + 120) / 260.0
    mw = np.exp(-u * u) * np.clip(0.5 + 0.7 * fbm(W, H, [40, 14], seed + 3), 0, 1) * (1 - smoothstep(380, 640, ys))
    rgb = mix(rgb, c01((96, 100, 150))[None, None, :], (mw * 0.35)[..., None])
    # kuzey ışıkları: dikey çizgili perdeler (yeşil-firuze gövde, mor tepe)
    aur = np.zeros((L.h, L.w), np.float32)
    aur_top = np.zeros((L.h, L.w), np.float32)
    streak = noise(W, 1, 0, seed + 5, sx=2.2, sy=0.01)[0]
    streak2 = noise(W, 1, 0, seed + 6, sx=9.0, sy=0.01)[0]
    for k, (y_mid, amp, ph, wid, inten) in enumerate([(250, 70, 0.0, 130, 0.9), (330, 50, 1.7, 100, 0.6), (190, 40, 3.1, 80, 0.45)]):
        curve = y_mid + amp * np.sin(xs[0] / 420.0 + ph) + 30 * np.sin(xs[0] / 150.0 + ph * 2.0)
        d = ys - curve[None, :]
        # perde: alt kenar keskin, yukarı doğru uzun soluma
        body = np.where(d > 0, np.exp(-(d / 14.0) ** 2), np.exp(-(d / wid) ** 2))
        body *= np.clip(0.4 + 0.9 * (0.5 + 0.5 * streak[None, :]) * (0.6 + 0.4 * streak2[None, :]), 0, 1.4)
        fade_x = smoothstep(-200, 300, xs) * (1 - smoothstep(1500 + 200 * k, 2000, xs))
        aur += body * fade_x * inten
        aur_top += np.where(d < -wid * 0.5, np.exp(-((d + wid) / (wid * 0.6)) ** 2), 0) * fade_x * inten
    aur = np.clip(aur, 0, 1.2)
    rgb = rgb + c01((60, 230, 170))[None, None, :] * (aur * 0.42)[..., None]
    rgb = rgb + c01((150, 80, 200))[None, None, :] * (np.clip(aur_top, 0, 1) * 0.22)[..., None]
    # ufuk parıltısı (ayın ve obanın ışığı)
    hz = np.exp(-((ys - 640) / 90.0) ** 2) * (0.6 + 0.4 * np.exp(-((xs - 1300) / 900.0) ** 2))
    rgb = mix(rgb, c01((120, 190, 180))[None, None, :], (hz * 0.25)[..., None])
    L.a = premul(np.clip(rgb, 0, 1), np.ones((L.h, L.w), np.float32))
    # yıldızlar
    sk = Sk(W, H)
    for _ in range(900):
        x, y = rng.uniform(0, W), rng.uniform(0, 600) ** 1.0
        r = rng.choice([0.6, 0.8, 1.0, 1.3, 1.7], p=[0.4, 0.28, 0.18, 0.1, 0.04])
        a = rng.uniform(0.35, 0.95) * (1 - smoothstep(420, 640, y))
        c = (230, 236, 255) if rng.random() < 0.7 else ((255, 226, 190) if rng.random() < 0.5 else (190, 220, 255))
        sk.c.drawCircle(x, y, r, sk.paint(c, a))
    # parlak yıldızlar: dört kollu ışıltı
    def sparkle(x, y, s, a=1.0, c=(240, 246, 255)):
        sk.c.drawCircle(x, y, s * 0.35, sk.paint(c, a))
        sk.c.drawCircle(x, y, s * 1.6, sk.paint(c, a * 0.18, blur=s * 0.8))
        for ang, k in ((0, 1.0), (math.pi / 2, 1.0), (math.pi / 4, 0.45), (-math.pi / 4, 0.45)):
            dx, dy = math.cos(ang) * s * 2.6 * k, math.sin(ang) * s * 2.6 * k
            sk.path(ribbon([(x - dx, y - dy), (x, y), (x + dx, y + dy)], [0.2, s * 0.32, 0.2]), c, a * 0.9)
    for _ in range(26):
        sparkle(rng.uniform(40, W - 40), rng.uniform(20, 470), rng.uniform(2.2, 4.0), rng.uniform(0.6, 0.95))
    # Ülker (Pleiades) ve Demir Kazık (Kutup yıldızı)
    for dx, dy, s in ((0, 0, 3.0), (14, -6, 2.4), (24, 4, 2.6), (10, 12, 2.2), (-8, 10, 2.0), (30, -12, 1.8), (20, 18, 1.6)):
        sparkle(1700 + dx, 120 + dy, s, 0.95, (210, 230, 255))
    sparkle(960, 64, 6.0, 1.0, (255, 250, 236))
    # hilal ay (sağ üst): ılık hale, mürekkep konturlu hilal
    mx, my, mr = 330, 150, 58
    sk.c.drawCircle(mx, my, mr * 3.2, sk.paint((150, 190, 220), 0.10, blur=mr * 1.6))
    sk.c.drawCircle(mx, my, mr * 1.5, sk.paint((200, 220, 230), 0.16, blur=mr * 0.5))
    moon = ko.skia.Path()
    moon.addCircle(mx, my, mr)
    cut = ko.skia.Path()
    cut.addCircle(mx + mr * 0.48, my - mr * 0.22, mr * 0.92)
    cres = ko.skia.Op(moon, cut, ko.skia.PathOp.kDifference_PathOp)
    sk.path(cres, (244, 236, 210), 1.0)
    inner = ko.skia.Path()
    inner.addCircle(mx - mr * 0.1, my + mr * 0.06, mr * 0.9)
    shade = ko.skia.Op(cres, inner, ko.skia.PathOp.kDifference_PathOp)
    sk.path(shade, (255, 252, 236), 1.0)
    for cx_, cy_, cr in ((mx - mr * 0.62, my + mr * 0.1, 7), (mx - mr * 0.45, my + mr * 0.55, 5), (mx - mr * 0.7, my - mr * 0.35, 4)):
        sk.c.drawCircle(cx_, cy_, cr, sk.paint((206, 196, 176), 0.8))
    sk.path(cres, INK, 0.9, 0, 3.0)
    L.over(sk.snap())
    return L


# ------------------------------------------------------------------ 1) dağlar ve Ulu Kayın (çok yavaş)
def ridge(W, base, amp, seed, rough=1.0, period=900.0):
    rng = np.random.default_rng(seed)
    xs = np.arange(W, dtype=np.float32)
    y = np.full(W, base, np.float32)
    for k, (p, a) in enumerate(((period, 1.0), (period / 2.3, 0.45), (period / 6, 0.18 * rough), (period / 17, 0.07 * rough))):
        ph = rng.uniform(0, 2 * math.pi)
        y -= amp * a * (0.5 + 0.5 * np.sin(xs * 2 * math.pi / p * (W / p // 1 * p / W if False else 1) + ph))
    # yatay döşeme için uçları eşitle
    t = np.linspace(0, 1, W)
    y = y + (y[0] - y[-1]) * (t - 0.5) * 0
    return y


def mountains(L, seed, base, amp, col, rim, fog, snow=0.0, ink_a=0.6, period=1280.0):
    W = L.w / ko.K
    xs = ko.axis(W)
    rng = np.random.default_rng(seed)
    y = np.full(L.w, base, np.float32)
    for p, a in ((period, 1.0), (period / 2, 0.5), (period / 5, 0.2), (period / 15, 0.07)):
        ph = rng.uniform(0, 2 * math.pi)
        y -= amp * a * np.abs(np.sin(xs * math.pi / p + ph)) ** 1.4
    ys = ko.axis(H)[:, None]
    cov = np.clip((ys - y[None, :]) * ko.HD + 0.5, 0, 1)
    # yüz gölgesi: eğim yönüne göre (ay solda): sol bakan yüz açık, sağ koyu (temel piksel başına eğim)
    dy = np.gradient(y) * ko.HD
    lit = np.clip(0.5 + dy * 1.2, 0, 1)[None, :] * np.exp(-np.clip(ys - y[None, :], 0, None) / 60.0)
    rgb = c01(col)[None, None, :] * (0.85 + 0.0 * ys[..., None])
    rgb = mix(rgb, c01(rim)[None, None, :], (lit * 0.55)[..., None])
    if snow > 0:
        sn = (np.clip(1 - (ys - y[None, :]) / (amp * 0.32), 0, 1) * (y[None, :] < base - amp * 0.55)) * snow
        sn *= np.clip(0.3 + lit * 1.4, 0, 1)
        rgb = mix(rgb, c01((214, 226, 240))[None, None, :], sn[..., None])
    # sırt mürekkep çizgisi
    ink = np.clip(1.6 - np.abs(ys - y[None, :] - 0.8), 0, 1) * ink_a
    rgb = mix(rgb, c01(INK)[None, None, :], ink[..., None])
    arr = premul(rgb.astype(np.float32), cov.astype(np.float32))
    apply_fog(arr, 0, SKY, fog)
    L.over(arr)
    return y


def leaf_mass(sk, cx, cy, r, seed, col, edge_col, rim_col=None, n_leaves=60, kut=0):
    """Çizgi roman yaprak kütlesi: yumuşak çok-loblu siluet, kenarı yaprak uçlarıyla tırtıklı, üstünde kuzey ışığı
    kenar ışığı, içinde ışıyan kut yaprakları."""
    rng = np.random.default_rng(seed)
    lobes = []
    for _ in range(7):
        a = rng.uniform(0, 2 * math.pi)
        d = r * rng.uniform(0.15, 0.5)
        lobes.append((cx + math.cos(a) * d, cy + math.sin(a) * d * 0.6, r * rng.uniform(0.45, 0.7)))
    for (x, y, rr) in lobes:
        sk.path(blob(x, y, rr, rr * 0.7, int(rng.integers(1 << 30)), n=14, jitter=0.12), col)
    for _ in range(n_leaves):
        x, y, rr = lobes[int(rng.integers(len(lobes)))]
        a = rng.uniform(math.pi * 0.9, math.pi * 2.1)
        px, py = x + math.cos(a) * rr * 0.95, y + math.sin(a) * rr * 0.68
        ang = a + rng.uniform(-0.6, 0.6)
        ln = rng.uniform(r * 0.09, r * 0.16)
        sk.path(leaf_shape(px, py, ln, ln * 0.42, ang), col)
        if rim_col is not None and math.sin(a) < -0.35:
            sk.path(leaf_shape(px, py, ln * 0.8, ln * 0.25, ang), rim_col, 0.55)
    for _ in range(int(n_leaves * 0.5)):
        x, y, rr = lobes[int(rng.integers(len(lobes)))]
        px, py = x + rng.uniform(-rr, rr) * 0.6, y + rng.uniform(-rr, rr) * 0.45
        ang = math.pi / 2 + rng.uniform(-0.8, 0.8)
        ln = rng.uniform(r * 0.06, r * 0.11)
        sk.path(leaf_shape(px, py, ln, ln * 0.4, ang), edge_col, 0.7)
    for _ in range(kut):
        x, y, rr = lobes[int(rng.integers(len(lobes)))]
        px, py = x + rng.uniform(-rr, rr) * 0.8, y + rng.uniform(-rr, rr) * 0.55
        ang = math.pi / 2 + rng.uniform(-0.9, 0.9)
        ln = rng.uniform(5, 10)
        sk.path(leaf_shape(px, py, ln * 1.8, ln * 1.0, ang), (90, 240, 220), 0.18, blur=4)
        sk.path(leaf_shape(px, py, ln, ln * 0.42, ang), (150, 255, 236), 0.95)


def layer_tree(seed=20):
    L = Layer(WL, H)
    # uzak sıradağlar (iki kat, karlı)
    mountains(L, seed, 640, 210, (58, 72, 110), (120, 150, 190), fog_amount(0.52, 0.2, 640, 70), snow=0.8, ink_a=0.25)
    # Ulu Kayın: dağların ardında, göğe değen ak gövde
    tx = 1150
    pad = 600
    sk = Sk(WL + 2 * pad, H)
    # dallar (gövdenin arkasında)
    rng = np.random.default_rng(seed + 1)
    branch_tips = []
    for k, (y0, side, ln, up) in enumerate([(300, -1, 640, 0.45), (250, 1, 700, 0.5), (190, -1, 520, 0.75), (160, 1, 560, 0.8),
                                            (110, -1, 380, 1.0), (90, 1, 420, 1.0), (380, -1, 420, 0.25), (360, 1, 460, 0.2)]):
        x0 = tx + pad + side * 20
        p2 = (x0 + side * ln, y0 - ln * up * 0.55)
        p1 = (x0 + side * ln * 0.45, y0 - ln * up * 0.15 - 40)
        pts = bezier((x0, y0), p1, p2, 18)
        wd = np.linspace(46 - k * 3, 8, 18)
        sk.path(ribbon(pts, wd), (128, 138, 160))
        sk.path(ribbon(pts + np.stack([np.full_like(wd, side * 2.0), wd * 0.18], 1), wd * 0.5), (82, 90, 120), 0.8)
        sk.path(ribbon(pts - np.stack([np.zeros_like(wd), wd * 0.22], 1), wd * 0.25), (176, 196, 206), 0.5)
        sk.path(ribbon(pts, wd), INK, 0.85, 0, 2.2)
        for j in range(4, 18, 4):
            q = pts[j]
            tw = bezier(q, (q[0] + side * 40, q[1] - 50), (q[0] + side * rng.uniform(60, 120), q[1] - rng.uniform(60, 130)), 8)
            sk.path(ribbon(tw, np.linspace(wd[j] * 0.35, 2, 8)), (112, 120, 144))
            sk.path(ribbon(tw, np.linspace(wd[j] * 0.35, 2, 8)), INK, 0.8, 0, 1.6)
            branch_tips.append(tw[-1])
        branch_tips.append(pts[-1])
    back = _wrap(sk.snap(), ko.P(pad), ko.P(WL))
    apply_fog(back, 0, SKY, fog_amount(0.22, 0.0, top=0.05))
    L.over(back)
    arr, xl, yt = trunk(H, WL, 690, tx, 190, seed + 2, kind='birch', lean=0.0, bend=0.08, top_y=-60, bark=(120, 130, 156),
                        light=(184, 196, 214), rim=(130, 230, 200), ink_w=5.0, taper=0.55, detail=1.0)
    apply_fog(arr, ko.P(yt), SKY, fog_amount(0.2, 0.25, 640, 90))
    L.over_wrap(arr, xl, yt)
    # taç: koyu yaprak kütleleri, üst kenarlarda kuzey ışığı, ışıyan kut yaprakları
    sk = Sk(WL + 2 * pad, H)
    rng = np.random.default_rng(seed + 3)
    masses = [(tx + pad + rng.uniform(-620, 620), rng.uniform(-90, 140), rng.uniform(110, 190)) for _ in range(13)]
    masses += [(q[0], q[1] - 10, rng.uniform(60, 110)) for q in branch_tips[::3]]
    masses.sort(key=lambda m: -m[1])
    for i, (x, y, r) in enumerate(masses):
        k = 0.75 + 0.25 * (i / len(masses))
        leaf_mass(sk, x, y, r, int(rng.integers(1 << 30)), tuple(np.array((40, 70, 80)) * k), tuple(np.array((26, 46, 58)) * k),
                  rim_col=(110, 230, 190), n_leaves=int(r * 0.6), kut=int(r * 0.12))
    crown = sk.snap()
    crown_w = _wrap(crown, ko.P(pad), ko.P(WL))
    apply_fog(crown_w, 0, SKY, fog_amount(0.18, 0.0, top=0.05))
    L.over(crown_w)
    # kökler dağ sırtına taşar + ön sıradağ (daha koyu) + kök boğazında sis
    mountains(L, seed + 5, 700, 120, (34, 44, 74), (80, 110, 150), fog_amount(0.38, 0.4, 680, 50), snow=0.35, ink_a=0.35, period=900.0)
    # dipte pus
    ys = ko.axis(H)[:, None]
    a = (np.exp(-((ys - 650) / 60.0) ** 2) * 0.5 * np.clip(0.6 + 0.5 * noise(WL, H, 0, seed + 9, sx=200, sy=20), 0, 1)).astype(np.float32)
    rgb = np.repeat(ko.hd_lin(SKY)[:, None, :], L.w, 1) * 0.5 + c01(FOG_C)[None, None, :] * 0.5
    fogL = premul(rgb, np.broadcast_to(a, (L.h, L.w)).astype(np.float32))
    L.over(fogL)
    return L


# ------------------------------------------------------------------ 2) uzak oba
def yurt_sil(sk, x, base, w, felt, door=True, smoke=False, rng=None):
    """Uzak yurt silueti: duvar + kubbe, ay ışığında ak keçe, kapısında sıcak ışık."""
    h_wall = w * 0.32
    h_dome = w * 0.36
    wall = poly_path([(x - w / 2, base), (x - w / 2, base - h_wall), (x + w / 2, base - h_wall), (x + w / 2, base)])
    dome = smooth_path([(x - w / 2 - 2, base - h_wall + 1), (x - w * 0.4, base - h_wall - h_dome * 0.5), (x, base - h_wall - h_dome),
                        (x + w * 0.4, base - h_wall - h_dome * 0.5), (x + w / 2 + 2, base - h_wall + 1)], True, 0.5)
    sk.path(wall, felt)
    sk.path(dome, tuple(np.array(felt) * 1.05))
    # gölge yarısı
    sk.path(poly_path([(x + w * 0.1, base), (x + w * 0.1, base - h_wall), (x + w / 2, base - h_wall), (x + w / 2, base)]), tuple(np.array(felt) * 0.62))
    sk.path(smooth_path([(x + w * 0.05, base - h_wall), (x + w * 0.22, base - h_wall - h_dome * 0.8), (x + w * 0.4, base - h_wall - h_dome * 0.5),
                         (x + w / 2 + 2, base - h_wall + 1)], True, 0.5), tuple(np.array(felt) * 0.66))
    sk.path(poly_path([(x - w / 2, base - h_wall - 1), (x + w / 2, base - h_wall - 1), (x + w / 2, base - h_wall + w * 0.06), (x - w / 2, base - h_wall + w * 0.06)]),
            (150, 50, 50), 0.8)
    sk.path(wall, INK, 0.85, 0, 1.4)
    sk.path(dome, INK, 0.85, 0, 1.4)
    if door:
        dw, dh = w * 0.14, h_wall * 0.75
        sk.c.drawCircle(x, base - dh * 0.5, dh * 1.4, sk.paint((255, 170, 80), 0.25, blur=dh))
        sk.path(poly_path([(x - dw / 2, base), (x - dw / 2, base - dh), (x + dw / 2, base - dh), (x + dw / 2, base)]), (255, 196, 110))
    if smoke and rng is not None:
        sx, sy = x, base - h_wall - h_dome
        pts = [(sx, sy)]
        for k in range(1, 9):
            pts.append((sx + k * 6 + math.sin(k * 0.9) * 8, sy - k * 22))
        sk.path(ribbon(np.array(pts), np.linspace(w * 0.08, w * 0.4, len(pts))), (150, 170, 190), 0.12, blur=6)


def horse_sil(sk, x, base, s, col, flip=1):
    body = smooth_path([(x - 14 * s * flip, base - 14 * s), (x + 12 * s * flip, base - 15 * s), (x + 14 * s * flip, base - 10 * s), (x - 14 * s * flip, base - 9 * s)], True, 0.5)
    sk.path(body, col)
    neck = poly_path([(x + 10 * s * flip, base - 14 * s), (x + 18 * s * flip, base - 24 * s), (x + 22 * s * flip, base - 22 * s), (x + 14 * s * flip, base - 11 * s)])
    sk.path(neck, col)
    for lx in (-11, -7, 9, 12):
        sk.path(ribbon([(x + lx * s * flip, base - 10 * s), (x + lx * s * flip, base)], [2.2 * s, 1.4 * s]), col)
    sk.path(ribbon([(x - 14 * s * flip, base - 13 * s), (x - 18 * s * flip, base - 6 * s)], [2.4 * s, 1.0 * s]), col)


def layer_camp(seed=30):
    L = Layer(WL, H)
    pad = 300
    rng = np.random.default_rng(seed)
    # bozkır tepeleri
    xs = np.arange(WL + 2 * pad, dtype=np.float32)
    sk = Sk(WL + 2 * pad, H)
    yb = 640 - 26 * np.sin(xs / 380.0) - 14 * np.sin(xs / 140.0 + 1.0)
    pts = [(x, y) for x, y in zip(xs[::20], yb[::20])] + [(xs[-1], H), (0, H)]
    sk.path(poly_path(pts), (34, 56, 72))
    sk.path(poly_path([(x, y) for x, y in zip(xs[::20], yb[::20])], False), INK, 0.5, 0, 2.0)
    # oba: küme küme yurtlar
    for cl in range(7):
        cx = rng.uniform(0, WL) + pad
        for k in range(int(rng.integers(3, 7))):
            x = cx + rng.uniform(-170, 170)
            base = float(np.interp(x, xs, yb)) + rng.uniform(4, 10)
            w = rng.uniform(34, 58)
            felt = tuple(np.array((168, 176, 190)) * rng.uniform(0.82, 1.0))
            yurt_sil(sk, x, base, w, felt, door=rng.random() < 0.75, smoke=rng.random() < 0.4, rng=rng)
        # tuğ ve kamp ateşi
        tx_ = cx + rng.uniform(-80, 80)
        tb = float(np.interp(tx_, xs, yb)) + 6
        sk.path(ribbon([(tx_, tb), (tx_, tb - 70)], [2.4, 1.6]), (40, 34, 40))
        sk.path(poly_path([(tx_ + 1, tb - 64), (tx_ + 22, tb - 60), (tx_ + 1, tb - 54)]), (150, 46, 46))
        fx_ = cx + rng.uniform(-120, 120)
        fb = float(np.interp(fx_, xs, yb)) + 8
        sk.c.drawCircle(fx_, fb - 4, 30, sk.paint((255, 150, 60), 0.18, blur=18))
        sk.path(smooth_path([(fx_ - 5, fb), (fx_ - 3, fb - 8), (fx_, fb - 14), (fx_ + 3, fb - 8), (fx_ + 5, fb)], True, 0.5), (255, 190, 90))
    # at sürüsü
    for _ in range(3):
        hx = rng.uniform(0, WL) + pad
        for k in range(int(rng.integers(4, 8))):
            x = hx + rng.uniform(-90, 90)
            base = float(np.interp(x, xs, yb)) + rng.uniform(6, 16)
            horse_sil(sk, x, base, rng.uniform(0.9, 1.2), (26, 34, 46), flip=1 if rng.random() < 0.5 else -1)
    arr = _wrap(sk.snap(), ko.P(pad), ko.P(WL))
    apply_fog(arr, 0, SKY, fog_amount(0.26, 0.3, 650, 50))
    L.over(arr)
    return L


# ------------------------------------------------------------------ 3) yakın sırt: huş korusu, balballar, fenerli çit
def layer_mid(seed=40):
    L = Layer(WL, H)
    pad = 300
    rng = np.random.default_rng(seed)
    xs = np.arange(WL + 2 * pad, dtype=np.float32)
    yb = 676 - 18 * np.sin(xs / 300.0 + 0.4) - 8 * np.sin(xs / 90.0)
    # huş korusu (gövde + koyu taç)
    sk = Sk(WL + 2 * pad, H)
    trees = []
    for g in range(4):
        gx = (g + rng.uniform(0.2, 0.8)) * WL / 4 + pad
        for k in range(int(rng.integers(2, 4))):
            x = gx + rng.uniform(-140, 140)
            base = float(np.interp(x, xs, yb)) + 8
            hgt = rng.uniform(240, 340)
            trees.append((x, base, hgt))
            for j in range(3):
                leaf_mass(sk, x + rng.uniform(-60, 60), base - hgt * rng.uniform(0.7, 0.95), rng.uniform(55, 85), int(rng.integers(1 << 30)),
                          (30, 52, 58), (20, 34, 42), rim_col=(80, 170, 150), n_leaves=50, kut=0)
    crowns = _wrap(sk.snap(), ko.P(pad), ko.P(WL))
    apply_fog(crowns, 0, SKY, fog_amount(0.32, 0.0))
    L.over(crowns)
    for (x, base, hgt) in trees:
            x = x - pad
            arr, xl, yt = trunk(H, WL, base, x, rng.uniform(16, 30), int(rng.integers(1 << 30)), kind='birch', lean=rng.uniform(-0.04, 0.04),
                                bend=rng.uniform(-0.2, 0.2), top_y=int(base - hgt), bark=(78, 86, 108), light=(124, 134, 156),
                                rim=(120, 210, 190), ink_w=2.2, taper=0.5, detail=0.8)
            apply_fog(arr, ko.P(yt), SKY, fog_amount(0.3, 0.25, 650, 60))
            L.over_wrap(arr, xl, yt)
    # sırt dolgusu + çit + balballar + fener dizisi
    sk = Sk(WL + 2 * pad, H)
    pts = [(x, y) for x, y in zip(xs[::16], yb[::16])] + [(xs[-1], H), (0, H)]
    sk.path(poly_path(pts), (22, 32, 44))
    for _ in range(int(WL * 1.2)):
        x = rng.uniform(0, WL + 2 * pad)
        y = float(np.interp(x, xs, yb)) + rng.uniform(-2, 30)
        c = (40, 66, 70) if rng.random() < 0.5 else (28, 44, 52)
        sk.path(blade(x, y + 4, rng.uniform(8, 22), rng.uniform(-0.4, 0.4), rng.uniform(1.6, 3.0)), c, 0.9)
    # çit (kazık + iki kat sırık)
    fx0 = 0
    while fx0 < WL + 2 * pad:
        seg = rng.uniform(300, 600)
        if rng.random() < 0.6:
            posts = np.arange(fx0, fx0 + seg, 46)
            for x in posts:
                y = float(np.interp(x, xs, yb)) + 6
                sk.path(ribbon([(x, y), (x + 1, y - 40)], [5, 4]), (52, 40, 40))
                sk.path(ribbon([(x, y), (x + 1, y - 40)], [5, 4]), INK, 0.8, 0, 1.2)
            for hy in (28, 14):
                line = [(x, float(np.interp(x, xs, yb)) + 6 - hy) for x in posts]
                if len(line) > 1:
                    sk.path(ribbon(np.array(line), [3.0] * len(line)), (64, 50, 46))
            # fener dizisi: kazıklar arasında sarkık ip ve sıcak fenerler
            for i in range(len(posts) - 1):
                a = (posts[i], float(np.interp(posts[i], xs, yb)) - 34)
                b = (posts[i + 1], float(np.interp(posts[i + 1], xs, yb)) - 34)
                mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 9)
                sk.path(ribbon(bezier(a, mid, b, 8), [1.2] * 8), (30, 24, 28))
                if i % 2 == 0:
                    sk.c.drawCircle(mid[0], mid[1] - 2, 14, sk.paint((255, 160, 70), 0.22, blur=9))
                    sk.path(smooth_path([(mid[0] - 3, mid[1] - 6), (mid[0] + 3, mid[1] - 6), (mid[0] + 3.5, mid[1] + 2), (mid[0] - 3.5, mid[1] + 2)], True, 0.4), (255, 200, 110))
        fx0 += seg
    for _ in range(5):
        x = rng.uniform(0, WL) + pad
        y = float(np.interp(x, xs, yb)) + 10
        from otuken_ink import balbal
        balbal(sk, x, y, rng.uniform(60, 80), (88, 94, 108), (130, 140, 156), int(rng.integers(1 << 30)), ink_a=0.8)
    arr = _wrap(sk.snap(), ko.P(pad), ko.P(WL))
    apply_fog(arr, 0, SKY, fog_amount(0.1, 0.3, 676, 40))
    L.over(arr)
    return L


def layer_fog(seed=60):
    W = WL
    ys = ko.axis(H)[:, None]
    n1 = noise(W, H, 0, seed, sx=140, sy=16)
    n2 = noise(W, H, 0, seed + 1, sx=50, sy=8)
    band = np.exp(-((ys - 680) / 60.0) ** 2) * 0.8 + np.exp(-((ys - 600) / 40.0) ** 2) * 0.3
    a = np.clip(band * np.clip(0.5 + 0.6 * n1 + 0.25 * n2, 0, 1) * 0.6, 0, 0.7).astype(np.float32)
    rgb = np.repeat(ko.hd_lin(SKY)[:, None, :], ko.P(W), 1) * 0.5 + c01(FOG_C)[None, None, :] * 0.5
    L = Layer(W, H)
    L.a = premul(rgb, a)
    return L


LAYERS = [('0_sky', layer_sky), ('1_tree', layer_tree), ('2_camp', layer_camp), ('3_mid', layer_mid), ('4_fog', layer_fog)]
VRAM_KEYS = {'1_tree', '2_camp', '3_mid'}


if __name__ == '__main__':
    import sys
    from PIL import Image
    ko.K = 1.0
    keys = [a for a in sys.argv[1:] if not a.endswith('.png')] or [k for k, _ in LAYERS]
    out = sys.argv[-1] if sys.argv[-1].endswith('.png') else 'yurt_bg_on.png'
    # bileşik önizleme: 1920x1080, katmanlar üst üste (kaydırmasız)
    comp = np.zeros((H, 1920, 3), np.float32)
    for k, fn in LAYERS:
        if k not in keys:
            continue
        Lr = fn()
        a = Lr.a[:, :1920]
        comp = a[..., :3] + comp * (1 - a[..., 3:4])
        Image.fromarray(Lr.rgba8()[:, :1920]).save(out.replace('.png', '_%s.png' % k))
    Image.fromarray((np.clip(comp, 0, 1) * 255).astype(np.uint8)).save(out)
