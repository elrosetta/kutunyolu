"""HD doku paketi (stil v2, "Doku kalitesi" 2K / 4K): aynı prosedürel çizimin 2 kat çözünürlükte yeniden üretimi.

Kullanım: dışa aktarım betiklerini KY_HD=2 ortam değişkeniyle çalıştır (tools/artgen/hd_v2.py hepsini sırayla yapar):
    KY_HD=2 python export_ink.py --bengu
Bu kip etkinken:
  * HD = 2: çizim takımları (inkkit.InkCanvas, inkkit_ortam.K, ...) doku yoğunluğunu, tuval boyunu, çizgi kalınlığını
    ve piksel cinsinden bulanıklık / doku tanesi yarıçaplarını HD ile çarpar: dünya boyu aynı, yalnızca ayrıntı artar
    (bitmap büyütme YOK; vektör/numpy çizim yeni çözünürlükte baştan yapılır).
  * assets/ altına yapılan PNG yazımları (PIL Image.save) assets_hd/x2/ altına AYNI göreli yolla yönlenir; ışıma (_e) ve
    normal (_n) dokuları yazılmaz (oyun onları temel çözünürlükte kullanır). json / .import yazımları da
    temel dosyaları ezmesin diye geçici klasöre gider (HD_META: karşılaştırma için saklanır). Zemin maskesi ve karo
    ışıma atlası (TileSet'te atlasla aynı boyda olmalı) pakete girer.
Sonra `python hd_paket.py` manifest.json'u, .import ayarlarını (BPTC + mipmap) ve WebP kodlamasını yapar ve her HD
dokunun küçültülmüş hâlini temel dokuyla karşılaştırır.
"""
import builtins
import os

HD = max(1, int(os.environ.get('KY_HD', '1') or '1'))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(ROOT, 'assets')
OUT = os.path.join(ROOT, 'assets_hd', 'x%d' % HD)
HD_META = os.path.join(ROOT, '.godot', 'hd_meta')     # HD kipinde yazılan json'lar (depoya girmez)

# HD'ye girmeyen dokular: ışıma / normal (temel çözünürlükte kalır). İstisna: karo atlasıyla aynı TileSet'te çizilen
# zemin maskesi (<biyom>_v2_mask, CanvasTexture normal yuvası: boyutu atlasla aynı olmalı) ve karo ışıma atlası
# (<biyom>_v2_e, aynı karo boyunu kullanır) pakete girer.
SKIP_SUFFIX = ('_e.png', '_n.png')
KEEP = ('tiles/otuken_v2_e.png', 'tiles/bozkir_v2_e.png', 'tiles/kaf_v2_e.png', 'tiles/sahmeran_v2_e.png',
        'tiles/tamu_v2_e.png')


def _norm(p):
    return os.path.normcase(os.path.abspath(os.fspath(p)))


def redirect(path):
    """assets/... -> assets_hd/x<HD>/... (HD kipi); yazılmaması gerekenler için None. Kip kapalıyken aynen döner."""
    if HD <= 1:
        return path
    ap = _norm(path)
    if not ap.startswith(_norm(ASSETS) + os.sep):
        return path
    rel = os.path.relpath(os.path.abspath(os.fspath(path)), ASSETS)
    low = rel.lower()
    if low.endswith('.json') or low.endswith('.import') or (low.endswith(SKIP_SUFFIX) and low.replace(os.sep, '/') not in KEEP):
        return os.path.join(HD_META, rel)
    return os.path.join(OUT, rel)


def is_hd():
    return HD > 1


def _install():
    from PIL import Image
    orig_save = Image.Image.save

    def save(self, fp, format=None, **params):
        if isinstance(fp, (str, os.PathLike)):
            fp2 = redirect(fp)
            os.makedirs(os.path.dirname(fp2), exist_ok=True)
            fp = fp2
        return orig_save(self, fp, format, **params)
    Image.Image.save = save

    orig_open = builtins.open

    def hd_open(file, mode='r', *a, **kw):
        if isinstance(file, (str, os.PathLike)) and any(m in mode for m in 'wax'):
            f2 = redirect(file)
            if f2 != file:
                os.makedirs(os.path.dirname(f2), exist_ok=True)
                file = f2
        return orig_open(file, mode, *a, **kw)
    builtins.open = hd_open

    orig_remove = os.remove

    def remove(p, *a, **kw):
        # HD kipinde temel varlıkları silme (eski sayfa temizliği vb.)
        if _norm(p).startswith(_norm(ASSETS) + os.sep):
            return None
        return orig_remove(p, *a, **kw)
    os.remove = remove


if HD > 1:
    _install()
