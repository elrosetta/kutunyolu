"""Kurgan Bekçisi (kimlik bekci) — stil v2 "mürekkep-cel" (inkkit.py). v1: creatures2.draw_bekci / BEKCI_ANIMS.

Kurganında dinlenemeyen kadim Göktürk savaşçısı: kurumuş kafatası yüz (oyuk göz çukurunda soğuk Kut ışığı), sivri
dilimli tunç miğfer + burun siperi + zincir ensel + kızıl at kılı sorgucu, tunç lamel zırh ve omuzluk, lamel etek
parçaları, kızıl keçe kaftan, sargılı baldır ve keçe çizme, tunç baldır siperi. Ön kolda deri kaplı büyük yuvarlak
kalkan (tunç kasnak, çivili kenar, sivri göbek, ışıyan Göktürk runa halkası); arka elde (kemik parmaklar) dilimli
tunç topuz (şestopor).

v29 tam gövde animasyonu (docs/TASARIM.md "v29: yer yaratıklarının tam gövde animasyonu"): bacaklar AYAK HEDEFLİ IK
(topuk noktası + ayak eğimi: itişte parmak kökü yerde kalır, topuk kalkar; erişilemeyen hedef kırpılır), kalça kayması,
gövde eğimi + omurga bükümü (bend), omuz dönüşü (tw: vuruşlarda kalça-omuz döner, arka omuz öne gelir), boyun dibinde
dönen baş grubu, bütün figür dönüşümü (x / y / roll: savrulma, yüzüstü ölüm), ikincil hareket (sorguç / etek gecikmesi),
toz, hız çizgisi, yer yarığı. Kareler yaratik_govde.Seq ile anahtar pozlardan üretilir (SEQS), yapay zekâ eşlemesi DURUM.

Bu sayfayı iki yapay zekâ paylaşır: shield (kurgan_bekcisi, yilan_muhafiz, simurg_muhafizi, tamu_bekcisi, tamu_muhafizi,
kaf_bekcisi) ve charger (al_atli, kara_atli, kurgan_atlisi). Çapalar: 'hand' = kalkan eli, 'head' = baş merkezi
(dönüşümlü dünya noktası). Hücre 384x416 (dünya 96x104), ayak (176, 392), çarpışma değişmez.
"""
import math

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_leg, fk_arm, lerp2, chain
from bengu_ink import along, _perp
import yaratik_govde as yg
from yaratik_govde import Seq

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
DUST = Ink('#9a8a74', '#5e5246', '#c8b89c', name='kurgan tozu')


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



def _leg(cv, hip, f, fa, z, near):
    """Ayak hedefli bacak: hip -> topuk f (IK, diz öne bükülür; erişilemeyen hedef kırpılır). fa: ayak eğimi
    (+ topuk kalkık / parmak ucunda itiş, - parmak kalkık / topuk vuruşu); ayak tabanı topuk çevresinde döner."""
    k, f = yg.ik2(hip, f, L_TH, L_SH, -1)
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

    def R(x, y, *r):   # ayak tabanı: topuk çevresinde eğim
        q = yg.rot_about((x, y), f, fa)
        return q + r
    toe = (f[0] + 4.8, f[1] - 0.6)
    boot = ik.union(cv.limb([bt, lerp2(bt, f, 0.6), f], [3.0, 2.8, 2.6]),
                    cv.blob([R(f[0] - 2.4, f[1] - 1.4), R(f[0] + 1.0, f[1] - 2.0), R(f[0] + 3.4, f[1] - 1.0), R(toe[0], toe[1] - 0.4),
                             R(toe[0] + 0.6, toe[1] - 1.2, 0.0), R(toe[0] + 0.4, f[1] + 0.2), R(f[0] - 2.4, f[1] + 0.3, 0.0)]))
    bdet = [('ink', [along(bt, f, 0.05, -2.9), along(bt, f, 0.08, 2.9)], 1.6, (0.1, 0.1)),
            ('ink', [R(f[0] + 0.5, f[1] - 1.8), R(f[0] + 2.0, f[1] - 0.9), R(f[0] + 3.2, f[1] - 0.7)], 1.0, (0.3, 0.5))]
    cv.shape(boot, bm, z=z + 0.3, sd=1.5, hi=0.3 if near else 0.0, details=bdet)
    cv.shape(cv.blob([R(f[0] - 2.5, f[1] - 0.2), R(toe[0] + 0.4, f[1] - 0.2), R(toe[0] + 0.3, f[1] + 0.5, 0.0), R(f[0] - 2.4, f[1] + 0.5, 0.0)]),
             Ink('#231a1e', '#141014', '#3a3036'), z=z + 0.35, flat=True, ol=0.7)
    # tunç baldır siperi (greave) + diz kapağı
    gp = cv.blob([along(k, bt, 0.12, 0.6), along(k, bt, 0.1, 3.3), along(k, bt, 0.55, 3.4), along(k, bt, 0.95, 2.8),
                  along(k, bt, 0.98, 0.4), along(k, bt, 0.5, 0.2)])
    cv.shape(gp, BRONZE if near else BRONZE_B, z=z + 0.4, sd=1.0, hi=0.5 if near else 0.0,
             details=[('ink', [along(k, bt, 0.2, 2.0), along(k, bt, 0.85, 1.9)], 0.9, (0.3, 0.3))])
    kp = cv.blob([along(k, f, -0.12, 0.2), along(k, f, -0.08, 3.4), along(k, f, 0.12, 3.6), along(k, f, 0.2, 1.0), along(k, f, 0.05, -1.2)])
    cv.shape(kp, BRONZE if near else BRONZE_B, z=z + 0.45, sd=0.9, hi=0.45 if near else 0.0)
    return k, f


def _dust(cv, c, amt, dirx=-1.0, seed=0, z=-14.0):
    """Toz bulutu: ayak dibinde kabaran, mürekkep konturlu yumuşak öbekler (hücum, kayma, ağır iniş)."""
    if amt <= 0.02:
        return
    for k in range(5):
        a = seed * 1.7 + k * 2.1
        r = (1.6 + 1.2 * abs(math.sin(a))) * (0.6 + 0.6 * amt)
        x = c[0] + dirx * (k * 2.6 + 1.0) * (0.5 + 0.7 * amt) + math.sin(a) * 1.2
        y = c[1] - r * 0.7 - (k % 2) * 1.2 * amt
        cv.shape(cv.ellipse((x, y), r * 1.25, r), DUST, z=z + k * 0.01, sd=0.8, ol=0.6, hi=0.0)


def _speed(cv, top, bot, x0, amt, z=-15.0):
    """Hücum hız çizgileri: gövdenin arkasında yatay kuru fırça darbeleri."""
    if amt <= 0.02:
        return
    for k in range(6):
        y = top + (bot - top) * (k + 0.5) / 6
        ln = (10.0 + 8.0 * abs(math.sin(k * 2.7 + 0.4))) * amt
        x = x0 - 2.0 * abs(math.sin(k * 1.3))
        cv.stroke([(x, y), (x - ln * 0.5, y + 0.1), (x - ln, y + 0.2)], 2.2 - 0.2 * (k % 3), z=z, col=INK, taper=(0.05, 0.95), alpha=0.7)


def _crack(cv, c, amt, z=-14.0):
    """Ağır topuz vuruşunda yer yarığı ve sıçrayan taş."""
    if amt <= 0.02:
        return
    for k, (a, ln) in enumerate(((-2.8, 7.0), (-2.2, 5.0), (-0.9, 5.5), (-0.35, 8.0), (-1.6, 4.0))):
        e = (c[0] + math.cos(a) * ln * amt, c[1] + math.sin(a) * ln * amt * 0.5)
        cv.stroke([c, lerp2(c, e, 0.5), e], 1.6, z=z + 2.0, col=INK, taper=(0.1, 0.9))
    for k in range(4):
        a = -math.pi * (0.2 + 0.2 * k)
        q = (c[0] + math.cos(a) * 6.0 * amt, c[1] - 2.0 - abs(math.sin(a)) * 5.0 * amt)
        cv.shape(cv.blob([(q[0] - 0.8, q[1]), (q[0], q[1] - 0.9), (q[0] + 0.9, q[1] + 0.2), (q[0], q[1] + 0.7)]), DUST.darker(0.7), z=z + 2.1, sd=0.4, ol=0.7)


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



