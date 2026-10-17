"""Şahmeran Mağaraları ortamı (sahmeran_ink.py boss çizimidir), stil v2 "mürekkep" paralaks katmanları (Shinobi: Art of Vengeance yönü, Ötüken ile aynı dil).

Yılanlar kraliçesinin yeraltı yurdu: dev mağara boşlukları, ışıyan zümrüt kristaller, yansımalı yeraltı gölü,
yılan kabartmalı taş sütunlar (sarmal yılan gövdesi, başlıkta kukuletalı baş), yosun, damlayan su, teal/zümrüt ışık.
Uzakta kayaya oyulmuş Şahmeran sarayı (basamaklı teraslar, kehribar ışıklı kemerli kapılar).

Katmanlar (1080 yükseklik, 1080p'de 1:1; data/stil_v2.json "sahmeran"):
  0 gök/uzak mağara (1920, sabit)  1 uzak duvar + saray + göl  2 sarkıt perdesi + dikitler + kristaller + göl
  2b pus   3 yılan sütunları + kayalar + kristaller + göl kıyısı   4 göl sisi   5 tavan çatlağı hüzmeleri + zerreler
  6 yakın koyu dikit/sarkıtlar + parlak kristaller
"""
import math

import numpy as np

import inkkit_ortam as ik
from inkkit_ortam import INK, Layer, Sk, bezier, blob, c01, fbm, mix, noise, poly_path, premul, ribbon, smooth_path, smoothstep
import inkkit_yeralti as Y
from otuken_ink import rock, grass_field

H = 1080
WL = 3840

SKY = Y.ramp([
    (0, (6, 9, 14)),
    (180, (8, 15, 20)),
    (380, (13, 32, 36)),
    (500, (24, 60, 60)),
    (575, (52, 118, 108)),
    (622, (92, 186, 162)),
    (648, (54, 112, 104)),
    (720, (22, 48, 50)),
    (860, (10, 22, 26)),
    (1080, (6, 10, 14)),
])
MINT = (150, 240, 210)
ROCK = (52, 64, 70)
ROCK_L = (104, 136, 134)
RIM = (110, 230, 196)
EMER = (40, 196, 150)
EMER_HI = (196, 255, 232)
AMETH = (150, 96, 214)
AMETH_HI = (232, 206, 255)
AMBER = (236, 170, 70)


def _fog(arr, y0, amt):
    return ik.apply_fog(arr, y0, SKY, amt)


fog_amount = Y.fog_amount


# ------------------------------------------------------------------ 0) uzak mağara (sabit)
def layer_sky(seed=1):
    W = 1920
    L = Layer(W, H)
    rgb = np.repeat(ik.hd_lin(SKY)[:, None, :], L.w, 1).copy()
    ys = ik.axis(H)[:, None]
    xs = ik.axis(W)[None, :]
    # göl ufkundaki parıltı kaynağı (uzak kristal ormanı)
    d = np.hypot((xs - 820) / 980.0, (ys - 610) / 300.0)
    rgb = mix(rgb, c01((110, 220, 190))[None, None, :], (np.exp(-d * d * 2.4) * 0.35)[..., None])
    n1 = fbm(W, H, [110, 40, 14], seed)
    rgb *= (1 + 0.07 * n1[..., None])
    # kubbe: üstte kayalık tavan dokusu (koyu lekeler + açık damar)
    vault = smoothstep(0.0, 0.6, fbm(W, H, [70, 22, 8], seed + 3) * 0.9 + 0.3) * (1 - smoothstep(80, 420, ys))
    rgb = mix(rgb, c01((4, 7, 10))[None, None, :], (vault * 0.8)[..., None])
    L.a = premul(rgb, np.ones((L.h, L.w), np.float32))
    # uzak dev sarkıt kütleleri (çok sisli siluet) ve tavandan inen sütunlar
    sk = Sk(W, H)
    rng = np.random.default_rng(seed + 5)
    for _ in range(26):
        x = rng.uniform(-40, W + 40)
        ln = rng.uniform(80, 340)
        w = rng.uniform(30, 110)
        pts = [(x - w / 2, -10), (x - w * 0.3, ln * 0.4), (x - w * 0.08, ln * 0.85), (x + rng.uniform(-6, 6), ln),
               (x + w * 0.1, ln * 0.8), (x + w * 0.32, ln * 0.35), (x + w / 2, -10)]
        sk.path(smooth_path(pts, True, 0.4), (16, 34, 38), rng.uniform(0.5, 0.9), 3)
    for x in (250, 1500):
        pts = [(x - 160, -10), (x - 60, 260), (x - 34, 430), (x - 70, 620), (x - 130, 700), (x + 140, 700), (x + 80, 610),
               (x + 40, 440), (x + 70, 250), (x + 170, -10)]
        sk.path(smooth_path(pts, True, 0.4), (20, 46, 48), 0.55, 6)
    arr = sk.snap()
    L.over(arr)
    # uzak kristal ışıkları (bokeh)
    g = Sk(W, H)
    for _ in range(70):
        x, y = rng.uniform(0, W), rng.uniform(300, 640)
        r = rng.uniform(2, 9)
        c = [EMER_HI, (120, 255, 210), AMETH_HI, (255, 214, 140)][int(rng.choice(4, p=[0.45, 0.3, 0.15, 0.1]))]
        g.c.drawCircle(x, y, r * 3, g.paint(c, 0.12, r * 2))
        g.c.drawCircle(x, y, r * 0.5, g.paint(c, 0.5, 1))
    L.over(g.snap())
    return L


# ------------------------------------------------------------------ yardımcılar
def column_shape(x, top, bot, w_top, w_mid, w_bot, seed, waist=0.55):
    """Tavanla zemini birleştiren kum saati biçimli sütun (sarkıt+dikit kaynaşması)."""
    rng = np.random.default_rng(seed)
    left, right = [], []
    for t in np.linspace(0, 1, 14):
        y = top + (bot - top) * t
        if t < waist:
            k = (t / waist)
            w = w_top + (w_mid - w_top) * smoothstep(0, 1, k)
        else:
            k = (t - waist) / (1 - waist)
            w = w_mid + (w_bot - w_mid) * smoothstep(0, 1, k) ** 1.4
        j = rng.uniform(-0.08, 0.08) * w
        left.append((x - w / 2 + j, y))
        right.append((x + w / 2 + j * 0.6, y))
    return smooth_path(left + right[::-1], True, 0.4)


