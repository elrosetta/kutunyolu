"""Hızlı kare doluluk kutusu (ss=1): python bbox_boss_ink.py <modül> anim:kare ..."""
import importlib
import sys

import numpy as np

m = importlib.import_module(sys.argv[1])
for spec in sys.argv[2:]:
    an, i = spec.split(':')
    rgba, nm, em, info = m.render_frame(an, int(i), ss=1)
    al = rgba[..., 3] > 0.04
    ys, xs = np.nonzero(al)
    ox, oy = m.FEET
    edges = [n for n, e in (('sol', al[:, 0]), ('sag', al[:, -1]), ('ust', al[0]), ('alt', al[-1])) if e.any()]
    print(spec, 'x %.0f..%.0f y %.0f..%.0f' % ((xs.min() - ox) / 4, (xs.max() - ox) / 4, (ys.min() - oy) / 4, (ys.max() - oy) / 4), 'KIRPIK ' + ','.join(edges) if edges else '')
