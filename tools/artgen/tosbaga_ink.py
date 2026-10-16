"""Taş Tosbağa (kimlik tosbaga; Taş Gulü ve Buz Tosbağası aynı çizimi tonla kullanır) — stil v2 "mürekkep-cel".
v1: creatures2.draw_tosbaga / TOSBAGA_ANIMS (aynı ad, kare sayısı, fps ve 'mouth' çapası).

Şahmeran mağarasının zırhlı bekçisi: yüksek kubbe kabuk yontulmuş taş plakalardan (sırt, yan ve kenar sıraları; her
plaka ayrı yüzey: ışık yanı açık, alt kenarı gölge, aralarında mürekkep oluk), plakalarda yosun ve çatlak, sırtta
mağara kristalleri (ışır). Kalın pullu fil bacakları ve kalın tırnaklar, kancalı gagalı iri baş (kaş çıkıntısı,
kristalden soluk göz), kısa dikenli kuyruk. Kabuğa çekilince yalnızca göz ağızdan bakar; 'spin'de kabuk yerde
yuvarlanır (ışık dünyada sabit: dönüş çizimden önce uygulanır). Isırık telegrafı: baş geriye çekilir, gaga açılır.
"""
import math

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_leg, lerp2
from bengu_ink import along
import creatures  # noqa: F401  (creatures2 döngüsel içe aktarımı: önce creatures yüklenmeli)
from creatures2 import TOSBAGA_ANIMS

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
CRYST_GLOW = (0.20, 0.85, 0.95)
EYE = (0.6, 1.0, 0.98)
EYE_GLOW = (0.2, 0.9, 1.0)

RX, RY = 20.5, 13.5
LEG = 7.8          # bacak parçası (v1: 6); kabuk kenarının altında bacaklar okunur


def ground(p):
    if p.get('spin', 0.0):
        return -15.2
    if p.get('hide', 0.0) >= 0.5:
        return -RY * 0.82 + p.get('bob', 0.0) * 0.3
    d = 0.0
    for k in ('hb', 'fb', 'hf', 'ff'):
        a = p.get(k, (0.2, 0.2))
        d = max(d, LEG * math.cos(a[0]) + LEG * math.cos(a[0] - a[1]))
    return -d - 4.0


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


def _shell(cv, c, p, z, rot=0.0):
    """Kabuk: alt plastron şeridi, gövde kubbesi, plakalar, kenar sırası, kristaller. rot: yuvarlanma açısı."""
    if rot:
        cr, sr = math.cos(rot), math.sin(rot)
        cv.push(lambda q, c=c: (c[0] + (q[0] - c[0]) * cr - (q[1] - c[1]) * sr, c[1] + (q[0] - c[0]) * sr + (q[1] - c[1]) * cr))
        # yuvarlanırken kabuk topa yakın (bacaklar/baş içeride): yerel x büzülür
        cv.push(lambda q, c=c: (c[0] + (q[0] - c[0]) * 0.78, c[1] + (q[1] - c[1]) * 1.04))
    hidden = p.get('hide', 0.0) >= 0.5
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
    # kristaller (sırtta, ışır)
    sp = p.get('spin', 0.0)
    for k, (u, h, lean) in enumerate(((-0.55, 6.0, -0.35), (-0.18, 9.5, -0.12), (0.2, 8.2, 0.1), (0.52, 5.4, 0.3))):
        base = _S((c[0], c[1] - 0.5), u, -0.9 + abs(u) * 0.35)
        h = h + (1.0 if hidden else 0.0)
        tip = (base[0] + math.sin(lean) * h, base[1] - math.cos(lean) * h)
        w = 2.2 + h * 0.08
        nx, ny = math.cos(lean), math.sin(lean)
        cr_ = cv.blob([(base[0] - nx * w, base[1] - ny * w + 0.8), (lerp2(base, tip, 0.6)[0] - nx * w * 0.8, lerp2(base, tip, 0.6)[1] - ny * w * 0.8),
                       (tip[0], tip[1], 0.0), (lerp2(base, tip, 0.5)[0] + nx * w * 0.9, lerp2(base, tip, 0.5)[1] + ny * w * 0.9),
                       (base[0] + nx * w, base[1] + ny * w + 0.8)])
        det = [('ink', [(base[0] + nx * 0.2, base[1] + 0.4), lerp2(base, tip, 0.8)], 0.9, (0.1, 0.7)),
               ('hi', cv.blob([lerp2(base, tip, 0.15), lerp2(base, tip, 0.85), (lerp2(base, tip, 0.5)[0] - nx * w * 0.6, lerp2(base, tip, 0.5)[1] - ny * w * 0.6)]))]
        cv.shape(cr_, CRYST, z=z + 0.3 + k * 0.01, sd=1.2, hi=0.0, details=det, glow=(0.10, 0.42, 0.48), ol=0.85)
        # küçük yan kristal
        if k in (1, 2):
            b2 = lerp2(base, tip, 0.25)
            t2 = (b2[0] + math.sin(lean + 0.7 * (1 if k == 2 else -1)) * h * 0.45, b2[1] - math.cos(lean + 0.7) * h * 0.45)
            cv.shape(cv.blob([(b2[0] - 1.0, b2[1] + 0.6), (t2[0], t2[1], 0.0), (b2[0] + 1.0, b2[1] + 0.6)]), CRYST, z=z + 0.28, sd=0.6,
                     glow=(0.08, 0.35, 0.4), ol=0.75)
    if rot:
        cv.pop()
        cv.pop()


