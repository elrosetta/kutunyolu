"""ink_parcacik: stil v2 mürekkep parçacık ve çizim dokuları (assets/fx/ink_p/).

v1'in kare piksel parçacıkları (soft_dot 16x16) ve Kenney fotoğrafik dokuları (k_*.png) yerine elle çizilmiş
sumi-e karşılıkları. Hepsi beyaz tonlu (RGB = mürekkep tonu, kenarda koyulaşan "ıslak kenar"), A = biçim;
renk oyunda modulate / parçacık rengiyle gelir. Doğrusal süzgeç + mipmap ile içe aktarılır.

    nokta      yumuşak fırça dokunuşu (genel zerre; soft_dot karşılığı)
    leke_0..2  dolu mürekkep lekesi, düzensiz kenar + uydu damlalar (ateş topu tutamı, gövde)
    duman_0..1 mürekkep yıkaması bulutu, tanecikli, ıslak kenar çizgili (duman, toz)
    kivilcim   sivri fırça fiskesi (kıvılcım; y ekseni hız yönünde, baş altta)
    yildiz     dört kollu fırça parıltısı (k_star karşılığı)
    yildiz2    yedi ışınlı ruh zerresi (k_star2 karşılığı)
    alev       yukarı kıvrılan fırça alev dili (k_flame karşılığı)
    halka      açık uçlu fırça halkası (k_ring karşılığı, yere yatık şok halkaları)
    kul        kâğıt külü pulu, yanık kenarlı, delikli
    damla      gözyaşı damla (baş altta)
    cizgi      yatay incelen fırça darbesi (baş solda): hız çizgisi, şimşek parçası, ışın
    kan_0..2   yere yapışan mürekkep sıçrantısı çıkartması
    catlak_0..1 yer çatlağı: dallanan ince koyu fırça çizgileri
    yaprak     koyu yaprak silueti
    serit      u boyunca sarar şerit fırça (çoklu nokta fırça çizgileri için)

Kullanım: cd tools/artgen && python ink_parcacik.py [--onizleme out.png]
"""
import math
import os
import sys

import numpy as np
import skia
from PIL import Image
from scipy import ndimage

from inkfx import SS, _arr, _surface, blob, drop, fft_noise, smoothstep, taper

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'assets', 'fx', 'ink_p')

IMPORT = """[remap]

importer="texture"
type="CompressedTexture2D"

[params]

compress/mode=0
mipmaps/generate=true
process/fix_alpha_border=true
"""


def _down(a, w, h):
    return a.reshape(h, SS, w, SS).mean(axis=(1, 3))


def roughen(cov_hi, seed, amt=0.35, sigma=1.6):
    """Kenar pürüzü: kaplama bulanıklaştırılıp ince gürültüyle eşiklenir (kâğıda emilen mürekkep kenarı)."""
    h, w = cov_hi.shape
    b = ndimage.gaussian_filter(cov_hi, sigma * SS)
    nz = fft_noise(h, w, beta=1.2, seed=seed + 11)
    hard = (b + (nz - 0.5) * amt) > 0.5
    return ndimage.gaussian_filter(hard.astype(float), 0.7 * SS)


def finish(cov_hi, w, h, seed, rim=0.28, rim_w=0.06, grain=0.1, blur=0.45, backrun=0.0, holes=0.0):
    """Yüksek çözünürlüklü kaplama -> (RGB tonu, A). rim: kenarda koyulaşma (ıslak kenar), rim_w: genişlik
    (kısa kenarın oranı), grain: tane, blur: kenar yumuşatma (çıktı pikseli), backrun: kenara paralel ince
    koyu çizgi, holes: kuru fırça / kül delikleri."""
    inside = cov_hi > 0.5
    d_in = ndimage.distance_transform_edt(inside) / SS
    d_in = _down(d_in, w, h)
    a = _down(cov_hi, w, h)
    if blur > 0:
        a = ndimage.gaussian_filter(a, blur)
    nz = fft_noise(h, w, beta=1.7, seed=seed)
    nz2 = fft_noise(h, w, beta=1.1, seed=seed + 7)
    rw = max(1.0, min(w, h) * rim_w)
    T = 1.0 - rim * np.exp(-d_in / rw)
    if backrun > 0:
        T -= backrun * np.exp(-((d_in - rw * 1.6) / (rw * 0.35)) ** 2)
    T *= 1.0 - grain * nz2
    if holes > 0:
        a *= smoothstep(holes - 0.08, holes + 0.08, nz)
    a *= 1.0 - grain * 0.6 * (1 - nz)
    return np.clip(T, 0, 1), np.clip(a, 0, 1)


