"""Türk mitolojisi silah, kalkan ve teçhizat sprite'ları — v14: hacimli, ağırlıklı yeniden çizim.

Hücre 128x80 doku pikseli ("texel": 2 → oyun 1/2 ölçekle çizer, dünya boyu eski 64x40 ile aynı; Data.wscale()).
Silahlar +x yönüne bakar, kabza/tutuş noktası pivotta (32,40); kalkan ve aygıtlar hücre ortasında (64,40).
Satırlar ORDER sırasındaki eşyalar, sütunlar data/items.json malzemeleri.

Gölgelendirme: volume.VCanvas (5 ton, sol-üst ışık, ortam kapanması, temas gölgesi, kenar ışığı, yalnızca gölge
tarafında koyu kontur) + silaha özgü geometri:
  * bıçak: düz gövde + eğik pah yüzeyleri (sırt pahı ışığa, ağız pahı gölgeye bakar), oluk (fuller: koyu çizgi +
    altında ışık çizgisi), ağız boyunca 1 px parlama çizgisi, uca doğru incelme ve kavis,
  * kabza: deri/ip sargı bantları (çapraz desen), bilezik, hacimli topuz; siper ve balçak gerçek silindir/küre,
  * sap: ahşap damarı; demir/tunç: çekiç çukurları; kemik: çatlak; altın: kakma; yeşim: yarı saydam ışık bandı;
    kara taş: keskin parlama; od taşı / ayaz / gök demiri / ruh: ışıyan damar, kırağı, öz (_e katmanı),
  * normal haritası düzleştirilmemiş hacim normalinden (pah, yuvarlak kabza, kubbeli göbek).
"""
import json
import math
import os
import numpy as np
from raster import Canvas, Mat, ramp, hx, band
from volume import VCanvas, _hash
from materials import M

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ITEMS = json.load(open(os.path.join(ROOT, 'data', 'items.json'), encoding='utf-8'))
MATS = {m['id']: m for m in ITEMS['materials']}

TEX = 2                      # doku pikseli / dünya birimi
CELL = (128, 80)
PIVOT = (32, 40)             # kabza pivotu (doku px)
CPIVOT = (64, 40)            # ortalanmış eşyalar


class WCanvas(VCanvas):
    """Silah tuvali: tam yuvarlak kapsüller, pah genişliği birebir (VCanvas.poly pahı 1.6 kat şişirir), silah ışığı."""
    FLAT = 0.0
    zscale = 1.0
    shade_kw = dict(light=(-0.5, -0.75, 0.55), rim=(0.62, -0.78), rim_col='#d6ecff', rim_amt=0.34,
                    ao=0.85, cast=0.5, form=0.26, grad=0.16, bands=(-0.26, 0.12, 0.60, 0.90),
                    cleanup=1, rim_th=0.70, lit_outline=0.3)

    def poly(self, pts, mat, z=0.0, bevel=1.2, height=1.5, tone=0.0, paint=None, tilt=(0.0, 0.0)):
        self._pc += 1
        self._cur = (1.0, 1.0)
        Canvas.poly(self, pts, mat, z=z, bevel=bevel, height=height, tone=tone, paint=paint, tilt=tilt)
        self._cur = None

    def tube(self, pts, r0, r1, mat, z=0.0, paint=None, tone=0.0):
        """Çoklu çizgi boyunca tek parça yuvarlak boru (yay kolu, kırbaç, ip, boynuz): eklem yerinde tümsek yok.
        Yarıçap r0 -> r1 yol boyunca doğrusal; paint için lu = yol oranı, lv = işaretli yan koordinat [-1, 1]."""
        P = np.array(pts, float)
        rm = max(r0, r1)
        g = self._grid(P[:, 0].min() - rm, P[:, 1].min() - rm, P[:, 0].max() + rm, P[:, 1].max() + rm)
        if g is None:
            return
        sl, px, py = g
        seg = np.hypot(P[1:, 0] - P[:-1, 0], P[1:, 1] - P[:-1, 1]) + 1e-9
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        tot = cum[-1]
        best = np.full(px.shape, 1e9)
        bt = np.zeros(px.shape); qx = np.zeros(px.shape); qy = np.zeros(px.shape); side = np.zeros(px.shape)
        for i in range(len(P) - 1):
            a, b = P[i], P[i + 1]
            sx, sy = b[0] - a[0], b[1] - a[1]
            t = np.clip(((px - a[0]) * sx + (py - a[1]) * sy) / (seg[i] * seg[i]), 0, 1)
            cx = a[0] + t * sx; cy = a[1] + t * sy
            d = np.hypot(px - cx, py - cy)
            m = d < best
            best[m] = d[m]; qx[m] = cx[m]; qy[m] = cy[m]
            bt[m] = ((cum[i] + t * seg[i]) / tot)[m]
            side[m] = (((px - cx) * (-sy) + (py - cy) * sx) / seg[i])[m]
        r = r0 + (r1 - r0) * bt
        inside = best <= r
        rr = np.maximum(r, 1e-3)
        h = np.sqrt(np.clip(r * r - best * best, 0, None))
        nx = (px - qx) / rr; ny = (py - qy) / rr; nz = h / rr
        self._pc += 1
        self._cur = (tot, rm)
        self._write(sl, inside, z + h, nx, ny, nz, mat, tone, paint, bt, side / rr, px, py)
        self._cur = None


# ------------------------------------------------------------ desen (paint) yardımcıları: mutlak koordinat
def near(pts, w, lo=0.0, hi=1.0, dy=0.0, dx=0.0):
    """pts çoklu çizgisine w px'den yakın pikseller; lo..hi: yol boyunca oran aralığı."""
    P = np.array(pts, float) + np.array([dx, dy])
    seg = np.hypot(P[1:, 0] - P[:-1, 0], P[1:, 1] - P[:-1, 1]) + 1e-9
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    tot = cum[-1]

    def f(lu, lv, px, py):
        best = np.full(px.shape, 1e9)
        bt = np.zeros(px.shape)
        for i in range(len(P) - 1):
            a, b = P[i], P[i + 1]
            sx, sy = b[0] - a[0], b[1] - a[1]
            L2 = sx * sx + sy * sy + 1e-9
            t = np.clip(((px - a[0]) * sx + (py - a[1]) * sy) / L2, 0, 1)
            d = np.hypot(px - (a[0] + t * sx), py - (a[1] + t * sy))
            m = d < best
            best[m] = d[m]
            bt[m] = ((cum[i] + t * seg[i]) / tot)[m]
        return (best < w) & (bt >= lo) & (bt <= hi)
    return f


def diag(period=4.2, width=1.4, slope=0.75, off=0.0):
    """Çapraz sargı bandı (deri/ip)."""
    def f(lu, lv, px, py):
        return ((px + py * slope + off) % period) < width
    return f


def grain(period=3.1, width=0.75, wob=0.45, seed=0.0, axis='x'):
    """Ahşap damarı: sap ekseni boyunca hafif dalgalı ince çizgiler."""
    def f(lu, lv, px, py):
        if axis == 'x':
            v = py + wob * np.sin(px * 0.31 + seed) + 0.2 * np.sin(px * 0.07 + seed * 2)
        else:
            v = px + wob * np.sin(py * 0.31 + seed)
        return (v % period) < width
    return f


def dimples(seed=1.0, cell=5.0, dens=0.32, which='hi'):
    """Çekiç çukurları: seyrek 2x2 çukur — sol-üst piksel koyu (which='hi' = gölge), sağ-alt açık ('lo')."""
    def f(lu, lv, px, py):
        cx = np.floor(px / cell); cy = np.floor(py / cell)
        h = _hash(cx, cy, seed)
        ox = np.floor(px - cx * cell); oy = np.floor(py - cy * cell)
        if which == 'hi':
            return (h < dens) & (ox == 1) & (oy == 1)
        return (h < dens) & (ox == 2) & (oy == 2)
    return f


def ring(cx, cy, r0, r1, ry=None):
    def f(lu, lv, px, py):
        d = np.hypot(px - cx, (py - cy) * (1.0 if ry is None else 1.0 / ry))
        return (d >= r0) & (d < r1)
    return f


def sectors(cx, cy, n, phase=0.0, duty=0.5):
    def f(lu, lv, px, py):
        a = (np.arctan2(py - cy, px - cx) + phase) / math.tau * n
        return (a % 1.0) < duty
    return f


def disc(cx, cy, r):
    def f(lu, lv, px, py):
        return np.hypot(px - cx, py - cy) < r
    return f


def box(x0, y0, x1, y1):
    def f(lu, lv, px, py):
        return (px >= x0) & (px < x1) & (py >= y0) & (py < y1)
    return f


def tri_row(y0, h, period, x0=0.0, up=True):
    """Kilim üçgen dizisi: y0 tabanında h yüksekliğinde testere dişleri."""
    def f(lu, lv, px, py):
        u = ((px - x0) % period) / period
        tri = 1.0 - np.abs(u * 2 - 1)
        d = (y0 - py) if up else (py - y0)
        return (d >= 0) & (d < tri * h)
    return f


def lerp_pts(a, b, k):
    return [(ax + (bx - ax) * k, ay + (by - ay) * k) for (ax, ay), (bx, by) in zip(a, b)]


def shift_pts(pts, dx=0.0, dy=0.0):
    return [(x + dx, y + dy) for x, y in pts]


def wave_pts(p0, p1, amp, n=4, k=12, phase=0.0):
    """İki nokta arasında dalgalı çoklu çizgi (damar, yılan, kırbaç)."""
    out = []
    for i in range(k + 1):
        t = i / k
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        nx, ny = -(p1[1] - p0[1]), (p1[0] - p0[0])
        L = math.hypot(nx, ny) + 1e-9
        s = math.sin(t * n * math.pi + phase) * amp * math.sin(t * math.pi) ** 0.5
        out.append((x + nx / L * s, y + ny / L * s))
    return out


# ------------------------------------------------------------ malzemeler
def _fl(col, emissive=0.0, outline=None):
    return Mat([hx(col)] * 5, flat=True, emissive=emissive, outline=outline)


def _shifted(m, k, **kw):
    """Rampayı k basamak kaydırılmış türev (k<0 koyu, k>0 açık)."""
    r = m.ramp
    idx = [min(4, max(0, i + k)) for i in range(5)]
    return Mat([r[i] for i in idx], spec=kw.get('spec', m.spec), emissive=kw.get('emissive', m.emissive), outline=m.outline)


BLADE = {
    'demir':      dict(mat='w_iron', glint='#f2f5fa', acc='w_brass', gem='w_gem_garnet', pat='dimple'),
    'tunc':       dict(mat='w_bronze', glint='#fff1c4', acc='w_iron', gem='w_gem_turq', pat='dimple'),
    'gumus':      dict(mat='w_silver', glint='#ffffff', acc='w_gold', gem='w_gem_sapphire', pat='clean'),
    'altin':      dict(mat='w_gold', glint='#fffbe0', acc='w_dark_iron', gem='w_gem_ruby', pat='ornament'),
    'kemik':      dict(mat='w_ivory', glint='#fffdf5', acc='w_bronze', gem='w_gem_amber', pat='crack'),
    'yesim':      dict(mat='w_jade', glint='#e8fff0', acc='w_gold', gem='w_gem_kut', pat='jade', em='w_jade_lit'),
    'kara_tas':   dict(mat='w_obsidian', glint='#ece4ff', acc='w_silver', gem='w_gem_violet', pat='obsidian'),
    'od_tasi':    dict(mat='w_ember_stone', glint='#ffd9a0', acc='w_dark_iron', gem='w_gem_amber', pat='ember', em='w_ember'),
    'ayaz':       dict(mat='w_frost', glint='#ffffff', acc='w_silver', gem='w_gem_ice', pat='frost', em='w_frost_glow'),
    'gok_demiri': dict(mat='w_sky_iron', glint='#eeeaff', acc='w_gold', gem='w_gem_sky', pat='sky', em='w_sky_vein'),
    'ruh':        dict(mat='w_spirit', glint='#ffffff', acc='w_ivory', gem='w_gem_kut', pat='spirit', em='w_spirit_core'),
}

_CACHE = {}


def mats_for(mid):
    if mid in _CACHE:
        return _CACHE[mid]
    d = BLADE[mid]
    B = M[d['mat']]
    glow = MATS[mid]['glow']
    em = M[d['em']] if 'em' in d else None
    mm = {
        'id': mid, 'pat': d['pat'], 'glow': glow,
        'b': B, 'bd': _shifted(B, -1), 'bl': _shifted(B, 1),
        'glint': _fl(d['glint'], emissive=(0.6 if mid in ('ruh', 'ayaz') else 0.0)),
        'A': M[d['acc']], 'Ad': _shifted(M[d['acc']], -1), 'gem': M[d['gem']], 'em': em,
        'G': M['w_leather'], 'Gd': M['w_leather_d'], 'cord': M['w_cord'], 'cordd': M['w_cord_d'],
        'W': M['w_ash'], 'Wd': M['w_ash_d'], 'bone': M['w_ivory'], 'felt': M['w_felt'], 'turq': M['turq'],
        'white': M['w_white'], 'iron': M['w_iron'], 'gold': M['w_gold'], 'string': M['w_string'],
        'horn': M['w_horn'], 'sinew': M['w_sinew'], 'kut': M['w_gem_kut'], 'ember': M['w_ember'], 'black': M['black'],
    }
    _CACHE[mid] = mm
    return mm


# ------------------------------------------------------------ malzeme desenleri (bıçak / başlık yüzeyi)
def surface_paint(mm, top, bot, mid, seed=1.0, x0=None):
    """Malzemeye özgü yüzey deseni: top/bot/mid bıçak kenar ve orta çizgileri (başlıklarda yaklaşık kutu)."""
    pat = mm['pat']
    out = []
    L = max(1.0, mid[-1][0] - mid[0][0])
    xs = np.array([p[0] for p in mid]); ys = np.array([p[1] for p in mid])
    if pat == 'dimple' or pat == 'sky':
        out += [(dimples(seed, 5.0, 0.30, 'hi'), mm['bd']), (dimples(seed, 5.0, 0.30, 'lo'), mm['bl'])]
    if pat == 'crack':
        a = lerp_pts(top, bot, 0.35); b = lerp_pts(top, bot, 0.7)
        n = len(mid)
        i0, i1 = int(n * 0.22), int(n * 0.58)
        c1 = [a[i0], (a[i0][0] + 3, a[i0][1] + 1.6), (a[i0][0] + 5, a[i0][1] + 1.0), (a[i0][0] + 8.5, a[i0][1] + 3.4), (a[i0][0] + 10, a[i0][1] + 3.0)]
        c2 = [b[i1], (b[i1][0] + 2.5, b[i1][1] - 1.5), (b[i1][0] + 5.5, b[i1][1] - 1.2), (b[i1][0] + 7, b[i1][1] - 3.0)]
        out += [(near(c1, 0.55), mm['bd']), (near(c2, 0.55), mm['bd']), (near(c1, 0.55, dy=1.0, dx=0.4), mm['bl'])]
    if pat == 'ornament':
        def orn(lu, lv, px, py):
            yc = np.interp(px, xs, ys)
            u = (px - xs[0]) % 8.0
            return ((np.abs(u - 4) * 0.8 + np.abs(py - yc) * 1.3) < 2.3) & (px > xs[0] + 6) & (px < xs[0] + L * 0.72)

        def orn_in(lu, lv, px, py):
            yc = np.interp(px, xs, ys)
            u = (px - xs[0]) % 8.0
            return ((np.abs(u - 4) * 0.8 + np.abs(py - yc) * 1.3) < 0.9) & (px > xs[0] + 6) & (px < xs[0] + L * 0.72)
        out += [(orn, mm['bd']), (orn_in, mm['bl'])]
    if pat == 'jade':
        bandl = lerp_pts(top, bot, 0.64)
        out += [(near(bandl, 1.05, 0.04, 0.93), mm['em']), (dimples(seed + 3, 7.0, 0.18, 'lo'), mm['bl'])]
    if pat == 'obsidian':
        n = len(mid)
        for k, t in enumerate((0.3, 0.55, 0.78)):
            i = int(n * t)
            p = lerp_pts(top, bot, 0.3)[i]
            arc = [(p[0] - 3, p[1] - 0.8), (p[0] - 1, p[1] + 0.6), (p[0] + 1.5, p[1] + 1.4), (p[0] + 4, p[1] + 1.0)]
            out += [(near(arc, 0.5), mm['bl'])]
    if pat == 'ember':
        v1 = wave_pts(mid[1], mid[-2], 1.8, n=4, k=14, phase=0.6)
        v2 = wave_pts(lerp_pts(top, bot, 0.72)[2], lerp_pts(top, bot, 0.3)[-3], 1.4, n=3, k=10, phase=2.0)
        out += [(near(v1, 0.6, 0.02, 0.9), mm['em']), (near(v2, 0.5, 0.1, 0.85), mm['em']),
                (dimples(seed + 7, 6.0, 0.22, 'lo'), mm['em'])]
    if pat == 'frost':
        out += [(near(top, 0.8, 0.05, 0.97, dy=0.7), mm['em']), (dimples(seed + 11, 6.0, 0.25, 'lo'), mm['em']),
                (dimples(seed + 11, 6.0, 0.25, 'hi'), mm['bl'])]
    if pat == 'sky':
        v1 = wave_pts(mid[1], mid[-2], 1.6, n=5, k=16, phase=1.2)
        out += [(near(v1, 0.55, 0.05, 0.88), mm['em'])]
    if pat == 'spirit':
        out += [(near(mid, 0.7, 0.06, 0.9, dy=-0.4), mm['em']), (near(lerp_pts(top, bot, 0.75), 0.5, 0.2, 0.8), mm['em']),
                (dimples(seed + 5, 6.0, 0.2, 'lo'), mm['em'])]
    return out