def _leg(cv, base, a, z, near, front):
    """Kalın sütun bacak (fil gibi): kabuk kenarının altından çıkar; iri pul plakalar, geniş taban, üç kalın tırnak."""
    k, f = fk_leg(base, a[0], a[1], LEG, LEG)
    m = SKIN if near else SKIN_B
    leg = ik.union(cv.limb([base, k, f], [5.0, 4.4, 4.0]),
                   cv.blob([(f[0] - 4.2, f[1] - 2.4), (f[0] + 2.6, f[1] - 3.0), (f[0] + 4.8, f[1] - 0.8), (f[0] + 4.6, f[1] + 0.3, 0.0), (f[0] - 4.0, f[1] + 0.3, 0.0)]))
    det = []
    if near:   # ön yüzde iri pul plakalar (yarım daire mürekkep kenar + açık üst)
        for t, o in ((0.45, 1.6), (0.62, -1.0), (0.75, 1.8), (0.88, -0.2), (0.5, -2.6)):
            q = along(base, f, t, o)
            det.append(('hi', cv.ellipse((q[0] - 0.2, q[1] - 0.3), 1.2, 0.8)))
            det.append(('ink', [(q[0] - 1.4, q[1] + 0.1), (q[0], q[1] + 0.9), (q[0] + 1.4, q[1] + 0.1)], 0.85, (0.2, 0.2)))
        det += cv.fold([along(base, k, 0.9, -3.5), along(base, k, 1.0, -1.0), along(base, k, 1.1, 1.5)], 0.6, 1.0, 1)
    det.append(('ink', [(f[0] - 3.4, f[1] - 1.8), (f[0] + 0.6, f[1] - 2.2), (f[0] + 3.4, f[1] - 1.2)], 0.9, (0.2, 0.4)))
    cv.shape(leg, m, z=z, sd=2.2, hi=0.3 if near else 0.0, details=det, bounce=0.25)
    for i in range(3):
        x, y = f[0] + 2.2 + i * 1.1, f[1] - 0.9 + i * 0.3
        cv.shape(cv.blob([(x - 0.7, y - 0.7), (x + 1.5, y + 0.9, 0.0), (x - 0.6, y + 0.8)]), CLAW if near else CLAW.darker(0.7), z=z + 0.2, sd=0.4, ol=0.6)
    return f


