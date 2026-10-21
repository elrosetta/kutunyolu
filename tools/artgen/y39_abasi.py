"""v39: Abası (kimlik abasi; Altay / Sibirya Türklerinin tek gözlü, demir dişli iblisi; Kaf dağları, yapay zekâ
"chainer", ağır) — mürekkep-cel tam gövde.

Kambur, kaba tüylü iblis: keçeleşmiş koyu toprak / kara postu kırağı ve buz sarkıtlarıyla kabuklanmış; derin göz
çukurunda TEK soluk mavi göz yanar; kocaman ağzında DEMİR dişler (metal parıltısı); maymunsu uzun kollar, iri eller,
kara pençeler; kısa çarpık bacaklar; bileklerde demir kelepçe. Yakın ön koluna sarılı ağır demir zincirin ucunda
iri, çengelli bir kanca.

Hücre 384x352 doku pikseli = dünya 96 x 88 (doku 4), ayak (26, 84). Gövde 32 x 60.
Satırlar: idle 8, move 8 (yumruk üstünde ağır yürüyüş, vx 60), hurt 3,
  atk_hook 10 (kancayı baş üstünde zincirle döndürür -> dümdüz ileri fırlatır: zincir hücrenin el verdiği kadar uzar,
  kanca ucunda; etkin karelerde gergin tutar, sonra geri sarar), atk_slam 9 (şahlanır, iki yumruk yukarıda -> çift
  yumrukla yere: buz kıymıkları, kırağı patlaması), atk_swing 8 (zinciri toplar -> çevresinde geniş yatay yay
  çizerek savurur: önde ve arkada hilal izi).
Çapa 'hand' = kanca her karede (atk_hook etkin karelerinde uzaktaki kanca).
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import lerp2
import bosskit as bk
import yaratik_govde as yg
import yaratik_ink_kit as yk
import ucan_v29 as u29
from ucan_v29 import pose_at

TEX = 4.0
CELL = (384, 352)       # dünya 96 x 88 (şahlanışta yumruklar için üstte, kanca atışı için önde pay)
FEET = (104, 336)       # dünya (26, 84)

FUR = Ink('#4e3a2e', '#221618', '#7c6a66', '#120a0c', kind='fur', name='keçe post')
FUR_B = FUR.darker(0.72)
SKIN = Ink('#5c5a6c', '#2a2838', '#8a8aa0', '#16141e', name='kara deri')
SKIN_B = SKIN.darker(0.75)
FROST = (0.80, 0.90, 0.98)
ICE = Ink('#c8e4f4', '#6a8cb4', '#ffffff', '#3a5478', name='buz')
IRON = Ink('#767c8a', '#343844', '#d0d8e6', '#1c1e28', kind='metal', name='demir')
IRON_T = Ink('#8a909e', '#3a3e4a', '#eef2fa', '#1e2028', kind='metal', name='demir diş')
CLAW = Ink('#26222a', '#0e0c10', '#5a5662', name='kara pençe')
MOUTH_IN = (0.24, 0.05, 0.08)
EYE = (0.52, 0.84, 1.0)
EYE_HOT = (0.97, 1.0, 1.0)
EYE_GLOW = (0.35, 0.7, 1.0)
SMEAR = (0.85, 0.93, 1.0)


def add(p, v, k=1.0):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


def polar(p, a, r):
    return (p[0] + math.cos(a) * r, p[1] + math.sin(a) * r)


HIP = (-3.0, -21.0)
SH_N = (9.0, -45.0)
SH_F = (2.0, -47.0)
L1, L2 = 14.0, 14.5

REST = dict(hx=0.0, hy=0.0, bob=0.0, lean=0.0, sx=1.0, sy=1.0, breath=0.0,
            ff=(5.0, 0.0), fb=(-8.0, 0.0),
            hn=(24.0, 0.0), hf=(16.0, 0.0), fist=1.0,              # el hedefleri (dünya); fist 1 = yumruk, 0 = açık pençe
            hk=(30.0, -2.0), sag=4.0, hz=25.0, ha=None, hook_on=1.0,  # kanca (dünya), zincir sarkması, z
            ht=0.0, jaw=0.25, brow=0.0, glow=0.6, lid=0.0,
            smear=0.0, sm=(0.0, 0.0), ring=0.0, burst=0.0, shard=0.0, jit=(0.0, 0.0), spin=0.0)


def _xf(p):
    c, s = math.cos(p['lean']), math.sin(p['lean'])
    off = (p['hx'] + p['jit'][0], p['hy'] + p['bob'] + p['jit'][1])

    def f(q):
        x = (q[0] - HIP[0]) * p['sx']
        y = (q[1] - HIP[1]) * p['sy']
        return (HIP[0] + off[0] + x * c - y * s, HIP[1] + off[1] + x * s + y * c)

    def inv(q):
        x, y = q[0] - HIP[0] - off[0], q[1] - HIP[1] - off[1]
        x, y = x * c + y * s, -x * s + y * c
        return (HIP[0] + x / p['sx'], HIP[1] + y / p['sy'])
    return f, inv


# ------------------------------------------------------------ parçalar
def _leg(cv, hip, foot, z, near):
    m = FUR if near else FUR_B
    ank = (foot[0], foot[1] - 2.4)
    knee, ank = yg.ik2(hip, ank, 9.0, 8.5, -1)
    knee = (knee[0] + 1.5, knee[1])                         # çarpık (yay) bacak
    thigh = bk.muscle(cv, hip, knee, 5.6, 4.2, front=1.2, back=1.0, at=0.4, knob=0.6)
    shin = bk.muscle(cv, knee, ank, 4.0, 3.0, front=0.3, back=1.4, at=0.3)
    cv.shape(ik.union(thigh, shin), m, z=z, sd=2.0, hi=0.3 if near else 0.0, fur=1.2)
    f = (ank[0], ank[1] + 2.4)
    sk = SKIN if near else SKIN_B
    cv.shape(cv.blob([(f[0] - 4.0, f[1] - 3.2), (f[0] + 1.0, f[1] - 4.0), (f[0] + 5.5, f[1] - 2.2), (f[0] + 7.0, f[1] - 0.2), (f[0] + 6.5, f[1] + 0.4, 0.0),
                      (f[0] - 4.2, f[1] + 0.4, 0.0), (f[0] - 5.0, f[1] - 1.5)]), sk, z=z + 0.2, sd=1.4, hi=0.25 if near else 0.0)
    for k in range(3):   # ayak pençeleri
        b = (f[0] + 4.2 + k * 1.2, f[1] - 1.2 + k * 0.3)
        cv.shape(cv.blob(bk.spike_pts((b[0] - 0.6, b[1] - 0.6), (b[0] + 0.6, b[1] + 0.4), (b[0] + 2.4, b[1] + 0.6), 0.3)), CLAW, z=z + 0.3, sd=0.3, ol=0.6)
    # bilekte demir kelepçe
    cv.shape(cv.capsule(lerp2(knee, ank, 0.8), lerp2(knee, ank, 0.92), 3.3, 3.2), IRON if near else IRON.darker(0.75), z=z + 0.25, sd=0.8, hi=0.3, ol=0.9)
    # dizde sarkan buz
    if near:
        yk.icicles(cv, [(knee[0] - 3.0, knee[1] + 3.0), (knee[0] - 1.2, knee[1] + 3.6)], ICE, z + 0.4, L=2.2, w=0.6, seed=4)


def _hand(cv, w, ang, m, z, fist, near):
    """İri el: yumrukta parmaklar içe kıvrık (pençeler yere), açıkken uzun kara pençeler yayılır."""
    pc = polar(w, ang, 2.4)
    cv.shape(cv.ellipse(pc, 3.8, 3.2, ang), m, z=z, sd=1.3, hi=0.3 if near else 0.0, ol=1.0,
             details=[('ink', [polar(pc, ang + 2.2, 1.6), polar(polar(pc, ang + 2.2, 1.6), ang, 2.4)], 0.9, (0.2, 0.6))])
    tips = []
    for k in range(4):
        a = ang + (k - 1.5) * (0.32 if fist > 0.5 else 0.42)
        b = polar(pc, a, 3.0)
        if fist > 0.5:     # kıvrık: pençe uçları aşağı / geriye
            mid = polar(b, a + 1.2, 1.4)
            tip = polar(mid, a + 2.2, 2.0)
        else:
            mid = polar(b, a, 2.4)
            tip = polar(mid, a + 0.45, 2.8)
        cv.shape(cv.limb([b, mid], [1.15, 1.0]), m, z=z + 0.1 + k * 0.01, sd=0.4, ol=0.8)
        cv.shape(cv.blob(bk.spike_pts(polar(mid, a + 1.57, 0.85), polar(mid, a - 1.57, 0.85), tip, 0.3)), CLAW, z=z + 0.15 + k * 0.01, sd=0.3, hi=0.2, ol=0.7)
        tips.append(tip)
    return tips


def _arm(cv, sh, tgt, z, near, fist, chain=False):
    e, h = yg.ik2(sh, tgt, L1, L2, +1)
    m = FUR if near else FUR_B
    up = bk.muscle(cv, sh, e, 5.4, 4.2, front=1.4, back=1.0, at=0.35, knob=0.5)
    fo = bk.muscle(cv, e, h, 4.4, 3.4, front=1.6, back=0.6, at=0.3)
    cv.shape(ik.union(up, fo), m, z=z, sd=2.2, hi=0.35 if near else 0.0, fur=1.3, bounce=0.25 if near else 0.0)
    # buz sarkıtları: kolun alt yanında
    if near:
        nrm = (h[1] - e[1], -(h[0] - e[0]))
        L = math.hypot(*nrm) or 1.0
        nrm = (nrm[0] / L, nrm[1] / L)
        if nrm[1] < 0:
            nrm = (-nrm[0], -nrm[1])
        pts = [add(lerp2(e, h, t), nrm, 3.4) for t in (0.2, 0.42, 0.6)]
        yk.icicles(cv, pts, ICE, z + 0.3, L=3.2, w=0.75, seed=7)
    ang = math.atan2(h[1] - e[1], h[0] - e[0])
    # demir kelepçe
    cv.shape(cv.capsule(lerp2(e, h, 0.82), lerp2(e, h, 0.98), 4.0, 3.8), IRON if near else IRON.darker(0.72), z=z + 0.2, sd=0.9, hi=0.35, ol=0.9,
             details=[('col', cv.ellipse(lerp2(e, h, 0.9), 0.6, 0.6), IRON.hi)])
    if chain:   # ön kola sarılı zincir: çapraz halkalar
        d = (math.cos(ang), math.sin(ang))
        n = (-d[1], d[0])
        for k in range(3):
            c = lerp2(e, h, 0.25 + k * 0.17)
            yk.chain_links(cv, add(c, n, -4.6), add(add(c, n, 4.6), d, 2.2), 3, IRON, z + 0.25 + k * 0.05, r=1.0)
    _hand(cv, h, ang, SKIN if near else SKIN_B, z + 0.5, fist, near)
    return e, h


HK = 1.45   # kanca ölçeği


def _hook(cv, c, ang, z, glint=0.0):
    """İri çengelli kanca: halka + kalın şaft + kıvrık çengel ve dikenli uç (c = kanca merkezi, ang = şaft yönü)."""
    d = (math.cos(ang), math.sin(ang))
    n = (-d[1], d[0])

    def P(t, o):
        t, o = t * HK, o * HK
        return (c[0] + d[0] * t + n[0] * o, c[1] + d[1] * t + n[1] * o)
    cv.shape(ik.diff(cv.ellipse(P(-4.8, 0), 1.9 * HK, 1.9 * HK), cv.ellipse(P(-4.8, 0), 0.9 * HK, 0.9 * HK)), IRON, z=z, sd=0.5, hi=0.3, ol=0.8)
    shaft = cv.capsule(P(-3.2, 0), P(3.0, 0), 1.1 * HK, 1.3 * HK)
    # çengel: şaftın ucundan geriye kıvrılan yay
    arc = [P(3.0 + 2.8 * math.sin(a), 3.0 * (1 - math.cos(a))) for a in np.linspace(0, math.pi * 0.95, 8)]
    bend = ik.taper_path([cv.W(q) for q in arc], cv.u(2.6 * HK), prof=lambda u: max(0.35, 1.0 - 0.6 * u))
    tip = P(-1.8, 6.4)
    barb = cv.blob(bk.spike_pts(arc[-1], P(0.6, 6.2), tip, 0.2))
    barb2 = cv.blob(bk.spike_pts(P(-0.4, 4.6), P(0.8, 5.6), P(-0.8, 3.0), 0.0))
    spike = cv.blob(bk.spike_pts(P(2.4, -1.0), P(3.4, -1.0), P(5.4, -2.8), 0.0))
    cv.shape(ik.union(shaft, bend, barb, barb2, spike), IRON, z=z + 0.05, sd=0.9, hi=0.4, ol=1.0)
    if glint > 0:
        yk.glow_soft(cv, P(4.2, 2.8), 2.6, EYE_GLOW, z=z + 0.1, alpha=0.4 * glint)
        cv.stroke([P(3.6, 1.2), P(5.2, 3.2)], 1.0, z=z + 0.12, col=(1, 1, 1), taper=(0.3, 0.3))


def _chain(cv, a, b, sag, z):
    """a -> b ağır zincir (sarkmalı): ara noktalar parabol, her parçada halka dizisi."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(2, int(L / 9) + 1)
    pts = []
    for i in range(n + 1):
        t = i / n
        q = lerp2(a, b, t)
        pts.append((q[0], q[1] + sag * 4 * t * (1 - t)))
    for i in range(n):
        seg = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        yk.chain_links(cv, pts[i], pts[i + 1], max(1, int(round(seg / 2.3))), IRON, z + i * 0.03, r=1.05, ol=0.7)
    return pts


