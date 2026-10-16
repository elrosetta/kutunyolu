"""Tepegöz — stil v2 "mürekkep-cel" boss (inkkit.py + bosskit.py). v1: creatures3.draw_tepegoz.

Dede Korkut'un tek gözlü devi: Konur Koca Saru Çoban'ın peri kızından olma oğlu. Kambur dağ gibi omuzlar, öne
sarkık kısa boyun, alnının ortasında kocaman tek göz (kehribar, damarlı; ışıma katmanında yanar), ağır kaş çıkıntısı,
alt çeneden fırlayan iki azı; peri anasının taktığı altın yüzük parmağında ışır (ok, kılıç işlemez); sırtında Oğuz
oklarının kırık sapları; boynunda insan kemiği ve kafatası kolye; koyun postu peştamal, deri kemer ve kemik toka;
baldırlarında çoban gibi deri dolak + ip çaprazı; elinde demir çemberli, çivili, taş gömülü meşe kütüğü gürz.
Uzak bileğinde kırık zincirli demir pranga.

Animasyon adları / kare sayıları / fps v1 ile aynı (idle 8, walk 8, windup 4, strike 4, slam 3, cast 3, hurt 2, rage 3);
çapalar 'hand' (gürz eli) ve 'mouth'. Hücre dünya 200x200 (v1), doku 800x800, ayak (96, 194) x4.
"""
import math

import inkkit as ik
from inkkit import Ink, INK
import bosskit as bk
from bosskit import along, add, lerp, polar

TEX = bk.TEX
CELL = (1024, 800)      # dünya 256 x 200 (v1 200x200; savuruşta gürz ucu +150'ye uzanır)
FEET = (384, 776)

# ------------------------------------------------------------ malzemeler
SKIN = Ink('#b4825c', '#4e2c3e', '#e2b088', '#2a1424', name='dev derisi')
SKIN_B = SKIN.darker(0.74, 'uzak deri')
SKIN_D = Ink('#8a5c46', '#4a2836', '#b88466', '#26121e', name='dudak/göz kapağı')
NAIL = Ink('#d8c6a0', '#8a7458', '#fff4d8', name='tırnak')
WOOL = Ink('#a8987c', '#585062', '#d8caa8', '#36303e', kind='fur', name='koyun postu')
WOOL_B = WOOL.darker(0.78, 'uzak post')
LEATHER = Ink('#6e4630', '#33201c', '#a07050', '#1e1214', name='deri')
LEATHER_B = LEATHER.darker(0.76)
ROPE = Ink('#b0905c', '#6a5034', '#e0c48a', name='ip')
BONE = Ink('#e8dcbc', '#9a8a6c', '#fffaea', '#5e4e3c', name='kemik')
BARK = Ink('#6a4a32', '#33221c', '#94704c', '#1c1210', name='meşe kabuğu')
WOOD = Ink('#a07a52', '#5e4030', '#cba274', name='kesik odun')
IRON = Ink('#6a6e7a', '#30323e', '#b4bccc', '#1c1e28', kind='metal', name='demir')
STONE = Ink('#8a8a84', '#4a4a56', '#c0c0b8', name='taş')
GOLD = Ink('#e8b44a', '#94561e', '#fff2b8', kind='metal', name='peri altını')
HAIR = Ink('#2e2830', '#16131a', '#5a5060', name='kara saç')
FLETCH = Ink('#c24a3a', '#6a2030', '#f07a5a', name='ok yeleği')
SHAFT = Ink('#c8a46c', '#7a5a3a', '#f0d49a', name='ok sapı')
MOUTH_IN = (0.32, 0.08, 0.10)
EYE_W = Ink('#f0e2b4', '#b89a70', '#fffbea', name='göz akı')
IRIS = (1.0, 0.66, 0.16)
IRIS_HOT = (1.0, 0.92, 0.55)
IRIS_GLOW = (1.0, 0.5, 0.08)
RING_GLOW = (1.0, 0.75, 0.25)

HIP_H = 70.0
L_TH, L_SH = 34.0, 34.0
L_UP, L_FO = 34.0, 31.0
CLUB_L = 68.0


# ------------------------------------------------------------ pozlar
def _base(**kw):
    d = dict(bob=0.0, lean=0.30, hx=0.0, ff=(15.0, 0.0), fb=(-15.0, 0.0), arm=0.25, el=0.45, arm_b=0.15, el_b=0.35,
             ca=0.75, cz=18.0, mouth=0.12, glow=0.55, hy=0.0, ht=0.0, lid=0.0, brow=0.0, fist_b=0.0, rock=0.0, ph=0.0,
             breath=0.0, arm_b_open=1.0)
    d.update(kw)
    return d


def _idle(t):
    s = math.sin(t * math.tau)
    return _base(bob=1.4 * s, breath=s, lean=0.30 + 0.02 * s, arm=0.22 + 0.02 * s, el=0.42, arm_b=0.12 - 0.03 * s, el_b=0.42,
                 ca=0.80 + 0.015 * s, mouth=0.14 + 0.08 * max(0.0, s), glow=0.55 + 0.35 * (0.5 + 0.5 * math.sin(t * math.tau * 2)),
                 hy=0.8 * s, ht=0.03 * s, ph=t * math.tau)


def _walk(t):
    ph = t * math.tau
    s, c = math.sin(ph), math.cos(ph)
    stride = 17.0

    def foot(phase):
        x = stride * math.sin(phase)
        lift = max(0.0, math.cos(phase)) ** 1.5 * 9.0       # öne giden ayak kalkar
        return (x, -lift)
    ff = foot(ph)
    fb = foot(ph + math.pi)
    return _base(bob=-abs(s) * 3.4 + 1.2, lean=0.34 + 0.03 * abs(c), ff=(ff[0] + 6, ff[1]), fb=(fb[0] - 8, fb[1]),
                 arm=0.30 - 0.18 * s, el=0.42, arm_b=0.15 + 0.22 * s, el_b=0.5, ca=0.62 - 0.08 * s,
                 mouth=0.2, glow=0.7, hy=1.2 * abs(s), ht=0.04 * s, ph=ph, hx=1.5 * s)


