"""v37 sesleri: KILIÇ ÇARPIŞMASI kritik + duyulur ölüm "dışşkk"ı.
İstek (oyuncu): "kritik sesi metal değil, tencere / tava vurmak gibi; KILIÇ ÇARPIŞMASI istiyorum" ve "öldürünce 'dışkkkkk' sesi
gelmiyor, Dead Cells'e yakın olsun" (özgün: hiçbir oyunun sesi kullanılmadı; sentez + yerel CC0 kayıtlar).

Neden tava gibiydi (v35): çan / plaka kip oranları (1, 1,18, 1,5, 2, 2,5 ...) sık ve uyumluya yakın dizilir, temel 2-2,7 kHz,
üstüne ~1 kHz "klang" gövdesi ve 0,5-0,8 sn sönüş: kulak bunu kalın, gövdeli bir kap (tencere / tava) çınlaması olarak duyar.
Kılıç çarpışmasında enerjinin çoğu 2,5-10 kHz'tedir: iki ince çelik çubuk (bıçak) çarpışır; ince çubuğun serbest-serbest
eğilme kipleri SEYREK ve inharmoniktir (1 : 2,76 : 5,40 : 8,93), kısa sönerler; ardından bıçakların birbirine sürtünüp
kaydığı 80-150 ms'lik "şiing" sıyırması gelir, en sonda çok ince, uzun, sessiz bir pırıltı kalır. 500 Hz altı neredeyse boş.

Kritik (darbe_kritik_1..4, darbe_kritik = en iyi çeşit): (1) 2 ms tık + Kenney impactMetal_light (perde yukarı, 900 Hz üstü:
gerçek çelik geçişi, gövdesi atılmış); (2) iki bıçak: ince çubuk kipleri (temel 2,6-3,6 kHz), 0,12-0,35 sn; (3) tiz pırıltı:
4-9 kHz'te seyrek kısa kipler, sessiz uzun kuyruk; (4) sıyırma: OGA RPG Sound Pack sword-unsheathe (gerçek kın / bıçak sürtünmesi,
2 kHz üstü, 110 ms) + sentez sıyırma 9 → 4,5 kHz; (5) yalnızca erken yansımalı minik oda; sonda 700 Hz'lik dik alçak kesim.
Künt kritik (darbe_kritik_kunt_1..3): aynı çelik ama bıçaklar biraz kalın (temel x0,8), daha sert geçiş, kısa "çank" (900 Hz
üstü gürültü vuruşu, 25 ms) — tava gövdesi yok. olum_vurus_1..2: kısa (0,4 sn), biraz kısık çarpışma (öldürüş "dışşkk"ını örtmesin).

Ölüm (vahset_patla_1..4, vahset_patla_agir_1..3): yüksek, vurucu ıslak patlama ~0,35-0,45 sn: "dı" (tık + Kenney impactPunch +
alt güm), "ış" (ıslak şapırtı + Kenney impactSoft + 2 kHz → 600 Hz inen ıslak "şlık" bandı + sıkışık çatırtı), "şşkk" (tiz
hışırtı kuyruğu, sonunda zerre çıtırtısı). v36'dan +2 dB ve daha çıtırtılı.

Kullanım: python tools/audiogen/v37.py                  (dosyaları yazar, sfx.json'u günceller)
          python tools/audiogen/v37.py --olc <klasör> <eski_klasör>  (spektrogram + ağırlık merkezi, eski / yeni)"""
import os
import sys
import json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, t_axis, exp_env, noise, distort, hp, lp, bp, master, write_wav, loudness, fft_filter
from layer import KI, load, trim, build, pitch
from pro import click
from impact import cut, crunch
from v26 import asat, transient, ny_comp, body
from v27 import scrape
import v35
import v36

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'audio', 'sfx')
TARGET = {'darbe_kritik': -6.5, 'darbe_kritik_kunt': -6.5, 'olum_vurus': -9.0, 'vahset_patla': -6.0, 'vahset_patla_agir': -5.0}
BAR = (1.0, 2.756, 5.404, 8.933)          # ince çubuğun (bıçak) serbest-serbest eğilme kipleri
UNSH = 'rpgpack/RPG Sound Pack/battle/sword-unsheathe%s.wav'


def _n(x):
    return x / (np.max(np.abs(x)) + 1e-9)