def palace(sk, x, base_y, s, col, lit, win, seed, ink_a=0.7):
    """Kayaya oyulmuş Şahmeran sarayı: basamaklı teraslar, kemerli kapılar (içleri kehribar ışık), çatıda iki
    yılan başlı burç, ortada kubbeli taht salonu."""
    rng = np.random.default_rng(seed)
    # kaya çıkıntısı
    crag = [(x - 260 * s, base_y + 20), (x - 220 * s, base_y - 120 * s), (x - 150 * s, base_y - 170 * s),
            (x - 60 * s, base_y - 200 * s), (x + 60 * s, base_y - 210 * s), (x + 170 * s, base_y - 160 * s),
            (x + 240 * s, base_y - 90 * s), (x + 280 * s, base_y + 20)]
    sk.path(smooth_path(crag, True, 0.35), col)
    lv = [(-190, -110, 190, -70), (-140, -170, 140, -110), (-90, -230, 90, -170)]
    for i, (x0, y0, x1, y1) in enumerate(lv):
        p = poly_path([(x + x0 * s, base_y + y1 * s), (x + x0 * s, base_y + y0 * s), (x + x1 * s, base_y + y0 * s),
                       (x + x1 * s, base_y + y1 * s)])
        sk.path(p, tuple(np.array(col) * (1.1 + 0.1 * i)))
        sk.path(ribbon([(x + x0 * s, base_y + y0 * s), (x + x1 * s, base_y + y0 * s)], [2.2 * s, 2.2 * s]), lit, 0.8)
        if ink_a > 0:
            sk.path(p, INK, ink_a, 0, 1.4)
        nd = 5 - i
        for k in range(nd):
            dx = x + (x0 + (x1 - x0) * (k + 0.5) / nd) * s
            dw, dh = 12 * s, (y1 - y0) * 0.62 * s
            dy = base_y + y1 * s
            door = smooth_path([(dx - dw / 2, dy), (dx - dw / 2, dy - dh * 0.6), (dx, dy - dh), (dx + dw / 2, dy - dh * 0.6),
                                (dx + dw / 2, dy)], True, 0.3)
            sk.path(door, (12, 14, 16))
            if rng.random() < 0.7:
                sk.path(door, win, rng.uniform(0.55, 0.95), 1.0)
    # kubbe
    cy = base_y - 230 * s
    dome = smooth_path([(x - 60 * s, cy), (x - 52 * s, cy - 40 * s), (x, cy - 74 * s), (x + 52 * s, cy - 40 * s), (x + 60 * s, cy)], True, 0.4)
    sk.path(dome, tuple(np.array(col) * 1.25))
    sk.path(ribbon([(x - 30 * s, cy - 50 * s), (x - 6 * s, cy - 70 * s)], [3 * s, 1 * s]), lit, 0.7)
    sk.path(ribbon([(x, cy - 74 * s), (x, cy - 100 * s)], [2.4 * s, 1 * s]), tuple(np.array(col) * 1.3))
    sk.c.drawCircle(x, cy - 102 * s, 4 * s, sk.paint(win, 0.9))
    # yılan başlı burçlar
    for side in (-1, 1):
        tx = x + side * 120 * s
        ty = base_y - 170 * s
        tw = poly_path([(tx - 14 * s, ty), (tx - 12 * s, ty - 110 * s), (tx + 12 * s, ty - 110 * s), (tx + 14 * s, ty)])
        sk.path(tw, tuple(np.array(col) * 1.15))
        hy = ty - 110 * s
        hood = smooth_path([(tx - 26 * s, hy + 6 * s), (tx - 22 * s, hy - 24 * s), (tx, hy - 40 * s),
                            (tx + 22 * s, hy - 24 * s), (tx + 26 * s, hy + 6 * s), (tx, hy - 4 * s)], True, 0.4)
        sk.path(hood, tuple(np.array(col) * 1.2))
        sk.c.drawCircle(tx - 6 * s, hy - 22 * s, 2.4 * s, sk.paint(win, 0.95))
        sk.c.drawCircle(tx + 6 * s, hy - 22 * s, 2.4 * s, sk.paint(win, 0.95))
        if ink_a > 0:
            sk.path(tw, INK, ink_a, 0, 1.4)
            sk.path(hood, INK, ink_a, 0, 1.4)


def crystals_row(L, seed, n, y_base, size, fog_amt, glow_a=0.5, xs=None, jit=8, cols=None, ink_a=1.0, ink_w=1.6,
                 halo=1.0):
    """Bir katmana kristal kümeleri + ışıma halesi (hale önce, kristal üstte)."""
    rng = np.random.default_rng(seed)
    pad = 300
    gsk = Sk(L.w / ik.K + 2 * pad, H)
    csk = Sk(L.w / ik.K + 2 * pad, H)
    xs = rng.uniform(0, L.w / ik.K, n) if xs is None else xs
    cols = cols or [(EMER, EMER_HI, (10, 64, 60))] * 5 + [(AMETH, AMETH_HI, (40, 20, 70))]
    for x in xs:
        body, hi, dk = cols[int(rng.integers(len(cols)))]
        sz = size * rng.uniform(0.6, 1.35)
        y = y_base + rng.uniform(-jit, jit)
        for dx in (0, L.w / ik.K, -L.w / ik.K):
            Y.crystal_cluster(csk, x + pad + dx, y, sz, int(x * 13) % 100000, body, hi, dk, ink_a=ink_a, ink_w=ink_w,
                              glow=gsk, glow_a=glow_a * halo)
    g = Y.wrap_core(gsk.snap(), ik.P(pad), L.w)
    c = Y.wrap_core(csk.snap(), ik.P(pad), L.w)
    _fog(c, 0, fog_amt)
    L.over(g)
    L.over(c)


def spike_one(top, length, width, x, seed, hang, rock_c, light, rim, ink_w, detail, lean=0.0, wet=0.6):
    hw = Y.stalactite_profile(top, length, width, seed, hang=hang)
    rng = np.random.default_rng(seed + 1)
    cur = rng.uniform(-0.12, 0.12) * width

    def cx(ys):
        t = np.clip((ys - top) / length, 0, 1)
        return x + lean * (ys - top) + cur * np.sin(t * math.pi)
    return Y.lathe(top, top + length + 2, cx, hw, seed, rock=rock_c, light=light, rim=rim, ink_w=ink_w, detail=detail,
                   wet=wet)


