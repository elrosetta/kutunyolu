"""Tamu / Erlik'in Ülkesi, stil v2 "mürekkep" paralaks katmanları (Ötüken ile aynı çizgi roman dili).

Kökün dibindeki zindan: tutulmuş kara güneş (ateş tacı), duman tavanı, uzakta Erlik Han'ın boynuzlu demir kalesi,
volkanik sırtlardan dökülen lav şelaleleri ve ufukta kabuklu lav denizi; bazalt sütun kümeleri (org boruları),
aralarına gerili zincirler, dev bir yaratığın kaburga kemerleri ve boynuzlu öküz kafatası; havada kül ve kor.
Işık aşağıdan gelir (lav): her biçimin alt kenarı ve lava bakan yüzü sıcak, üstü is-karası.

Katmanlar (1080 yükseklik, 1080p'de 1:1; data/stil_v2.json "tamu"):
  0 gök (1920, sabit)  1 uzak sırtlar + kale + lav denizi  2 bazalt yarları + şelaleler  2b duman
  3 kaburga kemerleri + zincirli sütunlar + lav ırmağı  4 alçak duman  5 lav ışıması + kor (toplamalı)  6 yakın
"""
import math

import numpy as np
from scipy import ndimage

import inkkit_ortam as ik
from inkkit_ortam import INK, Layer, Sk, bezier, blob, c01, fbm, mix, noise, poly_path, premul, ribbon, smooth_path, smoothstep
import inkkit_yeralti as Y

H = 1080
WL = 3840

SKY = Y.ramp([
    (0, (10, 4, 6)),
    (200, (20, 8, 10)),
    (380, (40, 13, 13)),
    (500, (84, 26, 18)),
    (575, (160, 58, 26)),
    (622, (236, 116, 46)),
    (648, (150, 50, 24)),
    (720, (60, 18, 14)),
    (860, (24, 8, 8)),
    (1080, (10, 4, 5)),
])
EMBER = (255, 150, 60)
LAVA_CORE = (255, 226, 150)
LAVA_MID = (255, 120, 36)
LAVA_CRUST = (120, 26, 16)
BASALT = (54, 46, 54)
BASALT_LIT = (176, 76, 46)
RIM = (255, 128, 56)
BONE = (160, 136, 116)
BONE_SH = (70, 40, 38)
BONE_HI = (232, 214, 186)
IRON = (58, 50, 54)
IRON_HI = (170, 110, 90)

fog_amount = Y.fog_amount


def _fog(arr, y0, amt):
    return ik.apply_fog(arr, y0, SKY, amt)


# ------------------------------------------------------------------ 0) gök: tutulmuş güneş + duman
def layer_sky(seed=1):
    W = 1920
    L = Layer(W, H)
    rgb = np.repeat(SKY[:, None, :], W, 1).copy()
    ys = np.arange(H, dtype=np.float32)[:, None]
    xs = np.arange(W, dtype=np.float32)[None, :]
    sx, sy, R = 1240.0, 250.0, 74.0
    d = np.hypot(xs - sx, ys - sy)
    ang = np.arctan2(ys - sy, xs - sx)
    # taç: açısal gürültülü ışınlar + yumuşak hale
    a_n = np.interp((ang + math.pi) / (2 * math.pi) * 720, np.arange(721), np.r_[noise(720, 1, 0, seed, sx=4, sy=0.01)[0], 0])
    a_n2 = np.interp((ang + math.pi) / (2 * math.pi) * 720, np.arange(721), np.r_[noise(720, 1, 0, seed + 1, sx=14, sy=0.01)[0], 0])
    rays = np.clip(0.5 + 0.8 * a_n + 0.4 * a_n2, 0, 1.4)
    corona = np.exp(-np.maximum(d - R, 0) / (36 + 70 * rays)) * (d > R - 1)
    halo = np.exp(-((d - R) / 300.0) ** 2) * 0.5
    rgb = mix(rgb, c01((255, 120, 50))[None, None, :], np.clip(halo * 0.6, 0, 1)[..., None])
    rgb = mix(rgb, c01((255, 170, 90))[None, None, :], np.clip(corona * 0.85, 0, 1)[..., None])
    ring = np.exp(-((d - R) / 2.6) ** 2)
    rgb = mix(rgb, c01((255, 236, 190))[None, None, :], np.clip(ring, 0, 1)[..., None])
    disc = np.clip(R - d + 0.5, 0, 1)
    rgb = mix(rgb, c01((6, 2, 4))[None, None, :], disc[..., None])
    n1 = fbm(W, H, [110, 40, 14], seed + 3)
    rgb *= (1 + 0.06 * n1[..., None])
    L.a = premul(rgb, np.ones((H, W), np.float32))
    # duman bulut kuşakları (alt yüzleri lavla aydınlanmış), güneşin önünden geçen ince şerit
    sm = Y.smoke_layer(W, H, seed + 5, [(120, 70, 0.9), (330, 60, 0.7), (470, 40, 0.6)], (26, 10, 12), (70, 24, 18),
                       under=(220, 90, 40), alpha=0.85, sx=200, sy=36)
    L.over(sm)
    # kor yıldızları
    g = Sk(W, H)
    rng = np.random.default_rng(seed + 7)
    for _ in range(140):
        x, y = rng.uniform(0, W), rng.uniform(0, 620)
        r = rng.uniform(0.6, 1.8)
        g.c.drawCircle(x, y, r, g.paint((255, 170, 90), rng.uniform(0.3, 0.9)))
    L.over(g.snap())
    return L


