"""v39: Tunga Hayaleti (kimlik tunga_hayaleti) — Alp Er Tunga ordusunun kurganlardan kalkan hayalet atlısı (Bozkır,
AI lancer). Et değil: ışıyan bir Saka savaşçısının anısı.

Tasarım: uzun boylu hayalet; altın levhalı sivri Saka keçe / tunç börkü (ok ucu levhaları, tepede altın topuz),
yanak siperi ve ensel; yüz yerine zifiri bir oyuk, içinde iki turkuaz göz ışığı. Turkuaz ışıyan lamel zırh (levha
kenarları ışır), soluk altın kemer ve yaka, omuzda lamel omuzluk; uzun yırtık gök mavisi pelerin rüzgârda akar.
Dizlerden aşağısı yoktur: baldırlar akan sis kuyruklarına dönüşür (süzülür, ayak yere zor değer). Gövde boyunun
~1,3 katı süvari kargısı: altın halkalı sap, yaprak temren, temrenin dibinde at kılı tuğ ve küçük çatal flama.

Satırlar (y39_mizrak_kit ortak tabloları): idle 8 (süzülüş salınımı, pelerin / sis akışı), move 8 (süzülerek
ilerleyiş), hurt 3, atk_lunge 9 (mk), atk_sweep 8 (mk), atk_throw 8 (mk; ışıktan cirit).
Çapa 'hand' = kargı ucu (fırlatmada cirit ucu), her karede. Hücre 448x352 (dünya 112x88), ayak (144, 336).
"""
import math

import numpy as np
import skia

import inkkit as ik
from inkkit import Ink, INK
from rig import lerp2, chain
import yaratik_ink_kit as yk
import ucan_v29 as u29
import y39_mizrak_kit as mk
from y39_mizrak_kit import along, add, dirv

TEX = 4.0
CELL = (448, 352)      # dünya 112 x 88 (uzun kargı: ileri hamlede uç ~ +70, kalkık savuruşta ~ -84)
FEET = (144, 336)      # dünya (36, 84)

# ------------------------------------------------------------ malzemeler
PLATE = Ink('#2f8f8c', '#15495e', '#8ef0dc', '#0a2434', kind='metal', name='hayalet lamel')
PLATE_B = PLATE.darker(0.72)
GOLD = Ink('#d6a648', '#7a4a1e', '#fff2a8', '#3a2208', kind='metal', name='soluk altın')
GOLD_B = GOLD.darker(0.72)
CLOAK = Ink('#5a9ed4', '#2a5288', '#b0dcf6', '#142a52', name='gök pelerin')
CLOAK_B = Ink('#3c78ac', '#1c3c6a', '#6aa6d6', '#0e1c3c', name='pelerin içi')
FELT = Ink('#22586c', '#0f2e40', '#4c96a6', '#071822', name='keçe börk')
UNDER = Ink('#284a62', '#122438', '#4c7690', '#08121e', name='kaftan')
UNDER_B = UNDER.darker(0.72)
SPIRIT = Ink('#a8e6e4', '#4e9aa8', '#eafffc', '#24525e', name='ruh eli')
SPIRIT_B = SPIRIT.darker(0.75)
WOOD = Ink('#3e3a40', '#1a161c', '#6e6670', name='kargı sapı')
HAIR = Ink('#dfe8ee', '#7c8ea0', '#ffffff', '#3a4656', name='at kılı tuğ')
MIST = Ink('#9ee6e0', '#4c98a6', '#e4fffa', '#1e4a56', name='sis')
EYE = (0.75, 1.0, 0.97)
GLOW = (0.12, 0.92, 0.84)
GLOW_D = (0.05, 0.42, 0.42)
VOID = (0.015, 0.03, 0.055)


def _mist_tail(cv, start, ang, L, w0, z, ph, seed, fade=0.75, wave=0.5, mat=MIST, glow_a=0.35):
    """Sis kuyruğu: kökü geniş, dalgalanarak incelen şerit; ucu silgiyle saydamlaşır, ince ışıma."""
    pts = chain(start, 6, L / 6.0, ang, 0.08, ph, wave)
    W = [cv.W(q) for q in pts]
    path = ik.taper_path(W, cv.u(w0), prof=lambda u: max(0.06, (1.0 - min(1.0, u)) ** 0.7 * (0.9 + 0.2 * math.sin(u * 8 + seed))))
    cv.shape(path, mat, z=z, sd=1.2, hi=0.3, ol=0.55, glow=(GLOW_D[0] * glow_a, GLOW_D[1] * glow_a, GLOW_D[2] * glow_a),
             details=[('ink', [pts[1], lerp2(pts[1], pts[3], 0.5), pts[3]], 0.8, (0.3, 0.7))])
    er = ik.taper_path(W[len(W) // 2 - 1:], cv.u(w0 * 2.4), (0.7, 0.0))

    def fn(c, er=er):
        p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, fade))
        p.setBlendMode(skia.BlendMode.kDstOut)
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.BlurStyle.kNormal_BlurStyle, cv.u(2.2)))
        c.drawPath(er, p)
    cv._q(z + 0.05, fn)
    return pts


