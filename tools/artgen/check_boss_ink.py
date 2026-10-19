"""Boss v2 sayfasında hücre kenarına değen (kırpılan) kareleri ve kare başına doluluk kutusunu yazar.

python check_boss_ink.py <kimlik>
"""
import json
import os
import sys

import numpy as np
from PIL import Image

import export_ink as ex


def main():
    bid = sys.argv[1]
    name = bid + '_v2'
    meta = json.load(open(os.path.join(ex.SPR, name + '.json'), encoding='utf-8'))
    cw, ch = meta['cell']
    ox, oy = meta['origin']
    tx = meta['texel']
    pages = [np.asarray(Image.open(os.path.join(ex.SPR, ex._page_name(name, k) + '.png')).convert('RGBA'))[..., 3] for k in range(meta['pages'])]
    bad = 0
    for an, a in sorted(meta['anims'].items(), key=lambda q: (q[1]['page'], q[1]['row'])):
        for i in range(a['frames']):
            row, col = a['row'] + i // a['cols'], i % a['cols']
            al = pages[a['page']][row * ch:(row + 1) * ch, col * cw:(col + 1) * cw] > 10
            ys, xs = np.nonzero(al)
            edges = [n for n, e in (('sol', al[:, 0]), ('sağ', al[:, -1]), ('üst', al[0]), ('alt', al[-1])) if e.any()]
            bb = ((xs.min() - ox) / tx, (ys.min() - oy) / tx, (xs.max() - ox) / tx, (ys.max() - oy) / tx) if len(xs) else None
            flag = ' KIRPIK ' + ','.join(edges) if edges else ''
            bad += bool(edges)
            print('%-7s %d  x %6.1f..%6.1f  y %6.1f..%5.1f%s' % (an, i, bb[0], bb[2], bb[1], bb[3], flag))
    print('kırpık kare:', bad)


if __name__ == '__main__':
    main()
