"""Kurgan Bekçisi (kimlik bekci) — stil v2 "mürekkep-cel" (inkkit.py). v1: creatures2.draw_bekci / BEKCI_ANIMS.

Kurganında dinlenemeyen kadim Göktürk savaşçısı: kurumuş kafatası yüz (oyuk göz çukurunda soğuk Kut ışığı), sivri
dilimli tunç miğfer + burun siperi + zincir ensel + kızıl at kılı sorgucu, tunç lamel zırh ve omuzluk, lamel etek
parçaları, kızıl keçe kaftan, sargılı baldır ve keçe çizme, tunç baldır siperi. Ön kolda deri kaplı büyük yuvarlak
kalkan (tunç kasnak, çivili kenar, sivri göbek, ışıyan Göktürk runa halkası); arka elde (kemik parmaklar) dilimli
tunç topuz (şestopor).

Animasyon adları, kare sayıları, fps/döngü ve çapalar ('hand' = kalkan eli, 'head' = baş merkezi) v1 ile aynı;
pozlar daha okunur telegraf için yeniden kurgulandı (hazırlıkta topuz başın üstünden arkaya, gözler alevlenir;
vuruşta adım + kuru fırça hız çizgisi; kalkan darbesinde omuz arkasında). Ayaklar yere çözülür (ground).
Çarpışma (26 x 58) ve ayak noktası değişmez. Yeniden boyamalar (world.json "tint") için orta değerli, az doygun taban.
"""
import math

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_leg, fk_arm, lerp2, chain
from bengu_ink import along, _perp

TEX = 4.0
CELL = (384, 416)        # dünya 96 x 104
FEET = (176, 392)        # dünya (44, 98)

L_TH, L_SH = 12.0, 12.0
L_UP, L_FO = 10.0, 9.0
TORSO = 17.0

# ------------------------------------------------------------ malzemeler (orta değer, az doygun: tint ile iyi boyanır)
BRONZE = Ink('#b18c56', '#5e4232', '#f3dca0', '#2e2020', kind='metal', name='eski tunç')
BRONZE_B = BRONZE.darker(0.7)
VERD = (0.40, 0.56, 0.50)                     # tunç pası (yeşil)
FELT = Ink('#8a3a3c', '#45192c', '#b45a54', '#28101e', name='kızıl keçe kaftan')
FELT_B = FELT.darker(0.72)
WRAP = Ink('#6c6466', '#33303c', '#968c88', name='baldır sargısı')
WRAP_B = WRAP.darker(0.72)
BOOT = Ink('#4e3c38', '#241a1e', '#76605a', name='keçe çizme')
BOOT_B = BOOT.darker(0.75)
BONE = Ink('#ddd0b0', '#857762', '#fffae6', '#4a3e36', name='kemik')
BONE_B = BONE.darker(0.75)
SKINDRY = Ink('#7a5e4a', '#3c2a26', '#a08068', name='kurumuş deri')
MAIL = Ink('#6e717e', '#30323e', '#b0b6c6', '#1c1d26', kind='metal', name='zincir örgü')
HIDE = Ink('#7c5c42', '#3e2a24', '#a8825e', '#24181a', name='kalkan derisi')
WOOD = Ink('#6a4a32', '#2e1e1a', '#9a7250', name='kalkan tahtası')
HAFT = Ink('#5e4030', '#2a1a16', '#8e6a4c', name='topuz sapı')
PLUME = Ink('#a83434', '#521a2a', '#e06050', name='at kılı sorguç')
LEATHER = Ink('#5a3a2a', '#28181a', '#86604a', name='kemer derisi')
EYE = (0.62, 0.96, 1.0)
EYE_GLOW = (0.30, 0.80, 1.0)
RUNE = (1.0, 0.82, 0.42)
RUNE_GLOW = (1.0, 0.55, 0.12)


# ------------------------------------------------------------ yardımcılar
def ground(p):
    """Kalça yüksekliği: yere en derin basan ayak y=0 olur (ayaklar zemine oturur); 'air' yukarı kaldırır."""
    def depth(a):
        return L_TH * math.cos(a[0]) + L_SH * math.cos(a[0] - a[1])
    return -max(depth(p['lb']), depth(p['lf'])) - p.get('air', 0.0)


def _rune_glyph(k):
    """Göktürk harflerine benzeyen kısa çizgi grupları (yerel -1..1 kutusunda)."""
    G = [
        [[(-0.6, 1.0), (0.0, -1.0), (0.6, 1.0)], [(-0.3, 0.2), (0.3, 0.2)]],          # ok ucu
        [[(0.0, -1.0), (0.0, 1.0)], [(0.0, -0.2), (0.7, -0.9)], [(0.0, 0.3), (-0.7, -0.4)]],   # dal
        [[(-0.7, -1.0), (0.7, 1.0)], [(0.7, -1.0), (-0.7, 1.0)]],                       # çarpı
        [[(-0.6, -1.0), (0.4, 0.0), (-0.6, 1.0)], [(0.4, 0.0), (0.8, 0.0)]],            # kanca
        [[(0.0, -1.0), (0.0, 1.0)], [(-0.7, -0.6), (0.0, 0.0), (0.7, -0.6)]],           # Y
        [[(-0.6, 1.0), (-0.6, -1.0), (0.6, -0.2)], [(0.6, -0.2), (0.6, 1.0)]],          # kapı
    ]
    return G[k % len(G)]


