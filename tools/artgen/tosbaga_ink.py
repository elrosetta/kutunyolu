"""Taş Tosbağa (kimlik tosbaga; Taş Gulü ve Buz Tosbağası aynı çizimi tonla kullanır) — stil v2 "mürekkep-cel".
v1: creatures2.draw_tosbaga ('mouth' çapası).

Şahmeran mağarasının zırhlı bekçisi: yüksek kubbe kabuk yontulmuş taş plakalardan (sırt, yan ve kenar sıraları; her
plaka ayrı yüzey: ışık yanı açık, alt kenarı gölge, aralarında mürekkep oluk), plakalarda yosun ve çatlak, sırtta
mağara kristalleri (ışır). Kalın pullu fil bacakları ve kalın tırnaklar, kancalı gagalı iri baş (kaş çıkıntısı,
kristalden soluk göz), kısa dikenli kuyruk.

v29 tam gövde animasyonu (docs/TASARIM.md "v29: yer yaratıklarının tam gövde animasyonu"; referans kara_boru_ink.py):
* bütün figür dönüşümü (x / y / roll / yaw: dönüşte yanal daralma) gövde merkezinde; kabuk kendi merkezinde eğilir
  (pitch: öne / arkaya yalpalama) ve ezilir (sq);
* AYAK HEDEFLİ bacaklar: dört ayağın yerdeki yeri (x, yerden yükseklik, taban açısı) yazılır, sütun bacak ik2 ile
  çözülür (diz önde); omuz / kalça kökü kabuğun içinde ayakla birlikte biraz kayar (kuşak dönüşü: adım boyu artar);
  erişilemeyen hedef kırpılır;
* boyun uzar / kabuğa çekilir (nk: -1 içeride, 0 dinlenme, +1 ısırık atılışı), baş boyun ucunda döner (hr), gaga açılır
  (jaw), göz alevlenir (eye) / kırpar (blink) / sersemler (dizzy: sarmal); baş -0,7'den derine çekilince kabuğun
  arkasına geçer (yalnızca gaga ucu görünür);
* kabuğa çekilme (hide 0..1: bacaklar kısalıp içeri girer, kabuk plastronuna oturur), yuvarlanma (spin: kabuk döner,
  kristal uçlarından ışık izi, hız yayları);
* kristaller: ışıma (glow), dikleşme (cr), sönme (dim: ölüm); kuyruk sallanır (tw).
Kareler yaratik_govde.Seq ile anahtar pozlardan; yapay zekâ (Enemy._ai_turtle) eşlemesi DURUM.
"""
import math

import inkkit as ik
from inkkit import Ink, INK
from rig import lerp2
from bengu_ink import along
import yaratik_govde as yg
import yaratik_ink_kit as yk
from yaratik_govde import Seq

TEX = 4.0
CELL = (416, 288)        # dünya 104 x 72 (v1: 96 x 64)
FEET = (192, 272)        # dünya (48, 68)

STONE = Ink('#909c90', '#454c5e', '#ccd6c4', '#262b3c', name='kabuk taşı')
STONE_D = Ink('#6c7774', '#343a4e', '#a2aca4', '#1e2232', name='kabuk kenarı')
MOSS = (0.36, 0.48, 0.30)
SKIN = Ink('#7c8656', '#3a4232', '#a9b67a', '#232a22', name='tosbağa derisi')
SKIN_B = SKIN.darker(0.72)
BELLY = Ink('#a59a6a', '#57503e', '#cfc492', name='karın kalkanı')
BEAK = Ink('#5a5040', '#28221e', '#8e8068', name='gaga')
CLAW = Ink('#d6c9a4', '#7a6c52', '#fffaea', name='tırnak')
CRYST = Ink('#86f0ee', '#2a8aa0', '#eaffff', '#14506a', name='kristal')
CRYST_DIM = Ink('#5a7c84', '#2a3c4a', '#8eaab0', '#162430', name='sönük kristal')
CRYST_GLOW = (0.20, 0.85, 0.95)
EYE = (0.6, 1.0, 0.98)
EYE_GLOW = (0.2, 0.9, 1.0)

RX, RY = 20.5, 13.5
LEG = 8.1          # sütun bacak parçası (v1 FK: 7,8; IK'de dizde pay kalsın diye biraz uzun)
CY0 = -19.44       # dinlenmede gövde (kabuk) merkezi yüksekliği (v1 ground() ile aynı)
CY_HIDE = -RY * 0.82   # kabuğa çekilince: plastron yere oturur
CY_SPIN = -15.2
C0 = (0.0, CY0)

# bacak kökleri (kabuk merkezine göre) ve dinlenmede ayak x'i (v1 FK: kök + 1,55)
BASES = {'hb': (-11.0, 4.0), 'fb': (10.0, 4.0), 'hf': (-9.0, 4.0), 'ff': (12.0, 4.0)}
FOOT0 = {k: b[0] + 1.55 for k, b in BASES.items()}

REST = dict(x=0.0, y=0.0, roll=0.0, yaw=0.0, pitch=0.0, sq=0.0,
            hb=(FOOT0['hb'], 0.0, 0.0), fb=(FOOT0['fb'], 0.0, 0.0), hf=(FOOT0['hf'], 0.0, 0.0), ff=(FOOT0['ff'], 0.0, 0.0),
            nk=0.0, hd=(0.0, 0.0), hr=0.0, jaw=0.05, eye=0.0, blink=0.0, dizzy=0.0,
            glow=0.0, cr=0.0, dim=0.0, tw=0.0, hide=0.0, spin=0.0)


def FT(**kw):
    """Ayak hedefleri dinlenme yerine göre: FT(hf=(dx, h, taban), ...) -> mutlak demetler."""
    out = {}
    for k, v in kw.items():
        v = tuple(v) + (0.0,) * (3 - len(v))
        out[k] = (FOOT0[k] + v[0], v[1], v[2])
    return out


def _S(c, u, v, rx=RX, ry=RY):
    """Kabuk yüzeyi: u yatay (-1..1, en kesitine göre), v dikey (-1 tepe .. 1 alt)."""
    w = math.sqrt(max(0.0, 1.0 - min(1.0, v * v))) if v < 0 else 1.0
    return (c[0] + u * rx * w, c[1] + v * ry)


def _scute(cv, c, u, v, su, sv, mat, z, seed, rx=RX, ry=RY, ring=True):
    """Kubbe üstünde altıgen plaka: merkez (u, v) yüzey koordinatı, su/sv yarı boy (yüzey birimi). Kubbenin
    eğriliğini izler (köşeler _S ile eşlenir), köşeleri yuvarlatılmış; her plaka ayrı yüzey gölgesi alır."""
    pts = []
    for j in range(6):
        a = j / 6 * math.tau + math.pi / 6
        q = _S(c, u + math.cos(a) * su, v + math.sin(a) * sv, rx, ry)
        pts.append((q[0], q[1], 0.55))
    path = cv.blob(pts)
    det = []
    r = (math.sin(seed * 12.9898) * 43758.5453) % 1.0
    ctr = _S(c, u, v, rx, ry)
    # büyüme halkası: içte küçük eş plaka çizgisi (yontu izi)
    inner = [_S(c, u + math.cos(j / 6 * math.tau + math.pi / 6) * su * 0.55, v + math.sin(j / 6 * math.tau + math.pi / 6) * sv * 0.55, rx, ry) for j in range(7)]
    if ring:
        det.append(('ink', inner[2:6], 0.8, (0.2, 0.2)))
    if r > 0.5:
        det.append(('ink', [ctr, _S(c, u + su * 0.5, v + sv * 0.4, rx, ry), _S(c, u + su * 0.4, v + sv * 0.95, rx, ry)], 0.9, (0.1, 0.8)))
    if r < 0.4:
        q = _S(c, u - su * 0.2, v - sv * 0.45, rx, ry)
        det.append(('col', cv.blob([(q[0] - 1.8, q[1] + 0.2), (q[0] - 0.4, q[1] - 0.9), (q[0] + 1.6, q[1] - 0.4), (q[0] + 0.8, q[1] + 0.9)]), MOSS))
    cv.shape(path, mat, z=z, sd=1.6, hi=0.4, details=det, ol=0.8, bounce=0.25, cast=0.3)


