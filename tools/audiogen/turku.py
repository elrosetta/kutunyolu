"""v10 müzik: türkü/oyun havası karakterinde hareketli parçalar.
Çalgılar (sentez): bağlama (çift telli tel + oktav teli, tezene tremolosu), zurna (testere dalga + formant + dem),
kaval (nefesli sinüs), davul (tokmak "güm" + çubuk "tek"), darbuka (düm / tek / ka). Usuller: 9/8 karşılama (2+2+2+3),
7/8 (3+2+2), 5/8 (2+3), halay 4/4. Ezgi türkü biçiminde: A A' B A'' (ikinci yarı tiz bölgede), karar sesine iniş, çarpma
süsleri. Tüm parçalar dikişsiz döngü. Kullanım: music.track() bu modülü çağırır."""
import math
import numpy as np
from synth import t_axis, env, exp_env, noise, fft_filter, sine, sweep, pluck, reverb, delay, distort, mix, place

HICAZ = [0, 1, 4, 5, 7, 8, 10]
HUSEYNI = [0, 2, 3, 5, 7, 9, 10]
KURDI = [0, 1, 3, 5, 7, 8, 10]
USSAK = [0, 1.5, 3, 5, 7, 8, 10]  # segâh perdesi yaklaşık (çeyrek ton)


def aenv(d, sr, a=0.01, r=0.04, s=0.85, dk=0.08):
    """Kısa notalarda da güvenli zarf: atak, hafif düşüş, sürme, bırakma (süreye sığdırılır)."""
    n = max(1, int(d * sr))
    t = np.arange(n) / sr
    a = min(a, d * 0.3)
    r = min(r, d * 0.4)
    e = np.where(t < a, t / max(a, 1e-4), s + (1 - s) * np.exp(-(t - a) / max(dk, 1e-3)))
    rel = np.clip((d - t) / max(r, 1e-4), 0, 1)
    return e * rel


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def bp(x, lo, hi, sr):
    return fft_filter(x, lo=lo, hi=hi, sr=sr, slope=1.2)


# ------------------------------------------------------------ çalgılar
def saz(f, dur, sr, bright=0.75, seed=0, g=1.0):
    """Bağlama: iki ince tel (hafif akortsuz) + bir alt oktav teli; tok gövde rezonansı."""
    d = max(0.08, dur)
    a = pluck(f, d, sr, bright=bright, decay=0.9955, seed=seed)
    b = pluck(f * 1.0045, d, sr, bright=bright * 0.9, decay=0.995, seed=seed + 1)
    c = pluck(f * 0.5, d, sr, bright=bright * 0.6, decay=0.996, seed=seed + 2)
    x = a * 0.5 + b * 0.4 + c * 0.3
    body = fft_filter(x, lo=700, hi=2600, sr=sr, slope=1.0) * 0.4
    return (x + body) * g


def saz_note(f, dur, sr, tremolo_step=0.0, seed=0, g=1.0, bright=0.75):
    """Uzun notalar tezeneyle titretilir (hızlı yineleme, söner); kısa notalar tek vuruş."""
    if tremolo_step <= 0 or dur < tremolo_step * 2.5:
        return saz(f, dur * 1.4, sr, bright, seed, g)
    n = int(dur / tremolo_step)
    out = np.zeros(int((dur + 0.4) * sr))
    for k in range(n):
        amp = g * (1.0 if k == 0 else 0.55 + 0.25 * ((k + 1) % 2)) * (1.0 - 0.3 * k / n)
        place(out, saz(f, tremolo_step * 2.2, sr, bright * (1.0 if k % 2 == 0 else 0.8), seed + k * 3, amp), k * tremolo_step, 1.0, sr)
    return out


def zurna(f, dur, sr, seed=0, g=1.0, glide=True):
    """Zurna: parlak testere dalga, kayışla başlar (yarım ton aşağıdan), titreşim, burunsu formantlar."""
    d = max(0.06, dur)
    t = t_axis(d, sr)
    f0 = np.full(len(t), f)
    if glide:
        gl = np.minimum(1.0, t / 0.035)
        f0 = f * (2 ** ((-1.0 + gl) / 12.0))
    vib = 1.0 + 0.007 * np.sin(2 * np.pi * 6.2 * t + seed) * np.minimum(1.0, t / 0.15)
    ph = 2 * np.pi * np.cumsum(f0 * vib) / sr
    saw = 2 * ((ph / (2 * np.pi)) % 1.0) - 1
    x = sum(bp(saw, fc * 0.7, fc * 1.3, sr) * gain for fc, gain in ((900, 1.0), (1700, 0.8), (3000, 0.45)))
    x = x + saw * 0.15
    x = distort(x * 1.6, 1.8)
    br = bp(noise(d, sr, seed), 2000, 6000, sr) * 0.05
    e = aenv(d, sr, 0.012, 0.03, 0.85, 0.06)
    return (x + br) * e * g


