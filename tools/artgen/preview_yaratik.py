"""Çeşitlemeli yaratık önizlemesi: her çeşitleme bir satır, seçili kareler yan yana (sisli yeşil zemin, 1080p ölçeği).

python preview_yaratik.py out.png --mod cor_ink [--var cor,kan_yarasasi | --var all] [--zoom 1] [--glow] anim:kare ...
  --glow: ışıma sayfasını oyundaki gibi (x1.6 toplamalı) ekler.  anim:kare yerine --all = her animasyonun her karesi.
"""
import importlib
import sys

import numpy as np
from PIL import Image


def comp(tiles_rows, glow_rows=None):
    h, w = tiles_rows[0][0].shape[:2]
    cols = max(len(r) for r in tiles_rows)
    H, W = h * len(tiles_rows), w * cols
    yy = np.linspace(0, 1, h)[:, None, None]
    cell_bg = (np.array([0.42, 0.55, 0.48]) * (1 - yy) + np.array([0.20, 0.28, 0.26]) * yy) * np.ones((h, w, 3))
    out = np.zeros((H, W, 3))
    for r, row in enumerate(tiles_rows):
        for k in range(cols):
            bg = cell_bg.copy()
            if k < len(row):
                t = row[k]
                a = t[..., 3:4]
                bg = bg * (1 - a) + t[..., :3] * a
                if glow_rows is not None:
                    g = glow_rows[r][k]
                    bg = bg + g[..., :3] * 1.6
            out[r * h:(r + 1) * h, k * w:(k + 1) * w] = bg
    return out


def main():
    args = sys.argv[1:]
    out = args.pop(0)
    mod, var, zoom, glow = 'cor_ink', None, 1, False

    def opt(name):
        if name in args:
            i = args.index(name)
            v = args[i + 1]
            del args[i:i + 2]
            return v
        return None
    mod = opt('--mod') or mod
    var = opt('--var')
    zoom = int(opt('--zoom') or 1)
    if '--glow' in args:
        args.remove('--glow')
        glow = True
    m = importlib.import_module(mod)
    vars_ = list(m.VARIANTS) if (var is None or var == 'all') else var.split(',')
    if '--all' in args:
        args.remove('--all')
        args = ['%s:%d' % (an, k) for an, v in m.ANIMS.items() for k in range(v[0])]
    rows, grows = [], []
    for v in vars_:
        row, grow = [], []
        for a in args:
            an, fi = a.split(':')
            rgba, nm, em, info = m.render_frame(an, int(fi), v)
            row.append(rgba)
            grow.append(em)
        rows.append(row)
        grows.append(grow)
        print(v, 'tamam', flush=True)
    img = comp(rows, grows if glow else None)
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    if zoom != 1:
        im = im.resize((im.width * zoom, im.height * zoom), Image.LANCZOS)
    im.save(out)


if __name__ == '__main__':
    main()
