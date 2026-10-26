"""ui_ink44: v44 Damgalar dokuları (scripts/core/Damga.gd, scripts/ui/DerinlikUI.gd) -> assets/ui/ink/*.png

ui_ink40'ın simge boru hattını (_render_icons: beyaz gövde, mürekkep konturu, gölge) kullanır.

  damga44.png     20 Damga tamgası, 128 px hücre (Damga.D sırasıyla): kurt izi, kartal gözü, ayı pençesi, od, kam
                  davulu, Börü Yası (ay + kurt), usul tokmakları, tulga, yel, kan, ayaz, ata kesesi, kut sarmalı,
                  Tengri şimşeği, Umay kuşu, sürü, demir (örs), Erlik mührü (ters üç çatal), okçu (Kayı yayı), balbal
  damga_tasi.png  Damga Taşı: konakta Bengisu'nun tezgâhı yanında dikili taş (mürekkep-cel; 48x80 dünya birimi,
                  texel 4 -> 192x320 px), yüzünde oyulmuş tamga çerçevesi (parlayan tamgayı oyun üstüne çizer)

Kullanım: cd tools/artgen && python ui_ink44.py [ad ...]     HD: KY_HD=2 python ui_ink44.py, sonra python hd_paket.py --paketle
"""
import math
import os
import sys

import numpy as np
import skia
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hdpack import HD
from ui_ink import OUT, fbm2, down, sk_canvas, sk_mask, paint, poly, disk, write_imports
from ui_ink40 import _render_icons

DAMGA = ['kurt_izi', 'kartal_gozu', 'ayi_postu', 'od_tamgasi', 'kam_tamgasi', 'boru_yasi', 'usul_tamgasi', 'tulga',
         'yel_tamgasi', 'kan_tamgasi', 'ayaz_tamgasi', 'ata_kesesi', 'kut_tamgasi', 'tengri_tamgasi', 'umay_tamgasi',
         'suru_tamgasi', 'demir_tamgasi', 'erlik_muhru', 'okcu_tamgasi', 'balbal_tamgasi']


def _st(n, w=0.085):
    return paint(n * w)


def _line(c, n, pts, w=0.085):
    p = skia.Path()
    p.moveTo(pts[0][0] * n, pts[0][1] * n)
    for q in pts[1:]:
        p.lineTo(q[0] * n, q[1] * n)
    c.drawPath(p, _st(n, w))


def _arc(c, n, cx, cy, r, a0, sweep, w=0.085):
    c.drawArc(skia.Rect((cx - r) * n, (cy - r) * n, (cx + r) * n, (cy + r) * n), a0, sweep, False, _st(n, w))


