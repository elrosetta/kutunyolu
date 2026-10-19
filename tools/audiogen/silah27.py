"""v27 yeni silahların sesleri (tek başına çalışır; export_audio.py'nin tam üretimine dokunmaz):
  kuzgu_isin_dongu   Kam Küzgüsü ışını: sıcak, ince titreşen uğultu + parıltılı cızırtı (döngü; Ses.loop_pitch ısıyla tizleşir)
  tatar_atis_1..2    Tatar Yayı: ağır kiriş "TUNK" (alçak gövde + kısa ahşap tıkırtı + metal tını)
  tatar_kurma        kurma çarkının tıkırtısı (kurulurken; Kusursuz Kurma ile)
  albasti_goc        Albastı Göçü: emilen fısıltı + ters süpürme (kaybolup belirme)
  bag_zincir         Tengri Bağı: çınlayan gök zinciri (kurulunca / çekişte)
Kullanım: python tools/audiogen/silah27.py  (assets/audio/sfx/*.wav + sfx.json girdileri; hedef yükseklikler aşağıda)"""
import os
import sys
import json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, t_axis, exp_env, noise, sine, sweep, fade, hp, lp, bp, master, write_wav, distort

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'audio', 'sfx')
TARGET = {'kuzgu_isin_dongu': -19.0, 'tatar_atis': -11.0, 'tatar_kurma': -15.0, 'albasti_goc': -13.0, 'bag_zincir': -13.0}


def kuzgu_loop():
    dur = 1.2   # döngü: bütün bileşenler bu sürede tam devir yapar
    t = t_axis(dur)
    base = 0.0
    for f, g in ((220.0, 0.5), (330.0, 0.32), (440.0, 0.22), (660.0, 0.12)):
        base = base + g * np.sin(2 * np.pi * f * t + np.sin(2 * np.pi * 5.0 * t) * 0.8)
    trem = 0.8 + 0.2 * np.sin(2 * np.pi * 10.0 * t)
    n = noise(dur, seed=27)
    hiss = bp(n, 3000, 9000) * (0.5 + 0.5 * np.sin(2 * np.pi * 15.0 * t) ** 2)
    crack = np.zeros_like(t)
    rng = np.random.default_rng(5)
    for k in range(18):
        i = int(rng.uniform(0, len(t) - 400))
        crack[i:i + 400] += rng.uniform(0.3, 1.0) * np.exp(-np.arange(400) / 60.0) * rng.choice([-1, 1])
    x = base * trem * 0.6 + hiss * 0.35 + hp(crack, 2000) * 0.25
    return x


def tatar_atis(i):
    dur = 0.45
    t = t_axis(dur)
    body = sweep(150 - 12 * i, 55, dur, curve=2.0) * exp_env(dur, 14.0)
    snap = bp(noise(dur, seed=40 + i), 600, 4000) * exp_env(dur, 70.0)
    ring = (np.sin(2 * np.pi * 1750 * t) + 0.5 * np.sin(2 * np.pi * 2630 * t)) * exp_env(dur, 22.0) * 0.18
    thr = lp(noise(dur, seed=50 + i), 900) * exp_env(dur, 9.0) * 0.4
    return fade(distort(body * 1.1, 2.0) * 0.8 + snap * 0.7 + ring + thr, 0.001, 0.05)


def tatar_kurma():
    dur = 0.3
    x = np.zeros(int(SR * dur))
    for k, at in enumerate((0.0, 0.07, 0.14)):
        c = bp(noise(0.03, seed=60 + k), 1500, 6000) * exp_env(0.03, 120.0)
        i = int(at * SR)
        x[i:i + len(c)] += c * (0.7 + 0.15 * k)
    return x


def albasti_goc():
    dur = 0.55
    t = t_axis(dur)
    n = noise(dur, seed=71)
    env_in = np.clip(t / 0.35, 0, 1) ** 2 * np.exp(-np.maximum(0, t - 0.35) * 30)
    swoosh = bp(n, 400, 3000) * env_in
    whisper = bp(noise(dur, seed=72), 2500, 7000) * (np.sin(2 * np.pi * 7 * t) ** 2) * env_in * 0.5
    low = sweep(90, 45, dur) * env_in * 0.4
    return fade(swoosh + whisper + low, 0.005, 0.04)


def bag_zincir():
    dur = 0.7
    t = t_axis(dur)
    x = 0.0
    rng = np.random.default_rng(9)
    for k in range(6):
        f = 1200 * (1 + 0.37 * k) + rng.uniform(-40, 40)
        x = x + np.sin(2 * np.pi * f * t) * exp_env(dur, 6.0 + 2 * k) * (0.5 / (1 + k * 0.3))
    clink = np.zeros_like(t)
    for at in (0.0, 0.05, 0.11):
        i = int(at * SR)
        c = bp(noise(0.02, seed=int(at * 100) + 3), 3000, 9000) * exp_env(0.02, 150.0)
        clink[i:i + len(c)] += c
    zap = bp(noise(dur, seed=91), 800, 5000) * exp_env(dur, 18.0) * 0.4
    return fade(x + clink * 0.8 + zap, 0.001, 0.08)


def build_all():
    out = {'kuzgu_isin_dongu': kuzgu_loop(), 'tatar_kurma': tatar_kurma(), 'albasti_goc': albasti_goc(), 'bag_zincir': bag_zincir()}
    for i in (1, 2):
        out['tatar_atis_%d' % i] = tatar_atis(i)
    return out


if __name__ == '__main__':
    res = build_all()
    mp = os.path.join(A, 'sfx.json')
    meta = json.load(open(mp, encoding='utf-8'))
    for name, x in res.items():
        loop = name.endswith('_dongu')
        key = name.rsplit('_', 1)[0] if name[-1].isdigit() else name
        db = TARGET.get(key, TARGET.get(name, -12.0))
        y = master(x, db, loop=loop)
        write_wav(os.path.join(A, name + '.wav'), y, SR, None)
        meta[name] = {'loop': loop, 'len': round(len(y) / SR, 3), 'hedef_db': db}
        print(name, round(len(y) / SR, 3), db)
    json.dump(meta, open(mp, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
