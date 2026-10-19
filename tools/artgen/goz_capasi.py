"""v25 Tepegöz göz çapası: sprite'ın ışıma sayfasındaki (<ad>_e.png, <ad>_p1_e.png) tek gözün parıltısından her
animasyon karesi için "eye" çapası hesaplar ve sprite json'una yazar (ayak noktasına göre dünya birimi, sağa bakış;
SpriteAnim.anchor yöne göre aynalar). Boss._tg_eye bu çapayı kullanır: göz ışını her karede, iki yöne ve taramada
gözden çıkar (eskiden gövde boyunun %67'si tahmini: ışın alakasız yerden çıkıyordu).

Kullanım: python tools/artgen/goz_capasi.py [tepegoz_v2 tepegoz]   (proje kökünden)
Yöntem: "mouth" çapasının üstündeki pencerede (ağzın 2-34 birim yukarısı, -30..+30 yanı) ışıma parlaklığı eşiği aşan
pikseller bağlı bileşenlere ayrılır; beklenen göz yerine (ağzın ~12 birim üstü) en yakın, en az 6 piksellik bileşenin
parlaklık ağırlıklı merkezi alınır. Göz kolun / gürzün arkasında kalan karelerde (parıltı yok) ağıza, bulunan karelerin
ortalama göz - ağız farkı eklenir.
"""
import json
import os
import sys

from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
SP = os.path.join(ROOT, 'assets', 'sprites')


def glow_pages(name, meta):
    pages = []
    n = int(meta.get('pages', 1))
    for p in range(n):
        fn = '%s_e.png' % name if p == 0 else '%s_p%d_e.png' % (name, p)
        path = os.path.join(SP, fn)
        pages.append(Image.open(path).convert('RGBA') if os.path.exists(path) else None)
    return pages


def find_eye(img, box, expect, thr=110):
    """box: (x0, y0, x1, y1) ışıma pikselinde; expect: (x, y). Dönüş: ağırlıklı merkez ya da None"""
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(img.width, x1), min(img.height, y1)
    if x1 <= x0 or y1 <= y0:
        return None
    px = img.load()
    w = {}
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = px[x, y]
            v = (max(r, g, b) * a) // 255
            if v >= thr:
                w[(x, y)] = v
    seen = set()
    best = None
    bd = 1e9
    for p in w:
        if p in seen:
            continue
        comp = []
        st = [p]
        seen.add(p)
        while st:
            q = st.pop()
            comp.append(q)
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                n = (q[0] + d[0], q[1] + d[1])
                if n in w and n not in seen:
                    seen.add(n)
                    st.append(n)
        if len(comp) < 6:
            continue
        tw = sum(w[c] for c in comp)
        cx = sum(c[0] * w[c] for c in comp) / tw
        cy = sum(c[1] * w[c] for c in comp) / tw
        dist = ((cx - expect[0]) ** 2 + (cy - expect[1]) ** 2) ** 0.5
        if dist < bd:
            bd = dist
            best = (cx, cy)
    return best


def run(name):
    jp = os.path.join(SP, name + '.json')
    meta = json.load(open(jp, encoding='utf-8'))
    texel = float(meta.get('texel', 1.0))
    gk = float(meta.get('glow_scale', 1.0))
    cw, ch = meta['cell']
    ox, oy = meta['origin']
    pages = glow_pages(name, meta)
    rows_pp = int(meta.get('page_rows', 9999))
    found = 0
    total = 0
    deltas = []
    miss = []
    for an, a in meta['anims'].items():
        data = a.get('data', [])
        for f in range(int(a['frames'])):
            total += 1
            if f >= len(data):
                data.append({})
            d = data[f]
            mouth = d.get('mouth')
            d.pop('eye', None)
            if 'page' in a:
                cols = max(1, int(a.get('cols', 9999)))
                pg = int(a['page'])
                row = int(a['row']) + f // cols
                col = f % cols
            else:
                row = int(a['row'])
                col = f
                pg = min(row // rows_pp, len(pages) - 1)
                row -= pg * rows_pp
            img = pages[pg] if pg < len(pages) else None
            eye = None
            if img is not None and mouth is not None:
                # dünya -> ışıma pikseli (kare içi)
                mx = (ox + mouth[0] * texel) / gk
                my = (oy + mouth[1] * texel) / gk
                k = texel / gk
                bx, by = col * cw / gk, row * ch / gk
                box = (bx + mx - 30 * k, by + my - 34 * k, bx + mx + 30 * k, by + my - 2 * k)
                c = find_eye(img, box, (bx + mx - 6 * k, by + my - 12 * k))
                if c is not None:
                    ex = (c[0] - bx) * gk
                    ey = (c[1] - by) * gk
                    eye = [round((ex - ox) / texel, 2), round((ey - oy) / texel, 2)]
                    found += 1
                    deltas.append((eye[0] - mouth[0], eye[1] - mouth[1]))
            if eye is None:
                miss.append((d, mouth))
            else:
                d['eye'] = eye
        a['data'] = data
    mdx = sum(v[0] for v in deltas) / max(1, len(deltas)) if deltas else -6.0
    mdy = sum(v[1] for v in deltas) / max(1, len(deltas)) if deltas else -12.0
    for d, mouth in miss:
        d['eye'] = [round(mouth[0] + mdx, 2), round(mouth[1] + mdy, 2)] if mouth else [20.0, -100.0]
    raw = open(jp, 'rb').read()
    crlf = b'\r\n' in raw
    out = json.dumps(meta, ensure_ascii=False, separators=(',', ':')) if b'\n' not in raw.strip() else json.dumps(meta, ensure_ascii=False, indent=1)
    if crlf:
        out = out.replace('\n', '\r\n')
    open(jp, 'wb').write(out.encode('utf-8'))
    print('%s: göz bulundu %d / %d kare' % (name, found, total))


if __name__ == '__main__':
    for n in (sys.argv[1:] or ['tepegoz_v2', 'tepegoz']):
        run(n)
