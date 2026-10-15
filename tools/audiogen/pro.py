"""v9 ses katmanı: her vuruş üç katmandan kurulur — geçiş (tık/çatırtı, tizde netlik), gövde (kayıt + perdesi düşen
alt ton, ağır silahta daha çok bas) ve kuyruk (ıslak/moloz/oda). Yaratık sesleri gerçek kayıtlar + biçimlendirici
(formant) sentezli seslerle; yeni arayüz sesleri yumuşak tahta/metal tıkırtı + kopuz teli. Tüm diziler mono, 44.1 kHz.
Yükseklik eşitlemesi export_audio.py içinde (synth.master) kategori hedefleriyle yapılır.
Yeniden üretim: python tools/audiogen/export_audio.py"""
import os
import sys
import math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import (SR, t_axis, env, exp_env, noise, fft_filter, sine, sweep, pluck, reverb, distort, mix, place, fade,
                   stft_shape, curve, resonance, voice, hp, lp, bp)
from layer import load, pitch, trim, tight, sub, ring, shimmer, build, SW, RP, KR, KI
import sfx as SY

RNG_BASE = 9000


# ------------------------------------------------------------ yapı taşları
def click(dur=0.012, lo=2500, hi=12000, seed=1, k=None):
    """Geçiş katmanı: çok kısa parlak çıtırtı (vuruşun 'netliği')."""
    k = k or 5.0 / dur
    return bp(noise(dur + 0.01, seed=seed), lo, hi)[:int(dur * SR)] * exp_env(dur, k)


def thump(f0=140, f1=45, dur=0.3, k=12, drive=1.5):
    """Gövde katmanı: perdesi hızla düşen alt ton, hafif doyurulmuş (göğüste hissedilen 'güm')."""
    x = sweep(f0, max(f1, 32), dur, curve=0.35) * exp_env(dur, k)
    return distort(x, drive) * 0.8 if drive > 1 else x


def tail(dur=0.3, lo=200, hi=2500, k=12, seed=2):
    return bp(noise(dur, seed=seed), lo, hi) * exp_env(dur, k)


def whoosh(dur=0.3, f_lo=400, f_hi=4000, peak=0.45, seed=3, q=1.2, k_up=2.0):
    """Doppler hissi veren savuruş: bant merkezi tepe anına kadar yükselip düşer; genlik tepe anında doruk."""
    n = noise(dur, seed=seed)
    tp = peak * dur

    def g(tt, ff):
        tt = np.clip(tt, 0, dur)
        u = tt / dur
        pos = np.where(tt < tp, (tt / tp) ** k_up, np.exp(-(tt - tp) / (dur - tp + 1e-3) * 2.2))
        fc = f_lo * (f_hi / f_lo) ** np.clip(pos, 0, 1)
        bw = fc * q
        return resonance(ff, fc, bw) * (0.02 + pos) * (1 - u ** 4)
    return stft_shape(n, g)


def metal_ring(f0=2600, dur=0.35, k=14, parts=(1.0, 1.52, 2.33, 3.01), seed=0):
    """Çelik çınlaması (inharmonik kısmi tonlar)."""
    rng = np.random.default_rng(seed)
    x = np.zeros(int(dur * SR))
    for i, p in enumerate(parts):
        f = f0 * p * (1 + rng.uniform(-0.01, 0.01))
        x += sine(f, dur, phase=rng.uniform(0, 6.28)) * exp_env(dur, k * (1 + 0.5 * i)) / (1 + i)
    return x


def room(x, size=0.5, wet=0.2, lpf=5000, seed=7):
    return reverb(x, 0.25 + size, wet, lp=lpf, seed=seed)


def gated(x, starts, durs, a=0.004):
    """Hece kapısı: x'i verilen başlangıç/süre aralıklarında açar (gülme, fısıltı heceleri)."""
    g = np.zeros(len(x))
    for s, d in zip(starts, durs):
        i, n = int(s * SR), int(d * SR)
        e = env(d, a=a, d=d - a - 0.01, s=0.0, r=0.01, curve=2.5)
        m = min(n, len(g) - i)
        if m > 0:
            g[i:i + m] = np.maximum(g[i:i + m], e[:m])
    return x * g


def rumble(dur=0.8, hi=180, k=4, seed=11):
    return lp(noise(dur, seed=seed), hi) * exp_env(dur, k) * 3.0


def debris(dur=0.6, n=14, seed=12, lo=1500, hi=7000, spread=1.0):
    """Moloz: rastgele küçük taş tıkırtıları (zamanla seyrelir)."""
    rng = np.random.default_rng(seed)
    x = np.zeros(int(dur * SR))
    for _ in range(n):
        t = (rng.random() ** 1.8) * dur * spread * 0.85
        d = rng.uniform(0.01, 0.03)
        c = bp(noise(d + 0.01, seed=int(rng.integers(1e6))), lo * rng.uniform(0.6, 1.4), hi)[:int(d * SR)] * exp_env(d, 160)
        place(x, c, t, rng.uniform(0.2, 1.0) * (1 - t / dur * 0.7))
    return x


def grind(dur=0.6, lo=150, hi=1800, rate=38, seed=13):
    """Taş sürtünmesi: düşük bant gürültü, düzensiz tanecikli genlik."""
    rng = np.random.default_rng(seed)
    x = bp(noise(dur, seed=seed), lo, hi)
    m = np.abs(lp(rng.standard_normal(int(dur * SR)), rate)) * 6
    return x * np.clip(m, 0, 1.5) * env(dur, a=0.08, d=dur - 0.16, s=0.0, r=0.08, curve=1.5)


def crackle(dur=0.6, n=40, seed=14, lo=1200, hi=8000):
    """Tahta çatırtısı / ateş çıtırtısı."""
    return debris(dur, n, seed, lo, hi)


def kopuz(freq, dur=0.6, bright=0.6, g=1.0, seed=0, decay=0.996):
    """Kopuz teli: Karplus-Strong + gövde rezonansı."""
    x = pluck(freq, dur, bright=bright, decay=decay, seed=seed)
    body = fft_filter(x, lo=150, hi=2500, peak=freq * 2 if freq * 2 < 2000 else 900, q=3)
    return fade((x * 0.7 + body * 0.5) * g, 0.001, 0.03)


def note(name):
    """'A4' gibi nota adından frekans (Hüseyni dizisinde kalmak için kolaylık)."""
    names = {'C': -9, 'C#': -8, 'D': -7, 'D#': -6, 'E': -5, 'F': -4, 'F#': -3, 'G': -2, 'G#': -1, 'A': 0, 'A#': 1, 'B': 2}
    o = int(name[-1])
    return 440.0 * 2 ** ((names[name[:-1]] + 12 * (o - 4)) / 12)


def bell(freq, dur=1.0, k=4.0, g=1.0):
    parts = (1.0, 2.0, 2.76, 4.07, 5.4)
    return sum(sine(freq * p, dur) * exp_env(dur, k * (1 + 0.6 * i)) / (1 + i * 0.8) for i, p in enumerate(parts)) * g


