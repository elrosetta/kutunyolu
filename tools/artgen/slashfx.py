"""Kesik ve darbe sprite'ları (prosedürel, beyaz; oyunda silah rengiyle boyanır, toplamalı çizilir).
Dead Cells kesik dili: kalın parlak yay, uçlara doğru incelir; ilk kare tam parlak, sonra iz kuyruk ucundan solar.
Kaba piksel görünümü için alfa 5 kademeye yuvarlanır. Çıktı: assets/fx/slash/<ad>.png (kareler yan yana) + slash.json."""
import math
import os
import json
import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'fx', 'slash')


def _grid(size):
    ys, xs = np.mgrid[0:size, 0:size]
    cx = cy = size / 2.0 - 0.5
    return xs - cx, ys - cy


def quant(a, levels=5):
    return np.round(np.clip(a, 0, 1) * levels) / levels


def arc_frames(size=128, frames=6, span=150, radius=0.4, thick=0.12, taper=1.0, sweep_from=-1, inner_dark=False, double=False):
    """Yay: açı aralığı span (derece), yarıçap size*radius. Sert kenarlı parlak bant + ince beyaz çekirdek + hafif dış ışıma.
    Kuyruk (üst) ucu kalın başlar, uca incelir; zamanla üstten (kuyruktan) silinir."""
    xs, ys = _grid(size)
    r = np.hypot(xs, ys) / size
    ang = np.degrees(np.arctan2(ys, xs))
    out = []
    half = span / 2.0
    for f in range(frames):
        k = f / max(1, frames - 1)
        u = np.clip(ang / half, -1.5, 1.5)
        inside = np.abs(ang) <= half
        w = thick * (1 - np.abs(u) ** (2.0 * taper)) * (1.0 - 0.3 * k)
        dist = np.abs(r - radius)
        band = np.clip((w - dist) / (w * 0.25 + 1e-4), 0, 1)
        glow = np.clip(1 - dist / (w * 1.9 + 1e-4), 0, 1) * 0.35
        core = np.clip((w * 0.28 - dist) / (w * 0.12 + 1e-4), 0, 1)
        kk = max(0.0, (k - 0.3) / 0.7)  # ilk %30 tam görünür, sonra kuyruktan silinir
        fade_edge = -1.0 + 2.3 * kk
        vis = np.clip((u - fade_edge) / 0.3, 0, 1)
        a = np.clip(band + glow, 0, 1) * vis * inside * (1.0 - 0.1 * k)
        if inner_dark:
            a = a * (1 - 0.3 * np.clip(1 - np.abs(r - (radius - w * 0.55)) / (w * 0.25 + 1e-4), 0, 1))
        rgb = np.ones((size, size, 3))
        rgb[..., 2] = 0.78 + 0.22 * core
        rgb[..., 1] = 0.9 + 0.1 * core
        rgb[..., :3] = np.clip(rgb[..., :3] + core[..., None] * vis[..., None] * 0.5, 0, 1.5)
        out.append(np.dstack([rgb, quant(a, 5)]))
    return out


def line_frames(size=96, frames=5, length=0.9, thick=0.08):
    """Saplama çizgisi: merkezden sağa uzanan, uca incelen parlak çizgi + uçta kıvılcım."""
    xs, ys = _grid(size)
    out = []
    for f in range(frames):
        k = f / max(1, frames - 1)
        x = xs / size + 0.5 - 0.1  # 0..1 sola kaydırılmış başlangıç
        L = length * (0.6 + 0.4 * min(1.0, k * 2.5))
        along = np.clip(x / L, 0, 1)
        w = thick * (1 - along ** 2.5) * (1 - 0.5 * k)
        a = np.clip(1 - np.abs(ys / size) / np.maximum(w, 1e-3), 0, 1) * (x > 0) * (x < L)
        a *= np.clip((x - (k * 1.1 - 0.1) * L) / 0.2 + 1, 0, 1)  # arkadan solma
        tip = np.exp(-((xs / size - (L - 0.5 + 0.1)) ** 2 + (ys / size) ** 2) * 900) * (1 - k)
        a = np.clip(a + tip, 0, 1)
        rgb = np.ones((size, size, 3)); rgb[..., 2] = 0.85
        out.append(np.dstack([rgb, quant(a, 5)]))
    return out


def ring_frames(size=96, frames=6, radius=0.4, thick=0.1):
    xs, ys = _grid(size)
    r = np.hypot(xs, ys) / size
    ang = np.degrees(np.arctan2(ys, xs))
    out = []
    for f in range(frames):
        k = f / max(1, frames - 1)
        w = thick * (1 - 0.6 * k)
        a = np.clip(1 - np.abs(r - radius) / w, 0, 1)
        # dönen boşluk: bir kuyruk gibi 1/3 silik
        gap = ((ang - 360 * k * 1.5) % 360) / 360.0
        a *= np.clip(gap * 2.2, 0, 1)
        a *= (1 - 0.5 * k)
        rgb = np.ones((size, size, 3)); rgb[..., 2] = 0.9
        out.append(np.dstack([rgb, quant(a, 5)]))
    return out


