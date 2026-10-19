"""v29 önizleme (geliştirme): bir çeşitlemenin satırlarını kontak sayfası olarak çizer (dışa aktarmadan, süreç havuzu).

python ucan_onizleme.py <çıktı.png> <modül> <çeşitleme> [satır ...] [--olcek=0.5] [--glow]
  ör. python ucan_onizleme.py x.png cor_ink kaf_kartali attack idle
Her satırın solunda ad, kare sayısı, fps; kare üstünde ts (varsa). Kırmızı çerçeve: kare hücre kenarına taşıyor (kırpılma).
"""
import importlib
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from PIL import Image, ImageDraw


def _job(a):
    mod, var, an, i = a
    m = importlib.import_module(mod)
    rgba, nm, em, info = m.render_frame(an, i, var)
    return (an, i), (rgba, em)


def main():
    args = sys.argv[1:]
    opts = [a for a in args if a.startswith('--')]
    args = [a for a in args if not a.startswith('--')]
    out, mod, var = args[:3]
    only = args[3:]
    sc = 0.5
    glow = '--glow' in opts
    for o in opts:
        if o.startswith('--olcek='):
            sc = float(o.split('=')[1])
    m = importlib.import_module(mod)
    rows = m.anims_for(var)
    names = [n for n in rows if not only or n in only]
    jobs = [(mod, var, n, i) for n in names for i in range(rows[n]['frames'])]
    with ProcessPoolExecutor(max_workers=11) as ex:
        res = dict(ex.map(_job, jobs))
    cw, ch = m.CELL
    W, H = int(cw * sc), int(ch * sc)
    cols = max(rows[n]['frames'] for n in names)
    lab = 110
    img = Image.new('RGB', (lab + cols * W, len(names) * H), (36, 44, 42))
    dr = ImageDraw.Draw(img)
    yy = np.linspace(0, 1, ch)[:, None, None]
    bg = (np.array([0.42, 0.55, 0.48]) * (1 - yy) + np.array([0.20, 0.28, 0.26]) * yy) * np.ones((ch, cw, 3))
    for r, n in enumerate(names):
        row = rows[n]
        for i in range(row['frames']):
            rgba, em = res[(n, i)]
            a = rgba[..., 3:4]
            o = bg * (1 - a) + rgba[..., :3] * a
            if glow:
                o = o + em[..., :3] * 1.6 * 0.6
            im = Image.fromarray((np.clip(o, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
            d2 = ImageDraw.Draw(im)
            d2.line([(0, int(m.FEET[1] * sc)), (W, int(m.FEET[1] * sc))], fill=(90, 110, 100))
            edge = max(a[:2].max(), a[-2:].max(), a[:, :2].max(), a[:, -2:].max())
            if edge > 0.05:
                d2.rectangle([0, 0, W - 1, H - 1], outline=(255, 40, 40), width=2)
            img.paste(im, (lab + i * W, r * H))
            if row.get('ts'):
                dr.text((lab + i * W + 3, r * H + 3), '%.2f' % row['ts'][i], fill=(255, 240, 160))
        dr.text((4, r * H + 4), '%s\n%df %dfps%s' % (n, row['frames'], row['fps'], ' L' if row['loop'] else ''), fill=(255, 255, 255))
        if row.get('mk'):
            dr.text((4, r * H + 34), 'mk ' + ','.join('%.2f' % v for v in row['mk']), fill=(255, 220, 120))
    img.save(out)
    print(out, img.size)


if __name__ == '__main__':
    main()