def head_paint(mm, x0, y0, x1, y1, seed=2.0):
    """Dikdörtgen başlık (çekiç, balta, topuz) için yüzey deseni."""
    n = 12
    xs = [x0 + (x1 - x0) * i / n for i in range(n + 1)]
    top = [(x, y0) for x in xs]; bot = [(x, y1) for x in xs]; mid = [(x, (y0 + y1) / 2) for x in xs]
    return surface_paint(mm, top, bot, mid, seed)


# ------------------------------------------------------------ parçalar
def blade_pts(x0, L, w, kind='double', curve=0.0, yelman=0.0, sway=0.0, n=18, tip_len=0.18, wave=0.0):
    """Bıçak profili: (üst kenar, alt kenar, orta) nokta listeleri; +x yönü. kind 'single': sırt üstte, ağız altta.
    curve: ucun yukarı kalkması (px); sway: ortada aşağı sarkma (yatağan); yelman: uca yakın sırt genişlemesi."""
    top, bot, mid = [], [], []
    for i in range(n + 1):
        t = i / n
        x = x0 + L * t
        yc = -curve * t * t + sway * math.sin(t * math.pi)
        if wave:
            yc += wave * math.sin(t * 5.5 * math.pi) * (1 - t) ** 0.3
        if kind == 'double':
            hw = w * 0.5 * (1 - 0.22 * t)
            if t > 1 - tip_len:
                hw *= (1 - t) / tip_len
            top.append((x, yc - hw)); bot.append((x, yc + hw)); mid.append((x, yc))
        else:
            ht = w * 0.42 * (1 - 0.25 * t)
            hb = w * 0.58 * (1 - 0.1 * t)
            if yelman and t > 0.6:
                k = (t - 0.6) / 0.4
                ht += yelman * math.sin(k * math.pi)
            off = 0.0
            if t > 1 - tip_len:
                k = (1 - t) / tip_len
                off = (1 - k) * w * 0.28
                ht *= k; hb *= k
            top.append((x, yc - ht - off)); bot.append((x, yc + hb - off)); mid.append((x, yc + (hb - ht) * 0.2 - off))
    return top, bot, mid


def draw_blade(c, mm, top, bot, mid, kind='double', z=1.0, fuller=True, extra=None, edge_glint=(0.22, 0.96),
               body_h=2.6, tilt_amt=0.75, pat=True, mat=None):
    """Bıçak: gövde (yuvarlatılmış siluet kenarı) + eğik pah yüzeyleri + oluk + ağız parlaması + malzeme deseni."""
    B = mat or mm['b']
    x0 = top[0][0]
    L = top[-1][0] - x0
    ridge = lerp_pts(top, bot, 0.5 if kind == 'double' else 0.6)
    paint = []
    if pat:
        paint += surface_paint(mm, top, bot, mid, seed=1.0 + x0 * 0.01)
    if extra:
        paint += extra
    if fuller:
        fl = lerp_pts(top, bot, 0.5 if kind == 'double' else 0.32)
        a, b = (0.1, 0.70) if kind == 'double' else (0.08, 0.78)
        paint += [(near(fl, 0.5, a, b, dy=1.05), mm['bl']), (near(fl, 0.5, a, b), mm['bd'])]
    # ağız parlaması (sol-üst ışığı yakalayan keskin kenar): alt kenarın 0.9 px içi
    paint += [(near(bot, 0.55, edge_glint[0], edge_glint[1], dy=-0.9), mm['glint'])]
    if kind == 'double':
        paint += [(near(top, 0.5, 0.55, 0.97, dy=0.9), mm['glint'])]
    body = top + bot[::-1]
    c.poly(body, B, z=z, bevel=1.6, height=body_h, paint=paint)
    zf = z + body_h + 0.15
    low = ridge + lerp_pts(bot, ridge, 0.14)[::-1]
    c.poly(low, B, z=zf, bevel=0.01, height=0.0, tilt=(0.0, tilt_amt), paint=paint)
    if kind == 'double':
        hi = lerp_pts(top, ridge, 0.14) + ridge[::-1]
        c.poly(hi, B, z=zf, bevel=0.01, height=0.0, tilt=(0.0, -tilt_amt), paint=paint)
    else:
        # sırt: dar, düz, hafif yukarı bakan şerit
        hi = lerp_pts(top, ridge, 0.14) + lerp_pts(top, ridge, 0.55)[::-1]
        c.poly(hi, B, z=zf, bevel=0.01, height=0.0, tilt=(0.0, -tilt_amt * 0.55), paint=paint)


def grip(c, mm, x0, x1, r=3.4, z=0.0, wrap='leather', y=0.0, ferrule=True, period=4.4):
    """Sargılı kabza: çapraz bant deseni + uçta bilezik."""
    if wrap == 'leather':
        G, Gd = mm['G'], mm['Gd']
    elif wrap == 'cord':
        G, Gd = mm['cord'], mm['cordd']
    elif wrap == 'bone':
        G, Gd = mm['bone'], _shifted(mm['bone'], -1)
    else:
        G, Gd = mm['W'], mm['Wd']
    pnt = [(diag(period, 1.3, 0.8), Gd)] if wrap in ('leather', 'cord') else [(grain(2.8, 0.7, 0.3), Gd)]
    if wrap == 'bone':
        pnt = [(near([(x0 + 2, y - r * 0.6), (x1 - 2, y - r * 0.5)], 0.45), Gd)]
    c.capsule((x0, y), (x1, y), r, r, G, z=z, paint=pnt)
    if ferrule:
        c.capsule((x1 - 1.6, y), (x1, y), r + 0.5, r + 0.5, mm['A'], z=z + 0.4)
        c.capsule((x0, y), (x0 + 1.2, y), r + 0.3, r + 0.3, mm['A'], z=z + 0.3)


def pommel(c, mm, x, r=4.6, style='disc', z=1.0, y=0.0, gem=True):
    A = mm['A']
    if style == 'disc':
        c.ellipse((x, y), r, r, A, z=z, paint=[(ring(x, y, r - 1.8, r - 0.9), mm['Ad'])])
        if gem:
            c.ellipse((x, y), 1.5, 1.5, mm['gem'], z=z + r + 1.5)
    elif style == 'knob':
        c.ellipse((x, y), r * 0.85, r, A, z=z)
        c.capsule((x + r * 0.6, y), (x + r * 0.9, y), r * 0.7, r * 0.7, mm['Ad'], z=z - 0.5)
    elif style == 'cap':
        c.capsule((x - 1.0, y), (x + 1.4, y), r, r, A, z=z)
    elif style == 'ears':
        # yatağan: kemik kulaklı topuz
        bone = mm['bone']
        c.ellipse((x - 1.5, y - 3.6), 3.6, 3.0, bone, z=z, rot=-0.5)
        c.ellipse((x - 1.5, y + 3.6), 3.6, 3.0, bone, z=z, rot=0.5)
        c.capsule((x + 1.0, y), (x + 3.0, y), 3.4, 3.4, bone, z=z - 0.5)
        c.ellipse((x + 2.5, y), 1.2, 1.2, A, z=z + 4)


def guard(c, mm, x=4.6, half=10.5, r=2.4, z=4.0, style='bar', gem=True):
    A = mm['A']
    if style == 'bar':
        c.capsule((x, -half), (x, half), r, r, A, z=z)
        c.ellipse((x, -half), r + 0.9, r + 0.9, A, z=z + 0.4)
        c.ellipse((x, half), r + 0.9, r + 0.9, A, z=z + 0.4)
        c.ellipse((x, 0), r + 1.4, r + 2.4, A, z=z + 1.0)
    elif style == 'wings':
        # balçak kanatları bıçağa doğru kıvrılır
        c.capsule((x, 0), (x + 3.5, -half), r, r * 0.75, A, z=z)
        c.capsule((x, 0), (x + 3.5, half), r, r * 0.75, A, z=z)
        c.ellipse((x + 3.6, -half), r * 0.9, r * 0.9, A, z=z + 0.4)
        c.ellipse((x + 3.6, half), r * 0.9, r * 0.9, A, z=z + 0.4)
        c.ellipse((x + 0.5, 0), r + 1.2, r + 2.0, A, z=z + 1.0)
    elif style == 'disc':
        c.ellipse((x, 0), r, half, A, z=z, paint=[(ring(x, 0, half - 2.2, half - 1.2, ry=1.0), mm['Ad'])])
    if gem:
        c.ellipse((x + (0.5 if style == 'wings' else 0), 0), 1.7, 1.7, mm['gem'], z=z + 5.0)


def hilt(c, mm, x0=-16.0, x1=2.5, r=3.4, guard_half=10.5, guard_r=2.4, guard_x=4.8, pom='disc', pom_r=4.6, gem=True,
         wrap='leather', gstyle='bar'):
    grip(c, mm, x0, x1, r, wrap=wrap)
    pommel(c, mm, x0 - pom_r * 0.45, pom_r, style=pom, z=1.0, gem=gem)
    if guard_half:
        guard(c, mm, guard_x, guard_half, guard_r, z=4.0, style=gstyle, gem=gem)


def haft(c, mm, x0, x1, r=2.8, y0=0.0, y1=0.0, z=0.0, wood=None, caps=True, bands=()):
    """Ahşap sap: damar + uç bilezikleri + isteğe bağlı metal bantlar."""
    Wm = wood or mm['W']
    Wd = mm['Wd'] if wood is None else _shifted(wood, -1)
    c.capsule((x0, y0), (x1, y1), r, r, Wm, z=z, paint=[(grain(3.0, 0.7, 0.5, seed=x0 * 0.1), Wd)])
    if caps:
        c.capsule((x0, y0), (x0 + 2.0, y0 + (y1 - y0) * 0.02), r + 0.5, r + 0.5, mm['A'], z=z + 0.4)
    for bx in bands:
        t = (bx - x0) / max(1e-6, (x1 - x0))
        yy = y0 + (y1 - y0) * t
        c.capsule((bx - 1.0, yy), (bx + 1.0, yy), r + 0.6, r + 0.6, mm['A'], z=z + 0.5)


def tassel(c, mm, p, strands=((0.9, 1.0), (0.3, 1.1), (-0.3, 1.0)), L=11.0, cols=None, z=2.0, knot=True):
    """Püskül: düğümden sarkan birkaç tel (kıl/keçe)."""
    cols = cols or (mm['felt'], mm['white'], mm['felt'])
    for k, (dx, dy) in enumerate(strands):
        m = cols[k % len(cols)]
        q = (p[0] + dx * L * 0.5, p[1] + dy * L)
        mid_ = (p[0] + dx * L * 0.2 + 0.6, p[1] + dy * L * 0.5)
        c.capsule(p, mid_, 1.0, 0.9, m, z=z)
        c.capsule(mid_, q, 0.9, 0.5, m, z=z)
    if knot:
        c.ellipse(p, 1.8, 1.6, mm['A'], z=z + 2)


def gem(c, mm, p, r=1.8, z=10.0, mat=None):
    c.ellipse(p, r, r, mat or mm['gem'], z=z)


def rivets(c, mm, pts, r=1.0, z=20.0, mat=None):
    for p in pts:
        c.ellipse(p, r, r, mat or mm['iron'], z=z)


# ------------------------------------------------------------ bıçak / başlık arketipleri
def sword(c, mm, L=58.0, w=9.5, kind='double', curve=0.0, yelman=0.0, sway=0.0, x0=7.0, z=1.0, fuller=True,
          extra=None, tip_len=0.18, wave=0.0, glint=(0.22, 0.96), mat=None):
    top, bot, mid = blade_pts(x0, L, w, kind, curve, yelman, sway, tip_len=tip_len, wave=wave)
    draw_blade(c, mm, top, bot, mid, kind=kind, z=z, fuller=fuller, extra=extra, edge_glint=glint, mat=mat)
    return top, bot, mid


def spear_head(c, mm, x0, L=28.0, w=11.0, z=2.0, tip_len=0.55, socket=True, mat=None):
    top, bot, mid = blade_pts(x0, L, w, 'double', n=16, tip_len=tip_len)
    # yaprak: tabanda hızla genişleyen profil
    n = len(top)
    top2, bot2 = [], []
    for i in range(n):
        t = i / (n - 1)
        k = min(1.0, t / 0.28) ** 0.6
        x, yt = top[i]; _, yb = bot[i]
        top2.append((x, yt * k + mid[i][1] * (1 - k))); bot2.append((x, yb * k + mid[i][1] * (1 - k)))
    draw_blade(c, mm, top2, bot2, mid, kind='double', z=z, fuller=True, edge_glint=(0.1, 0.95), body_h=2.4, mat=mat)
    if socket:
        c.capsule((x0 - 5.0, 0), (x0 + 1.5, 0), 3.4, 2.8, mm['A'], z=z + 1.0)
        c.capsule((x0 - 5.0, 0), (x0 - 4.0, 0), 3.9, 3.9, mm['Ad'], z=z + 1.2)
    return top2, bot2, mid


def axe_head(c, mm, hx_, kind='crescent', z=2.0, scale=1.0, mat=None, back_spike=False, beard=0.0):
    """Balta başı: sap üstünde göz (socket) + gövde + ağız pahı + parlama. hx_: başlığın sap üzerindeki merkezi."""
    B = mat or mm['b']
    s = scale
    if kind == 'crescent':
        # hilal: dış yay (ağız) geniş, iç yay sapa doğru içbükey; iki boynuz ince, orta köprü sapa oturur
        body = [(hx_ + 1, -19 * s), (hx_ + 7, -20 * s), (hx_ + 14, -14 * s), (hx_ + 18, -5 * s), (hx_ + 18, 5 * s),
                (hx_ + 14, 14 * s), (hx_ + 7, 20 * s), (hx_ + 1, 19 * s), (hx_ + 6, 14 * s), (hx_ + 9, 6 * s),
                (hx_ + 9, -6 * s), (hx_ + 6, -14 * s)]
        edge = [(hx_ + 7, -20 * s), (hx_ + 14, -14 * s), (hx_ + 18, -5 * s), (hx_ + 18, 5 * s), (hx_ + 14, 14 * s), (hx_ + 7, 20 * s)]
        bridge = [(hx_ - 3, -4.5 * s), (hx_ + 10, -6.5 * s), (hx_ + 10, 6.5 * s), (hx_ - 3, 4.5 * s)]
    elif kind == 'bearded':
        body = [(hx_ - 3, -3.5 * s), (hx_ - 1, -13 * s), (hx_ + 9, -15 * s), (hx_ + 13, -8 * s), (hx_ + 13, 6 * s),
                (hx_ + 11, 14 * s + beard), (hx_ + 3, 15 * s + beard), (hx_ + 1, 8 * s), (hx_ - 3, 3.5 * s), (hx_, 0)]
        edge = [(hx_ + 9, -15 * s), (hx_ + 13, -8 * s), (hx_ + 13, 6 * s), (hx_ + 11, 14 * s + beard)]
    else:  # 'broad' (ikiz balta): kısa geniş
        body = [(hx_ - 3, -3 * s), (hx_ - 1, -11 * s), (hx_ + 8, -13 * s), (hx_ + 11, -6 * s), (hx_ + 11, 6 * s),
                (hx_ + 8, 13 * s), (hx_ - 1, 11 * s), (hx_ - 3, 3 * s), (hx_, 0)]
        edge = [(hx_ + 8, -13 * s), (hx_ + 11, -6 * s), (hx_ + 11, 6 * s), (hx_ + 8, 13 * s)]
    xs = [p[0] for p in body]; ys = [p[1] for p in body]
    pat = head_paint(mm, min(xs), min(ys), max(xs), max(ys), seed=hx_ * 0.1)
    if kind == 'crescent':
        c.poly(bridge, B, z=z - 0.5, bevel=1.4, height=2.2, paint=pat)
    pat += [(near(edge, 0.6, 0.05, 0.95, dx=-0.9), mm['glint'])]
    c.poly(body, B, z=z, bevel=1.8, height=3.0, paint=pat)
    # ağız pahı: dış kenara paralel, +x'e bakan eğik şerit
    inner = [(x - 4.5 * s, y * 0.78) for x, y in edge]
    c.poly(edge + inner[::-1], B, z=z + 3.2, bevel=0.01, height=0.0, tilt=(0.7, 0.0), paint=pat)
    if back_spike:
        sp = [(hx_ - 2, -3.0), (hx_ - 14, -1.2), (hx_ - 14, 1.2), (hx_ - 2, 3.0)]
        c.poly(sp, B, z=z + 0.5, bevel=1.2, height=2.0, paint=[(near([(hx_ - 13, -0.4), (hx_ - 3, -1.6)], 0.5), mm['glint'])])
    # göz: sapı saran halka + perçinler
    c.capsule((hx_ - 1.5, -4.6 * s), (hx_ - 1.5, 4.6 * s), 2.6, 2.6, mm['A'], z=z + 3.5)
    c.ellipse((hx_ - 1.5, -4.6 * s), 1.0, 1.0, mm['Ad'], z=z + 7); c.ellipse((hx_ - 1.5, 4.6 * s), 1.0, 1.0, mm['Ad'], z=z + 7)


