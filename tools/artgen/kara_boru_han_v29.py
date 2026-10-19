"""Kara Börü Han v29: hamle başına tam gövde animasyonları (kara_boru_han_ink.draw pozlarıyla, tazı biriminde).

Kurt-ejder dili: sinsi alçak duruş (omuz yüksek, baş yere eğik), dörtnalda omurga toplanıp açılır (dönel dörtnal: arka
ayaklar, açık süzülme, ön ayaklar, toplu süzülme), sıçrayışta gövde gerilir, pençe yağmurunda ön ayaklar silah olur,
ağır pençede arka ayakları üstüne şaha kalkar ("!" hazırlıklardan ayrı, kule gibi silüet), "!!" zırhlı ulumada gövde
yere yapışır, yeleler kabarır. Yere basan patiler IK ile yerde kalır ('ik' hedefleri), havada gövde eğimi 'rot'.

Evre bölümleri Boss.gd'de adımlara eşlenir: w hazırlık, a hava / eylem, s temas, r toparlanma, d hücum döngüsü,
k kayarak duruş, c duvar tutunma, b ikinci pençe, W / S ağır pençe hazırlığı / teması.
"""
import math

import bosskit as bk
import kara_boru_han_ink as kb

SC = kb.SC
over = bk.over


def G(x, y=0.0):
    return ('ik', x, y)


def P(**kw):
    d = dict(bob=0.8, tilt=0.0, jaw=0.15, ph=0.0, rage=0.3, hy=2.0, hp=0.0, hf=G(-13.0), hb=G(-11.5), ff=G(10.5), fb=G(8.5),
             tw=0.0, mane=0.0, ear=0.0, chain=0.0, sq=0.0, hx=0.0, sx=0.0)
    d.update(kw)
    return d


def paws(p):
    hipp = (-10.0 + p.get('hx', 0.0), -19.0 + p['bob'] - p['tilt'] * 6)
    shp = (8.5 + p.get('sx', 0.0), -20.5 + p['bob'] + p['tilt'] * 6)
    hip_j = (hipp[0] + 0.5, hipp[1] + 0.5)
    sh_j = (shp[0] + 0.8, shp[1] + 1.5)
    return [kb._hind(hip_j, p[k])[2] for k in ('hf', 'hb')] + [kb._front(sh_j, p[k])[2] for k in ('ff', 'fb')]


def ground(p, lift=0.0):
    """En alçak pati y = -lift olacak biçimde gövdeyi indir / kaldır (FK dörtnal karelerinde yer teması)."""
    m = max(q[1] for q in paws(p))
    return over(p, bob=p['bob'] - lift - m)


def clip(frames, fps=10, loop=False, seg=None):
    return bk.clip(frames, fps, loop, seg)


# ------------------------------------------------------------ dolaşım
def _idle(t):
    s, c = math.sin(t * math.tau), math.cos(t * math.tau)
    tw_ = max(0.0, math.sin((t - 0.6) * math.tau * 2.5)) if 0.6 <= t < 1.0 else 0.0   # kulak seğirmesi / dudak kıvrımı
    return P(bob=1.0 + 0.5 * s, tilt=-0.02 * s, jaw=0.12 + 0.12 * max(0.0, s) + 0.25 * tw_, ph=t * math.tau, rage=0.3 + 0.12 * s,
             hy=2.6 + 0.5 * math.sin(t * math.tau + 0.6), hp=0.12 + 0.03 * s, tw=0.15 * math.sin(t * math.tau - 0.8), ear=0.1 + 0.5 * tw_,
             sx=0.3 * c, ff=G(10.8 + 0.3 * c), mane=-0.05 * s)


def _walk(t):
    """Sinsi yürüyüş (sürünerek yaklaşma): yanal sıralı adım (arka-ön aynı yan), baş omuz hizasının altında, kürek
    kemikleri sırayla kalkar; yere basan pati geriye eşit hızla akar."""
    S, st = 6.5, 0.66

    def foot(ph, x0):
        ph %= 1.0
        if ph < st:
            return G(x0 + S - 2 * S * ph / st)
        u = (ph - st) / (1 - st)
        e = u * u * (3 - 2 * u)
        return G(x0 - S + 2 * S * e, -math.sin(math.pi * u) * 3.6)
    b = math.cos(4 * math.pi * (t - 0.1))
    return P(bob=1.6 + 0.45 * b, tilt=0.04 * math.sin(2 * math.pi * t), hf=foot(t, -13.0), ff=foot(t + 0.25, 10.5), hb=foot(t + 0.5, -11.5),
             fb=foot(t + 0.75, 8.5), hy=3.4 + 0.4 * b, hp=0.22, jaw=0.25 + 0.1 * b, ph=t * math.tau * 2, rage=0.35, sx=0.6 * math.sin(2 * math.pi * t),
             tw=-0.1 + 0.12 * math.sin(2 * math.pi * t), ear=0.25, mane=0.05)


