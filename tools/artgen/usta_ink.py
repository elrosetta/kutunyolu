"""v32 Konak ve silah ustası: Bengisu Usta ile konak süsleri — stil v2 "mürekkep-cel" (inkkit.py / inkprop.py).

Bengisu ("bengi su": ölümsüzlük suyu) Demirci Kam Kuzgun'un kızıdır: babası yurtta ocağında döver, o kervanla yol
alır, alpların silahına yolda nakış vurur. Her derinlik arasındaki Konak'ta (Level.build_konak) ateşin başında bekler;
altınla silaha ek özellik nakşeder, nakışları yeniden döver, unsur aşılar, kaliteyi yükseltir, Kut Mührü basar
(scripts/core/Usta.gd, data/usta.json).

* npc_usta_v2 (NPC sayfası, npc_ink.py ile aynı düzen: idle 6 kare 8 fps, talk 4 kare 10 fps; yüz SOLA, ayak (0, 0)):
  genç, ince uzun bir kadın. Bakır kızılı saç tek kalın örgüde sırta iner (örgüde demir halkalar), alında deri bant ve
  firuze boncuk. Yeşil kısa kaftan (firuze-altın kenar işlemesi, kollar sıvalı: çıplak kaslı önkollar, deri bilek
  koruyucular), üstüne is lekeli deri önlük (göğüste kalem cebi: üç nakış kalemi), kızıl kuşak, şalvar, çizme. Ön elinde
  ucu Kut ışığıyla ışıyan nakış kalemi (çelik kalem, ucunda tamga damgası); arka elde küçük nakış çekici omuzda. Idle'da
  kalemin ucu nefes alır (ışıma), çekiç hafifçe salınır; konuşurken kalemi öne uzatır, çekiç kalkar ("göster bakalım").
* konak_ates_v2 (süs): taş halkalı konak ateşi: çapraz odunlar, harlı alev, közler (ışır), yanında iki minder ve kıl
  çuval; sacayağında bakır çaydanlık.
* usta_tezgah_v2 (süs): Bengisu'nun gezgin tezgâhı: kütük üstünde küçük örs, yanında taşınabilir tunç kor mangalı
  (körük hortumu, ışıyan kömür), yere serilmiş deri alet dürüsü (kalemler, eğe, maşa), asılı muskalar ve bir nakışlanan
  kılıç (örste, runları ışır), dayalı yük sepeti.
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_arm, lerp2, chain
from bengu_ink import along
from yurt import NPC_ANIMS
from npc_ink import _face, _hand, _sleeve, SKIN, GOLD, IRON, BOOT, CELL, FEET, TEX
import inkprop as P_
from inkprop import (Prop, FELT_C, RED, BLUE, TURQ, BRONZE, WOOD, WOOD_D, STEEL, LEATHER, ROPE, COPPER, STONE, STONE_D,
                     flame, diamond, tassel, grass_tufts)

# ------------------------------------------------------------ malzemeler
KAFTAN_G = Ink('#3f7a52', '#1c3a34', '#7ab888', '#0e2020', name='yeşil kaftan')
KAFTAN_GB = KAFTAN_G.darker(0.78)
APRON = Ink('#6e4a34', '#34221e', '#9c7250', '#1e1216', name='is lekeli önlük')
SASH = Ink('#b8342c', '#5e1830', '#e8664c', name='kızıl kuşak')
HAIR_C = Ink('#b4552a', '#5c2420', '#e89a5a', '#30120e', name='bakır saç')
PANTS = Ink('#3a3a4c', '#1c1c28', '#5c5c72', name='şalvar')
BRACER = Ink('#5a3a2a', '#2a1a16', '#86604a', name='bilek koruyucu')
KUT = (0.45, 1.0, 0.95)
KUT_GL = (0.3, 0.95, 1.0)
EMBER = (1.0, 0.55, 0.18)
EMBER_GL = (1.0, 0.42, 0.08)


# ------------------------------------------------------------ Bengisu Usta (yüz sola)
def draw_usta(cv, p):
    bob, lean, ph = p.get('bob', 0.0), p.get('lean', 0.0), p.get('ph', 0.0)
    talk = p.get('talk', 0.0)
    show = p.get('show', 0.0)          # konuşurken kalemi öne uzatma (0..1)
    hip = (0.0, -25.0 + bob * 0.3)
    neck = (hip[0] - math.sin(lean + 0.04) * 18.0, hip[1] - 18.0 + bob * 0.5)
    hd = (neck[0] - 1.4, neck[1] - 5.0)
    out = {'head': hd}
    hx, hy = hd
    # ---- arka örgü (sırta iner, demir halkalar; hafif salınır)
    br = chain((hx + 3.2, hy - 1.0), 8, 3.4, math.pi * 0.5 + 0.08 + math.sin(ph) * 0.03, 0.0, ph, 0.07)
    q = [cv.W(s) for s in br]
    cv.shape(ik.taper_path(q, cv.u(2.8), (0.05, 0.45)), HAIR_C, z=-14, sd=0.9, hi=0.3,
             details=[('ink', [lerp2(br[j], br[j + 1], 0.15), lerp2(br[j], br[j + 1], 0.6)], 0.9, (0.2, 0.2)) for j in range(0, 7)])
    for j in (2, 5):
        cv.shape(cv.ellipse(br[j], 1.4, 1.1), IRON, z=-13.9, sd=0.4, hi=0.3, ol=0.7)
    cv.shape(cv.blob([(br[-1][0] - 1.2, br[-1][1] - 0.6), (br[-1][0] + 1.2, br[-1][1] - 0.6), (br[-1][0] + 0.6, br[-1][1] + 3.0, 0.0),
                      (br[-1][0] - 0.8, br[-1][1] + 2.8, 0.0)]), HAIR_C.darker(0.85), z=-13.95, sd=0.4, ol=0.7)
    # ---- arka kol: küçük nakış çekici omuzda; konuşurken kalkar
    sh_b = (neck[0] + 3.4, neck[1] + 3.0)
    ab = p.get('ab', (0.3, -2.2))
    e, h = fk_arm(sh_b, ab[0], ab[1], 8.8, 8.2)
    _sleeve(cv, sh_b, e, h, KAFTAN_GB, -12, near=False, rolled=True, skin=SKIN.darker(0.8))
    # çekiç: sap elden yukarı-geriye, baş küçük demir
    ha = p.get('hang', -1.35)
    top = (h[0] + math.cos(ha) * 9.0, h[1] + math.sin(ha) * 9.0)
    butt = (h[0] - math.cos(ha) * 2.0, h[1] - math.sin(ha) * 2.0)
    cv.shape(cv.limb([butt, top], [0.95, 0.85]), WOOD, z=-11.8, sd=0.6, hi=0.3)
    dx_, dy_ = math.cos(ha + math.pi / 2), math.sin(ha + math.pi / 2)
    c_ = (top[0] + math.cos(ha) * 1.2, top[1] + math.sin(ha) * 1.2)
    head_ = cv.blob([(c_[0] + dx_ * 3.6 + math.cos(ha) * 1.6, c_[1] + dy_ * 3.6 + math.sin(ha) * 1.6, 0.2),
                     (c_[0] - dx_ * 3.6 + math.cos(ha) * 1.6, c_[1] - dy_ * 3.6 + math.sin(ha) * 1.6, 0.2),
                     (c_[0] - dx_ * 3.0 - math.cos(ha) * 1.6, c_[1] - dy_ * 3.0 - math.sin(ha) * 1.6, 0.2),
                     (c_[0] + dx_ * 3.0 - math.cos(ha) * 1.6, c_[1] + dy_ * 3.0 - math.sin(ha) * 1.6, 0.2)])
    cv.shape(head_, IRON.darker(0.9), z=-11.7, sd=1.0, hi=0.45)
    _hand(cv, e, h, SKIN, -11.6, near=False)
    # ---- bacaklar: şalvar + çizme
    for dx, zz, m in ((3.4, -9, PANTS.darker(0.75)), (-3.0, -2, PANTS)):
        top_ = (hip[0] + dx * 0.55, hip[1])
        knee = (hip[0] + dx * 0.95, hip[1] + 11.0)
        ft = (hip[0] + dx * 1.1, -0.2)
        leg = cv.limb([top_, lerp2(top_, knee, 0.5), knee, lerp2(knee, ft, 0.45)], [4.0, 4.2, 3.4, 3.6])
        cv.shape(leg, m, z=zz, sd=1.8, details=cv.fold([lerp2(top_, knee, 0.3), lerp2(top_, knee, 0.75), lerp2(knee, ft, 0.25)], 0.5, 1.0, 1))
        bt = BOOT if zz > -5 else BOOT.darker(0.75)
        boot = cv.blob([(ft[0] + 2.8, ft[1] - 7.6), (ft[0] - 3.0, ft[1] - 7.6), (ft[0] - 3.4, ft[1] - 2.6), (ft[0] - 6.0, ft[1] - 1.8),
                        (ft[0] - 7.0, ft[1] + 0.2, 0.0), (ft[0] + 3.0, ft[1] + 0.2, 0.0)])
        cv.shape(boot, bt, z=zz + 0.3, sd=1.2, hi=0.3,
                 details=[('stroke', [(ft[0] - 3.0, ft[1] - 6.8), (ft[0] + 2.6, ft[1] - 6.8)], 1.1, LEATHER.hi, (0.1, 0.1))])
    # ---- kaftan: yeşil, kısa (dize dek), firuze-altın kenar
    sk = math.sin(ph) * 0.35
    coat = cv.blob([(neck[0] - 5.0, neck[1] + 2.0), (neck[0] + 5.4, neck[1] + 1.8), (hip[0] + 7.0, hip[1] - 3.0), (hip[0] + 8.2 + sk, hip[1] + 10.6, 0.0),
                    (hip[0] + 1.6 + sk, hip[1] + 11.6), (hip[0] - 4.0 + sk, hip[1] + 11.0), (hip[0] - 8.6 + sk, hip[1] + 11.2, 0.0), (hip[0] - 7.0, hip[1] - 2.6)])
    det = cv.fold([(hip[0] + 3.6, hip[1] - 6.0), (hip[0] + 4.8, hip[1] + 3.0), (hip[0] + 5.2 + sk, hip[1] + 10.0)], 1.0, 1.2, 1)
    det += cv.fold([(hip[0] - 2.6, hip[1] - 1.0), (hip[0] - 3.4, hip[1] + 5.0), (hip[0] - 3.2 + sk, hip[1] + 10.5)], 0.8, 1.1, -1)
    # etek ucu: firuze bant + altın nokta
    hem = [(hip[0] - 8.4 + sk, hip[1] + 10.4), (hip[0] - 4.0 + sk, hip[1] + 10.2), (hip[0] + 1.6 + sk, hip[1] + 10.8), (hip[0] + 8.0 + sk, hip[1] + 9.8)]
    det.append(('stroke', hem, 2.0, TURQ.base, (0.02, 0.02)))
    for t in (0.15, 0.4, 0.65, 0.9):
        q0 = lerp2(hem[0], hem[-1], t)
        det.append(('col', cv.ellipse((q0[0], q0[1] + 0.2), 0.5, 0.5), GOLD.hi))
    cv.shape(coat, KAFTAN_G, z=0, sd=3.6, details=det, hatch=0.25, bounce=0.35)
    # ön açıklık: firuze şerit
    edge = [(neck[0] - 3.2, neck[1] + 1.6), (hip[0] - 3.4, hip[1] - 3.0), (hip[0] - 5.6 + sk, hip[1] + 11.0)]
    cv.shape(ik.isect(coat, ik.taper_path([cv.W(q) for q in edge], cv.u(1.6), prof=lambda s: 1.0)), TURQ, z=0.2, sd=0.5, ol=0.5)
    # ---- deri önlük: göğüsten dize, is lekeleri, kalem cebi
    apron = cv.blob([(neck[0] - 3.6, neck[1] + 3.6), (neck[0] + 1.8, neck[1] + 3.2), (hip[0] + 3.0, hip[1] - 3.6), (hip[0] + 3.8 + sk, hip[1] + 12.4, 0.0),
                     (hip[0] - 8.0 + sk, hip[1] + 12.8, 0.0), (hip[0] - 7.2, hip[1] - 2.0)])
    adet = cv.fold([(hip[0] - 3.6, hip[1] - 1.0), (hip[0] - 4.2, hip[1] + 5.0), (hip[0] - 3.6 + sk, hip[1] + 12.0)], 0.8, 1.2, 1)
    adet += [('col', cv.ellipse((hip[0] - 5.0, hip[1] + 5.0), 1.0, 0.7), (0.2, 0.12, 0.1)),
             ('col', cv.ellipse((hip[0] - 1.2, hip[1] + 8.6), 0.7, 0.5), (0.2, 0.12, 0.1)),
             ('ink', [(neck[0] - 2.6, neck[1] + 6.4), (neck[0] - 0.8, neck[1] + 7.2)], 0.9, (0.2, 0.2))]
    cv.shape(apron, APRON, z=1.0, sd=2.8, hi=0.3, details=adet, cast=0.7, bounce=0.3)
    cv.shape(cv.limb([(neck[0] - 3.2, neck[1] + 3.8), (neck[0] + 3.4, neck[1] + 2.8)], [0.7, 0.7]), APRON.darker(0.8), z=1.1, sd=0.5, ol=0.8)
    # kalem cebi: üç çelik nakış kalemi
    pk = (neck[0] - 1.6, neck[1] + 8.0)
    cv.shape(cv.blob([(pk[0] - 2.6, pk[1] - 0.4, 0.0), (pk[0] + 2.6, pk[1] - 0.4, 0.0), (pk[0] + 2.4, pk[1] + 3.6, 0.0), (pk[0] - 2.4, pk[1] + 3.6, 0.0)]),
             APRON.darker(0.85), z=1.2, sd=0.5, ol=0.8)
    for j, x in enumerate((-1.6, 0.0, 1.6)):
        cv.shape(cv.capsule((pk[0] + x, pk[1] - 0.2), (pk[0] + x + 0.3, pk[1] - 3.2 - (j % 2) * 0.8), 0.35, 0.3), STEEL, z=1.15, sd=0.2, ol=0.6)
    # kuşak + sarkan uç
    belt = ik.isect(coat, cv.blob([(hip[0] - 8.4, hip[1] - 4.4, 0.0), (hip[0] + 8.2, hip[1] - 4.8, 0.0), (hip[0] + 8.2, hip[1] - 2.2, 0.0), (hip[0] - 8.4, hip[1] - 1.8, 0.0)]))
    cv.shape(belt, SASH, z=1.4, sd=0.6, hi=0.2, ol=0.7,
             details=[('ink', [(hip[0] - 6.6 + j * 2.6, hip[1] - 4.2), (hip[0] - 6.0 + j * 2.6, hip[1] - 2.1)], 0.6, (0.1, 0.1)) for j in range(6)])
    knot = chain((hip[0] + 5.0, hip[1] - 2.4), 3, 2.2, math.pi * 0.5 + math.sin(ph) * 0.08, 0.04, ph, 0.12)
    cv.shape(ik.taper_path([cv.W(q) for q in knot], cv.u(1.4), (0.05, 0.3)), SASH, z=1.45, sd=0.5, ol=0.8)
    tassel(cv, knot[-1][0], knot[-1][1], 2.6, 1.4, GOLD, 1.46, sway=math.sin(ph) * 0.1, strands=4)
    # ---- baş: genç yüz, bakır saç (önden geriye taralı, alın bandı), firuze boncuk, küpe
    cv.shape(cv.limb([neck, (hx + 0.5, hy + 3.0)], [2.0, 2.0]), SKIN, z=2.0, sd=1.0)
    hair = cv.blob([(hx + 4.2, hy - 3.4), (hx + 0.4, hy - 5.6), (hx - 3.4, hy - 4.6), (hx - 2.2, hy - 3.2), (hx + 1.0, hy - 2.6), (hx + 2.2, hy + 0.6),
                    (hx + 2.6, hy + 2.6), (hx + 4.4, hy + 1.0), (hx + 5.2, hy - 1.4)])
    hdt = [('ink', [(hx + 0.6, hy - 4.8), (hx + 2.6, hy - 2.4), (hx + 3.4, hy + 0.8)], 1.0, (0.2, 0.6)),
           ('ink', [(hx - 1.6, hy - 4.6), (hx + 0.8, hy - 3.6), (hx + 2.0, hy - 1.2)], 0.9, (0.2, 0.6)),
           ('stroke', [(hx - 0.6, hy - 5.0), (hx + 1.8, hy - 4.0)], 0.9, HAIR_C.hi, (0.2, 0.6))]
    cv.shape(hair, HAIR_C, z=2.2, sd=1.6, hi=0.4, details=hdt, bounce=0.3)
    _face(cv, hd, SKIN, 2.1, mouth=talk * 0.7)
    # yanak kızarıklığı ve is lekesi
    cv.fill(cv.ellipse((hx - 1.8, hy + 1.2), 1.0, 0.55), (0.95, 0.55, 0.5), z=2.16, alpha=0.4)
    cv.fill(cv.ellipse((hx - 0.4, hy + 3.4), 0.8, 0.45), (0.2, 0.12, 0.1), z=2.17, alpha=0.55)
    # ön perçem
    st = chain((hx - 0.4, hy - 4.6), 4, 1.6, math.pi * 0.72, 0.05, ph, 0.05)
    cv.shape(ik.taper_path([cv.W(q) for q in st], cv.u(1.3), (0.1, 0.7)), HAIR_C, z=2.3, sd=0.5, hi=0.3, ol=0.7)
    # alın bandı (deri) + firuze boncuk
    band = cv.blob([(hx - 4.4, hy - 2.6), (hx - 0.6, hy - 3.8), (hx + 4.4, hy - 3.2), (hx + 4.6, hy - 2.0), (hx + 0.2, hy - 2.6), (hx - 4.2, hy - 1.6)])
    cv.shape(band, BRACER, z=2.8, sd=0.5, hi=0.25, ol=0.8)
    cv.fill(cv.ellipse((hx - 2.6, hy - 2.6), 0.75, 0.75), TURQ.base, z=2.9)
    cv.fill(cv.ellipse((hx - 2.75, hy - 2.75), 0.28, 0.28), (1, 1, 1), z=2.91)
    ea = (hx + 2.8, hy + 1.6)
    cv.shape(cv.limb([ea, (ea[0] + 0.1, ea[1] + 1.6)], [0.25, 0.25]), GOLD, z=2.17, sd=0.2, ol=0.5)
    cv.shape(cv.ellipse((ea[0] + 0.1, ea[1] + 2.4), 0.7, 0.9), TURQ, z=2.18, sd=0.3, hi=0.3, ol=0.6)
    # ---- ön kol: sıvalı yen, deri bilek koruyucu, nakış kalemi (ucu Kut ışığı)
    sh_f = (neck[0] - 3.4, neck[1] + 3.2)
    af = p.get('af', (-0.55, 0.9))
    e2, h2 = fk_arm(sh_f, af[0], af[1], 8.8, 8.2)
    out['hand'] = h2
    _sleeve(cv, sh_f, e2, h2, KAFTAN_G, 13, rolled=True, skin=SKIN)
    # bilek koruyucu
    cv.shape(cv.blob([along(e2, h2, 0.55, 2.3), along(e2, h2, 0.92, 2.1), along(e2, h2, 0.92, -2.0), along(e2, h2, 0.55, -2.2)]),
             BRACER, z=13.3, sd=0.8, hi=0.3, ol=0.85,
             details=[('ink', [along(e2, h2, t, 2.1), along(e2, h2, t, -2.0)], 0.6, (0.1, 0.1)) for t in (0.66, 0.8)])
    # kalem: elden sola-yukarı (konuşurken öne, yatay)
    ka = -math.pi * (0.72 - 0.22 * show) + math.sin(ph) * 0.02
    kd = (math.cos(ka), math.sin(ka))
    k0 = (h2[0] - kd[0] * 3.0, h2[1] - kd[1] * 3.0)
    k1 = (h2[0] + kd[0] * 9.5, h2[1] + kd[1] * 9.5)
    cv.shape(cv.limb([k0, lerp2(k0, k1, 0.6), k1], [1.0, 0.9, 0.5]), STEEL, z=14.4, sd=0.5, hi=0.5,
             details=[('ink', [lerp2(k0, k1, 0.2), lerp2(k0, k1, 0.24)], 0.8), ('ink', [lerp2(k0, k1, 0.3), lerp2(k0, k1, 0.34)], 0.8)])
    cv.shape(cv.ellipse(k0, 1.1, 1.1), GOLD, z=14.45, sd=0.3, hi=0.3, ol=0.6)
    # uç: tamga damgası + Kut ışığı (nefes alır)
    gl = 0.75 + 0.25 * math.sin(ph * 2.0)
    tip = (k1[0] + kd[0] * 1.2, k1[1] + kd[1] * 1.2)
    cv.fill(cv.ellipse(tip, 1.4 * gl, 1.4 * gl), KUT, z=14.5, glow=(KUT_GL[0] * gl, KUT_GL[1] * gl, KUT_GL[2] * gl))
    cv.fill(cv.ellipse(tip, 0.6, 0.6), (1, 1, 1), z=14.55, glow=(0.6, 1.0, 1.0))
    for j in range(3):
        a = ph * 1.5 + j * math.tau / 3
        r = 3.0 + math.sin(ph * 2 + j) * 0.5
        qq = (tip[0] + math.cos(a) * r, tip[1] + math.sin(a) * r * 0.6)
        cv.fill(cv.blob([(qq[0], qq[1] - 0.6, 0.0), (qq[0] + 0.35, qq[1], 0.0), (qq[0], qq[1] + 0.6, 0.0), (qq[0] - 0.35, qq[1], 0.0)]), KUT,
                z=14.6 if math.sin(a) > 0 else 13.9, glow=KUT_GL)
    _hand(cv, e2, h2, SKIN, 14)
    return out


def _pose(anim, t):
    s = math.sin(t * math.tau)
    c = math.cos(t * math.tau)
    p = dict(bob=0.6 * s, lean=0.02 * s, ph=t * math.tau)
    # idle: kalem göğüs hizasında (inceliyor), çekiç omuzda hafif salınır
    p.update(af=(-0.5, 1.15 + 0.03 * s), ab=(0.42 + 0.03 * s, -2.25 + 0.04 * c), hang=-1.3 + 0.05 * s)
    if anim == 'talk':
        # "Göster bakalım yiğit": kalem öne uzanır, çekiç kalkar, hafif öne eğilir
        p.update(talk=1.0 if t < 0.5 else 0.55, lean=0.05, show=0.75 + 0.25 * s, af=(-1.05 - 0.1 * s, 0.75),
                 ab=(0.1 + 0.05 * s, -2.55 + 0.08 * c), hang=-1.55 + 0.06 * s)
    return p


SHADE = dict(outer=0.5, rim=0.45, rim_col=(1.0, 0.86, 0.66), rim_dir=(0.6, -0.8), rim_w=1.3, form=(6.0, (0.8, 0.78, 0.9)))


def render_frame(anim, i, ss=3):
    n = NPC_ANIMS[anim][0]
    p = _pose(anim, i / n)
    cv = ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss)
    info = draw_usta(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info


ANIMS = {k: (v[0], None, True, True) for k, v in NPC_ANIMS.items()}


# ------------------------------------------------------------ konak ateşi (süs)
def konak_ates():
    """Taş halkalı konak ateşi: çapraz odunlar, harlı alev, közler; yanında minderler, kıl çuval, sacayakta çaydanlık."""
    P = Prop(120, 70, 60, 66)
    cv = P.cv
    rng = np.random.default_rng(32)
    # arka taşlar
    for i, x in enumerate((-20, -10, 0, 10, 20)):
        w = rng.uniform(4.0, 5.5)
        cv.shape(cv.blob([(x - w, -4.5, 0.0), (x - w * 0.7, -8.5 - (i % 2)), (x + w * 0.6, -8.0 - (i % 2) * 0.5), (x + w, -4.0, 0.0)]),
                 STONE_D, z=-1.0 + i * 0.01, sd=1.2, hi=0.3)
    # odunlar (çapraz)
    for a, zz, m in ((-0.35, 0.0, WOOD_D), (0.4, 0.05, WOOD), (0.05, 0.1, WOOD_D)):
        cv.shape(cv.capsule((-13 * math.cos(a), -5 + 5 * math.sin(a)), (13 * math.cos(a), -5 - 5 * math.sin(a)), 2.2, 2.0), m, z=zz, sd=1.0,
                 details=[('ink', [(-6 * math.cos(a), -5 + 2 * math.sin(a)), (4 * math.cos(a), -5 - 2 * math.sin(a))], 0.6, (0.3, 0.3))])
    # közler
    for k in range(7):
        x = -9 + k * 3
        cv.fill(cv.ellipse((x, -7.0 + (k % 2) * 0.8), 1.6, 0.9), (1.0, 0.5 + 0.05 * k, 0.15), z=0.15, glow=(1.0, 0.45, 0.1))
    flame(cv, 0, -8, 30, 22, 0.2, seed=11)
    flame(cv, -7, -8, 18, 12, 0.22, seed=12, lick=-0.25)
    flame(cv, 8, -8, 20, 12, 0.24, seed=13, lick=0.25)
    # ön taşlar
    for i, x in enumerate((-22, -12, -1, 10, 21)):
        w = rng.uniform(4.0, 5.6)
        cv.shape(cv.blob([(x - w, 0.5, 0.0), (x - w * 0.8, -4.0 - (i % 2) * 0.6), (x + w * 0.5, -4.6), (x + w, 0.5, 0.0)]), STONE,
                 z=0.5 + i * 0.01, sd=1.4, hi=0.45, details=[('ink', [(x - w * 0.4, -2.0), (x + w * 0.3, -1.4)], 0.6, (0.3, 0.3))])
    # ateşin taşlara düşen ışığı
    cv.fill(cv.ellipse((0, -2), 26, 5), (1.0, 0.5, 0.18), z=0.6, alpha=0.3, glow=(0.4, 0.15, 0.03))
    # sacayak + bakır çaydanlık (sağda, ateşin kenarında)
    for f in (-1, 1):
        cv.shape(cv.capsule((22 + f * 6, 0), (24 + f * 1.5, -18), 0.8, 0.7), IRON, z=0.7, sd=0.4, ol=0.7)
    cv.shape(cv.capsule((24, -18), (24, -21), 0.6, 0.6), IRON, z=0.72, sd=0.3, ol=0.7)
    pot = cv.blob([(18, -14, 0.0), (30, -14, 0.0), (31, -9), (28, -5), (24, -4.2), (20, -5), (17, -9)])
    cv.shape(pot, COPPER, z=0.8, sd=2.4, hi=0.6, bounce=0.3)
    cv.shape(cv.ellipse((24, -14), 6.2, 1.5), COPPER, z=0.85, sd=0.5, hi=0.4)
    cv.stroke([(30, -11), (34, -13), (35, -16)], 1.4, z=0.82, col=COPPER.shadow, taper=(0.1, 0.4))
    cv.stroke([(18, -14), (21, -19), (27, -19), (30, -14)], 1.0, z=0.78, col=INK)
    cv.stroke([(24, -22), (23, -27), (25, -31)], 1.2, z=0.75, col=(0.7, 0.7, 0.76), taper=(0.2, 0.9), alpha=0.35)
    # minderler (sol) + kıl çuval
    for x, m, m2 in ((-44, RED, GOLD), (-33, BLUE, FELT_C)):
        cush = cv.blob([(x - 8, 0.5, 0.0), (x - 8.5, -4), (x - 5, -6.5), (x + 5, -6.5), (x + 8.5, -4), (x + 8, 0.5, 0.0)])
        cv.shape(cush, m, z=0.3, sd=1.4, hi=0.3, details=[('col', cv.blob(diamond(x, -3.2, 2.6, 1.6)), m2.base),
                                                            ('ink', [(x - 7, -2.0), (x + 7, -2.0)], 0.6, (0.1, 0.1))])
    sack = cv.blob([(-56, 0.5, 0.0), (-57, -10), (-54, -16), (-48, -17), (-43, -14), (-42, -6), (-41, 0.5, 0.0)])
    cv.shape(sack, ROPE, z=0.2, sd=2.0, hi=0.4, details=cv.fold([(-52, -14), (-50, -8), (-51, -2)], 0.7, 1.0, 1) +
             [('stroke', [(-55, -15), (-49, -17.5), (-44, -15)], 1.0, ROPE.shadow, (0.1, 0.1))])
    cv.shape(cv.blob([(-52, -16, 0.0), (-47, -18.5), (-44, -15.5, 0.0), (-48, -14.5)]), FELT_C, z=0.25, sd=0.5, ol=0.6)
    grass_tufts(cv, -58, 56, 0, 30, 3.0, 33)
    return P.done(outer=1.1, rim=0.32)


# ------------------------------------------------------------ Bengisu'nun gezgin tezgâhı (süs)
def usta_tezgah():
    """Kütükte küçük örs (üstünde nakışlanan kılıç, runları ışır), taşınabilir kor mangalı (körüklü), deri alet dürüsü,
    asılı muskalar, yük sepeti. Köken: örs kütüğünün ayağı; Bengisu kütüğün 26 birim sağında durur (STAND_X)."""
    P = Prop(132, 92, 60, 88)
    cv = P.cv
    # ---- asılı muska / çaput çubuğu (arkada): iki kazık arasında ip
    for x in (-54, 6):
        cv.shape(cv.capsule((x, 0), (x - 1.0, -60), 1.3, 1.1), WOOD_D, z=-2.0, sd=0.8, hi=0.3)
    cv.stroke([(-55, -58), (-30, -53), (-5, -57)], 0.9, z=-1.9, col=ROPE.shadow, taper=(0.02, 0.02))
    for i, (x, m) in enumerate(((-47, RED), (-39, TURQ), (-31, GOLD), (-23, BLUE), (-14, RED))):
        y0 = -57 + (1 - abs(x + 30) / 25.0) * 4.0
        if i % 2 == 0:   # çaput
            cv.shape(cv.blob([(x - 1.4, y0, 0.0), (x + 1.4, y0, 0.0), (x + 2.4, y0 + 9), (x - 0.4, y0 + 11, 0.0), (x - 2.4, y0 + 8)]), m, z=-1.8, sd=0.8, hi=0.3)
        else:            # demir muska (üçgen) + boncuk
            cv.stroke([(x, y0), (x, y0 + 4)], 0.7, z=-1.8, col=INK)
            cv.shape(cv.blob([(x - 2.2, y0 + 4, 0.0), (x + 2.2, y0 + 4, 0.0), (x, y0 + 9, 0.0)]), IRON, z=-1.75, sd=0.6, hi=0.4, ol=0.8)
            cv.fill(cv.ellipse((x, y0 + 6), 0.7, 0.7), m.base, z=-1.7)
    # ---- yük sepeti (en solda, arkada)
    bask = cv.blob([(-58, 0.5, 0.0), (-59, -22), (-56, -26), (-40, -26), (-37, -22), (-38, 0.5, 0.0)])
    bdet = [('ink', [(-57, y), (-39, y)], 0.6, (0.05, 0.05)) for y in range(-24, -2, 4)]
    bdet += [('ink', [(x, -25), (x + 1, -1)], 0.6, (0.05, 0.05)) for x in (-53, -48, -43)]
    cv.shape(bask, ROPE.darker(0.9), z=-1.0, sd=2.4, hi=0.4, details=bdet)
    cv.shape(cv.blob([(-56, -26, 0.0), (-50, -31), (-44, -28), (-40, -26, 0.0)]), FELT_C, z=-0.95, sd=0.8, ol=0.6)
    cv.shape(cv.capsule((-52, -30), (-46, -40), 0.8, 0.6), WOOD, z=-0.96, sd=0.3, ol=0.6)   # sepetten çıkan sap
    # ---- kor mangalı (solda, önde): tunç tas üç ayakta, ışıyan kömür, deri körük hortumu
    mx = -24
    for f in (-1, 0, 1):
        cv.shape(cv.blob([(mx + f * 2, -12), (mx + f * 8, -1.5), (mx + f * 9, 0.4, 0.0), (mx + f * 6.5, 0.4, 0.0), (mx + f * 1, -7)]), BRONZE,
                 z=0.1 + 0.02 * f, sd=0.9, hi=0.3)
    bowl = cv.blob([(mx - 12, -22, 0.0), (mx + 12, -22, 0.0), (mx + 9, -14), (mx, -11.5), (mx - 9, -14)])
    cv.shape(bowl, BRONZE, z=0.5, sd=2.6, hi=0.6, details=[('stroke', [(mx - 10, -20.5), (mx + 10, -20.5)], 0.9, GOLD.hi, (0.1, 0.1))])
    cv.shape(cv.ellipse((mx, -22), 12, 2.0), Ink('#3a2420', '#1e1218', '#5a3828'), z=0.45, sd=0.5, ol=0.7)
    for k in range(6):
        x = mx - 8 + k * 3.2
        cv.fill(cv.ellipse((x, -22.6 + (k % 2) * 0.5), 1.8, 1.0), (1.0, 0.45 + 0.07 * k, 0.12), z=0.55, glow=(1.0, 0.4, 0.08))
    cv.fill(cv.ellipse((mx, -23), 9, 2.2), (1.0, 0.6, 0.2), z=0.56, alpha=0.5, glow=(0.8, 0.3, 0.05))
    flame(cv, mx - 2, -23, 9, 7, 0.6, seed=21, lick=-0.1)
    flame(cv, mx + 4, -23, 7, 5, 0.62, seed=22, lick=0.2)
    # körük: deri torba + hortum (mangala)
    bell = cv.blob([(mx - 30, -4), (mx - 28, -12), (mx - 20, -14), (mx - 14, -10), (mx - 16, -3), (mx - 24, -1)])
    cv.shape(bell, LEATHER, z=0.3, sd=1.6, hi=0.3, details=cv.fold([(mx - 26, -11), (mx - 22, -7), (mx - 20, -3)], 0.6, 1.0, 1))
    cv.shape(cv.capsule((mx - 32, -8), (mx - 36, -16), 1.0, 0.9), WOOD, z=0.32, sd=0.4, ol=0.7)
    cv.stroke([(mx - 15, -10), (mx - 11, -14), (mx - 9, -17)], 1.6, z=0.28, col=LEATHER.shadow, taper=(0.1, 0.1))
    # ---- kütük + küçük örs (köken: kütük ayağı)
    stump = cv.blob([(-10, 0.5, 0.0), (-11, 1.2, 0.0), (-9.5, -6), (-8.5, -16, 0.0), (8.5, -16, 0.0), (9.5, -6), (11, 1.2, 0.0), (10, 0.5, 0.0)])
    cv.shape(stump, WOOD, z=1.0, sd=3.8, hi=0.6, details=[('ink', [(x, -15), (x + 0.5, -2)], 0.6) for x in (-5, 0, 5)])
    cv.shape(cv.ellipse((0, -16), 8.6, 1.9), Ink('#b08a5c', '#6a4c34', '#dcb88a'), z=1.1, sd=0.5, ol=0.6,
             details=[('ink', [(-5, -16), (0, -15.3), (5, -16)], 0.5)])
    anvil = cv.blob([(-5, -16, 0.0), (-3.5, -19.5, 0.0), (-10, -20.8), (-16, -24, 0.0), (-5, -25, 0.0), (11, -25, 0.0), (11, -21.5, 0.0), (5, -19.5, 0.0), (6, -16, 0.0)])
    cv.shape(anvil, IRON, z=1.3, sd=2.2, hi=0.6)
    # nakışlanan kılıç: örs üstünde, kabza sağda; üstünde ışıyan Kut runları
    blade = cv.blob([(-16, -26.6, 0.0), (6, -27.4), (9, -26.9, 0.0), (6, -25.8), (-16, -25.5, 0.0)])
    cv.shape(blade, STEEL, z=1.4, sd=0.6, hi=0.5, details=[('stroke', [(-14, -26.4), (4, -26.8)], 0.5, (1, 1, 1), (0.2, 0.5))])
    cv.shape(cv.blob([(9, -28.4, 0.0), (10.4, -28.4, 0.0), (10.4, -24.2, 0.0), (9, -24.2, 0.0)]), GOLD, z=1.45, sd=0.3, hi=0.3, ol=0.7)
    cv.shape(cv.capsule((10.4, -26.4), (16, -26.2), 0.9, 0.9), LEATHER, z=1.42, sd=0.4, ol=0.8)
    for x, st in ((-11, [(-0.8, 0.8), (0.0, -0.8), (0.8, 0.8)]), (-6, [(-0.7, -0.8), (0.7, 0.8)]), (-1, [(0.0, -0.9), (0.0, 0.9), (-0.7, 0.2)])):
        cv.stroke([(x + a, -26.5 + b * 0.7) for a, b in st], 0.7, z=1.5, col=(0.5, 1.0, 0.95), taper=(0.1, 0.1), glow=(0.3, 0.95, 1.0))
    # örste duran küçük çekiç
    cv.shape(cv.capsule((12, -16), (18, -6), 0.9, 0.8), WOOD, z=1.5, sd=0.4, ol=0.7)
    cv.shape(cv.blob([(9.5, -19, 0.0), (15.5, -20.5, 0.0), (16.5, -16.5, 0.0), (10.5, -15, 0.0)]), IRON, z=1.55, sd=0.8, hi=0.3)
    # ---- deri alet dürüsü (örsün sağında yere serili): kalemler, eğe, maşa
    roll = cv.blob([(20, 0.5, 0.0), (19, -2.4, 0.0), (46, -3.0, 0.0), (47, 0.5, 0.0)])
    cv.shape(roll, LEATHER, z=0.9, sd=1.0, hi=0.3, details=[('ink', [(21, -1.5), (45, -2.0)], 0.6, (0.05, 0.05))])
    for i, x in enumerate((22, 26, 30)):
        cv.shape(cv.capsule((x, -2.5), (x + 0.8, -8.0 - (i % 2) * 1.5), 0.4, 0.3), STEEL, z=0.95, sd=0.2, ol=0.6)
        cv.shape(cv.capsule((x, -2.5), (x + 0.3, -4.2), 0.55, 0.5), WOOD, z=0.96, sd=0.2, ol=0.6)
    cv.shape(cv.blob([(34, -2.6, 0.0), (35.2, -10.5), (36.4, -2.6, 0.0)]), IRON, z=0.95, sd=0.4, ol=0.7,
             details=[('ink', [(34.6, -8), (36, -8)], 0.4), ('ink', [(34.5, -6), (36, -6)], 0.4), ('ink', [(34.4, -4), (36.1, -4)], 0.4)])
    for f in (-1, 1):
        cv.stroke([(41, -2.5), (41 + f * 1.4, -7.5), (41 + f * 0.5, -11)], 1.2, z=0.95, col=IRON.base, taper=(0.1, 0.2))
    cv.shape(cv.capsule((44, -3), (48, -3), 1.4, 1.4), ROPE, z=0.92, sd=0.4, ol=0.7)   # dürülmüş uç
    # kıvılcım izleri (mangaldan yükselen kor, ışır)
    rng = np.random.default_rng(5)
    for k in range(6):
        x, y = mx + rng.uniform(-6, 6), -28 - rng.uniform(0, 16)
        cv.fill(cv.ellipse((x, y), 0.5, 0.5), (1.0, 0.75, 0.3), z=0.7, glow=(1.0, 0.5, 0.1))
    grass_tufts(cv, -60, 60, 0, 28, 3.0, 36)
    return P.done(outer=1.1, rim=0.32)


ALL = {'konak_ates': konak_ates, 'usta_tezgah': usta_tezgah}
STAND_X = 26.0   # Bengisu'nun tezgâh kökenine (kütük) göre durduğu yer (dünya; Level._place_konak ile aynı)


if __name__ == '__main__':
    # önizleme: python usta_ink.py out.png -> tezgâh, ateş ve Bengisu idle/talk kareleri koyu zeminde
    import sys
    from PIL import Image
    out = sys.argv[-1] if sys.argv[-1].endswith('.png') else 'usta_on.png'
    props = [usta_tezgah(), konak_ates()]
    frames = [render_frame('idle', i) for i in (0, 2, 4)] + [render_frame('talk', i) for i in (0, 2)]
    fw = frames[0][0].shape[1]
    pw = sum(p[0].shape[1] for p in props) + 20 * len(props)
    Wd = pw + 40 + len(frames) * (fw + 10)
    Hd = max(max(p[0].shape[0] for p in props), frames[0][0].shape[0]) + 40
    bg = np.zeros((Hd, Wd, 3), np.float32)
    bg[:] = (0.09, 0.1, 0.16)

    def put(r, g, x, y):
        h, w = r.shape[:2]
        a = r[..., 3:4]
        bg[y:y + h, x:x + w] = bg[y:y + h, x:x + w] * (1 - a) + r[..., :3] * a
        if g is not None:
            bg[y:y + h, x:x + w] += g[..., :3] * g[..., 3:4] * 0.8
    x = 20
    for rgba, glow, org in props:
        put(rgba, glow, x, Hd - 20 - rgba.shape[0])
        x += rgba.shape[1] + 20
    x = pw + 40
    for r in frames:
        em = r[2]
        put(r[0], np.concatenate([em[..., :3] / np.maximum(em[..., 3:4], 1e-4), em[..., 3:4]], -1), x, Hd - 20 - r[0].shape[0])
        x += fw + 10
    Image.fromarray((np.clip(bg, 0, 1) * 255).astype(np.uint8)).save(out)
    print('önizleme', out, bg.shape)