def _ell_smear(cv, c, rx, ry, a0, a1, z, alpha=0.7, w=5.0):
    """Yatay savuruş izi: c çevresinde elips yayı (a0 -> a1), sona doğru kalınlaşan hilal."""
    n = 16
    out, inn = [], []
    for i in range(n + 1):
        u = i / n
        a = a0 + (a1 - a0) * u
        ww = w * (u ** 1.2)
        out.append((c[0] + math.cos(a) * rx, c[1] + math.sin(a) * ry))
        inn.append((c[0] + math.cos(a) * (rx - ww), c[1] + math.sin(a) * (ry - ww * ry / rx)))
    yk.wash(cv, cv.blob(out + inn[::-1]), SMEAR, alpha, z=z, glow=(0.2, 0.4, 0.7), glow_a=0.25 * alpha)
    cv.stroke(out[3:], 1.3, z=z + 0.01, col=INK, taper=(0.9, 0.1), alpha=0.75)


def _frost_fx(cv, p, c):
    """Çift yumruk vuruşu: yerden fışkıran buz kıymıkları, kırağı topakları, soğuk ışıma."""
    k = p['burst']
    if k > 0:
        yk.glow_soft(cv, (c[0], c[1] - 4), 10 + 12 * k, EYE_GLOW, z=-30, alpha=0.55 * (1.2 - k))
        for i in range(6):
            s = -1 if i % 2 else 1
            x = c[0] + s * (3 + i * 2.8) * (0.5 + k)
            r = (3.4 + (i % 3)) * (0.6 + 0.6 * k) * (1.0 - 0.07 * i)
            yk.puff(cv, (x, -r * 0.7 - k * i * 0.4), r, Ink('#d6e8f4', '#7c9ac0', '#ffffff'), z=(41 if i % 3 == 0 else -28) + i * 0.01, seed=i + 11)
        ring = [(c[0] + math.cos(t) * (8 + 22 * k), -0.6 + math.sin(t) * (8 + 22 * k) * 0.2) for t in np.linspace(0.1, math.pi - 0.1, 9)]
        cv.stroke(ring, 3.0 * (1.15 - k), z=40, col=ICE.hi, taper=(0.6, 0.6), alpha=0.85 * (1.1 - k), glow=(0.3, 0.55, 0.9))
    sh = p['shard']
    if sh > 0:
        rng = np.random.default_rng(21)
        for i in range(9):
            a = -math.pi / 2 + (i - 4) * 0.3 + rng.uniform(-0.1, 0.1)
            L = (5 + rng.uniform(3, 9) * (1.0 - abs(i - 4) * 0.1)) * sh
            b = (c[0] + (i - 4) * 2.2, 0.6)
            tip = polar(b, a, L)
            w = 1.2 + 0.4 * (i % 2)
            cv.shape(cv.blob([(b[0] - w, b[1]), polar(lerp2(b, tip, 0.5), a + 1.57, w * 0.7), (tip[0], tip[1], 0.0), polar(lerp2(b, tip, 0.5), a - 1.57, w * 0.7),
                              (b[0] + w, b[1])]), ICE, z=(35 if i % 2 else -26) + i * 0.01, sd=0.6, hi=0.5, ol=0.85, glow=(0.12, 0.25, 0.45))
        # savrulan buz kırıntıları
        u29.flecks(cv, (c[0], -10 * sh), 10, 4 + 6 * sh, 10 + 12 * sh, ICE.hi, 43, seed=5, s0=0.4, s1=0.9, glow=(0.2, 0.4, 0.7))


