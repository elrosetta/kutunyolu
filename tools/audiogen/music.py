"""Müzik döngüleri (prosedürel): kopuz (Karplus-Strong) + davul + rüzgâr/pad. Makam: Hicaz (1 b2 3 4 5 b6 b7) ve
Hüseyni benzeri (1 2 b3 4 5 6 b7). Her biyomun temposu, tınısı ve yoğunluğu farklı; hepsi dikişsiz döngü."""
import math
import numpy as np
from synth import SR, t_axis, env, exp_env, noise, fft_filter, sine, sweep, pluck, reverb, delay, distort, mix, place, fade

MSR = 22050  # müzik örnekleme hızı (dosya boyutu)
# biyom başına hedef yükseklik (synth.loudness, dB): savaş biyomları biraz önde, yurt/başlık sakin
TARGET_DB = {'otuken': -14.5, 'bozkir': -14.0, 'sahmeran': -15.0, 'kaf': -14.5, 'tamu': -14.0, 'boss': -13.5, 'yurt': -16.5, 'baslik': -16.0}

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


def melody(scale, root, bars, bpm, sr=MSR, seed=1, density=0.6, bright=0.5, octave=0, rest_p=0.25, decay=0.995, ab=True):
    """Makam üstünde yürüyen kopuz ezgisi: komşu adımlar çoğunlukta, arada sıçrama; eşlik için beşli dron.
    ab: parça iki bölümlü (A/B) — ikinci yarı başka tohumla, biraz daha yoğun ve bir derece yukarıda gezinir (tekrar hissi azalır)."""
    rng = np.random.default_rng(seed)
    rng_b = np.random.default_rng(seed + 1000)
    beat = 60.0 / bpm
    total = bars * 4 * beat
    x = np.zeros(int(total * sr))
    deg = 0
    t = 0.0
    half = False
    while t < total - beat * 0.5:
        if ab and not half and t >= total / 2:
            half = True
            rng = rng_b
            rest_p = rest_p * 0.75
            deg = 2
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


def rhythm(pattern, bars, bpm, sr=MSR, gain=1.0, swing=0.0, fill=None):
    """pattern: 16'lık dizi, 'D' dum, 'T' tek, 'K' ka, '.' sus, 'B' dev davul. fill: her 4. ölçüde çalınan dolgu kalıbı."""
    beat = 60.0 / bpm
    total = bars * 4 * beat
    x = np.zeros(int(total * sr))
    cache = {k: drum(v, sr) for k, v in (('D', 'dum'), ('T', 'tek'), ('K', 'ka'), ('B', 'dev'))}
    for b in range(bars):
        pat = fill if (fill and b % 4 == 3) else pattern
        for i, ch in enumerate(pat):
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