def _shield(cv, c, R, face, rot, z, near=True, spin=0.0):
    """Büyük yuvarlak kalkan. c merkez, R yarıçap, face: dış yüzün görünür oranı (0 = tam yan, 1 = tam karşı).
    Dış yüz sağa (düşmana) bakar; kalınlık (tahta kenar) sol yanda görünür."""
    rx = max(0.9, R * face)
    ry = R
    ca, sa = math.cos(rot), math.sin(rot)

    def E(u, v):   # kalkan yüzeyi: u, v in [-1, 1]
        x, y = u * rx, v * ry
        return (c[0] + x * ca - y * sa, c[1] + x * sa + y * ca)
    th = 1.5 + 0.8 * (1 - face)
    back = cv.ellipse((c[0] - th * ca, c[1] - th * sa), rx, ry, rot)
    cv.shape(back, WOOD if near else WOOD.darker(0.75), z=z - 0.2, sd=1.2, hi=0.0,
             details=[('ink', [E(-0.9, -0.5), E(-1.0, 0.0), E(-0.9, 0.5)], 1.0)])
    face_p = cv.ellipse(c, rx, ry, rot)
    det = []
    # deri yüzey: kesik izleri ve dikiş
    det.append(('ink', [E(-0.25, -0.62), E(0.05, -0.38), E(0.2, -0.26)], 1.1, (0.2, 0.6)))
    det.append(('ink', [E(0.35, 0.42), E(0.5, 0.62)], 1.0, (0.2, 0.6)))
    det.append(('shade', cv.wedge([E(-0.2, 0.55), E(0.15, 0.72), E(0.5, 0.6)], 0.6, 1.0)))
    cv.shape(face_p, HIDE if near else HIDE.darker(0.75), z=z, sd=3.2, hi=0.4, details=det, bounce=0.3, cast=0.8)
    # tunç kasnak (halka) + perçinler
    ring = ik.diff(face_p, cv.ellipse(c, rx * 0.86, ry * 0.86, rot))
    rdet = []
    for k in range(10):
        a = k / 10 * math.tau + 0.2
        q = E(math.cos(a) * 0.93, math.sin(a) * 0.93)
        rdet.append(('col', cv.ellipse(q, 0.55 * max(0.4, face), 0.55, rot), BRONZE.hi if math.cos(a) * -0.7 + math.sin(a) * -0.7 > 0 else BRONZE.deep))
    cv.shape(ring, BRONZE if near else BRONZE_B, z=z + 0.1, sd=1.4, hi=0.5, details=rdet, ol=0.8)
    # runa halkası: koyu boyalı bant, içinde ışıyan Göktürk harfleri
    band = ik.diff(cv.ellipse(c, rx * 0.72, ry * 0.72, rot), cv.ellipse(c, rx * 0.47, ry * 0.47, rot))
    cv.shape(band, Ink('#3a2a2a', '#1e1418', '#5a4440'), z=z + 0.15, sd=0.8, ol=0.5, grad=0.0, soft=0.0)
    for k in range(6):
        a = k / 6 * math.tau - math.pi / 2 + spin
        cu, cv_ = math.cos(a) * 0.595, math.sin(a) * 0.595
        if face < 0.35 and cu < -0.3:
            continue
        s = 0.085
        for st in _rune_glyph(k):
            pts = [E(cu + (x * math.cos(a + math.pi / 2) - y * math.sin(a + math.pi / 2)) * s,
                     cv_ + (x * math.sin(a + math.pi / 2) + y * math.cos(a + math.pi / 2)) * s) for x, y in st]
            cv.stroke(pts, 1.5, z=z + 0.2, col=RUNE, taper=(0.15, 0.15), glow=RUNE_GLOW)
    # göbek (umbo) + sivri uç
    umbo = cv.ellipse(c, rx * 0.3, ry * 0.3, rot)
    cv.shape(umbo, BRONZE if near else BRONZE_B, z=z + 0.3, sd=1.8, hi=0.6, cast=0.6)
    sp_len = 2.6 * (1 - face * 0.55) + 0.6
    tip = (c[0] + ca * sp_len, c[1] + sa * sp_len)
    cv.shape(cv.blob([(c[0] - sa * 1.0, c[1] + ca * 1.0), (tip[0], tip[1], 0.0), (c[0] + sa * 1.0, c[1] - ca * 1.0)]), BRONZE, z=z + 0.4, sd=0.6, hi=0.3, ol=0.8)
    return E


