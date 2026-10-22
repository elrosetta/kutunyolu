"""v40 arayüz sesleri (mürekkep / fırça / kâğıt / mühür dili; Main'deki çağrı adları aynı kalır, dosyalar üstüne yazılır):
  ui_gez_1..3  gezinme: kuru fırçanın kâğıda kısa dokunuşu (tiz bant gürültüsü, 40 ms) + çok kısık kopuz teli
  ui_sec_1..3  seçim: aynı dokunuş, bir tık daha dolu (ui_sec = ui_sec_1)
  ui_onay      onay: mühür basışı — kâğıda tok şaplak + ıslak mürekkep "şlap" + kısa çelik kenar + kopuz çift notası (E5 / A5)
  ui_iptal     vazgeç: kâğıt hışırtısı (geri çekilen yaprak) + kopuz alçalan ikili (A4 / E4)
  ui_ac        açılış: parşömenin açılışı — uzun kâğıt hışırtısı + fırça süpürmesi (hava) + yükselen kopuz üçlüsü
  ui_kapa      kapanış: kısa kâğıt sarılışı + alçalan kopuz ikilisi
Hedef yükseklik export_audio.TARGETS'tan (ui_gez / ui_sec -21, ui_ -17 dB).
Yeniden üretim: python tools/audiogen/v40_ui.py [ad...]"""
import os
import sys
import json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, t_axis, exp_env, env, noise, sine, fade, hp, lp, bp, write_wav, master
from pro import click, thump, room, note, kopuz, crackle
from impact import crunch
from v25 import steel

TARGET = {"ui_gez_1": -21.0, "ui_gez_2": -21.0, "ui_gez_3": -21.0, "ui_sec_1": -21.0, "ui_sec_2": -21.0, "ui_sec_3": -21.0,
          "ui_sec": -21.0, "ui_onay": -17.0, "ui_iptal": -17.0, "ui_ac": -17.0, "ui_kapa": -17.0}


def _mix(parts, dur):
    out = np.zeros(int(dur * SR))
    for x, at, g in parts:
        s = int(at * SR)
        n = min(len(x), len(out) - s)
        if n > 0:
            out[s:s + n] += x[:n] * g
    return out


def brush_touch(dur=0.05, seed=0, lo=2200, hi=9000, k=60.0):
    """Kuru fırça dokunuşu: tiz bant gürültüsü, çok hızlı sönen; kıl titreşimi için 110 Hz'lik hafif dalgalanma"""
    t = t_axis(dur)
    x = bp(noise(dur, seed=seed), lo, hi) * exp_env(dur, k) * (0.75 + 0.25 * np.sin(2 * np.pi * 110.0 * t))
    return x


def brush_sweep(dur=0.32, seed=0):
    """Fırça süpürmesi: hava bandı önce yükselip sonra inen süzgeç merkezi, yumuşak zarf"""
    n = int(dur * SR)
    x = noise(dur, seed=seed)
    # iki bant: alçak gövde (fırça teni) ve tiz kıl ıslığı; zarf: hızlı giriş, uzun çıkış
    e = env(dur, a=0.04, d=dur * 0.5, s=0.25, r=dur * 0.4)
    body = bp(x, 500, 2600) * e
    hair = bp(noise(dur, seed=seed + 1), 3500, 10000) * env(dur, a=0.02, d=dur * 0.35, s=0.15, r=dur * 0.5) * 0.6
    return (body + hair)[:n]


def paper_rustle(dur=0.28, seed=0, n_cr=26, g_cr=0.35):
    """Kâğıt hışırtısı: orta-tiz gürültü yumağı + çıtırtı taneleri"""
    x = bp(noise(dur, seed=seed), 900, 6500) * env(dur, a=0.01, d=dur * 0.6, s=0.2, r=dur * 0.3)
    cr = crackle(dur, n=n_cr, seed=seed + 7, lo=1500, hi=7500) * g_cr
    return x + cr


def gez(i):
    dur = 0.16
    parts = [(brush_touch(0.045, 500 + i, 2600 + 300 * i, 9000, 70.0), 0.0, 0.9),
             (kopuz(note('A5') * (1 + 0.004 * i), 0.12, 0.35, seed=510 + i), 0.0, 0.08)]
    return fade(_mix(parts, dur), 0.0005, 0.03)


