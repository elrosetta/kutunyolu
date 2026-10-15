"""HD doku paketleri (2K / 4K): aynı üreticileri N kat piksel yoğunluğunda çalıştırır.

Kullanım:  python tools/artgen/export_hd.py 2      (2K paketi -> assets_hd/x2)
           python tools/artgen/export_hd.py 4      (4K paketi -> assets_hd/x4)
           python tools/artgen/export_hd.py 2 --only sprites,weapons   (bölüm seç: sprites, npc, decor, weapons, fx,
                                                                         bg, tiles, yurt_hd, fx2)

Şekiller mantıksal birimde aynıdır; tuval N kat ince ızgarada rasterlanır (raster.SS), yani her şey gerçekten
daha ayrıntılı yeniden çizilir (büyütme değil). Yalnızca renk dokuları yazılır; normal ve parlama haritaları
ve JSON meta temel sürümden kullanılır. assets_hd/xN/manifest.json: göreli yol -> temel [genişlik, yükseklik].
Oyun (Data.tex) dokuyu bu temel boyutta raporlar: bölgeler, kareler ve çizim boyu değişmez.
"""
import io
import json
import os
import sys
import builtins

import raster

N = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 2
ONLY = set()
if '--only' in sys.argv:
    ONLY = set(sys.argv[sys.argv.index('--only') + 1].split(','))
raster.SS = N
ARGV = list(sys.argv)
sys.argv = [sys.argv[0]]  # export_assets kendi argümanlarını görmesin

import export_assets as E  # noqa: E402

HD = os.path.join(E.ROOT, 'assets_hd', 'x%d' % N)
MAN = os.path.join(HD, 'manifest.json')
manifest = json.load(open(MAN, encoding='utf-8')) if os.path.exists(MAN) else {}


MAX_TEX = 16384


