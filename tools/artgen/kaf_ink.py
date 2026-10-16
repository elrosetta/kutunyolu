"""Kaf Dağı, stil v2 "mürekkep" ortamı: dünyanın kıyısındaki kutsal karlı dağ.

Gece-şafak arası soğuk mavi-mor gök, yıldızlar, gökte dalgalanan kutup ışıkları (yeşil-turkuaz perdeler, mor saçaklı);
uzakta göğe yükselen Kaf Dağı: zümrüt zirvesi (efsanede göğün mavisi Kaf'ın zümrüdünden yansır) ilk ışıkla pembe-altın
yanar, çevresinde Zümrüdüanka süzülür. Ortada karlı ladin ormanları, donmuş çağlayanlı kayalıklar, buz kristali
kümeleri, donmuş çaputlu kam direği; önde karla yüklü koyu ladinler, buz sivrileri. Hava: tipi tülleri, düşen kar
(yakın / uzak), yer pusu. Sıcak vurgular: zirvedeki şafak, kam ateşleri, çaputlar. Işık soldan (ay / tan).

Çıktılar (export_ink_biyom.py kaf): assets/bg/kaf_v2_*.png. Tümü yordamsal.
"""
import math

import numpy as np
from scipy import ndimage

import inkkit_ortam as ik
from inkkit_ortam import (INK, Layer, Sk, apply_fog, bezier, blade, blob, c01, fbm, mix, noise, poly_path, premul,
                          ribbon, smooth_path, smoothstep, trunk)
from ink_biyom import (H, WL, cloud_masses, fold, fog_amount, hills, over, peak, place, ramp, range_layer, rays,
                       snowfall, veil)

LIGHT = -1.0          # ay / tan ışığı soldan

SKY_STOPS = [
    (0, (12, 14, 38)),
    (200, (22, 28, 66)),
    (380, (44, 50, 104)),
    (500, (82, 82, 142)),
    (575, (134, 118, 172)),
    (625, (186, 160, 196)),
    (665, (150, 146, 192)),
    (740, (100, 106, 160)),
    (860, (62, 70, 120)),
    (1080, (30, 34, 68)),
]
SKY = ramp(SKY_STOPS)
MINT = (200, 236, 250)
SNOW_LIT = (236, 244, 255)
SNOW_MID = (176, 194, 230)
SNOW_SH = (104, 118, 176)
ROCK = (70, 74, 112)
ROCK_D = (40, 40, 72)
NEEDLE = (30, 52, 66)
NEEDLE_D = (18, 28, 44)
ICE = (150, 220, 240)
ICE_D = (70, 140, 190)
EMERALD = (80, 230, 170)


# ------------------------------------------------------------------ 0) gök
def layer_sky(seed=1):
    W = 1920
    L = Layer(W, H)
    rgb = np.repeat(SKY[:, None, :], W, 1).copy()
    ys = np.arange(H, dtype=np.float32)[:, None]
    xs = np.arange(W, dtype=np.float32)[None, :]
    # ufukta şafak sızısı (sağda, sıcak pembe) + solda ay hâlesi
    d = np.hypot((xs - 1500) / 900.0, (ys - 640) / 220.0)
    rgb = mix(rgb, c01((236, 170, 186))[None, None, :], (np.exp(-d * d * 2.2) * 0.5)[..., None])
    d2 = np.hypot((xs - 360) / 300.0, (ys - 170) / 300.0)
    rgb = mix(rgb, c01((150, 170, 230))[None, None, :], (np.exp(-d2 * d2 * 2.5) * 0.35)[..., None])
    n1 = fbm(W, H, [110, 40, 14], seed)
    n2 = noise(W, H, 0, seed + 7, sx=90, sy=2.5)
    rgb *= (1 + 0.04 * n1[..., None] + 0.025 * n2[..., None])
    L.a = premul(rgb.astype(np.float32), np.ones((H, W), np.float32))
    s = Sk(W, H)
    rng = np.random.default_rng(seed + 3)
    for _ in range(700):
        x, y = rng.uniform(0, W), rng.uniform(0, 560) ** 1.0
        r = rng.uniform(0.5, 1.4) if rng.random() < 0.93 else rng.uniform(1.6, 2.4)
        a = rng.uniform(0.3, 0.95) * (1 - y / 700)
        s.c.drawCircle(x, y, r, s.paint((230, 236, 255), a))
        if r > 1.6:
            for ang in (0, math.pi / 2):
                ln = r * 4
                s.path(ribbon([(x - math.cos(ang) * ln, y - math.sin(ang) * ln), (x, y), (x + math.cos(ang) * ln, y + math.sin(ang) * ln)],
                              [0.1, 0.9, 0.1]), (230, 236, 255), a * 0.7)
    # hilal ay
    mx, my = 360, 170
    s.c.drawCircle(mx, my, 54, s.paint((220, 230, 255), 0.25, 18))
    s.c.drawCircle(mx, my, 40, s.paint((240, 244, 255), 1.0, 0.8))
    s.c.drawCircle(mx + 14, my - 8, 36, s.paint((0, 0, 0), 1.0, 0.8, 0.0, __import__('skia').BlendMode.kDstOut))
    L.over(s.snap())
    cloud_masses(L, SKY, seed + 5, [(1100, 560, 560, 40), (1700, 520, 380, 30), (300, 600, 460, 26)],
                 (40, 44, 90), (74, 74, 126), (196, 150, 190), (255, 210, 210), sun=(0.6, 0.8), alpha=0.85, wrap=False)
    return L


