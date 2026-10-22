"""v40 ortam cilası dokuları (stil v2 mürekkep): hava canlıları ve bakış anıtları.

Kullanım (tools/artgen içinde):
    python ortam40_ink.py                 hepsi
    python ortam40_ink.py --hava          hava canlıları  assets/bg/hava_{karga,kartal,yarasa}_v2.png (4 kare kanat çırpışı,
                                          ekran uzayı: 1080p'de 1 doku pikseli = 1 ekran pikseli; beyaz siluet, renk oyunda)
    python ortam40_ink.py --anit [biyom]  bakış anıtları  assets/decor/anit_<biyom>_v2.png (+ _e) ve decor_v2_<biyom>.json
                                          girdisi (dünya uzayı: 4 doku pikseli / birim, OrtamCila._anitlar z -4'e koyar)
KY_HD=2 ile çalıştırılırsa çıktılar assets_hd/x2'ye 2 kat çözünürlükte gider (hdpack.py); sonra hd_paket.py --paketle.

Anıtlar: Ötüken "Ulu Kayın sunağı" (iki yaşlı huş, aralarında çaput ipi, dibinde balballar), Bozkır "Han kurganı" (taş
halkalı büyük kurgan, tepesinde tuğ, önünde balbal dizisi), Kaf "Buz kulesi" (dev buz kristali kümesi + karlı kam direği),
Şahmeran "Yılan sütunu" (kehribar gözlü yılan kabartmalı sütun + kristaller), Tamu "Kemik kapısı" (dev kaburga kemeri,
öküz kafatası, zincirler, kor gözler ışıma).
"""
import json
import math
import os
import sys

import numpy as np

import inkkit_ortam as ik
from hdpack import HD
from inkkit_ortam import INK, Layer, Sk, bezier, blade, blob, c01, poly_path, premul, ribbon, smooth_path, trunk
import export_ink_ortam as E

A = E.A