def _windup(i):
    # gürzü yana-geriye çeker (yatay savuruş için gerilme); yüz ve göz görünür kalır, son kare tutulur
    return bk.pick(i, [
        _base(bob=2.0, lean=0.26, arm=0.15, el=0.75, ca=-0.2, cz=18.0, arm_b=0.5, el_b=0.6, mouth=0.25, glow=0.75, ht=-0.03),
        _base(bob=4.0, lean=0.16, hx=-1.5, arm=-0.55, el=1.25, ca=-2.3, cz=-6.0, arm_b=0.95, el_b=0.55, mouth=0.45, glow=0.85,
              ht=-0.08, ff=(19.0, 0.0), fb=(-19.0, 0.0), brow=0.5),
        _base(bob=8.0, lean=0.08, hx=-3.5, arm=-1.0, el=1.55, ca=-2.75, cz=-8.0, arm_b=1.35, el_b=0.3, mouth=0.8, glow=1.0,
              ht=-0.1, ff=(23.0, 0.0), fb=(-21.0, 0.0), brow=1.0, fist_b=-1.0),
        _base(bob=10.0, lean=0.04, hx=-5.0, arm=-1.15, el=1.65, ca=-2.9, cz=-8.0, arm_b=1.45, el_b=0.25, mouth=0.95, glow=1.0,
              ht=-0.12, ff=(25.0, 0.0), fb=(-22.0, 0.0), brow=1.0, fist_b=-1.0),
    ])


def _strike(i):
    return bk.pick(i, [
        _base(bob=6.0, lean=0.34, hx=3.0, arm=1.5, el=1.0, ca=-2.75, cz=-6.0, arm_b=0.2, el_b=0.9, mouth=1.0, glow=1.0, ht=0.05,
              ff=(24.0, 0.0), fb=(-18.0, 0.0), brow=1.0),
        _base(bob=5.0, lean=0.42, hx=4.0, arm=1.12, el=0.3, ca=0.45, cz=22.0, arm_b=-0.25, el_b=0.8, mouth=1.0, glow=1.0, ht=0.12,
              ff=(28.0, 0.0), fb=(-16.0, 0.0), brow=1.0),
        _base(bob=8.0, lean=0.62, hx=7.0, arm=1.05, el=0.1, ca=0.82, cz=22.0, arm_b=-0.35, el_b=0.7, mouth=0.85, glow=0.95, ht=0.15,
              ff=(29.0, 0.0), fb=(-15.0, 0.0), brow=0.8),
        _base(bob=6.0, lean=0.52, hx=5.0, arm=0.72, el=0.25, ca=0.95, cz=22.0, arm_b=0.0, el_b=0.6, mouth=0.5, glow=0.8, ht=0.08,
              ff=(26.0, 0.0), fb=(-16.0, 0.0), brow=0.4),
    ])


def _slam(i):
    return bk.pick(i, [
        _base(bob=6.0, lean=0.02, hx=-2.0, arm=2.1, el=1.8, ca=-2.95, cz=-6.0, arm_b=2.3, el_b=1.5, mouth=1.0, glow=1.0,
              ht=-0.2, ff=(10.0, -6.0), fb=(-12.0, -4.0), brow=1.0, fist_b=-1.0),
        _base(bob=2.0, lean=0.45, hx=4.0, arm=1.9, el=0.1, ca=0.45, cz=22.0, arm_b=1.7, el_b=0.15, mouth=1.0, glow=1.0, ht=0.1,
              ff=(20.0, 0.0), fb=(-18.0, 0.0), brow=1.0, fist_b=-1.0),
        _base(bob=12.0, lean=0.72, hx=6.0, arm=1.1, el=0.15, ca=1.25, cz=22.0, arm_b=0.9, el_b=0.2, mouth=0.8, glow=0.95, ht=0.2,
              ff=(25.0, 0.0), fb=(-22.0, 0.0), brow=0.8, fist_b=-1.0),
    ])


def _cast(i):
    return bk.pick(i, [
        # 0: fırlatış (taş elden çıktı): uzak kol önde uzanmış, ağız açık
        _base(bob=3.0, lean=0.45, hx=4.0, arm=0.35, el=0.4, ca=0.95, arm_b=1.75, el_b=0.05, mouth=0.9, glow=1.0, ht=0.1,
              ff=(22.0, 0.0), fb=(-16.0, 0.0), brow=0.8, arm_b_open=1.0),
        # 1: toparlanma
        _base(bob=1.5, lean=0.32, arm=0.3, el=0.45, ca=0.85, arm_b=2.1, el_b=0.9, mouth=0.5, glow=0.9, rock=0.6,
              ff=(18.0, 0.0), fb=(-17.0, 0.0), brow=0.5, arm_b_open=0.0),
        # 2: yükleniş (tutulur): kaya başının üstünde, göz parlıyor
        _base(bob=4.0, lean=0.12, hx=-2.0, arm=0.4, el=0.5, ca=0.75, arm_b=2.6, el_b=1.65, mouth=0.75, glow=1.0, rock=1.0,
              ht=-0.15, ff=(21.0, 0.0), fb=(-19.0, 0.0), brow=1.0, arm_b_open=0.0),
    ])


def _hurt(i):
    return bk.pick(i, [
        _base(bob=3.0, lean=0.05, hx=-5.0, arm=0.55, el=0.6, ca=0.4, arm_b=1.95, el_b=1.65, mouth=0.85, glow=0.25, lid=0.75,
              ht=-0.3, hy=-1.0, ff=(12.0, 0.0), fb=(-19.0, 0.0), brow=-0.3, arm_b_open=1.0),
        _base(bob=2.0, lean=0.18, hx=-2.5, arm=0.4, el=0.5, ca=0.6, arm_b=1.4, el_b=1.0, mouth=0.4, glow=0.45, lid=0.35,
              ht=-0.12, ff=(13.0, 0.0), fb=(-17.0, 0.0), arm_b_open=1.0),
    ])


