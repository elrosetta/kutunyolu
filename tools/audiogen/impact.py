"""v13 darbe hiyerarşisi: hafif / ağır / kritik / öldürücü vuruş, künt (taş-kalkan) darbe, savuruş hazırlığı,
kademeli patlama (tık+çatırtı -> alt bas gümbürtü -> moloz kuyruğu), yıldırım (çatırtı + gök gürlemesi + cızırtı döngüsü)
ve yer sarsıntısı. Hepsi mono 44.1 kHz; yükseklik eşitlemesi export_audio.py (synth.master) ile kategori hedeflerine göre.

Zamanlama (görselle hizalama): dosya başı = tetikleme anı. Hafif darbede geçiş t=0'dadır; ağır/kritik/öldürücü darbede
geçişten önce kısa bir bas ön-yankı / ters yükseliş vardır, geçişin dosya içindeki anı ONSET sözlüğünde (sn) tutulur ve
sfx.json'a "onset" olarak yazılır. Vuruş duraklaması (hitstop) ile aynı karede tetiklenince ön-yankı duraklamanın içine düşer,
geçiş de "darbe karesi"nin üstüne oturur. Patlamada tık t=0, alt bas t=+15 ms'de vurur.
Yeniden üretim: python tools/audiogen/export_audio.py --sfx [ad ...]"""
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import (SR, t_axis, env, exp_env, noise, fft_filter, sine, sweep, distort, mix, place, fade, reverb, hp, lp, bp)
from layer import KI, KR, trim, pitch, build
from pro import click, thump, tail, whoosh, metal_ring, room, rumble, debris, crackle, grind, bell, note

# geçiş (vuruş anı) dosya içinde kaçıncı saniyede (ön-yankı payı); çağıran taraf isterse bu kadar erken tetikler
ONSET = {'darbe_hafif': 0.0, 'darbe_agir': 0.036, 'darbe_kritik': 0.045, 'olum_vurus': 0.03, 'darbe_donuk': 0.0,
         'patlama': 0.0, 'patlama_buyuk': 0.0, 'patlama_uzak': 0.0, 'simsek_catirti': 0.03, 'gok_gurleme': 0.0,
         'sarsinti': 0.0, 'sarsinti_buyuk': 0.0}


# ------------------------------------------------------------ yapı taşları
def cut(x, dur, fout=0.02, fin=0.0005):
    """Diziyi dur saniyeye kes ve uçlarını yumuşat."""
    y = x[:int(dur * SR)].copy()
    return fade(y, fin, min(fout, len(y) / SR * 0.4))


def glue(x, drive=1.5):
    """Yapıştırıcı doyurma: tepeyi 1'e getirip yumuşakça sıkar (tepe/ortalama oranı düşer, master daha az sınırlar)."""
    return distort(x / (np.max(np.abs(x)) + 1e-9), drive)


def rev_swell(dur, lo=1500, hi=8000, seed=1, k=6.0):
    """Ters yükseliş: sona doğru üstel artan bant gürültüsü (vuruşa doğru 'çekilen' hava)."""
    t = t_axis(dur)
    return bp(noise(dur, seed=seed), lo, hi) * np.exp(k * (t / dur - 1.0))


def pre_drop(dur, f=72, seed=2, g_tone=0.5, g_noise=0.5):
    """Bas ön-yankı: geçişten hemen önce yükselen alt ton + alçak geçirilmiş gürültü (ağırlık 'geliyor' hissi)."""
    t = t_axis(dur)
    u = t / dur
    return sine(f, dur) * u ** 2 * g_tone + lp(noise(dur, seed=seed), 300) * u ** 3 * g_noise


def sub_drop(f0, f1, dur, k=6.0, drive=1.0, g=1.0, a=0.003):
    """Perdesi düşen alt bas (50-90 Hz bölgesi); drive > 1 ise hafif doyurma (küçük hoparlörde de okunsun)."""
    x = sweep(f0, f1, dur, curve=0.5) * exp_env(dur, k)
    na = max(1, int(a * SR))
    x[:na] *= np.linspace(0, 1, na)
    return (distort(x, drive) if drive > 1 else x) * g