# ------------------------------------------------------------------ hava canlıları (ekran uzayı, K = 1 x HD)
def _bird_frame(sk, cx, cy, s, phase, kind):
    """Tek kare siluet (beyaz; renk oyunda modüle edilir). phase 0..1: kanat çırpışı (0 yukarı, 0.5 aşağı)."""
    w = math.sin(phase * 2 * math.pi)       # +1 kanat yukarı, -1 aşağı
    WH = (255, 255, 255)
    if kind == 'karga':
        # gövde + baş + gaga + çatal kuyruk (yandan, sağa uçar)
        sk.path(smooth_path([(cx - 14 * s, cy), (cx - 4 * s, cy - 4 * s), (cx + 10 * s, cy - 4 * s), (cx + 18 * s, cy - 1.5 * s),
                             (cx + 26 * s, cy + 0.5 * s), (cx + 17 * s, cy + 3 * s), (cx + 4 * s, cy + 4.5 * s), (cx - 10 * s, cy + 4 * s)], True, 0.4), WH)
        sk.path(poly_path([(cx - 12 * s, cy - 1 * s), (cx - 28 * s, cy - 3 * s), (cx - 27 * s, cy + 1 * s), (cx - 28 * s, cy + 5 * s), (cx - 11 * s, cy + 4 * s)]), WH)
        # iki kanat (yakın öndeki, uzak arkadaki biraz küçük): omuzdan dirseğe, dirsekten uca; arka kenarda parmak tüyleri
        for k_, (dx_, sc) in enumerate(((0.0, 1.0), (-3.0, 0.8))):
            sh = (cx + 2 * s + dx_ * s, cy - 2 * s)
            el = (cx - 8 * s + dx_ * s, cy - (12 * w + 3) * s * sc)
            tp = (cx - 20 * s + dx_ * s, cy - (26 * w + 2) * s * sc)
            q = bezier(sh, el, tp, 10)
            sk.path(ribbon(q, np.linspace(8 * s, 3 * s, 10)), WH, 1.0 if k_ == 0 else 0.9)
            for j in range(3):
                f0 = q[8 - j * 2]
                f1 = (f0[0] - (7 + 2 * j) * s, f0[1] + (5 - 3 * w) * s * (1 + 0.5 * j))
                sk.path(ribbon([tuple(f0), f1], [3.2 * s, 0.8 * s]), WH, 1.0 if k_ == 0 else 0.9)
    elif kind == 'kartal':
        # süzülen kartal: geniş düz kanatlar, uçta açık parmak tüyleri; çırpış küçük
        sk.path(smooth_path([(cx - 10 * s, cy), (cx + 2 * s, cy - 4 * s), (cx + 14 * s, cy - 3 * s), (cx + 20 * s, cy - 0.5 * s),
                             (cx + 9 * s, cy + 4 * s), (cx - 8 * s, cy + 4 * s)], True, 0.4), WH)
        sk.path(poly_path([(cx - 8 * s, cy - 1 * s), (cx - 24 * s, cy - 2 * s), (cx - 24 * s, cy + 5 * s), (cx - 8 * s, cy + 4 * s)]), WH)
        for side in (-1, 1):
            sh = (cx + 2 * s, cy)
            el = (cx + side * 22 * s, cy - (4 * w + 4) * s)
            tp = (cx + side * 46 * s, cy - (8 * w + 1) * s)
            q = bezier(sh, el, tp, 12)
            sk.path(ribbon(q, np.linspace(11 * s, 6 * s, 12)), WH)
            for j in range(5):
                f0 = q[11 - j]
                f1 = (f0[0] - side * (1 + 1.5 * j) * s, f0[1] + (8 + 1.5 * j) * s)
                sk.path(ribbon([tuple(f0), f1], [3.0 * s, 0.7 * s]), WH)
    elif kind == 'yarasa':
        sk.path(smooth_path([(cx - 6 * s, cy - 1 * s), (cx, cy - 4 * s), (cx + 6 * s, cy - 1 * s), (cx + 4 * s, cy + 5 * s), (cx - 4 * s, cy + 5 * s)], True, 0.4), WH)
        for sx in (-1, 1):
            sk.path(poly_path([(cx + sx * 2 * s, cy - 3 * s), (cx + sx * 5 * s, cy - 9 * s), (cx + sx * 6 * s, cy - 2 * s)]), WH)
        for side in (-1, 1):
            sh = (cx + side * 4 * s, cy - 1 * s)
            el = (cx + side * 15 * s, cy - (10 * w + 4) * s)
            tp = (cx + side * 30 * s, cy - (18 * w) * s)
            bb = (cx + side * 3 * s, cy + 5 * s)
            # alt kenar: uçtan gövdeye; parmak uçları dışa (aşağı), aralar içbükey
            low = []
            for j, t in enumerate((0.18, 0.36, 0.55, 0.74, 0.9)):
                px_ = tp[0] + (bb[0] - tp[0]) * t
                py_ = tp[1] + (bb[1] - tp[1]) * t
                py_ += (-3.5 * s if j % 2 == 1 else 3.0 * s)
                low.append((px_, py_))
            sk.path(poly_path([sh, el, tp] + low + [bb]), WH)


def hava_strip(kind, cell=(96, 64), frames=4, s=1.0):
    W, Hh = cell[0] * frames, cell[1]
    sk = Sk(W, Hh)
    for f in range(frames):
        _bird_frame(sk, cell[0] * f + cell[0] / 2, Hh / 2 + 6, s, f / frames, kind)
    L = Layer(W, Hh)
    L.a = sk.snap()
    # kenarda hafif yumuşama: uzak siluet (keskin vektör kenarı 1080p'de fazla sert)
    return L


