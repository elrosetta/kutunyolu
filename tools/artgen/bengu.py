"""Kahraman: BENGÜ — kurt başlı alp (insansı gövde, kurt kafası).

Okunaklılık için sade siluet: büyük kurt başı (kulaklar, uzun burun, kut ışığı göz), kısa kırmızı kaftan,
deri kemer, koyu şalvar, çizme ve arkada dalgalanan tek bir turkuaz atkı. Ayrıntı azaltıldı;
renk blokları büyük ve net (Dead Cells'in "uzaktan da okunan" karakter ilkesi).

Ön kol iki biçimde kullanılır:
  * hareket animasyonlarında (idle, koşu, zıplama...) sprite'a çizilir;
  * silah gösteren animasyonlarda (saldırı, yay, fırlatma, kalkan) ÇİZİLMEZ: oyun kolu üç parça
    (üst kol, ön kol, yumruk) olarak omuz çapasından 60 FPS sürer; silah her zaman yumruğun içindedir.
Koordinatlar: ayak merkezi (0,0), y aşağı pozitif, yüz sağa. Kol açıları: 0 aşağı, pi/2 ileri, pi yukarı.
"""
import math
import numpy as np
from raster import Canvas, Mat, ramp, hx
import wolfkit as wk
from volume import VCanvas
from materials import M
from rig import fk_leg, fk_arm, lerp2, chain, Xf

# ------------------------------------------------------------ v13: 1.5x doku yoğunluğu
# Bengü 1.5 kat piksel yoğunluğunda çizilir (yeni karolar/arka planlar gibi): oyunda 2/3 ölçekle gösterilir,
# dünya boyutu aynı kalır, her doku pikseli 1080p'de 2x2 ekran pikseli olur. Çizim kodu DÜNYA birimindedir;
# TexScale sarmalayıcısı koordinat, yarıçap, eğim ve z'yi TEX ile çarpar. Çapalar (el, omuz, baş) dünya
# biriminde kalır: oyun kodu (Player.gd kol iskeleti) aynen çalışır.
TEX = 1.5
CELL = (144, 120)      # = (96, 80) * 1.5
FEET = (66, 111)       # = (44, 74) * 1.5


class TexScale:
    """Dünya biriminde çizimi doku pikseline ölçekler (orijin: ayak merkezi / pivot)."""
    def __init__(self, c, k=TEX):
        self.c, self.k = c, k

    def P(self, p):
        return (p[0] * self.k, p[1] * self.k)

    def capsule(self, p0, p1, r0, r1, mat, z=0.0, **kw):
        self.c.capsule(self.P(p0), self.P(p1), r0 * self.k, r1 * self.k, mat, z=z * self.k, **kw)

    def ellipse(self, c_, rx, ry, mat, z=0.0, **kw):
        self.c.ellipse(self.P(c_), rx * self.k, ry * self.k, mat, z=z * self.k, **kw)

    def poly(self, pts, mat, z=0.0, bevel=1.6, height=1.5, **kw):
        self.c.poly([self.P(q) for q in pts], mat, z=z * self.k, bevel=bevel * self.k, height=height * self.k, **kw)

    def dot(self, p, mat, z=50.0, size=1):
        self.c.dot(self.P(p), mat, z=z * self.k, size=size)


# ------------------------------------------------------------ malzemeler
BOOT = Mat(ramp(22, 0.50, 0.36, spread=0.45), name='kızıl-kahve çizme')
BOOT_D = Mat(ramp(20, 0.50, 0.24, spread=0.4), name='uzak çizme')
CUFF = Mat(ramp(30, 0.48, 0.52, spread=0.45), name='çizme konçu')
SOLE = Mat(ramp(250, 0.25, 0.13, spread=0.3), name='taban')
TUNIC = M['kaftan']
TUNIC_IN = M['kaftan_in']
LINING = Mat(ramp(340, 0.62, 0.30, spread=0.35), name='kaftan astarı (koyu)')
PANTS = M['indigo']
PANTS_D = Mat(ramp(238, 0.50, 0.28), name='uzak şalvar')
SCARF = M['turq']
SCARF_D = Mat(ramp(178, 0.74, 0.50), name='turkuaz kıvrım')
SASH = Mat(ramp(186, 0.62, 0.38, spread=0.45), name='koyu turkuaz kuşak')
LEATHER = M['leather']
LEATHER_D = Mat(ramp(18, 0.55, 0.30, spread=0.4), name='koyu deri')
GOLD = M['gold']
# ak kurt postu — gölgeleri soğuk arduvaz mavisine iner (beyaz post hacimli okunsun)
FUR = Mat([hx('#56647f'), hx('#8e9cb4'), hx('#c8d1df'), hx('#eaeff5'), hx('#ffffff')], name='ak kurt postu')
FUR_D = Mat([hx('#353c55'), hx('#56607c'), hx('#8590a8'), hx('#aab4c6'), hx('#cdd5e1')], name='kurt postu gölgesi')
EAR_IN = Mat(ramp(350, 0.35, 0.55, spread=0.4), name='kulak içi')
NOSE = Mat(ramp(250, 0.35, 0.16, spread=0.3), spec=0.9, name='burun')
FUR.fur = 0.8
FUR.bias = -0.12
FUR_D.fur = 0.6
for _m in (PANTS, PANTS_D):
    _m.fur = 0.25   # şalvar kumaşının hafif dokusu (aynı mekanizma, düşük genlik)


def _T(hip, axis, perp):
    """Gövde yerel koordinatı: u gövde ekseni boyunca (kalçadan yukarı), v öne."""
    def f(u, v):
        return (hip[0] + axis[0] * u + perp[0] * v, hip[1] + axis[1] * u + perp[1] * v)
    return f


