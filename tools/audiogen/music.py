"""Müzik döngüleri (prosedürel): kopuz (Karplus-Strong) + davul + rüzgâr/pad. Makam: Hicaz (1 b2 3 4 5 b6 b7) ve
Hüseyni benzeri (1 2 b3 4 5 6 b7). Her biyomun temposu, tınısı ve yoğunluğu farklı; hepsi dikişsiz döngü."""
import math
import numpy as np
from synth import SR, t_axis, env, exp_env, noise, fft_filter, sine, sweep, pluck, reverb, delay, distort, mix, place, fade

MSR = 22050  # müzik örnekleme hızı (dosya boyutu)

HICAZ = [0, 1, 4, 5, 7, 8, 10]
HUSEYNI = [0, 2, 3, 5, 7, 9, 10]
KURDI = [0, 1, 3, 5, 7, 8, 10]


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def drum(kind, sr=MSR):
    if kind == 'dum':
        dur = 0.4
        x = sweep(140, 48, dur, sr=sr, curve=0.5) * exp_env(dur, 12, sr)
        return mix(x, fft_filter(noise(dur, sr, 3), lo=100, hi=1500, sr=sr) * exp_env(dur, 40, sr) * 0.3)
    if kind == 'tek':
        dur = 0.18
        x = sweep(500, 180, dur, sr=sr, curve=0.6) * exp_env(dur, 30, sr) * 0.5
        return mix(x, fft_filter(noise(dur, sr, 4), lo=1500, hi=7000, sr=sr) * exp_env(dur, 45, sr) * 0.6)
    if kind == 'ka':
        dur = 0.1
        return fft_filter(noise(dur, sr, 5), lo=2500, hi=9000, sr=sr) * exp_env(dur, 60, sr) * 0.35
    dur = 0.9  # 'dev' derin davul
    x = sweep(90, 32, dur, sr=sr, curve=0.4) * exp_env(dur, 6, sr)
    return mix(x, fft_filter(noise(dur, sr, 6), hi=400, sr=sr) * exp_env(dur, 8, sr) * 0.5)


def pad(freqs, dur, sr=MSR, lp=900, wob=0.15, seed=11):
    t = t_axis(dur, sr)
    x = np.zeros(len(t))
    for k, f in enumerate(freqs):
        det = 1 + 0.004 * ((k % 3) - 1)
        x += np.sin(2 * np.pi * f * det * t + 0.3 * np.sin(2 * np.pi * (0.07 + 0.03 * k) * t)) / (k + 1.5)
    x *= 1 + wob * np.sin(2 * np.pi * 0.11 * t + seed)
    return fft_filter(x, hi=lp, sr=sr, slope=1.0)


def wind(dur, sr=MSR, seed=21, lo=150, hi=1500, amt=1.0):
    x = fft_filter(noise(dur, sr, seed), lo=lo, hi=hi, sr=sr, slope=1.0)
    m = fft_filter(noise(dur, sr, seed + 1), hi=0.4, sr=sr, slope=1.0)
    m = (m - m.min()) / (m.max() - m.min() + 1e-9)
    return x * (0.2 + 0.8 * m) * amt


def drips(dur, sr=MSR, seed=31, n=24):
    rng = np.random.default_rng(seed)
    x = np.zeros(int(dur * sr))
    for _ in range(n):
        f = rng.uniform(1200, 3200)
        d = sweep(f, f * 0.6, 0.12, sr=sr) * exp_env(0.12, 30, sr) * rng.uniform(0.2, 0.5)
        place(x, d, rng.uniform(0, dur - 0.2), 1.0, sr)
    return reverb(x, 1.5, 0.5, sr)


