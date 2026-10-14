"""Ulu Kayın yurdu: bölüm aralarındaki güvenli alan.
Süsler: ulu_kayin (dev ak kayın, kut ışıklı), ocak (ateş), cadir (keçe çadır).
NPC'ler: Umay Ana (ak giysili, geyik boynuzlu taç, ışıl), Demirci Kam Kuzgun (tıknaz, önlük, kuzgun tüyleri, çekiç),
Ozan Bilge Kopuz (yaşlı, kopuz, keçe börk). Hepsi yüz sola bakar (oyuncu soldan gelir); ayak merkezi (0,0)."""
import math
import random
import numpy as np
from raster import Canvas, Mat, ramp
from materials import M
from rig import fk_leg, fk_arm, lerp2, chain

BIRCH = Mat(ramp(40, 0.06, 0.92, spread=0.3), name='ak kayın kabuğu')
BIRCH_D = Mat(ramp(220, 0.12, 0.3, spread=0.3), name='kayın lekesi')
LEAF_P = Mat(ramp(70, 0.35, 0.75, spread=0.4), name='soluk yaprak')
LEAF_G = Mat(ramp(172, 0.6, 0.95, spread=0.3), emissive=0.8, outline='#0b4a52', name='kut yaprağı')
FELT = Mat(ramp(36, 0.25, 0.80, spread=0.35), name='keçe')
FELT_D = Mat(ramp(30, 0.35, 0.55), name='koyu keçe')
WHITE = Mat(ramp(200, 0.05, 0.96, spread=0.3), name='ak giysi')
WHITE_D = Mat(ramp(205, 0.12, 0.72), name='ak giysi gölge')
ANTLER = Mat(ramp(40, 0.3, 0.85), name='boynuz')
APRON = Mat(ramp(24, 0.5, 0.42), name='deri önlük')
RAVEN = Mat(ramp(250, 0.35, 0.18, spread=0.3), name='kuzgun tüyü')
BEARD = Mat(ramp(40, 0.1, 0.85, spread=0.3), name='ak sakal')
BEARD_B = Mat(ramp(20, 0.3, 0.3, spread=0.3), name='kara sakal')
KOPUZ = Mat(ramp(28, 0.6, 0.6), name='kopuz gövdesi')
FIRE = Mat(ramp(30, 0.9, 1.0), emissive=1.0, outline='#7a2a04', name='ateş')
FIRE_C = Mat(ramp(50, 0.6, 1.0), emissive=1.0, outline='#7a2a04', name='ateş göbeği')
SKIN = M['skin']
SKIN_S = M['skin_shadow']


# ------------------------------------------------------------ süsler
def decor_ulu_kayin():
    """Dev ak kayın: kalın gövde, iki ana dal, geniş soluk taç, yapraklar arasında kut ışıkları, yüzey kökleri."""
    c = Canvas(260, 300, 130, 294)
    rng = random.Random(7)
    marks = lambda lu, lv, px, py: (np.floor(py * 0.11 + np.sin(px * 0.6) * 0.8) % 4 == 0) & (np.abs(lv) < 0.45) & (((px * 3 + py) % 7) < 2.5)
    c.capsule((0, 0), (-6, -150), 20.0, 11.0, BIRCH, z=0, paint=[(marks, BIRCH_D)])
    for x0, y0, x1, y1, r in ((-4, -110, -70, -190, 7.0), (-5, -125, 62, -200, 6.5), (-6, -150, -30, -230, 5.0), (-6, -150, 28, -236, 5.0),
                              (-50, -170, -95, -215, 3.5), (45, -180, 92, -210, 3.5), (-6, -140, 10, -180, 3.0)):
        c.capsule((x0, y0), (x1, y1), r, r * 0.5, BIRCH, z=1, paint=[(marks, BIRCH_D)])
    # kökler
    for dx, a in ((-26, -0.9), (-12, -0.6), (14, 0.5), (30, 0.95)):
        c.capsule((dx * 0.35, -6), (dx * 1.6, 0), 5.5, 2.5, BIRCH, z=0.5, paint=[(marks, BIRCH_D)])
    # taç: büyük yaprak öbekleri (soluk), aralarda kut yaprakları
    for k in range(90):
        a = rng.uniform(0, math.tau); r = rng.uniform(0, 1) ** 0.6
        x = math.cos(a) * r * 115 - 4
        y = -215 + math.sin(a) * r * 62
        c.ellipse((x, y), rng.uniform(7, 13), rng.uniform(5, 9), LEAF_P, z=-3 + rng.uniform(0, 3))
    for k in range(26):
        a = rng.uniform(0, math.tau); r = rng.uniform(0.1, 1) ** 0.7
        x = math.cos(a) * r * 105 - 4
        y = -212 + math.sin(a) * r * 56
        c.ellipse((x, y), rng.uniform(2.5, 4), rng.uniform(2, 3), LEAF_G, z=2 + rng.uniform(0, 1))
    # dallardan sarkan çaputlar (dilek bezleri)
    for k in range(14):
        bx = rng.uniform(-80, 80); by = -185 + abs(bx) * 0.2
        col = [M['red_paint'], M['turq'], M['nazar_l'], M['gold']][k % 4]
        c.capsule((bx, by), (bx + rng.uniform(-2, 2), by + rng.uniform(8, 16)), 1.2, 0.9, col, z=3)
    return c


