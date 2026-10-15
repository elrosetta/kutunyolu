"""v11 müzik (sakin ama hareketli; zurna yerine mey/ney, bendir, bağlama arpeji). v10 müzik: türkü/oyun havası karakterinde hareketli parçalar.
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


# ------------------------------------------------------------ v11: yumuşak çalgılar (kulağı yormayan)
def mey(f, dur, sr, seed=0, g=1.0):
    """Mey: zurnanın yumuşak, buğulu kardeşi. Alçak geçiren testere + yavaş atak + geniş vibrato."""
    d = max(0.08, dur)
    t = t_axis(d, sr)
    vib = 1.0 + 0.005 * np.sin(2 * np.pi * 5.0 * t + seed) * np.minimum(1.0, t / 0.25)
    ph = 2 * np.pi * np.cumsum(f * vib) / sr
    saw = 2 * ((ph / (2 * np.pi)) % 1.0) - 1
    x = fft_filter(saw, hi=min(1800.0, f * 5.0), sr=sr, slope=1.6) * 0.8 + np.sin(ph) * 0.35
    breath = bp(noise(d, sr, seed), f, f * 4.0, sr) * 0.06
    e = aenv(d, sr, 0.07, 0.09, 0.82, 0.25)
    return (x + breath) * e * g


def ney(f, dur, sr, seed=0, g=1.0):
    """Ney: nefesli, saf ton; atakta hafif hava 'üfleme'si."""
    d = max(0.1, dur)
    t = t_axis(d, sr)
    vib = 1.0 + 0.004 * np.sin(2 * np.pi * 4.6 * t) * np.minimum(1.0, t / 0.3)
    ph = 2 * np.pi * np.cumsum(f * vib) / sr
    x = np.sin(ph) + 0.1 * np.sin(2 * ph) + 0.04 * np.sin(3 * ph)
    breath = bp(noise(d, sr, seed), f * 0.7, f * 2.5, sr) * (0.18 + 0.25 * np.exp(-t / 0.08))
    e = aenv(d, sr, 0.09, 0.12, 0.8, 0.3)
    return (x + breath) * e * g


def soft_kit(sr):
    """Bendir (derin, yumuşak), parmak tek'i, def zilleri (kısık), yumuşak davul tokmağı."""
    def bendir(g=1.0):
        d = 0.55
        x = sweep(105, 58, d, sr=sr, curve=0.5) * exp_env(d, 8, sr)
        skin = fft_filter(noise(d, sr, 13), hi=500, sr=sr, slope=1.2) * exp_env(d, 22, sr) * 0.35
        return mix(x, skin) * g

    def parmak():
        d = 0.12
        return mix(sine(430, d, sr) * exp_env(d, 40, sr) * 0.4, fft_filter(noise(d, sr, 14), lo=800, hi=3200, sr=sr, slope=1.2) * exp_env(d, 55, sr) * 0.35)

    def def_zil():
        d = 0.2
        return bp(noise(d, sr, 15), 4500, 8000, sr) * exp_env(d, 28, sr) * 0.12

    def tokmak():
        d = 0.5
        x = sweep(85, 45, d, sr=sr, curve=0.45) * exp_env(d, 7, sr)
        return mix(x, fft_filter(noise(d, sr, 16), hi=700, sr=sr, slope=1.2) * exp_env(d, 20, sr) * 0.3) * 0.9

    return {'B': bendir(), 'b': bendir(0.5), 'p': parmak(), 'h': def_zil(), 'G': tokmak(), 'g': tokmak() * 0.5}


def soft_drums(patterns, bars, step, sr, fill=None, swing=0.0):
    kit = soft_kit(sr)
    n_steps = len(next(iter(patterns)))
    total = bars * n_steps * step
    x = np.zeros(int((total + 1.0) * sr))
    rng = np.random.default_rng(9)
    for b in range(bars):
        for pat, g in patterns.items():
            use = fill[pat] if (fill and b % 4 == 3 and pat in fill) else pat
            for i, ch in enumerate(use):
                if ch in kit:
                    t = b * n_steps * step + i * step + (swing * step if i % 2 else 0.0)
                    place(x, kit[ch] * g * (0.85 + 0.25 * rng.random()), t, 1.0, sr)
    return x[:int(total * sr)]