def crunch(dur=0.08, seed=3, lo=250, hi=3200, drive=4.0, rate=90.0, k=None):
    """Çıtırtılı 'kırılma': bant gürültü, tanecikli genlik, doyurma (kemik/kabuk/odun kırılması)."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    x = bp(noise(dur, seed=seed), lo, hi)
    m = np.abs(lp(rng.standard_normal(n), rate))
    m /= np.max(m) + 1e-9
    return distort(x * (0.35 + m), drive) * exp_env(dur, k or 4.0 / dur)


def grains(dur, n=40, seed=4, lo=2500, hi=9000, dmin=0.004, dmax=0.015, g=1.0):
    """Zaman içine düzgün dağılmış küçük çıtırtılar (elektrik cızırtısı, uzak çatırtılar)."""
    rng = np.random.default_rng(seed)
    x = np.zeros(int(dur * SR))
    for _ in range(n):
        t = rng.random() * dur
        d = rng.uniform(dmin, dmax)
        c = bp(noise(d + 0.01, seed=int(rng.integers(1e6))), lo * rng.uniform(0.7, 1.3), hi)[:int(d * SR)] * exp_env(d, 3.0 / d)
        place(x, c, t, rng.uniform(0.3, 1.0) * g)
    return x


def shing(dur=0.3, f_lo=3500, f_hi=10000, seed=5, g=1.0, ring_f=4300.0):
    """Tiz 'şiing': yükselen süzgeçli hava + ince inharmonik çınlama."""
    air = whoosh(dur, f_lo, f_hi, 0.12, seed=seed, q=0.5)
    rng = metal_ring(ring_f, dur, 9, parts=(1.0, 1.41, 2.1), seed=seed)
    return (air * 0.8 + rng * 0.25) * g


def boom_sub(f0=70.0, f1=48.0, drop=0.15, dur=0.6, k=5.0, a=0.004, drive=1.8, f_end=None):
    """Patlama alt bası: perde f0 -> f1 (drop süresinde), sonra yavaşça f_end'e; üstel sönüm; hafif doyurma."""
    n = int(dur * SR)
    t = t_axis(dur)
    f_end = f_end or f1 * 0.9
    f = np.where(t < drop, f0 * (f1 / f0) ** (t / drop), f1 * (f_end / f1) ** np.clip((t - drop) / max(dur - drop, 1e-3), 0, 1))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * exp_env(dur, k)
    na = max(1, int(a * SR))
    x[:na] *= np.linspace(0, 1, na)
    return distort(x, drive) * 0.85 if drive > 1 else x


def loop_xf(x, xf=0.3):
    """Döngü dikişi: sonu başa çapraz geçirir (dikişte sıçrama olmaz)."""
    n = int(xf * SR)
    y = x[:-n].copy()
    w = np.linspace(0, 1, n)
    y[:n] = y[:n] * w + x[-n:] * (1 - w)
    return y