def _rage(i):
    # kükreme: baş yukarı, göğüs öne, uzak yumruk başın arkasında kalkık, gürz yana savrulmuş; göz alev alev
    return bk.pick(i, [
        _base(bob=7.0, lean=0.45, arm=0.5, el=0.6, ca=0.7, arm_b=0.9, el_b=1.1, mouth=0.5, glow=0.9, brow=1.0, fist_b=-1.0,
              ff=(20.0, 0.0), fb=(-20.0, 0.0), ht=0.15),
        _base(bob=2.0, lean=0.12, hx=-2.0, arm=0.95, el=0.35, ca=0.15, arm_b=1.9, el_b=1.0, mouth=0.9, glow=1.0, brow=1.0,
              fist_b=-1.0, ff=(22.0, 0.0), fb=(-22.0, 0.0), ht=-0.25, hy=-1.0),
        _base(bob=0.0, lean=-0.06, hx=-3.0, arm=1.15, el=0.25, ca=-0.15, arm_b=2.45, el_b=1.25, mouth=1.0, glow=1.0, brow=1.0,
              fist_b=-1.0, ff=(23.0, 0.0), fb=(-23.0, 0.0), ht=-0.45, hy=-2.0),
    ])


ANIMS = {
    'idle': (8, lambda i: _idle(i / 8)),
    'walk': (8, lambda i: _walk(i / 8)),
    'windup': (4, _windup),
    'strike': (4, _strike),
    'slam': (3, _slam),
    'cast': (3, _cast),
    'hurt': (2, _hurt),
    'rage': (3, _rage),
}


# ------------------------------------------------------------ parçalar
def _leg(cv, hip, foot, z, near):
    knee, _ = bk.ik2(hip, (foot[0], foot[1] - 4.5), L_TH, L_SH, -1)
    ank = (foot[0], foot[1] - 4.5)
    m = SKIN if near else SKIN_B
    thigh = bk.muscle(cv, hip, knee, 13.0, 9.0, front=1.6, back=1.2, at=0.35, knob=0.8)
    shin = bk.muscle(cv, knee, ank, 9.2, 5.8, front=0.2, back=2.4, at=0.3)
    det = []
    if near:
        det += [('ink', [along(hip, knee, 0.25, -6), along(hip, knee, 0.55, -5.5), along(hip, knee, 0.85, -4)], 1.4, (0.2, 0.6)),
                ('ink', [along(knee, ank, 0.05, 3.5), along(knee, ank, 0.25, 7.5), along(knee, ank, 0.5, 6.0)], 1.3, (0.3, 0.7)),
                ('ink', [along(hip, knee, 0.88, 4), along(hip, knee, 1.02, 5.8)], 1.2, (0.2, 0.8))]
    cv.shape(ik.union(thigh, shin), m, z=z, sd=4.0, hi=0.45 if near else 0.0, details=det, bounce=0.35 if near else 0.0,
             hatch=0.4 if near else 0.0)
    # deri dolak: baldırı saran deri şeritler + ip çapraz
    wrap = ik.isect(shin, cv.poly([along(knee, ank, 0.42, -14), along(knee, ank, 0.42, 14), along(knee, ank, 1.05, 14), along(knee, ank, 1.05, -14)]))
    lm = LEATHER if near else LEATHER_B
    wdet = []
    for k in range(5):
        t = 0.48 + k * 0.11
        wdet.append(('ink', [along(knee, ank, t, -9), along(knee, ank, t + 0.04, 0), along(knee, ank, t + 0.02, 9)], 1.1, (0.1, 0.1)))
    if near:
        for k in range(3):
            t = 0.5 + k * 0.15
            wdet.append(('stroke', [along(knee, ank, t, -6.5), along(knee, ank, t + 0.12, 6.5)], 1.6, ROPE.base, (0.05, 0.05)))
            wdet.append(('stroke', [along(knee, ank, t, 6.5), along(knee, ank, t + 0.12, -6.5)], 1.6, ROPE.shadow, (0.05, 0.05)))
    cv.shape(wrap, lm, z=z + 0.2, sd=2.0, hi=0.3 if near else 0.0, details=wdet)
    # ayak: geniş, kalın parmaklı, çıplak
    f = foot
    fpts = [(f[0] - 7.5, f[1] - 6.0), (f[0] - 2.0, f[1] - 8.0), (f[0] + 6.0, f[1] - 5.5), (f[0] + 13.0, f[1] - 3.0),
            (f[0] + 16.0, f[1] - 0.6), (f[0] + 15.5, f[1] + 0.6, 0.0), (f[0] - 8.5, f[1] + 0.6, 0.0), (f[0] - 9.5, f[1] - 3.0)]
    fdet = []
    toes = []
    for k in range(3):
        x = f[0] + 9.0 + k * 2.4
        fdet.append(('ink', [(x, f[1] - 3.2 + k * 0.6), (x + 0.4, f[1] + 0.2)], 1.1, (0.2, 0.5)))
        toes.append((x + 1.4, f[1] - 1.0 + k * 0.5))
    if near:
        fdet.append(('ink', [(f[0] - 2, f[1] - 6.5), (f[0] + 5, f[1] - 4.2)], 1.0, (0.3, 0.6)))
    cv.shape(cv.blob(fpts), m, z=z + 0.4, sd=2.4, hi=0.3 if near else 0.0, details=fdet)
    if near:
        for tp in toes:
            cv.shape(cv.ellipse(tp, 1.1, 0.75, 0.2), NAIL, z=z + 0.5, sd=0.3, ol=0.6, flat=True)
    return knee


