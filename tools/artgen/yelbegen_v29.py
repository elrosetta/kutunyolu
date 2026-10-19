"""Yelbegen v29: hamle başına tam gövde animasyonları (yelbegen_ink.draw pozlarıyla; tepegoz_ink iskelet anahtarları).

Üç başlı ayaz devi: ağır, sallanan yürüyüşte üç baş ayrı gecikmeyle sallanır (biri hırlar, biri etrafı kollar),
mızrak asa gibi yere vurulur. Hamlelerde başlar birbirinden bağımsız oynar: üfürükte üçü birden geriye çekilip
nefes alır, sonra öne uzanıp üfler; baş atışında sırayla boyun uzatıp ateş eder ve geri teper; ayaz soluğunda orta baş
yukarı kalkıp aşağı doğru huzme döker. Gürz (mızrak) savuruşunda mızrak omuz üstünden sırta düşer, adımla çakılır.

Evre bölümleri: w hazırlık, s temas, r toparlanma, a eylem / döngü, b / c / f arka / orta / ön baş atışı.
"""
import math

import bosskit as bk
import yelbegen_ink as yb
from tepegoz_ink import _base as TB

over = bk.over
Z3 = ((0.0, 0.0), (0.0, 0.0), (0.0, 0.0))


def B(**kw):
    d = TB(ca=-1.42, el=0.95, arm=0.55)
    d['heads'] = (0.0, 0.0, 0.0)
    d.update(kw)
    return d


def _geo(p):
    lean = p['lean']
    up = (math.sin(lean), -math.cos(lean))
    fw = (math.cos(lean), math.sin(lean))
    hip = (p['hx'], -yb.HIP_H + p['bob'])
    T = lambda u, f: bk.add(bk.add(hip, up, u), fw, f)
    _, hf = bk.arm_fk(T(55.0, -5.0), p['arm'], p['el'], yb.L_UP, yb.L_FO)
    _, hb = bk.arm_fk(T(59.0, 14.0), p['arm_b'], p['el_b'], yb.L_UP, yb.L_FO)
    return hf, hb


def fit(p, top=-190.0, ground=-5.0, left=-88.0, right=154.0):
    """El ve mızrak hücrede kalsın: el en çok -168'e kalkar (dirsek bükülür), mızrağın iki ucu sınır içinde, yerin altına
    girmez (uç yere değer)."""
    if p.get('rot'):
        return p
    while _geo(p)[0][1] < -168.0 and p['el'] < 2.6:
        p = over(p, el=p['el'] + 0.04)
    while _geo(p)[1][1] < -168.0 and p['el_b'] < 2.6:
        p = over(p, el_b=p['el_b'] + 0.04)
    h = _geo(p)[0]

    def ok(a):
        d = (math.cos(a), math.sin(a))
        for L in (-yb.SP_B - 7.0, yb.SP_F + yb.BLADE):
            x, y = h[0] + d[0] * L, h[1] + d[1] * L
            if not (top <= y <= ground and left <= x <= right):
                return False
        return True
    if ok(p['ca']):
        return p
    for k in range(1, 320):
        for sg in (1, -1):
            a = p['ca'] + sg * k * 0.01
            if ok(a):
                return over(p, ca=a)
    return p


def clip(frames, fps=10, loop=False, seg=None):
    return bk.clip([fit(f) for f in frames], fps, loop, seg)


def _idle(t):
    s, c = math.sin(t * math.tau), math.cos(t * math.tau)
    snap = max(0.0, math.sin((t - 0.6) * math.tau * 2.5)) if 0.6 <= t < 1.0 else 0.0     # ön baş hırlayıp atılır
    return B(bob=1.6 * s + 0.6, breath=s, lean=0.30 + 0.025 * s, hx=1.3 * c, arm=0.55 + 0.02 * s, el=0.95, ca=-1.42 + 0.02 * s,
             arm_b=0.12 - 0.04 * s, el_b=0.42, glow=0.6 + 0.3 * (0.5 + 0.5 * math.sin(t * math.tau * 2)), hy=1.0 * s, ht=0.04 * s, ph=t * math.tau,
             heads=(0.12 * s, -0.14 * math.sin(t * math.tau + 1.3), 0.1 * math.sin(t * math.tau + 2.2) + 0.25 * snap),
             hext=((0.0, 1.2 * math.sin(t * math.tau + 0.8)), (0.0, 0.0), (3.0 * snap, 1.0 * math.sin(t * math.tau + 1.9) + 1.5 * snap)),
             hj=(0.15 + 0.1 * max(0.0, c), 0.15 + 0.1 * max(0.0, s), 0.35 + 0.6 * snap), ff=(15.0 + 0.6 * c, 0.0), fb=(-15.0 + 0.6 * c, 0.0))


