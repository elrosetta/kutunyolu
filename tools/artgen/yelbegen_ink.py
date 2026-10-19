"""Yelbegen — stil v2 "mürekkep-cel" boss (inkkit.py + bosskit.py). v1: creatures3.draw_yelbegen.

Türk masallarının çok başlı devi (Yelbegen / Celmoğuz); burada Kaf Dağı'nın üç başlı ayaz devi. Buz mavisi, kırağı
desenli deri; omuzlarını ve sırtını örten kaba ak post pelerin (yaka halkası); omuzlarda, ön kollarda ve sırtta
büyüyen buz kristalleri (ışıma); üç ayrı baş: ortadaki iri ve azı dişli, buz boynuzlu; arkadaki başı geriye-yukarı
bakar, öndeki daha küçük baş hırlayarak öne eğilir; hepsinin gözleri ayaz mavisi yanar. Kemik saplı, ucu dev buz
kristali olan mızrak (yaba-kargı); baldırlarda ak post dolak, kemer ve kemik tokalı koyu post peştamal.

Pozlar Tepegöz ile aynı iskelet ve zamanlamayla (tepegoz_ink anahtar kareleri; mızrak açıları ayrı). Animasyon adları /
kare sayıları / fps v1 ile aynı; çapalar 'hand' (mızrak eli) ve 'mouth' (orta baş). Hücre dünya 256x208, ayak (96, 202).
"""
import math

import inkkit as ik
from inkkit import Ink, INK
import bosskit as bk
from bosskit import along, add, lerp, polar
import tepegoz_ink as tg

TEX = bk.TEX
CELL = (1024, 832)
FEET = (384, 808)

SKIN = Ink('#7a90b6', '#2a3262', '#cadcf0', '#141838', name='ayaz derisi')
SKIN_B = SKIN.darker(0.74, 'uzak deri')
SKIN_D = Ink('#6f84aa', '#2c3462', '#a8bcd8', name='dudak/kapak')
FUR = Ink('#e6ecf2', '#8290b6', '#ffffff', '#4e5a84', kind='fur', name='ak post')
FUR_B = FUR.darker(0.8, 'uzak post')
HIDE = Ink('#4a4e6a', '#22243a', '#767c9a', '#121322', kind='fur', name='koyu post')
LEATHER = Ink('#5a4440', '#2a1c20', '#866660', name='deri')
BONE = Ink('#e2dac4', '#8c8470', '#fffbea', '#575040', name='kemik')
ICE = Ink('#bfe6fa', '#5a8ac4', '#ffffff', '#2c4a8a', name='buz')
ICE_D = Ink('#8cc4ec', '#3e64a8', '#e6f8ff', name='koyu buz')
NAIL = Ink('#28304a', '#12162a', '#5a6484', name='kara tırnak')
HAIR = Ink('#f2f6fa', '#94a0c0', '#ffffff', '#5a6688', kind='fur', name='kırağı saç')
EYE = (0.62, 0.95, 1.0)
EYE_GLOW = (0.25, 0.8, 1.0)
ICE_GLOW = (0.18, 0.55, 0.9)
MOUTH_IN = (0.12, 0.12, 0.26)

HIP_H = 72.0
L_TH, L_SH = 36.0, 36.0
L_UP, L_FO = 35.0, 32.0
SP_F, SP_B = 44.0, 30.0       # mızrak: elden öne sap, geriye sap (dünya)
BLADE = 34.0


def _p(d, **kw):
    d = dict(d)
    d.setdefault('heads', (0.0, 0.0, 0.0))
    d.update(kw)
    return d


def _idle(i):
    t = i / 8
    s = math.sin(t * math.tau)
    p = tg._idle(t)
    # mızrak dik tutulur (asa gibi), dipçik yerde
    return _p(p, arm=0.55 + 0.02 * s, el=0.95, ca=-1.42 + 0.02 * s, heads=(0.15 * s, -0.12 * math.sin(t * math.tau + 1.3), 0.08 * math.sin(t * math.tau + 2.2)))


def _walk(i):
    t = i / 8
    s = math.sin(t * math.tau)
    p = tg._walk(t)
    return _p(p, arm=0.6 - 0.1 * s, el=0.95, ca=-1.3 - 0.08 * s, heads=(0.1 * s, -0.1 * s, 0.05))


def _heads(p, heads):
    return _p(p, heads=heads)