def save(name, T, A):
    os.makedirs(OUT, exist_ok=True)
    rgb = np.clip(T * 255 + 0.5, 0, 255).astype(np.uint8)
    al = np.clip(A * 255 + 0.5, 0, 255).astype(np.uint8)
    img = np.dstack([rgb, rgb, rgb, al])
    p = os.path.join(OUT, name + '.png')
    Image.fromarray(img, 'RGBA').save(p)
    if not os.path.exists(p + '.import'):
        with open(p + '.import', 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(IMPORT)
    return img


def _blob_pts(c, cx, cy, r, rng, jit=0.25, n=40):
    blob(c, cx, cy, r, rng, k=int(rng.integers(7, 12)), jit=jit)


# ------------------------------------------------------------------ dokular
def nokta(S=64, seed=1):
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    _blob_pts(c, S * 0.5, S * 0.5, S * 0.26, rng, jit=0.18)
    cov = _arr(s)
    T, A = finish(cov, S, S, seed, rim=0.18, rim_w=0.12, grain=0.06, blur=S * 0.07)
    # yumuşak hale: kenar dışına doğru incelen yıkama
    A = np.clip(A * 1.15, 0, 1)
    return save('nokta', T, A)


def leke(i, S=128):
    seed = 20 + i
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    _blob_pts(c, S * 0.5, S * 0.5, S * 0.33, rng, jit=0.2)
    for k in range(int(rng.integers(2, 5))):
        a = rng.uniform(0, 6.28)
        rr = S * rng.uniform(0.36, 0.44)
        drop(c, S * 0.5 + math.cos(a) * rr, S * 0.5 + math.sin(a) * rr, S * rng.uniform(0.018, 0.04), a, rng.uniform(1.0, 1.8))
    cov = roughen(_arr(s), seed)
    T, A = finish(cov, S, S, seed, rim=0.36, rim_w=0.07, grain=0.1, blur=0.5)
    return save('leke_%d' % i, T, A)


def duman(i, S=128):
    seed = 40 + i
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    for k in range(int(rng.integers(5, 8))):
        a = rng.uniform(0, 6.28)
        d = S * rng.uniform(0.0, 0.17)
        _blob_pts(c, S * 0.5 + math.cos(a) * d, S * 0.5 + math.sin(a) * d * 0.8, S * rng.uniform(0.13, 0.22), rng, jit=0.28)
    cov = roughen(_arr(s), seed, 0.5, 2.5)
    T, A = finish(cov, S, S, seed, rim=0.42, rim_w=0.05, grain=0.1, blur=S * 0.012, backrun=0.1)
    nz = fft_noise(S, S, beta=2.6, seed=seed + 3)
    A = A * (0.72 + 0.28 * nz)
    return save('duman_%d' % i, T, A)


def kivilcim(W=32, H=128, seed=60):
    rng = np.random.default_rng(seed)
    s, c = _surface(W, H)
    bend = rng.uniform(-0.12, 0.12) * W
    pts = [(W * 0.5, H * 0.9), (W * 0.5 + bend * 0.5, H * 0.55), (W * 0.5 + bend, H * 0.06)]
    taper(c, pts, W * 0.42, 0.4, wmid=W * 0.3)
    cov = _arr(s)
    T, A = finish(cov, W, H, seed, rim=0.15, rim_w=0.25, grain=0.06, blur=0.6)
    ys = (np.arange(H)[:, None] + 0.5) / H
    T = np.clip(T * (0.85 + 0.15 * ys), 0, 1)
    return save('kivilcim', T, A)


def yildiz(S=128, seed=70, n=4, name='yildiz', core=0.07, lens=(0.44, 0.47)):
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    cx = cy = S * 0.5
    a0 = rng.uniform(-0.1, 0.1) + (math.pi / 4 if n == 4 else 0)
    a0 = rng.uniform(-0.08, 0.08)
    for i in range(n):
        a = a0 + i * 2 * math.pi / n + rng.uniform(-0.12, 0.12) * (n > 4)
        L = S * rng.uniform(*lens) * (1.0 if (n == 4 or i % 2 == 0) else 0.6)
        b = rng.uniform(-0.08, 0.08)
        pts = [(cx, cy), (cx + math.cos(a + b * 0.3) * L * 0.5, cy + math.sin(a + b * 0.3) * L * 0.5),
               (cx + math.cos(a + b) * L, cy + math.sin(a + b) * L)]
        taper(c, pts, S * (0.11 if n == 4 else 0.08), 0.4, wmid=S * 0.04)
    _blob_pts(c, cx, cy, S * core, rng, jit=0.2)
    cov = _arr(s)
    T, A = finish(cov, S, S, seed, rim=0.12, rim_w=0.05, grain=0.05, blur=0.7)
    return save(name, T, A)


def alev(W=64, H=128, seed=80):
    rng = np.random.default_rng(seed)
    s, c = _surface(W, H)
    cx = W * 0.5
    sw = rng.uniform(0.12, 0.2) * W
    pts = [(cx, H * 0.86), (cx - sw * 0.6, H * 0.6), (cx + sw, H * 0.34), (cx - sw * 0.3, H * 0.08)]
    taper(c, pts, W * 0.62, 0.8, wmid=W * 0.4)
    # yan dilleri
    for side in (-1, 1):
        if rng.random() < 0.8:
            p0 = (cx + side * W * 0.16, H * 0.72)
            taper(c, [p0, (cx + side * W * 0.3, H * 0.5), (cx + side * W * 0.22, H * 0.3)], W * 0.2, 0.5)
    cov = _arr(s)
    T, A = finish(cov, W, H, seed, rim=0.22, rim_w=0.08, grain=0.1, blur=0.8)
    ys = (np.arange(H)[:, None] + 0.5) / H
    A = A * smoothstep(0.99, 0.8, ys)   # taban yumuşak
    return save('alev', T, A)


def halka(S=256, seed=90):
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    cx = cy = S * 0.5
    R0 = S * 0.41
    a0 = rng.uniform(0, 6.28)
    pts = []
    for t in np.linspace(0, 1, 48):
        a = a0 + math.radians(345) * t
        rr = R0 * (1 + 0.025 * math.sin(3 * a + 1.3))
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    taper(c, pts, S * 0.05, S * 0.006, wmid=S * 0.042)
    cov = _arr(s)
    T, A = finish(cov, S, S, seed, rim=0.2, rim_w=0.01, grain=0.1, blur=0.7)
    # kuru fırça: açı boyunca kıl çizgileri
    ys, xs = np.mgrid[0:S, 0:S] + 0.5
    r = np.hypot(xs - cx, ys - cy)
    nz = fft_noise(64, 256, beta=1.4, seed=seed + 1, fx=0.2, fy=1.0)
    ri = np.clip((r - R0 + S * 0.04) / (S * 0.08) * 63, 0, 63)
    ai = ((np.arctan2(ys - cy, xs - cx) / (2 * math.pi)) % 1.0) * 256
    st = ndimage.map_coordinates(nz, [ri, ai], order=1, mode='wrap')
    A = A * (0.5 + 0.5 * smoothstep(0.25, 0.6, st))
    return save('halka', T, A)


def kul(S=64, seed=100):
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    n = int(rng.integers(6, 9))
    path = skia.Path()
    for i in range(n):
        a = i * 2 * math.pi / n + rng.uniform(-0.25, 0.25)
        rr = S * rng.uniform(0.24, 0.42) * (1.0 if i % 2 == 0 else 0.8)
        x, y = S * 0.5 + math.cos(a) * rr, S * 0.5 + math.sin(a) * rr * 0.75
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    path.close()
    c.drawPath(path, skia.Paint(AntiAlias=True, Color=skia.Color4f(1, 1, 1, 1)))
    cov = _arr(s)
    T, A = finish(cov, S, S, seed, rim=0.55, rim_w=0.09, grain=0.2, blur=0.6, holes=0.22)
    return save('kul', T, A)


def damla(S=64, seed=110):
    s, c = _surface(S, S)
    taper(c, [(S * 0.5, S * 0.06), (S * 0.5, S * 0.4), (S * 0.5, S * 0.7)], 0.6, S * 0.4, cap=False)
    c.drawCircle(S * 0.5, S * 0.7, S * 0.2, skia.Paint(AntiAlias=True, Color=skia.Color4f(1, 1, 1, 1)))
    cov = _arr(s)
    T, A = finish(cov, S, S, seed, rim=0.3, rim_w=0.08, grain=0.05, blur=0.6)
    return save('damla', T, A)


def cizgi(W=256, H=32, seed=120):
    rng = np.random.default_rng(seed)
    s, c = _surface(W, H)
    b = rng.uniform(-0.12, 0.12) * H
    taper(c, [(W * 0.04, H * 0.5), (W * 0.35, H * 0.5 + b), (W * 0.97, H * 0.5 - b * 0.4)], H * 0.82, 0.5, wmid=H * 0.5)
    cov = _arr(s)
    T, A = finish(cov, W, H, seed, rim=0.25, rim_w=0.12, grain=0.08, blur=0.6)
    # kıl çizgileri boyuna; kuyruğa doğru kurur
    nz = fft_noise(H, W, beta=1.5, seed=seed + 1, fx=0.08, fy=1.6)
    xs = (np.arange(W)[None, :] + 0.5) / W
    dry = smoothstep(0.3, 1.0, xs)
    A = A * (1.0 - dry * (1.0 - smoothstep(0.3, 0.55, nz)))
    return save('cizgi', T, A)


def kan(i, S=128):
    seed = 130 + i
    rng = np.random.default_rng(seed)
    s, c = _surface(S, S)
    cx, cy = S * 0.5, S * 0.5
    _blob_pts(c, cx, cy, S * rng.uniform(0.17, 0.23), rng, jit=0.3)
    for k in range(int(rng.integers(5, 9))):
        a = rng.uniform(0, 6.28)
        L = S * rng.uniform(0.26, 0.45)
        w0 = S * rng.uniform(0.05, 0.1)
        taper(c, [(cx, cy), (cx + math.cos(a) * L * 0.55, cy + math.sin(a) * L * 0.55), (cx + math.cos(a + 0.08) * L, cy + math.sin(a + 0.08) * L)], w0, 0.6, wmid=w0 * 0.6)
    for k in range(int(rng.integers(8, 16))):
        a = rng.uniform(0, 6.28)
        rr = S * rng.uniform(0.3, 0.47)
        drop(c, cx + math.cos(a) * rr, cy + math.sin(a) * rr, S * rng.uniform(0.008, 0.025), a, rng.uniform(1.0, 2.0))
    cov = roughen(_arr(s), seed, 0.3, 1.0)
    T, A = finish(cov, S, S, seed, rim=0.4, rim_w=0.05, grain=0.12, blur=0.5)
    return save('kan_%d' % i, T, A)


def catlak(i, W=256, H=64):
    seed = 150 + i
    rng = np.random.default_rng(seed)
    s, c = _surface(W, H)
    n = 9
    pts = []
    for k in range(n):
        x = W * (0.06 + 0.88 * k / (n - 1))
        y = H * 0.5 + rng.uniform(-0.18, 0.18) * H
        pts.append((x, y))
    # merkez kalın, uçlar ince: iki yarı
    mid = n // 2
    taper(c, pts[mid::-1], H * 0.16, 0.5, wmid=H * 0.09)
    taper(c, pts[mid:], H * 0.16, 0.5, wmid=H * 0.09)
    for k in range(int(rng.integers(3, 6))):
        j = int(rng.integers(1, n - 1))
        x0, y0 = pts[j]
        a = rng.choice([-1, 1]) * rng.uniform(0.5, 1.2) + (0 if rng.random() < 0.5 else math.pi)
        L = W * rng.uniform(0.08, 0.16)
        taper(c, [(x0, y0), (x0 + math.cos(a) * L * 0.5, y0 + math.sin(a) * L * 0.3), (x0 + math.cos(a) * L, y0 + math.sin(a) * L * 0.5)], H * 0.07, 0.4)
    cov = _arr(s)
    T, A = finish(cov, W, H, seed, rim=0.1, rim_w=0.2, grain=0.1, blur=0.6)
    return save('catlak_%d' % i, T, A)


def yaprak(S=64, seed=170):
    s, c = _surface(S, S)
    taper(c, [(S * 0.12, S * 0.6), (S * 0.45, S * 0.42), (S * 0.9, S * 0.38)], S * 0.04, 0.6, wmid=S * 0.34)
    taper(c, [(S * 0.04, S * 0.7), (S * 0.14, S * 0.6)], S * 0.03, S * 0.03)
    cov = _arr(s)
    T, A = finish(cov, S, S, seed, rim=0.25, rim_w=0.1, grain=0.08, blur=0.6)
    return save('yaprak', T, A)


def serit(W=128, H=32, seed=180):
    """Şerit fırça: u boyunca sarar (kıl çizgileri), v enine yumuşak kenarlı. Çoklu nokta fırça çizgileri
    (InkDraw.line: şimşek, kement, bağ) bu dokuyla dörtgen dörtgen döşenir."""
    v = (np.arange(H)[:, None] + 0.5) / H
    nz = fft_noise(H, W, beta=1.4, seed=seed, fx=0.1, fy=1.5)
    edge = smoothstep(0.0, 0.2, v) * smoothstep(1.0, 0.8, v)
    A = edge * (0.72 + 0.28 * smoothstep(0.3, 0.65, nz))
    T = 1.0 - 0.3 * (1.0 - smoothstep(0.1, 0.4, np.minimum(v, 1 - v))) - 0.08 * nz
    T = np.broadcast_to(T, (H, W))
    return save('serit', np.clip(T, 0, 1), np.clip(A, 0, 1))


def build():
    out = {}
    out['nokta'] = nokta()
    for i in range(3):
        out['leke_%d' % i] = leke(i)
    for i in range(2):
        out['duman_%d' % i] = duman(i)
    out['kivilcim'] = kivilcim()
    out['yildiz'] = yildiz()
    out['yildiz2'] = yildiz(seed=75, n=7, name='yildiz2', core=0.1, lens=(0.3, 0.46))
    out['alev'] = alev()
    out['halka'] = halka()
    out['kul'] = kul()
    out['damla'] = damla()
    out['cizgi'] = cizgi()
    for i in range(3):
        out['kan_%d' % i] = kan(i)
    for i in range(2):
        out['catlak_%d' % i] = catlak(i)
    out['yaprak'] = yaprak()
    out['serit'] = serit()
    return out


def preview(out, path):
    cells = []
    for n, img in out.items():
        im = Image.fromarray(img, 'RGBA')
        k = 160 / max(im.size)
        im = im.resize((max(1, int(im.size[0] * k)), max(1, int(im.size[1] * k))), Image.LANCZOS)
        cells.append(im)
    W = 170 * 6
    rows = (len(cells) + 5) // 6
    sheet = Image.new('RGBA', (W, rows * 340), (236, 226, 204, 255))
    for i, im in enumerate(cells):
        x, y = (i % 6) * 170 + 5, (i // 6) * 340 + 5
        # üstte kâğıt üzerinde koyu mürekkep, altta gece zemininde parlak
        a = np.asarray(im)[..., 3:4].astype(float) / 255
        t = np.asarray(im)[..., :1].astype(float) / 255
        ink = np.dstack([np.full(a.shape[:2] + (1,), 20) * (0.6 + 0.4 * (1 - t)), np.full(a.shape[:2] + (1,), 16) * 1.0, np.full(a.shape[:2] + (1,), 30)]).astype(np.uint8)
        ink = Image.fromarray(np.concatenate([ink, (a * 255).astype(np.uint8)], 2), 'RGBA')
        sheet.alpha_composite(ink, (x, y))
        bg = Image.new('RGBA', (160, 160), (24, 22, 36, 255))
        warm = np.asarray(im).astype(float)
        warm[..., 0] *= 1.0; warm[..., 1] *= 0.62; warm[..., 2] *= 0.3
        bg.alpha_composite(Image.fromarray(warm.astype(np.uint8), 'RGBA'), (0, 0))
        sheet.alpha_composite(bg, (x, y + 168))
    sheet.save(path)


if __name__ == '__main__':
    out = build()
    if '--onizleme' in sys.argv:
        preview(out, sys.argv[sys.argv.index('--onizleme') + 1])
    print('ink_p: %d doku -> %s' % (len(out), OUT))
