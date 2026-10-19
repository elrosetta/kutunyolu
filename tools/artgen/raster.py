"""Sanat üreteci — Dead Cells tarzı cel gölgelendirmeli piksel sanat rasterleştiricisi.

Şekiller yükseklik alanı olarak çizilir (kapsül, elips, eğimli çokgen). Sonra:
  * 3 sert ton (gölge / ana / ışık) + metallerde parlama: yumuşak geçiş ve titreme yok,
  * normaller içeride düzleştirilir: yüzeyler düz kalır, sadece kenarlar döner,
  * desenler (kilim süsü, kürk tüyü, ahşap damarı) piksel başına malzeme değiştirerek eklenir,
  * renkli seçici kontur ve ince kenar ışığı eklenir,
  * Godot'nun 2D ışıkları için normal map üretilir.
"""
import colorsys
import numpy as np
from PIL import Image


def hx(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255.0


def _lerp_hue(h, target, amt):
    d = ((target - h + 180) % 360) - 180
    return (h + d * amt) % 360


def ramp(hue, sat=0.7, val=0.75, n=5, spread=0.5, shift=0.5):
    """Cel rampası: [derin gölge, gölge, ana, ışık, parlama].
    Gölgeler mora/maviye kayar ve doygunlaşır, ışıklar sarıya kayar ve açılır."""
    cols = []
    offs = [-2.0, -1.0, 0.0, 1.0, 1.9][:n]
    for o in offs:
        if o < 0:
            h = _lerp_hue(hue, 255, shift * 0.22 * -o)
            s = min(1.0, sat * (1 + 0.12 * -o))
            v = val * (1 - spread * 0.36 * -o)
        else:
            h = _lerp_hue(hue, 55, shift * 0.16 * o)
            s = sat * (1 - 0.18 * o)
            v = min(1.0, val + (1 - val) * 0.55 * o + spread * 0.08 * o)
        cols.append(np.array(colorsys.hsv_to_rgb(h / 360, max(0, min(1, s)), max(0, min(1, v)))))
    return cols


def flat(hexcol):
    c = hx(hexcol)
    return [c * 0.6, c * 0.8, c, np.minimum(1, c * 1.15), np.minimum(1, c * 1.3)]


def shift(a, dy, dx, fill):
    """Kenarda dönmeyen kaydırma: taşan kısım fill ile dolar (np.roll sarar, bu sarmaz)."""
    out = np.full_like(a, fill)
    h, w = a.shape[:2]
    ys = slice(max(dy, 0), h + min(dy, 0)); yd = slice(max(-dy, 0), h + min(-dy, 0))
    xs = slice(max(dx, 0), w + min(dx, 0)); xd = slice(max(-dx, 0), w + min(-dx, 0))
    out[ys, xs] = a[yd, xd]
    return out


class Mat:
    def __init__(self, ramp_cols, emissive=0.0, flat=False, spec=0.0, outline=None, name='', bands=(0.22, 0.66)):
        self.ramp = [np.array(c, float) for c in ramp_cols]
        self.emissive = emissive
        self.flat = flat
        self.spec = spec
        self.outline = outline
        self.name = name
        self.bands = bands


# HD doku paketleri (2K / 4K): mantıksal birim başına piksel çarpanı. Şekiller mantıksal birimde (temel
# sayfa pikseli) tanımlı kalır; tuval SS kat ince ızgarada rasterlanır, desenler (paint) mantıksal
# koordinatla çalıştığı için aynı görünür ama daha çok ayrıntıyla. (Eskiden v1 export_assets.py --hd N ayarlıyordu; v30'da
# v1 üreticileriyle birlikte kaldırıldı. Mürekkep üreticileri HD için hdpack.py / KY_HD kullanır.)
SS = 1


def thicken(out, steps):
    """Dış konturu steps-1 piksel daha kalınlaştırır (HD'de kontur, temel sanattaki kalınlığa yakın kalsın)."""
    for _ in range(max(0, steps - 1)):
        a = out[..., 3] > 0
        add = np.zeros(a.shape, bool)
        col = np.zeros_like(out)
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            sa = shift(a, dy, dx, False)
            so = shift(out, dy, dx, 0.0)
            new = (~a) & sa & (~add)
            col[new] = so[new]
            add |= new
        out[add] = col[add]
    return out


def _up(a, S, shape):
    """Mantıksal dizi -> fiziksel ızgara (en yakın komşu)."""
    if S == 1:
        return a
    hh, ww = shape
    yi = np.minimum((np.arange(hh) + 0.5) / S, a.shape[0] - 1e-6).astype(int)
    xi = np.minimum((np.arange(ww) + 0.5) / S, a.shape[1] - 1e-6).astype(int)
    return a[np.ix_(yi, xi)]


class Canvas:
    def __init__(self, w, h, ox=0, oy=0):
        self.S = SS
        self.lw, self.lh = w, h
        w, h = int(round(w * SS)), int(round(h * SS))
        self.w, self.h = w, h
        self.ox, self.oy = ox * SS, oy * SS
        self.z = np.full((h, w), -1e9)
        self.n = np.zeros((h, w, 3)); self.n[..., 2] = 1
        self.mat = np.full((h, w), -1, int)
        self.tone = np.zeros((h, w))
        self.mats = []
        self.emis = np.zeros((h, w, 3))

    def _mid(self, m):
        for i, x in enumerate(self.mats):
            if x is m:
                return i
        self.mats.append(m)
        return len(self.mats) - 1

    def _grid(self, x0, y0, x1, y1):
        S = self.S
        x0 = max(0, int(np.floor(x0 * S + self.ox)) - 1); y0 = max(0, int(np.floor(y0 * S + self.oy)) - 1)
        x1 = min(self.w, int(np.ceil(x1 * S + self.ox)) + 2); y1 = min(self.h, int(np.ceil(y1 * S + self.oy)) + 2)
        if x1 <= x0 or y1 <= y0:
            return None
        ys, xs = np.mgrid[y0:y1, x0:x1]
        return (slice(y0, y1), slice(x0, x1)), (xs + 0.5 - self.ox) / S, (ys + 0.5 - self.oy) / S

    def _write(self, sl, inside, z, nx, ny, nz, mat, tone=0.0, paint=None, lu=None, lv=None, px=None, py=None):
        mid = self._mid(mat)
        mids = np.full(inside.shape, mid)
        if paint:
            for fn, pm in paint:
                m = fn(lu, lv, px, py) & inside
                if m.any():
                    mids[m] = self._mid(pm)
        zr = self.z[sl]
        w = inside & (z > zr)
        if not w.any():
            return
        zr[w] = z[w]
        ln = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
        nr = self.n[sl]
        nr[..., 0][w] = (nx / ln)[w]; nr[..., 1][w] = (ny / ln)[w]; nr[..., 2][w] = (nz / ln)[w]
        self.mat[sl][w] = mids[w]
        self.tone[sl][w] = tone if np.isscalar(tone) else tone[w]

    @staticmethod
    def _flatten(nx, ny, nz, flat):
        if flat <= 0:
            return nx, ny, nz
        # iç kısım düz kalsın, sadece kenara yakın yerler dönsün
        e = np.sqrt(nx * nx + ny * ny)
        k = np.clip((e - flat) / (1 - flat + 1e-6), 0, 1)
        return nx * k, ny * k, np.maximum(nz, 1 - k)

    def capsule(self, p0, p1, r0, r1, mat, z=0.0, tone=0.0, flat=0.35, paint=None):
        p0 = np.array(p0, float); p1 = np.array(p1, float)
        rm = max(r0, r1)
        g = self._grid(min(p0[0], p1[0]) - rm, min(p0[1], p1[1]) - rm, max(p0[0], p1[0]) + rm, max(p0[1], p1[1]) + rm)
        if g is None:
            return
        sl, px, py = g
        sx, sy = p1 - p0
        L2 = sx * sx + sy * sy + 1e-9
        t = np.clip(((px - p0[0]) * sx + (py - p0[1]) * sy) / L2, 0, 1)
        cx = p0[0] + t * sx; cy = p0[1] + t * sy
        r = r0 + (r1 - r0) * t
        dx = px - cx; dy = py - cy
        d2 = dx * dx + dy * dy
        inside = d2 <= r * r
        h = np.sqrt(np.clip(r * r - d2, 0, None))
        rr = np.maximum(r, 1e-3)
        nx, ny, nz = self._flatten(dx / rr, dy / rr, h / rr, flat)
        Ls = np.sqrt(L2)
        side = (dx * (-sy) + dy * sx) / Ls / rr
        self._write(sl, inside, z + h, nx, ny, nz, mat, tone, paint, t, side, px, py)

    def ellipse(self, c, rx, ry, mat, z=0.0, rot=0.0, depth=1.0, tone=0.0, flat=0.35, paint=None):
        cx, cy = c
        R = max(rx, ry)
        g = self._grid(cx - R, cy - R, cx + R, cy + R)
        if g is None:
            return
        sl, px, py = g
        ca, sa = np.cos(rot), np.sin(rot)
        u = (px - cx) * ca + (py - cy) * sa
        v = -(px - cx) * sa + (py - cy) * ca
        q = (u / rx) ** 2 + (v / ry) ** 2
        inside = q <= 1
        h = np.sqrt(np.clip(1 - q, 0, None))
        nu = u / rx; nv = v / ry
        nx = nu * ca - nv * sa; ny = nu * sa + nv * ca
        nx, ny, nz = self._flatten(nx, ny, h / max(depth, 0.2), flat)
        self._write(sl, inside, z + h * min(rx, ry) * depth, nx, ny, nz, mat, tone, paint, u / rx, v / ry, px, py)

    def poly(self, pts, mat, z=0.0, bevel=1.6, height=1.5, tone=0.0, paint=None, tilt=(0.0, 0.0)):
        pts = np.array(pts, float)
        g = self._grid(pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max())
        if g is None:
            return
        sl, px, py = g
        inside = np.zeros(px.shape, bool)
        n = len(pts)
        dmin = np.full(px.shape, 1e9); nxb = np.zeros(px.shape); nyb = np.zeros(px.shape)
        for i in range(n):
            ax, ay = pts[i]; bx, by = pts[(i + 1) % n]
            cond = ((ay > py) != (by > py))
            xint = (bx - ax) * (py - ay) / ((by - ay) + 1e-12) + ax
            inside ^= cond & (px < xint)
            sx, sy = bx - ax, by - ay
            t = np.clip(((px - ax) * sx + (py - ay) * sy) / (sx * sx + sy * sy + 1e-9), 0, 1)
            qx = ax + t * sx - px; qy = ay + t * sy - py
            d = np.sqrt(qx * qx + qy * qy)
            m = d < dmin
            dmin[m] = d[m]; nxb[m] = qx[m]; nyb[m] = qy[m]
        k = np.clip(1 - dmin / max(bevel, 1e-3), 0, 1)
        ln = np.sqrt(nxb ** 2 + nyb ** 2) + 1e-9
        nx = nxb / ln * k * 0.9 + tilt[0]; ny = nyb / ln * k * 0.9 + tilt[1]
        hgt = height * np.clip(dmin / max(bevel, 1e-3), 0, 1)
        self._write(sl, inside, z + hgt, nx, ny, np.ones(px.shape) * (1 - k * 0.45), mat, tone, paint, px - pts[:, 0].min(), py - pts[:, 1].min(), px, py)

    def region(self, mask, mat, z=0.0, bevel=3, slope=0.55, tone=0.0, paint=None, x0=0, y0=0):
        """Piksel maskesinden eğimli bölge: kenara uzaklık = yükseklik (organik kenarlar için)."""
        hh, ww = mask.shape
        S = self.S
        d = np.zeros(mask.shape)
        cur = mask.copy()
        for _ in range(bevel):
            d += cur
            er = cur.copy()
            for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                er &= shift(cur, dy, dx, False)
            cur = er
        gx = (shift(d, 0, -1, 0.0) - shift(d, 0, 1, 0.0)) * 0.5
        gy = (shift(d, -1, 0, 0.0) - shift(d, 1, 0, 0.0)) * 0.5
        nx, ny, nz = -gx * slope, -gy * slope, np.ones(mask.shape)
        # fiziksel ızgara: maske ve eğim en yakın komşuyla büyütülür, desen koordinatı mantıksal kalır
        X0, Y0 = int(round(x0 * S)), int(round(y0 * S))
        H2, W2 = int(round(hh * S)), int(round(ww * S))
        sl = (slice(Y0, Y0 + H2), slice(X0, X0 + W2))
        mask, d, nx, ny = (_up(a, S, (H2, W2)) for a in (mask, d, nx, ny))
        nz = np.ones(mask.shape)
        ys, xs = np.mgrid[Y0:Y0 + H2, X0:X0 + W2]
        px, py = (xs + 0.5 - self.ox) / S, (ys + 0.5 - self.oy) / S
        self._write(sl, mask, z + d, nx, ny, nz, mat, tone, paint, d, d, px, py)

    def dot(self, p, mat, z=50.0, size=1):
        x = int(np.floor(p[0] * self.S + self.ox)); y = int(np.floor(p[1] * self.S + self.oy))
        if 0 <= x < self.w and 0 <= y < self.h:
            s = max(1, int(round(size * self.S)))
            sl = (slice(y, min(self.h, y + s)), slice(x, min(self.w, x + s)))
            hh, ww = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
            o = np.ones((hh, ww))
            self._write(sl, o.astype(bool), o * z, o * 0, o * 0, o, mat)

    # ------------------------------------------------------------ cel gölgelendirme
    def shade(self, light=(-0.5, -0.75, 0.55), rim=(0.9, -0.15, -0.35), rim_col='#bfefff', rim_amt=0.45,
              outline_mul=0.42, inner_lines=True, band_shift=0.0, **_):
        L = np.array(light, float); L /= np.linalg.norm(L)
        Rl = np.array(rim, float); Rl /= np.linalg.norm(Rl)
        rc = hx(rim_col)
        Hh, Ww = self.h, self.w
        out = np.zeros((Hh, Ww, 4))
        emis = np.zeros((Hh, Ww, 3))
        alpha = self.mat >= 0
        for mid, m in enumerate(self.mats):
            sel = self.mat == mid
            if not sel.any():
                continue
            nn = self.n[sel]
            R = np.array(m.ramp)
            if m.flat:
                idx = np.full(nn.shape[0], 2)
            else:
                d = nn @ L + self.tone[sel] + band_shift
                b0, b1 = m.bands
                idx = np.where(d < b0, 1, np.where(d < b1, 2, 3))
                if m.spec:
                    hv = L + np.array([0, 0, 1.0]); hv /= np.linalg.norm(hv)
                    idx = np.where((nn @ hv) ** 16 * m.spec > 0.55, 4, idx)
                idx = np.where(d < b0 - 0.55, 0, idx)
            col = R[np.clip(idx, 0, len(R) - 1)]
            if not m.flat and rim_amt > 0:
                rv = np.clip(nn @ Rl, 0, 1) * np.clip(1 - nn[:, 2], 0, 1)
                rmask = rv > 0.42
                col[rmask] = col[rmask] * (1 - rim_amt) + rc * rim_amt
            out[sel, :3] = col
            out[sel, 3] = 1
            if m.emissive:
                emis[sel] = col * m.emissive
        if inner_lines:
            z = self.z
            for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                zn = shift(z, dy, dx, -1e9)
                mn = shift(self.mat, dy, dx, -1)
                edge = alpha & (mn >= 0) & (zn > z + 3.0) & (mn != self.mat)
                if edge.any():
                    for mid, m in enumerate(self.mats):
                        e = edge & (self.mat == mid)
                        if e.any() and not m.emissive:
                            out[e, :3] = np.array(m.ramp[0]) * 0.85
        a = alpha
        nb = np.zeros_like(a)
        src = np.full(a.shape, -1)
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            sh = shift(a, dy, dx, False)
            shm = shift(self.mat, dy, dx, -1)
            new = (~a) & sh & (src < 0)
            src[new] = shm[new]
            nb |= (~a) & sh
        for mid, m in enumerate(self.mats):
            e = nb & (src == mid)
            if not e.any():
                continue
            oc = hx(m.outline) if m.outline else np.array(m.ramp[0]) * outline_mul
            out[e, :3] = oc
            out[e, 3] = 1
        self.emis = emis
        self.outline_mask = nb
        if self.S > 1:
            thicken(out, int(round(self.S * 0.5)))
            self.outline_mask = (out[..., 3] > 0) & ~alpha
        return out

    def normal_map(self, out_alpha):
        nm = np.zeros((self.h, self.w, 4))
        n = self.n.copy()
        n[self.outline_mask] = [0, 0, 1]
        nm[..., 0] = n[..., 0] * 0.5 + 0.5
        nm[..., 1] = -n[..., 1] * 0.5 + 0.5
        nm[..., 2] = n[..., 2] * 0.5 + 0.5
        nm[..., 3] = out_alpha
        return nm


# ------------------------------------------------------------ desen yardımcıları (paint)
def stripes(period=3, width=1, axis='u', offset=0.0):
    def f(lu, lv, px, py):
        c = lu if axis == 'u' else lv
        if axis in ('x', 'y'):
            c = px if axis == 'x' else py
        return ((np.floor(c * (period if axis in ('u', 'v') else 1) + offset)) % (period if axis in ('x', 'y') else 2) < width)
    return f


def band(lo, hi, axis='v'):
    def f(lu, lv, px, py):
        c = {'u': lu, 'v': lv, 'x': px, 'y': py}[axis]
        return (c >= lo) & (c < hi)
    return f


def zigzag(center, amp, period, thick, axis='u'):
    """Kilim zikzağı: yerel koordinatta testere dişi bir şerit."""
    def f(lu, lv, px, py):
        a = px if axis == 'x' else lu * period * 4
        tri = np.abs(((a / period) % 2) - 1) * 2 - 1
        c = py if axis == 'x' else lv
        return np.abs(c - (center + tri * amp)) < thick
    return f


def speckle(density=0.12, seed=1):
    def f(lu, lv, px, py):
        h = np.sin(np.floor(px) * 12.9898 + np.floor(py) * 78.233 + seed * 3.1) * 43758.5453
        return (h - np.floor(h)) < density
    return f


def to_img(arr):
    a = np.clip(arr * 255 + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(a, 'RGBA' if a.shape[2] == 4 else 'RGB')


def blur(a, r=2, it=3):
    out = a.copy()
    for _ in range(it):
        for ax in (0, 1):
            acc = np.zeros_like(out)
            for k in range(-r, r + 1):
                acc += np.roll(out, k, ax)
            out = acc / (2 * r + 1)
    return out
