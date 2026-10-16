"""inkkit: mürekkep + cel gölge karakter çizim takımı (stil v2 "çizgi roman", Shinobi: Art of Vengeance yönü).

Piksel sanat DEĞİL: Skia ile kenar yumuşatmalı vektör çizim, 1080p'de 1 doku pikseli = 1 ekran pikseli
(v15: dünya 480x270 x4 => doku yoğunluğu `k` = 4; önce 640x360 x3). Oyunda doğrusal süzgeç + mipmap ile gösterilir.

Model (her parça = kapalı bir yol):
  1. düz taban rengi
  2. tek sert gölge tonu: yol − (yolun ışığa doğru kaydırılmış kopyası) => ışığın tersindeki hilal (sol üst ışık)
     + isteğe bağlı açık gölge şekilleri (kumaş kıvrımı kamaları), seyrek mürekkep taraması (derin gölgede)
  3. küçük sert parlama: yol − (ışığın tersine kaydırılmış kopya) => ışığa bakan ince hilal (metalde keskin)
  4. kontur: ince fırça çizgisi + gölge tarafında kalınlaşan mürekkep hilali (değişken kalınlık, uçlarda incelir)
  5. alttakine düşen gölge (cast): parça gölge yönüne kaydırılıp alttaki çizimi çarpar (kModulate, alfayı korur)
Bitirişte: dış silüete ek kalın kontur (alt/gölge yanında daha kalın), içte ince soğuk kenar ışığı (arka kenar),
düz-yumuşak normal haritası (yalnızca silüet kenarında eğim: sahne ışıkları kenarı hafifçe yakar), ışıma katmanı.

Koordinatlar dünya biriminde (y aşağı), orijin ayak noktası; tüm genişlikler 1080p ekran pikseli (px) cinsinden,
`lw` ile ölçeklenir (k = 4: v2 kamerası 2,0 yakın, 1080p'de 1 doku pikseli = 1 ekran pikseli; çizgiler (k/3)^0.85 kalın).

Kalite katmanı (v15): kontur ışık yanında incelir ve yer yer kırılır (uçları sivrilen boşluk), gölge yanında kalınlaşır ve
dış kenarı kuru fırça gibi pürüzlenir; sert cel gölgesinin ışık yanına taşan bulanık ikincil yarı ton; gölgenin en uzak
kenarında yansıyan ışık bandı (bounce); metalde karanlık ufuk yansıması + keskin beyaz parlama ve yıldız ışıltı; postta
(kind='fur') kenardan içe doğru sivri kıl darbeleri; bitirişte dolguların içinde çok hafif fırça/kâğıt dokusu (grain).
"""
import colorsys
import math

import numpy as np
import skia
from scipy import ndimage

SD_K = 1.45        # gölge kayması çarpanı (hepsi için)
GRAD = 0.10        # parça içi değer geçişi (0 = düz)
INK = (0x15 / 255, 0x16 / 255, 0x1d / 255)
LIGHT = (-0.74, -0.67)      # ışığa doğru (sol üst)
GRAIN = 0.045               # dolgu içi fırça/kâğıt dokusu genliği (bitiriş)


