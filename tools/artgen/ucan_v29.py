"""v29: uçan ve büyücü yaratıkların tam gövde animasyon takımı (Çor ailesi, iye büyücüleri, Tozkoparan, Işıltı Kamı).

Eski yaratık satırları tek bir gövde çiziminin üstünde yalnızca kolu / feneri oynatıyordu ("saldırırken yalnızca kol
oynuyor"). Bu takım her kareyi bütün gövdeyle kurar:

  * anahtar pozlar + giriş eğrisi (`pose_at`): hazırlık oturarak kurulur, vuruş kübik hızlanır, aşma yavaşlayarak durur;
    döngülerde son anahtar ilk anahtara akar.
  * gövde dönüşümü (`body_xf`): bütün çizim bir pivot çevresinde döner, kayar ve EKSEN BOYUNCA ezilip uzar (squash /
    stretch). `fix_ellipse` elipsleri dönüşümle birlikte gerçekten ezer (inkkit yalnızca açıyı izliyordu).
  * kanat: yan görünüşte kanat çırpışı (`feather_wing`, `bat_wing`): aşağı vuruşta kanat tam açık (tüyler kapalı, geniş),
    yukarı vuruşta bilekten katlanır (el tüyleri geride, uç tüyler ayrılır), orta vuruşta kanat izleyiciye bakar (kısa ve
    geniş görünür). Tüyler kemik çizgisinin arkasında, vuruş yönünün tersine gecikir (overlap).
  * hız çizgileri (`speed_lines`), mürekkep zerreleri (`flecks`), çözülme (`dissolve`: ölümde gövde mürekkep / kor
    kenarlı lekelere ayrılarak dağılır; doğuşta tersine toplanır; ışıma sayfasına kor kenarı yazar).
  * zırhlı hazırlık ("!!") için turuncu kor halesi (`armor_aura`): "!" pozundan siluet ve ışımayla ayrılır.
"""
import math

import numpy as np
import skia
from scipy import ndimage

import inkkit as ik
from inkkit import Ink, INK
from rig import lerp2
import yaratik_ink_kit as yk

ARMOR = (1.0, 0.55, 0.1)       # "!!" turuncusu (Enemy._tele: Color(1.0, 0.62, 0.12))
ARMOR_HOT = (1.0, 0.86, 0.5)


# ------------------------------------------------------------------ zaman eğrileri ve anahtarlar
def ease(u, k='io'):
    u = min(1.0, max(0.0, u))
    if k == 'l':
        return u
    if k == 'i':        # hızlanarak (vuruş)
        return u * u * u
    if k == 'i2':
        return u * u
    if k == 'o':        # yavaşlayarak (aşma, oturma)
        return 1.0 - (1.0 - u) ** 3
    if k == 'o2':
        return 1.0 - (1.0 - u) ** 2
    if k == 'b':        # geri aşmalı yavaşlama (oturup hafif geri gelir)
        c = 1.70158
        return 1.0 + (c + 1.0) * (u - 1.0) ** 3 + c * (u - 1.0) ** 2
    if k == 'h':        # basamak: anahtar gelince birden
        return 1.0 if u >= 1.0 else 0.0
    return u * u * (3.0 - 2.0 * u)


