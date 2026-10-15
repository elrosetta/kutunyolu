"""Kesik ve darbe sprite'ları (prosedürel, beyaz; oyunda silah rengiyle çarpılarak boyanır, toplamalı çizilir).

Piksel-sanat dili (Tomlee / Medeiros kesik temelleri, anime darbe kareleri):
- Her savuruşta TEK temiz hilal: tek pürüzsüz eğri, baş kalın, kuyruk 1 piksele incelir ("rüzgâr tulumu" silueti).
  Tam şekil yalnızca tepe karesinde; öncesinde kısa "büyüme" karesi (baş önde), sonrasında kuyruk ucundan parçalanır:
  delikler -> tireler -> eğri boyunca seyrek, dışa savrulan pikseller (alfa soldurma yok).
- Üç ton: çekirdek 255, gövde 200, yalnızca dış/kuyruk tarafında 1 px kenar 120 (oyun çarparak boyar: gri = ton).
- Alfa kesinlikle 0 / 255; kenar yumuşatma ve bulanıklık yok.
Çıktı: assets/fx/slash/<ad>.png (kareler yan yana) + slash.json ({ad: {w, h, frames}}).
HD paketi (export_hd.py): SS = N iken aynı şekiller N kat ince ızgarada eşiklenir; koordinatlar mantıksal pikselde
kalır, 1 px'lik kenar / tire / kıvılcım desenleri mantıksal piksel boyunda kalır (SS ince piksel)."""
import math
import os
import json
import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'fx', 'slash')
SS = 1   # HD çarpanı (export_hd.py)

CORE = 1.0          # 255: çekirdek (beyaz kalır)
MID = 200 / 255.0   # 200: gövde (silah rengine boyanır)
EDGE = 120 / 255.0  # 120: 1 px dış kenar


def _mg(h, w):
    """np.mgrid[0:h, 0:w] karşılığı: SS kat ince ızgaranın piksel merkezleri, mantıksal koordinatta."""
    if SS == 1:
        return np.mgrid[0:h, 0:w]
    ys, xs = np.mgrid[0:h * SS, 0:w * SS]
    return (ys + 0.5) / SS - 0.5, (xs + 0.5) / SS - 0.5


def quant(a, levels=5):
    return np.round(np.clip(a, 0, 1) * levels) / levels


# ---------------------------------------------------------------- piksel ilkel şekilleri (hepsi mantıksal koordinat)

def _hash(ix, iy=0, seed=0):
    """Belirlenimci 0..1 karma (mantıksal piksel / parça indeksinden); SS'den bağımsız."""
    ix = np.asarray(ix).astype(np.int64) & 0xFFFFFFFF
    iy = np.asarray(iy).astype(np.int64) & 0xFFFFFFFF
    h = (ix * 374761393 + iy * 668265263 + (seed + 1) * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFF) / 65536.0


def _grow(m):
    """4-komşu genişletme, 1 mantıksal piksel (= SS ince piksel)."""
    out = m.copy()
    s = SS
    out[s:, :] |= m[:-s, :]
    out[:-s, :] |= m[s:, :]
    out[:, s:] |= m[:, :-s]
    out[:, :-s] |= m[:, s:]
    return out


def _erode(m):
    """4-komşu aşındırma, 1 mantıksal piksel."""
    out = m.copy()
    s = SS
    out[s:, :] &= m[:-s, :]
    out[:-s, :] &= m[s:, :]
    out[:, s:] &= m[:, :-s]
    out[:, :-s] &= m[:, s:]
    out[:s, :] = False
    out[-s:, :] = False
    out[:, :s] = False
    out[:, -s:] = False
    return out


class Frame:
    """Tek kare: ton alanı (0 = saydam, yoksa gri seviye). Sonradan boyanan üsttekini ezer."""

    def __init__(self, w, h):
        self.ys, self.xs = _mg(h, w)
        self.t = np.zeros(self.xs.shape)

    def put(self, mask, tone):
        self.t[mask] = tone

    def under(self, mask, tone):
        """Yalnızca boş piksellere boya."""
        self.t[mask & (self.t == 0)] = tone

    def outline(self, body, side=None, tone=EDGE):
        """Gövdenin dışına 1 px kenar (side: hangi tarafta)."""
        m = _grow(body) & ~body
        if side is not None:
            m &= side
        self.under(m, tone)

    def pix(self, x, y, tone):
        self.put(_pix(self.xs, self.ys, x, y), tone)

    def rgba(self):
        a = self.t > 0
        return np.dstack([np.repeat(self.t[..., None], 3, axis=2), a.astype(float)])


def _pix(xs, ys, x, y):
    """Tek mantıksal piksel (en yakın)."""
    x, y = round(float(x)), round(float(y))
    return (np.abs(xs - x) < 0.5 - 1e-6) & (np.abs(ys - y) < 0.5 - 1e-6)


def _box(xs, ys, x0, y0, x1, y1):
    """Kapsayıcı mantıksal piksel dikdörtgeni."""
    return (xs > x0 - 0.5) & (xs < x1 + 0.5) & (ys > y0 - 0.5) & (ys < y1 + 0.5)


def _disc(xs, ys, cx, cy, r):
    return np.hypot(xs - cx, ys - cy) <= r


def _ringm(xs, ys, cx, cy, r, th):
    return np.abs(np.hypot(xs - cx, ys - cy) - r) <= th / 2.0


def _diamond(xs, ys, cx, cy, r):
    return np.abs(xs - cx) + np.abs(ys - cy) <= r


