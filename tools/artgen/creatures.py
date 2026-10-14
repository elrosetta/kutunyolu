"""Ötüken Ormanı yaratıkları: Kara Börü, Çor, Ağaç İyesi, Balbal.

Hepsi yüz sağa bakar, ayak merkezi (0,0). Her yaratığın pozları ve animasyonları
ANIMS sözlüğünde; render_creature() Godot'ya aktarılacak kareyi üretir.
"""
import math
import numpy as np
from raster import Canvas, Mat, ramp
from materials import M
from rig import fk_leg, fk_arm, lerp2, chain, Xf
import bozkurt

BARK2 = Mat(ramp(18, 0.50, 0.26, spread=0.4), name='koyu kabuk')
STONE2 = Mat(ramp(216, 0.15, 0.40, spread=0.4), name='koyu taş')
LEAF_O = Mat(ramp(28, 0.85, 0.92), name='güz yaprağı')
LEAF_R = Mat(ramp(4, 0.75, 0.75), name='kızıl yaprak')


# ------------------------------------------------------------ KARA BÖRÜ
def draw_wolf(c, p):
    bob, tilt, jaw = p.get('bob', 0.0), p.get('tilt', 0.0), p.get('jaw', 0.0)
    hipp = (-9.5, -17 + bob - tilt * 6)
    shp = (8.5, -18 + bob + tilt * 6)
    back_dark = lambda lu, lv, px, py: lv < -0.35
    fur_s = lambda lu, lv, px, py: (np.floor(px * 0.7 - py) % 4 == 0) & (lv < 0.2)

    def leg(base, a, z, front):
        if front:
            k, f = fk_leg(base, a[0], a[1], 8.5, 9.0)
        else:
            k, f = fk_leg(base, a[0], a[1], 8.0, 9.5)
        mat = M['wolf_fur'] if z > 0 else M['wolf_fur2']
        c.capsule(base, k, 3.4 if not front else 3.0, 2.3, mat, z=z)
        c.capsule(k, f, 2.2, 1.7, mat, z=z)
        c.ellipse((f[0] + 1.3, f[1] - 0.8), 2.3, 1.4, mat, z=z + 0.1)
        for i in range(3):
            c.dot((f[0] + 2.6 + i * 0.1, f[1] - 1.6 + i), M['bone'], z=z + 2)
        return f

    leg(hipp, p['hb'], -8, False)
    leg(shp, p['fb'], -8, True)
    # kuyruk
    tl = chain((hipp[0] - 4, hipp[1] - 2), 5, 3.2, math.pi * 1.12 + p.get('tw', 0.0), -0.12, p.get('ph', 0.0), 0.25)
    for i, (a, b) in enumerate(zip(tl, tl[1:])):
        c.capsule(a, b, 2.8 - i * 0.3, 2.4 - i * 0.3, M['wolf_fur'] if i < 4 else M['corrupt'], z=-6)
    # gövde
    c.ellipse(hipp, 7.6, 7.0, M['wolf_fur'], z=0, paint=[(back_dark, M['wolf_fur2']), (fur_s, M['wolf_fur2'])])
    c.capsule(hipp, shp, 6.3, 7.0, M['wolf_fur'], z=1, paint=[(back_dark, M['wolf_fur2']), (fur_s, M['wolf_fur2'])])
    c.ellipse(shp, 8.0, 8.4, M['wolf_fur'], z=2, paint=[(back_dark, M['wolf_fur2']), (fur_s, M['wolf_fur2'])])
    # Erlik bozgunu: sırttaki kristaller
    for k, (t, h) in enumerate(((0.15, 6), (0.4, 9), (0.65, 7), (0.85, 5))):
        bx, by = lerp2(hipp, shp, t)
        by -= 6.5
        c.poly([(bx - 2.2, by + 2), (bx + 2.2, by + 2), (bx + 0.6, by - h), (bx - 0.8, by - h + 1.5)], M['corrupt'], z=6, bevel=1.1, height=1.5)
    # boyun + baş
    head = (shp[0] + 9.5, shp[1] - 6 + p.get('hy', 0.0))
    c.capsule((shp[0] + 2, shp[1] - 2), head, 5.6, 4.6, M['wolf_fur'], z=4, paint=[(back_dark, M['wolf_fur2'])])
    hx_, hy_ = head
    c.ellipse(head, 5.4, 4.6, M['wolf_fur'], z=6, paint=[(back_dark, M['wolf_fur2'])])
    c.poly([(hx_ - 3.5, hy_ - 2.5), (hx_ - 0.6, hy_ - 3.5), (hx_ - 2.4, hy_ - 9.5)], M['wolf_fur'], z=7, bevel=1.2, height=1.5)
    c.poly([(hx_ - 0.4, hy_ - 3.6), (hx_ + 2.0, hy_ - 3.0), (hx_ + 0.2, hy_ - 9.0)], M['wolf_fur2'], z=6.5, bevel=1.2, height=1.5)
    sn0 = (hx_ + 2.5, hy_ + 0.6)
    c.capsule(sn0, (hx_ + 10.5, hy_ + 1.6), 3.0, 1.9, M['wolf_fur'], z=8)
    c.ellipse((hx_ + 11.0, hy_ + 1.2), 1.2, 1.0, M['black'], z=10)
    jd = jaw * 3.2
    c.capsule((hx_ + 2.5, hy_ + 3.0), (hx_ + 9.5, hy_ + 3.6 + jd), 1.7, 1.1, M['wolf_fur2'], z=7.5)
    if jaw > 0.2:
        c.poly([(hx_ + 4, hy_ + 2.6), (hx_ + 10, hy_ + 2.9), (hx_ + 9.5, hy_ + 3.0 + jd * 0.8), (hx_ + 4, hy_ + 3.4 + jd * 0.5)], M['eye_red'], z=7.4, bevel=0.5, height=0.3)
    for i in range(4):
        c.dot((hx_ + 4.4 + i * 1.6, hy_ + 2.4), M['bone'], z=12)
        if jaw > 0.2:
            c.dot((hx_ + 4.6 + i * 1.5, hy_ + 2.6 + jd * (0.4 + i * 0.12)), M['bone'], z=12)
    c.capsule((hx_ + 1.4, hy_ - 1.6), (hx_ + 3.6, hy_ - 1.2), 0.7, 0.6, M['eye_red'], z=20)
    # yeleler: bozgun dikenleri
    for k in range(3):
        bx, by = hx_ - 4 - k * 2.5, hy_ - 1 + k * 1.5
        c.poly([(bx - 1.2, by + 1), (bx + 1.2, by + 1), (bx - 2.2, by - 5 + k)], M['corrupt'], z=7, bevel=0.8, height=1)
    leg(hipp, p['hf'], 8, False)
    leg(shp, p['ff'], 8, True)
    return {'mouth': (hx_ + 10, hy_ + 2.5)}


