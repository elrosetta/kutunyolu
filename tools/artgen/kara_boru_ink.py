"""Erlik Tazısı (kimlik kara_boru) — stil v2 "mürekkep-cel" (inkkit.py). v1: creatures.draw_hound.

v29 tam gövde animasyonu (docs/TASARIM.md "v29: yer yaratıklarının tam gövde animasyonu"): iskelet artık AYAK HEDEFLİ —
dört pençenin yerdeki / havadaki yeri yazılır, arka bacak (uyluk-baldır-tarak) ve ön bacak (kürek-kol-ön kol-tarak) IK ile
çözülür; gövde kalça ile omuz arasında eğilir (pitch), bükülür (flex: dörtnalda toplanma / gerilme), sırt kamburlaşır
(arch); baş boyun dibinde döner (hr) ve önden gider; kuyruk, yele, tasma zinciri ikincil harekettir. Bütün figür ayak
noktası çevresinde devrilebilir (roll: savrulma, ölüm). Kareler yaratik_govde.Seq ile anahtar pozlardan üretilir.

Hücre 320x224 doku pikseli = dünya 80x56 (texel 4), ayak (36, 52). Satırlar (SEQS) ve yapay zekâ eşlemesi (DURUM):
lunger / stalker / crawler / pouncer (ayaz_kurdu, yek, kirkayak, sicrayan_tazi, magara_pususu, kor_pususu da bu sayfayı
kullanır).
"""
import math

import inkkit as ik
from inkkit import Ink, INK
from rig import lerp2, chain
import wolfkit as wk
import yaratik_govde as yg
import yaratik_ink_kit as yk
from yaratik_govde import Seq, wave

TEX = 4.0
CELL = (320, 224)       # dünya 80 x 56 (texel 4)
FEET = (144, 208)

FURK = Ink('#3a3548', '#181522', '#68607e', '#0e0c16', kind='fur', name='tazı postu')
FURK_B = Ink('#2a2440', '#14111e', '#433c5c', '#0b0a12', kind='fur', name='uzak post')
SMOKE = Ink('#5a5470', '#262236', '#8a84a6', name='duman yele')
BONE = Ink('#e2d6b4', '#8c7c5c', '#fffbe8', '#5a4c38', name='kemik')
RUST = Ink('#9a5a34', '#4a2416', '#d08a52', name='paslı zincir')
IRON = Ink('#5e6070', '#2a2a36', '#a0a4b8', kind='metal', name='demir')
CLAW = Ink('#d8ccb0', '#7a6c52', '#ffffff', name='tırnak')
EMBER = (1.0, 0.56, 0.16)
EMBER_HOT = (1.0, 0.86, 0.45)
EMBER_GLOW = (1.0, 0.45, 0.08)

C0 = (-0.75, -19.75)          # gövde merkezi (kalça-omuz ortası), dünya
HIP0 = (-10.0, -19.0)
SH0 = (8.5, -20.5)
GROUND = -0.4                 # pençe noktası (taban 0,4 aşağıda yere değer)
R_HIND = 19.6                 # kalça -> pençe azami erim
R_FRONT = 18.6

# dinlenme pozu: hf/hb yakın/uzak arka, ff/fb yakın/uzak ön pençe (x, yerden yükseklik, parmak kıvrımı rad)
REST = dict(x=0.0, y=0.0, pitch=0.0, flex=0.0, arch=0.0, roll=0.0,
            hf=(-13.6, 0.0, 0.0), hb=(-11.2, 0.0, 0.0), ff=(9.8, 0.0, 0.0), fb=(12.0, 0.0, 0.0),
            hd=(0.0, 0.0), hr=0.0, jaw=0.1, lip=0.0, ear=0.0, eye=0.0, mane=0.0, hack=0.0,
            tw=0.0, tl=0.0, ph=0.0, chain=0.0, sq=0.0, br=0.0, blink=0.0, tongue=0.0, dust=0.0, snap=0.0)


def _reach(base, f, r):
    dx, dy = f[0] - base[0], f[1] - base[1]
    d = math.hypot(dx, dy)
    if d > r:
        return (base[0] + dx / d * r, base[1] + dy / d * r)
    return f


def _hind_t(hip, f, s=1.0):
    f = _reach(hip, f, R_HIND * s)
    up = wk.norm((hip[0] - f[0], hip[1] - f[1]))
    hock = wk.add(f, wk.rot(up, -0.55), 5.4 * s)
    knee, hock = wk.ik(hip, hock, 7.6 * s, 7.2 * s, -1)
    return knee, hock, f


def _front_t(sh, f, s=1.0):
    f = _reach(sh, f, R_FRONT * s)
    up = wk.norm((sh[0] - f[0], sh[1] - f[1]))
    wrist = wk.add(f, wk.rot(up, 0.32), 3.2 * s)
    elbow, wrist = wk.ik(sh, wrist, 7.6 * s, 8.4 * s, 1)
    return elbow, wrist, f


def _paw(cv, f, m, z, ang=0.0):
    ca, sa = math.cos(ang), math.sin(ang)

    def R(x, y, *r):
        dx, dy = x - f[0], y - f[1]
        return (f[0] + dx * ca - dy * sa, f[1] + dx * sa + dy * ca) + r
    paw = cv.blob([R(f[0] - 1.2, f[1] - 1.6), R(f[0] + 2.0, f[1] - 2.2), R(f[0] + 3.9, f[1] - 0.9), R(f[0] + 3.6, f[1] + 0.4, 0.0),
                   R(f[0] - 1.0, f[1] + 0.4, 0.0)])
    cv.shape(paw, m, z=z, sd=0.9, hi=0.3)
    for i in range(2):
        x, y = f[0] + 3.5 + i * 0.2, f[1] - 0.9 + i * 0.8
        cv.shape(cv.blob([R(x - 0.4, y - 0.5), R(x + 1.5, y + 0.4, 0.0), R(x - 0.4, y + 0.4)]), CLAW, z=z + 0.2, sd=0.3, ol=0.6)


def _tufts(pts, ang, length, width):
    """Dışa uzanan sivri tutam üçgenleri (dünya noktaları listesi -> çokgen noktaları listesi)."""
    out = []
    for i, (x, y) in enumerate(pts):
        a = ang + math.sin(i * 2.3 + x * 0.1) * 0.25
        ln = length * (0.78 + 0.22 * math.cos(i * 1.7))
        tip = (x + math.cos(a) * ln, y + math.sin(a) * ln)
        nx_, ny_ = -math.sin(a) * width * 0.5, math.cos(a) * width * 0.5
        out.append([(x + nx_, y + ny_), (tip[0], tip[1], 0.0), (x - nx_, y - ny_)])
    return out