# ------------------------------------------------------------ iskelet (v29 tam gövde)
H0 = 22.2                # dinlenmede kalça yüksekliği (ayaklar yerde, arka diz hafif bükük)
C0 = (0.0, -30.0)        # bütün figür dönüşüm merkezi (gövde ortası)
BALL = 4.6               # topuk -> parmak ucu (itişte ayak bu noktada döner)

# dinlenme pozu. fb / ff: arka (uzak) / ön (yakın) ayak hedefi (topuk x, yerden yükseklik, eğim: + topuk kalkık, - parmak
# kalkık); hx / hy kalça kayması (hy + aşağı), lean gövde eğimi (+ öne), bend omurga bükümü (göğüs öne kapanır), tw omuz
# dönüşü (+ arka omuz öne: vuruşta kalça-omuz döner), hd / hr baş kayması / boyun dibinde dönüş (+ çene aşağı),
# ab / af kol açıları (dünya; 0 aşağı, + öne), x / y / roll bütün figür (savrulma, ölüm).
REST = dict(x=0.0, y=0.0, roll=0.0, hx=0.0, hy=0.0, lean=0.05, bend=0.0, tw=0.0, bob=0.0,
            fb=(-9.4, 0.0, 0.0), ff=(4.1, 0.0, 0.0), hd=(0.0, 0.0), hr=0.0,
            ab=(0.25, 0.35), mace=0.12, mace_z=-12.0, af=(0.95, 1.05), shield=1.0, srot=None, spin=0.0,
            jaw=0.0, flare=0.0, plume=0.0, ph=0.0, sk=0.0, smear=0.0, dust=0.0, dustx=-1.0, speed=0.0, crack=0.0,
            sfree=None, mfree=None)


def _heel(t):
    """Ayak hedefi (x, h, a) -> topuk noktası (x, yükseklik). a > 0: parmak kökü yerde kalır, topuk kalkar."""
    x, h, a = t
    if a > 0:
        return (x + BALL * (1.0 - math.cos(a)), h + BALL * math.sin(a))
    return (x, h)


def draw(cv, p):
    yg.bake_xf(cv)
    q = dict(REST)
    q.update(p)
    p = q
    lean, bend, tw = p['lean'], p['bend'], p['tw']
    ph = p['ph']
    shield = p['shield']
    roll = p['roll']
    out = {}
    # yerdeki ayrıntılar (dönüşümsüz): toz, yarık
    if p['dust'] > 0.02:
        bx = min(p['fb'][0], p['ff'][0]) if p['dustx'] < 0 else max(p['fb'][0], p['ff'][0]) + 4.0
        _dust(cv, (bx + p['x'], 0.6), p['dust'], p['dustx'], seed=int(ph * 3) % 7)
    yg.xf_push(cv, C0, roll, p['x'], p['y'])
    hip = (p['hx'], -H0 + p['hy'])

    def F(t):   # dünya ayak hedefi -> figür çerçevesi (roll / x / y tersi: yazılan dünya konumu korunur)
        hx_, hh = _heel(t)
        w = (hx_ - p['x'], -hh - p['y'])
        return yg.rot_about(w, C0, -roll)

    tl = TORSO - p['bob'] * 0.6

    def ang(u):
        return lean + bend * max(0.0, u - 6.0) / 12.0

    p6 = (hip[0] + math.sin(lean) * 6.0, hip[1] - math.cos(lean) * 6.0)

    def T(u, v):   # gövde yereli: u omurga boyunca yukarı, v öne (bend: göğüs bel üstünden bükülür)
        if u <= 6.0:
            b = (hip[0] + math.sin(lean) * u, hip[1] - math.cos(lean) * u)
        else:
            am = lean + bend * (u - 6.0) / 24.0
            b = (p6[0] + math.sin(am) * (u - 6.0), p6[1] - math.cos(am) * (u - 6.0))
        a = ang(u)
        return (b[0] + math.cos(a) * v, b[1] + math.sin(a) * v)

    neck = T(tl, 0.6)
    an = ang(tl)
    head = (neck[0] + 1.6 + math.sin(an) * 1.8 + p['hd'][0], neck[1] - 5.8 + p['hd'][1])
    sh_b = T(tl - 3.4, -3.8 + tw * 5.5)
    sh_f = T(tl - 3.2, 3.4 - tw * 3.0)
    if p['speed'] > 0.02:
        _speed(cv, hip[1] - 26.0, hip[1] + 4.0, hip[0] - 12.0, p['speed'])

    # ---- arka kol + topuz
    ab = p['ab']
    e, h = fk_arm(sh_b, ab[0], ab[1], L_UP, L_FO)
    mz = p['mace_z']
    mace_w = None
    if p['mfree'] is None:
        hc = _mace(cv, h, p['mace'], mz, near=mz > 0, smear=p['smear'], pivot=sh_b)
        mace_w = yg.world(cv, hc)
    _arm(cv, sh_b, e, h, -11.0 if mz < 0 else mz + 1.0, near=mz > 0, pauldron=False)

    # ---- bacak çözümü (etek dizleri izler)
    hb_j = (hip[0] - 1.6, hip[1])
    hf_j = (hip[0] + 1.6, hip[1])
    fbt, fft = F(p['fb']), F(p['ff'])
    kb, _ = yg.ik2(hb_j, fbt, L_TH, L_SH, -1)
    kf, _ = yg.ik2(hf_j, fft, L_TH, L_SH, -1)
    fa_b = p['fb'][2] - roll
    fa_f = p['ff'][2] - roll

    # ---- arka etek kanadı
    sk = p['sk']
    back_fl = cv.blob([(hip[0] - 5.4, hip[1] - 2.0), (hip[0] + 1.0, hip[1] - 1.0), (kb[0] + 2.0 + sk, kb[1] + 1.4, 0.0),
                       (kb[0] - 1.6 + sk * 1.5, kb[1] + 2.4), (kb[0] - 5.0 + sk * 2.0, kb[1] + 1.0, 0.0)])
    cv.shape(back_fl, FELT_B, z=-10, sd=2.0, details=cv.fold([(hip[0] - 2.0, hip[1] + 1.0), (kb[0] - 1.4 + sk, kb[1])], 0.7, 1.2, 1))

    # ---- arka bacak
    _leg(cv, hb_j, fbt, fa_b, -9, False)

    # ---- ön etek (kaftan) : diz boyu, ön kanat ön dizi izler
    F_ = (max(hip[0] + 5.0, kf[0] + 2.6) + sk * 0.8, max(hip[1] + 5.0, kf[1] + 2.2))
    B_ = (min(hip[0] - 5.0, kb[0] - 1.6) + sk * 1.6, max(hip[1] + 5.0, kb[1] + 2.0))
    wav = [(F_[0], F_[1], 0.0)]
    for j, t in enumerate((0.25, 0.5, 0.75)):
        q_ = lerp2(F_, B_, t)
        wav.append((q_[0], q_[1] + (0.9 if j % 2 == 0 else 0.1) + 0.5 * math.sin(math.pi * t) + 0.4 * math.sin(ph * 2 + j)))
    wav.append((B_[0], B_[1], 0.0))
    skirt = cv.blob([(hip[0] - 6.0, hip[1] - 2.6, 0.6), (hip[0] + 6.0, hip[1] - 2.6, 0.6)] + wav)
    sdet = []
    for j, (u0, t) in enumerate(((-3.8, 0.85), (-1.2, 0.6), (1.4, 0.35), (3.8, 0.12))):
        top_ = (hip[0] + u0, hip[1] + 0.8)
        q_ = lerp2(F_, B_, t)
        sdet += cv.fold([top_, (lerp2(top_, q_, 0.5)[0] - 0.3, lerp2(top_, q_, 0.5)[1]), q_], 0.8, 1.2, -1, taper=(0.7, 0.05))
    for t in (0.18, 0.62):
        q_ = lerp2(F_, B_, t)
        sdet.append(('ink', [(q_[0] - 0.4, q_[1] - 1.4), (q_[0], q_[1] + 0.6)], 1.2, (0.6, 0.1)))
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
    col_ = cv.blob([T(14.6, -6.0), T(18.4, -4.4), T(19.4, 0.0), T(18.4, 4.0), T(15.2, 4.8), T(15.8, 0.0)])
    cv.shape(col_, MAIL, z=2.5, sd=1.2, spec=0.4,
             details=[('ink', [T(u_, -4.4), T(u_, 0.0), T(u_ - 0.3, 3.6)], 0.7, (0.05, 0.05)) for u_ in (15.2, 16.4, 17.5)])
    belt = cv.blob([T(-0.4, -6.6), T(2.6, -6.8), T(2.8, 7.0), T(-0.6, 6.9)])
    bdet = [('col', cv.blob([T(0.0, v - 0.8), T(2.2, v - 0.8), T(2.2, v + 0.8), T(0.0, v + 0.8)]), BRONZE.base) for v in (-3.6, 0.4, 4.2)]
    bdet += [('stroke', [T(1.7, v - 0.6), T(1.7, v + 0.5)], 0.8, BRONZE.hi, (0.2, 0.2)) for v in (-3.6, 0.4, 4.2)]
    cv.shape(belt, LEATHER, z=3.0, sd=1.0, hi=0.3, details=bdet, cast=0.5)
    # lamel etek parçaları (ön + yan): kemerden uyluk ortasına; ön parça ön uylukla birlikte açılır
    lift_f = max(0.0, (kf[0] - hip[0]) - 4.0) * 0.12
    for (v0, v1, zz, m, ex) in ((-6.4, -0.8, 3.2, BRONZE_B, 0.0), (0.6, 6.6, 3.4, BRONZE, lift_f)):
        dv = sk * 0.6 + ex * 4.0
        tas = cv.blob([(T(0.4, v0)[0], T(0.4, v0)[1], 0.0), (T(0.4, v1)[0], T(0.4, v1)[1], 0.0), (T(-7.0 + ex * 2, v1 + 0.6 + dv)[0], T(-7.0 + ex * 2, v1 + 0.6 + dv)[1], 0.0),
                       (T(-7.0 + ex * 2, v0 - 0.4 + dv)[0], T(-7.0 + ex * 2, v0 - 0.4 + dv)[1], 0.0)])
        tdt = []
        for u in (-2.2, -4.6):
            tdt.append(('ink', [T(u, v0 - 0.3 + dv * (-u / 7)), T(u, v1 + 0.5 + dv * (-u / 7))], 1.1, (0.02, 0.02)))
        vv = v0 + 1.2
        while vv < v1 + 0.2:
            tdt.append(('ink', [T(0.2, vv), T(-6.8, vv + 0.4 + dv)], 0.8, (0.05, 0.3)))
            tdt.append(('stroke', [T(-0.4, vv - 0.55), T(-2.0, vv - 0.5)], 0.8, BRONZE.hi, (0.2, 0.4)))
            vv += 1.5
        cv.shape(tas, m, z=zz, sd=1.4, hi=0.35 if m is BRONZE else 0.0, details=tdt, cast=0.4)

    # ---- ön bacak (uyluk eteğin altında kalır)
    _leg(cv, hf_j, fft, fa_f, 0.2, True)

    # ---- baş grubu: boyun dibinde döner (hr), önden gider (hd); biraz küçük (kahraman oranı)
    hs = 0.86
    yg.xf_push(cv, neck, p['hr'])
    cv.push(lambda q_, c=head: (c[0] + (q_[0] - c[0]) * hs, c[1] + (q_[1] - c[1]) * hs))
    _head(cv, head, p, 9.0)
    out['head'] = yg.world(cv, head)
    cv.pop()
    cv.pop()

    # ---- ön kol + kalkan
    af = p['af']
    e2, h2 = fk_arm(sh_f, af[0], af[1], L_UP, L_FO)
    out['hand'] = yg.world(cv, h2)
    sz = 14.0
    if p['sfree'] is not None:
        _arm(cv, sh_f, e2, h2, sz + 0.5, True)
        sc = h2
    else:
        if shield >= 1.5:   # darbe: kalkan ileri, yüzü yarı dönük
            face, rot, sc = 0.42, p['srot'] if p['srot'] is not None else -0.06, (h2[0] + 2.4, h2[1] - 0.6)
        elif shield >= 0.5:  # siper: geniş yüz
            face, rot, sc = 0.6, p['srot'] if p['srot'] is not None else 0.0, (h2[0] + 2.0, h2[1] - 1.0)
        else:              # yanda: kenarı görünür
            face, rot, sc = 0.24, p['srot'] if p['srot'] is not None else 0.25, (h2[0] + 0.8, h2[1] + 1.0)
        if shield < 0.5:
            _shield(cv, sc, 11.5, face, rot, sz - 0.5, spin=p['spin'])
            _arm(cv, sh_f, e2, h2, sz + 0.5, True)
        else:
            _arm(cv, sh_f, e2, h2, sz - 2.0, True)
            _shield(cv, sc, 11.5, face, rot, sz + 1.0, spin=p['spin'])
    out['shield'] = yg.world(cv, sc)
    cv.pop()   # figür
    # ---- elden düşen kalkan / topuz (ölüm): dünya konumunda, yerde
    if p['mfree'] is not None:
        mx, my, ma = p['mfree']
        _mace(cv, (mx, my), ma, -13.0, near=False)
    if p['sfree'] is not None:
        sx_, sy_, srot_, sface = p['sfree']
        _shield(cv, (sx_, sy_), 11.5, sface, srot_, -13.5, near=False, spin=p['spin'])
    if p['crack'] > 0.02:
        _crack(cv, ((mace_w[0] if mace_w else 44.0) + 1.0, 0.2), p['crack'])
    return out


