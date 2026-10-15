"""v11 biyom boss'ları: Tepegöz (Bozkır), Şahmeran Ana (Şahmeran'ın Mağarası), Yelbegen (Kaf Dağı), Erlik Han (Tamu).
Hepsi yüz sağa, ayak merkezi (0,0). Ortak animasyon adları: idle, walk, windup, strike, slam, cast, hurt, rage.
Poz anahtarları: bob, lean, arm (ön kol açısı, 0 aşağı / pi/2 ileri / pi yukarı), arm_b (arka kol), legs (yürüyüş fazı),
mouth (0..1), glow (göz/rune parlaklığı), extra (boss'a özgü: kuyruk dalgası, baş yönleri vb.)."""
import math
import numpy as np
from raster import Canvas, Mat, ramp
from materials import M
from rig import fk_leg, fk_arm, lerp2, chain
import creatures as C1


class _Z:
    """Z katmanlarını açar: büyük boss parçalarının kendi kabarıklığı (yarıçap kadar) üstündeki yüz/göz gibi ayrıntıları
    örtmesin diye tüm z değerleri ZK ile çarpılır (sıralama korunur, aralık büyür)."""
    ZK = 6.0

    def __init__(self, c):
        self.c = c

    def capsule(self, p0, p1, r0, r1, mat, z=0.0, **kw):
        self.c.capsule(p0, p1, r0, r1, mat, z=z * self.ZK, **kw)

    def ellipse(self, c_, rx, ry, mat, z=0.0, **kw):
        self.c.ellipse(c_, rx, ry, mat, z=z * self.ZK, **kw)

    def poly(self, pts, mat, z=0.0, **kw):
        self.c.poly(pts, mat, z=z * self.ZK, **kw)

    def dot(self, p, mat, z=50.0, **kw):
        self.c.dot(p, mat, z=z * self.ZK, **kw)


def _k(t, frames):
    """Kare listesi arasında yumuşak geçiş (smoothstep) — kukla gibi atlamayan pozlar."""
    n = len(frames)
    if n == 1:
        return frames[0]
    x = t * (n - 1)
    i = min(n - 2, int(x))
    u = x - i
    u = u * u * (3 - 2 * u)
    a, b = frames[i], frames[i + 1]
    out = {}
    for key in set(a) | set(b):
        va, vb = a.get(key, b.get(key)), b.get(key, a.get(key))
        if isinstance(va, tuple):
            out[key] = tuple(x0 + (y0 - x0) * u for x0, y0 in zip(va, vb))
        else:
            out[key] = va + (vb - va) * u
    return out


def _walk(t, amp=0.6, bob=2.0):
    s = math.sin(t * math.tau)
    return dict(legs=s * amp, bob=-abs(s) * bob + bob * 0.5, arm=0.3 - 0.25 * s, arm_b=0.3 + 0.25 * s, lean=0.06)


# ------------------------------------------------------------ TEPEGÖZ
TG_SKIN = Mat(ramp(28, 0.42, 0.62, spread=0.45), name='dev derisi')
TG_SKIN_D = Mat(ramp(20, 0.48, 0.42, spread=0.4), name='dev derisi gölge')
TG_HIDE = Mat(ramp(36, 0.35, 0.36, spread=0.4), name='post etek')
TG_EYE = Mat(ramp(48, 0.9, 1.0, spread=0.2), emissive=1.0, outline='#5a2a04', name='tek göz')
TG_CLUB = Mat(ramp(24, 0.5, 0.36, spread=0.45), name='kütük gürz')
TG_HAIR = Mat(ramp(20, 0.3, 0.18, spread=0.3), name='kara saç')


