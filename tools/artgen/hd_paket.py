"""HD doku paketi (stil v2) son işlem ve denetim: assets_hd/x2 altındaki 2 kat çözünürlüklü v2 dokuları.

Kullanım (tools/artgen içinde):
    python hd_paket.py --kontrol [göreli yol önekleri...]   HD PNG/WebP'leri temel dokuyla karşılaştırır (boyut tam 2 kat mı,
                                                           2x2 küçültülmüş hâli temel dokuya ne kadar yakın) ve özetler
    python hd_paket.py --paketle                            PNG -> WebP (kayıplı q90 alfa kayıpsız, ya da daha küçükse tümüyle
                                                           kayıpsız), .import (BPTC + mipmap),
                                                           manifest.json (temel boyut + dosya); PNG silinir
    python hd_paket.py --boyut                              paket boyutu özeti

manifest.json: {"<göreli temel yol>": [temel_g, temel_y, "<göreli HD dosya>", "<temel PNG md5>"]} (HD dosyası .webp; md5
tutmazsa oyun temel dokuyu kullanır; v30: eski v1 [temel_g, temel_y] girdileri ve x4 paketi kaldırıldı). Data.tex() HD dokuyu yükler ve ImageTexture.set_size_override ile temel boyutta raporlar: bölgeler,
kareler, köken ve dünya boyu değişmez, yalnızca ayrıntı artar.
Neden WebP: 2 kat dokular PNG olarak ~3 kat yer tutar (depo GitHub'da paylaşılıyor). Kayıplı WebP q90 (alfa kayıpsız,
renk 4:2:0 = HD'nin yarısı = temel çözünürlükte renk) temel PNG'nin ~0,6'sı; oyun zaten BPTC'ye yeniden sıkıştırıyor.
"""
import glob
import hashlib
import json
import os
import re
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = os.path.join(ROOT, 'assets')
X2 = os.path.join(ROOT, 'assets_hd', 'x2')
MAN = os.path.join(X2, 'manifest.json')
SCALE = 2
WEBP_Q = 90

IMPORT_TMPL = """[remap]

importer="texture"
type="CompressedTexture2D"

[deps]

source_file="res://assets_hd/x2/{rel}"

[params]

compress/mode={mode}
compress/high_quality={hq}
compress/lossy_quality=0.7
compress/uastc_level=0
compress/rdo_quality_loss=0.0
compress/hdr_compression=1
compress/normal_map=0
compress/channel_pack=0
mipmaps/generate=true
mipmaps/limit=-1
roughness/mode=0
roughness/src_normal=""
process/channel_remap/red=0
process/channel_remap/green=1
process/channel_remap/blue=2
process/channel_remap/alpha=3
process/fix_alpha_border=true
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_as_srgb=false
process/hdr_clamp_exposure=false
process/size_limit=0
detect_3d/compress_to=1
"""


def is_v2(rel):
    """Bu paketin kapsadığı v2 renk dokuları (v1 eski x2 dosyaları dokunulmaz)."""
    r = rel.replace('\\', '/')
    n = os.path.basename(r)
    return '_v2' in n or r.startswith('fx/ink/') or r.startswith('ui/ink/')


def hd_files(prefixes=()):
    out = []
    for p in glob.glob(os.path.join(X2, '**', '*.*'), recursive=True):
        if not p.lower().endswith(('.png', '.webp')):
            continue
        rel = os.path.relpath(p, X2).replace('\\', '/')
        if not is_v2(rel):
            continue
        if prefixes and not any(rel.startswith(x) for x in prefixes):
            continue
        out.append(rel)
    return sorted(out)


def base_of(rel):
    return os.path.splitext(rel)[0] + '.png'


def _premul(a):
    a = a.astype(np.float32) / 255.0
    a[..., :3] *= a[..., 3:4]
    return a


def check(rel):
    """(durum, metin): boyut ve 2x2 küçültme farkı (önçarpılmış RGBA, 0..1)."""
    b = base_of(rel)
    bp = os.path.join(A, b)
    if not os.path.exists(bp):
        return 'TEMEL_YOK', '%s: temel doku yok (%s)' % (rel, b)
    bi = Image.open(bp).convert('RGBA')
    hi = Image.open(os.path.join(X2, rel)).convert('RGBA')
    if hi.size != (bi.size[0] * SCALE, bi.size[1] * SCALE):
        return 'BOYUT', '%s: boyut %s, beklenen %s' % (rel, hi.size, (bi.size[0] * SCALE, bi.size[1] * SCALE))
    B = _premul(np.asarray(bi))
    H = _premul(np.asarray(hi))
    h, w = B.shape[:2]
    D = H.reshape(h, SCALE, w, SCALE, 4).mean(axis=(1, 3))
    d = np.abs(D - B)
    m = float(d.mean())
    p99 = float(np.percentile(d, 99))
    cov = float((B[..., 3] > 0.02).mean())
    st = 'TAMAM' if (m < 0.012 and p99 < 0.2) else ('UYARI' if m < 0.03 else 'FARKLI')
    return st, '%-6s %-48s %5dx%-5d ort %.4f p99 %.3f doluluk %.2f' % (st, rel, hi.size[0], hi.size[1], m, p99, cov)