def _wolf_run(t):
    ph = t * math.tau
    s, s2 = math.sin(ph), math.sin(ph + 0.6)
    return dict(bob=-abs(math.cos(ph)) * 1.5 + 0.5, tilt=0.12 * math.sin(ph),
                hb=(0.9 * s, 0.9 - 0.4 * s), hf=(0.9 * s2, 0.9 - 0.4 * s2),
                fb=(-0.9 * s + 0.1, 0.2 + 0.8 * max(0, s)), ff=(-0.9 * s2 + 0.1, 0.2 + 0.8 * max(0, s2)), tw=-0.2, ph=ph, jaw=0.15)


WOLF = {
    'idle': (6, lambda t: dict(bob=0.5 * math.sin(t * 6.28), hb=(0.25, 0.9), hf=(0.1, 0.8), fb=(-0.05, 0.1), ff=(0.08, 0.1), tw=0.1 * math.sin(t * 6.28), ph=t * 6.28, jaw=0.05)),
    'run': (6, _wolf_run),
    'windup': (2, lambda t: dict(bob=3.5, tilt=-0.18, hb=(0.6, 1.6), hf=(0.5, 1.5), fb=(0.5, 1.2), ff=(0.6, 1.3), tw=0.4, jaw=0.7 + 0.2 * t, hy=2)),
    'leap': (2, lambda t: dict(bob=-2, tilt=-0.08, hb=(-1.0, 0.3), hf=(-0.9, 0.4), fb=(1.2, 0.2), ff=(1.3, 0.3), tw=-0.4, jaw=1.0)),
    'hurt': (2, lambda t: dict(bob=1, tilt=0.2, hb=(0.3, 0.9), hf=(0.2, 0.8), fb=(-0.3, 0.3), ff=(-0.2, 0.2), tw=0.6, jaw=0.5, hy=-1)),
}


# ------------------------------------------------------------ ÇOR (salgın ruhu)
def draw_cor(c, p):
    t = p.get('t', 0.0)
    fl = math.sin(t * math.tau) * 2.0
    att = p.get('att', 0.0)
    K = 1.45
    tail = chain((0, -20 + fl), 5, 4.6, math.pi * 0.62, 0.22, t * math.tau * 2, 0.55)
    for i, (a, b) in enumerate(zip(tail, tail[1:])):
        c.capsule(a, b, (5.2 - i * 0.95) * K, (4.4 - i * 0.95) * K, M['cor'], z=-4 + i * 0.1)
    core = lambda lu, lv, px, py: (lu * lu + lv * lv) < 0.22
    c.ellipse((0, -33 + fl), 7.4 * K, 8.4 * K, M['cor'], z=0, paint=[(core, M['flower_y'])])
    # paçavra şeritler (maskenin arkasında)
    mx, my = 3.5 + att * 2, -35 + fl
    for sx, col in ((-5.5, M['cloth_blue']), (6.0, M['red_paint'])):
        st = chain((mx + sx, my + 2), 3, 3.4, math.pi * 0.5 + math.sin(t * 6.28 + sx) * 0.3, 0.0, t * 6.28, 0.2)
        for a, b in zip(st, st[1:]):
            c.capsule(a, b, 1.2, 1.0, col, z=4)
    # dal boynuzlar
    for sx, dx in ((-3.5, -5), (3.0, 4)):
        c.capsule((mx + sx, my - 7), (mx + sx + dx, my - 14), 1.3, 0.7, M['bark'], z=5)
    # ahşap maske: soluk oval, tek kırmızı şerit, iki göz oyuğu, ağız
    stripe = lambda lu, lv, px, py: (np.abs(lu) < 0.13) & (lv < 0.25)
    c.ellipse((mx, my), 6.0, 8.6, M['mask'], z=6, flat=0.75, paint=[(stripe, M['red_paint'])])
    for ex in (-2.4, 2.6):
        c.ellipse((mx + ex, my - 1.4), 1.6, 2.1 + att * 0.6, M['black'], z=20)
        c.dot((mx + ex, my - 1.4), M['cor'], z=26)
    c.ellipse((mx + 0.2, my + 4.2), 2.0, 1.0 + att * 1.8, M['black'], z=20)
    return {'mouth': (mx + 0.2, my + 4)}


COR = {
    'idle': (6, lambda t: dict(t=t)),
    'attack': (3, lambda t: dict(t=t, att=[0.2, 1.0, 0.6][min(2, int(t * 3))])),
    'hurt': (1, lambda t: dict(t=0.3, att=0.5)),
}