CRYSTALS = ((-0.55, 6.0, -0.35), (-0.18, 9.5, -0.12), (0.2, 8.2, 0.1), (0.52, 5.4, 0.3))


def _crystal_tip(c, k, p):
    u, h, lean = CRYSTALS[k]
    base = _S((c[0], c[1] - 0.5), u, -0.9 + abs(u) * 0.35)
    h = h + (1.0 if p.get('hide', 0.0) >= 0.5 else 0.0) + 2.6 * p.get('cr', 0.0) * (1.0 if k in (1, 2) else 0.7)
    lean = lean * (1.0 + 0.6 * p.get('cr', 0.0))
    return base, (base[0] + math.sin(lean) * h, base[1] - math.cos(lean) * h), h, lean


def _shell(cv, c, p, z, rot=0.0):
    """Kabuk: alt plastron şeridi, gövde kubbesi, plakalar, kenar sırası, kristaller. rot: yuvarlanma açısı."""
    if rot:
        cr, sr = math.cos(rot), math.sin(rot)
        cv.push(lambda q, c=c: (c[0] + (q[0] - c[0]) * cr - (q[1] - c[1]) * sr, c[1] + (q[0] - c[0]) * sr + (q[1] - c[1]) * cr))
        # yuvarlanırken kabuk topa yakın (bacaklar/baş içeride): yerel x büzülür
        cv.push(lambda q, c=c: (c[0] + (q[0] - c[0]) * 0.78, c[1] + (q[1] - c[1]) * 1.04))
    # plastron (karın kalkanı) alt kenarda
    cv.shape(cv.ellipse((c[0], c[1] + RY * 0.42), RX * 0.95, RY * 0.42), BELLY, z=z - 0.2, sd=1.2,
             details=[('ink', [(c[0] + x, c[1] + RY * 0.25), (c[0] + x + 0.4, c[1] + RY * 0.75)], 1.0) for x in (-9, -3, 3, 9)])
    dome = ik.union(cv.ellipse((c[0], c[1] - 0.5), RX, RY), cv.ellipse((c[0], c[1] + 3.5), RX * 1.02, RY * 0.6))
    cv.shape(dome, STONE_D, z=z, sd=4.0, hi=0.0, deep=0.25, cast=1.0)
    # plakalar: sırt (3 büyük) + yan (4) + kenar (9 küçük); aralarında koyu oluk (kubbe tabanı)
    cc = (c[0], c[1] - 0.5)
    for i, u in enumerate((-0.5, 0.0, 0.5)):
        _scute(cv, cc, u, -0.66, 0.27, 0.3, STONE, z + 0.1, i + 1)
    for i, u in enumerate((-0.78, -0.27, 0.27, 0.78)):
        _scute(cv, cc, u, -0.06, 0.25, 0.32, STONE, z + 0.1, i + 7)
    for i in range(9):
        u = -0.93 + i * 0.2325
        _scute(cv, cc, u, 0.47, 0.125, 0.17, STONE_D, z + 0.12, i + 17, ring=False)
    # kristaller (sırtta, ışır): glow parlatır, cr dikleştirip uzatır, dim söndürür (ölüm)
    dim = p.get('dim', 0.0)
    gk = (1.0 + 1.4 * p.get('glow', 0.0)) * (1.0 - 0.9 * dim)
    mat = CRYST if dim < 0.5 else CRYST_DIM
    for k in range(4):
        base, tip, h, lean = _crystal_tip(c, k, p)
        w = 2.2 + h * 0.08
        nx, ny = math.cos(lean), math.sin(lean)
        cr_ = cv.blob([(base[0] - nx * w, base[1] - ny * w + 0.8), (lerp2(base, tip, 0.6)[0] - nx * w * 0.8, lerp2(base, tip, 0.6)[1] - ny * w * 0.8),
                       (tip[0], tip[1], 0.0), (lerp2(base, tip, 0.5)[0] + nx * w * 0.9, lerp2(base, tip, 0.5)[1] + ny * w * 0.9),
                       (base[0] + nx * w, base[1] + ny * w + 0.8)])
        det = [('ink', [(base[0] + nx * 0.2, base[1] + 0.4), lerp2(base, tip, 0.8)], 0.9, (0.1, 0.7)),
               ('hi', cv.blob([lerp2(base, tip, 0.15), lerp2(base, tip, 0.85), (lerp2(base, tip, 0.5)[0] - nx * w * 0.6, lerp2(base, tip, 0.5)[1] - ny * w * 0.6)]))]
        g = tuple(min(1.0, v * gk) for v in (0.10, 0.42, 0.48)) if gk > 0.05 else None
        cv.shape(cr_, mat, z=z + 0.3 + k * 0.01, sd=1.2, hi=0.0, details=det, glow=g, ol=0.85)
        # küçük yan kristal
        if k in (1, 2):
            b2 = lerp2(base, tip, 0.25)
            t2 = (b2[0] + math.sin(lean + 0.7 * (1 if k == 2 else -1)) * h * 0.45, b2[1] - math.cos(lean + 0.7) * h * 0.45)
            g2 = tuple(min(1.0, v * gk) for v in (0.08, 0.35, 0.4)) if gk > 0.05 else None
            cv.shape(cv.blob([(b2[0] - 1.0, b2[1] + 0.6), (t2[0], t2[1], 0.0), (b2[0] + 1.0, b2[1] + 0.6)]), mat, z=z + 0.28, sd=0.6,
                     glow=g2, ol=0.75)
        if p.get('glow', 0.0) > 0.05 and dim < 0.5:   # "!!" / kükreme: kristal halesi
            yk.glow_soft(cv, lerp2(base, tip, 0.55), 3.0 + 3.5 * p['glow'], CRYST_GLOW, z=z + 0.5, blur=0.7, alpha=0.55 * p['glow'])
    if rot:
        cv.pop()
        cv.pop()