def draw(cv, p, ph):
    T, Ti = _xf(p)
    if p['burst'] > 0 or p['shard'] > 0:
        _frost_fx(cv, p, (p['hn'][0] * 0.5 + p['hf'][0] * 0.5 + 2, 0.0))
    for side, foot in ((-1, p['fb']), (1, p['ff'])):
        hp = T((HIP[0] + side * 3.0, HIP[1] + 1.0))
        _leg(cv, hp, (foot[0] + p['hx'], foot[1] + p['hy']), -12 if side < 0 else -6, side > 0)
    hz = p['hz']
    u29.body_xf(cv, HIP, p['lean'], p['sx'], p['sy'], (p['hx'] + p['jit'][0], p['hy'] + p['bob'] + p['jit'][1]))
    # uzak kol
    _arm(cv, SH_F, Ti(p['hf']), -20, False, p['fist'])
    br = p['breath']
    # ---- gövde: kambur, keçeleşmiş post (sırtta kabarık tutamlar)
    top = [(14.0, -35.0), (14.5 + br * 0.4, -42.0), (12.0, -49.0)]
    back = (yk.ragged((12.0, -49.0), (3.0, -56.0 - br * 0.6), 3, 2.4, seed=1) + [(3.0, -56.0 - br * 0.6)] +
            yk.ragged((3.0, -56.0 - br * 0.6), (-8.0, -52.0), 3, 2.6, seed=2) + [(-8.0, -52.0)] +
            yk.ragged((-8.0, -52.0), (-14.0, -36.0), 4, 2.6, seed=3) + [(-14.0, -36.0)] +
            yk.ragged((-14.0, -36.0), (-11.0, -21.0), 3, 2.2, seed=4) + [(-11.0, -21.0)] +
            yk.ragged((-11.0, -21.0), (-2.0, -16.0), 3, 2.0, seed=5) + [(-2.0, -16.0)] +
            yk.ragged((-2.0, -16.0), (9.0, -22.0 + br * 0.4), 3, 2.6, seed=6) + [(9.0, -22.0)])
    body = cv.blob(top + back + [(13.0, -28.0)])
    det = [('ink', [(5.0, -50.0), (0.0, -44.0), (-3.0, -36.0)], 1.0, (0.3, 0.6)),
           ('ink', [(-8.0, -44.0), (-9.0, -36.0), (-7.5, -28.0)], 1.0, (0.3, 0.6)),
           ('ink', [(6.0, -30.0), (2.0, -24.0)], 0.9, (0.3, 0.6)),
           ('col', cv.blob([(10.0, -50.0), (3.0, -56.5), (-8.0, -52.5), (-5.0, -50.5), (2.0, -53.0), (8.0, -48.0)]), FROST),          # kırağı yükü
           ('col', cv.blob([(-9.0, -50.5), (-13.5, -38.0), (-12.0, -38.5), (-8.5, -47.0)]), FROST)]
    for k in range(7):   # sırtta kırağılı tutam uçları
        q = (-10.0 + k * 3.0, -53.0 + abs(k - 4) * 0.9)
        det.append(('stroke', [q, (q[0] - 1.0, q[1] + 2.2)], 1.0, (0.9, 0.96, 1.0), (0.1, 0.9)))
    cv.shape(body, FUR, z=0, sd=3.6, hi=0.5, details=det, hatch=0.35, bounce=0.3, cast=0.8, fur=1.4)
    # karın altından sarkan buz
    yk.icicles(cv, [(-8.0, -18.5), (-4.0, -16.6), (1.0, -17.0), (6.0, -20.5)], ICE, 1.0, L=3.6, w=0.8, seed=2)
    # ---- baş (omuzların arasına gömük, önde ve alçakta)
    _head(cv, p, ph)
    # ---- yakın kol (zincir sarılı)
    e, h = _arm(cv, SH_N, Ti(p['hn']), 20, True, p['fist'], chain=True)
    hw = u29.to_world(cv, h)
    mouth = u29.to_world(cv, (22.0, -37.0))
    cv.pop()
    # ---- zincir + kanca (dünyada)
    anc = hw
    if p['hook_on'] > 0.5:
        hk = p['hk']
        pts = _chain(cv, hw, hk, p['sag'], hz - 1.0)
        ha = p['ha'] if p['ha'] is not None else math.atan2(hk[1] - pts[-2][1], hk[0] - pts[-2][0])
        _hook(cv, polar(hk, ha, 4.8 * HK), ha, hz, glint=p['glow'])
        anc = polar(hk, ha, 4.8 * HK)
    if p['smear'] > 0:
        a0, a1 = p['sm']
        c = T((4.0, -34.0))
        # arka yarı (gövdenin arkasında) ve ön yarı ayrı z
        _ell_smear(cv, c, 34.0, 9.0, a0, min(a1, math.pi * 2.0), -40, alpha=0.6 * p['smear'], w=6.0)
    if p['ring'] > 0:   # kanca döndürme izi (baş üstünde elips)
        c = (hw[0] + 1.0, hw[1] - 6.0)
        _ell_smear(cv, c, 15.0, 5.0, p['spin'] - 3.6, p['spin'], hz - 2.0, alpha=0.55 * p['ring'], w=3.0)
    return {'hand': anc, 'mouth': mouth}