def layer_aurora(seed=5):
    """Kutup ışığı perdeleri (toplamalı, yavaş nefes alır): dalgalı alt kenarı parlak yeşil-turkuaz, yukarı doğru
    sönen dikey ışınlar, üst saçakta mor."""
    W = WL
    ys = np.arange(H, dtype=np.float32)[:, None]
    xs = np.arange(W, dtype=np.float32)
    out = np.zeros((H, W, 3), np.float32)
    rng = np.random.default_rng(seed)
    for k in range(3):
        f1 = round(rng.uniform(1.5, 3.5)) * 2 * math.pi / W
        f2 = round(rng.uniform(5, 9)) * 2 * math.pi / W
        base = 190 + k * 60 + 60 * np.sin(xs * f1 + rng.uniform(0, 6)) + 22 * np.sin(xs * f2 + rng.uniform(0, 6))
        amp = np.clip(0.1 + 1.1 * noise(W, 1, 0, seed + k, sx=170, sy=1)[0], 0, 1) ** 1.4 * (1.0 - 0.25 * k)
        streak = np.clip(0.5 + 0.45 * noise(W, 1, 0, seed + 10 + k, sx=3.0, sy=1)[0]
                         + 0.35 * noise(W, 1, 0, seed + 30 + k, sx=14, sy=1)[0], 0.05, 1.2)
        hgt = 85 + 45 * noise(W, 1, 0, seed + 20 + k, sx=90, sy=1)[0]
        dy = base[None, :] - ys                                    # perde tabanından yukarı
        low = np.exp(-np.clip(-dy, 0, None) / 10.0)                 # tabanın altında hızla söner
        up = np.exp(-np.clip(dy, 0, None) / hgt[None, :]) * low
        g = up * amp[None, :] * streak[None, :]
        t = np.clip(dy / hgt[None, :], 0, 1.5)
        col = mix(c01((90, 255, 190))[None, None, :], c01((60, 200, 230))[None, None, :], smoothstep(0.1, 0.6, t)[..., None])
        col = mix(col, c01((200, 110, 255))[None, None, :], smoothstep(0.6, 1.2, t)[..., None])
        out += col * (g * 0.4 * (1 - smoothstep(330, 470, ys)))[..., None]
    out = np.clip(out, 0, 1)
    a = np.clip(out.max(-1), 0, 1)
    L = Layer(W, H)
    L.a = np.concatenate([out, a[..., None]], -1).astype(np.float32)
    return L


