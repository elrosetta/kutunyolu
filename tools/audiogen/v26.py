"""v26 kritik vuruş sesi: "kritik sesi Dead Cells'inkine yakın olsun; çok sönük."
v25'in kritiği temiz ve "güzel" idi ama sönüktü: ışıltı çanı ve oda kuyruğu dosyanın yarısını kaplıyor, master yüksekliği
(50 ms'lik en gür pencere) kuyruğu da sayınca geçiş görece kısık kalıyordu; SFX veri yolunun sıkıştırıcısı (-14 dB, 3:1)
kritiği sıradan vuruşun düzeyine geri bastırıyordu. Dead Cells'in kritiği kısa, gür ve "kirli": ağır, bozulmuş bir
"KRAK / THWACK"; göğüste vuran alçak-orta gövde, kırpılmış / kırık bitli parlak bir çatırtı, üstünde kısa metal "şing".
Yeni ses (geçiş t=0, ~0,22-0,28 sn), katmanlar:
  1. çatırtı (KRAK)     1,5-12 kHz gürültü patlaması, sert kırpma (asimetrik) + bit ezme (8 kHz / 5 bit tanecik), 18 ms
  2. gövde (THWACK)     perdesi 190 → 62 Hz düşen ton, asimetrik doyurma (80-200 Hz gövde + 2./3. harmonikler, küçük
                        hoparlörde de duyulur) + temiz alt bas + Kenney Impact impactPunch_heavy (CC0) bozularak
  3. ezilme             350-3800 Hz tanecikli, doyurulmuş kırılma gürültüsü (kemik / zırh "kıtır")
  4. şing               bıçak: 4-5 kHz inharmonik çelik tonları + Kenney RPG knifeSlice (CC0) tizi, 0,15 sn;
                        künt: 1,5-1,8 kHz kısa çan sesi (tok "dang"), daha alçak çatırtı, daha uzun gövde
  5. işlem              geçiş biçimleme (hızlı / yavaş zarf farkıyla saldırı +, gövde -), paralel sıkıştırma (NY,
                        4:1, 1 ms / 60 ms), son yumuşak kırpma; çok küçük oda
Yükseklik: export_audio.py TARGETS darbe_kritik -6,5 dB (sıradan darbe -10 / -10,5); Ses.HIT_TIERS kritik +1,5 dB ve
kendi veri yolu ("Krit": SFX sıkıştırıcısını atlar) → sıradan vuruşun ~7-9 dB üstünde; çalınınca öbür efektler ve
müzik kısa süre kısılır (Ses.krit_duck).
Yeniden üretim: python tools/audiogen/export_audio.py --sfx darbe_kritik darbe_kritik_1 ... darbe_kritik_kunt_3"""
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, t_axis, exp_env, noise, sine, sweep, distort, fade, hp, lp, bp
from layer import KI, KR, trim, build
from pro import click, room
from impact import crunch, cut


def bitcrush(x, rate=8000.0, bits=5):
    """Örnek tutma (rate Hz) + nicemleme (bits): tanecikli 'kırık bit' pürüzü."""
    step = max(1, int(SR / rate))
    y = np.repeat(x[::step], step)[:len(x)]
    q = 2 ** (bits - 1)
    return np.round(y * q) / q


def hardclip(x, drive=6.0, asym=0.18):
    """Asimetrik sert kırpma: çift harmonikler (kirli, sıcak) + tek harmonikler (sert)."""
    y = x / (np.max(np.abs(x)) + 1e-9) * drive + asym
    return np.clip(y, -1.0, 1.0) - np.clip(asym, -1.0, 1.0)


def asat(x, drive=4.0, asym=0.25):
    """Asimetrik yumuşak doyurma (tanh)."""
    y = np.tanh(x * drive + asym) - np.tanh(asym)
    return y / (np.max(np.abs(y)) + 1e-9)


def follow(x, att, rel):
    """Tepe zarfı izleyici (tek kutuplu, saldırı / bırakma sn)."""
    a = np.exp(-1.0 / (att * SR))
    r = np.exp(-1.0 / (rel * SR))
    e = np.zeros(len(x))
    v = 0.0
    ax = np.abs(x)
    for i in range(len(x)):
        c = a if ax[i] > v else r
        v = c * v + (1.0 - c) * ax[i]
        e[i] = v
    return e


def transient(x, attack=1.8, sustain=-0.25):
    """Geçiş biçimleme: hızlı zarf yavaşı aştığı yerde (saldırı) kazanç artar, gövdede hafif azalır."""
    f = follow(x, 0.0005, 0.02)
    s = follow(x, 0.012, 0.09)
    d = np.clip((f - s) / (f + 1e-6), 0.0, 1.0)
    g = 1.0 + attack * d + sustain * (1.0 - d) * (s / (np.max(s) + 1e-9))
    return x * g


def ny_comp(x, ratio=4.0, th_db=-18.0, att=0.001, rel=0.06, mix=0.55):
    """Paralel (New York) sıkıştırma: ezilmiş kopya kuru sesle karışır (gövde yoğunlaşır, geçiş korunur)."""
    x = x / (np.max(np.abs(x)) + 1e-9)
    e = follow(x, att, rel)
    th = 10 ** (th_db / 20)
    g = np.ones(len(x))
    over = e > th
    g[over] = (th * (e[over] / th) ** (1.0 / ratio)) / e[over]
    c = x * g
    c /= np.max(np.abs(c)) + 1e-9
    return x * (1.0 - mix) + c * mix


