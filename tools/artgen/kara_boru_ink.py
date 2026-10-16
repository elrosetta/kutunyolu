"""Erlik Tazısı (kimlik kara_boru) — stil v2 "mürekkep-cel" (inkkit.py). v1: creatures.draw_hound.

Aynı iskelet, pozlar (creatures.HOUND_ANIMS: idle 6, run 6, windup 2, leap 2, hurt 2) ve 'mouth' çapası; 3x doku
yoğunluğu (hücre 240x168 = dünya 80x56, ayak (36, 52)). Sıska ama güçlü kara tazı: derin göğüs, içe çekik bel,
kemik alın zırhı ve omur plakaları, dumanlı yele (uçları kor), kırık zincirli paslı tasma; göz ve ağız kor gibi yanar.
Koyu post mürekkep konturunu yutmasın diye sırtta soğuk ay kenar ışığı (finish rim) ve mor-gri parlama tonu.
"""
import math

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_leg, lerp2, chain
import wolfkit as wk
from creatures import HOUND_ANIMS

TEX = 3.0
CELL = (240, 168)
FEET = (108, 156)
ANIMS = {k: (v[0], v[1], k in ('idle', 'run'), True) for k, v in HOUND_ANIMS.items()}

FURK = Ink('#3a3548', '#181522', '#68607e', '#0e0c16', name='tazı postu')
FURK_B = Ink('#2a2440', '#14111e', '#433c5c', '#0b0a12', name='uzak post')
SMOKE = Ink('#5a5470', '#262236', '#8a84a6', name='duman yele')
BONE = Ink('#e2d6b4', '#8c7c5c', '#fffbe8', '#5a4c38', name='kemik')
RUST = Ink('#9a5a34', '#4a2416', '#d08a52', name='paslı zincir')
IRON = Ink('#5e6070', '#2a2a36', '#a0a4b8', name='demir')
CLAW = Ink('#d8ccb0', '#7a6c52', '#ffffff', name='tırnak')
EMBER = (1.0, 0.56, 0.16)
EMBER_HOT = (1.0, 0.86, 0.45)
EMBER_GLOW = (1.0, 0.45, 0.08)


def _hind(hip, a, s=1.0):
    _, foot = fk_leg(hip, a[0], a[1], 9.0 * s, 10.5 * s)
    up = wk.norm((hip[0] - foot[0], hip[1] - foot[1]))
    hock = wk.add(foot, wk.rot(up, -0.55), 5.4 * s)
    knee, hock = wk.ik(hip, hock, 7.6 * s, 7.2 * s, -1)
    return knee, hock, foot


def _front(sh, a, s=1.0):
    _, foot = fk_leg(sh, a[0], a[1], 9.0 * s, 10.0 * s)
    up = wk.norm((sh[0] - foot[0], sh[1] - foot[1]))
    wrist = wk.add(foot, wk.rot(up, 0.32), 3.2 * s)
    elbow, wrist = wk.ik(sh, wrist, 7.6 * s, 8.4 * s, 1)
    return elbow, wrist, foot


