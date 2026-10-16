"""Erlik Han — stil v2 "mürekkep-cel" boss (inkkit.py + bosskit.py). v1: creatures3.draw_erlik.

Yeraltının (Tamu) hükümdarı. Altay/Yakut anlatılarındaki gibi: kara sakalı beline inen, bıyıkları kulaklarına
dolanan, gözleri ve kaşları kapkara, alnından iri boğa boynuzları çıkan dev; demirden sarayının efendisi. Kara demir
lamel zırh (göğsünde boğa kafatası amblemi; çatlaklarından tamu ocağı kor gibi yanar), boğa boynuzu biçimli demir
omuzluklar, kor kenarlı yırtık kara pelerin, önü açık uzun kaftan (altın tamga işlemeli, eteği için için yanar),
demir dizlik ve çizme. Elinde "bolat" topuz: kanatlı, çivili demir baş, çatlaklarından ateş sızar. Başının arkasında
alev halesi; gözler, göğüs ocağı, topuz çatlakları ve alevler ışıma katmanında.

Animasyon adları / kare sayıları / fps v1 ile aynı (idle 8, walk 8, windup 4, strike 4, slam 3, cast 3, hurt 2, rage 3);
çapalar 'hand' (topuz eli) ve 'mouth'. Hücre dünya 256x200 (v1 200x200; savuruş menzili sağa uzanır), ayak (96, 194).
"""
import math

import inkkit as ik
from inkkit import Ink
import bosskit as bk
from bosskit import along, add, lerp, polar

TEX = bk.TEX
CELL = (1024, 800)
FEET = (384, 776)

# ------------------------------------------------------------ malzemeler
SKIN = Ink('#5e5a72', '#2a2638', '#8a86a2', '#16131e', name='kül teni')
SKIN_B = SKIN.darker(0.75, 'uzak ten')
BEARD = Ink('#2c2838', '#121018', '#6a6488', '#08070c', kind='fur', name='kara sakal')
IRON = Ink('#4a4c5a', '#1e1e2a', '#9096aa', '#101018', kind='metal', name='kara demir')
IRON_B = IRON.darker(0.72)
ROBE = Ink('#3a1a26', '#1a0a16', '#64303a', '#0e050c', name='kara kızıl kaftan')
ROBE_B = ROBE.darker(0.72)
LINING = Ink('#7a1e1e', '#3a0a14', '#a8382c', name='kızıl astar')
CAPE = Ink('#1e1a24', '#0c0a12', '#3a3446', name='kara pelerin')
GOLD = Ink('#c89a3e', '#6a3e1a', '#f4d68a', kind='metal', name='kararmış altın')
HORN = Ink('#cfc2a0', '#6e5e4a', '#f4ecd0', '#3e3226', name='boğa boynuzu')
LEATHER = Ink('#4a2e24', '#22140f', '#6e4636', name='deri')
BONE = Ink('#ddd0b0', '#857558', '#fbf4dc', name='kemik')
EMBER = (1.0, 0.45, 0.10)
EMBER_HOT = (1.0, 0.82, 0.35)
EMBER_GLOW = (1.0, 0.36, 0.05)
FIRE = ((0.85, 0.16, 0.04), (1.0, 0.5, 0.08), (1.0, 0.86, 0.4))
EYE = (1.0, 0.62, 0.12)

HIP_H = 66.0
L_TH, L_SH = 33.0, 33.0
L_UP, L_FO = 30.0, 28.0
MACE_L = 60.0


def _base(**kw):
    d = dict(bob=0.0, lean=0.08, hx=0.0, ff=(13.0, 0.0), fb=(-12.0, 0.0), arm=0.35, el=0.45, arm_b=0.2, el_b=0.5,
             ca=1.05, cz=18.0, mouth=0.0, glow=0.7, hy=0.0, ht=0.0, brow=0.3, orb=0.0, ph=0.0, fl=0.0, cape=0.0,
             open_b=0.6, wind=0.0)
    d.update(kw)
    return d


def _idle(t):
    s = math.sin(t * math.tau)
    return _base(bob=1.2 * s, arm=0.32 + 0.02 * s, el=0.5, arm_b=0.18 - 0.03 * s, el_b=0.6, ca=1.05 + 0.02 * s,
                 glow=0.6 + 0.3 * (0.5 + 0.5 * math.sin(t * math.tau * 2)), hy=0.6 * s, ph=t * math.tau, fl=t * math.tau,
                 cape=0.15 * s)


def _walk(t):
    ph = t * math.tau
    s = math.sin(ph)
    stride = 15.0

    def foot(phase):
        return (stride * math.sin(phase), -max(0.0, math.cos(phase)) ** 1.5 * 7.0)
    ff, fb = foot(ph), foot(ph + math.pi)
    return _base(bob=-abs(s) * 2.6 + 1.0, lean=0.12, ff=(ff[0] + 5, ff[1]), fb=(fb[0] - 6, fb[1]), arm=0.4 - 0.12 * s, el=0.5,
                 arm_b=0.2 + 0.2 * s, el_b=0.55, ca=1.0 - 0.06 * s, glow=0.75, hy=1.0 * abs(s), ph=ph, fl=ph * 2, cape=0.5 + 0.2 * s,
                 hx=1.2 * s, wind=0.6)