# dönel dörtnal anahtar pozları (FK açıları): açık süzülme, ön iniş, toplanma, toplu süzülme, arka iniş, arka itiş
_GAL = [
    dict(hb=(-1.1, 0.3), hf=(-1.0, 0.35), fb=(1.2, 0.2), ff=(1.35, 0.25), sx=1.6, hx=-1.0, tilt=-0.05, hy=0.6, hp=-0.04, lift=2.6),
    dict(hb=(-0.45, 0.8), hf=(-0.65, 0.6), fb=(0.95, 0.2), ff=(0.5, 0.2), sx=0.6, hx=-0.3, tilt=0.08, hy=2.0, hp=0.05, lift=0.0),
    dict(hb=(0.6, 1.4), hf=(0.35, 1.3), fb=(0.1, 0.25), ff=(-0.3, 0.3), sx=-1.6, hx=1.5, tilt=0.12, hy=2.6, hp=0.12, lift=0.0),
    dict(hb=(0.95, 1.6), hf=(0.85, 1.5), fb=(-0.5, 1.0), ff=(-0.75, 0.9), sx=-2.1, hx=2.0, tilt=0.04, hy=1.8, hp=0.08, lift=2.0),
    dict(hb=(0.75, 1.25), hf=(0.5, 1.0), fb=(0.0, 1.3), ff=(0.3, 1.2), sx=-1.0, hx=1.0, tilt=-0.08, hy=1.2, hp=0.0, lift=0.0),
    dict(hb=(-0.1, 0.8), hf=(-0.4, 0.6), fb=(0.8, 0.6), ff=(1.0, 0.5), sx=0.5, hx=0.0, tilt=-0.12, hy=0.8, hp=-0.04, lift=0.0),
]


def _gallop(t, low=0.0):
    k = bk.loop_keys(t, _GAL)
    lift = k.pop('lift')
    p = P(bob=0.0, jaw=0.45 + 0.3 * low, ph=t * math.tau, rage=0.45, tw=-0.45 - 0.25 * low, ear=0.45 + 0.3 * low, mane=0.35 + 0.2 * low,
          chain=-0.6, sq=0.6 * math.cos(t * math.tau * 2), **k)
    p['hy'] += 1.5 * low
    p['hp'] += 0.2 * low
    p = ground(p, lift)
    p['bob'] += 1.4 * low
    return p


