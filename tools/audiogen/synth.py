"""Saf numpy ses sentezi: gürültü bantları, zarflar, FFT süzgeçleri, Karplus-Strong tını, yankı, WAV yazımı.
Hiçbir dış kütüphane gerekmez. Tüm sesler prosedürel üretilir; ileride bir ses tasarımcısı dosyaları değiştirir."""
import math
import struct
import wave
import numpy as np

SR = 44100


def t_axis(dur, sr=SR):
    return np.arange(int(dur * sr)) / sr


def env(dur, a=0.005, d=0.1, s=0.0, r=0.05, sr=SR, curve=3.0):
    """ADSR benzeri zarf; d ve r üstel (curve) iner."""
    n = int(dur * sr)
    out = np.zeros(n)
    na, nd, nr = int(a * sr), int(d * sr), int(r * sr)
    ns = max(0, n - na - nd - nr)
    i = 0
    if na > 0:
        out[i:i + na] = np.linspace(0, 1, na); i += na
    if nd > 0:
        x = np.linspace(0, 1, nd)
        out[i:i + nd] = 1 - (1 - s) * (1 - np.exp(-curve * x)) / (1 - math.exp(-curve)); i += nd
    if ns > 0:
        out[i:i + ns] = s; i += ns
    if nr > 0:
        x = np.linspace(0, 1, min(nr, n - i))
        out[i:i + len(x)] = s * np.exp(-curve * x)
    return out[:n]


def exp_env(dur, k=8.0, sr=SR):
    t = t_axis(dur, sr)
    return np.exp(-k * t)


def noise(dur, sr=SR, seed=None):
    rng = np.random.default_rng(seed)
    return rng.uniform(-1, 1, int(dur * sr))


def fft_filter(x, lo=None, hi=None, sr=SR, slope=2.0, peak=None, q=4.0):
    """Frekans alanında süzgeç: lo altını, hi üstünü yumuşakça keser; peak varsa rezonans ekler."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / sr) + 1e-6
    g = np.ones_like(f)
    if lo:
        g *= 1 / (1 + (lo / f) ** (2 * slope))
    if hi:
        g *= 1 / (1 + (f / hi) ** (2 * slope))
    if peak:
        g *= 1 + 3.0 / (1 + ((f - peak) / (peak / q)) ** 2)
    return np.fft.irfft(X * g, n)


def sine(freq, dur, sr=SR, phase=0.0):
    return np.sin(2 * np.pi * freq * t_axis(dur, sr) + phase)


def sweep(f0, f1, dur, sr=SR, curve=1.0, wave='sine'):
    """Frekansı f0'dan f1'e kayan ton (üstel)."""
    t = t_axis(dur, sr)
    k = (t / dur) ** curve
    f = f0 * (f1 / f0) ** k
    ph = 2 * np.pi * np.cumsum(f) / sr
    if wave == 'saw':
        return 2 * ((ph / (2 * np.pi)) % 1.0) - 1
    if wave == 'square':
        return np.sign(np.sin(ph))
    if wave == 'tri':
        return 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1.0) - 1) - 1
    return np.sin(ph)


def pluck(freq, dur, sr=SR, bright=0.5, decay=0.996, seed=None):
    """Karplus-Strong: kopuz / saz tınısı. Blok blok vektörel; bright: başlangıç gürültü parlaklığı."""
    N = max(2, int(sr / freq))
    n = int(dur * sr)
    rng = np.random.default_rng(seed)
    buf = rng.uniform(-1, 1, N)
    buf = fft_filter(buf, hi=1500 + 6000 * bright, sr=sr, slope=1.0)
    out = np.zeros(n + N)
    out[:N] = buf
    i = N
    while i < n:
        prev = out[i - N:i]
        prev2 = np.concatenate(([out[i - N - 1]], prev[:-1]))
        blk = decay * 0.5 * (prev + prev2)
        m = min(N, n - i)
        out[i:i + m] = blk[:m]
        i += m
    return out[:n]


def reverb(x, dur_ir=1.2, mix=0.25, sr=SR, lp=4000, seed=7):
    """Üstel sönümlü gürültü IR ile FFT evrişimi."""
    ir = noise(dur_ir, sr, seed) * np.exp(-5.0 * t_axis(dur_ir, sr))
    ir = fft_filter(ir, hi=lp, sr=sr, slope=1.0)
    ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
    n = len(x) + len(ir) - 1
    y = np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(ir, n), n)
    out = np.zeros(n)
    out[:len(x)] += x
    return out * (1 - mix) + y * mix * 3.0


def delay(x, time_s, fb=0.3, mix=0.3, sr=SR):
    d = int(time_s * sr)
    out = x.copy()
    y = np.zeros(len(x) + d * 6)
    y[:len(x)] = x
    for k in range(1, 6):
        y[k * d:k * d + len(x)] += x * (fb ** k)
    y = y[:len(x)]
    return out * (1 - mix) + y * mix


def distort(x, drive=3.0):
    return np.tanh(x * drive) / math.tanh(drive)


def normalize(x, peak=0.9):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out


def place(dst, src, at_s, gain=1.0, sr=SR):
    i = int(at_s * sr)
    m = min(len(src), len(dst) - i)
    if m > 0:
        dst[i:i + m] += src[:m] * gain


def fade(x, fin=0.005, fout=0.02, sr=SR):
    n = len(x)
    a, b = int(fin * sr), int(fout * sr)
    y = x.copy()
    if a > 0:
        y[:a] *= np.linspace(0, 1, a)
    if b > 0:
        y[-b:] *= np.linspace(1, 0, b)
    return y


def write_wav(path, x, sr=SR, peak=0.9, stereo=None):
    x = normalize(x, peak) if peak else x
    x = np.clip(x, -1, 1)
    if stereo is not None:
        data = np.stack([x, stereo], axis=1).ravel()
        ch = 2
    else:
        data = x
        ch = 1
    pcm = (data * 32767).astype('<i2').tobytes()
    with wave.open(path, 'wb') as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm)
