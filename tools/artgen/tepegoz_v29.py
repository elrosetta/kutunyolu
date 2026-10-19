"""Tepegöz v29: hamle başına tam gövde animasyonları (tepegoz_ink.draw pozlarıyla).

Her hamle: hazırlık (bütün gövdeyle kurulma; "!!" zırhlı hamlelerde ayrı, yere çöken / kollarını açan duruş), temas,
aşma (follow-through), toparlanma. Evre bölümleri (seg) Boss.gd'de hamlenin adımlarına eşlenir: 'w' hazırlık (uyarı
süresine yayılır, son kare fırlama anı), 's' temas + aşma (vuruş anında açılır), 'r' toparlanma (hamle sonrası bekleme),
'a' eylem / döngü, 'd' hücum döngüsü, 'h' tutma, 't' fırlatma, 'v' açık pencere (GÖZ AÇIK) döngüsü.

Ağırlık: kalça (bob, hx) her zaman destek ayağının üstüne kayar; yere basan ayak kaymaz (yürüyüşte geriye eşit hızla
akar); ağır darbede gövde çöker (bob 12-26), baş ve göz gecikmeli izler (ht, hy); gürz ucu temasta yere değer.
"""
import math

import bosskit as bk
import tepegoz_ink as tg
from tepegoz_ink import _base as B

mix, over = bk.mix, bk.over
R = B()          # dinlenme duruşu


def club_tip(p, ca=None):
    """tepegoz_ink.draw ile aynı geometri: gürz eli ve ucu (dünya birimi, gövde dönüşümü öncesi)."""
    lean = p['lean']
    up = (math.sin(lean), -math.cos(lean))
    fw = (math.cos(lean), math.sin(lean))
    hip = (p['hx'], -tg.HIP_H + p['bob'])
    sc = bk.add(hip, up, 54.0)
    sh = bk.add(bk.add(sc, fw, -5.0), up, -1.0)
    _, h = bk.arm_fk(sh, p['arm'], p['el'], tg.L_UP, tg.L_FO)
    a = p['ca'] if ca is None else ca
    return h, (h[0] + math.cos(a) * tg.CLUB_L, h[1] + math.sin(a) * tg.CLUB_L)


def far_hand(p):
    lean = p['lean']
    up = (math.sin(lean), -math.cos(lean))
    fw = (math.cos(lean), math.sin(lean))
    sc = bk.add((p['hx'], -tg.HIP_H + p['bob']), up, 54.0)
    sh = bk.add(bk.add(sc, fw, 14.0), up, 3.0)
    return bk.arm_fk(sh, p['arm_b'], p['el_b'], tg.L_UP, tg.L_FO)[1]


def fit(p, top=-166.0, ground=-10.0, left=-80.0, right=146.0):
    """Gürz ucu hücrede kalsın ve yere gömülmesin: ucu sınır dışındaysa gürz açısı el çevresinde en yakın geçerli açıya
    döndürülür (temas karelerinde uç tam yere değer)."""
    if p.get('club_free') or p.get('rot'):
        return p
    # baş üstü kurulmada el hücre tavanına taşmasın: dirsek bükülür (gürz sırta düşer, okunur bir kurulma silueti)
    while club_tip(p)[0][1] < -150.0 and p['el'] < 2.6:
        p = over(p, el=p['el'] + 0.04)
    lim = -128.0 if p.get('rock', 0) > 0 else -150.0
    while far_hand(p)[1] < lim and p['el_b'] < 2.6:
        p = over(p, el_b=p['el_b'] + 0.04)
    h, t = club_tip(p)

    def ok(a):
        x, y = h[0] + math.cos(a) * tg.CLUB_L, h[1] + math.sin(a) * tg.CLUB_L
        return top <= y <= ground and left <= x <= right
    if ok(p['ca']):
        return p
    for k in range(1, 200):
        for sg in (1, -1):
            a = p['ca'] + sg * k * 0.01
            if ok(a):
                return over(p, ca=a)
    return p


def clip(frames, fps=10, loop=False, seg=None):
    return bk.clip([fit(f) for f in frames], fps, loop, seg)


# ------------------------------------------------------------ dolaşım
def _idle(t):
    s = math.sin(t * math.tau)
    c = math.cos(t * math.tau)
    tic = max(0.0, math.sin((t - 0.55) * math.tau * 2.0)) if 0.55 <= t < 0.8 else 0.0   # burun çekip başını silkme
    return B(bob=1.6 * s + 0.6, breath=s, lean=0.30 + 0.025 * s, hx=1.4 * c, arm=0.22 + 0.03 * s, el=0.44, arm_b=0.12 - 0.04 * s,
             el_b=0.42 + 0.05 * c, ca=0.80 + 0.03 * s, mouth=0.12 + 0.10 * max(0.0, s) + 0.3 * tic,
             glow=0.6 + 0.3 * (0.5 + 0.5 * math.sin(t * math.tau * 2)), hy=1.0 * s - 1.2 * tic, ht=0.04 * s + 0.12 * tic, ph=t * math.tau,
             brow=0.2 + 0.4 * tic, ff=(15.0 + 0.6 * c, 0.0), fb=(-15.0 + 0.6 * c, 0.0))


