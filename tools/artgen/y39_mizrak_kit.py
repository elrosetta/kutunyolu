"""v39: mızraklı (AI lancer) yaratıkların ortak iskeleti — Tunga Hayaleti (y39_tunga_hayaleti) ve Erlik Yasavulu
(y39_yasavul) bu dosyayı paylaşır.

İçerik:
  * iskelet çözümü (solve): kalça + eğik gövde (bekci_ink T(u, v) kalıbı), omuzlar, AYAK HEDEFLİ bacaklar (ik2),
    iki elle tutulan uzun sap: arka el (uzak kol) sapı tutar, ön el (yakın kol) sap üzerinde erişebildiği en yakın
    noktayı kavrar (sap elin içinden kayar: "sl"); tek el kipinde (fırlatma) sap uzak elde dik durur, yakın el serbest.
  * çizim sırası (draw): arka pelerin / kuyruklar, uzak kol, sap, bacaklar, gövde, baş, yakın kol, cirit, efektler.
    Malzeme ve parça çizimleri yaratık modülündeki S (stil) nesnesinden gelir.
  * efektler: hilal savuruş izi (smear_arc), hız çizgileri, toplanan zerreler.
  * ortak poz tabloları (rows): idle 8, move 8, hurt 3, atk_lunge 9, atk_sweep 8, atk_throw 8 (mk'li). Modüller
    idle / move'u kendi döngüleriyle değiştirebilir.
Koordinat: dünya birimi, ayak orijini (0, 0), x sağ +, y aşağı +; yaratık SAĞA bakar.
"""
import math

import numpy as np

import inkkit as ik
from inkkit import INK
from rig import lerp2
import yaratik_govde as yg
import yaratik_ink_kit as yk
import ucan_v29 as u29
from ucan_v29 import pose_at

L_UP, L_FO = 10.0, 9.5       # kol
REACH = L_UP + L_FO - 0.4
GRIP = 11.0                  # iki el arası (sap boyunca, varsayılan)


# ------------------------------------------------------------ küçük geometri
def along(a, b, t, off=0.0):
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1.0
    return (a[0] + dx * t - dy / d * off, a[1] + dy * t + dx / d * off)


def dirv(a):
    return (math.cos(a), math.sin(a))


def add(p, v, k=1.0):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


# ------------------------------------------------------------ efektler
def smear_arc(cv, c, r, a0, a1, w, col, glow, z, alpha=0.85, ink=True, hot=None):
    """Hilal savuruş izi: c çevresinde a0 -> a1 yayı (a1 = silahın şimdiki açısı). İz a1'de kalın, a0'a doğru incelir."""
    n = 18
    outer, inner = [], []
    for i in range(n + 1):
        u = i / n
        a = a0 + (a1 - a0) * u
        ww = w * (u ** 0.8)
        outer.append((c[0] + math.cos(a) * (r + ww * 0.35), c[1] + math.sin(a) * (r + ww * 0.35)))
        inner.append((c[0] + math.cos(a) * (r - ww * 0.65), c[1] + math.sin(a) * (r - ww * 0.65)))
    path = cv.poly(outer + inner[::-1])
    cv.fill(path, col, z=z, glow=glow, alpha=alpha)
    if hot is not None:   # sıcak çekirdek çizgisi (dış kenara yakın)
        cv.stroke([(c[0] + math.cos(a0 + (a1 - a0) * u) * (r + w * 0.15 * u), c[1] + math.sin(a0 + (a1 - a0) * u) * (r + w * 0.15 * u))
                   for u in np.linspace(0.25, 1.0, 9)], 1.6, z=z + 0.05, col=hot, taper=(0.9, 0.1), glow=glow)
    if ink:   # kuru fırça: dış kenarda incelen mürekkep çizgisi, içte iki kıl izi
        cv.stroke(outer[4:], 1.3, z=z + 0.1, col=INK, taper=(0.95, 0.05), alpha=0.9)
        for k, f in enumerate((0.45, 0.8)):
            pts = [(c[0] + math.cos(a0 + (a1 - a0) * u) * (r - w * f * u), c[1] + math.sin(a0 + (a1 - a0) * u) * (r - w * f * u))
                   for u in np.linspace(0.35 + 0.15 * k, 1.0, 7)]
            cv.stroke(pts, 0.9, z=z + 0.1, col=INK, taper=(0.9, 0.2), alpha=0.6)
    yk.glow_soft(cv, (c[0] + math.cos(a1) * r * 0.9, c[1] + math.sin(a1) * r * 0.9), w * 1.6, glow, z=z - 0.1, blur=0.7, alpha=0.5)


