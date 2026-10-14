"""Piksel sanat yardımcıları: dikişsiz (periyodik) gürültü, palet nicemleme, sıralı titreşim,
dikişsiz yerleştirme, yükseklikten normal map.
"""
import numpy as np

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def hexrgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255.0


def pal(*hexes):
    return np.array([hexrgb(h) for h in hexes])


def vnoise(w, h, cell_x, cell_y, rng, wrap_x=True, wrap_y=True):
    """Değer gürültüsü; w/cell ve h/cell tam sayıysa kenarlarda dikişsizdir."""
    gw, gh = max(1, w // cell_x), max(1, h // cell_y)
    g = rng.random((gh + 1, gw + 1))
    if wrap_x:
        g[:, gw] = g[:, 0]
    if wrap_y:
        g[gh, :] = g[0, :]
    ys = np.arange(h) / cell_y
    xs = np.arange(w) / cell_x
    y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
    fy = ys - y0; fx = xs - x0
    fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
    y0 = np.clip(y0, 0, gh - 1); x0 = np.clip(x0, 0, gw - 1)
    y1, x1 = y0 + 1, x0 + 1
    a = g[y0][:, x0]; b = g[y0][:, x1]; c = g[y1][:, x0]; d = g[y1][:, x1]
    top = a * (1 - fx) + b * fx
    bot = c * (1 - fx) + d * fx
    return top * (1 - fy[:, None]) + bot * fy[:, None]


def fbm(w, h, cells, weights, rng, aspect=1.0, wrap_y=True):
    out = np.zeros((h, w))
    tot = 0.0
    for c, wt in zip(cells, weights):
        cy = max(1, int(round(c * aspect)))
        out += vnoise(w, h, c, cy, rng, True, wrap_y) * wt
        tot += wt
    return out / tot


def ridged(w, h, cells, weights, rng, aspect=1.0):
    out = np.zeros((h, w))
    tot = 0.0
    for c, wt in zip(cells, weights):
        cy = max(1, int(round(c * aspect)))
        n = vnoise(w, h, c, cy, rng, True, False)
        out += (1 - np.abs(n * 2 - 1)) * wt
        tot += wt
    return out / tot


def profile(w, cells, weights, rng):
    """1B periyodik profil (dağ sırtı, orman çizgisi)."""
    return fbm(w, 1, cells, weights, rng, aspect=1.0, wrap_y=False)[0]


def quantize(v, thresholds, dither=0.0, ox=0, oy=0):
    """Sürekli değeri seviye indisine çevir; isteğe bağlı sıralı titreşimle bant sınırlarını kırar."""
    h, w = v.shape
    if dither > 0:
        b = np.tile(BAYER4, (h // 4 + 2, w // 4 + 2))[oy:oy + h, ox:ox + w] - 0.5
        v = v + b * dither
    return np.digitize(v, thresholds)


def shift(a, dy, dx, wrap=True, fill=0):
    if wrap:
        return np.roll(np.roll(a, dy, 0), dx, 1)
    out = np.full_like(a, fill)
    h, w = a.shape[:2]
    ys = slice(max(dy, 0), h + min(dy, 0)); yd = slice(max(-dy, 0), h + min(-dy, 0))
    xs = slice(max(dx, 0), w + min(dx, 0)); xd = slice(max(-dx, 0), w + min(-dx, 0))
    out[ys, xs] = a[yd, xd]
    return out


def normals_from_height(hgt, strength=1.0, wrap=True):
    gx = (shift(hgt, 0, -1, wrap) - shift(hgt, 0, 1, wrap)) * 0.5 * strength
    gy = (shift(hgt, -1, 0, wrap) - shift(hgt, 1, 0, wrap)) * 0.5 * strength
    n = np.stack([-gx, -gy, np.ones_like(hgt)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n


def normal_rgba(n, alpha=None):
    out = np.zeros(n.shape[:2] + (4,))
    out[..., 0] = n[..., 0] * 0.5 + 0.5
    out[..., 1] = -n[..., 1] * 0.5 + 0.5
    out[..., 2] = n[..., 2] * 0.5 + 0.5
    out[..., 3] = 1.0 if alpha is None else alpha
    return out


def outline_mask(alpha):
    a = alpha > 0
    nb = np.zeros_like(a)
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        nb |= shift(a, dy, dx, wrap=False, fill=False)
    return nb & ~a


def blend_over(dst, src):
    """dst: (h,w,4) | src: (h,w,4); düz alfa üst üste bindirme."""
    a = src[..., 3:4]
    out = dst.copy()
    out[..., :3] = dst[..., :3] * (1 - a) + src[..., :3] * a
    out[..., 3:4] = np.maximum(dst[..., 3:4], a)
    return out


def jitter_points(w, h, spacing, rng, jitter=0.8):
    pts = []
    for y in np.arange(spacing / 2, h, spacing):
        for x in np.arange(spacing / 2, w, spacing):
            pts.append((x + rng.uniform(-jitter, jitter) * spacing / 2, y + rng.uniform(-jitter, jitter) * spacing / 2))
    return pts