# ------------------------------------------------------------ darbe hiyerarşisi
def hits():
    out = {}
    # ---- hafif (kademe 0): 80-120 ms, geçiş < 10 ms, az bas. Tık + hafif kayıt gövdesi (250 Hz altı kesik) + kısa hava.
    for i, (g, f) in enumerate((('impactGeneric_light_000.ogg', 1.15), ('impactGeneric_light_002.ogg', 1.08), ('impactSoft_medium_001.ogg', 1.25))):
        body = hp(trim(pitch(KI(g), f), 0, 0.09, 0.03), 250)
        x = build([(click(0.007, 3000, 14000, 500 + i), 0.0, 0.55), (body, 0.0, 1.0),
                   (bp(noise(0.06, seed=510 + i), 900, 5000) * exp_env(0.06, 60), 0.0, 0.5),
                   (thump(230, 120, 0.06, 45, 1.0), 0.0, 0.22), (tail(0.07, 400, 2500, 50, 515 + i), 0.003, 0.35)])
        out['darbe_hafif_%d' % (i + 1)] = cut(x, 0.10 + 0.008 * i, 0.025)
    # ---- ağır (kademe 1): 36 ms bas ön-yankı -> geçiş + yumruk gövdesi + 60-90 Hz alt bas + kısa kuyruk (~220 ms).
    P = ONSET['darbe_agir']
    for i, (pn, sh, f0, fs) in enumerate((('impactPunch_heavy_000.ogg', 'impactSoft_heavy_001.ogg', 100, 68),
                                          ('impactPunch_heavy_002.ogg', 'impactSoft_heavy_003.ogg', 92, 62),
                                          ('impactPunch_heavy_004.ogg', 'impactSoft_heavy_004.ogg', 108, 74))):
        x = build([(pre_drop(P, fs + 6, 520 + i), 0.0, 0.5),
                   (click(0.012, 1200, 9000, 525 + i), P, 0.6), (trim(KI(pn), 0, 0.18), P, 1.0),
                   (trim(pitch(KI(sh), 0.85), 0, 0.2), P, 0.7), (thump(f0, 40, 0.22, 13, 2.6), P, 0.5),
                   (sub_drop(fs + 10, fs - 8, 0.21, 12, 1.0, 0.3), P, 1.0), (bp(noise(0.04, seed=545 + i), 200, 1200) * exp_env(0.04, 70), P, 0.5),
                   (tail(0.14, 250, 2200, 22, 530 + i), P + 0.005, 0.5), (debris(0.12, 4, 540 + i, 700, 3500), P + 0.01, 0.3)])
        out['darbe_agir_%d' % (i + 1)] = cut(room(glue(x, 2.0), 0.3, 0.08), P + 0.225, 0.03)
    out['darbe_agir'] = out['darbe_agir_1']
    # ---- kritik (kademe 2): ters yükseliş (45 ms) -> çatırtılı kırılma + bas düşüşü + çelik çınlaması + tiz hava, ~350 ms.
    P = ONSET['darbe_kritik']
    for i, (ks, pn, wd) in enumerate((('knifeSlice.ogg', 'impactPunch_heavy_000.ogg', 'impactWood_heavy_000.ogg'),
                                      ('knifeSlice2.ogg', 'impactPunch_heavy_002.ogg', 'impactWood_heavy_002.ogg'),
                                      ('knifeSlice.ogg', 'impactPunch_heavy_004.ogg', 'impactWood_heavy_003.ogg'))):
        pre = mix(rev_swell(P, 1500, 9000, 550 + i, 7.0) * 0.5, pre_drop(P, 80, 555 + i, 0.45, 0.2), metal_ring(3000 + 150 * i, P, 30, seed=560 + i)[::-1] * 0.2)
        x = build([(pre, 0.0, 0.8),
                   (click(0.01, 2500, 15000, 565 + i), P, 0.9), (trim(KR(ks), 0, 0.12), P, 0.6), (trim(KI(pn), 0, 0.2), P, 0.9),
                   (trim(KI(wd), 0, 0.12), P, 0.5), (crunch(0.07, 570 + i, 250, 3200, 4.0), P, 0.6),
                   (sub_drop(110, 45, 0.25, 9, 2.5, 0.5), P, 1.0), (metal_ring(2700 + 200 * i, 0.3, 10, seed=575 + i), P + 0.004, 0.3),
                   (bell(note('E6') * (1 + 0.06 * i), 0.3, 8, 0.07), P + 0.004, 1.0), (whoosh(0.25, 3000, 9000, 0.08, seed=580 + i, q=0.6), P + 0.01, 0.3),
                   (tail(0.16, 300, 1800, 20, 585 + i), P + 0.005, 0.6)])
        out['darbe_kritik_%d' % (i + 1)] = cut(room(glue(x, 1.4), 0.35, 0.12), P + 0.305, 0.03)
    out['darbe_kritik'] = out['darbe_kritik_1']
    # ---- öldürücü (kademe 3): kısa ön-yankı -> uzun bas düşüşü + ıslak kırılma + tiz 'şiing' kuyruğu (~0.6 s). Kritikten
    # daha alçak ve uzun, çan yok, hava var.
    P = ONSET['olum_vurus']
    for i, (pn, sh) in enumerate((('impactPunch_heavy_001.ogg', 'impactSoft_heavy_000.ogg'), ('impactPunch_heavy_003.ogg', 'impactSoft_heavy_002.ogg'))):
        pre = mix(pre_drop(P, 60, 600 + i, 0.5, 0.3), rev_swell(P, 400, 3000, 605 + i, 6.0) * 0.4)
        x = build([(pre, 0.0, 0.8),
                   (click(0.01, 1500, 10000, 610 + i), P, 0.7), (trim(KI(pn), 0, 0.22), P, 0.9), (trim(pitch(KI(sh), 0.75), 0, 0.3), P, 0.8),
                   (crunch(0.11, 615 + i, 200, 2500, 5.0, 70), P, 1.3), (sub_drop(120, 28, 0.5, 5.0, 3.0, 0.3), P, 1.0),
                   (rumble(0.35, 160, 8, 620 + i), P, 0.3), (shing(0.32, 3500, 10000, 625 + i, 0.3, 4300 + 300 * i), P + 0.03, 1.0),
                   (tail(0.2, 250, 1500, 14, 630 + i), P + 0.01, 0.5)])
        out['olum_vurus_%d' % (i + 1)] = cut(room(glue(x, 2.0), 0.45, 0.12), P + 0.57, 0.04)
    # ---- künt/donuk (taş, kalkan): alçak geçirilmiş plaka + yumuşak ağır + kısa gümbürtü; 3 kHz üstü yok.
    for i, (pl, f) in enumerate((('impactPlate_medium_001.ogg', 0.7), ('impactMining_002.ogg', 0.8))):
        x = build([(lp(trim(pitch(KI(pl), f), 0, 0.2), 1800), 0.0, 0.7), (trim(KI('impactSoft_heavy_002.ogg'), 0, 0.18), 0.0, 0.8),
                   (click(0.008, 600, 3000, 640 + i), 0.0, 0.4), (thump(120, 55, 0.16, 18, 1.8), 0.0, 0.6), (debris(0.15, 4, 645 + i, 600, 2500), 0.01, 0.25)])
        out['darbe_donuk_%d' % (i + 1)] = cut(lp(x, 3000), 0.22, 0.03)
    # ---- savuruş hazırlığı: ağır savuruş öncesi tutuşta kısa nefes / hava çekilişi (120 ms, kısık).
    for i in range(2):
        x = whoosh(0.12, 500 + 100 * i, 3500, 0.88, seed=650 + i, q=0.9, k_up=1.6) * 0.8 + rev_swell(0.12, 1500, 6000, 655 + i, 5.0) * 0.3
        out['savur_hazirlik_%d' % (i + 1)] = fade(x, 0.005, 0.015)
    return out