def draw_bengu(c, p, front_arm=True, back_arm=True):
    bob, lean = p['bob'], p['lean']
    sk, pk, bp = p.get('sk', 0.0), p.get('pk', 0.0), p.get('bp', 0.0)
    br = p.get('br', 0.0)          # nefes (göğüs/omuz)
    tw = p.get('tw', 0.0)          # koşuda gövde burulması: arka omuz ileri-geri
    hip = (p.get('hx', 0.0), -20 + bob)
    neck = (hip[0] + math.sin(lean) * (14 + br * 0.35), hip[1] - math.cos(lean) * (14 + br * 0.35))
    sx = p.get('sx', 0.0)
    sh_f = (neck[0] + 1.5 + sx + tw * 0.6, neck[1] + 2.4)
    sh_b = (neck[0] - 2.2 - sx * 0.5 - tw * 0.6, neck[1] + 2.2)
    head = (neck[0] + 1.8 + math.sin(lean) * 1.5 + p.get('hdx', 0.0), neck[1] - 6.2 + p.get('hdy', 0.0))
    out = {'sh_f': sh_f}
    nx_, ny_ = neck
    ax = (math.sin(lean), -math.cos(lean))
    pe = (math.cos(lean), math.sin(lean))
    T = _T(hip, ax, pe)

    # ------------------------------------------------ atkı kuyrukları (kumaş: incelir, kıvrımları koyu/açık)
    if pk <= 0:
        u_ = max(0.0, min(1.0, 1.0 + pk)) * 0.5
        a0, bend = math.pi * (0.95 - 0.12 * u_), -(0.03 + 0.12 * u_)
    else:
        r_ = min(1.0, pk / 1.1)
        a0, bend = math.pi * (0.89 + 0.17 * r_), -0.09 + 0.15 * r_
    # hareketsizken (|pk| küçük) atkı sırttan aşağı sarkar; hız arttıkça yataya açılır
    dr = max(0.0, min(1.0, 1.0 - abs(pk) / 0.7))
    a0 = a0 + (math.pi * 0.66 - a0) * dr * 0.85
    bend = bend + (-0.07 - bend) * dr * 0.85
    root = (nx_ - 1.8, ny_ + 0.9)
    for k, (n, seg, r0, z0, dph, da) in enumerate(((7, 3.1, 2.7, -14.0, 0.0, 0.0),)):
        sc = chain(root, n, seg, a0 + da, bend * (1.0 + 0.4 * k), bp * 6.28 - 0.9 - dph, 0.45 + 0.1 * k)
        # kumaş şerit: boyunca burulur — geniş (yüzü dönük, açık) / dar (kenarı dönük, koyu) dönüşümlü
        for i, (a, b) in enumerate(zip(sc, sc[1:])):
            tw_ = abs(math.cos(i * 1.15 + bp * 6.28 * 0.5))
            r = r0 * (1 - i / n * 0.45) * (0.55 + 0.45 * tw_)
            c.capsule(a, b, r, r * 0.92, SCARF if tw_ > 0.5 else SCARF_D, z=(8.5 - i * 0.3) if (i < 2 and k == 0) else z0 + i * 0.1)
        ex, ey = sc[-1]
        if k == 0:
            for j in range(3):   # kırmızı püskül
                c.capsule((ex, ey), (ex - 1.6 + j * 0.5, ey + 2.2 + j * 0.3), 0.45, 0.3, M['red_paint'], z=z0 + 1)
            c.ellipse((ex, ey), 1.2, 1.3, M['red_paint'], z=z0 + 1.2)

    # ------------------------------------------------ arka kol (gövdenin arkasında, koyu astar rengi)
    e, h = fk_arm(sh_b, p['ab'][0], p['ab'][1])
    if back_arm:
        c.capsule(sh_b, e, 2.7, 2.3, TUNIC_IN, z=-12)
        c.capsule(e, h, 2.3, 2.0, TUNIC_IN, z=-12)
        c.capsule(lerp2(e, h, 0.66), lerp2(e, h, 0.95), 2.4, 2.4, LEATHER_D, z=-11.5)
        c.ellipse(h, 2.0, 2.0, FUR_D, z=-11)
    out['hand_b'] = h
    out['ang_b'] = p['ab'][0] + p['ab'][1]
    out['sh_b'] = sh_b
    out['arm_b'] = (p['ab'][0], p['ab'][1])

    # ------------------------------------------------ kaftan arka eteği (astar görünür), arka bacak
    bot = hip[1] + 10.2
    flap = sk * 1.8
    c.poly([(hip[0] - 5.6, hip[1] - 1.0), (hip[0] - 1.0, hip[1] - 1.0), (hip[0] - 2.0 + flap * 0.6, bot + 0.4), (hip[0] - 8.0 + flap * 1.5, bot - 0.6)],
           LINING, z=-11, bevel=1.6, height=1.5)

    def leg(base, a, z, near):
        k, f = fk_leg(base, a[0], a[1])
        pm = PANTS if near else PANTS_D
        bm = BOOT if near else BOOT_D
        fold = lambda lu, lv, px, py: (np.floor(lu * 5.0 + lv * 1.2) % 3 == 0) & (lv > -0.2)
        # bol şalvar: uyluk kalın, dizde kırışık, baldır çizmeye girer
        c.capsule(base, k, 4.2, 3.3, pm, z=z, paint=[(fold, PANTS_D if near else LINING)])
        c.ellipse(k, 3.1, 3.0, pm, z=z + 0.2)
        c.capsule(k, lerp2(k, f, 0.52), 3.2, 2.6, pm, z=z + 0.1)
        # çizme: konç (ağız bandı), saya, taban, kalkık burun
        cuff_p = [(lambda lu, lv, px, py: lu < 0.035, GOLD), (lambda lu, lv, px, py: lu < 0.2, CUFF), (lambda lu, lv, px, py: lu < 0.25, LEATHER_D)] if near else [(lambda lu, lv, px, py: lu < 0.2, BOOT)]
        c.capsule(lerp2(k, f, 0.46), f, 3.4, 2.6, bm, z=z + 1.2, paint=cuff_p)
        toe = (f[0] + 4.4, f[1] - 0.9)
        c.capsule(f, (f[0] + 3.4, f[1] - 0.2), 2.4, 1.6, bm, z=z + 0.6)
        c.capsule((f[0] + 3.0, f[1] - 0.3), toe, 1.3, 0.7, bm, z=z + 0.7)   # Türk çizmesi: kalkık uç
        c.capsule((f[0] - 1.6, f[1] + 1.7), (f[0] + 3.6, f[1] + 1.3), 0.75, 0.6, SOLE, z=z + 0.8)
        c.capsule((f[0] - 1.8, f[1] + 0.6), (f[0] - 1.6, f[1] + 1.6), 1.0, 1.0, SOLE, z=z + 0.85)  # topuk
        return k, f

    leg(hip, p['lb'], -10, False)

    # ------------------------------------------------ gövde: fıçı göğüs + sırt kütlesi + karın (kaftan)
    collar = lambda lu, lv, px, py: np.zeros_like(px, bool)
    c.ellipse(sh_b, 3.0, 2.8, TUNIC_IN, z=-0.6)                                             # uzak omuz (arkada)
    c.ellipse(T(9.4, -2.0 - tw * 0.3), 5.6, 6.6 + br * 0.15, TUNIC, z=0, rot=lean)          # sırt / kürek
    c.ellipse(T(4.2, 0.2), 6.1, 5.2, TUNIC, z=0.4, rot=lean)                                # karın
    c.ellipse(T(9.0 + br * 0.1, 1.8 + br * 0.25), 6.1 + br * 0.2, 6.2 + br * 0.2, TUNIC, z=1.0, rot=lean)  # göğüs
    # sağ (ön) yaka: kaftanın sarma ağzı — altın şerit + altında astar kalınlığı
    lap = [T(13.4, 2.4), T(10.0, 4.2), T(6.0, 5.0), T(2.6, 5.4)]
    for a, b in zip(lap, lap[1:]):
        c.capsule((a[0] - 0.5, a[1] + 0.3), (b[0] - 0.5, b[1] + 0.3), 0.55, 0.55, LINING, z=6.2)
        c.capsule(a, b, 0.5, 0.5, GOLD, z=6.6)
    # dik yaka
    c.capsule(T(13.4, -3.2), T(14.0, 2.6), 1.5, 1.4, TUNIC, z=5.5)
    c.capsule(T(14.4, -3.0), T(14.9, 2.6), 0.5, 0.5, GOLD, z=6.0)

    # ------------------------------------------------ etek: ana etek (kıvrımlı), altın etek bandı
    hem = lambda lu, lv, px, py: py > bot - 1.3
    fold = lambda lu, lv, px, py: (np.floor(px - hip[0] + 0.5 * (py - hip[1]) * (sk * 0.3) + 40) % 5 == 0) & (py > hip[1] + 1.5) & (py < bot - 1.3)
    fx0, fx1 = hip[0] + 6.6, hip[0] + 7.6 + sk * 1.6
    fedge = lambda lu, lv, px, py: px > fx0 - 0.5 + (fx1 - fx0) * np.clip((py - hip[1] + 1.6) / (bot - hip[1] + 1.6), 0, 1)
    c.poly([(hip[0] - 6.9, hip[1] - 1.6), (hip[0] + 7.0, hip[1] - 1.6), (hip[0] + 8.2 + sk * 1.6, bot), (hip[0] + 1.0 + sk * 2.0, bot + 0.6),
            (hip[0] - 8.0 + sk * 2.4, bot - 0.5)], TUNIC, z=2, bevel=3.4, height=2, paint=[(hem, GOLD), (fold, TUNIC_IN)])

    # ------------------------------------------------ kuşak + kemer + toka + kese
    # 3/4 görünüş: yatay bantlar (kuşak, kemer) gövdenin fıçı biçimini izleyerek ortada aşağı kavislenir
    def band(u0, w, r, mat, z, sag=0.7):
        pts = [T(u0 - sag * math.cos(math.pi * 0.5 * v / w) ** 2, v) for v in np.linspace(-w, w, 6)]
        for a, b in zip(pts, pts[1:]):
            c.capsule(a, b, r, r, mat, z=z)
    band(0.6, 6.7, 1.6, SASH, 3.8)
    band(2.3, 6.7, 1.05, LEATHER, 4.4)
    c.ellipse(T(2.0, 4.6), 1.35, 1.55, GOLD, z=5.6, rot=lean)
    c.ellipse(T(2.0, 4.6), 0.55, 0.75, LEATHER_D, z=6.4, rot=lean)
    pc = T(-0.6, -4.2)
    c.ellipse(pc, 1.6, 2.0, LEATHER_D, z=5.0, rot=lean)                # kese
    c.ellipse((pc[0] + 0.1, pc[1] - 1.0), 1.7, 0.9, LEATHER, z=5.4, rot=lean)   # kapak
    c.dot((pc[0] + 0.2, pc[1] - 0.4), GOLD, z=8.0, size=1)

    # ------------------------------------------------ ön bacak, ön etek kanadı (bacağın üstüne biner)
    k, f = leg((hip[0] + 1, hip[1]), p['lf'], 6, True)
    out['foot_f'] = f

    # ------------------------------------------------ kurt başı
    hx_, hy_ = head
    jaw = p.get('jaw', 0.0)
    # boyun yelesi: yakanın üstüne, omuzlara taşan tüy öbekleri
    c.ellipse((nx_ - 0.6, ny_ - 1.0), 5.6, 4.0, FUR, z=9, rot=lean * 0.6)
    wk.tufts(c, [(nx_ - 4.8, ny_ - 0.2), (nx_ - 3.4, ny_ + 1.6), (nx_ - 1.0, ny_ + 2.5), (nx_ + 1.4, ny_ + 2.2)], FUR, 9.3, 2.9,
             math.pi * 0.62, jitter=0.35)
    wk.tufts(c, [(nx_ - 4.2, ny_ - 2.6), (nx_ - 5.4, ny_ - 0.8)], FUR, 9.2, 2.7, math.pi * 0.95, jitter=0.3)
    # kafatası + alın
    c.ellipse((hx_ - 0.7, hy_), 5.1, 4.8, FUR, z=10)
    c.ellipse((hx_ + 0.6, hy_ - 1.8), 3.6, 2.6, FUR, z=11.2)
    # yanak tüyü (ruff): başın arkasından aşağı sarkan öbekler
    wk.tufts(c, [(hx_ - 2.6, hy_ + 2.7), (hx_ - 4.1, hy_ + 1.0), (hx_ - 0.6, hy_ + 3.5)], FUR, 10.6, 2.9, math.pi * 0.68, jitter=0.3)
    c.ellipse((hx_ + 0.6, hy_ + 1.8), 3.0, 2.4, FUR, z=10.8)                  # yanak / burun kökü
    # burun: üst düzlem (ışık alır) + yan düzlem; alt çene ayrı ve koyu
    c.capsule((hx_ + 1.5, hy_ + 0.7), (hx_ + 10.0, hy_ + 1.6), 2.9, 1.8, FUR, z=11)
    c.capsule((hx_ + 3.0, hy_ - 0.5), (hx_ + 9.3, hy_ + 0.5), 1.1, 0.8, FUR, z=13.4)   # burun sırtı
    c.capsule((hx_ + 2.0, hy_ + 3.4), (hx_ + 8.4, hy_ + 3.7 + jaw * 2.5), 1.5, 1.0, FUR_D, z=10.5)
    c.ellipse((hx_ + 10.3, hy_ + 1.1), 1.45, 1.2, NOSE, z=15)
    c.capsule((hx_ + 5.0, hy_ + 3.0), (hx_ + 8.6, hy_ + 2.9 + jaw * 1.2), 0.3, 0.3, M['black'], z=12.5)  # dudak
    if jaw > 0.3:
        for tx in (4.5, 6.5):
            c.dot((hx_ + tx, hy_ + 3.3), M['bone'], z=14, size=2)
    # kulaklar: kalın (arka kenar koyu), geniş tabanlı, hafif geriye yatık; koşuda/darbede geriye yatar (gecikmeli)
    ear = p.get('ear', 0.0) + max(0.0, lean - 0.1) * 0.7 + math.sin(bp * 6.28 - 1.4) * 0.05
    for (ox, mat, zz, ln, near) in ((-3.2, FUR_D, 13.0, 6.8, False), (-0.2, FUR, 16.0, 7.4, True)):
        b0 = (hx_ + ox - 2.4, hy_ - 2.8)
        b1 = (hx_ + ox + 2.4, hy_ - 4.0)
        a = -math.pi * 0.5 - 0.32 - ear
        tip = (hx_ + ox + math.cos(a) * ln, hy_ - 3.8 + math.sin(a) * ln)
        c.poly([(b0[0] - 0.5, b0[1] + 0.3), b1, (tip[0] - 0.5, tip[1] + 0.3)], FUR_D, z=zz - 0.6, bevel=1.0, height=1.2)  # arka kenar
        c.poly([b0, b1, tip], mat, z=zz, bevel=1.0, height=1.4)
        if near:
            c.poly([lerp2(b0, b1, 0.25), lerp2(b0, b1, 0.85), lerp2(lerp2(b0, b1, 0.5), tip, 0.78)], EAR_IN, z=zz + 2.5, bevel=0.6, height=0.4)
    # kaş çıkıntısı + göz yuvası gölgesi, kut ışığı göz (yarık), savaş boyası
    c.capsule((hx_ + 0.7, hy_ - 2.3), (hx_ + 4.5, hy_ - 1.6), 0.85, 0.6, FUR, z=15.5)
    c.ellipse((hx_ + 3.0, hy_ - 0.5), 1.8, 1.3, FUR_D, z=13.5)
    c.capsule((hx_ + 2.2, hy_ - 0.8), (hx_ + 3.8, hy_ - 1.1), 0.5, 0.42, M['kut'], z=30)
    c.capsule((hx_ + 0.4, hy_ + 1.4), (hx_ + 2.6, hy_ + 2.0), 0.45, 0.45, M['red_paint'], z=14)
    c.capsule((hx_ + 0.9, hy_ + 2.5), (hx_ + 2.8, hy_ + 3.0), 0.35, 0.35, M['red_paint'], z=14)
    out['head'] = head
    # atkı düğümü (önde, boynu saran hacimli düğüm)
    c.capsule((nx_ - 1.6, ny_ + 0.2), (nx_ + 2.6, ny_ + 1.4), 1.9, 1.9, SCARF, z=14.6)
    c.ellipse((nx_ + 2.2, ny_ + 1.2), 2.2, 1.8, SCARF, z=15)
    c.capsule((nx_ + 2.6, ny_ + 2.0), (nx_ + 3.6 + sk * 0.4, ny_ + 4.8), 1.2, 0.8, SCARF_D, z=15.2)

    # ------------------------------------------------ ön kol (yalnızca hareket animasyonlarında)
    a1, a2 = p['af']
    e, h = fk_arm(sh_f, a1, a2, 8.5, 8.0 * p.get('ext', 1.0))
    if front_arm:
        _front_arm(c, sh_f, e, h, z=16.5)
    out['hand_f'] = h
    out['ang_f'] = a1 + a2
    out['arm'] = (a1, a2)
    return out