def _head(cv, p, ph):
    ht = p['ht']
    hc = (18.0, -41.0)
    piv = (12.0, -42.0)
    ca_, sa_ = math.cos(ht), math.sin(ht)

    def Q(u, v, *t):
        x, y = hc[0] + u - piv[0], hc[1] + v - piv[1]
        return (piv[0] + x * ca_ - y * sa_, piv[1] + x * sa_ + y * ca_) + tuple(t)
    jaw = p['jaw']
    ja = jaw * 0.55

    def J(u, v, *t):   # alt çene menteşesi (-4, 2)
        uu, vv = u + 4.0, v - 2.0
        return Q(-4.0 + uu * math.cos(ja) - vv * math.sin(ja), 2.0 + uu * math.sin(ja) + vv * math.cos(ja), *t)
    # ağız içi
    cv.fill(cv.blob([Q(-2, 1.5), Q(10.5, 1.8), J(10, 3.2), J(2, 4.0), J(-3, 3.0)]), MOUTH_IN, z=9.0)
    # alt çene (kalın, geniş) + DEMİR alt dişler
    lower = cv.blob([J(-6, 0.5), J(3, 2.6), J(11.5, 2.6), J(12.5, 5.5), J(8, 8.0), J(0, 8.2), J(-5, 6.0)])
    cv.shape(lower, SKIN, z=9.1, sd=1.6, hi=0.25, details=[('ink', [J(2, 6.6), J(8, 6.4)], 0.9, (0.3, 0.5))])
    for k in range(5):
        u = -0.5 + k * 2.6
        ln = 2.6 if k % 2 == 0 else 2.0
        cv.shape(cv.blob([J(u - 1.1, 3.2), J(u + 1.1, 3.2), J(u + 0.8, 3.2 - ln * 0.7), J(u, 3.2 - ln, 0.0), J(u - 0.8, 3.2 - ln * 0.7)]), IRON_T,
                 z=9.3 + k * 0.01, sd=0.4, hi=0.3, ol=0.75)
    # kafa: keçeleşmiş yele ile birleşen alçak kafatası, öne çıkık ağız
    skull = cv.blob([Q(-8, 2), Q(-9, -5), Q(-6, -9.5), Q(0, -11.0), Q(6, -9.5), Q(10.5, -6.0), Q(12.0, -2.5), Q(12.4, 1.0), Q(10.5, 2.2),
                     Q(2, 2.0), Q(-4, 3.5)])
    det = [('deep', cv.ellipse(Q(3.6, -4.2), 3.6, 3.2, ht)),                      # DERİN göz çukuru
           ('ink', [Q(9.5, -2.0), Q(11.4, 0.6)], 1.1, (0.3, 0.3)),
           ('ink', [Q(-3.5, -1.0), Q(-1.0, 1.4)], 0.9, (0.3, 0.3))]
    cv.shape(skull, SKIN, z=9.5, sd=2.4, hi=0.4, details=det, cast=1.0, bounce=0.3)
    # yele: başın üstünde ve arkasında kırağılı keçe
    mane = cv.blob([Q(-11, 4)] + yk.ragged(Q(-11, 4), Q(-8, -11), 3, 2.0, seed=8, side=1.0) + [Q(-8, -11)] +
                   yk.ragged(Q(-8, -11), Q(5, -12.5), 3, 1.8, seed=9, side=1.0) + [Q(5, -12.5), Q(8.5, -9.5), Q(4.0, -9.0), Q(-2, -8.5), Q(-6.0, -3.0), Q(-6.0, 3.5)])
    cv.shape(mane, FUR, z=9.6, sd=1.8, hi=0.4, fur=1.2,
             details=[('col', cv.blob([Q(-8, -10.5), Q(4, -12.4), Q(2, -10.5), Q(-6, -9.5)]), FROST)])
    # kaş çıkıntısı
    br = p['brow']
    cv.shape(cv.blob([Q(-0.5, -7.2 + br * 0.3), Q(4.0, -9.0 + br * 1.0), Q(8.6, -7.0 + br * 1.6), Q(8.0, -5.6 + br * 1.4), Q(4.0, -7.0 + br * 1.0), Q(0.0, -5.8)]),
             SKIN, z=9.9, sd=0.8, hi=0.35, cast=0.8)
    # TEK GÖZ: soluk mavi, çukurun dibinde
    ec = Q(4.2, -4.0)
    rr = 1.9 * (1.0 - 0.8 * p['lid'])
    g = 0.5 + 0.6 * p['glow']
    yk.glow_soft(cv, ec, 5.5 + 3.0 * p['glow'], EYE_GLOW, z=9.95, alpha=0.6 * g)
    cv.fill(cv.ellipse(ec, 2.0, rr, ht), EYE, z=10.0, glow=tuple(c * g for c in EYE_GLOW))
    cv.fill(cv.ellipse(add(ec, (-0.4, -0.3)), 1.0, rr * 0.55, ht), EYE_HOT, z=10.05, glow=EYE_HOT)
    cv.fill(cv.ellipse(add(ec, (0.5, 0.1)), 0.45, rr * 0.75, ht), (0.05, 0.08, 0.15), z=10.06)
    # üst DEMİR dişler: iri, düzensiz, metal parıltılı
    for k in range(5):
        u = 0.0 + k * 2.4
        ln = 3.0 if k % 2 == 0 else 2.3
        cv.shape(cv.blob([Q(u - 1.15, 1.6), Q(u + 1.15, 1.6), Q(u + 0.8, 1.6 + ln * 0.7), Q(u + 0.1, 1.6 + ln, 0.0), Q(u - 0.8, 1.6 + ln * 0.7)]), IRON_T,
                 z=10.1 + k * 0.01, sd=0.4, hi=0.35, ol=0.75)
    cv.fill(cv.ellipse(Q(11.8, -1.6), 0.8, 0.5, ht + 0.4), INK, z=10.2)   # burun deliği