def export_hava():
    ik.K = 1.0 * HD
    for kind, s in (('karga', 1.0), ('kartal', 1.0), ('yarasa', 1.0)):
        L = hava_strip(kind, s=s)
        E.save(L.rgba8(), 'bg', 'hava_%s_v2.png' % kind)


# ------------------------------------------------------------------ anıtlar (dünya uzayı, K = WORLD_K x HD)
def _grass(sk, rng, x0, x1, base_y, cols, n=50, hmax=22, lean=0.0):
    for _ in range(n):
        x = rng.uniform(x0, x1)
        sk.path(blade(x, base_y + 4, rng.uniform(6, hmax), rng.uniform(-0.45, 0.45) + lean, rng.uniform(1.6, 3.0)),
                cols[int(rng.integers(len(cols)))], 0.95)


def anit_otuken(seed=4001):
    """Ulu Kayın sunağı: iki yaşlı huş, aralarına gerilmiş çaput ipi, dibinde taş sunak ve iki balbal."""
    import otuken_ink_decor as D
    from otuken_ink import balbal, foliage, rock
    W, Hh = 520, 330
    L = Layer(W, Hh)
    base_y = Hh - 6
    rng = np.random.default_rng(seed)
    sk = Sk(W, Hh)
    # arka yaprak kütleleri
    for cx, cy, r in ((150, 40, 62), (372, 34, 70), (262, 22, 48)):
        foliage(sk, cx, cy, r, int(rng.integers(1 << 30)), (50, 74, 52), (120, 156, 108), n=110, leaf=(10, 18), ink_a=0.45)
    # dallar
    tips = []
    for x0, side, y0, ln in ((150, 1, 120, 120), (372, -1, 110, 120), (150, -1, 88, 70), (372, 1, 80, 80)):
        ang = math.radians(rng.uniform(32, 50))
        p2 = (x0 + side * math.sin(ang) * ln, y0 - math.cos(ang) * ln * 0.6)
        pts = bezier((x0, y0), ((x0 + p2[0]) / 2, (y0 + p2[1]) / 2 - 10), p2, 12)
        sk.path(ribbon(pts, np.linspace(11, 2.5, 12)), D.BARK_B)
        sk.path(ribbon(pts, np.linspace(11, 2.5, 12)), INK, 1.0, 0, 1.7)
        tips.append(pts)
        foliage(sk, p2[0], p2[1] - 8, 30, int(rng.integers(1 << 30)), (56, 82, 56), (126, 162, 112), n=50, ink_a=0.5)
    L.a = sk.snap()
    for x0, lean in ((150, -0.05), (372, 0.06)):
        arr, xl, yt = trunk(Hh, W, base_y, x0, 40, int(rng.integers(1 << 30)), kind='birch', lean=lean, bend=0.2, top_y=14,
                            bark=D.BARK_B, light=D.BARK_L, rim=(200, 230, 210), ink_w=2.8, taper=0.4)
        L.over(arr, xl, yt)
    sk2 = Sk(W, Hh)
    # çaput ipi: iki gövde arasında sarkık ip, üstünde renkli şeritler
    a, b = (164, 104), (358, 98)
    rope = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + math.sin(t * math.pi) * 26) for t in np.linspace(0, 1, 20)]
    sk2.path(ribbon(rope, [1.6] * 20), (40, 34, 36))
    for k in range(1, 19):
        if rng.random() < 0.2:
            continue
        q = rope[k]
        col = D.CLOTH[int(rng.integers(len(D.CLOTH)))]
        ln = rng.uniform(22, 44)
        sw = rng.uniform(-6, 8)
        cpts = bezier((q[0], q[1]), (q[0] + sw * 0.4, q[1] + ln * 0.5), (q[0] + sw, q[1] + ln), 10)
        wd = np.linspace(rng.uniform(4, 7), rng.uniform(2.5, 4.5), 10)
        sk2.path(ribbon(cpts, wd), col)
        sk2.path(ribbon(cpts[:4], wd[:4] * 0.6), tuple(np.array(col) * 0.7), 0.8)
        sk2.path(ribbon(cpts, wd), INK, 1.0, 0, 1.2)
    # dallardaki çaputlar
    for pts in tips[:2]:
        for t in (0.4, 0.6, 0.8):
            q = pts[int(t * 11)]
            col = D.CLOTH[int(rng.integers(len(D.CLOTH)))]
            ln = rng.uniform(24, 46)
            cpts = bezier((q[0], q[1]), (q[0] + 2, q[1] + ln * 0.5), (q[0] + rng.uniform(-8, 8), q[1] + ln), 10)
            wd = np.linspace(6, 3.5, 10)
            sk2.path(ribbon(cpts, wd), col)
            sk2.path(ribbon(cpts, wd), INK, 1.0, 0, 1.2)
    # taş sunak: üst üste yassı taşlar
    for i, (rx, ry) in enumerate(((40, 10), (30, 9), (22, 8))):
        y = base_y - 4 - i * 15
        p = blob(262, y, rx, ry, seed + 30 + i, n=10, jitter=0.12)
        sk2.path(p, (112, 118, 108))
        sk2.path(blob(262 - 10, y - 3, rx * 0.6, ry * 0.45, seed + 40 + i, n=8, jitter=0.1), (150, 158, 142), 0.6)
        sk2.path(p, INK, 1.0, 0, 2.2)
    for k, bx in enumerate((222, 306)):
        balbal(sk2, bx, base_y, 74 + 10 * k, (104, 110, 100), (140, 150, 134), seed + 50 + k)
    _grass(sk2, rng, 60, W - 60, base_y, [(52, 84, 58), (104, 142, 98), (74, 104, 70)], n=120, hmax=24)
    L.over(sk2.snap())
    for _ in range(4):
        r = rock(int(rng.integers(1 << 30)), rng.uniform(16, 26), rng.uniform(11, 16), base=(96, 102, 92))
        h, w = r.shape[:2]
        L.over(r, int(rng.uniform(70, W - 70) - w / ik.K / 2), int(base_y - h / ik.K + 6))
    return L, (W, Hh), (W / 2, base_y)