# ------------------------------------------------------------ AĞAÇ İYESİ
def draw_treant(c, p):
    bob, lean = p.get('bob', 0.0), p.get('lean', 0.0)
    grooves = lambda lu, lv, px, py: (np.floor(px + np.floor(py / 6) * 2) % 5 == 0)
    sh = (0 + math.sin(lean) * 40, -44 + bob)
    # kökler
    for dx, a in ((-10, -0.6), (-4, -0.2), (5, 0.3), (11, 0.7)):
        c.capsule((dx * 0.5, -6 + bob * 0.3), (dx + math.sin(a) * 6 + p.get('step', 0.0) * (1 if dx > 0 else -1), 0), 3.2, 1.6, M['bark'], z=-2, paint=[(grooves, BARK2)])
    # arka kol
    al = p.get('al', (0.3, 0.4))
    e, h = fk_arm((sh[0] - 7, sh[1] + 4), al[0], al[1], 13, 12)
    c.capsule((sh[0] - 7, sh[1] + 4), e, 4.2, 3.4, BARK2, z=-8)
    c.capsule(e, h, 3.4, 2.4, BARK2, z=-8)
    for k in (-0.5, 0.0, 0.5):
        a = al[0] + al[1] + k
        c.capsule(h, (h[0] + math.sin(a) * 6, h[1] + math.cos(a) * 6), 1.4, 0.6, BARK2, z=-8)
    # gövde
    c.poly([(-11, -2), (11, -2), (13 + sh[0] * 0.2, -30 + bob), (12 + sh[0], -46 + bob), (-12 + sh[0], -46 + bob), (-13 + sh[0] * 0.2, -30 + bob)],
           M['bark'], z=0, bevel=5, height=5, paint=[(grooves, BARK2)])
    # taç: rengârenk yapraklar
    cx, cy = sh[0], -54 + bob
    rng = np.random.RandomState(4)
    for i in range(34):
        a = rng.uniform(0, math.tau); r = rng.uniform(2, 15)
        mat = [M['leaf'], M['moss'], LEAF_O, LEAF_R, M['leaf']][i % 5]
        c.ellipse((cx + math.cos(a) * r * 1.25, cy + math.sin(a) * r * 0.7), rng.uniform(2.5, 4.5), rng.uniform(2.0, 3.4), mat, z=2 + rng.uniform(0, 4), rot=rng.uniform(0, 3))
    for dx, a in ((-6, -0.5), (5, 0.6), (0, 0)):
        c.capsule((cx + dx * 0.4, cy + 8), (cx + dx + math.sin(a) * 8, cy - 4), 2.0, 1.0, M['bark'], z=1.5)
    # yüz (gövdedeki budak)
    fx, fy = sh[0] * 0.8 - 1.5, -35 + bob
    c.ellipse((fx, fy), 7.5, 8.0, M['bark'], z=6, paint=[(grooves, BARK2)])
    for ex in (-2.6, 2.8):
        c.ellipse((fx + ex, fy - 1.5), 1.9, 2.4, M['black'], z=24)
        c.ellipse((fx + ex + 0.3, fy - 1.6), 0.9, 1.1, M['amber'], z=28)
    c.poly([(fx - 3, fy + 3.5), (fx + 3.5, fy + 3.0), (fx + 1.5, fy + 5.5 + p.get('roar', 0.0) * 2), (fx - 2, fy + 5.0 + p.get('roar', 0.0) * 2)], M['black'], z=24, bevel=0.5, height=0.3)
    # yosun + sinek mantarları
    sp = lambda lu, lv, px, py: (np.sin(px * 3.1 + py * 1.7) > 0.6)
    c.ellipse((-7 + sh[0] * 0.4, -24 + bob), 5.0, 3.0, M['moss'], z=7, paint=[(sp, M['grass_hi'])])
    c.ellipse((8, -12 + bob * 0.5), 4.0, 2.4, M['moss'], z=7, paint=[(sp, M['grass_hi'])])
    for mx_, my_, r in ((-10 + sh[0], -45 + bob, 3.4), (-6.5 + sh[0], -47 + bob, 2.5), (10, -10, 2.2)):
        c.capsule((mx_, my_ + r * 0.4), (mx_, my_ + r * 1.4), 0.9, 0.9, M['bone'], z=8)
        dots = lambda lu, lv, px, py: (np.sin(px * 5.3) * np.sin(py * 4.7) > 0.55) & (lv < 0.2)
        c.ellipse((mx_, my_), r, r * 0.65, M['amanita'], z=9, paint=[(dots, M['nazar_w'])])
    # ön kol
    ar = p.get('ar', (0.2, 0.5))
    e, h = fk_arm((sh[0] + 12, sh[1] + 4), ar[0], ar[1], 13, 13)
    c.capsule((sh[0] + 12, sh[1] + 4), e, 4.6, 3.8, M['bark'], z=12, paint=[(grooves, BARK2)])
    c.capsule(e, h, 3.8, 2.8, M['bark'], z=12, paint=[(grooves, BARK2)])
    for k in (-0.55, 0.0, 0.55):
        a = ar[0] + ar[1] + k
        c.capsule(h, (h[0] + math.sin(a) * 7, h[1] + math.cos(a) * 7), 1.6, 0.6, M['bark'], z=12)
    c.ellipse(lerp2(e, h, 0.4), 3.0, 1.8, M['moss'], z=13)
    return {'hand': h}


TREANT = {
    'idle': (4, lambda t: dict(bob=round(math.sin(t * 6.28)) * 0.6, lean=0.02 * math.sin(t * 6.28))),
    'walk': (6, lambda t: dict(bob=-abs(math.sin(t * 6.28)) * 1.2, lean=0.04 * math.sin(t * 6.28), step=2 * math.sin(t * 6.28),
                               al=(0.3 + 0.2 * math.sin(t * 6.28), 0.4), ar=(0.2 - 0.2 * math.sin(t * 6.28), 0.5))),
    'windup': (2, lambda t: dict(bob=-1, lean=-0.05, ar=(-2.6, 0.4), al=(0.6, 0.6), roar=1.0)),
    'slam': (2, lambda t: dict(bob=2, lean=0.08, ar=(1.2, 0.2), al=(0.2, 0.4), roar=0.6)),
    'hurt': (1, lambda t: dict(bob=1, lean=-0.06, ar=(-0.5, 0.6), al=(-0.3, 0.5))),
}


