"""Şahmeran Ana v29: hamle başına tam gövde animasyonları (sahmeran_ink.draw pozlarıyla).

Yılan kraliçenin dili: dinlenmede büyüleyici sekiz çizen salınım (bel, baş ters yönde), kangalda nefes gibi yürüyen
dalga; sürünürken kangal dalgaları yerde ilerler, kuyruk dalgalanır. Sokma öncesi kobra gibi kangalı sıkıştırıp geriye
çekilir (kuyruk ucu çıngırak gibi titrer), atılışta beden yatay bir mızrak olur; ıskalayınca başı yere saplanır ve
kurtulmak için çırpınır. Kuyruk süpürmesinde kuyruk S biçiminde kalkıp yere kamçılanır; mağara yıkımında kuyruk tavana
dikilir. "!!" taşlaştıran bakışta boyu uzar, yelpaze sonuna dek açılır, elleri yüzünü çerçeveler.

Evre bölümleri: w hazırlık, s temas, r toparlanma, d atılış, x atılış sonu, v saplanma (döngü), a eylem / döngü.
"""
import math

import bosskit as bk
from sahmeran_ink import _base as B

over = bk.over


def clip(frames, fps=10, loop=False, seg=None):
    return bk.clip(frames, fps, loop, seg)


def _idle(t):
    s, c = math.sin(t * math.tau), math.cos(t * math.tau)
    s2 = math.sin(t * math.tau * 2)
    fl = max(0.0, math.sin((t - 0.62) * math.tau * 3)) if 0.62 <= t < 0.95 else 0.0      # dil / tıslama seğirmesi
    return B(wx=10.0 + 3.2 * s, wy=-50.0 + 1.8 * s2, lean=0.08 + 0.06 * s, wv=t * math.tau, ht=-0.06 * s + 0.03 * s2, hood=0.5 + 0.1 * s2,
             arm=0.55 + 0.12 * math.sin(t * math.tau + 1.0), el=0.75 + 0.08 * c, arm_b=0.4 - 0.1 * s, el_b=0.8, claw=0.3 + 0.2 * fl,
             glow=0.6 + 0.3 * (0.5 + 0.5 * s2), hair=s, mouth=0.35 * fl, cw=1.2)


def _walk(t):
    s2, c2 = math.sin(t * math.tau * 2), math.cos(t * math.tau * 2)
    return B(wx=13.0 + 2.0 * s2, wy=-48.0 + 2.2 * c2, lean=0.2 + 0.04 * s2, wv=t * math.tau * 2, slide=1.0, cw=5.5, arm=0.7 + 0.12 * s2,
             el=0.8, arm_b=0.5 - 0.1 * s2, el_b=0.7, glow=0.7, hood=0.42 + 0.06 * c2, hair=0.6 + 0.5 * math.sin(t * math.tau * 2 + 1.0),
             ht=0.06 - 0.04 * s2)


SPIT = [
    B(wx=4, wy=-56, lean=-0.12, ht=-0.25, mouth=0.3, hood=0.9, arm=1.0, el=1.2, arm_b=0.9, el_b=1.3, claw=0.7, rise=0.5, coil=0.2, glow=0.9, wv=0.4),
    B(wx=1, wy=-60, lean=-0.22, ht=-0.36, mouth=0.6, hood=1.0, arm=1.05, el=1.35, arm_b=1.0, el_b=1.4, claw=0.9, rise=0.7, coil=0.3, glow=1.0,
      hair=-0.8, wv=0.8),
    B(wx=8, wy=-58, lean=0.05, ht=-0.12, mouth=0.9, hood=1.0, arm=1.2, el=0.9, arm_b=1.1, el_b=1.0, claw=1.0, rise=0.6, glow=1.0, hair=-0.3, wv=1.2),
    B(wx=22, wy=-52, lean=0.46, ht=0.22, mouth=1.0, hood=1.0, arm=1.45, el=0.2, arm_b=1.2, el_b=0.3, claw=1.0, glow=1.0, hair=1.2, tail=0.3, wv=1.8),
    B(wx=24, wy=-50, lean=0.5, ht=0.26, mouth=0.75, hood=0.9, arm=1.35, el=0.3, arm_b=1.1, el_b=0.4, claw=0.8, glow=0.9, hair=1.4, tail=0.2, wv=2.2),
    B(wx=16, wy=-50, lean=0.26, ht=0.1, mouth=0.3, hood=0.7, arm=0.9, el=0.6, arm_b=0.6, el_b=0.7, claw=0.5, glow=0.8, hair=0.8, wv=2.6),
    B(wx=11, wy=-50, lean=0.12, mouth=0.1, hood=0.55, wv=3.0, hair=0.4),
]

