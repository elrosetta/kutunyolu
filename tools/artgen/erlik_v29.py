"""Erlik Han v29: hamle başına tam gövde animasyonları (erlik_ink.draw pozlarıyla).

Tamu hükümdarının dili: ağır, ağırbaşlı yürüyüş (pelerin geride dalgalanır, alev halesi rüzgârla yatar), dinlenmede
topuz eli gevşek, öbür eli pençe gibi açılıp kapanır. Zincir atışında gövde yay gibi burulur, çekişte geriye yaslanıp
çeker, ardından topuzu aşağıdan yukarı savurur. Ateş dalgasında topuz iki elle baş üstünden yere iner. Tamu kapısında
pelerinine sarınıp yere batar, öbür yanda pelerini açarak alevle yükselir. "!!" Tamu Seli'nde boyu uzar, kollar göğe
açılır, hale ve pelerin kabarır.

Evre bölümleri: w hazırlık, s temas, r toparlanma, a eylem / döngü, p çekiş, u / U yukarı savuruş hazırlık / teması,
m geri sarma, W / S ikinci savuruş, k batış, h gizli, e yükseliş, L / K Tamu Seli döngüleri, V ikinci "!!" hazırlık.
"""
import math

import bosskit as bk
import erlik_ink as er
from erlik_ink import _base as B

over = bk.over


def _geo(p):
    lean = p['lean']
    up = (math.sin(lean), -math.cos(lean))
    fw = (math.cos(lean), math.sin(lean))
    hip = (p['hx'], -er.HIP_H + p['bob'])
    T = lambda u, f: bk.add(bk.add(hip, up, u), fw, f)
    _, hf = bk.arm_fk(T(55.0, -4.0), p['arm'], p['el'], er.L_UP, er.L_FO)
    _, hb = bk.arm_fk(T(59.0, 12.0), p['arm_b'], p['el_b'], er.L_UP, er.L_FO)
    return hf, hb


def fit(p, top=-176.0, ground=-14.0, left=-80.0, right=144.0):
    if p.get('rot') or p.get('dy', 0.0) > 0:
        return p
    while _geo(p)[0][1] < -162.0 and p['el'] < 2.6:
        p = over(p, el=p['el'] + 0.04)
    lim = -150.0 if p.get('orb', 0.0) > 0.05 else -166.0
    while _geo(p)[1][1] < lim and p['el_b'] < 2.6:
        p = over(p, el_b=p['el_b'] + 0.04)
    h = _geo(p)[0]

    def ok(a):
        x, y = h[0] + math.cos(a) * er.MACE_L, h[1] + math.sin(a) * er.MACE_L
        return top <= y <= ground and left <= x <= right
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
    cl = 0.5 + 0.5 * math.sin(t * math.tau * 2 + 0.5)        # uzak el pençe gibi açılıp kapanır
    return B(bob=1.2 * s, lean=0.08 + 0.015 * s, arm=0.32 + 0.02 * s, el=0.5, arm_b=0.22 - 0.04 * s, el_b=0.65 + 0.1 * c, ca=1.05 + 0.02 * s,
             glow=0.6 + 0.3 * (0.5 + 0.5 * math.sin(t * math.tau * 2)), hy=0.6 * s, ph=t * math.tau, fl=t * math.tau * 2, cape=0.15 * s + 0.1,
             open_b=0.3 + 0.6 * cl, brow=0.4 + 0.2 * s, ht=0.03 * c, hx=0.8 * c)


def _walk(t):
    ph = t * math.tau
    s = math.sin(ph)
    S = 15.5

    def foot(q):
        q %= 1.0
        if q < 0.58:
            return (S - 2 * S * q / 0.58, 0.0)
        u = (q - 0.58) / 0.42
        return (-S + 2 * S * (u * u * (3 - 2 * u)), -math.sin(math.pi * u) * 9.0)
    ff, fb = foot(t), foot(t + 0.5)
    w = math.cos(4 * math.pi * (t - 0.07))
    return B(bob=1.4 + 2.2 * w, lean=0.12 + 0.02 * w, ff=(ff[0] + 5, ff[1]), fb=(fb[0] - 6, fb[1]), arm=0.4 - 0.14 * s, el=0.5,
             arm_b=0.2 + 0.22 * s, el_b=0.6, ca=1.0 - 0.07 * s, glow=0.75, hy=0.8 * max(0.0, math.cos(4 * math.pi * (t - 0.15))), ph=ph,
             fl=ph * 2, cape=0.55 + 0.2 * math.sin(ph * 2 - 1.0), hx=1.2 * s, wind=0.65, open_b=0.5, brow=0.5)