# ------------------------------------------------------------------ öğeler
def spruce(sk, x, base_y, h, seed, needle=NEEDLE, needle_d=NEEDLE_D, snow=SNOW_LIT, snow_sh=SNOW_SH, ink_a=1.0,
           ink_w=1.4, light=LIGHT, tiers=None, snow_amt=1.0, trunk_col=(52, 40, 46), hatch=True, width_k=1.0):
    """Karla yüklü ladin: tek parça siluet (her katta aşağı sarkan dal uçları, aralarında içe giren çentik), gölge yarısı
    koyu, dal altlarında iğne taraması; dalların üstünde düzensiz kar yükleri (ışık tarafı parlak, öbürü mavi gölge),
    değişken kalınlıkta mürekkep kontur."""
    rng = np.random.default_rng(seed)
    w = h * rng.uniform(0.36, 0.46) * width_k
    n = tiers or max(4, int(h / 34) + int(rng.integers(0, 2)))
    top = base_y - h
    tw = max(1.5, h * 0.022)
    sk.path(poly_path([(x - tw, base_y), (x + tw, base_y), (x + tw * 0.4, top + h * 0.3), (x - tw * 0.4, top + h * 0.3)]), trunk_col)
    # katlar: dal ucu yüksekliği ve uzunluğu (tepeden tabana büyür)
    ts = np.sort(rng.uniform(0, 1, n - 1)) * 0.75 + np.linspace(0, 0.2, n - 1)
    ts = np.concatenate([[0.06], np.clip(ts, 0.08, 0.98)])
    ts = np.unique(np.round(ts, 3))
    ts[-1] = max(ts[-1], 0.9)
    sides = {}
    for sgn in (-1, 1):
        pts = []
        for i, t in enumerate(ts):
            half = w * 0.5 * (0.12 + 0.88 * t ** 0.9) * rng.uniform(0.82, 1.12)
            y_att = top + h * t * 0.9
            y_tip = y_att + h * rng.uniform(0.06, 0.11) + half * 0.15
            notch_y = y_tip - h * rng.uniform(0.02, 0.05)
            notch_x = half * rng.uniform(0.35, 0.6)
            if i > 0:
                pts.append((x + sgn * notch_x, notch_y - h * 0.04))
            # dalın üst kenarı: gövdeden uca sarkan eğri
            for s_ in (0.55, 0.85):
                pts.append((x + sgn * half * s_, y_att + (y_tip - y_att) * s_ ** 1.6))
            pts.append((x + sgn * half, y_tip))
            # uçtan geri: tırtıklı alt kenar
            for k in range(1, 4):
                pts.append((x + sgn * half * (1 - k * 0.12), y_tip - (k % 2) * rng.uniform(2, 5) * h / 300 - 0.5))
        sides[sgn] = pts
    right = sides[1]
    left = sides[-1][::-1]
    sil = [(x, top - h * 0.03)] + right + [(x + tw, base_y - 2), (x - tw, base_y - 2)] + left
    path = poly_path(sil)
    sk.path(path, needle)
    shp = [(x, top - h * 0.03)] + sides[1 if light < 0 else -1] + [(x, base_y - 2)]
    sk.path(poly_path(shp), needle_d, 0.8)
    if hatch and h > 60:
        for _ in range(int(h * 0.5)):
            t = rng.uniform(0.1, 0.95)
            sgn = 1 if rng.random() < 0.5 else -1
            half = w * 0.5 * (0.12 + 0.88 * t)
            xx = x + sgn * rng.uniform(0.1, 0.85) * half
            yy = top + h * t * 0.9 + rng.uniform(0, h * 0.06)
            ln = rng.uniform(3, 8) * h / 300 + 1.5
            sk.path(ribbon([(xx, yy), (xx + sgn * ln * 0.3, yy + ln)], [0.9, 0.2]), INK, ink_a * rng.uniform(0.3, 0.6))
    if ink_a > 0:
        sk.path(path, INK, ink_a, 0, ink_w)
    # kar yükleri
    if snow_amt > 0:
        for i, t in enumerate(ts):
            for sgn in (-1, 1):
                if rng.random() > 0.85 * snow_amt + 0.1:
                    continue
                half = w * 0.5 * (0.12 + 0.88 * t ** 0.9)
                y_att = top + h * t * 0.9
                y_tip = y_att + h * 0.08 + half * 0.15
                s0, s1 = rng.uniform(0.05, 0.3), rng.uniform(0.6, 0.95)
                ss = np.linspace(s0, s1, 7)
                bx = x + sgn * half * ss
                by = y_att + (y_tip - y_att) * ss ** 1.6 - 0.5
                th = (h * 0.022 + 1.4) * snow_amt * rng.uniform(0.7, 1.3)
                up = [(px_, py_ - th * math.sin(math.pi * (k_ / 6)) ** 0.6 - 0.3) for k_, (px_, py_) in enumerate(zip(bx, by))]
                lo = [(px_, py_ + th * 0.35) for px_, py_ in zip(bx[::-1], by[::-1])]
                sp = smooth_path(up + lo, True, 0.4)
                lit = sgn * light < 0
                sk.path(sp, snow if lit else snow_sh)
                if lit:
                    sk.path(smooth_path(up[1:-1] + [(q[0], q[1] + th * 0.4) for q in up[-2:0:-1]], True, 0.4), (255, 255, 255), 0.6)
                if ink_a > 0:
                    sk.path(smooth_path(lo, False, 0.4), INK, ink_a * 0.6, 0, ink_w * 0.6)
    sk.path(blob(x, top - h * 0.01, 2.5 + h * 0.012, 2.0 + h * 0.01, seed, n=8), snow)


def ice_crystal(sk, x, base_y, h, w, ang, seed, light=LIGHT, ink_a=1.0, ink_w=1.4, col=ICE, col_d=ICE_D, hi=(240, 252, 255)):
    """Altıgen buz kristali: sivri uçlu prizma, ışık yüzü açık, gölge yüzü koyu, iç kırılma çizgileri, kenarda beyaz parlama."""
    rng = np.random.default_rng(seed)
    ca, sa = math.cos(ang), math.sin(ang)

    def T(u, v):          # u: eksen boyunca (0 taban, 1 uç), v: genişlik (-1..1)
        px_ = u * h
        py_ = v * w * 0.5
        return (x + px_ * sa + py_ * ca, base_y - px_ * ca + py_ * sa)
    tipu = 1.0
    body = [T(0, -1), T(0.78, -1), T(tipu, 0.0), T(0.78, 1), T(0, 1)]
    left = [T(0, -1), T(0.78, -1), T(tipu, 0), T(0.82, -0.15), T(0, -0.25)]
    right = [T(0, 0.35), T(0.8, 0.3), T(tipu, 0), T(0.78, 1), T(0, 1)]
    sk.path(poly_path(body), col)
    lit_face, sh_face = (left, right) if light < 0 else (right, left)
    sk.path(poly_path(lit_face), tuple(np.minimum(np.array(col) * 1.25 + 20, 255)), 0.9)
    sk.path(poly_path(sh_face), col_d, 0.85)
    # iç kırılma çizgileri ve parlama
    for _ in range(int(rng.integers(2, 4))):
        u0 = rng.uniform(0.1, 0.6)
        sk.path(ribbon([T(u0, rng.uniform(-0.6, 0.6)), T(u0 + rng.uniform(0.1, 0.3), rng.uniform(-0.6, 0.6))], [0.6, 0.2]), hi, 0.6)
    sk.path(ribbon([T(0.08, -0.82 * -light), T(0.76, -0.86 * -light), T(0.97, -0.05 * -light)], [0.5, 1.6, 0.4]), hi, 0.9)
    if ink_a > 0:
        sk.path(poly_path(body), INK, ink_a, 0, ink_w)
        sk.path(ribbon([T(0.02, 0.0), T(0.8, 0.05)], [0.8, 0.3]), INK, ink_a * 0.5)


