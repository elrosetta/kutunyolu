"""v39: Aldaraş (kimlik aldaras) — Bozkır'ın kum fırtınasında dolaşan kâbus iblisi (AI ricochet).

Tasarım: sıska, uzun uzuvlu, insandan uzun ve ince göçebe cin; hep çömelik, yaylanan duruş. Kum aşısı (okra) yırtık
sargılara bürünmüş, boynundan rüzgârda dalgalanan uzun kızıl kuşak-atkı (ikinci ucu belde), çatlak tunç maskede üç
ışıyan göz yarığı (iki göz + alında dikey üçüncü; sıcak sarı-turuncu), çıplak, kaslı-sinirli koyu çivit kollar, kıvrık
pençeler. İki elinde tunç hilal orak.

Satırlar (hücre 288x256, dünya 72x64; ayak (112, 244) = dünya (28, 61)):
  idle 8 (çömelik salınım, atkı akar), move 8 (uzun adımlı yaylanan koşu, vx 110), hurt 3,
  atk_throw 8 (mk; orak başın arkasına kurulur, dönerek fırlar: dönen hilal + dönüş izi; el boş kalır, sonda yakalar),
  atk_flurry 10 (mk uzun etkin pencere; çapraz bıçak kurulumu, öne adımlayarak dört almaşık orak savuruşu + hilal izleri),
  flip 5 (döngüsüz geri takla kaçışı).
Çapa 'hand' = ön orak (yakın el) / fırlatılmış orağın konumu, her karede.
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import lerp2, chain
import yaratik_govde as yg
import yaratik_ink_kit as yk
import ucan_v29 as u29
from ucan_v29 import pose_at
import y39_mizrak_kit as mk
from y39_mizrak_kit import along, add, dirv

TEX = 4.0
CELL = (288, 256)
FEET = (112, 244)

SKIN = Ink('#3c3e80', '#1c1c48', '#6e70b8', '#0c0c26', name='çivit ten')
SKIN_B = SKIN.darker(0.72)
RAG = Ink('#b88a48', '#6a4624', '#e2bc7c', '#34200e', name='kum sargı')
RAG_B = RAG.darker(0.72)
SASH = Ink('#c4282a', '#621018', '#f05c46', '#2c060a', name='kızıl atkı')
SASH_B = SASH.darker(0.75)
MASK = Ink('#b47c3a', '#5a3418', '#f0ca8a', '#2a160a', kind='metal', name='çatlak tunç maske')
BRONZE = Ink('#cc9448', '#6a4020', '#ffe2a2', '#341c0a', kind='metal', name='tunç orak')
BRONZE_B = BRONZE.darker(0.75)
CLAW = Ink('#2a2028', '#100c10', '#6a5a60', name='pençe')
SAND = Ink('#a88a5c', '#6a5236', '#d2b688', name='kum')
EYE = (1.0, 0.9, 0.42)
GLOW = (1.0, 0.55, 0.06)

H0 = 20.5
L_TH, L_SH = 12.0, 11.5
TORSO = 15.5
A_UP, A_FO = 10.5, 10.0


def _sickle(cv, h, ang, near, z, glint=0.0):
    """Hilal orak: elde kısa sap (ang yönünde), sapın ucundan kavisli tunç ağız (hilal, oyuğu +n yanında)."""
    d = dirv(ang)
    n = (-d[1], d[0])
    butt = add(h, d, -2.2)
    top = add(h, d, 2.6)
    cv.shape(cv.capsule(butt, top, 0.75, 0.7), Ink('#4a3020', '#22140e', '#7a5638'), z=z, sd=0.4, ol=0.85)
    O = add(top, d, 4.4)
    outer = cv.ellipse(add(O, n, -0.6), 4.6, 4.6)
    inner = cv.ellipse(add(add(O, n, 1.6), d, 0.3), 4.2, 4.2)
    blade = ik.diff(outer, inner)
    m = BRONZE if near else BRONZE_B
    cv.shape(blade, m, z=z + 0.1, sd=0.6, hi=0.5, ol=0.9, glow=(0.08, 0.04, 0.0))
    # ağız kenarı parıltısı (iç kenar keskin)
    pts = [add(O, (math.cos(a) * 3.0, math.sin(a) * 3.0)) for a in np.linspace(math.atan2(-n[1], -n[0]) - 1.2, math.atan2(-n[1], -n[0]) + 1.2, 6)]
    pts = [add(add(q, n, 0.6), (0, 0)) for q in pts]
    cv.stroke(pts, 0.7, z=z + 0.15, col=BRONZE.hi, taper=(0.4, 0.4), glow=(GLOW[0] * (0.3 + glint), GLOW[1] * (0.3 + glint), GLOW[2] * (0.3 + glint)))
    cv.shape(cv.capsule(add(top, d, -0.5), add(top, d, 0.6), 1.1, 1.1), BRONZE, z=z + 0.12, sd=0.3, ol=0.8)
    return add(O, n, -3.0)


def _smear(cv, c, r, a0, a1, k, z=25.0):
    mk.smear_arc(cv, c, r, a0, a1, 3.6 * k, (0.95, 0.55, 0.2), (0.6, 0.28, 0.02), z, alpha=0.6 * k, hot=(1.0, 0.85, 0.5))


def _claws(cv, h, ang, z, near, spread=0.4, n=4, L=3.0):
    m = SKIN if near else SKIN_B
    cv.shape(cv.ellipse(h, 1.5, 1.2, ang), m, z=z, sd=0.4, ol=0.85)
    for k in range(n):
        a = ang + (k - (n - 1) / 2) * spread
        b = add(h, dirv(a), 1.0)
        m1 = add(b, dirv(a), L * 0.55)
        tip = add(m1, dirv(a + 0.7), L * 0.55)
        cv.shape(cv.limb([b, m1], [0.45, 0.35]), m, z=z + 0.05, sd=0.2, ol=0.7)
        cv.shape(cv.blob([add(m1, dirv(a + 2.2), 0.35), (tip[0], tip[1], 0.0), add(m1, dirv(a - 1.0), 0.35)]), CLAW, z=z + 0.06, sd=0.1, ol=0.6)


def _arm(cv, sh, h, near, z, ang, grip=True):
    bend = 1 if h[1] > sh[1] - 3 else -1
    e, h = yg.ik2(sh, h, A_UP, A_FO, bend)
    m = SKIN if near else SKIN_B
    up = cv.blob([along(sh, e, t, o) for t, o in ((-0.1, 1.6), (0.35, 2.0), (0.9, 1.3), (1.05, 0.0), (0.9, -1.3), (0.4, -1.8), (-0.1, -1.6))])
    cv.shape(up, m, z=z, sd=1.2, hi=0.3 if near else 0.0,
             details=[('ink', [along(sh, e, 0.3, 0.8), along(sh, e, 0.7, 0.4)], 0.7, (0.3, 0.6))] if near else ())
    fo = cv.blob([along(e, h, t, o) for t, o in ((-0.05, 1.2), (0.3, 1.6), (0.85, 0.9), (1.0, 0.7), (1.0, -0.7), (0.5, -1.2), (-0.05, -1.2))])
    cv.shape(fo, m, z=z + 0.1, sd=1.0, hi=0.3 if near else 0.0,
             details=[('ink', [along(e, h, 0.2, -0.4), along(e, h, 0.6, -0.6)], 0.6, (0.3, 0.6))] if near else ())
    # bilekte sargı
    cv.shape(cv.capsule(along(e, h, 0.7), along(e, h, 0.88), 1.1, 1.0), RAG if near else RAG_B, z=z + 0.15, sd=0.4, ol=0.8,
             details=[('ink', [along(e, h, 0.76, -1.0), along(e, h, 0.8, 1.0)], 0.6)])
    cv.shape(cv.ellipse(e, 1.4, 1.3), m, z=z + 0.05, sd=0.4, ol=0.0)
    if grip:
        cv.shape(cv.ellipse(h, 1.4, 1.2, ang + math.pi / 2), m, z=z + 2.0, sd=0.4, ol=0.85,
                 details=[('ink', [add(h, dirv(ang), -0.5 + k * 0.7), add(add(h, dirv(ang), -0.5 + k * 0.7), dirv(ang + math.pi / 2), 1.2)], 0.6) for k in range(2)])
        cv.shape(cv.blob([add(h, dirv(ang + math.pi / 2), 1.0), add(add(h, dirv(ang + math.pi / 2), 2.0), dirv(ang), -0.8) + (0.0,),
                          add(add(h, dirv(ang + math.pi / 2), 1.2), dirv(ang), -0.5)]), CLAW, z=z + 2.05, sd=0.1, ol=0.6)
    else:
        _claws(cv, h, math.atan2(h[1] - e[1], h[0] - e[0]), z + 0.2, near, spread=0.45)
    return e, h


def _leg(cv, hip, f, near, z, ph):
    k, f = yg.ik2(hip, f, L_TH, L_SH, -1)
    m = SKIN if near else SKIN_B
    rg = RAG if near else RAG_B
    cv.shape(cv.limb([hip, lerp2(hip, k, 0.5), k], [2.8, 2.4, 1.8]), rg, z=z, sd=1.4, details=cv.fold([lerp2(hip, k, 0.2), lerp2(hip, k, 0.8)], 0.5, 0.9, 1))
    sh = cv.limb([k, lerp2(k, f, 0.5), f], [1.8, 1.5, 1.1])
    cv.shape(sh, m, z=z + 0.1, sd=1.0, hi=0.25 if near else 0.0)
    for t in (0.15, 0.32, 0.5):   # baldır sargısı
        cv.shape(cv.capsule(along(k, f, t), along(k, f, t + 0.1), 1.9 - t, 1.8 - t), rg, z=z + 0.15, sd=0.3, ol=0.7)
    # uzun parmaklı ayak + pençe
    foot = cv.blob([(f[0] - 1.6, f[1] - 1.4), (f[0] + 1.6, f[1] - 1.2), (f[0] + 4.6, f[1] - 0.4), (f[0] + 5.2, f[1] + 0.2, 0.0), (f[0] - 1.4, f[1] + 0.3, 0.0)])
    cv.shape(foot, m, z=z + 0.2, sd=0.6, ol=0.9, details=[('ink', [(f[0] + 2.0, f[1] - 0.8), (f[0] + 4.0, f[1] - 0.2)], 0.6)])
    for j in range(2):
        b = (f[0] + 4.2 + j * 0.6, f[1] - 0.3 + j * 0.2)
        cv.shape(cv.blob([(b[0], b[1] - 0.4), (b[0] + 1.6, b[1] + 0.4, 0.0), (b[0], b[1] + 0.3)]), CLAW, z=z + 0.25, sd=0.1, ol=0.6)
    return k, f


def _scarf(cv, st, ang, L, w, mat, z, ph, wave, seed):
    pts = chain(st, 8, L / 8.0, ang, 0.06, ph, wave)
    W = [cv.W(q) for q in pts]
    path = ik.taper_path(W, cv.u(w), prof=lambda u: 0.85 + 0.25 * math.sin(u * 6 + seed))
    e, e1 = pts[-1], pts[-2]
    dx, dy = e[0] - e1[0], e[1] - e1[1]
    Ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / Ln * w * 0.5, dx / Ln * w * 0.5
    fork = cv.blob([(e1[0] + nx, e1[1] + ny), (e[0] + nx * 1.3 + dx * 0.6, e[1] + ny * 1.3 + dy * 0.6, 0.0), (e[0], e[1]),
                    (e[0] - nx * 1.2 + dx * 0.4, e[1] - ny * 1.2 + dy * 0.4, 0.0), (e1[0] - nx, e1[1] - ny)])
    det = [('ink', [pts[1], pts[2], pts[3]], 0.8, (0.3, 0.6)), ('ink', [pts[4], pts[5], pts[6]], 0.8, (0.3, 0.6)),
           ('shade', cv.wedge([pts[2], pts[3], pts[4]], w * 0.35, 1.0))]
    cv.shape(ik.union(path, fork), mat, z=z, sd=1.0, hi=0.35, ol=0.85, details=det)
    # saçak: kuşak ucunda ince püsküller
    for k in (-1, 0, 1):
        q = (e[0] + nx * k * 0.6, e[1] + ny * k * 0.6)
        cv.stroke([q, (q[0] + dx * 1.2 + k * 0.3, q[1] + dy * 1.2 + 0.4)], 0.6, z=z + 0.01, col=SASH.shadow, taper=(0.1, 0.8))
    return pts


REST = dict(x=0.0, y=0.0, roll=0.0, hx=0.0, hy=0.0, lean=0.38, fb=(-6.0, 0.0), ff=(6.0, 0.0),
            hb=(-2.0, 2.0), hf=(9.0, 0.0), sab=-1.2, saf=-1.0, fs=1.0, thr=0.0, tsp=0.0, ty=-24.0, catch=0.0,
            hd=(0.0, 0.0), flare=0.3, sc=0.5, sk=0.0, sm=(), dust=0.0, hurt=0.0, ph=0.0, tuck=0.0)
C_ROLL = (0.0, -22.0)


def draw(cv, p):
    yg.bake_xf(cv)
    q = dict(REST)
    q.update(p)
    p = q
    ph = p['ph']
    out = {}
    # ---- yer: gölge + kum tozu
    if p['y'] > -6:
        yk.wash(cv, cv.ellipse((p['x'] - 1.0, -0.4), 10.0 * (1 + p['y'] / 30.0), 1.4), (0.0, 0.0, 0.0), 0.25, z=-50, blur=0.8)
    if p['dust'] > 0.02:
        for k in range(4):
            r = (1.4 + 0.8 * k) * (0.6 + 0.6 * p['dust'])
            yk.wash(cv, cv.ellipse((p['x'] - 6.0 - k * 2.8, -r * 0.6 - (k % 2) * 0.8), r * 1.3, r * 0.8), SAND.base, 0.35 * p['dust'], z=-14 + k * 0.01, blur=0.6)
    # bütün figür: takla dönüşü (gövde ortası çevresinde) + öteleme
    yg.xf_push(cv, C_ROLL, p['roll'], p['x'], p['y'])
    hip = (p['hx'], -H0 + p['hy'])
    lean = p['lean']
    up = (math.sin(lean), -math.cos(lean))
    fw = (math.cos(lean), math.sin(lean))

    def T(u, v):
        v = v * 0.78   # sıska gövde
        return (hip[0] + up[0] * u + fw[0] * v, hip[1] + up[1] * u + fw[1] * v)
    neck = T(TORSO, 0.6)
    head = (neck[0] + 1.2 + up[0] * 3.5 + p['hd'][0], neck[1] + up[1] * 3.5 + p['hd'][1])
    sh_b = T(TORSO - 2.2, -1.6)
    sh_f = T(TORSO - 2.0, 1.4)
    sc = p['sc']
    # ---- atkı (arkada): boyundan rüzgârla geriye; ikinci uç belden
    _scarf(cv, T(TORSO - 0.5, -1.5), math.pi * (0.97 - 0.1 * sc) - lean * 0.3, 20.0 + 6.0 * sc, 2.8, SASH, -22, ph * 1.4, 0.35, 1)
    _scarf(cv, T(0.5, -2.5), math.pi * (0.8 - 0.12 * sc), 12.0 + 4.0 * sc, 2.0, SASH_B, -21, ph * 1.6 + 1.5, 0.4, 2)
    # ---- uzak kol + orak
    hbt = (hip[0] + p['hb'][0], hip[1] + p['hb'][1])
    e_b, h_b = _arm(cv, sh_b, hbt, False, -16.0, p['sab'])
    _sickle(cv, h_b, p['sab'], False, -15.0, glint=0.2)
    # ---- bacaklar
    fbt = (p['fb'][0], -p['fb'][1])
    fft = (p['ff'][0], -p['ff'][1])
    _leg(cv, (hip[0] - 1.0, hip[1]), fbt, False, -12.0, ph)
    # ---- gövde: sargılı ince gövde, yırtık bel saçakları
    torso = cv.blob([T(-1.5, -3.6), T(4.0, -3.4), T(9.0, -4.2), T(13.2, -3.6), T(15.0, -1.4), T(14.8, 2.2), T(12.0, 4.0),
                     T(7.0, 3.6), T(3.0, 3.6), T(-1.5, 3.8)])
    det = []
    for u in (2.0, 4.6, 7.2, 9.8):
        det.append(('ink', [T(u, -3.6), T(u + 1.6, 0.0), T(u + 2.8, 3.8)], 0.8, (0.1, 0.1)))
        det.append(('shade', cv.wedge([T(u + 0.3, -3.4), T(u + 1.9, 0.0), T(u + 3.0, 3.6)], 0.5, -1.0)))
    cv.shape(torso, RAG, z=0.0, sd=2.0, hi=0.35, details=det, hatch=0.3, bounce=0.3)
    # göğüste açık sargı arası: çivit ten + sinir çizgileri
    cv.shape(cv.blob([T(9.6, 1.2), T(12.6, 1.0), T(13.4, 3.2), T(11.0, 3.6)]), SKIN, z=0.2, sd=0.4, ol=0.6)
    # bel kuşağı (kızıl) + bel saçakları
    cv.shape(cv.blob([T(-0.6, -3.9), T(2.2, -3.8), T(2.4, 4.0), T(-0.8, 4.0)]), SASH, z=0.4, sd=0.6, hi=0.3, ol=0.9)
    for i in range(6):
        v = -3.0 + i * 1.3
        st = T(-0.6, v)
        sw = math.sin(ph * 2 + i * 1.1) * 0.8 - p['sk'] * 1.5 - 1.2
        ln = 5.5 + (i % 3) * 1.6
        pts = [st, (st[0] + sw * 0.4, st[1] + ln * 0.5), (st[0] + sw, st[1] + ln)]
        cv.shape(ik.taper_path([cv.W(q_) for q_ in pts], cv.u(1.2), (0.0, 0.85)), RAG if i % 2 else RAG_B, z=0.3 + i * 0.01, sd=0.3, ol=0.6)
    # ---- ön bacak
    _leg(cv, (hip[0] + 1.0, hip[1]), fft, True, 1.0, ph)
    # ---- baş: sargı başlık + çatlak tunç maske + üç göz yarığı
    hs = 0.8   # küçük baş (uzun boylu cin oranı)
    cv.push(lambda q_, c=head: (c[0] + (q_[0] - c[0]) * hs, c[1] + (q_[1] - c[1]) * hs))
    hx, hy = head
    hood = cv.blob([(hx - 3.6, hy + 3.0), (hx - 4.4, hy - 1.4), (hx - 2.6, hy - 4.6), (hx + 1.0, hy - 5.4), (hx + 3.6, hy - 3.4),
                    (hx + 2.6, hy + 2.0), (hx - 0.4, hy + 4.4)])
    cv.shape(hood, RAG, z=5.0, sd=1.4, hi=0.3, details=cv.fold([(hx - 2.0, hy - 4.0), (hx - 3.0, hy - 0.6), (hx - 2.4, hy + 3.0)], 0.6, 0.9, 1))
    tl_ = [(hx - 3.4, hy - 2.8), (hx - 7.0 - sc * 2, hy - 2.0 + math.sin(ph * 1.6) * 0.8), (hx - 10.0 - sc * 3, hy + 0.4 + math.sin(ph * 1.6 + 1) * 1.2)]
    cv.shape(ik.taper_path([cv.W(q_) for q_ in tl_], cv.u(2.0), (0.2, 0.9)), RAG_B, z=4.8, sd=0.5, ol=0.7)
    mask = cv.blob([(hx - 0.6, hy - 4.2), (hx + 2.6, hy - 4.0), (hx + 4.2, hy - 1.6), (hx + 4.6, hy + 1.4), (hx + 3.6, hy + 3.8, 0.4),
                    (hx + 1.6, hy + 4.8, 0.0), (hx - 0.2, hy + 3.4), (hx - 0.8, hy + 0.0)])
    mdet = [('ink', [(hx + 2.4, hy - 4.0), (hx + 2.0, hy - 2.4), (hx + 2.8, hy - 1.2)], 0.8, (0.1, 0.4)),
            ('ink', [(hx + 4.2, hy + 1.6), (hx + 2.8, hy + 2.2), (hx + 2.4, hy + 3.6), (hx + 1.4, hy + 4.4)], 0.8, (0.1, 0.4)),
            ('ink', [(hx + 1.4, hy + 3.0), (hx + 3.6, hy + 3.2)], 0.7, (0.2, 0.2)),
            ('shade', cv.wedge([(hx - 0.4, hy - 3.6), (hx - 0.8, hy + 0.0), (hx + 0.0, hy + 3.4)], 0.8, -1.0))]
    cv.shape(mask, MASK, z=6.0, sd=1.0, hi=0.45, details=mdet)
    fl = p['flare']
    ey = 0.3 if p['hurt'] > 0.5 else 1.0
    for (q_, rx, ry, rot) in (((hx + 3.2, hy - 0.6), 0.95, 0.42, -0.3), ((hx + 1.2, hy - 0.5), 0.75, 0.36, -0.2), ((hx + 2.4, hy - 2.9), 0.32, 0.85, 0.15)):
        cv.fill(cv.ellipse(q_, rx + 0.35, ry + 0.3, rot), INK, z=6.1)
        yk.eye_glow(cv, q_, rx * (0.85 + 0.3 * fl), ry * (0.8 + 0.4 * fl) * ey, rot, EYE, GLOW, 6.2, halo=2.4, halo_a=0.35 + 0.35 * fl)
    if fl > 0.4:
        cv.stroke([(hx + 3.6, hy - 0.7), (hx + 0.5, hy - 1.5), (hx - 3.0 - fl * 3.0, hy - 2.2 - fl)], 0.9 + 1.2 * fl, z=6.3, col=EYE, taper=(0.1, 0.95),
                  glow=GLOW, alpha=0.85)
    cv.stroke([(hx + 3.8, hy + 1.6), (hx + 2.6, hy + 2.2)], 0.6, z=6.15, col=(1.0, 0.7, 0.3), taper=(0.2, 0.6), glow=(0.6, 0.3, 0.02))   # ışıyan çatlak
    cv.pop()
    out['head'] = yg.world(cv, head)
    # ---- ön kol + orak (ya da boş el / yakalama)
    hft = (hip[0] + p['hf'][0], hip[1] + p['hf'][1])
    has = p['fs'] > 0.5
    e_f, h_f = _arm(cv, sh_f, hft, True, 12.0, p['saf'], grip=has)
    if has:
        bc = _sickle(cv, h_f, p['saf'], True, 14.0, glint=0.5 * fl)
        out['hand'] = yg.world(cv, bc)
    else:
        out['hand'] = yg.world(cv, h_f)
    # ---- savuruş izleri: (el 'f'/'b', a0, a1, k)
    for (wh, a0, a1, k) in p['sm']:
        sh = sh_f if wh == 'f' else sh_b
        hh = h_f if wh == 'f' else h_b
        r = mk.dist(sh, hh) + 8.0
        _smear(cv, sh, r, a0, a1, k, z=24.0 if wh == 'f' else -14.5)
    cv.pop()
    # ---- fırlatılmış orak: dönen hilal + dönüş izi (dünya; gövde dönüşümü yok)
    if p['thr'] > 0.02:
        c = (p['x'] + hip[0] + 6.0 + p['thr'], p['ty'])
        a = p['tsp']
        h_ = add(c, dirv(a + math.pi), 4.5)
        _sickle(cv, h_, a, True, 30.0, glint=1.0)
        for j in range(2):
            rr = 7.0 + j * 1.6
            arc = [(c[0] + math.cos(t) * rr, c[1] + math.sin(t) * rr * 0.85) for t in np.linspace(a + 0.6 + j * 3.1, a + 2.6 + j * 3.1, 7)]
            cv.stroke(arc, 1.6 - j * 0.3, z=29.5, col=(1.0, 0.82, 0.45), taper=(0.9, 0.1), glow=GLOW, alpha=0.85)
            cv.stroke([(q_[0], q_[1] + 0.5) for q_ in arc], 0.8, z=29.4, col=INK, taper=(0.9, 0.1), alpha=0.7)
        u29.speed_lines(cv, c, (1.0, 0.0), n=3, L=8.0, spread=6.0, w=1.2, col=SAND.base, alpha=0.6, z=29.0, seed=3)
        yk.glow_soft(cv, c, 6.0, GLOW, z=29.2, blur=0.7, alpha=0.35)
        out['hand'] = c
    return out


SHADE = dict(outer=0.5, rim=0.6, rim_col=(0.75, 0.8, 1.0), rim_dir=(0.6, -0.8), rim_w=1.3, form=(5.0, (0.76, 0.72, 0.86)))

# ====================================================================== pozlar
G = dict(lean=0.3, hx=0.0, hy=3.0, fb=(-7.0, 0.0), ff=(7.5, 0.0), hb=(-3.0, 1.0), hf=(9.0, -1.0), sab=-1.9, saf=-1.3, hd=(0.4, 0.6))


def _idle(t):
    s = math.sin(t * math.tau)
    s2 = math.sin(t * math.tau * 2)
    p = dict(REST)
    p.update(G)
    p.update(hy=3.0 + 0.8 * s2, lean=0.42 + 0.04 * s, hx=0.6 * s, hb=(-3.0 + 0.6 * s, 1.0 + 0.5 * s2), hf=(9.0 - 0.6 * s, -1.0 + 0.6 * s2),
             saf=-1.3 + 0.15 * s, sab=-1.9 - 0.1 * s, hd=(0.4 + 0.4 * s, 0.6 + 0.3 * s2), sc=0.5 + 0.2 * s, flare=0.3 + 0.2 * max(0.0, s), sk=0.3 * s)
    return p


RUN_S, RUN_D = 25.0, 0.38
_T_RUN = 8 / 14.0


def _rfoot(phi, home):
    phi %= 1.0
    if phi < RUN_D:
        u = phi / RUN_D
        return (home + RUN_S * (0.5 - u), 0.0)
    u = (phi - RUN_D) / (1.0 - RUN_D)
    e = u * u * (3 - 2 * u)
    return (home - RUN_S * 0.5 + RUN_S * e, 7.0 * math.sin(math.pi * u) ** 0.8)


def _move(t):
    c = math.cos(4 * math.pi * (t - RUN_D * 0.5))
    s1 = math.sin(t * math.tau)
    p = dict(REST)
    p.update(G)
    p.update(ff=_rfoot(t, 3.0), fb=_rfoot(t - 0.5, 0.0), hy=3.6 + 1.6 * c, hx=2.0, lean=0.7 + 0.04 * c, hd=(1.2, 1.4),
             hb=(-8.0 - 4.0 * s1, -2.0 + 2.0 * s1), hf=(6.0 + 5.0 * s1, 1.0 - 2.0 * s1), sab=-2.6 - 0.4 * s1, saf=-1.0 + 0.4 * s1,
             sc=1.2, sk=-1.0, flare=0.4, dust=0.4 + 0.2 * c)
    return p


def _k(keys):
    return lambda t: pose_at(t, keys, base=REST)


THROW = [
    (0.0, dict(G), 'io'),
    (0.14, dict(G, hx=-1.0, hy=3.6, lean=0.25, hf=(4.0, -16.0), saf=-2.4, flare=0.5, sc=0.7), 'o'),
    (0.28, dict(G, hx=-3.0, hy=4.4, lean=0.05, fb=(-9.0, 0.0), ff=(7.0, 0.0), hf=(-6.0, -24.0), saf=-3.4, hb=(6.0, -4.0), sab=-1.0,
                hd=(-0.6, 0.0), flare=0.9, sc=0.9, sk=0.8), 'o'),
    (0.42, dict(G, hx=-3.6, hy=4.8, lean=-0.02, fb=(-9.5, 0.0), ff=(7.0, 0.0), hf=(-9.0, -22.0), saf=-3.8, hb=(7.0, -3.0), sab=-0.9,
                hd=(-0.8, -0.2), flare=1.0, sc=1.0, sk=1.0), 'io'),
    (0.5, dict(G, x=2.0, hx=3.0, hy=4.0, lean=0.6, fb=(-11.0, 0.0), ff=(11.0, 0.0), hf=(15.0, -6.0), saf=-0.6, fs=0.0, hb=(-8.0, 0.0), sab=-2.4,
               hd=(1.4, 1.0), flare=1.0, sc=1.3, sk=-1.2, thr=17.0, tsp=0.0, ty=-21.0, sm=(('f', -2.2, -0.35, 1.0),)), 'i'),
    (0.62, dict(G, x=2.0, hx=3.4, hy=4.4, lean=0.66, fb=(-11.0, 0.0), ff=(11.0, 0.0), hf=(13.0, 2.0), saf=-0.3, fs=0.0, hb=(-8.0, 1.0),
                flare=0.7, sc=1.2, sk=-1.0, thr=32.0, tsp=-3.0, ty=-22.0, sm=()), 'l'),
    (0.78, dict(G, x=1.0, hx=1.5, hy=3.6, lean=0.5, fs=0.0, hf=(12.0, -10.0), saf=-1.0, thr=18.0, tsp=-7.0, ty=-24.0, flare=0.5), 'l'),
    (0.9, dict(G, x=0.5, hx=0.6, hy=3.2, fs=1.0, hf=(10.0, -6.0), saf=-1.6, thr=0.0, flare=0.4, catch=1.0), 'o'),
    (1.0, dict(G), 'io'),
]
THROW_TS = [0.0, 0.14, 0.28, 0.42, 0.5, 0.62, 0.78, 0.9]
THROW_MK = [0.42, 0.5, 0.66]

FL_W = dict(G, hx=-2.0, hy=5.0, lean=0.5, fb=(-9.0, 0.0), ff=(6.0, 0.0), hf=(4.0, -12.0), saf=-2.4, hb=(5.0, -13.0), sab=-0.8, flare=1.0, sc=0.9, sk=0.6)
FLURRY = [
    (0.0, dict(G), 'io'),
    (0.15, dict(FL_W, hy=4.0, hf=(6.0, -8.0), hb=(4.0, -9.0), flare=0.6), 'o'),
    (0.3, dict(FL_W), 'io'),
    (0.34, dict(G, x=3.0, hx=2.0, hy=4.0, lean=0.62, fb=(-10.0, 0.0), ff=(10.0, 0.0), hf=(14.0, 6.0), saf=0.2, hb=(4.0, -12.0), sab=-1.0,
                flare=1.0, sc=1.2, sk=-0.8, sm=(('f', -1.8, 0.4, 1.0),)), 'i'),
    (0.44, dict(G, x=5.0, hx=2.5, hy=4.2, lean=0.55, fb=(-9.0, 0.0), ff=(11.0, 0.0), hf=(4.0, 2.0), saf=-1.8, hb=(14.0, 4.0), sab=0.1,
                flare=1.0, sc=1.2, sk=-0.6, sm=(('b', -1.6, 0.35, 1.0),)), 'i'),
    (0.54, dict(G, x=7.0, hx=3.0, hy=3.6, lean=0.5, fb=(-8.0, 0.0), ff=(12.0, 0.0), hf=(15.0, -12.0), saf=-1.9, hb=(2.0, -2.0), sab=-1.5,
                flare=1.0, sc=1.3, sk=-0.8, sm=(('f', 0.8, -0.9, 1.0),)), 'i'),
    (0.64, dict(G, x=9.0, hx=3.0, hy=4.2, lean=0.6, fb=(-9.0, 0.0), ff=(11.0, 0.0), hf=(5.0, 1.0), saf=-1.4, hb=(15.0, -6.0), sab=-0.5,
                flare=1.0, sc=1.3, sk=-0.7, sm=(('b', 0.9, -0.8, 1.0),)), 'i'),
    (0.74, dict(G, x=10.0, hx=3.5, hy=4.6, lean=0.68, fb=(-10.0, 0.0), ff=(12.0, 0.0), hf=(15.0, 4.0), saf=0.3, hb=(13.0, 3.0), sab=0.2,
                flare=1.0, sc=1.2, sk=-0.9, sm=(('f', -1.5, 0.5, 0.9), ('b', -1.3, 0.4, 0.7))), 'i'),
    (0.82, dict(G, x=10.0, hx=2.5, hy=4.0, lean=0.55, fb=(-9.0, 0.0), ff=(11.0, 0.0), hf=(13.0, 2.0), saf=-0.3, hb=(10.0, 1.0), sab=-0.4,
                flare=0.6, sc=1.0, sk=-0.5, sm=()), 'o'),
    (0.92, dict(G, x=5.0, hx=1.0, hy=3.4, flare=0.4), 'io'),
    (1.0, dict(G, x=0.0), 'io'),
]
FLURRY_TS = [0.0, 0.15, 0.3, 0.34, 0.44, 0.54, 0.64, 0.74, 0.82, 0.92]
FLURRY_MK = [0.3, 0.34, 0.82]

TK = dict(fb=(-3.0, 13.0), ff=(2.0, 14.0), hy=-2.0)
FLIP = [
    (0.0, dict(G, hx=-1.0, hy=7.0, lean=0.2, fb=(-6.0, 0.0), ff=(6.0, 0.0), hf=(4.0, -16.0), hb=(-4.0, -16.0), saf=-2.6, sab=-2.8, flare=0.6,
               sc=0.3, dust=0.6), 'o'),
    (0.25, dict(G, **TK, x=-3.0, y=-8.0, roll=-1.7, lean=0.1, hf=(-2.0, -18.0), hb=(-6.0, -18.0), saf=-3.2, sab=-3.4, sc=1.0, dust=0.0), 'o'),
    (0.5, dict(G, **TK, x=-5.0, y=-7.0, roll=-3.4, lean=0.3, hf=(6.0, 0.0), hb=(2.0, 2.0), saf=-1.0, sab=-1.4, sc=1.2), 'l'),
    (0.75, dict(G, x=-4.0, y=-3.0, roll=-5.0, fb=(-4.0, 8.0), ff=(4.0, 6.0), hy=0.0, hf=(9.0, 2.0), hb=(-3.0, 3.0), sc=1.0), 'l'),
    (1.0, dict(G, x=0.0, y=0.0, roll=-6.283, hy=6.0, lean=0.5, fb=(-8.0, 0.0), ff=(7.0, 0.0), sc=0.8, dust=0.8), 'o'),
]

HURT = [
    (0.0, dict(G, x=-2.0, hx=-2.0, hy=4.0, lean=0.05, hd=(-1.2, -0.6), hf=(4.0, -6.0), hb=(-8.0, -4.0), hurt=1.0, flare=1.0, sc=-0.2, sk=1.0), 'l'),
    (0.5, dict(G, x=-3.0, hx=-1.0, hy=3.6, lean=0.25, hd=(-0.4, 0.2), hurt=0.6, flare=0.5, sk=0.5), 'o'),
    (1.0, dict(G, x=-2.0, hurt=0.2), 'o'),
]


def _row(frames, fps, loop, pose, ts=None, mk_=None, vx=None):
    return dict(frames=frames, fps=fps, loop=loop, pose=pose, ts=ts, mk=mk_, vx=vx)


ROWS = None


def anims_for(var='aldaras'):
    global ROWS
    if ROWS is None:
        ROWS = {
            'idle': _row(8, 8, True, _idle),
            'move': _row(8, 14, True, _move, vx=round(RUN_S / (RUN_D * _T_RUN), 1)),
            'hurt': _row(3, 12, False, _k(HURT)),
            'atk_throw': _row(8, 12, False, _k(THROW), ts=THROW_TS, mk_=THROW_MK),
            'atk_flurry': _row(10, 12, False, _k(FLURRY), ts=FLURRY_TS, mk_=FLURRY_MK),
            'flip': _row(5, 12, False, _k(FLIP)),
        }
    return ROWS


def durum_for(var='aldaras'):
    d = mk.durum(('throw', 'flurry'))
    d['evade'] = 'flip'
    return d


def render_frame(anim, i, var='aldaras', ss=3):
    r = anims_for(var)[anim]
    tt = mk.frame_time(r, i)
    p = dict(r['pose'](tt))
    p['ph'] = tt * math.tau * (1 if r['loop'] else 0.7) + (0 if r['loop'] else i * 0.6)
    if not r['loop']:   # anahtar karelerde savuruş izi yalnızca o kareye ait (ara karelerde sönmesin)
        keys = {'atk_throw': THROW, 'atk_flurry': FLURRY}.get(anim)
        if keys is not None:
            p['sm'] = next((d.get('sm', ()) for tk, d, e in keys if abs(tk - tt) < 1e-6), ())
    cv = u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, None, em, info
