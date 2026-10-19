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
  sanat_evren    Evren Kuyruğu hazırlık / süpürme: alçak toprak süpürmesi + boğuk ejder hırıltısı
  sanat_kut      Evren Kuyruğu "KÜT!": tok gövde vuruşu, yerden sekme (ikinci küçük vuruş), toprak, kısa gürleme
  sanat_tengri   Tengri Çarkı girdabı: içe çeken dönen bant (hızlanan salınım) + yükselen gök uğultusu
  sanat_vus      Tengri Çarkı "VUŞ!": dışa patlayan hava, gök gürültüsü çatırtısı, açılan süpürme
  sanat_yarik    Yer Yarığı dövüşü: kaya gövde vuruşu + toprak ezilmesi
  sanat_cat      Yer Yarığı "ÇAT!": taş yarılması (keskin çatırtı) + ilerleyip azalan kırılma tıkırtıları ve gürleme
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
          "sanat_gum": -6.5, "sanat_dans": -13.0, "sanat_cit": -8.5, "sanat_evren": -11.0, "sanat_kut": -7.0,
          "sanat_tengri": -11.0, "sanat_vus": -7.5, "sanat_yarik": -8.0, "sanat_cat": -7.0, "sanat_akin": -11.0,
          "sanat_viz": -8.5, "sanat_tam": -12.0}


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


def evren():
    dur = 0.6
    growl = voice(62.0, 0.5, vowels=('o', 'u'), size=1.6, breath=0.5, grit=0.6, seed=340, sub=0.5) * exp_env(0.5, 4.5) * 0.45
    return room(_mix([(whoosh(0.42, 180, 2600, 0.55, seed=341, q=1.3, k_up=1.2), 0.0, 1.0),
                      (lp(noise(0.3, seed=342), 900) * exp_env(0.3, 9.0), 0.04, 0.5),
                      (growl, 0.02, 1.0)], dur), 0.45, 0.18)


def kut():
    dur = 1.0
    return glue(room(_mix([
        (click(0.01, 1200, 7000, 345), 0.0, 0.8),
        (thump(130, 40, 0.42, 9, 2.0), 0.0, 1.1),
        (boom_sub(70.0, 38.0, 0.18, 0.7, 4.0, 0.003, 2.0), 0.0, 1.0),
        (crunch(0.16, 346, 180, 2400, 6.0, 80.0), 0.0, 0.8),
        (thump(170, 70, 0.18, 14, 1.6), 0.21, 0.45),                     # yerden sekme
        (crunch(0.06, 347, 300, 3000, 5.0, 120.0), 0.21, 0.35),
        (rumble(0.8, 150, 3.2, 348), 0.03, 0.6),
    ], dur), 0.6, 0.2), 1.4)


def tengri():
    dur = 0.75
    t = t_axis(dur)
    n = noise(dur, seed=350)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * (3.0 + 5.0 * t / dur) * t)
    swirl = bp(n, 500, 3500) * (0.3 + 0.7 * lfo) * np.minimum(1.0, t / 0.4) ** 1.5 * np.exp(-np.maximum(0.0, t - 0.6) * 18.0)
    hum = sweep(90, 180, dur, curve=1.4) * 0.15 * np.minimum(1.0, t / 0.3)
    body = fade((swirl + hum) * 0.9, 0.01, 0.06)
    return room(_mix([(body, 0.0, 1.0), (whoosh(0.5, 300, 5000, 0.85, seed=351, q=1.0, k_up=1.0), 0.15, 0.5)], dur), 0.5, 0.2)


def vus():
    dur = 1.0
    return glue(room(_mix([
        (lp(noise(0.08, seed=355), 2500) * exp_env(0.08, 30.0), 0.0, 1.0),
        (boom_sub(80.0, 42.0, 0.15, 0.6, 4.5, 0.002, 2.0), 0.0, 1.0),
        (whoosh(0.35, 3000, 400, 0.15, seed=356, q=0.8, k_up=3.0), 0.0, 0.9),
        (crackle(0.4, 40, 357, 1500, 9000), 0.02, 0.5),
        (rumble(0.9, 220, 3.0, 358), 0.05, 0.55),
        (shing(0.3, 4000, 10000, seed=359, g=0.6, ring_f=3500.0), 0.0, 0.2),
    ], dur), 0.65, 0.22), 1.4)


def yarik():
    dur = 0.7
    return glue(room(_mix([(click(0.01, 1500, 8000, 360), 0.0, 0.8), (thump(110, 42, 0.4, 10, 2.2), 0.0, 1.0),
                           (crunch(0.18, 361, 200, 2800, 6.5, 75.0), 0.0, 0.9), (rumble(0.6, 170, 4.0, 362), 0.02, 0.5)], dur), 0.5, 0.18), 1.3)


def cat():
    dur = 1.2
    parts = [(click(0.008, 2000, 11000, 365), 0.0, 1.0), (crunch(0.1, 366, 600, 6000, 7.0, 140.0), 0.0, 1.0),
             (boom_sub(66.0, 34.0, 0.2, 0.9, 3.6, 0.003, 2.2), 0.0, 1.1), (thump(140, 40, 0.5, 8, 2.0), 0.0, 0.8),
             (rumble(1.1, 150, 2.6, 367), 0.04, 0.8)]
    # yarık ilerler: azalan kırılma tıkırtıları
    for j in range(8):
        parts.append((crunch(0.04, 368 + j, 500, 5000, 5.0, 160.0), 0.08 + 0.045 * j, 0.5 * (1.0 - j / 10.0)))
    return glue(room(_mix(parts, dur), 0.6, 0.2), 1.5)


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
            "sanat_evren": evren(), "sanat_kut": kut(), "sanat_tengri": tengri(), "sanat_vus": vus(), "sanat_yarik": yarik(),
            "sanat_cat": cat(), "sanat_akin": akin(), "sanat_viz": viz(), "sanat_tam": tam()}


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
