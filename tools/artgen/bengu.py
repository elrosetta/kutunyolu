"""Kahraman: BENGÜ — kurt başlı alp (insansı gövde, kurt kafası).

Okunaklılık için sade siluet: büyük kurt başı (kulaklar, uzun burun, kut ışığı göz), kısa kırmızı kaftan,
deri kemer, koyu şalvar, çizme ve arkada dalgalanan tek bir turkuaz atkı. Ayrıntı azaltıldı;
renk blokları büyük ve net (Dead Cells'in "uzaktan da okunan" karakter ilkesi).

Ön kol iki biçimde kullanılır:
  * hareket animasyonlarında (idle, koşu, zıplama...) sprite'a çizilir;
  * silah gösteren animasyonlarda (saldırı, yay, fırlatma, kalkan) ÇİZİLMEZ: oyun kolu üç parça
    (üst kol, ön kol, yumruk) olarak omuz çapasından 60 FPS sürer; silah her zaman yumruğun içindedir.
Koordinatlar: ayak merkezi (0,0), y aşağı pozitif, yüz sağa. Kol açıları: 0 aşağı, pi/2 ileri, pi yukarı.
"""
import math
import numpy as np
from raster import Canvas, Mat, ramp
from materials import M
from rig import fk_leg, fk_arm, lerp2, chain, Xf

BOOT = Mat(ramp(24, 0.45, 0.30, spread=0.4), name='koyu çizme')
TUNIC = M['kaftan']
TUNIC_IN = M['kaftan_in']
PANTS = M['indigo']
SCARF = M['turq']
FUR = M['fur']
FUR_D = M['fur_dark']