def _front_arm(c, sh, e, h, z=16.5, mat=None, cuff=None, fist=None):
    """Ön kol: omuz kütlesi + altın dikiş halkası, kıvrımlı yen, deri bilek siperi + altın bant, pençe yumruk."""
    mat = mat or TUNIC
    c.ellipse(sh, 3.7, 3.4, mat, z=z)
    c.capsule(sh, e, 3.1, 2.6, mat, z=z + 0.5, paint=[(lambda lu, lv, px, py: (np.floor(lu * 4.0) % 2 == 1) & (lv > 0.35), TUNIC_IN)])
    c.ellipse(e, 2.5, 2.5, mat, z=z + 0.6)
    c.capsule(e, h, 2.6, 2.2, mat, z=z + 0.5)
    c.capsule(lerp2(e, h, 0.62), lerp2(e, h, 0.95), 2.65, 2.55, cuff or LEATHER, z=z + 1.5,
              paint=[(lambda lu, lv, px, py: (lu > 0.08) & (lu < 0.2), GOLD)])
    c.ellipse(h, 2.2, 2.2, fist or FUR_D, z=z + 2.5)


# ------------------------------------------------------------ kol parçaları (oyunda sürülür, 1.5x yoğunluk)
ARM_CELL = (18, 24)      # doku pikseli (dünya: 12 x 16)
ARM_PIVOT = (9, 5)       # doku pikseli
UPPER_LEN = 8.5          # dünya birimi (Player.gd geometri için kullanır)
FORE_LEN = 8.0


