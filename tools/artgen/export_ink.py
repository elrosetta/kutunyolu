"""Stil v2 "mürekkep-cel" dışa aktarımı (inkkit.py). v1 dosyalarına DOKUNMAZ; *_v2 adlı varlıkları yazar.

Kullanım:  python export_ink.py               (hepsi)
           python export_ink.py --bengu       assets/sprites/bengu_v2.{png,json} (+_e) ve bengu_kol_v2.{png,json}
           python export_ink.py --kara_boru   assets/sprites/kara_boru_v2.{png,json} (+_e)
           python export_ink.py --bengu idle run   yalnızca bu animasyonlar yeniden çizilir (diğer satırlar korunur)

Sayfa düzeni (satır sırası, kare sayısı, fps, döngü, kol bayrağı) v1/v2 json'undan alınır: oyun kodu aynı adlarla çalışır.
Meta: "texel": 3 (1080p'de 1 doku pikseli = 1 ekran pikseli), "filter": "linear" (oyunda doğrusal süzgeç + mipmap ve
ink_char.gdshader). Normal haritası YAZILMAZ: cel gölgesi dokuda; sahne ışığı yalnızca renk/şiddet taşır (bkz. TASARIM.md).
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = os.path.join(ROOT, 'assets')
SPR = os.path.join(A, 'sprites')


def ang_of(a):
    return math.atan2(math.cos(a), math.sin(a))


def _png(arr, path):
    a = np.clip(arr * 255.0 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(a, 'RGBA').save(path, optimize=True)


def _frame_meta(info):
    fr = {}
    for k in ('hand_f', 'hand_b', 'mouth', 'hand', 'head', 'sh_f', 'sh_b'):
        if info and k in info:
            fr[k] = [round(info[k][0], 2), round(info[k][1], 2)]
    for k in ('arm', 'arm_b'):
        if info and k in info:
            fr[k] = [round(info[k][0], 4), round(info[k][1], 4)]
    for k in ('ang_f', 'ang_b'):
        if info and k in info:
            fr[k] = round(ang_of(info[k]), 4)
    return fr


def export_sheet(name, layout_json, render, cell, origin, texel, only=(), extra_meta=None):
    """layout_json: satır düzeninin alındığı mevcut json (ör. bengu_v2.json). render(anim, i) -> (rgba, nm, em, info)."""
    lay = json.load(open(os.path.join(SPR, layout_json), encoding='utf-8'))
    names = sorted(lay['anims'].keys(), key=lambda a: lay['anims'][a]['row'])
    cols = max(lay['anims'][a]['frames'] for a in names)
    cw, ch = cell
    out_png = os.path.join(SPR, name + '.png')
    out_e = os.path.join(SPR, name + '_e.png')
    out_json = os.path.join(SPR, name + '.json')
    old = None
    if only and os.path.exists(out_json):
        o = json.load(open(out_json, encoding='utf-8'))
        if o.get('filter') == 'linear' and o['cell'] == list(cell):
            old = o
    if old:
        alb = np.asarray(Image.open(out_png).convert('RGBA'), np.float32) / 255.0
        glo = np.asarray(Image.open(out_e).convert('RGBA'), np.float32) / 255.0 if os.path.exists(out_e) else np.zeros_like(alb)
        alb, glo = alb.copy(), glo.copy()
        meta = old
    else:
        alb = np.zeros((len(names) * ch, cols * cw, 4), np.float32)
        glo = np.zeros_like(alb)
        meta = {'cell': list(cell), 'origin': list(origin), 'texel': texel, 'filter': 'linear', 'anims': {}}
        if extra_meta:
            meta.update(extra_meta)
    for r, an in enumerate(names):
        if old and an not in only:
            continue
        la = lay['anims'][an]
        n = la['frames']
        frames = []
        for i in range(n):
            rgba, nm, em, info = render(an, i)
            ys, xs = slice(r * ch, (r + 1) * ch), slice(i * cw, (i + 1) * cw)
            alb[ys, xs] = rgba
            ga = em[..., 3]
            glo[ys, xs, :3] = np.where(ga[..., None] > 1e-4, em[..., :3] / np.maximum(ga[..., None], 1e-4), 0)
            glo[ys, xs, 3] = ga
            frames.append(_frame_meta(info))
        meta['anims'][an] = {'row': r, 'frames': n, 'fps': la['fps'], 'loop': la['loop'], 'data': frames, 'arm': la.get('arm', True)}
        print(' ', name, an, n)
    _png(alb, out_png)
    if glo[..., 3].max() > 0:
        _png(glo, out_e)
        meta['glow'] = True
    json.dump(meta, open(out_json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('sprite', name, alb.shape[1], alb.shape[0])


def export_bengu(only=()):
    import bengu_ink as b
    export_sheet('bengu_v2', 'bengu.json',
                 lambda an, i: b.render_frame(an, i), b.CELL, b.FEET, b.TEX, only)
    parts = b.render_arm_parts()
    cw, ch = b.ARM_CELL
    alb = np.zeros((ch, cw * len(parts), 4), np.float32)
    for i, rgba in enumerate(parts):
        alb[:, i * cw:(i + 1) * cw] = rgba
    _png(alb, os.path.join(SPR, 'bengu_kol_v2.png'))
    json.dump({'cell': list(b.ARM_CELL), 'pivot': list(b.ARM_PIVOT), 'fist_pivot': list(b.FIST_PIVOT), 'texel': b.TEX,
               'filter': 'linear', 'upper_len': b.L_UP, 'fore_len': b.L_FORE,
               'parts': ['upper', 'fore', 'fist', 'upper_b', 'fore_b', 'fist_b']},
              open(os.path.join(SPR, 'bengu_kol_v2.json'), 'w', encoding='utf-8'), indent=1)
    print('sprite bengu_kol_v2', alb.shape)


def export_kara_boru(only=()):
    import kara_boru_ink as kb
    export_sheet('kara_boru_v2', 'kara_boru.json', lambda an, i: kb.render_frame(an, i), kb.CELL, kb.FEET, kb.TEX, only)


def main():
    args = sys.argv[1:]
    flags = [a for a in args if a.startswith('--')]
    only = tuple(a for a in args if not a.startswith('--'))
    every = not flags
    if every or '--bengu' in flags:
        export_bengu(only)
    if every or '--kara_boru' in flags:
        export_kara_boru(only)


if __name__ == '__main__':
    main()