def stalactite_row(L, seed, n, length, width, fog_amt, rock_c=ROCK, light=ROCK_L, rim=RIM, ink_w=1.5, detail=0.6,
                   ceil=-6, xs=None, dark_k=1.0, cluster=0.5):
    """Tavandan sarkıtlar; bir kısmı kök paylaşan 2-4'lü öbekler (büyük + yanında küçükler)."""
    rng = np.random.default_rng(seed)
    xs = rng.uniform(0, L.w / ik.K, n) if xs is None else xs
    for x in xs:
        group = [(x, 1.0)]
        if rng.random() < cluster:
            for _ in range(int(rng.integers(1, 4))):
                group.append((x + rng.uniform(-1, 1) * width * 0.9, rng.uniform(0.3, 0.7)))
        group.sort(key=lambda g: -g[1])
        for gx, k in group:
            ln = length * rng.uniform(0.4, 1.0) * k
            w = width * rng.uniform(0.6, 1.2) * (0.5 + 0.5 * k)
            top = ceil + rng.uniform(-12, 2)
            arr, xl, yt = spike_one(top, ln, w, gx, int(rng.integers(1 << 30)), True, rock_c, light, rim, ink_w,
                                    detail, lean=rng.uniform(-0.03, 0.03))
            arr[..., :3] *= dark_k
            _fog(arr, ik.P(yt), fog_amt)
            Y.place_arr(L, arr, ik.P(xl), ik.P(yt))


def stalagmite_row(L, seed, n, base_y, length, width, fog_amt, rock_c=ROCK, light=ROCK_L, rim=RIM, ink_w=1.5,
                   detail=0.6, xs=None, jit=8, dark_k=1.0, cluster=0.5):
    rng = np.random.default_rng(seed)
    xs = rng.uniform(0, L.w / ik.K, n) if xs is None else xs
    for x in xs:
        group = [(x, 1.0)]
        if rng.random() < cluster:
            for _ in range(int(rng.integers(1, 3))):
                group.append((x + rng.uniform(-1, 1) * width * 0.8, rng.uniform(0.3, 0.65)))
        group.sort(key=lambda g: -g[1])
        for gx, k in group:
            ln = length * rng.uniform(0.45, 1.0) * k
            w = width * rng.uniform(0.7, 1.2) * (0.55 + 0.45 * k)
            by = base_y + rng.uniform(-jit, jit) + (1 - k) * 6
            arr, xl, yt = spike_one(by - ln, ln + 6, w, gx, int(rng.integers(1 << 30)), False, rock_c, light, rim,
                                    ink_w, detail, lean=rng.uniform(-0.04, 0.04))
            arr[..., :3] *= dark_k
            _fog(arr, ik.P(yt), fog_amt)
            Y.place_arr(L, arr, ik.P(xl), ik.P(yt))


def mounds(L, seed, base_y, n, rx, ry, col, fog_amt, blur=4.0, jit=14, top_col=None):
    rng = np.random.default_rng(seed)
    pad = 300
    sk = Sk(L.w / ik.K + 2 * pad, H)
    for _ in range(n):
        x = rng.uniform(0, L.w / ik.K) + pad
        y = base_y + rng.uniform(-jit, jit)
        rxx, ryy = rx * rng.uniform(0.6, 1.4), ry * rng.uniform(0.6, 1.3)
        sk.path(blob(x, y, rxx, ryy, int(rng.integers(1 << 30)), n=16, jitter=0.2), col, 1.0, blur)
        if top_col is not None:
            sk.path(blob(x - rxx * 0.15, y - ryy * 0.55, rxx * 0.7, ryy * 0.3, int(rng.integers(1 << 30)), n=12, jitter=0.25),
                    top_col, 0.7, blur * 1.5)
    arr = Y.wrap_core(sk.snap(), ik.P(pad), L.w)
    _fog(arr, 0, fog_amt)
    L.over(arr)