def _head(cv, c, p, z):
    """Boyun + kancalı gagalı baş. Dönüş: ağız noktası."""
    jaw = p.get('jaw', 0.0)
    hx, hy = c[0] + 25.5, c[1] + 2 + p.get('hy', 0.0)
    nb = (c[0] + 15.5, c[1] + 3)
    neck = cv.limb([nb, lerp2(nb, (hx - 3, hy), 0.5), (hx - 3, hy)], [5.8, 5.0, 4.6])
    ndet = []
    for t, o0, o1 in ((0.25, 3.8, 1.2), (0.42, 4.0, 0.6), (0.6, 3.6, 1.4)):   # boğaz kırışıkları (alt yanda kısa)
        ndet.append(('ink', [along(nb, (hx - 3, hy), t, o0), along(nb, (hx - 3, hy), t + 0.06, o1)], 1.0, (0.1, 0.8)))
    for t, o in ((0.3, -2.4), (0.55, -1.6), (0.75, -2.8)):          # ense pulları
        q = along(nb, (hx - 3, hy), t, o)
        ndet.append(('ink', [(q[0] - 1.0, q[1]), (q[0], q[1] + 0.6), (q[0] + 1.0, q[1])], 0.8, (0.2, 0.2)))
    ndet += cv.fold([along(nb, (hx - 3, hy), 0.1, 3.6), along(nb, (hx - 3, hy), 0.5, 3.0), along(nb, (hx - 3, hy), 0.9, 3.4)], 0.7, 1.1, -1)
    cv.shape(neck, SKIN, z=z, sd=2.2, hi=0.3, details=ndet, bounce=0.3)
    jd = jaw * 3.0
    # alt gaga (açılır)
    lower = cv.blob([(hx - 1.5, hy + 2.0), (hx + 6.5, hy + 2.6 + jd * 0.7), (hx + 9.0, hy + 2.0 + jd, 0.0), (hx + 6.0, hy + 4.4 + jd), (hx - 0.5, hy + 4.6)])
    if jaw > 0.15:
        cv.fill(cv.blob([(hx + 0.5, hy + 1.6), (hx + 9.2, hy + 1.2), (hx + 8.6, hy + 2.4 + jd), (hx + 0.8, hy + 3.4)]), (0.22, 0.06, 0.08), z=z + 0.3)
    cv.shape(lower, BEAK, z=z + 0.4, sd=0.9, hi=0.25)
    head = cv.blob([(hx - 4.4, hy - 1.6), (hx - 2.6, hy - 4.8), (hx + 1.6, hy - 5.4), (hx + 5.0, hy - 4.0), (hx + 7.6, hy - 2.0),
                    (hx + 8.4, hy + 0.4), (hx + 6.0, hy + 2.2), (hx + 1.0, hy + 2.8), (hx - 3.6, hy + 3.0)])
    hdet = [('ink', [(hx - 2.0, hy - 3.6), (hx + 1.0, hy - 4.4), (hx + 4.4, hy - 3.4)], 1.2, (0.2, 0.4)),     # kaş sırtı
            ('ink', [(hx - 3.0, hy + 0.0), (hx - 1.0, hy + 1.0)], 0.9, (0.3, 0.3)),
            ('ink', [(hx - 3.2, hy - 1.8), (hx - 1.2, hy - 0.8)], 0.9, (0.3, 0.3))]
    cv.shape(head, SKIN, z=z + 0.5, sd=2.0, hi=0.4, details=hdet, bounce=0.3, cast=0.6)
    # üst gaga: kanca
    upper = cv.blob([(hx + 2.4, hy - 3.0), (hx + 7.0, hy - 2.4), (hx + 9.8, hy - 0.6), (hx + 10.2, hy + 1.4), (hx + 9.2, hy + 3.4, 0.0),
                     (hx + 8.2, hy + 1.6), (hx + 2.6, hy + 1.8)])
    cv.shape(upper, BEAK, z=z + 0.6, sd=1.0, hi=0.4, details=[('ink', [(hx + 3.0, hy + 1.8), (hx + 8.4, hy + 1.6)], 1.0, (0.1, 0.3))])
    # göz: kaş çıkıntısı altında kristal ışığı
    cv.fill(cv.ellipse((hx + 2.6, hy - 1.8), 1.5, 1.1, -0.15), INK, z=z + 0.7)
    fl = max(0.0, jaw - 0.45) * 1.6        # ısırık telegrafı: göz alevlenir
    cv.fill(cv.ellipse((hx + 2.9, hy - 1.9), 0.75 + 0.4 * fl, 0.55 + 0.3 * fl), EYE, z=z + 0.75, glow=EYE_GLOW)
    if fl > 0:
        cv.stroke([(hx + 2.8, hy - 1.9), (hx + 0.6, hy - 2.6), (hx - 2.0, hy - 3.0)], 1.4 + fl, z=z + 0.74, col=EYE, taper=(0.1, 0.95), glow=EYE_GLOW)
    return (hx + 9.6, hy + 1.8 + jd * 0.5)


