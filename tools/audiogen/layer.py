"""Katmanlı ses tasarımı: gerçek CC0 kayıtlar (Kenney Impact/RPG Audio, OGA Swishes, OGA RPG Sound Pack) + sentez tatlandırıcı.
Silah türüne göre savuruş ve darbe sesleri, yaratık sesleri, adımlar, toplama. Kaynak kayıtlar SRC klasöründe beklenir:
  SRC/swishes/swish-N.wav, SRC/rpgpack/RPG Sound Pack/..., SRC/rpg/Audio/*.ogg (Kenney RPG), SRC/impact/Audio/*.ogg (Kenney Impact)
Kullanım: python layer.py tools/audiogen/src   (çıktı: assets/audio/sfx/*.wav)
Not (v9): olağan üretim export_audio.py üzerinden yapılır; o, bu katmanları pro.py ile geçersiz kılar ve yükseklik eşitler."""
import os
import sys
import glob
import math
import numpy as np
import soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, t_axis, exp_env, env, noise, fft_filter, sine, sweep, reverb, fade, normalize, write_wav, place
import sfx as SY

SRC = sys.argv[1] if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'audio', 'sfx')
_cache = {}


def load(rel):
    """Mono, 44.1 kHz, tepe 1.0'a ölçekli."""
    if rel in _cache:
        return _cache[rel]
    p = os.path.join(SRC, rel)
    if not os.path.exists(p):
        g = glob.glob(p)
        if not g:
            raise FileNotFoundError(p)
        p = g[0]
    x, sr = sf.read(p, always_2d=True)
    x = x.mean(axis=1)
    if sr != SR:
        n = int(len(x) * SR / sr)
        x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)
    x = x / (np.max(np.abs(x)) + 1e-9)
    _cache[rel] = x
    return x


def pitch(x, f):
    """f > 1 ince ve kısa; f < 1 kalın ve uzun (yeniden örnekleme)."""
    n = int(len(x) / f)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def trim(x, start=0.0, dur=None, fout=0.03):
    a = int(start * SR)
    b = len(x) if dur is None else min(len(x), a + int(dur * SR))
    y = x[a:b].copy()
    return fade(y, 0.002, min(fout, len(y) / SR * 0.5))


def tight(x, thresh=0.02):
    """Baştaki sessizliği at."""
    idx = np.argmax(np.abs(x) > thresh)
    return x[max(0, idx - 100):]


def sub(freq, dur, k=10.0, g=0.5):
    return sine(freq, dur) * exp_env(dur, k) * g


def ring(freqs, dur=0.25, g=0.06, k=30.0):
    return sum(sine(f, dur) * exp_env(dur, k + i * 8) for i, f in enumerate(freqs)) * g


def shimmer(dur=0.35, g=0.15):
    t = t_axis(dur)
    x = np.sin(2 * np.pi * 1400 * t + 3 * np.sin(2 * np.pi * 6 * t)) + 0.6 * np.sin(2 * np.pi * 2100 * t)
    return x * exp_env(dur, 7) * g


def build(parts, dur=None):
    """parts: [(dizi, zaman, kazanç), ...]"""
    n = max(int(t * SR) + len(x) for x, t, g in parts)
    if dur:
        n = max(n, int(dur * SR))
    out = np.zeros(n)
    for x, t, g in parts:
        place(out, x, t, g)
    return out


SW = {k: lambda k=k: tight(load('swishes/swishes/swish-%d.wav' % k)) for k in range(1, 14)}
RP = lambda rel: tight(load('rpgpack/RPG Sound Pack/' + rel))
KR = lambda rel: tight(load('rpg/Audio/' + rel))
KI = lambda rel: tight(load('impact/Audio/' + rel))