def draw_tepegoz(c, p):
    """Tepegöz: Dede Korkut'un tek gözlü devi. Kambur, iri omuzlar, alnının ortasında kocaman yanan göz, post etek,
    elinde kaya çivili kütük gürz; boynunda kemik kolye."""
    c = _Z(c)
    bob, lean = p.get('bob', 0.0), p.get('lean', 0.0)
    legs = p.get('legs', 0.0)
    hip = (0.0, -58 + bob)
    neck = (hip[0] + math.sin(lean) * 44 + 6, hip[1] - math.cos(lean) * 44)
    # bacaklar: kalın, kısa
    for side, z in ((-1, -6), (1, 8)):
        a = 0.35 * legs * side
        k, f = fk_leg((hip[0] + side * 7, hip[1]), a, 0.25 + 0.3 * max(0, -legs * side), 30, 30)
        mat = TG_SKIN if z > 0 else TG_SKIN_D
        c.capsule((hip[0] + side * 7, hip[1]), k, 11, 9, mat, z=z)
        c.capsule(k, f, 9, 7, mat, z=z)
        c.ellipse((f[0] + 5, f[1] - 3), 10, 5, mat, z=z + 0.5)
    # etek
    c.poly([(hip[0] - 20, hip[1] - 8), (hip[0] + 20, hip[1] - 8), (hip[0] + 24, hip[1] + 18), (hip[0] - 22, hip[1] + 16)], TG_HIDE, z=2, bevel=3, height=2,
           paint=[(lambda lu, lv, px, py: (np.floor(px * 0.3) % 3 == 0) & (py > hip[1] + 10), M['bone'])])
    # arka kol
    ab = p.get('arm_b', 0.3)
    e, h = fk_arm((neck[0] - 14, neck[1] + 12), ab, 0.5, 28, 26)
    c.capsule((neck[0] - 14, neck[1] + 12), e, 10, 8, TG_SKIN_D, z=-8)
    c.capsule(e, h, 8, 7, TG_SKIN_D, z=-8)
    c.ellipse(h, 8, 7, TG_SKIN_D, z=-7)
    # gövde: kambur, göbekli
    mid = lerp2(hip, neck, 0.5)
    c.ellipse((mid[0] + 2, mid[1] + 4), 26, 30, TG_SKIN, z=3, rot=lean, depth=0.5, paint=[(lambda lu, lv, px, py: lv < -0.5, TG_SKIN_D)])
    c.ellipse((neck[0] - 4, neck[1] + 6), 24, 14, TG_SKIN, z=4, depth=0.5)  # kambur omuz
    # kemik kolye
    for k in range(5):
        a = math.pi * (0.25 + k * 0.12)
        c.poly([(neck[0] + math.cos(a) * 14 - 2, neck[1] + 12 + math.sin(a) * 6), (neck[0] + math.cos(a) * 14 + 2, neck[1] + 12 + math.sin(a) * 6),
                (neck[0] + math.cos(a) * 15, neck[1] + 20 + math.sin(a) * 6)], M['bone'], z=9, bevel=0.8, height=0.8)
    # baş: alçak, iri çene, tek göz
    head = (neck[0] + 10, neck[1] - 4 + p.get('hy', 0.0))
    hx, hy = head
    c.ellipse(head, 15, 14, TG_SKIN, z=40, paint=[(lambda lu, lv, px, py: lv < -0.55, TG_HAIR)])
    c.ellipse((hx + 6, hy + 8), 11, 7 + 4 * p.get('mouth', 0.0), TG_SKIN_D, z=41)
    if p.get('mouth', 0.0) > 0.2:
        c.ellipse((hx + 8, hy + 9), 7, 2 + 4 * p.get('mouth', 0.0), M['red_paint'], z=42)
        for i in range(3):
            c.dot((hx + 4 + i * 3, hy + 6), M['bone'], z=44, size=2)
    c.ellipse((hx + 6, hy - 3), 7.5, 7.0, M['nazar_w'], z=43)
    gl = p.get('glow', 0.6)
    c.ellipse((hx + 7 + gl * 1.5, hy - 3), 4.5, 4.5, TG_EYE, z=44)
    c.ellipse((hx + 8 + gl * 1.5, hy - 3), 1.8, 1.8, M['black'], z=45)
    c.capsule((hx - 2, hy - 11), (hx + 14, hy - 10), 2.0, 1.6, TG_SKIN_D, z=45)  # kaş çıkıntısı
    # ön kol + gürz
    a1 = p.get('arm', 0.3)
    e2, h2 = fk_arm((neck[0] + 10, neck[1] + 12), a1, 0.35, 28, 26)
    c.capsule((neck[0] + 10, neck[1] + 12), e2, 11, 9, TG_SKIN, z=58)
    c.capsule(e2, h2, 9, 8, TG_SKIN, z=58)
    c.ellipse(h2, 9, 8, TG_SKIN, z=59)
    ca = a1 + 0.35 + p.get('club', 0.0)
    tip = (h2[0] + math.sin(ca) * 62, h2[1] + math.cos(ca) * 62)
    c.capsule(h2, tip, 5, 10, TG_CLUB, z=57)
    for k in range(5):
        q = lerp2(h2, tip, 0.55 + k * 0.09)
        c.poly([(q[0] - 2, q[1] - 2), (q[0] + 2, q[1] + 2), (q[0] + math.cos(ca + 1.2) * 7, q[1] - math.sin(ca + 1.2) * 7)], M['stone'], z=57.5, bevel=0.8, height=1)
    return {'hand': h2, 'mouth': (hx + 8, hy + 8), 'eye': (hx + 7, hy - 3), 'club': tip}


