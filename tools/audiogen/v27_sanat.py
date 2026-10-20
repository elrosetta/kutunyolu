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
v31 kombo sanatları:
  sanat_dans     Kurt Dansı atılışı: kısa keskin "fışt" (dar bant süpürme) + ince çelik sürtme
  sanat_cit      Kurt Dansı "ÇIT!": kına giriş tıkı, kısa sessizlik, ardından birden patlayan kesik çatırtıları ve çelik şingi
v32 özgün sanatlar (Evren Kuyruğu / Tengri Çarkı / Yer Yarığı seslerinin yerine):
  sanat_pesrev   Pehlivan Savurması peşrevi: derin soluk + dize vurulan iki avuç şakı + toz süpürmesi
  sanat_tutus    kavrama: deri / kuşak gıcırtısı + gövde toku + kısa homurtu
  sanat_savur    çekiç savurması (yarım tur başına): alçak dönen ağır süpürme + ip ıslığı
  sanat_firlat   fırlatış: sert yukarı kıvrılan süpürme + homurtu + hava
  sanat_pat      "PAT!": ıslak şaplak + gövde toku + toprak ezilmesi + kısa gürleme
  sanat_kazik    Yıldırım Ağı kazığı: elektrik "cızz" (yüksek çatırtı + inen ton) + kazık toku
  sanat_ag       şimşek ağı: titreyen elektrik uğultusu (110 Hz harmonikler + genlik çırpıntısı) + ince çatırtı
  sanat_cak      "ÇAK!": yıldırım çatlaması (keskin tık + geniş bant patlama + kırpma) + gök gürlemesi kuyruğu
  sanat_davul    Tulpar Dörtnalı davul vuruşu: çerçeve davul zarı (perde düşen sinüs) + deri + oda
  sanat_dortnal  dörtnal: art arda toynak vuruşları (toprak) + rüzgâr + at soluğu / kişneme kırıntısı
  sanat_akin     Akıncı Akını yelpazesi: art arda beş kiriş tıngısı ve ok vızıltıları
  sanat_viz      Akıncı Akını delen ok "VIZ!": derin kiriş, ıslıklı uzun vızıltı (inen perde), hava yırtılması
  sanat_tam      ritim TAM: parlak tahta tok + iki notalı kısa çan
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
          "sanat_gum": -6.5, "sanat_dans": -13.0, "sanat_cit": -8.5, "sanat_akin": -11.0,
          "sanat_viz": -8.5, "sanat_tam": -12.0,
          "sanat_pesrev": -12.0, "sanat_tutus": -10.0, "sanat_savur": -12.5, "sanat_firlat": -11.0, "sanat_pat": -7.0,
          "sanat_kazik": -11.0, "sanat_ag": -14.0, "sanat_cak": -7.0, "sanat_davul": -9.0, "sanat_dortnal": -8.5}


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


# ------------------------------------------------------------------ v31 kombo sanatları
def dans():
    dur = 0.3
    return _mix([(whoosh(0.16, 1500, 9500, 0.3, seed=320, q=0.6, k_up=2.5), 0.0, 1.0),
                 (air(0.18, 5000, 11000, 321, 14.0), 0.0, 0.5),
                 (steel(4200.0, 0.05, 80.0, seed=322), 0.07, 0.25)], dur)


def cit():
    dur = 0.75
    parts = [(click(0.01, 2500, 10000, 323), 0.0, 1.0), (steel(3600.0, 0.05, 90.0, seed=324), 0.0, 0.5),
             (metal_ring(3300, 0.25, 18, seed=325), 0.0, 0.2)]
    # kısa sessizlik; sonra izler birden patlar
    for j in range(5):
        parts.append((crunch(0.06, 326 + j, 700, 7500, 5.5, 150.0), 0.1 + 0.018 * j, 0.6))
        parts.append((shing(0.16, 4500, 11000, seed=331 + j, g=0.7, ring_f=4200.0 + 250 * j), 0.1 + 0.018 * j, 0.3))
    parts.append((boom_sub(90.0, 50.0, 0.12, 0.35, 7.0, 0.003, 1.6), 0.1, 0.6))
    return room(_mix(parts, dur), 0.4, 0.18)


# ------------------------------------------------------------------ v32 özgün sanatlar
def pesrev():
    dur = 0.55
    breath = voice(90.0, 0.3, vowels=('a', 'o'), size=1.4, breath=0.9, grit=0.35, seed=400) * exp_env(0.3, 6.0) * 0.45
    parts = [(breath, 0.0, 1.0), (whoosh(0.3, 200, 2200, 0.5, seed=401, q=1.1), 0.05, 0.5)]
    for j in range(2):   # dize vurulan avuçlar: şak, şak
        parts.append((click(0.01, 900, 5000, 402 + j), 0.16 + 0.11 * j, 0.9))
        parts.append((bp(noise(0.05, seed=404 + j), 500, 3500) * exp_env(0.05, 45.0), 0.16 + 0.11 * j, 0.8))
        parts.append((thump(220, 110, 0.08, 20, 1.3), 0.16 + 0.11 * j, 0.5))
    return room(_mix(parts, dur), 0.35, 0.14)


