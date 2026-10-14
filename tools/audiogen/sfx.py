"""Ses efektleri (prosedürel). Her işlev bir numpy dizisi döndürür; SFX sözlüğü ad -> üretici."""
import math
import numpy as np
from synth import (SR, t_axis, env, exp_env, noise, fft_filter, sine, sweep, pluck, reverb, delay, distort,
                   normalize, mix, place, fade)


# ------------------------------------------------------------ savuruşlar
def swing(dur=0.22, lo=400, hi=5000, seed=1, doppler=(1.6, 0.7)):
    """Kılıç savruluşu: bant gürültüsü, hızla parlayıp kararır (Doppler hissi)."""
    n = noise(dur, seed=seed)
    a = fft_filter(n, lo=lo, hi=hi, slope=1.5)
    b = fft_filter(n, lo=lo * doppler[0], hi=hi * doppler[0], slope=1.5)
    e = env(dur, a=0.02, d=dur - 0.03, r=0.01, curve=4)
    k = np.linspace(1, 0, len(a)) ** 2
    return fade((a * (1 - k) + b * k) * e)


def swing_light(i):
    return swing(0.18 + 0.02 * i, 500 + 80 * i, 6000, seed=10 + i)


def swing_heavy(i):
    x = swing(0.42, 120, 1800, seed=20 + i, doppler=(1.3, 0.6))
    sub = sine(60 - 10 * i, 0.42) * exp_env(0.42, 6) * 0.5
    return fade(mix(x, sub))


def swing_whoosh_big():
    x = swing(0.6, 90, 1400, seed=31, doppler=(1.4, 0.5))
    return fade(mix(x, sine(45, 0.6) * exp_env(0.6, 4) * 0.5))


def thrust():
    x = swing(0.14, 900, 9000, seed=40, doppler=(1.8, 0.8))
    return fade(mix(x, sweep(1200, 300, 0.12) * exp_env(0.12, 25) * 0.4))


# ------------------------------------------------------------ darbeler
def hit_flesh(i):
    dur = 0.26
    thud = sweep(160 - 20 * i, 55, dur, curve=0.6) * exp_env(dur, 18)
    crack = fft_filter(noise(dur, seed=50 + i), lo=800, hi=4500) * exp_env(dur, 55)
    wet = fft_filter(noise(dur, seed=60 + i), lo=200, hi=1500) * exp_env(dur, 22) * 0.6
    return fade(mix(thud * 1.1, crack * 0.6, wet))


def hit_heavy():
    dur = 0.5
    thud = sweep(120, 38, dur, curve=0.5) * exp_env(dur, 9)
    crack = fft_filter(noise(dur, seed=70), lo=300, hi=3000) * exp_env(dur, 30)
    boom = sine(48, dur) * exp_env(dur, 6) * 0.8
    return fade(reverb(mix(thud, crack * 0.7, boom), 0.5, 0.18))


def hit_crit():
    dur = 0.55
    base = hit_heavy()[:int(dur * SR)]
    ring = sweep(2400, 1700, 0.4) * exp_env(0.4, 9) * 0.25
    shimmer = fft_filter(noise(0.4, seed=80), lo=4000, hi=12000) * exp_env(0.4, 12) * 0.3
    return fade(mix(base, ring, shimmer))


def hit_metal(i=0):
    dur = 0.4
    partials = [1.0, 2.76, 5.4, 8.9]
    f0 = 900 + 150 * i
    x = sum(sine(f0 * p, dur) * exp_env(dur, 10 + 6 * k) / (k + 1) for k, p in enumerate(partials))
    clk = fft_filter(noise(0.05, seed=90 + i), lo=2000, hi=9000) * exp_env(0.05, 80)
    return fade(mix(x * 0.5, clk))


def hit_blunt():
    dur = 0.35
    thud = sweep(110, 40, dur, curve=0.5) * exp_env(dur, 14)
    crunch = fft_filter(noise(dur, seed=100), lo=150, hi=1200) * exp_env(dur, 35)
    return fade(mix(thud, crunch * 0.8))


def hit_stone():
    dur = 0.4
    crack = fft_filter(noise(dur, seed=110), lo=600, hi=5000, peak=1800) * exp_env(dur, 28)
    rubble = fft_filter(noise(dur, seed=111), lo=120, hi=900) * env(dur, a=0.01, d=0.3, r=0.05)
    return fade(mix(crack, rubble * 0.6))