class ArmCanvas(VCanvas):
    """Oyunda döndürülen kol parçaları: ışık yandan (dönünce de silindir gibi okunur), dikey gradyan yok."""
    def shade(self, **kw):
        kw.setdefault('light', (-0.85, -0.15, 0.5))
        kw.setdefault('grad', 0.0)
        kw.setdefault('form', 0.3)
        kw.setdefault('rim', (1.0, 0.0))
        return super().shade(**kw)


def render_arm_parts():
    """Üst kol, ön kol (bilezikli) ve yumruk: aşağıyı gösteren (0,0) pivotlu küçük sprite'lar (1.5x).
    Sonra arka kol için koyu astar renginde aynı üçlü."""
    parts = []
    seam = lambda lu, lv, px, py: (np.floor(lu * 4.0) % 2 == 1) & (lv > 0.35)
    for (mat, cuff, fist, back) in ((TUNIC, LEATHER, FUR_D, False), (TUNIC_IN, LEATHER_D, FUR_D, True)):
        c = ArmCanvas(ARM_CELL[0], ARM_CELL[1], ARM_PIVOT[0], ARM_PIVOT[1]); c.zscale = TEX
        s = TexScale(c)
        s.capsule((0, 0), (0, UPPER_LEN), 2.9 - back * 0.2, 2.4 - back * 0.2, mat, z=0, paint=[(seam, TUNIC_IN if not back else LINING)])
        s.ellipse((0, 0.6), 3.1 - back * 0.2, 2.9 - back * 0.2, mat, z=0.5)
        parts.append(c)
        c = ArmCanvas(ARM_CELL[0], ARM_CELL[1], ARM_PIVOT[0], ARM_PIVOT[1]); c.zscale = TEX
        s = TexScale(c)
        s.capsule((0, 0), (0, FORE_LEN), 2.4 - back * 0.2, 2.0 - back * 0.1, mat, z=0)
        s.capsule((0, FORE_LEN * 0.62), (0, FORE_LEN * 0.95), 2.55, 2.5, cuff, z=1,
                  paint=[(lambda lu, lv, px, py: (lu > 0.08) & (lu < 0.2), GOLD if not back else LEATHER_D)])
        parts.append(c)
        c = ArmCanvas(ARM_CELL[0], ARM_CELL[1], ARM_PIVOT[0], ARM_PIVOT[1] + 3); c.zscale = TEX
        s = TexScale(c)
        s.ellipse((0, 0), 2.3 - back * 0.2, 2.3 - back * 0.2, fist, z=0)
        if not back:
            for i in range(3):   # parmak boğumları
                s.ellipse((-1.1 + i * 1.1, -0.9), 0.65, 0.55, FUR, z=2.4)
        parts.append(c)
    return parts


# ------------------------------------------------------------ pozlar
def P(**kw):
    d = dict(bob=0.0, lean=0.05, lb=(0.15, 0.12), lf=(-0.12, 0.08), ab=(0.2, 0.45), af=(-0.1, 0.55), sk=0.0, pk=0.0, bp=0.0, hx=0.0, sx=0.0, ext=1.0)
    d.update(kw)
    return d


def _lerp_pose(a, b, t):
    out = {}
    for k, va in a.items():
        vb = b.get(k, va)
        if isinstance(va, tuple):
            out[k] = tuple(x + (y - x) * t for x, y in zip(va, vb))
        else:
            out[k] = va + (vb - va) * t
    return out


def keyed(*keys):
    """Anahtar kareler arasında smoothstep geçiş."""
    def fn(t):
        for (t0, p0), (t1, p1) in zip(keys, keys[1:]):
            if t <= t1:
                u = 0.0 if t1 == t0 else max(0.0, min(1.0, (t - t0) / (t1 - t0)))
                u = u * u * (3 - 2 * u)
                return _lerp_pose(p0, p1, u)
        return keys[-1][1]
    return fn


def _run(t):
    s = math.sin(t * 6.28)
    ph = t * 6.28
    # gövde burulması (omuzlar kalçaya karşı), baş ve etek gecikmeli; atkı fazı bp ile akar
    return P(bob=-abs(math.sin(t * 6.28)) * 2.4 + 1.2, lean=0.28, lb=(0.95 * s, 0.3 + 0.95 * max(0, -s) + 0.15),
             lf=(-0.95 * s, 0.3 + 0.95 * max(0, s) + 0.15), ab=(-0.95 * s, 1.1), af=(0.95 * s, 1.1),
             sk=-0.7 + 0.25 * math.sin(2 * ph - 1.2), pk=-1.0, bp=t * 2, tw=0.8 * s, hdy=0.5 * math.sin(2 * ph - 0.9))


def _idle(t):
    s = math.sin(t * 6.28)
    # savaşçı duruşu: yakın bacak önde, uzak bacak geride (3/4 derinlik); nefesle göğüs/omuz kalkar,
    # baş ve etek nefesin ardından gecikmeli oynar
    return P(bob=-0.3 + 0.45 * s, lean=0.08 + 0.02 * s, lf=(0.25, 0.35), lb=(-0.25, 0.05),
             af=(0.02 + 0.05 * s, 0.7 + 0.08 * s), ab=(-0.12 - 0.04 * s, 0.55 + 0.06 * s),
             sk=0.25 * math.sin(t * 6.28 - 0.6), pk=0.35 * s, bp=t, jaw=0.0, br=s, hdy=0.35 * math.sin(t * 6.28 - 0.8))


# Saldırı gövdeleri (kolsuz): 8 kare. 0-1 hazırlık, 2-4 vuruş (3 = darbe), 5 aşma, 6-7 toparlanma.
# Kol ve silahın kendisi oyunda (Player.SWINGS) aynı zaman çizelgesiyle sürülür.
def _atk(*keys):
    return (8, keyed(*keys), False, False)


