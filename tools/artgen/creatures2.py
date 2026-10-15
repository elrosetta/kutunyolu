"""v9 yaratıkları: Bekçi (kalkanlı savaşçı; walker/shield/charger), Tosbağa (kabuğuna çekilen taş kaplumbağa),
Kara Börü Han (boss: dev bozgun tazısı). Hepsi yüz sağa, ayak merkezi (0,0)."""
import math
import numpy as np
from raster import Canvas, Mat, ramp
from materials import M
from rig import fk_leg, fk_arm, lerp2, chain
import creatures as C1

# ------------------------------------------------------------ BEKÇİ (kimlik: bekci)
BRONZE = Mat(ramp(36, 0.6, 0.62, spread=0.4), spec=0.7, name='tunç zırh')
BRONZE_D = Mat(ramp(30, 0.55, 0.38, spread=0.4), name='tunç gölge')
HIDE = Mat(ramp(20, 0.45, 0.42, spread=0.4), name='kurgan derisi')
CLOTH = Mat(ramp(350, 0.55, 0.45, spread=0.4), name='kızıl keçe')
SKULL = Mat(ramp(40, 0.18, 0.80, spread=0.4), name='kafatası')
RUNE = Mat(ramp(44, 0.9, 1.0, spread=0.2), emissive=0.9, outline='#5a3a04', name='kalkan runası')
GHOST_EYE = Mat(ramp(200, 0.5, 1.0, spread=0.2), emissive=1.0, outline='#0b3a52', name='ölü göz')