def mix(a, b, t):
    if isinstance(a, (tuple, list)):
        return tuple(mix(x, y, t) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return a + (b - a) * t
    return b if t >= 0.5 else a


def pose_at(t, keys, loop=False, base=None):
    """keys: [(zaman 0..1, {alan: değer}, giriş eğrisi)]. Eksik alanlar önceki anahtardan taşınır (ilkinde sonrakinden).
    loop: son anahtardan sonra ilk anahtara (zaman + 1) akar."""
    names = []
    for _, d, _ in keys:
        for n in d:
            if n not in names:
                names.append(n)
    cur = dict(base or {})
    for n in names:
        if n not in cur:
            for _, d, _ in keys:
                if n in d:
                    cur[n] = d[n]
                    break
    full = []
    for tk, d, e in keys:
        cur = dict(cur, **d)
        full.append((tk, cur, e))
    if loop:
        full.append((full[0][0] + 1.0, full[0][1], keys[0][2]))
        if t < full[0][0]:
            t += 1.0
    if t <= full[0][0]:
        return dict(full[0][1])
    for i in range(1, len(full)):
        if t <= full[i][0] + 1e-9:
            t0, a, _ = full[i - 1]
            t1, b, e = full[i]
            u = ease((t - t0) / max(1e-6, t1 - t0), e)
            return {n: mix(a[n], b[n], u) for n in a}
    return dict(full[-1][1])


def ts_even(n):
    return [round(i / n, 4) for i in range(n)]


# ------------------------------------------------------------------ gövde dönüşümü
def body_xf(cv, pv, rot=0.0, sx=1.0, sy=1.0, off=(0.0, 0.0), skew=0.0):
    """Bütün sonraki çizimi pv çevresinde ez/uzat (yerel eksende), eğ, döndür ve kaydır. cv.pop() ile kaldırılır."""
    c, s = math.cos(rot), math.sin(rot)

    def f(p):
        x = (p[0] - pv[0]) * sx
        y = (p[1] - pv[1]) * sy
        x += y * skew
        return (pv[0] + off[0] + x * c - y * s, pv[1] + off[1] + x * s + y * c)
    cv.push(f)


def fix_ellipse(cv):
    """Dönüşüm varken elipsleri örnek noktalarla çiz (ezilme / eğilme de uygulanır)."""
    if getattr(cv, '_v29e', False):
        return cv
    cv._v29e = True
    o = cv.ellipse

    def ell(c, rx, ry, rot=0.0):
        if not cv.xf:
            return o(c, rx, ry, rot)
        cr, sr = math.cos(rot), math.sin(rot)
        pts = []
        for i in range(20):
            a = i / 20 * math.tau
            x, y = math.cos(a) * rx, math.sin(a) * ry
            pts.append((c[0] + x * cr - y * sr, c[1] + x * sr + y * cr))
        return cv.blob(pts)
    cv.ellipse = ell
    return cv


def canvas(w, h, ox, oy, k, ss=3):
    return fix_ellipse(yk.occlude_glow(ik.InkCanvas(w, h, ox, oy, k=k, ss=ss)))


# ------------------------------------------------------------------ yardımcı geometri
def rot2(v, a):
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def norm2(v):
    L = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / L, v[1] / L)


def add(p, v, k=1.0):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


# ------------------------------------------------------------------ kanatlar
def wing_dirs(s, fold, sweep=0.35):
    """Yan görünüş kanat ekseni (yüz sağa, arka -x). s: -1 tam yukarı .. 0 geriye / izleyiciye .. 1 tam aşağı.
    Döner: kol, ön kol, el doğrultuları ve izdüşüm boyu (orta vuruşta kısa)."""
    d0 = norm2((-(sweep + 0.25 * fold), s * 1.25))
    ext = 0.34 + 0.66 * min(1.0, abs(s)) ** 0.8
    sg = -1.0 if s <= 0 else 1.0
    d1 = rot2(d0, sg * fold * 0.75)
    d2 = rot2(d1, sg * fold * 1.25)
    return d0, d1, d2, ext


def _trail(d, lag):
    """Tüy doğrultusu: geriye (arka kenar), vuruşun tersine gecikmeli; kemiğe dik bileşen ağır basar."""
    t = (-1.0, 0.45 * lag)
    dot = t[0] * d[0] + t[1] * d[1]
    t = (t[0] - 0.65 * dot * d[0], t[1] - 0.65 * dot * d[1])
    return norm2(t)