def _windup(i):
    # topuzu yana-geriye çeker; uzak el önde pençe gibi açık, alev halesi kabarır; son kare tutulur
    return bk.pick(i, [
        _base(bob=2.0, lean=0.12, arm=0.2, el=0.8, ca=-0.2, arm_b=0.6, el_b=0.6, glow=0.8, mouth=0.2, fl=1.0, cape=0.3),
        _base(bob=4.0, lean=0.04, hx=-1.5, arm=-0.5, el=1.3, ca=-2.3, cz=-6.0, arm_b=1.0, el_b=0.5, glow=0.9, mouth=0.45, brow=0.8,
              ff=(17.0, 0.0), fb=(-17.0, 0.0), fl=2.0, cape=0.5),
        _base(bob=7.0, lean=-0.02, hx=-3.0, arm=-0.95, el=1.6, ca=-2.75, cz=-8.0, arm_b=1.35, el_b=0.3, glow=1.0, mouth=0.8, brow=1.0,
              ff=(21.0, 0.0), fb=(-19.0, 0.0), fl=3.0, cape=0.7, open_b=1.0),
        _base(bob=9.0, lean=-0.05, hx=-4.0, arm=-1.1, el=1.7, ca=-2.9, cz=-8.0, arm_b=1.45, el_b=0.25, glow=1.0, mouth=0.95, brow=1.0,
              ff=(23.0, 0.0), fb=(-20.0, 0.0), fl=4.0, cape=0.8, open_b=1.0),
    ])


def _strike(i):
    return bk.pick(i, [
        _base(bob=6.0, lean=0.2, hx=3.0, arm=1.5, el=1.0, ca=-2.7, cz=-6.0, arm_b=0.2, el_b=0.9, mouth=1.0, glow=1.0, brow=1.0,
              ff=(22.0, 0.0), fb=(-16.0, 0.0), fl=1.0, cape=0.9, wind=1.0),
        _base(bob=5.0, lean=0.32, hx=4.0, arm=1.18, el=0.3, ca=0.42, cz=22.0, arm_b=-0.25, el_b=0.8, mouth=1.0, glow=1.0, brow=1.0,
              ff=(26.0, 0.0), fb=(-15.0, 0.0), fl=2.0, cape=1.0, wind=1.0),
        _base(bob=8.0, lean=0.45, hx=6.0, arm=0.95, el=0.15, ca=0.95, cz=22.0, arm_b=-0.35, el_b=0.7, mouth=0.85, glow=1.0, brow=0.9,
              ff=(27.0, 0.0), fb=(-14.0, 0.0), fl=3.0, cape=0.8, wind=0.8),
        _base(bob=5.0, lean=0.36, hx=4.0, arm=0.7, el=0.3, ca=1.1, cz=22.0, arm_b=0.0, el_b=0.6, mouth=0.5, glow=0.85, brow=0.5,
              ff=(24.0, 0.0), fb=(-15.0, 0.0), fl=4.0, cape=0.5, wind=0.4),
    ])


def _slam(i):
    return bk.pick(i, [
        _base(bob=5.0, lean=0.0, hx=-2.0, arm=2.15, el=1.75, ca=-2.95, cz=-6.0, arm_b=2.2, el_b=1.5, mouth=1.0, glow=1.0, brow=1.0,
              ff=(10.0, -5.0), fb=(-12.0, -4.0), fl=1.0, cape=1.0, open_b=0.0),
        _base(bob=2.0, lean=0.35, hx=4.0, arm=1.75, el=0.15, ca=0.55, cz=22.0, arm_b=1.6, el_b=0.2, mouth=1.0, glow=1.0, brow=1.0,
              ff=(20.0, 0.0), fb=(-17.0, 0.0), fl=2.0, cape=0.9, open_b=0.0, wind=1.0),
        _base(bob=11.0, lean=0.6, hx=6.0, arm=1.05, el=0.15, ca=1.3, cz=22.0, arm_b=0.85, el_b=0.2, mouth=0.8, glow=1.0, brow=0.8,
              ff=(24.0, 0.0), fb=(-21.0, 0.0), fl=3.0, cape=0.6, open_b=0.0),
    ])


def _cast(i):
    return bk.pick(i, [
        # 0: salış: uzak el öne itilmiş (ateş elden çıktı), alev halesi parlıyor
        _base(bob=3.0, lean=0.3, hx=4.0, arm=0.35, el=0.45, ca=1.0, arm_b=1.7, el_b=0.05, mouth=0.9, glow=1.0, brow=0.9,
              ff=(20.0, 0.0), fb=(-15.0, 0.0), fl=1.0, orb=0.35, open_b=1.0, cape=0.6),
        _base(bob=1.5, lean=0.15, arm=0.3, el=0.5, ca=1.0, arm_b=2.0, el_b=0.95, mouth=0.4, glow=0.9, ff=(16.0, 0.0), fb=(-15.0, 0.0),
              fl=2.0, orb=0.6, open_b=1.0, cape=0.4),
        # 2: yükleniş (tutulur): uzak el başın üstünde ateş küresi tutar
        _base(bob=4.0, lean=0.0, hx=-2.0, arm=0.4, el=0.55, ca=0.95, arm_b=2.55, el_b=1.6, mouth=0.7, glow=1.0, brow=1.0,
              ht=-0.12, ff=(19.0, 0.0), fb=(-17.0, 0.0), fl=3.0, orb=1.0, open_b=1.0, cape=0.6),
    ])


def _hurt(i):
    return bk.pick(i, [
        _base(bob=3.0, lean=-0.1, hx=-5.0, arm=0.6, el=0.6, ca=0.5, arm_b=1.95, el_b=1.6, mouth=0.8, glow=0.4, ht=-0.28, hy=-1.0,
              ff=(11.0, 0.0), fb=(-17.0, 0.0), brow=-0.2, fl=1.0, cape=-0.4, open_b=1.0),
        _base(bob=2.0, lean=0.02, hx=-2.5, arm=0.45, el=0.5, ca=0.75, arm_b=1.3, el_b=1.0, mouth=0.4, glow=0.55, ht=-0.1,
              ff=(12.0, 0.0), fb=(-15.0, 0.0), fl=2.0, cape=-0.2, open_b=1.0),
    ])


