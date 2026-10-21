"""v39: Şulmus (kimlik sulmus; Ötüken, yapay zekâ "summoner") — mürekkep-cel tam gövde.

Kambur, boynuzlu cin-kam / gulyabani ruhu: kurşuni-mor ten, iri sivri kulaklar, boncuk muskaları sarkan koç gibi
kıvrık boynuzlar, eğri dişli kocaman sırıtış, bir iri yeşil ışıyan göz + bir kısık göz, koyu kızıl / aşı (okra)
paçavralardan yamalı yırtık pelerin ve kemik nazarlıklar, ince bacaklar ve pençeli ayaklar; elinde ucu at kafatası
çıngıraklı, yeşil hortlak ateşli (ışır) eğri asa.

Satırlar (hücre 64 x 56 dünya, ayak (28, 53), doku 4):
  idle 8, move 8 (sinsi sinme yürüyüş, vx 55), hurt 3,
  atk_summon 9 (mk: asayı kaldırır, yerde yeşil mürekkep runa çemberi alevlenir, TEMAS karesi = yeşil ateş patlaması),
  atk_skull 8 (mk: asanın ucunda lanetli kafatası tutuşur, asa omuz üstünden savrulur, kafatası TEMAS karesinde fırlar),
  hop 4 (döngüsüz geri sıçrayış).
'hand' çapası = asa ucu (kafatası / efekt çıkışı), her karede.
Çağrılan yavru (sulmus_yavrusu) kendi modülünde: y39_sulmus_yavrusu.py.
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
CELL = (256, 224)       # dünya 64 x 56
FEET = (112, 212)       # dünya (28, 53)

SKIN = Ink('#8e80a2', '#463a60', '#beb0d0', '#261c36', name='mor-kurşuni ten')
SKIN_B = SKIN.darker(0.74)
EAR_IN = (0.72, 0.42, 0.55)
CLOAK = Ink('#7c2a28', '#3a1018', '#a84a3c', '#1c0810', name='kızıl paçavra')
CLOAK_B = Ink('#5a1e20', '#2a0a12', '#7a3430', '#14060a', name='pelerin arkası')
OCHRE = Ink('#b07e30', '#5c3a18', '#dcaa56', '#2e1c0c', name='aşı yaması')
RAG3 = Ink('#5a4434', '#2c1e18', '#806450', name='kahve yama')
BONE = Ink('#e2d6bc', '#8a7c66', '#fffaea', '#4a4034', name='kemik')
HORN = Ink('#b8a88c', '#5e5040', '#e4d8bc', '#302818', name='koç boynuzu')
WOOD = Ink('#7a5a3a', '#382618', '#a8825a', '#1a100a', name='eğri asa')
CLAW = Ink('#2e2830', '#121014', '#5a5060', name='pençe')
TOOTH = Ink('#e6dca4', '#8a7e50', '#fffbe0', name='eğri diş')
GREEN = (0.48, 1.0, 0.42)
GREEN_HOT = (0.88, 1.0, 0.8)
GREEN_G = (0.12, 0.9, 0.25)
BEADS = ((0.2, 0.72, 0.7), (0.78, 0.18, 0.14), (0.9, 0.86, 0.72))

HIP = (0.0, -14.0)


def _d(a):
    return (math.cos(a), math.sin(a))


def ghost_fire(cv, c, s, k, ph, z, seed=0):
    """Yeşil hortlak ateşi: yukarı kıvrılan dil dil alevler (dış yeşil, iç beyazımsı), ışıma + kıvılcım."""
    if k <= 0.02:
        return
    rng = np.random.default_rng(seed)
    yk.glow_soft(cv, (c[0], c[1] - s * 0.8), s * (1.6 + 0.8 * k), GREEN_G, z=z - 0.2, blur=0.6, alpha=0.5 + 0.3 * k)
    for j, (col, sc, zz) in enumerate(((GREEN, 1.0, 0.0), (GREEN_HOT, 0.55, 0.1))):
        for i in range(4 if j == 0 else 2):
            off = (i - 1.5) * s * 0.35 * sc
            h = s * (1.6 + 0.9 * rng.uniform(0.6, 1.2)) * sc * (0.6 + 0.6 * k)
            sway = math.sin(ph * 2 + i * 1.7) * s * 0.35
            b = (c[0] + off, c[1])
            tip = (c[0] + off * 0.4 + sway, c[1] - h)
            mid = (lerp2(b, tip, 0.5)[0] - sway * 0.6, lerp2(b, tip, 0.5)[1])
            w = s * 0.55 * sc
            path = cv.blob([(b[0] - w, b[1]), (mid[0] - w * 0.6, mid[1]), (tip[0], tip[1], 0.0), (mid[0] + w * 0.6, mid[1]), (b[0] + w, b[1]),
                            (b[0], b[1] + w * 0.6)])
            cv.fill(path, col, z=z + zz + i * 0.01, glow=GREEN_G if j == 0 else GREEN_HOT, alpha=0.92)
            if j == 0 and i % 2 == 0:
                cv.stroke([(b[0] - w * 0.8, b[1]), (mid[0] - w * 0.7, mid[1]), (tip[0], tip[1])], 0.8, z=z + 0.05, col=INK, taper=(0.3, 0.8), alpha=0.5)
    yk.sparks(cv, (c[0], c[1] - s), 3 + int(3 * k), s * 0.6, s * 2.6, GREEN_HOT, z + 0.3, seed=seed + 5, w=1.0, glow=GREEN_G, ang=-math.pi / 2, spread=1.4)


def cursed_skull(cv, c, r, z, k=1.0, ph=0.0, rot=0.0):
    """Lanetli kafatası: küçük kemik kafatası, göz oyuklarında yeşil ateş, ardında alev."""
    ghost_fire(cv, (c[0] - r * 0.2, c[1] - r * 0.3), r * 0.7, k, ph, z - 0.5, seed=31)
    cr, sr = math.cos(rot), math.sin(rot)
    P = lambda x, y, *e: (c[0] + x * cr - y * sr, c[1] + x * sr + y * cr) + e
    sk = cv.blob([P(-r, -0.2 * r), P(-0.6 * r, -0.95 * r), P(0.4 * r, -r), P(r, -0.3 * r), P(0.9 * r, 0.35 * r), P(0.55 * r, 0.7 * r), P(0.6 * r, 1.05 * r, 0.0),
                  P(-0.2 * r, 1.05 * r, 0.0), P(-0.3 * r, 0.6 * r), P(-0.85 * r, 0.4 * r)])
    det = [('ink', [P(-0.1 * r, 0.75 * r), P(0.1 * r, 1.0 * r)], 0.6), ('ink', [P(0.25 * r, 0.75 * r), P(0.35 * r, 1.0 * r)], 0.6),
           ('ink', [P(-0.5 * r, -0.6 * r), P(-0.2 * r, -0.2 * r)], 0.6)]
    cv.shape(sk, BONE, z=z, sd=r * 0.35, hi=0.3, ol=0.95, details=det)
    for q in (P(0.45 * r, 0.0), P(-0.05 * r, 0.05 * r)):
        cv.fill(cv.ellipse(q, r * 0.26, r * 0.3), INK, z=z + 0.1)
        yk.eye_glow(cv, q, r * 0.15, r * 0.18, 0, GREEN_HOT, GREEN_G, z + 0.2, halo=2.4, halo_a=0.45 * k)


def horse_skull(cv, top, ang, z, rattle=0.0):
    """Asa ucundaki at kafatası (öne bakar) + bağlı kemik çıngıraklar."""
    D = _d(ang)
    N = (-D[1], D[0])     # asaya dik, öne
    F = (N[0], N[1]) if N[0] > 0 else (-N[0], -N[1])
    Q = lambda a, b, *e: (top[0] + (F[0] * a + D[0] * b) * 1.3, top[1] + (F[1] * a + D[1] * b) * 1.3) + e
    sk = cv.blob([Q(-2.6, 0.6), Q(-2.2, 2.4), Q(0.6, 2.8), Q(5.2, 1.8), Q(7.0, 1.0, 0.0), Q(6.8, -0.2), Q(3.6, -0.6), Q(0.6, -1.4), Q(-1.8, -1.0)])
    det = [('deep', cv.ellipse(Q(0.8, 1.1), 0.9, 0.75)), ('ink', [Q(3.0, -0.4), Q(6.6, -0.1)], 0.7),
           ('ink', [Q(4.2, -0.5), Q(4.4, 0.2)], 0.5), ('ink', [Q(5.4, -0.3), Q(5.6, 0.3)], 0.5), ('deep', cv.ellipse(Q(6.4, 0.9), 0.35, 0.3))]
    cv.shape(sk, BONE, z=z, sd=0.9, hi=0.35, ol=1.0, details=det)
    q = Q(0.8, 1.1)
    yk.eye_glow(cv, q, 0.45, 0.4, 0, GREEN_HOT, GREEN_G, z + 0.1, halo=2.6, halo_a=0.4)
    # sarkan kemik çıngıraklar + şeritler
    for k in range(3):
        b = Q(-1.2 + k * 1.4, -1.0)
        e = (b[0] + math.sin(rattle + k) * 0.8, b[1] + 3.2 + k * 0.4)
        cv.stroke([b, e], 0.8, z=z - 0.2, col=(0.35, 0.22, 0.18))
        cv.shape(cv.ellipse(e, 0.6, 0.9, 0.3 * math.sin(rattle + k)), BONE if k != 1 else Ink(BEADS[1]), z=z - 0.1 + k * 0.01, sd=0.25, ol=0.6)
    for k in range(2):   # kızıl şerit
        b = Q(-2.2, -0.2 + k * 0.6)
        pts = [b, (b[0] - 2.0 + math.sin(rattle + k) * 0.6, b[1] + 2.0), (b[0] - 3.2 + math.sin(rattle * 1.3 + k) * 0.9, b[1] + 4.6)]
        cv.shape(ik.taper_path([cv.W(p) for p in pts], cv.u(1.1), (0.1, 0.8)), CLOAK if k == 0 else OCHRE, z=z - 0.3, sd=0.3, ol=0.7)
    return Q(2.0, -2.2)


def staff(cv, g, sa, z, fire, ph, rattle):
    """Eğri asa: g kavrayış, sa yukarı doğrultu. Döner: asa ucu (kafatasının üstü, ateş çıkışı)."""
    D = _d(sa)
    N = (-D[1], D[0])
    bot = (g[0] - D[0] * 12.0, g[1] - D[1] * 12.0)
    top = (g[0] + D[0] * 12.0, g[1] + D[1] * 12.0)
    pts = [bot, (lerp2(bot, top, 0.3)[0] + N[0] * 0.6, lerp2(bot, top, 0.3)[1] + N[1] * 0.6), (lerp2(bot, top, 0.6)[0] - N[0] * 0.7, lerp2(bot, top, 0.6)[1] - N[1] * 0.7),
           (lerp2(bot, top, 0.85)[0] + N[0] * 0.5, lerp2(bot, top, 0.85)[1] + N[1] * 0.5), top]
    cv.shape(ik.taper_path([cv.W(p) for p in pts], cv.u(2.0), prof=lambda u: 0.7 + 0.3 * u), WOOD, z=z, sd=0.5, hi=0.25, ol=0.9,
             details=[('ink', [pts[1], lerp2(pts[1], pts[2], 0.3)], 0.6), ('ink', [lerp2(pts[2], pts[3], 0.5), (lerp2(pts[2], pts[3], 0.5)[0] + N[0], lerp2(pts[2], pts[3], 0.5)[1] + N[1])], 0.6)])
    # budak
    kb = lerp2(pts[2], pts[3], 0.3)
    cv.shape(ik.taper_path([cv.W(kb), cv.W((kb[0] + N[0] * 2.0 + D[0] * 1.2, kb[1] + N[1] * 2.0 + D[1] * 1.2))], cv.u(1.0), (0.0, 0.9)), WOOD, z=z - 0.05, sd=0.3, ol=0.8)
    up = horse_skull(cv, top, sa, z + 0.3, rattle)
    ghost_fire(cv, up, 1.8, fire, ph, z + 0.6, seed=int(ph * 3) % 9)
    return up


def _arm(cv, sh, target, mat, z, bend=1.0, claw_ang=None):
    el, h = yg.ik2(sh, target, 6.3, 6.3, bend)
    cv.shape(cv.limb([sh, el, h], [1.3, 1.0, 0.85]), mat, z=z, sd=0.5, hi=0.25, ol=0.9)
    a = claw_ang if claw_ang is not None else math.atan2(h[1] - el[1], h[0] - el[0])
    yk.bone_hand(cv, h, a, mat, z + 0.1, n=3, L=2.4, spread=0.45, curl=0.7, r=0.4, palm=0.9)
    for k in range(3):   # kara tırnaklar
        aa = a + (k - 1) * 0.45
        q = (h[0] + math.cos(aa) * 2.0 + math.cos(aa + 0.7) * 1.2, h[1] + math.sin(aa) * 2.0 + math.sin(aa + 0.7) * 1.2)
        cv.stroke([q, (q[0] + math.cos(aa + 1.2) * 0.9, q[1] + math.sin(aa + 1.2) * 0.9)], 0.9, z=z + 0.3, col=INK, taper=(0.1, 0.9))
    return h


def _leg(cv, hp, foot, mat, z, near=True):
    """İnce, ters dizli (parmak ucunda) bacak + pençeli ayak."""
    ank = (foot[0] - 2.2, foot[1] - 3.0)
    kn, a2 = yg.ik2(hp, ank, 6.2, 6.0, -1.0)
    cv.shape(cv.limb([hp, kn, a2, foot], [1.5, 1.0, 0.75, 0.7]), mat, z=z, sd=0.5, hi=0.25 if near else 0.0, ol=0.9)
    for k in range(3):   # üç pençe parmak
        aa = -0.35 + k * 0.35
        tip = (foot[0] + math.cos(aa) * 2.4, foot[1] + math.sin(aa) * 1.2 + 0.4)
        cv.shape(ik.taper_path([cv.W(foot), cv.W(lerp2(foot, tip, 0.6)), cv.W(tip)], cv.u(0.8), (0.0, 0.9)), mat, z=z + 0.1 + k * 0.01, sd=0.2, ol=0.7)
        cv.stroke([tip, (tip[0] + 0.8, tip[1] + 0.5)], 0.9, z=z + 0.2, col=INK, taper=(0.1, 0.9))
    return foot


def rune_circle(cv, c, k, ph, z):
    """Yerde yeşil mürekkep runa çemberi (yassı elips): iki halka + eski Türk runası benzeri işaretler."""
    if k <= 0.02:
        return
    a = min(1.0, k)
    rx, ry = 11.0, 2.6
    for (sx, w) in ((1.0, 1.6), (0.72, 1.1)):
        ring = [(c[0] + math.cos(t) * rx * sx, c[1] + math.sin(t) * ry * sx) for t in np.linspace(0, math.tau, 33)]
        cv.stroke(ring, w + 1.2, z=z, col=INK, taper=(0.0, 0.0), alpha=0.7 * a)
        cv.stroke(ring, w, z=z + 0.01, col=GREEN, taper=(0.0, 0.0), glow=GREEN_G, alpha=a)
    for i in range(8):
        t = i / 8 * math.tau + ph * 0.3
        q = (c[0] + math.cos(t) * rx * 0.86, c[1] + math.sin(t) * ry * 0.86)
        cv.stroke([(q[0], q[1] - 0.9), (q[0], q[1] + 0.5)], 1.0, z=z + 0.02, col=GREEN_HOT, taper=(0.1, 0.1), glow=GREEN_G, alpha=a)
        cv.stroke([(q[0], q[1] - 0.6), (q[0] + 0.7 * (1 if i % 2 else -1), q[1] - 0.1)], 0.9, z=z + 0.02, col=GREEN_HOT, taper=(0.1, 0.4), glow=GREEN_G, alpha=a)
    yk.glow_soft(cv, c, rx * (0.8 + 0.4 * k), GREEN_G, z=z - 0.1, blur=0.7, alpha=0.35 * a, ry=ry * 2.2)


# ------------------------------------------------------------------ gövde
def body(cv, p):
    ph = p['ph']
    cs = p['cs']
    out = {}
    # arka kol (kafatası atışında da serbest)
    shb, shf = (1.0, -28.0), (5.4, -27.2)
    _arm(cv, shb, p['h2'], SKIN_B, -12, bend=1.0)
    # bacaklar: yerde ayak hedefleri dünyada
    f = cv.xf[-1]
    hb, hf = f((-1.6, -14.0)), f((1.8, -14.0))
    cv.pop()
    _leg(cv, hb, p['fb'], SKIN_B, -9, False)
    _leg(cv, hf, p['ff'], SKIN, -7, True)
    cv.push(f)
    # yırtık pelerin: kambur sırt, yamalar, kemik nazarlıklar
    hem = yk.ragged((7.4 + cs * 0.4, -11.0), (-6.8 + cs, -10.2), 6, 3.8, seed=3, side=-1.0)
    cloak = cv.blob([(-1.0, -32.0), (3.4, -31.0), (7.0, -27.6), (7.8, -21.0), (8.0, -15.0), (7.4 + cs * 0.4, -11.0, 0.0)] + hem +
                    [(-6.8 + cs, -10.2, 0.0), (-7.0 + cs * 0.6, -16.0), (-6.4, -24.0), (-4.4, -30.0)])
    det = []
    det += cv.fold([(1.0, -29.0), (0.0, -20.0), (-1.4 + cs * 0.5, -11.0)], 0.9, 1.2, 1)
    det += cv.fold([(5.6, -24.0), (5.4, -17.0), (5.0 + cs * 0.3, -11.0)], 0.8, 1.0, -1)
    det.append(('col', cv.blob([(-6.8, -24.0), (-2.6, -25.0), (-2.2, -19.0), (-7.0, -18.4)]), OCHRE.base))
    det.append(('col', cv.blob([(2.2, -18.0), (6.4, -18.6), (6.8, -13.6), (2.4, -13.0)]), RAG3.base))
    det.append(('col', cv.blob([(-5.0, -15.0), (-1.4, -15.4), (-1.6, -12.0), (-5.2, -11.6)]), OCHRE.shadow))
    for (a, b) in (((-6.8, -24.0), (-2.6, -25.0)), ((-2.6, -25.0), (-2.2, -19.0)), ((2.2, -18.0), (6.4, -18.6)), ((2.4, -13.0), (2.2, -18.0))):
        det.append(('ink', [a, b], 0.6, (0.0, 0.0)))
        for k in range(3):   # dikiş
            q = lerp2(a, b, 0.25 + k * 0.25)
            det.append(('stroke', [(q[0] - 0.3, q[1] - 0.5), (q[0] + 0.3, q[1] + 0.5)], 0.6, (0.85, 0.75, 0.55), (0.1, 0.1)))
    cv.shape(cloak, CLOAK, z=0, sd=2.0, hi=0.45, ol=1.0, details=det, hatch=0.35, bounce=0.25)
    # yaka: kemik nazarlıklar ve muska dizisi
    for k in range(4):
        x = 2.0 + k * 1.6
        y = -27.5 + k * 0.6
        e = (x + math.sin(ph + k) * 0.4, y + 2.6 + (k % 2) * 0.8)
        cv.stroke([(x, y), e], 0.8, z=4, col=(0.3, 0.2, 0.16))
        if k % 2 == 0:
            cv.shape(cv.blob([(e[0] - 0.6, e[1]), (e[0] + 0.6, e[1]), (e[0] + 0.3, e[1] + 2.0, 0.0), (e[0] - 0.3, e[1] + 2.0, 0.0)]), BONE, z=4.1 + k * 0.01, sd=0.3, ol=0.7)
        else:
            cv.shape(cv.ellipse((e[0], e[1] + 0.6), 0.7, 0.7), Ink(BEADS[k % 3]), z=4.1 + k * 0.01, sd=0.3, ol=0.7)
    # kemerden sarkan küçük kemik fetiş (kuş kafatası)
    q = (6.6, -12.0)
    cv.stroke([q, (q[0] + 0.3 + cs * 0.3, q[1] + 2.4)], 0.8, z=4, col=(0.3, 0.2, 0.16))
    cv.shape(cv.blob([(q[0] - 0.9, q[1] + 2.2), (q[0] + 1.0, q[1] + 2.0), (q[0] + 2.4 + cs * 0.3, q[1] + 3.2, 0.0), (q[0] + 0.6, q[1] + 3.8), (q[0] - 0.8, q[1] + 3.4)]),
             BONE, z=4.2, sd=0.4, ol=0.8, details=[('deep', cv.ellipse((q[0] + 0.1, q[1] + 2.8), 0.35, 0.35))])
    # ---- baş
    hc = (8.6 + p['hx'], -30.0 + p['hy'])
    u29.body_xf(cv, (hc[0] - 1.0, hc[1] + 2.0), 0.0, 1.42, 1.42)   # iri baş (abartılı oran)
    ear = p['ear']
    # arka kulak + arka boynuz
    cv.shape(cv.blob([(hc[0] - 2.0, hc[1] - 2.4), (hc[0] - 6.0, hc[1] - 4.6 - ear), (hc[0] - 10.5, hc[1] - 7.4 - ear * 2, 0.0), (hc[0] - 5.4, hc[1] - 1.8), (hc[0] - 2.0, hc[1] - 0.6)]),
             SKIN_B, z=1.0, sd=0.5, ol=0.85)
    _horn(cv, (hc[0] - 0.6, hc[1] - 3.6), 0.82, HORN.darker(0.72), 1.2, ph, beads=False)
    head = cv.blob([(hc[0] - 3.6, hc[1] - 1.6), (hc[0] - 2.0, hc[1] - 4.2), (hc[0] + 1.6, hc[1] - 4.8), (hc[0] + 4.2, hc[1] - 3.2), (hc[0] + 5.6, hc[1] - 1.2),
                    (hc[0] + 6.6, hc[1] + 0.8, 0.0), (hc[0] + 5.6, hc[1] + 2.4), (hc[0] + 2.6, hc[1] + 3.8), (hc[0] - 0.6, hc[1] + 3.2), (hc[0] - 3.2, hc[1] + 1.4)])
    cv.shape(head, SKIN, z=8, sd=1.2, hi=0.35, ol=1.0, bounce=0.2,
             details=[('ink', [(hc[0] + 0.2, hc[1] - 2.8), (hc[0] + 2.2, hc[1] - 3.4)], 0.6), ('shade', cv.ellipse((hc[0] - 1.4, hc[1] + 1.0), 2.2, 2.0))])
    # sırıtış: geniş ağız, eğri dişler
    g = p['grin']
    mouth = cv.blob([(hc[0] + 0.4, hc[1] + 0.8), (hc[0] + 3.2, hc[1] + 1.2), (hc[0] + 6.4, hc[1] + 0.6, 0.0), (hc[0] + 5.4, hc[1] + 2.0 + g * 1.4),
                     (hc[0] + 2.6, hc[1] + 2.6 + g * 1.6), (hc[0] + 0.8, hc[1] + 1.8 + g * 0.6)])
    cv.shape(mouth, Ink('#2a0e1c', '#16060e', '#4a1a2c'), z=9, sd=0.3, ol=0.9, details=[('col', cv.ellipse((hc[0] + 3.0, hc[1] + 2.0 + g), 1.3, 0.5 + 0.4 * g), (0.5, 0.12, 0.2))])
    for k, (x, up, ln) in enumerate(((1.2, 1, 1.0), (2.2, 1, 1.3), (3.3, 1, 0.9), (4.4, 1, 1.2), (5.4, 1, 0.8), (2.0, -1, 0.9), (3.8, -1, 1.1), (5.0, -1, 0.7))):
        y0 = hc[1] + (1.05 if up > 0 else 2.2 + g * 1.4)
        tq = (hc[0] + x + 0.25 * ((k * 37) % 3 - 1), y0 + up * ln)
        cv.shape(cv.blob([(hc[0] + x - 0.45, y0), (hc[0] + x + 0.45, y0), (tq[0], tq[1], 0.0)]), TOOTH, z=9.2 + k * 0.01, sd=0.15, ol=0.55)
    # kancalı burun
    cv.shape(cv.blob([(hc[0] + 4.0, hc[1] - 2.6), (hc[0] + 6.6, hc[1] - 1.6), (hc[0] + 7.6, hc[1] + 0.2, 0.0), (hc[0] + 5.8, hc[1] - 0.2), (hc[0] + 4.4, hc[1] - 0.6)]),
             SKIN, z=10, sd=0.5, hi=0.3, ol=0.9, details=[('ink', [(hc[0] + 5.6, hc[1] - 0.4), (hc[0] + 6.0, hc[1] - 0.8)], 0.5)])
    # gözler: iri yeşil + kısık
    ey = p['eye']
    big = (hc[0] + 3.0, hc[1] - 2.0)
    if ey < 0.3:
        cv.stroke([(big[0] - 1.4, big[1] - 0.6), (big[0], big[1] + 0.3), (big[0] + 1.4, big[1] - 0.6)], 1.1, z=11, col=INK, taper=(0.2, 0.2))
    else:
        rr = 1.3 + 0.25 * (ey - 1)
        cv.shape(cv.ellipse(big, rr + 0.5, rr + 0.35), Ink('#14101a', '#0a080c', '#2a2232'), z=10.5, sd=0.2, ol=0.8)
        yk.eye_glow(cv, big, rr, rr * 0.92, 0, GREEN, GREEN_G, 11, halo=2.2 + 0.5 * ey, halo_a=0.35 + 0.15 * ey)
        cv.fill(cv.ellipse((big[0] + 0.3, big[1]), 0.35, rr * 0.75), INK, z=11.1)
        cv.fill(cv.ellipse((big[0] - 0.35, big[1] - 0.45), 0.3, 0.25), GREEN_HOT, z=11.2, glow=GREEN_HOT)
    sq = (hc[0] - 0.4, hc[1] - 2.4)
    cv.stroke([(sq[0] - 1.0, sq[1] + 0.2), (sq[0] + 0.9, sq[1] - 0.1)], 1.0, z=11, col=INK, taper=(0.3, 0.3))
    cv.fill(cv.ellipse((sq[0], sq[1] + 0.1), 0.5, 0.2), GREEN, z=11.05, glow=GREEN_G)
    cv.stroke([(sq[0] - 1.2, sq[1] - 1.0), (sq[0] + 1.0, sq[1] - 0.6)], 0.9, z=11.1, col=INK, taper=(0.3, 0.6))
    cv.stroke([(big[0] - 1.8, big[1] - 1.9 - 0.3 * (ey > 1.5)), (big[0] + 1.6, big[1] - 1.4)], 1.0, z=11.3, col=INK, taper=(0.3, 0.6))
    # ön kulak: iri sivri, geriye
    earp = cv.blob([(hc[0] - 1.0, hc[1] - 2.0), (hc[0] - 5.0, hc[1] - 3.6 - ear), (hc[0] - 12.0, hc[1] - 5.8 - ear * 2.2, 0.0), (hc[0] - 5.6, hc[1] - 0.6),
                    (hc[0] - 1.6, hc[1] + 0.6)])
    cv.shape(earp, SKIN, z=12, sd=0.6, hi=0.3, ol=0.95,
             details=[('col', cv.blob([(hc[0] - 2.2, hc[1] - 1.4), (hc[0] - 9.5, hc[1] - 4.8 - ear * 2.0, 0.0), (hc[0] - 4.8, hc[1] - 1.0)]), EAR_IN),
                      ('ink', [(hc[0] - 6.0, hc[1] - 3.2), (hc[0] - 6.6, hc[1] - 2.2)], 0.5)])
    _horn(cv, (hc[0] + 0.8, hc[1] - 3.8), 1.0, HORN, 13, ph, beads=True)
    cv.pop()
    # ---- ön kol + asa
    up = staff(cv, p['g'], p['sa'], 16, p['fire'], ph, p['rattle'])
    _arm(cv, shf, p['g'], SKIN, 18, bend=-1.0, claw_ang=p['sa'] + math.pi / 2)
    out['hand'] = up
    if p['skull'] > 0:   # asa ucunda tutuşan kafatası (atış)
        so = p['soff']
        cursed_skull(cv, (up[0] + so[0], up[1] + so[1]), 1.6 + 0.6 * p['skull'], 20, k=p['skull'], ph=ph, rot=p['srot'])
    if p['sm'][2] > 0.05:   # savuruş izi
        a0, a1, k = p['sm']
        cc, R = p['g'], 15.0
        ang = np.linspace(a0, a1, 9)
        outer = [(cc[0] + math.cos(a) * R, cc[1] + math.sin(a) * R) for a in ang]
        inner = [(cc[0] + math.cos(a) * R * (0.6 + 0.3 * (1 - u)), cc[1] + math.sin(a) * R * (0.6 + 0.3 * (1 - u))) for u, a in zip(np.linspace(0, 1, 9), ang)]
        yk.wash(cv, cv.blob(outer + inner[::-1]), GREEN, 0.25 * k, z=-20, glow=GREEN_G, glow_a=0.15 * k)
        cv.stroke(outer, 1.4, z=-19.9, col=GREEN_HOT, taper=(0.9, 0.1), glow=GREEN_G, alpha=0.8 * k)
    return out


def _horn(cv, b, s, mat, z, ph, beads=True):
    """Koç boynuzu: kafanın üstünden geriye-aşağı kıvrılan sarmal; boğum çizgileri; uçtan boncuk muskaları sarkar."""
    c = (b[0] - 2.6 * s, b[1] - 0.6 * s)
    pts = []
    for k in range(11):
        u = k / 10
        a = -0.2 - u * 4.9
        r = (3.2 - 2.1 * u) * s
        pts.append((c[0] + math.cos(a) * r * 1.1, c[1] + math.sin(a) * r))
    pts[0] = b
    path = ik.taper_path([cv.W(q) for q in pts], cv.u(3.3 * s), prof=lambda u: max(0.2, 1.0 - 0.75 * u))
    det = []
    for k in range(1, 9):
        q0, q1 = pts[k], pts[k + 1]
        tg = u29.norm2((q1[0] - q0[0], q1[1] - q0[1]))
        nn = (-tg[1], tg[0])
        w = (3.3 - 2.4 * k / 10) * s * 0.5
        det.append(('ink', [(q0[0] - nn[0] * w, q0[1] - nn[1] * w), (q0[0] + nn[0] * w, q0[1] + nn[1] * w)], 0.6, (0.2, 0.2)))
    cv.shape(path, mat, z=z, sd=0.6, hi=0.35, ol=0.95, details=det)
    if beads:
        e0 = pts[6]
        for j in range(2):
            x0 = e0[0] + j * 1.2
            y = e0[1]
            for i in range(3):
                q = (x0 + math.sin(ph + j + i * 0.5) * 0.3, y + 1.2 + i * 1.15)
                cv.shape(cv.ellipse(q, 0.55, 0.55), Ink(BEADS[(i + j) % 3]), z=z + 0.2 + i * 0.01 + j * 0.05, sd=0.2, hi=0.15, ol=0.6)
            cv.stroke([(x0, y), (x0, y + 1.0)], 0.7, z=z + 0.15, col=(0.3, 0.2, 0.16))


def draw_body(cv, p):
    u29.body_xf(cv, HIP, p['rot'], p['sx'], p['sy'], (p['dx'], p['dy']))
    info = body(cv, p)
    hand = u29.to_world(cv, info['hand'])
    cv.pop()
    # yer efektleri (dünya)
    rune_circle(cv, (11.0, -0.4), p['rune'], p['ph'], -40)
    if p['burst'] > 0:
        k = p['burst']
        for i in range(5):
            x = 11.0 + (i - 2) * 4.4
            ghost_fire(cv, (x, -0.5), 2.2 + 1.2 * k * (1.0 - abs(i - 2) * 0.2), k, p['ph'] + i, 30 + i * 0.1, seed=40 + i)
        yk.sparks(cv, (11.0, -6.0), 10, 3.0, 14.0 * k, GREEN_HOT, 34, seed=12, w=1.3, glow=GREEN_G, ang=-math.pi / 2, spread=2.4)
        yk.glow_soft(cv, hand, 6.0 * k, GREEN_G, z=34, alpha=0.6 * k)
        ring = [(hand[0] + math.cos(t) * (2.0 + 5.0 * k), hand[1] + math.sin(t) * (2.0 + 5.0 * k)) for t in np.linspace(0, math.tau, 20)]
        cv.stroke(ring, 1.6 * (1.2 - k * 0.6), z=34.1, col=GREEN_HOT, taper=(0.0, 0.0), glow=GREEN_G, alpha=0.9)
    if p['puff'] > 0:
        import y39_yer_cucesi as yc
        yc.dust(cv, (p['dx'], -1.0), 3.0 * p['puff'] + 1.0, 27, seed=7, n=3, alpha=0.45)
    return {'hand': hand}


# ================================================================== pozlar
REST = dict(dx=0.0, dy=0.0, rot=0.12, sx=1.0, sy=1.0, fb=(-3.2, 0.0), ff=(4.0, 0.0), g=(15.0, -20.0), sa=-1.15, h2=(4.0, -18.0),
            hx=0.0, hy=0.0, ear=0.0, eye=1.0, grin=0.3, fire=0.6, rattle=0.0, cs=0.0, skull=0.0, soff=(0.0, -2.0), srot=0.0,
            sm=(0.0, 0.0, 0.0), rune=0.0, burst=0.0, puff=0.0)


def _idle(t):
    a = math.tau * t
    s = math.sin(a)
    return dict(dy=0.5 * (1 - math.cos(a)) * 0.5, sy=1.0 - 0.02 * s, rot=0.12 + 0.03 * s, hy=0.4 * math.sin(a - 0.6), hx=0.3 * math.sin(a * 2),
                g=(15.0, -20.0 + 0.3 * s), sa=-1.15 + 0.04 * s, ear=0.5 * math.sin(a * 2 + 1), grin=0.3 + 0.2 * math.sin(a * 2),
                fire=0.6 + 0.2 * math.sin(a * 3), rattle=a * 2, cs=0.6 * math.sin(a), h2=(4.0 + 0.5 * s, -18.0), eye=1.0 if int(t * 8) != 5 else 1.6, ph=a)


def _move(t):
    a = math.tau * t
    s = math.sin(a)
    stp = 4.2
    fb = (-0.2 - stp * math.cos(a), max(0.0, math.sin(a)) * 2.6)
    ff = (1.0 + stp * math.cos(a), max(0.0, -math.sin(a)) * 2.6)
    return dict(dy=1.4 - abs(s) * 1.0, rot=0.3 + 0.05 * math.sin(2 * a), fb=(fb[0], -fb[1]), ff=(ff[0], -ff[1]), hy=1.0 + 0.5 * math.sin(2 * a),
                g=(15.0 + 0.6 * s, -18.5 - 0.6 * abs(s)), sa=-1.0 + 0.08 * s, ear=-0.6 + 0.6 * math.sin(2 * a), grin=0.5, fire=0.6, rattle=a * 3,
                cs=-1.4 + 0.8 * math.sin(2 * a + 1), h2=(2.0 - 2.0 * s, -18.0), ph=a)


_HURT = [dict(dx=-2.0, rot=-0.22, sx=1.05, sy=0.94, hx=-1.0, hy=0.6, eye=0.0, grin=1.0, ear=1.6, g=(12.0, -22.0), sa=-1.6, fire=0.3, cs=1.6, h2=(-2.0, -24.0)),
         dict(dx=-2.5, rot=-0.1, hx=-0.6, eye=0.0, grin=0.7, ear=1.0, g=(13.0, -21.0), sa=-1.4, fire=0.4, cs=1.0, h2=(0.0, -21.0)),
         dict(dx=-1.2, rot=0.06, eye=1.0, grin=0.4, ear=0.4, g=(14.4, -20.0), sa=-1.2, fire=0.5, cs=0.4)]

# çağırma: asa havaya kalkar, runa çemberi tutuşur, TEMAS = yeşil ateş patlaması
_SUM = [dict(rot=0.08, g=(14.5, -22.0), sa=-1.3, fire=0.8, grin=0.5, rune=0.0),
        dict(rot=-0.02, dy=-0.6, g=(13.0, -25.0), sa=-1.45, fire=1.0, grin=0.7, eye=1.4, rune=0.3, h2=(2.0, -22.0), rattle=1.0),
        dict(rot=-0.12, dy=-1.2, sy=1.04, g=(12.0, -25.5), sa=-1.55, fire=1.3, grin=0.9, eye=1.8, rune=0.55, h2=(-1.0, -27.0), rattle=2.0, ear=0.8, hy=-0.8),
        dict(rot=-0.18, dy=-1.6, sy=1.06, g=(11.5, -26.0), sa=-1.62, fire=1.6, grin=1.0, eye=2.0, rune=0.8, h2=(-2.0, -29.0), rattle=3.0, ear=1.2, hy=-1.0),
        dict(rot=-0.2, dy=-1.8, sy=1.07, g=(11.2, -26.2), sa=-1.66, fire=1.8, grin=1.0, eye=2.0, rune=0.95, h2=(-2.4, -30.0), rattle=4.0, ear=1.4, hy=-1.2),
        dict(rot=0.32, dy=1.2, sy=0.92, sx=1.06, g=(16.5, -17.0), sa=-1.05, fire=2.0, grin=1.0, eye=2.0, rune=1.2, burst=0.35, h2=(6.0, -16.0), ear=-0.6,
             sm=(-1.9, -1.25, 0.8), cs=-1.0),
        dict(rot=0.36, dy=1.4, sy=0.92, sx=1.06, g=(17.0, -16.0), sa=-1.0, fire=1.6, grin=1.0, eye=2.0, rune=1.1, burst=0.85, h2=(6.0, -16.0), ear=-0.8, cs=-1.2),
        dict(rot=0.3, dy=1.0, g=(16.5, -17.0), sa=-1.05, fire=1.0, grin=0.8, eye=1.6, rune=0.6, burst=1.0, h2=(5.0, -17.0), cs=-0.6),
        dict(rot=0.16, dy=0.3, g=(15.0, -19.5), sa=-1.15, fire=0.7, grin=0.5, eye=1.0, rune=0.15, h2=(4.0, -18.0))]
_SUM_TS = [0.0, 0.1, 0.2, 0.3, 0.38, 0.46, 0.56, 0.7, 0.85]
_SUM_MK = [0.38, 0.46, 0.7]

# kafatası: asa ucunda kafatası tutuşur, asa omuz üstünden geriye kurulur, öne savrulur, TEMAS karesinde kafatası fırlar
_SKL = [dict(rot=0.1, g=(14.5, -21.0), sa=-1.25, fire=0.8, skull=0.3, grin=0.6),
        dict(rot=-0.08, g=(11.0, -25.5), sa=-1.8, fire=1.0, skull=0.6, grin=0.8, eye=1.5, h2=(1.0, -20.0), rattle=1.0),
        dict(rot=-0.22, dy=0.6, g=(8.0, -27.0), sa=-2.3, fire=1.3, skull=0.9, grin=1.0, eye=2.0, ear=0.8, h2=(0.0, -21.0), rattle=2.0, cs=1.0),
        dict(rot=-0.28, dy=0.9, sy=1.04, g=(7.0, -27.0), sa=-2.5, fire=1.5, skull=1.0, grin=1.0, eye=2.0, ear=1.2, h2=(-0.5, -21.0), rattle=3.0, cs=1.3),
        dict(rot=0.05, g=(12.0, -27.0), sa=-1.3, fire=1.6, skull=1.0, grin=1.0, eye=2.0, sm=(-2.6, -1.5, 0.7), h2=(2.0, -20.0)),
        dict(rot=0.28, dy=1.0, sy=0.95, g=(16.5, -22.0), sa=-0.6, fire=1.4, skull=1.0, soff=(3.0, -1.2), srot=0.6, grin=1.0, eye=2.0, sm=(-1.9, -0.8, 1.0),
             h2=(5.0, -17.0), ear=-0.6, cs=-1.0),
        dict(rot=0.32, dy=1.2, sy=0.94, g=(17.0, -19.0), sa=-0.45, fire=0.6, grin=0.9, eye=1.5, sm=(-1.2, -0.55, 0.4), h2=(5.0, -17.0), ear=-0.8, cs=-1.2),
        dict(rot=0.16, dy=0.4, g=(15.0, -20.0), sa=-1.15, fire=0.6, grin=0.5, h2=(4.0, -18.0))]
_SKL_TS = [0.0, 0.14, 0.27, 0.38, 0.47, 0.53, 0.68, 0.84]
_SKL_MK = [0.38, 0.53, 0.84]

# geri sıçrayış
_HOP = [dict(dy=2.0, sy=0.86, sx=1.1, rot=0.2, fb=(-4.0, 0.0), ff=(3.0, 0.0), ear=-0.6, grin=0.8, g=(14.0, -18.0), sa=-1.1, cs=-0.4),
        dict(dy=-4.5, dx=-3.0, sy=1.08, sx=0.94, rot=-0.15, fb=(-6.0, -3.0), ff=(-1.0, -3.6), ear=1.4, grin=1.0, eye=1.6, g=(13.0, -23.0), sa=-1.5, cs=1.6,
             h2=(-1.0, -24.0)),
        dict(dy=-4.0, dx=-5.0, rot=-0.08, fb=(-7.5, -1.6), ff=(-2.0, -2.4), ear=1.0, grin=0.8, g=(13.5, -21.0), sa=-1.35, cs=1.2, h2=(1.0, -20.0)),
        dict(dy=1.6, dx=-5.5, sy=0.9, sx=1.06, rot=0.22, fb=(-8.8, 0.0), ff=(-2.2, 0.0), ear=-0.4, grin=0.5, g=(13.5, -18.0), sa=-1.1, cs=-0.6, puff=0.7)]


def _row(frames, fps, loop, pose, ts=None, mk=None, vx=None):
    return dict(frames=frames, fps=fps, loop=loop, pose=pose, ts=ts, mk=mk, vx=vx)


ROWS = {
    'idle': _row(8, 9, True, _idle),
    'move': _row(8, 11, True, _move, vx=55.0),
    'hurt': _row(3, 14, False, _HURT),
    'atk_summon': _row(9, 12, False, _SUM, ts=_SUM_TS, mk=_SUM_MK),
    'atk_skull': _row(8, 12, False, _SKL, ts=_SKL_TS, mk=_SKL_MK),
    'hop': _row(4, 10, False, _HOP),
}

DURUM = {"idle": "idle", "chase": "move", "recover": "idle", "evade": "hop", "_hurt": "hurt", "_hurt_big": "hurt", "_break": "hurt"}
for _m in ('summon', 'skull'):
    for _k in ('windup', 'act', 'recover'):
        DURUM['%s/%s' % (_k, _m)] = 'atk_' + _m


def anims_for(var='sulmus'):
    return {k: {kk: vv for kk, vv in r.items() if kk != 'pose'} for k, r in ROWS.items()}


def durum_for(var='sulmus'):
    return DURUM


def pose_of(anim, i):
    r = ROWS[anim]
    src = r['pose'](i / r['frames']) if callable(r['pose']) else r['pose'][i]
    p = dict(REST, **src)
    if 'ph' not in src:
        p['ph'] = i * 0.9
    return p


SHADE = dict(outer=0.5, rim=0.7, rim_col=(0.7, 0.78, 1.0), rim_dir=(0.6, -0.8), rim_w=1.3, form=(4.0, (0.78, 0.74, 0.88)))


def render_frame(anim, i, var='sulmus', ss=3):
    p = pose_of(anim, i)
    cv = u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss)
    info = draw_body(cv, p)
    rgba, _nm, em = cv.finish(**SHADE)
    h = info['hand']
    return rgba, None, em, {'hand': (round(float(h[0]), 2), round(float(h[1]), 2))}