def feather_wing(cv, S, s, fold=0.0, spread=0.6, L=24.0, chord=9.0, lag=0.0, mats=None, z=0.0, near=True,
                 sweep=0.35, seed=0, ph=0.0, style='feather', glow=None, n_pri=5):
    """Tüylü kanat (Ayaz Çoru / Demir Gaga / Kurgan Ruhu). S omuz (dünya, yerel). lag: +1 aşağı vuruş (tüyler yukarı
    gecikir), -1 yukarı vuruş. mats = (örtü tüyü, uçuş tüyü, koyu ayrım rengi). Döner: {'tip', 'wrist', 'elbow'}."""
    cov, fea, sep = mats
    d0, d1, d2, ext = wing_dirs(s, fold, sweep)
    E = add(S, d0, L * 0.30 * ext)
    Wr = add(E, d1, L * 0.30 * ext)
    T = add(Wr, d2, L * 0.40 * ext * (1.0 - 0.35 * fold))
    tr0 = _trail(d0, lag)
    tr1 = _trail(d1, lag)
    tr2 = _trail(d2, lag)
    rng = np.random.default_rng(seed)
    cl = chord * (1.0 - 0.25 * fold)
    # ---- birincil uçuş tüyleri (el): tek tek, uçta "parmak" gibi ayrılır
    pri = []
    for i in range(n_pri):
        u = i / max(1, n_pri - 1)          # 0 bilek .. 1 uç
        root = lerp2(Wr, T, 0.15 + 0.8 * u)
        w = 0.25 + 0.6 * u
        dd = norm2((tr2[0] * (1 - w) + d2[0] * w, tr2[1] * (1 - w) + d2[1] * w))
        dd = rot2(dd, (u - 0.5) * spread * 0.5 * (-1 if s <= 0 else 1))
        ln = cl * (1.05 + 0.55 * u) * (1.0 + 0.15 * spread) * (0.8 + 0.2 * ext)
        flut = math.sin(ph + i * 0.9) * 0.08 * (0.3 + spread)
        dd = rot2(dd, flut)
        tip = add(root, dd, ln)
        mid = add(lerp2(root, tip, 0.5), (-dd[1], dd[0]), 0.35 * lag * (-1 if s > 0 else 1))
        wbase = cl * 0.28 * (1.0 - 0.3 * u)
        if style == 'ice':
            path = cv.blob([add(root, (-dd[1], dd[0]), wbase * 0.5), mid, (tip[0], tip[1], 0.0), add(root, (dd[1], -dd[0]), wbase * 0.5)])
        else:
            path = ik.taper_path([cv.W(root), cv.W(mid), cv.W(tip)], cv.u(wbase), prof=lambda x: max(0.12, max(0.0, 1 - x) ** 0.5 * min(1.0, x * 6 + 0.4)))
        pri.append((path, root, tip))
    for k, (path, root, tip) in enumerate(pri[::-1]):
        cv.shape(path, fea, z=z + 0.01 * k, sd=0.6, hi=0.15 if near else 0.0, ol=0.75,
                 details=[('stroke', [lerp2(root, tip, 0.1), lerp2(root, tip, 0.85)], 0.7, sep, (0.2, 0.7))], glow=glow)
    # ---- ikincil tüyler (ön kol): taraklı arka kenarlı tek blok
    edge = []
    nsec = 6
    for i in range(nsec + 1):
        u = i / nsec
        root = lerp2(E, Wr, u) if u < 1 else Wr
        tr = norm2(lerp2(tr1, tr2, u * 0.6))
        ln = cl * (0.95 - 0.1 * u) * (0.75 + 0.25 * ext)
        q = add(root, tr, ln + rng.uniform(-0.4, 0.4))
        edge.append((q[0], q[1], 0.0 if style != 'ice' else 0.0))
        if i < nsec:
            q2 = add(lerp2(root, lerp2(E, Wr, (i + 1) / nsec), 0.5), tr, ln * 0.82)
            edge.append(q2)
    # üçüncül (omuza yakın) kısa tüyler
    ter = add(lerp2(S, E, 0.5), tr0, cl * 0.62)
    sec_pts = [S, E, Wr] + edge[::-1] + [ter]
    det = []
    for i in range(1, nsec):
        u = i / nsec
        r_ = lerp2(E, Wr, u)
        tr = norm2(lerp2(tr1, tr2, u * 0.6))
        det.append(('ink', [add(r_, tr, cl * 0.25), add(r_, tr, cl * 0.85)], 0.8, (0.2, 0.6)))
    cv.shape(cv.blob(sec_pts), fea, z=z + 0.1, sd=1.0, hi=0.2 if near else 0.0, ol=0.85, details=det, glow=glow)
    # ---- örtü tüyleri: kemik boyunca kalın ön kenar + pul pul iki sıra
    lead_n = (-tr1[0], -tr1[1])
    cpts = [add(S, lead_n, 1.6), add(E, lead_n, 1.5), add(Wr, lead_n, 1.1), add(T, lead_n, 0.2),
            (T[0], T[1], 0.0), add(lerp2(Wr, T, 0.55), tr2, cl * 0.42), add(Wr, tr2, cl * 0.5),
            add(lerp2(E, Wr, 0.5), tr1, cl * 0.52), add(E, tr1, cl * 0.5), add(lerp2(S, E, 0.5), tr0, cl * 0.45), add(S, tr0, 2.0)]
    cdet = []
    for row in (0.22, 0.4):
        sc = []
        for i in range(6):
            u = i / 5
            r_ = lerp2(S, Wr, u) if u < 1 else Wr
            tr = norm2(lerp2(tr0, tr1, u))
            sc.append(add(r_, tr, cl * row * (1.0 if u < 0.85 else 0.8)))
        cdet.append(('ink', sc, 0.75, (0.2, 0.2)))
    cdet.append(('stroke', [add(S, lead_n, 0.8), add(E, lead_n, 0.8), add(Wr, lead_n, 0.5)], 1.0, cov.hi, (0.2, 0.5)))
    cv.shape(cv.blob(cpts), cov, z=z + 0.2, sd=1.1, hi=0.45 if near else 0.0, ol=0.9, details=cdet, fur=0.4 if style == 'feather' else 0.0, glow=glow)
    return {'tip': T, 'wrist': Wr, 'elbow': E, 'trail': tr2}


