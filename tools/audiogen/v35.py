"""v35 vahşet sesleri: parçalanma, kemik, et ve yeni METAL kritik.
İstek: "Vuruş sesleri de vahşet olsun ... kritik sesi düz METAL bir ses olsun" (Dead Cells'teki gibi ama özgün: kaynak kopyalanmadı,
tümü kipsel sentez + yerel CC0 Kenney kayıtları).

Sesler (hepsi çeşitli; Ses.gd _1.._N önekinden rastgele seçer):
  vahset_et_1..4      etli darbe: Kenney impactPunch/impactSoft (perdesi düşük) + ıslak şapırtı (süzgeçli gürültü, tanecik)
  vahset_kemik_1..4   kemik çatırtısı: hızlı tık dizisi (1-6 kHz) + Kenney impactWood_light (perde 0,7)
  vahset_olum_1..3    öldürüş patlaması: alt güm + büyük ıslak sıçrantı + kemik kırılması + Kenney impactSoft_heavy
  vahset_yirtil_1..3  ıslak yırtılma (parçalanma): gerilen lif gürültüsü (yükselen bant) + kopma tıkı + şapırtı
  vahset_dusme_1..4   parça yere düşer: tok ıslak "şlap"
  darbe_kritik_1..3   METAL kritik: bıçak-çelik "şiiing / KLANG" (aşağıya bakın); darbe_kritik = seçilen en iyi çeşit
  darbe_kritik_kunt_1..3  aynı tasarımın alçak (örs) çeşidi: künt silahta da metal

Kullanım: python tools/audiogen/v35.py            (dosyaları yazar, sfx.json'u günceller)
          python tools/audiogen/v35.py --olc <png> (yalnızca kritik çeşitlerini ölçer + spektrogram)"""
import os
import sys
import json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, t_axis, exp_env, noise, sweep, distort, fade, hp, lp, bp, master, write_wav, loudness, place
from layer import KI, KR, trim, build, pitch
from pro import click
from impact import cut, crunch
from v26 import asat, transient, ny_comp, body
from v27 import modes, scrape, metal_room

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'audio', 'sfx')
TARGET = {'vahset_et': -11.0, 'vahset_kemik': -12.5, 'vahset_olum': -8.5, 'vahset_yirtil': -12.0, 'vahset_dusme': -16.0,
          'darbe_kritik': -6.5, 'darbe_kritik_kunt': -6.5}


def _n(x):
    return x / (np.max(np.abs(x)) + 1e-9)