def hammer_head(c, mm, x0, x1, hy=14.0, z=2.0, mat=None, face_mat=None, bands=True):
    """Çekiç başı: ön yüz + üst pah (ışık) + alt pah (gölge) + vuruş yüzü (+x); perçinli bantlar."""
    B = mat or mm['b']
    pat = head_paint(mm, x0, -hy, x1, hy, seed=x0 * 0.1)
    c.poly([(x0, -hy), (x1, -hy), (x1 + 1.5, -hy + 3), (x1 + 1.5, hy - 3), (x1, hy), (x0, hy)], B, z=z, bevel=1.8, height=3.0, paint=pat)
    c.poly([(x0 + 1, -hy + 1), (x1 - 1, -hy + 1), (x1 - 2.5, -hy + 4.5), (x0 + 2.5, -hy + 4.5)], B, z=z + 3.2, bevel=0.01, height=0, tilt=(0, -0.8), paint=pat)
    c.poly([(x0 + 2.5, hy - 4.5), (x1 - 2.5, hy - 4.5), (x1 - 1, hy - 1), (x0 + 1, hy - 1)], B, z=z + 3.2, bevel=0.01, height=0, tilt=(0, 0.8), paint=pat)
    c.poly([(x1 - 2.5, -hy + 4.5), (x1 + 0.5, -hy + 3.5), (x1 + 0.5, hy - 3.5), (x1 - 2.5, hy - 4.5)], face_mat or B, z=z + 3.2, bevel=0.01, height=0, tilt=(0.7, 0.1), paint=pat)
    if bands:
        for bx in (x0 + 4.5, x1 - 6.5):
            c.capsule((bx, -hy - 0.8), (bx, hy + 0.8), 1.6, 1.6, mm['A'], z=z + 3.6)
            rivets(c, mm, [(bx, -hy + 3), (bx, hy - 3)], 0.9, z + 7, mm['Ad'])


def flanged_head(c, mm, hx_, R=8.0, z=2.0, n_fl=6):
    """Dilimli gürz başı (yan görünüş): silindir çekirdek + eksen düzleminde kanatlar. Üst kanat yüzü ışığa,
    alt kanat gölgeye bakar; ara kanatlar koyu türevle ayrılır (parça çizgileri), kökler arkaya doğru incelir."""
    B, Bd = mm['b'], mm['bd']
    pat = head_paint(mm, hx_ - 10, -14, hx_ + 12, 14, seed=hx_)
    core_r = R * 0.6
    c.capsule((hx_ - 10, 0), (hx_ + 9, 0), core_r, core_r, B, z=z, paint=pat)

    def fin(y0, y1, tilt, zz, mat, gl):
        sgn = 1 if y1 > y0 else -1
        pts = [(hx_ - 10, y0), (hx_ - 7, y1 - sgn * 1.2), (hx_ + 5, y1), (hx_ + 9, y1 - sgn * 2.0), (hx_ + 10, y0)]
        pn = pat + ([(near([(hx_ - 6.5, y1 - sgn * 0.4), (hx_ + 5, y1 + sgn * 0.6)], 0.55), mm['glint'])] if gl else [])
        c.poly(pts, mat, z=zz, bevel=1.0, height=1.4, tilt=tilt, paint=pn)
    fin(-4.0, -14.5, (0, -0.85), z + 3.0, B, True)       # üst kanat
    fin(4.0, 14.5, (0, 0.85), z + 3.0, B, False)         # alt kanat
    fin(-1.5, -9.0, (0, -0.4), z + 7.5, Bd, False)       # üst-ön kanat (kısaltılmış)
    fin(1.5, 9.0, (0, 0.4), z + 7.5, Bd, False)          # alt-ön kanat
    c.capsule((hx_ - 10, 0), (hx_ + 10, 0), 1.3, 1.3, mm['bl'], z=z + 12)   # ön kanat kenardan: sırt çizgisi
    c.ellipse((hx_ + 11.5, 0), 2.4, 3.8, mm['A'], z=z + 9)
    c.poly([(hx_ + 12.5, -2.2), (hx_ + 18.5, 0), (hx_ + 12.5, 2.2)], B, z=z + 8, bevel=0.8, height=1.0)
    c.capsule((hx_ - 12.5, 0), (hx_ - 10.5, 0), core_r + 0.6, core_r + 0.6, mm['A'], z=z + 1)


def spiked_head(c, mm, hx_, R=9.0, z=2.0):
    B = mm['b']
    pat = head_paint(mm, hx_ - R, -R, hx_ + R, R, seed=hx_ * 0.3)
    c.ellipse((hx_, 0), R, R, B, z=z, depth=0.9, paint=pat)
    for k in range(8):
        a = k / 8 * math.tau + 0.2
        dx, dy = math.cos(a), math.sin(a)
        b0 = (hx_ + dx * (R - 1.5) - dy * 1.6, dy * (R - 1.5) + dx * 1.6)
        b1 = (hx_ + dx * (R - 1.5) + dy * 1.6, dy * (R - 1.5) - dx * 1.6)
        tip = (hx_ + dx * (R + 6.5), dy * (R + 6.5))
        c.poly([b0, tip, b1], mm['iron'], z=z + R * 0.9 + 0.5, bevel=0.9, height=1.6, tilt=(dx * 0.6, dy * 0.6))
    # öne bakan çiviler: kısa koniler (daire + koyu halka)
    for (ox, oy) in ((-3.5, -2.5), (3.0, -3.5), (-2.0, 3.5), (3.5, 2.0)):
        c.ellipse((hx_ + ox, oy), 1.9, 1.9, mm['iron'], z=z + R + 3, depth=1.4)


# ------------------------------------------------------------ yaylar ve oklar
BOWS = ('turk_yayi', 'akinci_yayi', 'saganak_yayi', 'tufan_yayi', 'od_oklari')


def _limb_pts(half, bulge, recurve, grip_x=7.0, n=22):
    """Kurulu kompozit yay profili (yan görünüş, ok +x'e uçar): çalışan kollar tutamaktan öne (+x) şişer,
    siyahlar (katı uçlar) geriye kırılır; uçlar tutamağın gerisinde kalır (kiriş yüksekliği). Kiriş sprite'a
    çizilmez: oyun (Player.BowString) uçlardan gez noktasına kendi kirişini çizer; uçlar pivotun 6 px sağından
    daha geride olmalı (Player._bow_tips)."""
    pts = []
    for i in range(-n, n + 1):
        t = i / n
        a = abs(t)
        x = grip_x + bulge * math.sin(math.pi * a) ** 1.3 - recurve * a ** 5
        pts.append((x, half * t, t))
    return pts


def _limbs(c, pts, mm, lam, r0, z=1.0, siyah=None, layers=True):
    """Kol katmanları: bir yüz boynuz (koyu), öteki sinir (açık), ortada lak/ahşap; siyahlar ayrı katı uç."""
    xy = [(x, y) for x, y, t in pts]
    n = len(pts) // 2
    pnt = [(band(-1.0, -0.4, 'v'), mm['horn']), (band(0.42, 1.0, 'v'), mm['sinew'])] if layers else None
    cut = int(round(n * 0.2))   # |t| > 0.8: siyah
    up = xy[cut:n + 1]; dn = xy[n:len(xy) - cut]
    c.tube(up, r0 * 0.74, r0, lam, z=z, paint=pnt)
    c.tube(dn, r0, r0 * 0.74, lam, z=z, paint=pnt)
    if siyah is not None:
        sd = _shifted(siyah, -1)
        c.tube(xy[:cut + 1], r0 * 0.8, r0 * 0.8, siyah, z=z + 0.3, paint=[(band(-1, -0.45, 'v'), sd)])
        c.tube(xy[len(xy) - cut - 1:], r0 * 0.8, r0 * 0.8, siyah, z=z + 0.3, paint=[(band(-1, -0.45, 'v'), sd)])
        for e in (xy[0], xy[-1]):
            c.ellipse((e[0] + 1.2, e[1]), 0.9, 0.9, mm['black'], z=z + 6)   # gez çentiği


def _bow_grip(c, mm, x=7.0, half=5.5, r=3.8, z=4.0, mat=None):
    c.capsule((x, -half), (x, half), r, r, mat or mm['G'], z=z, paint=[(diag(3.6, 1.2, 0.0), mm['Gd'])])
    c.capsule((x, -half - 1.2), (x, -half - 0.2), r + 0.5, r + 0.5, mm['A'], z=z + 0.5)
    c.capsule((x, half + 0.2), (x, half + 1.2), r + 0.5, r + 0.5, mm['A'], z=z + 0.5)


def _string(c, mm, pts, z=0.0):
    a, b = pts[0], pts[-1]
    c.capsule((a[0] + 0.5, a[1]), (b[0] + 0.5, b[1]), 0.75, 0.75, mm['string'], z=z)


def _arrow(c, mm, a, length, z=6.0, x0=6.0, y0=0.0, head=None, fletch=None, shaft=None):
    """Ok: gezden uca; gövde + yaprak uç (parlamalı) + iki tüy."""
    ca, sa = math.cos(a), math.sin(a)
    nx, ny = -sa, ca
    x1, y1 = x0 + ca * length, y0 + sa * length
    sh = shaft or mm['W']
    c.capsule((x0 - 4 * ca, y0 - 4 * sa), (x1, y1), 1.05, 0.95, sh, z=z)
    hm = head or mm['iron']
    hl = 7.5
    hp = [(x1 + nx * 1.9, y1 + ny * 1.9), (x1 + ca * hl * 0.35 + nx * 2.2, y1 + sa * hl * 0.35 + ny * 2.2),
          (x1 + ca * hl, y1 + sa * hl), (x1 + ca * hl * 0.35 - nx * 2.2, y1 + sa * hl * 0.35 - ny * 2.2), (x1 - nx * 1.9, y1 - ny * 1.9)]
    c.poly(hp, hm, z=z + 1, bevel=1.4, height=1.6, paint=[(near([hp[3], hp[2]], 0.5, dx=-0.5), mm['glint'])])
    fm = fletch or mm['white']
    for sgn in (-1, 1):
        f0 = (x0 - 3.5 * ca, y0 - 3.5 * sa)
        f1 = (x0 - 9.5 * ca + nx * sgn * 2.8, y0 - 9.5 * sa + ny * sgn * 2.8)
        f2 = (x0 - 10.5 * ca + nx * sgn * 0.8, y0 - 10.5 * sa + ny * sgn * 0.8)
        f3 = (x0 - 1.5 * ca + nx * sgn * 0.9, y0 - 1.5 * sa + ny * sgn * 0.9)
        c.poly([f0, f1, f2, f3], fm, z=z + 0.5, bevel=0.8, height=0.6,
               paint=[(diag(2.4, 0.8, -ca * 0.5 if sgn > 0 else ca * 0.5), _shifted(fm, -1))])
    c.capsule((x0 - 10.5 * ca, y0 - 10.5 * sa), (x0 - 11.8 * ca, y0 - 11.8 * sa), 1.1, 1.1, mm['bone'], z=z + 0.6)


def draw_bow(c, iid, mm):
    """Her yay ayrı kimlik; malzeme rengi siyah/uç ve süslerde. Kiriş oyunda çizilir (sprite'ta yok)."""
    B, A = mm['b'], mm['A']
    if iid == 'turk_yayi':
        # kırmızı laklı derin kompozit yay, kemik siyahlar, altın çiçek benekleri
        pts = _limb_pts(29.0, 7.0, 10.0)
        _limbs(c, pts, mm, M['w_lacquer_r'], 3.4, z=1, siyah=mm['bone'])
        for t in (-0.62, -0.3, 0.3, 0.62):
            p = pts[int(round((t + 1) * 22))]
            c.ellipse((p[0], p[1]), 1.3, 1.3, mm['gold'], z=6)
        for t in (-0.74, 0.74):
            p = pts[int(round((t + 1) * 22))]
            c.capsule((p[0] - 2.2, p[1]), (p[0] + 2.2, p[1]), 1.3, 1.3, B, z=5.5)
        _bow_grip(c, mm)
        c.ellipse((7.5, 0), 1.3, 1.3, mm['gem'], z=10)
    elif iid == 'akinci_yayi':
        # kısa akıncı yayı: siyah lak, altın şeritler, tutamaktan sarkan kızıl at kılı püskül (uçlardan kısa kalır)
        pts = _limb_pts(23.0, 5.5, 9.0)
        _limbs(c, pts, mm, M['w_lacquer_k'], 3.1, z=1, siyah=B)
        for i in range(6, len(pts) - 6, 6):
            p = pts[i]
            c.capsule((p[0] - 2.0, p[1]), (p[0] + 2.0, p[1]), 1.0, 1.0, mm['gold'], z=5.5)
        _bow_grip(c, mm, half=4.5, mat=mm['felt'])
        tas = [(7.5, 5.0), (9.0, 9.5), (10.0, 14.0), (10.5, 17.5)]
        for a_, b_ in zip(tas, tas[1:]):
            c.capsule(a_, b_, 1.8, 1.4, mm['felt'], z=4, paint=[(grain(1.6, 0.5, 0.0, axis='y'), _shifted(mm['felt'], -1))])
        c.ellipse((10.5, 18.5), 2.4, 2.6, mm['felt'], z=4)
        c.capsule((8.6, 8.2), (8.8, 9.8), 2.3, 2.3, mm['gold'], z=6)
    elif iid == 'saganak_yayi':
        # çift katlı mavi yay: arkada malzeme renginde ikinci kol katmanı, üç ok yelpaze halinde kurulu
        back = _limb_pts(30.0, 7.2, 10.5, grip_x=3.4)
        front = _limb_pts(28.0, 7.0, 10.0, grip_x=7.6)
        _limbs(c, back, mm, B, 2.8, z=0, layers=False)
        _limbs(c, front, mm, M['w_lacquer_b'], 3.2, z=1, siyah=mm['bone'])
        for a in (-0.22, 0.0, 0.22):
            _arrow(c, mm, a, 28, z=6, x0=10.0, head=mm['iron'])
        _bow_grip(c, mm, x=7.6, z=8)
    elif iid == 'tufan_yayi':
        # büyük tufan yayı: turkuaz lak, kartal başlı altın uçlar, beş ok
        pts = _limb_pts(34.0, 8.0, 11.0)
        _limbs(c, pts, mm, M['w_lacquer_t'], 3.8, z=1)
        for end in (pts[0], pts[-1]):
            sgn = 1 if end[1] > 0 else -1
            c.ellipse((end[0] + 1.0, end[1] - sgn * 0.5), 4.2, 3.4, mm['gold'], z=3)
            c.poly([(end[0] + 3.8, end[1] - 1.4), (end[0] + 9.0, end[1] + sgn * 0.6), (end[0] + 3.8, end[1] + 1.8)], M['w_gem_amber'], z=4, bevel=0.8, height=0.8)
            c.ellipse((end[0] + 1.8, end[1] - sgn * 1.4), 0.9, 0.9, mm['black'], z=8)
        for t in (-0.45, 0.45):
            p = pts[int(round((t + 1) * 22))]
            c.capsule((p[0] - 2.6, p[1]), (p[0] + 2.6, p[1]), 1.4, 1.4, B, z=5.5)
        for a in (-0.4, -0.2, 0.0, 0.2, 0.4):
            _arrow(c, mm, a, 30, z=6, x0=8.0, head=mm['gold'], fletch=M['nazar_l'])
        _bow_grip(c, mm, x=7.0, half=5.5, z=8, mat=mm['gold'])
    elif iid == 'od_oklari':
        # od yayı: kömür ahşap, alev biçimli uçlar (ışıldar), tutamakta kor taşı, kurulu ateş oku
        pts = _limb_pts(27.0, 6.5, 9.5)
        _limbs(c, pts, mm, M['w_dark_wood'], 3.2, z=1, layers=False)
        for end in (pts[0], pts[-1]):
            sgn = 1 if end[1] > 0 else -1
            c.poly([(end[0] - 2.4, end[1] - sgn * 1.0), (end[0] + 3.4, end[1] - sgn * 3.6), (end[0] + 6.0, end[1] + sgn * 4.0), (end[0] + 1.0, end[1] + sgn * 2.4)], mm['ember'], z=3, bevel=1.2, height=1.2)
        for t in (-0.5, 0.5):
            p = pts[int(round((t + 1) * 22))]
            c.capsule((p[0] - 2.4, p[1]), (p[0] + 2.4, p[1]), 1.3, 1.3, B, z=5.5)
        _arrow(c, mm, 0.0, 30, z=6, x0=8.0, head=mm['ember'], fletch=mm['felt'])
        c.ellipse((42.0, 0), 4.4, 3.2, mm['ember'], z=8)
        c.ellipse((44.5, 0), 2.0, 1.6, M['flower_y'], z=9)
        _bow_grip(c, mm, z=8)
        c.ellipse((7.0, 0), 2.6, 2.6, mm['ember'], z=12)


