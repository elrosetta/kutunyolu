"""Yurt sakinleri — stil v2 "mürekkep-cel" (inkkit.py). v1: yurt.draw_human / NPC_STYLES / NPC_ANIMS.

Üç kişi, yakından görüldükleri için ayrıntılı: hepsi yüz SOLA (oyuncu soldan gelir; NPC.gd v1 ile aynı flip kuralı),
ayak merkezi (0, 0). Animasyonlar v1 ile aynı (idle 6 kare 8 fps döngü, talk 4 kare 10 fps döngü), çapalar
'hand' (ön el) ve 'head' (baş merkezi).

* Umay Ana: uzun boylu, dingin tanrıça. Ak keçe üstlük + yerlere değen ak entari (turkuaz-altın kenar işlemesi),
  gümüş-ak örgülü saç, altın alın tacından yükselen geyik boynuzları (boynuzlarda çaputlar ve altın pullar), ak kayın
  asa (tepesinde Kut ışığı, ışır), çevresinde dolaşan Kut zerreleri. Konuşurken arka eli kutsama için kalkar.
* Demirci Kam Kuzgun: geniş omuzlu, kalın kollu kam-demirci. Kuzgun tüylü kam başlığı, örgülü kara sakal, kızıl kaftan
  (kollar sıvalı), deri önlük (kam çıngırakları ve demir muskalar), kemerde kerpeten, elinde ağır balyoz (başında
  ocakta kızarmış runa, ışır). Konuşurken balyozu kaldırır.
* Ozan Bilge Kopuz: yaşlı ozan; uzun ak sakal, ak keçe börk (kara kalkık kenar), işlemeli devetüyü çapan, elinde
  uzun saplı kopuz (tellere dokunan el idle'da çalar), boynunda nazar boncuğu. Konuşurken kopuzu kaldırır.
"""
import math

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_arm, lerp2, chain
from bengu_ink import along
from yurt import NPC_ANIMS
import wolfkit as wk

TEX = 4.0
CELL = (320, 416)        # dünya 80 x 104 (v1: 64 x 88; boynuz ve kalkık balyoz için pay)
FEET = (160, 400)        # dünya (40, 100)

SKIN = Ink('#e2a982', '#9a5a52', '#ffd8b8', '#5a3038', name='ten')
SKIN_D = Ink('#c48a64', '#7a4238', '#ecb48a', '#48262c', name='yanık ten')
SKIN_O = Ink('#e6b496', '#a06a60', '#ffe2c8', '#603844', name='yaşlı ten')

# Umay
WHITE = Ink('#eef0f2', '#a2a8c4', '#ffffff', '#6a6e90', name='ak giysi')
WHITE_B = WHITE.darker(0.8)
FELTW = Ink('#e4ddd0', '#9c92a0', '#fffaf0', '#625a70', name='ak keçe')
TURQ = Ink('#2ab8b0', '#0e5a68', '#9ff6e2', name='turkuaz işleme')
GOLD = Ink('#e6b24c', '#94561e', '#fff4c0', kind='metal', name='altın')
ANTLER = Ink('#f0e4c8', '#a8927a', '#fffbee', '#6a5a50', name='boynuz')
HAIRW = Ink('#d8dce6', '#8a90aa', '#ffffff', '#5a5e7c', name='gümüş saç')
BIRCH = Ink('#ece8dc', '#9a968c', '#ffffff', name='kayın asa')
RIB_R = (0.80, 0.16, 0.18)
KUT = (0.55, 1.0, 1.0)
KUT_GL = (0.25, 0.9, 1.0)

# Demirci
KAFTAN = Ink('#a83236', '#561a2e', '#d85a50', '#2e0e1e', name='kızıl kaftan')
KAFTAN_B = KAFTAN.darker(0.74)
APRON = Ink('#7c5236', '#3a2420', '#a87a52', '#22141a', name='deri önlük')
IRON = Ink('#7a7e8c', '#363846', '#c4c8d6', '#20222c', kind='metal', name='demir')
RAVEN = Ink('#2c2a3a', '#14131c', '#5e5a7a', name='kuzgun tüyü')
BEARD_K = Ink('#2a2228', '#141016', '#5a4a52', name='kara sakal')
PANTS = Ink('#3e3a4a', '#1e1c28', '#5e5a6e', name='şalvar')
BOOT = Ink('#5a3c2e', '#28181a', '#866050', name='çizme')
WOOD = Ink('#b08458', '#5a3a2a', '#e0b888', name='dişbudak sap')
EMBER = (1.0, 0.55, 0.18)
EMBER_GL = (1.0, 0.42, 0.08)

# Ozan
CHAPAN = Ink('#b89a6c', '#62483e', '#e2c896', '#36262a', name='devetüyü çapan')
CHAPAN_B = CHAPAN.darker(0.76)
BORK = Ink('#ece4d2', '#a29680', '#fffcf0', name='ak keçe börk')
BORK_IN = Ink('#2a2630', '#141218', '#4a4656', name='börk kenarı')
BEARD_W = Ink('#eceef2', '#9ea4bc', '#ffffff', '#6a6e8a', name='ak sakal')
KOPUZ = Ink('#a06438', '#4c2a1e', '#d49460', '#2a1612', name='kopuz')
EMBR_R = Ink('#9a2a34', '#4c1222', '#c8484a', name='kırmızı işleme')
NAZAR = (0.16, 0.36, 0.85)


# ------------------------------------------------------------ ortak parçalar (yüz sola)
def _face(cv, hd, skin, z, eye_open=1.0, old=False, brow_col=None, mouth=0.0):
    """Profil yüz (sola): alın, burun, dudak, çene; badem göz (koyu iris + parıltı), kaş, kulak sağda."""
    hx, hy = hd
    face = cv.blob([(hx + 3.6, hy - 3.6), (hx + 0.4, hy - 4.8), (hx - 2.8, hy - 4.0), (hx - 4.2, hy - 1.8), (hx - 4.0, hy - 0.4),
                    (hx - 5.2, hy + 1.0, 0.4), (hx - 4.2, hy + 1.6), (hx - 4.4, hy + 2.6), (hx - 3.8, hy + 3.4), (hx - 3.9, hy + 4.0),
                    (hx - 2.6, hy + 5.0), (hx - 0.4, hy + 5.0), (hx + 2.6, hy + 3.4), (hx + 4.0, hy + 0.4)])
    det = [('ink', [(hx - 4.0, hy + 2.6), (hx - 3.0, hy + 2.75)], 1.1, (0.2, 0.5)),                         # dudak
           ('ink', [(hx - 4.4, hy + 1.6), (hx - 3.4, hy + 1.2)], 0.9, (0.3, 0.4)),                          # burun kanadı
           ('shade', cv.blob([(hx + 1.2, hy + 4.4), (hx + 3.6, hy + 0.6), (hx + 4.0, hy + 2.6), (hx + 2.2, hy + 4.6)]))]
    if old:
        det.append(('ink', [(hx - 2.6, hy + 0.6), (hx - 2.0, hy + 2.0)], 0.9, (0.3, 0.5)))   # yanak çizgisi
        det.append(('ink', [(hx - 1.4, hy - 1.0), (hx - 0.6, hy - 0.6)], 0.8, (0.3, 0.5)))
    cv.shape(face, skin, z=z, sd=1.6, hi=0.3, details=det, bounce=0.3)
    # kulak
    cv.shape(cv.blob([(hx + 2.2, hy - 0.8), (hx + 3.6, hy - 1.2), (hx + 3.8, hy + 1.2), (hx + 2.6, hy + 1.6)]), skin, z=z + 0.1, sd=0.6, ol=0.8,
             details=[('ink', [(hx + 2.7, hy - 0.4), (hx + 3.2, hy + 0.6)], 0.8)])
    # göz
    ec = (hx - 2.2, hy - 0.6)
    if eye_open > 0.5:
        cv.fill(cv.blob([(ec[0] - 1.1, ec[1] + 0.1, 0.0), (ec[0], ec[1] - 0.55), (ec[0] + 0.8, ec[1] - 0.1, 0.0), (ec[0] - 0.1, ec[1] + 0.45)]),
                (0.96, 0.94, 0.9), z=z + 0.2)
        cv.fill(cv.ellipse((ec[0] - 0.3, ec[1] - 0.05), 0.45, 0.5), (0.18, 0.12, 0.12), z=z + 0.25)
        cv.fill(cv.ellipse((ec[0] - 0.45, ec[1] - 0.25), 0.14, 0.14), (1.0, 1.0, 1.0), z=z + 0.3)
        cv.stroke([(ec[0] - 1.2, ec[1] - 0.05), (ec[0], ec[1] - 0.65), (ec[0] + 0.9, ec[1] - 0.2)], 1.3, z=z + 0.32, taper=(0.3, 0.2))
    else:   # dingin, yarı kapalı (Umay)
        cv.stroke([(ec[0] - 1.1, ec[1] + 0.1), (ec[0] - 0.1, ec[1] + 0.35), (ec[0] + 0.8, ec[1] + 0.05)], 1.5, z=z + 0.3, taper=(0.3, 0.3))
        cv.stroke([(ec[0] - 1.0, ec[1] + 0.25), (ec[0] - 1.6, ec[1] + 0.6)], 0.9, z=z + 0.3, taper=(0.1, 0.9))
    cv.stroke([(ec[0] - 1.4, ec[1] - 1.5), (ec[0] - 0.2, ec[1] - 1.9), (ec[0] + 1.2, ec[1] - 1.6)], 1.6, z=z + 0.33,
              col=brow_col or INK, taper=(0.2, 0.6))
    if mouth > 0.2:
        cv.fill(cv.blob([(hx - 3.9, hy + 2.6), (hx - 3.0, hy + 2.7), (hx - 3.2, hy + 3.2 + mouth * 0.6), (hx - 3.8, hy + 3.1)]), (0.35, 0.1, 0.12), z=z + 0.2)
    return face