def calm_melody(notes, bar_len):
    """Ezgiyi sakinleştir: üçlü kısa koşuları birleştir (ilk nota uzar), bölümlerin yarısında nefes payı bırak."""
    out = []
    i = 0
    while i < len(notes):
        dg, s0, ln = notes[i]
        j = i + 1
        # aynı grup içindeki 1'lik koşuları tek notaya topla
        while ln <= 1 and j < len(notes) and notes[j][2] <= 1 and notes[j][1] == s0 + ln and ln < 2:
            ln += notes[j][2]
            j += 1
        out.append((dg, s0, ln))
        i = j
    return out


def arp(scale, root, meter, bars, step, sr, seed=0, pattern=(0, 4, 7, 4), g=0.22, bright=0.4, every=1):
    """Bağlama arpeji: sürekli ama alçak sesli akış (hareketi bu taşır, ezgi sakin kalır)."""
    groups, bar_len = groups_of(meter)
    total = bars * bar_len * step
    x = np.zeros(int((total + 1.0) * sr))
    chords = [0, 0, 3, 4, 0, 0, 4, 0]
    k = 0
    for b in range(bars):
        c = chords[b % len(chords)]
        for i in range(0, bar_len, every):
            dg = c + pattern[k % len(pattern)]
            k += 1
            f = midi(deg_to_midi(scale, root, dg))
            acc = 1.0 if any(i == gs for gs, _ in groups) else 0.65
            place(x, saz(f, step * every * 2.2, sr, bright, seed + k * 5, g * acc), (b * bar_len + i) * step, 1.0, sr)
    return fft_filter(x[:int(total * sr)], hi=2800, sr=sr, slope=1.2)


def render_soft(notes, scale, root, step, total, sr, inst, seed=0, ornament=0.15, rng=None, g=0.6, bright=0.55):
    rng = rng or np.random.default_rng(seed)
    x = np.zeros(int((total + 2.0) * sr))
    for k, (dg, s0, ln) in enumerate(notes):
        f = midi(deg_to_midi(scale, root, dg))
        t = s0 * step
        d = ln * step
        if inst == 'saz':
            y = saz_note(f, d, sr, tremolo_step=step if ln >= 4 else 0.0, seed=seed + k * 7, g=g, bright=bright)
        elif inst == 'mey':
            y = mey(f, d * 1.02, sr, seed=seed + k, g=g)
        else:
            y = ney(f, d * 1.02, sr, seed=seed + k, g=g)
        place(x, y, t, 1.0, sr)
        if ln >= 4 and rng.random() < ornament:
            fg = midi(deg_to_midi(scale, root, dg + 1))
            orn = saz(fg, step * 0.8, sr, bright, seed + k * 11, g * 0.35) if inst == 'saz' else (mey if inst == 'mey' else ney)(fg, step * 0.6, sr, seed + k * 13, g * 0.4)
            place(x, orn, max(0.0, t - step * 0.5), 1.0, sr)
    return x[:int(total * sr)]