def _leg(cv, base, foot, z, near, s=1.0, toe=0.0):
    """Kalın sütun bacak (fil gibi), ayak hedefli: kök -> ayak ik2 (diz önde). s: içeri çekilme ölçeği, toe: taban açısı
    (+ ön taraf kalkar). İri pul plakalar, geniş taban, üç kalın tırnak."""
    L = LEG * s
    k, f = yg.ik2(base, foot, L, L, -1)
    rr = max(0.5, s)
    ca, sa = math.cos(-toe), math.sin(-toe)

    def R(x, y, *r):
        dx, dy = (x - f[0]) * rr, (y - f[1]) * rr
        return (f[0] + dx * ca - dy * sa, f[1] + dx * sa + dy * ca) + r
    m = SKIN if near else SKIN_B
    leg = ik.union(cv.limb([base, k, f], [5.0 * rr, 4.4 * rr, 4.0 * rr]),
                   cv.blob([R(f[0] - 4.2, f[1] - 2.4), R(f[0] + 2.6, f[1] - 3.0), R(f[0] + 4.8, f[1] - 0.8), R(f[0] + 4.6, f[1] + 0.3, 0.0), R(f[0] - 4.0, f[1] + 0.3, 0.0)]))
    det = []
    if near and s > 0.6:   # ön yüzde iri pul plakalar (yarım daire mürekkep kenar + açık üst)
        for t, o in ((0.45, 1.6), (0.62, -1.0), (0.75, 1.8), (0.88, -0.2), (0.5, -2.6)):
            q = along(base, f, t, o)
            det.append(('hi', cv.ellipse((q[0] - 0.2, q[1] - 0.3), 1.2, 0.8)))
            det.append(('ink', [(q[0] - 1.4, q[1] + 0.1), (q[0], q[1] + 0.9), (q[0] + 1.4, q[1] + 0.1)], 0.85, (0.2, 0.2)))
        det += cv.fold([along(base, k, 0.9, -3.5), along(base, k, 1.0, -1.0), along(base, k, 1.1, 1.5)], 0.6, 1.0, 1)
    det.append(('ink', [R(f[0] - 3.4, f[1] - 1.8), R(f[0] + 0.6, f[1] - 2.2), R(f[0] + 3.4, f[1] - 1.2)], 0.9, (0.2, 0.4)))
    cv.shape(leg, m, z=z, sd=2.2, hi=0.3 if near else 0.0, details=det, bounce=0.25)
    for i in range(3):
        x, y = f[0] + 2.2 + i * 1.1, f[1] - 0.9 + i * 0.3
        cv.shape(cv.blob([R(x - 0.7, y - 0.7), R(x + 1.5, y + 0.9, 0.0), R(x - 0.6, y + 0.8)]), CLAW if near else CLAW.darker(0.7), z=z + 0.2, sd=0.4, ol=0.6)
    return f


def _eye(cv, c, p, z):
    """Göz: kaş altında kristal ışığı. eye: alevlenme (ısırık / "!!"), blink: kapak, dizzy: sersem sarmalı."""
    ex, ey = c
    cv.fill(cv.ellipse((ex - 0.3, ey + 0.1), 1.5, 1.1, -0.15), INK, z=z)
    if p['dizzy'] > 0.5:
        pts = [(ex + math.cos(a) * (0.15 + a * 0.12), ey + math.sin(a) * (0.1 + a * 0.09)) for a in [i * 0.55 for i in range(13)]]
        cv.stroke(pts, 0.9, z=z + 0.05, col=EYE, taper=(0.1, 0.1), glow=EYE_GLOW)
        return
    if p['blink'] > 0.5:
        cv.stroke([(ex - 1.4, ey - 0.1), (ex, ey + 0.35), (ex + 1.3, ey - 0.05)], 1.0, z=z + 0.05, col=SKIN.hi, taper=(0.2, 0.2))
        return
    fl = p['eye']
    if p['dim'] > 0.5:
        cv.fill(cv.ellipse((ex, ey), 0.6, 0.4), (0.35, 0.45, 0.45), z=z + 0.05)
        return
    cv.fill(cv.ellipse((ex, ey), 0.75 + 0.4 * fl, 0.55 + 0.3 * fl), EYE, z=z + 0.05, glow=EYE_GLOW)
    if fl > 0.05:
        cv.stroke([(ex - 0.1, ey), (ex - 2.3, ey - 0.7 - 0.4 * fl), (ex - 4.6 * fl - 0.5, ey - 1.1 - 0.6 * fl)], 1.4 + fl, z=z + 0.04, col=EYE,
                  taper=(0.1, 0.95), glow=EYE_GLOW)
        yk.glow_soft(cv, (ex, ey), 1.8 + 2.2 * fl, EYE_GLOW, z=z + 0.1, blur=0.6, alpha=0.45 * fl)


def _head(cv, c, p, z):
    """Boyun + kancalı gagalı baş (kabuk çerçevesinde). nk boyunu uzatır / çeker, hd başı öteler, hr başı boyun ucunda
    döndürür. Dönüş: ağız noktası (dünya)."""
    jaw = p['jaw']
    nk = p['nk']
    ext = 10.0 * nk if nk > 0 else 9.5 * nk
    hx = c[0] + 25.5 + ext + p['hd'][0]
    hy = c[1] + 2.0 + p['hd'][1]
    nb = (c[0] + 15.5 + min(0.0, nk) * 1.5, c[1] + 3)
    ne = (hx - 3, hy)
    # boyun: uzayınca hafif yay (ense yukarı), çekilince kısa ve kırışık
    mid = lerp2(nb, ne, 0.5)
    mid = (mid[0] - 1.0 * max(0.0, nk), mid[1] - 2.4 * max(0.0, nk) + 0.12 * max(0.0, p['hd'][1]))
    neck = cv.limb([nb, mid, ne], [5.8 + 0.6 * max(0.0, nk), 5.2 - 0.4 * max(0.0, nk), 4.6 - 0.4 * max(0.0, nk)])
    ndet = []
    for t, o0, o1 in ((0.25, 3.8, 1.2), (0.42, 4.0, 0.6), (0.6, 3.6, 1.4)):   # boğaz kırışıkları (alt yanda kısa)
        ndet.append(('ink', [along(nb, ne, t, o0), along(nb, ne, t + 0.06, o1)], 1.0, (0.1, 0.8)))
    for t, o in ((0.3, -2.4), (0.55, -1.6), (0.75, -2.8)):          # ense pulları
        q = along(nb, ne, t, o)
        ndet.append(('ink', [(q[0] - 1.0, q[1]), (q[0], q[1] + 0.6), (q[0] + 1.0, q[1])], 0.8, (0.2, 0.2)))
    if nk < -0.15:   # çekilmiş boyun: deri kabuk ağzında boğum boğum toplanır
        for t in (0.2, 0.45, 0.7):
            ndet.append(('ink', [along(nb, ne, t, -4.6), along(nb, ne, t - 0.08, 0.0), along(nb, ne, t, 4.4)], 0.9 + 0.5 * -nk, (0.3, 0.3)))
    if nk > 0.4:     # gerilmiş boyun: uzun tendon çizgisi
        ndet.append(('ink', [along(nb, ne, 0.15, -1.2), along(nb, ne, 0.5, -2.0), along(nb, ne, 0.9, -1.4)], 0.9, (0.3, 0.6)))
    ndet += cv.fold([along(nb, ne, 0.1, 3.6), along(nb, ne, 0.5, 3.0), along(nb, ne, 0.9, 3.4)], 0.7, 1.1, -1)
    cv.shape(neck, SKIN, z=z, sd=2.2, hi=0.3, details=ndet, bounce=0.3)
    # baş grubu: boyun ucunda döner
    yg.xf_push(cv, ne, p['hr'])
    jd = jaw * 3.0
    ja = jaw * 0.28
    # alt gaga (menteşe hx-1, hy+2 çevresinde açılır)
    hinge = (hx - 1.0, hy + 2.6)

    def J(x, y, *r):
        return yg.rot_about((x, y), hinge, ja) + r
    lower = cv.blob([J(hx - 1.5, hy + 2.0), J(hx + 6.5, hy + 2.6), J(hx + 9.0, hy + 2.0, 0.0), J(hx + 6.0, hy + 4.4), J(hx - 0.5, hy + 4.6)])
    if jaw > 0.15:
        mouth = cv.blob([(hx + 0.5, hy + 1.6), (hx + 9.2, hy + 1.2), J(hx + 8.6, hy + 2.4), J(hx + 0.8, hy + 3.4)])
        cv.fill(mouth, (0.30, 0.07, 0.09), z=z + 0.3)
        if jaw > 0.5:   # dil
            cv.fill(cv.blob([J(hx + 1.0, hy + 3.0), J(hx + 4.6, hy + 2.6), J(hx + 5.2, hy + 3.2), J(hx + 1.2, hy + 3.6)]), (0.62, 0.22, 0.24), z=z + 0.32)
    cv.shape(lower, BEAK, z=z + 0.4, sd=0.9, hi=0.25)
    head = cv.blob([(hx - 4.4, hy - 1.6), (hx - 2.6, hy - 4.8), (hx + 1.6, hy - 5.4), (hx + 5.0, hy - 4.0), (hx + 7.6, hy - 2.0),
                    (hx + 8.4, hy + 0.4), (hx + 6.0, hy + 2.2), (hx + 1.0, hy + 2.8), (hx - 3.6, hy + 3.0)])
    brow = 0.8 * p['eye']   # kaş çatılır
    hdet = [('ink', [(hx - 2.0, hy - 3.6 + brow * 0.2), (hx + 1.0, hy - 4.4 + brow), (hx + 4.4, hy - 3.4 + brow * 1.2)], 1.2 + brow * 0.4, (0.2, 0.4)),
            ('ink', [(hx - 3.0, hy + 0.0), (hx - 1.0, hy + 1.0)], 0.9, (0.3, 0.3)),
            ('ink', [(hx - 3.2, hy - 1.8), (hx - 1.2, hy - 0.8)], 0.9, (0.3, 0.3))]
    cv.shape(head, SKIN, z=z + 0.5, sd=2.0, hi=0.4, details=hdet, bounce=0.3, cast=0.6)
    # üst gaga: kanca
    upper = cv.blob([(hx + 2.4, hy - 3.0), (hx + 7.0, hy - 2.4), (hx + 9.8, hy - 0.6), (hx + 10.2, hy + 1.4), (hx + 9.2, hy + 3.4, 0.0),
                     (hx + 8.2, hy + 1.6), (hx + 2.6, hy + 1.8)])
    cv.shape(upper, BEAK, z=z + 0.6, sd=1.0, hi=0.4, details=[('ink', [(hx + 3.0, hy + 1.8), (hx + 8.4, hy + 1.6)], 1.0, (0.1, 0.3))])
    _eye(cv, (hx + 2.9, hy - 1.9), p, z + 0.7)
    mouth_pt = yg.world(cv, (hx + 9.6, hy + 1.8 + jd * 0.5))
    cv.pop()
    return mouth_pt