CHAIN = [
    B(bob=3, lean=-0.02, hx=-2, arm=0.3, el=0.6, ca=1.15, arm_b=-0.6, el_b=1.2, open_b=0.0, mouth=0.3, brow=0.8, glow=0.9, cape=0.4, fl=1.0,
      ff=(17, 0), fb=(-17, 0)),
    B(bob=5, lean=-0.1, hx=-4, arm=0.25, el=0.7, ca=1.2, arm_b=-0.9, el_b=1.4, open_b=0.0, mouth=0.5, brow=1, glow=1, cape=0.6, fl=2.0,
      ff=(20, 0), fb=(-20, 0), ht=-0.05),
    B(bob=5, lean=-0.12, hx=-5, arm=0.2, el=0.7, ca=1.25, arm_b=-1.0, el_b=1.5, open_b=0.0, mouth=0.6, brow=1, glow=1, cape=0.7, fl=3.0,
      ff=(21, 0), fb=(-21, 0), ht=-0.08),
    # 3-4: atış — uzak kol sonuna dek ileri, avuç açık
    B(bob=5, lean=0.32, hx=4, arm=0.2, el=0.5, ca=1.4, arm_b=1.6, el_b=0.05, open_b=1.0, mouth=0.9, brow=1, glow=1, cape=0.9, wind=0.8,
      fl=4.0, ff=(26, 0), fb=(-16, 0), ht=0.1),
    B(bob=6, lean=0.36, hx=5, arm=0.18, el=0.5, ca=1.45, arm_b=1.52, el_b=0.1, open_b=1.0, mouth=0.8, brow=1, glow=1, cape=0.8, wind=0.7,
      fl=5.0, ff=(26, 0), fb=(-16, 0), ht=0.12),
    # 5-6: çekiş — geriye yaslanıp yumrukla çeker
    B(bob=7, lean=-0.18, hx=-6, arm=0.4, el=0.6, ca=1.1, arm_b=0.6, el_b=1.6, open_b=0.0, mouth=1.0, brow=1, glow=1, cape=0.5, fl=6.0,
      ff=(24, 0), fb=(-22, 0), ht=-0.1),
    B(bob=8, lean=-0.24, hx=-8, arm=0.45, el=0.6, ca=1.05, arm_b=0.2, el_b=1.9, open_b=0.0, mouth=1.0, brow=1, glow=1, cape=0.45, fl=7.0,
      ff=(25, 0), fb=(-23, 0), ht=-0.14),
    # 7: yukarı savuruş hazırlığı (topuz alçakta, arkada)
    B(bob=12, lean=0.35, hx=-2, arm=-0.6, el=0.3, ca=2.3, cz=-6, arm_b=0.5, el_b=0.8, open_b=0.0, mouth=0.8, brow=1, glow=1, cape=0.6, fl=8.0,
      ff=(24, 0), fb=(-20, 0)),
    # 8-9: yukarı savuruş teması ve aşma
    B(bob=4, lean=-0.06, hx=4, arm=2.4, el=0.15, ca=-1.4, arm_b=-0.3, el_b=0.6, open_b=0.0, mouth=1.0, brow=1, glow=1, cape=1.0, wind=1.0,
      fl=9.0, ff=(27, 0), fb=(-17, -2), ht=-0.2),
    B(bob=3, lean=-0.1, hx=3, arm=2.6, el=0.5, ca=-2.0, cz=-6, arm_b=-0.2, el_b=0.7, open_b=0.0, mouth=0.8, brow=1, glow=1, cape=0.9,
      wind=0.8, fl=10.0, ff=(27, 0), fb=(-18, 0), ht=-0.22),
    # 10: ıskaladı — zinciri geri sarar
    B(bob=4, lean=0.12, hx=1, arm=0.3, el=0.5, ca=1.15, arm_b=0.9, el_b=1.3, open_b=0.3, mouth=0.4, brow=0.8, glow=0.9, cape=0.5, fl=11.0,
      ff=(22, 0), fb=(-18, 0)),
    B(bob=2, lean=0.1, arm=0.33, el=0.5, ca=1.05, arm_b=0.3, el_b=0.7, open_b=0.5, mouth=0.2, brow=0.6, glow=0.8, cape=0.3, fl=12.0, ff=(16, 0)),
]