def x_frames(size=128, frames=6):
    """Çapraz kesik: ±40 derecede iki uzun, uca incelen çizgi; ikincisi bir kare gecikmeli belirir, ikisi de kuyruktan solar."""
    xs, ys = _grid(size)
    out = []
    for f in range(frames):
        k = f / max(1, frames - 1)
        a = np.zeros((size, size))
        core = np.zeros((size, size))
        for i, ang in enumerate((-40, 40)):
            kk = max(0.0, k - 0.12 * i)
            t = math.radians(ang)
            d = np.abs(-xs * math.sin(t) + ys * math.cos(t)) / size
            along = (xs * math.cos(t) + ys * math.sin(t)) / size  # -0.5..0.5
            L = 0.46
            w = 0.055 * (1 - (np.abs(along) / L) ** 1.6) * (1 - 0.5 * kk)
            band = np.clip((w - d) / (w * 0.3 + 1e-4), 0, 1) * (np.abs(along) < L)
            vis = np.clip((along + 0.5 - kk * 1.15) / 0.2 + 0.0, 0, 1) if i == 0 else np.clip((0.5 - along - kk * 1.15) / 0.2, 0, 1)
            a = np.maximum(a, band * vis)
            core = np.maximum(core, np.clip((w * 0.3 - d) / (w * 0.12 + 1e-4), 0, 1) * vis * (np.abs(along) < L))
        rgb = np.ones((size, size, 3)); rgb[..., 2] = 0.78 + 0.22 * core
        rgb = np.clip(rgb + core[..., None] * 0.5, 0, 1.5)
        out.append(np.dstack([rgb, quant(a, 5)]))
    return out


def impact_cut(size=64, frames=5):
    xs, ys = _grid(size)
    out = []
    for f in range(frames):
        k = f / max(1, frames - 1)
        a = np.zeros((size, size))
        for ang in (-35, 25):
            t = math.radians(ang)
            d = np.abs(-xs * math.sin(t) + ys * math.cos(t)) / size
            along = (xs * math.cos(t) + ys * math.sin(t)) / size
            L = 0.46 * (0.5 + 0.5 * min(1, k * 3))
            w = 0.045 * (1 - (np.abs(along) / L) ** 2) * (1 - 0.6 * k)
            a += np.clip(1 - d / np.maximum(w, 1e-3), 0, 1) * (np.abs(along) < L)
        flash = np.exp(-(xs ** 2 + ys ** 2) / (size * size * 0.004)) * (1 - k) ** 2 * 1.5
        rgb = np.ones((size, size, 3)); rgb[..., 2] = 0.85
        out.append(np.dstack([rgb, quant(np.clip(a + flash, 0, 1), 5)]))
    return out


def impact_blunt(size=64, frames=6):
    xs, ys = _grid(size)
    r = np.hypot(xs, ys) / size
    ang = np.arctan2(ys, xs)
    out = []
    for f in range(frames):
        k = f / max(1, frames - 1)
        ring = np.clip(1 - np.abs(r - 0.08 - 0.38 * k) / (0.06 * (1 - 0.5 * k) + 0.01), 0, 1) * (1 - k)
        cracks = np.zeros_like(r)
        for i in range(7):
            a0 = i * 2 * math.pi / 7 + 0.3
            d = np.abs(np.angle(np.exp(1j * (ang - a0))))
            cracks += np.clip(1 - d / 0.07, 0, 1) * (r < 0.1 + 0.35 * min(1, k * 2)) * (r > 0.04) * (1 - 0.7 * k)
        flash = np.exp(-r * r * 60) * (1 - k) ** 1.5
        rgb = np.ones((size, size, 3)); rgb[..., 1] = 0.9; rgb[..., 2] = 0.7
        out.append(np.dstack([rgb, quant(np.clip(ring + cracks + flash, 0, 1), 5)]))
    return out