def _walk(t):
    S = 17.5

    def foot(ph):
        ph %= 1.0
        if ph < 0.56:
            return (S - 2 * S * ph / 0.56, 0.0)
        u = (ph - 0.56) / 0.44
        return (-S + 2 * S * (u * u * (3 - 2 * u)), -math.sin(math.pi * u) * 14.0)
    ff, fb = foot(t), foot(t + 0.5)
    w = math.cos(4 * math.pi * (t - 0.07))
    sw = math.cos(2 * math.pi * t)
    lag = lambda k: math.cos(4 * math.pi * (t - 0.07 - k))      # başlar gövdenin çöküşünü gecikmeyle izler
    return B(bob=2.6 + 3.4 * w, lean=0.36 + 0.03 * w, hx=1.0 * sw, ff=(ff[0] + 5, ff[1]), fb=(fb[0] - 7, fb[1]), arm=0.6 - 0.12 * sw, el=0.95,
             ca=-1.3 - 0.1 * sw, arm_b=0.15 + 0.32 * sw, el_b=0.5, mouth=0.2, glow=0.7, hy=1.2 * max(0.0, lag(0.06)), ht=0.04 * sw,
             ph=t * math.tau, breath=0.5 * w, heads=(0.06 * lag(0.08), -0.08 * lag(0.12), 0.08 * lag(0.16)),
             hext=((0.0, 2.0 * lag(0.12)), (0.0, 1.5 * lag(0.08)), (1.0 * sw, 2.4 * lag(0.16))), hj=(0.2, 0.25 + 0.15 * max(0.0, w), 0.5))


CLUB = [
    B(bob=3, lean=0.2, hx=-2, arm=1.2, el=1.0, ca=-2.0, arm_b=0.8, el_b=1.0, heads=(-0.2, 0.2, -0.1), mouth=0.4, brow=0.6, fb=(-17, 0)),
    B(bob=5, lean=0.02, hx=-5, arm=2.2, el=1.4, ca=-2.7, cz=-6, arm_b=1.6, el_b=1.0, heads=(-0.3, 0.3, -0.2), mouth=0.7, brow=1, ht=-0.15,
      fb=(-22, 0), ff=(17, 0), glow=0.9),
    B(bob=7, lean=-0.12, hx=-7, arm=2.4, el=1.8, ca=-3.05, cz=-8, arm_b=2.2, el_b=1.3, fist_b=-1, heads=(-0.4, 0.35, -0.3), mouth=1.0, glow=1,
      ht=-0.3, brow=1, ff=(19, -4), fb=(-23, 0), breath=1, hext=((-3, -2), (-3, -2), (-4, -2))),
    B(bob=2, lean=0.25, hx=2, arm=2.3, el=0.5, ca=-1.6, arm_b=1.6, el_b=0.6, fist_b=-1, heads=(0.0, 0.0, 0.1), mouth=1.0, glow=1, ff=(27, 0),
      fb=(-21, 0)),
    B(bob=14, lean=0.75, hx=6, arm=1.3, el=0.1, ca=0.9, arm_b=1.0, el_b=0.3, heads=(0.25, -0.2, 0.35), mouth=1.0, glow=1, ht=0.25, ff=(31, 0),
      fb=(-23, 0), hext=((3, 2), (4, 3), (4, 3))),
    B(bob=12, lean=0.7, hx=5, arm=1.2, el=0.15, ca=1.0, arm_b=0.9, el_b=0.35, heads=(0.2, -0.15, 0.3), mouth=0.7, ht=0.2, ff=(31, 0), fb=(-23, 0)),
    B(bob=11, lean=0.62, hx=4, arm=1.1, el=0.25, ca=1.05, arm_b=0.8, el_b=0.4, heads=(0.15, -0.1, 0.25), mouth=0.5, ht=0.15, ff=(31, 0), fb=(-23, 0),
      breath=1),
    B(bob=6, lean=0.45, hx=2, arm=0.8, el=0.7, ca=0.1, arm_b=0.5, el_b=0.45, heads=(0.1, -0.05, 0.15), mouth=0.35, ff=(25, 0), fb=(-19, 0)),
    B(bob=2, lean=0.32, arm=0.58, el=0.95, ca=-1.2, mouth=0.2, ff=(17, 0)),
]