def _tail(cv, c, p):
    """Kısa dikenli kuyruk (kabuk çerçevesi); tw kökü çevresinde sallar (+ aşağı)."""
    root = (c[0] - 17.0, c[1] + 3.2)
    yg.xf_push(cv, root, p['tw'])
    cy = c[1]
    tl = cv.blob([(-17.0 + c[0], cy + 1.5), (-24.5 + c[0], cy + 5.5, 0.0), (-17.5 + c[0], cy + 5.0)])
    cv.shape(tl, SKIN_B, z=-4, sd=0.8, details=[('ink', [(-19.0 + c[0], cy + 3.2), (-22.0 + c[0], cy + 4.8)], 0.9)])
    for i in range(2):
        x = -19.0 - i * 2.4 + c[0]
        cv.shape(cv.blob([(x - 0.8, cy + 2.4 + i * 0.8), (x - 0.2, cy + 0.6 + i * 1.0, 0.0), (x + 0.6, cy + 2.6 + i * 0.8)]), STONE_D, z=-3.9, sd=0.4, ol=0.6)
    cv.pop()


def _draw_spin(cv, p):
    """Yuvarlanma: kabuk döner (ışık dünyada sabit: dönüş çizimden önce), kristal uçlarından ışık izi, hız yayları."""
    rot = p['spin']
    # dönen kabuğun yere değen alt ucu: yan yatınca uzun ekseni, ters dönünce kristalleri kabuğu yerden kaldırır
    lift = 4.0 * math.sin(rot) ** 2 + 9.0 * max(0.0, -math.cos(rot)) ** 4
    c = (0.0, CY_SPIN + p['y'] - lift)
    yg.xf_push(cv, (0.0, 0.0), 0.0, p['x'], 0.0)
    _shell(cv, c, p, 3, rot=rot)
    cr, sr = math.cos(rot), math.sin(rot)

    def RT(q):   # _shell'deki dönüşümün aynısı (büzülme + dönüş)
        x, y = (q[0] - c[0]) * 0.78, (q[1] - c[1]) * 1.04
        return (c[0] + x * cr - y * sr, c[1] + x * sr + y * cr)
    # kristal uçlarının ışık izi: dönüş yönünün tersine yay (uç, son 70 derecede geçtiği yol)
    for k in (0, 1, 2, 3):
        _b, tip, _h, _l = _crystal_tip(c, k, p)
        t = RT(tip)
        r = math.hypot(t[0] - c[0], t[1] - c[1])
        a0 = math.atan2(t[1] - c[1], t[0] - c[0])
        pts = [(c[0] + math.cos(a0 - j * 0.2) * r, c[1] + math.sin(a0 - j * 0.2) * r) for j in range(7)]
        pts = [q for q in pts if q[1] < 0.5]
        if len(pts) >= 2:
            cv.stroke(pts, 2.2 if k in (1, 2) else 1.5, z=2.6, col=CRYST.hi, taper=(0.1, 1.0), glow=CRYST_GLOW, alpha=0.85)
    # mürekkep hız yayları (kabuğun üst-arka yanında, dönüş yönünde incelir)
    for k, (rr, a, ln) in enumerate(((RX * 0.86 + 3.0, -1.75, 1.1), (RX * 0.86 + 5.5, -2.25, 0.8), (RX * 0.86 + 2.0, -2.9, 0.6))):
        pts = [(c[0] + math.cos(a - j * ln / 6) * rr, c[1] + math.sin(a - j * ln / 6) * rr * 0.95) for j in range(7)]
        cv.stroke(pts, 2.0 - k * 0.4, z=-5, col=INK, taper=(0.9, 0.1), alpha=0.75)
    # yerde toz / mürekkep çizgileri (arkada)
    for k in range(3):
        y = -1.2 - k * 2.2
        cv.stroke([(c[0] - 18 - k * 2, y), (c[0] - 27 - k * 4, y + 0.2)], 2.2 - k * 0.5, z=-5, col=INK, taper=(0.05, 0.9), alpha=0.7)
    # önde yer sürtünme kıvılcımı
    for k in range(3):
        a = -0.5 - k * 0.35
        q0 = (c[0] + 5.0 + k, -0.4)
        cv.stroke([q0, (q0[0] + math.cos(a) * (4 + k), q0[1] + math.sin(a) * (4 + k))], 1.1, z=6, col=(0.85, 1.0, 1.0),
                  taper=(0.1, 0.9), glow=CRYST_GLOW)
    cv.pop()
    return {'mouth': (c[0] + 30.0 + p['x'], c[1] + 4.5)}


