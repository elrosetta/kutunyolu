"""Kara Kam (kimlik arcura) ve biyom çeşitlemeleri — stil v2 "mürekkep-cel". v1: creatures.draw_kam.

Hücre dünya 76x72 (doku 304x288), ayak (36, 66), doku 4. 'hand' çapası (lanet küresi / yay kabzası / ışın çıkışı) her
karede döner; büyü, ok ve büyü bağı (ışın) oradan çıkar.

Tasarım: Erlik'e kul olmuş kara kam. Sibirya-Türk kam giysisi (manyak): diz altına inen deri kaftan, eteğinde ve
kollarında uzun deri saçaklar ve kızıl şeritler, göğsünde demir çıngıraklar ve tunç kuzgu (kam aynası); başında
baykuş tüyü yelpazesi ve geyik boynuzlu taç, yüzünde kemik maske ve gözlerin önüne sarkan saçak. Arka elinde
boyalı kam davulu (tüngür: Hayat Ağacı, Ay ve Güneş), ön elinde mor yanan lanet.

v29 tam gövde animasyonu (docs/TASARIM.md "v29: yer yaratıklarının tam gövde animasyonu"): bütün figür dönüşümü
(x / y / roll / ezilme), kalça çevresinde gövde eğimi (pitch) ve sönme (tsx / tsy: ölümde post söner), boyun dibinde
dönen baş grubu (hr / hd), AYAK HEDEFLİ bacak IK'sı (basan çizme kaymaz), ön kol açılarla, arka kol (davul eli) el
hedefli IK; kaftan etek ucu ayrı yaşar (hem: geride sürüklenme, flr: kabarma, hl: kalkma) ve yere değince yığılır;
saçaklar, çıngıraklar, tüyler, saç ikincil dalga (fr / ph). Yay (okçu), büyü bağı ışını (charmer), duman (ışınlanma),
rün halkası ve "!!" levitasyonu, ölümde çıkan ruh telleri.

Bir sayfa üç yapay zekâyı taşır (DURUM): illusionist (arcura: büyü + hayalet / ışınlanma), archer (kurgan_okcusu: ruh
yayı + geri takla), charmer (erlik_kizi: büyü bağı + iki güdümlü küre); isilti_bocegi (kamikaze) başka sayfa,
yalnızca çizilebilir kalır.

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
from rig import fk_arm, lerp2
import yaratik_govde as yg
import yaratik_ink_kit as yk
from yaratik_govde import Seq

TEX = 4.0
CELL = (304, 288)       # dünya 76 x 72
FEET = (144, 264)       # dünya (36, 66)

IRON = Ink('#6a6c7c', '#30303e', '#b0b4c8', '#1a1a24', kind='metal', name='demir')
BRONZE = Ink('#c08a40', '#62381c', '#f6d890', '#341e0e', kind='metal', name='tunç')
BONE = Ink('#e8dfc6', '#8c8072', '#fffbea', '#564a44', name='kemik')
WOOD = Ink('#8a5a34', '#40221a', '#b88654', name='davul kasnağı')
SMOKE = Ink('#8a7ca4', '#52466c', '#c6bade', name='duman')
SPIRIT = Ink('#b8a8d8', '#6a5a90', '#efe6ff', name='ruh')


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
        yk.glow_soft(cv, (dc[0] + 0.8, dc[1]), 3.0 + 1.5 * max(0.0, dr - 0.5), V['curse_glow'], z=z + 0.1, blur=0.6, alpha=0.25 + 0.3 * dr)
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
    for i in range(3):   # asılı çıngıraklar: dünyada aşağı sarkar (davul dönse de)
        a = 1.3 + i * 0.35
        q = P(math.cos(a) * 4.9, math.sin(a) * 6.7)
        e = (q[0] + math.sin(ph + i) * 0.6, q[1] + 2.6)
        cv.stroke([q, e], 0.9, z=z + 0.6, col=(0.3, 0.26, 0.24))
        cv.shape(cv.blob([(e[0] - 0.7, e[1]), (e[0] + 0.7, e[1]), (e[0] + 0.4, e[1] + 2.2), (e[0] - 0.4, e[1] + 2.2)]), IRON, z=z + 0.7, sd=0.3, hi=0.2, ol=0.6)
    if dr > 0.5:   # vuruş: davul titrer (mürekkep yayları)
        for k in range(2):
            r_ = 7.8 + k * 1.6
            cv.stroke([P(r_ * 0.6 * math.cos(a), r_ * math.sin(a)) for a in np.linspace(-0.9, 0.9, 5)], 1.0, z=z + 0.8, col=INK, taper=(0.5, 0.5))


# ====================================================================== iskelet
HIP = (0.0, -12.0)            # kalça (figür dönüşümünün ve gövde eğiminin merkezi)
GROUND = -0.5                 # çizme noktası (taban 0,5 aşağıda yere değer)
GW = -0.2                     # etek / saçak için yer çizgisi (dünya)
L_TH, L_SH = 5.6, 6.0         # uyluk / baldır

# dinlenme pozu. lf/lb: yakın/uzak çizme hedefi (x, yerden yükseklik, burun kalkışı rad); fk: 1 = hedef figür yerelinde (havada)
REST = dict(x=0.0, y=0.0, roll=0.0, sq=0.0, pitch=0.0, tsx=1.0, tsy=1.0, fk=0.0, lg=1.0,
            lf=(0.6, 0.0, 0.0), lb=(-1.8, 0.0, 0.0),
            hd=(0.0, 0.0), hr=0.0,
            ar=(0.6, 0.8), fing=0.0,
            dk=(0.0, 0.0), drot=0.0, drum=0.0, dwb=0.0, dwp=(-10.0, -7.0), bh=(4.0, -1.0), bhw=0.0,
            cast=0.0, flare=0.0, flick=0.0, orb=1.0, eye=0.0, eyek=1.0, blink=0.0,
            hem=0.0, hl=0.0, flr=0.0, fr=0.0, feath=0.0, hair=0.0, ph=0.0,
            bow=0.0, draw=0.0, arrow=0.0, snap=0.0, btilt=-0.08,
            beam=0.0, smoke=0.0, wisp=0.0, rune=0.0, daze=0.0)


def _smooth(a, b, v):
    u = yg.clamp((v - a) / (b - a), 0.0, 1.0)
    return u * u * (3 - 2 * u)


def draw(cv, p, V):
    yg.bake_xf(cv)
    q0 = dict(REST)
    q0.update(p)
    p = q0
    ph = p['ph']
    cast, flare = p['cast'], p['flare']
    fr = p['fr']
    C, CB, FR = V['coat'], V['coat_b'], V['fringe']
    sq = p['sq']
    sqx, sqy = 1.0 + 0.08 * sq, 1.0 - 0.1 * sq
    roll, X, Y = p['roll'], p['x'], p['y']
    pit, tsx, tsy = p['pitch'], p['tsx'], p['tsy']
    hip = HIP

    # ---- dönüşümler: yerel (dinlenme) -> ezilme (ayak noktası çevresinde) -> figür (kalça çevresinde roll + öteleme)
    def to_world(pt):
        r = yg.rot_about((pt[0] * sqx, pt[1] * sqy), hip, roll)
        return (r[0] + X, r[1] + Y)

    def to_local(w):
        r = yg.rot_about((w[0] - X, w[1] - Y), hip, -roll)
        return (r[0] / sqx, r[1] / sqy)

    def T(pt):   # gövde yereli -> figür yereli (kalça çevresinde sönme + eğim)
        d = yg.rot(((pt[0] - hip[0]) * tsx, (pt[1] - hip[1]) * tsy), pit)
        return (hip[0] + d[0], hip[1] + d[1])

    def G(pt, spread=0.0):   # yer kırpması: yere değen etek / saçak noktası yere yayılır
        w = to_world(pt)
        if w[1] > GW:
            return to_local((w[0] + spread * (w[1] - GW), GW))
        return pt

    yg.xf_push(cv, hip, roll, X, Y)
    cv.push(lambda q_: (q_[0] * sqx, q_[1] * sqy))
    lx = 0.0

    # ---- kaftan eşlemesi: üst kısım gövdeyle eğilir, etek ucu kendi yaşar (sürüklenme / kabarma / kalkma), yere yığılır
    hy0, hy1 = hip[1] - 14.5, hip[1] + 5.2
    hemdx = -p['hem'] * 3.0
    flr, hl = p['flr'], p['hl']

    def M(pt):
        v = yg.clamp((pt[1] - hy0) / (hy1 - hy0), 0.0, 1.3)
        w = _smooth(0.25, 1.0, v)
        a = T(pt)
        b = (pt[0] * (1.0 + 0.3 * flr) + hemdx * v + math.sin(ph + pt[0] * 0.55) * 0.7 * flr * v, pt[1] - (hl + 2.6 * flr) * v * v)
        o = lerp2(a, b, w)
        return G(o, 0.8 if pt[0] > 0 else -0.8)

    def Mp(pt):
        return M(pt) + tuple(pt[2:])

    # ---- erlik kızı: arkada dalgalanan uzun saç (baş grubunda; aşağıda)
    # ---- bacaklar: keçe çizme, uçları kalkık; ayak hedefli IK (basan çizme kaymaz)
    def F(t):
        w = (t[0], GROUND - t[1])
        loc = to_local(w)
        if p['fk']:
            loc = lerp2(loc, (t[0], GROUND - t[1]), p['fk'])
        return loc

    for side, key in ((-1, 'lb'), (1, 'lf')) if p['lg'] > 0.5 else ():   # lg 0: boş kaftan (ölüm yığını)
        t = p[key]
        z = -4 if side < 0 else -1
        base = (hip[0] + side * 1.4, hip[1])
        k, f = yg.ik2(base, F(t), L_TH, L_SH, -1)
        bm = V['boot'] if side > 0 else Ink(V['boot'].shadow, V['boot'].deep, V['boot'].base)
        ta = -t[2]
        ca, sa = math.cos(ta), math.sin(ta)
        R = lambda x_, y_, *r: (f[0] + x_ * ca - y_ * sa, f[1] + x_ * sa + y_ * ca) + r
        boot = cv.blob([R(-1.6, -1.2), R(1.8, -0.9), R(3.4, -1.4, 0.0), R(3.0, 0.4), R(-1.6, 0.5)])
        km = lerp2(k, f, 0.55)
        det = [('stroke', [km, (km[0] + 1.4, km[1])], 1.2, V['stripe'], (0.1, 0.1))]
        if side > 0:   # yakın çizme saçakların arasından görünür (adım okunur); baldır kaftanın arkasında kalır
            cv.shape(cv.limb([base, k, f], [2.0, 1.7, 1.6]), bm, z=z, sd=1.0, hi=0.3)
            cv.shape(ik.union(cv.limb([lerp2(k, f, 0.5), f], [1.65, 1.6]), boot), bm, z=8.15, sd=1.0, hi=0.3, details=det)
        else:
            cv.shape(ik.union(cv.limb([base, k, f], [2.0, 1.7, 1.6]), boot), bm, z=z, sd=1.0, hi=0.0, details=det)

    # ---- davul (arka elde, gövdenin arkasında) + arka kol (el hedefli IK)
    dr = p['drum']
    dkx, dky = p['dk']
    dc = T((hip[0] - 9.5 + dkx, hip[1] - 12 + dky))
    drot = 0.25 + p['drot'] + pit
    if p['dwb'] > 0:
        dc = lerp2(dc, to_local(p['dwp']), p['dwb'])
    _drum(cv, dc, drot, V, -16, ph, dr)
    shb = T((hip[0] - 3, hip[1] - 12))
    grip = (dc[0] + 3.0 * math.cos(drot - 0.25) - 1.0 * math.sin(drot - 0.25), dc[1] + 3.0 * math.sin(drot - 0.25) + 1.0 * math.cos(drot - 0.25))
    bhw = yg.clamp(p['bhw'], 0.0, 1.0)
    tgt = lerp2(grip, (shb[0] + p['bh'][0], shb[1] + p['bh'][1]), bhw)
    el, hb = yg.ik2(shb, tgt, 3.5, 3.5, -1)
    cv.shape(cv.limb([shb, el, hb], [1.9, 1.8, 1.5]), CB, z=-10, sd=0.9)
    cv.shape(cv.ellipse(hb, 1.1, 1.0), V['skin'], z=-9.9 if bhw < 0.5 else 25.5, sd=0.4, ol=0.8)
    if bhw > 0.5 and 'mirror' not in V['extra']:   # davul sırtta kayışla asılı
        cv.stroke([lerp2(dc, grip, 0.6), T((hip[0] - 1.0, hip[1] - 13.5))], 1.0, z=-9.8, col=(0.25, 0.16, 0.12))

    # ---- kam postu: aşağı genişler; yaka, kızıl şeritler, göğüste kuzgu ve çıngıraklar
    dress = V['mask'] == 'face'
    if dress:   # erlik kızı: dar bel, yere doğru açılan uzun yırtık etek
        hem = yk.ragged((10.5, hip[1] + 7.0), (-11.0, hip[1] + 7.5), 6, 3.2, seed=4, side=-1.0)
        cpts = [(-3.6 + lx, hip[1] - 14.5), (4.6 + lx, hip[1] - 14.5), (3.6 + lx * 0.6, hip[1] - 7.5), (6.5, hip[1] - 1.0),
                (10.5 + math.sin(ph) * 0.6, hip[1] + 7.0, 0.0)] + hem + [(-11.0 + math.sin(ph + 1) * 0.6, hip[1] + 7.5, 0.0), (-5.6, hip[1] - 1.0), (-3.0 + lx * 0.6, hip[1] - 7.5)]
    else:
        cpts = [(-4.8 + lx, hip[1] - 14.5), (5.6 + lx, hip[1] - 14.5), (7.0 + lx * 0.5, hip[1] - 6), (8.6, hip[1] + 1.0), (9.8, hip[1] + 5.2, 0.0),
                (0.0, hip[1] + 5.4), (-9.8, hip[1] + 5.2, 0.0), (-8.4, hip[1] + 1.0), (-6.8 + lx * 0.5, hip[1] - 6)]
    coat = cv.blob([Mp(q) for q in cpts])
    Ml = lambda pts: [M(q) for q in pts]
    det = []
    det += cv.fold(Ml([(1.0 + lx, hip[1] - 10), (2.0 + lx * 0.6, hip[1] - 3), (3.6, hip[1] + 4.8)]), 0.9, 1.3, -1)
    det += cv.fold(Ml([(-3.0 + lx, hip[1] - 9), (-4.5 + lx * 0.5, hip[1] - 2), (-6.0, hip[1] + 4.8)]), 0.9, 1.3, 1)
    if flr > 0.3:   # kabaran etekte ek kıvrım
        det += cv.fold(Ml([(5.0, hip[1] - 3), (6.6, hip[1] + 1.5), (7.8, hip[1] + 5.0)]), 0.7, 1.1, -1)
    if dress:
        det += cv.fold(Ml([(0.0, hip[1] - 4), (-1.0, hip[1] + 2), (-2.0, hip[1] + 7.5)]), 0.8, 1.2, 1)
        det.append(('stroke', Ml([(-3.4 + lx * 0.6, hip[1] - 7.6), (3.8 + lx * 0.6, hip[1] - 7.6)]), 1.6, V['stripe'], (0.05, 0.05)))
        det.append(('deep', cv.blob([M((-11.0, hip[1] + 7.5)), M((-6.0, hip[1] + 1.0)), M((-3.0, hip[1] + 8.0))])))
    else:
        det.append(('stroke', Ml([(-8.6, hip[1] + 3.0), (0.0, hip[1] + 3.3), (8.6, hip[1] + 3.0)]), 1.8, V['stripe'], (0.05, 0.05)))
        det.append(('stroke', Ml([(-3.8 + lx, hip[1] - 14.0), (0.6 + lx * 0.8, hip[1] - 4.0)]), 1.5, V['stripe'], (0.05, 0.3)))
    cv.shape(coat, C, z=0, sd=2.2, hi=0.45, details=det, hatch=0.35, bounce=0.3)
    # etek saçakları: deri püsküller, kızıl şeritler, demir çıngıraklar (dünyada aşağı sarkar, yere değince yayılır)
    for i in range(0 if dress else 15):
        x = -9.3 + i * 1.33
        root = M((x, hip[1] + 4.4))
        sway = math.sin(ph + i * 0.7) * 0.7 - fr * 2.8 + hemdx * 0.35
        Ln = ((4.6 if i % 3 else 6.4) + (i % 2) * 0.6) * (1.0 - 0.1 * flr)
        col = Ink(V['stripe']) if i % 4 == 0 else FR
        dn = yg.rot((0.0, 1.0), -roll)   # yerel çerçevede dünya "aşağı"sı
        side_ = yg.rot((1.0, 0.0), -roll)
        lift = flr * 0.8
        mid = (root[0] + dn[0] * Ln * 0.5 + side_[0] * sway * 0.5, root[1] + dn[1] * Ln * 0.5 + side_[1] * sway * 0.5 - lift * 0.5)
        tip = (root[0] + dn[0] * Ln + side_[0] * sway, root[1] + dn[1] * Ln + side_[1] * sway - lift)
        sp = 1.0 if x > 0 else -1.0
        pts = [root, G(mid, sp), G(tip, sp)]
        cv.shape(ik.taper_path([cv.W(q) for q in pts], cv.u(0.85), prof=lambda u: 1.0 if u < 0.8 else max(0.3, 1.0 - (u - 0.8) * 3.5)),
                 col, z=8 + (i % 2) * 0.3, sd=0.3, ol=0.6)
        if i % 5 == 2:
            q = lerp2(pts[1], pts[2], 0.5)
            cv.shape(cv.blob([(q[0] - 0.6, q[1]), (q[0] + 0.6, q[1]), (q[0] + 0.35, q[1] + 1.8), (q[0] - 0.35, q[1] + 1.8)]), IRON, z=9, sd=0.3, ol=0.6)

    # ---- gövde yereli (eğim): göğüs kuzgusu ve çıngıraklar
    cv.push(T)
    mc = (1.0 + lx * 0.8, hip[1] - 9.5)
    cv.shape(cv.ellipse(mc, 1.9, 1.9), V['mirror'], z=12.6, sd=0.6, hi=0.4, ol=0.8, details=[('col', cv.ellipse((mc[0] + 0.3, mc[1] + 0.3), 1.0, 1.0), V['mirror'].shadow)])
    if 'mirror' not in V['extra']:
        yk.glow_soft(cv, mc, 1.6 + p['rune'], V['curse_glow'], z=12.7, alpha=0.2 + 0.3 * min(1.0, cast + p['eye']))
    hang = -pit - roll
    for i in range(0 if dress else 5):
        x = -3.5 + lx * 0.8 + i * 1.9
        y = hip[1] - 7.0 + abs(i - 2) * 0.3
        a_ = hang + math.sin(ph + i) * 0.15 - fr * 0.4
        e = (x + math.sin(a_) * 2.6, y + math.cos(a_) * 2.6)
        cv.stroke([(x, y), e], 0.9, z=12.3, col=FR.shadow)
        cv.shape(cv.blob([(e[0] - 0.6, e[1]), (e[0] + 0.6, e[1]), (e[0] + 0.35, e[1] + 1.8), (e[0] - 0.35, e[1] + 1.8)]), IRON, z=12.4 + i * 0.01, sd=0.3, ol=0.6)

    # ---- baş grubu: boyun dibinde döner (hr), önden gider (hd)
    nb = (1.5, hip[1] - 15.0)
    yg.xf_push(cv, nb, p['hr'])
    cv.push(lambda q_, o=p['hd']: (q_[0] + o[0], q_[1] + o[1]))
    hd = (2.0, hip[1] - 18.5)
    hflow = -(pit + p['hr'] + roll) * 0.8 + p['hair']
    if V['hair'] is not None:
        hairp = []
        for k in range(5):
            st = [(hd[0] - 1.5 + k * 0.3, hd[1] - 2.5 + k * 0.6)]
            x, y = st[0]
            for j in range(6):
                a = math.pi * (0.62 + 0.04 * k) + math.sin(ph + j * 0.8 + k) * (0.12 + 0.1 * abs(p['hair'])) + hflow * (0.25 + j * 0.1)
                x += math.cos(a) * 3.0
                y += math.sin(a) * 3.0
                st.append((x, y))
            hairp.append(ik.taper_path([cv.W(q) for q in st], cv.u(3.4 - k * 0.3), (0.05, 0.8)))
        cv.shape(ik.union(*hairp), V['hair'], z=-18, sd=1.5, hi=0.6, details=[('stroke', [(hd[0] - 3, hd[1] - 1), (hd[0] - 7, hd[1] + 6)], 1.0, V['hair'].hi, (0.2, 0.6))])
    if V['mask'] != 'face':
        cv.shape(cv.ellipse((hd[0] - 1.5, hd[1] + 0.5), 3.8, 4.2), CB, z=3, sd=1.2)
    crown = V['crown']
    fe = p['feath']
    if crown in ('owl', 'eagle'):
        F_ = V['feather']
        for k in range(6):
            a = -2.65 - 0.12 * fe + k * (0.25 + 0.07 * fe) + math.sin(ph + k) * 0.05 - fr * 0.15
            b = (hd[0] - 1.5, hd[1] - 3.0)
            ln = (10.0 if crown == 'owl' else 11.5) * (1.0 + 0.08 * fe)
            tip = (b[0] + math.cos(a) * ln, b[1] + math.sin(a) * ln)
            perp = (-math.sin(a) * 1.5, math.cos(a) * 1.5)
            mid = lerp2(b, tip, 0.55)
            fdet = [('ink', [b, lerp2(b, tip, 0.9)], 0.8, (0.1, 0.5))]
            for j in range(3):
                q = lerp2(b, tip, 0.35 + j * 0.2)
                fdet.append(('stroke', [(q[0] - perp[0], q[1] - perp[1]), (q[0] + perp[0], q[1] + perp[1])], 1.0, V['feather_bar'], (0.2, 0.2)))
            cv.shape(cv.blob([b, (mid[0] + perp[0], mid[1] + perp[1]), (tip[0], tip[1], 0.0), (mid[0] - perp[0], mid[1] - perp[1])]), F_, z=1 + k * 0.2,
                     sd=0.6, hi=0.3, details=fdet, ol=0.8)
    if crown == 'crystal':
        F_ = V['feather']
        for k, (a, ln) in enumerate(((-2.4, 6.0), (-2.0, 8.5), (-1.6, 7.0), (-1.2, 5.0))):
            b = (hd[0] - 0.5 + k * 0.6, hd[1] - 3.2)
            a += (k - 1.5) * 0.08 * fe
            tip = (b[0] + math.cos(a) * ln, b[1] + math.sin(a) * ln)
            w = 1.3
            nx, ny = -math.sin(a) * w, math.cos(a) * w
            cv.shape(cv.blob([(b[0] + nx, b[1] + ny, 0.0), (lerp2(b, tip, 0.7)[0] + nx, lerp2(b, tip, 0.7)[1] + ny, 0.0), (tip[0], tip[1], 0.0),
                              (lerp2(b, tip, 0.7)[0] - nx, lerp2(b, tip, 0.7)[1] - ny, 0.0), (b[0] - nx, b[1] - ny, 0.0)]), F_, z=16 + k * 0.1, sd=0.9, hi=0.5,
                     glow=(0.04, 0.3, 0.2), details=[('stroke', [lerp2(b, tip, 0.2), lerp2(b, tip, 0.8)], 0.9, (1, 1, 1), (0.2, 0.6))])
            yk.glow_soft(cv, lerp2(b, tip, 0.6), 2.4, V['curse_glow'], z=16.5, alpha=0.3 + 0.3 * fe)
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
    ek = p['eyek']
    eye_on = (cast > 0.3 or flare > 0 or p['eye'] > 0.3) and ek > 0.5
    eb = 1.0 + 0.5 * p['eye']                     # "!!": göz alevi büyür
    bl = p['blink']
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
            if ek > 0.05 and bl < 0.9:
                s_ = 0.42 * (1.3 if eye_on else 1.0) * eb * ek
                yk.eye_glow(cv, q, s_, s_ * (1.0 - 0.7 * bl), 0, V['eye'] if not eye_on else V['curse_hot'],
                            V['eye_glow'] if not eye_on else V['curse_glow'], 21, halo=2.0 + p['eye'], halo_a=(0.3 + 0.3 * eye_on) * ek)
        # gözlerin önüne sarkan saçak (kam başlığı)
        for i in range(5):
            x = hd[0] - 1.0 + i * 1.35
            cv.stroke([(x, hd[1] - 2.4), (x - fr * 0.6 - hflow * 0.5, hd[1] - 0.2 + (i % 2) * 0.6)], 0.9, z=22, col=(0.1, 0.08, 0.1), taper=(0.0, 0.7))
    elif mk == 'horse':   # at kafatası maske: uzun burun öne-aşağı
        mask = cv.blob([(hd[0] - 1.8, hd[1] - 3.4), (hd[0] + 3.0, hd[1] - 3.8), (hd[0] + 7.6, hd[1] + 1.0), (hd[0] + 8.0, hd[1] + 3.2, 0.0),
                        (hd[0] + 4.4, hd[1] + 3.6), (hd[0] + 0.6, hd[1] + 3.0), (hd[0] - 1.8, hd[1] + 0.4)])
        mdet = [('deep', cv.ellipse((hd[0] + 6.8, hd[1] + 2.2), 0.6, 0.4)), ('ink', [(hd[0] + 3.0, hd[1] + 3.3), (hd[0] + 7.4, hd[1] + 3.2)], 0.9),
                ('stroke', [(hd[0] + 1.6, hd[1] - 2.8), (hd[0] + 6.8, hd[1] + 1.0)], 1.0, V['stripe'], (0.2, 0.5))]
        cv.shape(mask, BONE, z=14, sd=1.0, hi=0.35, details=mdet)
        q = (hd[0] + 1.6, hd[1] - 0.8)
        cv.fill(cv.ellipse(q, 1.1, 1.0), INK, z=20)
        if ek > 0.05 and bl < 0.9:
            yk.eye_glow(cv, q, 0.5 * (1.3 if eye_on else 1.0) * eb * ek, 0.45 * eb * ek * (1.0 - 0.7 * bl), 0, V['eye'], V['eye_glow'], 21,
                        halo=2.2 + p['eye'], halo_a=(0.3 + 0.3 * eye_on) * ek)
    elif mk == 'blind':   # kör kam: yüz + gözleri saran bez, altından ışık sızar
        face = cv.ellipse((hd[0] + 1.8, hd[1] + 0.4), 3.2, 4.0)
        cv.shape(face, V['skin'], z=14, sd=1.0, hi=0.3, details=[('ink', [(hd[0] + 1.2, hd[1] + 2.8), (hd[0] + 2.6, hd[1] + 2.6)], 0.9)])
        band = cv.blob([(hd[0] - 1.6, hd[1] - 2.0), (hd[0] + 5.2, hd[1] - 1.6), (hd[0] + 5.0, hd[1] + 0.4), (hd[0] - 1.6, hd[1] + 0.2)])
        cv.shape(band, FR, z=15, sd=0.6, hi=0.3, details=[('ink', [(hd[0] - 1.0, hd[1] - 0.8), (hd[0] + 4.6, hd[1] - 0.6)], 0.7)])
        cv.shape(ik.taper_path([cv.W((hd[0] - 1.4, hd[1] - 0.8)), cv.W((hd[0] - 4.0 - hflow, hd[1] + 1.8 + math.sin(ph) * 0.5)), cv.W((hd[0] - 5.0 - hflow * 2, hd[1] + 5.0))], cv.u(1.2), (0.1, 0.7)),
                 FR, z=2.5, sd=0.4, ol=0.7)
        if ek > 0.05:
            for q in ((hd[0] + 1.0, hd[1] + 0.6), (hd[0] + 3.6, hd[1] + 0.7)):
                cv.stroke([q, (q[0] + 0.1, q[1] + 2.0)], 0.8, z=15.5, col=V['curse'], taper=(0.1, 0.9), glow=V['curse_glow'])
                yk.glow_soft(cv, q, (1.4 + flare + p['eye']) * ek, V['curse_glow'], z=15.6, alpha=(0.4 + 0.3 * eye_on) * ek)
        for i in range(5):   # kır sakal
            x = hd[0] + 0.4 + i * 1.0
            cv.stroke([(x, hd[1] + 3.4), (x - fr - hflow * 0.5, hd[1] + 6.0 + (i % 2))], 0.9, z=15.7, col=(0.75, 0.75, 0.72), taper=(0.0, 0.8))
    else:                 # erlik kızı: solgun güzel yüz
        face = cv.blob([(hd[0] - 1.2, hd[1] - 2.8), (hd[0] + 3.0, hd[1] - 3.4), (hd[0] + 4.6, hd[1] - 0.8), (hd[0] + 4.2, hd[1] + 2.0),
                        (hd[0] + 2.6, hd[1] + 4.2, 0.0), (hd[0] + 0.4, hd[1] + 3.4), (hd[0] - 1.4, hd[1] + 0.6)])
        fdet = [('col', cv.blob([(hd[0] + 2.1, hd[1] + 2.4), (hd[0] + 3.5, hd[1] + 2.2), (hd[0] + 2.8, hd[1] + 2.9 + 0.5 * p['eye'])]), (0.78, 0.08, 0.14)),
                ('ink', [(hd[0] + 3.2, hd[1] - 0.4), (hd[0] + 3.8, hd[1] + 0.9), (hd[0] + 3.4, hd[1] + 1.2)], 0.7)]
        cv.shape(face, V['skin'], z=14, sd=1.0, hi=0.3, details=fdet)
        for q in ((hd[0] + 1.0, hd[1] - 0.6), (hd[0] + 3.4, hd[1] - 0.8)):
            hgt = 1.0 - 0.8 * bl
            cv.fill(cv.blob([(q[0] - 0.9, q[1] + 0.1), (q[0], q[1] - 0.5 * hgt), (q[0] + 0.9, q[1] - 0.2, 0.0), (q[0], q[1] + 0.4 * hgt)]), INK, z=20)
            if ek > 0.05 and bl < 0.9:
                yk.eye_glow(cv, (q[0] + 0.1, q[1] - 0.05), 0.4 * eb * ek, 0.3 * eb * ek * hgt, -0.2, V['eye'], V['eye_glow'], 21,
                            halo=2.2 + p['eye'], halo_a=(0.3 + 0.3 * eye_on) * ek)
        cv.stroke([(hd[0] - 0.2, hd[1] - 1.6 + 0.3 * p['eye']), (hd[0] + 1.6, hd[1] - 1.9 + 0.5 * p['eye'])], 0.8, z=21.5, col=INK, taper=(0.2, 0.8))
        # perçem: yüzün üstüne düşen saç
        frg = cv.blob([(hd[0] - 2.0, hd[1] + 1.0), (hd[0] - 1.8, hd[1] - 3.6), (hd[0] + 1.4, hd[1] - 5.2), (hd[0] + 4.6, hd[1] - 3.8),
                       (hd[0] + 4.8, hd[1] - 2.0, 0.0), (hd[0] + 2.0, hd[1] - 3.0), (hd[0] - 0.2, hd[1] - 1.6), (hd[0] - 0.6 - hflow * 0.6, hd[1] + 3.0, 0.0)])
        cv.shape(frg, V['hair'], z=22, sd=0.8, hi=0.5, details=[('stroke', [(hd[0] + 0.0, hd[1] - 4.2), (hd[0] + 2.8, hd[1] - 4.0)], 0.9, V['hair'].hi, (0.3, 0.5))])
        # gerdanlık: kemik boncuklar
        for i in range(5):
            q = (hd[0] - 0.8 + i * 1.1, hd[1] + 5.4 + abs(i - 2) * -0.25)
            cv.shape(cv.ellipse(q, 0.5, 0.6), BONE, z=13, sd=0.2, ol=0.6)
    if p['daze'] > 0.05:   # sersem: başın çevresinde dönen kıvılcımlar
        for k in range(3):
            a = ph * 1.0 + k * math.tau / 3
            q = (hd[0] + 1.0 + math.cos(a) * 5.5, hd[1] - 6.5 + math.sin(a) * 1.6)
            s_ = 0.7 + 0.3 * math.sin(a)
            cv.stroke([(q[0] - s_, q[1]), (q[0] + s_, q[1])], 1.0, z=30, col=V['curse_hot'], taper=(0.4, 0.4), glow=V['curse_glow'])
            cv.stroke([(q[0], q[1] - s_), (q[0], q[1] + s_)], 1.0, z=30, col=V['curse_hot'], taper=(0.4, 0.4), glow=V['curse_glow'])
    cv.pop()   # baş ötelemesi
    cv.pop()   # baş dönüşü
    cv.pop()   # gövde

    # ---- ön kol: lanet eli (açılar figür çerçevesinde)
    ar = p['ar']
    shf = T((hip[0] + 3.5, hip[1] - 12))
    e, h = fk_arm(shf, ar[0], ar[1], 5.5, 5.5)
    cuff = lerp2(e, h, 0.6)
    sleeve = cv.limb([shf, e, cuff], [2.0, 1.8, 2.1])
    cv.shape(sleeve, C, z=26, sd=1.0, hi=0.35, details=[('stroke', [lerp2(e, cuff, 0.6), cuff], 1.6, V['stripe'], (0.0, 0.0))])
    dn = yg.rot((0.0, 1.0), -roll)
    for k in (-1, 0, 1):   # kol saçakları dünyada sarkar
        q = (cuff[0] + k * 0.8, cuff[1])
        sw = math.sin(ph + k) * 0.3 - fr * 0.8
        cv.shape(ik.taper_path([cv.W(q), cv.W((q[0] + k * 0.3 + sw + dn[0] * 3.2, q[1] + dn[1] * 3.2))], cv.u(0.9), (0.0, 0.7)), FR, z=26.5 + k * 0.01, sd=0.3, ol=0.6)
    a = ar[0] + ar[1]
    fwd = (math.sin(a), math.cos(a))
    cv.shape(cv.capsule(cuff, h, 0.85, 0.9), V['skin'], z=27, sd=0.4, ol=0.8)
    bow = p['bow']
    gc = (h[0] + fwd[0] * 2.6, h[1] + fwd[1] * 2.6)
    if bow > 0.3:
        cv.shape(cv.ellipse(h, 1.25, 1.15), V['skin'], z=27.6, sd=0.4, ol=0.8)   # yumruk: yayı kavrar
    else:
        sp = 0.55 * (1.0 + 0.7 * p['fing'])
        for k in (-sp, 0.0, sp):
            tip = (h[0] + math.sin(a + k) * 2.6, h[1] + math.cos(a + k) * 2.6)
            cv.shape(ik.taper_path([cv.W(h), cv.W(lerp2(h, tip, 0.6)), cv.W(tip)], cv.u(0.75), (0.0, 0.8)), V['skin'], z=27.5, sd=0.3, ol=0.7)
    anchor = gc
    # lanet küresi: parlak çekirdek, dönen mürekkep sarmal, uyarıda halka + kıvılcımlar
    r = (1.0 + cast * 2.2 + p['flick']) * p['orb']
    if r > 0.25 and bow <= 0.3:
        yk.glow_soft(cv, gc, r * 2.6 + flare * 3, V['curse_glow'], z=29.5, blur=0.55, alpha=0.55 + 0.3 * flare)
        cv.fill(cv.ellipse(gc, r, r), V['curse'], z=30, glow=V['curse_glow'])
        cv.fill(cv.ellipse((gc[0] - r * 0.15, gc[1] - r * 0.15), r * 0.55, r * 0.55), V['curse_hot'], z=30.1, glow=V['curse_hot'])
        if r > 1.6:
            for k in range(2):   # sarmal
                a0 = ph * 1.5 + k * math.pi
                pts = [(gc[0] + math.cos(a0 + u * 3.5) * r * (0.4 + 0.8 * u), gc[1] + math.sin(a0 + u * 3.5) * r * (0.4 + 0.8 * u)) for u in np.linspace(0, 1, 6)]
                cv.stroke(pts, 1.1, z=30.2, col=INK, taper=(0.6, 0.2), alpha=0.85)
    if (cast > 0.5 or flare > 0) and bow <= 0.3:
        rr = max(r, 1.0) + 2.2 + flare * 1.0
        ring = [(gc[0] + math.cos(t_) * rr, gc[1] + math.sin(t_) * rr * 0.9) for t_ in np.linspace(ph, ph + 4.6, 9)]
        cv.stroke(ring, 1.3, z=31, col=V['curse'], taper=(0.6, 0.1), glow=V['curse_glow'])
        yk.sparks(cv, gc, 6, max(r, 1.0) + 1.0, max(r, 1.0) + 4.0, V['curse_hot'], 31.1, seed=abs(int(ph * 7)) + 1, w=1.1, glow=V['curse_glow'])
    # büyü bağı: açık avuçtan öne doğru ışın kökü (oyunda Isin ışını buradan sürer)
    bm_ = p['beam']
    if bm_ > 0.05:
        yk.glow_soft(cv, gc, 3.0 + 3.0 * bm_, V['curse_glow'], z=29.4, blur=0.6, alpha=0.5 + 0.4 * bm_)
        L_ = 1.5 + 3.0 * bm_
        cv.fill(cv.ellipse(gc, 1.0 + 0.8 * bm_, 1.0 + 0.8 * bm_), V['curse_hot'], z=31.4, glow=V['curse_glow'])
        yk.sparks(cv, gc, 6, 1.6, 4.5, V['curse_hot'], 31.6, seed=abs(int(ph * 3)) + 4, w=1.0, glow=V['curse_glow'], ang=math.atan2(fwd[1], fwd[0]), spread=2.2)
        cv.stroke([gc, (gc[0] + fwd[0] * L_ * 0.5, gc[1] + fwd[1] * L_ * 0.5), (gc[0] + fwd[0] * L_, gc[1] + fwd[1] * L_)], 2.6 * bm_ + 0.6, z=31.5,
                  col=V['curse_hot'], taper=(0.1, 0.9), glow=V['curse_glow'])
        for k in range(3):   # avucun çevresinde dönen büyü telleri
            a0 = ph * 2.0 + k * math.tau / 3
            pts = [(gc[0] + math.cos(a0 + u * 2.4) * (1.5 + 2.0 * u) * (0.6 + 0.4 * bm_), gc[1] + math.sin(a0 + u * 2.4) * (1.5 + 2.0 * u) * (0.6 + 0.4 * bm_))
                   for u in np.linspace(0, 1, 6)]
            cv.stroke(pts, 1.0, z=31.2, col=V['curse'], taper=(0.6, 0.2), glow=V['curse_glow'])
    # ruh yayı (Kurgan Kamı): kemik yay + ışıyan kiriş, ok arka elde
    if bow > 0.3:
        bt = p['btilt'] + 0.0
        up = yg.rot((0.0, -1.0), bt)
        back = yg.rot((-1.0, 0.0), bt)
        drw = yg.clamp(p['draw'], 0.0, 1.2)
        bend = 1.0 + 0.7 * drw
        limbs = []
        tips = []
        for s in (1, -1):
            pts = []
            for v, o in ((0.0, -0.3), (0.35, 0.35), (0.7, 1.5), (1.0, 2.3), (1.1, 1.5)):
                L_ = 8.2 * v
                oo = o * bend if v < 1.05 else (2.3 * bend - 0.9)
                pts.append((h[0] + up[0] * s * L_ + back[0] * oo, h[1] + up[1] * s * L_ + back[1] * oo))
            tips.append(pts[-2])
            limbs.append(ik.taper_path([cv.W(q) for q in pts], cv.u(1.5), prof=lambda u: max(0.35, 1.0 - 0.6 * u)))
        cv.shape(ik.union(*limbs), BONE, z=28, sd=0.5, hi=0.3, ol=0.85)
        if bow > 1.02:   # "!!": yay alev alır
            fl = min(1.0, (bow - 1.0) * 3.5)
            for tq in tips + [h]:
                yk.glow_soft(cv, tq, 2.4 + 2.0 * fl, V['curse_glow'], z=28.2, blur=0.6, alpha=0.6 * fl)
                yk.sparks(cv, tq, 4, 0.8, 3.6, V['curse_hot'], 28.3, seed=abs(int(tq[1] * 3)) + 7, w=1.0, glow=V['curse_glow'], ang=-math.pi / 2, spread=1.8)
        cv.shape(cv.capsule((h[0] + up[0] * 1.2, h[1] + up[1] * 1.2), (h[0] - up[0] * 1.2, h[1] - up[1] * 1.2), 0.9, 0.9), V['mirror'], z=28.5, sd=0.3, hi=0.2, ol=0.7)
        smid = lerp2(tips[0], tips[1], 0.5)
        nock = lerp2(smid, hb, yg.clamp(drw, 0.0, 1.0)) if bhw > 0.5 else smid
        snap = p['snap']
        if snap > 0.3:   # bırakış: kiriş öne fırlar, titrer
            nock = (smid[0] - back[0] * 1.6, smid[1] - back[1] * 1.6)
        cv.stroke([tips[0], nock, tips[1]], 1.3, z=28.8, col=V['curse_hot'], taper=(0.2, 0.2), glow=V['curse_glow'])
        gl = 0.25 + 0.35 * drw + 0.3 * max(0.0, bow - 1.0) * 3
        yk.glow_soft(cv, lerp2(nock, h, 0.5), 2.5 + 2.0 * drw, V['curse_glow'], z=28.7, blur=0.6, alpha=gl)
        if p['arrow'] > 0.5:
            d_ = (h[0] - nock[0], h[1] - nock[1])
            ln = math.hypot(*d_) + 1e-6
            d_ = (d_[0] / ln, d_[1] / ln)
            atip = (h[0] + d_[0] * 4.0, h[1] + d_[1] * 4.0)
            cv.stroke([nock, atip], 1.1, z=29.0, col=(0.85, 0.8, 0.68), taper=(0.0, 0.0))
            nx_, ny_ = -d_[1], d_[0]
            for s in (1, -1):   # tüy
                cv.fill(cv.blob([(nock[0] + d_[0] * 0.3, nock[1] + d_[1] * 0.3), (nock[0] + d_[0] * 2.6, nock[1] + d_[1] * 2.6),
                                 (nock[0] + d_[0] * 0.2 + nx_ * s * 1.3, nock[1] + d_[1] * 0.2 + ny_ * s * 1.3, 0.0)]), V['feather'].base, z=29.1)
            cv.fill(cv.blob([(atip[0] + d_[0] * 1.8, atip[1] + d_[1] * 1.8, 0.0), (atip[0] + nx_ * 0.8, atip[1] + ny_ * 0.8), (atip[0] - nx_ * 0.8, atip[1] - ny_ * 0.8)]),
                    V['curse_hot'], z=29.2, glow=V['curse_glow'])
            yk.glow_soft(cv, atip, 1.8 + 1.5 * drw, V['curse_glow'], z=29.3, alpha=0.6)
            anchor = atip
        else:
            anchor = (h[0] - back[0] * 3.0, h[1] - back[1] * 3.0)
        if snap > 0.05:
            yk.sparks(cv, h, 7, 1.5, 5.0 + 2.0 * snap, V['curse_hot'], 31, seed=5, w=1.2, glow=V['curse_glow'], ang=math.atan2(-back[1], -back[0]), spread=1.6)
        if bow < 0.95:   # beliriş / dağılış: kıvılcımlar
            yk.sparks(cv, h, 6, 2.0, 8.0, V['curse_hot'], 31.2, seed=9, w=1.0, glow=V['curse_glow'])
    anchor_w = yg.world(cv, anchor)
    cv.pop()   # ezilme
    cv.pop()   # figür

    # ---- dünya çerçevesi efektleri: rün halkası, duman, ruh telleri
    if p['rune'] > 0.05:
        rn = p['rune']
        rx, ry_ = 6.0 + 9.0 * rn, 1.6 + 1.6 * rn
        cx = X * 0.5
        ring = [(cx + math.cos(t_) * rx, -0.3 + math.sin(t_) * ry_) for t_ in np.linspace(0, math.tau, 25)]
        cv.stroke(ring, 1.4, z=-30, col=V['curse'], taper=(0.0, 0.0), glow=V['curse_glow'])
        for k in range(8):
            t_ = ph * 0.5 + k / 8 * math.tau
            q = (cx + math.cos(t_) * rx * 0.78, -0.3 + math.sin(t_) * ry_ * 0.78)
            cv.stroke([(q[0] - 0.5, q[1] - 0.8), (q[0], q[1] + 0.2), (q[0] + 0.5, q[1] - 0.8)], 1.0, z=-29.9 if math.sin(t_) < 0 else 40,
                      col=V['curse_hot'], taper=(0.2, 0.2), glow=V['curse_glow'])
        yk.glow_soft(cv, (cx, -0.6), rx, V['curse_glow'], z=-30.1, blur=0.7, alpha=0.35 * rn, ry=ry_ * 1.6)
    if p['smoke'] > 0.05:
        sm = p['smoke']
        c0 = (X + 2.5, -16.0)     # duman topağı dünyada (gövdeyi örter, dağılırken açılır ve yükselir)
        for k, (ox, oy, rr) in enumerate(((0.0, 0.0, 10.0), (-7.5, 7.0, 8.0), (7.0, 6.5, 8.0), (-5.0, -8.5, 7.5), (5.0, -10.0, 7.0), (0.5, 11.0, 7.5),
                                          (-1.0, -17.0, 6.0), (9.0, -3.0, 5.5), (-9.5, -2.0, 5.5), (6.5, -15.0, 6.5))):
            sc = sm * (0.8 + 0.2 * math.sin(ph + k))
            cc = (c0[0] + ox * (0.8 + 0.7 * (1 - sm)), c0[1] + oy * (0.85 + 0.5 * (1 - sm)) - (1 - sm) * 5.0)
            yk.puff(cv, cc, rr * sc, SMOKE, z=44 + k * 0.1, seed=k + 3)
        yk.glow_soft(cv, c0, 10.0 * sm, V['curse_glow'], z=43.9, blur=0.7, alpha=0.4 * sm)
        yk.sparks(cv, c0, 8, 6.0, 14.0, V['curse_hot'], 45, seed=abs(int(ph * 5)) + 2, w=1.0, glow=V['curse_glow'])
    if p['wisp'] > 0.05:
        wsp = p['wisp']
        c0 = to_world((1.0, -10.0))
        for k in range(3):
            st = (c0[0] - 3.0 + k * 3.0, c0[1] - wsp * 8.0 * (0.8 + 0.2 * k))
            yk.wisp(cv, st, -math.pi / 2 + (k - 1) * 0.25, 7.0 + 8.0 * min(1.0, wsp), 2.6 * max(0.2, 1.4 - wsp * 0.7), SPIRIT, 46 + k * 0.1,
                    ph=ph + k * 1.7, curl=0.9, alpha=0.8 * max(0.15, 1.3 - wsp * 0.6), glow=V['curse_glow'], glow_a=0.7)
    return {'hand': anchor_w}


SHADE = dict(outer=0.5, rim=0.7, rim_col=(0.7, 0.78, 1.0), rim_dir=(0.6, -0.8), rim_w=1.3, form=(4.0, (0.76, 0.74, 0.88)))


# ====================================================================== anahtar pozlar (yaratik_govde.Seq)
def _foot_cycle(phi, home, S, duty, lift, toe_up=0.5, toe_push=0.35):
    """Döngüsel çizme yolu: basma (duty) boyunca +S/2 -> -S/2 (gövdeye göre sabit hız), salınımda yayla öne."""
    phi %= 1.0
    if phi < duty:
        u = phi / duty
        toe = toe_push * max(0.0, (u - 0.7) / 0.3)          # itişte topuk kalkar (burun aşağı)
        return (home + S * (0.5 - u), 0.0, -toe)
    u = (phi - duty) / (1.0 - duty)
    e = u * u * (3 - 2 * u)
    return (home - S * 0.5 + S * e, lift * math.sin(math.pi * u) ** 0.8, toe_up * math.sin(math.pi * min(1.0, u * 1.2)))


RUN_S, RUN_DUTY, RUN_N, RUN_FPS = 12.0, 0.45, 8, 16


def _run(t):
    """Kambur koşturma: kısa hızlı adımlar, gövde öne eğik, etek ve saçaklar geride sürüklenir, davul sekerek gecikir."""
    c2 = math.cos(4 * math.pi * (t - RUN_DUTY * 0.5))
    p = dict(lf=_foot_cycle(t, 1.2, RUN_S, RUN_DUTY, 4.8, toe_up=0.7), lb=_foot_cycle(t - 0.5, -0.6, RUN_S, RUN_DUTY, 4.2, toe_up=0.7))
    p.update(y=1.8 + 1.3 * c2, pitch=0.3 + 0.05 * c2, hd=(1.4, 0.8 + 0.5 * c2), hr=0.08 - 0.06 * c2,
             ar=(1.05 + 0.18 * math.sin(t * math.tau), 0.45), cast=0.15, dk=(0.5, 0.9 * math.sin(4 * math.pi * t + 1.2)),
             drot=0.12 * math.sin(4 * math.pi * t + 0.6), hem=0.9 + 0.2 * math.sin(4 * math.pi * t - 0.6), hl=1.4,
             fr=0.7 + 0.35 * math.sin(4 * math.pi * t - 1.4), hair=0.5, ph=t * math.tau * 2, feath=-0.2)
    return p


def _idle_proc(p, t):
    """Bekleme: süzülür gibi salınım; etek, saçak, tüy ve saçta gecikmeli dalga; kürede titreşim."""
    p = dict(p)
    w = math.tau
    p['ph'] = t * w
    p['y'] = p.get('y', 0.0) + 0.55 * math.sin(t * w * 2)
    p['pitch'] = p.get('pitch', 0.0) + 0.03 * math.sin(t * w * 2 - 0.6)
    p['hr'] = p.get('hr', 0.0) + 0.05 * math.sin(t * w * 2 - 1.3)
    p['flick'] = p.get('flick', 0.0) + 0.3 * math.sin(t * w * 4)
    a1, a2 = p.get('ar', (0.6, 0.8))
    p['ar'] = (a1 + 0.12 * math.sin(t * w), a2 + 0.06 * math.sin(t * w + 1.0))
    p['hem'] = p.get('hem', 0.0) + 0.18 * math.sin(t * w * 2 - 1.6)
    p['fr'] = p.get('fr', 0.0) + 0.25 * math.sin(t * w * 2 - 2.2)
    return p


SEQS = {}
R0 = dict(ar=(0.75, 0.9), cast=0.2)

# ---- bekleme (8 kare, 1 sn): süzülen salınım; ortada davula kısa vuruş (tik): davul kalkar, baş vuruşla eğilir
SEQS['idle'] = Seq([
    (0.0, dict(R0), 'io'),
    (0.35, dict(R0, hd=(0.2, 0.0)), 'io'),
    (0.5, dict(R0, dk=(0.8, -2.2), drot=-0.35, drum=0.8, hd=(0.5, 0.6), hr=0.12, cast=0.35, feath=0.3), 'o'),
    (0.62, dict(R0, dk=(0.3, -0.8), drot=-0.1, drum=0.2, hd=(0.2, 0.2), hr=0.04, cast=0.28, feath=0.15), 'io'),
    (1.0, dict(R0), 'io'),
], n=8, fps=8, loop=True, proc=_idle_proc, rest=REST)

# ---- koşu (8 kare, adım 12 birim): vx = adım / basma süresi
SEQS['run'] = Seq([(i / 16, _run(i / 16), 'l') for i in range(17)], n=RUN_N, fps=RUN_FPS, loop=True, rest=REST,
                  extra={'vx': round(RUN_S / (RUN_DUTY * RUN_N / RUN_FPS), 1)})

# ---- dönüş (3 kare): baş eski yöne bakar, etek ve davul eski yönden savrulup gelir, oturur
SEQS['turn'] = Seq([
    (0.0, dict(R0, x=-0.8, pitch=-0.12, hd=(-2.2, 0.4), hr=-0.25, hem=-1.3, fr=-1.0, dk=(4.0, 0.5), drot=0.5, lf=(-1.2, 0.0, 0.0),
               lb=(-3.0, 1.5, 0.4), ar=(0.2, 0.9), feath=-0.3, hair=-0.6), 'l'),
    (0.5, dict(R0, x=-0.2, pitch=0.06, hd=(0.4, 0.3), hr=0.06, hem=0.5, fr=0.6, dk=(1.0, 0.0), drot=0.1, lb=(-2.2, 0.0, 0.0), ar=(0.6, 0.8)), 'o'),
    (1.0, dict(R0, hem=-0.15, fr=-0.2), 'o'),
], frames=[0.0, 0.45, 1.0], fps=12, rest=REST)

# ---- büyü (illusionist; hazırlık 4 + vuruş 4): davula vurur, el geriye-yukarı kalkar, küre büyür, derin kurulma
# (geri yaslanma, çömelme, halka döner) -> öne savuruş (temas: kol dümdüz, etek geriye kabarır) -> takip -> oturma
CAST_W = [
    dict(R0, pitch=-0.08, y=0.6, ar=(1.9, 0.9), cast=0.5, dk=(1.5, -3.0), drot=-0.45, drum=1.0, hd=(-0.3, 0.0), hr=-0.06, hem=-0.2,
         feath=0.3, lf=(1.2, 0.0, 0.0), lb=(-2.4, 0.0, 0.0)),
    dict(R0, pitch=-0.2, y=1.6, ar=(2.6, 0.6), cast=0.85, dk=(0.0, -1.5), drot=-0.2, drum=0.3, hd=(-0.8, -0.2), hr=-0.14, hem=-0.4, flr=0.2,
         feath=0.6, eye=0.4, lf=(2.0, 0.0, 0.0), lb=(-3.4, 0.0, 0.0), fr=-0.3),
    dict(R0, pitch=-0.28, y=2.8, ar=(2.95, 0.35), cast=1.2, flare=0.6, dk=(-0.5, -0.8), drot=-0.1, hd=(-1.0, 0.2), hr=-0.18, hem=-0.55,
         flr=0.35, feath=0.9, eye=0.8, lf=(2.6, 0.0, 0.0), lb=(-4.2, 0.0, 0.0), fr=-0.5, hair=0.4),
    dict(R0, pitch=0.12, y=1.6, x=1.0, ar=(2.1, 0.15), cast=1.2, flare=0.8, dk=(-1.5, -0.5), drot=0.2, hd=(1.0, 0.4), hr=0.06, hem=0.3,
         flr=0.3, feath=0.6, eye=1.0, lf=(3.4, 0.0, 0.0), lb=(-4.2, 0.0, -0.2), fr=0.3),
]
CAST_S = [
    dict(R0, pitch=0.34, y=2.2, x=1.6, ar=(1.55, 0.0), fing=1.0, cast=0.35, flare=1.0, dk=(-3.0, 1.0), drot=0.5, hd=(1.8, 0.8), hr=0.12,
         hem=1.4, flr=0.7, hl=1.0, fr=1.2, feath=-0.2, eye=1.0, lf=(5.2, 0.0, 0.0), lb=(-4.4, 0.0, -0.3), hair=0.8),
    dict(R0, pitch=0.24, y=1.6, x=1.3, ar=(1.42, 0.12), fing=0.7, cast=0.25, flare=0.35, dk=(-2.0, 0.6), drot=0.3, hd=(1.4, 0.6), hr=0.08,
         hem=0.9, flr=0.4, hl=0.6, fr=0.8, eye=0.6, lf=(5.2, 0.0, 0.0), lb=(-4.4, 0.0, 0.0), hair=0.5),
    dict(R0, pitch=0.08, y=0.8, x=0.6, ar=(1.0, 0.5), cast=0.2, dk=(-0.5, 0.0), drot=0.05, hd=(0.5, 0.2), hr=0.0, hem=-0.25, fr=-0.3,
         lf=(3.0, 0.0, 0.0), lb=(-2.4, 0.0, 0.0)),
    dict(R0, pitch=0.0, y=0.2, x=0.2, hem=0.05, fr=0.05, lf=(1.2, 0.0, 0.0), lb=(-1.9, 0.0, 0.0)),
]
SEQS['cast'] = Seq([(0.0, CAST_W[0], 'o'), (0.12, CAST_W[1], 'o'), (0.24, CAST_W[2], 'o'), (0.36, CAST_W[3], 'i'),
                    (0.48, CAST_S[0], 'i'), (0.6, CAST_S[1], 'o'), (0.78, CAST_S[2], 'o'), (1.0, CAST_S[3], 'io')],
                   frames=[(0.0, 0.0), (0.12, 0.2), (0.24, 0.45), (0.36, 0.0), (0.48, 0.0), (0.6, 0.2), (0.78, 0.5), (1.0, 0.78)],
                   seg=[('windup', 4), ('strike', 4)], lead={'windup': 0.05}, fps=10, rest=REST)

# ---- zırhlı büyü hazırlığı "!!" (4 kare): yerden yükselir (levitasyon), ayaklar sarkar, etek ve tüyler kabarır,
# altında rün halkası döner, davul başın üstünde gümbürder, küre iri, gözler alev alev
AA_UP = dict(y=-5.5, pitch=-0.26, lf=(2.2, 6.2, -0.8), lb=(-1.4, 5.6, -0.9), ar=(3.0, 0.3), cast=1.45, flare=1.0, dk=(3.5, -6.5), drot=-0.9,
             drum=1.0, hd=(-0.8, -0.6), hr=-0.22, hem=-0.2, flr=0.8, hl=0.0, feath=1.4, eye=1.0, rune=1.0, fr=-0.6, hair=1.2)
SEQS['cast_aa'] = Seq([
    (0.0, dict(R0, y=2.6, pitch=0.1, ar=(1.6, 0.9), cast=0.8, dk=(0.5, -1.0), drum=1.0, hd=(0.8, 0.8), hr=0.15, feath=0.5, eye=0.6, rune=0.35,
               lf=(1.6, 0.0, 0.0), lb=(-2.4, 0.0, 0.0), flr=0.2), 'o'),
    (0.3, dict(AA_UP, y=-3.0, flr=0.7, rune=0.75, cast=1.2, ar=(2.8, 0.4), lf=(2.2, 3.4, -0.5), lb=(-1.6, 2.8, -0.6)), 'o'),
    (0.62, dict(AA_UP), 'io'),
    (1.0, dict(AA_UP, y=-3.0, pitch=0.16, x=1.2, ar=(2.0, 0.1), hd=(1.2, 0.4), hr=0.08, hem=0.5, fr=0.4, dk=(1.0, -3.0), drot=0.1, lf=(3.2, 4.0, -0.5), lb=(-1.0, 3.4, -0.6)), 'i'),
], frames=[(0.0, 0.0), (0.3, 0.2), (0.62, 0.45), (1.0, 0.0)], seg=[('windup', 4)], lead={'windup': 0.05}, fps=10, rest=REST)

# ---- lanet (charmer "curse"; hazırlık 3 + vuruş 3 + toparlanma 2): el kalçaya çekilir, küre iki kat büyür, ayna kalkar;
# öne itiş (temas: iki küre fırlar), takip, iniş
CU_W = [
    dict(R0, pitch=-0.1, y=0.8, ar=(-0.3, 1.5), cast=0.7, dk=(2.0, -3.0), drot=-0.4, drum=0.6, hd=(-0.4, 0.2), hr=-0.05, hem=-0.15, feath=0.2,
         eye=0.3, lf=(1.4, 0.0, 0.0), lb=(-2.6, 0.0, 0.0), hair=0.3),
    dict(R0, pitch=-0.22, y=2.4, ar=(-0.75, 1.75), cast=1.3, flare=0.7, dk=(2.5, -4.0), drot=-0.6, drum=1.0, hd=(-0.6, 0.6), hr=0.05, hem=-0.4,
         flr=0.3, feath=0.6, eye=1.0, lf=(2.6, 0.0, 0.0), lb=(-4.0, 0.0, 0.0), fr=-0.4, hair=0.6),
    dict(R0, pitch=0.05, y=1.8, x=0.8, ar=(0.5, 0.9), cast=1.3, flare=0.8, dk=(1.0, -2.0), drot=-0.2, hd=(0.6, 0.6), hr=0.06, hem=0.2,
         flr=0.3, eye=1.0, lf=(3.4, 0.0, 0.0), lb=(-4.0, 0.0, -0.2)),
]
CU_S = [
    dict(R0, pitch=0.32, y=2.0, x=1.6, ar=(1.35, 0.05), fing=1.0, cast=0.3, flare=1.0, dk=(1.5, -1.0), drot=0.6, drum=0.8, hd=(1.6, 1.0), hr=0.14,
         hem=1.2, flr=0.6, hl=0.8, fr=1.0, eye=1.0, lf=(5.4, 0.0, 0.0), lb=(-4.2, 0.0, -0.3), hair=0.9),
    dict(R0, pitch=0.24, y=1.4, x=1.3, ar=(1.3, 0.15), fing=0.6, cast=0.2, flare=0.3, dk=(0.5, -0.5), drot=0.3, hd=(1.2, 0.8), hr=0.1,
         hem=0.8, flr=0.35, fr=0.7, eye=0.6, lf=(5.4, 0.0, 0.0), lb=(-4.2, 0.0, 0.0), hair=0.6),
    dict(R0, pitch=0.14, y=1.0, x=1.0, ar=(1.1, 0.4), cast=0.15, dk=(0.0, 0.0), hd=(0.8, 0.6), hr=0.06, hem=0.3, fr=0.2, lf=(5.4, 0.0, 0.0),
         lb=(-4.2, 0.0, 0.0)),
]
CU_R = [
    dict(R0, pitch=0.04, y=0.6, x=0.6, ar=(0.85, 0.7), hd=(0.3, 0.3), hem=-0.25, fr=-0.3, lf=(3.4, 0.0, 0.0), lb=(-2.4, 0.0, 0.0)),
    dict(R0, y=0.1, x=0.1, hem=0.05, lf=(1.0, 0.0, 0.0), lb=(-1.9, 0.0, 0.0)),
]
SEQS['curse'] = Seq([(0.0, CU_W[0], 'o'), (0.14, CU_W[1], 'o'), (0.28, CU_W[2], 'i'), (0.4, CU_S[0], 'i'), (0.52, CU_S[1], 'o'),
                     (0.66, CU_S[2], 'o'), (0.82, CU_R[0], 'io'), (1.0, CU_R[1], 'io')],
                    frames=[(0.0, 0.0), (0.14, 0.3), (0.28, 0.0), (0.4, 0.0), (0.52, 0.25), (0.66, 0.6), (0.82, 0.0), (1.0, 0.5)],
                    seg=[('windup', 3), ('strike', 3), ('recover', 2)], lead={'windup': 0.05}, fps=10, rest=REST)

# ---- ruh yayı (archer; hazırlık 4 + vuruş 4): kehribar ışıktan kemik yay belirir -> oku takar -> geri yaslanıp sonuna dek
# gerer (tutulur) -> nişan düzeltme (son 0,05 sn) / bırakış (temas: kiriş öne fırlar, çeken el geriye savrulur) -> takip ->
# yay dağılır, oturur. Davul kayışla sırtta.
BW = dict(bow=1.0, arrow=1.0, bhw=1.0, orb=0.0, cast=0.0, dk=(1.5, -2.0), drot=0.3)
SEQS['bow'] = Seq([
    (0.0, dict(R0, orb=0.0, bow=0.6, ar=(1.2, 0.35), bhw=0.4, bh=(4.0, 0.0), pitch=-0.04, y=0.6, hd=(0.3, 0.2), feath=0.2, eye=0.3,
               lf=(1.6, 0.0, 0.0), lb=(-2.6, 0.0, 0.0), dk=(1.0, -1.5), drot=0.2), 'o'),
    (0.13, dict(R0, **dict(BW, draw=0.25, ar=(1.52, 0.0), bh=(3.6, -0.6), pitch=-0.06, y=1.2, hd=(0.6, 0.4), hr=0.04, eye=0.5,
                           lf=(3.0, 0.0, 0.0), lb=(-3.6, 0.0, 0.0))), 'o'),
    (0.26, dict(R0, **dict(BW, draw=1.0, ar=(1.58, -0.04), bh=(1.6, -1.4), pitch=-0.16, y=2.4, hd=(0.4, 0.6), hr=0.02, eye=0.8, hem=-0.25, flr=0.15,
                           feath=0.4, lf=(4.2, 0.0, 0.0), lb=(-4.6, 0.0, 0.0), fr=-0.3)), 'o'),
    (0.38, dict(R0, **dict(BW, draw=1.08, ar=(1.62, -0.06), bh=(1.2, -1.5), pitch=-0.2, y=2.6, hd=(0.6, 0.7), hr=0.0, eye=1.0, hem=-0.3, flr=0.2,
                           feath=0.5, lf=(4.4, 0.0, 0.0), lb=(-4.8, 0.0, 0.0), fr=-0.4)), 'io'),
    (0.5, dict(R0, **dict(BW, arrow=0.0, draw=0.0, snap=1.0, ar=(1.8, -0.1), bh=(-2.8, 1.5), pitch=-0.08, y=1.8, x=-0.6, hd=(-0.2, 0.2),
                          hr=-0.06, eye=1.0, hem=-0.6, flr=0.35, fr=-0.8, lf=(4.0, 0.0, 0.0), lb=(-5.0, 0.0, 0.0), hair=-0.4)), 'i'),
    (0.62, dict(R0, **dict(BW, arrow=0.0, draw=0.0, snap=0.3, ar=(1.7, -0.05), bh=(-2.0, 2.0), pitch=-0.05, y=1.4, x=-0.4, hd=(0.0, 0.3),
                           eye=0.6, hem=-0.2, flr=0.15, fr=-0.3, lf=(4.0, 0.0, 0.0), lb=(-5.0, 0.0, 0.0))), 'o'),
    (0.8, dict(R0, orb=0.0, bow=0.6, ar=(1.2, 0.45), bhw=0.4, bh=(2.0, 2.0), pitch=0.04, y=0.8, x=-0.2, hd=(0.3, 0.3), hem=0.2, fr=0.2,
               lf=(2.6, 0.0, 0.0), lb=(-3.0, 0.0, 0.0), dk=(0.5, -0.8), drot=0.15), 'io'),
    (1.0, dict(R0, orb=0.4, ar=(0.8, 0.8), y=0.2, hem=-0.05, lf=(1.0, 0.0, 0.0), lb=(-1.9, 0.0, 0.0)), 'io'),
], frames=[(0.0, 0.0), (0.13, 0.18), (0.26, 0.42), (0.38, 0.0), (0.5, 0.0), (0.62, 0.22), (0.8, 0.5), (1.0, 0.8)],
    seg=[('windup', 4), ('strike', 4)], lead={'windup': 0.05}, fps=10, rest=REST)

# ---- zırhlı yay hazırlığı "!!" (4 kare): yere sinik geniş duruş, etek kabarır, yay alev alır, rün halkası, gözler yanar
BA = dict(R0, **dict(BW, draw=1.15, bow=1.3, ar=(1.6, -0.05), bh=(1.0, -1.6), pitch=-0.24, y=5.0, hd=(0.6, 0.9), hr=0.04, eye=1.0, hem=-0.4,
                     flr=0.7, hl=0.6, feath=1.2, rune=1.0, lf=(6.4, 0.0, 0.0), lb=(-6.6, 0.0, 0.2), fr=-0.6, hair=0.8))
SEQS['bow_aa'] = Seq([
    (0.0, dict(R0, orb=0.0, bow=0.8, ar=(1.3, 0.3), bhw=0.5, bh=(3.6, 0.0), pitch=0.0, y=2.4, hd=(0.4, 0.6), eye=0.6, rune=0.4, feath=0.4,
               lf=(3.0, 0.0, 0.0), lb=(-3.6, 0.0, 0.0), dk=(1.0, -1.5)), 'o'),
    (0.3, dict(BA, draw=0.8, y=4.2, flr=0.5, rune=0.75, bow=1.15), 'o'),
    (0.62, dict(BA), 'io'),
    (1.0, dict(BA, draw=1.2, pitch=-0.18, ar=(1.64, -0.08), x=0.6, hd=(0.9, 0.9)), 'io'),
], frames=[(0.0, 0.0), (0.3, 0.2), (0.62, 0.45), (1.0, 0.0)], seg=[('windup', 4)], lead={'windup': 0.05}, fps=10, rest=REST)

# ---- büyü bağı (charmer "charm"; hazırlık 3 + kanal 3 + toparlanma 2): ayna kalkar, avuç açılır; avuç öne itilir;
# kanal boyunca geri yaslanarak "çeker" (ışın avuçtan), saç ve etek dalgalanır; sonra kollar iner
CH = dict(R0, ar=(1.62, -0.02), fing=1.0, beam=1.0, cast=0.0, orb=0.3, dk=(3.0, -5.5), drot=-0.7, drum=0.9, eye=1.0, feath=0.6, hair=0.9,
          flr=0.35, lf=(4.2, 0.0, 0.0), lb=(-3.8, 0.0, 0.0))
SEQS['charm'] = Seq([
    (0.0, dict(R0, ar=(2.1, 0.2), fing=1.0, cast=0.6, dk=(2.5, -4.5), drot=-0.6, drum=0.6, pitch=-0.06, y=0.8, hd=(-0.2, 0.0), hr=-0.06,
               eye=0.5, feath=0.3, hair=0.4, lf=(1.6, 0.0, 0.0), lb=(-2.6, 0.0, 0.0)), 'o'),
    (0.13, dict(R0, ar=(2.0, -0.15), fing=1.0, cast=0.9, flare=0.6, beam=0.3, dk=(3.0, -6.0), drot=-0.8, drum=1.0, pitch=-0.22, y=2.2,
                hd=(-0.6, 0.2), hr=-0.12, eye=1.0, feath=0.7, hair=0.9, hem=-0.4, flr=0.3, lf=(2.8, 0.0, 0.0), lb=(-3.8, 0.0, 0.0), fr=-0.4), 'o'),
    (0.25, dict(CH, beam=0.7, pitch=0.12, y=1.6, x=1.0, hd=(1.0, 0.5), hr=0.06, hem=0.5, fr=0.4), 'i'),
    (0.37, dict(CH, pitch=-0.18, y=1.8, x=0.4, hd=(0.2, 0.5), hr=-0.04, hem=-0.6, fr=-0.6, ph=0.0), 'o'),
    (0.5, dict(CH, pitch=-0.3, y=2.6, x=-0.4, hd=(-0.2, 0.7), hr=-0.1, hem=-0.9, fr=-0.9, flr=0.5, ph=2.1, lb=(-4.4, 0.0, 0.0)), 'io'),
    (0.63, dict(CH, pitch=-0.24, y=2.2, x=0.0, hd=(0.0, 0.6), hr=-0.06, hem=-0.7, fr=-0.7, ph=4.2), 'io'),
    (0.8, dict(R0, ar=(1.2, 0.5), cast=0.25, dk=(1.0, -2.0), drot=-0.2, pitch=0.06, y=1.0, x=0.2, hd=(0.4, 0.4), hem=0.3, fr=0.3, hair=0.3,
               lf=(3.0, 0.0, 0.0), lb=(-2.6, 0.0, 0.0)), 'o'),
    (1.0, dict(R0, y=0.2, hem=-0.05, lf=(1.0, 0.0, 0.0), lb=(-1.9, 0.0, 0.0)), 'io'),
], frames=[(0.0, 0.0), (0.13, 0.3), (0.25, 0.0), (0.37, 0.0), (0.5, 0.33), (0.63, 0.66), (0.8, 0.0), (1.0, 0.5)],
    seg=[('windup', 3), ('channel', 3), ('recover', 2)], lead={'windup': 0.05}, fps=8, rest=REST)

# ---- zırhlı büyü bağı hazırlığı "!!" (3 kare): yükselir, kollar açılır, saç göğe kalkar, ayna alev alır, rün halkası
CA = dict(R0, y=-5.0, pitch=-0.2, ar=(2.3, -0.3), fing=1.0, cast=1.0, flare=1.0, beam=0.5, dk=(3.0, -8.0), drot=-1.0, drum=1.0, eye=1.0,
          feath=1.4, hair=1.6, flr=0.8, hl=0.0, rune=1.0, hem=-0.2, fr=-0.6, lf=(2.2, 5.6, -0.8), lb=(-1.4, 5.0, -0.9), hd=(-0.6, -0.4), hr=-0.18)
SEQS['charm_aa'] = Seq([
    (0.0, dict(R0, y=2.4, pitch=0.08, ar=(1.4, 0.8), cast=0.7, dk=(1.5, -2.0), drum=0.8, hd=(0.6, 0.8), hr=0.12, eye=0.6, rune=0.4, hair=0.4,
               feath=0.4, lf=(1.6, 0.0, 0.0), lb=(-2.4, 0.0, 0.0)), 'o'),
    (0.5, dict(CA), 'o'),
    (1.0, dict(CA, y=-3.0, pitch=0.14, x=1.0, ar=(1.65, -0.05), beam=0.8, hd=(1.0, 0.3), hr=0.06, hem=0.4, fr=0.4, lf=(3.0, 3.6, -0.5), lb=(-1.0, 3.0, -0.6)), 'i'),
], frames=[(0.0, 0.0), (0.5, 0.3), (1.0, 0.0)], seg=[('windup', 3)], lead={'windup': 0.05}, fps=10, rest=REST)

# ---- geri sekiş (illusionist / charmer kaçışı; dikey hız evresi, 4 kare): itişle havalanır, toplanır, etek yukarı
# kabarır, inişe uzanır, çöküp oturur
SEQS['hop'] = Seq([
    (0.0, dict(R0, y=-1.5, pitch=-0.22, lf=(3.0, 1.2, -0.3), lb=(0.6, 0.4, -0.5), ar=(1.9, 0.4), hd=(-0.3, 0.0), hr=0.05, hem=-1.0, flr=0.3,
               fr=-1.0, dk=(2.0, -2.0), drot=-0.3, hair=-0.6), 'o'),
    (0.4, dict(R0, y=-3.0, pitch=-0.1, fk=1.0, lf=(3.2, 6.0, 0.4), lb=(0.0, 5.4, 0.3), ar=(2.2, 0.3), hd=(0.0, 0.3), hr=0.08, hem=-0.6, flr=0.8,
               hl=1.4, fr=-0.6, dk=(1.0, -3.0), drot=-0.4, hair=-0.3, feath=0.3), 'io'),
    (0.7, dict(R0, y=-2.0, pitch=0.04, fk=0.6, lf=(2.4, 3.0, 0.2), lb=(-2.6, 2.4, 0.1), ar=(1.6, 0.4), hd=(0.4, 0.5), hr=0.1, hem=-0.2, flr=0.9,
               hl=2.6, fr=0.4, dk=(0.5, -4.0), drot=-0.2, hair=0.6, feath=0.3), 'io'),
    (1.0, dict(R0, y=3.0, pitch=0.18, lf=(2.2, 0.0, 0.0), lb=(-3.2, 0.0, 0.0), ar=(1.1, 0.6), hd=(0.8, 0.8), hr=0.14, hem=0.5, flr=0.2,
               fr=0.6, dk=(0.0, 1.0), drot=0.3, sq=0.5, hair=0.8), 'o'),
], frames=[(0.0, 0.0), (0.4, 0.3), (0.7, 0.58), (1.0, 0.85)], seg=[('air', 4)], fps=10, rest=REST)

# ---- geri takla (archer kaçışı; dikey hız evresi, 5 kare): kalça çevresinde tam geri dönüş, toplanmış bacaklar,
# kabaran etek; ayaküstü çömelerek iner
_FL = dict(R0, fk=1.0, lf=(3.0, 7.0, 0.6), lb=(1.0, 6.4, 0.5), ar=(1.2, 1.4), hd=(0.6, 0.8), hr=0.15, flr=0.8, hl=1.0, fr=0.4,
           dk=(1.5, 1.0), drot=0.6, feath=0.2, hem=0.3, hair=-0.4)
SEQS['flip'] = Seq([
    (0.0, dict(R0, y=-2.0, roll=-0.45, pitch=-0.12, lf=(2.4, 1.6, -0.4), lb=(0.4, 0.6, -0.6), ar=(2.4, 0.3), hd=(-0.6, -0.2), hr=-0.15,
               hem=-0.8, flr=0.3, fr=-0.9, dk=(2.0, -2.0), drot=-0.4, hair=-0.8), 'o'),
    (0.3, dict(_FL, y=-13.0, roll=-2.0), 'l'),
    (0.52, dict(_FL, y=-17.0, roll=-3.5, flr=1.0), 'l'),
    (0.74, dict(_FL, y=-12.0, roll=-5.0, fk=0.6, lf=(3.0, 4.0, 0.3), lb=(-0.6, 3.6, 0.2), ar=(1.8, 0.6)), 'l'),
    (1.0, dict(R0, y=3.2, roll=-6.283, pitch=0.24, lf=(2.6, 0.0, 0.0), lb=(-3.4, 0.0, 0.0), ar=(1.2, 0.6), hd=(0.8, 0.8), hr=0.14,
               hem=0.6, flr=0.25, fr=0.7, dk=(0.0, 1.0), drot=0.3, sq=0.5, hair=0.6), 'o'),
], frames=[(0.0, 0.0), (0.3, 0.2), (0.52, 0.42), (0.74, 0.62), (1.0, 0.84)], seg=[('air', 5)], fps=12, rest=REST)

# ---- belirme (ışınlanma sonrası "recover", st 0,35; 4 kare): duman topağından çömelik doğar, esneyerek kalkar,
# etek ve tüyler savrulup oturur
SEQS['appear'] = Seq([
    (0.0, dict(R0, smoke=1.0, y=5.0, sq=0.6, pitch=0.3, hd=(1.0, 1.4), hr=0.3, ar=(0.3, 1.2), cast=0.0, flr=0.6, eyek=0.4,
               lf=(2.0, 0.0, 0.0), lb=(-3.0, 0.0, 0.0), dk=(1.0, 2.0)), 'o'),
    (0.35, dict(R0, smoke=0.55, y=0.5, sq=-0.45, pitch=-0.08, hd=(-0.4, -0.4), hr=-0.12, ar=(2.2, 0.5), cast=0.6, flr=0.8, hl=1.2, feath=1.0,
                eye=0.8, hair=1.0, fr=-0.6, lf=(1.2, 0.0, 0.0), lb=(-2.0, 0.0, 0.0), dk=(0.5, -2.0), drot=-0.3), 'o'),
    (0.65, dict(R0, smoke=0.2, y=-0.3, sq=-0.12, pitch=-0.03, hd=(0.0, -0.2), ar=(1.2, 0.6), cast=0.4, flr=0.3, feath=0.4, eye=0.3, hair=0.3,
                fr=0.4, hem=0.3, dk=(0.0, -0.8)), 'io'),
    (1.0, dict(R0, sq=0.06, y=0.3, hem=-0.1, fr=-0.1), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.25), (0.65, 0.55), (1.0, 0.8)], seg=[('recover', 4)], fps=10, rest=REST)

# ---- hafif sarsılma (3 kare, 0,22 sn): geri silkinir, baş geriye, göz kısılır, el ve davul savrulur, küre söner
SEQS['hurt'] = Seq([
    (0.0, dict(R0, x=-1.6, y=1.0, pitch=-0.3, hd=(-1.4, -0.4), hr=-0.32, blink=1.0, ar=(2.3, 0.7), cast=0.0, flick=-0.4, dk=(-1.5, -2.0),
               drot=0.6, hem=-1.0, fr=-1.0, feath=-0.4, hair=-0.8, lf=(-0.4, 0.0, 0.0), lb=(-2.6, 0.0, 0.0)), 'o'),
    (0.5, dict(R0, x=-0.8, y=0.6, pitch=-0.12, hd=(-0.5, 0.0), hr=-0.12, blink=0.6, ar=(1.4, 0.8), dk=(-0.5, -0.8), drot=0.25, hem=-0.2, fr=-0.1,
               hair=-0.2, lf=(0.0, 0.0, 0.0), lb=(-2.4, 0.0, 0.0)), 'o'),
    (1.0, dict(R0, x=-0.2, y=0.2, hem=0.25, fr=0.3, lf=(0.4, 0.0, 0.0), lb=(-2.0, 0.0, 0.0)), 'o'),
], frames=[(0.0, 0.0), (0.5, 0.35), (1.0, 0.7)], fps=12, rest=REST)

# ---- ağır sendeleme (4 kare, 0,45 sn): darbeyle geriye savrulur, ön ayak yerden kesilir, arka ayak geri basar, davul
# havaya kalkar; sonra öne kamburlaşıp toparlanır
SEQS['hurt_big'] = Seq([
    (0.0, dict(R0, x=-3.0, y=0.4, pitch=-0.5, roll=-0.08, hd=(-1.8, -0.6), hr=-0.5, blink=1.0, ar=(2.8, 0.5), cast=0.0, orb=0.5, dk=(-2.0, -4.5),
               drot=1.0, hem=-1.6, flr=0.5, fr=-1.4, feath=-0.6, hair=-1.2, lf=(1.0, 2.6, 0.6), lb=(-5.0, 0.0, 0.0)), 'o'),
    (0.35, dict(R0, x=-3.4, y=2.0, pitch=-0.3, roll=-0.03, hd=(-1.0, 0.0), hr=-0.25, blink=0.9, ar=(2.0, 0.8), cast=0.0, orb=0.6, dk=(-1.5, -2.0),
                drot=0.6, hem=-0.8, flr=0.3, fr=-0.8, hair=-0.6, lf=(-1.0, 0.6, 0.2), lb=(-5.4, 0.0, 0.0)), 'io'),
    (0.7, dict(R0, x=-2.4, y=2.4, pitch=0.2, hd=(0.8, 0.8), hr=0.18, blink=0.4, ar=(0.9, 0.8), dk=(0.0, 0.5), drot=0.0, hem=0.6, fr=0.7,
               hair=0.5, lf=(-0.2, 0.0, 0.0), lb=(-5.0, 0.0, 0.0)), 'o'),
    (1.0, dict(R0, x=-1.2, y=0.6, pitch=0.05, hd=(0.2, 0.2), hr=0.04, hem=0.1, fr=0.1, lf=(-0.4, 0.0, 0.0), lb=(-3.2, 0.0, 0.0)), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.25), (0.7, 0.55), (1.0, 0.8)], fps=10, rest=REST)


# ---- duruş kırık / sersem (6 kare döngü): baş sarkık, gövde sallanır, kollar ve davul gevşek, küre cızırdar, kıvılcım döner
def _stun(t):
    s = math.sin(t * math.tau)
    c = math.cos(t * math.tau)
    return dict(x=1.2 * s, y=2.4 + 0.7 * c, pitch=0.26 + 0.07 * c, hd=(0.8 + 0.4 * s, 1.8), hr=0.42 + 0.14 * s, blink=0.6, ar=(0.15 + 0.15 * s, 0.2),
                cast=0.0, orb=0.45, flick=0.3 * s, dk=(1.5, 4.5 + 0.6 * c), drot=0.7 + 0.15 * s, hem=-0.6 * s, fr=-0.7 * c, daze=1.0,
                ph=t * math.tau, feath=-0.3, hair=-0.3 * s, lf=(0.8 + 0.6 * max(0.0, s), 0.0, 0.0), lb=(-2.6 + 0.6 * c, 0.0, 0.0))


SEQS['stun'] = Seq([(i / 12, _stun(i / 12), 'l') for i in range(13)], n=6, fps=6, loop=True, rest=REST)

# ---- havaya savrulma (dikey hız evresi; 4 kare): geriye devrilerek döner, kollar-bacaklar savrulur, etek kabarır
SEQS['launch'] = Seq([
    (0.0, dict(R0, y=-3.0, roll=-0.4, pitch=-0.25, fk=1.0, lf=(3.0, 3.6, 0.5), lb=(-1.0, 2.0, 0.3), ar=(2.7, 0.6), cast=0.0, orb=0.5, hd=(-1.2, -0.4),
               hr=-0.4, blink=1.0, dk=(-2.0, -4.0), drot=0.9, hem=0.6, flr=0.8, hl=2.0, fr=-0.6, hair=-1.0, feath=-0.4), 'o'),
    (0.4, dict(R0, y=-4.0, roll=-1.0, pitch=-0.15, fk=1.0, lf=(2.6, 6.0, 0.8), lb=(-0.4, 4.6, 0.6), ar=(2.2, 1.0), cast=0.0, orb=0.5, hd=(-0.8, 0.0),
               hr=-0.25, blink=0.9, dk=(-1.0, -5.0), drot=1.3, hem=0.8, flr=1.0, hl=2.4, fr=-0.4, hair=-0.6), 'io'),
    (0.7, dict(R0, y=-3.0, roll=-0.7, pitch=0.0, fk=0.8, lf=(3.6, 3.0, 0.2), lb=(-2.6, 3.8, 0.1), ar=(1.6, 0.6), cast=0.0, orb=0.5, hd=(0.0, 0.4),
               hr=0.0, blink=0.5, dk=(0.0, -3.0), drot=0.8, hem=0.4, flr=0.8, hl=2.0, fr=0.3, hair=0.3), 'io'),
    (1.0, dict(R0, y=-1.0, roll=-0.25, pitch=0.12, fk=0.4, lf=(3.0, 1.6, 0.0), lb=(-2.8, 1.0, 0.0), ar=(1.2, 0.6), cast=0.0, orb=0.6, hd=(0.6, 0.6),
               hr=0.1, blink=0.3, dk=(0.0, -1.0), drot=0.4, hem=0.2, flr=0.5, hl=1.2, fr=0.5, hair=0.5), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.25), (0.65, 0.55), (1.0, 0.82)], seg=[('air', 4)], fps=10, rest=REST)

# ---- kalkış (savrulma sonrası; 4 kare, 0,5 sn): diz çökmüş, eğik; doğrulur, eteğini silkeler
SEQS['getup'] = Seq([
    (0.0, dict(R0, y=7.0, pitch=0.62, hd=(1.4, 1.2), hr=0.3, blink=0.8, ar=(0.4, 0.2), cast=0.0, orb=0.4, dk=(2.0, 5.0), drot=0.6, hem=0.3,
               fr=0.3, lf=(3.0, 0.0, 0.0), lb=(-4.6, 0.0, -0.6), feath=-0.4), 'o'),
    (0.35, dict(R0, y=4.0, pitch=0.42, hd=(1.0, 1.0), hr=0.2, blink=0.4, ar=(0.6, 0.4), cast=0.1, orb=0.6, dk=(1.5, 2.5), drot=0.4, hem=0.4,
                fr=0.5, lf=(2.6, 0.0, 0.0), lb=(-3.4, 0.0, -0.3)), 'o'),
    (0.65, dict(R0, y=0.6, pitch=0.04, hd=(-0.2, -0.2), hr=-0.12, ar=(1.0, 0.7), cast=0.2, dk=(0.0, -1.0), drot=-0.2, hem=-0.9, flr=0.4,
                fr=-0.9, feath=0.4, hair=-0.8, lf=(1.2, 0.0, 0.0), lb=(-2.2, 0.0, 0.0)), 'io'),
    (1.0, dict(R0, y=0.3, hem=0.3, fr=0.4, hair=0.3), 'o'),
], frames=[(0.0, 0.0), (0.35, 0.3), (0.65, 0.6), (1.0, 0.85)], fps=10, rest=REST)

# ---- ölüm (8 kare, 0,9 sn): darbeyle geri şahlanır (lanet küresi patlar), dizleri çözülür, öne eğilip diz çöker,
# boş kaftan söner ve yere yığılır, davul düşüp yuvarlanır, ruh telleri yükselip dağılır
_DE = dict(R0, blink=1.0, orb=0.0, cast=0.0, dwb=1.0, lg=0.0, lf=(3.0, 0.0, 0.0), lb=(-4.4, 0.0, -0.8))
SEQS['death'] = Seq([
    (0.0, dict(R0, x=-1.5, y=0.6, pitch=-0.45, hd=(-1.6, -0.6), hr=-0.55, blink=1.0, ar=(2.9, 0.4), fing=1.0, cast=1.4, flare=1.0, dk=(-2.5, -5.0),
               drot=1.0, hem=-1.2, flr=0.6, fr=-1.2, feath=-0.5, hair=-1.2, lf=(1.6, 1.2, 0.4), lb=(-3.6, 0.0, 0.0)), 'o'),
    (0.16, dict(R0, x=-1.8, y=3.0, pitch=-0.25, hd=(-0.8, 0.0), hr=-0.3, blink=1.0, ar=(2.2, 0.8), cast=0.2, orb=0.6, dk=(-2.5, -2.5), drot=1.2,
                hem=-0.6, flr=0.4, fr=-0.6, hair=-0.6, lf=(0.6, 0.0, 0.0), lb=(-3.8, 0.0, 0.0), eyek=0.7), 'io'),
    (0.32, dict(R0, x=-1.6, y=6.0, pitch=0.25, hd=(0.8, 1.0), hr=0.35, blink=1.0, ar=(0.9, 0.5), cast=0.0, orb=0.3, dwb=0.6, dwp=(-12.0, -8.0), drot=1.6,
                hem=0.4, flr=0.2, fr=0.5, hair=0.4, lf=(2.6, 0.0, 0.0), lb=(-4.0, 0.0, -0.5), eyek=0.5), 'i2'),
    (0.46, dict(_DE, x=-1.4, y=8.0, pitch=0.55, tsy=0.88, hd=(1.4, 1.4), hr=0.5, ar=(1.0, 0.3), dwp=(-13.0, -6.5), drot=2.4, hem=0.4, fr=0.6,
                eyek=0.3, wisp=0.2), 'i'),
    (0.58, dict(_DE, x=-1.2, y=9.6, pitch=0.7, tsy=0.72, tsx=1.1, hd=(1.6, 1.8), hr=0.6, ar=(1.35, 0.05), dwp=(-14.5, -6.6), drot=3.1, hem=0.2,
                fr=0.3, eyek=0.15, wisp=0.5), 'o'),
    (0.7, dict(_DE, x=-1.0, y=10.4, pitch=0.78, tsy=0.6, tsx=1.15, hd=(1.8, 2.0), hr=0.65, ar=(1.42, 0.0), dwp=(-15.5, -6.8), drot=3.5, hem=0.1,
               fr=0.2, eyek=0.0, wisp=0.85), 'io'),
    (0.85, dict(_DE, x=-1.0, y=10.8, pitch=0.8, tsy=0.55, tsx=1.18, hd=(1.8, 2.0), hr=0.65, ar=(1.43, 0.0), dwp=(-15.8, -6.8), drot=3.6,
                eyek=0.0, wisp=1.15), 'o'),
    (1.0, dict(_DE, x=-1.0, y=11.0, pitch=0.8, tsy=0.52, tsx=1.2, hd=(1.8, 2.0), hr=0.65, ar=(1.43, 0.0), dwp=(-15.8, -6.8), drot=3.6,
               eyek=0.0, wisp=1.5), 'o'),
], frames=[(0.0, 0.0), (0.16, 0.1), (0.32, 0.22), (0.46, 0.34), (0.58, 0.46), (0.7, 0.58), (0.85, 0.72), (1.0, 0.88)], fps=10, rest=REST)

DURUM = {
    # ---- tepkiler (Enemy._anim_tick öncelikli anahtarları)
    '_hurt': {'a': 'hurt', 'u': 'up', 'd': 0.22},
    '_hurt_big': {'a': 'hurt_big', 'u': 'up', 'd': 0.45},
    '_break': {'a': 'stun', 'u': 'loop'},
    '_launch': {'a': 'launch', 'u': 'vy'},
    '_getup': {'a': 'getup', 'u': 'up', 'd': 0.5},
    '_death': {'a': 'death', 'u': 'up', 'd': 0.9},
    '_turn': {'a': 'turn', 'u': 'up', 'd': 0.2},
    '_roar': {'a': 'cast_aa', 'u': 'up', 'd': 0.8},
    # ---- illusionist (Kara Kam) ve ortak: büyü, ışınlanma sonrası belirme, kaçış sekişi
    'windup': {'a': 'cast', 's': 'windup', 'u': 'st'},
    'windup!!': {'a': 'cast_aa', 's': 'windup', 'u': 'st'},
    'attack': {'a': 'cast', 's': 'strike', 'u': 'st'},
    'chase>recover': {'a': 'appear', 's': 'recover', 'u': 'st'},     # _blink_away: dumandan belirme (st 0,35)
    'idle>recover': {'a': 'appear', 's': 'recover', 'u': 'st'},
    'recover': {'a': 'appear', 's': 'recover', 'u': 'st'},
    'evade': {'a': 'hop', 'u': 'vy'},
    # ---- archer (Kurgan Kamı): ruh yayı, geri takla
    'archer:windup': {'a': 'bow', 's': 'windup', 'u': 'st'},
    'archer:windup!!': {'a': 'bow_aa', 's': 'windup', 'u': 'st'},
    'archer:attack': {'a': 'bow', 's': 'strike', 'u': 'st'},
    'archer:evade': {'a': 'flip', 'u': 'vy'},
    # ---- charmer (Erlik'in Kızı): büyü bağı (charm) ya da iki güdümlü küre (curse)
    'charmer:windup/charm': {'a': 'charm', 's': 'windup', 'u': 'st'},
    'charmer:windup/charm!!': {'a': 'charm_aa', 's': 'windup', 'u': 'st'},
    'charm': {'a': 'charm', 's': 'channel', 'u': 'st'},
    'charm>recover': {'a': 'charm', 's': 'recover', 'u': 'st'},
    'charmer:recover/charm': {'a': 'charm', 's': 'recover', 'u': 'st'},
    'charmer:windup/curse': {'a': 'curse', 's': 'windup', 'u': 'st'},
    'charmer:windup/curse!!': {'a': 'cast_aa', 's': 'windup', 'u': 'st'},
    'charmer:attack': {'a': 'curse', 's': 'strike', 'u': 'st'},
    'attack>recover': {'a': 'curse', 's': 'recover', 'u': 'st'},
    'charmer:recover/curse': {'a': 'curse', 's': 'recover', 'u': 'st'},
    # ---- kamikaze (Işıltı Kamı; başka sayfa): fitil = zırhlı büyü hazırlığı (yükselip kabarır)
    'kamikaze:windup': {'a': 'cast_aa', 's': 'windup', 'u': 'st'},
}


def render_frame(anim, i, var='arcura', ss=3):
    V = VARIANTS[var]
    p = SEQS[anim].pose(i)
    cv = yk.occlude_glow(ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss))
    info = draw(cv, p, V)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info
