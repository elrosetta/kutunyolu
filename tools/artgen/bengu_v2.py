"""Bengü — stil v2 (gerçekçi piksel; bkz. style_v2.py). v1 (bengu.py) olduğu gibi durur.

Değişenler:
  * Oranlar: ~7 baş boy. Bacak 12 + 11.8 (v1: 10.5 + 10.5), gövde 17 (v1: 14), kol 10 + 9.4 (v1: 8.5 + 8),
    kurt başı daha küçük ve anatomik (uzun burun, belirgin kaş, yanak yelesi, dik kulak).
  * Malzeme ayrımı: kırmızı yün kaftan (mat, geniş bant), çelik lamel zırh yeleği ve omuzluk (metal:
    gök/yer yansıması + keskin parlama), deri kemer/çizme/bilek siperi (dar orta ton + kısa parlama),
    altın kemer plakaları, ak kurt postu yaka (tutamlı), çivit şalvar.
  * Değer yapısı: 7 ton, yansıyan ışık, 2 piksel ay kenar ışığı (style_v2.VCanvas2).
  * Doku yoğunluğu 2x (v1: 1.5x): 960x540 görüntü 1080p'de 2x ölçeklendiği için her doku pikseli tam bir
    ekran pikseline oturur (en keskin durum).
Poz parametreleri v1 ile aynı (bengu.ANIMS hepsi çalışır); idle, run ve atk_down v2'ye özgü yeniden kurgulandı.
Çapalar (sh_f, hand_f, ...) dünya biriminde: Player.gd kol iskeleti aynen çalışır (bengu_v2_kol.json).
"""
import math
import numpy as np
from raster import Mat
import wolfkit as wk
import bengu as v1
from bengu import TexScale, P, keyed
from materials import M
from rig import fk_leg, fk_arm, lerp2, chain, Xf
from style_v2 import VCanvas2, M2, variant

TEX = 2.0
CELL = (192, 160)      # dünya 96 x 80
FEET = (88, 148)       # dünya (44, 74)
L_THIGH, L_SHIN = 12.0, 11.8
L_UP, L_FORE = 10.0, 9.4
HIP_Y = -23.6
TORSO = 17.0

# ------------------------------------------------------------ malzemeler (7 ton)
KAFTAN = M2('#a3262b', 'cloth', 'kırmızı yün kaftan')
KAFTAN_F = variant(KAFTAN, -1, 'kaftan kıvrımı')
KAFTAN_IN = M2('#5e1a24', 'cloth', 'kaftan gölge yüzü', spread=0.9)
LINING = M2('#3b1622', 'cloth', 'kaftan astarı', spread=0.8)
EMBR = M2('#d0a24c', 'metal', 'altın sırma')
EMBR.env = 0.25
EMBR_D = M2('#4a2416', 'cloth', 'sırma zemini')
PANTS = M2('#2f3552', 'cloth', 'çivit yün şalvar')
PANTS_D = M2('#232740', 'cloth', 'uzak şalvar', spread=0.9)
PANTS_F = variant(PANTS, -2, 'şalvar kıvrımı')
BOOT = M2('#5c3324', 'leather', 'çizme derisi')
BOOT_D = M2('#40261d', 'leather', 'uzak çizme')
BOOT_F = variant(BOOT, -2, 'çizme kırışığı')
SOLE = M2('#211a1a', 'leather', 'taban', spread=0.7)
STEEL = M2('#8f9aab', 'metal', 'çelik lamel', shadow_hue=232, light_hue=200, sat_light=0.0)
STEEL_HI = variant(STEEL, +1, 'lamel üst kenarı')
STEEL_DK = variant(STEEL, -3, 'lamel arası')
STEEL_GAP = variant(STEEL, -1, 'lamel dikey aralığı')
STEEL_D = M2('#5d6474', 'metal', 'uzak çelik', shadow_hue=232, light_hue=200)
LACE = M2('#5a2e1e', 'leather', 'lamel bağı')
BELT = M2('#3f2619', 'leather', 'kemer')
BELT_D = variant(BELT, -2, 'kemer kenarı')
GOLD = M2('#d9ad52', 'metal', 'altın plaka')
GOLD.env = 0.35
BRACER = M2('#4d2f22', 'leather', 'bilek siperi')
GLOVE = M2('#2c2422', 'leather', 'eldiven', spread=0.8)
SCARF = M2('#1c9a93', 'cloth', 'turkuaz atkı', light_hue=150)
SCARF_D = variant(SCARF, -2, 'atkı kıvrımı')
FUR = M2('#c3cad8', 'fur', 'ak kurt postu', shadow_hue=236, light_hue=50, spread=0.85, lift=1.2)
FUR_D = M2('#7a8398', 'fur', 'post gölgesi', shadow_hue=236, spread=0.85)
FUR_N = variant(FUR, -1, 'post alt katı')
EAR_IN = M2('#7d4d55', 'skin', 'kulak içi')
NOSE = M2('#262230', 'leather', 'burun')
NOSE.spec = 1.0
LIP = Mat([np.array([0.06, 0.04, 0.07])] * 7, flat=True, name='dudak çizgisi')
TOOTH = M2('#e8e0cc', 'skin', 'diş')
KUT = M['kut']
PAINT = M2('#c3202b', 'cloth', 'savaş boyası')
PAINT.vb = None
PAINT.flat = True
TASSEL = M2('#b0222b', 'cloth', 'püskül')