def _hand(cv, e, h, skin, z, open_=0.0, near=True):
    """Eldeki avuç: kapalı (tutuyor) ya da açık (kutsama/el hareketi)."""
    m = skin if near else skin.darker(0.8)
    if open_ > 0.5:
        palm = cv.blob([along(e, h, 0.92, -1.2), along(e, h, 0.92, 1.3), along(e, h, 1.12, 1.6), along(e, h, 1.42, 1.2), along(e, h, 1.46, 0.0),
                        along(e, h, 1.42, -0.9), along(e, h, 1.16, -1.5)])
        det = [('ink', [along(e, h, 1.18, o), along(e, h, 1.42, o)], 0.8, (0.05, 0.6)) for o in (-0.4, 0.4)]
        cv.shape(palm, m, z=z, sd=0.8, hi=0.3, details=det, ol=0.85)
        th = cv.blob([along(e, h, 1.0, 1.2), along(e, h, 1.12, 2.4), along(e, h, 1.22, 2.2), along(e, h, 1.12, 1.2)])
        cv.shape(th, m, z=z + 0.05, sd=0.5, ol=0.8)
    else:
        fist = cv.blob([along(e, h, 0.9, -1.4), along(e, h, 0.9, 1.5), along(e, h, 1.05, 1.9), along(e, h, 1.22, 1.5), along(e, h, 1.26, 0.0),
                        along(e, h, 1.2, -1.3), along(e, h, 1.05, -1.7)])
        det = [('ink', [along(e, h, 1.1, o), along(e, h, 1.24, o)], 0.8, (0.05, 0.6)) for o in (-0.6, 0.3)]
        cv.shape(fist, m, z=z, sd=0.9, hi=0.3, details=det, ol=0.85)


def _sleeve(cv, sh, e, h, m, z, wide=0.0, cuff=None, near=True, rolled=False, skin=None):
    """Kol: bol yen (wide > 0: aşağı sarkan geniş ağız), dirsek kıvrımları; rolled: sıvalı kol (ön kol çıplak)."""
    up = cv.blob([along(sh, e, t, o) for t, o in ((-0.1, 3.0), (0.3, 3.2), (0.8, 2.7), (1.06, 2.4), (1.06, -2.3), (0.6, -2.8), (0.1, -3.2), (-0.12, -2.4))])
    det = cv.fold([along(sh, e, 0.65, -2.6), along(sh, e, 0.78, -1.0), along(sh, e, 0.88, 0.4)], 0.5, 1.1, 1, (0.1, 0.7)) if near else []
    cv.shape(up, m, z=z, sd=2.0, details=det, bounce=0.25 if near else 0.0)
    if rolled:
        fo = cv.blob([along(e, h, t, o) for t, o in ((-0.05, 2.4), (0.35, 2.6), (0.8, 1.9), (0.98, 1.7), (0.98, -1.7), (0.6, -2.2), (0.2, -2.6), (-0.08, -2.0))])
        cv.shape(fo, skin, z=z + 0.1, sd=1.6, hi=0.3 if near else 0.0,
                 details=[('ink', [along(e, h, 0.25, 1.2), along(e, h, 0.6, 1.0)], 0.9, (0.3, 0.5))] if near else ())
        roll = cv.blob([along(e, h, -0.1, 3.0), along(e, h, 0.12, 3.0), along(e, h, 0.14, -2.8), along(e, h, -0.08, -3.0)])
        cv.shape(roll, m, z=z + 0.15, sd=0.8, ol=0.9, details=[('ink', [along(e, h, 0.02, -2.6), along(e, h, 0.03, 2.6)], 0.9)])
        return
    pts = [(-0.05, 2.6), (0.4, 2.8 + wide * 0.4), (0.82, 2.6 + wide), (0.95, 2.8 + wide * 1.4), (0.92, -2.2 - wide * 0.3),
           (0.5, -2.4), (0.1, -2.7), (-0.08, -2.0)]
    fo = cv.blob([along(e, h, t, o) for t, o in pts])
    det = []
    if near:
        det += cv.fold([along(e, h, 0.2, 2.2), along(e, h, 0.5, 2.0 + wide * 0.4), along(e, h, 0.85, 2.4 + wide)], 0.6, 1.1, -1, (0.3, 0.3))
        det += cv.fold([along(e, h, 0.15, -2.0), along(e, h, 0.4, -1.4)], 0.4, 1.0, 1, (0.1, 0.7))
    cv.shape(fo, m, z=z + 0.1, sd=1.8, details=det, bounce=0.25 if near else 0.0)
    if cuff is not None:
        cf = ik.isect(fo, cv.poly([along(e, h, 0.8, -5), along(e, h, 0.8, 6 + wide), along(e, h, 1.0, 6 + wide), along(e, h, 1.0, -5)]))
        cv.shape(cf, cuff, z=z + 0.15, sd=0.6, hi=0.2, ol=0.6)


def _robe(cv, hip, neck, m, z, hem_w=11.0, sway=0.0, front_open=False, shadows=(), dets=(), bot=0.0):
    """Yere değen uzun giysi (A biçimi): omuzdan etek ucuna, etek ucu dalgalı; sway etek ucunu kaydırır."""
    hx, hy = hip
    nx, ny = neck
    top_l, top_r = (nx - 4.6, ny + 2.0), (nx + 4.8, ny + 2.2)
    hem = []
    for j in range(7):
        t = j / 6
        x = hx - hem_w + 2 * hem_w * t + sway * (1 - t * 0.5)
        y = bot - 0.2 + (0.7 if j % 2 else 0.0) * (1 if 0 < j < 6 else 0)
        hem.append((x, y))
    pts = [top_l, (hx - 6.6, hy - 3.0), hem[0] + (0.0,)] + [(x, y) for x, y in hem[1:-1]] + [hem[-1] + (0.0,), (hx + 6.8, hy - 3.0), top_r]
    path = cv.blob(pts)
    det = list(dets)
    for j, (t, o) in enumerate(((0.15, -1.0), (0.35, 0.4), (0.62, -0.4), (0.85, 0.6))):
        top_ = (hx - 4.5 + 9 * t, hy + 1.0)
        b_ = hem[min(6, int(t * 6 + 0.5))]
        det += cv.fold([top_, (lerp2(top_, b_, 0.55)[0] + o, lerp2(top_, b_, 0.55)[1]), (b_[0], b_[1] - 0.4)], 0.9 if j % 2 else 0.6, 1.2, -1 if j % 2 else 1, (0.6, 0.05))
    cv.shape(path, m, z=z, sd=4.0, details=det, hatch=0.3, deep=0.2, bounce=0.35, shadows=shadows)
    return path, hem


