"""Kara İye (kimlik agac_iyesi) ve biyom çeşitlemeleri — stil v2 "mürekkep-cel". v1: creatures.draw_iye.

Hücre dünya 128x112 (doku 4), ayak (60, 106); 'hand' çapası (ön yumruk; yer vuruşu / kök oradan çıkar).

Tasarım: Türk inancında "iye" bir yerin, ağacın, suyun koruyucu ruhudur. Kara İye kutsal bir dilek ağacının iyesiydi:
geyik kafatası başı, dallanan boynuzlarında hâlâ insanların bağladığı dilek çaputları sallanır. Erlik'in kara kökleri
göğsünü yarınca mor yanan çatlaklar açıldı. Kök bacaklar, kambur kütük gövde, sırtında yosun örtüsü ve mantarlar,
diz boyu uzun kollar ve kök pençeli yumruklar.

v29 tam gövde animasyonu (docs/TASARIM.md "v29: yer yaratıklarının tam gövde animasyonu"; referans kara_boru_ink.py):
iskelet AYAK HEDEFLİ — iki kök ayağın yerdeki / havadaki yeri yazılır (lf yakın, lb uzak: x, yerden yükseklik, parmak
kıvrımı), bacaklar kalça -> diz -> bilek IK ile çözülür (erişilemeyen hedef kırpılır); gövde kalçada öne / arkaya eğilir
(pitch), kamburlaşır (arch), omuzlar burulur (tw); baş grubu boyun dibinde döner (hr) ve önden gider (hd); kollar mutlak
açılarla (al / ar: (omuz, dirsek), 0 aşağı, + öne, pi yukarı; gövde eğiminden bağımsız sarkar), pençeler açılır (cl).
Bütün figür bir pivot (rp) çevresinde devrilir (roll: ölümde öne kesilen ağaç gibi), aynalanır / daralır (sx: dönüş ve
döner savuruşta gövde çevrilir), ezilip esner (sq). İkincil hareket: çaputlar ve yosun saçakları dünya aşağısına sarkar,
gecikmeli dalgayla (rag, ph) salınır. Yer etkisi: toprak topakları ve toz (dirt), adım tozu (pf).

Satırlar SEQS (sıra = satır), yapay zekâ eşlemesi DURUM: brute (Kara İye, Dev Çocuğu) + tornado / caster eşlemeleri
(Tozkoparan, Su İyesi, Od İyesi aynı satırları kullanabilir).

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
import yaratik_govde as yg
import yaratik_ink_kit as yk
from yaratik_govde import Seq

TEX = 4.0
CELL = (512, 448)       # dünya 128 x 112
FEET = (240, 424)       # dünya (60, 106)

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
        puff=Ink('#9c8a70', '#56463a', '#c8b898', name='toprak tozu'),
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
        eye=(0.85, 0.98, 1.0), caput=(), extra=('ice',), puff=Ink('#e4ecf6', '#8494b8', '#ffffff', name='kar tozu')),
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

def _roots(cv, foot, toe=0.0):
    """Kök saçaklı ayak: ayak noktasından yere yayılan dört kök. toe: saçaklar ayak çevresinde döner (itiş / havada sarkma)."""
    rng = np.random.default_rng(5)
    out = []
    for k, dx in enumerate((-6.5, -2.5, 3.5, 7.5)):
        s = (foot[0] + dx * 0.25, foot[1] - 1.0)
        e = (foot[0] + dx + rng.uniform(-0.6, 0.6), foot[1] + 3.6)
        m = (lerp2(s, e, 0.5)[0], lerp2(s, e, 0.5)[1] - 0.8)
        if toe:
            e = yg.rot_about(e, foot, toe)
            m = yg.rot_about(m, foot, toe * 0.6)
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


# ====================================================================== iskelet
HIP0 = (-7.0, -30.0)          # kalça (gövde yereli kökü; pitch bunun çevresinde)
T0 = (13.4, -22.7)            # kalça -> omuz (dinlenme)
L_THIGH, L_SHIN = 15.2, 12.4  # bacak IK kemikleri (kalça eklemi -> diz -> ayak noktası)
FOOT_Y = -3.0                 # ayak noktası (kök saçakları 3,6 aşağıda yere değer)
L_ARM = 19.0

# dinlenme pozu (eski idle'ın ortası). lf / lb: yakın / uzak ayak (x, yerden yükseklik, saçak kıvrımı rad)
REST = dict(x=0.0, y=0.0, roll=0.0, rp=(4.0, 0.0), sx=1.0, sq=0.0,
            pitch=0.0, arch=0.0, tw=0.0, br=0.0,
            lf=(0.0, 0.0, 0.0), lb=(-10.0, 0.0, 0.0),
            al=(0.12, 0.22), ar=(0.25, 0.12), cl=0.0,
            hr=0.0, hd=(0.0, 0.0), roar=0.0, flare=0.0, eye=0.0, rag=0.0, ph=0.0,
            dirt=0.0, dirt_x=40.0, pf=0.0, pf_x=0.0)


def _hang(q, dx, dy, comp):
    """q'dan (dx, dy) sarkan nokta; comp: yerel çerçevenin dünya açısının tersi (çaput / saçak dünya aşağısına sarkar)."""
    v = yg.rot((dx, dy), comp)
    return (q[0] + v[0], q[1] + v[1])


def _arm_pts(sh, a1, a2, l1=L_ARM, l2=L_ARM):
    return fk_arm(sh, a1, a2, l1, l2)


def _claws(cv, h, a, n_r, spread, ln, w):
    out = []
    for k in (-0.65, -0.22, 0.22, 0.65):
        kk = k * spread
        m = (h[0] + math.sin(a + kk) * n_r, h[1] + math.cos(a + kk) * n_r)
        tip = (h[0] + math.sin(a + kk * 1.25 + 0.15) * ln, h[1] + math.cos(a + kk * 1.25 + 0.15) * ln)
        out.append(ik.taper_path([cv.W(h), cv.W(m), cv.W(tip)], cv.u(w), (0.0, 0.95)))
    return out


def _ground_fx(cv, p, V):
    """Yer etkisi (dünya çerçevesinde, dönüşümsüz): vuruşta fışkıran toprak topakları + toz; adım tozu."""
    D = V['puff']
    d = p['dirt']
    if 0.0 < d < 1.0:
        x0 = p['dirt_x']
        rng = np.random.default_rng(int(x0 * 7) + 3)
        for k in range(7):
            vx = rng.uniform(-16, 16)
            vy = rng.uniform(14, 26)
            t = d * rng.uniform(0.75, 1.05)
            q = (x0 + vx * t, -(vy * t - 30.0 * t * t) - 1.0)
            if q[1] > 0.5:
                continue
            r = rng.uniform(0.9, 1.7) * (1.0 - 0.4 * d)
            cv.shape(cv.blob([(q[0] - r, q[1]), (q[0] - r * 0.3, q[1] - r * 0.9), (q[0] + r, q[1] - r * 0.4), (q[0] + r * 0.6, q[1] + r * 0.7)]),
                     V['bark_b'] if k % 2 else D, z=72 + k * 0.01, sd=r * 0.5, ol=0.7)
        s = 0.6 + 0.4 * d
        for k, (ox, rr) in enumerate(((-9.0, 4.5), (0.0, 5.5), (9.0, 4.5))):
            yk.puff(cv, (x0 + ox * (0.6 + d), -2.5 - d * 3.0 - (k == 1) * 1.5), rr * s, D, z=70 + k * 0.01, seed=k + 3, alpha=1.0)
    if p['pf'] > 0.0:
        a = p['pf']
        for k, ox in enumerate((-3.5, 3.5)):
            yk.puff(cv, (p['pf_x'] + ox * (0.7 + a * 0.5), -1.6 - a * 0.6), 1.6 + 1.6 * a, D, z=66 + k * 0.01, seed=k + 11)


