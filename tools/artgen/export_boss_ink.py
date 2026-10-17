"""Stil v2 "mürekkep-cel" boss dışa aktarımı. v1 dosyalarına DOKUNMAZ; <kimlik>_v2 adlı varlıkları yazar.

Kullanım:  python export_boss_ink.py                         (beş boss)
           python export_boss_ink.py tepegoz erlik_han       (yalnızca bunlar)
           python export_boss_ink.py tepegoz --anim strike   (yalnızca bu animasyonlar yeniden çizilir; diğer kareler korunur)
           python export_boss_ink.py --is 4                  (paralel süreç sayısı; varsayılan 4)
           python export_boss_ink.py --onizleme out.png tepegoz idle:0 strike:2 ...   (sayfa yazmadan önizleme)

Bosslar dev (hücre dünya boyu v1 ile aynı: 200x200 ...), doku yoğunluğu 4 => hücre 800x800 px. Bir sıraya 8 kare
4096'yı aşar; bu yüzden düzen animasyon başına: her animasyon kendi sayfasında, kareleri "cols" sütunda bir alt satıra
sarar (json anim "page", "row" = sayfadaki ilk satır, "cols"). SpriteAnim._apply bu alanları okur (yoksa eski düzen).
Sütun sayısı toplam alanı en küçük yapan değerdir; sayfalar en çok 4096x4096.

Işıma (_e) sayfaları yarım çözünürlükte (json "glow_scale": 2; SpriteAnim ışıma sprite'ını 2x ölçekler): ışıma
toplamalı ve yumuşak, yarım boy VRAM'in 1/4'ü. Hepsi BPTC + mipmap (export_ink._import).
Satır düzeni, kare sayısı, fps, döngü ve çapa adları v1 json'undan alınır; çapalar yeni çizimden (dünya birimi).
"""
import importlib
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
from PIL import Image

import export_ink as ex
from hdpack import HD   # KY_HD=2: renk sayfaları assets_hd/x2'ye 2 kat (düzen ve json temel hücreyle aynı)

SPR = ex.SPR
PAGE = 4096
BOSSES = {
    # kimlik: (modül, v1 json)
    'kara_boru_han': ('kara_boru_han_ink', 'kara_boru_han.json'),
    'tepegoz': ('tepegoz_ink', 'tepegoz.json'),
    'sahmeran_ana': ('sahmeran_ink', 'sahmeran_ana.json'),
    'yelbegen': ('yelbegen_ink', 'yelbegen.json'),
    'erlik_han': ('erlik_ink', 'erlik_han.json'),
}


def _render(job):
    mod, an, i = job
    m = importlib.import_module(mod)
    t0 = time.time()
    rgba, nm, em, info = m.render_frame(an, i)
    ga = em[..., 3]
    if HD > 1:   # HD paketi: ışıma sayfası yazılmaz; yalnızca "glow" bayrağı için var/yok
        return (an, i, rgba.astype(np.float16), bool(ga.max() > 0), info, time.time() - t0)
    glo = np.zeros_like(em)
    glo[..., :3] = np.where(ga[..., None] > 1e-4, em[..., :3] / np.maximum(ga[..., None], 1e-4), 0)
    glo[..., 3] = ga
    return (an, i, rgba.astype(np.float16), glo.astype(np.float16), info, time.time() - t0)


