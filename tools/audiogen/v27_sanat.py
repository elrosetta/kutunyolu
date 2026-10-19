"""v27 Savaş Sanatları sesleri (SavasSanati.gd). Hepsi sentez + mevcut yapı taşları (pro.py, impact.py, v25.py):
  sanat_baslat   telegraf: derin davul "dum" + yükselen hava süpürmesi + kısa çelik "şing" (sanat başlıyor, okunur)
  sanat_hazir    yeni Alp Nişanı / sanat hazır: iki notalı yumuşak çan (müzikle aynı dizi, Hüseyni)
  sanat_kasirga  Kasırga Kesişi: dönen rüzgâr (bant merkezi ve genliği tur hızında salınan gürültü) + uğultu
  sanat_hilal    Ay Hilali: keskin çekiş süpürmesi + camsı ay parıltısı (titreşen ince tonlar)
  sanat_cekis    Bir Çekiş / dalış inişi: dev gövde "güm" + kaya çatırtısı + uzun gürleme kuyruğu
  sanat_yuksel   Göğe Yükseliş: yükselen süpürme (bant merkezi tırmanır)
  sanat_atilis   Bozkurt Atılışı hazırlığı: kısa kurt soluğu + sert hava patlaması
  sanat_kin      Bozkurt Atılışı kın sesi: bıçak kına "çıt" + ardından kesik çatırtıları
  sanat_kam      Kam Darbesi: kam davulu (çerçeve davul) + boğaz uğultusu + ruh süpürmesi
  sanat_ors      Demir Duruş: örs çınlaması (inharmonik çelik kısmiler, uzun) + vuruş tıkı
  sanat_gum      v28 Göğe Yükseliş çakılışı ("GÜM!"): iki katlı dev gövde vuruşu (taiko + alt bas düşüşü), toprak
                 ezilmesi, taş çatırtısı ve saçılan döküntü, ıslak mürekkep şaplağı, kısa altın çınlama, uzun gürleme
Yeniden üretim: python tools/audiogen/v27_sanat.py [ses adları...]   (ad verilirse yalnız onlar; ya da export_audio.py --sfx sanat_...; hedef yükseklik aşağıda)"""
import os
import sys
import json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, t_axis, exp_env, noise, sine, sweep, distort, fade, hp, lp, bp, voice, write_wav, master
from pro import click, thump, tail, whoosh, metal_ring, room, rumble, crackle, note, bell
from impact import crunch, glue, cut, shing, boom_sub
from v25 import chime, air, steel

TARGET = {"sanat_baslat": -10.0, "sanat_hazir": -15.0, "sanat_kasirga": -12.0, "sanat_hilal": -11.0, "sanat_cekis": -7.5,
          "sanat_yuksel": -12.0, "sanat_atilis": -12.0, "sanat_kin": -9.5, "sanat_kam": -10.0, "sanat_ors": -9.0,
          "sanat_gum": -6.5}


def _mix(parts, dur):
    out = np.zeros(int(dur * SR))
    for x, at, g in parts:
        s = int(at * SR)
        n = min(len(x), len(out) - s)
        if n > 0:
            out[s:s + n] += x[:n] * g
    return out


def baslat():
    dur = 0.75
    drum = thump(120, 46, 0.5, 9, 1.6)
    return room(_mix([
        (drum, 0.0, 1.0),
        (lp(noise(0.06, seed=271), 700) * exp_env(0.06, 50), 0.0, 0.5),
        (whoosh(0.42, 300, 5200, 0.8, seed=272, q=0.9), 0.04, 0.6),
        (shing(0.32, 4200, 11000, seed=273, g=1.0, ring_f=3900.0), 0.38, 0.45),
        (chime(note('E5'), 0.4, 8.0, 5.0), 0.4, 0.18),
    ], dur), 0.4, 0.18)


def hazir():
    dur = 0.5
    return room(_mix([(chime(note('B5'), 0.36, 9.0, 5.5), 0.0, 0.5), (chime(note('E6'), 0.32, 10.0, 6.5), 0.07, 0.35),
                      (air(0.25, 3500, 9000, 274, 12.0), 0.0, 0.12)], dur), 0.3, 0.15)


def kasirga():
    dur = 0.62
    t = t_axis(dur)
    n = noise(dur, seed=275)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 3.4 * t - 1.2)
    lo = bp(n, 300, 1400) * (0.35 + 0.65 * lfo)
    hi = bp(n, 1800, 6000) * (0.2 + 0.8 * (1 - lfo)) * 0.6
    env_ = np.minimum(1.0, t / 0.05) * np.exp(-np.maximum(0.0, t - 0.4) * 9.0)
    hum = sweep(110, 160, dur, curve=0.6) * 0.18
    return fade((lo + hi + hum) * env_, 0.004, 0.06)


def hilal():
    dur = 0.6
    t = t_axis(0.45)
    shimmer = (np.sin(2 * np.pi * 2637 * t) + 0.8 * np.sin(2 * np.pi * 2643 * t + 0.7) + 0.4 * np.sin(2 * np.pi * 3951 * t)) * exp_env(0.45, 7.0) * 0.4
    return room(_mix([
        (whoosh(0.26, 900, 7500, 0.35, seed=276, q=0.8), 0.0, 1.0),
        (click(0.01, 3000, 12000, 277), 0.06, 0.6),
        (shimmer, 0.06, 0.55),
        (air(0.4, 4000, 10000, 278, 6.0), 0.06, 0.25),
    ], dur), 0.5, 0.22)


