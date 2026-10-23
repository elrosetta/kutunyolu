"""v42 sınav otağları (Otağ Yeri) mürekkep-cel çizimleri: üç sınav otağı + Han Otağı (açık / kapalı), otağ içi,
ödül sandığı, sınav tamgaları (arayüz).

Tasarım: Kut Kapısı'nın önüne kurulan küçük bir konak yeri. Her sınavın kendi keçe otağı var (yurt_ink._yurt gövdesi:
kerege duvar, uuk kubbe, tündük, kilim kuşakları, kolan ipleri); renk ve tuğ sancağı sınavı söyler:
  cabuk       Çabuk (süre)       krem keçe, ALTIN kuşak, altın sancakta kum saati tamgası
  dokunulmaz  Dokunulmaz (hasar) ak keçe, AK / gök kuşak, ak sancakta kalkan tamgası (daire + haç)
  avci        Avcı (av)          krem keçe, KIZIL kuşak, kızıl sancakta yay-ok tamgası
  han         Han Otağı          büyük ak keçe, kızıl + lacivert + altın, iki yan tuğ, tepede alemli tuğ (üç sınav birden)
Kapalı otağın kapısı koyu keçe perdeyle örtülü, iki ip çapraz bağlı (mühür oyunda çizilir: bekleyen / çatlak). Açık
otağın keçe perdesi yukarı dürülmüş, içerisi sıcak ışıkla parlar (ışıma katmanı).

Çıktı (tek atlas): assets/fx/ink/otag_v2.png (+ _e ışıma) + otag_v2.json {texel, sprites: {ad: {rect, pivot, texel, glow}}}
  otag_<tür>_acik / otag_<tür>_kapali   köken: taban ortası, texel 4
  otag_ic        otağ içi (240 x 135 birim, köken sol üst), texel 4
  sandik_kapali / sandik_acik  ödül sandığı (köken taban ortası), texel 4
  ui_tamga_<tür> beyaz tamga + mürekkep altlık (arayüzde renklendirilir), texel 8
  ui_muhur       beyaz mum mühür diski (kapı mührü / arayüz altlığı; renklendirilir), texel 8
Kullanım (tools/artgen içinde):
    python otag_ink.py                 temel atlas
    KY_HD=2 python otag_ink.py         HD atlas (assets_hd/x2/fx/ink/otag_v2.png), sonra
    python otag_ink.py --paketle       HD PNG -> WebP + manifest girişi
    python otag_ink.py --onizleme out.png
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import hdpack  # noqa: E402,F401
from hdpack import HD  # noqa: E402
import inkkit as ik  # noqa: E402
from inkkit import Ink, INK  # noqa: E402
from inkprop import (Prop, FELT, FELT_C, FELT_DK, RED, RED_D, BLUE, SKYB, GOLD, WOOD, WOOD_D, WOOD_R, ROPE, HAIR_K,  # noqa: E402
                     diamond, tassel, grass_tufts, ram_motif)
from yurt_ink import _yurt, _tug_head  # noqa: E402

A = os.path.normpath(os.path.join(HERE, '..', '..', 'assets'))

GOLDC = Ink('#dcaa44', '#7e4a26', '#ffeaa0', '#4a2414', name='altın kuşak')
AK = Ink('#eef0f4', '#8f96b4', '#ffffff', '#5c6080', name='ak kuşak')
DOOR_IN = (0.16, 0.08, 0.06)
WARM = (1.0, 0.72, 0.36)
WARM_GLOW = (1.0, 0.56, 0.2)

TURLER = {
    #            keçe    kuşak   kuşak2  kapı    sancak  R   duvar kubbe
    'cabuk': (FELT_C, GOLDC, RED_D, WOOD_R, GOLDC, 30, 28, 26),
    'dokunulmaz': (FELT, AK, SKYB, BLUE, AK, 30, 28, 26),
    'avci': (FELT_C, RED, RED_D, WOOD_R, RED, 30, 28, 26),
    'han': (FELT, RED, BLUE, WOOD_R, RED, 40, 34, 34),
}


def glyph_strokes(kind):
    """Sınav tamgası fırça darbeleri (-1..1 kutusu, y aşağı)."""
    if kind == 'cabuk':   # kum saati
        return [[(-0.8, -0.92), (0.8, -0.92)], [(-0.8, 0.92), (0.8, 0.92)], [(-0.6, -0.9), (0.0, 0.0), (0.6, 0.9)],
                [(0.6, -0.9), (0.0, 0.0), (-0.6, 0.9)]]
    if kind == 'dokunulmaz':   # kalkan: daire + haç
        c = [(math.cos(a) * 0.86, math.sin(a) * 0.86) for a in np.linspace(-math.pi * 0.5, math.pi * 1.48, 26)]
        return [c, [(0.0, -0.62), (0.0, 0.62)], [(-0.62, 0.0), (0.62, 0.0)]]
    if kind == 'avci':   # yay ve ok
        bow = [(-0.15, -1.0), (-0.62, -0.62), (-0.82, 0.0), (-0.62, 0.62), (-0.15, 1.0)]
        return [bow, [(-0.15, -1.0), (-0.15, 1.0)], [(-0.7, 0.0), (0.98, 0.0)], [(0.62, -0.34), (0.98, 0.0), (0.62, 0.34)]]
    # han: alem (üç uçlu tepe) + taban
    return [[(-0.78, 0.82), (-0.78, -0.42)], [(0.0, 0.82), (0.0, -1.0)], [(0.78, 0.82), (0.78, -0.42)], [(-0.95, 0.82), (0.95, 0.82)],
            [(-0.42, -0.62), (0.0, -0.18), (0.42, -0.62)]]


def draw_glyph(cv, kind, cx, cy, s, w, z, col=(1, 1, 1), glow=None, ink_under=True, alpha=1.0):
    for pts in glyph_strokes(kind):
        q = [(cx + x * s, cy + y * s) for x, y in pts]
        if ink_under:
            cv.stroke(q, w * 1.8, z=z, col=INK, taper=(0.06, 0.1), alpha=0.95 * alpha)
        cv.stroke(q, w * 1.15, z=z + 0.001, col=col, glow=glow, taper=(0.08, 0.14), alpha=alpha)


def _door(cv, dw, dh, acik, z, kind):
    """Kapı: oyma çerçeve + (açık) içi ışıyan aralık ve yukarı dürülmüş keçe perde | (kapalı) çapraz bağlı keçe perde."""
    frame = cv.blob([(-dw - 3.2, 0, 0.0), (-dw - 3.2, -dh - 3.5, 0.0), (dw + 3.2, -dh - 3.5, 0.0), (dw + 3.2, 0, 0.0)])
    cv.shape(frame, WOOD_D, z=z, sd=1.6, hi=0.5)
    hole = cv.blob([(-dw, 0, 0.0), (-dw, -dh, 0.0), (dw, -dh, 0.0), (dw, 0, 0.0)])
    if acik:
        cv.fill(hole, DOOR_IN, z=z + 0.1)
        # içerideki sıcak ışık: tabanda yayılan ışık + arka duvarda kilim
        cv.fill(cv.ellipse((0, -dh * 0.3), dw * 0.9, dh * 0.42), WARM, z=z + 0.11, glow=(0.7, 0.36, 0.12), alpha=0.45)
        kl = cv.blob([(-dw * 0.62, -dh * 0.88, 0.0), (dw * 0.62, -dh * 0.88, 0.0), (dw * 0.62, -dh * 0.3, 0.0), (-dw * 0.62, -dh * 0.3, 0.0)])
        cv.shape(kl, RED, z=z + 0.12, sd=0.6, ol=0.5, details=[('col', cv.blob(diamond(0, -dh * 0.6, dw * 0.36, dh * 0.16)), GOLD.base)])
        cv.fill(cv.blob([(-dw, -0.2, 0.0), (dw, -0.2, 0.0), (dw * 0.8, -dh * 0.12, 0.0), (-dw * 0.8, -dh * 0.12, 0.0)]), (1.0, 0.85, 0.5), z=z + 0.13,
                glow=WARM_GLOW, alpha=0.8)
        # yukarı dürülmüş perde (rulo) + iki ip
        roll = cv.capsule((-dw - 1.5, -dh - 0.6), (dw + 1.5, -dh - 0.6), 2.4, 2.4)
        cv.shape(roll, FELT_DK, z=z + 0.2, sd=1.0, hi=0.4, details=[('stroke', [(-dw, -dh - 1.6), (dw, -dh - 1.6)], 0.8, RED.base, (0.1, 0.1))])
        for f in (-1, 1):
            cv.stroke([(f * dw * 0.6, -dh - 3.0), (f * dw * 0.62, -dh + 1.6)], 0.9, z=z + 0.25, col=ROPE.base, taper=(0.1, 0.3))
    else:
        det = [('col', cv.blob(diamond(0, -dh * 0.55, dw * 0.7, dh * 0.3)), RED_D.base), ('col', cv.blob(diamond(0, -dh * 0.55, dw * 0.36, dh * 0.15)), RED.base)]
        for yy in (-dh * 0.12, -dh * 0.92):
            det.append(('col', cv.blob([(-dw, yy - 1.0, 0.0), (dw, yy - 1.0, 0.0), (dw, yy + 1.0, 0.0), (-dw, yy + 1.0, 0.0)]), RED.base))
        det += cv.fold([(-dw * 0.55, -dh + 2), (-dw * 0.5, -2)], depth=1.2, w=0.7)
        det += cv.fold([(dw * 0.5, -dh + 2), (dw * 0.55, -2)], depth=1.2, w=0.7)
        cv.shape(hole, FELT_DK, z=z + 0.1, sd=dw * 0.5, hi=0.4, details=det)
        for f in (-1, 1):
            cv.stroke([(-dw * 1.05 * f, -dh * 0.95), (dw * 1.05 * f, -dh * 0.12)], 1.0, z=z + 0.2, col=ROPE.base, taper=(0.15, 0.15))
        # mühür yeri: oyunda mum mühür çizilir (bekleyen / çatlak); burada koyu oyuk
        cv.fill(cv.ellipse((0, -dh * 0.55), dw * 0.62, dw * 0.62), INK, z=z + 0.15, alpha=0.55)


def otag(kind, acik):
    felt, band, band2, door, ban, R, wh, dh_ = TURLER[kind]
    eave = R + 4
    tug_h = 30 if kind != 'han' else 40
    Wd = 2 * eave + (40 if kind == 'han' else 34)
    Hd = wh + dh_ + tug_h + 22
    P = Prop(Wd, Hd, Wd / 2, Hd - 3, ss=4)
    cv = P.cv
    top, apex, eave = _yurt(cv, R, wh, dh_, felt, band, band2, door, rich=(kind == 'han'), seed={'cabuk': 11, 'dokunulmaz': 12, 'avci': 13, 'han': 14}[kind])
    dw = 7.5 if kind != 'han' else 9.0
    dh = wh * 0.9
    _door(cv, dw, dh, acik, 1.5, kind)
    # alınlıkta sınav tamgası (altın)
    draw_glyph(cv, kind, 0, -dh - 7.5, 2.4, 0.9, 1.9, col=GOLD.hi if acik else (0.82, 0.74, 0.6), glow=(0.9, 0.6, 0.2) if acik else None)
    # tündükten tuğ direği + sancak (sınav tamgası)
    cv.shape(cv.capsule((0, apex + 2), (0, apex - tug_h), 1.1, 0.9), WOOD_D, z=2.0, sd=0.6, hi=0.3)
    y0 = apex - tug_h + 6
    fl_w, fl_h = (17, 12) if kind != 'han' else (22, 15)
    flag = cv.blob([(1, y0, 0.0), (fl_w * 0.5, y0 + 1.2), (fl_w, y0 - 0.5, 0.0), (fl_w - 3.5, y0 + fl_h * 0.5), (fl_w + 1, y0 + fl_h, 0.0),
                    (fl_w * 0.5, y0 + fl_h - 1.0), (1, y0 + fl_h, 0.0)])
    cv.shape(flag, ban, z=1.95, sd=2.0, hi=0.4, details=cv.fold([(5, y0 + 2), (7, y0 + fl_h - 2)], depth=0.8, w=0.7))
    draw_glyph(cv, kind, fl_w * 0.45, y0 + fl_h * 0.5, fl_h * 0.3, 0.75, 1.97, col=INK if kind == 'dokunulmaz' else (1.0, 0.95, 0.85), ink_under=False)
    _tug_head(cv, 0, apex - tug_h, 0.55 if kind != 'han' else 0.75, 2.1, sway=0.05)
    if kind == 'han':
        # iki yanda küçük tuğ (kızıl / lacivert sancak) ve altın saçaklı yan örtüler
        for f, bm in ((-1, RED), (1, BLUE)):
            x = f * (eave + 10)
            cv.shape(cv.capsule((x, 0), (x, -58), 1.1, 0.9), WOOD_D, z=-0.5, sd=0.6, hi=0.3)
            fl = cv.blob([(x, -54, 0.0), (x + f * 11, -52.5), (x + f * 9, -48), (x + f * 12, -43, 0.0), (x, -44, 0.0)])
            cv.shape(fl, bm, z=-0.45, sd=1.4, hi=0.3)
            _tug_head(cv, x, -58, 0.45, -0.4, sway=0.06)
        for f in (-1, 1):
            x = f * (R * 0.62)
            hang = cv.blob([(x - 5, top + 6, 0.0), (x + 5, top + 6, 0.0), (x + 5, -8, 0.0), (x, -4, 0.0), (x - 5, -8, 0.0)])
            cv.shape(hang, BLUE, z=1.4, sd=2.5, hi=0.4, details=[('col', cv.blob(diamond(x, top + 16, 3.0, 4.4)), GOLD.base)])
            tassel(cv, x, -5, 5, 2.4, GOLD, 1.45, strands=3)
    if acik:
        # kapıdan yere düşen sıcak ışık ve tündükten sızan ışık
        cv.fill(cv.ellipse((0, -0.5), dw * 2.6, 2.4), WARM, z=0.9, glow=WARM_GLOW, alpha=0.35)
        cv.fill(cv.ellipse((0, apex + 1.0), 4.5, 1.4), WARM, z=0.95, glow=WARM_GLOW, alpha=0.8)
    grass_tufts(cv, -eave - 4, eave + 4, 0, 26 if kind != 'han' else 36, 2.4, 5)
    return P.done()


# ------------------------------------------------------------------ otağ içi
def otag_ic():
    Wd, Hd = 240, 135
    P = Prop(Wd, Hd, 0, 0, ss=3)
    cv = P.cv
    rng = np.random.default_rng(42)
    WALL = Ink('#6a4a38', '#3a2428', '#8c6a4c', name='iç keçe')
    # arka duvar (kerege üstünde keçe), hafif kavisli tavan çizgisi
    wall = cv.blob([(0, 0, 0.0), (Wd, 0, 0.0), (Wd, Hd, 0.0), (0, Hd, 0.0)])
    cv.shape(wall, WALL, z=0.0, sd=0.0, ol=0.0, hi=0.0, noshadow=True)
    # uuk (tavan sırıkları): tündükten ışınsal, kızıl boyalı
    tc = (120, -18)
    for k in range(-9, 10):
        ex = 120 + k * 15
        cv.stroke([(tc[0] + k * 1.2, tc[1] + 14), (ex, 44 + abs(k) * 0.6)], 3.4, z=0.2, col=WOOD_R.base, taper=(0.05, 0.05))
        cv.stroke([(tc[0] + k * 1.2 - 0.6, tc[1] + 14), (ex - 0.6, 44 + abs(k) * 0.6)], 0.5, z=0.21, col=WOOD_R.hi, taper=(0.05, 0.05))
    # tündük çemberi ve ay ışığı
    cv.shape(cv.ellipse((120, 3), 26, 7), WOOD, z=0.3, sd=1.6, hi=0.5)
    cv.fill(cv.ellipse((120, 2), 20, 4.6), (0.55, 0.75, 1.0), z=0.31, glow=(0.3, 0.5, 0.9), alpha=0.85)
    for k in range(-3, 4):
        cv.stroke([(120 + k * 5, -2), (120 + k * 5.6, 7)], 1.0, z=0.32, col=WOOD_D.base, taper=(0.1, 0.1))
    # kerege kafesi (çapraz çıtalar), duvarın alt üçte ikisi
    for k in range(-6, 34):
        x = k * 8.0
        cv.stroke([(x, 46), (x + 52, 106)], 2.2, z=0.4, col=WOOD.hi, taper=(0.05, 0.05), alpha=0.75)
        cv.stroke([(x + 52, 46), (x, 106)], 2.2, z=0.41, col=WOOD.base, taper=(0.05, 0.05), alpha=0.85)
    cv.fill(cv.blob([(0, 42, 0.0), (Wd, 42, 0.0), (Wd, 48, 0.0), (0, 48, 0.0)]), RED.base, z=0.45)
    for k in range(16):
        x = 8 + k * 15
        cv.fill(cv.blob(diamond(x, 45, 3.0, 2.2)), GOLD.base, z=0.46)
    # asılı kilimler (sol, sağ) ve tuğ
    for x0, mat in ((14, RED), (186, BLUE)):
        kl = cv.blob([(x0, 52, 0.0), (x0 + 40, 52, 0.0), (x0 + 40, 100, 0.0), (x0 + 20, 104), (x0, 100, 0.0)])
        det = [('col', cv.blob(diamond(x0 + 20, 76, 13, 17)), GOLD.base), ('col', cv.blob(diamond(x0 + 20, 76, 7, 9)), RED_D.base if mat is BLUE else BLUE.base),
               ('col', cv.blob(diamond(x0 + 20, 76, 2.5, 3.2)), (0.95, 0.9, 0.8))]
        for yy in (56, 96):
            det.append(('col', cv.blob([(x0, yy - 1.2, 0.0), (x0 + 40, yy - 1.2, 0.0), (x0 + 40, yy + 1.2, 0.0), (x0, yy + 1.2, 0.0)]), GOLD.shadow))
        cv.shape(kl, mat, z=0.6, sd=3.0, hi=0.5, details=det)
        for j in range(7):
            tassel(cv, x0 + 3 + j * 5.6, 101 + (2 if j == 3 else 0), 4, 1.6, GOLD, 0.62, strands=2)
    # yer kilimi (perspektif)
    rug = cv.blob([(26, 112, 0.0), (214, 112, 0.0), (236, 135, 0.0), (4, 135, 0.0)])
    det = []
    for k in range(7):
        x = 40 + k * 26.5
        det.append(('col', cv.blob(diamond(x, 123, 9, 6)), GOLD.base))
        det.append(('col', cv.blob(diamond(x, 123, 4, 2.6)), BLUE.base))
    det.append(('col', cv.blob([(26, 112, 0.0), (214, 112, 0.0), (216, 115, 0.0), (24, 115, 0.0)]), GOLD.shadow))
    cv.fill(cv.blob([(0, 104, 0.0), (Wd, 104, 0.0), (Wd, Hd, 0.0), (0, Hd, 0.0)]), (0.24, 0.15, 0.12), z=0.5)
    cv.shape(rug, RED, z=0.7, sd=2.0, hi=0.6, details=det)
    # ocak (sol orta): taş halka, kor, alev ışığı
    cv.shape(cv.ellipse((62, 114), 16, 4.2), Ink('#77727c', '#3e3a4c', '#b0aab6'), z=0.8, sd=1.2, hi=0.4)
    cv.fill(cv.ellipse((62, 112.5), 11, 2.8), (1.0, 0.5, 0.15), z=0.81, glow=(1.0, 0.45, 0.1))
    for j in range(5):
        a = rng.uniform(-0.4, 0.4)
        h = rng.uniform(12, 20)
        cv.stroke([(62 + (j - 2) * 3.0, 112), (62 + (j - 2) * 2.0 + a * 6, 112 - h * 0.6), (62 + (j - 2) * 1.0 + a * 9, 112 - h)], 3.2 - abs(j - 2) * 0.6,
                  z=0.82, col=(1.0, 0.62, 0.22), glow=(1.0, 0.5, 0.15), taper=(0.2, 0.9))
    # sıcak ışık havası: ocak çevresi ve ortada sandık yeri
    return P.done(outer=0.0, rim=0.0)


# ------------------------------------------------------------------ ödül sandığı
def sandik(acik):
    P = Prop(48, 44, 24, 41, ss=4)
    cv = P.cv
    body = cv.blob([(-18, 0, 0.0), (-18, -16, 0.0), (18, -16, 0.0), (18, 0, 0.0)])
    det = [('col', cv.blob([(-18, -10, 0.0), (18, -10, 0.0), (18, -8.4, 0.0), (-18, -8.4, 0.0)]), GOLD.shadow)]
    for x in (-12, 12):
        det.append(('col', cv.blob([(x - 1.6, 0, 0.0), (x - 1.6, -16, 0.0), (x + 1.6, -16, 0.0), (x + 1.6, 0, 0.0)]), GOLD.base))
    cv.shape(body, WOOD_R, z=0.0, sd=2.5, hi=0.6, details=det)
    ram_motif(cv, -5.5, -6.0, 2.2, 0.9, 0.1, col=GOLD.base)
    ram_motif(cv, 5.5, -6.0, 2.2, 0.9, 0.1, col=GOLD.base)
    if acik:
        # içerisi: altın ve Kut ışığı, kapak arkada dik
        lid = cv.blob([(-18, -16, 0.0), (-17, -33), (0, -37), (17, -33), (18, -16, 0.0)])
        cv.shape(lid, WOOD_R, z=-0.2, sd=2.0, hi=0.5, details=[('col', cv.blob([(-2, -16, 0.0), (2, -16, 0.0), (2, -36, 0.0), (-2, -36, 0.0)]), GOLD.base)])
        cv.fill(cv.blob([(-17, -16, 0.0), (17, -16, 0.0), (15, -19, 0.0), (-15, -19, 0.0)]), (0.25, 0.12, 0.08), z=0.05)
        for j in range(9):
            x = -13 + j * 3.2
            cv.shape(cv.ellipse((x, -18.2 - (1.2 if j % 2 else 0.0)), 2.0, 1.2), GOLD, z=0.2 + j * 0.001, sd=0.4, hi=0.3, ol=0.5)
        cv.fill(cv.ellipse((0, -22), 15, 7), WARM, z=0.3, glow=(1.0, 0.65, 0.2), alpha=0.18)
    else:
        lid = cv.blob([(-19, -15.5, 0.0), (-18, -22), (0, -25.5), (18, -22), (19, -15.5, 0.0)])
        cv.shape(lid, WOOD_R, z=0.2, sd=2.0, hi=0.6, details=[('col', cv.blob([(-2, -15.5, 0.0), (2, -15.5, 0.0), (2, -25.4, 0.0), (-2, -25.4, 0.0)]), GOLD.base)])
        cv.shape(cv.ellipse((0, -15.5), 3.4, 3.0), GOLD, z=0.3, sd=0.8, hi=0.4)
        cv.fill(cv.ellipse((0, -15.2), 1.2, 1.4), INK, z=0.31)
    return P.done(outer=1.0, rim=0.25)


# ------------------------------------------------------------------ arayüz tamgaları
def ui_tamga(kind):
    P = Prop(16, 16, 8, 8, ss=4, tex=8.0)
    draw_glyph(P.cv, kind, 0.0, 0.0, 6.0, 1.7, 0.0, col=(1.0, 1.0, 1.0))
    return P.done(outer=0.6, rim=0.0, grain=0.0)


def ui_muhur():
    P = Prop(16, 16, 8, 8, ss=4, tex=8.0)
    cv = P.cv
    rng = np.random.default_rng(5)
    pts = []
    for k in range(20):
        a = k / 20 * 2 * math.pi
        rr = 7.0 * (1.0 + 0.06 * math.sin(a * 3 + 0.4) + rng.uniform(-0.03, 0.03))
        pts.append((math.cos(a) * rr, math.sin(a) * rr))
    W = Ink('#f4f0e8', '#a49cac', '#ffffff', '#6a6478')
    cv.shape(cv.blob(pts), W, z=0, sd=0.9, hi=0.4, ol=1.0, details=[('shade', cv.ellipse((0, 0), 5.4, 5.4))])
    cv.fill(cv.ellipse((-0.2, -0.2), 5.0, 5.0), W.base, z=0.01)
    return P.done(outer=0.6, rim=0.0, grain=0.0)


def sprites():
    out = []
    for k in ('cabuk', 'dokunulmaz', 'avci', 'han'):
        out.append(('otag_%s_acik' % k, otag(k, True), 4.0))
        out.append(('otag_%s_kapali' % k, otag(k, False), 4.0))
    out.append(('otag_ic', otag_ic(), 4.0))
    out.append(('sandik_kapali', sandik(False), 4.0))
    out.append(('sandik_acik', sandik(True), 4.0))
    for k in ('cabuk', 'dokunulmaz', 'avci', 'han'):
        out.append(('ui_tamga_' + k, ui_tamga(k), 8.0))
    out.append(('ui_muhur', ui_muhur(), 8.0))
    return out


def to8(arr):
    return (np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)


def export():
    from export_ink_ortam import save
    items = sprites()
    W = 1024
    pad = 4
    order = sorted(items, key=lambda t: -t[1][0].shape[0])
    x = y = rowh = 0
    pos = {}
    for n, (r, g, o), tx in order:
        h, w = r.shape[0] // HD, r.shape[1] // HD
        if x + w + pad > W:
            x = 0
            y += rowh + pad
            rowh = 0
        pos[n] = (x, y)
        x += w + pad
        rowh = max(rowh, h)
    Hh = int(math.ceil((y + rowh) / 4.0) * 4)
    alb = np.zeros((Hh * HD, W * HD, 4), np.float32)
    glo = np.zeros_like(alb)
    meta = {"texel": 4.0, "filter": "linear", "_not": "v42 sınav otağları atlası (tools/artgen/otag_ink.py). rect/pivot temel doku pikseli; texel: doku pikseli / dünya (arayüz) birimi.",
            "sprites": {}}
    for n, (r, g, o), tx in items:
        px, py = pos[n]
        h, w = r.shape[:2]
        alb[py * HD:py * HD + h, px * HD:px * HD + w] = r
        glo[py * HD:py * HD + h, px * HD:px * HD + w] = g
        meta["sprites"][n] = {"rect": [px, py, w // HD, h // HD], "pivot": [round(o[0], 2), round(o[1], 2)], "texel": tx,
                              "glow": bool(g[..., 3].max() > 0.02)}
    save(to8(alb), 'fx/ink', 'otag_v2.png')
    save(to8(glo), 'fx/ink', 'otag_v2_e.png')
    json.dump(meta, open(os.path.join(A, 'fx', 'ink', 'otag_v2.json'), 'w', encoding='utf-8', newline='\n'), indent=1, ensure_ascii=False)
    print('  otag_v2', W, Hh, len(items))


def paketle():
    import hashlib
    import hd_paket
    rel = 'fx/ink/otag_v2.png'
    new, txt = hd_paket._encode(rel)
    print(txt)
    if not new:
        return
    man = json.load(open(hd_paket.MAN, encoding='utf-8'))
    from PIL import Image
    bw, bh = Image.open(os.path.join(A, rel)).size
    md5 = hashlib.md5(open(os.path.join(A, rel), 'rb').read()).hexdigest()
    man[rel] = [bw, bh, new, md5]
    json.dump(dict(sorted(man.items())), open(hd_paket.MAN, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    hd_paket._write_import(os.path.join(hd_paket.X2, new), new)
    print('manifest:', rel, man[rel])


def onizleme(out):
    from PIL import Image
    items = sprites()
    cols = [(n, r, g) for n, (r, g, o), tx in items if not n.startswith('ui_') and n != 'otag_ic']
    Wt = sum(c[1].shape[1] + 16 for c in cols) + 16
    Ht = max(c[1].shape[0] for c in cols) + 32
    bg = np.zeros((Ht, Wt, 3), np.float32)
    bg[:] = (0.07, 0.09, 0.15)
    x = 16
    for n, r, g in cols:
        h, w = r.shape[:2]
        y = Ht - 16 - h
        a = r[..., 3:4]
        bg[y:y + h, x:x + w] = bg[y:y + h, x:x + w] * (1 - a) + r[..., :3] * a + g[..., :3] * g[..., 3:4] * 0.9
        x += w + 16
    Image.fromarray((np.clip(bg, 0, 1) * 255).astype(np.uint8)).save(out)
    ic = [t for t in items if t[0] == 'otag_ic'][0][1]
    r, g = ic[0], ic[1]
    img = r[..., :3] * r[..., 3:4] + g[..., :3] * g[..., 3:4] * 0.9
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(out.replace('.png', '_ic.png'))
    print('önizleme', out)


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--paketle' in a:
        paketle()
    elif '--onizleme' in a:
        onizleme(a[a.index('--onizleme') + 1])
    else:
        export()