def crystal_cluster(sk, x, base_y, s, seed, **kw):
    rng = np.random.default_rng(seed)
    n = int(rng.integers(4, 8))
    items = []
    for k in range(n):
        ang = rng.uniform(-0.75, 0.75)
        h = s * rng.uniform(0.45, 1.0) * (1.0 if abs(ang) < 0.3 else 0.75)
        items.append((abs(ang), x + rng.uniform(-s * 0.18, s * 0.18), h, h * rng.uniform(0.2, 0.3), ang, int(rng.integers(1 << 20))))
    for _, xx, h, w, ang, sd in sorted(items, key=lambda q: -q[0]):
        ice_crystal(sk, xx, base_y, h, w, ang, sd, **kw)


def frozen_fall(L, x, top_y, base_y, w, seed, rock=ROCK, rock_d=ROCK_D, sky=None, fog=None, ink_a=1.0, ink_w=2.0, light=LIGHT,
                cliff=True):
    """Donmuş çağlayan: kayalık uçurum yüzünde aşağı akarken donmuş buz sütunları (mum akıntısı gibi yuvarlak), yarı saydam
    mavi-beyaz, çekirdekte turkuaz; üst dudakta buz saçakları, dipte buz yığını. Kayalık yanlarda karlı."""
    rng = np.random.default_rng(seed)
    pad = 60
    Wd = w * 2.2 + 2 * pad
    sk = Sk(Wd, base_y - top_y + 2 * pad)
    ox, oy = Wd / 2, pad
    hh = base_y - top_y
    # uçurum kayası (iki yan basamaklı), karlı üst kenar
    cliff = [(ox - w * 1.05, oy + hh + 10)]
    for k, s_ in enumerate(np.linspace(-1.05, 1.05, 13)):
        yy = oy + rng.uniform(-6, 10) + (abs(s_) ** 3) * hh * 0.2
        cliff.append((ox + s_ * w, yy))
    cliff.append((ox + w * 1.05, oy + hh + 10))
    cp = poly_path(cliff)
    draw_cliff = cliff
    if not draw_cliff:
        # yalnızca kaya yüzündeki oyuk: buzun arkasında koyu kanal
        ch = smooth_path([(ox - w * 0.48, oy + 8), (ox - w * 0.52, oy + hh * 0.5), (ox - w * 0.58, oy + hh + 4), (ox + w * 0.58, oy + hh + 4),
                          (ox + w * 0.52, oy + hh * 0.5), (ox + w * 0.48, oy + 8), (ox, oy + 2)], True, 0.5)
        sk.path(ch, rock_d, 0.6, 6)
    else:
        sk.path(cp, rock)
    # kaya yüzeyi: dikey kırık yüzler
    for _ in range(int(w / 6) if draw_cliff else 0):
        xx = ox + rng.uniform(-w, w)
        yy = oy + rng.uniform(10, hh)
        ln = rng.uniform(20, 60)
        lit = (xx - ox) * light > 0
        sk.path(poly_path([(xx, yy), (xx + rng.uniform(6, 16), yy + ln * 0.2), (xx + rng.uniform(2, 8), yy + ln), (xx - 3, yy + ln * 0.8)]),
                tuple(np.array(rock) * (1.25 if lit else 0.7)), 0.8)
        sk.path(ribbon([(xx, yy), (xx + 2, yy + ln)], [1.2, 0.3]), INK, ink_a * 0.6)
    # kar başlığı
    if draw_cliff:
        capt = [(p[0], p[1] - rng.uniform(4, 9)) for p in cliff[1:-1]]
        capb = [(p[0], p[1] + rng.uniform(4, 10)) for p in cliff[1:-1]][::-1]
        sk.path(smooth_path(capt + capb, True, 0.35), SNOW_SH)
        sk.path(smooth_path(capt + [(p[0], p[1] + 3) for p in capt[::-1]], True, 0.35), SNOW_LIT)
        if ink_a > 0:
            sk.path(cp, INK, ink_a, 0, ink_w)
    # buz sütunları
    cols = int(w / 9)
    for k in range(cols):
        xx = ox + (k / (cols - 1) - 0.5) * w * 0.85 + rng.uniform(-3, 3)
        y0 = oy + rng.uniform(0, 12)
        y1 = oy + hh - rng.uniform(0, 20) * (abs(xx - ox) / w)
        wd = rng.uniform(6, 16) * (1.2 - abs(xx - ox) / w * 0.6)
        n = 14
        yy = np.linspace(y0, y1, n)
        xs_ = xx + np.sin(np.linspace(0, rng.uniform(2, 5), n)) * rng.uniform(1, 4)
        ws = wd * (0.7 + 0.5 * np.abs(np.sin(np.linspace(0, rng.uniform(3, 7), n) + k)))
        pts = np.stack([xs_, yy], 1)
        base_c = np.array(ICE) * rng.uniform(0.75, 1.05)
        sk.path(ribbon(pts, ws), tuple(base_c), 0.92)
        sk.path(ribbon(pts + [-light * -ws[:, None].mean() * 0.25, 0], ws * 0.35), tuple(np.minimum(base_c * 1.35 + 30, 255)), 0.7)
        sk.path(ribbon(pts + [light * -ws.mean() * 0.25, 0], ws * 0.3), ICE_D, 0.6)
        if rng.random() < 0.5 and ink_a > 0:
            sk.path(ribbon(pts, ws), INK, ink_a * 0.5, 0, ink_w * 0.5)
    # üst dudakta saçaklar
    for k in range(int(w / 5)):
        xx = ox + rng.uniform(-w * 0.95, w * 0.95)
        if not draw_cliff and abs(xx - ox) > w * 0.55:
            continue
        yy = oy + rng.uniform(4, 12) + (abs((xx - ox) / w) ** 3) * hh * 0.2
        ln = rng.uniform(8, 30)
        p = poly_path([(xx - 2.5, yy), (xx + 2.5, yy), (xx, yy + ln)])
        sk.path(p, (210, 240, 252))
        if ink_a > 0:
            sk.path(p, INK, ink_a * 0.7, 0, 0.8)
    # dipte buz yığını
    heap = smooth_path([(ox - w * 0.6, oy + hh + 8), (ox - w * 0.45, oy + hh - 12), (ox - w * 0.1, oy + hh - 20),
                        (ox + w * 0.3, oy + hh - 14), (ox + w * 0.6, oy + hh + 8)], True, 0.4)
    sk.path(heap, (200, 228, 246))
    sk.path(smooth_path([(ox - w * 0.45, oy + hh - 8), (ox - w * 0.1, oy + hh - 18), (ox + w * 0.25, oy + hh - 12), (ox, oy + hh - 6)], True, 0.4), SNOW_LIT, 0.8)
    if ink_a > 0:
        sk.path(heap, INK, ink_a, 0, ink_w * 0.8)
    arr = sk.snap()
    yt = top_y - pad
    if fog is not None:
        apply_fog(arr, int(yt * ik.K), sky if sky is not None else SKY, fog)
    L.over_wrap(arr, int(x - Wd / 2), int(yt))