def draw(cv, p, V):
    yg.bake_xf(cv)
    q = dict(REST)
    q.update(p)
    p = q
    roar = p['roar']
    flare = p['flare']
    ph = p['ph']
    pitch, arch, tw = p['pitch'], p['arch'], p['tw']
    ex = V['extra']
    B, BB = V['bark'], V['bark_b']
    BK = V['back']
    bk = V['back_kind']
    # ---- bütün figür: pivot (rp) çevresinde devrilme + öteleme; içte aynalama / daralma (sx) ve ezilme (sq)
    yg.xf_push(cv, p['rp'], p['roll'], p['x'], p['y'])
    sq = p['sq']
    ssx = p['sx'] * (1.0 + 0.07 * sq)
    if abs(ssx) < 0.05:
        ssx = 0.05
    ssy = 1.0 - 0.08 * sq
    yg.xf_push(cv, (0.0, 0.0), 0.0, 0.0, 0.0, ssx, ssy)

    def F(t):   # dünya ayak hedefi -> figür çerçevesi (dönüşümlerin tersi): yere basan ayak kaymaz
        w = (t[0] - p['x'], FOOT_Y - t[1] - p['y'])
        w = yg.rot_about(w, p['rp'], -p['roll'])
        return (w[0] / ssx, w[1] / ssy)

    hip = HIP0
    sh = (hip[0] + T0[0] * (1.0 - 0.04 * arch), hip[1] + T0[1] * (1.0 - 0.07 * arch))

    def TB(pt):
        return yg.rot_about(pt, hip, pitch)
    comp_t = -(pitch + p['roll'])   # gövde yerelinde dünya aşağısı

    if 'dust' in ex:   # arkada dönen toz hortumu (bacakları sarar)
        dust = Ink('#c8ae80', '#7c6448', '#eedcb0', name='toz')
        for k in range(3):
            y0 = -6.0 - k * 9.0
            yk.wisp(cv, (hip[0] - 18 + k * 2, y0), -0.12 + k * 0.08, 34 - k * 4, 4.0 - k * 0.6, dust, -20 + k * 0.1, ph=ph + k * 1.7, curl=0.35,
                    alpha=0.5, ink=True)
    # ---- bacaklar: kök gibi kalın; ayak hedefli IK (diz öne)
    for side, z in ((-1, -12), (1, -1)):
        mat = B if side > 0 else BB
        tg = p['lf'] if side > 0 else p['lb']
        top = TB((hip[0] + side * 4, hip[1] + 2))
        knee, foot = yg.ik2(top, F(tg), L_THIGH, L_SHIN, -1)
        leg = ik.union(cv.limb([top, lerp2(top, knee, 0.5), knee, foot], [7.2, 6.8, 5.6, 5.2]), _roots(cv, foot, tg[2] if len(tg) > 2 else 0.0))
        det = _grooves(top, knee, 6.5, 4, 11 + side, 1.3, V if side > 0 else None) + _grooves(knee, foot, 5.2, 3, 21 + side, 1.2, V if side > 0 else None)
        det.append(('ink', [along(knee, top, 0.05, -4.5), along(knee, top, 0.0, 0.0), along(knee, top, 0.08, 4.0)], 1.6, (0.3, 0.3)))
        cv.shape(leg, mat, z=z, sd=3.0, hi=0.5 if side > 0 else 0.0, details=det, hatch=0.5 if side > 0 else 0.0)
        if 'ice' in ex and side > 0:
            yk.icicles(cv, [along(knee, foot, 0.1, 4.6), along(knee, foot, 0.12, -4.6)], V['horn'], z + 0.5, L=3.0, w=1.0, seed=7)

    # ---- gövde yereli (kalça çevresinde pitch)
    yg.xf_push(cv, hip, pitch)
    # ---- arka kol (mutlak açı -> yerel: + pitch)
    al = p['al']
    shb = (sh[0] - 7 - tw, sh[1] + 2)
    a1b = al[0] + pitch
    e, h = _arm_pts(shb, a1b, al[1], 18, 18)
    arm = ik.union(cv.limb([shb, lerp2(shb, e, 0.5), e, h], [6.0, 6.2, 4.8, 3.9]), cv.ellipse(h, 4.4, 4.0))
    a = a1b + al[1]
    claws = _claws(cv, h, a, 4.5, 1.0 + 0.7 * p['cl'], 8.0 * (1.0 + 0.2 * p['cl']), 3.2)
    cv.shape(ik.union(arm, *claws), BB, z=-16, sd=3.0, details=_grooves(shb, e, 5.5, 3, 31) + _grooves(e, h, 4.4, 2, 32))
    # ---- gövde: kambur sırt + fıçı göğüs (tek kontur); arch kamburu büyütür, br göğsü şişirir
    hump = lerp2(hip, sh, 0.55)
    cc = (sh[0] + 5.8, sh[1] + 10)
    br = p['br']
    body = ik.union(cv.capsule(hip, sh, 10.5, 13.5),
                    cv.ellipse((hump[0] - 1 - arch * 0.8, hump[1] - 4 - arch * 1.6), 13.0 + arch * 0.8, 11.5 + arch * 1.0, -0.5),
                    cv.ellipse(cc, 10.5 + br * 0.5, 12.5 + br * 0.4))
    det = []
    for k in range(6):
        o = -10 + k * 4.0
        pts = [along(hip, sh, 0.0, o * 0.8), along(hip, sh, 0.35, o * 1.05 + 1.0), along(hip, sh, 0.7, o * 1.1), along(hip, sh, 1.0, o * 0.9)]
        det.append(('ink', pts, 1.4 + (k % 2) * 0.3, (0.35, 0.35)))
        if k % 2 == 0:
            det.append(('stroke', [(q_[0] - 0.7, q_[1] - 0.5) for q_ in pts[1:3]], 1.2, B.hi, (0.4, 0.4)))
    kn = along(hip, sh, 0.35, 6.0)
    rng_ = np.random.default_rng(5)
    for k in range(9):
        q_ = along(hip, sh, rng_.uniform(0.05, 0.9), rng_.uniform(-9, 9))
        r_ = rng_.uniform(0.5, 1.1)
        det.append(('col', cv.ellipse(q_, r_, r_ * 0.8), ik.mix(B.hi, V['back'].hi, 0.6)))
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
    if flare > 0.75:   # derin kurulma: çatlaklar dallanır
        _crack(cv, [(fx_ + 1, fy_ + 4), (fx_ + 6, fy_ + 7), (fx_ + 8.5, fy_ + 12)], V, 44, cw * 0.55, hot=False)
        _crack(cv, [(gx - 1, gy + 5.5), (gx - 5.5, gy + 7.5)], V, 40, cw * 0.5, hot=False)
    core = cv.ellipse((fx_, fy_ - 1), 2.0 + flare * 0.5, 2.8 + flare * 0.6)
    cv.fill(core, V['crack'], z=45, glow=V['crack_glow'])
    cv.fill(cv.ellipse((fx_ + 0.2, fy_ - 1.3), 1.0, 1.5), V['crack_hot'], z=45.1, glow=V['crack_hot'])
    yk.glow_soft(cv, (fx_, fy_ - 1), 6.0 + flare * 3.0, V['crack_glow'], z=45.2, blur=0.6, alpha=0.2 + 0.4 * flare)
    yk.glow_soft(cv, (gx, gy + 3), 4.0 + flare * 2.0, V['crack_glow'], z=45.2, blur=0.6, alpha=0.14 + 0.4 * flare)
    # ---- sırttan çıkan kırık dallar (silüeti kırar); kar devinde buz dikenleri
    for j, (t, ang, ln, w) in enumerate(((0.35, -2.2, 11.0, 2.4), (0.55, -1.85, 14.0, 2.8), (0.75, -1.45, 9.0, 2.0))):
        q_ = lerp2((hip[0] - 4, hip[1] - 12), (sh[0] - 2, sh[1] - 12), t)
        q_ = (q_[0] - arch * 0.6, q_[1] - math.sin(t * math.pi) * (6.0 + arch * 1.8))
        ang += 0.015
        tip = (q_[0] + math.cos(ang) * ln, q_[1] + math.sin(ang) * ln)
        if V['horn_kind'] == 'crystal':
            yk.glow_soft(cv, lerp2(q_, tip, 0.6), 3.0, V['crack_glow'], z=15, blur=0.6, alpha=0.2)
            cv.shape(cv.blob([(q_[0] - w, q_[1] + 1, 0.0), lerp2((q_[0] - w * 0.7, q_[1]), tip, 0.6), (tip[0], tip[1], 0.0), lerp2((q_[0] + w * 0.7, q_[1]), tip, 0.6),
                              (q_[0] + w, q_[1] + 1, 0.0)]), V['horn'], z=15 + j * 0.01, sd=w * 0.8, hi=0.5,
                     details=[('stroke', [lerp2(q_, tip, 0.2), lerp2(q_, tip, 0.85)], 1.1, (1, 1, 1), (0.2, 0.6))])
            continue
        mid = lerp2(q_, tip, 0.55)
        mid = (mid[0] + math.cos(ang + 1.5) * 1.2, mid[1] + math.sin(ang + 1.5) * 1.2)
        tw_ = lerp2(q_, tip, 0.5)
        twig = (tw_[0] + math.cos(ang + 0.9) * ln * 0.4, tw_[1] + math.sin(ang + 0.9) * ln * 0.4)
        brp = ik.union(ik.taper_path([cv.W(q_), cv.W(mid), cv.W(tip)], cv.u(w * 2), prof=lambda u: max(0.35, 1.0 - 0.6 * u)),
                       ik.taper_path([cv.W(tw_), cv.W(twig)], cv.u(w * 0.9), (0.0, 0.9)))
        nx, ny = -math.sin(ang) * w * 0.45, math.cos(ang) * w * 0.45
        brp = ik.union(brp, cv.blob([(tip[0] + nx, tip[1] + ny), (tip[0] + math.cos(ang) * 1.8 + nx * 0.4, tip[1] + math.sin(ang) * 1.8 + ny * 0.4, 0.0),
                                     (tip[0], tip[1]), (tip[0] + math.cos(ang) * 1.2 - nx * 0.6, tip[1] + math.sin(ang) * 1.2 - ny * 0.6, 0.0), (tip[0] - nx, tip[1] - ny)]))
        cv.shape(brp, BB if j != 1 else B, z=15 + j * 0.01, sd=1.2, hi=0.35,
                 details=[('ink', [lerp2(q_, tip, 0.1), lerp2(q_, tip, 0.5), lerp2(q_, tip, 0.85)], 0.9, (0.3, 0.5))])
        if 'embers' in ex:
            cv.fill(cv.ellipse(tip, 0.9, 0.9), V['crack_hot'], z=15.2, glow=V['crack_glow'])
            yk.glow_soft(cv, tip, 2.5, V['crack_glow'], z=15.3, alpha=0.5)
        if j == 1 and V['caput']:
            for k_, col in enumerate(V['caput'][:2]):
                qq = lerp2(q_, tip, 0.6 + k_ * 0.15)
                sw = math.sin(ph + k_ * 2) * 0.5 - p['rag']
                cv.shape(ik.taper_path([cv.W(qq), cv.W(_hang(qq, -1.0 + sw, 3.0, comp_t)), cv.W(_hang(qq, -2.0 + sw * 2, 6.5, comp_t))], cv.u(1.5), (0.05, 0.5)),
                         Ink(col), z=15.3 + k_ * 0.01, sd=0.4, ol=0.7)
    # ---- sırt örtüsü (yosun / ot / su yosunu / kar / kül), alt kenarı saçaklı
    top, bot = [], []
    for i in range(9):
        t = i / 8
        q_ = lerp2((hip[0] - 6, hip[1] + 2), (sh[0] + 4, sh[1] - 2), t)
        bump = math.sin(t * math.pi)
        topy = q_[1] - 12.0 - bump * (8.5 + arch * 2.2)
        q_ = (q_[0] - arch * 0.8 * bump, q_[1])
        top.append((q_[0] - bump * 1.5 + math.sin(i * 2.3) * 0.6, topy + 1.0 - (i % 3 == 1) * 1.0))
        bot.append((q_[0] - bump * 1.5 + (1.5 if i % 2 else -1.0), topy + 9 + (i % 2) * 4.5 + bump * 2.0, 0.0 if i % 2 else 1.0))
    mdet = []
    for i in range(1, 8):
        q_ = top[i]
        mdet.append(('stroke', [(q_[0] + 0.5, q_[1] + 1.5), (q_[0] + 1.5, q_[1] + 4.0)], 1.6, BK.hi, (0.2, 0.7)))
    tt = []
    for i in range(len(top) - 1):
        q0, q1 = top[i], top[i + 1]
        tt.append(q0)
        m = lerp2(q0, q1, 0.5)
        dx, dy = q1[0] - q0[0], q1[1] - q0[1]
        L_ = math.hypot(dx, dy) or 1
        tt.append((m[0] + dy / L_ * 1.6, m[1] - dx / L_ * 1.6, 0.0))
    tt.append(top[-1])
    hug = ik.union(body, ik.moved(body, 0, -cv.u(2.2)), ik.moved(body, -cv.u(1.2), -cv.u(1.2)))
    cv.shape(ik.isect(cv.blob(tt + bot[::-1]), hug), BK, z=26, sd=2.4, hi=0.6, details=mdet, fur=1.3, soft=0.3, cast=0.8)
    for i in list(range(1, 8, 2)) + [2, 6]:   # sarkan saçaklar (dünya aşağısına, gecikmeli salınım)
        q_ = bot[i]
        L = (5 + (i * 7) % 6) * (1.6 if bk in ('weed', 'grass') else 1.0)
        sw = math.sin(ph + i) * 0.8 - p['rag'] * 1.6
        pts = [(q_[0], q_[1] - 1), _hang(q_, -0.4 + sw * 0.5, L * 0.5, comp_t), _hang(q_, -0.8 + sw, L, comp_t)]
        if bk == 'snow':
            yk.icicles(cv, [q_], V['horn'], 25.5, L=L * 0.7, w=0.9, seed=i)
            continue
        if bk == 'ash':
            cv.fill(cv.ellipse(pts[-1], 0.55, 0.55), V['crack_hot'], z=25.5, glow=V['crack_glow'])
        cv.shape(ik.taper_path([cv.W(r_) for r_ in pts], cv.u(1.8), (0.0, 0.85)), BK, z=25 + i * 0.01, sd=0.7, ol=0.8)
    if bk in ('moss', 'weed'):   # mantarlar / midyeler sırtta
        for j, t in enumerate((0.3, 0.55)):
            q_ = lerp2(top[2], top[6], t)
            q_ = (q_[0], q_[1] + 1.0)
            S = V['shroom']
            cap = cv.blob([(q_[0] - 2.2, q_[1]), (q_[0] - 1.6, q_[1] - 1.6), (q_[0], q_[1] - 2.3), (q_[0] + 1.6, q_[1] - 1.6), (q_[0] + 2.2, q_[1]), (q_[0], q_[1] + 0.5)])
            cv.shape(cv.capsule((q_[0], q_[1]), (q_[0] + 0.2, q_[1] + 2.0), 0.6, 0.7), Ink('#e8dcc4'), z=27 + j * 0.1, sd=0.4, ol=0.7)
            cv.shape(cap, S, z=27.05 + j * 0.1, sd=0.9, hi=0.35, ol=0.8,
                     details=[('col', cv.ellipse((q_[0] - 0.6, q_[1] - 1.3), 0.45, 0.35), S.hi)])
    if 'flames' in ex:   # omuz ve sırtta alev dilleri: kıvrık S dil, dışı kızıl içi sarı
        for j, t in enumerate((0.2, 0.5, 0.8)):
            q_ = lerp2(top[1], top[7], t)
            hgt = 7.0 + 2.5 * math.sin(ph * 2 + j * 2.1) + flare * 3.0
            wv = math.sin(ph * 3 + j * 1.3) * 1.2 + p['rag']

            def tongue(sc, q=q_, hgt=hgt, wv=wv):
                return cv.blob([(q[0] - 2.2 * sc, q[1] + 1.0), (q[0] - 2.0 * sc + wv * 0.3, q[1] - hgt * 0.35 * sc), (q[0] - 0.6 * sc + wv, q[1] - hgt * 0.7 * sc),
                                (q[0] - 1.6 + wv * 1.6, q[1] - hgt * sc, 0.0), (q[0] + 0.8 * sc + wv * 0.6, q[1] - hgt * 0.55 * sc), (q[0] + 2.0 * sc, q[1] - hgt * 0.2 * sc),
                                (q[0] + 2.2 * sc, q[1] + 1.0)])
            cv.fill(tongue(1.0), (0.95, 0.3, 0.06), z=27 + j * 0.1, glow=(1.0, 0.35, 0.02))
            cv.fill(tongue(0.6), (1.0, 0.82, 0.3), z=27.05 + j * 0.1, glow=(1.0, 0.75, 0.25))
            yk.glow_soft(cv, (q_[0], q_[1] - hgt * 0.4), 4.0, (1.0, 0.4, 0.02), z=27.2, blur=0.6, alpha=0.45)
    if 'embers' in ex:
        yk.sparks(cv, (sh[0] - 4, sh[1] - 16), 6, 2.0, 9.0, V['crack_hot'], 28, seed=int(ph * 10) + 3, w=1.1, glow=V['crack_glow'], ang=-math.pi / 2, spread=1.4)

    # ---- baş grubu: boyun dibinde döner (hr: + aşağı), önden gider (hd)
    hdx, hdy = p['hd']
    hr = p['hr']
    nb = (sh[0] + 3, sh[1] - 1)
    hx, hy = sh[0] + 14 + hdx, sh[1] + 2 + hdy - roar * 3
    neck_end = yg.rot_about((hx - 2, hy + 1), nb, hr)
    neck = cv.capsule(nb, neck_end, 6.0, 4.0)
    cv.shape(neck, B, z=20, sd=2.5, hi=0.4, details=_grooves(nb, neck_end, 5.0, 3, 41, 1.2, V))
    yg.xf_push(cv, nb, hr)
    comp_h = comp_t - hr
    hk = V['horn_kind']
    if hk == 'antler':
        _antler(cv, (hx - 3.5, hy - 4.0), -2.3 - roar * 0.15, 24, V['horn'] if V['horn'] is not BONE else Ink('#b4a68e', '#665848', '#d4c8b0', '#3a3028'), 6,
                r0=1.7, curve=0.3, seed=1, V=V)
    elif hk == 'crystal':
        _antler(cv, (hx - 3.0, hy - 4.0), -2.3, 16, V['horn'], 6, r0=1.4, seed=2, kind='crystal', V=V)
    jaw = 1.0 + roar * 4.0
    S = V['skull']
    fl = flare + p['eye']
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
        if fl > -0.5:
            for dx_ in (2.6, 7.6):
                yk.eye_glow(cv, (hx + dx_, hy - 1.0), 0.9 + fl * 0.3, 0.45 + fl * 0.15, 0.0, V['eye'], V['crack_glow'], 46)
        yk.icicles(cv, [(hx + 2, hy + 7.6 + jd * 0.6), (hx + 5, hy + 8.2 + jd * 0.8), (hx + 8, hy + 8.3 + jd)], V['horn'], 29.7, L=2.6, w=0.8, seed=12)
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
        if fl > -0.5:   # eye < 0: göz alevi söner (ölüm)
            yk.eye_glow(cv, (hx + 1.6, hy - 0.7), max(0.2, 1.0 + fl * 0.4), max(0.15, 0.8 + fl * 0.3), 0.2, V['eye'], V['crack_glow'], 46)
            if fl > 0.7:   # "!!": gözden sızan alev izi
                cv.stroke([(hx + 2.4, hy - 0.8), (hx - 2.6 - fl * 1.5, hy - 2.0 - fl * 0.8)], 0.9 + fl * 0.4, z=46.5, col=V['eye'], taper=(0.1, 0.9),
                          glow=V['crack_glow'])
    if hk == 'antler':
        r_ = _antler(cv, (hx - 1.0, hy - 4.6), -2.05 - roar * 0.15, 29, V['horn'], 34, r0=2.0, curve=0.28, seed=3, V=V)
        if V['caput'] and r_:
            pts_, tips = r_
            for j, (q_, col) in enumerate(zip([lerp2(pts_[1], pts_[2], 0.5), lerp2(pts_[2], pts_[3], 0.5), tips[1]], V['caput'])):
                sw = math.sin(ph + j * 1.9) * 0.4 - p['rag'] * (0.8 + j * 0.25)
                cv.shape(ik.taper_path([cv.W(q_), cv.W(_hang(q_, -0.8 + sw, 3.0, comp_h)), cv.W(_hang(q_, -1.6 + sw * 2, 6.0 + j, comp_h))], cv.u(1.4), (0.05, 0.5)),
                         Ink(col), z=35 + j * 0.01, sd=0.4, ol=0.7)
                cv.shape(cv.ellipse(q_, 0.9, 0.7), Ink(col), z=35.1 + j * 0.01, sd=0.3, ol=0.6)
    elif hk == 'ram':
        _ram(cv, (hx - 0.5, hy - 1.0), V['horn'], 34, roar, size=0.62)
    elif hk == 'crystal':
        _antler(cv, (hx + 1.5, hy - 5.0), -1.9, 20, V['horn'], 34, r0=1.7, seed=4, kind='crystal', V=V)
    cv.pop()   # baş

    # ---- ön kol: uzun, ağır; omuzda örtü, ön kolda çatlak, kök pençeli yumruk
    ar = p['ar']
    shf = (sh[0] + 1 + tw, sh[1] + 3)
    a1f = ar[0] + pitch
    e, h = _arm_pts(shf, a1f, ar[1])
    a = a1f + ar[1]
    fist = cv.ellipse(h, 5.0, 4.6)
    claws = _claws(cv, h, a, 5.0, 1.0 + 0.7 * p['cl'], 9.0 * (1.0 + 0.2 * p['cl']), 3.6)
    arm = ik.union(cv.limb([shf, lerp2(shf, e, 0.45), e, lerp2(e, h, 0.5), h], [6.5, 6.8, 5.2, 4.8, 4.4]), fist, *claws)
    det = _grooves(shf, e, 6.0, 4, 51, 1.3, V) + _grooves(e, h, 4.8, 3, 52, 1.2, V)
    det.append(('ink', [along(e, shf, 0.08, -4.5), e, along(e, h, 0.08, 4.5)], 1.6, (0.3, 0.3)))
    cv.shape(arm, B, z=50, sd=3.4, hi=0.6, details=det, hatch=0.35, bounce=0.3)
    m1, m2 = lerp2(e, h, 0.15), lerp2(e, h, 0.75)
    _crack(cv, [m1, (lerp2(m1, m2, 0.5)[0] + 1.2, lerp2(m1, m2, 0.5)[1]), m2], V, 62, 1.2 + max(0.0, flare) * 0.7)
    if flare > 0:
        yk.glow_soft(cv, h, 7.0, V['crack_glow'], z=62.5, blur=0.6, alpha=0.4 * min(1.0, flare))
    pad = cv.blob([(shf[0] - 7.5, shf[1] - 1.5), (shf[0] - 4.0, shf[1] - 6.5), (shf[0] + 3.0, shf[1] - 6.8), (shf[0] + 7.0, shf[1] - 2.0),
                   (shf[0] + 4.5, shf[1] + 1.5, 0.0), (shf[0] + 1.5, shf[1] + 0.2), (shf[0] - 1.5, shf[1] + 2.4, 0.0), (shf[0] - 4.5, shf[1] + 0.5)])
    cv.shape(pad, BK, z=58, sd=1.8, hi=0.5, fur=1.0, soft=0.3)
    if bk in ('moss', 'weed', 'grass'):
        for j, dx_ in enumerate((-5.0, -1.0, 3.5)):
            q_ = (shf[0] + dx_, shf[1] + 0.8 + (j % 2) * 1.2)
            L = 4.0 + j * 1.5 if bk != 'weed' else 7.0 + j * 2
            sw = math.sin(ph + j) * 0.6 - p['rag'] * 1.2
            cv.shape(ik.taper_path([cv.W(q_), cv.W(_hang(q_, sw * 0.5, L * 0.5, comp_t)), cv.W(_hang(q_, sw, L, comp_t))], cv.u(1.6), (0.0, 0.85)),
                     BK, z=57.5 + j * 0.01, sd=0.6, ol=0.8)
    if 'drips' in ex:   # su damlaları
        for j, q_ in enumerate((h, lerp2(e, h, 0.5), (cc[0] + 4, cc[1] + 12))):
            d = _hang(q_, 0.5, 5.5 + ((ph * 1.5 + j) % 2.0), comp_t)
            cv.shape(cv.blob([(d[0], d[1] - 1.6, 0.0), (d[0] + 0.8, d[1] + 0.2), (d[0], d[1] + 0.9), (d[0] - 0.8, d[1] + 0.2)]),
                     Ink('#9fe8e0', '#3a8a96', '#ffffff'), z=63 + j * 0.01, sd=0.4, hi=0.25, ol=0.6, glow=(0.05, 0.3, 0.3))
    if 'ice' in ex:
        yk.icicles(cv, [along(shf, e, 0.6, -5.5), along(shf, e, 0.85, -5.0), along(e, h, 0.4, -4.0)], V['horn'], 59, L=3.5, w=1.0, seed=11)
    hand = yg.world(cv, h)
    cv.pop()   # gövde
    if 'dust' in ex:   # öndeki toz teli (kolu sarar)
        dust = Ink('#d2b88a', '#866c4e', '#f2e2bc', name='toz')
        yk.wisp(cv, (hip[0] - 12, -4.0), -0.25, 40, 3.2, dust, 64, ph=ph + 0.6, curl=0.3, alpha=0.45, ink=True)
    cv.pop()   # ezilme / aynalama
    cv.pop()   # figür
    _ground_fx(cv, p, V)
    return {'hand': hand}


