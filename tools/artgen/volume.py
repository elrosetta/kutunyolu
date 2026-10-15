"""Hacimli gölgelendirme (v13): kurtlar ve Bengü için "kâğıt kesik" görünümünü kıran Canvas.

Eski cel gölgelendirici (raster.Canvas.shade) her parçanın içini düz bırakır (normal düzleştirme),
yalnızca 3 ton kullanır ve her parçanın çevresine aynı koyu çizgiyi çeker: parçalar üst üste yapıştırılmış
kâğıt gibi okunur. VCanvas aynı çizim API'sini korur, ama:
  * normaller düzleştirilmez; parça normali + bütün siluetten türetilen "büyük form" normali karışır
    (gövde, bacak ve baş tek bir hacim gibi döner),
  * 5 basamaklı rampa (derin gölge / gölge / ana / ışık / parlama), tutarlı sol-üst ışık,
  * ortam kapanması (AO): yakın parçanın altında kalan uzak parça kararır; sol-üst ışığın düşürdüğü
    1-2 piksellik temas gölgesi (cast shadow),
  * kürk: malzemede `fur` > 0 ise parçaya bağlı (karelerde kaymayan) tutam gürültüsü bant sınırlarını
    tırtıklı tüy öbeklerine çevirir,
  * seçici kontur: ışıklı kenarda malzemenin kendi koyu tonu, gölge kenarında koyuya yakın; aynı malzeme
    içindeki küçük z sıçramalarında iç çizgi yok (parçalar kaynaşır),
  * sırt/arka kenarda soğuk ay ışığı kenar parlaması,
  * normal map aynı (düzleştirilmemiş, büyük formla karışık) normalden üretilir: oyundaki 2D ışıklar
    hacmi yakalar.
"""
import numpy as np
from raster import Canvas, hx, shift, thicken


def _box(a, r):
    """Kenarı sarmayan kutu bulanıklığı (kümülatif toplamla)."""
    if r <= 0:
        return a
    p = np.pad(a, r, mode='edge')
    c = p.cumsum(0)
    c = np.vstack([np.zeros((1, c.shape[1])), c])
    v = (c[2 * r + 1:] - c[:-2 * r - 1]) / (2 * r + 1)
    c = v.cumsum(1)
    c = np.hstack([np.zeros((c.shape[0], 1)), c])
    return (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)


def _blur(a, r, it=2):
    for _ in range(it):
        a = _box(a, r)
    return a


def soft(mat, light=0.5, hi=0.45, fur=None):
    """Koyu postlar için rampayı yumuşat: ışık/parlama tonlarını ana tona yaklaştır (kimlik koyu kalsın)."""
    R = mat.ramp
    R[3] = R[2] * (1 - light) + R[3] * light
    R[4] = R[2] * (1 - hi) + R[4] * hi
    if fur is not None:
        mat.fur = fur
    return mat


def _hash(a, b, c):
    h = np.sin(a * 12.9898 + b * 78.233 + c * 37.719) * 43758.5453
    return h - np.floor(h)