def soul_release(dur=0.7, seed=15):
    """Ruh salınımı: ölümlerde gövde düşüşünün üstünde yükselen hafif hava + ince ton (tüm düşmanlarda ortak imza)."""
    air = whoosh(dur, 900, 7000, 0.3, seed=seed, q=0.8)
    tone = sweep(500, 1400, dur, curve=0.7) * env(dur, a=0.05, d=dur - 0.1, r=0.05, curve=3) * 0.12
    return room(mix(air * 0.5, tone), 0.6, 0.35)


# ------------------------------------------------------------ savuruşlar
def swings():
    out = {}
    # kılıç: kayıt + parlak bant savuruşu + ince çelik "şiing"
    for i, (k, f) in enumerate(((3, 1.0), (5, 1.06), (8, 1.03), (11, 1.1))):
        body = trim(pitch(SW[k](), f), 0, 0.3)
        out['savur_kilic_%d' % (i + 1)] = build([(body, 0.0, 0.85), (whoosh(0.24, 1200, 9500, 0.45, seed=100 + i), 0.0, 0.85),
                                                 (metal_ring(3200 + 250 * i, 0.22, 22, seed=i), 0.05, 0.035), (click(0.008, 5000, 14000, 105 + i), 0.09, 0.15)])
    # katana: kından çekiş + çok hızlı, parlak savuruş + uzun ince çınlama
    for i, (u, k) in enumerate(((2, 6), (4, 9), (5, 13))):
        out['savur_katana_%d' % (i + 1)] = build([(trim(RP('battle/sword-unsheathe%d.wav' % u), 0, 0.3), 0.0, 0.45), (trim(pitch(SW[k](), 1.25), 0, 0.22), 0.05, 0.85),
                                                  (whoosh(0.18, 1500, 10000, 0.4, seed=110 + i), 0.05, 0.5), (metal_ring(4100, 0.4, 9, seed=10 + i), 0.08, 0.04)])
    # dev kılıç / tırpan: kalın hava, bas savuruş ve alt nabız
    wh = load('whoosh2_0.wav')
    for i, (k, f) in enumerate(((1, 0.62), (7, 0.68), (10, 0.6))):
        out['savur_dev_%d' % (i + 1)] = build([(trim(pitch(SW[k](), f), 0, 0.55), 0.0, 0.8), (trim(pitch(wh[int(0.9 * SR):int(1.7 * SR)], 0.7 + 0.04 * i), 0, 0.5), 0.0, 0.3),
                                               (whoosh(0.5, 90, 900, 0.5, seed=120 + i, q=1.0), 0.0, 1.0), (sub(52 - 3 * i, 0.4, 8, 0.45), 0.2, 1.0),
                                               (metal_ring(1700, 0.35, 10, seed=20 + i), 0.25, 0.025)])
    # çekiç / gürz: ağır hava + kumaş + bas (çelik çınlaması yok)
    for i, (k, f) in enumerate(((2, 0.72), (10, 0.78), (6, 0.7))):
        out['savur_cekic_%d' % (i + 1)] = build([(trim(pitch(wh[int(1.0 * SR):int(1.8 * SR)], 0.75), 0, 0.5), 0.0, 0.4), (trim(pitch(SW[k](), f), 0, 0.45), 0.02, 0.7),
                                                 (trim(RP('inventory/cloth-heavy.wav'), 0, 0.25), 0.0, 0.3), (whoosh(0.46, 70, 600, 0.55, seed=130 + i, q=0.9), 0.0, 1.1),
                                                 (sub(46, 0.45, 7, 0.5), 0.2, 1.0)])
    # balta / teber: kalın savuruş + orta bant + sap gıcırtısı
    for i, (s, k) in enumerate(((2, 4), (3, 12), (1, 7))):
        out['savur_balta_%d' % (i + 1)] = build([(pitch(RP('battle/swing%s.wav' % ('' if s == 1 else s)), 0.85), 0.0, 0.7), (trim(pitch(SW[k](), 0.92), 0, 0.35), 0.02, 0.6),
                                                 (whoosh(0.36, 250, 3000, 0.5, seed=140 + i), 0.0, 0.7), (sub(60, 0.3, 10, 0.3), 0.15, 1.0)])
    # sırık / saplama: çok hızlı ince "fşt"
    for i, (k, f) in enumerate(((6, 1.35), (13, 1.3), (9, 1.4))):
        out['savur_sirik_%d' % (i + 1)] = build([(trim(pitch(SW[k](), f), 0, 0.2), 0.0, 0.85), (trim(pitch(RP('battle/swing3.wav'), 1.15), 0, 0.15), 0.0, 0.35),
                                                 (whoosh(0.16, 700, 6000, 0.35, seed=150 + i, k_up=1.0), 0.0, 0.6)])
    # bıçak / pençe: kısa, çok tiz
    for i, (k, f) in enumerate(((9, 1.5), (3, 1.42), (12, 1.55), (5, 1.6))):
        out['savur_bicak_%d' % (i + 1)] = build([(trim(pitch(SW[k](), f), 0, 0.18), 0.0, 0.85), (trim(KR('drawKnife3.ogg'), 0.05, 0.15), 0.0, 0.3),
                                                 (whoosh(0.13, 2000, 11000, 0.4, seed=160 + i), 0.0, 0.45)])
    # kırbaç: savuruş + uçta şaklama
    for i, (k, p) in enumerate(((5, 'impactPlate_light_000.ogg'), (8, 'impactPlate_light_002.ogg'), (11, 'impactPlate_light_003.ogg'))):
        crack = mix(click(0.006, 3000, 15000, 170 + i) * 1.5, tail(0.08, 2500, 9000, 70, 175 + i) * 0.6)
        out['savur_kirbac_%d' % (i + 1)] = build([(trim(pitch(SW[k](), 1.2), 0, 0.3), 0.0, 0.7), (trim(pitch(KI(p), 1.7), 0, 0.12), 0.13, 0.5), (crack, 0.13, 0.9)])
    # ruh kılıcı: savuruş + ışıltı + hayalet tonu
    for i, k in enumerate((4, 11, 2)):
        ghost = sweep(700 + 80 * i, 1200, 0.35) * env(0.35, a=0.05, d=0.25, r=0.05) * 0.1
        out['savur_ruh_%d' % (i + 1)] = build([(trim(pitch(SW[k](), 1.0), 0, 0.3), 0.0, 0.75), (shimmer(0.4, 0.13), 0.03, 1.0), (room(ghost, 0.6, 0.4), 0.02, 1.0),
                                               (whoosh(0.26, 600, 6000, 0.45, seed=180 + i), 0.0, 0.4)])
    # eski genel adlar (geri uyumluluk)
    for a, b in (('savur_hafif_1', 'savur_kilic_1'), ('savur_hafif_2', 'savur_kilic_2'), ('savur_hafif_3', 'savur_kilic_3'),
                 ('savur_agir_1', 'savur_cekic_1'), ('savur_agir_2', 'savur_dev_1'), ('savur_dev', 'savur_dev_2'), ('sapla', 'savur_sirik_1')):
        out[a] = out[b]
    return out


# ------------------------------------------------------------ darbeler
def wet(i, g=1.0):
    """Islak et katmanı (kesik/delik)."""
    return mix(tail(0.18, 300, 1800, 22, 200 + i), bp(noise(0.08, seed=210 + i), 1500, 5000) * exp_env(0.08, 45) * 0.5) * g


