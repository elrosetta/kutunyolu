"""Stil v2 HD doku paketini (assets_hd/x2, "Doku kalitesi" 2K / 4K) baştan üretir: her v2 dışa aktarım betiği KY_HD=2 ile
çalıştırılır (hdpack.py: aynı prosedürel çizim 2 kat çözünürlükte, çıktılar assets_hd/x2'ye, temel varlıklar ve json'lar
dokunulmaz), sonra hd_paket.py denetler ve paketler (WebP, .import, manifest.json).

Kullanım (tools/artgen içinde):
    python hd_v2.py                 hepsi (~1-2 saat, 12 çekirdek)
    python hd_v2.py karakter ortam  yalnızca bu gruplar (karakter, yaratik, boss, ortam, sus, silah, efekt, arayuz)
    python hd_v2.py --paketle       yalnızca son işlem
Temel bir doku yeniden üretildiyse karşılığını da HD'de yeniden üret: manifest'teki md5 tutmazsa oyun o doku için
temel sürüme düşer (uyarı verir).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

GROUPS = {
    'karakter': [['export_ink.py']],
    'yaratik': [['export_yaratik_a.py']],
    'boss': [['export_boss_ink.py']],
    'ortam': [['export_ink_ortam.py'], ['export_ink_biyom.py', 'bozkir', 'kaf'], ['export_ink_yeralti.py', 'hepsi']],
    'sus': [['export_sus.py']],          # yurt süsleri + yurt paralaksı (--yurt-bg) + ortak süsler, atlas, tehlike, efekt
    'silah': [['weapons_ink.py']],
    'efekt': [['inkfx.py']],
    'arayuz': [['ui_ink.py']],
}


def run(cmd):
    env = dict(os.environ, KY_HD='2')
    print('>>', 'KY_HD=2 python', ' '.join(cmd), flush=True)
    subprocess.run([sys.executable] + cmd, cwd=HERE, env=env, check=True)


def main():
    args = sys.argv[1:]
    if '--paketle' not in args:
        groups = [a for a in args if not a.startswith('--')] or list(GROUPS)
        for g in groups:
            for cmd in GROUPS[g]:
                run(cmd)
    subprocess.run([sys.executable, 'hd_paket.py', '--kontrol'], cwd=HERE, check=True)
    subprocess.run([sys.executable, 'hd_paket.py', '--paketle'], cwd=HERE, check=True)


if __name__ == '__main__':
    main()