def _ray(xs, ys, cx, cy, ang, r0, r1, h0, h1=0.5):
    """Merkezden ang derecede ışın: r0..r1 arası, yarı kalınlık h0 -> h1 (0.5 = tek piksel)."""
    t = math.radians(ang)
    dx, dy = xs - cx, ys - cy
    along = dx * math.cos(t) + dy * math.sin(t)
    perp = np.abs(-dx * math.sin(t) + dy * math.cos(t))
    u = np.clip((along - r0) / max(1e-6, r1 - r0), 0, 1)
    h = np.maximum(0.5 + 1e-3, h0 + (h1 - h0) * u)
    return (along >= r0 - 1e-6) & (along <= r1 + 1e-6) & (perp <= h)


def _ang_dash(xs, ys, cx, cy, n, duty=0.6, off=0.0):
    """Halka boyunca n parçalı açısal tire deseni (duty: açık oranı)."""
    ang = (np.degrees(np.arctan2(ys - cy, xs - cx)) + off) % 360.0
    per = 360.0 / n
    return (ang % per) / per < duty


def _polar(cx, cy, ang, r):
    t = math.radians(ang)
    return cx + math.cos(t) * r, cy + math.sin(t) * r


# ---------------------------------------------------------------- bant geometrisi (hilal / düz şerit ortak)

class ArcGeo:
    """Yay ekseni: merkez (cx, cy), yarıçap R, kuyruk açısı -> baş açısı (derece; görüntü koordinatı, +y aşağı).
    s: kuyruktan yay uzunluğu (px), d: eksenden işaretli uzaklık (+ = dış), inr: açı aralığı içinde."""

    def __init__(self, xs, ys, cx, cy, R, a_tail, a_head):
        self.cx, self.cy, self.R = cx, cy, R
        self.a_tail = math.radians(a_tail)
        self.sgn = 1.0 if a_head >= a_tail else -1.0
        span = abs(math.radians(a_head) - self.a_tail)
        dx, dy = xs - cx, ys - cy
        ang = np.arctan2(dy, dx)
        rel = ((ang - self.a_tail) * self.sgn + math.pi) % (2 * math.pi) - math.pi
        self.s = rel * R
        self.d = np.hypot(dx, dy) - R
        self.inr = (rel >= 0) & (rel <= span)
        self.L = span * R

    def xy(self, s, d):
        a = self.a_tail + self.sgn * s / self.R
        return self.cx + math.cos(a) * (self.R + d), self.cy + math.sin(a) * (self.R + d)


class LineGeo:
    """Düz eksen: (x0, y0)'dan ang derecede L px. d: + = eksenin "üst" tarafı (ang=0 için -y)."""

    def __init__(self, xs, ys, x0, y0, ang, L):
        self.x0, self.y0, self.L = x0, y0, L
        t = math.radians(ang)
        self.ca, self.sa = math.cos(t), math.sin(t)
        dx, dy = xs - x0, ys - y0
        self.s = dx * self.ca + dy * self.sa
        self.d = dx * self.sa - dy * self.ca
        self.inr = (self.s >= 0) & (self.s <= L)

    def xy(self, s, d):
        return self.x0 + self.ca * s + self.sa * d, self.y0 + self.sa * s - self.ca * d


def _band(g, H, p=0.6, inward=0.7, cut=1.0, th=1.0, floor=0.62, tail_cap=False):
    """Rüzgâr tulumu bandı. H: baştaki yarı kalınlık (px); kuyruk 1 px'e iner, baş yuvarlak kapaklı.
    cut: uzunluk oranı (büyüme karesi), th: kalınlık çarpanı. Bant eksenden içe (inward) doğru şişer.
    Döner: body, core, h (yarı kalınlık alanı), c (bant merkezinin d'si)."""
    L = g.L * cut
    Hc = max(floor, H * th * cut ** p)                      # baş kapağı yarıçapı
    h = np.maximum(floor, H * th * np.clip(g.s / g.L, 0, 1) ** p)
    c = -inward * (h - floor)
    cc = -inward * (Hc - floor)
    body = g.inr & (g.s <= L - Hc) & (np.abs(g.d - c) <= h)
    capd = np.hypot(g.s - (L - Hc), g.d - cc)
    body |= capd <= Hc
    core = body & (h >= 1.8) & (np.abs(g.d - c) <= 0.5 * h) & (g.s <= L - Hc)
    core |= (capd <= 0.5 * Hc) & (Hc >= 1.8)
    return body, core, h, c


def _dissolve(g, body, core, h, c, k, seed=0):
    """Kuyruktan başlayan parçalanma (k 0..1): sağlam -> çatlak (1 px enine kesikler, iç kenar tıraşlanır)
    -> ince tireler -> yok. Döner: body, core, keep (sağlam bölge)."""
    t = g.s / g.L
    P = -0.06 + 1.34 * k
    keep = t >= P
    hz = (t >= P - 0.16) & (t < P)
    dz = (t >= P - 0.44) & (t < P - 0.16)
    # çatlaklar: 5-7 px'lik parçalar arasında 1 px boşluk; parçaların iç tarafı %35 tıraşlanır
    seg = np.floor(g.s / 6.0)
    pos = g.s - seg * 6.0
    cut = pos < 1.0 + 1.0 * (_hash(seg, 1, seed) < 0.5)
    shave = g.d < c - 0.3 * h
    on3 = _hash(np.floor(g.s / 3.0), 0, seed) < 0.6
    strip = g.inr & (np.abs(g.d - (c + 1.0)) <= np.maximum(0.62, 0.3 * h))
    nb = (body & keep) | (body & hz & ~cut & ~shave) | (strip & dz & on3)
    return nb, core & keep, keep