def shockwave():
    dur = 0.9
    boom = sweep(90, 28, dur, curve=0.4) * exp_env(dur, 5)
    rumble = fft_filter(noise(dur, seed=120), hi=300) * exp_env(dur, 5)
    debris = fft_filter(noise(dur, seed=121), lo=800, hi=4000) * exp_env(dur, 12) * 0.4
    return fade(reverb(mix(boom, rumble, debris), 0.8, 0.2))


# ------------------------------------------------------------ yaratıklar
def growl(f0=90, dur=0.35, seed=130, grit=6.0):
    t = t_axis(dur)
    vib = 1 + 0.08 * np.sin(2 * np.pi * 28 * t)
    ph = 2 * np.pi * np.cumsum(f0 * vib) / SR
    x = np.sign(np.sin(ph)) * 0.5 + np.sin(ph * 2) * 0.3
    x = fft_filter(x * (1 + 0.6 * noise(dur, seed=seed)), lo=120, hi=2500, peak=700, q=2)
    return fade(distort(x, grit) * env(dur, a=0.02, d=dur - 0.08, r=0.05))


def wolf_hurt(i):
    return growl(130 + 30 * i, 0.3, 140 + i)


def wolf_die():
    x = growl(150, 0.7, 150)
    yelp = sweep(900, 400, 0.5) * exp_env(0.5, 6) * 0.3
    return fade(mix(x, yelp))


def cor_hurt(i):
    x = fft_filter(noise(0.25, seed=160 + i), lo=1500, hi=7000) * exp_env(0.25, 20)
    chirp = sweep(1800 + 300 * i, 900, 0.2) * exp_env(0.2, 12) * 0.5
    return fade(mix(x * 0.5, chirp))


def cor_die():
    pop = sweep(400, 80, 0.2) * exp_env(0.2, 20)
    hiss = fft_filter(noise(0.6, seed=170), lo=2000, hi=9000) * exp_env(0.6, 7) * 0.5
    return fade(mix(pop, hiss))


def treant_hurt(i):
    creak = fft_filter(noise(0.4, seed=180 + i), lo=200, hi=1200, peak=400 + 60 * i, q=6) * env(0.4, a=0.02, d=0.3, r=0.05)
    return fade(mix(creak, growl(60, 0.35, 185 + i, 3.0) * 0.5))


def treant_die():
    x = treant_hurt(2)
    crash = fft_filter(noise(0.9, seed=190), lo=100, hi=2500) * exp_env(0.9, 6)
    return fade(mix(x, crash * 0.8, sine(50, 0.9) * exp_env(0.9, 5) * 0.4))


def stone_hurt(i):
    return hit_stone() * 0.8


def stone_die():
    x = hit_stone()
    rumble = fft_filter(noise(1.0, seed=200), hi=400) * exp_env(1.0, 5)
    return fade(mix(x, rumble, sine(42, 1.0) * exp_env(1.0, 4) * 0.5))


def ghost_hurt(i):
    t = t_axis(0.4)
    x = np.sin(2 * np.pi * (500 + 80 * i) * t + 3 * np.sin(2 * np.pi * 7 * t)) * exp_env(0.4, 8)
    return fade(reverb(x * 0.6, 0.8, 0.35))


def ghost_die():
    x = sweep(700, 2500, 0.8) * exp_env(0.8, 5)
    air = fft_filter(noise(0.8, seed=210), lo=3000, hi=10000) * exp_env(0.8, 5) * 0.4
    return fade(reverb(mix(x * 0.5, air), 1.0, 0.4))


def enemy_attack_windup():
    x = fft_filter(noise(0.35, seed=220), lo=300, hi=2500) * env(0.35, a=0.25, d=0.08, r=0.02)
    return fade(mix(x, growl(80, 0.35, 221, 4) * 0.4))


# ------------------------------------------------------------ kahraman
def player_hurt():
    x = growl(220, 0.25, 230, 3.0)
    x = fft_filter(x, lo=250, hi=3500)
    return fade(mix(x, hit_flesh(0)[:len(x)] * 0.6))


def player_die():
    x = growl(200, 0.9, 240, 3.0) * env(0.9, a=0.05, d=0.7, r=0.1)
    tone = sweep(600, 150, 1.2) * exp_env(1.2, 3) * 0.3
    return fade(reverb(mix(x, tone), 1.5, 0.4))


def jump():
    x = fft_filter(noise(0.12, seed=250), lo=400, hi=3000) * exp_env(0.12, 30)
    return fade(mix(x, sweep(300, 700, 0.1) * exp_env(0.1, 30) * 0.3))


