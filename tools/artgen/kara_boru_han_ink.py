"""Kara Börü Han — stil v2 "mürekkep-cel" boss (inkkit.py + bosskit.py). v1: creatures2.draw_kara_boru_han.

Erlik Tazılarının hanı: tazının (kara_boru_ink) 2,3 katı, ama daha ağır yapılı bir kurt-ejder: kambur iri omuzlar, kalın
boyun ve dumanlı kara yele (uçları kan koru), derin göğüs, kalın bilekler ve kara pençeler. Sırtından fışkıran
"bozgun kristalleri" (Erlik'in bozgunu; mor-kızıl, ışır, öfkede uzar), böğründe kristal damarları; omuzlarda perçinli
kemik zırh, başında kemik dişli demir han tacı, alnında kemik maske; kan kırmızısı kor gözler ve ağız; boynunda kırık
dev zincirli pranga. Uluma pozunda baş göğe kalkar.

İskelet/pozlar v1 ile aynı (creatures2.KBH_ANIMS: idle 6, run 6, windup 2, leap 2, hurt 2, howl 3, slam 2, rage 2; fps
ve döngü v1 json'undan). Tazı birimleriyle çizilir (k = 4 x 2,3 doku pikseli / tazı birimi): dünya boyu v1 ile aynı.
Çapalar 'mouth' ve 'head' (dünya birimi). Hücre dünya 224x144 (v1 200x144), ayak (100, 138).
"""
import math

import inkkit as ik
from inkkit import Ink, INK
import bosskit as bk
from rig import fk_leg, lerp2, chain
import wolfkit as wk
import creatures  # noqa: F401  (creatures2 döngüsel içe aktarımı için önce)
from creatures2 import KBH_ANIMS

TEX = bk.TEX
SC = 2.3
CELL = (896, 576)       # dünya 224 x 144
FEET = (400, 528)       # dünya (100, 132): alt kenarda pati payı
ANIMS = {k: (v[0], v[1]) for k, v in KBH_ANIMS.items()}

FURK = Ink('#332c42', '#15111e', '#6a5e84', '#0b0912', kind='fur', name='han postu')
FURK_B = Ink('#251f34', '#110d18', '#463c5e', '#08070e', kind='fur', name='uzak post')
SMOKE = Ink('#4a4260', '#1e1a2c', '#7c72a0', name='duman yele')
BONE = Ink('#e0d2ae', '#887454', '#fff8e2', '#56462f', name='kemik')
RUST = Ink('#8a4a30', '#3e1c14', '#c27a4a', name='paslı demir')
IRON = Ink('#585a6a', '#24242e', '#a0a4b8', kind='metal', name='demir')
CLAW = Ink('#2a2630', '#121016', '#6a6474', name='kara tırnak')
CRYS = Ink('#d02a7a', '#5a0e4a', '#ff8ad0', '#2e0628', name='bozgun kristali')
EMBER = (1.0, 0.22, 0.28)
EMBER_HOT = (1.0, 0.75, 0.6)
EMBER_GLOW = (1.0, 0.12, 0.2)
CRYS_GLOW = (0.95, 0.15, 0.6)
CRYS_HOT = (1.0, 0.7, 0.92)
B = 1.16                 # kütle çarpanı (tazıdan daha ağır)


