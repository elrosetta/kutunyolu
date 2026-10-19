"""v25 kritik vuruş sesi: "kritik vuruş sesi tatmin edici olsun."
Eski kritik (impact.py) 45 ms'lik ters yükselişle başlıyordu: geçiş vuruş karesinden sonra geliyor, v25'in yumuşak vuruş
duraklamasıyla (Game.HS) "geç ve bulanık" kalıyordu; çan katmanı da uzun ve çınlamasız bir "dong" idi.
Yeni ses dört katman, geçiş t=0'da (dosyanın başında; ön yankı yok):
  1. keskin metal geçişi   2-15 kHz çok kısa tık + bıçak kaydı (Kenney RPG knifeSlice, CC0) + 3,5-5 kHz hızlı sönen
                           çelik kısmi tonları ("tsing"; bıçağın kemiğe / zırha değdiği an)
  2. derin gövde           yumruk gövdesi (Kenney Impact impactPunch_heavy, CC0) + perdesi 120 → 46 Hz düşen hafif
                           doyurulmuş alt bas (göğüste hissedilen "güm"); 6 ms gecikmeli: tıktan hemen sonra oturur
  3. parlak ışıltı kuyruğu  müzikle aynı dizide (Hüseyni / E-B-D) iki notalı kısa çan + birbirine 5-7 Hz vuran iki ince
                           ton (titreşen "ödül" parıltısı) + 3-9 kHz hava; ~0,4 sn'de söner
  4. küçük oda             kısa yankı (biyom yankısı ayrıca Ses veri yolunda)
Her çeşitte nota, çelik tonları ve gövde perdesi biraz farklı (art arda aynı ses gelmez; Ses.play ayrıca ±%5 perde
oynatır). Künt silah çeşidi ("darbe_kritik_kunt", Ses.hit kind "kunt"): bıçak kaydı yok, daha alçak ve tok gövde,
çatırtılı kırılma, daha kalın çan (A5). Yükseklik export_audio.py TARGETS: darbe_kritik -8 dB (sıradan darbe -10 /
-10,5; Ses.HIT_TIERS ayrıca 0 dB → normal vuruşun ~4-5 dB üstünde, öldürüş sesinin biraz altında).
Yeniden üretim: python tools/audiogen/export_audio.py --sfx darbe_kritik darbe_kritik_1 ... (ya da tamamı)."""
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, t_axis, exp_env, noise, sine, sweep, distort, fade, hp, lp, bp
from layer import KI, KR, trim, pitch, build
from pro import click, room, note
from impact import crunch, glue, cut


def steel(f0, dur=0.09, k=55.0, parts=(1.0, 1.37, 1.93, 2.61), seed=0):
    """Çelik 'tsing': inharmonik, hızlı sönen kısmi tonlar (yüksek kısmiler daha hızlı söner)."""
    rng = np.random.default_rng(seed)
    x = np.zeros(int(dur * SR))
    for i, p in enumerate(parts):
        f = f0 * p * (1 + rng.uniform(-0.008, 0.008))
        x += sine(f, dur, phase=rng.uniform(0, 6.28)) * exp_env(dur, k * (1 + 0.45 * i)) / (1 + 0.7 * i)
    return x


def chime(freq, dur=0.42, k=7.5, beat=6.0):
    """Kısa parlak çan: temel + 2,0 / 3,0 / 4,2 kısmiler; temelin yanında 'beat' Hz vuran ikiz (titreşen ışıltı)."""
    t = t_axis(dur)
    x = (sine(freq, dur) + 0.85 * np.sin(2 * np.pi * (freq + beat) * t + 1.1)) * exp_env(dur, k) * 0.55
    for i, (p, g) in enumerate(((2.0, 0.32), (3.0, 0.16), (4.2, 0.09))):
        x += sine(freq * p, dur) * exp_env(dur, k * (1.6 + 0.8 * i)) * g
    a = int(0.002 * SR)
    x[:a] *= np.linspace(0, 1, a)
    return fade(x, 0.0, 0.08)