def draw(cv, p):
    yg.bake_xf(cv)
    q = dict(REST)
    q.update(p)
    p = q
    if p['spin']:
        return _draw_spin(cv, p)
    hide = p['hide']
    C = C0
    pitch, sq = p['pitch'], p['sq']
    ssx, ssy = 1.0 + 0.07 * sq, 1.0 - 0.08 * sq
    sxf = 1.0 - 0.3 * p['yaw']
    # bütün figür: öteleme + devrilme + yanal daralma (gövde merkezinde)
    yg.xf_push(cv, C, p['roll'], p['x'], p['y'], sx=sxf)

    def B(pt):   # kabuk yereli (merkeze göre) -> figür çerçevesi (ezilme + pitch)
        return yg.rot_about((C[0] + pt[0] * ssx, C[1] + pt[1] * ssy), C, pitch)

    ca, sa = math.cos(-p['roll']), math.sin(-p['roll'])

    def F(t):    # dünya ayak hedefi -> figür çerçevesi (figür dönüşümünün tersi)
        w = (t[0] - p['x'] - C[0], -t[1] - p['y'] - C[1])
        w = (w[0] * ca - w[1] * sa, w[0] * sa + w[1] * ca)
        return (C[0] + w[0] / sxf, C[1] + w[1])

    s = 1.0 - 0.82 * hide

    def leg(key, z, near):
        t = p[key]
        bx, by = BASES[key]
        bx += yg.clamp(0.2 * (t[0] - FOOT0[key]), -2.2, 2.2)       # kuşak dönüşü
        base = B((bx * (1.0 - 0.25 * hide), by - 3.0 * hide))
        tgt = F(t)
        if hide > 0:
            tuck = (base[0] + 1.0, base[1] + 2 * LEG * s * 0.9)
            tgt = lerp2(tgt, tuck, min(1.0, hide * 1.2))
        if s > 0.28:
            _leg(cv, base, tgt, z, near, s, t[2])

    leg('hb', -6, False)
    leg('fb', -6, False)
    out = {}
    # ---- kabuk çerçevesi (ezilme + pitch)
    yg.xf_push(cv, C, pitch, sx=ssx, sy=ssy)
    if hide < 0.85:
        _tail(cv, C, p)
    if hide < 0.9:
        hz = 10 if (p['nk'] > -0.7 and hide < 0.4) else 1.0
        out['mouth'] = _head(cv, C, p, hz)
    _shell(cv, C, p, 3)
    if hide >= 0.9:
        # kabuk ağzından bakan göz
        cv.fill(cv.ellipse((C[0] + 18.0, C[1] + 2.4), 3.2, 2.2), INK, z=8)
        cv.fill(cv.ellipse((C[0] + 18.8, C[1] + 2.0), 0.9, 0.65), EYE, z=8.2, glow=EYE_GLOW)
        out['mouth'] = yg.world(cv, (C[0] + 30.0, C[1] + 4.5))
    cv.pop()
    leg('hf', 2.0, True)
    leg('ff', 2.2, True)
    cv.pop()
    return out


SHADE = dict(outer=0.5, rim=0.5, rim_col=(0.7, 0.9, 1.0), rim_dir=(0.55, -0.85), rim_w=1.4, form=(7.0, (0.74, 0.74, 0.86)))


# ====================================================================== anahtar pozlar (yaratik_govde.Seq)
def _foot_cycle(phi, home, S, duty, lift, toe_up=0.25, toe_push=0.25):
    """Döngüsel ayak yolu: basma (duty) boyunca +S/2 -> -S/2 (sabit hız, kayma yok), salınımda yayla öne."""
    phi %= 1.0
    if phi < duty:
        u = phi / duty
        x = home + S * (0.5 - u)
        toe = toe_push * max(0.0, (u - 0.8) / 0.2)            # itişte topuk kalkar (taban öne eğilir)
        return (x, 0.0, -toe)
    u = (phi - duty) / (1.0 - duty)
    e = u * u * (3 - 2 * u)
    x = home - S * 0.5 + S * e
    y = lift * math.sin(math.pi * u) ** 0.8
    return (x, y, toe_up * math.sin(math.pi * min(1.0, u * 1.2)))


WALK_S, WALK_DUTY = 14.0, 0.74


def _walk(t):
    """Yanal 4 vuruşlu yürüyüş (kaplumbağa): yakın arka -> yakın ön -> uzak arka -> uzak ön (%25 arayla), basma oranı
    0,74 (hep üç ayak yerde). Kabuk ön ayak iterken öne, arka iterken arkaya yalpalar; her basışta çöker (2 kez / döngü)."""
    p = {}
    for k, off in (('hf', 0.0), ('ff', 0.25), ('hb', 0.5), ('fb', 0.75)):
        p[k] = _foot_cycle(t - off, FOOT0[k] + 1.0, WALK_S, WALK_DUTY, 3.4 if k[0] == 'h' else 4.0)
    w = t * math.tau
    p.update(y=1.1 + 0.55 * math.cos(2 * w - 0.6), pitch=0.035 * math.sin(w + 0.9), x=0.5 * math.sin(w),
             nk=0.12 + 0.08 * math.sin(2 * w - 1.6), hd=(0.0, 0.5 + 0.6 * math.cos(2 * w - 1.2)), hr=0.04 * math.sin(2 * w - 2.0),
             tw=0.18 * math.sin(w - 1.4), jaw=0.06, glow=0.1 + 0.08 * math.sin(2 * w))
    return p


def _idle_proc(p, t):
    """Bekleme: ağır soluk (kabuk iner-kalkar, boyun soluğa göre uzar), kristal nabzı."""
    p = dict(p)
    w = t * math.tau
    p['y'] = p.get('y', 0.0) + 0.45 * math.sin(w)
    p['sq'] = p.get('sq', 0.0) + 0.06 * math.sin(w)
    p['nk'] = p.get('nk', 0.0) + 0.05 * math.sin(w + 0.8)
    p['glow'] = p.get('glow', 0.0) + 0.12 + 0.12 * math.sin(w - 0.5)
    return p


SEQS = {}

# ---- bekleme (8 kare): soluk, baş yavaşça sağa sola koklar, göz kırpma, kuyruk silkme
SEQS['idle'] = Seq([
    (0.0, dict(hd=(0.0, 0.0), hr=0.0, tw=0.0), 'io'),
    (0.25, dict(hd=(0.6, -0.5), hr=-0.07, tw=0.05, jaw=0.08), 'io'),
    (0.375, dict(hd=(0.6, -0.4), hr=-0.06, tw=0.4, jaw=0.2), 'o'),
    (0.5, dict(hd=(0.3, 0.2), hr=0.02, tw=-0.12, jaw=0.05), 'io'),
    (0.55, dict(hd=(0.2, 0.4), hr=0.05, blink=0.0), 'io'),
    (0.625, dict(hd=(0.1, 0.6), hr=0.08, blink=1.0), 'l'),
    (0.7, dict(hd=(0.0, 0.5), hr=0.06, blink=0.0), 'l'),
    (1.0, dict(hd=(0.0, 0.0), hr=0.0, tw=0.0), 'io'),
], n=8, fps=6, loop=True, proc=_idle_proc, rest=REST)

# ---- yürüyüş (8 kare, adım 14): vx 40 px/sn'de 1x (taş tosbağa hızı); fps = vx * n / adım
SEQS['walk'] = Seq([(i / 8, _walk(i / 8), 'l') for i in range(9)], n=8, fps=23, loop=True, rest=REST,
                   extra={'vx': 40.0})