ANIMS = {
    'idle': (8, _idle),
    'walk': (8, _walk),
    'windup': (4, lambda i: _p(tg._windup(i), heads=(-0.15 - 0.1 * i, 0.15 + 0.1 * i, -0.1 * i), **({'ca': -2.5} if i >= 2 else {}))),
    'strike': (4, lambda i: _heads(tg._strike(i), (0.15, -0.2, 0.25))),
    'slam': (3, lambda i: _heads(tg._slam(i), (-0.2, 0.25, 0.3))),
    'cast': (3, lambda i: _heads(tg._cast(i), (-0.35, 0.35, -0.3) if i == 2 else (0.1, -0.1, 0.2))),
    'hurt': (2, lambda i: _heads(tg._hurt(i), (0.3, 0.3, -0.2))),
    'rage': (3, lambda i: _heads(tg._rage(i), (-0.3 * i, 0.3 * i, -0.4 * i))),
}


# ------------------------------------------------------------ parçalar
def _crystal(cv, base, ang, ln, w, z, g=1.0, mat=ICE):
    """Buz kristali: altıgen kesitli, sivri uçlu prizma; ışıyan kenar."""
    d = (math.cos(ang), math.sin(ang))
    n = (-d[1], d[0])
    b0, b1 = add(base, n, w * 0.5), add(base, n, -w * 0.5)
    s0, s1 = add(b0, d, ln * 0.7), add(b1, d, ln * 0.62)
    tip = add(base, d, ln)
    path = cv.blob([b0, s0, (tip[0], tip[1], 0.0), s1, b1], closed=True)
    det = [('hi', cv.blob([b0, s0, (tip[0], tip[1], 0.0), add(base, d, ln * 0.6)])),
           ('ink', [add(base, d, ln * 0.1), add(base, d, ln * 0.85)], 0.8, (0.2, 0.6))]
    cv.shape(path, mat, z=z, sd=w * 0.35, hi=0.0, details=det, ol=0.85, flat=False, soft=0.0)
    cv.fill(cv.blob([add(base, d, ln * 0.55), (tip[0], tip[1], 0.0), add(add(base, d, ln * 0.6), n, -w * 0.15)]), (0.85, 0.97, 1.0),
            z=z + 0.01, glow=tuple(c * g for c in ICE_GLOW))


def _leg(cv, hip, foot, z, near):
    ank = (foot[0], foot[1] - 4.5)
    knee, _ = bk.ik2(hip, ank, L_TH, L_SH, -1)
    m = SKIN if near else SKIN_B
    thigh = bk.muscle(cv, hip, knee, 13.0, 9.0, front=1.6, back=1.2, at=0.35, knob=0.8)
    shin = bk.muscle(cv, knee, ank, 9.2, 5.8, front=0.2, back=2.4, at=0.3)
    det = []
    if near:
        det += [('ink', [along(hip, knee, 0.25, -6), along(hip, knee, 0.55, -5.5), along(hip, knee, 0.85, -4)], 1.4, (0.2, 0.6)),
                ('stroke', [along(hip, knee, 0.2, 3), along(hip, knee, 0.4, 6), along(hip, knee, 0.5, 4)], 1.1, SKIN.hi, (0.3, 0.6)),
                ('stroke', [along(hip, knee, 0.45, 5), along(hip, knee, 0.6, 8)], 1.0, SKIN.hi, (0.3, 0.6))]
    cv.shape(ik.union(thigh, shin), m, z=z, sd=4.0, hi=0.45 if near else 0.0, details=det, bounce=0.35 if near else 0.0,
             hatch=0.4 if near else 0.0)
    # ak post dolak (baldırı saran post, iki ip bağı)
    wrap = cv.blob([along(knee, ank, 0.3, -11), along(knee, ank, 0.25, 0), along(knee, ank, 0.3, 11.5)]
                   + bk.ragged([along(knee, ank, 1.02, 9.0), along(knee, ank, 1.06, 0.0), along(knee, ank, 1.02, -8.0)], 1.6, 3, -1.0, 1.0))
    fm = FUR if near else FUR_B
    wdet = [('stroke', [along(knee, ank, t, -9), along(knee, ank, t + 0.03, 0), along(knee, ank, t, 9.5)], 1.6, LEATHER.base, (0.05, 0.05))
            for t in (0.48, 0.8)]
    cv.shape(wrap, fm, z=z + 0.2, sd=2.4, hi=0.4 if near else 0.0, fur=1.0, details=wdet)
    f = foot
    fpts = [(f[0] - 7.5, f[1] - 6.0), (f[0] - 2.0, f[1] - 8.0), (f[0] + 6.0, f[1] - 5.5), (f[0] + 13.0, f[1] - 3.0),
            (f[0] + 16.0, f[1] - 0.6), (f[0] + 15.5, f[1] + 0.6, 0.0), (f[0] - 8.5, f[1] + 0.6, 0.0), (f[0] - 9.5, f[1] - 3.0)]
    fdet = [('ink', [(f[0] + 9.0 + k * 2.4, f[1] - 3.2 + k * 0.6), (f[0] + 9.4 + k * 2.4, f[1] + 0.2)], 1.1, (0.2, 0.5)) for k in range(3)]
    cv.shape(cv.blob(fpts), m, z=z + 0.4, sd=2.4, hi=0.3 if near else 0.0, details=fdet)
    if near:
        for k in range(3):
            cv.shape(cv.ellipse((f[0] + 10.4 + k * 2.4, f[1] - 1.0 + k * 0.5), 1.1, 0.75, 0.2), NAIL, z=z + 0.5, sd=0.3, ol=0.6, flat=True)
    return knee


