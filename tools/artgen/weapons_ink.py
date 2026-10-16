"""weapons_ink: stil v2 "mürekkep-cel" silah atlası (çizgi roman; Shinobi: Art of Vengeance yönü).

Geometri v1 ile birebir (`weapons_myth.draw_item`: aynı eşya kimlikleri, kabza pivotları, dünya boyları); yalnızca
çizim yöntemi değişir. Hacim tuvali (WCanvas: yükseklik + normal + parça kimliği) `raster.SS` = 2 x TEXEL_V2/2
ince ızgarada rasterlanır, sonra bu modülün mürekkep-cel gölgelendiricisiyle boyanır ve 2x kutu küçültmeyle kenar
yumuşatılır:
  * düz taban + tek sert gölge tonu (ışığın tersindeki yüzeyler, gölge rampası mora kayar) + ışığa bakan pah/kenar
    için açık ton; metal ve taşlarda keskin, küçük beyaz parlama (yansıma), mat malzemede yok,
  * alttakine düşen gölge (siper kabzaya, bilezik sapa: yükseklik alanından ışık yönünde),
  * mürekkep (#15161d): dış silüet ışık yanında ince, gölge yanında (sağ alt) kalın; parçaların üst üste geldiği
    yerde ince iç çizgi (alttaki parçanın üstüne); kenar yumuşatma süper örneklemeden,
  * ahşap damarı, deri/ip sargı, süs ve malzeme desenleri v1 boyamasından (yalnızca renk), ışıyan damarlar düz parlak.

Yoğunluk: TEXEL_V2 = 4 doku pikseli / dünya birimi (v2 kamerası 2x yakın: 1080p'de 4 ekran pikseli / birim, 1:1).
Atlas: her eşyanın 11 malzemesi için ortak sıkı kırpma; raf paketleme ile 4096 genişliğinde sayfalar
(`assets/weapons/weapons_v2_<n>.png`, en çok 4096x8192; 16384 sınırının çok altında). Meta `weapons_v2.json`:
  {"texel": 6, "pages": [...], "items": {kimlik: {"pivot": [x, y] (kırpma içinde, v2 pikseli), "size": [w, h],
   "m": {malzeme: [sayfa, x, y]}}}}
Oyunda Data.weapon_sprite() (yalnızca --stil=v2 ve bu dosya varsa) doğrusal süzgeç + mipmap ile kullanır.

Kullanım: cd tools/artgen && python weapons_ink.py [--onizleme out.png] [--yalniz kimlik,kimlik] [--is N]
"""
import json
import math
import os
import sys
import time

import numpy as np
from PIL import Image
from scipy import ndimage

import raster

TEXEL_V2 = 4
OVERS = 2                       # süper örnekleme
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'assets', 'weapons')
INK = np.array([0x15, 0x16, 0x1d], float) / 255.0
LIGHT = np.array([-0.55, -0.72, 0.5])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
SHADOW2D = np.array([0.6, 0.8])  # gölge yanı (sağ alt)