TAIL = [
    B(wx=14, wy=-48, lean=0.25, ht=0.05, arm=1.2, el=0.5, arm_b=1.4, el_b=0.4, hood=0.8, mouth=0.5, claw=0.8, tup=0.6, wv=0.0, glow=0.9),
    B(wx=16, wy=-47, lean=0.3, ht=0.08, arm=1.3, el=0.45, arm_b=1.5, el_b=0.35, hood=1.0, mouth=0.8, claw=1.0, tup=1.0, wv=1.6, glow=1.0, cw=1.0),
    B(wx=17, wy=-46, lean=0.36, ht=0.1, arm=1.35, el=0.4, arm_b=1.55, el_b=0.3, hood=1.0, mouth=0.9, claw=1.0, tup=1.0, wv=3.2, glow=1.0, cw=1.5),
    B(wx=26, wy=-40, lean=0.72, ht=0.32, arm=1.65, el=0.1, arm_b=1.2, el_b=0.2, hood=0.9, mouth=1.0, claw=1.0, tlash=1.0, cx=4, hair=1.5,
      wv=0.5, glow=1.0),
    B(wx=24, wy=-42, lean=0.62, ht=0.28, arm=1.5, el=0.2, arm_b=1.0, el_b=0.3, hood=0.85, mouth=0.8, claw=0.9, tlash=0.9, cx=3, hair=1.4, wv=1.0),
    B(wx=22, wy=-44, lean=0.5, ht=0.2, arm=1.2, el=0.35, arm_b=0.8, el_b=0.45, hood=0.8, mouth=0.6, claw=0.7, tlash=0.7, cx=2, hair=1.1, wv=1.6),
    B(wx=16, wy=-48, lean=0.3, ht=0.1, arm=0.8, el=0.6, arm_b=0.5, el_b=0.7, hood=0.65, mouth=0.3, tlash=0.3, hair=0.6, wv=2.2),
    B(wx=11, wy=-50, lean=0.12, hood=0.55, wv=2.8),
]

