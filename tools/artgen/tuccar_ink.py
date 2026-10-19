"""v24 tüccar: Bezirgân Sartak ve kervan tezgâhı — stil v2 "mürekkep-cel" (inkkit.py / inkprop.py).

Eski Türkçede "sart" tüccar demektir; Dede Korkut'ta bezirgânlar diyar diyar dolaşıp beylere armağan getirir.
Sartak bozkırın yol tanıdık bezirgânıdır: Erlik'in karanlığında bile kervanı yürür, Kut'a değil altına bakar.

* npc_tuccar_v2 (NPC sayfası, npc_ink.py ile aynı düzen: idle 6 kare 8 fps, talk 4 kare 10 fps; yüz SOLA, ayak (0, 0)):
  yanık tenli, orta yaşlı, sarkık kara-kır bıyıklı kurnaz bezirgân. Kürk kenarlı uzun sivri lacivert keçe börk (tepede
  kızıl püskül), çizgili ipek kaftan (safran / lacivert / kızıl alaca), altın kuşak ve kemerde sallanan sikke kesesi,
  ucu kalkık çizmeler. Sırtında ahşap çatkılı büyük yük küfesi: dürülmüş kilimler, bakır güğüm, tepede kancalı fener
  (ışır). Ön elinde tunç terazi (kefeler idle'da salınır, kefede altın sikkeler ışır); konuşurken arka eli "buyur"
  diye açılır, terazi öne kalkar.
* bezirgan_kervan_v2 (süs, sus_v2.json): çöken iki hörgüçlü deve (yük denkleri, kızıl keçe çul, boyun çıngırağı),
  yere serili kilim üstünde mallar (sehpada kılıç, yay, kalkan, küpler, mühürlü tomar, sikke yığını), solda fener
  direği ve kızıl-sarı flama. Tüccar kilimin ortasında, devenin önünde durur.
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_arm, lerp2, chain
from bengu_ink import along
from yurt import NPC_ANIMS
from npc_ink import _face, _hand, _sleeve, SKIN_D, GOLD, IRON, BOOT, CELL, FEET, TEX
import inkprop as P_
from inkprop import (Prop, FELT, FELT_C, RED, RED_D, BLUE, TURQ, BRONZE, WOOD, WOOD_D, WOOD_R, STEEL, LEATHER, HAIR_K,
                     ROPE, COPPER, diamond, tassel, grass_tufts)

# ------------------------------------------------------------ malzemeler
SILK_Y = Ink('#d89a34', '#8a4a2a', '#ffd88a', '#4e2420', name='safran ipek')
SILK_B = Ink('#2e4a8c', '#18224c', '#5a7ec8', '#0e1430', name='lacivert ipek')
SILK_R = Ink('#a8302c', '#561428', '#de5a46', name='kızıl ipek')
HAT = Ink('#2a3a6a', '#141c3a', '#4e68a8', '#0a0e22', name='lacivert keçe')
FUR = Ink('#8a6440', '#40281e', '#c4966a', '#24140e', kind='fur', name='samur kürk')
SASH = Ink('#e0b04a', '#8e5a22', '#fff0b0', name='altın kuşak')
BEARD = Ink('#3a3236', '#18141a', '#7a6e72', name='kır bıyık')
PACK = Ink('#8a6a48', '#40302c', '#bc9a70', '#241a1a', name='küfe ahşabı')
COIN = (1.0, 0.82, 0.32)
COIN_GL = (1.0, 0.7, 0.2)
LAMP = (1.0, 0.7, 0.3)
LAMP_GL = (1.0, 0.56, 0.16)


def _rug_roll(cv, a, b, r, mat, stripe, z):
    """Dürülmüş kilim (iki ucu görünen silindir)."""
    body = cv.capsule(a, b, r, r)
    det = [('ink', [lerp2(a, b, t), (lerp2(a, b, t)[0] + 0.2, lerp2(a, b, t)[1] + r * 1.6)], 0.8, (0.1, 0.1)) for t in (0.3, 0.7)]
    det.append(('col', ik.isect(body, cv.capsule(lerp2(a, b, 0.45), lerp2(a, b, 0.55), r * 1.2, r * 1.2)), stripe.base))
    cv.shape(body, mat, z=z, sd=r * 0.9, hi=0.3, details=det)
    cv.shape(cv.ellipse(b, r * 0.45, r), mat.darker(0.8), z=z + 0.05, sd=0.4, ol=0.8,
             details=[('ink', [(b[0], b[1] - r * 0.5), (b[0] + 0.3, b[1]), (b[0], b[1] + r * 0.5)], 0.7)])


# ------------------------------------------------------------ Bezirgân Sartak (yüz sola)
def draw_tuccar(cv, p):
    bob, lean, ph = p.get('bob', 0.0), p.get('lean', 0.0), p.get('ph', 0.0)
    talk = p.get('talk', 0.0)
    hip = (0.0, -24.0 + bob * 0.3)
    neck = (hip[0] - math.sin(lean + 0.08) * 17.0, hip[1] - 17.0 + bob * 0.5)
    hd = (neck[0] - 1.6, neck[1] - 4.8)
    out = {'head': hd}
    # ---- sırt küfesi (gövdenin arkasında): ahşap çatkı, dürülmüş kilimler, bakır güğüm, tepede fener
    px0 = neck[0] + 5.0
    fr_top = neck[1] - 13.0
    for dx in (0.0, 11.0):   # iki dikme
        cv.shape(cv.capsule((px0 + dx, hip[1] + 10.0), (px0 + dx - 0.6, fr_top), 1.0, 0.9), PACK.darker(0.85 if dx else 1.0),
                 z=-16 + dx * 0.01, sd=0.6, hi=0.25)
    for yy in (fr_top + 3.0, hip[1] - 2.0, hip[1] + 7.0):   # kayıtlar
        cv.shape(cv.capsule((px0 - 1.0, yy), (px0 + 12.0, yy + 0.4), 0.8, 0.8), PACK, z=-15.9, sd=0.5, ol=0.8)
    _rug_roll(cv, (px0 + 0.5, fr_top + 8.0), (px0 + 13.5, fr_top + 7.4), 3.0, SILK_R, SASH, -15.5)
    _rug_roll(cv, (px0 + 0.8, fr_top + 14.6), (px0 + 14.0, fr_top + 14.0), 2.7, BLUE, RED, -15.4)
    _rug_roll(cv, (px0 + 0.5, hip[1] + 1.6), (px0 + 13.0, hip[1] + 1.2), 2.9, FELT_C, SILK_B, -15.3)
    # yük ipi
    cv.stroke([(px0 - 0.5, fr_top + 4.0), (px0 + 6.0, fr_top + 18.0), (px0 + 12.5, hip[1] + 4.0)], 1.0, z=-15.0, col=ROPE.shadow)
    # bakır güğüm (yanda asılı)
    gc = (px0 + 15.0, hip[1] - 4.0 + math.sin(ph) * 0.3)
    gug = cv.blob([(gc[0] - 2.0, gc[1] - 6.0), (gc[0] + 2.0, gc[1] - 6.0), (gc[0] + 3.6, gc[1] - 1.0), (gc[0] + 3.2, gc[1] + 3.0),
                   (gc[0], gc[1] + 4.2, 0.0), (gc[0] - 3.2, gc[1] + 3.0), (gc[0] - 3.6, gc[1] - 1.0)])
    cv.shape(gug, COPPER, z=-14.8, sd=1.4, hi=0.5, details=[('stroke', [(gc[0] - 2.6, gc[1] - 1.0), (gc[0] + 2.6, gc[1] - 1.0)], 0.8, GOLD.base, (0.1, 0.1))])
    cv.shape(cv.capsule((gc[0] - 1.0, gc[1] - 6.0), (gc[0] - 1.2, gc[1] - 9.0), 0.9, 1.1), COPPER, z=-14.85, sd=0.5, ol=0.8)
    # tepede kancalı fener (salınır, ışır)
    hk = (px0 + 5.0, fr_top - 1.0)
    sw = math.sin(ph) * 0.12
    lc = (hk[0] + 2.0 + math.sin(sw) * 5.0, hk[1] + 3.0)
    cv.stroke([(hk[0] + 2.0, hk[1] - 1.6), lc], 0.8, z=-15.7, col=INK)
    lamp = cv.blob([(lc[0] - 2.4, lc[1] + 1.0, 0.0), (lc[0] + 2.4, lc[1] + 1.0, 0.0), (lc[0] + 2.8, lc[1] + 5.0), (lc[0] + 2.2, lc[1] + 8.0, 0.0),
                    (lc[0] - 2.2, lc[1] + 8.0, 0.0), (lc[0] - 2.8, lc[1] + 5.0)])
    cv.shape(lamp, Ink('#f4b44e', '#c46a24', '#fff2c0'), z=-15.6, sd=0.8, hi=0.0, ol=0.7, glow=LAMP_GL)
    cv.fill(cv.ellipse((lc[0], lc[1] + 4.6), 1.0, 1.6), (1.0, 0.96, 0.8), z=-15.55, glow=(1.0, 0.85, 0.5))
    cv.shape(cv.blob([(lc[0] - 2.8, lc[1] + 1.2, 0.0), (lc[0], lc[1] - 1.2), (lc[0] + 2.8, lc[1] + 1.2, 0.0)]), BRONZE, z=-15.5, sd=0.5, ol=0.7)
    # ---- arka kol (kemerdeki keseye yaslı; konuşurken "buyur" diye açılır)
    sh_b = (neck[0] + 3.4, neck[1] + 3.0)
    ab = p.get('ab', (0.25, 0.9))
    e, h = fk_arm(sh_b, ab[0], ab[1], 9.0, 8.5)
    _sleeve(cv, sh_b, e, h, SILK_B.darker(0.8), -12, wide=1.0, near=False, cuff=SASH.darker(0.8))
    _hand(cv, e, h, SKIN_D, -11.6, open_=1.0 if talk > 0.3 else 0.0, near=False)
    # ---- bacaklar: çizgili şalvar + ucu kalkık çizme
    for dx, zz, m in ((3.4, -9, SILK_B.darker(0.72)), (-3.0, -2, SILK_B)):
        top_ = (hip[0] + dx * 0.5, hip[1])
        knee = (hip[0] + dx * 0.9, hip[1] + 11.0)
        ft = (hip[0] + dx * 1.1, -0.2)
        leg = cv.limb([top_, lerp2(top_, knee, 0.5), knee, lerp2(knee, ft, 0.45)], [4.2, 4.4, 3.6, 3.8])
        cv.shape(leg, m, z=zz, sd=1.8, details=cv.fold([lerp2(top_, knee, 0.3), lerp2(top_, knee, 0.75), lerp2(knee, ft, 0.25)], 0.5, 1.0, 1))
        bt = BOOT if zz > -5 else BOOT.darker(0.75)
        boot = cv.blob([(ft[0] + 2.8, ft[1] - 7.4), (ft[0] - 3.0, ft[1] - 7.4), (ft[0] - 3.4, ft[1] - 2.6), (ft[0] - 6.2, ft[1] - 2.0),
                        (ft[0] - 8.0, ft[1] - 3.8, 0.0), (ft[0] - 7.0, ft[1] + 0.2, 0.0), (ft[0] + 3.0, ft[1] + 0.2, 0.0)])
        cv.shape(boot, bt, z=zz + 0.3, sd=1.2, hi=0.3,
                 details=[('stroke', [(ft[0] - 3.0, ft[1] - 6.6), (ft[0] + 2.6, ft[1] - 6.6)], 1.2, GOLD.base, (0.1, 0.1))])
    # ---- kaftan: çizgili ipek (alaca), dize kadar; önü kuşakla bağlı
    sk = math.sin(ph) * 0.4
    coat = cv.blob([(neck[0] - 5.4, neck[1] + 2.0), (neck[0] + 5.8, neck[1] + 1.8), (hip[0] + 7.6, hip[1] - 3.0), (hip[0] + 9.0 + sk, hip[1] + 12.6, 0.0),
                    (hip[0] + 2.0 + sk, hip[1] + 13.8), (hip[0] - 4.0 + sk, hip[1] + 13.0), (hip[0] - 9.4 + sk, hip[1] + 13.2, 0.0), (hip[0] - 7.6, hip[1] - 2.6)])
    det = []
    # alaca şeritleri: aşağı inen hafif kavisli bantlar (safran zemin üstünde lacivert ve kızıl)
    for j, (x0, col) in enumerate(((-6.0, SILK_B), (-2.6, SILK_R), (0.8, SILK_B), (4.2, SILK_R), (7.4, SILK_B))):
        a = (neck[0] + x0 * 0.7, neck[1] + 1.0)
        b = (hip[0] + x0 * 1.15 + sk, hip[1] + 14.0)
        m_ = lerp2(a, b, 0.5)
        det.append(('stroke', [a, (m_[0] + 0.5, m_[1]), b], 2.4 if col is SILK_B else 1.6, col.base, (0.05, 0.05)))
    det += cv.fold([(hip[0] + 3.6, hip[1] - 6.0), (hip[0] + 5.0, hip[1] + 3.0), (hip[0] + 5.6 + sk, hip[1] + 12.0)], 1.0, 1.2, 1)
    det += cv.fold([(hip[0] - 3.0, hip[1] - 1.0), (hip[0] - 3.8, hip[1] + 6.0), (hip[0] - 3.6 + sk, hip[1] + 12.5)], 0.8, 1.1, -1)
    cv.shape(coat, SILK_Y, z=0, sd=3.8, details=det, hatch=0.25, bounce=0.35)
    # yaka ve ön açıklık: kızıl şerit
    edge = [(neck[0] - 3.4, neck[1] + 1.6), (hip[0] - 3.6, hip[1] - 3.0), (hip[0] - 6.0 + sk, hip[1] + 13.0)]
    cv.shape(ik.isect(coat, ik.taper_path([cv.W(q) for q in edge], cv.u(1.8), prof=lambda s: 1.0)), SILK_R, z=0.2, sd=0.5, ol=0.5)
    # altın kuşak + sarkan uç + sikke kesesi
    belt = ik.isect(coat, cv.blob([(hip[0] - 9.0, hip[1] - 4.4, 0.0), (hip[0] + 9.0, hip[1] - 4.8, 0.0), (hip[0] + 9.0, hip[1] - 2.2, 0.0), (hip[0] - 9.0, hip[1] - 1.8, 0.0)]))
    cv.shape(belt, SASH.darker(0.9), z=0.5, sd=0.6, hi=0.2, ol=0.7,
             details=[('ink', [(hip[0] - 7.0 + j * 2.6, hip[1] - 4.2), (hip[0] - 6.4 + j * 2.6, hip[1] - 2.1)], 0.6, (0.1, 0.1)) for j in range(6)])
    knot = chain((hip[0] - 5.4, hip[1] - 2.4), 3, 2.4, math.pi * 0.55 + math.sin(ph) * 0.08, 0.04, ph, 0.12)
    cv.shape(ik.taper_path([cv.W(q) for q in knot], cv.u(1.6), (0.05, 0.3)), SASH, z=0.55, sd=0.5, ol=0.8)
    tassel(cv, knot[-1][0], knot[-1][1], 3.0, 1.6, SILK_R, 0.56, sway=math.sin(ph) * 0.1, strands=4)
    kc = (hip[0] + 4.6 + math.sin(ph + 0.6) * 0.4, hip[1] + 1.4)
    purse = cv.blob([(kc[0] - 2.4, kc[1] - 2.0), (kc[0] + 2.4, kc[1] - 2.0), (kc[0] + 3.4, kc[1] + 2.0), (kc[0] + 2.2, kc[1] + 4.2, 0.0),
                     (kc[0] - 2.2, kc[1] + 4.2, 0.0), (kc[0] - 3.4, kc[1] + 2.0)])
    cv.shape(purse, LEATHER, z=0.6, sd=1.2, hi=0.3,
             details=[('ink', [(kc[0] - 2.2, kc[1] - 1.0), (kc[0] + 2.2, kc[1] - 1.0)], 0.9), ('col', cv.ellipse((kc[0], kc[1] + 1.4), 1.0, 1.0), GOLD.base)])
    for j in range(3):   # kuşakta asılı sikkeler (ışıltılı)
        q = (hip[0] - 3.0 + j * 2.2, hip[1] - 0.4 + (j % 2) * 0.5 + math.sin(ph + j) * 0.2)
        cv.shape(cv.ellipse(q, 0.9, 0.9), GOLD, z=0.65, sd=0.3, hi=0.3, ol=0.6)
    # ---- baş: yanık ten, sarkık bıyık, sivri sakal, kürk kenarlı uzun sivri börk
    hx, hy = hd
    cv.shape(cv.limb([neck, (hx + 0.5, hy + 3.0)], [2.3, 2.3]), SKIN_D, z=2.0, sd=1.0)
    _face(cv, hd, SKIN_D, 2.1, mouth=talk * 0.8)
    # kurnaz bakış: kaşın ucu kalkık, göz altı kırışığı
    cv.stroke([(hx - 3.4, hy + 0.4), (hx - 2.0, hy + 0.9)], 0.8, z=2.4, taper=(0.3, 0.6))
    # sarkık bıyık (iki uç aşağı) + sivri sakal
    mst = cv.blob([(hx - 4.6, hy + 2.0), (hx - 2.8, hy + 1.5), (hx - 1.0, hy + 2.2), (hx - 1.4, hy + 3.2), (hx - 2.6, hy + 2.8),
                   (hx - 4.0, hy + 4.6), (hx - 4.8, hy + 7.2, 0.0), (hx - 5.4, hy + 4.2)])
    cv.shape(mst, BEARD, z=2.6, sd=0.6, hi=0.25, ol=0.9, details=[('stroke', [(hx - 4.2, hy + 2.2), (hx - 4.8, hy + 5.6)], 0.7, BEARD.hi, (0.2, 0.6))])
    goat = cv.blob([(hx - 3.6, hy + 4.0), (hx - 1.4, hy + 4.4), (hx - 1.8, hy + 6.6), (hx - 3.0, hy + 8.4, 0.0), (hx - 3.8, hy + 6.0)])
    cv.shape(goat, BEARD, z=2.55, sd=0.5, ol=0.8)
    # altın küpe
    ea = (hx + 2.8, hy + 1.6)
    cv.shape(cv.ellipse((ea[0], ea[1] + 1.4), 0.8, 1.0), GOLD, z=2.3, sd=0.3, hi=0.3, ol=0.6)
    # börk: kürk bant + uzun sivri keçe tepe (geriye eğik) + kızıl püskül
    tilt = 0.18 + math.sin(ph) * 0.02
    tip = (hx + 3.0 + math.sin(tilt) * 14.0, hy - 5.0 - math.cos(tilt) * 14.0)
    cone = cv.blob([(hx - 4.0, hy - 4.0), (hx - 1.4, hy - 9.0), (tip[0] - 1.0, tip[1] + 1.4), (tip[0], tip[1], 0.0), (tip[0] + 1.0, tip[1] + 2.2),
                    (hx + 4.6, hy - 6.0), (hx + 4.8, hy - 3.6)])
    cdet = cv.fold([(hx + 0.6, hy - 6.0), (hx + 2.4, hy - 11.0), (tip[0] - 0.4, tip[1] + 2.0)], 0.7, 1.0, 1)
    cdet.append(('stroke', [(hx - 2.6, hy - 6.0), (hx + 0.4, hy - 12.0)], 0.8, HAT.hi, (0.2, 0.5)))
    cv.shape(cone, HAT, z=2.8, sd=1.8, hi=0.3, details=cdet, bounce=0.3)
    tassel(cv, tip[0], tip[1] - 0.4, 4.0, 2.0, SILK_R, 2.85, sway=0.35 + math.sin(ph) * 0.1, strands=5)
    brim = cv.blob([(hx - 5.4, hy - 2.2), (hx - 5.0, hy - 5.8), (hx - 0.4, hy - 6.6), (hx + 4.4, hy - 6.4), (hx + 5.8, hy - 4.6),
                    (hx + 5.6, hy - 1.8), (hx + 0.4, hy - 2.6)])
    cv.shape(brim, FUR, z=2.9, sd=0.9, hi=0.3, ol=0.9)
    # alında küçük firuze nazar
    cv.fill(cv.ellipse((hx - 3.6, hy - 4.6), 0.75, 0.75), TURQ.base, z=2.95)
    cv.fill(cv.ellipse((hx - 3.75, hy - 4.75), 0.28, 0.28), (1, 1, 1), z=2.96)
    # ---- ön kol + tunç terazi (kefeler salınır; kefede ışıyan sikkeler)
    sh_f = (neck[0] - 3.4, neck[1] + 3.0)
    af = p.get('af', (-0.85, 1.25))
    e2, h2 = fk_arm(sh_f, af[0], af[1], 9.0, 8.5)
    out['hand'] = h2
    beam_c = (h2[0] - 0.4, h2[1] - 2.4)
    cv.shape(cv.capsule((h2[0] - 0.2, h2[1] + 0.6), beam_c, 0.45, 0.45), BRONZE, z=13.2, sd=0.3, ol=0.8)
    tilt_b = p.get('beam', 0.0)
    bl, br = 6.4, 6.4
    a_ = (beam_c[0] - math.cos(tilt_b) * bl, beam_c[1] - math.sin(tilt_b) * bl)
    b_ = (beam_c[0] + math.cos(tilt_b) * br, beam_c[1] + math.sin(tilt_b) * br)
    cv.shape(cv.capsule(a_, b_, 0.5, 0.5), BRONZE, z=13.3, sd=0.4, hi=0.3, ol=0.8)
    cv.shape(cv.ellipse(beam_c, 0.9, 0.9), GOLD, z=13.35, sd=0.3, hi=0.3, ol=0.7)
    for k, (q, swk) in enumerate(((a_, p.get('pan_a', 0.0)), (b_, p.get('pan_b', 0.0)))):
        pc = (q[0] + math.sin(swk) * 6.0, q[1] + 6.0)
        for dxx in (-1.6, 1.6):
            cv.stroke([q, (pc[0] + dxx, pc[1])], 0.6, z=13.25, col=INK, taper=(0.0, 0.0))
        pan = cv.blob([(pc[0] - 2.6, pc[1], 0.0), (pc[0] + 2.6, pc[1], 0.0), (pc[0] + 1.6, pc[1] + 1.4), (pc[0] - 1.6, pc[1] + 1.4)])
        cv.shape(pan, BRONZE, z=13.4, sd=0.5, hi=0.4, ol=0.8)
        if k == 0:   # sikke yığını
            for j in range(3):
                cv.fill(cv.ellipse((pc[0] - 1.0 + j * 1.0, pc[1] - 0.5 - (j == 1) * 0.6), 0.85, 0.5), COIN, z=13.45, glow=COIN_GL)
    _sleeve(cv, sh_f, e2, h2, SILK_B, 13, wide=1.4, cuff=SASH)
    _hand(cv, e2, h2, SKIN_D, 14)
    return out


def _pose(anim, t):
    s = math.sin(t * math.tau)
    c = math.cos(t * math.tau)
    p = dict(bob=0.6 * s, lean=0.02 * s, ph=t * math.tau)
    # idle: terazi elde, göğüs hizasında; kefeler ters salınır (ince denge), arka el kesede
    p.update(af=(-0.35, -1.2), ab=(0.2 + 0.04 * s, 1.0), beam=0.08 * s, pan_a=0.12 * c, pan_b=-0.12 * c)
    if anim == 'talk':
        # "Buyur, yiğit!": arka el açılıp öne uzanır, terazi biraz kalkar
        p.update(talk=1.0 if t < 0.5 else 0.55, lean=0.05, ab=(-1.05 - 0.15 * s, -0.5 + 0.1 * c), af=(-0.75, -0.95),
                 beam=-0.1 + 0.06 * s, pan_a=0.2 * s, pan_b=-0.2 * s)
    return p


SHADE = dict(outer=0.5, rim=0.45, rim_col=(1.0, 0.86, 0.66), rim_dir=(0.6, -0.8), rim_w=1.3, form=(6.0, (0.8, 0.78, 0.9)))


def render_frame(anim, i, ss=3):
    n = NPC_ANIMS[anim][0]
    p = _pose(anim, i / n)
    cv = ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss)
    info = draw_tuccar(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info


ANIMS = {k: (v[0], None, True, True) for k, v in NPC_ANIMS.items()}


# ------------------------------------------------------------ kervan tezgâhı (süs)
CAMEL = Ink('#b88a58', '#5e3e34', '#e4bc86', '#36221e', kind='fur', name='deve yünü')
CAMEL_B = CAMEL.darker(0.8)
CUL = Ink('#9a2a2e', '#4c1024', '#c84a44', name='kızıl çul')


def _camel(cv):
    """Çöken iki hörgüçlü deve (sola bakar), sırtında çul ve denkler. Ayak hizası y = 0."""
    # uzak (arka) katlanmış bacaklar
    cv.shape(cv.blob([(30, -3.0), (44, -4.5), (52, -1.2), (50, 0.4, 0.0), (28, 0.4, 0.0)]), CAMEL_B, z=-2.0, sd=1.2)
    # gövde + hörgüçler
    body = ik.union(cv.ellipse((40, -15), 25, 11), cv.ellipse((31, -26), 8.5, 7.5, -0.2), cv.ellipse((50, -26), 8.0, 7.0, 0.2),
                    cv.ellipse((22, -13), 10, 9.5))
    bdet = [('ink', [(20, -6), (36, -4.4), (56, -6)], 0.9), ('stroke', [(26, -30), (32, -33.5), (38, -31)], 1.0, CAMEL.hi, (0.2, 0.5)),
            ('stroke', [(46, -30), (51, -33), (56, -29)], 1.0, CAMEL.hi, (0.2, 0.5))]
    cv.shape(body, CAMEL, z=0, sd=5.0, hi=0.8, details=bdet, bounce=0.35, fur=0.6)
    # boyun (ileri-yukarı kıvrık) + baş
    neck = ik.union(cv.limb([(18, -18), (10, -22), (5, -32), (2, -42)], [6.4, 5.4, 4.4, 4.0]))
    cv.shape(neck, CAMEL, z=0.2, sd=2.6, hi=0.5, fur=0.5,
             details=[('ink', [(12, -20), (7, -26)], 0.8), ('stroke', [(6, -40), (9, -30)], 0.9, CAMEL.hi, (0.2, 0.5))])
    head = cv.blob([(4, -45), (0, -48), (-6, -47.5), (-13, -44.5), (-15, -41.5), (-13, -39.4), (-7, -39.0), (-1, -38.6), (4, -40)])
    hd = [('col', cv.ellipse((-4.5, -45.0), 1.1, 0.8), INK), ('stroke', [(-4.6, -45.5), (-4.0, -45.6)], 0.5, (1, 1, 1), (0.1, 0.1)),
          ('ink', [(-14.2, -41.6), (-12.6, -41.2)], 0.8), ('ink', [(-13.5, -39.6), (-10.0, -39.4)], 0.7)]
    cv.shape(head, CAMEL, z=0.3, sd=2.0, hi=0.4, details=hd)
    cv.shape(cv.blob([(1.5, -47.5), (2.5, -51.0, 0.0), (3.8, -47.2)]), CAMEL, z=0.25, sd=0.5, ol=0.7)   # kulak
    # yular + boyun çıngırağı
    cv.stroke([(-12, -40), (-6, -40.5), (1, -41.5)], 1.1, z=0.35, col=RED.base, taper=(0.05, 0.05))
    cv.stroke([(-2, -47), (-3, -40)], 1.0, z=0.35, col=RED.base, taper=(0.05, 0.05))
    cv.stroke([(9, -26), (11, -21)], 0.8, z=0.35, col=LEATHER.shadow)
    bell = cv.blob([(10, -21.4, 0.0), (12.6, -21.4, 0.0), (13.4, -17.4), (9.2, -17.4)])
    cv.shape(bell, BRONZE, z=0.4, sd=0.6, hi=0.4, ol=0.8)
    # boyun altı ve hörgüç tepesi uzun yün (kıl tutamları)
    for k in range(5):
        x = 13 - k * 2.0
        cv.stroke([(x, -21 - k * 3), (x - 2.6, -18.5 - k * 3)], 1.4, z=0.36, col=CAMEL.shadow, taper=(0.1, 0.8))
    # yakın katlanmış ön bacak (diz önde)
    cv.shape(cv.blob([(14, -6), (6, -4), (2.5, -1.6), (3, 0.4, 0.0), (22, 0.4, 0.0), (22, -4)]), CAMEL, z=0.5, sd=1.4, hi=0.3,
             details=[('ink', [(6, -3.4), (8, -1.0)], 0.8)])
    cv.shape(cv.blob([(40, -5), (54, -6), (62, -2.2), (60, 0.4, 0.0), (38, 0.4, 0.0)]), CAMEL, z=0.45, sd=1.4, hi=0.3)
    # kuyruk
    cv.shape(ik.taper_path([cv.W(q) for q in [(64, -18), (67, -12), (66, -6)]], cv.u(2.0), (0.1, 0.5)), CAMEL_B, z=-0.5, sd=0.6, ol=0.8)
    # çul (hörgüçler arası) + denkler
    cul = cv.blob([(30, -27, 0.0), (52, -27, 0.0), (56, -10, 0.0), (52, -8.5), (34, -8.5), (27, -10, 0.0)])
    det = [('col', cv.blob([(27, -12, 0.0), (56, -12, 0.0), (56, -9.5, 0.0), (27, -9.5, 0.0)]), GOLD.base)]
    for x in (34, 41, 48):
        det.append(('col', cv.blob(diamond(x, -18, 2.8, 3.4)), GOLD.base))
        det.append(('col', cv.blob(diamond(x, -18, 1.2, 1.4)), BLUE.base))
    cv.shape(cul, CUL, z=1.0, sd=3.0, hi=0.4, details=det)
    for k in range(9):
        x = 28 + k * 3.4
        cv.stroke([(x, -9.0), (x + 0.3, -6.4)], 0.8, z=0.95, col=GOLD.base, taper=(0.1, 0.7))
    # denkler: iki yana sarkan yük çuvalları + üstte dürülmüş kilimler
    sack = cv.blob([(34, -30), (48, -30), (50, -22), (47, -14, 0.0), (35, -14, 0.0), (32, -22)])
    sdet = cv.fold([(41, -29), (40, -22), (41, -15)], 0.8, 1.0, 1) + [('ink', [(33, -26), (49, -26)], 1.0)]
    for x in (37, 45):   # kilim heybe: kızıl elmas göbekler
        sdet.append(('col', cv.blob(diamond(x, -20.5, 3.2, 4.4)), RED.base))
        sdet.append(('col', cv.blob(diamond(x, -20.5, 1.3, 1.8)), GOLD.base))
    cv.shape(sack, BLUE, z=1.2, sd=3.0, hi=0.4, details=sdet)
    cv.stroke([(33, -26), (41, -36), (49, -26)], 1.0, z=1.3, col=ROPE.shadow)
    _rug_roll(cv, (30, -36), (52, -36.5), 3.2, SILK_R, SASH, 1.4)
    _rug_roll(cv, (32, -41.6), (50, -42.0), 2.8, BLUE, RED, 1.5)


def kervan():
    P = Prop(184, 104, 96, 100)
    cv = P.cv
    _camel(cv)
    # yere serili kilim (merkez soldan, tüccarın ayakları altında)
    rug = cv.blob([(-62, 1.2, 0.0), (-60, -3.0, 0.0), (22, -3.0, 0.0), (24, 1.2, 0.0)])
    det = [('col', cv.blob([(-60, -3.0, 0.0), (22, -3.0, 0.0), (22, -2.2, 0.0), (-60, -2.2, 0.0)]), GOLD.base)]
    for k in range(8):
        x = -54 + k * 10.4
        det.append(('col', cv.blob(diamond(x, -0.7, 3.6, 1.3)), BLUE.base))
        det.append(('col', cv.blob(diamond(x, -0.7, 1.4, 0.6)), GOLD.base))
    cv.shape(rug, RED, z=2.0, sd=0.9, hi=0.3, details=det, ol=0.8)
    for f, x0 in ((-1, -62), (1, 24)):
        for k in range(7):
            yy = -2.6 + k * 0.6
            cv.stroke([(x0, yy), (x0 + f * 3, yy + 0.6)], 0.8, z=1.9, col=FELT_C.base, taper=(0.1, 0.6))
    # mallar (kilimin üstünde, soldan sağa)
    # 1) alçak sehpada kılıç (yatay), kınının altın bileziği
    cv.shape(cv.blob([(-56, -3, 0.0), (-56, -9, 0.0), (-34, -9, 0.0), (-34, -3, 0.0)]), WOOD_R, z=2.2, sd=1.2, hi=0.3,
             details=[('stroke', [(-55, -8.2), (-35, -8.2)], 0.9, GOLD.base, (0.1, 0.1))])
    for x in (-52, -38):
        cv.shape(cv.blob([(x - 1.6, -9, 0.0), (x + 1.6, -9, 0.0), (x + 1.0, -13, 0.0), (x - 1.0, -13, 0.0)]), WOOD_D, z=2.25, sd=0.5, ol=0.8)
    blade = cv.blob([(-58, -13.8, 0.0), (-38, -14.6), (-31, -13.0, 0.0), (-38, -12.4), (-58, -12.6, 0.0)])
    cv.shape(blade, STEEL, z=2.4, sd=0.6, hi=0.5, details=[('stroke', [(-56, -13.4), (-36, -13.6)], 0.6, (1, 1, 1), (0.2, 0.5))])
    cv.shape(cv.capsule((-63, -13.2), (-58.5, -13.2), 1.0, 1.0), LEATHER, z=2.45, sd=0.4, ol=0.8)
    cv.shape(cv.blob([(-58.6, -16.4, 0.0), (-57.2, -16.4, 0.0), (-57.2, -10.0, 0.0), (-58.6, -10.0, 0.0)]), GOLD, z=2.5, sd=0.3, hi=0.3, ol=0.7)
    # 2) yaslanmış yuvarlak kalkan (kızıl göbek, tunç kabara)
    shc = (-24, -11)
    cv.shape(cv.ellipse(shc, 8.6, 9.6, -0.2), WOOD, z=2.15, sd=2.2, hi=0.4,
             details=[('col', cv.ellipse(shc, 6.4, 7.2, -0.2), RED.base), ('col', cv.ellipse(shc, 4.0, 4.6, -0.2), WOOD.base)])
    cv.shape(cv.ellipse(shc, 2.0, 2.2), BRONZE, z=2.2, sd=0.6, hi=0.5, ol=0.8)
    for k in range(8):
        a = k * math.tau / 8
        cv.fill(cv.ellipse((shc[0] + math.cos(a) * 7.6, shc[1] + math.sin(a) * 8.4), 0.55, 0.55), BRONZE.hi, z=2.21)
    # 3) kilime yatırılmış kirişli yay
    bow = [(-14, -4.0), (-8, -9.5), (2, -11.0), (11, -9.0), (16, -4.4)]
    cv.shape(ik.taper_path([cv.W(q) for q in bow], cv.u(1.4), prof=lambda s: 0.6 + 0.4 * math.sin(math.pi * s)), WOOD_D, z=2.6, sd=0.5, hi=0.3)
    cv.stroke([(-14, -4.0), (16, -4.4)], 0.7, z=2.55, col=FELT.hi)
    cv.shape(cv.capsule((0, -11.2), (4, -10.8), 0.9, 0.9), LEATHER, z=2.65, sd=0.3, ol=0.8)
    # 4) küpler ve mühürlü tomar, sikke yığını (öne)
    for x, hgt, m in ((-4, 9.0, COPPER), (5, 7.0, Ink('#9a6a4a', '#4a2c26', '#c89a72', name='pişmiş toprak'))):
        jar = cv.blob([(x - 2.0, -hgt - 1.0), (x + 2.0, -hgt - 1.0), (x + 4.0, -hgt * 0.5), (x + 3.0, -1.5), (x, -1.0, 0.0), (x - 3.0, -1.5), (x - 4.0, -hgt * 0.5)])
        cv.shape(jar, m, z=2.3, sd=1.4, hi=0.5, details=[('stroke', [(x - 3.6, -hgt * 0.55), (x + 3.6, -hgt * 0.55)], 0.8, GOLD.base, (0.1, 0.1))])
    sc = (14, -4.6)
    cv.shape(cv.capsule((sc[0] - 4.5, sc[1]), (sc[0] + 4.5, sc[1]), 1.8, 1.8), FELT_C, z=2.7, sd=0.6, hi=0.3,
             details=[('ink', [(sc[0] - 2, sc[1] - 1.6), (sc[0] - 2, sc[1] + 1.6)], 0.7)])
    cv.fill(cv.ellipse((sc[0] + 1.0, sc[1] + 1.4), 1.1, 1.1), RED.base, z=2.75, glow=(0.5, 0.1, 0.05))
    for j in range(5):
        cv.fill(cv.ellipse((-12 + (j % 3) * 1.6, -2.0 - (j // 3) * 0.9), 0.95, 0.55), COIN, z=2.8, glow=COIN_GL)
    # fener direği + kızıl-safran flama (solda)
    cv.shape(cv.capsule((-74, 1), (-74, -86), 1.6, 1.3), WOOD_D, z=1.0, sd=0.9, hi=0.35)
    cv.shape(cv.ellipse((-74, -87), 2.4, 2.4), GOLD, z=1.05, sd=0.6, hi=0.4)
    pen = cv.blob([(-73, -84, 0.0), (-52, -80.5), (-58, -78.0), (-50, -75.2, 0.0), (-73, -74.5, 0.0)])
    cv.shape(pen, SILK_R, z=0.95, sd=1.8, hi=0.4, details=cv.fold([(-70, -79.5), (-58, -78.5)], depth=0.7, w=0.8) +
             [('col', cv.blob([(-73, -78.4, 0.0), (-55, -77.2, 0.0), (-55, -76.0, 0.0), (-73, -76.4, 0.0)]), SILK_Y.base)])
    arm = [(-74, -66), (-66, -69), (-60, -66)]
    cv.shape(ik.taper_path([cv.W(q) for q in arm], cv.u(1.3), (0.05, 0.3)), IRON, z=1.1, sd=0.5, ol=0.8)
    lc = (-60, -60)
    cv.stroke([(-60, -66), (-60, -63)], 0.8, z=1.1, col=INK)
    glass = cv.blob([(-64, -63, 0.0), (-56, -63, 0.0), (-55, -57), (-56, -51, 0.0), (-64, -51, 0.0), (-65, -57)])
    cv.shape(glass, Ink('#f4b44e', '#c46a24', '#fff2c0'), z=1.2, sd=1.2, hi=0.0, ol=0.7, glow=LAMP_GL)
    cv.fill(cv.ellipse((lc[0], lc[1] + 3.0), 1.8, 2.8), (1.0, 0.96, 0.8), z=1.25, glow=(1.0, 0.85, 0.5))
    for x in (-63.6, -60, -56.4):
        cv.stroke([(x, -63), (x, -51)], 0.9, z=1.3, col=INK, taper=(0.05, 0.05))
    cv.shape(cv.blob([(-65, -63, 0.0), (-60, -66.5), (-55, -63, 0.0)]), BRONZE, z=1.35, sd=0.5, ol=0.7)
    cv.shape(cv.blob([(-80, 0.5, 0.0), (-79, -3), (-74, -4.5), (-69, -3), (-68, 0.5, 0.0)]), P_.STONE, z=1.1, sd=1.2, hi=0.4)
    grass_tufts(cv, -90, 86, 0, 46, 3.0, 24)
    return P.done(outer=1.1, rim=0.32)


ALL = {'bezirgan_kervan': kervan}
STAND_X = 48.0   # tüccarın tezgâh kökenine göre durduğu yer (dünya; Bezirgan.gd TEZGAH_DX ile aynı)


if __name__ == '__main__':
    # önizleme: python tuccar_ink.py out.png  -> tezgâh + tüccar idle/talk kareleri koyu zeminde
    import sys
    from PIL import Image
    out = sys.argv[-1] if sys.argv[-1].endswith('.png') else 'tuccar_on.png'
    rgba, glow, org = kervan()
    frames = [render_frame('idle', i) for i in (0, 2, 4)] + [render_frame('talk', i) for i in (0, 2)]
    fw = frames[0][0].shape[1]
    Wd = rgba.shape[1] + 40 + len(frames) * (fw + 10)
    Hd = max(rgba.shape[0], frames[0][0].shape[0]) + 40
    bg = np.zeros((Hd, Wd, 3), np.float32)
    bg[:] = (0.09, 0.1, 0.16)

    def put(r, g, x, y):
        h, w = r.shape[:2]
        a = r[..., 3:4]
        bg[y:y + h, x:x + w] = bg[y:y + h, x:x + w] * (1 - a) + r[..., :3] * a
        if g is not None:
            bg[y:y + h, x:x + w] += g[..., :3] * g[..., 3:4] * 0.8
    # tüccarı tezgâhın üstüne yerleştir (ayak = kilimin ortası)
    put(rgba, glow, 20, Hd - 20 - rgba.shape[0])
    fx = 20 + int(org[0] + STAND_X * TEX) - FEET[0]
    fy = Hd - 20 - rgba.shape[0] + int(org[1]) - FEET[1]
    r0 = frames[0]
    put(r0[0], np.concatenate([r0[2][..., :3] / np.maximum(r0[2][..., 3:4], 1e-4), r0[2][..., 3:4]], -1), fx, fy)
    x = rgba.shape[1] + 40
    for r in frames:
        em = r[2]
        put(r[0], np.concatenate([em[..., :3] / np.maximum(em[..., 3:4], 1e-4), em[..., 3:4]], -1), x, Hd - 20 - r[0].shape[0])
        x += fw + 10
    Image.fromarray((np.clip(bg, 0, 1) * 255).astype(np.uint8)).save(out)
    print('önizleme', out, bg.shape)
