"""Silah üreteci: her düşen silah benzersiz statlarla yuvarlanır + silah sprite tarifleri.

Kural: veri dosyasındaki her aralık [en kötü, en iyi] sırasındadır; kalite puanı
buna göre hesaplanır. Aynı silah tipi bile her düşüşte farklı statlarla gelir.
"""
import json
import math
import os
import random

from raster import Canvas, Mat, ramp, hx
from materials import M

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = json.load(open(os.path.join(ROOT, 'data', 'weapons.json'), encoding='utf-8'))
ARCH = {a['id']: a for a in DATA['archetypes']}
MATS = {m['id']: m for m in DATA['materials']}
AFF = {a['id']: a for a in DATA['affixes']}


def _wpick(items, weights, rng):
    tot = sum(weights)
    r = rng.random() * tot
    for it, w in zip(items, weights):
        r -= w
        if r <= 0:
            return it
    return items[-1]


def _roll_range(rng_, r, is_int):
    lo, hi = min(r), max(r)
    v = rng_.uniform(lo, hi)
    if is_int:
        v = round(v)
    q = 0.5 if r[0] == r[1] else (v - r[0]) / (r[1] - r[0])
    return v, max(0.0, min(1.0, q))


def roll_weapon(arch_id, tier=0, rng=None, material=None, rarity=None, flaw=None):
    rng = rng or random.Random()
    A = ARCH[arch_id]
    mat = MATS[material] if material else _wpick(DATA['materials'], [m['weight'][tier] for m in DATA['materials']], rng)
    rar_i = rarity if rarity is not None else DATA['rarities'].index(_wpick(DATA['rarities'], [r['weight'][tier] for r in DATA['rarities']], rng))
    R = DATA['rarities'][rar_i]
    qs = []
    dq = rng.uniform(0.85, 1.15); qs.append((dq - 0.85) / 0.3)
    sq = rng.uniform(0.92, 1.08); qs.append((sq - 0.92) / 0.16)
    dmg = A['dmg'] * mat['dmg'] * (1 + 0.6 * tier) * dq
    aps = A['aps'] * mat['speed'] * sq
    crit = max(0, A['crit'] + mat['crit'] + rng.uniform(-2, 3))
    crit_mult = A['crit_mult'] + mat['crit_mult']
    mv, mq = _roll_range(rng, A['mech']['range'], A['mech'].get('int'))
    qs.append(mq)
    n_aff = R['affixes'] + (1 if mat['id'] == 'yildiz' else 0)
    pool = [a for a in DATA['affixes'] if A['kind'] in a['kinds']]
    rng.shuffle(pool)
    affixes = []
    for a in pool[:n_aff]:
        v, q = _roll_range(rng, a['range'], a.get('int'))
        affixes.append({'id': a['id'], 'v': v, 'q': q})
        qs.append(q)
    if flaw is None:
        flaw = rng.choice(DATA['flaws']) if rng.random() < 0.18 else None
    elif flaw:
        flaw = next(f for f in DATA['flaws'] if f['id'] == flaw)
    if flaw:
        dmg *= 1.15
    epithet = rng.choice(DATA['epithets']) if R['id'] == 'efsane' else None
    w = {
        'arch': arch_id, 'tier': tier, 'material': mat['id'], 'rarity': rar_i, 'dmg': dmg, 'aps': aps,
        'crit': crit, 'crit_mult': crit_mult, 'mech_v': mv, 'affixes': affixes, 'flaw': flaw['id'] if flaw else None,
        'epithet': epithet, 'quality': round(100 * sum(qs) / len(qs)), 'seed': rng.randrange(1 << 30),
    }
    return w


def fmt_v(v):
    if isinstance(v, int) or float(v).is_integer() or abs(v) >= 10:
        return str(int(round(v)))
    return ('%.1f' % v).replace('.', ',')