def bassline(scale, root, bars, bpm, sr=MSR, seed=2, pattern='x.x.x.xxx.x.x.x.', octave=-1):
    """Tınlayan kopuz bası: kök/beşli/yedili üzerinde 16'lık yürüyüş; sürüş hissi (Dead Cells'in bas çizgileri gibi)."""
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm
    total = bars * 4 * beat
    x = np.zeros(int(total * sr))
    degs = [0, 0, 4, 0, 6, 0, 4, 3]
    for b in range(bars):
        for i, ch in enumerate(pattern):
            if ch == '.':
                continue
            t = b * 4 * beat + i * beat / 4
            dg = degs[(b * 2 + i // 8) % len(degs)] if rng.random() > 0.2 else int(rng.integers(0, 7))
            n = root + 12 * octave + scale[dg % 7]
            p = pluck(midi(n), beat * 0.6, sr, bright=0.25, decay=0.992, seed=int(rng.integers(1e6)))
            place(x, p * 0.6, t, 1.0, sr)
    return fft_filter(x, hi=1800, sr=sr, slope=1.0)


def riff(scale, root, bars, bpm, sr=MSR, seed=4, notes=None, octave=1):
    """Tekrarlayan kopuz riffi (kanca): 2 ölçülük motif, her tekrarda hafif varyasyon."""
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm
    total = bars * 4 * beat
    x = np.zeros(int(total * sr))
    if notes is None:
        notes = [(0, 0.5), (2, 0.5), (4, 0.5), (3, 0.5), (4, 1.0), (6, 0.5), (4, 0.5), (2, 1.0), (0, 0.5), (1, 0.5), (0, 2.0)]
    t = 0.0
    k = 0
    while t < total - beat * 0.5:
        dg, ln = notes[k % len(notes)]
        if (k // len(notes)) % 2 == 1 and rng.random() < 0.3:
            dg = (dg + 2) % 7
        f = midi(root + 12 * octave + scale[dg % 7] + (12 if dg >= 7 else 0))
        p = pluck(f, min(ln * beat * 1.4, 1.6), sr, bright=0.7, decay=0.996, seed=int(rng.integers(1e6)))
        place(x, p * 0.5, t, 1.0, sr)
        t += ln * beat
        k += 1
    return x


def track(biome, sr=MSR):
    if biome in ('otuken', 'bozkir', 'sahmeran', 'kaf', 'tamu', 'boss', 'baslik'):
        import turku
        return turku.track(biome, sr)
    """Hareketli savaş müzikleri: sürücü davul (16'lık tef + dum), kopuz bası, riff kancası, üstte doğaçlama ezgi."""
    if biome == 'otuken':
        bpm, bars, root, scale = 126, 16, 50, HICAZ
        rh = rhythm('D.K.T.K.D.KKT.K.', bars, bpm, sr, 0.85, fill='D.K.TTK.D.KKTTKK')
        bs = bassline(scale, root, bars, bpm, sr, 2, 'x.x.x.x.xx.x.x.x')
        rf = riff(scale, root, bars, bpm, sr, 4)
        mel = melody(scale, root + 12, bars, bpm, sr, seed=3, bright=0.5, rest_p=0.4)
        dr = drone(root, bars * 4 * 60 / bpm, sr, lp=500)
        x = mix(rh * 1.0, bs * 0.9, rf * 0.8, mel * 0.45, dr * 0.2)
        x = delay(x, 60 / bpm * 0.75, 0.25, 0.18, sr)
    elif biome == 'bozkir':
        bpm, bars, root, scale = 138, 16, 55, HUSEYNI
        rh = rhythm('D.T.K.T.D.T.KKT.', bars, bpm, sr, 0.9, swing=0.08, fill='D.TTK.T.D.TKTKTK')
        bs = bassline(scale, root, bars, bpm, sr, 5, 'x.x.x.x.x.x.x.xx')
        rf = riff(scale, root, bars, bpm, sr, 6, [(0, 0.5), (2, 0.5), (4, 0.5), (5, 0.5), (4, 0.5), (2, 0.5), (0, 1.0), (7, 0.5), (6, 0.5), (4, 1.0), (2, 0.5), (0, 0.5)])
        mel = melody(scale, root + 24, bars, bpm, sr, seed=7, bright=0.75, rest_p=0.35, decay=0.994)
        wn = wind(bars * 4 * 60 / bpm, sr, 22, 300, 2500, 0.1)
        x = mix(rh, bs * 0.9, rf * 0.8, mel * 0.4, wn)
    elif biome == 'sahmeran':
        bpm, bars, root, scale = 112, 16, 45, KURDI
        rh = rhythm('B.K.T.K.B.K.T.KK', bars, bpm, sr, 0.8, fill='B.K.TTK.B.KKT.KK')
        bs = bassline(scale, root, bars, bpm, sr, 8, 'x..x..x.x..x..x.')
        rf = riff(scale, root, bars, bpm, sr, 9, [(0, 0.5), (1, 0.5), (0, 0.5), (3, 0.5), (4, 1.0), (3, 0.5), (1, 0.5), (0, 1.0), (6, 0.5), (4, 0.5), (3, 1.0)])
        mel = melody(scale, root + 24, bars, bpm, sr, seed=10, bright=0.35, rest_p=0.5, decay=0.997)
        dp = drips(bars * 4 * 60 / bpm, sr, 31, 14)
        x = mix(rh, bs * 0.9, reverb(rf, 1.5, 0.35, sr) * 0.7, reverb(mel, 2.5, 0.5, sr) * 0.4, dp * 0.4)
    elif biome == 'kaf':
        bpm, bars, root, scale = 132, 16, 57, HUSEYNI
        rh = rhythm('D.K.K.T.D.K.T.KK', bars, bpm, sr, 0.85, fill='D.K.K.T.DDKKT.TT')
        bs = bassline(scale, root, bars, bpm, sr, 11, 'x.x.x.x.x.x.x.x.')
        rf = riff(scale, root, bars, bpm, sr, 12, [(4, 0.5), (6, 0.5), (7, 0.5), (6, 0.5), (4, 1.0), (2, 0.5), (4, 0.5), (0, 1.0), (2, 0.5), (4, 0.5), (6, 0.5), (4, 0.5)], 1)
        mel = melody(scale, root + 24, bars, bpm, sr, seed=13, bright=0.85, rest_p=0.4, decay=0.996)
        wn = wind(bars * 4 * 60 / bpm, sr, 23, 400, 4000, 0.22)
        ch = pad([midi(root + 24), midi(root + 31), midi(root + 36)], bars * 4 * 60 / bpm, sr, lp=2500, wob=0.3, seed=4) * 0.08
        x = mix(rh, bs * 0.85, rf * 0.8, reverb(mel, 1.6, 0.3, sr) * 0.4, wn, ch)
    elif biome == 'tamu':
        bpm, bars, root, scale = 144, 16, 43, HICAZ
        rh = rhythm('B.K.T.K.B.KKT.K.', bars, bpm, sr, 1.0, fill='B.K.T.K.B.TTB.TT')
        bs = distort(bassline(scale, root, bars, bpm, sr, 14, 'xx.x.x.xxx.x.x.x'), 2.2)
        rf = distort(riff(scale, root, bars, bpm, sr, 15, [(0, 0.5), (1, 0.5), (0, 0.5), (4, 0.5), (3, 0.5), (1, 0.5), (0, 1.0), (0, 0.5), (6, 0.5), (4, 0.5), (3, 0.5), (1, 1.0)]), 1.8)
        mel = melody(scale, root + 12, bars, bpm, sr, seed=16, bright=0.5, rest_p=0.3)
        dr = distort(drone(root, bars * 4 * 60 / bpm, sr, lp=500), 2.5)
        x = mix(rh, bs * 0.8, rf * 0.7, mel * 0.4, dr * 0.25)
    elif biome == 'boss':
        bpm, bars, root, scale = 150, 16, 48, HICAZ
        rh = rhythm('B.KKT.K.B.KKT.KK', bars, bpm, sr, 1.0, fill='BBKKTTKKBBKKTTKK')
        bs = distort(bassline(scale, root, bars, bpm, sr, 20, 'x.x.xx.x.x.xx.xx'), 2.0)
        rf = riff(scale, root, bars, bpm, sr, 21, [(0, 0.25), (0, 0.25), (1, 0.5), (0, 0.5), (4, 0.5), (3, 0.5), (1, 0.5), (0, 1.0), (6, 0.5), (4, 0.5), (3, 0.25), (1, 0.25), (0, 1.0)])
        mel = melody(scale, root + 24, bars, bpm, sr, seed=22, bright=0.8, rest_p=0.25, decay=0.995)
        ch = pad([midi(root + 12), midi(root + 19), midi(root + 24 + 1)], bars * 4 * 60 / bpm, sr, lp=1400, wob=0.4, seed=9) * 0.15
        x = mix(rh * 1.1, bs * 0.9, rf * 0.9, mel * 0.45, ch)
    elif biome == 'yurt':  # Ulu Kayın: sakin, sıcak
        bpm, bars, root, scale = 70, 16, 57, HUSEYNI
        mel = melody(scale, root + 12, bars, bpm, sr, seed=13, bright=0.55, rest_p=0.4, decay=0.997)
        dr = drone(root, bars * 4 * 60 / bpm, sr, lp=800)
        rh = rhythm('D.......T.......', bars, bpm, sr, 0.3, fill='D.......T...T.K.')
        fire = fft_filter(noise(bars * 4 * 60 / bpm, sr, 51), lo=300, hi=3000, sr=sr) * 0.08
        x = mix(reverb(mel, 1.5, 0.3, sr) * 0.8, dr * 0.35, rh, fire)
    else:  # başlık
        bpm, bars, root, scale = 96, 16, 50, HICAZ
        rh = rhythm('D...K.T...K.T.K.', bars, bpm, sr, 0.5, fill='D.K.K.T.D.K.TTKK')
        bs = bassline(scale, root, bars, bpm, sr, 30, 'x...x...x...x.x.')
        mel = melody(scale, root + 12, bars, bpm, sr, seed=17, bright=0.5, rest_p=0.45, decay=0.997)
        dr = drone(root, bars * 4 * 60 / bpm, sr, lp=500)
        wn = wind(bars * 4 * 60 / bpm, sr, 61, 100, 1200, 0.3)
        x = mix(rh, bs * 0.7, reverb(mel, 2.5, 0.5, sr) * 0.7, dr * 0.4, wn)
    # karışım cilası: 60 Hz altı çamuru temizle, hafif doyurma ile yapıştır
    x = fft_filter(x, lo=45, sr=sr, slope=1.5)
    x = np.tanh(x / (np.max(np.abs(x)) + 1e-9) * 1.4) / math.tanh(1.4)
    return loopify(x, sr)
