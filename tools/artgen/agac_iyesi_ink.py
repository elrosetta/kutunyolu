"""Kara İye (kimlik agac_iyesi) ve biyom çeşitlemeleri — stil v2 "mürekkep-cel". v1: creatures.draw_iye.

Aynı iskelet ve pozlar (creatures.IYE_ANIMS: idle 4, walk 6, windup 2, slam 2, hurt 1) ve 'hand' çapası (ön yumruk;
yer vuruşu oradan çıkar). Hücre dünya 128x112 (v1 112x104; boynuz ve kalkan kol sığsın), ayak (60, 106), doku 4.

Tasarım: Türk inancında "iye" bir yerin, ağacın, suyun koruyucu ruhudur. Kara İye kutsal bir dilek ağacının iyesiydi:
geyik kafatası başı, dallanan boynuzlarında hâlâ insanların bağladığı dilek çaputları sallanır. Erlik'in kara kökleri
göğsünü yarınca mor yanan çatlaklar açıldı. Kök bacaklar, kambur kütük gövde, sırtında yosun örtüsü ve mantarlar,
diz boyu uzun kollar ve kök pençeli yumruklar. Saldırı uyarısı: yumruğunu başının üstüne kaldırır, çene açılır
(kükreme), çatlaklar ve göz çukuru alevlenir.

Çeşitlemeler (VARIANTS; `<kimlik>_v2`):
  agac_iyesi  Kara İye     (Ötüken)   kara kabuk, yosun, geyik kafatası, Erlik moru
  tozkoparan  Tozkoparan   (Bozkır)   ağarmış kuru dağ ağacı (saksağul), sırtta kuru bozkır otu, koç boynuzlu kafatası,
                                      bacak ve kolları saran toz hortumu, kehribar çatlaklar
  su_iyesi    Su İyesi     (Şahmeran) ıslak kara-yeşil sürüklenmiş kütük, sarkan su yosunu, damlalar, camgöbeği çatlaklar
  dev_cocugu  Dev Çocuğu   (Kaf)      buz mavisi kaya beden, sırtta kar örtüsü, buz kristali boynuzlar, iri kaya kafa
  od_iyesi    Od İyesi     (Tamu)     kömürleşmiş kabuk, lav çatlakları, kül ve kor, yanık boynuz, omuzlarda alev dilleri
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_arm, lerp2
from creatures import IYE_ANIMS
import yaratik_ink_kit as yk

TEX = 4.0
CELL = (512, 448)       # dünya 128 x 112
FEET = (240, 424)       # dünya (60, 106)
ANIMS = {k: (v[0], v[1], k in ('idle', 'walk'), True) for k, v in IYE_ANIMS.items()}

BONE = Ink('#e6dcc0', '#8c7c68', '#fffbe8', '#5a4a40', name='kemik')


def _v(**kw):
    base = dict(
        bark=Ink('#6a4e3c', '#2e1e22', '#94725a', '#1a1016', name='kara kabuk'),
        bark_b=Ink('#4c3830', '#22161a', '#6a5040', '#120a0e', name='arka kabuk'),
        groove=(0.16, 0.1, 0.1),
        back=Ink('#5f7c3a', '#2a3c22', '#8eaa52', '#162214', kind='fur', name='yosun'),
        back_kind='moss',
        horn=BONE, horn_kind='antler', head='deer', skull=BONE,
        crack=(0.82, 0.45, 1.0), crack_hot=(0.97, 0.85, 1.0), crack_glow=(0.62, 0.2, 1.0),
        eye=(0.95, 0.75, 1.0), caput=((0.86, 0.2, 0.2), (0.94, 0.9, 0.78), (0.24, 0.55, 0.72), (0.9, 0.72, 0.2)),
        shroom=Ink('#c8743a', '#6a2c22', '#f0b070', name='mantar'),
        extra=(),
    )
    base.update(kw)
    return base


VARIANTS = {
    'agac_iyesi': _v(),
    'tozkoparan': _v(
        bark=Ink('#ab9474', '#5e4a44', '#d8c49c', '#33262a', name='ağarmış saksağul'),
        bark_b=Ink('#857058', '#463634', '#a48c6c', '#2a1e20', name='arka kuru dal'),
        groove=(0.3, 0.2, 0.16),
        back=Ink('#c9a54e', '#6c5028', '#ecd282', '#3a2a16', kind='fur', name='kuru bozkır otu'),
        back_kind='grass', horn=Ink('#d8ccae', '#7e6e5c', '#fff8e0', '#4a3c34', name='koç boynuzu'),
        horn_kind='ram', crack=(1.0, 0.7, 0.25), crack_hot=(1.0, 0.95, 0.7), crack_glow=(1.0, 0.5, 0.05),
        eye=(1.0, 0.85, 0.5), caput=((0.75, 0.2, 0.16), (0.94, 0.86, 0.7), (0.2, 0.42, 0.62)), extra=('dust',)),
    'su_iyesi': _v(
        bark=Ink('#2f5552', '#132a32', '#4e8478', '#0a161e', name='ıslak kütük'),
        bark_b=Ink('#24403f', '#0f1e26', '#386258', '#060e14', name='arka kütük'),
        groove=(0.04, 0.1, 0.12),
        back=Ink('#3a8a6a', '#174438', '#6cc49a', '#0a2620', kind='fur', name='su yosunu'),
        back_kind='weed', horn=Ink('#cfe2d8', '#5e7c86', '#ffffff', '#34505a', name='sedef boynuz'),
        crack=(0.35, 1.0, 0.9), crack_hot=(0.85, 1.0, 1.0), crack_glow=(0.1, 0.85, 0.85),
        eye=(0.8, 1.0, 1.0), shroom=Ink('#6fa0b0', '#2c4c64', '#b6e0e8', name='midye'),
        caput=((0.3, 0.6, 0.62), (0.85, 0.92, 0.9), (0.3, 0.6, 0.62)), extra=('drips',)),
    'dev_cocugu': _v(
        bark=Ink('#7c8aa2', '#38405e', '#b0bed4', '#1e2238', name='ayaz kayası'),
        bark_b=Ink('#5c6882', '#2a3048', '#808ca6', '#161a2c', name='arka kaya'),
        groove=(0.12, 0.13, 0.24),
        back=Ink('#eef4fb', '#8a9ac0', '#ffffff', '#56648c', kind='fur', name='kar örtüsü'),
        back_kind='snow', horn=Ink('#bfe6ff', '#4e86c4', '#ffffff', '#2a4e86', name='buz kristali'),
        horn_kind='crystal', head='stone', skull=Ink('#9aa8be', '#46506c', '#d0dcec', '#262c44', name='kaya baş'),
        crack=(0.6, 0.9, 1.0), crack_hot=(0.92, 1.0, 1.0), crack_glow=(0.25, 0.65, 1.0),
        eye=(0.85, 0.98, 1.0), caput=(), extra=('ice',)),
    'od_iyesi': _v(
        bark=Ink('#3e3036', '#18101a', '#62505a', '#0c070c', name='kömür kabuk'),
        bark_b=Ink('#2c2228', '#120c12', '#443840', '#08050a', name='arka kömür'),
        groove=(0.05, 0.02, 0.03),
        back=Ink('#5a5458', '#262226', '#8a8286', '#141014', kind='fur', name='kül'),
        back_kind='ash', horn=Ink('#3a3034', '#160e12', '#6a5a5a', '#0a0608', name='yanık boynuz'),
        horn_kind='antler', skull=Ink('#c8b8a4', '#6a5650', '#efe2cc', '#3a2a28', name='isli kemik'),
        crack=(1.0, 0.55, 0.12), crack_hot=(1.0, 0.92, 0.55), crack_glow=(1.0, 0.38, 0.02),
        eye=(1.0, 0.9, 0.5), caput=(), shroom=Ink('#3a3034', '#160e12', '#6a5a5a', name='kor'),
        extra=('flames', 'embers')),
}


def along(a, b, t, off=0.0):
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1.0
    return (a[0] + dx * t - dy / d * off, a[1] + dy * t + dx / d * off)


def _grooves(a, b, r, n, seed, w=1.3, V=None, t0=0.05, t1=0.95):
    """Kabuk oluğu: uzuv boyunca dalgalı mürekkep çizgileri + yanında açık ton (kabuk sırtı)."""
    rng = np.random.default_rng(seed)
    det = []
    for k in range(n):
        off = (k + 0.5) / n * 2 - 1
        off = off * r * 0.78 + rng.uniform(-0.3, 0.3)
        s0 = t0 + rng.uniform(0, 0.15)
        s1 = t1 - rng.uniform(0, 0.2)
        pts = [along(a, b, s0 + (s1 - s0) * u, off + math.sin(u * 5 + seed + k) * 0.5) for u in (0, 0.33, 0.66, 1.0)]
        det.append(('ink', pts, w * rng.uniform(0.8, 1.15), (0.3, 0.4)))
        if V is not None and k % 2 == 0:
            det.append(('stroke', [(q[0] - 0.55, q[1] - 0.4) for q in pts[1:3]], w * 0.9, V['bark'].hi, (0.4, 0.4)))
    return det


def _crack(cv, pts, V, z, w=1.6, hot=True):
    """Erlik çatlağı: mürekkep yarık + içinde yanan öz (ışıma)."""
    cv.stroke(pts, w + 1.3, z=z, col=INK, taper=(0.25, 0.25))
    cv.stroke(pts, w, z=z + 0.01, col=V['crack'], taper=(0.3, 0.3), glow=V['crack_glow'])
    if hot:
        cv.stroke(pts[1:-1] if len(pts) > 3 else pts, w * 0.45, z=z + 0.02, col=V['crack_hot'], taper=(0.3, 0.3), glow=V['crack_hot'])


def _roots(cv, foot, mat, z, side, seed):
    rng = np.random.default_rng(seed)
    out = []
    for k, dx in enumerate((-6.5, -2.5, 3.5, 7.5)):
        s = (foot[0] + dx * 0.25, foot[1] - 1.0)
        e = (foot[0] + dx + rng.uniform(-0.6, 0.6), 0.6)
        m = (lerp2(s, e, 0.5)[0], lerp2(s, e, 0.5)[1] - 0.8)
        out.append(ik.taper_path([cv.W(s), cv.W(m), cv.W(e)], cv.u(3.2 - abs(dx) * 0.12), (0.0, 0.9)))
    return ik.union(*out)


def _antler(cv, base, a0, L, mat, z, r0=1.8, curve=0.28, n=4, tines=(1, 2, 3), tine_len=0.42, seed=0, kind='antler', V=None):
    """Dallanan boynuz (tek kontur): ana gövde + öne-yukarı çatallar. kind 'crystal' = buz kristali kümesi."""
    rng = np.random.default_rng(seed)
    if kind == 'crystal':
        parts = []
        for k in range(4):
            a = a0 + (k - 1.5) * 0.32 + rng.uniform(-0.08, 0.08)
            ln = L * (0.45 + 0.35 * rng.random())
            w = r0 * (1.2 + 0.6 * rng.random())
            tip = (base[0] + math.cos(a) * ln, base[1] + math.sin(a) * ln)
            nx, ny = -math.sin(a) * w, math.cos(a) * w
            parts.append(cv.blob([(base[0] + nx, base[1] + ny, 0.0), (base[0] + nx + math.cos(a) * ln * 0.7, base[1] + ny + math.sin(a) * ln * 0.7, 0.0),
                                  (tip[0], tip[1], 0.0), (base[0] - nx + math.cos(a) * ln * 0.7, base[1] - ny + math.sin(a) * ln * 0.7, 0.0),
                                  (base[0] - nx, base[1] - ny, 0.0)]))
            cv.shape(parts[-1], mat, z=z + k * 0.02, sd=w * 0.9, hi=0.5, ol=0.85,
                     details=[('stroke', [lerp2(base, tip, 0.15), lerp2(base, tip, 0.8)], 1.0, (1, 1, 1), (0.2, 0.6))],
                     glow=None)
            yk.glow_soft(cv, lerp2(base, tip, 0.6), w * 1.5, V['crack_glow'], z=z, blur=0.6, alpha=0.18)
        return
    pts = [base]
    x, y = base
    seg = L / n
    for i in range(n):
        a = a0 + curve * i
        x += math.cos(a) * seg
        y += math.sin(a) * seg
        pts.append((x, y))
    paths = [ik.taper_path([cv.W(q) for q in pts], cv.u(r0 * 2), prof=lambda u: max(0.18, 1.0 - 0.75 * u))]
    tips = [pts[-1]]
    for i in tines:
        if i < len(pts) - 1:
            a = a0 + curve * i + 0.95
            q = pts[i]
            tl = L * tine_len * (1 - i * 0.12)
            mid = (q[0] + math.cos(a) * tl * 0.5, q[1] + math.sin(a) * tl * 0.5)
            tip = (mid[0] + math.cos(a - 0.4) * tl * 0.5, mid[1] + math.sin(a - 0.4) * tl * 0.5)
            paths.append(ik.taper_path([cv.W(q), cv.W(mid), cv.W(tip)], cv.u(r0 * 1.3 * (1 - i / n * 0.5)), prof=lambda u: max(0.15, 1.0 - 0.85 * u)))
            tips.append(tip)
    det = [('ink', [lerp2(pts[0], pts[1], 0.3), lerp2(pts[1], pts[2], 0.4)], 0.9, (0.3, 0.6))]
    cv.shape(ik.union(*paths), mat, z=z, sd=r0 * 0.8, hi=0.35, details=det, ol=0.9)
    if V is not None and 'embers' in V['extra']:
        for k, tp in enumerate(tips):
            cv.fill(cv.ellipse(tp, 0.7, 0.7), V['crack_hot'], z=z + 0.1, glow=V['crack_glow'])
    return pts, tips


def _ram(cv, base, mat, z, roar, size=1.0):
    """Kıvrık koç boynuzu: halka halka sarmal (boğumlu)."""
    pts = []
    for i in range(14):
        u = i / 13
        a = -math.pi * 0.35 - u * math.pi * 1.55 - roar * 0.1
        r = (7.5 - 4.5 * u) * size
        pts.append((base[0] - 2.5 * size + math.cos(a) * r * 0.9, base[1] + 2.2 * size + math.sin(a) * r))
    path = ik.taper_path([cv.W(q) for q in pts], cv.u(3.6 * size), prof=lambda u: max(0.2, 1.0 - 0.7 * u))
    det = [('ink', [along(pts[i], pts[i + 1], 0.5, -1.3 * size), along(pts[i], pts[i + 1], 0.5, 1.3 * size)], 1.0, (0.2, 0.2))
           for i in range(1, 12, 2)]
    cv.shape(path, mat, z=z, sd=1.8, hi=0.4, details=det)


def draw(cv, p, V):
    bob, lean = p.get('bob', 0.0), p.get('lean', 0.0)
    step = p.get('step', 0.0)
    roar = p.get('roar', 0.0)
    flare = p.get('flare', 0.0)
    ph = p.get('ph', 0.0)
    ex = V['extra']
    B, BB = V['bark'], V['bark_b']
    hip = (-7.0, -30 + bob * 0.6)
    sh = (5 + lean * 28, -54 + bob + max(0.0, lean) * 26 - min(0.0, lean) * 5)

    if 'dust' in ex:   # arkada dönen toz hortumu (bacakları sarar)
        dust = Ink('#c8ae80', '#7c6448', '#eedcb0', name='toz')
        for k in range(3):
            y0 = -6.0 - k * 9.0
            yk.wisp(cv, (hip[0] - 18 + k * 2, y0), -0.12 + k * 0.08, 34 - k * 4, 4.0 - k * 0.6, dust, -20 + k * 0.1, ph=ph + k * 1.7, curl=0.35,
                    alpha=0.5, ink=True)
    # ---- bacaklar: kök gibi kalın, ayaklarda kök saçakları
    for side, z in ((-1, -12), (1, -1)):
        mat = B if side > 0 else BB
        st = step * side
        top = (hip[0] + side * 4, hip[1] + 2)
        knee = (hip[0] + side * 4 + 4 + st * 0.5, -14 + bob * 0.3 - abs(st) * 0.3)
        foot = (hip[0] + side * 5 + 2 + st, -3)
        leg = ik.union(cv.limb([top, lerp2(top, knee, 0.5), knee, foot], [7.2, 6.8, 5.6, 5.2]), _roots(cv, foot, mat, z, side, 3 + side))
        det = _grooves(top, knee, 6.5, 4, 11 + side, 1.3, V if side > 0 else None) + _grooves(knee, foot, 5.2, 3, 21 + side, 1.2, V if side > 0 else None)
        det.append(('ink', [along(knee, top, 0.05, -4.5), along(knee, top, 0.0, 0.0), along(knee, top, 0.08, 4.0)], 1.6, (0.3, 0.3)))
        cv.shape(leg, mat, z=z, sd=3.0, hi=0.5 if side > 0 else 0.0, details=det, hatch=0.5 if side > 0 else 0.0)
        if 'ice' in ex and side > 0:
            yk.icicles(cv, [along(knee, foot, 0.1, 4.6), along(knee, foot, 0.12, -4.6)], V['horn'], z + 0.5, L=3.0, w=1.0, seed=7)
    # ---- arka kol
    al = p.get('al', (0.15, 0.2))
    shb = (sh[0] - 7, sh[1] + 2)
    e, h = fk_arm(shb, al[0], al[1], 18, 18)
    arm = ik.union(cv.limb([shb, lerp2(shb, e, 0.5), e, h], [6.0, 6.2, 4.8, 3.9]), cv.ellipse(h, 4.4, 4.0))
    a = al[0] + al[1]
    claws = [ik.taper_path([cv.W(h), cv.W((h[0] + math.sin(a + k) * 4.5, h[1] + math.cos(a + k) * 4.5)),
                            cv.W((h[0] + math.sin(a + k * 1.2 + 0.2) * 8.0, h[1] + math.cos(a + k * 1.2 + 0.2) * 8.0))], cv.u(3.2), (0.0, 0.95))
             for k in (-0.6, -0.2, 0.2, 0.6)]
    cv.shape(ik.union(arm, *claws), BB, z=-16, sd=3.0, details=_grooves(shb, e, 5.5, 3, 31) + _grooves(e, h, 4.4, 2, 32))
    # ---- gövde: kambur sırt + fıçı göğüs (tek kontur)
    hump = lerp2(hip, sh, 0.55)
    cc = (sh[0] + 6 - lean * 3, sh[1] + 10)
    body = ik.union(cv.capsule(hip, sh, 10.5, 13.5), cv.ellipse((hump[0] - 1, hump[1] - 4), 13.0, 11.5, -0.5), cv.ellipse(cc, 10.5, 12.5))
    det = []
    # gövde olukları: kalçadan omuza kavisli
    for k in range(6):
        o = -10 + k * 4.0
        pts = [along(hip, sh, 0.0, o * 0.8), along(hip, sh, 0.35, o * 1.05 + 1.0), along(hip, sh, 0.7, o * 1.1), along(hip, sh, 1.0, o * 0.9)]
        det.append(('ink', pts, 1.4 + (k % 2) * 0.3, (0.35, 0.35)))
        if k % 2 == 0:
            det.append(('stroke', [(q[0] - 0.7, q[1] - 0.5) for q in pts[1:3]], 1.2, B.hi, (0.4, 0.4)))
    # budak gözü (kabuk düğümü)
    kn = along(hip, sh, 0.35, 6.0)
    rng_ = np.random.default_rng(5)
    for k in range(9):
        q = along(hip, sh, rng_.uniform(0.05, 0.9), rng_.uniform(-9, 9))
        r_ = rng_.uniform(0.5, 1.1)
        det.append(('col', cv.ellipse(q, r_, r_ * 0.8), ik.mix(B.hi, V['back'].hi, 0.6)))
    det += [('deep', cv.ellipse(kn, 2.0, 2.6, 0.4)), ('ink', [(kn[0] - 1.6, kn[1] - 2.2), (kn[0] - 2.4, kn[1]), (kn[0] - 1.4, kn[1] + 2.4)], 1.4)]
    cv.shape(body, B, z=0, sd=6.0, hi=0.8, details=det, hatch=0.45, bounce=0.35, deep=0.35)
    # Erlik çatlakları: göğüs ve böğür (yanan öz)
    gx, gy = cc[0] + 5.5, cc[1] + 5
    cw = 1.5 + flare * 0.8
    _crack(cv, [(gx - 1.5, gy - 3.5), (gx + 0.5, gy + 1), (gx - 1, gy + 5.5), (gx + 0.5, gy + 10)], V, 40, cw)
    _crack(cv, [(gx + 0.5, gy + 1), (gx + 3.0, gy + 2.6)], V, 40, cw * 0.6, hot=False)
    fx_, fy_ = hip[0] + 3, hip[1] - 9
    _crack(cv, [(fx_ - 1, fy_ - 9), (fx_ + 1.5, fy_ - 4), (fx_ - 0.5, fy_), (fx_ + 1, fy_ + 4), (fx_ - 1.5, fy_ + 9)], V, 44, cw * 1.2)
    _crack(cv, [(fx_ + 1.5, fy_ - 4), (fx_ + 5.5, fy_ - 5.8)], V, 44, cw * 0.6, hot=False)
    _crack(cv, [(fx_ - 0.5, fy_), (fx_ - 4.5, fy_ + 1.5), (fx_ - 6.5, fy_ + 5)], V, 44, cw * 0.6, hot=False)
    core = cv.ellipse((fx_, fy_ - 1), 2.0 + flare * 0.5, 2.8 + flare * 0.6)
    cv.fill(core, V['crack'], z=45, glow=V['crack_glow'])
    cv.fill(cv.ellipse((fx_ + 0.2, fy_ - 1.3), 1.0, 1.5), V['crack_hot'], z=45.1, glow=V['crack_hot'])
    yk.glow_soft(cv, (fx_, fy_ - 1), 6.0 + flare * 3.0, V['crack_glow'], z=45.2, blur=0.6, alpha=0.2 + 0.4 * flare)
    yk.glow_soft(cv, (gx, gy + 3), 4.0 + flare * 2.0, V['crack_glow'], z=45.2, blur=0.6, alpha=0.14 + 0.4 * flare)
    # ---- sırttan çıkan kırık dallar (silüeti kırar); kar devinde buz dikenleri
    for j, (t, ang, ln, w) in enumerate(((0.35, -2.2, 11.0, 2.4), (0.55, -1.85, 14.0, 2.8), (0.75, -1.45, 9.0, 2.0))):
        q = lerp2((hip[0] - 4, hip[1] - 12), (sh[0] - 2, sh[1] - 12), t)
        q = (q[0], q[1] - math.sin(t * math.pi) * 6.0)
        ang += lean * 0.3
        tip = (q[0] + math.cos(ang) * ln, q[1] + math.sin(ang) * ln)
        if V['horn_kind'] == 'crystal':
            yk.glow_soft(cv, lerp2(q, tip, 0.6), 3.0, V['crack_glow'], z=15, blur=0.6, alpha=0.2)
            cv.shape(cv.blob([(q[0] - w, q[1] + 1, 0.0), lerp2((q[0] - w * 0.7, q[1]), tip, 0.6), (tip[0], tip[1], 0.0), lerp2((q[0] + w * 0.7, q[1]), tip, 0.6),
                              (q[0] + w, q[1] + 1, 0.0)]), V['horn'], z=15 + j * 0.01, sd=w * 0.8, hi=0.5,
                     details=[('stroke', [lerp2(q, tip, 0.2), lerp2(q, tip, 0.85)], 1.1, (1, 1, 1), (0.2, 0.6))])
            continue
        mid = lerp2(q, tip, 0.55)
        mid = (mid[0] + math.cos(ang + 1.5) * 1.2, mid[1] + math.sin(ang + 1.5) * 1.2)
        tw = lerp2(q, tip, 0.5)
        twig = (tw[0] + math.cos(ang + 0.9) * ln * 0.4, tw[1] + math.sin(ang + 0.9) * ln * 0.4)
        br = ik.union(ik.taper_path([cv.W(q), cv.W(mid), cv.W(tip)], cv.u(w * 2), prof=lambda u: max(0.35, 1.0 - 0.6 * u)),
                      ik.taper_path([cv.W(tw), cv.W(twig)], cv.u(w * 0.9), (0.0, 0.9)))
        # kırık uç: sivri kıymıklar
        nx, ny = -math.sin(ang) * w * 0.45, math.cos(ang) * w * 0.45
        br = ik.union(br, cv.blob([(tip[0] + nx, tip[1] + ny), (tip[0] + math.cos(ang) * 1.8 + nx * 0.4, tip[1] + math.sin(ang) * 1.8 + ny * 0.4, 0.0),
                                   (tip[0], tip[1]), (tip[0] + math.cos(ang) * 1.2 - nx * 0.6, tip[1] + math.sin(ang) * 1.2 - ny * 0.6, 0.0), (tip[0] - nx, tip[1] - ny)]))
        cv.shape(br, BB if j != 1 else B, z=15 + j * 0.01, sd=1.2, hi=0.35,
                 details=[('ink', [lerp2(q, tip, 0.1), lerp2(q, tip, 0.5), lerp2(q, tip, 0.85)], 0.9, (0.3, 0.5))])
        if 'embers' in ex:
            cv.fill(cv.ellipse(tip, 0.9, 0.9), V['crack_hot'], z=15.2, glow=V['crack_glow'])
            yk.glow_soft(cv, tip, 2.5, V['crack_glow'], z=15.3, alpha=0.5)
        if j == 1 and V['caput']:
            for k_, col in enumerate(V['caput'][:2]):
                qq = lerp2(q, tip, 0.6 + k_ * 0.15)
                sw = math.sin(ph + k_ * 2) * 0.5
                cv.shape(ik.taper_path([cv.W(qq), cv.W((qq[0] - 1.0 + sw, qq[1] + 3.0)), cv.W((qq[0] - 2.0 + sw * 2, qq[1] + 6.5))], cv.u(1.5), (0.05, 0.5)),
                         Ink(col), z=15.3 + k_ * 0.01, sd=0.4, ol=0.7)
    # ---- sırt örtüsü (yosun / ot / su yosunu / kar / kül), alt kenarı saçaklı
    top, bot = [], []
    for i in range(9):
        t = i / 8
        q = lerp2((hip[0] - 6, hip[1] + 2), (sh[0] + 4, sh[1] - 2), t)
        bump = math.sin(t * math.pi)
        topy = q[1] - 12.0 - bump * 8.5
        top.append((q[0] - bump * 1.5 + math.sin(i * 2.3) * 0.6, topy + 1.0 - (i % 3 == 1) * 1.0))
        bot.append((q[0] - bump * 1.5 + (1.5 if i % 2 else -1.0), topy + 9 + (i % 2) * 4.5 + bump * 2.0, 0.0 if i % 2 else 1.0))
    bk = V['back_kind']
    BK = V['back']
    mdet = []
    for i in range(1, 8):
        q = top[i]
        mdet.append(('stroke', [(q[0] + 0.5, q[1] + 1.5), (q[0] + 1.5, q[1] + 4.0)], 1.6, BK.hi, (0.2, 0.7)))
    # üst kenar: gövde sırtına oturan, tutam tutam kabarık kenar (yastık değil örtü)
    tt = []
    for i in range(len(top) - 1):
        q0, q1 = top[i], top[i + 1]
        tt.append(q0)
        m = lerp2(q0, q1, 0.5)
        dx, dy = q1[0] - q0[0], q1[1] - q0[1]
        L_ = math.hypot(dx, dy) or 1
        tt.append((m[0] + dy / L_ * 1.6, m[1] - dx / L_ * 1.6, 0.0))
    tt.append(top[-1])
    # örtü gövdenin sırtına oturur: gövde silüetinin biraz dışına taşan kısım tutam olarak kalır (şapka gibi durmasın)
    hug = ik.union(body, ik.moved(body, 0, -cv.u(2.2)), ik.moved(body, -cv.u(1.2), -cv.u(1.2)))
    cv.shape(ik.isect(cv.blob(tt + bot[::-1]), hug), BK, z=26, sd=2.4, hi=0.6, details=mdet, fur=1.3, soft=0.3, cast=0.8)
    for i in list(range(1, 8, 2)) + [2, 6]:   # sarkan saçaklar
        q = bot[i]
        L = (5 + (i * 7) % 6) * (1.6 if bk in ('weed', 'grass') else 1.0)
        sw = math.sin(ph + i) * 0.8 - lean * 2
        pts = [(q[0], q[1] - 1), (q[0] - 0.4 + sw * 0.5, q[1] + L * 0.5), (q[0] - 0.8 + sw, q[1] + L)]
        if bk == 'snow':
            yk.icicles(cv, [q], V['horn'], 25.5, L=L * 0.7, w=0.9, seed=i)
            continue
        if bk == 'ash':
            cv.fill(cv.ellipse(pts[-1], 0.55, 0.55), V['crack_hot'], z=25.5, glow=V['crack_glow'])
        cv.shape(ik.taper_path([cv.W(r_) for r_ in pts], cv.u(1.8), (0.0, 0.85)), BK, z=25 + i * 0.01, sd=0.7, ol=0.8)
    if bk in ('moss', 'weed'):   # mantarlar / midyeler sırtta
        for j, t in enumerate((0.3, 0.55)):
            q = lerp2(top[2], top[6], t)
            q = (q[0], q[1] + 1.0)
            S = V['shroom']
            cap = cv.blob([(q[0] - 2.2, q[1]), (q[0] - 1.6, q[1] - 1.6), (q[0], q[1] - 2.3), (q[0] + 1.6, q[1] - 1.6), (q[0] + 2.2, q[1]), (q[0], q[1] + 0.5)])
            cv.shape(cv.capsule((q[0], q[1]), (q[0] + 0.2, q[1] + 2.0), 0.6, 0.7), Ink('#e8dcc4'), z=27 + j * 0.1, sd=0.4, ol=0.7)
            cv.shape(cap, S, z=27.05 + j * 0.1, sd=0.9, hi=0.35, ol=0.8,
                     details=[('col', cv.ellipse((q[0] - 0.6, q[1] - 1.3), 0.45, 0.35), S.hi)])
    if 'flames' in ex:   # omuz ve sırtta alev dilleri: kıvrık S dil, dışı kızıl içi sarı
        for j, t in enumerate((0.2, 0.5, 0.8)):
            q = lerp2(top[1], top[7], t)
            hgt = 7.0 + 2.5 * math.sin(ph * 2 + j * 2.1) + flare * 3.0
            wv = math.sin(ph * 3 + j * 1.3) * 1.2
            def tongue(sc, q=q, hgt=hgt, wv=wv):
                return cv.blob([(q[0] - 2.2 * sc, q[1] + 1.0), (q[0] - 2.0 * sc + wv * 0.3, q[1] - hgt * 0.35 * sc), (q[0] - 0.6 * sc + wv, q[1] - hgt * 0.7 * sc),
                                (q[0] - 1.6 + wv * 1.6, q[1] - hgt * sc, 0.0), (q[0] + 0.8 * sc + wv * 0.6, q[1] - hgt * 0.55 * sc), (q[0] + 2.0 * sc, q[1] - hgt * 0.2 * sc),
                                (q[0] + 2.2 * sc, q[1] + 1.0)])
            cv.fill(tongue(1.0), (0.95, 0.3, 0.06), z=27 + j * 0.1, glow=(1.0, 0.35, 0.02))
            cv.fill(tongue(0.6), (1.0, 0.82, 0.3), z=27.05 + j * 0.1, glow=(1.0, 0.75, 0.25))
            yk.glow_soft(cv, (q[0], q[1] - hgt * 0.4), 4.0, (1.0, 0.4, 0.02), z=27.2, blur=0.6, alpha=0.45)
    if 'embers' in ex:
        yk.sparks(cv, (sh[0] - 4, sh[1] - 16), 6, 2.0, 9.0, V['crack_hot'], 28, seed=int(ph * 10) + 3, w=1.1, glow=V['crack_glow'], ang=-math.pi / 2, spread=1.4)
    # ---- baş
    hdy = p.get('hdy', 0.0)
    hx, hy = sh[0] + 14, sh[1] + 2 + hdy - roar * 3
    neck = cv.capsule((sh[0] + 3, sh[1] - 1), (hx - 2, hy + 1), 6.0, 4.0)
    cv.shape(neck, B, z=20, sd=2.5, hi=0.4, details=_grooves((sh[0] + 3, sh[1] - 1), (hx - 2, hy + 1), 5.0, 3, 41, 1.2, V))
    hk = V['horn_kind']
    if hk == 'antler':
        _antler(cv, (hx - 3.5, hy - 4.0), -2.3 - roar * 0.15, 24, V['horn'] if V['horn'] is not BONE else Ink('#b4a68e', '#665848', '#d4c8b0', '#3a3028'), 6,
                r0=1.7, curve=0.3, seed=1, V=V)
    elif hk == 'crystal':
        _antler(cv, (hx - 3.0, hy - 4.0), -2.3, 16, V['horn'], 6, r0=1.4, seed=2, kind='crystal', V=V)
    jaw = 1.0 + roar * 4.0
    S = V['skull']
    eyec = (hx + 1.4, hy - 0.6)
    if V['head'] == 'stone':   # dev başı: alçak alın, ağır kaş kemiği, gömük ayaz gözler, alt çeneden yukarı buz dişler
        jd = roar * 2.5
        cran = cv.blob([(hx - 6, hy - 1), (hx - 4.5, hy - 6.0), (hx + 1.5, hy - 8.0), (hx + 7.5, hy - 6.5), (hx + 10.5, hy - 3.0),
                        (hx + 11.5, hy + 0.5), (hx + 10.0, hy + 2.5), (hx + 4, hy + 3.0), (hx - 3, hy + 4)])
        jawp = cv.blob([(hx - 3.5, hy + 1.5), (hx + 4, hy + 2.0 + jd * 0.5), (hx + 11.8, hy + 2.5 + jd), (hx + 12.2, hy + 6.5 + jd, 0.0),
                        (hx + 8, hy + 8.5 + jd), (hx + 1, hy + 8.0 + jd * 0.6), (hx - 3.5, hy + 5.0)])
        jdet = [('ink', [(hx + 2, hy + 5.0 + jd * 0.6), (hx + 7, hy + 6.5 + jd), (hx + 10.5, hy + 6.0 + jd)], 1.2, (0.3, 0.3))]
        cv.shape(jawp, S, z=29, sd=2.0, hi=0.4, details=jdet, hatch=0.4)
        if roar > 0.2:
            cv.fill(cv.blob([(hx + 3, hy + 2.6), (hx + 11.4, hy + 2.6), (hx + 11.4, hy + 2.6 + jd), (hx + 4, hy + 2.6 + jd * 0.6)]), INK, z=29.4)
            yk.glow_soft(cv, (hx + 8, hy + 3 + jd * 0.5), 3.0, V['crack_glow'], z=29.5, blur=0.6, alpha=0.4 * roar)
        for dx_, ln in ((5.0, 3.6), (10.0, 3.0)):   # yukarı bakan buz dişler
            x0 = hx + dx_
            cv.shape(cv.blob([(x0 - 0.8, hy + 3.2 + jd), (x0 + 0.8, hy + 3.2 + jd), (x0 + 0.2, hy + 3.2 + jd - ln, 0.0)]), V['horn'], z=29.6, sd=0.4, hi=0.3, ol=0.75)
        hdet = [('deep', cv.blob([(hx - 1.5, hy - 2.6), (hx + 10.5, hy - 3.4), (hx + 10.5, hy - 0.8), (hx - 1.0, hy - 0.4)])),
                ('ink', [(hx + 8.6, hy - 1.0), (hx + 10.5, hy + 0.8), (hx + 11.6, hy + 0.3)], 1.3),
                ('ink', [(hx - 4.5, hy - 1.5), (hx - 2.5, hy + 0.5), (hx - 3.0, hy + 3.0)], 1.2),
                ('ink', [(hx + 1.0, hy - 6.4), (hx + 2.5, hy - 5.0), (hx + 2.0, hy - 3.6)], 1.0)]
        cv.shape(cran, S, z=30, sd=2.6, hi=0.6, details=hdet, hatch=0.3)
        brow = cv.blob([(hx - 2.5, hy - 2.2), (hx + 2, hy - 5.0), (hx + 8, hy - 4.8), (hx + 11.0, hy - 2.6), (hx + 8.5, hy - 2.0), (hx + 3, hy - 2.4)])
        cv.shape(brow, S, z=30.5, sd=1.2, hi=0.6, ol=0.9)
        for dx_ in (2.6, 7.6):
            yk.eye_glow(cv, (hx + dx_, hy - 1.0), 0.9 + flare * 0.3, 0.45 + flare * 0.15, 0.0, V['eye'], V['crack_glow'], 46)
        yk.icicles(cv, [(hx + 2, hy + 7.6 + jd * 0.6), (hx + 5, hy + 8.2 + jd * 0.8), (hx + 8, hy + 8.3 + jd)], V['horn'], 29.7, L=2.6, w=0.8, seed=12)
        eyec = (hx + 2.6, hy - 1.0)
    else:
        # geyik/koç kafatası: kafatası + uzun burun + alt çene
        skull = ik.union(cv.ellipse((hx, hy), 6.2, 5.4), cv.blob([(hx + 1, hy - 4.2), (hx + 14, hy + 2.8 - roar), (hx + 13.5, hy + 5.0 - roar), (hx + 2, hy + 4.8)]))
        sdet = [('deep', cv.blob([(hx + 9.5, hy + 0.6 - roar * 0.6), (hx + 12.6, hy + 2.4 - roar * 0.9), (hx + 10.0, hy + 2.0 - roar * 0.8)])),
                ('ink', [(hx - 4.5, hy + 2.2), (hx - 1.5, hy + 4.2), (hx + 2.5, hy + 4.8)], 1.2),
                ('ink', [(hx + 4.0, hy - 2.6), (hx + 8.0, hy - 0.6), (hx + 12.5, hy + 1.6 - roar)], 1.0, (0.2, 0.6)),
                ('ink', [(hx - 1.0, hy - 5.0), (hx + 0.2, hy - 3.2), (hx - 0.6, hy - 1.8)], 0.9)]
        cv.shape(skull, S, z=30, sd=1.6, hi=0.45, details=sdet)
        mand = cv.blob([(hx - 1, hy + 3.8), (hx + 11.5, hy + 4.6 - roar + jaw), (hx + 10.5, hy + 6.2 - roar + jaw), (hx, hy + 6.0)])
        cv.shape(mand, Ink(S.shadow, S.deep, S.base), z=29, sd=0.8, ol=0.9)
        if roar > 0.2:
            cv.fill(cv.blob([(hx + 1, hy + 4.4), (hx + 12, hy + 4.0 - roar), (hx + 11, hy + 4.7 - roar + jaw * 0.8), (hx + 1, hy + 5.0)]), INK, z=29.5)
            yk.glow_soft(cv, (hx + 6, hy + 4.6), 3.0, V['crack_glow'], z=29.6, blur=0.6, alpha=0.35 * roar)
        for i in range(5):
            x = hx + 4 + i * 1.8
            y = hy + 4.9 - roar * (0.4 + i * 0.1) + i * 0.2
            cv.fill(cv.blob([(x - 0.5, y - 0.6), (x + 0.5, y - 0.6), (x + 0.1, y + 0.9, 0.0)]), S.base, z=30.5)
        cv.fill(cv.ellipse((hx + 1.4, hy - 0.6), 2.7, 2.3, 0.2), INK, z=40)
        yk.eye_glow(cv, (hx + 1.6, hy - 0.7), 1.0 + flare * 0.4, 0.8 + flare * 0.3, 0.2, V['eye'], V['crack_glow'], 46)
    if hk == 'antler':
        r_ = _antler(cv, (hx - 1.0, hy - 4.6), -2.05 - roar * 0.15, 29, V['horn'], 34, r0=2.0, curve=0.28, seed=3, V=V)
        if V['caput'] and r_:
            pts_, tips = r_
            for j, (q, col) in enumerate(zip([lerp2(pts_[1], pts_[2], 0.5), lerp2(pts_[2], pts_[3], 0.5), tips[1]], V['caput'])):
                sw = math.sin(ph + j * 1.9) * 0.4 - lean * 0.5
                cv.shape(ik.taper_path([cv.W(q), cv.W((q[0] - 0.8 + sw, q[1] + 3.0)), cv.W((q[0] - 1.6 + sw * 2, q[1] + 6.0 + j))], cv.u(1.4), (0.05, 0.5)),
                         Ink(col), z=35 + j * 0.01, sd=0.4, ol=0.7)
                cv.shape(cv.ellipse(q, 0.9, 0.7), Ink(col), z=35.1 + j * 0.01, sd=0.3, ol=0.6)
    elif hk == 'ram':
        _ram(cv, (hx - 0.5, hy - 1.0), V['horn'], 34, roar, size=0.62)
    elif hk == 'crystal':
        _antler(cv, (hx + 1.5, hy - 5.0), -1.9, 20, V['horn'], 34, r0=1.7, seed=4, kind='crystal', V=V)
    # ---- ön kol: uzun, ağır; omuzda örtü, ön kolda çatlak, kök pençeli yumruk
    ar = p.get('ar', (0.25, 0.15))
    shf = (sh[0] + 1, sh[1] + 3)
    e, h = fk_arm(shf, ar[0], ar[1], 19, 19)
    a = ar[0] + ar[1]
    fist = cv.ellipse(h, 5.0, 4.6)
    claws = []
    for k in (-0.65, -0.22, 0.22, 0.65):
        m = (h[0] + math.sin(a + k) * 5.0, h[1] + math.cos(a + k) * 5.0)
        tip = (h[0] + math.sin(a + k * 1.25 + 0.15) * 9.0, h[1] + math.cos(a + k * 1.25 + 0.15) * 9.0)
        claws.append(ik.taper_path([cv.W(h), cv.W(m), cv.W(tip)], cv.u(3.6), (0.0, 0.95)))
    arm = ik.union(cv.limb([shf, lerp2(shf, e, 0.45), e, lerp2(e, h, 0.5), h], [6.5, 6.8, 5.2, 4.8, 4.4]), fist, *claws)
    det = _grooves(shf, e, 6.0, 4, 51, 1.3, V) + _grooves(e, h, 4.8, 3, 52, 1.2, V)
    det.append(('ink', [along(e, shf, 0.08, -4.5), e, along(e, h, 0.08, 4.5)], 1.6, (0.3, 0.3)))
    cv.shape(arm, B, z=50, sd=3.4, hi=0.6, details=det, hatch=0.35, bounce=0.3)
    m1, m2 = lerp2(e, h, 0.15), lerp2(e, h, 0.75)
    _crack(cv, [m1, (lerp2(m1, m2, 0.5)[0] + 1.2, lerp2(m1, m2, 0.5)[1]), m2], V, 62, 1.2 + flare * 0.7)
    if flare > 0:
        yk.glow_soft(cv, h, 7.0, V['crack_glow'], z=62.5, blur=0.6, alpha=0.4 * flare)
    pad = cv.blob([(shf[0] - 7.5, shf[1] - 1.5), (shf[0] - 4.0, shf[1] - 6.5), (shf[0] + 3.0, shf[1] - 6.8), (shf[0] + 7.0, shf[1] - 2.0),
                   (shf[0] + 4.5, shf[1] + 1.5, 0.0), (shf[0] + 1.5, shf[1] + 0.2), (shf[0] - 1.5, shf[1] + 2.4, 0.0), (shf[0] - 4.5, shf[1] + 0.5)])
    cv.shape(pad, BK, z=58, sd=1.8, hi=0.5, fur=1.0, soft=0.3)
    if bk in ('moss', 'weed', 'grass'):
        for j, dx_ in enumerate((-5.0, -1.0, 3.5)):
            q = (shf[0] + dx_, shf[1] + 0.8 + (j % 2) * 1.2)
            L = 4.0 + j * 1.5 if bk != 'weed' else 7.0 + j * 2
            sw = math.sin(ph + j) * 0.6 - lean * 1.5
            cv.shape(ik.taper_path([cv.W(q), cv.W((q[0] + sw * 0.5, q[1] + L * 0.5)), cv.W((q[0] + sw, q[1] + L))], cv.u(1.6), (0.0, 0.85)),
                     BK, z=57.5 + j * 0.01, sd=0.6, ol=0.8)
    if 'drips' in ex:   # su damlaları
        for j, q in enumerate((h, lerp2(e, h, 0.5), (cc[0] + 4, cc[1] + 12))):
            d = (q[0] + 0.5, q[1] + 5.5 + ((ph * 1.5 + j) % 2.0))
            cv.shape(cv.blob([(d[0], d[1] - 1.6, 0.0), (d[0] + 0.8, d[1] + 0.2), (d[0], d[1] + 0.9), (d[0] - 0.8, d[1] + 0.2)]),
                     Ink('#9fe8e0', '#3a8a96', '#ffffff'), z=63 + j * 0.01, sd=0.4, hi=0.25, ol=0.6, glow=(0.05, 0.3, 0.3))
    if 'ice' in ex:
        yk.icicles(cv, [along(shf, e, 0.6, -5.5), along(shf, e, 0.85, -5.0), along(e, h, 0.4, -4.0)], V['horn'], 59, L=3.5, w=1.0, seed=11)
    if 'dust' in ex:   # öndeki toz teli (kolu sarar)
        dust = Ink('#d2b88a', '#866c4e', '#f2e2bc', name='toz')
        yk.wisp(cv, (hip[0] - 12, -4.0), -0.25, 40, 3.2, dust, 64, ph=ph + 0.6, curl=0.3, alpha=0.45, ink=True)
    return {'hand': h}


def _pose(anim, i):
    n, fn, loop, arm = ANIMS[anim]
    p = dict(fn(i / n))
    p['ph'] = i / n * math.tau
    if anim == 'windup':
        p['flare'] = 0.6 + 0.4 * i   # hazırlık: çatlaklar ve göz alevlenir, yumruk ışır
    if anim == 'slam':
        p['flare'] = 0.8 - 0.5 * i
    return p


SHADE = dict(outer=0.6, rim=0.7, rim_col=(0.68, 0.76, 1.0), rim_dir=(0.6, -0.8), rim_w=1.6, form=(7.0, (0.74, 0.72, 0.86)))


def render_frame(anim, i, var='agac_iyesi', ss=3):
    V = VARIANTS[var]
    p = _pose(anim, i)
    cv = yk.occlude_glow(ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss))
    info = draw(cv, p, V)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