FIREWAVE = [
    B(bob=3, lean=0.12, hx=-2, arm=1.0, el=1.0, ca=-0.6, arm_b=0.9, el_b=1.2, open_b=0.0, mouth=0.3, brow=0.6, glow=0.9, cape=0.4, fl=1.0,
      fb=(-16, 0)),
    B(bob=4, lean=0.0, hx=-4, arm=2.1, el=1.3, ca=-2.2, cz=-6, arm_b=1.8, el_b=1.1, open_b=0.0, mouth=0.6, brow=1, glow=1, cape=0.6, fl=2.0,
      ht=-0.15, fb=(-20, 0), ff=(15, 0)),
    B(bob=6, lean=-0.12, hx=-6, arm=2.4, el=1.6, ca=-3.0, cz=-8, arm_b=2.3, el_b=1.4, open_b=0.0, mouth=1.0, brow=1, glow=1, cape=0.8, fl=3.0,
      ht=-0.3, ff=(17, -4), fb=(-21, 0), wind=0.6),
    B(bob=1, lean=0.2, hx=2, arm=2.4, el=0.4, ca=-1.65, arm_b=1.8, el_b=0.5, open_b=0.0, mouth=1.0, brow=1, glow=1, cape=0.9, fl=4.0, ht=-0.05,
      ff=(25, 0), fb=(-19, 0), wind=0.8),
    B(bob=15, lean=0.66, hx=6, arm=1.25, el=0.08, ca=1.3, arm_b=1.1, el_b=0.15, open_b=0.0, mouth=1.0, brow=1, glow=1, cape=1.0, wind=1.0,
      fl=5.0, ht=0.25, ff=(29, 0), fb=(-22, 0)),
    B(bob=12, lean=0.6, hx=5, arm=1.12, el=0.14, ca=1.35, arm_b=1.0, el_b=0.2, open_b=0.0, mouth=0.8, brow=1, glow=1, cape=0.8, wind=0.7,
      fl=6.0, ht=0.2, ff=(29, 0), fb=(-22, 0)),
    B(bob=11, lean=0.55, hx=4, arm=1.05, el=0.25, ca=1.38, arm_b=0.9, el_b=0.3, open_b=0.0, mouth=0.6, brow=0.9, glow=1, cape=0.6, fl=7.0,
      ht=0.16, ff=(29, 0), fb=(-22, 0)),
    B(bob=4, lean=0.2, hx=1, arm=0.45, el=0.5, ca=1.1, arm_b=0.4, el_b=0.6, open_b=0.4, mouth=0.3, brow=0.6, glow=0.8, cape=0.3, fl=8.0,
      ff=(18, 0)),
]

FIREBALLS = [
    B(bob=3, lean=0.05, arm=0.35, el=0.5, ca=1.0, arm_b=1.8, el_b=1.0, open_b=1.0, orb=0.4, mouth=0.4, brow=0.8, glow=1, cape=0.4, fl=1.0,
      ht=-0.1, ff=(18, 0), fb=(-16, 0)),
    B(bob=4, lean=-0.05, hx=-2, arm=0.4, el=0.55, ca=0.95, arm_b=2.5, el_b=1.5, open_b=1.0, orb=0.8, mouth=0.6, brow=1, glow=1, cape=0.6, fl=2.0,
      ht=-0.15, ff=(19, 0), fb=(-18, 0)),
    B(bob=5, lean=-0.1, hx=-3, arm=0.45, el=0.55, ca=0.95, arm_b=2.6, el_b=1.6, open_b=1.0, orb=1.0, mouth=0.8, brow=1, glow=1, cape=0.7, fl=3.0,
      ht=-0.2, ff=(20, 0), fb=(-19, 0), wind=0.4),
    B(bob=4, lean=0.32, hx=4, arm=0.3, el=0.45, ca=1.0, arm_b=1.65, el_b=0.05, open_b=1.0, orb=0.35, mouth=1.0, brow=1, glow=1, cape=0.8,
      wind=0.9, fl=4.0, ht=0.1, ff=(24, 0), fb=(-15, 0)),
    B(bob=5, lean=0.36, hx=5, arm=0.28, el=0.45, ca=1.05, arm_b=1.4, el_b=0.15, open_b=1.0, mouth=0.8, brow=1, glow=1, cape=0.7, wind=0.7,
      fl=5.0, ht=0.12, ff=(24, 0), fb=(-15, 0)),
    B(bob=2, lean=0.14, arm=0.33, el=0.5, ca=1.05, arm_b=0.6, el_b=0.7, open_b=0.7, mouth=0.3, brow=0.6, glow=0.85, cape=0.4, fl=6.0, ff=(17, 0)),
]