# ------------------------------------------------------------ patlama (kademeli)
def explosion(seed=700, big=False, far=False):
    """(a) 5 ms tık + çatırtı geçişi t=0, (b) 50-70 Hz alt bas gümbürtü t=+15 ms (150 ms'de perde düşer),
    (c) moloz / çakıl kuyruğu 0.6-1.0 s (seyrek çıtırtılar). big: 1.4 s, daha derin; far: ekran dışı, boğuk."""
    B = 0.02 if big else 0.015
    clk = click(0.005, 1500, 14000, seed, k=900)
    crack = mix(bp(noise(0.08, seed=seed + 1), 500, 7000) * exp_env(0.08, 40), distort(bp(noise(0.05, seed=seed + 2), 200, 4000), 4) * exp_env(0.05, 60) * 0.6,
                trim(KI('impactPlate_heavy_00%d.ogg' % (seed % 5)), 0, 0.08) * 0.5)
    if big:
        sub = boom_sub(58, 38, 0.2, 1.0, 5.0, 0.004, 2.0)
        mid = thump(170, 55, 0.3, 10, 2.8)
        whump = thump(120, 40, 0.4, 5, 2.4)  # ikinci dalga
        rum = rumble(1.3, 140, 2.2, seed + 3)
        deb = debris(1.2, 26, seed + 4, 900, 6000)
        crk = crackle(0.9, 14, seed + 5, 1500, 7000)
        low = bp(noise(0.7, seed=seed + 6), 150, 600) * exp_env(0.7, 5)
        parts = [(clk, 0.0, 1.0), (crack, 0.0, 1.5), (mid, B, 1.4), (sub, B, 0.3), (whump, 0.09, 0.12), (low, B, 0.3),
                 (rum, B + 0.02, 0.25), (deb, 0.08, 0.55), (crk, 0.12, 0.35)]
        x = room(glue(build(parts), 2.0), 1.0, 0.15, 4000)
        return cut(x, 1.4, 0.08)
    sub = boom_sub(70, 48, 0.15, 0.6, 6.0, 0.004, 1.8)
    mid = thump(200, 70, 0.2, 14, 2.8)
    rum = rumble(0.9, 170, 3.5, seed + 3)
    deb = debris(0.9, 14, seed + 4, 900, 6000)
    crk = crackle(0.7, 10, seed + 5, 1500, 7000)
    low = bp(noise(0.5, seed=seed + 6), 150, 600) * exp_env(0.5, 6)
    if far:
        # uzak: tık yok, çatırtı boğuk ve yumuşak başlar, gümbürtü uzun, büyük oda, 700 Hz üstü kesik
        crack_f = lp(crack, 500) * env(0.08, a=0.02, d=0.05, r=0.01)
        sub_f = boom_sub(62, 44, 0.2, 1.0, 3.0, 0.025, 1.4)
        parts = [(crack_f, 0.0, 0.8), (sub_f, B, 1.0), (lp(mid, 400) * 0.7, B + 0.01, 0.8), (rumble(1.2, 140, 2.0, seed + 7), B, 0.9),
                 (lp(deb, 700), 0.1, 0.4), (low * 0.6, B, 0.4)]
        x = lp(build(parts), 700)
        x = reverb(x, 1.6, 0.4, lp=900, seed=seed)
        return cut(x, 1.3, 0.1, 0.004)
    parts = [(clk, 0.0, 1.0), (crack, 0.0, 1.5), (mid, B, 1.4), (sub, B, 0.35), (low, B, 0.35), (rum, B + 0.02, 0.3), (deb, 0.06, 0.5), (crk, 0.08, 0.3)]
    x = room(glue(build(parts), 2.0), 0.8, 0.14, 4000)
    return cut(x, 1.05, 0.06)


