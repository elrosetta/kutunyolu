"""v27 metal kritik sesi: "kritik sesi daha metal olsun — kılıç çarpışması sesi gibi."
v26'nın kritiği gür ve kirliydi (KRAK + THWACK + kısa şing) ama ağırlığı alt-orta gövdedeydi: kulak "yumruk / kemik"
duyuyordu, "çelik" değil. Kılıç çarpışmasının imzası çınlayan çeliktir: iki bıçağın kendi kipleri (inharmonik kısmiler,
~1,2-9 kHz), ilk anda sert bir sıyırma ("şşk"), sonra parlak, hafifçe vuran (yakın iki kipin dövünmesi) bir "KLANG /
ŞİİİNG" çınlaması. Yeni ses (geçiş t=0) kipsel (modal) sentezle:
  1. çarpma tıkı        0-6 ms geniş bant tık (3-16 kHz) + 1,5 ms'lik metal "tink"
  2. sıyırma (ŞŞK)      bıçak bıçağın üstünden kayar: süzgeç frekansı 9 → 3,5 kHz kayan dar bant gürültü, tarak
                        süzgeçli (metal sürtünme tınısı), tanecikli genlik; 35-60 ms
  3. çınlama (KLANG)    iki bıçak = iki kip takımı (temel ~1,2-1,9 kHz; serbest-serbest çubuk / bıçak oranlarına yakın
                        inharmonik kısmiler 1,2-9 kHz). Her kip iki kola ayrılır (±2-5 Hz: dövünme, "vuu" titreşimi);
                        alt kipler 0,35-0,5 sn'de (T60), üst kipler 0,05-0,15 sn'de söner; vuruşta perde %0,4 düşer
  4. ağırlık            v26'dan kısa alt "yumruk" (perdesi 170 → 60 Hz düşen, doyurulmuş ton, 0,1 sn) ve Kenney
                        impactPunch_heavy (CC0) kısık: çelik baskın, gövde yalnız ağırlık için
  5. işlem              geçiş biçimleme, hafif paralel sıkıştırma, yumuşak kırpma (çınlamayı ezmeyecek kadar),
                        küçük metalik oda (erken yansımalar)
Künt çeşit (gürz, çekiç, topuz, taş, kalkan): ÖRS "DANG" — daha alçak (~550-900 Hz temelli), çan / örs kip oranları,
daha uzun çınlama, daha güçlü alt gövde, kısa çatırtı; sıyırma yok (yerine kısa tok vuruş gürültüsü).
Beş bıçak (darbe_kritik_1..5), dört künt (darbe_kritik_kunt_1..4) çeşidi; her çeşit başka temel / kip dağılımı / dövünme
hızı; Ses.HIT_TIERS kritik pv 0,06 (± %6 perde) ile her çalış başka. Yönlendirme v26 ile aynı (Krit veri yolu,
Ses.krit_duck kısma, tüm kritik yolları).
Yeniden üretim: python tools/audiogen/export_audio.py --sfx darbe_kritik darbe_kritik_1 ... darbe_kritik_5
darbe_kritik_kunt_1 ... darbe_kritik_kunt_4
Karşılaştırma görseli (v26 ↔ v27 dalga biçimi + spektrogram): python tools/audiogen/v27.py --karsilastir <v26_klasoru> <png>"""
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, t_axis, exp_env, noise, sweep, distort, fade, hp, lp, bp
from layer import KI, trim, build
from pro import click
from impact import cut
from v26 import asat, transient, ny_comp, body