def air(dur=0.3, lo=3000, hi=9500, seed=1, k=9.0):
    return bp(noise(dur, seed=seed), lo, hi) * exp_env(dur, k)


def sub_thump(f0, f1, dur, k, drive=1.8):
    x = sweep(f0, f1, dur, curve=0.45) * exp_env(dur, k)
    a = int(0.003 * SR)
    x[:a] *= np.linspace(0, 1, a)
    return fade(distort(x, drive) * 0.8, 0.0, 0.06)   # sonu yumuşak (kesik bas sonu tık yapıyordu)


def crit_blade(i):
    notes = (('E6', 'B6'), ('D6', 'A6'), ('E6', 'D7'), ('B5', 'E6'))
    n1, n2 = notes[i % 4]
    st = (3600.0, 4100.0, 3850.0, 4400.0)[i % 4]
    punch = ('impactPunch_heavy_000.ogg', 'impactPunch_heavy_002.ogg', 'impactPunch_heavy_004.ogg', 'impactPunch_heavy_001.ogg')[i % 4]
    slice_ = ('knifeSlice.ogg', 'knifeSlice2.ogg')[i % 2]
    x = build([
        # 1. metal geçişi
        (click(0.008, 2500, 15000, 700 + i), 0.0, 1.0),
        (hp(trim(KR(slice_), 0, 0.11, 0.03), 900), 0.0, 0.7),
        (steel(st, 0.1, 50.0, seed=710 + i), 0.0, 0.55),
        # 2. gövde
        (trim(KI(punch), 0, 0.18, 0.05), 0.006, 0.85),
        (sub_thump(122.0 - 6 * i, 46.0, 0.3, 10.0, 2.0), 0.006, 0.95),
        (lp(noise(0.05, seed=720 + i), 900) * exp_env(0.05, 60), 0.004, 0.5),
        # 3. ışıltı kuyruğu
        (chime(note(n1), 0.42, 9.0, 5.5 + 0.5 * i), 0.012, 0.42),
        (chime(note(n2), 0.34, 10.0, 7.0), 0.03, 0.22),
        (air(0.28, 3200, 9500, 730 + i, 10.0), 0.008, 0.28),
    ])
    y = room(glue(x, 1.35), 0.32, 0.1)
    return cut(y, 0.46, 0.06)


def crit_blunt(i):
    notes = ('A5', 'G5', 'B5')
    punch = ('impactPunch_heavy_003.ogg', 'impactPunch_heavy_000.ogg', 'impactPunch_heavy_004.ogg')[i % 3]
    x = build([
        (click(0.01, 1500, 11000, 750 + i), 0.0, 0.9),
        (steel(1700.0 + 140 * i, 0.12, 38.0, parts=(1.0, 1.52, 2.33), seed=755 + i), 0.0, 0.4),
        (crunch(0.07, 760 + i, 220, 2800, 4.0), 0.002, 0.55),
        (trim(KI(punch), 0, 0.22, 0.06), 0.004, 1.0),
        (sub_thump(100.0 - 5 * i, 38.0, 0.34, 8.5, 2.3), 0.004, 1.0),
        (chime(note(notes[i % 3]), 0.4, 9.0, 5.0), 0.014, 0.34),
        (air(0.22, 2400, 7000, 770 + i, 12.0), 0.01, 0.2),
    ])
    y = room(glue(x, 1.5), 0.35, 0.1)
    return cut(y, 0.46, 0.06)


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
    od = os.environ.get('V25_OUT', '.')   # deneme çıktısı (sys.argv layer.py'nin kaynak klasörü bağımsız değişkeniyle çakışır)
    for k, v in build_all().items():
        sf.write(os.path.join(od, k + '.wav'), master(v, -8.0), SR)
        print(k, round(len(v) / SR, 3))