def _walk(t):
    """Ağır, yeri döven yürüyüş: topuk vuruşunda kalça çöker (ağırlık kabulü), geçişte yükselir; omuzlar bacağa ters
    döner (gürz kolu arkaya savrulur), baş gecikmeli iner. Yere basan ayak geriye eşit hızla akar (35 birim / adım)."""
    S = 17.5

    def foot(ph):
        ph %= 1.0
        st = 0.56
        if ph < st:
            return (S - 2 * S * ph / st, 0.0)
        u = (ph - st) / (1 - st)
        e = u * u * (3 - 2 * u)
        return (-S + 2 * S * e, -math.sin(math.pi * u) * 15.0 * (1.0 - 0.25 * u))
    ff, fb = foot(t), foot(t + 0.5)
    w = math.cos(4 * math.pi * (t - 0.07))          # adım başına: +1 = çöküş (topuk vuruşu sonrası)
    sw = math.cos(2 * math.pi * t)                   # yakın bacak önde = +1
    return B(bob=2.6 + 3.4 * w, lean=0.36 + 0.03 * w, hx=1.0 * sw, ff=(ff[0] + 5, ff[1]), fb=(fb[0] - 7, fb[1]),
             arm=0.30 - 0.30 * sw, el=0.42 + 0.1 * (1 - sw), arm_b=0.15 + 0.32 * sw, el_b=0.5, ca=0.70 + 0.22 * sw,
             mouth=0.2 + 0.15 * max(0.0, w), glow=0.7, hy=1.6 * max(0.0, math.cos(4 * math.pi * (t - 0.14))), ht=0.05 * sw + 0.04 * w,
             ph=t * math.tau, breath=0.5 * w)


# ------------------------------------------------------------ gürz çakışı (iki elle baş üstünden)
SLAM = [
    B(bob=3, lean=0.20, hx=-2, arm=0.9, el=1.0, ca=-0.6, arm_b=0.6, el_b=0.9, mouth=0.3, brow=0.5, ht=-0.05, fb=(-17, 0)),
    B(bob=4, lean=0.04, hx=-4, arm=2.2, el=1.3, ca=-2.2, cz=-6, arm_b=1.4, el_b=1.1, mouth=0.6, brow=1, ht=-0.15, fb=(-21, 0), ff=(17, 0), glow=0.85),
    B(bob=6, lean=-0.14, hx=-7, arm=2.45, el=1.55, ca=-2.95, cz=-8, arm_b=2.2, el_b=1.3, fist_b=-1, mouth=1.0, brow=1, glow=1, ht=-0.32, hy=-2,
      ff=(19, -4), fb=(-23, 0), breath=1.0),
    B(bob=1, lean=0.22, hx=2, arm=2.45, el=0.35, ca=-1.65, arm_b=1.7, el_b=0.6, fist_b=-1, mouth=1.0, brow=1, glow=1, ht=-0.05,
      ff=(27, 0), fb=(-21, 0)),
    # 4: temas — gürz önde yere gömülür, gövde çöker, uzak el yere dayanır
    B(bob=15, lean=0.78, hx=6, arm=1.25, el=0.08, ca=1.22, arm_b=1.0, el_b=0.3, mouth=0.95, brow=1, glow=1, ht=0.28, hy=1.5,
      ff=(31, 0), fb=(-23, 0)),
    B(bob=12, lean=0.70, hx=5, arm=1.12, el=0.14, ca=1.3, arm_b=0.9, el_b=0.35, mouth=0.7, brow=0.9, glow=0.95, ht=0.22, ff=(31, 0), fb=(-23, 0)),
    B(bob=11, lean=0.64, hx=4, arm=1.05, el=0.25, ca=1.34, arm_b=0.8, el_b=0.4, mouth=0.55, brow=0.8, glow=0.9, ht=0.18, ff=(31, 0), fb=(-23, 0), breath=1),
    B(bob=8, lean=0.52, hx=3, arm=0.72, el=0.5, ca=1.02, arm_b=0.5, el_b=0.45, mouth=0.4, brow=0.6, ht=0.1, ff=(27, 0), fb=(-19, 0)),
    B(bob=4, lean=0.40, hx=1, arm=0.42, el=0.46, ca=0.86, arm_b=0.25, el_b=0.4, mouth=0.3, brow=0.4, ff=(21, -5), fb=(-16, 0)),
    B(bob=1, lean=0.32, arm=0.27, el=0.45, ca=0.78, mouth=0.2, ff=(16, 0)),
]