_GB = ((-3.0, -3.0), (-4.0, -3.0), (-4.0, -2.0))
GUST = [
    B(bob=4, lean=0.05, hx=-3, arm=0.6, el=0.9, ca=-1.4, arm_b=1.4, el_b=1.6, fist_b=-1, heads=(-0.4, 0.4, -0.35), hext=_GB, breath=1, mouth=0.2,
      glow=0.9),
    B(bob=5, lean=-0.08, hx=-4, arm=0.6, el=0.9, ca=-1.42, arm_b=1.45, el_b=1.7, fist_b=-1, heads=(-0.5, 0.5, -0.45),
      hext=((-5, -4), (-6, -4), (-6, -3)), breath=1, hj=(0.1, 0.1, 0.15), glow=1),
    B(bob=4, lean=0.12, hx=-1, arm=0.65, el=0.9, ca=-1.38, arm_b=1.5, el_b=1.0, heads=(-0.2, 0.2, -0.1), hj=(0.5, 0.6, 0.7), glow=1),
] + [B(bob=8 + k * 0.6, lean=0.4 + 0.02 * k, hx=3, ff=(28, 0), fb=(-22, 0), arm=0.75, el=0.8, ca=-1.3, arm_b=1.5, el_b=0.3,
       heads=(0.25 + 0.04 * (k - 1), -0.25 - 0.03 * k, 0.3 + 0.04 * (1 - k)), hext=((10, 3 + k * 0.5), (12 + k * 0.6, 3), (11, 2 + k * 0.5)),
       hj=(1.0, 1.0, 1.0), glow=1, ph=k * 2.1, breath=k - 1) for k in range(3)] + [
    B(bob=4, lean=0.3, hx=1, arm=0.6, el=0.9, ca=-1.38, arm_b=0.6, el_b=0.6, heads=(0.05, 0.0, 0.1), hj=(0.3, 0.3, 0.4)),
]