SHADE = dict(outer=0.5, rim=0.55, rim_col=(0.72, 0.86, 1.0), rim_dir=(0.55, -0.85), rim_w=1.4, form=(7.0, (0.74, 0.72, 0.86)))


# ====================================================================== anahtar pozlar (yaratik_govde.Seq)
# Duruş: disiplinli ağır piyade — geniş taban, ağırlık iki ayak arasında, kalkan göğüs önünde, topuz omuzda. Her vuruş
# ayaktan başlar: arka ayak iter (topuk kalkar), kalça öne kayar, omuz döner (tw), kol en son gelir.
def _foot(phi, home, S, duty, lift, push=0.5, strike=0.25):
    """Döngüsel ayak yolu: basma (duty) boyunca +S/2 -> -S/2 sabit hızla (gövdeye göre geri kayar), salınımda yayla öne."""
    phi %= 1.0
    if phi < duty:
        u = phi / duty
        x = home + S * (0.5 - u)
        a = push * max(0.0, (u - 0.62) / 0.38) ** 1.4
        if u < 0.14:
            a = -strike * (1.0 - u / 0.14)
        return (x, 0.0, a)
    u = (phi - duty) / (1.0 - duty)
    e = u * u * (3 - 2 * u)
    x = home - S * 0.5 + S * e
    h = lift * math.sin(math.pi * u) ** 0.9
    a = push * (1.0 - u) ** 2 - strike * u ** 3
    return (x, h, a)


G = dict(hy=1.4, lean=0.16, fb=(-13.0, 0.0, 0.0), ff=(5.0, 0.0, 0.0), af=(1.0, 1.12), ab=(-1.3, 3.75), mace=-2.3,
         hd=(0.3, 0.4), hr=0.05, shield=1.0)


def _guard(t):
    s = math.sin(t * math.tau)
    s2 = math.sin(t * math.tau * 2)
    p = dict(G)
    # nefes (2 soluk), ağırlık bir ayaktan ötekine (1 tur), tokat tiki: topuz sapını sıkıp gevşetir (0,55-0,75)
    tic = max(0.0, math.sin((t - 0.55) / 0.2 * math.pi)) if 0.55 < t < 0.75 else 0.0
    p.update(bob=0.5 * s2, hy=1.4 + 0.3 * s2 + 0.2 * s, hx=0.6 * s, lean=0.16 + 0.015 * s2, tw=0.04 * s,
             af=(1.0 + 0.02 * s2, 1.12 - 0.03 * s2), ab=(-1.3 - 0.06 * tic, 3.75 + 0.15 * tic), mace=-2.3 - 0.2 * tic,
             hd=(0.3 + 0.3 * s, 0.4 + 0.25 * s2), hr=0.05 + 0.03 * s, ph=t * math.tau, plume=0.05 * s, sk=-0.2 * s)
    return p