def plan(names, frames, cw, ch):
    """Animasyon başına (sayfa, satır, sütun) planı; toplam alanı en küçük sütun sayısı."""
    best = None
    for cols in range(1, PAGE // cw + 1):
        rows_max = PAGE // ch
        if any((frames[a] + cols - 1) // cols > rows_max for a in names):
            continue
        pages = [[]]
        used = 0
        lay = {}
        for an in names:
            r = (frames[an] + cols - 1) // cols
            if used + r > rows_max and pages[-1]:
                pages.append([])
                used = 0
            lay[an] = (len(pages) - 1, used, min(cols, frames[an]))
            used += r
            pages[-1].append(an)
        heights = []
        for k, pg in enumerate(pages):
            heights.append(sum((frames[a] + cols - 1) // cols for a in pg))
        area = sum(h * ch * cols * cw for h in heights)
        key = (area * (1.0 + 0.03 * len(pages)), len(pages))
        if best is None or key < best[0]:
            best = (key, cols, lay, heights)
    return best[1], best[2], best[3]


def _down2(img):
    """Önceden çarpılmış uzayda 2x2 ortalama (ışıma sayfası yarım boy)."""
    a = img[..., 3:4]
    pm = np.concatenate([img[..., :3] * a, a], -1)
    h, w = pm.shape[0] // 2 * 2, pm.shape[1] // 2 * 2
    pm = pm[:h, :w].reshape(h // 2, 2, w // 2, 2, 4).mean(axis=(1, 3))
    a = pm[..., 3:4]
    rgb = np.where(a > 1e-4, pm[..., :3] / np.maximum(a, 1e-4), 0)
    return np.concatenate([rgb, a], -1)


def export_boss(bid, only=(), procs=4):
    modname, v1 = BOSSES[bid]
    m = importlib.import_module(modname)
    lay = json.load(open(os.path.join(SPR, v1), encoding='utf-8'))
    names = sorted(lay['anims'].keys(), key=lambda a: lay['anims'][a]['row'])
    frames = {a: lay['anims'][a]['frames'] for a in names}
    for a in names:
        assert m.ANIMS[a][0] == frames[a], (bid, a, m.ANIMS[a][0], frames[a])
    cw, ch = m.CELL
    cols, L, heights = plan(names, frames, cw, ch)
    name = bid + '_v2'
    out_json = os.path.join(SPR, name + '.json')
    meta_cell = [cw, ch]
    hd_glow = False
    if HD > 1:
        # HD paketi: düzen (sütun, sayfa, satır) temel hücreyle planlanır, sayfalar HD kat; ışıma sayfası tutulmaz
        cw, ch = cw * HD, ch * HD
        pages_a = [np.zeros((h * ch, cols * cw, 4), np.float16) for h in heights]
        pages_g = None
    else:
        pages_a = [np.zeros((h * ch, cols * cw, 4), np.float32) for h in heights]
        pages_g = [np.zeros((h * ch, cols * cw, 4), np.float32) for h in heights]
    old = None
    if only and os.path.exists(out_json) and HD == 1:
        o = json.load(open(out_json, encoding='utf-8'))
        if o.get('cell') == [cw, ch] and o.get('cols') == cols:
            old = o
            for k in range(int(o.get('pages', 1))):
                pn = os.path.join(SPR, ex._page_name(name, k))
                a_ = np.asarray(Image.open(pn + '.png').convert('RGBA'), np.float32) / 255.0
                pages_a[k][:a_.shape[0], :a_.shape[1]] = a_
                if os.path.exists(pn + '_e.png'):
                    g_ = np.asarray(Image.open(pn + '_e.png').convert('RGBA'), np.float32) / 255.0
                    g_ = np.asarray(Image.fromarray((g_ * 255).astype(np.uint8), 'RGBA').resize((a_.shape[1], a_.shape[0]), Image.BILINEAR), np.float32) / 255.0
                    pages_g[k][:g_.shape[0], :g_.shape[1]] = g_
    meta = old or {}
    meta.update({'cell': meta_cell, 'origin': list(m.FEET), 'texel': m.TEX, 'filter': 'linear', 'cols': cols,
                 'glow_scale': 2, 'page_rows': 9999})
    meta.setdefault('anims', {})
    jobs = [(modname, an, i) for an in names if (not old or an in only) for i in range(frames[an])]
    t0 = time.time()
    infos = {}
    with Pool(procs) as pool:
        for an, i, rgba, glo, info, dt in pool.imap_unordered(_render, jobs):
            pg, row0, c_ = L[an]
            r, c = row0 + i // c_, i % c_
            pages_a[pg][r * ch:(r + 1) * ch, c * cw:(c + 1) * cw] = rgba
            if pages_g is None:
                hd_glow = hd_glow or glo
            else:
                pages_g[pg][r * ch:(r + 1) * ch, c * cw:(c + 1) * cw] = glo
            infos[(an, i)] = info
            print('  %s %s:%d %.1fs' % (bid, an, i, dt), flush=True)
    for an in names:
        if old and an not in only:
            continue
        la = lay['anims'][an]
        pg, row0, c_ = L[an]
        meta['anims'][an] = {'row': row0, 'page': pg, 'cols': c_, 'frames': la['frames'], 'fps': la['fps'], 'loop': la['loop'],
                             'arm': la.get('arm', True), 'data': [ex._frame_meta(infos[(an, i)]) for i in range(la['frames'])]}
    has_glow = hd_glow if pages_g is None else any(g[..., 3].max() > 0 for g in pages_g)
    for k in range(len(pages_a)):
        pn = os.path.join(SPR, ex._page_name(name, k))
        ex._png(pages_a[k], pn + '.png', vram=True)
        if has_glow and pages_g is not None:
            ex._png(_down2(pages_g[k]), pn + '_e.png', vram=True)
        print('  sayfa', ex._page_name(name, k), pages_a[k].shape[1], pages_a[k].shape[0])
    k = len(pages_a)
    while os.path.exists(os.path.join(SPR, ex._page_name(name, k) + '.png')):
        for suf in ('.png', '.png.import', '_e.png', '_e.png.import'):
            f = os.path.join(SPR, ex._page_name(name, k) + suf)
            if os.path.exists(f):
                os.remove(f)
        k += 1
    meta['glow'] = bool(has_glow)
    meta['pages'] = len(pages_a)
    json.dump(meta, open(out_json, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    px = sum(p.shape[0] * p.shape[1] for p in pages_a)
    print('sprite %s: %d sayfa, %d sütun, %.1f Mpx (ışıma %.1f Mpx), %.0f sn' % (name, len(pages_a), cols, px / 1e6, px / 4e6, time.time() - t0))


def preview(out, bid, specs, bg=True, zoom=1.0):
    """Seçili kareler sisli yeşil zeminde yan yana (1:1 = 1080p'de 2,0 kamera)."""
    m = importlib.import_module(BOSSES[bid][0])
    jobs = [(BOSSES[bid][0], s.split(':')[0], int(s.split(':')[1])) for s in specs]
    with Pool(min(4, len(jobs))) as pool:
        res = pool.map(_render, jobs)
    tiles = [r[2].astype(np.float32) for r in res]
    glows = [r[3].astype(np.float32) for r in res]
    h, w = tiles[0].shape[:2]
    W = w * len(tiles)
    yy = np.linspace(0, 1, h)[:, None, None]
    img = (np.array([0.42, 0.55, 0.48]) * (1 - yy) + np.array([0.20, 0.28, 0.26]) * yy) * np.ones((h, W, 3))
    for k, (t, g) in enumerate(zip(tiles, glows)):
        a = t[..., 3:4]
        sl = slice(k * w, (k + 1) * w)
        img[:, sl] = img[:, sl] * (1 - a) + t[..., :3] * a
        img[:, sl] += g[..., :3] * g[..., 3:4] * 0.6
        # ayak çizgisi
        img[m.FEET[1], sl] = img[m.FEET[1], sl] * 0.6
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    if zoom != 1.0:
        im = im.resize((int(W * zoom), int(h * zoom)), Image.LANCZOS)
    im.save(out)
    for r in res:
        print(r[0], r[1], '%.1fs' % r[5], r[4])


def main():
    args = sys.argv[1:]
    procs = 4
    if '--is' in args:
        i = args.index('--is'); procs = int(args[i + 1]); del args[i:i + 2]
    if '--onizleme' in args:
        i = args.index('--onizleme'); out = args[i + 1]; del args[i:i + 2]
        zoom = 1.0
        if '--zoom' in args:
            j = args.index('--zoom'); zoom = float(args[j + 1]); del args[j:j + 2]
        preview(out, args[0], args[1:], zoom=zoom)
        return
    only = ()
    if '--anim' in args:
        i = args.index('--anim'); only = tuple(args[i + 1:]); del args[i:]
    ids = [a for a in args if a in BOSSES] or list(BOSSES)
    for bid in ids:
        export_boss(bid, only, procs)


if __name__ == '__main__':
    main()