_HR = ((-3.0, -2.0), (-3.0, -3.0), (-3.0, -2.0))
HEADS = [
    B(bob=3, lean=0.15, arm=0.6, el=0.95, ca=-1.4, arm_b=0.9, el_b=1.2, fist_b=-1, heads=(-0.3, 0.35, -0.3), hext=_HR, mouth=0.5, glow=1),
    B(bob=4, lean=0.1, arm=0.6, el=0.95, ca=-1.42, arm_b=1.0, el_b=1.3, fist_b=-1, heads=(-0.35, 0.4, -0.35), hext=((-4, -3), (-4, -4), (-4, -3)),
      mouth=0.7, glow=1, breath=1),
    # arka baş ateşler / geri teper
    B(bob=5, lean=0.25, arm=0.6, el=0.95, ca=-1.4, arm_b=0.9, el_b=1.1, fist_b=-1, heads=(-0.25, -0.35, -0.25), hext=((15, 5), (-4, -3), (-4, -2)),
      hj=(1.0, 0.4, 0.6), glow=1),
    B(bob=4, lean=0.2, arm=0.6, el=0.95, ca=-1.4, arm_b=0.9, el_b=1.1, fist_b=-1, heads=(-0.25, 0.35, -0.25), hext=((-2, -2), (-3, -3), (-3, -2)),
      hj=(0.5, 0.5, 0.6), glow=1),
    # orta baş
    B(bob=5, lean=0.28, arm=0.6, el=0.95, ca=-1.4, arm_b=0.9, el_b=1.1, fist_b=-1, heads=(0.35, 0.3, -0.25), hext=((-3, -2), (16, 7), (-4, -2)),
      hj=(0.4, 1.0, 0.6), glow=1),
    B(bob=4, lean=0.22, arm=0.6, el=0.95, ca=-1.4, arm_b=0.9, el_b=1.1, fist_b=-1, heads=(-0.2, 0.3, -0.2), hext=((-2, -2), (-3, -3), (-3, -2)),
      hj=(0.4, 0.5, 0.6), glow=1),
    # ön baş
    B(bob=6, lean=0.3, arm=0.6, el=0.95, ca=-1.4, arm_b=0.9, el_b=1.1, fist_b=-1, heads=(-0.2, 0.3, 0.45), hext=((-3, -2), (-3, -2), (15, 8)),
      hj=(0.4, 0.5, 1.0), glow=1),
    B(bob=4, lean=0.24, arm=0.6, el=0.95, ca=-1.4, arm_b=0.9, el_b=1.1, fist_b=-1, heads=(-0.1, 0.2, 0.0), hext=((-1, -1), (-1, -1), (-3, -2)),
      hj=(0.4, 0.5, 0.6), glow=1),
    B(bob=2, lean=0.3, arm=0.58, el=0.95, ca=-1.38, heads=(0.0, 0.0, 0.05), hj=(0.2, 0.2, 0.4)),
]

BREATH = [
    B(bob=4, lean=0.05, arm=0.6, el=0.9, ca=-1.42, arm_b=1.2, el_b=1.4, fist_b=-1, heads=(-0.5, 0.3, 0.2), hext=((0, 0), (-4, -6), (2, 0)),
      hj=(0.6, 0.3, 0.8), glow=1, breath=1),
    B(bob=5, lean=-0.06, arm=0.6, el=0.9, ca=-1.44, arm_b=1.25, el_b=1.5, fist_b=-1, heads=(-0.62, 0.35, 0.25), hext=((0, 0), (-6, -8), (2, 0)),
      hj=(0.7, 0.2, 0.9), glow=1, breath=1),
    B(bob=5, lean=0.12, arm=0.62, el=0.9, ca=-1.4, arm_b=1.2, el_b=1.0, fist_b=-1, heads=(-0.2, 0.3, 0.2), hext=((0, 0), (0, -4), (2, 0)),
      hj=(0.6, 0.8, 0.8), glow=1),
] + [B(bob=9 + 0.7 * k, lean=0.45 + 0.015 * k, hx=3, ff=(28, 0), fb=(-22, 0), arm=0.7, el=0.85, ca=-1.3, arm_b=1.1, el_b=0.8, fist_b=-1,
       heads=(0.55 + 0.04 * (k - 1), 0.2, 0.3), hext=((0, 0), (14 + k * 0.6, 7 + 0.5 * k), (2, 1)), hj=(0.7, 1.0, 0.8), glow=1, breath=k - 1)
     for k in range(3)] + [
    B(bob=4, lean=0.3, arm=0.6, el=0.9, ca=-1.38, arm_b=0.6, el_b=0.6, heads=(0.0, 0.0, 0.1), hj=(0.3, 0.3, 0.4)),
]