def draw(cv, p):
    yg.bake_xf(cv)
    q = dict(REST)
    q.update(p)
    p = q
    tilt, jaw = 0.0, p['jaw']
    ph = p['ph']
    sq = p['sq']
    flex, arch, pitch = p['flex'], p['arch'], p['pitch']
    sqx, sqy = 1.0 + 0.06 * sq, 1.0 - 0.07 * sq
    # bütün figür: öteleme + devrilme (ayak noktası çevresinde değil, gövde merkezinde; ölüm / savrulma)
    yg.xf_push(cv, C0, p['roll'], p['x'], p['y'])
    if sq:
        cv.push(lambda q_: (q_[0] * sqx, q_[1] * sqy))
    # gövde yerel çerçevesi: kalça / omuz (flex: aradaki mesafe kısalır, arch: sırt kamburu)
    hipp = (HIP0[0] + flex * 0.5, HIP0[1] + arch * 0.4)
    shp = (SH0[0] - flex * 0.5, SH0[1] + arch * 0.2)

    def B(pt):   # gövde yereli -> figür çerçevesi (pitch)
        return yg.rot_about(pt, C0, pitch)
    hip_j = B((hipp[0] + 0.5, hipp[1] + 0.5))
    sh_j = B((shp[0] + 0.8, shp[1] + 1.5))
    # figür çerçevesindeki ayak hedefleri: dünya ayak hedefi figür dönüşümünün TERSİYLE (roll/x/y) çerçeveye alınır, böylece
    # roll = 0 iken yazılan dünya konumu aynen kalır
    def F(t):
        w = (t[0], GROUND - t[1])
        w = (w[0] - p['x'], w[1] - p['y'])
        return yg.rot_about(w, C0, -p['roll'])

    def legs(near):
        z = 8 if near else -8
        m = FURK if near else FURK_B
        hf = p['hf'] if near else p['hb']
        k, hk, f = _hind_t(hip_j, F(hf))
        th = lerp2(hip_j, k, 0.42)
        tdir = math.atan2(k[1] - hip_j[1], k[0] - hip_j[0])
        thigh = ik.union(cv.limb([hip_j, th, k], [4.6 if near else 4.0, 4.4 if near else 3.8, 2.3]),
                         cv.blob([q_ for t in _tufts([lerp2(hip_j, k, 0.5), lerp2(hip_j, k, 0.8)], tdir + math.pi * 0.25, 3.0, 2.0) for q_ in t]))
        hind = ik.union(thigh, cv.limb([k, hk, f], [2.3, 1.5, 1.3]))
        cv.shape(hind, m, z=z, sd=2.6, hi=0.3 if near else 0.0,
                 details=[('ink', [lerp2(hip_j, k, 0.25), lerp2(hip_j, k, 0.55), lerp2(hip_j, k, 0.75)], 1.2)] if near else ())
        _paw(cv, f, m, z + 0.5, hf[2] + p['roll'] * 0.0)
        ff = p['ff'] if near else p['fb']
        e, w, f2 = _front_t(sh_j, F(ff))
        blade = cv.ellipse(lerp2(sh_j, e, 0.35), 5.0, 3.4, math.atan2(e[1] - sh_j[1], e[0] - sh_j[0]))
        fdir = math.atan2(w[1] - e[1], w[0] - e[0])
        fore = ik.union(blade, cv.limb([sh_j, e, w, f2], [3.2, 2.2, 1.45, 1.3]),
                        cv.blob(_tufts([lerp2(e, w, 0.15)], fdir + math.pi * 0.35, 2.6, 1.6)[0]))
        cv.shape(fore, m, z=z + 0.6, sd=2.2, hi=0.3 if near else 0.0)
        _paw(cv, f2, m, z + 1.0, ff[2])
        if near:
            cv.shape(cv.ellipse(k, 1.2, 1.2), BONE, z=z + 1.2, sd=0.6, hi=0.3, ol=0.8)

    legs(False)
    # ---- gövde yereli (pitch)
    yg.xf_push(cv, C0, pitch)
    # kuyruk: kalın kök, dumanlı uçlar; tl kaldırır (-), tw salınım
    tw = p['tw']
    tl = chain((hipp[0] - 4.5, hipp[1] - 3.2), 5, 3.0, math.pi * 0.92 + tw - p['tl'], -0.12, ph - 0.9, 0.32)
    cv.shape(ik.union(ik.taper_path([cv.W(q_) for q_ in tl], cv.u(4.2), prof=lambda u: max(0.2, 0.55 + 0.6 * math.sin(math.pi * min(1.0, u * 1.3)) - 0.5 * u)),
                       *[cv.blob(t) for t in _tufts(tl[1:5], math.pi * 0.62 + tw - p['tl'], 2.6, 1.8)]), FURK_B, z=-6, sd=1.4)
    for k_, da in enumerate((-0.35, 0.0, 0.4)):
        tt = chain(tl[-1], 3, 2.2 - abs(da), math.pi * 1.1 + (tw - p['tl']) * 1.3 + da, -0.1, ph - 1.4 + k_, 0.45)
        cv.shape(ik.taper_path([cv.W(q_) for q_ in [tl[-2]] + tt], cv.u(2.6), (0.0, 0.8)), SMOKE, z=-6.2 + k_ * 0.1, sd=0.8, ol=0.8)
        if k_ == 1:
            cv.fill(ik.taper_path([cv.W(q_) for q_ in tt[-2:]], cv.u(1.0), (0.0, 0.9)), EMBER, z=-5.9, glow=EMBER_GLOW)
    # gövde: kalça + bel + derin göğüs + omuz tümseği (tek kontur); br = nefes (göğüs şişer)
    br = p['br']
    mid = lerp2(hipp, shp, 0.5)
    body = ik.union(cv.ellipse((hipp[0], hipp[1] - 0.5), 6.0, 6.2),
                    cv.capsule((hipp[0] + 1.5, hipp[1] - 2.4 - arch * 0.6), (shp[0] - 3.0, shp[1] - 0.8 - arch * 0.3), 4.3 + arch * 0.15, 6.4),
                    cv.ellipse((mid[0], mid[1] - 3.2 - arch * 1.1), 5.2, 3.0 + max(0.0, arch) * 0.3, 0.0),
                    cv.ellipse((shp[0] + 0.5, shp[1] + 1.8), 7.4 + br * 0.4, 8.3 + br * 0.5, -0.18),
                    cv.ellipse((shp[0] - 2.5, shp[1] - 4.6), 6.0, 3.4))
    bp = [lerp2((hipp[0] + 3.0, hipp[1] + 1.6), (shp[0] - 2.0, shp[1] + 7.0 + br * 0.4), t) for t in (0.15, 0.45, 0.75)]
    belly = [cv.blob(t) for t in _tufts(bp, math.pi * 0.7, 2.6, 1.8)]
    chest = [cv.blob(t) for t in _tufts([(shp[0] + 6.5, shp[1] + 2.0), (shp[0] + 6.0, shp[1] + 5.5), (shp[0] + 4.0, shp[1] + 8.4 + br * 0.4)], math.pi * 0.35, 2.8, 2.0)]
    body = ik.union(body, *belly, *chest)
    rdet = []
    for i in range(4):
        cx = shp[0] - 4.2 + i * 2.2
        pts = [(cx - 0.6, shp[1] - 1.0), (cx + 0.3, shp[1] + 2.4), (cx + 0.2, shp[1] + 5.4 - i * 0.4 + br * 0.3)]
        rdet.append(('stroke', [(q_[0] - 0.5, q_[1]) for q_ in pts], 1.6, FURK.hi, (0.4, 0.4)))
        rdet.append(('ink', pts, 1.3, (0.4, 0.4)))
    rdet += cv.fold([(hipp[0] + 2.0, hipp[1] - 3.0), (hipp[0] + 5.0, hipp[1] + 0.5), (hipp[0] + 4.6, hipp[1] + 3.6)], 0.8, 1.3, 1)
    cv.shape(body, FURK, z=0, sd=4.2, hi=0.45, details=rdet, hatch=0.0)
    # leğen kemiği plakası + omur plakaları (hack: tüyler diken diken -> plakalar dikilir)
    hack = p['hack']
    hx0, hy0 = hipp
    cv.shape(cv.blob([(hx0 - 4.0, hy0 - 4.6), (hx0 + 2.5, hy0 - 6.6), (hx0 + 3.8, hy0 - 4.4, 0.0), (hx0 - 1.8, hy0 - 2.8)]), BONE, z=10, sd=1.0, hi=0.3)
    for k_ in range(5):
        t = 0.16 + k_ * 0.17
        bx, by = lerp2(hipp, shp, t)
        r_t = 6.4 + 0.8 * t - 6.0 * t * (1 - t) + arch * 1.1 * math.sin(math.pi * t)
        by = by - r_t + 1.4
        h = (2.6 + (1.0 if k_ in (2, 3) else 0.0)) * (1.0 + 0.35 * hack)
        lean = -0.6 * hack
        cv.shape(cv.blob([(bx - 1.7, by + 1.0, 0.0), (bx + 1.2, by + 1.0, 0.0), (bx - 0.3 + lean, by - h, 0.0), (bx - 1.5 + lean, by - h + 1.0)]), BONE, z=9, sd=0.6, hi=0.25, ol=0.85)
    # ---- baş grubu: boyun dibinde döner (hr: + aşağı), önden gider (hd)
    hdx, hdy = p['hd']
    nb = (shp[0] + 2, shp[1] - 3)
    head = (shp[0] + 9.5 + hdx, shp[1] - 5.5 + hdy)
    # dumanlı yele: omuzdan başa; hack ile uzar ve dikleşir
    mane_end = yg.rot_about((head[0] - 2.5, head[1] - 3.5), nb, p['hr'])
    for k_ in range(6):
        t = k_ / 5
        bx, by = lerp2((shp[0] - 4, shp[1] - 6.6), mane_end, t)
        ang = math.pi * 1.15 + math.sin(ph - 0.8 + k_ * 1.3) * 0.16 + p['mane'] + hack * 0.35
        L = (6.5 + (k_ % 2) * 3.0 - t * 2.0) * (1.0 + 0.45 * hack)
        st = chain((bx, by), 4, L / 4, ang, 0.16 - hack * 0.08, ph - 0.8 + k_, 0.25)
        cv.shape(ik.taper_path([cv.W(q_) for q_ in st], cv.u(2.6 + hack * 0.5), (0.15, 0.85)), SMOKE, z=11 + k_ * 0.3, sd=0.9, hi=0.3, ol=0.75)
        if k_ % 2 or hack > 0.5:
            cv.fill(ik.taper_path([cv.W(q_) for q_ in st[-2:]], cv.u(1.4 + hack * 0.4), (0.0, 0.9)), EMBER, z=11.1 + k_ * 0.3, glow=EMBER_GLOW)
    neck = cv.capsule(nb, yg.rot_about(head, nb, p['hr']), 5.0, 3.9)
    yg.xf_push(cv, nb, p['hr'])
    hx_, hy_ = head
    ear = p['ear'] + math.sin(ph - 1.2) * 0.12
    for (ox, m, zz, ln) in ((-2.6, FURK_B, 7.6, 6.4), (-0.6, FURK, 15.0, 6.8)):
        e0 = (hx_ + ox, hy_ - 2.8)
        a = -math.pi * 0.5 - 0.45 - ear
        tip = (e0[0] + math.cos(a) * ln, e0[1] + math.sin(a) * ln)
        det = []
        if m is FURK:
            det = [('col', cv.blob([(e0[0] - 0.8, e0[1] + 0.4), (e0[0] + 0.9, e0[1]), (lerp2(e0, tip, 0.65)[0], lerp2(e0, tip, 0.65)[1], 0.0)]), (0.55, 0.16, 0.08))]
        cv.shape(cv.blob([(e0[0] - 2.0, e0[1] + 1.0), (tip[0], tip[1], 0.0), (e0[0] + 2.0, e0[1] + 0.2)]), m, z=zz, sd=1.4, details=det)
    sn = (hx_ + 9.0, hy_ + 1.9 - p['lip'] * 0.5)
    jd = jaw * 3.6
    jang = jaw * 0.32
    j1 = yg.rot_about((hx_ + 8.0, hy_ + 4.0), (hx_ + 1.6, hy_ + 3.0), jang)
    jm = yg.rot_about((hx_ + 5.0, hy_ + 3.6), (hx_ + 1.6, hy_ + 3.0), jang)
    mouth = cv.blob([(hx_ + 2.5, hy_ + 2.0), (sn[0] - 0.5, sn[1] + 0.9), (j1[0], j1[1] - 0.6), (jm[0], jm[1] - 0.2), (hx_ + 2.5, hy_ + 3.4 + jd * 0.2)])
    cv.fill(mouth, (0.85, 0.32, 0.08), z=7.0, glow=(0.42, 0.13, 0.02))
    if p['tongue'] > 0.05:
        tq = [lerp2((hx_ + 3.0, hy_ + 3.2), j1, 0.3), lerp2((hx_ + 3.0, hy_ + 3.6), j1, 0.8),
              (j1[0] + 1.2 * p['tongue'], j1[1] + 2.0 * p['tongue'])]
        cv.shape(cv.limb(tq, [0.9, 0.8, 0.6]), Ink('#b84a3a', '#6a1e1a', '#e88870'), z=7.1, sd=0.4, ol=0.6)
    if jaw > 0.15 or p['lip'] > 0.2:
        for i in range(3):
            x = hx_ + 4.6 + i * 1.8
            ln_t = 1.1 + (0.5 if i == 2 else 0.0) * (1 + p['lip'])
            cv.fill(cv.blob([(x - 0.45, hy_ + 2.0), (x + 0.45, hy_ + 2.0), (x, hy_ + 2.0 + ln_t, 0.0)]), BONE.base, z=7.2)
            if jaw > 0.15:
                x2 = lerp2((hx_ + 4.0, 0), (j1[0] - 0.6, 0), 0.25 + i * 0.3)[0]
                yb = lerp2(jm, j1, 0.2 + i * 0.35)[1] - 0.2
                cv.fill(cv.blob([(x2 - 0.4, yb), (x2 + 0.4, yb), (x2, yb - 1.0 - (0.4 if i == 0 else 0.0), 0.0)]), BONE.base, z=7.2)
    cv.shape(cv.limb([(hx_ + 1.6, hy_ + 3.0), jm, j1], [1.9, 1.5, 1.0]), FURK_B, z=7.5, sd=0.8)
    ruff = [cv.blob(t) for t in _tufts([(hx_ - 2.5, hy_ + 2.8), (hx_ - 4.2, hy_ + 1.2), (hx_ - 0.8, hy_ + 3.6)], math.pi * 0.72, 3.0, 2.2)]
    skull = cv.ellipse((hx_ - 0.3, hy_), 5.5, 4.8, -0.1)
    snout = cv.capsule((hx_ + 1.8, hy_ + 0.4), sn, 3.6, 2.2)
    headp = ik.union(skull, snout, *ruff)
    hdet = [('ink', [(hx_ + 3.0, hy_ + 2.0), (hx_ + 7.0, hy_ + 2.3), (sn[0] - 0.4, sn[1] + 0.8)], 1.4, (0.1, 0.5))]
    if p['lip'] > 0.15:   # hırlama: burun kırışıkları
        for i in range(3):
            x = hx_ + 3.8 + i * 1.5
            hdet.append(('ink', [(x, hy_ - 0.2 - i * 0.15), (x + 0.7, hy_ + 0.6), (x + 0.3, hy_ + 1.3)], 0.9 + p['lip'] * 0.5, (0.3, 0.5)))
    cv.pop()
    cv.shape(neck, FURK, z=8, sd=2.6, hi=0.45, cast=0.8)
    yg.xf_push(cv, nb, p['hr'])
    cv.shape(headp, FURK, z=8.1, sd=2.6, hi=0.45, details=hdet, cast=0.8)
    cv.shape(cv.blob([(hx_ - 2.8, hy_ - 4.0), (hx_ + 2.8, hy_ - 4.6), (hx_ + 5.0, hy_ - 2.2, 0.0), (hx_ + 0.4, hy_ - 1.5), (hx_ - 2.2, hy_ - 1.8)]),
             BONE, z=14, sd=1.2, hi=0.35, details=[('ink', [(hx_ - 1.0, hy_ - 3.6), (hx_ + 0.4, hy_ - 2.2)], 1.0)])
    cv.shape(cv.ellipse((sn[0] + 0.4, sn[1] - 0.2), 1.2, 1.0), Ink('#1a1820', '#0c0b10', '#5a5866'), z=24, sd=0.4, hi=0.2, ol=0.7)
    # göz: kara çukur içinde kor (eye: "!!" alevlenmesi; blink: kısılma / acı)
    ey = p['eye']
    bl = p['blink']
    cv.fill(cv.ellipse((hx_ + 2.2, hy_ - 1.1), 2.2, 1.45), INK, z=24)
    if bl < 0.9:
        hgt = (1.0 - bl)
        cv.fill(cv.blob([(hx_ + 0.8 - ey * 0.4, hy_ - 1.0, 0.0), (hx_ + 2.4, hy_ - 1.0 - 0.8 * hgt - ey * 0.3), (hx_ + 3.8 + ey * 0.5, hy_ - 0.8, 0.0),
                         (hx_ + 2.2, hy_ - 1.0 + 0.6 * hgt)]), EMBER_HOT, z=28, glow=EMBER_GLOW)
        if ey > 0.05:
            yk.glow_soft(cv, (hx_ + 2.4, hy_ - 1.1), 2.2 + 2.0 * ey, EMBER_GLOW, z=29, blur=0.6, alpha=0.5 * ey)
            cv.stroke([(hx_ + 3.6, hy_ - 1.0), (hx_ + 3.6 - 4.0 * ey, hy_ - 1.6 - 0.6 * ey)], 1.0 + ey, z=28.5, col=EMBER, taper=(0.1, 0.9), glow=EMBER_GLOW)
    # kırık zincirli tasma
    dx, dy = head[0] - nb[0], head[1] - nb[1]
    ln_ = math.hypot(dx, dy) + 1e-6
    nx, ny = -dy / ln_, dx / ln_
    cc = lerp2(nb, head, 0.5)
    a0 = (cc[0] - nx * 4.6, cc[1] - ny * 4.6)
    a1 = (cc[0] + nx * 4.6, cc[1] + ny * 4.6)
    cv.shape(cv.blob([a0, (cc[0] + dx * 0.08, cc[1] + dy * 0.08), a1, (cc[0] - dx * 0.12, cc[1] - dy * 0.12)]), RUST, z=16, sd=0.9, hi=0.35,
             details=[('col', cv.ellipse((cc[0] + nx * 4.6 * s_, cc[1] + ny * 4.6 * s_), 0.55, 0.55), IRON.hi) for s_ in (-0.25, 0.25, 0.75)])
    sw = math.sin(ph - 0.6) * 0.35 + p['chain'] - pitch - p['hr'] - p['roll']
    q_ = a1
    for i in range(3):
        nq = (q_[0] + math.sin(sw - i * 0.15) * 2.0, q_[1] + math.cos(sw - i * 0.15) * 2.0)
        m = IRON if i % 2 == 0 else RUST
        cv.shape(cv.ellipse(lerp2(q_, nq, 0.5), 1.0 if i % 2 == 0 else 0.8, 1.3 if i % 2 == 0 else 1.2,
                            math.atan2(nq[1] - q_[1], nq[0] - q_[0]) + math.pi / 2), m, z=17 + i, sd=0.5, hi=0.3, ol=0.8)
        q_ = nq
    mouth_pt = yg.world(cv, (hx_ + 9.4, hy_ + 2.6 + jd * 0.5))
    cv.pop()   # baş
    cv.pop()   # gövde
    legs(True)
    if sq:
        cv.pop()
    cv.pop()   # figür
    # toz: arka pençelerin itişinde / inişte yerden kalkan toz topakları (dünya; figür dönüşümünden bağımsız)
    if p['dust'] > 0.05:
        DUST = Ink('#b9b0a2', '#8c8274', '#e6dfd2', name='toz')
        hx_d = min(p['hf'][0], p['hb'][0])
        for i in range(3):
            r = (1.6 + 0.9 * i) * p['dust']
            yk.puff(cv, (hx_d - 2.5 - i * 3.4, -r * 0.6), r, DUST, z=-12 + i * 0.1, seed=7 + i, n=6, ol=0.3, sd=r * 0.15)
    # ısırık şaklaması: ağzın önünde kısa hız çizgileri
    if p['snap'] > 0.05:
        mx, my = mouth_pt
        for i, (dy, ln) in enumerate(((-2.2, 4.5), (0.0, 6.0), (2.2, 4.5))):
            L = ln * 1.7 * p['snap']
            cv.stroke([(mx + 1.5, my + dy), (mx + 1.5 + L * 0.6, my + dy * 1.4), (mx + 1.5 + L, my + dy * 1.9)], 2.0, z=40 + i * 0.1,
                      col=(1.0, 0.92, 0.75), taper=(0.2, 0.9), glow=EMBER_GLOW)
    return {'mouth': mouth_pt}