SHADE = dict(outer=0.6, rim=0.7, rim_col=(0.68, 0.76, 1.0), rim_dir=(0.6, -0.8), rim_w=1.6, form=(7.0, (0.74, 0.72, 0.86)))


# ====================================================================== anahtar pozlar (yaratik_govde.Seq)
# Ağırlık dili: her şey yavaş kalkar, uzun tutulur, ani ve ağır iner (yere çarpışta ezilme + toprak); baş hep önden gider,
# çaputlar / yosun saçakları gövdenin ardından gecikmeyle savrulur (rag). "!!" hazırlıkları daha geniş / alçak duruş,
# kabaran kambur (arch), açık çene (roar) ve alev alan çatlak / göz (flare).
def _foot_cycle(phi, home, S, duty, lift, toe_up=0.35, toe_push=0.3):
    """Döngüsel ayak yolu: basma (duty) boyunca +S/2 -> -S/2 (sabit hız), salınımda yayla öne (yükseklik lift)."""
    phi %= 1.0
    if phi < duty:
        u = phi / duty
        return (home + S * (0.5 - u), 0.0, toe_push * max(0.0, (u - 0.7) / 0.3))
    u = (phi - duty) / (1.0 - duty)
    e = u * u * (3 - 2 * u)
    return (home - S * 0.5 + S * e, lift * math.sin(math.pi * u) ** 0.8, toe_up * math.sin(math.pi * min(1.0, u * 1.2)))


