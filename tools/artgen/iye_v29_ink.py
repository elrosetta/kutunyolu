"""v29: Su İyesi, Od İyesi (caster) ve Tozkoparan (tornado) — tam gövde animasyonlu iye çizimi.

Kara İye çizimi (`agac_iyesi_ink.py`, ötekilerin dosyası: Kara İye, Dev Çocuğu) buraya ÇATALLANDI: bu üç iyenin
satırları kendi pozlarıyla ve kendi düzeniyle (`anims_for`) çizilir; Kara İye / Dev Çocuğu dışa aktarımları
değişmez. Eklenenler (ucan_v29):
  * gövde: kalça pivotunda üst gövde döner (öne çöküş / geriye kavis), ezilir / uzar; bacaklar yerde kalır, kalça
    iner (diz bükülür). Baş ayrı gecikir (hdy), kükreme (roar), kolların ikisi de tam yayla oynar.
  * büyü akışı: Su İyesi'nde ellerin arasında dönen su küresi, kolları saran su şeritleri ve salınışta su taçlı
    sıçrama; Od İyesi'nde alev küresi, kor girdabı ve alev patlaması. Işınlanma (blink_out / blink_in): beden
    öğesine karışarak dağılır (çözülme + su sütunu / alev yutması) ve öbür yanda toplanır.
  * Tozkoparan: bacakları kök saçağı olarak sarkan, TOZ HORTUMU üstünde süzülen bir iye. `walk` satırı yürüyüş
    değil süzülüş + gövde burulmasıdır: Enemy kasırga dönüşünde bu satırı ×2,6 hızla oynattığından (bugünkü kod)
    hızlı oynayınca dönen hortum gibi okunur. Ayrıca `spin` (gerçek dönüş: yan görünüş daralıp aynalanır, kollar
    yanlara açık, hortum gövdeyi sarar), `dizzy` (başı dönmüş sallanma) satırları genel oynatım içindir.

Satırlar (hücre 128x112 dünya, ayak (60, 106), doku 4; en çok 8 kare = 4096 px):
  su_iyesi / od_iyesi   idle 6, walk 8, windup 6 (Enemy "windup", oynatılır), slam 5 (Enemy "slam"), attack 8
                        (ts/mk: windup + slam zaman çizgisi), tele_zirh 5, blink_out 4, blink_in 4, hurt 3, stagger 4,
                        death 7, spawn 6
  tozkoparan            idle 6, walk 8, windup 6, slam 5 (yel itişi), attack 8 (ts/mk), tele_zirh 5, spin 8,
                        dizzy 8, hurt 3, stagger 4, death 7, spawn 6
'hand' çapası = ön yumruk (dünya, dönüşümden geçmiş).
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_arm, lerp2
import yaratik_ink_kit as yk
import ucan_v29 as u29
from ucan_v29 import pose_at

TEX = 4.0
CELL = (512, 448)       # dünya 128 x 112
FEET = (240, 424)       # dünya (60, 106)

BONE = Ink('#e6dcc0', '#8c7c68', '#fffbe8', '#5a4a40', name='kemik')
WATER = Ink('#6fd2dc', '#2a7c96', '#e4fbff', '#164a62', name='su')
WATER_D = Ink('#3a9ab0', '#1a5470', '#9ee8f0', '#0c2c40', name='derin su')
DUST = Ink('#c8ae80', '#7c6448', '#eedcb0', name='toz')
DUST_D = Ink('#a48a62', '#5e4a36', '#d2bc90', name='koyu toz')
FIRE_O = (0.95, 0.3, 0.06)
FIRE_Y = (1.0, 0.82, 0.3)
FIRE_G = (1.0, 0.35, 0.02)


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
        extra=(), elem=None, seed=1,
    )
    base.update(kw)
    return base


VARIANTS = {
    'tozkoparan': _v(
        bark=Ink('#ab9474', '#5e4a44', '#d8c49c', '#33262a', name='ağarmış saksağul'),
        bark_b=Ink('#857058', '#463634', '#a48c6c', '#2a1e20', name='arka kuru dal'),
        groove=(0.3, 0.2, 0.16),
        back=Ink('#c9a54e', '#6c5028', '#ecd282', '#3a2a16', kind='fur', name='kuru bozkır otu'),
        back_kind='grass', horn=Ink('#d8ccae', '#7e6e5c', '#fff8e0', '#4a3c34', name='koç boynuzu'),
        horn_kind='ram', crack=(1.0, 0.7, 0.25), crack_hot=(1.0, 0.95, 0.7), crack_glow=(1.0, 0.5, 0.05),
        eye=(1.0, 0.85, 0.5), caput=((0.75, 0.2, 0.16), (0.94, 0.86, 0.7), (0.2, 0.42, 0.62)), extra=('vortex',),
        elem='dust', seed=21),
    'su_iyesi': _v(
        bark=Ink('#2f5552', '#132a32', '#4e8478', '#0a161e', name='ıslak kütük'),
        bark_b=Ink('#24403f', '#0f1e26', '#386258', '#060e14', name='arka kütük'),
        groove=(0.04, 0.1, 0.12),
        back=Ink('#3a8a6a', '#174438', '#6cc49a', '#0a2620', kind='fur', name='su yosunu'),
        back_kind='weed', horn=Ink('#cfe2d8', '#5e7c86', '#ffffff', '#34505a', name='sedef boynuz'),
        crack=(0.35, 1.0, 0.9), crack_hot=(0.85, 1.0, 1.0), crack_glow=(0.1, 0.85, 0.85),
        eye=(0.8, 1.0, 1.0), shroom=Ink('#6fa0b0', '#2c4c64', '#b6e0e8', name='midye'),
        caput=((0.3, 0.6, 0.62), (0.85, 0.92, 0.9), (0.3, 0.6, 0.62)), extra=('drips',), elem='water', seed=23),
    'od_iyesi': _v(
        bark=Ink('#3e3036', '#18101a', '#62505a', '#0c070c', name='kömür kabuk'),
        bark_b=Ink('#2c2228', '#120c12', '#443840', '#08050a', name='arka kömür'),
        groove=(0.05, 0.02, 0.03),
        back=Ink('#5a5458', '#262226', '#8a8286', '#141014', kind='fur', name='kül'),
        back_kind='ash', horn=Ink('#3a3034', '#160e12', '#6a5a5a', '#0a0608', name='yanık boynuz'),
        horn_kind='antler', skull=Ink('#c8b8a4', '#6a5650', '#efe2cc', '#3a2a28', name='isli kemik'),
        crack=(1.0, 0.55, 0.12), crack_hot=(1.0, 0.92, 0.55), crack_glow=(1.0, 0.38, 0.02),
        eye=(1.0, 0.9, 0.5), caput=(), shroom=Ink('#3a3034', '#160e12', '#6a5a5a', name='kor'),
        extra=('flames', 'embers'), elem='fire', seed=25),
}


# ------------------------------------------------------------------ Kara İye yardımcıları (agac_iyesi_ink.py'den kopya)
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



# ------------------------------------------------------------------ öğe efektleri
def _flame(cv, base, h, w, z, ph, sc=1.0, glow_a=0.45):
    """Kıvrık S alev dili: dışı kızıl, içi sarı (Od İyesi)."""
    q = base
    wv = math.sin(ph) * w * 0.5

    def tongue(k):
        return cv.blob([(q[0] - w * k, q[1] + 1.0), (q[0] - w * 0.9 * k + wv * 0.3, q[1] - h * 0.35 * k), (q[0] - w * 0.3 * k + wv, q[1] - h * 0.7 * k),
                        (q[0] - w * 0.7 + wv * 1.6, q[1] - h * k, 0.0), (q[0] + w * 0.4 * k + wv * 0.6, q[1] - h * 0.55 * k), (q[0] + w * 0.9 * k, q[1] - h * 0.2 * k),
                        (q[0] + w * k, q[1] + 1.0)])
    cv.fill(tongue(1.0 * sc), FIRE_O, z=z, glow=FIRE_G)
    cv.fill(tongue(0.6 * sc), FIRE_Y, z=z + 0.05, glow=(1.0, 0.75, 0.25))
    yk.glow_soft(cv, (q[0], q[1] - h * 0.4), max(w, h) * 0.6, FIRE_G, z=z + 0.1, blur=0.6, alpha=glow_a)


def _orb(cv, c, k, V, z, ph):
    """Ellerin arasında toplanan öğe küresi (k 0..1+): su küresi (içinde dönen akıntı, köpük halkası) ya da alev topu."""
    if k <= 0.02:
        return
    r = 2.0 + 5.5 * k
    e = V['elem']
    if e == 'water':
        yk.glow_soft(cv, c, r * 2.0, V['crack_glow'], z=z - 0.1, blur=0.6, alpha=0.35 * k)
        cv.shape(cv.ellipse(c, r, r * 0.95), WATER, z=z, sd=r * 0.35, hi=r * 0.18, ol=0.8, glow=(0.03, 0.25, 0.28),
                 details=[('stroke', [(c[0] - r * 0.6, c[1] + r * 0.1), (c[0], c[1] - r * 0.5), (c[0] + r * 0.6, c[1] + r * 0.05)], 1.2, WATER.hi, (0.2, 0.6)),
                          ('ink', [(c[0] - r * 0.5, c[1] + r * 0.45), (c[0] + r * 0.1, c[1] + r * 0.2), (c[0] + r * 0.55, c[1] + r * 0.5)], 0.8, (0.3, 0.3))])
        for i in range(3):   # kürenin çevresinde dönen su şeritleri
            a = ph * 1.5 + i * math.tau / 3
            st = (c[0] + math.cos(a) * r * 1.25, c[1] + math.sin(a) * r * 0.6)
            yk.wisp(cv, st, a + math.pi / 2, r * 2.2, 1.6 + k, WATER, z + 0.2 + i * 0.01, ph=ph + i, curl=0.6, alpha=0.75, glow=(0.03, 0.3, 0.3), glow_a=0.5, ink=True)
        for i in range(5):
            a = ph * 2 + i * 1.3
            q = (c[0] + math.cos(a) * r * 1.6, c[1] + math.sin(a) * r * 1.2)
            cv.shape(cv.blob([(q[0], q[1] - 0.9, 0.0), (q[0] + 0.6, q[1] + 0.2), (q[0], q[1] + 0.7), (q[0] - 0.6, q[1] + 0.2)]), WATER, z=z + 0.3, sd=0.3, ol=0.6)
    elif e == 'fire':
        yk.glow_soft(cv, c, r * 2.2, FIRE_G, z=z - 0.1, blur=0.6, alpha=0.5 * k)
        cv.fill(cv.ellipse(c, r, r), FIRE_O, z=z, glow=FIRE_G)
        cv.fill(cv.ellipse((c[0] + r * 0.1, c[1] + r * 0.1), r * 0.62, r * 0.62), FIRE_Y, z=z + 0.05, glow=(1.0, 0.8, 0.3))
        cv.fill(cv.ellipse((c[0] + r * 0.15, c[1] + r * 0.15), r * 0.3, r * 0.3), (1.0, 0.97, 0.8), z=z + 0.06, glow=(1.0, 0.95, 0.7))
        for i in range(4):
            a = -math.pi / 2 + (i - 1.5) * 0.5 + math.sin(ph + i) * 0.2
            _flame(cv, (c[0] + math.cos(a) * r * 0.6, c[1] + math.sin(a) * r * 0.6), r * (1.0 + 0.3 * math.sin(ph * 2 + i)), r * 0.45, z + 0.1 + i * 0.01, ph + i * 1.7, glow_a=0.2)
        yk.sparks(cv, c, 6, r * 1.1, r * 2.0, FIRE_Y, z + 0.3, seed=int(ph * 10) % 97, w=1.1, glow=FIRE_G)
    else:
        yk.cloud(cv, c, r, DUST, z, seed=int(ph * 5) % 31, lobes=8)


def _burst(cv, c, d, k, V, z, ph, seed=0):
    """Salınış: elden fırlayan öğe patlaması (su taçlı sıçrama / alev püskürmesi / toz dalgası), d yönünde."""
    if k <= 0.02:
        return
    e = V['elem']
    rng = np.random.default_rng(seed)
    d = u29.norm2(d)
    if e == 'water':
        yk.glow_soft(cv, c, 9 * k, V['crack_glow'], z=z - 0.1, blur=0.6, alpha=0.35)
        for i in range(9):
            a = math.atan2(d[1], d[0]) + rng.uniform(-0.9, 0.9)
            L = (6 + rng.uniform(0, 10)) * k
            p0 = (c[0] + math.cos(a) * 1.5, c[1] + math.sin(a) * 1.5)
            p1 = (c[0] + math.cos(a) * L, c[1] + math.sin(a) * L - L * 0.15)
            cv.shape(ik.taper_path([cv.W(p0), cv.W(u29.lerp2(p0, p1, 0.5)), cv.W(p1)], cv.u(2.2 * k + 0.6), (0.1, 0.9)), WATER, z=z + i * 0.01, sd=0.4, hi=0.2, ol=0.7)
            q = (p1[0] + math.cos(a) * 1.8, p1[1] + math.sin(a) * 1.8)
            cv.shape(cv.blob([(q[0], q[1] - 1.0, 0.0), (q[0] + 0.7, q[1] + 0.2), (q[0], q[1] + 0.8), (q[0] - 0.7, q[1] + 0.2)]), WATER, z=z + 0.2, sd=0.3, ol=0.6)
        cv.shape(cv.ellipse(c, 4.5 * k, 2.6 * k, math.atan2(d[1], d[0]) + math.pi / 2), WATER_D, z=z + 0.3, sd=0.8, hi=0.4, ol=0.8)
    elif e == 'fire':
        yk.glow_soft(cv, c, 12 * k, FIRE_G, z=z - 0.1, blur=0.6, alpha=0.6)
        for i in range(7):
            a = math.atan2(d[1], d[0]) + rng.uniform(-0.7, 0.7)
            L = (5 + rng.uniform(0, 9)) * k
            q = (c[0] + math.cos(a) * L * 0.6, c[1] + math.sin(a) * L * 0.6)
            cv.fill(cv.ellipse(q, 2.6 * k + 0.5, 2.0 * k + 0.5, a), FIRE_O, z=z + i * 0.01, glow=FIRE_G)
            cv.fill(cv.ellipse(q, 1.4 * k + 0.3, 1.0 * k + 0.3, a), FIRE_Y, z=z + 0.05 + i * 0.01, glow=(1.0, 0.8, 0.3))
        yk.sparks(cv, c, 10, 3.0 * k, 14.0 * k, FIRE_Y, z + 0.3, seed=seed + 3, w=1.3, glow=FIRE_G, ang=math.atan2(d[1], d[0]), spread=1.8)
    else:
        for i in range(4):
            q = (c[0] + d[0] * (4 + i * 6) * k, c[1] + d[1] * (4 + i * 6) * k - i * 1.0)
            yk.cloud(cv, q, (3.0 + i * 1.6) * k, DUST if i % 2 == 0 else DUST_D, z + i * 0.05, seed=seed + i, lobes=7)
        u29.speed_lines(cv, c, (-d[0], -d[1]), n=6, L=22 * k, spread=18 * k, w=1.8, col=DUST_D.shadow, alpha=0.6, z=z + 0.4, seed=seed)


def _blink(cv, k, V, z, ph, cx=0.0):
    """Işınlanma örtüsü: su sütunu (aşağıdan yükselen sarmal su) ya da alev yutması, gövdeyi sarar."""
    if k <= 0.02:
        return
    if V['elem'] == 'water':
        yk.glow_soft(cv, (cx, -40), 26 * k, V['crack_glow'], z=z - 0.2, blur=0.6, alpha=0.35 * k)
        for i in range(6):
            a = ph * 2.0 + i * 1.05
            x0 = cx + math.cos(a) * 16 * k
            yk.wisp(cv, (x0, 0.0), -math.pi / 2 + math.sin(a) * 0.25, 70 * k, 5.0 * k + 1.0, WATER if i % 2 else WATER_D, z + i * 0.02, ph=ph + i, curl=0.5,
                    alpha=0.8, glow=(0.03, 0.3, 0.3), glow_a=0.5, ink=True)
        cv.shape(cv.ellipse((cx, -1.0), 22 * k, 4 * k), WATER_D, z=z + 0.2, sd=1.0, hi=0.5, ol=0.8)
    elif V['elem'] == 'fire':
        yk.glow_soft(cv, (cx, -40), 30 * k, FIRE_G, z=z - 0.2, blur=0.6, alpha=0.6 * k)
        for i in range(7):
            x = cx + (i - 3) * 6.0 * k
            _flame(cv, (x, 0.0), (30 + 25 * math.sin(i * 1.7 + ph)) * k, 6.0 * k + 1, z + i * 0.02, ph + i * 1.3, glow_a=0.3)
        yk.sparks(cv, (cx, -40), 14, 10 * k, 40 * k, FIRE_Y, z + 0.3, seed=int(ph * 7) % 50, w=1.3, glow=FIRE_G, ang=-math.pi / 2, spread=1.8)
    else:
        _vortex(cv, (cx, 0.0), -70.0, 1.2 * k, ph, z - 30, z, V)


def _vortex(cv, base, top_y, k, ph, z_back, z_front, V, width=1.0):
    """Toz hortumu: yerden yukarı genişleyen dönen bantlar. Arka yarılar gövdenin arkasında, ön yarılar önünde
    (yarı saydam: gövde içinden seçilir). k: yoğunluk (dönüşte 1,3: gövdeyi sarar)."""
    if k <= 0.02:
        return
    n = 7
    for i in range(n):
        u = i / (n - 1)
        y = base[1] + (top_y - base[1]) * u
        r = (4.0 + 20.0 * u ** 1.3) * k * width
        sway = math.sin(ph * 0.5 + u * 3.0) * 3.0 * u
        a0 = ph * 3.0 + i * 1.1
        for front in (False, True):
            pts = []
            for j in range(9):
                a = a0 + (math.pi if front else 0.0) + j / 8 * math.pi
                pts.append((base[0] + sway + math.cos(a) * r, y + math.sin(a) * r * 0.22))
            mat = DUST if (i + front) % 2 == 0 else DUST_D
            al = (0.55 if front else 0.75) * min(1.0, k)
            path = ik.taper_path([cv.W(q) for q in pts], cv.u(1.6 + 2.6 * u * k), (0.4, 0.4))

            def fn(c, path=path, mat=mat, al=al):
                c.drawPath(path, yk.paint(mat.base, al))
                c.drawPath(ik.diff(path, ik.moved(path, 0, -cv.u(0.6))), yk.paint(mat.shadow, al))
            cv._q((z_front if front else z_back) + i * 0.01, fn)
            if front and i % 2 == 1:
                cv.stroke(pts[2:7], 0.8, z=z_front + 0.2 + i * 0.01, col=INK, taper=(0.4, 0.4), alpha=0.6)
    # tabanda kabaran toz
    for j in range(3):
        q = (base[0] + (j - 1) * 9.0 * k, base[1] - 1.0)
        yk.puff(cv, q, (3.2 + j % 2) * k, DUST_D, z_front + 0.5 + j * 0.01, seed=j + int(ph * 3) % 11, n=6)


# ------------------------------------------------------------------ çizim
def draw(cv, p, V):
    bob, lean = p.get('bob', 0.0), p.get('lean', 0.0)
    step = p.get('step', 0.0)
    roar = p.get('roar', 0.0)
    flare = p.get('flare', 0.0)
    ph = p.get('ph', 0.0)
    ex = V['extra']
    B, BB = V['bark'], V['bark_b']
    rot = p.get('rot', 0.0)
    off = p.get('off', (0.0, 0.0))
    turn = p.get('turn', 0.0)
    float_ = 'vortex' in ex
    hip = (-7.0 + off[0], -30 + bob * 0.6 + (p.get('hover', 0.0) if float_ else 0.0))
    sh = (5 + lean * 28, -54 + bob + max(0.0, lean) * 26 - min(0.0, lean) * 5)
    # ---- dünya uzayı: ışınlanma örtüsü, zerreler — çözülen karelerde ayrı tuvalde çizilir (render_frame, '_fx')
    fxp = p.get('_fx', 'all')
    if fxp in ('all', 'fx') and p.get('blink', 0.0) > 0:
        _blink(cv, p['blink'], V, -40, ph, cx=hip[0] + 6)
    if fxp in ('all', 'fx') and p.get('ash', 0.0) > 0:
        col = WATER if V['elem'] == 'water' else (DUST if V['elem'] == 'dust' else Ink('#4a4448', '#221e22', '#7a7276'))
        u29.flecks(cv, (hip[0] + 6, -40.0 + bob * 0.5), int(16 * p['ash']) + 4, 6.0, 26.0, col, 80, seed=V['seed'] + int(ph * 9) % 50, s0=0.6, s1=1.6,
                   drift=(0.0, -1.0), dk=14.0 * p['ash'])
        if V['elem'] == 'fire':
            u29.flecks(cv, (hip[0] + 6, -40.0 + bob * 0.5), int(10 * p['ash']) + 3, 5.0, 24.0, V['crack_hot'], 81, seed=V['seed'] + 7, s0=0.4, s1=0.9,
                       drift=(0.3, -1.0), dk=20.0 * p['ash'], glow=V['crack_glow'])
    if fxp == 'fx':
        return {'hand': (0.0, 0.0)}
    if float_:
        _vortex(cv, (hip[0] + 2.0, 0.0), hip[1] + 6.0 - (36.0 * max(0.0, p.get('vk', 0.6) - 0.8)), p.get('vk', 0.6), p.get('vph', ph), -30, 70 if p.get('vk', 0.6) > 0.9 else -0.5, V,
                width=p.get('vw', 1.0))
    if p.get('streak', 0.0) > 0:
        u29.speed_lines(cv, (hip[0] + 6, -45.0), p.get('sdir', (1.0, 0.0)), n=7, L=26 * p['streak'], spread=50.0, w=2.0, col=DUST_D.shadow if float_ else INK,
                        alpha=0.5, z=-45, seed=int(ph * 9) % 77)
    # ---- bacaklar: kök gibi kalın, ayaklarda kök saçakları (Tozkoparan'da hortuma sarkan kök saçağı)
    for side, z in ((-1, -12), (1, -1)):
        mat = B if side > 0 else BB
        st = step * side
        top = (hip[0] + side * 4, hip[1] + 2)
        if float_:
            sw_ = math.sin(ph + side) * 2.0 + p.get('leg_sw', 0.0)
            knee = (top[0] + 2 + sw_ * 0.4, top[1] + 11)
            foot = (top[0] - 2 + sw_, top[1] + 21)
            leg = cv.limb([top, lerp2(top, knee, 0.5), knee, foot], [6.0, 5.2, 4.0, 1.2])
            tw = [ik.taper_path([cv.W(foot), cv.W((foot[0] + j * 2.0 + sw_ * 0.5, foot[1] + 5)), cv.W((foot[0] + j * 3.5 + sw_, foot[1] + 9))], cv.u(1.6), (0.0, 0.9))
                  for j in (-1, 0, 1)]
            leg = ik.union(leg, *tw)
            det = _grooves(top, knee, 5.5, 3, 11 + side, 1.2, V if side > 0 else None)
            cv.shape(leg, mat, z=z, sd=2.4, hi=0.4 if side > 0 else 0.0, details=det)
            continue
        knee = (hip[0] + side * 4 + 4 + st * 0.5, -14 + bob * 0.3 - abs(st) * 0.3)
        foot = (hip[0] - off[0] + side * 5 + 2 + st, -3)
        leg = ik.union(cv.limb([top, lerp2(top, knee, 0.5), knee, foot], [7.2, 6.8, 5.6, 5.2]), _roots(cv, foot, mat, z, side, 3 + side))
        det = _grooves(top, knee, 6.5, 4, 11 + side, 1.3, V if side > 0 else None) + _grooves(knee, foot, 5.2, 3, 21 + side, 1.2, V if side > 0 else None)
        det.append(('ink', [along(knee, top, 0.05, -4.5), along(knee, top, 0.0, 0.0), along(knee, top, 0.08, 4.0)], 1.6, (0.3, 0.3)))
        cv.shape(leg, mat, z=z, sd=3.0, hi=0.5 if side > 0 else 0.0, details=det, hatch=0.5 if side > 0 else 0.0)
    # ---- üst gövde dönüşümü: kalça pivotu (öne çöküş / geriye kavis, ezilme), dönüşte yan görünüş daralıp aynalanır
    tc = math.cos(turn * math.tau)
    tsx = (1.0 if tc >= 0 else -1.0) * max(0.22, abs(tc))
    u29.body_xf(cv, hip, rot, p.get('sx', 1.0) * tsx, p.get('sy', 1.0), (0.0, p.get('oy', 0.0)), p.get('skew', 0.0))
    if p.get('zirh', 0.0) > 0:
        u29.armor_aura(cv, (sh[0] - 2, sh[1] + 8), 27.0, p['zirh'], z=-48, seed=V['seed'], spikes=11)
    # ---- arka kol
    al = p.get('al', (0.15, 0.2))
    shb = (sh[0] - 7, sh[1] + 2)
    e, h_b = fk_arm(shb, al[0], al[1], 18, 18)
    arm = ik.union(cv.limb([shb, lerp2(shb, e, 0.5), e, h_b], [6.0, 6.2, 4.8, 3.9]), cv.ellipse(h_b, 4.4, 4.0))
    a = al[0] + al[1]
    cs = p.get('claw', 0.0)
    claws = [ik.taper_path([cv.W(h_b), cv.W((h_b[0] + math.sin(a + k) * 4.5, h_b[1] + math.cos(a + k) * 4.5)),
                            cv.W((h_b[0] + math.sin(a + k * (1.2 + cs) + 0.2) * 8.0, h_b[1] + math.cos(a + k * (1.2 + cs) + 0.2) * 8.0))], cv.u(3.2), (0.0, 0.95))
             for k in (-0.6, -0.2, 0.2, 0.6)]
    cv.shape(ik.union(arm, *claws), BB, z=-16, sd=3.0, details=_grooves(shb, e, 5.5, 3, 31) + _grooves(e, h_b, 4.4, 2, 32))
    # ---- gövde: kambur sırt + fıçı göğüs (tek kontur)
    hump = lerp2(hip, sh, 0.55)
    cc = (sh[0] + 6 - lean * 3, sh[1] + 10)
    body = ik.union(cv.capsule(hip, sh, 10.5, 13.5), cv.ellipse((hump[0] - 1, hump[1] - 4), 13.0, 11.5, -0.5), cv.ellipse(cc, 10.5, 12.5))
    det = []
    for k in range(6):
        o = -10 + k * 4.0
        pts = [along(hip, sh, 0.0, o * 0.8), along(hip, sh, 0.35, o * 1.05 + 1.0), along(hip, sh, 0.7, o * 1.1), along(hip, sh, 1.0, o * 0.9)]
        det.append(('ink', pts, 1.4 + (k % 2) * 0.3, (0.35, 0.35)))
        if k % 2 == 0:
            det.append(('stroke', [(q[0] - 0.7, q[1] - 0.5) for q in pts[1:3]], 1.2, B.hi, (0.4, 0.4)))
    kn = along(hip, sh, 0.35, 6.0)
    rng_ = np.random.default_rng(5)
    for k in range(9):
        q = along(hip, sh, rng_.uniform(0.05, 0.9), rng_.uniform(-9, 9))
        r_ = rng_.uniform(0.5, 1.1)
        det.append(('col', cv.ellipse(q, r_, r_ * 0.8), ik.mix(B.hi, V['back'].hi, 0.6)))
    det += [('deep', cv.ellipse(kn, 2.0, 2.6, 0.4)), ('ink', [(kn[0] - 1.6, kn[1] - 2.2), (kn[0] - 2.4, kn[1]), (kn[0] - 1.4, kn[1] + 2.4)], 1.4)]
    cv.shape(body, B, z=0, sd=6.0, hi=0.8, details=det, hatch=0.45, bounce=0.35, deep=0.35)
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
    # ---- sırttan çıkan kırık dallar (gövdeden gecikerek sallanır: br)
    brs = p.get('br', 0.0)
    for j, (t, ang, ln, w) in enumerate(((0.35, -2.2, 11.0, 2.4), (0.55, -1.85, 14.0, 2.8), (0.75, -1.45, 9.0, 2.0))):
        q = lerp2((hip[0] - 4, hip[1] - 12), (sh[0] - 2, sh[1] - 12), t)
        q = (q[0], q[1] - math.sin(t * math.pi) * 6.0)
        ang += lean * 0.3 + brs * (0.6 + 0.4 * j)
        tip = (q[0] + math.cos(ang) * ln, q[1] + math.sin(ang) * ln)
        mid = lerp2(q, tip, 0.55)
        mid = (mid[0] + math.cos(ang + 1.5) * 1.2, mid[1] + math.sin(ang + 1.5) * 1.2)
        tw_ = lerp2(q, tip, 0.5)
        twig = (tw_[0] + math.cos(ang + 0.9) * ln * 0.4, tw_[1] + math.sin(ang + 0.9) * ln * 0.4)
        br = ik.union(ik.taper_path([cv.W(q), cv.W(mid), cv.W(tip)], cv.u(w * 2), prof=lambda u: max(0.35, 1.0 - 0.6 * u)),
                      ik.taper_path([cv.W(tw_), cv.W(twig)], cv.u(w * 0.9), (0.0, 0.9)))
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
                sw = math.sin(ph + k_ * 2) * 0.5 - brs * 2.0
                cv.shape(ik.taper_path([cv.W(qq), cv.W((qq[0] - 1.0 + sw, qq[1] + 3.0)), cv.W((qq[0] - 2.0 + sw * 2, qq[1] + 6.5))], cv.u(1.5), (0.05, 0.5)),
                         Ink(col), z=15.3 + k_ * 0.01, sd=0.4, ol=0.7)
    # ---- sırt örtüsü, alt kenarı saçaklı (saçaklar gövdeden gecikir: fr)
    fr = p.get('fr', 0.0)
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
    for i in list(range(1, 8, 2)) + [2, 6]:
        q = bot[i]
        L = (5 + (i * 7) % 6) * (1.6 if bk in ('weed', 'grass') else 1.0)
        sw = math.sin(ph + i) * 0.8 - lean * 2 + fr * 3.0
        pts = [(q[0], q[1] - 1), (q[0] - 0.4 + sw * 0.5, q[1] + L * 0.5 - abs(fr) * 1.5), (q[0] - 0.8 + sw, q[1] + L - abs(fr) * 2.5)]
        if bk == 'ash':
            cv.fill(cv.ellipse(pts[-1], 0.55, 0.55), V['crack_hot'], z=25.5, glow=V['crack_glow'])
        cv.shape(ik.taper_path([cv.W(r_) for r_ in pts], cv.u(1.8), (0.0, 0.85)), BK, z=25 + i * 0.01, sd=0.7, ol=0.8)
    if bk in ('moss', 'weed'):
        for j, t in enumerate((0.3, 0.55)):
            q = lerp2(top[2], top[6], t)
            q = (q[0], q[1] + 1.0)
            S = V['shroom']
            cap = cv.blob([(q[0] - 2.2, q[1]), (q[0] - 1.6, q[1] - 1.6), (q[0], q[1] - 2.3), (q[0] + 1.6, q[1] - 1.6), (q[0] + 2.2, q[1]), (q[0], q[1] + 0.5)])
            cv.shape(cv.capsule((q[0], q[1]), (q[0] + 0.2, q[1] + 2.0), 0.6, 0.7), Ink('#e8dcc4'), z=27 + j * 0.1, sd=0.4, ol=0.7)
            cv.shape(cap, S, z=27.05 + j * 0.1, sd=0.9, hi=0.35, ol=0.8, details=[('col', cv.ellipse((q[0] - 0.6, q[1] - 1.3), 0.45, 0.35), S.hi)])
    if 'flames' in ex:   # omuz ve sırtta alev dilleri (kanallamada büyür)
        for j, t in enumerate((0.2, 0.5, 0.8)):
            q = lerp2(top[1], top[7], t)
            hgt = 7.0 + 2.5 * math.sin(ph * 2 + j * 2.1) + flare * 5.0
            _flame(cv, q, hgt, 2.2, 27 + j * 0.1, ph * 3 + j * 1.3)
    if 'embers' in ex:
        yk.sparks(cv, (sh[0] - 4, sh[1] - 16), 6 + int(flare * 6), 2.0, 9.0 + flare * 6, V['crack_hot'], 28, seed=int(ph * 10) + 3, w=1.1, glow=V['crack_glow'], ang=-math.pi / 2, spread=1.4)
    # ---- baş (gövdeden gecikir: hdy; kükreme roar)
    hdy = p.get('hdy', 0.0)
    hx, hy = sh[0] + 14 + p.get('hdx', 0.0), sh[1] + 2 + hdy - roar * 3
    neck = cv.capsule((sh[0] + 3, sh[1] - 1), (hx - 2, hy + 1), 6.0, 4.0)
    cv.shape(neck, B, z=20, sd=2.5, hi=0.4, details=_grooves((sh[0] + 3, sh[1] - 1), (hx - 2, hy + 1), 5.0, 3, 41, 1.2, V))
    hk = V['horn_kind']
    if hk == 'antler':
        _antler(cv, (hx - 3.5, hy - 4.0), -2.3 - roar * 0.15, 24, V['horn'] if V['horn'] is not BONE else Ink('#b4a68e', '#665848', '#d4c8b0', '#3a3028'), 6,
                r0=1.7, curve=0.3, seed=1, V=V)
    jaw = 1.0 + roar * 4.0
    S = V['skull']
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
    ee = p.get('eyes', 1.0)
    if ee > 0.05:
        yk.eye_glow(cv, (hx + 1.6, hy - 0.7), (1.0 + flare * 0.4) * ee, (0.8 + flare * 0.3) * ee, 0.2, V['eye'], V['crack_glow'], 46)
    if hk == 'antler':
        r_ = _antler(cv, (hx - 1.0, hy - 4.6), -2.05 - roar * 0.15, 29, V['horn'], 34, r0=2.0, curve=0.28, seed=3, V=V)
        if V['caput'] and r_:
            pts_, tips = r_
            for j, (q, col) in enumerate(zip([lerp2(pts_[1], pts_[2], 0.5), lerp2(pts_[2], pts_[3], 0.5), tips[1]], V['caput'])):
                sw = math.sin(ph + j * 1.9) * 0.4 - lean * 0.5 - brs * 2.0
                cv.shape(ik.taper_path([cv.W(q), cv.W((q[0] - 0.8 + sw, q[1] + 3.0)), cv.W((q[0] - 1.6 + sw * 2, q[1] + 6.0 + j))], cv.u(1.4), (0.05, 0.5)),
                         Ink(col), z=35 + j * 0.01, sd=0.4, ol=0.7)
                cv.shape(cv.ellipse(q, 0.9, 0.7), Ink(col), z=35.1 + j * 0.01, sd=0.3, ol=0.6)
    elif hk == 'ram':
        _ram(cv, (hx - 0.5, hy - 1.0), V['horn'], 34, roar, size=0.62)
    # ---- ön kol: uzun, ağır; omuzda örtü, ön kolda çatlak, kök pençeli yumruk
    ar = p.get('ar', (0.25, 0.15))
    shf = (sh[0] + 1, sh[1] + 3)
    e, h = fk_arm(shf, ar[0], ar[1], 19, 19)
    a = ar[0] + ar[1]
    fist = cv.ellipse(h, 5.0, 4.6)
    claws = []
    for k in (-0.65, -0.22, 0.22, 0.65):
        m = (h[0] + math.sin(a + k) * 5.0, h[1] + math.cos(a + k) * 5.0)
        tip = (h[0] + math.sin(a + k * (1.25 + cs) + 0.15) * 9.0, h[1] + math.cos(a + k * (1.25 + cs) + 0.15) * 9.0)
        claws.append(ik.taper_path([cv.W(h), cv.W(m), cv.W(tip)], cv.u(3.6), (0.0, 0.95)))
    arm = ik.union(cv.limb([shf, lerp2(shf, e, 0.45), e, lerp2(e, h, 0.5), h], [6.5, 6.8, 5.2, 4.8, 4.4]), fist, *claws)
    det = _grooves(shf, e, 6.0, 4, 51, 1.3, V) + _grooves(e, h, 4.8, 3, 52, 1.2, V)
    det.append(('ink', [along(e, shf, 0.08, -4.5), e, along(e, h, 0.08, 4.5)], 1.6, (0.3, 0.3)))
    cv.shape(arm, B, z=50, sd=3.4, hi=0.6, details=det, hatch=0.35, bounce=0.3)
    m1, m2 = lerp2(e, h, 0.15), lerp2(e, h, 0.75)
    _crack(cv, [m1, (lerp2(m1, m2, 0.5)[0] + 1.2, lerp2(m1, m2, 0.5)[1]), m2], V, 62, 1.2 + flare * 0.7)
    if flare > 0:
        yk.glow_soft(cv, h, 7.0, V['crack_glow'], z=62.5, blur=0.6, alpha=0.4 * flare)
        yk.glow_soft(cv, h_b, 6.0, V['crack_glow'], z=-15.5, blur=0.6, alpha=0.3 * flare)
    pad = cv.blob([(shf[0] - 7.5, shf[1] - 1.5), (shf[0] - 4.0, shf[1] - 6.5), (shf[0] + 3.0, shf[1] - 6.8), (shf[0] + 7.0, shf[1] - 2.0),
                   (shf[0] + 4.5, shf[1] + 1.5, 0.0), (shf[0] + 1.5, shf[1] + 0.2), (shf[0] - 1.5, shf[1] + 2.4, 0.0), (shf[0] - 4.5, shf[1] + 0.5)])
    cv.shape(pad, BK, z=58, sd=1.8, hi=0.5, fur=1.0, soft=0.3)
    if bk in ('moss', 'weed', 'grass'):
        for j, dx_ in enumerate((-5.0, -1.0, 3.5)):
            q = (shf[0] + dx_, shf[1] + 0.8 + (j % 2) * 1.2)
            L = 4.0 + j * 1.5 if bk != 'weed' else 7.0 + j * 2
            sw = math.sin(ph + j) * 0.6 - lean * 1.5 + fr * 2.5
            cv.shape(ik.taper_path([cv.W(q), cv.W((q[0] + sw * 0.5, q[1] + L * 0.5)), cv.W((q[0] + sw, q[1] + L))], cv.u(1.6), (0.0, 0.85)),
                     BK, z=57.5 + j * 0.01, sd=0.6, ol=0.8)
    if 'drips' in ex:   # su damlaları
        for j, q in enumerate((h, lerp2(e, h, 0.5), (cc[0] + 4, cc[1] + 12))):
            d = (q[0] + 0.5, q[1] + 5.5 + ((ph * 1.5 + j) % 2.0))
            cv.shape(cv.blob([(d[0], d[1] - 1.6, 0.0), (d[0] + 0.8, d[1] + 0.2), (d[0], d[1] + 0.9), (d[0] - 0.8, d[1] + 0.2)]),
                     Ink('#9fe8e0', '#3a8a96', '#ffffff'), z=63 + j * 0.01, sd=0.4, hi=0.25, ol=0.6, glow=(0.05, 0.3, 0.3))
    # ---- büyü akışı: kolları saran öğe şeritleri, iki elin arasındaki küre, salınış patlaması
    fl = p.get('flow', 0.0)
    if fl > 0 and V['elem'] in ('water', 'fire'):
        for j, (s0, s1, zz) in enumerate(((shf, h, 64), (shb, h_b, -15))):
            for k2 in range(2):
                pts = []
                for i in range(7):
                    u = i / 6
                    q = lerp2(s0, s1, 0.2 + 0.8 * u)
                    a2 = ph * 2.5 + u * 7.0 + k2 * math.pi
                    pts.append((q[0] + math.cos(a2) * 4.5, q[1] + math.sin(a2) * 2.0))
                if V['elem'] == 'water':
                    cv.shape(ik.taper_path([cv.W(q) for q in pts], cv.u(1.3 + fl), (0.2, 0.6)), WATER, z=zz + 0.3 + k2 * 0.01, sd=0.3, hi=0.2, ol=0.6,
                             glow=(0.03, 0.25, 0.28))
                else:
                    cv.stroke(pts, 1.6 + fl * 1.5, z=zz + 0.3 + k2 * 0.01, col=FIRE_Y, taper=(0.2, 0.7), glow=FIRE_G)
    orb_c = None
    if p.get('orb', 0.0) > 0:
        orb_c = lerp2(h, h_b, 0.5)
        orb_c = (orb_c[0] + p.get('orb_dx', 0.0), orb_c[1] + p.get('orb_dy', -3.0))
        _orb(cv, orb_c, p['orb'], V, 66, ph)
    if p.get('burst', 0.0) > 0:
        _burst(cv, (h[0] + 4, h[1] + 2), p.get('bdir', (1.0, 0.4)), p['burst'], V, 67, ph, seed=V['seed'])
    if p.get('gust', 0.0) > 0:
        _burst(cv, (h[0] + 6, -24.0), (1.0, -0.05), p['gust'], dict(V, elem='dust'), 67, ph, seed=V['seed'] + 2)
    hand = u29.to_world(cv, h)
    cv.pop()
    return {'hand': hand}


# ================================================================== v29 animasyon tabloları
REST = dict(bob=0.0, lean=0.0, step=0.0, roar=0.0, flare=0.0, rot=0.0, sx=1.0, sy=1.0, skew=0.0, off=(0.0, 0.0), oy=0.0, turn=0.0,
            al=(0.15, 0.2), ar=(0.25, 0.15), hdy=0.0, hdx=0.0, claw=0.0, br=0.0, fr=0.0, flow=0.0, orb=0.0, orb_dx=0.0, orb_dy=-3.0,
            burst=0.0, bdir=(1.0, 0.4), gust=0.0, blink=0.0, zirh=0.0, eyes=1.0, ash=0.0, dis=0.0, streak=0.0, sdir=(1.0, 0.0),
            vk=0.6, vw=1.0, hover=0.0, leg_sw=0.0)
S2 = math.tau


def _k(t, keys, loop=False):
    return pose_at(t, keys, loop=loop, base=REST)


def _row(frames, fps, loop, pose, ts=None, mk=None):
    return dict(frames=frames, fps=fps, loop=loop, pose=pose, ts=ts, mk=mk)


def _nl(keys):
    return lambda t: _k(t, keys)


# ---- büyücü iyeler (Su / Od)
def _c_idle(t):
    s = math.sin
    return dict(REST, t=t, bob=0.9 * s(S2 * t), rot=0.03 * s(S2 * t - 0.6), sy=1.0 + 0.015 * s(S2 * t), hdy=0.8 * s(S2 * t - 0.9),
                ar=(0.3 + 0.1 * s(S2 * t - 0.5), 0.25 + 0.12 * s(S2 * t - 0.9)), al=(0.2 - 0.08 * s(S2 * t), 0.25), br=0.05 * s(S2 * t - 1.2),
                fr=0.3 * s(S2 * t - 1.5), flow=0.25 + 0.1 * s(S2 * t), flare=0.15 + 0.1 * s(S2 * t))


def _c_walk(t):
    s, c = math.sin, math.cos
    return dict(REST, t=t, step=6.0 * s(S2 * t), bob=1.8 * c(2 * S2 * t), rot=0.08 + 0.03 * s(2 * S2 * t + 1.0), hdy=1.2 * c(2 * S2 * t - 0.8),
                ar=(0.3 - 0.4 * s(S2 * t), 0.2 + 0.15 * s(S2 * t + 0.5)), al=(0.2 + 0.4 * s(S2 * t), 0.25 - 0.1 * s(S2 * t)),
                br=0.08 * s(2 * S2 * t - 1.3), fr=0.6 * s(2 * S2 * t - 1.6), flow=0.2)


_C_WIND = [(0.0, dict(bob=3.0, rot=0.12, sy=0.95, ar=(0.7, 0.7), al=(0.6, 0.8), orb=0.2, orb_dy=0.0, flow=0.5, hdy=1.5, fr=0.5), 'io'),
           (0.2, dict(bob=0.5, rot=-0.02, sy=1.0, ar=(1.8, 0.5), al=(1.6, 0.6), orb=0.45, orb_dy=-2.0, flow=0.8, roar=0.3, flare=0.4, hdy=-0.5, br=-0.1, fr=-0.4), 'o'),
           (0.45, dict(bob=-2.5, rot=-0.1, sy=1.05, ar=(1.85, 0.35), al=(1.75, 0.42), orb=0.8, orb_dy=-4.0, flow=1.0, roar=0.7, flare=0.8, hdy=-2.0, br=-0.2, fr=-0.8, claw=0.6), 'o'),
           (0.7, dict(bob=-3.0, rot=-0.13, sy=1.07, ar=(1.9, 0.38), al=(1.8, 0.44), orb=1.0, orb_dy=-4.5, flow=1.2, roar=1.0, flare=1.0, hdy=-2.6, br=-0.25, fr=-1.0, claw=1.0), 'io'),
           (1.0, dict(bob=-3.2, rot=-0.14, sy=1.08, ar=(1.92, 0.4), al=(1.82, 0.46), orb=1.12, orb_dy=-4.8, flow=1.3, roar=1.0, flare=1.0, hdy=-2.8), 'io')]

_C_SLAM = [(0.0, dict(bob=2.5, rot=0.42, sy=0.92, sx=1.06, ar=(1.25, -0.1), al=(1.05, 0.05), orb=0.0, burst=1.0, bdir=(1.0, 0.5), flow=0.6, roar=1.0, flare=0.8, hdy=1.5,
                      br=0.35, fr=1.2, claw=1.0, streak=0.6, sdir=(1.0, 0.3)), 'i'),
           (0.25, dict(bob=3.0, rot=0.5, sy=0.94, sx=1.04, ar=(1.15, -0.05), burst=1.35, roar=0.9, hdy=2.2, br=0.45, fr=1.4, streak=0.2), 'o'),
           (0.5, dict(bob=2.2, rot=0.36, sy=1.0, sx=1.0, ar=(0.9, 0.1), al=(0.8, 0.2), burst=0.7, roar=0.5, flare=0.4, hdy=1.0, br=0.2, fr=0.6, streak=0.0, flow=0.3), 'o'),
           (0.75, dict(bob=1.0, rot=0.16, ar=(0.5, 0.2), al=(0.4, 0.25), burst=0.25, roar=0.2, flare=0.2, hdy=0.0, br=-0.05, fr=-0.2, claw=0.3), 'io'),
           (1.0, dict(bob=0.3, rot=0.05, ar=(0.3, 0.2), al=(0.2, 0.25), burst=0.0, roar=0.0, flare=0.1, hdy=0.3, br=0.0, fr=0.0, claw=0.0, flow=0.2), 'io')]


def _seq(keys_a, keys_b, split):
    """İki anahtar dizisini tek zaman çizgisine birleştir (a: 0..split, b: split..1)."""
    out = [(tk * split, d, e) for tk, d, e in keys_a]
    out += [(split + tk * (1.0 - split) + (1e-4 if tk == 0 else 0.0), d, e) for tk, d, e in keys_b]
    return out


_C_ATK = _seq(_C_WIND, _C_SLAM, 0.62)
_C_ATK_TS = [0.0, 0.14, 0.3, 0.46, 0.62, 0.72, 0.82, 0.92]

_C_TELEZ = [(0.0, dict(bob=3.2, rot=0.12, sy=0.94, sx=1.04, ar=(0.8, 0.6), al=(0.7, 0.7), zirh=0.3, flow=0.6, hdy=1.5), 'io'),
            (0.3, dict(bob=0.0, rot=-0.08, sy=1.02, sx=1.08, ar=(1.8, -0.05), al=(2.2, -0.15), zirh=0.7, flow=1.0, roar=0.6, flare=0.7, orb=0.5, orb_dy=-4.0, br=-0.2, fr=-0.6, claw=1.0), 'o'),
            (0.6, dict(bob=-3.0, rot=-0.1, sy=1.07, sx=1.1, ar=(1.95, -0.1), al=(2.4, -0.2), zirh=1.0, flow=1.4, roar=1.0, flare=1.0, orb=0.95, orb_dy=-5.0, br=-0.3, fr=-1.0), 'o'),
            (0.8, dict(bob=-3.4, rot=-0.12, sy=1.08, sx=1.11, ar=(1.97, -0.1), al=(2.42, -0.2), zirh=1.0, orb=1.15, roar=1.0, hdy=-2.5), 'io'),
            (1.0, dict(bob=-3.5, rot=-0.13, sy=1.09, sx=1.12, ar=(2.0, -0.1), al=(2.45, -0.2), zirh=1.0, orb=1.25, roar=1.0, hdy=-2.8), 'io')]

_C_BOUT = [(0.0, dict(bob=4.0, rot=0.1, sy=0.88, sx=1.08, ar=(0.6, 0.9), al=(0.5, 1.0), blink=0.3, flow=0.8, roar=0.4, hdy=2.0), 'o'),
           (0.33, dict(bob=-2.0, rot=-0.08, sy=1.18, sx=0.88, ar=(2.6, 0.5), al=(2.5, 0.6), blink=0.8, dis=0.3, flow=1.0, roar=0.8, flare=1.0), 'i'),
           (0.66, dict(bob=-4.0, sy=1.3, sx=0.8, blink=1.0, dis=0.72, flare=1.0), 'l'),
           (1.0, dict(bob=-5.0, sy=1.38, sx=0.76, blink=0.6, dis=0.96), 'l')]
_C_BIN = [(0.0, dict(bob=-5.0, sy=1.35, sx=0.78, blink=0.7, dis=0.92, ar=(2.6, 0.5), al=(2.5, 0.6), flare=1.0, flow=1.0), 'l'),
          (0.33, dict(bob=-2.0, sy=1.15, sx=0.9, blink=1.0, dis=0.5, roar=0.6), 'o'),
          (0.66, dict(bob=3.0, sy=0.86, sx=1.12, blink=0.5, dis=0.08, ar=(1.0, 0.5), al=(0.9, 0.6), roar=0.8, hdy=1.5, flare=0.6), 'o'),
          (1.0, dict(bob=0.8, sy=1.0, sx=1.0, blink=0.0, dis=0.0, ar=(0.4, 0.25), al=(0.3, 0.3), roar=0.1, hdy=0.3, flare=0.2, flow=0.3), 'io')]

_I_HURT = [(0.0, dict(rot=-0.26, sy=0.94, sx=1.04, hdy=-3.0, hdx=-1.5, ar=(0.9, 0.9), al=(1.2, 0.6), roar=0.6, eyes=0.6, br=0.4, fr=1.0, off=(-1.5, 0.0)), 'l'),
           (0.5, dict(rot=-0.16, sy=1.02, sx=0.99, hdy=-1.0, hdx=-0.5, ar=(0.6, 0.6), al=(0.8, 0.5), roar=0.3, eyes=0.85, br=0.2, fr=0.5, off=(-1.8, 0.0)), 'o'),
           (1.0, dict(rot=-0.05, sy=1.0, sx=1.0, hdy=0.0, hdx=0.0, ar=(0.35, 0.25), al=(0.25, 0.25), roar=0.1, eyes=1.0, br=0.0, fr=0.1, off=(-1.2, 0.0)), 'io')]
_I_STAG = [(0.0, dict(rot=-0.34, bob=2.0, hdy=-2.5, ar=(1.0, 1.0), al=(1.3, 0.8), roar=0.8, eyes=0.5, br=0.5, fr=1.2, off=(-2.0, 0.0)), 'l'),
           (0.33, dict(rot=0.18, bob=4.0, hdy=3.5, ar=(0.05, 0.1), al=(0.0, 0.1), roar=0.2, eyes=0.3, br=-0.2, fr=-0.8, off=(-2.5, 0.0)), 'o'),
           (0.66, dict(rot=-0.1, bob=3.0, hdy=1.5, ar=(0.2, 0.2), al=(0.15, 0.2), eyes=0.7, br=0.15, fr=0.4), 'io'),
           (1.0, dict(rot=0.05, bob=1.5, hdy=0.5, ar=(0.3, 0.2), al=(0.2, 0.25), eyes=1.0, br=0.0, fr=0.0, off=(-2.0, 0.0)), 'io')]
_I_DEATH = [(0.0, dict(rot=-0.3, sy=1.06, hdy=-3.5, ar=(2.2, 0.6), al=(2.4, 0.5), roar=1.0, flare=1.0, br=0.4, fr=1.0, claw=1.0), 'l'),
            (0.17, dict(rot=-0.12, bob=4.0, sy=0.98, hdy=0.0, ar=(0.8, 0.6), al=(0.9, 0.5), roar=0.7, flare=0.6, br=-0.1, fr=-0.6, eyes=0.8), 'o'),
            (0.33, dict(rot=0.38, bob=7.0, sy=0.95, hdy=3.0, ar=(0.1, 0.2), al=(0.0, 0.2), roar=0.3, flare=0.2, eyes=0.5, dis=0.12, ash=0.3, blink=0.2), 'io'),
            (0.5, dict(rot=0.62, bob=10.0, hdy=4.5, dis=0.35, ash=0.6, eyes=0.2, blink=0.4), 'io'),
            (0.67, dict(rot=0.75, bob=11.5, dis=0.58, ash=0.9, eyes=0.0, blink=0.5), 'l'),
            (0.83, dict(rot=0.8, bob=12.0, dis=0.8, ash=1.0, blink=0.4), 'l'),
            (1.0, dict(rot=0.82, bob=12.0, dis=0.95, ash=0.8, blink=0.2), 'l')]
_I_SPAWN = [(0.0, dict(bob=12.0, rot=0.5, dis=0.92, blink=0.8, eyes=0.0, ar=(0.1, 0.2), al=(0.0, 0.2), hdy=4.0), 'l'),
            (0.2, dict(bob=9.0, rot=0.35, dis=0.7, blink=1.0, ar=(0.4, 0.3), al=(0.3, 0.3), hdy=3.0), 'o'),
            (0.4, dict(bob=5.0, rot=0.15, dis=0.42, blink=0.8, hdy=1.5, flare=0.4), 'io'),
            (0.6, dict(bob=1.5, rot=-0.1, dis=0.15, blink=0.5, ar=(1.6, 0.4), al=(1.5, 0.5), roar=0.6, flare=0.8, hdy=-1.0, eyes=1.2), 'io'),
            (0.8, dict(bob=-1.5, rot=-0.18, dis=0.0, blink=0.2, ar=(2.4, 0.3), al=(2.3, 0.4), roar=1.0, flare=1.0, hdy=-2.0, eyes=1.3), 'o'),
            (1.0, dict(bob=0.5, rot=0.03, blink=0.0, ar=(0.35, 0.25), al=(0.25, 0.3), roar=0.1, flare=0.2, hdy=0.3, eyes=1.0), 'io')]


def _caster_rows():
    return {
        'idle': _row(6, 8, True, _c_idle),
        'walk': _row(8, 10, True, _c_walk),
        'windup': _row(6, 12, False, _nl(_C_WIND)),
        'slam': _row(5, 12, False, _nl(_C_SLAM)),
        'attack': _row(8, 12, False, _nl(_C_ATK), ts=_C_ATK_TS, mk=[0.62, 0.64, 0.82]),
        'tele_zirh': _row(5, 12, False, _nl(_C_TELEZ)),
        'blink_out': _row(4, 16, False, _nl(_C_BOUT)),
        'blink_in': _row(4, 16, False, _nl(_C_BIN)),
        'hurt': _row(3, 16, False, _nl(_I_HURT)),
        'stagger': _row(4, 10, False, _nl(_I_STAG)),
        'death': _row(7, 10, False, _nl(_I_DEATH)),
        'spawn': _row(6, 10, False, _nl(_I_SPAWN)),
    }


# ---- Tozkoparan: hortum üstünde süzülen iye
def _t_idle(t):
    s = math.sin
    return dict(REST, t=t, bob=-1.0 + 1.6 * s(S2 * t), hover=-2.0, rot=0.05 * s(S2 * t - 0.7), turn=0.03 * s(S2 * t - 0.3), hdy=1.0 * s(S2 * t - 1.0),
                ar=(0.5 + 0.2 * s(S2 * t - 0.4), 0.3 + 0.15 * s(S2 * t - 0.9)), al=(0.4 - 0.2 * s(S2 * t), 0.35), br=0.1 * s(S2 * t - 1.3),
                fr=0.8 * s(S2 * t - 1.5), vk=0.62, vph=S2 * t, leg_sw=1.5 * s(S2 * t - 1.0))


def _t_walk(t):
    """Süzülüş + gövde burulması (×2,6 hızda dönen hortum gibi okunur): kollar sırayla savrulur, hortum döner."""
    s = math.sin
    return dict(REST, t=t, bob=-1.0 + 1.2 * s(2 * S2 * t), hover=-2.0, rot=0.14 + 0.04 * s(S2 * t), turn=0.07 * s(S2 * t), hdy=0.8 * s(2 * S2 * t - 0.8),
                ar=(0.7 + 0.7 * s(S2 * t), 0.35 - 0.2 * s(S2 * t)), al=(0.7 - 0.7 * s(S2 * t), 0.35 + 0.2 * s(S2 * t)), br=0.25 * s(S2 * t - 1.2),
                fr=1.2 * s(S2 * t - 1.5), vk=0.75, vph=S2 * t * 2, leg_sw=-3.0 + 1.5 * s(S2 * t * 2), streak=0.3, sdir=(1.0, 0.0))


_T_WIND = [(0.0, dict(bob=1.0, hover=-1.0, rot=0.08, turn=-0.02, ar=(0.6, 0.6), al=(0.5, 0.6), vk=0.7, hdy=1.0), 'io'),
           (0.25, dict(bob=3.0, rot=-0.05, turn=-0.08, sy=0.94, sx=1.04, ar=(0.9, 1.5), al=(1.4, 1.2), vk=0.85, roar=0.3, flare=0.4, br=-0.2, fr=-0.8), 'o'),
           (0.55, dict(bob=4.5, rot=-0.15, turn=-0.13, sy=0.9, sx=1.06, ar=(1.0, 1.9), al=(1.6, 1.5), vk=1.0, roar=0.6, flare=0.8, br=-0.35, fr=-1.4, claw=1.0, hdy=2.0), 'o'),
           (0.8, dict(bob=5.0, rot=-0.18, turn=-0.15, sy=0.89, sx=1.07, vk=1.05, roar=0.8, flare=1.0, hdy=2.4), 'io'),
           (1.0, dict(bob=5.2, rot=-0.19, turn=-0.16, sy=0.88, sx=1.07, vk=1.1, roar=0.9, flare=1.0, hdy=2.5), 'io')]
_T_SLAM = [(0.0, dict(bob=-1.0, rot=0.32, turn=0.12, sy=1.08, sx=0.95, ar=(1.75, -0.1), al=(2.0, 0.0), gust=1.0, vk=1.0, roar=1.0, flare=0.8, br=0.4, fr=1.5, claw=1.0, hdy=-1.0,
                      streak=0.8, sdir=(1.0, 0.0)), 'i'),
           (0.25, dict(bob=-0.5, rot=0.36, turn=0.16, ar=(1.8, -0.15), al=(2.1, -0.05), gust=1.4, roar=0.9, br=0.5, fr=1.6, streak=0.4), 'o'),
           (0.5, dict(bob=0.5, rot=0.22, turn=0.08, sy=1.02, sx=0.99, ar=(1.3, 0.1), al=(1.5, 0.15), gust=0.8, roar=0.5, flare=0.4, br=0.2, fr=0.7, streak=0.0), 'o'),
           (0.75, dict(bob=0.0, rot=0.1, turn=0.02, ar=(0.8, 0.25), al=(0.8, 0.3), gust=0.3, roar=0.2, vk=0.8, br=0.0, fr=0.0, claw=0.3), 'io'),
           (1.0, dict(bob=-0.8, rot=0.06, turn=0.0, sy=1.0, sx=1.0, ar=(0.5, 0.3), al=(0.4, 0.35), gust=0.0, roar=0.0, flare=0.1, vk=0.65, claw=0.0, hdy=0.5), 'io')]
_T_ATK = _seq(_T_WIND, _T_SLAM, 0.55)
_T_ATK_TS = [0.0, 0.14, 0.3, 0.44, 0.55, 0.66, 0.78, 0.9]
_T_TELEZ = [(0.0, dict(bob=1.0, rot=0.08, turn=-0.02, ar=(0.6, 0.6), al=(0.5, 0.6), vk=0.8, zirh=0.3), 'io'),
            (0.3, dict(bob=3.5, rot=-0.08, turn=-0.1, sy=0.92, sx=1.08, ar=(1.0, 1.7), al=(1.5, 1.4), vk=1.0, roar=0.5, flare=0.7, zirh=0.7, br=-0.3, fr=-1.0), 'o'),
            (0.6, dict(bob=5.0, rot=-0.16, turn=-0.15, sy=0.88, sx=1.12, ar=(1.1, 2.0), al=(1.7, 1.6), vk=1.25, roar=1.0, flare=1.0, zirh=1.0, br=-0.4, fr=-1.6, claw=1.0, hdy=2.2), 'o'),
            (0.8, dict(bob=5.3, sy=0.87, sx=1.13, vk=1.3, zirh=1.0, hdy=2.5), 'io'),
            (1.0, dict(bob=5.5, sy=0.86, sx=1.14, vk=1.35, zirh=1.0, hdy=2.6), 'io')]


def _t_spin(t):
    """Gerçek kasırga dönüşü: gövde tam tur döner (yan görünüş daralır, yarım turda aynalanır), kollar yanlara açık,
    hortum gövdeyi sarar, hız çizgileri."""
    s = math.sin
    return dict(REST, t=t, bob=-2.0 + 0.8 * s(2 * S2 * t), hover=-4.0, rot=0.06, turn=t, sy=1.04, ar=(1.55, 0.05), al=(1.55, 0.05), roar=0.6, flare=0.8,
                br=0.5, fr=1.6, hdy=-1.0, vk=1.35, vw=1.15, vph=S2 * t * 2, leg_sw=-4.0, claw=1.0, streak=0.6, sdir=(math.cos(S2 * t), 0.0))


def _t_dizzy(t):
    """Başı dönmüş: gövde daire çizerek sallanır, baş geç gelir ve sarkar, kollar gevşek, hortum sönükleşip tekler."""
    s, c = math.sin, math.cos
    return dict(REST, t=t, bob=2.0 + 1.0 * s(2 * S2 * t), hover=-1.5, rot=0.16 * s(S2 * t), off=(2.0 * c(S2 * t), 0.0), turn=0.05 * c(S2 * t),
                hdy=2.5 + 2.0 * s(S2 * t - 1.2), hdx=1.5 * c(S2 * t - 1.2), ar=(0.08 + 0.1 * s(S2 * t - 0.8), 0.1), al=(0.05 - 0.1 * s(S2 * t - 0.8), 0.1),
                eyes=0.55, br=0.2 * s(S2 * t - 1.5), fr=1.0 * s(S2 * t - 1.8), vk=0.32 + 0.08 * s(3 * S2 * t), vph=S2 * t, leg_sw=2.0 * s(S2 * t - 1.0))


def _tz(keys):
    out = []
    for tk, d, e in keys:
        d2 = dict(d)
        d2.setdefault('hover', -2.0)
        out.append((tk, d2, e))
    return out


def _toz_rows():
    return {
        'idle': _row(6, 8, True, _t_idle),
        'walk': _row(8, 8, True, _t_walk),
        'windup': _row(6, 14, False, _nl(_T_WIND)),
        'slam': _row(5, 14, False, _nl(_T_SLAM)),
        'attack': _row(8, 14, False, _nl(_T_ATK), ts=_T_ATK_TS, mk=[0.55, 0.57, 0.78]),
        'tele_zirh': _row(5, 12, False, _nl(_T_TELEZ)),
        'spin': _row(8, 20, True, _t_spin),
        'dizzy': _row(8, 10, True, _t_dizzy),
        'hurt': _row(3, 16, False, _nl(_tz(_I_HURT))),
        'stagger': _row(4, 10, False, _nl(_tz(_I_STAG))),
        'death': _row(7, 10, False, _nl(_tz(_I_DEATH))),
        'spawn': _row(6, 10, False, _nl(_tz(_I_SPAWN))),
    }


DURUM = {
    'caster': {'idle': 'idle', 'chase': 'walk', 'windup': 'windup', 'windup_zirh': 'tele_zirh', 'slam': 'slam', 'recover': 'idle',
               'blink_out': 'blink_out', 'blink_in': 'blink_in', 'hurt': 'hurt', 'stagger': 'stagger', 'death': 'death', 'spawn': 'spawn'},
    'tornado': {'idle': 'idle', 'chase': 'walk', 'windup': 'windup', 'windup_zirh': 'tele_zirh', 'slam': 'slam', 'spin': 'spin', 'dizzy': 'dizzy',
                'recover': 'idle', 'hurt': 'hurt', 'stagger': 'stagger', 'death': 'death', 'spawn': 'spawn'},
}
_CACHE = {}


def anims_for(var):
    key = 'tornado' if var == 'tozkoparan' else 'caster'
    if key not in _CACHE:
        _CACHE[key] = _toz_rows() if key == 'tornado' else _caster_rows()
    return _CACHE[key]


def durum_for(var):
    return DURUM['tornado' if var == 'tozkoparan' else 'caster']


def frame_time(row, i):
    if row['ts']:
        return row['ts'][i]
    if row['loop']:
        return i / row['frames']
    return i / max(1, row['frames'] - 1)


SHADE = dict(outer=0.6, rim=0.7, rim_col=(0.68, 0.76, 1.0), rim_dir=(0.6, -0.8), rim_w=1.6, form=(7.0, (0.74, 0.72, 0.86)))


def render_frame(anim, i, var='su_iyesi', ss=3):
    V = VARIANTS[var]
    row = anims_for(var)[anim]
    tt = frame_time(row, i)
    p = dict(row['pose'](tt))
    has_vph = 'vph' in p
    p['ph'] = tt * math.tau if row['loop'] else (tt * 0.8 + i * 0.37) * math.tau
    if not has_vph:
        p['vph'] = p['ph']
    split = p.get('dis', 0.0) > 0
    if split:
        p['_fx'] = 'body'
    cv = u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss)
    info = draw(cv, p, V)
    rgba, nm, em = cv.finish(**SHADE)
    if split:
        hot = {'water': (0.3, 1.0, 0.95), 'fire': (1.0, 0.5, 0.1), 'dust': (1.0, 0.75, 0.35)}[V['elem']]
        rgba, em = u29.dissolve(rgba, em, p['dis'], seed=V['seed'] * 13 + (1 if anim in ('spawn', 'blink_in') else 0), hd=cv.hd,
                                grad=(0.0, 0.8), hot=hot, hot_a=0.9)
        if p.get('blink', 0.0) > 0 or p.get('ash', 0.0) > 0:
            cf = u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss)
            draw(cf, dict(p, _fx='fx'), V)
            fr, fn_, fe = cf.finish(outer=0.4)
            rgba, em = u29.over(fr, fe, rgba, em)
    return rgba, nm, em, info