# ------------------------------------------------------------ parçalar (v11: sakin ama hareketli)
def track(name, sr):
    rng = np.random.default_rng({'otuken': 11, 'bozkir': 22, 'sahmeran': 33, 'kaf': 44, 'tamu': 55, 'boss': 66, 'baslik': 77}.get(name, 1))
    if name == 'otuken':
        # 9/8 karşılama, ağırca; bağlama ezgi + ney cevabı + arpej; Hicaz (Re)
        meter, step, root, scale, bars = [2, 2, 2, 3], 0.125, 62, HICAZ, 16
        notes, bl = turku_melody(scale, meter, bars, rng, 0, 7)
        notes = calm_melody(notes, bl)
        total = bars * bl * step
        lead = render_soft(notes, scale, root, step, total, sr, 'saz', 101, 0.2, rng, 0.55, 0.5)
        echo = render_soft([(dg, s0 + 1, ln) for dg, s0, ln in notes if ln >= 4], scale, root, step, total, sr, 'ney', 102, 0.0, rng, 0.3)
        ar = arp(scale, root - 12, meter, bars, step, sr, 104, (0, 4, 7, 4, 2, 4), 0.2)
        bs = bass_line(scale, root - 12, meter, bars, step, sr, 103)
        dr = soft_drums({'B...p...B...p..p..': 0.9, '..h...h...h...h...': 0.5}, bars, step, sr, fill={'B...p...B...p..p..': 'B...p.p.B.p.p.B.p.'})
        x = mix(reverb(lead, 1.4, 0.22, sr), reverb(echo, 2.0, 0.4, sr), ar, bs * 0.6, dr * 0.75)
    elif name == 'bozkir':
        # halay yürüyüşü ama mey ile: buğulu ezgi, bağlama arpeji, bendir; Hüseyni (La, alçak)
        meter, step, root, scale, bars = [2, 2, 2, 2], 0.13, 57, HUSEYNI, 16
        notes, bl = turku_melody(scale, meter, bars, rng, 0, 8)
        notes = calm_melody(notes, bl)
        total = bars * bl * step
        lead = render_soft(notes, scale, root + 12, step, total, sr, 'mey', 201, 0.2, rng, 0.45)
        ar = arp(scale, root, meter, bars, step, sr, 202, (0, 4, 2, 4), 0.2)
        bs = bass_line(scale, root - 12, meter, bars, step, sr, 203)
        dr = soft_drums({'G...p.p.G...p...': 0.85, '....h.......h...': 0.5, '..b.......b.....': 0.6}, bars, step, sr, fill={'G...p.p.G...p...': 'G...p.p.G.p.G.p.'}, swing=0.06)
        x = mix(reverb(lead, 1.6, 0.28, sr), ar, bs * 0.65, dr * 0.75)
    elif name == 'sahmeran':
        # 7/8 (3+2+2): bağlama ezgi + ney cevabı, yankılı mağara; Kürdi (La)
        meter, step, root, scale, bars = [3, 2, 2], 0.125, 57, KURDI, 16
        notes, bl = turku_melody(scale, meter, bars, rng, 0, 8)
        notes = calm_melody(notes, bl)
        total = bars * bl * step
        lead = render_soft(notes, scale, root + 12, step, total, sr, 'saz', 301, 0.2, rng, 0.5, 0.45)
        ans = render_soft([(dg + 2, s0 + bl * 2, ln) for dg, s0, ln in notes if (s0 // bl) % 4 == 1 and ln >= 2], scale, root + 12, step, total, sr, 'ney', 302, 0.0, rng, 0.35)
        ar = arp(scale, root - 12, meter, bars, step, sr, 304, (0, 4, 7), 0.18)
        bs = bass_line(scale, root - 12, meter, bars, step, sr, 303)
        dr = soft_drums({'B.pp..b.p.....': 0.85, '......h.....h.': 0.4}, bars, step, sr, fill={'B.pp..b.p.....': 'B.pp..b.p.p.pp'})
        x = mix(reverb(lead, 1.8, 0.32, sr), reverb(ans, 2.2, 0.45, sr), reverb(ar, 1.5, 0.3, sr), bs * 0.6, dr * 0.7)
    elif name == 'kaf':
        # 5/8 (2+3): ney önde, bağlama arpeji, uzak rüzgâr; Uşşak (Mi)
        meter, step, root, scale, bars = [2, 3], 0.12, 64, USSAK, 24
        notes, bl = turku_melody(scale, meter, bars, rng, 0, 8)
        notes = calm_melody(notes, bl)
        total = bars * bl * step
        lead = render_soft(notes, scale, root, step, total, sr, 'ney', 401, 0.2, rng, 0.55)
        ar = arp(scale, root - 12, meter, bars, step, sr, 402, (0, 4, 7, 4, 9), 0.18)
        bs = bass_line(scale, root - 12, meter, bars, step, sr, 403)
        dr = soft_drums({'B...p.p...': 0.8, 'h.........': 0.35}, bars, step, sr, fill={'B...p.p...': 'B...p.p.pp'})
        wind = bp(noise(total, sr, 404), 300, 1800, sr) * 0.03 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * t_axis(total, sr)))
        x = mix(reverb(lead, 1.8, 0.35, sr), ar, bs * 0.6, dr * 0.7, wind)
    elif name == 'tamu':
        # 9/8, karanlık ama yormayan: mey (alçak), bağlama tremolo, derin tokmak; Hicaz (Do)
        meter, step, root, scale, bars = [2, 2, 2, 3], 0.11, 60, HICAZ, 16
        notes, bl = turku_melody(scale, meter, bars, rng, 0, 8)
        notes = calm_melody(notes, bl)
        total = bars * bl * step
        lead = render_soft(notes, scale, root, step, total, sr, 'mey', 501, 0.25, rng, 0.5)
        sz = render_soft(notes[::2], scale, root - 12, step, total, sr, 'saz', 502, 0.0, rng, 0.3, 0.4)
        ar = arp(scale, root - 12, meter, bars, step, sr, 504, (0, 4, 1, 4), 0.18)
        bs = bass_line(scale, root - 12, meter, bars, step, sr, 503)
        dr = soft_drums({'G...p...G...p.p.p.': 0.9, '..b.....b.........': 0.6, '......h.....h.....': 0.4}, bars, step, sr, fill={'G...p...G...p.p.p.': 'G.p.p.G.p.p.G.p.p.'})
        x = mix(reverb(lead, 1.6, 0.3, sr), sz, ar, bs * 0.7, dr * 0.8, dem(root - 12, total, sr, 0.03))
    elif name == 'boss':
        # boss: daha dolu ama sert değil: çift mey (oktav), bağlama tremolo, tokmak + bendir; Hicaz (Re)
        meter, step, root, scale, bars = [2, 2, 2, 2], 0.11, 62, HICAZ, 16
        notes, bl = turku_melody(scale, meter, bars, rng, 0, 8)
        notes = calm_melody(notes, bl)
        total = bars * bl * step
        lead = render_soft(notes, scale, root, step, total, sr, 'mey', 601, 0.3, rng, 0.5)
        lead2 = render_soft(notes, scale, root - 12, step, total, sr, 'mey', 602, 0.0, rng, 0.25)
        sz = render_soft(notes, scale, root, step, total, sr, 'saz', 603, 0.0, rng, 0.3, 0.45)
        ar = arp(scale, root - 12, meter, bars, step, sr, 605, (0, 4, 7, 4), 0.2)
        bs = bass_line(scale, root - 12, meter, bars, step, sr, 604)
        dr = soft_drums({'G...p.p.G...p.G.': 1.0, 'b.......b.......': 0.6, '....h.......h...': 0.45}, bars, step, sr, fill={'G...p.p.G...p.G.': 'G.p.G.p.G.p.G.G.'})
        x = mix(reverb(lead, 1.4, 0.25, sr), lead2, sz, ar, bs * 0.75, dr * 0.85)
    else:  # başlık: uzun hava; ney + bağlama, çok hafif bendir
        meter, step, root, scale, bars = [2, 2, 2, 3], 0.17, 62, HICAZ, 8
        notes, bl = turku_melody(scale, meter, bars, rng, 0, 7)
        notes = calm_melody(notes, bl)
        total = bars * bl * step
        lead = render_soft(notes, scale, root, step, total, sr, 'ney', 701, 0.3, rng, 0.55)
        sz = render_soft(notes[::2], scale, root - 12, step, total, sr, 'saz', 702, 0.15, rng, 0.35, 0.4)
        dr = soft_drums({'b.........p.....p.': 0.5}, bars, step, sr)
        x = mix(reverb(lead, 2.4, 0.4, sr), sz, dr)
    # mastering: yumuşak tavan, tizleri törpüle (kulak yormasın)
    x = fft_filter(x, lo=45, hi=6500, sr=sr, slope=1.3)
    rms = np.sqrt(np.mean(x ** 2)) + 1e-9
    x = np.tanh(x / (rms * 4.5))  # ortalamaya göre: tepe vuruşlar yumuşakça kırpılır, ezgi öne çıkar
    return loopify(x, sr)
