"""Stil v2 mürekkep-cel yaratıklar (A takımı): Çor, Kara İye, Balbal, Kara Kam ve biyom çeşitlemeleri.

Her çeşitleme kendi `<kimlik>_v2` sprite'ı olur (assets/sprites/<kimlik>_v2.{png,json} + _e ışıma sayfası); satır
düzeni, kare sayısı, fps ve döngü temel sprite'ın v1 json'undan (cor.json ...) alınır. Oyunda Enemy, v2'de düşmanın
kendi kimliğiyle bir `_v2` sprite'ı varsa onu kullanır (biyom tonu uygulanmaz, renkler çizimde); yoksa temel sprite.
v1 dosyalarına dokunmaz.

Kullanım:  python export_yaratik_a.py                     (hepsi, ~17 sayfa)
           python export_yaratik_a.py cor kan_yarasasi    (yalnızca bu kimlikler)
           python export_yaratik_a.py --cor | --iye | --balbal | --kam
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import export_ink as ex

# v29: bu kimlikler tam gövde animasyonlu kendi çizimleriyle export_ucan.py'den çıkar (burada atlanır; Çor ailesinin
# hepsi, Su / Od İyesi, Tozkoparan, Işıltı Kamı)
V29 = ('cor', 'kara_kus_yavrusu', 'kan_yarasasi', 'kaf_kartali', 'kayip_ruh', 'demir_gaga', 'su_iyesi', 'od_iyesi', 'tozkoparan',
       'isilti_bocegi')

MODS = {
    'cor': ('cor_ink', 'cor.json'),
    'iye': ('agac_iyesi_ink', 'agac_iyesi.json'),
    'balbal': ('balbal_ink', 'balbal.json'),
    'kam': ('arcura_ink', 'arcura.json'),
}


def _render(args):
    mod, an, i, var = args
    import importlib
    m = importlib.import_module(mod)
    rgba, nm, em, info = m.render_frame(an, i, var)
    if ex.HD > 1:   # HD paketi: normal/ışıma sayfası yazılmaz; ana sürece yalnızca renk (float16) + ışıma var/yok
        return (an, i), (rgba.astype(np.float16), None, np.full((1, 1, 4), em[..., 3].max(), np.float32), info)
    return (an, i), (rgba, nm, em, info)


def export_variant(group, var, pool):
    import importlib
    import json
    mod, lay = MODS[group]
    m = importlib.import_module(mod)
    layout = json.load(open(os.path.join(ex.SPR, lay), encoding='utf-8'))
    jobs = [(mod, an, i, var) for an, a in layout['anims'].items() for i in range(a['frames'])]
    cache = dict(pool.map(_render, jobs))
    ex.export_sheet(var + '_v2', lay, lambda an, i: cache[(an, i)], m.CELL, m.FEET, m.TEX)


def main():
    import importlib
    args = sys.argv[1:]
    groups = [g for g in MODS if '--' + g in args] or list(MODS)
    only = [a for a in args if not a.startswith('--')]
    # KY_IS: süreç sayısı sınırı (başka dışa aktarımlarla paralel çalışırken; varsayılan çekirdek - 1)
    workers = int(os.environ.get('KY_IS', '0') or '0') or max(1, (os.cpu_count() or 2) - 1)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for g in groups:
            m = importlib.import_module(MODS[g][0])
            for var in m.VARIANTS:
                if only and var not in only:
                    continue
                if var in V29:
                    print(var, ': v29 -> python export_ucan.py', var)
                    continue
                export_variant(g, var, pool)


if __name__ == '__main__':
    main()