# ------------------------------------------------------------ kalkanlar
def shield(c, mm, R=24.0, face=None, rim=None, boss=True, rivet_n=10, boss_r=6.0, face_paint=None, rim_w=3.6, boss_mat=None):
    rim_m = rim or mm['A']
    face_m = face or mm['b']
    # çerçeve: dış halka (perçinli), kenarda koyu kontur; yüz: hafif kubbeli
    c.ellipse((0, 0), R, R, rim_m, z=0, depth=0.08, paint=[(ring(0, 0, R - rim_w - 0.8, R - rim_w), _shifted(rim_m, -1))])
    c.ellipse((0, 0), R - rim_w, R - rim_w, face_m, z=1.0, depth=0.18, paint=face_paint)
    if rivet_n:
        pts = [(math.cos(k / rivet_n * math.tau) * (R - rim_w * 0.5), math.sin(k / rivet_n * math.tau) * (R - rim_w * 0.5)) for k in range(rivet_n)]
        rivets(c, mm, pts, 1.0, z=12, mat=_shifted(rim_m, 1))
    if boss:
        bm = boss_mat or mm['A']
        c.ellipse((0, 0), boss_r + 1.6, boss_r + 1.6, bm, z=9.0, depth=0.25)
        c.ellipse((0, 0), boss_r, boss_r, bm, z=10.0, depth=1.0)