def _lamellar(rx, ry, rowh=4.4, pw=3.6, k=TEX, hi=STEEL_HI, dk=STEEL_DK, lace=LACE):
    """Lamel zırh deseni: sıralı, şaşırtmalı çelik plakalar; plaka üst kenarı açık, aralar koyu, bağ noktaları.
    Elipsin yerel (lu, lv) koordinatına bağlı: karelerde gövdeyle birlikte hareket eder, kaymaz."""
    rxt, ryt = rx * k, ry * k

    def co(lu, lv):
        x = lu * rxt
        y = lv * ryt + 100.0
        r = np.floor(y / rowh)
        yy = y - r * rowh
        cx = np.mod(x + (r % 2) * pw * 0.5 + 100.0, pw)
        return yy, cx

    top = lambda lu, lv, px, py: co(lu, lv)[0] < 1.0
    vgap = lambda lu, lv, px, py: co(lu, lv)[1] < 0.9
    gap = lambda lu, lv, px, py: co(lu, lv)[0] >= rowh - 1.0
    tie = lambda lu, lv, px, py: (np.abs(co(lu, lv)[0] - 1.6) < 0.55) & (np.abs(co(lu, lv)[1] - pw * 0.55) < 0.5)
    return [(top, hi), (vgap, STEEL_GAP), (gap, dk), (tie, lace)]


def _T(hip, axis, perp):
    def f(u, v):
        return (hip[0] + axis[0] * u + perp[0] * v, hip[1] + axis[1] * u + perp[1] * v)
    return f


