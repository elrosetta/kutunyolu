"""Biyom tanımları: her biyomun toprak paleti, arka plan üreticisi ve oyun tarafı görsel ayarları.

Derinlik → biyom: 1-2 Kararan Ötüken (gece), 3-4 Bozkır Kurganları (gündüz), 5-6 Şahmeran Mağarası (mağara),
7-8 Kaf Dağı (karlı şafak), 9+ Erlik'in Ülkesi (lav gecesi). Godot tarafı data/world.json'daki "art" alanını okur.
"""
import numpy as np
from pixkit import pal, hexrgb
from raster import Mat, ramp

BIOMES = {
    'otuken': {
        'soil': dict(SOIL=pal('#100d0d', '#1a1515', '#251e1c', '#312924', '#3d342c', '#4a4035'),
                     CLAY=pal('#181014', '#26171a', '#341e20', '#422727', '#50312d', '#5e3b34'),
                     HUMUS=pal('#0c090b', '#130f11', '#1a1517', '#221b1c', '#2a2221', '#332927'),
                     GRASS=pal('#0a1913', '#10251b', '#173223', '#1f422b', '#2a5435', '#386941', '#4d7f4f'),
                     ROOT=pal('#1e1512', '#2e211a', '#413022', '#543f2c'),
                     SPECK=pal('#6f6a5c', '#4f5761', '#8b8474'),
                     WOOD=pal('#15100c', '#221a12', '#312619', '#413321', '#52412b', '#645036'),
                     ROCK=[(222, 0.12, 0.40), (20, 0.18, 0.36), (232, 0.16, 0.30), (275, 0.20, 0.42)],
                     STYLE=dict(cap='grass', bands=[('soil', 3), ('clay', 1.2), ('soil', 2), ('humus', 1.4), ('gravel', 1.0), ('soil', 1.5), ('clay', 0.8)],
                                roots=14, bones=6, cracks=10, extra=None, ceil='roots', glow=None),
                     ROOT_MAT=(25, 0.36, 0.38), OUTLINE='#0f0b0d'),
        'art': {'ambient': [0.40, 0.44, 0.62], 'sun': [0.62, 0.72, 1.0], 'sun_energy': 0.38, 'sun_rot': 40,
                'saturation': 0.96, 'contrast': 1.08, 'particles': 'ruh', 'fog': True, 'rays': [0.62, 0.8, 1.0, 0.07],
                'decor': ['dilek_agaci', 'kam_diregi', 'mantar', 'cicek', 'kaya', 'cira'], 'decor_tint': [0.66, 0.68, 0.78],
                'torch_col': [1.0, 0.58, 0.26], 'deep_color': [0.04, 0.03, 0.06], 'gate_col': [0.45, 0.9, 1.0],
                'styles': ['orman', 'ucurum', 'magara', 'harabe'], 'sky_scale': 1},
    },
    'bozkir': {
        'soil': dict(SOIL=pal('#4a3524', '#6a4b2e', '#8a6238', '#a97a44', '#c3934f', '#d8ab61'),
                     CLAY=pal('#5a3022', '#7e4328', '#a0572f', '#bf6c3a', '#d48348', '#e49a58'),
                     HUMUS=pal('#3a2a1c', '#4f3a26', '#654b30', '#7a5c3a', '#8f6e46', '#a37f52'),
                     GRASS=pal('#5a4a1a', '#7d6620', '#a3862a', '#c5a435', '#dfbf48', '#f0d565', '#fbe68e'),
                     ROOT=pal('#4a3320', '#66472c', '#86613c', '#a67c4e'),
                     SPECK=pal('#e8d7a8', '#b8aa88', '#f4e8c4'),
                     WOOD=pal('#4a3018', '#6a4624', '#8c5e30', '#ad783f', '#c8914f', '#dca962'),
                     ROCK=[(38, 0.25, 0.62), (28, 0.35, 0.55), (45, 0.18, 0.72), (20, 0.3, 0.48)],
                     STYLE=dict(cap='dry', bands=[('sand', 2.2), ('soil', 2), ('clay', 1.6), ('gravel', 1.1), ('sand', 1.4), ('soil', 1.5), ('clay', 1.0)],
                                roots=6, bones=4, cracks=16, extra='chalk', ceil='roots', glow=None),
                     ROOT_MAT=(30, 0.45, 0.6), OUTLINE='#3a2414'),
        'art': {'ambient': [0.98, 0.94, 0.86], 'sun': [1.0, 0.92, 0.75], 'sun_energy': 0.55, 'sun_rot': 55,
                'saturation': 1.08, 'contrast': 1.04, 'particles': 'polen', 'fog': False, 'rays': [1.0, 0.9, 0.6, 0.06],
                'decor': ['kam_diregi', 'kaya', 'cira', 'cicek'], 'decor_tint': [1.0, 0.98, 0.92],
                'torch_col': [1.0, 0.6, 0.3], 'deep_color': [0.22, 0.14, 0.08], 'gate_col': [1.0, 0.85, 0.5],
                'styles': ['orman', 'ucurum', 'harabe'], 'sky_scale': 1},
    },
    'sahmeran': {
        'soil': dict(SOIL=pal('#0e1412', '#172019', '#212c22', '#2b382b', '#364435', '#425141'),
                     CLAY=pal('#1a1424', '#2a1f3a', '#3a2a4e', '#4a3862', '#5a4676', '#6a5588'),
                     HUMUS=pal('#0a0f0d', '#111614', '#18201c', '#1f2923', '#27322b', '#2f3b33'),
                     GRASS=pal('#123a2a', '#1a5a3a', '#227a48', '#2d9a58', '#3fbb6c', '#62d88a', '#9af0b4'),
                     ROOT=pal('#1c2a26', '#2a3c36', '#3a5048', '#4d665c'),
                     SPECK=pal('#8ad8c0', '#c080e0', '#f0c860'),
                     WOOD=pal('#1a2420', '#28352f', '#38483f', '#495b50', '#5a6e61', '#6c8173'),
                     ROCK=[(160, 0.25, 0.42), (280, 0.35, 0.45), (150, 0.2, 0.3), (40, 0.5, 0.55)],
                     STYLE=dict(cap='moss', bands=[('soil', 2.2), ('clay', 1.4), ('humus', 1.2), ('soil', 2), ('gravel', 1.0), ('clay', 1.2)],
                                roots=5, bones=2, cracks=8, extra='crystal', ceil='moss', glow=[0.35, 1.0, 0.8]),
                     ROOT_MAT=(150, 0.3, 0.35), OUTLINE='#06100c'),
        'art': {'ambient': [0.34, 0.42, 0.44], 'sun': [0.5, 0.95, 0.75], 'sun_energy': 0.25, 'sun_rot': 70,
                'saturation': 1.1, 'contrast': 1.1, 'particles': 'spor', 'fog': True, 'rays': [0.5, 1.0, 0.7, 0.05],
                'decor': ['mantar', 'kaya'], 'decor_tint': [0.75, 0.95, 0.9],
                'torch_col': [0.5, 1.0, 0.7], 'deep_color': [0.03, 0.06, 0.05], 'gate_col': [0.7, 1.0, 0.6],
                'styles': ['magara', 'magara', 'harabe'], 'sky_scale': 1},
    },
    'kaf': {
        'soil': dict(SOIL=pal('#2c2f3a', '#3c4050', '#4e5366', '#60667c', '#737a92', '#878ea6'),
                     CLAY=pal('#3a3550', '#4c4668', '#5e587e', '#6f6a92', '#817ca5', '#938eb6'),
                     HUMUS=pal('#222532', '#2e3142', '#3a3e52', '#464a62', '#525772', '#5e6382'),
                     GRASS=pal('#8a9ab8', '#a8b8d2', '#c2d0e6', '#d8e4f4', '#e8f1fb', '#f4f9ff', '#ffffff'),
                     ROOT=pal('#3a3448', '#504a60', '#686280', '#807a9a'),
                     SPECK=pal('#ffffff', '#cfe4ff', '#9fc4ff'),
                     WOOD=pal('#2e2a3a', '#45405a', '#5c5676', '#746e92', '#8c86ac', '#a49ec4'),
                     ROCK=[(215, 0.12, 0.62), (225, 0.18, 0.5), (205, 0.08, 0.78), (240, 0.2, 0.42)],
                     STYLE=dict(cap='snow', bands=[('soil', 2.4), ('clay', 1.2), ('gravel', 1.3), ('soil', 1.6), ('clay', 1.0), ('humus', 0.8)],
                                roots=0, bones=0, cracks=12, extra='ice', ceil='ice', glow=None),
                     ROOT_MAT=(230, 0.2, 0.5), OUTLINE='#1a1a2a'),
        'art': {'ambient': [0.86, 0.86, 0.98], 'sun': [1.0, 0.78, 0.82], 'sun_energy': 0.5, 'sun_rot': 25,
                'saturation': 0.95, 'contrast': 1.05, 'particles': 'kar', 'fog': True, 'rays': [1.0, 0.8, 0.85, 0.07],
                'decor': ['kaya', 'cira', 'kam_diregi'], 'decor_tint': [0.85, 0.88, 1.0],
                'torch_col': [1.0, 0.65, 0.35], 'deep_color': [0.12, 0.12, 0.2], 'gate_col': [0.8, 0.9, 1.0],
                'styles': ['ucurum', 'ucurum', 'orman', 'harabe'], 'sky_scale': 1},
    },
    'tamu': {
        'soil': dict(SOIL=pal('#0c0a0c', '#161214', '#201a1c', '#2a2224', '#342a2c', '#3e3234'),
                     CLAY=pal('#3a0c08', '#6a1810', '#9a2a12', '#c84418', '#e86424', '#ff8a30'),
                     HUMUS=pal('#080606', '#0e0a0a', '#140e0e', '#1a1212', '#201616', '#261a1a'),
                     GRASS=pal('#3a1008', '#6a1c0a', '#9a300e', '#c84a14', '#ea6a1c', '#ff8e2c', '#ffb850'),
                     ROOT=pal('#2a1a16', '#3e2820', '#54382c', '#6a4838'),
                     SPECK=pal('#ff9a40', '#6a5a5a', '#ffd070'),
                     WOOD=pal('#1a1214', '#2a1c1e', '#3a2628', '#4a3032', '#5a3a3c', '#6a4446'),
                     ROCK=[(350, 0.15, 0.22), (10, 0.3, 0.25), (0, 0.1, 0.16), (20, 0.5, 0.35)],
                     STYLE=dict(cap='ash', bands=[('soil', 2.4), ('humus', 1.2), ('gravel', 1.2), ('soil', 1.8), ('humus', 1.4)],
                                roots=0, bones=9, cracks=6, extra='lava', ceil='drip', glow=[1.0, 0.42, 0.1]),
                     ROOT_MAT=(10, 0.4, 0.3), OUTLINE='#050303'),
        'art': {'ambient': [0.5, 0.3, 0.3], 'sun': [1.0, 0.45, 0.2], 'sun_energy': 0.3, 'sun_rot': 120,
                'saturation': 1.1, 'contrast': 1.12, 'particles': 'kor', 'fog': True, 'rays': [1.0, 0.4, 0.2, 0.05],
                'decor': ['kaya', 'cira', 'kam_diregi'], 'decor_tint': [0.6, 0.45, 0.45],
                'torch_col': [1.0, 0.45, 0.15], 'deep_color': [0.08, 0.02, 0.02], 'gate_col': [1.0, 0.5, 0.3],
                'styles': ['harabe', 'ucurum', 'magara'], 'sky_scale': 1},
    },
}