# ------------------------------------------------------------ eşyalar
def draw_item(c, iid, mm):
    B, A, G, W = mm['b'], mm['A'], mm['G'], mm['W']
    if iid in BOWS:
        draw_bow(c, iid, mm)
        return
    # ---------------------------------------------------------------- kılıçlar
    if iid == 'alp_kilici':
        hilt(c, mm, -16, 2.5, 3.4, guard_half=11, guard_r=2.4)
        sword(c, mm, L=58, w=9.5, kind='double')
    elif iid == 'pala':
        hilt(c, mm, -15, 2.5, 3.5, guard_half=8, guard_r=2.2, pom='knob', pom_r=4.4)
        sword(c, mm, L=56, w=11, kind='single', curve=11, yelman=3.2, tip_len=0.14)
    elif iid == 'yatagan':
        grip(c, mm, -14, 2.5, 3.2, wrap='bone')
        pommel(c, mm, -17.5, style='ears')
        c.capsule((2.5, 0), (5.0, 0), 3.6, 3.4, A, z=3)
        sword(c, mm, L=54, w=8.5, kind='single', curve=9, sway=4.0, x0=5.5, tip_len=0.15, fuller=True)
    elif iid == 'yildirim_kilici':
        # Tengri'nin kılıcı: hafif kavisli uzun tek ağızlı kılıç, mavi şimşek taşı, bıçakta beyaz şimşek kakması
        hilt(c, mm, -18, 2.5, 3.2, guard_half=7, guard_r=2.0, gstyle='wings', pom='disc', pom_r=4.2)
        zig = [(12, -1.2), (20, -2.6), (26, 0.4), (36, -2.2), (44, 0.2), (56, -3.0), (62, -1.6)]
        sword(c, mm, L=66, w=8.5, kind='single', curve=8, tip_len=0.16, extra=[(near(zig, 0.55), M['nazar_w'])])
        gem(c, mm, (5.3, 0), 1.9, z=11, mat=mm['kut'])
        tassel(c, mm, (-20.5, 1.5), strands=((0.6, 1.0), (0.1, 1.1), (-0.4, 0.95)), L=10, cols=(mm['felt'], mm['turq'], mm['gold']), z=2, knot=False)
    elif iid == 'ayaz_kilici':
        # ayaz kılıcı: geniş çift ağızlı bıçak, kırağılı sırt, sırtta buz kristalleri
        hilt(c, mm, -16, 2.5, 3.4, guard_half=11, guard_r=2.4)
        ice = M['w_frost_glow']
        t0, b0, _m0 = blade_pts(7, 60, 10)
        top, bot, mid = sword(c, mm, L=60, w=10, kind='double', extra=[(near(t0, 0.7, 0.08, 0.95, dy=0.8), ice)])
        for k, x in enumerate((18, 30, 42)):
            yt = np.interp(x, [p[0] for p in top], [p[1] for p in top])
            c.poly([(x - 1.5, yt + 0.5), (x + 2.0, yt + 0.5), (x + 1.2, yt - 5.5 + k * 0.6)], M['w_frost'], z=4, bevel=0.8, height=1.0, paint=[(near([(x + 0.2, yt), (x + 1.2, yt - 5)], 0.45), ice)])
        gem(c, mm, (4.8, 0), 1.8, z=11, mat=M['w_gem_ice'])
    elif iid == 'ruh_kilici':
        # ruh kılıcı: dalgalı ağız, ışıyan öz damarı; kabza kemik
        hilt(c, mm, -16, 2.5, 3.4, guard_half=9, guard_r=2.3, wrap='bone', pom='disc')
        sp = M['w_spirit_core']
        top, bot, mid = blade_pts(7, 62, 10, 'double', wave=1.6, tip_len=0.2)
        draw_blade(c, mm, top, bot, mid, 'double', extra=[(near(mid, 0.8, 0.05, 0.9), sp), (near(mid, 0.5, 0.3, 0.6, dy=-2.2), sp)])
        for x in (20, 34, 48):
            c.ellipse((x, 0), 1.3, 1.3, sp, z=6)
        gem(c, mm, (4.8, 0), 1.8, z=11, mat=mm['kut'])
    elif iid == 'ay_palasi':
        # ay palası: iki hilal bıçak (biri arkada), altın hilal tokalar
        for (ox, oy), z0 in (((6, 9), -8), ((0, 0), 0)):
            grip(c, mm, -10 + ox, 1.5 + ox, 2.8, z=z0, y=oy, wrap='cord')
            pommel(c, mm, -12 + ox, 3.4, style='cap', z=z0 + 1, y=oy, gem=False)
            top, bot, mid = blade_pts(3 + ox, 38, 8.5, 'single', curve=15, tip_len=0.2)
            top = shift_pts(top, 0, oy); bot = shift_pts(bot, 0, oy); mid = shift_pts(mid, 0, oy)
            draw_blade(c, mm, top, bot, mid, 'single', z=z0 + 1, fuller=False, mat=(B if z0 == 0 else mm['bd']))
            c.ellipse((2.0 + ox, oy), 2.6, 3.6, mm['gold'], z=z0 + 5, paint=[(ring(2.0 + ox, oy, 1.4, 2.4), _shifted(mm['gold'], -1))])
    elif iid == 'yilan_kilici':
        # yılan kılıcı (Şahmeran): dalgalı bıçak, yılan başı siper, zehir damlası
        hilt(c, mm, -16, 2.0, 3.3, guard_half=0, pom='knob', pom_r=4.4, wrap='cord')
        venom = M['w_venom']
        c.ellipse((4.5, 0), 4.2, 3.4, venom, z=4)
        c.ellipse((3.6, -1.3), 0.9, 0.9, M['eye_red'], z=10)
        c.poly([(7.5, 1.0), (10.5, 3.6), (8.0, 2.4)], venom, z=5, bevel=0.4, height=0.4)
        top, bot, mid = blade_pts(8, 60, 8.5, 'double', wave=2.2, tip_len=0.2)
        draw_blade(c, mm, top, bot, mid, 'double', extra=[(near(mid, 0.6, 0.05, 0.92, dy=-0.3), venom)], fuller=False)
        c.ellipse((58, 7.5), 1.3, 1.9, venom, z=8)
    elif iid == 'ruzgar_kilici':
        # rüzgâr kılıcı (Kaf): ince, uzun, kavisli; bıçakta hava oyukları, topuzda tüy
        hilt(c, mm, -16, 2.5, 3.0, guard_half=7, guard_r=1.9, gstyle='disc', pom='disc', pom_r=3.8)
        slots = []
        for x in (20, 32, 44):
            slots.append((near([(x, -1.2), (x + 7, -2.4)], 0.6), M['nazar_w']))
            slots.append((near([(x, -1.2), (x + 7, -2.4)], 0.5, dy=1.1), mm['bd']))
        sword(c, mm, L=68, w=7.0, kind='single', curve=11, tip_len=0.2, extra=slots)
        c.capsule((-18, 0), (-25, 6), 0.7, 0.5, mm['bone'], z=2)
        c.poly([(-23, 4), (-30, 10), (-26, 12), (-20, 7)], mm['white'], z=2, bevel=0.9, height=0.6, paint=[(diag(2.2, 0.7, -1.0), _shifted(mm['white'], -1))])
    elif iid == 'ulu_kilic':
        # devasa iki el kılıcı: uzun kabza, geniş siper, kalın bıçak; ortada ışıyan oyuk
        hilt(c, mm, -28, 2.5, 4.0, guard_half=14, guard_r=3.2, pom_r=5.8, guard_x=5.4)
        gl = _shifted(mm['gem'], 0)
        top, bot, mid = blade_pts(9, 84, 14, 'double', tip_len=0.16)
        draw_blade(c, mm, top, bot, mid, 'double', body_h=3.2, extra=[(near(mid, 0.85, 0.08, 0.68), gl)], fuller=False)
        c.capsule((9, -5.5), (9, 5.5), 2.0, 2.0, A, z=7)   # bıçak boğazı
    elif iid == 'bozgun_kilici':
        # Bozgun Kılıcı: Kara Börü Han'ın bozgun kristalinden dövülmüş dev kılıç; kemik boynuz siper
        crys = M['w_corrupt']
        grip(c, mm, -24, 2.0, 3.8)
        pommel(c, mm, -26.5, 5.2, style='disc', gem=True)
        bone = mm['bone']
        c.capsule((3.0, 0), (1.0, -12.0), 2.6, 1.4, bone, z=4, paint=[(diag(3.0, 0.7, 0.0), _shifted(bone, -1))])
        c.capsule((3.0, 0), (1.0, 12.0), 2.6, 1.4, bone, z=4, paint=[(diag(3.0, 0.7, 0.0), _shifted(bone, -1))])
        c.ellipse((3.5, 0), 3.6, 4.2, bone, z=5)
        gem(c, mm, (3.5, 0), 2.0, z=11, mat=crys)
        top, bot, mid = blade_pts(8, 82, 12.5, 'double', tip_len=0.18)
        draw_blade(c, mm, top, bot, mid, 'double', body_h=3.0, extra=[(near(wave_pts(mid[1], mid[-3], 1.2, n=5, k=16), 0.75, 0.04, 0.92), crys)])
        for x in (26, 44, 62):
            yt = np.interp(x, [p[0] for p in top], [p[1] for p in top])
            c.poly([(x - 2.5, yt + 0.4), (x + 2.5, yt + 0.4), (x + 0.5, yt - 7.0)], crys, z=5, bevel=0.9, height=1.0)
    elif iid == 'bori_hanceri':
        # Börü Hançeri: kısa kıvrık bıçak, kurt dişi kemik kabza, kan oluğu
        grip(c, mm, -11, 1.5, 3.0, wrap='bone', ferrule=False)
        bone = mm['bone']
        c.poly([(-11, -2.2), (-17, -4.5), (-14.5, -0.5), (-17, 3.5), (-11, 2.2)], bone, z=1, bevel=1.0, height=1.4)
        c.capsule((1.5, -4.0), (1.5, 4.0), 1.8, 1.8, A, z=4)
        sword(c, mm, L=32, w=7.5, kind='single', curve=7, x0=4, tip_len=0.2)
    # ---------------------------------------------------------------- baltalar, topuzlar, çekiçler
    elif iid == 'gurz':
        haft(c, mm, -22, 42, 2.9, bands=(10, 24))
        pommel(c, mm, -23.5, 3.8, style='cap', gem=False)
        c.capsule((-6, 0), (4, 0), 3.4, 3.4, G, z=1, paint=[(diag(4.0, 1.3, 0.8), mm['Gd'])])
        flanged_head(c, mm, 52, R=8.0, z=2)
    elif iid == 'civili_topuz':
        haft(c, mm, -18, 34, 2.9, bands=(14,))
        pommel(c, mm, -19.5, 3.8, style='cap', gem=False)
        c.capsule((-5, 0), (5, 0), 3.4, 3.4, G, z=1, paint=[(diag(4.0, 1.3, 0.8), mm['Gd'])])
        c.capsule((30, 0), (36, 0), 3.4, 3.8, A, z=2)
        spiked_head(c, mm, 44, R=9.5, z=2)
    elif iid == 'teber':
        haft(c, mm, -24, 62, 2.6, bands=(-8, 36))
        axe_head(c, mm, 50, kind='crescent', z=2, back_spike=True)
        c.capsule((60, 0), (69, 0), 1.6, 0.8, B, z=3)
        tassel(c, mm, (45, 5), strands=((0.5, 1.0), (0.0, 1.1), (-0.5, 1.0)), L=10, cols=(mm['felt'], mm['felt'], mm['felt']), z=8)
    elif iid == 'savas_baltasi':
        haft(c, mm, -20, 42, 2.7)
        c.capsule((-8, 0), (4, 0), 3.3, 3.3, G, z=1, paint=[(diag(4.2, 1.3, 0.8), mm['Gd'])])
        axe_head(c, mm, 34, kind='bearded', z=2, beard=4.0)
    elif iid == 'ikiz_balta':
        # İkiz Balta: iki kısa savaş baltası (biri arkada), kızıl kayış
        for (ox, oy), z0 in (((4, 11), -10), ((0, 0), 0)):
            haft(c, mm, -12 + ox, 26 + ox, 2.4, y0=oy, y1=oy, z=z0)
            # arkadaki daha koyu okunur: aynı malzeme, koyu türev
            body = [(20 + ox, -3 + oy), (22 + ox, -11 + oy), (31 + ox, -13 + oy), (34 + ox, -6 + oy), (34 + ox, 6 + oy), (31 + ox, 13 + oy), (22 + ox, 11 + oy), (20 + ox, 3 + oy), (23 + ox, oy)]
            edge = [(31 + ox, -13 + oy), (34 + ox, -6 + oy), (34 + ox, 6 + oy), (31 + ox, 13 + oy)]
            mat = B if z0 == 0 else mm['bd']
            pat = head_paint(mm, 20 + ox, -13 + oy, 34 + ox, 13 + oy) + [(near(edge, 0.6, 0.05, 0.95, dx=-0.9), mm['glint'])]
            c.poly(body, mat, z=z0 + 2, bevel=1.6, height=2.6, paint=pat)
            c.poly(edge + [(x - 3.5, oy + (y - oy) * 0.75) for x, y in edge][::-1], mat, z=z0 + 4.9, bevel=0.01, height=0, tilt=(0.7, 0), paint=pat)
            c.capsule((21 + ox, -4 + oy), (21 + ox, 4 + oy), 2.4, 2.4, A, z=z0 + 5.5)
            c.capsule((-6 + ox, oy - 1), (-2 + ox, oy + 1), 3.0, 3.0, mm['felt'], z=z0 + 2)
    elif iid == 'dag_cekici':
        # dağ çekici: uzun sap, dev demir başlık + taş vuruş bloğu, kemik dişler
        haft(c, mm, -26, 36, 3.6, bands=(-10, 12))
        pommel(c, mm, -28, 4.6, style='cap', gem=False)
        hammer_head(c, mm, 30, 62, hy=16, z=2)
        rock = M['w_rock']
        c.poly([(60, -12), (74, -10), (76, 0), (74, 10), (60, 12)], rock, z=4, bevel=2.0, height=3.0, paint=[(dimples(3.0, 5.0, 0.3, 'hi'), M['w_rock_d'])])
        for y in (-7, 0, 7):
            c.capsule((73, y), (82, y), 1.6, 0.8, mm['bone'], z=6)
        c.capsule((44, -19), (44, 19), 2.0, 2.0, A, z=6)
        rivets(c, mm, [(44, -14), (44, 14)], 1.0, 10, mm['Ad'])
    elif iid == 'kor_cekici':
        # kor çekici (Tamu): kara taş başlık, içinden sızan kor çatlakları, kısa kalın sap
        haft(c, mm, -22, 32, 3.4, bands=(8,))
        pommel(c, mm, -24, 4.4, style='cap', gem=False)
        ember = mm['ember']
        hammer_head(c, mm, 28, 60, hy=14, z=2, bands=False)
        cr = wave_pts((31, -9), (57, 8), 2.5, n=5, k=14)
        cr2 = wave_pts((34, 10), (54, -8), 2.0, n=4, k=12, phase=1.0)
        c.poly([(29, -13), (59, -13), (59, 13), (29, 13)], B, z=5.5, bevel=0.01, height=0,
               paint=[(lambda lu, lv, px, py: np.zeros(px.shape, bool), B), (near(cr, 0.7), ember), (near(cr2, 0.6), ember), (dimples(9.0, 6.0, 0.25, 'lo'), ember)] + head_paint(mm, 29, -13, 59, 13))
        for bx in (33, 53):
            c.capsule((bx, -15), (bx, 15), 1.7, 1.7, A, z=6)
        c.poly([(60, -3), (70, 0), (60, 3)], ember, z=6, bevel=1.0, height=1.2)
        c.capsule((40, -14), (40, -17), 1.4, 0.8, ember, z=7)
    # ---------------------------------------------------------------- mızraklar, cirit, sapan, kement, kırbaç
    elif iid == 'kargi':
        haft(c, mm, -26, 62, 2.4, bands=(-12, 8, 28))
        spear_head(c, mm, 64, L=28, w=11.5, z=2)
        tassel(c, mm, (58, 2.5), strands=((0.6, 1.0), (0.2, 1.15), (-0.2, 1.05), (-0.6, 0.9)), L=13, cols=(mm['felt'], mm['white'], mm['felt'], mm['white']), z=5)
    elif iid == 'tulpar_mizragi':
        # Tulpar Mızrağı: uzun akçaağaç sap, kanatlı yaprak uç, uçan at yelesi püskül, altın halkalar
        haft(c, mm, -26, 66, 2.4, bands=())
        for x in (-14, 10, 36):
            c.capsule((x - 1, 0), (x + 1, 0), 3.0, 3.0, mm['gold'], z=0.6)
        spear_head(c, mm, 66, L=26, w=10, z=2)
        c.poly([(66, -3.5), (62, -12), (70, -5)], mm['gold'], z=4, bevel=0.9, height=1.0)
        c.poly([(66, 3.5), (62, 12), (70, 5)], mm['gold'], z=4, bevel=0.9, height=1.0)
        tassel(c, mm, (60, 2.5), strands=((0.7, 1.0), (0.3, 1.15), (-0.1, 1.05), (-0.5, 0.9)), L=14, cols=(mm['white'], mm['turq'], mm['white'], mm['turq']), z=1)
    elif iid == 'cirit':
        haft(c, mm, -22, 58, 1.9, caps=False)
        spear_head(c, mm, 58, L=15, w=5.5, z=2, socket=False)
        c.capsule((56, 0), (59, 0), 2.4, 2.0, A, z=3)
        for sgn, m in ((-1, mm['felt']), (1, mm['turq'])):
            c.poly([(-22, 0), (-30, sgn * 4.5), (-28, sgn * 1.0), (-21, sgn * 1.4)], m, z=2, bevel=0.8, height=0.6, paint=[(diag(2.4, 0.8, 0.0), _shifted(m, -1))])
    elif iid == 'coban_sapani':
        # çoban sapanı: çatal sap, iki deri kayış, taş yuvası
        haft(c, mm, -14, 4, 3.0, caps=False)
        c.capsule((-14, 0), (-12.5, 0), 3.3, 3.3, G, z=0.5)
        c.capsule((4, 0), (16, -11), 2.4, 2.0, W, z=1, paint=[(grain(2.8, 0.7, 0.4, axis='x'), mm['Wd'])])
        c.capsule((4, 0), (16, 11), 2.4, 2.0, W, z=1, paint=[(grain(2.8, 0.7, 0.4, axis='x'), mm['Wd'])])
        c.capsule((16, -11), (11, -1), 0.9, 0.9, G, z=3); c.capsule((16, 11), (11, 1), 0.9, 0.9, G, z=3)
        c.ellipse((16, -11), 1.6, 1.6, A, z=4); c.ellipse((16, 11), 1.6, 1.6, A, z=4)
        c.ellipse((10, 0), 4.2, 3.6, G, z=4, paint=[(diag(3.0, 0.9, 0.5), mm['Gd'])])
        c.ellipse((9.6, -0.6), 2.4, 2.2, M['w_rock'], z=8, depth=1.0)
    elif iid == 'kement':
        # kement: kısa ahşap sap, halka halinde sarılmış ip, ileri uzanan ilmek ve düğüm
        haft(c, mm, -12, 8, 2.8, caps=True)
        cord, cd = mm['cord'], mm['cordd']
        tw = [(diag(2.6, 0.9, -0.8), cd)]
        for k, (ox, oy) in enumerate(((0, 0), (1.5, 1.0), (3.0, -1.0))):
            c.ellipse((22 + ox, oy), 12, 9, cord, z=1 + k * 0.5, paint=tw + [(disc(22 + ox, oy, 7.0), cord)])
            c.ellipse((22 + ox, oy), 7.6, 5.2, mm['black'], z=1.2 + k * 0.5)
        c.ellipse((23.5, 0), 7.6, 5.2, cord, z=0.8, paint=tw)
        loop = [(32, -5), (40, -9), (50, -12), (60, -11), (68, -14), (74, -22), (66, -28), (56, -24), (52, -17)]
        c.tube(loop, 1.5, 1.3, cord, z=3, paint=tw)
        c.ellipse((52, -16), 2.8, 2.4, cd, z=5)
        c.capsule((10, 2), (14, 5), 1.6, 1.4, G, z=3)
    elif iid == 'od_kamcisi':
        # od kamçısı: deri sargılı sap, örgülü kırbaç, uçlara doğru büyüyen kor alevleri
        grip(c, mm, -12, 8, 3.0, wrap='leather')
        pommel(c, mm, -13.5, 3.6, style='cap', gem=False)
        cord, cd = mm['cord'], mm['cordd']
        lash = [(8, 0), (18, -5), (28, -2), (40, -9), (52, -4), (64, -12), (74, -8)]
        c.tube(lash, 2.0, 1.0, cord, z=2, paint=[(diag(2.4, 0.9, -0.7), cd)])
        for k, (x, y) in enumerate(lash[2:]):
            c.ellipse((x, y - 2.5 - k * 0.3), 2.0 + k * 0.4, 2.8 + k * 0.5, mm['ember'], z=4)
            c.ellipse((x + 0.5, y - 2.0 - k * 0.3), 0.9 + k * 0.2, 1.3 + k * 0.2, M['flower_y'], z=5)
    # ---------------------------------------------------------------- hançer, pençe, tırpan
    elif iid == 'ikiz_bicak':
        for (ox, oy), z0 in (((6, 9), -10), ((0, 0), 0)):
            grip(c, mm, -11 + ox, 1.0 + ox, 2.7, z=z0, y=oy, wrap='cord')
            pommel(c, mm, -12.5 + ox, 3.4, style='disc', z=z0 + 1, y=oy, gem=False)
            c.capsule((1.5 + ox, -5 + oy), (1.5 + ox, 5 + oy), 1.6, 1.6, A, z=z0 + 4)
            c.ellipse((1.5 + ox, -5 + oy), 2.2, 2.2, A, z=z0 + 4.3); c.ellipse((1.5 + ox, 5 + oy), 2.2, 2.2, A, z=z0 + 4.3)
            top, bot, mid = blade_pts(3.5 + ox, 30, 6.5, 'double', tip_len=0.3)
            top = shift_pts(top, 0, oy); bot = shift_pts(bot, 0, oy); mid = shift_pts(mid, 0, oy)
            draw_blade(c, mm, top, bot, mid, 'double', z=z0 + 1, mat=(B if z0 == 0 else mm['bd']))
    elif iid == 'kurt_pencesi':
        for (ox, oy), z0 in (((5, 9), -10), ((0, 0), 0)):
            c.capsule((-10 + ox, oy), (2 + ox, oy), 4.2, 4.2, G, z=z0, paint=[(diag(4.0, 1.4, 0.9), mm['Gd'])])
            c.capsule((-1 + ox, -4.5 + oy), (-1 + ox, 4.5 + oy), 1.8, 1.8, A, z=z0 + 4)
            rivets(c, mm, [(-1 + ox, -3 + oy), (-1 + ox, 3 + oy)], 0.8, z0 + 8, mm['Ad'])
            mat = B if z0 == 0 else mm['bd']
            for k, (dy0, dy1) in enumerate(((-5.0, -10.0), (0.0, -1.5), (5.0, 7.0))):
                pts = [(2 + ox, dy0 - 2.4 + oy), (12 + ox, dy0 * 1.1 - 3.2 + oy), (22 + ox, dy0 + dy1 * 0.6 - 3.0 + oy), (30 + ox, dy1 + oy), (21 + ox, dy0 + dy1 * 0.5 + 1.0 + oy), (12 + ox, dy0 * 1.1 + 1.8 + oy), (2 + ox, dy0 + 2.4 + oy)]
                c.poly(pts, mat, z=z0 + 1 + k * 0.2, bevel=1.5, height=2.4, paint=[(near(pts[3:6], 0.55, dy=-1.0), mm['glint']), (near(pts[0:4], 0.5, dy=1.2), mm['bd'])])
    elif iid == 'erlik_tirpani':
        # tırpan: kavisli sap, dik tutamak, uzun kavisli bıçak; Erlik'in bozgun taşı bağlantıda
        snath = [(-26, 8), (-10, 4), (8, -1), (24, -5), (36, -7)]
        c.tube(snath, 2.8, 2.4, W, z=0, paint=[(grain(3.0, 0.7, 0.5), mm['Wd'])])
        c.capsule((-26, 8), (-24.5, 7.6), 3.0, 3.0, A, z=0.4)
        c.capsule((-6, 3), (-6, 11), 1.6, 1.6, W, z=2); c.capsule((-6, 11), (-6, 12), 2.2, 2.2, A, z=2.5)
        c.capsule((36, -7), (36, -13), 2.4, 2.4, A, z=3)
        top = [(36, -16), (46, -22), (58, -25), (70, -23), (82, -16)]
        bot = [(37, -11), (48, -16), (60, -19), (72, -19), (82, -16)]
        mid = lerp_pts(top, bot, 0.45)
        draw_blade(c, mm, top, bot, mid, 'single', z=2, fuller=True, edge_glint=(0.05, 0.95))
        gem(c, mm, (34, -9), 2.2, z=12, mat=M['w_corrupt'])
        tassel(c, mm, (-20, 9), strands=((0.5, 1.0), (0.0, 1.1), (-0.5, 1.0)), L=11, cols=(mm['felt'], mm['bone'], mm['felt']), z=3)
    # ---------------------------------------------------------------- v27: yeni silahlar
    elif iid == 'gun_ay_ikizi':
        # Gün-Ay İkizi (birleşik duruş): ortada kızıl ipli kabza; sağda altın güneş siperi ve yukarı kıvrılan Gün
        # bıçağı, solda gümüş hilal siperi ve aşağı kıvrılan Ay bıçağı (180° dönük S: döndükçe iki uç da biçer)
        gold, sil = mm['gold'], M['w_silver']
        grip(c, mm, -9, 9, 3.1, wrap='cord', ferrule=False)
        c.capsule((7.5, 0), (10.5, 0), 3.7, 3.7, gold, z=0.6)
        c.capsule((-10.5, 0), (-7.5, 0), 3.7, 3.7, sil, z=0.6)
        top, bot, mid = blade_pts(15.5, 44, 9.5, 'single', curve=11, tip_len=0.16)
        ray = lerp_pts(top, bot, 0.24)
        draw_blade(c, mm, top, bot, mid, 'single', z=1, extra=[(near(ray, 0.55, 0.06, 0.62), gold), (near(ray, 0.4, 0.66, 0.74), gold)])
        t2 = [(-x, -y) for x, y in top]; b2 = [(-x, -y) for x, y in bot]; m2 = [(-x, -y) for x, y in mid]
        moon = lerp_pts(t2, b2, 0.24)
        dots = []
        for k in (0.2, 0.36, 0.52):
            p = moon[int(k * (len(moon) - 1))]
            dots.append((disc(p[0], p[1], 0.9), M['w_frost_glow']))
        draw_blade(c, mm, t2, b2, m2, 'single', z=1, extra=[(near(moon, 0.45, 0.06, 0.6), sil)] + dots)
        _sun_disc(c, mm, (13.5, 0), 5.0, z=4)
        _moon_disc(c, mm, (-13.5, 0), 5.4, z=4)
        tassel(c, mm, (0, 3.0), strands=((0.6, 1.0), (0.1, 1.15), (-0.4, 1.0)), L=11, cols=(mm['felt'], mm['white'], mm['felt']), z=3)
    elif iid == 'gun_ay_ikizi_ay':
        # Gün-Ay İkizi (Ay duruşu): kabzadan ayrılmış iki hilal kılıç; öndeki güneş, arkadaki ay topuzlu
        gold, sil = mm['gold'], M['w_silver']
        for (ox, oy), z0, which in (((7, 10), -9, 'ay'), ((0, 0), 0, 'gun')):
            mat = B if z0 == 0 else mm['bd']
            grip(c, mm, -12 + ox, 1.5 + ox, 2.8, z=z0, y=oy, wrap='cord')
            top, bot, mid = blade_pts(4 + ox, 42, 8.4, 'single', curve=14, tip_len=0.18)
            top = shift_pts(top, 0, oy); bot = shift_pts(bot, 0, oy); mid = shift_pts(mid, 0, oy)
            inl = lerp_pts(top, bot, 0.24)
            draw_blade(c, mm, top, bot, mid, 'single', z=z0 + 1, fuller=False, mat=mat,
                       extra=[(near(inl, 0.5, 0.06, 0.6), gold if which == 'gun' else sil)])
            c.capsule((1.5 + ox, -3.6 + oy), (1.5 + ox, 3.6 + oy), 1.6, 1.6, gold if which == 'gun' else sil, z=z0 + 4)
            if which == 'gun':
                _sun_disc(c, mm, (-14.5 + ox, oy), 3.8, z=z0 + 2)
            else:
                _moon_disc(c, mm, (-14.5 + ox, oy), 4.0, z=z0 + 2)
    elif iid == 'kistin':
        # Kistin: kısa kayın sap, kurt başı topuz, kara demir zincir; ucunda tamga kazılı çivili top
        haft(c, mm, -15, 12, 2.9, bands=(9,))
        c.capsule((-13, 0), (-3, 0), 3.4, 3.4, G, z=1, paint=[(diag(4.0, 1.3, 0.8), mm['Gd'])])
        c.ellipse((-18.5, 0), 4.4, 3.7, A, z=1.5)
        c.poly([(-20.5, -2.6), (-23.5, -7.4), (-17.5, -3.4)], A, z=2.0, bevel=0.8, height=1.0)
        c.poly([(-15.5, -3.0), (-17.0, -7.8), (-13.5, -3.2)], mm['Ad'], z=1.8, bevel=0.8, height=1.0)
        c.poly([(-22.0, 0.6), (-25.5, 2.0), (-21.0, 2.6)], mm['Ad'], z=2.4, bevel=0.6, height=0.8)
        c.ellipse((-19.5, -1.2), 0.8, 0.8, M['eye_red'], z=8)
        c.capsule((11.5, 0), (15.5, 0), 3.4, 2.8, A, z=2)
        dk = M['w_dark_iron']
        x = 18.0
        for k in range(5):
            if k % 2 == 0:
                hole = (lambda lu, lv, px, py, x=x: ((px - x) / 2.3) ** 2 + (py / 0.95) ** 2 < 1.0)
                c.ellipse((x, 0), 3.9, 2.3, dk, z=3 + k * 0.2, paint=[(hole, M['black']), (dimples(3.0 + k, 3.0, 0.3, 'hi'), _shifted(dk, -1))])
            else:
                c.capsule((x - 3.4, 0), (x + 3.4, 0), 1.05, 1.05, _shifted(dk, 1), z=4.5)
            x += 6.0
        c.capsule((x - 3.0, 0), (x + 1.0, 0), 2.0, 2.4, dk, z=3)
        spiked_head(c, mm, x + 10.5, R=10.0, z=2)
        c.capsule((x + 10.5, -9.6), (x + 10.5, 9.6), 1.2, 1.2, mm['gold'], z=11.5)
        c.ellipse((x + 10.5, 0), 2.2, 2.2, M['eye_red'], z=14)
    elif iid == 'albasti_hanceri':
        # Albastı Hançeri: kara taş kabza, altın pençe siper, dalgalı kızıl ağızlı bıçak; topuzdan sarkan kızıl saç
        red = M['w_lacquer_r']
        obs = M['w_obsidian']
        for (ox, oy), z0 in (((6, 10), -10), ((0, 0), 0)):
            mat = B if z0 == 0 else mm['bd']
            c.capsule((-11 + ox, oy), (1.0 + ox, oy), 2.7, 2.6, obs, z=z0, paint=[(diag(3.4, 1.0, 0.8), _shifted(obs, 1))])
            c.ellipse((-12.8 + ox, oy), 3.0, 3.0, mm['gold'], z=z0 + 1)
            for k, (dx, dy) in enumerate(((3.5, -6.5), (5.0, -1.8), (3.5, 5.6))):
                c.tube([(1.0 + ox, oy + dy * 0.25), (2.5 + ox + dx * 0.4, oy + dy * 0.75), (1.5 + ox + dx, oy + dy)], 1.3, 0.5, mm['gold'], z=z0 + 4 + k * 0.2)
            top, bot, mid = blade_pts(3.5 + ox, 31, 7.6, 'single', curve=6, wave=1.3, tip_len=0.22)
            top = shift_pts(top, 0, oy); bot = shift_pts(bot, 0, oy); mid = shift_pts(mid, 0, oy)
            draw_blade(c, mm, top, bot, mid, 'single', z=z0 + 1, fuller=False, mat=mat,
                       extra=[(near(bot, 0.75, 0.04, 0.96, dy=-0.7), red), (near(lerp_pts(top, bot, 0.3), 0.4, 0.1, 0.7), mm['bd'])])
            tassel(c, mm, (-14.5 + ox, oy + 1.0), strands=((-0.5, 1.0), (-0.9, 1.15), (-1.3, 1.0), (-0.2, 1.1)), L=16,
                   cols=(red, _shifted(red, -1), red, _shifted(red, 1)), z=z0 + 0.5, knot=False)
    elif iid == 'cevgen':
        # Çevgen: bozkırın top oyunu çevgeninin savaş sopası; uzun kara değnek, sapa dik kızıl laklı tokmak (altın
        # bantlar, at başı uçlar), bilek kayışı ve rüzgârda uçuşan kurdeleler
        dw = M['w_dark_wood']
        shaft = [(-22, 1.2), (0, 0.6), (24, -0.2), (46, -1.0), (59, -1.8)]
        c.tube(shaft, 2.3, 1.9, dw, z=0, paint=[(grain(3.0, 0.6, 0.4), _shifted(dw, -1))])
        c.capsule((-21, 1.2), (-8, 0.8), 3.0, 2.8, G, z=0.8, paint=[(diag(4.0, 1.3, 0.8), mm['Gd'])])
        c.capsule((-24, 1.3), (-21.5, 1.2), 3.3, 3.3, A, z=1)
        c.tube([(-24, 2.0), (-29, 7.0), (-25, 11.0), (-21, 5.0)], 0.9, 0.9, mm['G'], z=-0.5)
        red = M['w_lacquer_r']
        hx_ = 62.0
        c.capsule((hx_, -12.5), (hx_, 12.5), 5.0, 5.0, red, z=2, paint=[(grain(2.4, 0.4, 0.2, axis='y'), _shifted(red, -1))])
        for y in (-8.5, 0.0, 8.5):
            c.capsule((hx_, y - 1.0), (hx_, y + 1.0), 5.6, 5.6, B, z=2.6, paint=[(dimples(2.0 + y, 3.0, 0.3, 'hi'), mm['bd'])])
        for sgn in (-1, 1):
            c.ellipse((hx_, sgn * 13.5), 5.0, 2.6, mm['gold'], z=3)
            c.poly([(hx_ - 2.5, sgn * 15.0), (hx_ + 3.5, sgn * 19.5), (hx_ + 5.5, sgn * 16.5), (hx_ + 2.5, sgn * 14.5)], mm['gold'], z=3.4, bevel=0.9, height=1.2)
            c.ellipse((hx_ + 3.0, sgn * 17.0), 0.7, 0.7, mm['black'], z=8)
        c.capsule((58, -1.8), (hx_ - 3.5, 0), 2.6, 2.8, A, z=4)
        for k, (m, dy) in enumerate(((mm['felt'], 2.0), (mm['white'], 4.0), (mm['turq'], 6.0))):
            c.tube([(55, 0), (50 - k * 2, 3 + dy), (44 - k * 3, 6 + dy * 1.4), (37 - k * 3, 7 + dy * 1.8)], 1.0, 0.6, m, z=1 + k * 0.2)
    elif iid == 'tatar_yayi':
        # Tatar Yayı: kurt başı oymalı kara kundak, boynuz-sinir kompozit yay, gergin kiriş, kurulu ağır ok, demir üzengi
        dw = M['w_dark_wood']
        stock = [(-22, -2.6), (-10, -3.4), (30, -2.8), (44, -2.4), (44, 2.4), (28, 3.0), (6, 3.4), (2.5, 9.5), (-2.5, 10.0),
                 (-6.5, 4.0), (-20, 4.8), (-25, 1.2)]
        inlay = [(near([(-16, -1.6), (-4, -2.0), (26, -1.6)], 0.45), mm['gold']), (grain(3.4, 0.6, 0.3), _shifted(dw, -1))]
        c.poly(stock, dw, z=0, bevel=1.6, height=2.6, paint=inlay)
        for bx in (8, 30):
            c.capsule((bx - 1.0, -3.4), (bx + 1.0, -3.4), 1.4, 1.4, A, z=2.4)
            c.capsule((bx, -3.5), (bx, 3.5), 1.2, 1.2, A, z=2.6)
        c.ellipse((-21.5, -0.4), 3.6, 3.2, A, z=2.5)
        c.poly([(-22.5, -2.6), (-25.5, -6.6), (-19.5, -3.2)], mm['Ad'], z=3.0, bevel=0.7, height=0.8)
        c.ellipse((-22.6, -1.0), 0.7, 0.7, M['eye_red'], z=8)
        c.capsule((2.5, 4.0), (4.5, 9.0), 1.0, 0.8, mm['iron'], z=2)
        pts = _limb_pts(19.0, 4.5, 6.0, grip_x=41.0)
        _limbs(c, pts, mm, M['w_lacquer_r'], 2.7, z=3, siyah=mm['bone'])
        nut = (16.0, -0.4)
        for e in (pts[0], pts[-1]):
            c.capsule((e[0] + 0.5, e[1]), nut, 0.7, 0.7, mm['string'], z=7)
        c.ellipse(nut, 1.8, 1.6, mm['iron'], z=6)
        c.capsule((15.0, -0.8), (46.0, -0.8), 1.25, 1.1, mm['W'], z=8, paint=[(grain(2.4, 0.4, 0.2), mm['Wd'])])
        hp = [(46.0, -3.0), (51.0, -2.0), (55.5, -0.8), (51.0, 0.4), (46.0, 1.4)]
        c.poly(hp, B, z=9, bevel=1.0, height=1.2, paint=[(near([hp[3], hp[2]], 0.5, dx=-0.4), mm['glint'])])
        for sgn in (-1, 1):
            c.poly([(17, -0.8), (21, -0.8 + sgn * 3.0), (25, -0.8 + sgn * 2.4), (24, -0.8)], mm['felt'], z=8.5, bevel=0.6, height=0.5)
        c.tube([(44, -2.0), (49.5, -5.2), (53, -0.4), (49.5, 4.4), (44, 2.0)], 1.0, 1.0, mm['iron'], z=1)
        tassel(c, mm, (-6, 4.5), strands=((0.4, 1.0), (0.0, 1.1)), L=8, cols=(mm['felt'], mm['turq']), z=2, knot=False)
    elif iid == 'tatar_oku':
        # Tatar Yayı'nın ağır oku (mermi sprite'ı): kısa kalın gövde, demir delici uç, keçe kanatçıklar
        c.capsule((-6, 0), (26, 0), 1.5, 1.3, mm['W'], z=0, paint=[(grain(2.4, 0.4, 0.2), mm['Wd'])])
        hp = [(25.0, -2.8), (31.0, -1.8), (36.5, 0.0), (31.0, 1.8), (25.0, 2.8)]
        c.poly(hp, B, z=1, bevel=1.0, height=1.4, paint=[(near([hp[3], hp[2]], 0.5, dx=-0.4), mm['glint'])])
        c.capsule((24.0, -2.0), (24.0, 2.0), 1.1, 1.1, A, z=2)
        for sgn in (-1, 1):
            c.poly([(-6, 0), (-2, sgn * 3.6), (4, sgn * 3.0), (3, 0)], mm['felt'], z=0.5, bevel=0.6, height=0.5)
    elif iid == 'kam_kuzgusu':
        # Kam Küzgüsü: kamın göğsündeki tunç ayna; malzeme renginde süslü çerçeve, parlak yüz, ortada güneş damgası,
        # kenarda çıngıraklar, sap halkasından sarkan çalama kurdeleleri
        haft(c, mm, -14, 4, 2.4, caps=True)
        c.capsule((-12, 0), (-3, 0), 2.8, 2.8, mm['cord'], z=0.8, paint=[(diag(3.0, 1.1, 0.8), mm['cordd'])])
        c.capsule((3.5, 0), (7.5, 0), 3.0, 2.6, A, z=1)
        cx = 21.5
        fr = [(ring(cx, 0, 12.6, 13.6), mm['bd']), (sectors(cx, 0, 16, 0.1, 0.5), mm['bl'])]
        c.ellipse((cx, 0), 14.8, 14.8, B, z=1, depth=0.22, paint=fr)
        sheen = [(near([(cx - 7, 7.5), (cx + 6, -8.0)], 1.2), mm['white']), (near([(cx - 3.5, 8.6), (cx + 8.2, -4.8)], 0.5), mm['white'])]
        c.ellipse((cx, 0), 11.8, 11.8, M['w_mirror'], z=2.6, depth=0.1, paint=sheen)
        for k in range(8):
            a = k / 8 * math.tau + 0.39
            c.poly([(cx + math.cos(a) * 3.2 - math.sin(a) * 1.1, math.sin(a) * 3.2 + math.cos(a) * 1.1),
                    (cx + math.cos(a) * 7.4, math.sin(a) * 7.4),
                    (cx + math.cos(a) * 3.2 + math.sin(a) * 1.1, math.sin(a) * 3.2 - math.cos(a) * 1.1)], mm['gold'], z=4.5, bevel=0.5, height=0.5)
        c.ellipse((cx, 0), 3.0, 3.0, mm['gold'], z=5)
        c.ellipse((cx, 0), 1.4, 1.4, mm['gem'], z=7.5)
        for k in range(7):
            a = -math.pi * 0.5 + (k - 3) * 0.42
            c.ellipse((cx + math.cos(a) * 16.4, math.sin(a) * 16.4), 1.7, 1.7, mm['gold'], z=3, depth=1.0)
        for k, (m, dx) in enumerate(((mm['felt'], -1.0), (mm['turq'], 0.6), (mm['gold'], 2.0), (mm['white'], 3.4))):
            c.tube([(5.5, 2.0), (5.0 + dx, 8.0), (4.0 + dx * 1.6, 14.0), (2.5 + dx * 2.2, 19.0)], 1.1, 0.7, m, z=-0.5 + k * 0.1)
    elif iid == 'tengri_bagi':
        # Tengri Bağı: gök demiri sap (mor ışıyan damar), ucunda büyük halka, halkanın içinde yüzen dört köşeli gök
        # taşı, halkadan sarkan kısa zincir ve hilal ağırlık
        sky = M['w_sky_iron']
        vein = wave_pts((-18, 0), (30, 0), 0.9, n=6, k=18)
        c.capsule((-20, 0), (30, 0), 2.5, 2.2, sky, z=0, paint=[(near(vein, 0.5, 0.02, 0.98), M['w_sky_vein']), (grain(3.0, 0.4, 0.2), _shifted(sky, -1))])
        c.capsule((-18, 0), (-8, 0), 3.0, 3.0, mm['cord'], z=0.8, paint=[(diag(3.0, 1.1, 0.8), mm['cordd'])])
        c.capsule((-22, 0), (-19.5, 0), 3.2, 3.2, A, z=1)
        c.capsule((28, 0), (32, 0), 3.0, 2.6, A, z=1)
        rcx = 44.0
        circ = [(rcx + math.cos(k / 32 * math.tau) * 11.0, math.sin(k / 32 * math.tau) * 11.0) for k in range(33)]
        c.tube(circ, 2.1, 2.1, B, z=2, paint=[(dimples(4.0, 3.0, 0.3, 'hi'), mm['bd'])])
        for k in range(4):
            a = k / 4 * math.tau + math.pi / 4
            c.ellipse((rcx + math.cos(a) * 11.0, math.sin(a) * 11.0), 1.6, 1.6, mm['gold'], z=5)
        st = []
        for k in range(8):
            a = k / 8 * math.tau - math.pi / 2
            r = 7.0 if k % 2 == 0 else 2.5
            st.append((rcx + math.cos(a) * r, math.sin(a) * r))
        c.poly(st, M['w_gem_sky'], z=4, bevel=1.2, height=1.6, paint=[(disc(rcx - 0.8, -1.0, 1.4), M['w_sky_vein'])])
        dk = M['w_dark_iron']
        y = 13.0
        for k in range(3):
            if k % 2 == 0:
                c.ellipse((rcx, y + 2.0), 1.9, 3.0, dk, z=3, paint=[(lambda lu, lv, px, py, yy=y: ((px - rcx) / 0.8) ** 2 + ((py - yy - 2.0) / 1.7) ** 2 < 1.0, M['black'])])
            else:
                c.capsule((rcx, y), (rcx, y + 4.0), 0.9, 0.9, _shifted(dk, 1), z=4)
            y += 3.6
        c.poly([(rcx - 4.5, y + 0.5), (rcx, y + 4.5), (rcx + 4.5, y + 0.5), (rcx, y + 2.4)], mm['gold'], z=3, bevel=0.8, height=1.0)
        tassel(c, mm, (30, 2.5), strands=((0.3, 1.0), (-0.2, 1.05)), L=9, cols=(mm['turq'], mm['white']), z=2)
    # ---------------------------------------------------------------- kalkanlar
    elif iid == 'yuvarlak_kalkan':
        pl = [(grain(6.0, 0.9, 0.2, axis='x'), mm['Wd']), (ring(0, 0, 13.5, 16.5), mm['felt']), (tri_row(13.5, 3.5, 6.0, up=True), mm['felt']),
              (ring(0, 0, 14.6, 15.4), mm['turq'])]
        shield(c, mm, R=24, face=W, face_paint=pl, boss_mat=mm['iron'])
    elif iid == 'kartal_kalkani':
        shield(c, mm, R=24, boss=False, face_paint=[(ring(0, 0, 17, 18.2), mm['bd'])])
        eag = [(-15, -1), (-9, -9), (-4, -5), (0, -11), (4, -5), (9, -9), (15, -1), (6, 1), (5, 9), (0, 14), (-5, 9), (-6, 1)]
        c.poly(eag, mm['gold'], z=12, bevel=1.4, height=1.8, paint=[(diag(2.6, 0.7, 0.5), _shifted(mm['gold'], -1))])
        c.ellipse((0, -6), 3.2, 3.2, mm['gold'], z=15)
        c.ellipse((1.0, -6.5), 0.8, 0.8, mm['black'], z=20)
        c.ellipse((0, 1), 3.4, 3.4, A, z=16, depth=1.0)
    elif iid == 'ayna_kalkan':
        mir = M['w_mirror']
        shield(c, mm, R=24, face=mir, rim=B, boss=False, rivet_n=12, face_paint=[(ring(0, 0, 9.5, 10.5), _shifted(mir, -1)), (ring(0, 0, 15.5, 16.5), _shifted(mir, -1))])
        c.ellipse((0, 0), 5.5, 5.5, B, z=9, depth=0.6)
        gem(c, mm, (0, 0), 2.6, z=16)
    elif iid == 'dikenli_kalkan':
        shield(c, mm, R=23, face=mm['iron'], rim=B, boss_mat=B, face_paint=[(dimples(4.0, 5.0, 0.3, 'hi'), _shifted(mm['iron'], -1)), (dimples(4.0, 5.0, 0.3, 'lo'), _shifted(mm['iron'], 1))])
        for k in range(8):
            a = k / 8 * math.tau
            dx, dy = math.cos(a), math.sin(a)
            c.poly([(dx * 20 - dy * 2.2, dy * 20 + dx * 2.2), (dx * 30, dy * 30), (dx * 20 + dy * 2.2, dy * 20 - dx * 2.2)], mm['iron'], z=14, bevel=1.0, height=1.4, tilt=(dx * 0.5, dy * 0.5))
        c.poly([(-2.5, -3), (0, -0.5), (2.5, -3), (0, 0)], mm['iron'], z=20, bevel=0.5, height=1)
        c.ellipse((0, 0), 2.8, 2.8, mm['iron'], z=22, depth=1.6)
    elif iid == 'kut_kalkani':
        nb = M['nazar_b']
        shield(c, mm, R=24, face=nb, rim=B, boss=False, face_paint=[(ring(0, 0, 16, 17), _shifted(nb, 1))])
        kut = mm['kut']
        for k in range(8):
            a = k / 8 * math.tau
            c.capsule((math.cos(a) * 7, math.sin(a) * 7), (math.cos(a) * 14, math.sin(a) * 14), 1.4, 0.7, kut, z=12)
        c.ellipse((0, 0), 7.5, 7.5, A, z=13, depth=0.4)
        c.ellipse((0, 0), 5.0, 5.0, kut, z=16, depth=1.0)
    elif iid == 'ejder_kalkani':
        red = Mat(ramp(4, 0.8, 0.6), name='kızıl deri')
        shield(c, mm, R=24, face=red, rim=B, boss=False, face_paint=[(ring(0, 0, 16.5, 17.6), _shifted(red, -1))])
        amb = M['w_gem_amber']
        body = [(-13, 4), (-8, -4), (-2, -8), (3, -2), (8, -9), (13, -3), (11, 4)]
        c.tube(body, 2.8, 2.2, amb, z=12)
        c.ellipse((13, -4), 3.4, 2.8, amb, z=14)
        c.ellipse((14, -5), 0.9, 0.9, mm['black'], z=20)
        for x, y in body[1:5]:
            c.poly([(x - 1.5, y - 2), (x + 1.5, y - 2), (x, y - 6)], amb, z=13, bevel=0.5, height=0.6)
        c.ellipse((0, 6), 3.0, 3.0, A, z=16, depth=1.0)
    elif iid == 'ulu_kayin_kalkani':
        bark = M['w_bark']
        shield(c, mm, R=24, face=bark, rim=B, boss=False, face_paint=[(grain(3.4, 0.8, 0.8, axis='y'), _shifted(bark, -1))])
        moss = M['moss']
        for k in range(5):
            a = -1.4 + k * 0.7
            c.capsule((0, 8), (math.sin(a) * 14, 8 - math.cos(a) * 18), 1.8, 1.0, moss, z=12)
            c.ellipse((math.sin(a) * 14, 8 - math.cos(a) * 18), 2.6, 1.8, M['leaf'], z=13, rot=a)
        c.ellipse((0, 8), 4.0, 4.0, bark, z=14, depth=1.0)
        gem(c, mm, (0, 8), 1.8, z=20, mat=mm['kut'])
    elif iid == 'tas_kalkan':
        st = M['w_rock']
        shield(c, mm, R=24, face=st, rim=M['w_rock_d'], boss=False, rivet_n=0, face_paint=[(dimples(5.0, 6.0, 0.3, 'hi'), M['w_rock_d'])])
        c.poly([(-10, -10), (10, -10), (12, 8), (-12, 8)], M['w_rock_d'], z=10, bevel=1.6, height=1.6)
        c.poly([(-7, -2), (-3, -2), (-5, 2)], st, z=13, bevel=0.5, height=0.6); c.poly([(3, -2), (7, -2), (5, 2)], st, z=13, bevel=0.5, height=0.6)
        c.capsule((-4, 5), (4, 5), 1.0, 1.0, M['w_rock_d'], z=13)
        c.ellipse((-5, -1), 1.4, 1.4, M['eye_red'], z=20); c.ellipse((5, -1), 1.4, 1.4, M['eye_red'], z=20)
        c.ellipse((0, 14), 3.2, 3.2, B, z=14, depth=1.0)
    # ---------------------------------------------------------------- aygıtlar / tılsımlar
    elif iid == 'kara_barut':
        # barut kesesi: deri torba, kıvrımlar, boğaz ipi, fitil ve kor
        c.ellipse((0, 5), 15, 13, G, z=0, depth=0.5, paint=[(near([(-9, 14), (-6, 4), (-7, -4)], 0.6), mm['Gd']), (near([(4, 15), (6, 6), (4, -3)], 0.6), mm['Gd']), (near([(-9, 14), (-6, 4), (-7, -4)], 0.5, dx=1.1), _shifted(G, 1))])
        c.capsule((0, -7), (0, -13), 5.0, 3.2, G, z=2, paint=[(grain(2.4, 0.6, 0.3, axis='y'), mm['Gd'])])
        c.capsule((-5.5, -8), (5.5, -8), 1.4, 1.4, mm['cord'], z=5, paint=[(diag(2.4, 0.9, 0.0), mm['cordd'])])
        c.capsule((0, -13), (6, -20), 1.3, 1.0, mm['bone'], z=3)
        c.ellipse((6.8, -21), 2.6, 2.6, mm['ember'], z=5)
        c.ellipse((7.2, -21.4), 1.1, 1.1, M['flower_y'], z=6)
        c.ellipse((-5, 4), 2.6, 2.6, A, z=6, depth=0.8)
    elif iid == 'bozkurt_cagrisi':
        # bozkurt çağrısı: ak kurt başı totemi, kut gözler
        fur, furd = mm['white'], M['fur_dark']
        c.poly([(-13, -8), (-9, -22), (-2, -10)], fur, z=1, bevel=1.4, height=1.4)
        c.poly([(2, -10), (9, -22), (13, -8)], fur, z=1, bevel=1.4, height=1.4)
        c.poly([(-10, -9), (-8, -18), (-3, -10)], furd, z=2, bevel=0.8, height=0.6)
        c.poly([(3, -10), (8, -18), (10, -9)], furd, z=2, bevel=0.8, height=0.6)
        c.ellipse((0, 0), 16, 15, fur, z=3, depth=0.5, paint=[(diag(3.2, 0.8, -1.4), _shifted(fur, -1)), (disc(0, -2, 9), fur)])
        c.capsule((0, 2), (0, 11), 5.4, 3.6, furd, z=12)
        c.ellipse((0, 12.5), 2.4, 1.8, mm['black'], z=16)
        for sx in (-1, 1):
            c.ellipse((sx * 6, -3), 3.0, 2.2, mm['black'], z=14, rot=sx * 0.35)
            c.ellipse((sx * 6, -3), 2.0, 1.4, mm['kut'], z=15, rot=sx * 0.35)
            c.capsule((sx * 3, 9), (sx * 4, 14), 0.8, 0.6, mm['bone'], z=14)
    elif iid == 'nazar_boncugu':
        nb = M['nazar_b']
        c.ellipse((0, 0), 16, 16, nb, z=0, depth=0.6, paint=[(disc(0, 0, 11.5), M['nazar_w']), (disc(0, 0, 7.6), M['nazar_l']), (disc(0, 0, 3.8), mm['black'])])
        c.ellipse((-4.5, -5.5), 1.8, 1.4, M['nazar_w'], z=14, rot=-0.6)
        c.capsule((0, -16), (0, -20), 1.6, 1.6, A, z=4)
        c.ellipse((0, -22), 2.6, 2.6, A, z=4, paint=[(disc(0, -22, 1.2), mm['black'])])
    elif iid == 'od_testisi':
        clay = M['w_clay']
        c.ellipse((0, 4), 13, 14, clay, z=0, depth=0.5, paint=[(ring(0, 4, 6.5, 8.5, ry=1.08), mm['turq']), (ring(0, 4, 7.0, 7.9, ry=1.08), M['nazar_w']), (grain(4.0, 0.6, 0.0, axis='x'), _shifted(clay, -1))])
        c.capsule((0, -8), (0, -16), 4.4, 5.2, clay, z=1)
        c.capsule((0, -16.5), (0, -15.5), 5.6, 5.6, _shifted(clay, -1), z=2)
        c.capsule((11, -4), (15, -12), 1.8, 1.8, clay, z=1); c.capsule((15, -12), (5, -15), 1.8, 1.6, clay, z=1)
        c.capsule((0, -17), (0, -20), 1.2, 1.0, mm['cord'], z=3)
        c.poly([(-4, -19), (4, -19), (3, -24), (1, -29), (-1, -25), (-3, -23)], mm['ember'], z=3, bevel=1.2, height=1.2)
        c.poly([(-1.5, -20), (1.5, -20), (0.5, -25)], M['flower_y'], z=4, bevel=0.5, height=0.5)
    elif iid == 'sifa_muskasi':
        # şifa muskası: deri üçgen kese, altın kenar, kut işareti, ip
        c.poly([(-13, -14), (13, -14), (13, 8), (0, 18), (-13, 8)], G, z=0, bevel=2.0, height=2.4, paint=[(diag(3.4, 0.8, 0.0), mm['Gd'])])
        c.poly([(-13, -14), (13, -14), (13, -10), (-13, -10)], mm['gold'], z=3, bevel=1.0, height=1.0)
        c.capsule((-6, -18), (6, -18), 1.3, 1.3, mm['cord'], z=1, paint=[(diag(2.4, 0.9, 0.0), mm['cordd'])])
        c.capsule((-6, -18), (-6, -13), 1.1, 1.1, mm['cord'], z=1); c.capsule((6, -18), (6, -13), 1.1, 1.1, mm['cord'], z=1)
        c.ellipse((0, -1), 6.0, 6.0, mm['kut'], z=5, depth=0.5)
        c.capsule((0, -6), (0, 4), 1.3, 1.3, M['nazar_w'], z=9); c.capsule((-5, -1), (5, -1), 1.3, 1.3, M['nazar_w'], z=9)
        rivets(c, mm, [(-10, 4), (10, 4), (0, 13)], 1.2, 8, A)
    elif iid == 'ayaz_tilsimi':
        ice, glow_ = M['w_frost'], M['w_frost_glow']
        body = [(0, -22), (9, -6), (16, 0), (9, 6), (0, 22), (-9, 6), (-16, 0), (-9, -6)]
        c.poly(body, ice, z=0, bevel=2.2, height=3.0)
        c.poly([(0, -20), (8, -6), (0, -2), (-8, -6)], ice, z=3.2, bevel=0.01, height=0, tilt=(0, -0.6))
        c.poly([(0, 2), (8, 6), (0, 20), (-8, 6)], ice, z=3.2, bevel=0.01, height=0, tilt=(0, 0.6))
        c.poly([(-15, 0), (-8, -5), (-1, 0), (-8, 5)], ice, z=3.2, bevel=0.01, height=0, tilt=(-0.6, 0))
        c.poly([(1, 0), (8, -5), (15, 0), (8, 5)], ice, z=3.2, bevel=0.01, height=0, tilt=(0.6, 0))
        c.ellipse((0, 0), 4.0, 4.0, glow_, z=6, depth=0.5)
        c.capsule((0, -22), (0, -26), 2.2, 1.8, M['w_silver'], z=4)
        c.ellipse((0, -29), 3.0, 3.0, M['w_silver'], z=4, paint=[(disc(0, -29, 1.4), mm['black'])])
    elif iid == 'yel_tilsimi':
        tq = mm['turq']
        c.ellipse((0, 0), 17, 17, mm['gold'], z=0, depth=0.1)
        c.ellipse((0, 0), 14, 14, tq, z=1, depth=0.3)
        for k in range(3):
            a0 = k * math.tau / 3
            pts = [(math.cos(a0 + t * 0.28) * (3 + t * 1.3), math.sin(a0 + t * 0.28) * (3 + t * 1.3)) for t in range(8)]
            for a_, b_ in zip(pts, pts[1:]):
                c.capsule(a_, b_, 1.5, 1.5, M['nazar_w'], z=8)
        for k in range(3):
            a = math.pi / 2 + (k - 1) * 0.7
            p = (math.cos(a) * 17, math.sin(a) * 17)
            c.capsule(p, (p[0] + math.cos(a) * 5, p[1] + math.sin(a) * 5), 0.8, 0.6, mm['cord'], z=1)
            c.poly([(p[0] + math.cos(a) * 4 - 2, p[1] + math.sin(a) * 4), (p[0] + math.cos(a) * 12, p[1] + math.sin(a) * 12 + 1), (p[0] + math.cos(a) * 4 + 2, p[1] + math.sin(a) * 4)], mm['white'], z=1, bevel=0.8, height=0.6)
    elif iid == 'davul_totemi':
        c.capsule((0, 10), (0, 24), 2.8, 2.8, W, z=0, paint=[(grain(3.0, 0.7, 0.4, axis='y'), mm['Wd'])])
        skin = Mat(ramp(36, 0.35, 0.86, spread=0.35), name='davul derisi')
        c.ellipse((0, -2), 18, 12.5, W, z=1, depth=0.1)
        c.ellipse((0, -2), 15.5, 10.5, skin, z=2, depth=0.1, paint=[(ring(0, -2, 4.5, 5.6, ry=0.72), M['red_paint']), (sectors(0, -2, 12, 0.0, 0.25), _shifted(skin, -1)), (disc(0, -2, 4.4), skin), (ring(0, -2, 9.5, 10.3, ry=0.72), M['red_paint'])])
        for k in range(8):
            a = k / 8 * math.tau
            c.capsule((math.cos(a) * 5.8, -2 + math.sin(a) * 4.2), (math.cos(a) * 8.5, -2 + math.sin(a) * 6.2), 0.8, 0.5, M['red_paint'], z=4)
        rivets(c, mm, [(math.cos(k / 10 * math.tau) * 17, -2 + math.sin(k / 10 * math.tau) * 11.6) for k in range(10)], 1.0, 8, A)
        for k in range(3):
            m = [mm['felt'], M['nazar_w'], mm['turq']][k]
            c.capsule((-8 + k * 8, -14), (-7 + k * 8, -25), 1.3, 0.8, m, z=4, paint=[(grain(1.8, 0.5, 0.0, axis='y'), _shifted(m, -1))])
    elif iid == 'ok_yagmuru':
        # sadak: çapraz deri tüp, beş ok
        c.capsule((-6, 14), (6, -4), 7.5, 6.5, G, z=0, paint=[(diag(3.2, 0.9, 0.0), mm['Gd']), (near([(-9, 8), (3, -4)], 0.7, dy=2.0), mm['felt'])])
        c.capsule((5, -5), (7, -3), 7.0, 7.0, mm['Gd'], z=0.5)
        c.capsule((-11, 7), (-2, 0), 1.6, 1.6, mm['cord'], z=4)
        for k in range(5):
            x = -7 + k * 3.2
            a = -1.35 + k * 0.1
            _arrow(c, mm, a, 14 + (k % 2) * 3, z=2 + k * 0.1, x0=x + 1, y0=-2, head=mm['iron'])
    elif iid == 'kartal_cagrisi':
        nb = M['nazar_b']
        c.ellipse((0, 0), 17, 17, mm['gold'], z=0, depth=0.15, paint=[(ring(0, 0, 14.5, 15.5), _shifted(mm['gold'], -1))])
        c.ellipse((0, 0), 14, 14, nb, z=1, depth=0.2)
        eag = [(-12, 0), (-7, -7), (-3, -3), (0, -9), (3, -3), (7, -7), (12, 0), (5, 2), (4, 8), (0, 12), (-4, 8), (-5, 2)]
        c.poly(eag, mm['gold'], z=8, bevel=1.2, height=1.6, paint=[(diag(2.4, 0.7, 0.5), _shifted(mm['gold'], -1))])
        c.ellipse((0, -4), 2.8, 2.8, mm['gold'], z=10)
        c.ellipse((0.8, -4.5), 0.8, 0.8, mm['black'], z=14)
        c.capsule((0, -17), (0, -21), 1.4, 1.4, A, z=2)
        rivets(c, mm, [(math.cos(k / 8 * math.tau) * 15.7, math.sin(k / 8 * math.tau) * 15.7) for k in range(8)], 1.0, 6, A)
    elif iid == 'ruh_kusu':
        kut, core = mm['kut'], M['w_spirit_core']
        c.poly([(-24, -3), (-9, -8), (-5, 2), (-18, 7)], kut, z=1, bevel=2.0, height=2.0, paint=[(near([(-22, -2), (-8, -5)], 0.6), core), (near([(-19, 4), (-8, -1)], 0.6), core)])
        c.poly([(24, -3), (9, -8), (5, 2), (18, 7)], kut, z=1, bevel=2.0, height=2.0, paint=[(near([(22, -2), (8, -5)], 0.6), core), (near([(19, 4), (8, -1)], 0.6), core)])
        c.ellipse((0, 2), 12, 9, kut, z=2, depth=0.5)
        c.poly([(-4, 8), (-12, 18), (-2, 14), (0, 20), (2, 14), (12, 18), (4, 8)], kut, z=1, bevel=1.4, height=1.0)
        c.ellipse((8, -6), 5.0, 5.0, core, z=4, depth=0.6)
        c.ellipse((9.5, -7), 1.3, 1.3, mm['black'], z=8)
        c.poly([(12, -6), (18, -4.5), (12, -3)], M['w_gem_amber'], z=7, bevel=0.5, height=0.5)
    elif iid == 'umay_tuyu':
        q = [(-12, 16), (12, -16)]
        c.poly([(-12, 12), (-4, -8), (8, -20), (14, -12), (6, 4), (-6, 16)], M['nazar_w'], z=1, bevel=2.0, height=1.6,
               paint=[(diag(2.6, 0.7, 1.2), _shifted(M['nazar_w'], -1)), (near(q, 0.6), mm['gold'])])
        c.capsule((-12, 16), (-15, 20), 1.0, 0.7, mm['gold'], z=3)
        c.ellipse((10, -18), 3.2, 3.2, mm['kut'], z=5, depth=0.6)
        c.ellipse((-15.5, 21), 1.8, 1.8, A, z=4)
    elif iid == 'kartal_tuyleri':
        for k in range(3):
            y = -10 + k * 10
            vane = [(-9, y - 4), (16, y - 8), (22, y - 4), (16, y + 1), (-9, y + 4)]
            m = mm['white']
            c.poly(vane, m, z=k * 3, bevel=1.4, height=1.2, paint=[(diag(2.4, 0.6, -0.8), _shifted(m, -1)), (box(13, y - 10, 24, y + 4), M['fur_dark']), (near([(-9, y), (22, y - 4)], 0.6), mm['bone'])])
            c.capsule((-12, y + 0.5), (-8, y), 0.9, 0.9, mm['bone'], z=k * 3 + 1)
        c.capsule((-6, -14), (-6, 14), 1.4, 1.4, mm['cord'], z=12, paint=[(diag(2.4, 0.9, 0.0), mm['cordd'])])
    elif iid == 'mancinik_tasi':
        rock, rd = M['w_rock'], M['w_rock_d']
        c.poly([(-18, -8), (-10, -16), (6, -18), (18, -10), (20, 4), (12, 16), (-6, 18), (-18, 10)], rock, z=0, bevel=3.0, height=4.0,
               paint=[(dimples(6.0, 5.0, 0.3, 'hi'), rd), (near([(-10, -8), (-2, -2), (4, 8), (3, 14)], 0.7), rd), (near([(2, -14), (8, -6), (16, -2)], 0.6), rd)])
        c.poly([(-6, -14), (6, -16), (8, -8), (-4, -6)], rock, z=4.2, bevel=0.01, height=0, tilt=(0, -0.6))
        for a_, b_ in (((-16, -10), (16, -8)), ((-18, 10), (18, 8))):
            c.capsule(a_, b_, 1.6, 1.6, mm['cord'], z=5, paint=[(diag(2.4, 0.9, -0.5), mm['cordd'])])
        c.ellipse((0, 0), 2.2, 2.2, mm['cordd'], z=7)
    elif iid == 'erlik_zinciri':
        dk = M['w_dark_iron']
        for k in range(6):
            a = k * 0.42 - 1.0
            x = -22 + k * 8.4
            y = math.sin(a) * 6
            m = mm['iron'] if k % 2 else _shifted(mm['iron'], -1)
            hole = (lambda lu, lv, px, py, x=x, y=y, a=a: (((px - x) * math.cos(a) + (py - y) * math.sin(a)) / 6.2) ** 2 + ((-(px - x) * math.sin(a) + (py - y) * math.cos(a)) / 4.0) ** 2 < 0.28)
            c.ellipse((x, y), 6.2, 4.0, m, z=(k % 2) * 3, rot=a, paint=[(hole, M['black']), (dimples(2.0 + k, 4.0, 0.3, 'hi'), _shifted(m, -1))])
        c.capsule((22, -2), (28, -1), 2.2, 2.6, dk, z=5)
        c.poly([(28, -6), (34, -2), (37, 7), (30, 10), (25, 3)], M['w_corrupt'], z=6, bevel=1.6, height=2.0)
        c.poly([(29, -4), (32, -2), (31, 4)], M['w_corrupt'], z=8.5, bevel=0.01, height=0, tilt=(-0.5, -0.4))
    # ---------------------------------------------------------------- âletler / asalar
    elif iid == 'kam_kopuzu':
        dark = M['w_dark_wood']
        c.ellipse((8, 0), 15, 11, W, z=0, depth=0.5, paint=[(grain(3.4, 0.7, 0.3, axis='x'), mm['Wd'])])
        c.ellipse((8, 0), 13, 9, Mat(ramp(28, 0.5, 0.78, spread=0.3), name='göğüs tahtası'), z=1, depth=0.12, paint=[(grain(2.6, 0.5, 0.2), mm['Wd'])])
        c.ellipse((6, 0), 3.6, 3.0, dark, z=3)
        c.capsule((20, -1), (56, -8), 2.6, 2.2, W, z=1, paint=[(grain(2.6, 0.6, 0.3), mm['Wd'])])
        c.capsule((56, -8), (62, -12), 2.4, 1.8, dark, z=1.5)
        c.capsule((16, 2), (16, -4), 1.0, 1.0, dark, z=4)
        for y in (-2.0, 0.0, 2.0):
            c.capsule((-4, y), (57, y - 7.5), 0.4, 0.4, mm['string'], z=5)
        for x in (54, 58):
            c.ellipse((x, -13.5), 1.5, 1.5, A, z=4)
        tassel(c, mm, (-6, 1), strands=((0.5, 1.0), (0.0, 1.1), (-0.4, 1.0)), L=9, cols=(mm['felt'], mm['turq'], mm['gold']), z=2)
    elif iid == 'gok_asasi':
        haft(c, mm, -26, 44, 2.6, caps=True)
        bark = M['w_bark']
        for k in range(3):
            a = -1.3 + k * 1.3
            c.capsule((44, 0), (50 + math.cos(a) * 9, math.sin(a) * 9 - 4), 2.0, 1.1, bark, z=1)
        c.ellipse((52, -6), 7.0, 7.0, mm['kut'], z=4, depth=0.7, paint=[(disc(49.5, -8.5, 2.0), M['w_spirit_core'])])
        c.poly([(52, -19), (48, -8), (54, -10), (50, 0)], M['nazar_w'], z=12, bevel=0.6, height=0.6)
        c.ellipse((40, -4), 2.0, 2.0, A, z=4)
        tassel(c, mm, (40, 2), strands=((0.3, 1.0), (-0.2, 1.05)), L=8, cols=(mm['felt'], mm['turq']), z=2)
    elif iid == 'kayin_asasi':
        # Ulu Kayın Asası: ak kayın sap (lentisel çizikler), uçta kök düğümü içinde kut taşı, yapraklar
        birch = M['w_birch']
        marks = []
        for x in (-20, -11, -1, 10, 20, 30, 40, 50):
            marks.append((near([(x, -1.4), (x + 2.2, 1.2)], 0.5), mm['black']))
        c.capsule((-26, 0), (60, 0), 3.0, 2.6, birch, z=0, paint=marks + [(grain(3.0, 0.5, 0.2), _shifted(birch, -1))])
        bark = M['w_bark']
        for a in (-1.0, -0.35, 0.35, 1.0):
            c.capsule((60, 0), (70 + math.cos(a) * 7, math.sin(a) * 9), 2.4, 1.3, bark, z=2, paint=[(grain(2.0, 0.5, 0.2), _shifted(bark, -1))])
        c.ellipse((70, 0), 6.0, 6.0, mm['kut'], z=4, depth=0.7, paint=[(disc(68, -2, 1.8), M['w_spirit_core'])])
        for a in (-1.6, 1.6, -2.4, 2.4):
            c.ellipse((66 + math.cos(a) * 12, math.sin(a) * 12), 4.4, 2.6, M['leaf'], z=1, rot=a, paint=[(near([(66 + math.cos(a) * 8, math.sin(a) * 8), (66 + math.cos(a) * 16, math.sin(a) * 16)], 0.5), _shifted(M['leaf'], -1))])
    elif iid == 'yel_borusu':
        horn_pts = [(-12, 2), (0, 0), (14, -2), (28, -7), (38, -14)]
        rs = [3.0, 3.6, 4.4, 5.6, 7.0]
        hm = mm['horn']
        c.tube(horn_pts, rs[0], rs[-1], hm, z=0, paint=[(grain(3.2, 0.7, 0.3), _shifted(hm, -1)), (band(-1.0, -0.55, 'v'), _shifted(hm, -1))])
        c.ellipse((40, -16), 8.4, 6.6, hm, z=1, rot=-0.6)
        c.ellipse((40.5, -16.5), 5.6, 4.0, M['black'], z=2, rot=-0.6)
        for i, x in enumerate((-4, 12, 26)):
            y = np.interp(x, [p[0] for p in horn_pts], [p[1] for p in horn_pts])
            c.capsule((x - 1.2, y), (x + 1.2, y), rs[i + 1] + 0.6, rs[i + 1] + 0.6, A, z=1)
        c.capsule((-12, 2), (-15, 2.6), 2.0, 1.6, A, z=1)
        tassel(c, mm, (-10, 4), strands=((0.4, 1.0), (0.0, 1.1), (-0.4, 1.0)), L=10, cols=(mm['felt'], mm['turq'], mm['gold']), z=2)