def draw(c, p, front_arm=True, back_arm=True):
    bob, lean = p['bob'], p['lean']
    sk, pk, bp = p.get('sk', 0.0), p.get('pk', 0.0), p.get('bp', 0.0)
    br = p.get('br', 0.0)
    tw = p.get('tw', 0.0)
    hip = (p.get('hx', 0.0), HIP_Y + bob * 1.1)
    tl = TORSO + br * 0.3
    neck = (hip[0] + math.sin(lean) * tl, hip[1] - math.cos(lean) * tl)
    sx = p.get('sx', 0.0)
    sh_f = (neck[0] + 1.4 + sx + tw * 0.7, neck[1] + 3.2)
    sh_b = (neck[0] - 2.8 - sx * 0.5 - tw * 0.7, neck[1] + 3.0)
    head = (neck[0] + 1.6 + math.sin(lean) * 1.6 + p.get('hdx', 0.0), neck[1] - 4.6 + p.get('hdy', 0.0))
    out = {'sh_f': sh_f}
    nx_, ny_ = neck
    ax = (math.sin(lean), -math.cos(lean))
    pe = (math.cos(lean), math.sin(lean))
    T = _T(hip, ax, pe)

    # ------------------------------------------------ atkı: uzun, iki kuyruk (siluetin imzası)
    if pk <= 0:
        u_ = max(0.0, min(1.0, 1.0 + pk)) * 0.5
        a0, bend = math.pi * (0.95 - 0.12 * u_), -(0.03 + 0.10 * u_)
    else:
        r_ = min(1.0, pk / 1.1)
        a0, bend = math.pi * (0.89 + 0.17 * r_), -0.09 + 0.15 * r_
    dr = max(0.0, min(1.0, 1.0 - abs(pk) / 0.7))
    a0 = a0 + (math.pi * 0.62 - a0) * dr * 0.85
    bend = bend + (-0.05 - bend) * dr * 0.85
    root = (nx_ - 1.6, ny_ + 1.2)
    # kumaş: kol gibi okunmasın diye ince, boyunca belirgin burulan (geniş/dar) ve kuyruğa doğru daralan şerit
    for k, (n, seg, r0, z0, dph, da) in enumerate(((9, 3.1, 1.75, -14.0, 0.0, 0.0), (7, 2.9, 1.25, -14.6, 1.3, 0.2))):
        sc = chain(root, n, seg, a0 + da, bend * (1.0 + 0.5 * k), bp * 6.28 - 0.9 - dph, 0.75 + 0.15 * k)
        for i, (a, b) in enumerate(zip(sc, sc[1:])):
            tw_ = abs(math.cos(i * 1.3 + k * 0.7 + bp * 6.28 * 0.5))
            r = r0 * (1 - i / n * 0.5) * (0.35 + 0.65 * tw_)
            zz = (8.5 - i * 0.3) if (i < 2 and k == 0) else z0 + i * 0.1
            c.capsule(a, b, r, r * 0.9, (SCARF if tw_ > 0.5 else SCARF_D) if k == 0 else SCARF_D, z=zz)
        ex, ey = sc[-1]
        for j in range(4):
            c.capsule((ex, ey), (ex - 1.2 + j * 0.6, ey + 2.6 + j * 0.2), 0.42, 0.28, TASSEL, z=z0 + 1)
        c.ellipse((ex, ey), 1.0, 1.0, GOLD, z=z0 + 1.3)

    # ------------------------------------------------ arka kol
    e, h = fk_arm(sh_b, p['ab'][0], p['ab'][1], L_UP, L_FORE)
    if back_arm:
        c.ellipse(sh_b, 3.1, 3.0, STEEL_D, z=-12.5)
        c.capsule(sh_b, e, 2.6, 2.2, KAFTAN_IN, z=-12.8)
        c.capsule(e, h, 2.2, 1.9, KAFTAN_IN, z=-12.8)
        c.capsule(lerp2(e, h, 0.5), lerp2(e, h, 0.95), 2.3, 2.1, BOOT_D, z=-12.2)
        c.ellipse(h, 1.9, 2.0, GLOVE, z=-11.8)
    out['hand_b'] = h
    out['ang_b'] = p['ab'][0] + p['ab'][1]
    out['sh_b'] = sh_b
    out['arm_b'] = (p['ab'][0], p['ab'][1])

    # ------------------------------------------------ kaftan arka eteği (diz boyu; yarık arkada, astar görünür)
    bot = hip[1] + 14.0
    flap = sk * 2.4
    c.poly([(hip[0] - 6.0, hip[1] - 1.0), (hip[0] - 0.5, hip[1] - 1.0), (hip[0] - 1.8 + flap * 0.6, bot + 0.4),
            (hip[0] - 9.0 + flap * 1.6, bot - 0.8)], LINING, z=-11, bevel=1.8, height=1.6,
           paint=[(lambda lu, lv, px, py: py > (bot - 1.6) * TEX, EMBR_D)])

    def leg(base, a, z, near):
        k, f = fk_leg(base, a[0], a[1], L_THIGH, L_SHIN)
        pm = PANTS if near else PANTS_D
        bm = BOOT if near else BOOT_D
        fold = lambda lu, lv, px, py: (np.floor(lu * 6.0 + lv * 1.4) % 3 == 0) & (lv > -0.1) & (lu > 0.25)
        c.capsule(base, k, 4.0, 3.0, pm, z=z, paint=[(fold, PANTS_F)] if near else None)
        c.ellipse(k, 2.9, 2.8, pm, z=z + 0.2)
        c.capsule(k, lerp2(k, f, 0.4), 3.0, 2.6, pm, z=z + 0.1)
        # uzun çizme: konç dizin hemen altına kadar, kırışıklı bilek, kalın taban, hafif kalkık burun
        wr = lambda lu, lv, px, py: (np.abs(lu - 0.72) < 0.05) | (np.abs(lu - 0.82) < 0.035)
        top = lambda lu, lv, px, py: lu < 0.09
        c.capsule(lerp2(k, f, 0.3), f, 3.0, 2.3, bm, z=z + 1.2,
                  paint=[(top, BELT_D), (wr, BOOT_F)] if near else [(top, BELT_D)])
        toe = (f[0] + 4.6, f[1] - 0.7)
        c.capsule(f, (f[0] + 3.4, f[1] + 0.1), 2.3, 1.6, bm, z=z + 0.6)
        c.capsule((f[0] + 3.0, f[1] - 0.1), toe, 1.25, 0.65, bm, z=z + 0.7)
        c.capsule((f[0] - 1.8, f[1] + 1.9), (f[0] + 3.9, f[1] + 1.5), 0.8, 0.6, SOLE, z=z + 0.8)
        c.capsule((f[0] - 2.0, f[1] + 0.7), (f[0] - 1.8, f[1] + 1.8), 1.0, 1.0, SOLE, z=z + 0.85)
        if near:   # çelik dizlik
            kk = lerp2(k, f, 0.06)
            c.ellipse((kk[0] + 1.2, kk[1]), 2.3, 2.5, STEEL, z=z + 4.0, rot=a[0] * 0.5)
            c.capsule((kk[0] + 0.4, kk[1] + 2.2), (kk[0] + 1.4, kk[1] + 4.6), 1.4, 1.0, STEEL, z=z + 3.8)
        return k, f

    leg(hip, p['lb'], -10, False)

    # ------------------------------------------------ gövde: kaftan
    c.ellipse(sh_b, 3.2, 3.0, KAFTAN_IN, z=-0.6)
    c.ellipse(T(11.0, -2.2 - tw * 0.3), 5.2, 7.6 + br * 0.15, KAFTAN, z=0, rot=lean)            # sırt
    c.ellipse(T(4.8, 0.2), 5.6, 5.4, KAFTAN, z=0.4, rot=lean)                                   # karın
    c.ellipse(T(11.2 + br * 0.1, 1.6 + br * 0.25), 5.8 + br * 0.2, 6.8 + br * 0.2, KAFTAN, z=1.0, rot=lean)  # göğüs
    # lamel yelek (göğüs + karın), deri kenar bandı
    lam1 = _lamellar(5.2, 6.4)
    c.ellipse(T(11.0, 1.8), 5.2, 6.4, STEEL, z=3.2, rot=lean, paint=lam1)
    lam2 = _lamellar(5.0, 4.6)
    c.ellipse(T(5.4, 1.0), 5.0, 4.6, STEEL, z=3.0, rot=lean, paint=lam2)
    edge = [T(15.8, 3.0), T(12.0, 5.6), T(7.0, 5.8), T(2.8, 5.4)]
    for a, b in zip(edge, edge[1:]):
        c.capsule(a, b, 0.75, 0.75, BELT, z=7.0)

    # ------------------------------------------------ etek ön parçası (diz boyu, kıvrımlı), altın sırma bandı
    hem = lambda lu, lv, px, py: py > (bot - 1.8) * TEX
    hem_pat = lambda lu, lv, px, py: (py > (bot - 1.5) * TEX) & (py < (bot - 0.5) * TEX) & (np.floor(px / 2.0) % 3 == 0)
    fold = lambda lu, lv, px, py: (np.floor(px / TEX - hip[0] + 0.45 * (py / TEX - hip[1]) * (sk * 0.3 - 0.2) + 40) % 5 == 0) & (py > (hip[1] + 2.0) * TEX) & (py < (bot - 1.8) * TEX)
    c.poly([(hip[0] - 7.0, hip[1] - 1.8), (hip[0] + 6.6, hip[1] - 1.8), (hip[0] + 8.4 + sk * 2.0, bot), (hip[0] + 1.0 + sk * 2.4, bot + 0.7),
            (hip[0] - 8.6 + sk * 2.8, bot - 0.6)], KAFTAN, z=2, bevel=3.6, height=2.2,
           paint=[(fold, KAFTAN_F), (hem, EMBR), (hem_pat, EMBR_D)])
    # pliler: belden etek ucuna genişleyen kumaş silindirleri; her biri kendi ışık/gölgesini alır (yün kıvrımı)
    for j, (u0, u1, r0, r1) in enumerate(((-5.6, -8.0, 1.5, 2.3), (-2.4, -3.6, 1.6, 2.4), (0.8, 0.9, 1.6, 2.5), (4.0, 5.6, 1.5, 2.4))):
        top_ = (hip[0] + u0, hip[1] + 0.6)
        bt_ = (hip[0] + u1 * 0.85 + sk * (1.8 + 0.3 * j), bot - 3.4 - 0.3 * ((j * 7) % 3))
        c.capsule(top_, bt_, r0 * 0.9, r1 * 0.85, KAFTAN, z=3.0 + 0.15 * j)

    # ------------------------------------------------ kemer: geniş deri, altın plakalar, sarkan kayışlar
    def band(u0, w, r, mat, z, sag=0.8):
        pts = [T(u0 - sag * math.cos(math.pi * 0.5 * v / w) ** 2, v) for v in np.linspace(-w, w, 7)]
        for a, b in zip(pts, pts[1:]):
            c.capsule(a, b, r, r, mat, z=z)
        return pts
    bp_ = band(1.2, 6.4, 1.5, BELT, 5.0)
    for i, q in enumerate(bp_[1:-1]):
        c.ellipse(q, 0.95, 1.1, GOLD, z=7.4, rot=lean)
    c.ellipse(T(1.0, 5.2), 1.4, 1.6, GOLD, z=8.2, rot=lean)                    # toka
    for dv, ln in ((2.8, 6.0), (4.4, 4.6)):                                     # sarkan kayışlar
        a = T(0.6, dv)
        b = (a[0] + sk * 0.8 + 0.4, a[1] + ln)
        c.capsule(a, b, 0.6, 0.5, BELT, z=8.4)
        c.ellipse(b, 0.7, 0.8, GOLD, z=8.6)
    pc = T(-0.6, -4.6)
    c.ellipse(pc, 1.7, 2.2, BELT, z=6.0, rot=lean)
    c.ellipse((pc[0] + 0.1, pc[1] - 1.1), 1.8, 0.9, BOOT, z=6.4, rot=lean)

    # ------------------------------------------------ ön bacak
    k, f = leg((hip[0] + 1, hip[1]), p['lf'], 6, True)
    out['foot_f'] = f

    # ------------------------------------------------ ak kurt postu yaka (omuzları saran pelerin)
    c.ellipse((nx_ - 0.4, ny_ + 1.4), 6.4, 3.6, FUR, z=9, rot=lean * 0.6)
    wk.tufts(c, [(nx_ - 5.4, ny_ + 1.6), (nx_ - 3.8, ny_ + 3.6), (nx_ - 1.6, ny_ + 4.4), (nx_ + 0.8, ny_ + 4.4), (nx_ + 3.0, ny_ + 3.6)],
             FUR, 9.3, 3.0, math.pi * 0.56, jitter=0.35)
    wk.tufts(c, [(nx_ - 5.6, ny_ - 0.2), (nx_ - 6.2, ny_ + 1.6)], FUR_N, 9.1, 2.6, math.pi * 0.85, jitter=0.3)

    # ------------------------------------------------ kurt başı (daha küçük, anatomik)
    hx_, hy_ = head
    jaw = p.get('jaw', 0.0)
    c.capsule((nx_ - 0.6, ny_ + 0.4), (hx_ - 1.0, hy_ + 1.4), 3.0, 2.8, FUR, z=9.6)       # boyun
    c.ellipse((hx_ - 0.6, hy_), 3.9, 3.6, FUR, z=10)                                      # kafatası
    c.ellipse((hx_ + 0.6, hy_ - 1.4), 2.8, 2.0, FUR, z=11.2)                              # alın
    wk.tufts(c, [(hx_ - 2.2, hy_ + 2.4), (hx_ - 3.4, hy_ + 0.8), (hx_ - 0.6, hy_ + 3.0)], FUR_N, 10.6, 2.6, math.pi * 0.7, jitter=0.3)
    c.ellipse((hx_ + 0.8, hy_ + 1.4), 2.4, 2.0, FUR, z=10.8)                              # yanak
    c.capsule((hx_ + 1.4, hy_ + 0.6), (hx_ + 8.0, hy_ + 1.7), 2.3, 1.35, FUR, z=11)      # burun
    c.capsule((hx_ + 2.6, hy_ - 0.4), (hx_ + 7.6, hy_ + 0.7), 0.9, 0.6, FUR, z=13.2)     # burun sırtı
    c.capsule((hx_ + 1.8, hy_ + 2.8), (hx_ + 6.8, hy_ + 3.0 + jaw * 2.2), 1.25, 0.8, FUR_D, z=10.5)  # alt çene
    c.ellipse((hx_ + 8.3, hy_ + 1.3), 1.15, 0.95, NOSE, z=15)
    c.capsule((hx_ + 4.0, hy_ + 2.5), (hx_ + 7.2, hy_ + 2.5 + jaw * 1.0), 0.28, 0.28, LIP, z=12.5)
    if jaw > 0.3:
        for tx in (4.2, 5.8):
            c.dot((hx_ + tx, hy_ + 2.8), TOOTH, z=14, size=1)
    ear = p.get('ear', 0.0) + max(0.0, lean - 0.1) * 0.7 + math.sin(bp * 6.28 - 1.4) * 0.05
    for (ox, mat, zz, ln, near) in ((-2.6, FUR_D, 13.0, 5.6, False), (-0.4, FUR, 16.0, 6.0, True)):
        b0 = (hx_ + ox - 1.9, hy_ - 2.3)
        b1 = (hx_ + ox + 1.9, hy_ - 3.3)
        a = -math.pi * 0.5 - 0.28 - ear
        tip = (hx_ + ox + math.cos(a) * ln, hy_ - 3.2 + math.sin(a) * ln)
        c.poly([(b0[0] - 0.4, b0[1] + 0.3), b1, (tip[0] - 0.4, tip[1] + 0.3)], FUR_D, z=zz - 0.6, bevel=0.9, height=1.2)
        c.poly([b0, b1, tip], mat, z=zz, bevel=0.9, height=1.4)
        if near:
            c.poly([lerp2(b0, b1, 0.28), lerp2(b0, b1, 0.82), lerp2(lerp2(b0, b1, 0.5), tip, 0.75)], EAR_IN, z=zz + 2.5, bevel=0.6, height=0.4)
    c.capsule((hx_ + 0.6, hy_ - 1.9), (hx_ + 3.8, hy_ - 1.4), 0.7, 0.5, FUR, z=15.5)      # kaş
    c.ellipse((hx_ + 2.4, hy_ - 0.4), 1.5, 1.1, FUR_D, z=13.5)                            # göz yuvası
    c.capsule((hx_ + 1.8, hy_ - 0.6), (hx_ + 3.2, hy_ - 0.85), 0.42, 0.36, KUT, z=30)    # kut gözü
    c.capsule((hx_ + 0.2, hy_ + 1.2), (hx_ + 2.2, hy_ + 1.7), 0.36, 0.36, PAINT, z=14)
    c.capsule((hx_ + 0.6, hy_ + 2.2), (hx_ + 2.4, hy_ + 2.6), 0.3, 0.3, PAINT, z=14)
    out['head'] = head
    # atkı düğümü
    c.capsule((nx_ - 1.4, ny_ + 0.6), (nx_ + 2.4, ny_ + 1.8), 1.7, 1.7, SCARF, z=14.6)
    c.ellipse((nx_ + 2.0, ny_ + 1.6), 1.9, 1.6, SCARF, z=15)
    c.capsule((nx_ + 2.4, ny_ + 2.4), (nx_ + 3.2 + sk * 0.4, ny_ + 5.4), 1.0, 0.7, SCARF_D, z=15.2)

    # ------------------------------------------------ ön kol
    a1, a2 = p['af']
    e, h = fk_arm(sh_f, a1, a2, L_UP, L_FORE * p.get('ext', 1.0))
    if front_arm:
        _front_arm(c, sh_f, e, h, z=16.5)
    out['hand_f'] = h
    out['ang_f'] = a1 + a2
    out['arm'] = (a1, a2)
    return out