def _club(cv, h, ca, z, p):
    d = (math.cos(ca), math.sin(ca))
    n = (-d[1], d[0])
    butt = add(h, d, -12.0)
    tip = add(h, d, CLUB_L)

    def P(t, o):
        return (butt[0] + d[0] * (CLUB_L + 12.0) * t + n[0] * o, butt[1] + d[1] * (CLUB_L + 12.0) * t + n[1] * o)
    # kütük: kökten başa kalınlaşan, budaklı, uçta kesik kök şişkinliği
    prof_o = [(0.0, 3.4), (0.15, 3.6), (0.3, 4.4), (0.42, 5.6), (0.5, 7.4), (0.58, 7.0), (0.68, 9.2), (0.78, 10.6), (0.86, 12.6),
              (0.94, 12.2), (1.0, 10.0)]
    prof_i = [(1.0, 9.5), (0.93, 12.0), (0.84, 11.2), (0.74, 10.2), (0.64, 8.0), (0.55, 7.6), (0.47, 5.2), (0.32, 4.2),
              (0.15, 3.5), (0.0, 3.2)]
    pts = [P(t, o) for t, o in prof_o] + [P(t, -o) for t, o in prof_i]
    log = cv.blob(pts)
    det = []
    # kabuk çatlakları: uzunlamasına kırık mürekkep çizgileri
    for k, (o0, t0, t1) in enumerate(((-6, 0.5, 0.95), (2, 0.62, 0.98), (7, 0.7, 0.92), (-2, 0.3, 0.55), (-9, 0.74, 0.97), (4, 0.4, 0.6))):
        det.append(('ink', [P(t0, o0), P((t0 + t1) / 2, o0 + (1.0 if k % 2 else -1.0)), P(t1, o0 * 1.15)], 1.2, (0.3, 0.4)))
    # budak gözleri
    for (t, o, r) in ((0.47, 5.0, 2.2), (0.8, -6.5, 2.6)):
        det.append(('deep', cv.ellipse(P(t, o), r, r * 0.7, ca)))
        det.append(('ink', [P(t - 0.03, o + r), P(t, o + r * 1.3), P(t + 0.03, o + r)], 1.0, (0.2, 0.2)))
    cv.shape(log, BARK, z=z, sd=3.6, hi=0.5, details=det, hatch=0.45, bounce=0.3)
    # kesik uç (açık renk odun halkaları)
    end = cv.ellipse(P(1.0, 0.0), 2.8, 10.2, ca)
    cv.shape(end, WOOD, z=z + 0.05, sd=1.2, hi=0.0, ol=0.9,
             details=[('ink', [P(1.0, -6), P(1.0, 0), P(1.0, 6)], 0.9, (0.2, 0.2))])
    # demir çemberler + perçin
    for t, w in ((0.62, 2.6), (0.88, 2.8)):
        band = ik.isect(cv.poly([P(t - w / (CLUB_L + 12) , -16), P(t + w / (CLUB_L + 12), -16), P(t + w / (CLUB_L + 12), 16), P(t - w / (CLUB_L + 12), 16)]), log)
        cv.shape(band, IRON, z=z + 0.1, sd=1.0, hi=0.35, ol=0.9,
                 details=[('col', cv.ellipse(P(t, o), 0.6, 0.6), IRON.hi) for o in (-5, 0, 5)])
    # çiviler (sivri, demir) + gömülü taşlar
    for k, (t, s_) in enumerate(((0.7, 1), (0.76, -1), (0.83, 1), (0.9, -1), (0.95, 1), (0.66, -1), (0.92, 0.0))):
        o = s_ * (10.5 if t > 0.8 else 8.8)
        if s_ == 0.0:
            continue
        base0, base1 = P(t - 0.025, o * 0.9), P(t + 0.025, o * 0.9)
        tipp = P(t + 0.01, o + s_ * 6.5)
        cv.shape(cv.blob(bk.spike_pts(base0, base1, tipp)), IRON, z=z - 0.05, sd=0.6, hi=0.25, ol=0.85)
    for (t, o, r) in ((0.74, 2.0, 2.6), (0.9, -3.5, 3.0)):
        cv.shape(cv.blob([polar(P(t, o), a, r * (0.8 + 0.25 * math.sin(a * 3))) for a in [k * 1.05 for k in range(6)]]), STONE,
                 z=z + 0.15, sd=1.2, hi=0.3, ol=0.85, details=[('ink', [P(t, o - r * 0.5), P(t + 0.02, o + r * 0.3)], 0.9)])
    # sapta deri sargı
    grip = ik.isect(log, cv.poly([P(0.02, -8), P(0.3, -8), P(0.3, 8), P(0.02, 8)]))
    cv.shape(grip, LEATHER, z=z + 0.12, sd=1.0, hi=0.25, ol=0.8,
             details=[('ink', [P(0.04 + k * 0.045, -4.5), P(0.07 + k * 0.045, 4.5)], 1.0, (0.1, 0.1)) for k in range(6)])
    return tip


HS = 0.84   # baş ölçeği (dev gövdeye göre küçük baş: daha tehditkâr siluet)