WALK_S, WALK_DUTY = 16.0, 0.62


def _walk(t):
    """Ağır yürüyüş (t=0 yakın ayak basar): basışta gövde çöker (ezilme), kalkışta toparlanır; kollar karşı salınır."""
    p = {'lf': _foot_cycle(t, 2.0, WALK_S, WALK_DUTY, 6.0), 'lb': _foot_cycle(t - 0.5, -8.0, WALK_S, WALK_DUTY, 5.0)}
    c2 = math.cos((t - 0.07) * 4 * math.pi)          # her basıştan hemen sonra çöküş
    s1 = math.sin(t * 2 * math.pi)
    c1 = math.cos(t * 2 * math.pi)
    stomp = max(0.0, c2) ** 3
    p.update(y=0.8 + 1.5 * c2, x=0.5 * c1, sq=0.35 * stomp, pitch=0.08 + 0.03 * math.cos((t - 0.15) * 4 * math.pi),
             tw=1.6 * c1, al=(0.2 + 0.42 * c1, 0.3 + 0.12 * max(0.0, c1)), ar=(0.25 - 0.45 * c1, 0.18 + 0.15 * max(0.0, -c1)),
             hd=(0.6 * s1, 1.2 * max(0.0, math.cos((t - 0.14) * 4 * math.pi))), hr=0.04 + 0.05 * math.cos((t - 0.12) * 4 * math.pi),
             rag=0.6 + 0.35 * math.sin((t - 0.2) * 4 * math.pi), ph=t * math.tau, br=0.3 * c2,
             pf=0.0)
    for ft, k in ((0.0, 'lf'), (0.5, 'lb')):           # basış tozu (ilk iki karede)
        dt = (t - ft) % 1.0
        if dt < 0.2:
            p['pf'] = 1.0 - dt / 0.2
            p['pf_x'] = p[k][0] + (2.0 if k == 'lf' else 0.0)
    return p


def _idle_proc(p, t):
    """Bekleme: ağır nefes (göğüs ve kambur kalkar), çatlak nabzı, çaput / yosun salınımı."""
    p = dict(p)
    b = math.sin(t * math.tau)
    p['br'] = p.get('br', 0.0) + 0.9 * b
    p['y'] = p.get('y', 0.0) - 0.7 * b + 0.3
    p['arch'] = p.get('arch', 0.0) + 0.25 * b
    p['flare'] = p.get('flare', 0.0) + 0.12 + 0.12 * math.sin(t * math.tau * 2 - 0.8)
    p['rag'] = p.get('rag', 0.0) + 0.25 * math.sin(t * math.tau - 1.2)
    p['ph'] = t * math.tau
    al, ar = p.get('al', REST['al']), p.get('ar', REST['ar'])
    p['al'] = (al[0] + 0.04 * math.sin(t * math.tau - 0.9), al[1])
    p['ar'] = (ar[0] + 0.05 * math.sin(t * math.tau - 0.7), ar[1] + 0.04 * b)
    return p


SEQS = {}