def _setup():
    import weapons_myth as wm
    raster.SS = wm.TEX and (TEXEL_V2 // wm.TEX) * OVERS  # mantıksal (v1 doku pikseli) başına fiziksel piksel
    return wm


def _shift(a, dy, dx, fill):
    return raster.shift(a, dy, dx, fill)


def ink_shade(c, mid):
    """Hacim tuvalini mürekkep-cel RGBA'ya çevirir (fiziksel ızgarada, önçarpılmamış)."""
    S = c.S
    k = S / OVERS                         # çıktı pikseli başına fiziksel piksel = OVERS; mantıksal px başına S
    A = c.mat >= 0
    H, W = A.shape
    n = c.n
    ndl = n[..., 0] * LIGHT[0] + n[..., 1] * LIGHT[1] + n[..., 2] * LIGHT[2]
    col = np.zeros((H, W, 3))
    emis_mask = np.zeros((H, W), bool)
    # alttakine düşen gölge: ışığa doğru birkaç piksel ötedeki yüzey belirgin yüksekse gölgede
    zz = np.where(A, c.z, -1e9)
    cast = np.zeros((H, W), bool)
    for d in (1.0, 2.0, 3.2):
        dx = int(round(-LIGHT[0] / np.hypot(LIGHT[0], LIGHT[1]) * d * S * 0.5))
        dy = int(round(-LIGHT[1] / np.hypot(LIGHT[0], LIGHT[1]) * d * S * 0.5))
        zt = _shift(zz, dy, dx, -1e9)
        cast |= A & (zt > zz + 1.1 + 0.9 * d)
    for i, m in enumerate(c.mats):
        sel = c.mat == i
        if not sel.any():
            continue
        r = np.array(m.ramp)
        if m.flat:
            col[sel] = r[2]
            continue
        if m.emissive >= 0.5:
            # ışıyan damar / öz: düz parlak, gölgesiz (ışıma rengi dokuda)
            col[sel] = r[3] * 0.6 + r[2] * 0.4
            emis_mask |= sel
            continue
        metal = m.spec >= 0.45
        d = ndl[sel]
        t = np.full(d.shape, 2)
        t[d < (0.36 if metal else 0.28)] = 1
        t[d > (0.80 if metal else 0.86)] = 3
        cs = cast[sel]
        t[cs] = np.minimum(t[cs], 1)
        t[cs & (d < 0.2)] = 0
        cc = r[t]
        if metal:
            hi = d > 0.955
            cc[hi] = r[4] * 0.5 + 0.5
        col[sel] = cc
    # çizgi roman metal parıltısı: bıçak/başlık metalinde, boyunun ~%62'sinde iki paralel çapraz beyaz çizgi
    import weapons_myth as wm
    mm = wm.mats_for(mid)
    bm = np.zeros((H, W), bool)
    for i, m in enumerate(c.mats):
        if (m is mm['b'] or m is mm['bd'] or m is mm['bl']) and m.spec >= 0.45 and m.emissive < 0.5:
            bm |= c.mat == i
    if bm.sum() > 40 * OVERS * OVERS:
        ys, xs = np.nonzero(bm)
        bx0, bx1 = xs.min(), xs.max()
        ym = ys.mean()
        yy, xx = np.mgrid[0:H, 0:W]
        u = (xx - (bx0 + 0.62 * (bx1 - bx0))) + 0.85 * (yy - ym)
        g1 = np.abs(u) < 0.9 * OVERS
        g2 = np.abs(u - 3.4 * OVERS) < 0.45 * OVERS
        gl = bm & (g1 | g2) & (ndl > 0.2)
        col[gl] = col[gl] * 0.15 + 0.85
    # Türk süsü: bıçak kökünde kazınmış koçboynuzu (iki karşılıklı sarmal) — koyu oyuk + altında ışık çizgisi
    if bm.sum() > 40 * OVERS * OVERS:
        _kocboynuzu(col, bm, c, mm, ndl)
    # ruh: bıçak yarı saydam (v1 ile aynı)
    alpha = A.astype(float)
    # ---- mürekkep
    ink = np.zeros((H, W), bool)
    # iç çizgiler: üstteki parçanın kenarı alttaki parçanın üzerine (parça kimliği değişir ve komşu belirgin yüksek)
    pid = c.pid
    zr = zz
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        for step in (1, 2):
            zn = _shift(zr, dy * step, dx * step, -1e9)
            pn = _shift(pid, dy * step, dx * step, -1)
            ink |= A & (pn != pid) & (zn > zr + 0.9) & (pn >= 0) & (zn > -1e8)
    # iç çizgileri ince tut: tek fiziksel halka yetmez, 1,2 çıktı pikseli civarı
    # dış silüet: ışık yanında ince, gölge yanında kalın (yönlü uzaklık eşiği)
    dist, inds = ndimage.distance_transform_edt(~A, return_indices=True)
    gy = (np.arange(H)[:, None] - inds[0])
    gx = (np.arange(W)[None, :] - inds[1])
    gl = np.hypot(gx, gy) + 1e-6
    facing = np.clip((gx * SHADOW2D[0] + gy * SHADOW2D[1]) / gl, -1, 1)
    thin, thick = 1.15 * OVERS, 2.9 * OVERS
    wpx = thin + (thick - thin) * np.clip(facing * 0.5 + 0.5, 0, 1) ** 1.5
    outer = (~A) & (dist <= wpx)
    col[ink] = INK
    col[outer] = INK
    alpha[outer] = 1.0
    if mid == 'ruh':
        for i, m in enumerate(c.mats):
            if m is mm['b'] or m is mm['bd'] or m is mm['bl']:
                sel = (c.mat == i) & ~ink
                alpha[sel] = 0.8
    rgba = np.dstack([col, alpha])
    return rgba, emis_mask


def _seg_dist(px, py, P):
    best = np.full(px.shape, 1e9)
    for i in range(len(P) - 1):
        ax, ay = P[i]
        bx, by = P[i + 1]
        sx, sy = bx - ax, by - ay
        t = np.clip(((px - ax) * sx + (py - ay) * sy) / (sx * sx + sy * sy + 1e-9), 0, 1)
        d = np.hypot(px - (ax + t * sx), py - (ay + t * sy))
        best = np.minimum(best, d)
    return best


def _kocboynuzu(col, bm, c, mm, ndl):
    """Bıçağın kabzaya yakın ucunda (kök) yatay koçboynuzu motifi: ortada dikey sap, iki yana kıvrılan sarmallar."""
    ys, xs = np.nonzero(bm)
    bx0, bx1 = xs.min(), xs.max()
    L = bx1 - bx0
    # kök kesitinde bıçak yüksekliği
    sel = xs < bx0 + 0.18 * L
    if sel.sum() < 10:
        return
    yk0, yk1 = ys[sel].min(), ys[sel].max()
    hgt = yk1 - yk0
    if hgt < 5.5 * OVERS or L < 40 * OVERS:
        return
    cx = bx0 + 0.13 * L
    cy = (yk0 + yk1) * 0.5
    s = hgt * 0.36
    curves = []
    for sg in (-1, 1):
        pts = [(cx, cy + s * 0.55), (cx, cy - s * 0.05)]
        for t in np.linspace(0, 1, 18):
            a = math.pi * 0.5 + sg * (-math.pi * 0.5 - t * math.pi * 1.6)
            r = s * (0.62 - 0.42 * t)
            ox = cx + sg * s * 0.55
            oy = cy - s * 0.05
            pts.append((ox + math.cos(a) * r * 1.0 - sg * s * 0.0, oy - math.sin(a) * r * -1.0 * 0 + math.sin(a) * r))
        curves.append(pts)
    x0, x1 = int(cx - s * 1.6), int(cx + s * 1.6) + 1
    y0, y1 = int(cy - s * 1.3), int(cy + s * 1.3) + 1
    H, W = bm.shape
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1] + 0.5
    d = np.minimum(_seg_dist(xx, yy, curves[0]), _seg_dist(xx, yy, curves[1]))
    dl = np.minimum(_seg_dist(xx, yy - 0.9 * OVERS, curves[0]), _seg_dist(xx, yy - 0.9 * OVERS, curves[1]))
    sub = bm[y0:y1, x0:x1]
    groove = sub & (d < 0.55 * OVERS)
    lit = sub & (dl < 0.45 * OVERS) & ~groove
    r = np.array(mm['b'].ramp)
    blk = col[y0:y1, x0:x1]
    blk[lit] = r[4] * 0.6 + 0.4 * blk[lit]
    blk[groove] = r[0] * 0.7 + INK * 0.3


