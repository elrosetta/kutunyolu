"""v32 Bengisu Usta (konak) sesleri (Main._usta_uygula). Sentez + mevcut yapı taşları (pro.py, impact.py, v25.py):
  usta_nakis   Nakış: kalemin çeliğe iki kısa "tink"i (ince çelik kipleri) + ardından Kut çınlaması (iki notalı çan, tiz)
  usta_damga   Mürekkep damgası: tok kâğıt şaplağı (alçak gürültü vuruşu) + kısa ıslak "şlap" + ince çelik damga çıtırtısı
  usta_dovme   Yeniden dövme: küçük örste iki çekiç vuruşu (çan oranlı demir kipleri, kısa) + kor cızırtısı
Hedef yükseklik: usta_nakis -13, usta_damga -12, usta_dovme -11 dB (export_audio.TARGETS).
Yeniden üretim: python tools/audiogen/v32_usta.py [ad...]  (ya da export_audio.py --sfx usta_nakis usta_damga usta_dovme)"""
import os
import sys
import json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import SR, t_axis, exp_env, noise, sine, fade, hp, lp, bp, write_wav, master
from pro import click, thump, metal_ring, room, note
from impact import crunch
from v25 import chime, steel

TARGET = {"usta_nakis": -13.0, "usta_damga": -12.0, "usta_dovme": -11.0}


def _mix(parts, dur):
    out = np.zeros(int(dur * SR))
    for x, at, g in parts:
        s = int(at * SR)
        n = min(len(x), len(out) - s)
        if n > 0:
            out[s:s + n] += x[:n] * g
    return out


def nakis():
    dur = 0.95
    parts = []
    for i, at in enumerate((0.0, 0.11)):
        parts.append((click(0.005, 3000, 12000, 410 + i), at, 0.7))
        parts.append((steel(5200.0 + i * 300.0, 0.08, 70.0, seed=412 + i), at, 0.5))
        parts.append((metal_ring(3900 + i * 240, 0.16, 26, parts=(1.0, 1.41, 2.2), seed=414 + i), at, 0.35))
    # Kut çınlaması: iki notalı tiz çan (Hüseyni'den E6 / B6), hafif dövünme
    parts.append((chime(note('E6'), 0.6, 6.5, 5.0), 0.2, 0.55))
    parts.append((chime(note('B6'), 0.55, 7.5, 6.0), 0.27, 0.4))
    # kut toz: tiz hava
    t = t_axis(0.5)
    shimmer = bp(noise(0.5, seed=416), 6000, 12000) * exp_env(0.5, 6.0) * (0.5 + 0.5 * np.sin(2 * np.pi * 9.0 * t)) * 0.18
    parts.append((shimmer, 0.22, 1.0))
    return room(_mix(parts, dur), 0.35, 0.16)


def damga():
    dur = 0.55
    # kâğıda tok şaplak: alçak gürültü vuruşu + kısa alt gövde
    slap = lp(noise(0.07, seed=420), 1400) * exp_env(0.07, 40.0)
    body = thump(170, 70, 0.14, 16, 1.2)
    # ıslak mürekkep "şlap": bant gürültüsü, hızlı sönen
    wet = bp(noise(0.05, seed=421), 500, 2600) * exp_env(0.05, 55.0)
    # damganın çelik kenarı: ince çıtırtı
    edge = crunch(0.04, 422, 1200, 7000, 3.0, 300.0)
    tink = steel(6400.0, 0.05, 90.0, seed=423)
    return room(_mix([(click(0.004, 1500, 9000, 424), 0.0, 0.6), (slap, 0.0, 1.0), (body, 0.0, 0.8), (wet, 0.004, 0.7),
                      (edge, 0.0, 0.35), (tink, 0.012, 0.22)], dur), 0.3, 0.12)


def dovme():
    dur = 0.9
    parts = []
    for i, (at, f) in enumerate(((0.0, 1480.0), (0.17, 1560.0))):
        parts.append((click(0.007, 2000, 11000, 430 + i), at, 0.9))
        parts.append((crunch(0.025, 432 + i, 700, 5000, 4.0, 220.0), at, 0.4))
        parts.append((metal_ring(f, 0.5, 7.0, parts=(1.0, 2.76, 5.40, 8.93, 1.51), seed=434 + i), at, 0.8 if i else 0.65))
        parts.append((metal_ring(f * 1.9, 0.3, 12.0, seed=436 + i), at, 0.3))
    # kor cızırtısı (ikinci vuruştan sonra kısa)
    t = t_axis(0.35)
    siz = bp(noise(0.35, seed=438), 2500, 9000) * exp_env(0.35, 9.0) * (0.6 + 0.4 * np.sin(2 * np.pi * 37.0 * t)) * 0.22
    parts.append((siz, 0.2, 1.0))
    return room(_mix(parts, dur), 0.45, 0.2)


def build_all():
    return {"usta_nakis": nakis(), "usta_damga": damga(), "usta_dovme": dovme()}


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