def hd_save(arr, path):
    rel = os.path.relpath(path, E.A).replace(os.sep, '/')
    if rel.endswith('_n.png') or rel.endswith('_e.png'):
        return
    out = os.path.join(HD, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img = E.to_img(arr)
    h, w = arr.shape[:2]
    # GPU doku sınırı (çoğu kartta 16384): aşan sayfa tam sayı çarpanla küçültülür; oyun boyutu
    # manifestteki temel boyuttan aldığı için yalnızca yoğunluk düşer (ör. 4K silah atlası = 2K yoğunluğu)
    k = 1
    while max(w, h) // k > MAX_TEX:
        k += 1
    if k > 1:
        img = img.reduce(k)
    img.save(out)
    manifest[rel] = [int(round(w / N)), int(round(h / N))]
    print('  hd', rel, img.width, img.height, ('(GPU sınırı: 1/%d)' % k) if k > 1 else '', flush=True)


def save_png(img, rel):
    """PIL görüntüsü (fx vb.) için"""
    out = os.path.join(HD, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)
    manifest[rel] = [img.width // N, img.height // N]
    print('  hd', rel, img.width, img.height, flush=True)


def fake_open(p, mode='r', *a, **k):
    # temel JSON meta dosyalarını ezme (open 'w' dosyayı boşaltırdı)
    if 'w' in mode and str(p).endswith('.json'):
        return io.StringIO()
    return builtins.open(p, mode, *a, **k)


E.save = hd_save
E.open = fake_open


def want(part):
    return not ONLY or part in ONLY


def write_manifest():
    """Diskteki manifestle birleştirerek yaz (başka bir export_hd süreci aynı anda çalışabilir)."""
    os.makedirs(HD, exist_ok=True)
    disk = json.load(builtins.open(MAN, encoding='utf-8')) if os.path.exists(MAN) else {}
    disk.update(manifest)
    manifest.update(disk)
    with builtins.open(MAN, 'w', encoding='utf-8') as f:
        json.dump(disk, f, ensure_ascii=False, indent=1, sort_keys=True)


def rebuild_manifest():
    """--manifest: assets_hd/xN altındaki PNG'lerden manifesti yeniden kur (temel boyut = boyut / N)."""
    from PIL import Image
    out = {}
    for root, _, files in os.walk(HD):
        for fn in files:
            if fn.endswith('.png'):
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, HD).replace(os.sep, '/')
                w, h = Image.open(full).size
                out[rel] = [w // N, h // N]
    with builtins.open(MAN, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
    print('manifest', len(out))


if '--manifest' in ARGV:
    rebuild_manifest()
    sys.exit(0)

if want('sprites'):
    E._export_player()
    write_manifest()
    for nm_ in E.creatures.CREATURES:
        E._export_creature(nm_)
        write_manifest()
if want('npc'):
    for nm_ in E.yurt.NPC_STYLES:
        an2 = {k: (v[0], v[1], True) for k, v in E.yurt.NPC_ANIMS.items()}
        E.export_sheet('npc_' + nm_, an2, lambda an, i, nm_=nm_: E.yurt.render_npc(nm_, an, i), E.yurt.NPC_CELL, E.yurt.NPC_FEET)
    write_manifest()
if want('decor'):
    for k, fn in list(E.env_forest.DECOR.items()) + list(E.yurt.DECOR.items()):
        c = fn()
        E.save(c.shade(rim_amt=0.25), os.path.join(E.A, 'decor', k + '.png'))
    write_manifest()
if want('weapons'):
    import weapons_myth
    alb, nrm, glo, wmeta = weapons_myth.build_atlas()
    E.save(alb, os.path.join(E.A, 'weapons', 'weapons.png'))
    write_manifest()
if want('fx'):
    import arrows
    save_png(arrows.build_sheet(N), 'fx/arrows.png')
    write_manifest()
if want('bg'):
    # paralaks katmanları: aynı kompozisyon N kat ince ızgarada (bgkit.set_scale; gök 960N x 540N, diğerleri 1920N x 540N)
    import bgkit
    bgkit.set_scale(N)
    import bg_hd
    import bg_yurt
    for bid, layers in bg_hd.BIOME_LAYERS.items():
        for nm_, fn in layers:
            save_png(fn(), 'bg/%s_%s.png' % (bid, nm_))
        write_manifest()
    for nm_, fn in bg_yurt.LAYERS.items():
        save_png(fn(), 'bg/%s.png' % nm_)
    write_manifest()
if want('tiles'):
    # zemin atlası (aynı hücre düzeni, N kat) + dikişsiz toprak dokusu (N kat; oyun soil_density'yi N ile çarpar) + tehlike karoları
    import numpy as np
    import biomes
    import hazards
    E.soil.set_hd(N)
    for bid, bcfg in biomes.BIOMES.items():
        E.soil.set_biome(bcfg['soil'])
        Al, _nm, _tm = E.soil.build_ground_atlas()
        E.save(Al, os.path.join(E.A, 'tiles', bid + '.png'))
        st, _sn, _se = E.soil.soil_texture()
        E.save(np.dstack([st, np.ones(st.shape[:2])]), os.path.join(E.A, 'tiles', bid + '_soil.png'))
        write_manifest()
    E.soil.set_hd(1)
    E.soil.set_biome(biomes.BIOMES['otuken']['soil'])
    from PIL import Image
    alb = hazards.build()[0]
    save_png(Image.fromarray((np.clip(alb, 0, 1) * 255).astype(np.uint8), 'RGBA'), 'tiles/hazards.png')
    write_manifest()
if want('yurt_hd'):
    # v13 yurt süsleri (raster.SS ile N kat ince Canvas; decor.json "k": 1.5 aynen geçerli)
    import yurt_hd
    for k, fn in yurt_hd.DECOR.items():
        cv = fn()
        E.save(cv.shade(rim_amt=0.25), os.path.join(E.A, 'decor', k + '.png'))
    write_manifest()
if want('fx2'):
    # kesik/darbe/iz sayfaları (slashfx.SS = N; slash.json mantıksal boyutla aynı kalır)
    import slashfx
    slashfx.SS = N
    slashfx.build_all(lambda name, im: save_png(im, 'fx/slash/%s.png' % name))
    write_manifest()
write_manifest()
print('HD paketi x%d: %d doku -> %s' % (N, len(manifest), HD))