def _spear(cv, h, ca, z, glow):
    d = (math.cos(ca), math.sin(ca))
    butt = add(h, d, -SP_B)
    head = add(h, d, SP_F)
    tip = add(head, d, BLADE)
    # sap: kemik/koyu ağaç, deri sargılı, kemik halkalar
    shaft = cv.capsule(butt, head, 3.0, 3.3)
    sdet = [('ink', [along(butt, head, t, -2.2), along(butt, head, t + 0.012, 2.2)], 0.9, (0.1, 0.1)) for t in (0.36, 0.39, 0.42, 0.45, 0.48)]
    sdet.append(('stroke', [along(butt, head, 0.05, 1.0), along(butt, head, 0.95, 1.0)], 0.8, BONE.hi, (0.2, 0.2)))
    cv.shape(shaft, BONE, z=z, sd=1.2, hi=0.3, details=sdet)
    for t in (0.06, 0.9):
        cv.shape(cv.ellipse(along(butt, head, t), 1.8, 3.4, ca), LEATHER, z=z + 0.05, sd=0.6, ol=0.85)
    # dipçik: sivri buz parçası
    _crystal(cv, butt, ca + math.pi, 7.0, 4.0, z - 0.05, 0.5 + 0.5 * glow)
    # baş: dev buz kristali (yassı, çift yanlı, kenarı dişli), kökünde yan kristaller
    n = (-d[1], d[0])
    w = 12.5
    pts = [add(head, n, 3.0, ), add(add(head, d, 5.0), n, w, ), (add(add(head, d, 8.0), n, w * 0.7)[0], add(add(head, d, 8.0), n, w * 0.7)[1], 0.0),
           (add(add(head, d, 13.0), n, w * 0.85)[0], add(add(head, d, 13.0), n, w * 0.85)[1], 0.0), add(add(head, d, 20.0), n, w * 0.45),
           (tip[0], tip[1], 0.0), add(add(head, d, 20.0), n, -w * 0.4), (add(add(head, d, 14.0), n, -w * 0.8)[0], add(add(head, d, 14.0), n, -w * 0.8)[1], 0.0),
           (add(add(head, d, 9.0), n, -w * 0.62)[0], add(add(head, d, 9.0), n, -w * 0.62)[1], 0.0), add(add(head, d, 4.0), n, -w), add(head, n, -3.0)]
    blade = cv.blob(pts)
    bdet = [('hi', cv.blob([add(head, n, 2.0), add(add(head, d, 6.0), n, w * 0.9), add(add(head, d, 12.0), n, w * 0.7), (tip[0], tip[1], 0.0),
                            add(add(head, d, 10.0), n, 0.5)])),
            ('ink', [add(head, d, 2.0), add(head, d, BLADE * 0.9)], 1.0, (0.2, 0.7)),
            ('ink', [add(add(head, d, 7.0), n, 3.0), add(add(head, d, 10.0), n, 0.5)], 0.8, (0.2, 0.2))]
    cv.shape(blade, ICE, z=z + 0.1, sd=2.0, hi=0.0, details=bdet, ol=1.0, soft=0.0)
    g = 0.5 + 0.5 * glow
    cv.stroke([add(head, d, 3.0), add(add(head, d, 12.0), n, 0.8), add(tip, d, -2.0)], 2.0, z=z + 0.12, col=(0.9, 0.98, 1.0),
              taper=(0.3, 0.7), glow=tuple(c * g for c in ICE_GLOW))
    for s in (-1, 1):
        _crystal(cv, add(head, n, s * 2.0), ca + s * 1.0, 9.0, 3.6, z + 0.08, g)
    return tip