# ------------------------------------------------------------ kaya atışı
THROW = [
    B(bob=13, lean=0.85, hx=3, arm=0.3, el=0.5, ca=0.95, arm_b=0.55, el_b=0.15, rock=0.75, mouth=0.3, ht=0.32, ff=(22, 0), fb=(-18, 0)),
    B(bob=7, lean=0.32, hx=0, arm=0.45, el=0.6, ca=0.9, arm_b=2.2, el_b=1.45, rock=1.0, mouth=0.6, ht=-0.1, brow=0.6, ff=(20, 0), fb=(-19, 0)),
    B(bob=5, lean=-0.06, hx=-5, arm=1.2, el=0.3, ca=0.15, arm_b=2.8, el_b=1.6, rock=1.0, mouth=0.85, glow=1, ht=-0.22, brow=1,
      ff=(20, 0), fb=(-23, 0), breath=1),
    B(bob=3, lean=0.18, hx=0, arm=0.7, el=0.4, ca=0.5, arm_b=2.55, el_b=1.0, rock=1.0, mouth=1.0, glow=1, ht=-0.05, brow=1, ff=(27, 0), fb=(-20, 0)),
    # 4: bırakış — uzak kol ileri uzanmış, kaya elden çıktı
    B(bob=7, lean=0.6, hx=6, arm=0.15, el=0.6, ca=1.05, arm_b=1.72, el_b=0.05, mouth=1.0, glow=1, ht=0.15, brow=1, ff=(29, 0), fb=(-15, -3),
      arm_b_open=1.0),
    B(bob=9, lean=0.66, hx=6, arm=0.1, el=0.5, ca=1.1, arm_b=1.1, el_b=0.2, mouth=0.8, ht=0.2, brow=0.8, ff=(29, 0), fb=(-16, 0)),
    B(bob=5, lean=0.47, hx=3, arm=0.2, el=0.45, ca=0.95, arm_b=0.6, el_b=0.4, mouth=0.4, ht=0.1, ff=(24, 0), fb=(-17, 0)),
    B(bob=2, lean=0.34, hx=1, arm=0.24, el=0.45, ca=0.8, arm_b=0.2, el_b=0.38, mouth=0.2, ff=(18, 0)),
]

# ------------------------------------------------------------ yer tepme (diz göğse, topuk yere)
STOMP = [
    B(bob=3, lean=0.22, hx=-4, arm=0.7, el=0.5, ca=0.6, arm_b=1.0, el_b=0.6, ff=(15, -7), fb=(-15, 0), mouth=0.3, brow=0.6),
    B(bob=1, lean=0.08, hx=-7, arm=1.25, el=0.3, ca=0.05, arm_b=1.65, el_b=0.5, ff=(19, -27), fb=(-14, 0), mouth=0.55, brow=1, ht=-0.12, glow=0.9),
    B(bob=0, lean=-0.02, hx=-8, arm=1.6, el=0.3, ca=-0.45, arm_b=2.05, el_b=0.5, fist_b=-1, ff=(21, -35), fb=(-13, 0), mouth=0.85, brow=1, ht=-0.24,
      glow=1, breath=1),
    # 3: topuk yere — gövde çöker, kollar savrulur
    B(bob=15, lean=0.48, hx=2, arm=0.55, el=0.4, ca=1.05, arm_b=0.45, el_b=0.3, fist_b=-1, ff=(25, 0), fb=(-17, 0), mouth=1.0, brow=1, ht=0.24,
      glow=1, hy=2),
    B(bob=12, lean=0.42, hx=2, arm=0.45, el=0.4, ca=1.0, arm_b=0.35, el_b=0.35, ff=(25, 0), fb=(-17, 0), mouth=0.7, brow=0.8, ht=0.18),
    B(bob=6, lean=0.36, hx=1, arm=0.32, el=0.45, ca=0.86, arm_b=0.22, el_b=0.4, ff=(21, 0), fb=(-16, 0), mouth=0.4, ht=0.08),
    B(bob=2, lean=0.31, arm=0.26, el=0.45, ca=0.8, ff=(16, 0), mouth=0.2),
]

