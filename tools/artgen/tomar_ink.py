"""v34 Kut Tomarı (stat tomarı) mürekkep-cel çizimleri: yerdeki tomar, kaide, açılış kareleri, tamga, arayüz kartları.

Tasarım: Ulu Kayın'ın kabuğundan dürülmüş sıcak krem bir kayın kabuğu tomarı (kara kayın benekleri, kıvrık kabuk
uçları, sarmal dürüm ağzı). İki ucunda tunç-altın **bozkurt başlı** topuzlar (dışa bakan kurt başı, ışıyan göz),
gövdede üç ışıyan **tamga** (Bozkurt kızılı kurt kulakları, Kartal mavisi kanatlı kuş, Ayı yeşili pençe: üç stat), sağ
üçte birde kızıl deri kayış ve üstünde **kızıl mum mühür** (altın Kut tamgası: Ulu Kayın ağacı); mühürden üç renk ipek
kurdele ve boncuk sarkar. Okununca tomar aşağı doğru açılır (asma tomar): üstte kurt başlı ahşap çubuk, kabuk yaprak,
iki yanda Göktürk harfi sütunları, ortada fırça halkası; seçilen statın tamgası halkanın içinde parlar.

Çıktı (tek atlas): assets/fx/ink/tomar_v2.png (+ _e ışıma) + tomar_v2.json {texel, sprites: {ad: {rect, pivot, texel}}}
  tomar          yerdeki kapalı tomar (köken: rulonun ortası), texel 4
  tomar_kaide    alçak oyma taş kaide + kilim örtü (köken: taban ortası), texel 4
  tomar_ac_0..5  açılış kareleri (köken: üst çubuğun ortası), texel 4
  tamga_kurt / tamga_kartal / tamga_ayi   seçilen statın büyük tamgası (açık tomarın halkasına konur), texel 4
  ui_tomar       arayüz simgesi (ışıma ve hale dokuya işlenmiş), texel 4
  ui_kart_kurt / ui_kart_kartal / ui_kart_ayi   tomar seçim kartı resmi (açık tomar + tamga, ışıma işlenmiş), texel 8
Çizim 4 kat süper örneklemeyle (ss=4), HD paketinde (KY_HD=2) iki kat çözünürlükte yeniden çizilir.

Kullanım (tools/artgen içinde):
    python tomar_ink.py                 temel atlas (assets/fx/ink/tomar_v2*)
    KY_HD=2 python tomar_ink.py         HD atlas (assets_hd/x2/fx/ink/tomar_v2.png), sonra:
    python tomar_ink.py --paketle       HD PNG -> WebP + manifest girişi (hd_paket._encode)
    python tomar_ink.py --onizleme out.png   koyu soğuk zemin üstünde önizleme (okunurluk denetimi)
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import hdpack  # noqa: E402,F401  (KY_HD=2: PNG yazımları assets_hd/x2'ye)
from hdpack import HD  # noqa: E402
import inkkit as ik  # noqa: E402
from inkkit import Ink, INK  # noqa: E402
from inkprop import Prop, GOLD, BRONZE, WOOD_D, STONE_W, STONE, RED, HAIR_W, ram_motif, diamond  # noqa: E402

A = os.path.normpath(os.path.join(HERE, '..', '..', 'assets'))

# ------------------------------------------------------------------ malzemeler (sıcak, soğuk zeminde canlı)
BARK = Ink('#efe0bf', '#ad8a72', '#fffaea', '#6c4a42', name='kayın kabuğu tomar')
BARK_IN = Ink('#f6ead0', '#c0a084', '#fffdf4', name='kabuk iç yüzü')
WAX = Ink('#b8202a', '#5c0c22', '#f0604a', '#360616', name='kızıl mum')
STRAP = Ink('#8c3424', '#44141c', '#c4644a', name='kızıl deri')
FIN = Ink('#e0a640', '#80461e', '#fff2b0', '#4a2414', kind='metal', name='altın tunç')
KILIM = Ink('#9c2a26', '#4c1022', '#d8583e', name='kilim')

STAT = {
    'kurt': (1.0, 0.416, 0.302),     # items.json ongun.kurt #ff6a4d
    'kartal': (0.369, 0.784, 1.0),   # #5ec8ff
    'ayi': (0.608, 0.878, 0.416),    # #9be06a
}
KUT_GOLD = (1.0, 0.82, 0.38)


def _lift(c, k=0.45):
    return tuple(min(1.0, v + (1 - v) * k) for v in c)


# ------------------------------------------------------------------ tamgalar (yerel birim: yaklaşık ±1 kutu)
def glyph_strokes(stat):
    """Tamga fırça darbeleri: [(noktalar, kalınlık_çarpanı)] (-1..1 kutusunda, y aşağı)."""
    if stat == 'kurt':
        # önden kurt başı: dolu baş (draw_glyph) üstünde iki çekik göz ve burun çizgisi (mürekkep oyuk)
        return []
    if stat == 'kartal':
        # açık kanatlı kartal: dikey gövde, yukarı kıvrık iki kanat, çatal kuyruk
        return [([(0.0, -0.98), (0.0, 0.72)], 1.0),
                ([(-1.0, -0.62), (-0.55, -0.12), (0.0, 0.05), (0.55, -0.12), (1.0, -0.62)], 1.0),
                ([(-0.42, 1.0), (0.0, 0.62), (0.42, 1.0)], 0.85),
                ([(-0.22, -0.78), (0.0, -1.0), (0.22, -0.78)], 0.6)]
    if stat == 'ayi':
        # ayı pençesi: dolu taban (draw_glyph'te dolgu) + dört tırnak
        out = []
        for k, x in enumerate((-0.8, -0.28, 0.28, 0.8)):
            y0 = -0.4 if k in (1, 2) else -0.16
            out.append(([(x, y0), (x * 1.06, y0 - 0.4), (x * 1.16 + (0.1 if x > 0 else -0.1), y0 - 0.62)], 0.95))
        return out
    # 'kut': Ulu Kayın (hayat ağacı): gövde, iki çift dal, kökler, tepe tomurcuğu
    return [([(0.0, 1.0), (0.0, -0.92)], 1.0),
            ([(0.0, 0.05), (-0.62, -0.42), (-0.78, -0.8)], 0.8), ([(0.0, 0.05), (0.62, -0.42), (0.78, -0.8)], 0.8),
            ([(0.0, -0.38), (-0.36, -0.7)], 0.7), ([(0.0, -0.38), (0.36, -0.7)], 0.7),
            ([(0.0, 0.7), (-0.55, 1.0)], 0.7), ([(0.0, 0.7), (0.55, 1.0)], 0.7)]


def draw_glyph(cv, stat, cx, cy, s, w, z, col=None, glow=None, ink_under=True, alpha=1.0):
    """Tamgayı (cx, cy) merkezli, s yarı boyunda çiz: altta kalın mürekkep, üstte dolgun renkli ışıyan fırça çizgisi,
    ortasında açık iç ışık. Ayı tamgasının pençe tabanı dolu şekil."""
    c = col if col is not None else STAT.get(stat, KUT_GOLD)
    g = glow if glow is not None else tuple(v * 0.62 for v in c)
    if stat == 'kurt':
        # kurt başı (önden; arayüzün "kurt" simgesiyle aynı siluet): dik sivri kulaklar, köşeli yanaklar, uzun dar burun
        def Q(pts):
            return [(cx + x * s, cy + y * s, 0.0) for x, y in pts]
        head = Q([(-0.7, -0.92), (-0.28, -0.42), (0.28, -0.42), (0.7, -0.92), (0.76, -0.08), (0.5, 0.26), (0.2, 0.92), (-0.2, 0.92),
                  (-0.5, 0.26), (-0.76, -0.08)])
        if ink_under:
            cv.fill(cv.blob([(cx + (p[0] - cx) * 1.14, cy + (p[1] - cy) * 1.1, 0.0) for p in head]), INK, z=z, alpha=0.92 * alpha)
        cv.fill(cv.blob(head), c, z=z + 0.001, glow=g, alpha=alpha)
        cv.fill(cv.blob(Q([(-0.5, -0.62), (-0.1, -0.3), (-0.3, -0.05), (-0.62, -0.12)])), _lift(c, 0.45), z=z + 0.002, alpha=alpha)
        for f in (-1, 1):
            cv.fill(cv.blob(Q([(f * 0.6, -0.78), (f * 0.38, -0.44), (f * 0.56, -0.44)])), INK, z=z + 0.003, alpha=0.85 * alpha)   # kulak içi
            cv.fill(cv.blob(Q([(f * 0.48, -0.06), (f * 0.14, 0.04), (f * 0.42, 0.16)])), INK, z=z + 0.003, alpha=alpha)          # çekik göz
        cv.fill(cv.blob(Q([(-0.17, 0.66), (0.17, 0.66), (0.0, 0.86)])), INK, z=z + 0.003, alpha=alpha)                          # burun
    if stat == 'ayi':
        pad = cv.ellipse((cx, cy + 0.5 * s), 0.68 * s, 0.47 * s)
        if ink_under:
            cv.fill(cv.ellipse((cx, cy + 0.5 * s), 0.68 * s + w * 0.09, 0.47 * s + w * 0.09), INK, z=z, alpha=0.92 * alpha)
        cv.fill(pad, c, z=z + 0.001, glow=g, alpha=alpha)
        cv.fill(cv.ellipse((cx - 0.2 * s, cy + 0.36 * s), 0.26 * s, 0.13 * s, rot=-0.3), _lift(c, 0.6), z=z + 0.002, alpha=alpha)
    for pts, wk in glyph_strokes(stat):
        q = [(cx + x * s, cy + y * s) for x, y in pts]
        if ink_under:
            cv.stroke(q, w * wk * 1.75, z=z, col=INK, taper=(0.08, 0.14), alpha=0.92 * alpha)
        cv.stroke(q, w * wk * 1.2, z=z + 0.001, col=c, glow=g, taper=(0.1, 0.18), alpha=alpha)
        cv.stroke(q, w * wk * 0.32, z=z + 0.002, col=_lift(c, 0.55), taper=(0.3, 0.4), alpha=alpha)


# ------------------------------------------------------------------ parçalar
def wolf_head(cv, x, y, s, face, z, eye_glow=KUT_GOLD):
    """Tunç-altın bozkurt başı topuz (yandan; face = +1 sağa bakar). (x, y): boyun ortası (çubuğun ucu).
    Sivri dik kulak, uzun burun, aralık çene ve ak dişi, ense yelesi; göz ışır."""
    def P(px, py, *r):
        return (x + face * px * s, y + py * s) + r
    head = cv.blob([P(-0.2, -2.0), P(-0.9, -2.9, 0.0), P(0.5, -2.7), P(0.8, -5.4, 0.0), P(2.3, -3.1), P(3.1, -3.0), P(3.9, -2.45), P(6.7, -1.75),
                    P(7.4, -1.25, 0.0), P(7.2, -0.62, 0.0), P(5.2, -0.25), P(4.3, 0.05, 0.0), P(6.3, 0.55), P(6.1, 0.95, 0.0), P(4.8, 1.35), P(3.3, 1.75),
                    P(2.5, 2.6), P(1.7, 2.3), P(0.9, 3.2, 0.0), P(0.3, 2.5), P(-0.2, 2.2)])
    det = [('ink', [P(5.2, -0.25), P(4.3, 0.05), P(3.4, 0.2)], 1.1, (0.1, 0.6)),     # ağız yarığı
           ('deep', cv.blob([P(1.15, -2.9), P(1.0, -4.6, 0.0), P(2.0, -3.0)])),      # kulak içi
           ('ink', [P(0.4, -1.6), P(1.2, 0.0), P(0.6, 1.6)], 0.8, (0.3, 0.3)),     # yele kıvrımları
           ('ink', [P(1.7, -1.3), P(2.3, 0.4), P(1.8, 1.8)], 0.65, (0.3, 0.3)),
           ('ink', [P(3.2, -2.5), P(4.4, -2.0)], 0.6, (0.2, 0.6)),                 # kaş
           ('stroke', [P(4.2, -2.2), P(6.9, -1.5)], 0.8, FIN.hi, (0.2, 0.4))]      # burun sırtı parlaması
    cv.shape(head, FIN, z=z, sd=1.0 * s, hi=0.45 * s, ol=1.0, details=det)
    # diş
    cv.shape(cv.blob([P(5.3, -0.2, 0.0), P(5.8, -0.18, 0.0), P(5.5, 0.55, 0.0)]), Ink('#fff6e0'), z=z + 0.005, sd=0.1, ol=0.4, flat=True)
    # burun ucu
    cv.shape(cv.ellipse(P(7.1, -1.15), 0.42 * s, 0.32 * s), Ink('#3a2018'), z=z + 0.006, sd=0.1, ol=0.3, flat=True)
    # ışıyan göz (çekik)
    cv.shape(cv.blob([P(3.0, -1.55, 0.0), P(3.7, -1.95), P(4.25, -1.75, 0.0), P(3.6, -1.35)]), Ink(_lift(eye_glow, 0.55)), z=z + 0.01, sd=0.1, ol=0.6,
             glow=eye_glow, flat=True)
    # boyun bileziği
    cv.shape(cv.blob([P(-0.7, -2.4, 0.0), P(0.3, -2.4, 0.0), P(0.3, 2.4, 0.0), P(-0.7, 2.4, 0.0)]), BRONZE, z=z + 0.02, sd=0.4 * s, hi=0.2 * s, ol=0.85,
             details=[('stroke', [P(-0.2, -2.1), P(-0.2, 2.1)], 0.8, FIN.hi, (0.2, 0.2))])


def lenticels(rng, x0, x1, y0, y1, n, avoid=()):
    out = []
    for _ in range(n):
        for _t in range(8):
            x = rng.uniform(x0, x1)
            if all(abs(x - a) > b for a, b in avoid):
                break
        y = rng.uniform(y0, y1)
        ln = rng.uniform(0.9, 2.4)
        out.append(('ink', [(x - ln / 2, y), (x + ln / 2, y + rng.uniform(-0.12, 0.12))], rng.uniform(1.1, 1.9), (0.35, 0.45)))
    return out


def ribbon(cv, x, y, ln, col, z, sway):
    m = Ink(col, tuple(v * 0.45 for v in col), _lift(col, 0.45))
    tip = (x + sway, y + ln)
    cv.shape(cv.blob([(x - 0.55, y, 0.0), (x + 0.55, y, 0.0), (x + sway * 0.5 + 0.7, y + ln * 0.55), (tip[0] + 0.5, tip[1] - 0.3), (tip[0], tip[1] + 0.6, 0.0),
                      (tip[0] - 0.5, tip[1] - 0.3), (x + sway * 0.5 - 0.6, y + ln * 0.5)]), m, z=z, sd=0.35, hi=0.15, ol=0.7)
    cv.shape(cv.ellipse((tip[0], tip[1] + 1.1), 0.75, 0.75), Ink(_lift(col, 0.3), tuple(v * 0.5 for v in col), (1, 1, 1)), z=z + 0.01, sd=0.25, hi=0.2,
             ol=0.6, glow=col)


def seal(cv, x, y, r, z, rng):
    """Kızıl mum mühür (düzensiz damlalı kenar) + altın Kut tamgası (Ulu Kayın)."""
    pts = []
    for k in range(18):
        a = k / 18 * 2 * math.pi
        rr = r * (1.0 + 0.09 * math.sin(a * 3 + 0.7) + rng.uniform(-0.05, 0.05))
        if 0.9 < a < 1.6:
            rr *= 1.22   # damla
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    cv.shape(cv.blob(pts), WAX, z=z, sd=0.9, hi=0.35, ol=1.0, bounce=0.3,
             details=[('shade', cv.ellipse((x, y), r * 0.7, r * 0.7)), ('col', cv.ellipse((x - 0.15, y - 0.15), r * 0.64, r * 0.64), WAX.base)])
    draw_glyph(cv, 'kut', x, y, r * 0.5, 0.9, z + 0.02, col=KUT_GOLD, ink_under=False)


# ------------------------------------------------------------------ kapalı tomar (yerde)
def tomar_kapali(tex=4.0, tilt=-0.07, eye=KUT_GOLD):
    W, H = 50, 34
    P = Prop(W, H, W / 2, 14, ss=4, tex=tex)
    cv = P.cv
    rng = np.random.default_rng(34)
    ca, sa = math.cos(tilt), math.sin(tilt)
    cv.push(lambda p: (p[0] * ca - p[1] * sa, p[0] * sa + p[1] * ca))
    L, R = 15.0, 4.7
    # rulo gövdesi
    body = cv.blob([(-L, -R, 0.0), (L, -R, 0.0), (L + 0.6, -R * 0.55), (L + 0.8, 0), (L + 0.6, R * 0.55), (L, R, 0.0), (-L, R, 0.0),
                    (-L - 0.6, R * 0.55), (-L - 0.8, 0), (-L - 0.6, -R * 0.55)])
    det = lenticels(rng, -L + 1.5, L - 1.5, -R + 0.7, R - 0.8, 26, avoid=((-10.0, 1.9), (-4.4, 1.9), (1.4, 1.9), (8.2, 3.2)))
    # boydan sarım çizgileri (kabuğun kat yeri), alt gölge bandı
    det.append(('ink', [(-L + 0.5, R * 0.62), (-2, R * 0.66), (L - 0.5, R * 0.6)], 0.6, (0.2, 0.2)))
    det.append(('shade', cv.blob([(-L, R * 0.35, 0.0), (L, R * 0.35, 0.0), (L, R, 0.0), (-L, R, 0.0)])))
    det.append(('hi', cv.blob([(-L + 1, -R * 0.78, 0.0), (L - 1, -R * 0.78, 0.0), (L - 1, -R * 0.55, 0.0), (-L + 1, -R * 0.55, 0.0)])))
    cv.shape(body, BARK, z=0.0, sd=2.2, hi=0.6, ol=1.05, bounce=0.35, details=det)
    # dürüm ağzı (sol uç): sarmal
    sp = [(-L - 0.2 + math.cos(a) * 1.3 * (1 - t * 0.75), math.sin(a) * R * 0.92 * (1 - t * 0.75)) for t, a in
          zip(np.linspace(0, 1, 40), np.linspace(-math.pi / 2, 2.6 * math.pi, 40))]
    cv.shape(cv.ellipse((-L - 0.2, 0), 1.45, R * 0.95), BARK_IN, z=0.05, sd=0.5, hi=0.2, ol=0.85)
    cv.stroke(sp, 0.75, z=0.06, col=INK, taper=(0.1, 0.5))
    # kıvrık kabuk uçları (sağ uçta kalkan dil)
    curl = cv.blob([(L - 3.5, -R + 0.1, 0.0), (L - 1.0, -R - 1.6), (L + 0.4, -R - 1.3, 0.0), (L - 0.3, -R + 0.1, 0.0)])
    cv.shape(curl, BARK_IN, z=0.07, sd=0.4, ol=0.8, details=[('shade', cv.ellipse((L - 0.6, -R - 0.9), 0.9, 0.6))])
    # çubuk uçları + kurt başlı topuzlar
    for f in (-1, 1):
        cv.shape(cv.capsule((f * (L - 0.5), 0), (f * (L + 2.3), 0), 1.05, 1.05), WOOD_D, z=-0.1, sd=0.4, hi=0.2, ol=0.8)
        wolf_head(cv, f * (L + 2.2), 0.0, 1.0, f, 0.2, eye_glow=eye)
    # sol uçta ince kayış
    cv.shape(cv.blob([(-12.6, -R - 0.25, 0.0), (-11.4, -R - 0.25, 0.0), (-11.4, R + 0.25, 0.0), (-12.6, R + 0.25, 0.0)]), STRAP, z=0.1, sd=0.45, hi=0.15,
             ol=0.8, details=[('ink', [(-12.0, -R), (-12.0, R)], 0.45, (0.2, 0.2))])
    # üç tamga (stat renkleri, ışır)
    for stat, gx in (('kurt', -7.6), ('kartal', -2.4), ('ayi', 2.8)):
        draw_glyph(cv, stat, gx, -0.2, 1.9, 1.25, 0.3)
    # sağda kayış + mühür + kurdeleler
    cv.shape(cv.blob([(7.3, -R - 0.35, 0.0), (9.1, -R - 0.35, 0.0), (9.1, R + 0.35, 0.0), (7.3, R + 0.35, 0.0)]), STRAP, z=0.1, sd=0.6, hi=0.2, ol=0.85,
             details=[('ink', [(7.7, -R), (7.7, R)], 0.4, (0.2, 0.2)), ('ink', [(8.7, -R), (8.7, R)], 0.4, (0.2, 0.2))])
    cv.pop()
    # kurdeleler dönüşsüz (aşağı sarkar); mühür dönüşlü konuma göre
    sx, sy = 8.2 * ca - 0.6 * sa, 8.2 * sa + 0.6 * ca
    for k, (stat, sw) in enumerate((('kurt', -1.6), ('kartal', 0.2), ('ayi', 1.9))):
        ribbon(cv, sx - 1.0 + k * 1.0, sy + 2.6, 7.2 + (1.2 if k == 1 else 0.0), STAT[stat], 0.35 - k * 0.001, sw)
    cv.push(lambda p: (p[0] * ca - p[1] * sa, p[0] * sa + p[1] * ca))
    seal(cv, 8.2, 0.6, 3.55, 0.45, rng)
    cv.pop()
    return P.done(outer=1.0, rim=0.3, rim_col=(0.7, 0.85, 1.0))


# ------------------------------------------------------------------ kaide
def kaide(tex=4.0):
    """Alçak oyma ak taş kaide: üstte kilim örtü (sarkan saçaklı), önde koçboynuzu oyma, iki yanda küçük taş boynuz."""
    P = Prop(34, 14, 17, 12, ss=4, tex=tex)
    cv = P.cv
    base = cv.blob([(-13, 0.5, 0.0), (-13.5, -3.5, 0.0), (-11.5, -6.5, 0.0), (11.5, -6.5, 0.0), (13.5, -3.5, 0.0), (13, 0.5, 0.0)])
    det = [('ink', [(-13, -3.5), (13, -3.5)], 0.7, (0.1, 0.1)), ('shade', cv.blob([(-13, -1.2, 0.0), (13, -1.2, 0.0), (13, 0.5, 0.0), (-13, 0.5, 0.0)]))]
    cv.shape(base, STONE_W, z=0, sd=1.8, hi=0.45, ol=1.0, details=det, hatch=0.25)
    ram_motif(cv, 0, -1.1, 2.2, 1.1, 0.1, col=INK)
    # kilim örtü: üst yüzde, önden sarkan iki uç
    kl = cv.blob([(-9.5, -6.8, 0.0), (9.5, -6.8, 0.0), (10.2, -4.2), (9.0, -2.4, 0.0), (6.0, -4.6), (-6.0, -4.6), (-9.0, -2.4, 0.0), (-10.2, -4.2)])
    kdet = [('col', cv.blob(diamond(0, -5.8, 1.6, 0.8)), (0.95, 0.78, 0.36)), ('col', cv.blob(diamond(-5.2, -5.4, 1.0, 0.55)), (0.2, 0.36, 0.62)),
            ('col', cv.blob(diamond(5.2, -5.4, 1.0, 0.55)), (0.2, 0.36, 0.62)), ('ink', [(-9.2, -5.0), (9.2, -5.0)], 0.4, (0.1, 0.1))]
    cv.shape(kl, KILIM, z=0.2, sd=0.8, hi=0.25, ol=0.85, details=kdet)
    for f in (-1, 1):
        for j in range(3):
            x = f * (9.4 - j * 0.6)
            cv.stroke([(x, -2.6 + j * 0.25), (x + f * 0.15, -1.2 + j * 0.25)], 0.6, z=0.25, col=(0.95, 0.85, 0.6), taper=(0.1, 0.5))
    # kaidenin ışıyan çentikleri (Kut altını)
    for x in (-10.6, 10.6):
        cv.stroke([(x, -5.2), (x, -2.0)], 0.9, z=0.15, col=_lift(KUT_GOLD, 0.3), glow=(0.8, 0.55, 0.18), taper=(0.2, 0.2))
    return P.done(outer=1.0, rim=0.25)


# ------------------------------------------------------------------ açık tomar (açılış kareleri, kart resmi)
def tomar_acik(k, tex=4.0, stat=None, ss=4):
    """k: açıklık 0..1. Köken: üst çubuğun ortası. Üstte kurt başlı ahşap çubuk; kabuk yaprak aşağı açılır, altta
    küçülen kabuk rulosu. Yaprakta iki yanda Göktürk harfi sütunları, ortada fırça halkası (k büyüdükçe görünür)."""
    W, H = 50, 44
    P = Prop(W, H, W / 2, 7, ss=ss, tex=tex)
    cv = P.cv
    rng = np.random.default_rng(7)
    Lh = 12.6
    Ls = 2.0 + k * 26.0          # yaprak boyu
    Rr = 4.6 * (1.0 - 0.42 * k)  # alt rulonun yarıçapı (açıldıkça incelir)
    # yaprak
    wav = [(-Lh, 0.0, 0.0), (Lh, 0.0, 0.0)]
    for t in np.linspace(0, 1, 7)[1:]:
        wav.append((Lh + 0.25 * math.sin(t * 9.0), Ls * t))
    for t in np.linspace(1, 0, 7)[:-1]:
        wav.append((-Lh - 0.25 * math.sin(t * 7.0 + 1.0), Ls * t))
    sheet = cv.blob(wav)
    det = lenticels(rng, -Lh + 1.0, Lh - 1.0, 1.0, max(1.2, Ls - 1.0), int(4 + 10 * k), avoid=((-9.2, 1.5), (9.2, 1.5), (0.0, 7.8)))
    det = [d for d in det if True]
    # kenar gölgesi ve rulonun yaprağa düşen gölgesi
    det.append(('shade', cv.blob([(-Lh, max(0.0, Ls - 2.2), 0.0), (Lh, max(0.0, Ls - 2.2), 0.0), (Lh, Ls, 0.0), (-Lh, Ls, 0.0)])))
    det.append(('shade', cv.blob([(-Lh, 0.0, 0.0), (Lh, 0.0, 0.0), (Lh, 1.3, 0.0), (-Lh, 1.3, 0.0)])))
    # Göktürk harfi sütunları (kara mürekkep)
    runes = [[(-0.6, -0.7), (0.0, 0.0), (-0.6, 0.7)], [(0.0, -0.8), (0.0, 0.8), (0.55, 0.2)], [(-0.5, -0.6), (0.5, 0.6)], [(0.5, -0.7), (-0.2, 0.0), (0.5, 0.7)],
             [(-0.5, -0.8), (0.0, 0.2), (0.5, -0.8)], [(0.0, -0.8), (0.0, 0.8)], [(-0.55, 0.6), (0.0, -0.7), (0.55, 0.6)]]
    for col_x in (-9.4, 9.4):
        y = 3.0
        j = 0 if col_x < 0 else 3
        while y < Ls - 2.6:
            rp = runes[j % len(runes)]
            det.append(('ink', [(col_x + px * 1.15, y + py * 1.15) for px, py in rp], 0.95, (0.25, 0.3)))
            y += 3.2
            j += 1
    cv.shape(sheet, BARK_IN, z=0.0, sd=0.9, hi=0.3, ol=0.95, details=det, grad=0.14)
    # fırça halkası (enso) ve tamga yeri
    cy = 14.0
    if k > 0.55:
        a_ = min(1.0, (k - 0.55) / 0.35)
        pts = [(math.cos(a) * 7.0, cy + math.sin(a) * 7.0) for a in np.linspace(-1.9, -1.9 + a_ * 5.9, 40)]
        cv.stroke(pts, 2.2, z=0.05, col=INK, taper=(0.05, 0.75), alpha=0.92)
        cv.stroke([(x * 0.98, y) for x, y in pts], 0.7, z=0.051, col=(0.86, 0.66, 0.3), taper=(0.1, 0.8), alpha=0.6)
    if stat:
        cv.fill(cv.ellipse((0.0, cy), 6.3, 6.3), STAT[stat], z=0.04, alpha=0.16, glow=tuple(v * 0.25 for v in STAT[stat]))
        draw_glyph(cv, stat, 0.0, cy, 4.6, 2.3, 0.08)
    # alt rulo
    yb = Ls + Rr * 0.55
    roll = cv.blob([(-Lh - 0.2, yb - Rr, 0.0), (Lh + 0.2, yb - Rr, 0.0), (Lh + 0.8, yb), (Lh + 0.2, yb + Rr, 0.0), (-Lh - 0.2, yb + Rr, 0.0),
                    (-Lh - 0.8, yb)])
    rdet = lenticels(rng, -Lh + 1, Lh - 1, yb - Rr + 0.5, yb + Rr - 0.6, int(5 + 8 * (1 - k)))
    rdet.append(('shade', cv.blob([(-Lh, yb + Rr * 0.3, 0.0), (Lh, yb + Rr * 0.3, 0.0), (Lh, yb + Rr, 0.0), (-Lh, yb + Rr, 0.0)])))
    cv.shape(roll, BARK, z=0.2, sd=1.6, hi=0.5, ol=1.0, bounce=0.3, details=rdet)
    for f in (-1, 1):
        cv.shape(cv.ellipse((f * (Lh + 0.3), yb), 1.1, Rr * 0.92), BARK_IN, z=0.21, sd=0.3, ol=0.7,
                 details=[('ink', [(f * (Lh + 0.3) + math.cos(a) * 0.5, yb + math.sin(a) * Rr * 0.5) for a in np.linspace(0, 5.5, 12)], 0.55, (0.1, 0.5))])
    # üst çubuk + kurt başları
    cv.shape(cv.capsule((-Lh - 2.5, 0.0), (Lh + 2.5, 0.0), 1.25, 1.25), WOOD_D, z=0.3, sd=0.6, hi=0.3, ol=0.9,
             details=[('stroke', [(-Lh, -0.6), (Lh, -0.6)], 0.6, (0.62, 0.46, 0.36), (0.1, 0.1))])
    for f in (-1, 1):
        wolf_head(cv, f * (Lh + 2.4), 0.0, 0.8, f, 0.35)
    # askı ipi (üst çubuğun iki ucundan tepeye)
    cv.stroke([(-Lh + 1.0, -0.8), (0.0, -5.6), (Lh - 1.0, -0.8)], 0.8, z=0.29, col=(0.78, 0.62, 0.38), taper=(0.1, 0.1))
    cv.shape(cv.ellipse((0.0, -5.7), 0.9, 0.9), FIN, z=0.31, sd=0.3, hi=0.2, ol=0.6)
    return P.done(outer=1.0, rim=0.25)


def tamga_buyuk(stat, tex=4.0):
    """Açık tomarın halkasına konan büyük tamga (ayrı sprite: oyunda açılırken belirir, ışır). Köken: merkez."""
    P = Prop(14, 14, 7, 7, ss=4, tex=tex)
    draw_glyph(P.cv, stat, 0.0, 0.0, 4.6, 2.3, 0.0)
    return P.done(outer=0.0, rim=0.0, grain=0.0)


# ------------------------------------------------------------------ arayüz: ışımayı dokuya işle
def bake_ui(res, halo=0.55, halo_col=(1.0, 0.78, 0.4), halo_r=None):
    """Arayüz dokusu (toplamalı ışıma çizilemez): ışıma albedoya eklenir, arkaya yumuşak sıcak hale."""
    from scipy import ndimage
    rgba, glow, org = res
    a = rgba[..., 3:4]
    ga = glow[..., 3:4]
    rgb = rgba[..., :3] * a
    rgb = rgb + glow[..., :3] * ga * 0.55 * a                 # ışıyan çizgiler daha parlak
    h, w = a.shape[:2]
    rr = halo_r if halo_r is not None else max(h, w) * 0.045
    # dış hale: silüet + ışıma bulanığı, sıcak renk
    src = np.clip(a[..., 0] * 0.6 + ga[..., 0] * 1.6, 0, 1)
    bl = ndimage.gaussian_filter(src, rr)
    gl_rgb = ndimage.gaussian_filter(glow[..., :3] * ga, (rr * 0.6, rr * 0.6, 0))
    hc = np.array(halo_col, np.float32)[None, None] * bl[..., None] * 0.7 + gl_rgb * 1.2
    ha = np.clip(bl * halo, 0, 0.75)[..., None]
    # önçarpılmış "over": sprite halenin üstünde
    out_rgb = rgb + hc * ha * (1 - a)
    out_a = a + ha * (1 - a)
    st = np.where(out_a > 1e-4, out_rgb / np.maximum(out_a, 1e-4), 0)
    return np.concatenate([np.clip(st, 0, 1), np.clip(out_a, 0, 1)], -1), np.zeros_like(glow), org


# ------------------------------------------------------------------ atlas
def sprites():
    out = []   # (ad, (rgba, glow, köken), texel)
    out.append(('tomar', tomar_kapali(), 4.0))
    out.append(('tomar_kaide', kaide(), 4.0))
    for i, k in enumerate((0.0, 0.16, 0.36, 0.58, 0.8, 1.0)):
        out.append(('tomar_ac_%d' % i, tomar_acik(k), 4.0))
    for st in ('kurt', 'kartal', 'ayi'):
        out.append(('tamga_' + st, tamga_buyuk(st), 4.0))
    out.append(('ui_tomar', bake_ui(tomar_kapali(tilt=-0.12)), 4.0))
    for st in ('kurt', 'kartal', 'ayi'):
        out.append(('ui_kart_' + st, bake_ui(tomar_acik(1.0, tex=8.0, stat=st, ss=3), halo=0.5, halo_col=_lift(STAT[st], 0.2)), 8.0))
    return out


def to8(arr):
    return (np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)


def export():
    from export_ink_ortam import save
    items = sprites()
    W = 1024
    pad = 4
    order = sorted(items, key=lambda t: -t[1][0].shape[0])
    x = y = rowh = 0
    pos = {}
    for n, (r, g, o), tx in order:
        h, w = r.shape[0] // HD, r.shape[1] // HD
        if x + w + pad > W:
            x = 0
            y += rowh + pad
            rowh = 0
        pos[n] = (x, y)
        x += w + pad
        rowh = max(rowh, h)
    Hh = int(math.ceil((y + rowh) / 4.0) * 4)
    alb = np.zeros((Hh * HD, W * HD, 4), np.float32)
    glo = np.zeros_like(alb)
    meta = {"texel": 4.0, "filter": "linear", "_not": "v34 Kut Tomarı atlası (tools/artgen/tomar_ink.py). rect/pivot temel doku pikseli; texel: doku pikseli / dünya (arayüz) birimi.",
            "sprites": {}}
    for n, (r, g, o), tx in items:
        px, py = pos[n]
        h, w = r.shape[:2]
        alb[py * HD:py * HD + h, px * HD:px * HD + w] = r
        glo[py * HD:py * HD + h, px * HD:px * HD + w] = g
        meta["sprites"][n] = {"rect": [px, py, w // HD, h // HD], "pivot": [round(o[0], 2), round(o[1], 2)], "texel": tx,
                              "glow": bool(g[..., 3].max() > 0.02)}
    save(to8(alb), 'fx/ink', 'tomar_v2.png')
    save(to8(glo), 'fx/ink', 'tomar_v2_e.png')
    json.dump(meta, open(os.path.join(A, 'fx', 'ink', 'tomar_v2.json'), 'w', encoding='utf-8', newline='\n'), indent=1, ensure_ascii=False)
    print('  tomar_v2', W, Hh, len(items))


def paketle():
    """HD PNG -> WebP ve manifest girişi (yalnızca bu atlas; öbür girişlere dokunmaz)."""
    import hashlib
    import hd_paket
    rel = 'fx/ink/tomar_v2.png'
    new, txt = hd_paket._encode(rel)
    print(txt)
    if not new:
        return
    man = json.load(open(hd_paket.MAN, encoding='utf-8'))
    from PIL import Image
    bw, bh = Image.open(os.path.join(A, rel)).size
    md5 = hashlib.md5(open(os.path.join(A, rel), 'rb').read()).hexdigest()
    man[rel] = [bw, bh, new, md5]
    json.dump(dict(sorted(man.items())), open(hd_paket.MAN, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    hd_paket._write_import(os.path.join(hd_paket.X2, new), new)
    print('manifest:', rel, man[rel])


def onizleme(out):
    """Okunurluk denetimi: soğuk koyu (Ötüken gecesi) ve mor-kızıl (Tamu) zeminde 3x büyük çizim, ışıma toplamalı."""
    from PIL import Image
    items = sprites()
    sc = 2
    cols = []
    for n, (r, g, o), tx in items:
        if HD > 1:
            pass
        rr = np.repeat(np.repeat(r, sc, 0), sc, 1) if tx < 8 else r
        gg = np.repeat(np.repeat(g, sc, 0), sc, 1) if tx < 8 else g
        cols.append((n, rr, gg))
    Wt = sum(c[1].shape[1] + 16 for c in cols) + 16
    Ht = max(c[1].shape[0] for c in cols) + 32
    rows = []
    for bgc in ((0.07, 0.09, 0.15), (0.13, 0.06, 0.09)):
        bg = np.zeros((Ht, Wt, 3), np.float32)
        bg[:] = bgc
        x = 16
        for n, r, g in cols:
            h, w = r.shape[:2]
            y = Ht - 16 - h
            a = r[..., 3:4]
            bg[y:y + h, x:x + w] = bg[y:y + h, x:x + w] * (1 - a) + r[..., :3] * a + g[..., :3] * g[..., 3:4] * 0.9
            x += w + 16
        rows.append(bg)
    img = np.concatenate(rows, 0)
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(out)
    print('önizleme', out, img.shape)


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--paketle' in a:
        paketle()
    elif '--onizleme' in a:
        onizleme(a[a.index('--onizleme') + 1])
    else:
        export()
