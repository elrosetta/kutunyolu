"""Yaratık mürekkep-cel ortak yardımcıları (Çor, Kara İye, Balbal, Kara Kam ve biyom çeşitlemeleri).

inkkit.InkCanvas üstüne küçük ekler: yumuşak ışıma (yalnızca _e katmanına, bulanık), yarı saydam duman/sis dolgusu,
yırtık kumaş kenarı, zincir halkası, kemik el, buz sarkıtı, kıvılcım/zerre. Hepsi kuyruğa (z, sıra) girer.
"""
import math

import numpy as np
import skia

import inkkit as ik
from inkkit import Ink, INK
from rig import lerp2


GLOW_K = 0.55   # oyunda ışıma sayfası x1.6 toplamalı + bloom: önizlemeden belirgin güçlü görünür, hale bu payla kısılır


def glow_soft(cv, c, r, col, z=0.0, blur=0.6, alpha=1.0, ry=None):
    """Bulanık ışıma lekesi: yalnızca ışıma sayfasına (oyunda toplamalı, ışıktan bağımsız)."""
    alpha = alpha * GLOW_K
    path = ik.ellipse_path(cv.W(c), cv.u(r), cv.u(ry if ry is not None else r))

    def fn(_c):
        p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(col[0], col[1], col[2], alpha))
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.BlurStyle.kNormal_BlurStyle, cv.u(r) * blur))
        cv.ec.drawPath(path, p)
    cv._q(z, fn)


def wash(cv, path, col, alpha, z=0.0, blur=0.0, glow=None, glow_a=1.0):
    """Yarı saydam boya (duman, ıslaklık, leke); isteğe bağlı bulanık kenar ve ışıma."""
    def fn(c):
        p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(col[0], col[1], col[2], alpha))
        if blur > 0:
            p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.BlurStyle.kNormal_BlurStyle, cv.u(blur)))
        c.drawPath(path, p)
        if glow is not None:
            g = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(glow[0], glow[1], glow[2], glow_a))
            if blur > 0:
                g.setMaskFilter(skia.MaskFilter.MakeBlur(skia.BlurStyle.kNormal_BlurStyle, cv.u(blur)))
            cv.ec.drawPath(path, g)
    cv._q(z, fn)


def clipped(cv, clip_path, z, draw):
    """draw(c) çağrısını clip_path içine kırparak kuyruğa al (leke, damar, desen)."""
    def fn(c):
        c.save()
        c.clipPath(clip_path, doAntiAlias=True)
        draw(c)
        c.restore()
    cv._q(z, fn)


def paint(col, a=1.0, blur=0.0):
    p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(col[0], col[1], col[2], a))
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.BlurStyle.kNormal_BlurStyle, blur))
    return p


def ragged(p0, p1, n, depth, seed=0, side=1.0, sharp=True):
    """p0 -> p1 arası yırtık kenar noktaları (dişler side yönüne). Uçlar sivri (z=0)."""
    rng = np.random.default_rng(seed)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L * side, dx / L * side
    out = []
    for i in range(1, n * 2):
        t = i / (n * 2) + rng.uniform(-0.25, 0.25) / (n * 2)
        tip = i % 2 == 1
        d = depth * (rng.uniform(0.55, 1.15) if tip else rng.uniform(0.0, 0.25))
        q = (p0[0] + dx * t + nx * d, p0[1] + dy * t + ny * d)
        out.append((q[0], q[1], 0.0) if (tip and sharp) else q)
    return out


def chain_links(cv, a, b, n, mat, z, r=0.75, ol=0.75):
    """a -> b arası zincir: dönüşümlü yassı / dik halkalar."""
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for i in range(n):
        t = (i + 0.5) / n
        q = lerp2(a, b, t)
        L = math.hypot(b[0] - a[0], b[1] - a[1]) / n
        if i % 2 == 0:
            ring = ik.diff(cv.ellipse(q, L * 0.62, r, ang), cv.ellipse(q, L * 0.32, r * 0.38, ang))
            cv.shape(ring, mat, z=z + i * 0.01, sd=0.4, hi=0.25, ol=ol)
        else:
            cv.shape(cv.ellipse(q, L * 0.6, r * 0.42, ang), mat, z=z + 0.005 + i * 0.01, sd=0.3, hi=0.2, ol=ol * 0.8)