def _mace(cv, h, ma, z, near=True, smear=0.0, pivot=None):
    """Dilimli tunç topuz (şestopor): el h, sap yönü ma (0 = aşağı). smear: vuruş karesinde kuru fırça hız izi
    (pivot = omuz; iz topuz başının geldiği yay üzerinde, geriye doğru incelir)."""
    d = (math.sin(ma), math.cos(ma))
    n = (-d[1], d[0])
    L = 12.5
    end = (h[0] + d[0] * L, h[1] + d[1] * L)
    butt = (h[0] - d[0] * 2.6, h[1] - d[1] * 2.6)
    cv.shape(cv.capsule(butt, end, 1.0, 0.9), HAFT if near else HAFT.darker(0.75), z=z, sd=0.8, hi=0.3,
             details=[('ink', [lerp2(butt, end, t), lerp2(butt, end, t + 0.06)], 0.9) for t in (0.35, 0.6)])
    # sap sargısı (kabza) + sapın ucunda tunç halka
    cv.shape(cv.capsule(lerp2(butt, end, 0.02), lerp2(butt, end, 0.22), 1.2, 1.15), LEATHER, z=z + 0.05, sd=0.5, ol=0.7,
             details=[('ink', [along(butt, end, t, -1.3), along(butt, end, t + 0.035, 1.3)], 0.8, (0.1, 0.1)) for t in (0.05, 0.1, 0.15, 0.2)])
    cv.shape(cv.capsule(lerp2(butt, end, 0.86), lerp2(butt, end, 0.93), 1.35, 1.35), BRONZE if near else BRONZE_B, z=z + 0.1, sd=0.5, hi=0.3, ol=0.8)
    hc = (end[0] + d[0] * 3.0, end[1] + d[1] * 3.0)
    # baş: dilimli küre (sekiz lob; yan dilimler siluette dişli), tepede sivri topuz
    ang = math.atan2(d[1], d[0])
    lobes = []
    for j in range(16):
        a = ang + j / 16 * math.tau
        r = 3.9 if j % 2 == 0 else 3.1
        ex = 1.12 if abs(math.cos(a - ang)) > 0.7 else 1.0     # sap ekseninde biraz uzun
        lobes.append((hc[0] + math.cos(a) * r * ex, hc[1] + math.sin(a) * r * ex, 0.0 if j % 2 == 0 else 1.0))
    core = cv.blob(lobes)
    spike = (hc[0] + d[0] * 6.4, hc[1] + d[1] * 6.4)
    cap = cv.blob([(hc[0] + d[0] * 3.0 + n[0] * 1.3, hc[1] + d[1] * 3.0 + n[1] * 1.3), (spike[0], spike[1], 0.0),
                   (hc[0] + d[0] * 3.0 - n[0] * 1.3, hc[1] + d[1] * 3.0 - n[1] * 1.3)])
    head = ik.union(core, cap)
    det = []
    for o in (-1.6, 0.0, 1.6):     # dilim sırtları
        det.append(('ink', [along(hc, spike, -0.55, o * 0.8), along(hc, spike, -0.05, o * 1.15), along(hc, spike, 0.42, o * 0.8)], 1.0, (0.2, 0.3)))
    det.append(('deep', cv.wedge([along(hc, spike, -0.55, 2.4), along(hc, spike, -0.05, 3.2), along(hc, spike, 0.42, 2.4)], 0.9, -1.0)))
    cv.shape(head, BRONZE if near else BRONZE_B, z=z + 0.2, sd=2.0, hi=0.6, details=det, cast=0.6)
    if smear > 0 and pivot is not None:
        # kuru fırça hız izi: topuz başının geldiği yayda (önceki açılar daha büyük), geriye incelen kıl darbeleri
        R0 = math.hypot(hc[0] - pivot[0], hc[1] - pivot[1])
        a_now = math.atan2(hc[0] - pivot[0], hc[1] - pivot[1])
        for k in range(9):        # kuru fırça: aralıklı kıl darbeleri, uzunlukları farklı
            dr = (k - 4) * 0.85
            ln = 0.55 + 0.45 * abs(math.sin(k * 2.3 + 0.7))
            if k in (0, 8):
                ln *= 0.6
            pts = [(pivot[0] + math.sin(a_now + 0.04 + j * 0.12 * smear * ln) * (R0 + dr), pivot[1] + math.cos(a_now + 0.04 + j * 0.12 * smear * ln) * (R0 + dr))
                   for j in range(7)]
            cv.stroke(pts, 3.4 - abs(k - 4) * 0.35, z=z - 0.5, col=INK, taper=(0.02, 0.98), alpha=0.92)
    return hc


def _bony_hand(cv, e, h, z, near=True):
    m = BONE if near else BONE_B
    fist = cv.blob([along(e, h, 0.86, -1.6), along(e, h, 0.88, 1.7), along(e, h, 1.02, 2.2), along(e, h, 1.18, 1.8),
                    along(e, h, 1.24, 0.2), along(e, h, 1.18, -1.6), along(e, h, 1.02, -2.0)])
    det = [('ink', [along(e, h, 1.06, o), along(e, h, 1.22, o + 0.1)], 1.0, (0.05, 0.6)) for o in (-1.0, 0.0, 1.0)]
    det.append(('deep', cv.wedge([along(e, h, 0.9, -1.6), along(e, h, 1.05, -2.0), along(e, h, 1.2, -1.5)], 0.5, 1.0)))
    cv.shape(fist, m, z=z, sd=1.0, hi=0.3, details=det)


def _arm(cv, sh, e, h, z, near, bony=True, pauldron=True):
    fm = FELT if near else FELT_B
    up = cv.blob([along(sh, e, t, o) for t, o in ((0.0, 3.4), (0.3, 3.5), (0.7, 2.9), (1.05, 2.4), (1.05, -2.3), (0.6, -2.9), (0.15, -3.3), (-0.1, -2.6))])
    det = []
    if near:
        det += cv.fold([along(sh, e, 0.6, -2.8), along(sh, e, 0.75, -1.2), along(sh, e, 0.85, 0.2)], 0.5, 1.2, 1, (0.1, 0.7))
        det += cv.fold([along(sh, e, 0.35, 2.8), along(sh, e, 0.5, 1.2)], 0.45, 1.0, -1, (0.1, 0.7))
    cv.shape(up, fm, z=z, sd=2.4, details=det, bounce=0.25 if near else 0.0)
    # ön kol: deri siper + tunç şerit
    fo = cv.blob([along(e, h, t, o) for t, o in ((-0.05, 2.5), (0.3, 2.7), (0.8, 2.0), (0.95, 1.8), (0.95, -1.8), (0.6, -2.3), (0.2, -2.6), (-0.08, -2.0))])
    fdet = []
    if near:
        for t in (0.25, 0.45, 0.65):
            fdet.append(('ink', [along(e, h, t, -2.4), along(e, h, t + 0.06, 2.4)], 1.0, (0.1, 0.1)))
        fdet.append(('col', cv.limb([along(e, h, 0.15, 1.7), along(e, h, 0.85, 1.4)], [0.6, 0.5]), BRONZE.base))
        fdet.append(('stroke', [along(e, h, 0.2, 1.9), along(e, h, 0.7, 1.6)], 0.8, BRONZE.hi, (0.3, 0.6)))
    cv.shape(fo, LEATHER if near else LEATHER.darker(0.75), z=z + 0.1, sd=1.8, hi=0.3 if near else 0.0, details=fdet)
    if bony:
        _bony_hand(cv, e, h, z + 0.3, near)
    if pauldron:
        pts = [along(sh, e, -0.3, -2.6), along(sh, e, -0.32, 1.8), along(sh, e, -0.02, 4.1), along(sh, e, 0.38, 4.0),
               along(sh, e, 0.52, 2.1), along(sh, e, 0.48, -1.8), along(sh, e, 0.22, -3.8)]
        pdet = []
        for t in (-0.08, 0.1, 0.27):
            pdet.append(('ink', [along(sh, e, t - 0.02, -3.6), along(sh, e, t + 0.05, 0.2), along(sh, e, t - 0.01, 3.9)], 1.15, (0.12, 0.12)))
            for o in (-2.2, -0.6, 1.0, 2.6):
                pdet.append(('ink', [along(sh, e, t + 0.02, o), along(sh, e, t + 0.14, o + 0.15)], 0.9, (0.2, 0.2)))
        pdet.append(('col', cv.ellipse(along(sh, e, 0.3, 2.4), 1.2, 0.8), VERD))
        cv.shape(cv.blob(pts), BRONZE if near else BRONZE_B, z=z + 0.6, sd=1.6, hi=0.55 if near else 0.0, details=pdet, cast=0.5)