# ------------------------------------------------------------------ renk
def hexc(s):
    s = s.lstrip('#')
    return tuple(int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _hue_toward(h, target, amt):
    d = ((target - h + 0.5) % 1.0) - 0.5
    step = math.copysign(min(abs(d), amt), d)
    return (h + step) % 1.0


def shade_of(rgb, v=0.56, hue=0.07, sat=1.12, target=0.70):
    """Gölge tonu: koyu, doyumlu, mor-maviye kayan (sarıda turuncu-toprağa, kırmızıda mora)."""
    h, s, vv = colorsys.rgb_to_hsv(*rgb)
    if s < 0.12:      # beyaz/gri: soğuk mavi-gri
        h, s = target - 0.05, max(s, 0.16) + 0.06
    else:
        h = _hue_toward(h, target, hue)
    return colorsys.hsv_to_rgb(h, min(1.0, s * sat), vv * v)


def light_of(rgb, v=1.16, sat=0.8, hue=0.03):
    h, s, vv = colorsys.rgb_to_hsv(*rgb)
    h = _hue_toward(h, 0.14, hue)
    return colorsys.hsv_to_rgb(h, s * sat, min(1.0, vv * v + 0.06))


def mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


class Ink:
    """Mürekkep-cel malzemesi: taban, gölge, parlama, (isteğe bağlı) derin gölge."""
    def __init__(self, base, shadow=None, hi=None, deep=None, kind='cloth', name=''):
        self.base = hexc(base) if isinstance(base, str) else base
        self.shadow = (hexc(shadow) if isinstance(shadow, str) else shadow) if shadow else shade_of(self.base)
        self.hi = (hexc(hi) if isinstance(hi, str) else hi) if hi else light_of(self.base)
        self.deep = (hexc(deep) if isinstance(deep, str) else deep) if deep else shade_of(self.shadow, v=0.62, hue=0.03)
        self.kind = kind
        self.name = name

    def darker(self, k=0.8, name=''):
        """Uzak (arka) bacak/kol için bir ton koyu kopya."""
        f = lambda c: tuple(x * k for x in c)
        m = Ink(f(self.base), f(self.shadow), f(self.hi), f(self.deep), self.kind, name or self.name + ' (uzak)')
        return m


def _c4(rgb, a=1.0):
    return skia.Color4f(rgb[0], rgb[1], rgb[2], a)


# ------------------------------------------------------------------ yol yardımcıları
def _op(a, b, op):
    r = skia.Op(a, b, op)
    return r if r is not None else skia.Path()


def union(*ps):
    out = None
    for p in ps:
        if p is None:
            continue
        out = skia.Path(p) if out is None else _op(out, p, skia.PathOp.kUnion_PathOp)
    return out if out is not None else skia.Path()


def diff(a, b):
    return _op(a, b, skia.PathOp.kDifference_PathOp)


def isect(a, b):
    return _op(a, b, skia.PathOp.kIntersect_PathOp)


def moved(p, dx, dy):
    q = skia.Path(p)
    q.offset(dx, dy)
    return q


def _cr_points(pts, closed, tens=1.0, n=8):
    """Catmull-Rom örnekleme (yoğun çoklu çizgi)."""
    P = [np.array(p[:2], float) for p in pts]
    m = len(P)
    out = []
    segs = m if closed else m - 1
    for i in range(segs):
        p0 = P[i - 1] if (closed or i > 0) else P[i]
        p1 = P[i]
        p2 = P[(i + 1) % m]
        p3 = P[(i + 2) % m] if (closed or i + 2 < m) else P[(i + 1) % m]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            q = 0.5 * ((2 * p1) + (-p0 + p2) * t * tens + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 * tens
                       + (-p0 + 3 * p1 - 3 * p2 + p3) * t3 * tens) if tens != 1.0 else \
                0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
            out.append(q)
    if not closed:
        out.append(P[-1])
    return out


def smooth_path(pts, closed=True):
    """Noktalardan geçen yumuşak yol. Nokta (x, y, 0) => sivri köşe (teğet sıfır)."""
    m = len(pts)
    P = [np.array(p[:2], float) for p in pts]
    T = [(p[2] if len(p) > 2 else 1.0) for p in pts]
    path = skia.Path()
    path.moveTo(*P[0])
    segs = m if closed else m - 1
    for i in range(segs):
        i0 = (i - 1) % m if closed else max(0, i - 1)
        i2 = (i + 1) % m
        i3 = (i + 2) % m if closed else min(m - 1, i + 2)
        p0, p1, p2, p3 = P[i0], P[i], P[i2], P[i3]
        c1 = p1 + (p2 - p0) / 6.0 * T[i]
        c2 = p2 - (p3 - p1) / 6.0 * T[i2]
        path.cubicTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if closed:
        path.close()
    return path


def poly_path(pts):
    path = skia.Path()
    path.moveTo(*pts[0][:2])
    for p in pts[1:]:
        path.lineTo(*p[:2])
    path.close()
    return path


def circle_path(c, r):
    p = skia.Path()
    p.addCircle(c[0], c[1], r)
    return p


def ellipse_path(c, rx, ry, rot=0.0):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(c[0] - rx, c[1] - ry, c[0] + rx, c[1] + ry))
    if rot:
        m = skia.Matrix()
        m.setRotate(math.degrees(rot), c[0], c[1])
        p.transform(m)
    return p


def capsule_path(p0, p1, r0, r1):
    """Konik kapsül (iki daire + dış teğetler)."""
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    d = math.hypot(dx, dy)
    if d < 1e-6 or d <= abs(r0 - r1):
        return circle_path(p0 if r0 >= r1 else p1, max(r0, r1))
    ux, uy = dx / d, dy / d
    s = (r0 - r1) / d
    c = math.sqrt(max(0.0, 1 - s * s))
    # teğet doğrultuları (normal bileşen c, eksen bileşen s)
    pts = []
    for sg in (1, -1):
        nx, ny = -uy * sg, ux * sg
        ox, oy = nx * c + ux * s, ny * c + uy * s
        pts.append(((x0 + ox * r0, y0 + oy * r0), (x1 + ox * r1, y1 + oy * r1)))
    quad = poly_path([pts[0][0], pts[0][1], pts[1][1], pts[1][0]])
    return union(circle_path(p0, r0), circle_path(p1, r1), quad)