def modes(f0, ratios, t60s, gains, dur, seed, beat=(2.0, 5.0), bend=0.004, spread=0.004):
    """Kipsel çınlama: her kip f0*oran'da, kendi sönüş süresiyle (T60, sn); her kip iki yakın kola ayrılır (dövünme)."""
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    x = np.zeros(len(t))
    # vuruşta bıçak gerilir: perde kısa sürede hafifçe düşer (çelik "tıııng" yerine canlı "şiiing")
    pitch = 1.0 + bend * np.exp(-t * 40.0)
    for r, t60, g in zip(ratios, t60s, gains):
        f = f0 * r * (1.0 + rng.uniform(-spread, spread))
        if f >= SR * 0.45:
            continue
        k = 6.91 / t60   # exp(-k t) → T60'da -60 dB
        db = rng.uniform(beat[0], beat[1])
        for side, w in ((-0.5, 0.55), (0.5, 0.45)):
            ph = 2 * np.pi * np.cumsum((f + side * db) * pitch) / SR
            x += np.sin(ph + rng.uniform(0, 6.28)) * np.exp(-k * t) * g * w
    a = int(0.0008 * SR)
    x[:a] *= np.linspace(0, 1, a)
    return x


def scrape(dur, f_hi, f_lo, seed, comb_hz=1900.0):
    """Sıyırma: dar bant gürültü, merkez frekansı f_hi → f_lo kayar; tarak süzgeci metal sürtünme tınısı, tanecikli genlik."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    src = noise(dur + 0.02, seed=seed)[:n]
    out = np.zeros(n)
    # dilimlerle kayan bant (her dilimde FFT bant geçiren): basit ama yeterli
    nseg = 8
    edges = np.linspace(0, n, nseg + 1).astype(int)
    for i in range(nseg):
        a, b = edges[i], edges[i + 1]
        u = (i + 0.5) / nseg
        fc = f_hi * (f_lo / f_hi) ** u
        seg = bp(src, fc * 0.72, fc * 1.35)[a:b]
        ramp = np.ones(b - a)
        out[a:b] += seg * ramp
    # tarak süzgeci (gecikmeli kopya): sürtünen çeliğin "zzz" tınısı
    d = max(1, int(SR / comb_hz))
    y = out.copy()
    y[d:] += 0.7 * out[:-d]
    m = np.abs(lp(rng.standard_normal(n), 260.0))
    m /= np.max(m) + 1e-9
    env = np.minimum(1.0, t / 0.002) * np.exp(-t * (3.2 / dur))
    return y * (0.45 + 0.55 * m) * env


def metal_room(x, seed=0):
    """Küçük metalik oda: birkaç erken yansıma (3-19 ms) + kısa, parlak dağınık kuyruk."""
    rng = np.random.default_rng(seed)
    y = x.copy()
    for ms, g in ((3.1, 0.22), (7.4, 0.16), (11.8, 0.12), (18.6, 0.08)):
        d = int(ms * 0.001 * SR * (1 + rng.uniform(-0.05, 0.05)))
        y[d:] += x[:-d] * g
    n = int(0.22 * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 22.0)
    ir = lp(ir, 7000)
    wet = np.convolve(x, ir)[:len(x)]
    wet /= np.max(np.abs(wet)) + 1e-9
    return y + wet * 0.06 * np.max(np.abs(y))


def finish(x, dur, drive=1.6, comp_mix=0.35):
    x = transient(x / (np.max(np.abs(x)) + 1e-9), attack=1.4, sustain=-0.1)
    x = ny_comp(x, ratio=3.0, th_db=-20.0, mix=comp_mix)
    x = distort(x / (np.max(np.abs(x)) + 1e-9), drive)   # yumuşak kırpma: geçiş gür, çınlama ezilmez
    x = metal_room(x)
    return cut(x, dur, 0.08)


# serbest-serbest çubuk (kılıç bıçağı ~ ince uzun çubuk) oranları 1, 2,76, 5,40, 8,93 ...; burulma / kalınlık kipleri
# araya girer (1,52, 2,05, 3,6, 4,4): gerçek bıçak spektrumu gibi sık ama inharmonik
BLADE_A = (1.0, 1.52, 2.05, 2.76, 3.62, 4.41, 5.40, 6.7)
BLADE_B = (1.0, 1.34, 1.93, 2.81, 3.33, 4.6, 5.9)
T60_A = (0.5, 0.42, 0.34, 0.28, 0.22, 0.2, 0.14, 0.09)
T60_B = (0.42, 0.34, 0.28, 0.22, 0.17, 0.13, 0.09)
G_A = (1.0, 0.55, 0.62, 0.55, 0.48, 0.42, 0.32, 0.22)
G_B = (0.85, 0.5, 0.48, 0.45, 0.38, 0.3, 0.2)
# çeşit başına [bıçak A temeli, bıçak B temeli, dövünme aralığı, sıyırma başı / sonu]
BLADE_V = [
    (1320.0, 1710.0, (2.5, 5.5), 9200.0, 3800.0),
    (1180.0, 1560.0, (2.0, 4.5), 8600.0, 3500.0),
    (1450.0, 1880.0, (3.0, 6.5), 9800.0, 4200.0),
    (1260.0, 1630.0, (1.6, 3.8), 8200.0, 3300.0),
    (1390.0, 1790.0, (3.5, 7.0), 9500.0, 4000.0),
]


def crit_blade(i):
    fa, fb, bt, s0, s1 = BLADE_V[i % len(BLADE_V)]
    punch = ('impactPunch_heavy_000.ogg', 'impactPunch_heavy_002.ogg', 'impactPunch_heavy_004.ogg', 'impactPunch_heavy_001.ogg')[i % 4]
    dur = 0.52
    x = build([
        # 1. çarpma tıkı
        (click(0.006, 3000, 16000, 1010 + i), 0.0, 0.75),
        (hp(noise(0.004, seed=1015 + i), 6000) * exp_env(0.004, 900.0), 0.0, 0.5),
        # 2. sıyırma
        (scrape(0.05 + 0.006 * (i % 3), s0, s1, 1020 + i, 1700.0 + 120 * i), 0.0, 0.7),
        # 3. çınlama: iki bıçak
        (modes(fa, BLADE_A, T60_A, G_A, dur, 1030 + i, bt), 0.0008, 0.62),
        (modes(fb, BLADE_B, T60_B, G_B, dur, 1040 + i, bt), 0.0016, 0.46),
        # 4. ağırlık (kısa, kısık)
        (body(170.0 - 6 * i, 60.0, 0.1, 30.0, 5.0), 0.001, 0.34),
        (asat(trim(KI(punch), 0, 0.09, 0.03), 2.5, 0.2), 0.0, 0.3),
    ])
    return finish(x, dur)


# örs / çan oranları: alçak, kalın gövdeli inharmonik kipler; uzun çınlama
ANVIL = (1.0, 1.59, 2.14, 2.65, 3.17, 4.1, 5.3, 6.9)
T60_N = (0.62, 0.5, 0.4, 0.3, 0.22, 0.15, 0.1, 0.07)
G_N = (1.0, 0.7, 0.62, 0.5, 0.4, 0.3, 0.2, 0.12)
BLUNT_V = [(640.0, (1.5, 3.5)), (720.0, (2.0, 4.0)), (580.0, (1.2, 3.0)), (810.0, (2.5, 5.0))]


def crit_blunt(i):
    f0, bt = BLUNT_V[i % len(BLUNT_V)]
    punch = ('impactPunch_heavy_003.ogg', 'impactPunch_heavy_000.ogg', 'impactPunch_heavy_004.ogg', 'impactPunch_heavy_002.ogg')[i % 4]
    dur = 0.6
    x = build([
        (click(0.007, 1800, 12000, 1060 + i), 0.0, 0.7),
        # tok vuruş gürültüsü (çekiç yüzü): kısa orta bant
        (asat(bp(noise(0.03, seed=1065 + i), 600, 4200), 3.0, 0.1) * exp_env(0.03, 120.0), 0.0, 0.55),
        # örs: ana kip takımı + üstte daha tiz ikinci gövde (çivi / demir halka)
        (modes(f0, ANVIL, T60_N, G_N, dur, 1070 + i, bt, bend=0.006), 0.0008, 0.7),
        (modes(f0 * 2.37, BLADE_B, tuple(t * 0.6 for t in T60_B), G_B, dur, 1075 + i, bt), 0.0015, 0.3),
        # ağırlık: künt silah daha çok gövde
        (body(150.0 - 6 * i, 48.0, 0.16, 18.0, 6.0), 0.001, 0.55),
        (asat(trim(KI(punch), 0, 0.14, 0.04), 3.0, 0.22), 0.0, 0.45),
    ])
    return finish(x, dur, 1.8, 0.42)


def sheath_click():
    """kin_kapa: kılıcın kına girişi (v27 SanatAnim kına koyma "çıt"ı): kısa, aşağı kayan çelik sıyırma ("şşk") + 45 ms
    sonra iki kısa metal tık (koruma kına oturur); çok küçük oda. -18 dB: vuruş seslerinin altında, süsleme düzeyinde."""
    dur = 0.16
    x = build([
        (scrape(0.04, 7200.0, 3600.0, 1090, 2300.0), 0.0, 0.5),
        (click(0.004, 2500, 12000, 1091), 0.045, 0.8),
        (modes(2350.0, (1.0, 1.62, 2.71, 3.9), (0.05, 0.04, 0.03, 0.02), (1.0, 0.6, 0.45, 0.3), 0.1, 1092), 0.046, 0.55),
        (click(0.003, 3000, 14000, 1093), 0.062, 0.45),
    ])
    x = x / (np.max(np.abs(x)) + 1e-9)
    return cut(metal_room(x, 3), dur, 0.04)


def build_all():
    out = {'kin_kapa': sheath_click()}
    for i in range(5):
        out['darbe_kritik_%d' % (i + 1)] = crit_blade(i)
    out['darbe_kritik'] = out['darbe_kritik_1']
    for i in range(4):
        out['darbe_kritik_kunt_%d' % (i + 1)] = crit_blunt(i)
    return out


def _read(p):
    import soundfile as sf
    x, sr = sf.read(p)
    if x.ndim > 1:
        x = x.mean(axis=1)
    return x, sr


def compare(old_dir, png, new_dir):
    """v26 ↔ v27 dalga biçimi ve spektrogram (bıçak ve künt çeşidinin ilki)."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows = [('v26 darbe_kritik_1', os.path.join(old_dir, 'darbe_kritik_1.wav')),
            ('v27 darbe_kritik_1', os.path.join(new_dir, 'darbe_kritik_1.wav')),
            ('v26 darbe_kritik_kunt_1', os.path.join(old_dir, 'darbe_kritik_kunt_1.wav')),
            ('v27 darbe_kritik_kunt_1', os.path.join(new_dir, 'darbe_kritik_kunt_1.wav'))]
    fig, ax = plt.subplots(len(rows), 2, figsize=(13, 10), gridspec_kw={'width_ratios': [1, 1.4]})
    for r, (name, p) in enumerate(rows):
        x, sr = _read(p)
        t = np.arange(len(x)) / sr
        ax[r][0].plot(t, x, lw=0.5, color='#223')
        ax[r][0].set_xlim(0, 0.62)
        ax[r][0].set_ylim(-1, 1)
        ax[r][0].set_title(name + ' (%.2f sn)' % (len(x) / sr), fontsize=9)
        ax[r][1].specgram(x, NFFT=1024, Fs=sr, noverlap=896, cmap='magma', vmin=-120)
        ax[r][1].set_xlim(0, 0.62)
        ax[r][1].set_ylim(0, 14000)
        ax[r][1].set_ylabel('Hz', fontsize=8)
    fig.tight_layout()
    fig.savefig(png, dpi=90)


if __name__ == '__main__':
    if '--karsilastir' in sys.argv:
        a = sys.argv[sys.argv.index('--karsilastir') + 1:]
        here = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'audio', 'sfx')
        compare(a[0], a[1], a[2] if len(a) > 2 else here)
        sys.exit(0)
    import soundfile as sf
    from synth import master
    od = os.environ.get('V27_OUT', '.')   # deneme çıktısı
    for k, v in build_all().items():
        sf.write(os.path.join(od, k + '.wav'), master(v, -6.5), SR)
        print(k, round(len(v) / SR, 3))