def damga_shape(name, c, n):
    P = paint()
    clr = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kClear)
    if name == 'kurt_izi':
        c.drawOval(skia.Rect(n * 0.3, n * 0.5, n * 0.7, n * 0.88), P)
        for (x, y, r) in [(0.2, 0.42, 0.085), (0.37, 0.24, 0.09), (0.63, 0.24, 0.09), (0.8, 0.42, 0.085)]:
            c.drawOval(skia.Rect((x - r * 0.8) * n, (y - r) * n, (x + r * 0.8) * n, (y + r) * n), P)
        c.drawPath(poly([(0.5, 0.58), (0.56, 0.7), (0.5, 0.82), (0.44, 0.7)], n), clr)
    elif name == 'kartal_gozu':
        _line(c, n, [(0.06, 0.34), (0.3, 0.5), (0.5, 0.3), (0.7, 0.5), (0.94, 0.34)])
        c.drawCircle(n * 0.5, n * 0.62, n * 0.16, P)
        c.drawCircle(n * 0.5, n * 0.62, n * 0.07, clr)
        _line(c, n, [(0.5, 0.78), (0.5, 0.95)])
    elif name == 'ayi_postu':
        for k in range(3):
            x = 0.24 + k * 0.26
            p = skia.Path()
            p.moveTo(x * n, 0.1 * n)
            p.quadTo((x + 0.16) * n, 0.5 * n, (x - 0.02) * n, 0.92 * n)
            c.drawPath(p, _st(n, 0.1))
    elif name == 'od_tamgasi':
        p = skia.Path()
        p.moveTo(n * 0.5, n * 0.06)
        p.cubicTo(n * 0.6, n * 0.32, n * 0.86, n * 0.42, n * 0.8, n * 0.68)
        p.cubicTo(n * 0.76, n * 0.86, n * 0.62, n * 0.92, n * 0.5, n * 0.92)
        p.cubicTo(n * 0.32, n * 0.92, n * 0.18, n * 0.8, n * 0.2, n * 0.62)
        p.cubicTo(n * 0.22, n * 0.46, n * 0.34, n * 0.4, n * 0.32, n * 0.26)
        p.cubicTo(n * 0.44, n * 0.32, n * 0.46, n * 0.22, n * 0.5, n * 0.06)
        p.close()
        c.drawPath(p, P)
        _line(c, n, [(0.36, 0.7), (0.5, 0.52), (0.64, 0.7)], 0.06)
        c.drawPath(poly([(0.36, 0.7), (0.5, 0.52), (0.64, 0.7)], n), clr)
    elif name == 'kam_tamgasi':
        c.drawCircle(n * 0.5, n * 0.5, n * 0.4, _st(n, 0.08))
        _line(c, n, [(0.5, 0.12), (0.5, 0.88)], 0.06)
        _line(c, n, [(0.12, 0.5), (0.88, 0.5)], 0.06)
        for (x, y) in [(0.32, 0.32), (0.68, 0.32), (0.32, 0.68), (0.68, 0.68)]:
            c.drawCircle(n * x, n * y, n * 0.055, P)
    elif name == 'boru_yasi':
        p = skia.Path()
        p.addCircle(n * 0.5, n * 0.55, n * 0.36)
        q = skia.Path()
        q.addCircle(n * 0.62, n * 0.47, n * 0.3)
        r = skia.Op(p, q, skia.PathOp.kDifference_PathOp)
        c.drawPath(r, P)
        c.drawPath(poly([(0.56, 0.18), (0.64, 0.04), (0.7, 0.2)], n), P)
        c.drawPath(poly([(0.74, 0.22), (0.86, 0.1), (0.86, 0.3)], n), P)
    elif name == 'usul_tamgasi':
        _line(c, n, [(0.18, 0.16), (0.66, 0.74)], 0.08)
        _line(c, n, [(0.82, 0.16), (0.34, 0.74)], 0.08)
        c.drawCircle(n * 0.18, n * 0.16, n * 0.08, P)
        c.drawCircle(n * 0.82, n * 0.16, n * 0.08, P)
        _arc(c, n, 0.5, 0.62, 0.34, 20, 140, 0.07)
    elif name == 'tulga':
        p = skia.Path()
        p.moveTo(n * 0.5, n * 0.06)
        p.cubicTo(n * 0.82, n * 0.1, n * 0.86, n * 0.4, n * 0.84, n * 0.62)
        p.lineTo(n * 0.16, n * 0.62)
        p.cubicTo(n * 0.14, n * 0.4, n * 0.18, n * 0.1, n * 0.5, n * 0.06)
        p.close()
        c.drawPath(p, P)
        c.drawRect(skia.Rect(n * 0.1, n * 0.62, n * 0.9, n * 0.72), P)
        _line(c, n, [(0.5, 0.0), (0.5, 0.06)], 0.06)
        _line(c, n, [(0.5, 0.72), (0.5, 0.94)], 0.09)
        c.drawRect(skia.Rect(n * 0.3, n * 0.34, n * 0.7, n * 0.42), clr)
    elif name == 'yel_tamgasi':
        for k in range(3):
            y = 0.26 + k * 0.24
            p = skia.Path()
            p.moveTo(n * 0.08, n * y)
            p.cubicTo(n * 0.3, n * (y - 0.12), n * 0.5, n * (y + 0.12), n * 0.72, n * y)
            p.quadTo(n * 0.9, n * (y - 0.08), n * 0.86, n * (y + 0.06))
            c.drawPath(p, _st(n, 0.075))
    elif name == 'kan_tamgasi':
        p = skia.Path()
        p.moveTo(n * 0.5, n * 0.06)
        p.cubicTo(n * 0.6, n * 0.32, n * 0.86, n * 0.48, n * 0.84, n * 0.66)
        p.cubicTo(n * 0.82, n * 0.86, n * 0.66, n * 0.94, n * 0.5, n * 0.94)
        p.cubicTo(n * 0.34, n * 0.94, n * 0.18, n * 0.86, n * 0.16, n * 0.66)
        p.cubicTo(n * 0.14, n * 0.48, n * 0.4, n * 0.32, n * 0.5, n * 0.06)
        p.close()
        c.drawPath(p, P)
        sc = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kClear, Style=skia.Paint.kStroke_Style,
                        StrokeWidth=n * 0.07, StrokeCap=skia.Paint.kRound_Cap)
        c.drawLine(n * 0.36, n * 0.62, n * 0.64, n * 0.62, sc)
        c.drawLine(n * 0.5, n * 0.5, n * 0.5, n * 0.8, sc)
    elif name == 'ayaz_tamgasi':
        for k in range(3):
            a = k * math.pi / 3 + math.pi / 6
            dx, dy = math.cos(a) * 0.42, math.sin(a) * 0.42
            _line(c, n, [(0.5 - dx, 0.5 - dy), (0.5 + dx, 0.5 + dy)], 0.08)
            for sg in (-1, 1):
                px, py = 0.5 + sg * dx * 0.7, 0.5 + sg * dy * 0.7
                for b in (-1, 1):
                    ba = a + b * math.pi / 4
                    _line(c, n, [(px, py), (px + sg * math.cos(ba) * 0.14, py + sg * math.sin(ba) * 0.14)], 0.06)
    elif name == 'ata_kesesi':
        p = skia.Path()
        p.moveTo(n * 0.36, n * 0.3)
        p.cubicTo(n * 0.06, n * 0.5, n * 0.1, n * 0.92, n * 0.5, n * 0.92)
        p.cubicTo(n * 0.9, n * 0.92, n * 0.94, n * 0.5, n * 0.64, n * 0.3)
        p.close()
        c.drawPath(p, P)
        c.drawPath(poly([(0.3, 0.08), (0.5, 0.2), (0.7, 0.08), (0.64, 0.3), (0.36, 0.3)], n), P)
        c.drawCircle(n * 0.5, n * 0.62, n * 0.1, clr)
        c.drawCircle(n * 0.5, n * 0.62, n * 0.045, P)
    elif name == 'kut_tamgasi':
        p = skia.Path()
        for i in range(120):
            t = i / 119.0
            a = t * math.pi * 4.2
            r = 0.04 + 0.38 * t
            x, y = 0.5 + math.cos(a) * r, 0.5 + math.sin(a) * r
            if i == 0:
                p.moveTo(x * n, y * n)
            else:
                p.lineTo(x * n, y * n)
        c.drawPath(p, _st(n, 0.075))
    elif name == 'tengri_tamgasi':
        _arc(c, n, 0.5, 0.56, 0.42, 200, 140, 0.07)
        c.drawPath(poly([(0.56, 0.18), (0.3, 0.56), (0.48, 0.56), (0.38, 0.94), (0.72, 0.46), (0.54, 0.46), (0.66, 0.18)], n), P)
    elif name == 'umay_tamgasi':
        p = skia.Path()
        p.moveTo(n * 0.04, n * 0.36)
        p.quadTo(n * 0.28, n * 0.26, n * 0.5, n * 0.56)
        p.quadTo(n * 0.72, n * 0.26, n * 0.96, n * 0.36)
        c.drawPath(p, _st(n, 0.085))
        c.drawCircle(n * 0.5, n * 0.36, n * 0.09, P)
        _line(c, n, [(0.5, 0.56), (0.5, 0.92)], 0.08)
        _line(c, n, [(0.36, 0.8), (0.5, 0.92), (0.64, 0.8)], 0.06)
    elif name == 'suru_tamgasi':
        for k in range(3):
            y = 0.2 + k * 0.26
            _line(c, n, [(0.16, y + 0.16), (0.5, y), (0.84, y + 0.16)], 0.085)
    elif name == 'demir_tamgasi':
        c.drawPath(poly([(0.1, 0.36), (0.9, 0.36), (0.78, 0.5), (0.62, 0.52), (0.66, 0.74), (0.34, 0.74), (0.38, 0.52), (0.22, 0.5)], n), P)
        c.drawRect(skia.Rect(n * 0.24, n * 0.74, n * 0.76, n * 0.86), P)
        _line(c, n, [(0.62, 0.08), (0.62, 0.26)], 0.1)
    elif name == 'erlik_muhru':
        _line(c, n, [(0.5, 0.06), (0.5, 0.72)], 0.08)
        p = skia.Path()
        p.moveTo(n * 0.18, n * 0.94)
        p.quadTo(n * 0.18, n * 0.62, n * 0.5, n * 0.62)
        p.quadTo(n * 0.82, n * 0.62, n * 0.82, n * 0.94)
        c.drawPath(p, _st(n, 0.08))
        _line(c, n, [(0.5, 0.72), (0.5, 0.96)], 0.08)
        c.drawCircle(n * 0.5, n * 0.24, n * 0.14, _st(n, 0.07))
    elif name == 'okcu_tamgasi':
        # Kayı tamgası: yay ve iki ok
        _arc(c, n, 0.5, 0.86, 0.36, 180, 180, 0.08)
        _line(c, n, [(0.5, 0.86), (0.28, 0.1)], 0.07)
        _line(c, n, [(0.5, 0.86), (0.72, 0.1)], 0.07)
        c.drawPath(poly([(0.28, 0.04), (0.2, 0.18), (0.34, 0.16)], n), P)
        c.drawPath(poly([(0.72, 0.04), (0.8, 0.18), (0.66, 0.16)], n), P)
    elif name == 'balbal_tamgasi':
        c.drawCircle(n * 0.5, n * 0.18, n * 0.12, P)
        c.drawPath(poly([(0.32, 0.32), (0.68, 0.32), (0.74, 0.92), (0.26, 0.92)], n), P)
        sc = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kClear, Style=skia.Paint.kStroke_Style,
                        StrokeWidth=n * 0.05, StrokeCap=skia.Paint.kRound_Cap)
        c.drawLine(n * 0.4, n * 0.5, n * 0.6, n * 0.5, sc)
        c.drawLine(n * 0.36, n * 0.72, n * 0.64, n * 0.72, sc)