# ---- bekleme (10 kare, 1,7 sn): ağır nefes, ortada başını yana eğip kafatasını sarsar (tik), çaputlar savrulur
SEQS['idle'] = Seq([
    (0.0, dict(hr=0.0, hd=(0.0, 0.0)), 'io'),
    (0.3, dict(hr=0.04, hd=(0.4, 0.6), x=0.3), 'io'),
    (0.5, dict(hr=-0.2, hd=(-0.6, -1.0), roar=0.35, x=0.0, rag=-0.5, eye=0.3), 'o'),
    (0.6, dict(hr=0.12, hd=(0.8, 0.8), roar=0.15, rag=0.6, eye=0.2), 'io'),
    (0.72, dict(hr=-0.06, hd=(0.2, 0.0), rag=-0.2), 'io'),
    (1.0, dict(hr=0.0, hd=(0.0, 0.0)), 'io'),
], n=10, fps=6, loop=True, proc=_idle_proc, rest=REST)

# ---- yürüyüş (8 kare, 1 sn, adım 16): vx 25,8 birim/sn'de 1x (agac_iyesi hızı 30, dev_cocugu 40)
SEQS['walk'] = Seq([(i / 16, _walk(i / 16), 'l') for i in range(17)], n=8, fps=8, loop=True, rest=REST,
                   extra={'vx': round(WALK_S / WALK_DUTY, 1)})

# ---- dönüş (4 kare, 0,4 sn — yavaş dönen dev): gövde eski yöne bakar (aynalı), daralarak döner, ağır oturur
SEQS['turn'] = Seq([
    (0.0, dict(sx=-0.75, pitch=0.12, y=1.5, hd=(-1.0, 1.0), hr=0.1, rag=-0.8, al=(0.4, 0.3), ar=(-0.1, 0.3), lf=(-1.0, 0.0, 0.0), lb=(-9.0, 2.5, 0.2)), 'l'),
    (0.4, dict(sx=0.5, pitch=0.18, y=2.5, hd=(2.0, 1.5), hr=0.05, rag=0.9, al=(0.5, 0.3), ar=(0.5, 0.3), lf=(1.5, 3.0, 0.2), lb=(-9.0, 0.0, 0.0)), 'l'),
    (0.75, dict(sx=0.92, pitch=0.12, y=2.0, sq=0.5, hd=(1.0, 1.0), rag=0.6, al=(0.3, 0.3), ar=(0.4, 0.2), lf=(1.0, 0.0, 0.0), lb=(-10.0, 0.0, 0.0), pf=0.8, pf_x=1.0), 'o'),
    (1.0, dict(sx=1.0, y=0.4, rag=0.2), 'o'),
], frames=[0.0, 0.4, 0.75, 1.0], fps=10, rest=REST)

# ---- ters tokat "!" (swat; hazırlık 3 + vuruş 3 + toparlanma 3): kollarını göğsünde toplayıp gövdeyi burar,
# sonra iki kolu iki yana fırlatan ani açılış (ön kol arkaya, arka kol öne: iki yanı birden süpürür)
SW_COIL = dict(y=3.0, pitch=0.28, tw=3.0, arch=0.6, al=(1.25, 1.5), ar=(1.45, 1.75), hr=0.15, hd=(1.0, 2.0), roar=0.35, flare=0.45, rag=-0.4,
               lf=(1.0, 0.0, 0.0), lb=(-12.0, 0.0, 0.0), cl=0.6)
SEQS['swat'] = Seq([
    (0.0, dict(y=1.0, pitch=0.1, al=(0.5, 0.6), ar=(0.7, 0.8), roar=0.1, flare=0.2), 'o'),
    (0.16, dict(SW_COIL), 'o'),
    (0.26, dict(SW_COIL, y=3.6, pitch=0.32, tw=3.4, al=(1.3, 1.6), ar=(1.5, 1.85), roar=0.5, flare=0.55), 'io'),
    (0.34, dict(y=2.0, pitch=0.05, tw=-1.0, al=(1.9, 0.4), ar=(0.6, 0.6), roar=0.8, flare=0.7, hr=-0.05, rag=0.2,
                lf=(1.0, 0.0, 0.0), lb=(-12.0, 0.0, 0.0), cl=1.0), 'i'),
    # temas: iki kol yatay iki yana (ön -> arka, arka -> ön)
    (0.42, dict(y=1.0, pitch=-0.16, tw=-3.5, sq=-0.3, al=(1.62, 0.05), ar=(-1.52, -0.1), roar=1.0, flare=0.8, hr=-0.15, hd=(-1.0, -0.5), rag=1.0,
                lf=(2.0, 0.0, 0.0), lb=(-12.0, 0.0, 0.3), cl=1.0), 'i'),
    (0.52, dict(y=1.5, pitch=-0.2, tw=-3.8, al=(2.1, 0.2), ar=(-2.0, -0.2), roar=0.9, flare=0.7, hr=-0.18, hd=(-1.2, -0.5), rag=1.3,
                lf=(2.0, 0.0, 0.0), lb=(-12.0, 0.0, 0.3), cl=0.8), 'o'),
    (0.64, dict(y=2.2, pitch=-0.08, tw=-2.6, al=(1.2, 0.5), ar=(-1.1, 0.2), roar=0.6, flare=0.5, hr=-0.05, rag=0.6,
                lf=(2.0, 0.0, 0.0), lb=(-12.0, 0.0, 0.0), cl=0.5), 'o'),
    (0.8, dict(y=1.6, pitch=0.06, tw=-0.8, al=(0.4, 0.4), ar=(-0.2, 0.3), roar=0.3, flare=0.3, rag=-0.3, lf=(1.0, 0.0, 0.0), lb=(-11.0, 0.0, 0.0)), 'io'),
    (1.0, dict(y=0.4, al=(0.14, 0.24), ar=(0.2, 0.14), flare=0.1), 'o'),
], frames=[(0.0, 0.0), (0.16, 0.25), (0.34, 0.0),
           (0.42, 0.0), (0.52, 0.3), (0.64, 0.65),
           (0.72, 0.0), (0.84, 0.4), (1.0, 0.75)],
    seg=[('windup', 3), ('strike', 3), ('recover', 3)], lead={'windup': 0.05}, rest=REST, fps=10)

# ---- çift yumruk yer ezişi "!!" (slam; hazırlık 4 + vuruş 3 + toparlanma 3): iki yumruğu başının üstüne kaldırır, geriye
# kavislenip kükrer (derin kurulma, uzun tutulur), sonra bütün ağırlığıyla öne çöküp yeri döver
SL_HOLD = dict(y=-1.8, pitch=-0.3, arch=-0.6, sq=-0.35, al=(3.75, 0.5), ar=(3.3, 0.4), hr=-0.3, hd=(-1.0, -1.5), roar=1.0, flare=1.0,
               rag=-0.9, lf=(5.0, 0.0, 0.0), lb=(-15.0, 0.0, 0.2), cl=0.3, br=1.0)
SEQS['slam'] = Seq([
    (0.0, dict(y=3.0, pitch=0.18, arch=0.8, al=(0.9, 0.9), ar=(1.1, 1.0), roar=0.3, flare=0.5, hr=0.1, lf=(3.0, 0.0, 0.0), lb=(-13.0, 0.0, 0.0)), 'o'),
    (0.12, dict(y=0.5, pitch=-0.1, arch=0.0, al=(2.8, 0.8), ar=(2.3, 0.7), roar=0.7, flare=0.8, hr=-0.15, rag=-0.5,
                lf=(5.0, 0.0, 0.0), lb=(-15.0, 0.0, 0.1), br=0.6), 'o'),
    (0.22, dict(SL_HOLD), 'o'),
    (0.3, dict(SL_HOLD, y=-2.2, pitch=-0.34, al=(3.82, 0.45), ar=(3.38, 0.36)), 'io'),
    (0.36, dict(y=0.5, pitch=0.3, arch=0.4, al=(1.9, 0.15), ar=(2.0, 0.1), hr=0.1, hd=(1.5, 1.0), roar=1.0, flare=1.0, rag=0.3,
                lf=(5.0, 0.0, 0.0), lb=(-15.0, 0.0, 0.2), cl=0.2), 'i'),
    # temas: yumruklar gövdenin ~40 birim önünde yerde, gövde çöker
    (0.42, dict(y=7.0, pitch=0.56, arch=0.6, sq=0.8, al=(0.82, -0.05), ar=(0.74, -0.05), hr=-0.3, hd=(2.0, 2.5), roar=0.9, flare=1.0, rag=1.4,
                lf=(5.0, 0.0, 0.0), lb=(-15.0, 0.0, 0.4), cl=0.0, dirt=0.05, dirt_x=42.0), 'i'),
    (0.5, dict(y=8.0, pitch=0.58, arch=0.7, sq=0.55, al=(0.84, -0.05), ar=(0.76, -0.05), hr=-0.26, hd=(2.0, 3.0), roar=0.7, flare=0.9, rag=1.0,
               lf=(5.0, 0.0, 0.0), lb=(-15.0, 0.0, 0.4), dirt=0.4, dirt_x=42.0), 'o'),
    (0.6, dict(y=7.5, pitch=0.55, arch=0.6, sq=0.3, al=(0.85, -0.02), ar=(0.77, -0.02), hr=-0.2, hd=(1.8, 2.6), roar=0.5, flare=0.7, rag=0.4,
               lf=(5.0, 0.0, 0.0), lb=(-15.0, 0.0, 0.3), dirt=0.8, dirt_x=42.0), 'o'),
    (0.74, dict(y=5.0, pitch=0.42, arch=0.5, al=(0.75, 0.3), ar=(0.65, 0.35), hr=0.2, hd=(1.0, 1.5), roar=0.3, flare=0.5, rag=-0.2,
                lf=(4.0, 0.0, 0.0), lb=(-14.0, 0.0, 0.1)), 'io'),
    (0.87, dict(y=2.5, pitch=0.18, arch=0.3, al=(0.3, 0.35), ar=(0.35, 0.25), hr=0.08, roar=0.35, flare=0.3, br=0.8, rag=-0.4,
                lf=(2.5, 0.0, 0.0), lb=(-12.0, 0.0, 0.0)), 'io'),
    (1.0, dict(y=0.4, al=(0.14, 0.24), ar=(0.24, 0.14), flare=0.12), 'o'),
], frames=[(0.0, 0.0), (0.12, 0.14), (0.24, 0.36), (0.36, 0.0),
           (0.42, 0.0), (0.5, 0.3), (0.6, 0.65),
           (0.74, 0.0), (0.87, 0.4), (1.0, 0.78)],
    seg=[('windup', 4), ('strike', 3), ('recover', 3)], lead={'windup': 0.05}, rest=REST, fps=10)