def hits():
    out = {}
    # kesik (kılıç): parlak dilim + yumuşak gövde + alt ton + ıslak kuyruk
    for i, (ks, f, sm) in enumerate((('knifeSlice.ogg', 1.0, 'impactSoft_medium_000.ogg'), ('knifeSlice2.ogg', 1.08, 'impactSoft_medium_002.ogg'),
                                     ('knifeSlice.ogg', 1.15, 'impactSoft_medium_003.ogg'), ('knifeSlice2.ogg', 0.95, 'impactSoft_medium_004.ogg'))):
        out['darbe_kesik_%d' % (i + 1)] = build([(click(0.01, 3000, 14000, 220 + i), 0.0, 0.7), (trim(pitch(KR(ks), f), 0, 0.28), 0.0, 0.9),
                                                 (trim(KI(sm), 0, 0.25), 0.0, 0.7), (thump(150 - 10 * i, 55, 0.22, 16), 0.0, 0.35), (wet(i), 0.01, 0.7)])
    # ağır kesik (dev kılıç): kalın dilim + ağır gövde + bol bas + oda
    for i, (f, sh) in enumerate(((0.8, 'impactSoft_heavy_000.ogg'), (0.74, 'impactSoft_heavy_003.ogg'), (0.7, 'impactSoft_heavy_004.ogg'))):
        x = build([(click(0.012, 2000, 10000, 230 + i), 0.0, 0.5), (trim(pitch(KR('knifeSlice.ogg'), f), 0, 0.4), 0.0, 0.7), (trim(KI(sh), 0, 0.35), 0.0, 0.9),
                   (thump(120, 38, 0.45, 8, 2.2), 0.0, 0.6), (wet(i + 3, 0.9), 0.01, 1.0), (tail(0.4, 150, 900, 9, 235 + i), 0.02, 0.3)])
        out['darbe_kesik_agir_%d' % (i + 1)] = room(x, 0.35, 0.12)
    # künt (gürz, çekiç normal vuruş): yumruk + ağır yumuşak + doyurulmuş bas + kemik çatırtısı
    for i, (pn, sh) in enumerate((('impactPunch_heavy_000.ogg', 'impactSoft_heavy_001.ogg'), ('impactPunch_heavy_002.ogg', 'impactSoft_heavy_002.ogg'),
                                  ('impactPunch_heavy_004.ogg', 'impactSoft_heavy_004.ogg'))):
        out['darbe_kunt_%d' % (i + 1)] = build([(click(0.01, 1500, 7000, 240 + i), 0.0, 0.5), (trim(KI(pn), 0, 0.3), 0.0, 0.9), (trim(pitch(KI(sh), 0.9), 0, 0.35), 0.0, 0.7),
                                                (thump(100, 36, 0.4, 9, 2.5), 0.0, 0.55), (debris(0.15, 5, 245 + i, 800, 4000), 0.01, 0.45), (tail(0.12, 400, 2500, 30, 248 + i), 0.0, 0.5)])
    # çekiç ağır (yere çakma / şarjlı): plaka + yumruk + derin gümbürtü + moloz + oda
    for i, (pl, pn) in enumerate((('impactPlate_heavy_000.ogg', 'impactPunch_heavy_001.ogg'), ('impactPlate_heavy_003.ogg', 'impactPunch_heavy_003.ogg'),
                                  ('impactPlate_heavy_001.ogg', 'impactPunch_heavy_000.ogg'))):
        x = build([(click(0.015, 1200, 8000, 250 + i), 0.0, 0.6), (trim(pitch(KI(pl), 0.65), 0, 0.5), 0.0, 0.45), (trim(KI(pn), 0, 0.3), 0.0, 0.9),
                   (thump(90, 28, 0.8, 5, 2.5), 0.0, 0.8), (rumble(0.7, 220, 5, 255 + i), 0.0, 0.3), (debris(0.6, 16, 258 + i), 0.03, 0.5)])
        out['darbe_cekic_%d' % (i + 1)] = room(x, 0.5, 0.15)
    # delme (kargı, saplama): keskin "tçık" + ıslak
    for i, f in enumerate((1.25, 1.35, 1.18)):
        out['darbe_delme_%d' % (i + 1)] = build([(click(0.008, 4000, 14000, 260 + i), 0.0, 0.6), (trim(pitch(KR('knifeSlice2.ogg'), f), 0, 0.22), 0.0, 0.75),
                                                 (trim(KI('impactSoft_medium_001.ogg'), 0, 0.2), 0.0, 0.5), (thump(170, 70, 0.15, 22), 0.0, 0.3), (wet(i + 6), 0.0, 0.8)])
    # balta / teber: odun yarma gibi "çat" + ağır gövde
    for i, sh in enumerate(('impactSoft_heavy_000.ogg', 'impactSoft_heavy_003.ogg', 'impactSoft_heavy_002.ogg')):
        out['darbe_balta_%d' % (i + 1)] = build([(click(0.01, 2000, 9000, 270 + i), 0.0, 0.5), (trim(pitch(KR('chop.ogg'), 1.0 - 0.06 * i), 0, 0.25), 0.0, 0.9),
                                                 (trim(KI(sh), 0, 0.3), 0.0, 0.7), (trim(KR('knifeSlice.ogg'), 0, 0.2), 0.0, 0.25), (thump(120, 42, 0.35, 10, 2.0), 0.0, 0.6),
                                                 (wet(i + 9, 0.6), 0.01, 1.0)])
    # kırbaç: şaklama + şap
    for i in range(2):
        out['darbe_kirbac_%d' % (i + 1)] = build([(click(0.006, 3000, 15000, 280 + i), 0.0, 1.0), (trim(pitch(KI('impactPlate_light_00%d.ogg' % (1 + 3 * i)), 1.7), 0, 0.15), 0.0, 0.6),
                                                  (trim(pitch(KR('knifeSlice2.ogg'), 1.4), 0, 0.15), 0.0, 0.35), (wet(i + 12), 0.0, 0.6), (thump(200, 90, 0.1, 30), 0.0, 0.4)])
    # taş (balbal / kalkan): madencilik vuruşu + plaka + çatlak + moloz
    for i, (mn, pl) in enumerate((('impactMining_000.ogg', 'impactPlate_medium_000.ogg'), ('impactMining_003.ogg', 'impactPlate_medium_002.ogg'),
                                  ('impactMining_001.ogg', 'impactPlate_medium_004.ogg'))):
        out['darbe_tas_%d' % (i + 1)] = build([(trim(KI(mn), 0, 0.35), 0.0, 0.9), (trim(KI(pl), 0, 0.3), 0.0, 0.4), (click(0.012, 1800, 9000, 290 + i), 0.0, 0.6),
                                               (thump(130, 60, 0.2, 18), 0.0, 0.3), (debris(0.35, 9, 295 + i), 0.02, 0.6)])
    out['darbe_tas'] = out['darbe_tas_1']
    # metal (siper): kayıt + çınlama
    for i, m in enumerate(('impactMetal_medium_000.ogg', 'impactMetal_heavy_002.ogg', 'impactMetal_medium_003.ogg')):
        out['darbe_metal_%d' % (i + 1)] = build([(trim(KI(m), 0, 0.4), 0.0, 0.9), (metal_ring(1900 + 300 * i, 0.5, 8, seed=30 + i), 0.0, 0.08), (click(0.008, 4000, 14000, 300 + i), 0.0, 0.4)])
    # kritik: çatırtılı darbe + derin düşüş + parlak "şiing" + kısa hava kuyruğu (ödül hissi)
    for i in range(3):
        sting = mix(metal_ring(2900 + 200 * i, 0.6, 6, seed=40 + i) * 0.16, bell(note('E6') * (1 + 0.06 * i), 0.6, 6, 0.06))
        x = build([(click(0.012, 2500, 14000, 310 + i), 0.0, 0.8), (trim(KR('knifeSlice.ogg' if i != 1 else 'knifeSlice2.ogg'), 0, 0.3), 0.0, 0.7),
                   (trim(KI('impactPunch_heavy_00%d.ogg' % (i * 2)), 0, 0.3), 0.0, 0.9), (thump(110, 32, 0.55, 6, 2.8), 0.0, 0.7),
                   (sting, 0.015, 1.0), (whoosh(0.5, 2500, 9000, 0.1, seed=315 + i, q=0.6), 0.03, 0.35), (wet(i + 15, 0.7), 0.0, 1.0)])
        out['darbe_kritik_%d' % (i + 1)] = room(x, 0.4, 0.14)
    out['darbe_kritik'] = out['darbe_kritik_1']
    # genel et darbesi (mermi, patlama, kapan): yumuşak + yumruk + alt ton
    for i, (sm, pm) in enumerate((('impactSoft_medium_000.ogg', 'impactPunch_medium_000.ogg'), ('impactSoft_medium_002.ogg', 'impactPunch_medium_002.ogg'),
                                  ('impactSoft_medium_004.ogg', 'impactPunch_medium_004.ogg'))):
        out['darbe_et_%d' % (i + 1)] = build([(click(0.008, 2000, 9000, 320 + i), 0.0, 0.35), (trim(KI(sm), 0, 0.25), 0.0, 0.8), (trim(KI(pm), 0, 0.2), 0.0, 0.6),
                                              (thump(140, 50, 0.22, 15), 0.0, 0.4), (wet(i + 18, 0.6), 0.0, 1.0)])
    out['darbe_kunt'] = out['darbe_kunt_1']
    # ağır genel darbe (Enemy: büyük vuruş): künt + ağır kesik karışımı
    out['darbe_agir'] = build([(out['darbe_kunt_2'], 0.0, 0.8), (thump(85, 30, 0.6, 6, 2.5), 0.0, 0.9), (rumble(0.5, 200, 7, 330), 0.0, 0.4), (wet(21, 0.6), 0.0, 1.0)])
    return out


