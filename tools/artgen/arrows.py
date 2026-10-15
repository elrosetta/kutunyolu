"""Ok sprite'ları: 32 yönde önceden çizilmiş, kenar yumuşatması olmayan piksel oklar.

Döndürülmüş piksel sanatı bulanık / tırtıklı görünür; bu yüzden her yön ayrı ayrı rasterlanır (3x3 alt örnek,
ikili kapsama). Satırlar türlerdir (VARIANTS), sütunlar açılardır (0 = sağa, saat yönünde 11,25° adımlar).
Çıktı: assets/fx/arrows.png (+ .json). Godot: Projectile.gd hframes = 32, vframes = len(VARIANTS).

Çalıştır:  python tools/artgen/arrows.py
"""
import json
import math
import os
from PIL import Image

CELL = 24
DIRS = 32


def hx(s):
    s = s.lstrip('#')
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


# tür: (sap, sap gölgesi, uç, uç parlak, tüy 1, tüy 2)
VARIANTS = {
    'normal': ('#c99a5e', '#7a5531', '#dfe6f0', '#ffffff', '#d8402f', '#f2ece0'),
    'altin': ('#f0c873', '#9a6a2a', '#ffe27a', '#fffbe0', '#ffd24a', '#fff3c4'),
    'od': ('#8a4a26', '#4a2414', '#ff8a2a', '#ffe08a', '#c8281c', '#ff7a2a'),
    'sel': ('#b9a789', '#6d5c46', '#bfe8ff', '#ffffff', '#4aa8ff', '#d8f2ff'),
    'kizil': ('#3a2a2a', '#1c1414', '#c9ccd6', '#ffffff', '#c0182a', '#e8c25a'),
    'dusman': ('#5a4a5e', '#2c2230', '#c86aff', '#f2d6ff', '#7a2a9a', '#3c1450'),
}
ORDER = list(VARIANTS.keys())


def part(x, y):
    """Yerel koordinatta (x ok yönünde, y dik) hangi parça: None / 'shaft' / 'shade' / 'head' / 'hi' / 'f1' / 'f2'."""
    ay = abs(y)
    # uç: x 4.5..9.5 arası üçgen
    if 4.5 <= x <= 9.6:
        w = (9.6 - x) * 0.55
        if ay <= max(0.55, w):
            return 'hi' if (x > 7.6 and ay < 0.6) else 'head'
    # sap
    if -9.0 <= x < 4.5 and ay <= 0.55:
        return 'shaft'
    # tüyler (geriye yatık paralelkenar)
    if -10.5 <= x <= -5.0:
        lo = 0.55
        hi = 0.55 + 2.1
        sk = (x + 10.5) * 0.18  # geriye doğru yatık
        if lo <= ay - sk * 0.0 <= hi and x <= -5.0 - (ay - 0.55) * 0.9:
            return 'f1' if y < 0 else 'f2'
    return None


def render_cell(ang, cols):
    img = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
    px = img.load()
    ca, sa = math.cos(ang), math.sin(ang)
    c0 = CELL / 2.0
    S = 3
    for j in range(CELL):
        for i in range(CELL):
            counts = {}
            for sj in range(S):
                for si in range(S):
                    wx = i + (si + 0.5) / S - c0
                    wy = j + (sj + 0.5) / S - c0
                    # dünya -> yerel (ters döndürme)
                    lx = wx * ca + wy * sa
                    ly = -wx * sa + wy * ca
                    p = part(lx, ly)
                    if p:
                        counts[p] = counts.get(p, 0) + 1
            if not counts:
                continue
            tot = sum(counts.values())
            if tot < 4:  # ikili kapsama eşiği (9 alt örnekte)
                continue
            p = max(counts, key=lambda k: (counts[k] + (2 if k in ('hi', 'head') else 0)))
            shaft, shade, head, hi, f1, f2 = cols
            col = {'shaft': shaft, 'head': head, 'hi': hi, 'f1': f1, 'f2': f2}[p]
            px[i, j] = hx(col)
    # sapın alt kenarına gölge: dolu pikselin hemen altı boşsa ve sap rengiyse koyulaştır
    out = img.copy()
    op = out.load()
    for j in range(CELL - 1):
        for i in range(CELL):
            if px[i, j][3] and px[i, j][:3] == hx(cols[0])[:3] and not px[i, j + 1][3] and abs(math.sin(ang)) < 0.9:
                op[i, j] = hx(cols[1])
    return out


def build(root):
    W = CELL * DIRS
    H = CELL * len(ORDER)
    sheet = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for r, name in enumerate(ORDER):
        cols = VARIANTS[name]
        for d in range(DIRS):
            ang = d * (2 * math.pi / DIRS)
            sheet.alpha_composite(render_cell(ang, cols), (d * CELL, r * CELL))
    out = os.path.join(root, 'assets', 'fx')
    sheet.save(os.path.join(out, 'arrows.png'))
    with open(os.path.join(out, 'arrows.json'), 'w', encoding='utf-8') as f:
        json.dump({'cell': CELL, 'dirs': DIRS, 'variants': ORDER}, f, ensure_ascii=False, indent=1)
    return sheet


if __name__ == '__main__':
    import sys
    root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
    sh = build(root)
    if len(sys.argv) > 1:
        bg = Image.new('RGBA', sh.size, (24, 20, 34, 255))
        bg.alpha_composite(sh)
        bg.resize((sh.width * 3, sh.height * 3), Image.NEAREST).save(sys.argv[1])
    print('arrows.png', sh.size)