TG_ANIMS = {
    'idle': (8, lambda t: dict(bob=1.2 * math.sin(t * math.tau), lean=0.1 + 0.02 * math.sin(t * math.tau), arm=0.35, arm_b=0.25, glow=0.5 + 0.5 * math.sin(t * math.tau))),
    'walk': (8, lambda t: dict(_walk(t, 0.6, 3.0), lean=0.14, glow=0.6)),
    'windup': (4, lambda t: _k(t, [dict(bob=1.0, lean=0.0, arm=0.9, club=0.0, glow=0.7), dict(bob=3.0, lean=-0.18, arm=2.9, club=0.4, glow=1.0, mouth=0.4)])),
    'strike': (4, lambda t: _k(t, [dict(bob=-2.0, lean=0.3, arm=1.6, club=0.2, mouth=0.8, glow=1.0), dict(bob=4.0, lean=0.42, arm=0.6, club=-0.3, mouth=0.4, glow=0.8)])),
    'slam': (3, lambda t: _k(t, [dict(bob=-6.0, lean=0.2, arm=3.0, arm_b=2.8, club=0.2, mouth=1.0), dict(bob=6.0, lean=0.45, arm=0.4, arm_b=0.6, club=-0.4, mouth=0.6)])),
    'cast': (3, lambda t: _k(t, [dict(bob=1.0, lean=-0.1, arm=0.3, arm_b=2.4, glow=0.8), dict(bob=0.0, lean=0.3, arm=0.3, arm_b=1.5, glow=1.0, mouth=0.5)])),
    'hurt': (2, lambda t: _k(t, [dict(bob=2.0, lean=-0.25, arm=0.6, mouth=0.7, glow=0.2), dict(bob=1.0, lean=-0.1, arm=0.4, mouth=0.3, glow=0.4)])),
    'rage': (3, lambda t: dict(bob=2 * math.sin(t * math.tau * 2), lean=-0.15, arm=2.6, arm_b=2.6, mouth=1.0, glow=1.0)),
}


# ------------------------------------------------------------ ŞAHMERAN ANA
SH_SCALE = Mat(ramp(108, 0.55, 0.5, spread=0.45), spec=0.6, name='yılan pulu')
SH_SCALE_D = Mat(ramp(118, 0.6, 0.32, spread=0.4), name='yılan pulu gölge')
SH_BELLY = Mat(ramp(54, 0.5, 0.78, spread=0.4), name='yılan karnı')
SH_SKIN = Mat(ramp(30, 0.35, 0.82, spread=0.4), name='şahmeran teni')
SH_GOLD = M['gold']
SH_GEM = Mat(ramp(150, 0.8, 0.95, spread=0.25), emissive=0.9, outline='#0b4a2a', name='zümrüt')
SH_HAIR = Mat(ramp(110, 0.5, 0.25, spread=0.3), name='yılan saçı')