def anka(sk, x, y, s, col, wing=0.0, ink_a=0.0):
    """Zümrüdüanka siluet: geniş kanatlar, uzun dalgalanan kuyruk tüyleri, tepeli baş."""
    body = smooth_path([(x - s * 0.5, y), (x, y - s * 0.12), (x + s * 0.55, y - s * 0.05), (x + s * 0.75, y - s * 0.18),
                        (x + s * 0.68, y + s * 0.02), (x + s * 0.2, y + s * 0.12), (x - s * 0.5, y + s * 0.08)], True, 0.4)
    sk.path(body, col)
    for sgn in (-1, 1):
        tip = (x + s * 0.1 + sgn * 0.0, y - s * (0.9 + wing) * (1 if sgn < 0 else 0.55))
        wingp = smooth_path([(x - s * 0.15, y - s * 0.05), (x - s * 0.45, tip[1] + s * 0.25), (tip[0] - s * 0.3, tip[1]),
                             (tip[0] + s * 0.25, tip[1] + s * 0.1), (x + s * 0.3, y - s * 0.05)], True, 0.35)
        sk.path(wingp, col, 0.9 if sgn < 0 else 0.6)
    for k in range(5):
        q = bezier((x - s * 0.45, y + s * 0.02), (x - s * (1.0 + k * 0.08), y + s * (0.25 + k * 0.05)),
                   (x - s * (1.6 + k * 0.15), y + s * (0.05 + k * 0.12)), 12)
        sk.path(ribbon(q, np.linspace(s * 0.06, s * 0.015, 12)), col, 0.85)
        sk.c.drawCircle(q[-1][0], q[-1][1], s * 0.035, sk.paint(col, 0.85))
    sk.path(ribbon([(x + s * 0.7, y - s * 0.17), (x + s * 0.62, y - s * 0.32), (x + s * 0.8, y - s * 0.28)], [s * 0.02, s * 0.03, s * 0.01]), col)