ICICLES = [
    B(bob=2, lean=0.05, arm=2.6, el=0.3, ca=-1.57, arm_b=2.2, el_b=0.6, fist_b=-1, heads=(-0.4, 0.4, -0.4), hj=(0.8, 0.8, 0.8), glow=1, ht=-0.3),
    B(bob=0, lean=-0.06, arm=2.7, el=0.2, ca=-1.57, arm_b=2.4, el_b=0.5, fist_b=-1, heads=(-0.5, 0.5, -0.5), hj=(1.0, 1.0, 1.0), glow=1, ht=-0.4,
      breath=1),
    B(bob=15, lean=0.4, hx=3, arm=1.2, el=0.3, ca=-1.4, arm_b=0.9, el_b=0.4, fist_b=-1, heads=(0.1, -0.1, 0.2), hj=(1.0, 1.0, 1.0), glow=1, ht=0.1,
      ff=(24, 0), fb=(-20, 0), hext=((2, 2), (3, 3), (3, 3))),
    B(bob=13, lean=0.36, hx=3, arm=1.15, el=0.35, ca=-1.42, arm_b=0.8, el_b=0.45, heads=(0.05, -0.05, 0.15), hj=(0.8, 0.8, 0.8), glow=1,
      ff=(24, 0), fb=(-20, 0)),
    B(bob=5, lean=0.32, arm=0.62, el=0.9, ca=-1.4, arm_b=0.4, el_b=0.6, heads=(0.0, 0.0, 0.05), hj=(0.3, 0.3, 0.4)),
]


def _storm(k):
    a = k / 4 * math.tau
    return B(bob=4 + 1.5 * math.sin(a), lean=0.12 + 0.05 * math.sin(a), hx=1.5 * math.cos(a), arm=0.7, el=0.85, ca=-1.4, arm_b=2.3 + 0.2 * math.sin(a),
             el_b=0.4, heads=(-0.45 + 0.15 * math.sin(a), 0.5 + 0.2 * math.cos(a), -0.2 + 0.25 * math.sin(a + 1.5)),
             hext=((-2 + 2 * math.cos(a), -3), (0, -3 + 1.5 * math.sin(a)), (2 * math.sin(a), -1)), hj=(1.0, 1.0, 1.0), glow=1, ph=a * 2,
             breath=math.sin(a), ht=-0.3)


BLIZZARD = [
    B(bob=3, lean=0.1, arm=0.7, el=0.85, ca=-1.4, arm_b=2.0, el_b=0.6, heads=(-0.4, 0.45, -0.3), hj=(0.7, 0.7, 0.8), glow=1, ht=-0.2),
    B(bob=2, lean=0.04, arm=0.7, el=0.85, ca=-1.42, arm_b=2.4, el_b=0.4, heads=(-0.5, 0.55, -0.4), hj=(1.0, 1.0, 1.0), glow=1, ht=-0.3, breath=1),
] + [_storm(k) for k in range(4)] + [
    B(bob=3, lean=0.28, arm=0.6, el=0.9, ca=-1.38, arm_b=0.5, el_b=0.6, heads=(0.0, 0.0, 0.05), hj=(0.3, 0.3, 0.4)),
]

LEAP = [
    B(bob=16, lean=0.5, arm=1.8, el=0.6, ca=1.3, arm_b=0.2, el_b=0.6, heads=(0.2, -0.1, 0.3), hj=(0.6, 0.6, 0.8), glow=1, ff=(22, 0), fb=(-22, 0)),
    B(bob=21, lean=0.58, arm=1.9, el=0.6, ca=1.35, arm_b=0.1, el_b=0.6, heads=(0.25, -0.1, 0.35), hj=(0.8, 0.8, 0.9), glow=1, ff=(22, 0), fb=(-22, 0),
      breath=1),
    B(bob=0, lean=0.12, arm=2.4, el=0.5, ca=1.45, arm_b=2.2, el_b=0.5, fist_b=-1, heads=(-0.3, 0.3, -0.2), hj=(1.0, 1.0, 1.0), glow=1, ff=(8, 0),
      fb=(-12, 0)),
    B(bob=-4, lean=-0.05, arm=2.5, el=0.7, ca=1.5, arm_b=2.5, el_b=0.6, fist_b=-1, heads=(-0.35, 0.35, -0.3), hj=(1.0, 1.0, 1.0), glow=1,
      ff=(16, -18), fb=(-12, -14)),
    B(bob=-2, lean=0.32, arm=1.6, el=0.3, ca=1.3, arm_b=1.6, el_b=0.4, fist_b=-1, heads=(0.1, -0.1, 0.2), hj=(1.0, 1.0, 1.0), glow=1, ff=(20, -4),
      fb=(-16, -2)),
    B(bob=22, lean=0.72, hx=4, arm=1.0, el=0.2, ca=1.35, arm_b=0.9, el_b=0.3, fist_b=-1, heads=(0.3, -0.2, 0.4), hj=(1.0, 1.0, 1.0), glow=1,
      ff=(26, 0), fb=(-24, 0), hext=((3, 3), (4, 4), (4, 4))),
    B(bob=19, lean=0.66, hx=3, arm=1.0, el=0.25, ca=1.38, arm_b=0.8, el_b=0.35, heads=(0.25, -0.15, 0.3), hj=(0.7, 0.7, 0.8), glow=1, ff=(26, 0),
      fb=(-24, 0)),
    B(bob=8, lean=0.45, arm=0.7, el=0.7, ca=-0.6, arm_b=0.4, el_b=0.5, heads=(0.1, 0.0, 0.1), hj=(0.3, 0.3, 0.5), ff=(21, 0), fb=(-19, 0)),
]