def draw_sahmeran(c, p):
    """Şahmeran Ana: yılanların kraliçesi. Belden yukarısı taçlı kadın (altın göğüslük, zümrüt taç), belden aşağısı
    halkalanmış dev yılan gövdesi; saçları yılan başlarıyla biter, arkasında kobra yelpazesi."""
    c = _Z(c)
    bob, lean = p.get('bob', 0.0), p.get('lean', 0.0)
    wave = p.get('wave', 0.0)
    # kuyruk halkaları (arkadan öne)
    pts = []
    for i in range(14):
        tt = i / 13
        x = -70 + tt * 80 + math.sin(tt * 6 + wave) * 6
        y = -10 - 6 * math.sin(tt * math.pi) + math.cos(tt * 9 + wave) * 2
        pts.append((x, y))
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        r = 6 + 9 * (i / 13)
        c.capsule(a, b, r, r + 0.6, SH_SCALE, z=-4 + i * 0.2, paint=[(lambda lu, lv, px, py: lv > 0.45, SH_BELLY), (lambda lu, lv, px, py: (np.floor(px * 0.35 + py * 0.35) % 3 == 0) & (lv < 0.2), SH_SCALE_D)])
    c.poly([(pts[0][0] - 2, pts[0][1] - 3), (pts[0][0] - 14, pts[0][1] - 10 + math.sin(wave) * 4), (pts[0][0] - 2, pts[0][1] + 3)], SH_SCALE_D, z=-5, bevel=1, height=1)
    base = (14 + math.sin(wave) * 2, -22 + bob)
    # beden bağlantısı: yılan gövdesi yukarı kalkar
    up = chain(pts[-1], 4, 9, -math.pi / 2 + 0.15 + lean, -0.05, wave, 0.15)
    for i, (a, b) in enumerate(zip(up, up[1:])):
        c.capsule(a, b, 15 - i * 0.8, 14 - i * 0.8, SH_SCALE, z=2 + i * 0.3, paint=[(lambda lu, lv, px, py: lv > 0.4, SH_BELLY)])
    waist = up[-1]
    # kobra yelpazesi (arkada)
    hood = (waist[0] - 2, waist[1] - 34)
    c.ellipse(hood, 30, 34, SH_SCALE_D, z=-10, depth=0.12, paint=[(lambda lu, lv, px, py: (np.abs(lu) < 0.35) & (lv > -0.6), SH_BELLY)])
    for k in range(4):
        c.ellipse((hood[0] + (k - 1.5) * 12, hood[1] - 6 + abs(k - 1.5) * 6), 3, 4, SH_GEM, z=-9)
    # kadın gövdesi
    chest = (waist[0] + 2 + lean * 10, waist[1] - 24)
    c.ellipse(lerp2(waist, chest, 0.5), 13, 18, SH_SKIN, z=6)
    c.ellipse((chest[0] + 1, chest[1] + 4), 12, 7, SH_GOLD, z=7, paint=[(lambda lu, lv, px, py: np.abs(lu) < 0.15, SH_GEM)])
    c.capsule((waist[0] - 13, waist[1] - 2), (waist[0] + 13, waist[1] - 2), 3, 3, SH_GOLD, z=8)
    # kollar
    for side, key, z in ((-1, 'arm_b', -2), (1, 'arm', 12)):
        a = p.get(key, 0.4)
        sh = (chest[0] + side * 10, chest[1] + 2)
        e, h = fk_arm(sh, a, 0.4, 16, 15)
        c.capsule(sh, e, 4.5, 4, SH_SKIN, z=z)
        c.capsule(e, h, 4, 3.5, SH_SKIN, z=z)
        c.capsule(lerp2(e, h, 0.7), lerp2(e, h, 0.9), 4.5, 4.5, SH_GOLD, z=z + 0.5)
        if side == 1:
            c.ellipse(h, 4, 4, SH_SKIN, z=z + 1)
            if p.get('orb', 0.0) > 0:
                c.ellipse((h[0] + 4, h[1] - 4), 6 * p['orb'], 6 * p['orb'], SH_GEM, z=z + 2)
    # baş, yılan saçlar, taç
    head = (chest[0] + 4, chest[1] - 18 + p.get('hy', 0.0))
    hx, hy = head
    for k in range(5):
        st = chain((hx - 4, hy - 2), 5, 5, math.pi * (0.75 + k * 0.1) + math.sin(wave + k) * 0.2, 0.12, wave + k, 0.3)
        for i, (a, b) in enumerate(zip(st, st[1:])):
            c.capsule(a, b, 3 - i * 0.35, 2.6 - i * 0.35, SH_HAIR, z=4 + k * 0.1)
        c.ellipse(st[-1], 3.2, 2.2, SH_SCALE, z=5 + k * 0.1)
        c.dot((st[-1][0] + 1, st[-1][1] - 1), M['eye_red'], z=30)
    c.ellipse(head, 9, 10, SH_SKIN, z=34)
    c.capsule((hx + 2, hy - 1), (hx + 6, hy - 1), 1.0, 0.9, M['black'], z=36)
    c.dot((hx + 5, hy - 1), SH_GEM, z=50, size=2)
    c.capsule((hx + 3, hy + 5), (hx + 7, hy + 5 + 2 * p.get('mouth', 0.0)), 1.0, 0.8, M['red_paint'], z=36)
    for k in range(5):
        x0 = hx - 8 + k * 4
        hh = 7 if k == 2 else 5
        c.poly([(x0 - 2, hy - 8), (x0 + 2, hy - 8), (x0, hy - 8 - hh)], SH_GOLD, z=37, bevel=0.7, height=0.8)
    c.capsule((hx - 9, hy - 8), (hx + 9, hy - 8), 1.6, 1.6, SH_GOLD, z=37.5)
    c.dot((hx, hy - 12), SH_GEM, z=50, size=3)
    return {'hand': (chest[0] + 22, chest[1] - 2), 'mouth': (hx + 6, hy + 5), 'tail': pts[0]}