def _hem_band(cv, path, hem, m, z, w=1.4, dy=-1.0):
    strip = ik.union(*[cv.capsule((x, y + dy), (x2, y2 + dy), w, w) for (x, y), (x2, y2) in zip(hem, hem[1:])])
    cv.shape(ik.isect(path, strip), m, z=z, sd=0.7, hi=0.25, ol=0.55)


# ------------------------------------------------------------ Umay Ana
def draw_umay(cv, p):
    bob, lean, ph = p.get('bob', 0.0), p.get('lean', 0.0), p.get('ph', 0.0)
    talk = p.get('talk', 0.0)
    hip = (0.0, -26.0 + bob * 0.3)
    neck = (hip[0] - math.sin(lean) * 19.0, hip[1] - 19.0 + bob * 0.5)
    hd = (neck[0] - 1.0, neck[1] - 5.4)
    out = {'head': hd}
    # ---- arka saç örgüleri (sırta iner)
    for k in range(2):
        st = chain((hd[0] + 2.6 + k * 1.2, hd[1] + 1.0), 7, 3.6, math.pi * 0.47 - k * 0.05, 0.0, ph + k, 0.08)
        q = [cv.W(s) for s in st]
        cv.shape(ik.taper_path(q, cv.u(2.6 - k * 0.4), (0.05, 0.4)), HAIRW, z=-14 + k * 0.1, sd=0.8, hi=0.3,
                 details=[('ink', [lerp2(st[j], st[j + 1], 0.2), lerp2(st[j], st[j + 1], 0.55)], 0.9, (0.2, 0.2)) for j in range(0, 6)])
        cv.shape(cv.ellipse(st[-1], 0.9, 1.2), GOLD, z=-13.9, sd=0.5, ol=0.7)
    # ---- arka kol (konuşurken kutsama için kalkar)
    sh_b = (neck[0] + 3.0, neck[1] + 3.0)
    ab = p.get('ab', (0.3, 0.5))
    e, h = fk_arm(sh_b, ab[0], ab[1], 9.5, 8.5)
    _sleeve(cv, sh_b, e, h, WHITE_B, -12, wide=1.6, cuff=GOLD.darker(0.8), near=False)
    _hand(cv, e, h, SKIN, -11.6, open_=1.0 if talk > 0.3 else 0.0, near=False)
    # ---- ak entari (yere değer) + keçe üstlük
    sw = math.sin(ph) * 0.5
    robe, hem = _robe(cv, hip, neck, WHITE, 0, hem_w=11.5, sway=sw)
    _hem_band(cv, robe, hem, TURQ, 0.2, w=1.3, dy=-1.2)
    _hem_band(cv, robe, hem, GOLD, 0.25, w=0.45, dy=-2.9)
    # ayak ucu
    cv.shape(cv.blob([(hip[0] - 7.0, -1.2), (hip[0] - 10.4, -1.0), (hip[0] - 11.0, 0.2, 0.0), (hip[0] - 6.6, 0.2, 0.0)]), GOLD.darker(0.7), z=0.1, sd=0.5, ol=0.8)
    # üstlük: omuzdan dize, önü açık; turkuaz kenar
    coat = cv.blob([(neck[0] - 4.8, neck[1] + 1.6), (hip[0] - 7.6, hip[1] + 4.0), (hip[0] - 8.6 + sw, hip[1] + 14.0, 0.0), (hip[0] - 4.0 + sw, hip[1] + 13.0),
                    (hip[0] + 2.0 + sw, hip[1] + 15.0), (hip[0] + 8.6 + sw, hip[1] + 13.6, 0.0), (hip[0] + 8.0, hip[1] - 2.0), (neck[0] + 5.6, neck[1] + 2.0)])
    cdet = cv.fold([(hip[0] + 4.0, hip[1] - 8.0), (hip[0] + 5.4, hip[1] + 2.0), (hip[0] + 5.0, hip[1] + 12.0)], 1.0, 1.3, 1)
    cdet += cv.fold([(hip[0] - 2.0, hip[1] - 2.0), (hip[0] - 1.0, hip[1] + 6.0), (hip[0] + 0.2, hip[1] + 13.0)], 0.7, 1.1, -1)
    cv.shape(coat, FELTW, z=1.0, sd=3.6, details=cdet, bounce=0.35, cast=0.8)
    # üstlük kenar işlemesi: ön açıklık boyunca turkuaz bant + altın nokta motifi
    edge = [(neck[0] - 4.4, neck[1] + 2.0), (hip[0] - 6.8, hip[1] + 4.0), (hip[0] - 7.8 + sw, hip[1] + 13.4)]
    band = ik.isect(coat, ik.taper_path([cv.W(q) for q in edge], cv.u(2.4), prof=lambda s: 1.0))
    cv.shape(band, TURQ, z=1.1, sd=0.6, ol=0.5,
             details=[('col', cv.ellipse(lerp2(edge[0], edge[1], t) if t < 1 else lerp2(edge[1], edge[2], t - 1), 0.4, 0.4), GOLD.hi) for t in (0.2, 0.5, 0.8, 1.2, 1.6)])
    hem2 = [(hip[0] - 8.6 + sw, hip[1] + 14.0), (hip[0] - 4.0 + sw, hip[1] + 13.0), (hip[0] + 2.0 + sw, hip[1] + 15.0), (hip[0] + 8.6 + sw, hip[1] + 13.6)]
    _hem_band(cv, coat, hem2, TURQ, 1.15, w=1.1, dy=-0.8)
    # kemer: dokuma kuşak + altın toka
    belt = cv.blob([(hip[0] - 6.8, hip[1] - 4.4), (hip[0] + 7.4, hip[1] - 4.8), (hip[0] + 7.6, hip[1] - 2.4), (hip[0] - 6.8, hip[1] - 2.0)])
    cv.shape(belt, TURQ, z=1.4, sd=0.8, hi=0.25,
             details=[('ink', [(hip[0] - 6.0 + j * 2.6, hip[1] - 4.3), (hip[0] - 5.0 + j * 2.6, hip[1] - 2.3)], 0.8, (0.1, 0.1)) for j in range(5)])
    cv.shape(cv.ellipse((hip[0] - 3.4, hip[1] - 3.4), 1.6, 1.4), GOLD, z=1.5, sd=0.6, hi=0.3, ol=0.8)
    # göğüs: üstlüğün içinden görünen entari + altın gerdanlık
    cv.shape(cv.blob([(neck[0] - 3.4, neck[1] + 1.2), (neck[0] + 1.6, neck[1] + 1.6), (hip[0] - 0.6, hip[1] - 4.8), (hip[0] - 5.6, hip[1] - 4.6)]),
             WHITE, z=1.2, sd=1.8, details=cv.fold([(neck[0] - 1.4, neck[1] + 3.0), (neck[0] - 2.0, neck[1] + 8.0)], 0.5, 1.0, 1))
    for j in range(5):
        a = math.pi * (0.15 + 0.7 * j / 4)
        c = (neck[0] - 0.6 + math.cos(a) * 3.4, neck[1] + 1.2 + math.sin(a) * 2.4)
        cv.shape(cv.blob([(c[0] - 0.6, c[1] - 0.3), (c[0] + 0.6, c[1] - 0.3), (c[0], c[1] + 1.4, 0.0)]), GOLD, z=1.6, sd=0.3, ol=0.6)
    # ---- baş: yüz + saç + taç + boynuzlar
    cv.shape(cv.limb([neck, (hd[0] + 0.5, hd[1] + 3.0)], [2.0, 2.0]), SKIN, z=2.0, sd=1.0)
    hx, hy = hd
    # saç kütlesi (başın arkası, omuza dökülür)
    hair = cv.blob([(hx + 4.4, hy - 3.6), (hx + 0.6, hy - 5.4), (hx - 3.4, hy - 4.6), (hx - 2.0, hy - 3.0), (hx + 1.2, hy - 2.4), (hx + 2.0, hy + 1.0),
                    (hx + 1.6, hy + 6.0), (hx + 3.6, hy + 10.0, 0.0), (hx + 6.0, hy + 5.0), (hx + 5.6, hy - 0.4)])
    hdt = [('ink', [(hx + 1.0, hy - 4.6), (hx + 3.0, hy - 2.0), (hx + 3.6, hy + 2.0), (hx + 4.0, hy + 7.0)], 1.0, (0.2, 0.6)),
           ('ink', [(hx - 1.4, hy - 4.6), (hx + 1.0, hy - 3.4), (hx + 2.2, hy - 0.4)], 0.9, (0.2, 0.6))]
    cv.shape(hair, HAIRW, z=2.2, sd=1.6, hi=0.4, details=hdt, bounce=0.3)
    _face(cv, hd, SKIN, 2.1, eye_open=0.0, mouth=talk * 0.5)
    # yüzü çerçeveleyen ön perçemler (omuza dökülür) + altın küpe
    for k, (dx, ln) in enumerate(((1.0, 6), (2.2, 7))):
        st = chain((hx + dx, hy - 3.2), ln, 1.9, math.pi * 0.52 + k * 0.04 + math.sin(ph + k) * 0.03, 0.01, ph + k, 0.05)
        cv.shape(ik.taper_path([cv.W(q) for q in st], cv.u(1.5 - k * 0.2), (0.1, 0.7)), HAIRW, z=2.15 + k * 0.01, sd=0.6, hi=0.3, ol=0.7)
    ea = (hx + 2.8, hy + 1.6)
    cv.shape(cv.limb([ea, (ea[0] + 0.1, ea[1] + 1.4)], [0.25, 0.25]), GOLD, z=2.17, sd=0.2, ol=0.5)
    cv.shape(cv.blob([(ea[0] - 0.6, ea[1] + 1.4), (ea[0] + 0.7, ea[1] + 1.4), (ea[0] + 0.05, ea[1] + 3.0, 0.0)]), GOLD, z=2.18, sd=0.3, hi=0.3, ol=0.6)
    # yanak kızarıklığı
    cv.fill(cv.ellipse((hx - 1.8, hy + 1.2), 1.1, 0.6), (0.95, 0.55, 0.5), z=2.16, alpha=0.45)
    # alın işareti (Kut damlası)
    cv.fill(cv.blob([(hx - 3.0, hy - 3.6, 0.0), (hx - 2.5, hy - 3.0), (hx - 3.0, hy - 2.4, 0.0), (hx - 3.5, hy - 3.0)]), KUT, z=2.6, glow=KUT_GL)
    # taç bandı
    band = cv.blob([(hx - 3.4, hy - 4.2), (hx + 0.4, hy - 5.6), (hx + 4.6, hy - 4.6), (hx + 4.6, hy - 3.4), (hx + 0.4, hy - 4.2), (hx - 3.2, hy - 3.0)])
    cv.shape(band, GOLD, z=2.8, sd=0.6, hi=0.35, ol=0.8,
             details=[('col', cv.ellipse((hx + 0.6, hy - 4.7), 0.7, 0.6), (0.2, 0.75, 0.75))])
    # boynuzlar: iki dallı geyik boynuzu (uzak olan arkada, koyu)
    for side, (bx, z_, m) in enumerate(((hx + 2.6, -1.0, ANTLER.darker(0.88)), (hx - 0.8, 3.0, ANTLER))):
        sway = math.sin(ph * 0.5) * 0.02
        lean_ = -0.25 if side else 0.15
        base = (bx, hy - 5.0)
        main = chain(base, 5, 4.0, -math.pi / 2 + lean_ + sway, 0.10 if side == 0 else -0.10, 0, 0.0)
        paths = [ik.taper_path([cv.W(q) for q in main], cv.u(3.0), prof=lambda s: max(0.35, 1.0 - 0.6 * s))]
        for j, (ti, da, ln) in enumerate(((1, -0.9, 4.4), (2, 0.8, 4.0), (3, -0.7, 3.6), (4, 0.6, 2.8))):
            b0 = main[ti]
            a0 = -math.pi / 2 + lean_ + da * (1 if side == 0 else -1)
            tine = chain(b0, 3, ln / 3, a0, -0.18 * (1 if da > 0 else -1), 0, 0.0)
            paths.append(ik.taper_path([cv.W(q) for q in tine], cv.u(2.1), prof=lambda s: max(0.2, 1.0 - 0.78 * s)))
        cv.shape(ik.union(*paths), m, z=z_, sd=0.9, hi=0.35, ol=0.6, soft=0.2, grad=0.0,
                 details=[('ink', [lerp2(main[j], main[j + 1], 0.4), lerp2(main[j], main[j + 1], 0.6)], 0.8, (0.2, 0.2)) for j in range(0, 4, 2)])
        if side == 1:   # çaputlar ve altın pullar
            for j, (ti, col) in enumerate(((1, RIB_R), (3, TURQ.base))):
                q0 = main[ti]
                rib = chain(q0, 3, 1.8, math.pi * 0.55 + math.sin(ph + j) * 0.15, 0.05, ph + j, 0.2)
                cv.shape(ik.taper_path([cv.W(q) for q in rib], cv.u(1.0), (0.05, 0.6)), Ink(col), z=z_ + 0.2, sd=0.4, ol=0.7)
            for ti in (2, 4):
                q0 = main[ti]
                cv.shape(cv.ellipse((q0[0] + 0.6, q0[1] + 1.6), 0.6, 0.75), GOLD, z=z_ + 0.25, sd=0.3, ol=0.7)
    # ---- ön kol + ak kayın asa
    sh_f = (neck[0] - 3.0, neck[1] + 3.0)
    af = p.get('af', (-0.3, 0.6))
    e2, h2 = fk_arm(sh_f, af[0], af[1], 9.5, 8.5)
    out['hand'] = h2
    top = (h2[0] - 1.2, h2[1] - 30.0)
    bot = (h2[0] + 1.0, -0.4)
    staff = cv.limb([bot, lerp2(bot, top, 0.5), top], [1.0, 1.05, 0.9])
    sdet = [('ink', [lerp2(bot, top, t), (lerp2(bot, top, t)[0] + 0.9, lerp2(bot, top, t)[1] + 0.1)], 1.1, (0.1, 0.4)) for t in (0.12, 0.3, 0.47, 0.66, 0.8)]
    cv.shape(staff, BIRCH, z=12, sd=0.9, hi=0.3, details=sdet)
    # asa tepesi: çatallı dal içinde Kut ışığı + dolaşan zerreler
    for da in (-0.5, 0.45):
        br = chain(top, 3, 1.6, -math.pi / 2 + da, -0.4 * (1 if da > 0 else -1), 0, 0.0)
        cv.shape(ik.taper_path([cv.W(q) for q in br], cv.u(0.9), (0.05, 0.8)), BIRCH, z=12.1, sd=0.4, ol=0.7)
    orb_c = (top[0], top[1] - 2.6)
    cv.fill(cv.ellipse(orb_c, 2.0, 2.0), KUT, z=12.3, glow=KUT_GL)
    cv.fill(cv.ellipse((orb_c[0] - 0.5, orb_c[1] - 0.5), 0.8, 0.8), (1, 1, 1), z=12.35, glow=(0.6, 1.0, 1.0))
    for k in range(4):
        a = ph + k * math.tau / 4
        r = 4.6 + math.sin(ph * 2 + k) * 0.6
        q = (orb_c[0] + math.cos(a) * r, orb_c[1] + math.sin(a) * r * 0.55)
        cv.fill(cv.blob([(q[0], q[1] - 0.8, 0.0), (q[0] + 0.45, q[1], 0.0), (q[0], q[1] + 0.8, 0.0), (q[0] - 0.45, q[1], 0.0)]), KUT,
                z=12.4 if math.sin(a) > 0 else -15, glow=KUT_GL)
    # asada çaput
    rib = chain((top[0] + 0.4, top[1] + 4.0), 4, 2.0, math.pi * 0.45 + math.sin(ph) * 0.2, 0.06, ph, 0.25)
    cv.shape(ik.taper_path([cv.W(q) for q in rib], cv.u(1.2), (0.05, 0.6)), Ink(RIB_R), z=12.2, sd=0.4, ol=0.7)
    _sleeve(cv, sh_f, e2, h2, WHITE, 13, wide=2.2, cuff=TURQ)
    _hand(cv, e2, h2, SKIN, 14)
    return out