def wet(dur, seed, lo=180.0, hi=2600.0, rate=140.0, k=None):
    """Islak şapırtı: bant gürültü, hızlı tanecikli genlik (sıvı damlacıkları), üstte kısa tiz cızırtı."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    x = bp(noise(dur, seed=seed), lo, hi)
    m = np.abs(lp(rng.standard_normal(n), rate))
    m = _n(m) ** 1.6
    hiss = hp(noise(dur, seed=seed + 1), 3500) * 0.25
    return (x * (0.25 + m) + hiss * m) * exp_env(dur, k or 5.0 / dur)


def snaps(dur, n, seed, lo=1000.0, hi=6000.0, g=1.0):
    """Kemik çatırtısı: kısa sürede sıkışık, giderek seyrekleşen tık dizisi."""
    rng = np.random.default_rng(seed)
    x = np.zeros(int(dur * SR) + 800)
    for i in range(n):
        t = dur * (rng.random() ** 1.8)
        d = rng.uniform(0.0015, 0.005)
        c = bp(noise(d + 0.01, seed=int(rng.integers(1e6))), lo * rng.uniform(0.6, 1.4), hi)[:int(d * SR)] * exp_env(d, 3.0 / d)
        place(x, c, t, rng.uniform(0.4, 1.0) * g * (1.0 - 0.5 * t / dur))
    return x


def flesh_hit(i):
    punch = ('impactPunch_heavy_000.ogg', 'impactPunch_heavy_001.ogg', 'impactPunch_heavy_003.ogg', 'impactPunch_heavy_004.ogg')[i % 4]
    soft = ('impactSoft_heavy_000.ogg', 'impactSoft_heavy_002.ogg', 'impactSoft_heavy_003.ogg', 'impactSoft_heavy_004.ogg')[i % 4]
    dur = 0.3
    x = build([
        (asat(trim(pitch(KI(punch), 0.82 + 0.04 * i), 0, 0.16, 0.05), 2.4, 0.2), 0.0, 0.8),
        (trim(pitch(KI(soft), 0.75), 0, 0.2, 0.06), 0.004, 0.6),
        (wet(0.2, 3500 + i), 0.006, 0.75),
        (body(120.0 - 8 * i, 50.0, 0.12, 22.0, 4.0), 0.0, 0.45),
        (crunch(0.05, 3510 + i, 400, 3000, 3.5, 120.0), 0.002, 0.25),
    ])
    x = ny_comp(_n(x), ratio=3.0, th_db=-18.0, mix=0.4)
    return cut(x, dur, 0.06)


def bone(i):
    wood = ('impactWood_light_000.ogg', 'impactWood_light_001.ogg', 'impactWood_light_002.ogg', 'impactWood_light_003.ogg')[i % 4]
    dur = 0.22
    x = build([
        (snaps(0.07 + 0.01 * i, 18 + 4 * i, 3600 + i), 0.0, 0.9),
        (asat(trim(pitch(KI(wood), 0.68 + 0.05 * i), 0, 0.12, 0.04), 3.0, 0.15), 0.0, 0.7),
        (crunch(0.06, 3610 + i, 900, 5200, 5.0, 220.0), 0.003, 0.55),
        (body(240.0, 90.0, 0.05, 50.0, 3.0), 0.0, 0.3),
    ])
    x = transient(_n(x), attack=1.6, sustain=-0.3)
    return cut(x, dur, 0.04)


def kill_burst(i):
    soft = ('impactSoft_heavy_001.ogg', 'impactSoft_heavy_003.ogg', 'impactSoft_heavy_004.ogg')[i % 3]
    punch = ('impactPunch_heavy_002.ogg', 'impactPunch_heavy_000.ogg', 'impactPunch_heavy_004.ogg')[i % 3]
    dur = 0.75
    x = build([
        (body(95.0 - 6 * i, 38.0, 0.35, 9.0, 5.0), 0.0, 0.9),
        (asat(trim(pitch(KI(punch), 0.7), 0, 0.2, 0.06), 3.0, 0.2), 0.0, 0.75),
        (trim(pitch(KI(soft), 0.62), 0, 0.3, 0.08), 0.006, 0.7),
        (wet(0.5, 3700 + i, 140.0, 2200.0, 90.0, 6.0), 0.01, 1.0),
        (wet(0.25, 3710 + i, 600.0, 4800.0, 260.0), 0.04, 0.45),   # ikinci dalga: zerreler
        (snaps(0.09, 26, 3720 + i), 0.012, 0.7),
        (asat(trim(pitch(KI('impactWood_light_004.ogg'), 0.62), 0, 0.1, 0.03), 3.0, 0.2), 0.014, 0.55),
    ])
    x = ny_comp(_n(x), ratio=4.0, th_db=-20.0, mix=0.5)
    x = distort(_n(x), 1.4)
    return cut(x, dur, 0.15)


def tear(i):
    """Islak yırtılma: lifler gerilir (yükselen bant gürültü + çıtırtı), sonra kopar (tık + şapırtı)."""
    dur = 0.42
    rng = np.random.default_rng(3800 + i)
    pre = 0.14 + 0.03 * i
    n = int(pre * SR)
    src = noise(pre + 0.01, seed=3801 + i)[:n]
    out = np.zeros(n)
    nseg = 10
    ed = np.linspace(0, n, nseg + 1).astype(int)
    for s in range(nseg):
        u = (s + 0.5) / nseg
        fc = 500.0 * (2600.0 / 500.0) ** u
        out[ed[s]:ed[s + 1]] = bp(src, fc * 0.6, fc * 1.6)[ed[s]:ed[s + 1]]
    m = _n(np.abs(lp(rng.standard_normal(n), 300.0))) ** 1.3
    stretch = out * (0.2 + m) * np.linspace(0.3, 1.0, n) ** 1.5
    x = build([
        (stretch, 0.0, 0.8),
        (snaps(pre, 14, 3810 + i, 1500.0, 7000.0, 0.5), 0.0, 0.6),
        (trim(pitch(KR('knifeSlice.ogg' if i % 2 == 0 else 'knifeSlice2.ogg'), 0.72), 0, 0.15, 0.05), pre - 0.02, 0.6),
        (click(0.006, 1500, 9000, 3820 + i), pre, 0.8),
        (wet(0.26, 3830 + i, 200.0, 3000.0, 160.0), pre + 0.003, 0.9),
        (body(160.0, 60.0, 0.08, 30.0, 3.0), pre, 0.4),
    ])
    return cut(_n(x), dur, 0.06)


def drop(i):
    soft = ('impactSoft_medium_000.ogg', 'impactSoft_medium_001.ogg', 'impactSoft_medium_002.ogg', 'impactSoft_medium_003.ogg')[i % 4]
    x = build([
        (trim(pitch(KI(soft), 0.7 + 0.05 * i), 0, 0.14, 0.04), 0.0, 0.8),
        (wet(0.12, 3900 + i, 200.0, 2400.0, 200.0), 0.002, 0.7),
    ])
    return cut(_n(x), 0.16, 0.04)


# ----------------------------------------------------------------------------- METAL kritik
# Hedef: düz, parlak, kesici çelik. Üç katman: (1) bıçağın çeliğe değdiği 3 ms'lik tık + 6 kHz üstü kısa "tss";
# (2) "şiiing": 11 → 5 kHz kayan, tarak süzgeçli dar bant sıyırma (40-70 ms); (3) çınlama: çan / plaka benzeri
# inharmonik kipler (temel 2,1-2,7 kHz, oranlar 1 .. 5,4 → ~13 kHz'e kadar), alt kipler 0,5-0,8 sn, üstler 0,1-0,25 sn
# söner; vuruşta perde %1,5-2,5 hızla düşer ("KLANG"ın düşüşü), her kip iki kola ayrılır (4-9 Hz dövünme = pırıltı).
# Altta yalnızca çok kısa bir "klang" gövdesi (temel × 0,42, 0,12 sn) ve küçük metal oda; v26/v27'nin yumruk / kirli
# doyurma katmanları YOK (kullanıcı "düz metal" istedi).
BELL = (1.0, 1.183, 1.506, 2.0, 2.514, 2.662, 3.011, 4.166, 5.43)
T60_BELL = (0.78, 0.7, 0.55, 0.42, 0.33, 0.3, 0.24, 0.16, 0.1)
G_BELL = (1.0, 0.5, 0.62, 0.7, 0.42, 0.38, 0.33, 0.22, 0.14)
CRIT_V = [
    # f0, bükülme, dövünme, sıyırma (baş, son, süre, kazanç), gövde kazancı, kuyruk ölçeği
    dict(f0=2380.0, bend=0.02, beat=(4.0, 8.5), s=(11500.0, 5200.0, 0.06, 0.65), g_body=0.32, t60k=1.3, seed=10),   # A: şiiing
    dict(f0=1960.0, bend=0.025, beat=(3.0, 6.5), s=(9000.0, 4200.0, 0.035, 0.4), g_body=0.5, t60k=1.2, seed=20),    # B: KLANG
    dict(f0=2720.0, bend=0.015, beat=(5.0, 9.5), s=(12500.0, 6000.0, 0.07, 0.55), g_body=0.25, t60k=1.45, seed=30), # C: tiz çın
]


def crit_metal(v, low=1.0):
    f0 = v['f0'] * low
    s0, s1, sd, sg = v['s']
    sd2 = sd
    k = v['t60k'] * (1.15 if low < 1.0 else 1.0)
    dur = 0.68
    sd_ = v['seed']
    x = build([
        (click(0.003, 2500, 18000, 4000 + sd_), 0.0, 0.9),
        (hp(noise(0.012, seed=4001 + sd_), 6000) * exp_env(0.012, 400.0), 0.0, 0.45),
        (scrape(sd2, s0 * (0.85 if low < 1.0 else 1.0), s1, 4002 + sd_, 2100.0), 0.0, sg),
        (modes(f0, BELL, tuple(t * k for t in T60_BELL), G_BELL, dur, 4003 + sd_, v['beat'], bend=v['bend'], spread=0.006), 0.0006, 0.75),
        # ikinci (karşı) bıçak: biraz tiz, kısa: çarpışmanın iki gövdesi
        (modes(f0 * 1.31, BELL[:6], tuple(t * 0.45 for t in T60_BELL[:6]), G_BELL[:6], dur, 4004 + sd_, v['beat'], bend=v['bend'] * 0.7), 0.0012, 0.32),
        # klang gövdesi
        (modes(f0 * 0.42, (1.0, 1.59, 2.14), (0.14, 0.1, 0.07), (1.0, 0.6, 0.4), 0.3, 4005 + sd_, (1.0, 3.0), bend=0.03), 0.0, v['g_body'] * (1.4 if low < 1.0 else 1.0)),
    ])
    x = transient(_n(x), attack=1.5, sustain=0.0)
    x = ny_comp(x, ratio=2.5, th_db=-22.0, mix=0.3)
    x = distort(_n(x), 1.15)
    x = metal_room(x, sd_)
    # kısa parlak oda kuyruğu (yalnızca tiz): pırıltıyı biraz uzatır
    rng = np.random.default_rng(4010 + sd_)
    nir = int(0.35 * SR)
    ir = hp(rng.standard_normal(nir), 2500) * np.exp(-np.arange(nir) / SR * 11.0)
    wet_ = np.convolve(x, ir)[:len(x)]
    x = x + _n(wet_) * 0.07 * np.max(np.abs(x))
    return cut(x, dur, 0.12)


def build_all():
    out = {}
    for i in range(4):
        out['vahset_et_%d' % (i + 1)] = flesh_hit(i)
        out['vahset_kemik_%d' % (i + 1)] = bone(i)
        out['vahset_dusme_%d' % (i + 1)] = drop(i)
    for i in range(3):
        out['vahset_olum_%d' % (i + 1)] = kill_burst(i)
        out['vahset_yirtil_%d' % (i + 1)] = tear(i)
    for i, v in enumerate(CRIT_V):
        out['darbe_kritik_%d' % (i + 1)] = crit_metal(v)
        out['darbe_kritik_kunt_%d' % (i + 1)] = crit_metal(v, 0.72)
    out['darbe_kritik'] = out['darbe_kritik_%d' % (BEST + 1)]
    return out


BEST = 2   # ölçüm + dinleme vekili sonrası seçilen en iyi çeşit (C: en parlak, en uzun pırıltılı çınlama); --olc ile yeniden ölçülür


def target_for(name):
    pre = name.rstrip('0123456789').rstrip('_')
    return TARGET.get(pre, -12.0)


def bands(x):
    """İlk 0,3 sn: bant payları (dB), spektral ağırlık merkezi (Hz), 0,2-0,5 sn kuyruk/geçiş oranı (dB)."""
    y = x[:int(0.3 * SR)]
    f = np.fft.rfftfreq(len(y), 1 / SR)
    P = np.abs(np.fft.rfft(y)) ** 2
    tot = P.sum() + 1e-12
    out = {}
    for lo, hi in ((80, 200), (200, 1000), (1000, 5000), (5000, 20000)):
        out['%d-%d' % (lo, hi)] = round(10 * np.log10(P[(f >= lo) & (f < hi)].sum() / tot + 1e-12), 1)
    out['merkez_hz'] = int((f * P).sum() / tot)
    a = np.sqrt(np.mean(x[:int(0.03 * SR)] ** 2))
    b = np.sqrt(np.mean(x[int(0.2 * SR):int(0.5 * SR)] ** 2))
    out['kuyruk_db'] = round(20 * np.log10(b / (a + 1e-9) + 1e-9), 1)
    out['yukseklik'] = round(loudness(x), 1)
    return out


def measure(png):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    vs = [master(crit_metal(v), TARGET['darbe_kritik']) for v in CRIT_V]
    fig, ax = plt.subplots(2, len(vs), figsize=(5 * len(vs), 7))
    for i, x in enumerate(vs):
        m = bands(x)
        print('çeşit', 'ABC'[i], m)
        ax[0, i].plot(np.arange(len(x)) / SR, x, lw=0.4)
        ax[0, i].set_title('darbe_kritik %s  merkez %d Hz  kuyruk %.1f dB' % ('ABC'[i], m['merkez_hz'], m['kuyruk_db']), fontsize=9)
        ax[1, i].specgram(x, NFFT=1024, Fs=SR, noverlap=768, cmap='magma', vmin=-120)
        ax[1, i].set_ylim(0, 16000)
    plt.tight_layout()
    plt.savefig(png, dpi=90)
    print('png:', png)


def main():
    if '--olc' in sys.argv:
        measure(sys.argv[sys.argv.index('--olc') + 1])
        return
    allx = build_all()
    mp = os.path.join(A, 'sfx.json')
    meta = json.load(open(mp, encoding='utf-8'))
    for name, x in sorted(allx.items()):
        y = master(x, target_for(name))
        write_wav(os.path.join(A, name + '.wav'), y, SR, None)
        meta[name] = {'loop': False, 'len': round(len(y) / SR, 3), 'hedef_db': target_for(name)}
    # v27'nin fazladan çeşitleri (4, 5 / kunt 4) kaldırılır: yalnızca yeni metal çeşitler çalsın
    for old in ('darbe_kritik_4', 'darbe_kritik_5', 'darbe_kritik_kunt_4'):
        meta.pop(old, None)
        for ext in ('.wav', '.wav.import'):
            p = os.path.join(A, old + ext)
            if os.path.exists(p):
                os.remove(p)
    json.dump(meta, open(mp, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('yazıldı:', len(allx))


if __name__ == '__main__':
    main()