def tutus():
    dur = 0.4
    grunt = voice(110.0, 0.18, vowels=('u', 'a'), size=1.2, breath=0.4, grit=0.7, seed=410) * exp_env(0.18, 12.0) * 0.4
    return room(_mix([(crunch(0.06, 411, 500, 3200, 4.0, 110.0), 0.0, 0.7),          # deri / kuşak
                      (thump(120, 52, 0.22, 12, 1.6), 0.01, 0.9),
                      (lp(noise(0.05, seed=412), 1500) * exp_env(0.05, 40.0), 0.0, 0.5),
                      (grunt, 0.03, 1.0)], dur), 0.3, 0.14)


def savur():
    dur = 0.5
    t = t_axis(dur)
    n = noise(dur, seed=420)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 2.6 * t - 1.0)
    lo = bp(n, 160, 1100) * (0.4 + 0.6 * lfo)
    hi = bp(n, 1400, 4500) * (0.25 + 0.75 * (1 - lfo)) * 0.45
    env_ = np.minimum(1.0, t / 0.04) * np.exp(-np.maximum(0.0, t - 0.32) * 10.0)
    whistle = sweep(900, 1300, dur, curve=0.8) * 0.06 * lfo
    return fade((lo + hi + whistle) * env_, 0.004, 0.06)


def firlat():
    dur = 0.5
    grunt = voice(120.0, 0.2, vowels=('a',), size=1.3, breath=0.5, grit=0.8, seed=430) * exp_env(0.2, 9.0) * 0.45
    return room(_mix([(whoosh(0.3, 300, 6000, 0.3, seed=431, q=0.8, k_up=2.2), 0.0, 1.0),
                      (air(0.3, 3500, 9500, 432, 9.0), 0.04, 0.3), (grunt, 0.0, 1.0)], dur), 0.35, 0.15)


def pat():
    dur = 0.95
    return glue(room(_mix([
        (lp(noise(0.08, seed=440), 2200) * exp_env(0.08, 32.0), 0.0, 1.0),        # ıslak şaplak
        (click(0.01, 1000, 6000, 441), 0.0, 0.8),
        (thump(140, 44, 0.4, 9, 2.0), 0.0, 1.1),
        (boom_sub(72.0, 40.0, 0.18, 0.6, 4.2, 0.003, 2.0), 0.0, 0.9),
        (crunch(0.14, 442, 200, 2600, 6.0, 80.0), 0.0, 0.8),
        (rumble(0.7, 150, 3.4, 443), 0.03, 0.55),
    ], dur), 0.55, 0.2), 1.4)


def kazik():
    dur = 0.4
    t = t_axis(0.16)
    zap = np.sin(2 * np.pi * np.cumsum(3200 * np.exp(-t * 14) + 500) / SR) * exp_env(0.16, 14.0) * 0.3
    return room(_mix([(crackle(0.14, 26, 450, 2500, 11000), 0.0, 0.9), (zap, 0.0, 1.0),
                      (click(0.008, 1500, 8000, 451), 0.1, 0.9), (thump(300, 120, 0.1, 18, 1.4), 0.1, 0.7),
                      (crunch(0.04, 452, 400, 3000, 4.0, 150.0), 0.1, 0.4)], dur), 0.3, 0.14)


def ag():
    dur = 0.6
    t = t_axis(dur)
    hum = np.zeros_like(t)
    for k, g in ((1, 1.0), (2, 0.5), (3, 0.35), (5, 0.2), (7, 0.12)):
        hum += np.sin(2 * np.pi * 110.0 * k * t + 0.3 * k) * g
    flut = 0.55 + 0.45 * np.sin(2 * np.pi * 23.0 * t) * np.sin(2 * np.pi * 7.3 * t + 1.0)
    env_ = np.minimum(1.0, t / 0.03) * np.exp(-np.maximum(0.0, t - 0.42) * 12.0)
    body = hum * 0.11 * flut * env_
    return fade(_mix([(body, 0.0, 1.0), (crackle(0.5, 36, 460, 3000, 10000), 0.0, 0.3)], dur), 0.004, 0.06)


def cak():
    dur = 1.1
    burst = distort(bp(noise(0.07, seed=470), 1500, 11000) * exp_env(0.07, 38.0), 4.0)
    return glue(room(_mix([
        (click(0.006, 3000, 14000, 471), 0.0, 1.0),
        (burst, 0.0, 1.0),
        (crackle(0.3, 34, 472, 2000, 10000), 0.01, 0.5),
        (boom_sub(80.0, 44.0, 0.16, 0.7, 4.0, 0.002, 2.0), 0.015, 0.9),
        (thump(150, 46, 0.35, 8, 2.0), 0.015, 0.7),
        (rumble(1.0, 200, 2.8, 473), 0.05, 0.7),
    ], dur), 0.65, 0.22), 1.5)