## Derinlik sırası (her biyom 2 derinlik)
ORDER = ['otuken', 'bozkir', 'sahmeran', 'kaf', 'tamu']

## Biyom düşmanları: world.json'daki kimlik -> temel yaratık sprite'ı ve renk tonu
RESKIN = {
    'bozkir': {'yek': ('kara_boru', [1.3, 1.1, 0.7]), 'kara_kus_yavrusu': ('cor', [1.1, 0.8, 0.5]), 'kurgan_bekcisi': ('balbal', [1.1, 1.0, 0.8]),
               'tozkoparan': ('agac_iyesi', [1.2, 1.0, 0.7]), 'kurgan_okcusu': ('arcura', [1.1, 0.9, 0.7]), 'al_atli': ('surale', [1.2, 0.6, 0.5])},
    'sahmeran': {'kirkayak': ('kara_boru', [0.6, 1.2, 0.8]), 'kan_yarasasi': ('cor', [1.2, 0.5, 0.6]), 'yilan_muhafiz': ('balbal', [0.6, 1.1, 0.8]),
                 'su_iyesi': ('agac_iyesi', [0.5, 0.9, 1.2]), 'isilti_bocegi': ('arcura', [0.7, 1.3, 0.9]), 'tas_kertenkele': ('surale', [0.7, 0.9, 0.7])},
    'kaf': {'ayaz_kurdu': ('kara_boru', [0.8, 0.95, 1.3]), 'kaf_kartali': ('cor', [0.9, 0.95, 1.2]), 'buz_balbali': ('balbal', [0.8, 0.9, 1.3]),
            'dev_cocugu': ('agac_iyesi', [0.85, 0.9, 1.2]), 'simurg_muhafizi': ('arcura', [1.0, 0.85, 1.1]), 'karakoncolos': ('surale', [0.8, 0.85, 1.1])},
    'tamu': {'demir_gaga': ('kara_boru', [1.2, 0.5, 0.4]), 'kayip_ruh': ('cor', [0.9, 0.6, 1.2]), 'tamu_bekcisi': ('balbal', [0.9, 0.5, 0.5]),
             'od_iyesi': ('agac_iyesi', [1.3, 0.6, 0.4]), 'erlik_kizi': ('arcura', [1.1, 0.6, 1.1]), 'kara_atli': ('surale', [0.7, 0.5, 0.6])},
}