SHADE = dict(outer=0.5, rim=0.9, rim_col=(0.62, 0.7, 1.0), rim_dir=(0.55, -0.85), rim_w=1.6, form=(6.0, (0.72, 0.7, 0.86)))


# ====================================================================== anahtar pozlar (yaratik_govde.Seq)
# Ayak işi: yürüyüş 4 vuruşlu yanal sıra (arka-ön aynı yan, %25 arayla; basma oranı 0,7), dörtnal döner (rotary gallop:
# uzak arka -> yakın arka -> yakın ön -> uzak ön; iki askı evresi: gerilmiş ve toplanmış), yere basan pençe gövdeye göre
# sabit hızla geriye kayar (adım boyu / basma süresi = gövde hızı) — oyunda "vx" ile koşu hızına kilitlenir, kayma yok.
def _foot_cycle(phi, home, S, duty, lift, toe_up=0.9, toe_push=0.35):
    """Döngüsel pençe yolu: basma (duty) boyunca +S/2 -> -S/2 (sabit hız), salınımda yayla öne (yükseklik lift)."""
    phi %= 1.0
    if phi < duty:
        u = phi / duty
        x = home + S * (0.5 - u)
        toe = toe_push * max(0.0, (u - 0.75) / 0.25)          # itişte parmak ucu
        return (x, 0.0, -toe * 0.6)
    u = (phi - duty) / (1.0 - duty)
    e = u * u * (3 - 2 * u)
    x = home - S * 0.5 + S * e
    y = lift * math.sin(math.pi * u) ** 0.8
    return (x, y, toe_up * math.sin(math.pi * min(1.0, u * 1.3)))


