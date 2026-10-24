"""v43 önce / sonra kare sayfası (sprite karesi düzeyinde): her hareket için üst satır v39 (bengu_ink), alt satır v43.
python onceson43.py <çıktı.png>   (iki ayrı süreçte çizer: bengu43_ink bengu_ink'i yerinde değiştirir)"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROWS = [('idle', [0, 3, 6]), ('run', [0, 2, 4, 6, 8]), ('jump', [0, 2]), ('fall', [1, 3]), ('roll', [1, 3, 5]),
        ('hurt', [0]), ('hero_land', [0, 2]), ('atk_horiz', [2, 4, 6]), ('atk_overhead_2h', [3, 5]),
        ('tirman', [0, 2, 4]), ('olum', [1, 3, 5])]


def render(mod, out):
    import importlib
    m = importlib.import_module(mod)
    tiles = {}
    for an, fr in ROWS:
        if an not in m.ANIMS:
            continue
        n, fn, loop, arm = m.ANIMS[an]
        m.ANIMS[an] = (n, fn, loop, True)     # ön kol çizimde (karşılaştırma)
        for i in fr:
            tiles['%s:%d' % (an, i)] = m.render_frame(an, i)[0][40:310, 60:330]
    np.savez_compressed(out, **{k.replace(':', '__'): v.astype(np.float16) for k, v in tiles.items()})


def main():
    if sys.argv[1] == '--ciz':
        render(sys.argv[2], sys.argv[3])
        return
    out = sys.argv[1]
    tmp = out + '.%s.npz'
    for mod in ('bengu_ink', 'bengu43_ink'):
        subprocess.check_call([sys.executable, __file__, '--ciz', mod, tmp % mod])
    old = dict(np.load(tmp % 'bengu_ink'))
    new = dict(np.load(tmp % 'bengu43_ink'))
    tw, th = 270, 270
    cols = max(len(fr) for _, fr in ROWS)
    W, H = 160 + cols * tw, len(ROWS) * th * 2
    bg = Image.new('RGB', (W, H), (40, 50, 50))
    d = ImageDraw.Draw(bg)
    f = ImageFont.truetype(os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'ui', 'fonts', 'AlegreyaSans-Medium.ttf'), 22)
    for r, (an, fr) in enumerate(ROWS):
        for k, (src, tag) in enumerate(((old, 'önce v39'), (new, 'sonra v43'))):
            y = (r * 2 + k) * th
            col = (52, 66, 62) if k == 0 else (30, 40, 44)
            d.rectangle([0, y, W, y + th], fill=col)
            d.text((10, y + 10), '%s\n%s' % (an, tag), font=f, fill=(225, 225, 215))
            for c, i in enumerate(fr):
                key = '%s__%d' % (an, i)
                if key not in src:
                    continue
                t = src[key].astype(np.float32)
                im = Image.fromarray((np.clip(t, 0, 1) * 255).astype(np.uint8), 'RGBA')
                bg.paste(im, (160 + c * tw, y), im)
    bg.save(out, quality=90)
    for mod in ('bengu_ink', 'bengu43_ink'):
        os.remove(tmp % mod)


if __name__ == '__main__':
    main()