def kaval(f, dur, sr, seed=0, g=1.0):
    d = max(0.08, dur)
    t = t_axis(d, sr)
    vib = 1.0 + 0.006 * np.sin(2 * np.pi * 5.0 * t) * np.minimum(1.0, t / 0.2)
    ph = 2 * np.pi * np.cumsum(f * vib) / sr
    x = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    breath = bp(noise(d, sr, seed), f * 0.8, f * 3.0, sr) * 0.25
    e = aenv(d, sr, 0.04, 0.06, 0.8, 0.1)
    return (x + breath) * e * g


def drum_set(sr):
    def gum():
        d = 0.5
        x = sweep(95, 42, d, sr=sr, curve=0.45) * exp_env(d, 7, sr)
        skin = bp(noise(d, sr, 3), 80, 900, sr) * exp_env(d, 18, sr) * 0.5
        return distort(mix(x, skin) * 1.3, 1.5)

    def gum_soft():
        return gum() * 0.55

    def cubuk():
        d = 0.12
        x = bp(noise(d, sr, 4), 1800, 7000, sr) * exp_env(d, 55, sr)
        return mix(x, sweep(900, 400, d, sr=sr) * exp_env(d, 50, sr) * 0.3)

    def dum():
        d = 0.3
        return mix(sweep(170, 70, d, sr=sr, curve=0.5) * exp_env(d, 14, sr), bp(noise(d, sr, 5), 200, 1200, sr) * exp_env(d, 30, sr) * 0.3)

    def tek():
        d = 0.15
        x = mix(sine(560, d, sr) * exp_env(d, 36, sr) * 0.6, bp(noise(d, sr, 6), 2500, 9000, sr) * exp_env(d, 45, sr))
        return x * 0.8

    def ka():
        d = 0.08
        return bp(noise(d, sr, 7), 3000, 10000, sr) * exp_env(d, 70, sr) * 0.5

    def zil():
        d = 0.35
        x = sum(sine(f, d, sr) * exp_env(d, 10 + i * 3, sr) for i, f in enumerate((3400, 5200, 7100))) * 0.08
        return mix(x, bp(noise(d, sr, 8), 6000, 11000, sr) * exp_env(d, 18, sr) * 0.12)

    return {'G': gum(), 'g': gum_soft(), 't': cubuk(), 'D': dum(), 'T': tek(), 'k': ka(), 'z': zil()}


def drums(patterns, bars, step, sr, gains=None, fill=None, swing=0.0):
    """patterns: {çalgı-tuşu-dizisi: kazanç}; her desen 16'lık birimlerde bir ölçü. fill: 4 ölçüde bir son ölçü deseni."""
    kit = drum_set(sr)
    n_steps = len(next(iter(patterns)))
    total = bars * n_steps * step
    x = np.zeros(int((total + 1.0) * sr))
    rng = np.random.default_rng(5)
    for b in range(bars):
        for pat, g in patterns.items():
            use = pat
            if fill and b % 4 == 3 and pat in fill:
                use = fill[pat]
            for i, ch in enumerate(use):
                if ch in kit:
                    t = b * n_steps * step + i * step + (swing * step if i % 2 else 0.0)
                    place(x, kit[ch] * g * (0.9 + 0.2 * rng.random()), t, 1.0, sr)
    return x[:int(total * sr)]


# ------------------------------------------------------------ ezgi
def groups_of(meter):
    """Usul grupları (16'lık birim): [2,2,2,3] -> grup başlangıçları ve uzunlukları"""
    out = []
    pos = 0
    for gsz in meter:
        out.append((pos, gsz * 2))
        pos += gsz * 2
    return out, pos