# ------------------------------------------------------------ yakın cezalandırıcı ("!!" zırhlı): iki yumrukla yere
NOVA = [
    B(bob=10, lean=0.55, hx=-1, arm=0.25, el=0.7, ca=1.1, arm_b=0.6, el_b=1.2, fist_b=-1, mouth=0.5, brow=1, glow=1, ht=0.3, ff=(20, 0), fb=(-20, 0)),
    B(bob=1, lean=-0.12, hx=-4, arm=2.3, el=0.25, ca=-2.0, cz=-6, arm_b=2.6, el_b=0.35, fist_b=-1, mouth=1.0, brow=1, glow=1, ht=-0.4, hy=-2,
      ff=(21, 0), fb=(-21, 0), breath=1),
    B(bob=17, lean=0.85, hx=4, arm=1.25, el=0.1, ca=1.4, arm_b=1.1, el_b=0.1, fist_b=-1, mouth=1.0, brow=1, glow=1, ht=0.35, ff=(24, 0), fb=(-22, 0)),
    B(bob=13, lean=0.7, hx=3, arm=1.05, el=0.25, ca=1.35, arm_b=0.85, el_b=0.25, fist_b=-1, mouth=0.7, brow=0.8, ht=0.25, ff=(24, 0), fb=(-22, 0)),
]

# ------------------------------------------------------------ kavrama ("!!" zırhlı)
GRAB = [
    B(bob=10, lean=0.55, hx=-3, arm=0.3, el=0.6, ca=0.95, arm_b=0.9, el_b=1.4, mouth=0.6, brow=1, glow=1, ht=0.12, ff=(19, 0), fb=(-21, 0)),
    B(bob=13, lean=0.62, hx=-5, arm=0.2, el=0.55, ca=1.0, arm_b=1.15, el_b=1.6, mouth=0.75, brow=1, glow=1, ht=0.05, ff=(20, 0), fb=(-23, 0), breath=1),
    B(bob=15, lean=0.7, hx=-7, arm=0.15, el=0.5, ca=1.05, arm_b=1.05, el_b=1.75, mouth=0.9, brow=1, glow=1, ht=0.0, hy=-1, ff=(21, 0), fb=(-25, 0)),
    # 3-4: uzanış — uzak kol sonuna dek ileri, avuç açık
    B(bob=10, lean=0.88, hx=8, arm=0.4, el=0.4, ca=1.1, arm_b=1.58, el_b=0.08, mouth=1.0, brow=1, glow=1, ht=0.3, ff=(34, 0), fb=(-14, -3)),
    B(bob=12, lean=0.92, hx=9, arm=0.45, el=0.4, ca=1.15, arm_b=1.48, el_b=0.18, mouth=0.9, brow=1, glow=1, ht=0.34, ff=(34, 0), fb=(-15, 0)),
    # 5-6: tutma / sıkma — yumruk göğüs önünde kalkık (yakalanan oyuncu orada)
    B(bob=3, lean=0.2, hx=1, arm=0.3, el=0.5, ca=0.9, arm_b=1.92, el_b=0.62, fist_b=-1, mouth=0.7, brow=1, glow=1, ht=-0.12, ff=(20, 0), fb=(-18, 0)),
    B(bob=5, lean=0.26, hx=1, arm=0.35, el=0.55, ca=0.92, arm_b=1.98, el_b=0.92, fist_b=-1, mouth=1.0, brow=1, glow=1, ht=-0.18, hy=-1, ff=(20, 0),
      fb=(-18, 0), breath=1),
    # 7-8: fırlatma
    B(bob=4, lean=-0.06, hx=-4, arm=0.6, el=0.4, ca=0.6, arm_b=2.85, el_b=1.2, fist_b=-1, mouth=0.9, brow=1, glow=1, ht=-0.25, ff=(20, 0), fb=(-22, 0)),
    B(bob=8, lean=0.62, hx=6, arm=0.15, el=0.5, ca=1.1, arm_b=1.45, el_b=0.08, mouth=1.0, brow=1, glow=1, ht=0.2, ff=(29, 0), fb=(-16, -2)),
    # 9-10: ıskaladı — öne savrulmuş, toparlanıyor (uzun açık)
    B(bob=16, lean=1.0, hx=11, arm=0.5, el=0.3, ca=1.25, arm_b=1.2, el_b=0.35, mouth=0.4, brow=0.2, glow=0.8, ht=0.42, hy=2, ff=(36, 0), fb=(-12, 0)),
    B(bob=9, lean=0.62, hx=6, arm=0.35, el=0.4, ca=1.0, arm_b=0.7, el_b=0.4, mouth=0.5, brow=0.8, glow=0.9, ht=0.15, ff=(28, 0), fb=(-15, 0)),
]