def blade(f0, dur, t60, seed, bend=0.012, g=(1.0, 0.55, 0.3, 0.16)):
    """İnce bıçak çınlaması: seyrek inharmonik çubuk kipleri, üst kipler daha kısa; her kip iki kola ayrılır (pırıltı)."""
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    x = np.zeros(len(t))
    pb = 1.0 + bend * np.exp(-t * 60.0)
    for j, (r, gg) in enumerate(zip(BAR, g)):
        f = f0 * r * (1.0 + rng.uniform(-0.004, 0.004))
        if f > SR * 0.45:
            continue
        k = 6.91 / (t60 / (1.0 + 0.6 * j))
        for side, w in ((-0.5, 0.55), (0.5, 0.45)):
            db = rng.uniform(5.0, 11.0)
            ph = 2 * np.pi * np.cumsum((f + side * db) * pb) / SR
            x += np.sin(ph + rng.uniform(0, 6.28)) * np.exp(-k * t) * gg * w
    a = int(0.0005 * SR)
    x[:a] *= np.linspace(0, 1, a)
    return x


def shimmer(dur, seed, n=7, lo=4200.0, hi=9500.0, t60=(0.15, 0.9)):
    """Tiz pırıltı: seyrek, kısa-orta sönüşlü ince kipler; biri uzun ve çok sessiz (çarpışmanın havada kalan "iiiin"i)."""
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    x = np.zeros(len(t))
    for i in range(n):
        f = rng.uniform(lo, hi)
        tt = rng.uniform(*t60)
        g = rng.uniform(0.25, 0.6) * (0.35 if tt > 0.5 else 1.0)
        x += np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) * np.exp(-6.91 / tt * t) * g
    return x


def room(x, seed):
    """Minik oda: yalnızca erken yansımalar (2-14 ms), tiz (yansımalar 1,5 kHz üstü): gövde katmaz."""
    rng = np.random.default_rng(seed)
    y = x.copy()
    h = hp(x, 1500)
    for ms, g in ((2.3, 0.16), (5.1, 0.12), (8.7, 0.08), (13.9, 0.05)):
        d = int(ms * 0.001 * SR * (1 + rng.uniform(-0.05, 0.05)))
        y[d:] += h[:-d] * g
    return y


def steel_hit(i, heavy=False):
    """Gerçek çelik geçişi: Kenney impactMetal_light (perde yukarı), gövdesi 900 Hz altından kesilmiş."""
    f = ('impactMetal_light_000.ogg', 'impactMetal_light_002.ogg', 'impactMetal_light_003.ogg', 'impactMetal_light_004.ogg')[i % 4]
    x = trim(pitch(KI(f), 1.35 if not heavy else 1.12), 0, 0.07 if not heavy else 0.05, 0.04)
    return fft_filter(x, lo=900 if not heavy else 1100, slope=3.0)


def blade_slide(i, dur=0.11, lo=2000.0):
    """Gerçek sıyırma: sword-unsheathe kaydının en parlak bölümü (2 kHz üstü), kısa."""
    k = i % 5
    x = load(UNSH % ('' if k == 0 else str(k + 1)))
    e = np.convolve(np.abs(hp(x, lo)), np.ones(441) / 441, 'same')
    s = max(0, int(np.argmax(e)) - int(0.01 * SR))
    y = hp(x[s:s + int(dur * SR)], lo)
    return _n(y) * exp_env(len(y) / SR, 3.5 / dur)


CV = [   # f0 (bıçak A), f0 oranı (bıçak B), sönüş, sıyırma (baş, son, süre), tohum
    dict(f0=2950.0, rb=1.19, t60=0.32, s=(9500.0, 4600.0, 0.10), seed=1),
    dict(f0=3350.0, rb=1.13, t60=0.26, s=(10500.0, 5200.0, 0.12), seed=2),
    dict(f0=2650.0, rb=1.27, t60=0.36, s=(9000.0, 4300.0, 0.09), seed=3),
    dict(f0=3600.0, rb=1.09, t60=0.24, s=(11000.0, 5600.0, 0.14), seed=4),
]