# ------------------------------------------------------------ BALBAL (canlanan taş heykel)
def draw_balbal(c, p):
    bob, sq = p.get('bob', 0.0), p.get('squash', 0.0)
    awake = p.get('awake', 1.0)
    W_ = 9 + sq * 2
    H_ = 44 - sq * 6
    lich = lambda lu, lv, px, py: (np.sin(px * 1.9 + 1) * np.sin(py * 2.3) > 0.72)
    crack = lambda lu, lv, px, py: np.abs((px - 2) * 0.8 - (py + 20) * 0.3) < 0.5
    # kaide
    c.poly([(-11, 0), (11, 0), (10, -5), (-10, -5)], STONE2, z=-2, bevel=2, height=2)
    # gövde
    c.poly([(-W_, -4 + bob), (W_, -4 + bob), (W_ - 1, -H_ * 0.62 + bob), (-W_ + 1, -H_ * 0.62 + bob)], M['stone'], z=0, bevel=2.6, height=3,
           paint=[(lich, M['lichen']), (crack, STONE2)])
    # kemer ve kılıç
    c.capsule((-W_ + 1, -16 + bob), (W_ - 1, -16 + bob), 1.4, 1.4, STONE2, z=4)
    sw = p.get('sword', 0.0)
    if sw > 0:
        ang = p.get('swang', 1.2)
        base = (W_ - 2, -22 + bob)
        tip = (base[0] + math.sin(ang) * 22, base[1] + math.cos(ang) * 22)
        c.capsule(base, tip, 1.8, 1.0, M['stone'], z=14, paint=[(lich, M['lichen'])])
        c.capsule((base[0] - 3 * math.cos(ang), base[1] + 3 * math.sin(ang)), (base[0] + 3 * math.cos(ang), base[1] - 3 * math.sin(ang)), 1.2, 1.2, STONE2, z=15)
    else:
        c.poly([(-4, -15 + bob), (-1, -15 + bob), (-3, -2 + bob), (-5.5, -3 + bob)], STONE2, z=5, bevel=1, height=1)
    # kollar + kadeh
    c.capsule((W_ - 1, -24 + bob), (W_ - 3, -17 + bob), 2.6, 2.4, M['stone'], z=6)
    c.capsule((W_ - 3, -17 + bob), (3, -20 + bob), 2.4, 2.2, M['stone'], z=7)
    c.poly([(0.5, -25 + bob), (6, -25 + bob), (5, -20 + bob), (1.5, -20 + bob)], M['gold'], z=9, bevel=1.2, height=1.5)
    c.capsule((-W_ + 1, -24 + bob), (-W_ + 2, -15 + bob), 2.4, 2.2, M['stone'], z=-3)
    # baş
    hy = -H_ * 0.62 - 7 + bob
    c.poly([(-6.5, hy + 7), (6.5, hy + 7), (7, hy - 4), (4, hy - 8), (-4, hy - 8), (-7, hy - 4)], M['stone'], z=3, bevel=2.4, height=3,
           paint=[(lich, M['lichen'])])
    c.capsule((-3.5, hy - 1.6), (-0.8, hy - 1.4), 0.7, 0.7, STONE2, z=9)
    c.capsule((2.0, hy - 1.4), (4.8, hy - 1.6), 0.7, 0.7, STONE2, z=9)
    eye = M['eye_red'] if awake > 0.5 else STONE2
    c.dot((-2.2, hy - 0.4), eye, z=20, size=1); c.dot((3.4, hy - 0.4), eye, z=20, size=1)
    c.capsule((-3.2, hy + 3.0), (0.6, hy + 2.2), 0.9, 0.6, STONE2, z=10)
    c.capsule((0.6, hy + 2.2), (4.6, hy + 3.0), 0.6, 0.9, STONE2, z=10)
    c.capsule((0.6, hy - 0.5), (1.2, hy + 2.0), 0.9, 0.9, M['stone'], z=11)
    return {}


BALBAL = {
    'idle': (2, lambda t: dict(awake=1.0, bob=0)),
    'dormant': (1, lambda t: dict(awake=0.0)),
    'hop': (4, lambda t: dict(squash=[0.8, 0.0, -0.4, 0.4][min(3, int(t * 4))], bob=[0, -3, -4, 0][min(3, int(t * 4))])),
    'windup': (2, lambda t: dict(sword=1, swang=math.pi + 0.5, bob=-1)),
    'strike': (2, lambda t: dict(sword=1, swang=1.25 - 0.2 * t, bob=1, squash=0.3)),
}


# ------------------------------------------------------------ ARÇURA (orman cini, yanıltıcı)
LEAFCLOAK = Mat(ramp(96, 0.55, 0.42, spread=0.45), name='yaprak pelerin')
GOBSKIN = Mat(ramp(70, 0.35, 0.55, spread=0.4), name='cin derisi')
HAT = Mat(ramp(18, 0.55, 0.32), name='keçe külah')