SCYTHE = [
    B(bob=3, lean=0.1, hx=-2, arm=0.2, el=0.8, ca=-0.3, arm_b=0.6, el_b=0.6, mouth=0.3, brow=0.6, glow=0.9, cape=0.3, fl=1.0, fb=(-16, 0)),
    B(bob=5, lean=0.02, hx=-4, arm=-0.5, el=1.3, ca=-2.4, cz=-6, arm_b=1.0, el_b=0.5, mouth=0.5, brow=1, glow=1, cape=0.5, fl=2.0, ff=(18, 0),
      fb=(-18, 0), open_b=1.0),
    B(bob=7, lean=-0.04, hx=-5, arm=-0.95, el=1.6, ca=-2.85, cz=-8, arm_b=1.35, el_b=0.3, mouth=0.8, brow=1, glow=1, cape=0.7, fl=3.0,
      ff=(21, 0), fb=(-19, 0), open_b=1.0),
    # 3-4: önden savuruş (göğüs hizasında yatay)
    B(bob=5, lean=0.32, hx=4, arm=1.2, el=0.3, ca=0.35, cz=22, arm_b=-0.25, el_b=0.8, mouth=1.0, brow=1, glow=1, cape=1.0, wind=1.0, fl=4.0,
      ff=(26, 0), fb=(-15, 0)),
    B(bob=8, lean=0.45, hx=6, arm=0.9, el=0.15, ca=1.0, cz=22, arm_b=-0.35, el_b=0.7, mouth=0.85, brow=1, glow=1, cape=0.8, wind=0.8, fl=5.0,
      ff=(27, 0), fb=(-14, 0)),
    # 5-6: ters savuruş hazırlığı (topuz gövdenin önünden çaprazlanır, omuz burulur)
    B(bob=6, lean=0.3, hx=3, arm=0.6, el=1.9, ca=2.9, cz=22, arm_b=-0.1, el_b=0.9, mouth=0.7, brow=1, glow=1, cape=0.6, fl=6.0, ff=(26, 0),
      fb=(-16, 0)),
    B(bob=7, lean=0.26, hx=2, arm=0.8, el=2.1, ca=-2.9, cz=22, arm_b=0.0, el_b=1.0, mouth=0.8, brow=1, glow=1, cape=0.7, fl=7.0, ff=(26, 0),
      fb=(-17, 0)),
    # 7-8: ters savuruş teması
    B(bob=6, lean=0.42, hx=6, arm=1.6, el=0.1, ca=-0.1, cz=-6, arm_b=0.6, el_b=0.5, mouth=1.0, brow=1, glow=1, cape=1.0, wind=1.0, fl=8.0,
      ff=(28, 0), fb=(-14, -2)),
    B(bob=7, lean=0.36, hx=5, arm=1.9, el=0.4, ca=-0.9, cz=-6, arm_b=0.5, el_b=0.6, mouth=0.8, brow=1, glow=1, cape=0.8, wind=0.7, fl=9.0,
      ff=(28, 0), fb=(-15, 0)),
    B(bob=3, lean=0.14, hx=1, arm=0.5, el=0.5, ca=0.9, arm_b=0.3, el_b=0.6, mouth=0.3, brow=0.6, glow=0.85, cape=0.4, fl=10.0, ff=(19, 0)),
]

PILLARS = [
    B(bob=3, lean=0.05, arm=0.35, el=0.5, ca=1.0, arm_b=2.0, el_b=0.7, open_b=1.0, mouth=0.4, brow=1, glow=1, cape=0.4, fl=1.0, ht=-0.1),
    B(bob=2, lean=-0.02, arm=0.35, el=0.5, ca=1.0, arm_b=2.4, el_b=0.6, open_b=1.0, mouth=0.6, brow=1, glow=1, cape=0.5, fl=2.0, ht=-0.15),
    B(bob=7, lean=0.3, hx=2, arm=0.35, el=0.5, ca=1.05, arm_b=1.1, el_b=0.15, open_b=0.0, mouth=0.9, brow=1, glow=1, cape=0.7, wind=0.6, fl=3.0,
      ht=0.15, ff=(22, 0)),
    B(bob=3, lean=0.1, arm=0.35, el=0.5, ca=1.0, arm_b=2.2, el_b=0.6, open_b=1.0, mouth=0.6, brow=1, glow=1, cape=0.5, fl=4.0, ht=-0.1),
    B(bob=2, lean=0.12, arm=0.33, el=0.5, ca=1.05, arm_b=0.4, el_b=0.7, open_b=0.6, mouth=0.3, brow=0.6, glow=0.85, cape=0.3, fl=5.0),
]

