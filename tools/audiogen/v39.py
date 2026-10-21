"""v39 sesleri: yeni yaratıkların hazırlık ("!" uyarısı) ve hamle sesleri. Yerel CC0 kayıtlar (OGA RPG Sound Pack NPC /
battle, OGA Swishes, Kenney Impact / RPG Audio) katmanlanır, sentezle tatlandırılır (layer.py yardımcıları).

Hazırlık (hazirlik_<kimlik>_1..2; Enemy._windup_sfx kendiliğinden çalar): yaratığın sesi + gerilme (yükselen süpürme)
  yer_cucesi: kazma kazıması + homurtu        kor_solucani: lav fokurtusu + taş çatırtısı
  sulmus: çıngırak + kıkırtı                 sulmus_yavrusu: tiz cıvıltı
  burkut: kartal çığlığı (kısa)              tunga_hayaleti: hayalet fısıltısı + tunç çınlaması
  yasavul: demir zırh + alev üfürmesi        aldaras: çift orak sürtünmesi
  tepegoz_yavrusu: dev homurtusu             agu_kurbagasi: gırtlak şişmesi (vrak)
  ag_ana: kitin tıkırtısı                     yilan_kami: tıslama + çan
  kar_cadisi: buz çatırtısı + nefes          abasi: zincir şakırtısı + hırıltı
  ejder_yavrusu: soluk alma + buz kristali
Hamleler (v39_<ad>): kazma, firlat, kaz, cik, cagir, kafatasi, cigilik, kanat, hucum, savur, cirit, cakma, orak, bulut,
  dil, tukur, ag, sifa, ruh, kar, buz, zincir, soluk, kuyruk.
Ölüm sesi v36 / v37 patlamasıdır (Gore malzemesine göre; Enemy.NOT_FLESH).

Kullanım: python tools/audiogen/v39.py   (assets/audio/sfx/*.wav yazar, sfx.json'u günceller)"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, t_axis, exp_env, noise, fft_filter, sine, sweep, reverb, fade, master, write_wav
from layer import load, pitch, trim, tight, build, sub, ring, shimmer

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'audio', 'sfx')
NPC = 'rpgpack/RPG Sound Pack/NPC/'
BAT = 'rpgpack/RPG Sound Pack/battle/'
INV = 'rpgpack/RPG Sound Pack/inventory/'


def S(rel, f=1.0, start=0.0, dur=None):
    return trim(pitch(tight(load(rel)), f), start, dur)


def sw(k, f=1.0):
    return S('swishes/swishes/swish-%d.wav' % k, f)


def ki(n, f=1.0):
    return S('impact/Audio/%s.ogg' % n, f)


def kr(n, f=1.0):
    return S('rpg/Audio/%s.ogg' % n, f)


def rise(f0, f1, dur, g=0.25, wave='saw'):
    x = sweep(f0, f1, dur, wave=wave) if wave != 'sine' else sweep(f0, f1, dur)
    return fft_filter(x, hi=3000) * np.linspace(0.2, 1.0, len(x)) * g


def hiss(dur, lo=2500, hi=9000, k=4.0, g=0.4, seed=1):
    return fft_filter(noise(dur, seed=seed), lo=lo, hi=hi) * exp_env(dur, k) * g


def rumble(dur, f=55, g=0.5):
    return fft_filter(noise(dur, seed=5), hi=220) * exp_env(dur, 3) * g + sub(f, dur, 5, g * 0.6)


def wet(x, mix=0.18):
    return reverb(x, 0.6, mix, lp=3500)


def hazirlik(kind, v):
    f = 1.0 + 0.06 * v
    if kind == 'yer_cucesi':
        return build([(kr('metalClick' if v == 0 else 'metalLatch', 0.7), 0.0, 0.7), (S(NPC + 'ogre/ogre%d.wav' % (2 + v), 1.5, 0, 0.45), 0.04, 0.6),
                      (rise(120, 380, 0.4, 0.18), 0.0, 1.0)])
    if kind == 'kor_solucani':
        return build([(S(NPC + 'slime/slime%d.wav' % (3 + v), 0.6), 0.0, 0.8), (rumble(0.6), 0.0, 0.7), (ki('impactMining_00%d' % (v + 1), 0.7), 0.1, 0.4)])
    if kind == 'sulmus':
        return build([(S(INV + 'beads.wav', 1.2 * f), 0.0, 0.7), (S(NPC + 'shade/shade%d.wav' % (4 + v), 1.4), 0.05, 0.7), (shimmer(0.4, 0.1), 0.1, 1.0)])
    if kind == 'sulmus_yavrusu':
        return build([(S(NPC + 'shade/shade%d.wav' % (8 + v), 2.2, 0, 0.3), 0.0, 0.8), (rise(900, 2400, 0.2, 0.12, 'sine'), 0.0, 1.0)])
    if kind == 'burkut':
        t = t_axis(0.5)
        scr = np.sin(2 * np.pi * (2100 + 500 * np.sin(2 * np.pi * 9 * t)) * t) * exp_env(0.5, 4) * 0.5
        scr = fft_filter(scr + noise(0.5, seed=3) * 0.15 * exp_env(0.5, 6), lo=900, hi=6000)
        return build([(scr, 0.0, 1.0), (sw(3 + v, 0.8), 0.15, 0.5)])
    if kind == 'tunga_hayaleti':
        return wet(build([(S(NPC + 'shade/shade%d.wav' % (1 + v), 0.8), 0.0, 0.8), (ring([660, 990, 1485], 0.8, 0.09, 6), 0.05, 1.0), (rise(200, 600, 0.5, 0.12), 0.0, 1.0)]), 0.3)
    if kind == 'yasavul':
        return build([(S(INV + 'chainmail%d.wav' % (1 + v)), 0.0, 0.8), (hiss(0.5, 300, 3000, 3, 0.4), 0.05, 1.0), (S(NPC + 'giant/giant%d.wav' % (1 + v), 1.2, 0, 0.5), 0.1, 0.5)])
    if kind == 'aldaras':
        return build([(S(BAT + 'sword-unsheathe%s.wav' % ('' if v == 0 else '2'), 1.1), 0.0, 0.8), (S(BAT + 'sword-unsheathe3.wav', 1.25), 0.12, 0.6), (S(NPC + 'shade/shade%d.wav' % (12 + v), 1.1), 0.0, 0.4)])
    if kind == 'tepegoz_yavrusu':
        return build([(S(NPC + 'giant/giant%d.wav' % (3 + v), 0.95), 0.0, 1.0), (rumble(0.5, 48, 0.4), 0.0, 1.0)])
    if kind == 'agu_kurbagasi':
        t = t_axis(0.55)
        croak = np.sign(np.sin(2 * np.pi * (85 + 30 * t) * t)) * (0.5 + 0.5 * np.sin(2 * np.pi * 22 * t)) * exp_env(0.55, 3)
        return build([(fft_filter(croak, hi=1400) * 0.6, 0.0, 1.0), (S(NPC + 'slime/slime%d.wav' % (1 + v), 0.8), 0.1, 0.6)])
    if kind == 'ag_ana':
        clicks = build([(kr('metalClick', 2.2 + 0.2 * k), 0.06 * k, 0.5) for k in range(6)])
        return build([(clicks, 0.0, 1.0), (S(NPC + 'beetle/bite-small%s.wav' % ('' if v == 0 else '2'), 0.7), 0.3, 0.6), (hiss(0.4, 3000, 8000, 6, 0.2), 0.0, 1.0)])
    if kind == 'yilan_kami':
        return wet(build([(hiss(0.7, 3500, 10000, 2.5, 0.6, seed=7 + v), 0.0, 1.0), (ring([880, 1320, 1760], 0.9, 0.1, 5), 0.1, 1.0)]), 0.3)
    if kind == 'kar_cadisi':
        return wet(build([(ki('impactGlass_light_00%d' % (1 + v), 1.3), 0.0, 0.6), (hiss(0.6, 800, 5000, 3, 0.4), 0.0, 1.0), (S(NPC + 'shade/shade%d.wav' % (6 + v), 1.2), 0.1, 0.6)]), 0.25)
    if kind == 'abasi':
        return build([(S(INV + 'chainmail%d.wav' % (1 + v), 0.75), 0.0, 0.9), (S(NPC + 'gutteral beast/mnstr%d.wav' % (3 + v), 0.85), 0.05, 0.8)])
    if kind == 'ejder_yavrusu':
        breath = fft_filter(noise(0.6, seed=9), lo=200, hi=2500) * np.linspace(0.1, 1.0, int(0.6 * SR)) * 0.5
        return build([(breath, 0.0, 1.0), (S(NPC + 'gutteral beast/mnstr%d.wav' % (8 + v), 1.3, 0, 0.5), 0.05, 0.5), (shimmer(0.4, 0.12), 0.25, 1.0)])
    raise KeyError(kind)


def hamle(n):
    if n == 'kazma':
        return build([(sw(2, 0.85), 0.0, 0.8), (ki('impactMining_002'), 0.12, 0.8)])
    if n == 'firlat':
        return build([(sw(6, 0.8), 0.0, 1.0), (rumble(0.2, 70, 0.3), 0.0, 1.0)])
    if n == 'kaz':
        return build([(ki('impactMining_003', 0.8), 0.0, 0.7), (fft_filter(noise(0.5, seed=2), hi=900) * exp_env(0.5, 4) * 0.6, 0.02, 1.0)])
    if n == 'cik':
        return build([(rumble(0.7, 45, 0.7), 0.0, 1.0), (ki('impactMining_001', 0.7), 0.0, 0.9), (ki('impactPunch_heavy_001'), 0.02, 0.6)])
    if n == 'cagir':
        return wet(build([(S(BAT + 'magic1.wav', 0.9), 0.0, 0.8), (S(NPC + 'shade/shade3.wav', 1.6), 0.05, 0.6), (shimmer(0.6, 0.15), 0.0, 1.0)]), 0.35)
    if n == 'kafatasi':
        return build([(sw(9, 1.1), 0.0, 0.8), (S(NPC + 'shade/shade14.wav', 1.3, 0, 0.4), 0.0, 0.6)])
    if n == 'cigilik':
        return build([(hazirlik('burkut', 1) * 1.0, 0.0, 0.8), (sw(11, 0.7), 0.05, 1.0)])
    if n == 'kanat':
        return build([(sw(4, 0.55), 0.0, 1.0), (sw(5, 0.6), 0.1, 0.8), (fft_filter(noise(0.3, seed=4), hi=700) * exp_env(0.3, 6) * 0.6, 0.0, 1.0)])
    if n == 'hucum':
        return build([(sw(12, 0.7), 0.0, 1.0), (hiss(0.4, 600, 4000, 5, 0.3), 0.0, 1.0), (S(INV + 'armor-light.wav', 0.8), 0.0, 0.5)])
    if n == 'savur':
        return build([(sw(7, 0.65), 0.0, 1.0), (rumble(0.2, 80, 0.2), 0.0, 1.0)])
    if n == 'cirit':
        return build([(sw(1, 1.1), 0.0, 1.0), (ring([1200, 1800], 0.4, 0.06, 9), 0.0, 1.0)])
    if n == 'cakma':
        return build([(ki('impactPunch_heavy_002', 0.6), 0.0, 1.0), (rumble(0.9, 40, 0.8), 0.0, 1.0), (ki('impactMining_004', 0.6), 0.03, 0.6)])
    if n == 'orak':
        return build([(sw(8, 1.25), 0.0, 1.0), (sw(8, 1.4), 0.12, 0.7), (S(BAT + 'sword-unsheathe4.wav', 1.3), 0.0, 0.4)])
    if n == 'bulut':
        return build([(fft_filter(noise(0.9, seed=6), lo=150, hi=2200) * exp_env(0.9, 2.5) * 0.7, 0.0, 1.0), (S(NPC + 'slime/slime7.wav', 0.7), 0.0, 0.6)])
    if n == 'dil':
        return build([(sw(10, 1.5), 0.0, 0.8), (S(NPC + 'slime/slime5.wav', 1.3), 0.08, 0.8)])
    if n == 'tukur':
        return build([(S(NPC + 'slime/slime2.wav', 1.1), 0.0, 1.0), (sw(3, 1.2), 0.0, 0.4)])
    if n == 'ag':
        return build([(hiss(0.35, 2000, 7000, 7, 0.6), 0.0, 1.0), (S(NPC + 'slime/slime9.wav', 1.6), 0.0, 0.4)])
    if n == 'sifa':
        t = t_axis(0.9)
        ch = sum(np.sin(2 * np.pi * f * t) for f in (523, 659, 784, 1046)) * exp_env(0.9, 3) * np.minimum(1, t * 12) * 0.15
        return wet(build([(ch, 0.0, 1.0), (S(BAT + 'spell.wav', 1.1), 0.0, 0.6)]), 0.35)
    if n == 'ruh':
        return wet(build([(S(BAT + 'spell.wav', 1.3), 0.0, 0.8), (hiss(0.4, 3000, 9000, 5, 0.25), 0.0, 1.0)]), 0.3)
    if n == 'kar':
        return wet(build([(hiss(0.6, 1000, 7000, 3.5, 0.6, seed=11), 0.0, 1.0), (shimmer(0.5, 0.15), 0.05, 1.0)]), 0.3)
    if n == 'buz':
        return build([(ki('impactGlass_medium_001', 1.2), 0.0, 0.8), (sw(5, 1.3), 0.0, 0.7), (ring([2400, 3600], 0.3, 0.06, 12), 0.0, 1.0)])
    if n == 'zincir':
        return build([(S(INV + 'chainmail1.wav', 0.9), 0.0, 1.0), (S(INV + 'chainmail2.wav', 1.1), 0.08, 0.8), (sw(13, 0.7), 0.0, 0.8)])
    if n == 'soluk':
        x = fft_filter(noise(1.0, seed=13), lo=500, hi=8000) * np.minimum(1, t_axis(1.0) * 10) * exp_env(1.0, 1.6) * 0.7
        return wet(build([(x, 0.0, 1.0), (shimmer(0.9, 0.12), 0.0, 1.0), (ki('impactGlass_light_003', 0.9), 0.05, 0.4)]), 0.25)
    if n == 'kuyruk':
        return build([(sw(13, 0.6), 0.0, 1.0), (ki('impactGlass_light_002', 1.4), 0.15, 0.4)])
    raise KeyError(n)


KINDS = ['yer_cucesi', 'kor_solucani', 'sulmus', 'sulmus_yavrusu', 'burkut', 'tunga_hayaleti', 'yasavul', 'aldaras',
         'tepegoz_yavrusu', 'agu_kurbagasi', 'ag_ana', 'yilan_kami', 'kar_cadisi', 'abasi', 'ejder_yavrusu']
MOVES = ['kazma', 'firlat', 'kaz', 'cik', 'cagir', 'kafatasi', 'cigilik', 'kanat', 'hucum', 'savur', 'cirit', 'cakma', 'orak',
         'bulut', 'dil', 'tukur', 'ag', 'sifa', 'ruh', 'kar', 'buz', 'zincir', 'soluk', 'kuyruk']


def main():
    out = {}
    for k in KINDS:
        for v in range(2):
            out['hazirlik_%s_%d' % (k, v + 1)] = (hazirlik(k, v), -15.0)
    for n in MOVES:
        out['v39_' + n] = (hamle(n), -13.0)
    mp = os.path.join(A, 'sfx.json')
    meta = json.load(open(mp, encoding='utf-8'))
    for name, (x, db) in sorted(out.items()):
        y = master(fade(np.asarray(x, float), 0.002, 0.03), db)
        write_wav(os.path.join(A, name + '.wav'), y, SR, None)
        meta[name] = {'loop': False, 'len': round(len(y) / SR, 3), 'hedef_db': db}
    json.dump(meta, open(mp, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('yazıldı:', len(out))


if __name__ == '__main__':
    main()