def taper_path(pts, w, taper=(0.35, 0.35), wmin=0.15, smooth=True, prof=None):
    """Değişken kalınlıklı fırça darbesi (dolu çokgen). pts cihaz koordinatı, w cihaz birimi en kalın genişlik."""
    if len(pts) < 2:
        return skia.Path()
    Q = _cr_points(pts, False, n=10) if (smooth and len(pts) > 2) else [np.array(p[:2], float) for p in pts]
    Q = np.array(Q)
    seg = np.hypot(*(Q[1:] - Q[:-1]).T)
    L = seg.sum()
    if L < 1e-6:
        return skia.Path()
    s = np.concatenate([[0], np.cumsum(seg)]) / L
    ti, to = taper
    if prof is None:
        a = np.clip(s / max(ti, 1e-3), 0, 1) if ti > 0 else np.ones_like(s)
        b = np.clip((1 - s) / max(to, 1e-3), 0, 1) if to > 0 else np.ones_like(s)
        wp = w * np.maximum(wmin, np.sin(a * math.pi / 2) * np.sin(b * math.pi / 2))
    else:
        wp = w * np.array([prof(x) for x in s])
    tg = np.gradient(Q, axis=0)
    tn = np.hypot(tg[:, 0], tg[:, 1])[:, None] + 1e-9
    tg = tg / tn
    nrm = np.stack([-tg[:, 1], tg[:, 0]], 1)
    left = Q + nrm * wp[:, None] * 0.5
    right = Q - nrm * wp[:, None] * 0.5
    path = poly_path([tuple(p) for p in np.concatenate([left, right[::-1]])])
    # yuvarlak uçlar (kalınsa)
    caps = [circle_path(tuple(Q[0]), wp[0] * 0.5), circle_path(tuple(Q[-1]), wp[-1] * 0.5)]
    return union(path, *caps)


def disk(r):
    r = max(0.5, r)
    n = int(math.ceil(r))
    y, x = np.mgrid[-n:n + 1, -n:n + 1]
    return (x * x + y * y) <= r * r + 0.25


