"""v37c kritik sesi: oyuncunun seçtiği aday "sekiro_2" (örs KANG, GERÇEK KAYIT) ve çeşitleri.
İstek (oyuncu, 4 tur ret sonrası): "Sekiro savuşturması gibi sert, metalik, gerçek KILIÇ sesi" — ince ting değil, sinüs "çınn"
değil, süzülmüş gürültü değil. Araştırma (scratch_v37/aday/tur4/ARASTIRMA.md): oyuncular Sekiro savuşturmasını "gürültülü,
bloktan daha tiz bir CLANG" diye anlatır (çan / ting değil): gövdeli (0,8-3 kHz) sert çelik vuruşu + üstünde gerçek çelik çınlaması.

Yapı (scratch_v37/aday/tur4/sekiro.py: sekiro_2 ile birebir; darbe_kritik_1 = seçilen aday):
  örs     : Pablo Bergel "Anvil #1" (BigSoundBank, CC0) demirci örsü vuruşu @30,67 s — gerçek 2,52 kHz örs çınlaması, 2 s temiz
            kuyruk; kaydın geçişi ve gövdesi korunur, 0,8-3 kHz'e +3 dB raf, geçiş şekillendirici (+6 dB ilk 10 ms),
            kuyruk doğal sönüm ölçülüp yalnızca eksik kadar kısaltılır (-40 dB @0,95 s).
  kaldırma: aynı örs kaydının geçişsiz kuyruğu (1,5 kHz üstü) %55: çınlama öne çıkar.
  kılıç   : Bird_man "Sword Clash" (Freesound 275159, CC0) ilk 110 ms — gerçek kılıç-kılıca geçiş, enerjisinin %93'ü 0,6-3 kHz
            ("CLANG" gövdesi, sertlik); +6 dB geçiş şekillendirici.
  kıvılcım: ihitokage "Sword hits - no reverb" (Freesound 397168, CC0) bıçak sürtünmesi, 6-13 kHz, 50 ms, %18.
  mekân   : üç erken yansıma (7 / 13 / 23 ms), reverb yok; tanh doyum (1,5); ön seviye -9 dB (aday önizlemesiyle aynı),
            export_audio.master() oyunun hedefine getirir (darbe_kritik -6,5 dB, olum_vurus -9 dB: v37 ile aynı).
Çeşitler (darbe_kritik_1..4): örs perdesi ±4-7 %, iki ayrı örs vuruşu (@30,67 s / @0,18 s), kılıç geçişi kaydın 1. / 2. vuruşu,
kuyruk ±15 %, kıvılcım kaynağı farklı. Künt (darbe_kritik_kunt_1..3): örs ×0,77-0,84 (alçak), kuyruk daha kısa, daha ağır geçiş
(+8 dB) + Kenney impactMetal_heavy alt gövdesi (250-2200 Hz, 60 ms). olum_vurus_1..2: aynı ses biraz kısa (0,75-0,8 sn), -9 dB.
Kaynak mp3 kalitesi: örs 256 kbps / 48 kHz (BigSoundBank WAV'ı girişsiz indirilemedi), kılıç 128 kbps "hq" önizleme (tam WAV
Freesound girişi ister; aynı ad .wav olarak src/'ye konursa load() onu yeğler). Hiçbir oyunun sesi kullanılmadı.

Kullanım: python tools/audiogen/v37c.py   (darbe_kritik[_1..4], darbe_kritik_kunt_1..3, olum_vurus_1..2 yazar, sfx.json'u günceller;
          export_audio.py de v37b'den sonra bunu çağırır)"""
import os
import sys
import json
import math
from fractions import Fraction
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, fft_filter, loudness, soft_limit, write_wav, hp, master

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'audio', 'sfx')
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
TARGET = {'darbe_kritik': -6.5, 'darbe_kritik_kunt': -6.5, 'olum_vurus': -9.0}   # v37 ile aynı
PRE = -9.0                                     # aday önizlemesinin ön seviyesi (sekiro.py TARGET)
ANVIL = 'bsb_anvil1_s3589.mp3'
SWORD = 'fs_275159_birdman_sword_clash.mp3'
SPARK = 'fs_397168_ihitokage_sword_hits_noreverb.mp3'
HEAVY = ('impact/Audio/impactMetal_heavy_000.ogg', 'impact/Audio/impactMetal_heavy_002.ogg', 'impact/Audio/impactMetal_heavy_003.ogg')
_cache = {}