def _head(cv, H, p, z):
    ht = p['ht']
    jaw = p['mouth']
    glow = p['glow']
    ca_, sa_ = math.cos(ht), math.sin(ht)

    def Q(u, v, *t):
        u, v = u * HS, v * HS
        return (H[0] + u * ca_ - v * sa_, H[1] + u * sa_ + v * ca_) + tuple(t)
    jd = jaw * 7.0
    # alt çene: menteşe (-2, 5) etrafında açılır
    ja = jaw * 0.42

    def J(u, v):
        uu, vv = u + 2.0, v - 5.0
        return Q(-2.0 + uu * math.cos(ja) - vv * math.sin(ja), 5.0 + uu * math.sin(ja) + vv * math.cos(ja))
    # (J alt çenenin noktaları; Q ölçeği uygular)
    # ağız içi
    if jaw > 0.12:
        cv.fill(cv.blob([Q(4, 6.5), Q(18, 7.5), J(17, 9.5), J(6, 12), J(0, 9)]), MOUTH_IN, z=z + 0.2)
        # dil
        cv.fill(cv.blob([J(3, 11), J(11, 11.5), J(14, 10.2), J(6, 9.5)]), (0.62, 0.22, 0.24), z=z + 0.25)
    # alt çene + azı dişleri
    lower = cv.blob([J(-6, 5), J(4, 8.5), J(16, 9.0), J(20, 11.0), J(18.5, 15.5), J(12, 18.5), J(2, 18.0), J(-6, 13.0)])
    cv.shape(lower, SKIN, z=z + 0.3, sd=2.6, hi=0.3, bounce=0.3,
             details=[('ink', [J(4, 15.5), J(10, 17), J(15, 15)], 1.2, (0.3, 0.5))])
    for (u, ln) in ((17.0, 7.0), (10.0, 5.5)):
        b0, b1 = J(u - 1.6, 9.2), J(u + 1.6, 9.2)
        tip = J(u + 1.2, 9.2 - ln)
        cv.shape(cv.blob(bk.spike_pts(b0, b1, tip, 0.4)), BONE, z=z + 0.9, sd=0.8, hi=0.3, ol=0.85)
    # kafatası + yüz (tek kontur): alçak alın, iri kaş çıkıntısı, basık geniş burun
    skull = cv.blob([Q(-15, 0), Q(-14, -9), Q(-8, -15.5), Q(1, -17.5), Q(10, -15), Q(16, -10), Q(19, -5.5), Q(19.5, -1.5),
                     Q(23.0, 2.5), Q(23.5, 5.0, 0.6), Q(20.5, 6.6), Q(18, 7.2), Q(9, 7.0), Q(1, 6.5), Q(-6, 9.5), Q(-12, 7)])
    det = []
    # göz çukuru gölgesi (kaşın altı)
    det.append(('deep', cv.blob([Q(1, -9.5), Q(9, -12), Q(17, -9), Q(17.5, -3), Q(14, 1.5), Q(4, 1.5), Q(0, -3)])))
    # yanak / burun kanadı / alın kırışıkları
    det += [('ink', [Q(18.5, 1.0), Q(16.5, 3.5), Q(17.5, 6.2)], 1.4, (0.2, 0.4)),
            ('ink', [Q(13, 3), Q(8, 5.2), Q(3, 4.4)], 1.1, (0.3, 0.6)),
            ('ink', [Q(-2, -14), Q(4, -15.5), Q(9, -14)], 1.0, (0.3, 0.4)),
            ('ink', [Q(-4, -11.5), Q(2, -13), Q(7, -12.4)], 0.9, (0.3, 0.4)),
            ('ink', [Q(-11, -2), Q(-9, 3), Q(-6, 6)], 1.2, (0.3, 0.3))]
    cv.shape(skull, SKIN, z=z + 0.5, sd=3.4, hi=0.5, details=det, cast=1.2, bounce=0.35, hatch=0.35)
    # kulak: küçük, sivri, delik memeli (kemik halka)
    ear = cv.blob([Q(-8, -6), Q(-12, -10), (Q(-14.5, -14)[0], Q(-14.5, -14)[1], 0.0), Q(-12.5, -4), Q(-9.5, 0)])
    cv.shape(ear, SKIN_D, z=z + 0.6, sd=1.3, hi=0.2, details=[('ink', [Q(-10.5, -4.5), Q(-11.5, -8.5)], 1.0)])
    cv.shape(cv.ellipse(Q(-10.5, 0.5), 1.4, 1.4), BONE, z=z + 0.65, sd=0.5, ol=0.7)
    # saç: kafanın arkasında yabani kara perçem (geriye savrulur)
    hair_pts = [Q(-6, -15.5), Q(-11, -14)]
    tl = []
    for k in range(6):
        a = math.pi * (1.05 + k * 0.09) + ht + math.sin(p['ph'] + k) * 0.06
        b = Q(-4 - k * 2.2, -16 + k * 2.6)
        tl.append([add(b, (math.cos(a + 1.6), math.sin(a + 1.6)), 2.0), polar(b, a, 9.0 - k * 0.6) + (0.0,), add(b, (math.cos(a - 1.6), math.sin(a - 1.6)), 2.0)])
    hair = ik.union(*[cv.blob(t) for t in tl], cv.blob(hair_pts + [Q(-14, -6), Q(-4, -12)]))
    cv.shape(hair, HAIR, z=z + 0.45, sd=1.6, hi=0.3, fur=0.6)
    # dudak üstü (üst çene kenarı) + üst dişler
    if jaw > 0.12:
        for k in range(4):
            u = 6.5 + k * 3.3
            cv.fill(cv.blob([Q(u - 1.2, 6.6), Q(u + 1.2, 6.6), Q(u + 0.2, 9.0 + (0.8 if k % 2 else 0.0), )]), BONE.base, z=z + 0.55)
    # TEK GÖZ: iri, kehribar, damarlı akı; ışıma katmanında yanar
    ec = Q(9.0, -4.0)
    lid = p['lid']
    er = 6.4
    eye = cv.ellipse(ec, er, er * (1.0 - 0.75 * lid), ht)
    vein = [('stroke', [Q(3.5 + k * 0.4, -4.5 + (k - 1.5) * 2.2), Q(5.5, -4.2 + (k - 1.5) * 1.4), Q(6.3, -4.0 + (k - 1.5) * 0.6)], 0.8, (0.78, 0.2, 0.18), (0.1, 0.8))
            for k in range(4)]
    cv.shape(eye, EYE_W, z=z + 0.8, sd=1.6, hi=0.0, ol=1.1, details=vein)
    if lid < 0.9:
        g = 0.4 + 0.6 * glow
        ic = Q(10.6 + 0.6 * glow, -4.0)
        ir = 3.7 * (1.0 - 0.45 * lid)
        cv.fill(cv.ellipse(ic, 3.7, ir, ht), IRIS, z=z + 0.85, glow=tuple(c * g for c in IRIS_GLOW))
        cv.fill(cv.ellipse(add(ic, (-0.6, -0.5)), 2.2, ir * 0.6, ht), IRIS_HOT, z=z + 0.86, glow=tuple(c * g for c in IRIS_HOT))
        cv.fill(cv.ellipse(add(ic, (0.4, 0.0)), 1.0, ir * 0.82, ht), (0.08, 0.04, 0.03), z=z + 0.87)   # dikey bebek
        cv.fill(cv.ellipse(add(ic, (-1.5, -1.6)), 0.8, 0.6), (1.0, 1.0, 0.95), z=z + 0.88, glow=(0.6, 0.55, 0.4))
    # üst göz kapağı (ağır) + kaş çıkıntısı: öfkede kaş iner
    br = p['brow']
    upper_lid = cv.blob([Q(2.5, -6 + 1.5 * lid), Q(9, -10.8 + br * 1.8 + 6.0 * lid), Q(15.6, -6.5 + br * 2.0 + 2.0 * lid),
                         Q(15.4, -8.4 + br * 1.4), Q(9, -12.4 + br * 1.4), Q(2.0, -8.0)])
    cv.shape(upper_lid, SKIN_D, z=z + 0.9, sd=1.0, ol=1.1)
    brow = cv.blob([Q(0, -9.5 + br * 0.4), Q(6, -14.5 + br * 1.2), Q(14, -13.5 + br * 2.6), Q(19.5, -8.5 + br * 2.4),
                    Q(18.5, -6.6 + br * 2.0), Q(12, -10.8 + br * 2.4), Q(5, -11.5 + br * 0.8)])
    cv.shape(brow, SKIN, z=z + 0.95, sd=1.8, hi=0.45, cast=0.9,
             details=[('ink', [Q(4, -13.5 + br), Q(11, -12.8 + br * 2), Q(17, -9.5 + br * 2.3)], 1.0, (0.2, 0.4))])
    # burun deliği
    cv.fill(cv.ellipse(Q(21.0, 4.6), 1.4, 0.8, ht + 0.3), INK, z=z + 1.0)
    return Q(20.5, 8.5 + jd * 0.5), ec