def streaks(cv, c, d, k, col, glow, z=-40.0, seed=0, spread=22.0, L=22.0, n=7):
    if k <= 0.02:
        return
    u29.speed_lines(cv, c, d, n=n, L=L * k, spread=spread, w=1.8, col=col, alpha=0.75 * min(1.0, k), z=z, seed=seed, glow=glow)
    u29.speed_lines(cv, (c[0], c[1] + 2.0), d, n=4, L=L * 0.7 * k, spread=spread * 0.8, w=1.2, col=INK, alpha=0.5 * min(1.0, k),
                    z=z - 0.1, seed=seed + 7)


# ------------------------------------------------------------ iskelet
REST = dict(x=0.0, y=0.0, bob=0.0, hx=0.0, hy=0.0, lean=0.08, tw=0.0, hd=(0.0, 0.0), hrot=0.0, roll=0.0,
            fb=(-6.0, 0.0), ff=(6.0, 0.0), mode=0.0, gh=(8.0, -9.0), la=-0.6, sl=0.0, hf=(10.0, -14.0),
            jav=0.0, ja=-0.2, jt=0.0, jp=(14.0, -40.0), jfa=-0.05, smear=0.0, sa0=-1.2, sa1=0.0, streak=0.0, flare=0.0,
            mist=0.0, cw=0.0, sk=0.0, hurt=0.0, burn=0.0, anc=0.0, fl=0.0)


def solve(p, S):
    """Poz -> eklemler (dünya). S: stil (H0 kalça yüksekliği, TORSO, L_TH / L_SH, LIFT, LANCE (geri, ileri))."""
    lift = S.LIFT
    base = (p['x'], p['y'] + p['bob'])
    hip = (base[0] + p['hx'], base[1] - S.H0 - lift + p['hy'])
    lean = p['lean']
    up = (math.sin(lean), -math.cos(lean))
    fw = (math.cos(lean), math.sin(lean))

    def T(u, v):
        return (hip[0] + up[0] * u + fw[0] * v, hip[1] + up[1] * u + fw[1] * v)
    J = dict(hip=hip, T=T, up=up, fw=fw)
    tl = S.TORSO
    J['neck'] = T(tl + 0.5, 0.8)
    J['head'] = (J['neck'][0] + 1.4 + up[0] * 4.5 + p['hd'][0], J['neck'][1] + up[1] * 4.5 - 1.0 + p['hd'][1])
    J['sh_b'] = T(tl - 2.6, -2.6 + p['tw'] * 4.0)
    J['sh_f'] = T(tl - 2.4, 2.2 - p['tw'] * 2.0)
    # bacaklar: ayak hedefi (x, yerden yükseklik); LIFT süzülme payı
    J['hb'] = (hip[0] - 1.6, hip[1])
    J['hf'] = (hip[0] + 1.6, hip[1])
    fbt = (p['fb'][0] + p['x'], -p['fb'][1] - lift + p['y'] * 0.0)
    fft = (p['ff'][0] + p['x'], -p['ff'][1] - lift + p['y'] * 0.0)
    J['kb'], J['fbt'] = yg.ik2(J['hb'], fbt, S.L_TH, S.L_SH, -1)
    J['kf'], J['fft'] = yg.ik2(J['hf'], fft, S.L_TH, S.L_SH, -1)
    # sap / kollar
    back, front = S.LANCE
    la = p['la']
    d = dirv(la)
    J['d'] = d
    one = p['mode'] > 0.5
    gh_t = (hip[0] + p['gh'][0], hip[1] + p['gh'][1])
    e_b, h_b = yg.ik2(J['sh_b'], gh_t, L_UP, L_FO, 1 if not one else 1)
    J['e_b'], J['h_b'] = e_b, h_b
    sl = p['sl']
    J['butt'] = add(h_b, d, -(back + sl))
    J['tip'] = add(h_b, d, front - sl)
    if not one:
        # ön el: sap üzerinde, GRIP'e en yakın erişilebilir nokta
        best, bs = None, 1e9
        for s in np.linspace(2.5, min(34.0, front - sl - 6.0), 64):
            q = add(h_b, d, s)
            if dist(q, J['sh_f']) <= REACH:
                if abs(s - GRIP) < bs:
                    bs, best = abs(s - GRIP), q
        if best is None:
            best = min((add(h_b, d, s) for s in np.linspace(2.5, 30.0, 40)), key=lambda q: dist(q, J['sh_f']))
        J['e_f'], J['h_f'] = yg.ik2(J['sh_f'], best, L_UP, L_FO, 1)
    else:
        hf_t = (hip[0] + p['hf'][0], hip[1] + p['hf'][1])
        bend = -1 if hf_t[1] < J['sh_f'][1] - 4 else 1     # kol yukarıdayken dirsek geride / aşağıda
        J['e_f'], J['h_f'] = yg.ik2(J['sh_f'], hf_t, L_UP, L_FO, bend)
    return J