def davul():
    dur = 0.55
    t = t_axis(0.4)
    membrane = np.sin(2 * np.pi * (88 + 50 * np.exp(-t * 26)) * t) * exp_env(0.4, 8.0) * 0.9
    skin = bp(noise(0.08, seed=480), 400, 2800) * exp_env(0.08, 38.0) * 0.5
    return room(_mix([(membrane, 0.0, 1.0), (skin, 0.0, 1.0), (click(0.006, 1200, 5000, 481), 0.0, 0.4)], dur), 0.5, 0.22)


def dortnal():
    dur = 0.85
    parts = [(whoosh(0.6, 250, 3500, 0.4, seed=490, q=1.1, k_up=1.3), 0.0, 0.55)]
    for j in range(6):   # toynaklar: dörtnal ritmi (ta-ta-dum)
        at = 0.02 + 0.09 * j + (0.03 if j % 3 == 2 else 0.0)
        parts.append((thump(190 - 10 * (j % 2), 85, 0.11, 18, 1.5), at, 0.8 if j % 3 != 2 else 1.0))
        parts.append((crunch(0.04, 491 + j, 250, 2600, 4.5, 130.0), at, 0.45))
    snort = voice(150.0, 0.28, vowels=('o', 'u'), size=1.5, breath=0.8, grit=0.6, seed=498) * exp_env(0.28, 7.0) * 0.3
    parts.append((snort, 0.05, 1.0))
    parts.append((sweep(620, 440, 0.16, curve=0.6) * exp_env(0.16, 12.0) * 0.12, 0.3, 1.0))   # kişneme kırıntısı
    return glue(room(_mix(parts, dur), 0.4, 0.16), 1.2)


def akin():
    dur = 0.7
    parts = []
    for j in range(5):
        tw = sweep(190 + 12 * j, 150, 0.12, curve=0.5) * exp_env(0.12, 30.0) * 0.5
        parts.append((click(0.006, 1500, 6000, 380 + j), 0.035 * j, 0.6))
        parts.append((tw, 0.035 * j, 0.7))
        parts.append((whoosh(0.22, 2500, 8000, 0.25, seed=386 + j, q=0.6, k_up=2.0), 0.035 * j + 0.02, 0.35))
    return room(_mix(parts, dur), 0.35, 0.14)


def viz():
    dur = 1.0
    t = t_axis(0.7)
    f = 2600 * np.exp(-t * 1.4) + 900
    whistle = np.sin(2 * np.pi * np.cumsum(f) / SR) * exp_env(0.7, 3.5) * np.minimum(1.0, t / 0.03) * 0.35
    return room(_mix([(thump(95, 60, 0.2, 18, 1.3), 0.0, 0.8), (click(0.006, 1500, 7000, 390), 0.0, 0.8),
                      (sweep(160, 110, 0.18, curve=0.5) * exp_env(0.18, 18.0) * 0.6, 0.0, 0.9),
                      (whistle, 0.02, 1.0), (whoosh(0.5, 6000, 1200, 0.1, seed=391, q=0.7, k_up=3.0), 0.02, 0.8),
                      (air(0.4, 5000, 11000, 392, 6.0), 0.03, 0.3)], dur), 0.4, 0.16)


def tam():
    dur = 0.6
    wood = bp(noise(0.05, seed=395), 900, 3200) * exp_env(0.05, 60.0)
    return room(_mix([(wood, 0.0, 1.0), (click(0.006, 2500, 9000, 396), 0.0, 0.5),
                      (chime(note('E6'), 0.4, 9.0, 5.0), 0.01, 0.5), (chime(note('B6'), 0.35, 10.0, 6.0), 0.06, 0.35)], dur), 0.35, 0.15)


def build_all():
    return {"sanat_baslat": baslat(), "sanat_hazir": hazir(), "sanat_kasirga": kasirga(), "sanat_hilal": hilal(),
            "sanat_cekis": cekis(), "sanat_yuksel": yuksel(), "sanat_atilis": atilis(), "sanat_kin": kin(),
            "sanat_kam": kam(), "sanat_ors": ors(), "sanat_gum": gum(), "sanat_dans": dans(), "sanat_cit": cit(),
            "sanat_akin": akin(), "sanat_viz": viz(), "sanat_tam": tam(),
            "sanat_pesrev": pesrev(), "sanat_tutus": tutus(), "sanat_savur": savur(), "sanat_firlat": firlat(), "sanat_pat": pat(),
            "sanat_kazik": kazik(), "sanat_ag": ag(), "sanat_cak": cak(), "sanat_davul": davul(), "sanat_dortnal": dortnal()}


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
