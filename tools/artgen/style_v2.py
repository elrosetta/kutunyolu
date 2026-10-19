"""Stil v2 ("gerçekçi piksel"): Shinobi: Art of Vengeance yönünde daha gerçekçi ama keskin piksel sanat.

v1 (volume.VCanvas) 5 tonlu, malzemeden bağımsız tek bir bant yapısı kullanır; v2 şunları ekler:
  * 7 tonlu rampa (derin gölge, gölge, yansıyan gölge, ana, yarı ışık, ışık, parlama); gölgeler soğuk
    mor-maviye, ışıklar sıcak gümüşe kayar (ay ışığı + ocak yansıması),
  * malzeme türü (`kind`): kumaş geniş/yumuşak bantlar ve mat; deri dar orta ton + kısa parlama;
    metal yüksek kontrast, gökyüzü/yer yansıması (üst yüz açık, alt yüz koyu) ve keskin parlama;
    post (kürk) tutam gürültüsü; ten/ağız gibi diğerleri kumaş gibi davranır,
  * yansıyan ışık: gölgedeki ve aşağı bakan yüzeyler yerden 1 basamak sıcak geri yansıma alır
    (hacmi "kâğıt" olmaktan çıkaran ana etken),
  * kalın (2 piksel) soğuk kenar ışığı: sırt/arka kenarda ay, siluet her zeminde okunur,
  * seçici kontur: gölge kenarında koyu, ışık kenarında malzemenin koyu tonu.
Aynı çizim API'si (capsule/ellipse/poly/dot + paint) geçerlidir; v1 sanatı etkilenmez.
"""
import colorsys
import numpy as np
from raster import Mat, hx, shift, thicken
from volume import VCanvas, _blur, _hash

# malzeme türüne göre bant eşikleri (7 ton -> 6 eşik) ve parlama gücü
KIND = {
    'cloth':   dict(vb=(-0.50, -0.26, -0.03, 0.20, 0.44, 0.76), spec=0.0, fur=0.05, bounce=1.0),
    'leather': dict(vb=(-0.34, -0.10, 0.12, 0.40, 0.66, 0.80), spec=0.6, fur=0.0, bounce=0.8),
    'metal':   dict(vb=(-0.30, -0.08, 0.10, 0.34, 0.58, 0.74), spec=1.0, fur=0.0, bounce=1.0, env=0.55),
    'fur':     dict(vb=(-0.40, -0.16, 0.06, 0.32, 0.58, 0.88), spec=0.0, fur=0.8, bounce=0.7),
    'skin':    dict(vb=(-0.38, -0.14, 0.08, 0.34, 0.60, 0.84), spec=0.3, fur=0.0, bounce=1.0),
}


def _lerp_hue(h, t, k):
    d = ((t - h + 540) % 360) - 180
    return (h + d * k) % 360


def tones(base, n=7, spread=1.0, shadow_hue=252, light_hue=42, sat_dark=0.18, sat_light=0.28, lift=1.0):
    """Taban renkten 7 tonlu rampa. Ortadaki (indeks 3) taban renktir."""
    r, g, b = hx(base) if isinstance(base, str) else base
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h *= 360
    out = []
    mid = n // 2
    for i in range(n):
        o = (i - mid) / mid          # -1 .. 1
        if o < 0:
            k = -o
            hh = _lerp_hue(h, shadow_hue, 0.30 * k)
            ss = min(1.0, s * (1 + sat_dark * k))
            vv = v * (1 - 0.62 * spread * k) ** 1.1
        else:
            k = o
            hh = _lerp_hue(h, light_hue, 0.22 * k)
            ss = s * (1 - sat_light * k)
            vv = min(1.0, v + (1 - v) * 0.62 * lift * k + 0.06 * k)
        out.append(np.array(colorsys.hsv_to_rgb(hh / 360, max(0, min(1, ss)), max(0, min(1, vv)))))
    return out


def M2(base, kind='cloth', name='', spread=1.0, lift=1.0, emissive=0.0, outline=None, **kw):
    """v2 malzemesi: 7 tonlu rampa + tür ayarları (vb, spec, env, fur, bounce)."""
    m = Mat(tones(base, spread=spread, lift=lift, **kw), emissive=emissive, outline=outline, name=name)
    for k_, v_ in KIND[kind].items():
        setattr(m, k_, v_)
    m.kind = kind
    m.fur = KIND[kind]['fur']
    return m