# ----------------------------------------------------------------- yükleme / dilimleme (sekiro.py ile birebir)
def load(name):
    if name not in _cache:
        p = os.path.join(SRC, name)
        w = os.path.splitext(p)[0] + '.wav'
        if not name.endswith('.wav') and os.path.exists(w):
            p = w                                   # tam kaliteli WAV varsa onu yeğle
        x, sr = sf.read(p, dtype='float64')
        if x.ndim > 1:
            x = x.mean(1)
        if sr != SR:
            fr = Fraction(SR, sr)
            x = resample_poly(x, fr.numerator, fr.denominator)
        _cache[name] = hp(x, 40)
    return _cache[name]


def hit(name, t0, dur, pre=0.0015, search=0.08):
    """Kayıttan tek vuruş: t0 civarında geçişi bulur (yerel tepenin %25'ini ilk aşan örnek), pre kadar önceden başlatır."""
    x = load(name)
    a = max(0, int((t0 - 0.03) * SR))
    b = min(len(x), int((t0 + search) * SR))
    seg = np.abs(x[a:b])
    thr = 0.25 * seg.max()
    on = max(0, a + int(np.argmax(seg > thr)) - int(pre * SR))
    y = x[on:on + int(dur * SR)].copy()
    n = int(0.0007 * SR)
    y[:n] *= np.linspace(0, 1, n)
    return y / (np.abs(y).max() + 1e-9)


def pitch(x, ratio):
    """Perdeyi ratio kat kaydırır (yeniden örnekleme; süre 1/ratio kat olur — kuyruk sonra yeniden şekillenir)."""
    fr = Fraction(ratio).limit_denominator(64)
    return resample_poly(x, fr.denominator, fr.numerator)


def natural_k(x):
    """Kaydın kendi sönüm hızı (dB/s eğimi, 20 ms sonrası, -45 dB üstü bölgede doğrusal uyum)."""
    w = int(0.01 * SR)
    e = np.sqrt(np.convolve(x ** 2, np.ones(w) / w, 'same')) + 1e-9
    edb = 20 * np.log10(e / e.max())
    t = np.arange(len(x)) / SR
    m = (t > 0.02) & (edb > -45)
    if m.sum() < 100:
        return 0.0
    slope = np.polyfit(t[m], edb[m], 1)[0]
    return max(0.0, -slope * math.log(10) / 20)


def decay(x, t40, floor_t=0.0):
    """Toplam sönüm -40 dB'ye t40 saniyede varsın: doğal sönüm ölçülür, yalnızca EKSİK kadar zarf eklenir."""
    t = np.arange(len(x)) / SR
    k = max(0.0, math.log(100) / t40 - natural_k(x))
    return x * np.exp(-k * np.maximum(0, t - floor_t))


def cut(x, dur, fo=0.04):
    n = int(dur * SR)
    y = np.zeros(n)
    m = min(n, len(x))
    y[:m] = x[:m]
    nf = min(int(fo * SR), n)
    y[-nf:] *= np.linspace(1, 0, nf) ** 2
    return y


def transient(x, ms=8.0, gain_db=6.0):
    """Geçiş şekillendirici: ilk ms içinde +gain_db, yumuşak iniş."""
    n = int(ms / 1000 * SR)
    g = np.ones(len(x))
    k = min(n, len(x))
    g[:k] = 10 ** (gain_db / 20) * np.linspace(1, 0, k) ** 1.5 + np.linspace(0, 1, k)
    return x * g


def sat(x, drive=1.6):
    return np.tanh(x * drive) / math.tanh(drive)