# ---- sıçrayıp ezme "!!" (leap; hazırlık 3 + havada 3 [dikey hız] + iniş ezişi 3 + toparlanma 2): derin çömelme, kollar
# geride; fırlayış; havada iki yumruk başın üstünde, dizler karına; inişte bütün kütleyle yere çakılır
LP_CROUCH = dict(y=9.0, pitch=0.42, arch=1.0, al=(-0.9, 0.5), ar=(-0.75, 0.45), hr=0.25, hd=(2.0, 2.5), roar=0.8, flare=0.9, rag=-0.6,
                 lf=(4.0, 0.0, 0.0), lb=(-14.0, 0.0, 0.3), cl=0.4, sq=0.4)
SEQS['leap'] = Seq([
    (0.0, dict(y=3.0, pitch=0.2, arch=0.5, al=(-0.2, 0.4), ar=(-0.1, 0.4), roar=0.4, flare=0.6, lf=(3.0, 0.0, 0.0), lb=(-12.0, 0.0, 0.0)), 'o'),
    (0.1, dict(LP_CROUCH), 'o'),
    (0.17, dict(LP_CROUCH, y=10.0, pitch=0.46, roar=1.0, flare=1.0), 'io'),
    (0.22, dict(y=-3.0, pitch=-0.05, sq=-0.6, al=(2.95, 0.35), ar=(2.45, 0.3), hr=-0.15, roar=1.0, flare=1.0, rag=1.2,
                lf=(6.0, 0.0, 0.5), lb=(-16.0, 3.0, 0.7)), 'i'),
    # havada (u: vy): kalkış, tepe, düşüş
    (0.36, dict(y=-4.0, pitch=-0.1, sq=-0.4, al=(3.5, 0.4), ar=(3.1, 0.35), hr=-0.2, roar=1.0, flare=1.0, rag=1.2,
                lf=(4.0, 6.0, 0.6), lb=(-14.0, 10.0, 0.8)), 'o'),
    (0.46, dict(y=-6.0, pitch=-0.2, arch=-0.3, al=(3.8, 0.45), ar=(3.35, 0.4), hr=-0.25, hd=(-0.5, -1.0), roar=1.0, flare=1.0, rag=0.2,
                lf=(6.0, 12.0, 0.5), lb=(-10.0, 14.0, 0.7)), 'io'),
    (0.56, dict(y=-3.0, pitch=0.25, arch=0.3, al=(2.5, 0.2), ar=(2.0, 0.15), hr=-0.05, hd=(1.5, 1.0), roar=1.0, flare=1.0, rag=-1.0,
                lf=(5.0, 4.0, 0.2), lb=(-13.0, 5.0, 0.3)), 'i'),
    # iniş ezişi (slam/leap; temas ilk kare)
    (0.64, dict(y=11.0, pitch=0.56, arch=0.9, sq=1.0, al=(0.76, -0.05), ar=(0.66, -0.05), hr=-0.3, hd=(2.0, 3.0), roar=0.9, flare=1.0, rag=1.6,
                lf=(6.0, 0.0, 0.0), lb=(-16.0, 0.0, 0.3), dirt=0.05, dirt_x=34.0, pf=1.0, pf_x=-6.0), 'i'),
    (0.72, dict(y=11.5, pitch=0.56, arch=0.9, sq=0.6, al=(0.78, -0.05), ar=(0.68, -0.05), hr=-0.26, hd=(2.0, 3.2), roar=0.7, flare=0.9, rag=1.0,
                lf=(6.0, 0.0, 0.0), lb=(-16.0, 0.0, 0.3), dirt=0.45, dirt_x=34.0, pf=0.6, pf_x=-6.0), 'o'),
    (0.82, dict(y=9.5, pitch=0.52, arch=0.8, sq=0.3, al=(0.78, 0.0), ar=(0.68, 0.0), hr=-0.2, hd=(1.8, 2.8), roar=0.5, flare=0.7, rag=0.3,
                lf=(6.0, 0.0, 0.0), lb=(-16.0, 0.0, 0.2), dirt=0.85, dirt_x=34.0), 'o'),
    # toparlanma
    (0.91, dict(y=5.0, pitch=0.35, arch=0.6, al=(0.6, 0.4), ar=(0.5, 0.4), hr=0.15, hd=(1.0, 1.5), roar=0.3, flare=0.4, rag=-0.3,
                lf=(4.0, 0.0, 0.0), lb=(-13.0, 0.0, 0.0)), 'io'),
    (1.0, dict(y=1.2, pitch=0.08, al=(0.2, 0.3), ar=(0.25, 0.2), flare=0.15, br=0.6), 'o'),
], frames=[(0.0, 0.0), (0.12, 0.2), (0.22, 0.0),
           (0.36, 0.0), (0.46, 0.35), (0.56, 0.68),
           (0.64, 0.0), (0.72, 0.3), (0.82, 0.62),
           (0.91, 0.0), (1.0, 0.5)],
    seg=[('windup', 3), ('air', 3), ('strike', 3), ('recover', 2)], lead={'windup': 0.05}, rest=REST, fps=10)

# ---- kök fışkırtma "!" (roots; hazırlık 3 + vuruş 2 + toparlanma 2): pençelerini açıp göğe kaldırır, sonra ikisini birden
# önündeki toprağa saplar (çatlaklar parlar); kökler oyuncunun altından çıkar
RT_UP = dict(y=-0.5, pitch=-0.15, arch=0.2, al=(2.55, -0.5), ar=(2.7, -0.55), hr=-0.2, hd=(-0.5, -1.0), roar=0.7, flare=0.7, rag=-0.6, cl=1.0,
             lf=(4.0, 0.0, 0.0), lb=(-13.0, 0.0, 0.1), br=0.8)
SEQS['roots'] = Seq([
    (0.0, dict(y=2.0, pitch=0.12, al=(0.9, 0.7), ar=(1.0, 0.8), roar=0.2, flare=0.35, cl=0.6), 'o'),
    (0.18, dict(RT_UP), 'o'),
    (0.32, dict(RT_UP, y=-1.0, pitch=-0.2, al=(2.65, -0.55), ar=(2.8, -0.6), roar=0.9, flare=0.85), 'io'),
    (0.4, dict(y=3.5, pitch=0.4, al=(1.0, 0.0), ar=(0.95, 0.0), hr=0.2, roar=0.9, flare=0.9, rag=0.4, cl=1.0, lf=(4.0, 0.0, 0.0), lb=(-13.0, 0.0, 0.1)), 'i'),
    # temas: pençeler toprakta (ayakların ~24 birim önü)
    (0.48, dict(y=8.5, pitch=0.78, arch=0.8, sq=0.5, al=(0.42, -0.25), ar=(0.36, -0.3), hr=-0.15, hd=(2.0, 2.0), roar=1.0, flare=1.0, rag=1.3, cl=1.0,
                lf=(5.0, 0.0, 0.0), lb=(-14.0, 0.0, 0.3), dirt=0.08, dirt_x=26.0), 'i'),
    (0.62, dict(y=9.5, pitch=0.8, arch=0.9, sq=0.3, al=(0.42, -0.3), ar=(0.36, -0.35), hr=-0.1, hd=(2.0, 2.5), roar=0.8, flare=1.0, rag=0.5, cl=1.0,
                lf=(5.0, 0.0, 0.0), lb=(-14.0, 0.0, 0.3), dirt=0.55, dirt_x=26.0), 'o'),
    (0.8, dict(y=5.0, pitch=0.45, arch=0.5, al=(0.6, 0.5), ar=(0.55, 0.55), hr=0.2, roar=0.4, flare=0.5, rag=-0.3, cl=0.5,
               lf=(4.0, 0.0, 0.0), lb=(-13.0, 0.0, 0.0)), 'io'),
    (1.0, dict(y=0.8, al=(0.15, 0.25), ar=(0.24, 0.16), flare=0.15), 'o'),
], frames=[(0.0, 0.0), (0.2, 0.25), (0.4, 0.0),
           (0.48, 0.0), (0.62, 0.4),
           (0.8, 0.0), (1.0, 0.55)],
    seg=[('windup', 3), ('strike', 2), ('recover', 2)], lead={'windup': 0.05}, rest=REST, fps=10)