def variant(m, dv=-1, name=''):
    """Aynı malzemenin tonca kaydırılmış eşi (ör. lamel kenarı, kıvrım içi). dv basamak cinsinden."""
    R = m.ramp
    n = len(R)
    ramp_ = [R[max(0, min(n - 1, i + dv))] for i in range(n)]
    m2 = Mat(ramp_, emissive=m.emissive, outline=m.outline, name=name or m.name + ' %+d' % dv)
    for k_ in ('vb', 'spec', 'fur', 'bounce', 'env', 'kind', 'bias'):
        if hasattr(m, k_):
            setattr(m2, k_, getattr(m, k_))
    return m2


class VCanvas2(VCanvas):
    """v2 gölgelendirici. Malzemede `vb` yoksa (v1 malzemesi) 5 tonu 7'ye yayar."""
    zscale = 1.0

    def _shade(self, light=(-0.55, -0.70, 0.45), rim=(0.70, -0.70), rim_col='#bcd8ff', rim_amt=0.55, rim_w=2,
               bounce_col='#7a4a3a', bounce_amt=0.0, ao=0.85, cast=0.5, form=0.5, fur_amp=0.10, cleanup=2,
               grad=0.30, rim_th=0.45, lit_outline=0.0, outline_k=(0.82, 0.55, 0.32), **_):
        L = np.array(light, float); L /= np.linalg.norm(L)
        Hh, Ww = self.h, self.w
        zs = self.zscale
        alpha = self.mat >= 0
        A = alpha.astype(float)
        S = self.S
        R_ = lambda r: max(1, int(round(r * S * zs)))
        # büyük form (siluet bulanıklığı) + parça normali
        hg = _blur(A, R_(1), 2) * 0.35 + _blur(A, R_(3), 2) * 0.45 + _blur(A, R_(6), 2) * 0.2
        gx = (shift(hg, 0, -1, 0.0) - shift(hg, 0, 1, 0.0)) * 0.5
        gy = (shift(hg, -1, 0, 0.0) - shift(hg, 1, 0, 0.0)) * 0.5
        ng = np.stack([-gx * 4.0 * S * zs, -gy * 4.0 * S * zs, np.ones_like(hg) * 0.9], -1)
        ng /= np.linalg.norm(ng, axis=-1, keepdims=True)
        n = self.n * (1 - form) + ng * form
        n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
        self.n_vol = n
        d = n @ L + self.tone
        ys = np.nonzero(alpha.any(1))[0]
        if len(ys):
            y0, y1 = ys[0], ys[-1] + 1
            yy = (np.arange(Hh)[:, None] - y0) / max(1, y1 - y0)
            d = d - grad * (np.clip(yy, 0, 1) - 0.4)
        # ortam kapanması + temas gölgesi
        z = np.where(alpha, self.z, -1e9)
        zmax = z.copy()
        ar = R_(2)
        for dy in range(-ar, ar + 1):
            for dx in range(-ar, ar + 1):
                if dy * dy + dx * dx <= ar * ar + 1:
                    zmax = np.maximum(zmax, shift(z, dy, dx, -1e9))
        occ = np.clip((zmax - z - 2.5 * zs) / (9.0 * zs), 0, 1) * alpha
        d -= ao * occ * 0.55
        cs = np.zeros((Hh, Ww), bool)
        for dy, dx in ((1, 1), (1, 0), (2, 1), (2, 2), (0, 1), (3, 2)):
            cs |= shift(z, int(round(dy * zs)), int(round(dx * zs)), -1e9) > z + 3.5 * zs
        cs &= alpha
        d -= cast * cs
        # malzeme başına: tutam gürültüsü, ton kaydırma, metal ortam yansıması
        fur = np.zeros((Hh, Ww))
        for mid, m in enumerate(self.mats):
            sel = self.mat == mid
            fa = getattr(m, 'fur', 0.0)
            if fa:
                fur[sel] = fa
            bi = getattr(m, 'bias', 0.0)
            if bi:
                d[sel] += bi
            env = getattr(m, 'env', 0.0)
            if env and sel.any():
                # gök (üst) açık, ufuk çizgisinde keskin geçiş, yer (alt) koyu: parlak metalin okuması
                ny_ = n[sel][:, 1]
                d[sel] = d[sel] * (1 - env) + np.where(ny_ < -0.05, 0.55 - ny_ * 0.4, -0.35 + ny_ * 0.1) * env
        if fur.any():
            u, v = self.uv[..., 0], self.uv[..., 1]
            row = np.floor(v * 0.5)
            off = _hash(row, self.pid, 3.1) * 3.0
            seg = np.floor(u * 0.3 + off)
            nz = _hash(row + 17.0 * seg, self.pid, 7.7) - 0.5
            d += nz * 2 * fur_amp * fur
        # siluet dış yönü
        ab = _blur(A, R_(1), 2)
        ogx = (shift(ab, 0, -1, 0.0) - shift(ab, 0, 1, 0.0))
        ogy = (shift(ab, -1, 0, 0.0) - shift(ab, 1, 0, 0.0))
        on = np.sqrt(ogx * ogx + ogy * ogy) + 1e-9
        ox_, oy_ = -ogx / on, -ogy / on
        # kenardan içeri mesafe (kenar ışığı kalınlığı)
        dist = np.zeros((Hh, Ww), int)
        cur = alpha.copy()
        for k in range(rim_w):
            er = cur & shift(cur, 1, 0, False) & shift(cur, -1, 0, False) & shift(cur, 0, 1, False) & shift(cur, 0, -1, False)
            dist[cur & ~er] = k + 1
            cur = er
        rl = np.array(rim, float); rl /= np.linalg.norm(rl)
        rimdot = ox_ * rl[0] + oy_ * rl[1]
        # dışa bakan kenar ışık yönüne ne kadar dönükse o kadar kalın: tam dönükte rim_w, yarı dönükte 1 piksel
        rimm = ((dist == 1) & (rimdot > rim_th)) | ((dist > 1) & (rimdot > rim_th + (1 - rim_th) * 0.5))
        # 1) ton indeksleri
        NT = 7
        IDX = np.full((Hh, Ww), -1)
        for mid, m in enumerate(self.mats):
            sel = self.mat == mid
            if not sel.any():
                continue
            nr = len(m.ramp)
            vb = getattr(m, 'vb', None)
            if m.flat:
                idx = np.full(sel.sum(), nr // 2)
            else:
                dd = d[sel]
                if vb is None:   # v1 malzemesi: 5 ton, v1 eşikleri
                    vb5 = (-0.30, 0.10, 0.52, 0.86)
                    idx = np.digitize(dd, vb5)
                else:
                    idx = np.digitize(dd, vb)
                sp = getattr(m, 'spec', 0.0)
                if sp:
                    hv = L + np.array([0, 0, 1.0]); hv /= np.linalg.norm(hv)
                    hi = (n[sel] @ hv) ** (24 if getattr(m, 'kind', '') == 'metal' else 14) * sp > 0.5
                    idx = np.where(hi, nr - 1, idx)
                if m.emissive:
                    idx = np.maximum(idx, nr // 2)
                idx = np.clip(idx, 0, nr - 1)
            IDX[sel] = idx
        # 2) yansıyan ışık: gölgedeki, aşağı/geri bakan pikseller 1 basamak açılır (yerden geri yansıma)
        down = (n[..., 1] > 0.25) & alpha
        for mid, m in enumerate(self.mats):
            if m.emissive or m.flat:
                continue
            b = getattr(m, 'bounce', 0.0)
            if not b:
                continue
            sel = (self.mat == mid) & down & (IDX >= 1) & (IDX <= 2) & ~cs
            IDX[sel] += 1
        # 3) yetim piksel temizliği
        for _ in range(cleanup):
            nbr = [(shift(IDX, dy, dx, -1), shift(self.mat, dy, dx, -1)) for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0))]
            same_any = np.zeros((Hh, Ww), bool)
            cnt = np.zeros((Hh, Ww, NT))
            for ni, nm_ in nbr:
                ok = (nm_ == self.mat) & (ni >= 0)
                same_any |= ok & (ni == IDX)
                for t in range(NT):
                    cnt[..., t] += ok & (ni == t)
            fix = alpha & ~same_any & (cnt.sum(-1) >= 2)
            for mid, m in enumerate(self.mats):
                if m.flat or m.emissive or getattr(m, 'kind', '') == 'metal':
                    fix &= self.mat != mid
            IDX = np.where(fix, cnt.argmax(-1), IDX)
        # 4) renk
        out = np.zeros((Hh, Ww, 4))
        emis = np.zeros((Hh, Ww, 3))
        rc = hx(rim_col)
        bc = hx(bounce_col)
        for mid, m in enumerate(self.mats):
            sel = self.mat == mid
            if not sel.any():
                continue
            R = np.array(m.ramp)
            col = R[np.clip(IDX[sel], 0, len(R) - 1)]
            if not m.emissive and not m.flat and rim_amt > 0:
                rm = rimm[sel]
                # kenar ışığı: malzemenin en açık tonlarından birine, ay rengine karışık
                top = R[np.clip(IDX[sel][rm] + 2, 0, len(R) - 1)]
                col[rm] = top * (1 - rim_amt) + rc * rim_amt
            if bounce_amt > 0 and not m.emissive:
                bm = (down[sel]) & (IDX[sel] <= 3)
                col[bm] = col[bm] * (1 - bounce_amt) + bc * bounce_amt * col[bm].mean(-1, keepdims=True) * 2
            out[sel, :3] = col
            out[sel, 3] = 1
            if m.emissive:
                emis[sel] = col * m.emissive
        # iç çizgiler (malzemeler arası belirgin derinlik sıçraması)
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            zn = shift(z, dy, dx, -1e9)
            mn = shift(self.mat, dy, dx, -1)
            same = mn == self.mat
            jump = np.where(same, 10.0, 3.5) * zs
            e = alpha & (mn >= 0) & (zn > z + jump) & ~rimm
            if e.any():
                for mid, m in enumerate(self.mats):
                    ee = e & (self.mat == mid)
                    if ee.any() and not m.emissive:
                        out[ee, :3] = np.array(m.ramp[0]) * 0.7
        # seçici dış kontur
        nb = np.zeros_like(alpha)
        src = np.full(alpha.shape, -1)
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            sh = shift(alpha, dy, dx, False)
            shm = shift(self.mat, dy, dx, -1)
            new = (~alpha) & sh & (src < 0)
            src[new] = shm[new]
            nb |= (~alpha) & sh
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
                mul = np.where(k > 0.35, outline_k[0], np.where(k > -0.2, outline_k[1], outline_k[2]))
                oc = base[None, :] * mul[:, None]
            out[e, :3] = oc
            out[e, 3] = 1
            if lit_outline < 1.0 and not m.outline:
                ee = np.zeros_like(e)
                ee[e] = lit[e] > 0.35
                out[ee, :3] = np.array(m.ramp[1])
                out[ee, 3] = lit_outline
        out[(out[..., 3] > 0) & (out[..., 3] < 0.01)] = 0
        self.emis = emis
        self.outline_mask = nb
        if S > 1:
            thicken(out, int(round(S * 0.5)))
            self.outline_mask = (out[..., 3] > 0) & ~alpha
        return out