def _walk(t):
    """Kalkan önde ağır yürüyüş: topuk-parmak, kalça iniş-çıkışı, omuz karşı dönüşü; adım 20 birim."""
    S, duty = 20.0, 0.6
    p = dict(G)
    p['ff'] = _foot(t, -1.0, S, duty, 3.4)
    p['fb'] = _foot(t - 0.5, -3.6, S, duty, 3.0)
    c2 = math.cos(t * 4 * math.pi)
    s1 = math.sin(t * math.tau)
    p.update(hy=1.6 + 0.9 * c2, hx=0.8, lean=0.2 + 0.02 * c2, tw=0.1 * s1, bob=0.4 * c2,
             af=(1.02, 1.1 + 0.04 * c2), ab=(-1.3 - 0.1 * s1, 3.75 + 0.06 * s1), mace=-2.3 - 0.1 * s1,
             hd=(0.6 + 0.3 * s1, 0.6 + 0.4 * c2), hr=0.07, ph=t * math.tau * 2, sk=-0.6 * s1, plume=-0.05 + 0.1 * c2)
    return p


def _charge(t):
    """Hücum koşusu (kalkan önde, omuz alçak): uçuş evreli koşu; adım 25 birim."""
    S, duty = 25.0, 0.38
    p = {}
    p['ff'] = _foot(t, 1.0, S, duty, 6.5, push=0.7, strike=0.1)
    p['fb'] = _foot(t - 0.5, -1.5, S, duty, 6.0, push=0.7, strike=0.1)
    c = math.cos(4 * math.pi * (t - duty * 0.5))
    p.update(hy=4.2 + 1.3 * c, hx=3.0, lean=0.5 + 0.03 * c, bend=0.15, tw=-0.25, bob=0.6 + 0.4 * c,
             shield=2.0, af=(1.42, -0.1), srot=-0.12, ab=(-0.95 + 0.1 * c, 1.1), mace=-1.6, mace_z=-12.0,
             hd=(1.4, 2.6 + 0.4 * c), hr=0.18, flare=0.7, jaw=0.4, plume=-0.45 + 0.08 * c, sk=-1.6, ph=t * math.tau * 3,
             speed=0.9, dust=0.6, dustx=-1.0)
    return p


SEQS = {}

# ---- siper bekleyişi (8 kare, 1,6 sn): kalkan arkasında nefes, ağırlık aktarımı, topuz sapını sıkma tiki, sorguç salınır
SEQS['guard'] = Seq([(i / 8, _guard(i / 8), 'l') for i in range(9)], n=8, fps=5, loop=True, rest=REST)

# ---- siper yürüyüşü (8 kare): vx 50 birim/sn'de 1x (devriye 0,35 x hız ... hücumcu kovalaması)
_T_WALK = 8 / 12.0
SEQS['walk'] = Seq([(i / 16, _walk(i / 16), 'l') for i in range(17)], n=8, fps=12, loop=True, rest=REST,
                   extra={'vx': round(20.0 / (0.6 * _T_WALK), 1)})

# ---- dönüş (4 kare, ~0,2 sn; yavaş döner): yeni yöne dönmüş gövde, kalkan henüz göğsün yanında (kenarı), ayaklar
# çaprazdan açılır, kalkan öne oturur
SEQS['turn'] = Seq([
    (0.0, dict(G, shield=0.0, af=(0.35, 1.3), srot=0.3, tw=-0.7, hx=-2.0, hy=2.4, lean=0.0, fb=(-3.0, 0.0, 0.3), ff=(-6.0, 2.5, 0.2),
               hd=(-1.6, 0.6), hr=-0.12, ab=(-0.2, 1.4), mace=-2.9, sk=1.2, plume=0.35), 'l'),
    (0.35, dict(G, shield=0.0, af=(0.7, 1.25), srot=0.15, tw=-0.35, hx=-0.8, hy=2.0, lean=0.08, fb=(-8.0, 0.0, 0.0), ff=(1.0, 2.0, 0.1),
                hd=(-0.4, 0.6), hr=0.0, sk=0.8, plume=0.14), 'o'),
    (0.7, dict(G, hy=1.8, sk=0.2, plume=-0.1), 'o'),
    (1.0, dict(G), 'io'),
], frames=[0.0, 0.33, 0.66, 1.0], fps=16, rest=REST)

# ---- dürtme "!" (hazırlık 0,28 / vuruş 0,25 / toparlanma 0,5): topuz kalçaya çekilir, ağırlık arka ayakta; ön adım + arka
# ayak itişi + omuz dönüşüyle düz topuz dürtmesi (uç ~48 birim), kalkan göğüste
J_COIL = dict(G, hx=-2.6, hy=2.6, lean=0.0, tw=-0.55, fb=(-13.5, 0.0, 0.0), ff=(5.5, 0.0, -0.15), af=(0.85, 1.25),
              ab=(-1.3, 2.9), mace=-1.75, mace_z=-12.0, hd=(-0.4, 0.8), hr=0.08, flare=0.35, jaw=0.2, sk=0.8, plume=0.17)
J_HIT = dict(G, hx=2.2, hy=3.0, lean=0.42, bend=0.12, tw=0.9, fb=(-15.0, 0.0, 0.75), ff=(11.5, 0.0, 0.0), af=(0.55, 1.4),
             ab=(1.5, 0.05), mace=1.62, mace_z=16.0, smear=0.0, hd=(1.8, 1.4), hr=0.12, flare=0.7, jaw=0.6, sk=-1.2, plume=-0.42)
SEQS['jab'] = Seq([
    (0.0, dict(G, hx=-1.0, hy=2.0, tw=-0.25, ab=(-1.2, 3.3), mace=-2.0, flare=0.2, sk=0.3), 'o'),
    (0.22, dict(J_COIL), 'o'),
    (0.36, dict(J_COIL, hx=0.5, lean=0.15, tw=-0.3, ff=(8.5, 1.8, -0.1), fb=(-13.5, 0.0, 0.3), sk=0.0), 'i'),
    (0.42, dict(J_HIT), 'i'),
    (0.55, dict(J_HIT, hx=2.4, lean=0.44, ab=(1.38, 0.2), mace=1.68, sk=-1.5, plume=-0.52), 'o'),
    (0.7, dict(G, hx=3.0, hy=2.6, lean=0.3, tw=0.4, fb=(-12.5, 0.0, 0.3), ff=(12.0, 0.0, 0.0), ab=(0.6, 1.2), mace=0.4, mace_z=-12.0,
               flare=0.3, sk=-0.6, plume=-0.21), 'o'),
    (0.85, dict(G, hx=1.0, hy=2.0, fb=(-12.5, 0.0, 0.0), ff=(8.0, 2.0, 0.0), ab=(-0.2, 1.6), mace=-2.0, sk=0.2), 'io'),
    (1.0, dict(G), 'o'),
], frames=[(0.0, 0.0), (0.36, 0.0), (0.42, 0.0), (0.55, 0.5), (0.7, 0.0), (0.85, 0.35), (1.0, 0.7)],
   seg=[('windup', 2), ('strike', 2), ('recover', 3)], lead={'windup': 0.05}, rest=REST, fps=10)

# ---- zırhlı dürtme hazırlığı "!!" (baskı altında): daha alçak, daha geniş; topuz daha geride, gözler alevli
SEQS['jab_aa'] = Seq([
    (0.0, dict(J_COIL, hx=-3.0, hy=6.2, lean=0.22, bend=0.15, fb=(-18.5, 0.0, 0.2), ff=(8.0, 0.0, -0.2), tw=-0.75, ab=(-1.55, 3.0),
               mace=-1.55, flare=1.0, jaw=0.7, hd=(0.2, 1.8), hr=0.16, sk=1.0, plume=0.24), 'o'),
    (1.0, dict(J_COIL, hx=1.5, hy=5.0, lean=0.35, bend=0.15, tw=-0.4, fb=(-18.0, 0.0, 0.6), ff=(11.5, 2.0, -0.1), ab=(-1.2, 2.6), mace=-1.9,
               flare=1.0, jaw=0.8, hd=(1.0, 1.6), hr=0.14, sk=0.2), 'i'),
], frames=[(0.0, 0.0), (1.0, 0.0)], seg=[('windup', 2)], lead={'windup': 0.05}, rest=REST, fps=10)