def _rage(i):
    return bk.pick(i, [
        _base(bob=7.0, lean=0.3, arm=0.5, el=0.6, ca=0.8, arm_b=0.9, el_b=1.1, mouth=0.5, glow=0.9, brow=1.0,
              ff=(18.0, 0.0), fb=(-18.0, 0.0), ht=0.15, fl=1.0, cape=0.6, open_b=0.0),
        _base(bob=2.0, lean=0.05, hx=-2.0, arm=0.95, el=0.35, ca=0.25, arm_b=1.9, el_b=1.0, mouth=0.9, glow=1.0, brow=1.0,
              ff=(20.0, 0.0), fb=(-20.0, 0.0), ht=-0.22, hy=-1.0, fl=2.5, cape=0.9, orb=0.6, open_b=1.0, wind=0.8),
        _base(bob=0.0, lean=-0.08, hx=-3.0, arm=1.15, el=0.25, ca=-0.1, arm_b=1.95, el_b=1.7, mouth=1.0, glow=1.0, brow=1.0,
              ff=(21.0, 0.0), fb=(-21.0, 0.0), ht=-0.28, hy=0.0, fl=4.0, cape=1.0, orb=1.0, open_b=1.0, wind=1.0),
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
    ank = (foot[0], foot[1] - 4.5)
    knee, _ = bk.ik2(hip, ank, L_TH, L_SH, -1)
    m = ROBE if near else ROBE_B
    im = IRON if near else IRON_B
    # şalvar (uyluk) + demir baldırlık + çizme
    thigh = bk.muscle(cv, hip, knee, 11.0, 8.0, front=1.2, back=1.0, at=0.35)
    cv.shape(thigh, m, z=z, sd=3.4, bounce=0.3 if near else 0.0,
             details=cv.fold([along(hip, knee, 0.3, -4), along(hip, knee, 0.6, -2), along(hip, knee, 0.85, 1)], 0.9, 1.2, 1) if near else ())
    greave = bk.prof(cv, knee, ank, [(-0.12, 6.0), (0.1, 8.0), (0.4, 7.4), (0.85, 5.6), (1.02, 5.2)],
                     [(-0.12, 6.0), (0.1, 6.6), (0.45, 6.8), (0.85, 5.0), (1.02, 4.8)])
    gdet = [('ink', [along(knee, ank, 0.12, -6), along(knee, ank, 0.95, -4.4)], 1.0, (0.2, 0.2))] if near else []
    cv.shape(greave, im, z=z + 0.2, sd=2.4, hi=0.4 if near else 0.0, details=gdet)
    # dizlik: sivri, boğa boynuzu kıvrımlı
    kp = cv.blob([along(knee, ank, -0.22, 0.0), along(knee, ank, -0.05, 7.5), along(knee, ank, 0.25, 6.5), along(knee, ank, 0.3, -2.0),
                  along(knee, ank, 0.05, -6.0)])
    cv.shape(kp, im, z=z + 0.3, sd=1.6, hi=0.5 if near else 0.0, ol=0.9)
    f = foot
    boot = cv.blob([(f[0] - 6.5, f[1] - 9.0), (f[0] + 3.0, f[1] - 8.5), (f[0] + 9.0, f[1] - 3.5), (f[0] + 14.0, f[1] - 1.2),
                    (f[0] + 15.0, f[1] + 0.6, 0.0), (f[0] - 7.5, f[1] + 0.6, 0.0)])
    cv.shape(boot, LEATHER if near else LEATHER.darker(0.75), z=z + 0.25, sd=2.0, hi=0.3 if near else 0.0,
             details=[('ink', [(f[0] + 1, f[1] - 7.5), (f[0] + 6, f[1] - 4)], 1.0)] if near else ())
    # çizme ucu demir başlık
    cv.shape(cv.blob([(f[0] + 7.0, f[1] - 4.2), (f[0] + 14.0, f[1] - 1.4), (f[0] + 15.6, f[1] + 0.6, 0.0), (f[0] + 6.5, f[1] + 0.6, 0.0)]),
             im, z=z + 0.35, sd=1.0, hi=0.4 if near else 0.0, ol=0.85)
    return knee


def _mace(cv, h, ca, z, glow):
    d = (math.cos(ca), math.sin(ca))
    n = (-d[1], d[0])
    butt = add(h, d, -12.0)
    tip = add(h, d, MACE_L)

    def P(t, o):
        return (butt[0] + d[0] * (MACE_L + 12.0) * t + n[0] * o, butt[1] + d[1] * (MACE_L + 12.0) * t + n[1] * o)
    # sap: demir, sarmal sargılı, uçta topuz
    haft = cv.capsule(P(0.0, 0), P(0.86, 0), 2.4, 2.8)
    hdet = [('ink', [P(0.08 + k * 0.05, -2.4), P(0.1 + k * 0.05, 2.4)], 0.9, (0.1, 0.1)) for k in range(5)]
    cv.shape(haft, IRON, z=z, sd=1.2, hi=0.4, details=hdet)
    cv.shape(cv.ellipse(P(0.0, 0), 3.4, 3.4), GOLD, z=z + 0.05, sd=1.0, hi=0.3, ol=0.9)   # dip topuzu
    for t in (0.72, 0.84):
        cv.shape(cv.ellipse(P(t, 0), 1.6, 3.8, ca), GOLD, z=z + 0.05, sd=0.8, hi=0.3, ol=0.85)
    # baş: kanatlı (8 kanat), ortası yuvarlak; kanat aralarında kor çatlakları
    hc = P(0.93, 0)
    R = 9.5
    flanges = []
    for k in range(6):
        a = k / 6 * math.tau + ca + 0.3
        flanges.append(cv.blob([polar(hc, a - 0.42, R * 0.6), polar(hc, a - 0.16, R * 1.32), (polar(hc, a, R * 1.5)[0], polar(hc, a, R * 1.5)[1], 0.0),
                                polar(hc, a + 0.16, R * 1.32), polar(hc, a + 0.42, R * 0.6)]))
    cv.shape(ik.union(*flanges), IRON, z=z + 0.1, sd=2.6, hi=0.55, hatch=0.3,
             details=[('ink', [polar(hc, k / 6 * math.tau + ca + 0.3, R * 0.7), polar(hc, k / 6 * math.tau + ca + 0.3, R * 1.3)], 1.0, (0.1, 0.5)) for k in range(6)])
    core = cv.ellipse(hc, R * 0.78, R * 0.78)
    cv.shape(core, IRON, z=z + 0.2, sd=2.2, hi=0.5)
    g = 0.5 + 0.5 * glow
    for k in range(3):
        a0 = ca + k * 2.1 + 0.4
        bk.crack_glow(cv, [polar(hc, a0, R * 0.7), polar(hc, a0 + 0.35, R * 0.35), polar(hc, a0 + 0.9, R * 0.1)], 1.6, EMBER,
                      tuple(c * g for c in EMBER_GLOW), z + 0.25)
    cv.shape(cv.ellipse(add(hc, d, R * 0.9), 2.2, 2.2), GOLD, z=z + 0.3, sd=0.8, hi=0.3, ol=0.85)
    return tip


def _flame_halo(cv, H, p, z, sh_f=None, sh_b=None):
    """Omuzların ve başın arkasından yükselen alev yelesi (tamu ateşi): geniş tabanlı, yukarı kıvrılıp sivrilen
    alev dilleri; ortadakiler boynuzların arasından yükselir (ışıma katmanında)."""
    fl = p['fl']
    g = 0.6 + 0.4 * p['glow']
    a0 = sh_f if sh_f is not None else add(H, (-14.0, 20.0))
    a1 = sh_b if sh_b is not None else add(H, (10.0, 20.0))
    n = 9
    for k in range(n):
        t = k / (n - 1)
        base = lerp(a0, a1, t)
        base = (base[0], base[1] - 6.0 * math.sin(t * math.pi))
        mid = 1.0 - abs(t - 0.5) * 2.0
        ln = (24.0 + 26.0 * mid) * (0.85 + 0.15 * math.sin(fl + k * 1.9)) + 6.0 * p['wind']
        ang = -math.pi * 0.5 + (t - 0.5) * 0.9 - 0.25 * p['wind'] + 0.08 * math.sin(fl * 0.7 + k)
        bk.flame(cv, base, ang, ln, 11.0 + 5.0 * mid, FIRE, z + (0.0 if k % 2 else 0.002), seed=k * 1.3, glow_k=g, ph=fl)


def _head(cv, H, p, z):
    ht = p['ht']
    jaw = p['mouth']
    ca_, sa_ = math.cos(ht), math.sin(ht)
    S = 1.15

    def Q(u, v, *t):
        u, v = u * S, v * S
        return (H[0] + u * ca_ - v * sa_, H[1] + u * sa_ + v * ca_) + tuple(t)
    br = p['brow']
    g = 0.5 + 0.5 * p['glow']
    # boynuzlar: şakaklardan yana açılıp yukarı kıvrılan iri boğa boynuzları (lir biçimi). Yakın boynuz geriye-yukarı,
    # uzak boynuz yüzün önünde ileri-yukarı görünür.
    for side, zz, mm in ((1, z - 0.6, HORN.darker(0.8)), (-1, z + 1.4, HORN)):
        if side > 0:
            pts = [Q(5, -12), Q(10, -17), Q(17, -20), Q(23, -25), Q(25, -32), Q(23, -39)]
        else:
            pts = [Q(-2, -11), Q(-8, -15), Q(-16, -17), Q(-23, -22), Q(-26, -30), Q(-24, -39)]
        horn = ik.taper_path([cv.W(q) for q in pts], cv.u(8.5 * S), prof=lambda u: max(0.05, max(0.0, 1.0 - u) ** 0.75))
        det = []
        for k in range(1, 4):
            q0, q1 = pts[k], pts[k + 1]
            nrm = bk.perp(q0, q1)[0]
            w = 4.0 * (1 - k / 5.5) * S
            det.append(('ink', [add(q0, nrm, w * 0.95), lerp(q0, q1, 0.15), add(q0, nrm, -w * 0.95)], 1.0, (0.2, 0.2)))
        cv.shape(horn, mm, z=zz, sd=2.4, hi=0.7, details=det, bounce=0.35)
    # ağız içi (kor gibi yanar)
    # yüz: uzun, köşeli; çıkık elmacık, kartal burun, derin göz çukuru
    face = cv.blob([Q(-9, -2), Q(-8, -10), Q(-3, -14.5), Q(4, -15), Q(10, -12), Q(12.5, -7), Q(13, -4), Q(16.5, 1.0), Q(15.5, 3.2, 0.5),
                    Q(13, 4), Q(13, 7), Q(9, 9), Q(2, 8), Q(-5, 5)])
    det = [('deep', cv.blob([Q(3, -6.5), Q(9, -8.5), Q(13, -6), Q(12, -3), Q(5, -3)])),
           ('ink', [Q(12.6, -2.2), Q(14.5, 1.5), Q(13.4, 3.2)], 1.2, (0.2, 0.3)),
           ('ink', [Q(9.5, 0.0), Q(7.0, 2.6), Q(5.0, 2.5)], 1.0, (0.3, 0.5)),
           ('ink', [Q(-1, -12), Q(4, -13), Q(8, -11)], 0.9, (0.3, 0.4))]
    cv.shape(face, SKIN, z=z, sd=2.6, hi=0.35, details=det, cast=1.0, bounce=0.35, hatch=0.4)
    # kulak (sivri) + demir küpe
    cv.shape(cv.blob([Q(-4, -5), Q(-8, -9), Q(-11, -13, 0.0), Q(-9, -3), Q(-6, 0)]), SKIN, z=z + 0.1, sd=1.0, hi=0.2,
             details=[('ink', [Q(-7, -4), Q(-8.5, -8)], 0.9)])
    cv.shape(cv.ellipse(Q(-7.5, 1.0), 1.4, 1.4), GOLD, z=z + 0.15, sd=0.5, ol=0.7)
    # gözler: kor gibi yanan, kara kaşın altında
    ec = Q(8.5, -5.2)
    cv.fill(cv.blob([Q(5.5, -5.0, 0.0), Q(8.5, -6.6), Q(11.8, -5.6, 0.0), Q(8.5, -4.2)]), EYE, z=z + 0.3, glow=tuple(c * g for c in EMBER_GLOW))
    cv.fill(cv.ellipse(Q(9.2, -5.3), 0.9, 0.9), EMBER_HOT, z=z + 0.31, glow=tuple(c * g for c in EMBER_HOT))
    # kalın kara kaş: öfkede iner, alına kırışık
    cv.shape(cv.blob([Q(3.5, -8.0 + br * 0.4), Q(8.5, -10.6 + br * 1.4), Q(13.6, -8.8 + br * 2.2), Q(13.0, -7.2 + br * 2.0),
                      Q(8.0, -8.4 + br * 1.4), Q(4.0, -6.8)]), BEARD, z=z + 0.35, sd=0.8, ol=0.9)
    # sakal: çeneden beline inen kara sakal, iki örgüye ayrılır, demir halkalı; bıyık kulağa kıvrılır
    wv = math.sin(p['ph']) * 0.6 + p['wind'] * 2.5
    beard = cv.blob([Q(-5, 0), Q(2, 5), Q(8, 6.5), Q(14, 5.0), Q(15.5, 10), Q(14, 18), Q(12 - wv * 0.5, 27), Q(9 - wv, 36), Q(6 - wv, 44, 0.0),
                     Q(3 - wv, 37), Q(1 - wv * 0.6, 42, 0.0), Q(-1 - wv * 0.4, 33), Q(-3, 22), Q(-6, 10)])
    bdet = []
    for k in range(7):
        u0 = -3 + k * 2.6
        bdet.append(('stroke', [Q(u0 + 1.5, 6 + k * 0.3), Q(u0 + 2.0, 16 + k), Q(u0 + 1.0 - wv * 0.6, 27 + k * 1.2)], 1.3, BEARD.hi, (0.3, 0.6)))
        bdet.append(('ink', [Q(u0 + 2.6, 7 + k * 0.3), Q(u0 + 3.1, 17 + k), Q(u0 + 2.1 - wv * 0.6, 28 + k * 1.2)], 1.0, (0.2, 0.6)))
    cv.shape(beard, BEARD, z=z + 4.0, sd=2.8, hi=0.45, fur=0.7, details=bdet, cast=1.4)
    for k, v in enumerate((24.0, 32.0)):
        rc = Q(7.5 - wv * (0.5 + k * 0.4), v)
        cv.shape(cv.ellipse(rc, 3.6 - k * 0.6, 1.6, ht), IRON, z=z + 4.1, sd=0.8, hi=0.45, ol=0.85)
    # bıyık: kıvrık, kulağa doğru
    must = ik.taper_path([cv.W(q) for q in [Q(14.5, 4.2), Q(10, 4.0), Q(4, 2.5), Q(-1, -1.5), Q(-2.5, -5.0)]], cv.u(3.4),
                         prof=lambda u: max(0.08, 1.0 - u * 0.95))
    cv.shape(must, BEARD, z=z + 4.2, sd=0.9, hi=0.4, ol=0.9)
    # ağız: sakalın içinde koyu yarık, açılınca içi kor
    if jaw > 0.25:
        m_ = cv.blob([Q(8, 6.2), Q(13.0, 5.8), Q(12.0, 7.0 + jaw * 3.0), Q(8.5, 7.4 + jaw * 2.6)])
        cv.fill(m_, (0.2, 0.04, 0.03), z=z + 4.3)
        cv.fill(cv.blob([Q(9, 6.8 + jaw), Q(12, 6.6 + jaw), Q(11.5, 7.0 + jaw * 2.4), Q(9.4, 7.2 + jaw * 2.2)]), EMBER, z=z + 4.31,
                glow=tuple(c * 0.7 * jaw for c in EMBER_GLOW))
        for k in range(3):
            u = 8.8 + k * 1.4
            cv.fill(cv.blob([Q(u - 0.5, 6.0), Q(u + 0.5, 6.0), Q(u, 7.3, 0.0)]), BONE.base, z=z + 4.32)
    # demir taç: alın bandı + sivri dişler (boynuzların arasında)
    band = cv.blob([Q(-7.5, -12.5), Q(-3, -15.6), Q(4, -16.4), Q(10.0, -13.8), Q(10.2, -12.0), Q(4, -14.4), Q(-3, -13.8), Q(-7, -10.8)])
    cv.shape(band, IRON, z=z + 0.8, sd=1.0, hi=0.45, ol=0.95,
             details=[('col', cv.ellipse(Q(4.0, -15.0), 1.3, 1.3), EMBER)])
    cv.fill(cv.ellipse(Q(4.0, -15.0), 1.2, 1.2), EMBER, z=z + 0.82, glow=tuple(c * g for c in EMBER_GLOW))
    for k, (u, hh) in enumerate(((-4.5, 6.0), (0.5, 9.0), (5.5, 7.0), (9.5, 4.5))):
        b0, b1 = Q(u - 1.8, -15.0 - 0.4 * k), Q(u + 1.8, -15.5 - 0.3 * k)
        tip = Q(u + 0.6, -15.5 - hh - 0.3 * k)
        cv.shape(cv.blob(bk.spike_pts(b0, b1, tip)), IRON, z=z + 0.78, sd=0.8, hi=0.4, ol=0.9)
    return Q(11.5, 7.0)


def _pauldron(cv, sh, e, z, near):
    """Boğa boynuzu biçimli demir omuzluk: üç lamel + dışa kıvrılan boynuz çıkıntısı."""
    m = IRON if near else IRON_B
    pts = [along(sh, e, -0.35, -6.0), along(sh, e, -0.38, 4.0), along(sh, e, -0.1, 11.0), along(sh, e, 0.3, 11.0),
           along(sh, e, 0.48, 6.0), along(sh, e, 0.45, -5.0), along(sh, e, 0.18, -10.5)]
    det = []
    for t in (-0.05, 0.13, 0.3):
        det.append(('ink', [along(sh, e, t - 0.02, -9.0), along(sh, e, t + 0.05, 0.0), along(sh, e, t - 0.02, 10.0)], 1.2, (0.15, 0.15)))
        det.append(('stroke', [along(sh, e, t + 0.02, -8.0), along(sh, e, t + 0.07, 0.0), along(sh, e, t + 0.02, 9.0)], 0.9, GOLD.base, (0.2, 0.2)))
    cv.shape(cv.blob(pts), m, z=z, sd=2.6, hi=0.6 if near else 0.0, details=det)
    # boynuz çıkıntısı (omzun üstünden yukarı-dışa)
    b0, b1 = along(sh, e, -0.3, 2.0), along(sh, e, -0.1, 8.0)
    tip = along(sh, e, -0.62, 12.0)
    cv.shape(cv.blob(bk.spike_pts(b0, b1, tip, -1.2)), HORN if near else HORN.darker(0.75), z=z + 0.05, sd=1.2, hi=0.4, ol=0.9)


def draw(cv, p):
    bob, lean = p['bob'], p['lean']
    up = (math.sin(lean), -math.cos(lean))
    fw = (math.cos(lean), math.sin(lean))
    HIP = (p['hx'], -HIP_H + bob)

    def T(u, f):
        return add(add(HIP, up, u), fw, f)
    SC = T(56.0, 0.0)
    sh_f = T(55.0, -4.0)
    sh_b = T(59.0, 12.0)
    H = add(T(74.0, 11.0), (0.0, p['hy']))
    hip_f = T(0.0, 4.0)
    hip_b = T(0.0, -7.0)
    g = 0.5 + 0.5 * p['glow']

    # ---- alev halesi + pelerin (en arkada)
    _flame_halo(cv, H, p, -25.0, T(64.0, -12.0), T(64.0, 14.0))
    cw_ = p['cape'] + p['wind'] * 0.6
    cape_top = [T(60.0, -14.0), T(62.0, 6.0)]
    hem = [T(-50.0 + 4 * math.sin(p['ph']), 2.0 - cw_ * 10.0), T(-56.0, -14.0 - cw_ * 14.0), T(-50.0, -30.0 - cw_ * 18.0),
           T(-34.0, -40.0 - cw_ * 16.0)]
    cape = cv.blob(cape_top + bk.ragged(hem, 4.0, 6, 1.0, 1.0) + [T(10.0, -36.0 - cw_ * 8.0), T(40.0, -26.0)])
    cdet = cv.fold([T(50.0, -16.0), T(10.0, -30.0 - cw_ * 6), T(-40.0, -42.0 - cw_ * 12)], 2.0, 1.4, 1)
    cdet += cv.fold([T(46.0, -8.0), T(0.0, -18.0 - cw_ * 6), T(-46.0, -24.0 - cw_ * 12)], 1.6, 1.3, 1)
    cv.shape(cape, CAPE, z=-30, sd=5.0, hi=0.3, details=cdet, hatch=0.5)
    # pelerin ucunda için için yanan kor
    for k in range(len(hem) - 1):
        a, b = hem[k], hem[k + 1]
        bk.crack_glow(cv, [lerp(a, b, 0.1), lerp(a, b, 0.5), lerp(a, b, 0.9)], 1.4, EMBER, tuple(c * 0.6 * g for c in EMBER_GLOW), -29.9)

    # ---- uzak kol
    eb, hb = bk.arm_fk(sh_b, p['arm_b'], p['el_b'], L_UP, L_FO)
    up_b = bk.muscle(cv, sh_b, eb, 9.5, 7.6, front=1.0, back=1.4, at=0.4)
    fo_b = bk.muscle(cv, eb, hb, 7.6, 5.8, front=1.4, back=0.5, at=0.25)
    cv.shape(up_b, ROBE_B, z=-20, sd=3.0)
    cv.shape(fo_b, IRON_B, z=-19.9, sd=2.4, hi=0.2, details=[('ink', [along(eb, hb, k * 0.2 + 0.15, -7), along(eb, hb, k * 0.2 + 0.18, 7)], 1.0) for k in range(4)])
    dhb = bk.perp(eb, hb)[1]
    if p['orb'] > 0.05:      # ateş küresi (cast)
        oc = add(hb, dhb, 6.0)
        r = 4.0 + 7.0 * p['orb']
        cv.fill(cv.ellipse(oc, r * 1.25, r * 1.25), (0.85, 0.2, 0.04), z=-19.0, glow=tuple(c * 0.9 for c in EMBER_GLOW), alpha=0.85)
        cv.fill(cv.ellipse(oc, r, r), EMBER, z=-18.99, glow=EMBER)
        cv.fill(cv.ellipse(add(oc, (-r * 0.2, -r * 0.2)), r * 0.55, r * 0.55), EMBER_HOT, z=-18.98, glow=EMBER_HOT)
        for k in range(3):
            bk.flame(cv, polar(oc, -math.pi * 0.5 + (k - 1) * 0.7, r * 0.6), -math.pi * 0.5 + (k - 1) * 0.35, r * (1.3 - 0.3 * abs(k - 1)),
                     r * 1.1, FIRE, -19.01, seed=k, glow_k=1.0, ph=p['fl'])
        cv.stroke([polar(oc, 0.5, r * 0.7), polar(oc, 1.6, r * 0.75), polar(oc, 2.8, r * 0.55), polar(oc, 3.6, r * 0.2)], 1.6, z=-18.97,
                  col=(1.0, 0.95, 0.75), taper=(0.2, 0.8), glow=(1.0, 0.8, 0.4))
    bk.open_hand(cv, hb, dhb, 6.4, SKIN_B, -19.5, spread=0.5 + 0.6 * p['open_b'], curl=0.9 - 0.6 * p['open_b'], near=False,
                 claws=Ink('#20202a', '#0c0c12', '#5a5a6a'))

    # ---- bacaklar + kaftan etekleri
    back_skirt = cv.blob([T(4.0, -16.0), T(4.0, 14.0)] + bk.ragged([T(-62.0 + p['bob'], 18.0 + p['wind'] * -6), T(-64.0 + p['bob'], -4.0 - p['wind'] * 8),
                                                                     T(-60.0 + p['bob'], -24.0 - p['wind'] * 10)], 2.5, 5, 1.0, 3.0))
    cv.shape(back_skirt, ROBE_B, z=-16, sd=4.0, details=cv.fold([T(-2.0, -6.0), T(-30.0, -9.0), T(-58.0, -12.0)], 1.6, 1.3, 1))
    _leg(cv, hip_b, p['fb'], -14, False)
    _leg(cv, hip_f, p['ff'], 2, True)

    # ---- gövde: lamel zırhlı göğüs + kaftan
    torso = ik.union(cv.ellipse(T(6.0, 0.0), 17.0, 12.0, lean), cv.ellipse(T(24.0, 2.0), 18.0, 18.0, lean),
                     cv.ellipse(T(42.0, 3.0), 22.0, 17.0, lean), cv.capsule(sh_f, sh_b, 11.0, 10.0),
                     cv.capsule(T(56.0, 4.0), add(H, (-3.0, 6.0)), 9.0, 7.0))
    cv.shape(torso, ROBE, z=0, sd=7.0, hi=0.4, cast=1.2, bounce=0.35, hatch=0.4)
    # lamel göğüs zırhı (kaftanın üstünde): sıra sıra plakalar
    cuir = ik.isect(torso, cv.blob([T(56.0, -10.0), T(56.0, 22.0), T(14.0, 22.0), T(10.0, 2.0), T(14.0, -16.0)]))
    ldet = []
    for k in range(7):
        u = 50.0 - k * 5.5
        ldet.append(('ink', [T(u, -16.0), T(u - 0.5, 4.0), T(u + 0.4, 24.0)], 1.1, (0.05, 0.05)))
        for j in range(6):
            f0 = -12.0 + j * 6.0 + (3.0 if k % 2 else 0.0)
            ldet.append(('ink', [T(u, f0), T(u - 5.0, f0 + 0.3)], 0.8, (0.1, 0.1)))
    cv.shape(cuir, IRON, z=1, sd=5.0, hi=0.6, details=ldet, hatch=0.3)
    # göğüs amblemi: boğa kafatası plakası; çatlaklarından tamu ocağı yanar
    ec_ = T(38.0, 10.0)
    plate = cv.blob([add(ec_, up, 7.0), add(add(ec_, up, 4.0), fw, 7.0), add(add(ec_, up, -5.0), fw, 5.0), add(ec_, up, -9.0),
                     add(add(ec_, up, -5.0), fw, -5.0), add(add(ec_, up, 4.0), fw, -7.0)])
    cv.shape(plate, IRON, z=1.5, sd=2.4, hi=0.6, ol=1.0)
    for s in (-1, 1):   # amblem boynuzları
        b0, b1 = add(add(ec_, up, 5.0), fw, s * 4.0), add(add(ec_, up, 2.0), fw, s * 6.5)
        cv.shape(cv.blob(bk.spike_pts(b0, b1, add(add(ec_, up, 10.0), fw, s * 12.0), 1.0)), GOLD, z=1.6, sd=0.8, hi=0.4, ol=0.85)
    bk.crack_glow(cv, [add(ec_, up, 4.0), add(add(ec_, up, 0.5), fw, 1.5), add(add(ec_, up, -3.0), fw, -1.0), add(ec_, up, -7.0)], 2.2,
                  EMBER, tuple(c * g for c in EMBER_GLOW), 1.7, branch=0.7, seed=1.0)
    for s in (-1, 1):  # göz oyukları kor
        cv.fill(cv.ellipse(add(add(ec_, up, 1.0), fw, s * 2.6), 1.3, 1.0), EMBER_HOT, z=1.75, glow=tuple(c * g for c in EMBER_HOT))
    # kemer: altın tamga plakalı geniş kuşak
    belt = ik.isect(torso, cv.poly([T(9.0, -30), T(9.0, 30), T(17.0, 30), T(17.0, -30)]))
    bdet = [('col', cv.ellipse(T(13.0, f), 1.6, 1.6), GOLD.base) for f in (-6.0, 2.0, 10.0)]
    cv.shape(belt, LEATHER, z=2.5, sd=2.0, hi=0.3, details=bdet)
    bc = T(13.0, 14.0)
    cv.shape(cv.blob([add(bc, (-4, -4)), add(bc, (4, -4.5)), add(bc, (5, 4)), add(bc, (-4, 4.5))]), GOLD, z=2.6, sd=1.4, hi=0.5,
             details=[('ink', [add(bc, (-2, -2)), add(bc, (0, 2)), add(bc, (2.2, -2))], 1.1)])
    # ön etek paneli (kaftanın önü, yakın uyluğun üstünde): altın tamga işlemeli, alt ucu kor
    sw = (p['ff'][0] - 13.0) * 0.4
    panel = cv.blob([T(10.0, 2.0), T(10.0, 20.0), T(-34.0, 24.0 + sw), T(-38.0, 14.0 + sw), T(-35.0, 2.0 + sw)])
    pdet = cv.fold([T(6.0, 10.0), T(-14.0, 12.0 + sw * 0.5), T(-34.0, 13.0 + sw)], 1.2, 1.2, 1)
    pdet.append(('stroke', [T(6.0, 17.5), T(-14.0, 19.5 + sw * 0.5), T(-34.0, 21.5 + sw)], 2.2, GOLD.base, (0.05, 0.05)))
    for k in range(3):   # tamga (Erlik'in üç dişli tamgası)
        c0 = T(-12.0 - k * 9.0, 15.0 + sw * (0.3 + k * 0.25))
        pdet.append(('stroke', [add(c0, up, 3.0), add(c0, up, -3.0)], 1.2, GOLD.base, (0.1, 0.1)))
        pdet.append(('stroke', [add(add(c0, up, 3.0), fw, -2.0), add(add(c0, up, 1.5), fw, 0.0), add(add(c0, up, 3.0), fw, 2.0)], 1.0, GOLD.base, (0.1, 0.1)))
    cv.shape(panel, ROBE, z=4, sd=3.4, hi=0.3, details=pdet, bounce=0.3)
    cv.shape(ik.isect(panel, cv.poly([T(-30.0, -10), T(-30.0, 40), T(-45.0, 40), T(-45.0, -10)])), LINING, z=4.1, sd=1.0, ol=0.7)
    bk.crack_glow(cv, [T(-35.0, 2.5 + sw), T(-37.0, 12.0 + sw), T(-34.5, 23.0 + sw)], 1.4, EMBER, tuple(c * 0.6 * g for c in EMBER_GLOW), 4.2)

    # ---- baş (sakal göğsün üstüne düşer)
    mouth = _head(cv, H, p, 12.0)
    _pauldron(cv, sh_b, eb, -18.0, False)

    # ---- yakın kol + topuz
    ef, hf = bk.arm_fk(sh_f, p['arm'], p['el'], L_UP, L_FO)
    ca = p['ca']
    d = (math.cos(ca), math.sin(ca))
    arm_z = 20.0
    tip = _mace(cv, hf, ca, p['cz'] if p['cz'] < 0 else arm_z - 0.5, p['glow'])
    up_f = bk.muscle(cv, sh_f, ef, 10.0, 8.0, front=1.4, back=1.8, at=0.42)
    fo_f = bk.muscle(cv, ef, hf, 8.2, 6.2, front=1.8, back=0.7, at=0.25)
    cv.shape(up_f, ROBE, z=arm_z, sd=3.6, hi=0.35, bounce=0.3,
             details=cv.fold([along(sh_f, ef, 0.55, -8), along(sh_f, ef, 0.7, -4), along(sh_f, ef, 0.8, 0)], 0.7, 1.2, 1))
    vdet = [('ink', [along(ef, hf, k * 0.2 + 0.12, -8), along(ef, hf, k * 0.2 + 0.15, 8)], 1.1, (0.1, 0.1)) for k in range(4)]
    vdet.append(('stroke', [along(ef, hf, 0.1, 5.5), along(ef, hf, 0.85, 4.5)], 0.9, IRON.hi, (0.3, 0.3)))
    cv.shape(fo_f, IRON, z=arm_z + 0.1, sd=2.8, hi=0.5, details=vdet)
    _pauldron(cv, sh_f, ef, arm_z + 0.4, True)
    bk.hand_grip(cv, hf, d, 6.8, SKIN, arm_z + 0.3, near=True, ring=GOLD)
    return {'hand': hf, 'mouth': mouth, 'mace': tip}


SHADE = dict(outer=0.65, rim=0.75, rim_col=(1.0, 0.55, 0.3), rim_dir=(-0.6, -0.8), rim_w=1.8, form=(10.0, (0.72, 0.68, 0.86)))


def render_frame(anim, i, ss=3):
    n, fn = ANIMS[anim]
    p = fn(i)
    cv = bk.new_canvas(CELL, FEET, ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
