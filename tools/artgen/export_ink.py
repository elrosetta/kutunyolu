"""Stil v2 "mürekkep" Ötüken ortamını dışa aktarır (v1 dosyalarına dokunmaz).

Kullanım:  python export_ink.py                 (hepsi)
           python export_ink.py --bg            paralaks katmanları  assets/bg/otuken_v2_*.png
           python export_ink.py --zemin         karo atlası + maske + toprak  assets/tiles/otuken_v2*
           python export_ink.py --on            ön plan şeritleri + yaprak  assets/bg/otuken_v2_fg_*.png
           python export_ink.py --suslar        süsler  assets/decor/*_v2.png + decor_v2.json
Her PNG için mipmap'li .import yazılır (oyunda doğrusal süzgeç + mipmap; v1 keskin piksel kalır).
Oyunda katman listesi ve parallaks çarpanları: data/stil_v2.json ("otuken").
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.normpath(os.path.join(HERE, '..', '..', 'assets'))

IMPORT_TMPL = """[remap]

importer="texture"
type="CompressedTexture2D"

[deps]

source_file="res://{rel}"

[params]

compress/mode=0
compress/high_quality=false
compress/lossy_quality=0.7
compress/uastc_level=0
compress/rdo_quality_loss=0.0
compress/hdr_compression=1
compress/normal_map=0
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
detect_3d/compress_to=1
"""


def save(arr8, sub, name):
    from PIL import Image
    path = os.path.join(A, sub, name)
    Image.fromarray(arr8, 'RGBA').save(path, optimize=True)
    imp = path + '.import'
    rel = 'assets/%s/%s' % (sub, name)
    # mevcut .import'u (uid'li) koru, yalnızca mipmap ayarını aç; yoksa şablon yaz
    if os.path.exists(imp):
        txt = open(imp, encoding='utf-8').read()
        if 'mipmaps/generate=false' in txt:
            open(imp, 'w', encoding='utf-8').write(txt.replace('mipmaps/generate=false', 'mipmaps/generate=true'))
    else:
        open(imp, 'w', encoding='utf-8').write(IMPORT_TMPL.format(rel=rel))
    print('  %s/%s %dx%d' % (sub, name, arr8.shape[1], arr8.shape[0]), flush=True)


def to8(a):
    """önçarpılmış float -> düz RGBA8"""
    al = a[..., 3:4]
    rgb = np.where(al > 1e-5, a[..., :3] / np.maximum(al, 1e-5), 0)
    return (np.clip(np.concatenate([rgb, al], -1), 0, 1) * 255 + 0.5).astype(np.uint8)


BG = [('0_sky', 'layer_sky'), ('1_far', 'layer_far'), ('2_farmid', 'layer_farmid'), ('3_mid', 'layer_mid'),
      ('4_fog', 'layer_fogband'), ('5_shafts', 'layer_shafts'), ('6_near', 'layer_near')]


def export_bg(only=None):
    import otuken_ink as O
    for key, fn in BG:
        if only and key not in only:
            continue
        t = time.time()
        L = getattr(O, fn)()
        save(L.rgba8(), 'bg', 'otuken_v2_%s.png' % key)
        print('    %.1fs' % (time.time() - t))


def export_ground():
    import otuken_ink_ground as G
    art, mask = G.build_atlas()
    save(to8(art), 'tiles', 'otuken_v2.png')
    m8 = (np.clip(mask, 0, 1) * 255 + 0.5).astype(np.uint8)
    save(m8, 'tiles', 'otuken_v2_mask.png')
    soil = G.soil_texture()
    save(soil.rgba8(), 'tiles', 'otuken_v2_soil.png')
    save(G.meadow_texture().rgba8(), 'tiles', 'otuken_v2_meadow.png')
    meta = {
        "tile": G.C, "world_tile": 24, "density": G.C / 24.0, "cols": G.COLS, "ground_rows": 3,
        "overlay_row": G.OROW, "grass_cols": G.GRASS_COLS, "ceiling_cols": G.CEIL_COLS, "platform_row": G.PROW,
        "ink": True, "filter": "linear_mipmap", "mask": "otuken_v2_mask.png", "soil_size": soil.w,
        "soil_density": 2.0, "meadow": "otuken_v2_meadow.png", "glow": None,
        "not": "v2 mürekkep zemini: sanat RGBA + R=toprak kaplaması, G=kenar gölgesi (CanvasTexture normal yuvasında)",
    }
    json.dump(meta, open(os.path.join(A, 'tiles', 'otuken_v2.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    # eski piksel v2 zemininin normal haritaları artık kullanılmıyor
    for old in ('otuken_v2_n.png', 'otuken_v2_soil_n.png'):
        for p in (os.path.join(A, 'tiles', old), os.path.join(A, 'tiles', old + '.import')):
            if os.path.exists(p):
                os.remove(p)


def export_fg():
    import otuken_ink_ground as G
    save(G.fg_grass_strip().rgba8(), 'bg', 'otuken_v2_fg_grass.png')
    save(G.fg_top_strip().rgba8(), 'bg', 'otuken_v2_fg_top.png')
    save(to8(G.leaf_particle()), 'bg', 'otuken_v2_leaf.png')


def export_decor():
    import otuken_ink_decor as D
    D.export(save, to8, A)


def main():
    args = sys.argv[1:]
    every = not any(a.startswith('--') for a in args)
    rest = [a for a in args if not a.startswith('--')]
    if every or '--bg' in args:
        export_bg(rest or None)
    if every or '--zemin' in args:
        export_ground()
    if every or '--on' in args:
        export_fg()
    if every or '--suslar' in args:
        export_decor()
    # eski piksel v2 orta katmanı yerini mürekkep katmanlarına bıraktı
    for p in (os.path.join(A, 'bg', 'otuken_3_mid_v2.png'), os.path.join(A, 'bg', 'otuken_3_mid_v2.png.import')):
        if os.path.exists(p):
            os.remove(p)


if __name__ == '__main__':
    main()