def _front_arm(c, sh, e, h, z=16.5):
    """Lamel omuzluk, kırmızı yen, deri bilek siperi (çelik şeritli), eldivenli yumruk."""
    c.capsule(sh, e, 2.7, 2.3, KAFTAN, z=z + 0.5, paint=[(lambda lu, lv, px, py: (np.floor(lu * 5.0) % 2 == 1) & (lv > 0.4), KAFTAN_F)])
    c.ellipse(e, 2.2, 2.2, KAFTAN, z=z + 0.6)
    c.capsule(e, h, 2.3, 2.0, KAFTAN, z=z + 0.5)
    c.capsule(lerp2(e, h, 0.45), lerp2(e, h, 0.94), 2.45, 2.25, BRACER, z=z + 1.5,
              paint=[(lambda lu, lv, px, py: (np.abs(lv) < 0.22), STEEL), (lambda lu, lv, px, py: (lu < 0.07) | (lu > 0.93), BELT_D)])
    c.ellipse(h, 2.0, 2.1, GLOVE, z=z + 2.5)
    # omuzluk: üç sıra lamel, kolun üstüne biner
    c.ellipse((sh[0] + 0.2, sh[1] + 0.8), 3.5, 3.6, STEEL, z=z + 2.0, paint=_lamellar(3.5, 3.6, rowh=3.8))