def explosions():
    out = {}
    for i in range(3):
        out['patlama_%d' % (i + 1)] = explosion(700 + 10 * i)
    out['patlama'] = out['patlama_1']
    out['patlama_buyuk'] = explosion(740, big=True)
    out['patlama_uzak'] = explosion(750, far=True)
    return out


# ------------------------------------------------------------ yıldırım
def thunder():
    out = {}
    # ---- çatırtı (beyaz kare anı): 30 ms ön cızırtı -> yırtılan parlak çatlak (60-120 ms)
    P = ONSET['simsek_catirti']
    for i in range(2):
        siz = grains(P, 10, 800 + i, 4000, 12000, 0.002, 0.006, 0.6) + bp(noise(P, seed=805 + i), 3000, 12000) * np.linspace(0.1, 1.0, int(P * SR)) ** 2 * 0.5
        tear = distort(sweep(2600 - 300 * i, 700, 0.09, wave='saw'), 3.0) * exp_env(0.09, 30) * 0.5
        x = build([(siz, 0.0, 0.3),
                   (click(0.006, 3000, 16000, 810 + i), P, 1.0), (bp(noise(0.1, seed=815 + i), 1500, 14000) * exp_env(0.1, 28), P, 1.0),
                   (tear, P, 1.0), (trim(pitch(KI('impactPlate_light_00%d.ogg' % (i * 2)), 1.6), 0, 0.08), P, 0.5),
                   (thump(300, 90, 0.08, 35, 1.5), P, 0.4), (bp(noise(0.1, seed=820 + i), 500, 3000) * exp_env(0.1, 25), P + 0.002, 0.5),
                   (crunch(0.05, 825 + i, 800, 6000, 3.0, 200), P + 0.003, 0.5)])
        out['simsek_catirti_%d' % (i + 1)] = cut(room(x, 0.3, 0.08, 6000), P + 0.13, 0.03)
    # ---- gök gürlemesi: 40-120 Hz ağırlıklı katmanlı gürültü, yavaş sönüm, iki ikincil yuvarlanma
    for i, (dur, rolls, fpk) in enumerate(((2.0, ((0.55, 0.6, 0.12), (1.2, 0.45, 0.18)), 70), (2.5, ((0.7, 0.55, 0.15), (1.5, 0.5, 0.22)), 60))):
        n = int(dur * SR)
        t = t_axis(dur)
        rng = np.random.default_rng(840 + i)
        e = np.exp(-1.6 * t)
        for (tc, g, w) in rolls:
            e += g * np.exp(-((t - tc) / w) ** 2)
        e *= np.minimum(1.0, t / 0.03)  # gürleme çatırtıdan sonra gelir: 30 ms yumuşak giriş
        m1 = np.abs(lp(rng.standard_normal(n), 5)); m1 /= np.max(m1) + 1e-9
        m2 = np.abs(lp(rng.standard_normal(n), 9)); m2 /= np.max(m2) + 1e-9
        base = fft_filter(noise(dur, seed=845 + i), hi=170, peak=fpk, q=1.5, slope=1.5) * (0.6 + 0.4 * m1)
        mid = bp(noise(dur, seed=850 + i), 90, 420) * (0.5 + 0.5 * m2) * 0.5
        grit = distort(base * 2.0, 2.5) * 0.4
        x = (base + mid + grit) * e
        x = reverb(x, 1.8, 0.3, lp=1200, seed=855 + i)
        out['gok_gurleme_%d' % (i + 1)] = cut(x, dur + 0.4, 0.3, 0.0)
    # ---- cızırtı (ön ipucu döngüsü, 2.5 s, kısık): elektrik hışırtısı + seyrek çıtırtılar + 100 Hz uğultu
    dur = 2.5
    n = int(dur * SR)
    rng = np.random.default_rng(860)
    m = np.abs(lp(rng.standard_normal(n), 12)); m /= np.max(m) + 1e-9
    hiss = bp(noise(dur, seed=861), 2500, 9000) * (0.4 + 0.6 * m)
    crk = grains(dur, 70, 862, 3000, 11000, 0.002, 0.008)
    hum = bp(np.sign(sine(100, dur)) + 0.5 * np.sign(sine(150, dur)), 600, 2600) * (0.5 + 0.5 * np.abs(lp(rng.standard_normal(n), 3)) / 3.0) * 0.15
    out['simsek_sizirti_dongu'] = loop_xf(mix(hiss * 0.5, crk * 0.6, hum), 0.3)
    return out