# ------------------------------------------------------------ ortam (karo / arka plan) son işlemleri
def value_grade(rgb, lo=0.0, hi=1.0, gamma=1.0, cool_shadow=(0.0, 0.0, 0.0), warm_light=(0.0, 0.0, 0.0), sat=1.0):
    """Değer yapısını açar: siyah/beyaz noktası, gama, gölgeye soğuk / ışığa sıcak renk kayması, doygunluk."""
    x = np.clip((rgb - lo) / max(1e-6, hi - lo), 0, 1) ** gamma
    lum = (x * np.array([0.299, 0.587, 0.114])).sum(-1, keepdims=True)
    x = lum + (x - lum) * sat
    x = x + np.array(cool_shadow) * (1 - lum) ** 2 + np.array(warm_light) * lum ** 2
    return np.clip(x, 0, 1)


def quantize_ramp(rgb, n=48, seed=0):
    """Toprak/kaya gibi ortam dokularını sınırlı bir palete indirger (piksel sanat okunurluğu, tonlar
    yine de zengin): luma'ya göre sıralı k-ortalamalar."""
    h, w, _ = rgb.shape
    X = rgb.reshape(-1, 3)
    rng = np.random.default_rng(seed)
    C = X[rng.choice(len(X), n, replace=False)].copy()
    for _ in range(8):
        dd = ((X[:, None, :] - C[None, :, :]) ** 2).sum(-1) if len(X) < 300000 else None
        if dd is None:
            break
        lab = dd.argmin(1)
        for k in range(n):
            s = lab == k
            if s.any():
                C[k] = X[s].mean(0)
    dd = ((X[:, None, :] - C[None, :, :]) ** 2).sum(-1)
    return C[dd.argmin(1)].reshape(h, w, 3)