def swings():
    out = {}
    # kılıç: hızlı swish + ince çelik çınlaması
    for i, (k, f) in enumerate(((3, 1.0), (5, 1.08), (8, 1.04), (11, 1.12))):
        out['savur_kilic_%d' % (i + 1)] = build([(trim(pitch(SW[k](), f), 0, 0.32), 0.0, 0.9), (ring((2600, 4100), 0.2, 0.05), 0.04, 1.0)])
    # katana (yıldırım): kından çekiş + çok hızlı swish
    for i, (u, k) in enumerate(((2, 6), (4, 9))):
        out['savur_katana_%d' % (i + 1)] = build([(trim(RP('battle/sword-unsheathe%d.wav' % u), 0, 0.3), 0.0, 0.55), (trim(pitch(SW[k](), 1.25), 0, 0.22), 0.05, 0.9)])
    # dev kılıç / tırpan: kalın, uzun hava + alt bas
    wh = load('whoosh2_0.wav')
    for i, (k, f) in enumerate(((1, 0.62), (7, 0.68))):
        out['savur_dev_%d' % (i + 1)] = build([(trim(pitch(SW[k](), f), 0, 0.55), 0.0, 0.9), (trim(pitch(wh[int(0.9 * SR):int(1.7 * SR)], 0.7), 0, 0.5), 0.0, 0.35), (sub(55, 0.45, 9, 0.5), 0.05, 1.0)])
    # çekiç / gürz: ağır hava + kumaş + bas
    for i, (k, f) in enumerate(((2, 0.72), (10, 0.78))):
        out['savur_cekic_%d' % (i + 1)] = build([(trim(pitch(wh[int(1.0 * SR):int(1.8 * SR)], 0.75), 0, 0.5), 0.0, 0.45), (trim(pitch(SW[k](), f), 0, 0.45), 0.02, 0.8),
                                                 (trim(RP('inventory/cloth-heavy.wav'), 0, 0.25), 0.0, 0.3), (sub(48, 0.5, 8, 0.45), 0.08, 1.0)])
    # balta / teber: kalın swing + swish
    for i, (s, k) in enumerate(((2, 4), (3, 12))):
        out['savur_balta_%d' % (i + 1)] = build([(pitch(RP('battle/swing%d.wav' % s), 0.85), 0.0, 0.8), (trim(pitch(SW[k](), 0.92), 0, 0.35), 0.02, 0.7)])
    # sırık / saplama: çok hızlı ince swish
    for i, (k, f) in enumerate(((6, 1.35), (13, 1.3))):
        out['savur_sirik_%d' % (i + 1)] = build([(trim(pitch(SW[k](), f), 0, 0.2), 0.0, 0.9), (trim(pitch(RP('battle/swing3.wav'), 1.15), 0, 0.15), 0.0, 0.4)])
    # bıçak / pençe: kısa, tiz
    for i, (k, f) in enumerate(((9, 1.5), (3, 1.42), (12, 1.55))):
        out['savur_bicak_%d' % (i + 1)] = build([(trim(pitch(SW[k](), f), 0, 0.18), 0.0, 0.9), (trim(KR('drawKnife3.ogg'), 0.05, 0.15), 0.0, 0.35)])
    # kırbaç: swish + şaklama
    for i, (k, p) in enumerate(((5, 'impactPlate_light_000.ogg'), (8, 'impactPlate_light_002.ogg'))):
        out['savur_kirbac_%d' % (i + 1)] = build([(trim(pitch(SW[k](), 1.2), 0, 0.3), 0.0, 0.8), (trim(pitch(KI(p), 1.7), 0, 0.12), 0.13, 0.7)])
    # ruh kılıcı: swish + ışıltı
    for i, k in enumerate((4, 11)):
        out['savur_ruh_%d' % (i + 1)] = build([(trim(pitch(SW[k](), 1.0), 0, 0.3), 0.0, 0.8), (shimmer(0.4, 0.14), 0.03, 1.0)])
    # eski genel adlar (geri uyumluluk)
    out['savur_hafif_1'] = out['savur_kilic_1']; out['savur_hafif_2'] = out['savur_kilic_2']; out['savur_hafif_3'] = out['savur_kilic_3']
    out['savur_agir_1'] = out['savur_cekic_1']; out['savur_agir_2'] = out['savur_dev_1']
    out['savur_dev'] = out['savur_dev_2']
    out['sapla'] = out['savur_sirik_1']
    return out