def draw(cv, p, S):
    """Bütün figür. Döner: çapalar {'hand': ..., 'head': ...} (dünya)."""
    yg.bake_xf(cv)
    q = dict(REST)
    q.update(p)
    p = q
    ph = p['ph']
    out = {}
    # ---- dünya efektleri (dönüşümsüz)
    J0 = solve(p, S)
    if p['streak'] > 0.02:
        streaks(cv, (J0['hip'][0] - 6.0, J0['hip'][1] - 10.0), (1.0, 0.0), p['streak'], S.STREAK, S.GLOW, seed=int(ph * 7) % 50)
    S.ground_fx(cv, p, J0)
    yg.xf_push(cv, (J0['hip'][0], J0['hip'][1]), p['roll'])
    J = J0
    S.back_layer(cv, p, J)                       # pelerin, sis kuyrukları, sırttaki parçalar
    # ---- uzak kol (omuz arkada; el sapı tutar)
    one = p['mode'] > 0.5
    S.arm(cv, J['sh_b'], J['e_b'], J['h_b'], near=False, z_up=-20.0, z_lo=-19.0 if one else 10.5, grip=True, d=J['d'])
    # ---- sap
    lz = -18.0 if one else 12.0
    S.weapon(cv, p, J, J['butt'], J['tip'], lz)
    # ---- bacaklar + gövde + baş
    S.legs(cv, p, J)
    S.torso(cv, p, J)
    yg.xf_push(cv, J['neck'], p['hrot'])
    S.head(cv, p, J, J['head'])
    out['head'] = yg.world(cv, J['head'])
    cv.pop()
    # ---- yakın kol
    S.arm(cv, J['sh_f'], J['e_f'], J['h_f'], near=True, z_up=20.0, z_lo=21.0, grip=not one or p['jav'] > 0.05,
          d=dirv(p['ja']) if one else J['d'])
    tip_w = yg.world(cv, J['tip'])
    out['tip'] = tip_w
    # ---- cirit (yakın elde) / fırlatılmış cirit
    jtip = None
    if one and p['jav'] > 0.02:
        jd = dirv(p['ja'])
        jtip = S.javelin(cv, add(J['h_f'], jd, -6.0), p['ja'], p['jav'], 22.0, ph, flying=False)
    if p['jt'] > 0.02:
        o = (J['hip'][0] + p['jp'][0] + p['jt'], J['hip'][1] + p['jp'][1] + p['jt'] * math.tan(p['jfa']))
        jtip = S.javelin(cv, o, p['jfa'], 1.0, 24.0, ph, flying=True, trail=min(1.0, p['jt'] / 10.0))
    if p['smear'] > 0.02:
        r = dist(J['h_b'], J['tip'])
        S.smear(cv, J['h_b'], r, p['sa0'], p['sa1'], p['smear'])
    cv.pop()
    if p['anc'] > 0.5 and jtip is not None:
        out['hand'] = yg.world(cv, jtip)
    elif p['anc'] > 0.5:
        out['hand'] = yg.world(cv, J['h_f'])
    else:
        out['hand'] = tip_w
    return out


# ====================================================================== ortak poz tabloları
# Duruş: kargı göğüs önünde çapraz (uç yukarı-ileri), ağırlık arka ayakta. Her saldırı ayaktan başlar.
G = dict(lean=0.1, hx=0.0, hy=0.6, fb=(-7.0, 0.0), ff=(6.0, 0.0), gh=(5.0, -10.0), la=-0.72, sl=0.0, tw=0.0,
         hd=(0.2, 0.3), hrot=0.0, flare=0.2)