# ------------------------------------------------------------------ yardımcılar
def ridge_shape(x0, x1, base, peak, seed, n=24, jag=0.25):
    rng = np.random.default_rng(seed)
    xs = np.linspace(x0, x1, n)
    pts = [(x0, base + 20)]
    for i, x in enumerate(xs):
        t = i / (n - 1)
        h = peak * (math.sin(t * math.pi) ** 0.8) * (1 + rng.uniform(-jag, jag))
        pts.append((x, base - h))
    pts.append((x1, base + 20))
    return poly_path(pts), pts


def fortress(sk, x, base_y, s, col, win, seed, ink_a=0.6):
    """Erlik Han'ın kalesi: sivri kayalık üstünde demir burçlar, burç başlarında öküz boynuzları, ortada boynuzlu
    taht kulesi; mazgallarda kızıl ışık; kale duvarından lav dökülür (çağıran ekler)."""
    rng = np.random.default_rng(seed)
    crag = [(x - 230 * s, base_y + 20), (x - 180 * s, base_y - 90 * s), (x - 120 * s, base_y - 130 * s), (x - 40 * s, base_y - 160 * s),
            (x + 60 * s, base_y - 150 * s), (x + 150 * s, base_y - 110 * s), (x + 220 * s, base_y - 40 * s), (x + 250 * s, base_y + 20)]
    sk.path(poly_path(crag), col)
    towers = [(-120, 150, 18), (-60, 210, 22), (0, 300, 30), (70, 230, 22), (130, 160, 18)]
    for (dx, th, tw) in towers:
        tx = x + dx * s
        ty = base_y - 140 * s
        top = ty - th * s
        body = poly_path([(tx - tw * s, ty), (tx - tw * 0.8 * s, top), (tx + tw * 0.8 * s, top), (tx + tw * s, ty)])
        sk.path(body, tuple(np.array(col) * 1.1))
        spire = poly_path([(tx - tw * 0.9 * s, top), (tx, top - tw * 1.8 * s), (tx + tw * 0.9 * s, top)])
        sk.path(spire, tuple(np.array(col) * 1.2))
        # öküz boynuzları
        for side in (-1, 1):
            horn = ribbon(bezier((tx + side * tw * 0.6 * s, top - tw * 0.6 * s), (tx + side * tw * 2.0 * s, top - tw * 0.4 * s),
                                 (tx + side * tw * 1.6 * s, top - tw * 2.4 * s), 10), np.linspace(5 * s, 0.6, 10))
            sk.path(horn, tuple(np.array(col) * 1.35))
            if ink_a > 0:
                sk.path(horn, INK, ink_a, 0, 1.0)
        for k in range(int(th / 40)):
            wy = ty - (20 + k * 40) * s
            sk.path(poly_path([(tx - 3 * s, wy), (tx + 3 * s, wy), (tx + 3 * s, wy - 9 * s), (tx - 3 * s, wy - 9 * s)]), win, rng.uniform(0.6, 1.0))
        if ink_a > 0:
            sk.path(body, INK, ink_a, 0, 1.2)
            sk.path(spire, INK, ink_a, 0, 1.2)
    # sur duvarı
    wall = poly_path([(x - 150 * s, base_y - 120 * s), (x + 160 * s, base_y - 120 * s), (x + 160 * s, base_y - 150 * s), (x - 150 * s, base_y - 150 * s)])
    sk.path(wall, tuple(np.array(col) * 1.05))
    for k in range(16):
        mx = x - 146 * s + k * 19 * s
        sk.path(poly_path([(mx, base_y - 150 * s), (mx + 9 * s, base_y - 150 * s), (mx + 9 * s, base_y - 160 * s), (mx, base_y - 160 * s)]), tuple(np.array(col) * 1.05))
    # kapı: boynuzlu kafatası kemeri, içinde ateş
    gx, gy = x, base_y - 120 * s
    gate = smooth_path([(gx - 22 * s, gy), (gx - 22 * s, gy - 22 * s), (gx, gy - 36 * s), (gx + 22 * s, gy - 22 * s), (gx + 22 * s, gy)], True, 0.3)
    sk.path(gate, win, 0.95)


def lava_sea(L, y0, y1, seed, bright=1.0, fog_k=0.0, scale=1.0):
    """Ufka uzanan kabuklu lav denizi: ufukta sıkışan (perspektif) kabuk plakaları, aralarında ışıyan çatlaklar;
    ufuk çizgisi en parlak, öne doğru kabuk kalınlaşır ve kararır."""
    W = L.w
    S = 512
    n1 = noise(W, S, 0, seed, sx=34 * scale, sy=10)
    n2 = noise(W, S, 0, seed + 1, sx=12 * scale, sy=5)
    ridge = (1 - np.abs(n1)) ** 7 + 0.5 * (1 - np.abs(n2)) ** 9
    blobs = smoothstep(0.35, 0.9, noise(W, S, 0, seed + 2, sx=60 * scale, sy=16) * 0.5 + 0.5)
    rows = np.arange(ik.P(y1 - y0), dtype=np.float32)
    t = rows / max(1, len(rows) - 1)
    src = np.clip((t ** 1.7) * (S - 1), 0, S - 1).astype(int)
    R = ridge[src]
    B = blobs[src]
    heat = np.clip(R * 1.2 + B * 0.5, 0, 1.4)
    horizon = np.exp(-t / 0.08)[:, None]
    heat = np.clip(heat * (0.55 + 0.45 * (1 - t))[:, None] + horizon * 0.8, 0, 1.5) * bright
    crust = mix(c01((34, 10, 10))[None, None, :], c01((70, 20, 14))[None, None, :], (B * 0.6)[..., None])
    col = mix(crust, c01(LAVA_CRUST)[None, None, :] * 1.6, smoothstep(0.1, 0.4, heat)[..., None])
    col = mix(col, c01(LAVA_MID)[None, None, :], smoothstep(0.35, 0.8, heat)[..., None])
    col = mix(col, c01(LAVA_CORE)[None, None, :], smoothstep(0.85, 1.3, heat)[..., None])
    col *= (1 - 0.45 * t)[:, None, None]
    if fog_k > 0:
        col = mix(col, SKY[ik.P(y0):ik.P(y0) + len(rows)][:, None, :], fog_k)
    a = np.ones(col.shape[:2], np.float32)
    a[0] = 0.5
    arr = premul(col.astype(np.float32), a)
    L.over(arr, 0, y0)


