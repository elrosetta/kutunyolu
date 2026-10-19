"""v29 yer yaratıkları poz önizlemesi (yalnızca geliştirme): satırların kareleri yan yana, yer çizgisi ve evre etiketiyle.

Kullanım: python yer_onizleme.py <sprite> <çıktı.png> [anim ...] [--olcek=0.5] [--sutun=10] [--ss=2]
  anim verilmezse tüm satırlar. Her karenin altında: ad, kare no, evre ve ts. Kırmızı çizgi = yer (ayak çizgisi).
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from PIL import Image, ImageDraw

import export_yer as ey


def _job(a):
    mod, var, an, i, ss = a
    import importlib
    m = importlib.import_module(mod)
    try:
        out = m.render_frame(an, i, var, ss=ss) if var is not None else m.render_frame(an, i, ss=ss)
    except TypeError:
        out = m.render_frame(an, i, var) if var is not None else m.render_frame(an, i)
    return (an, i), out[0]


def main():
    args = sys.argv[1:]
    sc = 0.5
    cols = 10
    ss = 2
    pos = []
    for a in args:
        if a.startswith('--olcek='):
            sc = float(a.split('=')[1])
        elif a.startswith('--sutun='):
            cols = int(a.split('=')[1])
        elif a.startswith('--ss='):
            ss = int(a.split('=')[1])
        else:
            pos.append(a)
    name, out = pos[0], pos[1]
    mod, var = ey.SHEETS[name]
    import importlib
    m = importlib.import_module(mod)
    anims = pos[2:] or list(m.SEQS)
    jobs = [(mod, var, an, i, ss) for an in anims for i in range(len(m.SEQS[an]))]
    with ProcessPoolExecutor(max_workers=int(os.environ.get('KY_IS', '0') or '0') or max(1, (os.cpu_count() or 2) - 2)) as pool:
        res = dict(pool.map(_job, jobs, chunksize=1))
    cw, ch = int(m.CELL[0] * sc), int(m.CELL[1] * sc)
    lab = 26
    rows = []
    for an in anims:
        s = m.SEQS[an]
        n = len(s)
        for r0 in range(0, n, cols):
            rows.append((an, list(range(r0, min(n, r0 + cols)))))
    W = cw * cols
    H = (ch + lab) * len(rows)
    img = Image.new('RGB', (W, H), (236, 229, 212))
    d = ImageDraw.Draw(img)
    segname = {}
    for an in anims:
        s = m.SEQS[an]
        k = 0
        for nm, c in s.seg:
            for j in range(c):
                segname[(an, k)] = nm
                k += 1
    for r, (an, idx) in enumerate(rows):
        y0 = r * (ch + lab)
        fy = y0 + int(m.FEET[1] * sc)
        for c, i in enumerate(idx):
            x0 = c * cw
            rgba = np.clip(np.asarray(res[(an, i)], np.float32) * 255, 0, 255).astype(np.uint8)
            im = Image.fromarray(rgba, 'RGBA').resize((cw, ch), Image.LANCZOS)
            d.line([(x0, fy), (x0 + cw, fy)], fill=(200, 80, 70), width=1)
            d.line([(x0 + int(m.FEET[0] * sc), fy - 4), (x0 + int(m.FEET[0] * sc), fy + 4)], fill=(200, 80, 70), width=1)
            img.paste(im, (x0, y0), im)
            ts = m.SEQS[an].frames[i][1]
            d.text((x0 + 3, y0 + ch + 2), '%s %d %s %.2f' % (an, i, segname[(an, i)], ts), fill=(40, 30, 30))
            d.line([(x0, y0), (x0, y0 + ch + lab)], fill=(200, 190, 170))
    img.save(out, quality=88)
    print(out, img.size)


if __name__ == '__main__':
    main()