# ---- zırhlı döner savuruş "!!" (spin / intikam; hazırlık 2 + dönüş 4 + toparlanma 2): iki kolu bir yana kurup gövdeyi
# burar; sonra kollar iki yana açık tam tur (sx: önden yana, arkaya, öbür yana) ve sendeleyerek oturur
def _spin_pose(k, base=None):
    """Döner savuruşun k. çeyreği (0 yan, 1 kenar, 2 arka, 3 kenar): sx ile gövde çevrilir, kollar iki yana açık."""
    sxs = (1.0, 0.55, -1.0, -0.55)
    d = dict(y=2.5, pitch=0.06, tw=0.0, sx=sxs[k], al=(1.62, 0.05), ar=(-1.55, -0.05), roar=1.0, flare=1.0, cl=0.8,
             hr=-0.05, hd=(0.5, 0.0), rag=(1.4, 1.0, -1.4, -1.0)[k], lf=(3.0, 0.0, 0.0), lb=(-11.0, 0.0, 0.0))
    if k in (1, 3):   # kenardan: kollar yanlara uzanır, dirsekler hafif bükük
        d.update(al=(1.5, 0.15), ar=(-1.4, -0.15), y=3.0, lf=(1.0, 2.5 if k == 1 else 0.0, 0.2), lb=(-9.0, 0.0 if k == 1 else 2.5, 0.2))
    if base:
        d.update(base)
    return d


SEQS['spin'] = Seq([
    (0.0, dict(y=3.0, pitch=0.22, arch=0.8, tw=-2.5, al=(-0.7, 0.6), ar=(-0.9, 0.5), roar=0.8, flare=0.9, hr=0.15, rag=0.4, cl=0.6,
               lf=(4.0, 0.0, 0.0), lb=(-14.0, 0.0, 0.2)), 'o'),
    (0.15, dict(y=5.5, pitch=0.32, arch=1.1, tw=-3.5, sq=0.4, al=(-1.3, 0.5), ar=(-1.5, 0.4), roar=1.0, flare=1.0, hr=0.25, hd=(1.5, 1.5), rag=0.8, cl=0.8,
                lf=(5.0, 0.0, 0.0), lb=(-15.0, 0.0, 0.3)), 'io'),
    (0.25, dict(y=3.0, pitch=0.12, tw=-1.0, al=(-0.2, 0.2), ar=(-0.9, 0.1), roar=1.0, flare=1.0, rag=1.0, cl=0.8, lf=(4.0, 0.0, 0.0), lb=(-14.0, 0.0, 0.2)), 'i'),
    (0.35, _spin_pose(0), 'l'),
    (0.45, _spin_pose(1), 'l'),
    (0.55, _spin_pose(2), 'l'),
    (0.65, _spin_pose(3), 'l'),
    (0.8, dict(y=3.5, pitch=0.2, sx=0.85, al=(0.9, 0.4), ar=(-0.5, 0.3), roar=0.6, flare=0.6, rag=1.2, lf=(3.0, 0.0, 0.0), lb=(-12.0, 0.0, 0.0), pf=0.8, pf_x=2.0, sq=0.4), 'o'),
    (1.0, dict(y=1.0, al=(0.2, 0.3), ar=(0.15, 0.2), flare=0.2, rag=-0.3), 'o'),
], frames=[(0.0, 0.0), (0.25, 0.0),
           (0.35, 0.0), (0.45, 0.25), (0.55, 0.5), (0.65, 0.75),
           (0.8, 0.0), (1.0, 0.5)],
    seg=[('windup', 2), ('rev', 4), ('recover', 2)], lead={'windup': 0.05}, rest=REST, fps=10)
# kasırga döngüsü (Tozkoparan 'spin' durumu; 4 kare)
SEQS['whirl'] = Seq([(i / 4, _spin_pose(i, dict(y=2.0)), 'l') for i in range(4)] + [(1.0, _spin_pose(0, dict(y=2.0)), 'l')],
                    n=4, fps=10, loop=True, rest=REST)

# ---- hafif sarsılma (3 kare, 0,22 sn): kafatası geri savrulur, çatlaklar parlar, kollar sarsılır
SEQS['hurt'] = Seq([
    (0.0, dict(x=-1.8, y=1.0, pitch=-0.16, hr=-0.3, hd=(-1.5, -1.0), roar=0.7, flare=0.9, al=(-0.25, 0.5), ar=(-0.2, 0.6), rag=1.2, sq=-0.2), 'o'),
    (0.5, dict(x=-1.0, y=1.2, pitch=-0.06, hr=-0.12, hd=(-0.5, 0.0), roar=0.4, flare=0.5, al=(0.0, 0.4), ar=(0.05, 0.4), rag=0.6), 'o'),
    (1.0, dict(y=0.5, hr=0.0, roar=0.1, flare=0.2, rag=-0.2), 'o'),
], frames=[(0.0, 0.0), (0.5, 0.35), (1.0, 0.7)], rest=REST, fps=12)

# ---- ağır sendeleme (4 kare, 0,45 sn): üst gövde geriye bükülür, yakın ayak geri adım atar, ağır öne toparlanış
SEQS['hurt_big'] = Seq([
    (0.0, dict(x=-3.0, y=0.0, pitch=-0.32, arch=-0.6, hr=-0.45, hd=(-2.0, -1.5), roar=1.0, flare=1.0, al=(-0.6, 0.7), ar=(-0.5, 0.9), rag=1.6, sq=-0.3,
               lf=(-2.0, 3.0, 0.3), lb=(-10.0, 0.0, 0.0)), 'o'),
    (0.35, dict(x=-4.5, y=2.5, pitch=-0.18, arch=-0.2, hr=-0.25, hd=(-1.0, 0.0), roar=0.7, flare=0.7, al=(-0.3, 0.6), ar=(-0.2, 0.7), rag=0.9,
                lf=(-5.0, 0.0, 0.0), lb=(-11.0, 0.0, 0.2), pf=0.9, pf_x=-5.0, sq=0.4), 'io'),
    (0.7, dict(x=-3.0, y=3.0, pitch=0.2, arch=0.6, hr=0.2, hd=(1.0, 1.5), roar=0.5, flare=0.4, al=(0.5, 0.4), ar=(0.6, 0.3), rag=-0.6,
               lf=(-4.0, 0.0, 0.0), lb=(-11.0, 0.0, 0.0)), 'o'),
    (1.0, dict(x=-2.5, y=1.0, pitch=0.06, hr=0.04, roar=0.2, flare=0.2, rag=-0.2, lf=(-3.0, 0.0, 0.0), lb=(-11.5, 0.0, 0.0)), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.25), (0.7, 0.55), (1.0, 0.8)], rest=REST, fps=10)


# ---- duruş kırık / sersem (6 kare döngü): kambur çöker, baş sarkık sallanır, kollar yerde sürünür, gözler söner
def _stun(t):
    s = math.sin(t * math.tau)
    c = math.cos(t * math.tau)
    return dict(x=1.4 * s, y=4.5 + 0.8 * c, pitch=0.3 + 0.05 * c, arch=1.0, hr=0.38 + 0.12 * s, hd=(1.5 + 0.8 * s, 3.5 + 0.6 * c),
                roar=0.45 + 0.1 * s, flare=-0.3 + 0.2 * c, eye=-0.6, al=(0.25 + 0.1 * s, 0.1), ar=(0.35 - 0.1 * s, 0.08), rag=0.6 * s,
                lf=(1.0, 0.0, 0.0), lb=(-11.0 + 1.0 * c, 0.6 * max(0.0, -s), 0.1), ph=t * math.tau)


SEQS['stun'] = Seq([(i / 12, _stun(i / 12), 'l') for i in range(13)], n=6, fps=6, loop=True, rest=REST)

# ---- havaya savrulma (dikey hız evresi; 4 kare): geriye devrilip kollar savrulur, dizler toplanır, düşüşte ayaklar aşağı
SEQS['launch'] = Seq([
    (0.0, dict(y=-2.0, roll=-0.25, rp=(-4.0, -30.0), pitch=-0.25, arch=-0.4, hr=-0.4, roar=1.0, flare=0.9, al=(2.4, 0.6), ar=(2.0, 0.8), rag=1.5,
               lf=(2.0, 6.0, 0.6), lb=(-9.0, 9.0, 0.7)), 'o'),
    (0.4, dict(y=-4.0, roll=-0.45, rp=(-4.0, -30.0), pitch=-0.1, arch=0.4, hr=-0.2, roar=0.8, flare=0.7, al=(2.9, 0.8), ar=(2.6, 0.9), rag=0.8,
               lf=(4.0, 12.0, 0.7), lb=(-6.0, 13.0, 0.8)), 'io'),
    (0.7, dict(y=-3.0, roll=-0.3, rp=(-4.0, -30.0), pitch=0.1, arch=0.4, hr=0.1, roar=0.6, flare=0.5, al=(1.6, 0.6), ar=(1.3, 0.7), rag=-0.6,
               lf=(3.0, 7.0, 0.4), lb=(-10.0, 6.0, 0.4)), 'io'),
    (1.0, dict(y=-1.0, roll=-0.1, rp=(-4.0, -30.0), pitch=0.15, hr=0.15, roar=0.5, flare=0.4, al=(0.8, 0.5), ar=(0.6, 0.6), rag=-1.0,
               lf=(3.0, 3.0, 0.2), lb=(-11.0, 2.0, 0.2)), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.25), (0.65, 0.55), (1.0, 0.82)], seg=[('air', 4)], rest=REST, fps=10)