class VCanvas(Canvas):
    FLAT = 0.0
    zscale = 1.0  # büyütülmüş (Sq zk) çizimlerde z eşikleri de ölçeklenir
    shade_kw = {}  # sprite'a özgü varsayılan shade() ayarları (ör. koyu yaratıklarda güçlü ay kenarı)

    def __init__(self, w, h, ox=0, oy=0):
        super().__init__(w, h, ox, oy)
        self.uv = np.zeros((self.h, self.w, 2))
        self.pid = np.zeros((self.h, self.w))
        self._pc = 0
        self._cur = None

    # parça yerel koordinatını (piksel ölçeğinde) kaydetmek için _write'ı sarar
    def _write(self, sl, inside, z, nx, ny, nz, mat, tone=0.0, paint=None, lu=None, lv=None, px=None, py=None):
        zr = self.z[sl]
        w = inside & (z > zr)
        super()._write(sl, inside, z, nx, ny, nz, mat, tone, paint, lu, lv, px, py)
        if not w.any() or self._cur is None:
            return
        su, sv = self._cur
        u = lu * su if lu is not None else px
        v = lv * sv if lv is not None else py
        self.uv[sl][..., 0][w] = np.broadcast_to(u, w.shape)[w]
        self.uv[sl][..., 1][w] = np.broadcast_to(v, w.shape)[w]
        self.pid[sl][w] = self._pc

    def capsule(self, p0, p1, r0, r1, mat, z=0.0, tone=0.0, flat=None, paint=None):
        self._pc += 1
        L = float(np.hypot(p1[0] - p0[0], p1[1] - p0[1]))
        self._cur = (max(L, 1.0), max(r0, r1))
        super().capsule(p0, p1, r0, r1, mat, z=z, tone=tone, flat=self.FLAT if flat is None else min(flat, 0.2), paint=paint)
        self._cur = None

    def ellipse(self, c, rx, ry, mat, z=0.0, rot=0.0, depth=1.0, tone=0.0, flat=None, paint=None):
        self._pc += 1
        self._cur = (rx, ry)
        super().ellipse(c, rx, ry, mat, z=z, rot=rot, depth=depth, tone=tone, flat=self.FLAT if flat is None else min(flat, 0.3), paint=paint)
        self._cur = None

    def poly(self, pts, mat, z=0.0, bevel=1.6, height=1.5, tone=0.0, paint=None, tilt=(0.0, 0.0)):
        self._pc += 1
        self._cur = (1.0, 1.0)
        super().poly(pts, mat, z=z, bevel=max(bevel, 1.0) * 1.6, height=height, tone=tone, paint=paint, tilt=tilt)
        self._cur = None

    def dot(self, p, mat, z=50.0, size=1):
        self._pc += 1
        super().dot(p, mat, z=z, size=size)

    # ------------------------------------------------------------ hacimli gölgelendirme
    def shade(self, **kw):
        for k, v in self.shade_kw.items():
            kw.setdefault(k, v)
        return self._shade(**kw)

    def _shade(self, light=(-0.55, -0.72, 0.42), rim=(0.62, -0.78), rim_col='#cfe6ff', rim_amt=0.28,
              ao=0.75, cast=0.42, form=0.55, fur_amp=0.11, bands=(-0.30, 0.10, 0.52, 0.86), cleanup=2, grad=0.32, rim_th=0.68, lit_outline=1.0, **_):
        L = np.array(light, float); L /= np.linalg.norm(L)
        Hh, Ww = self.h, self.w
        zs = self.zscale
        alpha = self.mat >= 0
        A = alpha.astype(float)
        # büyük form: siluetin çok ölçekli bulanıklığı yükseklik gibi davranır
        S = self.S
        R_ = lambda r: max(1, int(round(r * S)))
        hg = _blur(A, R_(1), 2) * 0.35 + _blur(A, R_(3), 2) * 0.45 + _blur(A, R_(6), 2) * 0.2
        gx = (shift(hg, 0, -1, 0.0) - shift(hg, 0, 1, 0.0)) * 0.5
        gy = (shift(hg, -1, 0, 0.0) - shift(hg, 1, 0, 0.0)) * 0.5
        ng = np.stack([-gx * 4.0 * S, -gy * 4.0 * S, np.ones_like(hg) * 0.9], -1)
        ng /= np.linalg.norm(ng, axis=-1, keepdims=True)
        n = self.n * (1 - form) + ng * form
        n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
        self.n_vol = n
        d = n @ L + self.tone
        # gökten gelen ortam ışığı: siluetin altı (karın, bacak içleri) üstüne göre koyu -> silindir okuması
        ys = np.nonzero(alpha.any(1))[0]
        if len(ys):
            y0, y1 = ys[0], ys[-1] + 1
            yy = (np.arange(Hh)[:, None] - y0) / max(1, y1 - y0)
            d = d - grad * (np.clip(yy, 0, 1) - 0.4)
        # ortam kapanması: çevresindeki daha yüksek (yakın) parçaların altında kalan pikseller
        z = np.where(alpha, self.z, -1e9)
        zf = np.where(alpha, self.z, np.nan)
        zmax = z.copy()
        ar = R_(2)
        for dy in range(-ar, ar + 1):
            for dx in range(-ar, ar + 1):
                if dy * dy + dx * dx <= 5 * S * S:
                    zmax = np.maximum(zmax, shift(z, dy, dx, -1e9))
        occ = np.clip((zmax - z - 2.5 * zs) / (9.0 * zs), 0, 1) * alpha
        d -= ao * occ * 0.55
        # temas gölgesi: sol-üstteki yakın parça sağ-alta düşer
        cs = np.zeros((Hh, Ww), bool)
        for dy, dx in ((1, 1), (1, 0), (2, 1), (2, 2), (0, 1)):
            cs |= shift(z, int(round(dy * S)), int(round(dx * S)), -1e9) > z + 3.5 * zs
        cs &= alpha
        d -= cast * cs
        # kürk tutamları (parçaya bağlı gürültü; animasyonda kaymaz)
        fur = np.zeros((Hh, Ww))
        for mid, m in enumerate(self.mats):
            fa = getattr(m, 'fur', 0.0)
            if fa:
                fur[self.mat == mid] = fa
            bi = getattr(m, 'bias', 0.0)   # malzemeye özgü ton kaydırma (ör. beyaz post daha çok orta tonda kalsın)
            if bi:
                d[self.mat == mid] += bi
        if fur.any():
            u, v = self.uv[..., 0], self.uv[..., 1]
            row = np.floor(v * 0.5)
            off = _hash(row, self.pid, 3.1) * 3.0
            seg = np.floor(u * 0.3 + off)
            nz = _hash(row + 17.0 * seg, self.pid, 7.7) - 0.5
            d += nz * 2 * fur_amp * fur
        b0, b1, b2, b3 = bands
        out = np.zeros((Hh, Ww, 4))
        emis = np.zeros((Hh, Ww, 3))
        rc = hx(rim_col)
        # siluet kenarı ve dış yönü (kenar ışığı + seçici kontur için)
        ab = _blur(A, R_(1), 2)
        ogx = (shift(ab, 0, -1, 0.0) - shift(ab, 0, 1, 0.0))
        ogy = (shift(ab, -1, 0, 0.0) - shift(ab, 1, 0, 0.0))
        on = np.sqrt(ogx * ogx + ogy * ogy) + 1e-9
        ox_, oy_ = -ogx / on, -ogy / on   # dışarı doğru
        edge_in = alpha & ~(shift(alpha, 1, 0, False) & shift(alpha, -1, 0, False) & shift(alpha, 0, 1, False) & shift(alpha, 0, -1, False))
        rl = np.array(rim, float); rl /= np.linalg.norm(rl)
        rimm = edge_in & ((ox_ * rl[0] + oy_ * rl[1]) > rim_th)
        # 1) ton indeksi haritası
        IDX = np.full((Hh, Ww), -1)
        for mid, m in enumerate(self.mats):
            sel = self.mat == mid
            if not sel.any():
                continue
            if m.flat:
                idx = np.full(sel.sum(), 2)
            else:
                dd = d[sel]
                idx = np.where(dd < b0, 0, np.where(dd < b1, 1, np.where(dd < b2, 2, 3)))
                hi = dd > b3
                if m.spec:
                    hv = L + np.array([0, 0, 1.0]); hv /= np.linalg.norm(hv)
                    hi = hi | ((n[sel] @ hv) ** 16 * m.spec > 0.55)
                else:
                    hi = hi & (dd > b3 + 0.06)
                idx = np.where(hi, 4, idx)
                if m.emissive:
                    # ışıyan malzeme gölgeye düşmez: en az ana ton, ışık yönünde açık ton
                    idx = np.maximum(idx, 2)
            IDX[sel] = idx
        # 2) yetim piksel temizliği: aynı malzemeli 4 komşusunun hiçbiriyle tonu tutmayan tek pikseller
        #    komşuların çoğunluk tonuna çekilir (piksel sanatında "kirli" gürültüyü önler)
        for _ in range(cleanup):
            nbr = [(shift(IDX, dy, dx, -1), shift(self.mat, dy, dx, -1)) for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0))]
            same_any = np.zeros((Hh, Ww), bool)
            cnt = np.zeros((Hh, Ww, 5))
            for ni, nm_ in nbr:
                ok = (nm_ == self.mat) & (ni >= 0)
                same_any |= ok & (ni == IDX)
                for t in range(5):
                    cnt[..., t] += ok & (ni == t)
            fix = alpha & ~same_any & (cnt.sum(-1) >= 2)
            for mid, m in enumerate(self.mats):
                if m.flat or m.emissive:
                    fix &= self.mat != mid
            IDX = np.where(fix, cnt.argmax(-1), IDX)
        # 3) renk
        for mid, m in enumerate(self.mats):
            sel = self.mat == mid
            if not sel.any():
                continue
            R = np.array(m.ramp)
            col = R[np.clip(IDX[sel], 0, len(R) - 1)]
            if not m.emissive and not m.flat and rim_amt > 0:
                rm = rimm[sel]
                col[rm] = col[rm] * (1 - rim_amt) + rc * rim_amt
            out[sel, :3] = col
            out[sel, 3] = 1
            if m.emissive:
                emis[sel] = col * m.emissive
        # iç çizgiler: farklı malzemede küçük, aynı malzemede büyük z sıçraması
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            zn = shift(z, dy, dx, -1e9)
            mn = shift(self.mat, dy, dx, -1)
            same = mn == self.mat
            jump = np.where(same, 9.0, 3.5) * zs
            e = alpha & (mn >= 0) & (zn > z + jump)
            if e.any():
                for mid, m in enumerate(self.mats):
                    ee = e & (self.mat == mid)
                    if ee.any() and not m.emissive:
                        out[ee, :3] = np.array(m.ramp[0]) * 0.72
        # seçici dış kontur
        nb = np.zeros_like(alpha)
        src = np.full(alpha.shape, -1)
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            sh = shift(alpha, dy, dx, False)
            shm = shift(self.mat, dy, dx, -1)
            new = (~alpha) & sh & (src < 0)
            src[new] = shm[new]
            nb |= (~alpha) & sh
        # ışıklı kenar: dış yön ışığın geldiği yöne (L'nin xy'si) bakar
        lit = (ox_ * L[0] + oy_ * L[1]) / (np.hypot(L[0], L[1]) + 1e-9)
        for mid, m in enumerate(self.mats):
            e = nb & (src == mid)
            if not e.any():
                continue
            if m.outline:
                oc = np.broadcast_to(hx(m.outline), (e.sum(), 3))
            else:
                base = np.array(m.ramp[0])
                k = np.clip(lit[e], -1, 1)
                mul = np.where(k > 0.35, 0.78, np.where(k > -0.2, 0.5, 0.3))
                oc = base[None, :] * mul[:, None]
            out[e, :3] = oc
            out[e, 3] = 1
            if lit_outline < 1.0 and not m.outline:
                # ışıklı kenarda kontur yok/yarı saydam: siluet "çıkartma" gibi kesik durmaz, ışık kenarda erir
                ee = np.zeros_like(e)
                ee[e] = lit[e] > 0.35
                out[ee, :3] = np.array(m.ramp[1])
                out[ee, 3] = lit_outline
        self.emis = emis
        self.outline_mask = nb
        if S > 1:
            thicken(out, int(round(S * 0.5)))
            self.outline_mask = (out[..., 3] > 0) & ~alpha
        return out

    def normal_map(self, out_alpha):
        nm = np.zeros((self.h, self.w, 4))
        n = getattr(self, 'n_vol', self.n).copy()
        n[self.outline_mask] = [0, 0, 1]
        nm[..., 0] = n[..., 0] * 0.5 + 0.5
        nm[..., 1] = -n[..., 1] * 0.5 + 0.5
        nm[..., 2] = n[..., 2] * 0.5 + 0.5
        nm[..., 3] = out_alpha
        return nm