def clash(v, i, heavy=False, dur=0.62):
    f0 = v['f0'] * (0.8 if heavy else 1.0)
    s0, s1, sd = v['s']
    sd_ = 7000 + v['seed'] * 10 + (5 if heavy else 0)
    parts = [
        (click(0.002, 3000, 18000, sd_), 0.0, 1.0),
        (steel_hit(i, heavy), 0.0, 0.8 if not heavy else 1.0),
        (blade(f0, dur, v['t60'] * (1.15 if heavy else 1.0), sd_ + 1), 0.0004, 0.7),
        (blade(f0 * v['rb'], dur, v['t60'] * 0.7, sd_ + 2), 0.0011, 0.45),   # karşı bıçak
        (shimmer(dur, sd_ + 3), 0.001, 0.32),
        (blade_slide(i), 0.004, 0.55),
        (scrape(sd, s0 * (0.88 if heavy else 1.0), s1, sd_ + 4, 2300.0), 0.003, 0.35),
    ]
    if heavy:
        # "çank": kısa, sert, gövdesiz gürültü vuruşu (künt silahın ağırlığı; tava gibi uzun orta-alt çınlama yok)
        parts.append((asat(fft_filter(noise(0.03, seed=sd_ + 5), lo=900, hi=7000) * exp_env(0.03, 130.0), 3.0, 0.1), 0.0, 0.7))
        parts.append((v35.snaps(0.03, 8, sd_ + 6, 2500.0, 9000.0, 0.6), 0.0, 0.4))
    x = build(parts)
    x = transient(_n(x), attack=1.6, sustain=-0.05)
    x = ny_comp(x, ratio=2.5, th_db=-22.0, mix=0.3)
    x = distort(_n(x), 1.1)
    x = room(x, sd_)
    x = fft_filter(x, lo=700 if not heavy else 600, slope=4.0)   # tencere / tava gövdesi yok
    return cut(x, dur, 0.15)


def dissk(i, heavy=False):
    """Dead Cells tarzı ölüm "dışşkk": vurucu, ıslak, çıtırtılı patlama + tiz hışırtı kuyruğu."""
    punch = ('impactPunch_heavy_000.ogg', 'impactPunch_heavy_002.ogg', 'impactPunch_heavy_003.ogg', 'impactPunch_heavy_004.ogg')[i % 4]
    soft = ('impactSoft_heavy_001.ogg', 'impactSoft_heavy_003.ogg', 'impactSoft_heavy_004.ogg', 'impactSoft_heavy_000.ogg')[i % 4]
    dur = 0.46 if heavy else 0.38
    tail = 0.34 if heavy else 0.28
    s = 7700 + i * 11 + (50 if heavy else 0)
    kk = 0.2 + 0.02 * i + (0.05 if heavy else 0.0)
    # "ış": 2 kHz → 600 Hz inen ıslak bant (ağız "ış" sesi gibi ıslak sıkışma)
    nsq = int(0.09 * SR)
    src = noise(0.1, seed=s + 9)[:nsq]
    sq = np.zeros(nsq)
    ed = np.linspace(0, nsq, 9).astype(int)
    for k in range(8):
        fc = 2100.0 * (600.0 / 2100.0) ** ((k + 0.5) / 8)
        sq[ed[k]:ed[k + 1]] = bp(src, fc * 0.7, fc * 1.5)[ed[k]:ed[k + 1]]
    sq = sq * exp_env(0.09, 25.0)
    x = build([
        (click(0.003, 1500, 16000, s), 0.0, 1.0),
        (asat(trim(pitch(KI(punch), 0.85 + 0.04 * i - (0.1 if heavy else 0.0)), 0, 0.11, 0.04), 3.5, 0.2), 0.0, 0.95),
        (trim(pitch(KI(soft), 0.72), 0, 0.14, 0.05), 0.002, 0.6),
        (body(140.0 - 10 * i - (30 if heavy else 0), 50.0, 0.1 if not heavy else 0.18, 24.0 if not heavy else 13.0, 5.0), 0.0, 0.3 if not heavy else 0.5),
        (asat(sq, 2.5, 0.1), 0.006, 0.8),
        (v35.wet(0.18, s + 1, 350.0, 4500.0, 260.0, 13.0), 0.004, 1.0),                     # ıslak şapırtı
        (crunch(0.07, s + 4, 700, 5500, 6.0, 200.0), 0.008, 0.6),                          # çıtırtılı sıkışma
        (v35.snaps(0.06, 14 + 3 * i, s + 5, 1500.0, 7000.0, 0.8), 0.01, 0.55),
        (v36.hiss(tail, s + 2, 2800.0, 4.6 / tail), 0.03, 1.05 if not heavy else 1.15),      # "şşş"
        (v35.snaps(0.06, 10 + 3 * i, s + 3, 2000.0, 9000.0, 0.8), kk, 0.7),                # "kk": zerreler çarpar
        (crunch(0.04, s + 6, 1200, 7000, 5.0, 180.0), kk + 0.005, 0.45),
    ])
    x = fft_filter(x, lo=95 if not heavy else 75, slope=2.0)   # alt güm payı sınırlı: yükseklik "ış / şşkk"a kalsın
    x = transient(_n(x), attack=2.0, sustain=-0.1)
    x = ny_comp(_n(x), ratio=4.0, th_db=-22.0, mix=0.5)
    x = distort(_n(x), 1.35)
    return cut(x, dur, 0.07)