def damga44():
    _render_icons(DAMGA, damga_shape, 'damga44.png')


def damga_tasi(seed=4401):
    """Dikili taş: koyu taş gövde, mürekkep kontur, yan gölge, çatlaklar, yosun, oyulmuş çerçeve, taban toprağı."""
    W, H = 192, 320
    S = 3
    w, h = W * S * HD, H * S * HD
    rng = np.random.default_rng(seed)
    surf, c = sk_canvas(w, h)
    body = skia.Path()
    body.moveTo(w * 0.2, h * 0.94)
    body.lineTo(w * 0.17, h * 0.3)
    body.cubicTo(w * 0.18, h * 0.08, w * 0.4, h * 0.03, w * 0.52, h * 0.035)
    body.cubicTo(w * 0.7, h * 0.04, w * 0.84, h * 0.12, w * 0.83, h * 0.32)
    body.lineTo(w * 0.81, h * 0.94)
    body.close()
    c.drawPath(body, paint())
    m = sk_mask(surf)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # taş rengi: soğuk gri, sağa doğru gölge, gürültü lekeleri
    base = np.array([0.43, 0.42, 0.46], np.float32)
    shade = np.clip((xx / w - 0.38) * 1.6, 0, 1)
    nz = fbm2(h, w, 18 * S * HD, rng, 4)
    nz = (nz - nz.mean()) / (nz.std() + 1e-6)
    rgb = base[None, None, :] * (1.0 - 0.38 * shade[..., None]) * (1.0 + 0.07 * nz[..., None])
    # üst ışık
    top = np.clip(1.0 - yy / (h * 0.4), 0, 1) * np.clip(1.0 - shade, 0, 1)
    rgb += 0.06 * top[..., None]
    # yosun (alt kısım, sol)
    moss = np.clip((yy / h - 0.62) * 3.0, 0, 1) * np.clip(nz * 0.6 + 0.2, 0, 1) * np.clip(1.0 - shade * 1.2, 0, 1)
    rgb = rgb * (1 - 0.55 * moss[..., None]) + np.array([0.28, 0.4, 0.24], np.float32)[None, None, :] * 0.55 * moss[..., None]
    # oyulmuş çerçeve (iç kenarı koyu, dış kenarı açık)
    s2, c2 = sk_canvas(w, h)
    fr = skia.Rect(w * 0.3, h * 0.2, w * 0.7, h * 0.56)
    c2.drawRoundRect(fr, w * 0.05, w * 0.05, paint(w * 0.03))
    frame = sk_mask(s2)
    fs = ndimage.shift(frame, (h * 0.004, w * 0.006), order=1)
    rgb = rgb * (1 - 0.6 * frame[..., None]) + 0.08 * np.clip(fs - frame, 0, 1)[..., None]
    # tamga yuvası (çerçeve içi hafif çukur)
    inner = ((xx > w * 0.33) & (xx < w * 0.67) & (yy > h * 0.22) & (yy < h * 0.54)).astype(np.float32)
    rgb *= (1 - 0.18 * inner[..., None])
    # alt yazıt şeridi: üç küçük oyuk çizgi
    s3, c3 = sk_canvas(w, h)
    for k in range(3):
        y = h * (0.64 + k * 0.07)
        c3.drawLine(w * 0.3, y, w * (0.68 - 0.05 * k), y + h * 0.005, paint(w * 0.022))
    runes = sk_mask(s3)
    rgb *= (1 - 0.55 * runes[..., None])
    # çatlaklar
    s4, c4 = sk_canvas(w, h)
    for (x0, y0, x1, y1, x2, y2) in [(0.78, 0.2, 0.7, 0.34, 0.74, 0.46), (0.24, 0.6, 0.3, 0.74, 0.26, 0.88)]:
        p = skia.Path()
        p.moveTo(w * x0, h * y0)
        p.quadTo(w * x1, h * y1, w * x2, h * y2)
        c4.drawPath(p, paint(w * 0.012))
    cracks = sk_mask(s4)
    rgb *= (1 - 0.7 * cracks[..., None])
    # mürekkep konturu
    r = int(w * 0.022)
    outline = np.clip(ndimage.grey_dilation(m, footprint=disk(r)) - m, 0, 1)
    ink = np.array([0.04, 0.035, 0.05], np.float32)
    alpha = np.clip(m + outline, 0, 1)
    rgb = rgb * m[..., None] + ink[None, None, :] * outline[..., None]
    rgb = rgb / np.maximum(alpha[..., None], 1e-4)
    # taban toprağı (yumuşak gölge lekesi)
    ground = np.exp(-(((xx - w * 0.5) / (w * 0.45)) ** 2 + ((yy - h * 0.95) / (h * 0.03)) ** 2))
    ga = np.clip(ground * 0.85, 0, 1) * (1 - alpha)
    rgb = rgb * alpha[..., None] + ink[None, None, :] * ga[..., None]
    alpha = np.clip(alpha + ga, 0, 1)
    rgb = rgb / np.maximum(alpha[..., None], 1e-4)
    out = np.zeros((h, w, 4), np.float32)
    out[..., :3] = np.clip(rgb, 0, 1)
    out[..., 3] = alpha
    o = down(out * np.concatenate([alpha[..., None]] * 3 + [np.ones_like(alpha)[..., None]], axis=2), S)
    a = o[..., 3]
    o[..., :3] = o[..., :3] / np.maximum(a[..., None], 1e-4)
    Image.fromarray(np.clip(np.rint(o * 255), 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'damga_tasi.png'))
    print('yazıldı damga_tasi.png', o.shape)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:]
    for fn in [damga44, damga_tasi]:
        if not only or fn.__name__ in only:
            fn()
    if HD <= 1:
        write_imports()