def weapon_name(w):
    A = ARCH[w['arch']]
    mat = MATS[w['material']]
    pre = AFF[w['affixes'][0]['id']]['adj'] + ' ' if w['affixes'] else ''
    return pre + mat['adj'] + ' ' + A['name']


def dps(w):
    hs = 1 + sum(a['v'] for a in w['affixes'] if a['id'] == 'hiz') / 100
    hd = 1 + sum(a['v'] for a in w['affixes'] if a['id'] == 'hasar') / 100
    cc = min(100, w['crit'] + sum(a['v'] for a in w['affixes'] if a['id'] == 'krit_sans')) / 100
    cm = w['crit_mult'] + sum(a['v'] for a in w['affixes'] if a['id'] == 'krit_hasar') / 100
    flaw_slow = 0.88 if w['flaw'] == 'agir' else 1
    return w['dmg'] * hd * w['aps'] * hs * flaw_slow * (1 + cc * (cm - 1))


def describe(w):
    A = ARCH[w['arch']]
    lines = [A['mech']['desc'].replace('{v}', fmt_v(w['mech_v']))]
    for a in w['affixes']:
        lines.append(AFF[a['id']]['desc'].replace('{v}', fmt_v(a['v'])))
    return lines


# ------------------------------------------------------------ sprite tarifleri
def weapon_mats(mat_id):
    m = MATS[mat_id]
    if mat_id == 'obsidyen':
        blade = Mat(ramp(m['hue'], m['sat'], 6, 0.04, 0.62, 0.3), spec=m['spec'])
    elif mat_id in ('cam', 'donmus', 'yildiz'):
        blade = Mat(ramp(m['hue'], m['sat'], 6, 0.30, 1.0, 0.25), spec=m['spec'], emissive=m['glow'])
    elif mat_id == 'gumus':
        blade = Mat(ramp(m['hue'], m['sat'], 6, 0.18, 1.0, 0.2), spec=m['spec'])
    elif mat_id == 'kemik':
        blade = Mat(ramp(m['hue'], m['sat'], 6, 0.25, 0.95, 0.2), spec=m['spec'])
    else:
        blade = Mat(ramp(m['hue'], m['sat'], 6, 0.12, 0.95, 0.3), spec=m['spec'])
    accent = {'pas': M['iron'], 'pirinc': M['iron'], 'gumus': M['gold'], 'cam': M['brass'], 'obsidyen': M['gold'],
              'kemik': M['leather'], 'kumtasi': M['brass'], 'yildiz': M['gold'], 'donmus': M['brass']}[mat_id]
    glow = {'cam': M['crystal'], 'donmus': M['crystal'], 'yildiz': M['magic'], 'obsidyen': M['magic']}.get(mat_id, M['ember'])
    return {'blade': blade, 'accent': accent, 'grip': M['leather'], 'wood': M['wood'], 'glow': glow, 'bone': M['bone'], 'iron': M['iron'], 'sand': M['sandglow']}


def _ring(c, cx, cy, r, mat, z, n=10, dot=0.8):
    for i in range(n):
        a = i / n * math.tau
        c.ellipse((cx + math.cos(a) * r, cy + math.sin(a) * r), dot, dot, mat, z=z)


def _arc(c, pts, r, mat, z):
    for a, b in zip(pts, pts[1:]):
        c.capsule(a, b, r, r, mat, z=z)


