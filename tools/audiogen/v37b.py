"""v37b ölüm sesi: oyuncunun seçtiği aday "olum_2a" ("vışkkkkk" + hafif "vıcık" et katmanı) ve çeşitleri.
İstek (oyuncu): "olum_2a'yı seçiyorum; kesip biçerken hep aynı ses çalmasın, çeşitlerini yap."

Yapı (scratch_v37/aday/aday.py: olum_2 + olum_2x(0) ile birebir; çeşit 1 = seçilen aday):
  "vış"   : bant geçiren gürültü 800 → 3800 Hz süpürme (sonda doruk) + OGA Swishes savuruşu (perde yukarı)
  "kkkkk" : tane bulutu: saniyede ~1100 → 60 sıklaşıp seyrelen çıtırtılar, %45'i yukarı kayan minik ıslak damla
  cızırtı : 3,5-11 kHz gürültü, düzensiz genlik kıpırtısı (yağda cızırdama)
  "vıcık" : 200-900 Hz ıslak sıkışma (perde oynayan yakın rezonanslar) + Kenney impactSoft_heavy (perde aşağı)
  yırtılma: takılıp kopan kısa gürültü patlamaları (600-3200 Hz); yapışkan damlalar (düşük perdeli "plop"lar)
Çeşitler (vahset_patla_1..6): vış perdesi / hızı ± %8-15, çıtırtı / damla / yırtılma tohumları farklı, vıcık zamanı ve
perdesi biraz farklı, uzunluk 0,45-0,6 sn. Ağır (vahset_patla_agir_1..3: kritik, bitirici, seçkin, boss): aynı karakter,
daha dolgun (alt kesim düşük), vıcık daha uzun / gür (ikinci vıcık), çıtırtı daha uzun.
Kaynaklar (CC0): Kenney Impact Sounds (impactSoft_heavy_001/003), OGA "Swishes Sound Pack" (swish-2/4/7/10). Kalanı sentez.
Hiçbir oyunun sesi kullanılmadı.

Kullanım: python tools/audiogen/v37b.py   (vahset_patla_1..6 + vahset_patla_agir_1..3 yazar, sfx.json'u günceller;
          export_audio.py de v37'den sonra bunu çağırır)"""
import os
import sys
import json
import numpy as np
import soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, t_axis, exp_env, noise, fft_filter, bp, distort, master, write_wav

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'audio', 'sfx')
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
TARGET = {'vahset_patla': -6.0, 'vahset_patla_agir': -5.0}   # v37 ile aynı düzey
_c = {}


def load(rel):
    if rel in _c:
        return _c[rel]
    x, sr = sf.read(os.path.join(SRC, rel), always_2d=True)
    x = x.mean(axis=1)
    if sr != SR:
        n = int(len(x) * SR / sr)
        x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)
    i = np.argmax(np.abs(x) > 0.02 * np.max(np.abs(x)))
    x = x[max(0, i - 40):]
    x = x / (np.max(np.abs(x)) + 1e-9)
    _c[rel] = x
    return x


def KI(f):
    return load('impact/Audio/' + f)


def pitch(x, f):
    n = int(len(x) / f)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def cut(x, dur, fo=0.03):
    y = x[:int(dur * SR)].copy()
    n = int(fo * SR)
    if len(y) > n:
        y[-n:] *= np.linspace(1, 0, n) ** 2
    return y


def nrm(x):
    return x / (np.max(np.abs(x)) + 1e-9)


def mix(parts, dur):
    out = np.zeros(int(dur * SR))
    for x, t, g in parts:
        a = int(t * SR)
        b = min(len(out), a + len(x))
        if b > a:
            out[a:b] += x[:b - a] * g
    return out


def whoosh(dur, f_a, f_b, seed, rise=0.75, bw=0.6):
    """'vış': bant geçiren gürültü, merkezi f_a → f_b süpürür; genlik yükselip sonda doruğa varır."""
    src = noise(dur + 0.01, seed=seed)
    n = int(dur * SR)
    y = np.zeros(n)
    seg = 16
    ed = np.linspace(0, n, seg + 1).astype(int)
    for k in range(seg):
        fc = f_a * (f_b / f_a) ** ((k + 0.5) / seg)
        y[ed[k]:ed[k + 1]] = bp(src, fc * (1 - bw * 0.5), fc * (1 + bw))[ed[k]:ed[k + 1]]
    t = np.linspace(0, 1, n)
    envl = np.where(t < rise, (t / rise) ** 2.0, np.exp(-(t - rise) / (1 - rise) * 4.0))
    return y * envl


