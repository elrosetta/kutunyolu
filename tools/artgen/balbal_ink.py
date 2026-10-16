"""Balbal (kimlik balbal) ve Buz Balbalı (buz_balbali) — stil v2 "mürekkep-cel". v1: creatures.draw_balbal.

Aynı pozlar (creatures.BALBAL_ANIMS: idle 2, dormant 1, hop 4, windup 2, strike 2); çapa yok (v1'de de yok).
Hücre dünya 88x80 (v1 72x72; kılıç savuruşu ve mürekkep sığsın), ayak (36, 74), doku 4.

Tasarım: Göktürk kurganlarının önüne dikilen balbal taşları, öldürülen düşmanı ya da alpın kendisini simgeler: kaba
yontulmuş granit gövde, düz oyma yüz, sarkık bıyık, sağ elde göğse tutulan kadeh, belde kemer ve kılıç. Burada
Erlik'in sesiyle uyanmış bir alp heykeli: yontu yüzeyleri (düz düzlemler, keski izleri), çatlaklar, bozkır taşlarına
özgü turuncu liken lekeleri ve yosun; Orhun runaları ve göz yarıkları uyanınca camgöbeği yanar. Uyurken (dormant)
kılıç kında, runalar sönük. Saldırı uyarısı: kılıcı başının üstüne kaldırır, gövde geriye eğilir, runalar ve
gözler parlar, kılıcın oluğundaki runa yanar; omuzdan taş tozu dökülür.

buz_balbali (Kaf): buz kabuğu tutmuş açık mavi taş, bıyıktan/kollardan sarkan buz, buzdan kılıç, ayaz mavisi runalar.
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_arm, lerp2
from creatures import BALBAL_ANIMS
import yaratik_ink_kit as yk

TEX = 4.0
CELL = (352, 320)       # dünya 88 x 80
FEET = (144, 296)       # dünya (36, 74)
ANIMS = {k: (v[0], v[1], k == 'idle', True) for k, v in BALBAL_ANIMS.items()}


def _v(**kw):
    base = dict(
        stone=Ink('#9a958a', '#4e4c5e', '#c8c2b0', '#2c2a3a', name='granit'),
        stone2=Ink('#a8a294', '#585566', '#d4cebc', '#302e40', name='kabartma'),
        stone_l=Ink('#bdb6a4', '#66626e', '#e6e0cc', '#3a3846', name='yüz düzlemi'),
        stone_d=Ink('#6e6a6c', '#38364a', '#8e8a88', '#201e2c', name='kaide'),
        lichen=(0.86, 0.52, 0.18), moss=(0.36, 0.48, 0.26),
        rune=(0.45, 1.0, 0.95), rune_hot=(0.88, 1.0, 1.0), rune_glow=(0.1, 0.85, 0.9),
        blade=Ink('#b4ae9e', '#5c5868', '#e0dacb', '#34323e', name='taş kılıç'), ice=False,
    )
    base.update(kw)
    return base


ICE = Ink('#cfeaff', '#6a98d0', '#ffffff', '#3a5c9a', name='buz')
VARIANTS = {
    'balbal': _v(),
    'buz_balbali': _v(
        stone=Ink('#9aaabb', '#4a5476', '#cad6e4', '#283050', name='donmuş taş'),
        stone2=Ink('#a6b6c6', '#52607e', '#d6e2ee', '#2c3454', name='donmuş kabartma'),
        stone_l=Ink('#c4d4e2', '#64749a', '#f0f6fc', '#36426a', name='buzlu yüz'),
        stone_d=Ink('#6e7a92', '#343c5c', '#8e9ab2', '#1c2240', name='buzlu kaide'),
        lichen=(0.92, 0.97, 1.0), moss=(0.75, 0.88, 1.0),
        rune=(0.65, 0.9, 1.0), rune_hot=(0.95, 1.0, 1.0), rune_glow=(0.3, 0.6, 1.0),
        blade=Ink('#bfe4ff', '#5a8cc8', '#ffffff', '#2c5096', name='buz kılıç'), ice=True),
}

# Orhun yazısını anımsatan damgalar (çizgi parçaları, birim kare içinde)
RUNES = [
    [((0.5, 0), (0.5, 1)), ((0.1, 0.25), (0.5, 0.5)), ((0.9, 0.25), (0.5, 0.5))],
    [((0.2, 0), (0.2, 1)), ((0.2, 0.2), (0.8, 0.5)), ((0.8, 0.5), (0.2, 0.8))],
    [((0.2, 0), (0.8, 1)), ((0.8, 0), (0.2, 1))],
    [((0.5, 0), (0.5, 1)), ((0.5, 0.3), (0.9, 0.0)), ((0.5, 0.3), (0.1, 0.0))],
    [((0.15, 0.2), (0.85, 0.2)), ((0.5, 0.2), (0.5, 1)), ((0.15, 0.7), (0.5, 1.0))],
    [((0.2, 0), (0.2, 1)), ((0.8, 0), (0.8, 1)), ((0.2, 0.5), (0.8, 0.5))],
    [((0.5, 0), (0.1, 0.5)), ((0.1, 0.5), (0.5, 1)), ((0.5, 0), (0.9, 0.5)), ((0.9, 0.5), (0.5, 1))],
]


def _rune(cv, x, y, k, V, z, awake, s=2.6, glow_k=1.0):
    for a, b in RUNES[k % len(RUNES)]:
        p0 = (x + a[0] * s * 0.7, y + a[1] * s)
        p1 = (x + b[0] * s * 0.7, y + b[1] * s)
        cv.stroke([p0, p1], 1.9, z=z, col=INK if not awake else (0.06, 0.2, 0.22), taper=(0.0, 0.0))
        if awake:
            cv.stroke([p0, p1], 1.0, z=z + 0.01, col=V['rune_hot'] if glow_k > 1 else V['rune'], taper=(0.0, 0.0), glow=V['rune_glow'])
    if awake:
        yk.glow_soft(cv, (x + s * 0.35, y + s * 0.5), s * (0.6 + 0.25 * glow_k), V['rune_glow'], z=z + 0.02, blur=0.6, alpha=0.12 + 0.12 * (glow_k - 1))


def _lichen(V, cv, pts, seed, r=1.0):
    """Liken / yosun lekeleri (shape details): düzensiz benek kümeleri."""
    rng = np.random.default_rng(seed)
    out = []
    for (x, y) in pts:
        for k in range(4):
            q = (x + rng.uniform(-1.2, 1.2) * r, y + rng.uniform(-0.8, 0.8) * r)
            rr = rng.uniform(0.35, 0.8) * r
            out.append(('col', cv.ellipse(q, rr, rr * 0.8, rng.uniform(0, 3)), V['lichen'] if k % 3 else V['moss']))
    return out


def draw(cv, p, V):
    sq = p.get('squash', 0.0)
    awake = p.get('awake', 1.0) > 0.5
    flare = p.get('flare', 0.0)
    sx, sy, dy = 1 + sq * 0.12, 1 - sq * 0.14, p.get('bob', 0.0)
    cv.push(lambda q: (q[0] * sx, q[1] * sy + dy))
    lean = p.get('lean', 0.0)
    L = lambda x, y, *t: (x + lean * (-y) * 0.12, y) + tuple(t)
    S, S2, SL, SD = V['stone'], V['stone2'], V['stone_l'], V['stone_d']
    gk = 1.0 + flare
    # ---- kaide: kaba yontulmuş blok
    base = cv.blob([(-12.5, 0.4, 0.0), (12.5, 0.4, 0.0), (11.5, -5.0), (6.0, -6.4, 0.0), (-4.0, -6.6), (-11.5, -5.5, 0.0)])
    bdet = [('ink', [(-12, -2.0), (-4, -1.4), (3, -2.2), (12, -1.6)], 1.0, (0.2, 0.2)),
            ('ink', [(5.5, -6.0), (6.5, -3.0), (5.8, 0.0)], 1.2), ('ink', [(-6.0, -6.2), (-6.8, -3.4)], 1.0)]
    bdet += _lichen(V, cv, [(-9.0, -4.8), (9.0, -1.2)], 3, 1.0)
    cv.shape(base, SD, z=-2, sd=2.2, hi=0.5, details=bdet, hatch=0.4)
    for i in range(3):
        _rune(cv, -8.0 + i * 6, -4.6, i + 2, V, 40, awake, s=2.4, glow_k=gk)
    # ---- arka saç örgüsü (taş)
    braid = [L(-5.5, -41), L(-7.0, -36), L(-7.8, -30)]
    cv.shape(ik.taper_path([cv.W(q) for q in braid], cv.u(3.2), (0.0, 0.5)), S2, z=-3, sd=1.0,
             details=[('ink', [along_(braid[0], braid[2], t, -1.2), along_(braid[0], braid[2], t + 0.08, 1.2)], 0.9, (0.1, 0.1)) for t in (0.2, 0.4, 0.6, 0.8)])
    # ---- gövde: kaftanlı taş blok (yontu düzlemleri)
    body = cv.blob([L(-9.5, -6), L(9.8, -6, ), L(10.2, -13), L(9.0, -27), L(5, -30.8), L(-5.5, -30.8), L(-9.2, -27.5), L(-10.2, -13)])
    det = []
    # ışık yanında düz yontu düzlemi (açık), gölge yanında ikinci düzlem
    det.append(('hi', cv.blob([L(-9.2, -27), L(-5.0, -30.2), L(-2.0, -29), L(-4.0, -16), L(-8.8, -14)])))
    det.append(('ink', [L(-2.0, -29), L(-4.0, -16), L(-3.4, -8)], 1.0, (0.2, 0.4)))
    det.append(('shade', cv.blob([L(6.5, -28), L(9.2, -26), L(10.2, -13), L(9.8, -6.5), L(6.5, -7), L(7.2, -18)])))
    # kaftan: yaka (çapraz), etek kenarı, çatlak
    det += [('ink', [L(1.0, -30.2), L(2.0, -24), L(2.6, -15)], 1.5, (0.1, 0.3)),
            ('ink', [L(-9.6, -7.6), L(0, -7.2), L(9.6, -7.6)], 1.3, (0.1, 0.1)),
            ('ink', [L(-3.0, -29), L(-3.8, -26), L(-2.6, -23.5), L(-3.6, -21)], 1.1, (0.0, 0.6))]
    # keski izleri: kısa paralel çizgiler
    for k in range(6):
        x0 = -7.5 + k * 2.6
        y0 = -11.5 - (k % 3) * 0.8
        det.append(('ink', [L(x0, y0), L(x0 + 1.2, y0 - 0.8)], 0.8, (0.3, 0.3)))
    det += _lichen(V, cv, [L(-8.4, -24), L(7.4, -8.5), L(-6.0, -9.0)], 7, 1.0)
    cv.shape(body, S, z=0, sd=4.0, hi=0.6, details=det, hatch=0.5, bounce=0.3)
    _rune(cv, *L(-8.2, -26.5), 0, V, 40, awake, s=2.6, glow_k=gk)
    _rune(cv, *L(-8.2, -21.5), 1, V, 40, awake, s=2.6, glow_k=gk)
    # ---- kemer: toka, plakalar, sarkan kese
    belt = ik.union(cv.capsule(L(-9.8, -14.6), L(9.8, -14.6), 1.4, 1.4))
    cv.shape(belt, SD, z=9, sd=0.8, hi=0.35, details=[('col', cv.ellipse(L(-6 + k * 3.2, -14.6), 0.7, 0.9), S2.base) for k in range(5)])
    cv.shape(cv.blob([L(2.3, -16.2), L(4.7, -16.2), L(4.9, -13.0), L(2.1, -13.0)]), SL, z=14, sd=0.5, hi=0.3, ol=0.8)
    cv.shape(cv.blob([L(-6.3, -13.6), L(-3.3, -13.6), L(-3.6, -9.6), L(-4.8, -9.0, 0.0), L(-6.0, -9.8)]), S2, z=12, sd=0.9, hi=0.3,
             details=[('ink', [L(-6.0, -12.6), L(-3.6, -12.6)], 0.9)])
    sword = p.get('sword', 1.0 if awake else 0.0)
    if sword < 0.5:   # kında kılıç
        cv.shape(cv.capsule(L(7.5, -14), L(1.5, -1.5), 1.6, 1.1), SD, z=13, sd=0.8, hi=0.3,
                 details=[('ink', [L(6.0, -11), L(4.6, -8)], 0.9)])
        cv.shape(cv.capsule(L(6.3, -16.2), L(9.7, -12.8), 0.95, 0.95), S2, z=14, sd=0.5, hi=0.3)
    # ---- arka kol: kadehi göğüste tutar
    shb = L(-5.5, -27.5)
    arm_b = cv.limb([shb, L(-5.7, -20), L(1.5, -21.6)], [2.8, 2.4, 2.1])
    cv.shape(arm_b, S2, z=10, sd=1.6, hi=0.4, details=[('ink', [L(-6.0, -24), L(-4.2, -22.6)], 0.9)])
    cup = cv.blob([L(-0.6, -28.0), L(6.2, -28.0), L(5.0, -23.0), L(3.4, -22.6), L(2.0, -22.6), L(0.8, -23.0)])
    cv.shape(cup, SL, z=18, sd=1.0, hi=0.45, details=[('deep', cv.ellipse(L(2.8, -27.6), 3.0, 0.6)),
                                                        ('ink', [L(0.2, -26.0), L(2.8, -25.4), L(5.6, -26.0)], 0.8)])
    cv.shape(cv.capsule(L(2.8, -23.0), L(2.8, -21.0), 0.8, 1.0), SL, z=18.1, sd=0.4, ol=0.8)
    cv.shape(cv.blob([L(0.0, -22.0), L(2.4, -22.8), L(3.2, -20.6), L(1.0, -19.8)]), S2, z=18.2, sd=0.5, hi=0.25, ol=0.8,
             details=[('ink', [L(1.0, -21.6), L(2.6, -21.0)], 0.7)])
    if awake and flare > 0:
        yk.glow_soft(cv, L(2.8, -27.6), 3.0, V['rune_glow'], z=18.3, alpha=0.35 * flare)
    # ---- baş: yuvarlak yüz, alçak börk, sarkık bıyık
    hc = L(1.5, -38.5)
    hx, hy = hc
    cv.shape(cv.capsule(L(0.5, -31), L(1.2, -33.5), 3.2, 3.0), S, z=1, sd=1.0)
    head = cv.blob([(hx - 6.6, hy - 2.0), (hx - 5.4, hy - 6.8), (hx + 1.0, hy - 8.4), (hx + 6.4, hy - 5.8), (hx + 7.2, hy + 1.0),
                    (hx + 5.4, hy + 6.6), (hx + 0.6, hy + 8.0), (hx - 4.6, hy + 6.0), (hx - 6.8, hy + 2.4)])
    hdet = [('ink', [(hx + 4.6, hy - 4.6), (hx + 3.6, hy - 3.0), (hx + 4.4, hy - 1.6)], 1.0, (0.0, 0.6))]
    hdet += _lichen(V, cv, [(hx - 4.5, hy + 3.0)], 13, 0.8)
    cv.shape(head, S, z=2, sd=2.4, hi=0.5, details=hdet, hatch=0.3)
    # börk
    cap = cv.blob([(hx - 7.4, hy - 3.2), (hx + 7.0, hy - 3.4), (hx + 5.6, hy - 8.8), (hx + 0.5, hy - 10.8), (hx - 5.6, hy - 9.4)])
    cv.shape(cap, S2, z=10, sd=1.6, hi=0.5, details=[('ink', [(hx - 4.0, hy - 9.0), (hx - 2.6, hy - 6.2), (hx - 3.0, hy - 3.6)], 1.0),
                                                       ('ink', [(hx + 2.4, hy - 10.2), (hx + 3.2, hy - 7.0), (hx + 3.0, hy - 3.8)], 1.0)] +
             _lichen(V, cv, [(hx - 2.0, hy - 8.6)], 17, 0.9))
    cv.shape(cv.capsule((hx - 7.5, hy - 3.5), (hx + 7.1, hy - 3.6), 1.15, 1.15), SD, z=13, sd=0.5, hi=0.3)
    # yüz düzlemi + kaş, gözler, burun, sarkık bıyık, sakal
    face = cv.blob([(hx + 0.2, hy - 2.4), (hx + 6.6, hy - 2.6), (hx + 7.0, hy + 3.0), (hx + 5.0, hy + 6.4), (hx + 1.0, hy + 5.0), (hx - 0.6, hy + 1.0)])
    cv.shape(face, SL, z=16, sd=1.2, hi=0.3, flat=False, ol=0.7)
    cv.stroke([(hx + 0.2, hy - 1.8), (hx + 3.2, hy - 2.2), (hx + 6.8, hy - 1.6)], 1.8, z=20, col=INK, taper=(0.2, 0.2))
    er = 0.55 + 0.2 * flare
    for ex_ in (1.9, 5.2):
        cv.fill(cv.ellipse((hx + ex_, hy - 0.5), 1.0, 0.45, 0.0), INK, z=21)
        if awake:
            yk.eye_glow(cv, (hx + ex_, hy - 0.5), 0.8, 0.28 * (1 + flare * 0.5), 0.0, V['rune_hot'], V['rune_glow'], 22, halo=1.6 + flare, halo_a=0.25 + 0.2 * flare)
    cv.stroke([(hx + 3.7, hy - 0.2), (hx + 4.1, hy + 1.6), (hx + 3.5, hy + 2.0)], 1.1, z=22, col=INK)
    must = cv.blob([(hx + 3.6, hy + 2.3), (hx + 1.2, hy + 2.8), (hx + 0.2, hy + 5.0), (hx + 0.4, hy + 6.6, 0.0), (hx + 1.0, hy + 4.4),
                    (hx + 3.6, hy + 3.3), (hx + 6.4, hy + 4.4), (hx + 7.0, hy + 6.6, 0.0), (hx + 7.0, hy + 4.8), (hx + 6.0, hy + 2.8)])
    cv.shape(must, S2, z=24, sd=0.9, hi=0.3, details=[('ink', [(hx + 1.4, hy + 3.4), (hx + 0.8, hy + 5.0)], 0.7)])
    cv.stroke([(hx + 2.6, hy + 4.4), (hx + 3.7, hy + 4.7), (hx + 4.8, hy + 4.4)], 1.0, z=24.1, col=INK)
    if V['ice']:
        yk.icicles(cv, [(hx + 0.6, hy + 6.3), (hx + 6.9, hy + 6.3), (hx - 4.0, hy + 6.0), (hx + 3.5, hy + 7.2)], ICE, 24.5, L=2.6, w=0.6, seed=2)
        yk.icicles(cv, [(hx - 6.0, hy - 3.0), (hx + 6.4, hy - 3.2)], ICE, 13.5, L=2.4, w=0.7, seed=3)
    # ---- ön kol + kılıç
    sa = p.get('arm', (0.15, 0.6))
    shf = L(6.5, -27.5)
    e, h = fk_arm(shf, sa[0], sa[1], 7.0, 6.5)
    if sword >= 0.5:
        ang = p.get('swang', sa[0] + sa[1])
        dx, dy_ = math.sin(ang), math.cos(ang)
        tip = (h[0] + dx * 18.5, h[1] + dy_ * 18.5)
        pom = (h[0] - dx * 3.2, h[1] - dy_ * 3.2)
        nx, ny = -dy_, dx
        cv.shape(cv.capsule(pom, h, 1.0, 0.95), SD, z=25, sd=0.5, hi=0.3)
        bl0 = (h[0] + dx * 2.0, h[1] + dy_ * 2.0)
        blade = cv.blob([(bl0[0] + nx * 2.2, bl0[1] + ny * 2.2), (h[0] + dx * 10.0 + nx * 2.6, h[1] + dy_ * 10.0 + ny * 2.6), (h[0] + dx * 15.5 + nx * 2.0, h[1] + dy_ * 15.5 + ny * 2.0),
                         (tip[0] + nx * 0.6, tip[1] + ny * 0.6, 0.0), (h[0] + dx * 15.5 - nx * 1.0, h[1] + dy_ * 15.5 - ny * 1.0), (bl0[0] - nx * 1.8, bl0[1] - ny * 1.8)])
        bdet = [('ink', [(h[0] + dx * 4 + nx * 0.2, h[1] + dy_ * 4 + ny * 0.2), (h[0] + dx * 14 + nx * 0.2, h[1] + dy_ * 14 + ny * 0.2)], 1.6, (0.1, 0.3))]
        bdet += [('ink', [(h[0] + dx * (6 + k * 3.5) - nx * 1.1, h[1] + dy_ * (6 + k * 3.5) - ny * 1.1),
                          (h[0] + dx * (6.8 + k * 3.5) - nx * 0.4, h[1] + dy_ * (6.8 + k * 3.5) - ny * 0.4)], 0.8) for k in range(3)]
        cv.shape(blade, V['blade'], z=27, sd=1.0, hi=0.45, details=bdet, glow=None)
        if awake:   # oluktaki runa ışığı
            gl = [(h[0] + dx * 4.5 + nx * 0.2, h[1] + dy_ * 4.5 + ny * 0.2), (h[0] + dx * 13.5 + nx * 0.2, h[1] + dy_ * 13.5 + ny * 0.2)]
            cv.stroke(gl, 0.8 + 0.5 * flare, z=27.2, col=V['rune_hot'], taper=(0.2, 0.3), glow=V['rune_glow'])
            if flare > 0:
                yk.glow_soft(cv, lerp2(h, tip, 0.55), 5.0, V['rune_glow'], z=27.3, blur=0.6, alpha=0.4 * flare, ry=3.0)
        cv.shape(cv.capsule((h[0] - nx * 3.4, h[1] - ny * 3.4), (h[0] + nx * 3.4, h[1] + ny * 3.4), 1.05, 1.05), SD, z=29, sd=0.5, hi=0.3)
        if V['ice']:
            yk.icicles(cv, [(h[0] - nx * 3.0, h[1] - ny * 3.0 + 0.6), (h[0] + nx * 3.0, h[1] + ny * 3.0 + 0.6)], ICE, 29.2, L=2.0, w=0.5, seed=5)
    arm = cv.limb([shf, lerp2(shf, e, 0.5), e, h], [3.0, 3.1, 2.6, 2.3])
    cv.shape(arm, S2, z=26, sd=1.8, hi=0.45, details=[('ink', [lerp2(shf, e, 0.85), lerp2(e, h, 0.15)], 1.0)])
    fist = cv.ellipse(h, 2.5, 2.4)
    cv.shape(fist, S2, z=28, sd=1.0, hi=0.35, details=[('ink', [(h[0] - 1.6, h[1] - 0.4), (h[0] + 1.4, h[1] - 0.6)], 0.8)])
    pad = cv.ellipse((shf[0] - 0.4, shf[1] - 0.6), 3.4, 2.2, -0.2)
    cv.shape(pad, SD, z=30, sd=1.0, hi=0.35, details=_lichen(V, cv, [(shf[0] - 1.0, shf[1] - 1.2)], 21, 0.7))
    if V['ice']:
        yk.icicles(cv, [(shf[0] - 2.5, shf[1] + 1.2), (shf[0] + 0.5, shf[1] + 1.6), lerp2(e, h, 0.4)], ICE, 30.5, L=3.0, w=0.7, seed=6)
    if flare > 0:   # omuzdan dökülen taş tozu (hazırlık)
        rng = np.random.default_rng(3)
        for k in range(6):
            q = (shf[0] + rng.uniform(-4, 2), shf[1] + rng.uniform(1, 9))
            r = rng.uniform(0.3, 0.6)
            cv.fill(cv.ellipse(q, r, r), S.shadow, z=31)
    cv.pop()
    return {}


def along_(a, b, t, off=0.0):
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1.0
    return (a[0] + dx * t - dy / d * off, a[1] + dy * t + dx / d * off)


def _pose(anim, i):
    n, fn, loop, arm = ANIMS[anim]
    p = dict(fn(i / n))
    if anim == 'windup':
        p['flare'] = 0.6 + 0.4 * i
    if anim == 'strike':
        p['flare'] = 0.5 - 0.3 * i
    return p


SHADE = dict(outer=0.55, rim=0.7, rim_col=(0.7, 0.8, 1.0), rim_dir=(0.6, -0.8), rim_w=1.4, form=(5.0, (0.76, 0.74, 0.88)))


def render_frame(anim, i, var='balbal', ss=3):
    V = VARIANTS[var]
    p = _pose(anim, i)
    cv = yk.occlude_glow(ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss))
    info = draw(cv, p, V)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
