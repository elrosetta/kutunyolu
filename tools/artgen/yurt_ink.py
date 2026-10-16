"""Ulu Kayın Yurdu, stil v2 "mürekkep-cel" süsleri (yurt_hd.py piksel sürümünün yerini alır; v1 dosyaları değişmez).

Her süs dünya biriminde çizilir (köken ayak noktası, y yukarı eksi), inkprop.TEX = 4 doku pikseli / dünya birimi.
Adlar v1 ile aynı + "_v2" (Level._hub_prop v2'de sus_v2.json'dan okur); köken ve yaklaşık dünya boyu v1 ile uyumlu,
böylece yerleşim (Level._place_hub) iki stilde ortak.

  yh_otag      han otağı: ak keçe kubbe, kilim kuşakları, at kılı kolan ipleri, oyma kızıl kapı, tündükte tuğ
  yh_cadir     süslü küçük yurt (gök mavisi kuşaklar)
  yh_kayin     Umay'ın dilek kayını: ak kabuk, çaputlar, ışıyan kut yaprakları
  yh_sunak     Umay sunağı: işlemeli ak örtü, süt kâseleri, mumlar, kuş başlıklı taş Umay heykeli
  yh_pinar     kutsal pınar: yosunlu kayalar, ışıyan çağlayan, taş havuz
  yh_demirhane demirci ocağı: taş körük ocağı, saçak, alet askısı, silah sehpası, fıçı
  yh_ors       kütük üstünde örs, kızgın kılıç
  yh_kartal    tünekte bürküt (altın kartal)
  yh_at        eğerli at (kızıl keçe eğer örtüsü, örgülü yele)
  yh_hali_sergi Ozan köşesi: gerili kilim, minderler, kopuz
  yh_hali_1/2  yere serili kilimler, yh_yol_1/2/3 taş döşeme, yh_seki kapı sekisi
  yh_mangal    tunç ateş tası, yh_kandil uzun tunç kandil, yh_fener kancalı fener
  yh_tug_k/m   tuğ: altın alem, at kılı püskül, kızıl / gök sancak
  yh_balbal_1/2 balbal, yh_kurgan dikili taş halkası (Orhun runlu), yh_kazan sacayaklı kazan
  yh_kapi      Kut Kapısı'nın taç kapısı: firuze çini kuşaklar, ışıyan runlar, koçboynuzu tepelik, güneş kursu
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from inkprop import (Prop, FELT, FELT_C, FELT_DK, RED, RED_D, BLUE, SKYB, TURQ, GOLD, BRONZE, IRON, STEEL, WOOD, WOOD_D,
                     WOOD_R, STONE, STONE_W, STONE_D, MOSS, LEATHER, HAIR_K, HAIR_W, ROPE, BARK_W, LEAF, COPPER,
                     CLOTH_COLS, FIRE_GLOW, KUT, KUT_GLOW, arc_pts, flame, ram_motif, diamond, tassel, grass_tufts)


# ------------------------------------------------------------------ yurt gövdesi (otağ ve çadır ortak)
SAG = 0.06   # yatay kuşakların gülümseme eğrisi (hafif yukarıdan bakış): merkez kenarlardan R*SAG aşağıda


def _band(cv, x0, x1, y, h, sag):
    """Kubbe/duvar boyunca hafif kavisli kuşak (dünya noktaları -> cihaz yolu)."""
    n = 9
    R = (x1 - x0) / 2
    cx = (x0 + x1) / 2
    top = [(x0 + (x1 - x0) * i / (n - 1), y + sag * (1 - ((x0 + (x1 - x0) * i / (n - 1) - cx) / R) ** 2)) for i in range(n)]
    bot = [(x, yy + h) for x, yy in top[::-1]]
    pts = [top[0] + (0.0,)] + top[1:-1] + [top[-1] + (0.0,), bot[0] + (0.0,)] + bot[1:-1] + [bot[-1] + (0.0,)]
    return cv.blob(pts)


def _sagy(x, R, y, sag):
    return y + sag * (1 - min(1.0, (x / R) ** 2))


def diff_shift(cv, path, dx, dy):
    """Yol eksi (dünya biriminde kaydırılmış kopyası): ışığın tersindeki gölge hilali."""
    return ik.diff(path, ik.moved(path, cv.u(dx), cv.u(dy)))


def _yurt(cv, R, wall_h, dome_h, felt, band, band2, door_mat, z0=0.0, rich=True, seed=1):
    """R: duvar yarı genişliği. Duvar (kerege) + kubbe (uuk) + tündük; kuşaklar ve kolan ipleri.
    Silindirik gölge açıkça çizilir: ışık solda, sağ yarıda gölge bandı + en sağda derin gölge, saçak altında
    kubbenin duvara düşen gölgesi."""
    rng = np.random.default_rng(seed)
    top = -wall_h
    apex = top - dome_h
    eave = R + 4
    sag = R * SAG
    # --- duvar: hafif şişkin, tabanda koyu keçe etek
    wall = cv.blob([(-R, 0, 0.0), (-R - 1.5, top * 0.5), (-R, top, 0.0), (R, top, 0.0), (R + 1.5, top * 0.5), (R, 0, 0.0)])
    det = []
    # keçe dikişleri (çapraz kapitone) ve dikey kıvrımlar
    for k in range(9):
        x = -R + (k + 0.5) * 2 * R / 9 + rng.uniform(-2, 2)
        det += cv.fold([(x, top + 3), (x + rng.uniform(-1.5, 1.5), top * 0.5), (x + rng.uniform(-1, 1), -3)], depth=1.4, w=0.7)
    for k in range(-14, 15):
        x = k * R / 7
        det.append(('stroke', [(x - 5, top + 4), (x + 5, -5)], 0.7, felt.shadow, (0.1, 0.1)))
    shad = [ik.isect(wall, cv.blob([(R * 0.38, 2, 0.0), (R * 0.38, top - 2, 0.0), (R + 4, top - 2, 0.0), (R + 4, 2, 0.0)])),
            _band(cv, -R - 3, R + 3, top - 1, 7.5, sag)]
    deep = ik.isect(wall, cv.blob([(R * 0.8, 2, 0.0), (R * 0.8, top - 2, 0.0), (R + 4, top - 2, 0.0), (R + 4, 2, 0.0)]))
    det.append(('deep', deep))
    cv.shape(wall, felt, z=z0, noshadow=True, shadows=shad, hi=0.8, details=det)
    cv.shape(_band(cv, -R - 0.5, R + 0.5, -4.5, 5.0, sag * 0.15), FELT_DK, z=z0 + 0.1, sd=1.5, ol=0.8)
    # --- duvar üstü kilim kuşağı (kızıl, elmas tamgalar)
    bh = wall_h * 0.2
    by = top + bh
    bandp = _band(cv, -R - 1, R + 1, top, bh, sag)
    det = []
    n = int(R * 2 / 13)
    for k in range(n):
        x = -R + (k + 0.5) * 2 * R / n
        yc = _sagy(x, R, top + bh / 2, sag)
        det.append(('col', cv.blob(diamond(x, yc, bh * 0.36, bh * 0.36)), GOLD.base))
        det.append(('col', cv.blob(diamond(x, yc, bh * 0.16, bh * 0.16)), band2.base))
        xs = x + R / n
        det.append(('ink', [(xs, _sagy(xs, R, top, sag) + 1), (xs, _sagy(xs, R, by, sag) - 1)], 0.8))
    det.append(('col', _band(cv, -R - 2, R + 2, by - 1.4, 1.4, sag), GOLD.shadow))
    det.append(('shade', ik.isect(bandp, cv.blob([(R * 0.45, top - 3, 0.0), (R + 4, top - 3, 0.0), (R + 4, by + 3, 0.0), (R * 0.45, by + 3, 0.0)]))))
    cv.shape(bandp, band, z=z0 + 0.3, noshadow=True, hi=0.4, details=det)
    # --- kolan ipleri: duvarı saran at kılı ip (iki sıra)
    for yy in (top * 0.42, top * 0.68):
        pts = [(x, _sagy(x, R, yy, sag)) for x in np.linspace(-R - 1.2, R + 1.2, 9)]
        rope = ik.taper_path([cv.W(p) for p in pts], cv.u(1.6), (0.02, 0.02))
        cv.shape(rope, ROPE, z=z0 + 0.4, sd=0.7, ol=0.7,
                 details=[('ink', [(x, _sagy(x, R, yy, sag) - 0.6), (x + 1.4, _sagy(x, R, yy, sag) + 0.7)], 0.6) for x in np.arange(-R, R, 3.2)])
    # --- kubbe (uuk): çatı keçesi, kızıl ve lacivert kuşaklar, ışınsal kaburga dikişleri
    dome_pts = [(-eave, top + 2, 0.0), (-eave + 2, top - dome_h * 0.18), (-R * 0.78, top - dome_h * 0.5), (-R * 0.42, top - dome_h * 0.86),
                (0, apex), (R * 0.42, top - dome_h * 0.86), (R * 0.78, top - dome_h * 0.5), (eave - 2, top - dome_h * 0.18), (eave, top + 2, 0.0)]
    dome = cv.blob(dome_pts)
    ribs = []
    for k in range(1, 14):
        a = -math.pi + k * math.pi / 14
        ex = math.cos(a) * eave * 0.98
        ribs.append(('stroke', [(math.cos(a) * 6, apex + 3), (math.cos(a) * eave * 0.62, top - dome_h * 0.6 + abs(math.sin(a)) * 3),
                                (ex, top + 1 + sag * (1 - (ex / eave) ** 2))], 1.3, GOLD.base if rich else felt.shadow, (0.1, 0.1)))
    dsh = diff_shift(cv, dome, -eave * 0.42, eave * 0.1)
    dd = diff_shift(cv, dome, -eave * 0.16, eave * 0.04)
    ribs.append(('deep', dd))
    cv.shape(dome, felt, z=z0 + 0.5, noshadow=True, shadows=[dsh], hi=1.0, details=ribs)
    # kubbe orta kuşağı: kızıl şerit
    mid = ik.isect(dome, _band(cv, -eave, eave, top - dome_h * 0.5, dome_h * 0.07, sag * 0.6))
    cv.shape(mid, band, z=z0 + 0.65, noshadow=True, shadows=[ik.isect(mid, dsh)], hi=0.3)
    # kubbe eteği kuşağı (lacivert, ak akar su deseni)
    skirt = ik.isect(dome, _band(cv, -eave - 2, eave + 2, top - dome_h * 0.21, dome_h * 0.21 + 3, sag))
    wave = []
    m = int(eave * 2 / 7)
    for k in range(m):
        x = -eave + 4 + k * (2 * eave - 8) / max(1, m - 1)
        yb = _sagy(x, eave, top - dome_h * 0.09, sag)
        wave.append(('stroke', ram_horn_wave(x, yb, 2.6), 1.3, FELT.hi, (0.2, 0.4)))
    wave.append(('col', _band(cv, -eave - 2, eave + 2, top - dome_h * 0.21, 1.2, sag), GOLD.base))
    cv.shape(skirt, band2, z=z0 + 0.6, noshadow=True, shadows=[ik.isect(skirt, dsh)], hi=0.5, details=wave)
    # tündük (tepe çemberi)
    cv.shape(cv.ellipse((0, apex + 1.5), 10, 3.6), GOLD if rich else WOOD, z=z0 + 0.8, sd=1.6, hi=0.5)
    cv.shape(cv.ellipse((0, apex + 1.0), 6, 1.8), WOOD_D, z=z0 + 0.85, sd=0.8, ol=0.6)
    # --- kapı: oyma kanatlar, altın koçboynuzu, çerçeve
    dw = R * 0.19
    dh = wall_h * 0.82
    frame = cv.blob([(-dw - 3, 0, 0.0), (-dw - 3, -dh - 3, 0.0), (dw + 3, -dh - 3, 0.0), (dw + 3, 0, 0.0)])
    cv.shape(frame, WOOD_D, z=z0 + 1.0, sd=2.0, hi=0.5)
    for f in (-1, 1):
        leaf = cv.blob([(f * 0.4, -0.5, 0.0), (f * 0.4, -dh, 0.0), (f * dw, -dh, 0.0), (f * dw, -0.5, 0.0)])
        cx = f * dw * 0.5
        dd = [('col', cv.blob([(cx - dw * 0.34, -dh * 0.9, 0.0), (cx + dw * 0.34, -dh * 0.9, 0.0), (cx + dw * 0.34, -dh * 0.55, 0.0), (cx - dw * 0.34, -dh * 0.55, 0.0)]), door_mat.shadow),
              ('col', cv.blob([(cx - dw * 0.34, -dh * 0.45, 0.0), (cx + dw * 0.34, -dh * 0.45, 0.0), (cx + dw * 0.34, -dh * 0.1, 0.0), (cx - dw * 0.34, -dh * 0.1, 0.0)]), door_mat.shadow)]
        cv.shape(leaf, door_mat, z=z0 + 1.1, sd=dw * 0.4, hi=0.4, details=dd)
        ram_motif(cv, cx, -dh * 0.75, dw * 0.28, 1.2, z0 + 1.2, col=GOLD.base)
        ram_motif(cv, cx, -dh * 0.3, dw * 0.28, 1.2, z0 + 1.2, col=GOLD.base)
    # kapı aralığından sızan sıcak ışık
    cv.fill(cv.blob([(-0.6, -0.5, 0.0), (-0.6, -dh + 1, 0.0), (0.6, -dh + 1, 0.0), (0.6, -0.5, 0.0)]), (1.0, 0.78, 0.4), z=z0 + 1.3,
            glow=(1.0, 0.6, 0.2))
    # kapı üstü oyma alınlık
    lint = cv.blob([(-dw - 5, -dh - 3, 0.0), (dw + 5, -dh - 3, 0.0), (dw + 3, -dh - 7, 0.0), (0, -dh - 9.5), (-dw - 3, -dh - 7, 0.0)])
    cv.shape(lint, WOOD_R, z=z0 + 1.05, sd=1.4, hi=0.4)
    ram_motif(cv, 0, -dh - 5.2, 2.6, 1.0, z0 + 1.1, col=GOLD.base)
    return top, apex, eave


def ram_horn_wave(x, y, s):
    """Akar su / koçboynuzu sırası için tek kıvrım (dünya noktaları)."""
    pts = [(x - s * 1.4, y + s * 0.4), (x - s * 0.6, y - s * 0.3), (x + s * 0.2, y - s * 0.6)]
    for i in range(10):
        a = -math.pi / 2 + i * 0.62
        r = s * 0.6 * (1 - i / 12)
        pts.append((x + s * 0.2 + math.cos(a) * r, y - s * 0.6 + r + math.sin(a) * r))
    return pts


def _tug_head(cv, x, y, s, z, banner=None, sway=0.0):
    """Tuğ başı: altın alem (hilal + üç uçlu tepe), altında at kılı püskül; isteğe bağlı sancak."""
    # alem: üç sivri uç + hilal
    tri = cv.blob([(x - 5 * s, y - 2 * s), (x - 6 * s, y - 10 * s, 0.0), (x - 3 * s, y - 5 * s), (x, y - 14 * s, 0.0),
                   (x + 3 * s, y - 5 * s), (x + 6 * s, y - 10 * s, 0.0), (x + 5 * s, y - 2 * s), (x, y + 1 * s)])
    cv.shape(tri, GOLD, z=z + 0.3, sd=1.2 * s, hi=0.4)
    cv.shape(cv.ellipse((x, y + 1.5 * s), 2.6 * s, 2.0 * s), GOLD, z=z + 0.35, sd=0.8, hi=0.3)
    # püskül: kara + ak at kılı (iki kat)
    tassel(cv, x, y + 3 * s, 20 * s, 9 * s, HAIR_K, z, sway=sway, strands=6)
    tassel(cv, x, y + 3 * s, 15 * s, 6 * s, HAIR_W, z + 0.1, sway=sway * 0.7, strands=4)
    cv.shape(cv.ellipse((x, y + 3.5 * s), 3.6 * s, 2.2 * s), RED, z=z + 0.2, sd=0.8, hi=0.3)


def otag():
    P = Prop(212, 186, 106, 182)
    cv = P.cv
    top, apex, eave = _yurt(cv, 88, 50, 72, FELT, RED, BLUE, WOOD_R, rich=True, seed=3)
    # yan sancak örtüleri (lacivert, altın tamga)
    for f in (-1, 1):
        x = f * 54
        hang = cv.blob([(x - 7, top + 10, 0.0), (x + 7, top + 10, 0.0), (x + 7, -10, 0.0), (x, -5, 0.0), (x - 7, -10, 0.0)])
        cv.shape(hang, BLUE, z=1.5, sd=3.5, hi=0.4,
                 details=[('col', cv.blob(diamond(x, top + 26, 4.2, 6.0)), GOLD.base), ('col', cv.blob(diamond(x, top + 26, 1.8, 2.8)), RED.base),
                          ('stroke', [(x - 6, top + 14), (x + 6, top + 14)], 1.2, GOLD.base, (0.0, 0.0))])
        tassel(cv, x, -6, 6, 3, GOLD, 1.6, strands=3)
    # tündükten yükselen tuğ direği + alem + kızıl flama
    pole = cv.capsule((0, apex + 2), (0, apex - 40), 1.4, 1.1)
    cv.shape(pole, WOOD_D, z=2.0, sd=0.8, hi=0.3)
    pen = cv.blob([(1, apex - 36, 0.0), (22, apex - 33), (16, apex - 30.5), (24, apex - 28, 0.0), (1, apex - 27.5, 0.0)])
    cv.shape(pen, RED, z=1.9, sd=2.0, hi=0.4, details=cv.fold([(4, apex - 32), (14, apex - 31.5)], depth=0.8, w=0.8))
    _tug_head(cv, 0, apex - 40, 0.9, 2.1, sway=0.05)
    grass_tufts(cv, -100, 100, 0, 70, 3.0, 5)
    return P.done()


def cadir():
    P = Prop(150, 124, 75, 120)
    cv = P.cv
    top, apex, eave = _yurt(cv, 62, 38, 48, FELT_C, BLUE, SKYB, BLUE, rich=False, seed=7)
    # tündükten tüten duman ağzı: küçük ahşap baca halkası
    grass_tufts(cv, -70, 70, 0, 46, 3.0, 9)
    return P.done()


# ------------------------------------------------------------------ direkler, ateşler
def tug(banner_mat, seed=0):
    """Tuğ: uzun direk, altın alem + at kılı püskül, rüzgârda dalgalanan çatal uçlu sancak (altın tamga)."""
    P = Prop(60, 174, 13, 170)
    cv = P.cv
    H = 158
    cv.shape(cv.capsule((0, 0), (0, -H), 1.9, 1.4), WOOD_D, z=0, sd=1.0, hi=0.4,
             details=[('stroke', [(-0.6, -10), (-0.6, -H + 6)], 0.8, WOOD.hi, (0.1, 0.1))])
    # taş ayak
    cv.shape(cv.blob([(-6, 0.5, 0.0), (-5, -4), (-2.5, -6, 0.0), (2.5, -6, 0.0), (5, -4), (6, 0.5, 0.0)]), STONE, z=0.2, sd=2.0, hi=0.4)
    # sancak: direğin sağında, çatal uç
    y0 = -H + 24
    hgt = 30
    rng = np.random.default_rng(seed)
    pts_top = [(2, y0)] + [(2 + x, y0 + math.sin(x * 0.12 + 0.6) * 3.2) for x in (12, 24, 36)]
    pts_bot = [(2 + x, y0 + hgt - x * 0.12 + math.sin(x * 0.12 + 1.2) * 3.2) for x in (36, 24, 12)] + [(2, y0 + hgt)]
    fork = (2 + 30, y0 + hgt * 0.55 + math.sin(30 * 0.12 + 0.9) * 3)
    flag = cv.blob([pts_top[0] + (0.0,)] + pts_top[1:3] + [(pts_top[3][0] + 6, pts_top[3][1] + 1, 0.0), fork + (0.0,),
                    (pts_bot[0][0] + 6, pts_bot[0][1] - 1, 0.0)] + pts_bot[1:3] + [pts_bot[3] + (0.0,)])
    det = [('col', cv.blob(diamond(16, y0 + hgt * 0.48, 6.4, 7.6)), GOLD.base), ('col', cv.blob(diamond(16, y0 + hgt * 0.48, 3.4, 4.2)), banner_mat.base),
           ('stroke', [(15, y0 + hgt * 0.48 - 1.5), (17, y0 + hgt * 0.48 + 1.5)], 0.9, GOLD.hi, (0.1, 0.1))]
    det += cv.fold([(8, y0 + 3), (12, y0 + hgt * 0.5), (9, y0 + hgt - 3)], depth=1.6, w=0.9)
    det += cv.fold([(27, y0 + 3), (30, y0 + hgt * 0.45), (28, y0 + hgt - 6)], depth=1.4, w=0.8)
    det.append(('col', cv.blob([(2, y0, 0.0), (40, y0 + 2, 0.0), (40, y0 + 4.5, 0.0), (2, y0 + 2.6, 0.0)]), GOLD.base))
    cv.shape(flag, banner_mat, z=-0.2, sd=5.0, hi=0.6, details=det)
    # direğe bağlayan halkalar
    for yy in (y0 + 2, y0 + hgt - 2):
        cv.shape(cv.ellipse((0, yy), 2.8, 1.4), GOLD, z=0.3, sd=0.6, ol=0.6)
    _tug_head(cv, 0, -H, 1.25, 0.6, sway=0.08)
    grass_tufts(cv, -10, 10, 0, 12, 1.0, seed + 3)
    return P.done()


def tug_k():
    return tug(RED, 11)


def tug_m():
    return tug(BLUE, 12)


def kandil():
    """Uzun tunç kandil: üç ayaklı taban, boğumlu gövde, tepede yağ tası ve alev."""
    P = Prop(32, 104, 16, 100)
    cv = P.cv
    for f in (-1, 0, 1):
        cv.shape(cv.blob([(f * 2, -10), (f * 9, -1.5), (f * 10, 0.4, 0.0), (f * 7.5, 0.4, 0.0), (f * 1, -6)]), BRONZE, z=0.1 * f, sd=1.0, hi=0.3)
    cv.shape(cv.capsule((0, -6), (0, -78), 1.6, 1.3), BRONZE, z=0.3, sd=0.9, hi=0.4)
    for yy in (-24, -50, -70):
        cv.shape(cv.ellipse((0, yy), 3.6, 2.2), GOLD, z=0.4, sd=0.9, hi=0.3)
    bowl = cv.blob([(-9, -82, 0.0), (9, -82, 0.0), (6, -76), (0, -74.5), (-6, -76)])
    cv.shape(bowl, BRONZE, z=0.5, sd=1.8, hi=0.5,
             details=[('stroke', [(-8, -81), (8, -81)], 1.0, GOLD.hi, (0.1, 0.1))])
    flame(cv, 0, -82, 15, 10, 0.6, seed=3)
    return P.done()


def mangal():
    """Tunç ateş tası: üç kıvrık ayak, kenarı koçboynuzu süslü kase, harlı alev."""
    P = Prop(40, 60, 20, 56)
    cv = P.cv
    for f in (-1, 1):
        cv.stroke([(f * 4, -24), (f * 9, -12), (f * 12, -2), (f * 15, 0)], 2.6, z=0.1, col=BRONZE.shadow, taper=(0.1, 0.1))
        cv.shape(ik.taper_path([cv.W(p) for p in [(f * 4, -24), (f * 9, -12), (f * 12, -2), (f * 15, 0)]], cv.u(2.4), (0.05, 0.05)),
                 BRONZE, z=0.2, sd=0.8, hi=0.3)
    cv.shape(ik.taper_path([cv.W(p) for p in [(0, -24), (0.5, -10), (0, 0)]], cv.u(2.4), (0.05, 0.05)), BRONZE, z=0.15, sd=0.8)
    bowl = cv.blob([(-15, -30, 0.0), (15, -30, 0.0), (11, -22), (0, -19.5), (-11, -22)])
    det = []
    for x in (-8, 0, 8):
        det.append(('stroke', ram_horn_wave(x, -25.5, 1.8), 1.0, GOLD.hi, (0.2, 0.4)))
    cv.shape(bowl, BRONZE, z=0.5, sd=3.0, hi=0.6, details=det)
    cv.shape(cv.ellipse((0, -30), 15, 2.4), Ink('#3a2420', '#1e1218', '#5a3828'), z=0.45, sd=0.5, ol=0.7)
    # közler
    for k in range(6):
        x = -10 + k * 4
        cv.fill(cv.ellipse((x, -30.5), 2.2, 1.2), (1.0, 0.5 + 0.06 * k, 0.15), z=0.55, glow=(1.0, 0.45, 0.1))
    flame(cv, 0, -30, 26, 20, 0.6, seed=5)
    flame(cv, -6, -30, 15, 10, 0.62, seed=6, lick=-0.2)
    flame(cv, 7, -30, 17, 11, 0.64, seed=7, lick=0.2)
    return P.done()


def fener():
    """Kancalı direkte fener: ahşap direk, demir kol, kehribar camlı fener (ışır), kırmızı ak bağ."""
    P = Prop(44, 108, 12, 104)
    cv = P.cv
    cv.shape(cv.capsule((0, 0), (0, -96), 1.9, 1.5), WOOD_D, z=0, sd=1.0, hi=0.4)
    arm = [(0, -92), (10, -96), (20, -94), (25, -88)]
    cv.shape(ik.taper_path([cv.W(p) for p in arm], cv.u(1.6), (0.05, 0.3)), IRON, z=0.3, sd=0.6, ol=0.8)
    cv.stroke([(25, -88), (25, -82)], 1.0, z=0.3, col=INK)
    # fener gövdesi
    cap = cv.blob([(19, -80, 0.0), (31, -80, 0.0), (28, -84), (25, -85.5, 0.0), (22, -84)])
    cv.shape(cap, IRON, z=0.5, sd=1.0, hi=0.4)
    glass = cv.blob([(20, -80, 0.0), (30, -80, 0.0), (31, -70), (30, -61, 0.0), (20, -61, 0.0), (19, -70)])
    cv.shape(glass, Ink('#f4b44e', '#c46a24', '#fff2c0'), z=0.6, sd=1.6, hi=0.0, ol=0.7, glow=(1.0, 0.62, 0.22))
    cv.fill(cv.ellipse((25, -69), 2.6, 4.0), (1.0, 0.96, 0.8), z=0.65, glow=(1.0, 0.85, 0.5))
    for x in (20.2, 25, 29.8):
        cv.stroke([(x, -80), (x, -61)], 1.2, z=0.7, col=INK, taper=(0.05, 0.05))
    cv.shape(cv.blob([(18.5, -61, 0.0), (31.5, -61, 0.0), (29, -58, 0.0), (21, -58, 0.0)]), IRON, z=0.75, sd=0.8, ol=0.7)
    # direğe bağlı kızıl-ak bez
    cv.shape(cv.blob([(1, -60, 0.0), (6, -58), (8, -40), (5, -38, 0.0), (3, -46), (1, -50, 0.0)]), RED, z=0.2, sd=1.4, hi=0.3)
    cv.shape(cv.blob([(1, -58, 0.0), (3.5, -57), (4.5, -44), (2.5, -42, 0.0), (1, -48, 0.0)]), FELT, z=0.25, sd=0.8, ol=0.6)
    cv.shape(cv.blob([(-5, 0.5, 0.0), (-4, -3), (0, -4.5), (4, -3), (5, 0.5, 0.0)]), STONE, z=0.2, sd=1.4, hi=0.4)
    return P.done()


def kazan():
    """Sacayak üstünde kara kazan, altında harlı ateş, kenarından taşan buhar izi."""
    P = Prop(60, 70, 30, 66)
    cv = P.cv
    for f in (-1, 1):
        cv.shape(ik.taper_path([cv.W(p) for p in [(f * 22, 0), (f * 10, -36), (f * 2, -58)]], cv.u(2.6), (0.05, 0.1)), WOOD, z=-0.5, sd=0.9, hi=0.3)
    cv.shape(ik.taper_path([cv.W(p) for p in [(3, 1), (1, -36), (0, -58)]], cv.u(2.4), (0.05, 0.1)), WOOD_D, z=-0.6, sd=0.8)
    cv.stroke([(0, -57), (0, -44)], 1.0, z=-0.4, col=INK)
    # odun ve ateş
    for a in (-0.4, 0.3):
        cv.shape(cv.capsule((-12 * math.cos(a), -2 + 4 * math.sin(a)), (12 * math.cos(a), -2 - 4 * math.sin(a)), 2.2, 2.0), WOOD_D, z=0.0, sd=1.0)
    flame(cv, 0, -3, 22, 22, 0.2, seed=8)
    # kazan
    pot = cv.blob([(-15, -42, 0.0), (15, -42, 0.0), (17, -34), (14, -24), (0, -19), (-14, -24), (-17, -34)])
    cv.shape(pot, IRON, z=0.5, sd=5.0, hi=0.8, bounce=0.35,
             details=[('fn', lambda c: None)])
    cv.shape(cv.ellipse((0, -42), 16, 3.0), IRON, z=0.6, sd=0.8, hi=0.5)
    cv.shape(cv.ellipse((0, -42.3), 13, 1.8), Ink('#c4b48c', '#8c7c5c', '#f0e4c0'), z=0.65, sd=0.4, ol=0.5)
    cv.stroke([(-15, -42), (-6, -52), (6, -52), (15, -42)], 1.0, z=0.4, col=INK)
    # kazanın altına düşen ateş ışığı
    cv.fill(ik.isect(pot, cv.ellipse((0, -18), 15, 7)), (1.0, 0.5, 0.18), z=0.66, alpha=0.55, glow=(0.6, 0.22, 0.05))
    return P.done()


# ------------------------------------------------------------------ taşlar
def balbal(seed=1, gem=False):
    """Balbal: yuvarlak başlı taş heykel, sarkık bıyık, göğsünde kap tutan eller; isteğe bağlı ışıyan kut taşı."""
    P = Prop(32, 64, 16, 62)
    cv = P.cv
    rng = np.random.default_rng(seed)
    body = cv.blob([(-9, 0, 0.0), (-10, -20), (-9.5, -36), (-8, -40, 0.0), (8, -40, 0.0), (9.5, -36), (10, -20), (9, 0, 0.0)])
    det = [('ink', [(-6, -26), (-1, -24), (3, -26)], 1.0), ('ink', [(-7, -30), (-3, -29)], 0.9), ('ink', [(7, -30), (3, -29)], 0.9),
           ('shade', cv.blob([(-3, -28, 0.0), (4, -28, 0.0), (3, -22, 0.0), (-2, -22, 0.0)])),
           ('ink', [(-8, -16), (-4, -10), (-6, -2)], 0.7), ('ink', [(6, -12), (8, -4)], 0.7)]
    for _ in range(9):
        x, y = rng.uniform(-8, 8), rng.uniform(-38, -2)
        det.append(('col', cv.ellipse((x, y), rng.uniform(1.0, 2.6), rng.uniform(0.8, 1.8)), MOSS.base))
    cv.shape(body, STONE_W, z=0, sd=3.6, hi=0.6, details=det, hatch=0.4)
    head = cv.blob([(-7.5, -38), (-8, -48), (-5, -55), (0, -56.5), (5, -55), (8, -48), (7.5, -38)])
    hd = [('ink', [(-5, -48), (-2, -47)], 1.1), ('ink', [(5, -48), (2, -47)], 1.1),
          ('ink', [(-1, -46), (0, -42.5), (1.5, -42.5)], 0.9),
          ('stroke', [(-5, -40.5), (-2, -41.5), (0, -40.8), (2, -41.5), (5, -40.5), (6, -38.5)], 1.6, INK, (0.2, 0.6)),
          ('shade', cv.blob([(-6, -50, 0.0), (-1.5, -49.5), (-1.5, -47, 0.0), (-6, -46.5, 0.0)])),
          ('shade', cv.blob([(6, -50, 0.0), (1.5, -49.5), (1.5, -47, 0.0), (6, -46.5, 0.0)]))]
    cv.shape(head, STONE_W, z=0.5, sd=3.0, hi=0.6, details=hd)
    cv.shape(cv.blob([(-6, -25), (-1, -27), (4, -25.5), (5, -21), (-5, -21)]), STONE, z=0.6, sd=1.0, ol=0.7)   # eller ve kap
    cv.shape(cv.blob([(-3.5, -28.5, 0.0), (3.5, -28.5, 0.0), (3, -25, 0.0), (-3, -25, 0.0)]), STONE_W, z=0.7, sd=0.8, ol=0.7)
    if gem:
        cv.shape(cv.blob(diamond(0, -33.5, 2.6, 3.2)), TURQ, z=0.8, sd=0.6, ol=0.7, glow=(0.3, 0.95, 0.9))
        for g in ((-6, -14), (-2, -10), (3, -14), (6, -9)):
            cv.stroke([(g[0] - 1.2, g[1] - 1.5), (g[0], g[1] + 1.5), (g[0] + 1.2, g[1] - 1.5)], 0.9, z=0.8, col=KUT, glow=KUT_GLOW)
    grass_tufts(cv, -14, 14, 0, 18, 1.0, seed + 5, hmax=8)
    return P.done()


def kurgan():
    """Kurgan: dikili taş halkası, ortadaki uzun taşta ışıyan Orhun yazısı, aralarda ot ve küçük adak taşları."""
    P = Prop(124, 70, 62, 66)
    cv = P.cv
    rng = np.random.default_rng(21)
    stones = [(-52, 18, 7), (-38, 26, 8), (-22, 22, 7.5), (0, 44, 9), (20, 28, 8), (36, 22, 7.5), (50, 16, 6.5)]
    for i, (x, h, w) in enumerate(stones):
        far = i % 2 == 1
        z = -1 if far else 0.0
        lean = rng.uniform(-0.08, 0.08)
        pts = [(x - w, 0.5, 0.0), (x - w * 1.05 + lean * h * 0.5, -h * 0.6), (x - w * 0.7 + lean * h, -h), (x + w * 0.2 + lean * h, -h - w * 0.35),
               (x + w * 0.8 + lean * h, -h * 0.9), (x + w * 1.05, -h * 0.4), (x + w, 0.5, 0.0)]
        det = []
        for _ in range(4):
            yy = rng.uniform(-h * 0.8, -2)
            det.append(('ink', [(x - w * 0.6, yy), (x + rng.uniform(-2, 2), yy + rng.uniform(-2, 2)), (x + w * 0.5, yy + 1)], 0.6, (0.4, 0.6)))
        for _ in range(3):
            det.append(('col', cv.ellipse((x + rng.uniform(-w, w) * 0.7, -rng.uniform(1, h * 0.5)), rng.uniform(1, 2.6), rng.uniform(0.7, 1.6)), MOSS.base))
        mat = STONE if not far else STONE_D
        if x == 0:
            for k, yy in enumerate((-36, -29, -22, -15, -8)):
                gl = [(-2.5, yy - 2.5), (0, yy + 2.5), (2.5, yy - 2.5)] if k % 2 == 0 else [(-2, yy - 2.8), (-2, yy + 2.8), (2.2, yy)]
                det.append(('stroke', gl, 1.3, KUT, (0.1, 0.1)))
        cv.shape(cv.blob(pts), mat, z=z, sd=w * 0.55, hi=0.6, details=det, hatch=0.35)
        if x == 0:
            for k, yy in enumerate((-36, -29, -22, -15, -8)):
                gl = [(-2.5, yy - 2.5), (0, yy + 2.5), (2.5, yy - 2.5)] if k % 2 == 0 else [(-2, yy - 2.8), (-2, yy + 2.8), (2.2, yy)]
                cv.stroke(gl, 1.3, z=z + 0.1, col=KUT, glow=KUT_GLOW, taper=(0.1, 0.1))
    grass_tufts(cv, -60, 60, 0, 70, 2.0, 22, hmax=9)
    return P.done()


def seki():
    """Kapı sekisinin basamak yüzü: yontma taş bloklar, firuze çini kuşak."""
    P = Prop(36, 31, 4, 29)
    cv = P.cv
    for r, (y0, y1) in enumerate(((-28, -15), (-15, 0.5))):
        x = -4 + (0 if r == 0 else -3)
        while x < 31:
            w = 11 if r == 0 else 13
            b = cv.blob([(x + 0.4, y1, 0.0), (x + 0.4, y0 + 0.4, 0.0), (min(31, x + w) - 0.4, y0 + 0.4, 0.0), (min(31, x + w) - 0.4, y1, 0.0)])
            cv.shape(b, STONE_W, z=0.1 * r, sd=2.4, hi=0.5, ol=0.8)
            x += w
    band = cv.blob([(-4, -17, 0.0), (31, -17, 0.0), (31, -13, 0.0), (-4, -13, 0.0)])
    cv.shape(band, TURQ, z=0.5, sd=1.0, hi=0.4, details=[('col', cv.blob(diamond(x, -15, 1.4, 1.4)), FELT.base) for x in range(-1, 31, 5)])
    return P.done()


def yol(seed):
    """Taş döşeme: yassı, düzensiz taşlar (toprağa gömülü, kenarlarında ot)."""
    P = Prop(78, 14, 39, 7)
    cv = P.cv
    rng = np.random.default_rng(seed)
    x = -37.0
    while x < 36:
        w = rng.uniform(8, 14)
        h = rng.uniform(3.0, 4.8)
        y = rng.uniform(-0.6, 0.8)
        pts = [(x, y + 1.5), (x + w * 0.1, y - h * 0.6), (x + w * 0.5, y - h), (x + w * 0.9, y - h * 0.7), (x + w, y + 1.2), (x + w * 0.5, y + 2.2)]
        mat = [STONE, STONE_W, STONE_D][int(rng.integers(3))]
        cv.shape(cv.blob(pts), mat, z=0, sd=1.6, hi=0.5, ol=0.8)
        x += w + rng.uniform(1.0, 3.0)
    grass_tufts(cv, -38, 38, 3, 26, 1.0, seed + 1, hmin=1.5, hmax=4.5)
    return P.done()


def hali(main, second, seed):
    """Yere serili kilim (neredeyse yandan): saçaklı uçlar, elmas göbekler."""
    P = Prop(100, 10, 50, 7)
    cv = P.cv
    rug = cv.blob([(-46, 1, 0.0), (-45, -2.5, 0.0), (45, -2.5, 0.0), (46, 1, 0.0)])
    det = [('col', cv.blob([(-45, -2.5, 0.0), (45, -2.5, 0.0), (45, -1.8, 0.0), (-45, -1.8, 0.0)]), GOLD.base)]
    for k in range(9):
        x = -40 + k * 10
        det.append(('col', cv.blob(diamond(x, -0.5, 3.6, 1.2)), second.base))
        det.append(('col', cv.blob(diamond(x, -0.5, 1.4, 0.6)), GOLD.base))
    cv.shape(rug, main, z=0, sd=0.9, hi=0.3, details=det, ol=0.8)
    for f in (-1, 1):
        for k in range(7):
            yy = -2 + k * 0.5
            cv.stroke([(f * 46, yy), (f * 49, yy + 0.6)], 0.8, z=-0.1, col=FELT_C.base, taper=(0.1, 0.6))
    return P.done()


def hali_sergi():
    """Ozan köşesi: iki direk arasında gerili büyük kilim, önünde minderler ve alçak sehpada kopuz."""
    P = Prop(134, 98, 66, 94)
    cv = P.cv
    for x in (-58, 58):
        cv.shape(cv.capsule((x, 0), (x, -84), 1.8, 1.5), WOOD_D, z=0, sd=1.0, hi=0.4)
        cv.shape(cv.ellipse((x, -85), 2.8, 2.8), GOLD, z=0.1, sd=0.8, hi=0.4)
    cv.shape(cv.capsule((-60, -80), (60, -80), 1.6, 1.6), WOOD, z=0.05, sd=0.8, hi=0.4)
    # kilim
    sag = [(-52, -78), (0, -77), (52, -78)]
    rug = cv.blob([(-52, -78, 0.0), (52, -78, 0.0), (51, -30), (53, -24, 0.0), (-53, -24, 0.0), (-51, -30)])
    det = [('col', cv.blob([(-47, -73, 0.0), (47, -73, 0.0), (47, -29, 0.0), (-47, -29, 0.0)]), BLUE.base),
           ('col', cv.blob([(-44, -70, 0.0), (44, -70, 0.0), (44, -32, 0.0), (-44, -32, 0.0)]), RED.base)]
    for k, x in enumerate((-26, 0, 26)):
        det.append(('col', cv.blob(diamond(x, -51, 11, 16)), GOLD.base))
        det.append(('col', cv.blob(diamond(x, -51, 8, 12)), BLUE.base))
        det.append(('col', cv.blob(diamond(x, -51, 4.5, 6.8)), RED.base))
        det.append(('col', cv.blob(diamond(x, -51, 1.8, 2.6)), FELT.base))
        for f in (-1, 1):
            det.append(('stroke', ram_horn_wave(x + f * 6, -64, 2.0), 1.0, GOLD.base, (0.2, 0.4)))
    for x in np.arange(-46, 47, 4.6):
        det.append(('col', cv.blob(diamond(x, -75.5, 1.6, 1.4)), GOLD.base))
        det.append(('col', cv.blob(diamond(x, -26.5, 1.6, 1.4)), GOLD.base))
    det += cv.fold([(-30, -77), (-31, -50), (-29, -25)], depth=2.0, w=1.0)
    det += cv.fold([(14, -77), (15, -52), (13, -25)], depth=2.2, w=1.0)
    det += cv.fold([(40, -77), (41, -55), (40, -25)], depth=1.6, w=0.8)
    cv.shape(rug, RED, z=0.2, sd=8.0, hi=0.6, details=det)
    for k in range(26):
        x = -50 + k * 4
        cv.stroke([(x, -24), (x + 0.5, -20)], 0.9, z=0.25, col=FELT_C.base, taper=(0.1, 0.7))
    # minderler
    for x, m in ((-36, BLUE), (-12, RED), (14, TURQ), (36, Ink('#c08a3a'))):
        cv.shape(cv.blob([(x - 12, 0.5, 0.0), (x - 13, -4), (x - 9, -8.5), (x, -9.5), (x + 9, -8.5), (x + 13, -4), (x + 12, 0.5, 0.0)]), m, z=1.0,
                 sd=3.0, hi=0.8, details=[('ink', [(x - 6, -6), (x, -5), (x + 6, -6)], 0.7), ('col', cv.ellipse((x, -5), 1.6, 1.2), GOLD.base)])
    # alçak sehpa ve kopuz
    cv.shape(cv.blob([(46, 0, 0.0), (46, -10, 0.0), (62, -10, 0.0), (62, 0, 0.0)]), WOOD_R, z=1.1, sd=1.6, hi=0.4)
    body = cv.blob([(48, -11), (50, -18), (55, -21), (60, -18), (61, -11), (55, -9.5)])
    cv.shape(body, WOOD, z=1.3, sd=2.6, hi=0.6, details=[('col', cv.ellipse((55, -15.5), 2.2, 2.0), WOOD_D.shadow)])
    cv.shape(ik.taper_path([cv.W((55, -20)), cv.W((52, -36)), cv.W((49, -46))], cv.u(1.8), (0.05, 0.1)), WOOD_D, z=1.25, sd=0.6, hi=0.2)
    cv.stroke([(54, -12), (50, -44)], 0.6, z=1.4, col=FELT.hi, alpha=0.8)
    cv.stroke([(56, -12), (51, -44)], 0.6, z=1.4, col=FELT.hi, alpha=0.8)
    return P.done()


# ------------------------------------------------------------------ büyük yapılar
def kapi():
    """Taç kapı: firuze çini kuşaklı iki sütun, tepelerinde ateş tasları; kemerde ışıyan Orhun runları,
    kilit taşında koçboynuzu, en tepede ışınlı altın güneş kursu (Kün Ana)."""
    P = Prop(176, 182, 88, 178)
    cv = P.cv
    for f in (-1, 1):
        x = f * 62
        # kaide
        cv.shape(cv.blob([(x - 13, 0.5, 0.0), (x - 13, -9, 0.0), (x - 10, -12, 0.0), (x + 10, -12, 0.0), (x + 13, -9, 0.0), (x + 13, 0.5, 0.0)]), STONE_W,
                 z=0, sd=3.0, hi=0.6, details=[('ink', [(x - 13, -6), (x + 13, -6)], 0.8)])
        col = cv.blob([(x - 9, -11, 0.0), (x - 9, -112, 0.0), (x + 9, -112, 0.0), (x + 9, -11, 0.0)])
        det = []
        for yy in np.arange(-108, -14, 12):
            det.append(('ink', [(x - 9, yy), (x + 9, yy)], 0.6))
        det.append(('col', cv.blob([(x - 5.5, -100, 0.0), (x + 5.5, -100, 0.0), (x + 5.5, -22, 0.0), (x - 5.5, -22, 0.0)]), TURQ.base))
        for yy in np.arange(-96, -24, 8):
            det.append(('col', cv.blob(diamond(x, yy, 3.6, 3.6)), BLUE.base))
            det.append(('col', cv.blob(diamond(x, yy, 1.5, 1.5)), FELT.base))
        det.append(('shade', cv.blob([(x + 3.5, -112, 0.0), (x + 9.5, -112, 0.0), (x + 9.5, -11, 0.0), (x + 3.5, -11, 0.0)])))
        cv.shape(col, STONE_W, z=0.2, noshadow=True, hi=0.6, details=det)
        # başlık (altın)
        cap = cv.blob([(x - 13, -112, 0.0), (x + 13, -112, 0.0), (x + 11, -118, 0.0), (x + 14, -122, 0.0), (x - 14, -122, 0.0), (x - 11, -118, 0.0)])
        cv.shape(cap, GOLD, z=0.4, sd=2.0, hi=0.5)
        # ateş tası
        bowl = cv.blob([(x - 9, -128, 0.0), (x + 9, -128, 0.0), (x + 6, -123), (x, -122), (x - 6, -123)])
        cv.shape(bowl, BRONZE, z=0.45, sd=1.8, hi=0.4)
        flame(cv, x, -128, 20, 14, 0.5, seed=40 + f)
    # kemer: iki kat taş, iç kenarda runlar
    def arch(r_out, r_in, y0):
        outer = [(-r_out, y0, 0.0)] + [(math.cos(a) * r_out, y0 + math.sin(a) * r_out * 0.62) for a in np.linspace(math.pi * 1.02, math.pi * 1.98, 12)] + [(r_out, y0, 0.0)]
        inner = [(r_in, y0, 0.0)] + [(math.cos(a) * r_in, y0 + math.sin(a) * r_in * 0.62) for a in np.linspace(math.pi * 1.98, math.pi * 1.02, 12)] + [(-r_in, y0, 0.0)]
        return cv.blob(outer + inner)
    a_out = arch(74, 52, -112)
    det = []
    for k in range(11):
        a = math.pi + (k + 0.5) * math.pi / 11
        p0 = (math.cos(a) * 52, -112 + math.sin(a) * 52 * 0.62)
        p1 = (math.cos(a) * 74, -112 + math.sin(a) * 74 * 0.62)
        det.append(('ink', [p0, p1], 0.8))
    det.append(('shade', ik.diff(a_out, ik.moved(a_out, cv.u(-8), cv.u(-4)))))
    cv.shape(a_out, STONE_W, z=0.3, noshadow=True, hi=0.6, details=det)
    band = arch(66, 58, -112)
    cv.shape(band, TURQ, z=0.35, noshadow=True, hi=0.2, ol=0.6)
    for k in range(9):
        a = math.pi + (k + 0.5) * math.pi / 9
        cx, cy = math.cos(a) * 62, -112 + math.sin(a) * 62 * 0.62
        ang = a + math.pi / 2
        gl = [(cx - math.cos(ang) * 2.2, cy - math.sin(ang) * 2.2), (cx + math.cos(a) * 1.8, cy + math.sin(a) * 1.8), (cx + math.cos(ang) * 2.2, cy + math.sin(ang) * 2.2)]
        cv.stroke(gl, 1.4, z=0.4, col=KUT, glow=KUT_GLOW, taper=(0.1, 0.1))
    # kilit taşı + koçboynuzu + güneş kursu
    key = cv.blob([(-9, -150, 0.0), (9, -150, 0.0), (7, -160, 0.0), (-7, -160, 0.0)])
    cv.shape(key, STONE_W, z=0.5, sd=2.0, hi=0.4)
    for f in (-1, 1):
        horn = ik.taper_path([cv.W(p) for p in [(0, -156)] + [(q[0], q[1]) for q in ram_horn_pts(f * 14, -162, 9, f)]], cv.u(4.0),
                             prof=lambda u: max(0.25, 1.0 - u * 0.75))
        cv.shape(horn, GOLD, z=0.6, sd=1.6, hi=0.5)
    for k in range(12):
        a = k * math.pi / 6
        ray = cv.blob([(math.cos(a - 0.12) * 9, -168 + math.sin(a - 0.12) * 9), (math.cos(a) * 16, -168 + math.sin(a) * 16, 0.0),
                       (math.cos(a + 0.12) * 9, -168 + math.sin(a + 0.12) * 9)])
        cv.fill(ray, GOLD.base, z=0.62, glow=(0.8, 0.5, 0.12))
    cv.shape(cv.ellipse((0, -168), 8.5, 8.5), GOLD, z=0.65, sd=2.0, hi=0.6, glow=(0.7, 0.42, 0.1))
    cv.shape(cv.ellipse((0, -168), 4.5, 4.5), Ink('#ffe6a0', '#d0902a', '#ffffff'), z=0.7, sd=1.0, ol=0.6, glow=(1.0, 0.8, 0.4))
    # sütunlara sarılı bayrak bağları
    for f in (-1, 1):
        x = f * 62
        cv.shape(cv.blob([(x - f * 9, -104, 0.0), (x - f * 18, -100), (x - f * 16, -84, 0.0), (x - f * 12, -92), (x - f * 9, -96, 0.0)]), RED, z=0.5, sd=1.4, hi=0.3)
    grass_tufts(cv, -80, 80, 0, 50, 2.0, 41, hmax=8)
    return P.done()


def ram_horn_pts(cx, cy, s, f):
    pts = []
    for i in range(16):
        t = i / 15
        a = math.pi / 2 + f * (t * 1.6 * math.pi)
        r = s * (1 - 0.7 * t)
        pts.append((cx + math.cos(a) * r * f * -1 + 0 * f, cy + math.sin(a) * r))
    return pts


def sunak():
    """Umay sunağı: taş seki üstünde işlemeli ak örtü, süt kâseleri, mumlar; arkada kanatlı kuş başlıklı taş Umay
    heykeli, göğsünde ışıyan kut taşı, iki yanında çaputlu ağaç dalları."""
    P = Prop(90, 106, 45, 102)
    cv = P.cv
    # heykel (arkada)
    for f in (-1, 1):
        wing = cv.blob([(f * 6, -70), (f * 14, -82), (f * 24, -90), (f * 32, -94, 0.0), (f * 31, -86), (f * 28, -80, 0.0), (f * 30, -74),
                        (f * 26, -68, 0.0), (f * 27, -62), (f * 22, -56, 0.0), (f * 20, -50), (f * 12, -46, 0.0), (f * 8, -54)])
        wd = [('ink', [(f * 12, -72), (f * 20, -80), (f * 28, -86)], 0.8), ('ink', [(f * 12, -64), (f * 20, -70), (f * 27, -74)], 0.8),
              ('ink', [(f * 11, -56), (f * 17, -60), (f * 23, -62)], 0.8)]
        cv.shape(wing, STONE_W, z=-1.0, sd=4.0, hi=0.5, details=wd, hatch=0.3)
    body = cv.blob([(-9, -34, 0.0), (-11, -50), (-8, -64), (-4, -70), (4, -70), (8, -64), (11, -50), (9, -34, 0.0)])
    det = cv.fold([(-3, -64), (-4, -50), (-5, -36)], depth=1.2, w=0.8) + cv.fold([(4, -62), (5, -48), (6, -36)], depth=1.2, w=0.8)
    det.append(('ink', [(-6, -54), (0, -52), (6, -54)], 0.8))
    cv.shape(body, STONE_W, z=-0.8, sd=4.0, hi=0.6, details=det)
    head = cv.blob([(-5, -70), (-5.5, -77), (0, -80.5), (5.5, -77), (5, -70), (0, -68.5)])
    cv.shape(head, STONE_W, z=-0.7, sd=2.6, hi=0.5,
             details=[('ink', [(-3, -75.5), (-1, -75)], 0.9), ('ink', [(3, -75.5), (1, -75)], 0.9), ('ink', [(-1.2, -71.5), (1.2, -71.5)], 0.7)])
    # kuş başlık (kuğu)
    crown = cv.blob([(-6.5, -78, 0.0), (-6, -84), (0, -86.5), (6, -84), (6.5, -78, 0.0)])
    cv.shape(crown, STONE_W, z=-0.6, sd=2.0, hi=0.4, details=[('ink', [(-6, -80.5), (6, -80.5)], 0.7)])
    bird = cv.blob([(-5, -86), (-2, -92), (2, -97), (5, -100), (8, -99), (6.5, -96.5), (4, -92), (6, -88), (2, -86)])
    cv.shape(bird, STONE_W, z=-0.55, sd=1.6, hi=0.3, details=[('ink', [(5.5, -98.5), (9.5, -98.6)], 0.9), ('ink', [(-3, -89), (3, -88)], 0.6)])
    cv.shape(cv.blob(diamond(0, -60, 3.0, 3.8)), TURQ, z=-0.5, sd=0.8, ol=0.7, glow=(0.3, 0.95, 0.9))
    # sunak sekisi
    cv.shape(cv.blob([(-34, 0.5, 0.0), (-34, -10, 0.0), (34, -10, 0.0), (34, 0.5, 0.0)]), STONE, z=0, sd=4.0, hi=0.5,
             details=[('ink', [(-34, -5), (34, -5)], 0.7)] + [('ink', [(x, -10), (x, -5)], 0.6) for x in (-20, 0, 18)])
    table = cv.blob([(-30, -10, 0.0), (-30, -34, 0.0), (30, -34, 0.0), (30, -10, 0.0)])
    cv.shape(table, STONE_W, z=0.2, sd=4.0, hi=0.5)
    cloth = cv.blob([(-31, -34, 0.0), (31, -34, 0.0), (32, -30), (30, -19, 0.0), (20, -21), (10, -18, 0.0), (0, -21), (-10, -18, 0.0), (-20, -21), (-30, -19, 0.0), (-32, -30)])
    det = [('col', cv.blob([(-31, -24, 0.0), (31, -24, 0.0), (31, -22, 0.0), (-31, -22, 0.0)]), RED.base)]
    for x in range(-24, 25, 8):
        det.append(('col', cv.blob(diamond(x, -28.5, 2.6, 2.6)), RED.base))
        det.append(('stroke', [(x - 2, -20.5), (x, -18.6), (x + 2, -20.5)], 0.8, RED.shadow, (0.1, 0.1)))
    det += cv.fold([(-15, -33), (-16, -22)], depth=1.4, w=0.7) + cv.fold([(16, -33), (15, -22)], depth=1.4, w=0.7)
    cv.shape(cloth, FELT, z=0.4, sd=4.0, hi=0.6, details=det)
    # kâseler ve mumlar
    for x in (-18, 8):
        cv.shape(cv.blob([(x - 5.5, -38, 0.0), (x + 5.5, -38, 0.0), (x + 3.5, -34.5), (x - 3.5, -34.5)]), Ink('#a46c40', '#5a3424', '#d8a070'), z=0.6, sd=1.2, hi=0.4)
        cv.shape(cv.ellipse((x, -38), 5.2, 1.2), FELT, z=0.65, sd=0.4, ol=0.6)
    for x in (-25, -4, 23):
        cv.shape(cv.blob([(x - 1.6, -34, 0.0), (x - 1.6, -42, 0.0), (x + 1.6, -42, 0.0), (x + 1.6, -34, 0.0)]), FELT_C, z=0.7, sd=0.8, ol=0.6)
        flame(cv, x, -42, 6, 3.6, 0.75, seed=60 + x)
    cv.shape(cv.blob([(14, -34, 0.0), (15, -38), (20, -40), (21, -34, 0.0)]), Ink('#7aa65a'), z=0.7, sd=0.8, ol=0.7)
    return P.done()


def pinar():
    """Kutsal pınar: yosunlu kaya yığını, aradan dökülen ışıyan çağlayan, taş halkalı havuz, eğrelti ve çaputlar."""
    P = Prop(134, 122, 66, 118)
    cv = P.cv
    rng = np.random.default_rng(71)
    rocks = [(-34, -58, 26, 34), (8, -78, 30, 34), (34, -46, 24, 30), (-12, -30, 30, 22), (40, -18, 18, 16), (-42, -18, 20, 16)]
    for i, (x, y, rx, ry) in enumerate(rocks):
        pts = [(x + math.cos(a) * rx * rng.uniform(0.85, 1.1), y + math.sin(a) * ry * rng.uniform(0.85, 1.1)) for a in np.linspace(0, 2 * math.pi, 11)[:-1]]
        det = []
        for _ in range(5):
            a = rng.uniform(math.pi * 1.05, math.pi * 1.7)
            q = (x + math.cos(a) * rx * 0.75, y + math.sin(a) * ry * 0.75)
            det.append(('col', cv.ellipse(q, rng.uniform(3, 7), rng.uniform(1.6, 3)), MOSS.base))
            det.append(('col', cv.ellipse((q[0] - 1, q[1] - 0.8), rng.uniform(1.5, 3), rng.uniform(0.6, 1.2)), MOSS.hi))
        for _ in range(3):
            q0 = (x + rng.uniform(-rx, rx) * 0.5, y + rng.uniform(-ry, ry) * 0.4)
            det.append(('ink', [q0, (q0[0] + rng.uniform(-6, 6), q0[1] + rng.uniform(4, 9))], 0.7, (0.3, 0.8)))
        cv.shape(cv.blob(pts), STONE if i % 2 == 0 else STONE_D, z=0.1 * i, sd=min(rx, ry) * 0.55, hi=0.8, details=det, hatch=0.35, bounce=0.3)
    # çağlayan: üst kayanın yarığından akan şerit (ışır)
    fall = [(4, -96), (-1, -84), (-6, -66), (-4, -48), (0, -30), (1, -12)]
    for q in ((-6, -66), (-4, -47), (0, -14)):
        for k in range(5):
            ang = math.pi * (1.1 + 0.2 * k)
            cv.stroke([(q[0] + math.cos(ang) * 3, q[1] + math.sin(ang) * 1.5), (q[0] + math.cos(ang) * 8, q[1] + math.sin(ang) * 4 + 2)], 1.4, z=1.15,
                      col=(0.9, 1.0, 1.0), taper=(0.2, 0.9), glow=(0.3, 0.75, 0.75))
    cv.shape(ik.taper_path([cv.W(p) for p in fall], cv.u(11.0), prof=lambda u: 0.5 + 0.5 * u), Ink('#7ee0dc', '#2e8a96', '#e8ffff'), z=1.0,
             sd=2.0, hi=0.0, ol=0.7, glow=(0.18, 0.6, 0.62))
    for dx in (-2.5, 0.5, 3):
        cv.stroke([(fall[0][0] + dx * 0.4, -92), (dx * 0.6 - 1, -60), (dx, -20)], 0.9, z=1.1, col=(0.92, 1.0, 1.0), taper=(0.3, 0.3), glow=(0.3, 0.7, 0.7))
    # havuz
    rim = cv.blob([(-30, 0.5, 0.0), (-31, -6), (-20, -12), (20, -12), (31, -6), (30, 0.5, 0.0)])
    cv.shape(rim, STONE_W, z=1.2, sd=3.0, hi=0.5, details=[('ink', [(x, -11), (x + 1, 0)], 0.6) for x in (-20, -8, 6, 18)])
    water = cv.blob([(-24, -8, 0.0), (-16, -11.5), (16, -11.5), (24, -8, 0.0), (16, -6.5), (-16, -6.5)])
    cv.shape(water, Ink('#3fb0b4', '#1c5a70', '#a8f4f0'), z=1.3, sd=1.0, hi=0.4, ol=0.6, glow=(0.12, 0.42, 0.46))
    for q in ((-6, -9), (4, -10), (10, -8)):
        cv.stroke([(q[0] - 3, q[1]), (q[0] + 3, q[1])], 0.8, z=1.35, col=(0.9, 1.0, 1.0), glow=(0.3, 0.7, 0.7))
    # eğrelti ve ot
    for x0, s in ((-52, 1.0), (50, 0.9), (-26, 0.7)):
        for k in range(5):
            a = math.radians(-90 + (k - 2) * 28)
            ln = 16 * s * (1 - abs(k - 2) * 0.12)
            tip = (x0 + math.cos(a) * ln, math.sin(a) * ln)
            pts = [(x0, 0), ((x0 + tip[0]) / 2 + math.cos(a) * 1.5, tip[1] * 0.55), tip]
            cv.stroke(pts, 2.0, z=2.0, col=LEAF.base, taper=(0.05, 0.8))
            for j in range(1, 6):
                t = j / 6
                q = (x0 + (tip[0] - x0) * t, tip[1] * t)
                for sg in (-1, 1):
                    cv.stroke([q, (q[0] + math.cos(a + sg * 1.1) * 4 * (1 - t * 0.6), q[1] + math.sin(a + sg * 1.1) * 4 * (1 - t * 0.6))], 1.6, z=2.0,
                              col=LEAF.hi if sg < 0 else LEAF.shadow, taper=(0.1, 0.9))
    grass_tufts(cv, -62, 62, 0, 50, 2.1, 72, hmax=9)
    return P.done()


def _foliage_clump(cv, cx, cy, r, mat, z, seed, kut=0.0):
    """Çizgi roman yaprak öbeği: tırtıklı kenarlı kütle (cel gölgeli), kenarda tek tek yaprak uçları, içte yaprak işaretleri;
    kut > 0 ise ışıyan turkuaz yapraklar."""
    rng = np.random.default_rng(seed)
    pts = []
    n = 22
    for i in range(n):
        a = i * 2 * math.pi / n
        rr = r * (1.0 + 0.14 * math.sin(a * 3 + seed) + rng.uniform(-0.05, 0.05))
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.72))
        a2 = a + math.pi / n
        rr2 = rr * 0.93
        pts.append((cx + math.cos(a2) * rr2, cy + math.sin(a2) * rr2 * 0.72, 0.0))
    det = []
    for _ in range(int(r * 0.9)):
        a = rng.uniform(0, 2 * math.pi)
        d = r * math.sqrt(rng.random()) * 0.85
        q = (cx + math.cos(a) * d, cy + math.sin(a) * d * 0.72)
        ang = math.pi / 2 + rng.uniform(-0.9, 0.9)
        ln = rng.uniform(2.5, 5)
        col = mat.hi if (q[1] < cy - r * 0.15 and q[0] < cx + r * 0.2) else mat.shadow
        det.append(('stroke', [q, (q[0] + math.cos(ang) * ln * 0.5 + 0.6, q[1] + math.sin(ang) * ln * 0.5), (q[0] + math.cos(ang) * ln, q[1] + math.sin(ang) * ln)],
                    1.6, col, (0.2, 0.9)))
        if rng.random() < 0.25:
            det.append(('ink', [q, (q[0] + math.cos(ang) * ln, q[1] + math.sin(ang) * ln)], 0.6, (0.2, 0.9)))
    cv.shape(cv.blob(pts), mat, z=z, sd=r * 0.42, hi=r * 0.06, details=det, hatch=0.3, bounce=0.25)
    if kut > 0:
        for _ in range(int(r * kut)):
            a = rng.uniform(0, 2 * math.pi)
            d = r * math.sqrt(rng.random()) * 0.95
            q = (cx + math.cos(a) * d, cy + math.sin(a) * d * 0.72)
            ang = math.pi / 2 + rng.uniform(-1.0, 1.0)
            ln = rng.uniform(2.4, 4.0)
            cv.stroke([q, (q[0] + math.cos(ang) * ln, q[1] + math.sin(ang) * ln)], 1.8, z=z + 0.05, col=(0.6, 1.0, 0.94), taper=(0.2, 0.9),
                      glow=(0.25, 0.85, 0.8))


def kayin():
    """Umay'ın dilek kayını: ak kabuklu yaşlı kayın, alçak dallarda renk renk çaputlar, gövdeye sarılı kızıl-ak bez,
    tepede ışıyan kut yaprakları."""
    P = Prop(204, 240, 100, 236)
    cv = P.cv
    rng = np.random.default_rng(81)
    # gövde: tabanda geniş kök boğazı, hafif S kıvrımı
    L = [(-9, 0, 0.0), (-13, 1.5, 0.0), (-8, -8), (-6.5, -40), (-7, -80), (-4, -120), (-5, -150), (-1, -176), (3, -176), (4, -150), (6, -120),
         (6.5, -80), (6, -40), (8, -8), (14, 1.5, 0.0), (9, 0, 0.0)]
    det = []
    for _ in range(40):
        y = rng.uniform(-170, -6)
        hw = 6.5 - (-y) * 0.012
        x0 = rng.uniform(-hw * 0.8, hw * 0.5)
        ln = rng.uniform(1.5, 4.5)
        det.append(('ink', [(x0, y), (x0 + ln * 0.5, y + rng.uniform(-0.4, 0.4)), (x0 + ln, y)], rng.uniform(1.0, 2.2), (0.4, 0.4)))
    for _ in range(4):
        y = rng.uniform(-150, -40)
        det.append(('col', cv.blob([(-3, y), (0, y - 2), (3, y), (0, y + 1.5)]), INK))
    det.append(('deep', cv.blob([(-13, 1.5, 0.0), (-8, -8), (-6.5, -14), (6, -14), (8, -8), (14, 1.5, 0.0)])))
    trunk = cv.blob(L)
    # dallar
    branches = [((-4, -112), (-40, -150), (-70, -158)), ((4, -120), (40, -152), (76, -160)), ((-3, -150), (-26, -184), (-48, -200)),
                ((3, -156), (26, -188), (46, -206)), ((-5, -86), (-30, -100), (-52, -104)), ((5, -92), (30, -108), (58, -112))]
    bp = [ik.taper_path([cv.W(a), cv.W(b), cv.W(c)], cv.u(5.5), prof=lambda u: max(0.18, 1.0 - u * 0.85)) for a, b, c in branches]
    cv.shape(ik.union(trunk, *bp), BARK_W, z=0, sd=7.0, hi=1.2, details=det, bounce=0.3)
    # kızıl-ak bez sarılı
    for k, yy in enumerate((-46, -40, -34)):
        m = RED if k % 2 == 0 else FELT
        cv.shape(cv.blob([(-7.6, yy, 0.0), (7.6, yy - 1.2, 0.0), (7.6, yy + 4, 0.0), (-7.6, yy + 5.2, 0.0)]), m, z=0.5, sd=2.4, ol=0.7)
    cv.shape(cv.blob([(5, -40), (9, -36), (11, -24, 0.0), (8, -28), (6, -22, 0.0), (5, -34)]), RED, z=0.45, sd=1.2, ol=0.7)
    # yaprak öbekleri (arkadakiler koyu)
    clumps = [(-58, -168, 30, -1), (60, -172, 32, -1), (0, -206, 40, -1), (-36, -206, 28, 1), (36, -212, 30, 1), (-74, -150, 22, 1),
              (78, -154, 22, 1), (-14, -184, 28, 1), (20, -186, 26, 1), (-48, -106, 16, 1), (56, -114, 16, 1)]
    for i, (x, y, r, layer) in enumerate(clumps):
        mat = LEAF.darker(0.72) if layer < 0 else LEAF
        _foliage_clump(cv, x, y, r, mat, z=(-1 if layer < 0 else 1.0 + i * 0.01), seed=90 + i, kut=0.0 if layer < 0 else 0.35)
    # çaputlar: alçak dallardan sarkan şeritler
    for (a, b, c) in branches[4:] + branches[:2]:
        for t in (0.35, 0.6, 0.85):
            q = (a[0] + (c[0] - a[0]) * t, a[1] + (c[1] - a[1]) * t + 4 * math.sin(t * math.pi))
            col = CLOTH_COLS[int(rng.integers(len(CLOTH_COLS)))]
            ln = rng.uniform(16, 30)
            sw = rng.uniform(-5, 6)
            wv = rng.uniform(1.5, 3.0)
            cl = []
            for j in range(7):
                t = j / 6
                cl.append((q[0] + sw * t + math.sin(t * 5 + q[0]) * wv * t, q[1] + ln * t))
            w0 = rng.uniform(2.6, 3.6)
            left = [(x - w0 * (0.55 + 0.25 * j / 6), y) for j, (x, y) in enumerate(cl)]
            right = [(x + w0 * (0.45 + 0.2 * j / 6), y + 0.6) for j, (x, y) in enumerate(cl)]
            tipc = (cl[-1][0] + 0.3, cl[-1][1] - 2.0)
            strip = cv.blob([left[0] + (0.0,)] + left[1:] + [(left[-1][0], left[-1][1] + 1.0, 0.0), tipc + (0.0,), (right[-1][0], right[-1][1] + 1.0, 0.0)] + right[::-1][1:-1] + [right[0] + (0.0,)])
            cv.shape(strip, Ink(col), z=2.0, sd=1.2, hi=0.3, ol=0.7, details=[('ink', [cl[1], cl[3], cl[5]], 0.6, (0.3, 0.6))])
            cv.shape(cv.ellipse(q, 1.6, 1.4), Ink(col).darker(0.8), z=2.05, sd=0.4, ol=0.5)
    # kökler ve ot
    for f in (-1, 1):
        cv.shape(ik.taper_path([cv.W((f * 6, -4)), cv.W((f * 16, -1)), cv.W((f * 26, 1))], cv.u(4.0), (0.0, 0.9)), BARK_W, z=0.2, sd=1.4, ol=0.8)
    grass_tufts(cv, -40, 40, 0, 40, 3.0, 83, hmax=9)
    return P.done(rim=0.45)


def demirhane():
    """Demirci ocağı: taş körük ocağı (ağzı kor gibi), baca, iki direkli ahşap saçak, asılı maşa ve çekiçler,
    silah sehpası, deri körük, su fıçısı."""
    P = Prop(164, 128, 80, 124)
    cv = P.cv
    # saçak direkleri ve çatısı (arkada)
    for x in (-70, 62):
        cv.shape(cv.capsule((x, 0), (x, -92), 2.2, 2.0), WOOD_D, z=-1.0, sd=1.2, hi=0.4)
    roof = cv.blob([(-80, -90, 0.0), (74, -98, 0.0), (76, -92, 0.0), (-78, -84, 0.0)])
    det = [('ink', [(x, -91 - (x + 80) * 0.05), (x + 2, -85 - (x + 80) * 0.05)], 0.7) for x in range(-74, 74, 7)]
    cv.shape(roof, WOOD, z=-0.9, sd=3.0, hi=0.6, details=det)
    for x in range(-76, 74, 9):
        cv.shape(cv.blob([(x, -86 - (x + 80) * 0.05), (x + 9, -86.5 - (x + 89) * 0.05), (x + 8, -80 - (x + 88) * 0.05, 0.0), (x + 1, -79.5 - (x + 81) * 0.05, 0.0)]),
                 RED_D if (x // 9) % 2 == 0 else WOOD_R, z=-0.85, sd=1.2, ol=0.6)
    # asılı aletler
    for x, kind in ((-56, 'masa'), (-46, 'cekic'), (-36, 'cekic'), (40, 'masa'), (50, 'cekic')):
        y0 = -85 - (x + 80) * 0.05
        cv.stroke([(x, y0), (x, y0 + 8)], 0.9, z=-0.8, col=INK)
        if kind == 'cekic':
            cv.shape(cv.capsule((x, y0 + 8), (x, y0 + 22), 0.9, 0.9), WOOD, z=-0.75, sd=0.4, ol=0.6)
            cv.shape(cv.blob([(x - 4, y0 + 20, 0.0), (x + 4, y0 + 20, 0.0), (x + 4, y0 + 24.5, 0.0), (x - 4, y0 + 24.5, 0.0)]), IRON, z=-0.7, sd=0.8, hi=0.3)
        else:
            for f in (-1, 1):
                cv.stroke([(x, y0 + 8), (x + f * 2, y0 + 18), (x + f * 0.6, y0 + 26)], 1.4, z=-0.75, col=IRON.base, taper=(0.1, 0.2))
    # silah sehpası (sağ)
    cv.shape(cv.blob([(52, 0.5, 0.0), (52, -6, 0.0), (76, -6, 0.0), (76, 0.5, 0.0)]), WOOD_D, z=-0.5, sd=1.2, ol=0.7)
    for i, x in enumerate((56, 62, 68, 73)):
        top = -60 + i * 6
        if i % 2 == 0:
            cv.shape(cv.blob([(x - 1.4, -6, 0.0), (x - 1.6, top + 6), (x, top, 0.0), (x + 1.6, top + 6), (x + 1.4, -6, 0.0)]), STEEL, z=-0.45 + i * 0.01, sd=0.8, hi=0.3)
            cv.shape(cv.capsule((x - 4, -18), (x + 4, -18), 1.1, 1.1), GOLD, z=-0.44 + i * 0.01, sd=0.4, ol=0.6)
        else:
            cv.shape(cv.capsule((x, -6), (x, top), 0.9, 0.8), WOOD, z=-0.45 + i * 0.01, sd=0.4, ol=0.6)
            cv.shape(cv.blob([(x - 2.2, top + 2, 0.0), (x, top - 7, 0.0), (x + 2.2, top + 2, 0.0)]), STEEL, z=-0.44 + i * 0.01, sd=0.6, ol=0.6)
    cv.shape(cv.capsule((52, -40), (76, -40), 1.2, 1.2), WOOD_D, z=-0.3, sd=0.6, ol=0.7)
    # ocak: taş kubbe + baca
    chim = cv.blob([(-16, -50, 0.0), (-14, -112, 0.0), (2, -112, 0.0), (4, -50, 0.0)])
    det = []
    for yy in np.arange(-108, -50, 7):
        det.append(('ink', [(-15, yy), (3, yy)], 0.6))
        off = 0 if int(yy) % 2 == 0 else 4
        for xx in (-10 + off, -2 + off):
            det.append(('ink', [(xx, yy), (xx, yy + 7)], 0.5))
    cv.shape(chim, STONE, z=0, sd=5.0, hi=0.5, details=det)
    cv.shape(cv.blob([(-17, -112, 0.0), (5, -112, 0.0), (4, -116, 0.0), (-16, -116, 0.0)]), STONE_D, z=0.05, sd=1.0, ol=0.7)
    dome = cv.blob([(-34, 0.5, 0.0), (-34, -18), (-26, -40), (-6, -52), (14, -46), (24, -28), (26, 0.5, 0.0)])
    det = []
    rng = np.random.default_rng(91)
    for _ in range(26):
        a = rng.uniform(math.pi * 1.0, math.pi * 2.0)
        rr = rng.uniform(0.3, 0.95)
        cx_, cy_ = -4 + math.cos(a) * 28 * rr, math.sin(a) * 48 * rr
        det.append(('ink', [(cx_ - 3, cy_), (cx_, cy_ - 1.2), (cx_ + 3, cy_)], 0.6, (0.3, 0.3)))
    cv.shape(dome, STONE, z=0.2, sd=9.0, hi=0.8, details=det, hatch=0.35)
    mouth = cv.blob([(-16, 0.5, 0.0), (-16, -12), (-4, -22), (8, -12), (8, 0.5, 0.0)])
    cv.shape(mouth, Ink('#ff9a3a', '#c4421c', '#fff0b0'), z=0.4, noshadow=True, ol=0.9, glow=(1.0, 0.45, 0.12),
             details=[('col', cv.blob([(-12, 0.5, 0.0), (-12, -8), (-4, -15), (4, -8), (4, 0.5, 0.0)]), (1.0, 0.86, 0.5))])
    for k in range(5):
        cv.fill(cv.ellipse((-12 + k * 4, -1.5), 2.2, 1.4), (1.0, 0.95, 0.75), z=0.45, glow=(1.0, 0.75, 0.35))
    cv.shape(cv.blob([(-18, -14, 0.0), (-4, -24), (10, -14, 0.0), (8, -12), (-4, -21), (-16, -12)]), STONE_W, z=0.42, sd=1.2, ol=0.8)
    # körük (deri) ve fıçı (sol)
    bel = cv.blob([(-62, -6), (-52, -14), (-38, -12), (-34, -8), (-38, -4), (-52, -2)])
    cv.shape(bel, LEATHER, z=0.6, sd=3.0, hi=0.5, details=cv.fold([(-56, -11), (-50, -8), (-56, -4)], depth=1.0, w=0.8))
    cv.shape(cv.capsule((-36, -8), (-30, -9), 1.4, 1.0), BRONZE, z=0.65, sd=0.5, ol=0.7)
    cv.shape(cv.capsule((-64, -8), (-74, -16), 1.0, 1.0), WOOD, z=0.55, sd=0.4, ol=0.6)
    barrel = cv.blob([(-80, 0.5, 0.0), (-81, -10), (-80, -22, 0.0), (-64, -22, 0.0), (-63, -10), (-64, 0.5, 0.0)])
    cv.shape(barrel, WOOD, z=0.7, sd=4.0, hi=0.6,
             details=[('col', cv.blob([(-81, -17, 0.0), (-63, -17, 0.0), (-63, -15, 0.0), (-81, -15, 0.0)]), IRON.base),
                      ('col', cv.blob([(-81, -6, 0.0), (-63, -6, 0.0), (-63, -4, 0.0), (-81, -4, 0.0)]), IRON.base)] +
                     [('ink', [(x, -21), (x, 0)], 0.6) for x in (-76, -72, -68)])
    cv.shape(cv.ellipse((-72, -22), 8, 1.6), Ink('#2c5a6c', '#163040', '#7ab0c4'), z=0.75, sd=0.4, ol=0.6)
    grass_tufts(cv, -80, 80, 0, 40, 2.0, 92, hmax=7)
    return P.done()


def ors():
    """Kütük üstünde örs, üstünde kızgın kılıç, yanına dayalı çekiç."""
    P = Prop(52, 42, 24, 40)
    cv = P.cv
    stump = cv.blob([(-11, 0.5, 0.0), (-12, 1.2, 0.0), (-10, -6), (-9, -17, 0.0), (9, -17, 0.0), (10, -6), (12, 1.2, 0.0), (11, 0.5, 0.0)])
    cv.shape(stump, WOOD, z=0, sd=4.0, hi=0.6, details=[('ink', [(x, -16), (x + 0.5, -2)], 0.6) for x in (-5, 0, 5)])
    cv.shape(cv.ellipse((0, -17), 9.2, 2.0), Ink('#b08a5c', '#6a4c34', '#dcb88a'), z=0.1, sd=0.5, ol=0.6,
             details=[('ink', [(-5, -17), (0, -16.2), (5, -17)], 0.5)])
    anvil = cv.blob([(-6, -17, 0.0), (-4, -21, 0.0), (-12, -22.5), (-19, -26, 0.0), (-6, -27, 0.0), (13, -27, 0.0), (13, -23, 0.0), (6, -21, 0.0), (7, -17, 0.0)])
    cv.shape(anvil, IRON, z=0.3, sd=2.4, hi=0.6)
    blade = cv.blob([(-14, -28.5, 0.0), (10, -29.5), (14, -28.8, 0.0), (10, -27.6), (-14, -27.4, 0.0)])
    cv.shape(blade, Ink('#ff8a3a', '#c43a1a', '#fff0a0'), z=0.4, sd=0.5, ol=0.7, glow=(1.0, 0.4, 0.1))
    cv.shape(cv.capsule((-14, -28), (-20, -28.2), 0.9, 0.9), IRON, z=0.42, sd=0.3, ol=0.6)
    cv.shape(cv.capsule((14, 0), (19, -20), 1.1, 1.0), WOOD, z=0.5, sd=0.5, ol=0.7)
    cv.shape(cv.blob([(15.5, -19, 0.0), (22.5, -21, 0.0), (23.5, -17, 0.0), (16.5, -15.5, 0.0)]), IRON, z=0.55, sd=0.8, hi=0.3)
    return P.done()


def kartal():
    """Tünekte bürküt: T biçimli ahşap tünek, deri bağlı altın kartal (sağa bakar), sarı ayaklar."""
    P = Prop(58, 98, 28, 94)
    cv = P.cv
    cv.shape(cv.capsule((0, 0), (0, -62), 2.0, 1.8), WOOD_D, z=0, sd=1.0, hi=0.4)
    cv.shape(cv.capsule((-12, -62), (14, -62), 1.8, 1.8), WOOD, z=0.1, sd=0.8, hi=0.4)
    cv.shape(cv.blob([(-6, 0.5, 0.0), (-5, -3), (0, -4.5), (5, -3), (6, 0.5, 0.0)]), STONE, z=0.2, sd=1.2, ol=0.8)
    FEATH = Ink('#6a4a30', '#2e1e1e', '#a07850', '#1a1014', name='kartal tüyü')
    NAPE = Ink('#c89a52', '#7a5430', '#f0d090', name='altın ense')
    tail = cv.blob([(-2, -66), (-12, -58), (-16, -48, 0.0), (-10, -50), (-6, -46, 0.0), (0, -60)])
    cv.shape(tail, FEATH.darker(0.85), z=0.3, sd=2.0, hi=0.3, details=[('ink', [(-6, -60), (-12, -51)], 0.7)])
    body = cv.blob([(-4, -64), (-6, -74), (-2, -84), (6, -88), (11, -84), (12, -74), (8, -64), (2, -62)])
    det = []
    for k in range(5):
        y = -82 + k * 4
        det.append(('stroke', [(-3, y), (3, y + 2), (8, y + 1)], 1.2, FEATH.shadow, (0.2, 0.4)))
    cv.shape(body, FEATH, z=0.4, sd=4.0, hi=0.5, details=det)
    wing = cv.blob([(0, -84), (-5, -76), (-9, -62, 0.0), (-3, -64), (4, -70), (6, -80)])
    det = [('ink', [(-1, -80), (-6, -66)], 0.8), ('ink', [(2, -78), (-3, -66)], 0.7)]
    for k in range(4):
        det.append(('stroke', [(-7 + k * 2, -66 + k * 0.5), (-4 + k * 2.5, -70)], 1.0, FEATH.hi, (0.2, 0.6)))
    cv.shape(wing, FEATH.darker(0.9), z=0.5, sd=2.6, hi=0.4, details=det)
    head = cv.blob([(2, -86), (4, -93), (9, -96), (14, -94), (16, -90), (12, -87), (8, -84)])
    cv.shape(head, NAPE, z=0.6, sd=2.0, hi=0.4, details=[('ink', [(4, -90), (8, -87)], 0.7)])
    beak = cv.blob([(14, -94.5), (19, -92.5), (19.5, -89, 0.0), (17.5, -90.5), (15, -90)])
    cv.shape(beak, Ink('#3a3438', '#1a161c', '#7a7078'), z=0.7, sd=0.6, hi=0.3)
    cv.shape(cv.blob([(14, -94.4), (16, -94.6), (16.4, -92), (14.2, -92)]), Ink('#e8c040'), z=0.72, sd=0.3, ol=0.5)
    cv.fill(cv.ellipse((12, -93), 1.2, 1.0), (1.0, 0.75, 0.2), z=0.75, glow=(0.8, 0.5, 0.1))
    cv.stroke([(10.5, -94.2), (14, -93.6)], 1.3, z=0.76, col=INK, taper=(0.1, 0.6))
    for x in (2, 7):
        cv.shape(cv.capsule((x, -64), (x + 0.5, -61), 1.0, 0.9), Ink('#e0b840'), z=0.8, sd=0.3, ol=0.6)
        for k in (-1, 0, 1):
            cv.stroke([(x, -61.5), (x + k * 1.6 + 0.5, -59.8)], 0.9, z=0.82, col=INK, taper=(0.1, 0.8))
    cv.stroke([(4, -62), (5, -54), (3, -48)], 1.2, z=0.85, col=LEATHER.base, taper=(0.1, 0.3))
    cv.shape(cv.blob([(1, -48, 0.0), (7, -46), (5, -40, 0.0), (3, -44)]), RED, z=0.86, sd=0.6, ol=0.6)
    return P.done()


def at():
    """Eğerli at (sola bakar): doru, kara yele örgülü ve kızıl kurdeleli, kızıl keçe eğer örtüsü altın kenarlı,
    yüksek kaşlı ahşap Türk eğeri, üzengiler, uzun kara kuyruk."""
    P = Prop(116, 88, 58, 84)
    cv = P.cv
    COAT = Ink('#7c4a2e', '#3a1e24', '#b47a4c', '#24121a', name='doru')
    COAT_B = COAT.darker(0.78)
    MANE = HAIR_K
    # uzak bacaklar
    def leg(top, knee, fet, hoof, mat, z, sock=False):
        p = ik.union(cv.limb([top, knee, fet], [4.4, 2.6, 2.0]), cv.limb([fet, hoof], [2.0, 2.3]))
        cv.shape(p, mat, z=z, sd=1.8, hi=0.3)
        if sock:
            cv.shape(ik.isect(p, cv.blob([(hoof[0] - 5, hoof[1] - 9, 0.0), (hoof[0] + 5, hoof[1] - 9, 0.0), (hoof[0] + 5, hoof[1] - 1.5, 0.0), (hoof[0] - 5, hoof[1] - 1.5, 0.0)])),
                     FELT_C, z=z + 0.01, sd=0.8, ol=0.0)
        cv.shape(cv.blob([(hoof[0] - 2.6, 0.5, 0.0), (hoof[0] - 2.2, -2.2, 0.0), (hoof[0] + 2.6, -2.2, 0.0), (hoof[0] + 3.0, 0.5, 0.0)]), Ink('#3a3036'), z=z + 0.02, sd=0.6, ol=0.7)
    leg((-14, -32), (-17, -16), (-16, -5), (-16.5, 0), COAT_B, -1.0)
    leg((26, -34), (32, -18), (29, -5), (29.5, 0), COAT_B, -1.0)
    # kuyruk
    tail = ik.taper_path([cv.W(p) for p in [(38, -46), (44, -40), (45, -26), (42, -12)]], cv.u(7.0), prof=lambda u: 0.45 + 0.55 * math.sin(math.pi * min(1, u * 0.9 + 0.1)))
    cv.shape(tail, MANE, z=-0.5, sd=2.0, hi=0.5,
             details=[('stroke', [(40, -40), (43, -28), (41, -16)], 0.8, MANE.hi, (0.2, 0.6))])
    # gövde
    body = ik.union(cv.ellipse((6, -40), 30, 12.5), cv.ellipse((-18, -40), 12, 13.5, -0.2), cv.ellipse((27, -41), 13, 13.5),
                    cv.capsule((-19, -45), (-31, -63), 10.5, 7.2))
    det = [('ink', [(-8, -30), (6, -28.5), (20, -30)], 0.9), ('ink', [(-26, -36), (-22, -30)], 0.8),
           ('stroke', [(-30, -60), (-24, -50), (-16, -44)], 1.0, COAT.hi, (0.2, 0.5))]
    cv.shape(body, COAT, z=0, sd=6.0, hi=1.0, details=det, bounce=0.35)
    head = cv.blob([(-28, -62), (-33, -70), (-38, -71), (-48, -58), (-52, -52), (-51, -48.5), (-46, -47.5), (-40, -52), (-33, -56)])
    hd = [('ink', [(-49, -51.5), (-47, -50.8)], 0.8), ('ink', [(-44, -55), (-40, -58)], 0.7),
          ('col', cv.ellipse((-36.5, -64), 1.3, 1.0), INK),
          ('stroke', [(-36.6, -64.6), (-36, -64.8)], 0.6, (1, 1, 1), (0.1, 0.1))]
    cv.shape(head, COAT, z=0.2, sd=3.0, hi=0.6, details=hd)
    for f in (0, 1):
        cv.shape(cv.blob([(-33 + f * 2.5, -69), (-34 + f * 2.5, -76, 0.0), (-30.5 + f * 2.5, -70)]), COAT, z=0.15 + f * 0.1, sd=0.8, ol=0.7)
    # yular (kızıl kayış)
    cv.stroke([(-36, -68), (-44, -56), (-50, -50)], 1.2, z=0.3, col=RED.base, taper=(0.05, 0.05))
    cv.stroke([(-35, -66), (-39, -58), (-43, -53)], 1.2, z=0.3, col=RED.base, taper=(0.05, 0.05))
    cv.stroke([(-46, -51), (-30, -46), (-14, -48)], 0.8, z=0.31, col=LEATHER.base, taper=(0.05, 0.05))
    # yele: örgü düğümleri + kurdele
    for k in range(6):
        t = k / 5
        q = (-31 + t * 13, -68 + t * 20)
        cv.shape(cv.ellipse((q[0] + 2, q[1]), 2.6, 2.2), MANE, z=0.35 + k * 0.01, sd=0.8, hi=0.3)
        if k % 2 == 0:
            cv.shape(cv.blob([(q[0] + 2, q[1] + 1), (q[0] + 5, q[1] + 6, 0.0), (q[0] + 3, q[1] + 2.6)]), RED, z=0.4, sd=0.4, ol=0.6)
    # yakın bacaklar
    leg((-18, -32), (-22, -16), (-21, -5), (-22, 0), COAT, 1.0, sock=True)
    leg((22, -34), (28, -17), (24, -5), (24.5, 0), COAT, 1.0)
    # eğer örtüsü + eğer + üzengi
    blanket = cv.blob([(-10, -50, 0.0), (18, -50, 0.0), (20, -30, 0.0), (16, -28), (-8, -28), (-12, -30, 0.0)])
    det = [('col', cv.blob([(-10, -32, 0.0), (20, -32, 0.0), (20, -29, 0.0), (-12, -29, 0.0)]), GOLD.base)]
    for x in (-4, 4, 12):
        det.append(('col', cv.blob(diamond(x, -38, 3.2, 3.6)), GOLD.base))
        det.append(('col', cv.blob(diamond(x, -38, 1.4, 1.6)), BLUE.base))
    cv.shape(blanket, RED, z=1.5, sd=4.0, hi=0.5, details=det)
    for k in range(10):
        x = -10 + k * 3
        cv.stroke([(x, -28.5), (x + 0.4, -25.5)], 0.8, z=1.45, col=GOLD.base, taper=(0.1, 0.7))
    saddle = cv.blob([(-7, -50, 0.0), (-9, -58, 0.0), (-4, -55), (8, -53), (14, -57, 0.0), (15, -50, 0.0)])
    cv.shape(saddle, WOOD_R, z=1.6, sd=2.4, hi=0.5, details=[('stroke', [(-6, -51), (13, -51)], 1.0, GOLD.base, (0.1, 0.1))])
    cv.shape(cv.blob([(-5, -53, 0.0), (12, -53, 0.0), (11, -49.5, 0.0), (-4, -49.5, 0.0)]), BLUE, z=1.65, sd=1.0, ol=0.7)
    cv.stroke([(3, -50), (3.5, -30), (3, -22)], 0.9, z=1.7, col=LEATHER.shadow)
    cv.shape(cv.blob([(0.5, -22.5, 0.0), (5.5, -22.5, 0.0), (4.8, -19.5, 0.0), (1.2, -19.5, 0.0)]), IRON, z=1.75, sd=0.4, ol=0.6)
    cv.stroke([(-10, -46), (-16, -40), (-24, -44)], 1.0, z=1.55, col=LEATHER.base, taper=(0.05, 0.05))
    return P.done()


# ------------------------------------------------------------------ önizleme
ALL = {
    'yh_otag': otag, 'yh_cadir': cadir, 'yh_kayin': kayin, 'yh_sunak': sunak, 'yh_pinar': pinar, 'yh_demirhane': demirhane,
    'yh_ors': ors, 'yh_kartal': kartal, 'yh_at': at, 'yh_hali_sergi': hali_sergi,
    'yh_hali_1': lambda: hali(RED, BLUE, 1), 'yh_hali_2': lambda: hali(BLUE, RED, 2),
    'yh_yol_1': lambda: yol(1), 'yh_yol_2': lambda: yol(2), 'yh_yol_3': lambda: yol(3),
    'yh_mangal': mangal, 'yh_kandil': kandil, 'yh_fener': fener, 'yh_tug_k': tug_k, 'yh_tug_m': tug_m,
    'yh_balbal_1': lambda: balbal(1, False), 'yh_balbal_2': lambda: balbal(2, True), 'yh_kurgan': kurgan,
    'yh_kapi': kapi, 'yh_kazan': kazan, 'yh_seki': seki,
}


if __name__ == '__main__':
    import sys
    from PIL import Image
    names = [a for a in sys.argv[1:] if a in ALL] or list(ALL)
    out = []
    for n in names:
        rgba, glow, org = ALL[n]()
        out.append((n, rgba, glow))
    W = sum(r.shape[1] for _, r, _ in out) + 40 * len(out)
    H = max(r.shape[0] for _, r, _ in out) + 40
    bg = np.zeros((H, W, 3), np.float32)
    bg[:] = (0.09, 0.1, 0.16)
    x = 20
    for n, r, g in out:
        h, w = r.shape[:2]
        y = H - 20 - h
        a = r[..., 3:4]
        bg[y:y + h, x:x + w] = bg[y:y + h, x:x + w] * (1 - a) + r[..., :3] * a
        bg[y:y + h, x:x + w] += g[..., :3] * g[..., 3:4] * 0.8
        x += w + 40
    Image.fromarray((np.clip(bg, 0, 1) * 255).astype(np.uint8)).save(sys.argv[-1] if sys.argv[-1].endswith('.png') else 'yurt_ink_on.png')