def _paw(cv, f, m, z):
    paw = cv.blob([(f[0] - 1.2, f[1] - 1.6), (f[0] + 2.0, f[1] - 2.2), (f[0] + 3.9, f[1] - 0.9), (f[0] + 3.6, f[1] + 0.4, 0.0),
                   (f[0] - 1.0, f[1] + 0.4, 0.0)])
    cv.shape(paw, m, z=z, sd=0.9, hi=0.3)
    for i in range(2):
        x, y = f[0] + 3.5 + i * 0.2, f[1] - 0.9 + i * 0.8
        cv.shape(cv.blob([(x - 0.4, y - 0.5), (x + 1.5, y + 0.4, 0.0), (x - 0.4, y + 0.4)]), CLAW, z=z + 0.2, sd=0.3, ol=0.6)


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
    bob, tilt, jaw = p.get('bob', 0.0), p.get('tilt', 0.0), p.get('jaw', 0.0)
    ph = p.get('ph', 0.0)
    sq = p.get('sq', 0.0)
    sqx, sqy = 1.0 + 0.06 * sq, 1.0 - 0.07 * sq
    if sq:
        cv.push(lambda q: (q[0] * sqx, q[1] * sqy))
    hipp = (-10.0, -19.0 + bob - tilt * 6)
    shp = (8.5, -20.5 + bob + tilt * 6)

    def legs(near):
        z = 8 if near else -8
        m = FURK if near else FURK_B
        hip_j = (hipp[0] + 0.5, hipp[1] + 0.5)
        sh_j = (shp[0] + 0.8, shp[1] + 1.5)
        k, hk, f = _hind(hip_j, p['hf'] if near else p['hb'])
        th = lerp2(hip_j, k, 0.42)
        thigh = ik.union(cv.limb([hip_j, th, k], [4.6 if near else 4.0, 4.4 if near else 3.8, 2.3]),
                         cv.blob([q for t in _tufts([lerp2(hip_j, k, 0.5), lerp2(hip_j, k, 0.8)], math.pi * 0.72, 3.0, 2.0) for q in t]))
        hind = ik.union(thigh, cv.limb([k, hk, f], [2.3, 1.5, 1.3]))
        cv.shape(hind, m, z=z, sd=2.6, hi=0.3 if near else 0.0,
                 details=[('ink', [lerp2(hip_j, k, 0.25), lerp2(hip_j, k, 0.55), lerp2(hip_j, k, 0.75)], 1.2)] if near else ())
        _paw(cv, f, m, z + 0.5)
        e, w, f2 = _front(sh_j, p['ff'] if near else p['fb'])
        blade = cv.ellipse(lerp2(sh_j, e, 0.35), 5.0, 3.4, math.atan2(e[1] - sh_j[1], e[0] - sh_j[0]))
        fore = ik.union(blade, cv.limb([sh_j, e, w, f2], [3.2, 2.2, 1.45, 1.3]),
                        cv.blob(_tufts([lerp2(e, w, 0.15)], math.pi * 0.85, 2.6, 1.6)[0]))
        cv.shape(fore, m, z=z + 0.6, sd=2.2, hi=0.3 if near else 0.0)
        _paw(cv, f2, m, z + 1.0)
        if near:
            cv.shape(cv.ellipse(k, 1.2, 1.2), BONE, z=z + 1.2, sd=0.6, hi=0.3, ol=0.8)

    legs(False)
    # ---- kuyruk: kalın kök, dumanlı uçlar
    tw = p.get('tw', 0.0)
    tl = chain((hipp[0] - 4.5, hipp[1] - 3.2), 5, 3.0, math.pi * 0.92 + tw, -0.12, ph - 0.9, 0.32)   # kurt gibi alçak taşınan kuyruk
    cv.shape(ik.union(ik.taper_path([cv.W(q) for q in tl], cv.u(4.2), prof=lambda u: max(0.2, 0.55 + 0.6 * math.sin(math.pi * min(1.0, u * 1.3)) - 0.5 * u)),
                       *[cv.blob(t) for t in _tufts(tl[1:5], math.pi * 0.62 + tw, 2.6, 1.8)]), FURK_B, z=-6, sd=1.4)
    for k_, da in enumerate((-0.35, 0.0, 0.4)):
        tt = chain(tl[-1], 3, 2.2 - abs(da), math.pi * 1.1 + tw * 1.3 + da, -0.1, ph - 1.4 + k_, 0.45)
        cv.shape(ik.taper_path([cv.W(q) for q in [tl[-2]] + tt], cv.u(2.6), (0.0, 0.8)), SMOKE, z=-6.2 + k_ * 0.1, sd=0.8, ol=0.8)
        if k_ == 1:
            cv.fill(ik.taper_path([cv.W(q) for q in tt[-2:]], cv.u(1.0), (0.0, 0.9)), EMBER, z=-5.9, glow=EMBER_GLOW)
    # ---- gövde: kalça + bel + derin göğüs + omuz tümseği (tek kontur)
    body = ik.union(cv.ellipse((hipp[0], hipp[1] - 0.5), 6.0, 6.2),
                    cv.capsule((hipp[0] + 1.5, hipp[1] - 2.4), (shp[0] - 3.0, shp[1] - 0.8), 4.3, 6.4),
                    cv.ellipse((shp[0] + 0.5, shp[1] + 1.8), 7.4, 8.3, -0.18),
                    cv.ellipse((shp[0] - 2.5, shp[1] - 4.6), 6.0, 3.4))
    bp = [lerp2((hipp[0] + 3.0, hipp[1] + 1.6), (shp[0] - 2.0, shp[1] + 7.0), t) for t in (0.15, 0.45, 0.75)]
    belly = [cv.blob(t) for t in _tufts(bp, math.pi * 0.7, 2.6, 1.8)]
    chest = [cv.blob(t) for t in _tufts([(shp[0] + 6.5, shp[1] + 2.0), (shp[0] + 6.0, shp[1] + 5.5), (shp[0] + 4.0, shp[1] + 8.4)], math.pi * 0.35, 2.8, 2.0)]
    body = ik.union(body, *belly, *chest)
    # kaburgalar: mürekkep yayları + açık tonlu çıkıntılar
    rdet = []
    for i in range(4):
        cx = shp[0] - 4.2 + i * 2.2
        pts = [(cx - 0.6, shp[1] - 1.0), (cx + 0.3, shp[1] + 2.4), (cx + 0.2, shp[1] + 5.4 - i * 0.4)]
        rdet.append(('stroke', [(q[0] - 0.5, q[1]) for q in pts], 1.6, FURK.hi, (0.4, 0.4)))
        rdet.append(('ink', pts, 1.3, (0.4, 0.4)))
    rdet += cv.fold([(hipp[0] + 2.0, hipp[1] - 3.0), (hipp[0] + 5.0, hipp[1] + 0.5), (hipp[0] + 4.6, hipp[1] + 3.6)], 0.8, 1.3, 1)
    cv.shape(body, FURK, z=0, sd=4.2, hi=0.45, details=rdet, hatch=0.0)
    # leğen kemiği plakası + omur plakaları
    hx0, hy0 = hipp
    cv.shape(cv.blob([(hx0 - 4.0, hy0 - 4.6), (hx0 + 2.5, hy0 - 6.6), (hx0 + 3.8, hy0 - 4.4, 0.0), (hx0 - 1.8, hy0 - 2.8)]), BONE, z=10, sd=1.0, hi=0.3)
    for k_ in range(5):
        t = 0.16 + k_ * 0.17
        bx, by = lerp2(hipp, shp, t)
        r_t = 6.4 + 0.8 * t - 6.0 * t * (1 - t)
        by = by - r_t + 1.4
        h = 2.6 + (1.0 if k_ in (2, 3) else 0.0)
        cv.shape(cv.blob([(bx - 1.7, by + 1.0, 0.0), (bx + 1.2, by + 1.0, 0.0), (bx - 0.3, by - h, 0.0), (bx - 1.5, by - h + 1.0)]), BONE, z=9, sd=0.6, hi=0.25, ol=0.85)
    # dumanlı yele: boyun üstünden geriye taşar, uçları kor
    hy0_ = p.get('hy', 0.0)
    for k_ in range(6):
        t = k_ / 5
        bx, by = lerp2((shp[0] - 4, shp[1] - 6.6), (shp[0] + 7, shp[1] - 9.0 + hy0_), t)
        ang = math.pi * 1.15 + math.sin(ph - 0.8 + k_ * 1.3) * 0.16 + p.get('mane', 0.0)
        L = 6.5 + (k_ % 2) * 3.0 - t * 2.0
        st = chain((bx, by), 4, L / 4, ang, 0.16, ph - 0.8 + k_, 0.25)
        cv.shape(ik.taper_path([cv.W(q) for q in st], cv.u(2.6), (0.15, 0.85)), SMOKE, z=11 + k_ * 0.3, sd=0.9, hi=0.3, ol=0.75)
        if k_ % 2:
            cv.fill(ik.taper_path([cv.W(q) for q in st[-2:]], cv.u(1.4), (0.0, 0.9)), EMBER, z=11.1 + k_ * 0.3, glow=EMBER_GLOW)
    # ---- boyun + baş
    head = (shp[0] + 9.5, shp[1] - 5.5 + hy0_)
    nb = (shp[0] + 2, shp[1] - 3)
    hx_, hy_ = head
    ear = p.get('ear', 0.0) + math.sin(ph - 1.2) * 0.12
    for (ox, m, zz, ln) in ((-2.6, FURK_B, 7.6, 6.4), (-0.6, FURK, 15.0, 6.8)):
        e0 = (hx_ + ox, hy_ - 2.8)
        a = -math.pi * 0.5 - 0.45 - ear
        tip = (e0[0] + math.cos(a) * ln, e0[1] + math.sin(a) * ln)
        det = []
        if m is FURK:
            det = [('col', cv.blob([(e0[0] - 0.8, e0[1] + 0.4), (e0[0] + 0.9, e0[1]), (lerp2(e0, tip, 0.65)[0], lerp2(e0, tip, 0.65)[1], 0.0)]), (0.55, 0.16, 0.08))]
        cv.shape(cv.blob([(e0[0] - 2.0, e0[1] + 1.0), (tip[0], tip[1], 0.0), (e0[0] + 2.0, e0[1] + 0.2)]), m, z=zz, sd=1.4, details=det)
    sn = (hx_ + 9.0, hy_ + 1.9)       # v1'den kısa ve kalın burun (timsah değil kurt)
    jd = jaw * 3.6
    j1 = (hx_ + 8.0, hy_ + 4.0 + jd)
    # ağız içi (kor gibi yanar) ve dişler
    mouth = cv.blob([(hx_ + 2.5, hy_ + 2.0), (sn[0] - 0.5, sn[1] + 0.9), (j1[0], j1[1] - 0.6), (hx_ + 2.5, hy_ + 3.4 + jd * 0.4)])
    cv.fill(mouth, (0.85, 0.32, 0.08), z=7.0, glow=(0.42, 0.13, 0.02))
    if jaw > 0.15:
        for i in range(3):
            x = hx_ + 4.6 + i * 1.8
            cv.fill(cv.blob([(x - 0.45, hy_ + 2.0), (x + 0.45, hy_ + 2.0), (x, hy_ + 3.1, 0.0)]), BONE.base, z=7.2)
            x2 = hx_ + 4.8 + i * 1.6
            yb = hy_ + 2.6 + jd * (0.55 + i * 0.12) + 0.6
            cv.fill(cv.blob([(x2 - 0.4, yb), (x2 + 0.4, yb), (x2, yb - 1.0, 0.0)]), BONE.base, z=7.2)
    cv.shape(cv.limb([(hx_ + 1.6, hy_ + 3.0), j1], [1.9, 1.0]), FURK_B, z=7.5, sd=0.8)
    neck = cv.capsule(nb, head, 5.0, 3.9)
    ruff = [cv.blob(t) for t in _tufts([(hx_ - 2.5, hy_ + 2.8), (hx_ - 4.2, hy_ + 1.2), (hx_ - 0.8, hy_ + 3.6)], math.pi * 0.72, 3.0, 2.2)]
    skull = cv.ellipse((hx_ - 0.3, hy_), 5.5, 4.8, -0.1)
    snout = cv.capsule((hx_ + 1.8, hy_ + 0.4), sn, 3.6, 2.2)
    headp = ik.union(neck, skull, snout, *ruff)
    hdet = [('ink', [(hx_ + 3.0, hy_ + 2.0), (hx_ + 7.0, hy_ + 2.3), (sn[0] - 0.4, sn[1] + 0.8)], 1.4, (0.1, 0.5))]
    cv.shape(headp, FURK, z=8, sd=2.6, hi=0.45, details=hdet, cast=0.8)
    # kemik kafa zırhı: alın plakası + burun sırtı
    cv.shape(cv.blob([(hx_ - 2.8, hy_ - 4.0), (hx_ + 2.8, hy_ - 4.6), (hx_ + 5.0, hy_ - 2.2, 0.0), (hx_ + 0.4, hy_ - 1.5), (hx_ - 2.2, hy_ - 1.8)]),
             BONE, z=14, sd=1.2, hi=0.35, details=[('ink', [(hx_ - 1.0, hy_ - 3.6), (hx_ + 0.4, hy_ - 2.2)], 1.0)])
    cv.shape(cv.ellipse((sn[0] + 0.4, sn[1] - 0.2), 1.2, 1.0), Ink('#1a1820', '#0c0b10', '#5a5866'), z=24, sd=0.4, hi=0.2, ol=0.7)
    # göz: kara çukur içinde kor
    cv.fill(cv.ellipse((hx_ + 2.2, hy_ - 1.1), 2.2, 1.45), INK, z=24)
    cv.fill(cv.blob([(hx_ + 0.8, hy_ - 1.0, 0.0), (hx_ + 2.4, hy_ - 1.8), (hx_ + 3.8, hy_ - 0.8, 0.0), (hx_ + 2.2, hy_ - 0.4)]), EMBER_HOT, z=28, glow=EMBER_GLOW)
    # kırık zincirli tasma
    dx, dy = head[0] - nb[0], head[1] - nb[1]
    ln_ = math.hypot(dx, dy) + 1e-6
    nx, ny = -dy / ln_, dx / ln_
    cc = lerp2(nb, head, 0.5)
    a0 = (cc[0] - nx * 4.6, cc[1] - ny * 4.6)
    a1 = (cc[0] + nx * 4.6, cc[1] + ny * 4.6)
    cv.shape(cv.blob([a0, (cc[0] + (head[0] - nb[0]) * 0.08, cc[1] + (head[1] - nb[1]) * 0.08), a1, (cc[0] - (head[0] - nb[0]) * 0.12, cc[1] - (head[1] - nb[1]) * 0.12)]), RUST, z=16, sd=0.9, hi=0.35,
             details=[('col', cv.ellipse((cc[0] + nx * 4.6 * s_, cc[1] + ny * 4.6 * s_), 0.55, 0.55), IRON.hi) for s_ in (-0.25, 0.25, 0.75)])
    sw = math.sin(ph - 0.6) * 0.35 + tilt * 1.5 + p.get('chain', 0.0)
    q = a1
    for i in range(3):
        nq = (q[0] + math.sin(sw - i * 0.15) * 2.0, q[1] + math.cos(sw - i * 0.15) * 2.0)
        m = IRON if i % 2 == 0 else RUST
        cv.shape(cv.ellipse(lerp2(q, nq, 0.5), 1.0 if i % 2 == 0 else 0.8, 1.3 if i % 2 == 0 else 1.2,
                            math.atan2(nq[1] - q[1], nq[0] - q[0]) + math.pi / 2), m, z=17 + i, sd=0.5, hi=0.3, ol=0.8)
        q = nq
    legs(True)
    if sq:
        cv.pop()
    return {'mouth': ((hx_ + 9.4) * sqx, (hy_ + 2.6 + jd * 0.5) * sqy)}


SHADE = dict(outer=0.5, rim=0.9, rim_col=(0.62, 0.7, 1.0), rim_dir=(0.55, -0.85), rim_w=1.6, form=(6.0, (0.72, 0.7, 0.86)))


def render_frame(anim, i, ss=3):
    n, fn, loop, arm = ANIMS[anim]
    p = fn(i / n)
    cv = ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