# ------------------------------------------------------------ yay ve ok
def bow():
    out = {}
    # germe: yay gövdesi gıcırtısı + kiriş gerginliği (perdesi yükselen sürtünme tonu)
    for i in range(2):
        d = 0.55
        fr = curve([(0, 85 + 6 * i), (d, 150 + 10 * i)], d)
        ph = 2 * np.pi * np.cumsum(fr) / SR
        tension = (np.sin(ph) * 0.4 + np.sin(2 * ph) * 0.25 + np.sin(3 * ph) * 0.12) * (1 + 0.5 * lp(noise(d, seed=340 + i), 40) * 4)
        tension = bp(tension, 120, 2500) * env(d, a=0.25, d=0.25, s=0.0, r=0.05, curve=1.5)
        out['yay_ger_%d' % (i + 1)] = build([(trim(KR('creak%d.ogg' % (3 if i == 0 else 1)), 0, 0.5), 0.0, 0.55), (tension, 0.0, 0.35),
                                             (trim(KR('cloth%d.ogg' % (1 + i)), 0, 0.3), 0.0, 0.25), (grind(d, 400, 3000, 60, 345 + i), 0.0, 0.15)])
    out['yay_ger'] = out['yay_ger_1']
    # bırakma: kirişin "tvang"ı (perdesi düşen tel) + kol vuruşu + çıkış havası
    for i in range(3):
        f0 = 98 * (1 + 0.07 * i)
        tw = pluck(f0, 0.45, bright=0.9, decay=0.993, seed=350 + i)
        bend = sweep(f0 * 1.25, f0 * 0.92, 0.3, curve=0.3) * exp_env(0.3, 14) * 0.5
        out['yay_birak_%d' % (i + 1)] = build([(click(0.006, 2000, 9000, 355 + i), 0.0, 0.6), (tw, 0.0, 0.55), (bend, 0.0, 0.5), (thump(180, 80, 0.12, 30), 0.0, 0.6),
                                               (whoosh(0.28, 1500, 9000, 0.25, seed=358 + i, q=0.8), 0.01, 0.6), (trim(pitch(RP('battle/swing3.wav'), 1.5), 0, 0.15), 0.0, 0.3)])
    out['yay_birak'] = out['yay_birak_1']
    # ok uçuşu: ince, tiz, Doppler'li vızıltı
    for i in range(3):
        d = 0.42
        x = whoosh(d, 1800, 9000, 0.5, seed=360 + i, q=0.35, k_up=1.6)
        tone = sweep(1300 + 100 * i, 900, d, curve=1.0) * env(d, a=0.15, d=0.22, r=0.05, curve=2.0) * 0.05
        out['ok_ucus_%d' % (i + 1)] = mix(x, tone)
    # ok vuruşu: ete saplanma (tok, ıslak), tahtaya (titreşen şaft), taşa (çıtırtı + sekme)
    for i in range(3):
        out['ok_vurus_%d' % (i + 1)] = build([(click(0.006, 2500, 10000, 370 + i), 0.0, 0.7), (trim(pitch(KR('knifeSlice2.ogg'), 1.4 + 0.08 * i), 0, 0.14), 0.0, 0.5),
                                              (trim(KI('impactSoft_medium_00%d.ogg' % (1 + i)), 0, 0.15), 0.0, 0.7), (thump(190, 70, 0.14, 26), 0.0, 0.3), (wet(30 + i, 0.7), 0.0, 1.0)])
    out['ok_vurus'] = out['ok_vurus_1']
    for i in range(2):
        d = 0.5
        f = 190 + 25 * i
        quiver = sine(f, d) * (0.5 + 0.5 * np.sin(2 * np.pi * (28 + 4 * i) * t_axis(d))) * exp_env(d, 7) * 0.4
        out['ok_vurus_tahta_%d' % (i + 1)] = build([(click(0.006, 2000, 8000, 375 + i), 0.0, 0.6), (trim(KI('impactWood_light_00%d.ogg' % (i * 2)), 0, 0.2), 0.0, 0.9),
                                                    (thump(260, 120, 0.1, 30), 0.0, 0.4), (quiver, 0.01, 0.45)])
    for i in range(2):
        out['ok_vurus_tas_%d' % (i + 1)] = build([(click(0.008, 3000, 12000, 380 + i), 0.0, 0.9), (trim(pitch(KI('impactMining_00%d.ogg' % (2 + i)), 1.5), 0, 0.15), 0.0, 0.6),
                                                  (debris(0.25, 6, 383 + i, 2500, 9000), 0.01, 0.5), (trim(pitch(KI('impactMetal_light_00%d.ogg' % i), 1.6), 0, 0.12), 0.02, 0.2)])
    return out