def anit_bozkir(seed=4002):
    """Han kurganı: taş halkalı büyük kurgan, tepesinde kurt başlı tuğ, önünde balbal dizisi, kuru ot."""
    from bozkir_ink import kurgan, tug, mirrored
    from otuken_ink import balbal
    import bozkir_ink_decor as D
    W, Hh = 560, 300
    sk = Sk(W, Hh)
    base_y = Hh - 8
    rng = np.random.default_rng(seed)
    kurgan(sk, W / 2, base_y - 10, 230, 118, (176, 112, 84), (104, 62, 78), stones=(128, 100, 100), ink_a=0.95, ink_w=2.4,
           seed=seed, stele=False, rim=(255, 206, 150))
    tug(sk, W / 2 + 14, base_y - 126, 150, wind=1.0, ink_a=0.95, seed=seed + 3)
    tug(sk, W / 2 - 30, base_y - 112, 120, wind=1.0, flag=(48, 86, 150), ink_a=0.95, seed=seed + 4)
    for k, bx in enumerate((90, 150, 410, 470)):
        mirrored(sk, bx, balbal, base_y + 2, rng.uniform(56, 72), (112, 80, 88), (214, 166, 128), seed + 20 + k, ink_a=0.95)
    _grass(sk, rng, 20, W - 20, base_y, D.GR, n=160, hmax=22, lean=0.45)
    L = Layer(W, Hh)
    L.a = sk.snap()
    return L, (W, Hh), (W / 2, base_y)