# ------------------------------------------------------------ kol parçaları (oyunda sürülür, 2x yoğunluk)
ARM_CELL = (24, 30)       # doku pikseli (dünya 12 x 15)
ARM_PIVOT = (12, 6)


class ArmCanvas(VCanvas2):
    def shade(self, **kw):
        kw.setdefault('light', (-0.85, -0.15, 0.5))
        kw.setdefault('grad', 0.0)
        kw.setdefault('form', 0.3)
        kw.setdefault('rim', (1.0, 0.0))
        kw.setdefault('rim_w', 1)
        return super().shade(**kw)


def render_arm_parts():
    parts = []
    seam = lambda lu, lv, px, py: (np.floor(lu * 5.0) % 2 == 1) & (lv > 0.4)
    for (mat, fold, back) in ((KAFTAN, KAFTAN_F, False), (KAFTAN_IN, LINING, True)):
        c = ArmCanvas(ARM_CELL[0], ARM_CELL[1], ARM_PIVOT[0], ARM_PIVOT[1]); c.zscale = TEX
        s = TexScale(c, TEX)
        s.capsule((0, 0), (0, L_UP), 2.7 - back * 0.2, 2.3 - back * 0.2, mat, z=0, paint=[(seam, fold)])
        if not back:
            s.ellipse((0, 0.6), 3.4, 3.4, STEEL, z=2.0, paint=_lamellar(3.4, 3.4, rowh=3.8))
        else:
            s.ellipse((0, 0.6), 3.0, 3.0, STEEL_D, z=1.0)
        parts.append(c)
        c = ArmCanvas(ARM_CELL[0], ARM_CELL[1], ARM_PIVOT[0], ARM_PIVOT[1]); c.zscale = TEX
        s = TexScale(c, TEX)
        s.capsule((0, 0), (0, L_FORE), 2.3 - back * 0.2, 2.0 - back * 0.1, mat, z=0)
        s.capsule((0, L_FORE * 0.45), (0, L_FORE * 0.94), 2.45, 2.25, BRACER if not back else BOOT_D, z=1,
                  paint=[(lambda lu, lv, px, py: (np.abs(lv) < 0.22), STEEL if not back else STEEL_D),
                         (lambda lu, lv, px, py: (lu < 0.07) | (lu > 0.93), BELT_D)])
        parts.append(c)
        c = ArmCanvas(ARM_CELL[0], ARM_CELL[1], ARM_PIVOT[0], ARM_PIVOT[1] + 3); c.zscale = TEX
        s = TexScale(c, TEX)
        s.ellipse((0, 0), 2.2 - back * 0.2, 2.2 - back * 0.2, GLOVE, z=0)
        if not back:
            for i in range(3):
                s.ellipse((-1.0 + i * 1.0, -0.9), 0.6, 0.5, BOOT, z=2.4)
        parts.append(c)
    return parts