# ------------------------------------------------------------------ tuval
class InkCanvas:
    """Dünya birimiyle çizim; `k` doku pikseli / dünya birimi, `ss` süper örnekleme.

    Çizim çağrıları (z, sıra) ile kuyruğa alınır; finish() sıralayıp çizer, küçültür ve son işlemleri yapar."""

    def __init__(self, w, h, ox, oy, k=3.0, ss=3, light=LIGHT, lw=None):
        self.w, self.h, self.ox, self.oy, self.k, self.ss = w, h, ox, oy, k, ss
        # çizgi kalınlığı ölçeği: genişlikler k=3 (1,5 yakınlık) için yazıldı; daha yoğun dokuda biraz daha ince göreli çizgi
        self.lw = lw if lw is not None else (k / 3.0) ** 0.85
        self.surf = skia.Surface(int(w * ss), int(h * ss))
        self.c = self.surf.getCanvas()
        self.c.clear(skia.Color4f(0, 0, 0, 0))
        self.esurf = skia.Surface(int(w * ss), int(h * ss))
        self.ec = self.esurf.getCanvas()
        self.ec.clear(skia.Color4f(0, 0, 0, 0))
        ln = math.hypot(*light)
        self.L = (light[0] / ln, light[1] / ln)
        self.ops = []
        self._seq = 0
        self.xf = []          # dünya -> dünya dönüşümleri (yuvarlanma vb.)
        self.wob = 0.0        # el çizimi titreşimi (dünya birimi)

    # ---- dönüşüm
    def push(self, fn):
        self.xf.append(fn)

    def pop(self):
        self.xf.pop()

    def W(self, p):
        x, y = p[0], p[1]
        for f in reversed(self.xf):
            x, y = f((x, y))
        return ((x * self.k + self.ox) * self.ss, (y * self.k + self.oy) * self.ss)

    def u(self, v):
        """dünya uzunluğu -> cihaz"""
        return v * self.k * self.ss

    def px(self, v):
        """1080p pikseli (k=3 ölçeğinde) -> cihaz"""
        return v * self.ss * self.lw

    # ---- yol kurucular (dünya biriminde girdi, cihaz yolu döner)
    def capsule(self, p0, p1, r0, r1):
        return capsule_path(self.W(p0), self.W(p1), self.u(r0), self.u(r1))

    def limb(self, pts, radii):
        """Eklemli uzuv: ardışık kapsüllerin birleşimi (kas şişkinliği için ara noktalar)."""
        ps = [capsule_path(self.W(a), self.W(b), self.u(ra), self.u(rb)) for a, b, ra, rb in zip(pts, pts[1:], radii, radii[1:])]
        return union(*ps)

    def ellipse(self, c, rx, ry, rot=0.0):
        rr = rot
        if self.xf:   # dönüşümün açısı: iki noktadan ölç
            a = self.W((0, 0))
            b = self.W((1, 0))
            rr += math.atan2(b[1] - a[1], b[0] - a[0])
        return ellipse_path(self.W(c), self.u(rx), self.u(ry), rr)

    def blob(self, pts, closed=True):
        q = [self.W(p) + ((p[2],) if len(p) > 2 else ()) for p in pts]
        return smooth_path(q, closed)

    def poly(self, pts):
        return poly_path([self.W(p) for p in pts])

    # ---- kuyruk
    def _q(self, z, fn):
        self.ops.append((z, self._seq, fn))
        self._seq += 1

    def shape(self, path, mat, z=0.0, sd=None, hi=0.0, ol=1.0, ol_side=1.0, cast=0.0, cast_col=(0.62, 0.6, 0.78),
              shadows=(), lights=(), details=(), hatch=0.0, hatch_ang=None, light=None, flat=False, deep=0.0,
              noshadow=False, glow=None, grad=GRAD, soft=None, bounce=0.0, spec=None, fur=None):
        """Bir parçayı çiz. sd: gölge kayması (dünya, None = biçimden), hi: parlama hilali (dünya),
        ol: kontur çarpanı, cast: alttakine düşen gölge (dünya), shadows: ek gölge yolları (cihaz; parçaya kırpılır),
        details: [(tür, veri, ...)] kırpılmış ayrıntılar: ('ink', pts_dünya, px, taper) | ('shade', yol) | ('hi', yol)
        | ('col', yol, rgb) | ('stroke', pts_dünya, px, rgb, taper), hatch: derin gölgede tarama yoğunluğu.
        soft: ikincil yumuşak yarı ton alfası (None = 0.38), bounce: gölge uzak kenarında yansıyan ışık alfası,
        spec: metal parlaması (None = metalde 1), fur: post kılı yoğunluğu (None = kind 'fur' ise 1)."""
        L = light or self.L
        if path is None or path.isEmpty():
            return

        def fn(c):
            b = path.getBounds()
            th = min(b.width(), b.height())
            d = self.u(sd) * SD_K if sd is not None else th * 0.6
            if cast > 0:
                pc = moved(path, -L[0] * self.u(cast), -L[1] * self.u(cast))
                p = skia.Paint(AntiAlias=True, Color4f=_c4(cast_col))
                p.setBlendMode(skia.BlendMode.kModulate)
                c.drawPath(diff(pc, path), p)
            c.save()
            c.clipPath(path, doAntiAlias=True)
            c.drawPath(path, skia.Paint(AntiAlias=True, Color4f=_c4(mat.base)))
            shp = None
            if not flat and not noshadow:
                shp = diff(path, moved(path, L[0] * d, L[1] * d))
                for s in shadows:
                    shp = union(shp, s)
                sa = 0.38 if soft is None else soft
                if sa > 0:   # ikincil yumuşak geçiş: sert gölgenin ışık yanına taşan bulanık yarı ton (iki tonlu cel)
                    wide = diff(path, moved(path, L[0] * d * 1.75, L[1] * d * 1.75))
                    sp_ = skia.Paint(AntiAlias=True, Color4f=_c4(mix(mat.base, mat.shadow, 0.6), sa))
                    sp_.setMaskFilter(skia.MaskFilter.MakeBlur(skia.BlurStyle.kNormal_BlurStyle, max(0.6, d * 0.3)))
                    c.drawPath(wide, sp_)
                c.drawPath(shp, skia.Paint(AntiAlias=True, Color4f=_c4(mat.shadow)))
                if bounce > 0:   # yansıyan ışık: gölgenin en uzak kenarında ince, yumuşak açık bant
                    far = diff(path, moved(path, L[0] * d * 0.32, L[1] * d * 0.32))
                    bp_ = skia.Paint(AntiAlias=True, Color4f=_c4(mix(mat.shadow, mat.base, 0.55), bounce))
                    bp_.setMaskFilter(skia.MaskFilter.MakeBlur(skia.BlurStyle.kNormal_BlurStyle, max(0.5, d * 0.07)))
                    c.drawPath(far, bp_)
                if deep > 0:
                    dp = diff(path, moved(path, L[0] * d * deep, L[1] * d * deep))
                    c.drawPath(dp, skia.Paint(AntiAlias=True, Color4f=_c4(mat.deep)))
            elif shadows:
                for s in shadows:
                    c.drawPath(s, skia.Paint(AntiAlias=True, Color4f=_c4(mat.shadow)))
            if grad > 0:   # yüzey içinde hafif değer geçişi (ışık yanı açık, gölge yanı koyu): düz "çıkartma" hissini kırar
                cx, cy = b.centerX(), b.centerY()
                R_ = 0.5 * math.hypot(b.width(), b.height())
                p0 = skia.Point(cx + L[0] * R_, cy + L[1] * R_)
                p1 = skia.Point(cx - L[0] * R_, cy - L[1] * R_)
                a_ = int(255 * grad)
                sh_ = skia.GradientShader.MakeLinear([p0, p1], [skia.ColorSetARGB(a_, 255, 250, 235), skia.ColorSetARGB(0, 128, 128, 128),
                                                                 skia.ColorSetARGB(int(a_ * 1.2), 20, 16, 40)], [0.0, 0.5, 1.0])
                c.drawPath(path, skia.Paint(AntiAlias=True, Shader=sh_))
            if hi > 0:
                hp = diff(path, moved(path, -L[0] * self.u(hi), -L[1] * self.u(hi)))
                c.drawPath(hp, skia.Paint(AntiAlias=True, Color4f=_c4(mat.hi)))
            for lp in lights:
                c.drawPath(lp, skia.Paint(AntiAlias=True, Color4f=_c4(mat.hi)))
            sp = (1.0 if mat.kind == 'metal' else 0.0) if spec is None else spec
            if sp > 0 and not flat:
                self._metal(c, path, b, L, d, mat, sp, hi)
            fr = (1.0 if mat.kind == 'fur' else 0.0) if fur is None else fur
            if fr > 0:
                self._fur(c, path, L, mat, fr, seed=(z * 7.31) % 6.283)
            if hatch > 0 and shp is not None:
                self._hatch(c, diff(path, moved(path, L[0] * d * 0.55, L[1] * d * 0.55)), hatch, hatch_ang)
            for dt in details:
                self._detail(c, dt, mat)
            c.restore()
            if glow is not None:
                self.ec.drawPath(path, skia.Paint(AntiAlias=True, Color4f=_c4(glow)))
            if ol > 0:
                self._outline(c, path, ol, ol_side, L, seed=(z * 12.9898) % 6.283)
        self._q(z, fn)

    def _contours(self, path, step):
        """Yolun her konturu için (P, T, N dışa, n, uzunluk) örnekleri."""
        out = []
        pm = skia.PathMeasure(path, True, 1.0)
        while True:
            Ln = pm.getLength()
            if Ln > step * 3:
                n = int(Ln / step)
                P = np.zeros((n, 2))
                T = np.zeros((n, 2))
                for i in range(n):
                    pos, tan = pm.getPosTan(Ln * i / n)
                    P[i] = (pos.fX, pos.fY)
                    T[i] = (tan.fX, tan.fY)
                N = np.stack([T[:, 1], -T[:, 0]], 1)
                # dışa bakan normal: birkaç örnekte yolun dışında kalan yönü seç
                votes = 0
                for i in range(0, n, max(1, n // 9)):
                    q = P[i] + N[i] * self.px(0.8)
                    votes += -1 if path.contains(float(q[0]), float(q[1])) else 1
                if votes < 0:
                    N = -N
                out.append((P, T, N, n, Ln))
            if not pm.nextContour():
                break
        return out

    def _outline(self, c, path, ol, side, L, seed=0.0):
        """Fırça konturu: yol boyunca örneklenir; kalınlık = taban x (0.8..1.2 düşük frekanslı fırça baskısı)
        + gölge yanında (normal ışığa ters baktıkça) dışa doğru kalınlaşma. Işık yanında ince ve yer yer kırık
        (boşluğun iki ucu sivrilir), gölge/alt yanda kalın ve dış kenarı kuru fırça gibi hafif pürüzlü."""
        w0 = self.px(1.5) * ol
        ex = self.px(2.4) * ol * side
        out = skia.Path()
        out.setFillType(skia.PathFillType.kWinding)
        step = self.px(1.1)
        rng = np.random.default_rng(int(abs(seed) * 1000) + 17)
        for P, T, N, n, Ln in self._contours(path, step):
            if True:
                sarc = np.arange(n) * (Ln / n) / (self.ss * self.lw)
                nz = 0.5 + 0.32 * np.sin(sarc * 0.11 + seed) + 0.18 * np.sin(sarc * 0.29 + seed * 1.7)
                sh = np.clip(N[:, 0] * -L[0] + N[:, 1] * -L[1], 0, 1) ** 1.2
                lf = np.clip(N[:, 0] * L[0] + N[:, 1] * L[1], 0, 1)
                w = w0 * (0.8 + 0.4 * nz) * (1.0 - 0.3 * lf) + ex * sh
                # kırık çizgi: ışığa bakan yanda seyrek boşluklar (uçlar yumuşakça incelir)
                if Ln / self.ss > 40:
                    brk = np.sin(sarc * (6.283 / 83.0) + seed * 7.0) + 0.55 * np.sin(sarc * (6.283 / 31.0) + seed * 3.1)
                    gap = np.clip((brk - 0.95) / 0.35, 0, 1) * np.clip((lf - 0.35) / 0.35, 0, 1)
                    gap = gap * gap * (3 - 2 * gap)
                    w = w * (1.0 - 0.93 * gap)
                win = np.minimum(w * 0.5, w0 * 0.55)
                # kuru fırça: kalın gölge yanının dış kenarı yüksek frekanslı pürüz (kıl izleri)
                rag = ndimage.gaussian_filter1d(rng.standard_normal(n), 1.2, mode='wrap')
                rag = rag / (rag.std() + 1e-6)
                ext = (w - win) * (1.0 + 0.16 * rag * np.clip(sh * 1.4 - 0.3, 0, 1))
                inner = P - N * win[:, None]
                outer = P + N * np.maximum(0.0, ext)[:, None]
                for i in range(n):
                    j = (i + 1) % n
                    q = [outer[i], outer[j], inner[j], inner[i]]
                    ar = sum(q[k][0] * q[(k + 1) % 4][1] - q[(k + 1) % 4][0] * q[k][1] for k in range(4))
                    if ar < 0:
                        q = q[::-1]
                    out.moveTo(*q[0])
                    out.lineTo(*q[1])
                    out.lineTo(*q[2])
                    out.lineTo(*q[3])
                    out.close()
        c.drawPath(out, skia.Paint(AntiAlias=True, Color4f=_c4(INK)))

    def _metal(self, c, path, b, L, d, mat, amt, hi):
        """Metal: ışıklı kenara paralel karanlık ufuk yansıması + keskin beyaz parlama + küçük yıldız ışıltı."""
        R_ = 0.5 * min(b.width(), b.height())
        if R_ < self.px(1.5):
            return
        dd = max(d, self.px(2.0))
        band = diff(isect(path, moved(path, -L[0] * dd * 0.55, -L[1] * dd * 0.55)),
                    moved(path, -L[0] * dd * 1.05, -L[1] * dd * 1.05))
        bpn = skia.Paint(AntiAlias=True, Color4f=_c4(mat.deep, 0.42 * amt))
        bpn.setMaskFilter(skia.MaskFilter.MakeBlur(skia.BlurStyle.kNormal_BlurStyle, max(0.5, dd * 0.06)))
        c.drawPath(band, bpn)
        hs = self.u(hi) * 0.45 if hi > 0 else self.px(1.2)
        glint = diff(path, moved(path, -L[0] * hs, -L[1] * hs))
        cx, cy = b.centerX(), b.centerY()
        big = max(b.width(), b.height())
        gc = (cx + L[0] * R_ * 0.75, cy + L[1] * R_ * 0.75)
        win_ = ellipse_path(gc, big * 0.42, big * 0.42)
        c.drawPath(isect(glint, win_), skia.Paint(AntiAlias=True, Color4f=_c4((1.0, 1.0, 0.98), 0.95 * min(1.0, amt))))
        if amt >= 1.0 and R_ > self.px(7.0):   # küçük dört kollu ışıltı (yatay kol uzun)
            sx, sy = cx + L[0] * R_ * 0.6, cy + L[1] * R_ * 0.6
            ln = min(R_ * 0.45, self.px(4.0))
            for a, k_ in ((0.0, 1.0), (math.pi * 0.5, 0.6)):
                dx, dy = math.cos(a) * ln * k_, math.sin(a) * ln * k_
                c.drawPath(taper_path([(sx - dx, sy - dy), (sx, sy), (sx + dx, sy + dy)], self.px(1.2), (0.5, 0.5)),
                           skia.Paint(AntiAlias=True, Color4f=_c4((1.0, 1.0, 1.0), 0.8)))

    def _fur(self, c, path, L, mat, amt, seed=0.0):
        """Post kılları: kenardan içe, hafif eğik, sivri uçlu kısa darbeler. Gölge yanında mürekkep, ortada gölge
        tonu, ışık yanında seyrek ve açık (kenar ışığını bölen kıl uçları)."""
        rng = np.random.default_rng(int(abs(seed) * 977) + 5)
        step = self.px(3.0) / max(0.3, amt)
        ink_p, sh_p, hi_p = skia.Path(), skia.Path(), skia.Path()
        for P, T, N, n, Ln in self._contours(path, step):
            for i in range(n):
                if rng.random() < 0.18:
                    continue
                sh = float(np.clip(N[i, 0] * -L[0] + N[i, 1] * -L[1], -1, 1))
                ln = self.px(rng.uniform(3.5, 7.5)) * (0.7 + 0.5 * amt)
                tilt = rng.uniform(0.25, 0.6) * (1 if (i % 2) else -1) * 0.6 + 0.35
                p0 = P[i] + N[i] * self.px(0.6)
                p1 = P[i] - N[i] * ln * 0.55 + T[i] * ln * tilt * 0.5
                p2 = P[i] - N[i] * ln + T[i] * ln * tilt
                st = taper_path([tuple(p0), tuple(p1), tuple(p2)], self.px(rng.uniform(0.9, 1.4)), (0.05, 0.85))
                if sh > 0.25:
                    ink_p.addPath(st)
                elif sh > -0.35:
                    sh_p.addPath(st)
                elif rng.random() < 0.5:
                    hi_p.addPath(st)
        dark = (0.3 * mat.base[0] + 0.55 * mat.base[1] + 0.15 * mat.base[2]) < 0.35
        # koyu postta kıllar açık tonla (parlama rengi) okunur, açık postta gölge tonuyla
        c.drawPath(sh_p, skia.Paint(AntiAlias=True, Color4f=_c4(mat.hi if dark else mat.shadow, 0.55 if dark else 0.8)))
        c.drawPath(ink_p, skia.Paint(AntiAlias=True, Color4f=_c4(INK, 0.85)))
        c.drawPath(hi_p, skia.Paint(AntiAlias=True, Color4f=_c4(mat.hi if dark else mat.shadow, 0.7 if dark else 0.45)))

    def _hatch(self, c, region, dens, ang=None):
        b = region.getBounds()
        if b.isEmpty():
            return
        a = ang if ang is not None else math.atan2(self.L[1], self.L[0]) + math.pi * 0.5 + 0.35
        dx, dy = math.cos(a), math.sin(a)
        nx, ny = -dy, dx
        sp = self.px(3.2) / max(0.2, dens)
        cx, cy = b.centerX(), b.centerY()
        R = math.hypot(b.width(), b.height()) * 0.5 + 2
        c.save()
        c.clipPath(region, doAntiAlias=True)
        k = 0
        t = -R
        while t <= R:
            ln = R * (0.55 + 0.45 * ((k * 0.618) % 1.0))
            p0 = (cx + nx * t - dx * ln, cy + ny * t - dy * ln)
            p1 = (cx + nx * t + dx * ln, cy + ny * t + dy * ln)
            c.drawPath(taper_path([p0, p1], self.px(1.1), (0.4, 0.4), smooth=False),
                       skia.Paint(AntiAlias=True, Color4f=_c4(INK, 0.85)))
            t += sp
            k += 1
        c.restore()

    def _detail(self, c, dt, mat):
        kind = dt[0]
        if kind == 'ink':          # ('ink', pts_dünya, px, taper)
            pts, w = dt[1], dt[2]
            tp = dt[3] if len(dt) > 3 else (0.4, 0.4)
            c.drawPath(taper_path([self.W(p) for p in pts], self.px(w), tp), skia.Paint(AntiAlias=True, Color4f=_c4(INK)))
        elif kind == 'stroke':     # ('stroke', pts_dünya, px, rgb, taper)
            pts, w, col = dt[1], dt[2], dt[3]
            tp = dt[4] if len(dt) > 4 else (0.4, 0.4)
            c.drawPath(taper_path([self.W(p) for p in pts], self.px(w), tp), skia.Paint(AntiAlias=True, Color4f=_c4(col)))
        elif kind == 'shade':      # ('shade', yol)
            c.drawPath(dt[1], skia.Paint(AntiAlias=True, Color4f=_c4(mat.shadow)))
        elif kind == 'deep':
            c.drawPath(dt[1], skia.Paint(AntiAlias=True, Color4f=_c4(mat.deep)))
        elif kind == 'hi':
            c.drawPath(dt[1], skia.Paint(AntiAlias=True, Color4f=_c4(mat.hi)))
        elif kind == 'col':        # ('col', yol, rgb)
            c.drawPath(dt[1], skia.Paint(AntiAlias=True, Color4f=_c4(dt[2])))
        elif kind == 'fn':         # ('fn', callable(c))
            dt[1](c)

    def wedge(self, pts, depth, side=1.0, power=0.8):
        """Kıvrım gölgesi kaması: çizginin bir yanına doğru şişen, iki ucu sivri şekil (cihaz yolu)."""
        Q = np.array(_cr_points([self.W(p) for p in pts], False, n=8)) if len(pts) > 2 else np.array([self.W(p) for p in pts])
        if len(Q) < 2:
            return skia.Path()
        tg = np.gradient(Q, axis=0)
        tg = tg / (np.hypot(tg[:, 0], tg[:, 1])[:, None] + 1e-9)
        nrm = np.stack([-tg[:, 1], tg[:, 0]], 1) * side
        s_ = np.linspace(0, 1, len(Q))
        prof = np.sin(np.pi * np.clip(s_, 0, 1)) ** power * self.u(depth)
        off = Q + nrm * prof[:, None]
        return poly_path([tuple(p) for p in np.concatenate([Q, off[::-1]])])

    def fold(self, pts, depth=0.9, w=1.4, side=1.0, taper=(0.45, 0.45)):
        """Kumaş kıvrımı: gölge kaması + üstünde mürekkep çizgisi (shape(details=...) için)."""
        return [('shade', self.wedge(pts, depth, side)), ('ink', pts, w, taper)]

    def stroke(self, pts, w, z=0.0, col=INK, taper=(0.35, 0.35), glow=None, alpha=1.0):
        """Serbest fırça darbesi (dünya noktaları, px genişlik)."""
        q = [self.W(p) for p in pts]

        def fn(c):
            pth = taper_path(q, self.px(w), taper)
            c.drawPath(pth, skia.Paint(AntiAlias=True, Color4f=_c4(col, alpha)))
            if glow is not None:
                self.ec.drawPath(pth, skia.Paint(AntiAlias=True, Color4f=_c4(glow)))
        self._q(z, fn)

    def fill(self, path, col, z=0.0, glow=None, alpha=1.0):
        def fn(c):
            c.drawPath(path, skia.Paint(AntiAlias=True, Color4f=_c4(col, alpha)))
            if glow is not None:
                self.ec.drawPath(path, skia.Paint(AntiAlias=True, Color4f=_c4(glow)))
        self._q(z, fn)

    # ---- bitiriş
    def finish(self, outer=1.1, outer_shift=(0.45, 0.75), rim=0.0, rim_col=(0.62, 0.86, 1.0), rim_dir=(0.8, -0.6),
               rim_w=1.4, normal_edge=3.0, normal_tilt=0.55, form=None, grain=GRAIN):
        for z, s, fn in sorted(self.ops, key=lambda o: (o[0], o[1])):
            fn(self.c)
        ss = self.ss
        if form:   # bütün gövdenin büyük ışık/gölge ayrımı (çizgi romanın kütle gölgesi)
            fd, fcol = form
            snap = self.surf.makeImageSnapshot()
            mask = skia.Surface(int(self.w * ss), int(self.h * ss))
            mc = mask.getCanvas()
            mc.clear(skia.Color4f(0, 0, 0, 0))
            mc.drawImage(snap, 0, 0)
            p = skia.Paint()
            p.setBlendMode(skia.BlendMode.kDstOut)
            mc.drawImage(snap, self.L[0] * self.u(fd), self.L[1] * self.u(fd), skia.SamplingOptions(), p)
            sh_img = mask.makeImageSnapshot()
            lp = skia.Paint()
            lp.setBlendMode(skia.BlendMode.kMultiply)
            self.c.saveLayer(None, lp)
            self.c.drawImage(sh_img, 0, 0)
            pm = skia.Paint(Color4f=_c4(fcol))
            pm.setBlendMode(skia.BlendMode.kSrcIn)
            self.c.drawPaint(pm)
            self.c.restore()
        img = self.surf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType,
                                                   alphaType=skia.AlphaType.kPremul_AlphaType).astype(np.float32) / 255.0
        A = img[..., 3]
        # dış silüet konturu: alfa genişletilir (alt/gölge yanına kayık), mürekkep altta
        lw = self.lw
        if outer > 0:
            sh = ndimage.shift(A, (outer_shift[1] * ss * lw, outer_shift[0] * ss * lw), order=1, mode='constant')
            dil = ndimage.grey_dilation(np.maximum(A, sh), footprint=disk(outer * ss * lw))
            dil = np.clip(dil, 0, 1)
            ink = np.zeros_like(img)
            ink[..., :3] = np.array(INK, np.float32) * dil[..., None]
            ink[..., 3] = dil
            img = img + ink * (1.0 - A[..., None])     # premultiplied "over": sprite ink'in üstünde
            A = img[..., 3]
        # içte ince soğuk kenar ışığı (arka kenar): siluetin rim_dir yanında, konturun hemen içinde
        if rim > 0:
            inner = ndimage.grey_erosion(A, footprint=disk((outer + 2.3) * ss * lw))
            dx, dy = rim_dir
            m = np.clip(inner - ndimage.shift(inner, (-dy * rim_w * ss * lw, -dx * rim_w * ss * lw), order=1, mode='constant'), 0, 1)
            m = m * rim
            col = np.array(rim_col, np.float32)
            rgb = img[..., :3]
            img[..., :3] = rgb + (col[None, None] * A[..., None] - rgb) * (m[..., None] * 0.5) * (1 - rgb)
        # küçült (kutu süzgeç, önceden çarpılmış uzayda)
        h, w = self.h, self.w
        img = img[:h * ss, :w * ss].reshape(h, ss, w, ss, 4).mean(axis=(1, 3))
        a = img[..., 3:4]
        rgb = np.where(a > 1e-4, img[..., :3] / np.maximum(a, 1e-4), 0)
        if grain > 0:   # dolgu içi fırça/kâğıt dokusu: karede sabit (kâğıt), koyularda (mürekkep) kendiliğinden kaybolur
            rgb = rgb * (1.0 + grain * paper_grain(h, w)[..., None])
        rgba = np.concatenate([np.clip(rgb, 0, 1), np.clip(a, 0, 1)], -1)
        em = self.esurf.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType,
                                                   alphaType=skia.AlphaType.kPremul_AlphaType).astype(np.float32) / 255.0
        em = em[:h * ss, :w * ss].reshape(h, ss, w, ss, 4).mean(axis=(1, 3))
        nm = soft_normal(rgba[..., 3], normal_edge, normal_tilt)
        return rgba, nm, em