BEST = 0


def build_all():
    # v37c: kritik (darbe_kritik*, olum_vurus*) artık v37c.py'de (örs KANG, gerçek kayıt); buradaki clash() yalnızca
    # tarihçe / --olc ölçümü için duruyor, dosya üretmez.
    out = {}
    for i in range(4):
        out['vahset_patla_%d' % (i + 1)] = dissk(i)
    for i in range(3):
        out['vahset_patla_agir_%d' % (i + 1)] = dissk(i, True)
    return out


def target_for(name):
    pre = name.rstrip('0123456789').rstrip('_')
    return TARGET.get(pre, -12.0)


def stats(x):
    y = x[:int(0.35 * SR)]
    f = np.fft.rfftfreq(len(y), 1 / SR)
    P = np.abs(np.fft.rfft(y)) ** 2
    tot = P.sum() + 1e-12
    return {'merkez_hz': int((f * P).sum() / tot),
            '<500Hz_%': round(100 * P[f < 500].sum() / tot, 2),
            '300-1500Hz_%': round(100 * P[(f >= 300) & (f < 1500)].sum() / tot, 1),
            '2.5-9kHz_%': round(100 * P[(f >= 2500) & (f < 9000)].sum() / tot, 1),
            'yukseklik': round(loudness(x), 1), 'sure': round(len(x) / SR, 2)}


def measure(outdir, olddir):
    import soundfile as sf
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows = []
    for nm in ('darbe_kritik_1', 'darbe_kritik_2', 'darbe_kritik_3', 'darbe_kritik_kunt_1', 'vahset_patla_1', 'vahset_patla_agir_1'):
        for tag, d in (('eski', olddir), ('yeni', A)):
            p = os.path.join(d, nm + '.wav')
            if os.path.exists(p):
                x, sr = sf.read(p, always_2d=True)
                rows.append((tag + ' ' + nm, x.mean(axis=1)))
    lines = []
    fig, ax = plt.subplots(len(rows) // 2, 2, figsize=(12, 2.6 * (len(rows) // 2)))
    for k, (nm, x) in enumerate(rows):
        m = stats(x)
        lines.append('%-28s %s' % (nm, m))
        a = ax[k // 2, k % 2]
        a.specgram(x + 1e-9, NFFT=1024, Fs=SR, noverlap=768, cmap='magma', vmin=-120)
        a.set_ylim(0, 16000)
        a.set_title('%s  merkez %d Hz  <500Hz %.2f%%' % (nm, m['merkez_hz'], m['<500Hz_%']), fontsize=9)
    plt.tight_layout()
    png = os.path.join(outdir, 'spektrogram_eski_yeni.png')
    plt.savefig(png, dpi=85)
    open(os.path.join(outdir, 'olcum.txt'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print('png:', png)


def main():
    if '--olc' in sys.argv:
        k = sys.argv.index('--olc')
        measure(sys.argv[k + 1], sys.argv[k + 2])
        return
    allx = build_all()
    mp = os.path.join(A, 'sfx.json')
    meta = json.load(open(mp, encoding='utf-8'))
    for name, x in sorted(allx.items()):
        y = master(x, target_for(name))
        write_wav(os.path.join(A, name + '.wav'), y, SR, None)
        meta[name] = {'loop': False, 'len': round(len(y) / SR, 3), 'hedef_db': target_for(name)}
    json.dump(meta, open(mp, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('yazıldı:', len(allx))


if __name__ == '__main__':
    main()