# ------------------------------------------------------------ yaratıklar
def creatures():
    out = {}
    beast = lambda m: tight(load('rpgpack/RPG Sound Pack/NPC/gutteral beast/mnstr%d.wav' % m))
    shade = lambda m: tight(load('rpgpack/RPG Sound Pack/NPC/shade/shade%d.wav' % m))
    giant = lambda m: tight(load('rpgpack/RPG Sound Pack/NPC/giant/giant%d.wav' % m))
    ogre = lambda m: tight(load('rpgpack/RPG Sound Pack/NPC/ogre/ogre%d.wav' % m))

    # --- Erlik Tazısı (kara_boru): hırlama, havlama-ince inleme, altta cehennem gürlemesi
    def hound_snarl(d, seed, f0=95):
        fr = curve([(0, f0), (d * 0.4, f0 * 1.25), (d, f0 * 0.9)], d)
        v = voice(fr, d, ('a', 'o', 'a'), size=0.9, breath=0.35, grit=3.0, jitter=0.08, seed=seed, sub=0.6)
        return v * env(d, a=0.03, d=d - 0.09, s=0.0, r=0.06, curve=1.5)

    def yelp(d, seed, f0=620):
        fr = curve([(0, f0), (d * 0.25, f0 * 1.15), (d, f0 * 0.55)], d)
        v = voice(fr, d, ('a', 'u'), size=0.55, breath=0.2, grit=1.2, jitter=0.04, seed=seed)
        return v * env(d, a=0.01, d=d - 0.05, s=0.0, r=0.04, curve=2.0)
    for i, (m, f) in enumerate(((1, 1.15), (2, 1.2), (3, 1.1), (12, 1.25))):
        out['kurt_can_%d' % (i + 1)] = build([(trim(pitch(beast(m), f), 0, 0.38), 0.0, 0.7), (yelp(0.22, 400 + i, 600 + 60 * i), 0.0, 0.45),
                                              (hound_snarl(0.3, 405 + i, 80), 0.02, 0.35)])
    out['kurt_olum'] = build([(trim(pitch(beast(14), 1.05), 0, 0.9), 0.0, 0.7), (yelp(0.55, 410, 700), 0.0, 0.5), (trim(pitch(beast(5), 1.3), 0, 0.5), 0.25, 0.3),
                              (thump(110, 40, 0.4, 10, 2.0), 0.45, 0.6), (bp(noise(0.8, seed=411), 1500, 7000) * env(0.8, a=0.2, d=0.5, r=0.1) * 0.25, 0.3, 1.0),
                              (soul_release(0.8, 412), 0.4, 0.6)])
    for i in range(2):
        x = build([(trim(pitch(beast(7 + 2 * i), 0.95), 0, 0.6), 0.0, 0.5), (hound_snarl(0.6, 420 + i, 85 + 10 * i), 0.0, 0.7)])
        out['kurt_hirlama_%d' % (i + 1)] = x
        out['hazirlik_kara_boru_%d' % (i + 1)] = x

    # --- Çor Ruhu (cor): fısıltı, tıslama, hayalet iniltisi (yankılı)
    def whisper(d, seed, vow=('i', 'u', 'a')):
        v = voice(320, d, vow, size=0.8, breath=0.97, jitter=0.0, seed=seed)
        return v * env(d, a=0.05, d=d - 0.12, s=0.0, r=0.07, curve=1.2)

    def hiss(d, seed):
        return bp(noise(d, seed=seed), 3000, 11000) * env(d, a=0.02, d=d - 0.06, s=0.0, r=0.04, curve=2.5)
    for i, s in enumerate((2, 3, 14)):
        x = build([(trim(pitch(shade(s), 1.15 + 0.05 * i), 0, 0.45), 0.0, 0.6), (hiss(0.3, 430 + i), 0.0, 0.35), (whisper(0.35, 433 + i), 0.0, 0.6)])
        out['cor_can_%d' % (i + 1)] = room(x, 0.7, 0.3)
    wail = voice(curve([(0, 520), (0.3, 640), (1.1, 220)], 1.1), 1.1, ('u', 'o', 'u'), size=0.8, breath=0.5, jitter=0.03, seed=440)
    wail *= env(1.1, a=0.08, d=0.9, s=0.0, r=0.1, curve=1.5)
    out['cor_olum'] = room(build([(trim(pitch(shade(8), 1.1), 0, 1.2), 0.0, 0.5), (wail, 0.0, 0.5), (hiss(0.9, 441), 0.1, 0.4), (soul_release(0.9, 442), 0.2, 0.8),
                                  (thump(200, 70, 0.15, 25), 0.0, 0.3)]), 1.0, 0.35)
    for i in range(2):
        x = room(mix(whisper(0.7, 445 + i, ('u', 'i', 'e', 'a')), hiss(0.7, 447 + i) * 0.3, trim(pitch(shade(10 + i), 1.2), 0, 0.7) * 0.35), 0.9, 0.4)
        out['cor_fisilti_%d' % (i + 1)] = x
        out['hazirlik_cor_%d' % (i + 1)] = x

    # --- Kara İye (agac_iyesi): derin inilti, odun gıcırtısı, boynuz takırtısı
    def groan(d, seed, f0=58):
        fr = curve([(0, f0 * 0.9), (d * 0.3, f0 * 1.1), (d, f0 * 0.75)], d)
        v = voice(fr, d, ('o', 'u', 'o'), size=1.9, breath=0.25, grit=1.5, jitter=0.05, seed=seed, sub=0.8)
        return v * env(d, a=0.08, d=d - 0.2, s=0.0, r=0.12, curve=1.2)
    for i, (g, f) in enumerate(((3, 0.72), (4, 0.68), (1, 0.7))):
        out['agac_can_%d' % (i + 1)] = build([(trim(pitch(giant(g), f), 0, 0.7), 0.0, 0.7), (trim(pitch(KR('creak%d.ogg' % (i + 1)), 0.8), 0, 0.45), 0.0, 0.45),
                                              (groan(0.55, 450 + i, 55 + 5 * i), 0.0, 0.5), (trim(KI('impactWood_medium_00%d.ogg' % i), 0, 0.2), 0.0, 0.4)])
    tdie = 2.2
    out['agac_olum'] = room(build([(trim(pitch(giant(2), 0.7), 0, 1.3), 0.0, 0.7), (groan(1.4, 460, 60), 0.0, 0.6), (crackle(0.9, 35, 461, 900, 6000), 0.3, 0.5),
                                   (trim(pitch(KR('creak2.ogg'), 0.6), 0, 0.9), 0.2, 0.5), (trim(KI('impactWood_heavy_000.ogg'), 0, 0.5), 1.05, 0.8),
                                   (thump(80, 26, 1.0, 4, 2.5), 1.05, 1.0), (rumble(1.0, 200, 4, 462), 1.05, 0.5), (soul_release(0.9, 463), 1.1, 0.6)], tdie), 0.7, 0.2)
    for i in range(2):
        x = build([(groan(0.9, 465 + i, 50 + 6 * i), 0.0, 0.7), (trim(pitch(KR('creak%d.ogg' % (2 + i)), 0.7), 0, 0.8), 0.05, 0.5), (crackle(0.7, 14, 467 + i, 800, 5000), 0.1, 0.3)])
        out['agac_inilti_%d' % (i + 1)] = x
        out['hazirlik_agac_iyesi_%d' % (i + 1)] = x

    # --- Balbal (taş heykel): çatlama, taş sürtünmesi, çöküş
    for i, mn in enumerate((0, 2, 4)):
        out['tas_can_%d' % (i + 1)] = build([(trim(pitch(KI('impactMining_00%d.ogg' % mn), 0.8), 0, 0.35), 0.0, 0.8), (click(0.015, 1500, 8000, 470 + i), 0.0, 0.7),
                                             (grind(0.35, 120, 1500, 40, 473 + i), 0.03, 0.6), (debris(0.4, 10, 476 + i), 0.02, 0.7), (thump(110, 50, 0.25, 14), 0.0, 0.3)])
    out['tas_olum'] = room(build([(click(0.02, 1200, 7000, 480), 0.0, 0.9), (trim(pitch(KI('impactMining_001.ogg'), 0.7), 0, 0.4), 0.0, 0.8),
                                  (grind(0.8, 90, 1200, 30, 481), 0.05, 0.7), (debris(1.3, 45, 482, 900, 6000), 0.15, 0.7),
                                  (thump(75, 25, 0.9, 4, 2.5), 0.55, 1.1), (rumble(1.2, 180, 3.5, 483), 0.5, 0.7), (soul_release(0.7, 484), 0.6, 0.5)], 2.0), 0.6, 0.2)
    for i in range(2):
        x = build([(grind(0.7, 100 + 20 * i, 1400, 25 + 10 * i, 486 + i), 0.0, 1.0), (debris(0.6, 7, 488 + i, 1200, 6000), 0.05, 0.3), (sub(45, 0.7, 3, 0.3), 0.0, 1.0)])
        out['tas_surtunme_%d' % (i + 1)] = x
        out['hazirlik_balbal_%d' % (i + 1)] = x

    # --- Kara Kam (arcura, eski "hayalet" sesleri): ilahi kırıntısı, kam davulu, kıkırtı
    def frame_drum(seed, f=78, g=1.0):
        d = 0.7
        mem = sweep(f * 1.25, f, d, curve=0.25) * exp_env(d, 6) + sweep(f * 1.6, f * 1.55, d) * exp_env(d, 14) * 0.4
        slap = bp(noise(0.06, seed=seed), 200, 2500) * exp_env(0.06, 50)
        rng = np.random.default_rng(seed)
        jing = np.zeros(int(0.5 * SR))
        for k in range(7):  # çıngıraklar (kam davulunun demir halkaları)
            place(jing, metal_ring(rng.uniform(3500, 6000), 0.15, 30, seed=int(rng.integers(1e5))), rng.uniform(0.0, 0.18), rng.uniform(0.3, 0.8))
        return build([(mem, 0.0, 1.0), (slap, 0.0, 0.5), (jing, 0.01, 0.12)]) * g

    def cackle(n, seed, f0=420, size=0.75):
        sy = 0.085
        d = n * sy + 0.1
        fr = curve([(0, f0), (d, f0 * 0.7)], d) * (1 + 0.08 * np.sin(2 * np.pi * 11 * t_axis(d)))
        v = voice(fr, d, ('a', 'e', 'a', 'ı'), size=size, breath=0.35, grit=1.5, jitter=0.05, seed=seed)
        return gated(v, [k * sy for k in range(n)], [sy * 0.7] * n)

    def chant(d, seed, f0=110):
        fr = f0 * (1 + 0.012 * np.sin(2 * np.pi * 5 * t_axis(d)))
        v = voice(fr, d, ('o', 'u', 'o', 'a'), size=1.15, breath=0.12, grit=0.8, jitter=0.01, seed=seed, sub=0.3)
        # gırtlak (hömey) üst tonu: dar bir harmonik yükselip iner
        h = curve([(0, 6), (d * 0.5, 9), (d, 7)], d)

        def g(tt, ff):
            hh = np.interp(np.clip(tt[:, 0], 0, d), np.linspace(0, d, len(h)), h)[:, None]
            return 1.0 + 6.0 * resonance(ff, hh * f0, 40)
        v = stft_shape(v, g)
        return v * env(d, a=0.1, d=d - 0.25, s=0.0, r=0.15, curve=1.0)
    for i in range(3):
        grunt = voice(curve([(0, 190 + 20 * i), (0.25, 130)], 0.25), 0.25, ('a', 'ı'), size=1.0, breath=0.3, grit=2.0, jitter=0.05, seed=490 + i)
        grunt *= env(0.25, a=0.01, d=0.2, r=0.04, curve=2)
        out['hayalet_can_%d' % (i + 1)] = build([(grunt, 0.0, 0.7), (cackle(2, 493 + i, 380), 0.12, 0.3), (frame_drum(496 + i, 90, 0.18), 0.0, 1.0)])
    out['hayalet_olum'] = room(build([(cackle(6, 500, 460), 0.0, 0.55), (chant(1.1, 501, 98), 0.4, 0.4), (frame_drum(502, 70), 0.45, 0.9),
                                      (sweep(500, 140, 1.0) * env(1.0, a=0.05, d=0.85, r=0.1) * 0.08, 0.5, 1.0), (soul_release(1.0, 503), 0.6, 0.7)], 2.0), 0.9, 0.3)
    for i in range(2):
        out['kam_davul_%d' % (i + 1)] = room(frame_drum(510 + i, 74 + 8 * i), 0.6, 0.2)
        out['kam_kahkaha_%d' % (i + 1)] = room(cackle(7 + i, 512 + i, 430 - 30 * i), 0.6, 0.25)
        ch = build([(chant(1.2, 514 + i, 104 + 12 * i), 0.0, 0.8), (frame_drum(516 + i, 76, 0.4), 0.0, 1.0), (frame_drum(518 + i, 80, 0.3), 0.55, 1.0)])
        out['kam_ilahi_%d' % (i + 1)] = room(ch, 0.8, 0.3)
        out['hazirlik_arcura_%d' % (i + 1)] = room(build([(chant(0.7, 520 + i, 110 + 10 * i), 0.0, 0.8), (frame_drum(522 + i, 80, 0.5), 0.0, 1.0)]), 0.7, 0.25)

    # --- Gulyabani (surale): çığlık, hırıltılı nefes, gırtlak gurultusu
    def shriek(d, seed, f0=780):
        fr = curve([(0, f0 * 0.8), (d * 0.2, f0 * 1.2), (d * 0.6, f0), (d, f0 * 0.6)], d)
        v = voice(fr, d, ('e', 'i', 'a'), size=0.65, breath=0.4, grit=2.5, jitter=0.07, seed=seed, sub=0.3)
        return v * env(d, a=0.015, d=d - 0.07, s=0.0, r=0.05, curve=1.2)

    def rasp(d, seed, f0=70):
        v = voice(f0, d, ('a', 'ı', 'a'), size=0.9, breath=0.85, grit=3.0, jitter=0.15, seed=seed)
        return v * env(d, a=0.04, d=d - 0.1, s=0.0, r=0.06, curve=1.0)
    for i in range(3):
        out['surale_can_%d' % (i + 1)] = build([(shriek(0.32, 530 + i, 720 + 60 * i), 0.0, 0.6), (rasp(0.3, 533 + i), 0.02, 0.5),
                                                (trim(pitch(ogre(1 + i), 1.35), 0, 0.3), 0.0, 0.35)])
    out['surale_olum'] = room(build([(shriek(0.8, 540, 820), 0.0, 0.6), (rasp(0.9, 541, 60), 0.5, 0.6), (trim(pitch(ogre(4), 1.2), 0, 0.5), 0.0, 0.3),
                                     (thump(120, 40, 0.35, 10, 2.0), 1.0, 0.7), (soul_release(0.8, 542), 0.8, 0.6)], 2.0), 0.6, 0.2)
    for i in range(2):
        x = build([(rasp(0.35, 545 + i), 0.0, 0.5), (shriek(0.5, 547 + i, 860 + 80 * i), 0.25, 0.7)])
        out['surale_ciglik_%d' % (i + 1)] = x
        out['hazirlik_surale_%d' % (i + 1)] = x

    # --- genel hazırlık (eski ad): gerilen hava + hırıltı
    out['dusman_hazirlik'] = build([(whoosh(0.4, 200, 2000, 0.85, seed=550, k_up=1.0), 0.0, 0.6), (trim(pitch(beast(7), 0.9), 0, 0.4), 0.0, 0.45)])
    # --- kahraman
    out['bengu_can'] = build([(trim(pitch(beast(15), 1.45), 0, 0.3), 0.0, 0.6), (trim(KI('impactPunch_medium_001.ogg'), 0, 0.2), 0.0, 0.8),
                              (thump(150, 50, 0.25, 14, 2.0), 0.0, 0.8), (click(0.01, 2000, 9000, 560), 0.0, 0.5)])
    return out