# ------------------------------------------------------------ animasyon tabloları
S2 = math.tau


def _k(t, keys):
    return pose_at(t, keys, base=REST)


def _idle(t):
    s = math.sin(S2 * t)
    sw = math.sin(S2 * t + 0.6)
    blink = 1.0 if int(round(t * 8)) == 6 else 0.0
    return dict(REST, bob=0.8 + 0.8 * s, breath=0.5 + 0.5 * s, sy=1.0 - 0.015 * s, lean=0.02 * s, hn=(24.0, 0.0), hf=(16.0, 0.0),
                hk=(31.0 + 0.8 * sw, -1.0), sag=3.5, jaw=0.25 + 0.15 * max(0, s), ht=0.04 * s, glow=0.55 + 0.3 * s, lid=0.9 * blink)


def _move(t):
    """Yumruk üstünde ağır yürüyüş: kollar destek (çapraz eşli), gövde iki kol arasında öne salınır; zincir sürüklenir."""
    S = 10.0

    def cyc(phv, home, lift):
        phv %= 1.0
        st = 0.55
        if phv < st:
            return (home + S - 2 * S * phv / st, 0.0)
        u = (phv - st) / (1 - st)
        e = u * u * (3 - 2 * u)
        return (home - S + 2 * S * e, -math.sin(math.pi * u) * lift)
    hn, hf = cyc(t, 24.0, 6.0), cyc(t + 0.5, 17.0, 5.0)
    ff, fb = cyc(t + 0.5, 5.0, 3.5), cyc(t, -8.0, 3.5)
    w = math.cos(4 * math.pi * (t - 0.1))
    sw = math.cos(S2 * t)
    return dict(REST, bob=1.2 + 1.4 * w, lean=0.06 + 0.04 * sw, hn=hn, hf=hf, ff=ff, fb=fb, hk=(hn[0] - 2.0 - 5.0 * (1 + sw), -1.0), sag=2.0,
                ha=None, jaw=0.35, ht=0.05 * sw, glow=0.7, breath=0.5 + 0.4 * w, sy=1.0 - 0.02 * w)