# ---- dönüş (4 kare, ~0,2 sn): kabuk yanal daralır (döner), baş içeride, ayaklar yeni yöne basar, oturur
SEQS['turn'] = Seq([
    (0.0, dict(yaw=0.9, x=-1.0, y=1.2, nk=-0.45, hd=(0.0, 0.5), tw=0.4, pitch=0.03,
               **FT(hf=(4.0, 0.0), hb=(3.0, 2.5, 0.2), ff=(-4.0, 0.0), fb=(-3.0, 3.0, 0.2))), 'l'),
    (0.35, dict(yaw=0.45, x=-0.5, y=1.6, nk=-0.25, hd=(0.0, 0.6), tw=0.25,
                **FT(hf=(1.0, 2.5, 0.2), hb=(1.0, 0.0), ff=(-1.0, 3.0, 0.3), fb=(-1.0, 0.0))), 'o'),
    (0.7, dict(yaw=0.1, y=0.8, nk=0.05, hd=(0.4, 0.0), tw=-0.1), 'o'),
    (1.0, dict(), 'o'),
], frames=[0.0, 0.33, 0.66, 1.0], fps=16, rest=REST)

# ---- ısırık: hazırlık "!" (4) + vuruş (2) + toparlanma (3)
# hazırlık: baş kabuğa geri çekilir, gaga açılır, ön ayaklar öne kazık gibi dikilir (DERİN KURULMA uzun tutulur),
# son kare (0,05 sn) baş fırlamaya başlar; vuruş İLK karesi boyun sonuna dek uzamış, gaga kapanıyor (temas); toparlanma
# boynu geri sarar
BRACE = dict(y=2.2, x=-1.6, pitch=-0.06, nk=-0.6, hd=(0.0, -0.8), hr=-0.1, jaw=0.85, eye=0.55, tw=0.3, glow=0.25,
             **FT(ff=(5.0, 0.0, 0.0), fb=(4.5, 0.0, 0.0), hf=(-2.5, 0.0, -0.15), hb=(-2.0, 0.0, -0.15)))
SEQS['bite'] = Seq([
    (0.0, dict(y=0.8, x=-0.4, nk=-0.15, hd=(0.0, -0.3), jaw=0.3, eye=0.15, tw=0.1), 'o'),
    (0.14, dict(BRACE, y=1.5, nk=-0.45, jaw=0.6, eye=0.35), 'o'),
    (0.26, dict(BRACE), 'o'),
    (0.38, dict(BRACE, x=2.4, y=0.8, pitch=0.07, nk=0.4, hd=(0.0, 0.4), hr=0.05, jaw=1.05, eye=0.7, tw=-0.2,
                **FT(ff=(5.0, 0.0, 0.0), fb=(4.5, 0.0, 0.0), hf=(-3.5, 0.0, -0.3), hb=(-3.0, 0.0, -0.3))), 'i'),
    (0.5, dict(x=3.6, y=1.4, pitch=0.11, sq=-0.25, nk=1.0, hd=(0.0, 1.6), hr=0.16, jaw=0.5, eye=0.6, tw=-0.35, glow=0.25,
               **FT(ff=(6.5, 0.0, 0.0), fb=(5.5, 0.0, 0.0), hf=(-3.5, 0.0, -0.3), hb=(-3.0, 0.0, -0.3))), 'i'),
    (0.6, dict(x=3.8, y=1.8, pitch=0.1, sq=0.1, nk=0.95, hd=(0.0, 1.6), hr=0.14, jaw=0.0, eye=0.4, tw=-0.2,
               **FT(ff=(6.5, 0.0, 0.0), fb=(5.5, 0.0, 0.0), hf=(-2.0, 0.0), hb=(-2.0, 0.0))), 'o'),
    (0.74, dict(x=3.0, y=1.4, pitch=0.05, nk=0.45, hd=(0.0, 1.0), hr=0.08, jaw=0.15, eye=0.15, tw=0.0,
                **FT(ff=(5.0, 0.0), fb=(4.0, 2.0, 0.2), hf=(-1.0, 0.0), hb=(-1.0, 0.0))), 'io'),
    (0.87, dict(x=1.5, y=0.6, nk=-0.1, hd=(0.0, 0.3), jaw=0.1, tw=0.1, **FT(ff=(2.0, 0.0), fb=(1.5, 0.0), hf=(0.0, 0.0), hb=(1.0, 2.0, 0.2))), 'io'),
    (1.0, dict(x=0.0, y=0.0, nk=0.0, jaw=0.05), 'o'),
], frames=[(0.0, 0.0), (0.14, 0.18), (0.26, 0.42), (0.38, 0.0), (0.5, 0.0), (0.6, 0.45), (0.74, 0.0), (0.87, 0.35), (1.0, 0.72)],
    seg=[('windup', 4), ('strike', 2), ('recover', 3)], lead={'windup': 0.05}, rest=REST, fps=10)

# ---- zırhlı hazırlık "!!" (4): kabuk şahlanır (ön yükselir), kristaller dikleşip parlar, baş yukarıda geri çekik,
# gaga sonuna dek açık tıslar, gözler alev; bacaklar geniş basar
AA = dict(y=-0.2, x=-1.8, pitch=-0.14, sq=-0.2, nk=-0.35, hd=(-0.5, -3.6), hr=-0.32, jaw=1.15, eye=1.0, glow=1.0, cr=1.0, tw=0.5,
          **FT(ff=(6.5, 0.0, 0.0), fb=(5.0, 0.0, 0.0), hf=(-4.0, 0.0, -0.2), hb=(-3.5, 0.0, -0.2)))
SEQS['bite_aa'] = Seq([
    (0.0, dict(y=0.6, x=-0.8, pitch=-0.05, nk=-0.3, hd=(0.0, -1.2), hr=-0.1, jaw=0.5, eye=0.4, glow=0.5, cr=0.4, tw=0.2), 'o'),
    (0.3, dict(AA, y=0.2, jaw=1.0, glow=0.8, cr=0.85, eye=0.8), 'o'),
    (0.62, dict(AA), 'io'),
    (1.0, dict(AA, x=2.6, y=1.0, pitch=0.08, sq=0.0, nk=0.45, hd=(0.0, 0.2), hr=0.06, jaw=1.1, tw=-0.2,
               **FT(ff=(6.5, 0.0, 0.0), fb=(5.0, 0.0, 0.0), hf=(-4.5, 0.0, -0.35), hb=(-4.0, 0.0, -0.35))), 'i'),
], frames=[(0.0, 0.0), (0.3, 0.18), (0.62, 0.42), (1.0, 0.0)], seg=[('windup', 4)], lead={'windup': 0.05}, rest=REST, fps=10)

# ---- kabuğa çekilme (4): irkilme (baş içeri, dizler kırılır), kabuk yere iner, bacaklar kısalır, kapanır (tutulur)
HIDE_Y = CY_HIDE - CY0
SEQS['shell'] = Seq([
    (0.0, dict(y=2.6, nk=-0.8, hd=(0.0, 0.5), jaw=0.3, blink=1.0, tw=0.4, sq=0.2, **FT(ff=(1.5, 0.0), hf=(-1.0, 0.0))), 'o'),
    (0.33, dict(y=HIDE_Y * 0.7, nk=-1.0, hide=0.55, sq=0.3, tw=0.6), 'i2'),
    (0.66, dict(y=HIDE_Y + 0.6, hide=0.9, nk=-1.0, sq=0.35), 'i'),
    (1.0, dict(y=HIDE_Y, hide=1.0, nk=-1.0, sq=0.0), 'b'),
], frames=[(0.0, 0.0), (0.33, 0.08), (0.66, 0.16), (1.0, 0.25)], fps=10, rest=REST)