def _arrows(cv, SC, up, fw, z, ph):
    """Sırttaki kırık Oğuz okları (ok işlemedi: saplar kırık, uçlar derinde değil)."""
    for k, (u, f, ang, ln) in enumerate(((14.0, -10.0, -2.3, 11.0), (8.0, -16.0, -2.75, 9.0), (18.0, -2.0, -1.85, 8.0))):
        b = add(add(SC, up, u), fw, f)
        a = ang + math.atan2(fw[1], fw[0])
        e = polar(b, a, ln)
        cv.shape(cv.capsule(b, e, 0.7, 0.6), SHAFT, z=z + k * 0.01, sd=0.4, ol=0.8, hi=0.2)
        if k != 1:   # kırık uç: kıymık
            cv.shape(cv.blob(bk.spike_pts(polar(e, a + 1.5, 0.6), polar(e, a - 1.5, 0.6), polar(e, a + 0.2, 2.2))), SHAFT, z=z + 0.02, sd=0.3, ol=0.7)
        else:        # yelek
            for s in (-1, 1):
                fl = cv.blob([polar(e, a, -1.0), polar(polar(e, a, -4.5), a + s * 1.4, 2.6), polar(e, a, -6.5), polar(e, a, -3.0)])
                cv.shape(fl, FLETCH, z=z + 0.02, sd=0.5, ol=0.7)
        cv.fill(cv.ellipse(b, 1.4, 1.0, a), (0.35, 0.1, 0.12), z=z - 0.01)


