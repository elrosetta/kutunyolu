"""v10 yay ve ok sesleri (pro.py'nin yay seslerinin üstüne yazar): Türk bileşik yayı karakteri.
  germe   : deri kabza sıkışı + boynuz/sinir gıcırtısı + perdesi yükselen kiriş gerginliği (kısa, gergin)
  dolu    : tam gerilince tok "tık" + ince çınlama (bırakma zamanı geldi)
  bırakma : kirişin tok "tvumm"u (perdesi düşen kalın tel) + sert çıtırtı + "fıvt" hava + kol titreşimi (brrr)
  uçuş    : ince ıslık (Doppler'le alçalan) + yelek hışırtısı
  vuruş   : ete "tok" (ıslak gövde), tahtaya saplanma + şaft titreşimi ("boyng"), taşa sekme ("çıng" + çakıl)
Kaynaklar: Kenney RPG Audio / Impact Sounds, OGA Swishes + RPG Sound Pack (CC0)."""
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, t_axis, env, exp_env, noise, fft_filter, sine, sweep, pluck, mix, place, fade, curve, hp, lp, bp
from layer import pitch, trim, build, SW, RP, KR, KI
from pro import click, thump, whoosh, debris


def _string(f0, dur, drop=0.82, bright=0.85, seed=0):
    """Kalın kiriş: iki telli (hafif akortsuz) Karplus + perdesi düşen alt ton."""
    a = pluck(f0, dur, bright=bright, decay=0.990, seed=seed)
    b = pluck(f0 * 1.006, dur, bright=bright * 0.8, decay=0.989, seed=seed + 1)
    bend = sweep(f0 * 1.35, f0 * drop, dur * 0.6, curve=0.35) * exp_env(dur * 0.6, 12) * 0.6
    return mix(a * 0.6, b * 0.5, bend)


def _limb_buzz(dur=0.18, f=52, seed=0):
    t = t_axis(dur)
    x = np.sin(2 * np.pi * f * t) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 31 * t)))
    return lp(x, 900) * exp_env(dur, 16) * 0.7


def build_bow():
    out = {}
    # germe: kısa ve gergin
    for i in range(3):
        d = 0.38
        fr = curve([(0, 110 + 8 * i), (d, 210 + 12 * i)], d)
        ph = 2 * np.pi * np.cumsum(fr) / SR
        ten = (np.sin(ph) * 0.5 + np.sin(2 * ph) * 0.2) * env(d, a=0.12, d=0.2, s=0.3, r=0.06, curve=1.5)
        ten = bp(ten, 150, 2200)
        out['yay_ger_%d' % (i + 1)] = build([
            (trim(KR(['beltHandle1.ogg', 'beltHandle2.ogg', 'dropLeather.ogg'][i]), 0, 0.2), 0.0, 0.6),
            (trim(pitch(KR('creak%d.ogg' % (1 + i)), 1.25), 0, 0.35), 0.03, 0.6),
            (ten, 0.0, 0.3),
            (trim(RP('inventory/cloth.wav'), 0, 0.2), 0.05, 0.25)])
    out['yay_ger'] = out['yay_ger_1']
    # tam gerildi
    out['yay_dolu'] = build([(click(0.008, 1500, 7000, 401), 0.0, 0.8), (trim(pitch(KI('impactPlate_light_003.ogg'), 1.8), 0, 0.12), 0.0, 0.35),
                             (sine(1760, 0.25) * exp_env(0.25, 14) * 0.12, 0.0, 1.0)])
    # bırakma
    for i in range(3):
        f0 = 72 * (1 + 0.06 * i)
        out['yay_birak_%d' % (i + 1)] = build([
            (click(0.004, 3000, 12000, 410 + i), 0.0, 0.9),
            (trim(pitch(KI('impactPlate_light_00%d.ogg' % i), 2.1), 0, 0.06), 0.0, 0.5),
            (_string(f0, 0.5, seed=415 + i), 0.0, 0.85),
            (thump(150, 60, 0.14, 24), 0.0, 0.6),
            (_limb_buzz(0.18, 48 + 4 * i, i), 0.01, 0.5),
            (trim(pitch(SW[[6, 9, 13][i]](), 1.75), 0, 0.16), 0.0, 0.7),
            (whoosh(0.22, 2500, 10000, 0.2, seed=420 + i, q=0.7), 0.02, 0.5)])
    out['yay_birak'] = out['yay_birak_1']
    out['yay_birak_tam'] = build([(out['yay_birak_2'], 0.0, 1.0), (thump(110, 40, 0.25, 12), 0.0, 0.6),
                                  (sweep(2600, 1500, 0.35) * exp_env(0.35, 8) * 0.15, 0.04, 1.0)])
    # uçuş ıslığı
    for i in range(3):
        d = 0.36
        tone = sweep(2500 + 150 * i, 1700, d, curve=1.2) * env(d, a=0.06, d=0.24, r=0.06, curve=2.0) * 0.18
        air = bp(noise(d, seed=430 + i), 2500, 7000) * env(d, a=0.05, d=0.25, r=0.06, curve=2.0) * 0.5
        out['ok_ucus_%d' % (i + 1)] = mix(tone, air)
    # ete saplanma
    for i in range(3):
        out['ok_vurus_%d' % (i + 1)] = build([
            (click(0.004, 2000, 9000, 440 + i), 0.0, 0.8),
            (trim(KI('impactSoft_heavy_00%d.ogg' % i), 0, 0.2), 0.0, 0.9),
            (trim(pitch(KI('impactWood_light_00%d.ogg' % (i % 3)), 1.35), 0, 0.12), 0.0, 0.45),
            (trim(pitch(KR('knifeSlice2.ogg'), 1.6), 0, 0.1), 0.0, 0.35),
            (thump(170, 60, 0.12, 26), 0.0, 0.5)])
    out['ok_vurus'] = out['ok_vurus_1']
    # tahtaya saplanma: tok + şaft titreşimi
    for i in range(2):
        d = 0.55
        f = 165 + 20 * i
        t = t_axis(d)
        boing = np.sin(2 * np.pi * f * t + 0.6 * np.sin(2 * np.pi * 26 * t)) * (0.6 + 0.4 * np.sin(2 * np.pi * 24 * t)) * exp_env(d, 6) * 0.45
        out['ok_vurus_tahta_%d' % (i + 1)] = build([(click(0.004, 2000, 8000, 450 + i), 0.0, 0.7), (trim(KI('impactWood_medium_00%d.ogg' % (i * 2)), 0, 0.25), 0.0, 1.0),
                                                    (boing, 0.01, 0.6)])
    # taşa sekme
    for i in range(2):
        out['ok_vurus_tas_%d' % (i + 1)] = build([(click(0.006, 3000, 12000, 460 + i), 0.0, 0.9), (trim(pitch(KI('impactMetal_light_00%d.ogg' % (i + 1)), 1.7), 0, 0.2), 0.0, 0.6),
                                                  (sine(3100 + 300 * i, 0.3) * exp_env(0.3, 16) * 0.15, 0.0, 1.0), (debris(0.3, 7, 465 + i, 2500, 9000), 0.02, 0.6)])
    return out


if __name__ == '__main__':
    print(sorted(build_bow().keys()))