# ------------------------------------------------------------ Demirci Kam Kuzgun
def draw_demirci(cv, p):
    bob, lean, ph = p.get('bob', 0.0), p.get('lean', 0.0), p.get('ph', 0.0)
    talk = p.get('talk', 0.0)
    hip = (0.0, -23.0 + bob * 0.3)
    neck = (hip[0] - math.sin(lean) * 16.5, hip[1] - 16.5 + bob * 0.5)
    hd = (neck[0] - 1.4, neck[1] - 5.0)
    out = {'head': hd}
    # ---- arka kol
    sh_b = (neck[0] + 4.0, neck[1] + 3.2)
    ab = p.get('ab', (0.3, 0.5))
    e, h = fk_arm(sh_b, ab[0], ab[1], 9.5, 8.5)
    _sleeve(cv, sh_b, e, h, KAFTAN_B, -12, near=False, rolled=True, skin=SKIN_D.darker(0.8))
    _hand(cv, e, h, SKIN_D, -11.6, near=False)
    # ---- bacaklar (şalvar + çizme), geniş duruş
    for dx, zz, m in ((3.6, -9, PANTS.darker(0.75)), (-3.4, -2, PANTS)):
        top_ = (hip[0] + dx * 0.6, hip[1])
        knee = (hip[0] + dx, hip[1] + 11.0)
        ft = (hip[0] + dx * 1.15, -0.2)
        leg = cv.limb([top_, lerp2(top_, knee, 0.5), knee, lerp2(knee, ft, 0.4)], [4.6, 4.8, 4.0, 4.2])
        cv.shape(leg, m, z=zz, sd=2.0, details=cv.fold([lerp2(top_, knee, 0.3), lerp2(top_, knee, 0.7), lerp2(knee, ft, 0.2)], 0.6, 1.1, 1))
        boot = cv.blob([(ft[0] + 3.0, ft[1] - 8.0), (ft[0] - 3.4, ft[1] - 8.0), (ft[0] - 3.6, ft[1] - 2.4), (ft[0] - 6.4, ft[1] - 1.6),
                        (ft[0] - 6.6, ft[1] + 0.2, 0.0), (ft[0] + 3.2, ft[1] + 0.2, 0.0)])
        cv.shape(boot, BOOT if zz > -5 else BOOT.darker(0.75), z=zz + 0.3, sd=1.4, hi=0.3,
                 details=[('ink', [(ft[0] - 3.4, ft[1] - 7.2), (ft[0] + 3.0, ft[1] - 7.2)], 1.4, (0.1, 0.1))])
    # ---- gövde: geniş kızıl kaftan (kısa, dize kadar)
    torso = cv.blob([(neck[0] - 6.4, neck[1] + 2.4), (neck[0] + 6.6, neck[1] + 2.0), (hip[0] + 8.2, hip[1] - 4.0), (hip[0] + 9.4, hip[1] + 9.0, 0.0),
                     (hip[0] - 9.6, hip[1] + 9.4, 0.0), (hip[0] - 8.4, hip[1] - 3.0)])
    tdet = cv.fold([(neck[0] + 3.0, neck[1] + 5.0), (hip[0] + 5.0, hip[1] - 4.0), (hip[0] + 6.0, hip[1] + 8.0)], 1.0, 1.3, 1)
    cv.shape(torso, KAFTAN, z=0, sd=4.0, details=tdet, hatch=0.35, bounce=0.35)
    # deri önlük: göğüsten dize; çıngırak muskalar
    apron = cv.blob([(neck[0] - 5.0, neck[1] + 3.4), (neck[0] + 1.6, neck[1] + 3.0), (hip[0] + 2.6, hip[1] - 4.0), (hip[0] + 3.4, hip[1] + 12.4, 0.0),
                     (hip[0] - 9.2, hip[1] + 12.8, 0.0), (hip[0] - 8.4, hip[1] - 2.0)])
    adet = cv.fold([(hip[0] - 4.0, hip[1] - 2.0), (hip[0] - 4.6, hip[1] + 5.0), (hip[0] - 4.0, hip[1] + 12.0)], 0.8, 1.2, 1)
    adet += [('ink', [(neck[0] - 3.4, neck[1] + 6.0), (neck[0] - 1.6, neck[1] + 7.0)], 1.0, (0.2, 0.2)),    # yanık izleri
             ('col', cv.ellipse((hip[0] - 5.6, hip[1] + 4.0), 0.9, 0.7), (0.2, 0.12, 0.1)),
             ('col', cv.ellipse((hip[0] - 1.6, hip[1] + 8.4), 0.7, 0.5), (0.2, 0.12, 0.1))]
    cv.shape(apron, APRON, z=1.0, sd=3.0, hi=0.3, details=adet, cast=0.8, bounce=0.3)
    # önlük askısı + muskalar
    cv.shape(cv.limb([(neck[0] - 4.6, neck[1] + 3.6), (neck[0] + 3.6, neck[1] + 2.6)], [0.8, 0.8]), APRON.darker(0.8), z=1.1, sd=0.5, ol=0.8)
    for j in range(3):
        q = (neck[0] - 3.8 + j * 2.4, neck[1] + 5.0 + j * 0.3 + math.sin(ph + j) * 0.2)
        cv.shape(cv.blob([(q[0] - 0.8, q[1]), (q[0] + 0.8, q[1]), (q[0] + 0.5, q[1] + 2.0, 0.0), (q[0] - 0.5, q[1] + 2.0, 0.0)]), IRON, z=1.2, sd=0.5, hi=0.25, ol=0.7)
    # kemer + kerpeten
    cv.shape(cv.blob([(hip[0] - 8.8, hip[1] - 3.6), (hip[0] + 8.6, hip[1] - 4.2), (hip[0] + 8.8, hip[1] - 1.6), (hip[0] - 8.8, hip[1] - 1.0)]),
             APRON.darker(0.7), z=1.3, sd=0.8, hi=0.2, details=[('col', cv.ellipse((hip[0] - 2.0, hip[1] - 2.4), 1.2, 1.1), IRON.base)])
    tg0 = (hip[0] + 6.0, hip[1] - 2.0)
    for da in (-0.08, 0.08):
        cv.shape(cv.limb([tg0, (tg0[0] + 1.4 + da * 10, tg0[1] + 9.0)], [0.6, 0.5]), IRON, z=1.25, sd=0.4, ol=0.7)
    # ---- baş: geniş yüz, örgülü kara sakal, kuzgun tüylü kam başlığı
    hx, hy = hd
    cv.shape(cv.limb([neck, (hx + 0.5, hy + 3.0)], [2.8, 2.8]), SKIN_D, z=2.0, sd=1.0)
    _face(cv, hd, SKIN_D, 2.1, mouth=talk)
    beard = cv.blob([(hx - 4.2, hy + 2.6), (hx - 2.0, hy + 3.4), (hx + 2.4, hy + 2.0), (hx + 3.0, hy + 5.0), (hx + 0.4, hy + 9.0),
                     (hx - 1.6, hy + 11.0, 0.0), (hx - 3.4, hy + 8.0), (hx - 4.8, hy + 4.6)])
    bdt = [('ink', [(hx - 3.2, hy + 4.0), (hx - 2.0, hy + 7.0), (hx - 1.6, hy + 10.0)], 0.9, (0.2, 0.6)),
           ('ink', [(hx - 0.6, hy + 4.0), (hx - 0.2, hy + 7.0)], 0.9, (0.2, 0.6)),
           ('stroke', [(hx - 2.6, hy + 3.6), (hx - 1.6, hy + 6.0)], 1.0, BEARD_K.hi, (0.3, 0.6))]
    cv.shape(beard, BEARD_K, z=2.5, sd=1.0, hi=0.3, details=bdt)
    for j in range(2):   # sakal örgüsü halkaları
        q = (hx - 1.8 + j * 0.3, hy + 7.0 + j * 2.4)
        cv.shape(cv.ellipse(q, 1.0, 0.5), IRON, z=2.6, sd=0.3, hi=0.2, ol=0.7)
    # bıyık
    cv.shape(cv.blob([(hx - 4.4, hy + 2.0), (hx - 2.8, hy + 1.6), (hx - 1.2, hy + 2.4), (hx - 2.4, hy + 3.4, 0.0), (hx - 4.6, hy + 3.6, 0.0)]),
             BEARD_K, z=2.6, sd=0.5, ol=0.8)
    # kam başlığı: deri bant + kuzgun tüyleri (geriye-yukarı), alında demir göz muskası
    cap = cv.blob([(hx - 4.0, hy - 2.6), (hx - 1.2, hy - 5.6), (hx + 3.4, hy - 5.4), (hx + 4.6, hy - 2.4), (hx + 2.0, hy - 3.2), (hx - 2.0, hy - 2.2)])
    cv.shape(cap, APRON, z=2.8, sd=1.0, hi=0.3, ol=0.9)
    for j in range(7):
        a = -math.pi * (0.5 + 0.06 * j) + 0.25 + math.sin(ph + j) * 0.03
        b0 = (hx - 1.6 + j * 0.8, hy - 4.8 - (0.3 if j % 2 else 0.0))
        L = 8.0 + (j % 3) * 1.6 - abs(j - 3) * 0.6
        tip = (b0[0] + math.cos(a) * L, b0[1] + math.sin(a) * L)
        mid = lerp2(b0, tip, 0.55)
        nx_, ny_ = -math.sin(a), math.cos(a)
        fe = cv.blob([(b0[0] - nx_ * 0.4, b0[1] - ny_ * 0.4), (mid[0] - nx_ * 1.3, mid[1] - ny_ * 1.3), (tip[0], tip[1], 0.0),
                      (mid[0] + nx_ * 1.1, mid[1] + ny_ * 1.1), (b0[0] + nx_ * 0.4, b0[1] + ny_ * 0.4)])
        cv.shape(fe, RAVEN, z=2.7 - j * 0.01, sd=0.6, hi=0.3, ol=0.8, details=[('stroke', [b0, lerp2(b0, tip, 0.85)], 0.7, RAVEN.hi, (0.1, 0.6))])
    cv.fill(cv.ellipse((hx - 2.0, hy - 3.6), 0.9, 0.9), IRON.hi, z=2.95)
    cv.fill(cv.ellipse((hx - 2.0, hy - 3.6), 0.4, 0.4), INK, z=2.96)
    # ---- ön kol + balyoz (sap dikey; başında kızgın runa)
    sh_f = (neck[0] - 4.2, neck[1] + 3.2)
    af = p.get('af', (-0.3, 0.6))
    e2, h2 = fk_arm(sh_f, af[0], af[1], 9.5, 8.5)
    out['hand'] = h2
    lift = p.get('lift', 0.0)
    # dinlenirken balyozun başı yerde (önde), sapı ele yaslı; konuşurken öne-yukarı kaldırılır (yüzü örtmez)
    ha = (-math.pi / 2 - 0.62) * lift + (math.pi / 2 + 0.42) * (1 - lift)
    L_ = 15.0 if lift > 0.5 else 13.5
    top = (h2[0] + math.cos(ha) * L_, h2[1] + math.sin(ha) * L_)
    butt = (h2[0] - math.cos(ha) * 3.0, h2[1] - math.sin(ha) * 3.0)
    cv.shape(cv.limb([butt, top], [1.15, 1.0]), WOOD, z=14.5, sd=0.8, hi=0.3,
             details=[('ink', [lerp2(butt, top, t), lerp2(butt, top, t + 0.05)], 0.9) for t in (0.3, 0.6)])
    dx_, dy_ = math.cos(ha + math.pi / 2), math.sin(ha + math.pi / 2)
    c_ = (top[0] + math.cos(ha) * 2.0, top[1] + math.sin(ha) * 2.0)
    hw, hh = 6.2, 3.0
    head_ = cv.blob([(c_[0] + dx_ * hw + math.cos(ha) * hh, c_[1] + dy_ * hw + math.sin(ha) * hh, 0.3),
                     (c_[0] - dx_ * hw * 0.8 + math.cos(ha) * hh, c_[1] - dy_ * hw * 0.8 + math.sin(ha) * hh, 0.3),
                     (c_[0] - dx_ * hw + math.cos(ha) * hh * 0.4, c_[1] - dy_ * hw + math.sin(ha) * hh * 0.4, 0.3),
                     (c_[0] - dx_ * hw - math.cos(ha) * hh * 0.4, c_[1] - dy_ * hw - math.sin(ha) * hh * 0.4, 0.3),
                     (c_[0] - dx_ * hw * 0.8 - math.cos(ha) * hh, c_[1] - dy_ * hw * 0.8 - math.sin(ha) * hh, 0.3),
                     (c_[0] + dx_ * hw - math.cos(ha) * hh, c_[1] + dy_ * hw - math.sin(ha) * hh, 0.3)])
    cv.shape(head_, IRON, z=14.6, sd=1.8, hi=0.55, cast=0.6,
             details=[('ink', [(c_[0] + dx_ * 2.2 + math.cos(ha) * hh, c_[1] + dy_ * 2.2 + math.sin(ha) * hh),
                               (c_[0] + dx_ * 2.2 - math.cos(ha) * hh, c_[1] + dy_ * 2.2 - math.sin(ha) * hh)], 1.0, (0.1, 0.1))])
    # kızgın runa (ışır): balyoz yüzünde ok ucu damga
    rc = (c_[0] - dx_ * 2.2, c_[1] - dy_ * 2.2)
    for st in ([(-1.0, 1.4), (0.0, -1.4), (1.0, 1.4)], [(-0.6, 0.3), (0.6, 0.3)]):
        pts = [(rc[0] + dx_ * x * 0.9 + math.cos(ha) * y * 0.9, rc[1] + dy_ * x * 0.9 + math.sin(ha) * y * 0.9) for x, y in st]
        cv.stroke(pts, 1.6, z=14.7, col=EMBER, taper=(0.15, 0.15), glow=EMBER_GL)
    _sleeve(cv, sh_f, e2, h2, KAFTAN, 13, rolled=True, skin=SKIN_D)
    _hand(cv, e2, h2, SKIN_D, 14)
    return out