def prism_cluster(L, seed, x, base_y, n, hmin, hmax, wmin, wmax, fog_amt, dark_k=1.0, ink_w=1.6, detail=0.8,
                  col=BASALT, lit=BASALT_LIT, rim=RIM, wrap=True):
    """Org borusu bazalt kümesi: yan yana, ortası yüksek altıgen sütunlar (arkadakiler önce)."""
    rng = np.random.default_rng(seed)
    cols = []
    xx = x - n * (wmin + wmax) / 4
    for i in range(n):
        w = rng.uniform(wmin, wmax)
        t = i / max(1, n - 1)
        h = hmin + (hmax - hmin) * math.sin(t * math.pi) ** 0.7 * rng.uniform(0.7, 1.05)
        cols.append((xx + w / 2, w, h))
        xx += w * rng.uniform(0.82, 0.96)
    order = sorted(range(n), key=lambda i: cols[i][2])     # kısa olan öne: önce uzunları çiz
    for i in order[::-1]:
        cx, w, h = cols[i]
        by = base_y + rng.uniform(-4, 6)
        arr, xl, yt = Y.basalt_prism(by - h, by, cx, w, int(rng.integers(1 << 30)), col=col, lit=lit, rim=rim,
                                     ink_w=ink_w, detail=detail, rim_side=1.0 if cx > x else -1.0)
        arr[..., :3] *= dark_k
        _fog(arr, ik.P(yt), fog_amt)
        Y.place_arr(L, arr, ik.P(xl), ik.P(yt), wrap)


def ribcage(L, x, base_y, span, height, seed, fog_amt, dark_k=1.0, n=7, ink_k=1.0, width=22):
    """Dev yaratık iskeleti: kavisli omurga ve ondan yere inen kaburga kemerleri (arkadakiler koyu)."""
    rng = np.random.default_rng(seed)
    pad = 300
    sk = Sk(span + 2 * pad + 400, H)
    ox = pad + 200
    spine = bezier((ox - 40, base_y - height * 0.55), (ox + span * 0.45, base_y - height * 1.08), (ox + span + 60, base_y - height * 0.6), 30)
    bone = tuple(np.array(BONE) * dark_k)
    sh = tuple(np.array(BONE_SH) * dark_k)
    hi = tuple(np.array(BONE_HI) * dark_k)
    # arka kaburgalar (öbür yan): ince, koyu
    for i in range(n):
        t = (i + 0.5) / n
        p0 = spine[int(t * 29)]
        foot = (p0[0] - span * 0.08 + rng.uniform(-10, 10), base_y + 4)
        ctrl = (p0[0] - span * 0.22, p0[1] + height * 0.25)
        Y.rib(sk, p0, ctrl, foot, width * 0.6, col=tuple(np.array(BONE) * 0.55 * dark_k), shade=tuple(np.array(BONE_SH) * 0.6 * dark_k),
              hi=tuple(np.array(BONE) * 0.7 * dark_k), ink_a=0.6 * ink_k, ink_w=1.4)
    # omurga ve omurlar
    Y.rib(sk, spine[0], spine[15], spine[-1], width * 1.4, col=bone, shade=sh, hi=hi, ink_a=ink_k, ink_w=2.0, n=30)
    for j in range(2, 29, 2):
        q = spine[j]
        sk.path(poly_path([(q[0] - 5, q[1] - width * 0.5), (q[0] + 3, q[1] - width * 1.3), (q[0] + 8, q[1] - width * 0.5)]), bone)
        sk.path(poly_path([(q[0] - 5, q[1] - width * 0.5), (q[0] + 3, q[1] - width * 1.3), (q[0] + 8, q[1] - width * 0.5)]), INK, ink_k, 0, 1.2)
    # ön kaburgalar: kalın, öne kavisli
    for i in range(n):
        t = (i + 0.3) / n
        p0 = spine[int(t * 29)]
        foot = np.array((p0[0] + span * 0.12 + rng.uniform(-14, 14), base_y + 6))
        ctrl = np.array((p0[0] + span * 0.3, p0[1] + height * 0.2))
        if rng.random() < 0.3:      # kırık kaburga: yarıda biter
            k = rng.uniform(0.45, 0.7)
            foot = (1 - k) ** 2 * np.array(p0) + 2 * (1 - k) * k * ctrl + k * k * foot
            ctrl = (np.array(p0) + ctrl) / 2
        Y.rib(sk, p0, tuple(ctrl), tuple(foot), width * (1.0 - 0.3 * abs(t - 0.5)), col=bone, shade=sh, hi=hi, ink_a=ink_k, ink_w=2.2)
    arr = sk.snap()
    _fog(arr, 0, fog_amt)
    Y.place_arr(L, arr, ik.P(x - ox), 0)