def _k(keys, base):
    return lambda t: pose_at(t, keys, base=base)


def idle_pose(t, base):
    s = math.sin(t * math.tau)
    s2 = math.sin(t * math.tau * 2)
    p = dict(base)
    p.update(G)
    p.update(bob=0.6 * s, hy=0.6 + 0.4 * s2, lean=0.1 + 0.02 * s2, la=-0.72 + 0.03 * s, gh=(5.0, -10.0 + 0.4 * s),
             hd=(0.2 + 0.2 * s, 0.3 + 0.2 * s2), flare=0.25 + 0.15 * max(0.0, s), cw=0.2 + 0.15 * s, sk=0.4 * s)
    return p


LUNGE = [
    (0.0, dict(G), 'io'),
    (0.12, dict(G, hx=-1.5, hy=1.5, lean=0.0, gh=(1.0, -8.5), la=-0.35, sl=2.0, tw=-0.2, flare=0.4, cw=0.4, mist=0.3), 'o'),
    (0.24, dict(hx=-4.0, hy=3.0, lean=-0.14, fb=(-10.0, 0.0), ff=(6.0, 0.0), gh=(-6.0, -6.5), la=-0.08, sl=4.0, tw=-0.5,
                hd=(-0.8, 0.6), flare=0.7, cw=0.6, mist=0.6, sk=0.8), 'o'),
    (0.36, dict(hx=-5.5, hy=4.0, lean=-0.22, fb=(-11.5, 0.0), ff=(6.5, 0.0), gh=(-10.0, -5.5), la=0.02, sl=5.0, tw=-0.7,
                hd=(-1.2, 0.8), flare=1.0, cw=0.8, mist=0.9, sk=1.0), 'o'),
    (0.46, dict(hx=-6.0, hy=4.3, lean=-0.24, fb=(-12.0, 0.0), ff=(6.5, 0.0), gh=(-11.0, -5.5), la=0.03, sl=5.0, tw=-0.75,
                hd=(-1.3, 0.9), flare=1.0, cw=0.9, mist=1.0, sk=1.1), 'io'),
    (0.52, dict(x=4.0, hx=5.0, hy=3.0, lean=0.42, fb=(-14.0, 0.0), ff=(15.0, 0.0), gh=(9.0, -9.0), la=-0.02, sl=4.0, tw=0.6,
                hd=(1.6, 1.4), flare=1.0, cw=1.4, mist=0.2, sk=-1.4, streak=1.0), 'i'),
    (0.62, dict(x=5.0, hx=5.5, hy=3.2, lean=0.46, fb=(-14.5, 0.0), ff=(16.0, 0.0), gh=(9.0, -8.6), la=0.0, sl=4.5, tw=0.65,
                hd=(1.8, 1.5), flare=0.9, cw=1.5, mist=0.0, sk=-1.6, streak=0.7), 'o'),
    (0.76, dict(x=4.0, hx=3.5, hy=2.4, lean=0.3, fb=(-12.0, 0.0), ff=(13.0, 0.0), gh=(8.0, -9.0), la=-0.25, sl=2.0, tw=0.3,
                hd=(1.0, 0.8), flare=0.5, cw=0.9, sk=-0.6, streak=0.0), 'io'),
    (0.88, dict(x=3.0, hx=1.5, hy=1.2, lean=0.16, fb=(-9.0, 0.0), ff=(9.0, 0.0), gh=(7.0, -9.5), la=-0.55, sl=0.0, tw=0.1,
                hd=(0.4, 0.4), flare=0.3, cw=0.4, sk=0.0), 'io'),
    (1.0, dict(G, x=0.0), 'io'),
]
LUNGE_TS = [0.0, 0.12, 0.24, 0.36, 0.46, 0.52, 0.62, 0.76, 0.88]
LUNGE_MK = [0.46, 0.52, 0.76]

