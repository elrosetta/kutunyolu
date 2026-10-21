"""v39: Bürküt (kimlik burkut) — Ötüken bozkır efsanelerinin dev altın kartalı (yapay zekâ: dalıcı / swooper, UÇAN).

Kam türkülerindeki "Bürküt" göğün katlarına kam ruhunu taşıyan dev berkuttur. Koyu çikolata kahvesi tüyler, ensede ve
boyunda altın-kehribar yele tüyleri (hackle), açık renkli ve çizgili (barlı) uçuş tüyleri, iri sarı çengel gaga ve ışıyan
kehribar göz (ışıma sayfası). Paçalı (tüylü) bacaklar, iri sarı parmaklar ve kara pençeler. Yakın bacağa kam çaputları
(kızıl / ak bez şeritler) ve küçük tunç çıngırak bağlı.

Satırlar (hücre 104 x 96 dünya, ayak / orijin (48, 66) = gövdenin altı ortası, doku 4):
  fly 8 (döngü: güçlü kanat çırpışı, ucan_v29.flap), hurt 3,
  atk_swoop 8 (mk: hazırlıkta yükselip şahlanır, kanatlar tepede, pençeler toplanır, göz alevlenir; temas = pençeler
               ÖNE uzanmış yatay pike, kanatlar geriye süpürülmüş, hız çizgileri; toparlanma = büyük yukarı çırpış),
  atk_feathers 8 (mk: hazırlıkta kanatlar geniş açılıp öne çanaklanır, tüyler kabarır; temas = sert aşağı vuruş ve
               kanatlardan fırlayan 5 tüy; toparlanma).
Çapalar her karede: 'mouth' (gaga ucu), 'hand' (pençelerin ortası).
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_leg, lerp2
import yaratik_ink_kit as yk
import ucan_v29 as u29
from ucan_v29 import pose_at, flap

TEX = 4.0
CELL = (416, 384)       # dünya 104 x 96 (kanat açıklığı sığsın)
FEET = (192, 264)       # dünya (48, 66): gövde kutusunun (36 x 26) alt ortası

# ------------------------------------------------------------------ malzemeler
BROWN = Ink('#6a4329', '#2e1810', '#9a6a40', '#170b07', kind='fur', name='çikolata tüy')
BROWN_D = Ink('#4a2e1e', '#22120c', '#6e4a30', '#100806', name='uzak tüy')
GOLDN = Ink('#d29a36', '#7a4a18', '#f6d27a', '#3e220a', kind='fur', name='altın yele')
COVW = Ink('#5e3a24', '#2a160e', '#8c6040', '#140a06', kind='fur', name='kanat örtüsü')
FLIGHT = Ink('#b8a68c', '#5e5060', '#e8dcc4', '#34283a', name='açık uçuş tüyü')
BAR = (0.24, 0.16, 0.12)
LEGF = Ink('#7e5436', '#38200f', '#b08050', '#1a0c06', kind='fur', name='paça')
TAILF = Ink('#8a6a4c', '#3e2a24', '#c0a07a', '#1e1210', name='kuyruk tüyü')
BEAK = Ink('#f0c23a', '#9a6412', '#fff0a0', '#4a2e08', name='gaga')
BEAK_TIP = (0.2, 0.18, 0.2)
FOOT = Ink('#e8b832', '#8e5a14', '#fde68a', '#40280a', name='parmak')
CLAW = Ink('#1e1a20', '#0a080c', '#4a4048', name='pençe')
BRONZE = Ink('#c08a40', '#62381c', '#f6d890', '#341e0e', kind='metal', name='tunç')
RIB = ((0.82, 0.16, 0.14), (0.95, 0.92, 0.84), (0.82, 0.16, 0.14), (0.95, 0.92, 0.84))
EYE = (1.0, 0.78, 0.25)
EYE_HOT = (1.0, 0.95, 0.7)
EYE_GLOW = (1.0, 0.5, 0.05)

C0 = (0.0, -14.0)        # gövde merkezi (dönüşüm pivotu)


# ------------------------------------------------------------------ parçalar
def _bars(cv, w, z, cl, mat_col=BAR, k=(0.45, 0.68, 0.88)):
    """Uçuş tüylerinin (ikinciller) üstünde çizgiler: kemik çizgisine paralel, tüy bölgesine kırpılmış."""
    E, Wr, tr = w['elbow'], w['wrist'], w['trail']
    reg = cv.blob([E, Wr, u29.add(Wr, tr, cl * 0.98), u29.add(E, tr, cl * 0.9)])
    strokes = []
    for kk in k:
        a = u29.add(E, tr, cl * kk * 0.92)
        b = u29.add(Wr, tr, cl * kk)
        strokes.append(ik.taper_path([cv.W(a), cv.W(lerp2(a, b, 0.5)), cv.W(b)], cv.px(1.6), (0.1, 0.1)))

    def draw(c):
        import skia
        for s in strokes:
            c.drawPath(s, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(mat_col[0], mat_col[1], mat_col[2], 0.8)))
    yk.clipped(cv, reg, z, draw)


def _wing(cv, p, near):
    s, fold, spread, lag = p['ws'], p['wf'], p['wsp'], p['wl']
    sweep = p['sweep']
    ph = p['ph']
    if near:
        S = (2.0, -20.0)
        mats = (COVW, FLIGHT, BAR)
        L, ch, z = 40.0, 13.5, 12.0
    else:
        S = (5.5, -22.0)
        s = max(-1.0, min(1.0, s * 0.92 + 0.05))
        mats = (COVW.darker(0.62), FLIGHT.darker(0.6), BAR)
        L, ch, z = 35.0, 12.0, -12.0
    w = u29.feather_wing(cv, S, s, fold, spread, L, ch, lag, mats, z=z, near=near, sweep=sweep, seed=3 if near else 4,
                         ph=ph + (0.0 if near else 0.6), n_pri=6)
    _bars(cv, w, z + 0.15, ch * (1.0 - 0.25 * fold), BAR if near else (0.12, 0.08, 0.08))
    return w


def _tail(cv, p):
    """Kuyruk yelpazesi: gövdenin arkasında 7 tüy; tsp = açılma (hazırlıkta yelpaze), tl = kaldırma."""
    root = (-13.0, -13.5)
    sp = p['tsp']
    base_a = math.pi + 0.12 - p['tl'] - p['rot'] * 0.3
    n = 7
    for k in range(n):
        u = k / (n - 1) - 0.5
        a = base_a + u * (0.35 + 0.55 * sp) + math.sin(p['ph'] + k) * 0.02
        ln = 18.0 - abs(u) * 4.0
        tip = (root[0] + math.cos(a) * ln, root[1] + math.sin(a) * ln)
        nx, ny = -math.sin(a), math.cos(a)
        wd = 2.0
        q0 = (root[0] + nx * wd * 0.6, root[1] + ny * wd * 0.6)
        q1 = (root[0] - nx * wd * 0.6, root[1] - ny * wd * 0.6)
        m1 = lerp2(root, tip, 0.75)
        pts = [q0, (m1[0] + nx * wd, m1[1] + ny * wd), (tip[0] + nx * wd * 0.6, tip[1] + ny * wd * 0.6), (tip[0] - math.cos(a) * -0.6, tip[1] - math.sin(a) * -0.6),
               (tip[0] - nx * wd * 0.6, tip[1] - ny * wd * 0.6), (m1[0] - nx * wd, m1[1] - ny * wd), q1]
        det = [('ink', [lerp2(root, tip, 0.15), lerp2(root, tip, 0.9)], 0.7, (0.2, 0.6))]
        for kk in (0.45, 0.62, 0.86):   # çizgiler: uçta kalın koyu kuşak
            q = lerp2(root, tip, kk)
            det.append(('stroke', [(q[0] + nx * 2.4, q[1] + ny * 2.4), (q[0] - nx * 2.4, q[1] - ny * 2.4)], 2.4 if kk > 0.8 else 1.4, BAR, (0.0, 0.0)))
        zz = -6.0 + (n - abs(k - (n - 1) / 2)) * 0.01 + (0.2 if k > n // 2 else 0.0)
        cv.shape(cv.blob(pts), TAILF if k >= n // 2 else TAILF.darker(0.75), z=zz, sd=0.8, hi=0.25, ol=0.8, details=det)


def _foot(cv, f, ang, opn, mat, cm, z):
    """Sarı pullu parmaklar + kara pençeler. ang: ayağın baktığı yön (rad, 0 = ileri), opn 0 kapalı yumruk .. 1 açık."""
    tips = []
    ca, sa = math.cos(ang), math.sin(ang)

    def R(x, y):
        return (f[0] + x * ca - y * sa, f[1] + x * sa + y * ca)
    cv.shape(cv.ellipse(f, 1.8, 1.5, ang), mat, z=z, sd=0.5, hi=0.25, ol=0.8)
    # üç ön parmak (yelpaze) + arka başparmak
    for j, (da, ln) in enumerate(((-0.55, 5.0), (0.0, 5.8), (0.55, 4.8), (math.pi - 0.2, 3.8))):
        a = da * (0.35 + 0.65 * opn) if j < 3 else da - (1 - opn) * 0.9
        cur = (1.0 - opn) * 1.3 + 0.25
        m = R(math.cos(a) * ln * 0.55, math.sin(a) * ln * 0.55)
        e = R(math.cos(a + cur * (1 if j < 3 else -1) * 0.5) * ln, math.sin(a + cur * (1 if j < 3 else -1) * 0.5) * ln)
        cv.shape(cv.limb([f, m, e], [1.1, 1.0, 0.85]), mat, z=z + 0.1 + j * 0.01, sd=0.4, hi=0.2, ol=0.75,
                 details=[('ink', [lerp2(f, m, 0.7), lerp2(m, e, 0.3)], 0.6, (0.3, 0.3))])
        # kara çengel pençe
        d = u29.norm2((e[0] - m[0], e[1] - m[1]))
        bend = (1 if j < 3 else -1)
        tip = u29.add(e, u29.rot2(d, 1.1 * bend), 2.5)
        mid = u29.add(e, u29.rot2(d, 0.4 * bend), 1.4)
        cv.shape(cv.blob([u29.add(e, (-d[1], d[0]), 0.8), mid, (tip[0], tip[1], 0.0), u29.add(e, (d[1], -d[0]), 0.8)]), cm, z=z + 0.2 + j * 0.01,
                 sd=0.3, hi=0.15, ol=0.7)
        tips.append(tip)
    return tips


def _leg(cv, p, near):
    hip = (3.5, -8.0) if near else (6.0, -9.0)
    a1, a2 = p['leg'] if near else p['legb']
    k, f = fk_leg(hip, a1, a2, 6.5, 6.0)
    m = BROWN if near else BROWN_D
    fm = FOOT if near else FOOT.darker(0.7)
    cm = CLAW if near else CLAW.darker(0.8)
    z = 8.0 if near else -9.0
    # paça: kalın tüylü uyluk + incik (ucunda tüy saçağı)
    thigh = cv.limb([hip, lerp2(hip, k, 0.5), k, lerp2(k, f, 0.75)], [3.6, 3.2, 2.4, 1.7])
    dd = u29.norm2((f[0] - k[0], f[1] - k[1]))
    nn = (-dd[1], dd[0])
    fr = [cv.blob([u29.add(lerp2(k, f, 0.55), nn, s * 1.6), u29.add(u29.add(lerp2(k, f, 0.95), dd, 0.8), nn, s * 1.4 + 0.6 * s), u29.add(lerp2(k, f, 0.8), nn, -s * 0.2)])
          for s in (-1, 1)]
    det = [('ink', [lerp2(hip, k, 0.3), lerp2(hip, k, 0.7), lerp2(k, f, 0.3)], 1.0, (0.3, 0.5))] if near else []
    cv.shape(ik.union(thigh, *fr), LEGF if near else BROWN_D, z=z, sd=1.8, hi=0.3 if near else 0.0, details=det, fur=0.7 if near else 0.0)
    fang = math.atan2(dd[1], dd[0]) - math.pi * 0.5 + p['fang']
    tips = _foot(cv, f, fang, p['claw'], fm, cm, z + 0.5)
    if near:
        _ribbons(cv, lerp2(k, f, 0.55), p, z + 1.0)
    return f, tips


def _ribbons(cv, at, p, z):
    """Kam çaputları (kızıl / ak bez şeritler) + küçük tunç çıngırak; rüzgârla geriye savrulur (wind: hız)."""
    ph = p['ph']
    wind = p['wind']
    cv.shape(cv.capsule((at[0] - 1.5, at[1] - 0.6), (at[0] + 1.6, at[1] + 0.4), 0.9, 0.9), Ink(RIB[0]), z=z + 0.3, sd=0.3, ol=0.7)
    for k in range(4):
        col = RIB[k]
        a = math.pi * (0.72 + 0.18 * wind) + (k - 1.5) * 0.14
        L = 6.5 + (k % 2) * 2.5 + wind * 3.0
        pts = [at]
        x, y = at
        for j in range(4):
            aa = a + math.sin(ph * 2 + k * 1.3 + j * 1.1) * (0.25 + 0.2 * wind) + j * 0.08
            x += math.cos(aa) * L / 4
            y += math.sin(aa) * L / 4
            pts.append((x, y))
        cv.shape(ik.taper_path([cv.W(q) for q in pts], cv.u(1.3), prof=lambda u: 1.0 if u < 0.85 else 0.4),
                 Ink(col), z=z + k * 0.01, sd=0.35, ol=0.65)
    # çıngırak: kısa ipte sarkar
    sw = math.sin(ph * 2 + 0.7) * 0.4 - wind * 0.5
    bq = (at[0] + math.sin(sw) * 2.4, at[1] + math.cos(sw) * 2.4)
    cv.stroke([at, bq], 0.8, z=z + 0.4, col=(0.3, 0.22, 0.18), taper=(0.0, 0.0))
    cv.shape(cv.ellipse((bq[0], bq[1] + 1.0), 1.25, 1.15), BRONZE, z=z + 0.5, sd=0.4, hi=0.3, ol=0.75,
             details=[('ink', [(bq[0] - 0.8, bq[1] + 1.4), (bq[0] + 0.8, bq[1] + 1.4)], 0.7, (0.1, 0.1))])


def _body(cv, p):
    rf = p['ruff']
    body = cv.blob([(-16.0, -15.0), (-9.0, -19.5), (0.0, -22.0), (7.0, -23.0), (12.0, -20.5), (14.0, -16.0), (12.0, -10.5),
                    (6.0, -6.5), (-2.0, -6.0), (-10.0, -9.0), (-16.5, -12.5)])
    det = []
    # göğüs / karın pul tüyleri (mürekkep yaylar)
    for r, (y0, n) in enumerate(((-17.0, 3), (-13.5, 4), (-10.0, 3))):
        for i in range(n):
            x = 10.5 - i * 4.2 - r * 1.6
            y = y0 + i * 0.9
            det.append(('ink', [(x - 1.6, y), (x - 0.2, y + 1.3), (x + 1.2, y + 0.2)], 0.9, (0.2, 0.4)))
    det += cv.fold([(-11.0, -17.0), (-4.0, -15.0), (2.0, -9.5)], 0.8, 1.1, 1)
    cv.shape(body, BROWN, z=0, sd=3.0, hi=0.5, details=det, bounce=0.3, fur=0.9)
    if rf > 0.05:   # kabaran tüyler: sırt ve göğüs kenarında dikilen sivri uçlar
        tufts = []
        for (x, y, a) in ((-12.0, -18.0, -2.3), (-7.0, -21.5, -2.0), (-2.0, -23.0, -1.8), (12.5, -12.0, 0.4), (9.0, -7.0, 0.9), (4.0, -4.5, 1.3)):
            ln = 2.6 * rf
            tufts.append(cv.blob([(x - math.sin(a) * 1.2, y + math.cos(a) * 1.2), (x + math.cos(a) * ln, y + math.sin(a) * ln, 0.0),
                                  (x + math.sin(a) * 1.2, y - math.cos(a) * 1.2)]))
        cv.shape(ik.union(*tufts), BROWN, z=-0.5, sd=0.8, ol=0.8)


def _head(cv, p):
    """Boyun yelesi (altın hackle) + baş + çengel gaga + kehribar göz. Döner: gaga ucu."""
    hdx, hdy = p['hd']
    hr = p['hr']
    nb = (8.0, -19.0)
    H = (16.0 + hdx, -24.5 + hdy)
    u29.body_xf(cv, nb, hr, 1.0, 1.0, (0.0, 0.0))
    ph = p['ph']
    rf = p['ruff'] + p['hack']
    # yele: başın tepesinden enseye, ensede omuza dökülen sivri altın mızrak tüyler (uçları geriye-aşağı)
    nape = [(H[0] - 1.0, H[1] - 3.6), (H[0] + 2.5, H[1] - 3.8), (H[0] + 4.2, H[1] - 2.2), (H[0] + 3.0, H[1] + 0.2),
            (H[0] + 2.5, H[1] + 3.0), (13.0, -14.0), (11.0, -12.5)]
    edge = yk.ragged((11.0, -12.5), (H[0] - 4.0 - rf * 1.2, H[1] - 2.8 - rf * 0.6), 8, 1.8 + 1.6 * rf, seed=5, side=-1.0)
    hdet = []
    for j in range(4):
        x0 = H[0] - 1.5 - j * 1.9
        y0 = H[1] - 1.5 + j * 2.2
        hdet.append(('ink', [(x0 + 1.5, y0 - 0.6), (x0, y0 + 1.0), (x0 - 1.6, y0 + 1.8)], 0.85, (0.1, 0.8)))
        hdet.append(('stroke', [(x0 + 1.8, y0 - 1.3), (x0 + 0.2, y0 + 0.2)], 1.2, GOLDN.hi, (0.3, 0.6)))
    cv.shape(cv.blob(nape + edge + [(H[0] - 4.5 - rf * 1.2, H[1] - 3.0 - rf * 0.6, 0.0)]), GOLDN, z=14, sd=1.8, hi=0.5, details=hdet,
             fur=0.5, cast=0.6)
    # baş: yassı tepe, öne doğru sivrilen yüz; yüz / gerdan koyu
    head = cv.blob([(H[0] - 2.0, H[1] - 3.4), (H[0] + 2.5, H[1] - 3.9), (H[0] + 5.2, H[1] - 2.4), (H[0] + 6.0, H[1] + 0.2),
                    (H[0] + 4.6, H[1] + 2.6), (H[0] + 1.0, H[1] + 3.4), (H[0] - 1.6, H[1] + 1.4)])
    cv.shape(head, GOLDN, z=15, sd=1.4, hi=0.45, fur=0.3,
             details=[('col', cv.blob([(H[0] + 0.2, H[1] + 0.2), (H[0] + 3.0, H[1] - 0.6), (H[0] + 6.2, H[1] - 0.2), (H[0] + 5.0, H[1] + 2.8), (H[0] + 0.5, H[1] + 3.6)]),
                       BROWN.base),
                      ('ink', [(H[0] + 0.6, H[1] + 1.4), (H[0] + 3.4, H[1] + 1.2)], 0.8, (0.3, 0.6))])
    # gaga: üst çene iri çengel, alt çene jaw ile açılır
    jaw = p['jaw']
    bb = (H[0] + 5.0, H[1] - 1.0)
    _B = lambda x, y: (bb[0] + x * 0.82, bb[1] + y * 0.82)   # gaga ölçeği
    piv = _B(-0.3, 1.6)
    lo = [u29.add(piv, u29.rot2((x - piv[0], y - piv[1]), jaw * 0.55)) for (x, y) in
          (_B(-0.2, 1.4), _B(4.6, 2.4), _B(6.4, 2.6), _B(4.2, 3.4), _B(-0.2, 3.0))]
    if jaw > 0.1:
        cv.fill(cv.blob([(bb[0], bb[1] + 1.5), _B(6.0, 2.6), lo[2], lo[0]]), (0.55, 0.12, 0.1), z=15.8)
    cv.shape(cv.blob([lo[0], lo[1], (lo[2][0], lo[2][1], 0.0), lo[3], lo[4]]), BEAK.darker(0.85), z=15.9, sd=0.5, hi=0.2, ol=0.85)
    tip = _B(8.0, 4.6)
    up = cv.blob([_B(-0.6, -2.0), _B(2.8, -2.4), _B(6.2, -1.0), _B(8.4, 1.8), (tip[0], tip[1], 0.0),
                  _B(6.6, 2.4), _B(3.0, 1.8), _B(-0.4, 1.6)])
    tipr = cv.blob([_B(6.6, -0.8), _B(8.6, 1.6), (tip[0], tip[1]), _B(6.4, 2.6)])
    cv.shape(up, BEAK, z=16, sd=1.0, hi=0.4, details=[('col', tipr, BEAK_TIP), ('ink', [_B(0.8, 1.4), _B(4.0, 1.6), _B(6.6, 2.4)], 0.9, (0.2, 0.3)),
                                                     ('stroke', [_B(1.4, -1.6), _B(5.6, -1.0)], 1.0, BEAK.hi, (0.3, 0.6))])
    # mum (cere) + burun deliği
    cv.shape(cv.blob([_B(-1.2, -2.2), _B(1.6, -2.4), _B(1.8, 1.6), _B(-1.0, 1.8)]), FOOT, z=16.2, sd=0.4, ol=0.7,
             details=[('col', cv.ellipse(_B(0.6, -0.6), 0.5, 0.35), INK)])
    # göz: kaş çıkıntısı altında ışıyan kehribar
    ey = p['eye']
    sq = p['squint']
    ec = (H[0] + 1.6, H[1] - 1.4)
    cv.fill(cv.ellipse(ec, 1.6, 1.25 * (1 - 0.6 * sq)), INK, z=17)
    yk.eye_glow(cv, ec, 1.05, 0.85 * (1 - 0.7 * sq), 0.0, EYE if ey < 0.5 else EYE_HOT, EYE_GLOW, 17.5, halo=2.0 + 1.6 * ey, halo_a=0.35 + 0.45 * ey)
    cv.fill(cv.ellipse((ec[0] + 0.3, ec[1]), 0.42, 0.42 * (1 - 0.7 * sq)), INK, z=17.8)
    # kaş: sert çatık çıkıntı
    brow = cv.blob([(ec[0] - 2.6, ec[1] - 1.2), (ec[0] + 0.5, ec[1] - 2.4 + sq * 0.6), (ec[0] + 3.4, ec[1] - 1.0), (ec[0] + 2.6, ec[1] - 0.3), (ec[0] - 0.5, ec[1] - 0.9)])
    cv.shape(brow, BROWN, z=18, sd=0.6, ol=0.85)
    if ey > 0.4:   # alevlenme izi: gözün arkasına uzanan ışık çizgisi
        cv.stroke([(ec[0] + 0.4, ec[1]), (ec[0] - 3.5 * ey, ec[1] - 0.8 * ey)], 1.0 + ey, z=18.5, col=EYE_HOT, taper=(0.1, 0.9), glow=EYE_GLOW)
    mouth = u29.to_world(cv, tip)
    cv.pop()
    return mouth


def _flung(cv, p):
    """Fırlatılan tüyler: kanattan öne-aşağı uçan 5 küçük tüy + arkalarında kısa hız izi (dünya uzayı)."""
    k = p['fling']
    if k <= 0.02:
        return
    rng = np.random.default_rng(21)
    for i in range(5):
        st = (-2.0 + rng.uniform(-5, 5), -4.0 + rng.uniform(-6, 6))
        a = rng.uniform(-0.3, 0.4)
        dist = (12.0 + rng.uniform(4, 22)) * k
        q = (st[0] + math.cos(a) * dist + 10.0 * k, st[1] + math.sin(a) * dist)
        d = (math.cos(a), math.sin(a))
        L = 4.8
        nx, ny = -d[1], d[0]
        tip = u29.add(q, d, L)
        tail = u29.add(q, d, -L)
        vane = cv.blob([tail, u29.add(u29.add(q, d, -0.6), (nx, ny), 1.6), (tip[0], tip[1], 0.0), u29.add(u29.add(q, d, -0.4), (nx, ny), -1.3)])
        yk.glow_soft(cv, q, 3.5, EYE_GLOW, z=39.5, alpha=0.35)
        cv.shape(vane, GOLDN if i % 2 else FLIGHT, z=40 + i * 0.01, sd=0.5, hi=0.3, ol=0.9, glow=(0.3, 0.14, 0.0),
                 details=[('ink', [tail, tip], 0.6, (0.0, 0.6)), ('stroke', [lerp2(tail, tip, 0.4), u29.add(lerp2(tail, tip, 0.55), (nx, ny), 0.9)], 0.8, BAR, (0.2, 0.2))])
        for o in (-0.8, 0.8):
            b0 = u29.add(u29.add(tail, d, -0.5), (nx, ny), o)
            cv.stroke([b0, u29.add(b0, d, -7.0 * k - 3.0)], 1.4, z=39, col=(1.0, 0.85, 0.5), taper=(0.1, 0.95), alpha=0.75, glow=(0.3, 0.14, 0.0))


def draw(cv, p):
    off = p['off']
    if p['streak'] > 0.02:
        d = p.get('sdir', (1.0, 0.0))
        u29.speed_lines(cv, (off[0] - 10.0, C0[1] + off[1]), d, n=7, L=24.0 * p['streak'], spread=26.0, w=1.8,
                        col=(0.85, 0.75, 0.55), alpha=0.55 * min(1.0, p['streak']), z=-40, seed=int(p['t'] * 40) + 3)
    if p['zirh'] > 0:
        u29.armor_aura(cv, (C0[0] + off[0], C0[1] + off[1]), 26.0, p['zirh'], z=-45, seed=3)
    u29.body_xf(cv, C0, p['rot'], p['sx'], p['sy'], off)
    _wing(cv, p, False)
    _leg(cv, p, False)
    _tail(cv, p)
    _body(cv, p)
    f, tips = _leg(cv, p, True)
    _wing(cv, p, True)
    mouth = _head(cv, p)
    hand = u29.to_world(cv, (sum(t[0] for t in tips[:3]) / 3, sum(t[1] for t in tips[:3]) / 3))
    cv.pop()
    _flung(cv, p)
    if p['loose'] > 0:   # acı: kopan tüyler
        u29.flecks(cv, (C0[0] + off[0], C0[1] + off[1] - 2), 6, 6.0, 16.0, BROWN, 50, seed=int(p['t'] * 30) + 2, s0=0.6, s1=1.3,
                   drift=(-1.0, -0.4), dk=6.0 * p['loose'])
    return {'mouth': mouth, 'hand': hand}


# ================================================================== animasyon
REST = dict(t=0.0, ws=0.0, wf=0.0, wsp=0.5, wl=0.0, sweep=0.35, bob=0.0, rot=0.0, sx=1.0, sy=1.0, off=(0.0, 0.0),
            hd=(0.0, 0.0), hr=0.0, jaw=0.0, eye=0.0, squint=0.0, ruff=0.0, hack=0.0, tsp=0.2, tl=0.0,
            leg=(-1.25, 0.35), legb=(-1.35, 0.3), claw=0.2, fang=0.0, wind=0.5, streak=0.0, fling=0.0, loose=0.0, zirh=0.0)


def _fly(t):
    w, bob = flap(t, down=0.45, top=-0.86, bot=0.8, fold_max=0.85, bob_amp=2.0)
    s = math.sin(math.tau * t)
    return dict(REST, t=t, **w, off=(0.0, bob), rot=-0.04 + 0.05 * math.sin(math.tau * (t - 0.15)), hd=(0.3 * s, -0.4 * bob * 0.3),
                hr=-0.03 * s, tsp=0.25 + 0.1 * s, tl=0.06 * math.sin(math.tau * (t - 0.3)), wind=0.6,
                leg=(-1.25 + 0.06 * s, 0.35), legb=(-1.35 + 0.06 * s, 0.3))


def _K(keys):
    return lambda t: pose_at(t, keys, base=REST)


_SW_TS = [0.0, 0.12, 0.24, 0.36, 0.48, 0.56, 0.7, 0.85]
_SWOOP = [
    (0.0, dict(ws=-0.2, wf=0.1, wsp=0.5, wl=-0.3, rot=-0.12, off=(-1.0, -1.0), eye=0.2, leg=(-0.9, -1.5), tsp=0.3), 'l'),
    (0.12, dict(ws=-0.75, wf=0.15, wsp=0.7, wl=-0.6, rot=-0.28, off=(-3.0, -2.0), hd=(-0.5, -0.5), hr=0.05, eye=0.6, leg=(-0.2, -2.0), legb=(-0.3, -1.9),
                claw=0.0, tsp=0.6, tl=-0.15, hack=0.4, jaw=0.2), 'o'),
    (0.24, dict(ws=-0.92, wf=0.05, wsp=0.95, wl=-0.2, rot=-0.38, off=(-5.0, -2.5), hd=(-1.0, -0.8), hr=0.1, eye=1.0, leg=(0.1, -2.3), legb=(0.0, -2.2),
                tsp=1.0, tl=-0.3, hack=1.0, jaw=0.45, zirh=0.0), 'o'),
    (0.36, dict(ws=-0.95, wf=0.0, wsp=1.0, wl=0.0, rot=-0.42, off=(-5.5, -3.0), hd=(-1.2, -1.0), eye=1.0, jaw=0.5), 'io'),
    (0.48, dict(ws=0.05, wf=0.45, wsp=0.3, wl=0.8, sweep=1.5, rot=0.22, off=(1.0, -1.0), hd=(1.0, 0.6), hr=-0.05, eye=1.0, leg=(0.9, -0.6), legb=(0.8, -0.7),
                claw=0.6, tsp=0.2, tl=0.1, hack=0.6, jaw=0.3, streak=0.6, sx=1.04, sy=0.97, wind=1.0), 'i'),
    (0.56, dict(ws=-0.05, wf=0.55, wsp=0.2, wl=0.5, sweep=2.1, rot=0.04, off=(8.0, 1.5), hd=(1.6, 0.8), hr=-0.08, leg=(1.55, -0.15), legb=(1.4, -0.25),
                claw=1.0, fang=0.3, tsp=0.1, jaw=0.6, streak=1.0, sx=1.08, sy=0.94), 'o'),
    (0.70, dict(ws=-0.35, wf=0.35, wsp=0.5, wl=-0.5, sweep=1.0, rot=-0.06, off=(9.0, 1.0), leg=(1.35, -0.4), legb=(1.2, -0.5), claw=0.0, fang=0.1,
                streak=0.5, sx=1.02, sy=0.98, eye=0.6, jaw=0.2), 'o'),
    (0.85, dict(ws=-0.9, wf=0.35, wsp=0.85, wl=-0.8, sweep=0.35, rot=-0.16, off=(4.0, -1.0), hd=(0.0, -0.3), leg=(0.2, -1.4), legb=(0.1, -1.3), claw=0.1,
                fang=0.0, streak=0.0, sx=1.0, sy=1.0, eye=0.3, jaw=0.0, hack=0.2, tsp=0.5), 'io'),
    (1.0, dict(ws=0.3, wf=0.05, wsp=0.5, wl=0.6, rot=-0.04, off=(1.0, 0.5), leg=(-0.8, -1.4), legb=(-0.9, -1.3), eye=0.1, hack=0.0, tsp=0.3), 'io'),
]

_FE_TS = [0.0, 0.12, 0.24, 0.36, 0.48, 0.56, 0.7, 0.85]
_FEATH = [
    (0.0, dict(ws=0.0, wf=0.1, wsp=0.5, rot=-0.04, eye=0.1), 'l'),
    (0.12, dict(ws=-0.6, wf=0.05, wsp=0.85, wl=-0.4, sweep=0.0, rot=-0.14, off=(-1.5, -1.5), ruff=0.5, hack=0.4, eye=0.5, tsp=0.6, jaw=0.2), 'o'),
    (0.24, dict(ws=-0.38, wf=0.0, wsp=1.0, wl=0.0, sweep=-0.5, rot=-0.2, off=(-3.0, -0.5), hd=(-0.8, -0.4), ruff=1.0, hack=1.0, eye=1.0, tsp=1.0,
                tl=-0.2, jaw=0.55, leg=(-0.5, -1.6)), 'o'),
    (0.36, dict(ws=-0.32, wsp=1.0, sweep=-0.62, rot=-0.24, off=(-3.5, -0.5), hd=(-1.0, -0.5), ruff=1.1, hack=1.1, eye=1.0, jaw=0.6), 'io'),
    (0.48, dict(ws=0.55, wf=0.0, wsp=0.35, wl=1.0, sweep=0.1, rot=0.06, off=(0.0, -1.0), hd=(0.6, 0.3), ruff=0.6, hack=0.6, jaw=0.4), 'i'),
    (0.56, dict(ws=0.82, wf=0.0, wsp=0.6, wl=0.7, sweep=0.35, rot=0.1, off=(1.5, -3.0), hd=(1.0, 0.4), ruff=0.3, fling=0.35, jaw=0.7, eye=0.8, tsp=0.5), 'o'),
    (0.70, dict(ws=0.7, wf=0.15, wsp=0.5, wl=0.2, rot=0.06, off=(1.0, -2.0), ruff=0.15, fling=0.8, jaw=0.4, eye=0.5), 'o'),
    (0.85, dict(ws=-0.6, wf=0.7, wsp=0.8, wl=-0.8, sweep=0.35, rot=-0.06, off=(0.0, 0.5), ruff=0.0, hack=0.1, fling=0.0, jaw=0.0, eye=0.2, tsp=0.3, tl=0.0,
                leg=(-1.0, -1.4)), 'io'),
    (1.0, dict(ws=0.2, wf=0.1, wsp=0.5, wl=0.4, rot=-0.04, off=(0.0, 0.0), eye=0.1), 'io'),
]

_HURT = [
    (0.0, dict(ws=-0.85, wf=0.3, wsp=1.0, wl=-0.8, rot=-0.3, off=(-4.0, -1.0), hd=(-1.5, 0.5), hr=0.25, squint=1.0, jaw=0.8, ruff=0.8, tsp=0.9, tl=-0.25,
               leg=(0.4, -1.0), legb=(0.3, -0.9), claw=1.0, loose=0.6, sx=0.96, sy=1.04), 'l'),
    (0.5, dict(ws=-0.4, wf=0.6, wsp=0.8, wl=-0.4, rot=-0.18, off=(-5.0, 0.5), hd=(-0.8, 0.3), hr=0.12, squint=0.6, jaw=0.4, ruff=0.4, tsp=0.6,
               leg=(-0.2, -1.2), legb=(-0.3, -1.1), claw=0.6, loose=1.0, sx=1.0, sy=1.0), 'o'),
    (1.0, dict(ws=0.4, wf=0.2, wsp=0.5, wl=0.5, rot=-0.06, off=(-3.0, 0.5), hd=(0.0, 0.0), hr=0.0, squint=0.2, jaw=0.1, ruff=0.0, tsp=0.3, tl=0.0,
               leg=(-0.9, -1.4), legb=(-1.0, -1.3), claw=0.2, loose=1.4), 'io'),
]


def _row(frames, fps, loop, pose, ts=None, mk=None, vx=None):
    return dict(frames=frames, fps=fps, loop=loop, pose=pose, ts=ts, mk=mk, vx=vx)


ROWS = {
    'fly': _row(8, 11, True, _fly),
    'hurt': _row(3, 14, False, _K(_HURT)),
    'atk_swoop': _row(8, 12, False, _K(_SWOOP), ts=_SW_TS, mk=[0.47, 0.56, 0.72]),
    'atk_feathers': _row(8, 12, False, _K(_FEATH), ts=_FE_TS, mk=[0.47, 0.56, 0.74]),
}

DURUM = {"idle": "fly", "chase": "fly", "recover": "fly", "evade": "fly", "_hurt": "hurt", "_hurt_big": "hurt", "_break": "hurt",
         "windup/swoop": "atk_swoop", "act/swoop": "atk_swoop", "recover/swoop": "atk_swoop",
         "windup/feathers": "atk_feathers", "act/feathers": "atk_feathers", "recover/feathers": "atk_feathers"}


def anims_for(var='burkut'):
    return {k: {kk: vv for kk, vv in r.items() if kk != 'pose'} for k, r in ROWS.items()}


def durum_for(var='burkut'):
    return dict(DURUM)


def _frame_time(row, i):
    if row['ts']:
        return row['ts'][i]
    if row['loop']:
        return i / row['frames']
    return i / max(1, row['frames'] - 1)


SHADE = dict(outer=0.5, rim=0.8, rim_col=(0.75, 0.82, 1.0), rim_dir=(0.6, -0.8), rim_w=1.4, form=(5.0, (0.76, 0.72, 0.86)))


def render_frame(anim, i, var='burkut', ss=3):
    row = ROWS[anim]
    tt = _frame_time(row, i)
    p = dict(row['pose'](tt))
    p['t'] = tt
    p['ph'] = tt * math.tau * (1 if row['loop'] else 1.5) + i * 0.7
    cv = u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
