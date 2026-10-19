"""Stil v2 "mürekkep" biyom ortamlarını dışa aktarır (Bozkır Kurganları, Kaf Dağı). v1 ve Ötüken dosyalarına dokunmaz.

Kullanım:  python export_ink_biyom.py bozkir [kaf ...]          (verilen biyomların hepsi)
           python export_ink_biyom.py kaf --bg [katman ...]     paralaks katmanları  assets/bg/<biyom>_v2_*.png
           python export_ink_biyom.py kaf --zemin               karo atlası + maske + toprak + örtü  assets/tiles/<biyom>_v2*
           python export_ink_biyom.py kaf --on                  ön plan şeritleri + parçacık  assets/bg/<biyom>_v2_fg_*.png
           python export_ink_biyom.py kaf --suslar              süsler  assets/decor/*_<biyom>_v2.png + decor_v2_<biyom>.json
           python export_ink_biyom.py kaf --tehlike             tehlike karoları  assets/tiles/hazards_<biyom>_v2.png
Kaydetme, .import (mipmap, BPTC) ve önçarpım dönüşümü export_ink_ortam.py'den. Oyunda katman listesi, paralaks çarpanları,
ışık ve renk derecelendirme: data/stil_v2.json (biyom girdisi).
"""
import json
import os
import sys
import time

import numpy as np

import export_ink_ortam as E
from hdpack import HD   # KY_HD=2: çıktı ölçeği K x HD (json temel değerlerle)

A = E.A

BIOMES = {
    'bozkir': dict(
        par='bozkir_ink', ground='bozkir_ink_ground', decor='bozkir_ink_decor',
        bg=[('0_sky', 'layer_sky'), ('0b_shafts', 'layer_shafts'), ('1_far', 'layer_far'), ('2_farmid', 'layer_farmid'),
            ('2b_haze', 'layer_haze'), ('3_mid', 'layer_mid'), ('4_dust', 'layer_dust'), ('6_near', 'layer_near'),
            ('7_wind', 'layer_wind')],
        vram=['1_far', '2_farmid', '3_mid', '6_near', '7_wind'],
        fg=[('fg_grass', 'fg_grass_strip'), ('chaff', 'chaff_particle')],
    ),
    'kaf': dict(
        par='kaf_ink', ground='kaf_ink_ground', decor='kaf_ink_decor',
        bg=[('0_sky', 'layer_sky'), ('0b_aurora', 'layer_aurora'), ('1_far', 'layer_far'), ('2_farmid', 'layer_farmid'),
            ('2b_haze', 'layer_haze'), ('3_mid', 'layer_mid'), ('4_blizzard', 'layer_blizzard'), ('5_snow_far', 'layer_snow_far'),
            ('6_near', 'layer_near'), ('7_snow', 'layer_snow')],
        vram=['1_far', '2_farmid', '3_mid', '6_near', '5_snow_far', '7_snow'],
        fg=[('fg_grass', 'fg_grass_strip'), ('fg_top', 'fg_top_strip'), ('flake', 'flake_particle')],
    ),
}


def _vram(b):
    spec = BIOMES[b]
    E.VRAM.update({'%s_v2_%s.png' % (b, k) for k in spec['vram']})
    E.VRAM.update({'%s_v2_soil.png' % b, '%s_v2_meadow.png' % b})


def export_bg(b, only=None):
    import importlib
    import inkkit_ortam as ik
    ik.K = 1.0 * HD
    m = importlib.import_module(BIOMES[b]['par'])
    for key, fn in BIOMES[b]['bg']:
        if only and key not in only:
            continue
        t = time.time()
        L = getattr(m, fn)()
        E.save(L.rgba8(), 'bg', '%s_v2_%s.png' % (b, key))
        print('    %.1fs' % (time.time() - t), flush=True)


def export_ground(b):
    import importlib
    import inkkit_ortam as ik
    import ink_zemin as Z
    ik.K = E.WORLD_K * HD
    G = importlib.import_module(BIOMES[b]['ground'])
    art, mask = Z.build_atlas(G.ST, G.grass_tuft, G.ceiling_roots, G.platform_cell)
    E.save(E.to8(art), 'tiles', '%s_v2.png' % b)
    E.save((np.clip(mask, 0, 1) * 255 + 0.5).astype(np.uint8), 'tiles', '%s_v2_mask.png' % b)
    soil = G.soil_texture()
    E.save(soil.rgba8(), 'tiles', '%s_v2_soil.png' % b)
    E.save(G.meadow_texture().rgba8(), 'tiles', '%s_v2_meadow.png' % b)
    meta = {
        "tile": ik.P(Z.C) // HD, "world_tile": 24, "density": ik.P(Z.C) // HD / 24.0, "cols": Z.COLS, "ground_rows": 3,
        "overlay_row": Z.OROW, "grass_cols": Z.GRASS_COLS, "ceiling_cols": Z.CEIL_COLS, "platform_row": Z.PROW,
        "ink": True, "filter": "linear_mipmap", "mask": "%s_v2_mask.png" % b, "soil_size": soil.w // HD,
        "soil_density": 2.0 * E.WORLD_K, "meadow": "%s_v2_meadow.png" % b, "glow": None,
        "not": "v2 mürekkep zemini (%s): sanat RGBA + R=toprak kaplaması, G=kenar gölgesi (CanvasTexture normal yuvasında)" % b,
    }
    json.dump(meta, open(os.path.join(A, 'tiles', '%s_v2.json' % b), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def export_fg(b):
    import importlib
    import inkkit_ortam as ik
    ik.K = 1.0 * HD
    G = importlib.import_module(BIOMES[b]['ground'])
    for key, fn in BIOMES[b]['fg']:
        r = getattr(G, fn)()
        arr = r.rgba8() if hasattr(r, 'rgba8') else E.to8(r)
        E.save(arr, 'bg', '%s_v2_%s.png' % (b, key))


def export_decor(b):
    import importlib
    import inkkit_ortam as ik
    ik.K = E.WORLD_K * HD
    D = importlib.import_module(BIOMES[b]['decor'])
    D.export(E.save, E.to8, A, b)


def export_hazard(b):
    import inkkit_ortam as ik
    import ink_tehlike as T
    ik.K = E.WORLD_K * HD
    E.save(E.to8(T.build(b)), 'tiles', 'hazards_%s_v2.png' % b)


def main():
    args = sys.argv[1:]
    biomes = [a for a in args if a in BIOMES]
    rest = [a for a in args if not a.startswith('--') and a not in BIOMES]
    flags = [a for a in args if a.startswith('--')]
    every = not flags
    for b in biomes:
        print('== %s' % b, flush=True)
        _vram(b)
        if every or '--bg' in flags:
            export_bg(b, rest or None)
        if every or '--zemin' in flags:
            export_ground(b)
        if every or '--on' in flags:
            export_fg(b)
        if every or '--suslar' in flags:
            export_decor(b)
        if every or '--tehlike' in flags:
            export_hazard(b)


if __name__ == '__main__':
    main()