LUNGE = [
    B(wx=2, wy=-44, lean=-0.05, ht=0.1, mouth=0.5, hood=1.0, arm=1.3, el=1.0, arm_b=1.2, el_b=1.1, claw=1.0, rise=0.3, glow=1.0, coil=0.5, cx=-4,
      tup=0.4, wv=1.0),
    B(wx=-6, wy=-40, lean=-0.15, ht=0.2, mouth=0.8, hood=1.0, arm=1.35, el=1.1, arm_b=1.25, el_b=1.2, claw=1.0, rise=0.2, glow=1.0, coil=0.9,
      cx=-8, hair=-1.0, tup=0.7, wv=2.5),
    B(wx=-8, wy=-38, lean=-0.2, ht=0.22, mouth=1.0, hood=1.0, arm=1.4, el=1.1, arm_b=1.3, el_b=1.2, claw=1.0, rise=0.2, glow=1.0, coil=1.0,
      cx=-10, hair=-1.2, tup=0.8, wv=4.0),
    # 3-4: atılış (beden yatay mızrak)
    B(wx=48, wy=-30, lean=1.2, ht=0.55, mouth=1.0, hood=0.9, arm=1.65, el=0.05, arm_b=1.6, el_b=0.1, claw=1.0, glow=1.0, coil=-0.5, cx=6,
      hair=2.0, tail=0.8, wv=0.5),
    B(wx=50, wy=-28, lean=1.25, ht=0.6, mouth=1.0, hood=0.85, arm=1.7, el=0.05, arm_b=1.62, el_b=0.08, claw=1.0, glow=1.0, coil=-0.5, cx=7,
      hair=2.2, tail=1.0, wv=1.5),
    B(wx=40, wy=-34, lean=0.9, ht=0.4, mouth=0.6, hood=0.6, arm=0.9, el=0.4, arm_b=0.8, el_b=0.5, claw=0.6, glow=0.9, coil=-0.3, cx=5, hair=1.4,
      wv=2.0),
    # 6-8: ıskaladı — başı yere saplandı, çırpınır
    B(wx=50, wy=-20, lean=1.55, ht=0.9, mouth=0.3, hood=0.3, arm=1.2, el=0.6, arm_b=1.0, el_b=0.5, claw=0.5, glow=0.45, coil=-0.3, cx=6,
      hair=2.2, tlash=0.4, wv=0.0),
    B(wx=49, wy=-21, lean=1.5, ht=0.85, mouth=0.5, hood=0.35, arm=1.0, el=0.8, arm_b=1.2, el_b=0.3, claw=0.7, glow=0.5, coil=-0.3, cx=6,
      hair=2.0, tail=0.5, tup=0.3, wv=1.5),
    B(wx=51, wy=-19, lean=1.58, ht=0.95, mouth=0.4, hood=0.3, arm=1.3, el=0.4, arm_b=0.9, el_b=0.7, claw=0.7, glow=0.5, coil=-0.3, cx=6,
      hair=2.3, tail=0.9, wv=3.0),
    B(wx=30, wy=-38, lean=0.6, ht=0.1, mouth=0.6, hood=0.7, arm=0.9, el=0.6, arm_b=0.8, el_b=0.7, claw=0.6, glow=0.8, cx=3, hair=1.0, wv=4.0),
]

SNAKES = [
    B(wx=8, wy=-60, lean=-0.1, ht=-0.25, arm=2.3, el=0.4, arm_b=2.5, el_b=0.3, hood=1.0, mouth=0.6, glow=1.0, rise=0.7, claw=1.0, hair=-1.0),
    B(wx=8, wy=-66, lean=-0.18, ht=-0.32, arm=2.6, el=0.25, arm_b=2.8, el_b=0.2, hood=1.0, mouth=0.8, glow=1.0, rise=0.9, claw=1.0, hair=-1.2, cw=1.5),
] + [B(wx=8 + 3 * math.sin(k / 4 * math.tau), wy=-64 + 2 * math.cos(k / 4 * math.tau), lean=-0.14 + 0.05 * math.sin(k / 4 * math.tau),
       ht=-0.3 + 0.1 * math.cos(k / 4 * math.tau), arm=2.4 + 0.3 * math.sin(k / 4 * math.tau), el=0.4 + 0.3 * math.cos(k / 4 * math.tau),
       arm_b=2.6 - 0.3 * math.sin(k / 4 * math.tau), el_b=0.4 - 0.25 * math.cos(k / 4 * math.tau), hood=1.0, mouth=0.85 + 0.15 * math.sin(k * 1.7),
       glow=1.0, rise=0.8, claw=1.0, hair=1.2 * math.sin(k / 4 * math.tau), cw=2.0, wv=k * 1.57) for k in range(4)]

DRIP = [
    B(wx=10, wy=-52, lean=0.05, ht=-0.3, arm=0.9, el=1.2, arm_b=0.8, el_b=1.2, mouth=0.3, hood=0.8, tceil=0.3, glow=0.9, wv=0.5),
    B(wx=10, wy=-54, lean=-0.08, ht=-0.45, arm=1.0, el=1.1, arm_b=0.9, el_b=1.1, mouth=0.5, hood=0.9, tceil=0.7, glow=1.0, wv=1.0),
    B(wx=9, wy=-55, lean=-0.12, ht=-0.5, arm=1.1, el=1.0, arm_b=1.0, el_b=1.0, mouth=0.7, hood=1.0, tceil=1.0, glow=1.0, wv=1.5),
    B(wx=12, wy=-50, lean=0.1, ht=-0.4, arm=1.8, el=0.3, arm_b=2.0, el_b=0.3, mouth=1.0, hood=1.0, tceil=1.0, glow=1.0, wv=2.6, claw=1.0, cw=2.0),
    B(wx=12, wy=-51, lean=0.08, ht=-0.38, arm=1.7, el=0.35, arm_b=1.9, el_b=0.35, mouth=0.8, hood=1.0, tceil=0.95, glow=1.0, wv=3.6, claw=0.9,
      cw=1.5),
    B(wx=11, wy=-51, lean=0.1, ht=-0.12, arm=1.0, el=0.7, arm_b=0.9, el_b=0.8, mouth=0.4, hood=0.7, tceil=0.5, wv=4.4),
    B(wx=10, wy=-50, lean=0.1, ht=0.0, mouth=0.15, hood=0.55, tceil=0.15, wv=5.0),
]