def kontrol(prefixes):
    files = hd_files(prefixes)
    cnt = {}
    for rel in files:
        st, txt = check(rel)
        cnt[st] = cnt.get(st, 0) + 1
        print(txt, flush=True)
    print('özet:', cnt, 'dosya', len(files))


def _write_import(path, rel):
    imp = path + '.import'
    # büyük ayrıntılı dokular BPTC (VRAM sıkıştırmalı, yüksek kalite); çok küçükler kayıpsız
    w, h = Image.open(path).size
    vram = w * h >= 256 * 256
    mode, hq = ('2', 'true') if vram else ('0', 'false')
    if os.path.exists(imp):
        txt = open(imp, encoding='utf-8').read()
        new = re.sub(r'compress/mode=\d', 'compress/mode=' + mode, txt)
        new = re.sub(r'compress/high_quality=\w+', 'compress/high_quality=' + hq, new)
        new = new.replace('mipmaps/generate=false', 'mipmaps/generate=true')
        if new != txt:
            open(imp, 'w', encoding='utf-8', newline='\n').write(new)
    else:
        open(imp, 'w', encoding='utf-8', newline='\n').write(IMPORT_TMPL.format(rel=rel, mode=mode, hq=hq))


def _encode(rel):
    """Bir HD PNG'yi denetle ve WebP'ye çevir; (yeni göreli yol | None, metin)."""
    p = os.path.join(X2, rel)
    st, txt = check(rel)
    if st in ('TEMEL_YOK', 'BOYUT'):
        return None, 'ATLANDI ' + txt
    im = Image.open(p).convert('RGBA')
    wp = os.path.splitext(p)[0] + '.webp'
    # kayıplı q90 ile kayıpsız WebP'den küçük olanı (seyrek / düz renkli dokularda kayıpsız çoğu zaman daha küçük)
    im.save(wp, format='WEBP', quality=WEBP_Q, method=6, alpha_quality=100)
    lossy = os.path.getsize(wp) if not rel.endswith('_mask.png') else 1 << 40   # maske = veri: hep kayıpsız
    ll = wp + '.ll'
    im.save(ll, format='WEBP', lossless=True, quality=80, method=4)
    if os.path.getsize(ll) < lossy:
        os.replace(ll, wp)
        txt += '  (kayıpsız)'
    else:
        os.remove(ll)
    os.remove(p)
    if os.path.exists(p + '.import'):
        os.remove(p + '.import')
    return os.path.splitext(rel)[0] + '.webp', txt


def paketle():
    from concurrent.futures import ProcessPoolExecutor
    man = json.load(open(MAN, encoding='utf-8')) if os.path.exists(MAN) else {}
    files = hd_files()
    pngs = [r for r in files if r.lower().endswith('.png')]
    done = [r for r in files if not r.lower().endswith('.png')]
    with ProcessPoolExecutor(max_workers=max(1, (os.cpu_count() or 2) - 1)) as pool:
        for rel, txt in pool.map(_encode, pngs):
            print(txt, flush=True)
            if rel:
                done.append(rel)
    for rel in sorted(done):
        p = os.path.join(X2, rel)
        b = base_of(rel)
        bw, bh = Image.open(os.path.join(A, b)).size
        # temel PNG özeti: temel doku sonradan yeniden üretilirse Data eski HD'yi kullanmaz
        md5 = hashlib.md5(open(os.path.join(A, b), 'rb').read()).hexdigest()
        man[b] = [bw, bh, rel, md5]
        _write_import(p, rel)
    man = dict(sorted(man.items()))
    json.dump(man, open(MAN, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print('manifest:', len(man), 'giriş (v2:', sum(1 for v in man.values() if len(v) > 2), ')')
    boyut()


def boyut():
    tot = {}
    for rel in hd_files():
        k = rel.split('/')[0]
        tot.setdefault(k, [0, 0])
        tot[k][0] += 1
        tot[k][1] += os.path.getsize(os.path.join(X2, rel))
    s = 0
    for k, (n, b) in sorted(tot.items()):
        print('%-8s %4d dosya %7.1f MB' % (k, n, b / 1e6))
        s += b
    print('v2 HD toplam %.1f MB' % (s / 1e6))


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--paketle' in a:
        paketle()
    elif '--boyut' in a:
        boyut()
    else:
        kontrol([x for x in a if not x.startswith('--')])