def swish(i, p=1.3, dur=0.16, lo=700.0):
    """Gerçek savuruş (OGA Swishes), perde yukarı, kısa."""
    x = load('swishes/swishes/swish-%d.wav' % i)
    e = np.convolve(np.abs(x), np.ones(441) / 441, 'same')
    pk = int(np.argmax(e))
    s = max(0, pk - int(0.09 * SR * p))
    y = pitch(x[s:], p)[:int(dur * SR)]
    y = fft_filter(y, lo=lo, slope=2.0)
    return nrm(y) * np.linspace(0.3, 1, len(y)) ** 0.5


def crackle(dur, seed, rate=(900.0, 60.0), lo=1500.0, hi=9000.0, wet=0.0, gl=(0.0008, 0.004), decay=4.0):
    """'kkkkk' tane bulutu; wet>0 iken tanelerin bir kısmı yukarı kayan minik ıslak damla olur."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    x = np.zeros(n)
    t = 0.0
    while t < dur:
        u = t / dur
        r = rate[0] * (rate[1] / rate[0]) ** u
        t += rng.exponential(1.0 / r)
        st = int(t * SR)
        if st >= n:
            break
        amp = np.exp(-decay * u) * rng.uniform(0.3, 1.0)
        if rng.random() < wet:
            L = int(rng.uniform(0.004, 0.012) * SR)
            tg = np.arange(L) / SR
            f0 = rng.uniform(1200, 4000)
            ph = 2 * np.pi * np.cumsum(f0 * (1 + 2.5 * tg / tg[-1])) / SR
            g = np.sin(ph) * np.exp(-tg * rng.uniform(250, 600)) * 0.8
        else:
            L = max(8, int(rng.uniform(*gl) * SR))
            g = rng.uniform(-1, 1, L) * np.exp(-np.arange(L) / L * 5)
            fc = rng.uniform(lo, hi)
            g = g + 0.6 * np.sin(2 * np.pi * fc * np.arange(L) / SR) * np.exp(-np.arange(L) / L * 4)
        e = min(n, st + L)
        x[st:e] += g[:e - st] * amp
    return fft_filter(x, lo=lo * 0.6, hi=hi * 1.3, slope=1.5)


def sizzle(dur, seed, lo=3000.0, hi=11000.0, k=6.0, am=55.0):
    """Islak cızırtı: tiz gürültü, düzensiz genlik kıpırtısı."""
    rng = np.random.default_rng(seed)
    x = fft_filter(noise(dur, seed=seed), lo=lo, hi=hi, slope=2.0)
    m = np.abs(fft_filter(rng.standard_normal(len(x)), hi=am, slope=1.0))
    m = m / (np.max(m) + 1e-9)
    return x * m ** 1.3 * exp_env(dur, k)


def splat(p=0.95, dur=0.12):
    x = cut(pitch(KI('impactSoft_heavy_001.ogg'), p), dur, 0.04)
    return fft_filter(x, lo=180, slope=2.0)


def squelch(dur, seed, f0=420.0, wob=0.35):
    """'Vıcık': 200-900 Hz ıslak sıkışma; yakın rezonanslar, hızlı perde oynaması, gürültü pürüzü."""
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    x = np.zeros(len(t))
    for j, r in enumerate((1.0, 1.55, 2.1)):
        fm = f0 * r * (1 + wob * np.sin(2 * np.pi * rng.uniform(22, 38) * t + rng.uniform(0, 6)) * np.exp(-t * 12)
                       + 0.4 * (1 - np.exp(-t * 25)))
        x += np.sin(2 * np.pi * np.cumsum(fm) / SR) * (0.8 ** j)
    nz = fft_filter(noise(dur, seed=seed + 1), lo=200, hi=900, slope=2.0)
    x = x * (0.6 + 0.4 * nrm(np.abs(nz))) + nrm(nz) * 1.2
    e = np.minimum(t / 0.004, 1.0) * np.exp(-t * 6.91 / dur * 1.3)
    return distort(nrm(x * e), 1.8)


def tear(dur, seed, n=55, lo=600.0, hi=3200.0):
    """Islak yırtılma: takılıp kopan kısa gürültü patlamaları dizisi."""
    rng = np.random.default_rng(seed)
    src = fft_filter(noise(dur + 0.02, seed=seed), lo=lo, hi=hi, slope=2.0)
    m = np.zeros(int(dur * SR))
    for tt in np.sort(rng.beta(1.5, 3.0, n)) * dur:
        st = int(tt * SR)
        L = int(rng.uniform(0.002, 0.007) * SR)
        e = min(len(m), st + L)
        m[st:e] += np.exp(-np.arange(e - st) / L * 3) * rng.uniform(0.4, 1.0)
    return nrm(src[:len(m)] * m)


def drops(dur, seed, n=14):
    """Yapışkan sıçrayan damlalar."""
    return nrm(crackle(dur, seed, rate=(n * 6.0, n * 1.0), lo=500, hi=3500, wet=1.0, decay=2.0))


def kill_finish(x, dur, lo=250.0, drive=1.3):
    x = fft_filter(x, lo=lo, slope=2.0)
    x = distort(nrm(x), drive)
    return cut(x, dur, 0.08)


# çeşit: ps (vış perde / hız çarpanı), sw (savuruş kaydı), sd (tohum kayması), sq (vıcık perde çarpanı), dt (vıcık
# zaman kayması, sn), d (uzunluk)
VAR = [
    dict(ps=1.00, sw=7, sd=0, sq=1.00, dt=0.000, d=0.55),    # = aday olum_2a
    dict(ps=1.10, sw=7, sd=11, sq=1.08, dt=-0.004, d=0.50),
    dict(ps=0.90, sw=4, sd=23, sq=0.92, dt=0.006, d=0.58),
    dict(ps=1.14, sw=10, sd=37, sq=1.04, dt=0.002, d=0.47),
    dict(ps=0.87, sw=7, sd=41, sq=0.95, dt=0.008, d=0.60),
    dict(ps=1.06, sw=4, sd=59, sq=1.12, dt=-0.002, d=0.52),
]
HVAR = [
    dict(ps=0.92, sw=7, sd=101, sq=0.90, dt=0.000, d=0.60),
    dict(ps=0.86, sw=2, sd=113, sq=0.85, dt=0.005, d=0.62),
    dict(ps=0.98, sw=10, sd=127, sq=0.94, dt=-0.003, d=0.60),
]


def olum(v, heavy=False):
    ps, sd, d = v['ps'], v['sd'], v['d']
    w = 0.11 / ps
    raw = mix([(whoosh(w, 800 * ps, 3800 * ps, 201 + sd, rise=0.8), 0, 0.9), (swish(v['sw'], 1.3 * ps, w), 0, 0.5),
               (crackle(0.42 + (0.06 if heavy else 0), 202 + sd, rate=(1100, 60), lo=1300, hi=7500, wet=0.45), w - 0.01, 0.9),
               (sizzle(0.4, 203 + sd, 3500, 11000, 5.5), w - 0.005, 0.5),
               (splat(1.2 * (0.9 if heavy else 1.0), 0.07), w - 0.012, 0.35)], d)
    g = 0.75 if heavy else 0.45
    s = 700 + sd
    sq0 = w - 0.012 + v['dt']
    soft = fft_filter(cut(pitch(KI('impactSoft_heavy_003.ogg'), (0.75 if heavy else 0.8) * v['sq']), 0.12, 0.04), lo=180, slope=2.0)
    parts = [(nrm(raw), 0, 0.85 if heavy else 1.0),
             (squelch(0.14 if heavy else 0.11, s, 420 * v['sq'] * (0.9 if heavy else 1.0)), sq0, 0.55 * g),
             (nrm(soft), sq0, 0.4 * g),
             (tear(0.2 if heavy else 0.16, s + 3, 55 if heavy else 40), w - 0.005 + v['dt'], 0.5 * g),
             (drops(0.4, s + 4, 16 if heavy else 10), w + 0.03, 0.4 * g)]
    if heavy:
        parts.append((squelch(0.07, s + 2, 590 * v['sq'], 0.5), w + 0.06 + v['dt'], 0.3 * g))
    x = mix(parts, d)
    return kill_finish(x, d, 110 if heavy else 150, 1.35 if heavy else 1.3)


def build_all():
    out = {}
    for i, v in enumerate(VAR):
        out['vahset_patla_%d' % (i + 1)] = olum(v)
    for i, v in enumerate(HVAR):
        out['vahset_patla_agir_%d' % (i + 1)] = olum(v, True)
    return out


def target_for(name):
    return TARGET['vahset_patla_agir' if name.startswith('vahset_patla_agir') else 'vahset_patla']


def main():
    allx = build_all()
    mp = os.path.join(A, 'sfx.json')
    meta = json.load(open(mp, encoding='utf-8'))
    for name, x in sorted(allx.items()):
        y = master(x, target_for(name))
        write_wav(os.path.join(A, name + '.wav'), y, SR, None)
        meta[name] = {'loop': False, 'len': round(len(y) / SR, 3), 'hedef_db': target_for(name)}
        print(name, round(len(y) / SR, 3))
    json.dump(meta, open(mp, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('yazıldı:', len(allx))


if __name__ == '__main__':
    main()
