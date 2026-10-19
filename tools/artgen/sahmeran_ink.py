"""Şahmeran Ana — stil v2 "mürekkep-cel" boss (inkkit.py + bosskit.py). v1: creatures3.draw_sahmeran.

Anadolu'nun yılanlar şahı (Şahmeran): belden yukarısı taçlı kadın, belden aşağısı yerde kıvrılan dev yılan gövdesi;
halk resimlerindeki gibi kuyruğunun ucu da bir yılan başıyla biter. Altın pullu göğüslük, zümrüt taşlı yüksek taç,
kolye ve bilezikler; kara saçları beline iner, aralarından küçük yılanlar baş çıkarır; arkasında kobra yelpazesi (göz
desenli, altın kenarlı; hazırlıkta açılır). Gözleri zümrüt gibi yanar (dikey yılan bebeği), parmak uçları altın
pençe. Pullar zümrüt yeşili, sırtta koyu baklava deseni, karın pulları altın-krem; zehir yeşili ışımalar.

Animasyon adları / kare sayıları / fps v1 ile aynı (idle 8, walk 8, windup 4, strike 4, slam 3, cast 3, hurt 2, rage 3);
çapalar 'hand' (yakın el) ve 'mouth'. Hücre dünya 256x176 (v1 200x176), ayak (100, 170).
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
import bosskit as bk
from bosskit import along, add, polar

TEX = bk.TEX
CELL = (1024, 704)
FEET = (436, 680)

SKIN = Ink('#c99a76', '#6a3c4c', '#f2c8a0', '#3a1c2c', name='şahmeran teni')
SKIN_B = SKIN.darker(0.78)
SCALE = Ink('#2e8a5c', '#103c3c', '#62c88a', '#08201e', name='zümrüt pul')
SCALE_B = SCALE.darker(0.75)
BELLY = Ink('#dccb8c', '#8a7444', '#fff2c0', '#4e3e24', name='karın pulu')
GOLD = Ink('#e6b44a', '#8a4e1c', '#fff0b4', '#4a2a10', kind='metal', name='altın')
GOLD_B = GOLD.darker(0.75)
HAIR = Ink('#1c2622', '#0a100e', '#3e5a4e', '#050807', name='kara saç')
HOOD = Ink('#1a4638', '#0a2220', '#2f6e54', '#051210', name='kobra yelpazesi')
LIP = (0.42, 0.1, 0.18)
GEM = (0.3, 1.0, 0.55)
GEM_GLOW = (0.15, 0.9, 0.35)
EYE = (0.55, 1.0, 0.45)
EYE_GLOW = (0.25, 0.95, 0.3)
VENOM = (0.55, 1.0, 0.35)
MOUTH_IN = (0.3, 0.06, 0.12)

L_UP, L_FO = 15.5, 14.5
WS = 1.3          # kadın gövdesinin ölçeği (yılan gövdesine göre heybetli kraliçe)


def _base(**kw):
    d = dict(wx=10.0, wy=-50.0, lean=0.08, wv=0.0, arm=0.5, el=0.7, arm_b=0.35, el_b=0.8, mouth=0.0, glow=0.6, ht=0.0,
             hood=0.5, orb=0.0, claw=0.3, tail=0.0, slide=0.0, hair=0.0, rise=0.0)
    d.update(kw)
    return d


def _idle(i):
    t = i / 8
    s = math.sin(t * math.tau)
    return _base(wy=-50.0 + 1.5 * s, wx=10.0 + 0.8 * math.sin(t * math.tau + 0.6), lean=0.08 + 0.03 * s, wv=t * math.tau,
                 arm=0.55 + 0.05 * s, el=0.75, arm_b=0.35 - 0.04 * s, glow=0.55 + 0.35 * (0.5 + 0.5 * math.sin(t * math.tau * 2)),
                 ht=0.03 * s, hood=0.45 + 0.05 * s, hair=s)


def _walk(i):
    t = i / 8
    s = math.sin(t * math.tau * 2)
    return _base(wy=-49.0 + 1.2 * s, wx=13.0, lean=0.18, wv=t * math.tau * 2, arm=0.6, el=0.8, arm_b=0.5, el_b=0.7,
                 glow=0.7, hood=0.4, hair=math.sin(t * math.tau * 2 + 1.0) + 0.6, slide=1.0, ht=0.05)


def _windup(i):
    # dikilir: gövde yükselir ve geriye çekilir, yelpaze açılır, pençeler kalkar, ağız açık (son kare tutulur)
    return bk.pick(i, [
        _base(wy=-56.0, wx=7.0, lean=0.0, wv=0.5, arm=1.2, el=1.0, arm_b=1.0, el_b=1.0, mouth=0.3, glow=0.8, hood=0.7, claw=0.7, rise=0.3),
        _base(wy=-64.0, wx=3.0, lean=-0.12, wv=1.0, arm=1.6, el=1.0, arm_b=1.8, el_b=1.1, mouth=0.6, glow=0.9, hood=0.9, claw=1.0, ht=-0.1, rise=0.6, hair=-0.5),
        _base(wy=-70.0, wx=-1.0, lean=-0.22, wv=1.4, arm=1.75, el=1.15, arm_b=2.2, el_b=1.1, mouth=0.9, glow=1.0, hood=1.0, claw=1.0, ht=-0.18, rise=0.9, hair=-1.0),
        _base(wy=-72.0, wx=-2.0, lean=-0.26, wv=1.6, arm=1.8, el=1.2, arm_b=2.3, el_b=1.1, mouth=1.0, glow=1.0, hood=1.0, claw=1.0, ht=-0.2, rise=1.0, hair=-1.2),
    ])


def _strike(i):
    # atılış: üst gövde öne fırlar (yılan gibi), iki pençe ileri, kuyruk geride kamçılanır
    return bk.pick(i, [
        _base(wy=-56.0, wx=24.0, lean=0.55, wv=2.0, arm=1.7, el=0.3, arm_b=1.5, el_b=0.4, mouth=1.0, glow=1.0, hood=1.0, claw=1.0, ht=0.25, tail=0.5, hair=1.5),
        _base(wy=-46.0, wx=40.0, lean=0.95, wv=2.4, arm=1.6, el=0.1, arm_b=1.55, el_b=0.2, mouth=1.0, glow=1.0, hood=0.9, claw=1.0, ht=0.55, tail=1.0, hair=2.0),
        _base(wy=-40.0, wx=42.0, lean=1.05, wv=2.8, arm=1.2, el=0.2, arm_b=1.1, el_b=0.35, mouth=0.8, glow=0.9, hood=0.7, claw=0.8, ht=0.65, tail=0.6, hair=1.8),
        _base(wy=-44.0, wx=30.0, lean=0.7, wv=3.1, arm=0.8, el=0.5, arm_b=0.7, el_b=0.6, mouth=0.4, glow=0.75, hood=0.55, claw=0.5, ht=0.35, tail=0.2, hair=1.0),
    ])


def _slam(i):
    return bk.pick(i, [
        _base(wy=-74.0, wx=0.0, lean=-0.25, wv=0.6, arm=1.85, el=1.1, arm_b=2.4, el_b=1.0, mouth=1.0, glow=1.0, hood=1.0, claw=1.0, ht=-0.25, rise=1.0, hair=-1.2),
        _base(wy=-48.0, wx=30.0, lean=0.8, wv=1.8, arm=1.4, el=0.2, arm_b=1.3, el_b=0.2, mouth=1.0, glow=1.0, hood=0.9, claw=1.0, ht=0.35, tail=0.8, hair=1.5),
        _base(wy=-30.0, wx=36.0, lean=1.2, wv=2.6, arm=0.7, el=0.5, arm_b=0.6, el_b=0.5, mouth=0.7, glow=0.9, hood=0.6, claw=0.8, ht=0.8, tail=0.4, hair=1.6),
    ])


def _cast(i):
    return bk.pick(i, [
        # 0: salış: yakın el ileri itilmiş (zehir elden çıktı)
        _base(wy=-52.0, wx=16.0, lean=0.35, wv=0.8, arm=1.6, el=0.05, arm_b=0.6, el_b=0.8, mouth=0.9, glow=1.0, hood=0.8, claw=1.0, orb=0.25, ht=0.12, hair=0.8),
        _base(wy=-54.0, wx=11.0, lean=0.12, wv=1.2, arm=1.2, el=0.9, arm_b=0.8, el_b=1.2, mouth=0.4, glow=0.9, hood=0.7, claw=0.6, orb=0.6, hair=0.0),
        # 2: yükleniş (tutulur): iki el göğüs önünde zehir küresi örer, yelpaze açık, gözler yanar
        _base(wy=-58.0, wx=8.0, lean=0.0, wv=1.6, arm=1.25, el=1.35, arm_b=1.1, el_b=1.5, mouth=0.6, glow=1.0, hood=1.0, claw=0.4, orb=1.0, ht=-0.08, rise=0.5, hair=-0.6),
    ])


def _hurt(i):
    return bk.pick(i, [
        _base(wy=-48.0, wx=4.0, lean=-0.35, wv=0.9, arm=0.9, el=1.6, arm_b=1.4, el_b=1.4, mouth=0.8, glow=0.4, hood=0.3, claw=0.6, ht=-0.35, hair=1.5),
        _base(wy=-49.0, wx=7.0, lean=-0.15, wv=1.2, arm=0.7, el=1.0, arm_b=0.8, el_b=1.0, mouth=0.4, glow=0.5, hood=0.4, claw=0.4, ht=-0.15, hair=0.8),
    ])


def _rage(i):
    return bk.pick(i, [
        _base(wy=-44.0, wx=12.0, lean=0.4, wv=0.4, arm=0.9, el=1.2, arm_b=0.8, el_b=1.3, mouth=0.4, glow=0.9, hood=0.6, claw=0.8, ht=0.2, hair=1.0),
        _base(wy=-62.0, wx=6.0, lean=-0.05, wv=1.2, arm=1.6, el=0.8, arm_b=2.0, el_b=0.7, mouth=0.9, glow=1.0, hood=1.0, claw=1.0, ht=-0.2, rise=0.7, hair=-0.6),
        _base(wy=-70.0, wx=2.0, lean=-0.15, wv=2.0, arm=1.75, el=0.9, arm_b=2.45, el_b=0.6, mouth=1.0, glow=1.0, hood=1.0, claw=1.0, ht=-0.35, rise=1.0, hair=-1.2),
    ])


ANIMS = {
    'idle': (8, _idle), 'walk': (8, _walk), 'windup': (4, _windup), 'strike': (4, _strike),
    'slam': (3, _slam), 'cast': (3, _cast), 'hurt': (2, _hurt), 'rage': (3, _rage),
}


# ------------------------------------------------------------ yılan gövdesi
T_UP = [(-60.0, -72.0), (-74.0, -54.0), (-67.0, -35.0), (-52.0, -19.0), (-40.0, -10.0)]
T_CEIL = [(-52.0, -150.0), (-58.0, -118.0), (-58.0, -80.0), (-50.0, -42.0), (-40.0, -12.0)]
T_LASH = [(-90.0, -6.0), (-78.0, -5.0), (-65.0, -5.0), (-52.0, -6.0), (-40.0, -8.5)]


def _segments(p):
    """Yılan gövdesinin merkez çizgisi, üç parça + yükseliş: (noktalar, kalınlıklar, z) listesi. Kuyruk ucundan bele:
    yerde uzanan kuyruk -> alt halka ön yayı -> üst halka arka yayı (alt halkanın arkasında) -> üst halka ön yayı ->
    bele yükselen gövde. Halkalar yerde yığılmış bir yılan kangalı okutur."""
    wv, W = p['wv'], (p['wx'], p['wy'])
    tail, slide = p['tail'], p['slide']
    sw = math.sin(wv)
    # kuyruk (yerde, dalgalanır; saldırıda kamçılanıp kalkar)
    tl = []
    for i, (x, y) in enumerate(((-90.0, -12.0), (-80.0, -6.5), (-66.0, -6.5), (-52.0, -7.0), (-40.0, -9.0))):
        u = i / 4
        tl.append((x + math.sin(wv - i * 0.9) * 2.5 * slide, y - abs(math.sin(wv - i * 1.1)) * (1 - u) * (2.0 + 2.0 * slide)
                   - tail * (1 - u) ** 2 * 10.0 + math.sin(wv * 0.5 + i) * tail * (1 - u) * 3.0))
    # v29 kuyruk biçimleri: tup (çıngırak gibi S kalkış), tceil (tavana dikilen kuyruk), tlash (yere çarpıp uzanan kamçı)
    for key, shape in (('tup', T_UP), ('tceil', T_CEIL), ('tlash', T_LASH)):
        k = p.get(key, 0.0)
        if k:
            tl = [(a[0] + (b[0] + math.sin(wv - i * 1.3) * 2.0 * (1 - i / 4) - a[0]) * k,
                   a[1] + (b[1] + math.cos(wv - i * 1.1) * 2.0 * (1 - i / 4) - a[1]) * k) for i, (a, b) in enumerate(zip(tl, shape))]
    c1 = (-8.0 + 2.0 * sw * slide, -11.0)
    lower = tl + [(-24.0, -11.0 + 0.5 * sw), (-6.0, -11.0), (12.0, -12.0), (25.0, -17.0)]
    back = [(25.0, -17.0), (24.0, -25.0), (8.0, -30.5), (-12.0, -30.0), (-28.0, -26.0), (-34.0, -22.5)]
    upper = [(-34.0, -22.5), (-30.0, -32.0), (-14.0, -35.0), (4.0, -36.0)]
    # v29 kangal: coil (+ sıkışıp geriye çekilir: atılış öncesi yay gibi kurulma), cx kayma, cw kangalda yürüyen dalga
    cl, cx, cw = p.get('coil', 0.0), p.get('cx', 0.0), p.get('cw', 0.0)
    if cl or cx or cw:
        def C(q, k):
            x, y = q
            y = -11.0 + (y + 11.0) * (1.0 - 0.28 * cl) - math.sin(wv * 1.0 - k * 0.9) * cw * (1.0 if y < -14 else 0.4)
            return ((x - 0.0) * (1.0 + 0.08 * cl) + cx - 6.0 * cl + math.cos(wv - k * 0.9) * cw * 0.6, y)
        n0 = len(tl)
        lower = tl + [C(q, k + n0) for k, q in enumerate(lower[n0:])]
        back = [C(q, k + 4) for k, q in enumerate(back)]
        upper = [C(q, k + 10) for k, q in enumerate(upper)]
    # yükseliş: üst halkadan bele S kıvrımı
    b0 = upper[-1]
    rise = []
    for k in range(1, 5):
        u = k / 4
        x = b0[0] + (W[0] - b0[0]) * u + math.sin(u * math.pi) * (5.0 - 3.0 * p['rise'])
        y = b0[1] + (W[1] + 5.0 - b0[1]) * (u ** 0.85)
        rise.append((x, y))
    upper_rise = upper + rise + [W]
    _ = c1
    nl = len(lower)
    wl = [4.0 + 18.0 * min(1.0, (i / (nl - 1)) * 1.6) for i in range(nl)]
    return [(back, [23.0] * len(back), -16.0), (lower, wl, -12.0),
            (upper_rise, [22.0, 22.0, 21.0, 20.0] + [20.0 - 6.0 * (k / 4) for k in range(1, 5)] + [13.0], -11.0)]


def _body_seg(cv, pts, widths, z, cap0=True, cap1=True):
    Q = np.array(ik._cr_points([cv.W(q) for q in pts], False, n=10))
    Wd = np.interp(np.linspace(0, 1, len(Q)), np.linspace(0, 1, len(widths)), [cv.u(w) for w in widths])
    tg = np.gradient(Q, axis=0)
    tg = tg / (np.hypot(tg[:, 0], tg[:, 1])[:, None] + 1e-9)
    nrm = np.stack([-tg[:, 1], tg[:, 0]], 1)    # karın yanı: hep alta/öne bakar (halkanın arka yayında da)
    flip = (nrm[:, 0] * 0.35 + nrm[:, 1]) < 0
    nrm[flip] *= -1
    left = Q - nrm * Wd[:, None] * 0.5
    right = Q + nrm * Wd[:, None] * 0.5
    parts = [ik.poly_path([tuple(q) for q in np.concatenate([left, right[::-1]])])]
    if cap0:
        parts.append(ik.circle_path(tuple(Q[0]), Wd[0] * 0.5))
    if cap1:
        parts.append(ik.circle_path(tuple(Q[-1]), Wd[-1] * 0.5))
    body = ik.union(*parts)
    bl = Q + nrm * Wd[:, None] * 0.12
    br = Q + nrm * Wd[:, None] * 0.52
    belly = ik.poly_path([tuple(q) for q in np.concatenate([bl, br[::-1]])])
    det = []
    L = len(Q)
    Paint, c4 = ik.skia.Paint, ik._c4
    for i in range(3, L - 3, 6):     # sırtta koyu baklava deseni (açık kenarlı)
        c = Q[i] - nrm[i] * Wd[i] * 0.16
        w = Wd[i] * 0.2
        t_ = tg[i] * w * 1.5
        nn = nrm[i] * w
        dia = ik.poly_path([tuple(c - t_), tuple(c - nn), tuple(c + t_), tuple(c + nn)])
        det.append(('deep', dia))
        det.append(('fn', lambda c_, d_=dia: c_.drawPath(d_, Paint(AntiAlias=True, Style=Paint.kStroke_Style, StrokeWidth=cv.px(1.0), Color4f=c4(SCALE.hi, 0.8)))))
    for i in range(2, L - 2, 2):     # pul yayları
        for o in (-0.36, -0.06):
            c = Q[i] + nrm[i] * Wd[i] * o
            a = c - tg[i] * Wd[i] * 0.07 - nrm[i] * Wd[i] * 0.05
            b = c + tg[i] * Wd[i] * 0.07 - nrm[i] * Wd[i] * 0.05
            det.append(('fn', lambda c_, pts_=(tuple(a), tuple(c), tuple(b)): c_.drawPath(ik.taper_path(list(pts_), cv.px(0.9), (0.3, 0.3)),
                                                                                          Paint(AntiAlias=True, Color4f=c4(SCALE.shadow, 0.75)))))
    cv.shape(body, SCALE, z=z, sd=6.0, hi=0.55, details=det, bounce=0.4, hatch=0.3, cast=1.4)
    bdet = []
    for i in range(1, L - 1, 3):
        a0, a1 = tuple(Q[i] + nrm[i] * Wd[i] * 0.14), tuple(Q[i] + nrm[i] * Wd[i] * 0.5)
        bdet.append(('fn', lambda c_, a0=a0, a1=a1: c_.drawPath(ik.taper_path([a0, a1], cv.px(1.1), (0.2, 0.2), smooth=False),
                                                                Paint(AntiAlias=True, Color4f=c4(BELLY.shadow)))))
    cv.shape(ik.isect(belly, body), BELLY, z=z + 0.05, sd=2.4, hi=0.35, details=bdet, ol=0.8)


def _serpent(cv, p, z):
    segs = _segments(p)
    for pts, widths, zz in segs:
        _body_seg(cv, pts, widths, z + (zz + 12.0) * 0.5)
    return segs[1][0], segs[1][1]


def _tail_head(cv, p, pts, z, g):
    """Kuyruk ucundaki yılan başı (halk resmindeki Şahmeran kuyruğu): yukarı kalkık, ağzı açık, gözü yanar."""
    tip = pts[0]
    d = bk.perp(pts[1], pts[0])[1]
    ang = math.atan2(d[1], d[0]) - 0.6 - 0.3 * p['tail']
    d = (math.cos(ang), math.sin(ang))
    n = (-d[1], d[0])
    h = add(tip, d, 3.0)
    jaw = 0.4 + 0.5 * p['tail'] + 0.2 * math.sin(p['wv'])
    head = cv.blob([add(h, n, -3.0), add(add(h, d, 5.0), n, -3.0), add(add(h, d, 9.0), n, -1.0), add(add(h, d, 9.5), n, 0.6, ),
                    add(add(h, d, 5.0), n, 1.0), add(h, n, 3.0)])
    lower = cv.blob([add(add(h, d, 2.0), n, 1.5), add(add(h, d, 8.0), n, 1.5 + jaw * 3.0), add(add(h, d, 7.0), n, 2.6 + jaw * 3.0), add(add(h, d, 2.0), n, 3.0)])
    cv.fill(cv.blob([add(add(h, d, 3.0), n, 0.8), add(add(h, d, 8.5), n, 0.8), add(add(h, d, 7.5), n, 1.8 + jaw * 3.0)]), MOUTH_IN, z=z - 0.05)
    cv.shape(lower, SCALE, z=z - 0.02, sd=0.8, hi=0.2, ol=0.85)
    cv.shape(head, SCALE, z=z, sd=1.4, hi=0.4, ol=0.95, details=[('deep', cv.blob([add(add(h, d, 2.0), n, -2.6), add(add(h, d, 6.0), n, -2.4), add(add(h, d, 4.0), n, -1.2)]))])
    cv.fill(cv.ellipse(add(add(h, d, 5.5), n, -1.2), 0.9, 0.6, ang), EYE, z=z + 0.1, glow=tuple(c * g for c in EYE_GLOW))
    # çatal dil
    t0 = add(add(h, d, 8.0), n, 1.4 + jaw * 1.5)
    cv.stroke([t0, add(t0, d, 3.0), add(add(t0, d, 4.5), n, -1.0)], 0.9, z=z + 0.05, col=(0.75, 0.1, 0.2), taper=(0.1, 0.6))
    cv.stroke([add(t0, d, 3.0), add(add(t0, d, 4.5), n, 1.0)], 0.8, z=z + 0.05, col=(0.75, 0.1, 0.2), taper=(0.1, 0.6))


def _hood(cv, NK, ht, p, z, g):
    """Kobra yelpazesi: başın arkasında açılan, kaburgalı, kenarı dalgalı deri; içte açık karın bantları, altın kenar,
    uçlarda zümrüt taşlar (hazırlıkta/öfkede açılır)."""
    f = 0.6 + 0.5 * p['hood']
    c = add(NK, (-2.0 * WS, -9.0 * WS * f))
    rx, ry = 15.0 * WS * f, 21.0 * WS * f
    outline = []
    n = 9
    # yanlara açılan, üstte hafif dalgalı, boyuna doğru daralan yelpaze (ters damla)
    prof = [(-0.15, 0.95), (-0.55, 0.75), (-0.9, 0.35), (-1.0, -0.15), (-0.95, -0.6), (-0.6, -0.92), (0.0, -1.0), (0.6, -0.92),
            (0.95, -0.6), (1.0, -0.15), (0.9, 0.35), (0.55, 0.75), (0.15, 0.95)]
    for k, (u, v) in enumerate(prof):
        outline.append((c[0] + u * rx, c[1] + v * ry, 0.0 if (4 <= k <= 8 and k % 2 == 0) else 1.0))
    hood = cv.blob(outline)
    det = []
    for k in range(5):   # kaburgalar
        aa = -math.pi * 0.5 + (k - 2) * 0.5
        det.append(('ink', [polar(c, aa, rx * 0.15), polar(c, aa, ry * 0.9)], 1.1, (0.3, 0.6)))
    # iç yüzde açık karın bantları (ortada dikey pul şeridi)
    band = cv.blob([add(c, (-3.5 * f, -ry * 0.75)), add(c, (3.5 * f, -ry * 0.75)), add(c, (4.5 * f, ry * 0.3)), add(c, (-4.5 * f, ry * 0.3))])
    det.append(('col', band, mix_(HOOD.base, BELLY.base, 0.55)))
    for k in range(5):
        y = -ry * 0.65 + k * ry * 0.2
        det.append(('ink', [add(c, (-3.8 * f, y)), add(c, (3.8 * f, y + 0.6))], 0.8, (0.1, 0.1)))
    cv.shape(hood, HOOD, z=z, sd=4.0, hi=0.35, details=det, bounce=0.35, hatch=0.3)
    rim = ik.diff(hood, cv.blob([(q[0] * 0.9 + c[0] * 0.1, q[1] * 0.9 + c[1] * 0.1) + tuple(q[2:]) for q in outline]))
    cv.shape(rim, GOLD, z=z + 0.05, sd=0.8, hi=0.3, ol=0.6)
    for k in range(0, n + 1, 2):
        a = math.pi * (0.62 + k / n * 1.76)
        if math.sin(a) > 0.2:
            continue
        q = (c[0] + math.cos(a) * rx * 0.97, c[1] + math.sin(a) * ry * 0.97)
        cv.fill(cv.ellipse(q, 1.2 * f, 1.4 * f), GEM, z=z + 0.1, glow=tuple(cc * g * 0.8 for cc in GEM_GLOW))


def mix_(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _hair_snake(cv, root, ang, ln, ph, z, g, k):
    st = []
    x, y = root
    for i in range(6):
        a = ang + math.sin(ph - i * 0.9 + k) * 0.35
        x += math.cos(a) * ln / 6
        y += math.sin(a) * ln / 6
        st.append((x, y))
    body = ik.taper_path([cv.W(q) for q in [root] + st], cv.u(2.6 * WS), prof=lambda u: 0.55 + 0.45 * (1 - u))
    cv.shape(body, SCALE.darker(0.85), z=z, sd=0.8, hi=0.3, ol=0.8)
    h = st[-1]
    d = bk.perp(st[-2], st[-1])[1]
    hd = cv.blob([add(h, (-d[1], d[0]), -1.6 * WS), add(h, d, 3.4 * WS), add(h, (-d[1], d[0]), 1.6 * WS)])
    cv.shape(hd, SCALE, z=z + 0.01, sd=0.6, hi=0.3, ol=0.8)
    cv.fill(cv.ellipse(add(h, d, 1.4), 0.5, 0.5), (1.0, 0.25, 0.2), z=z + 0.02, glow=(0.8, 0.12, 0.1))


def _arm(cv, sh, a1, a2, z, near, claw, g, orb=0.0):
    e, h = bk.arm_fk(sh, a1, a2, L_UP * WS, L_FO * WS)
    m = SKIN if near else SKIN_B
    up = bk.muscle(cv, sh, e, 3.6 * WS, 2.8 * WS, front=0.5, back=0.4, at=0.35)
    fo = bk.muscle(cv, e, h, 2.8 * WS, 2.0 * WS, front=0.5, back=0.2, at=0.25)
    cv.shape(ik.union(up, fo), m, z=z, sd=1.6, hi=0.35 if near else 0.0, bounce=0.3 if near else 0.0)
    gm = GOLD if near else GOLD_B
    for (a, b, t0, t1) in ((sh, e, 0.3, 0.42), (e, h, 0.72, 0.9)):   # kolluk + bilezik
        band = ik.isect(ik.union(up, fo), cv.poly([along(a, b, t0, -6), along(a, b, t0, 6), along(a, b, t1, 6), along(a, b, t1, -6)]))
        cv.shape(band, gm, z=z + 0.05, sd=0.6, hi=0.3, ol=0.7,
                 details=[('col', cv.ellipse(along(a, b, (t0 + t1) / 2, 0.0), 0.7, 0.7), GEM)] if near else ())
    # el: açık, uzun altın pençeli
    d = bk.perp(e, h)[1]
    bk.open_hand(cv, h, d, 2.6 * WS, m, z + 0.1, spread=0.5 + 0.7 * claw, curl=0.9 - 0.7 * claw, near=near, claws=GOLD)
    if orb > 0.05 and near:
        oc = add(h, d, 6.5)
        r = (2.5 + 4.0 * orb) * WS
        cv.fill(cv.ellipse(oc, r * 1.3, r * 1.3), (0.15, 0.6, 0.25), z=z + 0.3, glow=tuple(c * 0.8 for c in GEM_GLOW), alpha=0.6)
        cv.fill(cv.ellipse(oc, r, r), VENOM, z=z + 0.31, glow=GEM_GLOW)
        cv.fill(cv.ellipse(add(oc, (-r * 0.25, -r * 0.25)), r * 0.45, r * 0.45), (0.9, 1.0, 0.8), z=z + 0.32, glow=(0.6, 1.0, 0.6))
        for k in range(3):
            a = k * 2.1 + orb * 3.0
            cv.stroke([polar(oc, a, r * 1.1), polar(oc, a + 0.8, r * 1.5), polar(oc, a + 1.5, r * 1.2)], 1.0, z=z + 0.33,
                      col=VENOM, taper=(0.2, 0.7), glow=GEM_GLOW)
    return e, h


def _head(cv, H, ht, p, z, g):
    ca_, sa_ = math.cos(ht), math.sin(ht)

    def Q(u, v, *t):
        u, v = u * WS, v * WS
        return (H[0] + u * ca_ - v * sa_, H[1] + u * sa_ + v * ca_) + tuple(t)
    jaw = p['mouth']
    # saç (arkada, omuzlara ve sırta dökülür)
    hw = p['hair']
    hair = cv.blob([Q(-1, -8.5), Q(-6, -7), Q(-8.5, -2), Q(-9.5 - hw, 6), Q(-11 - hw * 1.5, 14), Q(-10 - hw * 2.0, 22), Q(-6 - hw * 1.6, 26, 0.0),
                    Q(-4 - hw, 18), Q(-2, 10), Q(1, 4)])
    hdet = [('stroke', [Q(-4, -6), Q(-6.5 - hw * 0.5, 4), Q(-8 - hw * 1.4, 18)], 1.0, HAIR.hi, (0.3, 0.6)),
            ('ink', [Q(-2, -4), Q(-4.5 - hw * 0.5, 6), Q(-6 - hw * 1.2, 16)], 0.9, (0.3, 0.6))]
    cv.shape(hair, HAIR, z=z - 0.5, sd=2.0, hi=0.35, details=hdet)
    # yüz (3/4 profil): alın, kaş kemeri, ince düz burun, dolgun dudak, sivri çene, çene hattı kulağa
    face = cv.blob([Q(-4.5, -7.0), Q(0.0, -9.0), Q(4.5, -7.6), Q(6.0, -4.6), Q(5.8, -3.2), Q(7.7, -0.2, 0.0), Q(6.3, 0.9), Q(6.8, 2.3),
                    Q(6.0, 3.1 + jaw * 0.6), Q(6.4, 4.2 + jaw * 1.6), Q(5.4, 5.6 + jaw * 1.8), Q(4.8, 7.0 + jaw * 1.8, 0.5), Q(2.4, 7.5 + jaw * 1.4),
                    Q(-1.5, 5.0), Q(-3.6, 1.0), Q(-5.0, -3.0)])
    det = [('shade', cv.wedge([Q(1.0, 1.5), Q(3.0, 3.2), Q(4.8, 5.8)], 0.6, 1.0)),          # elmacık altı gölgesi
           ('ink', [Q(6.9, -1.0), Q(7.5, -0.2), Q(6.4, 0.6)], 0.9, (0.2, 0.3)),               # burun ucu
           ('ink', [Q(5.6, -3.6), Q(6.2, -1.8)], 0.8, (0.3, 0.5)),                           # burun sırtı
           ('ink', [Q(4.5, 6.6 + jaw * 1.8), Q(3.0, 7.2 + jaw * 1.4)], 0.9, (0.3, 0.3)),
           ('hi', cv.blob([Q(1.5, -6.5), Q(4.2, -7.0), Q(4.6, -5.6), Q(2.0, -5.2)]))]
    cv.shape(face, SKIN, z=z, sd=1.6, hi=0.3, details=det, cast=0.6, bounce=0.4)
    # alın üstüne inen saç (ortadan ayrık), yüzün arka kenarını çerçeveler
    fr = cv.blob([Q(-6.5, -6.5), Q(-1.0, -10.0), Q(4.8, -8.4), Q(5.4, -7.0), Q(1.0, -7.4), Q(-2.0, -5.5), Q(-4.0, -1.0), Q(-4.5, 6.0),
                  Q(-6.0, 4.0)])
    cv.shape(fr, HAIR, z=z + 0.02, sd=1.2, hi=0.35, details=[('stroke', [Q(-1.0, -9.0), Q(2.5, -8.2)], 0.9, HAIR.hi, (0.3, 0.5))])
    # küpe (altın halka + zümrüt)
    cv.shape(cv.ellipse(Q(-3.0, 3.2), 0.9 * WS, 1.3 * WS, ht), GOLD, z=z + 0.06, sd=0.4, ol=0.7)
    cv.fill(cv.ellipse(Q(-3.0, 4.6), 0.55 * WS, 0.8 * WS, ht), GEM, z=z + 0.07, glow=tuple(c * 0.6 * g for c in GEM_GLOW))
    # ağız: koyu erik dudaklar; açılınca yılan dişleri (iki sivri üst diş)
    if jaw > 0.2:
        cv.fill(cv.blob([Q(4.6, 3.0), Q(6.3, 2.9), Q(6.1, 3.5 + jaw * 1.8), Q(4.8, 3.6 + jaw * 1.5)]), MOUTH_IN, z=z + 0.1)
        for u in (5.2, 6.0):
            cv.fill(cv.blob([Q(u - 0.25, 2.95), Q(u + 0.25, 2.95), Q(u, 4.1 + jaw * 0.4, 0.0)]), (0.98, 0.95, 0.88), z=z + 0.11)
    cv.fill(cv.blob([Q(4.6, 2.6), Q(5.6, 2.1), Q(6.6, 2.4), Q(6.0, 3.0), Q(4.7, 3.0)]), LIP, z=z + 0.12)
    cv.fill(cv.blob([Q(4.8, 3.6 + jaw * 1.6), Q(6.2, 3.5 + jaw * 1.6), Q(5.8, 4.4 + jaw * 1.6), Q(5.0, 4.4 + jaw * 1.6)]), LIP, z=z + 0.12)
    cv.fill(cv.ellipse(Q(5.6, 3.9 + jaw * 1.6), 0.4, 0.2), (0.85, 0.55, 0.6), z=z + 0.13)
    # gözler: iri badem, tamamı zümrüt (yılan gözü), dikey bebek; sürme kanadı arkaya uzanır; uzak göz burun yanında
    ec = Q(3.4, -2.8)
    cv.fill(cv.blob([Q(1.6, -2.6, 0.0), Q(3.4, -3.8), Q(5.0, -3.0, 0.0), Q(3.4, -1.9)]), EYE, z=z + 0.2, glow=tuple(c * g for c in EYE_GLOW))
    cv.fill(cv.ellipse(Q(3.6, -2.85), 0.3 * WS, 0.75 * WS, ht), (0.03, 0.08, 0.04), z=z + 0.21)
    cv.fill(cv.ellipse(Q(3.0, -3.3), 0.25 * WS, 0.2 * WS, ht), (0.95, 1.0, 0.9), z=z + 0.215)
    cv.stroke([Q(1.0, -2.3), Q(1.6, -2.9), Q(3.4, -4.0), Q(5.1, -3.1)], 1.5, z=z + 0.22, col=INK, taper=(0.4, 0.3))
    cv.stroke([Q(1.8, -2.4), Q(0.2, -3.2)], 1.3, z=z + 0.22, col=INK, taper=(0.1, 0.9))                           # sürme kanadı
    cv.fill(cv.blob([Q(5.5, -3.0, 0.0), Q(6.0, -3.5), Q(6.3, -2.9, 0.0), Q(5.9, -2.5)]), EYE, z=z + 0.2, glow=tuple(c * g * 0.7 for c in EYE_GLOW))
    br = p['mouth'] * 0.6 + p['claw'] * 0.3
    cv.stroke([Q(1.4, -4.9 + br * 0.2), Q(3.6, -5.6 + br * 0.5), Q(5.6, -4.6 + br * 0.9)], 1.1, z=z + 0.22, col=HAIR.base, taper=(0.3, 0.5))
    # taç: yüksek, üç sivri, ortada zümrüt; yanlarda yılan başları
    cr = cv.blob([Q(-4.5, -7.0), Q(-5.5, -12.0), Q(-3.0, -11.0), Q(-1.5, -17.0), Q(0.8, -12.0), Q(2.2, -21.0, 0.0), Q(3.8, -12.0), Q(5.4, -16.0),
                  Q(6.6, -10.5), Q(6.0, -6.6), Q(1.0, -8.6)])
    cdet = [('ink', [Q(-4.4, -8.6), Q(1.0, -10.2), Q(6.2, -8.2)], 1.0, (0.1, 0.1))]
    cv.shape(cr, GOLD, z=z + 0.3, sd=1.2, hi=0.45, details=cdet, ol=0.95)
    cv.fill(cv.blob([Q(1.0, -11.0), Q(2.2, -14.0, 0.0), Q(3.4, -11.0), Q(2.2, -9.6, 0.0)]), GEM, z=z + 0.35, glow=tuple(c * g for c in GEM_GLOW))
    for u in (-3.0, 5.0):
        cv.fill(cv.ellipse(Q(u, -9.6), 0.7, 0.7), (0.9, 0.15, 0.2), z=z + 0.35, glow=(0.5, 0.05, 0.08))
    return Q(5.5, 4.6), ec


def draw(cv, p):
    g = 0.5 + 0.5 * p['glow']
    W = (p['wx'], p['wy'])
    lean = p['lean']
    up = (math.sin(lean), -math.cos(lean))
    fw = (math.cos(lean), math.sin(lean))

    def T(u, f, *t):
        return add(add(W, up, u * WS), fw, f * WS) + tuple(t)
    CH = T(20.0, 0.0)            # göğüs merkezi
    NK = T(30.0, 1.5)            # boyun kökü
    sh_f = T(27.0, -2.5)
    sh_b = T(28.5, 6.0)
    ht = p['ht'] + lean * 0.4
    H = add(T(36.5, 4.0), (0.0, 0.0))

    # ---- kobra yelpazesi + saç yılanları (en arkada)
    _hood(cv, NK, ht, p, -30.0, g)
    for k in range(4):
        root = T(31.0 - k * 4.0, -4.0 - k * 1.2)
        ang = math.pi * (0.95 + k * 0.1) - lean * 0.6 - p['hair'] * 0.15
        _hair_snake(cv, root, ang, (13.0 - k) * WS, p['wv'], -28.0 + k * 0.01, g, k)
    # ---- uzak kol
    _arm(cv, sh_b, p['arm_b'], p['el_b'], -20.0, False, p['claw'], g)
    # ---- yılan gövdesi + kuyruk başı
    pts, widths = _serpent(cv, p, -10.0)
    _tail_head(cv, p, pts, -9.0, g)
    # ---- kadın gövdesi: bel (pullar tene geçer) + göğüs kafesi + omuzlar
    front = [(-2.0, 6.8), (2.0, 6.4), (6.0, 6.6), (10.0, 7.8), (14.0, 10.0), (18.0, 9.2), (21.0, 7.4), (25.0, 5.4), (28.5, 3.4)]
    back = [(29.0, -2.0), (27.0, -4.8), (22.0, -6.8), (16.0, -6.4), (10.0, -5.0), (5.0, -5.8), (0.0, -6.8), (-2.0, -6.8)]
    body_ = cv.blob([T(u, f) for u, f in front] + [T(u, f) for u, f in back])
    shoulders = cv.capsule(sh_f, sh_b, 3.6 * WS, 3.2 * WS)
    neck = cv.capsule(NK, add(H, (-1.0 * WS, 4.0 * WS)), 2.5 * WS, 2.1 * WS)
    torso = ik.union(body_, shoulders, neck)
    tdet = [('ink', [T(4.6, 5.4), T(4.0, 5.5)], 1.4, (0.2, 0.2)),                    # göbek
            ('ink', [T(7.0, 1.0), T(4.0, 2.0), T(1.0, 1.5)], 0.9, (0.3, 0.5)),      # karın çizgisi
            ('ink', [T(24.5, 0.0), T(25.5, 3.0), T(24.0, 5.5)], 0.9, (0.3, 0.3)),   # köprücük
            ('shade', cv.wedge([T(16.0, -6.0), T(11.0, -4.6), T(6.0, -5.4)], 1.2, -1.0))]
    cv.shape(torso, SKIN, z=0, sd=4.0, hi=0.45, details=tdet, bounce=0.4, cast=0.8, hatch=0.25)
    # bel kuşağı: pul -> ten geçişi altın kemer; sarkan zincir ve zümrütler
    belt = ik.isect(torso, cv.poly([T(-2.0, -12), T(-2.0, 12), T(4.0, 12), T(4.0, -12)]))
    cv.shape(belt, GOLD, z=0.5, sd=1.0, hi=0.4, details=[('ink', [T(1.0, -7), T(1.2, 0), T(1.0, 7)], 0.9, (0.1, 0.1))])
    for k in range(4):
        q = T(0.0, -4.0 + k * 3.2)
        cv.shape(cv.blob([q, add(q, (1.0, 0.0)), (add(q, up, -4.0 - (k % 2) * 1.5)[0] + 0.5, add(q, up, -4.0 - (k % 2) * 1.5)[1], 0.0)]), GOLD,
                 z=0.6 + k * 0.01, sd=0.4, ol=0.7)
    cv.fill(cv.ellipse(T(1.0, 5.0), 1.1 * WS, 1.1 * WS), GEM, z=0.7, glow=tuple(c * g * 0.7 for c in GEM_GLOW))
    # altın pullu göğüslük
    bp = cv.blob([T(21.5, 0.5), T(22.0, 6.8), T(19.0, 9.8), T(14.0, 10.6), T(10.2, 8.6), T(10.4, 3.0), T(13.0, -0.5), T(18.0, -1.0)])
    bdet = []
    for r in range(4):
        for c in range(4):
            q = T(20.0 - r * 2.6, 1.0 + c * 2.3 + (1.1 if r % 2 else 0.0))
            bdet.append(('ink', [add(q, fw, -1.1), add(q, up, -1.0), add(q, fw, 1.1)], 0.8, (0.2, 0.2)))
    cv.shape(bp, GOLD, z=1.0, sd=2.0, hi=0.5, details=bdet, cast=0.6)
    cv.fill(cv.blob([T(16.5, 5.2), T(15.0, 6.6, 0.0), T(13.0, 5.4), T(15.0, 4.2, 0.0)]), GEM, z=1.05, glow=tuple(c * g for c in GEM_GLOW))
    cv.stroke([T(21.0, 1.0), T(25.0, -1.5), T(28.0, -3.0)], 1.2, z=1.02, col=GOLD.shadow, taper=(0.1, 0.1))     # askı
    # kolye: altın yarım ay + zümrüt damla
    nk = [T(28.0, -1.0), T(25.5, 2.5), T(26.5, 5.5)]
    cv.stroke(nk, 1.8, z=1.2, col=GOLD.base, taper=(0.1, 0.1))
    cv.fill(cv.blob([T(25.8, 2.2), T(23.6, 2.8, 0.0), T(25.8, 3.4)]), GEM, z=1.25, glow=tuple(c * g for c in GEM_GLOW))
    # boyuna dolanan küçük yılan
    _hair_snake(cv, T(29.0, -3.0), -0.2 - lean, 9.0 * WS, p['wv'] + 1.0, 1.4, g, 7)
    # ---- baş
    mouth, ec = _head(cv, H, ht, p, 8.0, g)
    # ---- yakın kol (zehir küresi)
    e, h = _arm(cv, sh_f, p['arm'], p['el'], 14.0, True, p['claw'], g, p['orb'])
    return {'hand': h, 'mouth': mouth}


SHADE = dict(outer=0.65, rim=0.75, rim_col=(0.6, 1.0, 0.75), rim_dir=(0.6, -0.8), rim_w=1.6, form=(8.0, (0.72, 0.72, 0.86)))


def render_frame(anim, i, ss=3):
    p = CLIPS[anim]['fn'](i) if anim in CLIPS else ANIMS[anim][1](i)
    cv = bk.new_canvas(CELL, FEET, ss)
    xf = bk.body_xf(cv, p)
    info = draw(cv, p)
    if xf:
        cv.pop()
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, bk.xf_info(info, xf)


from sahmeran_v29 import CLIPS  # noqa: E402  v29 tam gövde animasyonları