def downsample(rgba, f):
    h, w = rgba.shape[0] // f * f, rgba.shape[1] // f * f
    a = rgba[:h, :w]
    pm = a[..., :3] * a[..., 3:4]
    pm = pm.reshape(h // f, f, w // f, f, 3).mean(axis=(1, 3))
    al = a[..., 3].reshape(h // f, f, w // f, f).mean(axis=(1, 3))
    rgb = pm / np.maximum(al[..., None], 1e-6)
    return np.dstack([np.clip(rgb, 0, 1), al])


def render(iid, mid):
    wm = _setup()
    pv = wm.pivot_of(iid)
    c = wm.WCanvas(wm.CELL[0], wm.CELL[1], pv[0], pv[1])
    mm = wm.mats_for(mid)
    wm.draw_item(c, iid, mm)
    rgba, _ = ink_shade(c, mid)
    out = downsample(rgba, OVERS)
    return out


def _job(args):
    iid, mid = args
    return iid, mid, render(iid, mid)


def build(only=None, workers=8, preview=None):
    wm = _setup()
    mids = [m['id'] for m in wm.ITEMS['materials']]
    ids = [i for i in wm.ORDER if (not only or i in only)]
    jobs = [(i, m) for i in ids for m in mids]
    t0 = time.time()
    res = {}
    if workers > 1:
        from multiprocessing import Pool
        with Pool(workers) as p:
            for iid, mid, img in p.imap_unordered(_job, jobs, chunksize=2):
                res[(iid, mid)] = img
    else:
        for j in jobs:
            iid, mid, img = _job(j)
            res[(iid, mid)] = img
    print('çizim: %d hücre, %.1f sn' % (len(jobs), time.time() - t0))
    # ---- eşya başına ortak kırpma, raf paketleme
    F = TEXEL_V2 // wm.TEX               # v1 doku pikseli -> v2 pikseli
    items = {}
    rects = []
    for iid in ids:
        u = None
        for mid in mids:
            a = res[(iid, mid)][..., 3] > 0.004
            ys, xs = np.nonzero(a)
            if len(xs) == 0:
                continue
            bb = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
            u = bb if u is None else (min(u[0], bb[0]), min(u[1], bb[1]), max(u[2], bb[2]), max(u[3], bb[3]))
        if u is None:
            u = (0, 0, 2, 2)
        x0, y0, x1, y1 = int(max(0, u[0] - 2)), int(max(0, u[1] - 2)), int(u[2] + 2), int(u[3] + 2)
        pv = wm.pivot_of(iid)
        items[iid] = {'crop': (x0, y0, x1, y1), 'pivot': [pv[0] * F - x0, pv[1] * F - y0], 'size': [x1 - x0, y1 - y0], 'm': {}}
        for mid in mids:
            rects.append((iid, mid, x1 - x0, y1 - y0))
    PW, PH = 4096, 8192
    pages = []
    cur = None
    rects.sort(key=lambda r: -r[3])
    pos = {}
    x = y = shelf = 0
    pi = -1
    for iid, mid, w, h in rects:
        if pi < 0 or x + w > PW:
            x = 0
            y += shelf
            shelf = 0
        if pi < 0 or y + h > PH:
            pi += 1
            x = y = shelf = 0
            pages.append(0)
        pos[(iid, mid)] = (pi, x, y)
        pages[pi] = max(pages[pi], y + h)
        x += w + 2
        shelf = max(shelf, h + 2)
    imgs = [np.zeros((int(math.ceil(hh / 4.0) * 4), PW, 4)) for hh in pages]
    for (iid, mid), (p, x, y) in pos.items():
        x0, y0, x1, y1 = items[iid]['crop']
        cell = res[(iid, mid)][y0:y1, x0:x1]
        imgs[p][y:y + cell.shape[0], x:x + cell.shape[1]] = cell
        items[iid]['m'][mid] = [int(p), int(x), int(y)]
    meta = {'texel': TEXEL_V2, 'filter': 'linear', 'pages': [], 'items': {}}
    for p, im in enumerate(imgs):
        nm = 'weapons_v2_%d.png' % p
        meta['pages'].append(nm)
        if not only:
            _save(im, os.path.join(OUT, nm))
            _import_file(nm)
    for iid in ids:
        d = items[iid]
        meta['items'][iid] = {'pivot': [float(d['pivot'][0]), float(d['pivot'][1])], 'size': d['size'], 'm': d['m']}
    if only:
        print('--yalniz: atlas yazılmadı (yalnız önizleme)')
    else:
        with open(os.path.join(OUT, 'weapons_v2.json'), 'w', encoding='utf-8') as f:
            json.dump(meta, f, separators=(',', ':'))
        print('sayfalar:', [im.shape[:2] for im in imgs])
    if preview:
        _preview(res, ids, mids, preview)
    return res


def _save(arr, path):
    a = (np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(a, 'RGBA').save(path, optimize=True)


IMPORT = """[remap]

importer="texture"
type="CompressedTexture2D"

[deps]

source_file="res://assets/weapons/{name}"

[params]

compress/mode=2
compress/high_quality=true
compress/lossy_quality=0.7
compress/hdr_compression=1
compress/normal_map=2
compress/channel_pack=0
mipmaps/generate=true
mipmaps/limit=-1
roughness/mode=0
roughness/src_normal=""
process/channel_remap/red=0
process/channel_remap/green=1
process/channel_remap/blue=2
process/channel_remap/alpha=3
process/fix_alpha_border=true
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_as_srgb=false
process/hdr_clamp_exposure=false
process/size_limit=0
detect_3d/compress_to=0
"""


def _import_file(nm):
    ip = os.path.join(OUT, nm + '.import')
    if not os.path.exists(ip):
        with open(ip, 'w', encoding='utf-8') as f:
            f.write(IMPORT.format(name=nm))


def _preview(res, ids, mids, path, mats=('demir', 'altin', 'od_tasi', 'ruh')):
    cells = []
    for iid in ids:
        row = [res[(iid, m)] for m in mats if (iid, m) in res]
        cells.append(row)
    h, w = cells[0][0].shape[:2]
    cols = 2
    rows = (len(cells) + cols - 1) // cols
    out = np.zeros((rows * h, cols * len(mats) * w, 3))
    out[:] = np.array([0.36, 0.42, 0.34])
    for k, row in enumerate(cells):
        for j, im in enumerate(row):
            y = (k // cols) * h
            x = ((k % cols) * len(mats) + j) * w
            a = im[..., 3:4]
            out[y:y + h, x:x + w] = im[..., :3] * a + out[y:y + h, x:x + w] * (1 - a)
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(path)


if __name__ == '__main__':
    only = None
    if '--yalniz' in sys.argv:
        only = sys.argv[sys.argv.index('--yalniz') + 1].split(',')
    workers = int(sys.argv[sys.argv.index('--is') + 1]) if '--is' in sys.argv else max(1, (os.cpu_count() or 2) - 1)
    pv = sys.argv[sys.argv.index('--onizleme') + 1] if '--onizleme' in sys.argv else None
    build(only, workers, pv)
