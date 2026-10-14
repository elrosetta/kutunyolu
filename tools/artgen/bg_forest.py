"""Ötüken Ormanı paralaks katmanları (yatayda dikişsiz döşenir).

Gün batımı paleti: lacivert → şeftali gökyüzü, mor dağlar, turkuaz uzak orman,
yeşil-turuncu-kızıl güz ağaçları, koyu ön plan gövdeleri. Siluetler kenar yumuşatmasız
(piksel sanat) çizilir; üst kenarlara güneş ışığı (rim) eklenir.
"""
import math
import random
import numpy as np
from PIL import Image, ImageDraw


def hexc(h, a=255):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def rim(img, color, side='up', width=1):
    a = np.array(img)
    al = a[..., 3] > 0
    edge = np.zeros_like(al)
    for k in range(1, width + 1):
        if side == 'up':
            edge |= al & ~np.roll(al, k, 0)
        elif side == 'left':
            edge |= al & ~np.roll(al, k, 1)
    a[edge, :3] = color[:3]
    return Image.fromarray(a)


def tiled(W, H, draw_fn):
    """Şekilleri x-W, x, x+W konumlarında çizip ortadaki W genişliğini al: dikişsiz döşeme."""
    big = Image.new('RGBA', (W * 3, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    for off in (0, W, 2 * W):
        draw_fn(d, off)
    return big.crop((W, 0, 2 * W, H))


def sky(W=640, H=360):
    ys = np.arange(H)[:, None]
    stops = [(0, '#152a5a'), (90, '#2e4f8f'), (170, '#7a6fb0'), (215, '#e88f8a'), (250, '#f6b77a'), (290, '#ffd99a'), (360, '#ffe8b8')]
    col = np.zeros((H, 3))
    for (y0, c0), (y1, c1) in zip(stops, stops[1:]):
        m = (np.arange(H) >= y0) & (np.arange(H) <= y1)
        t = (np.arange(H)[m] - y0) / max(1, y1 - y0)
        a, b = np.array(hexc(c0)[:3]), np.array(hexc(c1)[:3])
        col[m] = a + (b - a) * t[:, None]
    # hafif bantlama (piksel sanat hissi)
    q = (np.floor(col / 3) * 3)
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = q[:, None, :].astype(np.uint8)
    img[..., 3] = 255
    # güneş + hale
    cx, cy = 420, 236
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt((xx - cx) ** 2 + ((yy - cy) * 1.1) ** 2)
    for r, c in ((95, '#ffd29a'), (62, '#ffe2ac'), (40, '#fff0c6'), (24, '#fff8e2')):
        m = d < r
        img[m, :3] = (img[m, :3] * 0.45 + np.array(hexc(c)[:3]) * 0.55).astype(np.uint8)
    # bulut şeritleri
    rng = random.Random(5)
    im = Image.fromarray(img)
    dr = ImageDraw.Draw(im)
    for k in range(9):
        y = rng.randint(60, 200); x = rng.randint(-80, W); w = rng.randint(90, 220); h = rng.randint(4, 9)
        c = '#f3a29a' if y > 140 else '#8a7cc4'
        dr.rectangle((x, y, x + w, y + h), fill=hexc(c))
        dr.rectangle((x + 12, y - h // 2, x + w - 24, y), fill=hexc(c))
        dr.rectangle((x + 6, y + h, x + w - 10, y + h + 2), fill=hexc('#ffd0a8' if y > 140 else '#b6a6e0'))
    return im


def mountains(W=1280, H=360):
    rng = random.Random(8)
    peaks = [(rng.uniform(0, W), rng.uniform(70, 140), rng.uniform(90, 170)) for _ in range(9)]

    def draw(d, off):
        for x, h, w in peaks:
            top = 250 - h
            d.polygon([(off + x - w, 262), (off + x - w * 0.15, top + 8), (off + x, top), (off + x + w * 0.2, top + 10), (off + x + w, 262)], fill=hexc('#6a63a4'))
            d.polygon([(off + x - w * 0.22, top + 18), (off + x - w * 0.08, top + 6), (off + x, top), (off + x + w * 0.12, top + 8), (off + x + w * 0.26, top + 22), (off + x + w * 0.1, top + 16), (off + x - 0.05 * w, top + 22)], fill=hexc('#efe6ff'))
        d.rectangle((off, 258, off + W, H), fill=hexc('#7d74b4'))
    im = tiled(W, H, draw)
    return rim(im, hexc('#ffc6a6'), 'up', 1)


def forest_far(W=1280, H=360):
    rng = random.Random(9)
    trees = [(rng.uniform(0, W), rng.uniform(16, 34), rng.uniform(232, 262)) for _ in range(70)]

    def draw(d, off):
        d.rectangle((off, 262, off + W, H), fill=hexc('#3c7476'))
        for x, r, y in trees:
            d.ellipse((off + x - r, y - r * 1.3, off + x + r, y + r), fill=hexc('#3c7476'))
            d.polygon([(off + x - r * 0.6, y - r * 0.4), (off + x, y - r * 2.2), (off + x + r * 0.6, y - r * 0.4)], fill=hexc('#3c7476'))
    im = tiled(W, H, draw)
    im = rim(im, hexc('#8cc9a4'), 'up', 1)
    a = np.array(im)
    ys = np.arange(H)[:, None]
    mist = np.clip((ys - 270) / 60, 0, 1)
    a[..., :3] = (a[..., :3] * (1 - mist[..., None] * 0.55) + np.array([214, 232, 220]) * mist[..., None] * 0.55).astype(np.uint8)
    return Image.fromarray(a)


from raster import Canvas, Mat, ramp, to_img

CAN = {
    'g1': Mat(ramp(128, 0.55, 0.58)), 'g2': Mat(ramp(150, 0.50, 0.50)), 'g3': Mat(ramp(100, 0.60, 0.66)),
    'or': Mat(ramp(28, 0.80, 0.88)), 'rd': Mat(ramp(6, 0.70, 0.72)), 'au': Mat(ramp(46, 0.78, 0.92)),
}
TRUNK = Mat(ramp(20, 0.40, 0.40, spread=0.45))
BIRCH = Mat(ramp(40, 0.10, 0.94, spread=0.35))
PINE = Mat(ramp(160, 0.50, 0.42))
MOSS = Mat(ramp(100, 0.62, 0.55))
BLACK = Mat(ramp(250, 0.3, 0.12), flat=True)


def _wrap(W, x):
    return [x - W, x, x + W]


def _canopy(c, x, top, r, mat, rng, light=0.0):
    pts = [(rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(int(14 + r))]
    for k, (u, v) in enumerate(sorted(pts, key=lambda p: p[1])):
        if u * u + v * v > 1.1:
            continue
        rr = rng.uniform(0.32, 0.5) * r
        c.ellipse((x + u * r * 1.05, top + v * r * 0.75), rr, rr * 0.82, mat, z=5 + (1 - v) * 3 + rng.uniform(0, 1), tone=light, flat=0.25)


def _finish(c, mist_col, mist_amt, rim_col='#ffd9a0'):
    rgba = c.shade(light=(-0.75, -0.55, 0.45), rim=(-0.9, -0.3, -0.2), rim_col=rim_col, rim_amt=0.55)
    a = rgba[..., 3:4]
    mc = np.array(hexc(mist_col)[:3]) / 255.0
    rgba[..., :3] = rgba[..., :3] * (1 - mist_amt) + mc * mist_amt
    return Image.fromarray((np.clip(rgba, 0, 1) * 255).astype(np.uint8), 'RGBA')


def forest_mid(W=1280, H=360):
    rng = random.Random(10)
    c = Canvas(W, H)
    x = 10.0
    kinds = ['oak', 'birch', 'pine', 'oak', 'oak', 'birch', 'pine']
    while x < W:
        kind = rng.choice(kinds)
        top = rng.uniform(140, 200)
        for xx in _wrap(W, x):
            if kind == 'pine':
                c.capsule((xx, 312), (xx, top - 10), 3.2, 1.8, TRUNK, z=0)
                for k in range(5):
                    y = top + k * 22
                    w_ = 12 + k * 7
                    pts = [(xx - 2, y - 6), (xx + 2, y - 6)]
                    for j in range(7):
                        t = j / 6
                        pts.append((xx + w_ * (1 - t * 2) * (1 if j % 2 == 0 else 0.82), y + 20 - (j % 2) * 4))
                    c.poly(pts, PINE, z=4 + k * 0.2, bevel=5, height=4)
            elif kind == 'birch':
                marks = lambda lu, lv, px, py: (np.sin(py * 0.9 + px * 0.2) > 0.82) & (np.abs(lv) < 0.7)
                c.capsule((xx, 312), (xx + rng.uniform(-6, 6), top + 10), 3.6, 2.4, BIRCH, z=1, paint=[(marks, BLACK)])
                _canopy(c, xx, top, rng.uniform(22, 30), CAN[rng.choice(['au', 'g3', 'or'])], rng)
            else:
                c.capsule((xx, 312), (xx, top + 12), 5.0, 3.2, TRUNK, z=1)
                c.capsule((xx, top + 30), (xx + 18, top + 6), 2.2, 1.2, TRUNK, z=1)
                c.capsule((xx, top + 36), (xx - 16, top + 14), 2.2, 1.2, TRUNK, z=1)
                _canopy(c, xx, top, rng.uniform(28, 40), CAN[rng.choice(['g1', 'g2', 'g1', 'or', 'rd', 'au'])], rng)
        x += rng.uniform(52, 96)
    # zemin: çalılıklar
    for k in range(70):
        bx = k * (W / 70) + rng.uniform(-4, 4)
        for xx in _wrap(W, bx):
            c.ellipse((xx, 304 + rng.uniform(-4, 4)), rng.uniform(12, 20), rng.uniform(8, 12), CAN['g2'], z=12)
    c.poly([(0, 306), (W, 306), (W, H), (0, H)], CAN['g2'], z=11, bevel=2, height=1)
    return _finish(c, '#9fc6c2', 0.07)


def forest_near(W=1280, H=360):
    rng = random.Random(11)
    c = Canvas(W, H)
    bark = lambda lu, lv, px, py: (np.floor(px * 0.25 + np.sin(py * 0.05) * 2) % 5 == 0)
    dark = Mat(ramp(20, 0.40, 0.24, spread=0.45))
    for k in range(4):
        x = k * W / 4 + rng.uniform(0, W / 6)
        w = rng.uniform(20, 32)
        for xx in _wrap(W, x):
            c.poly([(xx - w * 1.3, H), (xx - w, H - 40), (xx - w * 0.8, 0), (xx + w * 0.8, 0), (xx + w, H - 40), (xx + w * 1.3, H)], TRUNK, z=0, bevel=10, height=8, paint=[(bark, dark)])
            for j in range(3):
                my = rng.uniform(40, 300)
                c.ellipse((xx - w * 0.6, my), rng.uniform(5, 9), rng.uniform(10, 18), MOSS, z=9)
            for j in range(3):
                vx = xx + rng.uniform(-w, w)
                ln = rng.uniform(50, 110)
                pts = [(vx + math.sin(i * 0.6) * 2, i * ln / 8) for i in range(9)]
                for a, b in zip(pts, pts[1:]):
                    c.capsule(a, b, 1.1, 1.1, MOSS, z=12)
                for i in range(2, 9, 2):
                    c.ellipse((pts[i][0] + 3, pts[i][1]), 3.2, 1.8, CAN['g3'], z=13, rot=0.5)
    for k in range(120):
        gx = k * (W / 120) + rng.uniform(-3, 3)
        for xx in _wrap(W, gx):
            h = rng.uniform(14, 40)
            c.capsule((xx, H + 2), (xx + rng.uniform(-8, 8), H - h), 2.4, 0.6, CAN['g2'], z=15)
    return _finish(c, '#101c1a', 0.6, rim_col='#7fae8a')


def god_ray(w=64, h=256):
    xs = np.linspace(-1, 1, w)[None, :]
    ys = np.linspace(0, 1, h)[:, None]
    a = np.clip(1 - np.abs(xs) ** 1.5, 0, 1) * np.clip(1 - ys, 0, 1) ** 1.3 * np.clip(ys * 6, 0, 1)
    img = np.zeros((h, w, 4), np.uint8)
    img[..., :3] = 255
    img[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(img)


def soft_dot(size=16):
    xs = np.linspace(-1, 1, size)
    d = np.sqrt(xs[None, :] ** 2 + xs[:, None] ** 2)
    a = np.clip(1 - d, 0, 1) ** 1.8
    img = np.zeros((size, size, 4), np.uint8)
    img[..., :3] = 255
    img[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(img)


def leaf_particles():
    img = Image.new('RGBA', (24, 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for k, c in enumerate(['#e0b03a', '#d9822b', '#b8432f', '#5a9a3c', '#8cc96a', '#ffffff']):
        d.rectangle((k * 4, 1, k * 4 + 2, 2), fill=hexc(c))
        d.point((k * 4 + 1, 0), fill=hexc(c))
    return img