def decor_ocak():
    """Ocak: taş halka, odunlar, yükselen alev dilleri (ışık kaynağı)."""
    c = Canvas(48, 40, 24, 38)
    for k in range(7):
        a = math.pi + k * math.pi / 6
        c.ellipse((math.cos(a) * 18, -2 + math.sin(a) * 3), 4.2, 2.8, M['stone'], z=1)
    c.capsule((-10, -4), (9, -7), 2.4, 2.0, M['wood'], z=2)
    c.capsule((-8, -7), (11, -3), 2.2, 1.8, M['bark'], z=2.5)
    c.poly([(-9, -6), (9, -6), (6, -16), (3, -24), (0, -18), (-3, -28), (-6, -17)], FIRE, z=5, bevel=1.6, height=1.2)
    c.poly([(-4, -6), (4, -6), (2, -13), (0, -19), (-2, -12)], FIRE_C, z=7, bevel=1.0, height=0.8)
    return c


def decor_cadir():
    """Keçe çadır (yurt): yuvarlak gövde, konik çatı, kırmızı kapı perdesi, tepe deliği."""
    c = Canvas(96, 80, 48, 78)
    band = lambda lu, lv, px, py: (np.floor(py * 0.5) % 9 == 0)
    c.ellipse((0, -14), 40, 16, FELT, z=0, depth=0.6, paint=[(band, FELT_D)])
    c.poly([(-42, -22), (42, -22), (3, -62), (-3, -62)], FELT, z=2, bevel=3, height=2)
    for k in range(5):
        x = -34 + k * 17
        c.capsule((x, -22), (0, -60), 0.8, 0.6, FELT_D, z=3)
    c.poly([(-9, 0), (9, 0), (7, -26), (-7, -26)], M['red_paint'], z=4, bevel=1.2, height=0.8)
    c.ellipse((0, -61), 5, 2.5, FELT_D, z=4)
    return c


DECOR = {'ulu_kayin': decor_ulu_kayin, 'ocak': decor_ocak, 'cadir': decor_cadir}