def draw_weapon(c, arch, mm, v=0.0):
    """v: 0..1 arası biçim çeşitlemesi (aynı tipin farklı düşüşleri hafifçe farklı görünür)."""
    B, A, G, W = mm['blade'], mm['accent'], mm['grip'], mm['wood']
    L = 1 + (v - 0.5) * 0.16
    if arch == 'akrep_kilici':
        c.capsule((-6, 0), (0, 0), 1.4, 1.4, G); c.ellipse((-7.2, 0), 1.9, 1.9, A, z=1)
        c.capsule((1, -4.6), (1, 4.6), 1.3, 1.3, A, z=2); c.ellipse((1, 0), 1.3, 1.3, mm['glow'], z=4)
        e = 20 * L
        c.poly([(2, -1.7), (e, -1.4), (e + 1, -3.8), (e + 9, 0), (e + 1, 3.8), (e, 1.4), (2, 1.7)], B, z=1, bevel=1.7, height=2)
        _ring(c, 7, 0, 2.9, B, 4, 12, 0.85); c.ellipse((7, 0), 1.5, 1.5, M['void'], z=5)
    elif arch == 'sarkac_baltasi':
        c.capsule((-9, 0), (24 * L, 0), 1.3, 1.3, W); _ring(c, -10.5, 0, 1.6, A, 2, 8, 0.6)
        for x in (1, 18 * L): c.capsule((x, -1.6), (x, 1.6), 1.0, 1.0, A, z=2)
        c.ellipse((26 * L, -1.5), 6.8, 6.8, B, z=1)
        c.ellipse((26 * L, -1.5), 3.0, 3.0, A, z=6); c.ellipse((26 * L, -1.5), 1.2, 1.2, mm['glow'], z=9)
    elif arch == 'yanki_hancerleri':
        for off, z0 in (((3, 4.5), -6), ((0, 0), 0)):
            ox, oy = off
            c.capsule((-4 + ox, oy), (0 + ox, oy), 1.3, 1.3, G, z=z0)
            c.capsule((0.6 + ox, -3 + oy), (0.6 + ox, 3 + oy), 1.0, 1.0, A, z=z0 + 1)
            c.poly([(1 + ox, -1.5 + oy), (10 * L + ox, -1.9 + oy), (16 * L + ox, 0.3 + oy), (10 * L + ox, 1.1 + oy), (1 + ox, 1.3 + oy)], B, z=z0 + 1, bevel=1.3, height=1.5)
    elif arch == 'geri_sarma_mizragi':
        e = 30 * L
        c.capsule((-11, 0), (e, 0), 1.2, 1.2, W)
        for x in (3, 8, 13): c.ellipse((x, 0), 1.6, 1.6, A, z=2)
        _ring(c, e, 0, 2.6, A, 3, 8, 1.0); c.ellipse((e, 0), 1.4, 1.4, A, z=4)
        c.poly([(e + 1, -2.7), (e + 8, -1.5), (e + 14, 0), (e + 8, 1.5), (e + 1, 2.7), (e + 3, 0)], B, z=2, bevel=1.5, height=2)
    elif arch == 'zemberek_cekici':
        c.capsule((-9, 0), (16, 0), 1.5, 1.5, W)
        c.poly([(14, -6.5), (23, -6.5), (23, 6.5), (14, 6.5)], B, z=2, bevel=2.2, height=3)
        c.capsule((23, -5.5), (23, 5.5), 1.4, 1.4, A, z=4)
        for i in range(5): c.ellipse((15 + i * 1.6, -7.6 - (i % 2) * 0.8), 1.1, 1.1, A, z=5)
    elif arch == 'cam_tirpan':
        c.capsule((-11, 2), (22, -2), 1.2, 1.2, W); c.capsule((20, -3.5), (22, -1), 1.6, 1.6, A, z=3)
        c.poly([(21, -2.5), (17, -9), (9, -12.5 * L), (-1, -12 * L), (8, -9), (14, -5.5), (18, -1)], B, z=2, bevel=1.8, height=2)
    elif arch == 'kum_kamcisi':
        c.capsule((-5, 0), (3, 0), 1.6, 1.6, G); c.ellipse((-6, 0), 1.8, 1.8, A, z=2)
        pts = [(3, 0)]
        for i in range(26):
            a = i / 26 * math.tau * 2.2
            pts.append((5 + i * 0.6 + math.cos(a) * 3.5, math.sin(a) * 3.5))
        pts.append((24 * L, 2))
        _arc(c, pts, 0.9, B, 1)
        c.ellipse((24 * L, 2), 1.3, 1.3, mm['sand'], z=4)
    elif arch == 'pas_yumruklari':
        c.capsule((-5, -3.5), (-5, 3.5), 2.2, 2.2, G)
        c.ellipse((2, 0), 5.5, 4.6, B, z=2)
        for i, yy in enumerate((-3.2, -1.1, 1.1, 3.2)): c.ellipse((7, yy), 1.4, 1.1, A, z=6)
        c.capsule((-1, -4.5), (4, -4.5), 0.8, 0.8, A, z=5)
    elif arch == 'kadran_kalkani':
        c.ellipse((4, 0), 9.5, 9.5, B, z=1); c.ellipse((4, 0), 7.4, 7.4, mm['bone'], z=4)
        for i in range(12):
            a = i / 12 * math.tau
            c.ellipse((4 + math.cos(a) * 6, math.sin(a) * 6), 0.55, 0.55, mm['iron'], z=9)
        c.capsule((4, 0), (4, -5), 0.55, 0.55, mm['iron'], z=10); c.capsule((4, 0), (7.2, 1.2), 0.55, 0.55, mm['iron'], z=10)
        c.ellipse((4, 0), 1.2, 1.2, A, z=11)
    elif arch == 'tiktak_kilici':
        c.capsule((-5, 0), (0, 0), 1.2, 1.2, G); c.ellipse((-6, 0), 1.5, 1.5, A, z=2)
        c.ellipse((1, 0), 2.4, 4.0, A, z=3)
        c.poly([(2, -0.95), (30 * L, -0.55), (34 * L, 0), (30 * L, 0.55), (2, 0.95)], B, z=2, bevel=0.9, height=1)
        c.capsule((1, 3.5), (-1, 10), 0.5, 0.5, A, z=4); c.ellipse((-1, 10.5), 1.7, 1.7, mm['glow'], z=5)
    elif arch == 'pas_capasi':
        c.capsule((-6, 0), (21, 0), 1.9, 1.7, B, z=1); _ring(c, -8.5, 0, 2.2, mm['iron'], 2, 10, 0.75)
        c.capsule((2, -5.5), (2, 5.5), 1.3, 1.3, B, z=2)
        _arc(c, [(22, 0), (21.5, -4), (19, -7.5)], 1.5, B, 2); _arc(c, [(22, 0), (21.5, 4), (19, 7.5)], 1.5, B, 2)
        c.poly([(18, -9.5), (21.5, -6.5), (17, -6)], B, z=3, bevel=1, height=1); c.poly([(18, 9.5), (21.5, 6.5), (17, 6)], B, z=3, bevel=1, height=1)
    elif arch == 'ters_akis_glevi':
        c.capsule((-13, 0), (21, 0), 1.1, 1.1, W)
        c.poly([(20, -2.2), (27, -1.6), (33 * L, 0.6), (27, 2.0), (20, 2.2)], B, z=2, bevel=1.4, height=1.5)
        c.poly([(-12, -2.2), (-19, -1.6), (-25 * L, 0.6), (-19, 2.0), (-12, 2.2)], B, z=2, bevel=1.4, height=1.5)
        c.poly([(1, -4.5), (7, -4.5), (4, 0), (7, 4.5), (1, 4.5), (4, 0)], A, z=3, bevel=1, height=1)
        c.ellipse((4, 2.4), 1.4, 1.2, mm['sand'], z=6); c.ellipse((4, -2.6), 0.9, 0.9, mm['sand'], z=6)
    # ------------------------------------------------ uzak
    elif arch == 'zemberek_yayi':
        pts = [(5.5 - 7 * (t / 6) ** 2, 13 * t / 6) for t in range(-6, 7)]
        _arc(c, pts, 1.2, B, 1)
        c.capsule((-1.5, -12.5), (-1.5, 12.5), 0.35, 0.35, mm['bone'], z=0)
        for i in range(4): c.ellipse((5.5 - i * 0.2, -2.2 + i * 1.4), 1.3, 0.8, A, z=4)
    elif arch == 'kadran_diski':
        for i in range(12):
            a = i / 12 * math.tau
            c.ellipse((4 + math.cos(a) * 8.2, math.sin(a) * 8.2), 1.1, 1.1, B, z=0)
        c.ellipse((4, 0), 7.6, 7.6, B, z=1); c.ellipse((4, 0), 5.2, 5.2, mm['bone'], z=4)
        c.capsule((4, 0), (4, -4), 0.5, 0.5, mm['iron'], z=8); c.capsule((4, 0), (6.5, 1.5), 0.5, 0.5, mm['iron'], z=8)
        c.ellipse((4, 0), 1.1, 1.1, mm['glow'], z=9)
    elif arch == 'saniye_tufegi':
        c.poly([(-11, 1), (-2, -1.6), (-2, 3.2), (-11, 4.5)], W, z=0, bevel=1.4, height=1.5)
        c.capsule((-2, 0), (8, 0), 2.5, 2.5, A, z=1)
        c.ellipse((3.5, -1), 3.2, 3.6, B, z=4)
        for i in range(4): c.capsule((1.5 + i * 1.3, -3.6), (1.5 + i * 1.3, 1.6), 0.35, 0.35, mm['iron'], z=7)
        c.capsule((8, -0.6), (24 * L, -0.6), 1.15, 1.15, B, z=2); c.ellipse((24 * L, -0.6), 1.7, 1.7, A, z=3)
        c.poly([(-1, 2.5), (2, 2.5), (1, 7), (-2, 7)], W, z=0, bevel=1, height=1)
    elif arch == 'golge_asasi':
        c.capsule((-11, 0), (23, 0), 1.1, 1.1, W)
        c.ellipse((26, 0), 3.2, 5.2, A, z=2)
        c.poly([(25.5, -0.5), (32, -5.5), (31.5, 0.5)], B, z=4, bevel=1, height=1.5)
        c.ellipse((26, 0.8), 1.3, 1.3, mm['glow'], z=6)
    elif arch == 'kum_sapani':
        c.capsule((-7, 0), (2, 0), 1.5, 1.5, W)
        c.capsule((2, 0), (8, -5.5), 1.2, 1.1, W, z=1); c.capsule((2, 0), (8, 5.5), 1.2, 1.1, W, z=1)
        c.capsule((8, -5.5), (5, 0), 0.4, 0.4, mm['bone'], z=2); c.capsule((8, 5.5), (5, 0), 0.4, 0.4, mm['bone'], z=2)
        c.ellipse((4.5, 0), 2.0, 2.0, mm['grip'], z=3); c.ellipse((4.3, -0.4), 1.0, 1.0, mm['sand'], z=6)
        c.ellipse((8, -5.5), 1.2, 1.2, B, z=3); c.ellipse((8, 5.5), 1.2, 1.2, B, z=3)
    elif arch == 'seken_arbalet':
        c.capsule((-11, 0), (14, 0), 1.7, 1.5, W)
        c.capsule((10, 0), (7, -9.5), 1.2, 0.9, B, z=2); c.capsule((10, 0), (7, 9.5), 1.2, 0.9, B, z=2)
        c.capsule((6.5, -9.5), (1, 0), 0.35, 0.35, mm['bone'], z=3); c.capsule((6.5, 9.5), (1, 0), 0.35, 0.35, mm['bone'], z=3)
        c.capsule((0, -0.8), (19 * L, -0.8), 0.6, 0.6, A, z=4); c.poly([(19 * L, -2.2), (22 * L, -0.8), (19 * L, 0.6)], B, z=5, bevel=0.8, height=1)
    elif arch == 'yanki_tabancasi':
        c.poly([(-7, 7), (-3.5, 7), (-1, 0), (-4.5, 0)], W, z=0, bevel=1.2, height=1.5)
        c.capsule((-4, -0.5), (6, -0.5), 2.1, 2.1, A, z=1)
        c.poly([(6, -2), (14, -2.4), (17 * L, -5), (17 * L, 4), (14, 1.4), (6, 1)], B, z=2, bevel=1.5, height=2)
        for i in range(3): _ring(c, 19 * L + i * 2.2, -0.5, 2.5 + i, mm['glow'], -4, 6 + i * 2, 0.45)
    elif arch == 'cam_kiymiklari':
        for k, ang in enumerate((-0.45, 0.0, 0.45)):
            ca, sa = math.cos(ang), math.sin(ang)
            P = lambda x, y: (x * ca - y * sa, x * sa + y * ca)
            c.capsule(P(-3, 0), P(1, 0), 0.9, 0.9, G, z=k)
            c.poly([P(1.5, -1.3), P(10 * L, -1.0), P(14 * L, 0), P(10 * L, 1.0), P(1.5, 1.3)], B, z=k + 1, bevel=1.1, height=1.2)
    elif arch == 'firtina_borusu':
        c.capsule((-10, 0), (-6, 0), 1.1, 1.1, A, z=1)
        c.poly([(-6, -1.6), (13, -3), (20 * L, -7.5), (20 * L, 7.5), (13, 3), (-6, 1.6)], B, z=1, bevel=2, height=2.5)
        for x in (3, 12): c.capsule((x, -2.8), (x, 2.8), 0.9, 0.9, A, z=4)
        c.ellipse((20 * L, 0), 1.6, 7.0, M['void'], z=5)
    elif arch == 'kronometre':
        c.poly([(-3, 3), (1, 3), (-1, 10), (-5, 10)], W, z=0, bevel=1, height=1.5)
        c.ellipse((2, 0), 6.2, 6.2, A, z=1); c.ellipse((2, 0), 4.6, 4.6, mm['bone'], z=4)
        c.capsule((2, 0), (2, -3.5), 0.45, 0.45, mm['iron'], z=7); c.capsule((2, 0), (4.5, 1), 0.45, 0.45, mm['iron'], z=7)
        c.capsule((2, -6), (2, -8.8), 1.0, 1.0, A, z=2); c.ellipse((2, -9.4), 1.4, 0.9, A, z=3)
        c.capsule((8, 0), (19 * L, 0), 1.2, 1.2, B, z=2)
    elif arch == 'cam_ocagi_asasi':
        c.capsule((-11, 0), (20, 0), 1.1, 1.1, W)
        for dy in (-3.5, 3.5): c.capsule((20, dy * 0.4), (26, dy), 0.6, 0.6, A, z=4); c.capsule((26, dy), (29, 0), 0.6, 0.6, A, z=4)
        c.ellipse((24.8, 0), 3.3, 3.3, M['ember'], z=2)
    elif arch == 'bag_kancasi':
        c.capsule((-7, 0), (1, 0), 1.5, 1.5, G); c.ellipse((-8, 0), 1.6, 1.6, A, z=2)
        for i in range(9): c.ellipse((2.5 + i * 1.5, math.sin(i * 1.3) * 1.4), 0.9, 0.7, mm['iron'], z=1, rot=i)
        c.capsule((15, 0), (20, 0), 1.4, 1.4, B, z=2)
        _arc(c, [(20, 0), (22.5, -2.5), (22, -5.5), (19, -6.5)], 1.2, B, 3)
        _arc(c, [(20, 0), (22.5, 2.5), (22, 5.5), (19, 6.5)], 1.2, B, 3)


def render_weapon(arch, mat_id, v=0.5, size=(64, 32), pivot=(16, 16), **kw):
    c = Canvas(size[0], size[1], pivot[0], pivot[1])
    draw_weapon(c, arch, weapon_mats(mat_id), v)
    kw.setdefault('rim_amt', 0.35)
    return c, c.shade(light=(-0.4, -0.75, 0.55), **kw)