GATE = [
    B(bob=4, lean=0.05, arm=0.6, el=1.6, ca=2.4, cz=-6, arm_b=1.0, el_b=1.9, open_b=0.0, mouth=0.4, brow=1, glow=1, cape=-0.5, fl=1.0,
      ff=(12, 0), fb=(-12, 0)),
    B(bob=7, lean=0.1, arm=0.7, el=1.8, ca=2.5, cz=-6, arm_b=1.1, el_b=2.0, open_b=0.0, mouth=0.5, brow=1, glow=1, cape=-0.7, fl=2.0,
      ff=(10, 0), fb=(-10, 0)),
    # 2-4: batış (pelerinine sarınır, yere gömülür)
    B(bob=14, lean=0.2, arm=0.7, el=1.9, ca=2.5, cz=-6, arm_b=1.1, el_b=2.0, open_b=0.0, mouth=0.3, brow=1, glow=1.0, cape=-0.8, fl=3.0,
      ff=(10, 0), fb=(-10, 0), dy=16.0),
    B(bob=18, lean=0.25, arm=0.7, el=1.9, ca=2.5, cz=-6, arm_b=1.1, el_b=2.0, open_b=0.0, mouth=0.2, brow=1, glow=1.0, cape=-0.8, fl=4.0,
      ff=(10, 0), fb=(-10, 0), dy=48.0),
    B(bob=18, lean=0.25, arm=0.7, el=1.9, ca=2.5, cz=-6, arm_b=1.1, el_b=2.0, open_b=0.0, mouth=0.2, brow=1, glow=1.0, cape=-0.8, fl=5.0,
      ff=(10, 0), fb=(-10, 0), dy=90.0),
    # 5-7: yükseliş (pelerin açılır, kollar yana, alevle fırlar)
    B(bob=6, lean=-0.1, arm=1.7, el=0.3, ca=-0.6, arm_b=2.3, el_b=0.3, open_b=1.0, mouth=1.0, brow=1, glow=1, cape=1.0, wind=1.0, fl=6.0,
      ht=-0.3, ff=(16, 0), fb=(-16, 0), dy=18.0),
    B(bob=1, lean=-0.12, arm=1.9, el=0.2, ca=-0.9, arm_b=2.5, el_b=0.25, open_b=1.0, mouth=1.0, brow=1, glow=1, cape=1.0, wind=1.0, fl=7.0,
      ht=-0.35, ff=(18, 0), fb=(-18, 0)),
    B(bob=3, lean=0.05, arm=1.2, el=0.35, ca=0.2, arm_b=1.7, el_b=0.4, open_b=1.0, mouth=0.8, brow=1, glow=1, cape=0.8, wind=0.7, fl=8.0,
      ht=-0.1, ff=(19, 0), fb=(-18, 0)),
    B(bob=2, lean=0.1, arm=0.4, el=0.5, ca=1.05, arm_b=0.4, el_b=0.7, open_b=0.6, mouth=0.4, brow=0.8, glow=0.9, cape=0.4, fl=9.0, ff=(17, 0)),
]

SOULS = [
    B(bob=3, lean=0.0, arm=1.4, el=0.4, ca=0.2, arm_b=1.9, el_b=0.6, open_b=1.0, mouth=0.4, brow=1, glow=1, cape=0.5, fl=1.0, ht=-0.2),
    B(bob=2, lean=-0.08, arm=1.8, el=0.3, ca=-0.5, arm_b=2.4, el_b=0.4, open_b=1.0, mouth=0.7, brow=1, glow=1, cape=0.7, fl=2.0, ht=-0.35, hy=-1),
] + [B(bob=4 + 0.8 * math.sin(k * 2.1), lean=-0.1 + 0.03 * math.sin(k * 2.1), arm=1.9 + 0.15 * math.sin(k * 2.1), el=0.25, ca=-0.6,
       arm_b=2.5 - 0.15 * math.sin(k * 2.1), el_b=0.35, open_b=1.0, mouth=1.0, brow=1, glow=1, cape=0.8 + 0.1 * k, wind=0.6, fl=3.0 + k * 1.3,
       ht=-0.42, hy=-1.5) for k in range(3)]

WALLS = [
    B(bob=4, lean=0.1, arm=0.7, el=1.7, ca=2.4, cz=-6, arm_b=1.0, el_b=1.8, open_b=1.0, mouth=0.5, brow=1, glow=1, cape=0.3, fl=1.0),
    B(bob=6, lean=0.18, arm=0.6, el=1.9, ca=2.6, cz=-6, arm_b=0.9, el_b=2.0, open_b=1.0, mouth=0.7, brow=1, glow=1, cape=0.2, fl=2.0, ht=0.1),
    B(bob=4, lean=0.0, arm=-0.9, el=0.2, ca=1.6, arm_b=2.0, el_b=0.15, open_b=1.0, mouth=1.0, brow=1, glow=1, cape=1.0, wind=1.0, fl=3.0,
      ht=-0.2, ff=(20, 0), fb=(-20, 0)),
    B(bob=4, lean=-0.02, arm=-0.85, el=0.25, ca=1.6, arm_b=1.95, el_b=0.2, open_b=1.0, mouth=0.8, brow=1, glow=1, cape=0.9, wind=0.8, fl=4.0,
      ht=-0.18, ff=(20, 0), fb=(-20, 0)),
    B(bob=2, lean=0.1, arm=0.4, el=0.5, ca=1.05, arm_b=0.4, el_b=0.7, open_b=0.6, mouth=0.3, brow=0.7, glow=0.9, cape=0.4, fl=5.0, ff=(17, 0)),
]