def draw(cv, p):
    bob = p.get('bob', 0.0)
    hide = p.get('hide', 0.0)
    spin = p.get('spin', 0.0)
    cy = ground(p) + (bob * 0.4 if hide < 0.5 else 0.0)
    c = (0.0, cy)
    out = {}
    if hide < 0.5:
        legs = (('hb', -11, -6, False, False), ('fb', 10, -6, False, True), ('hf', -9, 2.0, True, False), ('ff', 12, 2.2, True, True))
        for key, dx, zz, near, front in legs[:2]:
            _leg(cv, (dx, cy + 4), p.get(key, (0.2, 0.2)), zz, near, front)
        # kuyruk: kısa, dikenli
        tl = cv.blob([(-17.0, cy + 1.5), (-24.5, cy + 5.5, 0.0), (-17.5, cy + 5.0)])
        cv.shape(tl, SKIN_B, z=-4, sd=0.8, details=[('ink', [(-19.0, cy + 3.2), (-22.0, cy + 4.8)], 0.9)])
        for i in range(2):
            x = -19.0 - i * 2.4
            cv.shape(cv.blob([(x - 0.8, cy + 2.4 + i * 0.8), (x - 0.2, cy + 0.6 + i * 1.0, 0.0), (x + 0.6, cy + 2.6 + i * 0.8)]), STONE_D, z=-3.9, sd=0.4, ol=0.6)
        out['mouth'] = _head(cv, c, p, 10)
        _shell(cv, c, p, 3)
        for key, dx, zz, near, front in legs[2:]:
            _leg(cv, (dx, cy + 4), p.get(key, (0.2, 0.2)), zz, near, front)
    else:
        _shell(cv, c, p, 3, rot=spin)
        if not spin:
            # kabuk ağzından bakan göz
            cv.fill(cv.ellipse((c[0] + 18.0, c[1] + 2.4), 3.2, 2.2), INK, z=8)
            cv.fill(cv.ellipse((c[0] + 18.8, c[1] + 2.0), 0.9, 0.65), EYE, z=8.2, glow=EYE_GLOW)
        else:
            # yuvarlanma: yerde toz/mürekkep hız çizgileri (arkada)
            for k in range(3):
                y = 0.0 - 1.2 - k * 2.2
                cv.stroke([(c[0] - 18 - k * 2, y), (c[0] - 26 - k * 4, y + 0.2)], 2.2 - k * 0.5, z=-5, col=INK, taper=(0.05, 0.9), alpha=0.7)
        out['mouth'] = (c[0] + 30.0, c[1] + 4.5)
    return out


ANIMS = {k: (v[0], v[1], k in ('idle', 'walk'), True) for k, v in TOSBAGA_ANIMS.items()}
SHADE = dict(outer=0.5, rim=0.5, rim_col=(0.7, 0.9, 1.0), rim_dir=(0.55, -0.85), rim_w=1.4, form=(7.0, (0.74, 0.74, 0.86)))


def render_frame(anim, i, ss=3):
    n, fn, loop, arm = ANIMS[anim]
    p = dict(fn(i / n))
    if anim == 'spin':
        p['spin'] = i / n * math.tau + 0.3   # 4 karede tam tur (çeyrek adımlar: kristaller öne yuvarlanır)
    cv = ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss)
    info = draw(cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
