"""Balbal (kimlik balbal) ve Buz Balbalı (buz_balbali) — stil v2 "mürekkep-cel". v1: creatures.draw_balbal.

v29 tam gövde animasyonu (docs/TASARIM.md "v29: yer yaratıklarının tam gövde animasyonu"): taş heykelin bacağı yok;
"ayağı" kaidesidir — kaide yere basar, kaymaz (hareket sekiştir). İskelet: bütün figür dönüşümü (x / y / roll: kaide
kenarı ya da gövde ortası çevresinde devrilme, ezilme-esneme), gövde kaidenin üstünde bel noktasında eğilir (pitch),
bükülür (lean: omurga kavsi), şişer (swell: "!!"), burulur (tw: yakın omuz geriye), baş boyun dibinde döner (hr) ve
önden gider (hd); ön kol açılarla (arm) + kılıç açısı (swang), saç örgüsü ve kemer kesesi gecikmeli sallanır (proc).
Taş etkileri: çatlaklar (crack; uyanışta / "!!"de içinden runa ışığı sızar: cglow), omuzdan dökülen toz (drip),
yere çarpan taşın kıymıkları (chips), toz bulutu (dust), çakma halkası (ring), kılıç izi (smear), uyurken üstünü örten
toz (dorm), ölümde moloz yığını (rubble), yere düşen baş (hfree) ve kılıç (swfree).

Hücre dünya 88x80 (doku 4), ayak (36, 74). Satırlar SEQS'te, yapay zekâ (hopper + intikam "cut") eşlemesi DURUM'da.
Çapa yok (v1'de de yoktu).

Tasarım: Göktürk kurganlarının önüne dikilen balbal taşları, öldürülen düşmanı ya da alpın kendisini simgeler: kaba
yontulmuş granit gövde, düz oyma yüz, sarkık bıyık, sağ elde göğse tutulan kadeh, belde kemer ve kılıç. Burada
Erlik'in sesiyle uyanmış bir alp heykeli: yontu yüzeyleri (düz düzlemler, keski izleri), çatlaklar, bozkır taşlarına
özgü turuncu liken lekeleri ve yosun; Orhun runaları ve göz yarıkları uyanınca camgöbeği yanar. Uyurken (dormant)
kılıç kında, runalar sönük.

buz_balbali (Kaf): buz kabuğu tutmuş açık mavi taş, bıyıktan/kollardan sarkan buz, buzdan kılıç, ayaz mavisi runalar.
"""
import math

import numpy as np
import skia

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_arm, lerp2
import yaratik_govde as yg
import yaratik_ink_kit as yk
from yaratik_govde import Seq

TEX = 4.0
CELL = (352, 320)       # dünya 88 x 80
FEET = (144, 296)       # dünya (36, 74)


