"""Çor Ruhu (kimlik cor) ve biyom çeşitlemeleri — stil v2 "mürekkep-cel". v1: creatures.draw_cor.

Aynı iskelet ve pozlar (creatures.COR_ANIMS: idle 6, attack 3, hurt 1); 'mouth' çapası = buhurdan/fenerin merkezi
(mermi oradan çıkar). Doku 4 piksel / dünya birimi; hücre dünya 80x76 (v1 64x76'dan geniş: mürekkep konturu ve
savrulan fener sığsın), ayak (34, 70).

Tasarım: Türk halk inancında "çor" hastalık getiren kötü ruhtur. Kirli, küllü bir kefene sarınmış, ayaksız süzülen
uzun bir gölge: sivri ucu geriye sarkan başlık, içinde zifiri karanlık ve iki solgun ışık; yırtık kefen kuyrukları,
kemik eller, bileğe bağlanmış çalınmış dilek çaputları (hastalar için ağaca bağlanan bez parçaları). Zincirdeki tunç
buhurdanın kafes pencerelerinden salgın ateşi yanar, sporlu duman tüter. Saldırı uyarısı: buhurdanı arkaya çeker,
ateş parlar, gözler büyür; savuruşta spor bulutu patlar.

Çeşitlemeler (VARIANTS; oyunda `<kimlik>_v2` sprite'ı, biyom tonu uygulanmaz):
  cor               Çor Ruhu       (Ötüken)  küllü kefen, salgın yeşili
  kara_kus_yavrusu  Kurgan Ruhu    (Bozkır)  aşı boyalı keçe, sivri Saka börkü, altın ölü maskesi, kehribar ateş
  kan_yarasasi      Kan Çoru       (Şahmeran) kan kızılı yarasa kanatlı kefen, kulaklı başlık, kızıl ışık
  kaf_kartali       Ayaz Çoru      (Kaf)     buz mavisi donmuş kefen, kartal tüyü yaka, buz sarkıtları, ayaz ışığı
  kayip_ruh         Kayıp Ruh      (Tamu)    soluk mor, saydamlaşan kuyruk, kırık pranga zinciri, ruh feneri
  demir_gaga        Demir Gaga     (Tamu)    pas-kara kefen, demir kuş gagası maske, kor dolu demir buhurdan
"""
import math

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_arm, lerp2, chain
from creatures import COR_ANIMS
import yaratik_ink_kit as yk

TEX = 4.0
CELL = (320, 304)       # dünya 80 x 76
FEET = (136, 280)       # dünya (34, 70)
ANIMS = {k: (v[0], v[1], k == 'idle', True) for k, v in COR_ANIMS.items()}

BONE = Ink('#e4dcc4', '#8a7f72', '#fffbec', '#544a48', name='kemik')
BRONZE = Ink('#b98a3e', '#5e3a1c', '#f4d88a', '#33200f', kind='metal', name='tunç')
IRON = Ink('#5e6070', '#2a2a36', '#a0a4b8', '#17171f', kind='metal', name='demir')
GOLD = Ink('#e8b84a', '#8e541c', '#fff2b8', '#4a2a0c', kind='metal', name='altın')


def _v(**kw):
    base = dict(
        robe=Ink('#c3bcae', '#6a6280', '#ece6d6', '#3c3654', name='küllü kefen'),
        robe_b=Ink('#a39cab', '#575170', '#c8c2cc', '#322d48', name='kefen arkası'),
        mantle=Ink('#a59d9a', '#57506c', '#cfc8c0', '#332e48', name='omuz örtüsü'),
        stain=(0.42, 0.52, 0.28), stain_a=0.5,
        fire=(0.74, 1.0, 0.36), fire_hot=(0.93, 1.0, 0.7), glow=(0.45, 0.95, 0.12),
        eye=(0.85, 1.0, 0.55), eye_glow=(0.5, 1.0, 0.2),
        smoke=Ink('#8fa070', '#4e5c40', '#c4d49a', name='salgın dumanı'), smoke_glow=(0.18, 0.4, 0.04),
        metal=BRONZE, bone=BONE, caput=((0.78, 0.22, 0.2), (0.9, 0.86, 0.74), (0.3, 0.42, 0.62)),
        face='void', hood='tip', extra=(), lantern='censer', tail_fade=0.0,
    )
    base.update(kw)
    return base