GAZE = [
    B(wx=8, wy=-62, lean=-0.05, ht=-0.05, hood=1.0, arm=1.9, el=1.9, arm_b=2.0, el_b=1.9, claw=0.8, glow=0.8, mouth=0.2, rise=0.8),
    B(wx=8, wy=-66, lean=-0.06, ht=-0.1, hood=1.0, arm=2.2, el=2.0, arm_b=2.3, el_b=2.0, claw=0.9, glow=1.0, mouth=0.25, rise=0.9, cw=1.0),
    B(wx=8, wy=-68, lean=-0.06, ht=-0.1, hood=1.0, arm=2.25, el=2.05, arm_b=2.35, el_b=2.05, claw=1.0, glow=1.0, mouth=0.4, rise=1.0, coil=0.3,
      cw=1.5, wv=1.0),
    B(wx=8, wy=-68.5, lean=-0.08, ht=-0.12, hood=1.0, arm=2.3, el=2.1, arm_b=2.4, el_b=2.1, claw=1.0, glow=1.0, mouth=0.5, rise=1.0, coil=0.35,
      hair=-1.2, cw=2.0, wv=2.0),
    B(wx=16, wy=-60, lean=0.35, ht=0.25, hood=1.0, arm=-0.5, el=0.2, arm_b=2.6, el_b=0.2, claw=1.0, glow=1.0, mouth=1.0, rise=0.6, hair=1.4),
    B(wx=17, wy=-59, lean=0.38, ht=0.27, hood=1.0, arm=-0.45, el=0.25, arm_b=2.55, el_b=0.25, claw=1.0, glow=1.0, mouth=0.9, rise=0.6, hair=1.5),
    B(wx=12, wy=-52, lean=0.15, ht=0.05, hood=0.7, arm=0.6, el=0.7, arm_b=0.6, el_b=0.8, glow=0.8, mouth=0.3),
]

VENOM = [
    B(wx=10, wy=-58, lean=-0.08, ht=-0.1, arm=2.4, el=0.6, arm_b=2.6, el_b=0.5, hood=0.9, mouth=0.5, claw=1.0, glow=1.0, rise=0.6),
    B(wx=10, wy=-61, lean=-0.12, ht=-0.15, arm=2.6, el=0.45, arm_b=2.8, el_b=0.4, hood=1.0, mouth=0.7, claw=1.0, glow=1.0, rise=0.7),
    B(wx=18, wy=-36, lean=0.72, ht=0.3, arm=1.0, el=0.1, arm_b=0.9, el_b=0.15, hood=1.0, mouth=1.0, claw=1.0, glow=1.0, cw=2.5, wv=1.0),
    B(wx=12, wy=-52, lean=0.2, ht=0.0, arm=1.9, el=0.5, arm_b=2.1, el_b=0.45, hood=0.9, mouth=0.6, claw=0.9, glow=1.0, cw=1.0, wv=2.0),
    B(wx=12, wy=-50, lean=0.18, arm=1.0, el=0.7, arm_b=0.9, el_b=0.8, hood=0.7, mouth=0.3, wv=2.6),
    B(wx=10, wy=-50, lean=0.1, hood=0.55, wv=3.0),
]