def _leg(cv, hip, a, z, near):
    k, f = fk_leg(hip, a[0], a[1], L_TH, L_SH)
    wm = WRAP if near else WRAP_B
    bm = BOOT if near else BOOT_B
    thigh = cv.limb([hip, lerp2(hip, k, 0.5), k], [4.2, 4.0, 3.2])
    cv.shape(thigh, wm, z=z, sd=2.2)
    bt = lerp2(k, f, 0.55)
    shin = cv.limb([k, lerp2(k, f, 0.35), bt], [3.1, 3.2, 2.7])
    sdet = []
    for t in (0.1, 0.25, 0.4, 0.55, 0.7, 0.85):   # sargı: çapraz bant çizgileri
        sdet.append(('ink', [along(k, bt, t, -3.0), along(k, bt, t + 0.1, 3.0)], 1.0, (0.15, 0.15)))
    cv.shape(shin, wm, z=z + 0.1, sd=1.8, details=sdet if near else sdet[::2])
    toe = (f[0] + 4.8, f[1] - 0.6)
    boot = ik.union(cv.limb([bt, lerp2(bt, f, 0.6), f], [3.0, 2.8, 2.6]),
                    cv.blob([(f[0] - 2.4, f[1] - 1.4), (f[0] + 1.0, f[1] - 2.0), (f[0] + 3.4, f[1] - 1.0), (toe[0], toe[1] - 0.4),
                             (toe[0] + 0.6, toe[1] - 1.2, 0.0), (toe[0] + 0.4, f[1] + 0.2), (f[0] - 2.4, f[1] + 0.3, 0.0)]))
    bdet = [('ink', [along(bt, f, 0.05, -2.9), along(bt, f, 0.08, 2.9)], 1.6, (0.1, 0.1)),
            ('ink', [(f[0] + 0.5, f[1] - 1.8), (f[0] + 2.0, f[1] - 0.9), (f[0] + 3.2, f[1] - 0.7)], 1.0, (0.3, 0.5))]
    cv.shape(boot, bm, z=z + 0.3, sd=1.5, hi=0.3 if near else 0.0, details=bdet)
    cv.shape(cv.blob([(f[0] - 2.5, f[1] - 0.2), (toe[0] + 0.4, f[1] - 0.2), (toe[0] + 0.3, f[1] + 0.5, 0.0), (f[0] - 2.4, f[1] + 0.5, 0.0)]),
             Ink('#231a1e', '#141014', '#3a3036'), z=z + 0.35, flat=True, ol=0.7)
    # tunç baldır siperi (greave) + diz kapağı
    gp = cv.blob([along(k, bt, 0.12, 0.6), along(k, bt, 0.1, 3.3), along(k, bt, 0.55, 3.4), along(k, bt, 0.95, 2.8),
                  along(k, bt, 0.98, 0.4), along(k, bt, 0.5, 0.2)])
    cv.shape(gp, BRONZE if near else BRONZE_B, z=z + 0.4, sd=1.0, hi=0.5 if near else 0.0,
             details=[('ink', [along(k, bt, 0.2, 2.0), along(k, bt, 0.85, 1.9)], 0.9, (0.3, 0.3))])
    kp = cv.blob([along(k, f, -0.12, 0.2), along(k, f, -0.08, 3.4), along(k, f, 0.12, 3.6), along(k, f, 0.2, 1.0), along(k, f, 0.05, -1.2)])
    cv.shape(kp, BRONZE if near else BRONZE_B, z=z + 0.45, sd=0.9, hi=0.45 if near else 0.0)
    return k, f


