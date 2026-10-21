"""v39: Yılan Kamı (kimlik yilan_kami) — Şahmeran'ın rahibi; Şahmeran mağaraları; yapay zekâ şifacı / güçlendirici.

Cüppeli kam rahip: başında arkadan yükselen büyük, pullu kobra başlığı (kenarı altın, sırtında kara göz lekeleri);
başlığın yılan başı alnın üstünden öne eğilir, gözleri ışır, dili titrer. Yüzün alt yarısı altın pul peçeyle örtülü.
Zümrüt yeşili ve altın cüppe: önde pul işlemeli altın şerit, omuzlarda pul pelerincik, yere dek inen saçaklı etek
(ayaklar görünmez, süzülür). Kollarda kıvrılmış yılan biçimli altın bilezikler. Arka elinde bir asa: asaya canlı
yeşil bir yılan sarılır, asanın ucunda ışıyan yeşim taşı.

Satırlar (hücre 288x256 px = dünya 72x64, ayak (28, 60), doku 4; gövde 18 x 40):
  idle 8 (salınır, asadaki yılan kıpırdar), move 8 (süzülür, etek saçakları akar), hurt 3,
  atk_heal 9 (mk: asa havaya kalkar, taşta yeşil ışık sarmalı dolar, kobra başlığı açılır -> taştan öne-yukarı parlak
  yeşil patlama, huzme başlangıcı), atk_wisp 8 (mk: avuçta üç yeşil ruh ışığı toplanır -> eller ileri itilir, salınır),
  blink 6 (yeşil pullara / sise çözülür; ışınlanıp gitme ve gelme aynı satır).
'hand' çapası = asanın yeşim taşı (şifa huzmesi / ruh ışığı çıkışı), her karede.
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import lerp2
import yaratik_ink_kit as yk
import yaratik_govde as yg
import ucan_v29 as u29
from ucan_v29 import pose_at

TEX = 4.0
CELL = (288, 256)       # dünya 72 x 64 (şifa huzmesi önde sığsın)
FEET = (112, 240)       # dünya (28, 60)

SKIN = Ink('#b98a64', '#6a4434', '#e2b88c', '#3a2018', name='esmer ten')
SKIN_B = SKIN.darker(0.75)
ROBE = Ink('#1f8f5c', '#0c4c38', '#46c884', '#05281e', name='zümrüt cüppe')
ROBE_B = Ink('#15603f', '#083424', '#25865a', '#031a12', name='cüppe arkası')
GOLD = Ink('#e0b040', '#7e5418', '#fff0a0', '#3e260a', kind='metal', name='altın')
HOOD = Ink('#2a9658', '#124c30', '#74d48c', '#072818', name='kobra başlığı')
BELLY = Ink('#e2cc7a', '#8a6a34', '#fff4c0', '#4a3416', name='başlık karnı')
SNAKE = Ink('#58bc48', '#26662a', '#b0f07e', '#103414', name='asa yılanı')
WOOD = Ink('#5e3c24', '#2a160e', '#8e6442', '#140a06', name='asa')
JADE = Ink('#5cf0a0', '#1c9a5e', '#e6fff0', '#0a5432', name='yeşim')
JADE_C = (0.4, 1.0, 0.62)
JADE_HOT = (0.88, 1.0, 0.9)
JADE_GLOW = (0.1, 0.95, 0.45)
SEYE = (1.0, 0.95, 0.45)
SEYE_GLOW = (0.6, 0.95, 0.1)
TONGUE = (0.85, 0.12, 0.16)

UA, FA = 8.0, 7.6


# ------------------------------------------------------------------ parçalar
def _scales(c0, c1, rows, cols, r, w=0.6):
    """c0..c1 dikdörtgeninde pul yayları (ayrıntı listesi: mürekkep hilaller)."""
    det = []
    for j in range(rows):
        for i in range(cols):
            x = c0[0] + (c1[0] - c0[0]) * (i + 0.5 * (j % 2)) / cols
            y = c0[1] + (c1[1] - c0[1]) * j / max(1, rows - 1)
            det.append(('ink', [(x - r, y - r * 0.2), (x, y + r * 0.7), (x + r, y - r * 0.2)], w, (0.2, 0.2)))
    return det


def _hood(cv, hd, p, ph):
    """Kobra başlığı: başın arkasından yükselen geniş pullu yelpaze + alnın üstüne eğilen yılan başı."""
    fl = p['hood']
    hx, hy = hd
    s = 0.78 + 0.32 * fl
    top = (hx - 3.0, hy - 13.0 * s)
    pts = [(hx - 1.0, hy + 2.0), (hx - 6.0 * s, hy + 5.0), (hx - 10.5 * s, hy + 0.5), (hx - 11.0 * s, hy - 6.5 * s),
           (top[0] - 4.0 * s, top[1] + 2.2), (top[0] + 0.6, top[1] - 0.6), (hx + 1.0, hy - 10.5 * s), (hx + 1.8, hy - 4.5)]
    hood = cv.blob(pts)
    det = _scales((hx - 10.0 * s, hy - 11.0 * s), (hx + 0.6, hy + 3.0), 8, 6, 0.95, 0.55)
    # kara göz lekeleri (kobra damgası) + altın kenar
    for (ex, ey) in ((-7.0, -5.5), (-4.2, -9.0)):
        det.append(('col', cv.ellipse((hx + ex * s, hy + ey * s), 1.5 * s, 1.0 * s, -0.6), (0.04, 0.1, 0.07)))
        det.append(('col', cv.ellipse((hx + ex * s + 0.2, hy + ey * s - 0.1), 0.6 * s, 0.4 * s, -0.6), GOLD.hi))
    det.append(('stroke', [(hx - 6.0 * s, hy + 4.8), (hx - 10.3 * s, hy + 0.5), (hx - 10.8 * s, hy - 6.5 * s), (top[0] - 3.8 * s, top[1] + 2.2), (top[0] + 0.4, top[1] - 0.4)],
                1.5, GOLD.base, (0.1, 0.3)))
    cv.shape(hood, HOOD, z=-14, sd=1.4, hi=0.5, details=det, bounce=0.3, ol=1.0)
    # başlığın soluk karnı (öne bakan iç yüz; başın hemen arkasında)
    belly = cv.blob([(hx + 1.8, hy - 4.0), (hx + 0.9, hy - 10.2 * s), (top[0] + 0.6, top[1] - 0.4), (top[0] - 0.6, top[1] + 2.4), (hx - 1.2, hy - 8.0 * s), (hx - 0.4, hy - 4.6)])
    bdet = [('ink', [lerp2((hx - 0.8, hy - 4.6), (top[0] - 0.4, top[1] + 2.0), k / 5), lerp2((hx + 1.7, hy - 4.2), (top[0] + 0.6, top[1] - 0.2), k / 5)], 0.5, (0.2, 0.2))
            for k in range(1, 5)]
    cv.shape(belly, BELLY, z=-13.5, sd=0.8, hi=0.3, details=bdet, ol=0.8)
    # yılan başı: başlığın tepesinden öne kıvrılan boyun, alnın üstünde öne bakan baş
    nk0 = (top[0] + 0.2, top[1] + 0.8)
    sway = math.sin(ph * 1.3) * 0.5
    nk1 = (hx + 1.0 + sway, hy - 13.6 * s - 0.8 * fl)
    shd = (hx + 4.0 + sway + 0.8 * fl, hy - 10.0 * s - 0.6 * fl)
    cv.shape(cv.limb([nk0, nk1, shd], [1.6, 1.35, 1.15]), HOOD, z=19, sd=0.6, hi=0.3, ol=0.9,
             details=[('stroke', [lerp2(nk0, nk1, 0.3), nk1, lerp2(nk1, shd, 0.6)], 0.8, BELLY.base, (0.2, 0.4))])
    a = math.atan2(shd[1] - nk1[1], shd[0] - nk1[0]) + 0.15
    d = (math.cos(a), math.sin(a))
    n = (-d[1], d[0])
    sn = (shd[0] + d[0] * 3.0, shd[1] + d[1] * 3.0)
    head = cv.blob([(shd[0] - n[0] * 1.6 - d[0] * 0.6, shd[1] - n[1] * 1.6 - d[1] * 0.6), (shd[0] + d[0] * 1.6 - n[0] * 1.5, shd[1] + d[1] * 1.6 - n[1] * 1.5),
                    (sn[0] - n[0] * 0.4, sn[1] - n[1] * 0.4), (sn[0] + n[0] * 0.5, sn[1] + n[1] * 0.5), (shd[0] + n[0] * 1.3, shd[1] + n[1] * 1.3)])
    cv.shape(head, HOOD, z=19.5, sd=0.6, hi=0.35, ol=0.95, details=[('ink', [(shd[0] + d[0] * 0.6 + n[0] * 0.6, shd[1] + d[1] * 0.6 + n[1] * 0.6), (sn[0] + n[0] * 0.3, sn[1] + n[1] * 0.3)], 0.6, (0.2, 0.3))])
    q = (shd[0] + d[0] * 1.2 - n[0] * 0.6, shd[1] + d[1] * 1.2 - n[1] * 0.6)
    yk.eye_glow(cv, q, 0.5 + 0.15 * fl, 0.4, a, SEYE, SEYE_GLOW, 20, halo=2.2, halo_a=0.35 + 0.3 * fl)
    if math.sin(ph * 2.0) > 0.0 or fl > 0.5:   # dil
        t0 = (sn[0] + d[0] * 0.2, sn[1] + d[1] * 0.2 + 0.3)
        t1 = (t0[0] + d[0] * 2.2, t0[1] + d[1] * 2.2)
        cv.stroke([t0, t1], 0.5, z=19.4, col=TONGUE, taper=(0.1, 0.2))
        for sg in (-1, 1):
            cv.stroke([t1, (t1[0] + d[0] * 0.9 + n[0] * 0.5 * sg, t1[1] + d[1] * 0.9 + n[1] * 0.5 * sg)], 0.4, z=19.4, col=TONGUE, taper=(0.1, 0.8))
    # altın taç bandı (başlığın başa bağlandığı yer)
    cv.shape(cv.capsule((hx - 3.0, hy - 3.6), (hx + 3.0, hy - 4.2), 0.9, 0.9), GOLD, z=18, sd=0.3, hi=0.3, ol=0.85)
    cv.shape(cv.ellipse((hx + 1.0, hy - 4.0), 0.8, 0.8), JADE, z=18.2, sd=0.2, ol=0.7, glow=(0.05, 0.4, 0.2))


def _face(cv, hd, p):
    hx, hy = hd
    pain = p['pain']
    face = cv.blob([(hx - 2.6, hy - 3.2), (hx + 2.6, hy - 3.6), (hx + 4.0, hy - 1.4), (hx + 4.6, hy + 0.8, 0.0), (hx + 3.8, hy + 2.4), (hx + 3.4, hy + 4.6),
                    (hx + 0.6, hy + 4.8), (hx - 2.2, hy + 2.8), (hx - 3.0, hy - 0.4)])
    cv.shape(face, SKIN, z=14, sd=1.0, hi=0.3, bounce=0.3)
    # göz: sürmeli koyu göz, hafif yeşil ışıltı
    q = (hx + 2.2, hy - 1.2)
    sq = 0.4 if pain > 0.3 else 0.0
    cv.fill(cv.blob([(q[0] - 1.2, q[1] + 0.1), (q[0], q[1] - 0.7 + sq), (q[0] + 1.1, q[1] - 0.1, 0.0), (q[0], q[1] + 0.5)]), INK, z=15)
    yk.eye_glow(cv, (q[0] + 0.2, q[1] - 0.05), 0.35, 0.28 * (1 - 0.5 * sq), 0.0, JADE_C, JADE_GLOW, 16, halo=2.0, halo_a=0.25 + 0.35 * p['flare'])
    cv.stroke([(q[0] - 1.5, q[1] + 0.2), (q[0] - 2.6, q[1] - 0.3)], 0.6, z=15.5, col=INK, taper=(0.1, 0.9))          # sürme kuyruğu
    cv.stroke([(hx + 0.6, hy - 2.6 + sq), (hx + 2.4, hy - 2.6), (hx + 3.6, hy - 2.0)], 0.8, z=15.6, col=INK, taper=(0.2, 0.6))
    # pul peçe: burnun altından çeneye; tırtıklı altın pullar, uçta sarkan sikkeler
    veil = cv.blob([(hx - 1.6, hy + 0.0), (hx + 2.8, hy + 0.2), (hx + 5.0, hy + 0.6), (hx + 4.6, hy + 4.0), (hx + 3.8, hy + 6.2, 0.0),
                    (hx + 2.0, hy + 5.4), (hx + 0.4, hy + 6.4, 0.0), (hx - 1.0, hy + 5.0), (hx - 2.2, hy + 3.0)])
    det = _scales((hx - 1.0, hy + 1.0), (hx + 4.6, hy + 5.0), 4, 4, 0.7, 0.5)
    cv.shape(veil, GOLD, z=17, sd=0.8, hi=0.4, details=det, ol=0.9)
    for k, x in enumerate((hx + 0.4, hx + 2.0, hx + 3.8)):
        y = hy + 6.0 + (0.4 if k == 1 else 0.0)
        cv.shape(cv.ellipse((x, y + 0.9), 0.55, 0.55), GOLD, z=17.2 + k * 0.01, sd=0.2, ol=0.6)


def _sleeve_arm(cv, sp, tgt, z, near, p, ph, palm=0.0, bend=1):
    """Geniş saçaklı yen + yılan bilezikli ön kol + el (palm 0 kapalı tutuş .. 1 açık / avuç yukarı)."""
    e, h = yg.ik2(sp, tgt, UA, FA, bend)
    m = SKIN if near else SKIN_B
    R = ROBE if near else ROBE_B
    a_f = math.atan2(h[1] - e[1], h[0] - e[0])
    cv.shape(cv.limb([e, lerp2(e, h, 0.5), h], [1.1, 1.0, 0.9]), m, z=z, sd=0.5, hi=0.2 if near else 0.0, ol=0.85)
    # yılan bilezik: ön kolu saran altın sarmal (iki tur) + baş
    for k in range(3):
        q = lerp2(e, h, 0.45 + k * 0.16)
        cv.shape(cv.ellipse(q, 0.55, 1.35, a_f), GOLD, z=z + 0.1 + k * 0.01, sd=0.2, hi=0.2, ol=0.7)
    qh = lerp2(e, h, 0.95)
    cv.shape(cv.ellipse((qh[0] - math.sin(a_f) * 1.0, qh[1] + math.cos(a_f) * 1.0), 0.7, 0.5, a_f), GOLD, z=z + 0.15, sd=0.2, ol=0.6)
    # el
    ang = a_f + p['wr'] * (1 if near else 0)
    pc = (h[0] + math.cos(ang) * 1.2, h[1] + math.sin(ang) * 1.2)
    cv.shape(cv.ellipse(pc, 1.5, 1.05, ang), m, z=z + 0.3, sd=0.4, hi=0.2 if near else 0.0, ol=0.8)
    for k in range(4):
        fa = ang + (k - 1.5) * (0.18 + 0.2 * palm) - (1 - palm) * 0.2
        m1 = (pc[0] + math.cos(fa) * 1.8, pc[1] + math.sin(fa) * 1.8)
        fb = fa + (1.0 - palm) * 1.4 + palm * -0.3
        t = (m1[0] + math.cos(fb) * 1.4, m1[1] + math.sin(fb) * 1.4)
        cv.shape(cv.limb([pc, m1, t], [0.45, 0.4, 0.32]), m, z=z + 0.35 + k * 0.01, sd=0.2, ol=0.7)
    ta = ang - 1.2
    cv.shape(cv.limb([pc, (pc[0] + math.cos(ta) * 1.8, pc[1] + math.sin(ta) * 1.8)], [0.5, 0.35]), m, z=z + 0.32, sd=0.2, ol=0.7)
    # yen: omuzdan dirseğin altına çan biçimi, ağzında altın şerit + saçak
    a_u = math.atan2(e[1] - sp[1], e[0] - sp[0])
    dn = (math.cos(a_u + 0.9), math.sin(a_u + 0.9))
    cuff0 = lerp2(e, h, 0.3)
    mouth_a = (cuff0[0] - dn[0] * 0.4 + math.sin(a_f) * 2.4, cuff0[1] - dn[1] * 0.4 - math.cos(a_f) * 2.4)
    mouth_b = (cuff0[0] - math.sin(a_f) * 2.8 + dn[0] * 1.5, cuff0[1] + math.cos(a_f) * 2.8 + dn[1] * 1.5 + 1.2)
    sl = cv.blob([(sp[0] - 1.6, sp[1] - 0.8), (sp[0] + 1.6, sp[1] - 1.0), (e[0] + math.sin(a_u) * 1.4, e[1] - math.cos(a_u) * 1.4), mouth_a,
                  (mouth_b[0], mouth_b[1], 0.0), (e[0] - math.sin(a_u) * 2.2, e[1] + math.cos(a_u) * 2.2 + 1.0), (sp[0] - 1.8, sp[1] + 2.0)])
    cv.shape(sl, R, z=z + 0.5, sd=1.0, hi=0.3 if near else 0.0, ol=0.9,
             details=[('stroke', [mouth_a, lerp2(mouth_a, mouth_b, 0.5), mouth_b], 1.4, GOLD.base, (0.05, 0.05))] + cv.fold([lerp2(sp, e, 0.3), lerp2(e, mouth_b, 0.5)], 0.6, 1.0, 1))
    for k in range(4):   # yen saçağı
        q = lerp2(mouth_a, mouth_b, 0.15 + k * 0.25)
        aa = math.pi * 0.5 + math.sin(ph + k) * 0.25 + p['drag'] * 0.6
        cv.shape(ik.taper_path([cv.W(q), cv.W((q[0] + math.cos(aa) * 2.4, q[1] + math.sin(aa) * 2.4))], cv.u(0.7), (0.0, 0.7)), GOLD if k % 2 else R,
                 z=z + 0.55 + k * 0.01, sd=0.2, ol=0.6)
    return pc, ang


def _staff(cv, g, a, ph, p, z):
    """Asa: tutuş g, açı a (0 dik, + üstü öne). Yılan sarmalı + yeşim taşı. Döner: taş merkezi."""
    up = (math.sin(a), -math.cos(a))
    n = (-up[1], up[0])
    top = (g[0] + up[0] * 17.0, g[1] + up[1] * 17.0)
    bot = (g[0] - up[0] * (24.0 - p['lift']), g[1] - up[1] * (24.0 - p['lift']))
    cv.shape(cv.limb([bot, g, top], [0.8, 0.85, 0.75]), WOOD, z=z, sd=0.4, hi=0.2, ol=0.9,
             details=[('ink', [lerp2(bot, top, 0.3), lerp2(bot, top, 0.5)], 0.5, (0.3, 0.3))])
    # taç: altın çatal + yeşim
    gem = (top[0] + up[0] * 2.0, top[1] + up[1] * 2.0)
    for sg in (-1, 1):
        cv.shape(ik.taper_path([cv.W(top), cv.W((top[0] + n[0] * 1.6 * sg + up[0] * 1.0, top[1] + n[1] * 1.6 * sg + up[1] * 1.0)),
                                cv.W((gem[0] + n[0] * 1.2 * sg + up[0] * 1.4, gem[1] + n[1] * 1.2 * sg + up[1] * 1.4))], cv.u(0.7), (0.1, 0.8)), GOLD, z=z + 0.3, sd=0.2, hi=0.2, ol=0.7)
    ch = p['charge']
    r = 1.7 + 0.5 * ch
    yk.glow_soft(cv, gem, 4.5 + 6.0 * ch + 3.0 * p['burst'], JADE_GLOW, z=z + 0.4, blur=0.6, alpha=0.55 + 0.35 * ch)
    cv.shape(cv.ellipse(gem, r * 0.85, r, a), JADE, z=z + 0.5, sd=0.5, hi=0.5, ol=0.85, glow=(0.08, 0.6, 0.3),
             details=[('col', cv.ellipse((gem[0] - 0.4, gem[1] - 0.5), r * 0.35, r * 0.4), JADE_HOT)])
    # asaya sarılan yılan (önden geçen parçalar asanın önünde, arkadan geçenler arkasında)
    u0, u1 = 0.18, 0.86
    N = 26
    coil = p['coil'] + ph * 0.3
    pts = []
    for i in range(N + 1):
        u = u0 + (u1 - u0) * i / N
        q = lerp2(bot, top, u)
        k = coil + u * 3.2 * math.tau
        amp = 1.7 * (0.6 + 0.4 * math.sin(math.pi * (i / N) ** 0.7))
        pts.append(((q[0] + n[0] * math.sin(k) * amp, q[1] + n[1] * math.sin(k) * amp), math.cos(k)))
    for i in range(N):
        (q0, c0), (q1, _c1) = pts[i], pts[i + 1]
        w = 0.55 + 0.55 * (i / N) ** 0.6
        zz = z + (0.2 if c0 > 0 else -0.2) + i * 0.001
        cv.shape(cv.capsule(q0, q1, w, w * 1.02), SNAKE if c0 > 0 else SNAKE.darker(0.7), z=zz, sd=0.25, hi=0.15 if c0 > 0 else 0.0, ol=0.7)
        if c0 > 0 and i % 2 == 0:
            cv.stroke([q0, q1], 0.5, z=zz + 0.0005, col=(0.85, 0.9, 0.4), taper=(0.3, 0.3))
    # yılan başı: taşın altında öne uzanır (ileri-geri salınır)
    last = pts[-1][0]
    sw = math.sin(ph * 1.6) * 0.8 + p['strike'] * 2.0
    sh_ = (last[0] + n[0] * 1.0 + 1.5 + sw, last[1] - 0.6 - 0.3 * sw)
    cv.shape(cv.limb([last, lerp2(last, sh_, 0.5), sh_], [1.1, 1.0, 0.9]), SNAKE, z=z + 0.6, sd=0.3, hi=0.2, ol=0.8)
    hdp = cv.blob([(sh_[0] - 0.6, sh_[1] - 1.1), (sh_[0] + 1.8, sh_[1] - 0.8), (sh_[0] + 3.2, sh_[1] + 0.1, 0.0), (sh_[0] + 1.6, sh_[1] + 0.9), (sh_[0] - 0.6, sh_[1] + 0.9)])
    cv.shape(hdp, SNAKE, z=z + 0.7, sd=0.3, hi=0.3, ol=0.9)
    yk.eye_glow(cv, (sh_[0] + 1.2, sh_[1] - 0.35), 0.35, 0.3, 0, SEYE, SEYE_GLOW, z + 0.8, halo=2.0, halo_a=0.3)
    if math.sin(ph * 2.3 + 1.0) > 0.2:
        t0 = (sh_[0] + 3.2, sh_[1] + 0.2)
        cv.stroke([t0, (t0[0] + 1.6, t0[1] + 0.3)], 0.4, z=z + 0.65, col=TONGUE, taper=(0.1, 0.3))
    return gem


def _wisp(cv, c, r, tail, ph, z, k=1.0):
    """Yeşil ruh ışığı: parlak çekirdek + incelen kuyruk (tail: kuyruk ucu)."""
    yk.glow_soft(cv, c, r * 3.2, JADE_GLOW, z=z - 0.01, blur=0.6, alpha=0.6 * k)
    if tail is not None:
        mid = lerp2(c, tail, 0.5)
        mid = (mid[0] + math.sin(ph) * 0.8, mid[1] + math.cos(ph) * 0.8)
        cv.stroke([c, mid, tail], r * 2.6, z=z - 0.005, col=JADE_C, taper=(0.1, 0.95), alpha=0.75 * k, glow=JADE_GLOW)
        cv.stroke([c, mid, tail], r * 0.7, z=z - 0.004, col=INK, taper=(0.3, 0.9), alpha=0.35 * k)
    cv.fill(cv.ellipse(c, r, r), JADE_C, z=z, glow=JADE_GLOW, alpha=k)
    cv.fill(cv.ellipse((c[0] - r * 0.2, c[1] - r * 0.2), r * 0.55, r * 0.55), JADE_HOT, z=z + 0.01, glow=JADE_HOT, alpha=k)
    cv.stroke([(c[0] + math.cos(ph + t) * r * 1.5, c[1] + math.sin(ph + t) * r * 1.5) for t in np.linspace(0, 2.6, 6)], 0.6, z=z + 0.02, col=INK, taper=(0.5, 0.5), alpha=0.6 * k)


def _scales_fx(cv, c, k, ph, seed, z):
    """Işınlanma: dağılan yeşil pullar + yeşil sis."""
    if k <= 0.02:
        return
    rng = np.random.default_rng(seed)
    for i in range(4):
        q = (c[0] + rng.uniform(-6, 6), c[1] + rng.uniform(-12, 10) - 4 * k)
        # sis: yalnızca ışıma sayfasına yumuşak yeşil leke (doku sayfasında kontur halkası bırakmasın)
        yk.glow_soft(cv, q, (5 + 5 * k) * rng.uniform(0.8, 1.2), (0.2, 0.75, 0.45), z=z - 1 + i * 0.01, blur=0.7, alpha=0.35 * min(1.0, k * 1.6), ry=3 + 3 * k)
    for i in range(int(10 + 22 * k)):
        a = rng.uniform(0, math.tau) + ph * 0.5
        r = rng.uniform(2.0, 8.0 + 10.0 * k)
        q = (c[0] + math.cos(a) * r, c[1] + math.sin(a) * r * 1.4 - 5.0 * k * rng.uniform(0.3, 1))
        s = rng.uniform(0.5, 1.1)
        b = rng.uniform(0, math.tau)
        d = (math.cos(b), math.sin(b))
        nn = (-d[1], d[0])
        sc = cv.blob([(q[0] - d[0] * s, q[1] - d[1] * s), (q[0] + nn[0] * s * 0.9, q[1] + nn[1] * s * 0.9), (q[0] + d[0] * s * 1.3, q[1] + d[1] * s * 1.3, 0.0),
                      (q[0] - nn[0] * s * 0.9, q[1] - nn[1] * s * 0.9)])
        cv.shape(sc, SNAKE if i % 3 else GOLD, z=z + i * 0.001, sd=0.2, ol=0.6, glow=(0.05, 0.35, 0.15) if i % 2 else None)
    yk.glow_soft(cv, c, 10 + 8 * k, JADE_GLOW, z=z - 2, blur=0.6, alpha=0.3 * k)


# ------------------------------------------------------------------ bütün figür
def draw(cv, p):
    yg.bake_xf(cv)
    ph = p['ph']
    fxp = p.get('_fx', 'all')
    if fxp in ('all', 'fx'):
        _scales_fx(cv, (2.0, -20.0), p['mist'], ph, 41 + int(p['mist'] * 9), 50)
    if fxp == 'fx':
        return {'hand': (0.0, 0.0)}
    hip = (0.0, -16.0 + p['bob'])
    if p['streak'] > 0:
        u29.speed_lines(cv, (-6, -16), (1.0, 0.0), n=4, L=10 * p['streak'], spread=22, w=1.2, col=(0.5, 0.8, 0.6), alpha=0.4, z=-40, seed=int(ph * 7) % 40)
    u29.body_xf(cv, hip, p['rot'], p['sx'], p['sy'], p['jit'], 0.0)
    lean = p['lean']
    lx = lean * 3.0
    sh = (0.4 + lx, -29.0 + p['bob'] * 0.6 + lean * 1.2)
    hd = (sh[0] + 3.4 + lean, sh[1] - 4.8 + lean * 0.6)
    drag = p['drag']
    sw = math.sin(ph) * 0.6
    dx = -drag * 3.5

    # ---- kobra başlığı (arkada) + arka kol + asa
    _hood(cv, hd, p, ph)
    sb = (sh[0] - 0.6, sh[1] + 1.0)
    g = p['sg']
    _sleeve_arm(cv, sb, (g[0] - 0.6, g[1] + 0.6), -11, False, p, ph, palm=0.0)
    gem = _staff(cv, g, p['sa'], ph, p, -9)

    # ---- cüppe: omuzdan yere, altta genişleyen etek; önde pul işlemeli altın şerit
    hemL = (-10.0 + dx + sw, -3.0)
    hemR = (9.0 + dx * 0.3 + sw * 0.5, -3.2)
    robe = cv.blob([(sh[0] + 3.0, sh[1] - 1.0), (sh[0] - 2.6, sh[1] - 1.2), (sh[0] - 4.6, sh[1] + 3.0), (hip[0] - 4.6 + dx * 0.1, hip[1]),
                    (-7.0 + dx * 0.6, -9.0), (hemL[0], hemL[1], 0.0), (lerp2(hemL, hemR, 0.5)[0], -2.2), (hemR[0], hemR[1], 0.0), (5.6 + dx * 0.2, -9.0),
                    (hip[0] + 4.4, hip[1]), (sh[0] + 5.0, sh[1] + 5.0)])
    det = []
    det += cv.fold([(hip[0] - 1.6, hip[1] + 1), (-3.2 + dx * 0.5, -9.0), (-5.0 + dx * 0.8, -3.4)], 0.9, 1.2, 1)
    det += cv.fold([(hip[0] + 1.0, hip[1] + 2), (1.0 + dx * 0.3, -9.0), (0.6 + dx * 0.4, -3.4)], 0.7, 1.0, -1)
    det.append(('deep', cv.blob([(hemL[0], hemL[1]), (-5.0 + dx * 0.6, -9.0), (-2.4 + dx * 0.3, -3.0)])))
    cv.shape(robe, ROBE, z=0, sd=2.0, hi=0.5, details=det, hatch=0.3, bounce=0.35)
    # ön şerit (yakadan eteğe): altın, pul işlemeli
    bx0, bx1 = sh[0] + 3.6, hemR[0] - 2.2
    band = cv.blob([(sh[0] + 2.4, sh[1] + 0.5), (sh[0] + 4.6, sh[1] + 1.0), (hip[0] + 3.6, hip[1]), (bx1 + 1.2, -3.1), (bx1 - 1.6, -3.0), (hip[0] + 1.4, hip[1])])
    bdet = _scales((hip[0] + 1.6, hip[1] - 9.0), (bx1, -4.0), 9, 1, 0.8, 0.5)
    bdet.append(('ink', [(sh[0] + 3.0, sh[1] + 1.0), (hip[0] + 2.0, hip[1]), (bx1 - 1.2, -3.2)], 0.6, (0.1, 0.1)))
    cv.shape(band, GOLD, z=1, sd=0.6, hi=0.3, details=bdet, ol=0.8)
    # etek bandı + saçaklar (yere değer, harekette geride akar)
    cv.shape(cv.blob([(hemL[0] + 0.6, hemL[1] - 1.6), (hemR[0] - 0.4, hemR[1] - 1.6), (hemR[0], hemR[1], 0.0), (hemL[0], hemL[1], 0.0)]), GOLD, z=1.5, sd=0.4, hi=0.2, ol=0.8,
             details=_scales((hemL[0] + 1.0, hemL[1] - 0.9), (hemR[0] - 0.8, hemR[1] - 0.9), 1, 9, 0.6, 0.45))
    for i in range(16):
        u = i / 15
        q = lerp2(hemL, hemR, u)
        L = 2.8 + (i % 2) * 0.6
        aa = math.pi * 0.5 + math.sin(ph + i * 0.8) * 0.15 + drag * 0.55
        e = (q[0] + math.cos(aa) * L, min(0.2, q[1] + math.sin(aa) * L))
        cv.shape(ik.taper_path([cv.W(q), cv.W(lerp2(q, e, 0.5)), cv.W(e)], cv.u(0.75), prof=lambda x: 1.0 if x < 0.75 else max(0.3, 1.0 - (x - 0.75) * 3)),
                 GOLD if i % 3 == 0 else ROBE_B, z=0.5 + (i % 2) * 0.01, sd=0.2, ol=0.6)
    # kuşak: altın yılan
    cv.shape(cv.capsule((hip[0] - 4.4, hip[1] - 0.4), (hip[0] + 4.4, hip[1] - 0.6), 0.9, 0.9), GOLD, z=2, sd=0.3, hi=0.3, ol=0.85,
             details=_scales((hip[0] - 3.6, hip[1] - 0.6), (hip[0] + 3.6, hip[1] - 0.6), 1, 6, 0.5, 0.4))
    cv.shape(cv.ellipse((hip[0] + 4.4, hip[1] - 0.6), 1.0, 0.8), GOLD, z=2.1, sd=0.3, hi=0.3, ol=0.85)
    yk.eye_glow(cv, (hip[0] + 4.7, hip[1] - 0.8), 0.25, 0.2, 0, SEYE, SEYE_GLOW, 2.2, halo=1.6, halo_a=0.2)

    # ---- omuz pelerinciği: pul pul yeşil-altın
    edge = yk.ragged((sh[0] - 5.6, sh[1] + 6.0), (sh[0] + 5.4, sh[1] + 4.4), 6, 1.3, seed=12, side=1.0)
    cape = cv.blob([(sh[0] + 3.8, sh[1] - 1.6), (sh[0] + 0.4, sh[1] - 2.6), (sh[0] - 3.6, sh[1] - 2.0), (sh[0] - 5.8, sh[1] + 1.4), (sh[0] - 5.6, sh[1] + 6.0, 0.0)] + edge +
                   [(sh[0] + 5.4, sh[1] + 4.4, 0.0), (sh[0] + 5.6, sh[1] + 1.2)])
    cdet = _scales((sh[0] - 4.6, sh[1] - 0.6), (sh[0] + 4.4, sh[1] + 4.4), 4, 6, 0.8, 0.55)
    cdet.append(('stroke', [(sh[0] - 5.4, sh[1] + 5.2), (sh[0], sh[1] + 5.4), (sh[0] + 5.0, sh[1] + 3.9)], 1.1, GOLD.base, (0.1, 0.1)))
    cv.shape(cape, HOOD, z=16, sd=1.0, hi=0.4, details=cdet, ol=1.0)
    _face(cv, hd, p)

    # ---- ön kol
    sf = (sh[0] + 2.2, sh[1] + 1.6)
    pc, ang = _sleeve_arm(cv, sf, p['af'], 30, True, p, ph, palm=p['palm'])

    # ---- şifa: taşta ışık sarmalı / öne-yukarı patlama
    ch = p['charge']
    if ch > 0.05:
        for k in range(3):
            a0 = ph * 2.0 + k * math.tau / 3
            pts = [(gem[0] + math.cos(a0 + u * 4.0) * (1.5 + 6.5 * ch * (1 - u)), gem[1] + math.sin(a0 + u * 4.0) * (1.5 + 6.5 * ch * (1 - u)) * 0.85)
                   for u in np.linspace(0, 1, 10)]
            cv.stroke(pts, 1.4, z=36 + k * 0.01, col=JADE_C, taper=(0.8, 0.2), alpha=0.85, glow=JADE_GLOW)
            cv.stroke(pts[:5], 0.5, z=36.005 + k * 0.01, col=INK, taper=(0.6, 0.4), alpha=0.5)
        yk.sparks(cv, gem, int(4 + 6 * ch), 3.0, 4.0 + 5.0 * ch, JADE_HOT, 37, seed=int(ph * 5) + 2, w=0.8, glow=JADE_GLOW)
    bu = p['burst']
    if bu > 0.05:
        ba = -0.42
        d = (math.cos(ba), math.sin(ba))
        nn = (-d[1], d[0])
        L = 6.0 + 10.0 * bu
        g0 = (gem[0] + d[0] * 1.0, gem[1] + d[1] * 1.0)
        beam = cv.blob([(g0[0] + nn[0] * 1.2, g0[1] + nn[1] * 1.2), (g0[0] + d[0] * L + nn[0] * 2.8, g0[1] + d[1] * L + nn[1] * 2.8),
                        (g0[0] + d[0] * (L + 1.5), g0[1] + d[1] * (L + 1.5)), (g0[0] + d[0] * L - nn[0] * 2.8, g0[1] + d[1] * L - nn[1] * 2.8),
                        (g0[0] - nn[0] * 1.2, g0[1] - nn[1] * 1.2)])
        cv.fill(beam, JADE_C, z=38, glow=JADE_GLOW, alpha=0.8 * min(1.0, bu * 1.4))
        cv.stroke([g0, (g0[0] + d[0] * L * 0.9, g0[1] + d[1] * L * 0.9)], 1.4, z=38.1, col=JADE_HOT, taper=(0.1, 0.6), glow=JADE_HOT)
        for k in range(10):   # yıldız patlaması
            a = k / 10 * math.tau + 0.2
            r0, r1 = 2.4, 2.4 + (3.0 + 4.0 * (k % 2)) * bu
            cv.stroke([(gem[0] + math.cos(a) * r0, gem[1] + math.sin(a) * r0), (gem[0] + math.cos(a) * r1, gem[1] + math.sin(a) * r1)], 1.2, z=38.2, col=JADE_HOT,
                      taper=(0.1, 0.9), glow=JADE_GLOW)
        ring = [(gem[0] + math.cos(t) * (3.0 + 5.0 * bu), gem[1] + math.sin(t) * (3.0 + 5.0 * bu)) for t in np.linspace(0, math.tau, 20)]
        cv.stroke(ring, 1.4 * (1.2 - bu * 0.5), z=38.3, col=JADE_C, taper=(0.0, 0.0), glow=JADE_GLOW, alpha=0.8)
        yk.glow_soft(cv, gem, 8.0 + 6.0 * bu, JADE_GLOW, z=37.9, blur=0.6, alpha=0.7)

    # ---- ruh ışıkları (atk_wisp): avuçta toplanır / ileri salınır
    wg = p['wg']
    if wg > 0.02:
        c = lerp2(pc, gem, 0.45)
        c = (c[0], c[1] - 1.5)
        for k in range(3):
            a = ph * 1.6 + k * math.tau / 3
            r = 6.5 * (1.0 - wg) + 2.2
            q = (c[0] + math.cos(a) * r, c[1] + math.sin(a) * r * 0.7)
            tl = (q[0] + math.cos(a - 1.2) * 3.0, q[1] + math.sin(a - 1.2) * 2.0)
            _wisp(cv, q, 0.9 + 0.6 * wg, tl, ph + k, 39 + k * 0.01, k=min(1.0, 0.4 + wg))
        yk.glow_soft(cv, c, 3.0 + 4.0 * wg, JADE_GLOW, z=38.8, alpha=0.4 * wg)
    wr = p['wrel']
    if wr > 0.02:
        for k, a in enumerate((-0.45, -0.12, 0.2)):
            dd = 3.0 + 20.0 * wr * (1.0 - 0.1 * k)
            q = (pc[0] + math.cos(a) * dd, pc[1] + math.sin(a) * dd)
            tl = (q[0] - math.cos(a) * (3.0 + 6.0 * wr), q[1] - math.sin(a) * (3.0 + 6.0 * wr) + math.sin(ph + k) * 1.2)
            _wisp(cv, q, 1.5, tl, ph + k * 2, 39 + k * 0.01)
    hand = u29.to_world(cv, gem)
    cv.pop()
    return {'hand': hand}


# ================================================================== animasyon tabloları
REST = dict(bob=0.0, lean=0.1, rot=0.0, sx=1.0, sy=1.0, jit=(0.0, 0.0), af=(6.6, -21.8), wr=-0.9, palm=0.8, sg=(10.0, -21.0), sa=0.04, lift=0.0,
            coil=0.0, strike=0.0, hood=0.0, drag=0.0, flare=0.0, pain=0.0, charge=0.0, burst=0.0, wg=0.0, wrel=0.0, dis=0.0, mist=0.0, streak=0.0)
S2 = math.tau


def _keys(ts, frames):
    return [(t, d, 'l') for t, d in zip(ts, frames)]


def _idle(t):
    s = math.sin
    a = S2 * t
    return dict(REST, bob=0.5 * s(a), rot=0.035 * s(a + 0.3), lean=0.1 + 0.05 * s(a), af=(6.6 + 0.4 * s(a + 1), -21.8 + 0.5 * s(a)), sa=0.04 + 0.03 * s(a + 0.6),
                sg=(10.0 + 0.3 * s(a), -21.0 + 0.4 * s(a)), coil=a, strike=0.3 * max(0.0, s(a * 2)), hood=0.1 + 0.1 * s(a))


def _move(t):
    s = math.sin
    a = S2 * t
    return dict(REST, bob=-0.8 - 0.5 * s(2 * a), rot=0.07, lean=0.35, drag=1.0 + 0.2 * s(a), af=(8.5, -20.5 + 0.5 * s(a)), sa=0.14 + 0.03 * s(a),
                sg=(11.0, -20.5 + 0.3 * s(2 * a)), lift=2.0, coil=a, hood=0.15, streak=0.5)


_HEAL_TS = [0.0, 0.12, 0.24, 0.36, 0.48, 0.54, 0.66, 0.8, 0.9]
_HEAL = _keys(_HEAL_TS, [
    dict(lean=0.05, sg=(10.5, -24.0), sa=0.0, lift=3.0, af=(7.0, -22.0), charge=0.15, hood=0.2),
    dict(lean=-0.2, bob=-0.6, rot=-0.06, sg=(9.5, -29.0), sa=-0.06, lift=8.0, af=(9.0, -27.0), palm=0.9, wr=-0.5, charge=0.4, hood=0.5, flare=0.3, sy=1.03),
    dict(lean=-0.35, bob=-1.2, rot=-0.12, sg=(8.5, -32.4), sa=-0.1, lift=12.0, af=(10.0, -31.0), palm=1.0, wr=-0.8, charge=0.75, hood=0.9, flare=0.6, sy=1.05, strike=0.5),
    dict(lean=-0.4, bob=-1.4, rot=-0.14, sg=(8.3, -32.8), sa=-0.12, lift=12.5, af=(10.2, -31.6), palm=1.0, wr=-0.8, charge=1.0, hood=1.0, flare=1.0, sy=1.06, strike=0.8),
    # temas: asa öne-yukarı uzanır, taştan parlak patlama
    dict(lean=0.35, bob=-0.6, rot=0.1, sg=(13.0, -30.0), sa=0.5, lift=12.0, af=(13.0, -27.0), palm=1.0, wr=-0.3, charge=0.3, burst=0.5, hood=1.0, flare=1.0,
         jit=(1.2, 0.0), sy=1.02),
    dict(lean=0.4, bob=-0.5, rot=0.12, sg=(13.4, -30.0), sa=0.55, lift=12.0, af=(13.5, -26.0), charge=0.15, burst=1.0, hood=0.9, flare=0.8, jit=(1.5, 0.0)),
    dict(lean=0.3, bob=-0.3, rot=0.08, sg=(12.5, -28.0), sa=0.38, lift=9.0, af=(11.0, -24.0), palm=0.6, charge=0.0, burst=0.6, hood=0.6, flare=0.5, jit=(1.0, 0.0)),
    dict(lean=0.15, bob=0.0, rot=0.02, sg=(11.0, -24.0), sa=0.12, lift=3.0, af=(8.0, -21.0), palm=0.4, burst=0.0, hood=0.3, flare=0.2, jit=(0.4, 0.0)),
    dict(lean=0.1, sg=(10.0, -21.0), sa=0.04, lift=0.0, af=(6.6, -21.8), wr=-0.9, palm=0.8, hood=0.1, flare=0.0, jit=(0.0, 0.0)),
])

_WISP_TS = [0.0, 0.14, 0.28, 0.42, 0.5, 0.62, 0.76, 0.9]
_WISP = _keys(_WISP_TS, [
    dict(lean=0.05, sg=(11.0, -22.0), sa=0.15, af=(9.0, -21.0), palm=0.8, wr=-0.6, wg=0.1),
    dict(lean=-0.1, bob=0.5, rot=-0.05, sg=(10.0, -21.0), sa=0.2, af=(8.0, -20.0), palm=1.0, wr=-1.0, wg=0.4, hood=0.3, flare=0.3, sx=1.02, sy=0.98),
    dict(lean=-0.25, bob=1.0, rot=-0.1, sg=(9.0, -21.0), sa=0.24, af=(6.0, -19.5), palm=1.0, wr=-1.2, wg=0.75, hood=0.5, flare=0.6, sx=1.04, sy=0.96),
    dict(lean=-0.3, bob=1.2, rot=-0.12, sg=(8.8, -21.0), sa=0.25, af=(5.4, -19.2), palm=1.0, wr=-1.25, wg=1.0, hood=0.6, flare=0.9, sx=1.05, sy=0.95, jit=(-0.6, 0.0)),
    # temas: eller ileri itilir, ışıklar salınır
    dict(lean=0.5, bob=-0.4, rot=0.12, sg=(13.0, -22.0), sa=0.35, af=(16.0, -23.0), palm=1.0, wr=-0.2, wg=0.0, wrel=0.2, hood=0.7, flare=1.0, jit=(1.5, 0.0), sx=0.98, sy=1.03),
    dict(lean=0.55, bob=-0.2, rot=0.12, sg=(13.4, -22.0), sa=0.36, af=(16.4, -22.5), wrel=0.65, hood=0.6, flare=0.7, jit=(1.8, 0.0)),
    dict(lean=0.3, bob=0.0, rot=0.05, sg=(11.5, -21.5), sa=0.18, af=(11.0, -21.0), palm=0.6, wr=0.0, wrel=0.0, hood=0.3, flare=0.3, jit=(1.0, 0.0)),
    dict(lean=0.1, sg=(10.0, -21.0), sa=0.04, af=(6.6, -21.8), wr=-0.9, palm=0.8, hood=0.1, flare=0.0, jit=(0.3, 0.0)),
])

_HURT = _keys([0.0, 0.5, 1.0], [
    dict(rot=-0.22, bob=0.8, lean=-0.3, jit=(-2.0, 0.0), af=(4.0, -25.0), palm=1.0, wr=-0.6, sg=(8.0, -22.0), sa=-0.18, lift=1.0, pain=1.0, hood=0.9, drag=-0.6, strike=1.0),
    dict(rot=-0.1, bob=0.6, lean=-0.1, jit=(-2.6, 0.0), af=(5.5, -22.0), sg=(9.0, -21.5), sa=-0.06, pain=0.7, hood=0.6, drag=-0.3),
    dict(rot=-0.03, bob=0.2, lean=0.05, jit=(-1.8, 0.0), af=(6.8, -20.2), sg=(9.8, -21.0), sa=0.02, pain=0.3, hood=0.2),
])

_BLINK = _keys([0.0, 0.2, 0.4, 0.6, 0.8, 1.0], [
    dict(bob=0.8, lean=0.0, af=(8.0, -24.0), palm=1.0, wr=-0.8, sg=(10.0, -24.0), sa=0.0, lift=3.0, charge=0.6, hood=1.0, flare=1.0, mist=0.3, sy=0.97),
    dict(bob=0.4, charge=0.8, mist=0.6, dis=0.22, sx=0.96, sy=1.03),
    dict(bob=0.0, charge=0.9, mist=0.9, dis=0.48, sx=0.92, sy=1.05),
    dict(bob=-0.4, mist=1.0, dis=0.72, sx=0.86, sy=1.08),
    dict(bob=-0.8, mist=0.8, dis=0.92, sx=0.82, sy=1.1),
    dict(bob=-1.0, mist=0.45, dis=1.0, sx=0.8, sy=1.12),
])


def _row(frames, fps, loop, pose, ts=None, mk=None, vx=None):
    return dict(frames=frames, fps=fps, loop=loop, pose=pose, ts=ts, mk=mk, vx=vx)


def _nl(keys):
    return lambda t: pose_at(t, keys, base=REST)


ROWS = None


def anims_for(var='yilan_kami'):
    global ROWS
    if ROWS is None:
        ROWS = {
            'idle': _row(8, 8, True, _idle),
            'move': _row(8, 10, True, _move),
            'hurt': _row(3, 14, False, _nl(_HURT)),
            'atk_heal': _row(9, 10, False, _nl(_HEAL), ts=_HEAL_TS, mk=[0.36, 0.48, 0.66]),
            'atk_wisp': _row(8, 10, False, _nl(_WISP), ts=_WISP_TS, mk=[0.42, 0.5, 0.66]),
            'blink': _row(6, 12, False, _nl(_BLINK)),
        }
    return ROWS


def durum_for(var='yilan_kami'):
    d = {'idle': 'idle', 'chase': 'move', 'recover': 'idle', 'evade': 'move', '_hurt': 'hurt', '_hurt_big': 'hurt', '_break': 'hurt'}
    for m in ('heal', 'wisp'):
        for k in ('windup', 'act', 'recover'):
            d['%s/%s' % (k, m)] = 'atk_' + m
    d.update({'blink_out': 'blink', 'blink_in': 'blink'})
    return d


def frame_time(row, i):
    if row['ts']:
        return row['ts'][i]
    if row['loop']:
        return i / row['frames']
    return i / max(1, row['frames'] - 1)


SHADE = dict(outer=0.6, rim=0.7, rim_col=(0.75, 1.0, 0.85), rim_dir=(0.6, -0.8), rim_w=1.3, form=(4.0, (0.74, 0.8, 0.84)))


def render_frame(anim, i, var='yilan_kami', ss=3):
    row = anims_for(var)[anim]
    tt = frame_time(row, i)
    p = dict(row['pose'](tt))
    p['ph'] = tt * math.tau * (1 if row['loop'] else 0.6) + (0 if row['loop'] else i * 0.9)
    split = p.get('dis', 0.0) > 0
    if split:
        p['_fx'] = 'body'
    cv = u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    if split:
        rgba, em = u29.dissolve(rgba, em, p['dis'], seed=57, hd=cv.hd, grad=(-0.3, -0.5), hot=(0.3, 1.0, 0.5), hot_a=1.0)
        cf = u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss)
        draw(cf, dict(p, _fx='fx'))
        fr, _n, fe = cf.finish(outer=0.4)
        rgba, em = u29.over(fr, fe, rgba, em)
    return rgba, nm, em, info