# ------------------------------------------------------------ NPC gövdesi
def draw_human(c, p, st):
    """Basit insan: st = {robe, robe_d, skin, hair, extras(fn)}. Yüz sola (flip export'ta değil: doğrudan sola çizilir)."""
    bob = p.get('bob', 0.0)
    lean = p.get('lean', 0.0)
    hip = (0.0, -22 + bob)
    neck = (hip[0] - math.sin(lean) * 15, hip[1] - 15)
    head = (neck[0] - 1.5, neck[1] - 7)
    robe, robe_d = st['robe'], st['robe_d']
    # arka kol
    e, h = fk_arm((neck[0] + 3, neck[1] + 3), p.get('ab', (0.2, 0.4))[0], p.get('ab', (0.2, 0.4))[1], 9, 8)
    c.capsule((neck[0] + 3, neck[1] + 3), e, 2.8, 2.4, robe_d, z=-10)
    c.capsule(e, h, 2.4, 2.0, robe_d, z=-10)
    c.ellipse(h, 2.0, 2.0, st.get('skin', SKIN), z=-9)
    # bacaklar / etek
    if st.get('long_robe', True):
        c.poly([(hip[0] - 7, hip[1] - 2), (hip[0] + 7, hip[1] - 2), (hip[0] + 10, 0), (hip[0] - 10, 0)], robe, z=0, bevel=2.5, height=2)
        c.capsule((hip[0] - 5, -1), (hip[0] + 5, -1), 1.5, 1.5, robe_d, z=1)
    else:
        for dx, zz in ((3, -2), (-3, 4)):
            k, f = fk_leg((hip[0] + dx, hip[1]), 0.05 * dx, 0.1, 10, 10)
            c.capsule((hip[0] + dx, hip[1]), k, 3.2, 2.8, M['indigo'], z=zz)
            c.capsule(k, f, 2.8, 2.4, M['indigo'], z=zz)
            c.capsule(f, (f[0] - 4, f[1] - 0.3), 2.2, 1.4, M['boot'], z=zz + 0.2)
    # gövde
    mid = lerp2(hip, neck, 0.5)
    c.ellipse((mid[0], mid[1] + 1), st.get('width', 7.5), 10.0, robe, z=2, rot=-lean)
    if st.get('belt', True):
        c.capsule((hip[0] - 7, hip[1] - 2), (hip[0] + 7, hip[1] - 2), 1.8, 1.8, M['leather'], z=4)
    if 'apron' in st:
        c.poly([(hip[0] - 6, hip[1] - 12), (hip[0] + 6, hip[1] - 12), (hip[0] + 8, 0), (hip[0] - 8, 0)], st['apron'], z=5, bevel=2, height=1.5)
    # baş
    hx, hy = head
    c.ellipse((hx, hy), 5.6, 6.0, st.get('skin', SKIN), z=10)
    c.ellipse((hx - 4.5, hy + 1.0), 1.6, 1.2, st.get('skin', SKIN), z=11)  # burun (sola)
    c.dot((hx - 2.5, hy - 0.8), M['black'], z=20, size=1)
    if 'beard' in st:
        c.poly([(hx - 6, hy + 2), (hx + 4, hy + 3), (hx + 1, hy + 14 + st.get('beard_len', 0)), (hx - 4, hy + 12 + st.get('beard_len', 0))], st['beard'], z=12, bevel=2, height=1.2)
    if 'hair' in st:
        c.ellipse((hx + 1, hy - 3), 6.2, 4.6, st['hair'], z=11.5)
        if st.get('long_hair', False):
            c.capsule((hx + 4, hy - 1), (hx + 7, hy + 18), 3.2, 2.0, st['hair'], z=1)
    if 'hat' in st:
        st['hat'](c, hx, hy)
    # ön kol
    e, h = fk_arm((neck[0] - 3, neck[1] + 3), p.get('af', (-0.2, 0.5))[0], p.get('af', (-0.2, 0.5))[1], 9, 8)
    c.capsule((neck[0] - 3, neck[1] + 3), e, 3.0, 2.5, robe, z=14)
    c.capsule(e, h, 2.5, 2.1, robe, z=14)
    c.ellipse(h, 2.1, 2.1, st.get('skin', SKIN), z=15)
    if 'held' in st:
        st['held'](c, h, p)
    return {'hand': h, 'head': head}


def hat_antler(c, hx, hy):
    c.capsule((hx - 5, hy - 4), (hx + 5, hy - 4), 1.4, 1.4, M['gold'], z=13)
    for sx in (-1, 1):
        bx = hx + sx * 3.5
        c.capsule((bx, hy - 5), (bx + sx * 4, hy - 16), 1.3, 0.8, ANTLER, z=12.5)
        c.capsule((bx + sx * 2, hy - 10), (bx + sx * 6, hy - 14), 0.9, 0.6, ANTLER, z=12.5)
        c.capsule((bx + sx * 3, hy - 14), (bx + sx * 2, hy - 20), 0.9, 0.6, ANTLER, z=12.5)
    c.dot((hx, hy - 6), M['kut'], z=30, size=2)