def bone_hand(cv, wrist, ang, mat, z, n=3, L=2.6, spread=0.5, curl=0.5, r=0.42, palm=1.1):
    """Kemik el: avuç + boğumlu parmaklar (ang = parmak yönü, radyan, x ekseninden)."""
    cv.shape(cv.ellipse(wrist, palm * 1.2, palm, ang), mat, z=z, sd=0.5, hi=0.25, ol=0.8)
    tips = []
    for k in range(n):
        a = ang + (k - (n - 1) / 2) * spread
        m = (wrist[0] + math.cos(a) * L * 0.55, wrist[1] + math.sin(a) * L * 0.55)
        t = (m[0] + math.cos(a + curl) * L * 0.55, m[1] + math.sin(a + curl) * L * 0.55)
        cv.shape(cv.limb([wrist, m, t], [r * 1.1, r, r * 0.55]), mat, z=z + 0.1 + k * 0.01, sd=0.3, hi=0.2, ol=0.75)
        cv.shape(cv.ellipse(m, r * 1.15, r * 1.15), mat, z=z + 0.15 + k * 0.01, sd=0.2, ol=0.6)
        tips.append(t)
    return tips


def icicles(cv, pts, mat, z, L=3.0, w=1.0, seed=3, glow=None):
    """Kenar boyunca sarkan buz sarkıtları (dünya noktaları)."""
    rng = np.random.default_rng(seed)
    for i, q in enumerate(pts):
        ln = L * rng.uniform(0.5, 1.2)
        ww = w * rng.uniform(0.7, 1.2)
        tri = cv.blob([(q[0] - ww, q[1] - 0.3), (q[0] + ww, q[1] - 0.3), (q[0] + rng.uniform(-0.3, 0.3), q[1] + ln, 0.0)])
        cv.shape(tri, mat, z=z + i * 0.01, sd=0.5, hi=0.35, ol=0.7, glow=glow)