NOVA = [
    B(bob=12, lean=0.5, arm=1.2, el=1.2, ca=0.1, arm_b=1.0, el_b=1.3, fist_b=-1, heads=(0.3, -0.25, 0.4), hj=(1.0, 1.0, 1.0), glow=1, brow=1,
      ff=(21, 0), fb=(-21, 0), hext=((2, 3), (3, 4), (3, 4))),
    B(bob=15, lean=0.58, arm=1.25, el=1.25, ca=0.12, arm_b=1.05, el_b=1.35, fist_b=-1, heads=(0.35, -0.3, 0.45), hj=(1.0, 1.0, 1.0), glow=1,
      brow=1, ff=(22, 0), fb=(-22, 0), hext=((2, 4), (3, 5), (3, 5)), breath=1),
    B(bob=8, lean=0.15, arm=0.9, el=0.6, ca=-1.4, arm_b=2.2, el_b=0.4, fist_b=-1, heads=(-0.45, 0.5, -0.4), hj=(1.0, 1.0, 1.0), glow=1, brow=1,
      ff=(24, 0), fb=(-22, 0), ht=-0.35),
    B(bob=7, lean=0.18, arm=0.88, el=0.62, ca=-1.4, arm_b=2.1, el_b=0.45, fist_b=-1, heads=(-0.4, 0.45, -0.35), hj=(1.0, 1.0, 1.0), glow=1,
      brow=1, ff=(24, 0), fb=(-22, 0), ht=-0.3),
]

ROAR = [
    B(bob=8, lean=0.6, arm=0.6, el=0.9, ca=-1.2, arm_b=0.2, el_b=0.6, fist_b=-1, heads=(0.3, -0.25, 0.4), hj=(0.1, 0.1, 0.3), glow=0.8, ht=0.35,
      hy=2, ff=(18, 0), fb=(-18, 0)),
    B(bob=11, lean=0.72, arm=0.55, el=0.95, ca=-1.15, arm_b=0.1, el_b=0.9, fist_b=-1, heads=(0.4, -0.35, 0.5), hj=(0.15, 0.15, 0.3), glow=0.9,
      ht=0.45, hy=3, ff=(19, 0), fb=(-19, 0), breath=1),
    B(bob=2, lean=0.08, arm=1.4, el=0.4, ca=-1.3, arm_b=1.8, el_b=0.9, fist_b=-1, heads=(-0.3, 0.35, -0.25), hj=(0.8, 0.8, 0.8), glow=1, ht=-0.3,
      hy=-2, ff=(21, 0), fb=(-21, 0)),
    B(bob=0, lean=-0.1, arm=1.7, el=0.2, ca=-1.25, arm_b=2.5, el_b=1.0, fist_b=-1, heads=(-0.5, 0.55, -0.45), hj=(1.0, 1.0, 1.0), glow=1, ht=-0.5,
      hy=-3, ff=(23, 0), fb=(-23, 0), breath=1, hext=((-2, -3), (0, -3), (2, -2))),
    B(bob=1, lean=-0.07, arm=1.72, el=0.18, ca=-1.25, arm_b=2.55, el_b=1.05, fist_b=-1, heads=(-0.45, 0.6, -0.5), hj=(1.0, 1.0, 1.0), glow=1,
      ht=-0.46, hy=-2.5, ff=(23, 0), fb=(-23, 0), breath=0.6, hext=((-3, -3), (0, -4), (3, -2))),
    B(bob=0, lean=-0.1, arm=1.68, el=0.22, ca=-1.25, arm_b=2.48, el_b=0.95, fist_b=-1, heads=(-0.55, 0.5, -0.4), hj=(1.0, 1.0, 1.0), glow=1,
      ht=-0.52, hy=-3, ff=(23, 0), fb=(-23, 0), breath=1, hext=((-2, -4), (0, -3), (2, -3))),
    B(bob=3, lean=0.3, arm=0.6, el=0.9, ca=-1.38, arm_b=0.4, el_b=0.6, heads=(0.05, 0.0, 0.1), hj=(0.3, 0.3, 0.5), glow=0.9, ff=(17, 0)),
]