def draw_arcura(c, p):
    bob = p.get('bob', 0.0)
    lean = p.get('lean', 0.0)
    cast = p.get('cast', 0.0)
    hip = (0, -12 + bob)
    # bacaklar: ince, eğri
    for side, (a1, a2) in ((-1, p.get('lb', (0.3, 0.3))), (1, p.get('lf', (-0.2, 0.3)))):
        k, f = fk_leg((hip[0] + side * 2, hip[1]), a1, a2, 6.0, 6.0)
        c.capsule((hip[0] + side * 2, hip[1]), k, 1.6, 1.3, GOBSKIN, z=-4 if side < 0 else 4)
        c.capsule(k, f, 1.3, 1.1, GOBSKIN, z=-4 if side < 0 else 4)
        c.capsule(f, (f[0] + 3, f[1] - 0.3), 1.2, 0.8, GOBSKIN, z=-3.9 if side < 0 else 4.1)
    # yaprak pelerin: gövdeyi saran, uçları sivri
    leaf = lambda lu, lv, px, py: (np.floor(px * 0.6 + py * 0.3) % 3 == 0)
    c.poly([(-7, hip[1] - 9), (7 + lean * 4, hip[1] - 9), (9, hip[1] + 2), (5, hip[1] + 5), (1, hip[1] + 2), (-3, hip[1] + 5), (-8, hip[1] + 1)],
           LEAFCLOAK, z=0, bevel=2.4, height=2, paint=[(leaf, M['moss'])])
    # baş: iri, uzun burun, sivri kulaklar, külah
    hd = (1.5 + lean * 3, hip[1] - 15)
    c.ellipse(hd, 5.2, 4.6, GOBSKIN, z=6)
    c.capsule((hd[0] + 3, hd[1] + 0.5), (hd[0] + 9, hd[1] + 2.5), 1.3, 0.8, GOBSKIN, z=8)
    c.poly([(hd[0] - 4, hd[1] - 1), (hd[0] - 9, hd[1] - 4), (hd[0] - 4, hd[1] + 1.5)], GOBSKIN, z=5, bevel=0.8, height=0.8)
    c.poly([(hd[0] - 5, hd[1] - 3), (hd[0] + 5, hd[1] - 3), (hd[0] + 1 + cast * 2, hd[1] - 16 - cast * 2)], HAT, z=7, bevel=1.4, height=1.5)
    c.capsule((hd[0] - 5.5, hd[1] - 3), (hd[0] + 5.5, hd[1] - 3), 1.1, 1.1, M['red_paint'], z=8)
    c.dot((hd[0] + 0.5, hd[1] - 0.5), M['amber'], z=20); c.dot((hd[0] + 3.2, hd[1] - 0.5), M['amber'], z=20)
    c.capsule((hd[0] + 0.5, hd[1] + 2.5), (hd[0] + 3.5, hd[1] + 2.5 + cast), 0.5, 0.5, M['black'], z=18)
    # kollar: büyü yaparken ileri uzanır, parmak uçlarında kıvılcım
    ar = p.get('ar', (0.4, 0.5))
    e, h = fk_arm((hip[0] + 4, hip[1] - 7), ar[0], ar[1], 6.0, 6.0)
    c.capsule((hip[0] + 4, hip[1] - 7), e, 1.5, 1.3, LEAFCLOAK, z=10)
    c.capsule(e, h, 1.3, 1.1, GOBSKIN, z=10)
    for k in range(3):
        c.capsule(h, (h[0] + 2.5 + k * 0.4, h[1] - 1.5 + k * 1.3), 0.5, 0.35, GOBSKIN, z=11)
    if cast > 0.3:
        c.ellipse((h[0] + 4, h[1]), 2.2 * cast, 2.2 * cast, M['corrupt'], z=14)
    e2, h2 = fk_arm((hip[0] - 3, hip[1] - 7), -0.3, 0.6, 6.0, 6.0)
    c.capsule((hip[0] - 3, hip[1] - 7), e2, 1.4, 1.2, LEAFCLOAK, z=-6)
    c.capsule(e2, h2, 1.2, 1.0, GOBSKIN, z=-6)
    return {'hand': h}


ARCURA = {
    'idle': (4, lambda t: dict(bob=0.6 * math.sin(t * 6.28), lean=0.0, ar=(0.4 + 0.1 * math.sin(t * 6.28), 0.5))),
    'run': (6, lambda t: dict(bob=-abs(math.sin(t * 6.28)) * 1.5, lean=0.25, lb=(0.8 * math.sin(t * 6.28), 0.5 + 0.5 * max(0, -math.sin(t * 6.28))),
                              lf=(-0.8 * math.sin(t * 6.28), 0.5 + 0.5 * max(0, math.sin(t * 6.28))), ar=(0.9, 0.6))),
    'cast': (3, lambda t: dict(bob=[-1, -2, 0][min(2, int(t * 3))], lean=-0.1, cast=[0.4, 1.0, 0.7][min(2, int(t * 3))], ar=[(0.8, 0.9), (1.5, 0.1), (1.3, 0.3)][min(2, int(t * 3))])),
    'hurt': (1, lambda t: dict(bob=1, lean=-0.2, ar=(-0.6, 0.8))),
}


# ------------------------------------------------------------ ŞÜRALE (uzun parmaklı orman yaratığı)
SURSKIN = Mat(ramp(48, 0.35, 0.5, spread=0.45), name='şürale derisi')
SURHAIR = Mat(ramp(95, 0.6, 0.35, spread=0.4), name='yosun saç')