def melody(scale, root, bars, bpm, sr=MSR, seed=1, density=0.6, bright=0.5, octave=0, rest_p=0.25, decay=0.995):
    """Makam üstünde yürüyen kopuz ezgisi: komşu adımlar çoğunlukta, arada sıçrama; eşlik için beşli dron."""
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm
    total = bars * 4 * beat
    x = np.zeros(int(total * sr))
    deg = 0
    t = 0.0
    while t < total - beat * 0.5:
        step = rng.choice([-2, -1, -1, 0, 1, 1, 2, 3, -3], p=[0.08, 0.25, 0.1, 0.1, 0.25, 0.08, 0.06, 0.04, 0.04])
        deg = int(np.clip(deg + step, -3, 10))
        ln = rng.choice([0.5, 1.0, 1.0, 1.5, 2.0], p=[0.35, 0.3, 0.1, 0.15, 0.1]) * beat
        if rng.random() > rest_p:
            n = root + 12 * octave + scale[deg % 7] + 12 * (deg // 7)
            f = midi(n)
            dur = min(ln * 1.6, 2.5)
            p = pluck(f, dur, sr, bright=bright, decay=decay, seed=int(rng.integers(1e6)))
            place(x, p * rng.uniform(0.35, 0.6), t, 1.0, sr)
            if rng.random() < 0.3:  # çarpma (süsleme)
                g = pluck(midi(n + scale[(deg + 1) % 7] - scale[deg % 7]), 0.3, sr, bright=bright, seed=int(rng.integers(1e6)))
                place(x, g * 0.25, max(0.0, t - beat * 0.12), 1.0, sr)
        t += ln
    return x


def drone(root, dur, sr=MSR, fifth=True, lp=700):
    f = midi(root)
    freqs = [f, f * 1.005, f * 0.5]
    if fifth:
        freqs += [f * 1.5, f * 1.5 * 0.997]
    return pad(freqs, dur, sr, lp=lp)


def rhythm(pattern, bars, bpm, sr=MSR, gain=1.0, swing=0.0):
    """pattern: 16'lık dizi, 'D' dum, 'T' tek, 'K' ka, '.' sus, 'B' dev davul."""
    beat = 60.0 / bpm
    total = bars * 4 * beat
    x = np.zeros(int(total * sr))
    cache = {k: drum(v, sr) for k, v in (('D', 'dum'), ('T', 'tek'), ('K', 'ka'), ('B', 'dev'))}
    for b in range(bars):
        for i, ch in enumerate(pattern):
            if ch == '.':
                continue
            t = b * 4 * beat + i * beat / 4 + (swing * beat / 4 if i % 2 else 0)
            place(x, cache[ch], t, gain, sr)
    return x


def loopify(x, sr=MSR, xf=1.5):
    """Dikişsiz döngü: sonun kuyruğunu başa çapraz geçir."""
    n = int(xf * sr)
    y = x[:-n].copy()
    tail = x[-n:]
    w = np.linspace(0, 1, n)
    y[:n] = y[:n] * w + tail * (1 - w)
    return y


def track(biome, sr=MSR):
    if biome == 'otuken':
        bpm, bars, root, scale = 72, 8, 50, HICAZ
        mel = melody(scale, root + 12, bars, bpm, sr, seed=3, bright=0.45, rest_p=0.35)
        dr = drone(root, bars * 4 * 60 / bpm, sr, lp=600)
        rh = rhythm('D...T.K.D..DT.K.', bars, bpm, sr, 0.6)
        wn = wind(bars * 4 * 60 / bpm, sr, 21, 120, 900, 0.35)
        x = mix(mel * 0.8, dr * 0.35, rh, wn)
        x = delay(x, 60 / bpm * 0.75, 0.3, 0.25, sr)
    elif biome == 'bozkir':
        bpm, bars, root, scale = 104, 8, 55, HUSEYNI
        mel = melody(scale, root + 12, bars, bpm, sr, seed=5, bright=0.7, rest_p=0.2, octave=0)
        mel2 = melody(scale, root, bars, bpm, sr, seed=6, bright=0.4, rest_p=0.55, decay=0.993)
        dr = drone(root, bars * 4 * 60 / bpm, sr, lp=900)
        rh = rhythm('D.T.K.T.D.T.KKT.', bars, bpm, sr, 0.75, swing=0.1)
        wn = wind(bars * 4 * 60 / bpm, sr, 22, 300, 2500, 0.3)
        x = mix(mel * 0.8, mel2 * 0.5, dr * 0.25, rh, wn)
    elif biome == 'sahmeran':
        bpm, bars, root, scale = 64, 8, 45, KURDI
        mel = melody(scale, root + 24, bars, bpm, sr, seed=7, bright=0.3, rest_p=0.5, decay=0.997)
        dr = drone(root, bars * 4 * 60 / bpm, sr, lp=400)
        rh = rhythm('B.......K...B.K.', bars, bpm, sr, 0.5)
        dp = drips(bars * 4 * 60 / bpm, sr, 31, 20)
        x = mix(reverb(mel, 2.5, 0.5, sr) * 0.7, dr * 0.45, rh, dp * 0.6)
    elif biome == 'kaf':
        bpm, bars, root, scale = 84, 8, 57, HUSEYNI
        mel = melody(scale, root + 24, bars, bpm, sr, seed=9, bright=0.8, rest_p=0.4, decay=0.996)
        dr = drone(root, bars * 4 * 60 / bpm, sr, lp=1200)
        rh = rhythm('D...K.T...K.T.K.', bars, bpm, sr, 0.45)
        wn = wind(bars * 4 * 60 / bpm, sr, 23, 400, 4000, 0.6)
        ch = pad([midi(root + 24), midi(root + 31), midi(root + 36)], bars * 4 * 60 / bpm, sr, lp=2500, wob=0.3, seed=4) * 0.12
        x = mix(reverb(mel, 2.0, 0.4, sr) * 0.7, dr * 0.3, rh, wn, ch)
    elif biome == 'tamu':
        bpm, bars, root, scale = 92, 8, 43, HICAZ
        mel = melody(scale, root + 12, bars, bpm, sr, seed=11, bright=0.5, rest_p=0.3)
        dr = distort(drone(root, bars * 4 * 60 / bpm, sr, lp=500), 2.5)
        rh = rhythm('B.K.T.K.B.KKT.K.', bars, bpm, sr, 0.9)
        wn = fft_filter(noise(bars * 4 * 60 / bpm, sr, 41), lo=60, hi=500, sr=sr) * 0.25
        x = mix(mel * 0.7, dr * 0.4, rh, wn)
    elif biome == 'yurt':  # Ulu Kayın: sakin, sıcak
        bpm, bars, root, scale = 66, 8, 57, HUSEYNI
        mel = melody(scale, root + 12, bars, bpm, sr, seed=13, bright=0.55, rest_p=0.4, decay=0.997)
        dr = drone(root, bars * 4 * 60 / bpm, sr, lp=800)
        rh = rhythm('D.......T.......', bars, bpm, sr, 0.3)
        fire = fft_filter(noise(bars * 4 * 60 / bpm, sr, 51), lo=300, hi=3000, sr=sr) * 0.08
        x = mix(reverb(mel, 1.5, 0.3, sr) * 0.8, dr * 0.35, rh, fire)
    else:  # başlık
        bpm, bars, root, scale = 60, 8, 50, HICAZ
        mel = melody(scale, root + 12, bars, bpm, sr, seed=17, bright=0.4, rest_p=0.5, decay=0.997)
        dr = drone(root, bars * 4 * 60 / bpm, sr, lp=500)
        wn = wind(bars * 4 * 60 / bpm, sr, 61, 100, 1200, 0.4)
        x = mix(reverb(mel, 2.5, 0.5, sr) * 0.7, dr * 0.45, wn)
    return loopify(x, sr)