def _sun_disc(c, mm, p, r, z=4.0):
    """v27 Gün-Ay İkizi: altın güneş siperi (disk + sekiz sivri ışın + ortada kızıl taş)."""
    gold = mm['gold']
    for k in range(8):
        a = k / 8 * math.tau + math.pi / 8
        ca, sa = math.cos(a), math.sin(a)
        c.poly([(p[0] + ca * r * 0.8 - sa * 1.3, p[1] + sa * r * 0.8 + ca * 1.3), (p[0] + ca * (r + 3.6), p[1] + sa * (r + 3.6)),
                (p[0] + ca * r * 0.8 + sa * 1.3, p[1] + sa * r * 0.8 - ca * 1.3)], gold, z=z, bevel=0.6, height=0.8)
    c.ellipse(p, r, r, gold, z=z + 0.5, paint=[(ring(p[0], p[1], r - 1.6, r - 0.9), _shifted(gold, -1))])
    c.ellipse(p, 1.7, 1.7, M['w_gem_ruby'], z=z + r + 1.5)


def _moon_disc(c, mm, p, r, z=4.0):
    """v27 Gün-Ay İkizi: gümüş hilal siperi (bıçağa açılan hilal + ortada inci)."""
    sil = M['w_silver']
    pts = []
    for i in range(25):
        a = math.radians(-145 + 290 * i / 24)
        pts.append((p[0] + math.cos(a) * r, p[1] + math.sin(a) * r))
    ic = (p[0] - r * 0.55, p[1])
    for i in range(25):
        a = math.radians(145 - 290 * i / 24)
        pts.append((ic[0] + math.cos(a) * r * 0.78, ic[1] + math.sin(a) * r * 0.78))
    c.poly(pts, sil, z=z, bevel=1.0, height=1.6, paint=[(near(pts[2:23], 0.45, dx=-0.6), _shifted(sil, 1))])
    c.ellipse((p[0] + r * 0.35, p[1]), 1.5, 1.5, M['w_white'], z=z + 3)