def land(i):
    dur = 0.18 + 0.1 * i
    thud = sweep(140, 50, dur, curve=0.6) * exp_env(dur, 20)
    grit = fft_filter(noise(dur, seed=260 + i), lo=300, hi=3000) * exp_env(dur, 40) * 0.5
    return fade(mix(thud * (0.7 + 0.3 * i), grit))


def roll():
    x = fft_filter(noise(0.3, seed=270), lo=200, hi=2000) * env(0.3, a=0.03, d=0.2, r=0.05)
    sw = swing(0.25, 300, 2500, seed=271) * 0.6
    return fade(mix(x, sw))


def step(i):
    dur = 0.09
    x = fft_filter(noise(dur, seed=280 + i), lo=200, hi=2500) * exp_env(dur, 50)
    return fade(mix(x, sweep(120, 70, dur) * exp_env(dur, 40) * 0.4))


def drink():
    x = np.zeros(int(0.5 * SR))
    for k in range(3):
        g = sweep(500 + 120 * k, 900 + 150 * k, 0.08) * exp_env(0.08, 20)
        place(x, g, 0.12 * k, 0.5)
    place(x, fft_filter(noise(0.3, seed=290), lo=800, hi=4000) * env(0.3, a=0.1, d=0.15, r=0.05), 0.0, 0.3)
    return fade(x)


# ------------------------------------------------------------ ağır saldırı / kut
def charge_loop():
    dur = 1.0
    t = t_axis(dur)
    x = np.sin(2 * np.pi * 110 * t) * 0.3 + np.sin(2 * np.pi * 165 * t) * 0.2
    x *= 1 + 0.4 * np.sin(2 * np.pi * 9 * t)
    sh = fft_filter(noise(dur, seed=300), lo=2500, hi=9000) * 0.15 * (0.5 + 0.5 * np.sin(2 * np.pi * 12 * t))
    return mix(x, sh)  # döngü: fade yok


def charge_full():
    x = sweep(400, 1600, 0.25) * exp_env(0.25, 8)
    chime = sum(sine(f, 0.5) * exp_env(0.5, 6) for f in (1320, 1980, 2640)) * 0.2
    return fade(mix(x * 0.6, chime))


def heavy_release():
    x = swing_whoosh_big()
    return fade(mix(x, sweep(600, 120, 0.3) * exp_env(0.3, 10) * 0.5))


def kut_transform():
    dur = 1.4
    rise = sweep(120, 900, 0.8, curve=1.5) * env(0.8, a=0.3, d=0.4, r=0.1)
    boom = sine(48, dur) * exp_env(dur, 3) * 0.7
    howl = growl(260, 1.0, 310, 2.0) * env(1.0, a=0.2, d=0.6, r=0.2)
    air = fft_filter(noise(dur, seed=311), lo=1000, hi=8000) * env(dur, a=0.4, d=0.8, r=0.2) * 0.4
    x = np.zeros(int(dur * SR))
    place(x, rise, 0.0); place(x, boom, 0.6); place(x, howl, 0.55, 0.6); place(x, air, 0.0)
    return fade(reverb(x, 1.5, 0.35))