# ---- savuruş: kargı omuz üstüne kalkar (uç yukarı, el baş hizasında), sonra yukarıdan öne geniş yay
SWEEP = [
    (0.0, dict(G), 'io'),
    (0.14, dict(G, hx=-1.0, hy=1.4, lean=0.0, gh=(1.0, -15.0), la=-0.9, sl=8.0, tw=-0.3, flare=0.4, cw=0.4), 'o'),
    (0.28, dict(hx=-3.5, hy=2.4, lean=-0.18, fb=(-10.0, 0.0), ff=(5.0, 0.0), gh=(-3.0, -18.0), la=-1.0, sl=15.0, tw=-0.7,
                hd=(-0.8, 0.0), hrot=-0.08, flare=0.8, cw=0.7, sk=0.8, mist=0.5), 'o'),
    (0.42, dict(hx=-4.5, hy=2.8, lean=-0.26, fb=(-10.5, 0.0), ff=(5.0, 0.0), gh=(-5.0, -19.0), la=-1.1, sl=18.0, tw=-0.85,
                hd=(-1.0, -0.2), hrot=-0.1, flare=1.0, cw=0.9, sk=1.0, mist=0.9), 'io'),
    (0.5, dict(x=3.0, hx=3.5, hy=3.0, lean=0.34, fb=(-12.0, 0.0), ff=(12.0, 0.0), gh=(11.0, -14.0), la=0.12, sl=2.0, tw=0.6,
               hd=(1.2, 1.0), hrot=0.08, flare=1.0, cw=1.2, sk=-1.2, smear=1.0, sa0=-0.8, sa1=0.12, mist=0.0), 'i'),
    (0.6, dict(x=4.0, hx=4.5, hy=3.6, lean=0.42, fb=(-12.5, 0.0), ff=(13.0, 0.0), gh=(12.0, -9.0), la=0.5, sl=0.0, tw=0.8,
               hd=(1.5, 1.4), hrot=0.1, flare=0.8, cw=1.3, sk=-1.4, smear=0.85, sa0=-0.45, sa1=0.5), 'o'),
    (0.74, dict(x=3.0, hx=2.5, hy=2.4, lean=0.28, fb=(-11.0, 0.0), ff=(11.0, 0.0), gh=(9.0, -8.0), la=0.35, sl=0.0, tw=0.4,
                hd=(0.8, 0.8), hrot=0.04, flare=0.4, cw=0.8, sk=-0.6, smear=0.0), 'io'),
    (0.87, dict(x=1.0, hx=1.0, hy=1.2, lean=0.15, fb=(-8.0, 0.0), ff=(8.0, 0.0), gh=(6.0, -9.5), la=-0.35, sl=0.0, tw=0.1,
                hd=(0.3, 0.4), flare=0.3, cw=0.4, sk=0.0), 'io'),
    (1.0, dict(G, x=0.0), 'io'),
]
SWEEP_TS = [0.0, 0.14, 0.28, 0.42, 0.5, 0.6, 0.74, 0.87]
SWEEP_MK = [0.42, 0.5, 0.72]