def _head(cv, head, p, z):
    hx, hy = head
    jaw = p.get('jaw', 0.0)
    flare = p.get('flare', 0.0)
    ph = p.get('ph', 0.0)
    # sorguç (at kılı): miğfer tepesinden arkaya akar
    top = (hx + 0.6, hy - 13.6)
    for k in range(6):
        sw = math.sin(ph - k * 0.7) * 0.18 + p.get('plume', 0.0)
        st = chain((top[0] - 0.2 + k * 0.15, top[1] + 0.3 + k * 0.15), 7, 2.3 + (k % 3) * 0.35, math.pi * 1.22 - k * 0.05 + sw, -0.13, ph + k * 0.9, 0.22)
        cv.shape(ik.taper_path([cv.W(q) for q in st], cv.u(1.7 if k % 2 else 2.2), (0.1, 0.9)), PLUME if k % 3 else PLUME.darker(0.75),
                 z=z - 1.5 + k * 0.05, sd=0.6, hi=0.25 if k % 3 == 1 else 0.0, ol=0.7)
    # ensel (zincir örgü): miğferin arkasından omuza
    av = cv.blob([(hx - 5.6, hy - 2.6), (hx - 7.0, hy + 2.0), (hx - 7.6, hy + 6.8, 0.6), (hx - 4.0, hy + 8.0), (hx - 0.5, hy + 7.0),
                  (hx + 1.0, hy + 4.0), (hx - 0.5, hy + 1.0), (hx - 2.0, hy - 1.6)])
    mdet = []
    for r in range(6):
        y = hy - 0.8 + r * 1.45
        pts = [(hx - 7.8 + j * 1.2, y + (0.45 if j % 2 else 0.0)) for j in range(9)]
        mdet.append(('ink', pts, 0.75, (0.05, 0.05)))
    cv.shape(av, MAIL, z=z, sd=1.6, hi=0.3, details=mdet, spec=0.4)
    # kafatası yüz: elmacık, burun boşluğu, göz çukuru, dişler, alt çene; yanakta kurumuş deri
    skull = cv.blob([(hx - 2.6, hy - 2.4), (hx + 2.0, hy - 3.2), (hx + 5.0, hy - 2.4), (hx + 6.0, hy - 0.6), (hx + 6.2, hy + 1.4),
                     (hx + 5.4, hy + 2.6), (hx + 2.4, hy + 3.2), (hx - 1.4, hy + 3.2), (hx - 2.8, hy + 1.0)])
    sdet = [('col', cv.blob([(hx - 2.0, hy - 0.6), (hx + 0.8, hy - 0.2), (hx + 1.4, hy + 1.8), (hx - 0.6, hy + 2.6), (hx - 2.2, hy + 1.6)]), SKINDRY.base),
            ('ink', [(hx - 1.6, hy + 0.2), (hx - 0.2, hy + 1.2), (hx + 0.6, hy + 2.4)], 0.9, (0.2, 0.5)),
            ('deep', cv.blob([(hx + 4.6, hy + 0.4), (hx + 5.6, hy + 0.7), (hx + 5.2, hy + 1.7, 0.0)])),
            ('ink', [(hx + 1.2, hy + 2.4), (hx + 3.0, hy + 2.6), (hx + 5.4, hy + 2.4)], 1.3, (0.1, 0.1))]
    for i in range(4):
        x = hx + 1.6 + i * 1.05
        sdet.append(('ink', [(x, hy + 1.9), (x + 0.05, hy + 3.0)], 0.8, (0.1, 0.1)))
    cv.shape(skull, BONE, z=z + 0.5, sd=1.8, hi=0.35, details=sdet, bounce=0.3)
    # alt çene (sallanır)
    jd = jaw * 2.2
    jw = cv.blob([(hx - 1.6, hy + 2.6), (hx + 4.8, hy + 2.9 + jd * 0.8), (hx + 4.6, hy + 4.1 + jd), (hx + 1.0, hy + 4.4 + jd * 0.6), (hx - 1.2, hy + 3.6)])
    jdet = [('ink', [(hx + 1.6 + i * 1.0, hy + 3.0 + jd * 0.7), (hx + 1.7 + i * 1.0, hy + 3.7 + jd * 0.75)], 0.75, (0.1, 0.1)) for i in range(3)]
    cv.shape(jw, BONE_B, z=z + 0.45, sd=0.9, details=jdet)
    if jaw > 0.2:
        cv.fill(cv.blob([(hx + 1.2, hy + 2.9), (hx + 5.0, hy + 2.8), (hx + 4.6, hy + 2.9 + jd * 0.8), (hx + 1.2, hy + 3.2 + jd * 0.5)]), INK, z=z + 0.44)
    # göz çukuru + soğuk Kut ışığı (telegraf: flare ile büyür, arkaya iz bırakır)
    sock = cv.blob([(hx + 1.2, hy - 1.4), (hx + 3.2, hy - 2.0), (hx + 4.3, hy - 0.9), (hx + 3.6, hy + 0.5), (hx + 1.6, hy + 0.4)])
    cv.fill(sock, INK, z=z + 0.6)
    er = 0.55 + 0.35 * flare
    cv.fill(cv.ellipse((hx + 2.9, hy - 0.7), er * 1.15, er), EYE, z=z + 0.7, glow=EYE_GLOW)
    if flare > 0.05:
        trail = [(hx + 3.0, hy - 0.8), (hx + 0.5, hy - 1.4 - flare * 0.4), (hx - 2.5 - flare * 2.0, hy - 2.0 - flare * 0.8)]
        cv.stroke(trail, 1.6 + flare * 1.6, z=z + 0.65, col=EYE, taper=(0.1, 0.95), glow=EYE_GLOW)
        cv.fill(cv.ellipse((hx + 2.9, hy - 0.7), er * 2.4, er * 2.2), (0, 0, 0), z=-99, glow=(0.15 * flare, 0.45 * flare, 0.6 * flare), alpha=0.0)
    # miğfer: sivri dilimli kase + alın bandı (perçinli) + burun siperi + yanak siperi
    helm = cv.blob([(hx - 6.0, hy - 1.6), (hx - 6.2, hy - 5.0), (hx - 4.0, hy - 9.2), (hx - 0.2, hy - 12.6), (hx + 0.6, hy - 14.0, 0.0),
                    (hx + 2.0, hy - 12.2), (hx + 5.0, hy - 8.8), (hx + 6.8, hy - 5.0), (hx + 7.0, hy - 1.6, 0.4)])
    hdet = []
    for o in (-3.6, -0.6, 2.6, 5.2):     # dilim kenarları (tepeye yakınsar)
        hdet.append(('ink', [(hx + o, hy - 2.4), (hx + o * 0.55 + 0.2, hy - 8.0), (hx + 0.5, hy - 13.2)], 1.0, (0.05, 0.6)))
    hdet.append(('col', cv.blob([(hx - 3.2, hy - 6.0), (hx - 1.8, hy - 7.6), (hx - 1.2, hy - 5.6, 0.0)]), VERD))
    cv.shape(helm, BRONZE, z=z + 1.0, sd=2.6, hi=0.6, details=hdet, cast=0.8)
    band = cv.blob([(hx - 6.3, hy - 3.4), (hx + 7.1, hy - 3.6), (hx + 7.3, hy - 1.2, 0.0), (hx - 6.2, hy - 1.0, 0.0)])
    bdet = [('col', cv.ellipse((hx + x, hy - 2.3), 0.5, 0.5), BRONZE.hi) for x in (-4.6, -2.0, 0.6, 3.2, 5.8)]
    cv.shape(band, BRONZE, z=z + 1.1, sd=0.9, hi=0.4, details=bdet, ol=0.9)
    nasal = cv.blob([(hx + 5.4, hy - 2.6), (hx + 6.6, hy - 2.8), (hx + 6.9, hy + 1.6, 0.0), (hx + 5.9, hy + 1.9, 0.0)])
    cv.shape(nasal, BRONZE, z=z + 1.2, sd=0.7, hi=0.35, ol=0.8)
    cheek = cv.blob([(hx - 3.6, hy - 1.4), (hx - 0.4, hy - 1.6), (hx - 0.6, hy + 2.6), (hx - 2.4, hy + 4.2, 0.0), (hx - 3.8, hy + 2.0)])
    cv.shape(cheek, BRONZE, z=z + 1.15, sd=1.1, hi=0.4, ol=0.9,
             details=[('col', cv.ellipse((hx - 2.0, hy + 0.4), 0.5, 0.5), BRONZE.hi), ('col', cv.ellipse((hx - 2.2, hy + 2.4), 0.45, 0.45), BRONZE.hi)])
    # tepe: tüp + topuz
    cv.shape(cv.ellipse((hx + 0.6, hy - 13.7), 1.0, 0.9), BRONZE, z=z + 1.3, sd=0.5, hi=0.3, ol=0.8)