SH_ANIMS = {
    'idle': (8, lambda t: dict(bob=1.5 * math.sin(t * math.tau), wave=t * math.tau, arm=0.5, arm_b=0.4, lean=0.05 * math.sin(t * math.tau))),
    'walk': (8, lambda t: dict(bob=1.0 * math.sin(t * math.tau * 2), wave=t * math.tau * 2, arm=0.6, arm_b=0.6, lean=0.15)),
    'windup': (4, lambda t: _k(t, [dict(bob=0.0, wave=0.0, arm=0.6, lean=0.0), dict(bob=-4.0, wave=1.2, arm=2.6, arm_b=2.0, lean=-0.25, mouth=0.6, hy=-3.0)])),
    'strike': (4, lambda t: _k(t, [dict(bob=-2.0, wave=2.0, arm=1.6, lean=0.4, mouth=1.0), dict(bob=2.0, wave=3.0, arm=1.2, lean=0.3, mouth=0.5)])),
    'slam': (3, lambda t: _k(t, [dict(bob=-8.0, wave=0.5, arm=2.8, arm_b=2.8, lean=-0.2), dict(bob=4.0, wave=2.5, arm=0.8, arm_b=0.8, lean=0.35)])),
    'cast': (3, lambda t: _k(t, [dict(bob=0.0, wave=0.5, arm=1.6, orb=0.5), dict(bob=-2.0, wave=1.5, arm=2.0, orb=1.0, mouth=0.8)])),
    'hurt': (2, lambda t: _k(t, [dict(bob=2.0, wave=1.0, arm=0.2, lean=-0.3, mouth=0.8), dict(bob=1.0, wave=1.5, arm=0.3, lean=-0.15)])),
    'rage': (3, lambda t: dict(bob=2 * math.sin(t * math.tau * 2), wave=t * math.tau * 3, arm=2.8, arm_b=2.8, mouth=1.0, lean=-0.1)),
}


# ------------------------------------------------------------ YELBEGEN (üç başlı buz devi)
YB_ICE = Mat(ramp(198, 0.35, 0.9, spread=0.35), spec=1.0, name='buz derisi')
YB_ICE_D = Mat(ramp(205, 0.45, 0.62, spread=0.35), name='buz gölge')
YB_FUR = Mat(ramp(210, 0.08, 0.86, spread=0.35), name='ak post')
YB_CRYS = Mat(ramp(185, 0.6, 1.0, spread=0.25), emissive=0.8, outline='#0b3a52', name='buz kristali')
YB_EYE = Mat(ramp(190, 0.7, 1.0, spread=0.2), emissive=1.0, outline='#0b3a52', name='ayaz gözü')


def draw_yelbegen(c, p):
    """Yelbegen: Kaf Dağı'nın üç başlı devi. Buz kabuklu omuzlar, ak post pelerin, sırtında buz kristalleri;
    üç baş farklı yönlere bakar (heads: üç başın açı sapmaları), elinde buzdan dev mızrak."""
    c = _Z(c)
    bob, lean = p.get('bob', 0.0), p.get('lean', 0.0)
    legs = p.get('legs', 0.0)
    hip = (0.0, -64 + bob)
    neck = (hip[0] + math.sin(lean) * 48 + 4, hip[1] - math.cos(lean) * 48)
    for side, z in ((-1, -6), (1, 8)):
        a = 0.3 * legs * side
        k, f = fk_leg((hip[0] + side * 9, hip[1]), a, 0.2 + 0.3 * max(0, -legs * side), 32, 32)
        mat = YB_ICE if z > 0 else YB_ICE_D
        c.capsule((hip[0] + side * 9, hip[1]), k, 10, 8.5, mat, z=z)
        c.capsule(k, f, 8.5, 7, mat, z=z)
        c.ellipse((f[0] + 5, f[1] - 3), 9, 5, YB_FUR, z=z + 0.5)
    # pelerin
    c.poly([(neck[0] - 18, neck[1] + 6), (neck[0] + 6, neck[1] + 4), (hip[0] + 6, hip[1] + 30), (hip[0] - 34, hip[1] + 26)], YB_FUR, z=-12, bevel=3, height=2,
           paint=[(lambda lu, lv, px, py: np.floor(px * 0.25 - py * 0.1) % 3 == 0, Mat(ramp(210, 0.12, 0.7)))])
    ab = p.get('arm_b', 0.3)
    e, h = fk_arm((neck[0] - 14, neck[1] + 12), ab, 0.5, 28, 26)
    c.capsule((neck[0] - 14, neck[1] + 12), e, 9, 7.5, YB_ICE_D, z=-8)
    c.capsule(e, h, 7.5, 6.5, YB_ICE_D, z=-8)
    mid = lerp2(hip, neck, 0.5)
    c.ellipse(mid, 22, 30, YB_ICE, z=3, rot=lean, depth=0.5, paint=[(lambda lu, lv, px, py: (np.abs(np.sin(px * 0.35 + py * 0.2)) < 0.15), YB_ICE_D)])
    # omuz buz kabukları + kristaller
    for side in (-1, 1):
        sp = (neck[0] + side * 16, neck[1] + 8)
        c.ellipse(sp, 12, 9, YB_ICE_D, z=8)
        for k in range(3):
            c.poly([(sp[0] - 4 + k * 4, sp[1] - 4), (sp[0] + k * 4, sp[1] - 4), (sp[0] - 2 + k * 4 + side * 2, sp[1] - 16 - k * 3)], YB_CRYS, z=9, bevel=1, height=1.2)
    # üç baş
    hd = p.get('heads', (0.0, 0.0, 0.0))
    for k, (ox, oy, z) in enumerate(((-14, 4, 30), (14, 2, 31), (2, -6, 33))):
        hx, hy = neck[0] + ox, neck[1] - 10 + oy + p.get('hy', 0.0)
        c.capsule((neck[0] + ox * 0.4, neck[1] + 4), (hx, hy), 7, 6, YB_ICE, z=z - 1)
        c.ellipse((hx, hy), 9, 8.5, YB_ICE, z=z)
        ang = hd[k] if k < len(hd) else 0.0
        mx, my = hx + math.cos(ang) * 9, hy + 4 + math.sin(ang) * 3
        c.capsule((hx + 2, hy + 2), (mx + 3, my), 5, 3, YB_ICE_D, z=z + 0.5)
        c.dot((hx + 3, hy - 2), YB_EYE, z=30, size=2)
        c.dot((hx + 6, hy - 2), YB_EYE, z=30, size=2)
        for j in range(2):
            c.poly([(hx - 6 + j * 8, hy - 6), (hx - 2 + j * 8, hy - 6), (hx - 6 + j * 8, hy - 16)], YB_CRYS, z=z + 1, bevel=0.8, height=1)
        if p.get('mouth', 0.0) > 0.2:
            c.ellipse((mx + 2, my + 1), 3, 1 + 2 * p['mouth'], M['black'], z=z + 1)
    # ön kol + buz mızrağı
    a1 = p.get('arm', 0.4)
    e2, h2 = fk_arm((neck[0] + 14, neck[1] + 12), a1, 0.35, 28, 26)
    c.capsule((neck[0] + 14, neck[1] + 12), e2, 10, 8, YB_ICE, z=58)
    c.capsule(e2, h2, 8, 7, YB_ICE, z=58)
    sa = a1 + 0.35 + p.get('spear', 0.0)
    tip = (h2[0] + math.sin(sa) * 70, h2[1] + math.cos(sa) * 70)
    tail = (h2[0] - math.sin(sa) * 24, h2[1] - math.cos(sa) * 24)
    c.capsule(tail, tip, 3, 2.5, YB_ICE_D, z=57)
    c.poly([(tip[0] - 4, tip[1] - 4), (tip[0] + 4, tip[1] + 4), (tip[0] + math.sin(sa) * 18, tip[1] + math.cos(sa) * 18)], YB_CRYS, z=57.5, bevel=1.4, height=1.6)
    c.ellipse(h2, 8, 7, YB_ICE, z=59)
    return {'hand': h2, 'mouth': (neck[0] + 6, neck[1] - 10), 'spear': tip}


