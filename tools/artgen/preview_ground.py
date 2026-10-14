"""Zemin önizlemesi: ground.gdshader'ın yaptığını Python'da taklit eder (anahtar renk → dünya
koordinatlı toprak, gölge/ışık bantları, derinlikle kararma)."""
import sys
import numpy as np
from PIL import Image

import soil
from raster import to_img

TS = soil.TS


def compose(grid, soil_rgb, atlas, meta, bg=None, seed=3):
    rng = np.random.default_rng(seed)
    gh, gw = len(grid), len(grid[0])
    W, H = gw * TS, gh * TS
    out = np.zeros((H, W, 3)) if bg is None else bg[:H, :W, :3].copy()
    cell = lambda x, y: grid[y][x] if 0 <= x < gw and 0 <= y < gh else 1
    # derinlik: havaya uzaklık (karo)
    dist = np.full((gh, gw), 99)
    frontier = [(x, y) for y in range(gh) for x in range(gw) if cell(x, y) != 1]
    for x, y in frontier:
        dist[y, x] = 0
    k = 0
    while frontier and k < 12:
        nf = []
        for x, y in frontier:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < gw and 0 <= ny < gh and dist[ny, nx] > dist[y, x] + 1:
                    dist[ny, nx] = dist[y, x] + 1
                    nf.append((nx, ny))
        frontier = nf
        k += 1
    dn = np.clip((dist - 1) / 5.0, 0, 1)
    # tile merkezlerinden piksele yumuşak (bilinear) yayılım
    ys = (np.arange(H) + 0.5) / TS - 0.5
    xs = (np.arange(W) + 0.5) / TS - 0.5
    y0 = np.clip(np.floor(ys).astype(int), 0, gh - 1); x0 = np.clip(np.floor(xs).astype(int), 0, gw - 1)
    y1 = np.clip(y0 + 1, 0, gh - 1); x1 = np.clip(x0 + 1, 0, gw - 1)
    fy = np.clip(ys - np.floor(ys), 0, 1)[:, None]; fx = np.clip(xs - np.floor(xs), 0, 1)[None, :]
    depth = (dn[y0][:, x0] * (1 - fx) + dn[y0][:, x1] * fx) * (1 - fy) + (dn[y1][:, x0] * (1 - fx) + dn[y1][:, x1] * fx) * fy
    deep_col = np.array([0.04, 0.03, 0.06])
    S = soil_rgb.shape[0]
    for y in range(gh):
        for x in range(gw):
            c = cell(x, y)
            if c == 1:
                m = (1 if cell(x, y - 1) != 1 else 0) | (2 if cell(x + 1, y) != 1 else 0) | (4 if cell(x, y + 1) != 1 else 0) | (8 if cell(x - 1, y) != 1 else 0)
                v = (x + y) % 3
                tile = atlas[v * TS:(v + 1) * TS, m * TS:(m + 1) * TS]
            elif c == 2:
                kind = 1 if (cell(x - 1, y) == 2 and cell(x + 1, y) == 2) else (0 if cell(x - 1, y) != 2 else 2)
                r = meta['platform_row']
                tile = atlas[r * TS:(r + 1) * TS, kind * TS:(kind + 1) * TS]
            else:
                tile = None
                if cell(x, y + 1) == 1 and rng.random() < 0.75:
                    r = meta['overlay_row']; k2 = rng.integers(0, 8)
                    tile = atlas[r * TS:(r + 1) * TS, k2 * TS:(k2 + 1) * TS]
                elif y > 0 and cell(x, y - 1) == 1 and rng.random() < 0.5:
                    r = meta['overlay_row']; k2 = 8 + rng.integers(0, 3)
                    tile = atlas[r * TS:(r + 1) * TS, k2 * TS:(k2 + 1) * TS]
            if tile is None:
                continue
            px, py = x * TS, y * TS
            rgb = tile[..., :3].copy(); a = tile[..., 3] > 0
            ws = soil_rgb[(np.arange(py, py + TS) % S)[:, None], (np.arange(px, px + TS) % S)[None, :]]
            for key, mul in ((soil.KEY_SOIL, 1.0), (soil.KEY_SHADE, 0.62), (soil.KEY_LIT, 1.18)):
                km = a & (np.abs(rgb - key).sum(-1) < 0.05)
                if km.any():
                    sv = np.clip(ws * mul, 0, 1)
                    d = depth[py:py + TS, px:px + TS][..., None]
                    sv = sv * (1 - np.clip(d, 0, 1) * 0.85) + deep_col * np.clip(d, 0, 1) * 0.85
                    rgb[km] = sv[km]
            region = out[py:py + TS, px:px + TS]
            region[a] = rgb[a]
    return out


def demo_grid():
    gw, gh = 30, 13
    g = [[0] * gw for _ in range(gh)]
    heights = [8, 8, 8, 8, 8, 8, 7, 7, 7, 6, 6, 6, 6, 6, 7, 7, 8, 9, 9, 9, 9, 8, 8, 8, 7, 7, 7, 7, 8, 8]
    for x in range(gw):
        for y in range(heights[x], gh):
            g[y][x] = 1
    for x in range(3, 9):
        g[3][x] = 1
    for x in range(4, 8):
        g[4][x] = 1
    for x in range(20, 24):
        g[5][x] = 2
    return g


if __name__ == '__main__':
    tex, tex_n = soil.soil_texture()
    A, N, meta = soil.build_ground_atlas()
    g = demo_grid()
    bg = np.zeros((len(g) * TS, len(g[0]) * TS, 3)); bg[...] = [0.12, 0.17, 0.24]
    img = compose(g, tex, A, meta, bg)
    to_img(img).resize((img.shape[1] * 2, img.shape[0] * 2), Image.NEAREST).save(sys.argv[1])
    t2 = np.tile(tex, (2, 2, 1))
    to_img(t2).resize((t2.shape[1] * 2, t2.shape[0] * 2), Image.NEAREST).save(sys.argv[2])
    print('ok')
