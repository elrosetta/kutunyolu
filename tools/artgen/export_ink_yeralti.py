"""Stil v2 "mürekkep" yeraltı biyomlarını dışa aktarır: Şahmeran Mağaraları ve Tamu (Erlik'in Ülkesi).
v1 dosyalarına ve Ötüken v2 dosyalarına dokunmaz; kaydetme / .import / BPTC kuralları export_ink_ortam ile aynı.

Kullanım:  python export_ink_yeralti.py sahmeran [--bg [katman...]] [--zemin] [--on] [--suslar] [--tehlike]
           python export_ink_yeralti.py tamu ...
           python export_ink_yeralti.py hepsi          (iki biyom, her şey)
Çıktılar (<b> = sahmeran | tamu):
  assets/bg/<b>_v2_*.png                 paralaks katmanları + ön plan şeritleri + parçacık
  assets/tiles/<b>_v2{,_mask,_e,_soil,_soil_e,_meadow}.png + <b>_v2.json   zemin
  assets/decor/*_<b>_v2{,_e}.png + decor_v2_<b>.json                        biyom süsleri
  assets/tiles/hazard_<tür>_v2.png       sıvı tehlike dokusu (zehir / lav; liquid_ink.gdshader)
"""
import json
import os
import sys
import time

import numpy as np

import export_ink_ortam as E
from export_ink_ortam import A, save, to8, WORLD_K
from hdpack import HD   # KY_HD=2: çıktı ölçeği K x HD (json temel değerlerle)

BG = [('0_sky', 'layer_sky'), ('1_far', 'layer_far'), ('2_farmid', 'layer_farmid'), ('2b_haze', 'layer_haze'),
      ('3_mid', 'layer_mid'), ('4_fog', 'layer_fogband'), ('5_shafts', 'layer_shafts'), ('6_near', 'layer_near')]

MODS = {
    'sahmeran': ('sahmeran_ink_ortam', 'sahmeran_ink_ground', 'sahmeran_ink_decor'),
    'tamu': ('tamu_ink_ortam', 'tamu_ink_ground', 'tamu_ink_decor'),
}


def _vram(b):
    # ayrıntılı büyük dokular BC7; gök, sis, pus, hüzme, maske ve ışıma kayıpsız
    E.VRAM.update({'%s_v2_1_far.png' % b, '%s_v2_2_farmid.png' % b, '%s_v2_3_mid.png' % b, '%s_v2_6_near.png' % b,
                   '%s_v2_soil.png' % b, '%s_v2_meadow.png' % b})


def export_bg(b, only=None):
    import importlib
    import inkkit_ortam as ik
    O = importlib.import_module(MODS[b][0])
    ik.K = 1.0 * HD
    for key, fn in getattr(O, 'EXPORT_BG', BG):
        if only and key not in only:
            continue
        t = time.time()
        L = getattr(O, fn)()
        save(L.rgba8(), 'bg', '%s_v2_%s.png' % (b, key))
        print('    %.1fs' % (time.time() - t), flush=True)


def export_ground(b):
    import importlib
    import inkkit_ortam as ik
    import inkkit_zemin as Z
    G = importlib.import_module(MODS[b][1])
    ik.K = WORLD_K * HD
    art, mask, emit, cells = Z.build_atlas(G.SPEC)
    save(to8(art), 'tiles', '%s_v2.png' % b)
    save((np.clip(mask, 0, 1) * 255 + 0.5).astype(np.uint8), 'tiles', '%s_v2_mask.png' % b)
    save(to8(emit), 'tiles', '%s_v2_e.png' % b)
    soil, soil_e = G.soil_texture()
    save(soil.rgba8(), 'tiles', '%s_v2_soil.png' % b)
    save(soil_e.rgba8(), 'tiles', '%s_v2_soil_e.png' % b)
    top = G.moss_texture() if hasattr(G, 'moss_texture') else G.top_texture()
    save(top.rgba8(), 'tiles', '%s_v2_meadow.png' % b)
    meta = {
        "tile": ik.P(Z.C) // HD, "world_tile": 24, "density": ik.P(Z.C) // HD / 24.0, "cols": Z.COLS, "ground_rows": 3,
        "overlay_row": Z.OROW, "grass_cols": Z.GRASS_COLS, "ceiling_cols": Z.CEIL_COLS, "platform_row": Z.PROW,
        "ink": True, "filter": "linear_mipmap", "mask": "%s_v2_mask.png" % b, "soil_size": soil.w // HD,
        "soil_density": 2.0 * WORLD_K, "meadow": "%s_v2_meadow.png" % b, "glow": None,
        "emit": "%s_v2_e.png" % b, "emit_cells": cells, "soil_e": "%s_v2_soil_e.png" % b,
        "meadow_depth": getattr(G, 'MEADOW_DEPTH', 0.55),
        "not": "v2 mürekkep zemini (%s): sanat RGBA + maske (R kaplama, G kenar gölgesi) + ışıma atlası (_e, ADD) + "
               "dünya uzayı kaya (_soil, ışıyan damarlar _soil_e) ve üst yüzey (_meadow)" % b,
    }
    json.dump(meta, open(os.path.join(A, 'tiles', '%s_v2.json' % b), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def export_fg(b):
    import importlib
    import inkkit_ortam as ik
    G = importlib.import_module(MODS[b][1])
    ik.K = 1.0 * HD
    save(G.fg_bottom_strip().rgba8(), 'bg', '%s_v2_fg_bottom.png' % b)
    save(G.fg_top_strip().rgba8(), 'bg', '%s_v2_fg_top.png' % b)
    for nm, fn in getattr(G, 'PARTICLES', {}).items():
        save(to8(getattr(G, fn)()), 'bg', '%s_v2_%s.png' % (b, nm))


def export_decor(b):
    import importlib
    import inkkit_ortam as ik
    D = importlib.import_module(MODS[b][2])
    ik.K = WORLD_K * HD
    D.export(save, to8, A, b)


def export_hazard(b):
    import inkkit_ortam as ik
    import hazard_ink as HZ
    ik.K = 1.0 * HD
    for kind, fn in HZ.KINDS.get(b, {}).items():
        save(getattr(HZ, fn)(), 'tiles', 'hazard_%s_v2.png' % kind)


def run(b, args):
    _vram(b)
    every = not any(a.startswith('--') for a in args)
    rest = [a for a in args if not a.startswith('--')]
    print('==', b, flush=True)
    if every or '--bg' in args:
        export_bg(b, rest or None)
    if every or '--zemin' in args:
        export_ground(b)
    if every or '--on' in args:
        export_fg(b)
    if every or '--suslar' in args:
        export_decor(b)
    if every or '--tehlike' in args:
        export_hazard(b)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    b = args.pop(0)
    for bb in (['sahmeran', 'tamu'] if b == 'hepsi' else [b]):
        run(bb, args)


if __name__ == '__main__':
    main()