def steel(f0, dur=0.15, k=30.0, parts=(1.0, 1.41, 2.03, 2.76), seed=0, bend=0.012):
    """Çelik 'şing': inharmonik kısmiler, perde hafifçe aşağı kayar, yüksek kısmi hızlı söner."""
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    x = np.zeros(len(t))
    for i, p in enumerate(parts):
        f = f0 * p * (1 + rng.uniform(-0.006, 0.006))
        ph = 2 * np.pi * np.cumsum(f * (1.0 - bend * (1 - np.exp(-t * 30.0)))) / SR
        x += np.sin(ph + rng.uniform(0, 6.28)) * np.exp(-k * (1 + 0.5 * i) * t) / (1 + 0.6 * i)
    a = int(0.0015 * SR)
    x[:a] *= np.linspace(0, 1, a)
    return x


def crack(dur, lo, hi, seed, drive=6.0, rate=8000.0, bits=5):
    """KRAK: bant gürültü patlaması, sert kırpılır ve bit ezilir; çok hızlı söner."""
    x = bp(noise(dur + 0.01, seed=seed), lo, hi)[:int(dur * SR)]
    x = hardclip(x, drive, 0.12)
    x = bitcrush(x, rate, bits)
    x = hp(x, lo * 0.6)
    return x * exp_env(dur, 4.5 / dur)


def smack(dur, lo, hi, seed, drive=5.0):
    """Orta "şak": 0,5-2,5 kHz bant gürültü, kırpılmış, hızlı söner (tokat / kemik çatırdaması gövdesi)."""
    x = bp(noise(dur + 0.01, seed=seed), lo, hi)[:int(dur * SR)]
    return asat(x, drive, 0.15) * exp_env(dur, 3.5 / dur)


def body(f0, f1, dur, k, drive=5.0):
    """THWACK gövdesi: perdesi düşen ton, asimetrik doyurulur (80-200 Hz + harmonikler)."""
    x = sweep(f0, f1, dur, curve=0.4) * exp_env(dur, k)
    a = int(0.0015 * SR)
    x[:a] *= np.linspace(0, 1, a)
    return fade(asat(x, drive, 0.3), 0.0, 0.03)


def finish(x, dur, drive=3.0):
    x = transient(x / (np.max(np.abs(x)) + 1e-9))
    x = ny_comp(x)
    x = distort(x / (np.max(np.abs(x)) + 1e-9), drive)   # son yumuşak kırpma: tepe/ortalama oranı düşer, gür okunur
    x = room(x, 0.12, 0.05, lpf=6000)
    return cut(x, dur, 0.05)


def crit_blade(i):
    punch = ('impactPunch_heavy_000.ogg', 'impactPunch_heavy_002.ogg', 'impactPunch_heavy_004.ogg', 'impactPunch_heavy_001.ogg')[i % 4]
    slice_ = ('knifeSlice.ogg', 'knifeSlice2.ogg')[i % 2]
    st = (4200.0, 4650.0, 3950.0, 4450.0)[i % 4]
    x = build([
        # 1. çatırtı + tık + orta "şak"
        (crack(0.028, 1500, 12000, 900 + i), 0.0, 1.25),
        (click(0.005, 3000, 16000, 910 + i), 0.0, 0.6),
        (smack(0.045, 700, 2600, 915 + i), 0.0, 0.8),
        # 2. gövde
        (body(190.0 - 8 * i, 62.0, 0.16, 22.0, 6.0), 0.001, 0.72),
        (sine(58.0 + 3 * i, 0.14) * exp_env(0.14, 18.0), 0.002, 0.22),
        (asat(trim(KI(punch), 0, 0.14, 0.04), 3.0, 0.2), 0.0, 0.7),
        # 3. ezilme
        (crunch(0.1, 920 + i, 500, 5000, 7.0, 150.0), 0.002, 1.0),
        # 4. şing
        (steel(st, 0.16, 24.0, seed=930 + i), 0.004, 0.5),
        (hp(trim(KR(slice_), 0, 0.12, 0.04), 2600), 0.003, 0.5),
    ])
    return finish(x, 0.24)


def crit_blunt(i):
    punch = ('impactPunch_heavy_003.ogg', 'impactPunch_heavy_000.ogg', 'impactPunch_heavy_004.ogg')[i % 3]
    x = build([
        (crack(0.03, 700, 9000, 950 + i, 7.0, 6000.0, 5), 0.0, 1.15),
        (click(0.006, 1800, 11000, 960 + i), 0.0, 0.5),
        (smack(0.055, 450, 1900, 965 + i), 0.0, 0.85),
        (body(160.0 - 7 * i, 48.0, 0.2, 16.0, 7.0), 0.001, 0.8),
        (sine(50.0 + 3 * i, 0.18) * exp_env(0.18, 13.0), 0.002, 0.3),
        (asat(trim(KI(punch), 0, 0.18, 0.05), 3.5, 0.25), 0.0, 0.85),
        (crunch(0.12, 970 + i, 260, 3600, 8.0, 120.0), 0.002, 1.0),
        (steel(1550.0 + 130 * i, 0.12, 36.0, parts=(1.0, 1.52, 2.33), seed=980 + i, bend=0.02), 0.003, 0.4),
    ])
    return finish(x, 0.28, 3.2)


def build_all():
    out = {}
    for i in range(4):
        out['darbe_kritik_%d' % (i + 1)] = crit_blade(i)
    out['darbe_kritik'] = out['darbe_kritik_1']
    for i in range(3):
        out['darbe_kritik_kunt_%d' % (i + 1)] = crit_blunt(i)
    return out


if __name__ == '__main__':
    import soundfile as sf
    from synth import master
    od = os.environ.get('V26_OUT', '.')   # deneme çıktısı
    for k, v in build_all().items():
        sf.write(os.path.join(od, k + '.wav'), master(v, -6.5), SR)
        print(k, round(len(v) / SR, 3))
