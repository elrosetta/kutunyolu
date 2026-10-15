"""Bütün üretilmiş görselleri Godot projesine yazar (albedo + normal map + JSON meta).

Kullanım:  python export_assets.py            (proje kökü: bu dosyanın iki üstü)
           python export_assets.py --tiles [biyom ...]   yalnızca zemin karoları + toprak dokuları
           python export_assets.py --bg [biyom ...]      yalnızca paralaks arka planları
           python export_assets.py --creatures [kimlik ...]   yalnızca yaratık sprite'ları (varsayılan: hepsi)
           python export_assets.py --kurt                yalnızca kurt sprite'ları (Bengü, kol, tazı, Han, Bozkurt)
Sanatçı çizimleri geldiğinde aynı dosya adlarıyla değiştirmek yeterli: oyun JSON meta'yı okur.
"""
import json
import math
import os
import sys
import numpy as np
from PIL import Image

from raster import to_img
import bengu
import creatures
import env_forest
import yurt
import bg_forest
import biomes
import soil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = os.path.join(ROOT, 'assets')

FPS = {'crouch': 6, 'crouch_atk': 8, 'sprint': 18, 'walk': 10, 'guard': 6, 'bash': 12, 'charge': 16, 'stagger': 8, 'shell': 8, 'spin': 16, 'bite': 10, 'howl': 8, 'slam': 10, 'rage': 10, 'strike': 12, 'idle': 8, 'run': 14, 'jump': 8, 'fall': 8, 'roll': 18, 'land': 14, 'slash1': 16, 'slash2': 16, 'thrust': 14, 'heavy': 11, 'bow': 10,
       'atk_down': 16, 'atk_up': 16, 'atk_horiz': 16, 'atk_thrust': 16, 'atk_heavy': 12, 'atk_spin': 16, 'atk_lunge': 16, 'grab': 10,
       'throw': 14, 'block': 1, 'cast': 10, 'hurt': 10, 'drink': 6, 'walk': 8, 'windup': 8, 'leap': 10, 'attack': 10, 'slam': 10,
       'hop': 10, 'strike': 10, 'dormant': 1}