SELI = [
    # 0-2: "!!" — boyu uzar, kollar göğe açılır, hale ve pelerin kabarır
    B(bob=3, lean=0.0, arm=1.0, el=0.8, ca=0.6, arm_b=1.4, el_b=0.8, open_b=1.0, mouth=0.5, brow=1, glow=1, cape=0.6, wind=0.6, fl=1.0, ht=-0.1),
    B(bob=0, lean=-0.08, arm=2.0, el=0.3, ca=-0.6, arm_b=2.3, el_b=0.3, open_b=1.0, mouth=0.8, brow=1, glow=1, cape=0.9, wind=1.0, fl=2.0,
      ht=-0.3, hy=-1, ff=(18, 0), fb=(-18, 0)),
    B(bob=4, lean=-0.1, arm=2.2, el=0.25, ca=-0.8, arm_b=2.55, el_b=0.25, open_b=1.0, mouth=1.0, brow=1, glow=1, cape=1.0, wind=1.0, fl=3.0,
      ht=-0.42, hy=-2, ff=(19, 0), fb=(-19, 0)),
] + [B(bob=2 + 0.8 * math.sin(k * 1.6), lean=-0.06 + 0.04 * math.sin(k * 1.6), arm=1.6 + 0.3 * math.sin(k * 1.6), el=0.3, ca=0.0,
       arm_b=[2.4, 1.6, 2.0, 1.4][k], el_b=[0.5, 0.05, 0.4, 0.1][k], open_b=1.0, orb=[0.6, 0.2, 0.8, 0.3][k], mouth=1.0, brow=1, glow=1,
       cape=1.0, wind=1.0, fl=4.0 + k * 1.5, ht=-0.25, ff=(19, 0), fb=(-19, 0)) for k in range(4)] + [
    # 7-8: ikinci "!!" (kor yağmuru): avuçlar göğe, gövde geriye yaslanır
    B(bob=2, lean=-0.14, arm=2.3, el=0.6, ca=-0.4, arm_b=2.5, el_b=0.6, open_b=1.0, mouth=0.9, brow=1, glow=1, cape=0.8, wind=0.6, fl=10.0,
      ht=-0.5, hy=-2, ff=(18, 0), fb=(-18, 0)),
    B(bob=5, lean=-0.18, arm=2.4, el=0.5, ca=-0.5, arm_b=2.6, el_b=0.5, open_b=1.0, mouth=1.0, brow=1, glow=1, cape=0.9, wind=0.8, fl=11.0,
      ht=-0.55, hy=-2.5, ff=(18, 0), fb=(-18, 0)),
] + [B(bob=4 + 1.2 * math.sin(k * 2.0), lean=0.1 + 0.05 * math.sin(k * 2.0), arm=1.4 - 0.4 * (k % 2), el=0.4, ca=0.6, arm_b=[1.2, 2.2, 1.5][k],
       el_b=[0.3, 0.8, 0.4][k], open_b=[0.0, 1.0, 0.0][k], mouth=0.9, brow=1, glow=1, cape=0.8, wind=0.7, fl=12.0 + k * 1.4, ht=0.05,
       ff=(20, 0), fb=(-18, 0)) for k in range(3)] + [
    B(bob=2, lean=0.1, arm=0.4, el=0.5, ca=1.05, arm_b=0.4, el_b=0.7, open_b=0.6, mouth=0.3, brow=0.8, glow=0.9, cape=0.4, fl=16.0, ff=(17, 0)),
]

NOVA = [
    B(bob=10, lean=0.4, arm=0.9, el=1.9, ca=2.5, cz=-6, arm_b=1.0, el_b=2.0, open_b=0.0, mouth=0.8, brow=1, glow=1, cape=-0.4, fl=1.0, ht=0.2,
      ff=(19, 0), fb=(-19, 0)),
    B(bob=13, lean=0.5, arm=0.95, el=2.0, ca=2.6, cz=-6, arm_b=1.05, el_b=2.1, open_b=0.0, mouth=1.0, brow=1, glow=1, cape=-0.5, fl=2.0, ht=0.25,
      ff=(20, 0), fb=(-20, 0)),
    B(bob=4, lean=-0.06, arm=-0.9, el=0.2, ca=1.7, arm_b=2.0, el_b=0.15, open_b=1.0, mouth=1.0, brow=1, glow=1, cape=1.0, wind=1.0, fl=3.0,
      ht=-0.3, ff=(22, 0), fb=(-22, 0)),
    B(bob=4, lean=-0.04, arm=-0.85, el=0.25, ca=1.7, arm_b=1.95, el_b=0.2, open_b=1.0, mouth=0.8, brow=1, glow=1, cape=0.9, wind=0.8, fl=4.0,
      ht=-0.25, ff=(22, 0), fb=(-22, 0)),
]