# ------------------------------------------------------------ Ozan Bilge Kopuz
def draw_ozan(cv, p):
    bob, lean, ph = p.get('bob', 0.0), p.get('lean', 0.0), p.get('ph', 0.0)
    talk = p.get('talk', 0.0)
    hip = (0.0, -24.0 + bob * 0.3)
    neck = (hip[0] - math.sin(lean + 0.06) * 17.5, hip[1] - 17.5 + bob * 0.5)
    hd = (neck[0] - 1.6, neck[1] - 4.8)
    out = {'head': hd}
    # ---- arka kol (tellere dokunan el)
    sh_b = (neck[0] + 3.2, neck[1] + 3.0)
    ab = p.get('ab', (0.3, 0.5))
    e, h = fk_arm(sh_b, ab[0], ab[1], 9.0, 8.5)
    # ---- çapan (yere yakın), kenar işlemesi
    sw = math.sin(ph) * 0.4
    robe, hem = _robe(cv, hip, neck, CHAPAN, 0, hem_w=10.5, sway=sw, bot=-1.2)
    _hem_band(cv, robe, hem, EMBR_R, 0.2, w=1.1, dy=-1.1)
    for x in (-7.5, -2.5, 2.5, 7.5):
        q = (hip[0] + x + sw * 0.5, -2.4)
        cv.shape(cv.blob([(q[0] - 1.0, q[1]), (q[0], q[1] - 0.9), (q[0] + 1.0, q[1]), (q[0], q[1] + 0.9)]), GOLD, z=0.3, sd=0.3, ol=0.5)
    # çizme uçları (kalkık)
    for dx_, zz in ((-6.0, 0.15), (3.0, -0.1)):
        cv.shape(cv.blob([(hip[0] + dx_ + 2.6, -1.6), (hip[0] + dx_ - 2.6, -1.6), (hip[0] + dx_ - 4.0, -1.6), (hip[0] + dx_ - 4.8, -2.6, 0.0),
                          (hip[0] + dx_ - 3.6, 0.2, 0.0), (hip[0] + dx_ + 2.6, 0.2, 0.0)]), BOOT, z=zz, sd=0.6, hi=0.3, ol=0.85)
    # önü açık kenar şeridi (göğüsten eteğe)
    edge = [(neck[0] - 2.8, neck[1] + 2.4), (hip[0] - 4.0, hip[1] - 2.0), (hip[0] - 5.4 + sw, -1.6)]
    cv.shape(ik.isect(robe, ik.taper_path([cv.W(q) for q in edge], cv.u(2.0), prof=lambda s: 1.0)), EMBR_R, z=0.25, sd=0.5, ol=0.5,
             details=[('ink', [lerp2(edge[0], edge[1], t) for t in (0.0, 0.5, 1.0)] + [edge[2]], 0.6, (0.0, 0.0))])
    # kuşak
    cv.shape(cv.blob([(hip[0] - 7.0, hip[1] - 4.2), (hip[0] + 7.4, hip[1] - 4.6), (hip[0] + 7.6, hip[1] - 2.0), (hip[0] - 7.0, hip[1] - 1.6)]),
             EMBR_R, z=0.4, sd=0.8, hi=0.2,
             details=[('ink', [(hip[0] - 6.0 + j * 2.8, hip[1] - 4.0), (hip[0] - 5.4 + j * 2.8, hip[1] - 1.9)], 0.8, (0.1, 0.1)) for j in range(5)])
    kn = chain((hip[0] - 5.0, hip[1] - 2.4), 3, 2.0, math.pi * 0.55 + math.sin(ph) * 0.1, 0.03, ph, 0.15)
    cv.shape(ik.taper_path([cv.W(q) for q in kn], cv.u(1.2), (0.05, 0.4)), EMBR_R, z=0.45, sd=0.4, ol=0.7)
    # ---- baş: yaşlı yüz, uzun ak sakal, ak keçe börk
    hx, hy = hd
    cv.shape(cv.limb([neck, (hx + 0.5, hy + 3.0)], [2.0, 2.0]), SKIN_O, z=2.0, sd=1.0)
    _face(cv, hd, SKIN_O, 2.1, old=True, brow_col=(0.85, 0.86, 0.9), mouth=talk)
    # kaş (ak, gür)
    cv.shape(cv.blob([(hx - 4.0, hy - 2.4), (hx - 1.2, hy - 3.0), (hx + 0.8, hy - 2.4), (hx - 1.4, hy - 1.8, 0.0)]), BEARD_W, z=2.55, sd=0.4, ol=0.6)
    bsw = math.sin(ph * 1.0) * 0.4
    beard = cv.blob([(hx - 4.6, hy + 2.2), (hx - 2.0, hy + 3.0), (hx + 2.6, hy + 1.6), (hx + 3.0, hy + 6.0), (hx + 1.0 + bsw, hy + 13.0),
                     (hx - 1.6 + bsw, hy + 17.0, 0.0), (hx - 3.2 + bsw * 0.5, hy + 11.0), (hx - 5.0, hy + 5.0)])
    bdt = [('ink', [(hx - 3.6, hy + 4.0), (hx - 2.4, hy + 9.0), (hx - 1.6 + bsw, hy + 15.0)], 0.9, (0.2, 0.6)),
           ('ink', [(hx - 0.8, hy + 4.4), (hx - 0.2, hy + 9.0), (hx + 0.2 + bsw, hy + 12.0)], 0.9, (0.2, 0.6)),
           ('ink', [(hx + 1.6, hy + 4.0), (hx + 1.4, hy + 7.4)], 0.8, (0.2, 0.6))]
    cv.shape(beard, BEARD_W, z=2.5, sd=1.4, hi=0.3, details=bdt, bounce=0.3)
    cv.shape(cv.blob([(hx - 4.8, hy + 1.8), (hx - 3.0, hy + 1.4), (hx - 1.0, hy + 2.4), (hx - 3.0, hy + 4.0, 0.0), (hx - 5.2, hy + 3.8, 0.0)]),
             BEARD_W, z=2.6, sd=0.5, ol=0.8)
    # börk: uzun ak keçe gövde, kara kalkık kenar
    bork = cv.blob([(hx - 4.0, hy - 3.6), (hx - 3.2, hy - 12.0), (hx - 1.6, hy - 13.6), (hx + 2.4, hy - 13.4), (hx + 3.8, hy - 11.6), (hx + 4.4, hy - 3.6)])
    bkd = cv.fold([(hx + 1.2, hy - 12.4), (hx + 2.0, hy - 8.0), (hx + 2.2, hy - 4.8)], 0.6, 1.0, 1)
    bkd.append(('ink', [(hx - 1.0, hy - 13.0), (hx - 0.6, hy - 6.0)], 0.8, (0.2, 0.4)))
    cv.shape(bork, BORK, z=2.8, sd=1.8, hi=0.35, details=bkd, bounce=0.3)
    brim = cv.blob([(hx - 5.4, hy - 2.4), (hx - 4.8, hy - 5.6), (hx + 0.0, hy - 5.0), (hx + 5.2, hy - 5.8), (hx + 5.6, hy - 2.6), (hx + 0.2, hy - 2.2)])
    cv.shape(brim, BORK_IN, z=2.9, sd=0.6, hi=0.3, ol=0.9,
             details=[('stroke', [(hx - 4.6, hy - 4.4), (hx + 0.0, hy - 3.8), (hx + 4.6, hy - 4.6)], 0.8, GOLD.base, (0.1, 0.1))])
    # nazar boncuğu (boyunda)
    nz = (neck[0] - 1.4, neck[1] + 3.6)
    cv.fill(cv.ellipse(nz, 1.0, 1.0), NAZAR, z=2.45)
    cv.fill(cv.ellipse(nz, 0.6, 0.6), (1, 1, 1), z=2.46)
    cv.fill(cv.ellipse((nz[0] - 0.1, nz[1]), 0.3, 0.3), (0.05, 0.1, 0.3), z=2.47)
    # ---- kopuz: armut gövde sağ kalçada, uzun sap sola-yukarı; ön el sapı tutar, arka el telleri çalar (IK)
    sh_f = (neck[0] - 3.0, neck[1] + 3.0)
    lift = p.get('lift', 0.0)
    body_c = (hip[0] + 2.2, hip[1] - 3.0 - lift * 2.5)
    ang = math.radians(-146 + lift * 10)          # sap yönü (sol-yukarı)
    nk = (math.cos(ang), math.sin(ang))
    pe_ = (-nk[1], nk[0])
    end = (body_c[0] + nk[0] * 24.0, body_c[1] + nk[1] * 24.0)
    hk = lerp2(body_c, end, 0.6)
    e2, h2 = wk.ik(sh_f, (hk[0] + pe_[0] * 0.4, hk[1] + pe_[1] * 0.4), 9.0, 8.5, -1)
    out['hand'] = h2
    strum = p.get('strum', 0.0)
    tgt = (body_c[0] + nk[0] * (1.8 + strum * 0.8) + pe_[0] * (1.2 + strum), body_c[1] + nk[1] * (1.8 + strum * 0.8) + pe_[1] * (1.2 + strum))
    if p.get('wave', 0.0) > 0:   # konuşurken arka el havada (anlatır)
        tgt = (sh_b[0] - 9.0, sh_b[1] + 3.0 - p['wave'] * 3.0)
    e, h = wk.ik(sh_b, tgt, 9.0, 8.5, -1)
    bowl = cv.blob([(body_c[0] - nk[0] * 7.0, body_c[1] - nk[1] * 7.0),
                    (body_c[0] - nk[0] * 5.0 + pe_[0] * 4.6, body_c[1] - nk[1] * 5.0 + pe_[1] * 4.6),
                    (body_c[0] + nk[0] * 2.0 + pe_[0] * 3.8, body_c[1] + nk[1] * 2.0 + pe_[1] * 3.8),
                    (body_c[0] + nk[0] * 6.0 + pe_[0] * 1.4, body_c[1] + nk[1] * 6.0 + pe_[1] * 1.4),
                    (body_c[0] + nk[0] * 6.0 - pe_[0] * 1.4, body_c[1] + nk[1] * 6.0 - pe_[1] * 1.4),
                    (body_c[0] + nk[0] * 2.0 - pe_[0] * 3.8, body_c[1] + nk[1] * 2.0 - pe_[1] * 3.8),
                    (body_c[0] - nk[0] * 5.0 - pe_[0] * 4.6, body_c[1] - nk[1] * 5.0 - pe_[1] * 4.6)])
    neck_k = cv.limb([lerp2(body_c, end, 0.2), end], [1.0, 0.85])
    head_k = cv.blob([(end[0] - pe_[0] * 1.0, end[1] - pe_[1] * 1.0), (end[0] + nk[0] * 4.2 - pe_[0] * 1.6, end[1] + nk[1] * 4.2 - pe_[1] * 1.6, 0.0),
                      (end[0] + nk[0] * 4.6 + pe_[0] * 0.4, end[1] + nk[1] * 4.6 + pe_[1] * 0.4), (end[0] + pe_[0] * 1.0, end[1] + pe_[1] * 1.0)])
    cv.shape(ik.union(neck_k, head_k), KOPUZ.darker(0.85), z=10, sd=0.8, hi=0.3,
             details=[('ink', [lerp2(body_c, end, t + 0.0), lerp2(body_c, end, t + 0.01)], 1.4, (0.0, 0.0)) for t in (0.45, 0.6, 0.75, 0.88)])
    for j in range(3):   # burgu (akort mandalları)
        q = (end[0] + nk[0] * (1.2 + j * 1.2), end[1] + nk[1] * (1.2 + j * 1.2))
        cv.shape(cv.limb([q, (q[0] + pe_[0] * 1.8, q[1] + pe_[1] * 1.8)], [0.4, 0.5]), BONE_K, z=10.1, sd=0.3, ol=0.6)
    bdet = [('deep', cv.wedge([(body_c[0] - nk[0] * 5.0 - pe_[0] * 3.6, body_c[1] - nk[1] * 5.0 - pe_[1] * 3.6),
                               (body_c[0] + nk[0] * 1.0 - pe_[0] * 3.4, body_c[1] + nk[1] * 1.0 - pe_[1] * 3.4),
                               (body_c[0] + nk[0] * 5.0 - pe_[0] * 1.2, body_c[1] + nk[1] * 5.0 - pe_[1] * 1.2)], 0.9, -1.0))]
    # deri kapak (göğüs) + ses deliği
    skin_ = cv.blob([(body_c[0] - nk[0] * 5.6, body_c[1] - nk[1] * 5.6), (body_c[0] - nk[0] * 3.0 + pe_[0] * 3.4, body_c[1] - nk[1] * 3.0 + pe_[1] * 3.4),
                     (body_c[0] + nk[0] * 0.6 + pe_[0] * 2.2, body_c[1] + nk[1] * 0.6 + pe_[1] * 2.2),
                     (body_c[0] + nk[0] * 0.6 - pe_[0] * 2.2, body_c[1] + nk[1] * 0.6 - pe_[1] * 2.2),
                     (body_c[0] - nk[0] * 3.0 - pe_[0] * 3.4, body_c[1] - nk[1] * 3.0 - pe_[1] * 3.4)])
    cv.shape(bowl, KOPUZ, z=10.2, sd=2.2, hi=0.45, details=bdet, cast=0.8, bounce=0.3)
    cv.shape(skin_, Ink('#e8d6b0', '#9c8664', '#fff4dc'), z=10.3, sd=1.0, ol=0.6)
    cv.fill(cv.ellipse((body_c[0] + nk[0] * 2.4, body_c[1] + nk[1] * 2.4), 1.0, 0.8), (0.12, 0.08, 0.06), z=10.35)
    # teller (ince açık çizgi) + titreşim
    vib = 0.25 * math.sin(ph * 3.0) * (1 - lift)
    for j, o in enumerate((-0.45, 0.0, 0.45)):
        a = (body_c[0] - nk[0] * 4.8 + pe_[0] * o, body_c[1] - nk[1] * 4.8 + pe_[1] * o)
        b = (end[0] + pe_[0] * o * 0.4, end[1] + pe_[1] * o * 0.4)
        m = lerp2(a, b, 0.35)
        m = (m[0] + pe_[0] * vib * (j - 1), m[1] + pe_[1] * vib * (j - 1))
        cv.stroke([a, m, b], 0.6, z=10.4, col=(0.95, 0.92, 0.82), taper=(0.0, 0.0))
    # arka kol: kopuzun önünde tellere uzanır (gövdeyi çapraz geçer)
    _sleeve(cv, sh_b, e, h, CHAPAN_B, 10.6, wide=0.8, near=True, cuff=EMBR_R)
    _hand(cv, e, h, SKIN_O, 10.9, open_=1.0 if p.get('wave', 0.0) > 0 else 0.0)
    # ön kol: sapı tutan el
    _sleeve(cv, sh_f, e2, h2, CHAPAN, 13, wide=1.2, cuff=EMBR_R)
    _hand(cv, e2, h2, SKIN_O, 14)
    return out