STAGGER = [
    B(bob=4, lean=-0.16, hx=-7, arm=0.95, el=0.5, ca=-0.6, arm_b=2.0, el_b=0.5, mouth=0.85, glow=0.3, ht=-0.45, hy=-2, ff=(12, 0), fb=(-19, 0),
      heads=(-0.4, 0.4, -0.3), hj=(0.8, 0.8, 0.9), arm_b_open=1.0),
    B(bob=6, lean=-0.06, hx=-11, arm=0.7, el=0.6, ca=-0.2, arm_b=1.5, el_b=0.6, mouth=0.7, glow=0.35, ht=-0.3, ff=(6, -9), fb=(-31, 0),
      heads=(-0.2, 0.3, -0.1), hj=(0.6, 0.6, 0.7), arm_b_open=1.0),
    B(bob=26, lean=0.36, hx=-6, arm=0.6, el=0.6, ca=-1.3, arm_b=0.5, el_b=0.2, mouth=0.5, glow=0.4, ht=0.42, hy=1, ff=(22, 0), fb=(-34, 0),
      heads=(0.45, -0.4, 0.5), hj=(0.4, 0.5, 0.5), arm_b_open=1.0),
    B(bob=27, lean=0.42, hx=-6, arm=0.6, el=0.6, ca=-1.3, arm_b=0.45, el_b=0.2, mouth=0.4, glow=0.35, ht=0.5, hy=2.5, ff=(22, 0), fb=(-34, 0),
      heads=(0.55, -0.5, 0.6), hj=(0.3, 0.4, 0.4), breath=1, arm_b_open=1.0),
    B(bob=26.5, lean=0.4, hx=-6, arm=0.6, el=0.6, ca=-1.3, arm_b=0.45, el_b=0.2, mouth=0.55, glow=0.4, ht=0.46, hy=2, ff=(22, 0), fb=(-34, 0),
      heads=(0.4, -0.55, 0.45), hj=(0.5, 0.3, 0.6), breath=-0.5, arm_b_open=1.0),
    B(bob=18, lean=0.52, hx=-3, arm=0.6, el=0.7, ca=-1.35, arm_b=0.9, el_b=0.6, mouth=0.65, glow=0.6, ht=0.2, ff=(22, 0), fb=(-28, 0),
      heads=(0.2, -0.2, 0.25), hj=(0.6, 0.6, 0.7)),
    B(bob=3, lean=0.3, arm=0.58, el=0.92, ca=-1.38, arm_b=0.3, el_b=0.6, fist_b=-1, glow=1.0, mouth=0.4, brow=1, ff=(16, 0), heads=(0.0, 0.0, 0.1),
      hj=(0.5, 0.5, 0.8)),
]