# ------------------------------------------------------------ sıçrayış zinciri
POUNCE = [
    P(bob=3.0, tilt=0.05, hx=1.0, hf=G(-9.5), hb=G(-8.5), ff=G(12.0), fb=G(10.0), hy=3.0, hp=0.2, jaw=0.5, tw=0.5, ear=0.5, rage=0.45, mane=-0.2),
    P(bob=5.0, tilt=0.0, hx=1.6, sx=-1.0, hf=G(-8.5), hb=G(-7.5), ff=G(13.0), fb=G(11.0), hy=3.5, hp=0.25, jaw=0.85, tw=0.7, ear=0.6, rage=0.8,
      mane=-0.3, sq=0.4),
    P(bob=-0.5, tilt=-0.1, sx=1.0, hf=G(-15.5), hb=G(-14.5), ff=(1.0, 0.8), fb=(0.8, 0.9), hy=0.5, hp=-0.1, jaw=1.0, tw=-0.2, rage=0.9,
      rot=-0.28, rp=(-32.0, 0.0), mane=0.2),
    # 3-5: havada (gerilme, tepe, düşüş)
    P(bob=-2.0, hb=(-1.1, 0.3), hf=(-1.0, 0.35), ff=(1.35, 0.25), fb=(1.2, 0.2), sx=2.0, hx=-1.0, rot=-0.15, rp=(0.0, -46.0), jaw=1.0, hy=0.0,
      hp=-0.1, tw=-0.6, mane=0.45, chain=-1.2, rage=0.9),
    P(bob=-2.0, hb=(0.25, 1.2), hf=(0.35, 1.3), ff=(1.75, 1.5), fb=(1.55, 1.4), sx=0.0, rot=0.0, jaw=1.0, hy=0.4, tw=-0.3, mane=0.3, chain=-0.6,
      rage=1.0),
    P(bob=-2.0, hb=(-0.6, 0.5), hf=(-0.5, 0.45), ff=(0.65, 0.1), fb=(0.85, 0.15), sx=1.2, rot=0.22, rp=(0.0, -46.0), jaw=0.85, hy=1.0, hp=0.15,
      tw=-0.5, mane=0.4, chain=-1.0, rage=0.9),
    # 6-7: iniş (ön ayaklar yükü karşılar, göğüs çöker)
    P(bob=4.0, tilt=0.15, sx=-1.0, ff=G(13.5), fb=G(11.5), hf=G(-16.0), hb=G(-14.5), hy=3.2, hp=0.15, jaw=0.6, sq=0.7, tw=0.2, mane=-0.1, rage=0.6),
    P(bob=2.2, tilt=0.05, ff=G(12.0), fb=G(10.0), hf=G(-14.0), hb=G(-12.5), hy=2.6, jaw=0.35, sq=0.2, rage=0.45),
    P(bob=1.2, hy=2.4, jaw=0.25, hp=0.1),
]

BACK = [
    P(bob=1.0, hf=G(-12.0), hb=G(-10.5), ff=(1.9, 1.3), fb=(1.6, 1.4), jaw=0.5, hy=0.5, hp=-0.1, rot=-0.35, rp=(-28.0, 0.0), dx=6.0, tw=-0.5, mane=-0.2),
    P(bob=-2.0, hb=(0.6, 1.4), hf=(0.5, 1.3), ff=(0.5, 1.4), fb=(0.3, 1.5), rot=-0.15, rp=(0.0, -46.0), jaw=0.4, hy=1.2, tw=0.6),
    P(bob=-1.0, hb=(0.2, 0.8), hf=(0.15, 0.75), ff=(0.2, 0.3), fb=(0.05, 0.3), rot=-0.05, rp=(0.0, -46.0), jaw=0.4, hy=2.0, tw=0.4),
    P(bob=3.0, hf=G(-11.0), hb=G(-9.5), ff=G(12.0), fb=G(10.0), sq=0.5, hy=2.8, hp=0.15, jaw=0.45, tw=0.4, rage=0.5),
]

# ------------------------------------------------------------ yer yaran hamle (hücum)
RUSH = [
    P(bob=2.0, tilt=0.1, hf=G(-15.0), hb=G(-14.0), ff=G(15.5, -2.5), fb=G(9.0), hy=4.0, hp=0.3, jaw=0.7, rage=0.55, tw=0.3, ear=0.5, mane=-0.2),
    P(bob=3.0, tilt=0.2, hf=G(-15.5), hb=G(-14.5), ff=G(13.5), fb=G(11.5), hy=4.5, hp=0.38, jaw=0.95, rage=0.85, tw=0.5, ear=0.6, mane=-0.35,
      sq=0.3),
    over(_gallop(5 / 6), rot=-0.1, rp=(-30.0, 0.0), jaw=1.0, hy=2.5, hp=0.2),
] + [_gallop(k / 4, low=1.0) for k in range(4)] + [
    P(bob=2.0, tilt=-0.15, hx=1.5, ff=G(19.5), fb=G(17.5), hf=G(-7.0), hb=G(-6.0), hy=1.2, hp=-0.1, jaw=0.5, rot=-0.08, rp=(0.0, 0.0), tw=0.6,
      mane=0.4, rage=0.5),
    P(bob=1.8, tilt=0.08, ff=G(16.0), fb=G(14.0), hf=G(-10.0), hb=G(-9.0), hy=2.4, hp=0.12, jaw=0.4, tw=0.3, rage=0.45),
    P(bob=1.2, hy=2.6, hp=0.12, jaw=0.3),
]