def body(x, db=3.0, lo=800.0, hi=3000.0):
    """0,8-3 kHz 'metal ağırlığı' rafı."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR) + 1e-6
    g = 1 + (10 ** (db / 20) - 1) / (1 + ((np.log(f / math.sqrt(lo * hi))) / (0.5 * math.log(hi / lo))) ** 6)
    return np.fft.irfft(X * g, n)


def gate(x, db=-52.0, win=0.01):
    """Kayıt gürültü tabanını kuyrukta siler."""
    w = int(win * SR)
    e = np.sqrt(np.convolve(x ** 2, np.ones(w) / w, 'same')) + 1e-9
    edb = 20 * np.log10(e / e.max())
    return x * np.clip((edb - db) / 8, 0, 1)


def early(x, taps=((0.007, 0.22), (0.013, 0.16), (0.023, 0.10)), lp_hz=7000.0):
    y = x.copy()
    for t, g in taps:
        d = int(t * SR)
        z = np.zeros_like(x)
        z[d:] = x[:-d] * g
        y += fft_filter(z, hi=lp_hz, slope=1.5)
    return y


def mixat(parts, dur):
    out = np.zeros(int(dur * SR))
    for x, at, g in parts:
        i = int(at * SR)
        m = min(len(x), len(out) - i)
        if m > 0:
            out[i:i + m] += x[:m] * g
    return out


def finish(x, dur, dense=1.2):
    """Hafif doyum (sertlik), ön seviyeye eşitle; tepe aşarsa tek yumuşak sınır."""
    x = cut(x, dur)
    x = sat(x / (np.abs(x).max() + 1e-9), dense)
    x = x * 10 ** ((PRE - loudness(x)) / 20)
    if np.abs(x).max() > 0.95:
        x = soft_limit(x, ceiling=0.95, knee=0.75)
        x = x * 10 ** (min(0.0, PRE - loudness(x)) / 20)
    return np.clip(x, -1, 1)


def ring(src, ratio, t40, dur, lo=None):
    """Gerçek örs kuyruğu: perde kaydır, kuyruk şekillendir, hedef band altını temizle; kaynağın geçişi atılır."""
    x = pitch(src, ratio) if ratio != 1 else src
    x = x[int(0.004 * SR):]
    n = int(0.003 * SR)
    x[:n] *= np.linspace(0, 1, n)
    x = decay(x, t40, floor_t=0.02)
    if lo:
        x = fft_filter(x, lo=lo, slope=1.5)
    return cut(x / (np.abs(x).max() + 1e-9), dur)


# ----------------------------------------------------------------- kayıt katmanları
def anvil(t0):
    """Pablo Bergel örsü: @30,67 s 2,2 s temiz kuyruk (1,4 s alınır); @0,18 s 1,2 s temiz (sonraki vuruş alınmaz)."""
    return gate(hit(ANVIL, t0, 1.4 if t0 > 1.0 else 1.15))


def sword(t0):
    """Bird_man kılıç çarpışması, ilk 110 ms (kayıtta 1. vuruş @0,01 s, 2. vuruş @0,13 s)."""
    return gate(hit(SWORD, t0, 0.11)) * np.exp(-np.arange(int(0.11 * SR)) / SR * 30)


def sparkle(dur=0.05, src=5.35):
    x = hit(SPARK, src, dur)
    x = fft_filter(x, lo=6000, hi=13000, slope=2.0)
    return x / (np.abs(x).max() + 1e-9) * np.exp(-np.arange(len(x)) / SR * 45)


def heavy_body(i, dur=0.06):
    """Künt: Kenney impactMetal_heavy alt gövdesi (250-2200 Hz), 60 ms."""
    x = hit(HEAVY[i % 3], 0.0, dur, search=0.2)
    x = fft_filter(x, lo=250, hi=2200, slope=2.0)
    return x / (np.abs(x).max() + 1e-9) * np.exp(-np.arange(len(x)) / SR * 25)


def kang(anvil_t=30.666, ratio=1.0, t40=0.95, dur=1.05, sword_t=0.01, spark_t=5.35, tr_db=6.0, body_db=3.0,
         lift_g=0.55, spark_g=0.18, heavy=None):
    """Örs KANG (varsayılanlar = seçilen aday sekiro_2)."""
    an = anvil(anvil_t)
    if ratio != 1:
        an = pitch(an, ratio)
    an = decay(an, t40, 0.05)
    lift = ring(anvil(anvil_t), ratio, t40, dur, lo=1500)
    parts = [(transient(body(an, body_db), 10, tr_db), 0, 1.0), (lift, 0.004, lift_g),
             (transient(sword(sword_t), 6, tr_db), 0.0, 0.8), (sparkle(0.05, spark_t), 0.001, spark_g)]
    if heavy is not None:
        parts.append((heavy_body(heavy), 0.0, 0.6))
    return finish(early(mixat(parts, dur)), dur, 1.5)


CV = [   # darbe_kritik_1..4 (1 = sekiro_2 birebir)
    dict(),
    dict(anvil_t=0.183, ratio=1.05, t40=0.82, dur=0.95, sword_t=0.13, spark_t=3.11, tr_db=6.5),
    dict(anvil_t=30.666, ratio=0.955, t40=1.08, dur=1.15, sword_t=0.01, spark_t=6.41, tr_db=5.5, body_db=3.5),
    dict(anvil_t=0.183, ratio=1.07, t40=0.9, dur=1.0, sword_t=0.13, spark_t=0.69, tr_db=6.0, spark_g=0.22),
]
KUNT = [  # darbe_kritik_kunt_1..3: örs alçak (×0,77-0,84), kuyruk kısa, ağır geçiş + alt gövde
    dict(anvil_t=30.666, ratio=0.8, t40=0.75, dur=0.85, sword_t=0.01, spark_t=5.35, tr_db=8.0, body_db=4.0, spark_g=0.1, heavy=0),
    dict(anvil_t=0.183, ratio=0.84, t40=0.68, dur=0.8, sword_t=0.13, spark_t=3.11, tr_db=8.0, body_db=4.0, spark_g=0.1, heavy=1),
    dict(anvil_t=30.666, ratio=0.77, t40=0.8, dur=0.9, sword_t=0.01, spark_t=6.41, tr_db=8.5, body_db=4.5, spark_g=0.08, heavy=2),
]
OLUM = [  # olum_vurus_1..2: aynı KANG biraz kısa (öldürüş "dışşkk"ını örtmesin; hedef -9 dB)
    dict(t40=0.7, dur=0.8),
    dict(anvil_t=0.183, ratio=1.03, t40=0.65, dur=0.75, sword_t=0.13, spark_t=3.11),
]


def build_all():
    out = {}
    for i, v in enumerate(CV):
        out['darbe_kritik_%d' % (i + 1)] = kang(**v)
    for i, v in enumerate(KUNT):
        out['darbe_kritik_kunt_%d' % (i + 1)] = kang(**v)
    for i, v in enumerate(OLUM):
        out['olum_vurus_%d' % (i + 1)] = kang(**v)
    out['darbe_kritik'] = out['darbe_kritik_1']   # tek dosya isteyen yer için (Ses.has) = seçilen aday
    return out


def target_for(name):
    pre = name.rstrip('0123456789').rstrip('_')
    return TARGET.get(pre, -12.0)


def stats(x):
    n = len(x)
    X = np.abs(np.fft.rfft(x * np.hanning(n))) ** 2
    f = np.fft.rfftfreq(n, 1 / SR)
    w = int(0.01 * SR)
    e = np.sqrt(np.convolve(x ** 2, np.ones(w) / w, 'same')) + 1e-9
    edb = 20 * np.log10(e / e.max())
    idx = np.where(edb < -40)[0]
    return {'tepe_hz': int(f[np.argmax(X * (f > 300))]), 'merkez_hz': int((f * X).sum() / X.sum()),
            't40': round(idx[0] / SR if len(idx) else n / SR, 2), '0.6-3kHz_%': int(100 * X[(f > 600) & (f < 3000)].sum() / X.sum()),
            'yukseklik': round(loudness(x), 1), 'sure': round(n / SR, 2)}


def main():
    allx = build_all()
    mp = os.path.join(A, 'sfx.json')
    meta = json.load(open(mp, encoding='utf-8'))
    for name, x in sorted(allx.items()):
        y = master(x, target_for(name))
        write_wav(os.path.join(A, name + '.wav'), y, SR, None)
        meta[name] = {'loop': False, 'len': round(len(y) / SR, 3), 'hedef_db': target_for(name)}
        print('%-20s %s' % (name, stats(y)))
    json.dump(meta, open(mp, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('yazıldı:', len(allx))


if __name__ == '__main__':
    main()