BONE_K = Ink('#e8dcc0', '#9a8a6a', '#fffaee', name='kemik mandal')

# ------------------------------------------------------------ pozlar (v1: idle 6, talk 4; kişiye göre ek anahtarlar)
def _pose(name, anim, t):
    s = math.sin(t * math.tau)
    c = math.cos(t * math.tau)
    p = dict(bob=0.6 * s, lean=0.02 * s, ph=t * math.tau)
    if name == 'umay':
        # ön el asayı tutar (el göğüs hizasında), arka el yanda; konuşurken arka el kutsama için öne-yukarı kalkar
        p.update(af=(-1.0, 0.95), ab=(0.25 + 0.04 * s, 0.35))
        if anim == 'talk':
            p.update(talk=1.0 if t < 0.5 else 0.6, lean=0.04, ab=(-1.55 - 0.15 * s, 0.85 + 0.1 * c))
    elif name == 'demirci':
        p.update(af=(-0.55, 0.5), ab=(0.3 + 0.04 * s, 0.6), lift=0.0)
        if anim == 'talk':
            p.update(talk=0.8 + 0.2 * s, lift=1.0, af=(-1.05 - 0.2 * max(0.0, s), 1.55), ab=(-0.7 + 0.25 * s, 1.4), lean=0.05)
    else:   # ozan: kopuz kucakta, arka el tellere dokunur
        p.update(strum=math.sin(t * math.tau * 2))
        if anim == 'talk':
            p.update(talk=0.8 + 0.2 * s, lift=0.4 + 0.2 * s, wave=0.6 + 0.4 * s, lean=-0.03, strum=0.0)
    return p


DRAW = {'umay': draw_umay, 'demirci': draw_demirci, 'ozan': draw_ozan}
ANIMS = {k: (v[0], None, True, True) for k, v in NPC_ANIMS.items()}
SHADE = dict(outer=0.5, rim=0.45, rim_col=(1.0, 0.86, 0.66), rim_dir=(0.6, -0.8), rim_w=1.3, form=(6.0, (0.8, 0.78, 0.9)))


def render_npc(name, anim, i, ss=3):
    n = NPC_ANIMS[anim][0]
    p = _pose(name, anim, i / n)
    cv = ik.InkCanvas(CELL[0], CELL[1], FEET[0], FEET[1], k=TEX, ss=ss)
    info = DRAW[name](cv, p)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, nm, em, info


class _Mod:
    """preview/sheet için tek kişilik görünüm: npc_ink.who('umay').render_frame(anim, i)."""
    def __init__(self, name):
        self.name = name
        self.ANIMS = ANIMS

    def render_frame(self, anim, i):
        return render_npc(self.name, anim, i)


def who(name):
    return _Mod(name)