def draw_bekci(c, p):
    """Kurgan Bekçisi: kadim savaşçı iskeleti, tunç pullu zırh, keçe etek, büyük runalı yuvarlak kalkan (ön kol),
    arka elde topuz. shield: 0 yanda, 1 önde kaldırılmış (siper), 2 ileri uzatılmış (kalkan darbesi); lean öne eğilme."""
    bob, lean = p.get('bob', 0.0), p.get('lean', 0.0)
    shield = p.get('shield', 1.0)
    hip = (0.0, -24 + bob)
    neck = (hip[0] + math.sin(lean) * 16, hip[1] - math.cos(lean) * 16)
    head = (neck[0] + 1.5 + math.sin(lean) * 2, neck[1] - 7)
    # bacaklar
    for dx, a, zz in ((-2.5, p.get('lb', (0.2, 0.1)), -4), (2.5, p.get('lf', (-0.2, 0.1)), 6)):
        k, f = fk_leg((hip[0] + dx, hip[1]), a[0], a[1], 11, 11)
        mat = HIDE if zz > 0 else BRONZE_D
        c.capsule((hip[0] + dx, hip[1]), k, 3.6, 3.0, HIDE, z=zz)
        c.capsule(k, f, 3.0, 2.4, mat, z=zz)
        c.capsule((k[0], k[1] - 1), (k[0] + 1, k[1] + 3), 3.2, 2.6, BRONZE, z=zz + 0.5)  # dizlik
        c.capsule(f, (f[0] + 4.5, f[1] - 0.3), 2.4, 1.5, BRONZE_D, z=zz + 0.2)
    # etek
    c.poly([(hip[0] - 8, hip[1] - 2), (hip[0] + 8, hip[1] - 2), (hip[0] + 9, hip[1] + 9), (hip[0] - 9, hip[1] + 9)], CLOTH, z=1, bevel=2.2, height=1.8)
    # arka kol + topuz
    ab = p.get('ab', (0.5, 0.6))
    e, h = fk_arm((neck[0] - 3, neck[1] + 3), ab[0], ab[1], 10, 9)
    c.capsule((neck[0] - 3, neck[1] + 3), e, 3.2, 2.8, BRONZE_D, z=-6)
    c.capsule(e, h, 2.8, 2.4, HIDE, z=-6)
    ma = p.get('mace', 0.0)  # topuz açısı (0 aşağı sarkık)
    mx, my = h[0] + math.sin(ma) * 14, h[1] + math.cos(ma) * 14
    c.capsule(h, (mx, my), 1.4, 1.4, M['wood'], z=-5)
    c.ellipse((mx, my), 4.2, 4.2, BRONZE, z=-5)
    for k in range(6):
        a = k / 6 * math.tau
        c.dot((mx + math.cos(a) * 4.8, my + math.sin(a) * 4.8), BRONZE_D, z=-4.5)
    # gövde: pullu zırh
    scales = lambda lu, lv, px, py: (np.floor(py * 0.6 + (np.floor(px * 0.5) % 2) * 0.5) % 2 == 0)
    mid = lerp2(hip, neck, 0.5)
    c.ellipse((mid[0], mid[1] + 1), 8.0, 11.0, BRONZE, z=2, rot=lean, paint=[(scales, BRONZE_D)])
    c.capsule((hip[0] - 8, hip[1] - 2.5), (hip[0] + 8, hip[1] - 2.5), 2.0, 2.0, M['leather'], z=4)
    # omuzluk
    c.ellipse((neck[0] + 4, neck[1] + 3), 4.5, 3.2, BRONZE, z=9)
    # baş: kafatası + sivri tunç miğfer, kulaklıklar
    hx, hy = head
    c.ellipse((hx, hy), 5.6, 5.4, SKULL, z=10)
    c.ellipse((hx + 3.5, hy - 0.5), 1.8, 1.4, M['black'], z=12)
    c.dot((hx + 3.6, hy - 0.6), GHOST_EYE, z=30, size=2)
    c.poly([(hx + 1, hy + 2), (hx + 5.5, hy + 1.5), (hx + 5, hy + 4), (hx + 1, hy + 4)], SKULL, z=11, bevel=0.8, height=0.6)
    for i in range(3):
        c.dot((hx + 1.8 + i * 1.3, hy + 3.2), M['black'], z=13)
    c.poly([(hx - 6.5, hy - 2), (hx + 6.5, hy - 2), (hx + 5, hy - 6.5), (hx + 1.5, hy - 15), (hx - 2, hy - 6.5)], BRONZE, z=12, bevel=1.6, height=1.6)
    c.capsule((hx - 6.5, hy - 2), (hx + 6.5, hy - 2), 1.4, 1.4, BRONZE_D, z=12.5)
    c.poly([(hx - 6.5, hy - 1), (hx - 4, hy - 1), (hx - 4.5, hy + 5), (hx - 7, hy + 4)], BRONZE_D, z=11.5, bevel=0.8, height=0.8)
    c.capsule((hx + 1.5, hy - 15), (hx - 1, hy - 20), 0.9, 0.5, CLOTH, z=12)  # miğfer püskülü
    # ön kol + kalkan
    if shield >= 1.5:
        af = (1.55, -0.1)
    elif shield >= 0.5:
        af = (0.9, 1.1)
    else:
        af = (0.2, 0.6)
    af = p.get('af', af)
    e2, h2 = fk_arm((neck[0] + 3, neck[1] + 3), af[0], af[1], 10, 9)
    c.capsule((neck[0] + 3, neck[1] + 3), e2, 3.3, 2.8, BRONZE, z=14)
    c.capsule(e2, h2, 2.8, 2.4, HIDE, z=14)
    # kalkan: büyük yuvarlak, merkez tunç göbek, rune halkası
    sx = h2[0] + 2.0
    sy = h2[1]
    rx = 3.5 if shield < 0.5 else (11.0 if shield < 1.5 else 7.0)
    ry = 12.0
    c.ellipse((sx, sy), rx, ry, HIDE, z=16, depth=0.5)
    c.ellipse((sx, sy), rx * 0.82, ry * 0.82, BRONZE_D, z=17, depth=0.3)
    c.ellipse((sx, sy), rx * 0.3, ry * 0.3, BRONZE, z=18)
    if shield >= 0.5:
        for k in range(6):
            a = k / 6 * math.tau + 0.3
            c.dot((sx + math.cos(a) * rx * 0.6, sy + math.sin(a) * ry * 0.6), RUNE, z=30, size=2)
    return {'hand': h2, 'shield': (sx, sy), 'head': head}


def _bekci_walk(t):
    s = math.sin(t * math.tau)
    return dict(bob=-abs(s) * 1.4 + 0.6, lean=0.08, lb=(0.7 * s, 0.35 + 0.6 * max(0, -s)), lf=(-0.7 * s, 0.35 + 0.6 * max(0, s)),
                ab=(0.5 - 0.3 * s, 0.6), shield=1.0, mace=0.2 * s)