def ox_skull(sk, x, base_y, s, col=BONE, sh=BONE_SH, hi=BONE_HI, eye=(255, 120, 40), ink_k=1.0):
    """Yerde yatan dev boynuzlu öküz kafatası (Erlik'in simgesi); göz çukurlarında kor."""
    sk.path(smooth_path([(x - 60 * s, base_y), (x - 70 * s, base_y - 50 * s), (x - 40 * s, base_y - 90 * s), (x, base_y - 100 * s),
                         (x + 40 * s, base_y - 90 * s), (x + 70 * s, base_y - 50 * s), (x + 60 * s, base_y), (x + 30 * s, base_y + 10 * s),
                         (x - 30 * s, base_y + 10 * s)], True, 0.4), col)
    head = smooth_path([(x - 60 * s, base_y), (x - 70 * s, base_y - 50 * s), (x - 40 * s, base_y - 90 * s), (x, base_y - 100 * s),
                        (x + 40 * s, base_y - 90 * s), (x + 70 * s, base_y - 50 * s), (x + 60 * s, base_y), (x + 30 * s, base_y + 10 * s),
                        (x - 30 * s, base_y + 10 * s)], True, 0.4)
    sk.c.save()
    sk.c.clipPath(head, doAntiAlias=True)
    sk.path(blob(x + 30 * s, base_y - 20 * s, 60 * s, 60 * s, 3, 10, 0.1), sh, 0.6)
    sk.path(blob(x - 30 * s, base_y - 70 * s, 30 * s, 20 * s, 4, 10, 0.1), hi, 0.5)
    sk.c.restore()
    for side in (-1, 1):
        horn = bezier((x + side * 55 * s, base_y - 78 * s), (x + side * 150 * s, base_y - 110 * s), (x + side * 130 * s, base_y - 210 * s), 16)
        sk.path(ribbon(horn, np.linspace(30 * s, 2, 16)), col)
        sk.path(ribbon(horn + np.array([side * 5 * s, 6 * s]), np.linspace(16 * s, 1, 16)), sh, 0.6)
        for j in range(2, 14, 2):
            q = horn[j]
            sk.path(ribbon([(q[0] - 8 * s, q[1] + 3 * s), (q[0] + 8 * s, q[1] - 3 * s)], [0.5, 0.5]), INK, 0.5 * ink_k)
        sk.path(ribbon(horn, np.linspace(30 * s, 2, 16)), INK, ink_k, 0, 1.8)
        ex = x + side * 26 * s
        eye_p = smooth_path([(ex - 14 * s, base_y - 56 * s), (ex, base_y - 66 * s), (ex + 14 * s, base_y - 54 * s), (ex, base_y - 44 * s)], True, 0.4)
        sk.path(eye_p, (12, 4, 6))
        sk.c.drawCircle(ex, base_y - 55 * s, 4 * s, sk.paint(eye, 0.95))
        sk.c.drawCircle(ex, base_y - 55 * s, 10 * s, sk.paint(eye, 0.35, 6 * s))
    for side in (-1, 1):
        sk.path(smooth_path([(x + side * 6 * s, base_y - 20 * s), (x + side * 14 * s, base_y - 4 * s), (x + side * 4 * s, base_y - 2 * s)], True, 0.4), (12, 4, 6))
    sk.path(head, INK, ink_k, 0, 2.2)
    for k in range(3):
        sk.path(ribbon([(x - 20 * s + k * 18 * s, base_y - 96 * s), (x - 16 * s + k * 18 * s, base_y - 80 * s)], [1.2, 0.3]), INK, 0.6 * ink_k)


def chains_between(L, seed, posts, y_top, fog_amt, dark_k=1.0, link=11, sag=(60, 140), col=IRON, hi=IRON_HI, extra_hang=6):
    """Sütunlar arasında sarkan zincirler + tavandan sarkan kancalı zincirler."""
    rng = np.random.default_rng(seed)
    pad = 300
    sk = Sk(L.w / ik.K + 2 * pad, H)
    c = tuple(np.array(col) * dark_k)
    h = tuple(np.array(hi) * dark_k)
    for (xa, ya), (xb, yb) in posts:
        for dx in (0, L.w / ik.K, -L.w / ik.K):
            Y.chain(sk, (xa + pad + dx, ya), (xb + pad + dx, yb), rng.uniform(*sag), link=link, col=c, hi=h)
    for _ in range(extra_hang):
        x = rng.uniform(0, L.w / ik.K) + pad
        ln = rng.uniform(120, 360)
        for dx in (0, L.w / ik.K, -L.w / ik.K):
            Y.chain(sk, (x + dx, y_top - 10), (x + dx + 0.5, y_top + ln), 0, link=link, col=c, hi=h)
            # kanca
            hk = bezier((x + dx, y_top + ln + 4), (x + dx + 14, y_top + ln + 24), (x + dx - 2, y_top + ln + 30), 10)
            sk.path(ribbon(hk, np.linspace(4, 1.5, 10)), c)
            sk.path(ribbon(hk, np.linspace(4, 1.5, 10)), INK, 1.0, 0, 1.0)
    arr = Y.wrap_core(sk.snap(), pad, L.w)
    _fog(arr, 0, fog_amt)
    L.over(arr)


