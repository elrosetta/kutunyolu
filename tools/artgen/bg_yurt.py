"""Ulu Kayın Yurdu (v13) paralaks katmanları, 1.5x yoğunluk (gök 960x540, diğerleri 1920x540; oyunda 2/3 ölçek).

  yurt_0_sky  : kutsal gece; çivit tepe, ufukta kehribar-turkuaz ışıma, kut ışığı perdeleri (kuzey ışığı), yıldızlar
  yurt_1_tree : Bai-Terek / Ulu Kayın: dağların ardından göğe yükselen dev ak kayın; ışıl taç, çaputlar, ruh ışıkları
                (tek ağaç, saydam katman; çok yavaş kayar, yurdun her yerinden görünür)
  yurt_2_camp : uzak büyük oba: tepelerde onlarca yurt, kapı ışıkları, ocak dumanları, tuğlar, at sürüsü, kurganlar
  yurt_3_mid  : yakın tepe: dilek kayınları, büyük yurt siluetleri, fener dizileri, tuğlar
Dağlar ve sis Ötüken'den (otuken_1_mountains, otuken_5_fog) ödünç alınır.
HD paketleri: bk.set_scale(N) ile N kat ince ızgarada aynı kompozisyon (bkz. bgkit.py); bk.S == 1 temel çıktıdır.

Kullanım: python bg_yurt.py   (assets/bg'ye yazar)
"""
import math
import os

import numpy as np

import bgkit as bk
from bgkit import W, H, SW, SH, Layer, norm, lin, mgrid, bay, nfbm, upx, thin
from hdkit import hexrgb, pal, bayer, fbm, to_image, reduce_palette

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = os.path.join(ROOT, 'assets')
LT = norm([0.55, -0.6, 0.58])
TREE_X = 560      # ağaç gövdesinin katman x'i (doku pikseli): yurt boyunca ekranın ortasında kalır


def _out(rgba, n=64):
    if n == 0:
        return to_image(rgba)
    return to_image(reduce_palette(rgba, n, 4))