def turku_melody(scale, meter, bars, rng, low=0, high=9, kar=0):
    """Türkü ezgisi: notalar (derece, başlangıç-16'lık, uzunluk-16'lık). A A' B A'' — her bölüm 4 ölçü (16 ölçüde 4 bölüm).
    Grup başında uzun, ara yerlerde kısa notalar; çoğunlukla adım adım; bölüm sonları karar sesine (0) iner."""
    groups, bar_len = groups_of(meter)

    def motif(start_deg, up):
        notes = []
        deg = start_deg
        for gs, gl in groups:
            r = rng.random()
            if r < 0.35 or gl <= 2:
                notes.append((deg, gs, gl))
            elif r < 0.75:
                notes.append((deg, gs, gl // 2))
                deg = int(np.clip(deg + rng.choice([-1, 1, 1, 2]) * (1 if up else -1), low, high))
                notes.append((deg, gs + gl // 2, gl - gl // 2))
            else:
                q = max(1, gl // 3)
                for k in range(3 if gl >= 3 else 2):
                    notes.append((deg, gs + k * q, q if k < 2 else gl - 2 * q))
                    deg = int(np.clip(deg + rng.choice([-1, 1]), low, high))
            deg = int(np.clip(deg + rng.choice([-1, 0, 1, 1, -2]) * (1 if up else -1), low, high))
        return notes, deg

    def cadence(from_deg):
        # karar: dereceler aşağı adım adım 0'a
        notes = []
        path = list(range(min(from_deg, 4), -1, -1))
        if len(path) < 2:
            path = [2, 1, 0]
        per = max(1, bar_len // len(path))
        for k, dg in enumerate(path):
            ln = per if k < len(path) - 1 else bar_len - per * (len(path) - 1)
            notes.append((dg + kar, k * per, ln))
        return notes

    sections = []
    m1, d1 = motif(low + 2, True)
    m2, d2 = motif(d1, False)
    m3, d3 = motif(low + 4, True)
    for sec in range(max(1, bars // 4)):
        part = []
        if sec % 4 in (0, 1, 3):
            base = [m1, m2, m1 if sec % 4 != 1 else motif(d2, True)[0]]
        else:
            hi_a, dh = motif(low + 5, True)
            hi_b, _ = motif(dh, False)
            base = [hi_a, hi_b, m3]
        for bi, mm in enumerate(base):
            part.append([(dg, s0 + bi * bar_len, ln) for dg, s0, ln in mm])
        part.append([(dg, s0 + 3 * bar_len, ln) for dg, s0, ln in cadence(d2 if sec % 2 == 0 else d3)])
        flat = [n for p in part for n in p]
        sections.append([(dg, s0 + sec * 4 * bar_len, ln) for dg, s0, ln in flat])
    return [n for s in sections for n in s], bar_len


def deg_to_midi(scale, root, dg):
    o, i = divmod(int(dg), 7)
    return root + 12 * o + scale[i]


def render_line(notes, scale, root, step, total, sr, inst, seed=0, ornament=0.25, rng=None, **kw):
    rng = rng or np.random.default_rng(seed)
    x = np.zeros(int((total + 1.5) * sr))
    for k, (dg, s0, ln) in enumerate(notes):
        m = deg_to_midi(scale, root, dg)
        f = midi(m)
        t = s0 * step
        d = ln * step
        if inst == 'saz':
            y = saz_note(f, d, sr, tremolo_step=step if ln >= 3 else 0.0, seed=seed + k * 7, g=0.6)
        elif inst == 'zurna':
            y = zurna(f, d * 0.95, sr, seed=seed + k, g=0.5)
        else:
            y = kaval(f, d * 0.95, sr, seed=seed + k, g=0.6)
        place(x, y, t, 1.0, sr)
        # çarpma (süs): uzun notadan önce üst komşudan kısa vuruş
        if ln >= 3 and rng.random() < ornament:
            fg = midi(deg_to_midi(scale, root, dg + 1))
            if inst == 'saz':
                g = saz(fg, step * 0.8, sr, 0.8, seed + k * 11, 0.3)
            elif inst == 'zurna':
                g = zurna(fg, step * 0.5, sr, seed + k * 13, 0.35, glide=False)
            else:
                g = kaval(fg, step * 0.5, sr, seed + k * 13, 0.35)
            place(x, g, max(0.0, t - step * 0.45), 1.0, sr)
    return x[:int(total * sr)]


def bass_line(scale, root, meter, bars, step, sr, seed=0):
    """Bağlama alt teli: grup başlarında kök / beşli / dördüncü; ölçünün son grubunda yürüyüş"""
    groups, bar_len = groups_of(meter)
    rng = np.random.default_rng(seed)
    total = bars * bar_len * step
    x = np.zeros(int((total + 1.0) * sr))
    seq = [0, 0, 4, 3, 0, 0, 4, 0]
    for b in range(bars):
        for gi, (gs, gl) in enumerate(groups):
            dg = seq[(b + gi) % len(seq)] if gi < len(groups) - 1 else int(rng.choice([0, 1, 4, 3]))
            f = midi(root - 12 + scale[dg])
            place(x, saz(f, gl * step * 1.1, sr, 0.35, seed + b * 9 + gi, 0.55), (b * bar_len + gs) * step, 1.0, sr)
    return fft_filter(x[:int(total * sr)], hi=1500, sr=sr, slope=1.0)


def dem(root, total, sr, g=0.12):
    """Dem: ikinci zurnanın tuttuğu karar sesi (ince, sürekli)"""
    f = midi(root)
    t = t_axis(total, sr)
    ph = 2 * np.pi * f * t
    saw = 2 * ((ph / (2 * np.pi)) % 1.0) - 1
    return bp(saw, 400, 2500, sr) * g * (0.85 + 0.15 * np.sin(2 * np.pi * 0.2 * t))


def loopify(x, sr, xf=0.8):
    n = int(xf * sr)
    y = x[:-n].copy()
    tail = x[-n:]
    w = np.linspace(0, 1, n)
    y[:n] = y[:n] * w + tail * (1 - w)
    return y


# ------------------------------------------------------------ parçalar
def track(name, sr):
    rng = np.random.default_rng({'otuken': 11, 'bozkir': 22, 'sahmeran': 33, 'kaf': 44, 'tamu': 55, 'boss': 66, 'baslik': 77}.get(name, 1))
    if name == 'otuken':
        # 9/8 karşılama, bağlama önde, davul + darbuka; Hicaz (Re)
        meter, step, root, scale, bars = [2, 2, 2, 3], 0.1, 62, HICAZ, 16
        notes, bl = turku_melody(scale, meter, bars, rng, 0, 9)
        total = bars * bl * step
        lead = render_line(notes, scale, root, step, total, sr, 'saz', 101, 0.3, rng)
        echo = render_line([(dg + 7, s0, ln) for dg, s0, ln in notes[::2]], scale, root - 12, step, total, sr, 'kaval', 102, 0.0, rng) * 0.35
        bs = bass_line(scale, root - 12, meter, bars, step, sr, 103)
        dr = drums({'G...g...G...g.t.t.': 1.0, '..t...t...t...t...': 0.5, 'D.k.T.k.D.k.T.k.TkT': 0.0, 'D.kkT.k.D.kkT.kTkT'[:18]: 0.55},
                   bars, step, sr, fill={'G...g...G...g.t.t.': 'G.g.G.g.G.g.G.tGtG'})
        x = mix(lead * 1.0, echo, bs * 0.8, dr * 0.9)
    elif name == 'bozkir':
        # halay: davul-zurna, dem; Hüseyni (La)
        meter, step, root, scale, bars = [2, 2, 2, 2], 0.115, 69, HUSEYNI, 16
        notes, bl = turku_melody(scale, meter, bars, rng, 0, 9)
        total = bars * bl * step
        lead = render_line(notes, scale, root, step, total, sr, 'zurna', 201, 0.35, rng)
        sz = render_line(notes, scale, root - 12, step, total, sr, 'saz', 202, 0.0, rng) * 0.45
        bs = bass_line(scale, root - 12, meter, bars, step, sr, 203)
        dr = drums({'G...t.t.G.t.t.t.': 1.1, 'g.......g.......': 0.6, '....t.......t...': 0.4},
                   bars, step, sr, fill={'G...t.t.G.t.t.t.': 'G.t.G.t.G.tGtGtG'}, swing=0.08)
        x = mix(lead * 0.9, sz, bs * 0.7, dr, dem(root - 12, total, sr, 0.1))
    elif name == 'sahmeran':
        # 7/8 (3+2+2), bağlama + darbuka + kaval cevabı; Kürdi (La), yankılı
        meter, step, root, scale, bars = [3, 2, 2], 0.11, 57, KURDI, 16
        notes, bl = turku_melody(scale, meter, bars, rng, 0, 9)
        total = bars * bl * step
        lead = render_line(notes, scale, root + 12, step, total, sr, 'saz', 301, 0.3, rng)
        ans = render_line([(dg + 2, s0 + bl * 2, ln) for dg, s0, ln in notes if (s0 // bl) % 4 == 1], scale, root + 12, step, total, sr, 'kaval', 302, 0.2, rng) * 0.5
        bs = bass_line(scale, root - 12, meter, bars, step, sr, 303)
        dr = drums({'D.kkT.D.T.kkT.': 0.9, 'g.....g...g...': 0.5}, bars, step, sr, fill={'D.kkT.D.T.kkT.': 'D.kkTkD.TkTkTk'})
        x = mix(reverb(lead, 1.6, 0.3, sr), reverb(ans, 2.0, 0.45, sr), bs * 0.8, dr * 0.85)
    elif name == 'kaf':
        # 5/8 (2+3), kaval önde, bağlama eşlik, rüzgâr; Uşşak benzeri (Mi)
        meter, step, root, scale, bars = [2, 3], 0.1, 64, USSAK, 24
        notes, bl = turku_melody(scale, meter, bars, rng, 0, 9)
        total = bars * bl * step
        lead = render_line(notes, scale, root + 12, step, total, sr, 'kaval', 401, 0.3, rng)
        sz = render_line(notes[::2], scale, root, step, total, sr, 'saz', 402, 0.1, rng) * 0.5
        bs = bass_line(scale, root - 12, meter, bars, step, sr, 403)
        dr = drums({'G.t.G.t.t.': 0.9, 'z.........': 0.5, '..k...k.k.': 0.5}, bars, step, sr, fill={'G.t.G.t.t.': 'G.tGtGtGtG'})
        wind = bp(noise(total, sr, 404), 400, 3000, sr) * 0.04
        x = mix(reverb(lead, 1.4, 0.3, sr), sz, bs * 0.7, dr * 0.85, wind)
    elif name == 'tamu':
        # hızlı 9/8, zurna + bağlama tremolo + bozuk davul; Hicaz (Do)
        meter, step, root, scale, bars = [2, 2, 2, 3], 0.085, 60, HICAZ, 16
        notes, bl = turku_melody(scale, meter, bars, rng, 0, 9)
        total = bars * bl * step
        lead = render_line(notes, scale, root + 12, step, total, sr, 'zurna', 501, 0.4, rng)
        sz = render_line(notes, scale, root, step, total, sr, 'saz', 502, 0.0, rng) * 0.5
        bs = distort(bass_line(scale, root - 12, meter, bars, step, sr, 503), 1.8)
        dr = distort(drums({'G.t.G.t.G.t.G.tGt.': 1.0, 'D.k.T.k.D.k.T.kTkT': 0.6}, bars, step, sr, fill={'G.t.G.t.G.t.G.tGt.': 'GtGtGtGtGtGtGtGtGt'}), 1.4)
        x = mix(lead * 0.85, sz, bs * 0.8, dr, dem(root, total, sr, 0.08))
    elif name == 'boss':
        # ağır halay, iki zurna + bağlama tremolo + çift davul; Hicaz (Re)
        meter, step, root, scale, bars = [2, 2, 2, 2], 0.1, 62, HICAZ, 16
        notes, bl = turku_melody(scale, meter, bars, rng, 0, 9)
        total = bars * bl * step
        lead = render_line(notes, scale, root + 12, step, total, sr, 'zurna', 601, 0.45, rng)
        lead2 = render_line([(dg + 2, s0, ln) for dg, s0, ln in notes], scale, root + 12, step, total, sr, 'zurna', 602, 0.0, rng) * 0.35
        sz = render_line(notes, scale, root, step, total, sr, 'saz', 603, 0.0, rng) * 0.55
        bs = distort(bass_line(scale, root - 12, meter, bars, step, sr, 604), 1.6)
        dr = drums({'G.t.G.ttG.t.GtGt': 1.2, 'g...g...g...g...': 0.6, 'z.......z.......': 0.5}, bars, step, sr, fill={'G.t.G.ttG.t.GtGt': 'GtGtGtGtGGtGGtGG'})
        x = mix(lead * 0.85, lead2, sz, bs * 0.8, dr, dem(root, total, sr, 0.1))
    else:  # başlık: ağır kaval + bağlama, hafif davul (uzun hava havası)
        meter, step, root, scale, bars = [2, 2, 2, 3], 0.16, 62, HICAZ, 8
        notes, bl = turku_melody(scale, meter, bars, rng, 0, 8)
        total = bars * bl * step
        lead = render_line(notes, scale, root + 12, step, total, sr, 'kaval', 701, 0.4, rng)
        sz = render_line(notes[::2], scale, root, step, total, sr, 'saz', 702, 0.2, rng) * 0.5
        dr = drums({'g.........t.....t.': 0.6}, bars, step, sr)
        x = mix(reverb(lead, 2.2, 0.4, sr), sz, dr, dem(root - 12, total, sr, 0.06))
    x = fft_filter(x, lo=40, sr=sr, slope=1.5)
    x = np.tanh(x / (np.max(np.abs(x)) + 1e-9) * 1.5) / math.tanh(1.5)
    return loopify(x, sr)