_HURT = [(0.0, dict(lean=-0.25, hx=-2.5, bob=1.0, ht=-0.25, jaw=0.8, lid=0.6, brow=-0.5, hn=(18.0, -10.0), hf=(10.0, -6.0), fist=0.0, hk=(22.0, -2.0),
                    jit=(-1.2, 0.0), glow=0.3), 'l'),
         (0.5, dict(lean=-0.15, hx=-3.5, ht=-0.12, jaw=0.6, lid=0.3, hn=(20.0, -4.0), hf=(12.0, -2.0), jit=(-0.6, 0.0)), 'o'),
         (1.0, dict(lean=-0.02, hx=-3.0, bob=0.5, ht=0.0, jaw=0.3, lid=0.0, brow=0.0, hn=(23.0, 0.0), hf=(15.0, 0.0), fist=1.0, hk=(29.0, -1.0),
                    jit=(0.0, 0.0), glow=0.6), 'io')]

# atk_hook: zinciri baş üstünde döndür -> dümdüz ileri fırlat (gergin) -> geri sar
_SPIN_C = (6.0, -72.0)


def _spin(a, r=13.0):
    return (_SPIN_C[0] + math.cos(a) * r, _SPIN_C[1] + math.sin(a) * r * 0.32)


_HOOK_TS = [0.0, 0.1, 0.2, 0.3, 0.38, 0.42, 0.55, 0.68, 0.8, 0.9]
_HOOK = [
    (0.0, dict(), 'l'),
    (0.1, dict(lean=-0.12, bob=-1.0, hn=(8.0, -66.0), fist=1.0, hk=_spin(0.6), sag=1.5, hz=25, jaw=0.5, brow=0.6, glow=0.8, ring=0.8, spin=0.6, ht=-0.1), 'o'),
    (0.2, dict(lean=-0.18, bob=-1.5, hn=(6.0, -68.0), hk=_spin(3.4), hz=-25, ring=1.0, spin=3.4, jaw=0.6, brow=1.0, glow=1.0), 'l'),
    # derin kurulma (W): kol geride, kanca arkada en uzakta, gövde burulmuş
    (0.3, dict(lean=-0.3, bob=-1.0, hx=-2.0, hn=(-4.0, -60.0), hf=(18.0, -26.0), hk=(-12.0, -64.0), sag=0.5, hz=-25, ring=1.0, spin=3.4 + 2.6, jaw=0.8,
               ff=(7.0, 0.0), fb=(-10.0, 0.0)), 'o'),
    # fırlayış: kol öne savrulur, kanca uçuşta
    (0.38, dict(lean=0.15, bob=1.0, hx=1.0, hn=(28.0, -52.0), hf=(10.0, -20.0), hk=(44.0, -54.0), sag=0.0, hz=25, ring=0.0, jaw=1.0, ht=0.08), 'i'),
    # TEMAS (C): zincir dümdüz ileri gerili, kanca en uçta
    (0.42, dict(lean=0.28, bob=2.0, hx=2.0, hn=(31.0, -49.0), hf=(8.0, -14.0), hk=(50.0, -48.0), sag=0.0, ha=0.0, jaw=1.0, brow=1.0, glow=1.0, ht=0.12), 'o'),
    (0.55, dict(lean=0.26, bob=2.0, hn=(31.0, -48.0), hk=(50.0, -47.0), sag=0.4, jaw=0.8), 'l'),
    # geri sarma: kanca çekilir, zincir gevşer
    (0.68, dict(lean=0.0, bob=1.0, hx=0.0, hn=(20.0, -34.0), hf=(14.0, -8.0), hk=(42.0, -24.0), sag=5.0, ha=math.pi, jaw=0.5, brow=0.5, glow=0.8), 'io'),
    (0.8, dict(hn=(24.0, -8.0), hf=(16.0, 0.0), hk=(30.0, -12.0), sag=5.0, ha=None, jaw=0.35, brow=0.2), 'io'),
    (1.0, dict(lean=0.0, bob=0.0, hn=(24.0, 0.0), hf=(16.0, 0.0), hk=(30.0, -2.0), sag=4.0, jaw=0.25, brow=0.0, ht=0.0, glow=0.6, ff=(5.0, 0.0),
               fb=(-8.0, 0.0)), 'io')]