def draw_bengu(c, p, front_arm=True, back_arm=True):
    bob, lean = p['bob'], p['lean']
    sk, pk, bp = p.get('sk', 0.0), p.get('pk', 0.0), p.get('bp', 0.0)
    hip = (p.get('hx', 0.0), -20 + bob)
    neck = (hip[0] + math.sin(lean) * 14, hip[1] - math.cos(lean) * 14)
    sx = p.get('sx', 0.0)
    sh_f = (neck[0] + 1.5 + sx, neck[1] + 2.4)
    sh_b = (neck[0] - 2.2 - sx * 0.5, neck[1] + 2.2)
    head = (neck[0] + 1.8 + math.sin(lean) * 1.5 + p.get('hdx', 0.0), neck[1] - 6.2 + p.get('hdy', 0.0))
    out = {'sh_f': sh_f}
    # ------------------------------------------------ atkı (arkada dalgalanır)
    sc = chain((neck[0] - 2.0, neck[1] + 0.5), 6, 3.4, math.pi * 0.86 + pk * 0.3, -0.05, bp * 6.28, 0.35, sway=pk * 0.5)
    for i, (a, b) in enumerate(zip(sc, sc[1:])):
        r = 2.6 - i * 0.22
        c.capsule(a, b, r, r - 0.2, SCARF, z=8.5 - i * 0.3 if i < 2 else -14 + i * 0.1)
    c.ellipse(sc[-1], 1.4, 1.9, M['red_paint'], z=-13)
    # ------------------------------------------------ arka kol
    e, h = fk_arm(sh_b, p['ab'][0], p['ab'][1])
    if back_arm:
        c.capsule(sh_b, e, 2.6, 2.2, TUNIC_IN, z=-12)
        c.capsule(e, h, 2.2, 1.9, TUNIC_IN, z=-12)
        c.capsule(lerp2(e, h, 0.7), lerp2(e, h, 0.95), 2.3, 2.3, M['leather'], z=-11.5)
        c.ellipse(h, 2.0, 2.0, FUR_D, z=-11)
    out['hand_b'] = h
    out['ang_b'] = p['ab'][0] + p['ab'][1]
    out['sh_b'] = sh_b
    out['arm_b'] = (p['ab'][0], p['ab'][1])
    # ------------------------------------------------ arka bacak
    k, f = fk_leg(hip, p['lb'][0], p['lb'][1])
    c.capsule(hip, k, 3.4, 2.9, PANTS, z=-10)
    c.capsule(k, f, 2.9, 2.4, PANTS, z=-10)
    c.capsule(lerp2(k, f, 0.45), f, 2.9, 2.6, BOOT, z=-9.6)
    c.capsule(f, (f[0] + 4.0, f[1] - 0.3), 2.2, 1.4, BOOT, z=-9.5)
    # ------------------------------------------------ gövde ve etek
    mid = lerp2(hip, neck, 0.5)
    nx_, ny_ = neck
    collar = lambda lu, lv, px, py: (np.abs(py - (ny_ + 1.5)) < 0.8)
    c.ellipse((mid[0], mid[1] + 0.5), 6.6, 8.6, TUNIC, z=0, rot=lean, paint=[(collar, M['gold'])])
    bot = hip[1] + 9.5
    hem = lambda lu, lv, px, py: py > bot - 1.4
    c.poly([(hip[0] - 6.2, hip[1] - 1.5), (hip[0] + 6.4, hip[1] - 1.5), (hip[0] + 7.6 + sk * 1.6, bot), (hip[0] - 7.2 + sk * 2.4, bot - 0.5)],
           TUNIC, z=2, bevel=2.2, height=2, paint=[(hem, M['gold'])])
    c.capsule((hip[0] - 6.4, hip[1] - 2.2), (hip[0] + 6.6, hip[1] - 2.2), 1.9, 1.9, M['leather'], z=4)
    c.ellipse((hip[0] + 2.4, hip[1] - 2.2), 1.7, 1.6, M['gold'], z=5)
    # ------------------------------------------------ ön bacak
    k, f = fk_leg(hip, p['lf'][0], p['lf'][1])
    c.capsule((hip[0] + 1, hip[1]), k, 3.5, 3.0, PANTS, z=6)
    c.capsule(k, f, 3.0, 2.5, PANTS, z=6)
    c.capsule(lerp2(k, f, 0.45), f, 3.0, 2.7, BOOT, z=6.5)
    c.capsule(f, (f[0] + 4.2, f[1] - 0.3), 2.3, 1.4, BOOT, z=6.6)
    out['foot_f'] = f
    # ------------------------------------------------ kurt başı
    hx_, hy_ = head
    strand = lambda lu, lv, px, py: (np.floor(px * 0.6 + py * 1.1) % 3 == 0) & (lv > 0.0)
    c.ellipse((nx_ - 0.5, ny_ - 0.8), 5.4, 3.8, FUR, z=9, rot=lean * 0.6, paint=[(strand, FUR_D)])
    top_dark = lambda lu, lv, px, py: lv < -0.45
    c.ellipse((hx_ - 0.6, hy_), 5.4, 5.0, FUR, z=10, paint=[(top_dark, FUR_D)])
    jaw = p.get('jaw', 0.0)
    under = lambda lu, lv, px, py: lv > 0.45
    c.capsule((hx_ + 2.0, hy_ + 1.0), (hx_ + 10.0, hy_ + 2.2), 2.8, 1.8, FUR, z=11, paint=[(under, FUR_D)])
    c.capsule((hx_ + 2.2, hy_ + 3.6), (hx_ + 8.6, hy_ + 4.0 + jaw * 2.5), 1.5, 1.0, FUR_D, z=10.5)
    c.ellipse((hx_ + 10.4, hy_ + 1.5), 1.3, 1.1, M['black'], z=13)
    if jaw > 0.3:
        for tx in (4.5, 6.5):
            c.dot((hx_ + tx, hy_ + 3.3), M['bone'], z=14)
    # kulaklar
    c.poly([(hx_ - 4.2, hy_ - 3.0), (hx_ - 1.2, hy_ - 4.6), (hx_ - 3.6, hy_ - 11.0)], FUR, z=9.6, bevel=1.2, height=1.4)
    c.poly([(hx_ - 0.6, hy_ - 4.6), (hx_ + 2.4, hy_ - 4.0), (hx_ + 0.8, hy_ - 11.4)], FUR, z=12, bevel=1.2, height=1.4)
    c.poly([(hx_ + 0.1, hy_ - 5.0), (hx_ + 1.5, hy_ - 4.8), (hx_ + 0.8, hy_ - 9.2)], FUR_D, z=12.3, bevel=0.6, height=0.5)
    # göz (kut ışığı), kaş, savaş boyası
    c.capsule((hx_ + 1.2, hy_ - 2.0), (hx_ + 4.2, hy_ - 1.4), 0.55, 0.5, FUR_D, z=14)
    c.dot((hx_ + 2.8, hy_ - 0.6), M['kut'], z=30, size=2)
    c.capsule((hx_ + 0.2, hy_ + 0.9), (hx_ + 2.2, hy_ + 2.8), 0.5, 0.5, M['red_paint'], z=14)
    out['head'] = head
    # atkı düğümü (önde)
    c.ellipse((nx_ + 2.0, ny_ + 1.0), 2.0, 1.6, SCARF, z=15)
    # ------------------------------------------------ ön kol (yalnızca hareket animasyonlarında)
    a1, a2 = p['af']
    e, h = fk_arm(sh_f, a1, a2, 8.5, 8.0 * p.get('ext', 1.0))
    if front_arm:
        c.capsule(sh_f, e, 2.8, 2.4, TUNIC, z=17)
        c.capsule(e, h, 2.4, 2.0, TUNIC, z=17)
        c.capsule(lerp2(e, h, 0.68), lerp2(e, h, 0.95), 2.5, 2.5, M['leather'], z=18)
        c.ellipse(h, 2.1, 2.1, FUR_D, z=19)
    out['hand_f'] = h
    out['ang_f'] = a1 + a2
    out['arm'] = (a1, a2)
    return out