def _v(**kw):
    base = dict(
        stone=Ink('#9a958a', '#4e4c5e', '#c8c2b0', '#2c2a3a', name='granit'),
        stone2=Ink('#a8a294', '#585566', '#d4cebc', '#302e40', name='kabartma'),
        stone_l=Ink('#bdb6a4', '#66626e', '#e6e0cc', '#3a3846', name='yüz düzlemi'),
        stone_d=Ink('#6e6a6c', '#38364a', '#8e8a88', '#201e2c', name='kaide'),
        lichen=(0.86, 0.52, 0.18), moss=(0.36, 0.48, 0.26), dust=(0.78, 0.74, 0.66),
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
        lichen=(0.92, 0.97, 1.0), moss=(0.75, 0.88, 1.0), dust=(0.86, 0.92, 1.0),
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

# Çatlak ağı (gövde yereli, L() öncesi): (yol, eşik) — crack eşiği geçince görünür; uzunluk crack ile büyür
CRACKS_BODY = [
    ([(-9.6, -19.0), (-7.2, -18.2), (-6.0, -15.6), (-3.6, -15.0)], 0.0),
    ([(9.8, -22.0), (7.4, -20.6), (7.8, -17.4), (5.6, -16.2)], 0.15),
    ([(3.4, -30.6), (4.0, -28.4), (2.6, -26.8)], 0.3),
    ([(-8.8, -9.0), (-6.4, -10.6), (-4.2, -9.8), (-2.4, -11.6)], 0.45),
    ([(9.6, -9.4), (7.0, -10.8), (6.2, -12.4)], 0.55),
    ([(-1.0, -24.0), (0.6, -21.0), (-0.6, -18.6), (0.8, -16.0)], 0.7),
]
CRACKS_BASE = [
    ([(-12.0, -3.4), (-9.6, -2.6), (-8.6, -0.4)], 0.2),
    ([(11.4, -4.6), (9.2, -3.4), (9.8, -1.0)], 0.5),
]
CRACKS_HEAD = [   # baş yereli: hc çevresinde
    ([(-6.2, 1.0), (-4.0, 1.8), (-3.4, 4.2)], 0.25),
    ([(2.0, -8.6), (1.2, -6.4), (2.4, -4.8)], 0.6),
]

WAIST = (0.0, -6.0)     # gövde eğilme noktası (kaide üstü)
COM = (0.0, -24.0)      # savrulmada dönme merkezi


def _rune(cv, x, y, k, V, z, a, s=2.6, glow_k=1.0):
    """Runa damgası; a: yanma (0 sönük .. 1 yanık), glow_k: parlama (1 olağan, >1 alevlenme)."""
    lit = a > 0.05
    for pa, pb in RUNES[k % len(RUNES)]:
        p0 = (x + pa[0] * s * 0.7, y + pa[1] * s)
        p1 = (x + pb[0] * s * 0.7, y + pb[1] * s)
        cv.stroke([p0, p1], 1.9, z=z, col=INK if not lit else (0.06, 0.2, 0.22), taper=(0.0, 0.0))
        if lit:
            col = V['rune_hot'] if glow_k > 1.05 else V['rune']
            col = tuple(0.15 + (c - 0.15) * min(1.0, a) for c in col)
            cv.stroke([p0, p1], 1.0, z=z + 0.01, col=col, taper=(0.0, 0.0),
                      glow=tuple(g * min(1.0, a) for g in V['rune_glow']))
    if lit:
        yk.glow_soft(cv, (x + s * 0.35, y + s * 0.5), s * (0.6 + 0.25 * glow_k), V['rune_glow'], z=z + 0.02, blur=0.6,
                     alpha=(0.12 + 0.12 * (glow_k - 1)) * min(1.0, a))


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


def _dorm(V, cv, pts, seed, r=1.0):
    """Uyurken üst yüzeyleri örten soluk toz / kum yığıntısı (details)."""
    rng = np.random.default_rng(seed)
    out = []
    for (x, y, w) in pts:
        for k in range(3):
            q = (x + rng.uniform(-w, w) * 0.6, y + rng.uniform(-0.3, 0.5))
            out.append(('col', cv.ellipse(q, w * rng.uniform(0.35, 0.6) * r, 0.7 * r, rng.uniform(-0.2, 0.2)), V['dust']))
    return out


def _cracks(cv, lst, amt, glow, V, z, T=lambda q: q, w=1.25):
    """Çatlaklar: mürekkep çizgisi; glow > 0 ise içinden runa ışığı sızar."""
    if amt <= 0.02:
        return
    for pts, th in lst:
        if amt <= th:
            continue
        f = min(1.0, (amt - th) / 0.35)
        n = len(pts)
        m = max(2, int(math.ceil(f * (n - 1))) + 1)
        q = [T(p) for p in pts[:m]]
        if f < 1.0 and m >= 2:   # son parça kısmi
            fr = f * (n - 1) - (m - 2)
            q[-1] = lerp2(q[-2], q[-1], max(0.05, min(1.0, fr)))
        cv.stroke(q, w + 0.5 * f, z=z, col=INK, taper=(0.1, 0.6))
        if glow > 0.05:
            cv.stroke(q, 0.6 + 0.5 * glow, z=z + 0.01, col=V['rune_hot'], taper=(0.2, 0.7),
                      glow=tuple(g * min(1.0, glow) for g in V['rune_glow']))


def _sword(cv, h, ang, V, z, awake, flare, s_len=1.0):
    """Taş kılıç: h kabza (el), ang yön (0 aşağı, + ileri). Uç noktasını döndürür."""
    dx, dy_ = math.sin(ang), math.cos(ang)
    Ls = 18.5 * s_len
    tip = (h[0] + dx * Ls, h[1] + dy_ * Ls)
    pom = (h[0] - dx * 3.2, h[1] - dy_ * 3.2)
    nx, ny = -dy_, dx
    cv.shape(cv.capsule(pom, h, 1.0, 0.95), V['stone_d'], z=z - 2, sd=0.5, hi=0.3)
    bl0 = (h[0] + dx * 2.0, h[1] + dy_ * 2.0)
    k = Ls / 18.5
    blade = cv.blob([(bl0[0] + nx * 2.2, bl0[1] + ny * 2.2), (h[0] + dx * 10.0 * k + nx * 2.6, h[1] + dy_ * 10.0 * k + ny * 2.6),
                     (h[0] + dx * 15.5 * k + nx * 2.0, h[1] + dy_ * 15.5 * k + ny * 2.0),
                     (tip[0] + nx * 0.6, tip[1] + ny * 0.6, 0.0), (h[0] + dx * 15.5 * k - nx * 1.0, h[1] + dy_ * 15.5 * k - ny * 1.0),
                     (bl0[0] - nx * 1.8, bl0[1] - ny * 1.8)])
    bdet = [('ink', [(h[0] + dx * 4 + nx * 0.2, h[1] + dy_ * 4 + ny * 0.2), (h[0] + dx * 14 * k + nx * 0.2, h[1] + dy_ * 14 * k + ny * 0.2)], 1.6, (0.1, 0.3))]
    bdet += [('ink', [(h[0] + dx * (6 + j * 3.5) - nx * 1.1, h[1] + dy_ * (6 + j * 3.5) - ny * 1.1),
                      (h[0] + dx * (6.8 + j * 3.5) - nx * 0.4, h[1] + dy_ * (6.8 + j * 3.5) - ny * 0.4)], 0.8) for j in range(3)]
    cv.shape(blade, V['blade'], z=z, sd=1.0, hi=0.45, details=bdet, glow=None)
    if awake > 0.3:   # oluktaki runa ışığı
        gl = [(h[0] + dx * 4.5 + nx * 0.2, h[1] + dy_ * 4.5 + ny * 0.2), (h[0] + dx * 13.5 * k + nx * 0.2, h[1] + dy_ * 13.5 * k + ny * 0.2)]
        cv.stroke(gl, 0.8 + 0.5 * flare, z=z + 0.2, col=V['rune_hot'], taper=(0.2, 0.3), glow=V['rune_glow'])
        if flare > 0:
            yk.glow_soft(cv, lerp2(h, tip, 0.55), 5.0, V['rune_glow'], z=z + 0.3, blur=0.6, alpha=0.4 * flare, ry=3.0)
    cv.shape(cv.capsule((h[0] - nx * 3.4, h[1] - ny * 3.4), (h[0] + nx * 3.4, h[1] + ny * 3.4), 1.05, 1.05), V['stone_d'], z=z + 2, sd=0.5, hi=0.3)
    if V['ice']:
        yk.icicles(cv, [(h[0] - nx * 3.0, h[1] - ny * 3.0 + 0.6), (h[0] + nx * 3.0, h[1] + ny * 3.0 + 0.6)], ICE, z + 2.2, L=2.0, w=0.5, seed=5)
    return tip


def _smear(cv, c, r, a0, a1, al, V, z):
    """Kılıç izi: c çevresinde a0'dan a1'e (kılıç açısı kuralı) incelen hilal; ucu kalın (şimdiki konum)."""
    if al <= 0.02 or abs(a1 - a0) < 0.05:
        return
    n = 14
    outer, inner = [], []
    for i in range(n + 1):
        t = i / n
        a = a0 + (a1 - a0) * t
        d = (math.sin(a), math.cos(a))
        w = r * (0.02 + 0.5 * t ** 1.6)
        outer.append((c[0] + d[0] * (r + 0.6), c[1] + d[1] * (r + 0.6)))
        inner.append((c[0] + d[0] * (r - w), c[1] + d[1] * (r - w)))
    # yerin altına taşmasın: cihaz uzayında yer çizgisine kırp
    gy = (0.3 * cv.k + cv.oy) * cv.ss
    dev = [cv.W(q) for q in outer + inner[::-1]]
    path = ik.poly_path([(x, min(y, gy)) for x, y in dev])
    edge = [q for q in outer if yg.world(cv, q)[1] < 0.3]
    yk.wash(cv, path, (0.96, 0.97, 1.0), 0.75 * al, z=z, glow=V['rune_glow'], glow_a=0.35 * al)
    if len(edge) > 1:
        cv.stroke(edge, 1.3, z=z + 0.01, col=(0.22, 0.24, 0.32), taper=(0.9, 0.05), alpha=0.8 * al)
    for k in (0.35, 0.65):   # hız çizgileri
        ln = [lerp2(outer[i], inner[i], k) for i in range(int(n * 0.35), n + 1)]
        ln = [q for q in ln if yg.world(cv, q)[1] < 0.3]
        if len(ln) < 2:
            continue
        cv.stroke(ln, 0.8, z=z + 0.02, col=(0.55, 0.6, 0.72), taper=(0.9, 0.2), alpha=0.6 * al)


def _chips(cv, c, amt, ang, spread, seed, V, z, rad=9.0, n=9):
    """Taş kıymıkları: c'den ang yönüne (radyan, ekran: 0 sağ, -pi/2 yukarı) saçılan köşeli parçalar + toz zerresi."""
    if amt <= 0.02:
        return
    rng = np.random.default_rng(int(seed))
    S = V['stone_d']
    for i in range(n):
        a = ang + rng.uniform(-0.5, 0.5) * spread
        d = rad * amt * rng.uniform(0.35, 1.0)
        q = (c[0] + math.cos(a) * d, c[1] + math.sin(a) * d)
        r = rng.uniform(0.45, 1.15) * (0.6 + 0.4 * amt)
        k = rng.integers(3, 5)
        rot = rng.uniform(0, math.tau)
        pts = [(q[0] + math.cos(rot + j / k * math.tau) * r * rng.uniform(0.7, 1.2),
                q[1] + math.sin(rot + j / k * math.tau) * r * rng.uniform(0.7, 1.2), 0.0) for j in range(k)]
        cv.shape(cv.blob(pts), S if i % 3 else V['stone'], z=z + i * 0.01, sd=0.4, hi=0.2, ol=0.7)
        if i % 2 == 0:   # iz çizgisi
            back = (q[0] - math.cos(a) * 2.2 * amt, q[1] - math.sin(a) * 2.2 * amt)
            cv.stroke([back, q], 0.8, z=z - 0.01, col=(0.3, 0.3, 0.36), taper=(0.9, 0.1), alpha=0.6)


def _dust(cv, c, amt, V, z, seed=1, w=14.0):
    """Yer tozu: kaidenin iki yanına yayılan yarı saydam toz + mürekkepli topaklar."""
    if amt <= 0.02:
        return
    rng = np.random.default_rng(seed)
    dm = Ink(tuple(min(1.0, x * 1.0) for x in V['dust']), tuple(x * 0.62 for x in V['dust']), (1.0, 0.98, 0.94), name='toz')
    for sgn in (-1, 1):
        for k in range(3):
            q = (c[0] + sgn * (w * 0.55 + k * 3.6) * (0.6 + 0.4 * amt), c[1] - 1.2 - k * 0.8 * amt)
            r = (2.6 - k * 0.5) * (0.5 + 0.7 * amt)
            yk.wash(cv, cv.ellipse(q, r * 1.5, r, 0.0), V['dust'], 0.35 * amt, z=z - 0.1, blur=0.8)
            if k < 2 and amt > 0.25:
                yk.puff(cv, q, r * 0.8, dm, z + k * 0.01 + (0.02 if sgn > 0 else 0.0), seed=seed + k * 3 + (sgn > 0), n=6, ol=0.55)


def _ring(cv, c, amt, V, z):
    """Çakma halkası: yerde genişleyen şok dalgası (önü kalın) + runa ışığı."""
    if amt <= 0.02:
        return
    rx = 8.0 + 22.0 * amt
    ry = 2.0 + 2.6 * amt
    al = 1.0 - 0.6 * amt
    front = [(c[0] + math.cos(a) * rx, c[1] + math.sin(a) * ry) for a in np.linspace(0.05, math.pi - 0.05, 18)]
    back = [(c[0] + math.cos(a) * rx, c[1] + math.sin(a) * ry) for a in np.linspace(math.pi + 0.15, math.tau - 0.15, 14)]
    cv.stroke(back, 1.2, z=-4, col=V['rune'], taper=(0.6, 0.6), glow=V['rune_glow'], alpha=0.6 * al)
    cv.stroke(front, 2.4, z=z, col=(0.96, 1.0, 1.0), taper=(0.7, 0.7), glow=V['rune_glow'], alpha=al)
    cv.stroke([(q[0], q[1] + 0.4) for q in front], 1.0, z=z + 0.01, col=(0.2, 0.22, 0.3), taper=(0.7, 0.7), alpha=0.6 * al)
    yk.glow_soft(cv, c, rx * 0.8, V['rune_glow'], z=z, blur=0.6, alpha=0.35 * al, ry=ry * 1.6)


def _rubble(cv, amt, V, z, seed=11):
    """Ölüm sonu moloz yığını: kaidenin üstünde / önünde kırık granit blokları."""
    if amt <= 0.02:
        return
    rng = np.random.default_rng(seed)
    S, S2, SD = V['stone'], V['stone2'], V['stone_d']
    blocks = [(-6.5, -7.5, 4.2), (2.5, -8.2, 4.6), (8.5, -6.4, 3.6), (-1.5, -11.5, 3.8), (5.0, -12.0, 3.0), (-9.0, -5.6, 3.0),
              (12.5, -1.6, 2.6), (-13.0, -1.2, 2.2), (15.5, -0.9, 1.6), (0.5, -15.0, 2.6)]
    for i, (x, y, r) in enumerate(blocks):
        f = min(1.0, max(0.0, amt * 1.6 - i * 0.07))
        if f <= 0.02:
            continue
        rr = r * (0.55 + 0.45 * f)
        yy = y * (0.45 + 0.55 * f) if y < -3 else y
        k = int(rng.integers(5, 7))
        rot = rng.uniform(0, math.tau)
        pts = [(x + math.cos(rot + j / k * math.tau) * rr * rng.uniform(0.75, 1.15),
                yy + math.sin(rot + j / k * math.tau) * rr * rng.uniform(0.65, 1.0), 0.0 if j % 2 else 0.6) for j in range(k)]
        det = [('ink', [(x - rr * 0.4, yy - rr * 0.1), (x + rr * 0.1, yy + rr * 0.3)], 0.9)]
        if i in (0, 3):
            det += _lichen(V, cv, [(x + 0.5, yy - rr * 0.4)], seed + i, 0.7)
        cv.shape(cv.blob(pts), (S, S2, SD)[i % 3], z=z + i * 0.05, sd=1.2, hi=0.4, details=det, hatch=0.3)


def _rest():
    return dict(x=0.0, y=0.0, roll=0.0, rp=0.0, rc=0.0, sq=0.0, sx=1.0, pitch=0.0, lean=0.0, swell=1.0, sink=0.0, tw=0.0,
                shy=0.0, hd=(0.0, 0.0), hr=0.0, arm=(0.35, 0.9), swang=1.0, sword=1.0, awake=1.0, flare=0.0, eye=0.0,
                crack=0.0, cglow=0.0, drip=0.0, dorm=0.0, chips=0.0, chip=(14.0, -2.0, -1.2, 1.4, 1.0), dust=0.0,
                ring=0.0, ringx=0.0, smear=(0.0, 0.0, 0.0), rubble=0.0, hfree=0.0, swfree=0.0, swp=(20.0, -1.5, 1.45),
                brd=0.0, pouch=0.0, pulse=0.0, blink=0.0)


REST = _rest()


def _head(cv, p, V, hc, awake, flare):
    """Baş grubu (çağıran dönüşümü kurar): yuvarlak yüz, alçak börk, sarkık bıyık."""
    S, S2, SL, SD = V['stone'], V['stone2'], V['stone_l'], V['stone_d']
    hx, hy = hc
    head = cv.blob([(hx - 6.6, hy - 2.0), (hx - 5.4, hy - 6.8), (hx + 1.0, hy - 8.4), (hx + 6.4, hy - 5.8), (hx + 7.2, hy + 1.0),
                    (hx + 5.4, hy + 6.6), (hx + 0.6, hy + 8.0), (hx - 4.6, hy + 6.0), (hx - 6.8, hy + 2.4)])
    hdet = [('ink', [(hx + 4.6, hy - 4.6), (hx + 3.6, hy - 3.0), (hx + 4.4, hy - 1.6)], 1.0, (0.0, 0.6))]
    hdet += _lichen(V, cv, [(hx - 4.5, hy + 3.0)], 13, 0.8)
    cv.shape(head, S, z=2, sd=2.4, hi=0.5, details=hdet, hatch=0.3)
    # börk
    cdet = [('ink', [(hx - 4.0, hy - 9.0), (hx - 2.6, hy - 6.2), (hx - 3.0, hy - 3.6)], 1.0),
            ('ink', [(hx + 2.4, hy - 10.2), (hx + 3.2, hy - 7.0), (hx + 3.0, hy - 3.8)], 1.0)] + _lichen(V, cv, [(hx - 2.0, hy - 8.6)], 17, 0.9)
    if p['dorm'] > 0.05:
        cdet += _dorm(V, cv, [(hx - 1.0, hy - 10.0, 4.5), (hx + 3.5, hy - 9.2, 3.0)], 31, p['dorm'])
    cap = cv.blob([(hx - 7.4, hy - 3.2), (hx + 7.0, hy - 3.4), (hx + 5.6, hy - 8.8), (hx + 0.5, hy - 10.8), (hx - 5.6, hy - 9.4)])
    cv.shape(cap, S2, z=10, sd=1.6, hi=0.5, details=cdet)
    cv.shape(cv.capsule((hx - 7.5, hy - 3.5), (hx + 7.1, hy - 3.6), 1.15, 1.15), SD, z=13, sd=0.5, hi=0.3)
    # yüz düzlemi + kaş, gözler, burun, sarkık bıyık, sakal
    face = cv.blob([(hx + 0.2, hy - 2.4), (hx + 6.6, hy - 2.6), (hx + 7.0, hy + 3.0), (hx + 5.0, hy + 6.4), (hx + 1.0, hy + 5.0), (hx - 0.6, hy + 1.0)])
    cv.shape(face, SL, z=16, sd=1.2, hi=0.3, flat=False, ol=0.7)
    ey = p['eye']
    brow = -0.6 * ey   # öfke: kaş içe çöker
    cv.stroke([(hx + 0.2, hy - 1.8 + brow * 0.2), (hx + 3.2, hy - 2.2 - brow), (hx + 6.8, hy - 1.6 + brow * 0.6)], 1.8 + 0.4 * ey, z=20, col=INK, taper=(0.2, 0.2))
    bl = p['blink']
    for ex_ in (1.9, 5.2):
        cv.fill(cv.ellipse((hx + ex_, hy - 0.5), 1.0, 0.45 * (1.0 - 0.6 * bl), 0.0), INK, z=21)
        if awake > 0.3 and bl < 0.8:
            a = min(1.0, (awake - 0.3) / 0.5)
            yk.eye_glow(cv, (hx + ex_, hy - 0.5), 0.8 + 0.25 * ey, 0.28 * (1 + flare * 0.5 + ey * 0.4) * (1.0 - bl), 0.0, V['rune_hot'],
                        tuple(g * a for g in V['rune_glow']), 22, halo=1.6 + flare + ey, halo_a=(0.25 + 0.2 * flare + 0.2 * ey) * a)
    if ey > 0.2 and awake > 0.5:   # "!!": gözden geriye akan ışık izi
        for ex_ in (5.2,):
            cv.stroke([(hx + ex_ - 0.4, hy - 0.5), (hx + ex_ - 3.0 * ey - 1.0, hy - 1.1 - 0.4 * ey)], 0.9 + 0.6 * ey, z=22.5, col=V['rune_hot'],
                      taper=(0.1, 0.9), glow=V['rune_glow'])
    cv.stroke([(hx + 3.7, hy - 0.2), (hx + 4.1, hy + 1.6), (hx + 3.5, hy + 2.0)], 1.1, z=22, col=INK)
    must = cv.blob([(hx + 3.6, hy + 2.3), (hx + 1.2, hy + 2.8), (hx + 0.2, hy + 5.0), (hx + 0.4, hy + 6.6, 0.0), (hx + 1.0, hy + 4.4),
                    (hx + 3.6, hy + 3.3), (hx + 6.4, hy + 4.4), (hx + 7.0, hy + 6.6, 0.0), (hx + 7.0, hy + 4.8), (hx + 6.0, hy + 2.8)])
    cv.shape(must, S2, z=24, sd=0.9, hi=0.3, details=[('ink', [(hx + 1.4, hy + 3.4), (hx + 0.8, hy + 5.0)], 0.7)])
    cv.stroke([(hx + 2.6, hy + 4.4), (hx + 3.7, hy + 4.7 - 0.5 * ey), (hx + 4.8, hy + 4.4)], 1.0, z=24.1, col=INK)
    _cracks(cv, CRACKS_HEAD, p['crack'], p['cglow'], V, 16.5, T=lambda q: (hx + q[0], hy + q[1]), w=1.0)
    if V['ice']:
        yk.icicles(cv, [(hx + 0.6, hy + 6.3), (hx + 6.9, hy + 6.3), (hx - 4.0, hy + 6.0), (hx + 3.5, hy + 7.2)], ICE, 24.5, L=2.6, w=0.6, seed=2)
        yk.icicles(cv, [(hx - 6.0, hy - 3.0), (hx + 6.4, hy - 3.2)], ICE, 13.5, L=2.4, w=0.7, seed=3)


def _clip_begin(cv, path):
    """Bundan sonra kuyruğa giren her çizimi path içine kırp (ölümde kaideye gömülen gövde)."""
    o_q = cv._q

    def q(z, fn):
        def g(c):
            c.save()
            c.clipPath(path, doAntiAlias=True)
            cv.ec.save()
            cv.ec.clipPath(path, doAntiAlias=True)
            try:
                fn(c)
            finally:
                cv.ec.restore()
                c.restore()
        o_q(z, g)
    cv._q = q
    return o_q


def draw(cv, p, V):
    yg.bake_xf(cv)
    q0 = dict(REST)
    q0.update(p)
    p = q0
    awake = p['awake']
    flare = p['flare']
    gk = 1.0 + flare + 0.25 * p['pulse']
    S, S2, SL, SD = V['stone'], V['stone2'], V['stone_l'], V['stone_d']
    # ---- yer etkileri (dünya; figürden bağımsız): halka, toz, kıymık
    _ring(cv, (p['ringx'], 0.2), p['ring'], V, 44)
    _dust(cv, (p['x'], 0.0), p['dust'], V, 45, seed=3)
    cx, cy, ca, csp, cseed = p['chip']
    _chips(cv, (cx, cy), p['chips'], ca, csp, cseed, V, 46)
    if p['swfree'] > 0.5:   # yere düşmüş kılıç (ölüm)
        sx_, sy_, sa_ = p['swp']
        _sword(cv, (sx_, sy_), sa_, V, 39, 0.0, 0.0)
    # ---- figür dönüşümü: kaide kenarı (rp) ya da gövde ortası çevresinde devrilme + ezilme-esneme
    sq = p['sq']
    piv = lerp2((p['rp'], 0.0), COM, p['rc'])
    yg.xf_push(cv, piv, p['roll'], p['x'], p['y'], (1 + sq * 0.12) * p['sx'], 1 - sq * 0.14)
    # ---- kaide: kaba yontulmuş blok
    base = cv.blob([(-12.5, 0.4, 0.0), (12.5, 0.4, 0.0), (11.5, -5.0), (6.0, -6.4, 0.0), (-4.0, -6.6), (-11.5, -5.5, 0.0)])
    bdet = [('ink', [(-12, -2.0), (-4, -1.4), (3, -2.2), (12, -1.6)], 1.0, (0.2, 0.2)),
            ('ink', [(5.5, -6.0), (6.5, -3.0), (5.8, 0.0)], 1.2), ('ink', [(-6.0, -6.2), (-6.8, -3.4)], 1.0)]
    bdet += _lichen(V, cv, [(-9.0, -4.8), (9.0, -1.2)], 3, 1.0)
    if p['dorm'] > 0.05:
        bdet += _dorm(V, cv, [(-8.0, -5.8, 3.0), (2.0, -6.4, 4.0)], 5, p['dorm'])
    cv.shape(base, SD, z=-2, sd=2.2, hi=0.5, details=bdet, hatch=0.4)
    for i in range(3):
        _rune(cv, -8.0 + i * 6, -4.6, i + 2, V, 40, awake, s=2.4, glow_k=gk)
    _cracks(cv, CRACKS_BASE, p['crack'], p['cglow'], V, 40.5)
    _rubble(cv, p['rubble'], V, 41)
    # ---- gövde dönüşümü: bel noktasında eğilme (pitch), şişme (swell), ölümde kaideye gömülme (sink)
    o_q = None
    if p['sink'] > 0.05:
        clip = cv.poly([(-60, -95), (70, -95), (70, -5.0), (11.5, -5.0), (6.0, -6.2), (-4.0, -6.4), (-11.5, -5.3), (-60, -5.3)])
        o_q = _clip_begin(cv, clip)
    yg.xf_push(cv, WAIST, p['pitch'], 0.0, p['sink'], p['swell'], 1.0 + (p['swell'] - 1.0) * 0.4)
    lean = p['lean']
    L = lambda x, y, *t: (x + lean * (-y - 6.0) * 0.12, y) + tuple(t)
    tw = p['tw']
    # ---- arka saç örgüsü (taş): brd ikincil salınım (kökte döner)
    br0 = L(-5.5, -41)
    braid = [br0] + [yg.rot_about(L(*b), br0, p['brd']) for b in ((-7.0, -36), (-7.8, -30))]
    cv.shape(ik.taper_path([cv.W(q) for q in braid], cv.u(3.2), (0.0, 0.5)), S2, z=-3, sd=1.0,
             details=[('ink', [along_(braid[0], braid[2], t, -1.2), along_(braid[0], braid[2], t + 0.08, 1.2)], 0.9, (0.1, 0.1)) for t in (0.2, 0.4, 0.6, 0.8)])
    # ---- gövde: kaftanlı taş blok (yontu düzlemleri)
    body = cv.blob([L(-9.5, -6), L(9.8, -6, ), L(10.2, -13), L(9.0, -27), L(5 + tw * 0.3, -30.8), L(-5.5, -30.8), L(-9.2, -27.5), L(-10.2, -13)])
    det = []
    det.append(('hi', cv.blob([L(-9.2, -27), L(-5.0, -30.2), L(-2.0, -29), L(-4.0, -16), L(-8.8, -14)])))
    det.append(('ink', [L(-2.0, -29), L(-4.0, -16), L(-3.4, -8)], 1.0, (0.2, 0.4)))
    det.append(('shade', cv.blob([L(6.5, -28), L(9.2, -26), L(10.2, -13), L(9.8, -6.5), L(6.5, -7), L(7.2, -18)])))
    det += [('ink', [L(1.0, -30.2), L(2.0, -24), L(2.6, -15)], 1.5, (0.1, 0.3)),
            ('ink', [L(-9.6, -7.6), L(0, -7.2), L(9.6, -7.6)], 1.3, (0.1, 0.1)),
            ('ink', [L(-3.0, -29), L(-3.8, -26), L(-2.6, -23.5), L(-3.6, -21)], 1.1, (0.0, 0.6))]
    for k in range(6):
        x0 = -7.5 + k * 2.6
        y0 = -11.5 - (k % 3) * 0.8
        det.append(('ink', [L(x0, y0), L(x0 + 1.2, y0 - 0.8)], 0.8, (0.3, 0.3)))
    det += _lichen(V, cv, [L(-8.4, -24), L(7.4, -8.5), L(-6.0, -9.0)], 7, 1.0)
    if p['dorm'] > 0.05:
        det += _dorm(V, cv, [(*L(-5.0, -30.4), 3.5), (*L(4.0, -30.4), 2.5)], 9, p['dorm'])
    cv.shape(body, S, z=0, sd=4.0, hi=0.6, details=det, hatch=0.5, bounce=0.3)
    _rune(cv, *L(-8.2, -26.5), 0, V, 40, awake, s=2.6, glow_k=gk)
    _rune(cv, *L(-8.2, -21.5), 1, V, 40, awake, s=2.6, glow_k=gk)
    _cracks(cv, CRACKS_BODY, p['crack'], p['cglow'], V, 8.5, T=lambda q: L(*q))
    # ---- kemer: toka, plakalar, sarkan kese (pouch: gecikmeli salınım)
    belt = ik.union(cv.capsule(L(-9.8, -14.6), L(9.8, -14.6), 1.4, 1.4))
    cv.shape(belt, SD, z=9, sd=0.8, hi=0.35, details=[('col', cv.ellipse(L(-6 + k * 3.2, -14.6), 0.7, 0.9), S2.base) for k in range(5)])
    cv.shape(cv.blob([L(2.3, -16.2), L(4.7, -16.2), L(4.9, -13.0), L(2.1, -13.0)]), SL, z=14, sd=0.5, hi=0.3, ol=0.8)
    pk0 = L(-4.8, -13.6)
    pr = lambda x, y: yg.rot_about(L(x, y), pk0, p['pouch'])
    cv.shape(cv.blob([pr(-6.3, -13.6), pr(-3.3, -13.6), pr(-3.6, -9.6), pr(-4.8, -9.0) + (0.0,), pr(-6.0, -9.8)]), S2, z=12, sd=0.9, hi=0.3,
             details=[('ink', [pr(-6.0, -12.6), pr(-3.6, -12.6)], 0.9)])
    sword = p['sword']
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
    if awake > 0.5 and flare > 0:
        yk.glow_soft(cv, L(2.8, -27.6), 3.0, V['rune_glow'], z=18.3, alpha=0.35 * flare)
    # ---- boyun + baş (boyun dibinde döner: hr + aşağı/ileri; hd önden gider)
    cv.shape(cv.capsule(L(0.5, -31), L(1.2, -33.5), 3.2, 3.0), S, z=1, sd=1.0)
    nb = L(1.0, -32.0)
    hc = L(1.5, -38.5)
    if p['hfree'] < 0.5:
        yg.xf_push(cv, nb, p['hr'], p['hd'][0], p['hd'][1])
        _head(cv, p, V, hc, awake, flare)
        cv.pop()
    # ---- ön kol + kılıç (tw: burulma -> yakın omuz geriye; shy: omuz kalkar)
    sa = p['arm']
    shf = L(6.5 + tw * 2.6, -27.5 + p['shy'])
    e, h = fk_arm(shf, sa[0], sa[1], 7.0, 6.5)
    if sword >= 0.5 and p['swfree'] < 0.5:
        tip = _sword(cv, h, p['swang'], V, 27, awake, flare)
        sm = p['smear']
        if sm[2] > 0.02:
            _smear(cv, shf, math.hypot(tip[0] - shf[0], tip[1] - shf[1]), sm[0], sm[1], sm[2], V, 26.5)
    arm = cv.limb([shf, lerp2(shf, e, 0.5), e, h], [3.0, 3.1, 2.6, 2.3])
    cv.shape(arm, S2, z=26, sd=1.8, hi=0.45, details=[('ink', [lerp2(shf, e, 0.85), lerp2(e, h, 0.15)], 1.0)])
    fist = cv.ellipse(h, 2.5, 2.4)
    cv.shape(fist, S2, z=28, sd=1.0, hi=0.35, details=[('ink', [(h[0] - 1.6, h[1] - 0.4), (h[0] + 1.4, h[1] - 0.6)], 0.8)])
    pdet = _lichen(V, cv, [(shf[0] - 1.0, shf[1] - 1.2)], 21, 0.7)
    if p['dorm'] > 0.05:
        pdet += _dorm(V, cv, [(shf[0] - 0.5, shf[1] - 2.2, 2.6)], 23, p['dorm'])
    pad = cv.ellipse((shf[0] - 0.4, shf[1] - 0.6), 3.4, 2.2, -0.2)
    cv.shape(pad, SD, z=30, sd=1.0, hi=0.35, details=pdet)
    if V['ice']:
        yk.icicles(cv, [(shf[0] - 2.5, shf[1] + 1.2), (shf[0] + 0.5, shf[1] + 1.6), lerp2(e, h, 0.4)], ICE, 30.5, L=3.0, w=0.7, seed=6)
    dr = max(p['drip'], flare * 0.6)
    if dr > 0.02:   # omuzdan / börkten dökülen taş tozu
        rng = np.random.default_rng(3)
        for k in range(7):
            qq = (shf[0] + rng.uniform(-4, 2), shf[1] + rng.uniform(1, 4 + 8 * dr))
            r = rng.uniform(0.3, 0.65) * (0.6 + 0.4 * dr)
            cv.fill(cv.ellipse(qq, r, r), S.shadow, z=31)
        for k in range(4):
            qq = (hc[0] + rng.uniform(-6, 4), hc[1] - 6 + rng.uniform(-2, 6 * dr))
            cv.fill(cv.ellipse(qq, 0.35, 0.35), V['dust'], z=31)
    cv.pop()   # gövde
    if o_q is not None:
        cv._q = o_q
    if p['hfree'] >= 0.5:   # kopup düşen baş: figür yerelinde serbest
        yg.xf_push(cv, nb, p['hr'], p['hd'][0], p['hd'][1])
        _head(cv, p, V, hc, awake, flare)
        cv.pop()
    cv.pop()   # figür
    return {}


def along_(a, b, t, off=0.0):
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1.0
    return (a[0] + dx * t - dy / d * off, a[1] + dy * t + dx / d * off)


# ================================================================ animasyon
def _lagged(seq, k=1.0):
    """İkincil hareket: saç örgüsü ve kese gövdeyle birlikte değil, gecikmeli ve yerçekimine göre sallanır."""
    def proc(p, rt):
        dt = 0.07
        q1 = seq.q(max(0.0, rt - dt)) if not seq.loop else seq.q(rt - dt)
        tilt = p.get('pitch', 0.0) + p.get('roll', 0.0)
        tilt1 = q1.get('pitch', 0.0) + q1.get('roll', 0.0)
        dy = p.get('y', 0.0) - q1.get('y', 0.0)
        dxv = p.get('x', 0.0) - q1.get('x', 0.0)
        p = dict(p)
        p['brd'] = p.get('brd', 0.0) - 0.75 * tilt + k * (2.2 * (tilt1 - tilt) - 0.05 * dy + 0.06 * dxv)
        p['pouch'] = p.get('pouch', 0.0) - 0.8 * tilt + k * (2.6 * (tilt1 - tilt) + 0.07 * dxv)
        if seq.extra_proc:
            p = seq.extra_proc(p, rt)
        return p
    seq.extra_proc = seq.proc
    seq.proc = proc
    return seq


def P(*ds, **kw):
    """Poz birleştirme: sözlükler sırayla, sonra anahtar sözcükler (sonraki öncekini ezer)."""
    out = {}
    for d in ds:
        out.update(d)
    out.update(kw)
    return out


def S_(keys, **kw):
    kw.setdefault('rest', REST)
    return _lagged(Seq(keys, **kw))


# kılıç / kol anahtar pozları
ARM_REST = dict(arm=(0.35, 0.9), swang=1.0)
ARM_HIGH_BACK = dict(arm=(3.15, 0.35), swang=3.9)   # kılıç başın üstünden geriye kurulmuş
ARM_GUARD = dict(arm=(1.0, 1.65), swang=2.75)       # önkol göğüs önünde, kılıç yukarı-ileri dik


def _idle_proc(p, t):
    p = dict(p)
    p['pulse'] = p.get('pulse', 0.0) + math.sin(t * math.tau)
    return p


SEQS = {}

# ---- uyku (1 kare): heykel; kılıç kında, runalar sönük, baş hafif eğik, üstü toz tutmuş
DORMANT = dict(awake=0.0, sword=0.0, arm=(0.05, 0.4), swang=0.45, hr=0.08, hd=(0.3, 0.6), pitch=0.02, dorm=1.0, blink=0.6)
SEQS['dormant'] = S_([(0.0, DORMANT, 'l')], frames=[0.0], fps=1)

# ---- uyanış (6 kare, st 0,5): çatlaklardan ışık sızar -> sarsılır, tozunu silkeler -> runalar yanar, baş kalkar ->
# el kabzaya -> kılıcı kınından yukarı çeker (alev) -> dikleşip duruşa oturur
SEQS['wake'] = S_([
    (0.0, dict(DORMANT, crack=0.35, cglow=0.9, awake=0.08, dorm=0.9), 'l'),
    (0.2, dict(DORMANT, crack=0.6, cglow=1.0, awake=0.25, x=0.7, roll=-0.03, rp=-12.0, dorm=0.45, drip=1.0, chips=0.5,
               chip=(0.0, -30.0, -1.57, 3.0, 7), blink=0.0, eye=0.3), 'o'),
    (0.4, dict(DORMANT, crack=0.7, cglow=0.8, awake=0.75, x=-0.5, roll=0.025, rp=12.0, hr=-0.22, hd=(-0.5, -1.0), dorm=0.1, drip=0.7,
               pitch=-0.1, lean=-0.3, blink=0.0, eye=0.5, flare=0.5, dust=0.4, sq=-0.12, y=-0.8), 'o'),
    (0.6, dict(awake=0.9, sword=0.0, arm=(-0.35, 1.95), swang=0.4, crack=0.7, cglow=0.5, tw=-0.5, pitch=0.05, hr=0.04, hd=(0.4, 0.2),
               dorm=0.0, flare=0.4, drip=0.3, sq=0.15), 'io'),
    (0.8, dict(awake=1.0, sword=1.0, arm=(2.2, 0.35), swang=2.75, crack=0.7, cglow=0.35, tw=0.3, pitch=-0.08, hr=-0.1, hd=(-0.4, -0.6),
               flare=1.0, eye=0.5, sq=-0.12, y=-0.6, smear=(0.5, 2.75, 0.7)), 'i2'),
    (1.0, P(ARM_REST, awake=1.0, crack=0.3, cglow=0.15, flare=0.2, sq=0.08), 'o'),
], frames=[(0.0, 0.0), (0.2, 0.14), (0.4, 0.3), (0.6, 0.5), (0.8, 0.68), (1.0, 0.86)], seg=[('wake', 6)], fps=12)

# ---- bekleme (8 kare): taş "nefesi" = runa nabzı, gıcırdayan küçük ağırlık kaymaları, ortada baş tiki (sert, kesik)
IDLE_A = P(ARM_REST, crack=0.25, cglow=0.0)
SEQS['idle'] = S_([
    (0.0, dict(IDLE_A, hr=0.0, x=0.0, swang=1.0), 'io'),
    (0.25, dict(IDLE_A, x=0.35, pitch=0.015, arm=(0.38, 0.92), swang=1.04, hr=0.02), 'io'),
    (0.45, dict(IDLE_A, x=0.2, pitch=0.01, hr=0.02), 'io'),
    (0.52, dict(IDLE_A, x=0.25, pitch=0.0, hr=-0.14, hd=(-0.5, -0.4), drip=0.5, eye=0.15), 'i'),
    (0.7, dict(IDLE_A, x=0.1, hr=-0.12, hd=(-0.4, -0.3), drip=0.25, eye=0.1), 'l'),
    (0.78, dict(IDLE_A, x=-0.15, hr=0.03, hd=(0.1, 0.1), pitch=-0.01, sq=0.04), 'i'),
    (1.0, dict(IDLE_A, hr=0.0, x=0.0, swang=1.0), 'io'),
], n=8, fps=7, loop=True, proc=_idle_proc)

# ---- siper (3 kare, up 0,5): önkol ve kılıç yüzün önüne kalkar, gövde geri yaslanır, baş siperin arkasına gömülür
SEQS['guard'] = S_([
    (0.0, dict(IDLE_A, arm=(0.75, 1.35), swang=2.2, pitch=-0.03, hr=0.06, sq=0.06), 'l'),
    (0.4, P(IDLE_A, ARM_GUARD, pitch=-0.07, lean=-0.3, hr=0.14, hd=(-0.6, 0.8), tw=0.4, sq=0.12, x=-0.6, eye=0.3, flare=0.2), 'o'),
    (1.0, P(IDLE_A, ARM_GUARD, arm=(1.02, 1.62), pitch=-0.06, lean=-0.25, hr=0.12, hd=(-0.5, 0.7), tw=0.4, sq=0.08, x=-0.5, eye=0.3), 'io'),
], frames=[(0.0, 0.0), (0.4, 0.2), (1.0, 0.55)], fps=10)

# ---- seğirtme / sekiş (vy; 5 kare): kaideyle itiş (esneme, öne atılan gövde) -> havada toplanma -> tepe ->
# düşüş (gövde geride, kaide öne uzanır) -> iniş (ağır, kılıç dengede)
SEQS['hop'] = S_([
    (0.0, dict(IDLE_A, sq=-0.35, y=-1.0, pitch=0.12, lean=0.3, arm=(0.2, 0.8), swang=0.95, hr=0.1, hd=(0.6, 0.3), drip=0.3), 'l'),
    (0.3, dict(IDLE_A, sq=0.12, y=-3.0, pitch=0.06, arm=(0.55, 1.0), swang=1.35, hr=0.05, roll=0.05, rc=1.0), 'o'),
    (0.5, dict(IDLE_A, sq=0.0, y=-3.4, pitch=0.0, arm=(0.6, 1.0), swang=1.45, hr=0.0, roll=0.02, rc=1.0), 'io'),
    (0.75, dict(IDLE_A, sq=-0.25, y=-2.2, pitch=-0.08, lean=-0.2, arm=(0.75, 0.9), swang=1.55, hr=-0.06, hd=(-0.3, -0.4), roll=-0.04, rc=1.0), 'i2'),
    (1.0, dict(IDLE_A, sq=-0.15, y=-0.6, pitch=-0.05, arm=(0.6, 0.9), swang=1.4, hr=0.04, roll=-0.02, rc=1.0), 'o'),
], frames=[(0.0, 0.0), (0.3, 0.18), (0.5, 0.4), (0.75, 0.6), (1.0, 0.85)], seg=[('air', 5)], fps=10)

# ---- taş kılıç savuruşu "!" (hazırlık 4 + vuruş 2 + toparlanma 3)
CUT_DEEP = P(IDLE_A, ARM_HIGH_BACK, pitch=-0.16, lean=-0.55, tw=-0.8, hr=0.12, hd=(1.0, 0.8), sq=-0.08, y=-0.4, flare=0.9, eye=0.35, shy=-1.2)
SEQS['cut'] = S_([
    (0.0, dict(IDLE_A, arm=(0.9, 1.0), swang=1.8, pitch=0.04, tw=-0.2, sq=0.1, hr=0.06, flare=0.2), 'o'),
    (0.14, dict(IDLE_A, arm=(2.2, 0.6), swang=3.0, pitch=-0.08, lean=-0.3, tw=-0.55, hr=0.1, hd=(0.6, 0.4), flare=0.6, shy=-0.8), 'o'),
    (0.3, dict(CUT_DEEP), 'o'),
    (0.42, dict(CUT_DEEP, arm=(2.6, 0.2), swang=2.6, pitch=0.02, lean=0.1, tw=-0.2, hr=0.1, hd=(1.4, 0.8), sq=-0.18, y=-0.6,
                smear=(3.9, 2.6, 0.5)), 'i'),
    # vuruş: temas — kılıç önde yatay, gövde öne yüklenir; ardından yere dek iner (kıymık)
    (0.5, dict(IDLE_A, arm=(1.55, 0.1), swang=1.5, pitch=0.2, lean=0.5, tw=0.6, hr=0.06, hd=(1.6, 1.0), sq=0.25, x=2.0, flare=0.7, eye=0.3,
               smear=(3.6, 1.5, 1.0)), 'i'),
    (0.62, dict(IDLE_A, arm=(1.15, 0.1), swang=0.8, pitch=0.24, lean=0.6, tw=0.7, hr=0.14, hd=(1.4, 1.4), sq=0.35, x=2.4, flare=0.3,
                smear=(2.4, 0.8, 0.55), chips=1.0, chip=(31.0, -1.0, -1.9, 1.5, 4), dust=0.35), 'o'),
    # toparlanma: ağır, gıcırtılı geri çekiliş
    (0.74, dict(IDLE_A, arm=(1.0, 0.2), swang=0.6, pitch=0.24, lean=0.5, tw=0.6, hr=0.12, hd=(1.2, 1.2), sq=0.28, x=2.2, chips=0.4,
                chip=(29.0, -1.0, -1.9, 1.5, 4), drip=0.4), 'o'),
    (0.87, dict(IDLE_A, arm=(0.6, 0.6), swang=0.8, pitch=0.1, lean=0.2, tw=0.3, hr=0.06, hd=(0.5, 0.5), sq=0.12, x=1.0), 'io'),
    (1.0, dict(IDLE_A, x=0.0), 'o'),
], frames=[(0.0, 0.0), (0.14, 0.22), (0.3, 0.45), (0.42, 0.0),
           (0.5, 0.0), (0.62, 0.4),
           (0.74, 0.0), (0.87, 0.35), (1.0, 0.72)],
    seg=[('windup', 4), ('strike', 2), ('recover', 3)], lead={'windup': 0.05}, fps=10)

# ---- zırhlı hamle "!!" (intikam kesiği; hazırlık 3 + atılan kesik 2 + toparlanma 2): alçak geniş duruş, kabaran gövde,
# çatlaklardan ışık, kılıç kalçadan geriye yatay çekilmiş -> öne atılan uzun yatay kesik
REV_DEEP = dict(IDLE_A, arm=(-0.9, 1.1), swang=-1.25, pitch=0.12, lean=0.35, tw=-1.0, swell=1.08, sq=0.32, y=0.4, hr=0.2, hd=(1.6, 1.6),
                flare=1.0, eye=1.0, crack=1.0, cglow=1.0, x=-1.2, drip=0.8)
SEQS['rev'] = S_([
    (0.0, dict(IDLE_A, arm=(-0.3, 1.0), swang=-0.3, pitch=0.06, tw=-0.5, swell=1.04, sq=0.18, hr=0.12, hd=(0.8, 0.8), flare=0.6, eye=0.6,
               crack=0.85, cglow=0.7), 'o'),
    (0.25, dict(REV_DEEP), 'o'),
    (0.4, dict(REV_DEEP, arm=(0.2, 1.0), swang=0.6, pitch=0.2, tw=-0.2, x=1.5, sq=0.1, smear=(-1.25, 0.6, 0.5)), 'i'),
    (0.5, dict(IDLE_A, arm=(1.6, -0.05), swang=1.62, pitch=0.3, lean=0.6, tw=0.8, swell=1.05, sq=0.2, x=5.0, hr=0.1, hd=(2.0, 1.4),
               flare=0.9, eye=0.9, crack=1.0, cglow=0.7, smear=(-0.6, 1.62, 1.0), dust=0.4), 'i'),
    (0.65, dict(IDLE_A, arm=(2.3, 0.05), swang=2.5, pitch=0.18, lean=0.3, tw=1.0, swell=1.03, sq=0.05, x=5.5, hr=0.0, hd=(1.6, 0.6),
                flare=0.5, eye=0.6, crack=1.0, cglow=0.4, smear=(1.0, 2.5, 0.6)), 'o'),
    (0.82, dict(IDLE_A, arm=(1.4, 0.6), swang=1.9, pitch=0.08, tw=0.5, x=3.0, sq=0.12, crack=0.9, cglow=0.15, drip=0.4), 'o'),
    (1.0, dict(IDLE_A, x=0.0, crack=0.8), 'o'),
], frames=[(0.0, 0.0), (0.25, 0.25), (0.4, 0.0),
           (0.5, 0.0), (0.65, 0.4),
           (0.82, 0.0), (1.0, 0.55)],
    seg=[('windup', 3), ('strike', 2), ('recover', 2)], lead={'windup': 0.05}, fps=10)

# ---- sıçrayıp çakma "!!" (hazırlık 3 + hava 3 + çakma 2 + toparlanma 2)
LEAP_DEEP = dict(IDLE_A, arm=(2.8, 0.5), swang=3.65, pitch=0.1, lean=0.2, swell=1.08, sq=0.42, y=0.6, hr=0.18, hd=(1.4, 1.4), flare=1.0,
                 eye=1.0, crack=1.0, cglow=1.0, shy=-1.0, drip=0.9, tw=-0.3)
SEQS['leap'] = S_([
    (0.0, dict(IDLE_A, arm=(1.6, 0.8), swang=2.4, sq=0.2, pitch=0.06, flare=0.5, eye=0.5, crack=0.85, cglow=0.6, hr=0.08), 'o'),
    (0.1, dict(LEAP_DEEP), 'o'),
    (0.16, dict(LEAP_DEEP, sq=-0.35, y=-1.2, pitch=-0.05, lean=-0.2, hr=0.0, hd=(0.6, -0.4), dust=0.6), 'i'),
    # hava (vy): esneyerek yükseliş, tepede kılıç geride kurulu (gövde yay), düşüşte kılıç başın üstünden iner
    (0.3, dict(IDLE_A, arm=(2.85, 0.45), swang=3.55, sq=-0.3, y=-2.5, pitch=-0.06, lean=-0.3, hr=-0.04, flare=0.9, eye=1.0, crack=1.0, cglow=0.8,
               roll=0.0, rc=1.0), 'o'),
    (0.42, P(IDLE_A, ARM_HIGH_BACK, sq=0.05, y=-3.5, pitch=-0.18, lean=-0.6, tw=-0.6, hr=0.1, hd=(1.0, 0.6), flare=1.0, eye=1.0,
                crack=1.0, cglow=0.9, shy=-1.2, roll=-0.06, rc=1.0), 'io'),
    (0.54, dict(IDLE_A, arm=(2.0, 0.1), swang=2.1, sq=-0.25, y=-2.0, pitch=0.12, lean=0.3, tw=0.3, hr=0.12, hd=(1.4, 1.2), flare=1.0,
                eye=1.0, crack=1.0, cglow=0.8, roll=0.08, rc=1.0, smear=(3.9, 2.1, 0.8)), 'i'),
    # çakma: temas — kılıç önde yere gömülü, gövde öne katlanmış, halka + kıymık + toz
    (0.64, dict(IDLE_A, arm=(1.15, 0.15), swang=0.42, sq=0.5, y=0.5, pitch=0.34, lean=0.6, tw=0.6, hr=0.16, hd=(1.6, 1.8), flare=1.0,
                eye=0.8, crack=1.0, cglow=0.8, x=1.5, smear=(2.4, 0.42, 0.8), ring=0.25, ringx=20.0, chips=1.0,
                chip=(25.0, -1.0, -1.57, 2.4, 9), dust=0.9), 'i'),
    (0.76, dict(IDLE_A, arm=(1.15, 0.15), swang=0.42, sq=0.38, y=0.3, pitch=0.3, lean=0.55, tw=0.6, hr=0.14, hd=(1.4, 1.6), flare=0.4,
                eye=0.5, crack=1.0, cglow=0.5, x=1.5, ring=0.8, ringx=20.0, chips=1.6, chip=(25.0, -1.0, -1.57, 2.6, 9), dust=1.0), 'o'),
    # toparlanma: kılıcı yerden söker, dikleşir
    (0.88, dict(IDLE_A, arm=(0.9, 0.4), swang=0.75, sq=0.2, pitch=0.16, lean=0.3, tw=0.3, hr=0.08, hd=(0.6, 0.8), x=0.9, crack=0.9,
                cglow=0.2, chips=0.5, chip=(25.0, -1.0, -1.57, 1.4, 12), drip=0.6), 'o'),
    (1.0, dict(IDLE_A, x=0.0, crack=0.8), 'o'),
], frames=[(0.0, 0.0), (0.1, 0.3), (0.16, 0.0),
           (0.3, 0.0), (0.42, 0.35), (0.54, 0.62),
           (0.64, 0.0), (0.76, 0.45),
           (0.88, 0.0), (1.0, 0.5)],
    seg=[('windup', 3), ('air', 3), ('strike', 2), ('recover', 2)], lead={'windup': 0.05}, fps=10)

# ---- dönüş (3 kare, ~0,2 sn): taş blok olduğu yerde sekerek döner — kenardan görünüş (dar), baş geride kalır
SEQS['turn'] = S_([
    (0.0, dict(IDLE_A, sx=0.55, y=-1.2, hr=-0.15, hd=(-2.5, -0.5), arm=(0.2, 0.7), swang=0.6, sq=-0.1), 'l'),
    (0.5, dict(IDLE_A, sx=0.85, y=-0.6, hr=-0.05, hd=(-0.8, 0.0), arm=(0.3, 0.8), swang=0.85), 'o'),
    (1.0, dict(IDLE_A, sq=0.12, dust=0.25), 'o'),
], frames=[(0.0, 0.0), (0.5, 0.35), (1.0, 0.7)], fps=12)

# ---- hafif sarsılma (3 kare, 0,22): darbe yerinden kıymık, gövde sertçe geri, baş geri savrulur, çatlak parlar
SEQS['hurt'] = S_([
    (0.0, dict(IDLE_A, pitch=-0.09, lean=-0.3, hr=-0.16, hd=(-0.8, -0.5), x=-1.2, crack=0.85, cglow=0.4, blink=0.8, chips=0.8,
               chip=(8.0, -24.0, -0.4, 1.6, 21), arm=(0.15, 1.2), swang=1.3, roll=-0.03, rp=-12.0), 'l'),
    (0.5, dict(IDLE_A, pitch=-0.04, hr=-0.06, x=-0.8, crack=0.8, cglow=0.15, blink=0.3, chips=1.4, chip=(8.0, -24.0, -0.4, 1.6, 21),
               arm=(0.25, 1.0), swang=1.15, roll=-0.01, rp=-12.0), 'o'),
    (1.0, dict(IDLE_A, x=-0.3, sq=0.05), 'o'),
], frames=[(0.0, 0.0), (0.5, 0.35), (1.0, 0.7)], fps=12)

# ---- ağır sendeleme (4 kare, 0,45): kaidenin arka kenarına devrilir, ön kenar kalkar, sonra "GÜM" diye oturur
SEQS['hurt_big'] = S_([
    (0.0, dict(IDLE_A, roll=-0.16, rp=-12.0, pitch=-0.12, lean=-0.4, hr=-0.25, hd=(-1.2, -0.8), crack=1.0, cglow=0.5, blink=1.0,
               chips=1.0, chip=(8.0, -26.0, -0.5, 1.8, 25), arm=(0.0, 1.5), swang=1.9, drip=0.8), 'o'),
    (0.35, dict(IDLE_A, roll=-0.1, rp=-12.0, pitch=-0.06, lean=-0.2, hr=-0.12, crack=1.0, cglow=0.2, blink=0.6, chips=1.6,
                chip=(8.0, -26.0, -0.5, 1.8, 25), arm=(0.1, 1.3), swang=1.6, drip=0.6), 'io'),
    (0.7, dict(IDLE_A, roll=0.0, rp=-12.0, pitch=0.06, lean=0.2, hr=0.08, hd=(0.4, 0.6), sq=0.3, crack=0.95, blink=0.2, dust=0.8,
               arm=(0.5, 0.8), swang=0.8), 'i2'),
    (1.0, dict(IDLE_A, sq=0.05, crack=0.9, dust=0.3), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.25), (0.7, 0.55), (1.0, 0.8)], fps=10)


# ---- duruş kırık / sersem (6 kare döngü): kaide kenarlarında sallanır, baş sarkık, kılıç ucu yerde sürünür,
# runalar cızırdayarak söner / yanar, tozlar dökülür
def _stun(t):
    s = math.sin(t * math.tau)
    c = math.cos(t * math.tau)
    return dict(IDLE_A, roll=0.05 * s, rp=-12.0 if s < 0 else 12.0, pitch=0.09 + 0.03 * c, lean=0.25, hr=0.28 + 0.06 * s,
                hd=(1.0 + 0.4 * s, 2.2), arm=(0.2, 0.45), swang=0.75 + 0.1 * s, awake=0.55 + 0.35 * abs(math.sin(t * math.tau * 3)),
                crack=1.0, cglow=0.3 + 0.3 * abs(c), blink=0.5, drip=0.5 + 0.3 * abs(s), x=0.6 * s)


SEQS['stun'] = S_([(i / 12, _stun(i / 12), 'l') for i in range(13)], n=6, fps=6, loop=True)

# ---- havaya savrulma (vy; 4 kare): taş blok geriye devrilerek döner, kıymık saçar; düşüşte kaide aşağı döner
SEQS['launch'] = S_([
    (0.0, dict(IDLE_A, roll=-0.3, rc=1.0, y=-2.0, pitch=-0.1, hr=-0.2, hd=(-1.0, -0.6), arm=(0.0, 1.6), swang=2.0, crack=1.0, cglow=0.4,
               blink=1.0, chips=1.2, chip=(0.0, -20.0, -2.4, 2.0, 33), sq=-0.15), 'o'),
    (0.4, dict(IDLE_A, roll=-0.55, rc=1.0, y=-3.0, pitch=-0.06, hr=-0.1, arm=(-0.2, 1.8), swang=2.4, crack=1.0, cglow=0.2, blink=0.8,
               drip=0.8), 'io'),
    (0.7, dict(IDLE_A, roll=-0.3, rc=1.0, y=-2.4, pitch=0.04, hr=0.05, arm=(0.4, 1.2), swang=1.6, crack=1.0, blink=0.5), 'io'),
    (1.0, dict(IDLE_A, roll=-0.08, rc=1.0, y=-1.0, pitch=0.05, hr=0.06, arm=(0.5, 0.9), swang=1.2, crack=1.0, blink=0.2, sq=-0.1), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.25), (0.65, 0.55), (1.0, 0.82)], seg=[('air', 4)], fps=10)

# ---- ölüm (8 kare, 0,9): çatlaklar parlayıp yayılır -> runalar söner, kılıç elden düşer -> baş kopar ->
# gövde öne çöker ve kaideye gömülerek ufalanır -> moloz yığını, yanında baş ve kırık kılıç
DEAD_SW = (19.0, -1.6, 1.62)
SEQS['death'] = S_([
    (0.0, dict(IDLE_A, crack=1.0, cglow=1.0, flare=1.0, eye=1.0, pitch=-0.1, lean=-0.3, hr=-0.2, hd=(-0.8, -0.6), arm=(0.1, 1.4),
               swang=1.8, chips=0.9, chip=(4.0, -28.0, -1.2, 3.0, 41), x=-1.0), 'o'),
    (0.14, dict(IDLE_A, crack=1.0, cglow=0.6, awake=0.45, flare=0.0, pitch=0.0, hr=0.1, hd=(0.4, 0.6), arm=(0.0, 0.3), swang=0.3,
                swfree=1.0, swp=(14.0, -11.0, 1.2), chips=1.4, chip=(4.0, -28.0, -1.2, 3.0, 41), drip=1.0, x=-0.6), 'io'),
    (0.3, dict(IDLE_A, crack=1.0, cglow=0.3, awake=0.2, pitch=0.08, lean=0.2, hfree=1.0, hr=0.35, hd=(3.0, -2.5), arm=(-0.1, 0.2), swang=0.3,
               swfree=1.0, swp=DEAD_SW, chips=1.0, chip=(3.0, -33.0, -1.4, 2.4, 43), drip=1.0, dust=0.3), 'o'),
    (0.44, dict(IDLE_A, crack=1.0, cglow=0.1, awake=0.0, pitch=0.2, lean=0.4, sink=4.0, hfree=1.0, hr=1.1, hd=(9.0, 12.0), arm=(-0.1, 0.1),
                swang=0.3, swfree=1.0, swp=DEAD_SW, drip=1.0, rubble=0.15, dust=0.5), 'i2'),
    (0.58, dict(IDLE_A, crack=1.0, awake=0.0, pitch=0.24, lean=0.4, sink=10.0, sq=0.1, hfree=1.0, hr=1.6, hd=(13.0, 25.5), arm=(-0.2, 0.1),
                swang=0.3, swfree=1.0, swp=DEAD_SW, drip=1.0, rubble=0.45, dust=0.9, chips=1.0, chip=(12.0, -2.0, -1.57, 2.8, 45)), 'i'),
    (0.72, dict(IDLE_A, crack=1.0, awake=0.0, pitch=0.2, lean=0.3, sink=17.0, sq=0.15, hfree=1.0, hr=1.75, hd=(15.0, 26.5), arm=(-0.2, 0.1),
                swang=0.3, swfree=1.0, swp=DEAD_SW, drip=0.6, rubble=0.75, dust=1.0), 'o'),
    (0.86, dict(IDLE_A, crack=1.0, awake=0.0, pitch=0.16, lean=0.2, sink=23.0, sq=0.15, hfree=1.0, hr=1.78, hd=(15.6, 26.8), arm=(-0.2, 0.1),
                swang=0.3, swfree=1.0, swp=DEAD_SW, drip=0.2, rubble=0.95, dust=0.6), 'o'),
    (1.0, dict(IDLE_A, crack=1.0, awake=0.0, pitch=0.12, lean=0.2, sink=26.0, sq=0.15, hfree=1.0, hr=1.78, hd=(15.8, 26.8), arm=(-0.2, 0.1),
               swang=0.3, swfree=1.0, swp=DEAD_SW, rubble=1.0, dust=0.25), 'o'),
], frames=[(0.0, 0.0), (0.14, 0.1), (0.3, 0.22), (0.44, 0.34), (0.58, 0.46), (0.72, 0.58), (0.86, 0.72), (1.0, 0.88)], fps=10)

# ---- kükreme (seçkin; 5 kare, 0,8): kılıcı göğe kaldırır, baş geriye, runalar ve çatlaklar alev alır, toz silkelenir
SEQS['roar'] = S_([
    (0.0, dict(IDLE_A), 'io'),
    (0.25, dict(IDLE_A, arm=(1.6, 0.8), swang=2.4, pitch=0.06, sq=0.2, hr=0.1, flare=0.4, crack=0.85, cglow=0.4), 'o'),
    (0.5, dict(IDLE_A, arm=(2.85, 0.45), swang=3.55, pitch=-0.12, lean=-0.4, sq=-0.15, hr=-0.3, hd=(-0.6, -1.2), flare=1.0, eye=1.0,
               crack=1.0, cglow=1.0, swell=1.06, drip=1.0, shy=-1.2, dust=0.6), 'o'),
    (0.75, dict(IDLE_A, arm=(2.87, 0.45), swang=3.57, pitch=-0.11, lean=-0.4, sq=-0.12, hr=-0.28, hd=(-0.6, -1.1), flare=0.9, eye=1.0,
                crack=1.0, cglow=0.9, swell=1.05, drip=0.7, shy=-1.2, dust=0.3), 'io'),
    (1.0, dict(IDLE_A, crack=0.85), 'o'),
], n=5, fps=8)

DURUM = {
    # ---- tepkiler
    '_hurt': {'a': 'hurt', 'u': 'up', 'd': 0.22},
    '_hurt_big': {'a': 'hurt_big', 'u': 'up', 'd': 0.45},
    '_break': {'a': 'stun', 'u': 'loop'},
    '_launch': {'a': 'launch', 'u': 'vy'},
    '_death': {'a': 'death', 'u': 'up', 'd': 0.9},
    '_turn': {'a': 'turn', 'u': 'up', 'd': 0.2},
    '_roar': {'a': 'roar', 'u': 'up', 'd': 0.8},
    '_guard': {'a': 'guard', 'u': 'up', 'd': 0.5},
    # ---- uyku / uyanış / dolaşma
    'dormant': {'a': 'dormant', 'u': 'loop'},
    'dormant>recover': {'a': 'wake', 'u': 'st'},
    'idle': {'a': 'idle', 'u': 'loop'},
    'chase': {'a': 'idle', 'u': 'loop'},
    'hop': {'a': 'hop', 'u': 'vy'},
    # ---- taş kılıç "!" / zırhlı kesik "!!" (intikam ya da baskı altında zırhlanan kesik)
    'windup/cut': {'a': 'cut', 's': 'windup', 'u': 'st'},
    'windup/cut!!': {'a': 'rev', 's': 'windup', 'u': 'st'},
    'strike/cut': {'a': 'cut', 's': 'strike', 'u': 'st'},
    'recover/cut': {'a': 'cut', 's': 'recover', 'u': 'st'},
    'rev/cut': {'a': 'rev', 's': 'strike', 'u': 'st'},
    'rev': {'a': 'rev', 's': 'strike', 'u': 'st'},
    'rev>recover': {'a': 'rev', 's': 'recover', 'u': 'st'},
    # ---- sıçrayıp çakma "!!"
    'windup/leap!!': {'a': 'leap', 's': 'windup', 'u': 'st'},
    'windup/leap': {'a': 'leap', 's': 'windup', 'u': 'st'},
    'leap/leap': {'a': 'leap', 's': 'air', 'u': 'vy'},
    'leap': {'a': 'leap', 's': 'air', 'u': 'vy'},
    'strike/leap': {'a': 'leap', 's': 'strike', 'u': 'st'},
    'recover/leap': {'a': 'leap', 's': 'recover', 'u': 'st'},
    # ---- geri dönüşler
    'windup': {'a': 'cut', 's': 'windup', 'u': 'st'},
    'windup!!': {'a': 'rev', 's': 'windup', 'u': 'st'},
    'strike': {'a': 'cut', 's': 'strike', 'u': 'st'},
    'recover': {'a': 'cut', 's': 'recover', 'u': 'st'},
}

SHADE = dict(outer=0.55, rim=0.7, rim_col=(0.7, 0.8, 1.0), rim_dir=(0.6, -0.8), rim_w=1.4, form=(5.0, (0.76, 0.74, 0.88)))


def render_frame(anim, i, var='balbal', ss=3):
    V = VARIANTS[var]
    p = SEQS[anim].pose(i)
    cv = yk.occlude_glow(ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss))
    info = draw(cv, p, V)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