# ---- ölüm (8 kare, 0,9 sn): darbeyle geri şahlanıp son kez kükrer, dizleri çöker, kesilen ağaç gibi öne devrilir, yere
# gümler (toprak), bir kez seker, çatlakların ışığı ve göz alevi söner, gövde çöküp yığılır
DROP = dict(rp=(16.0, 0.0))
SEQS['death'] = Seq([
    (0.0, dict(DROP, x=-2.0, y=-0.5, pitch=-0.36, arch=-0.6, hr=-0.5, hd=(-1.5, -2.0), roar=1.0, flare=1.0, al=(1.4, 0.8), ar=(1.9, 0.6), rag=1.4, sq=-0.3,
               lf=(1.0, 0.0, 0.0), lb=(-10.0, 0.0, 0.0)), 'o'),
    (0.16, dict(DROP, x=-1.0, y=9.0, pitch=0.1, arch=0.6, hr=0.1, hd=(0.5, 1.0), roar=0.8, flare=0.7, al=(0.3, 0.4), ar=(0.5, 0.3), rag=-0.6, sq=0.3,
                lf=(1.0, 0.0, 0.0), lb=(-10.0, 0.0, 0.3)), 'o'),
    (0.32, dict(DROP, x=-2.0, y=11.0, roll=0.35, pitch=0.3, arch=0.8, hr=0.3, hd=(1.5, 2.0), roar=0.6, flare=0.5, al=(0.0, 0.3), ar=(0.2, 0.2), rag=-1.0,
                lf=(1.0, 0.0, 0.0), lb=(-10.0, 0.0, 0.3)), 'i2'),
    (0.48, dict(DROP, x=-9.0, y=9.5, roll=0.98, pitch=0.35, arch=0.6, hr=0.25, hd=(2.0, 1.0), roar=0.7, flare=0.4, al=(-0.5, 0.2), ar=(-0.3, 0.3), rag=-1.6,
                lf=(1.0, 0.0, 0.0), lb=(-10.0, 1.0, 0.3), sq=0.6, dirt=0.05, dirt_x=36.0), 'i'),
    (0.6, dict(DROP, x=-9.0, y=7.5, roll=0.9, pitch=0.3, arch=0.6, hr=0.3, hd=(2.0, 1.0), roar=0.5, flare=0.25, al=(-0.2, 0.3), ar=(0.0, 0.3), rag=0.8,
               lf=(1.0, 0.0, 0.0), lb=(-10.0, 1.0, 0.3), sq=0.2, dirt=0.4, dirt_x=36.0), 'o'),
    (0.72, dict(DROP, x=-9.0, y=10.0, roll=0.99, pitch=0.35, arch=0.5, hr=0.3, hd=(2.0, 1.0), roar=0.4, flare=0.0, eye=-0.2, al=(-0.4, 0.2), ar=(-0.2, 0.3),
                rag=-0.6, lf=(1.0, 0.0, 0.0), lb=(-10.0, 0.0, 0.3), sq=0.5, dirt=0.8, dirt_x=36.0), 'i'),
    (0.86, dict(DROP, x=-9.0, y=11.0, roll=1.0, pitch=0.35, arch=0.3, hr=0.32, hd=(2.0, 1.0), roar=0.3, flare=-0.4, eye=-0.6, al=(-0.4, 0.2), ar=(-0.2, 0.3),
                rag=-0.3, lf=(1.0, 0.0, 0.0), lb=(-10.0, 0.0, 0.3), sq=0.8), 'o'),
    (1.0, dict(DROP, x=-9.0, y=12.0, roll=1.0, pitch=0.35, arch=0.2, hr=0.34, hd=(2.0, 1.0), roar=0.25, flare=-0.7, eye=-1.0, al=(-0.4, 0.2), ar=(-0.2, 0.3),
               rag=0.0, lf=(1.0, 0.0, 0.0), lb=(-10.0, 0.0, 0.3), sq=1.0), 'o'),
], frames=[(0.0, 0.0), (0.16, 0.1), (0.32, 0.22), (0.48, 0.34), (0.6, 0.46), (0.72, 0.58), (0.86, 0.72), (1.0, 0.88)], rest=REST, fps=10)

# ---- kükreme (seçkin; 6 kare, 0,8 sn): göğsünü şişirip kollarını iki yana açar, başını göğe kaldırıp kükrer
SEQS['roar'] = Seq([
    (0.0, dict(), 'io'),
    (0.2, dict(y=2.5, pitch=0.25, arch=0.8, hr=0.25, hd=(1.0, 1.5), al=(0.6, 0.6), ar=(0.7, 0.6), roar=0.2, flare=0.4, rag=-0.4), 'o'),
    (0.45, dict(y=-1.5, pitch=-0.28, arch=-0.4, hr=-0.45, hd=(-1.0, -2.0), al=(2.2, 0.5), ar=(2.0, 0.6), roar=1.0, flare=1.0, br=1.2, cl=1.0, rag=1.0,
                lf=(3.0, 0.0, 0.0), lb=(-13.0, 0.0, 0.0), sq=-0.3), 'o'),
    (0.75, dict(y=-1.2, pitch=-0.24, arch=-0.3, hr=-0.4, hd=(-1.0, -1.8), al=(2.1, 0.55), ar=(1.9, 0.65), roar=0.95, flare=1.0, br=1.0, cl=1.0, rag=-0.6,
                lf=(3.0, 0.0, 0.0), lb=(-13.0, 0.0, 0.0)), 'io'),
    (1.0, dict(y=0.5, flare=0.2, rag=0.3), 'o'),
], n=6, fps=8, rest=REST)

R = {'u': 'st'}
DURUM = {
    # ---- tepkiler (Enemy._anim_tick öncelikli anahtarları)
    '_hurt': {'a': 'hurt', 'u': 'up', 'd': 0.22},
    '_hurt_big': {'a': 'hurt_big', 'u': 'up', 'd': 0.45},
    '_break': {'a': 'stun', 'u': 'loop'},
    '_launch': {'a': 'launch', 'u': 'vy'},
    '_death': {'a': 'death', 'u': 'up', 'd': 0.9},
    '_turn': {'a': 'turn', 'u': 'up', 'd': 0.4},
    '_roar': {'a': 'roar', 'u': 'up', 'd': 0.8},
    # ---- brute (Kara İye, Dev Çocuğu)
    'windup/swat': {'a': 'swat', 's': 'windup', 'u': 'st'},
    'windup/swat!!': {'a': 'swat', 's': 'windup', 'u': 'st'},
    'slam/swat': {'a': 'swat', 's': 'strike', 'u': 'st'},
    'recover/swat': {'a': 'swat', 's': 'recover', 'u': 'st'},
    'windup/slam': {'a': 'slam', 's': 'windup', 'u': 'st'},
    'windup/slam!!': {'a': 'slam', 's': 'windup', 'u': 'st'},
    'slam/slam': {'a': 'slam', 's': 'strike', 'u': 'st'},
    'recover/slam': {'a': 'slam', 's': 'recover', 'u': 'st'},
    'windup/leap': {'a': 'leap', 's': 'windup', 'u': 'st'},
    'windup/leap!!': {'a': 'leap', 's': 'windup', 'u': 'st'},
    'leap/leap': {'a': 'leap', 's': 'air', 'u': 'vy'},
    'leap': {'a': 'leap', 's': 'air', 'u': 'vy'},
    'slam/leap': {'a': 'leap', 's': 'strike', 'u': 'st'},
    'recover/leap': {'a': 'leap', 's': 'recover', 'u': 'st'},
    'windup/roots': {'a': 'roots', 's': 'windup', 'u': 'st'},
    'windup/roots!!': {'a': 'roots', 's': 'windup', 'u': 'st'},
    'slam/roots': {'a': 'roots', 's': 'strike', 'u': 'st'},
    'recover/roots': {'a': 'roots', 's': 'recover', 'u': 'st'},
    # zırhlı intikam (Enemy._tick_revenge: windup 0,34 -> rev 0,32 -> recover 0,45)
    'windup/spin!!': {'a': 'spin', 's': 'windup', 'u': 'st'},
    'windup/spin': {'a': 'spin', 's': 'windup', 'u': 'st'},
    'rev/spin': {'a': 'spin', 's': 'rev', 'u': 'st'},
    'recover/spin': {'a': 'spin', 's': 'recover', 'u': 'st'},
    # genel geri dönüşler
    'windup': {'a': 'swat', 's': 'windup', 'u': 'st'},
    'windup!!': {'a': 'slam', 's': 'windup', 'u': 'st'},
    'slam': {'a': 'slam', 's': 'strike', 'u': 'st'},
    'recover': {'a': 'slam', 's': 'recover', 'u': 'st'},
    # ---- tornado (Tozkoparan): yel tokadı = ters tokat, kasırga = döner savuruş + döngü, baş dönmesi = sersem
    'tornado:windup/gust': {'a': 'swat', 's': 'windup', 'u': 'st'},
    'tornado:slam/gust': {'a': 'swat', 's': 'strike', 'u': 'st'},
    'tornado:recover/gust': {'a': 'swat', 's': 'recover', 'u': 'st'},
    'tornado:windup/spin!!': {'a': 'spin', 's': 'windup', 'u': 'st'},
    'tornado:spin': {'a': 'whirl', 'u': 'loop'},
    'tornado:dizzy': {'a': 'stun', 'u': 'loop'},
    # ---- caster (Su İyesi, Od İyesi): göl = kök saplama, küreler = ters tokatla savurma
    'caster:windup/pool': {'a': 'roots', 's': 'windup', 'u': 'st'},
    'caster:slam/pool': {'a': 'roots', 's': 'strike', 'u': 'st'},
    'caster:recover/pool': {'a': 'roots', 's': 'recover', 'u': 'st'},
    'caster:windup/orbs': {'a': 'swat', 's': 'windup', 'u': 'st'},
    'caster:slam/orbs': {'a': 'swat', 's': 'strike', 'u': 'st'},
    'caster:recover/orbs': {'a': 'swat', 's': 'recover', 'u': 'st'},
}


def render_frame(anim, i, var='agac_iyesi', ss=3):
    V = VARIANTS[var]
    p = SEQS[anim].pose(i)
    cv = yk.occlude_glow(ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss))
    info = draw(cv, p, V)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