def anit_kaf(seed=4003):
    """Buz kulesi: dev buz kristali kümesi, önünde karlı kam direği ve kar tümseği."""
    from kaf_ink import crystal_cluster, shaman_pole, SNOW_LIT, SNOW_MID, SNOW_SH, ICE, ICE_D
    W, Hh = 440, 360
    sk = Sk(W, Hh)
    base_y = Hh - 8
    rng = np.random.default_rng(seed)
    # kar tümseği (arka)
    p = smooth_path([(20, base_y + 6), (60, base_y - 30), (160, base_y - 44), (300, base_y - 40), (400, base_y - 22), (420, base_y + 6)], True, 0.4)
    sk.path(p, SNOW_MID)
    sk.path(smooth_path([(60, base_y - 28), (160, base_y - 44), (300, base_y - 40), (250, base_y - 20), (120, base_y - 14)], True, 0.4), SNOW_LIT, 0.9)
    sk.path(p, INK, 0.8, 0, 2.0)
    crystal_cluster(sk, 220, base_y - 30, 300, seed, ink_a=1.0, ink_w=1.8)
    crystal_cluster(sk, 110, base_y - 10, 120, seed + 1, ink_a=1.0)
    crystal_cluster(sk, 340, base_y - 14, 140, seed + 2, ink_a=1.0)
    shaman_pole(sk, 60, base_y, 180, seed + 5, ink_a=1.0)
    L = Layer(W, Hh)
    L.a = sk.snap()
    # ışıma: kristal gövdelerinde soğuk mavi
    g = Sk(W, Hh)
    for cx, cy, r in ((220, base_y - 150, 90), (110, base_y - 60, 40), (340, base_y - 70, 46)):
        g.c.drawCircle(cx, cy, r, g.paint((120, 200, 255), 0.35, 30))
    G = Layer(W, Hh)
    G.a = g.snap() * (L.a[..., 3:4] > 0.5)
    return L, (W, Hh), (W / 2, base_y), G


def anit_sahmeran(seed=4004):
    """Yılan sütunu: kehribar gözlü, yılan kabartmalı taş sütun; dibinde kristal kümeleri (ışır)."""
    import sahmeran_ink_ortam as S
    import inkkit_yeralti as Y
    W, Hh = 360, 400
    base_y = Hh - 8
    L = Layer(W, Hh)
    old = S.H
    S.H = Hh
    try:
        S.snake_pillar(L, W / 2, base_y, 64, seed, np.zeros(1080, np.float32), cap_y=60)
    finally:
        S.H = old
    sk = Sk(W, Hh)
    rng = np.random.default_rng(seed)
    Y.crystal_cluster(sk, 70, base_y - 2, 46, seed + 1, body=S.EMER, hi=S.EMER_HI, dark=(14, 70, 70), ink_a=1.0)
    Y.crystal_cluster(sk, 300, base_y - 2, 38, seed + 2, body=S.AMETH, hi=S.AMETH_HI, dark=(60, 30, 90), ink_a=1.0)
    for _ in range(30):
        x = rng.uniform(20, W - 20)
        sk.path(blade(x, base_y + 4, rng.uniform(5, 14), rng.uniform(-0.4, 0.4), rng.uniform(1.5, 2.6)), (40, 90, 64) if rng.random() < 0.6 else (110, 190, 120), 0.9)
    L.over(sk.snap())
    g = Sk(W, Hh)
    g.c.drawCircle(70, base_y - 24, 40, g.paint((60, 255, 190), 0.45, 22))
    g.c.drawCircle(300, base_y - 20, 34, g.paint((190, 120, 255), 0.4, 20))
    g.c.drawCircle(W / 2, 70, 30, g.paint((255, 200, 90), 0.3, 18))
    G = Layer(W, Hh)
    G.a = g.snap() * (L.a[..., 3:4] > 0.5)
    return L, (W, Hh), (W / 2, base_y), G