def shaman_pole(sk, x, base_y, h, seed, ink_a=1.0, light=LIGHT):
    """Karlı kam direği: oymalı direk, tepede kartal, donmuş (sert) çaputlar, buz saçağı."""
    rng = np.random.default_rng(seed)
    s = h / 200.0
    wd = 7 * s
    post = poly_path([(x - wd, base_y), (x + wd, base_y), (x + wd * 0.8, base_y - h * 0.78), (x - wd * 0.8, base_y - h * 0.78)])
    sk.path(post, (82, 64, 66))
    sk.path(poly_path([(x - wd * light * -1, base_y), (x - wd * 0.2 * light * -1, base_y), (x, base_y - h * 0.78), (x - wd * 0.8 * light * -1, base_y - h * 0.78)]), (124, 104, 106), 0.7)
    for k in range(4):
        y = base_y - h * (0.2 + 0.14 * k)
        r = poly_path([(x - wd * 1.15, y), (x + wd * 1.15, y), (x + wd * 1.15, y + 5 * s), (x - wd * 1.15, y + 5 * s)])
        sk.path(r, (60, 46, 50))
        sk.path(ribbon([(x - wd * 1.2, y - 1), (x + wd * 1.2, y - 1)], [2.4 * s, 2.4 * s]), SNOW_LIT, 0.9)
        if ink_a > 0:
            sk.path(r, INK, ink_a, 0, 1.2)
    if ink_a > 0:
        sk.path(post, INK, ink_a, 0, 1.8)
    ty = base_y - h * 0.8
    for sgn in (-1, 1):
        wing = smooth_path([(x, ty), (x + sgn * 30 * s, ty - 16 * s), (x + sgn * 48 * s, ty - 28 * s), (x + sgn * 44 * s, ty - 14 * s),
                            (x + sgn * 34 * s, ty - 6 * s), (x + sgn * 18 * s, ty + 4 * s)], True, 0.35)
        sk.path(wing, (96, 76, 72))
        sk.path(smooth_path([(x + sgn * 8 * s, ty - 6 * s), (x + sgn * 30 * s, ty - 18 * s), (x + sgn * 46 * s, ty - 29 * s),
                             (x + sgn * 32 * s, ty - 15 * s)], True, 0.35), SNOW_LIT, 0.95)
        if ink_a > 0:
            sk.path(wing, INK, ink_a, 0, 1.5)
    head = smooth_path([(x - 5 * s, ty + 2 * s), (x - 1 * s, ty - 16 * s), (x + 8 * s, ty - 14 * s), (x + 12 * s, ty - 9 * s), (x + 5 * s, ty - 6 * s), (x + 4 * s, ty + 3 * s)], True, 0.4)
    sk.path(head, (120, 98, 92))
    if ink_a > 0:
        sk.path(head, INK, ink_a, 0, 1.4)
    sk.c.drawCircle(x + 4 * s, ty - 12 * s, 1.3 * s, sk.paint(INK))
    cols = [(176, 52, 46), (230, 222, 206), (70, 110, 180), (214, 168, 70)]
    for k in range(6):
        y0 = ty + 10 * s + k * 5 * s
        side = -1 if k % 2 == 0 else 1
        q = bezier((x + side * wd, y0), (x + side * 14 * s, y0 + 14 * s), (x + side * rng.uniform(14, 22) * s, y0 + rng.uniform(34, 52) * s), 8)
        sk.path(ribbon(q, np.linspace(4.5 * s, 3.2 * s, 8)), cols[k % 4])
        sk.path(ribbon(q[:3], [2.5 * s] * 3), SNOW_LIT, 0.8)
        if ink_a > 0:
            sk.path(ribbon(q, np.linspace(4.5 * s, 3.2 * s, 8)), INK, ink_a * 0.9, 0, 0.9)
        for j in range(2):
            ex, ey = q[-1]
            sk.path(poly_path([(ex - 1.2, ey), (ex + 1.2, ey), (ex, ey + rng.uniform(5, 10) * s)]), (210, 240, 252), 0.9)


def snow_ground(L, sky, seed, y0, amp, fog, ink_a=0.8, lit=SNOW_LIT, mid=SNOW_MID, sh=SNOW_SH, light=LIGHT, ink_w=2.0):
    """Karlı zemin bandı: yumuşak dalgalı kar tümsekleri (ışık tarafı parlak, çukurlar mavi), rüzgâr izi çizgileri."""
    top, xs = hills(L, sky, seed, y0, amp, 4, lit, sh, fog, light=light, ink_a=ink_a, ink_w=ink_w, tex=0.03,
                    rim=(255, 255, 255))
    return top, xs