BEKCI_ANIMS = {
    'idle': (4, lambda t: dict(bob=0.5 * math.sin(t * math.tau), lean=0.03, shield=1.0, mace=0.1 * math.sin(t * math.tau))),
    'walk': (6, _bekci_walk),
    'guard': (1, lambda t: dict(bob=1.5, lean=0.18, lb=(0.5, 0.5), lf=(-0.5, 0.5), shield=1.0, af=(1.0, 1.2))),
    'windup': (2, lambda t: C1.keyed(t, [dict(bob=1.0, lean=-0.15, shield=0.0, af=(-0.3, 0.8), ab=(-1.2, 0.9), mace=-2.4),
                                         dict(bob=1.6, lean=-0.22, shield=0.0, af=(-0.4, 0.9), ab=(-1.6, 1.0), mace=-2.9)])),
    'strike': (2, lambda t: C1.keyed(t, [dict(bob=0.0, lean=0.35, shield=0.0, af=(0.5, 0.6), ab=(1.4, 0.2), mace=1.4, lf=(0.6, 0.5), lb=(-0.5, 0.3)),
                                         dict(bob=0.8, lean=0.4, shield=0.0, af=(0.5, 0.6), ab=(1.6, 0.1), mace=1.7, lf=(0.7, 0.5), lb=(-0.6, 0.3))])),
    'bash': (2, lambda t: C1.keyed(t, [dict(bob=0.5, lean=0.2, shield=2.0, lf=(0.5, 0.5), lb=(-0.5, 0.3)),
                                       dict(bob=0.0, lean=0.35, shield=2.0, lf=(0.7, 0.5), lb=(-0.6, 0.3))])),
    'charge': (4, lambda t: dict(bob=-abs(math.sin(t * math.tau)) * 2 + 0.5, lean=0.45, shield=2.0, lb=(1.0 * math.sin(t * math.tau), 0.5 + 0.7 * max(0, -math.sin(t * math.tau))),
                                 lf=(-1.0 * math.sin(t * math.tau), 0.5 + 0.7 * max(0, math.sin(t * math.tau))), ab=(-0.9, 0.8), mace=-1.5)),
    'stagger': (2, lambda t: C1.keyed(t, [dict(bob=2.0, lean=-0.3, shield=0.0, af=(0.6, -0.3), ab=(0.9, 0.3), mace=0.8),
                                          dict(bob=1.0, lean=-0.2, shield=0.0, af=(0.4, -0.2), ab=(0.7, 0.3), mace=0.6)])),
    'hurt': (1, lambda t: dict(bob=1.0, lean=-0.25, shield=1.0, af=(0.8, 1.0), ab=(0.9, 0.5))),
}


# ------------------------------------------------------------ TOSBAĞA (kimlik: tosbaga)
SHELL = Mat(ramp(150, 0.22, 0.42, spread=0.45), name='kabuk taşı')
SHELL_D = Mat(ramp(160, 0.3, 0.26, spread=0.4), name='kabuk gölgesi')
SHELL_HI = Mat(ramp(140, 0.18, 0.58, spread=0.4), name='kabuk sırtı')
TSKIN = Mat(ramp(88, 0.35, 0.5, spread=0.4), name='tosbağa derisi')
TSKIN_D = Mat(ramp(92, 0.4, 0.34, spread=0.4), name='tosbağa derisi gölge')
CRYST = Mat(ramp(172, 0.7, 0.95, spread=0.3), emissive=0.7, outline='#0b4a52', name='kabuk kristali')


