"""Tüm sesleri üretir: assets/audio/sfx/*.wav (44.1 kHz mono) ve assets/audio/music/*.wav (22.05 kHz mono).
Kullanım: python tools/audiogen/export_audio.py [--sfx] [--music] [ad ...]"""
import os
import sys
import json
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from synth import write_wav, SR
import sfx as S
import music as Mu

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'audio')
os.makedirs(os.path.join(A, 'sfx'), exist_ok=True)
os.makedirs(os.path.join(A, 'music'), exist_ok=True)
args = sys.argv[1:]
only = [a for a in args if not a.startswith('-')]
do_sfx = '--sfx' in args or not any(a.startswith('-') for a in args)
do_music = '--music' in args or not any(a.startswith('-') for a in args)

if do_sfx:
    meta = {}
    for name, fn in S.SFX.items():
        if only and name not in only:
            continue
        t0 = time.time()
        x = fn()
        peak = None if name.endswith('_dongu') else 0.85
        if peak is None:
            x = x / (np.max(np.abs(x)) + 1e-9) * 0.6
        write_wav(os.path.join(A, 'sfx', name + '.wav'), x, SR, peak)
        meta[name] = {'loop': name.endswith('_dongu'), 'len': round(len(x) / SR, 3)}
        print('sfx', name, round(len(x) / SR, 2), 's', round(time.time() - t0, 2))
    json.dump(meta, open(os.path.join(A, 'sfx', 'sfx.json'), 'w', encoding='utf-8'), indent=1)
if do_music:
    for biome in ['otuken', 'bozkir', 'sahmeran', 'kaf', 'tamu', 'yurt', 'baslik']:
        if only and biome not in only:
            continue
        t0 = time.time()
        x = Mu.track(biome)
        write_wav(os.path.join(A, 'music', biome + '.wav'), x, Mu.MSR, 0.8)
        print('music', biome, round(len(x) / Mu.MSR, 1), 's', round(time.time() - t0, 1))