# ------------------------------------------------------------ v2 pozları
def _idle(t):
    s = math.sin(t * 6.28)
    # gerçekçi savaşçı duruşu: ağırlık arka bacakta (hafif kontrapost), ön ayak açık, dizler yumuşak;
    # nefesle göğüs/omuz kalkar; baş, etek ve atkı gecikmeli izler
    return P(bob=-0.1 + 0.35 * s, lean=0.06 + 0.02 * s, lf=(0.30, 0.42), lb=(-0.24, 0.14),
             af=(0.10 + 0.04 * s, 0.55 + 0.06 * s), ab=(-0.18 - 0.03 * s, 0.45 + 0.05 * s),
             sk=0.2 * math.sin(t * 6.28 - 0.6), pk=0.3 * s, bp=t, jaw=0.0, br=s, hdy=0.3 * math.sin(t * 6.28 - 0.8),
             sx=0.2)


def _run(t):
    ph = t * 6.28

    def legp(q):
        th = 0.86 * math.sin(q) + 0.06
        sw = max(0.0, math.cos(q))          # salınım evresi (bacak öne gelirken)
        st = max(0.0, -math.cos(q))         # basış evresi
        kn = 0.18 + 1.65 * sw ** 1.4 + 0.32 * st ** 2
        return (th, kn)
    # iki iniş (ph = 0, pi) arası uçuş evresi; gövde basışta çöker, itişte yükselir
    bob = 1.3 * math.cos(2 * ph) - 0.4
    return P(bob=bob, lean=0.26 + 0.03 * math.cos(2 * ph), lf=legp(ph), lb=legp(ph + math.pi),
             af=(-0.85 * math.sin(ph) + 0.15, 1.55 - 0.25 * math.sin(ph)), ab=(0.85 * math.sin(ph) + 0.1, 1.5 + 0.25 * math.sin(ph)),
             sk=-0.8 + 0.3 * math.sin(2 * ph - 1.2), pk=-1.0, bp=t * 2, tw=0.7 * math.sin(ph),
             hdy=0.4 * math.sin(2 * ph - 0.9), sx=0.3)


