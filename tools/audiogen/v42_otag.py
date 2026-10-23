"""v42 sınav ve otağ sesleri (mühür / mürekkep / keçe dili; v40 arayüz sesleriyle aynı aile):
  otag_damga   sınav kazanıldı: ıslak mühür basışı (tok şaplak + mürekkep "şlap") + kopuz üçlüsü (A4 / C#5 / E5) + ince çan
  otag_catlak  sınav kaybedildi: kuru mum mührün çatlaması (kısa çıtırtı + taş tıkırtısı) + alçalan, kısık kopuz ikilisi
  otag_ac      otağa girme: keçe kapının kalkışı (yumuşak hışırtı + kumaş süpürmesi) + uzak çan ve sıcak kopuz akoru
  otag_odul    otağ sandığı: tahta kapak + altın şıngırtısı + yükselen kopuz dörtlüsü
Hedef yükseklik TARGET (dB). Yeniden üretim: python tools/audiogen/v42_otag.py [ad...]"""
import os
import sys
import json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, exp_env, env, noise, fade, lp, bp, write_wav, master
from pro import click, thump, room, note, kopuz, crackle, bell
from impact import crunch
from v25 import steel
from v40_ui import _mix, brush_sweep, paper_rustle

TARGET = {"otag_damga": -17.0, "otag_catlak": -20.0, "otag_ac": -18.0, "otag_odul": -16.0}


def damga():
    dur = 1.1
    slap = lp(noise(0.08, seed=4201), 1400) * exp_env(0.08, 34.0)
    body = thump(170, 62, 0.16, 15, 1.3)
    wet = bp(noise(0.06, seed=4202), 450, 2600) * exp_env(0.06, 50.0)
    parts = [(slap, 0.0, 0.9), (body, 0.0, 0.8), (wet, 0.005, 0.5), (click(0.005, 1500, 7000, 4203), 0.0, 0.25),
             (kopuz(note('A4'), 0.6, 0.55, seed=4204), 0.05, 0.28), (kopuz(note('C#5'), 0.55, 0.55, seed=4205), 0.11, 0.24),
             (kopuz(note('E5'), 0.6, 0.6, seed=4206), 0.17, 0.24), (bell(note('E6'), 0.8, 5.0, 0.12), 0.17, 1.0)]
    return room(_mix(parts, dur), 0.4, 0.14)


def catlak():
    dur = 0.75
    cr = crackle(0.22, n=18, seed=4211, lo=1800, hi=8000)
    snap = crunch(0.05, 4212, 900, 6000, 3.0, 260.0)
    tick = click(0.004, 2000, 9000, 4213)
    parts = [(snap, 0.0, 0.8), (cr, 0.01, 0.5), (tick, 0.09, 0.3), (tick, 0.15, 0.2),
             (kopuz(note('E4'), 0.35, 0.3, seed=4214), 0.05, 0.16), (kopuz(note('C4'), 0.4, 0.3, seed=4215), 0.13, 0.16)]
    return room(_mix(parts, dur), 0.3, 0.1)


def ac():
    dur = 1.2
    parts = [(paper_rustle(0.42, 4221, 10, 0.15), 0.0, 0.5), (brush_sweep(0.5, 4222), 0.0, 0.55),
             (lp(noise(0.5, seed=4223), 600) * env(0.5, a=0.08, d=0.2, s=0.3, r=0.2), 0.0, 0.5),
             (bell(note('A5'), 1.0, 3.5, 0.1), 0.18, 1.0), (kopuz(note('A3'), 0.8, 0.45, seed=4224), 0.2, 0.3),
             (kopuz(note('E4'), 0.7, 0.45, seed=4225), 0.24, 0.24), (kopuz(note('A4'), 0.7, 0.5, seed=4226), 0.28, 0.2)]
    return room(_mix(parts, dur), 0.5, 0.18)


def odul():
    dur = 1.3
    lid = thump(130, 55, 0.12, 20, 1.1)
    parts = [(lid, 0.0, 0.7), (click(0.008, 900, 5000, 4231), 0.0, 0.4)]
    for i in range(7):
        parts.append((steel(5200.0 + 700 * (i % 3), 0.12, 40.0, seed=4232 + i), 0.08 + i * 0.045, 0.14))
    for i, n in enumerate(('A4', 'C#5', 'E5', 'A5')):
        parts.append((kopuz(note(n), 0.6, 0.6, seed=4240 + i), 0.12 + i * 0.07, 0.24))
    parts.append((bell(note('A6'), 0.7, 5.0, 0.1), 0.35, 1.0))
    return room(_mix(parts, dur), 0.4, 0.14)


def build_all():
    return {'otag_damga': damga(), 'otag_catlak': catlak(), 'otag_ac': ac(), 'otag_odul': odul()}


if __name__ == '__main__':
    A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'audio', 'sfx')
    meta_p = os.path.join(A, 'sfx.json')
    meta = json.load(open(meta_p, encoding='utf-8')) if os.path.exists(meta_p) else {}
    only = set(sys.argv[1:])
    for k, v in build_all().items():
        if only and k not in only:
            continue
        y = master(fade(v, 0.0005, 0.05), TARGET.get(k, -17.0))
        write_wav(os.path.join(A, k + '.wav'), y, SR, None)
        meta[k] = {'loop': False, 'len': round(len(y) / SR, 3), 'hedef_db': TARGET.get(k, -17.0)}
        print(k, round(len(y) / SR, 3))
    json.dump(meta, open(meta_p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
