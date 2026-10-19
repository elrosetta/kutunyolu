"""v29: uçan ve büyücü yaratıkların tam gövde animasyonlu sayfaları (assets/sprites/<kimlik>_v2.{png,json} + _e).

Kullanım (tools/artgen içinde):
    python export_ucan.py                       hepsi (10 sayfa)
    python export_ucan.py kan_yarasasi od_iyesi yalnızca bu kimlikler
    KY_HD=2 python export_ucan.py               HD x2 paketi (assets_hd/x2; sonra python hd_paket.py --paketle)

Çizim modülleri: cor_ink.py (Çor ailesi), iye_v29_ink.py (Su / Od İyesi, Tozkoparan), isilti_v29_ink.py (Işıltı Kamı).
Her modül `anims_for(kimlik)` ile satır düzenini (kare, fps, döngü, isteğe bağlı ts / mk) ve `durum_for(kimlik)` ile
Enemy durumu -> satır önerisini verir. json'a yazılanlar:
  * satır başına "ts" (karelerin başlangıç anı, 0..1) ve "mk" = [W, C, H] (hazırlık sonu, temas, etkin evre sonu;
    Bengü v28 `Player._body_frame` sözleşmesi, 0 ve 1 örtük) ve "v29": true — saldırı satırlarında.
  * sayfa düzeyinde "durum": {Enemy durumu: satır} (genel, veri güdümlü oynatım için; bugünkü Enemy.gd okumaz).
Satır adları bugünkü Enemy.gd'nin çağırdıklarıyla uyumludur (idle / attack 0-1 / hurt; walk / windup / slam; run /
cast; kaçışta `hop`); yeni satırlar (tele, tele_zirh, death, spawn, ...) yalnızca ekdir.
Kareler süreç havuzunda paralel çizilir (export_ink.export_sheet `par`).
"""
import functools
import os
import sys

import numpy as np

import export_ink as ex

CREATURES = {
    'cor': 'cor_ink', 'kara_kus_yavrusu': 'cor_ink', 'kan_yarasasi': 'cor_ink', 'kaf_kartali': 'cor_ink', 'kayip_ruh': 'cor_ink',
    'demir_gaga': 'cor_ink',
    'su_iyesi': 'iye_v29_ink', 'od_iyesi': 'iye_v29_ink', 'tozkoparan': 'iye_v29_ink',
    'isilti_bocegi': 'isilti_v29_ink',
}
# satır sırasının başı (eski v1 düzeni: ilk satır "idle" kalır; SpriteAnim ilk satırı oynatarak açılır)
LAYOUT = {'cor_ink': 'cor.json', 'iye_v29_ink': 'agac_iyesi.json', 'isilti_v29_ink': 'arcura.json'}


def _par(mod, var, job):
    import importlib
    m = importlib.import_module(mod)
    rgba, nm, em, info = m.render_frame(job[0], job[1], var)
    if ex.HD > 1:   # HD: ışıma sayfası yazılmaz, yalnızca var / yok
        em = em[..., 3:4].max().reshape(1, 1, 1) * np.ones((1, 1, 4), np.float32)
        return rgba.astype(np.float16), None, em, info
    return rgba, None, em, info


def export(var):
    import importlib
    mod = CREATURES[var]
    m = importlib.import_module(mod)
    rows = m.anims_for(var)
    lo, am = {}, {}
    for an, r in rows.items():
        lo[an] = {'frames': r['frames'], 'fps': r['fps'], 'loop': r['loop'], 'arm': False}
        if r.get('ts'):
            am[an] = {'ts': [round(x, 4) for x in r['ts']], 'mk': [round(x, 4) for x in r['mk']], 'v29': True}
    assert max(r['frames'] for r in rows.values()) * m.CELL[0] <= ex.PAGE_MAX, var + ': satır 4096 pikseli aşıyor'
    lay = os.path.join(ex.SPR, LAYOUT[mod])
    import json
    base = json.load(open(lay, encoding='utf-8'))
    extra = [a for a in base['anims'] if a not in rows]
    assert not extra, '%s: düzende fazladan satır %s' % (var, extra)
    ex.export_sheet(var + '_v2', LAYOUT[mod], lambda an, i: m.render_frame(an, i, var), m.CELL, m.FEET, m.TEX,
                    layout_over=lo, anim_meta=am, extra_meta={'durum': m.durum_for(var), 'v29': True},
                    par=functools.partial(_par, mod, var))
    if ex.HD == 1:
        half_glow(var + '_v2')


def half_glow(name):
    """Işıma sayfasını yarı çözünürlüğe indir (json "glow_scale": 2; SpriteAnim._glow_k). Işıma zaten bulanık: görüntü
    aynı, depo boyutu ~1/4."""
    import json
    from PIL import Image
    jp = os.path.join(ex.SPR, name + '.json')
    meta = json.load(open(jp, encoding='utf-8'))
    if meta.get('glow_scale', 1) != 1 or not meta.get('glow'):
        return
    for k in range(int(meta.get('pages', 1))):
        ep = os.path.join(ex.SPR, ex._page_name(name, k) + '_e.png')
        if not os.path.exists(ep):
            continue
        im = Image.open(ep).convert('RGBA')
        a = np.asarray(im, np.float32) / 255.0
        h, w = a.shape[0] // 2 * 2, a.shape[1] // 2 * 2
        pm = a[:h, :w].copy()
        pm[..., :3] *= pm[..., 3:4]
        pm = pm.reshape(h // 2, 2, w // 2, 2, 4).mean(axis=(1, 3))
        al = pm[..., 3:4]
        pm[..., :3] = np.where(al > 1e-4, pm[..., :3] / np.maximum(al, 1e-4), 0)
        ex._png(pm, ep)
    meta['glow_scale'] = 2
    json.dump(meta, open(jp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print('  ışıma yarı çözünürlük', name)


def main():
    only = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--yari_isima' in sys.argv:   # yalnızca var olan sayfaların ışımasını yarıya indir
        for var in CREATURES:
            if not only or var in only:
                half_glow(var + '_v2')
        return
    for var in CREATURES:
        if only and var not in only:
            continue
        print('==', var, flush=True)
        export(var)


if __name__ == '__main__':
    main()