# ---- baş üstü ezme "!!" (hazırlık 0,75 / vuruş 0,45 / toparlanma 0,5): topuz yükselir, gövde geriye burulur, ön diz
# kalkar (DERİN KURULMA uzun tutulur); ön ayak yere vurur, kalça çöker, topuz başın üstünden yere iner (uç ~50 birim, yerde)
H_COIL = dict(G, hx=-3.4, hy=3.6, lean=-0.22, bend=-0.1, tw=-0.95, fb=(-12.0, 0.0, 0.0), ff=(1.5, 6.5, 0.3),
              af=(0.75, 1.35), ab=(-2.75, -0.55), mace=-1.45, mace_z=-12.0, hd=(-0.8, -0.4), hr=-0.12,
              flare=1.0, jaw=0.85, sk=1.2, plume=0.35, bob=-0.6)
H_HIT = dict(G, hx=4.2, hy=6.0, lean=0.62, bend=0.25, tw=0.95, fb=(-15.5, 0.0, 0.8), ff=(14.0, 0.0, 0.0), af=(0.4, 1.3),
             ab=(1.05, -0.05), mace=0.95, mace_z=16.0, smear=0.75, hd=(2.0, 2.6), hr=0.26, flare=1.0, jaw=1.0, sk=-1.6,
             plume=-0.63, crack=1.0, dust=0.7, dustx=1.0, bob=0.8)
SEQS['heavy'] = Seq([
    (0.0, dict(G, hx=-1.2, hy=2.4, lean=0.02, tw=-0.4, ab=(-1.6, 0.4), mace=-2.3, flare=0.5, jaw=0.4, sk=0.5, ff=(5.0, 0.0, -0.1)), 'o'),
    (0.14, dict(H_COIL, hy=3.0, lean=-0.12, ff=(3.5, 3.0, 0.15), ab=(-2.5, -0.35), mace=-1.9, tw=-0.75), 'o'),
    (0.3, dict(H_COIL), 'o'),
    (0.4, dict(H_COIL, hx=-3.0, hy=3.8, ff=(2.0, 7.0, 0.3), ab=(-2.8, -0.6), mace=-1.35, plume=0.32), 'io'),
    (0.47, dict(G, hx=3.0, hy=3.0, lean=0.25, tw=-0.1, fb=(-14.5, 0.0, 0.5), ff=(12.0, 1.5, -0.2), af=(0.6, 1.3),
                ab=(-2.9, 0.1), mace=-3.05, mace_z=-12.0, hd=(0.8, 0.6), hr=0.0, flare=1.0, jaw=1.0, sk=-0.6, plume=0.0), 'i'),
    (0.53, dict(H_HIT), 'i'),
    (0.64, dict(H_HIT, hx=7.0, hy=6.6, lean=0.68, bend=0.3, ab=(0.9, -0.05), mace=0.78, smear=0.0, crack=0.8, dust=1.0, plume=-0.7), 'o'),
    (0.78, dict(G, hx=4.0, hy=4.6, lean=0.45, tw=0.5, fb=(-14.0, 0.0, 0.4), ff=(14.0, 0.0, 0.0), ab=(0.6, 0.8), mace=0.9, mace_z=16.0,
                hd=(1.4, 1.8), hr=0.2, flare=0.4, jaw=0.4, sk=-0.6, plume=-0.21, crack=0.0), 'io'),
    (0.9, dict(G, hx=1.4, hy=2.6, lean=0.25, tw=0.0, fb=(-13.0, 0.0, 0.0), ff=(9.0, 2.0, 0.0), ab=(-0.6, 1.3), mace=-1.8,
               mace_z=-12.0, sk=0.4, plume=0.07), 'io'),
    (1.0, dict(G), 'o'),
], frames=[(0.0, 0.0), (0.14, 0.18), (0.3, 0.4), (0.47, 0.0), (0.53, 0.0), (0.64, 0.45), (0.78, 0.0), (0.9, 0.35), (1.0, 0.72)],
   seg=[('windup', 4), ('strike', 2), ('recover', 3)], lead={'windup': 0.05}, rest=REST, fps=10)

# ---- kalkan itişi "!" (hazırlık 0,4 / vuruş 0,3 / toparlanma 0,5): kalkan omza çekilir, çömelir; arka ayak iter, omuz
# kalkanın arkasına girer, kol düz: kalkan ~26 birim öne
B_COIL = dict(G, hx=-2.4, hy=3.4, lean=0.12, tw=-0.3, fb=(-14.0, 0.0, 0.0), ff=(4.5, 0.0, 0.0), shield=1.0, af=(0.55, 1.5),
              ab=(-0.7, 1.4), mace=-2.4, hd=(0.0, 1.2), hr=0.1, flare=0.35, jaw=0.3, sk=0.8, plume=0.14)
B_HIT = dict(G, hx=6.0, hy=3.4, lean=0.45, bend=0.1, tw=0.15, fb=(-14.5, 0.0, 0.8), ff=(14.5, 0.0, 0.0), shield=2.0,
             af=(1.55, -0.05), srot=-0.1, ab=(-1.0, 1.2), mace=-1.9, hd=(1.8, 1.8), hr=0.16, flare=0.6, jaw=0.6, sk=-1.4,
             plume=-0.49)
SEQS['bash'] = Seq([
    (0.0, dict(B_COIL), 'o'),
    (0.3, dict(B_COIL, hx=0.5, hy=3.0, lean=0.3, fb=(-14.0, 0.0, 0.45), ff=(8.5, 2.0, -0.1), af=(1.0, 0.9), sk=0.2), 'i'),
    (0.42, dict(B_HIT), 'i'),
    (0.58, dict(B_HIT, hx=6.6, lean=0.48, af=(1.5, 0.0), sk=-1.6, plume=-0.56), 'o'),
    (0.78, dict(G, hx=2.5, hy=2.4, lean=0.25, fb=(-12.5, 0.0, 0.2), ff=(11.0, 0.0, 0.0), af=(1.2, 0.6), shield=1.0, sk=-0.4,
                plume=-0.14), 'io'),
    (1.0, dict(G), 'o'),
], frames=[(0.0, 0.0), (0.3, 0.0), (0.42, 0.0), (0.58, 0.5), (0.78, 0.0), (1.0, 0.55)],
   seg=[('windup', 2), ('strike', 2), ('recover', 2)], lead={'windup': 0.05}, rest=REST, fps=10)

# ---- zırhlı kalkan hücumu (intikam "!!" 0,34 / rev 0,32): yere sinik, kalkan omuza yaslı, topuz havada; patlayan
# ileri atılış — kalkan ~30 birim önde, iki ayak da yerden kesilmek üzere
SEQS['bash_aa'] = Seq([
    (0.0, dict(B_COIL, hx=-3.4, hy=5.2, lean=0.3, bend=0.12, tw=-0.45, fb=(-16.5, 0.0, 0.0), ff=(5.5, 0.0, -0.2), af=(0.7, 1.35),
               ab=(-2.0, 0.3), mace=-2.9, flare=1.0, jaw=0.8, hd=(0.8, 2.6), hr=0.2, sk=1.0, plume=0.21), 'o'),
    (0.35, dict(B_COIL, hx=1.0, hy=4.4, lean=0.45, bend=0.12, tw=-0.2, fb=(-16.0, 0.0, 0.6), ff=(10.0, 2.4, -0.1), af=(1.1, 0.8),
                ab=(-1.8, 0.5), mace=-2.7, flare=1.0, jaw=0.9, hd=(1.4, 2.4), hr=0.2, sk=0.0, plume=-0.21), 'i'),
    (0.5, dict(B_HIT, hx=7.5, hy=4.0, lean=0.55, bend=0.15, fb=(-16.0, 0.8, 0.9), ff=(16.0, 0.0, 0.0), af=(1.58, -0.08),
               ab=(-1.5, 0.6), mace=-2.4, flare=1.0, jaw=1.0, sk=-1.8, plume=-0.7, dust=0.6), 'i'),
    (1.0, dict(B_HIT, hx=7.0, hy=3.6, lean=0.5, fb=(-15.0, 0.0, 0.6), ff=(16.0, 0.0, 0.0), af=(1.5, 0.0), ab=(-1.2, 0.9), mace=-2.1,
               flare=0.8, jaw=0.7, sk=-1.4, plume=-0.56, dust=0.9), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.0), (0.5, 0.0), (1.0, 0.5)], seg=[('windup', 2), ('rev', 2)], lead={'windup': 0.05},
   rest=REST, fps=10)