class Style:
    H0 = 22.0
    LIFT = 3.0
    TORSO = 16.5
    L_TH, L_SH = 11.0, 11.5
    LANCE = (12.0, 58.0)
    STREAK = (0.45, 0.95, 0.92)
    GLOW = GLOW

    # ---- yer: sis birikintisi, toplanan zerreler
    def ground_fx(self, cv, p, J):
        ph = p['ph']
        cx = J['hip'][0] - 2.0
        yk.wash(cv, cv.ellipse((cx, -0.6), 13.0, 2.2), MIST.base, 0.22, z=-45, blur=1.2, glow=GLOW_D, glow_a=0.25)
        yk.wash(cv, cv.ellipse((cx - 6.0 + math.sin(ph) * 1.5, -1.2), 7.0, 1.6), MIST.hi, 0.18, z=-44.9, blur=1.0)
        if p['mist'] > 0.02:   # hazırlık: dört yandan toplanan sis zerreleri + gövde halesi
            k = p['mist']
            c = (J['hip'][0], J['hip'][1] - 12.0)
            u29.flecks(cv, c, int(6 + 10 * k), 10.0 - 4.0 * k, 22.0 - 6.0 * k, MIST.hi, 40, seed=int(ph * 9) % 31, s0=0.3, s1=0.8, glow=GLOW_D)
            yk.glow_soft(cv, c, 18.0, GLOW, z=-46, blur=0.7, alpha=0.25 * k)

    # ---- arka katman: pelerin + sis kuyrukları
    def back_layer(self, cv, p, J):
        ph = p['ph']
        T = J['T']
        cw = p['cw']
        sk = p['sk']
        yk.glow_soft(cv, T(8.0, 0.0), 17.0, GLOW, z=-48, blur=0.75, alpha=0.16 + 0.18 * p['flare'])
        # pelerin: omuzlardan arkaya akan uzun yırtık kumaş (rüzgâr cw: + daha yatay, geriye)
        s0 = T(self.TORSO + 0.4, -1.0)
        s1 = T(self.TORSO - 1.0, -4.6)
        hip = J['hip']
        fl = math.sin(ph + 0.6) * 1.3
        bx = hip[0] - 9.0 - 9.0 * cw + sk * 1.2
        by = -4.0 - 6.0 * cw + fl * 0.5
        hem = yk.ragged((hip[0] - 3.5 + sk * 0.5, hip[1] + 14.0 - cw * 3.0), (bx - 6.0 + fl, by - 2.0), 5, 3.6, seed=5, side=1.0)
        pts = [s0, s1, (hip[0] - 6.5 - 3.0 * cw, hip[1] - 8.0 - cw * 1.5), (bx - 7.0 + fl * 0.8, by - 12.0 - cw * 4.0 + fl),
               (bx - 8.0 + fl, by - 3.0, 0.0)] + hem[::-1] + [(hip[0] - 3.5 + sk * 0.5, hip[1] + 14.0 - cw * 3.0, 0.0), (hip[0] - 2.0, hip[1] + 2.0)]
        cloak = cv.blob(pts)
        det = []
        det += cv.fold([lerp2(s1, (bx, by), 0.15), lerp2(s1, (bx - 2, by - 4), 0.5), (bx - 3.0 + fl, by - 4.0)], 1.0, 1.3, 1)
        det += cv.fold([lerp2(s0, hip, 0.4), (hip[0] - 5.0 - cw * 2, hip[1] + 4.0), (hip[0] - 6.0 - cw * 4 + fl * 0.5, hip[1] + 12.0 - cw * 3)], 0.9, 1.2, -1)
        det.append(('deep', cv.blob([(bx - 8.0 + fl, by - 3.0), (bx - 2.0, by - 8.0), (bx + 0.0, by - 1.5)])))
        cv.shape(cloak, CLOAK_B, z=-26, sd=2.4, hi=0.4, details=det, hatch=0.3, bounce=0.3)
        # pelerin kenarı ışır (hayalet)
        cv.stroke([(q[0], q[1]) for q in hem[::2]], 0.9, z=-25.9, col=CLOAK.hi, taper=(0.2, 0.2), glow=GLOW_D, alpha=0.8)
        # ön kanat: omuzdan sarkan pelerin şeridi (gövdenin arkasında, uzun)
        for i, (o, ln, zz) in enumerate(((0.0, 1.0, -24.0), (2.2, 0.8, -23.5))):
            st = T(self.TORSO - 1.5 - o, -4.0)
            _mist_tail(cv, st, math.pi * (0.62 + 0.08 * cw) + sk * 0.04, 26.0 * ln, 3.4, zz, ph + i * 1.7, 2 + i, fade=0.55,
                       mat=CLOAK if i == 0 else CLOAK_B, glow_a=0.2)
        # sis kuyrukları: dizlerden aşağı / geriye akan bacaklar (ayak yere zor değer)
        for i, (kn, f, zz, sc) in enumerate(((J['kb'], J['fbt'], -16.0, 0.85), (J['kf'], J['fft'], -2.0, 1.0))):
            ang = math.atan2(f[1] - kn[1], f[0] - kn[0])
            ang = ang + 0.35 + 0.2 * cw
            _mist_tail(cv, (kn[0], kn[1] - 0.5), ang, 13.5 * sc, 3.6 * sc, zz, ph * 1.3 + i * 2.1, 7 + i, fade=0.7,
                       mat=MIST if i else MIST.darker(0.8))
        for i in range(3):   # ince sis telleri
            st = (J['hip'][0] - 3.0 + i * 2.0, J['hip'][1] + 8.0)
            yk.wisp(cv, st, math.pi * (0.58 + 0.06 * i) + 0.15 * cw, 12.0 + 3 * i, 2.0, MIST, -17 + i * 0.1, ph=ph * 1.5 + i * 2.0,
                    curl=0.7, alpha=0.5, glow=GLOW_D, glow_a=0.4)

    # ---- bacaklar: lamel etekli uyluklar (dizden aşağısı sis)
    def legs(self, cv, p, J):
        for side in (0, 1):
            hj = J['hb'] if side == 0 else J['hf']
            kn = J['kb'] if side == 0 else J['kf']
            m = UNDER if side else UNDER_B
            cv.shape(cv.limb([hj, lerp2(hj, kn, 0.5), kn], [3.6, 3.4, 2.8]), m, z=-12.0 if side == 0 else 0.5, sd=1.8,
                     details=cv.fold([lerp2(hj, kn, 0.3), lerp2(hj, kn, 0.8)], 0.6, 1.0, 1))
            # diz: altın kapak + ışıyan kırık kenar (sis buradan başlar)
            cv.shape(cv.ellipse(kn, 2.4, 1.9, math.atan2(kn[1] - hj[1], kn[0] - hj[0])), GOLD if side else GOLD_B, z=-11.8 if side == 0 else 0.7,
                     sd=0.6, hi=0.4 if side else 0.0, ol=0.8)
            yk.glow_soft(cv, (kn[0], kn[1] + 1.2), 3.6, GLOW, z=-11.7 if side == 0 else 0.8, alpha=0.45)

    # ---- gövde: ışıyan lamel zırh
    def torso(self, cv, p, J):
        T = J['T']
        ph = p['ph']
        tl = self.TORSO
        torso = cv.blob([T(-1.5, -5.4), T(3.0, -4.8), T(7.5, -5.8), T(12.0, -7.0), T(15.2, -6.0), T(17.2, -3.0), T(17.4, 2.2),
                         T(15.2, 6.6), T(11.0, 7.8), T(6.5, 6.4), T(3.0, 5.0), T(-1.5, 5.8)])
        det = []
        rows = (1.5, 3.8, 6.1, 8.4, 10.7, 13.0)
        for i, u in enumerate(rows):
            det.append(('shade', cv.wedge([T(u + 2.0, -6.6), T(u + 1.8, 0.6), T(u + 2.0, 7.4)], 0.4, 1.0)))
            det.append(('ink', [T(u, -7.0), T(u - 0.3, 0.6), T(u, 7.8)], 1.1, (0.05, 0.05)))
            for v in (-5.6, -3.4, -1.2, 1.0, 3.2, 5.4):
                vv = v + (1.1 if i % 2 else 0.0)
                det.append(('ink', [T(u + 0.2, vv), T(u + 2.1, vv)], 0.85, (0.1, 0.3)))
        cv.shape(torso, PLATE, z=2.0, sd=3.2, hi=0.6, details=det, deep=0.2, bounce=0.35, glow=(0.0, 0.06, 0.06))
        # levha sıralarının ışıyan alt kenarları (nabız)
        pul = 0.75 + 0.25 * math.sin(ph * 2.0)
        for i, u in enumerate(rows[1:]):
            cv.stroke([T(u + 0.25, -5.0 + (i % 2) * 0.6), T(u + 0.0, 0.6), T(u + 0.25, 6.4 - (i % 2) * 0.6)], 0.9, z=2.3,
                      col=(0.55, 1.0, 0.92), taper=(0.3, 0.3), glow=(GLOW[0] * pul * 0.7, GLOW[1] * pul * 0.7, GLOW[2] * pul * 0.7), alpha=0.85)
        # yaka: altın boyunluk
        col_ = cv.blob([T(14.2, -5.2), T(17.6, -3.8), T(18.4, 0.4), T(17.4, 3.8), T(14.6, 4.4), T(15.3, 0.0)])
        cv.shape(col_, GOLD, z=2.6, sd=1.1, hi=0.5, ol=0.9,
                 details=[('ink', [T(u_, -3.8), T(u_ + 0.2, 0.0), T(u_ - 0.2, 3.6)], 0.7, (0.05, 0.05)) for u_ in (15.4, 16.6)])
        # kemer: altın plakalı
        belt = cv.blob([T(-0.6, -5.8), T(2.2, -6.0), T(2.4, 6.2), T(-0.8, 6.1)])
        bdet = [('col', cv.blob([T(0.0, v - 0.9), T(1.9, v - 0.9), T(1.9, v + 0.9), T(0.0, v + 0.9)]), GOLD.base) for v in (-3.4, 0.0, 3.4)]
        bdet += [('stroke', [T(1.5, v - 0.6), T(1.5, v + 0.5)], 0.8, GOLD.hi, (0.2, 0.2)) for v in (-3.4, 0.0, 3.4)]
        cv.shape(belt, UNDER, z=3.0, sd=0.9, hi=0.3, details=bdet, cast=0.5)
        # lamel etek: ön ve yan parçalar, kemerden diz üstüne
        kf = J['kf']
        hip = J['hip']
        lift = max(0.0, (kf[0] - hip[0]) - 3.0) * 0.12
        for (v0, v1, zz, m, ex) in ((-6.0, -0.6, 3.2, PLATE_B, 0.0), (0.4, 6.2, 3.4, PLATE, lift)):
            dv = p['sk'] * 0.6 + ex * 4.0
            a0, a1 = T(0.2, v0), T(0.2, v1)
            b1, b0 = T(-8.0 + ex * 2, v1 + 0.6 + dv), T(-8.0 + ex * 2, v0 - 0.4 + dv)
            tas = cv.blob([(a0[0], a0[1], 0.0), (a1[0], a1[1], 0.0), (b1[0], b1[1], 0.0), (b0[0], b0[1], 0.0)])
            tdt = []
            for u in (-2.4, -5.0):
                tdt.append(('ink', [T(u, v0 - 0.3 + dv * (-u / 8)), T(u, v1 + 0.5 + dv * (-u / 8))], 1.0, (0.02, 0.02)))
            vv = v0 + 1.3
            while vv < v1 + 0.2:
                tdt.append(('ink', [T(0.0, vv), T(-7.8, vv + 0.4 + dv)], 0.75, (0.05, 0.3)))
                vv += 1.6
            cv.shape(tas, m, z=zz, sd=1.3, hi=0.35 if m is PLATE else 0.0, details=tdt, cast=0.4)
            cv.stroke([b0, b1], 1.0, z=zz + 0.05, col=(0.55, 1.0, 0.92), taper=(0.2, 0.2), glow=(GLOW[0] * 0.6, GLOW[1] * 0.6, GLOW[2] * 0.6))

    # ---- baş: sivri Saka börkü, yüzsüz oyuk, turkuaz gözler
    def head(self, cv, p, J, hc):
        hx, hy = hc
        ph = p['ph']
        fl = p['flare']
        hurt = p['hurt']
        # ensel (arkaya sarkan keçe + altın pullar)
        nk = cv.blob([(hx - 4.2, hy - 2.0), (hx - 6.0, hy + 2.5), (hx - 6.6, hy + 6.8, 0.0), (hx - 2.6, hy + 6.0), (hx - 0.6, hy + 3.0), (hx - 1.0, hy - 1.0)])
        cv.shape(nk, FELT.darker(0.85), z=7.0, sd=1.2, hi=0.2,
                 details=[('col', cv.ellipse((hx - 4.4 + k * 0.9, hy + 1.6 + k * 1.4), 0.5, 0.5), GOLD.base) for k in range(3)])
        # yüz oyuğu
        face = cv.blob([(hx - 1.8, hy - 2.6), (hx + 3.2, hy - 3.0), (hx + 4.6, hy - 0.6), (hx + 4.2, hy + 2.6), (hx + 2.0, hy + 4.4, 0.0),
                        (hx - 0.6, hy + 3.4), (hx - 2.0, hy + 0.6)])
        cv.fill(face, VOID, z=8.0)
        yk.glow_soft(cv, (hx + 2.0, hy + 0.2), 4.2, GLOW_D, z=8.05, blur=0.6, alpha=0.5)
        # gözler: yakın göz (önde) büyük, uzak göz küçük; telegrafta alevlenir, arkaya iz bırakır
        er = 0.55 + 0.45 * fl
        ey = 0.4 if hurt > 0.5 else 1.0
        for (ex_, ey_, s) in ((hx + 3.0, hy - 0.4, 1.0), (hx + 0.7, hy - 0.5, 0.7)):
            yk.eye_glow(cv, (ex_, ey_), er * 1.05 * s, er * 0.8 * s * ey, -0.1, EYE, GLOW, 8.2, halo=2.6, halo_a=0.35 + 0.35 * fl)
        if fl > 0.3:
            cv.stroke([(hx + 3.0, hy - 0.4), (hx + 0.2, hy - 1.2 - fl * 0.4), (hx - 3.5 - fl * 3.0, hy - 1.6 - fl * 1.0)], 1.2 + 1.4 * fl,
                      z=8.15, col=EYE, taper=(0.1, 0.95), glow=GLOW, alpha=0.9)
        # yanak siperi (altın kenarlı keçe), çeneye iner
        ch = cv.blob([(hx - 3.6, hy - 2.2), (hx - 0.6, hy - 2.4), (hx - 0.2, hy + 2.0), (hx - 1.0, hy + 5.4, 0.0), (hx - 3.4, hy + 3.6)])
        cv.shape(ch, FELT, z=9.0, sd=1.0, hi=0.3, details=[('stroke', [(hx - 0.5, hy - 2.0), (hx - 0.2, hy + 2.0), (hx - 0.9, hy + 5.0)], 1.1, GOLD.base, (0.1, 0.4))])
        # sivri börk: geriye hafif kıvrık uzun koni
        tipx, tipy = hx - 4.2, hy - 17.5
        helm = cv.blob([(hx - 4.8, hy - 1.8), (hx - 5.0, hy - 6.0), (hx - 4.4, hy - 11.0), (tipx + 0.4, tipy + 2.0), (tipx, tipy, 0.0),
                        (tipx + 1.6, tipy + 2.2), (hx + 0.6, hy - 9.0), (hx + 4.4, hy - 4.6), (hx + 5.4, hy - 2.2, 0.4)])
        hdet = [('ink', [(hx - 1.6, hy - 2.6), (hx - 2.6, hy - 9.0), (tipx + 0.6, tipy + 1.5)], 1.0, (0.05, 0.7)),
                ('shade', cv.wedge([(hx - 4.6, hy - 2.0), (hx - 4.8, hy - 8.0), (tipx + 0.3, tipy + 2.0)], 1.2, -1.0))]
        cv.shape(helm, FELT, z=9.5, sd=2.0, hi=0.5, details=hdet, cast=0.6)
        # altın levhalar: yukarı bakan ok uçları + kuş, tepede topuz
        for k, (u, s) in enumerate(((0.25, 1.0), (0.48, 0.85), (0.68, 0.7))):
            c = lerp2((hx + 1.2, hy - 3.6), (tipx + 0.8, tipy + 1.6), u)
            pl = cv.blob([(c[0] - 1.2 * s, c[1] + 1.4 * s), (c[0] - 0.2 * s, c[1] - 1.8 * s, 0.0), (c[0] + 1.0 * s, c[1] + 1.4 * s), (c[0] - 0.1 * s, c[1] + 0.6 * s)])
            cv.shape(pl, GOLD, z=9.7 + k * 0.01, sd=0.4, hi=0.3, ol=0.7, glow=(0.05, 0.04, 0.0))
        for k in range(3):
            c = lerp2((hx - 3.4, hy - 4.0), (tipx + 0.2, tipy + 3.2), 0.2 + k * 0.28)
            cv.shape(cv.ellipse(c, 0.65, 0.65), GOLD, z=9.7, sd=0.2, ol=0.6)
        cv.shape(cv.ellipse((tipx + 0.1, tipy - 0.4), 1.0, 1.0), GOLD, z=9.8, sd=0.4, hi=0.3, ol=0.8)
        # alın bandı: altın, perçinli
        band = cv.blob([(hx - 5.2, hy - 3.6), (hx + 5.4, hy - 3.6), (hx + 5.6, hy - 1.6, 0.0), (hx - 5.0, hy - 1.4, 0.0)])
        cv.shape(band, GOLD, z=9.9, sd=0.8, hi=0.45, ol=0.9,
                 details=[('col', cv.ellipse((hx + x, hy - 2.5), 0.45, 0.45), GOLD.deep) for x in (-3.6, -1.2, 1.2, 3.6)])
        # börkün kenarı soluk ışır
        yk.glow_soft(cv, (hx - 1.0, hy - 8.0), 6.0, GLOW, z=9.95, blur=0.7, alpha=0.15)

    # ---- kol: keçe yen + lamel omuzluk + altın bilezik + ruh eli
    def arm(self, cv, sh, e, h, near, z_up, z_lo, grip=True, d=(1.0, 0.0)):
        m = UNDER if near else UNDER_B
        up = cv.limb([sh, lerp2(sh, e, 0.5), e], [2.9, 2.7, 2.3])
        cv.shape(up, m, z=z_up, sd=1.6, details=cv.fold([lerp2(sh, e, 0.3), lerp2(sh, e, 0.85)], 0.6, 1.0, 1) if near else ())
        fo = cv.limb([e, lerp2(e, h, 0.5), lerp2(e, h, 0.86)], [2.2, 2.1, 1.7])
        cv.shape(fo, m, z=z_lo, sd=1.3)
        br = cv.capsule(lerp2(e, h, 0.38), lerp2(e, h, 0.82), 2.0, 1.85)
        cv.shape(br, GOLD if near else GOLD_B, z=z_lo + 0.1, sd=1.0, hi=0.45 if near else 0.0, ol=0.85,
                 details=[('ink', [along(e, h, t, -1.8), along(e, h, t, 1.8)], 0.8, (0.1, 0.1)) for t in (0.5, 0.62, 0.74)])
        # ruh eli: kavrayan yumruk (parmak boğumları sap boyunca)
        hm = SPIRIT if near else SPIRIT_B
        ang = math.atan2(d[1], d[0])
        fist = cv.ellipse(h, 1.9, 1.5, ang + (math.pi / 2 if grip else 0.0))
        fdet = [('ink', [add(h, d, k * 0.9 - 0.9), add(add(h, d, k * 0.9 - 0.9), (-d[1], d[0]), 1.4)], 0.7, (0.1, 0.5)) for k in range(3)] if grip else ()
        cv.shape(fist, hm, z=z_lo + 0.3 if not (near and grip) else z_lo + 2.0, sd=0.6, hi=0.3, ol=0.85, details=fdet, glow=(0.03, 0.12, 0.12))
        if near:   # lamel omuzluk
            pts = [along(sh, e, -0.35, -2.6), along(sh, e, -0.3, 2.0), along(sh, e, 0.05, 4.0), along(sh, e, 0.5, 3.6),
                   along(sh, e, 0.6, 1.0), along(sh, e, 0.5, -2.4), along(sh, e, 0.2, -3.6)]
            pdet = []
            for t in (-0.1, 0.1, 0.3):
                pdet.append(('ink', [along(sh, e, t - 0.02, -3.4), along(sh, e, t + 0.05, 0.4), along(sh, e, t, 3.7)], 1.0, (0.12, 0.12)))
            cv.shape(cv.blob(pts), PLATE, z=z_up + 0.6, sd=1.4, hi=0.55, details=pdet, cast=0.5)
            cv.stroke([along(sh, e, 0.48, -2.2), along(sh, e, 0.56, 1.0), along(sh, e, 0.48, 3.4)], 0.9, z=z_up + 0.7,
                      col=(0.55, 1.0, 0.92), taper=(0.2, 0.2), glow=(GLOW[0] * 0.6, GLOW[1] * 0.6, GLOW[2] * 0.6))

    # ---- kargı: sap, altın halkalar, yaprak temren, at kılı tuğ, çatal flama
    def weapon(self, cv, p, J, butt, tip, z):
        ph = p['ph']
        d = J['d']
        n = (-d[1], d[0])
        L = mk.dist(butt, tip)
        bl = 9.0
        bb = add(tip, d, -bl)          # temren dibi
        cv.shape(cv.capsule(butt, bb, 0.7, 0.62), WOOD, z=z, sd=0.5, hi=0.25, ol=0.85,
                 details=[('ink', [add(butt, d, s), add(butt, d, s + 1.2)], 0.7) for s in (8.0, 20.0, 33.0)])
        for s in (0.6, L * 0.32, L * 0.58):     # altın halkalar
            q = add(butt, d, s)
            cv.shape(cv.capsule(add(q, d, -0.6), add(q, d, 0.6), 0.95, 0.95), GOLD, z=z + 0.05, sd=0.3, hi=0.3, ol=0.7)
        # dipçik demiri
        cv.shape(cv.blob([add(butt, n, 0.8), add(add(butt, d, -2.4), n, 0.0) + (0.0,), add(butt, n, -0.8)]), GOLD, z=z + 0.04, sd=0.3, ol=0.7)
        # tuğ: temren dibinde at kılı (hareketin ve yerçekiminin tersine akar)
        flow = math.atan2(0.6, -1.0) - p['cw'] * 0.15
        for k in range(5):
            a = flow + (k - 2) * 0.16 + math.sin(ph * 1.3 + k) * 0.08
            st = add(add(bb, d, -1.6), n, (k - 2) * 0.35)
            pts = [st]
            x, y = st
            for j in range(4):
                aa = a + j * 0.18 + math.sin(ph + j + k) * 0.1
                x += math.cos(aa) * 2.6
                y += math.sin(aa) * 2.6 + 0.5 * j
                pts.append((x, y))
            cv.shape(ik.taper_path([cv.W(q) for q in pts], cv.u(2.0 if k % 2 else 2.6), (0.15, 0.9)), HAIR if k % 2 == 0 else HAIR.darker(0.85),
                     z=z - 0.2 + k * 0.01, sd=0.15, hi=0.3, ol=0.45, glow=(0.03, 0.1, 0.1))
        cv.shape(cv.capsule(add(bb, d, -2.6), add(bb, d, 0.2), 1.25, 1.0), GOLD, z=z + 0.1, sd=0.5, hi=0.4, ol=0.8)
        # flama: tuğun arkasında küçük çatal bayrak
        fa = add(butt, d, L * 0.76)
        fb_ = add(fa, d, -4.0)
        wv = math.sin(ph * 1.7) * 1.0
        fl_back = (-1.0 - 0.3 * p['cw'], 0.25)
        tipf = (fa[0] + fl_back[0] * 9.0, fa[1] + fl_back[1] * 9.0 + 1.5 + wv)
        flag = cv.blob([fa, (tipf[0] + 0.5, tipf[1] - 0.8, 0.0), lerp2(tipf, fb_, 0.4), (tipf[0] - 0.4, tipf[1] + 2.4 + wv * 0.4, 0.0), fb_])
        cv.shape(flag, CLOAK, z=z - 0.3, sd=0.8, hi=0.3, ol=0.75,
                 details=[('stroke', [lerp2(fa, fb_, 0.5), lerp2(fa, tipf, 0.6)], 0.9, GOLD.base, (0.1, 0.5))])
        # temren: soluk altın yaprak, kenarları turkuaz ışır
        mid = add(bb, d, bl * 0.42)
        blade = cv.blob([(bb[0], bb[1]), add(mid, n, 1.7), (tip[0], tip[1], 0.0), add(mid, n, -1.7)])
        cv.shape(blade, GOLD, z=z + 0.2, sd=0.6, hi=0.5, ol=0.85, glow=(0.06, 0.2, 0.18),
                 details=[('ink', [add(bb, d, 1.0), add(tip, d, -1.5)], 0.8, (0.1, 0.6))])
        cv.stroke([add(mid, n, 1.5), add(tip, d, -0.4)], 0.8, z=z + 0.25, col=EYE, taper=(0.2, 0.8), glow=GLOW)
        yk.glow_soft(cv, add(tip, d, -3.0), 3.2 + 2.0 * p['flare'], GLOW, z=z + 0.3, alpha=0.35 + 0.3 * p['flare'])

    # ---- ışıktan cirit: turkuaz çekirdek, ak sıcak öz, belirirken kıvılcımlar toplanır; uçarken iz
    def javelin(self, cv, base, ang, k, L, ph, flying=False, trail=0.0):
        d = dirv(ang)
        n = (-d[1], d[0])
        Lk = L * (0.45 + 0.55 * min(1.0, k))
        tip = add(base, d, Lk)
        a = min(1.0, k * 1.3)
        if flying and trail > 0:
            for j in range(3):
                st = add(add(base, d, 2.0), n, (j - 1) * 1.1)
                cv.stroke([st, add(st, d, -14.0 * trail - j * 3.0)], 2.2 - j * 0.5, z=29.0, col=(0.55, 1.0, 0.92), taper=(0.05, 0.95),
                          glow=GLOW, alpha=0.75)
            yk.wisp(cv, add(base, d, 1.0), ang + math.pi, 16.0 * trail, 2.4, MIST, 28.8, ph=ph * 2, curl=0.5, alpha=0.5, glow=GLOW_D, glow_a=0.5)
        shaft = ik.taper_path([cv.W(add(base, d, -1.5)), cv.W(add(base, d, Lk * 0.5)), cv.W(add(tip, d, -4.0))], cv.u(1.4), (0.5, 0.1))
        cv.fill(shaft, (0.45, 0.95, 0.9), z=30.0, glow=GLOW, alpha=0.85 * a)
        hd_ = cv.blob([add(add(tip, d, -4.5), n, 1.5), (tip[0], tip[1], 0.0), add(add(tip, d, -4.5), n, -1.5), add(tip, d, -3.2)])
        cv.fill(hd_, (0.7, 1.0, 0.96), z=30.1, glow=GLOW, alpha=a)
        cv.stroke([add(base, d, 1.0), add(tip, d, -0.8)], 0.8, z=30.2, col=(1.0, 1.0, 1.0), taper=(0.6, 0.3), glow=(0.7, 1.0, 1.0), alpha=a)
        yk.glow_soft(cv, add(base, d, Lk * 0.6), Lk * 0.45, GLOW, z=29.9, blur=0.7, alpha=0.45 * a, ry=Lk * 0.25)
        if k < 0.95 and not flying:
            yk.sparks(cv, add(base, d, Lk * 0.5), 7, 2.0, 6.0 + 4.0 * (1 - k), (0.7, 1.0, 0.96), 30.3, seed=int(ph * 11) % 40 + 1, w=0.9, glow=GLOW)
        return tip

    # ---- hilal savuruş izi
    def smear(self, cv, c, r, a0, a1, k):
        mk.smear_arc(cv, c, r * 0.86, a0, a1, 9.0 * k, (0.42, 0.95, 0.9), GLOW, 11.0, alpha=0.55 * k, hot=(0.9, 1.0, 1.0))


