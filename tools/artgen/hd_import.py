"""4K paketini (assets_hd/x4) video belleğinde sıkıştırılmış (BC7) içe aktarılacak şekilde ayarlar.

Godot yeni PNG'ler için önce varsayılan (kayıpsız) .import dosyası üretir; bu betik x4 altındakileri
compress/mode=2 (VRAM) + high_quality (BC7) yapar. Sonra Godot'yu --import ile yeniden çalıştır.
4x dokular kayıpsız kalırsa tek bir boss sayfası ~160 MB video belleği tutar; BC7 ile ~40 MB.
Kullanım:  python tools/artgen/hd_import.py
"""
import glob
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
n = 0
for f in glob.glob(os.path.join(ROOT, 'assets_hd', 'x4', '**', '*.png.import'), recursive=True):
    s = open(f, encoding='utf-8').read()
    t = s.replace('compress/mode=0', 'compress/mode=2').replace('compress/high_quality=false', 'compress/high_quality=true')
    if t != s:
        open(f, 'w', encoding='utf-8', newline='\n').write(t)
        n += 1
print('x4 VRAM sıkıştırma:', n, 'dosya güncellendi')