NOVA = [
    B(wx=6, wy=-42, lean=0.0, ht=0.1, hood=1.0, arm=0.9, el=1.6, arm_b=1.0, el_b=1.6, claw=1.0, mouth=0.8, glow=1.0, coil=0.8, cx=-4, tup=0.6, wv=1.0),
    B(wx=4, wy=-40, lean=-0.05, ht=0.12, hood=1.0, arm=0.85, el=1.7, arm_b=0.95, el_b=1.7, claw=1.0, mouth=1.0, glow=1.0, coil=1.0, cx=-5, tup=1.0,
      wv=2.6),
    B(wx=14, wy=-50, lean=0.2, ht=0.0, hood=1.0, arm=2.0, el=0.1, arm_b=-0.3, el_b=0.2, claw=1.0, mouth=1.0, glow=1.0, tlash=1.0, cw=3.0, hair=1.5,
      wv=0.5),
    B(wx=13, wy=-50, lean=0.18, ht=0.02, hood=0.9, arm=1.8, el=0.2, arm_b=-0.2, el_b=0.3, claw=0.9, mouth=0.8, glow=1.0, tlash=0.8, cw=2.0, hair=1.2,
      wv=1.5),
]

ROAR = [
    B(wx=12, wy=-46, lean=0.35, ht=0.3, hood=0.4, arm=0.5, el=0.6, arm_b=0.3, el_b=0.7, mouth=0.2, glow=0.8),
    B(wx=11, wy=-56, lean=0.1, ht=0.0, hood=0.8, arm=1.2, el=0.9, arm_b=1.1, el_b=0.9, mouth=0.5, glow=0.9, rise=0.4),
    B(wx=9, wy=-66, lean=-0.12, ht=-0.35, hood=1.0, arm=2.1, el=0.3, arm_b=2.4, el_b=0.3, mouth=1.0, glow=1.0, rise=0.9, claw=1.0, tup=0.7, wv=1.0),
    B(wx=9, wy=-68, lean=-0.14, ht=-0.45, hood=1.0, arm=2.2, el=0.25, arm_b=2.5, el_b=0.25, mouth=1.0, glow=1.0, rise=1.0, claw=1.0, tup=1.0,
      wv=2.0, hair=-1.2, cw=2.0),
    B(wx=9, wy=-68, lean=-0.13, ht=-0.47, hood=1.0, arm=2.25, el=0.22, arm_b=2.45, el_b=0.28, mouth=1.0, glow=1.0, rise=1.0, claw=1.0, tup=1.0,
      wv=3.0, hair=-1.3, cw=2.0),
    B(wx=10, wy=-60, lean=0.1, ht=-0.1, hood=0.9, arm=1.3, el=0.6, arm_b=1.4, el_b=0.6, mouth=0.7, glow=1.0, rise=0.6, tup=0.5, wv=4.0),
    B(wx=11, wy=-52, lean=0.2, ht=0.05, hood=0.7, arm=0.7, el=0.7, arm_b=0.5, el_b=0.8, mouth=0.3, glow=0.9, wv=5.0),
]

STAGGER = [
    B(wx=2, wy=-46, lean=-0.4, ht=-0.45, arm=0.9, el=1.6, arm_b=1.5, el_b=1.4, mouth=0.8, glow=0.3, hood=0.2, hair=1.5),
    B(wx=6, wy=-34, lean=0.6, ht=0.5, arm=0.4, el=0.3, arm_b=0.3, el_b=0.3, mouth=0.4, glow=0.3, hood=0.1, coil=-0.2, hair=1.2),
    B(wx=10, wy=-26, lean=1.0, ht=0.7, arm=0.9, el=0.2, arm_b=0.8, el_b=0.25, mouth=0.35, glow=0.3, hood=0.1, coil=-0.2, hair=1.6),
    B(wx=10, wy=-25, lean=1.02, ht=0.72, arm=0.9, el=0.2, arm_b=0.8, el_b=0.25, mouth=0.3, glow=0.3, hood=0.1, coil=-0.2, hair=1.7, cw=1.0, wv=1.0),
    B(wx=10, wy=-27, lean=0.98, ht=0.6, arm=0.95, el=0.25, arm_b=0.85, el_b=0.3, mouth=0.45, glow=0.35, hood=0.15, coil=-0.2, hair=1.5, cw=1.0, wv=2.0),
    B(wx=8, wy=-40, lean=0.4, ht=0.2, arm=0.8, el=0.8, arm_b=0.7, el_b=0.9, mouth=0.6, glow=0.6, hood=0.5, hair=0.8),
    B(wx=10, wy=-50, lean=0.1, ht=0.0, arm=0.8, el=0.9, arm_b=0.7, el_b=1.0, mouth=0.7, glow=1.0, hood=0.9, claw=1.0),
]