def hat_raven(c, hx, hy):
    c.ellipse((hx + 1, hy - 4), 6.4, 3.2, M['leather'], z=12.8)
    for k in range(4):
        c.poly([(hx - 1 + k * 1.6, hy - 6), (hx + 1 + k * 1.6, hy - 6), (hx + 3 + k * 2.0, hy - 16 - k)], RAVEN, z=12.6, bevel=0.8, height=0.6)


def hat_bork(c, hx, hy):
    c.poly([(hx - 7, hy - 3), (hx + 7, hy - 3), (hx + 5, hy - 14), (hx - 5, hy - 14)], FELT, z=12.8, bevel=1.8, height=1.2)
    c.capsule((hx - 7, hy - 3), (hx + 7, hy - 3), 1.6, 1.6, FELT_D, z=13)


def held_hammer(c, h, p):
    c.capsule(h, (h[0] - 2, h[1] - 18), 1.4, 1.2, M['wood'], z=16)
    c.poly([(h[0] - 8, h[1] - 22), (h[0] + 4, h[1] - 22), (h[0] + 4, h[1] - 15), (h[0] - 8, h[1] - 15)], M['iron'], z=17, bevel=1.5, height=1.5)


def held_kopuz(c, h, p):
    c.ellipse((h[0] - 2, h[1] + 4), 7.0, 5.0, KOPUZ, z=13)
    c.capsule((h[0] + 3, h[1] + 2), (h[0] + 22, h[1] - 8), 1.6, 1.4, M['wood'], z=13.5)
    for k in range(3):
        c.capsule((h[0] - 6, h[1] + 3 + k), (h[0] + 20, h[1] - 7 + k), 0.3, 0.3, M['bone'], z=14)
    c.ellipse((h[0] - 2, h[1] + 4), 2.0, 1.6, M['black'], z=14)


def held_staff(c, h, p):
    c.capsule((h[0], h[1] + 14), (h[0] - 1, h[1] - 26), 1.3, 1.1, BIRCH, z=16)
    c.dot((h[0] - 1, h[1] - 28), M['kut'], z=30, size=3)
    for k in range(3):
        a = p.get('ph', 0.0) + k * 2.1
        c.dot((h[0] - 1 + math.cos(a) * 6, h[1] - 28 + math.sin(a) * 6), M['kut'], z=30, size=1)


NPC_STYLES = {
    'umay': dict(robe=WHITE, robe_d=WHITE_D, hair=BEARD, long_hair=True, hat=hat_antler, held=held_staff, width=7.0),
    'demirci': dict(robe=M['kaftan_in'], robe_d=M['leather'], skin=SKIN_S, hair=RAVEN, beard=BEARD_B, beard_len=2, hat=hat_raven,
                    apron=APRON, held=held_hammer, width=9.5, long_robe=False),
    'ozan': dict(robe=FELT, robe_d=FELT_D, beard=BEARD, beard_len=6, hat=hat_bork, held=held_kopuz, width=7.5),
}


def _idle(t):
    s = math.sin(t * math.tau)
    return dict(bob=0.8 * s, lean=0.03 * s, af=(-0.3 + 0.05 * s, 0.6), ab=(0.3, 0.5), ph=t * math.tau)


def _talk(t):
    s = math.sin(t * math.tau)
    return dict(bob=0.5 * s, lean=0.06, af=(-0.8 + 0.3 * s, 0.9), ab=(0.4, 0.6), ph=t * math.tau)


NPC_ANIMS = {'idle': (6, _idle), 'talk': (4, _talk)}
NPC_CELL = (64, 88)
NPC_FEET = (32, 84)


def render_npc(name, anim, i):
    n, fn = NPC_ANIMS[anim]
    p = fn(i / n)
    c = Canvas(NPC_CELL[0], NPC_CELL[1], NPC_FEET[0], NPC_FEET[1])
    info = draw_human(c, p, NPC_STYLES[name])
    rgba = c.shade()
    nm = c.normal_map(rgba[..., 3])
    return c, rgba, nm, info