# ------------------------------------------------------------ kol parçaları (oyunda sürülür)
ARM_CELL = (12, 16)
ARM_PIVOT = (6, 3)
UPPER_LEN = 8.5
FORE_LEN = 8.0


def render_arm_parts():
    """Üst kol, ön kol (bilezikli) ve yumruk: aşağıyı gösteren (0,0) pivotlu küçük sprite'lar.
    Normal map düz bırakılır (döndürülen parçalarda ışık tutarlı kalsın)."""
    parts = []
    c = Canvas(ARM_CELL[0], ARM_CELL[1], ARM_PIVOT[0], ARM_PIVOT[1])
    c.capsule((0, 0), (0, UPPER_LEN), 2.8, 2.4, TUNIC, z=0, paint=[(lambda lu, lv, px, py: np.abs(px + 0.6) < 0.35, TUNIC_IN)])
    parts.append(c)
    c = Canvas(ARM_CELL[0], ARM_CELL[1], ARM_PIVOT[0], ARM_PIVOT[1])
    c.capsule((0, 0), (0, FORE_LEN), 2.4, 2.0, TUNIC, z=0)
    c.capsule((0, FORE_LEN * 0.66), (0, FORE_LEN * 0.95), 2.5, 2.5, M['leather'], z=1)
    c.capsule((0, FORE_LEN * 0.7), (0, FORE_LEN * 0.72), 2.6, 2.6, M['gold'], z=2)
    parts.append(c)
    c = Canvas(ARM_CELL[0], ARM_CELL[1], ARM_PIVOT[0], ARM_PIVOT[1] + 2)
    c.ellipse((0, 0), 2.3, 2.3, FUR_D, z=0)
    c.capsule((-1.2, -0.6), (1.2, -0.6), 0.4, 0.4, M['black'], z=1)
    parts.append(c)
    # arka kol: astar rengi, biraz ince (gövdenin arkasında)
    c = Canvas(ARM_CELL[0], ARM_CELL[1], ARM_PIVOT[0], ARM_PIVOT[1])
    c.capsule((0, 0), (0, UPPER_LEN), 2.6, 2.2, TUNIC_IN, z=0)
    parts.append(c)
    c = Canvas(ARM_CELL[0], ARM_CELL[1], ARM_PIVOT[0], ARM_PIVOT[1])
    c.capsule((0, 0), (0, FORE_LEN), 2.2, 1.9, TUNIC_IN, z=0)
    c.capsule((0, FORE_LEN * 0.66), (0, FORE_LEN * 0.95), 2.3, 2.3, M['leather'], z=1)
    parts.append(c)
    c = Canvas(ARM_CELL[0], ARM_CELL[1], ARM_PIVOT[0], ARM_PIVOT[1] + 2)
    c.ellipse((0, 0), 2.1, 2.1, FUR_D, z=0)
    parts.append(c)
    return parts


