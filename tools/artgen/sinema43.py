"""v43 sinematik motoru için katmanlı sumi-e çekimleri (sumi.py fırça takımı + hikaye_ink.py motifleri).

    python sinema43.py                    hepsi -> assets/sinema/<çekim>_<katman>.webp (+ katmanlar.json)
    python sinema43.py kayin gunana       yalnızca bu çekimler
    python sinema43.py --onizleme <png>   her çekimin katmanları üst üste (temas sayfası)

Her çekim 2560x1440 "tuval" biriminde boyanır (4K'ya hazır; 1080p'de 0,75 ölçek). Katman türleri:
  * arka (opak WebP): kâğıt + gök / yer yıkamaları — en uzak düzlem
  * saydam katmanlar (RGBA WebP): orta / ön düzlem mürekkebi; motor bunları derinliğe göre kaydırır (paralaks),
    odak dışındakileri bulanıklaştırır (odak çekimi), ağaç tepeleri / çaputlar rüzgârda salınır
  * oyuncular (RGBA, kırpılmış): ayrı canlandırılan parçalar (Bengü'nün düşüşü, Erlik, kırkı bıçakları, Umay'ın
    kanatları, yazı); tuvaldeki yeri katmanlar.json "ofs" ile saklanır (motor aynı yere koyar, anahtarlarla oynatır)
  * ışık (RGBA, yarım çözünürlük): altın varak / kor ışıması, motorda toplamalı ve nabızlı
Kompozisyon: üçler kuralı, değer grupları (koyu kütle / boş kâğıt / tek sıcak vurgu), altta anlatı için sakin bant.
Bengü'nün çizimi stilize tutulur (kurt başlıklı kukuleta, tek uzun örgü ucunda al bağ, kam davulu, kısa kılıç; oyun
içi karakter tasarımı değişse de bu siluet dili uyumlu kalır).
"""
import json
import math
import os
import sys

import numpy as np
from scipy import ndimage

from sumi import Sumi, fbm, catmull, INK, GOLD, GOLD_HI, VERM, PAPER
from hikaye_ink import mountains, tree, braid, chain, seal, sun_glow, silhouette, BRAID_COLS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'assets', 'sinema')
W, H = 2560, 1440

NIGHT = (0.70, 0.72, 0.79)
DUSK = (0.80, 0.78, 0.78)
DAWN = (0.98, 0.87, 0.72)
PALE = (0.93, 0.90, 0.83)
INDIGO = (0.30, 0.34, 0.52)
ROSE = (0.95, 0.52, 0.40)
SAFFRON = (0.98, 0.70, 0.30)
TEAL = (0.42, 0.68, 0.74)
EMBER = (1.0, 0.42, 0.14)
KAFTAN = (0.557, 0.157, 0.204)  # Bengü'nün kaftanı: kök boya kızılı (#8e2834; ky-bengu43 'Tan Bekçisi')
POST = (0.95, 0.92, 0.85)       # ak kurt postu (kukuleta + pelerin)
GUMUS = (0.80, 0.82, 0.88)      # şolpı diskleri
DERI = (0.26, 0.16, 0.10)       # geniş deri kemer
CIVIT = (0.22, 0.24, 0.40)      # dar çivit şalvar

META = {}
_SIRA = [0]


def _sira():
    _SIRA[0] += 1
    return _SIRA[0]


# ====================================================================== katman çıkışı
def _rgba(S, gold_k=1.0, ink=None):
    """Kâğıtsız (saydam) birleşim: renkli yıkama, kara mürekkep, kızıl, altın sırayla "üstüne" bindirilir."""
    h, w = S.h, S.w
    A = np.zeros((h, w), np.float32)
    C = np.zeros((h, w, 3), np.float32)

    def over(col, a):
        nonlocal A, C
        a = np.clip(a, 0, 1)
        na = a + A * (1 - a)
        C = np.where(na[..., None] > 1e-5, (col * a[..., None] + C * (A * (1 - a))[..., None]) / np.maximum(na, 1e-5)[..., None], 0)
        A = na

    ca = np.clip(S.Ca, 0, 1)
    cc = np.where(ca[..., None] > 1e-4, S.C / np.maximum(ca, 1e-4)[..., None], 0)
    over(cc * 0.92, ca)
    d = np.clip(S.D, 0, 1)
    d = 1 - (1 - d) ** 1.25
    ic = INK if ink is None else np.array(ink, np.float32)
    # ince yıkamada mürekkep kâğıda karışır gibi hafif sıcak / gri: düşük yoğunlukta biraz açık
    over(ic[None, None, :] * (0.55 + 0.45 * d[..., None]) + np.array([0.18, 0.17, 0.17]) * (1 - d[..., None]) ** 2, d)
    over(np.broadcast_to(VERM, (h, w, 3)), S.R)
    g = np.clip(S.G * gold_k, 0, 1)
    sp = fbm(h, w, 2.0, S.seed + 55, octaves=2)
    gc = GOLD[None, None, :] * (0.78 + 0.32 * sp[..., None]) + (GOLD_HI - GOLD)[None, None, :] * np.clip(sp - 0.72, 0, 1)[..., None] * 2.2
    over(gc, g)
    return np.concatenate([np.clip(C, 0, 1), A[..., None]], -1)


def _save(arr, name, q=86):
    from PIL import Image
    os.makedirs(OUT, exist_ok=True)
    a = (np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)
    mode = 'RGBA' if a.shape[2] == 4 else 'RGB'
    im = Image.fromarray(a, mode)
    p = os.path.join(OUT, name + '.webp')
    im.save(p, 'WEBP', quality=q, method=6, alpha_quality=90)
    return im


def arka(S, name, tone, gold_k=1.0, glow=True):
    """Opak arka plan (kâğıt + yıkamalar)."""
    col = S.compose(tone=tone, gold_k=gold_k)
    _save(col, name, q=84)
    META[name] = {'w': S.w, 'h': S.h, 'ofs': [0, 0], 'opak': True, 'sira': 0}
    if glow:
        isik(S, name, gold_k)


def katman(S, name, gold_k=1.0, glow=True, ink=None, krp=False):
    """Saydam katman (tam tuval ya da kırpılmış oyuncu)."""
    arr = _rgba(S, gold_k, ink)
    ofs = [0, 0]
    if krp:
        a = arr[..., 3]
        ys, xs = np.where(a > 0.01)
        if len(xs):
            x0, x1 = max(0, xs.min() - 8), min(S.w, xs.max() + 9)
            y0, y1 = max(0, ys.min() - 8), min(S.h, ys.max() + 9)
            arr = arr[y0:y1, x0:x1]
            ofs = [int(x0), int(y0)]
    _save(arr, name, q=88)
    META[name] = {'w': int(arr.shape[1]), 'h': int(arr.shape[0]), 'ofs': ofs, 'sira': _sira()}
    if glow:
        isik(S, name, gold_k)