def anit_tamu(seed=4005):
    """Kemik kapısı: dev kaburga kemeri, altında boynuzlu öküz kafatası, sarkan kancalı zincirler; göz çukurları kor."""
    import tamu_ink_ortam as T
    import inkkit_yeralti as Y
    W, Hh = 560, 380
    base_y = Hh - 8
    L = Layer(W, Hh)
    old = T.H
    T.H = Hh
    try:
        T.ribcage(L, W / 2 - 170, base_y, 340, 300, seed, np.zeros(1080, np.float32), dark_k=1.0, n=6, ink_k=1.0, width=20)
    finally:
        T.H = old
    sk = Sk(W, Hh)
    rng = np.random.default_rng(seed)
    T.ox_skull(sk, W / 2, base_y - 6, 0.78, ink_k=1.0)
    for k in range(4):
        x = rng.uniform(60, W - 60)
        ln = rng.uniform(60, 150)
        Y.chain(sk, (x, 0), (x + 0.5, ln), 0, link=9, col=T.IRON, hi=T.IRON_HI)
        hk = bezier((x, ln + 4), (x + 12, ln + 20), (x - 2, ln + 26), 10)
        sk.path(ribbon(hk, np.linspace(3.5, 1.3, 10)), T.IRON)
        sk.path(ribbon(hk, np.linspace(3.5, 1.3, 10)), INK, 1.0, 0, 1.0)
    # kül yığını ve kemik kırıntıları
    for _ in range(14):
        x = rng.uniform(40, W - 40)
        p = blob(x, base_y + 1, rng.uniform(6, 16), rng.uniform(3, 6), int(rng.integers(1 << 20)), n=8, jitter=0.2)
        sk.path(p, (46, 36, 40))
        sk.path(p, INK, 0.8, 0, 1.0)
    L.over(sk.snap())
    g = Sk(W, Hh)
    s = 0.78
    for side in (-1, 1):
        ex = W / 2 + side * 26 * s
        g.c.drawCircle(ex, base_y - 6 - 55 * s, 9, g.paint((255, 140, 50), 0.9, 5))
        g.c.drawCircle(ex, base_y - 6 - 55 * s, 26, g.paint((255, 90, 30), 0.35, 16))
    G = Layer(W, Hh)
    G.a = g.snap()
    return L, (W, Hh), (W / 2, base_y), G


ANIT = {'otuken': anit_otuken, 'bozkir': anit_bozkir, 'kaf': anit_kaf, 'sahmeran': anit_sahmeran, 'tamu': anit_tamu}


def export_anit(only=None):
    ik.K = E.WORLD_K * HD
    tex = 2.0 * ik.KB()
    for b, fn in ANIT.items():
        if only and b not in only:
            continue
        res = fn()
        L, origin = res[0], res[2]
        key = 'anit_%s_v2' % b
        E.save(E.to8(L.a), 'decor', key + '.png')
        h, w = L.a.shape[:2]
        meta = {"size": [int(w) // HD, int(h) // HD], "origin": [int(round(origin[0] * ik.KB())), int(round(origin[1] * ik.KB()))],
                "texel": tex, "noflip": b in ('bozkir', 'kaf')}
        if len(res) > 3:
            E.save(E.to8(res[3].a), 'decor', key + '_e.png')
            meta["glow"] = True
        # biyom süs tablosuna girdi (decor_v2_<biyom>.json; Ötüken ortak decor_v2.json)
        jp = os.path.join(A, 'decor', 'decor_v2.json' if b == 'otuken' else 'decor_v2_%s.json' % b)
        d = json.load(open(jp, encoding='utf-8')) if os.path.exists(jp) else {}
        d[key] = meta
        json.dump(d, open(jp, 'w', encoding='utf-8'), indent=1)


def main():
    args = sys.argv[1:]
    flags = [a for a in args if a.startswith('--')]
    rest = [a for a in args if not a.startswith('--')]
    every = not flags
    if every or '--hava' in flags:
        export_hava()
    if every or '--anit' in flags:
        export_anit(rest or None)


if __name__ == '__main__':
    main()
