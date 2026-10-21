"""v39: Kar Cadısı (kimlik kar_cadisi) — Kaf'ın kar cadısı; yapay zekâ "blinker": ışınlanıp arkadan bıçaklar.

Uzun boylu, sıska, kambur bir kocakarı: ayazdan morarmış mavi-beyaz ten, çökük yanaklı sivri yüz, oyuk göz
çukurlarında buz-camgöbeği ışık; rüzgârda yana savrulan çok uzun ak saç (büyük silüet), başında buz sarkıtlarından
taç; omuzlarında kuyruk uçları kara ak kakım / kar tilkisi postu, altında yırtık çivit elbise (eteği yere dek, ayaklar
görünmez, süzülür). Uzun ince kollar, uzun donmuş kara-mavi tırnaklar; ön elde kıvrık, soluk ışıyan buz hançeri.

Satırlar (hücre 320x256 px = dünya 80x64, ayak (37, 60), doku 4; gövde 18 x 44):
  idle 8 (kambur, saç dalgalanır, parmaklar seğirir), move 8 (süzülen sinsi yürüyüş, vx 80), hurt 3,
  atk_stab 10 (mk [0,3, 0,34, 0,8]: kurulma -> hançer / pençe / hançer üç hızlı kesik, buz-mavisi hilal izleri),
  atk_shards 8 (mk: eller havada buz kristalleri büyür -> yelpaze gibi ileri savrulur), blink 6 (kar girdabına
  çözülür; kaybolma ve belirme aynı satır).
'hand' çapası = ön avuç (hançer / buz kıymığı çıkışı); atk_shards hazırlığında kristal kümesinin ortası.
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
CELL = (320, 256)       # dünya 80 x 64 (rüzgârda savrulan saç için arkada geniş pay)
FEET = (148, 240)       # dünya (37, 60)

SKIN = Ink('#c6d8ea', '#6a80b0', '#f2faff', '#34406e', name='ayaz ten')
SKIN_B = SKIN.darker(0.74)
HAIR = Ink('#eef3fa', '#8c9ec6', '#ffffff', '#46527c', name='ak saç')
HAIR_B = Ink('#b8c4d8', '#66749a', '#dce6f2', '#353e60', name='ak saç (arka)')
FUR = Ink('#dedfe6', '#8e90a8', '#ffffff', '#52546e', kind='fur', name='kakım postu')
TIP = Ink('#1c1a22', '#0a090e', '#4a4656', name='kuyruk ucu')
DRESS = Ink('#3c3c86', '#1c1a48', '#5c5cb0', '#0e0c28', name='çivit elbise')
DRESS_B = Ink('#26265a', '#121030', '#3a3a7a', '#08061a', name='elbise arkası')
CLAW = Ink('#1e2a4c', '#0a0e20', '#6684c4', '#04060e', name='donmuş tırnak')
ICE = Ink('#a6e8ff', '#4a8ec4', '#eaffff', '#24588a', name='buz')
ICE_G = (0.05, 0.32, 0.5)
EYE = (0.8, 1.0, 1.0)
EYE_GLOW = (0.2, 0.85, 1.0)
GLOW = (0.25, 0.75, 1.0)
HOT = (0.85, 0.98, 1.0)
SNOW = Ink('#f2f6fc', '#9aaac8', '#ffffff', name='kar')

UA, FA = 9.6, 9.6        # üst kol / ön kol


# ------------------------------------------------------------------ parçalar
def _hair(cv, hd, p, ph, back):
    """Rüzgârda yana (geriye, -x) savrulan uzun ak saç. back=True: başın arkasındaki büyük kütle."""
    wind = p['wind']
    hup = p['hup']
    n = 13 if back else 4
    for i in range(n):
        u = i / max(1, n - 1)
        if back:
            root = (hd[0] - 2.6 + u * 1.6, hd[1] - 3.6 + u * 5.2)
            a0 = math.pi + 0.42 - u * 0.95 + hup * (0.45 - 0.2 * u) - (wind - 1.0) * 0.25 * (u - 0.5)
            L = (17.0 + 9.0 * math.sin(math.pi * u) + (i % 3) * 1.6) * (0.85 + 0.2 * wind)
            w = 3.5 - 0.8 * (i % 2)
        else:   # öne düşen tutamlar da rüzgârla geriye gider
            root = (hd[0] + 0.5 - u * 1.8, hd[1] - 4.2 + u * 0.6)
            a0 = math.pi + 0.25 - u * 0.5 + hup * 0.3
            L = 9.0 + 3.0 * u
            w = 1.9
        segs = 8
        pts = [root]
        x, y = root
        for j in range(segs):
            v = (j + 1) / segs
            a = a0 + math.sin(ph * 1.0 + j * 0.85 + i * 1.3) * (0.18 + 0.1 * wind) * v + 0.12 * v * (1 if i % 2 else -1)
            x += math.cos(a) * L / segs
            y += math.sin(a) * L / segs
            pts.append((x, y))
        prof = lambda q: max(0.12, max(0.0, 1.0 - q) ** 0.75 * min(1.0, q * 6 + 0.55))
        m = HAIR_B if (back and i % 3 == 1) else HAIR
        det = [('stroke', [pts[2], pts[4], pts[6]], 0.8, m.hi, (0.3, 0.7))] if i % 2 == 0 else [('ink', [pts[3], pts[5], pts[7]], 0.6, (0.3, 0.7))]
        cv.shape(ik.taper_path([cv.W(q) for q in pts], cv.u(w), prof=prof), m, z=(-24 + i * 0.05) if back else (23 + i * 0.05),
                 sd=0.7, hi=0.0, ol=0.85, details=det)


def _crown(cv, hd, p):
    """Buz sarkıtı taç: alnın üstünde kara-çivit bant, ışıyan sarkıtlar yukarı / geriye."""
    band = cv.capsule((hd[0] - 2.8, hd[1] - 3.4), (hd[0] + 3.2, hd[1] - 4.0), 0.75, 0.75)
    cv.shape(band, DRESS_B, z=21.5, sd=0.3, ol=0.8)
    for k, (bx, a, L) in enumerate(((-2.4, -2.45, 4.6), (-1.0, -2.1, 7.4), (0.6, -1.75, 9.0), (2.0, -1.45, 6.8), (3.0, -1.15, 4.4))):
        b = (hd[0] + bx, hd[1] - 3.8 - 0.2 * (bx > 0))
        L = L * (1.0 + 0.12 * p['flare'])
        tip = (b[0] + math.cos(a) * L, b[1] + math.sin(a) * L)
        nx, ny = -math.sin(a) * 0.95, math.cos(a) * 0.95
        m_ = lerp2(b, tip, 0.35)
        cv.shape(cv.blob([(b[0] + nx, b[1] + ny, 0.0), (m_[0] + nx * 0.8, m_[1] + ny * 0.8), (tip[0], tip[1], 0.0), (m_[0] - nx * 0.8, m_[1] - ny * 0.8),
                          (b[0] - nx, b[1] - ny, 0.0)]), ICE, z=21 + k * 0.01, sd=0.5, hi=0.35, ol=0.8, glow=ICE_G,
                 details=[('stroke', [lerp2(b, tip, 0.15), lerp2(b, tip, 0.75)], 0.6, (1, 1, 1), (0.2, 0.7))])
    yk.glow_soft(cv, (hd[0] + 0.4, hd[1] - 9.0), 4.0, GLOW, z=21.2, alpha=0.22 + 0.25 * p['flare'])


def _head(cv, hd, p):
    hx, hy = hd
    pain = p['pain']
    skull = cv.blob([(hx - 3.6, hy - 0.8), (hx - 2.8, hy - 4.0), (hx + 0.8, hy - 5.0), (hx + 3.6, hy - 3.8), (hx + 4.4, hy - 1.6),
                     (hx + 6.4, hy + 1.2, 0.0), (hx + 4.6, hy + 1.8), (hx + 4.4, hy + 2.9), (hx + 3.6, hy + 3.4), (hx + 3.9, hy + 5.0, 0.0),
                     (hx + 1.4, hy + 4.7), (hx - 1.2, hy + 2.8)])
    det = [('deep', cv.blob([(hx + 1.2, hy - 2.2), (hx + 4.0, hy - 2.0), (hx + 3.8, hy + 0.3), (hx + 1.4, hy + 0.4)])),        # oyuk göz çukuru
           ('deep', cv.blob([(hx + 0.6, hy + 1.2), (hx + 3.0, hy + 1.6), (hx + 3.4, hy + 3.4), (hx + 1.2, hy + 3.2)])),        # çökük yanak
           ('ink', [(hx + 0.4, hy + 1.0), (hx + 2.0, hy + 1.5), (hx + 3.6, hy + 1.6)], 0.9, (0.2, 0.6)),
           ('ink', [(hx + 4.4, hy - 1.4), (hx + 5.6, hy + 0.6), (hx + 4.7, hy + 1.6)], 0.8, (0.2, 0.5)),                           # burun
           ('ink', [(hx - 0.2, hy + 3.0), (hx + 1.6, hy + 3.9), (hx + 3.2, hy + 4.6)], 0.7, (0.3, 0.5))]                          # çene kemiği
    if pain > 0.3:   # acı: ağız açılır
        det.append(('col', cv.blob([(hx + 2.6, hy + 2.6), (hx + 4.3, hy + 2.6), (hx + 4.0, hy + 2.6 + 1.6 * pain), (hx + 2.8, hy + 2.6 + 1.3 * pain)]), (0.12, 0.08, 0.2)))
    else:
        det.append(('ink', [(hx + 2.4, hy + 2.9), (hx + 3.4, hy + 2.6), (hx + 4.4, hy + 2.8)], 0.8, (0.2, 0.3)))
    cv.shape(skull, SKIN, z=14, sd=1.1, hi=0.35, details=det, bounce=0.3)
    # göz: kara oyuk + buz ışığı (flare ile büyür, geriye iz bırakır)
    q = (hx + 2.7, hy - 0.9)
    fl = p['flare']
    cv.fill(cv.ellipse(q, 1.25, 0.95, -0.15), INK, z=15)
    rr = 0.5 + 0.28 * fl
    yk.eye_glow(cv, q, rr * (1.0 - 0.4 * pain), rr * 0.8 * (1.0 - 0.5 * pain), -0.15, EYE, EYE_GLOW, 16, halo=2.4 + fl, halo_a=0.35 + 0.35 * fl)
    if fl > 0.5:
        cv.stroke([(q[0] - 0.2, q[1]), (q[0] - 2.5 - 3.0 * fl, q[1] - 0.6 - 0.8 * fl)], 0.6 + 0.6 * fl, z=16.1, col=EYE, taper=(0.1, 0.9), glow=EYE_GLOW)
    # kaş: çatık kara çizgi
    cv.stroke([(hx + 1.2, hy - 2.4 + 0.3 * pain), (hx + 2.8, hy - 2.0), (hx + 4.0, hy - 2.6 - 0.4 * fl)], 0.9, z=16.2, col=INK, taper=(0.2, 0.6))
    # saç kapağı: başın üstünü / arkasını örter
    cap = cv.blob([(hx - 4.0, hy + 1.6), (hx - 3.8, hy - 3.4), (hx - 0.6, hy - 5.6), (hx + 2.8, hy - 5.2), (hx + 4.2, hy - 3.4, 0.0),
                   (hx + 1.6, hy - 3.6), (hx - 0.4, hy - 2.4), (hx - 1.2, hy + 0.6), (hx - 1.8, hy + 3.4, 0.0)])
    cv.shape(cap, HAIR, z=20, sd=0.8, hi=0.3, ol=0.9, details=[('ink', [(hx - 2.6, hy - 3.0), (hx - 2.0, hy - 0.4), (hx - 2.6, hy + 2.0)], 0.7, (0.3, 0.6)),
                                                             ('stroke', [(hx - 1.4, hy - 4.6), (hx + 1.6, hy - 4.6)], 0.8, HAIR.hi, (0.3, 0.6))])


def _claw_hand(cv, h, ang, curl, spread, z, near, ph, twitch=0.0):
    """Uzun avuç + dört boğumlu parmak + uzun kara-mavi donmuş tırnaklar."""
    m = SKIN if near else SKIN_B
    cm = CLAW if near else CLAW.darker(0.8)
    pc = (h[0] + math.cos(ang) * 1.3, h[1] + math.sin(ang) * 1.3)
    cv.shape(cv.ellipse(pc, 1.8, 1.15, ang), m, z=z, sd=0.5, hi=0.2 if near else 0.0, ol=0.85)
    tips = []
    for k in range(4):
        c_ = curl + (math.sin(ph * 3 + k * 1.7) * 0.25 * twitch)
        fa = ang + (k - 1.5) * (0.2 + 0.28 * spread)
        m1 = (pc[0] + math.cos(fa) * 2.6, pc[1] + math.sin(fa) * 2.6)
        fb = fa + c_ * 0.75
        m2 = (m1[0] + math.cos(fb) * 2.0, m1[1] + math.sin(fb) * 2.0)
        fc = fb + c_ * 0.55
        L = 4.6 - abs(k - 1.5) * 0.5
        tip = (m2[0] + math.cos(fc + 0.25 * c_) * L, m2[1] + math.sin(fc + 0.25 * c_) * L)
        mid = (m2[0] + math.cos(fc) * L * 0.55, m2[1] + math.sin(fc) * L * 0.55)
        nx, ny = -math.sin(fc), math.cos(fc)
        cv.shape(cv.limb([pc, m1, m2], [0.62, 0.5, 0.45]), m, z=z + 0.1 + k * 0.01, sd=0.3, ol=0.75)
        cv.shape(cv.blob([(m2[0] + nx * 0.55, m2[1] + ny * 0.55), (mid[0] + nx * 0.42, mid[1] + ny * 0.42), (tip[0], tip[1], 0.0),
                          (mid[0] - nx * 0.25, mid[1] - ny * 0.25), (m2[0] - nx * 0.5, m2[1] - ny * 0.5)]), cm, z=z + 0.2 + k * 0.01, sd=0.3, hi=0.2, ol=0.8,
                 details=[('stroke', [lerp2(m2, mid, 0.3), lerp2(mid, tip, 0.5)], 0.5, cm.hi, (0.2, 0.7))])
        tips.append(tip)
    # başparmak
    ta = ang - 1.1
    t1 = (pc[0] + math.cos(ta) * 1.8, pc[1] + math.sin(ta) * 1.8)
    t2 = (t1[0] + math.cos(ta + 0.5) * 2.4, t1[1] + math.sin(ta + 0.5) * 2.4)
    cv.shape(cv.limb([pc, t1], [0.6, 0.5]), m, z=z + 0.05, sd=0.3, ol=0.75)
    cv.shape(cv.blob([(t1[0] - 0.4, t1[1]), (t2[0], t2[1], 0.0), (t1[0] + 0.4, t1[1] + 0.3)]), cm, z=z + 0.06, sd=0.2, ol=0.7)
    return pc, tips


def _dagger_hand(cv, h, ang, dg, z, p):
    """Ön el: buz hançerini kavrar. Kıvrık bıçak avuçtan dg açısıyla çıkar, soluk camgöbeği ışır."""
    pc = (h[0] + math.cos(ang) * 1.2, h[1] + math.sin(ang) * 1.2)
    da = ang + dg
    d = (math.cos(da), math.sin(da))
    n = (-d[1], d[0])
    # kabza (yumruğun iki yanından çıkar)
    hb = (pc[0] - d[0] * 2.4, pc[1] - d[1] * 2.4)
    cv.shape(cv.capsule(hb, (pc[0] + d[0] * 1.4, pc[1] + d[1] * 1.4), 0.6, 0.6), DRESS_B, z=z - 0.2, sd=0.2, ol=0.7)
    cv.shape(cv.ellipse(hb, 0.75, 0.75), ICE, z=z - 0.15, sd=0.2, ol=0.7, glow=ICE_G)
    # bıçak: kıvrık hilal (sırtı n yanında şişer)
    b = (pc[0] + d[0] * 1.4, pc[1] + d[1] * 1.4)
    L = 9.5
    tip = (b[0] + d[0] * L - n[0] * 2.2, b[1] + d[1] * L - n[1] * 2.2)
    m1 = (b[0] + d[0] * L * 0.45, b[1] + d[1] * L * 0.45)
    blade = cv.blob([(b[0] - n[0] * 0.8, b[1] - n[1] * 0.8), (m1[0] - n[0] * 1.1, m1[1] - n[1] * 1.1), (tip[0], tip[1], 0.0),
                     (m1[0] + n[0] * 0.9 + d[0] * 1.2, m1[1] + n[1] * 0.9 + d[1] * 1.2), (b[0] + n[0] * 1.0, b[1] + n[1] * 1.0)])
    cv.shape(blade, ICE, z=z - 0.1, sd=0.5, hi=0.4, ol=0.85, glow=ICE_G,
             details=[('stroke', [lerp2(b, m1, 0.2), m1, lerp2(m1, tip, 0.6)], 0.7, (1, 1, 1), (0.2, 0.8)),
                      ('ink', [(m1[0] + n[0] * 0.3, m1[1] + n[1] * 0.3), lerp2(m1, tip, 0.5)], 0.5, (0.3, 0.6))])
    yk.glow_soft(cv, lerp2(b, tip, 0.5), 3.4 + 1.5 * p['flare'], GLOW, z=z, alpha=0.35 + 0.2 * p['flare'])
    # yumruk: kıvrık parmak boğumları kabzanın üstünde
    m = SKIN
    cv.shape(cv.ellipse(pc, 1.7, 1.3, ang), m, z=z, sd=0.5, hi=0.2, ol=0.85)
    for k in range(3):
        q = (pc[0] + d[0] * (0.9 - k * 0.9) + n[0] * 1.2, pc[1] + d[1] * (0.9 - k * 0.9) + n[1] * 1.2)
        cv.shape(cv.ellipse(q, 0.7, 0.6), m, z=z + 0.1 + k * 0.01, sd=0.2, ol=0.7)
        t = (q[0] + n[0] * 0.9 - d[0] * 0.4, q[1] + n[1] * 0.9 - d[1] * 0.4)
        cv.shape(cv.blob([(q[0] - d[0] * 0.3, q[1] - d[1] * 0.3), (t[0], t[1], 0.0), (q[0] + d[0] * 0.3, q[1] + d[1] * 0.3)]), CLAW, z=z + 0.15 + k * 0.01, sd=0.2, ol=0.6)
    return pc, tip


def _arm(cv, sp, tgt, wrist, z, near, ph, p, kind):
    e, h = yg.ik2(sp, tgt, UA, FA, 1)
    m = SKIN if near else SKIN_B
    arm = ik.union(cv.limb([sp, lerp2(sp, e, 0.5), e], [1.5, 1.15, 0.95]), cv.ellipse(e, 1.05, 1.0), cv.limb([e, lerp2(e, h, 0.5), h], [0.95, 0.8, 0.7]))
    cv.shape(arm, m, z=z, sd=0.8, hi=0.25 if near else 0.0, ol=0.9,
             details=[('ink', [lerp2(e, h, 0.15), lerp2(e, h, 0.6)], 0.6, (0.3, 0.6))] if near else ())
    # yırtık çivit yen: üst kolu örter, dirsekten şerit sarkar
    D = DRESS if near else DRESS_B
    sl = cv.limb([sp, lerp2(sp, e, 0.55), lerp2(sp, e, 0.92)], [2.3, 2.0, 1.9])
    cv.shape(sl, D, z=z + 0.3, sd=0.9, hi=0.25 if near else 0.0, ol=0.9)
    for j in range(2):
        q = lerp2(sp, e, 0.78 + j * 0.12)
        a0 = math.pi * 0.55 + math.sin(ph + j * 2) * 0.25 + p['drag'] * 0.7
        st = [q]
        for s in range(3):
            st.append((st[-1][0] + math.cos(a0 + s * 0.15) * 1.6, st[-1][1] + math.sin(a0 + s * 0.15) * 1.6))
        cv.shape(ik.taper_path([cv.W(s) for s in st], cv.u(1.1), (0.05, 0.9)), D, z=z + 0.35 + j * 0.01, sd=0.3, ol=0.7)
    ang = math.atan2(h[1] - e[1], h[0] - e[0]) + wrist
    if kind == 'dagger':
        pc, tip = _dagger_hand(cv, h, ang, p['dg'], z + 0.5, p)
        return pc, tip
    pc, tips = _claw_hand(cv, h, ang, p['gb'], p['spr'], z + 0.5, near, ph, p['tw'])
    return pc, tips[1]


def _smear(cv, c, r, a0, a1, w, z, alpha=0.9, claws=False):
    """Buz-mavisi hilal izi: ucunda (a1) kalın, başında incelen yay; pençede üç ince paralel iz."""
    def band(rr, ww, al):
        n = 16
        out, inn = [], []
        for i in range(n + 1):
            u = i / n
            a = a0 + (a1 - a0) * u
            t = ww * (u ** 1.4) * (1.0 - 0.6 * max(0.0, u - 0.88) / 0.12)
            out.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr))
            inn.append((c[0] + math.cos(a) * (rr - t), c[1] + math.sin(a) * (rr - t)))
        path = cv.poly(out + inn[::-1])
        cv.fill(path, (0.78, 0.96, 1.0), z=z, alpha=al, glow=GLOW)
        cv.stroke(out[4:], 0.9, z=z + 0.01, col=INK, taper=(0.9, 0.1), alpha=0.85)
        cv.stroke(inn[8:], 0.6, z=z + 0.01, col=(0.2, 0.5, 0.8), taper=(0.9, 0.2), alpha=0.7)
    if claws:
        for k in range(3):
            band(r - k * 1.7, w * 0.45, alpha * (1.0 - 0.15 * k))
    else:
        band(r, w, alpha)


def _crystal(cv, c, a, L, w, z, glow_a=0.4):
    d = (math.cos(a), math.sin(a))
    n = (-d[1], d[0])
    pts = [(c[0] - d[0] * L * 0.45, c[1] - d[1] * L * 0.45, 0.0), (c[0] + n[0] * w, c[1] + n[1] * w),
           (c[0] + d[0] * L * 0.55, c[1] + d[1] * L * 0.55, 0.0), (c[0] - n[0] * w * 0.8, c[1] - n[1] * w * 0.8)]
    cv.shape(cv.blob(pts), ICE, z=z, sd=0.4, hi=0.3, ol=0.85, glow=ICE_G,
             details=[('stroke', [(c[0] - d[0] * L * 0.3, c[1] - d[1] * L * 0.3), (c[0] + d[0] * L * 0.4, c[1] + d[1] * L * 0.4)], 0.6, (1, 1, 1), (0.2, 0.7))])
    yk.glow_soft(cv, c, L * 0.6, GLOW, z=z - 0.01, alpha=glow_a)


def _snow(cv, c, k, ph, seed, z):
    """Kar girdabı: gövde çevresinde dönen kar zerreleri + beyaz rüzgâr yayları."""
    if k <= 0.02:
        return
    rng = np.random.default_rng(seed)
    for i in range(int(10 + 22 * k)):
        a = rng.uniform(0, math.tau) + ph * 0.8
        r = rng.uniform(3.0, 9.0 + 10.0 * k)
        q = (c[0] + math.cos(a) * r, c[1] + math.sin(a) * r * 1.4 - 4.0 * k * rng.uniform(0, 1))
        s = rng.uniform(0.35, 0.9)
        cv.shape(cv.ellipse(q, s, s * 0.85), SNOW, z=z + i * 0.001, sd=0.2, ol=0.55, glow=(0.08, 0.25, 0.35))
    for j in range(3):
        r = 6.0 + 4.0 * j + 5.0 * k
        a0 = ph * 1.3 + j * 2.1
        pts = [(c[0] + math.cos(a0 + u * 2.4) * r, c[1] + math.sin(a0 + u * 2.4) * r * 1.5) for u in np.linspace(0, 1, 9)]
        cv.stroke(pts, 1.4, z=z + 0.5, col=(0.92, 0.97, 1.0), taper=(0.9, 0.2), alpha=0.75 * min(1.0, k * 1.5), glow=(0.15, 0.45, 0.6))
        cv.stroke(pts[3:], 0.6, z=z + 0.49, col=INK, taper=(0.8, 0.3), alpha=0.5 * min(1.0, k * 1.5))
    yk.glow_soft(cv, c, 10 + 8 * k, GLOW, z=z - 1, blur=0.6, alpha=0.3 * k)


# ------------------------------------------------------------------ bütün figür
def draw(cv, p):
    yg.bake_xf(cv)
    ph = p['ph']
    fxp = p.get('_fx', 'all')
    hip = (0.0, -21.0 + p['bob'])
    if fxp in ('all', 'fx'):
        _snow(cv, (1.0, -24.0), p['snow'], ph, 31 + int(p['snow'] * 7), 50)
    if fxp == 'fx':
        return {'hand': (0.0, 0.0)}
    if p['streak'] > 0:
        u29.speed_lines(cv, (-6, -22), (1.0, 0.0), n=5, L=12 * p['streak'], spread=26, w=1.3, col=(0.75, 0.85, 0.98), alpha=0.45, z=-40, seed=int(ph * 7) % 40)
    u29.body_xf(cv, hip, p['rot'], p['sx'], p['sy'], p['jit'], 0.0)
    lean = p['lean']
    lx = lean * 4.0
    sh = (-0.5 + lx, -35.5 + p['bob'] * 0.6 + lean * 2.0)
    hd = (sh[0] + 6.0 + lean * 1.5 + p['hd'][0], sh[1] - 3.0 + lean * 1.2 + p['hd'][1])
    drag = p['drag']
    sw = math.sin(ph) * 0.7
    dx = -drag * 4.5

    # ---- arkadaki saç kütlesi + arka kol
    yg.xf_push(cv, hd, 0.0, 0.0, 0.0, 1.15, 1.15)
    _hair(cv, hd, p, ph, True)
    cv.pop()
    sb = (sh[0] - 0.6, sh[1] + 1.2)
    _arm(cv, sb, p['ab'], p['wb'], -12, False, ph, p, 'claw')

    # ---- elbisenin arkada savrulan yırtık şeritleri
    for j in range(4):
        q = (-5.0 + j * 1.2 + dx * 0.5, -10.0 + j * 1.5)
        a0 = math.pi * 0.72 + math.sin(ph + j * 1.4) * 0.15 + drag * 0.35
        st = [q]
        for s in range(4):
            st.append((st[-1][0] + math.cos(a0 - s * 0.12) * 2.4, st[-1][1] + math.sin(a0 - s * 0.12) * 2.4))
        cv.shape(ik.taper_path([cv.W(s) for s in st], cv.u(2.0), (0.1, 0.9)), DRESS_B, z=-6 + j * 0.01, sd=0.5, ol=0.8)

    # ---- elbise: kambur sırt, dar bel, yere dek açılan yırtık etek
    hem = yk.ragged((7.6 + dx * 0.35 + sw * 0.5, -2.6), (-10.5 + dx + sw, -2.2), 7, 3.0, seed=5, side=-1.0)
    dress = cv.blob([(sh[0] + 3.2, sh[1] - 0.8), (sh[0] - 2.4, sh[1] - 1.8), (sh[0] - 4.8, sh[1] + 2.4), (hip[0] - 4.2 + dx * 0.15, hip[1] - 1.0),
                     (-7.0 + dx * 0.6, -9.0), (-10.5 + dx + sw, -2.2, 0.0)] + hem[::-1] +
                    [(7.6 + dx * 0.35 + sw * 0.5, -2.6, 0.0), (4.6 + dx * 0.2, -9.0), (hip[0] + 3.4, hip[1] - 1.2), (sh[0] + 4.4, sh[1] + 5.4)])
    det = []
    det += cv.fold([(hip[0] + 1.0, hip[1] - 1.0), (1.4 + dx * 0.2, -10.0), (2.6 + dx * 0.3, -3.0)], 0.9, 1.2, -1)
    det += cv.fold([(hip[0] - 2.0, hip[1]), (-3.6 + dx * 0.5, -10.0), (-5.6 + dx * 0.8, -3.0)], 1.0, 1.2, 1)
    det += cv.fold([(sh[0] - 3.2, sh[1] + 4), (hip[0] - 3.0, hip[1] - 3.0)], 0.6, 1.0, 1)
    det.append(('stroke', [(hip[0] - 3.8, hip[1] - 0.6), (hip[0] + 0.2, hip[1] - 0.2), (hip[0] + 3.4, hip[1] - 0.8)], 1.3, (0.62, 0.72, 0.9), (0.05, 0.05)))
    det.append(('deep', cv.blob([(-10.5 + dx + sw, -2.2), (-6.0 + dx * 0.6, -8.0), (-3.0 + dx * 0.3, -2.4)])))
    cv.shape(dress, DRESS, z=0, sd=2.2, hi=0.5, details=det, hatch=0.35, bounce=0.3)
    # kuşaktan sarkan kemik / buz muskaları
    for k in range(2):
        q = (hip[0] - 1.2 + k * 2.6, hip[1] - 0.2)
        e = (q[0] + math.sin(ph + k) * 0.4 - drag * 1.2, q[1] + 3.4 + k * 0.6)
        cv.stroke([q, e], 0.6, z=1, col=(0.55, 0.62, 0.8))
        cv.shape(cv.blob([(e[0] - 0.5, e[1]), (e[0] + 0.5, e[1]), (e[0], e[1] + 2.0, 0.0)]), ICE, z=1.1 + k * 0.01, sd=0.2, ol=0.7, glow=ICE_G)

    # ---- boyun + baş + taç + öndeki saç
    nb = (sh[0] + 2.4, sh[1] - 0.6)
    cv.shape(cv.limb([nb, lerp2(nb, (hd[0] - 0.4, hd[1] + 3.0), 0.5), (hd[0] - 0.4, hd[1] + 3.0)], [1.4, 1.1, 1.2]), SKIN, z=8, sd=0.6,
             details=[('ink', [lerp2(nb, hd, 0.2), lerp2(nb, hd, 0.6)], 0.6, (0.3, 0.3))])
    yg.xf_push(cv, hd, 0.0, 0.0, 0.0, 1.15, 1.15)
    _head(cv, hd, p)
    _crown(cv, hd, p)
    cv.pop()

    # ---- kakım postu: omuzlarda kürk şal, kara uçlu kuyruklar
    bl = (sh[0] - 8.0 + dx * 0.25, sh[1] + 9.0)
    fl = (sh[0] + 5.6, sh[1] + 5.2)
    edge = yk.ragged(bl, fl, 7, 1.8, seed=9, side=1.0)
    shawl = cv.blob([(sh[0] + 4.4, sh[1] - 1.6), (sh[0] + 1.0, sh[1] - 3.6), (sh[0] - 3.8, sh[1] - 3.4), (sh[0] - 6.8, sh[1] + 0.4),
                     (bl[0], bl[1], 0.0)] + edge + [(fl[0], fl[1], 0.0), (sh[0] + 6.0, sh[1] + 1.6)])
    sdet = [('ink', [(sh[0] - 5.4, sh[1] + 1.2), (sh[0] - 2.4, sh[1] + 4.4), (sh[0] + 1.4, sh[1] + 4.8)], 0.7, (0.3, 0.4)),
            ('ink', [(sh[0] - 2.0, sh[1] - 2.4), (sh[0] - 4.4, sh[1] + 2.0)], 0.6, (0.3, 0.5)),
            ('shade', cv.wedge([(sh[0] - 7.0, sh[1] + 2.4), (sh[0] - 1.0, sh[1] + 6.6), (sh[0] + 5.0, sh[1] + 4.6)], 1.4, -1))]
    cv.shape(shawl, FUR, z=18, sd=1.2, hi=0.45, details=sdet, fur=0.7, ol=1.0)
    for j, (u, Ln) in enumerate(((0.1, 3.4), (0.42, 4.2), (0.78, 3.8))):
        q = lerp2((fl[0] - 0.8, fl[1] - 0.6), (bl[0] + 0.8, bl[1] - 0.8), u)
        a0 = math.pi * 0.5 + math.sin(ph + j * 1.9) * 0.18 + drag * 0.6 + lean * 0.1
        st = [q]
        for s in range(3):
            st.append((st[-1][0] + math.cos(a0 + s * 0.12) * Ln / 3, st[-1][1] + math.sin(a0 + s * 0.12) * Ln / 3))
        cv.shape(ik.taper_path([cv.W(s) for s in st], cv.u(1.7), prof=lambda x: 0.7 + 0.4 * math.sin(math.pi * min(1, x * 1.1))), FUR, z=18.5 + j * 0.01,
                 sd=0.4, ol=0.8, fur=0.5)
        e = st[-1]
        cv.shape(cv.blob([(e[0] - 0.75, e[1] - 0.6), (e[0] + 0.75, e[1] - 0.6), (e[0] + math.cos(a0) * 1.3, e[1] + math.sin(a0) * 1.3, 0.0)]), TIP,
                 z=18.6 + j * 0.01, sd=0.2, ol=0.7)
    yg.xf_push(cv, hd, 0.0, 0.0, 0.0, 1.15, 1.15)
    _hair(cv, hd, p, ph, False)
    cv.pop()

    # ---- ön kol: buz hançeri
    sf = (sh[0] + 2.4, sh[1] + 1.8)
    pc, tip = _arm(cv, sf, p['af'], p['wf'], 30, True, ph, p, 'dagger')

    # ---- kristaller (atk_shards): eller arasında büyür / yelpaze gibi fırlar
    anchor = pc
    ice = p['ice']
    if ice > 0.02:
        cc = (p['af'][0] * 0.5 + p['ab'][0] * 0.5 + 2.5, min(p['af'][1], p['ab'][1]) - 1.0)
        yk.glow_soft(cv, cc, 5.0 + 8.0 * ice, GLOW, z=34, blur=0.6, alpha=0.5 + 0.3 * ice)
        cv.fill(cv.ellipse(cc, 1.0 + 1.4 * ice, 1.0 + 1.4 * ice), HOT, z=34.5, glow=GLOW)
        for k in range(6):
            a = ph * 0.6 + k * math.tau / 6
            r = 1.0 + 2.6 * ice
            q = (cc[0] + math.cos(a) * r, cc[1] + math.sin(a) * r * 0.8)
            _crystal(cv, q, a + 0.4, (2.4 + 4.4 * ice) * (0.8 + 0.12 * (k % 3)), 0.6 + 0.8 * ice, 35 + k * 0.01, glow_a=0.2)
        yk.sparks(cv, cc, 6, 2.0 + 3.0 * ice, 4.0 + 5.0 * ice, HOT, 36, seed=int(ph * 5) + 3, w=0.8, glow=GLOW)
        anchor = cc
    sh_ = p['shard']
    if sh_ > 0.02:
        o = pc
        for k, a in enumerate((-0.32, -0.05, 0.22)):
            dd = 4.0 + 18.0 * sh_ * (1.0 - 0.12 * k)
            q = (o[0] + math.cos(a) * dd, o[1] + math.sin(a) * dd)
            cv.stroke([(o[0] + math.cos(a) * dd * 0.35, o[1] + math.sin(a) * dd * 0.35), q], 1.6, z=37, col=(0.75, 0.95, 1.0), taper=(0.95, 0.1), alpha=0.7, glow=GLOW)
            _crystal(cv, q, a, 5.5, 1.3, 38 + k * 0.01, glow_a=0.5)
        yk.sparks(cv, o, 7, 1.5, 4.5, HOT, 36, seed=19, w=0.9, glow=GLOW, ang=0.0, spread=1.6)
    thr = p.get('thr', 0.0)
    if thr > 0:
        d = (tip[0] - pc[0], tip[1] - pc[1])
        L = math.hypot(*d) or 1.0
        d = (d[0] / L, d[1] / L)
        n = (-d[1], d[0])
        t0 = (tip[0] + d[0] * 1.0, tip[1] + d[1] * 1.0)
        for k, (off, ln, w) in enumerate(((0.0, 16.0, 2.4), (2.6, 11.0, 1.0), (-2.4, 9.0, 0.9))):
            a = (t0[0] + n[0] * off * 0.5, t0[1] + n[1] * off * 0.5)
            b = (a[0] - d[0] * ln + n[0] * off, a[1] - d[1] * ln + n[1] * off)
            pts = [b, lerp2(b, a, 0.6), a]
            cv.stroke(pts, w * 2.2, z=40 + k * 0.01, col=(0.8, 0.97, 1.0), taper=(0.95, 0.15), alpha=0.85 * thr, glow=GLOW)
            cv.stroke(pts, w * 0.7, z=40.05 + k * 0.01, col=INK, taper=(0.95, 0.3), alpha=0.6 * thr)
        yk.sparks(cv, t0, 6, 0.8, 3.5, HOT, 41, seed=23, w=0.9, glow=GLOW, ang=0.0, spread=1.8)
        yk.glow_soft(cv, t0, 4.0, GLOW, z=39.9, alpha=0.6 * thr)
    for sm in p.get('sm', ()):
        _smear(cv, *sm)
    hand = u29.to_world(cv, anchor)
    cv.pop()
    return {'hand': hand}


# ================================================================== animasyon tabloları
REST = dict(bob=0.0, lean=0.6, rot=0.0, sx=1.0, sy=1.0, jit=(0.0, 0.0), hd=(0.0, 0.0), af=(12.5, -19.5), ab=(7.0, -17.5), wf=0.2, wb=0.4,
            dg=-1.0, gb=0.55, spr=0.3, tw=0.0, wind=1.0, hup=0.0, drag=0.0, flare=0.0, pain=0.0, ice=0.0, shard=0.0, dis=0.0, snow=0.0,
            streak=0.0)
S2 = math.tau


def _keys(ts, frames):
    """Kare başına anahtar (kare anı = anahtar anı; ara değer doğrusal)."""
    return [(t, d, 'l') for t, d in zip(ts, frames)]


def _idle(t):
    s = math.sin
    a = S2 * t
    return dict(REST, bob=0.5 * s(a), lean=0.6 + 0.05 * s(a + 0.6), rot=0.02 * s(a - 0.4), af=(12.5 + 0.6 * s(a), -19.5 + 0.8 * s(a + 1.0)),
                ab=(7.0 + 0.5 * s(a + 2.0), -17.5 + 0.6 * s(a + 0.5)), gb=0.5 + 0.3 * s(2 * a), tw=1.0, hd=(0.3 * s(a), 0.2 * s(a + 1)),
                wind=1.0 + 0.1 * s(a))


def _move(t):
    s = math.sin
    a = S2 * t
    return dict(REST, bob=-0.6 - 0.6 * s(2 * a), lean=0.88, rot=0.08 + 0.02 * s(2 * a), drag=1.0 + 0.15 * s(a),
                af=(15.0 + 2.0 * s(a), -23.0 + 1.2 * s(a + 1.2)), ab=(11.0 - 2.5 * s(a), -18.0 + 1.0 * s(a + 0.4)), gb=0.35 + 0.2 * s(a), spr=0.6,
                wind=1.35, hup=0.1, streak=0.6, tw=0.5, hd=(0.5, 0.4))


_STAB_TS = [0.0, 0.1, 0.2, 0.3, 0.34, 0.46, 0.58, 0.7, 0.8, 0.9]
_STAB = _keys(_STAB_TS, [
    dict(flare=0.3, lean=0.65, af=(12.0, -21.0), ab=(7.0, -19.0)),
    dict(bob=1.5, lean=0.9, rot=-0.08, af=(3.0, -27.0), ab=(-2.0, -22.0), dg=-0.2, flare=0.6, hup=0.3, gb=0.2, spr=0.7, sx=1.03, sy=0.97),
    dict(bob=2.6, lean=1.0, rot=-0.18, af=(-1.0, -30.0), ab=(-5.0, -24.0), dg=0.1, flare=1.0, hup=0.55, gb=0.05, spr=1.0, sx=1.05, sy=0.94, jit=(-1.0, 0.0)),
    dict(bob=2.8, lean=1.02, rot=-0.2, af=(-1.6, -30.6), ab=(-5.6, -24.4), dg=0.15, flare=1.0, hup=0.6, gb=0.0, spr=1.0, sx=1.06, sy=0.93, jit=(-1.3, 0.0)),
    # temas 1: hançer yukarıdan aşağı-öne biçer
    dict(bob=0.5, lean=1.0, rot=0.14, af=(20.0, -18.0), ab=(-1.0, -23.0), dg=-0.5, flare=1.0, hup=0.3, sx=0.98, sy=1.03, jit=(4.0, 0.0)),
    # temas 2: arka el pençeyle aşağıdan yukarı tırmalar
    dict(bob=0.2, lean=0.95, rot=0.06, af=(8.0, -22.0), ab=(21.0, -30.0), dg=-0.6, wb=-0.3, gb=0.0, spr=0.9, flare=0.9, jit=(5.0, 0.0)),
    # temas 3: hançer dümdüz saplanır
    dict(bob=0.0, lean=1.05, rot=0.16, af=(21.0, -26.0), ab=(9.0, -22.0), dg=-0.05, wf=0.0, wb=0.4, gb=0.3, flare=0.9, jit=(6.0, 0.0), sx=1.04, sy=0.98),
    dict(bob=0.6, lean=1.0, rot=0.12, af=(19.0, -21.0), ab=(13.0, -16.0), dg=-0.4, gb=0.4, flare=0.6, jit=(6.0, 0.0)),
    dict(bob=0.4, lean=0.8, rot=0.04, af=(15.0, -20.0), ab=(9.0, -17.0), dg=-0.8, flare=0.4, jit=(4.0, 0.0)),
    dict(bob=0.1, lean=0.65, rot=0.0, af=(13.0, -19.5), ab=(7.0, -17.5), dg=-1.0, flare=0.2, jit=(1.5, 0.0)),
])

# kareye çizili kesik izleri (poz karışımına girmez): (merkez, yarıçap, a0, a1, kalınlık, z[, alfa, pençe])
SMEARS = {('atk_stab', 4): [((9.0, -27.0), 13.5, -1.9, 0.55, 4.6, 40)],
          ('atk_stab', 5): [((12.0, -21.0), 11.5, 1.1, -0.75, 3.4, 41, 0.9, True)],
          ('atk_stab', 7): [((12.0, -21.0), 11.0, 0.2, -0.75, 2.0, 39, 0.35, True)]}
THRUST = {('atk_stab', 6): 1.0, ('atk_stab', 7): 0.4}     # saplama izi: hançer ucunun arkasında uzun sivri buz izi

_SHARD_TS = [0.0, 0.14, 0.28, 0.42, 0.48, 0.6, 0.76, 0.9]
_SHARDS = _keys(_SHARD_TS, [
    dict(lean=0.55, af=(11.0, -27.0), ab=(6.0, -27.0), flare=0.2, dg=-1.4, wb=-0.4),
    dict(lean=0.3, bob=-1.0, af=(12.0, -45.0), ab=(7.0, -46.0), wf=-0.4, wb=-0.6, dg=-1.6, ice=0.35, flare=0.5, hup=0.3, gb=0.2, spr=0.8, sy=1.03),
    dict(lean=0.2, bob=-1.4, rot=-0.06, af=(11.5, -46.0), ab=(6.5, -47.0), wf=-0.5, wb=-0.7, dg=-1.6, ice=0.7, flare=0.8, hup=0.5, gb=0.1, spr=1.0, sy=1.05),
    dict(lean=0.15, bob=-1.6, rot=-0.13, af=(11.0, -46.5), ab=(6.0, -47.4), wf=-0.5, wb=-0.7, dg=-1.6, ice=1.0, flare=1.0, hup=0.6, gb=0.0, spr=1.0, sy=1.06, jit=(-1.0, 0.0)),
    dict(lean=0.95, bob=0.5, rot=0.14, af=(21.0, -28.0), ab=(18.0, -26.0), wf=0.0, wb=0.0, dg=-0.4, ice=0.0, shard=0.15, flare=1.0, hup=0.2, gb=0.0, spr=1.0, jit=(2.5, 0.0), sx=1.03),
    dict(lean=1.0, bob=0.8, rot=0.16, af=(22.0, -25.0), ab=(19.0, -23.0), dg=-0.4, shard=0.55, flare=0.7, jit=(3.0, 0.0)),
    dict(lean=0.8, bob=0.5, rot=0.06, af=(16.0, -21.0), ab=(11.0, -19.0), dg=-0.8, shard=0.0, flare=0.3, gb=0.4, spr=0.5, jit=(2.0, 0.0)),
    dict(lean=0.65, bob=0.1, rot=0.0, af=(13.0, -19.5), ab=(7.0, -17.5), dg=-1.0, flare=0.1, gb=0.55, spr=0.3, jit=(0.5, 0.0)),
])

_HURT = _keys([0.0, 0.5, 1.0], [
    dict(rot=-0.17, bob=0.6, lean=0.25, jit=(-1.0, 0.0), af=(7.0, -27.0), ab=(-1.0, -29.0), wf=-0.6, dg=-1.4, pain=1.0, hup=0.7, gb=0.0, spr=1.0, sx=0.96, sy=1.04, drag=-0.6),
    dict(rot=-0.09, bob=0.8, lean=0.4, jit=(-1.4, 0.0), af=(9.0, -23.0), ab=(2.0, -24.0), dg=-1.2, pain=0.7, hup=0.4, gb=0.3, drag=-0.3),
    dict(rot=-0.03, bob=0.3, lean=0.55, jit=(-1.0, 0.0), af=(11.5, -20.0), ab=(6.0, -18.5), dg=-1.0, pain=0.3, hup=0.1, gb=0.5),
])

_BLINK = _keys([0.0, 0.2, 0.4, 0.6, 0.8, 1.0], [
    dict(bob=1.5, lean=0.9, rot=0.0, af=(8.0, -27.0), ab=(5.0, -28.0), dg=-1.6, wf=-0.6, flare=1.0, hup=0.5, snow=0.3, gb=0.6, sy=0.96),
    dict(bob=1.0, lean=0.9, af=(7.0, -28.0), ab=(4.0, -29.0), flare=1.0, hup=0.7, snow=0.6, dis=0.22, sx=0.95, sy=1.03),
    dict(bob=0.5, af=(6.5, -29.0), ab=(3.5, -30.0), hup=0.9, snow=0.9, dis=0.48, sx=0.9, sy=1.06),
    dict(bob=0.0, hup=1.0, snow=1.0, dis=0.72, sx=0.84, sy=1.1),
    dict(bob=-0.5, snow=0.8, dis=0.92, sx=0.8, sy=1.12),
    dict(bob=-0.8, snow=0.45, dis=1.0, sx=0.78, sy=1.14),
])


def _row(frames, fps, loop, pose, ts=None, mk=None, vx=None):
    return dict(frames=frames, fps=fps, loop=loop, pose=pose, ts=ts, mk=mk, vx=vx)


def _nl(keys):
    return lambda t: pose_at(t, keys, base=REST)


ROWS = None


def anims_for(var='kar_cadisi'):
    global ROWS
    if ROWS is None:
        ROWS = {
            'idle': _row(8, 8, True, _idle),
            'move': _row(8, 11, True, _move, vx=80.0),
            'hurt': _row(3, 14, False, _nl(_HURT)),
            'atk_stab': _row(10, 12, False, _nl(_STAB), ts=_STAB_TS, mk=[0.3, 0.34, 0.8]),
            'atk_shards': _row(8, 10, False, _nl(_SHARDS), ts=_SHARD_TS, mk=[0.42, 0.48, 0.62]),
            'blink': _row(6, 12, False, _nl(_BLINK)),
        }
    return ROWS


def durum_for(var='kar_cadisi'):
    d = {'idle': 'idle', 'chase': 'move', 'recover': 'idle', 'evade': 'move', '_hurt': 'hurt', '_hurt_big': 'hurt', '_break': 'hurt'}
    for m in ('stab', 'shards'):
        for k in ('windup', 'act', 'recover'):
            d['%s/%s' % (k, m)] = 'atk_' + m
    d.update({'windup/blink': 'blink', 'blink_out': 'blink', 'blink_in': 'blink'})
    return d


def frame_time(row, i):
    if row['ts']:
        return row['ts'][i]
    if row['loop']:
        return i / row['frames']
    return i / max(1, row['frames'] - 1)


SHADE = dict(outer=0.6, rim=0.75, rim_col=(0.7, 0.9, 1.0), rim_dir=(0.6, -0.8), rim_w=1.3, form=(4.0, (0.72, 0.74, 0.9)))


def render_frame(anim, i, var='kar_cadisi', ss=3):
    row = anims_for(var)[anim]
    tt = frame_time(row, i)
    p = dict(row['pose'](tt))
    p['sm'] = SMEARS.get((anim, i), ())
    p['thr'] = THRUST.get((anim, i), 0.0)
    p['ph'] = tt * math.tau * (1 if row['loop'] else 0.6) + (0 if row['loop'] else i * 0.9)
    split = p.get('dis', 0.0) > 0
    if split:
        p['_fx'] = 'body'
    cv = u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    if split:
        rgba, em = u29.dissolve(rgba, em, p['dis'], seed=91, hd=cv.hd, grad=(0.3, -0.5), hot=(0.45, 0.9, 1.0), hot_a=1.0)
        cf = u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss)
        draw(cf, dict(p, _fx='fx'))
        fr, _n, fe = cf.finish(outer=0.4)
        rgba, em = u29.over(fr, fe, rgba, em)
    return rgba, nm, em, info