def draw_tosbaga(c, p):
    """Taş Tosbağa: Şahmeran mağarasının zırhlı bekçisi. Yüksek kubbe kabuk (taş plakalar, sırtta kristaller),
    kısa güçlü bacaklar, kalın boyun, gagalı baş. hide: 0 dışarıda, 1 kabuğa çekilmiş; spin: kabuk dönüş açısı; jaw."""
    bob = p.get('bob', 0.0)
    hide = p.get('hide', 0.0)
    spin = p.get('spin', 0.0)
    jaw = p.get('jaw', 0.0)
    cx, cy = 0.0, -14 + bob
    # bacaklar (dışarıdaysa)
    if hide < 0.5:
        for dx, a, zz, front in ((-11, p.get('hb', (0.3, 0.2)), -6, False), (10, p.get('fb', (-0.2, 0.2)), -6, True), (-9, p.get('hf', (0.2, 0.2)), 8, False), (12, p.get('ff', (-0.3, 0.2)), 8, True)):
            k, f = fk_leg((cx + dx, cy + 4), a[0], a[1], 6, 6)
            mat = TSKIN if zz > 0 else TSKIN_D
            c.capsule((cx + dx, cy + 4), k, 3.6, 3.0, mat, z=zz)
            c.capsule(k, f, 3.0, 2.8, mat, z=zz)
            c.ellipse((f[0] + 1, f[1] - 0.5), 3.4, 1.8, mat, z=zz + 0.2)
            for i in range(3):
                c.dot((f[0] + 2.5 + i * 1.2, f[1] + 0.4), M['bone'], z=zz + 2)
        # kuyruk
        c.capsule((cx - 17, cy + 3), (cx - 24, cy + 6), 2.2, 0.8, TSKIN_D, z=-4)
    # alt plastron
    c.ellipse((cx, cy + 4), 19, 5, TSKIN_D, z=0, depth=0.6)
    # kabuk kubbesi: plakalar (spin ile desen kayar)
    plates = lambda lu, lv, px, py: (np.floor((px - cx + spin * 6) * 0.22 + np.floor((py - cy) * 0.28) * 0.5) % 2 == 0) & ((np.abs(np.sin((px - cx + spin * 6) * 0.7) * np.sin((py - cy) * 0.9))) > 0.25)
    c.ellipse((cx, cy - 2), 20, 13, SHELL, z=3, depth=0.9, paint=[(plates, SHELL_D)])
    c.ellipse((cx - 1, cy - 6), 13, 6, SHELL_HI, z=4, depth=0.5, paint=[(plates, SHELL)])
    # kenar halkası
    c.capsule((cx - 20, cy + 2), (cx + 20, cy + 2), 2.2, 2.2, SHELL_D, z=5)
    # sırt kristalleri
    for k, (ox, h) in enumerate(((-9, 6), (-3, 9), (4, 8), (10, 5))):
        sx = cx + ox + math.sin(spin * 2 + k) * 1.5
        sy = cy - 9 - (h * 0.3)
        c.poly([(sx - 2.2, sy + 3), (sx + 2.2, sy + 3), (sx + 0.6, sy - h), (sx - 1.0, sy - h + 1.5)], CRYST, z=6 + k * 0.1, bevel=1.2, height=1.5)
    # baş + boyun
    if hide < 0.5:
        hx, hy = cx + 27, cy + 2 + p.get('hy', 0.0)
        c.capsule((cx + 16, cy + 3), (hx - 3, hy), 4.8, 4.2, TSKIN, z=10)
        c.ellipse((hx, hy), 5.4, 4.6, TSKIN, z=11)
        c.poly([(hx + 2, hy + 0.5), (hx + 9.5, hy + 1.5), (hx + 2, hy + 3.5 + jaw * 2.5)], TSKIN_D, z=12, bevel=1.0, height=1.0)  # gaga
        c.poly([(hx + 2.5, hy - 1.5), (hx + 10, hy + 0.8), (hx + 2.5, hy + 1.5)], TSKIN, z=12.5, bevel=1.0, height=1.0)
        c.dot((hx + 2.5, hy - 1.8), M['black'], z=20, size=2)
        c.dot((hx + 3.0, hy - 2.0), CRYST, z=21)
        if jaw > 0.2:
            for i in range(2):
                c.dot((hx + 4 + i * 2.2, hy + 1.4 + jaw * 1.5), M['bone'], z=22)
    else:
        # kabuk ağzından bakan göz
        c.ellipse((cx + 19, cy + 2), 3.5, 2.2, M['black'], z=10)
        c.dot((cx + 20, cy + 1.5), CRYST, z=21, size=2)
    return {'mouth': (cx + 30, cy + 3)}


def _tos_walk(t):
    s = math.sin(t * math.tau)
    return dict(bob=-abs(s) * 0.8, hb=(0.5 * s + 0.2, 0.2), fb=(-0.5 * s - 0.1, 0.2), hf=(-0.5 * s + 0.2, 0.2), ff=(0.5 * s - 0.1, 0.2), hy=0.5 * s, jaw=0.1)


