"""Stil v2 "mürekkep-cel" dışa aktarımı (inkkit.py). v1 dosyalarına DOKUNMAZ; *_v2 adlı varlıkları yazar.

Kullanım:  python export_ink.py               (hepsi)
           python export_ink.py --bengu       assets/sprites/bengu_v2.{png,json} (+_e) ve bengu_kol_v2.{png,json}
           python export_ink.py --kara_boru   assets/sprites/kara_boru_v2.{png,json} (+_e)
           python export_ink.py --bengu idle run   yalnızca bu animasyonlar yeniden çizilir (diğer satırlar korunur)

Sayfa düzeni (satır sırası, kare sayısı, fps, döngü, kol bayrağı) v1/v2 json'undan alınır: oyun kodu aynı adlarla çalışır.
Meta: "texel": 4 (v2 kamerası 2,0 yakın: 1080p'de 1 doku pikseli = 1 ekran pikseli), "filter": "linear" (oyunda doğrusal
süzgeç + mipmap ve ink_char.gdshader). Normal haritası YAZILMAZ: cel gölgesi dokuda; sahne ışığı yalnızca renk/şiddet taşır.

Sayfalar: bir sayfa en çok PAGE_MAX piksel yüksek (eski/tümleşik GPU'larda 8192 sınırının altında kalır). Satırlar sırayla
sayfalara bölünür: <ad>.png (0. sayfa), <ad>_p1.png, <ad>_p2.png ... (+ her birinin _e ışıma sayfası); json "page_rows"
(sayfa başına satır) ve "pages" (sayfa sayısı). Data.sprite / SpriteAnim satırın sayfasını seçer (sayfasız eski json da çalışır).
Büyük sayfalar VRAM sıkıştırmalı (BPTC, yüksek kalite) + mipmap içe aktarılır.
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


PAGE_MAX = 4096

IMPORT_TMPL = """[remap]

importer="texture"
type="CompressedTexture2D"

[deps]

source_file="res://assets/sprites/{name}"

[params]

compress/mode={mode}
compress/high_quality={hq}
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


def _import(path, vram):
    """.import: mipmap açık; büyük sayfalarda BPTC (mode 2, yüksek kalite), küçüklerde kayıpsız. Var olan dosyada
    uid korunur, yalnızca sıkıştırma/mipmap satırları düzeltilir."""
    imp = path + '.import'
    mode, hq = ('2', 'true') if vram else ('0', 'false')
    if os.path.exists(imp):
        txt = open(imp, encoding='utf-8').read()
        import re
        new = re.sub(r'compress/mode=\d', 'compress/mode=' + mode, txt)
        new = re.sub(r'compress/high_quality=\w+', 'compress/high_quality=' + hq, new)
        new = new.replace('mipmaps/generate=false', 'mipmaps/generate=true')
        if new != txt:
            open(imp, 'w', encoding='utf-8', newline='\n').write(new)
    else:
        open(imp, 'w', encoding='utf-8', newline='\n').write(IMPORT_TMPL.format(name=os.path.basename(path), mode=mode, hq=hq))


def _png(arr, path, vram=None):
    a = np.clip(arr * 255.0 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(a, 'RGBA').save(path, optimize=True)
    _import(path, (a.shape[0] * a.shape[1] > 2_000_000) if vram is None else vram)


def _page_name(name, k):
    return name if k == 0 else '%s_p%d' % (name, k)


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
    out_json = os.path.join(SPR, name + '.json')
    rpp = max(1, PAGE_MAX // ch)
    old = None
    if only and os.path.exists(out_json):
        o = json.load(open(out_json, encoding='utf-8'))
        if o.get('filter') == 'linear' and o['cell'] == list(cell):
            old = o
    if old:
        al, gl = [], []
        for k in range(int(old.get('pages', 1))):
            pn = os.path.join(SPR, _page_name(name, k))
            a_ = np.asarray(Image.open(pn + '.png').convert('RGBA'), np.float32) / 255.0
            al.append(a_)
            gl.append(np.asarray(Image.open(pn + '_e.png').convert('RGBA'), np.float32) / 255.0
                      if os.path.exists(pn + '_e.png') else np.zeros_like(a_))
        alb = np.zeros((len(names) * ch, cols * cw, 4), np.float32)
        glo = np.zeros_like(alb)
        y = 0
        for a_, g_ in zip(al, gl):
            alb[y:y + a_.shape[0], :a_.shape[1]] = a_
            glo[y:y + g_.shape[0], :g_.shape[1]] = g_
            y += a_.shape[0]
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
    n_pages = (len(names) + rpp - 1) // rpp
    has_glow = glo[..., 3].max() > 0
    for k in range(n_pages):
        pn = os.path.join(SPR, _page_name(name, k))
        ys = slice(k * rpp * ch, min(len(names), (k + 1) * rpp) * ch)
        _png(alb[ys], pn + '.png')
        if has_glow:
            _png(glo[ys], pn + '_e.png')
        print('  sayfa', _page_name(name, k), alb[ys].shape[1], alb[ys].shape[0])
    # artık kullanılmayan eski sayfa dosyaları
    k = n_pages
    while os.path.exists(os.path.join(SPR, _page_name(name, k) + '.png')):
        for suf in ('.png', '.png.import', '_e.png', '_e.png.import'):
            f = os.path.join(SPR, _page_name(name, k) + suf)
            if os.path.exists(f):
                os.remove(f)
        k += 1
    meta['glow'] = bool(has_glow)
    meta['texel'] = texel
    meta['page_rows'] = rpp
    meta['pages'] = n_pages
    json.dump(meta, open(out_json, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print('sprite', name, alb.shape[1], alb.shape[0], 'sayfa', n_pages)


def export_bengu(only=()):
    import bengu_ink as b
    export_sheet('bengu_v2', 'bengu.json',
                 lambda an, i: b.render_frame(an, i), b.CELL, b.FEET, b.TEX, only)
    # kol parçaları: 0. satır sol üst ışık, 1. satır ışık parça ekseninde aynalanmış ("alt_row"; ink_char karıştırır)
    cw, ch = b.ARM_CELL
    rows = [b.render_arm_parts(), b.render_arm_parts(mirror=True)]
    alb = np.zeros((ch * len(rows), cw * len(rows[0]), 4), np.float32)
    for r, parts in enumerate(rows):
        for i, rgba in enumerate(parts):
            alb[r * ch:(r + 1) * ch, i * cw:(i + 1) * cw] = rgba
    _png(alb, os.path.join(SPR, 'bengu_kol_v2.png'), vram=False)
    json.dump({'cell': list(b.ARM_CELL), 'pivot': list(b.ARM_PIVOT), 'fist_pivot': list(b.FIST_PIVOT), 'texel': b.TEX,
               'filter': 'linear', 'upper_len': b.L_UP, 'fore_len': b.L_FORE, 'alt_row': 1,
               'parts': ['upper', 'fore', 'fist', 'upper_b', 'fore_b', 'fist_b']},
              open(os.path.join(SPR, 'bengu_kol_v2.json'), 'w', encoding='utf-8', newline='\n'), indent=1)
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