def draw(cv, p):
    lean = p.get('lean', 0.0)
    bob = p.get('bob', 0.0)
    ph = p.get('ph', 0.0)
    shield = p.get('shield', 1.0)
    hip = (p.get('hx', 0.0), ground(p))
    ax = (math.sin(lean), -math.cos(lean))
    pe = (math.cos(lean), math.sin(lean))
    tl = TORSO - bob * 0.6

    def T(u, v):
        return (hip[0] + ax[0] * u + pe[0] * v, hip[1] + ax[1] * u + pe[1] * v)
    neck = T(tl, 0.6)
    head = (neck[0] + 1.6 + math.sin(lean) * 1.8 + p.get('hdx', 0.0), neck[1] - 5.8 + p.get('hdy', 0.0))
    sh_b = T(tl - 3.4, -3.8)
    sh_f = T(tl - 3.2, 3.4)
    out = {'head': head}

    # ---- arka kol + topuz
    ab = p.get('ab', (0.4, 0.5))
    e, h = fk_arm(sh_b, ab[0], ab[1], L_UP, L_FO)
    mz = p.get('mace_z', -12.0)
    _mace(cv, h, p.get('mace', 0.0), mz, near=mz > 0, smear=p.get('smear', 0.0), pivot=sh_b)
    _arm(cv, sh_b, e, h, -11.0 if mz < 0 else mz + 1.0, near=mz > 0, pauldron=False)

    # ---- arka etek kanadı
    kb, _ = fk_leg(hip, p['lb'][0], p['lb'][1], L_TH, L_SH)
    kf, _ = fk_leg(hip, p['lf'][0], p['lf'][1], L_TH, L_SH)
    sk = p.get('sk', 0.0)
    back_fl = cv.blob([(hip[0] - 5.4, hip[1] - 2.0), (hip[0] + 1.0, hip[1] - 1.0), (kb[0] + 2.0 + sk, kb[1] + 1.4, 0.0),
                       (kb[0] - 1.6 + sk * 1.5, kb[1] + 2.4), (kb[0] - 5.0 + sk * 2.0, kb[1] + 1.0, 0.0)])
    cv.shape(back_fl, FELT_B, z=-10, sd=2.0, details=cv.fold([(hip[0] - 2.0, hip[1] + 1.0), (kb[0] - 1.4 + sk, kb[1])], 0.7, 1.2, 1))

    # ---- arka bacak
    _leg(cv, (hip[0] - 1.6, hip[1]), p['lb'], -9, False)

    # ---- ön etek (kaftan) : diz boyu, ön kanat ön dizi izler
    F = (max(hip[0] + 5.0, kf[0] + 2.6) + sk * 0.8, max(hip[1] + 5.0, kf[1] + 2.2))
    B = (min(hip[0] - 5.0, kb[0] - 1.6) + sk * 1.6, max(hip[1] + 5.0, kb[1] + 2.0))
    wav = [(F[0], F[1], 0.0)]
    for j, t in enumerate((0.25, 0.5, 0.75)):
        q = lerp2(F, B, t)
        wav.append((q[0], q[1] + (0.9 if j % 2 == 0 else 0.1) + 0.5 * math.sin(math.pi * t)))
    wav.append((B[0], B[1], 0.0))
    skirt = cv.blob([(hip[0] - 6.0, hip[1] - 2.6, 0.6), (hip[0] + 6.0, hip[1] - 2.6, 0.6)] + wav)
    sdet = []
    for j, (u0, t) in enumerate(((-3.8, 0.85), (-1.2, 0.6), (1.4, 0.35), (3.8, 0.12))):
        top_ = (hip[0] + u0, hip[1] + 0.8)
        q = lerp2(F, B, t)
        sdet += cv.fold([top_, (lerp2(top_, q, 0.5)[0] - 0.3, lerp2(top_, q, 0.5)[1]), q], 0.8, 1.2, -1, taper=(0.7, 0.05))
    # yırtık etek ucu: birkaç küçük çentik
    for t in (0.18, 0.62):
        q = lerp2(F, B, t)
        sdet.append(('ink', [(q[0] - 0.4, q[1] - 1.4), (q[0], q[1] + 0.6)], 1.2, (0.6, 0.1)))
    cv.shape(skirt, FELT, z=1.0, sd=2.8, details=sdet, hatch=0.35, deep=0.25, bounce=0.3)
    hem = [(x, y) for (x, y, *_) in wav]
    strip = ik.union(*[cv.capsule((x, y - 1.0), (x2, y2 - 1.0), 1.0, 1.0) for (x, y), (x2, y2) in zip(hem, hem[1:])])
    cv.shape(ik.isect(skirt, strip), Ink('#3a2a26', '#1e1418', '#5a4640'), z=1.1, sd=0.5, ol=0.5)

    # ---- gövde: tunç lamel zırh
    torso = cv.blob([T(-1.0, -6.0), T(3.0, -5.3), T(7.5, -6.6), T(12.0, -8.2), T(15.8, -7.4), T(18.0, -3.6), T(18.4, 2.4),
                     T(16.0, 7.9), T(11.6, 9.5), T(6.6, 7.2), T(3.0, 5.7), T(-1.0, 6.4)])
    tdet = []
    rows = (1.6, 4.0, 6.4, 8.8, 11.2, 13.6)
    for i, u in enumerate(rows):
        tdet.append(('shade', cv.wedge([T(u + 2.2, -7.4), T(u + 2.0, 0.6), T(u + 2.2, 8.4)], 0.4, 1.0)))
        tdet.append(('ink', [T(u, -7.8), T(u - 0.3, 0.6), T(u, 8.8)], 1.2, (0.05, 0.05)))
        for v in (-6.6, -4.4, -2.2, 0.0, 2.2, 4.4, 6.6):
            vv = v + (1.1 if i % 2 else 0.0)
            tdet.append(('ink', [T(u + 0.2, vv), T(u + 2.2, vv)], 0.95, (0.1, 0.3)))
        tdet.append(('stroke', [T(u + 0.5, -3.4), T(u + 0.45, -2.4)], 1.0, BRONZE.hi, (0.2, 0.2)))
    tdet.append(('col', cv.blob([T(7.0, 2.6), T(8.0, 3.6), T(7.4, 4.6), T(6.6, 3.6)]), VERD))
    cv.shape(torso, BRONZE, z=2.0, sd=3.6, hi=0.6, details=tdet, deep=0.25, bounce=0.3)
    # zincir yaka
    col_ = cv.blob([T(14.6, -6.0), T(18.4, -4.4), T(19.4, 0.0), T(18.4, 4.0), T(15.2, 4.8), T(15.8, 0.0)])
    cv.shape(col_, MAIL, z=2.5, sd=1.2, spec=0.4,
             details=[('ink', [T(u_, -4.4 + j * 0.0) for j in range(1)] + [T(u_, 0.0), T(u_ - 0.3, 3.6)], 0.7, (0.05, 0.05)) for u_ in (15.2, 16.4, 17.5)])
    # kemer + tunç plakalar
    belt = cv.blob([T(-0.4, -6.6), T(2.6, -6.8), T(2.8, 7.0), T(-0.6, 6.9)])
    bdet = [('col', cv.blob([T(0.0, v - 0.8), T(2.2, v - 0.8), T(2.2, v + 0.8), T(0.0, v + 0.8)]), BRONZE.base) for v in (-3.6, 0.4, 4.2)]
    bdet += [('stroke', [T(1.7, v - 0.6), T(1.7, v + 0.5)], 0.8, BRONZE.hi, (0.2, 0.2)) for v in (-3.6, 0.4, 4.2)]
    cv.shape(belt, LEATHER, z=3.0, sd=1.0, hi=0.3, details=bdet, cast=0.5)
    # lamel etek parçaları (ön + yan): kemerden uyluk ortasına
    for (v0, v1, zz, m) in ((-6.4, -0.8, 3.2, BRONZE_B), (0.6, 6.6, 3.4, BRONZE)):
        dv = sk * 0.6
        tas = cv.blob([(T(0.4, v0)[0], T(0.4, v0)[1], 0.0), (T(0.4, v1)[0], T(0.4, v1)[1], 0.0), (T(-7.0, v1 + 0.6 + dv)[0], T(-7.0, v1 + 0.6 + dv)[1], 0.0),
                       (T(-7.0, v0 - 0.4 + dv)[0], T(-7.0, v0 - 0.4 + dv)[1], 0.0)])
        tdt = []
        for u in (-2.2, -4.6):     # bağcık sıraları
            tdt.append(('ink', [T(u, v0 - 0.3 + dv * (-u / 7)), T(u, v1 + 0.5 + dv * (-u / 7))], 1.1, (0.02, 0.02)))
        vv = v0 + 1.2
        while vv < v1 + 0.2:      # dikey şeritler
            tdt.append(('ink', [T(0.2, vv), T(-6.8, vv + 0.4 + dv)], 0.8, (0.05, 0.3)))
            tdt.append(('stroke', [T(-0.4, vv - 0.55), T(-2.0, vv - 0.5)], 0.8, BRONZE.hi, (0.2, 0.4)))
            vv += 1.5
        cv.shape(tas, m, z=zz, sd=1.4, hi=0.35 if m is BRONZE else 0.0, details=tdt, cast=0.4)

    # ---- ön bacak (uyluk eteğin altında kalır)
    _leg(cv, (hip[0] + 1.6, hip[1]), p['lf'], 0.2, True)

    # ---- baş (biraz küçük: kahraman oranı)
    hs = 0.86
    cv.push(lambda q, c=head: (c[0] + (q[0] - c[0]) * hs, c[1] + (q[1] - c[1]) * hs))
    _head(cv, head, p, 9.0)
    cv.pop()

    # ---- ön kol + kalkan
    af = p.get('af', (0.9, 1.1))
    e2, h2 = fk_arm(sh_f, af[0], af[1], L_UP, L_FO)
    out['hand'] = h2
    sz = 14.0
    if shield >= 1.5:   # darbe: kalkan ileri, yüzü yarı dönük
        face, rot, sc = 0.42, p.get('srot', -0.06), (h2[0] + 2.4, h2[1] - 0.6)
    elif shield >= 0.5:  # siper: geniş yüz
        face, rot, sc = 0.6, p.get('srot', 0.0), (h2[0] + 2.0, h2[1] - 1.0)
    else:              # yanda: kenarı görünür
        face, rot, sc = 0.24, p.get('srot', 0.25), (h2[0] + 0.8, h2[1] + 1.0)
    if shield < 0.5:
        # kalkan gövdenin önünde ama kol onun önünde (kayışından tutulmuş, yana açılmış)
        _shield(cv, sc, 11.5, face, rot, sz - 0.5, spin=p.get('spin', 0.0))
        _arm(cv, sh_f, e2, h2, sz + 0.5, True)
    else:
        _arm(cv, sh_f, e2, h2, sz - 2.0, True)
        _shield(cv, sc, 11.5, face, rot, sz + 1.0, spin=p.get('spin', 0.0))
    out['shield'] = sc
    return out