# ---- hücum hazırlığı "!!" (0,75; akıncı): ayaklar açılır ve toprağa gömülür, omuz alçalır, kalkan önde yükselir, topuz
# geride; DERİN KURULMA (toz, alevli gözler) — son karede ilk itiş
C_COIL = dict(G, hx=-2.0, hy=6.0, lean=0.45, bend=0.15, tw=-0.3, fb=(-17.0, 0.0, 0.35), ff=(7.0, 0.0, -0.1), shield=2.0,
              af=(1.35, 0.0), srot=-0.1, ab=(-1.2, 1.2), mace=-1.8, hd=(1.4, 3.2), hr=0.22, flare=1.0, jaw=0.6, sk=0.6,
              plume=0.0, dust=0.8, dustx=-1.0, bob=0.8)
SEQS['charge_windup'] = Seq([
    (0.0, dict(G, hx=-1.0, hy=2.6, lean=0.2, fb=(-14.5, 0.0, 0.0), ff=(6.0, 0.0, 0.0), af=(1.1, 0.8), flare=0.5, jaw=0.3, sk=0.4), 'o'),
    (0.25, dict(C_COIL, hy=4.6, lean=0.36, flare=0.8, dust=0.4), 'o'),
    (0.55, dict(C_COIL), 'io'),
    (1.0, dict(C_COIL, hx=3.5, hy=4.6, lean=0.55, fb=(-18.0, 0.0, 0.85), ff=(11.0, 3.5, -0.1), sk=-0.8, plume=-0.35, dust=1.0), 'i'),
], frames=[(0.0, 0.0), (0.25, 0.2), (0.55, 0.45), (1.0, 0.0)], seg=[('windup', 4)], lead={'windup': 0.05}, rest=REST, fps=10)

# ---- hücum (6 kare döngü, 400 birim/sn'de 1x): kalkan önde, omuz alçak, hız çizgisi + toz
_T_CH = 6 / 36.0
SEQS['charge'] = Seq([(i / 12, _charge(i / 12), 'l') for i in range(13)], n=6, fps=36, loop=True, rest=REST,
                     extra={'vx': round(25.0 / (0.38 * _T_CH), 1)})

# ---- kayarak duruş (hücum sonu toparlanma 0,7): ön ayak öne kazık, topuk toprağı yarar, gövde geriye yaslanır, toz
SEQS['skid'] = Seq([
    (0.0, dict(G, hx=-1.0, hy=5.0, lean=-0.12, tw=-0.2, fb=(-8.0, 0.0, 0.3), ff=(16.0, 0.0, -0.45), shield=2.0, af=(1.3, 0.1), srot=-0.05,
               ab=(-1.2, 1.3), mace=-1.4, hd=(-0.6, 1.4), hr=0.0, flare=0.5, jaw=0.5, sk=1.6, plume=0.56, dust=1.0, dustx=1.0, bob=0.6), 'o'),
    (0.4, dict(G, hx=1.0, hy=3.6, lean=0.0, fb=(-10.0, 0.0, 0.1), ff=(12.0, 0.0, -0.2), shield=1.0, af=(1.15, 0.7), ab=(-0.8, 1.5),
               mace=-2.2, hd=(0.0, 1.0), flare=0.3, jaw=0.3, sk=0.9, plume=0.28, dust=0.6, dustx=1.0), 'o'),
    (1.0, dict(G), 'io'),
], frames=[(0.0, 0.0), (0.4, 0.3), (1.0, 0.65)], seg=[('recover', 3)], rest=REST, fps=10)

# ---- hücum ortasında dönüş "!!" (0,4): kayıp dönmüş, çömelmiş; kalkanı yeniden kaldırır, itiş
SEQS['reset'] = Seq([
    (0.0, dict(G, hx=-2.0, hy=5.0, lean=0.05, tw=-0.6, fb=(-6.0, 0.0, 0.2), ff=(-1.0, 1.5, 0.2), shield=0.0, af=(0.6, 1.2), srot=0.3,
               ab=(-0.6, 1.4), mace=-2.4, hd=(-1.2, 1.6), hr=-0.05, flare=0.8, jaw=0.5, sk=1.8, plume=0.63, dust=1.0, dustx=1.0), 'o'),
    (0.45, dict(C_COIL, dust=0.6), 'o'),
    (1.0, dict(C_COIL, hx=3.5, hy=4.6, lean=0.55, fb=(-18.0, 0.0, 0.85), ff=(11.0, 3.5, -0.1), sk=-0.8, plume=-0.35, dust=1.0), 'i'),
], frames=[(0.0, 0.0), (0.45, 0.3), (1.0, 0.0)], seg=[('windup', 3)], lead={'windup': 0.05}, rest=REST, fps=10)

# ---- sendeleme (kalkan düştü / duvara çarptı; st 1,4-1,6; 6 kare): kalkan kolu geniş savrulur, baş geri, iki geri adım,
# dizler titrer, sonra kalkanı toparlar
ST_OPEN = dict(G, hx=-3.0, hy=3.0, lean=-0.32, bend=-0.15, tw=-0.4, fb=(-14.0, 0.0, 0.0), ff=(1.0, 4.5, -0.3), shield=0.0,
               af=(-0.9, -0.5), srot=0.9, ab=(1.0, 0.4), mace=1.0, hd=(-1.6, 0.0), hr=-0.35, jaw=1.0, flare=0.0, sk=1.6,
               plume=0.63, bob=-0.4)
SEQS['stagger'] = Seq([
    (0.0, dict(ST_OPEN), 'o'),
    (0.12, dict(ST_OPEN, hx=-4.0, hy=4.0, lean=-0.25, fb=(-15.0, 2.0, 0.4), ff=(-2.0, 0.0, 0.0), af=(-1.1, -0.3), hr=-0.3, sk=1.2), 'o'),
    (0.3, dict(ST_OPEN, hx=-1.0, hy=5.0, lean=0.1, bend=0.1, tw=-0.2, fb=(-13.0, 0.0, 0.0), ff=(2.0, 0.0, 0.0), af=(-0.2, 0.6),
               srot=0.6, ab=(0.4, 0.3), mace=0.85, hd=(0.4, 2.4), hr=0.25, jaw=0.7, sk=0.4, plume=-0.21), 'io'),
    (0.5, dict(ST_OPEN, hx=1.0, hy=5.6, lean=0.25, bend=0.15, tw=0.0, fb=(-12.0, 0.0, 0.0), ff=(3.0, 0.0, 0.0), af=(0.3, 0.6),
               srot=0.5, ab=(0.25, 0.3), mace=0.8, hd=(1.0, 3.2), hr=0.4, jaw=0.6, sk=-0.3, plume=-0.35), 'io'),
    (0.72, dict(G, hx=-0.5, hy=4.0, lean=0.12, shield=0.0, af=(0.5, 0.9), srot=0.35, ab=(0.0, 0.8), mace=-0.6, hd=(0.0, 2.0),
                hr=0.2, jaw=0.4, sk=0.3, plume=0.0), 'io'),
    (1.0, dict(G, hy=2.2), 'o'),
], frames=[(0.0, 0.0), (0.12, 0.08), (0.3, 0.22), (0.5, 0.42), (0.72, 0.68), (1.0, 0.88)], seg=[('stagger', 6)], rest=REST, fps=8)