def hits():
    out = {}
    wet = lambda i: SY.hit_flesh(i) * 0.45
    # kesik (kılıç): bıçak dilimi + yumuşak darbe + ıslak
    for i, (ks, f, sm) in enumerate((('knifeSlice.ogg', 1.0, 'impactSoft_medium_000.ogg'), ('knifeSlice2.ogg', 1.08, 'impactSoft_medium_002.ogg'), ('knifeSlice.ogg', 1.15, 'impactSoft_medium_003.ogg'))):
        out['darbe_kesik_%d' % (i + 1)] = build([(trim(pitch(KR(ks), f), 0, 0.3), 0.0, 0.8), (trim(KI(sm), 0, 0.25), 0.0, 0.8), (wet(i), 0.0, 1.0)])
    # ağır kesik (dev kılıç): kalın dilim + ağır yumuşak + bas
    for i, (f, sh) in enumerate(((0.8, 'impactSoft_heavy_000.ogg'), (0.74, 'impactSoft_heavy_003.ogg'))):
        out['darbe_kesik_agir_%d' % (i + 1)] = build([(trim(pitch(KR('knifeSlice.ogg'), f), 0, 0.4), 0.0, 0.8), (trim(KI(sh), 0, 0.35), 0.0, 0.9), (sub(60, 0.4, 9, 0.5), 0.0, 1.0)])
    # künt (gürz, çekiç normal vuruş)
    for i, (pn, sh) in enumerate((('impactPunch_heavy_000.ogg', 'impactSoft_heavy_001.ogg'), ('impactPunch_heavy_002.ogg', 'impactSoft_heavy_002.ogg'), ('impactPunch_heavy_004.ogg', 'impactSoft_heavy_004.ogg'))):
        out['darbe_kunt_%d' % (i + 1)] = build([(trim(KI(pn), 0, 0.3), 0.0, 0.9), (trim(pitch(KI(sh), 0.9), 0, 0.35), 0.0, 0.7), (sub(58, 0.35, 11, 0.5), 0.0, 1.0)])
    # çekiç ağır (yere çakma / şarjlı): plaka + yumruk + bas gümbürtü
    for i, (pl, pn) in enumerate((('impactPlate_heavy_000.ogg', 'impactPunch_heavy_001.ogg'), ('impactPlate_heavy_003.ogg', 'impactPunch_heavy_003.ogg'))):
        out['darbe_cekic_%d' % (i + 1)] = build([(trim(pitch(KI(pl), 0.65), 0, 0.5), 0.0, 0.55), (trim(KI(pn), 0, 0.3), 0.0, 0.9), (sub(45, 0.6, 6, 0.6), 0.0, 1.0),
                                                 (fft_filter(noise(0.5, seed=5), hi=250) * exp_env(0.5, 6), 0.0, 0.35)])
    # delme (kargı, saplama)
    for i, f in enumerate((1.25, 1.35)):
        out['darbe_delme_%d' % (i + 1)] = build([(trim(pitch(KR('knifeSlice2.ogg'), f), 0, 0.25), 0.0, 0.8), (trim(KI('impactSoft_medium_001.ogg'), 0, 0.2), 0.0, 0.5), (wet(1), 0.0, 0.6)])
    # balta / teber: kesme darbesi
    for i, sh in enumerate(('impactSoft_heavy_000.ogg', 'impactSoft_heavy_003.ogg')):
        out['darbe_balta_%d' % (i + 1)] = build([(trim(KR('chop.ogg'), 0, 0.25), 0.0, 0.9), (trim(KI(sh), 0, 0.3), 0.0, 0.7), (trim(KR('knifeSlice.ogg'), 0, 0.2), 0.0, 0.3)])
    # kırbaç
    out['darbe_kirbac_1'] = build([(trim(pitch(KI('impactPlate_light_001.ogg'), 1.7), 0, 0.15), 0.0, 0.8), (trim(pitch(KR('knifeSlice2.ogg'), 1.4), 0, 0.15), 0.0, 0.4), (wet(2), 0.0, 0.5)])
    # taş (balbal / kalkan)
    for i, (mn, pl) in enumerate((('impactMining_000.ogg', 'impactPlate_medium_000.ogg'), ('impactMining_003.ogg', 'impactPlate_medium_002.ogg'))):
        out['darbe_tas_%d' % (i + 1)] = build([(trim(KI(mn), 0, 0.35), 0.0, 0.9), (trim(KI(pl), 0, 0.3), 0.0, 0.5)])
    out['darbe_tas'] = out['darbe_tas_1']
    # metal (siper)
    for i, m in enumerate(('impactMetal_medium_000.ogg', 'impactMetal_heavy_002.ogg')):
        out['darbe_metal_%d' % (i + 1)] = build([(trim(KI(m), 0, 0.4), 0.0, 0.9)])
    # kritik: dilim + yumruk + çan + ışıltı
    out['darbe_kritik'] = build([(trim(KR('knifeSlice.ogg'), 0, 0.3), 0.0, 0.8), (trim(KI('impactPunch_heavy_000.ogg'), 0, 0.3), 0.0, 0.9),
                                 (trim(pitch(KI('impactBell_heavy_001.ogg'), 1.2), 0, 0.45), 0.02, 0.3), (shimmer(0.4, 0.12), 0.02, 1.0), (sub(55, 0.4, 9, 0.5), 0.0, 1.0)])
    out['darbe_agir'] = out['darbe_kunt_2']
    # genel et darbesi (mermi, diğer): yumuşak + orta yumruk
    for i, (sm, pm) in enumerate((('impactSoft_medium_000.ogg', 'impactPunch_medium_000.ogg'), ('impactSoft_medium_002.ogg', 'impactPunch_medium_002.ogg'), ('impactSoft_medium_004.ogg', 'impactPunch_medium_004.ogg'))):
        out['darbe_et_%d' % (i + 1)] = build([(trim(KI(sm), 0, 0.25), 0.0, 0.8), (trim(KI(pm), 0, 0.2), 0.0, 0.6)])
    out['darbe_kunt'] = out['darbe_kunt_1']
    out['ok_vurus'] = build([(trim(pitch(KR('knifeSlice2.ogg'), 1.4), 0, 0.15), 0.0, 0.6), (trim(KI('impactSoft_medium_001.ogg'), 0, 0.15), 0.0, 0.6)])
    return out