# ------------------------------------------------------------------ paralaks katmanları
def layer_far(seed=20):
    """Kaf Dağı: göğe yükselen zümrüt zirveli devasa dağ + uzak sıradağlar; zirvede şafak pembesi, çevresinde Anka."""
    L = Layer(WL, H)
    rng = np.random.default_rng(seed)
    peaks = []
    x = 0.0
    while x < WL:
        x += rng.uniform(240, 460)
        if 1500 < x < 2300:
            continue
        peaks.append((x, rng.uniform(430, 540), 650, rng.uniform(200, 380), rng.uniform(200, 380)))
    n = len(peaks)
    range_layer(L, SKY, peaks, lambda i: fog_amount(0.62, 0.3, 640, 50), seed + 1,
                rock_lit=(110, 112, 170), rock_sh=(70, 70, 130), snow_lit=(214, 220, 250), snow_sh=(132, 140, 196),
                snow_line=0.55, ink_a=0.0, n_ridges=7, hatch=0.0, light=LIGHT, rough=0.3, crease=0.4,
                sil_rim=(236, 220, 250), sil_rim_w=1.6, gully_snow=0.4)
    # Kaf: dev zirve (omuzlarıyla)
    kx = 1900
    kaf = [(kx - 420, 300, 660, 520, 380), (kx + 380, 330, 660, 420, 560), (kx, 110, 660, 560, 600)]
    range_layer(L, SKY, kaf, lambda i: fog_amount(0.42 - 0.08 * i, 0.32, 640, 60, top=0.0), seed + 7,
                rock_lit=(108, 116, 176), rock_sh=(58, 62, 118), snow_lit=(255, 222, 232), snow_sh=(150, 156, 214),
                snow_line=0.62, ink_a=0.35, ink_w=1.6, n_ridges=11, hatch=0.25, light=LIGHT, rough=0.24, crease=0.55,
                sil_rim=(255, 214, 220), sil_rim_w=2.2, gully_snow=0.2, streak=0.04)
    # zümrüt zirve ışıltısı + Anka
    s = Sk(WL, H)
    s.c.drawCircle(kx, 150, 120, s.paint(EMERALD, 0.16, 50))
    s.path(smooth_path([(kx - 16, 150), (kx - 4, 112), (kx + 10, 128), (kx + 22, 160), (kx, 175)], True, 0.4), EMERALD, 0.55, 3)
    s.path(ribbon([(kx - 6, 120), (kx + 2, 150)], [1.4, 0.4]), (220, 255, 236), 0.8)
    anka(s, kx + 260, 230, 52, (40, 44, 86), wing=0.15)
    anka(s, 640, 330, 22, (60, 64, 110), wing=-0.2)
    L.over(s.snap())
    hills(L, SKY, seed + 2, 662, 22, 4, (170, 176, 220), (120, 124, 180), fog_amount(0.55, 0.2, 650, 30), light=LIGHT)
    return L


def layer_farmid(seed=30):
    """Uzak-orta sırtlar: yamaçlarda karlı ladin ormanı siluetleri, uzakta donmuş çağlayan, yer pusu."""
    L = Layer(WL, H)
    rng = np.random.default_rng(seed)
    peaks = []
    x = 0.0
    while x < WL:
        x += rng.uniform(300, 560)
        peaks.append((x, rng.uniform(470, 560), 690, rng.uniform(260, 420), rng.uniform(260, 420)))
    range_layer(L, SKY, peaks, lambda i: fog_amount(0.36, 0.3, 680, 50), seed + 1,
                rock_lit=(96, 100, 156), rock_sh=(54, 56, 104), snow_lit=(220, 226, 252), snow_sh=(130, 138, 196),
                snow_line=0.7, ink_a=0.35, ink_w=1.4, n_ridges=6, hatch=0.2, light=LIGHT, rough=0.22,
                sil_rim=(220, 226, 255), sil_rim_w=1.4, gully_snow=0.3)
    frozen_fall(L, peaks[3][0] + 30, peaks[3][1] + 60, 690, 50, seed + 5, rock_d=(50, 54, 96), sky=SKY,
                fog=fog_amount(0.36, 0.25, 680, 50), ink_a=0.4, ink_w=1.4, cliff=False)
    top, xs = hills(L, SKY, seed + 2, 700, 40, 4, (196, 206, 246), (116, 124, 186), fog_amount(0.32, 0.25, 690, 40),
                    light=LIGHT, ink_a=0.3, ink_w=1.2, tex=0.03, rim=(240, 246, 255))
    pad = 200
    sk = Sk(WL + 2 * pad, H)
    ty = lambda x: float(np.interp(x % WL, xs, top))
    for _ in range(120):
        x = rng.uniform(0, WL)
        if rng.random() < 0.5:
            x = (rng.choice([300, 1200, 2100, 3300]) + rng.normal(0, 160)) % WL
        h = rng.uniform(30, 70)
        spruce(sk, x + pad, ty(x) + 6, h, int(rng.integers(1 << 20)), needle=(52, 66, 104), needle_d=(36, 44, 82),
               snow=(220, 228, 252), snow_sh=(134, 142, 200), ink_a=0.0, snow_amt=0.8, trunk_col=(52, 54, 92))
    arr = fold(sk.snap(), pad, WL)
    apply_fog(arr, 0, SKY, fog_amount(0.34, 0.25, 690, 40))
    L.over(arr)
    return L