def wolf_howl():
    dur = 1.6
    t = t_axis(dur)
    f = 330 * (1 + 0.5 * np.sin(np.pi * t / dur) ** 0.7) * (1 + 0.02 * np.sin(2 * np.pi * 5.5 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * 0.6 + np.sin(2 * ph) * 0.25 + np.sin(3 * ph) * 0.1
    x *= env(dur, a=0.15, d=1.0, s=0.5, r=0.4)
    return fade(reverb(x, 1.8, 0.4))


def wolf_bite(i):
    snap = fft_filter(noise(0.12, seed=320 + i), lo=800, hi=6000) * exp_env(0.12, 45)
    x = mix(growl(110 + 20 * i, 0.25, 325 + i), snap * 0.8, hit_flesh(i)[:int(0.25 * SR)] * 0.7)
    return fade(x)


def pounce():
    x = swing(0.35, 200, 3000, seed=330, doppler=(1.5, 0.6))
    return fade(mix(x, growl(140, 0.3, 331) * 0.5))


# ------------------------------------------------------------ yay / mermi / büyü
def bow_draw():
    x = fft_filter(noise(0.4, seed=340), lo=300, hi=2000, peak=600, q=3) * env(0.4, a=0.05, d=0.3, r=0.05)
    creak = sweep(180, 260, 0.4) * env(0.4, a=0.1, d=0.25, r=0.05) * 0.2
    return fade(mix(x * 0.6, creak))


def bow_release():
    tw = sweep(900, 300, 0.15) * exp_env(0.15, 25)
    air = fft_filter(noise(0.25, seed=350), lo=1500, hi=9000) * exp_env(0.25, 18)
    return fade(mix(tw * 0.6, air))


def arrow_hit():
    x = fft_filter(noise(0.15, seed=360), lo=600, hi=5000) * exp_env(0.15, 40)
    return fade(mix(x, sweep(300, 120, 0.12) * exp_env(0.12, 30) * 0.6))


def explosion():
    dur = 1.1
    boom = sweep(150, 30, dur, curve=0.4) * exp_env(dur, 5)
    crack = fft_filter(noise(dur, seed=370), lo=400, hi=6000) * exp_env(dur, 14)
    rumble = fft_filter(noise(dur, seed=371), hi=250) * exp_env(dur, 4)
    return fade(reverb(distort(mix(boom, crack * 0.8, rumble), 2.0), 1.0, 0.25))


def magic_cast():
    dur = 0.6
    t = t_axis(dur)
    x = np.sin(2 * np.pi * 660 * t + 4 * np.sin(2 * np.pi * 110 * t)) * exp_env(dur, 6)
    sh = fft_filter(noise(dur, seed=380), lo=3000, hi=11000) * exp_env(dur, 8) * 0.4
    return fade(reverb(mix(x * 0.5, sh), 1.0, 0.3))


def lightning():
    crack = fft_filter(noise(0.5, seed=390), lo=1500, hi=12000) * exp_env(0.5, 25)
    buzz = np.sign(np.sin(2 * np.pi * 90 * t_axis(0.5))) * exp_env(0.5, 10) * 0.3
    boom = sweep(120, 40, 0.6) * exp_env(0.6, 7) * 0.6
    return fade(reverb(mix(crack, buzz, boom), 1.0, 0.3))


def freeze():
    dur = 0.6
    shimmer = sum(sine(f, dur) * exp_env(dur, 5 + k) for k, f in enumerate((2200, 3300, 4400, 5600))) * 0.15
    crackle = fft_filter(noise(dur, seed=400), lo=3000, hi=12000) * (noise(dur, seed=401) > 0.92) * exp_env(dur, 6)
    return fade(mix(shimmer, crackle * 0.5))


def fire_loop():
    dur = 1.5
    x = fft_filter(noise(dur, seed=410), lo=200, hi=3000)
    x *= 0.6 + 0.4 * fft_filter(noise(dur, seed=411), hi=12) * 3
    return x * 0.5


def poison():
    x = np.zeros(int(0.6 * SR))
    for k in range(6):
        b = sweep(300 + 90 * k, 600 + 90 * k, 0.07) * exp_env(0.07, 25)
        place(x, b, 0.08 * k, 0.4)
    return fade(mix(x, fft_filter(noise(0.6, seed=420), lo=500, hi=2500) * exp_env(0.6, 6) * 0.3))


# ------------------------------------------------------------ toplama / arayüz
def pickup_gold():
    x = sum(sine(f, 0.18) * exp_env(0.18, 18) for f in (2100, 2640)) * 0.4
    return fade(mix(x, sweep(1500, 2600, 0.06) * exp_env(0.06, 20) * 0.3))


def pickup_kut():
    dur = 0.35
    x = sum(sine(f, dur) * exp_env(dur, 7 + k * 2) for k, f in enumerate((1047, 1319, 1568, 2093))) * 0.25
    sh = fft_filter(noise(dur, seed=430), lo=5000, hi=12000) * exp_env(dur, 12) * 0.2
    return fade(reverb(mix(x, sh), 0.6, 0.25))


def pickup_item():
    x = np.zeros(int(0.4 * SR))
    for k, f in enumerate((523, 659, 784)):
        place(x, sine(f, 0.25) * exp_env(0.25, 8) * 0.3, 0.07 * k)
    return fade(reverb(x, 0.5, 0.2))


def scroll():
    x = np.zeros(int(0.9 * SR))
    for k, f in enumerate((392, 494, 587, 784)):
        place(x, pluck(f, 0.7, bright=0.7, seed=440 + k) * 0.5, 0.12 * k)
    return fade(reverb(x, 1.2, 0.3))


def ui_move():
    return fade(sine(1200, 0.05) * exp_env(0.05, 40) * 0.5)


def ui_confirm():
    return fade(mix(sine(880, 0.12) * exp_env(0.12, 15), sine(1320, 0.18) * exp_env(0.18, 12) * 0.6) * 0.5)


def unlock():
    x = np.zeros(int(1.2 * SR))
    for k, f in enumerate((523, 659, 784, 1047)):
        place(x, pluck(f, 0.9, bright=0.6, seed=450 + k) * 0.5, 0.1 * k)
    place(x, hit_metal(1) * 0.5, 0.35)
    return fade(reverb(x, 1.2, 0.3))


def gate():
    dur = 1.6
    t = t_axis(dur)
    x = np.sin(2 * np.pi * 110 * t + 2 * np.sin(2 * np.pi * 0.5 * t)) * env(dur, a=0.3, d=1.0, r=0.3) * 0.4
    sh = fft_filter(noise(dur, seed=460), lo=2000, hi=9000) * env(dur, a=0.5, d=0.8, r=0.3) * 0.3
    ch = sum(sine(f, dur) * env(dur, a=0.4, d=0.9, r=0.3) for f in (880, 1320, 1760)) * 0.12
    return fade(reverb(mix(x, sh, ch), 2.0, 0.45))


def npc_blip(i):
    return fade(sine(600 + 120 * i, 0.06) * exp_env(0.06, 30) * 0.4)


def anvil():
    return fade(mix(hit_metal(2), hit_blunt() * 0.4))


def kut_bank():
    x = np.zeros(int(1.4 * SR))
    for k in range(8):
        place(x, sine(1047 * (1 + 0.5 * (k % 3)), 0.25) * exp_env(0.25, 10) * 0.25, 0.09 * k)
    place(x, pickup_kut(), 0.75, 1.0)
    return fade(reverb(x, 1.2, 0.3))


SFX = {
    'savur_hafif_1': lambda: swing_light(0), 'savur_hafif_2': lambda: swing_light(1), 'savur_hafif_3': lambda: swing_light(2),
    'savur_agir_1': lambda: swing_heavy(0), 'savur_agir_2': lambda: swing_heavy(1), 'savur_dev': swing_whoosh_big, 'sapla': thrust,
    'darbe_et_1': lambda: hit_flesh(0), 'darbe_et_2': lambda: hit_flesh(1), 'darbe_et_3': lambda: hit_flesh(2),
    'darbe_agir': hit_heavy, 'darbe_kritik': hit_crit, 'darbe_metal_1': lambda: hit_metal(0), 'darbe_metal_2': lambda: hit_metal(1),
    'darbe_kunt': hit_blunt, 'darbe_tas': hit_stone, 'sarsinti': shockwave,
    'kurt_can_1': lambda: wolf_hurt(0), 'kurt_can_2': lambda: wolf_hurt(1), 'kurt_olum': wolf_die,
    'cor_can_1': lambda: cor_hurt(0), 'cor_can_2': lambda: cor_hurt(1), 'cor_olum': cor_die,
    'agac_can_1': lambda: treant_hurt(0), 'agac_can_2': lambda: treant_hurt(1), 'agac_olum': treant_die,
    'tas_can_1': lambda: stone_hurt(0), 'tas_olum': stone_die,
    'hayalet_can_1': lambda: ghost_hurt(0), 'hayalet_can_2': lambda: ghost_hurt(1), 'hayalet_olum': ghost_die,
    'dusman_hazirlik': enemy_attack_windup,
    'bengu_can': player_hurt, 'bengu_olum': player_die, 'zipla': jump, 'inis_1': lambda: land(0), 'inis_2': lambda: land(1),
    'yuvarlan': roll, 'adim_1': lambda: step(0), 'adim_2': lambda: step(1), 'sise': drink,
    'sarj_dongu': charge_loop, 'sarj_dolu': charge_full, 'agir_birak': heavy_release,
    'kut_donusum': kut_transform, 'uluma': wolf_howl, 'isirik_1': lambda: wolf_bite(0), 'isirik_2': lambda: wolf_bite(1), 'sicrayis': pounce,
    'yay_ger': bow_draw, 'yay_birak': bow_release, 'ok_vurus': arrow_hit, 'patlama': explosion, 'buyu': magic_cast,
    'yildirim': lightning, 'donma': freeze, 'ates_dongu': fire_loop, 'zehir': poison,
    'altin': pickup_gold, 'kut_tane': pickup_kut, 'esya': pickup_item, 'tilsim': scroll,
    'ui_sec': ui_move, 'ui_onay': ui_confirm, 'acilis': unlock, 'kapi': gate,
    'npc_1': lambda: npc_blip(0), 'npc_2': lambda: npc_blip(1), 'npc_3': lambda: npc_blip(2), 'ors': anvil, 'kut_banka': kut_bank,
}