# ------------------------------------------------------------ pozlar
def P(**kw):
    d = dict(bob=0.0, lean=0.05, lb=(0.15, 0.12), lf=(-0.12, 0.08), ab=(0.2, 0.45), af=(-0.1, 0.55), sk=0.0, pk=0.0, bp=0.0, hx=0.0, sx=0.0, ext=1.0)
    d.update(kw)
    return d


def _lerp_pose(a, b, t):
    out = {}
    for k, va in a.items():
        vb = b.get(k, va)
        if isinstance(va, tuple):
            out[k] = tuple(x + (y - x) * t for x, y in zip(va, vb))
        else:
            out[k] = va + (vb - va) * t
    return out


def keyed(*keys):
    """Anahtar kareler arasında smoothstep geçiş."""
    def fn(t):
        for (t0, p0), (t1, p1) in zip(keys, keys[1:]):
            if t <= t1:
                u = 0.0 if t1 == t0 else max(0.0, min(1.0, (t - t0) / (t1 - t0)))
                u = u * u * (3 - 2 * u)
                return _lerp_pose(p0, p1, u)
        return keys[-1][1]
    return fn


def _run(t):
    s = math.sin(t * 6.28)
    return P(bob=-abs(math.sin(t * 6.28)) * 2.4 + 1.2, lean=0.28, lb=(0.95 * s, 0.3 + 0.95 * max(0, -s) + 0.15),
             lf=(-0.95 * s, 0.3 + 0.95 * max(0, s) + 0.15), ab=(-0.95 * s, 1.1), af=(0.95 * s, 1.1), sk=-0.7, pk=-1.0, bp=t * 2)


def _idle(t):
    s = math.sin(t * 6.28)
    return P(bob=0.6 * s, lean=0.05 + 0.02 * s, af=(-0.12 + 0.05 * s, 0.55 + 0.08 * s), ab=(0.2 - 0.04 * s, 0.45 + 0.06 * s),
             sk=0.25 * s, pk=0.35 * s, bp=t, jaw=0.0)


# Saldırı gövdeleri (kolsuz): 8 kare. 0-1 hazırlık, 2-4 vuruş (3 = darbe), 5 aşma, 6-7 toparlanma.
# Kol ve silahın kendisi oyunda (Player.SWINGS) aynı zaman çizelgesiyle sürülür.
def _atk(*keys):
    return (8, keyed(*keys), False, False)