TOSBAGA_ANIMS = {
    'idle': (4, lambda t: dict(bob=0.4 * math.sin(t * math.tau), hy=0.6 * math.sin(t * math.tau), jaw=0.05)),
    'walk': (6, _tos_walk),
    'shell': (2, lambda t: dict(hide=1.0, bob=1.5 - 0.5 * t)),
    'spin': (4, lambda t: dict(hide=1.0, bob=-1.0, spin=t * math.tau)),
    'windup': (2, lambda t: dict(bob=1.0, hy=-3.0 - 2.0 * t, jaw=0.6 + 0.3 * t)),
    'bite': (2, lambda t: dict(bob=-0.5, hy=2.0, jaw=0.0 if t > 0.5 else 1.0, fb=(-0.5, 0.2), ff=(-0.6, 0.2))),
    'hurt': (1, lambda t: dict(bob=1.0, hy=-1.0, jaw=0.4)),
}


# ------------------------------------------------------------ KARA BÖRÜ HAN (boss)
KBH = Mat(ramp(272, 0.32, 0.16, spread=0.45), name='han postu')
KBH_D = Mat(ramp(276, 0.4, 0.10, spread=0.4), name='han sırtı')
KBH_RIB = Mat(ramp(262, 0.2, 0.3, spread=0.4), name='han kaburga')
KBH_SMOKE = Mat(ramp(300, 0.3, 0.3, spread=0.35), name='kara yele')
KBH_EMBER = Mat(ramp(350, 0.95, 1.0, spread=0.2), emissive=1.0, outline='#3a0210', name='kan kor')
CORRUPT = M['corrupt']
from volume import soft as _soft
_soft(KBH, 0.85, 0.6, 1.0); _soft(KBH_D, 0.85, 0.6, 1.0); _soft(KBH_SMOKE, 0.6, 0.5, 0.7)


def draw_kara_boru_han(c, p):
    """Kara Börü Han: Erlik Tazısı'nın 2.3 katı; kara post, kan rengi kor gözler, sırtından fışkıran bozgun kristalleri,
    omuzlarda kemik zırh plakaları, boynunda kırık dev zincir, tacı (kafatası tacı)."""
    S = C1.Sq(c, 2.3, 2.3, 0.0, zk=2.3)
    old = (C1.HOUND, C1.HOUND_D, C1.HOUND_RIB, C1.SMOKE, C1.EMBER, C1.EMBER_D)
    C1.HOUND, C1.HOUND_D, C1.HOUND_RIB, C1.SMOKE, C1.EMBER, C1.EMBER_D = KBH, KBH_D, KBH_RIB, KBH_SMOKE, KBH_EMBER, KBH_EMBER
    try:
        info = C1.draw_hound(S, p)
    finally:
        C1.HOUND, C1.HOUND_D, C1.HOUND_RIB, C1.SMOKE, C1.EMBER, C1.EMBER_D = old
    # bozgun kristalleri: sırt boyunca büyük, ph ile titreşir; rage > 0 iken daha uzun
    rage = p.get('rage', 0.0)
    bob, tilt = p.get('bob', 0.0), p.get('tilt', 0.0)
    sq = p.get('sq', 0.0)   # tazı koşusundaki ezilme/uzama (draw_hound ile aynı)
    sqx, sqy = 1.0 + 0.06 * sq, 1.0 - 0.07 * sq
    hipp = (-10.0 * 2.3 * sqx, (-19.0 + bob - tilt * 6) * 2.3 * sqy)
    shp = (8.5 * 2.3 * sqx, (-20.5 + bob + tilt * 6) * 2.3 * sqy)
    for k, (t, h) in enumerate(((0.05, 14), (0.25, 22), (0.45, 26), (0.65, 20), (0.85, 15))):
        bx, by = lerp2(hipp, shp, t)
        by -= 15 + 4 * t
        hh = h * (1 + 0.5 * rage) + math.sin(p.get('ph', 0.0) + k) * 1.5
        c.poly([(bx - 5, by + 4), (bx + 5, by + 4), (bx + 1.5, by - hh), (bx - 2.5, by - hh + 4)], CORRUPT, z=40 + k, bevel=2.0, height=2.5)
    # omuz kemik plakası + kafatası tacı
    # omuz kemik plakası: kavisli (elips) — düz yapıştırma gibi değil, omzun üstünü saran bir kabuk
    c.ellipse((shp[0] + 1, shp[1] - 13), 13.5, 7.5, C1.BONE_D, z=42, rot=-0.18, depth=0.45)
    c.ellipse((shp[0] + 3, shp[1] - 15), 9.0, 3.6, M['bone'], z=44.5, rot=-0.18, depth=0.4)
    for k in range(3):
        c.ellipse((shp[0] - 8 + k * 8, shp[1] - 9 - k * 1.5), 1.2, 1.2, M['iron'], z=47)
    head = (shp[0] + 9.5 * 2.3 * sqx, shp[1] - (5.5 - p.get('hy', 0.0)) * 2.3 * sqy)
    for k in range(3):
        ox = head[0] - 10 + k * 7
        c.poly([(ox - 2, head[1] - 10), (ox + 2, head[1] - 10), (ox, head[1] - 20 - (3 if k == 1 else 0))], M['bone'], z=44, bevel=1.0, height=1.2)
    return {'mouth': (info['mouth'][0] * 2.3, info['mouth'][1] * 2.3), 'head': head}