# ------------------------------------------------------------ göz ışını
BEAM = [
    B(bob=6, lean=0.1, hx=-3, arm=0.8, el=0.6, ca=0.55, arm_b=1.0, el_b=1.25, fist_b=-1, lid=0.55, glow=0.7, mouth=0.3, ht=-0.25, hy=-2, brow=1,
      ff=(18, 0), fb=(-18, 0)),
    B(bob=8, lean=0.22, hx=-2, arm=0.7, el=0.55, ca=0.6, arm_b=1.15, el_b=1.0, fist_b=-1, lid=0.0, glow=1.0, mouth=0.35, ht=-0.12, brow=-0.5,
      ff=(23, 0), fb=(-21, 0), breath=1),
    B(bob=10, lean=0.36, hx=1, arm=0.55, el=0.5, ca=0.75, arm_b=1.25, el_b=0.75, fist_b=-1, lid=0.0, glow=1.0, mouth=0.45, ht=0.15, brow=-0.6,
      ff=(26, 0), fb=(-22, 0)),
]
BEAM += [over(BEAM[2], bob=11 + k, lean=0.42 + 0.02 * k, hx=1.0 - k, ht=0.25 + 0.04 * (k - 1), mouth=0.55 + 0.1 * k, breath=k - 1,
              hy=0.6 * (k - 1)) for k in range(3)]
BEAM += [B(bob=6, lean=0.2, hx=-3, arm=0.6, el=0.55, ca=0.7, arm_b=0.8, el_b=0.9, lid=0.65, glow=0.55, mouth=0.3, ht=-0.22, hy=-1.5,
           ff=(22, 0), fb=(-19, 0)),
         B(bob=3, lean=0.3, hx=-1, arm=0.35, el=0.5, ca=0.78, arm_b=0.3, el_b=0.5, lid=0.3, glow=0.6, mouth=0.2, ht=0.08, ff=(17, 0))]

# ------------------------------------------------------------ hücum (boğa gibi başı önde)


def _run(t):
    S = 26.0

    def foot(ph):
        ph %= 1.0
        if ph < 0.42:
            return (S - 2 * S * ph / 0.42, 0.0)
        u = (ph - 0.42) / 0.58
        return (-S + 2 * S * (u * u * (3 - 2 * u)), -math.sin(math.pi * u) * 20.0)
    ff, fb = foot(t), foot(t + 0.5)
    w = math.cos(4 * math.pi * (t - 0.05))
    sw = math.cos(2 * math.pi * t)
    return B(bob=8 + 4 * w, lean=0.9 + 0.04 * w, hx=4, ff=(ff[0] + 8, ff[1]), fb=(fb[0] - 4, fb[1]), arm=0.15 - 0.45 * sw, el=0.5,
             ca=2.55 - 0.15 * sw, cz=-6, arm_b=0.5 + 0.6 * sw, el_b=0.9, fist_b=-1, mouth=0.75, glow=1, brow=1, ht=0.5, hy=2,
             ph=t * math.tau * 2, breath=w)


CHARGE = [
    B(bob=8, lean=0.68, hx=-2, arm=0.15, el=0.35, ca=1.5, arm_b=0.35, el_b=0.6, fist_b=-1, mouth=0.5, brow=1, glow=1, ht=0.45, ff=(19, -7), fb=(-20, 0)),
    B(bob=14, lean=0.86, hx=-3, arm=-0.2, el=0.4, ca=2.4, cz=-6, arm_b=0.5, el_b=0.8, fist_b=-1, mouth=0.8, brow=1, glow=1, ht=0.5, hy=2,
      ff=(23, 0), fb=(-27, 0), breath=1),
    B(bob=10, lean=0.95, hx=2, arm=-0.35, el=0.4, ca=2.55, cz=-6, arm_b=0.8, el_b=0.9, fist_b=-1, mouth=0.9, brow=1, glow=1, ht=0.5, hy=2,
      ff=(31, 0), fb=(-31, -5)),
] + [_run(k / 4) for k in range(4)] + [
    B(bob=11, lean=0.3, hx=-7, arm=0.6, el=0.4, ca=0.6, arm_b=1.3, el_b=0.4, mouth=0.6, brow=0.8, glow=0.9, ht=-0.12, ff=(32, 0), fb=(-17, 0)),
]

# ------------------------------------------------------------ GÖZ AÇIK (duvara çarptı: sersem, göz kocaman açık)


def _daze(k):
    s = math.sin(k / 4 * math.tau)
    c = math.cos(k / 4 * math.tau)
    return B(bob=25.5 + 1.2 * s, lean=0.26 + 0.05 * s, hx=-4 + 0.8 * c, arm=0.35, el=0.3, ca=1.35 + 0.03 * s, arm_b=0.55 + 0.06 * c, el_b=0.25,
             lid=0.0, glow=0.85 + 0.15 * c, mouth=0.45 + 0.12 * s, brow=-0.5, ht=0.3 + 0.13 * c, hy=1.5 * s, ff=(24, 0), fb=(-34, 0),
             breath=s, arm_b_open=1.0)