DEATH = [
    B(bob=4, lean=-0.2, hx=-6, arm=1.3, el=0.4, ca=-0.4, arm_b=2.3, el_b=0.4, mouth=1.0, glow=0.8, ht=-0.5, hy=-3, ff=(13, 0), fb=(-20, 0),
      heads=(-0.5, 0.55, -0.45), hj=(1.0, 1.0, 1.0), arm_b_open=1.0),
    B(bob=6, lean=-0.12, hx=-10, arm=1.0, el=0.5, ca=0.0, arm_b=1.9, el_b=0.5, mouth=0.9, glow=0.6, ht=-0.38, ff=(8, -7), fb=(-30, 0),
      heads=(-0.3, 0.4, -0.2), hj=(0.8, 0.8, 0.9), arm_b_open=1.0),
    B(bob=24, lean=0.22, hx=-7, arm=0.7, el=0.4, ca=0.4, arm_b=0.9, el_b=0.3, mouth=0.6, glow=0.5, ht=0.2, ff=(20, 0), fb=(-32, 0),
      heads=(0.3, -0.3, 0.4), hj=(0.6, 0.6, 0.6), arm_b_open=1.0),
    B(bob=34, lean=0.18, hx=-6, arm=0.5, el=0.2, ca=0.08, arm_b=0.25, el_b=0.15, mouth=0.5, glow=0.4, ht=0.5, hy=2, ff=(4, 0), fb=(-12, 0),
      heads=(0.5, -0.5, 0.6), hj=(0.5, 0.5, 0.5), arm_b_open=1.0),
    B(bob=35, lean=0.28, hx=-6, arm=0.45, el=0.2, ca=0.06, arm_b=0.2, el_b=0.15, mouth=0.35, glow=0.3, ht=0.65, hy=3, ff=(4, 0), fb=(-12, 0),
      heads=(0.6, -0.6, 0.7), hj=(0.4, 0.4, 0.4), arm_b_open=1.0, breath=1),
] + [B(bob=35, lean=0.5 + 0.04 * k, hx=-6, arm=0.6 + 0.3 * k, el=0.2, ca=-[0.3, 0.72, 0.98, 1.04][k] - 0.05, arm_b=0.8 + 0.25 * k, el_b=0.2, mouth=0.35, glow=max(0.0, 0.25 - 0.1 * k),
       ht=0.6 - 0.08 * k, ff=(4, 0), fb=(-12, 0), heads=(0.6, -0.6, 0.7), hj=(0.3, 0.3, 0.3), arm_b_open=1.0,
       rot=[0.3, 0.72, 0.98, 1.04][k], rp=(6.0, -4.0), dy=-5.0) for k in range(4)]


CLIPS = {
    'idle': clip([_idle(k / 8) for k in range(8)], 7, loop=True),
    'walk': clip([_walk(k / 8) for k in range(8)], 8, loop=True),
    'yb_club': clip(CLUB, 12, seg={'w': [0, 3], 's': [4, 6], 'r': [7, 8]}),
    'yb_gust': clip(GUST, 10, seg={'w': [0, 2], 'a': [3, 5, 3], 'r': [6, 6]}),
    'yb_heads': clip(HEADS, 10, seg={'w': [0, 1], 'b': [2, 3], 'c': [4, 5], 'f': [6, 7], 'r': [8, 8]}),
    'yb_breath': clip(BREATH, 10, seg={'w': [0, 2], 'a': [3, 5, 3], 'r': [6, 6]}),
    'yb_icicles': clip(ICICLES, 10, seg={'w': [0, 1], 's': [2, 3], 'r': [4, 4]}),
    'yb_blizzard': clip(BLIZZARD, 8, seg={'w': [0, 1], 'a': [2, 5, 2], 'r': [6, 6]}),
    'yb_leap': clip(LEAP, 10, seg={'w': [0, 1], 'a': [2, 4], 's': [5, 6], 'r': [7, 7]}),
    'yb_nova': clip(NOVA, 10, seg={'w': [0, 1], 's': [2, 3]}),
    'yb_roar': clip(ROAR, 9, seg={'a': [0, 6]}),
    'yb_stagger': clip(STAGGER, 8, seg={'a': [0, 6]}),
    'yb_death': clip(DEATH, 8, seg={'a': [0, 8]}),
}