def snake_pillar(L, x, base_y, width, seed, fog_amt, stone=(66, 82, 84), stone_l=(150, 176, 166), snake=(40, 74, 58),
                 snake_l=(110, 170, 126), eye=(255, 200, 90), turns=4.6, cap_y=150, dark_k=1.0, ink_k=1.0):
    """Yılan kabartmalı taş sütun: silindirik gövde, kaide ve başlık blokları; gövdeye sarılan yılanın ön yarı
    kıvrımları (gölge düşürür, sırtında pul çizgileri), başlıkta kukuletalı yılan başı (kehribar gözlü)."""
    rng = np.random.default_rng(seed)
    arr, xl, yt = ik.trunk(H, WL, base_y, x, width, seed, kind='pine', lean=0.0, bend=0.0, top_y=-60, bark=stone,
                           light=stone_l, rim=RIM, ink_w=2.2 * ink_k, light_side=-1.0, detail=0.35, taper=0.0)
    arr[..., :3] *= dark_k
    _fog(arr, ik.P(yt), fog_amt)
    Y.place_arr(L, arr, ik.P(xl), ik.P(yt))
    pad = 160
    Wc = width * 3 + 2 * pad
    sk = Sk(Wc, H)
    cx = Wc / 2
    R = width * 0.56
    bw = width * 0.44
    sd = tuple(np.array(stone) * 0.45 * dark_k)
    sc = tuple(np.array(snake) * dark_k)
    sl = tuple(np.array(snake_l) * dark_k)
    y_top = cap_y + 60
    pitch = (base_y - 40 - y_top) / turns
    # kıvrımlar: aşağıdan yukarı; yalnızca ön yarı (cos > 0)
    k = 0
    while True:
        phi0 = -math.pi / 2 + 2 * math.pi * k
        yb = base_y - 40 - pitch * k
        if yb - pitch * 0.5 < y_top:
            break
        ph = np.linspace(phi0, phi0 + math.pi, 24)
        px = cx + R * np.sin(ph)
        py = yb - pitch * (ph - phi0) / (2 * math.pi) + 0.0
        pts = np.stack([px, py], 1)
        wv = bw * (0.85 + 0.15 * np.cos(ph - phi0 - math.pi / 2))
        sk.path(ribbon(pts + np.array([3, bw * 0.45]), wv * 0.9), sd, 0.7, 3)          # sütuna düşen gölge
        sk.path(ribbon(pts, wv), sc)
        sk.path(ribbon(pts + np.array([0, bw * 0.3]), wv * 0.3), tuple(np.array((112, 126, 96)) * dark_k), 0.8)  # karın pulları
        sk.path(ribbon(pts + np.array([-1, -bw * 0.24]), wv * 0.3), sl, 0.85)         # üst sırt ışığı
        for j in range(2, 23, 2):   # karın plakaları (kısa enine çizgiler)
            q = pts[j] + np.array([0, bw * 0.3])
            sk.path(ribbon([(q[0], q[1] - wv[j] * 0.14), (q[0] + 1.0, q[1] + wv[j] * 0.14)], [0.8, 0.8]), INK, 0.45 * ink_k)
        sk.path(ribbon(pts, wv), INK, 0.9 * ink_k, 0, 1.6)
        # pul izleri: V biçimli kısa darbeler
        for j in range(3, 22, 2):
            q = pts[j]
            tg = pts[j + 1] - pts[j - 1]
            ang = math.atan2(tg[1], tg[0])
            ca, sa = math.cos(ang), math.sin(ang)
            nx, ny = -sa, ca
            s_ = wv[j] * 0.32
            a = (q[0] - ca * s_ + nx * s_, q[1] - sa * s_ + ny * s_)
            b = (q[0] + ca * s_ * 0.4, q[1] + sa * s_ * 0.4)
            c = (q[0] - ca * s_ - nx * s_, q[1] - sa * s_ - ny * s_)
            sk.path(ribbon([a, b, c], [0.4, 1.1, 0.4]), INK, 0.45 * ink_k)
        k += 1
    # kaide ve başlık blokları
    for (yy, hh, ww) in ((base_y - 18, 22, width * 1.5), (base_y - 34, 16, width * 1.25), (cap_y, 28, width * 1.55),
                         (cap_y + 26, 14, width * 1.3)):
        p = poly_path([(cx - ww / 2, yy), (cx + ww / 2, yy), (cx + ww / 2, yy + hh), (cx - ww / 2, yy + hh)])
        sk.path(p, tuple(np.array(stone) * 1.05 * dark_k))
        sk.path(poly_path([(cx - ww / 2, yy), (cx + ww / 2, yy), (cx + ww / 2, yy + 4), (cx - ww / 2, yy + 4)]),
                tuple(np.array(stone_l) * dark_k), 0.75)
        sk.path(poly_path([(cx + ww * 0.2, yy + 4), (cx + ww / 2, yy + 4), (cx + ww / 2, yy + hh), (cx + ww * 0.2, yy + hh)]),
                tuple(np.array(stone) * 0.55 * dark_k), 0.8)
        sk.path(p, INK, ink_k, 0, 2.0)
        # zikzak oyma
        zz = [(cx - ww / 2 + 6 + i * 9, yy + hh * (0.4 if i % 2 else 0.75)) for i in range(int((ww - 12) / 9) + 1)]
        if len(zz) > 2:
            sk.path(ribbon(zz, [1.0] * len(zz)), INK, 0.5 * ink_k)
    # başlıktaki kukuletalı yılan başı (sütunun önüne, yana dönük)
    side = 1 if rng.random() < 0.5 else -1
    hx, hy = cx + side * width * 0.2, cap_y - 6
    hs = width / 52.0
    hood = smooth_path([(hx - 30 * hs, hy + 8 * hs), (hx - 34 * hs, hy - 30 * hs), (hx - 16 * hs, hy - 58 * hs), (hx, hy - 66 * hs), (hx + 16 * hs, hy - 58 * hs),
                        (hx + 34 * hs, hy - 30 * hs), (hx + 30 * hs, hy + 8 * hs), (hx, hy - 6 * hs)], True, 0.4)
    sk.path(hood, sc)
    sk.path(smooth_path([(hx - 18 * hs, hy - 2 * hs), (hx - 22 * hs, hy - 30 * hs), (hx, hy - 56 * hs), (hx + 22 * hs, hy - 30 * hs), (hx + 18 * hs, hy - 2 * hs), (hx, hy - 14 * hs)],
                        True, 0.4), sl, 0.55)
    head = smooth_path([(hx - 9 * hs, hy - 40 * hs), (hx, hy - 62 * hs), (hx + 9 * hs, hy - 40 * hs), (hx + side * 4 * hs, hy - 26 * hs), (hx - side * 4 * hs, hy - 26 * hs)], True, 0.4)
    sk.path(head, tuple(np.array(snake_l) * 0.9 * dark_k))
    sk.path(hood, INK, ink_k, 0, 2.0)
    sk.path(head, INK, ink_k, 0, 1.4)
    for sx in (-1, 1):
        sk.c.drawCircle(hx + sx * 4 * hs, hy - 48 * hs, 2.2, sk.paint(eye, 1.0))
        sk.c.drawCircle(hx + sx * 4 * hs, hy - 48 * hs, 5.0, sk.paint(eye, 0.25, 3))
    # kukulete deseni
    for sx in (-1, 1):
        sk.path(smooth_path([(hx + sx * 12 * hs, hy - 34 * hs), (hx + sx * 20 * hs, hy - 26 * hs), (hx + sx * 14 * hs, hy - 18 * hs), (hx + sx * 8 * hs, hy - 26 * hs)], True, 0.4),
                INK, 0.6 * ink_k)
    a = sk.snap()
    _fog(a, 0, fog_amt)
    Y.place_arr(L, a, ik.P(x - Wc / 2), 0)


def moss_drape(L, seed, n, fog_amt, y_max=140, col=(40, 90, 64), hi=(110, 190, 120), ink_a=0.6):
    """Tavandan sarkan yosun / kök saçakları (ıslak, ucunda damla)."""
    rng = np.random.default_rng(seed)
    pad = 200
    sk = Sk(L.w / ik.K + 2 * pad, H)
    for _ in range(n):
        x0 = rng.uniform(0, L.w / ik.K) + pad
        for k in range(int(rng.integers(4, 12))):
            sx = x0 + rng.normal(0, 30)
            ln = rng.uniform(20, y_max)
            pts = bezier((sx, -5), (sx + rng.uniform(-8, 8), ln * 0.5), (sx + rng.uniform(-14, 14), ln), 10)
            c = hi if rng.random() < 0.2 else col
            for dx in (0, L.w / ik.K, -L.w / ik.K):
                q = pts + np.array([dx, 0])
                sk.path(ribbon(q, np.linspace(rng.uniform(2, 5), 0.6, 10)), c, 0.95)
                if ink_a > 0 and rng.random() < 0.5:
                    sk.path(ribbon(q[5:], np.linspace(1.2, 0.3, 5)), INK, ink_a)
                if rng.random() < 0.3:
                    sk.c.drawCircle(q[-1][0], q[-1][1] + 3, 1.6, sk.paint(MINT, 0.8))
    arr = Y.wrap_core(sk.snap(), ik.P(pad), L.w)
    _fog(arr, 0, fog_amt)
    L.over(arr)