YB_ANIMS = {
    'idle': (8, lambda t: dict(bob=1.5 * math.sin(t * math.tau), lean=0.05, arm=0.5, arm_b=0.3, heads=(0.2 * math.sin(t * math.tau), -0.2 * math.sin(t * math.tau + 1), 0.0))),
    'walk': (8, lambda t: dict(_walk(t, 0.55, 3.0), lean=0.12, heads=(0.1, -0.1, 0.0))),
    'windup': (4, lambda t: _k(t, [dict(bob=1.0, arm=0.6, spear=0.0), dict(bob=3.0, lean=-0.2, arm=3.0, spear=0.6, mouth=0.5, heads=(-0.4, 0.4, -0.2))])),
    'strike': (4, lambda t: _k(t, [dict(bob=-2.0, lean=0.35, arm=1.6, spear=-0.2, mouth=1.0), dict(bob=3.0, lean=0.45, arm=1.2, spear=-0.4, mouth=0.4)])),
    'slam': (3, lambda t: _k(t, [dict(bob=-6.0, lean=0.1, arm=3.0, arm_b=3.0), dict(bob=6.0, lean=0.45, arm=0.5, arm_b=0.5, mouth=0.8)])),
    'cast': (3, lambda t: _k(t, [dict(bob=0.0, arm=0.6, arm_b=2.2, mouth=0.3, heads=(-0.5, 0.5, -0.6)), dict(bob=-2.0, arm=0.6, arm_b=2.6, mouth=1.0, heads=(-0.8, 0.8, -1.0))])),
    'hurt': (2, lambda t: _k(t, [dict(bob=2.0, lean=-0.25, arm=0.6, mouth=0.7), dict(bob=1.0, lean=-0.1, arm=0.4)])),
    'rage': (3, lambda t: dict(bob=2 * math.sin(t * math.tau * 2), lean=-0.15, arm=2.6, arm_b=2.6, mouth=1.0, heads=(-0.8, 0.8, -1.2))),
}