# ------------------------------------------------------------ pençe yağmuru (3 hızlı + şaha kalkıp ağır pençe)
_RP = (-30.0, 0.0)
FLURRY = [
    P(bob=0.5, ff=(2.35, 0.9), fb=G(9.0), jaw=0.7, hy=0.5, rot=-0.24, rp=_RP, dy=-3.0, dx=6.0, rage=0.55, tw=-0.5, mane=-0.2),
    P(bob=0.5, ff=(2.7, 1.1), fb=G(9.0), jaw=0.9, hy=0.2, rot=-0.3, rp=_RP, dy=-3.0, dx=6.0, rage=0.6, tw=-0.55, mane=-0.25),
    P(bob=1.0, sx=2.5, hx=0.5, ff=(1.45, -0.25), fb=G(9.5), jaw=1.0, hy=1.8, hp=0.15, rot=0.1, rp=_RP, rage=0.7, tw=-0.3, mane=0.3),
    P(bob=1.2, sx=1.8, ff=(0.35, 0.1), fb=(2.6, 1.0), jaw=0.9, hy=1.6, hp=0.05, rot=0.08, rp=_RP, rage=0.7, tw=-0.2),
    P(bob=1.0, sx=2.5, ff=(0.6, 0.5), fb=(1.45, -0.25), jaw=1.0, hy=1.8, hp=0.15, rot=0.1, rp=_RP, rage=0.75, tw=-0.3, mane=0.3),
    P(bob=1.2, sx=1.8, ff=(2.6, 1.0), fb=(0.35, 0.1), jaw=0.9, hy=1.6, rot=0.08, rp=_RP, rage=0.75, tw=-0.2),
    # 6-8: ağır pençe hazırlığı: arka ayaklar üstüne şaha kalkar, iki ön pençe göğe açık, kristaller alevlenir
    P(bob=0.0, ff=(2.6, 0.5), fb=(2.3, 0.3), hf=G(-12.5), hb=G(-11.0), jaw=1.0, hy=-0.5, hp=-0.15, rot=-0.72, rp=_RP, dy=-3.0, dx=14.0, rage=1.0, tw=-1.0,
      mane=-0.5),
    P(bob=-0.3, ff=(2.95, 0.6), fb=(2.7, 0.45), hf=G(-12.5), hb=G(-11.0), jaw=1.0, hy=-1.0, hp=-0.2, rot=-0.84, rp=_RP, dy=-3.0, dx=14.0, rage=1.0, tw=-1.1,
      mane=-0.6),
    P(bob=0.0, ff=(2.0, -0.2), fb=(1.8, -0.1), hf=G(-13.5), hb=G(-12.0), jaw=1.0, hy=0.5, hp=0.05, rot=-0.48, rp=_RP, dy=-3.0, dx=10.0, rage=1.0, tw=-0.7,
      mane=0.0),
    # 9-10: iki pençe birden yere (temas)
    P(bob=4.0, tilt=0.1, sx=2.5, ff=G(20.0), fb=G(18.0), hf=G(-15.0), hb=G(-13.5), hy=3.2, hp=0.22, jaw=1.0, sq=0.7, rot=0.1, rp=(0.0, 0.0),
      rage=1.0, tw=-0.2, mane=0.4),
    P(bob=3.0, tilt=0.06, sx=2.0, ff=G(19.0), fb=G(17.0), hf=G(-14.5), hb=G(-13.0), hy=3.0, hp=0.18, jaw=0.7, sq=0.25, rot=0.05, rp=(0.0, 0.0),
      rage=0.8),
    P(bob=1.5, hy=2.6, jaw=0.35, hp=0.12, rage=0.5),
]

# ------------------------------------------------------------ uluma (ruh tazıları çağrılır)
HOWL = [
    P(bob=2.0, hy=3.0, hp=0.4, jaw=0.2, rage=0.5, tw=0.2),
    P(bob=1.0, tilt=-0.1, hy=2.0, hp=0.2, jaw=0.1, rage=0.6, mane=-0.3, tw=0.4),
    P(bob=0.4, tilt=-0.25, hy=-6.0, jaw=0.8, rage=0.9, mane=-0.5, tw=0.6),
    P(bob=0.0, tilt=-0.3, hy=-7.0, jaw=1.0, rage=1.0, mane=-0.7, tw=0.7, ph=1.0),
    P(bob=0.2, tilt=-0.3, hy=-6.8, jaw=0.95, rage=1.0, mane=-0.65, tw=0.72, ph=2.0),
    P(bob=0.0, tilt=-0.31, hy=-7.2, jaw=1.0, rage=0.95, mane=-0.75, tw=0.68, ph=3.0),
    P(bob=0.2, tilt=-0.29, hy=-6.9, jaw=0.97, rage=1.0, mane=-0.7, tw=0.7, ph=4.0),
]

