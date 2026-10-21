"""v39: yeni yaratıkların mürekkep-cel sayfaları (assets/sprites/<kimlik>_v2.{png,json} + _e).

Kullanım (tools/artgen içinde):
    python export_v39.py                         hepsi
    python export_v39.py yer_cucesi burkut       yalnızca bu kimlikler
    KY_HD=2 python export_v39.py [kimlik ...]    HD x2 paketi (assets_hd/x2; sonra python hd_paket.py --paketle)
    python export_v39.py --onizle <kimlik> <çıktı.png>   bütün satırların bütün kareleri (sisli zemin, ışıma x1,6)
    KY_PAR=4                                     süreç havuzu boyu (varsayılan 3; 0 = sıralı)

Çizim modülleri `y39_<ad>.py` (sözleşme, export_ucan.py ile aynı):
  TEX, CELL (px), FEET (px, ayak orijini), anims_for(kimlik) -> {satır: {frames, fps, loop, ts?, mk?, vx?}} (sıra = satır
  sırası, ilk satır "idle" ya da "fly"), durum_for(kimlik) -> kısa biçim "durum" sözlüğü (docs/v29/enemy_anim_json.md),
  render_frame(satır, i, kimlik) -> (rgba, None, em, {çapa: (x, y)}).
Satır düzeni v1 json'undan değil doğrudan modülden gelir (yeni yaratıkların v1 sayfası yoktur).
"""
import functools
import json
import os
import sys

import numpy as np

import export_ink as ex

# kimlik -> çizim modülü (yavrular / çeşitlemeler aynı modülde)
CREATURES = {
    'yer_cucesi': 'y39_yer_cucesi', 'kor_solucani': 'y39_kor_solucani',
    'sulmus': 'y39_sulmus', 'sulmus_yavrusu': 'y39_sulmus_yavrusu',
    'burkut': 'y39_burkut', 'ejder_yavrusu': 'y39_ejder_yavrusu', 'ag_ana': 'y39_ag_ana',
    'tunga_hayaleti': 'y39_tunga_hayaleti', 'yasavul': 'y39_yasavul', 'aldaras': 'y39_aldaras',
    'tepegoz_yavrusu': 'y39_tepegoz_yavrusu', 'abasi': 'y39_abasi', 'agu_kurbagasi': 'y39_agu_kurbagasi',
    'kar_cadisi': 'y39_kar_cadisi', 'yilan_kami': 'y39_yilan_kami',
}


def _par(mod, var, job):
    import importlib
    m = importlib.import_module(mod)
    rgba, nm, em, info = m.render_frame(job[0], job[1], var)
    if ex.HD > 1:
        em = em[..., 3:4].max().reshape(1, 1, 1) * np.ones((1, 1, 4), np.float32)
        return rgba.astype(np.float16), None, em, info
    return rgba, None, em, info


def _check(var, rows, durum):
    for k, v in durum.items():
        a = v if isinstance(v, str) else v.get('a')
        assert a in rows, '%s: durum %s -> satır yok: %s' % (var, k, a)
    for an, r in rows.items():
        if r.get('ts'):
            assert len(r['ts']) == r['frames'], '%s/%s: ts uzunluğu' % (var, an)
        if r.get('mk'):
            assert len(r['mk']) == 3 and 0 < r['mk'][0] <= r['mk'][1] <= r['mk'][2] < 1, '%s/%s: mk' % (var, an)


def export(var):
    import importlib
    mod = CREATURES[var]
    m = importlib.import_module(mod)
    rows = m.anims_for(var)
    durum = m.durum_for(var)
    _check(var, rows, durum)
    lay = {'anims': {an: {'row': i, 'frames': r['frames'], 'fps': r['fps'], 'loop': r['loop'], 'arm': False}
                     for i, (an, r) in enumerate(rows.items())}}
    am = {}
    for an, r in rows.items():
        e = {}
        if r.get('ts'):
            e['ts'] = [round(x, 4) for x in r['ts']]
        if r.get('mk'):
            e['mk'] = [round(x, 4) for x in r['mk']]
            e['v29'] = True
        if r.get('vx'):
            e['vx'] = round(float(r['vx']), 2)
        if e:
            am[an] = e
    assert max(r['frames'] for r in rows.values()) * m.CELL[0] <= ex.PAGE_MAX, var + ': satır 4096 pikseli aşıyor'
    npar = int(os.environ.get('KY_PAR', '3') or '0')
    par = functools.partial(_par, mod, var) if npar > 0 else None
    if par is not None:
        os.environ['KY_PAR_N'] = str(npar)
    ex.export_sheet(var + '_v2', lay, lambda an, i: m.render_frame(an, i, var), m.CELL, m.FEET, m.TEX,
                    anim_meta=am, extra_meta={'durum': durum, 'v29': True, 'v39': True}, par=par)
    if ex.HD == 1:
        import export_ucan
        export_ucan.half_glow(var + '_v2')


def onizle(var, out, scale=1.0):
    """Bütün satırlar: her satır bir sıra, sisli soğuk zemin (oyundaki gibi koyu), ışıma x1,6 toplamalı."""
    import importlib
    from PIL import Image, ImageDraw
    m = importlib.import_module(CREATURES[var])
    rows = m.anims_for(var)
    w, h = m.CELL
    cols = max(r['frames'] for r in rows.values())
    W, H = cols * w, len(rows) * h
    yy = np.linspace(0, 1, h)[:, None, None]
    bg0 = (np.array([0.20, 0.23, 0.30]) * (1 - yy) + np.array([0.08, 0.09, 0.13]) * yy) * np.ones((h, w, 3))
    out_im = np.zeros((H, W, 3))
    for r, (an, row) in enumerate(rows.items()):
        for i in range(row['frames']):
            rgba, _n, em, _info = m.render_frame(an, i, var)
            a = rgba[..., 3:4]
            c = bg0 * (1 - a) + rgba[..., :3] * a
            c = c + em[..., :3] * em[..., 3:4] * 1.6 if em.shape[-1] == 4 else c
            out_im[r * h:(r + 1) * h, i * w:(i + 1) * w] = np.clip(c, 0, 1)
    im = Image.fromarray((out_im * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for r, an in enumerate(rows):
        d.text((4, r * h + 4), an, fill=(255, 230, 160))
        d.line([(0, r * h), (W, r * h)], fill=(60, 60, 70))
    if scale != 1.0:
        im = im.resize((int(W * scale), int(H * scale)), Image.LANCZOS)
    im.save(out)
    print('önizleme', out, im.size)


def main():
    args = sys.argv[1:]
    if args and args[0] == '--onizle':
        onizle(args[1], args[2], float(args[3]) if len(args) > 3 else 0.5)
        return
    only = [a for a in args if not a.startswith('--')]
    for var in CREATURES:
        if only and var not in only:
            continue
        print('==', var, flush=True)
        export(var)


if __name__ == '__main__':
    main()