# ------------------------------------------------------------ ERLİK HAN
EH_ROBE = Mat(ramp(270, 0.4, 0.18, spread=0.4), name='kara cübbe')
EH_ROBE_D = Mat(ramp(280, 0.45, 0.1, spread=0.35), name='kara cübbe gölge')
EH_SKIN = Mat(ramp(350, 0.3, 0.35, spread=0.4), name='erlik derisi')
EH_GOLD = Mat(ramp(30, 0.7, 0.6), spec=0.8, name='kararmış altın')
EH_FIRE = Mat(ramp(22, 0.95, 1.0, spread=0.3), emissive=1.0, outline='#5a1004', name='tamu ateşi')
EH_HORN = Mat(ramp(30, 0.2, 0.75, spread=0.4), name='boynuz')


def draw_erlik(c, p):
    """Erlik Han: yeraltının hükümdarı. Koç boynuzlu taç, alev sakal, kara cübbe (altın şeritli), göğsünde kor çekirdek,
    elinde topuzlu demir asa; arkasında yanan ateş halesi."""
    c = _Z(c)
    bob, lean = p.get('bob', 0.0), p.get('lean', 0.0)
    legs = p.get('legs', 0.0)
    fl = p.get('flame', 0.0)
    hip = (0.0, -62 + bob)
    neck = (hip[0] + math.sin(lean) * 50 + 4, hip[1] - math.cos(lean) * 50)
    # ateş halesi
    for k in range(9):
        a = math.pi * (0.95 + k * 0.14)
        r = 40 + 6 * math.sin(fl + k)
        bx, by = neck[0] - 6 + math.cos(a) * 22, neck[1] - 8 + math.sin(a) * 22
        c.poly([(bx - 5, by + 3), (bx + 5, by + 3), (bx + math.cos(a) * (r - 22) * 0.8, by + math.sin(a) * (r - 22) * 0.8 - 6)], EH_FIRE, z=-14, bevel=1.5, height=1)
    # cübbe etek (bacakları örter)
    sw = legs * 6
    c.poly([(hip[0] - 18, hip[1] - 10), (hip[0] + 18, hip[1] - 10), (hip[0] + 28 + sw, 0), (hip[0] - 26 + sw * 0.5, 0)], EH_ROBE, z=0, bevel=3, height=2,
           paint=[(lambda lu, lv, px, py: (np.abs(px - (hip[0] + 2)) < 2.2), EH_GOLD), (lambda lu, lv, px, py: py > -5, EH_GOLD)])
    for side in (-1, 1):
        c.ellipse((hip[0] + side * 9 + sw * 0.5, -3), 7, 4, M['black'], z=1)
    ab = p.get('arm_b', 0.3)
    e, h = fk_arm((neck[0] - 14, neck[1] + 12), ab, 0.5, 26, 24)
    c.capsule((neck[0] - 14, neck[1] + 12), e, 9, 8, EH_ROBE_D, z=-8)
    c.capsule(e, h, 8, 7, EH_ROBE_D, z=-8)
    c.ellipse(h, 6, 6, EH_SKIN, z=-7)
    if p.get('orb', 0.0) > 0:
        c.ellipse((h[0] - 4, h[1] - 6), 8 * p['orb'], 8 * p['orb'], EH_FIRE, z=-6)
    mid = lerp2(hip, neck, 0.5)
    c.ellipse(mid, 22, 30, EH_ROBE, z=3, rot=lean, depth=0.5, paint=[(lambda lu, lv, px, py: np.abs(lu) < 0.12, EH_GOLD)])
    c.ellipse((mid[0] + 2, mid[1] - 6), 6, 6, EH_FIRE, z=6)  # kor çekirdek
    for side in (-1, 1):
        c.ellipse((neck[0] + side * 16, neck[1] + 8), 12, 8, EH_GOLD, z=8)
        c.poly([(neck[0] + side * 12, neck[1] + 2), (neck[0] + side * 22, neck[1] + 2), (neck[0] + side * 20, neck[1] - 10)], EH_HORN, z=8.5, bevel=1, height=1)
    # baş: alev sakal, koç boynuzları, taç
    head = (neck[0] + 6, neck[1] - 10 + p.get('hy', 0.0))
    hx, hy = head
    for k in range(5):
        bx = hx - 4 + k * 3
        c.poly([(bx - 2, hy + 6), (bx + 2, hy + 6), (bx + 1 + math.sin(fl + k) * 2, hy + 18 + (k % 2) * 4)], EH_FIRE, z=34, bevel=1, height=0.8)
    c.ellipse(head, 10, 11, EH_SKIN, z=35)
    c.capsule((hx + 1, hy - 2), (hx + 8, hy - 2), 1.4, 1.2, EH_FIRE, z=37)
    c.capsule((hx - 2, hy - 6), (hx + 9, hy - 5), 1.4, 1.2, M['black'], z=37)
    if p.get('mouth', 0.0) > 0.2:
        c.ellipse((hx + 5, hy + 5), 4, 1 + 2.5 * p['mouth'], EH_FIRE, z=37)
    for side in (-1, 1):
        hp = chain((hx + side * 7, hy - 8), 5, 6, -math.pi / 2 + side * 1.2, side * 0.45, 0, 0)
        for i, (a, b) in enumerate(zip(hp, hp[1:])):
            c.capsule(a, b, 4 - i * 0.6, 3.5 - i * 0.6, EH_HORN, z=36 if side > 0 else 9)
    for k in range(3):
        c.poly([(hx - 6 + k * 6, hy - 10), (hx - 2 + k * 6, hy - 10), (hx - 4 + k * 6, hy - 20)], EH_GOLD, z=38, bevel=0.8, height=0.8)
    c.capsule((hx - 7, hy - 10), (hx + 9, hy - 10), 1.6, 1.6, EH_GOLD, z=38.5)
    # ön kol + topuzlu asa
    a1 = p.get('arm', 0.4)
    e2, h2 = fk_arm((neck[0] + 14, neck[1] + 12), a1, 0.35, 26, 24)
    c.capsule((neck[0] + 14, neck[1] + 12), e2, 9, 8, EH_ROBE, z=58)
    c.capsule(e2, h2, 8, 7, EH_ROBE, z=58)
    ma = a1 + 0.35 + p.get('mace', 0.0)
    tip = (h2[0] + math.sin(ma) * 58, h2[1] + math.cos(ma) * 58)
    tail = (h2[0] - math.sin(ma) * 18, h2[1] - math.cos(ma) * 18)
    c.capsule(tail, tip, 2.5, 2.5, M['iron'], z=57)
    c.ellipse(tip, 9, 9, M['iron'], z=57.5)
    for k in range(8):
        a = k / 8 * math.tau
        c.poly([(tip[0] + math.cos(a) * 7 - 1.5, tip[1] + math.sin(a) * 7), (tip[0] + math.cos(a) * 7 + 1.5, tip[1] + math.sin(a) * 7), (tip[0] + math.cos(a) * 13, tip[1] + math.sin(a) * 13)],
               M['iron'], z=57.6, bevel=0.6, height=0.8)
    c.ellipse(tip, 4, 4, EH_FIRE, z=58)
    c.ellipse(h2, 6.5, 6.5, EH_SKIN, z=59)
    return {'hand': h2, 'mouth': (hx + 5, hy + 5), 'mace': tip, 'orb': (h[0] - 4, h[1] - 6)}


