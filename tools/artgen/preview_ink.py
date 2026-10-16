"""Mürekkep-cel önizleme: seçili karelerin sisli yeşil zemin üzerinde yan yana dizilmesi.

python preview_ink.py out.png [--mod bengu_ink] [--zoom 2] anim:kare anim:kare ...
"""
import importlib
import sys
import time

import numpy as np
from PIL import Image


def main():
    args = sys.argv[1:]
    out = args.pop(0)
    mod = 'bengu_ink'
    zoom = 2
    if '--mod' in args:
        i = args.index('--mod'); mod = args[i + 1]; del args[i:i + 2]
    if '--zoom' in args:
        i = args.index('--zoom'); zoom = int(args[i + 1]); del args[i:i + 2]
    m = importlib.import_module(mod)
    cols = 0
    if '--all' in args:   # her animasyondan bir kare (saldırılarda darbe karesi 3), ızgara
        args.remove('--all')
        args = ['%s:%d' % (an, (3 if v[0] == 8 and an.startswith('atk') else v[0] // 2)) for an, v in m.ANIMS.items()]
        cols = 8
    if '--anim' in args:  # tek animasyonun bütün kareleri
        i = args.index('--anim'); an = args[i + 1]
        args = ['%s:%d' % (an, k) for k in range(m.ANIMS[an][0])]
    tiles = []
    for a in args:
        an, fi = a.split(':')
        t0 = time.time()
        rgba, nm, em, info = m.render_frame(an, int(fi))
        tiles.append(rgba)
    h, w = tiles[0].shape[:2]
    if cols:
        rows = (len(tiles) + cols - 1) // cols
        blank = np.zeros_like(tiles[0])
        tiles = tiles + [blank] * (rows * cols - len(tiles))
        tiles = [np.concatenate(tiles[r * cols:(r + 1) * cols], 1) for r in range(rows)]
        tiles = [np.concatenate(tiles, 0)]
        h, w = tiles[0].shape[:2]
    W = w * len(tiles)
    yy = np.linspace(0, 1, h)[:, None, None]
    bg = (np.array([0.42, 0.55, 0.48]) * (1 - yy) + np.array([0.20, 0.28, 0.26]) * yy) * np.ones((h, W, 3))
    for k, t in enumerate(tiles):
        a = t[..., 3:4]
        bg[:, k * w:(k + 1) * w] = bg[:, k * w:(k + 1) * w] * (1 - a) + t[..., :3] * a
    img = Image.fromarray((np.clip(bg, 0, 1) * 255).astype(np.uint8))
    if zoom != 1:
        img = img.resize((W * zoom, h * zoom), Image.LANCZOS)
    img.save(out)


if __name__ == '__main__':
    main()