# atk_slam: şahlan, iki yumruk yukarıda -> çift yumrukla yere, buz patlaması
_SLAM_TS = [0.0, 0.1, 0.2, 0.32, 0.42, 0.48, 0.6, 0.75, 0.88]
_SLAM = [
    (0.0, dict(), 'l'),
    (0.1, dict(lean=-0.2, bob=-1.0, hn=(20.0, -40.0), hf=(14.0, -38.0), hk=(22.0, -24.0), sag=4.0, jaw=0.5, brow=0.6, glow=0.8, ht=-0.1), 'o'),
    (0.2, dict(lean=-0.45, bob=-2.5, hx=-2.0, hn=(10.0, -64.0), hf=(4.0, -64.0), hk=(4.0, -48.0), sag=6.0, jaw=0.8, brow=1.0, glow=1.0, ht=-0.2,
               ff=(7.0, 0.0), fb=(-10.0, 0.0)), 'o'),
    # derin kurulma (W): dimdik şahlanmış, yumruklar en tepede
    (0.32, dict(lean=-0.58, bob=-3.0, hx=-3.0, hn=(4.0, -69.0), hf=(-2.0, -68.0), hk=(-2.0, -52.0), sag=6.0, jaw=1.0, ht=-0.28, sy=1.04, sx=0.97), 'o'),
    (0.42, dict(lean=0.2, bob=1.0, hx=1.0, hn=(30.0, -30.0), hf=(26.0, -32.0), hk=(18.0, -44.0), sag=2.0, jaw=1.0, ht=0.0, sy=1.0, sx=1.0,
                smear=0.0), 'i'),
    # TEMAS (C): iki yumruk yere çakılı, gövde öne çöker; buz kıymıkları
    (0.48, dict(lean=0.45, bob=5.0, hx=2.0, hn=(31.0, 0.0), hf=(26.0, 0.0), hk=(22.0, -4.0), sag=2.0, jaw=1.0, ht=0.2, sy=0.92, sx=1.06, burst=0.25,
                shard=0.6, jit=(0.5, 0.0)), 'i'),
    (0.6, dict(bob=5.5, lean=0.46, burst=0.6, shard=1.0, jaw=0.8, sy=0.94, sx=1.05, jit=(0.0, 0.0)), 'o'),
    (0.75, dict(bob=3.5, lean=0.3, burst=0.95, shard=0.8, hn=(29.0, 0.0), hf=(22.0, 0.0), jaw=0.5, brow=0.5, sy=0.98, sx=1.02), 'o'),
    (1.0, dict(lean=0.0, bob=0.0, hx=0.0, hn=(24.0, 0.0), hf=(16.0, 0.0), hk=(30.0, -2.0), sag=4.0, jaw=0.25, brow=0.0, ht=0.0, burst=0.0, shard=0.0,
               sy=1.0, sx=1.0, ff=(5.0, 0.0), fb=(-8.0, 0.0)), 'io')]