def _leg_ang(hip, a, l1, l2):
    """v29: bacak ya açı (a1, a2) ya da ayak hedefi ('ik', x, y) ile verilir; hedef iki kemik IK ile açıya çevrilir
    (diz / dirsek öne: yere basan pati kaymaz, gövde çökünce bacak bükülür)."""
    if not (isinstance(a, tuple) and len(a) == 3 and a[0] == 'ik'):
        return a
    dx, dy = a[1] - hip[0], a[2] - hip[1]
    d = max(abs(l1 - l2) + 0.05, min(l1 + l2 - 0.02, math.hypot(dx, dy)))
    th = math.atan2(dx, dy)
    al = math.acos(max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    a1 = th + al
    k = (hip[0] + math.sin(a1) * l1, hip[1] + math.cos(a1) * l1)
    tx, ty = hip[0] + math.sin(th) * d, hip[1] + math.cos(th) * d
    return (a1, a1 - math.atan2(tx - k[0], ty - k[1]))


def _hind(hip, a, s=1.0):
    a = _leg_ang(hip, a, 9.0 * s, 10.5 * s)
    _, foot = fk_leg(hip, a[0], a[1], 9.0 * s, 10.5 * s)
    up = wk.norm((hip[0] - foot[0], hip[1] - foot[1]))
    hock = wk.add(foot, wk.rot(up, -0.55), 5.4 * s)
    knee, hock = wk.ik(hip, hock, 7.6 * s, 7.2 * s, -1)
    return knee, hock, foot


def _front(sh, a, s=1.0):
    a = _leg_ang(sh, a, 9.0 * s, 10.0 * s)
    _, foot = fk_leg(sh, a[0], a[1], 9.0 * s, 10.0 * s)
    up = wk.norm((sh[0] - foot[0], sh[1] - foot[1]))
    wrist = wk.add(foot, wk.rot(up, 0.32), 3.2 * s)
    elbow, wrist = wk.ik(sh, wrist, 7.6 * s, 8.4 * s, 1)
    return elbow, wrist, foot


def _paw(cv, f, m, z, near):
    paw = cv.blob([(f[0] - 1.6, f[1] - 2.0), (f[0] + 2.0, f[1] - 2.6), (f[0] + 4.3, f[1] - 1.1), (f[0] + 4.0, f[1] + 0.4, 0.0),
                   (f[0] - 1.4, f[1] + 0.4, 0.0)])
    cv.shape(paw, m, z=z, sd=1.0, hi=0.3 if near else 0.0,
             details=[('ink', [(f[0] + 1.5 + k * 0.9, f[1] - 1.6), (f[0] + 1.9 + k * 0.9, f[1] + 0.2)], 1.0, (0.2, 0.5)) for k in range(2)] if near else ())
    for i in range(3):
        x, y = f[0] + 3.4 + i * 0.35, f[1] - 1.3 + i * 0.6
        cv.shape(cv.blob([(x - 0.5, y - 0.5), (x + 1.9, y + 0.5, 0.0), (x - 0.5, y + 0.45)]), CLAW, z=z + 0.2, sd=0.3, ol=0.6)


def _tufts(pts, ang, length, width, seed=0.0):
    return bk.tufts(pts, ang, length, width, seed)


def _crystal(cv, base, ang, ln, w, z, g):
    """Bozgun kristali: sivri, yüzlü prizma; ışıyan iç damar."""
    d = (math.cos(ang), math.sin(ang))
    n = (-d[1], d[0])
    b0, b1 = bk.add(base, n, w * 0.5), bk.add(base, n, -w * 0.5)
    s0, s1 = bk.add(b0, d, ln * 0.72), bk.add(b1, d, ln * 0.6)
    tip = bk.add(base, d, ln)
    path = cv.blob([b0, s0, (tip[0], tip[1], 0.0), s1, b1])
    det = [('hi', cv.blob([b0, s0, (tip[0], tip[1], 0.0), bk.add(base, d, ln * 0.55)])),
           ('ink', [bk.add(base, d, ln * 0.12), bk.add(base, d, ln * 0.88)], 0.9, (0.2, 0.6))]
    cv.shape(path, CRYS, z=z, sd=w * 0.3, details=det, ol=0.85, soft=0.0)
    cv.fill(cv.blob([bk.add(base, d, ln * 0.25), (tip[0], tip[1], 0.0), bk.add(bk.add(base, d, ln * 0.6), n, -w * 0.18)]), CRYS_HOT,
            z=z + 0.01, glow=tuple(c * g for c in CRYS_GLOW))


def draw(cv, p):
    bob, tilt, jaw = p.get('bob', 0.0), p.get('tilt', 0.0), p.get('jaw', 0.0)
    ph = p.get('ph', 0.0)
    sq = p.get('sq', 0.0)
    rage = p.get('rage', 0.0)
    hy0_ = p.get('hy', 0.0)
    howl = max(0.0, -hy0_ - 3.0) / 4.0          # uluma: baş göğe kalkar (hy -5..-7)
    g = 0.55 + 0.45 * max(rage, jaw * 0.6)
    sqx, sqy = 1.0 + 0.06 * sq, 1.0 - 0.07 * sq
    if sq:
        cv.push(lambda q: (q[0] * sqx, q[1] * sqy))
    # v29: omurga sıkışma / uzama (dörtnala toplanma - açılma): hx kalça, sx omuz yatay kayması
    hipp = (-10.0 + p.get('hx', 0.0), -19.0 + bob - tilt * 6)
    shp = (8.5 + p.get('sx', 0.0), -20.5 + bob + tilt * 6)

    def legs(near):
        z = 8 if near else -8
        m = FURK if near else FURK_B
        hip_j = (hipp[0] + 0.5, hipp[1] + 0.5)
        sh_j = (shp[0] + 0.8, shp[1] + 1.5)
        k, hk, f = _hind(hip_j, p['hf'] if near else p['hb'])
        th = lerp2(hip_j, k, 0.42)
        thigh = ik.union(cv.limb([hip_j, th, k], [5.4 * B if near else 4.6 * B, 5.0 * B if near else 4.4 * B, 2.7 * B]),
                         *[cv.blob(t) for t in _tufts([lerp2(hip_j, k, 0.4), lerp2(hip_j, k, 0.65), lerp2(hip_j, k, 0.85)], math.pi * 0.72, 3.4, 2.2)])
        hind = ik.union(thigh, cv.limb([k, hk, f], [2.7 * B, 1.8 * B, 1.55 * B]),
                        *[cv.blob(t) for t in _tufts([lerp2(k, hk, 0.6), hk], math.pi * 0.85, 2.2, 1.6, 1.0)])
        det = [('ink', [lerp2(hip_j, k, 0.25), lerp2(hip_j, k, 0.55), lerp2(hip_j, k, 0.75)], 1.3)] if near else []
        cv.shape(hind, m, z=z, sd=2.8, hi=0.3 if near else 0.0, details=det, bounce=0.3 if near else 0.0)
        _paw(cv, f, m, z + 0.5, near)
        e, w, f2 = _front(sh_j, p['ff'] if near else p['fb'])
        blade = cv.ellipse(lerp2(sh_j, e, 0.35), 6.2 * B, 4.2 * B, math.atan2(e[1] - sh_j[1], e[0] - sh_j[0]))
        fore = ik.union(blade, cv.limb([sh_j, e, w, f2], [3.9 * B, 2.7 * B, 1.8 * B, 1.55 * B]),
                        *[cv.blob(t) for t in _tufts([lerp2(e, w, 0.1), lerp2(e, w, 0.35)], math.pi * 0.85, 3.0, 1.8)])
        cv.shape(fore, m, z=z + 0.6, sd=2.4, hi=0.3 if near else 0.0, bounce=0.3 if near else 0.0,
                 details=[('ink', [lerp2(sh_j, e, 0.5), lerp2(e, w, 0.2), lerp2(e, w, 0.5)], 1.2, (0.3, 0.5))] if near else ())
        _paw(cv, f2, m, z + 1.0, near)
        if near:   # bilekte demir halka
            cv.shape(cv.ellipse(lerp2(w, f2, 0.1), 2.3, 1.2, math.atan2(f2[1] - w[1], f2[0] - w[0]) + math.pi / 2), IRON, z=z + 1.1, sd=0.5, hi=0.3, ol=0.8)
        return k

    legs(False)
    # ---- kuyruk: kalın kök, dumanlı uçlar (kor)
    tw = p.get('tw', 0.0)
    tl = chain((hipp[0] - 5.0, hipp[1] - 3.5), 6, 3.2, math.pi * 0.92 + tw, -0.12, ph - 0.9, 0.32)
    cv.shape(ik.union(ik.taper_path([cv.W(q) for q in tl], cv.u(5.0), prof=lambda u: max(0.2, 0.55 + 0.6 * math.sin(math.pi * min(1.0, u * 1.3)) - 0.5 * u)),
                       *[cv.blob(t) for t in _tufts(tl[1:6], math.pi * 0.62 + tw, 3.0, 2.0)]), FURK_B, z=-6, sd=1.6, fur=0.8)
    for k_, da in enumerate((-0.35, 0.0, 0.4)):
        tt = chain(tl[-1], 3, 2.4 - abs(da), math.pi * 1.1 + tw * 1.3 + da, -0.1, ph - 1.4 + k_, 0.45)
        cv.shape(ik.taper_path([cv.W(q) for q in [tl[-2]] + tt], cv.u(2.9), (0.0, 0.8)), SMOKE, z=-6.2 + k_ * 0.1, sd=0.8, ol=0.8)
        cv.fill(ik.taper_path([cv.W(q) for q in tt[-2:]], cv.u(1.1), (0.0, 0.9)), EMBER, z=-5.9 + k_ * 0.01, glow=tuple(c * g for c in EMBER_GLOW))
    # ---- gövde: kalça + bel + derin göğüs + kambur omuz (tek kontur)
    body = ik.union(cv.ellipse((hipp[0], hipp[1] - 0.5), 6.6 * B, 6.6 * B),
                    cv.capsule((hipp[0] + 1.5, hipp[1] - 2.4), (shp[0] - 3.0, shp[1] - 0.8), 4.9 * B, 7.0 * B),
                    cv.ellipse((shp[0] + 0.5, shp[1] + 1.6), 8.2 * B, 9.0 * B, -0.18),
                    cv.ellipse((shp[0] - 2.5, shp[1] - 5.0), 7.2 * B, 4.4 * B, -0.1))
    bp = [lerp2((hipp[0] + 3.0, hipp[1] + 1.8), (shp[0] - 2.0, shp[1] + 8.0), t) for t in (0.15, 0.4, 0.65, 0.85)]
    belly = [cv.blob(t) for t in _tufts(bp, math.pi * 0.7, 3.0, 2.0)]
    chest = [cv.blob(t) for t in _tufts([(shp[0] + 7.5, shp[1] + 2.0), (shp[0] + 7.0, shp[1] + 5.5), (shp[0] + 5.0, shp[1] + 9.0), (shp[0] + 2.0, shp[1] + 10.6)],
                                        math.pi * 0.38, 3.2, 2.2)]
    body = ik.union(body, *belly, *chest)
    rdet = []
    for i in range(4):
        cx = shp[0] - 4.6 + i * 2.4
        pts = [(cx - 0.6, shp[1] - 1.0), (cx + 0.3, shp[1] + 2.6), (cx + 0.2, shp[1] + 6.0 - i * 0.4)]
        rdet.append(('stroke', [(q[0] - 0.5, q[1]) for q in pts], 1.6, FURK.hi, (0.4, 0.4)))
        rdet.append(('ink', pts, 1.3, (0.4, 0.4)))
    rdet += cv.fold([(hipp[0] + 2.0, hipp[1] - 3.0), (hipp[0] + 5.0, hipp[1] + 0.5), (hipp[0] + 4.6, hipp[1] + 3.6)], 0.8, 1.3, 1)
    # yara izleri (tazı ağzı, Bengü'nün atalarının kılıcı)
    s0, s1 = (hipp[0] + 6.0, hipp[1] - 3.0), (hipp[0] + 11.0, hipp[1] + 2.5)
    rdet.append(('stroke', [s0, lerp2(s0, s1, 0.5), s1], 1.8, (0.55, 0.4, 0.6), (0.2, 0.2)))
    cv.shape(body, FURK, z=0, sd=4.6, hi=0.45, details=rdet, bounce=0.35, hatch=0.3)
    # böğürde kristal damarları (ışıyan çatlaklar)
    vein = [(hipp[0] + 3.0, hipp[1] - 1.0), (hipp[0] + 7.0, hipp[1] + 0.8), (hipp[0] + 10.5, hipp[1] - 0.6), (shp[0] - 4.0, shp[1] + 1.8)]
    bk.crack_glow(cv, vein, 1.6, CRYS_HOT, tuple(c * g * 0.8 for c in CRYS_GLOW), 0.5, branch=0.6, seed=2.0)
    # leğen kemiği plakası
    hx0, hy0 = hipp
    cv.shape(cv.blob([(hx0 - 3.6, hy0 - 5.6), (hx0 + 1.8, hy0 - 7.2), (hx0 + 3.2, hy0 - 5.4, 0.0), (hx0 - 1.8, hy0 - 4.0)]), BONE.darker(0.85), z=10, sd=1.0, hi=0.3,
             details=[('ink', [(hx0 - 2.5, hy0 - 5.0), (hx0 + 1.5, hy0 - 6.0)], 0.9)])
    # ---- bozgun kristalleri: sırt boyunca (öfkede uzar)
    for k_, (t, h, a) in enumerate(((0.02, 9.0, -1.9), (0.2, 13.0, -1.75), (0.38, 15.5, -1.6), (0.56, 13.5, -1.45), (0.74, 10.5, -1.3), (0.9, 7.0, -1.2))):
        bx, by = lerp2(hipp, shp, t)
        r_t = 6.4 * B + 0.8 * t - 6.0 * t * (1 - t)
        by = by - r_t + 1.6
        hh = h * (0.85 + 0.55 * rage) + math.sin(ph + k_) * 0.4
        _crystal(cv, (bx, by), a - tilt * 0.4, hh, 3.6 + h * 0.12, 9.0 + k_ * 0.02, g)
        if k_ % 2 == 0:   # yan küçük kristal
            _crystal(cv, (bx - 1.6, by + 0.8), a - 0.55, hh * 0.45, 2.2, 8.9 + k_ * 0.02, g * 0.8)
    # ---- omuz kemik zırhı (perçinli)
    sp = (shp[0] + 0.5, shp[1] - 5.5)
    armor = cv.blob([(sp[0] - 6.5, sp[1] + 1.5), (sp[0] - 4.0, sp[1] - 2.4), (sp[0] + 2.5, sp[1] - 3.2), (sp[0] + 6.5, sp[1] - 0.8),
                     (sp[0] + 6.0, sp[1] + 2.4), (sp[0] + 0.5, sp[1] + 3.6), (sp[0] - 5.0, sp[1] + 3.4)])
    adet = [('ink', [(sp[0] - 4.0, sp[1] + 0.2), (sp[0] + 0.5, sp[1] - 1.0), (sp[0] + 5.0, sp[1] + 0.4)], 1.0, (0.15, 0.15))]
    adet += [('col', cv.ellipse((sp[0] - 3.5 + k * 3.5, sp[1] + 2.0 - k * 0.2), 0.55, 0.55), IRON.hi) for k in range(3)]
    cv.shape(armor, BONE, z=11, sd=1.6, hi=0.45, details=adet, cast=0.8)
    # ---- dumanlı yele: boyun üstünden geriye, uçları kan koru
    for k_ in range(8):
        t = k_ / 7
        bx, by = lerp2((shp[0] - 5, shp[1] - 7.4), (shp[0] + 7.5, shp[1] - 9.5 + hy0_ * (0.4 + 0.3 * howl)), t)
        ang = math.pi * 1.15 + math.sin(ph - 0.8 + k_ * 1.3) * 0.16 + p.get('mane', 0.0) - howl * 0.3
        L = 7.5 + (k_ % 2) * 3.4 - t * 2.0
        st = chain((bx, by), 4, L / 4, ang, 0.16, ph - 0.8 + k_, 0.25)
        cv.shape(ik.taper_path([cv.W(q) for q in st], cv.u(3.0), (0.15, 0.85)), SMOKE, z=6.0 + k_ * 0.1, sd=0.9, hi=0.3, ol=0.75)
        if k_ % 2:
            cv.fill(ik.taper_path([cv.W(q) for q in st[-2:]], cv.u(1.5), (0.0, 0.9)), EMBER, z=6.05 + k_ * 0.1, glow=tuple(c * g for c in EMBER_GLOW))

    # ---- boyun + baş (uluma: baş boyun kökü etrafında göğe döner)
    head = (shp[0] + 9.5 + p.get('hdx', 0.0), shp[1] - 5.5 + hy0_ * (1.0 - 0.6 * howl))
    nb = (shp[0] + 2, shp[1] - 3)
    ang_h = -0.75 * howl + p.get('hp', 0.0)     # v29 hp: baş eğimi (+ burun aşağı, - göğe)
    if ang_h:
        cah, sah = math.cos(ang_h), math.sin(ang_h)
        piv = nb
        cv.push(lambda q: (piv[0] + (q[0] - piv[0]) * cah - (q[1] - piv[1]) * sah, piv[1] + (q[0] - piv[0]) * sah + (q[1] - piv[1]) * cah))
    hx_, hy_ = head
    ear = p.get('ear', 0.0) + math.sin(ph - 1.2) * 0.12
    for (ox, m, zz, ln) in ((-2.8, FURK_B, 7.6, 6.6), (-0.8, FURK, 15.0, 7.0)):
        e0 = (hx_ + ox, hy_ - 3.0)
        a = -math.pi * 0.5 - 0.5 - ear
        tip = (e0[0] + math.cos(a) * ln, e0[1] + math.sin(a) * ln)
        det = []
        if m is FURK:
            det = [('col', cv.blob([(e0[0] - 0.8, e0[1] + 0.4), (e0[0] + 0.9, e0[1]), (lerp2(e0, tip, 0.65)[0], lerp2(e0, tip, 0.65)[1], 0.0)]), (0.45, 0.1, 0.16))]
        cv.shape(cv.blob([(e0[0] - 2.2, e0[1] + 1.0), (tip[0], tip[1], 0.0), (e0[0] + 2.2, e0[1] + 0.2)]), m, z=zz, sd=1.4, details=det)
    sn = (hx_ + 9.6, hy_ + 2.1)
    jd = jaw * 4.0
    j1 = (hx_ + 8.4, hy_ + 4.4 + jd)
    mouth = cv.blob([(hx_ + 2.5, hy_ + 2.2), (sn[0] - 0.5, sn[1] + 0.9), (j1[0], j1[1] - 0.6), (hx_ + 2.5, hy_ + 3.6 + jd * 0.4)])
    cv.fill(mouth, (0.62, 0.08, 0.12), z=7.0, glow=tuple(c * 0.45 * g for c in EMBER_GLOW))
    if jaw > 0.15:
        for i in range(4):
            x = hx_ + 4.0 + i * 1.6
            cv.fill(cv.blob([(x - 0.45, hy_ + 2.2), (x + 0.45, hy_ + 2.2), (x, hy_ + 3.5 - (0.0 if i else -0.6), 0.0)]), BONE.base, z=7.2)
            x2 = hx_ + 4.4 + i * 1.4
            yb = hy_ + 2.8 + jd * (0.55 + i * 0.12) + 0.6
            cv.fill(cv.blob([(x2 - 0.4, yb), (x2 + 0.4, yb), (x2, yb - 1.1 - (0.6 if i == 0 else 0.0), 0.0)]), BONE.base, z=7.2)
    cv.shape(cv.limb([(hx_ + 1.6, hy_ + 3.2), j1], [2.1, 1.1]), FURK_B, z=7.5, sd=0.8)
    for k, (x, ln) in enumerate(((hx_ + 7.6, 2.4), (hx_ + 5.4, 1.8))):   # hep görünen üst azı dişleri
        cv.shape(cv.blob(bk.spike_pts((x - 0.55, hy_ + 2.3), (x + 0.55, hy_ + 2.3), (x + 0.15, hy_ + 2.3 + ln), 0.2)), BONE, z=9.0 + k * 0.01,
                 sd=0.3, ol=0.75)
    neck = cv.capsule(nb, head, 5.8 * B, 4.3 * B)
    ruff = [cv.blob(t) for t in _tufts([(hx_ - 2.5, hy_ + 3.2), (hx_ - 4.6, hy_ + 1.4), (hx_ - 0.8, hy_ + 4.2), (hx_ - 6.0, hy_ - 0.8)],
                                         math.pi * 0.72, 3.6, 2.6)]
    skull = cv.ellipse((hx_ - 0.3, hy_), 6.0, 5.2, -0.1)
    snout = cv.capsule((hx_ + 1.8, hy_ + 0.4), sn, 3.9, 2.4)
    headp = ik.union(neck, skull, snout, *ruff)
    hdet = [('ink', [(hx_ + 3.0, hy_ + 2.2), (hx_ + 7.0, hy_ + 2.5), (sn[0] - 0.4, sn[1] + 0.8)], 1.4, (0.1, 0.5)),
            ('ink', [(hx_ + 5.0, hy_ - 1.6), (hx_ + 7.0, hy_ - 0.9)], 1.0, (0.3, 0.3)),
            ('ink', [(hx_ + 4.6, hy_ - 0.8), (hx_ + 6.6, hy_ - 0.1)], 1.0, (0.3, 0.3))]
    cv.shape(headp, FURK, z=8, sd=2.8, hi=0.45, details=hdet, cast=0.8, bounce=0.3)
    # kemik maske: alın + burun sırtı, gözü çevreler
    cv.shape(cv.blob([(hx_ - 2.6, hy_ - 4.6), (hx_ + 2.6, hy_ - 5.2), (hx_ + 5.6, hy_ - 3.0, 0.0), (hx_ + 8.6, hy_ - 1.2, 0.0), (hx_ + 5.4, hy_ - 1.9),
                      (hx_ + 1.4, hy_ - 2.9), (hx_ - 1.8, hy_ - 2.6)]),
             BONE, z=14, sd=1.3, hi=0.4, details=[('ink', [(hx_ - 1.2, hy_ - 3.8), (hx_ + 0.6, hy_ - 2.2)], 1.0),
                                                   ('ink', [(hx_ + 4.0, hy_ - 2.4), (hx_ + 6.5, hy_ - 1.3)], 0.9)])
    # han tacı: demir halka + kemik dişler
    crown_c = (hx_ - 1.0, hy_ - 4.6)
    cv.shape(cv.blob([(crown_c[0] - 4.2, crown_c[1] + 0.8), (crown_c[0] - 3.6, crown_c[1] - 0.9), (crown_c[0] + 3.8, crown_c[1] - 1.4),
                      (crown_c[0] + 4.4, crown_c[1] + 0.2), (crown_c[0] - 0.2, crown_c[1] + 0.9)]), IRON, z=14.5, sd=0.7, hi=0.4, ol=0.9)
    for k in range(4):
        ox = crown_c[0] - 3.0 + k * 2.2
        hh = 4.2 + (1.6 if k == 1 else 0.0) - k * 0.3
        b0, b1 = (ox - 0.8, crown_c[1] - 0.6), (ox + 0.8, crown_c[1] - 0.8)
        cv.shape(cv.blob(bk.spike_pts(b0, b1, (ox - 0.6, crown_c[1] - 0.7 - hh), -0.3)), BONE, z=14.4 - k * 0.01, sd=0.6, hi=0.3, ol=0.85)
    cv.fill(cv.ellipse((crown_c[0] + 0.4, crown_c[1] - 0.2), 0.6, 0.6), CRYS_HOT, z=14.6, glow=tuple(c * g for c in CRYS_GLOW))
    cv.shape(cv.ellipse((sn[0] + 0.4, sn[1] - 0.2), 1.3, 1.1), Ink('#1a1820', '#0c0b10', '#5a5866'), z=24, sd=0.4, hi=0.2, ol=0.7)
    # göz: kemik maskenin içinde kan koru
    cv.fill(cv.ellipse((hx_ + 2.4, hy_ - 1.2), 2.3, 1.5), INK, z=24)
    cv.fill(cv.blob([(hx_ + 0.6, hy_ - 1.0, 0.0), (hx_ + 2.6, hy_ - 2.1), (hx_ + 4.4, hy_ - 0.8, 0.0), (hx_ + 2.4, hy_ - 0.4)]), EMBER, z=28,
            glow=tuple(c * g for c in EMBER_GLOW))
    cv.fill(cv.ellipse((hx_ + 2.9, hy_ - 1.15), 0.55, 0.45), EMBER_HOT, z=28.1, glow=tuple(c * g for c in EMBER_HOT))
    # pranga + kırık dev zincir
    dx, dy = head[0] - nb[0], head[1] - nb[1]
    ln_ = math.hypot(dx, dy) + 1e-6
    nx, ny = -dy / ln_, dx / ln_
    cc = lerp2(nb, head, 0.42)
    rr = 5.4 * B
    a0 = (cc[0] - nx * rr, cc[1] - ny * rr)
    a1 = (cc[0] + nx * rr, cc[1] + ny * rr)
    cv.shape(cv.blob([a0, (cc[0] + dx * 0.1, cc[1] + dy * 0.1), a1, (cc[0] - dx * 0.14, cc[1] - dy * 0.14)]), RUST, z=16, sd=1.0, hi=0.35,
             details=[('col', cv.ellipse((cc[0] + nx * rr * s_, cc[1] + ny * rr * s_), 0.6, 0.6), IRON.hi) for s_ in (-0.4, 0.1, 0.6)])
    for k in range(3):   # yakada sivri demir dikenler
        q0 = (cc[0] + nx * rr * (-0.6 + k * 0.6), cc[1] + ny * rr * (-0.6 + k * 0.6))
        cv.shape(cv.blob(bk.spike_pts((q0[0] - dx * 0.05, q0[1] - dy * 0.05), (q0[0] + dx * 0.05, q0[1] + dy * 0.05),
                                      (q0[0] - dx * 0.5 + nx, q0[1] - dy * 0.5 + ny))), IRON, z=15.9, sd=0.5, ol=0.8)
    if ang_h:
        cv.pop()
    sw = math.sin(ph - 0.6) * 0.35 + tilt * 1.5 + p.get('chain', 0.0)
    q = a1 if not ang_h else (nb[0] + (a1[0] - nb[0]) * math.cos(ang_h) - (a1[1] - nb[1]) * math.sin(ang_h),
                              nb[1] + (a1[0] - nb[0]) * math.sin(ang_h) + (a1[1] - nb[1]) * math.cos(ang_h))
    for i in range(4):
        nq = (q[0] + math.sin(sw - i * 0.15) * 2.4, q[1] + math.cos(sw - i * 0.15) * 2.4)
        m = IRON if i % 2 == 0 else RUST
        cv.shape(cv.ellipse(lerp2(q, nq, 0.5), 1.2 if i % 2 == 0 else 0.9, 1.6 if i % 2 == 0 else 1.4,
                            math.atan2(nq[1] - q[1], nq[0] - q[0]) + math.pi / 2), m, z=17 + i, sd=0.5, hi=0.3, ol=0.8)
        q = nq
    legs(True)
    if sq:
        cv.pop()
    # çapalar (dünya birimi; tazı birimi x 2,3), uluma dönüşü dahil
    def R(pt):
        if not ang_h:
            return pt
        return (nb[0] + (pt[0] - nb[0]) * math.cos(ang_h) - (pt[1] - nb[1]) * math.sin(ang_h),
                nb[1] + (pt[0] - nb[0]) * math.sin(ang_h) + (pt[1] - nb[1]) * math.cos(ang_h))
    mo = R((hx_ + 9.6, hy_ + 2.8 + jd * 0.5))
    hd = R(head)
    return {'mouth': (mo[0] * sqx * SC, mo[1] * sqy * SC), 'head': (hd[0] * sqx * SC, hd[1] * sqy * SC)}


SHADE = dict(outer=0.65, rim=0.9, rim_col=(0.75, 0.72, 1.0), rim_dir=(0.55, -0.85), rim_w=1.8, form=(4.0, (0.72, 0.7, 0.86)))


def render_frame(anim, i, ss=3):
    if anim in CLIPS:
        p = CLIPS[anim]['fn'](i)
    else:
        n, fn = ANIMS[anim]
        p = fn(i / n)
    cv = bk.new_canvas(CELL, FEET, ss, k=TEX * SC)
    xf = bk.body_xf(cv, p, unit=SC)
    info = draw(cv, p)
    if xf:
        cv.pop()
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, bk.xf_info(info, xf, unit=SC)


from kara_boru_han_v29 import CLIPS  # noqa: E402  v29 tam gövde animasyonları