# ---- yuvarlanma (6 kare döngü; yapay zekâ anim.speed 2): kabuk döner, kristal izleri, hafif sekme
SEQS['spin'] = Seq([(i / 6, dict(hide=1.0, spin=0.3 + i / 6 * math.tau, y=-0.6 * abs(math.sin(i / 6 * math.tau * 2)), glow=0.6), 'l')
                    for i in range(7)], n=6, fps=10, loop=True, rest=REST)

# ---- yuvarlanma sonrası "başı döndü" (6 kare, st 1,0): kabuk açılır, baş sarkık çıkar, sallanır, gözler sarmal
DZ = dict(dizzy=1.0, jaw=0.45, y=2.4, nk=0.25, tw=-0.3, **FT(ff=(3.0, 0.0), fb=(4.0, 0.0), hf=(-3.0, 0.0), hb=(-3.5, 0.0)))
SEQS['dizzy'] = Seq([
    (0.0, dict(y=HIDE_Y, hide=1.0, nk=-1.0), 'l'),
    (0.18, dict(y=HIDE_Y * 0.45, hide=0.45, nk=-0.4, dizzy=1.0, sq=-0.2, roll=0.04,
                **FT(ff=(3.0, 0.0), fb=(4.0, 0.0), hf=(-3.0, 0.0), hb=(-3.5, 0.0))), 'o'),
    (0.36, dict(DZ, hd=(-1.0, 2.8), hr=0.34, pitch=0.06, roll=0.05, x=0.8), 'o'),
    (0.54, dict(DZ, hd=(1.0, 3.0), hr=0.15, pitch=-0.04, roll=-0.04, x=-0.8), 'io'),
    (0.72, dict(DZ, hd=(-0.6, 3.2), hr=0.38, pitch=0.05, roll=0.04, x=0.6), 'io'),
    (1.0, dict(DZ, y=1.2, nk=0.1, dizzy=0.0, blink=1.0, hd=(0.0, 1.0), hr=-0.15, jaw=0.2, pitch=0.0, roll=0.0, x=0.0), 'io'),
], n=6, fps=6, rest=REST)

# ---- hafif sarsılma (3 kare, 0,22 sn): kabuk geriye sarsılır, baş darbeden içeri kaçar, gözler kısılır
SEQS['hurt'] = Seq([
    (0.0, dict(x=-2.2, y=0.6, pitch=-0.09, nk=-0.55, hd=(0.0, -1.0), hr=-0.3, jaw=0.7, blink=1.0, tw=0.5, sq=0.2,
               **FT(ff=(0.0, 1.8, 0.3))), 'o'),
    (0.5, dict(x=-1.0, y=0.8, pitch=-0.03, nk=-0.3, hr=-0.1, jaw=0.4, blink=1.0, tw=0.3), 'o'),
    (1.0, dict(x=-0.3, nk=-0.05, jaw=0.15, tw=0.1), 'o'),
], frames=[(0.0, 0.0), (0.5, 0.35), (1.0, 0.7)], rest=REST, fps=12)

# ---- ağır sendeleme (4 kare, 0,45 sn): ön kalkar (ön ayaklar yerden kesilir), kabuk geriye yatar, baş savrulur,
# arkaya basıp düşer, kabuk yere vurup ezilir
SEQS['hurt_big'] = Seq([
    (0.0, dict(x=-3.2, y=-0.6, pitch=-0.24, nk=-0.2, hd=(-1.0, -2.5), hr=-0.55, jaw=1.0, blink=1.0, tw=0.7,
               **FT(ff=(-1.0, 5.5, 0.6), fb=(-1.0, 6.0, 0.6), hf=(-2.0, 0.0, 0.2), hb=(-1.5, 0.0, 0.2))), 'o'),
    (0.35, dict(x=-3.6, y=0.4, pitch=-0.12, nk=-0.3, hd=(0.0, -0.5), hr=-0.25, jaw=0.6, blink=1.0, tw=0.5,
                **FT(ff=(-1.5, 2.0, 0.3), fb=(-1.0, 2.5, 0.3), hf=(-2.5, 0.0), hb=(-2.0, 0.0))), 'io'),
    (0.65, dict(x=-3.0, y=2.4, pitch=0.06, sq=0.45, nk=-0.1, hd=(0.0, 1.5), hr=0.15, jaw=0.4, blink=0.0, tw=-0.2,
                **FT(ff=(-1.0, 0.0), fb=(-1.0, 0.0), hf=(-2.5, 0.0), hb=(-2.0, 0.0))), 'i'),
    (1.0, dict(x=-1.0, y=0.6, nk=0.0, jaw=0.2, tw=0.0, **FT(ff=(-0.5, 0.0), fb=(-0.5, 0.0), hf=(-1.0, 0.0), hb=(-1.0, 0.0))), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.22), (0.65, 0.5), (1.0, 0.78)], rest=REST, fps=10)


# ---- duruş kırık / sersem (6 kare döngü): bacaklar ayrık, kabuk yalpalar, baş yere sarkık sallanır, gözler sarmal
def _stun(t):
    s = math.sin(t * math.tau)
    c = math.cos(t * math.tau)
    return dict(x=1.0 * s, y=3.0 + 0.5 * c, pitch=0.05 * s, roll=0.03 * s, nk=0.3 + 0.08 * c, hd=(0.8 * s, 3.2 + 0.7 * c),
                hr=0.32 + 0.12 * s, jaw=0.5 + 0.1 * c, dizzy=1.0, tw=-0.35 + 0.1 * s, glow=0.0,
                **FT(ff=(4.0, 0.0), fb=(5.0 + 0.8 * s, 0.0), hf=(-3.5, 0.0), hb=(-4.0 + 0.8 * c, 0.0)))


SEQS['stun'] = Seq([(i / 12, _stun(i / 12), 'l') for i in range(13)], n=6, fps=6, loop=True, rest=REST)

# ---- havaya savrulma (dikey hız evresi; 4 kare): kabuk geriye devrilerek döner, bacaklar boşlukta çırpınır, baş içeri
SEQS['launch'] = Seq([
    (0.0, dict(y=-1.5, roll=-0.3, nk=-0.4, hd=(0.0, -1.0), hr=-0.4, jaw=0.9, blink=1.0, tw=0.7,
               **FT(ff=(-1.0, 4.0, 0.5), fb=(0.0, 5.0, 0.6), hf=(1.0, 3.5, 0.4), hb=(2.0, 4.5, 0.5))), 'o'),
    (0.4, dict(y=-2.5, roll=-0.6, nk=-0.6, hr=-0.2, jaw=0.7, blink=1.0, tw=0.9,
               **FT(ff=(2.0, 6.0, 0.7), fb=(-1.0, 4.5, 0.4), hf=(-2.0, 5.5, 0.6), hb=(2.5, 3.5, 0.3))), 'io'),
    (0.7, dict(y=-2.0, roll=-0.4, nk=-0.3, hr=0.0, jaw=0.8, blink=0.0, tw=0.5,
               **FT(ff=(-2.0, 4.0, 0.3), fb=(2.0, 6.0, 0.6), hf=(2.0, 3.0, 0.3), hb=(-1.5, 5.0, 0.5))), 'io'),
    (1.0, dict(y=-0.5, roll=-0.12, nk=0.0, hd=(0.0, 0.5), jaw=0.5, tw=0.3,
               **FT(ff=(1.0, 1.5, 0.1), fb=(1.5, 2.0, 0.1), hf=(-1.0, 1.5, 0.1), hb=(-0.5, 2.0, 0.1))), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.25), (0.65, 0.55), (1.0, 0.82)], seg=[('air', 4)], rest=REST, fps=10)

