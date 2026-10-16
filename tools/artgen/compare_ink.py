"""Referans (1080p ölçeğinde) ile mürekkep-cel karelerini aynı ölçekte yan yana koyar.

python compare_ink.py referans.png out.png [--mod bengu_ink] [--zoom 2] anim:kare ...
"""
import importlib
import sys

import numpy as np
from PIL import Image


def main():
    args = sys.argv[1:]
    ref, out = args.pop(0), args.pop(0)
    mod, zoom = 'bengu_ink', 2
    if '--mod' in args:
        i = args.index('--mod'); mod = args[i + 1]; del args[i:i + 2]
    if '--zoom' in args:
        i = args.index('--zoom'); zoom = int(args[i + 1]); del args[i:i + 2]
    m = importlib.import_module(mod)
    R = Image.open(ref).convert('RGB')
    s = 1080 / R.size[1]
    R = R.resize((int(R.size[0] * s), 1080), Image.LANCZOS)
    rc = R.crop((int(460 * s), int(560 * s), int(880 * s), int(735 * s)))   # iki ayakta ninja
    tiles = [m.render_frame(a.split(':')[0], int(a.split(':')[1]))[0] for a in args]
    h = max(rc.size[1], tiles[0].shape[0])
    W = rc.size[0] + sum(t.shape[1] for t in tiles)
    canvas = Image.new('RGB', (W, h), (60, 80, 70))
    canvas.paste(rc, (0, h - rc.size[1]))
    # oyun karesine benzer zemin: referansın sis tonundan
    x = rc.size[0]
    bgc = np.array(rc)[:40, :].reshape(-1, 3).mean(0) / 255.0
    for t in tiles:
        th, tw = t.shape[:2]
        bg = np.ones((th, tw, 3)) * bgc
        a = t[..., 3:4]
        comp = bg * (1 - a) + t[..., :3] * a
        canvas.paste(Image.fromarray((comp * 255).astype(np.uint8)), (x, h - th))
        x += tw
    if zoom != 1:
        canvas = canvas.resize((W * zoom, h * zoom), Image.LANCZOS)
    canvas.save(out)


if __name__ == '__main__':
    main()