def ash_ground(L, seed, y0, fog_amt, col=(34, 26, 30), top=(92, 80, 80), cracks=True, bumps=18, ember_n=60):
    """Kül kaplı bazalt zemin şeridi: üst kenarda açık kül, içinde ışıyan lav çatlakları ve kor noktaları."""
    rng = np.random.default_rng(seed)
    pad = 200
    W = L.w / ik.K
    sk = Sk(W + 2 * pad, H)
    pts = [(x, y0 + bumps * 0.5 * math.sin(x / 190.0) + bumps * 0.3 * math.sin(x / 61.0 + 2) + rng.uniform(-2, 2))
           for x in np.linspace(0, W + 2 * pad, 120)]
    sk.path(smooth_path(pts + [(W + 2 * pad, H + 10), (0, H + 10)], True, 0.3), col)
    sk.path(ribbon([(p[0], p[1] + 3) for p in pts], [6] * len(pts)), top, 0.9)
    sk.path(ribbon([(p[0], p[1] + 0.5) for p in pts], [1.6] * len(pts)), (200, 120, 90), 0.6)
    sk.path(ribbon(pts, [2.2] * len(pts)), INK, 0.9)
    if cracks:
        for _ in range(int(W / 90)):
            x = rng.uniform(0, W) + pad
            y = y0 + rng.uniform(14, 120)
            q = [(x, y)]
            for k in range(int(rng.integers(3, 7))):
                q.append((q[-1][0] + rng.uniform(8, 26), q[-1][1] + rng.uniform(-8, 8)))
            ws = np.linspace(rng.uniform(1.5, 3.5), 0.5, len(q))
            sk.path(ribbon(q, ws * 3), (255, 90, 30), 0.25, 3)
            sk.path(ribbon(q, ws * 1.4), INK, 0.9)
            sk.path(ribbon(q, ws * 0.7), (255, 170, 70), 1.0)
    for _ in range(ember_n):
        x, y = rng.uniform(0, W) + pad, y0 + rng.uniform(4, 60)
        sk.c.drawCircle(x, y, rng.uniform(0.8, 1.8), sk.paint((255, 160, 70), rng.uniform(0.5, 1)))
    arr = Y.wrap_core(sk.snap(), pad, L.w)
    _fog(arr, 0, fog_amt)
    L.over(arr)


# ------------------------------------------------------------------ 1) uzak sırtlar + kale + lav denizi
def layer_far(seed=20):
    L = Layer(WL, H)
    rng = np.random.default_rng(seed)
    pad = 300
    glowL = Layer(WL, H)
    sk = Sk(WL + 2 * pad, H)
    for k in range(6):
        x0 = rng.uniform(0, WL) + pad - 400
        p, pts = ridge_shape(x0, x0 + rng.uniform(600, 1100), 640, rng.uniform(140, 320), int(x0), jag=0.3)
        sk.path(p, (44, 16, 16))
    arr = Y.wrap_core(sk.snap(), pad, WL)
    _fog(arr, 0, fog_amount(0.5, 0.3, 620, 80, top=0.1))
    L.over(arr)
    sk = Sk(WL + 2 * pad, H)
    fortress(sk, 1300 + pad, 640, 1.0, (30, 12, 14), (255, 90, 40), seed + 4, ink_a=0.5)
    arr = Y.wrap_core(sk.snap(), pad, WL)
    _fog(arr, 0, fog_amount(0.32, 0.2, 620, 60))
    L.over(arr)
    for (x, top, w) in ((1300, 500, 10), (1180, 520, 6), (2650, 420, 12), (3350, 470, 8), (480, 450, 9)):
        Y.lava_fall(L, x, top, 650, w, int(x), glow_L=glowL, fog_k=0.15, fog_col=(150, 50, 24), splash=False)
    L.a = glowL.a * 0.6 + L.a * (1 - glowL.a[..., 3:4] * 0.6)
    lava_sea(L, 640, 820, seed + 9, bright=1.1, fog_k=0.15)
    Y.reflect(L, 642, 120, seed + 11, tint=(120, 40, 20), k_dark=0.5, ripple=1.5, shine=(255, 200, 120), shine_n=60, fade=0.5)
    return L


# ------------------------------------------------------------------ 2) bazalt yarları + şelaleler
def layer_farmid(seed=30):
    L = Layer(WL, H)
    rng = np.random.default_rng(seed)
    glowL = Layer(WL, H)
    sm = Y.smoke_layer(WL, H, seed + 6, [(200, 120, 0.6)], (40, 14, 14), (90, 30, 20), under=(200, 80, 40), alpha=0.6, sx=160, sy=60)
    L.over(sm)
    for k, x in enumerate((300, 1250, 2100, 3000)):
        prism_cluster(L, seed + k, x, 668, int(rng.integers(6, 11)), 160, rng.uniform(300, 430), 26, 46,
                      fog_amount(0.38, 0.3, 640, 60, top=0.1), dark_k=0.85, ink_w=1.0, detail=0.5)
    for x in (700, 1680, 2560, 3500):
        Y.lava_fall(L, x + rng.uniform(-40, 40), rng.uniform(380, 480), 672, rng.uniform(10, 16), int(x), glow_L=glowL,
                    fog_k=0.1, fog_col=(160, 50, 24))
    L.a = glowL.a * 0.7 + L.a * (1 - glowL.a[..., 3:4] * 0.7)
    lava_sea(L, 668, 860, seed + 9, bright=0.95, scale=1.3)
    Y.reflect(L, 670, 140, seed + 11, tint=(110, 34, 18), k_dark=0.5, ripple=2.0, shine=(255, 200, 120), shine_n=90, fade=0.55)
    return L