# ------------------------------------------------------------ yer sarsıntısı
def shockwaves():
    out = {}
    # ---- sarsıntı: derin güm + çakıl saçılması (0.55 s)
    x = build([(click(0.01, 300, 2500, 900, k=600), 0.0, 0.5), (trim(KI('impactSoft_heavy_004.ogg'), 0, 0.2), 0.0, 0.8),
               (trim(pitch(KI('impactPlate_heavy_002.ogg'), 0.6), 0, 0.3), 0.0, 0.35), (thump(85, 30, 0.4, 8, 2.8), 0.0, 0.7),
               (trim(KI('impactPunch_heavy_001.ogg'), 0, 0.2), 0.0, 0.8),
               (sub_drop(60, 42, 0.35, 7, 1.0, 0.4), 0.004, 1.0), (rumble(0.5, 150, 6, 901), 0.0, 0.5),
               (debris(0.5, 22, 902, 900, 5000), 0.02, 0.55), (grind(0.3, 150, 1500, 40, 903), 0.03, 0.25)])
    out['sarsinti'] = cut(room(glue(x, 2.0), 0.5, 0.12), 0.6, 0.05)
    # ---- büyük sarsıntı: daha derin, ikinci dalga, uzun moloz (1.1 s)
    x = build([(click(0.012, 250, 2000, 910, k=500), 0.0, 0.5), (trim(KI('impactSoft_heavy_001.ogg'), 0, 0.25), 0.0, 0.8),
               (trim(pitch(KI('impactPlate_heavy_004.ogg'), 0.55), 0, 0.4), 0.0, 0.4), (thump(70, 24, 0.8, 5, 3.0), 0.0, 0.5),
               (trim(KI('impactPunch_heavy_003.ogg'), 0, 0.22), 0.0, 0.9),
               (sub_drop(52, 36, 0.6, 5.0, 1.0, 0.3), 0.004, 1.0), (thump(60, 30, 0.5, 6, 2.4), 0.14, 0.25),
               (rumble(1.0, 130, 3, 911), 0.0, 0.55), (debris(1.0, 34, 912, 800, 5000), 0.03, 0.55), (grind(0.6, 120, 1200, 32, 913), 0.05, 0.15),
               (bp(noise(0.6, seed=914), 150, 600) * exp_env(0.6, 5), 0.0, 0.3)])
    out['sarsinti_buyuk'] = cut(room(glue(x, 2.2), 0.8, 0.18), 1.1, 0.08)
    return out


def build_all():
    out = {}
    for fn in (hits, explosions, thunder, shockwaves):
        out.update(fn())
    return out


if __name__ == '__main__':
    for k, v in sorted(build_all().items()):
        print('%-24s %.3fs' % (k, len(v) / SR))
