"""Boss v2 sayfasından kontak sayfası: her animasyon bir satır, kareler 1:1 ya da küçültülmüş (inceleme için).

python sheet_boss_ink.py <kimlik> out.png [--olcek 0.5]
"""
import json
import os
import sys

import numpy as np
from PIL import Image

import export_ink as ex


def main():
    bid, out = sys.argv[1], sys.argv[2]
    sc = float(sys.argv[sys.argv.index('--olcek') + 1]) if '--olcek' in sys.argv else 0.5
    name = bid + '_v2'
    meta = json.load(open(os.path.join(ex.SPR, name + '.json'), encoding='utf-8'))
    cw, ch = meta['cell']
    pages = [Image.open(os.path.join(ex.SPR, ex._page_name(name, k) + '.png')).convert('RGBA') for k in range(meta['pages'])]
    glows = []
    for k in range(meta['pages']):
        g = os.path.join(ex.SPR, ex._page_name(name, k) + '_e.png')
        glows.append(Image.open(g).convert('RGBA').resize(pages[k].size, Image.BILINEAR) if os.path.exists(g) else None)
    names = sorted(meta['anims'], key=lambda a: (meta['anims'][a]['page'], meta['anims'][a]['row']))
    mx = max(meta['anims'][a]['frames'] for a in names)
    W, H = int(cw * sc), int(ch * sc)
    sheet = Image.new('RGB', (W * mx, H * len(names)))
    yy = np.linspace(0, 1, H)[:, None, None]
    bg = ((np.array([0.42, 0.55, 0.48]) * (1 - yy) + np.array([0.18, 0.24, 0.24]) * yy) * np.ones((H, W, 3)) * 255).astype(np.uint8)
    for r, an in enumerate(names):
        a = meta['anims'][an]
        for i in range(a['frames']):
            row, col = a['row'] + i // a['cols'], i % a['cols']
            box = (col * cw, row * ch, (col + 1) * cw, (row + 1) * ch)
            fr = pages[a['page']].crop(box).resize((W, H), Image.LANCZOS)
            tile = Image.fromarray(bg.copy()).convert('RGBA')
            tile.alpha_composite(fr)
            if glows[a['page']] is not None:
                g = np.asarray(glows[a['page']].crop(box).resize((W, H), Image.BILINEAR), np.float32) / 255.0
                t = np.asarray(tile, np.float32) / 255.0
                t[..., :3] = np.clip(t[..., :3] + g[..., :3] * g[..., 3:4] * 0.6, 0, 1)
                tile = Image.fromarray((t * 255).astype(np.uint8))
            sheet.paste(tile.convert('RGB'), (i * W, r * H))
    sheet.save(out, quality=90)
    print(out, sheet.size)


if __name__ == '__main__':
    main()