# ------------------------------------------------------------------ 3) kaburga + zincirli sütunlar
def layer_mid(seed=40):
    L = Layer(WL, H)
    rng = np.random.default_rng(seed)
    fogm = fog_amount(0.16, 0.34, 660, 70, top=0.06)
    # zincir taşıyan uzun sütunlar
    posts = []
    xs = [380, 900, 2650, 3250]
    for x in xs:
        prism_cluster(L, int(x), x, 708, int(rng.integers(2, 4)), 300, 520, 36, 54, fogm, dark_k=0.85, ink_w=1.4, detail=0.7)
        posts.append(x)
    ribcage(L, 1500, 712, 780, 430, seed + 3, fog_amount(0.2, 0.3, 670, 60, top=0.05), dark_k=0.72, ink_k=0.85, width=17)
    chains_between(L, seed + 5, [((380, 230), (900, 260)), ((2650, 200), (3250, 250)), ((3250, 250), (380 + WL, 230))], -10,
                   fog_amount(0.15, 0.1, 600, 60, top=0.05), dark_k=0.85, extra_hang=5)
    sk = Sk(WL + 600, H)
    ox_skull(sk, 2200 + 300, 714, 0.9, ink_k=0.85)
    arr = Y.wrap_core(sk.snap(), 300, WL)
    _fog(arr, 0, fog_amount(0.14, 0.25, 680, 40))
    L.over(arr)
    ash_ground(L, seed + 7, 712, fog_amount(0.12, 0.25, 700, 30), col=(30, 20, 24), top=(84, 66, 66), bumps=12, ember_n=40)
    return L


# ------------------------------------------------------------------ 6) yakın
def layer_near(seed=50):
    L = Layer(WL, H)
    rng = np.random.default_rng(seed)
    chains_between(L, seed + 5, [], -10, fog_amount(0.0, 0.0), dark_k=0.7, link=16, extra_hang=7)
    for x in (260, 1300, 2200, 3100):
        prism_cluster(L, int(x) + 3, x, 790, int(rng.integers(2, 4)), 220, rng.uniform(380, 640), 60, 92,
                      fog_amount(0.02, 0.15, 760, 40), dark_k=0.75, ink_w=2.4, detail=1.0, col=(40, 32, 38))
    ash_ground(L, seed + 7, 784, fog_amount(0.03, 0.15, 780, 30), col=(18, 12, 16), top=(70, 56, 58), bumps=22, ember_n=90)
    # kemik çıkıntıları
    sk = Sk(WL + 400, H)
    for _ in range(9):
        x = rng.uniform(0, WL) + 200
        p0 = (x, 800)
        p2 = (x + rng.uniform(-60, 60), 800 - rng.uniform(60, 150))
        Y.rib(sk, p0, ((p0[0] + p2[0]) / 2 + rng.uniform(-30, 30), (p0[1] + p2[1]) / 2), p2, rng.uniform(10, 18),
              col=tuple(np.array(BONE) * 0.7), shade=tuple(np.array(BONE_SH) * 0.7), hi=tuple(np.array(BONE_HI) * 0.7))
    L.over(Y.wrap_core(sk.snap(), 200, WL))
    return L


# ------------------------------------------------------------------ duman / ışıma
def layer_haze(seed=65):
    sm = Y.smoke_layer(WL, H, seed, [(560, 110, 0.75), (420, 80, 0.35)], (60, 22, 20), (110, 40, 26), under=(230, 100, 46),
                       alpha=0.5, sx=220, sy=40)
    L = Layer(WL, H)
    L.a = sm
    return L


def layer_fogband(seed=60):
    sm = Y.smoke_layer(WL, H, seed, [(690, 45, 0.9), (640, 30, 0.4), (760, 40, 0.4)], (90, 34, 26), (150, 60, 34),
                       under=(255, 130, 60), alpha=0.6, sx=140, sy=14)
    L = Layer(WL, H)
    L.a = sm
    return L


def layer_shafts(seed=70):
    """Toplamalı lav ışıması: ufuktan yükselen sıcak parıltı, ısı dalgası kıvrımları ve yükselen korlar."""
    W = 2880
    rng = np.random.default_rng(seed)
    ys = np.arange(H, dtype=np.float32)[:, None]
    xs = np.arange(W, dtype=np.float32)[None, :]
    glow = np.exp(-((ys - 660) / 160.0) ** 2) * (0.5 + 0.35 * noise(W, H, 0, seed, sx=200, sy=400))
    # yukarı kıvrılan ısı tülleri
    warp = noise(W, H, 0, seed + 1, sx=40, sy=60) * 30
    streak = noise(W, H, 0, seed + 2, sx=14, sy=50)
    heat = np.clip(streak, 0, 1) ** 3 * smoothstep(300, 600, ys + warp) * (1 - smoothstep(620, 720, ys)) * 0.12
    out = np.clip(glow * 0.55 + heat, 0, 1)
    bl = 200
    t = np.linspace(0, 1, bl)[None, :]
    out[:, :bl] = out[:, :bl] * t + out[:, -bl:] * (1 - t)
    out = out[:, :W - bl]
    W2 = out.shape[1]
    col = c01((255, 110, 40))
    rgb = col[None, None, :] * out[..., None]
    a = out.copy()
    sk = Sk(W2, H)
    for _ in range(220):
        x, y = rng.uniform(0, W2), rng.uniform(80, 820)
        r = rng.uniform(0.7, 2.2)
        c = (255, 190, 100) if rng.random() < 0.7 else (255, 120, 50)
        sk.c.drawCircle(x, y, r * 3, sk.paint(c, 0.15, r * 2))
        sk.path(ribbon([(x, y), (x + rng.uniform(-2, 2), y + r * 4)], [r * 1.4, 0.3]), c, 0.9)
    m = sk.snap()
    rgb = m[..., :3] + rgb * (1 - m[..., 3:4])
    a = m[..., 3] + a * (1 - m[..., 3])
    L = Layer(W2, H)
    L.a = np.concatenate([rgb, a[..., None]], -1).astype(np.float32)
    return L