ORDER = ['alp_kilici', 'pala', 'yatagan', 'gurz', 'teber', 'kargi', 'ikiz_bicak', 'turk_yayi', 'akinci_yayi', 'cirit', 'coban_sapani',
         'yuvarlak_kalkan', 'kartal_kalkani', 'ayna_kalkan', 'kara_barut', 'bozkurt_cagrisi', 'nazar_boncugu', 'od_testisi',
         'yildirim_kilici', 'savas_baltasi', 'kement', 'od_kamcisi', 'civili_topuz', 'erlik_tirpani', 'kurt_pencesi', 'ayaz_kilici',
         'saganak_yayi', 'tufan_yayi', 'od_oklari', 'kam_kopuzu', 'gok_asasi', 'yel_borusu', 'kartal_tuyleri', 'mancinik_tasi',
         'dikenli_kalkan', 'kut_kalkani', 'ejder_kalkani', 'ulu_kayin_kalkani', 'tas_kalkan',
         'sifa_muskasi', 'ayaz_tilsimi', 'yel_tilsimi', 'davul_totemi', 'ok_yagmuru', 'kartal_cagrisi', 'ruh_kusu', 'umay_tuyu', 'erlik_zinciri',
         'ulu_kilic', 'dag_cekici', 'ruh_kilici', 'ay_palasi', 'yilan_kilici', 'kor_cekici', 'ruzgar_kilici',
         'tulpar_mizragi', 'bori_hanceri', 'ikiz_balta', 'kayin_asasi', 'bozgun_kilici',
         'gun_ay_ikizi', 'gun_ay_ikizi_ay', 'kistin', 'albasti_hanceri', 'cevgen', 'tatar_yayi', 'tatar_oku', 'kam_kuzgusu',
         'tengri_bagi']


