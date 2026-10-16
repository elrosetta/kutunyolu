"""inkprop: stil v2 "mürekkep-cel" dünya nesneleri (süs, sunak, totem, toplanabilir, mermi) için ortak yardımcılar.

inkkit.InkCanvas üstüne ince bir katman: dünya biriminde çizilir, doku yoğunluğu TEX = 4 doku pikseli / dünya birimi
(v2 kamerası 2,0 yakın: 1080p'de 1 doku pikseli = 1 ekran pikseli). Çıktı düz (önçarpılmamış) RGBA albedo + ışıma
(toplamalı, ayrı doku) + köken (doku pikseli). Oyunda doğrusal süzgeç + mipmap (Level._decor_v2 / SusV2.gd).

Malzemeler gece ışığına göre seçildi: gölge tonları mor-maviye kayar (inkkit.shade_of), ışık sol üstten.
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK

TEX = 4.0

# ------------------------------------------------------------------ ortak malzemeler (gece, şenlikli yurt)
FELT = Ink('#e9e1cd', '#8c8fae', '#fffaf0', '#5d5d80', name='ak keçe')
FELT_C = Ink('#d8c7a4', '#86788e', '#f6ead0', name='krem keçe')
FELT_DK = Ink('#5a4a40', '#2c2430', '#7c6858', name='koyu keçe')
RED = Ink('#b8342c', '#5e1830', '#e8664c', '#3a0e22', name='kilim kızılı')
RED_D = Ink('#7c2028', '#3c0e22', '#a83c38', name='koyu kızıl')
BLUE = Ink('#2f5395', '#192650', '#5c88cc', '#101838', name='lacivert')
SKYB = Ink('#5f9ccc', '#2e4c80', '#a8d4f0', name='gök mavisi')
TURQ = Ink('#2fb2a8', '#17606a', '#8cf0e0', name='firuze çini')
GOLD = Ink('#dba443', '#87502a', '#fff0b4', '#4e2a1c', kind='metal', name='altın')
BRONZE = Ink('#b27a3c', '#5c3424', '#f0c088', '#3a2018', kind='metal', name='tunç')
IRON = Ink('#5f6272', '#2a2a38', '#a8acc0', '#16161e', kind='metal', name='demir')
STEEL = Ink('#8a90a4', '#3c4056', '#e8ecf8', '#1e2030', kind='metal', name='çelik')
WOOD = Ink('#7c5538', '#3e2a2c', '#b08458', '#24181c', name='ahşap')
WOOD_D = Ink('#53392c', '#291c22', '#7c5a44', name='koyu ahşap')
WOOD_R = Ink('#9a3a2a', '#4a1a24', '#d06448', name='boyalı ahşap')
STONE = Ink('#8d909a', '#4a4a62', '#c4c8d2', '#2c2c40', name='taş')
STONE_W = Ink('#b6b2a4', '#65647a', '#e2dece', name='ak taş')
STONE_D = Ink('#5e6070', '#30304a', '#8a8e9e', name='koyu taş')
MOSS = Ink('#4f6e48', '#263a34', '#86a874', name='yosun')
LEATHER = Ink('#7a4a30', '#3a2026', '#ae7450', name='deri')
HAIR_K = Ink('#2a262e', '#121018', '#5a5462', name='kara at kılı')
HAIR_W = Ink('#e4e0d6', '#8a8aa4', '#ffffff', name='ak at kılı')
ROPE = Ink('#bca27a', '#6a5040', '#e8d4a8', name='kıl ip')
BARK_W = Ink('#e6e4da', '#8e92a8', '#ffffff', '#55587a', name='kayın kabuğu')
LEAF = Ink('#4d7a54', '#22403c', '#8ec08a', name='yaprak')
COPPER = Ink('#b0603a', '#56282a', '#eea078', kind='metal', name='bakır')
CLOTH_COLS = [(0.72, 0.2, 0.18), (0.88, 0.86, 0.8), (0.22, 0.38, 0.7), (0.86, 0.66, 0.24), (0.2, 0.56, 0.5)]

FIRE = (1.0, 0.56, 0.16)
FIRE_HOT = (1.0, 0.86, 0.5)
FIRE_GLOW = (1.0, 0.48, 0.12)
KUT = (0.45, 1.0, 0.95)
KUT_GLOW = (0.3, 0.95, 1.0)


class Prop:
    """Dünya biriminde ölçülen nesne tuvali. (w, h) dünya boyutu, (ox, oy) köken (sol üstten, dünya)."""

    def __init__(self, w, h, ox, oy, ss=3, tex=TEX):
        self.tex = tex
        self.w, self.h = int(round(w * tex)), int(round(h * tex))
        self.ox, self.oy = ox * tex, oy * tex
        self.cv = ik.InkCanvas(self.w, self.h, self.ox, self.oy, k=tex, ss=ss)

    def done(self, outer=1.1, rim=0.32, rim_col=(0.6, 0.78, 1.0), form=None, grain=ik.GRAIN):
        rgba, nm, em = self.cv.finish(outer=outer, rim=rim, rim_col=rim_col, form=form, grain=grain)
        ga = em[..., 3:4]
        glow = np.concatenate([np.where(ga > 1e-4, em[..., :3] / np.maximum(ga, 1e-4), 0), ga], -1)
        return rgba, glow, (self.ox, self.oy)


# ------------------------------------------------------------------ çizim yardımcıları
def arc_pts(cx, cy, rx, ry, a0, a1, n=16):
    return [(cx + math.cos(a) * rx, cy + math.sin(a) * ry) for a in np.linspace(a0, a1, n)]


def flame(cv, x, y, h, w, z, seed=0, glow=True, lick=0.0):
    """Katmanlı alev: dış turuncu, iç sarı, beyaz çekirdek; hepsi ışıma katmanına da yazılır (toplamalı)."""
    rng = np.random.default_rng(seed)
    sway = lick + rng.uniform(-0.15, 0.15)
    outer = [(x - w * 0.5, y), (x - w * 0.62, y - h * 0.3), (x - w * 0.3, y - h * 0.62), (x - w * 0.2 + sway * w, y - h * 0.8, 0.0),
             (x - w * 0.02, y - h * 0.62), (x + w * 0.12 + sway * w, y - h, 0.0), (x + w * 0.34, y - h * 0.55),
             (x + w * 0.62, y - h * 0.32), (x + w * 0.5, y)]
    cv.fill(cv.blob(outer), (0.96, 0.42, 0.12), z=z, glow=(0.9, 0.34, 0.06) if glow else None)
    mid = [(x - w * 0.32, y), (x - w * 0.36, y - h * 0.3), (x - w * 0.08, y - h * 0.58), (x + w * 0.06 + sway * w * 0.6, y - h * 0.82, 0.0),
           (x + w * 0.22, y - h * 0.42), (x + w * 0.32, y)]
    cv.fill(cv.blob(mid), (1.0, 0.72, 0.26), z=z + 0.01, glow=(1.0, 0.62, 0.18) if glow else None)
    core = [(x - w * 0.16, y), (x - w * 0.12, y - h * 0.3), (x + w * 0.02, y - h * 0.5, 0.0), (x + w * 0.14, y - h * 0.26), (x + w * 0.14, y)]
    cv.fill(cv.blob(core), (1.0, 0.95, 0.78), z=z + 0.02, glow=(1.0, 0.9, 0.6) if glow else None)
    # mürekkep diller (çizgi roman alevi: dış kenarda birkaç koyu fırça kıvrımı)
    for k in range(2):
        sx = x + (k - 0.5) * w * 0.5
        cv.stroke([(sx, y - h * 0.1), (sx + w * 0.08, y - h * 0.35), (sx - w * 0.04, y - h * 0.55)], 1.2, z=z + 0.03,
                  col=(0.55, 0.12, 0.05), taper=(0.6, 0.9), alpha=0.7)


def ram_horn(cx, cy, s, flip=1.0, turns=1.15, n=26):
    """Koçboynuzu motifi (sarmal): dünya noktaları listesi."""
    pts = []
    for i in range(n):
        t = i / (n - 1)
        a = -math.pi / 2 + t * turns * 2 * math.pi
        r = s * (1.0 - 0.78 * t)
        pts.append((cx + flip * (math.cos(a) * r), cy + math.sin(a) * r + s * 0.35 * (1 - t)))
    return pts


def ram_motif(cv, cx, cy, s, w, z, col=INK, glow=None):
    """Simetrik koçboynuzu: ortada dikey sap, iki yana kıvrılan sarmallar."""
    cv.stroke([(cx, cy + s * 0.9), (cx, cy - s * 0.1)], w, z=z, col=col, taper=(0.2, 0.2), glow=glow)
    for f in (-1.0, 1.0):
        base = [(cx, cy - s * 0.1), (cx + f * s * 0.45, cy - s * 0.65)]
        sp = ram_horn(cx + f * s * 0.85, cy - s * 0.25, s * 0.42, flip=-f)
        cv.stroke(base + sp, w, z=z, col=col, taper=(0.1, 0.7), glow=glow)


def diamond(cx, cy, rx, ry):
    return [(cx, cy - ry, 0.0), (cx + rx, cy, 0.0), (cx, cy + ry, 0.0), (cx - rx, cy, 0.0)]


def tassel(cv, x, y, ln, w, mat, z, sway=0.0, strands=5):
    """Püskül / at kılı demeti: bağ düğümü + aşağı sarkan sivri tutamlar."""
    paths = []
    for i in range(strands):
        dx = (i - (strands - 1) / 2) * w / strands
        tip = (x + dx * 1.6 + sway * ln, y + ln * (0.85 + 0.15 * math.cos(i * 1.7)))
        paths.append(cv.blob([(x + dx - w * 0.12, y), (x + dx + w * 0.12, y), (tip[0] + w * 0.05, (y + tip[1]) / 2), (tip[0], tip[1], 0.0),
                              (tip[0] - w * 0.08, (y + tip[1]) / 2)]))
    cv.shape(ik.union(*paths), mat, z=z, sd=w * 0.35, ol=0.8,
             details=[('ink', [(x + (i - 2) * w * 0.18, y + ln * 0.2), (x + (i - 2) * w * 0.3 + sway * ln * 0.6, y + ln * 0.75)], 0.8)
                      for i in range(strands)])


def bunting_flag(cv, x, y, w, h, col, z):
    """Üçgen bayrakçık."""
    m = Ink(col)
    cv.shape(cv.blob([(x - w / 2, y, 0.0), (x + w / 2, y, 0.0), (x, y + h, 0.0)]), m, z=z, sd=w * 0.2, ol=0.7)


def grass_tufts(cv, x0, x1, y, n, z, seed, hmin=2.5, hmax=7.0, cols=None):
    """Taban ot tutamları (mürekkep uçlu)."""
    rng = np.random.default_rng(seed)
    cols = cols or [(0.24, 0.36, 0.28), (0.36, 0.5, 0.36), (0.18, 0.26, 0.24)]
    for _ in range(n):
        x = rng.uniform(x0, x1)
        h = rng.uniform(hmin, hmax)
        lean = rng.uniform(-0.5, 0.5)
        col = cols[int(rng.integers(len(cols)))]
        cv.stroke([(x, y + 0.6), (x + lean * h * 0.3, y - h * 0.6), (x + lean * h, y - h)], rng.uniform(1.6, 2.6), z=z,
                  col=col, taper=(0.0, 0.85))
        if rng.random() < 0.5:
            cv.stroke([(x + lean * h * 0.55, y - h * 0.62), (x + lean * h, y - h)], 1.0, z=z + 0.01, col=INK, taper=(0.2, 0.9), alpha=0.8)
