"""v39: Ağu Kurbağası (kimlik agu_kurbagasi; Şahmeran mağaralarının dev zehir kurbağası, yapay zekâ "gasser") —
mürekkep-cel tam gövde.

Kocaman, bodur kurbağa: zeytin ve hardal benekli deri, üstünde ışıyan zehir yeşili siğiller ve irin kabarcıkları;
iri altın gözler, YATAY göz bebekleri; geniş ağız; şişirilebilen kocaman gırtlak kesesi (soluk sarı-yeşil, şiştikçe
ışır); sırtında taç gibi gölet yosunu sarkıntıları ve küçük mantarlar; kalın arka bacaklar.

Hücre 320x224 doku pikseli = dünya 80 x 56 (doku 4), ayak (24, 52). Gövde 40 x 30.
Satırlar: idle 8 (gırtlak kesesi atar, göz kırpar), move 6 (ağır sıçrayışlar, vx 60), hurt 3,
  atk_cloud 9 (kese kocaman şişer ve ışır -> önüne büyük yeşil zehir bulutu üfler -> kese söner),
  atk_bomb 8 (geriye kalkar, yanaklar şişer -> yukarı-ileri bir zehir topağı tükürür),
  atk_tongue 8 (yere çöker, ağız aralık -> uzun pembe-mor dil dümdüz ileri, yapışkan uçlu; etkin karelerde gergin
  durur, sonra geri çekilir).
Çapa 'mouth' her karede; 'hand' = dil ucu (dil etkin karelerinde), öteki karelerde ağız.
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import lerp2
import bosskit as bk
import yaratik_govde as yg
import yaratik_ink_kit as yk
import ucan_v29 as u29
from ucan_v29 import pose_at

TEX = 4.0
CELL = (320, 224)       # dünya 80 x 56
FEET = (96, 208)        # dünya (24, 52)

SKIN = Ink('#7c8a36', '#3a4422', '#aab650', '#1e2414', name='zeytin deri')
SKIN_B = SKIN.darker(0.72)
BELLY = Ink('#c8b45a', '#6e6634', '#ecdc8a', '#3a3420', name='hardal karın')
MOTTLE = (0.80, 0.64, 0.22)
MOTTLE_D = (0.30, 0.34, 0.16)
SAC = Ink('#d8e48a', '#8a9a4e', '#f6ffc4', '#4a5430', name='gırtlak kesesi')
WART = (0.62, 1.0, 0.32)
WART_GLOW = (0.35, 0.95, 0.1)
EYE_G = (1.0, 0.78, 0.18)
EYE_HOT = (1.0, 0.94, 0.55)
EYE_GLOW = (0.95, 0.6, 0.05)
WEED = Ink('#3e6a3a', '#1c3424', '#66984e', name='gölet yosunu')
STEM = Ink('#e4dcc0', '#8e8670', '#fffbe8', name='mantar sapı')
CAP = Ink('#d0782e', '#6c3420', '#f6b060', name='mantar şapkası')
CAP2 = Ink('#9ad8c0', '#3a7a74', '#e0fff4', name='ışıyan mantar')
MOUTH_IN = (0.30, 0.06, 0.10)
TONGUE = Ink('#c0548e', '#5e2048', '#ec90c0', '#30102a', name='dil')
GAS = Ink('#86c840', '#3c6a2a', '#c8f080', '#1e3a18', name='zehir bulutu')
GLOB = Ink('#9ee048', '#3e7a24', '#e4ff9a', name='zehir topağı')


def add(p, v, k=1.0):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


def polar(p, a, r):
    return (p[0] + math.cos(a) * r, p[1] + math.sin(a) * r)


REST = dict(hx=0.0, hy=0.0, rot=0.0, sx=1.0, sy=1.0, breath=0.0, ext=0.0, fr=0.0,
            sac=0.0, jaw=0.0, cheek=0.0, lid=0.0, glow=0.5, tl=0.0, tty=0.0,
            cloud=0.0, glob=0.0, gx=0.0, gy=0.0, drip=0.0, jit=(0.0, 0.0), squint=0.0)

PIV = (4.0, 0.0)
MOUTH = (24.0, -12.5)
HINGE = (9.0, -11.0)


# ------------------------------------------------------------ parçalar
def _hind(cv, p, near):
    """Kalın arka bacak: oturuşta katlı (ayak öne), sıçrayışta geriye uzanır."""
    e = p['ext']
    m = SKIN if near else SKIN_B
    dz = 0.0 if near else -20.0
    off = (0.0, 0.0) if near else (5.0, -1.0)
    hip = add((-8.0, -12.0), off)
    knee = add(lerp2((-17.0, -6.0), (-15.0, -7.0), e), off)
    ank = add(lerp2((-10.0, -2.0), (-24.0, -3.0), e), off)
    toe = add(lerp2((0.0, -0.5), (-32.0, 0.0), e), off)
    thigh = bk.muscle(cv, hip, knee, 7.0, 4.6, front=1.5, back=1.0, at=0.4, knob=0.6)
    shin = bk.muscle(cv, knee, ank, 4.0, 2.6, front=0.4, back=0.8, at=0.3)
    det = [('col', cv.ellipse(lerp2(hip, knee, 0.5), 2.0, 1.4, 0.4), MOTTLE), ('col', cv.ellipse(lerp2(knee, ank, 0.4), 1.2, 0.8), MOTTLE)] if near else []
    cv.shape(ik.union(thigh, shin), m, z=-6 + dz, sd=2.2, hi=0.35 if near else 0.0, details=det, bounce=0.3)
    # perdeli uzun parmaklar
    a = math.atan2(toe[1] - ank[1], toe[0] - ank[0])
    tips = [polar(toe, a + k * 0.35, 1.5) for k in (-1, 0, 1)]
    web = cv.blob([polar(ank, a + 1.6, 1.6), tips[0], add(lerp2(tips[0], tips[1], 0.5), (math.cos(a), math.sin(a)), -1.2), tips[1],
                   add(lerp2(tips[1], tips[2], 0.5), (math.cos(a), math.sin(a)), -1.2), tips[2], polar(ank, a - 1.6, 1.6)])
    cv.shape(web, m, z=-5.8 + dz, sd=0.9, hi=0.2 if near else 0.0)
    for t in tips:
        cv.shape(cv.ellipse(t, 0.9, 0.9), m, z=-5.7 + dz, sd=0.3, ol=0.6)


def _front(cv, p, near):
    m = SKIN if near else SKIN_B
    r = p['fr']
    sh = (12.0, -8.0) if near else (7.0, -8.0)
    hd = (16.5 + r * 3.0, 0.0 - r * 2.0) if near else (10.5 + r * 2.0, -0.5 - r * 1.5)
    el = (sh[0] + (hd[0] - sh[0]) * 0.3 - 1.5, (sh[1] + hd[1]) * 0.5 + 0.5)
    cv.shape(cv.limb([sh, el, hd], [3.0, 2.2, 1.6]), m, z=(14 if near else -10), sd=1.2, hi=0.25 if near else 0.0)
    for k in (-1, 0, 1, 2):   # yayık parmaklar, uçlarda yuvarlak yastık
        tip = polar(hd, -0.1 + k * 0.55 + (0.3 if not near else 0.0), 2.6)
        tip = (tip[0], min(tip[1], 0.4))
        cv.shape(cv.limb([hd, tip], [0.9, 0.7]), m, z=(14.1 if near else -9.9), sd=0.3, ol=0.7)
        cv.shape(cv.ellipse(tip, 0.75, 0.6), m, z=(14.2 if near else -9.8), sd=0.2, ol=0.6)


def _crown(cv, p, ph):
    """Sırtta taç: sarkan gölet yosunu + küçük mantarlar (biri ışır)."""
    sw = math.sin(ph) * 0.6 - p['rot'] * 3.0 + p['hy'] * -0.15
    for k, (x, y, L) in enumerate(((-15.0, -22.0, 7.0), (-11.0, -25.0, 9.0), (-6.0, -26.5, 6.0), (-18.0, -18.0, 6.5), (-2.0, -27.0, 5.0))):
        pts = [(x, y), (x - 1.5 + sw * 0.4, y + L * 0.45), (x - 2.5 + sw, y + L)]
        cv.shape(ik.taper_path([cv.W(q) for q in pts], cv.u(1.6), (0.1, 0.85)), WEED, z=6 + k * 0.01, sd=0.4, hi=0.2, ol=0.7)
    for k, (x, y, s, mat) in enumerate(((-9.0, -26.5, 1.0, CAP), (-4.0, -27.6, 0.8, CAP2), (-13.0, -24.5, 0.75, CAP), (0.5, -27.0, 0.6, CAP))):
        top = (x + 0.3, y - 2.6 * s)
        cv.shape(cv.capsule((x, y), top, 0.55 * s, 0.45 * s), STEM, z=7 + k * 0.02, sd=0.3, ol=0.7)
        cap = cv.blob([(top[0] - 2.1 * s, top[1] + 0.5 * s), (top[0] - 1.2 * s, top[1] - 1.3 * s), (top[0] + 0.4 * s, top[1] - 1.8 * s),
                       (top[0] + 2.0 * s, top[1] - 0.6 * s), (top[0] + 2.2 * s, top[1] + 0.5 * s, 0.0), (top[0] - 2.2 * s, top[1] + 0.6 * s, 0.0)])
        glow = (0.1, 0.4, 0.35) if mat is CAP2 else None
        cv.shape(cap, mat, z=7.01 + k * 0.02, sd=0.5, hi=0.3, ol=0.75, glow=glow,
                 details=[('col', cv.ellipse((top[0] - 0.6 * s, top[1] - 0.6 * s), 0.35 * s, 0.3 * s), mat.hi)])
        if mat is CAP2:
            yk.glow_soft(cv, top, 2.8, (0.3, 1.0, 0.8), z=7.2, alpha=0.5)


WARTS = [(-14.0, -14.0, 1.0), (-9.0, -19.0, 1.3), (-3.0, -22.0, 0.9), (2.0, -18.0, 1.1), (7.0, -21.5, 0.8), (-12.0, -8.0, 0.9), (-5.0, -12.0, 1.4),
         (1.0, -10.5, 0.8), (6.0, -14.0, 1.0), (-17.0, -12.0, 0.7), (-1.0, -15.5, 0.7), (10.0, -17.0, 0.7)]
PUST = [(-7.0, -16.0, 1.7), (3.5, -21.0, 1.5), (-15.0, -18.0, 1.3), (5.0, -11.5, 1.2)]
MOT = [(-10.0, -14.0, 3.5, 2.4, 0.3), (0.0, -20.0, 4.0, 2.0, -0.2), (-16.0, -9.0, 2.6, 2.0, 0.6), (4.0, -13.0, 3.0, 2.0, 0.2), (12.0, -19.5, 2.4, 1.6, -0.4),
       (-4.0, -8.0, 2.8, 1.8, 0.0)]


def _gas(cv, c, r, z, seed, glow=None):
    """Yumuşak zehir bulutu topağı: üst üste binen yuvarlak loblar (tek kontur), iç kıvrım çizgileri, ışıyan sporlar."""
    rng = np.random.default_rng(seed)
    parts = [cv.ellipse(c, r * 0.75, r * 0.65)]
    for k in range(7):
        a = k / 7 * math.tau + rng.uniform(-0.25, 0.25)
        rr = r * rng.uniform(0.32, 0.45)
        parts.append(cv.ellipse(polar(c, a, r - rr), rr, rr * 0.92))
    path = ik.union(*parts)
    det = []
    for k in range(3):
        a = rng.uniform(0, math.tau)
        q = polar(c, a, r * 0.35)
        det.append(('ink', [(q[0] - r * 0.25, q[1] + r * 0.06), (q[0], q[1] - r * 0.14), (q[0] + r * 0.22, q[1] + r * 0.05)], 1.0, (0.3, 0.3)))
    cv.shape(path, GAS, z=z, sd=r * 0.3, hi=r * 0.1, ol=0.8, glow=glow, details=det)


def draw(cv, p, ph):
    # ---------------- bulut / topak (dünyada, gövde dönüşümünden bağımsız)
    u29.body_xf(cv, PIV, p['rot'], p['sx'], p['sy'], (p['hx'] + p['jit'][0], p['hy'] + p['jit'][1]))
    br = p['breath']
    _hind(cv, p, False)
    _front(cv, p, False)
    # ---------------- gövde (üst çene ağız çizgisinde biter)
    body = cv.blob([MOUTH, (23.5, -16.5), (19.0, -21.5), (13.0, -24.0), (5.0, -25.5 - br * 0.3), (-4.0, -27.0 - br * 0.4), (-13.0, -24.5), (-19.5, -16.0),
                    (-20.0, -7.0), (-14.0, -2.0), (-4.0, -1.2), (6.0, -1.6), (10.0, -4.0), HINGE, (16.0, -11.8)])
    det = [('col', cv.ellipse((x, y), rx, ry, a), MOTTLE) for x, y, rx, ry, a in MOT]
    det += [('col', cv.ellipse((x + 0.8, y + 0.6), rx * 0.45, ry * 0.4, a), MOTTLE_D) for x, y, rx, ry, a in MOT[::2]]
    det += [('ink', [(-17.0, -6.0), (-10.0, -3.0), (-2.0, -2.0)], 1.0, (0.4, 0.5)),
            ('ink', [(15.0, -21.0), (19.0, -18.5)], 0.9, (0.3, 0.4))]
    cv.shape(body, SKIN, z=0, sd=3.2, hi=0.6, details=det, bounce=0.35, hatch=0.3, cast=0.8)
    # karın (hardal), gövdenin alt kenarı
    cv.shape(ik.isect(body, cv.ellipse((0.0, -2.0), 13.0, 4.0)), BELLY, z=0.5, sd=1.2, hi=0.0, ol=0.0)
    # siğiller (ışıyan) + irin kabarcıkları
    gl = 0.6 + 0.4 * p['glow']
    for k, (x, y, r) in enumerate(WARTS):
        cv.shape(cv.ellipse((x, y), r, r * 0.85), SKIN, z=1 + k * 0.01, sd=r * 0.5, hi=r * 0.25, ol=0.6,
                 details=[('col', cv.ellipse((x - r * 0.15, y - r * 0.2), r * 0.45, r * 0.4), WART)], glow=None)
        cv.fill(cv.ellipse((x - r * 0.15, y - r * 0.2), r * 0.42, r * 0.36), WART, z=1.005 + k * 0.01, glow=tuple(c * gl * 0.7 for c in WART_GLOW))
    for k, (x, y, r) in enumerate(PUST):
        rr = r * (1.0 + 0.12 * math.sin(ph * 2 + k))
        cv.shape(cv.ellipse((x, y), rr, rr * 0.9), Ink('#a8e85a', '#4a8a2a', '#efffb8'), z=1.5 + k * 0.01, sd=rr * 0.4, hi=rr * 0.3, ol=0.8,
                 glow=tuple(c * gl for c in WART_GLOW))
        yk.glow_soft(cv, (x, y), rr * 2.4, WART_GLOW, z=1.6, alpha=0.4 * gl)
    _crown(cv, p, ph)
    # ---------------- ağız: alt çene menteşe çevresinde açılır, altında gırtlak kesesi
    ja = p['jaw'] * 0.3
    c_, s_ = math.cos(ja), math.sin(ja)

    def J(q):
        x, y = q[0] - HINGE[0], q[1] - HINGE[1]
        return (HINGE[0] + x * c_ - y * s_, HINGE[1] + x * s_ + y * c_)
    if p['jaw'] > 0.05:
        cv.fill(cv.blob([HINGE, (16.0, -11.8), MOUTH, J((24.0, -11.5)), J((16.0, -10.5))]), MOUTH_IN, z=2.0)
    lower = [J(q) for q in ((24.0, -12.0), (23.0, -9.0), (19.0, -6.0), (13.0, -4.0), (9.0, -4.0), (8.0, -8.0))]
    cv.shape(cv.blob([J(HINGE), J((16.0, -11.6))] + lower), SKIN, z=2.1, sd=1.6, hi=0.25,
             details=[('col', cv.ellipse(J((16.0, -6.5)), 4.0, 2.0, ja), BELLY.base)])
    # dudak çizgisi (geniş sırıtış)
    cv.stroke([HINGE, (16.0, -11.8), MOUTH], 1.6, z=2.3, col=INK, taper=(0.6, 0.2))
    # gırtlak kesesi
    sac = p['sac']
    if sac > 0.02:
        rx, ry = 3.0 + 9.0 * sac, 2.4 + 7.4 * sac
        cc = J((15.0 + 4.0 * sac, -4.0 + 2.0 * sac))
        cc = (cc[0], min(cc[1], 1.0 - ry))
        sg = (0.35 * sac, 0.5 * sac, 0.08 * sac)
        cv.shape(cv.ellipse(cc, rx, ry), SAC, z=12, sd=ry * 0.4, hi=ry * 0.15, ol=1.0, glow=sg if sac > 0.4 else None,
                 details=[('ink', [(cc[0] - rx * 0.5, cc[1] - ry * 0.2), (cc[0], cc[1] + ry * 0.1), (cc[0] + rx * 0.5, cc[1] - ry * 0.1)], 0.8, (0.4, 0.4)),
                          ('hi', cv.ellipse((cc[0] - rx * 0.3, cc[1] - ry * 0.45), rx * 0.35, ry * 0.18, -0.3))])
        if sac > 0.4:
            yk.glow_soft(cv, cc, max(rx, ry) * 1.5, (0.6, 1.0, 0.2), z=12.1, alpha=0.55 * sac)
    # yanak şişmesi (topak tükürme)
    if p['cheek'] > 0.02:
        ck = p['cheek']
        cv.shape(cv.ellipse((16.5, -13.0), 3.0 + 3.0 * ck, 2.0 + 2.6 * ck), SKIN, z=2.5, sd=1.2, hi=0.4, ol=0.9,
                 details=[('col', cv.ellipse((16.0, -13.5), 1.2 + ck, 0.9 + ck * 0.7), MOTTLE)])
    # ---------------- göz: başın tepesinde kabarık, altın, yatay bebek
    ec = (14.5, -22.5)
    cv.shape(cv.ellipse((ec[0] - 0.5, ec[1] + 0.8), 5.6, 4.8), SKIN, z=3.0, sd=1.6, hi=0.5)
    lid = max(p['lid'], p['squint'] * 0.5)
    eg = 0.4 + 0.6 * p['glow']
    yk.glow_soft(cv, ec, 6.0, EYE_GLOW, z=3.05, alpha=0.3 * eg)
    cv.fill(cv.ellipse(ec, 4.0, 3.7), (0.12, 0.08, 0.04), z=3.1)
    cv.fill(cv.ellipse(ec, 3.6, 3.3), EYE_G, z=3.12, glow=tuple(c * 0.5 * eg for c in EYE_GLOW))
    cv.fill(cv.ellipse((ec[0] - 0.8, ec[1] - 0.9), 2.0, 1.4), EYE_HOT, z=3.13, glow=tuple(c * 0.4 * eg for c in EYE_HOT))
    pw = 2.6 * (1.0 - 0.35 * p['glow'])
    cv.fill(cv.ellipse((ec[0] + 0.4, ec[1] + 0.2), pw, 0.95), (0.04, 0.03, 0.02), z=3.14)   # YATAY bebek
    cv.fill(cv.ellipse((ec[0] - 1.4, ec[1] - 1.5), 0.7, 0.5), (1, 1, 1), z=3.15)
    for k in range(5):   # altın göz damarları
        a = k / 5 * math.tau + 0.4
        cv.stroke([polar(ec, a, 1.8), polar(ec, a + 0.2, 3.0)], 0.6, z=3.13, col=(0.7, 0.42, 0.08), taper=(0.2, 0.7))
    if lid > 0.02:   # göz kapağı yukarıdan iner
        top = ec[1] - 4.2
        yb = top + 8.4 * lid
        cv.shape(cv.blob([(ec[0] - 4.6, ec[1] - 1.0), (ec[0] - 2.5, top), (ec[0] + 2.5, top), (ec[0] + 4.6, ec[1] - 1.0),
                          (ec[0] + 4.3, min(yb, ec[1] + 3.8)), (ec[0], min(yb + 0.8, ec[1] + 4.2)), (ec[0] - 4.3, min(yb, ec[1] + 3.8))]),
                 SKIN, z=3.2, sd=1.0, hi=0.3, ol=1.0)
    else:
        cv.stroke([(ec[0] - 4.2, ec[1] - 1.8), (ec[0] - 1.0, ec[1] - 4.0), (ec[0] + 3.0, ec[1] - 3.4)], 1.4, z=3.2, col=INK, taper=(0.3, 0.6))
    cv.fill(cv.ellipse((22.8, -16.2), 0.6, 0.4), INK, z=3.3)   # burun deliği
    # ---------------- yakın bacaklar
    _hind(cv, p, True)
    _front(cv, p, True)
    # ---------------- dil
    mouth = u29.to_world(cv, MOUTH)
    tipw = mouth
    if p['tl'] > 0.5:
        L = p['tl']
        st = (MOUTH[0] - 1.0, MOUTH[1] + 0.8)
        tip = (st[0] + L, st[1] + p['tty'])
        pts = [st, (st[0] + L * 0.3, st[1] + 0.6 + p['tty'] * 0.2), (st[0] + L * 0.7, st[1] + 0.5 + p['tty'] * 0.6), tip]
        cv.shape(ik.taper_path([cv.W(q) for q in pts], cv.u(3.4), prof=lambda u: 1.0 - 0.35 * u), TONGUE, z=16, sd=0.8, hi=0.3, ol=1.0,
                 details=[('ink', [lerp2(st, tip, 0.1), lerp2(st, tip, 0.8)], 0.7, (0.2, 0.6))])
        cv.shape(cv.blob([(tip[0] - 1.5, tip[1] - 2.2), (tip[0] + 1.6, tip[1] - 2.6), (tip[0] + 3.0, tip[1] - 0.4), (tip[0] + 2.2, tip[1] + 2.2),
                          (tip[0] - 0.8, tip[1] + 2.4), (tip[0] - 1.8, tip[1] + 0.4)]), TONGUE, z=16.2, sd=1.2, hi=0.5, ol=1.0,
                 details=[('col', cv.ellipse((tip[0] + 0.6, tip[1] - 0.2), 1.6, 1.4), (0.95, 0.62, 0.86))])
        for k in range(2):   # yapışkan damlalar
            q = (tip[0] - 0.5 + k * 1.8, tip[1] + 2.2)
            cv.shape(cv.blob([(q[0] - 0.4, q[1]), (q[0] + 0.4, q[1]), (q[0], q[1] + 1.6 + k * 0.6, 0.0)]), Ink('#f0b0d8', '#9a5080', '#fff0fa'),
                     z=16.3, sd=0.2, ol=0.6)
        tipw = u29.to_world(cv, (tip[0] + 1.0, tip[1]))
    cv.pop()
    # ---------------- zehir bulutu (dünyada)
    k = p['cloud']
    if k > 0.02:
        a = 1.0 - max(0.0, k - 1.0)
        for i in range(4):
            u = (i + 1) / 4
            c = (mouth[0] + 2.0 + 26.0 * u * min(1.0, k * 1.2), mouth[1] + 1.0 - 5.0 * u * min(k, 1.2) + math.sin(i * 2.1) * 2.5)
            r = (3.5 + 10.0 * u) * min(1.0, 0.35 + 0.75 * k) * (1.0 - 0.25 * max(0.0, k - 1.0))
            if c[0] + r > 54.0:
                c = (54.0 - r, c[1])
            if c[1] - r < -50:
                c = (c[0], -50 + r)
            if c[1] + r > 0.5:
                c = (c[0], 0.5 - r)
            yk.glow_soft(cv, c, r * 1.5, (0.4, 0.9, 0.1), z=29.9, alpha=0.45 * a)
            _gas(cv, c, r, 30 + i * 0.1, 3 + i, glow=(0.1, 0.28, 0.03) if a > 0.5 else None)
            u29.flecks(cv, c, 4, r * 1.0, r * 1.5, GAS.hi, 30.4, seed=7 + i, s0=0.3, s1=0.6, glow=WART_GLOW)
        if k < 0.8:   # ağızdan çıkan akım
            yk.wisp(cv, mouth, -0.05, 10.0, 3.2, GAS, 29.5, ph=ph, curl=0.4, glow=(0.3, 0.8, 0.1), glow_a=0.4)
    if p['glob'] > 0.5:
        g = (p['gx'], p['gy'])
        u29.speed_lines(cv, g, (0.7, -0.7), n=4, L=8, spread=4, w=1.4, col=GAS.shadow, alpha=0.6, z=31, seed=4, glow=(0.2, 0.5, 0.05))
        yk.glow_soft(cv, g, 6.0, (0.5, 1.0, 0.15), z=32, alpha=0.7)
        cv.shape(cv.blob([(g[0] - 2.6, g[1] + 0.6), (g[0] - 1.2, g[1] - 2.6), (g[0] + 2.2, g[1] - 2.6), (g[0] + 3.0, g[1] + 0.2), (g[0] + 1.2, g[1] + 2.6),
                          (g[0] - 2.2, g[1] + 2.4)]), GLOB, z=32.1, sd=1.0, hi=0.5, ol=1.0, glow=(0.25, 0.55, 0.06),
                 details=[('col', cv.ellipse((g[0] - 0.6, g[1] - 0.8), 0.9, 0.7), GLOB.hi)])
        for i in range(3):
            q = (g[0] - 3.5 - i * 2.2, g[1] + 2.5 + i * 1.6)
            cv.fill(cv.ellipse(q, 0.8 - i * 0.15, 0.8 - i * 0.15), GLOB.base, z=32.2, glow=WART_GLOW)
    if p['drip'] > 0:   # ağızdan sızan zehir
        for i in range(2):
            q = (mouth[0] - 2.0 - i * 2.5, mouth[1] + 2.0 + p['drip'] * (1.5 + i))
            cv.shape(cv.blob([(q[0] - 0.5, q[1] - 1.0), (q[0] + 0.5, q[1] - 1.0), (q[0] + 0.6, q[1] + 0.6), (q[0], q[1] + 1.6, 0.0), (q[0] - 0.6, q[1] + 0.6)]),
                     GLOB, z=33, sd=0.3, ol=0.6, glow=WART_GLOW)
    hand = tipw if p['tl'] > 0.5 else mouth
    if p['glob'] > 0.5:
        hand = (p['gx'], p['gy'])
    return {'mouth': mouth, 'hand': hand}


# ------------------------------------------------------------ animasyon tabloları
S2 = math.tau


def _k(t, keys):
    return pose_at(t, keys, base=REST)


def _idle(t):
    s = math.sin(S2 * t)
    pulse = 0.5 + 0.5 * math.sin(S2 * t * 2)
    blink = 1.0 if int(round(t * 8)) == 3 else 0.0
    return dict(REST, breath=0.5 + 0.5 * s, sy=1.0 + 0.015 * s, sx=1.0 - 0.01 * s, sac=0.12 + 0.3 * pulse, glow=0.4 + 0.4 * pulse, lid=blink,
                rot=0.01 * s)


_MOVE = [(0.0, dict(sy=0.88, sx=1.1, ext=0.0, rot=0.05, glow=0.5), 'l'),
         (1 / 6, dict(hy=-5.0, sy=1.14, sx=0.9, ext=1.0, rot=-0.12, fr=0.6, sac=0.2), 'o'),
         (2 / 6, dict(hy=-10.0, sy=1.08, sx=0.95, ext=0.8, rot=-0.04, fr=0.8), 'o'),
         (3 / 6, dict(hy=-7.0, sy=1.02, sx=0.98, ext=0.4, rot=0.1, fr=1.0), 'i2'),
         (4 / 6, dict(hy=0.0, sy=0.82, sx=1.16, ext=0.0, rot=0.06, fr=0.2, sac=0.35, jit=(0.0, 0.3)), 'i'),
         (5 / 6, dict(hy=0.0, sy=0.94, sx=1.05, ext=0.0, rot=0.02, fr=0.0, sac=0.15, jit=(0.0, 0.0)), 'o'),
         (1.0, dict(sy=0.88, sx=1.1, ext=0.0, rot=0.05, sac=0.1), 'io')]

_HURT = [(0.0, dict(rot=-0.2, hx=-2.5, sx=1.08, sy=0.9, jaw=0.6, squint=1.0, lid=0.6, sac=0.5, glow=0.2, jit=(-1.0, 0.0)), 'l'),
         (0.5, dict(rot=-0.1, hx=-3.5, sx=1.0, sy=1.03, jaw=0.3, lid=0.3, sac=0.3, jit=(-0.5, 0.0)), 'o'),
         (1.0, dict(rot=0.0, hx=-3.0, sx=1.0, sy=1.0, jaw=0.0, squint=0.0, lid=0.0, sac=0.1, glow=0.5, jit=(0.0, 0.0)), 'io')]

_CLOUD_TS = [0.0, 0.1, 0.2, 0.32, 0.4, 0.45, 0.58, 0.75, 0.88]
_CLOUD = [(0.0, dict(), 'l'),
          (0.1, dict(sac=0.4, glow=0.7, rot=-0.04, sy=1.03), 'o'),
          (0.2, dict(sac=0.75, glow=0.9, rot=-0.1, sy=1.06, sx=0.97, squint=0.4), 'o'),
          (0.32, dict(sac=1.0, glow=1.0, rot=-0.16, sy=1.08, sx=0.96, squint=0.6, hx=-1.0), 'o'),     # derin kurulma (W): kese en büyük, ışıyor
          (0.4, dict(sac=0.85, rot=0.04, sy=1.0, sx=1.03, jaw=0.7, hx=0.5, squint=0.2), 'i'),
          (0.45, dict(sac=0.55, rot=0.1, sy=0.94, sx=1.08, jaw=1.0, hx=1.5, cloud=0.35, glow=1.0), 'i'),   # TEMAS (C): bulut üflenir
          (0.58, dict(sac=0.25, rot=0.12, jaw=0.9, cloud=0.8), 'o'),
          (0.75, dict(sac=0.0, rot=0.04, sy=0.97, sx=1.03, jaw=0.3, cloud=1.15, glow=0.4, drip=1.0, hx=0.5), 'o'),
          (0.88, dict(sac=0.05, rot=0.0, sy=1.0, sx=1.0, jaw=0.0, cloud=1.3, drip=0.5, hx=0.0, squint=0.0, glow=0.5), 'io'),
          (1.0, dict(sac=0.1, cloud=0.0, drip=0.0), 'h')]

_BOMB_TS = [0.0, 0.12, 0.24, 0.36, 0.46, 0.5, 0.64, 0.82]
_BOMB = [(0.0, dict(), 'l'),
         (0.12, dict(rot=-0.1, cheek=0.4, sy=1.04, sx=0.97, glow=0.7, hx=-0.5), 'o'),
         (0.24, dict(rot=-0.22, cheek=0.8, sy=1.08, sx=0.95, glow=0.9, hx=-1.5, ext=0.25, squint=0.5), 'o'),
         (0.36, dict(rot=-0.3, cheek=1.0, sy=1.1, sx=0.94, glow=1.0, hx=-2.0, ext=0.35, squint=0.7), 'o'),   # W
         (0.46, dict(rot=-0.12, cheek=0.6, sy=1.02, sx=1.0, jaw=0.6, hx=0.0, ext=0.2), 'i'),
         (0.5, dict(rot=-0.18, cheek=0.0, sy=1.12, sx=0.94, jaw=1.0, glob=1.0, gx=33.0, gy=-30.0, squint=0.0), 'i'),   # C: topak çıkar
         (0.64, dict(rot=-0.02, sy=0.96, sx=1.04, jaw=0.4, glob=0.0, drip=1.0, ext=0.0), 'o'),
         (1.0, dict(rot=0.0, sy=1.0, sx=1.0, jaw=0.0, drip=0.0, glow=0.5, hx=0.0), 'io')]

_TONGUE_TS = [0.0, 0.14, 0.28, 0.36, 0.48, 0.6, 0.74, 0.87]
_TL = 26.0
_TONGUE = [(0.0, dict(), 'l'),
           (0.14, dict(sy=0.9, sx=1.08, rot=0.06, jaw=0.15, squint=0.4, glow=0.8), 'o'),
           (0.28, dict(sy=0.84, sx=1.12, rot=0.1, jaw=0.3, squint=0.7, glow=1.0, hx=-1.0), 'o'),            # W: alçak çömelme, ağız aralık
           (0.36, dict(sy=1.0, sx=1.03, rot=0.04, jaw=0.75, tl=_TL, tty=0.6, hx=1.5, squint=0.0), 'i'),      # C: dil dümdüz ileri
           (0.48, dict(tl=_TL, tty=1.2, jaw=0.75), 'l'),
           (0.6, dict(tl=_TL * 0.55, tty=2.0, jaw=0.6, hx=1.0), 'io'),
           (0.74, dict(tl=0.0, tty=0.0, jaw=0.2, hx=0.5, sy=0.97), 'io'),
           (1.0, dict(jaw=0.0, hx=0.0, sy=1.0, sx=1.0, rot=0.0, glow=0.5), 'io')]


def _row(frames, fps, loop, pose, ts=None, mk=None, vx=None):
    d = dict(frames=frames, fps=fps, loop=loop, pose=pose, ts=ts, mk=mk)
    if vx:
        d['vx'] = vx
    return d


def _nl(keys):
    return lambda t: _k(t, keys)


ROWS = None


def anims_for(var='agu_kurbagasi'):
    global ROWS
    if ROWS is None:
        ROWS = {
            'idle': _row(8, 8, True, _idle),
            'move': _row(6, 10, True, _nl(_MOVE), vx=60.0),
            'hurt': _row(3, 12, False, _nl(_HURT)),
            'atk_cloud': _row(9, 10, False, _nl(_CLOUD), ts=_CLOUD_TS, mk=[0.32, 0.45, 0.62]),
            'atk_bomb': _row(8, 10, False, _nl(_BOMB), ts=_BOMB_TS, mk=[0.36, 0.5, 0.62]),
            'atk_tongue': _row(8, 10, False, _nl(_TONGUE), ts=_TONGUE_TS, mk=[0.28, 0.36, 0.6]),
        }
    return ROWS


def durum_for(var='agu_kurbagasi'):
    d = {"idle": "idle", "chase": "move", "recover": "idle", "evade": "move", "_hurt": "hurt", "_hurt_big": "hurt", "_break": "hurt"}
    for m in ('cloud', 'bomb', 'tongue'):
        for ph in ('windup', 'act', 'recover'):
            d[ph + '/' + m] = 'atk_' + m
    d['hold/tongue'] = 'atk_tongue'
    return d


def frame_time(row, i):
    if row['ts']:
        return row['ts'][i]
    if row['loop']:
        return i / row['frames']
    return i / max(1, row['frames'] - 1)


SHADE = dict(outer=0.55, rim=0.65, rim_col=(0.72, 0.86, 1.0), rim_dir=(0.6, -0.8), rim_w=1.4, form=(4.0, (0.78, 0.76, 0.88)))


def render_frame(anim, i, var='agu_kurbagasi', ss=3):
    row = anims_for(var)[anim]
    tt = frame_time(row, i)
    p = dict(row['pose'](tt))
    ph = tt * math.tau * (2 if row['loop'] else 1) + i * 0.9
    cv = yg.bake_xf(u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss))
    info = draw(cv, p, ph)
    rgba, _nm, em = cv.finish(**SHADE)
    return rgba, None, em, info