EH_ANIMS = {
    'idle': (8, lambda t: dict(bob=1.5 * math.sin(t * math.tau), flame=t * math.tau, arm=0.5, arm_b=0.3, lean=0.04)),
    'walk': (8, lambda t: dict(bob=-abs(math.sin(t * math.tau)) * 2 + 1, legs=math.sin(t * math.tau), flame=t * math.tau, arm=0.5, arm_b=0.4, lean=0.1)),
    'windup': (4, lambda t: _k(t, [dict(bob=1.0, arm=0.6, flame=0.0), dict(bob=3.0, lean=-0.2, arm=3.0, mace=0.4, mouth=0.5, flame=2.0)])),
    'strike': (4, lambda t: _k(t, [dict(bob=-2.0, lean=0.35, arm=1.6, mace=-0.2, mouth=1.0, flame=3.0), dict(bob=4.0, lean=0.45, arm=0.6, mace=-0.4, mouth=0.4, flame=4.0)])),
    'slam': (3, lambda t: _k(t, [dict(bob=-6.0, lean=0.1, arm=3.0, arm_b=3.0, flame=1.0), dict(bob=6.0, lean=0.45, arm=0.4, arm_b=0.5, mouth=0.8, flame=3.0)])),
    'cast': (3, lambda t: _k(t, [dict(bob=0.0, arm=0.6, arm_b=2.0, orb=0.5, flame=1.0), dict(bob=-2.0, arm=0.6, arm_b=2.6, orb=1.0, mouth=1.0, flame=2.0)])),
    'hurt': (2, lambda t: _k(t, [dict(bob=2.0, lean=-0.25, arm=0.6, mouth=0.7), dict(bob=1.0, lean=-0.1, arm=0.4)])),
    'rage': (3, lambda t: dict(bob=2 * math.sin(t * math.tau * 2), lean=-0.15, arm=2.6, arm_b=2.6, mouth=1.0, flame=t * math.tau * 3, orb=1.0)),
}

CREATURES3 = {
    'tepegoz': (draw_tepegoz, TG_ANIMS, (200, 200), (96, 194)),
    'sahmeran_ana': (draw_sahmeran, SH_ANIMS, (200, 176), (100, 170)),
    'yelbegen': (draw_yelbegen, YB_ANIMS, (200, 208), (96, 202)),
    'erlik_han': (draw_erlik, EH_ANIMS, (200, 200), (96, 194)),
}