KBH_ANIMS = {
    'idle': C1.HOUND_ANIMS['idle'],
    'run': C1.HOUND_ANIMS['run'],
    'windup': C1.HOUND_ANIMS['windup'],
    'leap': C1.HOUND_ANIMS['leap'],
    'hurt': C1.HOUND_ANIMS['hurt'],
    'howl': (3, lambda t: C1.keyed(t, [dict(bob=0.5, tilt=-0.25, hb=(0.4, 1.0), hf=(0.3, 0.9), fb=(0.2, 0.3), ff=(0.3, 0.3), tw=0.6, hy=-5.0, jaw=0.6, mane=-0.5, ph=0.0, rage=0.4),
                                       dict(bob=0.0, tilt=-0.3, hb=(0.4, 1.0), hf=(0.3, 0.9), fb=(0.2, 0.3), ff=(0.3, 0.3), tw=0.7, hy=-7.0, jaw=1.0, mane=-0.7, ph=1.5, rage=1.0),
                                       dict(bob=0.3, tilt=-0.28, hb=(0.4, 1.0), hf=(0.3, 0.9), fb=(0.2, 0.3), ff=(0.3, 0.3), tw=0.65, hy=-6.0, jaw=0.8, mane=-0.6, ph=3.0, rage=0.8)])),
    'slam': (2, lambda t: C1.keyed(t, [dict(bob=-3.0, tilt=0.25, hb=(-0.3, 0.8), hf=(-0.2, 0.7), fb=(1.3, 0.1), ff=(1.4, 0.1), tw=-0.4, hy=3.0, jaw=1.0, mane=0.4, rage=1.0),
                                       dict(bob=3.5, tilt=0.1, hb=(0.5, 1.3), hf=(0.4, 1.2), fb=(0.5, 1.0), ff=(0.6, 1.1), tw=0.5, hy=3.5, jaw=0.6, mane=0.2, rage=0.6)])),
    'rage': (2, lambda t: C1.keyed(t, [dict(bob=1.5, tilt=-0.1, hb=(0.5, 1.4), hf=(0.4, 1.3), fb=(0.3, 0.9), ff=(0.4, 1.0), tw=0.5, hy=1.0, jaw=1.0, mane=-0.3, ph=0.5, rage=1.0),
                                       dict(bob=2.5, tilt=-0.15, hb=(0.6, 1.5), hf=(0.5, 1.4), fb=(0.4, 1.0), ff=(0.5, 1.1), tw=0.6, hy=1.5, jaw=1.0, mane=-0.4, ph=2.0, rage=1.0)])),
}

CREATURES2 = {
    'bekci': (draw_bekci, BEKCI_ANIMS, (80, 96), (40, 92)),
    'tosbaga': (draw_tosbaga, TOSBAGA_ANIMS, (96, 64), (46, 60)),
    'kara_boru_han': (draw_kara_boru_han, KBH_ANIMS, (200, 144), (92, 138)),
}