# ------------------------------------------------------------ pozlar (v1 BEKCI_ANIMS ile aynı ad/kare sayısı)
def keyed(t, frames):
    return frames[min(len(frames) - 1, int(t * len(frames) + 1e-6))]


def _idle(t):
    s = math.sin(t * math.tau)
    return dict(bob=0.5 * s, lean=0.05, lb=(-0.34, -0.02), lf=(0.42, 0.62), shield=1.0, af=(0.95, 1.05 + 0.04 * s),
                ab=(0.25 + 0.04 * s, 0.35), mace=0.12 + 0.08 * s, ph=t * math.tau)


def _walk(t):
    ph = t * math.tau
    s, c = math.sin(ph), math.cos(ph)
    return dict(bob=-abs(s) * 0.8 + 0.4, lean=0.1, lb=(-0.55 * s, 0.25 + 0.75 * max(0.0, c)), lf=(0.55 * s, 0.25 + 0.75 * max(0.0, -c)),
                shield=1.0, af=(0.95, 1.05), ab=(0.3 - 0.35 * s, 0.4), mace=0.25 - 0.3 * s, sk=-0.5 * s, ph=ph, hdy=0.3 * abs(s))


def _charge(t):
    ph = t * math.tau
    s, c = math.sin(ph), math.cos(ph)
    return dict(bob=1.0, lean=0.42, lb=(-0.95 * s - 0.1, 0.35 + 1.1 * max(0.0, c)), lf=(0.95 * s + 0.2, 0.35 + 1.1 * max(0.0, -c)),
                shield=2.0, af=(1.45, -0.05), ab=(-0.8, 0.9), mace=-1.4, sk=-1.4, ph=ph * 1.5, air=0.6 * abs(c),
                plume=0.35, flare=0.5, srot=-0.1)