def _ice_head(cv, H, sc, ht, jaw, glow, z, seed=0.0, crown=True, near=True, flip=False):
    ca_, sa_ = math.cos(ht), math.sin(ht)
    fx = -1.0 if flip else 1.0

    def Q(u, v, *t):
        u, v = u * sc * fx, v * sc
        return (H[0] + u * ca_ - v * sa_, H[1] + u * sa_ + v * ca_) + tuple(t)
    ja = jaw * 0.45

    def J(u, v):
        uu, vv = u + 2.0, v - 5.0
        return Q(-2.0 + uu * math.cos(ja) - vv * math.sin(ja), 5.0 + uu * math.sin(ja) + vv * math.cos(ja))
    sm = SKIN if near else SKIN_B
    g = 0.45 + 0.55 * glow
    if jaw > 0.12:
        cv.fill(cv.blob([Q(3, 6), Q(16, 6.5), J(15, 9), J(5, 11), J(0, 8.5)]), MOUTH_IN, z=z + 0.2)
    lower = cv.blob([J(-6, 5), J(4, 8.0), J(15, 8.6), J(18, 10.5), J(16.5, 14.5), J(10, 17.0), J(1, 16.5), J(-6, 12.0)])
    cv.shape(lower, sm, z=z + 0.3, sd=2.4, hi=0.3, bounce=0.3)
    for (u, ln) in ((15.0, 6.5), (8.5, 5.0)):
        b0, b1 = J(u - 1.5, 9.0), J(u + 1.5, 9.0)
        cv.shape(cv.blob(bk.spike_pts(b0, b1, J(u + 1.2, 9.0 - ln), 0.4)), BONE, z=z + 0.9, sd=0.7, hi=0.3, ol=0.85)
    skull = cv.blob([Q(-12, 0), Q(-11, -9), Q(-5, -14), Q(3, -15), Q(10, -12), Q(14, -6), Q(14.5, -2), Q(18.5, 1.6), Q(18, 4.0, 0.5),
                     Q(14, 5.5), Q(7, 6.0), Q(0, 6.0), Q(-6, 9), Q(-10, 6)])
    det = [('deep', cv.blob([Q(3, -6.5), Q(9, -8.5), Q(14, -6), Q(13, -2.5), Q(5, -2.5)])),
           ('ink', [Q(14.0, -1.0), Q(16.0, 2.0), Q(15.0, 4.5)], 1.2, (0.2, 0.3)),
           ('ink', [Q(11, 2), Q(7, 4.0), Q(3, 3.5)], 1.0, (0.3, 0.6)),
           ('stroke', [Q(-6, -10), Q(-2, -8), Q(-4, -4)], 1.0, SKIN.hi, (0.3, 0.6)),
           ('ink', [Q(-1, -12), Q(4, -13), Q(8, -11.5)], 0.9, (0.3, 0.4))]
    cv.shape(skull, sm, z=z + 0.5, sd=3.0, hi=0.45 if near else 0.0, details=det, cast=1.0, bounce=0.35, hatch=0.35 if near else 0.0)
    # kırağı saç: başın arkasından geriye savrulan ak perçem
    tl = []
    for k in range(5):
        a = math.pi * (1.0 + k * 0.1) + ht + math.sin(seed + k) * 0.08
        b = Q(-3 - k * 2.4, -14 + k * 3.0)
        tl.append([add(b, (math.cos(a + 1.6), math.sin(a + 1.6)), 2.2 * sc), polar(b, a, (10.0 - k * 0.7) * sc) + (0.0,),
                   add(b, (math.cos(a - 1.6), math.sin(a - 1.6)), 2.2 * sc)])
    cv.shape(ik.union(*[cv.blob(t) for t in tl], cv.blob([Q(-4, -15), Q(-12, -11), Q(-13, -3), Q(-6, -9)])), HAIR if near else FUR_B,
             z=z + 0.45, sd=1.6, hi=0.3, fur=0.6)
    # kırağı sakal (çeneden sarkan buz saçakları)
    beard = cv.blob([J(2, 15.0), J(8, 17.0), J(14, 15.0), J(12, 21.0), (J(9, 25.0)[0], J(9, 25.0)[1], 0.0), J(7, 20.0), (J(4, 23.0)[0], J(4, 23.0)[1], 0.0), J(2, 18.5)])
    cv.shape(beard, HAIR if near else FUR_B, z=z + 0.35, sd=1.2, hi=0.3, fur=0.5)
    if jaw > 0.12:
        for k in range(4):
            u = 5.5 + k * 3.0
            cv.fill(cv.blob([Q(u - 1.1, 6.0), Q(u + 1.1, 6.0), Q(u, 8.4, 0.0)]), BONE.base, z=z + 0.55)
    # iki göz (ayaz mavisi, ışır) + buzlu kaş
    for (u, v, r) in ((7.0, -4.6, 2.1), (12.2, -4.3, 1.5)):
        cv.fill(cv.blob([Q(u - r * 1.3, v - 0.5, 0.0), Q(u, v - r * 0.15), Q(u + r * 1.3, v + 0.5, 0.0), Q(u, v + r * 0.45)]), EYE, z=z + 0.8,
                glow=tuple(c * g for c in EYE_GLOW))
    brow = cv.blob([Q(1, -10.0), Q(8, -9.6), Q(15.5, -5.0), Q(15.2, -3.4, 0.0), Q(8, -5.8), Q(2, -7.2)])
    cv.shape(brow, sm, z=z + 0.95, sd=1.4, hi=0.45, cast=0.8)
    for k in range(3):   # kaştan sarkan buz saçağı
        u = 5.0 + k * 3.5
        cv.fill(cv.blob([Q(u - 0.8, -6.4 + k * 0.9), Q(u + 0.8, -6.0 + k * 0.9), Q(u + 0.1, -3.6 + k * 0.9 + (k % 2), 0.0)]), ICE.base, z=z + 0.96)
    cv.fill(cv.ellipse(Q(17.5, 3.0), 1.2, 0.7, ht + 0.3), INK, z=z + 1.0)
    # buz boynuzlar/taç: başın üstünden çıkan kristaller
    if crown:
        for k, (u, a, ln, w) in enumerate(((-4.0, -2.2, 12.0, 4.4), (1.0, -1.85, 15.0, 5.0), (6.0, -1.45, 10.0, 4.0))):
            aa = a + ht if not flip else math.pi - a - ht
            _crystal(cv, Q(u, -12.5 + abs(u) * 0.1), aa, ln * sc, w * sc, z + 0.4 + k * 0.01, g)
    return Q(17.0, 7.0)