# Saldırı (yukarıdan aşağı kesiş) v2: daha derin hazırlık (sırt kavisi, ağırlık geride), patlayıcı ileri adım,
# darbede kalça ve omuz tam burulur, gövde öne çöker; aşma ve toparlanmada atkı/etek gecikmeli savrulur.
ATK_DOWN = keyed((0.0, P(lean=-0.18, ab=(0.7, 0.5), lf=(0.35, 0.45), lb=(-0.35, 0.25), sx=-1.2, bob=0.6, sk=0.45, pk=0.35, tw=-0.4)),
                 (0.25, P(lean=-0.34, ab=(0.95, 0.55), lf=(0.30, 0.5), lb=(-0.42, 0.35), sx=-2.2, bob=1.6, sk=0.6, pk=0.5, hdy=-0.6, tw=-0.9, hx=-0.8)),
                 (0.4, P(lean=0.34, ab=(-0.7, 0.7), lf=(0.75, 0.75), lb=(-0.6, 0.15), sx=1.8, bob=0.6, sk=-0.6, pk=-0.4, hx=3.0, jaw=0.6, tw=0.6)),
                 (0.55, P(lean=0.56, ab=(-1.15, 0.8), lf=(0.85, 0.85), lb=(-0.72, 0.12), sx=2.8, bob=2.2, sk=-0.95, pk=-0.8, hx=4.6, jaw=0.9, tw=1.0)),
                 (0.78, P(lean=0.42, ab=(-0.7, 0.7), lf=(0.7, 0.7), lb=(-0.6, 0.2), sx=1.6, bob=1.6, sk=-0.5, pk=-0.3, hx=4.0, tw=0.5)),
                 (1.0, P(lean=0.16, ab=(-0.2, 0.6), lf=(0.45, 0.45), lb=(-0.38, 0.22), sx=0.5, bob=0.4, sk=-0.1, hx=2.0)))

