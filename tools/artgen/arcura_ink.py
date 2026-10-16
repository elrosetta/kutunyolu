"""Kara Kam (kimlik arcura) ve biyom çeşitlemeleri — stil v2 "mürekkep-cel". v1: creatures.draw_kam.

Aynı iskelet ve pozlar (creatures.KAM_ANIMS: idle 4, run 6, cast 3, hurt 1) ve 'hand' çapası (lanet küresi; büyü
oradan fırlar). Hücre dünya 76x72 (v1 64x64), ayak (36, 66), doku 4.

Tasarım: Erlik'e kul olmuş kara kam. Sibirya-Türk kam giysisi (manyak): diz altına inen deri kaftan, eteğinde ve
kollarında uzun deri saçaklar ve kızıl şeritler, göğsünde demir çıngıraklar ve tunç kuzgu (kam aynası); başında
baykuş tüyü yelpazesi ve geyik boynuzlu taç, yüzünde kemik maske ve gözlerin önüne sarkan saçak. Arka elinde
boyalı kam davulu (tüngür: Hayat Ağacı, Ay ve Güneş), ön elinde mor yanan lanet. Saldırı uyarısı: davula vurur,
eli geriye kalkar, küre büyür ve çevresinde lanet halkası döner; maskenin gözleri yanar.

Çeşitlemeler (VARIANTS; `<kimlik>_v2`):
  arcura          Kara Kam        (Ötüken)   kızıl-kahve post, kemik maske, baykuş tüyü, geyik boynuzu, Erlik moru
  kurgan_okcusu   Kurgan Kamı     (Bozkır)   aşı keçe, at kafatası maske, kartal tüyü taç, altın kuzgu, kehribar lanet
  isilti_bocegi   Işıltı Kamı     (Şahmeran) koyu deniz yeşili, gözleri bağlı kör kam, başında ışıldayan kristaller, yeşil ışık
  erlik_kizi      Erlik'in Kızı   (Tamu)     kara uzun saç, solgun yüz, kızıl dudak, küçük kara boynuzlar, kızıl-kara
                                             yırtık elbise; davul yerine kara kuzgu ayna, macenta büyü
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_leg, fk_arm, lerp2
from creatures import KAM_ANIMS
import yaratik_ink_kit as yk

TEX = 4.0
CELL = (304, 288)       # dünya 76 x 72
FEET = (144, 264)       # dünya (36, 66)
ANIMS = {k: (v[0], v[1], k in ('idle', 'run'), True) for k, v in KAM_ANIMS.items()}

IRON = Ink('#6a6c7c', '#30303e', '#b0b4c8', '#1a1a24', kind='metal', name='demir')
BRONZE = Ink('#c08a40', '#62381c', '#f6d890', '#341e0e', kind='metal', name='tunç')
BONE = Ink('#e8dfc6', '#8c8072', '#fffbea', '#564a44', name='kemik')
WOOD = Ink('#8a5a34', '#40221a', '#b88654', name='davul kasnağı')


def _v(**kw):
    base = dict(
        coat=Ink('#7a3a2c', '#3a1620', '#a8583e', '#1e0a12', name='kam postu'),
        coat_b=Ink('#55281f', '#2a0e16', '#76402e', '#14060c', name='post arkası'),
        fringe=Ink('#c49a64', '#6a4a34', '#ecc890', name='deri saçak'),
        stripe=(0.75, 0.16, 0.14), skin=Ink('#8a8aa4', '#44446a', '#b6b6cc', name='kam eli'),
        boot=Ink('#3a2a2a', '#1a1218', '#5a4444', name='keçe çizme'),
        drum=Ink('#d8c49c', '#8a6c54', '#f6ead0', name='davul derisi'), paint=(0.62, 0.14, 0.1),
        feather=Ink('#b8956a', '#5c4434', '#e2c69a', '#2e2018', name='baykuş tüyü'), feather_bar=(0.32, 0.22, 0.16),
        horn=BONE, mask='bone', crown='owl',
        curse=(0.78, 0.35, 1.0), curse_hot=(0.96, 0.85, 1.0), curse_glow=(0.6, 0.15, 1.0),
        eye=(1.0, 0.35, 0.3), eye_glow=(0.9, 0.12, 0.08), mirror=BRONZE,
        hair=None, extra=(),
    )
    base.update(kw)
    return base


VARIANTS = {
    'arcura': _v(),
    'kurgan_okcusu': _v(
        coat=Ink('#b0824a', '#5e3a28', '#dcae6e', '#2e1a14', name='aşı keçe'),
        coat_b=Ink('#865c36', '#432618', '#a87a4c', '#22120c', name='keçe arkası'),
        fringe=Ink('#d8c090', '#7e664a', '#f8e8c0', name='açık saçak'), stripe=(0.6, 0.12, 0.12),
        feather=Ink('#5e4636', '#2a1c18', '#8c6a50', '#140c0a', name='kartal tüyü'), feather_bar=(0.92, 0.88, 0.8),
        mask='horse', crown='eagle', mirror=Ink('#e6b84c', '#8a521c', '#fff2b8', '#4a2a0c', kind='metal', name='altın'),
        curse=(1.0, 0.72, 0.25), curse_hot=(1.0, 0.95, 0.7), curse_glow=(1.0, 0.5, 0.05),
        eye=(1.0, 0.8, 0.35), eye_glow=(1.0, 0.5, 0.05)),
    'isilti_bocegi': _v(
        coat=Ink('#2c5a5a', '#122a36', '#468a80', '#08141c', name='mağara postu'),
        coat_b=Ink('#1e4044', '#0c1c26', '#2e605c', '#050c12', name='post arkası'),
        fringe=Ink('#9ab8a0', '#4a6a64', '#cce4cc', name='yosun saçak'), stripe=(0.3, 0.75, 0.55),
        drum=Ink('#b8d4c0', '#5e8078', '#e2f4e6', name='davul derisi'), paint=(0.1, 0.42, 0.36),
        feather=Ink('#6fe0c0', '#2a7a7a', '#d0fff0', '#124a4c', name='kristal'), feather_bar=(0.85, 1.0, 0.95),
        mask='blind', crown='crystal', mirror=IRON,
        curse=(0.45, 1.0, 0.65), curse_hot=(0.9, 1.0, 0.9), curse_glow=(0.15, 0.95, 0.45),
        eye=(0.5, 1.0, 0.7), eye_glow=(0.15, 0.95, 0.45)),
    'erlik_kizi': _v(
        coat=Ink('#7c1a2a', '#34081c', '#b03040', '#1a0410', name='kızıl elbise'),
        coat_b=Ink('#2a1420', '#140810', '#462232', '#0a0408', name='kara astar'),
        fringe=Ink('#2e1622', '#140a10', '#5a2c3e', name='yırtık etek'), stripe=(0.9, 0.7, 0.3),
        skin=Ink('#d8cad8', '#7c6c96', '#fff4fc', name='solgun ten'), boot=Ink('#1e1218', '#0c060a', '#3a2830', name='kara çizme'),
        feather=Ink('#1e1620', '#0c080e', '#463a4e', '#060408', name='kara saç'), feather_bar=(0.3, 0.2, 0.35),
        horn=Ink('#2a2228', '#100c10', '#6a5a66', '#060406', name='kara boynuz'),
        mask='face', crown='horns', mirror=Ink('#2a2434', '#0e0c16', '#8a7aa8', '#06050a', kind='metal', name='kara ayna'),
        curse=(1.0, 0.35, 0.8), curse_hot=(1.0, 0.85, 0.95), curse_glow=(1.0, 0.12, 0.6),
        eye=(1.0, 0.55, 0.85), eye_glow=(1.0, 0.15, 0.6), hair=Ink('#1e1620', '#0c080e', '#463a4e', '#060408', name='kara saç'),
        extra=('mirror',)),
}


def _drum(cv, dc, rot, V, z, ph, dr):
    """Kam davulu (tüngür): kasnak + boyalı deri + asılı demir çıngıraklar. Erlik kızında kara ayna."""
    if 'mirror' in V['extra']:
        M = V['mirror']
        cv.shape(cv.ellipse(dc, 5.0, 5.4, rot), M, z=z, sd=1.4, hi=0.6, details=[('col', cv.ellipse((dc[0] + 0.6, dc[1] + 0.5), 3.4, 3.8, rot), (0.05, 0.03, 0.08))])
        yk.glow_soft(cv, (dc[0] + 0.8, dc[1]), 3.0, V['curse_glow'], z=z + 0.1, blur=0.6, alpha=0.25 + 0.3 * dr)
        cv.stroke([(dc[0] - 1.6, dc[1] - 1.6), (dc[0] + 0.4, dc[1] - 2.6)], 1.2, z=z + 0.2, col=(0.8, 0.7, 0.95), taper=(0.3, 0.3))
        for k in range(8):   # kenarda kemik dişler
            a = k / 8 * math.tau
            q = (dc[0] + math.cos(a) * 5.4, dc[1] + math.sin(a) * 5.8)
            cv.shape(cv.blob([(q[0] - math.sin(a) * 0.6, q[1] + math.cos(a) * 0.6), (q[0] + math.cos(a) * 1.4, q[1] + math.sin(a) * 1.4, 0.0),
                              (q[0] + math.sin(a) * 0.6, q[1] - math.cos(a) * 0.6)]), BONE, z=z - 0.1, sd=0.3, ol=0.6)
        return
    cv.shape(cv.ellipse(dc, 5.5, 7.3, rot), WOOD, z=z, sd=1.2, hi=0.4)
    skin = cv.ellipse(dc, 4.5, 6.3, rot)
    cr, sr = math.cos(rot), math.sin(rot)
    P = lambda u, v: (dc[0] + u * cr - v * sr, dc[1] + u * sr + v * cr)
    col = V['paint']
    det = [('stroke', [P(0, -5.2), P(0, 5.2)], 1.6, col, (0.1, 0.1)),           # Hayat Ağacı gövdesi
           ('stroke', [P(0, -2.0), P(-2.4, -3.8)], 1.2, col, (0.0, 0.5)), ('stroke', [P(0, -2.0), P(2.4, -3.8)], 1.2, col, (0.0, 0.5)),
           ('stroke', [P(0, 0.8), P(-2.8, -0.6)], 1.2, col, (0.0, 0.5)), ('stroke', [P(0, 0.8), P(2.8, -0.6)], 1.2, col, (0.0, 0.5)),
           ('stroke', [P(-4.0, 2.8), P(4.0, 2.8)], 1.3, col, (0.1, 0.1)),           # yer çizgisi
           ('col', cv.ellipse(P(-2.6, -4.6), 0.9, 0.9), col),                         # güneş
           ('col', ik.diff(cv.ellipse(P(2.6, -4.6), 0.9, 0.9), cv.ellipse(P(3.0, -4.9), 0.8, 0.8)), col)]   # ay
    cv.shape(skin, V['drum'], z=z + 0.5, sd=1.4, hi=0.3, details=det)
    for i in range(3):
        a = 1.3 + i * 0.35
        q = (dc[0] + math.cos(a) * 4.9, dc[1] + math.sin(a) * 6.7)
        e = (q[0] + math.sin(ph + i) * 0.6, q[1] + 2.6)
        cv.stroke([q, e], 0.9, z=z + 0.6, col=(0.3, 0.26, 0.24))
        cv.shape(cv.blob([(e[0] - 0.7, e[1]), (e[0] + 0.7, e[1]), (e[0] + 0.4, e[1] + 2.2), (e[0] - 0.4, e[1] + 2.2)]), IRON, z=z + 0.7, sd=0.3, hi=0.2, ol=0.6)
    if dr > 0.5:   # vuruş: davul titrer (mürekkep yayları)
        for k in range(2):
            r_ = 7.8 + k * 1.6
            cv.stroke([P(r_ * 0.6 * math.cos(a), r_ * math.sin(a)) for a in np.linspace(-0.9, 0.9, 5)], 1.0, z=z + 0.8, col=INK, taper=(0.5, 0.5))


def draw(cv, p, V):
    bob, lean = p.get('bob', 0.0), p.get('lean', 0.0)
    cast = p.get('cast', 0.0)
    ph = p.get('ph', 0.0)
    flare = p.get('flare', 0.0)
    hip = (0.0, -12 + bob)
    lx = lean * 5
    C, CB, FR = V['coat'], V['coat_b'], V['fringe']
    # ---- erlik kızı: arkada dalgalanan uzun saç
    hd = (2.0 + lx * 1.3, hip[1] - 18.5)
    if V['hair'] is not None:
        hairp = []
        for k in range(5):
            st = [(hd[0] - 1.5 + k * 0.3, hd[1] - 2.5 + k * 0.6)]
            x, y = st[0]
            for j in range(6):
                a = math.pi * (0.62 + 0.04 * k) + math.sin(ph + j * 0.8 + k) * 0.12 + lean * 0.4
                x += math.cos(a) * 3.0
                y += math.sin(a) * 3.0
                st.append((x, y))
            hairp.append(ik.taper_path([cv.W(q) for q in st], cv.u(3.4 - k * 0.3), (0.05, 0.8)))
        cv.shape(ik.union(*hairp), V['hair'], z=-18, sd=1.5, hi=0.6, details=[('stroke', [(hd[0] - 3, hd[1] - 1), (hd[0] - 7, hd[1] + 6)], 1.0, V['hair'].hi, (0.2, 0.6))])
    # ---- bacaklar: keçe çizme, uçları kalkık
    for side, (a1, a2) in ((-1, p.get('lb', (0.2, 0.3))), (1, p.get('lf', (-0.15, 0.3)))):
        z = -4 if side < 0 else -1
        base = (hip[0] + side * 2, hip[1])
        k, f = fk_leg(base, a1, a2, 5.6, 6.0)
        bm = V['boot'] if side > 0 else Ink(V['boot'].shadow, V['boot'].deep, V['boot'].base)
        leg = ik.union(cv.limb([base, k, f], [2.0, 1.7, 1.6]),
                       cv.blob([(f[0] - 1.6, f[1] - 1.2), (f[0] + 1.8, f[1] - 0.9), (f[0] + 3.4, f[1] - 1.4, 0.0), (f[0] + 3.0, f[1] + 0.4), (f[0] - 1.6, f[1] + 0.5)]))
        cv.shape(leg, bm, z=z, sd=1.0, hi=0.3 if side > 0 else 0.0,
                 details=[('stroke', [lerp2(k, f, 0.55), (lerp2(k, f, 0.55)[0] + 1.4, lerp2(k, f, 0.55)[1])], 1.2, V['stripe'], (0.1, 0.1))])
    # ---- davul (arka elde, gövdenin arkasında) + arka kol
    dr = p.get('drum', 0.0)
    dc = (hip[0] - 9.5 + lx * 0.5, hip[1] - 12 - dr * 3)
    _drum(cv, dc, 0.25 - dr * 0.3, V, -16, ph, dr)
    shb = (hip[0] - 3 + lx, hip[1] - 12)
    hb = (dc[0] + 3, dc[1] + 1)
    cv.shape(cv.limb([shb, lerp2(shb, hb, 0.5), hb], [1.9, 1.8, 1.5]), CB, z=-10, sd=0.9)
    cv.shape(cv.ellipse(hb, 1.1, 1.0), V['skin'], z=-9.9, sd=0.4, ol=0.8)
    # ---- kam postu: aşağı genişler; yaka, kızıl şeritler, göğüste kuzgu ve çıngıraklar
    dress = V['mask'] == 'face'
    if dress:   # erlik kızı: dar bel, yere doğru açılan uzun yırtık etek
        hem = yk.ragged((10.5, hip[1] + 7.0), (-11.0, hip[1] + 7.5), 6, 3.2, seed=4, side=-1.0)
        coat = cv.blob([(-3.6 + lx, hip[1] - 14.5), (4.6 + lx, hip[1] - 14.5), (3.6 + lx * 0.6, hip[1] - 7.5), (6.5, hip[1] - 1.0),
                        (10.5 + math.sin(ph) * 0.6, hip[1] + 7.0, 0.0)] + hem + [(-11.0 + math.sin(ph + 1) * 0.6, hip[1] + 7.5, 0.0), (-5.6, hip[1] - 1.0), (-3.0 + lx * 0.6, hip[1] - 7.5)])
    else:
        coat = cv.blob([(-4.8 + lx, hip[1] - 14.5), (5.6 + lx, hip[1] - 14.5), (7.0 + lx * 0.5, hip[1] - 6), (9.8, hip[1] + 5.2, 0.0),
                        (-9.8, hip[1] + 5.2, 0.0), (-6.8 + lx * 0.5, hip[1] - 6)])
    det = []
    det += cv.fold([(1.0 + lx, hip[1] - 10), (2.0 + lx * 0.6, hip[1] - 3), (3.6, hip[1] + 4.8)], 0.9, 1.3, -1)
    det += cv.fold([(-3.0 + lx, hip[1] - 9), (-4.5 + lx * 0.5, hip[1] - 2), (-6.0, hip[1] + 4.8)], 0.9, 1.3, 1)
    if dress:
        det += cv.fold([(0.0, hip[1] - 4), (-1.0, hip[1] + 2), (-2.0, hip[1] + 7.5)], 0.8, 1.2, 1)
        det.append(('stroke', [(-3.4 + lx * 0.6, hip[1] - 7.6), (3.8 + lx * 0.6, hip[1] - 7.6)], 1.6, V['stripe'], (0.05, 0.05)))
        det.append(('deep', cv.blob([(-11.0, hip[1] + 7.5), (-6.0, hip[1] + 1.0), (-3.0, hip[1] + 8.0)])))
    else:
        det.append(('stroke', [(-8.6, hip[1] + 3.0), (0.0, hip[1] + 3.3), (8.6, hip[1] + 3.0)], 1.8, V['stripe'], (0.05, 0.05)))
        det.append(('stroke', [(-3.8 + lx, hip[1] - 14.0), (0.6 + lx * 0.8, hip[1] - 4.0)], 1.5, V['stripe'], (0.05, 0.3)))
    cv.shape(coat, C, z=0, sd=2.2, hi=0.45, details=det, hatch=0.35, bounce=0.3)
    # göğüs: kuzgu (kam aynası) + çıngıraklar
    mc = (1.0 + lx * 0.8, hip[1] - 9.5)
    cv.shape(cv.ellipse(mc, 1.9, 1.9), V['mirror'], z=12.6, sd=0.6, hi=0.4, ol=0.8, details=[('col', cv.ellipse((mc[0] + 0.3, mc[1] + 0.3), 1.0, 1.0), V['mirror'].shadow)])
    if 'mirror' not in V['extra']:
        yk.glow_soft(cv, mc, 1.6, V['curse_glow'], z=12.7, alpha=0.2 + 0.3 * cast)
    for i in range(0 if dress else 5):
        x = -3.5 + lx * 0.8 + i * 1.9
        y = hip[1] - 7.0 + abs(i - 2) * 0.3
        e = (x + math.sin(ph + i) * 0.4 - lean * 1.2, y + 2.6)
        cv.stroke([(x, y), e], 0.9, z=12.3, col=FR.shadow)
        cv.shape(cv.blob([(e[0] - 0.6, e[1]), (e[0] + 0.6, e[1]), (e[0] + 0.35, e[1] + 1.8), (e[0] - 0.35, e[1] + 1.8)]), IRON, z=12.4 + i * 0.01, sd=0.3, ol=0.6)
    # etek saçakları: deri püsküller, kızıl şeritler, demir çıngıraklar
    for i in range(0 if dress else 15):
        x = -9.3 + i * 1.33
        y = hip[1] + 4.4
        sway = math.sin(ph + i * 0.7) * 0.7 - lean * 2.8
        Ln = (4.6 if i % 3 else 6.4) + (i % 2) * 0.6
        col = Ink(V['stripe']) if i % 4 == 0 else FR
        pts = [(x, y), (x + sway * 0.5, y + Ln * 0.5), (x + sway, y + Ln)]
        cv.shape(ik.taper_path([cv.W(q) for q in pts], cv.u(0.85), prof=lambda u: 1.0 if u < 0.8 else max(0.3, 1.0 - (u - 0.8) * 3.5)),
                 col, z=8 + (i % 2) * 0.3, sd=0.3, ol=0.6)
        if i % 5 == 2:
            q = (x + sway * 0.8, y + Ln * 0.75)
            cv.shape(cv.blob([(q[0] - 0.6, q[1]), (q[0] + 0.6, q[1]), (q[0] + 0.35, q[1] + 1.8), (q[0] - 0.35, q[1] + 1.8)]), IRON, z=9, sd=0.3, ol=0.6)
    # ---- baş
    if V['mask'] != 'face':
        cv.shape(cv.ellipse((hd[0] - 1.5, hd[1] + 0.5), 3.8, 4.2), CB, z=3, sd=1.2)
    crown = V['crown']
    if crown in ('owl', 'eagle'):
        F = V['feather']
        for k in range(6):
            a = -2.65 + k * 0.25 + math.sin(ph + k) * 0.05 - lean * 0.2
            b = (hd[0] - 1.5, hd[1] - 3.0)
            ln = 10.0 if crown == 'owl' else 11.5
            tip = (b[0] + math.cos(a) * ln, b[1] + math.sin(a) * ln)
            perp = (-math.sin(a) * 1.5, math.cos(a) * 1.5)
            mid = lerp2(b, tip, 0.55)
            fdet = [('ink', [b, lerp2(b, tip, 0.9)], 0.8, (0.1, 0.5))]
            for j in range(3):
                q = lerp2(b, tip, 0.35 + j * 0.2)
                fdet.append(('stroke', [(q[0] - perp[0], q[1] - perp[1]), (q[0] + perp[0], q[1] + perp[1])], 1.0, V['feather_bar'], (0.2, 0.2)))
            cv.shape(cv.blob([b, (mid[0] + perp[0], mid[1] + perp[1]), (tip[0], tip[1], 0.0), (mid[0] - perp[0], mid[1] - perp[1])]), F, z=1 + k * 0.2,
                     sd=0.6, hi=0.3, details=fdet, ol=0.8)
    if crown == 'crystal':
        F = V['feather']
        for k, (a, ln) in enumerate(((-2.4, 6.0), (-2.0, 8.5), (-1.6, 7.0), (-1.2, 5.0))):
            b = (hd[0] - 0.5 + k * 0.6, hd[1] - 3.2)
            tip = (b[0] + math.cos(a) * ln, b[1] + math.sin(a) * ln)
            w = 1.3
            nx, ny = -math.sin(a) * w, math.cos(a) * w
            cv.shape(cv.blob([(b[0] + nx, b[1] + ny, 0.0), (lerp2(b, tip, 0.7)[0] + nx, lerp2(b, tip, 0.7)[1] + ny, 0.0), (tip[0], tip[1], 0.0),
                              (lerp2(b, tip, 0.7)[0] - nx, lerp2(b, tip, 0.7)[1] - ny, 0.0), (b[0] - nx, b[1] - ny, 0.0)]), F, z=16 + k * 0.1, sd=0.9, hi=0.5,
                     glow=(0.04, 0.3, 0.2), details=[('stroke', [lerp2(b, tip, 0.2), lerp2(b, tip, 0.8)], 0.9, (1, 1, 1), (0.2, 0.6))])
            yk.glow_soft(cv, lerp2(b, tip, 0.6), 2.4, V['curse_glow'], z=16.5, alpha=0.3)
    if crown == 'owl':
        for (bx, a0, L_, m, zz) in ((-0.5, -1.85, 10, Ink('#a89a82', '#5a4e44', '#cfc2aa'), 4), (1.6, -1.4, 11, V['horn'], 16)):
            pts = [(hd[0] + bx, hd[1] - 3.5)]
            x, y = pts[0]
            for i in range(3):
                a = a0 - 0.22 * i
                x += math.cos(a) * L_ / 3
                y += math.sin(a) * L_ / 3
                pts.append((x, y))
            tine_b = pts[1]
            tine = (tine_b[0] + math.cos(a0 + 0.9) * 3.0, tine_b[1] + math.sin(a0 + 0.9) * 3.0)
            tine2 = (pts[2][0] + math.cos(a0 + 0.7) * 2.6, pts[2][1] + math.sin(a0 + 0.7) * 2.6)
            path = ik.union(ik.taper_path([cv.W(q) for q in pts], cv.u(2.0), prof=lambda u: max(0.2, 1 - 0.7 * u)),
                            ik.taper_path([cv.W(tine_b), cv.W(tine)], cv.u(1.2), (0.0, 0.9)), ik.taper_path([cv.W(pts[2]), cv.W(tine2)], cv.u(1.0), (0.0, 0.9)))
            cv.shape(path, m, z=zz, sd=0.7, hi=0.3, ol=0.85)
    if crown == 'horns':
        for (bx, m, zz, s) in ((-0.8, Ink(V['horn'].shadow, V['horn'].deep, V['horn'].base), 4, 0.85), (1.6, V['horn'], 16, 1.0)):
            b = (hd[0] + bx, hd[1] - 3.4)
            pts = [b, (b[0] - 0.6 * s, b[1] - 2.6 * s), (b[0] - 2.4 * s, b[1] - 4.4 * s), (b[0] - 4.6 * s, b[1] - 4.6 * s)]
            cv.shape(ik.taper_path([cv.W(q) for q in pts], cv.u(1.8 * s), prof=lambda u: max(0.08, 1 - 0.95 * u)), m, z=zz, sd=0.6, hi=0.35, ol=0.85)
    # alın bandı
    if V['mask'] not in ('face',):
        cv.shape(cv.capsule((hd[0] - 2.4, hd[1] - 3.2), (hd[0] + 4.4, hd[1] - 3.4), 1.05, 1.05), Ink(V['stripe']), z=18, sd=0.5, hi=0.3)
        for i in range(3):
            cv.shape(cv.ellipse((hd[0] - 1.0 + i * 2.2, hd[1] - 3.4), 0.55, 0.55), V['mirror'], z=18.5, sd=0.2, hi=0.2, ol=0.6)
    eye_on = cast > 0.3 or flare > 0
    mk = V['mask']
    if mk == 'bone':
        mask = cv.blob([(hd[0] - 1.6, hd[1] - 3.2), (hd[0] + 3.8, hd[1] - 3.6), (hd[0] + 5.2, hd[1] - 0.4), (hd[0] + 4.4, hd[1] + 3.0),
                        (hd[0] + 1.8, hd[1] + 4.8, 0.0), (hd[0] - 0.6, hd[1] + 3.0), (hd[0] - 1.8, hd[1] + 0.2)])
        mdet = [('stroke', [(hd[0] + 0.6, hd[1] + 0.5), (hd[0] + 0.4, hd[1] + 2.6)], 0.9, V['stripe'], (0.1, 0.6)),
                ('stroke', [(hd[0] + 3.2, hd[1] + 0.5), (hd[0] + 3.4, hd[1] + 2.6)], 0.9, V['stripe'], (0.1, 0.6)),
                ('ink', [(hd[0] + 0.6, hd[1] + 3.2), (hd[0] + 1.9, hd[1] + 3.5), (hd[0] + 3.2, hd[1] + 3.0)], 1.0, (0.2, 0.2)),
                ('ink', [(hd[0] + 1.9, hd[1] - 0.6), (hd[0] + 2.3, hd[1] + 1.2)], 0.8)]
        cv.shape(mask, BONE, z=14, sd=1.0, hi=0.35, details=mdet)
        eyes = [(hd[0] + 0.5, hd[1] - 0.9), (hd[0] + 3.1, hd[1] - 0.9)]
        for q in eyes:
            cv.fill(cv.ellipse(q, 0.95, 1.15), INK, z=20)
            yk.eye_glow(cv, q, 0.42 * (1.3 if eye_on else 1.0), 0.42 * (1.3 if eye_on else 1.0), 0, V['eye'] if not eye_on else V['curse_hot'],
                        V['eye_glow'] if not eye_on else V['curse_glow'], 21, halo=2.0, halo_a=0.3 + 0.3 * eye_on)
        # gözlerin önüne sarkan saçak (kam başlığı)
        for i in range(5):
            x = hd[0] - 1.0 + i * 1.35
            cv.stroke([(x, hd[1] - 2.4), (x - lean * 0.6, hd[1] - 0.2 + (i % 2) * 0.6)], 0.9, z=22, col=(0.1, 0.08, 0.1), taper=(0.0, 0.7))
    elif mk == 'horse':   # at kafatası maske: uzun burun öne-aşağı
        mask = cv.blob([(hd[0] - 1.8, hd[1] - 3.4), (hd[0] + 3.0, hd[1] - 3.8), (hd[0] + 7.6, hd[1] + 1.0), (hd[0] + 8.0, hd[1] + 3.2, 0.0),
                        (hd[0] + 4.4, hd[1] + 3.6), (hd[0] + 0.6, hd[1] + 3.0), (hd[0] - 1.8, hd[1] + 0.4)])
        mdet = [('deep', cv.ellipse((hd[0] + 6.8, hd[1] + 2.2), 0.6, 0.4)), ('ink', [(hd[0] + 3.0, hd[1] + 3.3), (hd[0] + 7.4, hd[1] + 3.2)], 0.9),
                ('stroke', [(hd[0] + 1.6, hd[1] - 2.8), (hd[0] + 6.8, hd[1] + 1.0)], 1.0, V['stripe'], (0.2, 0.5))]
        cv.shape(mask, BONE, z=14, sd=1.0, hi=0.35, details=mdet)
        q = (hd[0] + 1.6, hd[1] - 0.8)
        cv.fill(cv.ellipse(q, 1.1, 1.0), INK, z=20)
        yk.eye_glow(cv, q, 0.5 * (1.3 if eye_on else 1.0), 0.45, 0, V['eye'], V['eye_glow'], 21, halo=2.2, halo_a=0.3 + 0.3 * eye_on)
    elif mk == 'blind':   # kör kam: yüz + gözleri saran bez, altından ışık sızar
        face = cv.ellipse((hd[0] + 1.8, hd[1] + 0.4), 3.2, 4.0)
        cv.shape(face, V['skin'], z=14, sd=1.0, hi=0.3, details=[('ink', [(hd[0] + 1.2, hd[1] + 2.8), (hd[0] + 2.6, hd[1] + 2.6)], 0.9)])
        band = cv.blob([(hd[0] - 1.6, hd[1] - 2.0), (hd[0] + 5.2, hd[1] - 1.6), (hd[0] + 5.0, hd[1] + 0.4), (hd[0] - 1.6, hd[1] + 0.2)])
        cv.shape(band, FR, z=15, sd=0.6, hi=0.3, details=[('ink', [(hd[0] - 1.0, hd[1] - 0.8), (hd[0] + 4.6, hd[1] - 0.6)], 0.7)])
        cv.shape(ik.taper_path([cv.W((hd[0] - 1.4, hd[1] - 0.8)), cv.W((hd[0] - 4.0, hd[1] + 1.8 + math.sin(ph) * 0.5)), cv.W((hd[0] - 5.0, hd[1] + 5.0))], cv.u(1.2), (0.1, 0.7)),
                 FR, z=2.5, sd=0.4, ol=0.7)
        for q in ((hd[0] + 1.0, hd[1] + 0.6), (hd[0] + 3.6, hd[1] + 0.7)):
            cv.stroke([q, (q[0] + 0.1, q[1] + 2.0)], 0.8, z=15.5, col=V['curse'], taper=(0.1, 0.9), glow=V['curse_glow'])
            yk.glow_soft(cv, q, 1.4 + flare, V['curse_glow'], z=15.6, alpha=0.4 + 0.3 * eye_on)
        for i in range(5):   # kır sakal
            x = hd[0] + 0.4 + i * 1.0
            cv.stroke([(x, hd[1] + 3.4), (x - lean, hd[1] + 6.0 + (i % 2))], 0.9, z=15.7, col=(0.75, 0.75, 0.72), taper=(0.0, 0.8))
    else:                 # erlik kızı: solgun güzel yüz
        face = cv.blob([(hd[0] - 1.2, hd[1] - 2.8), (hd[0] + 3.0, hd[1] - 3.4), (hd[0] + 4.6, hd[1] - 0.8), (hd[0] + 4.2, hd[1] + 2.0),
                        (hd[0] + 2.6, hd[1] + 4.2, 0.0), (hd[0] + 0.4, hd[1] + 3.4), (hd[0] - 1.4, hd[1] + 0.6)])
        fdet = [('col', cv.blob([(hd[0] + 2.1, hd[1] + 2.4), (hd[0] + 3.5, hd[1] + 2.2), (hd[0] + 2.8, hd[1] + 2.9)]), (0.78, 0.08, 0.14)),
                ('ink', [(hd[0] + 3.2, hd[1] - 0.4), (hd[0] + 3.8, hd[1] + 0.9), (hd[0] + 3.4, hd[1] + 1.2)], 0.7)]
        cv.shape(face, V['skin'], z=14, sd=1.0, hi=0.3, details=fdet)
        for q in ((hd[0] + 1.0, hd[1] - 0.6), (hd[0] + 3.4, hd[1] - 0.8)):
            cv.fill(cv.blob([(q[0] - 0.9, q[1] + 0.1), (q[0], q[1] - 0.5), (q[0] + 0.9, q[1] - 0.2, 0.0), (q[0], q[1] + 0.4)]), INK, z=20)
            yk.eye_glow(cv, (q[0] + 0.1, q[1] - 0.05), 0.4, 0.3, -0.2, V['eye'], V['eye_glow'], 21, halo=2.2, halo_a=0.3 + 0.3 * eye_on)
        cv.stroke([(hd[0] - 0.2, hd[1] - 1.6), (hd[0] + 1.6, hd[1] - 1.9)], 0.8, z=21.5, col=INK, taper=(0.2, 0.8))
        # perçem: yüzün üstüne düşen saç
        fr = cv.blob([(hd[0] - 2.0, hd[1] + 1.0), (hd[0] - 1.8, hd[1] - 3.6), (hd[0] + 1.4, hd[1] - 5.2), (hd[0] + 4.6, hd[1] - 3.8),
                      (hd[0] + 4.8, hd[1] - 2.0, 0.0), (hd[0] + 2.0, hd[1] - 3.0), (hd[0] - 0.2, hd[1] - 1.6), (hd[0] - 0.6, hd[1] + 3.0, 0.0)])
        cv.shape(fr, V['hair'], z=22, sd=0.8, hi=0.5, details=[('stroke', [(hd[0] + 0.0, hd[1] - 4.2), (hd[0] + 2.8, hd[1] - 4.0)], 0.9, V['hair'].hi, (0.3, 0.5))])
        # gerdanlık: kemik boncuklar
        for i in range(5):
            q = (hd[0] - 0.8 + i * 1.1, hd[1] + 5.4 + abs(i - 2) * -0.25)
            cv.shape(cv.ellipse(q, 0.5, 0.6), BONE, z=13, sd=0.2, ol=0.6)
    # ---- ön kol: lanet eli
    ar = p.get('ar', (0.6, 0.8))
    shf = (hip[0] + 3.5 + lx, hip[1] - 12)
    e, h = fk_arm(shf, ar[0], ar[1], 5.5, 5.5)
    cuff = lerp2(e, h, 0.6)
    sleeve = cv.limb([shf, e, cuff], [2.0, 1.8, 2.1])
    cv.shape(sleeve, C, z=26, sd=1.0, hi=0.35, details=[('stroke', [lerp2(e, cuff, 0.6), cuff], 1.6, V['stripe'], (0.0, 0.0))])
    for k in (-1, 0, 1):
        q = (cuff[0] + k * 0.8, cuff[1])
        cv.shape(ik.taper_path([cv.W(q), cv.W((q[0] + k * 0.3 + math.sin(ph + k) * 0.3, q[1] + 3.2))], cv.u(0.9), (0.0, 0.7)), FR, z=26.5 + k * 0.01, sd=0.3, ol=0.6)
    a = ar[0] + ar[1]
    cv.shape(cv.capsule(cuff, h, 0.85, 0.9), V['skin'], z=27, sd=0.4, ol=0.8)
    for k in (-0.55, 0.0, 0.55):
        tip = (h[0] + math.sin(a + k) * 2.6, h[1] + math.cos(a + k) * 2.6)
        cv.shape(ik.taper_path([cv.W(h), cv.W(lerp2(h, tip, 0.6)), cv.W(tip)], cv.u(0.75), (0.0, 0.8)), V['skin'], z=27.5, sd=0.3, ol=0.7)
    # lanet küresi: parlak çekirdek, dönen mürekkep sarmal, uyarıda halka + kıvılcımlar
    gc = (h[0] + math.sin(a) * 2.6, h[1] + math.cos(a) * 2.6)
    r = 1.0 + cast * 2.2 + p.get('flick', 0.0)
    yk.glow_soft(cv, gc, r * 2.6 + flare * 3, V['curse_glow'], z=29.5, blur=0.55, alpha=0.55 + 0.3 * flare)
    cv.fill(cv.ellipse(gc, r, r), V['curse'], z=30, glow=V['curse_glow'])
    cv.fill(cv.ellipse((gc[0] - r * 0.15, gc[1] - r * 0.15), r * 0.55, r * 0.55), V['curse_hot'], z=30.1, glow=V['curse_hot'])
    if r > 1.6:
        for k in range(2):   # sarmal
            a0 = ph * 1.5 + k * math.pi
            pts = [(gc[0] + math.cos(a0 + u * 3.5) * r * (0.4 + 0.8 * u), gc[1] + math.sin(a0 + u * 3.5) * r * (0.4 + 0.8 * u)) for u in np.linspace(0, 1, 6)]
            cv.stroke(pts, 1.1, z=30.2, col=INK, taper=(0.6, 0.2), alpha=0.85)
    if cast > 0.5 or flare > 0:
        rr = r + 2.2 + flare * 1.0
        ring = [(gc[0] + math.cos(t_) * rr, gc[1] + math.sin(t_) * rr * 0.9) for t_ in np.linspace(ph, ph + 4.6, 9)]
        cv.stroke(ring, 1.3, z=31, col=V['curse'], taper=(0.6, 0.1), glow=V['curse_glow'])
        yk.sparks(cv, gc, 6, r + 1.0, r + 4.0, V['curse_hot'], 31.1, seed=int(ph * 7) + 1, w=1.1, glow=V['curse_glow'])
    return {'hand': gc}


def _pose(anim, i):
    n, fn, loop, arm = ANIMS[anim]
    p = dict(fn(i / n))
    if anim == 'cast' and i == 0:
        p['flare'] = 1.0
    return p


SHADE = dict(outer=0.5, rim=0.7, rim_col=(0.7, 0.78, 1.0), rim_dir=(0.6, -0.8), rim_w=1.3, form=(4.0, (0.76, 0.74, 0.88)))


def render_frame(anim, i, var='arcura', ss=3):
    V = VARIANTS[var]
    p = _pose(anim, i)
    cv = yk.occlude_glow(ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss))
    info = draw(cv, p, V)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
