"""bosskit: stil v2 "mürekkep-cel" boss çizimleri için ortak yardımcılar (inkkit.py üstüne).

Bosslar dev: hücre dünya boyu v1 ile aynı (kamera boss boyunu hücre yüksekliğinden okur), doku yoğunluğu 4
(1080p'de 2,0 yakınlıkta 1 doku pikseli = 1 ekran pikseli). Çizgi kalınlıkları Bengü ve yaratıklarla aynı (lw sabit):
boss büyüdükçe kontur kalınlaşmaz, ayrıntı artar. Işık sol üstten (inkkit.LIGHT).

Koordinatlar dünya biriminde, orijin ayak noktası, y aşağı, yüz sağa (+x).
"""
import math

import numpy as np
import skia

import inkkit as ik


TEX = 4.0


# ------------------------------------------------------------------ geometri
def perp(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1.0
    return (-dy / d, dx / d), (dx / d, dy / d)


def along(a, b, t, off=0.0, *tens):
    """a->b doğrusunda t konumu, normal yönünde off kayması (normal = yönün saat tersine dik; aşağı inen kemikte -x).
    İsteğe bağlı üçüncü değer blob gerginliği (0 = sivri köşe)."""
    n, _ = perp(a, b)
    return (a[0] + (b[0] - a[0]) * t + n[0] * off, a[1] + (b[1] - a[1]) * t + n[1] * off) + tuple(tens)


def add(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def polar(c, ang, r):
    return (c[0] + math.cos(ang) * r, c[1] + math.sin(ang) * r)


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def ik2(a, b, l1, l2, bend):
    """a'dan b'ye iki kemik (wolfkit.ik ile aynı): bend=+1/-1 eklemin hangi yanda olduğu."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    d = max(abs(l1 - l2) + 0.05, min(l1 + l2 - 0.05, d))
    ca = max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)))
    ang = math.acos(ca)
    base = math.atan2(dy, dx)
    j = (a[0] + math.cos(base + bend * ang) * l1, a[1] + math.sin(base + bend * ang) * l1)
    e = (a[0] + math.cos(base) * d, a[1] + math.sin(base) * d)
    return j, e


def arm_fk(sh, a1, a2, l1, l2):
    """creatures3 kol açısı: 0 aşağı, pi/2 ileri (+x), pi yukarı; a2 dirsek bükümü (ileri doğru)."""
    e = (sh[0] + math.sin(a1) * l1, sh[1] + math.cos(a1) * l1)
    h = (e[0] + math.sin(a1 + a2) * l2, e[1] + math.cos(a1 + a2) * l2)
    return e, h


def prof(cv, a, b, outer, inner):
    """Profil uzuv: a->b ekseni boyunca (t, kayma) listeleri; outer +normal yanı (baştan sona), inner -normal yanı
    (sondan başa sıralanır). Kas şişkinliği, eklem çıkıntısı, incelme hepsi profilde."""
    pts = [along(a, b, t, o) for t, o in outer] + [along(a, b, t, -o) for t, o in sorted(inner, key=lambda q: -q[0])]
    return cv.blob(pts)


def muscle(cv, a, b, r0, r1, front=0.0, back=0.0, at=0.35, knob=0.0):
    """Kaslı uzuv: r0 -> r1 incelen, `at` konumunda +normal yanda `front`, -normal yanda `back` şişkinlik,
    uçta `knob` eklem topuzu."""
    rm = r0 + (r1 - r0) * at
    outer = [(-0.04, r0 * 0.75), (0.08, r0 * 0.98), (at, rm + front), (0.78, r1 * 1.02 + front * 0.25), (1.0, r1 + knob), (1.06, r1 * 0.6)]
    inner = [(-0.04, r0 * 0.75), (0.1, r0 * 0.95), (at + 0.08, rm + back), (0.8, r1 * 1.0 + back * 0.2), (1.0, r1 + knob * 0.6), (1.06, r1 * 0.6)]
    return ik.union(prof(cv, a, b, outer, inner), cv.capsule(a, a, r0 * 0.92, r0 * 0.92), cv.capsule(b, b, r1 * 0.95, r1 * 0.95))


def spike_pts(base0, base1, tip, bulge=0.0):
    m = lerp(base0, base1, 0.5)
    n, _ = perp(base0, tip)
    mid0 = add(lerp(base0, tip, 0.5), n, bulge)
    mid1 = add(lerp(base1, tip, 0.5), n, bulge)
    return [base0, mid0, (tip[0], tip[1], 0.0), mid1, base1, (m[0], m[1])]


def tufts(pts, ang, length, width, seed=0.0):
    """Dışa uzanan sivri tutam çokgen noktaları listesi (kara_boru_ink ile aynı)."""
    out = []
    for i, (x, y) in enumerate(pts):
        a = ang + math.sin(i * 2.3 + x * 0.1 + seed) * 0.25
        ln = length * (0.78 + 0.22 * math.cos(i * 1.7 + seed))
        tip = (x + math.cos(a) * ln, y + math.sin(a) * ln)
        nx_, ny_ = -math.sin(a) * width * 0.5, math.cos(a) * width * 0.5
        out.append([(x + nx_, y + ny_), (tip[0], tip[1], 0.0), (x - nx_, y - ny_)])
    return out


def fur_edge(cv, pts, ang, length, width, seed=0.0):
    return [cv.blob(t) for t in tufts(pts, ang, length, width, seed)]


def ragged(pts_line, depth, n_teeth, side=1.0, seed=0.0):
    """Çizgi boyunca dişli (yırtık kumaş / post) kenar noktaları: kapalı şeklin bir kenarı olarak kullanılır."""
    out = []
    P = [np.array(p[:2], float) for p in pts_line]
    seg = [np.linalg.norm(P[i + 1] - P[i]) for i in range(len(P) - 1)]
    L = sum(seg)
    m = n_teeth * 2
    for i in range(m + 1):
        s = L * i / m
        j = 0
        while j < len(seg) - 1 and s > seg[j]:
            s -= seg[j]
            j += 1
        t = s / max(seg[j], 1e-6)
        p = P[j] + (P[j + 1] - P[j]) * t
        d = (P[j + 1] - P[j]) / max(seg[j], 1e-6)
        nrm = np.array([-d[1], d[0]]) * side
        tip = (i % 2 == 1)
        r = depth * (0.6 + 0.4 * math.sin(i * 2.7 + seed)) if tip else 0.0
        q = p + nrm * r
        out.append((float(q[0]), float(q[1]), 0.0 if tip else 0.7))
    return out


# ------------------------------------------------------------------ zamanlama
def ease(u):
    return u * u * (3 - 2 * u)


def _mixd(a, b, u):
    out = {}
    for key in set(a) | set(b):
        va, vb = a.get(key, b.get(key)), b.get(key, a.get(key))
        if isinstance(va, (tuple, list)):
            out[key] = tuple(x0 + (y0 - x0) * u for x0, y0 in zip(va, vb))
        elif isinstance(va, (int, float)):
            out[key] = va + (vb - va) * u
        else:
            out[key] = vb if u > 0.5 else va
    return out


def keys(t, frames):
    """Doğrusal olmayan anahtar kare geçişi (t 0..1 bütün kareleri kapsar; son kare t=1)."""
    n = len(frames)
    if n == 1:
        return dict(frames[0])
    x = t * (n - 1)
    i = min(n - 2, int(x))
    return _mixd(frames[i], frames[i + 1], ease(x - i))


def pick(i, frames):
    """Kare kare (her karenin pozu ayrı tasarlandı)."""
    return dict(frames[min(i, len(frames) - 1)])


def loop_keys(t, frames):
    """Döngüsel geçiş (t 0..1, son kareden ilkine sarar)."""
    n = len(frames)
    x = (t % 1.0) * n
    i = int(x) % n
    return _mixd(frames[i], frames[(i + 1) % n], ease(x - int(x)))


# ------------------------------------------------------------------ ortak parçalar
def hand_grip(cv, h, d, r, mat, z, near=True, knuckle=None, ring=None, ring_glow=None):
    """Sap kavrayan dev el: avuç kütlesi sapa dik, dört parmak sapın önünden sarılır, başparmak üstten kilitler.
    h el merkezi (sap ekseninde), d sap yönü (birim). Dönüş: çizim yok, kuyruğa alır."""
    n = (-d[1], d[0])
    # sapın iki yanında yumruk: sap ekseni boyunca 1.6r, dik yönde 2r
    pts = []
    for (u, v) in ((-0.95, -0.9), (-0.7, -1.15), (0.0, -1.2), (0.7, -1.1), (0.98, -0.6), (1.0, 0.4), (0.75, 1.05),
                   (0.0, 1.15), (-0.75, 1.0), (-1.0, 0.2)):
        pts.append((h[0] + d[0] * u * r * 0.85 + n[0] * v * r, h[1] + d[1] * u * r * 0.85 + n[1] * v * r))
    fist = cv.blob(pts)
    det = []
    if near:
        for k in range(3):     # parmak araları (sapın önünde boğum çizgileri)
            u = -0.55 + k * 0.55
            a0 = (h[0] + d[0] * u * r * 0.85 + n[0] * 0.15 * r, h[1] + d[1] * u * r * 0.85 + n[1] * 0.15 * r)
            a1 = (h[0] + d[0] * u * r * 0.85 + n[0] * 1.05 * r, h[1] + d[1] * u * r * 0.85 + n[1] * 1.05 * r)
            det.append(('ink', [a0, a1], 1.3, (0.1, 0.6)))
        # boğum parlaması
        kc = (h[0] + n[0] * 0.75 * r, h[1] + n[1] * 0.75 * r)
        det.append(('hi', cv.ellipse(kc, r * 0.32, r * 0.2, math.atan2(d[1], d[0]))))
    cv.shape(fist, mat, z=z, sd=r * 0.42, hi=0.35 if near else 0.0, details=det, bounce=0.3 if near else 0.0)
    # başparmak
    th = cv.blob([(h[0] - d[0] * 0.6 * r - n[0] * 0.9 * r, h[1] - d[1] * 0.6 * r - n[1] * 0.9 * r),
                  (h[0] - d[0] * 1.0 * r - n[0] * 0.2 * r, h[1] - d[1] * 1.0 * r - n[1] * 0.2 * r),
                  (h[0] - d[0] * 0.75 * r + n[0] * 0.5 * r, h[1] - d[1] * 0.75 * r + n[1] * 0.5 * r),
                  (h[0] - d[0] * 0.2 * r + n[0] * 0.2 * r, h[1] - d[1] * 0.2 * r + n[1] * 0.2 * r)])
    cv.shape(th, mat, z=z + 0.05, sd=r * 0.25, hi=0.25 if near else 0.0, ol=0.85)
    if ring is not None:
        u = 0.1
        rc = (h[0] + d[0] * u * r + n[0] * 1.0 * r, h[1] + d[1] * u * r + n[1] * 1.0 * r)
        cv.shape(cv.ellipse(rc, r * 0.2, r * 0.3, math.atan2(d[1], d[0])), ring, z=z + 0.1, sd=0.4, hi=0.3, ol=0.8, glow=ring_glow)
    return fist


def open_hand(cv, w, d, r, mat, z, spread=0.6, curl=0.3, near=True, claws=None):
    """Açık el (pençe gibi açılmış parmaklar): w bilek, d el yönü (birim)."""
    n = (-d[1], d[0])
    palm_c = (w[0] + d[0] * r * 0.8, w[1] + d[1] * r * 0.8)
    palm = cv.ellipse(palm_c, r * 1.0, r * 0.85, math.atan2(d[1], d[0]))
    parts = [palm]
    tips = []
    for k in range(4):
        a = (k - 1.5) * spread * 0.45
        base = (palm_c[0] + d[0] * r * 0.6 + n[0] * (k - 1.5) * r * 0.42, palm_c[1] + d[1] * r * 0.6 + n[1] * (k - 1.5) * r * 0.42)
        dd = (d[0] * math.cos(a) - d[1] * math.sin(a), d[0] * math.sin(a) + d[1] * math.cos(a))
        ln = r * (1.05 - 0.12 * abs(k - 1.5))
        mid = (base[0] + dd[0] * ln * 0.55, base[1] + dd[1] * ln * 0.55)
        cd = (dd[0] * math.cos(curl) - dd[1] * math.sin(curl), dd[0] * math.sin(curl) + dd[1] * math.cos(curl))
        tip = (mid[0] + cd[0] * ln * 0.55, mid[1] + cd[1] * ln * 0.55)
        parts.append(cv.limb([base, mid, tip], [r * 0.24, r * 0.21, r * 0.16]))
        tips.append((tip, cd))
    # başparmak
    tb = (palm_c[0] - n[0] * r * 0.7, palm_c[1] - n[1] * r * 0.7)
    tt = (tb[0] + d[0] * r * 0.6 - n[0] * r * 0.55, tb[1] + d[1] * r * 0.6 - n[1] * r * 0.55)
    parts.append(cv.limb([tb, tt], [r * 0.3, r * 0.18]))
    cv.shape(ik.union(*parts), mat, z=z, sd=r * 0.35, hi=0.3 if near else 0.0, bounce=0.25 if near else 0.0,
             details=[('ink', [lerp(palm_c, tips[k][0], 0.35), lerp(palm_c, tips[k][0], 0.55)], 1.0, (0.2, 0.6)) for k in (1, 2)] if near else ())
    if claws is not None:
        for tip, cd in tips:
            cv.shape(cv.blob([(tip[0] - cd[1] * r * 0.14, tip[1] + cd[0] * r * 0.14), (tip[0] + cd[0] * r * 0.4, tip[1] + cd[1] * r * 0.4, 0.0),
                              (tip[0] + cd[1] * r * 0.14, tip[1] - cd[0] * r * 0.14)]), claws, z=z + 0.1, sd=0.3, ol=0.7)
    return palm_c


def glow_dot(cv, c, r, col, glow, z, core=None):
    """Işıyan nokta (göz, kor): dış renk + sıcak çekirdek, ikisi de ışıma katmanında."""
    cv.fill(cv.ellipse(c, r, r), col, z=z, glow=glow)
    if core is not None:
        cv.fill(cv.ellipse(c, r * 0.5, r * 0.5), core, z=z + 0.01, glow=core)


def flame(cv, base, ang, length, width, cols, z, seed=0.0, glow_k=1.0, ph=0.0):
    """Alev dili: kıvrık, sivri uçlu; üç katman (dış koyu kızıl, orta turuncu, iç sarı). cols = (dış, orta, iç)."""
    pts = []
    n = 6
    for i in range(n + 1):
        s = i / n
        a = ang + math.sin(s * 3.3 + ph + seed) * 0.35 * s
        pts.append((base[0] + math.cos(a) * length * s + math.sin(seed + s * 5) * width * 0.25 * s,
                    base[1] + math.sin(a) * length * s))
    for k, (col, wk_) in enumerate(zip(cols, (1.0, 0.62, 0.3))):
        pth = ik.taper_path([cv.W(q) for q in pts[:n + 1 - k]], cv.u(width * wk_), prof=lambda u: max(0.05, max(0.0, 1 - u) ** 0.9 * (0.7 + 0.3 * math.sin(u * 3.1))))
        g = tuple(c_ * glow_k * (0.55 + 0.25 * k) for c_ in col)
        cv.fill(pth, col, z=z + k * 0.01, glow=g)


def crack_glow(cv, pts, w, col, glow, z, branch=0.0, seed=0.0):
    """Işıyan çatlak (kor/kristal damarı): incelen fırça + ışıma; isteğe bağlı kısa dallar."""
    cv.stroke(pts, w, z=z, col=col, taper=(0.2, 0.6), glow=glow)
    if branch > 0:
        rng = np.random.default_rng(int(seed * 1000) + 3)
        for i in range(1, len(pts) - 1):
            if rng.random() < branch:
                a = math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0]) + rng.choice([-1, 1]) * rng.uniform(0.6, 1.1)
                ln = dist(pts[i], pts[i + 1]) * rng.uniform(0.4, 0.8)
                cv.stroke([pts[i], polar(pts[i], a, ln)], w * 0.6, z=z, col=col, taper=(0.1, 0.9), glow=glow)


class BossCanvas(ik.InkCanvas):
    """InkCanvas + örtülen ışıma: ışımasız opak bir parça çizilince altındaki (daha önce çizilmiş) ışıma silinir.
    inkkit'te ışıma katmanı örtülmez (küçük yaratıklarda göz hep üstte); bosslarda arkada kalan kristal/kor/kaya
    çatlağı, önündeki kolun üstünden parlamasın."""

    def _metal(self, *a, **kw):
        # Skia yol işlemi bazı dejenere (çok ince) altın/demir parçalarında başarısız olabilir: parlama atlanır
        try:
            super()._metal(*a, **kw)
        except RuntimeError:
            pass

    def _erase(self, path, z):
        def fn(c):
            p = skia.Paint(AntiAlias=True)
            p.setBlendMode(skia.BlendMode.kDstOut)
            self.ec.drawPath(path, p)
        self._q(z, fn)

    def shape(self, path, mat, z=0.0, **kw):
        super().shape(path, mat, z=z, **kw)
        if kw.get('glow') is None and path is not None and not path.isEmpty():
            self._erase(path, z)

    def fill(self, path, col, z=0.0, glow=None, alpha=1.0):
        super().fill(path, col, z=z, glow=glow, alpha=alpha)
        if glow is None and alpha > 0.6 and path is not None and not path.isEmpty():
            self._erase(path, z)


def new_canvas(cell, feet, ss=3, k=TEX):
    """Boss tuvali: k doku pikseli / çizim birimi (varsayılan 4 = dünya birimi); çizgi ölçeği hep Bengü ile aynı
    (lw = (4/3)^0.85), k büyüse de (Kara Börü Han tazı birimiyle çizilir: k = 4 x 2,3)."""
    return BossCanvas(cell[0], cell[1], feet[0], feet[1], k=k, ss=ss, lw=(TEX / 3.0) ** 0.85)