ANIMS = {
    # ad: (kare sayısı, poz fonksiyonu, döngü mü, ön kol çizilsin mi)
    'idle': (8, _idle, True, True),
    'run': (8, _run, True, True),
    'jump': (3, keyed((0.0, P(bob=-0.5, lean=0.05, lb=(0.5, 1.2), lf=(-0.2, 0.4), ab=(-0.6, 0.6), af=(1.0, 0.5), sk=-0.6, pk=-0.8)),
                      (1.0, P(bob=-1.5, lean=0.12, lb=(0.8, 1.5), lf=(-0.35, 0.55), ab=(-1.0, 0.7), af=(1.5, 0.45), sk=-0.9, pk=-1.1))), False, True),
    'fall': (3, keyed((0.0, P(bob=-0.5, lean=0.0, lb=(0.5, 0.6), lf=(-0.3, 0.6), ab=(1.3, 0.3), af=(1.6, 0.3), sk=0.5, pk=0.6)),
                      (1.0, P(bob=0.5, lean=-0.08, lb=(0.3, 0.3), lf=(-0.45, 0.8), ab=(1.9, 0.3), af=(2.2, 0.2), sk=1.0, pk=1.1))), False, True),
    'land': (2, keyed((0.0, P(bob=3.0, lean=0.18, lb=(-0.5, 0.9), lf=(0.55, 1.0), ab=(0.5, 0.7), af=(0.7, 0.7), sk=0.3, pk=0.4)),
                      (1.0, P(bob=1.2, lean=0.1, lb=(-0.2, 0.4), lf=(0.2, 0.4), ab=(0.3, 0.5), af=(0.2, 0.6)))), False, True),
    'roll': (8, lambda t: P(bob=8, lean=0.9, lb=(2.1, 2.9), lf=(1.9, 2.8), ab=(1.6, 2.0), af=(1.4, 2.2), sk=0.4, pk=-0.6, bp=t, roll=t), False, True),
    'hurt': (3, keyed((0.0, P(lean=-0.35, af=(-1.0, 0.7), ab=(-1.2, 0.5), bob=0.5, lf=(-0.3, 0.3), lb=(0.4, 0.2), sk=0.9, pk=1.1, jaw=0.8)),
                      (1.0, P(lean=-0.2, af=(-0.6, 0.6), ab=(-0.8, 0.5), bob=1.5, lf=(-0.1, 0.3), lb=(0.2, 0.2), sk=0.6, pk=0.8, jaw=0.3))), False, True),
    'drink': (2, lambda t: P(lean=-0.1, af=(2.6 + 0.2 * t, 1.6), ab=(0.3, 0.4)), False, True),
    # çömelme: dizler kırık, gövde alçak; silahlı sürümde kollar iskeletle sürülür
    'crouch': (2, lambda t: P(bob=9.0 + 0.4 * t, lean=0.22, lb=(0.9, 1.9), lf=(-0.7, 1.9), ab=(0.3, 0.6), af=(-0.2, 0.7), sk=0.5, pk=0.4, hdy=1.0), True, True),
    'crouch_atk': (1, lambda t: P(bob=9.0, lean=0.3, lb=(0.9, 1.9), lf=(-0.7, 1.9), ab=(0.5, 0.6), sx=-1.0, sk=0.4, pk=0.3, hdy=1.0), False, False),
    'sprint': (8, lambda t: P(bob=-abs(math.sin(t * 6.28)) * 3.0 + 1.0, lean=0.5, lb=(1.2 * math.sin(t * 6.28), 0.3 + 1.1 * max(0, -math.sin(t * 6.28)) + 0.2),
                              lf=(-1.2 * math.sin(t * 6.28), 0.3 + 1.1 * max(0, math.sin(t * 6.28)) + 0.2), ab=(-1.3 * math.sin(t * 6.28), 1.3), af=(1.3 * math.sin(t * 6.28), 1.3), sk=-1.1, pk=-1.4, bp=t * 2.5), True, True),
    # --- kolsuz gövdeler (silahlı)
    'atk_down': _atk((0.0, P(lean=-0.15, ab=(0.6, 0.5), lf=(0.3, 0.4), lb=(-0.3, 0.2), sx=-1.0, bob=0.5, sk=0.4, pk=0.3)),
                     (0.25, P(lean=-0.28, ab=(0.8, 0.5), lf=(0.3, 0.4), lb=(-0.3, 0.25), sx=-1.8, bob=1.2, sk=0.5, pk=0.4, hdy=-0.5)),
                     (0.4, P(lean=0.3, ab=(-0.6, 0.7), lf=(0.6, 0.6), lb=(-0.5, 0.2), sx=1.5, bob=0.2, sk=-0.5, hx=2.5, jaw=0.6)),
                     (0.55, P(lean=0.48, ab=(-1.0, 0.8), lf=(0.7, 0.65), lb=(-0.6, 0.2), sx=2.4, bob=1.4, sk=-0.75, hx=3.8, jaw=0.8)),
                     (1.0, P(lean=0.18, ab=(-0.2, 0.6), lf=(0.45, 0.45), lb=(-0.35, 0.2), sx=0.5, bob=0.3, sk=-0.2, hx=1.5))),
    'atk_up': _atk((0.0, P(lean=0.2, ab=(-0.3, 0.5), lf=(0.5, 0.6), lb=(-0.5, 0.3), sx=-1.0, bob=2.0, sk=-0.2)),
                   (0.25, P(lean=0.26, ab=(-0.4, 0.5), lf=(0.55, 0.75), lb=(-0.55, 0.4), sx=-1.5, bob=3.0, sk=-0.1)),
                   (0.4, P(lean=0.1, ab=(0.3, 0.6), lf=(0.45, 0.4), lb=(-0.45, 0.3), sx=1.2, bob=0.0, sk=-0.4, hx=1.5, jaw=0.6)),
                   (0.55, P(lean=-0.12, ab=(0.9, 0.6), lf=(0.6, 0.6), lb=(-0.3, 0.5), sx=2.0, bob=-2.0, sk=-0.6, pk=-0.4, hx=2.5, jaw=0.8, hdy=-0.6)),
                   (1.0, P(lean=0.0, ab=(0.3, 0.5), lf=(0.4, 0.4), lb=(-0.3, 0.3), sx=0.4, bob=-0.5, sk=-0.2, hx=1.8))),
    'atk_horiz': _atk((0.0, P(lean=0.1, ab=(0.9, 0.4), lf=(0.4, 0.45), lb=(-0.4, 0.2), sx=-2.0, bob=0.8, sk=0.2)),
                      (0.25, P(lean=0.04, ab=(1.2, 0.4), lf=(0.4, 0.5), lb=(-0.45, 0.25), sx=-3.0, bob=1.2, sk=0.4, pk=0.3)),
                      (0.4, P(lean=0.3, ab=(-0.2, 0.6), lf=(0.65, 0.6), lb=(-0.55, 0.2), sx=1.0, bob=0.5, sk=-0.4, hx=2.0, jaw=0.6)),
                      (0.55, P(lean=0.36, ab=(-1.1, 0.7), lf=(0.7, 0.6), lb=(-0.6, 0.2), sx=3.0, bob=0.8, sk=-0.7, pk=-0.5, hx=3.4, jaw=0.8)),
                      (1.0, P(lean=0.15, ab=(-0.3, 0.5), lf=(0.45, 0.45), lb=(-0.4, 0.2), sx=0.8, bob=0.4, sk=-0.2, hx=1.8))),
    'atk_thrust': _atk((0.0, P(lean=-0.12, ab=(0.4, 0.6), lf=(0.2, 0.3), lb=(-0.2, 0.2), sx=-2.0, sk=0.2, hx=-1.0)),
                       (0.25, P(lean=-0.18, ab=(0.5, 0.6), lf=(0.15, 0.3), lb=(-0.2, 0.25), sx=-2.6, sk=0.3, hx=-1.5, bob=0.8)),
                       (0.4, P(lean=0.3, ab=(-0.6, 0.6), lf=(0.75, 0.6), lb=(-0.65, 0.2), sx=2.0, sk=-0.6, hx=3.0, jaw=0.6)),
                       (0.55, P(lean=0.42, ab=(-0.9, 0.6), lf=(0.9, 0.6), lb=(-0.75, 0.2), sx=3.2, sk=-0.8, hx=4.6, jaw=0.8)),
                       (1.0, P(lean=0.15, ab=(-0.1, 0.6), lf=(0.4, 0.4), lb=(-0.35, 0.2), sx=0.5, sk=-0.2, hx=2.0))),
    'atk_heavy': _atk((0.0, P(lean=-0.2, ab=(-2.4, 1.2), lf=(0.3, 0.4), lb=(-0.3, 0.3), sx=-1.0, bob=1.5, sk=0.5, pk=0.4)),
                      (0.25, P(lean=-0.32, ab=(-2.9, 1.4), lf=(0.35, 0.45), lb=(-0.35, 0.3), sx=-1.5, bob=2.6, sk=0.6, pk=0.5, hdy=-0.8)),
                      (0.4, P(lean=0.2, ab=(-1.4, 0.6), lf=(0.6, 0.7), lb=(-0.5, 0.35), sx=1.0, bob=-2.0, sk=-0.2, hx=2.0, jaw=0.7)),
                      (0.55, P(lean=0.62, ab=(1.0, 0.2), lf=(0.9, 1.0), lb=(-0.7, 0.3), sx=2.5, bob=3.2, sk=-0.75, hx=4.2, jaw=1.0)),
                      (1.0, P(lean=0.3, ab=(0.5, 0.5), lf=(0.5, 0.6), lb=(-0.4, 0.3), sx=0.5, bob=0.8, sk=-0.2, hx=2.0))),
    'atk_spin': _atk((0.0, P(lean=0.1, ab=(-0.6, 0.6), lf=(0.4, 0.5), lb=(-0.4, 0.2), sx=-1.0, bob=0.5)),
                     (0.25, P(lean=-0.1, ab=(-0.8, 0.6), lf=(0.35, 0.5), lb=(-0.4, 0.25), sx=-1.5, bob=1.2, sk=0.3)),
                     (0.4, P(lean=0.1, ab=(0.2, 0.4), lf=(0.6, 0.6), lb=(-0.6, 0.3), sx=1.5, bob=-1.8, pk=-0.6, sk=-0.6, jaw=0.6)),
                     (0.55, P(lean=-0.12, ab=(0.9, 0.4), lf=(0.5, 0.6), lb=(-0.5, 0.3), sx=-1.0, bob=-2.2, pk=0.6, sk=0.4, jaw=0.8)),
                     (0.75, P(lean=0.08, ab=(0.2, 0.5), lf=(0.4, 0.45), lb=(-0.4, 0.2), sx=1.0, bob=0.8, pk=0.3, sk=0.2)),
                     (1.0, P(lean=0.05, ab=(0.1, 0.5), lf=(0.3, 0.4), lb=(-0.3, 0.2), sx=0.0, bob=0.3))),
    'atk_lunge': _atk((0.0, P(lean=-0.15, ab=(0.4, 0.6), lf=(0.2, 0.3), lb=(-0.3, 0.2), sx=-2.0, sk=0.3)),
                      (0.25, P(lean=-0.22, ab=(0.5, 0.6), lf=(0.15, 0.3), lb=(-0.3, 0.25), sx=-2.5, sk=0.4, hx=-1.0, bob=0.6)),
                      (0.4, P(lean=0.5, ab=(-0.8, 0.4), lf=(0.9, 0.5), lb=(-0.8, 0.2), sx=2.5, sk=-0.8, pk=-0.7, hx=4.0, bob=1.0, jaw=0.6)),
                      (0.55, P(lean=0.6, ab=(-1.0, 0.4), lf=(1.05, 0.5), lb=(-0.95, 0.2), sx=3.5, sk=-1.0, pk=-0.9, hx=5.5, bob=1.5, jaw=1.0)),
                      (1.0, P(lean=0.3, ab=(-0.3, 0.5), lf=(0.5, 0.5), lb=(-0.5, 0.2), sx=0.8, sk=-0.4, hx=3.0, bob=0.5))),
    'bow': (3, lambda t: [P(lean=0.0, ab=(1.4, -1.2), lf=(0.25, 0.3), lb=(-0.3, 0.2)),
                          P(lean=-0.05, ab=(1.45, -2.3), lf=(0.3, 0.3), lb=(-0.35, 0.2)),
                          P(lean=0.08, ab=(0.6, -0.4), lf=(0.3, 0.3), lb=(-0.35, 0.2))][min(2, int(t * 3))], False, False),
    'throw': (3, lambda t: [P(lean=-0.2, ab=(0.8, 0.5), lf=(0.4, 0.4), lb=(-0.3, 0.2), sx=-1.5),
                            P(lean=0.3, ab=(-0.5, 0.6), lf=(0.6, 0.6), lb=(-0.5, 0.2), sk=-0.4, sx=2.0),
                            P(lean=0.2, ab=(-0.2, 0.6), lf=(0.4, 0.4), lb=(-0.3, 0.2), sx=0.8)][min(2, int(t * 3))], False, False),
    'block': (1, lambda t: P(lean=0.12, ab=(1.25, 1.0), lf=(0.45, 0.5), lb=(-0.45, 0.3), bob=1.5, sx=1.0), False, False),
    'cast': (2, lambda t: [P(lean=-0.05, ab=(0.5, 1.2), sx=-0.5), P(lean=0.15, ab=(1.4, 0.3), lf=(0.3, 0.3), lb=(-0.3, 0.2), sx=1.5, jaw=0.7)][min(1, int(t * 2))], False, False),
}


def render_frame(anim, i, cell=(96, 80), feet=(44, 74)):
    n, fn, loop, arm = ANIMS[anim]
    t = (i / n) if loop else (min(0.999, i / n + 0.5 / n) if n > 1 else 0.0)
    p = fn(t)
    c = Canvas(cell[0], cell[1], feet[0], feet[1])
    if 'roll' in p:
        ang = p['roll'] * math.tau
        xf = Xf(c, 0, -16, ang, pivot=(0, -19))
        info = draw_bengu(xf, p, True)
    else:
        info = draw_bengu(c, p, arm, arm)
    rgba = c.shade()
    nm = c.normal_map(rgba[..., 3])
    return c, rgba, nm, info