def bat_wing(cv, S, s, fold=0.0, L=24.0, lag=0.0, mats=None, z=0.0, near=True, sweep=0.3, flank=None, seed=0, ph=0.0):
    """Zar kanat (Kan Çoru): kol + dört uzun parmak, aralarında içe kavisli zar; yukarı vuruşta parmaklar toplanır,
    zar buruşur. flank: zarın gövdeye bağlandığı nokta."""
    mem, bone, vein = mats
    d0, d1, d2, ext = wing_dirs(s, fold, sweep)
    E = add(S, d0, L * 0.2 * ext)
    Wr = add(E, d1, L * 0.26 * ext)
    tr2 = _trail(d2, lag)
    flank = flank or add(S, (-0.4, 1.0), 9.0)
    # parmak yelpazesi: önde el doğrultusunun biraz önü, arkada arka kenarın da ötesi (zar geniş açılır);
    # katlanınca yelpaze kapanır, parmaklar kısalır (yukarı vuruşta zar buruşur)
    a0 = math.atan2(d2[1], d2[0])
    a1 = math.atan2(tr2[1], tr2[0])
    da = (a1 - a0 + math.pi) % math.tau - math.pi
    sg = 1.0 if da >= 0 else -1.0
    fanr = (abs(da) + 0.55) * (1.0 - 0.78 * fold)
    tips = []
    for j in range(4):
        u = j / 3.0
        a = a0 - sg * 0.12 * (1.0 - fold) + sg * fanr * u + math.sin(ph + j) * 0.05
        ln = L * (0.56 - 0.05 * j) * (0.5 + 0.5 * ext) * (1.0 - 0.42 * fold)
        tips.append(add(Wr, (math.cos(a), math.sin(a)), ln))
    pts = [S, E, Wr, (tips[0][0], tips[0][1], 0.0)]
    for j in range(1, 4):
        a, b = tips[j - 1], tips[j]
        m = lerp2(a, b, 0.5)
        m = lerp2(m, Wr, 0.24 + 0.1 * fold)
        pts += [m, (b[0], b[1], 0.0)]
    m = lerp2(tips[-1], flank, 0.5)
    m = lerp2(m, lerp2(Wr, S, 0.5), 0.28)
    pts += [m, (flank[0], flank[1], 0.0)]
    det = [('ink', [Wr, lerp2(Wr, t, 0.55), t], 1.6 if near else 1.2, (0.05, 0.8)) for t in tips]
    det += [('stroke', [lerp2(Wr, t, 0.2), lerp2(Wr, t, 0.7)], 0.7, vein, (0.2, 0.6)) for t in tips[1:3]]
    # zar kırışıkları (katlanınca)
    if fold > 0.2:
        for j in range(3):
            a = lerp2(tips[j], tips[j + 1], 0.5)
            det.append(('ink', [lerp2(Wr, a, 0.3), lerp2(Wr, a, 0.75)], 0.6 + fold * 0.5, (0.3, 0.3)))
    cv.shape(cv.blob(pts), mem, z=z, sd=1.6, hi=0.0, details=det, ol=0.9)
    # kol kemiği + başparmak pençesi
    cv.shape(cv.limb([S, E, Wr], [1.0, 0.8, 0.65]), bone, z=z + 0.1, sd=0.5, hi=0.25 if near else 0.0, ol=0.8)
    th = add(Wr, norm2(lerp2(d1, (-d1[1], d1[0]), 0.5)), 2.2)
    cv.shape(cv.blob([add(Wr, (0.5, 0.3)), (th[0], th[1], 0.0), add(Wr, (-0.5, -0.3))]), bone, z=z + 0.12, sd=0.3, ol=0.7)
    return {'tip': tips[0], 'wrist': Wr, 'elbow': E, 'tips': tips}