def draw_surale(c, p):
    bob = p.get('bob', 0.0)
    lean = p.get('lean', 0.0)
    grab = p.get('grab', 0.0)
    hip = (0, -34 + bob)
    neck = (hip[0] + math.sin(lean) * 26, hip[1] - math.cos(lean) * 26)
    # bacaklar: uzun, dizleri geriye kırık (keçi gibi)
    for side, (a1, a2) in ((-1, p.get('lb', (0.3, 0.5))), (1, p.get('lf', (-0.2, 0.5)))):
        k, f = fk_leg((hip[0] + side * 2.5, hip[1]), a1, a2, 17.0, 17.0)
        c.capsule((hip[0] + side * 2.5, hip[1]), k, 2.6, 2.0, SURSKIN, z=-6 if side < 0 else 6)
        c.capsule(k, f, 2.0, 1.4, SURSKIN, z=-6 if side < 0 else 6)
        c.poly([(f[0] - 2, f[1]), (f[0] + 3, f[1] - 3), (f[0] + 5, f[1])], M['bone'], z=-5.9 if side < 0 else 6.1, bevel=0.8, height=0.8)
    # gövde: sıska, kaburgalı
    ribs = lambda lu, lv, px, py: (np.floor(py * 0.6) % 2 == 0) & (lu > 0.1) & (lv > -0.3) & (lv < 0.4)
    c.capsule(hip, neck, 6.5, 4.5, SURSKIN, z=0, paint=[(ribs, Mat(ramp(40, 0.4, 0.35)))])
    # yosun saç ve tek boynuz
    hd = (neck[0] + 2, neck[1] - 6)
    for k in range(7):
        a = -2.2 + k * 0.45
        c.capsule((hd[0] - 1, hd[1] - 3), (hd[0] - 1 + math.cos(a) * 9, hd[1] - 3 + math.sin(a) * 9 + 4), 1.6, 0.6, SURHAIR, z=3)
    c.ellipse(hd, 5.6, 5.0, SURSKIN, z=6)
    c.poly([(hd[0] - 1, hd[1] - 4), (hd[0] + 2, hd[1] - 4), (hd[0] + 2, hd[1] - 13)], M['bone'], z=7, bevel=1, height=1)
    c.capsule((hd[0] + 3, hd[1] + 1.5), (hd[0] + 9, hd[1] + 3.5), 1.6, 0.9, SURSKIN, z=8)
    c.dot((hd[0] + 1.5, hd[1] - 0.5), M['eye_red'], z=20); c.dot((hd[0] + 4.5, hd[1] - 0.5), M['eye_red'], z=20)
    jaw = 0.5 + grab * 2.0
    c.poly([(hd[0] + 1, hd[1] + 3), (hd[0] + 8, hd[1] + 4.5), (hd[0] + 7, hd[1] + 4.5 + jaw), (hd[0] + 1, hd[1] + 3.5 + jaw)], M['black'], z=19, bevel=0.5, height=0.3)
    for k in range(3):
        c.dot((hd[0] + 2.5 + k * 1.8, hd[1] + 3.5), M['bone'], z=21)
    # kollar: çok uzun; parmaklar 3 uzun kıvrık
    for side, z, a in ((-1, -8, p.get('ab', (0.4, 0.6))), (1, 10, p.get('af', (0.2, 0.7)))):
        sh = (neck[0] + side * 4, neck[1] + 3)
        e, h = fk_arm(sh, a[0], a[1], 16.0, 15.0)
        c.capsule(sh, e, 2.4, 1.8, SURSKIN, z=z)
        c.capsule(e, h, 1.8, 1.3, SURSKIN, z=z)
        ang = a[0] + a[1]
        for k in range(3):
            fa = ang + (k - 1) * 0.5 + grab * 0.5
            tip = (h[0] + math.sin(fa) * 10, h[1] + math.cos(fa) * 10)
            mid = (h[0] + math.sin(fa - 0.3 * grab) * 5, h[1] + math.cos(fa - 0.3 * grab) * 5)
            c.capsule(h, mid, 1.0, 0.7, SURSKIN, z=z + 0.5)
            c.capsule(mid, tip, 0.7, 0.4, M['bone'], z=z + 0.6)
    return {}


SURALE = {
    'idle': (4, lambda t: dict(bob=0.8 * math.sin(t * 6.28), lean=0.1, ab=(0.4 + 0.1 * math.sin(t * 6.28), 0.6), af=(0.2, 0.7 + 0.1 * math.sin(t * 6.28)))),
    'walk': (6, lambda t: dict(bob=-abs(math.sin(t * 6.28)) * 2.0, lean=0.2, lb=(0.7 * math.sin(t * 6.28), 0.4 + 0.5 * max(0, -math.sin(t * 6.28))),
                               lf=(-0.7 * math.sin(t * 6.28), 0.4 + 0.5 * max(0, math.sin(t * 6.28))), ab=(0.6, 0.6), af=(0.3, 0.8))),
    'windup': (2, lambda t: dict(bob=2, lean=-0.15, ab=(-0.9, 0.9), af=(-1.1, 1.0), grab=0.5)),
    'grab': (2, lambda t: dict(bob=-1, lean=0.45, ab=(1.3, 0.1), af=(1.45, 0.0), grab=1.0)),
    'hurt': (1, lambda t: dict(bob=1, lean=-0.2, ab=(-0.4, 0.7), af=(-0.5, 0.8))),
}


# ------------------------------------------------------------ BOZKURT (Bengü'nün ruh biçimi)
SFUR = Mat(ramp(205, 0.08, 0.96, spread=0.3), name='ak ruh postu')
SFUR_D = Mat(ramp(200, 0.25, 0.7, spread=0.35), name='ruh postu gölgesi')
SMANE = Mat(ramp(172, 0.7, 0.95, spread=0.25), emissive=0.7, outline='#0b4a52', name='kut yelesi')


