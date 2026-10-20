"""v36 ölüm patlaması sesi: kısa, ıslak, vurucu "dışşkk".
İstek: Dead Cells'teki gibi düşman ölünce "dışşkk" diye bir ölüm sesi (özgün: kaynak kopyalanmadı; sentez + yerel CC0
Kenney kayıtları). Üç bölüm: (1) "dı": sert geçiş (3 ms tık + Kenney impactPunch, perde düşük, doyurulmuş) ve kısa alt güm;
(2) "şş": ıslak sıçrantı (tanecikli bant gürültü) + tiz ıslak hışırtı kuyruğu, 0,25-0,35 sn söner; (3) "kk": kuyrukta
çok kısa sıkışık çıtırtı (zerreler yere / duvara çarpar).
  vahset_patla_1..4       sıradan öldürüş (~0,3 sn)
  vahset_patla_agir_1..3  kritik / bitiriş / seçkin / boss: daha dolgun alt, daha uzun hışırtı (~0,4 sn)
Ayrıca v35'in vahset_et_1..4 vuruş seslerini biraz daha çıtkı yapar (geçiş vurgusu, 0,22 sn).
v35'in vahset_olum / vahset_yirtil / vahset_dusme sesleri silinir (parçalanma yok).
Kullanım: python tools/audiogen/v36.py"""
import os
import sys
import json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, exp_env, noise, distort, hp, lp, bp, master, write_wav, place
from layer import KI, trim, build, pitch
from pro import click
from impact import cut, crunch
from v26 import asat, transient, ny_comp, body
import v35

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'audio', 'sfx')
TARGET = {'vahset_patla': -8.0, 'vahset_patla_agir': -7.0, 'vahset_et': -11.0}
OLD = ('vahset_olum', 'vahset_yirtil', 'vahset_dusme')


def _n(x):
    return x / (np.max(np.abs(x)) + 1e-9)


def hiss(dur, seed, lo=2500.0, k=None):
    """Islak hışırtı ("şşş"): tiz bant gürültü, hızlı tanecikli genlik, ~üstel sönüm."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    x = bp(noise(dur, seed=seed), lo, 11000.0)
    m = _n(np.abs(lp(rng.standard_normal(n), 220.0))) ** 1.2
    return x * (0.35 + m) * exp_env(dur, k or 4.2 / dur)


def dissk(i, heavy=False):
    punch = ('impactPunch_heavy_000.ogg', 'impactPunch_heavy_002.ogg', 'impactPunch_heavy_003.ogg', 'impactPunch_heavy_004.ogg')[i % 4]
    soft = ('impactSoft_heavy_001.ogg', 'impactSoft_heavy_003.ogg', 'impactSoft_heavy_004.ogg', 'impactSoft_heavy_000.ogg')[i % 4]
    dur = 0.42 if heavy else 0.32
    tail = 0.36 if heavy else 0.26
    s = 6100 + i * 7 + (50 if heavy else 0)
    kk = 0.17 + 0.02 * i + (0.04 if heavy else 0.0)
    x = build([
        (click(0.003, 1800, 16000, s), 0.0, 1.0),
        (asat(trim(pitch(KI(punch), 0.78 + 0.05 * i - (0.1 if heavy else 0.0)), 0, 0.12, 0.04), 3.0, 0.2), 0.0, 0.85),
        (trim(pitch(KI(soft), 0.7), 0, 0.14, 0.05), 0.003, 0.5),
        (body(130.0 - 10 * i - (25 if heavy else 0), 48.0, 0.12 if not heavy else 0.2, 20.0 if not heavy else 12.0, 5.0), 0.0, 0.55 if not heavy else 0.85),
        (v35.wet(0.16, s + 1, 300.0, 3800.0, 220.0, 14.0), 0.004, 0.9),              # ıslak şapırtı
        (hiss(tail, s + 2), 0.012, 0.75 if not heavy else 0.85),                      # "şşş"
        (v35.snaps(0.05, 9 + 3 * i, s + 3, 1800.0, 8000.0, 0.7), kk, 0.55),           # "kk": zerreler çarpar
        (crunch(0.04, s + 4, 900, 5000, 4.0, 160.0), kk + 0.006, 0.35),
    ])
    x = transient(_n(x), attack=1.8, sustain=-0.15)
    x = ny_comp(_n(x), ratio=3.5, th_db=-20.0, mix=0.45)
    x = distort(_n(x), 1.25)
    return cut(x, dur, 0.06)


def flesh_snappy(i):
    x = v35.flesh_hit(i)
    x = transient(_n(x), attack=1.7, sustain=-0.35)
    return cut(x, 0.22, 0.05)


def target_for(name):
    pre = name.rstrip('0123456789').rstrip('_')
    return TARGET.get(pre, -12.0)


def main():
    out = {}
    for i in range(4):
        out['vahset_patla_%d' % (i + 1)] = dissk(i)
        out['vahset_et_%d' % (i + 1)] = flesh_snappy(i)
    for i in range(3):
        out['vahset_patla_agir_%d' % (i + 1)] = dissk(i, True)
    mp = os.path.join(A, 'sfx.json')
    meta = json.load(open(mp, encoding='utf-8'))
    for name, x in sorted(out.items()):
        y = master(x, target_for(name))
        write_wav(os.path.join(A, name + '.wav'), y, SR, None)
        meta[name] = {'loop': False, 'len': round(len(y) / SR, 3), 'hedef_db': target_for(name)}
    for k in list(meta.keys()):
        if k.rstrip('0123456789').rstrip('_') in OLD:
            meta.pop(k)
    for f in os.listdir(A):
        if f.split('.')[0].rstrip('0123456789').rstrip('_') in OLD:
            os.remove(os.path.join(A, f))
    json.dump(meta, open(mp, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('yazıldı:', len(out))


if __name__ == '__main__':
    main()