# ------------------------------------------------------------ arayüz
def ui():
    """Arayüz: yumuşak tahta tıkırtısı + metal kopça + kopuz teli. Hepsi aynı tını ailesinde (Hüseyni, La kökü)."""
    out = {}
    wood = lambda k, f=1.0, d=0.08: trim(pitch(KI('impactWood_light_00%d.ogg' % k), f), 0, d, 0.02)
    for i in range(3):
        x = build([(wood(i, 1.9 + 0.08 * i, 0.05), 0.0, 0.8), (kopuz(note('A5') * (1 + 0.003 * i), 0.12, 0.4, seed=600 + i), 0.0, 0.12)])
        out['ui_gez_%d' % (i + 1)] = fade(x, 0.0005, 0.02)
        out['ui_sec_%d' % (i + 1)] = out['ui_gez_%d' % (i + 1)]
    out['ui_sec'] = out['ui_sec_1']
    out['ui_onay'] = build([(wood(1, 1.4, 0.07), 0.0, 0.8), (trim(KR('metalClick.ogg'), 0, 0.08, 0.02), 0.0, 0.25),
                            (kopuz(note('E5'), 0.4, 0.6, seed=610), 0.0, 0.5), (kopuz(note('A5'), 0.5, 0.6, seed=611), 0.07, 0.55)])
    out['ui_iptal'] = build([(wood(3, 1.2, 0.07), 0.0, 0.7), (kopuz(note('A4'), 0.3, 0.45, seed=612), 0.0, 0.45), (kopuz(note('E4'), 0.35, 0.4, seed=613), 0.07, 0.45)])
    out['ui_ac'] = build([(trim(KR('bookOpen.ogg'), 0, 0.15), 0.0, 0.5), (trim(RP('inventory/cloth.wav'), 0, 0.25), 0.0, 0.35), (wood(2, 1.1, 0.08), 0.03, 0.5),
                          (kopuz(note('A3'), 0.5, 0.5, seed=614), 0.03, 0.4), (kopuz(note('E4'), 0.45, 0.5, seed=615), 0.06, 0.3), (kopuz(note('A4'), 0.4, 0.5, seed=616), 0.09, 0.25)])
    out['ui_kapa'] = build([(trim(KR('bookClose.ogg'), 0, 0.2), 0.0, 0.5), (wood(4, 1.0, 0.08), 0.02, 0.5), (kopuz(note('E4'), 0.3, 0.35, seed=617), 0.0, 0.3),
                            (kopuz(note('A3'), 0.35, 0.35, seed=618), 0.05, 0.35)])
    out['esya_kusan'] = room(build([(trim(KR('metalLatch.ogg'), 0, 0.2), 0.0, 0.5), (trim(RP('inventory/armor-light.wav'), 0, 0.35), 0.02, 0.6),
                                    (trim(RP('battle/sword-unsheathe3.wav'), 0, 0.3), 0.05, 0.3), (thump(160, 70, 0.15, 25), 0.02, 0.4),
                                    (kopuz(note('A3'), 0.6, 0.6, seed=620), 0.06, 0.35), (kopuz(note('E4'), 0.55, 0.6, seed=621), 0.08, 0.3),
                                    (kopuz(note('A4'), 0.5, 0.6, seed=622), 0.1, 0.3)]), 0.4, 0.15)
    out['esya_degis'] = build([(trim(KR('dropLeather.ogg'), 0, 0.3), 0.0, 0.6), (trim(RP('inventory/metal-small2.wav'), 0, 0.25), 0.05, 0.35),
                               (trim(KR('cloth3.ogg'), 0, 0.25), 0.0, 0.3), (wood(0, 1.0, 0.08), 0.02, 0.4), (kopuz(note('D4'), 0.35, 0.5, seed=625), 0.05, 0.3)])
    # tılsım seçimi: yükselen kopuz arpeji + çan ışıltısı + yumuşak alt dalga (ödül)
    d = 1.6
    arp = [(note('A3'), 0.0), (note('E4'), 0.07), (note('A4'), 0.14), (note('B4'), 0.21), (note('E5'), 0.28), (note('A5'), 0.36)]
    parts = [(kopuz(f, 1.0, 0.65, seed=630 + k, decay=0.997), t, 0.4) for k, (f, t) in enumerate(arp)]
    parts += [(bell(note('E6'), 1.2, 3.0, 0.05), 0.36, 1.0), (bell(note('A6'), 1.2, 3.0, 0.035), 0.42, 1.0),
              (sub(note('A1'), 0.9, 4, 0.35), 0.0, 1.0), (whoosh(0.7, 2000, 9000, 0.6, seed=638, q=0.5), 0.0, 0.25), (shimmer(0.9, 0.06), 0.3, 1.0)]
    out['tilsim_sec'] = room(build(parts, d), 0.8, 0.3)
    # seviye atlama: kopuz akoru vuruşu + davul + parlak çan çiçeği
    strum = [(note('A2'), 0.0), (note('E3'), 0.015), (note('A3'), 0.03), (note('E4'), 0.045), (note('A4'), 0.06)]
    parts = [(kopuz(f, 1.4, 0.7, seed=640 + k, decay=0.998), t, 0.4) for k, (f, t) in enumerate(strum)]
    parts += [(thump(110, 45, 0.6, 6, 1.5), 0.0, 0.9), (bp(noise(0.05, seed=646), 300, 3000) * exp_env(0.05, 50), 0.0, 0.5),
              (bell(note('A5'), 1.5, 2.2, 0.06), 0.12, 1.0), (bell(note('E6'), 1.5, 2.2, 0.05), 0.18, 1.0), (bell(note('A6'), 1.5, 2.2, 0.04), 0.24, 1.0),
              (whoosh(0.5, 1500, 10000, 0.15, seed=647, q=0.5), 0.1, 0.3), (shimmer(1.2, 0.08), 0.15, 1.0)]
    out['seviye'] = room(build(parts, 2.0), 0.9, 0.3)
    # NPC konuşma kırıntıları: kısa kopuz + tahta
    for i, nm in enumerate(('E4', 'A4', 'B4')):
        out['npc_%d' % (i + 1)] = build([(kopuz(note(nm), 0.18, 0.5, seed=650 + i), 0.0, 0.6), (wood(i, 1.6, 0.04), 0.0, 0.3)])
    return out


