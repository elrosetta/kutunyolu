"""v27 savaş sanatları ustası: Alp Ata — stil v2 "mürekkep-cel" (inkkit.py; npc_ink.py yardımcıları).

Dede Korkut'un ak sakallı yiğitlerinden: nice savaştan dönmüş, yüzü yara izli yaşlı alp. Yurtta gençlere savaş
sanatlarını (Kasırga Kesişi, Bir Çekiş, Ay Hilali ...) öğretir; karşılığında Kut ister.

* npc_alp_ata_v2 (NPC sayfası, npc_ink.py ile aynı düzen: idle 6 kare 8 fps, talk 4 kare 10 fps; yüz SOLA, ayak (0, 0)):
  geniş omuzlu, hafif kambur yaşlı savaşçı. Sivri demir miğfer (kürk kenarlı, tepede kızıl at kılı tuğ; tuğ idle'da
  salınır), uzun çatal ak bıyık ve örgülü ak sakal, yanakta yara izi. Lacivert kaftan üstünde demir pul zırh (yatay
  sıralı lameller), omuzlarda bozkurt postu (arka omuzda kurt başı, kulaklar), kızıl kuşak, çizme. İki eli önüne dikili
  ulu kılıcın balçağında (kılıcın ucu yerde); konuşurken ön eli öğretir gibi açılıp kalkar, kılıçta arka el kalır.
"""
import math

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_arm, lerp2, chain
from bengu_ink import along
from yurt import NPC_ANIMS
import wolfkit as wk
from npc_ink import (_face, _hand, _sleeve, SKIN_O, GOLD, IRON, BOOT, BEARD_W, CELL, FEET, TEX)

KAFTAN_L = Ink('#2c4478', '#141e3c', '#5876b4', '#0a1028', name='lacivert kaftan')
LAMEL = Ink('#8a8e9c', '#3e4050', '#d0d4e0', '#20222c', kind='metal', name='pul zırh')
POST = Ink('#8c8a90', '#44424c', '#cac6cc', '#24222a', kind='fur', name='bozkurt postu')
POST_D = POST.darker(0.78)
RED_S = Ink('#a8302c', '#561428', '#de5a46', name='kızıl kuşak')
TUG = Ink('#b8282a', '#5a0e1c', '#ec5a48', name='kızıl at kılı')
STEEL = Ink('#b8bcc8', '#5a5e6e', '#f4f6fc', '#2a2c38', kind='metal', name='çelik')
LEATHER_K = Ink('#5a3a2a', '#2a1a16', '#86604a', name='kabza derisi')