_GRAIN = {}


def paper_grain(h, w, seed=11):
    """Yaklaşık [-1, 1] doku: çapraz yönlü fırça izleri (uzun, yumuşak) + ince kâğıt tanesi. Boyuta göre önbellekli."""
    key = (h, w, seed)
    if key in _GRAIN:
        return _GRAIN[key]
    rng = np.random.default_rng(seed)
    m = int(math.hypot(h, w)) + 8
    f = ndimage.gaussian_filter(rng.standard_normal((m, m)).astype(np.float32), (0.9, 7.0), mode='wrap')
    f = ndimage.rotate(f, 32.0, reshape=False, order=1, mode='wrap')
    y0, x0 = (m - h) // 2, (m - w) // 2
    f = f[y0:y0 + h, x0:x0 + w]
    f = f / (f.std() + 1e-6)
    g = ndimage.gaussian_filter(rng.standard_normal((h, w)).astype(np.float32), 0.7)
    g = g / (g.std() + 1e-6)
    out = np.clip(0.75 * f + 0.35 * g, -2.5, 2.5) / 2.5
    _GRAIN[key] = out.astype(np.float32)
    return _GRAIN[key]


def soft_normal(A, edge=3.0, tilt=0.55):
    """Düz normal + yalnızca silüet kenarında yumuşak dışa eğim (sahne ışığı kenarı hafifçe yakar)."""
    B = ndimage.gaussian_filter(A, edge * 0.6)
    gy, gx = np.gradient(B)
    nx, ny = -gx, -gy
    mag = np.hypot(nx, ny)
    s = np.clip(mag * edge * 2.2, 0, 1) * tilt
    nx = np.where(mag > 1e-5, nx / np.maximum(mag, 1e-5), 0) * s
    ny = np.where(mag > 1e-5, ny / np.maximum(mag, 1e-5), 0) * s
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    out = np.zeros(A.shape + (4,), np.float32)
    out[..., 0] = nx * 0.5 + 0.5
    out[..., 1] = -ny * 0.5 + 0.5   # Godot: yeşil yukarı (OpenGL)
    out[..., 2] = nz * 0.5 + 0.5
    out[..., 3] = A
    return out


def to_png(arr, path):
    from PIL import Image
    a = np.clip(arr * 255.0 + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(a, 'RGBA').save(path)