def rocks(L, seed, n, y_base, rx, ry, fog_amt, base=(64, 80, 82), moss=(58, 112, 80), jit=8):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        r = rock(int(rng.integers(1 << 30)), rx * rng.uniform(0.6, 1.3), ry * rng.uniform(0.6, 1.2), base=base, moss=moss)
        h, w = r.shape[:2]
        x = rng.uniform(0, L.w / ik.K)
        yt = y_base + rng.uniform(-jit, jit) - h / ik.K + 8
        _fog(r, ik.P(yt), fog_amt)
        Y.place_arr(L, r, ik.P(x - w / ik.K / 2), ik.P(yt))


def water_band(L, y0, y1, col_top, col_bot, alpha=1.0):
    """Göl yüzeyi: düz koyu su bandı (yansıma bunun üstüne düşer)."""
    ys = ik.axis(H)
    t = smoothstep(y0, y1, ys)
    rgb = mix(c01(col_top)[None, :], c01(col_bot)[None, :], t[:, None])
    a = (smoothstep(y0 - 1, y0 + 1.5, ys) * alpha).astype(np.float32)
    arr = np.repeat(premul(rgb[:, None, :].repeat(1, 1), a[:, None])[:, :, :], L.w, 1)
    L.a = arr + L.a * (1 - arr[..., 3:4])


# ------------------------------------------------------------------ 1) uzak duvar + saray + göl
def layer_far(seed=20):
    L = Layer(WL, H)
    rng = np.random.default_rng(seed)
    pad = 300
    sk = Sk(WL + 2 * pad, H)
    # dev kum saati sütunlar
    for x in (420, 1500, 2350, 3500):
        x += rng.uniform(-60, 60)
        sk.path(column_shape(x + pad, -20, 650, rng.uniform(260, 380), rng.uniform(60, 110), rng.uniform(200, 300),
                             int(x)), (26, 54, 56))
    # uzak mağara duvarı tümsekleri
    for _ in range(18):
        x = rng.uniform(0, WL) + pad
        sk.path(blob(x, 640, rng.uniform(120, 300), rng.uniform(40, 90), int(rng.integers(1 << 30)), 16, 0.2), (24, 52, 54), 1.0, 4)
    # tavandan sarkan kütle
    for _ in range(30):
        x = rng.uniform(0, WL) + pad
        ln = rng.uniform(60, 260)
        w = rng.uniform(40, 130)
        sk.path(smooth_path([(x - w / 2, -10), (x - w * 0.2, ln * 0.6), (x, ln), (x + w * 0.2, ln * 0.6), (x + w / 2, -10)], True, 0.4),
                (16, 34, 38), 1.0, 2)
    arr = Y.wrap_core(sk.snap(), ik.P(pad), ik.P(WL))
    _fog(arr, 0, fog_amount(0.55, 0.3, 610, 90, top=0.1))
    L.over(arr)
    sk = Sk(WL + 2 * pad, H)
    for x in (1050, 2900):
        palace(sk, x + pad, 640, 0.95, (40, 70, 70), (110, 170, 150), AMBER, int(x), ink_a=0.55)
    arr = Y.wrap_core(sk.snap(), ik.P(pad), ik.P(WL))
    _fog(arr, 0, fog_amount(0.38, 0.2, 620, 60))
    L.over(arr)
    crystals_row(L, seed + 3, 22, 640, 26, fog_amount(0.4, 0.2, 630, 40), glow_a=0.55, ink_a=0.0, halo=1.2)
    water_band(L, 646, 800, (34, 82, 80), (10, 26, 30))
    Y.reflect(L, 646, 150, seed + 9, tint=(20, 60, 62), k_dark=0.7, ripple=2.0, shine=(160, 250, 225), shine_n=120)
    return L


# ------------------------------------------------------------------ 2) sarkıt perdesi + dikit + kristal
def layer_farmid(seed=30):
    L = Layer(WL, H)
    stalactite_row(L, seed, 40, 300, 50, fog_amount(0.4, 0.0, top=0.12), ink_w=0.9, detail=0.35,
                   rock_c=(40, 56, 60), light=(90, 124, 120))
    mounds(L, seed + 1, 652, 26, 150, 44, (30, 62, 62), fog_amount(0.36, 0.3, 640, 50), blur=4)
    stalagmite_row(L, seed + 2, 22, 664, 170, 40, fog_amount(0.34, 0.3, 640, 60), ink_w=0.9, detail=0.35,
                   rock_c=(40, 58, 60), light=(90, 128, 122))
    crystals_row(L, seed + 3, 16, 662, 40, fog_amount(0.25, 0.2, 650, 40), glow_a=0.55, ink_a=0.6, ink_w=1.2)
    water_band(L, 668, 830, (28, 68, 68), (8, 22, 26))
    Y.reflect(L, 668, 170, seed + 9, tint=(16, 50, 54), k_dark=0.6, ripple=2.6, shine=(150, 245, 220), shine_n=160)
    return L


# ------------------------------------------------------------------ 3) yılan sütunları + kıyı
def shore(L, seed, y0, col, top_col, fog_amt, n=7, wmin=200, wmax=520, hmin=14, hmax=40, ink_a=0.7, moss=None):
    """Göl kıyısında yassı kaya adacıkları / setler (üstü yosunlu, önü mürekkep konturlu)."""
    rng = np.random.default_rng(seed)
    pad = 300
    sk = Sk(L.w / ik.K + 2 * pad, H)
    for _ in range(n):
        x = rng.uniform(0, L.w / ik.K) + pad
        w = rng.uniform(wmin, wmax)
        h = rng.uniform(hmin, hmax)
        pts = [(x - w / 2, y0 + 4)]
        for t in np.linspace(0.05, 0.95, 9):
            pts.append((x - w / 2 + w * t, y0 - h * (math.sin(t * math.pi) ** 0.6) * rng.uniform(0.7, 1.1)))
        pts.append((x + w / 2, y0 + 4))
        p = smooth_path(pts, True, 0.35)
        for dx in (0, L.w / ik.K, -L.w / ik.K):
            q = smooth_path([(px + dx, py) for px, py in pts], True, 0.35)
            sk.path(q, col)
            top = [(px + dx, py + 3) for px, py in pts[1:-1]]
            sk.path(ribbon(top, [h * 0.22] * len(top)), top_col, 0.9)
            if ink_a > 0:
                sk.path(q, INK, ink_a, 0, 1.4)
    arr = Y.wrap_core(sk.snap(), ik.P(pad), L.w)
    _fog(arr, 0, fog_amt)
    L.over(arr)


