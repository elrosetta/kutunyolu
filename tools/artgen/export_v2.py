"""Stil v2 dışa aktarımı: v1 dosyalarına DOKUNMAZ, yalnızca *_v2 adlı varlıkları yazar.

Kullanım:  python export_v2.py               (hepsi)
           python export_v2.py --bengu       assets/sprites/bengu_v2.{png,json} (+_n, _e) ve bengu_kol_v2.{png,json}
           python export_v2.py --otuken      assets/tiles/otuken_v2* ve assets/bg/otuken_v2_*.png
Adlandırma: v1 kimliğinin sonuna "_v2" (bengu -> bengu_v2, bengu_kol -> bengu_kol_v2, otuken -> otuken_v2,
otuken_3_mid -> otuken_3_mid_v2). Oyunda: -- --stil=v2 (Data.stil_id): _v2 sürümü varsa o, yoksa v1 kullanılır.
"""
import json
import os
import sys
import numpy as np

import raster
from export_assets import A, export_sheet, save


def export_bengu():
    import bengu_v2 as b
    export_sheet('bengu_v2', b.ANIMS, lambda an, i: b.render_frame(an, i), b.CELL, b.FEET, b.TEX)
    parts = b.render_arm_parts()
    cw, ch = int(b.ARM_CELL[0] * raster.SS), int(b.ARM_CELL[1] * raster.SS)
    alb = np.zeros((ch, cw * len(parts), 4))
    for i, pc in enumerate(parts):
        alb[:, i * cw:(i + 1) * cw] = pc.shade()
    save(alb, os.path.join(A, 'sprites', 'bengu_kol_v2.png'))
    json.dump({'cell': list(b.ARM_CELL), 'pivot': list(b.ARM_PIVOT), 'fist_pivot': [b.ARM_PIVOT[0], b.ARM_PIVOT[1] + 3],
               'texel': b.TEX, 'upper_len': b.L_UP, 'fore_len': b.L_FORE, 'parts': ['upper', 'fore', 'fist', 'upper_b', 'fore_b', 'fist_b']},
              open(os.path.join(A, 'sprites', 'bengu_kol_v2.json'), 'w', encoding='utf-8'), indent=1)
    print('sprite bengu_kol_v2', alb.shape)


def export_otuken():
    import otuken_v2
    otuken_v2.export(A)


def main():
    args = sys.argv[1:]
    every = not any(a.startswith('--') for a in args)
    if every or '--bengu' in args:
        export_bengu()
    if every or '--otuken' in args:
        export_otuken()


if __name__ == '__main__':
    main()
