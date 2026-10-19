"""v28 gövde animasyonu önizlemesi (yalnızca geliştirme): kareler yan yana, ön kol savuruşun o anki pozunda, basit bıçak.

Kullanım: python govde_onizleme.py <çıktı.png> <anim>[:<savuruş>[:<erim>]] ... [--eski] [--olcek=0.5]
  --eski   v27 gövdesi (bengu_ink.ANIMS_V27, eşit aralıklı kareler) — önce / sonra karşılaştırması
Savuruş anahtarları scripts/actors/Player.gd SWINGS'ten okunur (kol açıları oyundaki gibi; 3B düzlem izdüşümü yok).
"""
import json
import math
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw

import bengu_ink as b
import inkkit as ik
from rig import fk_arm

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def swings():
    out = {}
    for f in ('scripts/actors/Player.gd', 'scripts/core/Silah27.gd'):
        src = open(os.path.join(ROOT, f), encoding='utf-8').read()
        m = re.search(r'const SWINGS := \{(.*?)\n\}', src, re.S)
        body = m.group(1)
        for mm in re.finditer(r'"(\w+)": (\{"body".*?\]\]\})', body, re.S):
            txt = re.sub(r'#.*', '', mm.group(2)).replace('true', 'true')
            try:
                out[mm.group(1)] = json.loads(txt)
            except Exception:
                pass
    return out


SW = swings()


def ck(sw):
    if 'ck' in sw:
        return sw['ck']
    h0 = sw['hit'][0]
    if sw.get('around') or 'multi' in sw:
        return h0
    for k in sw['keys']:
        if k[0] > h0 + 0.001:
            return min(k[0], sw['hit'][1] - 0.01)
    return h0


def tau_to_k(sw, tau, mk):
    a = [0.0, sw['hit'][0], ck(sw), sw['hit'][1], 1.0]
    m = [0.0, mk[0], mk[1], mk[2], 1.0]
    for i in range(4):
        if tau <= m[i + 1]:
            u = 0.0 if m[i + 1] == m[i] else (tau - m[i]) / (m[i + 1] - m[i])
            return a[i] + (a[i + 1] - a[i]) * u
    return 1.0


def ease(u, e):
    if e == 1:
        return u * u * u
    if e == 2:
        return 1 - (1 - u) ** 3
    return u * u * (3 - 2 * u)


def swing_pose(sw, k):
    ks = sw['keys']
    for k0, k1 in zip(ks, ks[1:]):
        if k <= k1[0]:
            u = ease(max(0.0, min(1.0, (k - k0[0]) / max(1e-4, k1[0] - k0[0]))), int(k1[6]))
            return [k0[j] + (k1[j] - k0[j]) * u for j in range(1, 6)]
    return ks[-1][1:6]


def frame(anim, i, sw=None, R=28.0, old=False):
    tab = b.ANIMS_V27 if old else b.ANIMS
    n, fn, loop, arm = tab[anim]
    if not old and anim in b.RT:
        t = b.RT[anim][i]
        mk = b._gv.V28[anim].marks
    else:
        t = min(0.999, i / n + 0.5 / n)
        mk = None
    p = dict(fn(t))
    cv = ik.InkCanvas(b.CELL[0], b.CELL[1], b.FEET[0], b.FEET[1], k=b.TEX, ss=2)
    pose = None
    if sw is not None:
        k = tau_to_k(sw, t, mk) if mk else t
        pose = swing_pose(sw, k)
        p['af'] = (pose[0], pose[1])
        p['ext'] = pose[4]
    info = b.draw_turn(cv, p, sw is not None, True)
    if pose is not None:
        h = info['hand_f']
        a = pose[0] + pose[1] + pose[2]
        tip = (h[0] + math.sin(a) * R, h[1] + math.cos(a) * R)
        cv.stroke([h, tip], 2.2, z=30, col=(0.75, 0.8, 0.9), taper=(0.0, 0.6))
    rgba, nm, em = cv.finish(**b.SHADE)
    return rgba, t, info


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    old = '--eski' in sys.argv
    sc = 0.5
    cols = 99
    for a in sys.argv:
        if a.startswith('--olcek='):
            sc = float(a.split('=')[1])
        if a.startswith('--sutun='):
            cols = int(a.split('=')[1])
    out, specs = args[0], args[1:]
    rows = []
    for spec in specs:
        parts = spec.split(':')
        an = parts[0]
        sw = SW.get(parts[1]) if len(parts) > 1 and parts[1] else None
        R = float(parts[2]) if len(parts) > 2 else 28.0
        n = (b.ANIMS_V27 if old else b.ANIMS)[an][0]
        tiles = []
        for i in range(n):
            rgba, t, info = frame(an, i, sw, R, old)
            a = np.clip(rgba * 255 + 0.5, 0, 255).astype(np.uint8)
            im = Image.fromarray(a, 'RGBA').crop((24, 30, 384, 320))
            bg = Image.new('RGBA', im.size, (236, 232, 222, 255))
            d = ImageDraw.Draw(bg)
            gy = b.FEET[1] - 30 + int(round(-b.FOOT_Y * 0)) - 0
            d.line([(0, gy + 8), (im.size[0], gy + 8)], fill=(150, 140, 130, 255), width=2)
            d.line([(b.FEET[0] - 24, 0), (b.FEET[0] - 24, im.size[1])], fill=(215, 205, 195, 255), width=1)
            bg.alpha_composite(im)
            d = ImageDraw.Draw(bg)
            d.text((6, 4), '%s %d  t%.2f' % (an if i == 0 else '', i, t), fill=(40, 30, 30, 255))
            tiles.append(bg)
        for j in range(0, len(tiles), cols):
            part = tiles[j:j + cols]
            w = sum(t.size[0] for t in part)
            row = Image.new('RGBA', (w, part[0].size[1]))
            x = 0
            for t in part:
                row.paste(t, (x, 0))
                x += t.size[0]
            rows.append(row)
    W = max(r.size[0] for r in rows)
    H = sum(r.size[1] for r in rows)
    sheet = Image.new('RGBA', (W, H), (255, 255, 255, 255))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.size[1]
    sheet = sheet.resize((int(W * sc), int(H * sc)), Image.LANCZOS)
    sheet.convert('RGB').save(out)
    print(out, sheet.size)


if __name__ == '__main__':
    main()