def _walk(t):
    S, duty = 15.0, 0.68
    p = {}
    for k, home, off in (('hf', -12.6, 0.0), ('ff', 10.6, 0.25), ('hb', -10.8, 0.5), ('fb', 12.4, 0.75)):
        p[k] = _foot_cycle(t - off, home, S, duty, 3.6 if k[0] == 'h' else 4.2)
    p.update(y=0.6 * math.cos(t * 4 * math.pi) + 0.6, pitch=0.035 * math.sin(t * 2 * math.pi + 0.4),
             hd=(0.6 * math.sin(t * 2 * math.pi), 1.8 + 0.9 * math.cos(t * 4 * math.pi + 0.6)), hr=0.12 + 0.05 * math.sin(t * 4 * math.pi + 0.8),
             tw=0.08 * math.sin(t * 2 * math.pi), ph=t * math.tau, jaw=0.14, x=0.4 * math.sin(t * 2 * math.pi), mane=0.05, br=0.3 * math.sin(t * 4 * math.pi))
    return p


def _gallop(t):
    """Döner dörtnal: t=0 uzak arka iner. Toplanma askısı ~0,85, gerilme askısı ~0,45."""
    S, duty = 30.0, 0.30
    p = {}
    for k, home, off, lift in (('hb', -11.0, 0.00, 7.0), ('hf', -12.0, 0.10, 7.0), ('ff', 10.0, 0.38, 6.0), ('fb', 12.0, 0.48, 6.0)):
        p[k] = _foot_cycle(t - off, home, S, duty, lift, toe_up=1.3)
    # omurga: arka bacaklar basarken toplanır (öne gelir), ön bacaklar basarken gerilir
    flex = 3.6 * math.cos((t - 0.05) * math.tau)
    p.update(flex=flex, arch=1.4 * math.cos((t - 0.05) * math.tau),
             y=-1.2 - 1.6 * math.sin((t - 0.2) * math.tau) ** 2 + 0.8,
             pitch=0.09 * math.sin((t - 0.12) * math.tau),
             hd=(1.0 + 1.2 * math.sin((t + 0.15) * math.tau), 0.4 + 1.0 * math.cos((t + 0.1) * math.tau)),
             hr=-0.02 - 0.1 * math.sin((t + 0.15) * math.tau), tw=-0.25 + 0.15 * math.sin(t * math.tau),
             tl=0.05, ph=t * math.tau, jaw=0.38 + 0.12 * math.sin(t * math.tau), ear=0.35, mane=0.2, sq=0.0, tongue=0.0)
    return p