ANIMS = dict(v1.ANIMS)
ANIMS['idle'] = (8, _idle, True, True)
ANIMS['run'] = (8, _run, True, True)
ANIMS['atk_down'] = (8, ATK_DOWN, False, False)
V2_ANIMS = ('idle', 'run', 'atk_down')   # v2'ye özgü kurgulanan animasyonlar (diğerleri v1 pozlarıyla v2 çizimi)

SHADE = dict(light=(-0.72, -0.58, 0.38), form=0.5, grad=0.34, rim_amt=0.38, rim_w=2, rim_th=0.5, lit_outline=0.0)


def render_frame(anim, i, cell=CELL, feet=FEET):
    n, fn, loop, arm = ANIMS[anim]
    t = (i / n) if loop else (min(0.999, i / n + 0.5 / n) if n > 1 else 0.0)
    p = fn(t)
    c = VCanvas2(cell[0], cell[1], feet[0], feet[1])
    c.zscale = TEX
    s = TexScale(c, TEX)
    if 'roll' in p:
        ang = p['roll'] * math.tau
        xf = Xf(s, 0, -19, ang, pivot=(0, -23))
        info = draw(xf, p, True)
    else:
        info = draw(s, p, arm, arm)
    rgba = c.shade(**SHADE)
    nm = c.normal_map(rgba[..., 3])
    return c, rgba, nm, info