DAZED = [
    B(bob=6, lean=-0.22, hx=-7, arm=1.0, el=0.2, ca=0.0, arm_b=2.2, el_b=0.3, lid=0.0, glow=1.0, mouth=0.95, brow=-0.3, ht=-0.5, hy=-3,
      ff=(10, -6), fb=(-24, 0), arm_b_open=1.0),
    B(bob=24, lean=0.28, hx=-5, arm=0.35, el=0.3, ca=1.3, arm_b=0.6, el_b=0.25, lid=0.0, glow=1.0, mouth=0.6, brow=-0.4, ht=0.38, hy=1,
      ff=(24, 0), fb=(-34, 0), arm_b_open=1.0),
] + [_daze(k) for k in range(4)] + [
    B(bob=12, lean=0.32, hx=-2, arm=0.6, el=0.5, ca=0.9, arm_b=1.0, el_b=1.0, fist_b=-1, lid=0.0, glow=1.0, mouth=0.7, brow=1, ht=-0.1,
      ff=(22, 0), fb=(-24, 0)),
]

# ------------------------------------------------------------ dağ sarsıntısı (ortaya sıçrayış)
QUAKE = [
    B(bob=18, lean=0.58, hx=-2, arm=-0.35, el=0.45, ca=2.4, cz=-6, arm_b=-0.15, el_b=0.5, mouth=0.6, brow=1, glow=1, ht=0.3, ff=(21, 0), fb=(-21, 0)),
    B(bob=22, lean=0.65, hx=-3, arm=-0.6, el=0.45, ca=2.6, cz=-6, arm_b=-0.3, el_b=0.5, mouth=0.8, brow=1, glow=1, ht=0.35, ff=(22, 0), fb=(-22, 0),
      breath=1),
    # 2-4: havada (yükseliş, tepe, düşüş)
    B(bob=0, lean=0.12, arm=2.4, el=0.6, ca=-2.0, cz=-6, arm_b=2.4, el_b=0.4, fist_b=-1, mouth=0.9, brow=1, glow=1, ht=-0.2, ff=(8, 4), fb=(-12, 6)),
    B(bob=-4, lean=-0.1, arm=2.8, el=1.15, ca=-2.7, cz=-8, arm_b=2.65, el_b=0.8, fist_b=-1, mouth=1.0, brow=1, glow=1, ht=-0.3, ff=(16, -18),
      fb=(-12, -14)),
    B(bob=-2, lean=0.3, arm=2.35, el=0.45, ca=-1.6, arm_b=2.0, el_b=0.5, fist_b=-1, mouth=1.0, brow=1, glow=1, ht=0.0, ff=(20, -4), fb=(-16, -2)),
    # 5-6: iniş çakışı
    B(bob=19, lean=0.82, hx=5, arm=1.22, el=0.08, ca=1.28, arm_b=0.95, el_b=0.15, fist_b=-1, mouth=1.0, brow=1, glow=1, ht=0.32, hy=2,
      ff=(27, 0), fb=(-25, 0)),
    B(bob=17, lean=0.74, hx=4, arm=1.1, el=0.15, ca=1.33, arm_b=0.85, el_b=0.25, fist_b=-1, mouth=0.75, brow=0.9, glow=1, ht=0.25, ff=(27, 0),
      fb=(-25, 0)),
    B(bob=8, lean=0.5, hx=2, arm=0.6, el=0.4, ca=1.0, arm_b=0.45, el_b=0.4, mouth=0.4, ht=0.1, ff=(22, 0), fb=(-19, 0)),
]