def _idle_proc(p, t):
    """Bekleme: nefes, kuyruk ve yelede ikincil dalga."""
    p = dict(p)
    p['br'] = p.get('br', 0.0) + 0.6 * math.sin(t * math.tau * 2)
    p['y'] = p.get('y', 0.0) + 0.35 * math.sin(t * math.tau * 2 + 0.6)
    p['ph'] = t * math.tau * 2
    return p


ST = REST    # kısaltma
CROUCH = dict(y=4.2, pitch=0.13, flex=2.6, arch=1.2, hf=(-9.5, 0.0, 0.3), hb=(-7.5, 0.0, 0.3), ff=(9.0, 0.0, 0.0), fb=(11.0, 0.0, 0.0),
              hd=(0.5, 3.5), hr=0.22, jaw=0.55, lip=0.8, ear=0.6, tw=0.35, tl=-0.1, mane=-0.1, hack=0.45)

SEQS = {}

# ---- bekleme (12 kare, 1,5 sn): başı alçak, sinsi soluk; ağırlık aktarımı; ortada hırlayıp başını silker (tik)
SEQS['idle'] = Seq([
    (0.0, dict(hd=(0.0, 2.0), hr=0.16, jaw=0.12, tw=0.1, x=0.0), 'io'),
    (0.25, dict(hd=(0.6, 2.4), hr=0.2, jaw=0.16, tw=-0.05, x=0.6, hf=(-13.6, 0.0, 0.0), ff=(9.8, 0.0, 0.0)), 'io'),
    (0.45, dict(hd=(0.3, 2.2), hr=0.15, jaw=0.12, tw=0.12, x=0.2), 'io'),
    (0.55, dict(hd=(1.4, 3.0), hr=0.24, jaw=0.5, lip=1.0, ear=0.7, tw=0.0, x=0.9, hack=0.35, mane=-0.1, blink=0.3), 'o'),
    (0.68, dict(hd=(1.1, 2.6), hr=0.18, jaw=0.35, lip=0.85, ear=0.6, hack=0.3, x=0.7, chain=0.6), 'io'),
    (0.8, dict(hd=(-0.4, 1.6), hr=0.06, jaw=0.14, lip=0.1, ear=0.1, tw=0.18, x=-0.3, chain=-0.4), 'o'),
    (1.0, dict(hd=(0.0, 2.0), hr=0.16, jaw=0.12, tw=0.1, x=0.0), 'io'),
], n=12, fps=8, loop=True, proc=_idle_proc, rest=REST)

# ---- yürüyüş (devriye; 8 kare, adım 15 birim): vx 26 px/sn'de 1x
SEQS['walk'] = Seq([(i / 8, _walk(i / 8), 'l') for i in range(9)], n=8, fps=14, loop=True, rest=REST,
                   extra={'vx': 26.0})
# ---- dörtnal (8 kare, adım 30): vx 80 px/sn'de 1x; yavaşta yürüyüşe döner
SEQS['run'] = Seq([(i / 16, _gallop(i / 16), 'l') for i in range(17)], n=8, fps=18, loop=True, rest=REST,
                  extra={'vx': 80.0, 'alt': [['walk', 46.0]]})

# ---- dönüş (3 kare, ~0,22 sn): yeni yöne bakarken baş hâlâ omuzdan geriye, gövde toplanıp döner, oturur
SEQS['turn'] = Seq([
    (0.0, dict(flex=4.5, pitch=-0.05, hd=(-9.0, -1.5), hr=-0.5, x=-1.5, hf=(-8.0, 0.0, 0.2), hb=(-6.0, 1.5, 0.6),
               ff=(6.0, 0.0, 0.0), fb=(9.0, 2.0, 0.6), tw=0.7, ear=0.4), 'l'),
    (0.5, dict(flex=2.0, hd=(-1.5, 1.0), hr=0.0, x=-0.4, hf=(-11.5, 1.6, 0.6), hb=(-9.5, 0.0, 0.0), ff=(8.0, 1.8, 0.7), fb=(11.0, 0.0, 0.0), tw=0.35), 'o'),
    (1.0, dict(hd=(0.0, 2.0), hr=0.14, tw=0.1), 'o'),
], frames=[0.0, 0.45, 1.0], fps=12, rest=REST)

# ---- atılış hazırlığı "!" (4 kare): geri yaslanma, çömelme, derin kurulma (tutulur), fırlayış (son 0,05 sn)
SEQS['windup'] = Seq([
    (0.0, dict(y=1.2, x=-1.0, hd=(-0.6, 2.4), hr=0.12, jaw=0.25, lip=0.5, ear=0.3, hack=0.2, tw=0.2), 'o'),
    (0.3, dict(CROUCH, x=-1.6), 'o'),
    (0.62, dict(CROUCH, x=-2.4, y=5.4, flex=3.4, pitch=0.16, hd=(0.8, 4.2), jaw=0.85, lip=1.0, ear=0.9, eye=0.35, hack=0.6,
                hf=(-8.6, 0.0, 0.45), hb=(-6.6, 0.0, 0.45), tw=0.45), 'o'),
    (1.0, dict(dust=1.0, x=3.5, y=0.5, flex=-3.0, arch=-0.6, pitch=-0.07, hf=(-18.0, 0.0, 1.0), hb=(-16.0, 0.8, 1.0), ff=(19.0, 4.0, 0.8),
               fb=(21.0, 5.5, 0.9), hd=(3.5, 0.5), hr=-0.12, jaw=1.0, lip=0.9, ear=0.8, tw=-0.35, mane=0.3, hack=0.4, chain=-1.0), 'i'),
], frames=[(0.0, 0.0), (0.3, 0.22), (0.62, 0.5), (1.0, 0.0)], seg=[('windup', 4)], lead={'windup': 0.05}, rest=REST, fps=10)

# ---- zırhlı atılış hazırlığı "!!" (4 kare): tüyler dimdik, yere sinik geniş duruş, gözler alev alev, kuyruk kaskatı
AA = dict(y=6.2, x=-2.6, pitch=0.2, flex=3.0, arch=2.2, hf=(-9.5, 0.0, 0.5), hb=(-6.0, 0.0, 0.5), ff=(11.5, 0.0, 0.0), fb=(14.5, 0.0, 0.0),
          hd=(2.0, 5.6), hr=0.34, jaw=1.0, lip=1.2, ear=1.0, eye=1.0, hack=1.0, mane=0.15, tw=-0.15, tl=-0.35, chain=0.6)
SEQS['windup_aa'] = Seq([
    (0.0, dict(y=2.0, x=-1.2, hd=(0.0, 3.0), hr=0.2, jaw=0.45, lip=0.9, ear=0.6, hack=0.6, eye=0.4, tl=-0.2), 'o'),
    (0.3, dict(AA, y=5.0, hack=0.85, eye=0.7, jaw=0.8), 'o'),
    (0.62, dict(AA), 'io'),
    (1.0, dict(dust=1.2, x=3.8, y=0.5, flex=-3.4, arch=-0.6, pitch=-0.08, hf=(-19.0, 0.0, 1.0), hb=(-17.0, 0.8, 1.0), ff=(19.5, 4.5, 0.8),
               fb=(21.5, 6.0, 0.9), hd=(3.6, 0.5), hr=-0.12, jaw=1.0, lip=1.2, ear=1.0, eye=1.0, hack=0.9, tw=-0.35, mane=0.35, chain=-1.0), 'i'),
], frames=[(0.0, 0.0), (0.3, 0.2), (0.62, 0.45), (1.0, 0.0)], seg=[('windup', 4)], lead={'windup': 0.05}, rest=REST, fps=10)