def sparks(cv, c, n, r0, r1, col, z, seed=1, w=1.2, glow=None, ang=None, spread=math.pi * 2):
    """Kıvılcım / zerre: kısa incelen çizgiler (dışa doğru)."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        a = (ang if ang is not None else 0.0) + (rng.uniform(-0.5, 0.5) * spread if ang is not None else rng.uniform(0, math.tau))
        ra = rng.uniform(r0, r1)
        ln = rng.uniform(0.8, 2.0)
        p0 = (c[0] + math.cos(a) * ra, c[1] + math.sin(a) * ra)
        p1 = (c[0] + math.cos(a) * (ra + ln), c[1] + math.sin(a) * (ra + ln))
        cv.stroke([p0, p1], w * rng.uniform(0.7, 1.3), z=z, col=col, taper=(0.1, 0.9), glow=glow)


def puff(cv, c, r, mat, z, seed=0, n=7, alpha=1.0, glow=None, ol=0.7, sd=None):
    """Çizgi roman duman/bulut topağı: kenarı kabarık (yay dizisi), mürekkep konturlu."""
    rng = np.random.default_rng(seed)
    pts = []
    for i in range(n * 2):
        a = i / (n * 2) * math.tau + rng.uniform(-0.1, 0.1)
        rr = r * (1.0 if i % 2 == 0 else 0.84) * rng.uniform(0.92, 1.08)
        pts.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr * 0.9, 1.0 if i % 2 == 0 else 0.0))
    path = cv.blob(pts)
    cv.shape(path, mat, z=z, sd=sd if sd is not None else r * 0.35, hi=r * 0.12, ol=ol, glow=glow, grad=0.0, soft=0.2)
    return path


def eye_glow(cv, c, rx, ry, rot, hot, glow, z, halo=2.2, halo_a=0.38):
    """Parlayan göz: sıcak çekirdek (doku) + ışıma (sayfa) + bulanık hale."""
    cv.fill(cv.ellipse(c, rx, ry, rot), hot, z=z, glow=glow)
    glow_soft(cv, c, max(rx, ry) * halo, glow, z=z, blur=0.5, alpha=halo_a)


def occlude_glow(cv):
    """Işıma sayfasını z sırasına uydur: her opak parça (shape/fill) altındaki önceki ışımayı siler.
    (inkkit ışımayı ayrı yüzeye çizer; arkada kalan fener/göz ışığı önündeki gövdenin içinden görünmesin.)"""
    if getattr(cv, '_occl', False):
        return cv
    cv._occl = True
    o_shape, o_fill = cv.shape, cv.fill

    def _erase(path, z):
        def fn(_c):
            p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, 1))
            p.setBlendMode(skia.BlendMode.kDstOut)
            cv.ec.drawPath(path, p)
        cv._q(z, fn)

    def shape(path, mat, z=0.0, **kw):
        if path is not None and not path.isEmpty():
            _erase(path, z)
        o_shape(path, mat, z=z, **kw)

    def fill(path, col, z=0.0, glow=None, alpha=1.0):
        if alpha >= 0.99 and glow is None:
            _erase(path, z)
        o_fill(path, col, z=z, glow=glow, alpha=alpha)
    cv.shape, cv.fill = shape, fill
    return cv


def wisp(cv, start, ang, L, w, mat, z, ph=0.0, curl=0.9, alpha=0.85, glow=None, glow_a=0.6, ink=True):
    """Kıvrılan duman teli: S eğrisi boyunca kalınlaşıp incelen yarı saydam şerit + bir yanında ince mürekkep çizgisi."""
    n = 7
    pts = []
    x, y = start
    for i in range(n + 1):
        u = i / n
        a = ang + math.sin(ph + u * 4.0) * curl * u
        pts.append((x, y))
        x += math.cos(a) * L / n
        y += math.sin(a) * L / n
    W = [cv.W(q) for q in pts]
    prof = lambda u: max(0.05, math.sin(math.pi * min(1.0, u) ** 0.7) * (0.75 + 0.25 * math.sin(u * 7 + ph)))
    body = ik.taper_path(W, cv.u(w), prof=prof)

    def fn(c):
        c.drawPath(body, paint(mat.base, alpha))
        # gölge yanı: aynı şerit, ışığın tersine kaydırılmış farkı
        sh = ik.diff(body, ik.moved(body, cv.L[0] * cv.u(w * 0.35), cv.L[1] * cv.u(w * 0.35)))
        c.drawPath(sh, paint(mat.shadow, alpha))
        if glow is not None:
            g = paint(glow, glow_a, cv.u(w * 0.3))
            cv.ec.drawPath(body, g)
    cv._q(z, fn)
    if ink:
        side = [lerp2(pts[i], pts[i + 1], 0.5) for i in range(1, n - 1)]
        cv.stroke(side, 0.9, z=z + 0.01, col=INK, taper=(0.3, 0.6), alpha=0.8)
    return pts


def cloud(cv, c, r, mat, z, seed=0, lobes=9, glow=None, ol=0.75, spores=None, spore_glow=None):
    """Çizgi roman bulut patlaması: düzensiz loblu büyük topak + iç kıvrım çizgileri + saçılan spor noktaları."""
    rng = np.random.default_rng(seed)
    pts = []
    for i in range(lobes * 2):
        a = i / (lobes * 2) * math.tau + rng.uniform(-0.12, 0.12)
        lob = i % 2 == 0
        rr = r * (rng.uniform(0.85, 1.15) if lob else rng.uniform(0.62, 0.75))
        pts.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr * 0.85, 1.25 if lob else 0.0))
    path = cv.blob(pts)
    det = []
    for k in range(3):
        a = rng.uniform(0, math.tau)
        q = (c[0] + math.cos(a) * r * 0.45, c[1] + math.sin(a) * r * 0.38)
        det.append(('ink', [(q[0] - r * 0.25, q[1] + r * 0.05), (q[0], q[1] - r * 0.12), (q[0] + r * 0.22, q[1] + r * 0.04)], 1.0, (0.3, 0.3)))
    cv.shape(path, mat, z=z, sd=r * 0.35, hi=r * 0.1, ol=ol, glow=glow, grad=0.0, soft=0.25, details=det)
    if spores:
        for k in range(spores):
            a = rng.uniform(0, math.tau)
            rr = r * rng.uniform(1.05, 1.6)
            q = (c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr * 0.85)
            s = rng.uniform(0.35, 0.7)
            cv.fill(cv.ellipse(q, s, s), mat.hi, z=z + 0.1, glow=spore_glow)
    return path