ROAR = [
    B(bob=7, lean=0.35, arm=0.5, el=0.6, ca=0.9, arm_b=0.9, el_b=1.1, mouth=0.4, glow=0.9, brow=1, ff=(18, 0), fb=(-18, 0), ht=0.2, fl=1.0,
      cape=0.5, open_b=0.0),
    B(bob=9, lean=0.45, arm=0.4, el=0.7, ca=1.0, arm_b=0.8, el_b=1.3, mouth=0.3, glow=0.9, brow=1, ff=(19, 0), fb=(-19, 0), ht=0.3, fl=2.0,
      cape=0.4, open_b=0.0),
    B(bob=2, lean=0.05, hx=-2, arm=1.2, el=0.35, ca=0.0, arm_b=1.9, el_b=0.8, mouth=0.9, glow=1, brow=1, ff=(20, 0), fb=(-20, 0), ht=-0.22,
      hy=-1, fl=3.0, cape=0.9, orb=0.5, open_b=1.0, wind=0.8),
    B(bob=0, lean=-0.08, hx=-3, arm=1.6, el=0.25, ca=-0.6, arm_b=2.3, el_b=0.9, mouth=1.0, glow=1, brow=1, ff=(21, 0), fb=(-21, 0), ht=-0.35,
      hy=-1.5, fl=4.0, cape=1.0, orb=1.0, open_b=1.0, wind=1.0),
    B(bob=0, lean=-0.07, hx=-3, arm=1.62, el=0.22, ca=-0.65, arm_b=2.32, el_b=0.92, mouth=1.0, glow=1, brow=1, ff=(21, 0), fb=(-21, 0),
      ht=-0.37, hy=-1.4, fl=5.3, cape=1.0, orb=1.0, open_b=1.0, wind=1.0),
    B(bob=0, lean=-0.08, hx=-3, arm=1.58, el=0.26, ca=-0.58, arm_b=2.28, el_b=0.88, mouth=1.0, glow=1, brow=1, ff=(21, 0), fb=(-21, 0),
      ht=-0.33, hy=-1.6, fl=6.6, cape=1.0, orb=0.9, open_b=1.0, wind=1.0),
    B(bob=3, lean=0.12, arm=0.5, el=0.5, ca=1.0, arm_b=0.5, el_b=0.8, mouth=0.4, glow=0.95, brow=1, ff=(17, 0), fl=8.0, cape=0.5, open_b=0.6),
]

STAGGER = [
    B(bob=3, lean=-0.14, hx=-6, arm=0.7, el=0.5, ca=0.3, arm_b=1.95, el_b=1.6, mouth=0.8, glow=0.4, ht=-0.32, hy=-1.0, ff=(11, 0), fb=(-17, 0),
      brow=-0.2, fl=1.0, cape=-0.4, open_b=1.0),
    B(bob=6, lean=-0.05, hx=-10, arm=0.55, el=0.5, ca=0.7, arm_b=1.4, el_b=1.0, mouth=0.6, glow=0.4, ht=-0.2, ff=(5, -8), fb=(-28, 0),
      fl=2.0, cape=-0.2, open_b=1.0),
    B(bob=24, lean=0.32, hx=-6, arm=0.4, el=0.3, ca=1.35, arm_b=0.5, el_b=0.2, mouth=0.5, glow=0.4, ht=0.38, hy=1, ff=(21, 0), fb=(-32, 0),
      fl=3.0, cape=0.2, open_b=1.0),
    B(bob=25, lean=0.38, hx=-6, arm=0.38, el=0.3, ca=1.38, arm_b=0.45, el_b=0.2, mouth=0.4, glow=0.35, ht=0.46, hy=2, ff=(21, 0), fb=(-32, 0),
      fl=4.0, cape=0.15, open_b=1.0),
    B(bob=24.5, lean=0.36, hx=-6, arm=0.38, el=0.3, ca=1.38, arm_b=0.45, el_b=0.2, mouth=0.5, glow=0.4, ht=0.42, hy=1.5, ff=(21, 0), fb=(-32, 0),
      fl=5.0, cape=0.2, open_b=1.0),
    B(bob=14, lean=0.4, hx=-3, arm=0.55, el=0.3, ca=1.25, arm_b=0.9, el_b=0.6, mouth=0.65, glow=0.6, ht=0.15, ff=(21, 0), fb=(-26, 0),
      fl=6.0, cape=0.3, open_b=0.3),
    B(bob=3, lean=0.12, arm=0.4, el=0.5, ca=1.0, arm_b=0.4, el_b=0.8, mouth=0.5, glow=1.0, brow=1, ff=(17, 0), fl=7.0, cape=0.4, open_b=0.0),
]