VARIANTS = {
    'cor': _v(),
    'kara_kus_yavrusu': _v(
        robe=Ink('#c48a4c', '#6c3a2c', '#ecc07a', '#3a1c1a', name='aşı keçe'),
        robe_b=Ink('#8e5a36', '#4a2420', '#b07a4c', '#2a1214', name='keçe arkası'),
        mantle=Ink('#a4342c', '#541a24', '#d4604a', '#2e0c16', name='kızıl keçe'),
        stain=(0.35, 0.22, 0.12), stain_a=0.35,
        fire=(1.0, 0.72, 0.25), fire_hot=(1.0, 0.92, 0.6), glow=(1.0, 0.55, 0.08),
        eye=(1.0, 0.85, 0.4), eye_glow=(1.0, 0.6, 0.1),
        smoke=Ink('#b89a72', '#6a5040', '#e2caa0', name='kurgan tozu'), smoke_glow=(0.4, 0.22, 0.02),
        metal=GOLD, face='gold', hood='cap'),
    'kan_yarasasi': _v(
        robe=Ink('#8e2232', '#3e0c24', '#c8424a', '#22061a', name='kan kefen'),
        robe_b=Ink('#5e1426', '#2c0818', '#7e2232', '#16040e', name='kanat zarı'),
        mantle=Ink('#3a2030', '#1c0e1c', '#5e3a4a', '#0e060e', name='kara örtü'),
        stain=(0.2, 0.02, 0.06), stain_a=0.45,
        fire=(1.0, 0.3, 0.3), fire_hot=(1.0, 0.75, 0.7), glow=(1.0, 0.1, 0.12),
        eye=(1.0, 0.55, 0.5), eye_glow=(1.0, 0.12, 0.1),
        smoke=Ink('#a04656', '#521c30', '#d47a84', name='kan buğusu'), smoke_glow=(0.45, 0.02, 0.05),
        metal=IRON, face='void', hood='ears', extra=('wings',),
        caput=((0.18, 0.1, 0.14), (0.62, 0.12, 0.16), (0.18, 0.1, 0.14))),
    'kaf_kartali': _v(
        robe=Ink('#bcd0e4', '#58689a', '#f2f8ff', '#323c6a', name='donmuş kefen'),
        robe_b=Ink('#7e92b4', '#3c4874', '#a8bcd8', '#222a4e', name='buz arkası'),
        mantle=Ink('#e8e2d4', '#7c7a96', '#ffffff', '#4a4864', name='kartal tüyü'),
        stain=(0.6, 0.85, 1.0), stain_a=0.3,
        fire=(0.62, 0.92, 1.0), fire_hot=(0.92, 1.0, 1.0), glow=(0.3, 0.75, 1.0),
        eye=(0.85, 0.98, 1.0), eye_glow=(0.35, 0.8, 1.0),
        smoke=Ink('#cfe4f4', '#6a84b0', '#ffffff', name='ayaz buğusu'), smoke_glow=(0.08, 0.22, 0.42),
        metal=IRON, face='void', hood='tip', extra=('icicles', 'feathers'),
        caput=((0.36, 0.52, 0.8), (0.92, 0.94, 1.0), (0.36, 0.52, 0.8))),
    'kayip_ruh': _v(
        robe=Ink('#9a8cc8', '#4a3c84', '#cec4f0', '#281e52', name='ruh örtüsü'),
        robe_b=Ink('#6a5ca0', '#342a68', '#8e82c0', '#1c1440', name='ruh arkası'),
        mantle=Ink('#7c6eb0', '#3c3072', '#a69ad8', '#20184a', name='ruh örtüsü 2'),
        stain=(0.6, 0.9, 1.0), stain_a=0.25,
        fire=(0.6, 0.95, 1.0), fire_hot=(0.92, 1.0, 1.0), glow=(0.35, 0.8, 1.0),
        eye=(0.85, 1.0, 1.0), eye_glow=(0.3, 0.85, 1.0),
        smoke=Ink('#a8c8f0', '#5466a8', '#e4f0ff', name='ruh buğusu'), smoke_glow=(0.08, 0.3, 0.5),
        metal=IRON, face='mask', extra=('shackle',), lantern='cage', tail_fade=0.7,
        caput=((0.5, 0.45, 0.7), (0.8, 0.8, 0.9), (0.5, 0.45, 0.7))),
    'demir_gaga': _v(
        robe=Ink('#7a6c6a', '#3a2c34', '#a69690', '#1c1218', name='kurum kefen'),
        robe_b=Ink('#564a4c', '#2a1e24', '#76686a', '#140c10', name='kefen arkası'),
        mantle=Ink('#8a4426', '#3a1614', '#a85a34', '#1e0a0a', name='pas'),
        stain=(1.0, 0.45, 0.1), stain_a=0.0,
        fire=(1.0, 0.55, 0.15), fire_hot=(1.0, 0.88, 0.5), glow=(1.0, 0.4, 0.04),
        eye=(1.0, 0.82, 0.4), eye_glow=(1.0, 0.45, 0.05),
        smoke=Ink('#6a5a5a', '#2e2428', '#9a8484', name='kurum'), smoke_glow=(0.5, 0.15, 0.0),
        metal=IRON, face='beak', extra=('embers',),
        caput=((0.5, 0.2, 0.12), (0.3, 0.26, 0.26), (0.5, 0.2, 0.12))),
}


def _tail(cv, start, n, seg, ang, ph, mat, z, w0, seed, fade=0.0, glow=None):
    pts = chain(start, n, seg, ang, 0.1, ph, 0.5)
    W = [cv.W(q) for q in pts]
    path = ik.taper_path(W, cv.u(w0), prof=lambda u: max(0.08, (1.0 - min(1.0, u)) ** 0.8 * (0.9 + 0.25 * math.sin(u * 9 + seed))))
    # yırtık uç: iki diş
    e, e1 = pts[-1], pts[-2]
    dx, dy = e[0] - e1[0], e[1] - e1[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    fork = cv.blob([(e1[0] + nx * 1.2, e1[1] + ny * 1.2), (e[0] + nx * 1.6 + dx * 0.3, e[1] + ny * 1.6 + dy * 0.3, 0.0),
                    (e1[0] + dx * 0.4, e1[1] + dy * 0.4)])
    path = ik.union(path, fork)
    mid = pts[len(pts) // 2]
    det = [('ink', [pts[1], lerp2(pts[1], pts[3], 0.5), pts[3]], 1.1, (0.3, 0.6))]
    if fade > 0:   # kuyruk ucu saydamlaşır (kayıp ruh): önce çiz, sonra silgi
        cv.shape(path, mat, z=z, sd=1.6, hi=0.25, details=det, ol=0.8, glow=glow)
        er = ik.taper_path(W[len(W) // 2:], cv.u(w0 * 2.2), (0.6, 0.0))

        def fn(c, er=er):
            import skia
            p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, fade))
            p.setBlendMode(skia.BlendMode.kDstOut)
            p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.BlurStyle.kNormal_BlurStyle, cv.u(2.0)))
            c.drawPath(er, p)
        cv._q(z + 0.05, fn)
    else:
        cv.shape(path, mat, z=z, sd=1.6, hi=0.25, details=det, ol=0.9)
    return pts


