"""v39: Şulmus Yavrusu (kimlik sulmus_yavrusu; Şulmus'un çağırdığı minik cin, yapay zekâ "swarm", UÇAN).

Minik boynuzlu cin ruhu: yuvarlak mor-kurşuni gövde, ortada tek iri yeşil ışıyan göz, sivri kulaklar ve küçük koç
boynuzları, eğri dişli sırıtış, yarasa zar kanatları, arkada kor kuyruk teli (ışır), sarkan pençeli ayakçıklar.

Satırlar (hücre 32 x 32 dünya, ayak (16, 24), gövde merkezi ayağın 8 birim üstünde, doku 4):
  fly 6 (döngü: kanat çırpışı), tele 3 (döngüsüz: kanatlar geriye toplanır, göz alevlenir),
  swoop 4 (döngüsüz: hız çizgileriyle öne pike), hurt 2.
Çapalar: 'mouth' ve 'hand' = göz / ağız önü (efekt çıkışı).
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import lerp2
import yaratik_ink_kit as yk
import ucan_v29 as u29
import y39_sulmus as sm

TEX = 4.0
CELL = (128, 128)       # dünya 32 x 32
FEET = (64, 96)         # dünya (16, 24)

SKIN = sm.SKIN
MEM = Ink('#5a3a5e', '#2c1632', '#86608a', '#160a1a', name='zar kanat')
MEM_B = MEM.darker(0.7)
BONE_W = Ink('#3a2a40', '#1a1020', '#6a5272', name='kanat kemiği')
EMBER = (1.0, 0.6, 0.2)
EMBER_G = (1.0, 0.35, 0.05)
C0 = (0.0, -8.0)


def draw(cv, p):
    ph = p['ph']
    c = (C0[0], C0[1] + p['bob'])
    u29.body_xf(cv, c, p['rot'], p['sx'], p['sy'], (0.0, 0.0))
    # kor kuyruk teli (arkada)
    tail = [(c[0] - 3.0, c[1] + 2.0)]
    for k in range(6):
        u = (k + 1) / 6
        tail.append((c[0] - 3.0 - u * 9.0 * p['tl'], c[1] + 2.0 + math.sin(ph * 2 + u * 4) * 1.6 * u - u * 1.5 * p['tlift']))
    cv.shape(ik.taper_path([cv.W(q) for q in tail], cv.u(1.6), prof=lambda u: max(0.08, 1 - u)), SKIN.darker(0.8), z=-20, sd=0.3, ol=0.8)
    for k, q in enumerate(tail[3:]):
        cv.fill(cv.ellipse(q, 0.7 - k * 0.15, 0.7 - k * 0.15), EMBER, z=-19.9 + k * 0.01, glow=EMBER_G)
    yk.glow_soft(cv, tail[-1], 2.4, EMBER_G, z=-19.8, alpha=0.6)
    yk.sparks(cv, tail[-1], 3, 0.5, 3.0, EMBER, -19.7, seed=int(ph * 3) % 11, w=0.9, glow=EMBER_G)
    # uzak kanat
    S_b = (c[0] - 1.0, c[1] - 2.6)
    S_f = (c[0] + 0.4, c[1] - 2.2)
    u29.bat_wing(cv, S_b, p['ws'] - 0.15, p['wf'], L=11.0, lag=p['wl'], mats=(MEM_B, BONE_W.darker(0.8), MEM.shadow), z=-12, near=False,
                 sweep=p['sweep'], flank=(c[0] - 2.5, c[1] + 1.0), seed=2, ph=ph)
    # ayakçıklar
    for k, x in enumerate((-1.2, 1.4)):
        b = (c[0] + x, c[1] + 3.6)
        f = (b[0] - 0.8 - p['swp'] * 2.5 + k * 0.4, b[1] + 3.0 - p['swp'] * 1.2)
        cv.shape(cv.limb([b, f], [0.8, 0.55]), SKIN if k else SKIN.darker(0.75), z=-4 + k, sd=0.3, ol=0.8)
        for j in range(3):
            a = 0.9 + j * 0.45
            cv.stroke([f, (f[0] + math.cos(a) * 1.2, f[1] + math.sin(a) * 1.2)], 0.9, z=-3.9 + k, col=INK, taper=(0.1, 0.9))
    # gövde + baş (tek yuvarlak)
    bd = cv.blob([(c[0] - 4.6, c[1] + 0.4), (c[0] - 3.6, c[1] - 3.6), (c[0] + 0.4, c[1] - 5.0), (c[0] + 4.2, c[1] - 3.4), (c[0] + 5.2, c[1] + 0.4),
                  (c[0] + 3.6, c[1] + 3.8), (c[0] - 0.2, c[1] + 4.8), (c[0] - 3.4, c[1] + 3.6)])
    cv.shape(bd, SKIN, z=0, sd=1.3, hi=0.4, ol=1.0, bounce=0.25, details=[('shade', cv.ellipse((c[0] - 1.6, c[1] + 2.6), 2.6, 1.6))])
    # kulaklar + boynuzlar
    ear = p['ear']
    for k, (x, m, zz) in enumerate(((-1.4, SKIN.darker(0.75), -1), (1.0, SKIN, 3))):
        b = (c[0] + x, c[1] - 3.8)
        cv.shape(cv.blob([(b[0] + 1.2, b[1] + 0.6), (b[0] - 1.0 - ear, b[1] - 1.6 - ear * 0.5), (b[0] - 4.6 - ear * 1.5, b[1] - 3.4 - ear, 0.0),
                          (b[0] - 1.4, b[1] + 1.0)]), m, z=zz, sd=0.4, ol=0.85, details=[('col', cv.blob([(b[0], b[1] + 0.2), (b[0] - 3.6 - ear, b[1] - 2.6 - ear * 0.8, 0.0), (b[0] - 1.0, b[1] + 0.6)]), sm.EAR_IN)])
    for k, (x, m, zz) in enumerate(((0.6, sm.HORN.darker(0.72), -0.5), (2.4, sm.HORN, 4))):
        b = (c[0] + x, c[1] - 4.4)
        pts = [b, (b[0] - 0.6, b[1] - 1.8), (b[0] - 2.0, b[1] - 2.4), (b[0] - 2.8, b[1] - 1.4)]
        cv.shape(ik.taper_path([cv.W(q) for q in pts], cv.u(1.3), prof=lambda u: max(0.15, 1 - 0.8 * u)), m, z=zz, sd=0.3, hi=0.2, ol=0.85)
    # iri tek göz
    ey = p['eye']
    eg = (c[0] + 1.6, c[1] - 1.2)
    rr = 1.7 + 0.35 * (ey - 1)
    cv.shape(cv.ellipse(eg, rr + 0.6, rr + 0.45), Ink('#14101a', '#0a080c', '#2a2232'), z=5, sd=0.2, ol=0.8)
    yk.eye_glow(cv, eg, rr, rr * 0.92, 0, sm.GREEN, sm.GREEN_G, 6, halo=2.2 + 0.6 * ey, halo_a=0.35 + 0.2 * ey)
    if ey > 0.3:
        cv.fill(cv.ellipse((eg[0] + 0.4, eg[1]), 0.45, rr * 0.75), INK, z=6.1)
        cv.fill(cv.ellipse((eg[0] - 0.4, eg[1] - 0.5), 0.35, 0.3), sm.GREEN_HOT, z=6.2, glow=sm.GREEN_HOT)
    else:
        cv.stroke([(eg[0] - 1.6, eg[1]), (eg[0] + 1.6, eg[1] - 0.2)], 1.2, z=6.3, col=INK)
    cv.stroke([(eg[0] - 2.2, eg[1] - 2.2), (eg[0] + 2.0, eg[1] - 1.6 - 0.4 * (ey > 1.5))], 1.1, z=6.4, col=INK, taper=(0.3, 0.6))
    # sırıtış
    g = p['grin']
    m0 = (c[0] + 0.4, c[1] + 1.8)
    mouth = cv.blob([m0, (c[0] + 2.6, c[1] + 2.0), (c[0] + 4.8, c[1] + 1.2, 0.0), (c[0] + 3.8, c[1] + 2.8 + g), (c[0] + 1.6, c[1] + 3.2 + g)])
    cv.shape(mouth, Ink('#2a0e1c', '#16060e', '#4a1a2c'), z=7, sd=0.2, ol=0.85)
    for k, x in enumerate((1.2, 2.3, 3.4, 4.2)):
        y0 = c[1] + 1.9 - (0.2 if k == 3 else 0.0)
        cv.shape(cv.blob([(c[0] + x - 0.35, y0), (c[0] + x + 0.35, y0), (c[0] + x + 0.1 * (k % 2), y0 + 0.9, 0.0)]), sm.TOOTH, z=7.2 + k * 0.01, sd=0.1, ol=0.5)
    # yakın kanat
    u29.bat_wing(cv, S_f, p['ws'], p['wf'], L=12.0, lag=p['wl'], mats=(MEM, BONE_W, MEM.hi), z=10, near=True, sweep=p['sweep'],
                 flank=(c[0] - 1.6, c[1] + 2.0), seed=3, ph=ph)
    mouth_w = u29.to_world(cv, (c[0] + 4.0, c[1] + 0.6))
    cv.pop()
    if p['streak'] > 0:
        u29.speed_lines(cv, (c[0] - 4.0, c[1]), p['sdir'], n=5, L=12 * p['streak'], spread=9, w=1.4, col=INK, alpha=0.55, z=-40, seed=int(ph * 5) % 17)
        u29.speed_lines(cv, (c[0] - 3.0, c[1] + 1.0), p['sdir'], n=3, L=9 * p['streak'], spread=6, w=1.2, col=sm.GREEN, alpha=0.6, z=-39, seed=5, glow=sm.GREEN_G)
    if p['flare'] > 0:
        yk.glow_soft(cv, mouth_w, 4.0 * p['flare'], sm.GREEN_G, z=30, alpha=0.6 * p['flare'])
        yk.sparks(cv, (C0[0] + 1.6, C0[1] - 1.2 + p['bob']), 6, 2.6, 5.0 + 2 * p['flare'], sm.GREEN_HOT, 30.1, seed=3, w=1.0, glow=sm.GREEN_G)
    return {'mouth': mouth_w}


REST = dict(bob=0.0, rot=0.0, sx=1.0, sy=1.0, ws=0.0, wf=0.0, wl=0.0, sweep=0.3, tl=1.0, tlift=0.0, ear=0.0, eye=1.0, grin=0.4, swp=0.0,
            streak=0.0, sdir=(1.0, 0.0), flare=0.0)


def _fly(t):
    w, bob = u29.flap(t, bob_amp=1.4)
    return dict(ws=w['ws'], wf=w['wf'], wl=w['wl'], bob=bob, rot=0.06 * math.sin(math.tau * t), ear=0.4 * math.sin(math.tau * t + 1.0),
                grin=0.4 + 0.2 * math.sin(math.tau * t * 2), ph=math.tau * t)


_TELE = [dict(ws=-0.7, wf=0.6, wl=-0.4, sweep=0.9, bob=-0.6, rot=-0.25, sx=0.94, sy=1.06, eye=1.6, ear=0.8, grin=0.8, tl=0.8, tlift=1.0, flare=0.4),
         dict(ws=-0.85, wf=0.8, wl=-0.6, sweep=1.2, bob=-1.0, rot=-0.35, sx=0.9, sy=1.1, eye=2.0, ear=1.2, grin=1.0, tl=0.7, tlift=1.4, flare=0.8),
         dict(ws=-0.9, wf=0.9, wl=-0.7, sweep=1.3, bob=-1.2, rot=-0.4, sx=0.88, sy=1.12, eye=2.2, ear=1.4, grin=1.0, tl=0.6, tlift=1.6, flare=1.0)]
_SWOOP = [dict(ws=0.2, wf=0.95, wl=0.0, sweep=1.4, rot=0.45, sx=1.15, sy=0.88, eye=2.0, ear=-0.8, grin=1.0, tl=1.3, swp=1.0, streak=0.8, sdir=(0.9, 0.45)),
          dict(ws=0.15, wf=1.0, wl=0.0, sweep=1.5, rot=0.5, sx=1.2, sy=0.85, eye=2.0, ear=-1.0, grin=1.0, tl=1.4, swp=1.0, streak=1.0, sdir=(0.9, 0.45), ph=1.0),
          dict(ws=0.3, wf=0.9, wl=0.2, sweep=1.4, rot=0.4, sx=1.15, sy=0.88, eye=1.8, ear=-0.8, grin=1.0, tl=1.3, swp=0.9, streak=0.9, sdir=(0.95, 0.3), ph=2.0),
          dict(ws=-0.6, wf=0.3, wl=-0.6, sweep=0.6, rot=0.1, eye=1.4, ear=-0.2, grin=0.7, tl=1.1, swp=0.4, streak=0.3, sdir=(1.0, 0.0), ph=3.0)]
_HURT = [dict(ws=-0.4, wf=0.7, wl=0.6, rot=-0.45, sx=1.06, sy=0.94, bob=-1.0, eye=0.0, grin=1.0, ear=1.6, tl=0.8, tlift=-1.0),
         dict(ws=0.4, wf=0.4, wl=-0.3, rot=-0.2, bob=0.0, eye=1.0, grin=0.6, ear=0.8)]


def _row(frames, fps, loop, pose):
    return dict(frames=frames, fps=fps, loop=loop, pose=pose, ts=None, mk=None, vx=None)


ROWS = {
    'fly': _row(6, 14, True, _fly),
    'tele': _row(3, 10, False, _TELE),
    'swoop': _row(4, 14, False, _SWOOP),
    'hurt': _row(2, 12, False, _HURT),
}
DURUM = {"idle": "fly", "chase": "fly", "windup": "tele", "swoop": "swoop", "recover": "fly", "evade": "fly",
         "_hurt": "hurt", "_hurt_big": "hurt", "_break": "hurt"}


def anims_for(var='sulmus_yavrusu'):
    return {k: {kk: vv for kk, vv in r.items() if kk != 'pose'} for k, r in ROWS.items()}


def durum_for(var='sulmus_yavrusu'):
    return DURUM


SHADE = dict(outer=0.5, rim=0.7, rim_col=(0.7, 0.78, 1.0), rim_dir=(0.6, -0.8), rim_w=1.2, form=(3.0, (0.78, 0.74, 0.88)))


def render_frame(anim, i, var='sulmus_yavrusu', ss=3):
    r = ROWS[anim]
    src = r['pose'](i / r['frames']) if callable(r['pose']) else r['pose'][i]
    p = dict(REST, **src)
    if 'ph' not in src:
        p['ph'] = i * 1.1
    cv = u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss)
    info = draw(cv, p)
    rgba, _nm, em = cv.finish(**SHADE)
    m = (round(float(info['mouth'][0]), 2), round(float(info['mouth'][1]), 2))
    return rgba, None, em, {'mouth': m, 'hand': m}