def draw(cv, p):
    bob, lean = p['bob'], p['lean']
    up = (math.sin(lean), -math.cos(lean))
    fw = (math.cos(lean), math.sin(lean))
    HIP = (p['hx'], -HIP_H + bob)

    def T(u, f):
        return add(add(HIP, up, u), fw, f)
    SC = T(56.0, 0.0)
    sh_f = T(55.0, -5.0)
    sh_b = T(59.0, 14.0)
    br = p['breath']
    hd = p['heads']
    # v29 hext: başlara ayrı kayma ((arka), (orta), (ön)) — boyun uzar / geri çekilir (sırayla ateş eden başlar, nefes)
    he = p.get('hext', ((0.0, 0.0), (0.0, 0.0), (0.0, 0.0)))
    H = add(add(T(76.0, 14.0), (0.0, p['hy'])), he[1])          # orta baş
    H_back = add(add(T(80.0, -10.0), (0.0, p['hy'] * 0.6)), he[0])  # arka baş (yüksekte, geriye bakar)
    H_front = add(add(T(60.0, 36.0), (0.0, p['hy'] * 1.2)), he[2])  # ön baş (alçakta, öne eğik, hırlar)
    hj = p.get('hj', (p['mouth'] * 0.8, p['mouth'], min(1.0, p['mouth'] + 0.35)))   # v29: baş başına çene
    hip_f, hip_b = T(0.0, 5.0), T(0.0, -9.0)
    g = 0.5 + 0.5 * p['glow']

    # ---- post pelerin (sırttan dizlere iner, en arkada)
    cw = 0.3 * math.sin(p['ph'])
    cape = cv.blob([T(62.0, -14.0), T(66.0, 4.0), T(56.0, 2.0)]
                   + bk.ragged([T(-26.0, -6.0 + cw * 4), T(-34.0, -20.0 + cw * 6), T(-28.0, -36.0 + cw * 8), T(-10.0, -40.0 + cw * 6)], 4.0, 7, 1.0, 1.0)
                   + [T(30.0, -30.0)])
    cdet = cv.fold([T(52.0, -20.0), T(10.0, -30.0), T(-26.0, -32.0 + cw * 7)], 2.0, 1.4, 1)
    cdet += cv.fold([T(46.0, -10.0), T(0.0, -16.0), T(-28.0, -16.0 + cw * 5)], 1.6, 1.3, 1)
    cv.shape(cape, FUR_B, z=-30, sd=5.0, hi=0.3, details=cdet, fur=1.0, hatch=0.3)

    # ---- uzak kol + buz büyüsü
    eb, hb = bk.arm_fk(sh_b, p['arm_b'], p['el_b'], L_UP, L_FO)
    up_b = bk.muscle(cv, sh_b, eb, 11.0, 8.4, front=1.0, back=2.0, at=0.4, knob=0.6)
    fo_b = bk.muscle(cv, eb, hb, 8.6, 6.2, front=1.6, back=0.6, at=0.25)
    cv.shape(ik.union(up_b, fo_b), SKIN_B, z=-20, sd=3.6, bounce=0.2)
    for k in range(3):   # ön kolda buz büyümesi
        _crystal(cv, along(eb, hb, 0.3 + k * 0.2, -6.0), math.atan2(hb[1] - eb[1], hb[0] - eb[0]) + 2.2, 7.0 - k, 3.4, -19.8 + k * 0.01, g * 0.7, ICE_D)
    dhb = bk.perp(eb, hb)[1]
    if p['rock'] > 0:      # buz yükü (cast): elde kristal demeti
        rc = add(hb, dhb, 8.0)
        bk.open_hand(cv, hb, dhb, 7.6, SKIN_B, -19.85, spread=1.1, curl=0.6, near=False, claws=NAIL)
        for k in range(7):
            a = -math.pi * 0.5 + (k - 3) * 0.42
            _crystal(cv, add(rc, (0.0, 4.0)), a, (10.0 + 6.0 * (1 - abs(k - 3) / 3)) * p['rock'], 5.0 * p['rock'], -19.7 + k * 0.01, 1.0)
        cv.fill(cv.ellipse(rc, 5.0 * p['rock'], 5.0 * p['rock']), (0.75, 0.95, 1.0), z=-19.6, glow=EYE_GLOW, alpha=0.9)
    elif p['fist_b'] < 0 or p['arm_b_open'] < 0.5:
        cv.shape(cv.ellipse(add(hb, dhb, 4.0), 7.8, 7.0), SKIN_B, z=-19.6, sd=2.4,
                 details=[('ink', [add(add(hb, dhb, 6.5), (-dhb[1], dhb[0]), k * 2.5 - 2.5), add(add(hb, dhb, 10.0), (-dhb[1], dhb[0]), k * 2.5 - 2.5)], 1.0) for k in range(3)])
    else:
        bk.open_hand(cv, hb, dhb, 7.6, SKIN_B, -19.6, spread=0.8, curl=0.5, near=False, claws=NAIL)

    _leg(cv, hip_b, p['fb'], -15, False)

    # ---- gövde
    pelvis = cv.ellipse(T(4.0, 0.0), 19.0, 13.5, lean)
    belly = cv.ellipse(T(18.0, 8.0 + br * 0.5), 20.0, 18.5, lean)
    chest = cv.ellipse(T(38.0, 7.0), 26.0, 20.0, lean)
    back = cv.ellipse(T(34.0, -10.0), 15.0, 20.0, lean)
    traps = cv.blob([T(46.0, -18.0), T(58.0, -14.0), T(66.0, -2.0), T(66.0, 14.0), T(58.0, 30.0), T(46.0, 26.0)])
    torso = ik.union(pelvis, belly, chest, back, traps, cv.capsule(sh_f, sh_b, 12.5, 11.5))
    tdet = [('ink', [T(52.0, -20.0), T(42.0, -24.0), T(28.0, -21.0)], 1.4, (0.3, 0.5)),
            ('ink', [T(9.0, 4.0), T(4.0, 15.0), T(7.5, 26.0)], 1.6, (0.3, 0.4))]
    tdet += cv.fold([T(30.0, 24.0), T(25.0, 28.0), T(18.0, 30.0)], 1.0, 1.2, 1)
    # kırağı desenleri (açık, dallanan çizgiler)
    for k, (u0, f0) in enumerate(((44.0, -8.0), (30.0, 4.0), (20.0, -6.0))):
        a0 = T(u0, f0)
        tdet.append(('stroke', [a0, T(u0 - 4.0, f0 + 4.0), T(u0 - 3.0, f0 + 9.0)], 1.3, SKIN.hi, (0.2, 0.7)))
        tdet.append(('stroke', [T(u0 - 4.0, f0 + 4.0), T(u0 - 8.0, f0 + 3.0)], 1.0, SKIN.hi, (0.2, 0.8)))
    cv.shape(torso, SKIN, z=0, sd=9.0, hi=0.7, details=tdet, cast=1.4, bounce=0.45, hatch=0.5, deep=0.35)
    for k, (f0, f1, w_) in enumerate(((0.0, 16.0, 1.0), (16.5, 30.0, 0.8))):
        pec = cv.blob([T(51.0, f0 + 2.0), T(52.0, f1 - 1.0), T(46.0, f1 + 1.5), T(36.0, f1 + 0.5), T(32.0, (f0 + f1) / 2 + 1.0),
                       T(34.0, f0 + 1.5), T(42.0, f0)])
        cv.shape(pec, SKIN, z=0.4 + k * 0.01, sd=4.5 * w_, hi=0.5, cast=1.6, bounce=0.35, ol=0.8,
                 details=[('ink', [T(34.0, f0 + 2.0), T(32.0, (f0 + f1) / 2), T(35.0, f1)], 1.5, (0.2, 0.4))])
    for k in range(4):   # karın kasları
        cv.shape(cv.ellipse(T(26.0 - k * 6.0, 18.0 - k * 0.3), 4.6, 3.2, lean), SKIN, z=0.3, sd=1.6, hi=0.3, ol=0.6)
    # sırtta buz kristalleri
    for k, (u, f, a, ln) in enumerate(((60.0, -12.0, -2.4, 16.0), (52.0, -20.0, -2.7, 13.0), (44.0, -24.0, -2.95, 10.0), (64.0, -2.0, -2.1, 12.0))):
        _crystal(cv, T(u, f), a + lean, ln, 6.0, -1.0 + k * 0.01, g)

    # ---- peştamal (koyu post) + kemer
    belt = ik.isect(torso, cv.poly([T(2.0, -40), T(2.0, 40), T(10.5, 40), T(10.5, -40)]))
    skirt = cv.blob([T(6.0, -20.0), T(6.0, 22.0)] + bk.ragged([T(-22.0, 24.0), T(-27.0, 10.0), T(-25.0, -6.0), T(-19.0, -21.0)], 3.4, 6, 1.0, 2.0))
    sdet = cv.fold([T(2.0, 13.0), T(-9.0, 15.0), T(-20.0, 13.0)], 1.4, 1.3, 1) + cv.fold([T(1.0, -4.0), T(-10.0, -5.0), T(-19.0, -3.0)], 1.2, 1.2, 1)
    cv.shape(skirt, HIDE, z=3, sd=4.0, hi=0.4, fur=1.0, details=sdet, bounce=0.3)
    cv.shape(belt, LEATHER, z=3.5, sd=2.2, hi=0.35, details=[('ink', [T(6.3, -22), T(6.8, 0), T(6.0, 24)], 0.9, (0.1, 0.1))])
    _leg(cv, hip_f, p['ff'], 2.0, True)
    bc = T(6.5, 14.0)
    cv.shape(cv.ellipse(bc, 5.0, 4.2, lean), BONE, z=9, sd=1.2, hi=0.4, details=[('ink', [add(bc, (-2.5, 0)), add(bc, (2.8, 0))], 1.0)])
    _crystal(cv, add(bc, (0.0, 0.0)), math.pi * 0.5, 6.0, 3.2, 9.1, g)

    # ---- üç baş: arka (yüksekte, geriye-yukarı bakar), orta (iri), ön (alçak, hırlar)
    # boyunlar (her baş kendi kalın boynunda)
    for hh, w0, w1, zz in ((H_back, 11.0, 8.0, 5.0), (H, 12.0, 9.0, 7.0), (H_front, 11.0, 8.0, 9.0)):
        cv.shape(cv.capsule(T(56.0, (hh[0] - SC[0]) * 0.3 + 4.0), add(hh, (-3.0, 6.0)), w0, w1), SKIN if zz > 6 else SKIN_B, z=zz, sd=3.0,
                 hi=0.3, bounce=0.3, details=[('ink', [lerp(T(56.0, 4.0), hh, 0.4), lerp(T(56.0, 4.0), hh, 0.7)], 1.2, (0.3, 0.5))])
    _ice_head(cv, H_back, 0.85, 0.35 - hd[1], hj[0], p['glow'], 5.5, seed=1.0, near=False, flip=True)
    # boyun kökü post yakası (omuzları saran halka)
    collar = cv.blob(bk.ragged([T(48.0, -18.0), T(62.0, -16.0), T(70.0, 0.0), T(70.0, 18.0), T(62.0, 34.0), T(48.0, 32.0)], 3.0, 9, 1.0, 2.0)
                     + [T(46.0, 20.0), T(52.0, 6.0), T(46.0, -6.0)])
    cv.shape(collar, FUR, z=10.0, sd=4.0, hi=0.5, fur=1.0, bounce=0.35,
             details=cv.fold([T(64.0, -6.0), T(60.0, 6.0), T(62.0, 18.0)], 1.4, 1.2, 1))
    mouth = _ice_head(cv, H, 1.1, p['ht'] + hd[0], hj[1], p['glow'], 12.0, seed=0.0)
    _ice_head(cv, H_front, 0.86, 0.3 + p['ht'] * 0.6 + hd[2], hj[2], p['glow'], 16.0, seed=2.0, crown=True)

    # ---- yakın kol + mızrak
    ef, hf = bk.arm_fk(sh_f, p['arm'], p['el'], L_UP, L_FO)
    ca = p['ca']
    d = (math.cos(ca), math.sin(ca))
    arm_z = 20.0
    tip = _spear(cv, hf, ca, p['cz'] if p['cz'] < 0 else arm_z - 0.5, p['glow'])
    up_f = bk.muscle(cv, sh_f, ef, 12.5, 9.2, front=1.8, back=2.6, at=0.42, knob=0.8)
    fo_f = bk.muscle(cv, ef, hf, 9.6, 7.0, front=2.2, back=0.8, at=0.25)
    deltoid = cv.ellipse(add(sh_f, bk.perp(sh_f, ef)[1], 3.0), 14.0, 12.0, math.atan2(ef[1] - sh_f[1], ef[0] - sh_f[0]))
    adet = [('ink', [along(sh_f, ef, 0.45, -12.5), along(sh_f, ef, 0.55, -10.0), along(sh_f, ef, 0.62, -7.0)], 1.3, (0.2, 0.6)),
            ('ink', [along(ef, hf, 0.1, 9.0), along(ef, hf, 0.3, 9.5), along(ef, hf, 0.5, 7.5)], 1.2, (0.3, 0.6)),
            ('stroke', [along(sh_f, ef, 0.2, 4.0), along(sh_f, ef, 0.35, 8.0), along(sh_f, ef, 0.5, 6.0)], 1.1, SKIN.hi, (0.3, 0.6))]
    cv.shape(ik.union(deltoid, up_f, fo_f), SKIN, z=arm_z, sd=4.2, hi=0.5, details=adet, bounce=0.35, hatch=0.35, cast=1.0)
    # omuz: buz kabuğu + kristaller
    shell = cv.blob([along(sh_f, ef, -0.3, -6.0, 0.0), along(sh_f, ef, -0.26, 5.0, 0.0), along(sh_f, ef, 0.0, 12.0, 0.0), along(sh_f, ef, 0.22, 11.0, 0.0),
                     along(sh_f, ef, 0.3, 3.0, 0.0), along(sh_f, ef, 0.22, -7.0, 0.0)])
    cv.shape(shell, ICE_D, z=arm_z + 0.2, sd=2.4, hi=0.6, ol=0.95, soft=0.0,
             details=[('ink', [along(sh_f, ef, -0.1, 0.0), along(sh_f, ef, 0.2, 8.0)], 0.9, (0.2, 0.3))])
    for k, (t, o, a, ln) in enumerate(((-0.2, 4.0, -2.0, 13.0), (0.0, 9.0, -1.5, 11.0), (-0.3, -4.0, -2.5, 9.0))):
        _crystal(cv, along(sh_f, ef, t, o), a, ln, 5.0, arm_z + 0.25 + k * 0.01, g)
    wr = ik.isect(fo_f, cv.poly([along(ef, hf, 0.7, -14), along(ef, hf, 0.7, 14), along(ef, hf, 0.9, 14), along(ef, hf, 0.9, -14)]))
    cv.shape(wr, FUR, z=arm_z + 0.1, sd=1.3, hi=0.3, fur=0.8)
    bk.hand_grip(cv, hf, d, 8.6, SKIN, arm_z + 0.3, near=True)
    return {'hand': hf, 'mouth': mouth, 'spear': tip, 'head': H}


SHADE = dict(outer=0.65, rim=0.8, rim_col=(0.75, 0.92, 1.0), rim_dir=(0.6, -0.8), rim_w=1.8, form=(11.0, (0.74, 0.74, 0.9)))


def render_frame(anim, i, ss=3):
    p = CLIPS[anim]['fn'](i) if anim in CLIPS else ANIMS[anim][1](i)
    cv = bk.new_canvas(CELL, FEET, ss)
    xf = bk.body_xf(cv, p)
    info = draw(cv, p)
    if xf:
        cv.pop()
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, bk.xf_info(info, xf)


from yelbegen_v29 import CLIPS  # noqa: E402  v29 tam gövde animasyonları