# ------------------------------------------------------------ duvardan pike (tutunma, dalış, iniş)
_WP = (-2.3, -46.0)
WALL = [
    P(bob=3.0, sq=0.5, hf=G(-10.0), hb=G(-9.0), ff=G(11.0), fb=G(9.0), hy=1.0, hp=-0.45, jaw=0.6, rot=1.15, rp=_WP, dx=-8.0, dy=-8.0, rage=0.8, tw=-1.2),
    P(bob=2.0, hf=G(-11.0), hb=G(-10.0), ff=G(11.5), fb=G(9.5), hy=1.0, hp=-0.5, jaw=0.75, rot=1.15, rp=_WP, dx=-8.0, dy=-8.0, rage=0.9, tw=-1.25, ph=1.0),
    P(bob=2.4, hf=G(-11.0), hb=G(-10.0), ff=G(11.5), fb=G(9.5), hy=1.2, hp=-0.55, jaw=0.95, rot=1.15, rp=_WP, dx=-8.0, dy=-8.0, rage=1.0, tw=-1.2,
      ph=2.0, mane=-0.3),
    P(bob=-2.0, hb=(-1.1, 0.3), hf=(-1.0, 0.35), ff=(1.35, 0.25), fb=(1.2, 0.2), sx=2.0, hx=-1.0, rot=0.9, rp=_WP, dy=-14.0, jaw=1.0, hy=0.0, tw=-0.7,
      mane=0.5, chain=-1.2, rage=1.0),
    P(bob=-2.0, hb=(-0.9, 0.4), hf=(-0.8, 0.45), ff=(1.0, 0.05), fb=(0.9, 0.1), sx=2.2, hx=-1.2, rot=0.85, rp=_WP, dy=-14.0, jaw=1.0, hy=0.5, tw=-0.8,
      mane=0.55, chain=-1.3, rage=1.0),
    P(bob=5.0, tilt=0.15, sx=-1.0, ff=G(14.5), fb=G(12.5), hf=G(-15.0), hb=G(-13.5), hy=3.5, hp=0.2, jaw=1.0, sq=0.85, rage=1.0, tw=0.3, mane=0.3),
    P(bob=3.6, tilt=0.08, ff=G(13.5), fb=G(11.5), hf=G(-14.0), hb=G(-12.5), hy=3.0, hp=0.15, jaw=0.6, sq=0.3, rage=0.8),
    P(bob=1.5, hy=2.6, jaw=0.35, hp=0.12, rage=0.5),
]

# ------------------------------------------------------------ bozgun kristalleri (sırttan yay atışı)
CRYS = [
    P(bob=2.0, tilt=-0.06, hy=3.0, hp=0.3, jaw=0.5, rage=0.9, mane=-0.4, tw=0.4),
    P(bob=2.6, tilt=-0.1, hy=3.4, hp=0.38, jaw=0.7, rage=1.0, mane=-0.5, tw=0.5, sq=0.3),
    P(bob=-0.5, tilt=-0.12, hy=1.0, hp=-0.15, jaw=1.0, rage=1.0, mane=0.4, tw=0.2, ph=1.5),
    P(bob=1.4, tilt=-0.06, hy=2.2, hp=0.1, jaw=0.8, rage=0.95, mane=0.0, tw=0.3, ph=2.5),
    P(bob=2.4, tilt=-0.08, hy=3.0, hp=0.3, jaw=0.6, rage=1.0, mane=-0.3, tw=0.45, ph=3.5),
]

