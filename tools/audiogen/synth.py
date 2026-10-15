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


# ------------------------------------------------------------ v9: zamanla değişen süzgeç, ses yolu, mastering
def stft_shape(x, fn, sr=SR, n=1024, hop=256):
    """Zamanla değişen süzgeç: kısa süreli Fourier; fn(t (kare,1), f (1,kutu)) -> kazanç dizisi. Hann pencere, 4x örtüşme."""
    if len(x) < n:
        x = np.concatenate((x, np.zeros(n - len(x))))
    L = len(x)
    pad = np.concatenate((np.zeros(n), x, np.zeros(n + hop)))
    w = np.hanning(n + 1)[:-1]
    idx = np.arange(0, len(pad) - n, hop)
    frames = np.stack([pad[i:i + n] * w for i in idx])
    F = np.fft.rfft(frames, axis=1)
    tt = ((idx - n + n / 2) / sr)[:, None]
    ff = np.fft.rfftfreq(n, 1 / sr)[None, :] + 1e-6
    F *= fn(tt, ff)
    y = np.fft.irfft(F, n, axis=1) * w
    out = np.zeros(len(pad))
    norm = np.zeros(len(pad))
    for k, i in enumerate(idx):
        out[i:i + n] += y[k]
        norm[i:i + n] += w * w
    out /= np.maximum(norm, 1e-3)
    return out[n:n + L]


def curve(points, dur, sr=SR):
    """[(zaman, değer), ...] noktalarından doğrusal eğri (örnek başına)."""
    t = t_axis(dur, sr)
    ts = [p[0] for p in points]
    vs = [p[1] for p in points]
    return np.interp(t, ts, vs)


def resonance(f, fc, bw):
    return 1.0 / (1.0 + ((f - fc) / (bw * 0.5)) ** 2)


VOWELS = {  # erkek sesi biçimlendiricileri (Hz): F1, F2, F3
    'a': (730, 1090, 2440), 'o': (570, 840, 2410), 'u': (300, 870, 2240),
    'i': (270, 2290, 3010), 'e': (530, 1840, 2480), 'ı': (350, 1350, 2500),
}


def voice(f0, dur, vowels=('a',), size=1.0, breath=0.15, grit=0.0, jitter=0.02, sr=SR, seed=0, sub=0.0):
    """Biçimlendirici sentezli ses: f0 sayı ya da örnek eğrisi; vowels zamana yayılan ünlü dizisi; size>1 iri gövde
    (biçimlendiriciler aşağı kayar); breath hırıltı gürültüsü; grit gırtlak bozulması; sub alt oktav (iri yaratıklar)."""
    n = int(dur * sr)
    rng = np.random.default_rng(seed)
    f = np.full(n, float(f0)) if np.isscalar(f0) else np.asarray(f0, float)[:n]
    jit = fft_filter(rng.standard_normal(n), hi=30, sr=sr, slope=1.0)
    jit /= np.max(np.abs(jit)) + 1e-9
    f = f * (1 + jitter * jit)
    ph = np.cumsum(f) / sr
    saw = 2 * (ph % 1.0) - 1
    src = saw + 0.35 * np.sign(np.sin(2 * np.pi * ph))
    if sub:
        src += sub * (2 * ((ph * 0.5) % 1.0) - 1)
    nz = rng.uniform(-1, 1, n)
    src = src * (1 - breath) + nz * breath * (0.6 + 0.4 * (np.sin(2 * np.pi * ph) > 0))
    if grit:
        src = np.tanh(src * (1 + grit)) * (1 + 0.5 * grit * fft_filter(rng.uniform(-1, 1, n), hi=60, sr=sr))
    fm = np.array([VOWELS[v] for v in vowels], float) / size
    tv = np.linspace(0, dur, len(vowels))

    def g(tt, ff):
        tt = np.clip(tt, 0, dur)
        out = np.zeros((tt.shape[0], ff.shape[1]))
        for k in range(3):
            fc = np.interp(tt[:, 0], tv, fm[:, k])[:, None]
            out += resonance(ff, fc, 80 + 0.08 * fc) * (1.0, 0.7, 0.35)[k]
        return out + 0.02
    return stft_shape(src, g, sr)


def hp(x, f=30, sr=SR):
    return fft_filter(x, lo=f, sr=sr, slope=1.5)


def lp(x, f, sr=SR):
    return fft_filter(x, hi=f, sr=sr, slope=1.5)


def bp(x, lo, hi, sr=SR):
    return fft_filter(x, lo=lo, hi=hi, sr=sr, slope=1.5)


def loudness(x, sr=SR, win=0.05):
    """Algılanan yükseklik kestirimi: 80 Hz altı kesilmiş, 50 ms'lik pencerelerin en yüksek RMS'i (dBFS)."""
    y = fft_filter(x, lo=80, sr=sr, slope=1.0)
    y = fft_filter(y, lo=1500, sr=sr, slope=0.5) * 0.4 + y * 0.8  # tiz bölgeye hafif ağırlık (K-ağırlığı benzeri)
    w = max(1, int(win * sr))
    if len(y) < w:
        return 20 * math.log10(np.sqrt(np.mean(y ** 2)) + 1e-9)
    c = np.cumsum(np.concatenate(([0.0], y ** 2)))
    r = np.sqrt((c[w:] - c[:-w]) / w)
    return 20 * math.log10(np.max(r) + 1e-9)


def soft_limit(x, ceiling=0.89, knee=0.7):
    """Tepe sınırlayıcı: knee*ceiling üstünü tanh ile yumuşakça ceiling'e bükler (kırpma yok)."""
    k = knee * ceiling
    a = np.abs(x)
    over = a > k
    y = x.copy()
    r = ceiling - k
    y[over] = np.sign(x[over]) * (k + r * np.tanh((a[over] - k) / r))
    return y


def master(x, target_db=-12.0, ceiling=0.89, sr=SR, loop=False):
    """Seviye eşitleme: DC/infrases temizliği, hedef yükseklik, yumuşak tepe sınırlama, uçlarda kısa yumuşatma."""
    x = np.asarray(x, float)
    x = x - np.mean(x)
    x = fft_filter(x, lo=35, sr=sr, slope=2.0)  # 35 Hz altı hoparlörde duyulmaz, yalnızca pay yer
    g = 10 ** ((target_db - loudness(x, sr)) / 20)
    pk = np.max(np.abs(x)) * g + 1e-9
    if pk > ceiling * 2.0:  # en fazla ~6 dB yumuşak sınırlama (vuruşa 'yumruk' katar, geçişleri ezmez)
        g *= ceiling * 2.0 / pk
    x = soft_limit(x * g, ceiling)
    if not loop:
        x = trim_tail(x, sr=sr)
        x = x - np.mean(x)  # sınırlayıcının bükümünden kalan DC
        x = fade(x, 0.001, min(0.01, len(x) / sr * 0.2), sr)
    return x


def trim_tail(x, db=-58.0, sr=SR, keep=0.02):
    """Sondaki duyulmaz yankı kuyruğunu kes (tepeye göre db altı)."""
    th = np.max(np.abs(x)) * 10 ** (db / 20)
    idx = np.nonzero(np.abs(x) > th)[0]
    if len(idx) == 0:
        return x
    end = min(len(x), idx[-1] + int(keep * sr))
    return x[:end]
