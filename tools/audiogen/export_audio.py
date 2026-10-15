"""Tüm sesleri üretir: assets/audio/sfx/*.wav (44.1 kHz mono; ortam döngüleri 22.05 kHz) ve assets/audio/music/*.wav (22.05 kHz mono).
Sıra: sfx.py (eski sentez) -> layer.py (CC0 kayıt katmanları) -> pro.py (v9 katmanları, üstüne yazar) -> mastering.
Mastering: her ses kategorisine göre aynı algılanan yüksekliğe (synth.loudness) getirilir, tepe -1 dBFS'de yumuşak sınırlanır.
Böylece çağrı yerlerindeki vol_db farkları gerçekten kategori farkı olur (eskiden her dosya tepeden eşitleniyordu: kısa
vuruşlar uzun seslerden algıda çok daha kısık kalıyordu).
Kullanım: python tools/audiogen/export_audio.py [--sfx] [--music] [ad ...]   Denetim: python tools/audiogen/check.py"""
import os
import re
import sys
import json
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from synth import write_wav, SR, master
import sfx as S
import music as Mu

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'audio')
os.makedirs(os.path.join(A, 'sfx'), exist_ok=True)
os.makedirs(os.path.join(A, 'music'), exist_ok=True)
args = sys.argv[1:]
only = [a for a in args if not a.startswith('-')]
do_sfx = '--sfx' in args or not any(a.startswith('-') for a in args)
do_music = '--music' in args or not any(a.startswith('-') for a in args)

# Kategori -> hedef yükseklik (dB, synth.loudness ölçüsü). İlk eşleşen kural geçerli.
TARGETS = [
    (r'^ortam_', -21.0), (r'^kalp_dongu$', -13.0), (r'_dongu$', -17.0),
    (r'^darbe_(kritik|cekic)', -9.0), (r'^darbe_agir$', -9.5), (r'^darbe_', -10.0), (r'^ok_vurus', -11.0), (r'^ok_ucus', -17.0),
    (r'^(patlama|sarsinti)$', -8.0), (r'^(yildirim|kut_donusum)$', -9.0),
    (r'^savur_(dev|cekic|agir)', -12.0), (r'^(savur_|sapla$)', -13.0),
    (r'_olum$', -10.0), (r'^(hazirlik_|dusman_hazirlik$|kurt_hirlama|cor_fisilti|agac_inilti|tas_surtunme|surale_ciglik|kam_)', -13.0),
    (r'_can(_\d+)?$', -12.0), (r'^(isirik|sicrayis|uluma)', -11.0),
    (r'^adim_', -20.0), (r'^inis_', -15.0), (r'^(zipla|yuvarlan)$', -16.0),
    (r'^(ui_gez|ui_sec)', -21.0), (r'^npc_', -19.0), (r'^ui_', -17.0), (r'^esya_(kusan|degis)$', -15.0), (r'^(tilsim_sec|seviye)$', -12.0),
    (r'^altin', -16.0), (r'^kut_tane$', -16.0), (r'^(esya|tilsim|sise|acilis|ors|kut_banka|kapi)$', -13.0),
    (r'^yay_ger', -16.0), (r'^yay_dolu', -15.0), (r'^yay_birak', -12.0),
]


def target_for(name):
    for pat, db in TARGETS:
        if re.search(pat, name):
            return db
    return -12.0


if do_sfx:
    import layer as L
    import pro as P
    allsfx = {}
    t0 = time.time()
    for name, fn in S.SFX.items():
        if only and name not in only:
            continue
        allsfx[name] = fn()
    for fn in (L.swings, L.hits, L.creatures, L.movement_pickups):
        allsfx.update(fn())
    allsfx.update(P.build_all())
    import bow2
    allsfx.update(bow2.build_bow())
    amb = P.ambience()
    print('üretildi:', len(allsfx) + len(amb), 'ses', round(time.time() - t0, 1), 's')
    meta = {}
    for name, x in sorted(allsfx.items()):
        if only and name not in only:
            continue
        loop = name.endswith('_dongu')
        y = master(x, target_for(name), loop=loop)
        write_wav(os.path.join(A, 'sfx', name + '.wav'), y, SR, None)
        meta[name] = {'loop': loop, 'len': round(len(y) / SR, 3), 'hedef_db': target_for(name)}
    for name, x in sorted(amb.items()):
        if only and name not in only:
            continue
        y = master(x, target_for(name), sr=P.AMB_SR, loop=True)
        write_wav(os.path.join(A, 'sfx', name + '.wav'), y, P.AMB_SR, None)
        meta[name] = {'loop': True, 'len': round(len(y) / P.AMB_SR, 3), 'hedef_db': target_for(name)}
    mp = os.path.join(A, 'sfx', 'sfx.json')
    if only and os.path.exists(mp):
        old = json.load(open(mp, encoding='utf-8'))
        old.update(meta)
        meta = old
    json.dump(meta, open(mp, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('sfx yazıldı:', len(meta))
if do_music:
    for biome in ['otuken', 'bozkir', 'sahmeran', 'kaf', 'tamu', 'boss', 'yurt', 'baslik']:
        if only and biome not in only:
            continue
        t0 = time.time()
        x = Mu.track(biome)
        x = master(x, Mu.TARGET_DB.get(biome, -15.0), ceiling=0.85, sr=Mu.MSR, loop=True)
        write_wav(os.path.join(A, 'music', biome + '.wav'), x, Mu.MSR, None)
        print('music', biome, round(len(x) / Mu.MSR, 1), 's', round(time.time() - t0, 1))