def draw(cv, p):
    bob, lean = p['bob'], p['lean']
    up = (math.sin(lean), -math.cos(lean))
    fw = (math.cos(lean), math.sin(lean))
    HIP = (p['hx'], -HIP_H + bob)
    SC = add(HIP, up, 54.0)
    # 3/4 önden: yakın omuz önde (göğüs görünür), uzak omuz geride ve biraz yüksekte
    sh_f = add(add(SC, fw, -5.0), up, -1.0)
    sh_b = add(add(SC, fw, 14.0), up, 3.0)
    br = p['breath']
    # baş: kısa boyun öne sarkık, iki omuz arasından çıkar (trapez kasları başın yanlarına kadar yükselir)
    H = add(add(add(SC, fw, 19.0), up, 13.0), (0.0, p['hy']))
    hip_f = add(HIP, fw, 5.0)
    hip_b = add(HIP, fw, -9.0)

    # ---- uzak kol (gövdenin arkasında)
    eb, hb = bk.arm_fk(sh_b, p['arm_b'], p['el_b'], L_UP, L_FO)
    up_b = bk.muscle(cv, sh_b, eb, 11.0, 8.4, front=1.0, back=2.0, at=0.4, knob=0.6)
    fo_b = bk.muscle(cv, eb, hb, 8.6, 6.2, front=1.6, back=0.6, at=0.25)
    cv.shape(ik.union(up_b, fo_b), SKIN_B, z=-20, sd=3.6, bounce=0.2)
    # pranga + kırık zincir (uzak bilek)
    cuff = ik.isect(fo_b, cv.poly([along(eb, hb, 0.72, -12), along(eb, hb, 0.72, 12), along(eb, hb, 0.9, 12), along(eb, hb, 0.9, -12)]))
    cv.shape(cuff, IRON.darker(0.8), z=-19.8, sd=1.2, hi=0.3, details=[('ink', [along(eb, hb, 0.81, -7), along(eb, hb, 0.81, 7)], 0.9)])
    q = along(eb, hb, 0.85, 7.5)
    for k in range(3):
        nq = (q[0] + 1.0 + math.sin(p['ph'] + k) * 0.8, q[1] + 3.2)
        cv.shape(cv.ellipse(lerp(q, nq, 0.5), 1.2 if k % 2 == 0 else 0.8, 1.9, 0.15), IRON.darker(0.8), z=-19.7 + k * 0.01, sd=0.5, ol=0.8)
        q = nq
    dhb = bk.perp(eb, hb)[1]
    if p['rock'] > 0:          # yükseltilen kaya (cast): elin üstünde
        rc = add(hb, dhb, 10.0)
        rr = 16.0 * p['rock']
        rock = cv.blob([polar(rc, k * 0.785 + 0.2 + 0.15 * math.sin(k * 1.7), rr * (0.86 + 0.16 * math.sin(k * 2.3 + 0.5))) + ((0.0,) if k % 3 == 0 else (0.55,)) for k in range(8)])
        cdet = [('ink', [polar(rc, 2.4, rr * 0.7), rc, polar(rc, -0.2, rr * 0.6)], 1.3, (0.2, 0.4)),
                ('ink', [polar(rc, 1.0, rr * 0.8), polar(rc, 1.3, rr * 0.2)], 1.1, (0.2, 0.4))]
        cv.shape(rock, STONE, z=-19.75, sd=4.0, hi=0.5, details=cdet, hatch=0.5, bounce=0.3)
        bk.crack_glow(cv, [polar(rc, 2.6, rr * 0.55), polar(rc, 2.0, rr * 0.2), polar(rc, 0.3, rr * 0.45)], 1.6, IRIS, tuple(c * 0.7 for c in IRIS_GLOW), -19.74)
        bk.open_hand(cv, hb, dhb, 7.6, SKIN_B, -19.85, spread=1.1, curl=0.6, near=False, claws=NAIL)
    elif p['fist_b'] < 0 or p['arm_b_open'] < 0.5:
        cv.shape(cv.ellipse(add(hb, dhb, 4.0), 7.8, 7.0), SKIN_B, z=-19.6, sd=2.4,
                 details=[('ink', [add(add(hb, dhb, 6.5), (-dhb[1], dhb[0]), k * 2.5 - 2.5), add(add(hb, dhb, 10.0), (-dhb[1], dhb[0]), k * 2.5 - 2.5)], 1.0) for k in range(3)])
    else:
        bk.open_hand(cv, hb, dhb, 7.6, SKIN_B, -19.6, spread=0.8, curl=0.5, near=False, claws=NAIL)

    # ---- bacaklar
    _leg(cv, hip_b, p['fb'], -15, False)

    # ---- gövde: kalça + göbek + göğüs kafesi + sırt + trapez (tek kontur)
    def T(u, f):
        return add(add(HIP, up, u), fw, f)
    pelvis = cv.ellipse(T(4.0, 0.0), 19.0, 13.5, lean)
    belly = cv.ellipse(T(18.0, 9.0 + br * 0.6), 21.0 + br * 0.5, 19.5, lean)
    chest = cv.ellipse(T(38.0, 7.0), 25.0, 19.0, lean)
    back = cv.ellipse(T(34.0, -10.0), 15.0, 20.0, lean)
    traps = cv.blob([T(46.0, -18.0), T(58.0, -14.0), T(64.0, -3.0), T(63.0, 12.0), T(56.0, 24.0), T(46.0, 24.0)])
    shoulders = cv.capsule(sh_f, sh_b, 12.5, 11.5)
    nape = cv.capsule(T(56.0, 6.0), add(H, (-5.0, 5.0)), 12.0, 9.0)
    torso = ik.union(pelvis, belly, chest, back, traps, shoulders, nape)
    tdet = []
    # sırt kası ayrımı, kaburga gölgeleri, göbek altı kıvrımı
    tdet += [('ink', [T(52.0, -20.0), T(42.0, -24.0), T(28.0, -21.0)], 1.4, (0.3, 0.5)),
             ('ink', [T(31.0, -7.0), T(29.0, -1.0)], 1.0, (0.3, 0.3)),
             ('ink', [T(27.0, -9.0), T(25.0, -3.0)], 1.0, (0.3, 0.3)),
             ('ink', [T(9.0, 4.0), T(4.0, 15.0), T(7.5, 27.0)], 1.6, (0.3, 0.4)),
             ('ink', [T(17.0, 26.0), T(15.6, 27.0)], 1.8, (0.2, 0.2))]
    tdet += cv.fold([T(30.0, 24.0), T(25.0, 28.0), T(18.0, 30.5)], 1.0, 1.2, 1)
    # yara izleri (dikişli) — Oğuz kılıçlarının izleri
    s0, s1 = T(44.0, -10.0), T(26.0, 10.0)
    tdet.append(('stroke', [s0, lerp(s0, s1, 0.5), s1], 2.4, SKIN.hi, (0.2, 0.2)))
    tdet.append(('ink', [add(s0, (0.6, 0.6)), add(lerp(s0, s1, 0.5), (0.6, 0.6)), add(s1, (0.6, 0.6))], 0.9, (0.2, 0.2)))
    for k in range(4):
        m = lerp(s0, s1, 0.15 + k * 0.23)
        tdet.append(('ink', [add(m, (-1.4, -1.6)), add(m, (1.4, 1.6))], 0.8, (0.1, 0.1)))
    cv.shape(torso, SKIN, z=0, sd=9.0, hi=0.7, details=tdet, cast=1.4, bounce=0.45, hatch=0.55, deep=0.35)
    # göğüs kasları: iki kütle (yakın büyük, uzak öne dönük dar), aralarında göğüs kemiği oluğu
    pdet_all = []
    for k, (f0, f1, w_) in enumerate(((0.0, 16.0, 1.0), (16.5, 29.0, 0.8))):
        pec = cv.blob([T(51.0, f0 + 2.0), T(52.0, f1 - 1.0), T(46.0, f1 + 1.5), T(36.0, f1 + 0.5), T(32.0, (f0 + f1) / 2 + 1.0),
                       T(34.0, f0 + 1.5), T(42.0, f0)])
        pdet = [('ink', [T(34.0, f0 + 2.0), T(32.0, (f0 + f1) / 2), T(35.0, f1)], 1.5, (0.2, 0.4))]
        for j in range(5):   # göğüs kılları
            c0 = T(44.0 - (j % 3) * 3.0, f0 + 3.0 + j * (f1 - f0 - 4.0) / 5.0)
            pdet.append(('ink', [c0, add(c0, (0.8, 1.9))], 0.8, (0.1, 0.7)))
        cv.shape(pec, SKIN, z=0.4 + k * 0.01, sd=4.5 * w_, hi=0.5, cast=1.6, bounce=0.35, details=pdet, ol=0.8)
    # karın: sarkık göbek kütlesi
    gut = cv.ellipse(T(15.0, 17.0 + br * 0.6), 13.5, 13.0 + br * 0.4, lean)
    cv.shape(gut, SKIN, z=0.3, sd=4.5, hi=0.4, cast=1.2, bounce=0.35, ol=0.7,
             details=[('ink', [T(15.0, 25.0), T(13.5, 25.5)], 1.8, (0.2, 0.2))])
    # sırt okları
    _arrows(cv, SC, up, fw, 0.5, p['ph'])

    # ---- kemer + post etek (kalçayı saran kaba koyun postu, yırtık etek ucu)
    belt = ik.isect(torso, cv.poly([T(2.0, -40), T(2.0, 40), T(10.5, 40), T(10.5, -40)]))
    bdet = [('ink', [T(6.3, -22), T(6.8, 0), T(6.0, 24)], 0.9, (0.1, 0.1))]
    skirt = cv.blob([T(6.0, -20.0), T(6.0, 22.0)] + bk.ragged([T(-20.0, 24.0), T(-25.0, 10.0), T(-23.0, -6.0), T(-18.0, -21.0)], 3.4, 6, 1.0, 2.0))
    sdet = cv.fold([T(2.0, 13.0), T(-9.0, 15.0), T(-20.0, 13.0)], 1.4, 1.3, 1)
    sdet += cv.fold([T(1.0, -4.0), T(-10.0, -5.0), T(-19.0, -3.0)], 1.2, 1.2, 1)
    sdet += cv.fold([T(-2.0, 4.0), T(-12.0, 5.0), T(-22.0, 4.5)], 0.9, 1.1, -1)
    cv.shape(skirt, WOOL, z=3, sd=4.0, hi=0.4, fur=1.0, details=sdet, bounce=0.3, hatch=0.4)
    cv.shape(belt, LEATHER, z=3.5, sd=2.2, hi=0.35, details=bdet)

    # ---- yakın bacak
    _leg(cv, hip_f, p['ff'], 2.0, True)
    # kemik toka + asılı boynuz
    bc = add(add(HIP, up, 6.5), fw, 14.0)
    cv.shape(cv.blob([add(bc, (-4.5, -3)), add(bc, (4.5, -3.5)), add(bc, (5.5, 3.2)), add(bc, (-4, 3.6))]), BONE, z=9, sd=1.2, hi=0.4,
             details=[('ink', [add(bc, (-2.5, 0)), add(bc, (2.8, 0))], 1.0)])
    hn0 = add(add(HIP, up, 5.0), fw, -8.0)
    horn = cv.blob([hn0, add(hn0, (3.0, 1.0)), add(hn0, (1.5, 10.0)), (add(hn0, (-3.5, 15.0))[0], add(hn0, (-3.5, 15.0))[1], 0.0), add(hn0, (-1.5, 8.0))])
    cv.shape(horn, BONE, z=8.5, sd=1.3, hi=0.3, details=[('ink', [add(hn0, (0.5, 4)), add(hn0, (2.2, 4.6))], 0.9), ('ink', [add(hn0, (0, 7.5)), add(hn0, (1.8, 8))], 0.9)])

    # ---- kolye: ip + kemikler + kafatası (göğsün üstünde)
    nk0 = add(add(SC, fw, 1.0), up, 2.0)
    nk1 = add(add(SC, fw, 21.0), up, -2.0)
    nmid = add(add(SC, fw, 13.0), up, -15.0)
    rope = [nk0, lerp(nk0, nmid, 0.5), nmid, lerp(nmid, nk1, 0.5), nk1]
    cv.stroke(rope, 1.6, z=10, col=ROPE.shadow, taper=(0.1, 0.1))
    for k, t in enumerate((0.15, 0.3, 0.45, 0.62, 0.78, 0.9)):
        q = bk.lerp(rope[int(t * 4)], rope[min(4, int(t * 4) + 1)], (t * 4) % 1.0)
        a = math.pi * 0.5 + (t - 0.5) * 0.8
        tip = polar(q, a, 6.0 if k % 2 else 4.5)
        cv.shape(cv.blob(bk.spike_pts(polar(q, a + 1.6, 1.3), polar(q, a - 1.6, 1.3), tip, 0.3)), BONE, z=10.2 + k * 0.01, sd=0.7, hi=0.3, ol=0.8)
    # kafatası pandantif
    sk = add(nmid, (0.0, 3.0))
    skull = cv.blob([add(sk, (-4.2, -1)), add(sk, (-3.2, -4.6)), add(sk, (0.5, -5.6)), add(sk, (4.0, -3.8)), add(sk, (4.6, 0.5)),
                     add(sk, (3.0, 3.0)), add(sk, (2.4, 5.6)), add(sk, (-2.2, 5.6)), add(sk, (-2.8, 3.0)), add(sk, (-4.4, 1.5))])
    sdet = [('col', cv.ellipse(add(sk, (-1.6, 0.0)), 1.3, 1.5), INK), ('col', cv.ellipse(add(sk, (2.0, -0.2)), 1.2, 1.4), INK),
            ('col', cv.blob([add(sk, (0.2, 1.8)), add(sk, (0.9, 3.0)), add(sk, (-0.4, 3.0))]), INK),
            ('ink', [add(sk, (-1.6, 4.6)), add(sk, (1.8, 4.6))], 0.8, (0.1, 0.1))]
    cv.shape(skull, BONE, z=10.5, sd=1.5, hi=0.4, details=sdet)

    # ---- baş
    mouth, ec = _head(cv, H, p, 12.0)

    # ---- yakın kol + gürz
    ef, hf = bk.arm_fk(sh_f, p['arm'], p['el'], L_UP, L_FO)
    ca = p['ca']
    d = (math.cos(ca), math.sin(ca))
    up_f = bk.muscle(cv, sh_f, ef, 12.5, 9.2, front=1.8, back=2.6, at=0.42, knob=0.8)
    fo_f = bk.muscle(cv, ef, hf, 9.6, 7.0, front=2.2, back=0.8, at=0.25)
    deltoid = cv.ellipse(add(sh_f, bk.perp(sh_f, ef)[1], 3.0), 14.0, 12.0, math.atan2(ef[1] - sh_f[1], ef[0] - sh_f[0]))
    adet = [('ink', [along(sh_f, ef, 0.45, -12.5), along(sh_f, ef, 0.55, -10.0), along(sh_f, ef, 0.62, -7.0)], 1.3, (0.2, 0.6)),
            ('ink', [along(ef, hf, 0.1, 9.0), along(ef, hf, 0.3, 9.5), along(ef, hf, 0.5, 7.5)], 1.2, (0.3, 0.6)),
            ('ink', [along(sh_f, ef, 0.92, 4.0), along(sh_f, ef, 1.04, 6.5)], 1.2, (0.2, 0.8))]
    cz = p['cz']
    arm_z = 20.0
    # gürz önce (elin altında), el en üstte
    tip = _club(cv, hf, ca, cz if cz < 0 else arm_z - 0.5, p)
    cv.shape(ik.union(deltoid, up_f, fo_f), SKIN, z=arm_z, sd=4.2, hi=0.5, details=adet, bounce=0.35, hatch=0.35, cast=1.0)
    # deri bileklik
    wr = ik.isect(fo_f, cv.poly([along(ef, hf, 0.7, -14), along(ef, hf, 0.7, 14), along(ef, hf, 0.9, 14), along(ef, hf, 0.9, -14)]))
    cv.shape(wr, LEATHER, z=arm_z + 0.1, sd=1.3, hi=0.3, details=[('ink', [along(ef, hf, 0.78, -6), along(ef, hf, 0.8, 6)], 0.9)])
    bk.hand_grip(cv, hf, d, 8.6, SKIN, arm_z + 0.3, near=True, ring=GOLD, ring_glow=RING_GLOW)
    return {'hand': hf, 'mouth': mouth, 'eye': ec, 'club': tip}


SHADE = dict(outer=0.65, rim=0.55, rim_col=(0.7, 0.85, 1.0), rim_dir=(0.6, -0.8), rim_w=1.8, form=(11.0, (0.74, 0.7, 0.86)))


def render_frame(anim, i, ss=3):
    n, fn = ANIMS[anim]
    p = fn(i)
    cv = bk.new_canvas(CELL, FEET, ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