def layer_mid(seed=40):
    """Orta: karlı kayalıklar ve donmuş çağlayan, buz kristali kümeleri, karlı ladinler, kam direği; kar zemini."""
    L = Layer(WL, H)
    rng = np.random.default_rng(seed)
    peaks = [(700, 440, 720, 260, 300, {'n_ridges': 7}), (2500, 470, 720, 300, 260, {'n_ridges': 6}),
             (3500, 500, 720, 240, 260, {'n_ridges': 5})]
    range_layer(L, SKY, peaks, lambda i: fog_amount(0.16, 0.22, 700, 40), seed + 1,
                rock_lit=(92, 96, 150), rock_sh=(46, 46, 90), snow_lit=SNOW_LIT, snow_sh=(140, 150, 206),
                snow_line=0.32, ink_a=0.8, ink_w=2.0, hatch=0.6, light=LIGHT, rough=0.2, crease=0.6, gully_snow=0.45,
                sil_rim=(236, 244, 255), sil_rim_w=1.8)
    frozen_fall(L, 760, 520, 726, 80, seed + 5, sky=SKY, fog=fog_amount(0.14, 0.2, 700, 40), ink_a=0.85, cliff=False)
    top, xs = snow_ground(L, SKY, seed + 2, 728, 34, fog_amount(0.1, 0.2, 715, 30), ink_a=0.7)
    ty = lambda x: float(np.interp(x % WL, xs, top))
    pad = 300
    sk = Sk(WL + 2 * pad, H)
    for k, cx in enumerate((300, 2000, 3150)):
        crystal_cluster(sk, cx + pad, ty(cx) + 6, rng.uniform(70, 110), seed + 10 + k, ink_a=0.8)
    shaman_pole(sk, 2300 + pad, ty(2300) + 6, 170, seed + 3, ink_a=0.85)
    for _ in range(26):
        x = rng.uniform(0, WL)
        if 640 < x < 880:
            continue
        spruce(sk, x + pad, ty(x) + 8, rng.uniform(80, 170), int(rng.integers(1 << 20)), needle=(52, 72, 112),
               needle_d=(34, 46, 84), ink_a=0.75, ink_w=1.3, snow_amt=1.4)
    arr = fold(sk.snap(), pad, WL)
    apply_fog(arr, 0, SKY, fog_amount(0.12, 0.22, 700, 40))
    L.over(arr)
    return L


def layer_near(seed=50):
    """Yakın: karla yüklü dev koyu ladinler (tepeleri kadraj dışında), buz sivrileri, karlı kayalar, kar tümsekleri."""
    L = Layer(WL, H)
    rng = np.random.default_rng(seed)
    top, xs = snow_ground(L, SKY, seed + 2, 752, 26, fog_amount(0.02, 0.1, 750, 30), ink_a=0.9, lit=(214, 226, 252),
                          mid=SNOW_MID, sh=(84, 96, 156), ink_w=2.4)
    ty = lambda x: float(np.interp(x % WL, xs, top))
    pad = 400
    sk = Sk(WL + 2 * pad, H)
    for k, cx in enumerate((900, 2600)):
        crystal_cluster(sk, cx + pad, ty(cx) + 10, rng.uniform(120, 160), seed + 20 + k, ink_a=1.0, ink_w=1.8)
    for k, cx in enumerate((200, 640, 1750, 2240, 3200, 3620)):
        spruce(sk, cx + pad + rng.uniform(-40, 40), ty(cx) + 14, rng.uniform(420, 620), seed + 40 + k,
               needle=(22, 34, 52), needle_d=(12, 18, 32), snow=(206, 218, 248), snow_sh=(96, 108, 170), ink_a=1.0,
               ink_w=2.2, trunk_col=(36, 26, 34))
    arr = fold(sk.snap(), pad, WL)
    apply_fog(arr, 0, SKY, fog_amount(0.03, 0.1, 740, 40, top=0.06))
    L.over(arr)
    from otuken_ink import rock as _rock
    for _ in range(6):
        r = _rock(int(rng.integers(1 << 30)), rng.uniform(34, 64), rng.uniform(22, 38), base=(84, 88, 136),
                  moss=SNOW_LIT, ink_w=3.0)
        x = rng.uniform(0, WL)
        place(L, r, x, ty(x) + 14, SKY, fog_amount(0.03, 0.1, 740, 30))
    return L


def layer_haze(seed=65):
    """Orta derinlik pusu: vadilerde asılı soğuk sis."""
    return veil(WL, SKY, seed, [(660, 80, 0.8), (560, 60, 0.3)], 0.3, MINT, 0.48, sx=(240, 70), sy=(30, 14))


def layer_blizzard(seed=60):
    """Tipi tülleri: rüzgârla yatay savrulan kar perdeleri (sürüklenir) + ince kar çizgileri."""
    return veil(WL, SKY, seed, [(700, 120, 0.8), (520, 120, 0.35), (860, 80, 0.5)], 0.55, (220, 230, 255), 0.55,
                sx=(200, 60), sy=(40, 10), streaks=0.45, streak_sx=220)


def layer_shafts(seed=70):
    """Aydan süzülen soğuk hüzmeler (toplamalı), soldan çapraz."""
    return rays(2880, seed, 20, (170, 200, 255), n=6, wid=(60, 160), inten=(0.12, 0.3), fade=(0.0, 0.08, 0.45, 0.7))


def layer_snow(seed=80):
    """Düşen kar (iki yönlü döşenir): ParallaxBG "snow" türü; hem kayar hem düşer."""
    return snowfall(1920, 1080, seed, 520, 0.8, 2.6, col=(236, 242, 255), alpha=(0.4, 0.95))


def layer_snow_far(seed=81):
    return snowfall(1920, 1080, seed, 900, 0.5, 1.4, col=(210, 222, 255), alpha=(0.25, 0.7))