# ------------------------------------------------------------ yakın cezalandırıcı "!!": yere yapışır, sonra şok uluması
NOVA = [
    P(bob=4.0, ff=G(16.0), fb=G(14.0), hf=G(-15.5), hb=G(-14.0), hy=4.2, hp=0.45, jaw=1.0, rage=1.0, mane=-0.6, tw=0.9, ear=0.8),
    P(bob=5.0, ff=G(16.5), fb=G(14.5), hf=G(-16.0), hb=G(-14.5), hy=4.6, hp=0.5, jaw=1.0, rage=1.0, mane=-0.7, tw=1.0, ear=0.8, sq=0.45),
    P(bob=0.0, tilt=-0.2, ff=G(14.0), fb=G(12.0), hf=G(-15.0), hb=G(-13.5), hy=-5.5, jaw=1.0, rage=1.0, mane=-0.8, tw=0.8, ph=1.0),
    P(bob=0.3, tilt=-0.22, ff=G(14.0), fb=G(12.0), hf=G(-15.0), hb=G(-13.5), hy=-6.2, jaw=1.0, rage=1.0, mane=-0.75, tw=0.75, ph=2.0),
]

# ------------------------------------------------------------ kükreme (giriş / evre): şaha kalkıp göğe ulur
ROAR = [
    P(bob=3.0, hy=3.5, hp=0.35, jaw=0.3, rage=0.6, tw=0.3, mane=-0.2),
    P(bob=0.5, ff=(2.2, 0.8), fb=G(9.5), rot=-0.3, rp=_RP, dy=-3.0, dx=6.0, jaw=0.6, hy=0.5, rage=0.75, tw=-0.5),
    P(bob=0.0, ff=(2.6, 0.7), fb=(2.2, 0.9), hf=G(-12.5), hb=G(-11.0), rot=-0.58, rp=_RP, dy=-3.0, dx=12.0, jaw=0.85, hy=-2.0, rage=0.9, tw=-0.9, mane=-0.4),
    P(bob=0.0, ff=(2.8, 0.9), fb=(2.4, 1.1), hf=G(-12.5), hb=G(-11.0), rot=-0.62, rp=_RP, dy=-3.0, dx=12.0, jaw=1.0, hy=-6.5, rage=1.0, tw=-1.0, mane=-0.7, ph=1.0),
    P(bob=0.0, ff=(2.75, 0.85), fb=(2.45, 1.15), hf=G(-12.5), hb=G(-11.0), rot=-0.62, rp=_RP, dy=-3.0, dx=12.0, jaw=1.0, hy=-6.8, rage=1.0, tw=-1.0, mane=-0.75,
      ph=2.0),
    P(bob=1.5, ff=(1.0, 0.6), fb=(0.8, 0.7), rot=-0.2, rp=_RP, jaw=0.8, hy=0.0, rage=0.9, tw=-0.3),
    P(bob=3.0, tilt=0.1, ff=G(13.0), fb=G(11.0), sq=0.5, hy=3.0, hp=0.25, jaw=0.85, rage=0.8, tw=0.3, mane=-0.3),
]

# ------------------------------------------------------------ duruş kırılması
STAGGER = [
    P(bob=1.0, tilt=-0.1, hx=1.0, hy=-1.5, hp=-0.25, jaw=0.6, rot=-0.14, rp=_RP, ear=-0.6, mane=-0.3, chain=0.8, tw=-0.3, rage=0.2),
    P(bob=3.5, tilt=-0.3, hf=G(-15.0), hb=G(-13.0), ff=G(12.0), fb=G(9.5), hy=0.5, hp=-0.1, jaw=0.5, ear=-0.6, tw=0.5, rage=0.15),
    P(bob=7.0, tilt=0.0, hf=G(-15.5), hb=G(-13.5), ff=G(14.0), fb=G(12.0), hy=4.5, hp=0.55, jaw=0.4, ear=-0.5, tw=-0.2, rage=0.1, sq=0.4),
    P(bob=7.2, tilt=0.02, hf=G(-15.5), hb=G(-13.5), ff=G(14.0), fb=G(12.0), hy=5.0, hp=0.6, jaw=0.3, ear=-0.5, tw=-0.25, rage=0.1, chain=1.0),
    P(bob=7.0, tilt=0.0, hf=G(-15.5), hb=G(-13.5), ff=G(14.0), fb=G(12.0), hy=3.5, hp=0.25, jaw=0.5, ear=-0.4, tw=-0.15, rage=0.15, chain=-1.0),
    P(bob=4.0, tilt=0.06, hf=G(-14.0), hb=G(-12.5), ff=G(12.5), fb=G(10.5), hy=3.0, hp=0.2, jaw=0.7, tw=0.2, rage=0.35),
    P(bob=1.5, hy=2.6, hp=0.15, jaw=0.85, rage=0.6, mane=-0.3, tw=0.4),
]