def yurt_sky(seed=61):
    rng = np.random.default_rng(seed)
    img = bk.gradient([(0, '#04040f'), (0.22, '#0a0b22'), (0.45, '#141838'), (0.62, '#1f2648'), (0.74, '#2e3150'),
                       (0.84, '#4a3c4e'), (0.93, '#6a4a48'), (1.0, '#7a5444')], SW, SH)
    yy, xx = (np.mgrid[0:SH, 0:SW].astype(float) if bk.S == 1 else mgrid(SH, SW))
    Sx = bk.S
    # ağacın ardındaki kutsal ışıma (ekran ortası, biraz sol)
    cx, cy = 380.0, 250.0
    d = np.sqrt(((xx - cx) / 1.25) ** 2 + (yy - cy) ** 2)
    halo = np.clip(1 - d / 430, 0, 1) ** 2.0
    img = img + halo[..., None] * (hexrgb('#3f7f8a') - img) * 0.42
    # kut ışığı perdeleri: dalgalı, dikey çizgili turkuaz-yeşil bantlar, üstte mora döner
    curt = np.zeros(yy.shape)
    for (y0, amp, ph, fr, th) in ((150, 40, 0.3, 0.0062, 46), (205, 30, 2.1, 0.0085, 34), (110, 26, 4.0, 0.011, 24)):
        yc = y0 + np.sin(xx * fr + ph) * amp + np.sin(xx * fr * 2.7 + ph * 1.7) * amp * 0.35
        below = (yy - yc)
        band = np.where(below > 0, np.exp(-below / th), np.exp(below / 6.0))
        rays = 0.72 + 0.28 * np.sin(xx * 0.21 + np.sin(xx * 0.037 + ph) * 4.0)
        curt = np.maximum(curt, band * rays)
    curt *= np.clip(1 - np.abs(xx - 480) / 620, 0.25, 1)
    green = hexrgb('#5fe0b8'); violet = hexrgb('#8a5ad0')
    tint = green[None, None, :] * (1 - np.clip((150 - yy) / 120, 0, 1))[..., None] + violet[None, None, :] * np.clip((150 - yy) / 120, 0, 1)[..., None]
    img = img + curt[..., None] * 0.32 * (tint - img * 0.3)
    # samanyolu
    t = (xx * 0.5 - yy)
    band = np.exp(-((t + 40) / 80.0) ** 2)
    mw = nfbm(SW, SH, [96, 48, 24, 12], rng, wrap_y=False)
    img += (band * np.clip(mw - 0.4, 0, 1) * 0.14)[..., None] * hexrgb('#9aa6d8')
    img = bk.dq(np.clip(img, 0, 1), 64)
    L = Layer(SW, SH)
    L.rgba[..., :3] = img; L.rgba[..., 3] = 1
    for _ in range(1100):
        x, y = int(rng.integers(0, SW)), int(rng.integers(0, int(SH * 0.66)))
        br = rng.random()
        if rng.random() > band[y * Sx, x * Sx] * 0.7 + 0.4:
            continue
        c = hexrgb('#e8ecff') if br > 0.82 else (hexrgb('#9aa6cf') if br > 0.4 else hexrgb('#555d88'))
        if Sx == 1:
            L.px(x, y, c, 0.9)
            if br > 0.985:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    L.px(x + dx, y + dy, hexrgb('#7d88b8'), 0.8)
        else:
            if br > 0.985:
                w_ = thin() / Sx
                L.stroke([(x - 1.1, y + 0.5 - w_ / 2), (x + 2.1, y + 0.5 - w_ / 2)], hexrgb('#7d88b8'), 0.8, wid=w_, gap=1e9)
                L.stroke([(x + 0.5 - w_ / 2, y - 1.1), (x + 0.5 - w_ / 2, y + 2.1)], hexrgb('#7d88b8'), 0.8, wid=w_, gap=1e9)
            L.star(x, y, c, 0.9)
    # Ülker (Pleiades): küçük parlak yıldız öbeği sağ üstte
    for dx, dy in ((0, 0), (5, -2), (9, 1), (3, 4), (12, -4), (7, 6)):
        if Sx == 1:
            L.px(800 + dx, 70 + dy, hexrgb('#f4f6ff'))
            L.px(801 + dx, 70 + dy, hexrgb('#9aa6cf'), 0.6)
        else:
            L.dot(800 + dx + 0.5, 70 + dy + 0.25, hexrgb('#9aa6cf'), 0.6, r=max(1, Sx // 2) + 1)
            L.star(800 + dx, 70 + dy, hexrgb('#f4f6ff'))
    # ince ay hilali
    mx, my, R = 860.0, 150.0, 18.0
    dm = np.sqrt((xx - mx) ** 2 + (yy - my) ** 2)
    dm2 = np.sqrt((xx - mx - 7) ** 2 + (yy - my + 4) ** 2)
    cres = (dm < R) & (dm2 > R * 0.92)
    L.rgba[cres, :3] = hexrgb('#f2e6c4')
    glow = np.clip(1 - dm / 70, 0, 1) ** 2 * 0.25 * (dm >= R)
    L.rgba[..., :3] = L.rgba[..., :3] + glow[..., None] * (hexrgb('#c8b890') - L.rgba[..., :3])
    return _out(L.rgba, 0)


def yurt_tree(seed=62):
    """Dev ak kayın: puslu-ak gövde, kara halkalar, göğe açılan dallar, turkuaz-altın ışıl taç, sarkan çaputlar."""
    rng = np.random.default_rng(seed)
    out = Layer()
    X0 = TREE_X
    # arka ışıma (saydam, basamaklı)
    yy, xx = (np.mgrid[0:H, 0:W].astype(float) if bk.S == 1 else mgrid(H, W))
    dx = (xx - X0 + W / 2) % W - W / 2
    d = np.sqrt((dx / 1.6) ** 2 + ((yy - 150) / 1.0) ** 2)
    glow_a = np.clip(1 - d / 420, 0, 1) ** 1.6 * 0.30
    ga = np.floor(glow_a * 10 + (bay(H, W) - 0.5) * 0.9) / 10
    out.rgba[..., :3] = hexrgb('#4fa7a8')
    out.rgba[..., 3] = np.clip(ga, 0, 1)
    T = Layer()
    BARK = pal('#1c2232', '#273042', '#343e54', '#445068', '#56627c', '#6c7a94', '#8896ae')
    rim = hexrgb('#8fd8d0')
    # gövde: dev, aşağıda genişleyen; kökler yayılır
    trunk = [(X0, 560), (X0 - 8, 440), (X0 + 6, 330), (X0 - 4, 250), (X0 + 4, 196)]
    T.tube(trunk, 70, 30, BARK, LT, bark=0.35, rng=rng, rim_col=rim, rr=[86, 64, 50, 42, 36])
    for s_ in (-1, 1):
        for k in range(2):
            T.tube([(X0 + s_ * 30, 430 + k * 30), (X0 + s_ * (90 + k * 40), 470 + k * 25), (X0 + s_ * (170 + k * 60), 520)], 26 - k * 6, 6, BARK, LT)
    # kayın halkaları (koyu yatay lekeler)
    for k in range(110):
        y = rng.uniform(200, 520)
        r = float(np.interp(y, [196, 250, 330, 440, 560], [36, 42, 50, 64, 86]))
        xc = float(np.interp(y, [196, 250, 330, 440, 560], [X0 + 4, X0 - 4, X0 + 6, X0 - 8, X0]))
        w_ = rng.uniform(5, 18)
        x0 = xc + rng.uniform(-r * 0.85, r * 0.6)
        if bk.S == 1:
            for j in range(int(w_)):
                T.px(x0 + j, y + (1 if j % 4 == 0 else 0), BARK[0])
                if j % 2 == 0:
                    T.px(x0 + j, y + 1, BARK[1])
        else:
            # HD: kayın lekesi: ortası kalın, uçları incelen kara yarık + altında koyu gölge
            nj = int(w_)
            T.stroke([(x0 + j, y + 1.2 + 0.25 * math.sin(j * 0.7)) for j in range(nj)], BARK[1], wid=0.8, gap=1e9)
            T.stroke([(x0 + j, y + 0.4 + 0.25 * math.sin(j * 0.7)) for j in range(nj)], BARK[0], wid=0.9, gap=1e9)
    # taç: dalların ucunda ayrı ayrı büyük bulut-öbekleri, aralarından gök ve dallar görünür
    CL = [(-480, 175, 104, 46), (-340, 84, 120, 52), (-160, 22, 130, 56), (30, -24, 150, 62), (210, 34, 130, 54),
          (370, 96, 120, 50), (500, 184, 96, 42), (-250, 196, 76, 34), (280, 206, 76, 32), (-70, 128, 66, 30), (120, 140, 60, 28)]
    top = (X0 + 4, 200)
    BR = pal('#141a28', '#1c2434', '#262f42', '#323c52', '#404c64', '#505e78')
    for dx, cy, rx, ry in CL:
        ex, ey = X0 + dx, cy + ry * 0.2
        c1 = (X0 + dx * 0.3, top[1] - 40 - abs(dx) * 0.12)
        c2 = (X0 + dx * 0.75, ey - 30)
        w0 = 19 if abs(dx) > 300 else 16
        T.tube([top, c1, c2, (ex, ey)], w0, 4, BR, LT, bark=0.3, rng=rng)
        for k in range(3):
            t = rng.uniform(0.45, 0.9)
            bx = c1[0] + (ex - c1[0]) * t; by = c1[1] + (ey - c1[1]) * t
            T.tube([(bx, by), (bx + rng.uniform(-50, 50), by - rng.uniform(25, 55))], 5, 1.0, BR, LT)
    LEAF = pal('#060d16', '#09141e', '#0d1b26', '#12232f', '#182c38', '#1f3742', '#28444d', '#335458')
    lights = []
    for dx, cy, rx, ry in CL:
        cx0 = X0 + dx
        pts = []
        for k in range(int(rx * ry / 260) + 8):
            a = rng.uniform(0, math.tau); r = rng.uniform(0, 1) ** 0.5
            pts.append((cy + math.sin(a) * r * ry, cx0 + math.cos(a) * r * rx, rng.uniform(18, 34) * (1.1 - 0.35 * r)))
        pts.sort(key=lambda c: -c[0])
        for py_, px_, r in pts[::-1]:
            lift = -0.15 + (cy - py_) / ry * 0.18
            T.sphere(px_, py_, r, LEAF, LT, rough=0.55, rng=rng, squash=0.7, edge_cut=0.35, lift=lift, cell=3.0, rim_col=hexrgb('#4a8480') if rng.random() < 0.5 else None)
        for k in range(int(rx * ry / 40)):
            a = rng.uniform(0, math.tau); r = rng.uniform(0, 1) ** 0.6
            lights.append((cx0 + math.cos(a) * r * rx * 1.05, cy + math.sin(a) * r * ry * 1.05))
        # öbeğin altından sarkan çaputlar
        for k in range(int(rx / 40)):
            x = cx0 + rng.uniform(-rx * 0.8, rx * 0.8)
            y = cy + ry * 0.75 * math.sqrt(max(0.0, 1 - ((x - cx0) / rx) ** 2)) - 4
            ln = int(rng.integers(5, 12))
            cols = [hexrgb(c) for c in ('#c84a50', '#e8e0d0', '#4a7ad0', '#e8b840', '#40b890')]
            c = cols[int(rng.integers(0, len(cols)))] * 0.7
            if bk.S == 1:
                for j in range(ln):
                    T.px(x, y + j, c)
                    T.px(x + 1, y + j, c * 0.7)
            else:
                rib = [(x + math.sin(j * 0.8) * 0.25, y + j) for j in range(ln)]
                T.stroke([(a + 1, b) for a, b in rib], c * 0.7, gap=1e9)
                T.stroke(rib, c, gap=1e9)
    for x, y in lights:
        c = hexrgb('#9df2e0') if rng.random() < 0.72 else hexrgb('#ffe7a0')
        if bk.S == 1:
            T.px(x, y, c)
            if rng.random() < 0.4:
                T.px(x + 1, y, c * 0.7); T.px(x, y + 1, c * 0.55)
            if rng.random() < 0.06:
                for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    T.px(x + ddx, y + ddy, c * 0.65)
        else:
            big = rng.random() < 0.4
            cross = rng.random() < 0.06
            r_ = max(1, bk.S // 2)
            if big:
                T.dot(x + 0.5, y + 0.25, c * 0.7, r=r_); T.dot(x + 0.25, y + 0.5, c * 0.55, r=r_)
            if cross:
                w_ = thin() / bk.S
                T.stroke([(x - 1, y + 0.5), (x + 2, y + 0.5)], c * 0.65, wid=w_, gap=1e9)
                T.stroke([(x + 0.5, y - 1), (x + 0.5, y + 2)], c * 0.65, wid=w_, gap=1e9)
            T.dot(x, y, c, r=r_ + (1 if big else 0))
    # atmosfer: uzak, mavimsi pus (gövde altı daha puslu)
    hz = np.clip((yy - 200) / 260, 0, 1) * 0.45 + 0.1
    bk.apply_haze(T.rgba, '#2a3a52', hz * (T.rgba[..., 3] > 0))
    out.over(T)
    # ışıl noktalar pustan etkilenmesin: tekrar parlat (taçtaki kut ışıkları)
    return _out(out.rgba, 72)


def yurt_camp(seed=63):
    """Uzak büyük oba: üç tepe sırası, yurt kümeleri (kapı ışıklı), duman, tuğ siluetleri, at sürüsü, kurganlar."""
    rng = np.random.default_rng(seed)
    out = Layer()
    rows = [(352, 24, pal('#141c30', '#18223a', '#1d2842', '#222f4a', '#283652'), 0.32),
            (372, 26, pal('#10172a', '#141c32', '#18223a', '#1d2842', '#222f4a'), 0.2),
            (394, 30, pal('#0b1222', '#0e1628', '#121b30', '#162036', '#1a263e'), 0.08)]
    felt = [pal('#3a3c4c', '#555666', '#6e6c78', '#86828a'), pal('#34384c', '#4c5068', '#626680', '#787c94')]
    door = [hexrgb('#ffb45a'), hexrgb('#ff9440'), hexrgb('#ffd890')]
    for k, (base, amp, ramp, hz) in enumerate(rows):
        ridge = bk.ridge_line(W, base, amp, [480, 240, 120, 60], rng)
        L = Layer()
        bk.hills(L, ridge, ramp, LT, rng, grass=None, shadows=0.08, depth_dark=0.15, tex=0.05)
        n_y = (14, 18, 10)[k]
        s_r = ((6, 8), (8, 11), (10, 14))[k]
        xs = np.sort(rng.uniform(0, W, n_y))
        for cx in xs:
            for j in range(int(rng.integers(1, 4))):
                xx = cx + j * rng.uniform(s_r[1] * 1.4, s_r[1] * 2.2)
                s = rng.uniform(*s_r)
                b = ridge[int(xx) % W] + 2
                bk.yurt(L, xx, b, s, felt[int(rng.integers(0, 2))], rng, smoke=hexrgb('#5a6276') if rng.random() < 0.5 else None)
                # kapı ışığı (yurt fonksiyonunun kızıl kapısını kehribar ışıkla değiştir)
                hb = s * 0.42
                if bk.S == 1:
                    for y in range(int(b - hb * 0.7), int(b) + 1):
                        L.px(xx + 1, y, door[0]); L.px(xx + 2, y, door[1])
                    L.px(xx + 1, b - hb * 0.7 - 1, door[2])
                    # yerde ışık lekesi
                    for ddx in range(-3, 6):
                        L.px(xx + ddx, b + 1, door[1], 0.35)
                else:
                    fx_ = math.floor(xx)
                    L.poly([(fx_ + 1, b - hb * 0.7), (fx_ + 2, b - hb * 0.7), (fx_ + 2, math.floor(b) + 1), (fx_ + 1, math.floor(b) + 1)], door[0])
                    L.poly([(fx_ + 2, b - hb * 0.7), (fx_ + 3, b - hb * 0.7), (fx_ + 3, math.floor(b) + 1), (fx_ + 2, math.floor(b) + 1)], door[1])
                    L.stroke([(fx_ + 1, b - hb * 0.7 - 0.6), (fx_ + 2.6, b - hb * 0.7 - 0.6)], door[2], wid=thin() / bk.S, gap=1e9)
                    L.stroke([(xx - 3, b + 1), (xx + 6, b + 1)], door[1], 0.35, wid=1.0, gap=1e9)
            # tuğ direği
            if rng.random() < 0.5:
                tx = cx - rng.uniform(6, 12)
                tb = ridge[int(tx) % W] + 2
                th = s_r[1] * 3.2
                fc = None
                if bk.S == 1:
                    L.line(tx, tb, tx, tb - th, ramp[0])
                    for j in range(4):
                        L.px(tx - 1 + (j % 2), tb - th + 2 + j, hexrgb('#0a0a10'))
                    fc = hexrgb('#8a3040') if rng.random() < 0.6 else hexrgb('#30508a')
                    for j in range(int(s_r[1])):
                        for i in range(3):
                            L.px(tx + 1 + j, tb - th + 3 + i + (j // 4), fc * (0.8 if i == 2 else 1.0))
                else:
                    # HD: ince direk, at kılı püskül, rüzgârda dalgalanan sancak
                    L.line(tx + 0.5, tb, tx + 0.5, tb - th, ramp[0], wid=0.6)
                    L.stroke([(tx - 0.6, tb - th + 1.6), (tx + 0.5, tb - th + 2.2), (tx - 0.2, tb - th + 6.0)], hexrgb('#0a0a10'), wid=0.9, gap=1e9)
                    fc = hexrgb('#8a3040') if rng.random() < 0.6 else hexrgb('#30508a')
                    fl_ = int(s_r[1])
                    up_ = [(tx + 1 + j, tb - th + 3 + j / 4 + math.sin(j * 0.9) * 0.3) for j in range(fl_ + 1)]
                    dn_ = [(a, b_ + 3) for a, b_ in up_]
                    L.poly(up_ + dn_[::-1], fc)
                    L.stroke([(a, b_ - 0.6) for a, b_ in dn_], fc * 0.8, wid=1.0, gap=1e9)
        # ocak ateşleri (parlak kıvılcım noktaları)
        for _ in range((6, 9, 5)[k]):
            fx = rng.uniform(0, W)
            fb = ridge[int(fx) % W] + 1
            if bk.S == 1:
                L.px(fx, fb, hexrgb('#ffe6a0')); L.px(fx + 1, fb, hexrgb('#ff9a40')); L.px(fx, fb - 1, hexrgb('#ffb860'))
                L.px(fx - 1, fb, hexrgb('#c86030'))
                for j in range(8):
                    L.px(fx + j * 0.3, fb - 2 - j, hexrgb('#5a6276'), 0.4 * (1 - j / 8))
            else:
                # HD: küçük alev dili (dıştan içe), üstünde incelen duman
                for j in range(8):
                    L.stroke([(fx + j * 0.3 + math.sin(j * 0.8) * 0.25, fb - 2 - j), (fx + (j + 1) * 0.3 + math.sin((j + 1) * 0.8) * 0.25, fb - 3 - j)],
                             hexrgb('#5a6276'), 0.4 * (1 - j / 8), wid=0.8, gap=1e9)
                L.stroke([(fx - 1, fb + 0.5), (fx + 0.2, fb + 0.5)], hexrgb('#c86030'), wid=1.0, gap=1e9)
                L.poly([(fx - 0.5, fb + 1), (fx + 1.8, fb + 1), (fx + 0.8, fb - 1.4)], hexrgb('#ff9a40'))
                L.poly([(fx + 0.1, fb + 1), (fx + 1.2, fb + 1), (fx + 0.5, fb - 0.6)], hexrgb('#ffe6a0'))
        if k == 1:
            for _ in range(12):
                hx = 1350 + rng.uniform(-70, 70)
                bk.horse(L, hx, ridge[int(hx) % W] + 7 + rng.uniform(0, 5), hexrgb('#080a12'), rng, facing=1 if rng.random() < 0.5 else -1)
        if k == 0:
            for x in rng.uniform(0, W, 4):
                bk.kurgan(L, x, ridge[int(x) % W] + 3, rng.uniform(14, 22), rng.uniform(5, 8), ramp, LT, rng)
        bk.apply_haze(L.rgba, '#2c3a56', hz * (L.rgba[..., 3] > 0))
        out.over(L)
    return _out(out.rgba)


def yurt_mid(seed=64):
    """Yakın sırt: dilek kayınları, büyük yurt siluetleri, iplerde fener dizileri, tuğlar. Düşük kontrast."""
    rng = np.random.default_rng(seed)
    out = Layer()
    G = pal('#070c12', '#0a121a', '#0e1822', '#13202c', '#192a36', '#213440')
    BIR = pal('#1a1e28', '#3a404e', '#555c6a', '#707684', '#8a909c')
    LEAFB = pal('#0a141a', '#0f1c24', '#14262e', '#1b3038', '#243c44', '#2e4a50')
    ridge = bk.ridge_line(W, 418, 14, [480, 240, 120], rng)
    felt = pal('#1c1e2a', '#2c2e3c', '#3a3c4c', '#4a4a5a')
    # büyük yurtlar
    for cx in (260, 700, 1180, 1620):
        b = ridge[cx % W] + 3
        bk.yurt(out, cx, b, rng.uniform(26, 34), felt, rng, smoke=hexrgb('#3a4252'))
        s = 30
        if bk.S == 1:
            for y in range(int(b - s * 0.42 * 0.7), int(b) + 1):
                for dd in range(1, 4):
                    out.px(cx + dd, y, hexrgb('#e09040') if dd < 3 else hexrgb('#a05a28'))
        else:
            yt_ = int(b - s * 0.42 * 0.7)
            out.poly([(cx + 1, yt_), (cx + 3, yt_), (cx + 3, int(b) + 1), (cx + 1, int(b) + 1)], hexrgb('#e09040'))
            out.poly([(cx + 3, yt_), (cx + 4, yt_), (cx + 4, int(b) + 1), (cx + 3, int(b) + 1)], hexrgb('#a05a28'))
    # kayınlar
    for x in (120, 470, 930, 1400, 1800):
        b = ridge[x % W] + 4
        h = rng.uniform(120, 170)
        out.tube([(x, b), (x + rng.uniform(-6, 6), b - h * 0.8)], 3.4, 1.8, BIR, LT)
        for k in range(int(h / 8)):
            yk = b - rng.uniform(5, h * 0.75)
            out.line(x - 3, yk, x + 1, yk + rng.uniform(-1, 1), BIR[0])
        bk.deciduous(out, x, b - h * 0.35, h * 0.75, LEAFB, BIR, LT, rng, crown_w=0.5, sparse=0.25, rim_col=hexrgb('#3f6466'), branch_r=1.6)
        cols = [hexrgb(c) for c in ('#7a2a30', '#9a9488', '#284a7a', '#9a7a2a')]
        for _ in range(16):
            cx_ = x + rng.uniform(-40, 40); cy_ = b - h * 0.6 + rng.uniform(-20, 20)
            c = cols[int(rng.integers(0, 4))]
            nk = int(rng.integers(4, 10))
            out.stroke([(cx_ + math.sin(k * 0.9) * 0.2, cy_ + k) for k in range(nk)] if bk.S > 1 else [(cx_, cy_ + k) for k in range(nk)], c, gap=1e9)
    # fener dizileri: direkler arası sarkık ip, üstünde kehribar fenerler
    poles = [60, 380, 560, 860, 1040, 1300, 1500, 1720, 1900]
    for p in poles:
        b = ridge[p % W] + 3
        out.line(p, b, p, b - 70, G[2])
        _pt_ = out.px if bk.S == 1 else (lambda x_, y_, c_: out.dot(x_ + 0.25, y_ + 0.25, c_, r=max(1, bk.S // 2) + 1))
        _pt_(p, b - 71, hexrgb('#c8a040'))
    for a, b_ in zip(poles, poles[1:]):
        ya = ridge[a % W] + 3 - 66; yb = ridge[b_ % W] + 3 - 66
        n = int(b_ - a)
        if bk.S > 1:
            # HD: sarkık ip sürekli ve ince
            out.stroke([(a + i, ya + (yb - ya) * (i / n) + math.sin(i / n * math.pi) * 22 + 0.25) for i in range(n + 1)], G[3], wid=0.6, gap=1e9)
        for i in range(n + 1):
            t = i / n
            y = ya + (yb - ya) * t + math.sin(t * math.pi) * 22
            if bk.S == 1:
                out.px(a + i, y, G[3])
            if i % 22 == 11:
                out.px(a + i, y + 1, G[3])
                for yy_ in range(2, 6):
                    out.px(a + i, y + yy_, hexrgb('#ffc060') if yy_ < 5 else hexrgb('#c87830'))
                    out.px(a + i + 1, y + yy_, hexrgb('#e09040'))
            elif i % 11 == 5:
                fc = [hexrgb('#8a2a30'), hexrgb('#2a4a8a'), hexrgb('#a08a3a'), hexrgb('#a8a8a0')][(i // 11) % 4]
                for yy_ in range(1, 5):
                    for xx_ in range(0, 4 - yy_ // 2):
                        out.px(a + i + xx_ - 1, y + yy_, fc * 0.7)
    # ön tümsek ve ot
    L = Layer()
    bk.hills(L, ridge, G, LT, rng, grass=0.5, shadows=0.05, depth_dark=0.3, tex=0.06)
    out.over(L)
    bk.apply_haze(out.rgba, '#1a2636', 0.18 * (out.rgba[..., 3] > 0))
    return _out(out.rgba)


LAYERS = {'yurt_0_sky': yurt_sky, 'yurt_1_tree': yurt_tree, 'yurt_2_camp': yurt_camp, 'yurt_3_mid': yurt_mid}


if __name__ == '__main__':
    import sys
    only = [a for a in sys.argv[1:] if not a.startswith('-')]
    for nm, fn in LAYERS.items():
        if only and nm not in only:
            continue
        fn().save(os.path.join(A, 'bg', nm + '.png'))
        print('bg', nm)