def layer_mid(seed=40):
    L = Layer(WL, H)
    moss_drape(L, seed + 7, 18, fog_amount(0.18, 0, top=0.05), y_max=110)
    stalactite_row(L, seed, 18, 250, 64, fog_amount(0.22, 0.0, top=0.06), ink_w=1.3, detail=0.6,
                   rock_c=(42, 56, 62), light=(104, 140, 136), dark_k=0.9)
    fogm = fog_amount(0.14, 0.36, 660, 70, top=0.06)
    for x in (640, 2480):
        snake_pillar(L, x, 700, 78, int(x), fogm, dark_k=0.92)
    stalagmite_row(L, seed + 2, 10, 704, 190, 56, fog_amount(0.15, 0.3, 670, 50), ink_w=1.3, detail=0.6,
                   rock_c=(44, 58, 62), light=(104, 140, 136), dark_k=0.92)
    shore(L, seed + 4, 706, (34, 60, 60), (52, 108, 80), fog_amount(0.12, 0.3, 690, 40))
    rocks(L, seed + 5, 7, 706, 40, 24, fog_amount(0.18, 0.2, 690, 40))
    crystals_row(L, seed + 3, 13, 704, 54, fog_amount(0.06, 0.12, 690, 30), glow_a=0.6, ink_a=0.9, ink_w=1.5)
    Y.reflect(L, 708, 190, seed + 9, tint=(14, 44, 48), k_dark=0.5, ripple=3.2, shine=(150, 245, 220), shine_n=200,
              fade=0.85)
    return L


# ------------------------------------------------------------------ 6) yakın
def layer_near(seed=50):
    L = Layer(WL, H)
    stalactite_row(L, seed, 9, 300, 100, fog_amount(0.0, 0.0), ink_w=2.4, detail=0.95,
                   rock_c=(30, 36, 42), light=(80, 110, 112), rim=(120, 240, 200), dark_k=0.85,
                   xs=np.array([120, 640, 900, 1500, 2050, 2600, 2880, 3300, 3620], np.float32), cluster=0.7)
    # kıyı kaya zemini: ıslak koyu taş, üstünde yosun, yer yer su birikintisi
    rng = np.random.default_rng(seed + 11)
    pad = 300
    sk = Sk(WL + 2 * pad, H)
    pts = [(x, 772 + 16 * math.sin(x / 210.0) + 10 * math.sin(x / 67.0 + 1) + rng.uniform(-3, 3))
           for x in np.linspace(0, WL + 2 * pad, 110)]
    body = smooth_path(pts + [(WL + 2 * pad, H + 10), (0, H + 10)], True, 0.3)
    sk.path(body, (20, 30, 34))
    sk.path(ribbon([(p[0], p[1] + 5) for p in pts], [9] * len(pts)), (40, 86, 66), 0.95)
    sk.path(ribbon([(p[0], p[1] + 1) for p in pts], [2.2] * len(pts)), (110, 190, 140), 0.6)
    sk.path(ribbon(pts, [2.4] * len(pts)), INK, 0.9)
    for _ in range(40):   # yatay tabaka çizgileri
        x = rng.uniform(0, WL + 2 * pad)
        y = rng.uniform(800, 1000)
        ln = rng.uniform(40, 160)
        sk.path(ribbon([(x, y), (x + ln * 0.5, y + rng.uniform(-3, 3)), (x + ln, y + rng.uniform(-2, 2))], [0.4, 1.6, 0.4]),
                INK, 0.6)
    arr = Y.wrap_core(sk.snap(), ik.P(pad), ik.P(WL))
    L.over(arr)
    stalagmite_row(L, seed + 2, 8, 784, 300, 104, fog_amount(0.02, 0.2, 760, 40), ink_w=2.4, detail=0.95,
                   rock_c=(30, 38, 44), light=(84, 112, 114), rim=(120, 240, 200), dark_k=0.88,
                   xs=np.array([300, 1180, 1340, 2240, 3000, 3460, 3760, 1900], np.float32), cluster=0.6)
    rocks(L, seed + 5, 8, 786, 70, 40, fog_amount(0.03, 0.2, 760, 30), base=(52, 64, 68), moss=(48, 100, 70))
    crystals_row(L, seed + 3, 9, 788, 84, fog_amount(0.0, 0.05, 760, 30), glow_a=0.75, ink_a=1.0, ink_w=2.0,
                 xs=np.array([220, 700, 1250, 1720, 2160, 2700, 3120, 3400, 3720], np.float32))
    grass_field(L, seed + 6, 776, 830, 0.3, (60, 128, 90), (20, 40, 38), 6, 18, 1.6, 3.0,
                fog=fog_amount(0.05, 0.15, 780, 30), dark_strokes=0.4, ink_tips=0.3, fill=False)
    return L


# ------------------------------------------------------------------ sis / pus / ışık
def layer_haze(seed=65):
    W = WL
    ys = ik.axis(H)[:, None]
    n1 = noise(W, H, 0, seed, sx=220, sy=40)
    n2 = noise(W, H, 0, seed + 1, sx=70, sy=24)
    n3 = noise(W, H, 0, seed + 2, sx=18, sy=60)
    band = np.exp(-((ys - 600) / 110.0) ** 2) * 0.8 + np.exp(-((ys - 430) / 90.0) ** 2) * 0.25
    a = band * np.clip(0.35 + 0.7 * n1 + 0.3 * n2 + 0.2 * n3, 0, 1)
    a = np.clip(a * 0.4, 0, 0.5).astype(np.float32)
    rgb = np.repeat(ik.hd_lin(SKY)[:, None, :], ik.P(W), 1) * 0.7 + c01(MINT)[None, None, :] * 0.3
    L = Layer(W, H)
    L.a = premul(rgb, a)
    return L


def layer_fogband(seed=60):
    W = WL
    ys = ik.axis(H)[:, None]
    n1 = noise(W, H, 0, seed, sx=140, sy=14)
    n2 = noise(W, H, 0, seed + 1, sx=50, sy=7)
    band = np.exp(-((ys - 700) / 40.0) ** 2) * 0.85 + np.exp(-((ys - 650) / 30.0) ** 2) * 0.4 + np.exp(-((ys - 760) / 40.0) ** 2) * 0.35
    a = band * np.clip(0.5 + 0.6 * n1 + 0.25 * n2, 0, 1)
    a = np.clip(a * 0.6, 0, 0.75).astype(np.float32)
    rgb = np.repeat(ik.hd_lin(SKY)[:, None, :], ik.P(W), 1) * 0.55 + c01(MINT)[None, None, :] * 0.45
    L = Layer(W, H)
    L.a = premul(rgb, a)
    return L