def isik(S, name, gold_k=1.0, ofs=(0, 0), size=None):
    g = np.clip(S.G * gold_k, 0, 1)
    if g.max() < 0.02 and np.abs(S.E).max() < 0.02:
        return
    gl = S.glow(0.5, 22.0, gold_k)
    if size is not None:
        x0, y0 = ofs[0] // 2, ofs[1] // 2
        gl = gl[y0:y0 + size[1] // 2 + 1, x0:x0 + size[0] // 2 + 1]
    _save(gl, name + '_isik', q=80)
    META[name]['isik'] = True


def yeni(seed):
    return Sumi(W, H, seed)


# ====================================================================== motifler (v43)
def ink_sky(S, top, bot, seed, y0=0, y1=H, gran=0.55, wobble=70):
    S.grad_wash(y0, y1, top, bot, seed=seed, gran=gran, wobble=wobble)


def stars(S, n, box, seed, k=0.75):
    rs = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    pts = []
    for _ in range(n):
        r = rs.uniform(0.8, 2.6) if rs.random() < 0.9 else rs.uniform(3.0, 4.5)
        pts.append((rs.uniform(x0, x1), rs.uniform(y0, y1) * (0.6 + 0.4 * rs.random()), r))
    S.dots(pts, 0, layer='G', k=k)


def moon(S, x, y, r, halo=0.35):
    S.erase(S.ellipse_mask(x, y, r, r), 0.97)
    S.enso(x, y, r * 1.06, r * 0.08, load=0.55, dry=0.65, a0=0.5, span=4.6)
    sun_glow(S, x, y, r * 3.2, col=(0.55, 0.64, 0.86), k=halo)


def grass_tuft(S, x, y, h, n, seed, lean=0.0, load=1.0, layer='D', col=None, w=None):
    rs = np.random.default_rng(seed)
    for i in range(n):
        bx = x + rs.normal(0, h * 0.18)
        hh = h * rs.uniform(0.45, 1.0)
        ln = lean + rs.uniform(-0.35, 0.35)
        pts = [(bx, y + 6), (bx + math.sin(ln) * hh * 0.4, y - hh * 0.5), (bx + math.sin(ln) * hh * 1.0 + ln * hh * 0.3, y - hh)]
        S.stroke(pts, (w or h * 0.035) * rs.uniform(0.6, 1.2), load=load * rs.uniform(0.75, 1.0), dry=0.35, taper=(0.02, 0.95), layer=layer, col=col)


def rock(S, x, y, rw, rh, seed, dens=0.9):
    rs = np.random.default_rng(seed)
    pts = []
    for k in range(9):
        a = math.pi + k / 8 * math.pi
        pts.append((x + math.cos(a) * rw * rs.uniform(0.8, 1.05), y + math.sin(a) * rh * rs.uniform(0.8, 1.1)))
    pts += [(x + rw, y + rh * 0.2), (x - rw, y + rh * 0.2)]
    S.wash(S.path_mask(pts), dens=dens, blur=2.0, bleed=0.5, gran=0.5, seed=seed)
    S.stroke(pts[:6], rw * 0.07, load=1.0, dry=0.7, taper=(0.1, 0.6))


def bengu43(S, x, y, s, pose='davul', load=1.0, k_hood=1.0, hair='uzun'):
    """Bengü (v43 sinema çizimi): kurt postu kukuleta (iki kulak, alında burun kemeri), tek uzun örgü (ucunda al bağ),
    çivit kaftan (beline kuşak), kemerinde kam davulu, kısa eğri kılıç. y: ayak tabanı; s: boy ölçüsü (baş-ayak ~ s).
    pose: davul (yandan, davulu kaldırmış, ateşe dönük), arka (sırtı dönük, yola bakar), dusus (sırtüstü savrulur),
    diz (diz çökmüş, elleri önde), dal (dalda oturur, kısa saç)."""
    L = dict(layer='D')
    if pose in ('davul', 'arka'):
        # gövde: kaftan siluet (koyu çivit yıkama + kara kontur)
        hx, hy = x, y - s * 0.86
        body = [(x - s * 0.07, y - s * 0.78), (x + s * 0.08, y - s * 0.78), (x + s * 0.13, y - s * 0.6), (x + s * 0.12, y - s * 0.42),
                (x + s * 0.2, y - s * 0.12), (x + s * 0.24, y), (x - s * 0.24, y), (x - s * 0.19, y - s * 0.14), (x - s * 0.13, y - s * 0.42),
                (x - s * 0.13, y - s * 0.62)]
        m = S.path_mask(body)
        S.wash(m, dens=0.9 * load, blur=1.4, bleed=0.5, gran=0.25, layer='C', col=KAFTAN)
        S.wash(m * 0.9, dens=0.22 * load, blur=1.4, bleed=0.6, gran=0.3, **L)
        # önü açık kaftan: sarılma çizgisinde ince safran şerit
        S.stroke([(x + s * 0.03, y - s * 0.77), (x + s * 0.0, y - s * 0.46), (x - s * 0.03, y - s * 0.12), (x - s * 0.05, y - s * 0.01)], s * 0.012, load=0.9, dry=0.2, layer='C', col=SAFFRON)
        # geniş deri kemer, gümüş levhalar, güneş tokası (Kut koru)
        S.stroke([(x - s * 0.13, y - s * 0.47), (x, y - s * 0.45), (x + s * 0.13, y - s * 0.48)], s * 0.045, load=load, dry=0.2, layer='C', col=DERI)
        S.dots([(x + k * s * 0.05, y - s * 0.46, s * 0.008) for k in (-2, -1, 1, 2)], 0, layer='C', col=GUMUS, k=0.9)
        S.dots([(x, y - s * 0.455, s * 0.016)], 0, layer='G', k=1.0)
        # kontur: gölge yanı kalın kuru fırça
        S.stroke([body[-1], body[-2], body[-3], body[-4]], s * 0.03, load=load, dry=0.55, taper=(0.1, 0.5), **L)
        S.stroke([body[1], body[2], body[3], body[4], body[5]], s * 0.018, load=load * 0.9, dry=0.7, taper=(0.1, 0.6), **L)
        # bacak arası ve çizmeler
        S.stroke([(x - s * 0.02, y - s * 0.32), (x - s * 0.03, y - s * 0.02)], s * 0.02, load=0.8, dry=0.5, **L)
        S.wash(S.path_mask([(x - s * 0.17, y - s * 0.08), (x - s * 0.05, y - s * 0.08), (x - s * 0.04, y + 2), (x - s * 0.2, y + 2)], smooth=False), dens=load, blur=1, bleed=0.2, gran=0.1, **L)
        S.wash(S.path_mask([(x + s * 0.04, y - s * 0.08), (x + s * 0.16, y - s * 0.08), (x + s * 0.21, y + 2), (x + s * 0.03, y + 2)], smooth=False), dens=load, blur=1, bleed=0.2, gran=0.1, **L)
        # kukuleta: kurt başı (kulaklar, burun kemeri öne), omuzlara inen post
        hood = [(hx - s * 0.1, hy + s * 0.12), (hx - s * 0.11, hy - s * 0.02), (hx - s * 0.085, hy - s * 0.1), (hx - s * 0.075, hy - s * 0.17),
                (hx - s * 0.04, hy - s * 0.11), (hx + s * 0.02, hy - s * 0.12), (hx + s * 0.05, hy - s * 0.19), (hx + s * 0.075, hy - s * 0.1),
                (hx + s * 0.14 if pose == 'davul' else hx + s * 0.09, hy - s * 0.05), (hx + s * 0.1, hy + s * 0.0), (hx + s * 0.12, hy + s * 0.12)]
        # ak kurt postu: ensesinden bele inen pelerin + kukuleta (kısa burun, uçları koyu uzun kulaklar, camgöbeği Kut gözü)
        cape = [(hx - s * 0.12, hy + s * 0.06), (x - s * 0.17, y - s * 0.62), (x - s * 0.16, y - s * 0.44), (x + s * 0.15, y - s * 0.44), (x + s * 0.15, y - s * 0.62), (hx + s * 0.12, hy + s * 0.06)]
        cm = S.path_mask(cape) if pose == 'arka' else S.path_mask([(hx - s * 0.12, hy + s * 0.06), (x - s * 0.2, y - s * 0.6), (x - s * 0.17, y - s * 0.44), (x - s * 0.05, y - s * 0.6), (hx + s * 0.05, hy + s * 0.08)])
        S.erase(cm, 0.95)
        S.wash(cm, dens=0.9, blur=1.2, bleed=0.5, gran=0.2, layer='C', col=POST)
        hm = S.path_mask(hood)
        S.erase(hm, 0.95)
        S.wash(hm, dens=0.95 * k_hood, blur=1.0, bleed=0.5, gran=0.15, layer='C', col=POST)
        S.stroke(hood + [hood[0]], s * 0.01, load=0.75 * load, dry=0.55, taper=(0.0, 0.0), **L)
        S.dots([(hood[3][0], hood[3][1] + s * 0.012, s * 0.014), (hood[6][0], hood[6][1] + s * 0.012, s * 0.014)], 0, k=0.95)
        S.dots([(hx + s * 0.06, hy - s * 0.07, s * 0.008)], 0, layer='C', col=(0.35, 0.9, 1.0), k=1.0)
        rs = np.random.default_rng(int(x + y))
        for i in range(9):
            px = hx + rs.uniform(-0.11, 0.11) * s
            S.stroke([(px, hy + s * 0.02), (px + rs.uniform(-0.03, 0.03) * s, hy + s * 0.12), (px + rs.uniform(-0.05, 0.05) * s, hy + s * 0.19)],
                     s * 0.008, load=load * 0.45, dry=0.75, taper=(0.1, 0.9), **L)
        if pose == 'davul':
            # yüz: kâğıt boşluğu (yan profil), tek göz fırçası
            S.erase(S.path_mask([(hx + s * 0.04, hy - s * 0.04), (hx + s * 0.085, hy - s * 0.02), (hx + s * 0.08, hy + s * 0.05), (hx + s * 0.045, hy + s * 0.07)]), 0.75)
            S.stroke([(hx + s * 0.055, hy + s * 0.0), (hx + s * 0.07, hy + s * 0.003)], s * 0.008, load=1.0, dry=0.1, **L)
            # kam davulu: kaldırılmış (önde, oval, kenarı kalın; derisinde kızıl gök resmi)
            dx, dy = x + s * 0.26, y - s * 0.72
            S.wash(S.ellipse_mask(dx, dy, s * 0.13, s * 0.17), dens=0.35 * load, blur=1.5, bleed=0.6, gran=0.5, layer='C', col=(0.85, 0.72, 0.52))
            S.enso(dx, dy, s * 0.15, s * 0.035, load=load, dry=0.4, a0=-2.0, span=6.0, squash=1.15)
            S.stroke([(dx - s * 0.1, dy), (dx + s * 0.1, dy)], s * 0.012, layer='R', load=0.9, dry=0.3)
            S.stroke([(dx, dy - s * 0.13), (dx, dy + s * 0.13)], s * 0.012, layer='R', load=0.9, dry=0.3)
            S.dots([(dx - s * 0.05, dy - s * 0.06, s * 0.016), (dx + s * 0.05, dy - s * 0.06, s * 0.016)], 0, layer='R', k=0.9)
            # kollar: biri davulu tutar, öbürü tokmakla
            S.stroke([(x + s * 0.08, y - s * 0.74), (x + s * 0.17, y - s * 0.66), (x + s * 0.2, y - s * 0.74)], s * 0.05, load=load, dry=0.35, **L)
            S.stroke([(x - s * 0.06, y - s * 0.73), (x - s * 0.02, y - s * 0.95), (x + s * 0.1, y - s * 1.02)], s * 0.045, load=load, dry=0.35, **L)
            S.stroke([(x + s * 0.1, y - s * 1.02), (x + s * 0.2, y - s * 0.92)], s * 0.018, load=load, dry=0.2, **L)
            # örgü: arkadan rüzgârla
            pts = [(hx - s * 0.08, hy + s * 0.04), (hx - s * 0.2, hy + s * 0.2), (hx - s * 0.28, hy + s * 0.34), (hx - s * 0.4, hy + s * 0.42)]
        else:
            # sırtı dönük: örgü sırtın ortasından iner; kılıç belde
            pts = [(hx, hy + s * 0.08), (hx + s * 0.01, hy + s * 0.25), (hx - s * 0.02, hy + s * 0.4), (hx + s * 0.01, hy + s * 0.52)]
            S.stroke([(x + s * 0.1, y - s * 0.47), (x + s * 0.2, y - s * 0.3), (x + s * 0.27, y - s * 0.1)], s * 0.022, load=load, dry=0.2, taper=(0.02, 0.9), **L)
            # davul sırtta (yandan elips)
            S.enso(x - s * 0.14, y - s * 0.55, s * 0.08, s * 0.025, load=load, dry=0.4, squash=1.6, a0=-1.0, span=6.0)
        braid(S, pts, s * 0.045, layer='D', k=load)
        # örgü ucunda gümüş şolpı diskleri
        S.dots([(pts[-1][0] - s * 0.012 * k, pts[-1][1] + s * 0.03 * k, s * 0.018) for k in (1, 2, 3)], 0, layer='C', col=GUMUS, k=1.0)
    elif pose == 'dusus':
        J = {'pel': (0, 0), 'ch': (-0.45, 0.25), 'nk': (-0.6, 0.33), 'hd': (-0.76, 0.42), 'sh': (-0.52, 0.27), 'el1': (-0.78, -0.05), 'ha1': (-0.66, -0.42),
             'el2': (-0.36, 0.62), 'ha2': (-0.08, 0.78), 'kn1': (0.4, -0.36), 'ft1': (0.56, -0.8), 'kn2': (0.52, -0.06), 'ft2': (0.96, -0.28)}
        segs = [('pel', 'ch', 0.3, 0.28), ('ch', 'nk', 0.16, 0.1), ('sh', 'el1', 0.1, 0.08), ('el1', 'ha1', 0.08, 0.05), ('sh', 'el2', 0.1, 0.08),
                ('el2', 'ha2', 0.08, 0.05), ('pel', 'kn1', 0.15, 0.11), ('kn1', 'ft1', 0.1, 0.07), ('pel', 'kn2', 0.15, 0.11), ('kn2', 'ft2', 0.1, 0.07)]
        skirt = [(-0.12, 0.12), (0.12, -0.28), (0.55, -0.45), (0.7, -0.1), (0.3, 0.12)]
        sc = s * 0.42
        P = silhouette(S, x, y, sc, J, segs, polys=[skirt], dens=0.95 * load)
        hd = P['hd']
        # kukuleta: kulaklar aşağı (baş aşağı), post savrulur
        S.dots([(hd[0], hd[1], sc * 0.15)], 0, k=load)
        for a in (2.2, 2.8):
            S.stroke([(hd[0], hd[1]), (hd[0] + math.cos(a) * sc * 0.25, hd[1] + math.sin(a) * sc * 0.25)], sc * 0.09, load=load, dry=0.2, taper=(0.1, 0.95))
        # kaftan rengi
        S.wash(S.path_mask([(x + sc * u, y + sc * v) for u, v in skirt]), dens=0.6, blur=2, bleed=0.4, gran=0.3, layer='C', col=KAFTAN)
        braid(S, [(hd[0] - sc * 0.06, hd[1] - sc * 0.06), (hd[0] - sc * 0.25, hd[1] - sc * 0.5), (hd[0] - sc * 0.05, hd[1] - sc * 0.95), (hd[0] - sc * 0.3, hd[1] - sc * 1.4)],
              sc * 0.12, layer='D', k=load)
        S.stroke([(hd[0] - sc * 0.3, hd[1] - sc * 1.4), (hd[0] - sc * 0.36, hd[1] - sc * 1.55)], sc * 0.09, load=1.0, dry=0.2, layer='R')
    elif pose == 'diz':
        J = {'pel': (0, -0.45), 'ch': (0.03, -0.95), 'nk': (0.05, -1.08), 'hd': (0.07, -1.2), 'sh': (0.05, -0.93), 'el1': (0.3, -0.78), 'ha1': (0.42, -0.98),
             'el2': (0.22, -0.7), 'ha2': (0.36, -0.94), 'kn1': (0.38, -0.42), 'ft1': (0.4, 0.0), 'kn2': (-0.08, 0.0), 'ft2': (-0.5, 0.0)}
        segs = [('pel', 'ch', 0.3, 0.27), ('ch', 'nk', 0.15, 0.1), ('sh', 'el1', 0.1, 0.08), ('el1', 'ha1', 0.08, 0.06), ('sh', 'el2', 0.1, 0.08),
                ('el2', 'ha2', 0.08, 0.06), ('pel', 'kn1', 0.16, 0.12), ('kn1', 'ft1', 0.11, 0.08), ('pel', 'kn2', 0.16, 0.12), ('kn2', 'ft2', 0.11, 0.06)]
        skirt = [(-0.2, -0.62), (0.16, -0.62), (0.44, -0.28), (0.1, -0.08), (-0.36, -0.06)]
        sc = s * 0.8
        P = silhouette(S, x, y, sc, J, segs, polys=[skirt], dens=0.95 * load)
        S.D *= 0.55   # siluet koyuluğu: kızıl kaftan seçilsin
        S.wash(S.path_mask([(x + sc * u, y + sc * v) for u, v in skirt]), dens=0.9, blur=2, bleed=0.4, gran=0.3, layer='C', col=KAFTAN)
        hd = P['hd']
        S.dots([(hd[0], hd[1], sc * 0.12)], 0, k=load)
        # kukuleta geriye düşmüş (sırtta post), kısa kesik saç: ensede tutam
        pm = S.path_mask([(hd[0] - sc * 0.12, hd[1] + sc * 0.08), (hd[0] - sc * 0.26, hd[1] + sc * 0.2), (hd[0] - sc * 0.22, hd[1] + sc * 0.42),
                          (hd[0] - sc * 0.05, hd[1] + sc * 0.3)])
        S.erase(pm, 0.95)
        S.wash(pm, dens=0.95, blur=1.2, bleed=0.5, gran=0.2, layer='C', col=POST)
        for a in (-2.4, -2.0):
            S.stroke([(hd[0] - sc * 0.2, hd[1] + sc * 0.22), (hd[0] - sc * 0.2 + math.cos(a) * sc * 0.14, hd[1] + sc * 0.22 + math.sin(a) * sc * 0.14)], sc * 0.05,
                     load=1.0, dry=0.3, taper=(0.1, 0.95))
        S.stroke([(hd[0] - sc * 0.06, hd[1] - sc * 0.08), (hd[0] - sc * 0.17, hd[1] + sc * 0.02), (hd[0] - sc * 0.21, hd[1] + sc * 0.1)], sc * 0.08, load=load, dry=0.4,
                 taper=(0.1, 0.9))
    elif pose == 'dal':
        hd = (x, y - s * 0.95)
        S.dots([(hd[0], hd[1], s * 0.11)], 0, k=load)
        # kukuleta sırtta, kulaklar seçilir
        pm = S.path_mask([(hd[0] - s * 0.1, hd[1] + s * 0.1), (hd[0] - s * 0.22, hd[1] + s * 0.22), (hd[0] - s * 0.2, hd[1] + s * 0.45), (hd[0] - s * 0.02, hd[1] + s * 0.3)])
        S.wash(pm, dens=0.95, blur=1.2, bleed=0.5, gran=0.2, layer='C', col=POST)
        for a in (-2.5, -2.0):
            S.stroke([(hd[0] - s * 0.18, hd[1] + s * 0.24), (hd[0] - s * 0.18 + math.cos(a) * s * 0.13, hd[1] + s * 0.24 + math.sin(a) * s * 0.13)], s * 0.05,
                     load=1.0, dry=0.3, taper=(0.1, 0.95))
        S.stroke([(x, y - s * 0.82), (x - s * 0.03, y - s * 0.5), (x, y - s * 0.2)], s * 0.22, load=load, dry=0.35, taper=(0.1, 0.3), layer='C', col=KAFTAN)
        S.stroke([(x, y - s * 0.82), (x - s * 0.03, y - s * 0.5), (x, y - s * 0.2)], s * 0.2, load=load * 0.6, dry=0.45, taper=(0.1, 0.3))
        S.stroke([(x, y - s * 0.2), (x + s * 0.3, y - s * 0.15), (x + s * 0.35, y + s * 0.25), (x + s * 0.32, y + s * 0.55)], s * 0.1, load=load, dry=0.45)
        S.stroke([(x - s * 0.02, y - s * 0.18), (x + s * 0.2, y - s * 0.05), (x + s * 0.18, y + s * 0.35), (x + s * 0.25, y + s * 0.6)], s * 0.09, load=load, dry=0.5)
        # kısa kesik saç: rüzgârda iki tutam
        S.stroke([(hd[0] - s * 0.05, hd[1] - s * 0.05), (hd[0] - s * 0.22, hd[1] + s * 0.03), (hd[0] - s * 0.34, hd[1] + s * 0.0)], s * 0.08, load=load, dry=0.4, taper=(0.1, 0.9))
        S.stroke([(hd[0] - s * 0.04, hd[1] - s * 0.09), (hd[0] - s * 0.2, hd[1] - s * 0.08), (hd[0] - s * 0.3, hd[1] - s * 0.12)], s * 0.05, load=load, dry=0.5, taper=(0.1, 0.9))
        # beş renkli örgü bileğinde (küçük al-gök-sarı benekler)
        for i, c in enumerate(('al', 'ak', 'gok', 'sari', 'altin')):
            S.dots([(x + s * 0.12 + i * s * 0.025, y - s * 0.38 + i * s * 0.01, s * 0.016)], 0, layer='C', col=BRAID_COLS[c], k=0.95)


def gun_ana43(S, cx, cy, s, dens=0.9, halo=True, wind=0.35, layer='D'):
    """Gün Ana (önden, kollar açık) — hikaye_ink figürü örgüsüz (örgüler motorda canlı şerit olarak çizilir), kaftanı
    sıcak safran yıkama ile."""
    from hikaye_ink import figure_gun_ana
    hx, hy = figure_gun_ana(S, cx, cy, s, layer_body=layer, body_dens=dens, braids=False, halo=halo, wind=wind)
    return hx, hy


def erlik_figure(S, x, y, s):
    """Erlik Han: köklerden yükselen dev boynuzlu kütle; demir taç, sakal örgüleri, kor gözler. y: göğüs hizası."""
    hx, hy = x, y - s * 0.55
    body = [(x - s * 1.6, y + s * 1.6), (x - s * 1.35, y + s * 0.4), (x - s * 0.95, y - s * 0.05), (x - s * 0.42, y - s * 0.22), (x - s * 0.2, y - s * 0.4),
            (hx - s * 0.2, hy - s * 0.05), (hx - s * 0.16, hy - s * 0.34), (hx, hy - s * 0.42), (hx + s * 0.16, hy - s * 0.34), (hx + s * 0.2, hy - s * 0.05),
            (x + s * 0.2, y - s * 0.4), (x + s * 0.42, y - s * 0.22), (x + s * 0.95, y - s * 0.05), (x + s * 1.35, y + s * 0.4), (x + s * 1.6, y + s * 1.6)]
    m = S.path_mask(body)
    S.wash(m, dens=0.95, blur=6, bleed=0.65, gran=0.45, seed=401)
    # omuz kürkü / zırh: kuru fırça darbeleri
    rs = np.random.default_rng(402)
    for i in range(36):
        a = rs.uniform(-1, 1)
        px = x + a * s * 1.25
        py = y + abs(a) * s * 0.25 - s * 0.1
        S.stroke([(px, py), (px + a * s * 0.08, py + s * 0.18), (px + a * s * 0.14 + rs.uniform(-8, 8), py + s * 0.38)], s * 0.05, load=1.0, dry=0.8, taper=(0.1, 0.9))
    # boynuzlar: koç boynuzu gibi dışa kıvrılan, kalın kuru fırça
    for side in (-1, 1):
        b = (hx + side * s * 0.14, hy - s * 0.28)
        pts = [b, (b[0] + side * s * 0.35, b[1] - s * 0.4), (b[0] + side * s * 0.8, b[1] - s * 0.38), (b[0] + side * s * 0.95, b[1] - s * 0.05),
               (b[0] + side * s * 0.78, b[1] + s * 0.12)]
        S.stroke(pts, s * 0.16, load=1.0, dry=0.45, taper=(0.02, 0.85))
        for k in range(6):
            t = 0.15 + k * 0.13
            q = catmull(pts, 8)[int(t * (len(catmull(pts, 8)) - 1))]
            S.stroke([(q[0] - s * 0.05, q[1] - s * 0.03), (q[0] + s * 0.05, q[1] + s * 0.03)], s * 0.02, load=0.6, dry=0.8)
    # demir taç: dokuz diş
    for k in range(9):
        a = -math.pi / 2 + (k - 4) * 0.16
        S.stroke([(hx + math.cos(a) * s * 0.17, hy - s * 0.18 + math.sin(a) * s * 0.17 + s * 0.1), (hx + math.cos(a) * s * 0.28, hy - s * 0.18 + math.sin(a) * s * 0.28)],
                 s * 0.035, load=1.0, dry=0.3, taper=(0.1, 0.9))
    # gözler: kor
    for side in (-1, 1):
        S.stroke([(hx + side * s * 0.11, hy - s * 0.02), (hx + side * s * 0.04, hy + s * 0.02)], s * 0.035, layer='R', load=1.0, dry=0.1, taper=(0.3, 0.1))
        sun_glow(S, hx + side * s * 0.075, hy, s * 0.05, col=(1.0, 0.25, 0.1), k=1.4)
    # sakal örgüleri: aşağı uzanan iki koyu örgü
    for side in (-1, 1):
        braid(S, [(hx + side * s * 0.06, hy + s * 0.18), (hx + side * s * 0.1, hy + s * 0.45), (hx + side * s * 0.05, hy + s * 0.7)], s * 0.07, layer='D')
    return hx, hy


def wing(S, x, y, s, side, seed):
    """Umay'ın kanadı: kök (x, y), side=-1 sol / +1 sağ. Üç sıra tüy: örtü tüyleri kısa, uçuş tüyleri uzun; soluk
    turkuaz yıkama, koyu sap, uçlarda altın kenar."""
    rs = np.random.default_rng(seed)
    for row, (n, ln0, ln1, wd, k) in enumerate(((11, 1.0, 0.62, 0.11, 0.55), (9, 0.62, 0.4, 0.09, 0.62), (7, 0.36, 0.22, 0.08, 0.7))):
        for i in range(n):
            t = i / max(1, n - 1)
            a = -0.95 + t * 1.25 + rs.uniform(-0.03, 0.03)
            ln = s * (ln0 + (ln1 - ln0) * t) * rs.uniform(0.95, 1.05)
            base = (x + side * s * (0.08 + 0.06 * row) * math.cos(a * 0.5), y + s * 0.05 * t + s * row * 0.03)
            tip = (base[0] + side * math.cos(a) * ln, base[1] + math.sin(a) * ln * 0.8 + s * 0.25 * t)
            mid = ((base[0] + tip[0]) / 2 + side * s * 0.02, (base[1] + tip[1]) / 2 - s * 0.05 * (1 - t))
            m = S.stroke([base, mid, tip], s * wd * rs.uniform(0.9, 1.1), load=0.9, dry=0.3, taper=(0.05, 0.75), ret=True)
            S.put(m, 'C', col=TEAL if row == 0 else (0.55, 0.76, 0.78), k=k)
            S.stroke([base, mid, tip], s * 0.008, load=0.55, dry=0.5, taper=(0.1, 0.9))
            if row == 0:
                m2 = S.stroke([mid, tip], s * 0.012, load=1.0, dry=0.55, taper=(0.3, 0.9), ret=True)
                S.put(m2, 'G', k=0.6)
    # kanat kemiği: kalın kuru fırça
    S.stroke([(x, y), (x + side * s * 0.4, y - s * 0.28), (x + side * s * 0.95, y - s * 0.4)], s * 0.035, load=0.95, dry=0.45, taper=(0.05, 0.9))


def shear_blade(S, piv, ang, ln, w, side):
    """Kırkı bıçağı: yaydan (piv) uca uzun üçgen; kesici kenar ince kâğıt pırıltısı."""
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa * side, ca * side
    tip = (piv[0] + ca * ln, piv[1] + sa * ln)
    pts = [piv, (piv[0] + ca * ln * 0.35 + nx * w, piv[1] + sa * ln * 0.35 + ny * w), (piv[0] + ca * ln * 0.7 + nx * w * 0.7, piv[1] + sa * ln * 0.7 + ny * w * 0.7), tip,
           (piv[0] + ca * ln * 0.5, piv[1] + sa * ln * 0.5)]
    S.wash(S.path_mask(pts, smooth=False), dens=1.0, blur=0.8, bleed=0.3, gran=0.15)
    S.stroke([(piv[0] + ca * ln * 0.1, piv[1] + sa * ln * 0.1), tip], w * 0.08, load=1.0, dry=0.1, layer='G', taper=(0.1, 0.9))
    return tip


PARCA = os.path.join(__import__('tempfile').gettempdir(), 'sinema43_meta')


def save_meta(shot):
    """Çekim başına parça (paralel üretim için); --birlestir hepsini katmanlar.json'a yazar."""
    os.makedirs(PARCA, exist_ok=True)
    json.dump(META, open(os.path.join(PARCA, shot + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)


def birlestir():
    p = os.path.join(OUT, 'katmanlar.json')
    old = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
    for f in sorted(os.listdir(PARCA)):
        old.update(json.load(open(os.path.join(PARCA, f), encoding='utf-8')))
    json.dump(dict(sorted(old.items())), open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


# ====================================================================== AÇILIŞ ÇEKİMLERİ
def c_kayin():
    """1 · Ulu Kayın: üç kat dünya. Gök (ay, yıldız tozu), yer (ufuk), yeraltı (kökler). Kamera aydan aşağı süzülür."""
    S = yeni(4301)
    ink_sky(S, 0.62, 0.18, 11, 0, 900)
    S.grad_wash(980, 1440, 0.0, 0.92, seed=12, gran=0.55, wobble=90)
    moon(S, 1880, 300, 92)
    stars(S, 260, (0, 0, W, 760), 13)
    mountains(S, [(0, 960), (240, 900), (420, 930), (700, 840), (980, 905), (1250, 870), (1520, 925), (1780, 850), (2050, 915), (2300, 880), (2560, 930)], 1060, dens=0.3, seed=14)
    mountains(S, [(0, 1010), (380, 970), (760, 1000), (1200, 960), (1600, 995), (2000, 965), (2560, 1000)], 1100, dens=0.22, seed=15, texture=False)
    S.mist(1000, 60, 0.85, seed=16)
    arka(S, 'kayin_arka', NIGHT)
    # orta: Ulu Kayın (üçler kuralı: sol üçte bire yakın), kökler yeraltına
    T = yeni(4302)
    tree(T, 1100, 1040, 860, spread=1.2, seed=17, load=1.0, root_depth=380)
    T.stroke([(1100, 1300), (1094, 1040), (1108, 760), (1098, 480), (1110, 260)], 7, load=1.0, dry=0.55, layer='G', taper=(0.1, 0.4))
    # kökler arasında üç kat: yeraltında soluk kor damarları
    rs = np.random.default_rng(171)
    for j in range(70):
        a = rs.uniform(-math.pi, 0)
        r = rs.uniform(120, 420)
        T.leaf(1100 + math.cos(a) * r * 1.5, 380 + math.sin(a) * r * 0.55, rs.uniform(18, 40), rs.uniform(-math.pi, 0.2), load=0.8)
    katman(T, 'kayin_agac')
    # ön: sol altta kaya + otlar, sağ üstte sarkan dal (odak dışı çerçeve)
    F = yeni(4303)
    rock(F, 260, 1400, 420, 170, 18)
    grass_tuft(F, 140, 1300, 260, 18, 19, lean=0.3)
    grass_tuft(F, 520, 1330, 200, 12, 20, lean=0.2)
    grass_tuft(F, 2380, 1440, 280, 16, 21, lean=-0.3)
    F.stroke([(2600, 40), (2300, 120), (2050, 230), (1900, 300)], 46, load=1.0, dry=0.5, taper=(0.02, 0.95))
    rs = np.random.default_rng(22)
    for j in range(40):
        F.leaf(rs.uniform(1900, 2560), rs.uniform(60, 360), rs.uniform(26, 56), rs.uniform(-math.pi, 0.4), load=0.9)
    katman(F, 'kayin_on', glow=False)


def c_gunana():
    """2 · Gün Ana Kaf'ın ardından doğar: büyük güneş haresi, figür ortada; beş örgü motorda canlı ışık şeritleri."""
    S = yeni(4311)
    yy = np.arange(H, dtype=np.float32)[:, None] * np.ones((1, W), np.float32)
    S.put(np.clip(1 - yy / 700, 0, 1) * 0.3, 'C', col=INDIGO)
    S.put(np.exp(-((yy - 820) / 260) ** 2) * 0.55, 'C', col=ROSE)
    S.put(np.exp(-((yy - 1000) / 160) ** 2) * 0.7, 'C', col=SAFFRON)
    sun_glow(S, 1280, 640, 760, col=(1.0, 0.72, 0.38), k=0.7)
    S.erase(S.ellipse_mask(1280, 640, 330, 330), 0.0)
    S.enso(1280, 640, 360, 34, load=1.0, dry=0.42, layer='G', a0=-2.2, span=5.7)
    S.enso(1280, 640, 430, 10, load=0.7, dry=0.75, layer='G', a0=0.9, span=4.0)
    mountains(S, [(0, 1080), (300, 1000), (560, 1040), (900, 960), (1280, 1010), (1640, 950), (1960, 1030), (2280, 980), (2560, 1040)], 1300, dens=0.22, blur=10, seed=24, texture=False)
    arka(S, 'gunana_arka', DAWN)
    G = yeni(4312)
    gun_ana43(G, 1280, 860, 300, dens=0.9, halo=False, wind=0.4)
    katman(G, 'gunana_figur', krp=True)
    F = yeni(4313)
    mountains(F, [(0, 1150), (220, 1020), (420, 1090), (640, 960), (860, 1080), (1020, 1150), (1180, 1200), (1400, 1190), (1560, 1100), (1760, 990), (1960, 1080),
                  (2200, 980), (2400, 1060), (2560, 1000)], 1440, dens=0.75, blur=3.5, seed=21)
    mountains(F, [(0, 1260), (400, 1200), (800, 1250), (1300, 1290), (1800, 1230), (2200, 1270), (2560, 1220)], 1440, dens=0.5, blur=8, seed=22, texture=False)
    F.mist(1190, 40, 0.6, seed=23)
    katman(F, 'gunana_on', glow=False)


def c_toren():
    """3 · Tan töreni: Ulu Kayın'ın dibinde tören ateşi (motorda canlı alev), davulu kaldırmış tan bekçisi Bengü;
    ardında dilek çaputlu direkler. Ön düzlemde çaput ipi ve otlar (odak çekimi önden Bengü'ye)."""
    S = yeni(4321)
    ink_sky(S, 0.72, 0.5, 31, 0, 1440, wobble=90)
    sun_glow(S, 1380, 1120, 520, col=(1.0, 0.5, 0.2), k=0.45)
    S.put(ndimage.gaussian_filter(S.ellipse_mask(1300, 1180, 620, 200), 60) * 0.3, 'C', col=EMBER)
    # Ulu Kayın'ın dev gövde dibi solda (çerçeve dışına taşar) ve kökleri
    S.wash(S.path_mask([(0, 0), (520, 0), (560, 600), (640, 1000), (820, 1180), (0, 1240)]), dens=0.9, blur=6, bleed=0.6, gran=0.5, seed=33)
    for k in range(6):
        S.stroke([(380 + k * 40, 0), (440 + k * 30, 500), (520 + k * 40, 900), (700 + k * 120, 1200)], 26 - k * 3, load=0.9, dry=0.7, taper=(0.02, 0.8))
    for k in range(4):
        S.stroke([(560, 1080 + k * 24), (760 + k * 60, 1150 + k * 20), (880 + k * 110, 1190 + k * 34), (1000 + k * 150, 1250 + k * 40)], 34 - k * 6, load=1.0, dry=0.55, taper=(0.05, 0.9))
    # zemin
    S.grad_wash(1180, 1440, 0.0, 0.9, seed=34, gran=0.5)
    # dilek direkleri ve çaputlar (uzakta)
    for i, x0 in enumerate((1850, 2120, 2380)):
        S.stroke([(x0, 1220), (x0 + 6, 800 - i * 40)], 12, load=0.6, dry=0.6, taper=(0.1, 0.2))
        for j in range(4):
            yy0 = 840 - i * 40 + j * 60
            m = S.stroke([(x0, yy0), (x0 + 40, yy0 + 20), (x0 + 90, yy0 + 50)], 14, load=0.8, dry=0.3, ret=True)
            S.put(m, 'C', col=list(BRAID_COLS.values())[(i + j) % 5], k=0.55)
    arka(S, 'toren_arka', NIGHT)
    B = yeni(4322)
    bengu43(B, 1640, 1230, 520, pose='davul')
    katman(B, 'toren_bengu', krp=True)
    F = yeni(4323)
    # çaput ipi üstte (salınır) — renkli bezler
    rope = [(-40, 120), (600, 230), (1300, 260), (2000, 200), (2600, 90)]
    F.stroke(rope, 10, load=0.9, dry=0.3, taper=(0.0, 0.0))
    R = catmull(rope, 12)
    for i in range(0, len(R), 4):
        p = R[i]
        c = list(BRAID_COLS.values())[(i // 4) % 5]
        m = F.stroke([p, (p[0] + 14, p[1] + 70), (p[0] + 4, p[1] + 150)], 40, load=0.9, dry=0.4, taper=(0.05, 0.8), ret=True)
        F.put(m, 'C', col=c, k=0.8)
        F.put(m * 0.25, 'D')
    grass_tuft(F, 200, 1440, 380, 22, 35, lean=0.25)
    grass_tuft(F, 2450, 1440, 300, 16, 36, lean=-0.2)
    katman(F, 'toren_on', glow=False)


def c_erlik():
    """4 · Erlik köklerden çıkar: kara gece, köklerde kor yarıkları; dev boynuzlu kütle yükselir (oyuncu)."""
    S = yeni(4331)
    ink_sky(S, 0.86, 0.95, 41, 0, 1440, gran=0.65, wobble=120)
    # yarık zemin: kor damarları
    rs = np.random.default_rng(42)
    for i in range(14):
        x0 = rs.uniform(300, 2260)
        pts = [(x0, 1440)]
        for k in range(5):
            pts.append((pts[-1][0] + rs.uniform(-90, 90), pts[-1][1] - rs.uniform(40, 90)))
        m = S.stroke(pts, rs.uniform(5, 12), load=1.0, dry=0.5, taper=(0.1, 0.9), ret=True)
        S.put(m, 'R', k=0.85)
        S.E += ndimage.gaussian_filter(m, 6)[..., None] * np.array([1.0, 0.3, 0.08], np.float32) * 1.6
    arka(S, 'erlik_arka', (0.6, 0.6, 0.66))
    E = yeni(4332)
    erlik_figure(E, 1280, 900, 520)
    katman(E, 'erlik_figur', krp=True)
    F = yeni(4333)
    # kökler: ön planda yarılan dev kökler (koyu), kor kenarlı
    for k in range(7):
        side = -1 if k % 2 == 0 else 1
        x0 = 1280 + side * (200 + k * 150)
        F.stroke([(x0, 1500), (x0 - side * 80, 1250), (x0 - side * 220, 1100), (x0 - side * 300, 980)], 70 - k * 6, load=1.0, dry=0.55, taper=(0.02, 0.9))
        m = F.stroke([(x0 + 10, 1480), (x0 - side * 70, 1250), (x0 - side * 210, 1110)], 8, load=1.0, dry=0.6, taper=(0.1, 0.9), ret=True)
        F.put(m, 'R', k=0.7)
    F.grad_wash(1300, 1440, 0.0, 0.95, seed=43)
    katman(F, 'erlik_on')


def c_kirki():
    """5 · Kara kırkı: Erlik'in eli iki bıçaklı kırkıyı kapar; beş örgü (motorda canlı) tek tek kesilir.
    Bıçaklar ayrı oyuncu (motor yay çevresinde döndürür)."""
    S = yeni(4341)
    ink_sky(S, 0.9, 0.8, 51, 0, 1440, gran=0.6)
    sun_glow(S, 1500, 600, 700, col=(1.0, 0.7, 0.35), k=0.35)
    S.erase(sun_glow(S, 1500, 600, 520, col=(0, 0, 0), k=0.0), 0.35)
    S.enso(1500, 600, 520, 22, load=0.8, dry=0.6, layer='G', a0=-1.0, span=4.8)
    arka(S, 'kirki_arka', (0.62, 0.6, 0.62))
    for side, nm in ((1, 'kirki_ust'), (-1, 'kirki_alt')):
        K = yeni(4342 + side)
        piv = (420, 760)
        ang = -0.06 * side
        # yay (U kemer) yalnızca üst parçada
        if side == 1:
            K.stroke([(piv[0] + 20, piv[1] - 40), (piv[0] - 160, piv[1] - 60), (piv[0] - 240, piv[1]), (piv[0] - 160, piv[1] + 60), (piv[0] + 20, piv[1] + 40)],
                     40, load=1.0, dry=0.35, taper=(0.1, 0.1))
        shear_blade(K, (piv[0] + 20, piv[1] - side * 30), ang, 1150, 95, side)
        # el: Erlik'in pençesi tutamakta (üst parçada)
        if side == 1:
            K.stroke([(piv[0] - 520, piv[1] - 520), (piv[0] - 300, piv[1] - 300), (piv[0] - 80, piv[1] - 170)], 150, load=1.0, dry=0.55, taper=(0.0, 0.3))
            for k in range(4):
                K.stroke([(piv[0] - 90 + k * 40, piv[1] - 170), (piv[0] - 70 + k * 44, piv[1] - 90), (piv[0] - 100 + k * 40, piv[1] + 10)], 22, load=1.0, dry=0.4, taper=(0.05, 0.95))
        katman(K, nm, krp=True)
    META['kirki_ust']['pivot'] = [440, 760]
    META['kirki_alt']['pivot'] = [440, 760]


def c_zincir():
    """6 · Dokuz gecenin zinciri: toprağın katmanları (yeraltı kesiti); Gün Ana ışığı sönerek aşağı çekilir."""
    S = yeni(4351)
    ink_sky(S, 0.55, 0.95, 61, 0, 1440, gran=0.6)
    for k, y in enumerate((300, 560, 800, 1020, 1240)):
        mountains(S, [(0, y + 30), (500, y - 20), (900, y + 40), (1400, y - 10), (1900, y + 30), (2560, y - 20)], y + 260, dens=0.18 + k * 0.08, blur=8, seed=62 + k, texture=k % 2 == 0)
    # taşlaşmış kökler yatay
    for k in range(5):
        S.stroke([(-50, 420 + k * 220), (700, 380 + k * 230), (1500, 440 + k * 210), (2600, 400 + k * 220)], 10, load=0.5, dry=0.8, taper=(0.0, 0.0))
    arka(S, 'zincir_arka', (0.66, 0.64, 0.66))
    G = yeni(4352)
    gun_ana43(G, 1280, 620, 230, dens=0.75, halo=True, wind=0.15, layer='G')
    katman(G, 'zincir_gunana', krp=True)
    F = yeni(4353)
    for side in (-1, 1):
        for k in range(4):
            x0 = 1280 + side * (760 + k * 120)
            F.stroke([(x0, -20), (x0 - side * 90, 500), (x0 + side * 40, 1000), (x0 - side * 60, 1460)], 60 - k * 10, load=1.0, dry=0.6, taper=(0.02, 0.4))
    katman(F, 'zincir_on', glow=False)


def c_dusus():
    """7 · Bengü düşer: kül grisi gök, aşağıda sönmüş tören ateşinin duman sütunu. Bengü ayrı oyuncu (döne döne düşer)."""
    S = yeni(4361)
    ink_sky(S, 0.5, 0.75, 71, 0, 1440, gran=0.6, wobble=100)
    for k in range(5):
        S.stroke([(1100 + k * 60, 1460), (1060 + k * 80, 1100), (1150 + k * 40, 760), (1040 + k * 90, 300), (1180 + k * 50, -40)], 90 - k * 12, load=0.28, dry=0.85, taper=(0.1, 0.9))
    S.wash(S.ellipse_mask(1200, 1420, 380, 70), dens=0.6, blur=14, bleed=0.3, gran=0.6, layer='C', col=EMBER, seed=72)
    sun_glow(S, 1200, 1410, 220, col=(1.0, 0.42, 0.12), k=0.7)
    arka(S, 'dusus_arka', (0.72, 0.71, 0.72))
    B = yeni(4362)
    bengu43(B, 1280, 1000, 560, pose='arka')   # motor döndürür: baş aşağı savrulan beden
    katman(B, 'dusus_bengu', krp=True)
    F = yeni(4363)
    # kırık kam davulu ve kılıç (ön düzlem, alt köşeler)
    F.enso(2150, 1330, 150, 24, load=1.0, dry=0.45, squash=0.45, a0=-2.6, span=5.0)
    F.stroke([(2050, 1310), (2150, 1350), (2230, 1320)], 12, load=0.9, dry=0.3)
    F.stroke([(220, 1300), (500, 1230), (820, 1190)], 16, load=1.0, dry=0.1, taper=(0.02, 0.95))
    F.stroke([(200, 1290), (250, 1330)], 22, load=1.0, dry=0.1)
    katman(F, 'dusus_on', glow=False)


def c_umay():
    """8 · Umay Ana ruh kuşunu tutar: soluk turkuaz-kâğıt gök, Ulu Kayın dalı; dev kanatlar iki yandan kapanır
    (iki oyuncu), ortada motorda canlı altın ruh kuşu."""
    S = yeni(4371)
    ink_sky(S, 0.12, 0.3, 81, 0, 1440, gran=0.5)
    S.put(np.ones((H, W), np.float32) * 0.18, 'C', col=TEAL)
    sun_glow(S, 1280, 700, 300, col=(1.0, 0.85, 0.5), k=0.7)
    S.stroke([(-40, 200), (500, 240), (900, 360), (1150, 500)], 54, load=1.0, dry=0.5, taper=(0.02, 0.95))
    S.stroke([(500, 240), (580, 130), (680, 60)], 22, load=1.0, dry=0.5, taper=(0.05, 0.9))
    rs = np.random.default_rng(82)
    for j in range(46):
        S.leaf(rs.uniform(80, 1100), rs.uniform(80, 480), rs.uniform(20, 42), rs.uniform(-math.pi, 0.3), load=0.8)
    arka(S, 'umay_arka', PALE)
    for side, nm in ((-1, 'umay_kanat_sol'), (1, 'umay_kanat_sag')):
        K = yeni(4372 + side)
        wing(K, 1280 + side * 80, 700, 1000, side, 83 + side)
        katman(K, nm, krp=True)
        META[nm]['pivot'] = [1280 + side * 80, 700]
    U = yeni(4375)
    # Umay'ın yüzü: kanatların ortasında, kâğıda emilmiş soluk portre (yalnızca göz kapakları, kaş, dudak fırçası)
    hx, hy = 1280, 480
    U.wash(U.ellipse_mask(hx, hy, 120, 150), dens=0.12, blur=20, bleed=0.2, gran=0.3, layer='C', col=TEAL)
    for side in (-1, 1):
        U.stroke([(hx + side * 70, hy - 10), (hx + side * 40, hy + 4), (hx + side * 14, hy - 2)], 7, load=0.7, dry=0.3, taper=(0.2, 0.6))
        U.stroke([(hx + side * 80, hy - 50), (hx + side * 50, hy - 62), (hx + side * 16, hy - 52)], 6, load=0.5, dry=0.5, taper=(0.2, 0.6))
    U.stroke([(hx - 22, hy + 82), (hx, hy + 88), (hx + 22, hy + 82)], 6, load=0.5, dry=0.3, layer='R', taper=(0.3, 0.3))
    for k in range(8):
        a = -math.pi / 2 + (k - 3.5) * 0.25
        U.stroke([(hx + math.cos(a) * 150, hy + math.sin(a) * 170), (hx + math.cos(a) * 260, hy + math.sin(a) * 300 - 40)], 10, load=0.5, dry=0.7, layer='G')
    katman(U, 'umay_yuz', krp=True)


def c_yol():
    """9 · Yol aşağı iner: ay, kök kemeri, aşağıda beş uzak örgü ışığı; sırtı dönük Bengü kemerin ağzında."""
    S = yeni(4381)
    ink_sky(S, 0.55, 0.97, 91, 0, 1440, gran=0.55, wobble=60)
    moon(S, 1900, 260, 100, halo=0.4)
    stars(S, 120, (0, 0, W, 600), 92, k=0.5)
    S.erase(ndimage.gaussian_filter(S.path_mask([(900, 1440), (960, 900), (1120, 700), (1280, 660), (1440, 700), (1600, 900), (1660, 1440)]), 30), 0.22)
    for i in range(9):
        y = 900 + i * 62
        w = 220 + i * 60
        S.stroke([(1280 - w / 2, y), (1280, y + 8), (1280 + w / 2, y)], 14 - i, load=0.55, dry=0.75, taper=(0.3, 0.3))
    # aşağıda beş uzak örgü ışığı (yeraltında bekleyen bekçiler)
    for i, c in enumerate(('al', 'ak', 'gok', 'sari', 'altin')):
        x = 1080 + i * 100 + (i % 2) * 20
        y = 1340 - (i % 3) * 30
        sun_glow(S, x, y, 26, col=BRAID_COLS[c], k=1.6)
        S.dots([(x, y, 6)], 0, layer='C', col=BRAID_COLS[c], k=0.9)
    S.mist(1250, 80, 0.45, seed=93)
    arka(S, 'yol_arka', NIGHT)
    B = yeni(4382)
    bengu43(B, 1280, 900, 300, pose='arka')
    katman(B, 'yol_bengu', krp=True)
    F = yeni(4383)
    for side in (-1, 1):
        for k in range(6):
            x0 = 1280 + side * (360 + k * 70)
            F.stroke([(x0, -20), (x0 - side * 50, 380), (1280 + side * (220 + k * 40), 760), (1280 + side * (330 + k * 60), 1460)], 52 - k * 6, load=1.0, dry=0.55,
                     taper=(0.02, 0.6))
    katman(F, 'yol_on', glow=False)


def c_baslik():
    """10 · Başlık: kâğıt, tan rengi yıkama; "Kut'un Yolu" fırça yazısı (ayrı oyuncu, motor soldan sağa yazar), altın
    enso (ayrı, motor çember boyunca çizer), kızıl mühür."""
    import skia
    S = yeni(4391)
    S.grad_wash(0, 1440, 0.08, 0.3, seed=101, gran=0.5)
    S.wash(S.ellipse_mask(1280, 700, 1100, 420), dens=0.12, blur=60, bleed=0.4, gran=0.6, layer='C', col=SAFFRON, seed=102)
    arka(S, 'baslik_arka', (0.95, 0.9, 0.82))
    # yazı: KaushanScript ile skia'da yaz, mürekkep dokusu ver (kuru fırça kopukları + ıslak kenar)
    T = yeni(4392)
    font_p = os.path.join(ROOT, 'assets', 'ui', 'fonts', 'KaushanScript-Regular.ttf')
    tf = skia.Typeface.MakeFromFile(font_p)

    def fn(c):
        f = skia.Font(tf, 330)
        txt = "Kut'un Yolu"
        wdt = f.measureText(txt)
        p = skia.Paint(AntiAlias=True, Color=skia.ColorWHITE)
        c.drawString(txt, 1280 - wdt / 2, 790, f, p)
    m = T.raster(fn)
    ys, xs = np.where(m > 0.3)
    m = np.roll(m, (int(700 - (ys.min() + ys.max()) / 2), int(1280 - (xs.min() + xs.max()) / 2)), axis=(0, 1))
    n = fbm(H, W, 6.0, 4393, octaves=3)
    streak = ndimage.gaussian_filter1d(np.random.default_rng(4394).random((H, W)).astype(np.float32), 9, axis=1)
    dry = np.clip((streak - 0.47) * 9, 0, 1) * (1 - np.clip(ndimage.gaussian_filter(m, 6) * 1.3, 0, 1)) * 0.0
    mm = np.clip(ndimage.gaussian_filter(m, 1.2) * (0.86 + 0.24 * n) - 0.15 * np.clip((streak - 0.5) * 6, 0, 1) * m, 0, 1)
    ring = np.clip(ndimage.gaussian_filter(m, 1.5) - ndimage.gaussian_filter(m, 5), 0, 1)
    T.put(np.clip(mm + ring * 0.4, 0, 1), 'D')
    T.splatter(1900, 640, 30, 40, size=(2, 7), seed=4395)
    T.splatter(700, 820, 20, 30, size=(2, 6), seed=4396)
    katman(T, 'baslik_yazi', krp=True, glow=False)
    E = yeni(4397)
    E.enso(1280, 700, 520, 46, load=1.0, dry=0.5, layer='G', a0=-2.4, span=5.9)
    katman(E, 'baslik_enso', krp=True)
    M = yeni(4398)
    seal(M, 2010, 930, 96, 43)
    katman(M, 'baslik_muhur', krp=True, glow=False)


# ====================================================================== SON ÇEKİMLERİ
def c_son_or():
    """S1 · Beş örgüyü avucunda örer: diz çökmüş Bengü (kısa saç), ışık önünde; örgüler motorda ellerine akar."""
    S = yeni(4401)
    ink_sky(S, 0.7, 0.88, 111, 0, 1440, gran=0.55)
    sun_glow(S, 1400, 700, 600, col=(1.0, 0.7, 0.35), k=0.6)
    S.erase(sun_glow(S, 1400, 700, 420, col=(0, 0, 0), k=0.0), 0.45)
    S.grad_wash(1200, 1440, 0.0, 0.6, seed=112)
    arka(S, 'sonor_arka', NIGHT)
    B = yeni(4402)
    bengu43(B, 1140, 1300, 520, pose='diz')
    katman(B, 'sonor_bengu', krp=True)


def c_son_kir():
    """S2 · Zincir kırılır (zincir motorda; burada yalnızca karanlık zemin ve ışığın yarığı)."""
    S = yeni(4411)
    ink_sky(S, 0.8, 0.9, 121, 0, 1440, gran=0.6)
    for k in range(6):
        S.stroke([(-40, 300 + k * 180), (900, 280 + k * 190), (1700, 320 + k * 170), (2600, 290 + k * 185)], 8, load=0.4, dry=0.85, taper=(0, 0))
    arka(S, 'sonkir_arka', (0.62, 0.6, 0.64), glow=False)


def c_son_yuksel():
    """S3 · Gün Ana köklerden yükselir: dev gövde dikey; dallar altınla tutuşur (ışık katmanı ayrı belirir)."""
    S = yeni(4421)
    ink_sky(S, 0.35, 0.8, 131, 0, 1440, gran=0.5)
    sun_glow(S, 1280, 420, 600, col=(1.0, 0.72, 0.36), k=0.6)
    S.erase(sun_glow(S, 1280, 420, 480, col=(0, 0, 0), k=0.0), 0.5)
    arka(S, 'sonyuksel_arka', NIGHT)
    T = yeni(4422)
    tree(T, 1280, 1560, 1600, spread=1.3, seed=132, load=1.0, gold_leaves=34, roots=False)
    katman(T, 'sonyuksel_agac')
    G = yeni(4423)
    gun_ana43(G, 1280, 860, 220, dens=0.8, halo=True, wind=0.3, layer='G')
    katman(G, 'sonyuksel_gunana', krp=True)


def c_son_tan():
    """S4 · Ve tan söktü: ufukta Ulu Kayın (açılışın ağacıyla aynı biçim, altın yapraklı), güneş ardından doğar."""
    S = yeni(4431)
    yy = np.arange(H, dtype=np.float32)[:, None] * np.ones((1, W), np.float32)
    S.put(np.clip(1 - yy / 900, 0, 1) * 0.35, 'C', col=INDIGO)
    S.put(np.exp(-((yy - 760) / 240) ** 2) * 0.7, 'C', col=ROSE)
    S.put(np.exp(-((yy - 900) / 140) ** 2) * 0.85, 'C', col=SAFFRON)
    mountains(S, [(0, 1000), (500, 960), (900, 990), (1400, 950), (1900, 985), (2560, 960)], 1100, dens=0.25, blur=10, seed=141, texture=False)
    arka(S, 'sontan_arka', DAWN)
    G = yeni(4432)
    G.put(G.ellipse_mask(1280, 1000, 360, 360) * 0.9, 'C', col=(0.98, 0.5, 0.2))
    sun_glow(G, 1280, 1000, 600, col=(1.0, 0.62, 0.3), k=0.9)
    G.enso(1280, 1000, 372, 24, load=1.0, dry=0.45, layer='G', a0=-3.1, span=3.4)
    katman(G, 'sontan_gunes', krp=True)
    F = yeni(4433)
    hill = [(0, 1060), (360, 1010), (700, 1040), (1000, 1000), (1280, 1015), (1560, 990), (1900, 1035), (2200, 1000), (2560, 1040)]
    F.put(ndimage.gaussian_filter(F.path_mask(hill + [(2560, 1440), (0, 1440)]), 2.0) * 0.93, 'D')   # düz, sakin tepe (tanesiz)
    F.stroke(hill, 10, load=0.9, dry=0.7, taper=(0.0, 0.0))
    tree(F, 1280, 1015, 760, spread=1.25, seed=143, load=1.0, gold_leaves=40, roots=False)
    katman(F, 'sontan_on')


def c_son_dal():
    """S5 · Dalda oturan Bengü; bir yanda güneş, öbür yanda ince hilal."""
    S = yeni(4441)
    S.put(np.ones((H, W), np.float32) * 0.16, 'C', col=SAFFRON)
    sun_glow(S, 1840, 600, 480, col=(1.0, 0.68, 0.32), k=0.8)
    S.put(S.ellipse_mask(1840, 600, 230, 230) * 0.8, 'C', col=(0.98, 0.55, 0.25))
    S.enso(1840, 600, 240, 14, load=0.9, dry=0.5, layer='G', a0=-2.0, span=5.5)
    S.enso(420, 240, 64, 13, load=0.6, dry=0.4, a0=1.2, span=2.6)
    arka(S, 'sondal_arka', DAWN)
    F = yeni(4442)
    F.stroke([(-60, 1020), (480, 960), (1120, 935), (1600, 975), (2000, 1090)], 74, load=1.0, dry=0.5, taper=(0.02, 0.9))
    F.stroke([(800, 950), (900, 830), (1040, 750)], 24, load=1.0, dry=0.5, taper=(0.05, 0.9))
    rs = np.random.default_rng(144)
    for j in range(46):
        m = F.leaf(rs.uniform(480, 2080), rs.uniform(750, 1050), rs.uniform(20, 42), rs.uniform(-math.pi, 0.3), ret=True)
        F.put(m, 'G' if rs.random() < 0.6 else 'D', k=0.9)
    bengu43(F, 1250, 945, 190, pose='dal')
    katman(F, 'sondal_on')


# ====================================================================== ORTAK (kart / örgü / bölüm)
def c_kart():
    """Boss kartı ve örgü sahnesi: saydam yatay mürekkep bandı (oyun ardında görünür) + kâğıt lifli koyu yıkama."""
    S = yeni(4451)
    yy = np.arange(H, dtype=np.float32)[:, None] * np.ones((1, W), np.float32)
    n = fbm(H, W, 140.0, 4452, octaves=3)
    band = np.exp(-((yy - 720 + (n - 0.5) * 160) / 330) ** 4)
    S.wash(band, dens=0.92, blur=10, bleed=0.4, gran=0.55, seed=4453)
    # bandın iki ucunda kuru fırça kopukları
    rs = np.random.default_rng(4454)
    for i in range(30):
        y = rs.uniform(420, 1020)
        x0 = rs.uniform(-100, 200) if i % 2 == 0 else rs.uniform(2360, 2660)
        x1 = x0 + (rs.uniform(400, 900) if i % 2 == 0 else -rs.uniform(400, 900))
        S.stroke([(x0, y), ((x0 + x1) / 2, y + rs.uniform(-10, 10)), (x1, y + rs.uniform(-20, 20))], rs.uniform(14, 40), load=0.8, dry=0.8, taper=(0.05, 0.9))
    katman(S, 'kart_bant', glow=False)


RENDER = {'kayin': c_kayin, 'gunana': c_gunana, 'toren': c_toren, 'erlik': c_erlik, 'kirki': c_kirki, 'zincir': c_zincir, 'dusus': c_dusus,
          'umay': c_umay, 'yol': c_yol, 'baslik': c_baslik, 'sonor': c_son_or, 'sonkir': c_son_kir, 'sonyuksel': c_son_yuksel, 'sontan': c_son_tan,
          'sondal': c_son_dal, 'kart': c_kart}


def onizleme(path, names):
    """Her çekimin katmanları tuvaldeki yerlerinde üst üste (motorun ilk karesine yakın) -> temas sayfası."""
    from PIL import Image
    meta = json.load(open(os.path.join(OUT, 'katmanlar.json'), encoding='utf-8'))
    tiles = []
    for nm in names:
        base = Image.new('RGBA', (W, H), (12, 12, 16, 255))
        for k, v in sorted(((k, v) for k, v in meta.items() if k.startswith(nm + '_')), key=lambda kv: kv[1].get('sira', 0)):
            im = Image.open(os.path.join(OUT, k + '.webp')).convert('RGBA')
            base.alpha_composite(im, tuple(v['ofs']))
            if v.get('isik'):
                g = Image.open(os.path.join(OUT, k + '_isik.webp')).convert('RGBA').resize((im.size[0], im.size[1]))
                arr = np.asarray(base).astype(np.float32)
                ga = np.asarray(g).astype(np.float32) / 255.0
                ox, oy = v['ofs']
                sub = arr[oy:oy + g.size[1], ox:ox + g.size[0], :3]
                sub += ga[:sub.shape[0], :sub.shape[1], :3] * ga[:sub.shape[0], :sub.shape[1], 3:4] * 255 * 0.3
                arr[oy:oy + g.size[1], ox:ox + g.size[0], :3] = np.clip(sub, 0, 255)
                base = Image.fromarray(arr.astype(np.uint8), 'RGBA')
        tiles.append(base.convert('RGB').resize((640, 360)))
    cols = 2
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (640 * cols, 360 * rows), 'black')
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * 640, (i // cols) * 360))
    sheet.save(path, quality=85)


def main(args):
    if args and args[0] == '--birlestir':
        birlestir()
        return
    if args and args[0] == '--onizleme':
        names = args[2:] or list(RENDER.keys())
        onizleme(args[1], names)
        return
    names = args or list(RENDER.keys())
    for n in names:
        import time
        t0 = time.time()
        META.clear()
        _SIRA[0] = 0
        RENDER[n]()
        save_meta(n)
        print(n, round(time.time() - t0, 1), 's')


if __name__ == '__main__':
    main(sys.argv[1:])