def draw_spirit_wolf(c, p):
    """Büyük ruh kurdu: kara börünün 1.6 katı; ak post, kut ışığıyla yanan yele ve gözler, turkuaz atkı.
    Pozlar: bob, tilt, jaw, hb/hf/fb/ff bacak açıları, tw kuyruk, hy baş, crouch (sıçrama hazırlığı), howl (uluma)."""
    K = 1.6
    bob, tilt, jaw = p.get('bob', 0.0), p.get('tilt', 0.0), p.get('jaw', 0.0)
    howl = p.get('howl', 0.0)
    crouch = p.get('crouch', 0.0)
    hipp = (-9.5 * K, (-17 + bob - tilt * 6) * K + crouch * 6)
    shp = (8.5 * K, (-18 + bob + tilt * 6) * K + crouch * 6)
    back_dark = lambda lu, lv, px, py: lv < -0.35
    fur_s = lambda lu, lv, px, py: (np.floor(px * 0.5 - py * 0.8) % 5 == 0) & (lv < 0.2)

    def leg(base, a, z, front):
        if front:
            k, f = fk_leg(base, a[0], a[1], 8.5 * K, 9.0 * K)
        else:
            k, f = fk_leg(base, a[0], a[1], 8.0 * K, 9.5 * K)
        mat = SFUR if z > 0 else SFUR_D
        c.capsule(base, k, (3.4 if not front else 3.0) * K, 2.3 * K, mat, z=z)
        c.capsule(k, f, 2.2 * K, 1.7 * K, mat, z=z)
        c.ellipse((f[0] + 1.3 * K, f[1] - 0.8 * K), 2.3 * K, 1.4 * K, mat, z=z + 0.1)
        for i in range(3):
            c.dot((f[0] + (2.6 + i * 0.1) * K, f[1] - 1.6 * K + i * K), M['bone'], z=z + 2)
        return f

    leg(hipp, p['hb'], -8, False)
    leg(shp, p['fb'], -8, True)
    # kuyruk: uzun, uçta kut alevi
    tl = chain((hipp[0] - 4 * K, hipp[1] - 2 * K), 6, 3.6 * K, math.pi * 1.12 + p.get('tw', 0.0), -0.12, p.get('ph', 0.0), 0.25)
    for i, (a, b) in enumerate(zip(tl, tl[1:])):
        c.capsule(a, b, (3.0 - i * 0.3) * K, (2.6 - i * 0.3) * K, SFUR if i < 4 else SMANE, z=-6)
    # gövde
    c.ellipse(hipp, 7.6 * K, 7.0 * K, SFUR, z=0, paint=[(back_dark, SFUR_D), (fur_s, SFUR_D)])
    c.capsule(hipp, shp, 6.3 * K, 7.0 * K, SFUR, z=1, paint=[(back_dark, SFUR_D), (fur_s, SFUR_D)])
    c.ellipse(shp, 8.0 * K, 8.4 * K, SFUR, z=2, paint=[(back_dark, SFUR_D), (fur_s, SFUR_D)])
    # sırt yelesi: kut ışığıyla yanan alev dilleri
    for k, (t, h) in enumerate(((0.1, 7), (0.3, 10), (0.5, 9), (0.7, 8), (0.88, 6))):
        bx, by = lerp2(hipp, shp, t)
        by -= 6.5 * K
        sway = math.sin(p.get('ph', 0.0) + k) * 1.5
        c.poly([(bx - 2.4 * K, by + 2), (bx + 2.4 * K, by + 2), (bx + 0.6 * K + sway, by - h * K)], SMANE, z=6, bevel=1.4, height=2)
    # turkuaz atkı (boyunda)
    c.capsule((shp[0] - 4 * K, shp[1] - 4 * K), (shp[0] + 5 * K, shp[1] - 2 * K), 2.2 * K, 2.0 * K, M['turq'], z=5)
    sc = chain((shp[0] - 5 * K, shp[1] - 3 * K), 4, 4.0 * K, math.pi * 0.95 + p.get('tw', 0.0) * 0.5, 0.05, p.get('ph', 0.0), 0.35)
    for i, (a, b) in enumerate(zip(sc, sc[1:])):
        c.capsule(a, b, (1.8 - i * 0.25) * K, (1.6 - i * 0.25) * K, M['turq'], z=-5)
    # boyun + baş
    hy_off = p.get('hy', 0.0) * K - howl * 10
    head = (shp[0] + 9.5 * K - howl * 3, shp[1] - 6 * K + hy_off)
    c.capsule((shp[0] + 2 * K, shp[1] - 2 * K), head, 5.6 * K, 4.6 * K, SFUR, z=4, paint=[(back_dark, SFUR_D)])
    hx_, hy_ = head
    c.ellipse(head, 5.4 * K, 4.6 * K, SFUR, z=6, paint=[(back_dark, SFUR_D)])
    c.poly([(hx_ - 3.5 * K, hy_ - 2.5 * K), (hx_ - 0.6 * K, hy_ - 3.5 * K), (hx_ - 2.4 * K, hy_ - 9.5 * K)], SFUR, z=7, bevel=1.2, height=1.5)
    c.poly([(hx_ - 0.4 * K, hy_ - 3.6 * K), (hx_ + 2.0 * K, hy_ - 3.0 * K), (hx_ + 0.2 * K, hy_ - 9.0 * K)], SFUR_D, z=6.5, bevel=1.2, height=1.5)
    # burun: ulurken yukarı kalkar
    ang = -howl * 0.9
    sn1 = (hx_ + 2.5 * K + math.cos(ang) * 8 * K, hy_ + 0.6 * K + math.sin(ang) * 8 * K)
    c.capsule((hx_ + 2.5 * K, hy_ + 0.6 * K), sn1, 3.0 * K, 1.9 * K, SFUR, z=8)
    c.ellipse((sn1[0] + 0.5 * K, sn1[1] - 0.4 * K), 1.2 * K, 1.0 * K, M['black'], z=10)
    jd = (jaw + howl * 0.5) * 3.2 * K
    jaw0 = (hx_ + 2.5 * K, hy_ + 3.0 * K)
    jaw1 = (hx_ + 2.5 * K + math.cos(ang + 0.15) * 7 * K, hy_ + 3.0 * K + math.sin(ang + 0.15) * 7 * K + jd)
    c.capsule(jaw0, jaw1, 1.7 * K, 1.1 * K, SFUR_D, z=7.5)
    if jaw + howl > 0.2:
        c.poly([(hx_ + 4 * K, hy_ + 2.6 * K), (sn1[0] - 1, sn1[1] + 2.2 * K), (jaw1[0], jaw1[1] - 1), (hx_ + 4 * K, hy_ + 3.4 * K + jd * 0.5)], M['red_paint'], z=7.4, bevel=0.5, height=0.3)
    for i in range(4):
        c.dot((hx_ + (4.4 + i * 1.6) * K, hy_ + 2.4 * K), M['bone'], z=12, size=2)
    # göz: kut ışığı; savaş boyası
    c.capsule((hx_ + 1.0 * K, hy_ - 1.8 * K), (hx_ + 3.8 * K, hy_ - 1.2 * K), 0.9 * K, 0.8 * K, M['kut'], z=20)
    c.capsule((hx_ + 0.2 * K, hy_ + 0.8 * K), (hx_ + 2.2 * K, hy_ + 2.6 * K), 0.6, 0.6, M['red_paint'], z=14)
    leg(hipp, p['hf'], 8, False)
    leg(shp, p['ff'], 8, True)
    return {'mouth': (sn1[0], sn1[1] + 2 * K)}