# ---- sıçrayış (dikey hız evresi; 5 kare): gerilmiş kalkış, tepede çene sonuna dek açık, inişte ŞAK diye kapanan ısırık,
# iniş için uzanan ön bacaklar
SEQS['leap'] = Seq([
    (0.0, dict(x=4.0, y=-1.5, flex=-4.5, arch=-1.0, pitch=-0.06, hf=(-27.0, 2.5, 1.3), hb=(-25.0, 4.0, 1.4), ff=(25.0, 7.0, 0.6),
               fb=(27.0, 9.0, 0.7), hd=(4.0, 0.0), hr=-0.12, jaw=1.1, lip=1.0, ear=1.0, tw=-0.45, tl=0.05, mane=0.45, chain=-1.3, hack=0.35), 'o'),
    (0.4, dict(x=4.0, y=-3.0, flex=-3.5, arch=-0.6, pitch=0.0, hf=(-22.0, 9.0, 1.4), hb=(-20.0, 11.0, 1.5), ff=(26.0, 8.0, 0.5),
               fb=(28.0, 10.0, 0.6), hd=(4.5, 1.0), hr=0.0, jaw=1.2, lip=1.1, ear=1.0, tw=-0.35, mane=0.4, chain=-0.8, hack=0.4, eye=0.4), 'io'),
    (0.6, dict(snap=1.0, x=4.5, y=-2.0, flex=-1.5, pitch=0.1, hf=(-17.0, 9.0, 1.2), hb=(-15.0, 10.0, 1.3), ff=(22.0, 4.0, 0.3),
               fb=(24.0, 6.0, 0.4), hd=(5.0, 2.5), hr=0.2, jaw=0.0, lip=1.1, ear=0.8, tw=-0.15, mane=0.2, chain=0.5, hack=0.35), 'i'),
    (1.0, dict(x=2.5, y=-0.5, flex=1.5, pitch=0.15, hf=(-11.0, 5.0, 0.9), hb=(-9.0, 6.0, 1.0), ff=(16.0, 1.0, 0.1),
               fb=(18.0, 2.0, 0.2), hd=(2.0, 3.0), hr=0.2, jaw=0.25, lip=0.6, ear=0.5, tw=0.0, chain=0.9), 'o'),
], frames=[(0.0, 0.0), (0.25, 0.2), (0.45, 0.42), (0.62, 0.58), (1.0, 0.8)], seg=[('air', 5)], rest=REST, fps=10)

# ---- geri sekiş (dikey hız evresi; 4 kare): ön bacaklarla itip geriye, baş hep oyuncuda, arka ayaklarla iniş
SEQS['back'] = Seq([
    (0.0, dict(x=-1.0, y=-0.5, pitch=-0.2, flex=1.0, hf=(-14.0, 0.0, 0.6), hb=(-12.0, 1.0, 0.6), ff=(13.0, 2.0, 0.8), fb=(15.0, 4.0, 0.9),
               hd=(1.0, -1.0), hr=-0.1, jaw=0.6, lip=0.8, ear=0.6, tw=0.4, chain=0.8), 'o'),
    (0.4, dict(x=-2.0, y=-3.0, pitch=-0.1, flex=3.0, arch=1.4, hf=(-15.0, 4.0, 1.0), hb=(-13.0, 5.0, 1.1), ff=(8.0, 5.0, 1.0), fb=(10.0, 6.0, 1.1),
               hd=(1.5, 1.0), hr=0.05, jaw=0.5, lip=0.9, ear=0.6, tw=0.55, chain=0.4), 'io'),
    (0.75, dict(x=-1.0, y=-0.5, pitch=-0.04, flex=1.5, hf=(-15.5, 0.5, 0.5), hb=(-13.5, 1.2, 0.6), ff=(9.0, 2.5, 0.7), fb=(11.0, 3.0, 0.8),
                hd=(1.0, 2.0), hr=0.12, jaw=0.4, lip=0.7, tw=0.35), 'o'),
    (1.0, dict(y=1.6, pitch=0.06, flex=1.0, hf=(-13.6, 0.0, 0.0), hb=(-11.4, 0.0, 0.0), ff=(10.0, 0.0, 0.0), fb=(12.0, 0.0, 0.0),
               hd=(0.5, 2.6), hr=0.18, jaw=0.35, lip=0.6, tw=0.2), 'o'),
], frames=[(0.0, 0.0), (0.4, 0.3), (0.75, 0.62), (1.0, 0.85)], seg=[('air', 4)], rest=REST, fps=10)

# ---- alçak atılış (Mağara Tazısı zincir ısırığı; 3 kare, st 0,2): yere yapışık gerilme, ısırık, toplanma
SEQS['dash'] = Seq([
    (0.0, dict(dust=0.9, x=3.0, y=3.0, flex=-4.0, pitch=0.02, hf=(-22.0, 0.0, 1.0), hb=(-20.0, 1.5, 1.2), ff=(20.0, 2.5, 0.6), fb=(22.0, 3.5, 0.7),
               hd=(4.0, 3.0), hr=0.05, jaw=1.1, lip=1.0, ear=1.0, tw=-0.5, mane=0.4, chain=-1.0), 'o'),
    (0.5, dict(snap=1.0, x=4.0, y=3.5, flex=-2.0, pitch=0.08, hf=(-18.0, 3.0, 1.2), hb=(-16.0, 2.0, 1.0), ff=(19.0, 0.0, 0.0), fb=(21.0, 1.0, 0.3),
               hd=(5.0, 4.0), hr=0.12, jaw=0.0, lip=1.0, ear=0.9, tw=-0.3, mane=0.3, chain=0.4), 'i'),
    (1.0, dict(x=2.0, y=3.5, flex=2.5, pitch=0.12, hf=(-10.0, 0.0, 0.3), hb=(-8.0, 1.5, 0.6), ff=(14.0, 0.0, 0.0), fb=(16.0, 0.0, 0.0),
               hd=(2.0, 3.5), hr=0.2, jaw=0.45, lip=0.8, ear=0.7, tw=0.1, chain=0.8), 'o'),
], frames=[(0.0, 0.0), (0.5, 0.35), (1.0, 0.75)], seg=[('strike', 3)], rest=REST, fps=12)

# ---- pusu atlayışı (yukarıdan; dikey hız evresi; 4 kare): pençeler açık, gövde aşağı dönük, iniş için toplanma
SEQS['pounce'] = Seq([
    (0.0, dict(x=2.0, y=-4.0, flex=-3.0, pitch=-0.25, hf=(-20.0, 8.0, 1.2), hb=(-18.0, 10.0, 1.3), ff=(18.0, 16.0, -0.2), fb=(21.0, 18.0, -0.1),
               hd=(3.0, -2.0), hr=-0.3, jaw=1.0, lip=1.0, ear=0.9, tw=-0.3, mane=0.4, hack=0.6, chain=-1.0), 'o'),
    (0.45, dict(x=2.0, y=-4.0, flex=-2.0, pitch=0.12, hf=(-18.0, 10.0, 1.0), hb=(-16.0, 12.0, 1.1), ff=(21.0, 9.0, -0.5), fb=(24.0, 11.0, -0.4),
                hd=(4.0, 2.0), hr=0.15, jaw=1.15, lip=1.1, ear=1.0, tw=-0.1, mane=0.2, hack=0.7, eye=0.5), 'io'),
    (0.75, dict(x=1.5, y=-2.0, flex=0.5, pitch=0.3, hf=(-13.0, 9.0, 0.9), hb=(-11.0, 10.0, 1.0), ff=(17.0, 3.0, -0.3), fb=(20.0, 4.0, -0.2),
                hd=(3.0, 4.0), hr=0.35, jaw=0.9, lip=1.0, ear=0.9, tw=0.2, mane=0.0, hack=0.6, chain=0.8), 'i'),
    (1.0, dict(x=1.0, y=0.0, flex=2.0, pitch=0.3, hf=(-10.0, 5.0, 0.8), hb=(-8.0, 6.0, 0.9), ff=(14.0, 0.5, 0.0), fb=(17.0, 1.0, 0.0),
               hd=(2.0, 4.0), hr=0.35, jaw=0.7, lip=0.9, ear=0.8, tw=0.3, hack=0.5, chain=1.0), 'o'),
], frames=[(0.0, 0.0), (0.4, 0.3), (0.72, 0.6), (1.0, 0.85)], seg=[('air', 4)], rest=REST, fps=10)