def sec(i):
    dur = 0.2
    parts = [(brush_touch(0.06, 520 + i, 1800 + 250 * i, 8000, 50.0), 0.0, 1.0),
             (click(0.004, 2500, 9000, 530 + i), 0.0, 0.25),
             (kopuz(note('A5') * (1 + 0.004 * i), 0.16, 0.4, seed=540 + i), 0.0, 0.14)]
    return fade(_mix(parts, dur), 0.0005, 0.03)


def onay():
    dur = 0.6
    slap = lp(noise(0.07, seed=550), 1500) * exp_env(0.07, 38.0)
    body = thump(180, 70, 0.14, 16, 1.2)
    wet = bp(noise(0.05, seed=551), 500, 2800) * exp_env(0.05, 55.0)
    edge = crunch(0.04, 552, 1200, 7000, 3.0, 300.0)
    tink = steel(6200.0, 0.05, 90.0, seed=553)
    parts = [(click(0.004, 1500, 9000, 554), 0.0, 0.5), (slap, 0.0, 1.0), (body, 0.0, 0.75), (wet, 0.004, 0.7), (edge, 0.0, 0.3),
             (tink, 0.012, 0.18), (kopuz(note('E5'), 0.4, 0.6, seed=555), 0.02, 0.45), (kopuz(note('A5'), 0.45, 0.6, seed=556), 0.08, 0.5)]
    return room(_mix(parts, dur), 0.3, 0.12)


def iptal():
    dur = 0.45
    parts = [(paper_rustle(0.22, 560, 18, 0.3), 0.0, 0.8), (brush_touch(0.05, 561, 1500, 6000, 45.0), 0.0, 0.35),
             (kopuz(note('A4'), 0.3, 0.45, seed=562), 0.0, 0.4), (kopuz(note('E4'), 0.35, 0.4, seed=563), 0.08, 0.4)]
    return fade(_mix(parts, dur), 0.001, 0.04)


def ac():
    dur = 0.8
    parts = [(paper_rustle(0.42, 570, 34, 0.4), 0.0, 0.85), (brush_sweep(0.34, 572), 0.02, 0.55),
             (click(0.006, 1200, 6000, 574), 0.0, 0.3),
             (kopuz(note('A3'), 0.5, 0.5, seed=575), 0.04, 0.4), (kopuz(note('E4'), 0.45, 0.5, seed=576), 0.08, 0.32),
             (kopuz(note('A4'), 0.4, 0.5, seed=577), 0.12, 0.28)]
    return room(_mix(parts, dur), 0.35, 0.12)


def kapa():
    dur = 0.55
    parts = [(paper_rustle(0.26, 580, 22, 0.35), 0.0, 0.8), (brush_sweep(0.2, 582)[::-1], 0.0, 0.3),
             (thump(150, 60, 0.1, 22, 1.0), 0.1, 0.35),
             (kopuz(note('E4'), 0.3, 0.35, seed=583), 0.0, 0.32), (kopuz(note('A3'), 0.35, 0.35, seed=584), 0.06, 0.36)]
    return room(_mix(parts, dur), 0.3, 0.1)


def build_all():
    out = {}
    for i in range(3):
        out['ui_gez_%d' % (i + 1)] = gez(i)
        out['ui_sec_%d' % (i + 1)] = sec(i)
    out['ui_sec'] = out['ui_sec_1']
    out['ui_onay'] = onay()
    out['ui_iptal'] = iptal()
    out['ui_ac'] = ac()
    out['ui_kapa'] = kapa()
    return out


if __name__ == '__main__':
    A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'audio', 'sfx')
    meta_p = os.path.join(A, 'sfx.json')
    meta = json.load(open(meta_p, encoding='utf-8')) if os.path.exists(meta_p) else {}
    only = set(sys.argv[1:])
    for k, v in build_all().items():
        if only and k not in only:
            continue
        y = master(v, TARGET.get(k, -17.0))
        write_wav(os.path.join(A, k + '.wav'), y, SR, None)
        meta[k] = {'loop': False, 'len': round(len(y) / SR, 3), 'hedef_db': TARGET.get(k, -17.0)}
        print(k, round(len(y) / SR, 3))
    json.dump(meta, open(meta_p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