def impact_pierce(size=64, frames=5):
    xs, ys = _grid(size)
    out = []
    for f in range(frames):
        k = f / max(1, frames - 1)
        L = 0.48 * (0.4 + 0.6 * min(1, k * 2.5))
        w = 0.05 * (1 - np.abs(xs / size) / L) * (1 - 0.6 * k)
        line = np.clip(1 - np.abs(ys / size) / np.maximum(w, 1e-3), 0, 1) * (np.abs(xs / size) < L)
        sp = np.zeros_like(line)
        for i in range(6):
            a0 = i * math.pi / 3 + 0.2
            px, py = math.cos(a0) * (0.12 + 0.25 * k) * size, math.sin(a0) * (0.12 + 0.25 * k) * size
            sp += np.exp(-((xs - px) ** 2 + (ys - py) ** 2) / (size * 0.08)) * (1 - k)
        rgb = np.ones((size, size, 3)); rgb[..., 2] = 0.8
        out.append(np.dstack([rgb, quant(np.clip(line + sp, 0, 1), 5)]))
    return out


def impact_magic(size=64, frames=6):
    xs, ys = _grid(size)
    r = np.hypot(xs, ys) / size
    ang = np.arctan2(ys, xs)
    out = []
    for f in range(frames):
        k = f / max(1, frames - 1)
        ring = np.clip(1 - np.abs(r - 0.1 - 0.3 * k) / 0.04, 0, 1) * (1 - k)
        runes = (np.sin(ang * 6 + k * 8) > 0.6) * np.clip(1 - np.abs(r - 0.22 - 0.1 * k) / 0.05, 0, 1) * (1 - k)
        flash = np.exp(-r * r * 50) * (1 - k) ** 2
        rgb = np.ones((size, size, 3)); rgb[..., 0] = 0.8
        out.append(np.dstack([rgb, quant(np.clip(ring + runes + flash, 0, 1), 5)]))
    return out


def decal_crack(w=64, h=20, var=0):
    rng = np.random.default_rng(10 + var)
    ys, xs = np.mgrid[0:h, 0:w]
    a = np.zeros((h, w))
    cx = w / 2
    for i in range(7):
        ang = rng.uniform(-0.5, 0.5) + (i - 3) * 0.5
        ln = rng.uniform(w * 0.2, w * 0.5)
        for t in np.linspace(0, 1, 60):
            px = cx + math.cos(ang) * ln * t + math.sin(t * 9 + i) * 1.5
            py = h / 2 + math.sin(ang) * ln * t * 0.4
            d = np.hypot(xs - px, ys - py)
            a = np.maximum(a, np.clip(1 - d / (1.3 * (1 - t * 0.6)), 0, 1))
    rgb = np.zeros((h, w, 3)) + [0.05, 0.03, 0.05]
    return np.dstack([rgb, quant(a, 3)])


def decal_blood(w=40, h=16, var=0):
    rng = np.random.default_rng(20 + var)
    ys, xs = np.mgrid[0:h, 0:w]
    a = np.zeros((h, w))
    for i in range(14):
        px, py = rng.normal(w / 2, w * 0.18), rng.normal(h / 2, h * 0.14)
        rad = rng.uniform(1.5, 5.0)
        a = np.maximum(a, np.clip(1 - np.hypot((xs - px) / 1.6, ys - py) / rad, 0, 1))
    rgb = np.zeros((h, w, 3)) + [0.45, 0.04, 0.08]
    return np.dstack([rgb, quant(a, 3)])


def save_sheet(name, frames, meta):
    os.makedirs(OUT, exist_ok=True)
    h, w = frames[0].shape[:2]
    sheet = np.zeros((h, w * len(frames), 4))
    for i, f in enumerate(frames):
        sheet[:, i * w:(i + 1) * w] = f
    Image.fromarray((np.clip(sheet, 0, 1) * 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, name + '.png'))
    meta[name] = {'w': w, 'h': h, 'frames': len(frames)}
    print('slash', name, w, h, len(frames))


def main():
    meta = {}
    save_sheet('arc', arc_frames(128, 8, 130, 0.4, 0.13), meta)
    save_sheet('arc_thin', arc_frames(128, 8, 105, 0.4, 0.09, 1.2), meta)
    save_sheet('arc_heavy', arc_frames(144, 9, 160, 0.4, 0.17, 0.8, inner_dark=True), meta)
    save_sheet('arc_short', arc_frames(80, 6, 115, 0.4, 0.13), meta)
    save_sheet('line', line_frames(96, 5), meta)
    save_sheet('ring', ring_frames(112, 6, 0.4, 0.1), meta)
    save_sheet('x', x_frames(96, 6), meta)
    save_sheet('impact_cut', impact_cut(64, 5), meta)
    save_sheet('impact_blunt', impact_blunt(64, 6), meta)
    save_sheet('impact_pierce', impact_pierce(64, 5), meta)
    save_sheet('impact_magic', impact_magic(64, 6), meta)
    for v in range(2):
        save_sheet('decal_crack_%d' % v, [decal_crack(64, 20, v)], meta)
    for v in range(3):
        save_sheet('decal_blood_%d' % v, [decal_blood(40, 16, v)], meta)
    json.dump(meta, open(os.path.join(OUT, 'slash.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