S = Style()


# ------------------------------------------------------------ döngüler
def _idle(t):
    p = mk.idle_pose(t, mk.REST)
    s = math.sin(t * math.tau)
    c = math.cos(t * math.tau)
    p.update(bob=-1.2 * s, fb=(-5.0 + 0.6 * c, 1.0), ff=(4.0 - 0.6 * c, 1.2), cw=0.25 + 0.2 * c, sk=0.5 * s)
    return p


def _move(t):
    s = math.sin(t * math.tau)
    c = math.cos(t * math.tau)
    p = dict(mk.REST)
    p.update(mk.G)
    p.update(bob=-1.0 * s, lean=0.3 + 0.02 * c, hx=1.5, hy=0.5, fb=(-11.0 + 1.0 * c, 4.5), ff=(-2.0 - 1.0 * c, 3.0),
             gh=(8.0, -8.5 + 0.4 * s), la=-0.32 + 0.03 * s, tw=0.1, hd=(1.0, 0.6), flare=0.4, cw=1.0 + 0.2 * c, sk=-0.8 + 0.3 * s,
             streak=0.35)
    return p


def _tweak(keys):
    return keys


ROWS = None


def anims_for(var='tunga_hayaleti'):
    global ROWS
    if ROWS is None:
        ROWS = mk.rows(mk.REST, idle=_idle, move=_move, tweak=_tweak)
    return ROWS


def durum_for(var='tunga_hayaleti'):
    return mk.durum(('lunge', 'sweep', 'throw'))


SHADE = dict(outer=0.5, rim=0.65, rim_col=(0.6, 0.95, 1.0), rim_dir=(0.6, -0.8), rim_w=1.4, form=(6.0, (0.74, 0.8, 0.9)))


def render_frame(anim, i, var='tunga_hayaleti', ss=3):
    r = anims_for(var)[anim]
    tt = mk.frame_time(r, i)
    p = dict(r['pose'](tt))
    p['ph'] = tt * math.tau * (1 if r['loop'] else 0.7) + (0 if r['loop'] else i * 0.6)
    cv = u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss)
    info = mk.draw(cv, p, S)
    rgba, nm, em = cv.finish(**SHADE)
    rgba, em = u29.fade(rgba, em, 0.93)    # hayalet: hafif saydam
    return rgba, None, em, {'hand': info['hand'], 'head': info['head']}