# ------------------------------------------------------------ ölüm: şaha kalkıp geri sendeler, arka ayaklar çöker, yere yığılır
DEATH = [
    P(bob=0.5, ff=(2.3, 0.8), fb=(2.0, 1.0), rot=-0.32, rp=_RP, dy=-3.0, dx=6.0, jaw=1.0, hy=-4.0, rage=0.8, tw=-0.6, mane=-0.5, ear=-0.6),
    P(bob=2.0, tilt=-0.2, hx=1.0, hf=G(-15.0), hb=G(-14.0), ff=G(13.0), fb=G(11.0), jaw=0.8, hy=0.0, hp=-0.2, rage=0.6, ear=-0.6, tw=0.3),
    P(bob=4.0, tilt=-0.4, hf=G(-14.5), hb=G(-13.0), ff=G(12.0), fb=G(10.0), jaw=0.6, hy=1.0, hp=0.0, rage=0.45, ear=-0.6, tw=0.0),
    P(bob=7.5, tilt=-0.2, hf=G(-15.5), hb=G(-14.0), ff=G(14.0), fb=G(12.0), jaw=0.5, hy=3.0, hp=0.3, rage=0.3, ear=-0.6, tw=-0.3),
    P(bob=9.0, tilt=0.0, hf=G(-17.0), hb=G(-15.5), ff=G(16.0), fb=G(14.0), jaw=0.5, hy=5.0, hp=0.5, rage=0.2, ear=-0.7, tw=-0.5),
    P(bob=10.5, tilt=0.02, hf=G(-18.5), hb=G(-17.0), ff=G(18.0), fb=G(16.0), jaw=0.45, hy=5.0, hp=0.55, rage=0.1, ear=-0.8, tw=-0.6, sq=0.4),
    P(bob=11.0, tilt=0.02, hf=G(-19.0), hb=G(-17.5), ff=G(18.5), fb=G(16.5), jaw=0.3, hy=5.2, hp=0.58, rage=0.05, ear=-0.8, tw=-0.65, sq=0.2),
    P(bob=11.0, tilt=0.02, hf=G(-19.0), hb=G(-17.5), ff=G(18.5), fb=G(16.5), jaw=0.2, hy=5.3, hp=0.6, rage=0.0, ear=-0.8, tw=-0.7),
    P(bob=11.0, tilt=0.02, hf=G(-19.0), hb=G(-17.5), ff=G(18.5), fb=G(16.5), jaw=0.15, hy=5.3, hp=0.6, rage=0.0, ear=-0.8, tw=-0.7),
]


CLIPS = {
    'idle': clip([_idle(k / 8) for k in range(8)], 7, loop=True),
    'run': clip([_gallop(k / 8) for k in range(8)], 14, loop=True),
    'walk': clip([_walk(k / 8) for k in range(8)], 12, loop=True),
    'kbh_pounce': clip(POUNCE, 12, seg={'w': [0, 2], 'a': [3, 5], 's': [6, 7], 'r': [8, 8]}),
    'kbh_back': clip(BACK, 10, seg={'a': [0, 2], 'r': [3, 3]}),
    'kbh_rush': clip(RUSH, 14, seg={'w': [0, 2], 'd': [3, 6, 3], 'k': [7, 8], 'r': [9, 9]}),
    'kbh_flurry': clip(FLURRY, 14, seg={'w': [0, 1], 'a': [2, 3], 'b': [4, 5], 'W': [6, 8], 'S': [9, 10], 'r': [11, 11]}),
    'kbh_howl': clip(HOWL, 10, seg={'w': [0, 1], 'a': [2, 6, 4]}),
    'kbh_wall': clip(WALL, 10, seg={'c': [0, 2, 1], 'd': [3, 4], 's': [5, 5], 'r': [5, 7]}),
    'kbh_crys': clip(CRYS, 10, seg={'w': [0, 1], 'a': [2, 4]}),
    'kbh_nova': clip(NOVA, 10, seg={'w': [0, 1], 's': [2, 3]}),
    'kbh_roar': clip(ROAR, 9, seg={'a': [0, 6]}),
    'kbh_stagger': clip(STAGGER, 8, seg={'a': [0, 6]}),
    'kbh_death': clip(DEATH, 8, seg={'a': [0, 8]}),
}