# ------------------------------------------------------------ döngüler (kalp, ortam)
def heartbeat():
    """Düşük can kalp atışı: 1.0 sn'lik dikişsiz döngü (çalma perdesi hızlandırır)."""
    d = 1.0
    lub = mix(thump(70, 42, 0.16, 22, 1.5), lp(noise(0.05, seed=660), 300) * exp_env(0.05, 60) * 0.4)
    dub = mix(thump(85, 50, 0.13, 26, 1.5) * 0.7, lp(noise(0.04, seed=661), 400) * exp_env(0.04, 70) * 0.3)
    x = build([(lub, 0.03, 1.0), (dub, 0.30, 1.0)], d)[:int(d * SR)]
    return x


AMB_SR = 22050


def _loop(x, sr, xf=1.0):
    n = int(xf * sr)
    y = x[:-n].copy()
    w = np.linspace(0, 1, n)
    y[:n] = y[:n] * w + x[-n:] * (1 - w)
    return y


def ambience():
    """Biyom ortam döngüleri (22.05 kHz, ~12 sn): rüzgâr, damla, çıtırtı, uzak sesler. Müziğin altında çok kısık çalar."""
    sr = AMB_SR
    d = 13.0
    T = t_axis(d, sr)
    rng = np.random.default_rng(700)

    def windbed(seed, lo, hi, depth=0.7, rate=0.15):
        x = fft_filter(noise(d, sr, seed), lo=lo, hi=hi, sr=sr, slope=1.0)
        m = fft_filter(noise(d, sr, seed + 1), hi=rate, sr=sr, slope=1.0)
        m = (m - m.min()) / (m.max() - m.min() + 1e-9)
        return x * ((1 - depth) + depth * m)

    def events(fn, n, seed, lo=0.0, hi=None):
        r = np.random.default_rng(seed)
        x = np.zeros(len(T))
        for _ in range(n):
            e = fn(r)
            place(x, e, r.uniform(lo, (hi or d) - len(e) / sr - 0.05), 1.0, sr)
        return x

    def bird(r):
        dd = r.uniform(0.08, 0.2)
        f0 = r.uniform(2500, 4200)
        tt = t_axis(dd, sr)
        return np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.25 * np.sin(2 * np.pi * r.uniform(8, 20) * tt))) / sr) * exp_env(dd, 10, sr) * r.uniform(0.03, 0.08)

    def drip(r):
        f = r.uniform(900, 2600)
        return sweep(f, f * 1.6, 0.06, sr=sr) * exp_env(0.06, 50, sr) * r.uniform(0.15, 0.4)

    def pop(r):
        dd = r.uniform(0.005, 0.02)
        return fft_filter(noise(dd + 0.01, sr, int(r.integers(1e6))), lo=800, hi=6000, sr=sr)[:int(dd * sr)] * r.uniform(0.2, 0.7)
    out = {}
    out['ortam_otuken_dongu'] = mix(windbed(701, 150, 1200, 0.6) * 0.5, windbed(703, 2000, 6000, 0.8, 0.3) * 0.12, events(bird, 9, 705))
    out['ortam_bozkir_dongu'] = mix(windbed(711, 200, 2500, 0.8, 0.2) * 0.7, windbed(713, 3000, 8000, 0.9, 0.4) * 0.2)
    cave = reverb(events(drip, 14, 722), 2.0, 0.5, sr, lp=3000, seed=723)[:len(T)]
    out['ortam_sahmeran_dongu'] = mix(fft_filter(noise(d, sr, 721), lo=40, hi=220, sr=sr, slope=1.0) * 0.45, cave * 0.8,
                                      np.sin(2 * np.pi * 55 * T) * 0.02 * (1 + 0.5 * np.sin(2 * np.pi * 0.1 * T)))
    whistle = stft_shape(noise(d, sr, 731), lambda tt, ff: resonance(ff, 900 + 400 * np.sin(2 * np.pi * tt / d * 3), 60) + 0.6 * resonance(ff, 1500 + 300 * np.sin(2 * np.pi * tt / d * 2 + 1), 80), sr)
    out['ortam_kaf_dongu'] = mix(windbed(732, 300, 3500, 0.85, 0.25) * 0.6, whistle * 0.35 * (0.5 + 0.5 * np.sin(2 * np.pi * T / d * 2) ** 2))
    moan = np.zeros(len(T))
    for k in range(2):
        dd = 3.0
        mm = voice(curve([(0, 70), (dd, 52)], dd, sr), dd, ('o', 'u'), size=1.6, breath=0.6, grit=1.0, sr=sr, seed=741 + k)
        place(moan, mm * env(dd, a=1.0, d=1.6, r=0.4, sr=sr, curve=1.0) * 0.12, 1.5 + 6.0 * k, 1.0, sr)
    out['ortam_tamu_dongu'] = mix(fft_filter(noise(d, sr, 742), lo=30, hi=160, sr=sr, slope=1.0) * 0.6, events(pop, 70, 743) * 0.35,
                                  windbed(744, 400, 2000, 0.7, 0.2) * 0.12, moan)
    out['ortam_yurt_dongu'] = mix(events(pop, 110, 751) * 0.45, windbed(752, 200, 2500, 0.6) * 0.18,
                                  fft_filter(noise(d, sr, 753), lo=100, hi=900, sr=sr, slope=1.0) * 0.12)
    return {k: _loop(v, sr) for k, v in out.items()}