def save(arr, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    to_img(arr).save(path)


def ang_of(a):
    return math.atan2(math.cos(a), math.sin(a))


def export_sheet(name, anims, render, cell, origin):
    names = list(anims.keys())
    cols = max(anims[a][0] for a in names)
    W, H = cols * cell[0], len(names) * cell[1]
    alb = np.zeros((H, W, 4)); nrm = np.zeros((H, W, 4)); glo = np.zeros((H, W, 4))
    meta = {'cell': list(cell), 'origin': list(origin), 'anims': {}}
    for r, an in enumerate(names):
        n = anims[an][0]
        loop = anims[an][2] if len(anims[an]) > 2 else an in ('idle', 'run', 'walk')
        frames = []
        for i in range(n):
            res = render(an, i)
            c, rgba, nm, info = res
            alb[r * cell[1]:(r + 1) * cell[1], i * cell[0]:(i + 1) * cell[0]] = rgba
            nrm[r * cell[1]:(r + 1) * cell[1], i * cell[0]:(i + 1) * cell[0]] = nm
            em = c.emis
            ga = (em.max(axis=2) > 0).astype(float)
            glo[r * cell[1]:(r + 1) * cell[1], i * cell[0]:(i + 1) * cell[0], :3] = np.clip(em * 1.0, 0, 1)
            glo[r * cell[1]:(r + 1) * cell[1], i * cell[0]:(i + 1) * cell[0], 3] = ga
            fr = {}
            for k in ('hand_f', 'hand_b', 'mouth', 'hand', 'head', 'sh_f', 'sh_b'):
                if info and k in info:
                    fr[k] = [round(info[k][0], 2), round(info[k][1], 2)]
            if info and 'arm' in info:
                fr['arm'] = [round(info['arm'][0], 4), round(info['arm'][1], 4)]
            if info and 'arm_b' in info:
                fr['arm_b'] = [round(info['arm_b'][0], 4), round(info['arm_b'][1], 4)]
            for k in ('ang_f', 'ang_b'):
                if info and k in info:
                    fr[k] = round(ang_of(info[k]), 4)
            frames.append(fr)
        meta['anims'][an] = {'row': r, 'frames': n, 'fps': FPS.get(an, 10), 'loop': bool(loop), 'data': frames,
                             'arm': bool(anims[an][3]) if len(anims[an]) > 3 else True}
    save(alb, os.path.join(A, 'sprites', name + '.png'))
    save(nrm, os.path.join(A, 'sprites', name + '_n.png'))
    if glo[..., 3].max() > 0:
        save(glo, os.path.join(A, 'sprites', name + '_e.png'))
        meta['glow'] = True
    json.dump(meta, open(os.path.join(A, 'sprites', name + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('sprite', name, W, H)


def export_tiles(only=()):
    """Zemin atlası + dikişsiz toprak dokusu (1.5x yoğunluk; bkz. soil.py)."""
    for bid, bcfg in biomes.BIOMES.items():
        if only and bid not in only:
            continue
        soil.set_biome(bcfg['soil'])
        Al, Nm, tmeta = soil.build_ground_atlas()
        save(Al, os.path.join(A, 'tiles', bid + '.png')); save(Nm, os.path.join(A, 'tiles', bid + '_n.png'))
        st, sn, se = soil.soil_texture()
        save(np.dstack([st, np.ones(st.shape[:2])]), os.path.join(A, 'tiles', bid + '_soil.png'))
        save(sn, os.path.join(A, 'tiles', bid + '_soil_n.png'))
        ep = os.path.join(A, 'tiles', bid + '_soil_e.png')
        if se is not None:
            save(np.dstack([se, np.ones(st.shape[:2])]), ep)
        elif os.path.exists(ep):
            os.remove(ep)
        json.dump(tmeta, open(os.path.join(A, 'tiles', bid + '.json'), 'w', encoding='utf-8'), indent=1)
        print('tiles', bid, Al.shape)
    soil.set_biome(biomes.BIOMES['otuken']['soil'])


def export_bg(only=()):
    """Paralaks katmanları (1.5x yoğunluk: gök 960x540, diğerleri 1920x540; bkz. bg_hd.py)."""
    import bg_hd
    for bid, layers in bg_hd.BIOME_LAYERS.items():
        if only and bid not in only:
            continue
        for nm_, fn in layers:
            fn().save(os.path.join(A, 'bg', '%s_%s.png' % (bid, nm_)))
        print('bg', bid)
    if not only or 'yurt' in only:
        import bg_yurt
        for nm_, fn in bg_yurt.LAYERS.items():
            fn().save(os.path.join(A, 'bg', nm_ + '.png'))
        print('bg yurt')


def main():
    only_ = [a for a in sys.argv[1:] if not a.startswith('-')]
    if '--tiles' in sys.argv or '--bg' in sys.argv:
        if '--tiles' in sys.argv:
            export_tiles(only_)
        if '--bg' in sys.argv:
            export_bg(only_)
        return
    if '--weapons' in sys.argv:
        _weapons_only()
        return
    if '--kurt' in sys.argv:
        _kurt_only()
        return
    if '--creatures' in sys.argv:
        _creatures_only([a for a in sys.argv[1:] if not a.startswith('-')])
        return
    # kahraman + kol iskeleti
    _export_player()
    # yaratıklar
    for nm_ in creatures.CREATURES:
        _export_creature(nm_)
    # yurt NPC'leri
    for nm_ in yurt.NPC_STYLES:
        an2 = {k: (v[0], v[1], True) for k, v in yurt.NPC_ANIMS.items()}
        export_sheet('npc_' + nm_, an2, lambda an, i, nm_=nm_: yurt.render_npc(nm_, an, i), yurt.NPC_CELL, yurt.NPC_FEET)
    if '--sprites' in sys.argv:
        return
    # karolar: her biyom için ayrı palet
    only = [a for a in sys.argv[1:] if not a.startswith('-')]
    export_tiles(only)
    # süsler
    dmeta = {}
    for k, fn in list(env_forest.DECOR.items()) + list(yurt.DECOR.items()):
        c = fn()
        rgba = c.shade(rim_amt=0.25)
        save(rgba, os.path.join(A, 'decor', k + '.png'))
        save(c.normal_map(rgba[..., 3]), os.path.join(A, 'decor', k + '_n.png'))
        has_glow = bool(c.emis.max() > 0)
        if has_glow:
            g = np.zeros((c.h, c.w, 4)); g[..., :3] = np.clip(c.emis, 0, 1); g[..., 3] = (c.emis.max(axis=2) > 0)
            save(g, os.path.join(A, 'decor', k + '_e.png'))
        dmeta[k] = {'size': [c.w, c.h], 'origin': [c.ox, c.oy], 'glow': has_glow}
    # v13 yurt süsleri (1.5x yoğunluk, "k": 1.5)
    import yurt_hd
    yurt_hd.export(dmeta)
    json.dump(dmeta, open(os.path.join(A, 'decor', 'decor.json'), 'w', encoding='utf-8'), indent=1)
    print('decor', len(dmeta))
    # paralaks
    export_bg(only)
    bg_forest.god_ray().save(os.path.join(A, 'fx', 'god_ray.png'))
    bg_forest.soft_dot().save(os.path.join(A, 'fx', 'soft_dot.png'))
    bg_forest.leaf_particles().save(os.path.join(A, 'fx', 'leaves.png'))
    print('bg ok')
    # silahlar
    import weapons_myth
    alb, nrm, glo, wmeta = weapons_myth.build_atlas()
    save(alb, os.path.join(A, 'weapons', 'weapons.png')); save(nrm, os.path.join(A, 'weapons', 'weapons_n.png')); save(glo, os.path.join(A, 'weapons', 'weapons_e.png'))
    json.dump(wmeta, open(os.path.join(A, 'weapons', 'weapons.json'), 'w', encoding='utf-8'), indent=1)
    print('weapons', alb.shape)


def _export_creature(nm_):
    draw, anims, cell, feet = creatures.CREATURES[nm_]
    an2 = {k: (v[0], v[1], k in ('idle', 'run', 'walk')) for k, v in anims.items()}
    export_sheet(nm_, an2, lambda an, i, nm_=nm_: creatures.render_creature(nm_, an, i), cell, feet)


def _export_player():
    export_sheet('bengu', bengu.ANIMS, lambda an, i: bengu.render_frame(an, i), (96, 80), (44, 74))
    # oyunda sürülen ön kol parçaları: üst kol, ön kol, yumruk (her biri aşağıyı gösterir, pivot üstte)
    parts = bengu.render_arm_parts()
    cw, ch = bengu.ARM_CELL
    alb = np.zeros((ch, cw * len(parts), 4))
    for i, pc in enumerate(parts):
        alb[:, i * cw:(i + 1) * cw] = pc.shade()
    save(alb, os.path.join(A, 'sprites', 'bengu_kol.png'))
    json.dump({'cell': [cw, ch], 'pivot': list(bengu.ARM_PIVOT), 'fist_pivot': [bengu.ARM_PIVOT[0], bengu.ARM_PIVOT[1] + 2],
               'upper_len': bengu.UPPER_LEN, 'fore_len': bengu.FORE_LEN, 'parts': ['upper', 'fore', 'fist', 'upper_b', 'fore_b', 'fist_b']},
              open(os.path.join(A, 'sprites', 'bengu_kol.json'), 'w', encoding='utf-8'), indent=1)


def _kurt_only():
    """v13: yalnızca kurt sprite'ları (Bengü + kol iskeleti, Erlik Tazısı, Kara Börü Han, Bozkurt)."""
    _export_player()
    for nm_ in sorted(creatures.VOLUME):
        _export_creature(nm_)


def _creatures_only(names):
    for nm_ in (names or list(creatures.CREATURES.keys())):
        _export_creature(nm_)


def _weapons_only():
    import weapons_myth
    alb, nrm, glo, wmeta = weapons_myth.build_atlas()
    save(alb, os.path.join(A, 'weapons', 'weapons.png')); save(nrm, os.path.join(A, 'weapons', 'weapons_n.png')); save(glo, os.path.join(A, 'weapons', 'weapons_e.png'))
    json.dump(wmeta, open(os.path.join(A, 'weapons', 'weapons.json'), 'w', encoding='utf-8'), indent=1)
    print('weapons', alb.shape)


if __name__ == '__main__':
    main()