def _embers(fr, g, h_fn, c_fn, k, seed=0, step=6.0):
    """Dağılmış bölgede eğri boyunca seyrek, dışa savrulan tek pikseller."""
    P = -0.06 + 1.34 * k
    n = int(g.L // step) + 1
    for i in range(n):
        s = 2.5 + step * i + 2.0 * _hash(i, 1, seed)
        t = s / g.L
        age = (P - 0.44 - t) / 0.5
        if age <= 0 or age >= 1 or _hash(i, 2, seed) > 0.6:
            continue
        off = 2.0 + 9.0 * age
        x, y = g.xy(s, c_fn(s) + off)
        fr.pix(x, y, MID if age < 0.5 else EDGE)


def _draw_band(fr, g, H, stage, k=0.0, p=0.6, inward=0.7, seed=0, outline=True, inner_rim=False, speed=False):
    """Bir bant karesi: stage 'grow' (baş önde yarım), 'peak' (tam), 'fade' (k ile parçalanır)."""
    cut = 0.55 if stage == 'grow' else 1.0
    th = 1.0 - 0.3 * k if stage == 'fade' else 1.0
    body, core, h, c = _band(g, H, p, inward, cut, th)
    keep = np.ones_like(body)
    if stage == 'fade':
        body, core, keep = _dissolve(g, body, core, h, c, k, seed)
    fr.put(body, MID)
    if inner_rim:
        fr.put(body & ~_erode(body) & (g.d < c) & (h >= 2.5) & keep, EDGE)
    fr.put(core, CORE)
    if outline:
        fr.outline(body & keep, side=(g.d > c))
    if speed and stage == 'peak':
        # iç tarafta birkaç hız tiresi (eş merkezli, 2 px kalın, başın gerisinde)
        for a, b, off in ((0.26, 0.38, 4.0), (0.46, 0.60, 4.0), (0.36, 0.44, 8.0)):
            m = g.inr & (np.abs(g.d - (c - h - off)) <= 1.0) & (g.s >= a * g.L) & (g.s <= b * g.L)
            fr.put(m, MID)
    if stage == 'fade':
        def c_fn(s):
            hh = max(0.62, H * th * min(1.0, s / g.L) ** p)
            return -inward * (hh - 0.62)
        _embers(fr, g, None, c_fn, k, seed)


def _schedule(frames):
    """Kare planı: büyüme, tepe, sonra k 0..1 parçalanma."""
    out = [('grow', 0.0), ('peak', 0.0)]
    n = frames - 2
    for i in range(n):
        out.append(('fade', 0.1 + 0.9 * i / max(1, n - 1)))
    return out


# ---------------------------------------------------------------- sayfalar

def arc_frames(size=128, frames=8, span=130, radius=0.4, thick=0.09, inner_rim=False, speed=False):
    """Hilal: yarıçap size*radius, açı aralığı span (derece, +x etrafında; kuyruk üstte, baş altta: aşağı savuruş).
    thick: baştaki tam kalınlık / size. Oyun yayı bıçak ucundan geçecek şekilde ölçekler (yarıçap = 0.4 w)."""
    out = []
    c = size / 2.0 - 0.5
    R = size * radius
    H = thick * size / 2.0
    for stage, k in _schedule(frames):
        fr = Frame(size, size)
        g = ArcGeo(fr.xs, fr.ys, c, c, R, -span / 2.0, span / 2.0)
        _draw_band(fr, g, H, stage, k, inner_rim=inner_rim, speed=speed)
        out.append(fr.rgba())
    return out


def line_frames(size=96, frames=5):
    """Saplama: sol-ortadan (pivot 0.1, 0.5) sağa uzanan sivri iğne + 2-3 kısa paralel hız çizgisi; tepe 1 kare."""
    out = []
    x0 = round(size * 0.1)
    y = size // 2 - 1
    Lf = size * 0.86
    H = 2.0  # en kalın yerde 5 satır; uçtaki %40 tek piksel iğne

    def needle(fr, cut, th):
        """Sivri iğne: dipten hızla kalınlaşır (u 0.15), uca doğru doğrusal incelir; satır sayısı 5-3-1."""
        xs, ys = fr.xs, fr.ys
        L = Lf * cut
        s = xs - x0
        u = np.clip(s / L, 0, 1)
        h = H * th * np.minimum(1.0, u / 0.15) ** 0.5 * (1.0 - u) ** 0.9
        h = np.maximum(0.5 + 1e-3, h)
        return (s >= 0) & (s <= L) & (np.abs(ys - y) <= h), h, s

    plan = [(0.6, 1.0), (1.0, 1.0), (1.0, 0.7), (1.0, 0.5), None]
    for f in range(frames):
        fr = Frame(size, size)
        xs, ys = fr.xs, fr.ys
        if plan[f] is None:
            # eksen boyunca seyrek pikseller; uçta 2 px parça
            for i, x in enumerate(range(x0 + 40, x0 + int(Lf) - 3, 5)):
                fr.pix(x, y, MID if i % 2 == 0 else EDGE)
            fr.put(_box(xs, ys, x0 + int(Lf) - 1, y, x0 + int(Lf), y), CORE)
            out.append(fr.rgba())
            continue
        cut, th = plan[f]
        body, h, s = needle(fr, cut, th)
        core = body & (np.abs(ys - y) <= 0.5 * h) & (h >= 1.4)
        if f == 2:
            # dip tarafı (arka %45) 4 px'lik tirelere ayrılır, uç bütün kalır
            on = _hash(np.floor(s / 4.0), 0, 3) < 0.6
            body &= (s > 0.45 * Lf) | on
            core &= s > 0.45 * Lf
        if f == 3:
            # tamamı tek satır tireler; uçtaki 10 px bütün
            on = _hash(np.floor(s / 4.0), 0, 4) < 0.5
            body &= ((s > Lf - 10) | on) & (np.abs(ys - y) <= 0.5 + 1e-3)
            core &= False
        fr.put(body, MID)
        fr.put(core, CORE)
        if f <= 1:
            fr.outline(body & (h >= 1.4), side=(ys < y))
        # hız çizgileri: tepe karesinde 3 (1 px, kademeli), sonraki karede 2 (öne kayar, kısalır, söner)
        if f == 1:
            for (dy, a, b) in ((-5, 0.22, 0.42), (5, 0.14, 0.32), (-8, 0.06, 0.18)):
                fr.put(_box(xs, ys, x0 + int(a * Lf), y + dy, x0 + int(b * Lf), y + dy), MID)
        elif f == 2:
            for (dy, a, b) in ((-5, 0.40, 0.50), (5, 0.32, 0.40)):
                fr.put(_box(xs, ys, x0 + int(a * Lf), y + dy, x0 + int(b * Lf), y + dy), EDGE)
        out.append(fr.rgba())
    return out


def ring_frames(size=112, frames=6, radius=0.4):
    """Dönüş halkası: tam halka, genişlerken 5 yaya bölünür, tirelere ve noktalara dağılır. Tepe: kare 1."""
    out = []
    c = size / 2.0 - 0.5
    R = size * radius
    T = size * 0.065
    plan = [  # (yarıçap oranı, kalınlık, boşluk derecesi, tire deseni, nokta)
        (0.82, T * 0.85, 0, False, False),
        (1.00, T, 0, False, False),
        (1.03, T * 0.7, 14, False, False),
        (1.07, T * 0.42, 34, False, False),
        (1.10, 1.2, 40, True, False),
        (1.12, 1.0, 0, False, True),
    ]
    for f in range(frames):
        rr, th, gap, dash, dots = plan[f % len(plan)]
        fr = Frame(size, size)
        xs, ys = fr.xs, fr.ys
        r = R * rr
        off = 17.0 * f
        if dots:
            n = int(2 * math.pi * r / 7)
            for i in range(n):
                if _hash(i, 0, 9) > 0.7:
                    continue
                x, y = _polar(c, c, off + 360.0 * i / n, r + 1.5 * _hash(i, 1, 9))
                fr.pix(x, y, MID if i % 2 == 0 else EDGE)
            out.append(fr.rgba())
            continue
        rad = np.hypot(xs - c, ys - c)
        body = np.abs(rad - r) <= th / 2.0
        if gap:
            body &= _ang_dash(xs, ys, c, c, 5, 1.0 - gap / 72.0, off)
        if dash:
            ang = (np.degrees(np.arctan2(ys - c, xs - c)) + off) % 360.0
            seg = np.floor(np.radians(ang) * r / 4.0)
            body &= _hash(seg, 0, 5) < 0.6
        fr.put(body, MID)
        if f <= 2:
            fr.put(body & (np.abs(rad - (r + th * 0.1)) <= th * 0.22) & (th >= 3.5), CORE)
            fr.outline(body, side=(rad > r))
        out.append(fr.rgba())
    return out


def x_frames(size=96, frames=6):
    """Çapraz kesik: iki hilal (sol-üstten sağ-alta, bir kare sonra sağ-üstten sol-alta), ikisi de kuyruktan dağılır."""
    out = []
    c = size / 2.0 - 0.5
    Rb = size * 0.75
    half_chord = size * 0.44
    ha = math.degrees(math.asin(half_chord / Rb))
    H = size * 0.075 / 2.0
    # A vuruşu: yön 40 derece (sağ-aşağı), merkez eksenin sağ-üst tarafında; yay sol-alta doğru şişer
    t = math.radians(40)
    nx, ny = math.sin(t), -math.cos(t)
    cxA, cyA = c + nx * Rb, c + ny * Rb
    th0 = math.degrees(math.atan2(-ny, -nx))      # merkezden orijine bakış
    planA = [('grow', 0), ('peak', 0), ('fade', 0.3), ('fade', 0.6), ('fade', 0.9), None]
    planB = [None, ('grow', 0), ('peak', 0), ('fade', 0.3), ('fade', 0.6), ('fade', 0.9)]
    for f in range(frames):
        fr = Frame(size, size)
        for plan, mirror, seed in ((planA, False, 11), (planB, True, 12)):
            if plan[f] is None:
                continue
            stage, k = plan[f]
            xs = (2 * c - fr.xs) if mirror else fr.xs
            g = ArcGeo(xs, fr.ys, cxA, cyA, Rb, th0 + ha, th0 - ha)
            _draw_band(fr, g, H, stage, k, p=0.65, seed=seed)
        out.append(fr.rgba())
    return out


def impact_cut(size=64, frames=5):
    """Kesik darbesi: 4 uzun ince + 4 kısa ışınlı yıldız; ışınlar uzar, merkez halkalaşır, kıvılcımlara ayrılıp söner."""
    out = []
    c = size // 2
    for f in range(frames):
        fr = Frame(size, size)
        xs, ys = fr.xs, fr.ys
        if f == 0:
            m = _disc(xs, ys, c, c, 4.2)
            for a in (0, 90, 180, 270):
                m |= _ray(xs, ys, c, c, a, 0, 22, 2.0)
            for a in (45, 135, 225, 315):
                m |= _ray(xs, ys, c, c, a, 0, 12, 1.4)
            fr.put(m, CORE)
            fr.put(m & (np.hypot(xs - c, ys - c) > 18), MID)
        elif f == 1:
            m = np.zeros(xs.shape, bool)
            for a in (0, 90, 180, 270):
                m |= _ray(xs, ys, c, c, a, 6, 28, 1.5)
            for a in (45, 135, 225, 315):
                m |= _ray(xs, ys, c, c, a, 6, 17, 1.0)
            fr.put(m, MID)
            rad = np.hypot(xs - c, ys - c)
            fr.put(m & (rad > 8) & (rad < 20), CORE)
            fr.put(_ringm(xs, ys, c, c, 5, 2.2), CORE)
        elif f == 2:
            m = np.zeros(xs.shape, bool)
            for a in (0, 90, 180, 270):
                m |= _ray(xs, ys, c, c, a, 16, 27, 1.0)
            for a in (45, 135, 225, 315):
                m |= _ray(xs, ys, c, c, a, 12, 18, 0.5)
            fr.put(m, MID)
            fr.put(m & (np.hypot(xs - c, ys - c) < 22), CORE)
            fr.put(_ringm(xs, ys, c, c, 8, 1.4) & _ang_dash(xs, ys, c, c, 8, 0.7, 10), MID)
        elif f == 3:
            for a in (0, 90, 180, 270):
                x, y = _polar(c, c, a, 26)
                fr.put(_box(xs, ys, round(x) - (a == 180), round(y) - (a == 270), round(x) + (a == 0), round(y) + (a == 90)), CORE)
                fr.pix(*_polar(c, c, a, 22), MID)
            for a in (45, 135, 225, 315):
                fr.pix(*_polar(c, c, a, 20), MID)
            fr.put(_ringm(xs, ys, c, c, 11, 1.1) & _ang_dash(xs, ys, c, c, 8, 0.45, 25), EDGE)
        else:
            for a in (0, 90, 180, 270):
                fr.pix(*_polar(c, c, a, 29), MID)
            for a in (45, 135, 225, 315):
                fr.pix(*_polar(c, c, a, 23), EDGE)
        out.append(fr.rgba())
    return out


def impact_blunt(size=64, frames=6):
    """Künt darbe: şişman yıldız patlaması + koyu çekirdekli "çatırtı" lekesi; ışınlar iri kıvılcım parçalarına ayrılır."""
    out = []
    c = size // 2
    for f in range(frames):
        fr = Frame(size, size)
        xs, ys = fr.xs, fr.ys
        rad = np.hypot(xs - c, ys - c)
        if f == 0:
            m = _disc(xs, ys, c, c, 9.5)
            for a, (r1, h0) in zip(range(0, 360, 45), [(21, 3.5), (15, 3.0)] * 4):
                m |= _ray(xs, ys, c, c, a, 0, r1, h0)
            fr.put(m, CORE)
            fr.put(_disc(xs, ys, c, c, 5.5), MID)
            fr.put(_disc(xs, ys, c, c, 2.6), EDGE)
        elif f == 1:
            m = np.zeros(xs.shape, bool)
            for a, (r1, h0) in zip(range(0, 360, 45), [(26, 2.6), (19, 2.2)] * 4):
                m |= _ray(xs, ys, c, c, a, 7, r1, h0)
            fr.put(m, MID)
            fr.put(m & (rad < 17), CORE)
            fr.put(_ringm(xs, ys, c, c, 8, 3.2), MID)
            fr.put(_ringm(xs, ys, c, c, 8.6, 1.8), CORE)
        elif f == 2:
            m = np.zeros(xs.shape, bool)
            for a, (r0, r1) in zip(range(0, 360, 45), [(18, 26), (14, 20)] * 4):
                m |= _ray(xs, ys, c, c, a, r0, r1, 1.6, 1.0)
            fr.put(m, MID)
            fr.put(m & (rad < 22), CORE)
            fr.put(_ringm(xs, ys, c, c, 12, 2.0), MID)
        elif f == 3:
            for a, r in zip(range(0, 360, 45), [26, 21] * 4):
                x, y = _polar(c, c, a, r)
                fr.put(_box(xs, ys, round(x) - 1, round(y) - 1, round(x), round(y)), MID)
            fr.put(_ringm(xs, ys, c, c, 16, 1.1) & _ang_dash(xs, ys, c, c, 8, 0.6, 20), EDGE)
        elif f == 4:
            for a, r in zip(range(0, 360, 45), [28, 23] * 4):
                fr.pix(*_polar(c, c, a, r), MID if a % 90 == 0 else EDGE)
            fr.put(_ringm(xs, ys, c, c, 19, 1.1) & _ang_dash(xs, ys, c, c, 8, 0.35, 30), EDGE)
        else:
            for a in (0, 90, 180, 270):
                fr.pix(*_polar(c, c, a, 30), MID)
        out.append(fr.rgba())
    return out


def impact_pierce(size=64, frames=5):
    """Saplama darbesi: vuruş ekseni boyunca uzun dar diken çifti + küçük halka; parçalanıp noktalara iner."""
    out = []
    c = size // 2
    for f in range(frames):
        fr = Frame(size, size)
        xs, ys = fr.xs, fr.ys
        if f == 0:
            # ileri diken uzun, geri diken kısa; küçük halka dikenlerin dibini sarar (artı işareti yok: nişangâh gibi durmasın)
            m = _ray(xs, ys, c, c, 0, 0, 27, 2.4) | _ray(xs, ys, c, c, 180, 0, 15, 2.0)
            fr.put(m, CORE)
            fr.put(m & (np.abs(xs - c) > 21), MID)
            fr.put(_ringm(xs, ys, c, c, 6, 1.6) & ~m, CORE)
        elif f == 1:
            m = _ray(xs, ys, c, c, 0, 9, 30, 1.6) | _ray(xs, ys, c, c, 180, 9, 20, 1.4)
            fr.put(m, MID)
            fr.put(m & (np.abs(xs - c) < 22), CORE)
            fr.put(_ringm(xs, ys, c, c, 8.5, 1.6) & ~m, MID)
            fr.put(_ringm(xs, ys, c, c, 9.0, 0.9) & ~m, CORE)
            fr.put(_box(xs, ys, c, c - 12, c, c - 11) | _box(xs, ys, c, c + 11, c, c + 12), MID)
        elif f == 2:
            m = _ray(xs, ys, c, c, 0, 18, 29, 1.0) | _ray(xs, ys, c, c, 180, 14, 21, 1.0)
            fr.put(m, MID)
            fr.put(m & (np.abs(xs - c) < 24), CORE)
            fr.put(_box(xs, ys, c, c - 14, c + 1, c - 13) | _box(xs, ys, c, c + 13, c + 1, c + 14), MID)
            fr.put(_ringm(xs, ys, c, c, 11, 1.1) & _ang_dash(xs, ys, c, c, 6, 0.65, 15), MID)
        elif f == 3:
            fr.put(_box(xs, ys, c + 25, c, c + 30, c), MID)
            fr.pix(c - 22, c, MID)
            fr.pix(c, c - 15, EDGE)
            fr.pix(c, c + 15, EDGE)
            fr.put(_ringm(xs, ys, c, c, 13, 1.1) & _ang_dash(xs, ys, c, c, 6, 0.4, 35), EDGE)
        else:
            fr.pix(c + 31, c, MID)
            fr.pix(c + 27, c, EDGE)
            fr.pix(c - 24, c, EDGE)
        out.append(fr.rgba())
    return out


def impact_magic(size=64, frames=6):
    """Büyü darbesi: 6 uçlu parıltı + halka; uçlar baklava parçalarına ayrılır, halka 6 yaya bölünüp tirelere iner."""
    out = []
    c = size // 2
    longs, shorts = (90, 270), (30, 150, 210, 330)
    for f in range(frames):
        fr = Frame(size, size)
        xs, ys = fr.xs, fr.ys
        rad = np.hypot(xs - c, ys - c)
        if f == 0:
            m = _disc(xs, ys, c, c, 3.2)
            for a in longs:
                m |= _ray(xs, ys, c, c, a, 0, 18, 1.6)
            for a in shorts:
                m |= _ray(xs, ys, c, c, a, 0, 13, 1.3)
            fr.put(m, CORE)
            fr.put(m & (rad > 14), MID)
            fr.put(_ringm(xs, ys, c, c, 7, 1.4) & ~m, CORE)
        elif f == 1:
            m = np.zeros(xs.shape, bool)
            for a in longs:
                m |= _ray(xs, ys, c, c, a, 6, 22, 1.4)
            for a in shorts:
                m |= _ray(xs, ys, c, c, a, 5, 16, 1.1)
            fr.put(m, MID)
            fr.put(m & (rad < 15), CORE)
            fr.put(_ringm(xs, ys, c, c, 10, 1.6) & ~m, MID)
            fr.put(_ringm(xs, ys, c, c, 10.4, 0.9) & ~m, CORE)
        elif f == 2:
            for a in longs:
                x, y = _polar(c, c, a, 20)
                fr.put(_diamond(xs, ys, round(x), round(y), 2), CORE)
            for a in shorts:
                x, y = _polar(c, c, a, 15)
                fr.put(_diamond(xs, ys, round(x), round(y), 1.5), MID)
            fr.put(_ringm(xs, ys, c, c, 13, 1.2) & _ang_dash(xs, ys, c, c, 6, 0.78, 30), MID)
        elif f == 3:
            for a in longs:
                x, y = _polar(c, c, a, 23)
                fr.put(_diamond(xs, ys, round(x), round(y), 1), MID)
            for a in shorts:
                x, y = _polar(c, c, a, 18)
                fr.put(_diamond(xs, ys, round(x), round(y), 1), MID)
            fr.put(_ringm(xs, ys, c, c, 16, 1.1) & _ang_dash(xs, ys, c, c, 12, 0.5, 45), EDGE)
        elif f == 4:
            for a in longs:
                fr.pix(*_polar(c, c, a, 25), MID)
            for a in shorts:
                fr.pix(*_polar(c, c, a, 20), EDGE)
            for i in range(12):
                fr.pix(*_polar(c, c, 15 + 30 * i, 19), EDGE)
        else:
            for a in longs:
                fr.pix(*_polar(c, c, a, 27), MID)
            for a in (30, 210):
                fr.pix(*_polar(c, c, a, 21), EDGE)
        out.append(fr.rgba())
    return out


def spark_frames(size=16, frames=4):
    """Küçük kıvılcım: 2-3 px nokta, +x yönünde tireye uzar, söner (oyun hız yönüne döndürür)."""
    out = []
    c = size // 2
    for f in range(frames):
        fr = Frame(size, size)
        xs, ys = fr.xs, fr.ys
        if f == 0:
            fr.put(_box(xs, ys, c - 1, c, c + 1, c) | _box(xs, ys, c, c - 1, c, c + 1), CORE)
        elif f == 1:
            fr.put(_box(xs, ys, c - 3, c - 1, c + 3, c), MID)
            fr.put(_box(xs, ys, c - 1, c - 1, c + 1, c), CORE)
        elif f == 2:
            fr.put(_box(xs, ys, c - 3, c, c + 5, c), MID)
            fr.put(_box(xs, ys, c + 1, c, c + 3, c), CORE)
        else:
            fr.put(_box(xs, ys, c + 2, c, c + 4, c), EDGE)
            fr.pix(c + 3, c, MID)
        out.append(fr.rgba())
    return out


def spark_m_frames(size=24, frames=5):
    """Orta kıvılcım: baklava nokta -> kalın tire -> uzun tire -> iki tire -> iki piksel."""
    out = []
    c = size // 2
    for f in range(frames):
        fr = Frame(size, size)
        xs, ys = fr.xs, fr.ys
        if f == 0:
            fr.put(_diamond(xs, ys, c, c, 2), CORE)
            fr.outline(_diamond(xs, ys, c, c, 2), tone=MID)
        elif f == 1:
            fr.put(_box(xs, ys, c - 5, c - 1, c + 4, c + 1), MID)
            fr.put(_box(xs, ys, c - 3, c - 1, c + 3, c), CORE)
            fr.put(_box(xs, ys, c - 7, c, c - 6, c) | _box(xs, ys, c + 5, c, c + 6, c), EDGE)
        elif f == 2:
            fr.put(_box(xs, ys, c - 5, c - 1, c + 8, c), MID)
            fr.put(_box(xs, ys, c, c - 1, c + 6, c), CORE)
        elif f == 3:
            fr.put(_box(xs, ys, c - 2, c, c + 2, c) | _box(xs, ys, c + 5, c, c + 9, c), MID)
            fr.pix(c + 7, c, CORE)
        else:
            fr.pix(c + 2, c, EDGE)
            fr.pix(c + 9, c, MID)
        out.append(fr.rgba())
    return out


def hit_ring_frames(size=48, frames=5):
    """Vuruş halkası: ince, keskin halka genişler, tirelere bölünüp söner."""
    out = []
    c = size // 2
    plan = [(5, 2.2, None, None), (10, 2.2, None, None), (15, 1.2, None, None), (19, 1.1, 10, 0.55), (22, 1.1, 10, 0.3)]
    for f in range(frames):
        r, th, n, duty = plan[f % len(plan)]
        fr = Frame(size, size)
        xs, ys = fr.xs, fr.ys
        rad = np.hypot(xs - c, ys - c)
        m = np.abs(rad - r) <= th / 2.0
        if n:
            m &= _ang_dash(xs, ys, c, c, n, duty, 12.0 * f)
        tone = CORE if f <= 1 else (MID if f <= 3 else EDGE)
        fr.put(m, tone)
        if f == 1:
            fr.put(m & (rad < r), MID)
        out.append(fr.rgba())
    return out


def smear_frames(w=96, h=24, frames=2):
    """Yatay silah izi: sola incelen, sağda (baş) yuvarlak kalın şerit; kare 0 dolu, kare 1 tireli."""
    out = []
    y = h // 2
    x0 = 4
    L = w - 8
    H = 4.0
    for f in range(frames):
        fr = Frame(w, h)
        g = LineGeo(fr.xs, fr.ys, x0, y, 0, L)
        # inward 0.35: bant hafifçe aşağı şişer, satır sayısı çoğunlukla birer birer artar
        body, core, hh, c = _band(g, H, p=0.8, inward=0.35, th=1.0 if f == 0 else 0.7)
        if f == 0:
            fr.put(body, MID)
            fr.put(core, CORE)
            fr.outline(body, side=(g.d > c))
        else:
            on = _hash(np.floor((g.s + 2) / 5.0), 0, 21) < 0.62
            fr.put(body & on, MID)
            fr.put(core & on & (g.s > 0.6 * L), CORE)
        out.append(fr.rgba())
    return out


def crit_burst_frames(size=96, frames=6):
    """Kritik vuruş: 1 kare dolu disk -> 8 ışınlı yıldız + halka -> ışınlar kopar, halka genişler, kıvılcımlar söner."""
    out = []
    c = size // 2
    axes, diags = (0, 90, 180, 270), (45, 135, 225, 315)
    for f in range(frames):
        fr = Frame(size, size)
        xs, ys = fr.xs, fr.ys
        rad = np.hypot(xs - c, ys - c)
        if f == 0:
            d = _disc(xs, ys, c, c, 30)
            fr.put(d, CORE)
            fr.outline(d, tone=MID)
        elif f == 1:
            m = _disc(xs, ys, c, c, 7.5)
            for a in axes:
                m |= _ray(xs, ys, c, c, a, 0, 42, 3.0)
            for a in diags:
                m |= _ray(xs, ys, c, c, a, 0, 32, 2.4)
            fr.put(m, CORE)
            fr.put(m & (rad > 30), MID)
            fr.put(_ringm(xs, ys, c, c, 16, 3.2) & ~m, MID)
            fr.put(_ringm(xs, ys, c, c, 16.6, 1.6) & ~m, CORE)
        elif f == 2:
            m = np.zeros(xs.shape, bool)
            for a in axes:
                m |= _ray(xs, ys, c, c, a, 12, 46, 2.4)
            for a in diags:
                m |= _ray(xs, ys, c, c, a, 10, 36, 1.8)
            fr.put(m, MID)
            fr.put(m & (rad < 32), CORE)
            fr.put(_ringm(xs, ys, c, c, 7, 2.0), MID)
            fr.put(_ringm(xs, ys, c, c, 24, 2.2) & ~m, MID)
            fr.put(_ringm(xs, ys, c, c, 24.6, 1.0) & ~m, CORE)
        elif f == 3:
            m = np.zeros(xs.shape, bool)
            for a in axes:
                m |= _ray(xs, ys, c, c, a, 30, 46, 1.5, 0.5)
            for a in diags:
                m |= _ray(xs, ys, c, c, a, 26, 38, 1.0, 0.5)
            fr.put(m, MID)
            fr.put(m & (rad < 40), CORE)
            fr.put(_ringm(xs, ys, c, c, 31, 1.2) & _ang_dash(xs, ys, c, c, 16, 0.6, 5), MID)
        elif f == 4:
            for a in axes:
                x, y = _polar(c, c, a, 45)
                fr.put(_box(xs, ys, round(x) - 1, round(y) - 1, round(x), round(y)), MID)
            for a in diags:
                fr.pix(*_polar(c, c, a, 39), EDGE)
            fr.put(_ringm(xs, ys, c, c, 37, 1.1) & _ang_dash(xs, ys, c, c, 16, 0.35, 15), EDGE)
        else:
            for a in axes:
                fr.pix(*_polar(c, c, a, 47), MID)
            fr.put(_ringm(xs, ys, c, c, 42, 1.1) & _ang_dash(xs, ys, c, c, 16, 0.15, 25), EDGE)
        out.append(fr.rgba())
    return out


def kill_flash_frames(size=64, frames=3):
    """Öldürme parıltısı: dolu baklava -> içi boş kalın baklava -> ince, büyük baklava."""
    out = []
    c = size // 2
    for f in range(frames):
        fr = Frame(size, size)
        xs, ys = fr.xs, fr.ys
        if f == 0:
            d = _diamond(xs, ys, c, c, 9)
            fr.put(d, CORE)
            fr.outline(d, tone=MID)
        elif f == 1:
            fr.put(_diamond(xs, ys, c, c, 19) & ~_diamond(xs, ys, c, c, 15), MID)
            fr.put(_diamond(xs, ys, c, c, 19) & ~_diamond(xs, ys, c, c, 17), CORE)
        else:
            fr.put(_diamond(xs, ys, c, c, 29) & ~_diamond(xs, ys, c, c, 27.5), MID)
            for dx, dy in ((29, 0), (-29, 0), (0, 29), (0, -29)):
                fr.put(_box(xs, ys, c + dx - 1, c + dy - 1, c + dx + 1, c + dy + 1) & _diamond(xs, ys, c, c, 29), CORE)
        out.append(fr.rgba())
    return out


# ---------------------------------------------------------------- yer izleri (toplamalı değil, olduğu gibi)

def decal_crack(w=64, h=20, var=0):
    rng = np.random.default_rng(10 + var)
    ys, xs = _mg(h, w)
    a = np.zeros(xs.shape)
    cx = w / 2
    for i in range(7):
        ang = rng.uniform(-0.5, 0.5) + (i - 3) * 0.5
        ln = rng.uniform(w * 0.2, w * 0.5)
        for t in np.linspace(0, 1, 60):
            px = cx + math.cos(ang) * ln * t + math.sin(t * 9 + i) * 1.5
            py = h / 2 + math.sin(ang) * ln * t * 0.4
            d = np.hypot(xs - px, ys - py)
            a = np.maximum(a, np.clip(1 - d / (1.3 * (1 - t * 0.6)), 0, 1))
    rgb = np.zeros(xs.shape + (3,)) + [0.05, 0.03, 0.05]
    return np.dstack([rgb, quant(a, 3)])


def decal_blood(w=40, h=16, var=0):
    rng = np.random.default_rng(20 + var)
    ys, xs = _mg(h, w)
    a = np.zeros(xs.shape)
    for i in range(14):
        px, py = rng.normal(w / 2, w * 0.18), rng.normal(h / 2, h * 0.14)
        rad = rng.uniform(1.5, 5.0)
        a = np.maximum(a, np.clip(1 - np.hypot((xs - px) / 1.6, ys - py) / rad, 0, 1))
    rgb = np.zeros(xs.shape + (3,)) + [0.45, 0.04, 0.08]
    return np.dstack([rgb, quant(a, 3)])


# ---------------------------------------------------------------- yazım

def sheet_img(frames):
    h, w = frames[0].shape[:2]
    sheet = np.zeros((h, w * len(frames), 4))
    for i, f in enumerate(frames):
        sheet[:, i * w:(i + 1) * w] = f
    return Image.fromarray(np.rint(np.clip(sheet, 0, 1) * 255).astype(np.uint8), 'RGBA')


def save_sheet(name, frames, meta, out_fn=None):
    """out_fn(name, PIL) verilirse (HD paketi) dosyayı o yazar; meta mantıksal boyutludur."""
    h, w = frames[0].shape[:2]
    im = sheet_img(frames)
    if out_fn is not None:
        out_fn(name, im)
    else:
        os.makedirs(OUT, exist_ok=True)
        im.save(os.path.join(OUT, name + '.png'))
    meta[name] = {'w': w // SS, 'h': h // SS, 'frames': len(frames)}
    print('slash', name, w, h, len(frames))


def build_all(out_fn=None):
    """Bütün kesik/darbe/iz sayfalarını üret; meta döndür. (Adlar, kare sayıları ve boyutlar oyunla sözleşmelidir.)"""
    meta = {}
    save_sheet('arc', arc_frames(128, 8, 130, 0.4, 0.09), meta, out_fn)
    save_sheet('arc_thin', arc_frames(128, 8, 112, 0.4, 0.06), meta, out_fn)
    save_sheet('arc_heavy', arc_frames(144, 9, 160, 0.4, 0.13, inner_rim=True, speed=True), meta, out_fn)
    save_sheet('arc_short', arc_frames(80, 6, 115, 0.4, 0.09), meta, out_fn)
    save_sheet('line', line_frames(96, 5), meta, out_fn)
    save_sheet('ring', ring_frames(112, 6, 0.4), meta, out_fn)
    save_sheet('x', x_frames(96, 6), meta, out_fn)
    save_sheet('impact_cut', impact_cut(64, 5), meta, out_fn)
    save_sheet('impact_blunt', impact_blunt(64, 6), meta, out_fn)
    save_sheet('impact_pierce', impact_pierce(64, 5), meta, out_fn)
    save_sheet('impact_magic', impact_magic(64, 6), meta, out_fn)
    # yeni sayfalar (koordinatör: kıvılcım / vuruş halkası / iz / kritik / öldürme)
    save_sheet('spark_s', spark_frames(16, 4), meta, out_fn)
    save_sheet('spark_m', spark_m_frames(24, 5), meta, out_fn)
    save_sheet('hit_ring', hit_ring_frames(48, 5), meta, out_fn)
    save_sheet('smear_h', smear_frames(96, 24, 2), meta, out_fn)
    save_sheet('crit_burst', crit_burst_frames(96, 6), meta, out_fn)
    save_sheet('kill_flash', kill_flash_frames(64, 3), meta, out_fn)
    for v in range(2):
        save_sheet('decal_crack_%d' % v, [decal_crack(64, 20, v)], meta, out_fn)
    for v in range(3):
        save_sheet('decal_blood_%d' % v, [decal_blood(40, 16, v)], meta, out_fn)
    return meta


def main():
    meta = build_all()
    json.dump(meta, open(os.path.join(OUT, 'slash.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