ANIMS = {
    # ad: (kare sayısı, poz fonksiyonu, döngü mü, ön kol çizilsin mi)
    'idle': (8, _idle, True, True),
    'run': (8, _run, True, True),
    'jump': (3, keyed((0.0, P(bob=-0.5, lean=0.05, lb=(0.5, 1.2), lf=(-0.2, 0.4), ab=(-0.6, 0.6), af=(1.0, 0.5), sk=-0.6, pk=-0.8)),
                      (1.0, P(bob=-1.5, lean=0.12, lb=(0.8, 1.5), lf=(-0.35, 0.55), ab=(-1.0, 0.7), af=(1.5, 0.45), sk=-0.9, pk=-1.1))), False, True),
    'fall': (3, keyed((0.0, P(bob=-0.5, lean=0.0, lb=(0.5, 0.6), lf=(-0.3, 0.6), ab=(1.3, 0.3), af=(1.6, 0.3), sk=0.5, pk=0.6)),
                      (1.0, P(bob=0.5, lean=-0.08, lb=(0.3, 0.3), lf=(-0.45, 0.8), ab=(1.9, 0.3), af=(2.2, 0.2), sk=1.0, pk=1.1))), False, True),
    'land': (2, keyed((0.0, P(bob=3.0, lean=0.18, lb=(-0.5, 0.9), lf=(0.55, 1.0), ab=(0.5, 0.7), af=(0.7, 0.7), sk=0.3, pk=0.4)),
                      (1.0, P(bob=1.2, lean=0.1, lb=(-0.2, 0.4), lf=(0.2, 0.4), ab=(0.3, 0.5), af=(0.2, 0.6)))), False, True),
    'roll': (8, lambda t: P(bob=8, lean=0.9, lb=(2.1, 2.9), lf=(1.9, 2.8), ab=(1.6, 2.0), af=(1.4, 2.2), sk=0.4, pk=-0.6, bp=t, roll=t), False, True),
    'hurt': (3, keyed((0.0, P(lean=-0.35, af=(-1.0, 0.7), ab=(-1.2, 0.5), bob=0.5, lf=(-0.3, 0.3), lb=(0.4, 0.2), sk=0.9, pk=1.1, jaw=0.8)),
                      (1.0, P(lean=-0.2, af=(-0.6, 0.6), ab=(-0.8, 0.5), bob=1.5, lf=(-0.1, 0.3), lb=(0.2, 0.2), sk=0.6, pk=0.8, jaw=0.3))), False, True),
    'drink': (2, lambda t: P(lean=-0.1, af=(2.6 + 0.2 * t, 1.6), ab=(0.3, 0.4)), False, True),
    # çömelme: dizler kırık, gövde alçak; silahlı sürümde kollar iskeletle sürülür
    'crouch': (2, lambda t: P(bob=9.0 + 0.4 * t, lean=0.22, lb=(0.9, 1.9), lf=(-0.7, 1.9), ab=(0.3, 0.6), af=(-0.2, 0.7), sk=0.5, pk=0.4, hdy=1.0), True, True),
    'crouch_atk': (1, lambda t: P(bob=9.0, lean=0.3, lb=(0.9, 1.9), lf=(-0.7, 1.9), ab=(0.5, 0.6), sx=-1.0, sk=0.4, pk=0.3, hdy=1.0), False, False),
    'sprint': (8, lambda t: P(bob=-abs(math.sin(t * 6.28)) * 3.0 + 1.0, lean=0.5, lb=(1.2 * math.sin(t * 6.28), 0.3 + 1.1 * max(0, -math.sin(t * 6.28)) + 0.2),
                              lf=(-1.2 * math.sin(t * 6.28), 0.3 + 1.1 * max(0, math.sin(t * 6.28)) + 0.2), ab=(-1.3 * math.sin(t * 6.28), 1.3), af=(1.3 * math.sin(t * 6.28), 1.3), sk=-1.1, pk=-1.4, bp=t * 2.5), True, True),
    # --- kolsuz gövdeler (silahlı)
    'atk_down': _atk((0.0, P(lean=-0.15, ab=(0.6, 0.5), lf=(0.3, 0.4), lb=(-0.3, 0.2), sx=-1.0, bob=0.5, sk=0.4, pk=0.3)),
                     (0.25, P(lean=-0.28, ab=(0.8, 0.5), lf=(0.3, 0.4), lb=(-0.3, 0.25), sx=-1.8, bob=1.2, sk=0.5, pk=0.4, hdy=-0.5)),
                     (0.4, P(lean=0.3, ab=(-0.6, 0.7), lf=(0.6, 0.6), lb=(-0.5, 0.2), sx=1.5, bob=0.2, sk=-0.5, hx=2.5, jaw=0.6)),
                     (0.55, P(lean=0.48, ab=(-1.0, 0.8), lf=(0.7, 0.65), lb=(-0.6, 0.2), sx=2.4, bob=1.4, sk=-0.75, hx=3.8, jaw=0.8)),
                     (1.0, P(lean=0.18, ab=(-0.2, 0.6), lf=(0.45, 0.45), lb=(-0.35, 0.2), sx=0.5, bob=0.3, sk=-0.2, hx=1.5))),
    'atk_up': _atk((0.0, P(lean=0.2, ab=(-0.3, 0.5), lf=(0.5, 0.6), lb=(-0.5, 0.3), sx=-1.0, bob=2.0, sk=-0.2)),
                   (0.25, P(lean=0.26, ab=(-0.4, 0.5), lf=(0.55, 0.75), lb=(-0.55, 0.4), sx=-1.5, bob=3.0, sk=-0.1)),
                   (0.4, P(lean=0.1, ab=(0.3, 0.6), lf=(0.45, 0.4), lb=(-0.45, 0.3), sx=1.2, bob=0.0, sk=-0.4, hx=1.5, jaw=0.6)),
                   (0.55, P(lean=-0.12, ab=(0.9, 0.6), lf=(0.6, 0.6), lb=(-0.3, 0.5), sx=2.0, bob=-2.0, sk=-0.6, pk=-0.4, hx=2.5, jaw=0.8, hdy=-0.6)),
                   (1.0, P(lean=0.0, ab=(0.3, 0.5), lf=(0.4, 0.4), lb=(-0.3, 0.3), sx=0.4, bob=-0.5, sk=-0.2, hx=1.8))),
    'atk_horiz': _atk((0.0, P(lean=0.1, ab=(0.9, 0.4), lf=(0.4, 0.45), lb=(-0.4, 0.2), sx=-2.0, bob=0.8, sk=0.2)),
                      (0.25, P(lean=0.04, ab=(1.2, 0.4), lf=(0.4, 0.5), lb=(-0.45, 0.25), sx=-3.0, bob=1.2, sk=0.4, pk=0.3)),
                      (0.4, P(lean=0.3, ab=(-0.2, 0.6), lf=(0.65, 0.6), lb=(-0.55, 0.2), sx=1.0, bob=0.5, sk=-0.4, hx=2.0, jaw=0.6)),
                      (0.55, P(lean=0.36, ab=(-1.1, 0.7), lf=(0.7, 0.6), lb=(-0.6, 0.2), sx=3.0, bob=0.8, sk=-0.7, pk=-0.5, hx=3.4, jaw=0.8)),
                      (1.0, P(lean=0.15, ab=(-0.3, 0.5), lf=(0.45, 0.45), lb=(-0.4, 0.2), sx=0.8, bob=0.4, sk=-0.2, hx=1.8))),
    'atk_thrust': _atk((0.0, P(lean=-0.12, ab=(0.4, 0.6), lf=(0.2, 0.3), lb=(-0.2, 0.2), sx=-2.0, sk=0.2, hx=-1.0)),
                       (0.25, P(lean=-0.18, ab=(0.5, 0.6), lf=(0.15, 0.3), lb=(-0.2, 0.25), sx=-2.6, sk=0.3, hx=-1.5, bob=0.8)),
                       (0.4, P(lean=0.3, ab=(-0.6, 0.6), lf=(0.75, 0.6), lb=(-0.65, 0.2), sx=2.0, sk=-0.6, hx=3.0, jaw=0.6)),
                       (0.55, P(lean=0.42, ab=(-0.9, 0.6), lf=(0.9, 0.6), lb=(-0.75, 0.2), sx=3.2, sk=-0.8, hx=4.6, jaw=0.8)),
                       (1.0, P(lean=0.15, ab=(-0.1, 0.6), lf=(0.4, 0.4), lb=(-0.35, 0.2), sx=0.5, sk=-0.2, hx=2.0))),
    'atk_heavy': _atk((0.0, P(lean=-0.2, ab=(-2.4, 1.2), lf=(0.3, 0.4), lb=(-0.3, 0.3), sx=-1.0, bob=1.5, sk=0.5, pk=0.4)),
                      (0.25, P(lean=-0.32, ab=(-2.9, 1.4), lf=(0.35, 0.45), lb=(-0.35, 0.3), sx=-1.5, bob=2.6, sk=0.6, pk=0.5, hdy=-0.8)),
                      (0.4, P(lean=0.2, ab=(-1.4, 0.6), lf=(0.6, 0.7), lb=(-0.5, 0.35), sx=1.0, bob=-2.0, sk=-0.2, hx=2.0, jaw=0.7)),
                      (0.55, P(lean=0.62, ab=(1.0, 0.2), lf=(0.9, 1.0), lb=(-0.7, 0.3), sx=2.5, bob=3.2, sk=-0.75, hx=4.2, jaw=1.0)),
                      (1.0, P(lean=0.3, ab=(0.5, 0.5), lf=(0.5, 0.6), lb=(-0.4, 0.3), sx=0.5, bob=0.8, sk=-0.2, hx=2.0))),
    'atk_spin': _atk((0.0, P(lean=0.1, ab=(-0.6, 0.6), lf=(0.4, 0.5), lb=(-0.4, 0.2), sx=-1.0, bob=0.5)),
                     (0.25, P(lean=-0.1, ab=(-0.8, 0.6), lf=(0.35, 0.5), lb=(-0.4, 0.25), sx=-1.5, bob=1.2, sk=0.3)),
                     (0.4, P(lean=0.1, ab=(0.2, 0.4), lf=(0.6, 0.6), lb=(-0.6, 0.3), sx=1.5, bob=-1.8, pk=-0.6, sk=-0.6, jaw=0.6)),
                     (0.55, P(lean=-0.12, ab=(0.9, 0.4), lf=(0.5, 0.6), lb=(-0.5, 0.3), sx=-1.0, bob=-2.2, pk=0.6, sk=0.4, jaw=0.8)),
                     (0.75, P(lean=0.08, ab=(0.2, 0.5), lf=(0.4, 0.45), lb=(-0.4, 0.2), sx=1.0, bob=0.8, pk=0.3, sk=0.2)),
                     (1.0, P(lean=0.05, ab=(0.1, 0.5), lf=(0.3, 0.4), lb=(-0.3, 0.2), sx=0.0, bob=0.3))),
    'atk_lunge': _atk((0.0, P(lean=-0.15, ab=(0.4, 0.6), lf=(0.2, 0.3), lb=(-0.3, 0.2), sx=-2.0, sk=0.3)),
                      (0.25, P(lean=-0.22, ab=(0.5, 0.6), lf=(0.15, 0.3), lb=(-0.3, 0.25), sx=-2.5, sk=0.4, hx=-1.0, bob=0.6)),
                      (0.4, P(lean=0.5, ab=(-0.8, 0.4), lf=(0.9, 0.5), lb=(-0.8, 0.2), sx=2.5, sk=-0.8, pk=-0.7, hx=4.0, bob=1.0, jaw=0.6)),
                      (0.55, P(lean=0.6, ab=(-1.0, 0.4), lf=(1.05, 0.5), lb=(-0.95, 0.2), sx=3.5, sk=-1.0, pk=-0.9, hx=5.5, bob=1.5, jaw=1.0)),
                      (1.0, P(lean=0.3, ab=(-0.3, 0.5), lf=(0.5, 0.5), lb=(-0.5, 0.2), sx=0.8, sk=-0.4, hx=3.0, bob=0.5))),
    # --- v15: arketipe özgü gövdeler. Kalça/omuz/eğilim işi yapar; ön kol oyunda sürülür (sh_f çapası tutarlı).
    # iki elli baş üstü: silah tepeye kaldırılır (sırt kavisi), adımla iner, darbede dizler bükülür
    'atk_overhead_2h': _atk((0.0, P(lean=-0.2, ab=(-2.6, 1.3), lf=(0.2, 0.3), lb=(-0.3, 0.3), sx=-1.2, bob=1.0, hdy=-0.3)),
                            (0.3, P(lean=-0.42, ab=(-3.0, 1.5), lf=(0.1, 0.35), lb=(-0.4, 0.3), sx=-2.0, bob=2.2, sk=0.6, pk=0.5, hdy=-1.0)),
                            (0.45, P(lean=0.25, ab=(-1.2, 0.5), lf=(0.8, 0.6), lb=(-0.6, 0.2), sx=1.5, bob=-1.0, hx=3.0, jaw=0.7)),
                            (0.6, P(lean=0.7, ab=(1.1, 0.2), lf=(0.75, 1.6), lb=(-0.6, 1.0), sx=2.8, bob=6.5, hx=5.0, sk=-0.8, pk=-0.6, jaw=1.0, hdy=0.5)),
                            (0.78, P(lean=0.55, ab=(0.9, 0.3), lf=(0.7, 1.3), lb=(-0.6, 0.8), sx=2.2, bob=5.0, hx=4.5, sk=-0.4, pk=-0.3)),
                            (1.0, P(lean=0.25, ab=(0.4, 0.5), lf=(0.5, 0.6), lb=(-0.45, 0.3), sx=0.6, bob=1.0, hx=2.5))),
    # geri sıçrayış: öne yüklen, geriye hopla, havada kes, çömelerek in (yatağan çekilme kesiği)
    'atk_backstep': _atk((0.0, P(lean=0.15, ab=(0.6, 0.5), lf=(0.5, 0.5), lb=(-0.3, 0.2), sx=0.5, bob=1.0)),
                         (0.25, P(lean=0.3, ab=(0.9, 0.5), lf=(0.6, 0.7), lb=(-0.5, 0.3), sx=1.5, bob=2.6, hx=1.0, sk=-0.3)),
                         (0.42, P(lean=-0.15, ab=(-0.3, 0.8), lf=(0.9, 1.4), lb=(0.3, 1.2), sx=-0.5, bob=-5.0, hx=-3.0, sk=0.9, pk=1.0, jaw=0.6, hdy=-0.4)),
                         (0.58, P(lean=-0.3, ab=(-0.8, 0.6), lf=(1.1, 1.3), lb=(0.5, 1.0), sx=-1.5, bob=-4.0, hx=-5.5, sk=1.1, pk=1.2, jaw=0.8)),
                         (0.78, P(lean=-0.1, ab=(-0.3, 0.6), lf=(0.3, 0.9), lb=(-0.2, 0.8), sx=-0.5, bob=2.5, hx=-6.0, sk=0.6, pk=0.7)),
                         (1.0, P(lean=0.05, ab=(0.2, 0.5), lf=(0.25, 0.4), lb=(-0.25, 0.2), sx=0.0, bob=0.5, hx=-5.0))),
    # alçak süpürme: derin çömelme, bıçak yer hizasında
    'atk_sweep_low': _atk((0.0, P(lean=0.1, ab=(0.8, 0.5), lf=(0.3, 0.5), lb=(-0.3, 0.3), sx=-1.5, bob=2.0)),
                          (0.25, P(lean=-0.05, ab=(1.3, 0.5), lf=(0.5, 1.5), lb=(-0.5, 1.3), sx=-3.0, bob=7.5, sk=0.5, pk=0.3, hdy=0.6)),
                          (0.42, P(lean=0.35, ab=(-0.3, 0.6), lf=(0.9, 2.0), lb=(-0.8, 1.6), sx=1.5, bob=10.0, hx=1.5, sk=-0.5, jaw=0.6, hdy=1.0)),
                          (0.58, P(lean=0.45, ab=(-1.0, 0.7), lf=(1.0, 2.0), lb=(-0.9, 1.6), sx=3.0, bob=10.0, hx=2.5, sk=-0.8, pk=-0.5, jaw=0.8, hdy=1.0)),
                          (0.78, P(lean=0.3, ab=(-0.5, 0.6), lf=(0.6, 1.4), lb=(-0.6, 1.1), sx=1.5, bob=6.0, hx=2.0, sk=-0.3)),
                          (1.0, P(lean=0.1, ab=(0.1, 0.5), lf=(0.3, 0.5), lb=(-0.3, 0.3), sx=0.3, bob=1.5, hx=1.5))),
    # aparkat: çömelmeden yükseliş, ayaklar yerden kesilir (havaya atar)
    'atk_uppercut': _atk((0.0, P(lean=0.25, ab=(0.3, 0.6), lf=(0.4, 0.9), lb=(-0.4, 0.6), sx=-1.0, bob=4.0)),
                         (0.25, P(lean=0.4, ab=(0.6, 0.8), lf=(0.6, 1.8), lb=(-0.7, 1.5), sx=-2.0, bob=9.0, sk=0.4, pk=0.3, hdy=0.8)),
                         (0.42, P(lean=0.0, ab=(-0.5, 0.6), lf=(0.5, 0.6), lb=(-0.6, 0.5), sx=1.0, bob=-1.0, hx=1.5, sk=-0.5, jaw=0.6)),
                         (0.58, P(lean=-0.3, ab=(-1.4, 0.6), lf=(0.6, 1.2), lb=(-0.2, 0.9), sx=2.0, bob=-7.0, hx=2.5, sk=-0.9, pk=-0.8, jaw=1.0, hdy=-0.8)),
                         (0.78, P(lean=-0.15, ab=(-0.8, 0.6), lf=(0.4, 0.7), lb=(-0.3, 0.5), sx=1.0, bob=-3.0, hx=2.5, sk=-0.4, pk=-0.4)),
                         (1.0, P(lean=0.05, ab=(0.0, 0.5), lf=(0.3, 0.5), lb=(-0.3, 0.3), sx=0.3, bob=1.0, hx=2.0))),
    # uzun hamle: arka bacak gergin, ön diz kırık, gövde yere yakın (kargı / mızrak)
    'atk_lunge_long': _atk((0.0, P(lean=-0.1, ab=(0.5, 0.6), lf=(0.2, 0.4), lb=(-0.2, 0.2), sx=-2.0, hx=-1.0, bob=0.5)),
                           (0.28, P(lean=-0.25, ab=(0.7, 0.8), lf=(0.1, 0.6), lb=(-0.4, 0.3), sx=-3.2, hx=-2.5, bob=1.5, sk=0.4, pk=0.3, hdy=-0.3)),
                           (0.44, P(lean=0.55, ab=(-1.0, 0.3), lf=(1.0, 0.9), lb=(-0.9, 0.05), sx=3.0, hx=6.0, bob=4.5, sk=-1.0, pk=-0.9, jaw=0.8)),
                           (0.6, P(lean=0.65, ab=(-1.3, 0.3), lf=(1.05, 0.95), lb=(-0.95, 0.0), sx=3.8, hx=8.0, bob=6.0, sk=-1.2, pk=-1.1, jaw=1.0)),
                           (0.8, P(lean=0.5, ab=(-0.9, 0.4), lf=(0.95, 0.85), lb=(-0.85, 0.05), sx=2.5, hx=7.0, bob=5.0, sk=-0.8, pk=-0.7)),
                           (1.0, P(lean=0.25, ab=(-0.2, 0.5), lf=(0.5, 0.5), lb=(-0.5, 0.2), sx=0.8, hx=4.0, bob=1.5, sk=-0.3))),
    # tam gövde çark: omuzlar geriye burulur, bacaklar çaprazlanır, gövde kalkar, tur tamamlanır
    'atk_spin_2h': _atk((0.0, P(lean=0.1, ab=(0.4, 0.5), lf=(0.4, 0.5), lb=(-0.4, 0.3), sx=-1.0, bob=1.0)),
                        (0.22, P(lean=0.0, ab=(1.0, 0.4), lf=(0.6, 0.7), lb=(-0.6, 0.4), sx=-3.0, tw=-1.5, bob=2.5, sk=0.5, pk=0.4, hdx=-1.5)),
                        (0.38, P(lean=0.15, ab=(0.2, 0.3), lf=(0.3, 0.9), lb=(0.4, 0.9), sx=0.5, tw=0.0, bob=-1.5, sk=-0.3, pk=-0.4, hdx=0.0, jaw=0.6)),
                        (0.52, P(lean=-0.1, ab=(-1.2, 0.5), lf=(-0.3, 1.0), lb=(0.9, 0.8), sx=3.5, tw=1.5, bob=-3.0, sk=-1.0, pk=-1.0, hdx=1.5, jaw=0.8)),
                        (0.68, P(lean=0.05, ab=(-0.4, 0.5), lf=(0.6, 0.8), lb=(-0.2, 0.6), sx=1.0, tw=0.5, bob=-0.5, sk=0.8, pk=0.9, hdx=0.5)),
                        (0.84, P(lean=0.2, ab=(0.3, 0.5), lf=(0.5, 0.6), lb=(-0.5, 0.4), sx=-0.5, tw=-0.3, bob=1.5, sk=0.3, pk=0.3, hx=1.5)),
                        (1.0, P(lean=0.08, ab=(0.2, 0.5), lf=(0.35, 0.45), lb=(-0.35, 0.3), sx=0.0, tw=0.0, bob=0.5, hx=1.5))),
    # ikiz bıçak: gövde burulması omuzdan omuza; ön omuz keser, ardından arka kol ikinci bıçakla öne fırlar
    'atk_dual': _atk((0.0, P(lean=0.1, ab=(-0.6, 0.6), lf=(0.4, 0.5), lb=(-0.4, 0.3), sx=-2.0, tw=-0.8, bob=0.5)),
                     (0.22, P(lean=0.05, ab=(-1.2, 0.9), lf=(0.45, 0.55), lb=(-0.45, 0.3), sx=-3.0, tw=-1.4, bob=1.0, sk=0.3, hdx=-0.5)),
                     (0.4, P(lean=0.3, ab=(-1.4, 1.3), lf=(0.6, 0.6), lb=(-0.6, 0.3), sx=3.0, tw=1.4, bob=0.0, sk=-0.5, hx=1.5, jaw=0.6, hdx=0.5)),
                     (0.55, P(lean=0.25, ab=(1.5, 0.3), lf=(0.6, 0.6), lb=(-0.6, 0.3), sx=1.0, tw=-0.6, bob=0.3, sk=-0.8, pk=-0.5, hx=2.5, jaw=0.8, hdx=0.0)),
                     (0.72, P(lean=0.3, ab=(1.8, 0.2), lf=(0.65, 0.6), lb=(-0.65, 0.3), sx=-0.5, tw=-1.2, bob=0.6, hx=3.0, sk=-0.4)),
                     (1.0, P(lean=0.12, ab=(0.6, 0.5), lf=(0.45, 0.5), lb=(-0.45, 0.3), sx=0.3, tw=0.0, bob=0.4, hx=2.0))),
    # kırbaç: ağırlık arka ayakta, sırt kavisli; omuz öne şaklar, kalça ardından gelir
    'atk_whip': _atk((0.0, P(lean=-0.1, ab=(0.4, 0.5), lf=(0.3, 0.3), lb=(-0.4, 0.3), sx=-1.0, bob=0.5)),
                     (0.25, P(lean=-0.35, ab=(0.7, 0.6), lf=(0.2, 0.3), lb=(-0.6, 0.5), sx=-2.5, bob=2.0, hx=-2.5, sk=0.6, pk=0.5, hdy=-0.5)),
                     (0.4, P(lean=0.15, ab=(-0.2, 0.6), lf=(0.6, 0.5), lb=(-0.5, 0.3), sx=2.5, bob=0.0, hx=1.0, sk=-0.4, jaw=0.5)),
                     (0.52, P(lean=0.42, ab=(-0.8, 0.6), lf=(0.8, 0.6), lb=(-0.7, 0.2), sx=3.5, bob=1.0, hx=3.5, sk=-0.9, pk=-0.8, jaw=0.9, hdy=0.2)),
                     (0.75, P(lean=0.3, ab=(-0.4, 0.6), lf=(0.6, 0.5), lb=(-0.55, 0.2), sx=2.0, bob=0.6, hx=3.0, sk=-0.5, pk=-0.4)),
                     (1.0, P(lean=0.1, ab=(0.1, 0.5), lf=(0.4, 0.4), lb=(-0.4, 0.25), sx=0.5, bob=0.3, hx=2.0))),
    # çekiç çakışı: çömel, küçük sıçrayış (dizler toplu, çekiç tepede), iki ayak birden yere çakılır
    'atk_slam_jump': _atk((0.0, P(lean=0.1, ab=(-2.2, 1.2), lf=(0.3, 0.9), lb=(-0.3, 0.7), sx=-1.0, bob=4.0)),
                          (0.22, P(lean=0.2, ab=(-2.8, 1.4), lf=(0.4, 1.6), lb=(-0.4, 1.4), sx=-1.5, bob=7.5, sk=0.5, pk=0.4, hdy=0.6)),
                          (0.4, P(lean=-0.1, ab=(-3.0, 1.3), lf=(0.6, 1.5), lb=(0.2, 1.5), sx=-1.0, bob=-7.0, hx=1.0, sk=0.9, pk=0.9, hdy=-0.6, jaw=0.5)),
                          (0.52, P(lean=0.2, ab=(-1.6, 0.6), lf=(0.5, 1.1), lb=(0.1, 1.1), sx=1.0, bob=-3.0, hx=2.0, sk=0.6, pk=0.4, jaw=0.8)),
                          (0.64, P(lean=0.55, ab=(1.0, 0.2), lf=(0.7, 1.7), lb=(-0.7, 1.5), sx=2.5, bob=9.0, hx=3.0, sk=-1.0, pk=-0.8, jaw=1.0, hdy=1.0)),
                          (0.82, P(lean=0.45, ab=(0.8, 0.3), lf=(0.6, 1.4), lb=(-0.6, 1.2), sx=2.0, bob=7.0, hx=3.0, sk=-0.5, pk=-0.3)),
                          (1.0, P(lean=0.2, ab=(0.4, 0.5), lf=(0.4, 0.6), lb=(-0.4, 0.4), sx=0.5, bob=2.0, hx=2.5))),
    # balta fırlatma: gövde geriye burulur (ağırlık arkada), bırakışta öne doğru tam burulma
    'atk_throw_axe': _atk((0.0, P(lean=-0.15, ab=(0.6, 0.5), lf=(0.3, 0.4), lb=(-0.3, 0.2), sx=-1.5, tw=-0.6, bob=0.5)),
                          (0.22, P(lean=-0.4, ab=(1.0, 0.6), lf=(0.1, 0.3), lb=(-0.5, 0.4), sx=-3.5, tw=-1.6, bob=1.5, hx=-2.0, sk=0.6, pk=0.5, hdx=-1.0, hdy=-0.6)),
                          (0.36, P(lean=0.3, ab=(-0.6, 0.7), lf=(0.7, 0.6), lb=(-0.7, 0.2), sx=2.5, tw=1.2, bob=0.0, hx=2.5, sk=-0.6, jaw=0.7, hdx=0.5)),
                          (0.5, P(lean=0.55, ab=(-1.3, 0.7), lf=(0.9, 0.8), lb=(-0.8, 0.2), sx=3.5, tw=1.6, bob=1.5, hx=4.5, sk=-1.0, pk=-0.9, jaw=1.0, hdx=1.0)),
                          (0.75, P(lean=0.4, ab=(-0.8, 0.6), lf=(0.7, 0.7), lb=(-0.6, 0.2), sx=2.0, tw=0.8, bob=1.0, hx=3.5, sk=-0.5)),
                          (1.0, P(lean=0.15, ab=(-0.2, 0.5), lf=(0.45, 0.5), lb=(-0.4, 0.2), sx=0.5, tw=0.0, bob=0.5, hx=2.0))),
    'bow': (3, lambda t: [P(lean=0.0, ab=(1.4, -1.2), lf=(0.25, 0.3), lb=(-0.3, 0.2)),
                          P(lean=-0.05, ab=(1.45, -2.3), lf=(0.3, 0.3), lb=(-0.35, 0.2)),
                          P(lean=0.08, ab=(0.6, -0.4), lf=(0.3, 0.3), lb=(-0.35, 0.2))][min(2, int(t * 3))], False, False),
    'throw': (3, lambda t: [P(lean=-0.2, ab=(0.8, 0.5), lf=(0.4, 0.4), lb=(-0.3, 0.2), sx=-1.5),
                            P(lean=0.3, ab=(-0.5, 0.6), lf=(0.6, 0.6), lb=(-0.5, 0.2), sk=-0.4, sx=2.0),
                            P(lean=0.2, ab=(-0.2, 0.6), lf=(0.4, 0.4), lb=(-0.3, 0.2), sx=0.8)][min(2, int(t * 3))], False, False),
    'block': (1, lambda t: P(lean=0.12, ab=(1.25, 1.0), lf=(0.45, 0.5), lb=(-0.45, 0.3), bob=1.5, sx=1.0), False, False),
    'cast': (2, lambda t: [P(lean=-0.05, ab=(0.5, 1.2), sx=-0.5), P(lean=0.15, ab=(1.4, 0.3), lf=(0.3, 0.3), lb=(-0.3, 0.2), sx=1.5, jaw=0.7)][min(1, int(t * 2))], False, False),
}


# hacimli gölgelendirme ayarları (volume.VCanvas.shade): daha geniş ışık bandı, güçlü büyük form
SHADE = dict(form=0.7, bands=(-0.12, 0.3, 0.56, 0.8), grad=0.45, rim_amt=0.3, rim_th=0.6, lit_outline=0.0)


def render_frame(anim, i, cell=CELL, feet=FEET):
    """Tek kare (1.5x doku yoğunluğu). Dönen çapalar dünya birimindedir."""
    n, fn, loop, arm = ANIMS[anim]
    t = (i / n) if loop else (min(0.999, i / n + 0.5 / n) if n > 1 else 0.0)
    p = fn(t)
    c = VCanvas(cell[0], cell[1], feet[0], feet[1])
    c.zscale = TEX
    s = TexScale(c)
    if 'roll' in p:
        ang = p['roll'] * math.tau
        xf = Xf(s, 0, -16, ang, pivot=(0, -19))
        info = draw_bengu(xf, p, True)
    else:
        info = draw_bengu(s, p, arm, arm)
    rgba = c.shade(**SHADE)
    nm = c.normal_map(rgba[..., 3])
    return c, rgba, nm, info