# ---- iniş çöküşü (pusu sonrası toparlanma; st 0,45; 3 kare): göğüs yere yakın, toz, kalkış
SEQS['land'] = Seq([
    (0.0, dict(dust=1.3, y=6.0, x=1.0, pitch=0.25, flex=2.5, arch=1.6, hf=(-9.0, 0.0, 0.5), hb=(-7.0, 0.0, 0.6), ff=(15.0, 0.0, 0.0), fb=(18.0, 0.0, 0.0),
               hd=(2.0, 6.0), hr=0.3, jaw=0.6, lip=0.8, ear=0.8, tw=0.5, hack=0.4, chain=1.2), 'o'),
    (0.5, dict(y=3.0, x=0.5, pitch=0.1, flex=1.0, hf=(-11.5, 0.0, 0.2), hb=(-9.5, 0.0, 0.3), ff=(12.5, 0.0, 0.0), fb=(15.0, 0.0, 0.0),
               hd=(1.0, 3.5), hr=0.2, jaw=0.4, lip=0.6, ear=0.5, tw=0.3, hack=0.2), 'io'),
    (1.0, dict(y=0.6, hd=(0.4, 2.4), hr=0.16, jaw=0.25, lip=0.3, tw=0.15), 'o'),
], frames=[(0.0, 0.0), (0.5, 0.35), (1.0, 0.7)], seg=[('recover', 3)], rest=REST, fps=10)

# ---- hafif sarsılma (3 kare, 0,22 sn): baş darbeden kaçar, gözler kısılır, kulaklar yatar, çene acıyla açık
SEQS['hurt'] = Seq([
    (0.0, dict(x=-2.0, y=1.5, pitch=-0.12, flex=1.5, hd=(-2.5, -2.0), hr=-0.35, jaw=0.7, lip=0.3, ear=1.0, blink=1.0, tw=-0.65,
               hf=(-14.0, 0.0, 0.2), hb=(-12.0, 0.0, 0.2), ff=(8.5, 2.0, 0.6), fb=(11.0, 1.0, 0.4), chain=1.2, mane=-0.3), 'o'),
    (0.5, dict(x=-1.0, y=1.0, pitch=-0.05, flex=1.0, hd=(-1.0, 0.5), hr=-0.12, jaw=0.45, ear=0.7, blink=0.6, tw=-0.5, chain=0.5), 'o'),
    (1.0, dict(hd=(0.2, 2.0), hr=0.12, jaw=0.3, lip=0.4, ear=0.3, tw=-0.38), 'o'),
], frames=[(0.0, 0.0), (0.5, 0.35), (1.0, 0.7)], rest=REST, fps=12)

# ---- ağır sendeleme (4 kare, 0,45 sn): ön ayaklar yerden kesilir, gövde bükülür, arka ayaklar kayarak tutunur
SEQS['hurt_big'] = Seq([
    (0.0, dict(x=-3.5, y=-1.0, pitch=-0.3, flex=2.5, arch=-1.0, hd=(-3.5, -3.0), hr=-0.55, jaw=0.9, ear=1.0, blink=1.0, tw=-0.75,
               hf=(-15.0, 0.0, 0.0), hb=(-13.0, 0.5, 0.2), ff=(6.0, 7.0, 0.9), fb=(9.0, 9.0, 1.0), chain=1.6, mane=-0.5, roll=-0.1), 'o'),
    (0.35, dict(x=-3.0, y=1.0, pitch=-0.12, flex=2.5, hd=(-2.0, 0.0), hr=-0.25, jaw=0.6, ear=0.9, blink=0.8, tw=-0.65,
                hf=(-15.5, 0.0, 0.0), hb=(-13.5, 0.0, 0.0), ff=(7.5, 2.5, 0.7), fb=(10.0, 3.5, 0.8), chain=1.0, roll=-0.05), 'io'),
    (0.7, dict(x=-1.5, y=2.5, pitch=0.08, flex=1.5, hd=(0.0, 3.0), hr=0.15, jaw=0.5, lip=0.5, ear=0.6, blink=0.3, tw=-0.5,
               hf=(-14.0, 0.0, 0.2), hb=(-12.0, 0.0, 0.2), ff=(9.0, 0.0, 0.0), fb=(11.0, 0.0, 0.0), chain=0.2), 'o'),
    (1.0, dict(y=0.8, hd=(0.3, 2.2), hr=0.14, jaw=0.3, lip=0.6, ear=0.3, tw=-0.38), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.25), (0.7, 0.55), (1.0, 0.8)], rest=REST, fps=10)


# ---- duruş kırık / sersem (6 kare döngü): baş sarkık sallanır, bacaklar titrek, sendeler
def _stun(t):
    s = math.sin(t * math.tau)
    c = math.cos(t * math.tau)
    return dict(x=1.6 * s, y=2.6 + 0.8 * c, pitch=0.12 + 0.05 * c, flex=1.0, roll=0.05 * s, hd=(0.5 * s, 6.0 + 0.8 * c), hr=0.5 + 0.12 * s,
                jaw=0.55, tongue=0.8, ear=0.9, blink=0.55, tw=-0.6 + 0.15 * s, chain=0.8 * s, mane=-0.3,
                hf=(-13.0, 0.0, 0.0), hb=(-10.0 + 1.0 * c, 0.0, 0.2), ff=(9.0, 0.0, 0.0), fb=(13.0 + 0.8 * s, 0.6 * max(0.0, s), 0.2))


SEQS['stun'] = Seq([(i / 12, _stun(i / 12), 'l') for i in range(13)], n=6, fps=6, loop=True, rest=REST)

# ---- havaya savrulma (dikey hız evresi; 4 kare): kıvrılıp yana yatarak döner, düşüşte bacaklar çırpınır
SEQS['launch'] = Seq([
    (0.0, dict(y=-3.0, roll=-0.35, pitch=-0.2, flex=3.0, arch=2.0, hd=(-2.5, -1.0), hr=-0.4, jaw=0.9, ear=1.0, blink=1.0, tw=0.9,
               hf=(-9.0, 8.0, 1.2), hb=(-7.0, 10.0, 1.3), ff=(6.0, 9.0, 1.0), fb=(9.0, 11.0, 1.1), chain=1.5, mane=-0.4), 'o'),
    (0.4, dict(y=-4.0, roll=-0.8, pitch=-0.1, flex=4.0, arch=2.4, hd=(-2.0, 1.0), hr=-0.2, jaw=0.8, ear=1.0, blink=0.9, tw=1.0,
               hf=(-8.0, 6.0, 1.3), hb=(-5.0, 9.0, 1.4), ff=(5.0, 6.0, 1.2), fb=(8.0, 9.0, 1.3), chain=-1.0), 'io'),
    (0.7, dict(y=-3.0, roll=-0.55, pitch=0.1, flex=1.0, arch=0.5, hd=(0.0, 1.0), hr=0.0, jaw=0.7, ear=0.9, blink=0.5, tw=0.6,
               hf=(-14.0, 6.0, 0.9), hb=(-11.0, 4.0, 0.7), ff=(12.0, 5.0, 0.3), fb=(15.0, 3.0, 0.2), chain=0.5), 'io'),
    (1.0, dict(y=-1.0, roll=-0.2, pitch=0.15, flex=0.0, hd=(1.0, 2.5), hr=0.15, jaw=0.6, ear=0.8, blink=0.3, tw=0.3,
               hf=(-14.0, 3.0, 0.5), hb=(-12.0, 2.0, 0.4), ff=(13.0, 2.5, 0.0), fb=(16.0, 1.5, 0.0), chain=0.2), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.25), (0.65, 0.55), (1.0, 0.82)], seg=[('air', 4)], rest=REST, fps=10)