def cekis():
    dur = 1.0
    return glue(room(_mix([
        (click(0.01, 1500, 9000, 279), 0.0, 0.8),
        (crunch(0.14, 280, 200, 3000, 6.0, 80.0), 0.0, 0.9),
        (boom_sub(78.0, 40.0, 0.2, 0.75, 4.5, 0.003, 2.2), 0.0, 1.2),
        (rumble(0.9, 160, 3.5, 281), 0.03, 0.7),
        (crackle(0.5, 30, 282, 1500, 7000), 0.04, 0.35),
    ], dur), 0.6, 0.2), 1.4)


def yuksel():
    dur = 0.45
    return _mix([(whoosh(0.4, 250, 6500, 0.85, seed=283, q=1.0, k_up=1.4), 0.0, 1.0), (air(0.3, 3000, 9000, 284, 8.0), 0.15, 0.25)], dur)


def atilis():
    dur = 0.4
    breath = voice(95.0, 0.22, vowels=('a', 'o'), size=1.3, breath=0.9, grit=0.25, seed=285)
    return _mix([(breath * exp_env(0.22, 9.0) * 0.5, 0.0, 1.0), (whoosh(0.2, 1200, 9000, 0.6, seed=286, q=0.7), 0.12, 0.9),
                 (click(0.008, 4000, 12000, 287), 0.2, 0.4)], dur)


def kin():
    dur = 0.55
    parts = [(click(0.012, 2000, 9000, 288), 0.0, 1.0), (steel(3200.0, 0.06, 70.0, seed=289), 0.0, 0.5), (metal_ring(2900, 0.2, 22, seed=290), 0.0, 0.25)]
    for j in range(3):
        parts.append((crunch(0.05, 291 + j, 900, 7000, 5.0, 140.0), 0.08 + 0.035 * j, 0.55))
        parts.append((shing(0.12, 5000, 11000, seed=294 + j, g=0.7, ring_f=4600.0 + 300 * j), 0.08 + 0.035 * j, 0.3))
    return room(_mix(parts, dur), 0.35, 0.15)


def kam():
    dur = 0.8
    t = t_axis(0.5)
    membrane = (np.sin(2 * np.pi * (95 + 40 * np.exp(-t * 30)) * t) * exp_env(0.5, 7.0)) * 0.9
    skin = bp(noise(0.12, seed=297), 300, 2500) * exp_env(0.12, 30.0) * 0.6
    drone = voice(73.0, 0.55, vowels=('o', 'u'), size=1.4, breath=0.3, grit=0.15, seed=298, sub=0.4) * exp_env(0.55, 4.0) * 0.35
    return room(_mix([(membrane, 0.0, 1.0), (skin, 0.0, 1.0), (drone, 0.03, 1.0),
                      (whoosh(0.35, 400, 4000, 0.6, seed=299, q=1.1), 0.12, 0.45)], dur), 0.55, 0.25)


def ors():
    dur = 0.9
    return room(_mix([(click(0.008, 2500, 12000, 302), 0.0, 1.0), (crunch(0.03, 303, 800, 6000, 4.0, 200.0), 0.0, 0.5),
                      (metal_ring(1180, 0.85, 4.5, parts=(1.0, 2.76, 5.40, 8.93, 1.51), seed=300), 0.0, 0.9),
                      (metal_ring(2210, 0.5, 9.0, seed=301), 0.0, 0.4)], dur), 0.45, 0.2)


def gum():
    dur = 1.3
    return glue(room(_mix([
        (click(0.012, 1200, 8000, 305), 0.0, 0.9),
        (thump(150, 38, 0.55, 7, 2.2), 0.0, 1.1),
        (boom_sub(64.0, 33.0, 0.22, 1.0, 3.6, 0.003, 2.4), 0.0, 1.3),
        (thump(110, 44, 0.4, 9, 1.8), 0.075, 0.6),                       # ikinci kat: gövdenin yere oturması
        (crunch(0.2, 306, 160, 2600, 6.5, 70.0), 0.0, 1.0),
        (lp(noise(0.09, seed=307), 1800) * exp_env(0.09, 35.0), 0.005, 0.7),   # ıslak şaplak
        (crackle(0.7, 46, 308, 1200, 7500), 0.05, 0.4),
        (rumble(1.2, 140, 2.6, 309), 0.04, 0.85),
        (shing(0.35, 3800, 10500, seed=310, g=0.8, ring_f=3300.0), 0.02, 0.16),
    ], dur), 0.7, 0.22), 1.5)


def build_all():
    return {"sanat_baslat": baslat(), "sanat_hazir": hazir(), "sanat_kasirga": kasirga(), "sanat_hilal": hilal(),
            "sanat_cekis": cekis(), "sanat_yuksel": yuksel(), "sanat_atilis": atilis(), "sanat_kin": kin(),
            "sanat_kam": kam(), "sanat_ors": ors(), "sanat_gum": gum()}


if __name__ == '__main__':
    A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'audio', 'sfx')
    meta_p = os.path.join(A, 'sfx.json')
    meta = json.load(open(meta_p, encoding='utf-8'))
    only = set(sys.argv[1:])
    for k, v in build_all().items():
        if only and k not in only:
            continue
        y = master(v, TARGET.get(k, -12.0))
        write_wav(os.path.join(A, k + '.wav'), y, SR, None)
        meta[k] = {'loop': False, 'len': round(len(y) / SR, 3), 'hedef_db': TARGET.get(k, -12.0)}
        print(k, round(len(y) / SR, 3))
    json.dump(meta, open(meta_p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