def centered(iid):
    return iid in ('yuvarlak_kalkan', 'kartal_kalkani', 'ayna_kalkan', 'kara_barut', 'bozkurt_cagrisi', 'nazar_boncugu', 'od_testisi',
                   'dikenli_kalkan', 'kut_kalkani', 'ejder_kalkani', 'ulu_kayin_kalkani', 'tas_kalkan', 'mancinik_tasi', 'kartal_tuyleri',
                   'sifa_muskasi', 'ayaz_tilsimi', 'yel_tilsimi', 'davul_totemi', 'ok_yagmuru', 'kartal_cagrisi', 'ruh_kusu', 'umay_tuyu', 'erlik_zinciri',
                   'gun_ay_ikizi')


def pivot_of(iid):
    return CPIVOT if centered(iid) else PIVOT


def render_item(iid, mid):
    pv = pivot_of(iid)
    c = WCanvas(CELL[0], CELL[1], pv[0], pv[1])
    mm = mats_for(mid)
    draw_item(c, iid, mm)
    rgba = c.shade()
    # ruh: bıçak/başlık yarı saydam (içi oyunda _e katmanıyla ışır)
    if mid == 'ruh':
        for k, m in enumerate(c.mats):
            if m is mm['b'] or m is mm['bd'] or m is mm['bl']:
                sel = c.mat == k
                rgba[sel, 3] = 0.78
    return c, rgba, c.normal_map(rgba[..., 3]), pv


def build_atlas():
    import raster
    N = raster.SS  # HD paketi: fiziksel hücre büyür, meta mantıksal kalır
    cw, ch = int(CELL[0] * N), int(CELL[1] * N)
    mids = [m['id'] for m in ITEMS['materials']]
    H, Wd = len(ORDER) * ch, len(mids) * cw
    alb = np.zeros((H, Wd, 4)); nrm = np.zeros_like(alb); glo = np.zeros_like(alb)
    meta = {'cell': list(CELL), 'texel': TEX, 'materials': mids, 'items': {}}
    for r, iid in enumerate(ORDER):
        for k, mid in enumerate(mids):
            c, rgba, nm, pv = render_item(iid, mid)
            ys, xs = slice(r * ch, (r + 1) * ch), slice(k * cw, (k + 1) * cw)
            alb[ys, xs] = rgba; nrm[ys, xs] = nm
            em = c.emis
            glo[ys, xs, :3] = np.clip(em, 0, 1); glo[ys, xs, 3] = (em.max(axis=2) > 0)
        meta['items'][iid] = {'row': r, 'pivot': list(pivot_of(iid))}
    return alb, nrm, glo, meta