# ---- hafif sarsılma (3 kare, 0,22 sn): kalkanın arkasına sinip geri sarsılır, baş eğilir
SEQS['hurt'] = Seq([
    (0.0, dict(G, hx=-2.8, hy=2.6, lean=-0.1, tw=-0.25, af=(0.85, 1.25), ab=(-0.1, 1.2), mace=-2.2, hd=(-1.4, 1.2), hr=-0.2,
               jaw=0.8, sk=1.2, plume=0.42, bob=-0.5), 'o'),
    (0.5, dict(G, hx=-1.4, hy=2.2, lean=0.05, hd=(-0.4, 0.8), hr=-0.05, jaw=0.4, sk=0.6, plume=0.14), 'o'),
    (1.0, dict(G), 'o'),
], frames=[(0.0, 0.0), (0.5, 0.35), (1.0, 0.7)], rest=REST, fps=12)

# ---- ağır sendeleme (4 kare, 0,45 sn): kalkan yana açılır, gövde geriye bükülür, ön ayak kalkar, geri adım
SEQS['hurt_big'] = Seq([
    (0.0, dict(ST_OPEN, hx=-4.0, hy=2.4, lean=-0.36, af=(-1.0, -0.3), srot=0.8), 'o'),
    (0.35, dict(ST_OPEN, hx=-3.0, hy=4.0, lean=-0.15, fb=(-15.0, 0.0, 0.0), ff=(0.0, 0.0, 0.0), af=(-0.5, 0.3), srot=0.6,
                hd=(-0.6, 1.4), hr=-0.1, jaw=0.7, sk=1.0, plume=0.28), 'io'),
    (0.7, dict(G, hx=-1.4, hy=3.4, lean=0.1, shield=1.0, af=(0.85, 1.2), hd=(0.0, 1.4), hr=0.1, jaw=0.4, sk=0.5, plume=-0.07), 'o'),
    (1.0, dict(G), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.25), (0.7, 0.55), (1.0, 0.8)], rest=REST, fps=10)


# ---- duruş kırık / sersem (6 kare döngü): kalkan aşağıda sürünür, topuz sarkık, baş sallanır, dizler titrer
def _stun(t):
    s = math.sin(t * math.tau)
    c = math.cos(t * math.tau)
    return dict(G, hx=1.2 * s, hy=4.2 + 0.6 * c, lean=0.22 + 0.05 * c, bend=0.2, tw=0.1 * s, roll=0.03 * s,
                fb=(-11.0 + 0.8 * c, 0.0, 0.0), ff=(4.0 + 0.6 * s, 0.6 * max(0.0, s), 0.0), shield=0.0, af=(0.45, 0.25 + 0.1 * s), srot=0.15,
                ab=(0.12, 0.2), mace=0.95 + 0.08 * s, hd=(0.6 * s, 3.4 + 0.6 * c), hr=0.42 + 0.1 * s, jaw=0.7, flare=0.0,
                ph=t * math.tau, sk=0.6 * s, plume=0.35 * s - 0.25)


SEQS['stun'] = Seq([(i / 12, _stun(i / 12), 'l') for i in range(13)], n=6, fps=6, loop=True, rest=REST)

# ---- havaya savrulma (dikey hız evresi; 4 kare): geriye devrilir, kalkan ve topuz savrulur, bacaklar toplanır
SEQS['launch'] = Seq([
    (0.0, dict(ST_OPEN, y=-4.0, roll=-0.25, hy=0.0, fb=(-13.0, 4.0, 0.4), ff=(2.0, 7.0, 0.2), af=(-1.4, -0.3), ab=(1.6, 0.4), mace=1.6), 'o'),
    (0.4, dict(ST_OPEN, y=-6.0, roll=-0.55, hy=-1.0, lean=-0.2, fb=(-10.0, 9.0, 0.3), ff=(4.0, 11.0, 0.2), af=(-1.8, 0.2), ab=(2.2, 0.3),
               mace=2.4, hd=(-1.0, 0.6), hr=-0.3, sk=2.0, plume=0.84), 'io'),
    (0.7, dict(ST_OPEN, y=-5.0, roll=-0.4, hy=0.0, lean=-0.05, fb=(-14.0, 7.0, 0.2), ff=(6.0, 6.0, 0.0), af=(-0.6, 0.6), ab=(1.2, 0.4),
               mace=1.2, hd=(-0.4, 1.0), hr=-0.1, sk=1.0, plume=0.56), 'io'),
    (1.0, dict(ST_OPEN, y=-2.0, roll=-0.15, hy=1.0, lean=0.1, fb=(-14.0, 3.0, 0.1), ff=(6.0, 2.0, 0.0), af=(0.2, 0.8), ab=(0.6, 0.6),
               mace=0.6, hd=(0.4, 1.4), hr=0.1, jaw=0.6, sk=0.4, plume=0.21), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.25), (0.65, 0.55), (1.0, 0.82)], seg=[('air', 4)], rest=REST, fps=10)

# ---- kalkış (4 kare, 0,5 sn): dizden, kalkana dayanarak doğrulur
SEQS['getup'] = Seq([
    (0.0, dict(G, hx=-1.0, hy=10.0, lean=0.45, bend=0.25, fb=(-14.0, 0.0, 0.9), ff=(6.0, 0.0, 0.0), shield=1.0, af=(0.85, 0.7),
               ab=(0.2, 0.3), mace=1.25, hd=(1.0, 3.0), hr=0.35, jaw=0.6, sk=0.6, plume=-0.28), 'o'),
    (0.35, dict(G, hx=0.0, hy=6.0, lean=0.35, bend=0.15, fb=(-13.0, 0.0, 0.5), ff=(5.5, 0.0, 0.0), af=(0.7, 0.8), ab=(-0.2, 1.0),
                mace=-1.2, hd=(0.8, 2.0), hr=0.2, jaw=0.4, sk=0.4), 'o'),
    (0.65, dict(G, hy=2.6, lean=0.2, hd=(0.3, 0.8), hr=0.08, sk=-0.3, plume=0.21), 'io'),
    (1.0, dict(G), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.3), (0.65, 0.6), (1.0, 0.85)], rest=REST, fps=10)

# ---- ölüm (8 kare, 0,9 sn): darbeyle geri sarsılır, dizleri çözülür ve dizüstü çöker, kalkan kolundan kayıp düşer,
# topuz elden bırakılır, yüzüstü yere kapanır
SEQS['death'] = Seq([
    (0.0, dict(ST_OPEN, hx=-3.0, lean=-0.35, af=(-0.6, -0.2), jaw=1.0, flare=1.0), 'o'),
    (0.14, dict(ST_OPEN, hx=-2.0, hy=6.0, lean=-0.1, fb=(-13.0, 0.0, 0.3), ff=(2.0, 0.0, 0.0), af=(-0.2, 0.3), srot=0.5,
                ab=(0.5, 0.3), mace=0.6, hd=(-0.4, 1.4), hr=0.0, jaw=0.9, flare=0.6, sk=0.8), 'o'),
    (0.3, dict(G, hx=-1.0, hy=11.3, lean=0.15, bend=0.15, fb=(-21.0, 0.0, 1.25), ff=(3.0, 0.0, 0.0), shield=0.0, af=(0.8, 0.5), srot=0.2,
               ab=(0.35, 0.3), mace=1.35, hd=(0.6, 2.6), hr=0.35, jaw=0.9, flare=0.3, sk=0.5, plume=-0.28), 'i2'),
    (0.45, dict(G, hx=0.0, hy=12.3, lean=0.3, bend=0.2, fb=(-21.0, 0.0, 1.35), ff=(3.0, 0.0, 0.0), sfree=(15.0, -7.5, 0.55, 0.45),
                af=(0.1, 0.2), ab=(0.0, 0.2), mfree=(-15.0, -2.2, -1.45), hd=(1.0, 3.6), hr=0.5, jaw=0.7, flare=0.1, sk=0.3, plume=-0.3), 'o'),
    (0.6, dict(G, hx=0.5, hy=12.8, lean=0.6, bend=0.3, fb=(-21.5, 0.0, 1.4), ff=(3.0, 0.0, 0.0), sfree=(16.0, -2.4, 1.45, 0.35),
               af=(1.0, 0.3), ab=(0.2, 0.2), mfree=(-16.0, -1.3, -1.57), hd=(1.4, 4.4), hr=0.6, jaw=0.6, flare=0.0, plume=-0.5), 'i'),
    (0.75, dict(G, x=6.0, y=4.8, roll=0.95, hx=0.5, hy=12.0, lean=0.4, bend=0.25, fb=(-22.0, 2.0, 1.5), ff=(-17.0, 2.0, 1.5),
                sfree=(16.0, -3.0, 1.55, 0.32), af=(0.15, 0.3), ab=(0.3, 0.3), mfree=(-16.0, -1.3, -1.57), hd=(1.4, 3.0), hr=0.4,
                jaw=0.8, plume=-0.9), 'i'),
    (0.88, dict(G, x=11.0, y=10.4, roll=1.42, hx=0.5, hy=8.0, lean=0.2, bend=0.1, fb=(-30.0, 2.0, 1.5), ff=(-26.0, 2.0, 1.5),
                sfree=(16.0, -3.0, 1.57, 0.3), af=(0.5, 0.3), ab=(0.4, 0.2), mfree=(-16.0, -1.3, -1.57), hd=(1.0, 2.0), hr=0.2,
                jaw=0.4, plume=-0.7, dust=0.6, dustx=1.0), 'i'),
    (1.0, dict(G, x=11.5, y=10.8, roll=1.5, hx=0.5, hy=8.0, lean=0.15, bend=0.05, fb=(-30.0, 2.0, 1.5), ff=(-27.0, 2.0, 1.5),
               sfree=(16.0, -3.0, 1.57, 0.3), af=(0.4, 0.2), ab=(0.3, 0.15), mfree=(-16.0, -1.3, -1.57), hd=(1.0, 2.0), hr=0.15,
               jaw=0.3, plume=-0.5), 'o'),
], frames=[(0.0, 0.0), (0.14, 0.1), (0.3, 0.22), (0.45, 0.34), (0.6, 0.47), (0.75, 0.6), (0.88, 0.72), (1.0, 0.86)], rest=REST, fps=10)