DEATH = [
    B(wx=0, wy=-60, lean=-0.45, ht=-0.6, arm=2.2, el=0.4, arm_b=2.5, el_b=0.3, mouth=1.0, hood=1.0, glow=0.6, hair=-1.0),
    B(wx=2, wy=-54, lean=-0.3, ht=-0.45, arm=1.8, el=0.6, arm_b=2.0, el_b=0.5, mouth=0.8, hood=0.7, glow=0.5),
    B(wx=8, wy=-44, lean=0.3, ht=0.3, arm=0.9, el=0.5, arm_b=0.8, el_b=0.5, mouth=0.5, hood=0.4, glow=0.4, hair=0.8),
    B(wx=14, wy=-30, lean=0.9, ht=0.6, arm=0.6, el=0.3, arm_b=0.5, el_b=0.3, mouth=0.4, hood=0.2, glow=0.3, hair=1.4, coil=-0.2),
    B(wx=22, wy=-21, lean=1.3, ht=0.8, arm=1.0, el=0.2, arm_b=0.8, el_b=0.3, mouth=0.35, hood=0.1, glow=0.2, hair=1.8, coil=-0.3),
    B(wx=28, wy=-15, lean=1.52, ht=0.9, arm=1.5, el=0.2, arm_b=1.3, el_b=0.25, mouth=0.3, hood=0.0, glow=0.1, hair=2.0, coil=-0.3, tlash=0.5),
    B(wx=28, wy=-15, lean=1.52, ht=0.9, arm=1.5, el=0.2, arm_b=1.3, el_b=0.25, mouth=0.25, hood=0.0, glow=0.05, hair=2.0, coil=-0.3, tup=0.4, wv=1.5),
    B(wx=28, wy=-15, lean=1.52, ht=0.9, arm=1.5, el=0.2, arm_b=1.3, el_b=0.25, mouth=0.2, hood=0.0, glow=0.0, hair=2.0, coil=-0.3, tlash=0.8, wv=3.0),
    B(wx=28, wy=-15, lean=1.52, ht=0.92, arm=1.5, el=0.2, arm_b=1.3, el_b=0.25, mouth=0.15, hood=0.0, glow=0.0, hair=2.0, coil=-0.3, tlash=0.85,
      wv=3.4),
]


CLIPS = {
    'idle': clip([_idle(k / 8) for k in range(8)], 7, loop=True),
    'walk': clip([_walk(k / 8) for k in range(8)], 10, loop=True),
    'sh_spit': clip(SPIT, 10, seg={'w': [0, 2], 's': [3, 4], 'r': [5, 6]}),
    'sh_tail': clip(TAIL, 12, seg={'w': [0, 2], 's': [3, 5], 'r': [6, 7]}),
    'sh_lunge': clip(LUNGE, 12, seg={'w': [0, 2], 'd': [3, 4, 3], 'x': [5, 5], 'v': [6, 8, 7], 'r': [9, 9]}),
    'sh_snakes': clip(SNAKES, 9, seg={'w': [0, 1], 'a': [2, 5, 2]}),
    'sh_drip': clip(DRIP, 10, seg={'w': [0, 2], 's': [3, 4], 'r': [5, 6]}),
    'sh_gaze': clip(GAZE, 10, seg={'w': [0, 3], 's': [4, 5], 'r': [6, 6]}),
    'sh_venom': clip(VENOM, 10, seg={'w': [0, 1], 'a': [2, 3], 'r': [4, 5]}),
    'sh_nova': clip(NOVA, 10, seg={'w': [0, 1], 's': [2, 3]}),
    'sh_roar': clip(ROAR, 9, seg={'a': [0, 6]}),
    'sh_stagger': clip(STAGGER, 8, seg={'a': [0, 6]}),
    'sh_death': clip(DEATH, 8, seg={'a': [0, 8]}),
}