def _sleeve(cv, sh, e, h, mat, z, r0, r1, seed, near):
    """Bol yen: omuzdan dirseğe genişler, bileğin üstünde yırtık ağızla biter."""
    mouth_c = lerp2(e, h, 0.25)
    dx, dy = mouth_c[0] - sh[0], mouth_c[1] - sh[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    a = (mouth_c[0] + nx * r1, mouth_c[1] + ny * r1)
    b = (mouth_c[0] - nx * r1 * 1.15, mouth_c[1] - ny * r1 * 1.15 + 1.5)
    edge = yk.ragged(a, b, 3, 1.6, seed=seed, side=-1.0)
    pts = [(sh[0] + nx * r0, sh[1] + ny * r0), lerp2((sh[0] + nx * r0, sh[1] + ny * r0), a, 0.5), a] + edge + [b,
           lerp2((sh[0] - nx * r0, sh[1] - ny * r0), b, 0.5), (sh[0] - nx * r0, sh[1] - ny * r0), (sh[0] - dx / L * r0, sh[1] - dy / L * r0)]
    path = cv.blob(pts)
    det = cv.fold([lerp2(sh, mouth_c, 0.25), lerp2(sh, mouth_c, 0.6), (mouth_c[0] - nx * 0.6, mouth_c[1] - ny * 0.6)], 0.7, 1.2, 1)
    det += [('deep', cv.ellipse(lerp2(a, b, 0.5), 1.4, r1 * 0.9, math.atan2(dy, dx)))]
    cv.shape(path, mat, z=z, sd=1.8, hi=0.3 if near else 0.0, details=det, hatch=0.4 if near else 0.0)
    return mouth_c


def _caput(cv, at, V, z, ph, k0=0):
    """Bileğe bağlı dilek çaputları: kısa incelen bez şeritler."""
    for k in range(3):
        col = V['caput'][(k + k0) % len(V['caput'])]
        a = math.pi * 0.5 + (k - 1) * 0.35 + math.sin(ph + k * 1.7) * 0.15
        L = 3.2 + (k % 2) * 1.4
        e = (at[0] + math.cos(a) * L - 0.6, at[1] + math.sin(a) * L)
        m = lerp2(at, e, 0.5)
        pts = [at, (m[0] + math.sin(ph + k) * 0.5, m[1]), e]
        cv.shape(ik.taper_path([cv.W(q) for q in pts], cv.u(1.0), (0.05, 0.4)), Ink(col), z=z + k * 0.01, sd=0.35, ol=0.65)


def _lantern(cv, cen, V, z, flare, t):
    """Buhurdan (tunç/demir kafes, pencerelerinden ateş) ya da ruh kafesi."""
    M = V['metal']
    cx, cy = cen
    gl, hot, fire = V['glow'], V['fire_hot'], V['fire']
    if V['lantern'] == 'cage':
        # ruh kafesi: demir çubuklar, içinde süzülen ruh alevi
        yk.glow_soft(cv, (cx, cy + 0.3), 7.0 + flare * 3.0, gl, z=z, blur=0.55, alpha=0.5 + 0.3 * flare)
        body = cv.ellipse((cx, cy + 0.4), 3.3, 4.0)
        cv.shape(body, Ink(fire), z=z, flat=True, ol=0.0, glow=gl)
        fl = cv.blob([(cx - 1.8, cy + 2.4), (cx - 0.6, cy - 1.0), (cx - 0.2, cy - 3.6 - flare, 0.0), (cx + 1.2, cy - 0.4), (cx + 1.8, cy + 2.4)])
        cv.fill(fl, hot, z=z + 0.2, glow=hot)
        for k in range(5):
            x = cx - 3.0 + k * 1.5
            bow = 1.0 - ((k - 2) / 2.4) ** 2
            cv.shape(ik.taper_path([cv.W((x * 0.9 + cx * 0.1, cy - 3.4)), cv.W((cx + (x - cx) * (1.0 + 0.25 * bow), cy + 0.4)), cv.W((x * 0.9 + cx * 0.1, cy + 4.2))],
                                   cv.u(0.6), (0.0, 0.0)), M, z=z + 0.5, sd=0.3, hi=0.15, ol=0.6)
        cv.shape(cv.ellipse((cx, cy - 3.6), 2.6, 0.9), M, z=z + 0.6, sd=0.5, hi=0.3)
        cv.shape(cv.ellipse((cx, cy + 4.3), 2.4, 0.8), M, z=z + 0.6, sd=0.5, hi=0.3)
        cv.shape(cv.ellipse((cx, cy - 4.8), 0.8, 0.8), M, z=z + 0.7, sd=0.3)
        return
    yk.glow_soft(cv, (cx, cy + 0.6), 6.5 + flare * 3.5, gl, z=z, blur=0.55, alpha=0.45 + 0.35 * flare)
    # gövde: çömlek biçimi, alt sivri uç, kulplar
    pot = cv.blob([(cx - 3.6, cy - 1.4), (cx - 3.9, cy + 1.2), (cx - 2.6, cy + 3.6), (cx - 0.8, cy + 4.6), (cx, cy + 6.4, 0.0),
                   (cx + 0.8, cy + 4.6), (cx + 2.6, cy + 3.6), (cx + 3.9, cy + 1.2), (cx + 3.6, cy - 1.4)])
    wins = []
    for k in range(3):
        x = cx - 2.1 + k * 2.1
        wins.append(cv.blob([(x - 0.55, cy - 0.8), (x + 0.55, cy - 0.8), (x + 0.6, cy + 1.6), (x, cy + 2.6 - abs(k - 1) * 0.5, 0.0), (x - 0.6, cy + 1.6)]))
    win = ik.union(*wins)
    det = [('col', win, fire), ('ink', [(cx - 3.4, cy + 2.9), (cx, cy + 3.5), (cx + 3.4, cy + 2.9)], 1.0)]
    cv.shape(pot, M, z=z, sd=1.3, hi=0.4, details=det)
    cv.fill(ik.isect(win, ik.moved(win, cv.u(0.3), cv.u(0.2))), hot, z=z + 0.05, glow=gl)
    # rim + kubbe kapak + tepe çubuğu
    cv.shape(cv.ellipse((cx, cy - 1.6), 4.1, 1.0), M, z=z + 0.2, sd=0.6, hi=0.35)
    lid = cv.blob([(cx - 3.0, cy - 2.0), (cx - 2.2, cy - 3.8), (cx, cy - 4.8), (cx + 2.2, cy - 3.8), (cx + 3.0, cy - 2.0)])
    holes = ik.union(*[cv.ellipse((cx - 1.4 + k * 1.4, cy - 3.0), 0.38, 0.5) for k in range(3)])
    cv.shape(lid, M, z=z + 0.3, sd=0.8, hi=0.35, details=[('col', holes, fire)])
    cv.fill(holes, hot, z=z + 0.35, glow=gl)
    cv.shape(cv.blob([(cx - 0.5, cy - 4.6), (cx, cy - 7.0, 0.0), (cx + 0.5, cy - 4.6)]), M, z=z + 0.4, sd=0.3, hi=0.2, ol=0.7)
    cv.shape(cv.ellipse((cx, cy - 5.0), 0.8, 0.8), M, z=z + 0.45, sd=0.3, hi=0.2, ol=0.7)
    # kulp halkaları
    for s in (-1, 1):
        ring = ik.diff(cv.ellipse((cx + s * 4.1, cy - 0.6), 1.1, 1.3), cv.ellipse((cx + s * 4.1, cy - 0.6), 0.5, 0.7))
        cv.shape(ring, M, z=z + 0.25, sd=0.3, hi=0.2, ol=0.7)


def draw(cv, p, V):
    t = p.get('t', 0.0)
    ph = t * math.tau
    fl = math.sin(ph) * 2.0 + p.get('dy', 0.0)
    lean = p.get('lean', 0.0)
    att = p.get('att', 0.0)
    flare = p.get('flare', 0.0)
    hurt = p.get('hurt', 0.0)
    cx, cy = 0.0, -29 + fl
    hx = cx + lean * 3
    R, RB, MT = V['robe'], V['robe_b'], V['mantle']
    ex = V['extra']

    # ---- kanatlar (kan çoru): omuzdan geriye açılan yırtık zar
    if 'wings' in ex:
        WM = Ink('#b23a48', '#5a1630', '#e0666a', '#2a0818', name='kanat zarı')
        for k, (zz, sp, m) in enumerate(((-9.0, 1.0, WM), (-3.5, 0.82, Ink(WM.shadow, WM.deep, WM.base)))):
            root = (hx - 3.0 + k * 1.5, cy - 8.0)
            beat = math.sin(ph * 1.0 + k * 0.6) * 0.18 - lean * 0.2
            a0 = math.pi * (1.28 if k == 0 else 1.14) + beat
            fingers = []
            for j in range(4):
                a = a0 - 0.05 + j * 0.3
                L = (26.0 - j * 3.6) * sp
                fingers.append((root[0] + math.cos(a) * L, root[1] + math.sin(a) * L))
            pts = [root, (fingers[0][0], fingers[0][1], 0.0)]
            for j in range(1, 4):
                mid = lerp2(fingers[j - 1], fingers[j], 0.5)
                mid = lerp2(mid, root, 0.22)
                pts += [mid, (fingers[j][0], fingers[j][1], 0.0)]
            pts += [lerp2(fingers[-1], (hx + 1, cy + 3), 0.5), (hx + 1, cy + 2)]
            det = [('ink', [root, lerp2(root, f, 0.6), f], 2.0, (0.05, 0.85)) for f in fingers]
            cv.shape(cv.blob(pts), m, z=zz, sd=2.0, hi=0.0, details=det, ol=0.9)
            cv.shape(cv.ellipse(root, 1.4, 1.4), Ink('#3a1a24'), z=zz + 0.1, sd=0.5, ol=0.7)
    # ---- kefen kuyrukları: arkada iki uzun yırtık şerit (kumaş gibi geniş kök, dalgalanır)
    tails = ((-7.5, 6, 0.0, RB, 0.86, 7.0),)
    for k, (sx, n, ph0, mat, a0, w0) in enumerate(tails):
        _tail(cv, (cx + sx, cy + 5), n, 3.4, math.pi * a0 - lean * 0.4, ph + ph0, mat, -6 + k, w0, k * 1.3, fade=V['tail_fade'])
    # ---- arka kol: yen + kemik pençe
    ab = p.get('ab', (1.2, 0.6))
    shb = (hx - 3.5, cy - 6)
    e, h = fk_arm(shb, ab[0], ab[1], 5.5, 5.5)
    m_ = _sleeve(cv, shb, e, h, RB, -8, 2.4, 3.0, 11, False)
    cv.shape(cv.limb([m_, h], [0.75, 0.6]), V['bone'], z=-8.5, sd=0.4)
    a = ab[0] + ab[1]
    yk.bone_hand(cv, h, math.pi / 2 - a, V['bone'], -8.4, n=4, L=4.0, spread=0.35, curl=0.55, r=0.36)
    # ---- kefen gövde: omuzdan aşağı daralır, yırtık etek
    fw = math.sin(ph + 0.8) * 1.2
    hem = [(cx + 8.0, cy + 2.0), (cx + 7.2, cy + 7.0)] + yk.ragged((cx + 6.0, cy + 9.0), (cx - 13.0 + fw, cy + 15.0), 5, 5.0, seed=3, side=1.0) +         [(cx - 14.5 + fw, cy + 13.0, 0.0), (cx - 11.0, cy + 4.0), (cx - 9.5, cy - 1.0)]
    body = cv.blob([(hx - 7.0, cy - 9.0), (hx + 6.0, cy - 9.0), (cx + 8.2, cy - 2.0)] + hem)
    fold = []
    fold += cv.fold([(hx + 2.0, cy - 7.0), (cx + 2.8, cy - 1.0), (cx + 3.4, cy + 7.0)], 1.0, 1.4, -1)
    fold += cv.fold([(hx - 3.0, cy - 7.0), (cx - 3.0, cy + 0.0), (cx - 1.5, cy + 8.5)], 1.1, 1.4, 1)
    fold += cv.fold([(cx - 6.5, cy - 2.0), (cx - 6.0, cy + 4.0), (cx - 5.0, cy + 8.0)], 0.8, 1.2, 1)
    if V['stain_a'] > 0:   # salgın lekesi: etekten yukarı sızan ıslak leke
        st = V['stain']
        stain = cv.blob([(cx - 9, cy + 2), (cx - 4, cy - 1.5), (cx + 1, cy + 1.5), (cx + 6, cy - 0.5), (cx + 9, cy + 3), (cx + 9, cy + 14), (cx - 9, cy + 14)])
        fold.append(('fn', lambda c, s=stain, st=st: c.drawPath(s, yk.paint(st, V['stain_a'], cv.u(0.8)))))
    for (hx_, hy_, rr) in ((cx - 4.5, cy + 3.5, 1.6), (cx + 3.2, cy + 7.0, 1.2), (cx - 9.0, cy + 9.5, 1.0)):
        hole_ = cv.blob(yk.ragged((hx_ - rr, hy_), (hx_ + rr, hy_), 2, rr * 0.9, seed=int(hx_ * 7) % 97, side=-1.0) +
                        yk.ragged((hx_ + rr, hy_), (hx_ - rr, hy_), 2, rr * 0.9, seed=int(hy_ * 5) % 89, side=-1.0))
        fold.append(('col', hole_, INK))
    cv.shape(body, R, z=0, sd=3.2, hi=0.45, details=fold, hatch=0.35, bounce=0.35)
    # göğüste kemik muska + ip
    cord = [(hx - 5.5, cy - 7.5), (hx - 1.0, cy - 4.2), (hx + 4.5, cy - 7.0)]
    cv.stroke(cord, 1.0, z=5.5, col=(0.35, 0.28, 0.24), taper=(0.0, 0.0))
    am = (hx - 1.0, cy - 3.2)
    cv.shape(cv.blob([(am[0] - 1.0, am[1]), (am[0] + 1.0, am[1]), (am[0] + 0.6, am[1] + 2.6), (am[0], am[1] + 3.4, 0.0), (am[0] - 0.6, am[1] + 2.6)]),
             V['metal'] if V['face'] == 'gold' else V['bone'], z=5.6, sd=0.5, hi=0.3, ol=0.8,
             details=[('ink', [(am[0], am[1] + 0.6), (am[0], am[1] + 2.4)], 0.9)])
    # ---- omuz örtüsü (pelerin): yırtık kenarlı kısa katman
    mpts = [(hx - 8.2, cy - 10.0), (hx + 6.4, cy - 10.5), (hx + 7.8, cy - 6.0)] + \
        yk.ragged((hx + 7.0, cy - 4.5), (hx - 9.0, cy - 3.5), 4, 2.4, seed=7, side=1.0) + [(hx - 9.8, cy - 6.5)]
    mdet = cv.fold([(hx - 1.0, cy - 9.0), (hx - 0.5, cy - 6.0), (hx + 0.5, cy - 3.2)], 0.7, 1.2, 1)
    if 'feathers' in ex:   # kartal tüyü yaka: üst üste binen sivri tüyler
        mpts = [(hx - 8.2, cy - 10.0), (hx + 6.4, cy - 10.5), (hx + 8.4, cy - 6.0)] + \
            yk.ragged((hx + 8.0, cy - 4.5), (hx - 10.0, cy - 2.5), 6, 4.2, seed=8, side=1.0) + [(hx - 10.5, cy - 6.5)]
        for j in range(6):
            x0 = hx + 6.0 - j * 2.7
            mdet.append(('ink', [(x0, cy - 7.5), (x0 - 0.4, cy - 4.5 + (j % 2)), (x0 - 0.9, cy - 2.0 + (j % 2) * 1.2)], 0.9, (0.2, 0.7)))
            mdet.append(('stroke', [(x0 - 0.7, cy - 7.0), (x0 - 1.0, cy - 4.0)], 1.2, MT.shadow, (0.3, 0.6)))
    cv.shape(cv.blob(mpts), MT, z=6, sd=1.8, hi=0.4, details=mdet, fur=0.6 if 'feathers' in ex else 0.0)
    if 'icicles' in ex:
        yk.icicles(cv, [(hx + 6.5, cy - 4.5), (hx + 3.0, cy - 3.0), (hx - 1.0, cy - 2.6), (hx - 5.0, cy - 2.4)], Ink('#e8f6ff', '#7aa0d0', '#ffffff'), 6.5, L=3.0, w=0.7, seed=4)
        yk.icicles(cv, [(cx + 6.5, cy + 3.0), (cx + 3.0, cy + 7.0), (cx - 2.0, cy + 7.5), (cx - 6.5, cy + 5.5)], Ink('#e8f6ff', '#7aa0d0', '#ffffff'), 1.0, L=3.5, w=0.8, seed=5)
    # ---- başlık
    tip_y = cy - 13 + fl * 0.3 - lean * 2
    if V['hood'] == 'cap':     # Saka börkü: dimdik sivri keçe külah, altın plakalı
        hood = cv.blob([(hx - 6.5, cy - 6), (hx - 8.0, cy - 13), (hx - 6.0, cy - 19), (hx - 4.0, cy - 25.0), (hx - 4.5, cy - 33.0, 0.0),
                        (hx + 0.5, cy - 26.0), (hx + 5.8, cy - 21.5), (hx + 8.5, cy - 15.5), (hx + 8, cy - 9), (hx + 5, cy - 5)])
    elif V['hood'] == 'ears':  # kulaklı başlık (yarasa)
        hood = cv.blob([(hx - 6.5, cy - 6), (hx - 9, cy - 13), (hx - 8.5, cy - 19), (hx - 7.5, cy - 29.0, 0.0), (hx - 3.5, cy - 23.0),
                        (hx + 0.0, cy - 24.0), (hx + 3.0, cy - 31.0, 0.0), (hx + 5.0, cy - 22.5), (hx + 8.5, cy - 15.5), (hx + 8, cy - 9), (hx + 5, cy - 5)])
    else:
        hood = cv.blob([(hx - 6.5, cy - 6), (hx - 9, cy - 13), (hx - 14.5, tip_y, 0.0), (hx - 8.5, cy - 19), (hx - 4, cy - 23.5),
                        (hx + 1.5, cy - 24.5), (hx + 6, cy - 21.5), (hx + 8.5, cy - 15.5), (hx + 8, cy - 9), (hx + 5, cy - 5)])
    hdet = cv.fold([(hx - 5.0, cy - 21.0), (hx - 3.0, cy - 16.0), (hx - 3.5, cy - 9.0)], 1.0, 1.3, 1)
    hdet += cv.fold([(hx - 9.0, cy - 13.5), (hx - 6.0, cy - 12.0), (hx - 4.5, cy - 8.0)], 0.6, 1.1, 1)
    if V['hood'] == 'cap':
        for j in range(3):
            q = (hx - 3.8 + j * 0.2, cy - 28.0 + j * 4.0)
            hdet.append(('col', cv.blob([(q[0] - 1.0, q[1]), (q[0], q[1] - 1.2), (q[0] + 1.0, q[1]), (q[0], q[1] + 1.2)]), GOLD.base))
    cv.shape(hood, R, z=4, sd=3.0, hi=0.5, details=hdet, hatch=0.3, bounce=0.3, cast=0.8)
    # başlık ağzı
    oc = (hx + 4.2, cy - 14.0)
    lip = cv.ellipse(oc, 4.6, 6.0, 0.2)
    cv.shape(lip, MT if V['hood'] != 'cap' else R, z=10, sd=1.0, hi=0.4, ol=0.8)
    hole = cv.ellipse((oc[0] + 0.5, oc[1] + 0.4), 3.6, 5.0, 0.2)
    cv.fill(hole, INK, z=11)
    if flare > 0:
        yk.glow_soft(cv, (oc[0] + 1.0, oc[1] + 1.0), 3.5, V['eye_glow'], z=11.1, blur=0.6, alpha=0.2 * flare)
    ey = oc[1] - 1.4
    er = 1.0 + 0.35 * flare - 0.4 * hurt
    face = V['face']
    if face == 'gold':      # altın ölü maskesi
        mask = cv.blob([(oc[0] - 2.4, oc[1] - 3.6), (oc[0] + 3.2, oc[1] - 3.8), (oc[0] + 3.6, oc[1] + 0.5), (oc[0] + 2.4, oc[1] + 3.8),
                        (oc[0] + 0.5, oc[1] + 4.6, 0.0), (oc[0] - 1.6, oc[1] + 3.2), (oc[0] - 2.6, oc[1] - 0.5)])
        slits = ik.union(cv.ellipse((oc[0] - 0.6, ey + 0.1), 1.1, 0.4, -0.1), cv.ellipse((oc[0] + 2.2, ey), 1.0, 0.4, 0.1))
        mdet = [('col', slits, INK), ('ink', [(oc[0] + 0.8, ey + 0.4), (oc[0] + 1.4, oc[1] + 1.6), (oc[0] + 0.7, oc[1] + 2.0)], 0.9),
                ('ink', [(oc[0] - 0.6, oc[1] + 2.8), (oc[0] + 2.2, oc[1] + 2.7)], 1.0, (0.2, 0.2))]
        cv.shape(mask, GOLD, z=12, sd=1.0, hi=0.4, details=mdet)
        yk.eye_glow(cv, (oc[0] - 0.6, ey + 0.1), 0.7 * er, 0.28 * er, -0.1, V['eye'], V['eye_glow'], 13)
        yk.eye_glow(cv, (oc[0] + 2.2, ey), 0.65 * er, 0.28 * er, 0.1, V['eye'], V['eye_glow'], 13)
    elif face == 'beak':    # demir kuş gagası maske
        mask = cv.blob([(oc[0] - 2.0, oc[1] - 3.6), (oc[0] + 2.8, oc[1] - 3.4), (oc[0] + 4.0, oc[1] - 1.0), (oc[0] + 12.5, oc[1] + 2.4 + att * 0.6, 0.0),
                        (oc[0] + 3.4, oc[1] + 3.0), (oc[0] - 1.0, oc[1] + 3.0)])
        mdet = [('ink', [(oc[0] + 3.4, oc[1] + 0.3), (oc[0] + 8.0, oc[1] + 1.6), (oc[0] + 12.0, oc[1] + 2.4)], 1.0, (0.1, 0.8))]
        mdet += [('col', cv.ellipse((oc[0] + 0.4 + j * 1.4, oc[1] + 2.0), 0.35, 0.35), IRON.hi) for j in range(3)]
        cv.shape(mask, IRON, z=12, sd=1.1, hi=0.45, details=mdet)
        cv.fill(cv.ellipse((oc[0] + 1.2, ey), 1.3, 1.1), INK, z=12.5)
        yk.eye_glow(cv, (oc[0] + 1.3, ey), 0.75 * er, 0.55 * er, 0.0, V['eye'], V['eye_glow'], 13)
    elif face == 'mask':    # soluk ağlayan yüz maskesi (kayıp ruh)
        mask = cv.ellipse((oc[0] + 0.8, oc[1] + 0.2), 2.8, 3.8, 0.15)
        mdet = [('ink', [(oc[0] + 0.0, oc[1] + 2.6), (oc[0] + 1.0, oc[1] + 2.2), (oc[0] + 2.0, oc[1] + 2.8)], 0.9, (0.2, 0.2))]
        cv.shape(mask, Ink('#dcd8ec', '#7c78a4', '#ffffff'), z=12, sd=0.9, hi=0.3, details=mdet)
        for dx_ in (-0.4, 2.0):
            cv.fill(cv.ellipse((oc[0] + dx_, ey + 0.4), 0.7, 0.9), INK, z=12.4)
            yk.eye_glow(cv, (oc[0] + dx_, ey + 0.4), 0.38 * er, 0.5 * er, 0.0, V['eye'], V['eye_glow'], 13)
            cv.stroke([(oc[0] + dx_, ey + 1.2), (oc[0] + dx_ + 0.1, ey + 3.4), (oc[0] + dx_ - 0.1, ey + 5.0)], 0.9, z=13, col=V['fire'], taper=(0.1, 0.9), glow=V['eye_glow'])
    else:                   # karanlıkta iki göz + kemik dişler
        yk.eye_glow(cv, (oc[0] - 0.2, ey), 0.95 * er, 0.55 * er, -0.25, V['eye'], V['eye_glow'], 13)
        yk.eye_glow(cv, (oc[0] + 2.7, ey + 0.1), 0.8 * er, 0.5 * er, 0.2, V['eye'], V['eye_glow'], 13)
        # karanlıkta seçilen kafatası: elmacık kemiği hilali ve sivri alt dişler (ağız saldırıda açılır)
        cv.fill(cv.blob([(oc[0] - 1.6, oc[1] + 0.2), (oc[0] + 0.8, oc[1] + 0.9), (oc[0] + 3.6, oc[1] + 0.1), (oc[0] + 3.4, oc[1] + 0.7),
                         (oc[0] + 0.8, oc[1] + 1.6), (oc[0] - 1.4, oc[1] + 0.9)]), V['robe'].shadow, z=12.4)
        jaw = 0.4 + att * 1.6
        for i, (dx_, ln) in enumerate(((-0.6, 1.3), (0.7, 1.7), (1.9, 1.5), (3.0, 1.1))):
            y0 = oc[1] + 3.6 + jaw
            cv.fill(cv.blob([(oc[0] + dx_ - 0.4, y0), (oc[0] + dx_ + 0.4, y0), (oc[0] + dx_ + 0.05, y0 - ln, 0.0)]), V['bone'].shadow, z=12.6)
    # ---- buhurdan (ön kolun zincirinde)
    af = p.get('af', (0.9, 0.5))
    sh = (hx + 4.5, cy - 6)
    e, h = fk_arm(sh, af[0], af[1], 5.5, 5.5)
    sw = p.get('sw', math.sin(ph) * 0.35)
    L = 8.0
    cen = (h[0] + math.sin(sw) * L, h[1] + math.cos(sw) * L)
    cz = p.get('cz', 16)
    lid = (cen[0] - math.sin(sw) * 5.0, cen[1] - math.cos(sw) * 5.0)
    yk.chain_links(cv, h, lid, 4, V['metal'], cz - 0.5, r=0.7)
    _lantern(cv, cen, V, cz, flare, t)
    # tüten duman (sporlu teller): fenerden yükselip kıvrılır
    sm = V['smoke']
    for i in range(2):
        u = ((t + i * 0.5) % 1.0)
        yk.wisp(cv, (cen[0] - 0.3 + i * 0.6, cen[1] - 6.5), -math.pi / 2 - 0.25 + i * 0.2, 9.0 + 3.0 * u, 2.6 + 0.8 * u, sm, -2 + i * 0.1,
                ph=ph + i * 2.0, curl=0.8, alpha=0.55 - 0.25 * u, glow=V['smoke_glow'], glow_a=0.5, ink=(i == 0))
    for i in range(3):
        u = ((t * 1.0 + i / 3.0) % 1.0)
        q = (cen[0] - 1 + math.sin(u * 6 + i) * 1.6 - u * 2.5, cen[1] - 7 - u * 10)
        cv.fill(cv.ellipse(q, 0.45, 0.45), V['fire_hot'], z=-1.9, glow=V['glow'], alpha=1.0 - u * 0.6)
    pf = p.get('puff', 0.0)
    if pf > 0:   # spor patlaması: fenerin önünde büyük bulut + saçılan sporlar
        yk.cloud(cv, (cen[0] + 4.0 * pf, cen[1] - 0.5), 4.6 * pf, sm, cz + 4, seed=21, lobes=9, glow=V['smoke_glow'],
                 spores=10, spore_glow=V['glow'])
        yk.cloud(cv, (cen[0] + 8.5 * pf, cen[1] - 3.5 * pf), 2.4 * pf, sm, cz + 4.2, seed=22, lobes=7, glow=V['smoke_glow'])
        yk.sparks(cv, (cen[0] + 3, cen[1]), 9, 4.0 * pf, 9.0 * pf, V['fire_hot'], cz + 5, seed=4, w=1.3, glow=V['glow'])
    if flare > 0:   # hazırlık: buhurdandan fışkıran kıvılcımlar (uyarı)
        yk.sparks(cv, cen, 7, 3.5, 6.5, V['fire_hot'], cz + 2, seed=9, w=1.2, glow=V['glow'])
    if 'embers' in ex:
        yk.sparks(cv, (cen[0], cen[1] - 3), 4, 2.0, 5.0, V['fire_hot'], cz + 2, seed=int(t * 30) + 2, w=1.0, glow=V['glow'], ang=-math.pi / 2, spread=1.2)
    # ---- ön kol: yen, kemik ön kol ve zinciri tutan el
    m_ = _sleeve(cv, sh, e, h, R, 24, 2.5, 3.2, 21, True)
    cv.shape(cv.limb([m_, lerp2(m_, h, 0.5), h], [0.85, 0.7, 0.75]), V['bone'], z=23.6, sd=0.4, hi=0.2)
    a = af[0] + af[1]
    yk.bone_hand(cv, h, math.pi / 2 - a, V['bone'], 25.0, n=4, L=3.4, spread=0.42, curl=1.0, palm=1.1, r=0.38)
    _caput(cv, m_, V, 24.5, ph)
    if 'shackle' in ex:   # kırık pranga: bilekte demir halka, sarkan kopuk zincir
        cv.shape(cv.ellipse(lerp2(m_, h, 0.55), 1.5, 1.1, math.atan2(h[1] - m_[1], h[0] - m_[0]) + math.pi / 2), IRON, z=25.5, sd=0.5, hi=0.3)
        q0 = lerp2(m_, h, 0.55)
        q1 = (q0[0] - 1.5 + math.sin(ph) * 0.8, q0[1] + 6.0)
        yk.chain_links(cv, q0, q1, 4, IRON, 25.4, r=0.6)
    return {'mouth': (cen[0], cen[1] + 0.5)}


def _pose(anim, i):
    n, fn, loop, arm = ANIMS[anim]
    p = dict(fn(i / n))
    if anim == 'attack' and i == 0:
        p['flare'] = 1.0          # hazırlık: ateş parlar, gözler büyür (oyuncu okur)
        p['cz'] = 15              # geriye çekilen buhurdan gövdenin önünde görünür (v1'de arkada kalıyordu)
    if anim == 'hurt':
        p['hurt'] = 1.0
    return p


SHADE = dict(outer=0.5, rim=0.6, rim_col=(0.7, 0.78, 1.0), rim_dir=(0.6, -0.8), rim_w=1.4, form=(5.0, (0.76, 0.74, 0.88)))


def render_frame(anim, i, var='cor', ss=3):
    V = VARIANTS[var]
    p = _pose(anim, i)
    cv = yk.occlude_glow(ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss))
    info = draw(cv, p, V)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
