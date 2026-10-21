"""v39: Yeraltı Cücesi (kimlik yer_cucesi; Ötüken mağaraları, yapay zekâ "burrower") — mürekkep-cel tam gövde.

Tıknaz cüce madenci: dizlerine inen örgülü pas kızılı sakal (bronz halkalı iki örgü), iri yumru burun, ağır kaşların
altında kor gözler, ezik demir madenci başlığı ve önünde amber yağ feneri (ışır), yamalı deri önlük + keseli kemer,
kalın çizmeler, ucu turkuaz kristalli (ışır) iki elle tutulan büyük kazma.

Satırlar (hücre 56 x 52 dünya, ayak (24, 49), doku 4):
  idle 6, move 8 (paytak yürüyüş, vx 70), hurt 3,
  atk_pick 8 (tepeden öne kazma savuruşu; mk), atk_throw 8 (yedek taşı omuz üstünden fırlatır; taş TEMAS karesinde
  elden çıkar; mk), dig 6 (döngüsüz: sıçrar, başüstü yere dalar; son kareler yalnızca toprak püskürmesi + tümsek),
  burrow 4 (döngü: yalnızca ilerleyen toprak tümseği, fener ışığı ve kazma ucu görünür, moloz),
  atk_emerge 8 (mk; hazırlık = şişen, çatlayan tümsek, toprağın altından fener ışığı; temas = yerden yukarı fırlayıp
  kazmayla aşağıdan yukarı vurur, taşlar uçar; toparlanma = yere iner).
'hand' çapası = kazma ucu (kristal) ya da atılan taş; her karede verilir.
Yer altı kırpması: gövde ayrı tuvalde çizilir, `gl` (dünya y) altındaki satırlar silinir, toprak / tümsek üstüne biner.
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import lerp2
import yaratik_ink_kit as yk
import yaratik_govde as yg
import ucan_v29 as u29

TEX = 4.0
CELL = (224, 208)       # dünya 56 x 52
FEET = (96, 196)        # dünya (24, 49)

# ------------------------------------------------------------------ malzemeler
SKIN = Ink('#d89a74', '#8e5244', '#f6c8a2', '#4e2a26', name='cüce teni')
NOSE = Ink('#e08a70', '#9a4440', '#ffbca0', '#52201e', name='yumru burun')
BEARD = Ink('#c0582c', '#6e2a18', '#ee8c50', '#3a120c', kind='fur', name='pas sakal')
BROW = Ink('#a84a26', '#5a2214', '#d87440', '#2e0e08', kind='fur', name='kaş')
CAP = Ink('#717684', '#353a48', '#b4bac8', '#1c1e28', kind='metal', name='demir başlık')
BRASS = Ink('#c89040', '#6a3c1a', '#f8dc90', '#38200c', kind='metal', name='pirinç')
APRON = Ink('#86563a', '#43281a', '#b48256', '#22120c', name='deri önlük')
PATCH = Ink('#a27a48', '#56402a', '#cca870', name='yama')
PATCH2 = Ink('#5e4a3a', '#2e221c', '#82705a', name='koyu yama')
SHIRT = Ink('#4c5e3e', '#252f22', '#73865a', '#141a12', name='yosun gömlek')
SHIRT_B = SHIRT.darker(0.72)
BELT = Ink('#4a3020', '#22140e', '#70503a', name='kemer')
BOOT = Ink('#4e382a', '#24180f', '#765a44', '#140c08', name='çizme')
BOOT_B = BOOT.darker(0.72)
WOOD = Ink('#9a6a3e', '#4a2c1a', '#c8945e', '#26160c', name='sap')
IRON = Ink('#7a7e8c', '#373b48', '#c0c6d4', '#1a1c26', kind='metal', name='kazma demiri')
CRYST = Ink('#5eead8', '#1e8a92', '#dcfff8', '#0e4a56', name='turkuaz kristal')
CRYST_G = (0.12, 0.85, 0.8)
EARTH = Ink('#715238', '#37261b', '#9e7a54', '#1c120d', name='toprak')
EARTH_D = Ink('#5a412e', '#2c1e16', '#7c6046', '#160e0a', name='koyu toprak')
ROCK = Ink('#9a7458', '#4a3226', '#c89c74', '#24160f', name='taş')
LAMP = (1.0, 0.82, 0.42)
LAMP_G = (1.0, 0.55, 0.1)
EMBER = (1.0, 0.66, 0.25)
EMBER_G = (1.0, 0.36, 0.05)

HIP = (0.0, -8.0)


def _d(a):
    return (math.cos(a), math.sin(a))


# ------------------------------------------------------------------ kazma
def pick(cv, g, pa, z, flip=1.0, pz=18.0, glow=1.0):
    """Kazma: g alt kavrayış, pa sapın doğrultusu (g'den başa). Sivri uç sapın saat yönündeki yanında (flip=-1 ters).
    Döner: (kristal uç, baş merkezi)."""
    d = _d(pa)
    s = (-d[1] * flip, d[0] * flip)
    butt = (g[0] - d[0] * 3.0, g[1] - d[1] * 3.0)
    c = (g[0] + d[0] * 14.0, g[1] + d[1] * 14.0)
    haft = cv.limb([butt, lerp2(butt, c, 0.5), c], [0.75, 0.7, 0.8])
    cv.shape(haft, WOOD, z=z, sd=0.5, hi=0.25, ol=0.85,
             details=[('ink', [lerp2(butt, c, 0.2), lerp2(butt, c, 0.36)], 0.7), ('ink', [lerp2(butt, c, 0.62), lerp2(butt, c, 0.74)], 0.6)])
    # sap sargısı (deri) ve demir yüzük
    cv.shape(cv.capsule(lerp2(butt, c, 0.02), lerp2(butt, c, 0.16), 0.95, 0.95), BELT, z=z + 0.05, sd=0.3, ol=0.7,
             details=[('ink', [lerp2(butt, c, 0.07 + k * 0.04), (lerp2(butt, c, 0.07 + k * 0.04)[0] + s[0] * 0.8, lerp2(butt, c, 0.07 + k * 0.04)[1] + s[1] * 0.8)], 0.6) for k in range(3)])
    # baş: sivri uç (kavisli, sapa doğru bükük) + küt çekiç ucu
    tip = (c[0] + s[0] * 7.4 - d[0] * 2.0, c[1] + s[1] * 7.4 - d[1] * 2.0)
    mid = (c[0] + s[0] * 4.0 - d[0] * 0.2, c[1] + s[1] * 4.0 - d[1] * 0.2)
    blunt = (c[0] - s[0] * 4.2 + d[0] * 0.2, c[1] - s[1] * 4.2 + d[1] * 0.2)
    head = cv.blob([(blunt[0] + d[0] * 1.3, blunt[1] + d[1] * 1.3, 0.0), (c[0] + d[0] * 1.6, c[1] + d[1] * 1.6),
                    (mid[0] + d[0] * 1.1, mid[1] + d[1] * 1.1), (tip[0], tip[1], 0.0), (mid[0] - d[0] * 0.9, mid[1] - d[1] * 0.9),
                    (c[0] - d[0] * 1.5, c[1] - d[1] * 1.5), (blunt[0] - d[0] * 1.3, blunt[1] - d[1] * 1.3, 0.0)])
    cv.shape(head, IRON, z=z + 0.2, sd=0.8, hi=0.35, ol=0.95,
             details=[('ink', [(c[0] - s[0] * 1.6 - d[0] * 0.9, c[1] - s[1] * 1.6 - d[1] * 0.9), (c[0] - s[0] * 1.6 + d[0] * 0.9, c[1] - s[1] * 1.6 + d[1] * 0.9)], 0.7),
                      ('ink', [(c[0] + s[0] * 1.6 - d[0] * 0.9, c[1] + s[1] * 1.6 - d[1] * 0.9), (c[0] + s[0] * 1.6 + d[0] * 0.9, c[1] + s[1] * 1.6 + d[1] * 0.9)], 0.7)])
    # kristal uç: sivri ucun üstüne oturtulmuş turkuaz taş
    kb = lerp2(mid, tip, 0.35)
    kt = (tip[0] + s[0] * 1.3 - d[0] * 0.4, tip[1] + s[1] * 1.3 - d[1] * 0.4)
    cry = cv.blob([(kb[0] + d[0] * 1.2, kb[1] + d[1] * 1.2, 0.0), (lerp2(kb, kt, 0.6)[0] + d[0] * 0.9, lerp2(kb, kt, 0.6)[1] + d[1] * 0.9, 0.0),
                   (kt[0], kt[1], 0.0), (lerp2(kb, kt, 0.6)[0] - d[0] * 0.9, lerp2(kb, kt, 0.6)[1] - d[1] * 0.9, 0.0), (kb[0] - d[0] * 1.1, kb[1] - d[1] * 1.1, 0.0)])
    cv.shape(cry, CRYST, z=z + 0.3, sd=0.5, hi=0.4, ol=0.8, glow=(0.05, 0.32, 0.3),
             details=[('stroke', [lerp2(kb, kt, 0.15), lerp2(kb, kt, 0.75)], 0.8, (1, 1, 1), (0.2, 0.6))])
    yk.glow_soft(cv, lerp2(kb, kt, 0.6), 2.6 * glow, CRYST_G, z=z + 0.35, alpha=0.5 * glow)
    return kt, c


def rock(cv, c, r, z, rot=0.0, glow=1.0):
    """Atılan taş: köşeli kaya yumrusu, damarında küçük turkuaz kristal."""
    pts = []
    for k in range(7):
        a = rot + k / 7 * math.tau
        rr = r * (1.0, 0.8, 0.95, 0.75, 1.05, 0.85, 0.9)[k]
        pts.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr, 0.0 if k % 2 == 0 else 1.0))
    cv.shape(cv.blob(pts), ROCK, z=z, sd=0.8, hi=0.35, ol=0.9,
             details=[('ink', [(c[0] - r * 0.5, c[1] + r * 0.1), (c[0] + r * 0.1, c[1] - r * 0.2), (c[0] + r * 0.4, c[1] + r * 0.3)], 0.7)])
    q = (c[0] + math.cos(rot - 0.8) * r * 0.45, c[1] + math.sin(rot - 0.8) * r * 0.45)
    cv.shape(cv.blob([(q[0] - 0.7, q[1] + 0.3, 0.0), (q[0] + 0.1, q[1] - 1.1, 0.0), (q[0] + 0.8, q[1] + 0.4, 0.0)]), CRYST, z=z + 0.1, sd=0.2, ol=0.6,
             glow=(0.05, 0.3, 0.28))
    yk.glow_soft(cv, q, 1.8 * glow, CRYST_G, z=z + 0.2, alpha=0.4 * glow)


# ------------------------------------------------------------------ toprak efektleri (kor solucanı da kullanır)
def mound(cv, cx, w, h, z, mat=EARTH, mat2=EARTH_D, seed=0, crack=0.0, crack_col=LAMP, crack_glow=LAMP_G, ph=0.0, lumps=5):
    """Yerdeki tümsek: üstü topaklı kubbe, taban yayvan; crack > 0 ise ışıyan çatlaklar."""
    rng = np.random.default_rng(seed)
    pts = [(cx - w * 1.15, 0.6, 0.0)]
    for k in range(lumps * 2 + 1):
        u = k / (lumps * 2)
        x = cx - w + 2 * w * u
        prof = math.sin(math.pi * u) ** 0.8
        y = -h * prof * (1.0 if k % 2 == 0 else 0.86) + rng.uniform(-0.3, 0.3) * h * 0.1 + math.sin(ph + k) * 0.25
        pts.append((x, y))
    pts.append((cx + w * 1.15, 0.6, 0.0))
    path = cv.blob(pts)
    det = []
    for k in range(lumps):
        x = cx - w * 0.7 + w * 1.4 * (k + 0.5) / lumps
        y = -h * 0.55 * math.sin(math.pi * (k + 0.5) / lumps)
        det.append(('ink', [(x - 1.2, y + 0.4), (x, y - 0.3), (x + 1.0, y + 0.5)], 0.8, (0.3, 0.3)))
    det.append(('deep', cv.blob([(cx - w * 1.15, 0.6), (cx + w * 1.15, 0.6), (cx + w * 0.8, -h * 0.18), (cx - w * 0.8, -h * 0.18)])))
    cv.shape(path, mat, z=z, sd=h * 0.35, hi=0.45, ol=0.95, details=det, hatch=0.3, fur=0.0)
    # topaklar / taşçıklar
    for k in range(lumps + 2):
        u = rng.uniform(0.1, 0.9)
        x = cx - w + 2 * w * u
        y = -h * math.sin(math.pi * u) ** 0.8 * rng.uniform(0.2, 0.9)
        r_ = rng.uniform(0.7, 1.4)
        cv.shape(cv.ellipse((x, y), r_, r_ * 0.8, rng.uniform(0, 3)), mat2 if k % 2 else ROCK, z=z + 0.2 + k * 0.01, sd=0.35, hi=0.2, ol=0.7)
    if crack > 0.02:
        for k in range(int(2 + 4 * crack)):
            a = -math.pi / 2 + rng.uniform(-1.1, 1.1)
            b = (cx + rng.uniform(-0.3, 0.3) * w, -h * 0.35)
            L = h * (0.4 + 0.6 * crack) * rng.uniform(0.6, 1.0)
            p1 = (b[0] + math.cos(a) * L * 0.5 + rng.uniform(-0.8, 0.8), b[1] + math.sin(a) * L * 0.5)
            p2 = (b[0] + math.cos(a) * L * 1.1, b[1] + math.sin(a) * L * 1.0)
            cv.stroke([b, p1, p2], 1.8 + 1.4 * crack, z=z + 0.5 + k * 0.01, col=INK, taper=(0.2, 0.8))
            cv.stroke([b, p1, p2], 0.9 + 1.0 * crack, z=z + 0.55 + k * 0.01, col=crack_col, taper=(0.2, 0.8), glow=crack_glow)
        yk.glow_soft(cv, (cx, -h * 0.5), w * (0.6 + 0.5 * crack), crack_glow, z=z + 0.6, blur=0.6, alpha=0.35 + 0.4 * crack, ry=h * 0.8)
    return path


def debris(cv, c, n, spread, height, z, seed=0, k=1.0, ang=-math.pi / 2, cone=1.2, mats=(EARTH, ROCK, EARTH_D), s0=0.5, s1=1.4, fall=0.0):
    """Saçılan toprak / taş parçaları: c'den ang yönünde koni içinde yükselen (k = uçuşun ilerlemesi 0..1)."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        a = ang + rng.uniform(-0.5, 0.5) * cone
        sp = rng.uniform(0.4, 1.0)
        dist = height * sp * k
        q = (c[0] + math.cos(a) * dist + rng.uniform(-1, 1) * spread * 0.3, c[1] + math.sin(a) * dist + fall * k * k * 8 * sp)
        r_ = rng.uniform(s0, s1)
        rr = rng.uniform(0, math.tau)
        pts = [(q[0] + math.cos(rr + j * 2.1) * r_ * (1.0 if j % 2 == 0 else 0.7), q[1] + math.sin(rr + j * 2.1) * r_ * (1.0 if j % 2 == 0 else 0.7), 0.0)
               for j in range(3)]
        cv.shape(cv.blob(pts), mats[i % len(mats)], z=z + i * 0.01, sd=0.3, hi=0.15, ol=0.7)
        if i % 3 == 0 and k > 0.1:   # uçuş izi
            back = (q[0] - math.cos(a) * 2.2, q[1] - math.sin(a) * 2.2)
            cv.stroke([back, q], 0.9, z=z - 0.1, col=INK, taper=(0.9, 0.1), alpha=0.6)


def dust(cv, c, r, z, seed=0, alpha=0.5, n=3):
    """Toz bulutu: yarı saydam topaklar (soğuk gri-kahve)."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        q = (c[0] + rng.uniform(-1, 1) * r, c[1] - rng.uniform(0, 0.6) * r)
        rr = r * rng.uniform(0.45, 0.7)
        pts = [(q[0] + math.cos(a) * rr * (1.0 if j % 2 == 0 else 0.82), q[1] + math.sin(a) * rr * 0.8 * (1.0 if j % 2 == 0 else 0.82))
               for j, a in enumerate(np.linspace(0, math.tau, 12, endpoint=False))]
        path = cv.blob(pts)
        yk.wash(cv, path, (0.55, 0.5, 0.45), alpha * 0.7, z=z + i * 0.01, blur=0.4)
        cv.stroke([(q[0] - rr * 0.7, q[1] - rr * 0.3), (q[0] - rr * 0.1, q[1] - rr * 0.8), (q[0] + rr * 0.6, q[1] - rr * 0.4)], 0.8, z=z + i * 0.01 + 0.005,
                  col=INK, taper=(0.4, 0.4), alpha=alpha * 0.6)


# ------------------------------------------------------------------ cüce gövdesi
def _arm(cv, sh, target, mat, z, bend=1.0, fist=True):
    el, h = yg.ik2(sh, target, 5.0, 5.0, bend)
    up = cv.limb([sh, el], [2.1, 1.8])
    cv.shape(up, mat, z=z, sd=0.8, hi=0.3, ol=0.9)
    fore = cv.limb([el, h], [1.75, 1.5])
    cv.shape(fore, BELT, z=z + 0.1, sd=0.6, hi=0.25, ol=0.9,
             details=[('ink', [lerp2(el, h, 0.45), (lerp2(el, h, 0.45)[0] + 0.4, lerp2(el, h, 0.45)[1] + 0.9)], 0.6)])
    if fist:
        cv.shape(cv.ellipse(h, 1.55, 1.4), SKIN, z=z + 0.2, sd=0.5, hi=0.25, ol=0.85,
                 details=[('ink', [(h[0] - 0.3, h[1] - 1.0), (h[0] + 0.2, h[1] + 0.8)], 0.6)])
    return h


def _leg(cv, hp, foot, mat, z, near=True, fk=None):
    if fk is not None:
        a1, a2 = fk
        kn = (hp[0] + math.sin(a1) * 4.3, hp[1] + math.cos(a1) * 4.3)
        f = (kn[0] + math.sin(a1 - a2) * 4.0, kn[1] + math.cos(a1 - a2) * 4.0)
    else:
        kn, f = yg.ik2(hp, foot, 4.3, 4.3, -1.0)
    sh = SHIRT if near else SHIRT_B
    cv.shape(cv.limb([hp, kn, f], [2.3, 2.0, 2.0]), sh, z=z, sd=0.8, hi=0.25 if near else 0.0, ol=0.9)
    # kalın çizme: konç + burnu kalkık taban
    ang = math.atan2(f[1] - kn[1], f[0] - kn[0]) - math.pi / 2
    ca, sa = math.cos(ang), math.sin(ang)
    P = lambda x, y, *t: (f[0] + x * ca - y * sa, f[1] + x * sa + y * ca) + t
    boot = cv.blob([P(-2.4, -2.6), P(2.0, -2.8), P(2.4, -0.6), P(4.8, 0.0), P(5.2, 1.0, 0.0), P(4.2, 1.6), P(-2.6, 1.6, 0.0), P(-2.8, 0.0)])
    cv.shape(boot, BOOT if near else BOOT_B, z=z + 0.2, sd=0.9, hi=0.3 if near else 0.0, ol=1.0,
             details=[('ink', [P(-2.4, -1.6), P(2.2, -1.8)], 0.9), ('ink', [P(-2.6, 1.0), P(4.6, 1.0)], 0.8),
                      ('col', cv.ellipse(P(0.6, -2.2), 0.4, 0.4), BRASS.base)])
    return f


def body(cv, p):
    """Cüce: yerel gövde çerçevesinde (kalça HIP, yüz sağa). Döner {'hand': kazma ucu ya da taş}."""
    ph = p['ph']
    bs = p['bs']
    eye = p['eye']
    # ---- arka kol (iki elle tutuşta kazmanın alt ucu; tek elde kazmayı tutar)
    d = _d(p['pa'])
    g = p['g']
    two = p['two'] > 0.5
    hup = (g[0] + d[0] * 3.6, g[1] + d[1] * 3.6)
    shb, shf = (-2.6, -20.0), (3.2, -20.3)
    _arm(cv, shb, g, SHIRT_B, -12, bend=-1.0)
    # ---- bacaklar
    if p['fk'] is not None:   # havada: bacaklar gövdeyle birlikte döner (ileri kinematik)
        _leg(cv, (-2.8, -8.0), None, SHIRT_B, -8, False, fk=p['fk'][0])
        _leg(cv, (2.6, -8.0), None, SHIRT, -6, True, fk=p['fk'][1])
    else:                     # yerde: ayaklar dünyada sabit, kalça gövdeyle kayar (ik)
        f = cv.xf[-1]
        hb, hf_ = f((-2.8, -8.0)), f((2.6, -8.0))
        cv.pop()
        _leg(cv, hb, p['fb'], SHIRT_B, -8, False)
        _leg(cv, hf_, p['ff'], SHIRT, -6, True)
        cv.push(f)
    # ---- fıçı gövde
    torso = cv.blob([(-5.4, -21.4), (0.0, -23.2), (5.6, -22.0), (8.6, -17.0), (9.4, -12.0), (7.4, -7.4), (0.0, -6.2), (-7.2, -7.2), (-8.6, -12.5), (-7.6, -18.0)])
    cv.shape(torso, SHIRT, z=0, sd=2.4, hi=0.5, ol=1.0, hatch=0.3, bounce=0.3,
             details=cv.fold([(-4.5, -17.0), (-5.6, -12.0), (-4.6, -8.0)], 0.9, 1.1, 1))
    # kemer + keseler
    belt = cv.blob([(-8.8, -12.6), (9.2, -12.2), (9.0, -10.0), (-8.6, -10.4)])
    cv.shape(belt, BELT, z=1, sd=0.6, hi=0.25, ol=0.9)
    for (x, w_, h_, m) in ((-6.8, 2.2, 2.8, APRON), (-3.6, 1.6, 2.2, PATCH2)):
        cv.shape(cv.blob([(x - w_, -11.8), (x + w_, -11.8), (x + w_ * 0.9, -11.8 + h_, 0.0), (x - w_ * 0.9, -11.8 + h_, 0.0)]), m, z=1.2, sd=0.6, hi=0.2, ol=0.85,
                 details=[('ink', [(x - w_ * 0.9, -10.8), (x + w_ * 0.9, -10.8)], 0.7), ('col', cv.ellipse((x, -10.6), 0.35, 0.35), BRASS.base)])
    # önlük: yamalı deri, dikiş izleri
    apron = cv.blob([(1.2, -20.5), (6.4, -20.0), (8.8, -14.0), (9.4, -6.0), (8.0, -4.2), (2.0, -4.6), (0.6, -10.0)])
    pt1 = cv.blob([(3.0, -9.5), (6.6, -9.8), (6.8, -6.6), (3.2, -6.3)])
    pt2 = cv.blob([(5.8, -16.2), (8.4, -16.0), (8.6, -13.6), (6.0, -13.8)])
    adet = [('col', pt1, PATCH.base), ('col', pt2, PATCH2.base),
            ('ink', [(3.0, -9.5), (6.6, -9.8), (6.8, -6.6), (3.2, -6.3), (3.0, -9.5)], 0.5, (0.0, 0.0)),
            ('ink', [(5.8, -16.2), (8.4, -16.0), (8.6, -13.6), (6.0, -13.8), (5.8, -16.2)], 0.5, (0.0, 0.0))]
    for k in range(4):
        adet.append(('stroke', [(3.4 + k * 0.9, -9.9), (3.6 + k * 0.9, -9.1)], 0.6, PATCH.hi, (0.1, 0.1)))
    adet += cv.fold([(4.0, -12.0), (4.6, -8.0), (5.0, -4.8)], 0.7, 0.9, -1)
    cv.shape(apron, APRON, z=3, sd=1.2, hi=0.35, ol=0.95, details=adet, bounce=0.2)
    cv.shape(cv.ellipse((8.8, -11.2), 0.9, 0.8), BRASS, z=3.2, sd=0.3, hi=0.2, ol=0.7)   # kemer tokası
    # ---- baş
    hc = (2.8, -27.0)
    cv.shape(cv.ellipse((hc[0] - 0.4, hc[1]), 4.6, 4.4), SKIN, z=6, sd=1.2, hi=0.3, ol=0.95)
    cv.shape(cv.ellipse((hc[0] - 2.6, hc[1] + 0.2), 1.1, 1.5, 0.2), SKIN, z=6.1, sd=0.4, ol=0.8,
             details=[('ink', [(hc[0] - 2.8, hc[1] - 0.4), (hc[0] - 2.5, hc[1] + 0.7)], 0.6)])
    # sakal: çeneden göbeğe yayılan kütle + dizlere inen iki örgü
    sway = bs * 1.2
    beard = cv.blob([(hc[0] - 1.6, hc[1] + 0.2), (hc[0] + 1.8, hc[1] + 1.6), (hc[0] + 6.4, hc[1] + 1.0), (hc[0] + 7.6, hc[1] + 3.6),
                     (hc[0] + 7.2 + sway * 0.4, hc[1] + 8.6), (hc[0] + 5.6 + sway * 0.6, hc[1] + 13.0, 0.0), (hc[0] + 3.2 + sway * 0.5, hc[1] + 11.6),
                     (hc[0] + 1.0 + sway * 0.4, hc[1] + 13.4, 0.0), (hc[0] - 0.8 + sway * 0.2, hc[1] + 8.4), (hc[0] - 2.4, hc[1] + 4.0)])
    bdet = []
    for k in range(4):
        x0 = hc[0] + 0.2 + k * 1.7
        bdet.append(('ink', [(x0, hc[1] + 3.0), (x0 + 0.3 + sway * 0.2, hc[1] + 7.0), (x0 + sway * 0.4, hc[1] + 10.5)], 0.7, (0.3, 0.6)))
        bdet.append(('stroke', [(x0 + 0.6, hc[1] + 2.6), (x0 + 0.8 + sway * 0.2, hc[1] + 6.0)], 0.9, BEARD.hi, (0.3, 0.6)))
    cv.shape(beard, BEARD, z=10, sd=1.4, hi=0.45, ol=1.0, details=bdet, fur=0.6)
    for j, (bx, ln) in enumerate(((hc[0] + 1.6, 10.0), (hc[0] + 5.0, 9.0))):
        pts = [(bx + sway * 0.4, hc[1] + 11.0)]
        for k in range(4):
            pts.append((bx + sway * (0.6 + 0.35 * k) + math.sin(ph + k * 0.8 + j) * 0.25, hc[1] + 11.0 + ln * (k + 1) / 4))
        cv.shape(ik.taper_path([cv.W(q) for q in pts], cv.u(2.1), prof=lambda u: max(0.35, 1.0 - 0.45 * u)), BEARD, z=10.5 + j * 0.1, sd=0.6, hi=0.3, ol=0.9,
                 details=[('ink', [lerp2(pts[k], pts[k + 1], 0.5), (lerp2(pts[k], pts[k + 1], 0.5)[0] + 0.9, lerp2(pts[k], pts[k + 1], 0.5)[1] - 0.6)], 0.6) for k in range(4)])
        rq = lerp2(pts[1], pts[2], 0.6)
        cv.shape(cv.capsule((rq[0] - 0.9, rq[1]), (rq[0] + 0.9, rq[1]), 0.6, 0.6), BRASS, z=10.8 + j * 0.1, sd=0.25, hi=0.2, ol=0.7)
        tipq = pts[-1]
        cv.shape(cv.blob([(tipq[0] - 0.9, tipq[1] - 0.6), (tipq[0] + 0.9, tipq[1] - 0.6), (tipq[0] + 0.2, tipq[1] + 1.6, 0.0)]), BEARD, z=10.7 + j * 0.1, sd=0.3, ol=0.8)
    # bıyık: burnun altından iki yana kıvrık
    mo = p['mouth']
    if mo > 0.05:
        cv.shape(cv.ellipse((hc[0] + 4.8, hc[1] + 3.0), 1.4, 0.8 + 1.2 * mo), Ink('#3a1418', '#1e0a0e', '#5a2428'), z=11, sd=0.3, ol=0.8,
                 details=[('col', cv.ellipse((hc[0] + 4.9, hc[1] + 2.4), 0.9, 0.35), (0.92, 0.9, 0.8))])
    must = cv.blob([(hc[0] + 2.0, hc[1] + 1.6), (hc[0] + 5.0, hc[1] + 0.8), (hc[0] + 8.2, hc[1] + 1.4), (hc[0] + 9.2, hc[1] + 3.0, 0.0),
                    (hc[0] + 7.0, hc[1] + 2.4), (hc[0] + 5.0, hc[1] + 2.2), (hc[0] + 2.6, hc[1] + 3.2, 0.0)])
    cv.shape(must, BEARD, z=12, sd=0.7, hi=0.35, ol=0.9, fur=0.4)
    # yumru burun
    cv.shape(cv.ellipse((hc[0] + 6.0, hc[1] + 0.2), 2.0, 1.8, 0.2), NOSE, z=13, sd=0.8, hi=0.45, ol=0.95,
             details=[('ink', [(hc[0] + 5.2, hc[1] + 1.4), (hc[0] + 5.8, hc[1] + 1.9)], 0.6), ('hi', cv.ellipse((hc[0] + 5.5, hc[1] - 0.7), 0.6, 0.4))])
    # gözler: kor; eye 0 = sıkılı (acı), 1 = olağan, 2 = alev
    for j, q in enumerate(((hc[0] + 2.4, hc[1] - 1.7), (hc[0] + 5.0, hc[1] - 1.9))):
        if eye < 0.3:
            cv.stroke([(q[0] - 0.9, q[1] - 0.4), (q[0], q[1] + 0.2), (q[0] + 0.9, q[1] - 0.4)], 1.0, z=13.5, col=INK, taper=(0.2, 0.2))
        else:
            r_ = 0.55 + 0.15 * min(eye, 2.0)
            cv.fill(cv.ellipse(q, 1.0, 0.75), INK, z=13.4)
            yk.eye_glow(cv, q, r_, r_ * 0.75, 0.0, EMBER, EMBER_G, 13.5, halo=2.0 + 0.6 * eye, halo_a=0.25 + 0.2 * eye)
    # ağır kaşlar (gözlerin üstüne sarkan)
    bl = -0.6 if eye >= 1.9 else (0.5 if eye < 0.3 else 0.0)
    brow = cv.blob([(hc[0] + 0.6, hc[1] - 3.0 + bl * 0.5), (hc[0] + 3.6, hc[1] - 3.6), (hc[0] + 6.8, hc[1] - 3.4 - bl), (hc[0] + 7.2, hc[1] - 2.4 - bl, 0.0),
                    (hc[0] + 4.6, hc[1] - 2.2), (hc[0] + 1.6, hc[1] - 1.8 + bl * 0.5, 0.0)])
    cv.shape(brow, BROW, z=14, sd=0.6, hi=0.3, ol=0.9, fur=0.5)
    # ezik demir başlık + ön fener
    capp = cv.blob([(hc[0] - 4.8, hc[1] - 1.6), (hc[0] - 4.2, hc[1] - 5.6), (hc[0] - 0.6, hc[1] - 8.2), (hc[0] + 2.0, hc[1] - 7.4),
                    (hc[0] + 3.2, hc[1] - 8.0), (hc[0] + 5.8, hc[1] - 6.0), (hc[0] + 6.8, hc[1] - 3.4)])
    cdet = [('ink', [(hc[0] + 1.4, hc[1] - 7.6), (hc[0] + 2.2, hc[1] - 6.0), (hc[0] + 3.2, hc[1] - 7.4)], 0.8, (0.1, 0.1)),   # ezik
            ('shade', cv.ellipse((hc[0] + 2.2, hc[1] - 6.4), 1.4, 1.0)),
            ('ink', [(hc[0] - 3.6, hc[1] - 3.0), (hc[0] - 2.0, hc[1] - 6.8)], 0.6, (0.3, 0.3))]
    for k in range(4):
        cdet.append(('col', cv.ellipse((hc[0] - 3.4 + k * 2.4, hc[1] - 3.0 - math.sin(k / 3 * math.pi) * 0.6), 0.32, 0.32), CAP.hi))
    cv.shape(capp, CAP, z=15, sd=1.2, hi=0.45, ol=1.0, details=cdet)
    brim = cv.blob([(hc[0] - 5.6, hc[1] - 1.2), (hc[0] + 7.8, hc[1] - 3.2), (hc[0] + 8.2, hc[1] - 2.0, 0.0), (hc[0] - 5.4, hc[1] - 0.2, 0.0)])
    cv.shape(brim, CAP.darker(0.85), z=15.2, sd=0.4, hi=0.2, ol=0.9)
    lc = (hc[0] + 6.2, hc[1] - 5.2)
    lamp = p['lamp']
    cv.shape(cv.blob([(lc[0] - 1.6, lc[1] - 1.8), (lc[0] + 1.0, lc[1] - 2.0), (lc[0] + 1.4, lc[1] + 1.6), (lc[0] - 1.6, lc[1] + 1.6)]), BRASS, z=16, sd=0.5, hi=0.3, ol=0.9)
    cv.fill(cv.ellipse((lc[0] + 1.3, lc[1] - 0.2), 0.9 + 0.1 * lamp, 1.6), LAMP, z=16.2, glow=LAMP_G)
    cv.fill(cv.ellipse((lc[0] + 1.4, lc[1] - 0.4), 0.45, 0.8), (1.0, 0.97, 0.85), z=16.3, glow=(1.0, 0.85, 0.5))
    yk.glow_soft(cv, (lc[0] + 1.6, lc[1] - 0.2), 4.5 * lamp, LAMP_G, z=16.4, blur=0.6, alpha=0.6 * lamp)
    if lamp > 0.3:   # fener ışık konisi (soluk amber)
        cone = cv.blob([(lc[0] + 1.6, lc[1] - 1.0), (lc[0] + 12.0, lc[1] - 4.5), (lc[0] + 13.0, lc[1] + 4.0), (lc[0] + 1.6, lc[1] + 0.8)])
        yk.wash(cv, cone, LAMP, 0.0, z=-30, glow=LAMP_G, glow_a=0.07 * lamp)
    # ---- kazma (iki elle: önde; tek elle arka elde) + ön kol
    out = {}
    flip = p['flip']
    if two:
        kt, kc = pick(cv, g, p['pa'], p['pz'], flip=flip, glow=p['cg'])
        _arm(cv, shf, hup, SHIRT, 20, bend=-1.0)
        out['hand'] = kt
    else:
        kt, kc = pick(cv, g, p['pa'], -11, flip=flip, glow=p['cg'])
        hf = _arm(cv, shf, p['h2'], SHIRT, 20, bend=-1.0, fist=True)
        if p['rock'] > 0:
            rp = (hf[0] + p['roff'][0], hf[1] + p['roff'][1])
            rock(cv, rp, 3.1, 21 if p['rock'] < 1.5 else 19, rot=ph)
            out['hand'] = rp
        else:
            out['hand'] = hf
    # ---- savuruş izi (yay)
    sm = p['sm']
    if sm[2] > 0.05:
        a0, a1, k = sm
        cc = p['smc']
        R = p['smr']
        ang = np.linspace(a0, a1, 9)
        outer = [(cc[0] + math.cos(a) * R, cc[1] + math.sin(a) * R) for a in ang]
        inner = [(cc[0] + math.cos(a) * R * (0.55 + 0.35 * (1 - u)), cc[1] + math.sin(a) * R * (0.55 + 0.35 * (1 - u))) for u, a in zip(np.linspace(0, 1, 9), ang)]
        arc = cv.blob([(q[0], q[1], 1.0) for q in outer] + [(q[0], q[1], 1.0) for q in inner[::-1]])
        yk.wash(cv, arc, (0.9, 0.95, 0.95), 0.35 * k, z=-20, glow=CRYST_G, glow_a=0.12 * k)
        cv.stroke(outer, 1.6, z=-19.9, col=INK, taper=(0.9, 0.1), alpha=0.7 * k)
        cv.stroke([(cc[0] + math.cos(a) * R * 0.92, cc[1] + math.sin(a) * R * 0.92) for a in ang], 1.0, z=-19.8, col=CRYST.hi, taper=(0.9, 0.1),
                  glow=CRYST_G, alpha=0.8 * k)
    return out


# ------------------------------------------------------------------ çizim
def draw_body(cv, p):
    cv.wob = 0.0
    u29.body_xf(cv, HIP, p['rot'], p['sx'], p['sy'], (p['dx'], p['dy']))
    info = body(cv, p)
    hand = u29.to_world(cv, info['hand'])
    cv.pop()
    return {'hand': hand}


def draw_fx(cv, p):
    """Yer efektleri (dünya): tümsek, toprak püskürmesi, toz, vuruş kıvılcımı, çukur."""
    ph = p['ph']
    out = {}
    m = p['mound']
    if m is not None:
        cx, w, h, cr = m
        mound(cv, cx, w, h, 5, seed=p['seed'], crack=cr, ph=ph)
        if p['peek'] > 0:   # tümsekten kazma ucu görünür
            q = (cx + w * 0.35, -h * 0.85)
            kt = (q[0] + 2.0, q[1] - 2.6 * p['peek'])
            cv.shape(cv.blob([(q[0] - 0.8, q[1] + 0.6, 0.0), (kt[0], kt[1], 0.0), (q[0] + 1.2, q[1] + 0.4, 0.0)]), CRYST, z=4.8, sd=0.3, hi=0.3, ol=0.8,
                     glow=(0.05, 0.32, 0.3))
            yk.glow_soft(cv, kt, 2.6, CRYST_G, z=4.9, alpha=0.6)
            out['hand'] = kt
        if p['mglow'] > 0:   # fener ışığı toprağın altından
            yk.glow_soft(cv, (cx - w * 0.1, -h * 0.4), w * 0.9, LAMP_G, z=5.9, blur=0.7, alpha=0.4 * p['mglow'], ry=h * 0.9)
    if p['spray'] > 0:
        k = p['spray']
        c = p['sprc']
        debris(cv, c, 16, 6.0, 20.0, 30, seed=p['seed'] + 3, k=k, cone=p['cone'], ang=p['sang'], fall=0.4)
        dust(cv, (c[0], c[1] - 2), 3.0 + 4.0 * k, 29, seed=p['seed'] + 5, n=3)
    if p['rocks'] > 0:   # emerge: dört yana taşlar
        k = p['rocks']
        debris(cv, (p['sprc'][0], 0.0), 12, 10.0, 26.0, 31, seed=p['seed'] + 9, k=k, cone=2.2, mats=(ROCK, EARTH, ROCK), s0=0.8, s1=1.9, fall=0.6)
    if p['crater'] > 0:
        w = p['crater']
        cx = p['sprc'][0]
        cv.shape(cv.blob([(cx - w, 0.4, 0.0), (cx - w * 0.75, -1.6), (cx - w * 0.3, -0.8), (cx + w * 0.3, -0.9), (cx + w * 0.8, -1.8), (cx + w, 0.4, 0.0)]),
                 EARTH, z=28, sd=0.6, hi=0.3, ol=0.9)
    if p['impact'] > 0:   # kazma yere çarpar: kıvılcım + toprak
        k = p['impact']
        c = p['impc']
        yk.sparks(cv, c, 7, 0.8, 3.5 + 3 * k, (1.0, 0.9, 0.6), 32, seed=p['seed'] + 2, w=1.2, glow=LAMP_G, ang=-math.pi * 0.6, spread=2.0)
        yk.sparks(cv, c, 4, 0.6, 3.0, CRYST.hi, 32.1, seed=p['seed'] + 7, w=1.0, glow=CRYST_G, ang=-math.pi * 0.35, spread=1.2)
        debris(cv, c, 8, 3.0, 9.0 * k + 2, 31, seed=p['seed'] + 11, k=min(1.0, 0.4 + k), cone=1.6, ang=-math.pi * 0.55, s0=0.4, s1=1.0, fall=0.3)
        yk.glow_soft(cv, c, 4.0 * k, CRYST_G, z=32.2, alpha=0.6 * k)
    if p['puff'] > 0:
        dust(cv, (p['dx'], -1.0), 3.5 * p['puff'] + 1.0, 27, seed=p['seed'] + 13, n=3, alpha=0.5)
    return out


# ================================================================== pozlar
REST = dict(dx=0.0, dy=0.0, rot=0.0, sx=1.0, sy=1.0, fb=(-3.6, 0.0), ff=(3.4, 0.0), fk=None,
            g=(6.4, -16.0), pa=1.45, pz=18.0, flip=-1.0, two=1.0, h2=(6.0, -14.0), rock=0.0, roff=(0.8, -1.4),
            bs=0.0, eye=1.0, mouth=0.0, lamp=1.0, cg=1.0, sm=(0.0, 0.0, 0.0), smc=(1.0, -20.0), smr=14.0,
            body=1.0, gl=None, mound=None, peek=0.0, mglow=0.0, spray=0.0, sprc=(4.0, 0.0), sang=-math.pi / 2, cone=1.2, rocks=0.0, crater=0.0,
            impact=0.0, impc=(14.0, 0.0), puff=0.0, seed=1)


def _idle(t):
    s = math.sin(math.tau * t)
    c = math.cos(math.tau * t)
    return dict(dy=0.4 * (1 - c) * 0.5 + 0.0, sy=1.0 - 0.025 * s, sx=1.0 + 0.02 * s, rot=-0.02 + 0.015 * s, g=(6.4, -16.0 + 0.5 * (1 - c) * 0.5), pa=1.45 + 0.02 * s,
                bs=0.3 * math.sin(math.tau * t - 0.8), lamp=1.0 + 0.12 * math.sin(math.tau * t * 3), eye=1.0 if int(t * 6) != 4 else 0.0)


def _move(t):
    a = math.tau * t
    s = math.sin(a)
    # paytak yürüyüş: adım başına yan yalpa, gövde inip kalkar
    stp = 3.4
    fb = (-0.6 - stp * math.cos(a), max(0.0, math.sin(a)) * 2.4)
    ff = (0.6 + stp * math.cos(a), max(0.0, -math.sin(a)) * 2.4)
    return dict(dy=-abs(math.sin(a)) * 1.3 + 0.6, rot=0.08 + 0.07 * math.sin(2 * a + 0.4), fb=(fb[0], -fb[1]), ff=(ff[0], -ff[1]),
                g=(5.0 + 0.5 * s, -10.5 - 0.6 * abs(s)), pa=-0.85 + 0.08 * s, flip=1.0, bs=-0.6 + 0.5 * math.sin(2 * a - 1.0), lamp=1.0 + 0.1 * math.sin(a * 3), seed=int(t * 8))


_HURT = [dict(dx=-2.0, rot=-0.32, sy=0.94, sx=1.05, eye=0.0, mouth=0.9, g=(3.0, -15.0), pa=-1.75, flip=1.0, bs=1.0, fb=(-4.4, 0.0), ff=(2.0, -1.2), lamp=1.4),
         dict(dx=-2.6, rot=-0.22, sy=1.02, eye=0.0, mouth=0.6, g=(3.6, -14.0), pa=-1.5, flip=1.0, bs=0.6, ff=(2.6, 0.0), lamp=1.2),
         dict(dx=-1.4, rot=-0.08, eye=1.0, mouth=0.2, g=(4.0, -12.6), pa=-1.3, flip=1.0, bs=0.2)]

# tepeden öne kazma: gerilme (kazma başın arkasında), fırlayış, yere saplanma (kıvılcım), toparlanma
_PICK = [dict(rot=-0.08, dy=0.6, sy=0.96, g=(3.0, -17.0), pa=-1.7, flip=1.0, pz=18.0, bs=-0.3, fb=(-4.6, 0.0), ff=(4.6, 0.0)),
         dict(rot=-0.2, dy=0.4, g=(2.4, -24.0), pa=-2.2, flip=1.0, pz=18.0, bs=-0.6, eye=1.5, fb=(-4.6, 0.0), ff=(4.8, 0.0)),
         dict(rot=-0.32, dy=1.0, sy=1.04, sx=0.97, g=(2.0, -26.0), pa=-2.5, flip=1.0, pz=18.0, bs=-0.8, eye=2.0, lamp=1.3, cg=1.4, fb=(-5.0, 0.0), ff=(5.2, 0.0)),
         dict(rot=-0.38, dy=1.6, sy=1.06, sx=0.96, g=(1.4, -26.4), pa=-2.72, flip=1.0, pz=18.0, bs=-1.0, eye=2.0, mouth=0.4, lamp=1.5, cg=1.6, fb=(-5.0, 0.0), ff=(5.4, 0.0)),
         dict(rot=0.08, dy=-0.4, g=(5.0, -24.0), pa=-1.05, flip=1.0, pz=18.0, bs=-0.6, eye=2.0, mouth=0.6, cg=1.5, sm=(-2.9, -1.2, 0.7), smc=(1.0, -20.0), smr=15.0,
              fb=(-5.0, 0.0), ff=(6.2, 0.0)),
         dict(rot=0.22, dx=2.6, dy=1.6, sy=0.94, sx=1.06, g=(8.0, -15.0), pa=0.28, flip=1.0, pz=18.0, bs=0.9, eye=2.0, mouth=0.9, cg=1.8,
              sm=(-1.9, 0.6, 1.0), smc=(2.0, -18.0), smr=15.5, impact=1.0, impc=(17.0, 0.0), fb=(-5.4, 0.0), ff=(7.0, 0.0)),
         dict(rot=0.26, dx=2.8, dy=2.0, sy=0.93, sx=1.07, g=(8.4, -14.0), pa=0.34, flip=1.0, pz=18.0, bs=1.1, eye=1.5, mouth=0.5, cg=1.3,
              sm=(-0.6, 0.75, 0.4), smc=(2.0, -18.0), smr=15.5, impact=0.55, impc=(17.0, 0.0), fb=(-5.4, 0.0), ff=(7.0, 0.0), puff=0.6),
         dict(rot=0.12, dx=1.2, dy=0.6, g=(7.0, -13.0), pa=0.0, flip=1.0, pz=18.0, bs=0.4, eye=1.0, fb=(-4.4, 0.0), ff=(5.0, 0.0), puff=0.3)]
_PICK_TS = [0.0, 0.13, 0.25, 0.36, 0.46, 0.52, 0.66, 0.82]
_PICK_MK = [0.36, 0.52, 0.82]

# yedek taşı omuz üstünden fırlatır: kazma arka elde yere dayalı; taş TEMAS karesinde elden çıkar
_TG, _TPA = (-4.0, -12.0), 1.95
_THROW = [dict(two=0.0, g=_TG, pa=_TPA, flip=1.0, pz=18.0, h2=(6.4, -15.0), rock=1.0, rot=0.02),
          dict(two=0.0, g=_TG, pa=_TPA, flip=1.0, pz=18.0, h2=(2.0, -20.5), rock=1.0, rot=-0.14, dy=0.4, eye=1.4),
          dict(two=0.0, g=_TG, pa=_TPA, flip=1.0, pz=18.0, h2=(-3.6, -23.0), rock=2.0, rot=-0.28, dy=1.0, sy=1.03, eye=2.0, bs=-0.6, lamp=1.3, ff=(5.0, 0.0)),
          dict(two=0.0, g=_TG, pa=_TPA, flip=1.0, pz=18.0, h2=(-5.4, -22.4), rock=2.0, rot=-0.36, dy=1.4, sy=1.05, eye=2.0, bs=-0.9, lamp=1.5, mouth=0.4, ff=(5.4, 0.0)),
          dict(two=0.0, g=_TG, pa=_TPA, flip=1.0, pz=18.0, h2=(5.0, -29.0), rock=1.0, roff=(0.4, -2.2), rot=0.0, eye=2.0, bs=-0.4, mouth=0.6, ff=(5.8, 0.0),
               sm=(-2.2, -1.1, 0.6), smc=(3.2, -20.0), smr=8.6),
          dict(two=0.0, g=_TG, pa=_TPA, flip=1.0, pz=18.0, h2=(11.8, -22.0), rock=1.0, roff=(2.6, -0.8), rot=0.3, dx=1.8, dy=0.8, eye=2.0, bs=0.8, mouth=0.9,
               ff=(6.6, 0.0), sm=(-1.6, -0.25, 1.0), smc=(3.2, -20.0), smr=8.8),
          dict(two=0.0, g=_TG, pa=_TPA, flip=1.0, pz=18.0, h2=(10.8, -14.6), rock=0.0, rot=0.36, dx=2.0, dy=1.2, eye=1.4, bs=1.0, mouth=0.4, ff=(6.6, 0.0)),
          dict(two=0.0, g=_TG, pa=_TPA, flip=1.0, pz=18.0, h2=(7.0, -14.0), rock=0.0, rot=0.1, dx=0.8, dy=0.4, eye=1.0, bs=0.4, ff=(4.6, 0.0))]
_THROW_TS = [0.0, 0.14, 0.27, 0.38, 0.47, 0.53, 0.68, 0.84]
_THROW_MK = [0.38, 0.53, 0.84]

# yere dalış: çömelir, sıçrar, başüstü döner, toprağa gömülür; en sonda yalnızca tümsek + püskürme
_FKT = ((0.9, 1.6), (0.6, 1.5))
_DIG = [dict(dy=2.2, sy=0.88, sx=1.1, rot=-0.15, g=(1.0, -21.0), pa=-1.75, flip=1.0, pz=18.0, eye=2.0, bs=-0.6, fb=(-5.0, 0.0), ff=(5.0, 0.0), lamp=1.3),
        dict(dy=-7.0, dx=2.0, sy=1.08, sx=0.94, rot=0.7, g=(8.0, -20.0), pa=-0.6, flip=1.0, pz=18.0, eye=2.0, bs=-1.0, fk=_FKT, puff=0.7, sprc=(0.0, 0.0)),
        dict(dy=-5.0, dx=5.0, rot=2.1, g=(9.0, -18.0), pa=-0.3, flip=1.0, pz=18.0, eye=2.0, bs=-1.2, fk=_FKT, gl=0.4, spray=0.15, sprc=(9.0, 0.0), sang=-math.pi / 2,
             cone=1.6, mound=(9.0, 5.0, 1.6, 0.0), seed=4),
        dict(dy=-3.0, dx=8.0, rot=2.95, g=(9.0, -18.0), pa=-0.3, flip=1.0, pz=18.0, eye=2.0, fk=_FKT, gl=0.4, spray=0.5, sprc=(8.0, 0.0), cone=1.8,
             mound=(8.0, 6.5, 2.6, 0.0), seed=4),
        dict(dy=8.0, dx=8.0, rot=3.1, g=(9.0, -18.0), pa=-0.3, flip=1.0, pz=18.0, fk=((0.3, 1.2), (-0.4, 0.4)), gl=-1.0, spray=0.6, sprc=(5.0, 0.0), cone=1.6,
             mound=(8.0, 8.5, 4.4, 0.0), seed=4),
        dict(body=0.0, spray=1.0, sprc=(8.0, 0.0), cone=2.2, mound=(8.0, 9.0, 5.0, 0.0), mglow=0.5, seed=4)]

# yer altında ilerleyen tümsek (yalnızca toprak, fener ışığı ve kazma ucu)


def _burrow(t):
    a = math.tau * t
    return dict(body=0.0, mound=(0.0 + 0.5 * math.sin(a), 11.0 + 0.5 * math.sin(2 * a), 7.0 + 0.5 * math.cos(2 * a), 0.35),
                peek=1.0, mglow=0.7 + 0.2 * math.sin(a * 2), spray=0.5 + 0.2 * math.sin(a), sprc=(-6.0, 0.0), sang=-math.pi * 0.72, cone=0.9,
                seed=10 + int(t * 4) * 3, ph=a)


# yerden fırlayış: tümsek şişer ve çatlar (ışık), sonra aşağıdan yukarı kazma vuruşu, taşlar uçar, iner
_EMERGE = [dict(body=0.0, mound=(2.0, 9.0, 5.4, 0.35), peek=0.6, mglow=0.8, seed=21),
           dict(body=0.0, mound=(2.0, 10.0, 6.6, 0.6), peek=0.8, mglow=1.0, seed=22, spray=0.15, sprc=(2.0, -3.0), cone=2.4),
           dict(body=0.0, mound=(2.0, 11.0, 8.0, 0.9), peek=1.0, mglow=1.3, seed=23, spray=0.25, sprc=(2.0, -4.0), cone=2.6),
           dict(body=0.0, mound=(2.0, 11.6, 8.8, 1.0), peek=1.2, mglow=1.6, seed=24, spray=0.3, sprc=(2.0, -5.0), cone=2.6),
           dict(dy=7.0, dx=1.0, rot=-0.1, g=(6.0, -10.0), pa=0.35, flip=-1.0, pz=18.0, eye=2.0, mouth=0.8, bs=1.0, gl=0.2, fk=((0.4, 0.9), (-0.2, 0.7)),
                rocks=0.35, crater=7.0, sprc=(2.0, 0.0), spray=0.4, cone=2.4, seed=25, lamp=1.6, cg=1.6,
                sm=(1.2, 0.1, 0.6), smc=(3.0, -12.0), smr=14.0),
           dict(dy=-4.0, dx=2.4, rot=-0.22, sy=1.08, sx=0.94, g=(9.0, -20.0), pa=-0.6, flip=-1.0, pz=18.0, eye=2.0, mouth=1.0, bs=1.4, fk=((0.5, 1.0), (0.1, 0.9)),
                rocks=0.7, crater=7.5, sprc=(2.0, 0.0), spray=0.8, cone=2.2, seed=25, lamp=1.6, cg=1.8,
                sm=(0.9, -0.95, 1.0), smc=(3.0, -16.0), smr=16.0),
           dict(dy=-5.0, dx=3.0, rot=-0.28, sy=1.04, g=(7.5, -23.0), pa=-1.1, flip=-1.0, eye=1.6, mouth=0.6, bs=1.2, fk=((0.7, 1.4), (0.4, 1.3)),
                rocks=1.0, crater=7.0, sprc=(2.0, 0.0), spray=1.0, cone=2.0, seed=25, cg=1.3, sm=(-0.3, -1.45, 0.45), smc=(3.0, -16.0), smr=16.0),
           dict(dy=1.4, dx=3.0, sy=0.9, sx=1.08, rot=0.05, g=(6.0, -13.0), pa=-2.4, flip=-1.0, eye=1.0, bs=-0.4, fb=(-1.4, 0.0), ff=(6.8, 0.0),
                crater=5.0, sprc=(2.0, 0.0), puff=1.0, seed=26)]
_EMERGE_TS = [0.0, 0.14, 0.27, 0.38, 0.47, 0.53, 0.68, 0.84]
_EMERGE_MK = [0.38, 0.53, 0.84]


def _row(frames, fps, loop, pose, ts=None, mk=None, vx=None):
    return dict(frames=frames, fps=fps, loop=loop, pose=pose, ts=ts, mk=mk, vx=vx)


ROWS = {
    'idle': _row(6, 7, True, _idle),
    'move': _row(8, 12, True, _move, vx=70.0),
    'hurt': _row(3, 14, False, _HURT),
    'atk_pick': _row(8, 12, False, _PICK, ts=_PICK_TS, mk=_PICK_MK),
    'atk_throw': _row(8, 12, False, _THROW, ts=_THROW_TS, mk=_THROW_MK),
    'dig': _row(6, 12, False, _DIG),
    'burrow': _row(4, 10, True, _burrow),
    'atk_emerge': _row(8, 12, False, _EMERGE, ts=_EMERGE_TS, mk=_EMERGE_MK),
}


def _durum(moves, extra):
    d = {"idle": "idle", "chase": "move", "recover": "idle", "evade": "move", "_hurt": "hurt", "_hurt_big": "hurt", "_break": "hurt"}
    for m in moves:
        for k in ("windup", "act", "recover"):
            d['%s/%s' % (k, m)] = 'atk_' + m
    d.update(extra)
    return d


DURUM = _durum(('pick', 'throw', 'emerge'), {"windup/dig": "dig", "act/dig": "dig", "burrow": "burrow"})


def anims_for(var='yer_cucesi'):
    return {k: {kk: vv for kk, vv in r.items() if kk != 'pose'} for k, r in ROWS.items()}


def durum_for(var='yer_cucesi'):
    return DURUM


def pose_of(anim, i):
    r = ROWS[anim]
    if callable(r['pose']):
        t = i / r['frames']
        p = dict(REST, **r['pose'](t))
    else:
        p = dict(REST, **r['pose'][i])
    p.setdefault('ph', 0.0)
    if 'ph' not in (r['pose'](0) if callable(r['pose']) else r['pose'][i]):
        p['ph'] = i * 0.9
    return p


SHADE = dict(outer=0.5, rim=0.7, rim_col=(0.7, 0.78, 1.0), rim_dir=(0.6, -0.8), rim_w=1.3, form=(4.0, (0.78, 0.74, 0.86)))


def _clip_ground(rgba, em, cv, gl):
    """Dünya y = gl çizgisinin altını sil (gövde toprağın içinde)."""
    row = int(round(cv.oy + gl * cv.k))
    row = max(0, min(rgba.shape[0], row))
    rgba = rgba.copy()
    em = em.copy()
    rgba[row:] = 0.0
    em[row:] = 0.0
    return rgba, em


def render_frame(anim, i, var='yer_cucesi', ss=3):
    p = pose_of(anim, i)
    info = {}
    W, H = CELL
    if p['body'] > 0:
        cv = u29.canvas(W, H, FEET[0], FEET[1], TEX, ss=ss)
        info = draw_body(cv, p)
        rgba, nm, em = cv.finish(**SHADE)
        if p['gl'] is not None:
            rgba, em = _clip_ground(rgba, em, cv, p['gl'])
    else:
        rgba = em = None
    cf = u29.canvas(W, H, FEET[0], FEET[1], TEX, ss=ss)
    fi = draw_fx(cv=cf, p=p)
    fr, _n, fe = cf.finish(outer=0.45, form=None)
    if rgba is None:
        rgba, em = fr, fe
    else:
        rgba, em = u29.over(fr, fe, rgba, em)
    if 'hand' in fi and (p['body'] <= 0 or anim == 'burrow'):
        info['hand'] = fi['hand']
    if 'hand' not in info:
        info['hand'] = (p['sprc'][0], -4.0)
    if info['hand'][1] > -1.0:   # toprağın altındaysa çapa yüzeye
        info['hand'] = (info['hand'][0], -1.0)
    info = {k: (round(float(v[0]), 2), round(float(v[1]), 2)) for k, v in info.items()}
    return rgba.astype(np.float32), None, em.astype(np.float32), info