def layer_shafts(seed=70):
    """Tavan çatlaklarından süzülen soluk yeşil ışık hüzmeleri + havada asılı ışıklı zerreler (toplamalı)."""
    W = 2880
    out = np.zeros((ik.P(H), ik.P(W)), np.float32)
    rng = np.random.default_rng(seed)
    ys = ik.axis(H)[:, None]
    xs = ik.axis(W)[None, :]
    ang = math.radians(10)
    u_all = xs * math.cos(ang) + ys * math.sin(ang)
    # aralık temel piksel ızgarasından (HD'de aynı hüzme konumları)
    ub = np.arange(W, dtype=np.float32)[None, :] * math.cos(ang) + np.arange(H, dtype=np.float32)[:, None] * math.sin(ang)
    umin, umax = float(ub.min()), float(ub.max())
    for k in range(5):
        u0 = rng.uniform(umin + 200, umax - 300)
        wid = rng.uniform(26, 90)
        out += np.exp(-((u_all - u0) / wid) ** 2) * rng.uniform(0.3, 0.6)
        out += np.exp(-((u_all - u0) / (wid * 3.5)) ** 2) * 0.08
    v = ys / H
    fade = smoothstep(0.0, 0.06, v) * (1 - smoothstep(0.42, 0.68, v))
    brk = np.clip(0.75 + 0.5 * noise(W, H, 0, seed + 5, sx=50, sy=120), 0.3, 1.0)
    out *= fade * brk
    out = np.clip(out, 0, 1)
    bl = 200
    blp = ik.P(bl)
    t = np.clip(ik.axis(bl) / (bl - 1), 0, 1)[None, :]
    out[:, :blp] = out[:, :blp] * t + out[:, -blp:] * (1 - t)
    out = out[:, :out.shape[1] - blp]
    W2 = W - bl
    col = c01((120, 230, 190))
    rgb = col[None, None, :] * out[..., None]
    a = out.copy()
    # ışıklı zerreler (spor, su damlası parıltısı)
    sk = Sk(W2, H)
    for _ in range(170):
        x, y = rng.uniform(0, W2), rng.uniform(80, 760)
        r = rng.uniform(0.8, 2.6)
        c = (190, 255, 230) if rng.random() < 0.8 else (230, 200, 255)
        sk.c.drawCircle(x, y, r * 3.5, sk.paint(c, 0.18, r * 2.5))
        sk.c.drawCircle(x, y, r, sk.paint(c, 0.85, 0.4))
    m = sk.snap()
    rgb = m[..., :3] + rgb * (1 - m[..., 3:4])
    a = m[..., 3] + a * (1 - m[..., 3])
    L = Layer(W2, H)
    L.a = np.concatenate([rgb, a[..., None]], -1).astype(np.float32)
    return L


