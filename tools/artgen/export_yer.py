"""v29 yer yaratıkları dışa aktarımı: tam gövde animasyon satırları + json "v29" / "durum" eşlemesi.

Kullanım (tools/artgen içinde):
    python export_yer.py                       hepsi
    python export_yer.py kara_boru bekci ...   yalnızca bu sprite kimlikleri
    KY_HD=2 python export_yer.py ...           HD x2 sayfaları (assets_hd/x2; sonra python hd_paket.py --paketle)
    KY_IS=6 ...                                süreç sayısı sınırı

Satır düzeni artık v1 json'undan DEĞİL, modülün SEQS sözlüğünden gelir (yaratik_govde.layout). Her satıra yaratik_govde.Seq
meta'sı ("seg", "ts", "lead", "vx", "alt" ...) yazılır; json üst düzeyine "v29": 1 ve "durum" (Enemy._anim_tick eşlemesi).
Sözleşme: docs/v29/enemy_anim_json.md.
"""
import importlib
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import export_ink as ex
import yaratik_govde as yg

# sprite kimliği -> (modül, çeşitleme adı ya da None)
SHEETS = {
    'kara_boru': ('kara_boru_ink', None),
    'agac_iyesi': ('agac_iyesi_ink', 'agac_iyesi'),
    'dev_cocugu': ('agac_iyesi_ink', 'dev_cocugu'),
    'bekci': ('bekci_ink', None),
    'balbal': ('balbal_ink', 'balbal'),
    'buz_balbali': ('balbal_ink', 'buz_balbali'),
    'tosbaga': ('tosbaga_ink', None),
    'surale': ('surale_ink', None),
    'arcura': ('arcura_ink', 'arcura'),
    'kurgan_okcusu': ('arcura_ink', 'kurgan_okcusu'),
    'erlik_kizi': ('arcura_ink', 'erlik_kizi'),
}


def _render(args):
    mod, var, an, i = args
    m = importlib.import_module(mod)
    out = m.render_frame(an, i, var) if var is not None else m.render_frame(an, i)
    rgba, nm, em, info = out
    if ex.HD > 1:
        return (an, i), (rgba.astype(np.float16), None, np.full((1, 1, 4), em[..., 3].max(), np.float32), info)
    return (an, i), (rgba, None, em, info)


def export(name, pool):
    mod, var = SHEETS[name]
    m = importlib.import_module(mod)
    seqs = m.SEQS
    yg.check_durum(seqs, m.DURUM)
    jobs = [(mod, var, an, i) for an, s in seqs.items() for i in range(len(s))]
    cache = dict(pool.map(_render, jobs, chunksize=1))
    ex.export_sheet(name + '_v2', yg.layout(seqs), lambda an, i: cache[(an, i)], m.CELL, m.FEET, m.TEX,
                    anim_meta=yg.anim_meta(seqs), extra_meta={'v29': 1, 'durum': m.DURUM})
    halve_glow(name + '_v2')


def halve_glow(name):
    """Işıma sayfaları yarım çözünürlükte (json "glow_scale": 2; SpriteAnim._glow_k): yumuşak toplamalı ışıma için
    yeterli, depo boyutu ~1/4. HD paketi ışıma sayfası yazmaz (temel kalır)."""
    import json
    from PIL import Image
    if ex.HD > 1:
        return
    jp = os.path.join(ex.SPR, name + '.json')
    meta = json.load(open(jp, encoding='utf-8'))
    if not meta.get('glow') or meta.get('glow_scale', 1) == 2:
        return
    for k in range(int(meta.get('pages', 1))):
        pn = os.path.join(ex.SPR, ex._page_name(name, k) + '_e.png')
        if not os.path.exists(pn):
            continue
        im = Image.open(pn).convert('RGBA')
        a = np.asarray(im, np.float32) / 255.0
        # önçarpımlı küçültme (saydam kenarda renk kararmasın)
        pm = a.copy()
        pm[..., :3] *= pm[..., 3:4]
        h, w = pm.shape[0] // 2 * 2, pm.shape[1] // 2 * 2
        pm = pm[:h, :w].reshape(h // 2, 2, w // 2, 2, 4).mean(axis=(1, 3))
        al = pm[..., 3:4]
        pm[..., :3] = np.where(al > 1e-4, pm[..., :3] / np.maximum(al, 1e-4), 0)
        ex._png(pm, pn, vram=False)
    meta['glow_scale'] = 2
    json.dump(meta, open(jp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print('  ışıma yarım çözünürlük', name)


def main():
    names = [a for a in sys.argv[1:] if not a.startswith('--')] or list(SHEETS)
    if '--isima' in sys.argv:   # yalnızca var olan sayfaların ışımasını yarıya indir
        for n in names:
            halve_glow(n + '_v2')
        return
    workers = int(os.environ.get('KY_IS', '0') or '0') or max(1, (os.cpu_count() or 2) - 2)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for n in names:
            export(n, pool)


if __name__ == '__main__':
    main()