# ---- savaş narası (seçkin; 5 kare, 0,8 sn): topuzu kalkanın kasnağına vurur, başını kaldırıp gözleri alevlenir
SEQS['roar'] = Seq([
    (0.0, dict(G), 'io'),
    (0.25, dict(G, hx=-1.5, hy=2.6, lean=-0.05, tw=-0.4, ab=(-2.4, -0.3), mace=-2.0, af=(0.9, 1.2), hd=(-0.6, 0.0), hr=-0.15,
                flare=0.6, jaw=0.4, sk=0.6), 'o'),
    (0.45, dict(G, hx=1.5, hy=3.4, lean=0.25, tw=0.5, ab=(0.9, 0.6), mace=1.0, mace_z=16.0, af=(0.95, 1.15), hd=(0.8, 1.2), hr=0.1,
                flare=1.0, jaw=0.6, sk=-0.6, plume=-0.28), 'i'),
    (0.75, dict(G, hx=-0.5, hy=2.0, lean=-0.12, tw=0.2, ab=(0.4, 0.9), mace=0.2, mace_z=16.0, af=(0.8, 1.2), hd=(-1.0, -1.2), hr=-0.45,
                flare=1.0, jaw=1.2, sk=0.3, plume=0.28), 'o'),
    (1.0, dict(G), 'io'),
], frames=[0.0, 0.25, 0.45, 0.75, 1.0], fps=8, rest=REST)

DURUM = {
    # ---- tepkiler
    '_hurt': {'a': 'hurt', 'u': 'up', 'd': 0.22},
    '_hurt_big': {'a': 'hurt_big', 'u': 'up', 'd': 0.45},
    '_break': {'a': 'stun', 'u': 'loop'},
    '_launch': {'a': 'launch', 'u': 'vy'},
    '_getup': {'a': 'getup', 'u': 'up', 'd': 0.5},
    '_death': {'a': 'death', 'u': 'up', 'd': 0.9},
    '_turn': {'a': 'turn', 'u': 'up', 'd': 0.2},
    '_roar': {'a': 'roar', 'u': 'up', 'd': 0.8},
    # ---- kalkanlı bekçi (shield): dürtme / baş üstü ezme / kalkan itişi; intikam kalkan hücumu
    'windup/jab': {'a': 'jab', 's': 'windup', 'u': 'st'},
    'windup/jab!!': {'a': 'jab_aa', 's': 'windup', 'u': 'st'},
    'strike/jab': {'a': 'jab', 's': 'strike', 'u': 'st'},
    'recover/jab': {'a': 'jab', 's': 'recover', 'u': 'st'},
    'windup/heavy!!': {'a': 'heavy', 's': 'windup', 'u': 'st'},
    'windup/heavy': {'a': 'heavy', 's': 'windup', 'u': 'st'},
    'strike/heavy': {'a': 'heavy', 's': 'strike', 'u': 'st'},
    'recover/heavy': {'a': 'heavy', 's': 'recover', 'u': 'st'},
    'windup/bash': {'a': 'bash', 's': 'windup', 'u': 'st'},
    'windup/bash!!': {'a': 'bash_aa', 's': 'windup', 'u': 'st'},
    'strike/bash': {'a': 'bash', 's': 'strike', 'u': 'st'},
    'rev/bash': {'a': 'bash_aa', 's': 'rev', 'u': 'st'},
    'rev': {'a': 'bash_aa', 's': 'rev', 'u': 'st'},
    'recover/bash': {'a': 'bash', 's': 'recover', 'u': 'st'},
    'windup!!': {'a': 'jab_aa', 's': 'windup', 'u': 'st'},
    'windup': {'a': 'jab', 's': 'windup', 'u': 'st'},
    'strike': {'a': 'jab', 's': 'strike', 'u': 'st'},
    'recover': {'a': 'jab', 's': 'recover', 'u': 'st'},
    'stagger': {'a': 'stagger', 's': 'stagger', 'u': 'st'},
    # ---- kalkanlı akıncı (charger): hücum / yakın kalkan darbesi
    'charge>windup': {'a': 'reset', 's': 'windup', 'u': 'st'},
    'charger:windup/charge!!': {'a': 'charge_windup', 's': 'windup', 'u': 'st'},
    'charger:windup/charge': {'a': 'charge_windup', 's': 'windup', 'u': 'st'},
    'charger:windup!!': {'a': 'charge_windup', 's': 'windup', 'u': 'st'},
    'charger:charge': {'a': 'charge', 'u': 'loop'},
    'charger:recover/charge': {'a': 'skid', 's': 'recover', 'u': 'st'},
    'charger:windup/bash': {'a': 'bash', 's': 'windup', 'u': 'st'},
    'charger:strike/bash': {'a': 'bash', 's': 'strike', 'u': 'st'},
    'charger:recover/bash': {'a': 'bash', 's': 'recover', 'u': 'st'},
    'charger:recover': {'a': 'skid', 's': 'recover', 'u': 'st'},
}


def render_frame(anim, i, ss=3):
    seq = SEQS[anim]
    p = seq.pose(i)
    p = _secondary(seq, i, p)
    cv = ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info


def _secondary(seq, i, p):
    """İkincil hareket: sorguç ve etek, gövdenin bir önceki andaki konumuna göre gecikir (ataletle geride kalır)."""
    rt = seq.frames[i][0]
    dt = 0.08
    t0 = rt - dt
    if not seq.loop and t0 < 0.0:
        return p
    q0 = seq.q(t0)
    r = dict(REST)
    r.update(p)
    o = dict(REST)
    o.update(q0)

    def hx_(d):
        return d['hx'] + d['x'] + math.sin(d['lean']) * 30.0 + d['hd'][0]

    def hy_(d):
        return d['hy'] + d['y'] + d['hd'][1]
    vx = hx_(r) - hx_(o)
    vy = hy_(r) - hy_(o)
    p = dict(p)
    p['plume'] = r['plume'] + max(-0.5, min(0.5, -vx * 0.05 + vy * 0.05))
    p['sk'] = r['sk'] - max(-1.0, min(1.0, (r['hx'] + r['x'] - o['hx'] - o['x']) * 0.15))
    return p
