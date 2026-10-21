"""v38: paralaks katmanlarının saydam üst / alt şeritleri (data/bg_kirp.json).

Paralaks katmanları (assets/bg/*_v2_*.png, 1080 px yükseklik) ekranı boydan boya kaplayan dörtgenlerdir; dağ, sis, pus
katmanlarının üst ve alt kısımları tamamen saydamdır ama GPU yine her pikseli örnekler ve karıştırır (tümleşik GPU'da
piksel doldurma darboğazı). Bu betik her katmanın alfa > 1 olan ilk ve son satırını (2 px pay ile) yazar; ParallaxBG
yalnızca bu dikey bölgeyi çizer (Sprite2D bölgesi + ofset: görüntü bayt bayt aynı, yatay döşeme değişmez).
Kullanım (tools/artgen içinde): python bg_kirp.py   (katman dokuları yeniden üretilince yeniden çalıştırın)
"""
import json
import os

import numpy as np
from PIL import Image

KOK = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main():
    out = {}
    bg = os.path.join(KOK, "assets", "bg")
    for f in sorted(os.listdir(bg)):
        if not f.endswith(".png") or "_v2_" not in f or "_fg_" in f:
            continue
        im = Image.open(os.path.join(bg, f))
        if im.mode != "RGBA":
            continue
        a = np.asarray(im)[:, :, 3]
        rows = np.where(a.max(axis=1) > 1)[0]
        h = a.shape[0]
        if len(rows) == 0:
            continue
        y0 = max(0, int(rows[0]) - 2)
        y1 = min(h, int(rows[-1]) + 3)
        if y1 - y0 >= h * 0.97:
            continue  # kırpılacak bir şey yok
        out[f[:-4]] = [y0, y1, h]
    with open(os.path.join(KOK, "data", "bg_kirp.json"), "w", encoding="utf-8", newline="\n") as fp:
        json.dump(out, fp, indent=1, sort_keys=True)
        fp.write("\n")
    print("bg_kirp.json: %d katman" % len(out))


if __name__ == "__main__":
    main()