def _swolf_run(t):
    ph = t * math.tau
    s, s2 = math.sin(ph), math.sin(ph + 0.6)
    return dict(bob=-abs(math.cos(ph)) * 1.8 + 0.6, tilt=0.14 * math.sin(ph),
                hb=(0.95 * s, 0.9 - 0.4 * s), hf=(0.95 * s2, 0.9 - 0.4 * s2),
                fb=(-0.95 * s + 0.1, 0.2 + 0.8 * max(0, s)), ff=(-0.95 * s2 + 0.1, 0.2 + 0.8 * max(0, s2)), tw=-0.2, ph=ph, jaw=0.2)


SPIRIT_WOLF = {
    'idle': (6, lambda t: dict(bob=0.5 * math.sin(t * 6.28), hb=(0.25, 0.9), hf=(0.1, 0.8), fb=(-0.05, 0.1), ff=(0.08, 0.1), tw=0.1 * math.sin(t * 6.28), ph=t * 6.28, jaw=0.1)),
    'run': (8, _swolf_run),
    'bite': (5, lambda t: [dict(bob=2.0, tilt=-0.12, hb=(0.5, 1.5), hf=(0.4, 1.4), fb=(0.4, 1.0), ff=(0.5, 1.1), tw=0.4, jaw=0.9, hy=1.5, ph=0.0),
                           dict(bob=-1.5, tilt=0.0, hb=(-0.8, 0.3), hf=(-0.7, 0.4), fb=(1.0, 0.2), ff=(1.1, 0.3), tw=-0.3, jaw=1.0, hy=0.5, ph=1.0),
                           dict(bob=-2.0, tilt=0.06, hb=(-1.0, 0.2), hf=(-0.9, 0.3), fb=(1.2, 0.2), ff=(1.3, 0.3), tw=-0.5, jaw=0.0, hy=0.0, ph=2.0),
                           dict(bob=-1.0, tilt=0.04, hb=(-0.6, 0.4), hf=(-0.5, 0.5), fb=(0.9, 0.3), ff=(1.0, 0.3), tw=-0.4, jaw=0.1, hy=0.0, ph=3.0),
                           dict(bob=0.0, tilt=0.0, hb=(0.2, 0.9), hf=(0.1, 0.8), fb=(0.0, 0.2), ff=(0.1, 0.2), tw=0.0, jaw=0.2, hy=0.0, ph=4.0)][min(4, int(t * 5))]),
    'pounce': (4, lambda t: [dict(bob=3.5, tilt=-0.2, crouch=1.0, hb=(0.7, 1.7), hf=(0.6, 1.6), fb=(0.6, 1.3), ff=(0.7, 1.4), tw=0.5, jaw=0.4, hy=2.5),
                             dict(bob=-2.0, tilt=-0.1, hb=(-1.1, 0.3), hf=(-1.0, 0.4), fb=(1.3, 0.2), ff=(1.4, 0.3), tw=-0.5, jaw=1.0, hy=0.0),
                             dict(bob=-2.5, tilt=0.02, hb=(-1.2, 0.2), hf=(-1.1, 0.3), fb=(1.4, 0.2), ff=(1.5, 0.3), tw=-0.6, jaw=1.0, hy=0.0),
                             dict(bob=0.5, tilt=0.1, hb=(0.3, 1.0), hf=(0.2, 0.9), fb=(0.4, 0.6), ff=(0.5, 0.7), tw=0.2, jaw=0.3, hy=0.5)][min(3, int(t * 4))]),
    'howl': (4, lambda t: dict(bob=0.5, tilt=-0.25, hb=(0.4, 1.0), hf=(0.3, 0.9), fb=(0.2, 0.3), ff=(0.3, 0.3), tw=0.6, howl=[0.4, 1.0, 1.0, 0.7][min(3, int(t * 4))], ph=t * 6.28)),
    'hurt': (2, lambda t: dict(bob=1, tilt=0.2, hb=(0.3, 0.9), hf=(0.2, 0.8), fb=(-0.3, 0.3), ff=(-0.2, 0.2), tw=0.6, jaw=0.5, hy=-1)),
}

CREATURES = {
    'kara_boru': (draw_wolf, WOLF, (80, 56), (36, 52)),
    'cor': (draw_cor, COR, (64, 76), (28, 70)),
    'agac_iyesi': (draw_treant, TREANT, (112, 104), (52, 100)),
    'balbal': (draw_balbal, BALBAL, (72, 72), (30, 68)),
    'arcura': (draw_arcura, ARCURA, (64, 64), (30, 60)),
    'surale': (draw_surale, SURALE, (112, 104), (50, 100)),
    'bengu_kurt': (bozkurt.draw_bozkurt, bozkurt.BOZKURT_ANIMS, bozkurt.CELL, bozkurt.FEET),
}


def render_creature(name, anim, i):
    draw, anims, cell, feet = CREATURES[name]
    n, fn = anims[anim]
    t = i / n
    p = fn(t)
    c = Canvas(cell[0], cell[1], feet[0], feet[1])
    info = draw(c, p)
    rgba = c.shade()
    nm = c.normal_map(rgba[..., 3])
    return c, rgba, nm, info
