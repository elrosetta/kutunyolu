"""v43 Bengü konsept sayfaları: üç palet yönü (durgun, koşu, saldırı, oyun boyu silüet, palet şeridi).
python konsept43.py <çıktı_klasörü>"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import bengu43_ink as k

FONT = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'ui', 'fonts')
BASLIK = {'tan': 'A  "Tan Kızılı"', 'safak': 'B  "Şafak Çivit"', 'kul': 'C  "Kül Keçe"'}
NOT = {'tan': 'kök boya kızılı kaftan · safran sırma/kuşak · kemik beyazı kurt postu',
       'safak': 'gece çividi kaftan · kızıl astar/kuşak · safran güneş nakışı',
       'kul': 'boyasız keçe kaftan · kara-kızıl tamga bordürü · boz kurt postu'}


def frame(an, i, arm=True):
    n, fn, loop, a = k.b.ANIMS[an]
    k.b.ANIMS[an] = (n, fn, loop, arm)
    try:
        return k.render_frame(an, i)[0]
    finally:
        k.b.ANIMS[an] = (n, fn, loop, a)


def comp(bg, t, x, y, z=1):
    im = Image.fromarray((np.clip(t, 0, 1) * 255).astype(np.uint8), 'RGBA')
    if z != 1:
        im = im.resize((im.width * z, im.height * z), Image.LANCZOS)
    bg.alpha_composite(im, (x, y))


def sheet(ad, out):
    k.palet(ad)
    k.KONSEPT = True
    W, H = 2200, 1000
    bg = Image.new('RGBA', (W, H), (34, 40, 46, 255))
    d = ImageDraw.Draw(bg)
    # soğuk dünya zemini: üst sis yeşili, alt mağara laciverdi
    for yy in range(H):
        t = yy / H
        c = (int(70 * (1 - t) + 22 * t), int(92 * (1 - t) + 26 * t), int(84 * (1 - t) + 38 * t))
        d.line([(0, yy), (W, yy)], fill=c + (255,))
    f1 = ImageFont.truetype(os.path.join(FONT, 'Cinzel-VF.ttf'), 46)
    f2 = ImageFont.truetype(os.path.join(FONT, 'AlegreyaSans-Medium.ttf'), 26)
    d.text((40, 24), 'Bengü — Tan Bekçisi  ' + BASLIK[ad], font=f1, fill=(240, 228, 204))
    d.text((40, 84), NOT[ad], font=f2, fill=(200, 205, 210))
    comp(bg, frame('idle', 0), -120, 60, 3)
    comp(bg, frame('run', 3), 640, 300, 2)
    comp(bg, frame('atk_horiz', 6), 1180, 300, 2)
    # oyun boyu (1080p'de 1 doku pikseli = 1 ekran pikseli) + silüet
    t = frame('idle', 0)
    comp(bg, t, 1840, 560, 1)
    sil = t.copy()
    sil[..., :3] = 0.05
    comp(bg, sil, 1960, 560, 1)
    run = frame('run', 6)
    sil2 = run.copy()
    sil2[..., :3] = 0.05
    comp(bg, sil2, 1600, 560, 1)
    d.text((1880, 540), 'oyun boyu · silüet', font=f2, fill=(200, 205, 210))
    # palet şeridi
    pal = k.PALETLER[ad]
    x = 1760
    for key in ('kaftan', 'astar', 'sirma', 'pant', 'boot', 'kusak', 'fur', 'plak'):
        for j, hx in enumerate(pal[key][:3]):
            c = tuple(int(hx[i:i + 2], 16) for i in (1, 3, 5))
            d.rectangle([x, 120 + j * 34, x + 46, 150 + j * 34], fill=c + (255,))
        d.text((x, 228), key, font=ImageFont.truetype(os.path.join(FONT, 'AlegreyaSans-Medium.ttf'), 18), fill=(210, 210, 210))
        x += 54
    k.KONSEPT = False
    bg.convert('RGB').save(out, quality=92)


if __name__ == '__main__':
    od = sys.argv[1]
    os.makedirs(od, exist_ok=True)
    for ad in (sys.argv[2:] or ('tan', 'safak', 'kul')):
        sheet(ad, os.path.join(od, 'konsept_%s.jpg' % ad))
        print('konsept', ad)