# ------------------------------------------------------------------ boss arenası: Erlik Han'ın tahtı
def throne_erlik(L, cx, base_y, fog_amt, seed=9):
    """Kafatası basamaklı bazalt kürsü üstünde demir taht: dikenli yüksek arkalık, tepede dev öküz boynuzları,
    arkalığın ortasında tutulmuş kara güneş amblemi (kor halkalı), kafatası başlı kolçaklar, iki yanda lav
    mangalları, arkalığa tavandan inen zincirler ve kızıl sancaklar."""
    rng = np.random.default_rng(seed)
    pad = 500
    W = 1200
    sk = Sk(W + 2 * pad, H)
    x = W / 2 + pad
    iron, iron_d, iron_l = (52, 42, 48), (26, 20, 24), (150, 84, 64)
    # tavandan inen zincirler
    for sd in (-1, 1):
        for k in range(2):
            Y.chain(sk, (x + sd * (120 + k * 60), -10), (x + sd * (90 + k * 40), base_y - 470 + k * 30), 10, link=14,
                    col=(64, 54, 58), hi=IRON_HI, thick=3.4)
    # sancaklar
    for sd in (-1, 1):
        bx = x + sd * 190
        pole = poly_path([(bx - 3, base_y - 90), (bx + 3, base_y - 90), (bx + 3, base_y - 520), (bx - 3, base_y - 520)])
        sk.path(pole, iron)
        sk.path(pole, INK, 1.0, 0, 1.4)
        ban = smooth_path([(bx + sd * 4, base_y - 510), (bx + sd * 70, base_y - 505), (bx + sd * 66, base_y - 330),
                           (bx + sd * 52, base_y - 300), (bx + sd * 40, base_y - 340), (bx + sd * 26, base_y - 296), (bx + sd * 6, base_y - 330)], True, 0.25)
        sk.path(ban, (120, 22, 20))
        sk.path(smooth_path([(bx + sd * 6, base_y - 505), (bx + sd * 30, base_y - 505), (bx + sd * 24, base_y - 320), (bx + sd * 8, base_y - 330)], True, 0.3), (160, 40, 30), 0.7)
        sk.c.drawCircle(bx + sd * 36, base_y - 440, 18, sk.paint((14, 6, 8)))
        sk.c.drawCircle(bx + sd * 36, base_y - 440, 18, sk.paint((255, 170, 80), 0.9, 0, 2.0))
        sk.path(ban, INK, 1.0, 0, 1.6)
    # arkalık
    back = poly_path([(x - 150, base_y - 150), (x - 165, base_y - 430), (x - 120, base_y - 470), (x - 60, base_y - 520), (x, base_y - 540),
                      (x + 60, base_y - 520), (x + 120, base_y - 470), (x + 165, base_y - 430), (x + 150, base_y - 150)])
    sk.path(back, iron)
    sk.c.save()
    sk.c.clipPath(back, doAntiAlias=True)
    sk.path(poly_path([(x + 40, base_y - 560), (x + 200, base_y - 560), (x + 200, base_y - 100), (x + 60, base_y - 100)]), iron_d, 0.7)
    sk.path(poly_path([(x - 170, base_y - 560), (x - 120, base_y - 560), (x - 110, base_y - 100), (x - 170, base_y - 100)]), iron_l, 0.35)
    for yy in range(int(base_y - 520), int(base_y - 150), 46):   # yatay demir levha derzleri ve perçinler
        sk.path(ribbon([(x - 170, yy), (x + 170, yy + 2)], [2.0, 2.0]), INK, 0.7)
        for k in range(-3, 4):
            sk.c.drawCircle(x + k * 44, yy + 8, 2.4, sk.paint(iron_l, 0.8))
    sk.c.restore()
    sk.path(back, INK, 1.0, 0, 3.0)
    for sd in (-1, 1):   # kenar dikenleri
        for k in range(6):
            yy = base_y - 200 - k * 48
            xx = x + sd * (150 + k * 2.5)
            sk.path(poly_path([(xx, yy - 10), (xx + sd * 34, yy - 18), (xx, yy + 8)]), iron)
            sk.path(poly_path([(xx, yy - 10), (xx + sd * 34, yy - 18), (xx, yy + 8)]), INK, 1.0, 0, 1.2)
    # öküz boynuzları
    for sd in (-1, 1):
        horn = bezier((x + sd * 70, base_y - 520), (x + sd * 330, base_y - 560), (x + sd * 280, base_y - 760), 20)
        sk.path(ribbon(horn, np.linspace(60, 3, 20)), BONE)
        sk.path(ribbon(horn + np.array([sd * 8, 12]), np.linspace(30, 1, 20)), BONE_SH, 0.65)
        sk.path(ribbon(horn - np.array([sd * 6, 10]), np.linspace(14, 1, 20)), BONE_HI, 0.6)
        for j in range(2, 18, 2):
            q = horn[j]
            sk.path(ribbon([(q[0] - 14, q[1] + 6), (q[0] + 14, q[1] - 6)], [0.8, 0.8]), INK, 0.6)
        sk.path(ribbon(horn, np.linspace(60, 3, 20)), INK, 1.0, 0, 2.4)
    # kara güneş amblemi
    ey = base_y - 380
    sk.c.drawCircle(x, ey, 74, sk.paint((255, 120, 40), 0.35, 26))
    sk.c.drawCircle(x, ey, 58, sk.paint((255, 200, 120)))
    for k in range(16):
        a = k * math.pi / 8
        sk.path(poly_path([(x + math.cos(a - 0.08) * 56, ey + math.sin(a - 0.08) * 56), (x + math.cos(a) * 84, ey + math.sin(a) * 84),
                           (x + math.cos(a + 0.08) * 56, ey + math.sin(a + 0.08) * 56)]), (255, 150, 60), 0.9)
    sk.c.drawCircle(x, ey, 50, sk.paint((10, 4, 6)))
    sk.c.drawCircle(x, ey, 58, sk.paint(INK, 1.0, 0, 2.0))
    # oturak ve kafatası kolçaklar
    seat = poly_path([(x - 190, base_y - 150), (x + 190, base_y - 150), (x + 200, base_y - 110), (x - 200, base_y - 110)])
    sk.path(seat, iron)
    sk.path(poly_path([(x - 190, base_y - 150), (x + 190, base_y - 150), (x + 192, base_y - 142), (x - 192, base_y - 142)]), iron_l, 0.7)
    sk.path(seat, INK, 1.0, 0, 2.0)
    from tamu_ink_decor import skull as dskull
    for sd in (-1, 1):
        arm = poly_path([(x + sd * 160, base_y - 110), (x + sd * 160, base_y - 230), (x + sd * 215, base_y - 230), (x + sd * 215, base_y - 110)])
        sk.path(arm, iron)
        sk.path(arm, INK, 1.0, 0, 2.0)
        dskull(sk, sk, x + sd * 188, base_y - 250, 2.2, horns=True)
    # kafatası basamakları (bazalt)
    for i, (hw_, yy, hh) in enumerate([(380, base_y - 30, 32), (320, base_y - 60, 30), (260, base_y - 90, 28)]):
        p = poly_path([(x - hw_, yy + hh), (x - hw_, yy), (x + hw_, yy), (x + hw_, yy + hh)])
        sk.path(p, BASALT)
        sk.path(poly_path([(x - hw_, yy), (x + hw_, yy), (x + hw_, yy + 5), (x - hw_, yy + 5)]), BASALT_LIT, 0.55)
        sk.path(p, INK, 1.0, 0, 2.2)
        for k in range(int(hw_ / 40)):
            dskull(sk, None, x - hw_ + 30 + k * 80, yy + hh * 0.55, 0.9)
    # lav mangalları
    for sd in (-1, 1):
        bx = x + sd * 330
        for lg in (-1, 0, 1):
            leg = ribbon([(bx + lg * 14, base_y - 100), (bx + lg * 30, base_y - 30), (bx + lg * 36, base_y)], [6, 5, 4])
            sk.path(leg, iron)
            sk.path(leg, INK, 1.0, 0, 1.4)
        bowl = smooth_path([(bx - 50, base_y - 130), (bx + 50, base_y - 130), (bx + 36, base_y - 92), (bx - 36, base_y - 92)], True, 0.3)
        sk.path(bowl, iron)
        sk.path(bowl, INK, 1.0, 0, 2.0)
        fl = smooth_path([(bx - 44, base_y - 128), (bx - 30, base_y - 190), (bx - 10, base_y - 250), (bx + 4, base_y - 200), (bx + 16, base_y - 270),
                          (bx + 30, base_y - 190), (bx + 44, base_y - 128)], True, 0.45)
        sk.path(fl, (255, 110, 30), 0.95, 3)
        sk.path(smooth_path([(bx - 24, base_y - 128), (bx - 8, base_y - 200), (bx + 10, base_y - 170), (bx + 24, base_y - 128)], True, 0.45), (255, 200, 110), 1.0, 1.5)
        sk.c.drawCircle(bx, base_y - 170, 90, sk.paint((255, 120, 40), 0.18, 40))
    arr = sk.snap()
    _fog(arr, 0, fog_amt)
    Y.place_arr(L, arr, ik.P(cx - W / 2 - pad), 0)