# ------------------------------------------------------------------ efektler
def speed_lines(cv, c, d, n=5, L=14.0, spread=8.0, w=1.6, col=INK, alpha=0.55, z=-30.0, seed=0, glow=None):
    """Hız çizgileri: c merkezinin arkasında (d hareket yönü), incelen kuru fırça darbeleri."""
    rng = np.random.default_rng(seed)
    d = norm2(d)
    nx, ny = -d[1], d[0]
    for i in range(n):
        o = (i / max(1, n - 1) - 0.5) * spread + rng.uniform(-0.6, 0.6)
        ln = L * rng.uniform(0.6, 1.15)
        st = add(add(c, (nx, ny), o), d, -rng.uniform(1.0, 4.0))
        en = add(st, d, -ln)
        cv.stroke([st, lerp2(st, en, 0.5), en], w * rng.uniform(0.7, 1.3), z=z, col=col, taper=(0.05, 0.95), alpha=alpha, glow=glow)


def flecks(cv, c, n, r0, r1, mat, z, seed=0, s0=0.4, s1=1.1, drift=(0.0, -1.0), dk=0.0, glow=None, alpha=1.0):
    """Mürekkep / kül zerreleri: c çevresinde saçılmış küçük yırtık lekeler (dk: sürüklenme miktarı, dünya)."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        a = rng.uniform(0, math.tau)
        ra = rng.uniform(r0, r1)
        q = (c[0] + math.cos(a) * ra + drift[0] * dk * rng.uniform(0.5, 1.2), c[1] + math.sin(a) * ra * 0.8 + drift[1] * dk * rng.uniform(0.5, 1.2))
        sz = rng.uniform(s0, s1)
        rr = rng.uniform(0, math.tau)
        pts = [(q[0] + math.cos(rr) * sz * 1.4, q[1] + math.sin(rr) * sz * 1.4, 0.0), (q[0] + math.cos(rr + 2.0) * sz * 0.8, q[1] + math.sin(rr + 2.0) * sz * 0.8),
               (q[0] + math.cos(rr + 3.4) * sz, q[1] + math.sin(rr + 3.4) * sz, 0.0), (q[0] + math.cos(rr + 4.8) * sz * 0.7, q[1] + math.sin(rr + 4.8) * sz * 0.7)]
        if isinstance(mat, Ink):
            cv.shape(cv.blob(pts), mat, z=z + i * 0.001, sd=0.3, ol=0.6, glow=glow)
        else:
            cv.fill(cv.blob(pts), mat, z=z + i * 0.001, glow=glow, alpha=alpha)


def armor_aura(cv, c, r, k, z=-40.0, seed=0, spikes=9):
    """"!!" zırhlı hazırlık halesi: turuncu bulanık ışıma + dışa sivrilen kor çizgiler (yalnızca zırhlı pozlarda)."""
    if k <= 0:
        return
    yk.glow_soft(cv, c, r * (0.9 + 0.2 * k), ARMOR, z=z, blur=0.55, alpha=0.55 * k)
    rng = np.random.default_rng(seed)
    for i in range(spikes):
        a = i / spikes * math.tau + rng.uniform(-0.2, 0.2)
        r0 = r * rng.uniform(0.55, 0.75)
        r1 = r0 + r * rng.uniform(0.25, 0.45) * k
        p0 = (c[0] + math.cos(a) * r0, c[1] + math.sin(a) * r0)
        p1 = (c[0] + math.cos(a) * r1, c[1] + math.sin(a) * r1)
        cv.stroke([p0, p1], 1.6 * k + 0.4, z=z + 0.1, col=ARMOR_HOT, taper=(0.1, 0.95), glow=ARMOR, alpha=0.9)


_NOISE = {}


def _noise(h, w, seed, hd):
    key = (h, w, seed, hd)
    if key not in _NOISE:
        bh, bw = max(8, h // hd), max(8, w // hd)
        rng = np.random.default_rng(seed)
        n = ndimage.gaussian_filter(rng.random((bh, bw)), bh / 40.0) * 0.65 + ndimage.gaussian_filter(rng.random((bh, bw)), bh / 110.0) * 0.35
        n = (n - n.min()) / max(1e-6, n.max() - n.min())
        if hd > 1:
            n = ndimage.zoom(n, (h / bh, w / bw), order=1)[:h, :w]
        _NOISE[key] = n
    return _NOISE[key]


def dissolve(rgba, em, k, seed=0, hd=1, grad=(0.0, -0.6), edge=0.07, hot=(1.0, 0.5, 0.15), hot_a=1.0, center=None):
    """Çözülme (ölüm / doğuş / ışınlanma): k 0 -> bütün, 1 -> tamamen dağılmış. grad: dağılmanın yönü (gövdenin o yanı
    önce dağılır, ör. (0, -0.6) = alttan yukarı değil, üstten aşağı kalır). Kenar şeridi ışıma sayfasına `hot` yazılır."""
    if k <= 0:
        return rgba, em
    h, w = rgba.shape[:2]
    n = _noise(h, w, seed, hd)
    a = rgba[..., 3]
    ys, xs = np.nonzero(a > 0.05)
    if len(ys) == 0:
        return rgba, em
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    yy = (np.arange(h)[:, None] - y0) / max(1, y1 - y0)
    xx = (np.arange(w)[None, :] - x0) / max(1, x1 - x0)
    g = n * 0.62 + (yy - 0.5) * grad[1] * -1.0 * 0.38 + (xx - 0.5) * grad[0] * -1.0 * 0.38 + 0.19
    # sıra eşitleme: gövde piksellerinde g düzgün dağılsın (k = dağılan alan oranı, doğrusal)
    m = a > 0.02
    if m.sum() > 16:
        gv = g[m]
        order = np.argsort(gv)
        rk = np.empty_like(gv)
        rk[order] = np.linspace(0.0, 1.0, len(gv))
        g2 = np.full_like(g, 1.0)
        g2[m] = rk
        g = g2
    thr = k * (1.0 + edge * 2.0) - edge
    keep = np.clip((g - thr) / edge, 0.0, 1.0)
    band = np.clip(1.0 - np.abs(g - thr - edge * 0.5) / (edge * 1.4), 0.0, 1.0) * (a > 0.02)
    out = rgba.copy()
    out[..., 3] = a * keep
    # kenar: mürekkep koyulaşır (yanık kâğıt)
    dark = band * keep
    out[..., :3] = out[..., :3] * (1.0 - 0.6 * dark[..., None]) + np.array(INK) * 0.6 * dark[..., None]
    em2 = em.copy()
    if hot is not None and hot_a > 0:
        b = (band * a * hot_a)[..., None]
        em2[..., :3] = em2[..., :3] * keep[..., None] + np.array(hot) * b
        em2[..., 3] = np.clip(em2[..., 3] * keep + b[..., 0], 0, 1)
    else:
        em2 = em2 * keep[..., None]
    return out, em2


def fade(rgba, em, k):
    out = rgba.copy()
    out[..., 3] *= k
    return out, em * k


def to_world(cv, p):
    """Yerel (dönüşümlü) noktayı sprite dünya koordinatına çevir (çapa: 'mouth', 'hand')."""
    x, y = p[0], p[1]
    for f in reversed(cv.xf):
        x, y = f((x, y))
    return (x, y)


def flap(t, down=0.45, top=-1.0, bot=0.95, fold_max=0.9, bob_amp=1.8):
    """Kanat çırpış döngüsü (t 0..1): aşağı vuruş (kanat açık, tüyler yukarı gecikir, gövde yükselir) ve yukarı vuruş
    (bilekten katlanır, uç tüyler ayrılır, gövde iner). Döner: kanat alanları + gövde inişi (bob, + = aşağı)."""
    t = t % 1.0
    if t < down:
        u = t / down
        s = top + (bot - top) * ease(u, 'io')
        fold = 0.05
        lag = math.sin(math.pi * u)
        spread = 0.3 + 0.35 * u
    else:
        u = (t - down) / (1.0 - down)
        s = bot + (top - bot) * ease(u, 'io')
        fold = fold_max * math.sin(math.pi * min(1.0, u * 1.1)) ** 0.8
        lag = -math.sin(math.pi * u)
        spread = 0.45 + 0.55 * math.sin(math.pi * u)
    bob = bob_amp * math.cos(math.tau * (t - 0.08))
    return dict(ws=s, wf=fold, wl=lag, wsp=spread), bob


def over(top, top_em, bot, bot_em):
    """Düz alfalı iki kareyi üst üste koy (top bot'un üstünde); ışıma sayfaları (önceden çarpılmış) toplanır."""
    ta, ba = top[..., 3:4], bot[..., 3:4]
    oa = ta + ba * (1.0 - ta)
    rgb = np.where(oa > 1e-5, (top[..., :3] * ta + bot[..., :3] * ba * (1.0 - ta)) / np.maximum(oa, 1e-5), 0.0)
    out = np.concatenate([rgb, oa], -1)
    em = np.clip(top_em + bot_em * (1.0 - ta), 0.0, 1.0)
    return out, em