# ---- fırlatma: kargı uzak elde dik (dipçik yerde), yakın elde ışıktan cirit belirir; kol başın arkasına kurulur,
# öne savrulur; cirit elden çıkar (el boş), uçar; toparlanma
TH0 = dict(mode=1.0, gh=(-5.0, -11.0), la=-1.5, sl=20.0, anc=1.0)
GT = dict(G, **TH0)
THROW = [
    (0.0, dict(GT, hf=(9.0, -12.0), jav=0.15, ja=-0.1, lean=0.08), 'io'),
    (0.14, dict(GT, hx=-1.0, hy=1.0, lean=0.0, hf=(4.0, -26.0), jav=0.55, ja=-0.25, tw=-0.3, flare=0.5, mist=0.4), 'o'),
    (0.28, dict(TH0, hx=-3.5, hy=2.4, lean=-0.2, fb=(-10.5, 0.0), ff=(6.5, 0.0), hf=(-11.0, -27.0), jav=0.9, ja=-0.16, tw=-0.8,
                hd=(-0.8, 0.0), hrot=-0.06, flare=0.9, cw=0.6, sk=0.8, mist=0.8), 'o'),
    (0.42, dict(TH0, hx=-4.5, hy=2.8, lean=-0.28, fb=(-11.0, 0.0), ff=(7.0, 0.0), hf=(-14.0, -26.0), jav=1.0, ja=-0.14, tw=-0.95,
                hd=(-1.0, -0.2), hrot=-0.08, flare=1.0, cw=0.8, sk=1.0, mist=1.0), 'io'),
    (0.5, dict(TH0, x=2.0, hx=4.0, hy=2.6, lean=0.36, fb=(-12.0, 0.0), ff=(12.0, 0.0), hf=(16.0, -27.0), jav=0.0, ja=-0.1, tw=0.7,
               hd=(1.4, 1.0), hrot=0.06, flare=1.0, cw=1.2, sk=-1.2, jt=4.0, jp=(18.0, -30.0), jfa=-0.06, mist=0.0, streak=0.0), 'i'),
    (0.6, dict(TH0, x=3.0, hx=5.0, hy=3.0, lean=0.44, fb=(-12.5, 0.0), ff=(13.0, 0.0), hf=(17.0, -16.0), jav=0.0, tw=0.8,
               hd=(1.6, 1.4), hrot=0.08, flare=0.8, cw=1.3, sk=-1.4, jt=30.0, jp=(18.0, -30.0), jfa=-0.06), 'l'),
    (0.74, dict(TH0, x=2.0, hx=2.5, hy=2.0, lean=0.26, fb=(-11.0, 0.0), ff=(10.0, 0.0), hf=(11.0, -12.0), jav=0.0, tw=0.3,
                hd=(0.8, 0.8), flare=0.4, cw=0.8, sk=-0.6, jt=0.0), 'io'),
    (0.87, dict(GT, x=0.5, hx=0.5, hy=1.0, lean=0.12, hf=(9.0, -11.0), jav=0.1, ja=-0.1, flare=0.3, cw=0.4), 'io'),
    (1.0, dict(GT, x=0.0, hf=(9.0, -12.0), jav=0.15), 'io'),
]
THROW_TS = [0.0, 0.14, 0.28, 0.42, 0.5, 0.6, 0.74, 0.87]
THROW_MK = [0.42, 0.5, 0.7]

HURT = [
    (0.0, dict(G, x=-2.5, hx=-3.0, hy=2.0, lean=-0.3, gh=(0.0, -12.0), la=-0.88, tw=-0.4, hd=(-1.4, -0.4), hrot=-0.22, hurt=1.0,
               flare=1.0, cw=-0.6, sk=1.2, roll=-0.06), 'l'),
    (0.5, dict(G, x=-3.5, hx=-1.6, hy=1.6, lean=-0.1, gh=(3.0, -11.0), la=-0.85, tw=-0.2, hd=(-0.4, 0.4), hrot=-0.08, hurt=0.6,
               flare=0.5, cw=-0.2, sk=0.6, roll=-0.02), 'o'),
    (1.0, dict(G, x=-2.0, hurt=0.2), 'o'),
]


def row(frames, fps, loop, pose, ts=None, mk=None, vx=None):
    return dict(frames=frames, fps=fps, loop=loop, pose=pose, ts=ts, mk=mk, vx=vx)


def rows(base, idle=None, move=None, move_vx=None, tweak=None):
    """Satır tablosu. tweak(keys) -> keys: modül pozları kendi bedenine uydurabilir (ör. ağır yasavul daha alçak)."""
    tw = tweak or (lambda k: k)
    return {
        'idle': row(8, 8, True, idle or (lambda t: idle_pose(t, base))),
        'move': row(8, 10, True, move, vx=move_vx),
        'hurt': row(3, 12, False, _k(tw(HURT), base)),
        'atk_lunge': row(9, 12, False, _k(tw(LUNGE), base), ts=LUNGE_TS, mk=LUNGE_MK),
        'atk_sweep': row(8, 12, False, _k(tw(SWEEP), base), ts=SWEEP_TS, mk=SWEEP_MK),
        'atk_throw': row(8, 12, False, _k(tw(THROW), base), ts=THROW_TS, mk=THROW_MK),
    }


def durum(moves):
    d = {"idle": "idle", "chase": "move", "recover": "idle", "evade": "move",
         "_hurt": "hurt", "_hurt_big": "hurt", "_break": "hurt"}
    for m in moves:
        for s in ('windup', 'act', 'recover'):
            d['%s/%s' % (s, m)] = 'atk_' + m
    return d


def frame_time(r, i):
    if r['ts']:
        return r['ts'][i]
    if r['loop']:
        return i / r['frames']
    return i / max(1, r['frames'] - 1)