# ------------------------------------------------------------ kükreme (giriş, evre geçişi, GÖZ AÇIK sonrası)
ROAR = [
    B(bob=8, lean=0.6, hx=0, arm=0.1, el=0.4, ca=1.2, arm_b=0.2, el_b=0.6, fist_b=-1, mouth=0.1, brow=1, glow=0.8, ht=0.35, hy=2, ff=(18, 0), fb=(-18, 0)),
    B(bob=11, lean=0.72, hx=-1, arm=0.0, el=0.5, ca=1.3, arm_b=0.1, el_b=0.9, fist_b=-1, mouth=0.15, brow=1, glow=0.9, ht=0.45, hy=3, ff=(19, 0),
      fb=(-19, 0), breath=1),
    B(bob=2, lean=0.08, hx=-2, arm=1.2, el=0.3, ca=-0.3, arm_b=1.8, el_b=0.9, fist_b=-1, mouth=0.8, brow=1, glow=1, ht=-0.3, hy=-2, ff=(21, 0), fb=(-21, 0)),
    B(bob=0, lean=-0.1, hx=-3, arm=1.65, el=0.2, ca=-0.85, arm_b=2.5, el_b=1.0, fist_b=-1, mouth=1.0, brow=1, glow=1, ht=-0.5, hy=-3, ff=(23, 0),
      fb=(-23, 0), breath=1),
    B(bob=1, lean=-0.07, hx=-3, arm=1.7, el=0.18, ca=-0.9, arm_b=2.55, el_b=1.05, fist_b=-1, mouth=1.0, brow=1, glow=1, ht=-0.46, hy=-2.5,
      ff=(23, 0), fb=(-23, 0), breath=0.6),
    B(bob=0, lean=-0.1, hx=-3, arm=1.62, el=0.22, ca=-0.8, arm_b=2.48, el_b=0.95, fist_b=-1, mouth=1.0, brow=1, glow=1, ht=-0.52, hy=-3,
      ff=(23, 0), fb=(-23, 0), breath=1),
    B(bob=4, lean=0.16, hx=-1, arm=1.0, el=0.35, ca=0.2, arm_b=1.35, el_b=1.9, fist_b=-1, mouth=0.7, brow=1, glow=1, ht=-0.1, ff=(21, 0), fb=(-20, 0)),
    B(bob=3, lean=0.3, arm=0.4, el=0.45, ca=0.75, arm_b=0.4, el_b=0.6, mouth=0.3, brow=0.8, glow=0.9, ht=0.05, ff=(17, 0)),
]

# ------------------------------------------------------------ duruş kırılması (SENDELEDİ)
STAGGER = [
    B(bob=4, lean=-0.16, hx=-7, arm=0.95, el=0.3, ca=0.15, arm_b=2.0, el_b=0.5, lid=0.7, glow=0.3, mouth=0.85, brow=-0.3, ht=-0.45, hy=-2,
      ff=(12, 0), fb=(-19, 0), arm_b_open=1.0),
    B(bob=6, lean=-0.06, hx=-11, arm=0.7, el=0.4, ca=0.5, arm_b=1.5, el_b=0.6, lid=0.5, glow=0.35, mouth=0.7, ht=-0.3, ff=(6, -9), fb=(-31, 0),
      arm_b_open=1.0),
    B(bob=26, lean=0.36, hx=-6, arm=0.4, el=0.3, ca=1.42, arm_b=0.5, el_b=0.2, lid=0.5, glow=0.4, mouth=0.5, ht=0.42, hy=1, ff=(22, 0), fb=(-34, 0),
      arm_b_open=1.0),
    B(bob=27, lean=0.42, hx=-6, arm=0.38, el=0.3, ca=1.44, arm_b=0.45, el_b=0.2, lid=0.45, glow=0.35, mouth=0.4, ht=0.5, hy=2.5, ff=(22, 0),
      fb=(-34, 0), breath=1, arm_b_open=1.0),
    B(bob=26.5, lean=0.4, hx=-6, arm=0.38, el=0.3, ca=1.44, arm_b=0.45, el_b=0.2, lid=0.4, glow=0.4, mouth=0.55, ht=0.46, hy=2, ff=(22, 0),
      fb=(-34, 0), breath=-0.5, arm_b_open=1.0),
    B(bob=18, lean=0.52, hx=-3, arm=0.6, el=0.2, ca=1.3, arm_b=0.9, el_b=0.6, lid=0.2, glow=0.6, mouth=0.65, ht=0.2, ff=(22, 0), fb=(-28, 0)),
    B(bob=9, lean=0.4, hx=-1, arm=0.45, el=0.4, ca=1.0, arm_b=0.8, el_b=1.0, fist_b=-1, glow=0.85, mouth=0.75, brow=1, ht=0.0, ff=(20, 0), fb=(-20, 0)),
    B(bob=3, lean=0.3, arm=0.3, el=0.45, ca=0.8, arm_b=0.3, el_b=0.6, fist_b=-1, glow=1.0, mouth=0.4, brow=1, ff=(16, 0)),
]