def creatures():
    out = {}
    for i, (m, f) in enumerate(((1, 1.15), (2, 1.2), (3, 1.1))):
        out['kurt_can_%d' % (i + 1)] = trim(pitch(RP('NPC/gutteral beast/mnstr%d.wav' % m), f), 0, 0.4)
    out['kurt_olum'] = build([(trim(pitch(RP('NPC/gutteral beast/mnstr14.wav'), 1.05), 0, 0.9), 0.0, 0.9), (trim(pitch(RP('NPC/gutteral beast/mnstr5.wav'), 1.3), 0, 0.5), 0.25, 0.4)])
    for i, (g, f) in enumerate(((3, 0.9), (4, 0.85))):
        out['agac_can_%d' % (i + 1)] = build([(trim(pitch(RP('NPC/giant/giant%d.wav' % g), f), 0, 0.6), 0.0, 0.9), (trim(KR('creak%d.ogg' % (i + 1)), 0, 0.4), 0.0, 0.4)])
    out['agac_olum'] = build([(trim(pitch(RP('NPC/giant/giant2.wav'), 0.85), 0, 0.9), 0.0, 0.9), (trim(KI('impactWood_heavy_000.ogg'), 0, 0.5), 0.35, 0.7), (sub(50, 0.8, 5, 0.4), 0.3, 1.0)])
    for i, b in enumerate(('bite-small.wav', 'bite-small2.wav')):
        out['cor_can_%d' % (i + 1)] = build([(trim(pitch(RP('NPC/beetle/' + b), 1.3), 0, 0.3), 0.0, 0.8), (SY.cor_hurt(i), 0.0, 0.4)])
    out['cor_olum'] = build([(trim(pitch(RP('NPC/beetle/bite-small3.wav'), 1.1), 0, 0.4), 0.0, 0.8), (SY.cor_die(), 0.0, 0.6)])
    out['dusman_hazirlik'] = build([(trim(pitch(RP('NPC/gutteral beast/mnstr7.wav'), 0.9), 0, 0.4), 0.0, 0.6)])
    out['bengu_can'] = build([(trim(pitch(RP('NPC/gutteral beast/mnstr15.wav'), 1.45), 0, 0.3), 0.0, 0.7), (trim(KI('impactPunch_medium_001.ogg'), 0, 0.2), 0.0, 0.7)])
    out['bengu_olum'] = build([(trim(pitch(RP('NPC/gutteral beast/mnstr11.wav'), 1.2), 0, 0.8), 0.0, 0.8), (SY.player_die(), 0.1, 0.5)])
    out['isirik_1'] = build([(trim(pitch(RP('NPC/gutteral beast/mnstr10.wav'), 1.1), 0, 0.35), 0.0, 0.7), (trim(KR('knifeSlice2.ogg'), 0, 0.2), 0.05, 0.5), (trim(KI('impactSoft_heavy_001.ogg'), 0, 0.3), 0.05, 0.7)])
    out['isirik_2'] = build([(trim(pitch(RP('NPC/gutteral beast/mnstr12.wav'), 1.0), 0, 0.35), 0.0, 0.7), (trim(KR('knifeSlice.ogg'), 0, 0.2), 0.05, 0.5), (trim(KI('impactSoft_heavy_003.ogg'), 0, 0.3), 0.05, 0.7)])
    return out