def draw_alp_ata(cv, p):
    bob, lean, ph = p.get('bob', 0.0), p.get('lean', 0.0), p.get('ph', 0.0)
    talk = p.get('talk', 0.0)
    hip = (0.0, -24.0 + bob * 0.3)
    neck = (hip[0] - math.sin(lean + 0.12) * 17.5, hip[1] - 17.5 + bob * 0.5)
    hd = (neck[0] - 1.8, neck[1] - 4.8)
    out = {'head': hd}
    # ---- ulu kılıç: önde, ucu yerde dikili (balçak göğüs altı)
    sx = hip[0] - 16.0
    tip = (sx + 0.4, -0.6)
    guard = (sx, hip[1] + 2.5)
    pommel = (sx - 0.2, guard[1] - 8.6)
    blade = cv.blob([(tip[0], tip[1] + 0.6, 0.0), (guard[0] - 1.9, guard[1] + 1.0), (guard[0] + 1.9, guard[1] + 1.0)])
    cv.shape(blade, STEEL, z=11, sd=0.9, hi=0.6, cast=0.5,
             details=[('ink', [(guard[0], guard[1] + 1.4), (tip[0] + 0.1, tip[1] - 2.0)], 0.7, (0.0, 0.3)),
                      ('stroke', [(guard[0] - 0.8, guard[1] + 2.0), (tip[0] - 0.2, tip[1] - 4.0)], 0.7, STEEL.hi, (0.1, 0.5))])
    cv.shape(cv.blob([(guard[0] - 5.4, guard[1] - 0.6), (guard[0] + 5.4, guard[1] - 0.6), (guard[0] + 4.6, guard[1] + 1.3, 0.0),
                      (guard[0] - 4.6, guard[1] + 1.3, 0.0)]), GOLD, z=11.2, sd=0.6, hi=0.4, ol=0.8)
    cv.shape(cv.limb([guard, pommel], [1.1, 1.0]), LEATHER_K, z=11.1, sd=0.5, hi=0.2,
             details=[('ink', [lerp2(guard, pommel, t), lerp2(guard, pommel, t + 0.08)], 0.7) for t in (0.2, 0.45, 0.7)])
    cv.shape(cv.ellipse(pommel, 1.7, 1.5), GOLD, z=11.3, sd=0.5, hi=0.5, ol=0.8)
    # ---- arka kol: balçağın altında, kılıcı tutar
    sh_b = (neck[0] + 3.4, neck[1] + 3.2)
    eb, hb = wk.ik(sh_b, (guard[0] + 0.8, guard[1] - 3.6), 9.0, 8.5, -1)
    _sleeve(cv, sh_b, eb, hb, KAFTAN_L.darker(0.8), -12, wide=0.4, near=False, cuff=LAMEL.darker(0.8))
    # ---- bacaklar: lacivert şalvar + çizme (geniş duruş)
    for dx, zz, m in ((3.8, -9, KAFTAN_L.darker(0.6)), (-3.2, -2, KAFTAN_L.darker(0.75))):
        top_ = (hip[0] + dx * 0.55, hip[1])
        knee = (hip[0] + dx * 1.0, hip[1] + 11.0)
        ft = (hip[0] + dx * 1.2, -0.2)
        leg = cv.limb([top_, lerp2(top_, knee, 0.5), knee, lerp2(knee, ft, 0.45)], [4.6, 4.8, 4.0, 4.0])
        cv.shape(leg, m, z=zz, sd=2.0, details=cv.fold([lerp2(top_, knee, 0.3), lerp2(top_, knee, 0.75), lerp2(knee, ft, 0.25)], 0.5, 1.0, 1))
        boot = cv.blob([(ft[0] + 3.0, ft[1] - 8.6), (ft[0] - 3.2, ft[1] - 8.6), (ft[0] - 3.6, ft[1] - 2.4), (ft[0] - 6.6, ft[1] - 1.8),
                        (ft[0] - 7.2, ft[1] + 0.2, 0.0), (ft[0] + 3.2, ft[1] + 0.2, 0.0)])
        cv.shape(boot, BOOT if zz > -5 else BOOT.darker(0.75), z=zz + 0.3, sd=1.3, hi=0.3,
                 details=[('stroke', [(ft[0] - 3.2, ft[1] - 7.6), (ft[0] + 2.8, ft[1] - 7.6)], 1.2, GOLD.base, (0.1, 0.1))])
    # ---- kaftan etekleri (dize dek, yırtmaçlı) + pul zırh gövde
    sk = math.sin(ph) * 0.35
    skirt = cv.blob([(hip[0] - 8.6, hip[1] - 3.0), (hip[0] + 8.8, hip[1] - 3.4), (hip[0] + 10.0 + sk, hip[1] + 12.6, 0.0),
                     (hip[0] + 1.2 + sk, hip[1] + 13.6), (hip[0] - 10.4 + sk, hip[1] + 12.8, 0.0)])
    sdet = cv.fold([(hip[0] - 3.0, hip[1]), (hip[0] - 3.6 + sk, hip[1] + 7.0), (hip[0] - 3.2 + sk, hip[1] + 13.0)], 0.9, 1.2, 1)
    sdet += cv.fold([(hip[0] + 4.0, hip[1]), (hip[0] + 4.4 + sk, hip[1] + 7.0), (hip[0] + 5.0 + sk, hip[1] + 12.6)], 0.7, 1.1, -1)
    cv.shape(skirt, KAFTAN_L, z=0, sd=3.6, details=sdet, hatch=0.3, bounce=0.3)
    torso = cv.blob([(neck[0] - 6.8, neck[1] + 2.2), (neck[0] + 6.8, neck[1] + 1.8), (hip[0] + 8.6, hip[1] - 4.0), (hip[0] + 8.0, hip[1] + 1.0, 0.0),
                     (hip[0] - 8.6, hip[1] + 1.4, 0.0), (hip[0] - 8.8, hip[1] - 3.4)])
    ldet = []
    for r in range(6):   # yatay lamel sıraları
        t = (r + 0.6) / 6.4
        y0 = lerp2(neck, hip, t)[1] + 1.6
        xl = lerp2((neck[0] - 6.6, 0), (hip[0] - 8.6, 0), t)[0]
        xr = lerp2((neck[0] + 6.6, 0), (hip[0] + 8.6, 0), t)[0]
        ldet.append(('ink', [(xl, y0), ((xl + xr) / 2, y0 + 0.5), (xr, y0)], 0.8, (0.05, 0.05)))
        for k in range(7):   # dikey dikiş çizgileri (kayış)
            x = lerp2((xl, 0), (xr, 0), (k + 0.5 + (r % 2) * 0.5) / 7.5)[0]
            ldet.append(('ink', [(x, y0 - 2.4), (x, y0 - 0.4)], 0.55, (0.1, 0.1)))
    cv.shape(torso, LAMEL, z=1.0, sd=3.2, hi=0.45, details=ldet, cast=0.7, bounce=0.3)
    # kızıl kuşak + uçları
    cv.shape(cv.blob([(hip[0] - 9.0, hip[1] - 4.4), (hip[0] + 8.8, hip[1] - 4.8), (hip[0] + 9.0, hip[1] - 1.4), (hip[0] - 9.0, hip[1] - 1.0)]),
             RED_S, z=1.4, sd=0.9, hi=0.25, details=[('ink', [(hip[0] - 7.0 + j * 3.4, hip[1] - 4.2), (hip[0] - 6.4 + j * 3.4, hip[1] - 1.2)], 0.7, (0.1, 0.1)) for j in range(5)])
    kn = chain((hip[0] + 6.0, hip[1] - 2.6), 3, 2.4, math.pi * 0.45 + math.sin(ph) * 0.12, 0.05, ph, 0.18)
    cv.shape(ik.taper_path([cv.W(q) for q in kn], cv.u(1.6), (0.1, 0.4)), RED_S, z=1.45, sd=0.5, ol=0.7)
    # ---- bozkurt postu: omuzlardan sırta (tırtıklı kürk ucu), arka omuzda kurt başı
    pelt_pts = [(neck[0] - 7.4, neck[1] + 1.2), (neck[0] - 3.0, neck[1] - 1.6), (neck[0] + 4.0, neck[1] - 1.8), (neck[0] + 9.6, neck[1] + 1.2)]
    for j in range(7):   # tırtıklı alt kenar
        x = lerp2((neck[0] + 9.4, 0), (neck[0] - 7.6, 0), j / 6.0)[0]
        y = neck[1] + 6.4 + (2.4 if j % 2 else 0.0) + math.sin(ph + j) * 0.2
        pelt_pts.append((x, y, 0.0) if j % 2 else (x, y))
    pelt = cv.blob(pelt_pts)
    pdet = [('ink', [(neck[0] - 4.0 + j * 2.6, neck[1] + 0.4), (neck[0] - 3.6 + j * 2.6, neck[1] + 4.2)], 0.7, (0.2, 0.6)) for j in range(5)]
    cv.shape(pelt, POST, z=1.8, sd=2.0, hi=0.35, details=pdet, bounce=0.3)
    wh = (neck[0] + 7.8, neck[1] - 1.4)   # kurt başı (arka omuz, burnu sola-aşağı)
    head_w = cv.blob([(wh[0] - 5.2, wh[1] + 1.8), (wh[0] - 2.0, wh[1] - 1.6), (wh[0] + 2.6, wh[1] - 1.8), (wh[0] + 3.6, wh[1] + 1.6),
                      (wh[0] + 0.8, wh[1] + 3.4), (wh[0] - 4.6, wh[1] + 3.0, 0.0)])
    cv.shape(head_w, POST_D, z=1.9, sd=1.0, hi=0.3, ol=0.9,
             details=[('ink', [(wh[0] - 3.4, wh[1] + 1.6), (wh[0] - 1.6, wh[1] + 1.0)], 0.8, (0.1, 0.4)),
                      ('col', cv.ellipse((wh[0] - 4.6, wh[1] + 2.2), 0.7, 0.6), (0.06, 0.04, 0.05))])
    for ex in (0.2, 2.2):
        cv.shape(cv.blob([(wh[0] + ex - 0.9, wh[1] - 1.2), (wh[0] + ex + 0.3, wh[1] - 4.4, 0.0), (wh[0] + ex + 1.3, wh[1] - 1.0)]), POST_D, z=1.85, sd=0.5, ol=0.85)
    # ---- baş: yaşlı yüz, yara izi, çatal ak bıyık, örgülü ak sakal, sivri demir miğfer + tuğ
    hx, hy = hd
    cv.shape(cv.limb([neck, (hx + 0.5, hy + 3.0)], [2.6, 2.6]), SKIN_O, z=2.0, sd=1.0)
    _face(cv, hd, SKIN_O, 2.1, old=True, brow_col=(0.85, 0.86, 0.9), mouth=talk)
    cv.stroke([(hx - 0.2, hy - 1.6), (hx + 1.2, hy + 2.4)], 0.9, z=2.32, col=(0.55, 0.2, 0.2), taper=(0.2, 0.2))   # yara izi
    cv.shape(cv.blob([(hx - 4.2, hy - 2.6), (hx - 1.2, hy - 3.2), (hx + 0.8, hy - 2.6), (hx - 1.4, hy - 1.9, 0.0)]), BEARD_W, z=2.55, sd=0.4, ol=0.6)
    bsw = math.sin(ph) * 0.35
    beard = cv.blob([(hx - 4.4, hy + 2.6), (hx - 1.6, hy + 3.2), (hx + 2.4, hy + 1.8), (hx + 2.6, hy + 5.6), (hx + 0.2 + bsw, hy + 10.0),
                     (hx - 1.0 + bsw, hy + 14.6, 0.0), (hx - 2.6 + bsw * 0.6, hy + 9.6), (hx - 4.6, hy + 5.0)])
    bdt = [('ink', [(hx - 3.0, hy + 4.2), (hx - 1.8, hy + 8.6), (hx - 1.0 + bsw, hy + 13.0)], 0.9, (0.2, 0.6)),
           ('ink', [(hx - 0.4, hy + 4.2), (hx + 0.2, hy + 8.0)], 0.8, (0.2, 0.6))]
    cv.shape(beard, BEARD_W, z=2.5, sd=1.3, hi=0.3, details=bdt, bounce=0.3)
    for j in range(2):   # örgü halkaları (altın)
        q = (hx - 1.2 + bsw * (0.4 + 0.3 * j), hy + 9.6 + j * 2.4)
        cv.shape(cv.ellipse(q, 1.1, 0.5), GOLD, z=2.6, sd=0.3, hi=0.3, ol=0.7)
    # çatal bıyık: iki uzun uç aşağı sarkar
    for side, (x0, x1) in enumerate(((-4.6, -6.6), (-1.0, 0.6))):
        must = cv.blob([(hx - 3.6, hy + 2.0), (hx - 1.6, hy + 2.2), (hx + x0 * 0.2 - 1.2, hy + 3.2), (hx + x1, hy + 7.6 + bsw * 0.4, 0.0),
                        (hx + x0 * 0.5 - 1.8, hy + 3.6)])
        cv.shape(must, BEARD_W, z=2.62 + side * 0.01, sd=0.5, ol=0.8)
    # miğfer: sivri demir külah, alın siperi, kürk kenar
    helm = cv.blob([(hx - 4.8, hy - 2.6), (hx - 3.8, hy - 8.0), (hx - 0.6, hy - 13.8, 0.0), (hx + 3.2, hy - 8.6), (hx + 4.8, hy - 2.8)])
    hdet = [('ink', [(hx - 0.6, hy - 13.2), (hx - 0.2, hy - 4.0)], 0.8, (0.1, 0.4)),
            ('stroke', [(hx - 2.8, hy - 9.0), (hx - 3.6, hy - 4.4)], 0.8, LAMEL.hi, (0.2, 0.4))]
    cv.shape(helm, IRON, z=2.8, sd=1.6, hi=0.55, details=hdet, cast=0.4)
    brim = cv.blob([(hx - 5.6, hy - 1.8), (hx - 5.0, hy - 4.4), (hx + 0.4, hy - 4.0), (hx + 5.6, hy - 4.6), (hx + 5.8, hy - 2.0), (hx + 0.2, hy - 1.4)])
    cv.shape(brim, POST, z=2.9, sd=0.8, hi=0.3, ol=0.9,
             details=[('ink', [(hx - 4.4 + j * 1.8, hy - 4.0), (hx - 4.2 + j * 1.8, hy - 2.0)], 0.6, (0.2, 0.5)) for j in range(6)])
    cv.shape(cv.ellipse((hx - 0.6, hy - 14.0), 1.1, 0.9), GOLD, z=2.95, sd=0.4, hi=0.4, ol=0.8)
    # tuğ: tepeden geriye savrulan kızıl at kılı (salınır)
    tug = chain((hx - 0.4, hy - 14.4), 5, 2.6, -math.pi * 0.12 + math.sin(ph) * 0.12, 0.16, ph, 0.25)
    cv.shape(ik.taper_path([cv.W(q) for q in tug], cv.u(2.6), (0.3, 0.05)), TUG, z=2.7, sd=0.9, hi=0.3, ol=0.85,
             details=[('ink', [tug[1], tug[3], tug[5]], 0.7, (0.1, 0.6))])
    # ---- ön kol: idle'da balçakta (arka elin üstünde), konuşurken açılıp kalkar (öğretir)
    sh_f = (neck[0] - 3.0, neck[1] + 4.0)
    teach = p.get('teach', 0.0)
    if teach > 0.05:
        tgt = (sh_f[0] - 10.0 - 1.5 * teach, sh_f[1] - 3.0 - 5.0 * teach)
    else:
        tgt = (pommel[0] + 0.4, pommel[1] + 1.6)
    ef, hf = wk.ik(sh_f, tgt, 9.0, 8.5, -1)
    out['hand'] = hf
    _hand(cv, eb, hb, SKIN_O, 11.5, near=False)   # arka el kılıcın önünde görünür (kabzayı kavrar)
    _sleeve(cv, sh_f, ef, hf, KAFTAN_L, 13, wide=0.6, cuff=LAMEL)
    # omuzluk (pul zırh)
    cv.shape(cv.blob([along(sh_f, ef, 0.0, 3.0), along(sh_f, ef, 0.36, 3.4), along(sh_f, ef, 0.42, -2.8), along(sh_f, ef, 0.02, -2.4)]),
             LAMEL, z=13.3, sd=1.0, hi=0.45, ol=0.85,
             details=[('ink', [along(sh_f, ef, t, 3.2), along(sh_f, ef, t, -2.6)], 0.6, (0.1, 0.1)) for t in (0.14, 0.27)])
    _hand(cv, ef, hf, SKIN_O, 14, open_=1.0 if teach > 0.05 else 0.0)
    return out


def _pose(anim, t):
    s = math.sin(t * math.tau)
    p = dict(bob=0.5 * s, lean=0.015 * s, ph=t * math.tau)
    if anim == 'talk':
        p.update(talk=1.0 if t < 0.5 else 0.5, teach=0.7 + 0.3 * s, lean=0.03)
    return p


SHADE = dict(outer=0.5, rim=0.45, rim_col=(1.0, 0.86, 0.66), rim_dir=(0.6, -0.8), rim_w=1.3, form=(6.0, (0.8, 0.78, 0.9)))


def render_frame(anim, i, ss=3):
    n = NPC_ANIMS[anim][0]
    p = _pose(anim, i / n)
    cv = ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss)
    info = draw_alp_ata(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info


ANIMS = {k: (v[0], None, True, True) for k, v in NPC_ANIMS.items()}