# ------------------------------------------------------------------ boss arenası: Şahmeran Ana'nın taht salonu
def throne_sahmeran(L, cx, base_y, fog_amt, seed=7):
    """Gölün kıyısında taht: basamaklı taş kürsü, sarmal yılan gövdesinden oturak, arkada dev kukulete (pullu,
    göz desenli), tepede taçlı yılan başı ve kehribar gözler; kürsüde ışıyan kristaller."""
    rng = np.random.default_rng(seed)
    pad = 500
    W = 1100
    sk = Sk(W + 2 * pad, H)
    x = W / 2 + pad
    stone, stone_l, stone_d = (70, 92, 92), (140, 176, 166), (34, 46, 50)
    snake, snake_l, belly = (52, 84, 72), (120, 170, 140), (110, 120, 96)
    # kukulete (arka): dev kobra, önden — boyun dar, ortada geniş açılan kukulete, ön yüzde enine karın pulları
    top = base_y - 600
    hood = smooth_path([(x - 120, base_y - 150), (x - 210, base_y - 290), (x - 250, base_y - 400), (x - 190, base_y - 500),
                        (x - 70, top + 40), (x, top + 20), (x + 70, top + 40), (x + 190, base_y - 500), (x + 250, base_y - 400),
                        (x + 210, base_y - 290), (x + 120, base_y - 150)], True, 0.4)
    sk.path(hood, snake)
    sk.c.save()
    sk.c.clipPath(hood, doAntiAlias=True)
    # kenara doğru koyulaşan kukulete, ortada açık karın şeridi
    sk.path(smooth_path([(x - 250, base_y - 420), (x - 190, base_y - 510), (x - 120, base_y - 300), (x - 140, base_y - 150),
                         (x - 260, base_y - 150)], True, 0.4), (30, 52, 46), 0.7)
    sk.path(smooth_path([(x + 250, base_y - 420), (x + 190, base_y - 510), (x + 120, base_y - 300), (x + 140, base_y - 150),
                         (x + 260, base_y - 150)], True, 0.4), (30, 52, 46), 0.85)
    belly_band = smooth_path([(x - 70, base_y - 150), (x - 90, base_y - 330), (x - 70, top + 70), (x, top + 50), (x + 70, top + 70),
                              (x + 90, base_y - 330), (x + 70, base_y - 150)], True, 0.4)
    sk.path(belly_band, (112, 124, 98), 0.8)
    yy = top + 70
    k = 0
    while yy < base_y - 150:
        wv = 70 + 20 * math.sin((yy - top) / 420 * math.pi)
        sk.path(smooth_path([(x - wv, yy + 6), (x, yy), (x + wv, yy + 6)], False, 0.5), INK, 0.6, 0, 1.6)
        yy += 26 - k * 0.2
        k += 1
    for r in range(10):   # yan pullar
        yy = base_y - 200 - r * 36
        for kk in range(-7, 8):
            if abs(kk) < 3:
                continue
            px = x + kk * 32 + (16 if r % 2 else 0)
            sk.path(smooth_path([(px - 12, yy), (px, yy - 13), (px + 12, yy)], False, 0.5), INK, 0.35, 0, 1.3)
    sk.c.restore()
    sk.path(hood, INK, 0.9, 0, 3.0)
    # taçlı baş: kukuletanın tepesinde öne eğik
    hx, hy = x, top + 10
    head = smooth_path([(hx - 44, hy + 14), (hx - 50, hy - 26), (hx - 26, hy - 64), (hx, hy - 72), (hx + 26, hy - 64), (hx + 50, hy - 26),
                        (hx + 44, hy + 14), (hx + 20, hy + 40), (hx - 20, hy + 40)], True, 0.4)
    sk.path(head, snake_l)
    sk.path(smooth_path([(hx + 10, hy - 66), (hx + 50, hy - 26), (hx + 44, hy + 14), (hx + 20, hy + 40), (hx + 6, hy + 40)], True, 0.4), snake, 0.55)
    sk.path(head, INK, 0.9, 0, 2.6)
    sk.path(ribbon([(hx - 18, hy + 30), (hx, hy + 34), (hx + 18, hy + 30)], [1.0, 2.4, 1.0]), INK, 0.9)
    sk.path(ribbon([(hx, hy + 36), (hx - 2, hy + 62), (hx - 10, hy + 74)], [2.2, 1.6, 0.6]), (190, 60, 60))
    sk.path(ribbon([(hx - 2, hy + 62), (hx + 8, hy + 74)], [1.4, 0.6]), (190, 60, 60))
    crown = poly_path([(hx - 40, hy - 52), (hx - 50, hy - 112), (hx - 22, hy - 84), (hx, hy - 136), (hx + 22, hy - 84), (hx + 50, hy - 112), (hx + 40, hy - 52)])
    sk.path(crown, (196, 160, 80))
    sk.path(poly_path([(hx - 40, hy - 52), (hx + 40, hy - 52), (hx + 42, hy - 62), (hx - 42, hy - 62)]), (150, 110, 50), 0.9)
    sk.path(crown, INK, 0.9, 0, 2.2)
    for sd in (-1, 1):
        ep = smooth_path([(hx + sd * 12, hy - 18), (hx + sd * 24, hy - 26), (hx + sd * 34, hy - 16), (hx + sd * 22, hy - 10)], True, 0.4)
        sk.path(ep, AMBER)
        sk.path(ep, INK, 0.9, 0, 1.4)
        sk.path(ribbon([(hx + sd * 23, hy - 24), (hx + sd * 23, hy - 12)], [1.6, 1.6]), INK, 0.9)
        sk.c.drawCircle(hx + sd * 23, hy - 18, 20, sk.paint(AMBER, 0.25, 10))
    Y.crystal_cluster(sk, hx, hy - 92, 40, seed + 3, EMER, EMER_HI, (10, 64, 60), ink_w=1.6, glow=sk, glow_a=0.6, n=3, spread=0.5)
    # oturak: üç sarmal halka
    for i, (yy, rx, w) in enumerate([(base_y - 110, 230, 56), (base_y - 160, 200, 50), (base_y - 205, 170, 44)]):
        band = np.array([(x + rx * math.cos(a), yy + 22 * math.sin(a)) for a in np.linspace(0, math.pi, 30)])
        sk.path(ribbon(band, [w] * 30), snake)
        sk.path(ribbon(band + np.array([0, w * 0.28]), [w * 0.3] * 30), belly, 0.85)
        sk.path(ribbon(band - np.array([0, w * 0.26]), [w * 0.2] * 30), snake_l, 0.8)
        for j in range(1, 29, 2):
            q = band[j]
            sk.path(smooth_path([(q[0] - 8, q[1] + 4), (q[0], q[1] - 6), (q[0] + 8, q[1] + 4)], False, 0.5), INK, 0.5, 0, 1.2)
        sk.path(ribbon(band, [w] * 30), INK, 0.9, 0, 2.4)
    # kürsü basamakları
    for i, (hw_, yy, hh) in enumerate([(340, base_y - 26, 30), (290, base_y - 52, 28), (240, base_y - 78, 26)]):
        p = poly_path([(x - hw_, yy + hh), (x - hw_, yy), (x + hw_, yy), (x + hw_, yy + hh)])
        sk.path(p, stone)
        sk.path(poly_path([(x - hw_, yy), (x + hw_, yy), (x + hw_, yy + 5), (x - hw_, yy + 5)]), stone_l, 0.75)
        sk.path(poly_path([(x + hw_ * 0.4, yy + 5), (x + hw_, yy + 5), (x + hw_, yy + hh), (x + hw_ * 0.4, yy + hh)]), stone_d, 0.5)
        for k in range(int(hw_ / 26)):
            px = x - hw_ + 20 + k * 52
            sk.path(smooth_path([(px - 10, yy + hh - 6), (px, yy + 8), (px + 10, yy + hh - 6)], False, 0.5), INK, 0.6, 0, 1.4)
        sk.path(p, INK, 0.9, 0, 2.2)
    for sd in (-1, 1):
        Y.crystal_cluster(sk, x + sd * 310, base_y - 26, 90, seed + 10 + sd, EMER, EMER_HI, (10, 64, 60), ink_w=2.0, glow=sk,
                          glow_a=0.6, n=6)
        Y.crystal_cluster(sk, x + sd * 380, base_y, 60, seed + 20 + sd, AMETH, AMETH_HI, (40, 20, 70), ink_w=1.6, glow=sk,
                          glow_a=0.5, n=4)
    arr = sk.snap()
    _fog(arr, 0, fog_amt)
    Y.place_arr(L, arr, ik.P(cx - W / 2 - pad), 0)


def layer_mid_boss(seed=40):
    L = Layer(WL, H)
    moss_drape(L, seed + 7, 18, fog_amount(0.18, 0, top=0.05), y_max=110)
    stalactite_row(L, seed, 16, 250, 64, fog_amount(0.22, 0.0, top=0.06), ink_w=1.3, detail=0.6,
                   rock_c=(42, 56, 62), light=(104, 140, 136), dark_k=0.9,
                   xs=np.random.default_rng(seed).uniform(0, WL, 16))
    fogm = fog_amount(0.14, 0.36, 660, 70, top=0.06)
    for x in (900, 2060, 3300):
        snake_pillar(L, x, 700, 82, int(x), fogm, dark_k=0.92)
    throne_sahmeran(L, 1480, 706, fog_amount(0.1, 0.3, 660, 60, top=0.04))
    shore(L, seed + 4, 706, (34, 60, 60), (52, 108, 80), fog_amount(0.12, 0.3, 690, 40), n=4)
    crystals_row(L, seed + 3, 8, 704, 54, fog_amount(0.06, 0.12, 690, 30), glow_a=0.6, ink_a=0.9, ink_w=1.5,
                 xs=np.array([300, 640, 2500, 2800, 3600, 3100, 450, 2650], np.float32))
    Y.reflect(L, 708, 190, seed + 9, tint=(14, 44, 48), k_dark=0.5, ripple=3.2, shine=(150, 245, 220), shine_n=200,
              fade=0.85)
    return L


EXPORT_BG = [('0_sky', 'layer_sky'), ('1_far', 'layer_far'), ('2_farmid', 'layer_farmid'), ('2b_haze', 'layer_haze'),
             ('3_mid', 'layer_mid'), ('4_fog', 'layer_fogband'), ('5_shafts', 'layer_shafts'), ('6_near', 'layer_near'),
             ('3_mid_boss', 'layer_mid_boss')]
