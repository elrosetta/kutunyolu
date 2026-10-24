"""v43 yeni Bengü — "Tan Bekçisi" (mürekkep-cel; bkz. docs/TASARIM.md "v43: yeni Bengü").

Karakter tasarımı: Gün Ana'nın şafak ateşini bekleyen bozkır savaşçısı kadın. Silüetin üç ikonu:
  1. kurt postu başlık: zırh başlık değil, başın üstüne yumuşakça oturan gerçek post (burun alnın önünde, dik kulaklar
     uçları koyu), sırtta kürek kemiğine inen post kuyruğu ve YALNIZCA ön omuzda pençeli post (asimetrik omuz),
  2. uzun tek örgü (oyunda fizikli; şolpı gümüş pullarıyla, BenguSac.gd),
  3. önü kavuşturmalı, bel kemeriyle sıkılmış, yırtmaçlı uzun kaftan (arka etekler oyunda kumaş şerit: BenguKusak.gd).
Zarafet = sadelik: iri zırh plakaları, dizlik, lamel yelek ve kocaman çizme kaldırıldı; ince ve uzun uzuvlar (eklemler
KESİNTİSİZ tek kontur: diz / dirsek yuvarlak büküm, kapsül tümsekleri yok), görünür boyun, küçük baş (~7,5 baş boy).
Renk: soğuk dünyada sıcak kahraman — paletin tek baskın rengi + tek vurgu (PALETLER; 'tan' seçildi).

İskelet, kemik boyları, pozlar ve çapalar bengu_ink / bengu_govde ile aynı (Player.SWINGS, vuruş kutuları, saç ve kuşak
çapaları değişmez); bu modül yalnızca ÇİZİMİ değiştirir: bengu_ink.draw / render_arm_parts yerine geçer (install()).
Yeni çapa: 'etek' (kaftanın arka etek kökü, oyunda kumaş şeritler buradan sarkar).
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink
import bengu_ink as b
from rig import fk_leg, fk_arm, lerp2
from bengu import P

TEX = b.TEX
L_THIGH, L_SHIN, L_UP, L_FORE = b.L_THIGH, b.L_SHIN, b.L_UP, b.L_FORE
HIP_Y, TORSO, AXK = b.HIP_Y, b.TORSO, b.AXK
HEAD_K = 0.8          # baş + başlık (v39 0,9): ~7,5 baş boy, zarif
WAIST_K = 0.86        # gövde yanal ölçeği (ince bel)

# ------------------------------------------------------------ paletler (konsept: üç yön, biri seçilir)
PALETLER = {
    # A "Tan Kızılı": kök boya kızılı kaftan, safran sırma ve kuşak, kemik beyazı post — şafak ateşi
    'tan': dict(
        kaftan=('#8e2834', '#44142e', '#c4544a', '#220a1a'), astar=('#d79a3e', '#7c4a22', '#f2c870'),
        sirma=('#e2ae4c', '#86531f', '#fae2a4'), pant=('#2c3150', '#151830', '#4a5278', '#0c0e1e'),
        boot=('#4a2a26', '#1f1114', '#77493c'), kusak=('#e0a53e', '#8a4f1c', '#f8d888', '#4a240e'),
        fur=('#ece6d8', '#a29aac', '#fffaf0', '#625a72'), plak=('#a8aab4', '#4e5262', '#e8ecf4'),
        deri=('#4a2a22', '#25120e', '#86563c')),
    # B "Şafak Çivit": gece çividi kaftan, kızıl astar, safran güneş nakışı
    'safak': dict(
        kaftan=('#2e3866', '#141a38', '#56649c', '#0a0d22'), astar=('#a8303a', '#521630', '#d65c50'),
        sirma=('#e2ae4c', '#86531f', '#fae2a4'), pant=('#3a2a3a', '#1c121e', '#5c4658', '#0e0910'),
        boot=('#7a4a2e', '#33191a', '#a8744e'), kusak=('#b8323c', '#56142c', '#e6685a', '#2a0a18'),
        fur=('#e4e0d6', '#7e86a4', '#faf8f2', '#535c7e'), plak=('#b9c0cc', '#5c6478', '#f2f6fc'),
        deri=('#4a2c24', '#1f100e', '#76503c')),
    # C "Kül Keçe": boyasız keçe kaftan, kara-kızıl tamga bordürü, boz kurt postu
    'kul': dict(
        kaftan=('#d6c8aa', '#7c7088', '#f4ead2', '#4a4058'), astar=('#2a2430', '#141018', '#4a4250'),
        sirma=('#9e2a34', '#4a1228', '#d0584a'), pant=('#3a3c46', '#1a1b24', '#5c5e6c', '#0e0e14'),
        boot=('#2e2428', '#141014', '#544448'), kusak=('#b02e38', '#521430', '#e0604e', '#280a18'),
        fur=('#a4a8b6', '#565e7c', '#d4d8e2', '#3c4460'), plak=('#c9a454', '#76501e', '#f4dca0'),
        deri=('#3a2620', '#1a0f0c', '#62443a')),
}
SECIM = 'tan'
# palet başına biçim düğmeleri (konsept yönleri): ön etek boyu, pelerin boyu
BICIM = {'tan': (1.0, 1.0), 'safak': (0.72, 0.6), 'kul': (1.25, 1.25)}


def _ink(t, kind='cloth', name=''):
    return Ink(*t, kind=kind, name=name)


def palet(ad):
    """Modül malzemelerini seçili palete bağla."""
    global KAFTAN, KAFTAN_B, ASTAR, SIRMA, PANT, PANT_B, BOOT, BOOT_B, KUSAK, FUR, FUR_B, PLAK, DERI, PAL
    PAL = ad
    d = PALETLER[ad]
    KAFTAN = _ink(d['kaftan'], name='kaftan')
    KAFTAN_B = KAFTAN.darker(0.74)
    ASTAR = _ink(d['astar'], name='astar')
    SIRMA = _ink(d['sirma'], kind='metal', name='sırma')
    PANT = _ink(d['pant'], name='şalvar')
    PANT_B = PANT.darker(0.72)
    BOOT = _ink(d['boot'], name='keçe çizme')
    BOOT_B = BOOT.darker(0.72)
    KUSAK = _ink(d['kusak'], name='kuşak')
    FUR = _ink(d['fur'], kind='fur', name='post')
    FUR_B = FUR.darker(0.8)
    PLAK = _ink(d['plak'], kind='metal', name='kemer plakası')
    DERI = _ink(d['deri'], name='deri')


palet(SECIM)
SKIN = b.SKIN
PELT = b.PELT
HAIR = b.HAIR
GOLD = b.GOLD
NOSE = b.NOSE
TOOTH = b.TOOTH
EAR_IN = b.EAR_IN
SOLE = b.SOLE
PAINT = (0.74, 0.14, 0.17)
KOR = b.KOR
GUN = (1.0, 0.74, 0.34)           # güneş tamgası ışıması (sırtta, hafif)
EYE_DARK = (0.12, 0.08, 0.1)


def _T(hip, ax, pe):
    def f(u, v, *k):
        return (hip[0] + ax[0] * u + pe[0] * v, hip[1] + ax[1] * u + pe[1] * v) + tuple(k)
    return f


along = b.along


def _interp(ctrl):
    """[(s, değer)] denetim noktalarından yumuşak (smoothstep) aradeğerleme."""
    def f(s):
        if s <= ctrl[0][0]:
            return ctrl[0][1]
        for (s0, v0), (s1, v1) in zip(ctrl, ctrl[1:]):
            if s <= s1:
                t = (s - s0) / max(1e-6, s1 - s0)
                t = t * t * (3 - 2 * t)
                return v0 + (v1 - v0) * t
        return ctrl[-1][1]
    return f


def soft_limb(cv, pts, ctrl):
    """Kesintisiz uzuv: Catmull-Rom omurga (eklemde yuvarlak büküm) + uzunluk boyunca yumuşak en profili.
    ctrl: [(s 0..1, çap dünya birimi)]. Kapsül birleşimindeki eklem tümsekleri / kırık kontur yok."""
    q = [cv.W(p) for p in pts]
    f = _interp(ctrl)
    mx = max(v for _, v in ctrl)
    return ik.taper_path(q, cv.u(mx), prof=lambda s: f(s) / mx)


def _spine(a, k, c, n=2):
    """Eklem noktası k'yi (diz / dirsek) çevreleyen ara noktalar: Catmull-Rom'un eklemde yuvarlak dönmesi için."""
    return [a, lerp2(a, k, 0.5), lerp2(a, k, 0.86), k, lerp2(k, c, 0.14), lerp2(k, c, 0.5), c]


# ------------------------------------------------------------ bacak
def _leg(cv, hip, a, z, near, pitch=0.0):
    k, f = fk_leg(hip, a[0], a[1], L_THIGH, L_SHIN)
    cp_, sp_ = math.cos(pitch), math.sin(pitch)

    def R(q):
        dx, dy = q[0] - f[0], q[1] - f[1]
        return (f[0] + dx * cp_ - dy * sp_, f[1] + dx * sp_ + dy * cp_) + tuple(q[2:])
    pm = PANT if near else PANT_B
    bm = BOOT if near else BOOT_B
    bend = max(0.0, min(1.0, a[1] / 2.2))
    # uyluk -> diz -> baldır tek kontur: kalçada dolgun, dizde incelir (büküldükçe diz kapağı dolgunlaşır), baldır kası
    spine = _spine(hip, k, f)
    leg = soft_limb(cv, spine, [(0.0, 5.0), (0.2, 4.6), (0.42, 3.6 + 0.4 * bend), (0.5, 3.3 + 0.5 * bend),
                                (0.62, 3.5), (0.75, 2.9), (1.0, 2.3)])
    n, d = b._perp(k, f)
    det = []
    if near:
        # diz büküm kıvrımları (arka yanda kumaş toplanır) + uyluk boyunca tek uzun kıvrım: çok çizgi değil, öz
        det += cv.fold([along(hip, k, 0.3, -1.2), along(hip, k, 0.62, -0.4), along(hip, k, 0.9, 0.6)], 0.5, 1.0, 1, (0.5, 0.2))
        det += cv.fold([along(k, f, -0.04, -1.4), along(k, f, 0.06, -0.6)], 0.35 + 0.4 * bend, 1.0, 1, (0.2, 0.6))
        det.append(('ink', [along(hip, k, 0.95, 1.5), along(k, f, 0.08, 1.5)], 0.9, (0.6, 0.6)))
    cv.shape(leg, pm, z=z, sd=1.9 if near else 2.6, details=det, hatch=0.35 if near else 0.0, bounce=0.3 if near else 0.0)
    # keçe çizme: baldırın üçte birinden (diz altı) ayağa; ağzı biraz bol, sırma bantlı; burnu hafif kalkık (bozkır çizmesi)
    bt = lerp2(k, f, 0.3)
    toe = R((f[0] + 4.3, f[1] + 0.2))
    tip = R((f[0] + 5.0, f[1] - 0.7, 0.0))
    heel = R((f[0] - 1.9, f[1] + 1.1))
    shaft = soft_limb(cv, [along(k, f, 0.26), lerp2(bt, f, 0.5), f], [(0.0, 3.5), (0.2, 3.3), (0.7, 2.55), (1.0, 2.5)])
    foot = cv.blob([R((f[0] - 1.9, f[1] - 1.2)), R((f[0] + 1.0, f[1] - 1.5)), R((f[0] + 3.0, f[1] - 0.6)), tip,
                    R((f[0] + 4.6, f[1] + 0.5)), toe, R((f[0] + 1.0, f[1] + 1.25, 0.0)), (heel[0] + 0.1, heel[1] + 0.2, 0.0),
                    R((f[0] - 2.3, f[1] - 0.2))])
    boot = ik.union(shaft, foot)
    bdet = []
    if near:
        bdet.append(('ink', [along(k, f, 0.55, -1.2), along(k, f, 0.66, -0.2)], 0.9, (0.3, 0.5)))
        bdet.append(('stroke', [along(bt, f, 0.15, 1.1), along(bt, f, 0.7, 1.0)], 0.8, BOOT.hi, (0.4, 0.4)))
    cv.shape(boot, bm, z=z + 0.4, details=bdet, sd=1.3, hi=0.3 if near else 0.0)
    cuff = ik.isect(boot, cv.poly([along(k, f, 0.24, -3.0), along(k, f, 0.24, 3.0), along(k, f, 0.33, 3.0), along(k, f, 0.33, -3.0)]))
    cv.shape(cuff, SIRMA if near else SIRMA.darker(0.7), z=z + 0.45, sd=0.6, hi=0.2 if near else 0.0, ol=0.6, spec=0.5)
    sole = cv.blob([(heel[0] - 0.3, heel[1] - 0.15), toe, (toe[0] - 0.2, toe[1] + 0.7, 0.0), (heel[0], heel[1] + 0.8, 0.0)])
    cv.shape(sole, SOLE, z=z + 0.5, flat=True, ol=0.7)
    return k, f


# ------------------------------------------------------------ kol (tek kontur: omuz -> dirsek -> bilek; kumaş kol, deri siper)
AW = 1.0


def arm_shapes(cv, sh, e, h, z, near=True, sleeve_k=1.0):
    km = KAFTAN if near else KAFTAN_B
    bend = 0.0
    a1 = math.atan2(e[0] - sh[0], e[1] - sh[1])
    a2 = math.atan2(h[0] - e[0], h[1] - e[1])
    bend = min(1.0, abs((a2 - a1 + math.pi) % (2 * math.pi) - math.pi) / 2.0)
    spine = _spine(sh, e, h)
    # omuz yuvarlak (deltoid), üst kol incelir, dirsekte kumaş, ön kol kası, bilekte ince
    arm = soft_limb(cv, spine, [(0.0, 3.5), (0.12, 3.2), (0.36, 2.7), (0.5, 2.55 + 0.25 * bend), (0.62, 2.7),
                                (0.82, 2.2), (1.0, 1.75)])
    arm = ik.union(arm, cv.ellipse(sh, 1.85, 1.85))
    det = []
    if near:
        # dirsek içinde toplanan kumaş (bükülünce belirginleşir) + omuzdan inen tek kıvrım
        det += cv.fold([along(sh, e, 0.72, -1.2), along(sh, e, 0.88, -0.5), along(e, h, 0.06, -0.2)], 0.3 + 0.35 * bend, 0.9, 1, (0.2, 0.6))
        det += cv.fold([along(sh, e, 0.2, 1.3), along(sh, e, 0.5, 0.9)], 0.35, 0.8, -1, (0.3, 0.5))
    cv.shape(arm, km, z=z, sd=1.7, details=det, bounce=0.3 if near else 0.0)
    # deri bilek siperi (ön kolun yarısından bileğe) + sırma kol ağzı
    br = ik.isect(arm, cv.poly([along(e, h, 0.5, -3), along(e, h, 0.5, 3), along(e, h, 1.2, 3), along(e, h, 1.2, -3)]))
    bdet = []
    if near:
        bdet.append(('ink', [along(e, h, 0.66, -1.0), along(e, h, 0.7, 1.0)], 0.7, (0.2, 0.2)))
        bdet.append(('ink', [along(e, h, 0.82, -1.0), along(e, h, 0.86, 1.0)], 0.7, (0.2, 0.2)))
        bdet.append(('stroke', [along(e, h, 0.58, 0.8), along(e, h, 0.92, 0.6)], 0.7, DERI.hi, (0.3, 0.3)))
    cv.shape(br, DERI if near else DERI.darker(0.75), z=z + 0.1, sd=0.9, hi=0.25 if near else 0.0, details=bdet)
    cuff = ik.isect(arm, cv.poly([along(e, h, 0.44, -3), along(e, h, 0.44, 3), along(e, h, 0.52, 3), along(e, h, 0.52, -3)]))
    cv.shape(cuff, SIRMA if near else SIRMA.darker(0.7), z=z + 0.15, sd=0.5, hi=0.2 if near else 0.0, ol=0.6, spec=0.5)


def fist(cv, e, h, z, near=True):
    """İnce deri eldivenli yumruk (küçük; boğumlar + sarılı başparmak)."""
    gm = DERI if near else DERI.darker(0.75)
    k_ = 0.74
    cv.push(lambda q, c0=h: (c0[0] + (q[0] - c0[0]) * k_, c0[1] + (q[1] - c0[1]) * k_))
    al = lambda t, o: along(e, h, t, o)
    body = cv.blob([al(0.86, -2.0), al(0.86, 1.9), al(0.97, 2.6), al(1.1, 2.6), al(1.2, 2.1), al(1.25, 0.5),
                    al(1.24, -1.3), al(1.14, -2.3), al(0.98, -2.4)])
    det = []
    if near:
        for o in (-1.0, 0.3, 1.5):
            det.append(('ink', [al(1.14, o), al(1.25, o + 0.1)], 0.9, (0.05, 0.8)))
        det.append(('ink', [al(1.0, 2.5), al(1.05, 1.0), al(1.03, -0.6)], 1.0, (0.1, 0.6)))
    cv.shape(body, gm, z=z, sd=1.1, hi=0.3 if near else 0.0, details=det)
    th = cv.blob([al(0.92, 1.7), al(1.0, 2.85), al(1.12, 2.5), al(1.08, 1.3)])
    cv.shape(th, gm, z=z + 0.05, sd=0.7, hi=0.2 if near else 0.0, ol=0.8)
    cv.pop()


def shoulder_pelt(cv, sh, e, z, swing=0.0, near=True):
    """Asimetrik omuz postu (yalnızca ön omuz): başlığın kurt derisi omzun üstünden dökülür, kurdun ön ayağı göğse sarkar
    (koyu tırnaklı pençe). Omuz ekleminin üstünü örter: kol nereye dönerse dönsün menteşe görünmez (oyunda yaşayan kolun
    üstünde ayrı katman olarak çizilir, kolla yalnızca biraz döner)."""
    c = (sh[0] - 0.3, sh[1] - 0.6)
    sw = swing * 0.8
    paw = (c[0] + 2.0 + sw * 0.4, c[1] + 5.0)
    pts = [(c[0] - 3.2, c[1] + 0.6), (c[0] - 2.4, c[1] - 1.2), (c[0] - 0.4, c[1] - 1.9), (c[0] + 1.8, c[1] - 1.2),
           (c[0] + 2.9, c[1] + 0.6), (paw[0] + 1.1, paw[1] - 1.6), (paw[0] + 0.9, paw[1] + 0.4, 0.4),
           (paw[0] - 0.6, paw[1] + 0.6, 0.4), (paw[0] - 0.9, paw[1] - 1.2), (c[0] + 0.6, c[1] + 2.4, 0.0),
           (c[0] - 0.2, c[1] + 1.6), (c[0] - 1.0, c[1] + 2.8, 0.0), (c[0] - 1.8, c[1] + 1.6), (c[0] - 2.6, c[1] + 2.4, 0.0)]
    path = cv.blob(pts)
    det = [('ink', [(c[0] - 1.6, c[1] - 0.6), (c[0] + 0.2, c[1] + 0.4), (c[0] + 1.6, c[1] + 1.8)], 0.8, (0.4, 0.4)),
           ('shade', cv.wedge([(c[0] + 2.6, c[1] + 0.6), (paw[0] + 0.9, paw[1] - 1.4)], 0.6, 1.0)),
           ('shade', cv.wedge([(c[0] - 3.0, c[1] + 1.0), (c[0] - 0.6, c[1] + 2.2), (c[0] + 1.2, c[1] + 1.6)], 0.6, -1.0))]
    m = FUR if near else FUR_B
    cv.shape(path, m.darker(0.94), z=z, sd=0.9, hi=0.25, cast=0.5, details=det, fur=0.9)
    for dx in (-0.5, 0.15, 0.8):
        cv.stroke([(paw[0] + dx, paw[1] + 0.2), (paw[0] + dx - 0.15, paw[1] + 1.2)], 1.0, z=z + 0.1, taper=(0.1, 0.9))


def _arm(cv, sh, e, h, z, near=True, pelt=False):
    arm_shapes(cv, sh, e, h, z, near)
    fist(cv, e, h, z + 0.4, near)
    if pelt:
        shoulder_pelt(cv, sh, e, z + 0.8, near=near)


# ------------------------------------------------------------ baş
def _head(cv, head, neck, p, z):
    """Profil yüz (sağa bakan) + kurt postu başlık. Başlık kask değil: kurdun üst başı (burun, kaş, kulaklar) başın
    üstüne oturur, post yanlardan yüzü çerçeveleyip enseden sırta akar."""
    hx_, hy_ = head
    jaw = p.get('jaw', 0.0)
    bp = p.get('bp', 0.0)
    lean = p['lean']
    ear = p.get('ear', 0.0) + max(0.0, lean - 0.1) * 0.5 + math.sin(bp * 6.28 - 1.4) * 0.05

    def H(x, y, *k):
        return (hx_ + x, hy_ + y - 0.3) + tuple(k)
    FS, FX0, FY0 = 1.16, 0.4, 0.8

    def F(x, y, *k):
        return (hx_ + FX0 + (x - FX0) * FS, hy_ + FY0 + (y - FY0) * FS) + tuple(k)

    # kulaklar: dik, uzun, uçları koyu (kurt): uzak kulak arkada
    for near in (False, True):
        if near:
            b0, b1, ln, a_ = H(0.2, -4.6), H(2.6, -4.3), 5.6, -math.pi * 0.5 - 0.12 - ear
            mat, zz, org = FUR, z + 2.2, H(1.2, -4.6)
        else:
            b0, b1, ln, a_ = H(-2.6, -3.8), H(-0.1, -4.8), 5.0, -math.pi * 0.5 - 0.36 - ear
            mat, zz, org = FUR_B, z - 0.8, H(-1.4, -4.4)
        tip = (org[0] + math.cos(a_) * ln, org[1] + math.sin(a_) * ln)
        m0, m1 = lerp2(b0, tip, 0.55), lerp2(b1, tip, 0.55)
        e_path = cv.blob([b0, (m0[0] - 0.35, m0[1]), (tip[0], tip[1], 0.0), (m1[0] + 0.3, m1[1] + 0.1), b1])
        det = [('col', cv.blob([lerp2(b0, tip, 0.72), (tip[0], tip[1], 0.0), lerp2(b1, tip, 0.72)]), (0.2, 0.19, 0.24))]
        if near:
            i0, i1 = lerp2(b0, b1, 0.3), lerp2(b0, b1, 0.78)
            itip = lerp2(lerp2(b0, b1, 0.5), tip, 0.7)
            det.append(('col', cv.blob([i0, lerp2(i0, itip, 0.6), (itip[0], itip[1], 0.0), lerp2(i1, itip, 0.5), i1]), EAR_IN.shadow))
        cv.shape(e_path, mat, z=zz, sd=1.2, details=det, fur=0.4)

    # yüz: zarif profil (düz burun, belirgin elmacık, ince çene)
    jw = jaw * 0.9
    face = cv.blob([F(-1.2, -3.0), F(1.4, -3.2), F(2.6, -2.5), F(3.05, -1.6), F(2.95, -0.95), F(3.55, 0.2, 0.3),
                    F(3.35, 0.55, 0.5), F(2.98, 0.68), F(3.12, 1.1), F(2.9, 1.4 + jw * 0.35), F(3.02, 1.78 + jw),
                    F(2.8, 2.3 + jw), F(2.45, 2.8 + jw, 0.6), F(1.5, 2.95 + jw * 0.6), F(0.2, 2.5), F(-1.3, 0.6)])
    fdet = [
        ('shade', cv.blob([F(-1.0, -3.4), F(3.4, -3.4), F(3.0, -2.15), F(2.1, -1.85), F(1.0, -1.95), F(-1.0, -1.7)])),
        # kaş ince ve kararlı; göz badem, koyu (camgöbeği Kut ışığı kurt gözünde yaşar), uzun kirpik kuyruğu
        ('ink', [F(1.2, -1.42), F(2.05, -1.66), F(2.95, -1.5)], 1.5, (0.2, 0.5)),
        ('col', cv.blob([F(2.72, -0.86, 0.0), F(2.12, -1.12), F(1.36, -0.98), F(1.46, -0.6, 0.0), F(2.2, -0.56)]), (0.95, 0.92, 0.88)),
        ('col', cv.ellipse(F(2.22, -0.84), 0.4 * FS, 0.42 * FS), EYE_DARK),
        ('col', cv.ellipse(F(2.36, -0.95), 0.12 * FS, 0.12 * FS), (1.0, 0.95, 0.85)),
        ('ink', [F(2.82, -0.95), F(2.1, -1.2), F(1.25, -1.04), F(0.65, -0.78)], 1.5, (0.1, 0.75)),
        ('ink', [F(3.0, 0.36), F(2.74, 0.5), F(2.78, 0.66)], 0.8, (0.3, 0.3)),
        ('col', cv.blob([F(3.2, 1.0), F(2.94, 1.34 + jw * 0.3), F(3.08, 1.78 + jw), F(2.66, 1.68 + jw * 0.8), F(2.7, 1.16)]), (0.7, 0.3, 0.32)),
        ('ink', [F(3.0, 1.38 + jw * 0.35), F(2.55, 1.46 + jw * 0.4)], 0.9, (0.1, 0.7)),
        # tek kızıl çizgi: gözün altından şakağa (şafak boyası) — sade
        ('stroke', [F(2.5, -0.2), F(1.6, -0.12), F(0.3, 0.1)], 1.7, PAINT, (0.15, 0.7)),
        ('shade', cv.wedge([F(0.8, 1.0), F(1.5, 1.9), F(2.4, 2.6)], 0.4, -1.0)),
    ]
    if jaw > 0.3:
        fdet.append(('col', cv.blob([F(2.98, 1.28), F(2.48, 1.42), F(2.6, 1.72 + jw), F(3.02, 1.72 + jw)]), (0.3, 0.06, 0.1)))
    cv.shape(face, SKIN, z=z + 0.4, sd=0.7, hi=0.22, details=fdet, bounce=0.35, soft=0.25)
    # uzun ince boyun (görünür: yaşayan insan)
    cv.shape(soft_limb(cv, [F(0.7, 2.2), lerp2(F(0.7, 2.2), (neck[0] + 0.7, neck[1] + 0.8), 0.5), (neck[0] + 0.7, neck[1] + 0.8)],
                       [(0.0, 2.6), (1.0, 3.2)]), SKIN, z=z - 0.2, sd=0.9, ol=0.9,
             details=[('shade', cv.wedge([F(0.2, 2.3), (neck[0] + 0.2, neck[1] + 0.2)], 0.5, -1.0))])
    # yüzü çerçeveleyen tutam + alnın kâkülü
    lock = ik.taper_path([cv.W(F(1.0, -2.5)), cv.W(F(0.5, -0.8)), cv.W(F(0.4, 1.3)), cv.W(F(0.8, 3.3 + jw * 0.5))],
                         cv.u(1.0), prof=lambda s: max(0.2, max(0.0, 1.0 - s) ** 0.7) * (0.6 + 0.4 * min(1.0, s * 6.0)))
    cv.shape(lock, HAIR, z=z + 1.95, sd=0.5, ol=0.7, details=[('stroke', [F(0.85, -2.0), F(0.55, -0.4), F(0.5, 1.1)], 0.7, HAIR.hi, (0.3, 0.6))])
    bang = ik.taper_path([cv.W(F(2.0, -2.6)), cv.W(F(2.5, -2.0)), cv.W(F(2.75, -1.7))], cv.u(0.75), (0.1, 0.9))
    cv.shape(bang, HAIR, z=z + 0.6, sd=0.4, ol=0.6)

    # kurt postu: üst baş + kalın ama kısa burun + yanlardan yüzü saran post (alt kenarı yumuşak, tutamlı)
    hood = cv.blob([H(-4.0, 2.2), H(-4.3, -1.2), H(-3.4, -3.7), H(-1.4, -5.1), H(1.1, -5.5), H(2.9, -5.1), H(3.9, -4.5),
                    H(5.2, -4.3), H(6.4, -4.05), H(7.2, -3.7), H(7.55, -3.2, 0.5), H(7.4, -2.65, 0.5), H(6.8, -2.3),
                    H(5.8, -1.95), H(4.6, -1.95), H(3.4, -2.05), H(2.3, -2.3, 0.5), H(1.1, -2.0),
                    H(0.25, -0.6), H(-0.1, 1.3), H(0.3, 3.0, 0.0), H(-0.6, 3.6), H(-1.2, 4.6, 0.0), H(-2.0, 4.0),
                    H(-3.0, 4.9, 0.0), H(-3.5, 3.6)])
    hdet = [
        ('deep', cv.wedge([H(3.2, -4.4), H(4.4, -4.15), H(5.6, -3.85)], 0.45, 1.0)),
        ('ink', [H(3.1, -4.55), H(4.4, -4.3), H(5.7, -3.95)], 1.6, (0.15, 0.7)),
        ('ink', [H(7.2, -2.55), H(6.3, -2.3), H(5.4, -2.25)], 1.1, (0.2, 0.5)),
        ('shade', cv.wedge([H(7.0, -2.3), H(5.4, -1.85), H(3.4, -2.05)], 0.45, 1.0)),
        ('shade', cv.wedge([H(1.3, -2.1), H(0.45, -0.6), H(0.1, 1.4), H(0.4, 3.0)], 0.7, -1.0)),
        ('ink', [H(-0.5, -1.6), H(-1.0, -0.1), H(-0.8, 1.2)], 0.9, (0.4, 0.4)),
        ('ink', [H(-1.9, 1.0), H(-2.4, 2.4), H(-1.9, 3.6)], 0.9, (0.4, 0.4)),
        # sırtın koyu eyer lekesi (kurt postunun deseni): başlığa derinlik
        ('col', cv.blob([H(-3.4, -3.2), H(-1.2, -4.9), H(1.6, -5.2), H(0.8, -4.0), H(-1.2, -2.5), H(-3.2, -1.2)]), FUR.shadow),
        # alında küçük kızıl tamga (tan işareti: üç ışınlı)
        ('stroke', [H(2.4, -5.0), H(3.1, -4.75)], 1.3, PAINT, (0.2, 0.4)),
    ]
    cv.shape(hood, FUR, z=z + 1.6, sd=0.9, hi=0.32, details=hdet, cast=0.5, bounce=0.35, fur=0.9)
    # ense yelesi: başlığın arkasından sırta dökülen post (başlık + pelerin tek kurt derisi okunur)
    mane = cv.blob([H(-3.2, -3.4), H(-4.6, -1.0), H(-5.4, 2.0), H(-6.4, 4.4, 0.0), H(-5.0, 4.0), H(-5.6, 6.4, 0.0),
                    H(-4.0, 5.6), H(-3.8, 7.6, 0.0), H(-2.6, 5.4), H(-1.0, 4.4), H(-1.6, 1.0)])
    cv.shape(mane, FUR, z=z + 1.2, sd=1.0, hi=0.2, fur=1.0,
             details=[('ink', [H(-4.0, 0.0), H(-4.8, 3.0)], 0.8, (0.4, 0.4)), ('ink', [H(-2.8, 2.0), H(-3.4, 5.0)], 0.8, (0.4, 0.4))])
    # kurt gözü: camgöbeği Kut ışığı (başlıkta)
    cv.fill(cv.blob([H(4.15, -3.55, 0.0), H(4.8, -3.86), H(5.5, -3.66, 0.0), H(4.86, -3.38)]), b.EYE, z=z + 1.9, glow=b.EYE_GLOW)
    cv.shape(cv.blob([H(6.9, -3.85), H(7.65, -3.6), H(7.75, -3.0, 0.4), H(7.2, -2.85)]), NOSE, z=z + 2.0, sd=0.4, hi=0.3, ol=0.7)
    for fx_, fy_, ln in ((6.2, -2.05, 1.0), (4.4, -1.95, 0.8)):
        cv.shape(cv.blob([H(fx_ + 0.28, fy_), H(fx_ - 0.26, fy_), H(fx_ + 0.02, fy_ + ln, 0.0)]), TOOTH, z=z + 1.5, sd=0.3, ol=0.6, hi=0.0)


# ------------------------------------------------------------ gövde
def _xf(cv, p):
    return b._xf(cv, p)


def draw(cv, p, front_arm=True, back_arm=True):
    bob, lean = p['bob'], p['lean']
    sk, pk, bp = p.get('sk', 0.0), p.get('pk', 0.0), p.get('bp', 0.0)
    br = p.get('br', 0.0)
    tw = p.get('tw', 0.0)
    hip = (p.get('hx', 0.0), HIP_Y + bob * 1.1)
    curl = p.get('curl', 0.0)
    tl = TORSO * (1.0 - 0.32 * curl) + br * 0.3
    neck = (hip[0] + math.sin(lean) * tl, hip[1] - math.cos(lean) * tl)
    sx = p.get('sx', 0.0)
    sh_f = (neck[0] + 1.4 + sx + tw * 0.7, neck[1] + 3.2)
    sh_b = (neck[0] - 2.8 - sx * 0.5 - tw * 0.7, neck[1] + 3.0)
    head = (neck[0] + 1.6 + math.sin(lean) * 1.6 + p.get('hdx', 0.0), neck[1] - 4.6 + p.get('hdy', 0.0))
    out = {'sh_f': sh_f}
    ts_ = (tl / (TORSO + br * 0.3) if curl else 1.0) * AXK
    ax = (math.sin(lean) * ts_, -math.cos(lean) * ts_)
    pe = (math.cos(lean) * WAIST_K, math.sin(lean) * WAIST_K)
    T = _T(hip, ax, pe)
    out['kusak'] = _xf(cv, T(4.4, -4.9))
    out['etek'] = _xf(cv, T(2.0, -4.4))

    # ---- arka kol
    e, h = fk_arm(sh_b, p['ab'][0], p['ab'][1], L_UP, L_FORE)
    if back_arm:
        _arm(cv, sh_b, e, h, -12.5, near=False)
    out['hand_b'] = h
    out['ang_b'] = p['ab'][0] + p['ab'][1]
    out['sh_b'] = sh_b
    out['arm_b'] = (p['ab'][0], p['ab'][1])

    # ---- arka etek kökü (kısa; uzun yırtmaçlı etekler oyunda kumaş şerit olarak buradan sarkar)
    flap = sk * 1.6
    bk = cv.blob([(hip[0] - 4.8, hip[1] - 1.6), (hip[0] - 0.6, hip[1] - 1.2), (hip[0] - 1.0 + flap * 0.3, hip[1] + 7.4),
                  (hip[0] - 3.6 + flap, hip[1] + 8.2, 0.0), (hip[0] - 6.6 + flap * 1.4, hip[1] + 6.4, 0.0)])
    cv.shape(bk, KAFTAN_B, z=-11, sd=1.8, details=[('ink', [(hip[0] - 2.6, hip[1] + 0.5), (hip[0] - 3.2 + flap, hip[1] + 7.0)], 0.9, (0.3, 0.6))])

    # ---- arka bacak
    _leg(cv, hip, p['lb'], -10, False, pitch=p.get('fpb', 0.0))

    # ---- gövde: ince bel, göğüs kavsi, düz sırt (kaftan bedene oturur)
    torso = cv.blob([T(-0.8, -5.0), T(3.6, -3.7), T(7.4, -4.0), T(11.0, -4.9 - br * 0.1), T(14.6, -4.9), T(16.8, -3.3),
                     T(17.8, -0.8), T(17.4, 1.6), T(15.6, 3.6), T(12.8, 5.1 + br * 0.25), T(10.2, 4.0), T(6.6, 3.0),
                     T(3.0, 3.4), T(0.2, 4.6), T(-0.8, 4.9)])
    tdet = cv.fold([T(13.4, -4.2), T(10.0, -3.0), T(6.6, -3.3)], 0.55, 1.0, 1)
    tdet += cv.fold([T(10.0, 4.0), T(8.2, 2.6), T(6.4, 2.6)], 0.4, 0.9, 1)
    cv.shape(torso, KAFTAN, z=0, sd=3.8, hatch=0.35, deep=0.3, details=tdet, bounce=0.35)
    # sırtta güneş tamgası (Gün Ana'nın işareti): sırma halka + sekiz ışın, hafif ışır (örgüler toplandıkça parlar)
    sc = T(8.2, -3.6)
    ring = ik.isect(torso, ik.union(cv.ellipse(sc, 1.1, 1.1), *[cv.capsule(sc, (sc[0] + math.cos(a) * 1.75, sc[1] + math.sin(a) * 1.75), 0.2, 0.08)
                                                                   for a in [i * math.pi / 4 for i in range(8)]]))
    cv.shape(ring, SIRMA.darker(0.8), z=0.4, sd=0.4, hi=0.2, ol=0.4, spec=0.3)
    cv.fill(ik.isect(torso, cv.ellipse(sc, 0.5, 0.5)), GUN, z=0.5, glow=(0.32, 0.18, 0.06))
    # önü kavuşturmalı yaka: üst panel sağdan sola biner, kenarında sırma tamga şeridi (bel kemerine iner)
    lap = [T(17.4, 1.3), T(15.6, 3.6), T(12.8, 5.0), T(10.2, 4.3), T(6.6, 3.5), T(4.2, 3.8), T(4.6, 1.4), T(9.6, 0.6),
           T(14.4, -0.4), T(17.0, -1.2)]
    cv.shape(cv.blob(lap), KAFTAN, z=0.6, sd=1.4, hi=0.15, ol=0.7,
             details=cv.fold([T(14.0, 2.8), T(11.0, 2.0), T(8.0, 1.6)], 0.35, 0.8, -1))
    edge = [T(17.1, -1.1), T(14.4, -0.3), T(9.6, 0.7), T(4.6, 1.5)]
    strip = ik.taper_path([cv.W(q) for q in edge], cv.u(0.75), (0.05, 0.3))
    cv.shape(strip, SIRMA, z=0.8, sd=0.5, hi=0.2, ol=0.5, spec=0.4,
             details=[('ink', [T(16.6, -0.75), T(13.0, 0.05), T(8.0, 0.95), T(4.8, 1.3)], 0.6, (0.0, 0.0))])
    # dik yaka (kısa)
    cv.shape(cv.blob([T(16.6, -3.0), T(18.4, -2.2), T(18.6, 0.6), T(17.4, 1.5), T(16.8, -0.8)]), ASTAR, z=0.9, sd=0.6, hi=0.2, ol=0.7)

    # ---- ön etek: önü AÇIK kaftan; ön kenar kemerden geriye-aşağı çapraz iner (ön uyluk görünür), etek ucu arkaya doğru
    # uzar (kuyruklar oyunda kumaş şerit): kutu / kilt değil, akan çapraz bir çizgi
    kb, _ = fk_leg(hip, p['lb'][0], p['lb'][1], L_THIGH, L_SHIN)
    raised = p['lf'][0] > 0.95
    ek, pk_ = BICIM.get(PAL, (1.0, 1.0))
    Fp = (hip[0] + 1.6 + sk * 1.0, hip[1] + 6.4 * ek - max(0.0, sk - 0.6) * 1.5)
    Bp = (max(hip[0] - 8.6, min(hip[0] - 5.0, kb[0] - 1.6)) + sk * 2.4, hip[1] + 9.6 * ek - max(0.0, -sk) * 2.0 - max(0.0, sk - 0.6) * 2.4)
    wav = [(Fp[0], Fp[1], 0.0)]
    for j, t in enumerate((0.33, 0.66)):
        q = lerp2(Fp, Bp, t)
        wav.append((q[0], q[1] + 0.5 * math.sin(math.pi * t)))
    wav.append((Bp[0], Bp[1], 0.0))
    ftop = T(2.6, 4.0)
    fmid = (lerp2(ftop, Fp, 0.5)[0] + 0.9, lerp2(ftop, Fp, 0.5)[1])
    skirt = cv.blob([(hip[0] - 5.0, hip[1] - 2.0, 0.6), (ftop[0], ftop[1], 0.6), fmid] + wav)
    sdet = cv.fold([(hip[0] - 1.0, hip[1] + 1.2), (hip[0] - 1.8, hip[1] + 5.0), lerp2(Fp, Bp, 0.55)], 0.6, 1.0, -1, taper=(0.7, 0.05))
    sdet += cv.fold([(hip[0] - 3.6, hip[1] + 1.0), lerp2(Fp, Bp, 0.92)], 0.4, 0.8, -1, taper=(0.7, 0.05))
    cv.shape(skirt, KAFTAN, z=2.0, sd=2.4, details=sdet, hatch=0.3, deep=0.3, bounce=0.3)
    # ön kenarda astarın dönüşü (açık kaftanın iç yüzü: ince safran şerit)
    fe = ik.isect(skirt, ik.taper_path([cv.W(ftop), cv.W(fmid), cv.W(Fp)], cv.u(1.1), (0.0, 0.3)))
    cv.shape(fe, ASTAR, z=2.1, sd=0.5, hi=0.2, ol=0.5)

    # ---- kemer: geniş deri, gümüş plakalar, önde güneş tokası (Kut közü), arkada kısa bıçak
    belt_pts = [T(3.9 - 0.6 * math.cos(math.pi * 0.5 * v / 5.6) ** 2, v) for v in (-5.0, -2.6, -0.2, 2.2, 4.6)]
    belt = ik.union(*[cv.capsule(a_, b_, 1.35, 1.35) for a_, b_ in zip(belt_pts, belt_pts[1:])])
    cv.shape(belt, DERI, z=5.0, sd=1.0, hi=0.25, cast=0.6)
    for q in belt_pts[1:-1]:
        cv.shape(cv.ellipse(q, 0.55, 0.62, lean), PLAK, z=7.2, sd=0.4, hi=0.3, ol=0.6)
    buck = T(3.6, 4.8)
    cv.shape(cv.ellipse(buck, 1.25, 1.4, lean), GOLD, z=8.2, sd=0.6, hi=0.35, ol=0.8)
    cv.fill(cv.ellipse(buck, 0.55, 0.62, lean), KOR, z=8.3, glow=(1.0, 0.5, 0.18))
    # kayış + sarkan gümüş halka (yürüyüşte sallanır: sk)
    a = T(3.2, 2.6)
    bq = (a[0] + sk * 0.6 + 0.2, a[1] + 4.2)
    cv.shape(cv.capsule(a, bq, 0.45, 0.4), DERI, z=8.4, sd=0.4, ol=0.7)
    cv.shape(cv.ellipse(bq, 0.6, 0.7), PLAK, z=8.6, sd=0.4, hi=0.3, ol=0.7)
    # arka belde kısa bıçak (kının ucu aşağı-geri)
    k0, k1 = T(3.6, -5.6), T(-2.2, -7.4)
    cv.shape(cv.capsule(k0, k1, 0.75, 0.5), DERI.darker(0.8), z=4.4, sd=0.5, ol=0.8)
    cv.shape(cv.capsule(T(4.3, -5.4), T(6.2, -5.0), 0.45, 0.45), PLAK, z=4.5, sd=0.3, hi=0.3, ol=0.7)

    # ---- kuşak düğümü (arkada; kuyrukları oyunda Verlet: BenguKusak)
    cv.shape(cv.ellipse(T(4.4, -4.9), 1.25, 1.1, lean), KUSAK, z=5.6, sd=0.6, hi=0.3, ol=0.8,
             details=[('ink', [T(3.8, -5.3), T(5.0, -4.5)], 0.8)])

    # ---- ön bacak
    k, f = _leg(cv, (hip[0] + 1, hip[1]), p['lf'], 6.0 if raised else 1.0, True, pitch=p.get('fpf', 0.0))
    out['foot_f'] = f

    # ---- kurt derisi pelerin: başlığın devamı, enseden sırt boyunca bele iner (sırta yapışık, ucu tutamlı, hızla savrulur).
    # Silüetin ana ikonu: ak kurt başı + sırttan akan ak post + kızıl kaftan. (Omuz postu denendi: oyun boyunda omuzluk gibi
    # okundu; bırakıldı.)
    cf = p.get('cf', 0.0)
    fl = max(0.0, -sk) * 0.8 + max(0.0, cf) * 1.2
    edge = []
    for i in range(9):
        t = i / 8
        u = 18.8 - 15.0 * t * BICIM.get(PAL, (1, 1))[1]
        v = -5.0 - (0.8 + 2.6 * t * t) * (1.0 + fl * 0.8) - 0.4 * math.sin(i * 1.9 + bp * 6.28) * t
        edge.append(T(u, v, 0.0 if i % 2 else 0.6))
    tip = T(18.8 - 16.2 * BICIM.get(PAL, (1, 1))[1] - fl * 2.0, -7.6 - fl * 3.0, 0.0)
    cl = BICIM.get(PAL, (1, 1))[1]
    inner = [T(18.8 - (18.8 - u) * cl, v) for u, v in ((4.2, -4.6), (8.0, -4.6), (12.0, -4.6), (16.0, -4.2), (18.6, -2.4))]
    cape = cv.blob([T(19.8, -1.8)] + edge + [tip] + inner)
    cdet = [('ink', [T(17.6, -5.6), T(13.0, -6.2), T(8.0, -6.6)], 0.8, (0.4, 0.5)),
            ('ink', [T(15.0, -5.2), T(10.0, -5.6)], 0.7, (0.5, 0.5)),
            ('col', cv.blob([T(18.4, -4.0), T(14.0, -5.0), T(9.0, -5.2), T(5.0, -5.0), T(9.0, -4.7), T(14.0, -4.5)]), FUR.shadow)]
    cv.shape(cape, FUR, z=9.0, sd=0.9, hi=0.25, cast=0.7, fur=1.0, details=cdet)

    # ---- baş
    hs = HEAD_K
    cv.push(lambda q, c0=head: (c0[0] + (q[0] - c0[0]) * hs, c0[1] + (q[1] - c0[1]) * hs))
    _head(cv, head, neck, p, 10.0)
    cv.pop()
    out['head'] = head
    sac = (head[0] - 3.3 * hs / 1.05, head[1] + 2.2 * hs / 1.05)
    s0 = _xf(cv, sac)
    s1 = _xf(cv, (sac[0] - 0.5, sac[1] + 0.87))
    out['sac'] = s0
    out['sac_d'] = math.atan2(s1[1] - s0[1], s1[0] - s0[0])
    out['neck'] = _xf(cv, neck)
    out['hip'] = _xf(cv, hip)
    if KONSEPT:
        _konsept_ekleri(cv, sac, hip, p)

    # ---- ön kol (sprite'ta; silahlıyken oyunda yaşayan iskelet kol + omuz postu katmanı çizer)
    a1, a2 = p['af']
    e, h = fk_arm(sh_f, a1, a2, L_UP, L_FORE * p.get('ext', 1.0))
    if front_arm:
        _arm(cv, sh_f, e, h, 16.5, near=True)
    out['hand_f'] = h
    out['ang_f'] = a1 + a2
    out['arm'] = (a1, a2)
    return out


KONSEPT = False      # konsept sayfası: oyunda fizikli olan örgü + kaftan kuyrukları durağan çizilir


def _konsept_ekleri(cv, sac, hip, p):
    """Konsept sayfası için: uzun tek örgü (şolpı gümüş pullarıyla) + yırtmaçlı arka etek kuyrukları (oyunda fizikli)."""
    sk = p.get('sk', 0.0)
    blow = max(0.0, -sk)
    pts = [sac]
    a = math.pi * 0.5 + 0.12 + blow * 0.9
    x, y = sac
    for i in range(12):
        a += -0.01 + blow * 0.03
        x += math.cos(a) * 2.1
        y += math.sin(a) * 2.1
        pts.append((x, y))
    br = ik.taper_path([cv.W(q) for q in pts[:-2]], cv.u(2.0), prof=lambda s: 1.0 - 0.35 * s)
    lob = []
    for i in range(1, len(pts) - 3):
        q0, q1 = pts[i], pts[i + 1]
        n, d = b._perp(q0, q1)
        lob.append(('ink', [(q0[0] + n[0] * 0.8, q0[1] + n[1] * 0.8), lerp2(q0, q1, 0.6), (q0[0] - n[0] * 0.8, q0[1] - n[1] * 0.8)], 0.7, (0.2, 0.2)))
    cv.shape(br, HAIR, z=-13.5, sd=0.6, hi=0.2, details=lob)
    for j in range(5):
        q = lerp2(pts[-4], pts[-1], j / 4.0)
        cv.shape(cv.ellipse((q[0] + 0.2 * j, q[1]), 0.95 - 0.08 * j, 0.95 - 0.08 * j), PLAK, z=-13.3 + 0.01 * j, sd=0.4, hi=0.35, ol=0.7)
    for ox, ln, m in ((-1.0, 14.5, ASTAR), (-3.4, 13.0, KAFTAN_B)):
        r0 = (hip[0] + ox, hip[1] + 4.0)
        tip = (r0[0] - 2.4 - blow * 7.0 + sk * 1.5, r0[1] + ln - blow * 5.0)
        mid = lerp2(r0, tip, 0.5)
        cv.shape(cv.blob([(r0[0] + 1.6, r0[1]), (mid[0] + 1.6, mid[1]), (tip[0] + 1.2, tip[1], 0.0), (tip[0] - 1.4, tip[1] - 1.2, 0.0),
                          (mid[0] - 1.8, mid[1]), (r0[0] - 1.8, r0[1])]), m, z=-12 if m is ASTAR else -12.2, sd=1.2)


# ------------------------------------------------------------ yaşayan kol dokusu (oyunda BenguKol.gd bükerek çizer)
# Düz (dinlenme) kol şeridi: omuz üstte, dirsek L_UP aşağıda, bilek L_UP + L_FORE'da. Oyunda şerit omuz -> dirsek ->
# bilek eğrisi boyunca (dirsekte yuvarlatılmış) bükülür: kumaş kol kesintisiz kıvrılır, menteşe yok.
ARM_CELL = (40, 96)           # her parça aynı hücre (doku pikseli; dünya 10 x 24)
STRIP_PIVOT = (20, 14)        # şeritte omuz (dünya 5, 3.5)
FIST_PIVOT = (20, 14)         # yumrukta bilek (kemik ucu)
ARM_PARTS = ['strip', '', 'fist', 'strip_b', '', 'fist_b']


def render_arm_strip(ss=4, mirror=False):
    """bengu_kol_v2 satırı: [şerit, boş, yumruk, şerit_arka, boş, yumruk_arka] (eski 6 sütun düzeni; +y kemik yönü).
    Şerit: düz kol (omuz başı -> dirsek -> bilek), oyunda BenguKol.gd bükerek çizer."""
    light = (-ik.LIGHT[0], ik.LIGHT[1]) if mirror else ik.LIGHT
    out = []
    blank = None
    for near in (True, False):
        cv = ik.InkCanvas(ARM_CELL[0], ARM_CELL[1], STRIP_PIVOT[0], STRIP_PIVOT[1], k=TEX, ss=ss, light=light)
        arm_shapes(cv, (0, 0), (0, L_UP), (0, L_UP + L_FORE), 0, near)
        rgba = cv.finish(outer=0.4)[0]
        out.append(rgba)
        blank = np.zeros_like(rgba)
        out.append(blank)
        cv = ik.InkCanvas(ARM_CELL[0], ARM_CELL[1], FIST_PIVOT[0], FIST_PIVOT[1], k=TEX, ss=ss, light=light)
        fist(cv, (0, -L_FORE), (0, 0), 0, near)
        out.append(cv.finish(outer=0.4)[0])
    return out


# ------------------------------------------------------------ yeni satırlar: tırmanma (zincir / ip / sarmaşık), ölüm
def _climb(t):
    """Tırmanma döngüsü (yüz duvara değil, yandan: iki el ip üstünde sırayla uzanır, bacaklar sırayla çekilir).
    Kol açıları: 0 aşağı, pi yukarı. Ön ve arka el yarım faz kaymalı; kalça el çekişiyle hafif kalkar."""
    ph = t * math.tau
    s = math.sin(ph)
    c = math.cos(ph)
    reach_f = 0.5 + 0.5 * s
    reach_b = 0.5 - 0.5 * s
    return P(bob=-0.6 + 0.8 * c, lean=0.06, hx=-1.2,
                lf=(0.55 + 0.95 * reach_b, 1.0 + 1.1 * reach_b), lb=(0.3 + 0.95 * reach_f, 0.9 + 1.1 * reach_f),
                af=(1.75 + 1.1 * reach_f, 1.2 - 1.05 * reach_f), ab=(1.6 + 1.1 * reach_b, 1.25 - 1.05 * reach_b),
                sk=0.4, pk=0.5, bp=t, jaw=0.0, hdy=-0.6, hdx=0.5, sx=0.6, tw=0.25 * s, cf=-0.2)


def _climb_idle(t):
    s = math.sin(t * math.tau)
    return P(bob=-0.2 + 0.25 * s, lean=0.08, hx=-1.2, lf=(1.05, 1.6), lb=(0.55, 1.4),
                af=(2.6 + 0.03 * s, 0.35), ab=(1.8, 1.1), sk=0.35, pk=0.4, bp=t, br=s, hdy=-0.4 + 0.15 * s, hdx=0.4, sx=0.5)


def _death(t):
    """Ölüm: darbe -> dizler çözülür -> yana yığılır (son karede yerde, baş öne)."""
    k1 = b._smooth(0.0, 0.35, t)
    k2 = b._smooth(0.3, 0.9, t)
    p = P(bob=0.0 + 6.0 * k1 + 10.0 * k2, lean=-0.4 * (1 - k2) + 1.25 * k2, hx=-2.0 * k1 - 3.0 * k2,
             lf=(0.6 + 0.9 * k1, 0.6 + 1.6 * k1), lb=(-0.6 + 1.5 * k2, 0.5 + 1.9 * k2),
             af=(-1.2 + 1.9 * k2, 1.0 - 0.6 * k2), ab=(-1.5 + 2.2 * k2, 0.6), sk=1.0 - 0.6 * k2, pk=1.0,
             jaw=0.8 * (1 - k2), hdy=-0.6 + 2.6 * k2, hdx=-0.8 + 1.6 * k2, bp=t, cf=0.6 * (1 - k2))
    return b.ground(p, 0.0) if k2 < 0.98 else b.ground(p, 0.0)


NEW_ANIMS = {
    'tirman': (6, _climb, True, True),
    'tirman_bekle': (2, _climb_idle, True, True),
    'olum': (6, _death, False, True),
}
NEW_LAYOUT = {
    'tirman': {'frames': 6, 'fps': 9, 'loop': True, 'arm': True},
    'tirman_bekle': {'frames': 2, 'fps': 2, 'loop': True, 'arm': True},
    'olum': {'frames': 6, 'fps': 10, 'loop': False, 'arm': True},
}


def install():
    """bengu_ink'in çizimini v43 tasarımıyla değiştir (pozlar, satırlar, çapalar aynı) ve yeni satırları ekle."""
    b.draw = draw
    b.render_arm_parts = render_arm_strip
    b.ARM_CELL, b.ARM_PIVOT, b.FIST_PIVOT = ARM_CELL, STRIP_PIVOT, FIST_PIVOT
    b.ANIMS.update(NEW_ANIMS)
    b.MOVE_LAYOUT.update(NEW_LAYOUT)
    return b


install()
ANIMS = b.ANIMS
render_frame = b.render_frame