# ---- kalkış (savrulma sonrası; 4 kare, 0,5 sn): yere yapışmış gövde ön bacaklarla doğrulur, silkinir
SEQS['getup'] = Seq([
    (0.0, dict(y=9.0, x=-1.0, pitch=0.1, flex=1.0, hd=(1.5, 8.0), hr=0.45, jaw=0.5, ear=0.9, blink=0.8, tw=-0.7,
               hf=(-19.0, 0.0, -0.4), hb=(-17.0, 0.0, -0.3), ff=(15.0, 0.0, -0.3), fb=(18.0, 0.0, -0.2), chain=1.0), 'o'),
    (0.35, dict(y=5.5, pitch=0.16, flex=2.5, arch=1.5, hd=(0.5, 5.0), hr=0.4, jaw=0.4, ear=0.8, blink=0.4, tw=-0.6,
                hf=(-10.5, 0.0, 0.6), hb=(-8.5, 0.0, 0.8), ff=(11.0, 0.0, 0.0), fb=(13.0, 1.5, 0.4), chain=0.6), 'o'),
    (0.65, dict(y=1.5, roll=0.05, pitch=0.04, hd=(-0.5, 1.5), hr=-0.25, jaw=0.3, ear=0.2, tw=-0.55, mane=0.5, chain=-1.2), 'io'),
    (1.0, dict(y=0.6, hd=(0.3, 2.2), hr=0.15, jaw=0.25, lip=0.5, ear=0.3, tw=-0.38, mane=-0.2, chain=0.6), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.3), (0.65, 0.6), (1.0, 0.85)], rest=REST, fps=10)

# ---- ölüm (8 kare, 0,9 sn): darbeyle geri şahlanır, arka bacaklar çöker, ön bacaklar bükülüp öne kayar, göğüs ve baş
# yere çarpar, son bir çırpınış (arka bacak tekmesi) ve gövde gevşeyip yayılır
SEQS['death'] = Seq([
    (0.0, dict(x=-3.0, y=-0.5, pitch=-0.24, flex=2.0, arch=-1.0, hd=(-3.0, -3.0), hr=-0.55, jaw=1.1, ear=1.0, blink=1.0, tw=-0.8,
               hf=(-15.0, 0.0, 0.0), hb=(-13.0, 0.0, 0.0), ff=(6.0, 8.0, 1.0), fb=(9.0, 10.0, 1.1), chain=1.8, mane=-0.6), 'o'),
    (0.18, dict(x=-3.5, y=4.0, pitch=-0.3, flex=3.5, arch=1.5, hd=(-2.0, -1.0), hr=-0.4, jaw=0.9, ear=1.0, blink=1.0, tw=-0.7,
                hf=(-9.0, 0.0, 0.8), hb=(-7.0, 0.0, 0.8), ff=(8.0, 3.0, 0.9), fb=(11.0, 4.0, 1.0), chain=0.6), 'io'),
    (0.36, dict(x=-3.0, y=7.5, pitch=0.1, flex=3.0, arch=1.0, hd=(0.0, 4.0), hr=0.3, jaw=0.7, ear=1.0, blink=1.0, tw=-0.6,
                hf=(-9.0, 0.0, 1.0), hb=(-7.0, 0.0, 1.0), ff=(10.0, 0.0, 0.0), fb=(13.0, 0.0, 0.0), chain=1.4), 'i2'),
    (0.52, dict(x=-2.5, y=10.0, pitch=0.2, flex=1.5, roll=0.08, hd=(2.0, 5.2), hr=0.5, jaw=0.9, ear=1.0, blink=1.0, tw=-0.65, tongue=0.5,
                hf=(-13.0, 0.0, 0.4), hb=(-11.0, 0.0, 0.4), ff=(15.0, 0.0, -0.2), fb=(18.0, 0.0, -0.2), chain=1.6), 'i'),
    (0.64, dict(x=-2.5, y=11.0, pitch=0.12, flex=0.5, roll=0.04, hd=(2.5, 5.2), hr=0.42, jaw=0.6, ear=1.0, blink=1.0, tw=-0.75, tongue=0.9,
                hf=(-18.0, 0.0, -0.3), hb=(-15.0, 4.0, 0.6), ff=(17.0, 0.0, -0.3), fb=(20.0, 0.0, -0.3), chain=0.8), 'o'),
    (0.76, dict(x=-2.5, y=11.0, pitch=0.12, flex=0.3, roll=0.04, hd=(2.5, 5.2), hr=0.42, jaw=0.7, ear=1.0, blink=1.0, tw=-0.6, tongue=1.0,
                hf=(-21.0, 2.5, 0.2), hb=(-17.0, 0.0, -0.3), ff=(17.5, 0.0, -0.3), fb=(20.5, 0.0, -0.3), chain=0.5), 'io'),
    (1.0, dict(x=-2.5, y=11.5, pitch=0.1, flex=0.0, roll=0.04, hd=(2.8, 5.2), hr=0.42, jaw=0.5, ear=1.0, blink=1.0, tw=-0.5, tongue=1.0,
               hf=(-20.0, 0.0, -0.4), hb=(-17.5, 0.0, -0.4), ff=(18.0, 0.0, -0.3), fb=(21.0, 0.0, -0.3), chain=0.0, mane=-0.4), 'o'),
], frames=[(0.0, 0.0), (0.16, 0.1), (0.34, 0.22), (0.5, 0.34), (0.62, 0.46), (0.74, 0.58), (0.86, 0.72), (1.0, 0.88)], rest=REST, fps=10)

# ---- uluma (seçkin kükremesi; 6 kare): başını göğe kaldırır, tüyler kabarır, uzun uluma
SEQS['howl'] = Seq([
    (0.0, dict(hd=(0.0, 2.0), hr=0.14), 'io'),
    (0.25, dict(y=1.5, x=-1.0, pitch=-0.1, hd=(-2.0, -3.0), hr=-0.7, jaw=0.4, ear=0.4, tw=0.3, hack=0.5, mane=0.1,
                hf=(-12.0, 0.0, 0.2), hb=(-10.0, 0.0, 0.2)), 'o'),
    (0.55, dict(y=0.5, x=-1.5, pitch=-0.22, hd=(-3.0, -5.0), hr=-1.05, jaw=0.95, ear=0.3, tw=0.5, hack=1.0, mane=0.3, eye=0.8, br=1.0,
                hf=(-12.0, 0.0, 0.2), hb=(-10.0, 0.0, 0.2)), 'io'),
    (0.8, dict(y=0.8, x=-1.2, pitch=-0.2, hd=(-2.8, -4.6), hr=-0.98, jaw=0.85, ear=0.3, tw=0.45, hack=0.9, mane=0.4, eye=0.6, br=0.4,
               hf=(-12.0, 0.0, 0.2), hb=(-10.0, 0.0, 0.2)), 'io'),
    (1.0, dict(hd=(0.0, 2.0), hr=0.14, hack=0.2), 'o'),
], n=6, fps=8, rest=REST)

DURUM = {
    # ---- tepkiler (Enemy._anim_tick öncelikli anahtarları)
    '_hurt': {'a': 'hurt', 'u': 'up', 'd': 0.22},
    '_hurt_big': {'a': 'hurt_big', 'u': 'up', 'd': 0.45},
    '_break': {'a': 'stun', 'u': 'loop'},
    '_launch': {'a': 'launch', 'u': 'vy'},
    '_getup': {'a': 'getup', 'u': 'up', 'd': 0.5},
    '_death': {'a': 'death', 'u': 'up', 'd': 0.9},
    '_turn': {'a': 'turn', 'u': 'up', 'd': 0.2},
    '_roar': {'a': 'howl', 'u': 'up', 'd': 0.8},
    # ---- saldırılar
    'windup': {'a': 'windup', 's': 'windup', 'u': 'st'},
    'windup!!': {'a': 'windup_aa', 's': 'windup', 'u': 'st'},
    'leap': {'a': 'leap', 'u': 'vy'},
    'back': {'a': 'back', 'u': 'vy'},
    'evade': {'a': 'back', 'u': 'vy'},
    'dash': {'a': 'dash', 'u': 'st'},
    'leap/pounce': {'a': 'pounce', 'u': 'vy'},      # pusu tazısı: perch'ten atlayış (hamle windup'tan taşınır)
    'recover/pounce': {'a': 'land', 'u': 'st'},
    'recover': {'a': 'land', 'u': 'st'},
}


def render_frame(anim, i, ss=3):
    p = SEQS[anim].pose(i)
    cv = ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