# atk_swing: zinciri topla -> çevresinde geniş yatay yayla savur (önde ve arkada hilal)
_SWING_TS = [0.0, 0.12, 0.26, 0.36, 0.42, 0.54, 0.72, 0.86]
_SWING = [
    (0.0, dict(), 'l'),
    (0.12, dict(lean=-0.1, hx=-1.0, hn=(10.0, -30.0), hf=(12.0, -14.0), hk=(4.0, -22.0), sag=3.0, hz=25, jaw=0.5, brow=0.6, glow=0.8), 'o'),
    # derin kurulma (W): gövde geriye burulur, kanca arkada yere yakın
    (0.26, dict(lean=-0.2, hx=-3.0, bob=1.5, hn=(-6.0, -30.0), hf=(14.0, -20.0), hk=(-22.0, -20.0), sag=2.0, hz=-25, jaw=0.8, brow=1.0, glow=1.0,
                ff=(7.0, 0.0), fb=(-11.0, 0.0), sx=0.94), 'o'),
    (0.36, dict(lean=0.0, hx=0.0, bob=2.0, hn=(22.0, -34.0), hk=(18.0, -26.0), sag=0.0, hz=25, jaw=1.0, smear=0.8, sm=(math.pi * 0.95, math.pi * 1.9),
                sx=1.0), 'i'),
    # TEMAS (C): kanca önde en uzakta, zincir gergin; önde-arkada savuruş hilali
    (0.42, dict(lean=0.15, hx=1.5, bob=2.5, hn=(28.0, -46.0), hf=(6.0, -22.0), hk=(48.0, -40.0), sag=0.0, ha=0.0, hz=25, jaw=1.0, brow=1.0,
                smear=1.0, sm=(math.pi * 0.7, math.pi * 2.05), ht=0.1, jit=(0.5, 0.0)), 'o'),
    # aşma: kanca arkaya döner (gövdenin arkasından)
    (0.54, dict(lean=-0.05, hx=0.5, hn=(12.0, -36.0), hf=(10.0, -18.0), hk=(-18.0, -36.0), sag=0.5, ha=math.pi, hz=-25, smear=0.8,
                sm=(math.pi * 0.0, math.pi * 1.0), jaw=0.8, jit=(0.0, 0.0)), 'o'),
    (0.72, dict(lean=0.0, hn=(20.0, -10.0), hf=(15.0, -2.0), hk=(8.0, -6.0), sag=4.0, ha=None, hz=25, smear=0.0, jaw=0.5, brow=0.3, glow=0.7), 'io'),
    (1.0, dict(lean=0.0, hx=0.0, bob=0.0, hn=(24.0, 0.0), hf=(16.0, 0.0), hk=(30.0, -2.0), sag=4.0, jaw=0.25, brow=0.0, ht=0.0, glow=0.6,
               ff=(5.0, 0.0), fb=(-8.0, 0.0)), 'io')]


def _row(frames, fps, loop, pose, ts=None, mk=None, vx=None):
    d = dict(frames=frames, fps=fps, loop=loop, pose=pose, ts=ts, mk=mk)
    if vx:
        d['vx'] = vx
    return d


def _nl(keys):
    return lambda t: _k(t, keys)


ROWS = None


def anims_for(var='abasi'):
    global ROWS
    if ROWS is None:
        ROWS = {
            'idle': _row(8, 7, True, _idle),
            'move': _row(8, 12, True, _move, vx=60.0),
            'hurt': _row(3, 12, False, _nl(_HURT)),
            'atk_hook': _row(10, 10, False, _nl(_HOOK), ts=_HOOK_TS, mk=[0.3, 0.42, 0.68]),
            'atk_slam': _row(9, 10, False, _nl(_SLAM), ts=_SLAM_TS, mk=[0.32, 0.48, 0.62]),
            'atk_swing': _row(8, 10, False, _nl(_SWING), ts=_SWING_TS, mk=[0.26, 0.42, 0.6]),
        }
    return ROWS


def durum_for(var='abasi'):
    d = {"idle": "idle", "chase": "move", "recover": "idle", "evade": "move", "_hurt": "hurt", "_hurt_big": "hurt", "_break": "hurt"}
    for m in ('hook', 'slam', 'swing'):
        for ph in ('windup', 'act', 'recover'):
            d[ph + '/' + m] = 'atk_' + m
    d['hold/hook'] = 'atk_hook'
    return d


def frame_time(row, i):
    if row['ts']:
        return row['ts'][i]
    if row['loop']:
        return i / row['frames']
    return i / max(1, row['frames'] - 1)


SHADE = dict(outer=0.55, rim=0.75, rim_col=(0.7, 0.85, 1.0), rim_dir=(0.6, -0.8), rim_w=1.5, form=(5.0, (0.76, 0.76, 0.9)))


def render_frame(anim, i, var='abasi', ss=3):
    row = anims_for(var)[anim]
    tt = frame_time(row, i)
    p = dict(row['pose'](tt))
    ph = tt * math.tau * (2 if row['loop'] else 1) + i * 0.9
    cv = yg.bake_xf(u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss))
    info = draw(cv, p, ph)
    rgba, _nm, em = cv.finish(**SHADE)
    return rgba, None, em, info
