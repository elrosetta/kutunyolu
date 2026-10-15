"""v12 mekanik sesleri: Usul Vuruşu, Üç Âlem (kam transı), Don Değiştirme, Ad Koyma Töreni.
Hepsi yumuşak, müzikal (müzikle aynı çalgı ailesi: bendir, zil, bağlama, ney)."""
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, t_axis, exp_env, noise, fft_filter, sine, sweep, mix, place, reverb
import turku as T


def _bendir(f0=105, f1=58, d=0.45, g=1.0, seed=1):
    x = sweep(f0, f1, d, sr=SR, curve=0.5) * exp_env(d, 9, SR)
    skin = fft_filter(noise(d, SR, seed), hi=600, sr=SR, slope=1.2) * exp_env(d, 24, SR) * 0.35
    return mix(x, skin) * g


def _zil(f=3400, d=0.5, g=0.3, seed=2):
    x = sum(sine(ff, d, SR) * exp_env(d, 7 + i * 3, SR) * (0.6 ** i) for i, ff in enumerate((f, f * 1.51, f * 2.07)))
    return mix(x * 0.25, T.bp(noise(d, SR, seed), 5000, 9000, SR) * exp_env(d, 30, SR) * 0.15) * g


def _pad(x, d):
    out = np.zeros(int(d * SR))
    out[:min(len(x), len(out))] = x[:len(out)]
    return out


def _chord(notes, d, g=0.5, bright=0.5, seed=0, strum=0.03):
    out = np.zeros(int((d + 0.5) * SR))
    for i, m in enumerate(notes):
        place(out, T.saz(T.midi(m), d, SR, bright, seed + i * 3, g), i * strum, 1.0, SR)
    return out


def build():
    out = {}
    # ---- Usul: vuruş tam usulün üstüne denk gelince (yumuşak bendir + ince zil; düm daha tok)
    out['usul_vurus'] = mix(_bendir(140, 90, 0.25, 0.5, 11), _zil(3600, 0.35, 0.45, 12))
    out['usul_dum'] = mix(_bendir(110, 55, 0.45, 1.0, 13), _zil(2900, 0.6, 0.5, 14), T.saz(T.midi(62), 0.6, SR, 0.5, 15, 0.35))
    out['usul_seri'] = mix(_chord([62, 66, 69, 74], 0.9, 0.35, 0.55, 16, 0.04), _zil(4200, 0.8, 0.35, 17))
    # ---- Üç Âlem: göğe yükseliş (parlak, yükselen ney + zil), yeraltına iniş (derin, alçalan), dönüş
    d = 1.4
    rise = T.ney(T.midi(74), d, SR, 21, 0.4) * np.linspace(0.3, 1.0, int(d * SR))[:int(max(0.1, d) * SR)]
    gl = sweep(400, 1600, d, sr=SR, curve=1.4) * exp_env(d, 2.5, SR) * 0.12
    out['alem_gok'] = reverb(mix(_pad(rise, d), gl, _zil(5200, 1.2, 0.5, 22), _chord([74, 78, 81], 1.2, 0.25, 0.6, 23, 0.08)), 2.2, 0.45, SR)
    boom = sweep(90, 32, 1.4, sr=SR, curve=0.6) * exp_env(1.4, 2.8, SR)
    whisper = T.bp(noise(1.4, SR, 24), 500, 2500, SR) * np.exp(-((t_axis(1.4, SR) - 0.6) / 0.4) ** 2) * 0.25
    out['alem_yer'] = reverb(mix(boom * 0.9, whisper, _bendir(80, 40, 0.8, 0.8, 25), T.mey(T.midi(38), 1.2, SR, 26, 0.35)), 2.6, 0.5, SR)
    back = sweep(1800, 300, 0.5, sr=SR, curve=0.6) * np.linspace(0, 1, int(0.5 * SR)) ** 2 * 0.25
    out['alem_cikis'] = reverb(mix(back, T.bp(noise(0.5, SR, 27), 800, 5000, SR) * np.linspace(0, 1, int(0.5 * SR)) ** 3 * 0.4, _pad(_zil(3000, 0.4, 0.3, 28), 0.9)), 1.4, 0.35, SR)
    out['ruh_kusu'] = mix(_zil(4800, 0.5, 0.5, 29), T.ney(T.midi(86), 0.25, SR, 30, 0.25))
    out['ruh_tasi'] = reverb(mix(_bendir(70, 35, 0.6, 0.9, 31), T.bp(noise(0.6, SR, 32), 300, 2000, SR) * exp_env(0.6, 6, SR) * 0.4), 1.8, 0.4, SR)
    # ---- Don: ruhu emme (içe çekilen hışırtı + alçalan ses), dönüşüm (patlayan bendir + nefes)
    suck = T.bp(noise(0.7, SR, 41), 600, 6000, SR) * np.linspace(0, 1, int(0.7 * SR)) ** 2 * 0.5
    out['don_al'] = reverb(mix(suck, sweep(1400, 300, 0.7, sr=SR, curve=0.7) * np.linspace(0, 1, int(0.7 * SR)) * 0.15, _pad(_zil(2500, 0.5, 0.35, 42), 1.0)), 1.5, 0.35, SR)
    out['don_donus'] = reverb(mix(_bendir(130, 45, 0.7, 1.0, 43), T.bp(noise(0.6, SR, 44), 300, 3000, SR) * exp_env(0.6, 5, SR) * 0.5, T.mey(T.midi(45), 0.7, SR, 45, 0.4)), 1.8, 0.35, SR)
    out['don_bitis'] = mix(T.bp(noise(0.4, SR, 46), 1000, 6000, SR) * exp_env(0.4, 7, SR) * 0.4, _zil(3800, 0.4, 0.3, 47))
    # ---- Ad Koyma: destan anı (kısa bağlama çarpması), tören (ozan kopuzu: yükselen dizi + karar)
    out['destan'] = mix(_chord([62, 69, 74], 0.8, 0.45, 0.6, 51, 0.05), _zil(3400, 0.7, 0.35, 52), _bendir(100, 55, 0.4, 0.6, 53))
    seq = [62, 63, 66, 67, 69, 70, 74]
    tor = np.zeros(int(3.2 * SR))
    for i, m in enumerate(seq):
        place(tor, T.saz(T.midi(m), 0.45, SR, 0.55, 60 + i, 0.5), i * 0.13, 1.0, SR)
    place(tor, _chord([62, 69, 74, 78], 1.8, 0.45, 0.5, 70, 0.05), 7 * 0.13 + 0.05, 1.0, SR)
    place(tor, _bendir(100, 50, 0.6, 0.9, 71), 7 * 0.13 + 0.05, 1.0, SR)
    out['ad_toren'] = reverb(tor, 2.0, 0.3, SR)
    return out


if __name__ == '__main__':
    print(sorted(build().keys()))
