"""Stil v2 "mürekkep": yurt, süsler, toplanabilirler, mermiler, tehlike karoları ve dünya efektleri (v1 dosyalarına dokunmaz).

Kullanım:  python export_sus.py                 (hepsi)
           python export_sus.py --yurt [ad...]  Ulu Kayın Yurdu süsleri     assets/decor/yh_*_v2.png  (sus_v2.json)
           python export_sus.py --yurt-bg       yurt paralaks katmanları    assets/bg/yurt_v2_*.png
           python export_sus.py --suslar        ortak süsler (sunak, totem, kapı, ruh taşı, bulut)   assets/decor/*_v2.png
           python export_sus.py --atlas         toplanabilirler + mermiler  assets/fx/ink/sus_v2.png + sus_v2.json
           python export_sus.py --tehlike       tehlike karoları            assets/tiles/hazards_v2{,_e}.png
           python export_sus.py --efekt         mürekkep kare animasyonları assets/fx/anim/<ad>_v2.png + anim_v2.json
           python export_sus.py --tuccar        v24 bezirgân kervanı (tezgâh) assets/decor/bezirgan_kervan_v2.png (sus_v2.json)
           python export_sus.py --usta          v32 konak ateşi + Bengisu'nun tezgâhı assets/decor/{konak_ates,usta_tezgah}_v2.png
Hepsi yordamsal (skia-python + numpy), dışarıdan doku yok. Her PNG için mipmap'li .import yazılır; oyunda doğrusal süzgeç.
Süs meta biçimi decor_v2.json ile aynı ("size", "origin" doku pikseli, "texel" doku pikseli / dünya birimi, "glow");
Level._decor_v2 her iki dosyayı okur (biyom süsleri decor_v2.json'da, bunlar sus_v2.json'da: dosya çakışması olmaz).
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.normpath(os.path.join(HERE, '..', '..', 'assets'))
sys.path.insert(0, HERE)

import hdpack  # noqa: E402,F401  (KY_HD=2: PNG yazımları assets_hd/x2'ye, json'lar .godot/hd_meta'ya)
from hdpack import HD  # noqa: E402
from export_ink_ortam import save as _save_raw, VRAM  # noqa: E402

TEXEL = 4.0


def to8(arr):
    return (np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)


def save(arr8, sub, name, vram=False):
    if vram:
        VRAM.add(name)
    _save_raw(arr8, sub, name)


def _meta_path():
    return os.path.join(A, 'decor', 'sus_v2.json')


def load_meta():
    p = _meta_path()
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}


def write_meta(meta):
    json.dump(dict(sorted(meta.items())), open(_meta_path(), 'w', encoding='utf-8', newline='\n'), indent=1, ensure_ascii=False)


def put_decor(meta, name, res):
    rgba, glow, origin = res
    h, w = rgba.shape[:2]
    h, w = h // HD, w // HD   # HD paketi: doku HD kat; meta (boyut, köken) temel doku pikseli kalır
    big = w * h > 600_000
    save(to8(rgba), 'decor', name + '_v2.png', vram=big)
    entry = {"size": [int(w), int(h)], "origin": [int(round(origin[0])), int(round(origin[1]))], "texel": TEXEL}
    gp = os.path.join(A, 'decor', name + '_v2_e.png')
    if glow[..., 3].max() > 0.02:
        save(to8(glow), 'decor', name + '_v2_e.png')
        entry["glow"] = True
    else:
        for f in (gp, gp + '.import'):
            if os.path.exists(f):
                os.remove(f)
    meta[name + '_v2'] = entry


def export_yurt(only=None):
    import yurt_ink as Y
    meta = load_meta()
    for n, fn in Y.ALL.items():
        if only and n not in only:
            continue
        t = time.time()
        put_decor(meta, n, fn())
        print('    %s %.1fs' % (n, time.time() - t), flush=True)
    write_meta(meta)


def export_yurt_bg(only=None):
    import inkkit_ortam as ko
    import yurt_ink_bg as B
    ko.K = 1.0 * HD
    for key, fn in B.LAYERS:
        if only and key not in only:
            continue
        t = time.time()
        L = fn()
        save(L.rgba8(), 'bg', 'yurt_v2_%s.png' % key, vram=key in B.VRAM_KEYS)
        print('    %.1fs' % (time.time() - t), flush=True)


def export_suslar(only=None):
    import sus_ink as S
    meta = load_meta()
    for n, fn in S.DECOR.items():
        if only and n not in only:
            continue
        put_decor(meta, n, fn())
        print('   ', n, flush=True)
    write_meta(meta)


def export_tuccar(only=None):
    import tuccar_ink as T
    meta = load_meta()
    for n, fn in T.ALL.items():
        if only and n not in only:
            continue
        put_decor(meta, n, fn())
        print('   ', n, flush=True)
    write_meta(meta)


def export_usta(only=None):
    """v32 konak süsleri (usta_ink.py): konak ateşi ve Bengisu'nun gezgin tezgâhı (sus_v2.json)."""
    import usta_ink as U
    meta = load_meta()
    for n, fn in U.ALL.items():
        if only and n not in only:
            continue
        put_decor(meta, n, fn())
        print('   ', n, flush=True)
    write_meta(meta)


def export_atlas():
    import sus_ink as S
    S.export_atlas(save, to8, A)


def export_tehlike():
    import sus_ink as S
    S.export_hazards(save, to8, A)


def export_efekt(only=None):
    import sus_fx as F
    F.export(save, to8, A, only)


def main():
    args = sys.argv[1:]
    every = not any(a.startswith('--') for a in args)
    rest = [a for a in args if not a.startswith('--')] or None
    if every or '--yurt' in args:
        export_yurt(rest)
    if every or '--yurt-bg' in args:
        export_yurt_bg(rest)
    if every or '--suslar' in args:
        export_suslar(rest)
    if every or '--atlas' in args:
        export_atlas()
    if every or '--tehlike' in args:
        export_tehlike()
    if every or '--efekt' in args:
        export_efekt(rest)
    if every or '--tuccar' in args:
        export_tuccar(rest)
    if every or '--usta' in args:
        export_usta(rest)


if __name__ == '__main__':
    main()