def extras():
    """Patlama ve sarsıntıya ağırlık: eski sentez + derin gövde + moloz + oda."""
    out = {}
    out['patlama'] = room(build([(SY.explosion(), 0.0, 0.8), (click(0.02, 800, 9000, 800), 0.0, 0.8), (thump(90, 24, 1.3, 3.5, 3.0), 0.0, 1.0),
                                 (debris(1.4, 40, 801, 1000, 7000), 0.05, 0.4), (rumble(1.6, 160, 2.5, 802), 0.0, 0.6)]), 0.8, 0.15)
    out['sarsinti'] = room(build([(SY.shockwave(), 0.0, 0.7), (thump(75, 22, 1.2, 3.5, 3.0), 0.0, 1.0), (debris(1.0, 30, 803), 0.05, 0.35),
                                  (rumble(1.2, 150, 3, 804), 0.0, 0.6)]), 0.7, 0.12)
    out['inis_2'] = build([(trim(KI('impactSoft_heavy_002.ogg'), 0, 0.3), 0.0, 0.9), (trim(KI('footstep_grass_004.ogg'), 0, 0.25), 0.0, 0.6),
                           (thump(90, 35, 0.35, 10, 2.0), 0.0, 0.9), (debris(0.25, 6, 805, 800, 5000), 0.01, 0.25)])
    return out


def build_all():
    out = {}
    for fn in (swings, hits, bow, creatures, ui, extras):
        out.update(fn())
    out['kalp_dongu'] = heartbeat()
    return out