IRON_HI = (170, 110, 90)


def layer_mid_boss(seed=40):
    L = Layer(WL, H)
    rng = np.random.default_rng(seed)
    fogm = fog_amount(0.16, 0.34, 660, 70, top=0.06)
    for x in (500, 2600, 3300):
        prism_cluster(L, int(x), x, 708, int(rng.integers(2, 4)), 300, 520, 36, 54, fogm, dark_k=0.85, ink_w=1.4, detail=0.7)
    chains_between(L, seed + 5, [((2600, 200), (3300, 250))], -10, fog_amount(0.15, 0.1, 600, 60, top=0.05), dark_k=0.85, extra_hang=3)
    throne_erlik(L, 1480, 712, fog_amount(0.1, 0.25, 670, 50, top=0.04))
    ash_ground(L, seed + 7, 712, fog_amount(0.12, 0.25, 700, 30), col=(30, 20, 24), top=(84, 66, 66), bumps=12, ember_n=40)
    return L


EXPORT_BG = [('0_sky', 'layer_sky'), ('1_far', 'layer_far'), ('2_farmid', 'layer_farmid'), ('2b_haze', 'layer_haze'),
             ('3_mid', 'layer_mid'), ('4_fog', 'layer_fogband'), ('5_shafts', 'layer_shafts'), ('6_near', 'layer_near'),
             ('3_mid_boss', 'layer_mid_boss')]