DEATH = [
    B(bob=4, lean=-0.2, hx=-6, arm=1.4, el=0.3, ca=-0.3, arm_b=2.3, el_b=0.4, mouth=1.0, glow=0.8, ht=-0.45, hy=-2, ff=(13, 0), fb=(-19, 0),
      fl=1.0, cape=0.8, wind=0.6, open_b=1.0, brow=-0.3),
    B(bob=6, lean=-0.12, hx=-10, arm=1.0, el=0.4, ca=0.3, arm_b=1.9, el_b=0.5, mouth=0.9, glow=0.6, ht=-0.35, ff=(8, -7), fb=(-29, 0),
      fl=2.0, cape=0.6, open_b=1.0),
    B(bob=22, lean=0.22, hx=-7, arm=0.6, el=0.3, ca=1.2, arm_b=0.9, el_b=0.3, mouth=0.6, glow=0.5, ht=0.2, ff=(20, 0), fb=(-31, 0),
      fl=3.0, cape=0.3, open_b=1.0),
    B(bob=32, lean=0.18, hx=-6, arm=0.3, el=0.2, ca=0.1, arm_b=0.25, el_b=0.15, mouth=0.5, glow=0.4, ht=0.5, hy=2, ff=(4, 0), fb=(-12, 0),
      fl=4.0, cape=0.1, open_b=1.0),
    B(bob=33, lean=0.28, hx=-6, arm=0.25, el=0.2, ca=0.08, arm_b=0.2, el_b=0.15, mouth=0.35, glow=0.3, ht=0.62, hy=3, ff=(4, 0), fb=(-12, 0),
      fl=5.0, cape=0.0, open_b=1.0),
] + [B(bob=33, lean=0.5 + 0.04 * k, hx=-6, arm=0.6 + 0.3 * k, el=0.2, ca=-[0.3, 0.72, 0.98, 1.04][k] + 0.05, arm_b=0.8 + 0.25 * k, el_b=0.2,
       mouth=0.3, glow=max(0.0, 0.25 - 0.1 * k), ht=0.55 - 0.06 * k, ff=(4, 0), fb=(-12, 0), fl=6.0 + k, cape=-0.2, open_b=1.0,
       rot=[0.3, 0.72, 0.98, 1.04][k], rp=(6.0, -4.0), dy=-5.0) for k in range(4)]


CLIPS = {
    'idle': clip([_idle(k / 8) for k in range(8)], 7, loop=True),
    'walk': clip([_walk(k / 8) for k in range(8)], 8, loop=True),
    'er_chain': clip(CHAIN, 10, seg={'w': [0, 2], 's': [3, 4], 'p': [5, 6, 5], 'u': [7, 7], 'U': [8, 9], 'm': [10, 11]}),
    'er_wave': clip(FIREWAVE, 12, seg={'w': [0, 3], 's': [4, 6], 'r': [7, 7]}),
    'er_fireballs': clip(FIREBALLS, 10, seg={'w': [0, 2], 's': [3, 4], 'r': [5, 5]}),
    'er_scythe': clip(SCYTHE, 12, seg={'w': [0, 2], 's': [3, 4], 'W': [5, 6], 'S': [7, 8], 'r': [9, 9]}),
    'er_pillars': clip(PILLARS, 10, seg={'w': [0, 1], 'a': [2, 3], 'r': [4, 4]}),
    'er_gate': clip(GATE, 10, seg={'w': [0, 1], 'k': [2, 4], 'h': [4, 4], 'e': [5, 7], 'r': [8, 8]}),
    'er_souls': clip(SOULS, 9, seg={'w': [0, 1], 'a': [2, 4, 2]}),
    'er_walls': clip(WALLS, 10, seg={'w': [0, 1], 's': [2, 3], 'r': [4, 4]}),
    'er_seli': clip(SELI, 8, seg={'w': [0, 2], 'L': [3, 6, 3], 'V': [7, 8], 'K': [9, 11, 9], 'r': [12, 12]}),
    'er_nova': clip(NOVA, 10, seg={'w': [0, 1], 's': [2, 3]}),
    'er_roar': clip(ROAR, 9, seg={'a': [0, 6]}),
    'er_stagger': clip(STAGGER, 8, seg={'a': [0, 6]}),
    'er_death': clip(DEATH, 8, seg={'a': [0, 8]}),
}
