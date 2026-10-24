"""v43 sinematik müzik ipuçları ve sesleri (Sinema.gd çekim listeleriyle eş zamanlı).

Müzik (assets/audio/music, 32 kHz mono, döngüsüz):
  sinema_giris  açılış (~82 sn): gırtlak (hömey) dem sesi + ney + kopuz + kam davulu; çekim başları ve "vurus" anları
                data/sinema/giris.json'dan okunur — kesmeler vuruşa, beş makas kesimi beş davul / çelik darbesine, başlık
                kartı büyük vuruşa (sub düşüşü + gong + kopuz akoru) denk gelir. Erlik'te dem bozulur (kara gırtlak),
                düşüşte müzik çekilir (yalnız rüzgâr + tek ney), Umay'da sıcak ney ezgisi döner, yolda davul hızlanır.
  sinema_son    son (~80 sn): örgüler örülürken kopuz pırıltısı, zincir kırılınca aydınlık vuruş, tan söktüğünde davullu
                halk ezgisi; jenerik boyunca sakin ney + kopuz.
Sesler (assets/audio/sfx): sin_ruzgar, sin_parilti, sin_davul, sin_ates, sin_gumbur, sin_erlik, sin_zincir, sin_makas,
  sin_dusus, sin_kus, sin_kanat, sin_vurus, sin_muhur, sin_orgu, sin_kart, sin_kirilma.
Yeniden üretim: python tools/audiogen/v43_sinema.py [muzik] [ses] [ad...]
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, t_axis, env, exp_env, noise, fft_filter, sine, sweep, pluck, reverb, delay, fade, write_wav, master, voice, lp, bp, hp
from pro import kopuz, note, bell, crackle, whoosh, metal_ring, thump, click, room
from turku import ney, mey
from impact import sub_drop, rev_swell, crunch, boom_sub
from v40_ui import brush_sweep, paper_rustle

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
MUS = os.path.join(ROOT, 'assets', 'audio', 'music')
SFX = os.path.join(ROOT, 'assets', 'audio', 'sfx')
MSR = 32000


def resample(x, sr_in=SR, sr_out=MSR):
    n = int(len(x) * sr_out / sr_in)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def put(dst, src, at=0.0, g=1.0):
    i = int(at * SR)
    if i < 0:
        src = src[-i:]
        i = 0
    m = min(len(src), len(dst) - i)
    if m > 0:
        dst[i:i + m] += src[:m] * g


def zaman(json_ad):
    d = json.load(open(os.path.join(ROOT, 'data', 'sinema', json_ad + '.json'), encoding='utf-8'))
    bas, t = {}, 0.0
    vur = []
    for c in d['cekimler']:
        bas[c['id']] = t
        for v in c.get('vurus', []):
            vur.append(t + v)
        t += c['sure']
    return bas, vur, t


# ====================================================================== çalgılar
def hoomey(f0, dur, grit=0.0, seed=0, whistle=0.35):
    """Gırtlak dem sesi (hömey / kargıra): biçimlendiricili alçak ses + üst armonikte gezinen ıslık."""
    v = voice(f0, dur, vowels=('o', 'u', 'o', 'a', 'o'), size=1.7, breath=0.08, grit=grit, jitter=0.006, seed=seed, sub=0.4 if grit > 0 else 0.0)
    t = t_axis(dur)
    # ıslık: 6.-12. armonikler arasında yavaşça gezinen dar bant
    h = 8 + 2.5 * np.sin(2 * np.pi * t / 9.0 + seed)
    ph = 2 * np.pi * np.cumsum(f0 * np.round(h * 2) / 2) / SR
    wh = np.sin(ph) * whistle * 0.12
    wh = fft_filter(wh, hi=2500, slope=1.0)
    return lp(v, 1800) + wh


def davul(g=1.0, f0=95.0, f1=46.0, dur=1.1, seed=0):
    """Kam davulu: geniş çerçeveli derin vuruş, deri hışırtısı, çıngırak."""
    x = sweep(f0, f1, dur, curve=0.45) * exp_env(dur, 5.0)
    skin = fft_filter(noise(dur, seed=seed), hi=600, slope=1.2) * exp_env(dur, 16.0) * 0.4
    rattle = bp(noise(0.35, seed=seed + 1), 3000, 8000) * exp_env(0.35, 14.0) * 0.06
    out = np.zeros(int(dur * SR))
    out[:len(x)] += x + skin
    out[:len(rattle)] += rattle
    return out * g


def dev_vurus(dur=5.0):
    """Başlık / kırılma vuruşu: dev davul + sub düşüşü + gong + parlak akor."""
    out = np.zeros(int(dur * SR))
    put(out, davul(1.4, 80, 36, 2.0, 11), 0.0)
    put(out, sub_drop(70, 30, 2.5, k=2.5, g=1.0), 0.0, 0.8)
    t = t_axis(dur)
    gong = sum(np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 0.7 * t)) * exp_env(dur, k) * g
               for f, k, g in ((110 * 1.0, 0.9, 0.3), (110 * 2.02, 1.2, 0.2), (110 * 2.76, 1.6, 0.14), (110 * 4.1, 2.2, 0.08)))
    out += gong * 0.6
    out += bp(noise(dur, seed=12), 2500, 9000) * exp_env(dur, 1.6) * 0.08
    return out


def kopuz_akor(notalar, dur=3.0, g=0.3, aralik=0.035, seed=0):
    out = np.zeros(int(dur * SR))
    for i, n in enumerate(notalar):
        put(out, kopuz(note(n), dur - i * aralik, 0.6, seed=seed + i, decay=0.998), i * aralik, g)
    return out


def ney_ezgi(notalar, sure_k=1.0, g=0.3, seed=0):
    """notalar: [(ad, sure), ...] ad None: sus. Legato ney (notalar hafif örtüşür)."""
    tot = sum(d for _, d in notalar) * sure_k + 1.0
    out = np.zeros(int(tot * SR))
    t = 0.0
    for i, (n, d) in enumerate(notalar):
        d *= sure_k
        if n:
            put(out, ney(note(n), d + 0.25, SR, seed=seed + i, g=1.0), t, g)
        t += d
    return out


def pad(freqs, dur, lpf=1200, wob=0.2, seed=0):
    t = t_axis(dur)
    x = np.zeros(len(t))
    for k, f in enumerate(freqs):
        for det in (0.997, 1.003):
            x += np.sin(2 * np.pi * f * det * t + 0.4 * np.sin(2 * np.pi * (0.05 + 0.02 * k) * t + seed)) / (k + 1.5)
    x *= 1 + wob * np.sin(2 * np.pi * 0.09 * t + seed)
    return lp(x, lpf) * env(dur, a=min(2.5, dur * 0.3), d=0.1, s=1.0, r=min(2.5, dur * 0.3))


def ruzgar(dur, seed=0, lo=200, hi=1600):
    x = fft_filter(noise(dur, seed=seed), lo=lo, hi=hi, slope=1.0)
    m = fft_filter(noise(dur, seed=seed + 1), hi=0.35, slope=1.0)
    m = (m - m.min()) / (m.max() - m.min() + 1e-9)
    return x * (0.25 + 0.75 * m)


def zarf(dur, keys):
    """[(t, kazanç), ...] doğrusal kazanç eğrisi."""
    t = t_axis(dur)
    ks = np.array(keys, float)
    return np.interp(t, ks[:, 0], ks[:, 1])


# ====================================================================== AÇILIŞ
def sinema_giris():
    B, V, T = zaman('giris')
    dur = T + 3.0
    out = np.zeros(int(dur * SR))
    e_ = B['erlik']
    k_ = B['kirki']
    z_ = B['zincir']
    d_ = B['dusus']
    u_ = B['umay']
    y_ = B['yol']
    b_ = B['baslik']
    # --- dem: A1 hömey; Erlik'te kararır (kara gırtlak), düşüşte çekilir, yolda yükselir, başlıkta keser
    dem = hoomey(55.0, dur, grit=0.0, seed=1)
    dem_g = zarf(dur, [(0, 0), (3, 0.35), (B['gunana'], 0.3), (B['toren'], 0.4), (e_, 0.25), (k_, 0.2), (z_, 0.4), (d_ - 0.5, 0.35), (d_ + 1.0, 0.0),
                       (u_ + 2.0, 0.0), (y_, 0.2), (b_ - 0.1, 0.65), (b_ + 0.5, 0.0), (dur, 0.0)])
    out += dem * dem_g
    kara = hoomey(41.2, k_ - e_ + 2.0, grit=1.4, seed=2, whistle=0.0)
    put(out, kara * env(len(kara) / SR, a=0.4, d=0.1, s=1.0, r=1.5), e_, 0.55)
    # --- rüzgâr
    out += ruzgar(dur, 3) * zarf(dur, [(0, 0.0), (1.0, 0.25), (B['gunana'], 0.12), (B['toren'], 0.05), (d_, 0.3), (d_ + 3, 0.4), (u_, 0.12), (y_, 0.25), (b_, 0.1), (dur, 0.0)])
    # --- ney: Ulu Kayın ezgisi (Hüseyni, A), Gün Ana yükselişi, Umay'ın ninnisi, düşüşte tek alçalan nota
    put(out, ney_ezgi([('A4', 2.0), ('C5', 1.0), ('B4', 1.0), ('A4', 1.4), ('G4', 0.8), ('A4', 2.4)], g=0.24, seed=10), 1.4)
    put(out, ney_ezgi([('E4', 1.0), ('A4', 1.0), ('B4', 0.7), ('C5', 0.7), ('D5', 1.2), ('E5', 2.2), ('D5', 0.6), ('E5', 1.6)], g=0.24, seed=20), B['gunana'] + 0.8)
    put(out, ney_ezgi([('E5', 1.8), ('D5', 0.6), ('C5', 0.6), ('B4', 0.6), ('A4', 2.4)], g=0.2, seed=30), d_ + 0.6)
    put(out, ney_ezgi([('A4', 1.2), ('B4', 0.6), ('C5', 1.2), ('B4', 0.6), ('A4', 0.8), ('E4', 1.6), ('G4', 0.8), ('A4', 2.2)], g=0.26, seed=40), u_ + 1.4)
    put(out, ney_ezgi([('E5', 1.2), ('A5', 4.5)], g=0.22, seed=50), b_ + 2.4)
    # --- kopuz: Gün Ana'da pırıltı arpejleri, törende ostinato, Umay'da arpej
    ar = ['A3', 'E4', 'A4', 'C5', 'E5', 'C5', 'A4', 'E4']
    for i in range(18):
        put(out, kopuz(note(ar[i % 8]), 1.6, 0.5, seed=60 + i, decay=0.997), B['gunana'] + 1.6 + i * 0.4, 0.12)
    ost = ['A2', 'A3', 'E3', 'A3', 'G3', 'A3', 'E3', 'C4']
    for i in range(32):
        put(out, kopuz(note(ost[i % 8]), 0.6, 0.55, seed=80 + i), B['toren'] + 0.5 + i * 0.25, 0.16 if i % 4 == 0 else 0.1)
    for i in range(20):
        put(out, kopuz(note(['A3', 'C4', 'E4', 'A4', 'B4', 'A4', 'E4', 'C4'][i % 8]), 1.4, 0.45, seed=120 + i), u_ + 3.0 + i * 0.3, 0.1)
    # --- padler
    put(out, pad([110, 164.8, 220, 246.9, 329.6], 9.5, 1400, seed=1), B['gunana'], 0.16)
    put(out, pad([55, 82.4, 110, 130.8], 8.5, 600, seed=2), z_, 0.22)
    put(out, pad([110, 164.8, 220, 277.2, 329.6], 10.0, 1600, seed=3), u_, 0.14)
    put(out, pad([110, 164.8, 220, 329.6, 440], 9.0, 2200, seed=4), b_ + 0.5, 0.2)
    # --- davullar: tören vuruşları (giris.json "vurus"), Erlik'in iki dev vuruşu, beş kesim, yolda hızlanan nabız
    for v in V:
        if B['toren'] <= v < e_:
            put(out, davul(0.55, seed=int(v * 10)), v, 1.0)
    put(out, sub_drop(62, 28, 3.0, k=1.8, g=1.0), e_, 0.9)
    put(out, davul(1.2, 70, 34, 2.0, 5), e_, 1.0)
    put(out, davul(1.0, 70, 34, 2.0, 6), e_ + 2.0, 0.8)
    put(out, rev_swell(1.0, 400, 6000, seed=7), e_ - 1.0, 0.25)
    for i, v in enumerate([x for x in V if k_ <= x < z_]):
        put(out, davul(0.9 + 0.1 * i, 90, 40, 1.2, 20 + i), v, 1.0)
        put(out, metal_ring(2400 + 180 * i, 0.9, 6, seed=30 + i), v, 0.12)
    put(out, davul(0.5, 70, 36, 1.4, 41), z_ + 0.4, 1.0)
    t = y_ + 0.5
    gap = 1.0
    while t < b_ - 0.3:
        put(out, davul(0.35 + 0.45 * (t - y_) / (b_ - y_), seed=int(t * 13)), t, 1.0)
        t += gap
        gap = max(0.22, gap * 0.86)
    put(out, rev_swell(2.6, 300, 9000, seed=8), b_ + 0.6 - 2.6, 0.4)
    # --- başlık vuruşu (başlık yazısı belirirken)
    put(out, dev_vurus(6.0), b_ + 0.6, 1.0)
    put(out, kopuz_akor(['A2', 'E3', 'A3', 'C4', 'E4', 'A4'], 4.0, 0.3, seed=200), b_ + 0.62)
    put(out, bell(note('E6'), 3.0, 1.2, 0.1), b_ + 3.3)
    y = reverb(out, 2.4, 0.22, lp=5000)[:len(out)]
    y = fade(y, 0.02, 3.0)
    return y


# ====================================================================== SON
def sinema_son():
    B, V, T = zaman('son')
    n_j = 12
    dur = T + 3.0 + n_j * 2.6 + 3.0
    out = np.zeros(int(dur * SR))
    o_, k_, y_, t_, d_ = B['sonor'], B['sonkir'], B['sonyuksel'], B['sontan'], B['sondal']
    dem = hoomey(55.0, dur, seed=5, whistle=0.5)
    out += dem * zarf(dur, [(0, 0), (3, 0.3), (k_ + 2.6, 0.35), (k_ + 2.7, 0.0), (y_, 0.15), (t_, 0.25), (d_, 0.15), (dur - 6, 0.12), (dur, 0)])
    # örgüler örülürken kopuz pırıltısı, örgüler birleşince akor
    for i in range(22):
        put(out, kopuz(note(['E4', 'A4', 'B4', 'C5', 'E5', 'B4', 'A4', 'C5'][i % 8]), 1.5, 0.5, seed=300 + i, decay=0.997), o_ + 0.8 + i * 0.2, 0.1)
    put(out, ney_ezgi([('A4', 1.4), ('B4', 0.7), ('C5', 0.7), ('E5', 2.0), ('D5', 0.8), ('C5', 1.6)], g=0.24, seed=310), o_ + 1.0)
    put(out, kopuz_akor(['A2', 'E3', 'A3', 'C#4', 'E4'], 3.5, 0.26, seed=320), o_ + 5.2)
    # zincir: kalp atışı davul, kırılınca aydınlık vuruş
    for i in range(5):
        put(out, davul(0.4 + 0.1 * i, 80, 42, 0.8, 330 + i), k_ + i * 0.55, 1.0)
    put(out, rev_swell(1.5, 500, 9000, seed=9), k_ + 2.6 - 1.5, 0.35)
    put(out, dev_vurus(6.0), k_ + 2.6, 0.9)
    put(out, kopuz_akor(['A2', 'E3', 'A3', 'C#4', 'E4', 'A4'], 4.0, 0.3, seed=340), k_ + 2.62)
    put(out, bell(note('A5'), 3.0, 1.0, 0.12), k_ + 2.7)
    # yükseliş: A majör'e (Hicaz'dan aydınlığa) yükselen ney + pad
    put(out, pad([110, 138.6, 164.8, 220, 277.2], 9.0, 2000, seed=6), y_, 0.2)
    put(out, ney_ezgi([('E4', 0.8), ('A4', 0.8), ('C#5', 0.8), ('E5', 1.2), ('F#5', 0.6), ('E5', 0.6), ('A5', 3.0)], g=0.24, seed=350), y_ + 1.0)
    # tan: davullu halk ezgisi (6/8)
    step = 0.25
    tt = t_ + 0.5
    i = 0
    while tt < d_ + 1.0:
        if i % 6 == 0:
            put(out, davul(0.45, 95, 50, 0.8, 400 + i), tt, 1.0)
        elif i % 6 == 3:
            put(out, davul(0.25, 140, 80, 0.4, 400 + i), tt, 1.0)
        put(out, kopuz(note(['A3', 'E4', 'A4', 'C#5', 'B4', 'A4'][i % 6]), 0.7, 0.55, seed=500 + i), tt, 0.1)
        tt += step
        i += 1
    put(out, dev_vurus(5.0), t_ + 3.0, 0.6)
    put(out, ney_ezgi([('A4', 0.75), ('C#5', 0.75), ('E5', 1.5), ('D5', 0.75), ('C#5', 0.75), ('B4', 1.5), ('A4', 2.0)], g=0.26, seed=360), t_ + 3.2)
    # dal + jenerik: sakin ney ve kopuz, uzun
    mel = [('E5', 1.6), ('C#5', 0.8), ('B4', 0.8), ('A4', 2.4), (None, 0.8), ('B4', 0.8), ('C#5', 0.8), ('E5', 1.6), ('F#5', 0.8), ('E5', 2.4), (None, 1.2)]
    tt = d_ + 1.0
    while tt < dur - 8:
        put(out, ney_ezgi(mel, g=0.2, seed=int(tt)), tt)
        for j in range(28):
            put(out, kopuz(note(['A3', 'E4', 'A4', 'E4', 'C#4', 'E4', 'B3', 'E4'][j % 8]), 1.2, 0.45, seed=600 + j), tt + j * 0.5, 0.08)
        tt += sum(d for _, d in mel)
    put(out, pad([110, 164.8, 220, 277.2, 329.6], dur - d_, 1600, seed=7), d_, 0.12)
    y = reverb(out, 2.4, 0.22, lp=5000)[:len(out)]
    return fade(y, 0.02, 5.0)


# ====================================================================== SESLER
def s_ruzgar():
    d = 4.5
    return ruzgar(d, 701, 250, 2200) * env(d, a=0.8, d=1.5, s=0.6, r=2.0) + bp(noise(d, seed=702), 2500, 6000) * env(d, a=1.0, d=1.0, s=0.3, r=2.0) * 0.15


def s_parilti():
    d = 2.2
    out = np.zeros(int(d * SR))
    for i, n in enumerate(['E6', 'A6', 'B6', 'E7', 'C#7']):
        put(out, bell(note(n), 1.4, 3.0, 0.15), i * 0.09)
    return reverb(out, 1.6, 0.4)[:len(out)]


def s_davul():
    return room(davul(1.0, 98, 48, 1.0, 710), 0.5, 0.2)


def s_ates():
    d = 4.0
    x = lp(noise(d, seed=720), 700) * 0.35 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.7 * t_axis(d)))
    return (x + crackle(d, n=90, seed=721, lo=1500, hi=7000) * 0.5) * env(d, a=0.4, d=1.0, s=0.8, r=1.0)


def s_gumbur():
    d = 3.0
    out = lp(noise(d, seed=730), 160) * env(d, a=0.2, d=1.0, s=0.5, r=1.4) * 1.5
    put(out, sub_drop(50, 28, 2.5, k=2.0, g=0.7), 0.0)
    return out


def s_erlik():
    d = 2.6
    f = np.linspace(70, 48, int(d * SR))
    v = voice(f, d, vowels=('a', 'o', 'u'), size=2.4, breath=0.35, grit=2.2, jitter=0.05, seed=740, sub=0.8)
    return lp(v, 2200) * env(d, a=0.25, d=0.8, s=0.7, r=1.0)


def s_zincir():
    d = 1.8
    out = np.zeros(int(d * SR))
    rs = np.random.default_rng(750)
    t = 0.0
    while t < d - 0.2:
        put(out, metal_ring(rs.uniform(1800, 3600), 0.25, 18, seed=int(rs.integers(1 << 20))), t, rs.uniform(0.25, 0.5))
        put(out, click(0.01, 1500, 8000, int(rs.integers(1 << 20))), t, 0.5)
        t += rs.uniform(0.04, 0.12)
    out += lp(noise(d, seed=751), 900) * env(d, a=0.05, d=0.6, s=0.4, r=0.6) * 0.3
    return out


def s_makas():
    """Kırkı: iki çelik bıçağın sürtünüp kapanışı (şıırrk) + tok kapanma + kesilen ışığın cam gibi kırılışı."""
    d = 1.0
    out = np.zeros(int(d * SR))
    sc = bp(noise(0.12, seed=760), 3000, 9000) * np.linspace(0.3, 1.0, int(0.12 * SR)) * 0.6
    put(out, sc, 0.0)
    put(out, metal_ring(4200, 0.5, 9, seed=761), 0.11, 0.35)
    put(out, thump(220, 90, 0.12, 30, 1.2), 0.11, 0.6)
    put(out, click(0.006, 2000, 9000, 762), 0.11, 0.8)
    for i, n in enumerate(['E7', 'B6', 'G#6']):
        put(out, bell(note(n), 0.6, 6.0, 0.08), 0.13 + i * 0.03)
    return out


def s_dusus():
    d = 6.5
    x = whoosh(d, 200, 3000, 0.75, seed=770, q=0.7) * 0.8
    return x + ruzgar(d, 771, 150, 900) * env(d, a=1.0, d=2.0, s=0.7, r=2.0) * 0.6


def s_kus():
    d = 1.3
    out = np.zeros(int(d * SR))
    for i in range(3):
        f0 = 2600 + i * 300
        ch = sweep(f0, f0 * 1.5, 0.12) * env(0.12, a=0.01, d=0.08, s=0.2, r=0.03) * 0.3
        put(out, ch, 0.1 + i * 0.16)
    put(out, whoosh(0.5, 600, 4000, 0.4, seed=780) * 0.3, 0.0)
    return reverb(out, 1.0, 0.25)[:len(out)]


def s_kanat():
    d = 1.4
    out = np.zeros(int(d * SR))
    for i in range(3):
        put(out, whoosh(0.4, 300, 2500, 0.45, seed=790 + i) * 0.6, i * 0.32)
    put(out, bell(note('A5'), 1.0, 2.5, 0.06), 0.9)
    return out


def s_vurus():
    return dev_vurus(4.0)


def s_muhur():
    d = 0.7
    slap = lp(noise(0.08, seed=800), 1400) * exp_env(0.08, 34.0)
    out = np.zeros(int(d * SR))
    put(out, slap, 0.0, 0.9)
    put(out, thump(170, 62, 0.16, 15, 1.3), 0.0, 0.8)
    put(out, bp(noise(0.06, seed=801), 450, 2600) * exp_env(0.06, 50.0), 0.005, 0.5)
    return room(out, 0.4, 0.15)


def s_orgu():
    d = 3.0
    out = np.zeros(int(d * SR))
    put(out, kopuz_akor(['A3', 'E4', 'A4', 'C#5', 'E5'], 2.6, 0.3, aralik=0.07, seed=810))
    for i, n in enumerate(['A5', 'C#6', 'E6', 'A6']):
        put(out, bell(note(n), 1.6, 2.5, 0.08), 0.3 + i * 0.12)
    put(out, rev_swell(0.6, 2000, 9000, seed=811), 0.0, 0.2)
    return reverb(out, 1.8, 0.3)[:len(out)]


def s_kart():
    d = 2.5
    out = np.zeros(int(d * SR))
    put(out, davul(1.0, 80, 38, 1.6, 820), 0.0)
    put(out, brush_sweep(0.5, 821), 0.0, 0.6)
    put(out, metal_ring(1800, 1.2, 4, seed=822), 0.02, 0.12)
    return out


def s_kirilma():
    d = 3.0
    out = np.zeros(int(d * SR))
    put(out, crunch(0.12, 830, 600, 6000, 4.0, 120.0), 0.1, 0.8)
    for i in range(10):
        put(out, metal_ring(2000 + i * 260, 0.6, 10, seed=831 + i), 0.1 + i * 0.03, 0.15)
    put(out, rev_swell(0.4, 1500, 9000, seed=845), -0.3 + 0.4, 0.3)
    return out


SESLER = {'sin_ruzgar': (s_ruzgar, -20.0), 'sin_parilti': (s_parilti, -20.0), 'sin_davul': (s_davul, -15.0), 'sin_ates': (s_ates, -22.0),
          'sin_gumbur': (s_gumbur, -16.0), 'sin_erlik': (s_erlik, -15.0), 'sin_zincir': (s_zincir, -18.0), 'sin_makas': (s_makas, -15.0),
          'sin_dusus': (s_dusus, -19.0), 'sin_kus': (s_kus, -20.0), 'sin_kanat': (s_kanat, -18.0), 'sin_vurus': (s_vurus, -13.0),
          'sin_muhur': (s_muhur, -17.0), 'sin_orgu': (s_orgu, -17.0), 'sin_kart': (s_kart, -15.0), 'sin_kirilma': (s_kirilma, -14.0)}


def main(args):
    only = set(a for a in args if a not in ('muzik', 'ses'))
    do_m = 'ses' not in args or 'muzik' in args
    do_s = 'muzik' not in args or 'ses' in args
    if do_m:
        for ad, fn, db in (('sinema_giris', sinema_giris, -16.0), ('sinema_son', sinema_son, -16.5)):
            if only and ad not in only:
                continue
            y = master(fn(), db)
            y = resample(y)
            write_wav(os.path.join(MUS, ad + '.wav'), y, MSR, None)
            print(ad, round(len(y) / MSR, 2), 's')
    if do_s:
        meta_p = os.path.join(SFX, 'sfx.json')
        meta = json.load(open(meta_p, encoding='utf-8')) if os.path.exists(meta_p) else {}
        for ad, (fn, db) in SESLER.items():
            if only and ad not in only:
                continue
            y = master(fade(fn(), 0.0005, 0.05), db)
            write_wav(os.path.join(SFX, ad + '.wav'), y, SR, None)
            meta[ad] = {'loop': False, 'len': round(len(y) / SR, 3), 'hedef_db': db}
            print(ad, round(len(y) / SR, 2))
        json.dump(meta, open(meta_p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main(sys.argv[1:])