## Pozlama dengesi (v16): gündüz biyomlarının toprak paletleri göz yakıyordu (doygun sarı, açık uçlar ~0,85).
## Palet tanımları okunaklı kalsın diye renkler yerinde değil, burada derecelenir: (değer, doygunluk, koyu uç).
## Koyu uç: rampanın alt yarısı ek olarak karartılır; gölge/ışık arası değer aralığı açılır (hacim okunur).
## Gece biyomlarında ise tersi: toprak kesiti arka plan duvarlarıyla aynı karanlıktaydı, oyun alanı ayrışmıyordu;
## yalnızca toprak/humus/kök/ahşap/taş (ışıyan lav ve kapak renkleri değil) bir tık açılır. 4. öğe: derecelenecek paletler.
_EARTH = ('SOIL', 'HUMUS', 'ROOT', 'WOOD', 'ROCK')
SOIL_GRADE = {
    'bozkir': (0.86, 0.78, 0.84),
    'kaf': (0.94, 0.9, 0.86),
    'otuken': (1.12, 1.0, 1.0, _EARTH),
    'sahmeran': (1.15, 1.0, 1.0, _EARTH),
    'tamu': (1.4, 1.0, 1.0, _EARTH),
}


def _grade_ramp(p, val, sat, dark):
    p = np.asarray(p, float)
    lum = (p * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True)
    q = (lum + (p - lum) * sat) * val
    n = len(q)
    if n > 2:
        w = np.clip(1.0 - np.arange(n) / (n - 1) * 2.0, 0, 1)[:, None]   # alt yarı: 1 → 0
        q = q * (1 - w * (1 - dark))
    return np.clip(q, 0, 1)


for _bid, _g in SOIL_GRADE.items():
    _v, _s, _d = _g[:3]
    _keys = _g[3] if len(_g) > 3 else ('SOIL', 'CLAY', 'HUMUS', 'GRASS', 'ROOT', 'SPECK', 'WOOD', 'ROCK')
    _sc = BIOMES[_bid]['soil']
    for _k in _keys:
        if _k != 'ROCK':
            _sc[_k] = _grade_ramp(_sc[_k], _v, _s, _d)
    if 'ROCK' in _keys:
        _sc['ROCK'] = [(h, s * _s, min(0.95, v * _v)) for (h, s, v) in _sc['ROCK']]
    if 'ROOT' in _keys:
        _rh, _rs, _rv = _sc['ROOT_MAT']
        _sc['ROOT_MAT'] = (_rh, _rs * _s, min(0.95, _rv * _v))