def movement_pickups():
    out = {}
    for name, pre in (('cim', 'footstep_grass'), ('kar', 'footstep_snow'), ('tas', 'footstep_concrete'), ('tahta', 'footstep_wood')):
        for i in range(5):
            out['adim_%s_%d' % (name, i + 1)] = trim(KI('%s_00%d.ogg' % (pre, i)), 0, 0.25) * 0.8
    out['adim_1'] = out['adim_cim_1']; out['adim_2'] = out['adim_cim_2']
    out['inis_1'] = build([(trim(KI('footstep_grass_002.ogg'), 0, 0.25), 0.0, 0.8), (trim(KI('impactSoft_medium_000.ogg'), 0, 0.2), 0.0, 0.5)])
    out['inis_2'] = build([(trim(KI('impactSoft_heavy_002.ogg'), 0, 0.3), 0.0, 0.9), (trim(KI('footstep_grass_004.ogg'), 0, 0.25), 0.0, 0.6), (sub(60, 0.3, 12, 0.4), 0.0, 1.0)])
    out['yuvarlan'] = build([(trim(RP('inventory/cloth-heavy.wav'), 0, 0.35), 0.0, 0.8), (trim(KR('cloth2.ogg'), 0, 0.3), 0.08, 0.5), (trim(pitch(SW[6](), 0.9), 0, 0.3), 0.0, 0.35)])
    out['zipla'] = build([(trim(KR('cloth1.ogg'), 0, 0.15), 0.0, 0.6), (SY.jump(), 0.0, 0.5)])
    for i in range(3):
        out['altin_%d' % (i + 1)] = trim(RP('inventory/coin%s.wav' % ('' if i == 0 else str(i + 1))), 0, 0.3)
    out['altin'] = out['altin_1']
    out['esya'] = build([(trim(RP('inventory/armor-light.wav'), 0, 0.4), 0.0, 0.7), (trim(RP('battle/sword-unsheathe3.wav'), 0, 0.35), 0.05, 0.4), (SY.pickup_item(), 0.0, 0.5)])
    out['sise'] = build([(trim(RP('inventory/bottle.wav'), 0, 0.4), 0.0, 0.7), (trim(RP('inventory/bubble2.wav'), 0, 0.3), 0.15, 0.5)])
    for i in range(3):
        out['ui_sec_%d' % (i + 1)] = trim(RP('interface/interface%d.wav' % (i + 1)), 0, 0.2) * 0.6
    out['ui_sec'] = out['ui_sec_1']
    out['ui_onay'] = trim(RP('interface/interface4.wav'), 0, 0.35) * 0.7
    out['yay_birak'] = build([(trim(pitch(RP('battle/swing3.wav'), 1.5), 0, 0.15), 0.0, 0.6), (SY.bow_release(), 0.0, 0.8)])
    out['yay_ger'] = build([(trim(KR('creak3.ogg'), 0, 0.4), 0.0, 0.5), (SY.bow_draw(), 0.0, 0.6)])
    out['buyu'] = build([(trim(RP('battle/magic1.wav'), 0, 0.7), 0.0, 0.7), (SY.magic_cast(), 0.0, 0.5)])
    out['npc_1'] = trim(RP('interface/interface5.wav'), 0, 0.15) * 0.5
    out['npc_2'] = trim(RP('interface/interface6.wav'), 0, 0.15) * 0.5
    out['ors'] = build([(trim(KI('impactMetal_heavy_000.ogg'), 0, 0.5), 0.0, 0.9), (trim(KI('impactBell_heavy_002.ogg'), 0, 0.6), 0.0, 0.25)])
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    allsfx = {}
    for fn in (swings, hits, creatures, movement_pickups):
        allsfx.update(fn())
    for name, x in allsfx.items():
        write_wav(os.path.join(OUT, name + '.wav'), x, SR, 0.88)
    print('katmanlı ses:', len(allsfx))
    # eski jenerik dosyalar kalsın; sfx.json'u güncelle
    import json
    meta_p = os.path.join(OUT, 'sfx.json')
    meta = json.load(open(meta_p, encoding='utf-8')) if os.path.exists(meta_p) else {}
    for name, x in allsfx.items():
        meta[name] = {'loop': False, 'len': round(len(x) / SR, 3), 'src': 'layer'}
    json.dump(meta, open(meta_p, 'w', encoding='utf-8'), indent=1)


if __name__ == '__main__':
    main()