BEKCI_POSES = {
    'idle': (4, _idle),
    'walk': (6, _walk),
    'guard': (1, lambda t: dict(bob=1.6, lean=0.2, lb=(-0.55, -0.1), lf=(0.75, 1.15), shield=1.0, af=(1.05, 1.2),
                                ab=(-0.45, 1.6), mace=-2.7, ph=0.6, hdy=0.4)),
    'windup': (2, lambda t: keyed(t, [
        dict(bob=1.0, lean=-0.12, lb=(-0.35, 0.0), lf=(0.5, 0.75), shield=0.0, af=(0.35, 0.9), ab=(-2.3, -0.4), mace=-2.35,
             mace_z=-12, ph=1.0, flare=0.6, plume=0.25, jaw=0.3, hdx=-0.4),
        dict(bob=1.8, lean=-0.22, lb=(-0.3, 0.0), lf=(0.55, 0.95), shield=0.0, af=(0.2, 1.0), ab=(-2.55, -0.7), mace=-1.75,
             mace_z=-12, ph=1.6, flare=1.0, plume=0.4, jaw=0.6, hdx=-0.8)])),
    'strike': (2, lambda t: keyed(t, [
        dict(bob=1.2, lean=0.38, lb=(-0.75, 0.0), lf=(0.85, 0.9), shield=0.0, af=(0.05, 0.6), ab=(1.55, 0.1), mace=1.45,
             mace_z=16, ph=3.0, smear=0.0, flare=0.8, plume=-0.3, jaw=0.8, sk=-0.8),
        dict(bob=1.6, lean=0.45, lb=(-0.8, 0.0), lf=(0.95, 1.0), shield=0.0, af=(0.0, 0.5), ab=(1.25, 0.45), mace=2.05,
             mace_z=16, ph=3.8, smear=0.0, flare=0.4, plume=-0.4, jaw=0.4, sk=-1.0)])),
    'bash': (2, lambda t: keyed(t, [
        dict(bob=0.8, lean=0.26, lb=(-0.6, 0.0), lf=(0.7, 0.85), shield=2.0, af=(1.3, 0.25), ab=(-0.4, 0.9), mace=-0.9, ph=2.0, flare=0.4, sk=-0.6),
        dict(bob=1.2, lean=0.4, lb=(-0.85, 0.0), lf=(0.9, 0.95), shield=2.0, af=(1.55, -0.05), ab=(-0.7, 0.9), mace=-1.3, ph=2.6,
             flare=0.6, sk=-1.0, srot=-0.12)])),
    'charge': (4, _charge),
    'stagger': (2, lambda t: keyed(t, [
        dict(bob=2.2, lean=-0.3, lb=(-0.15, 0.1), lf=(0.6, 1.1), shield=0.0, af=(0.6, -0.4), ab=(0.95, 0.35), mace=0.9, ph=0.5,
             jaw=1.0, hdx=-1.0, hdy=0.4, srot=0.5, sk=1.2),
        dict(bob=1.4, lean=-0.2, lb=(-0.2, 0.1), lf=(0.55, 0.95), shield=0.0, af=(0.45, -0.25), ab=(0.75, 0.35), mace=0.65, ph=1.2,
             jaw=0.6, hdx=-0.6, srot=0.4, sk=0.8)])),
    'hurt': (1, lambda t: dict(bob=1.2, lean=-0.22, lb=(-0.3, 0.0), lf=(0.5, 0.8), shield=1.0, af=(0.8, 1.0), ab=(0.9, 0.5), mace=0.6,
                               jaw=0.8, hdx=-0.8, ph=0.3, sk=0.8)),
}
ANIMS = {k: (v[0], v[1], k in ('idle', 'walk'), True) for k, v in BEKCI_POSES.items()}

SHADE = dict(outer=0.5, rim=0.55, rim_col=(0.72, 0.86, 1.0), rim_dir=(0.55, -0.85), rim_w=1.4, form=(7.0, (0.74, 0.72, 0.86)))


def render_frame(anim, i, ss=3):
    n, fn, loop, arm = ANIMS[anim]
    p = fn(i / n)
    cv = ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