# ---- ölüm (8 kare, 0,9 sn): darbeyle ön kalkar, baş acıyla göğe, bacaklar çözülür (dizler yanlara kırılır), kabuk yere
# GÜM diye çarpar (ezilme, sekme), baş boynuyla yere uzanıp yığılır, kristaller söner
SEQS['death'] = Seq([
    (0.0, dict(x=-2.5, y=-0.5, pitch=-0.2, nk=0.3, hd=(-1.0, -4.0), hr=-0.7, jaw=1.15, eye=0.6, blink=0.0, tw=0.6, glow=0.6,
               **FT(ff=(-1.0, 4.5, 0.6), fb=(-1.0, 5.0, 0.6), hf=(-1.5, 0.0), hb=(-1.0, 0.0))), 'o'),
    (0.16, dict(x=-2.8, y=1.5, pitch=-0.1, nk=0.25, hd=(-0.5, -2.0), hr=-0.45, jaw=0.9, eye=0.0, blink=1.0, tw=0.4, glow=0.3,
                **FT(ff=(0.0, 2.0, 0.3), fb=(0.0, 2.5, 0.3), hf=(-3.0, 0.0, 0.3), hb=(-2.5, 0.0, 0.3))), 'io'),
    (0.32, dict(x=-2.5, y=5.0, pitch=0.05, nk=0.2, hd=(0.0, 1.0), hr=0.0, jaw=0.7, blink=1.0, tw=0.1, glow=0.15, dim=0.2,
                **FT(ff=(3.5, 0.0), fb=(4.5, 0.0), hf=(-5.0, 0.0), hb=(-4.5, 0.0))), 'i2'),
    (0.44, dict(x=-2.5, y=HIDE_Y + 0.4, pitch=0.06, sq=0.6, nk=0.25, hd=(0.5, 4.0), hr=0.3, jaw=0.8, blink=1.0, tw=-0.3, dim=0.4,
                **FT(ff=(6.0, 0.0), fb=(7.0, 0.0), hf=(-7.0, 0.0), hb=(-6.5, 0.0))), 'i'),
    (0.56, dict(x=-2.5, y=HIDE_Y - 0.8, pitch=0.03, sq=-0.15, nk=0.35, hd=(1.0, 4.5), hr=0.4, jaw=0.6, blink=1.0, tw=-0.4, dim=0.6,
                **FT(ff=(6.5, 0.0), fb=(7.5, 0.0), hf=(-7.5, 0.0), hb=(-7.0, 0.0))), 'o'),
    (0.7, dict(x=-2.5, y=HIDE_Y + 0.2, pitch=0.04, sq=0.2, nk=0.3, hd=(1.0, 7.0), hr=0.55, jaw=0.5, blink=1.0, tw=-0.5, dim=0.8,
               **FT(ff=(7.0, 0.0), fb=(8.0, 0.0), hf=(-8.0, 0.0), hb=(-7.5, 0.0))), 'i'),
    (0.84, dict(x=-2.5, y=HIDE_Y, pitch=0.03, sq=0.05, nk=0.32, hd=(1.0, 8.0), hr=0.5, jaw=0.35, blink=1.0, tw=-0.55, dim=1.0,
                **FT(ff=(7.0, 0.0), fb=(8.0, 0.0), hf=(-8.0, 0.0), hb=(-7.5, 0.0))), 'o'),
    (1.0, dict(x=-2.5, y=HIDE_Y, pitch=0.03, sq=0.0, nk=0.32, hd=(1.1, 8.2), hr=0.5, jaw=0.3, blink=1.0, tw=-0.55, dim=1.0,
               **FT(ff=(7.2, 0.0), fb=(8.2, 0.0), hf=(-8.2, 0.0), hb=(-7.7, 0.0))), 'o'),
], frames=[(0.0, 0.0), (0.16, 0.1), (0.32, 0.22), (0.44, 0.33), (0.56, 0.44), (0.7, 0.57), (0.84, 0.72), (1.0, 0.88)], rest=REST, fps=10)

# ---- kükreme / tıslama (seçkin; 6 kare, 0,8 sn): kabuk şahlanır, boyun göğe uzanır, kristaller parlar, uzun tıslama
SEQS['roar'] = Seq([
    (0.0, dict(), 'io'),
    (0.2, dict(x=-1.0, y=1.4, pitch=0.04, nk=-0.5, hd=(0.0, 0.5), jaw=0.3, eye=0.3, glow=0.3, tw=0.2), 'o'),
    (0.45, dict(x=-1.6, y=-0.2, pitch=-0.15, sq=-0.25, nk=0.55, hd=(-2.0, -5.0), hr=-0.6, jaw=1.2, eye=1.0, glow=1.0, cr=1.0, tw=0.6,
                **FT(ff=(4.0, 0.0), fb=(3.5, 0.0), hf=(-3.0, 0.0, -0.2), hb=(-2.5, 0.0, -0.2))), 'o'),
    (0.75, dict(x=-1.4, y=0.0, pitch=-0.13, sq=-0.2, nk=0.5, hd=(-1.8, -4.6), hr=-0.52, jaw=1.1, eye=0.9, glow=0.9, cr=0.9, tw=0.5,
                **FT(ff=(4.0, 0.0), fb=(3.5, 0.0), hf=(-3.0, 0.0, -0.2), hb=(-2.5, 0.0, -0.2))), 'io'),
    (1.0, dict(glow=0.2), 'o'),
], n=6, fps=8, rest=REST)

DURUM = {
    # ---- tepkiler (Enemy._anim_tick öncelikli anahtarları)
    '_hurt': {'a': 'hurt', 'u': 'up', 'd': 0.22},
    '_hurt_big': {'a': 'hurt_big', 'u': 'up', 'd': 0.45},
    '_break': {'a': 'stun', 'u': 'loop'},
    '_launch': {'a': 'launch', 'u': 'vy'},
    '_death': {'a': 'death', 'u': 'up', 'd': 0.9},
    '_turn': {'a': 'turn', 'u': 'up', 'd': 0.2},
    '_roar': {'a': 'roar', 'u': 'up', 'd': 0.8},
    # ---- turtle yapay zekâsı
    'windup': {'a': 'bite', 's': 'windup', 'u': 'st'},
    'windup!!': {'a': 'bite_aa', 's': 'windup', 'u': 'st'},
    'strike': {'a': 'bite', 's': 'strike', 'u': 'st'},
    'recover': {'a': 'bite', 's': 'recover', 'u': 'st'},
    'spin>recover': {'a': 'dizzy', 'u': 'st'},
    'shell': {'a': 'shell', 'u': 'st'},
    'spin': {'a': 'spin', 'u': 'loop'},
}


def render_frame(anim, i, ss=3):
    p = SEQS[anim].pose(i)
    cv = ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