# ------------------------------------------------------------ ölüm (diz çöker, gürz elden düşer, yüzüstü yıkılır)
DEATH = [
    B(bob=4, lean=-0.2, hx=-6, arm=1.45, el=0.2, ca=-0.5, arm_b=2.3, el_b=0.4, lid=0.15, glow=0.8, mouth=1.0, brow=-0.4, ht=-0.5, hy=-3,
      ff=(13, 0), fb=(-20, 0), arm_b_open=1.0),
    B(bob=6, lean=-0.12, hx=-10, arm=1.1, el=0.3, ca=0.2, arm_b=1.9, el_b=0.5, lid=0.3, glow=0.6, mouth=0.9, ht=-0.38, ff=(8, -7), fb=(-30, 0),
      arm_b_open=1.0),
    B(bob=24, lean=0.22, hx=-7, arm=0.6, el=0.2, arm_b=0.9, el_b=0.3, lid=0.45, glow=0.5, mouth=0.6, ht=0.2, ff=(20, 0), fb=(-32, 0),
      club_free=(34.0, -40.0, 1.15), arm_b_open=1.0),
    B(bob=34, lean=0.18, hx=-6, arm=0.2, el=0.15, arm_b=0.25, el_b=0.15, lid=0.55, glow=0.4, mouth=0.5, ht=0.5, hy=2, ff=(4, 0), fb=(-12, 0),
      club_free=(46.0, -13.0, 0.06, -14), arm_b_open=1.0),
    B(bob=35, lean=0.28, hx=-6, arm=0.15, el=0.15, arm_b=0.2, el_b=0.15, lid=0.7, glow=0.3, mouth=0.35, ht=0.65, hy=3, ff=(4, 0), fb=(-12, 0),
      club_free=(46.0, -13.0, 0.06, -14), arm_b_open=1.0, breath=1),
    B(bob=35, lean=0.5, hx=-6, arm=0.5, el=0.2, arm_b=0.8, el_b=0.2, lid=0.8, glow=0.25, mouth=0.4, ht=0.6, hy=2, ff=(4, 0), fb=(-12, 0),
      club_free=(46.0, -13.0, 0.06, -14), arm_b_open=1.0, rot=0.3, rp=(6.0, -4.0)),
    B(bob=35, lean=0.6, hx=-6, arm=1.0, el=0.2, arm_b=1.2, el_b=0.15, lid=0.9, glow=0.15, mouth=0.5, ht=0.4, hy=1, ff=(4, 0), fb=(-12, 0),
      club_free=(46.0, -13.0, 0.06, -14), arm_b_open=1.0, rot=0.72, rp=(6.0, -4.0)),
    B(bob=35, lean=0.62, hx=-6, arm=1.4, el=0.3, arm_b=1.5, el_b=0.2, lid=1.0, glow=0.05, mouth=0.4, ht=0.3, ff=(4, 0), fb=(-12, 0),
      club_free=(46.0, -13.0, 0.06, -14), arm_b_open=1.0, rot=0.98, rp=(6.0, -4.0)),
    B(bob=35, lean=0.6, hx=-6, arm=1.5, el=0.35, arm_b=1.6, el_b=0.2, lid=1.0, glow=0.0, mouth=0.3, ht=0.3, ff=(4, 0), fb=(-12, 0),
      club_free=(46.0, -13.0, 0.06, -14), arm_b_open=1.0, rot=1.04, rp=(6.0, -4.0)),
    B(bob=35, lean=0.6, hx=-6, arm=1.5, el=0.35, arm_b=1.6, el_b=0.2, lid=1.0, glow=0.0, mouth=0.25, ht=0.32, ff=(4, 0), fb=(-12, 0),
      club_free=(46.0, -13.0, 0.06, -14), arm_b_open=1.0, rot=1.02, rp=(6.0, -4.0)),
]


CLIPS = {
    'idle': clip([_idle(k / 8) for k in range(8)], 7, loop=True),
    'walk': clip([_walk(k / 8) for k in range(8)], 8, loop=True),
    'tg_slam': clip(SLAM, 12, seg={'w': [0, 3], 's': [4, 6], 'r': [7, 9]}),
    'tg_throw': clip(THROW, 10, seg={'w': [0, 3], 's': [4, 5], 'r': [6, 7]}),
    'tg_stomp': clip(STOMP, 12, seg={'w': [0, 2], 's': [3, 4], 'r': [5, 6]}),
    'tg_nova': clip(NOVA, 10, seg={'w': [0, 1], 's': [2, 3]}),
    'tg_grab': clip(GRAB, 10, seg={'w': [0, 2], 's': [3, 4], 'h': [5, 6, 5], 't': [7, 8], 'r': [9, 10]}),
    'tg_beam': clip(BEAM, 10, seg={'w': [0, 2], 'a': [3, 5, 3], 'r': [6, 7]}),
    'tg_charge': clip(CHARGE, 12, seg={'w': [0, 2], 'd': [3, 6, 3], 'r': [7, 7]}),
    'tg_dazed': clip(DAZED, 7, seg={'v': [0, 5, 2], 'w': [6, 6]}),
    'tg_quake': clip(QUAKE, 10, seg={'w': [0, 1], 'a': [2, 4], 's': [5, 6], 'r': [7, 7]}),
    'tg_roar': clip(ROAR, 10, seg={'a': [0, 7]}),
    'tg_stagger': clip(STAGGER, 8, seg={'a': [0, 7]}),
    'tg_death': clip(DEATH, 8, seg={'a': [0, 9]}),
}
