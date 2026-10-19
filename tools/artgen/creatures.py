"""Ötüken yaratıkları (v2): Erlik Tazısı, Çor Ruhu, Kara İye, Balbal, Kara Kam, Gulyabani.

Hepsi yüz sağa bakar, ayak merkezi (0,0), y aşağı pozitif. Her yaratığın pozları ve animasyonları
sözlüklerde (ad: (kare sayısı, poz işlevi)); render_creature() Godot'ya aktarılacak kareyi üretir.
Tasarım ilkesi (Dead Cells / Bengü ile uyumlu): koyu, desatüre ay ışıklı ortamda okunan siluet; yaratık
başına sınırlı palet (2-3 ana renk + tek bir parlayan vurgu), büyük renk blokları, 3 tonlu cel gölge;
gözler/runalar/fener `emissive` malzemeyle _e katmanına düşer. Kimlikler (kara_boru, cor...) oyun kodu
için korunur; animasyon adları, kare sayıları ve çapalar (mouth, hand) değişmez.
"""
import math
import numpy as np
from raster import Canvas, Mat, ramp
from materials import M
from rig import fk_leg, fk_arm, lerp2, chain, Xf
import bozkurt
import wolfkit as wk
from volume import VCanvas, soft

# v13: hacimli gölgelendirme kullanan kurt sprite'ları (bkz. volume.py)
VOLUME = {'kara_boru', 'kara_boru_han', 'bengu_kurt'}


# ------------------------------------------------------------ ortak yardımcılar
class Sq:
    """Ezilme/uzama: noktaları ayak merkezine göre ölçekler (sx, sy) ve dy kadar kaydırır."""
    def __init__(self, c, sx=1.0, sy=1.0, dy=0.0, zk=1.0):
        self.c, self.sx, self.sy, self.dy = c, sx, sy, dy
        self.k = (sx + sy) * 0.5
        self.zk = zk  # büyütülmüş parçaların kabarıklığı küçük ayrıntıları örtmesin diye z de ölçeklenebilir

    def P(self, p):
        return (p[0] * self.sx, p[1] * self.sy + self.dy)

    def _z(self, kw):
        if self.zk != 1.0 and 'z' in kw:
            kw['z'] = kw['z'] * self.zk
        return kw

    def capsule(self, p0, p1, r0, r1, mat, **kw):
        self.c.capsule(self.P(p0), self.P(p1), r0 * self.k, r1 * self.k, mat, **self._z(kw))

    def ellipse(self, c_, rx, ry, mat, **kw):
        self.c.ellipse(self.P(c_), rx * self.sx, ry * self.sy, mat, **self._z(kw))

    def poly(self, pts, mat, **kw):
        if self.zk != 1.0:
            kw.setdefault('bevel', 1.6)
            kw.setdefault('height', 1.5)
            kw['bevel'] *= self.k
            kw['height'] *= self.k
        self.c.poly([self.P(q) for q in pts], mat, **self._z(kw))

    def dot(self, p, mat, **kw):
        if self.zk != 1.0:
            # büyütülmüş tek piksel: küçük elips (dişler, perçinler)
            self.c.ellipse(self.P(p), 0.5 * self.k, 0.5 * self.k, mat, **self._z(kw))
            return
        self.c.dot(self.P(p), mat, **kw)


def strand(c, pts, r0, r1, mat, z, tip=None, tip_from=None):
    """Zincir noktalarını incelen kapsüllerle çizer (saç, paçavra, yele). tip: son parçaların malzemesi."""
    n = len(pts) - 1
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        ra = r0 + (r1 - r0) * i / n
        rb = r0 + (r1 - r0) * (i + 1) / n
        m = tip if (tip is not None and i >= (tip_from if tip_from is not None else n - 1)) else mat
        c.capsule(a, b, ra, rb, m, z=z)


def antler(c, base, a0, L, mat, z, r0=1.5, curve=0.25, tines=(1, 2, 3), tine_len=0.38, n=4):
    """Dallanan boynuz: ana gövde a0 açısıyla (cos/sin) çıkar, her düğümden öne-yukarı çatal verir."""
    pts = [base]
    x, y = base
    seg = L / n
    for i in range(n):
        a = a0 + curve * i
        x += math.cos(a) * seg
        y += math.sin(a) * seg
        pts.append((x, y))
    for i, (p0, p1) in enumerate(zip(pts, pts[1:])):
        c.capsule(p0, p1, r0 * (1 - i / n * 0.6), r0 * (1 - (i + 1) / n * 0.6), mat, z=z)
    for i in tines:
        if i < len(pts) - 1:
            a = a0 + curve * i + 0.95
            q = pts[i]
            tl = L * tine_len * (1 - i * 0.12)
            mid = (q[0] + math.cos(a) * tl * 0.5, q[1] + math.sin(a) * tl * 0.5)
            tip = (mid[0] + math.cos(a - 0.4) * tl * 0.5, mid[1] + math.sin(a - 0.4) * tl * 0.5)
            c.capsule(q, mid, r0 * 0.62, r0 * 0.45, mat, z=z)
            c.capsule(mid, tip, r0 * 0.45, 0.45, mat, z=z)
    return pts


def keyed(t, frames):
    return frames[min(len(frames) - 1, int(t * len(frames) + 1e-6))]


# ------------------------------------------------------------ ERLİK TAZISI (kimlik: kara_boru)
HOUND = Mat(ramp(266, 0.24, 0.31, spread=0.5), name='tazı postu')
HOUND_D = Mat(ramp(270, 0.30, 0.205, spread=0.45), name='tazı sırtı')
HOUND_RIB = Mat(ramp(258, 0.14, 0.46, spread=0.4), name='kaburga çıkıntısı')
SMOKE = Mat(ramp(262, 0.16, 0.24, spread=0.4), name='duman yele')
BONE_D = Mat(ramp(34, 0.22, 0.68, spread=0.4), name='eski kemik')
EMBER = Mat(ramp(26, 0.95, 1.0, spread=0.2), emissive=1.0, outline='#3a0c02', name='kor')
EMBER_D = Mat(ramp(12, 0.90, 0.88, spread=0.25), emissive=0.7, outline='#2a0602', name='sönük kor')
RUST = Mat(ramp(18, 0.34, 0.52, spread=0.45), spec=0.4, name='paslı zincir')
CLAW_H = Mat(ramp(30, 0.20, 0.75, spread=0.4), name='tazı tırnağı')
soft(HOUND, 0.55, 0.45, 1.0); soft(HOUND_D, 0.6, 0.5, 1.0); soft(SMOKE, 0.6, 0.5, 0.7)


def draw_hound(c, p):
    """Erlik Tazısı (v13): yeraltının sıska ama güçlü kara tazısı. Derin göğüs, içe çekik bel, kaslı omuz ve
    kalça; üç eklemli bacaklar (dirsek geride, topuk geride), geniş pençeler. Kemik alın zırhı, sırtta omur
    plakaları, çıkık kaburgalar, dumanlı yele (uçları kor), kırık zincirli tasma; gözleri ve ağzı kor gibi yanar.
    Uzak bacaklar koyu postla ve gövdenin arkasında; kulak, yele ve kuyruk gövdeden gecikmeli salınır."""
    bob, tilt, jaw = p.get('bob', 0.0), p.get('tilt', 0.0), p.get('jaw', 0.0)
    ph = p.get('ph', 0.0)
    # koşuda ezilme/uzama: yere basışta gövde hafif basılır, uçuşta uzar (ayak merkezine göre)
    sq = p.get('sq', 0.0)
    sqx, sqy = 1.0 + 0.06 * sq, 1.0 - 0.07 * sq
    if sq:
        c = Sq(c, sqx, sqy, 0.0)
    hipp = (-10.0, -19.0 + bob - tilt * 6)
    shp = (8.5, -20.5 + bob + tilt * 6)
    back_dark = lambda lu, lv, px, py: lv < -0.55
    belly_dark = lambda lu, lv, px, py: lv > 0.6

    def legs(near):
        z = 8 if near else -8
        mat = HOUND if near else HOUND_D
        shm = HOUND_D if near else SMOKE
        hip_j = (hipp[0] + 0.5, hipp[1] + 0.5)
        sh_j = (shp[0] + 0.8, shp[1] + 1.5)
        a_h = p['hf'] if near else p['hb']
        a_f = p['ff'] if near else p['fb']
        k, hk, f = wk.hind_leg(c, hip_j, a_h, 1.0, mat, z, thigh_r=4.4 if near else 3.8, sh_mat=shm, claw=CLAW_H)
        # uyluk arkası tüy fırçası (pantolon)
        wk.tufts(c, [wk.lerp(hip_j, k, 0.35), wk.lerp(hip_j, k, 0.7)], shm, z - 0.4, 3.0, math.pi * 0.72, jitter=0.25)
        e, w, f2 = wk.front_leg(c, sh_j, a_f, 1.0, mat, z, sh_mat=shm, claw=CLAW_H)
        wk.tufts(c, [wk.lerp(e, w, 0.15)], shm, z - 0.2, 2.4, math.pi * 0.85, jitter=0.2)
        if near:
            c.ellipse(k, 1.1, 1.1, BONE_D, z=z + 4.5)   # dizde kemik çıkıntısı
        return f

    legs(False)
    # kuyruk: kalın kök, dumanlı uç, ucu kor; gövdeden gecikmeli kıvrılır
    tw = p.get('tw', 0.0)
    tl = chain((hipp[0] - 4.5, hipp[1] - 3.2), 5, 3.0, math.pi * 1.06 + tw, -0.2, ph - 0.9, 0.32)
    strand(c, tl, 2.6, 1.5, HOUND_D, -6)
    wk.tufts(c, tl[1:4], SMOKE, -6.2, 2.6, math.pi * 1.35 + tw, jitter=0.3)
    for k_, da in enumerate((-0.35, 0.0, 0.4)):
        tt = chain(tl[-1], 3, 2.2 - abs(da), math.pi * 1.1 + tw * 1.3 + da, -0.1, ph - 1.4 + k_, 0.45)
        strand(c, tt, 1.5, 0.5, SMOKE, -6 + k_ * 0.1, tip=EMBER_D if k_ == 1 else None)
    # ------------------------------------------------ gövde: kalça, içe çekik bel, derin göğüs, omuz tümseği
    ribs = lambda lu, lv, px, py: (np.floor((px - py * 0.35) * 0.5) % 2 == 0) & (lv > 0.0) & (lv < 0.7) & (lu < 0.3) & (lu > -0.75)
    c.ellipse((hipp[0], hipp[1] - 0.5), 6.0, 6.2, HOUND, z=0, paint=[(back_dark, HOUND_D)])
    c.capsule((hipp[0] + 1.5, hipp[1] - 2.4), (shp[0] - 3.0, shp[1] - 0.8), 4.3, 6.4, HOUND, z=1, paint=[(back_dark, HOUND_D), (belly_dark, HOUND_D)])
    c.ellipse((shp[0] + 0.5, shp[1] + 1.8), 7.4, 8.3, HOUND, z=2, rot=-0.18, paint=[(back_dark, HOUND_D), (ribs, HOUND_RIB)])
    c.ellipse((shp[0] - 2.5, shp[1] - 4.6), 6.0, 3.4, HOUND, z=2.5, paint=[(back_dark, HOUND_D)])
    # karın saçağı + göğüs tüyü
    bp = [wk.lerp((hipp[0] + 3.0, hipp[1] + 3.2), (shp[0] - 2.0, shp[1] + 8.6), t) for t in (0.15, 0.45, 0.75)]
    wk.tufts(c, bp, HOUND_D, 9.6, 2.6, math.pi * 0.7, jitter=0.25)
    wk.tufts(c, [(shp[0] + 6.5, shp[1] + 2.0), (shp[0] + 6.0, shp[1] + 5.5), (shp[0] + 4.0, shp[1] + 8.4)], HOUND, 9.7, 2.8, math.pi * 0.35, jitter=0.3)
    # leğen kemiği plakası
    hx0, hy0 = hipp
    c.poly([(hx0 - 4.0, hy0 - 4.6), (hx0 + 2.5, hy0 - 6.6), (hx0 + 3.8, hy0 - 4.4), (hx0 - 1.8, hy0 - 2.8)], BONE_D, z=10, bevel=1.0, height=1.2)
    # omur plakaları (sırt çizgisi boyunca, küçülen)
    for k_ in range(5):
        t = 0.16 + k_ * 0.17
        bx, by = wk.lerp(hipp, shp, t)
        r_t = 6.4 + 0.8 * t - 6.0 * t * (1 - t)
        by = by - r_t + 1.4
        h = 2.6 + (1.0 if k_ in (2, 3) else 0.0)
        c.poly([(bx - 1.7, by + 1.0), (bx + 1.2, by + 1.0), (bx - 0.3, by - h), (bx - 1.5, by - h + 1.0)], M['bone'], z=9, bevel=0.9, height=1.0)
    # dumanlı yele: boyun üstünden geriye taşar; uçları kor, gövdeden gecikmeli dalgalanır
    hy0_ = p.get('hy', 0.0)
    for k_ in range(6):
        t = k_ / 5
        bx, by = wk.lerp((shp[0] - 4, shp[1] - 6.6), (shp[0] + 7, shp[1] - 9.0 + hy0_), t)
        ang = math.pi * 1.15 + math.sin(ph - 0.8 + k_ * 1.3) * 0.16 + p.get('mane', 0.0)
        L = 6.5 + (k_ % 2) * 3.0 - t * 2.0
        st = chain((bx, by), 4, L / 4, ang, 0.16, ph - 0.8 + k_, 0.25)
        strand(c, st, 1.9, 0.5, SMOKE, 11 + k_ * 0.3, tip=EMBER_D if k_ % 2 else None)
    # ------------------------------------------------ boyun + baş
    head = (shp[0] + 9.5, shp[1] - 5.5 + hy0_)
    nb = (shp[0] + 2, shp[1] - 3)
    c.capsule(nb, head, 5.0, 3.9, HOUND, z=4, paint=[(back_dark, HOUND_D), (belly_dark, HOUND_D)])
    hx_, hy_ = head
    # boyun altı / yanak tüyü (ruff)
    wk.tufts(c, [(hx_ - 2.5, hy_ + 2.8), (hx_ - 4.2, hy_ + 1.2), (hx_ - 0.8, hy_ + 3.6)], HOUND, 12.5, 3.0, math.pi * 0.72, jitter=0.35)
    c.ellipse((hx_ - 0.3, hy_), 5.2, 4.5, HOUND, z=6, rot=-0.1)
    # kulaklar: uzak kulak koyu; kulaklar başın ardından gecikmeli oynar
    ear = p.get('ear', 0.0) + math.sin(ph - 1.2) * 0.12
    for (ox, mat, zz, ln) in ((-2.6, HOUND_D, 5.5, 6.4), (-0.6, HOUND, 13.0, 6.8)):
        e0 = (hx_ + ox, hy_ - 2.8)
        a = -math.pi * 0.5 - 0.75 - ear
        tip = (e0[0] + math.cos(a) * ln, e0[1] + math.sin(a) * ln)
        c.poly([(e0[0] - 2.0, e0[1] + 1.0), (e0[0] + 2.0, e0[1] + 0.2), tip], mat, z=zz, bevel=1.0, height=1.4)
        if mat is HOUND:
            c.poly([(e0[0] - 0.8, e0[1] + 0.4), (e0[0] + 0.9, e0[1]), wk.lerp(e0, tip, 0.65)], EMBER_D, z=zz + 0.4, bevel=0.5, height=0.3)
    # burun: kama; alt çene ayrı
    sn = (hx_ + 10.6, hy_ + 1.7)
    c.capsule((hx_ + 1.8, hy_ + 0.4), sn, 3.4, 1.7, HOUND, z=8, paint=[(belly_dark, HOUND_D)])
    jd = jaw * 3.6
    j1 = (hx_ + 9.4, hy_ + 3.8 + jd)
    c.poly([(hx_ + 2.5, hy_ + 2.0), (sn[0] - 0.5, sn[1] + 0.9), (j1[0], j1[1] - 0.6), (hx_ + 2.5, hy_ + 3.4 + jd * 0.4)], EMBER, z=7.9, bevel=0.5, height=0.3)
    c.capsule((hx_ + 1.6, hy_ + 3.0), j1, 1.9, 1.0, HOUND_D, z=7.5)
    if jaw > 0.15:
        for i in range(3):
            c.dot((hx_ + 4.6 + i * 1.8, hy_ + 2.4), M['bone'], z=30)
            c.dot((hx_ + 4.8 + i * 1.6, hy_ + 2.6 + jd * (0.55 + i * 0.12)), M['bone'], z=30)
    # kemik kafa zırhı: alın plakası + burun sırtı şeridi (başın hacmi okunsun diye dar)
    c.poly([(hx_ - 2.8, hy_ - 4.0), (hx_ + 2.8, hy_ - 4.6), (hx_ + 5.0, hy_ - 2.2), (hx_ + 0.4, hy_ - 1.5), (hx_ - 2.2, hy_ - 1.8)],
           M['bone'], z=14, bevel=1.0, height=1.2)
    c.poly([(hx_ + 3.4, hy_ - 3.0), (hx_ + 11.0, hy_ + 0.1), (hx_ + 10.6, hy_ + 1.1), (hx_ + 3.6, hy_ - 1.2)], M['bone'], z=14, bevel=0.7, height=0.8)
    c.ellipse((sn[0] + 0.4, sn[1] - 0.2), 1.15, 0.95, M['black'], z=24)
    c.ellipse((hx_ + 2.2, hy_ - 1.1), 1.9, 1.2, M['black'], z=24)
    c.capsule((hx_ + 1.4, hy_ - 1.1), (hx_ + 3.2, hy_ - 0.9), 0.75, 0.6, EMBER, z=28)
    # kırık zincirli tasma
    dx, dy = head[0] - nb[0], head[1] - nb[1]
    ln = math.hypot(dx, dy) + 1e-6
    nx, ny = -dy / ln, dx / ln
    cc = lerp2(nb, head, 0.5)
    a0 = (cc[0] - nx * 4.6, cc[1] - ny * 4.6); a1 = (cc[0] + nx * 4.6, cc[1] + ny * 4.6)
    c.capsule(a0, a1, 1.5, 1.5, RUST, z=16)
    for s_ in (-0.25, 0.25, 0.75):
        c.dot((cc[0] + nx * 4.6 * s_, cc[1] + ny * 4.6 * s_), M['iron'], z=22)
    sw = math.sin(ph - 0.6) * 0.35 + tilt * 1.5 + p.get('chain', 0.0)
    q = a1
    for i in range(3):
        nq = (q[0] + math.sin(sw - i * 0.15) * 2.0, q[1] + math.cos(sw - i * 0.15) * 2.0)
        if i % 2 == 0:
            c.ellipse(lerp2(q, nq, 0.5), 1.0, 1.3, M['iron'], z=17 + i)
        else:
            c.ellipse(lerp2(q, nq, 0.5), 0.8, 1.2, RUST, z=17 + i)
        q = nq
    legs(True)
    return {'mouth': ((hx_ + 10) * sqx, (hy_ + 2.6 + jd * 0.5) * sqy)}


def _hound_run(t):
    ph = t * math.tau
    s, s2 = math.sin(ph), math.sin(ph + 0.6)
    return dict(bob=-abs(math.cos(ph)) * 1.6 + 0.5, tilt=0.13 * math.sin(ph), hy=1.0 + 0.6 * math.sin(ph - 0.5),
                sq=1.0 - 2.0 * abs(math.cos(ph)), ear=0.25 + 0.15 * math.sin(ph - 1.0),
                hb=(0.95 * s, 0.9 - 0.4 * s), hf=(0.95 * s2, 0.9 - 0.4 * s2), mane=0.15,
                fb=(-0.95 * s + 0.1, 0.2 + 0.8 * max(0, s)), ff=(-0.95 * s2 + 0.1, 0.2 + 0.8 * max(0, s2)), tw=-0.25, ph=ph, jaw=0.3)


HOUND_ANIMS = {
    # bekleme: başı yere eğik, sinsi soluk; yele titrer
    'idle': (6, lambda t: dict(bob=0.6 * math.sin(t * 6.28), hy=1.6 + 0.5 * math.sin(t * 6.28 + 0.5), hb=(0.25, 0.9), hf=(0.1, 0.8),
                               fb=(-0.05, 0.1), ff=(0.08, 0.1), tw=0.12 * math.sin(t * 6.28), ph=t * 6.28, jaw=0.12 + 0.1 * max(0, math.sin(t * 6.28)))),
    'run': (6, _hound_run),
    # hazırlık: çömelir, hırlar; ikinci kare daha derin (tutulur)
    'windup': (2, lambda t: keyed(t, [
        dict(bob=3.0, tilt=-0.15, hb=(0.6, 1.5), hf=(0.5, 1.4), fb=(0.4, 1.1), ff=(0.5, 1.2), tw=0.4, jaw=0.6, hy=2.0, ph=1.0, mane=-0.1),
        dict(bob=4.2, tilt=-0.2, hb=(0.7, 1.75), hf=(0.6, 1.65), fb=(0.6, 1.35), ff=(0.7, 1.45), tw=0.55, jaw=0.95, hy=2.8, ph=2.0, mane=-0.2)])),
    # sıçrayış: gerilmiş gövde, açık çene; ikinci karede bacaklar toplanır
    'leap': (2, lambda t: keyed(t, [
        dict(bob=-2.2, tilt=-0.08, hb=(-1.1, 0.3), hf=(-1.0, 0.4), fb=(1.3, 0.2), ff=(1.4, 0.3), tw=-0.5, jaw=1.0, hy=0.0, ph=0.5, mane=0.35, chain=-1.2),
        dict(bob=-1.6, tilt=0.02, hb=(-0.7, 0.6), hf=(-0.6, 0.7), fb=(1.0, 0.6), ff=(1.1, 0.7), tw=-0.4, jaw=0.6, hy=0.5, ph=1.5, mane=0.3, chain=-0.8)])),
    'hurt': (2, lambda t: keyed(t, [
        dict(bob=1, tilt=0.22, hb=(0.3, 0.9), hf=(0.2, 0.8), fb=(-0.3, 0.3), ff=(-0.2, 0.2), tw=0.7, jaw=0.6, hy=-1.5, ph=0.3, mane=-0.3, chain=0.8),
        dict(bob=0.5, tilt=0.12, hb=(0.3, 0.9), hf=(0.15, 0.8), fb=(-0.15, 0.2), ff=(-0.1, 0.15), tw=0.4, jaw=0.3, hy=-0.5, ph=1.3, mane=-0.15, chain=0.4)])),
}


# ------------------------------------------------------------ ÇOR RUHU (kimlik: cor)
ROBE = Mat(ramp(282, 0.20, 0.40, spread=0.45), name='çor kefeni')
ROBE_D = Mat(ramp(276, 0.28, 0.24, spread=0.4), name='kefen gölgesi')
BRONZE = Mat(ramp(38, 0.62, 0.66), spec=0.6, name='tunç buhurdan')
PLAGUE = Mat(ramp(92, 0.85, 1.0, spread=0.2), emissive=1.0, outline='#1e3a06', name='salgın ışığı')
PLAGUE_D = Mat(ramp(100, 0.75, 0.78, spread=0.25), emissive=0.55, outline='#14280a', name='salgın dumanı')


def draw_cor(c, p):
    """Çor Ruhu: başlıklı, süzülen salgın hayaleti. Paçavra etek kuyrukları, iskelet eller, zincirde sallanan
    yeşil ışıklı buhurdan fener; sporlar fenerden saçılır ('mouth' çapası fenerin kendisidir)."""
    t = p.get('t', 0.0)
    ph = t * math.tau
    fl = math.sin(ph) * 2.0 + p.get('dy', 0.0)
    lean = p.get('lean', 0.0)
    cx, cy = 0.0, -29 + fl
    hx = cx + lean * 3
    # etek kuyrukları: üç ayrı yırtık şerit, arkaya ve aşağı süzülür
    for k, (sx, n, ph0, mat, a0) in enumerate(((-7, 5, 0.0, ROBE_D, 0.78), (-2.5, 6, 1.7, ROBE_D, 0.62), (2.5, 5, 3.1, ROBE, 0.52))):
        st = chain((cx + sx, cy + 7), n, 3.2, math.pi * a0 - lean * 0.4, 0.1, ph + ph0, 0.5)
        strand(c, st, 3.4, 0.6, mat, -6 + k)
    # arka kol: iskelet pençe
    ab = p.get('ab', (1.2, 0.6))
    shb = (hx - 3.5, cy - 6)
    e, h = fk_arm(shb, ab[0], ab[1], 5.5, 5.5)
    c.capsule(shb, e, 2.4, 2.8, ROBE_D, z=-8)
    c.capsule(e, h, 0.8, 0.7, M['bone'], z=-8)
    a = ab[0] + ab[1]
    for k in (-0.5, 0.0, 0.5):
        c.capsule(h, (h[0] + math.sin(a + k) * 3.4, h[1] + math.cos(a + k) * 3.4), 0.6, 0.4, M['bone'], z=-7.9)
    # kefen gövde: omuzdan aşağı daralan, yırtık uçlu
    folds = lambda lu, lv, px, py: (np.floor(px * 0.45 + np.sin(py * 0.35) * 0.8) % 3 == 0)
    c.poly([(hx - 7, cy - 9), (hx + 6, cy - 9), (cx + 8, cy + 2), (cx + 5.5, cy + 9), (cx + 3, cy + 6), (cx + 0.5, cy + 11), (cx - 2, cy + 6),
            (cx - 5, cy + 10), (cx - 7.5, cy + 4), (cx - 9, cy - 2)], ROBE, z=0, bevel=2.6, height=3, paint=[(folds, ROBE_D)])
    # başlık: yuvarlak tepe, sivri ucu arkaya ve aşağı sarkar
    hood = [(hx - 6.5, cy - 6), (hx - 9, cy - 13), (hx - 13, cy - 13 + fl * 0.3 - lean * 2), (hx - 8.5, cy - 19), (hx - 4, cy - 23.5),
            (hx + 1.5, cy - 24.5), (hx + 6, cy - 21.5), (hx + 8.5, cy - 15.5), (hx + 8, cy - 9), (hx + 5, cy - 5)]
    c.poly(hood, ROBE, z=4, bevel=2.6, height=3.5, paint=[(lambda lu, lv, px, py: (px < hx - 4) & (py > cy - 16), ROBE_D)])
    # başlık ağzı: açık kenar + karanlık + iki yeşil göz + kemik dişler
    c.ellipse((hx + 4.0, cy - 14), 4.2, 5.6, ROBE_D, z=11, rot=0.2)
    c.ellipse((hx + 4.6, cy - 13.6), 3.2, 4.6, M['black'], z=13, rot=0.2)
    att = p.get('att', 0.0)
    c.capsule((hx + 3.0, cy - 15.4), (hx + 3.9, cy - 15.2), 0.75, 0.7, PLAGUE, z=20)
    c.capsule((hx + 6.0, cy - 15.2), (hx + 6.5, cy - 15.4), 0.6, 0.6, PLAGUE, z=20)
    for i in range(3):
        c.dot((hx + 3.4 + i * 1.3, cy - 11.6 + att * 0.8), M['bone'], z=20)
    # buhurdan fener (ön kolun zincirinde)
    af = p.get('af', (0.9, 0.5))
    sh = (hx + 4.5, cy - 6)
    e, h = fk_arm(sh, af[0], af[1], 5.5, 5.5)
    sw = p.get('sw', math.sin(ph) * 0.35)
    L = 8.0
    cen = (h[0] + math.sin(sw) * L, h[1] + math.cos(sw) * L)
    cz = p.get('cz', 16)
    for i in range(1, 5):
        c.dot(lerp2(h, cen, i / 5.0), BRONZE, z=cz)
    bars = lambda lu, lv, px, py: (np.abs(lu) < 0.16) | (np.abs(lv) < 0.14)
    c.ellipse((cen[0], cen[1] - 3.6), 2.2, 1.4, BRONZE, z=cz + 1)
    c.ellipse((cen[0], cen[1] + 0.4), 3.4, 3.8, PLAGUE, z=cz + 1, flat=0.8, paint=[(bars, BRONZE)])
    c.capsule((cen[0] - 3.2, cen[1] + 3.6), (cen[0] + 3.2, cen[1] + 3.6), 0.9, 0.9, BRONZE, z=cz + 3)
    c.poly([(cen[0] - 1.2, cen[1] + 4), (cen[0] + 1.2, cen[1] + 4), (cen[0], cen[1] + 6.2)], BRONZE, z=cz + 1, bevel=0.6, height=0.6)
    # yükselen salgın dumanı
    puff = p.get('puff', 0.0)
    for i in range(3):
        u = ((t * 1.0 + i / 3.0) % 1.0)
        px_ = cen[0] - 1 + math.sin(u * 6 + i) * 1.5 - u * 3
        py_ = cen[1] - 5 - u * 9
        r = 0.9 + u * 0.9
        c.ellipse((px_, py_), r, r, PLAGUE_D, z=-2)
    if puff > 0:
        for i in range(6):
            a = i * 1.05 + 0.4
            c.ellipse((cen[0] + 2.5 + math.cos(a) * 4.0 * puff, cen[1] + math.sin(a) * 3.4 * puff), 1.7 * puff, 1.7 * puff, PLAGUE_D, z=cz + 4)
    # ön kol: yırtık yen, kemik ön kol ve el (fenerin önünde)
    c.capsule(sh, e, 2.5, 3.1, ROBE, z=24)
    c.poly([(e[0] - 2.5, e[1] + 1), (e[0] + 2.5, e[1] - 1), (e[0] + 1, e[1] + 4.5), (e[0] - 0.5, e[1] + 2.5), (e[0] - 2, e[1] + 4)], ROBE_D, z=23.5, bevel=0.8, height=0.8)
    c.capsule(e, h, 0.9, 0.7, M['bone'], z=25)
    c.ellipse(h, 1.4, 1.2, M['bone'], z=25.5)
    a = af[0] + af[1]
    for k in (-0.45, 0.45):
        c.capsule(h, (h[0] + math.sin(a + k) * 2.4, h[1] + math.cos(a + k) * 2.4), 0.5, 0.4, M['bone'], z=26)
    return {'mouth': (cen[0], cen[1] + 0.5)}


COR_ANIMS = {
    'idle': (6, lambda t: dict(t=t, sw=math.sin(t * math.tau - 0.6) * 0.45, af=(0.9 + 0.1 * math.sin(t * math.tau), 0.5),
                               ab=(1.1 + 0.15 * math.sin(t * math.tau + 1), 0.7))),
    # 0: buhurdanı geriye çeker (hazırlık), 1: öne savurur, spor patlar, 2: savruluş sürer
    'attack': (3, lambda t: keyed(t, [
        dict(t=0.1, lean=-0.7, af=(-0.5, 0.5), ab=(0.6, 0.9), sw=-0.9, att=0.2, dy=-1.5, cz=-12),
        dict(t=0.3, lean=0.8, af=(1.7, -0.1), ab=(1.6, 0.2), sw=2.1, att=1.0, puff=1.0, dy=1.0),
        dict(t=0.5, lean=0.4, af=(1.4, 0.3), ab=(1.3, 0.5), sw=1.2, att=0.5, puff=0.6, dy=0.5)])),
    'hurt': (1, lambda t: dict(t=0.3, lean=-0.9, af=(1.2, 1.0), ab=(2.0, 0.6), sw=1.5, att=0.6, dy=-1)),
}


# ------------------------------------------------------------ KARA İYE (kimlik: agac_iyesi)
IBARK = Mat(ramp(22, 0.36, 0.32, spread=0.45), name='kara kabuk')
IBARK_D = Mat(ramp(16, 0.42, 0.22, spread=0.4), name='kabuk oyuğu')
IMOSS = Mat(ramp(98, 0.40, 0.46, spread=0.45), name='kara yosun')
IMOSS_D = Mat(ramp(108, 0.45, 0.32, spread=0.4), name='yosun gölgesi')
ANTLER = Mat(ramp(32, 0.26, 0.76, spread=0.45), name='geyik boynuzu')
ANTLER_D = Mat(ramp(26, 0.30, 0.48, spread=0.4), name='arka boynuz')
CRACK = Mat(ramp(286, 0.70, 1.0, spread=0.2), emissive=1.0, outline='#2a0838', name='Erlik çatlağı')


def _crack(c, pts, z, r=0.65):
    for a, b in zip(pts, pts[1:]):
        c.capsule(a, b, r, r * 0.8, CRACK, z=z)


def draw_iye(c, p):
    """Kara İye: Erlik'in bozduğu dev orman koruyucusu. Geyik kafatası, dallanan boynuzlar, sırtı örten yosun,
    kabuk gövdede mor yanan Erlik çatlakları; yere değen uzun ve ağır kollar."""
    bob, lean = p.get('bob', 0.0), p.get('lean', 0.0)
    step = p.get('step', 0.0)
    roar = p.get('roar', 0.0)
    grooves = lambda lu, lv, px, py: ((px + 2.2 * np.sin(py * 0.23)) % 5) < 1.0
    hip = (-7.0, -30 + bob * 0.6)
    sh = (5 + lean * 28, -54 + bob + max(0.0, lean) * 26 - min(0.0, lean) * 5)
    # bacaklar: kök gibi kalın, ayaklar kök saçar
    for side, z in ((-1, -12), (1, 12)):
        mat = IBARK if z > 0 else IBARK_D
        st = step * side
        top = (hip[0] + side * 4, hip[1] + 2)
        knee = (hip[0] + side * 4 + 4 + st * 0.5, -14 + bob * 0.3 - abs(st) * 0.3)
        foot = (hip[0] + side * 5 + 2 + st, -3)
        c.capsule(top, knee, 7.0, 5.6, mat, z=z, paint=[(grooves, IBARK_D)])
        c.capsule(knee, foot, 5.6, 5.0, mat, z=z, paint=[(grooves, IBARK_D)])
        for dx in (-7, -2, 4, 8):
            c.capsule((foot[0] + dx * 0.3, foot[1]), (foot[0] + dx, 0), 2.6, 1.0, mat, z=z - 1)
    # arka kol
    al = p.get('al', (0.15, 0.2))
    shb = (sh[0] - 7, sh[1] + 2)
    e, h = fk_arm(shb, al[0], al[1], 18, 18)
    c.capsule(shb, e, 6.0, 4.8, IBARK_D, z=-16)
    c.capsule(e, h, 4.8, 3.8, IBARK_D, z=-16)
    c.ellipse(h, 4.4, 4.0, IBARK_D, z=-15)
    a = al[0] + al[1]
    for k in (-0.6, -0.2, 0.2, 0.6):
        c.capsule(h, (h[0] + math.sin(a + k) * 7.5, h[1] + math.cos(a + k) * 7.5), 1.6, 0.5, IBARK_D, z=-15)
    # gövde: kambur sırt, öne taşan fıçı göğüs
    c.capsule(hip, sh, 12.0, 14.0, IBARK, z=0, paint=[(grooves, IBARK_D)])
    hump = lerp2(hip, sh, 0.55)
    c.ellipse((hump[0] - 2, hump[1] - 4), 14.0, 12.0, IBARK, z=1, paint=[(grooves, IBARK_D)])
    cc = (sh[0] + 6 - lean * 3, sh[1] + 10)
    c.ellipse(cc, 10.5, 12.5, IBARK, z=3, paint=[(grooves, IBARK_D)])
    # Erlik çatlakları: göğsün önü (kolun önünde kalan yer) ve sırt
    gx, gy = cc[0] + 5.5, cc[1] + 5
    _crack(c, [(gx - 1.5, gy - 1.5), (gx + 0.5, gy + 2), (gx - 1, gy + 6), (gx + 0.5, gy + 10)], 40, 0.55)
    _crack(c, [(gx + 0.5, gy + 2), (gx + 2.6, gy + 3.5)], 40, 0.45)
    # böğür: Erlik'in zincir izi gibi yarılmış büyük çatlak, ortasında yanan öz
    fx_, fy_ = hip[0] + 3, hip[1] - 9
    _crack(c, [(fx_ - 1, fy_ - 8), (fx_ + 1.5, fy_ - 4), (fx_ - 0.5, fy_), (fx_ + 1, fy_ + 4), (fx_ - 1.5, fy_ + 9)], 44, 0.75)
    _crack(c, [(fx_ + 1.5, fy_ - 4), (fx_ + 5, fy_ - 5.5)], 44, 0.5)
    _crack(c, [(fx_ - 0.5, fy_), (fx_ - 4.5, fy_ + 1.5), (fx_ - 6, fy_ + 5)], 44, 0.5)
    _crack(c, [(fx_ + 1, fy_ + 4), (fx_ + 4, fy_ + 6)], 44, 0.5)
    c.ellipse((fx_, fy_ - 1), 1.8, 2.6, CRACK, z=46)
    # sırt yosunu: tek parça örtü, alt kenarı püsküllü
    top, bot = [], []
    for i in range(9):
        t = i / 8
        q = lerp2((hip[0] - 6, hip[1] + 2), (sh[0] + 4, sh[1] - 2), t)
        bump = math.sin(t * math.pi)
        topy = q[1] - 12.5 - bump * 9
        top.append((q[0] - bump * 1.5, topy - 1.5))
        bot.append((q[0] - bump * 1.5 + (1.5 if i % 2 else -1.0), topy + 7 + (i % 2) * 3.0))
    moss_d = lambda lu, lv, px, py: (np.sin(px * 0.9 + py * 0.4) > 0.55)
    c.poly(top + bot[::-1], IMOSS, z=26, bevel=2.0, height=2.5, paint=[(moss_d, IMOSS_D)])
    for i in range(1, 8, 2):
        q = bot[i]
        L = 4 + (i * 7) % 5
        c.capsule(q, (q[0] - 0.8 - lean * 2, q[1] + L), 1.1, 0.5, IMOSS_D, z=25)
    # baş: geyik kafatası, öne ve aşağı sarkık
    hdy = p.get('hdy', 0.0)
    hx, hy = sh[0] + 14, sh[1] + 2 + hdy - roar * 3
    c.capsule((sh[0] + 3, sh[1] - 1), (hx - 2, hy + 1), 6.0, 4.0, IBARK, z=20, paint=[(grooves, IBARK_D)])
    antler(c, (hx - 3.5, hy - 4.0), -2.3 - roar * 0.15, 24, ANTLER_D, 6, r0=1.6, curve=0.3, tines=(1, 2, 3))
    c.ellipse((hx, hy), 6.2, 5.4, M['bone'], z=30)
    c.poly([(hx + 1, hy - 4.2), (hx + 14, hy + 2.8 - roar), (hx + 13.5, hy + 5.0 - roar), (hx + 2, hy + 4.8)], M['bone'], z=31, bevel=1.4, height=1.6)
    jaw = 1.0 + roar * 4.0
    c.poly([(hx - 1, hy + 3.8), (hx + 11.5, hy + 4.6 - roar + jaw), (hx + 10.5, hy + 6.0 - roar + jaw), (hx, hy + 5.8)], BONE_D, z=29, bevel=0.8, height=1.0)
    c.capsule((hx + 6.5, hy - 0.4 - roar * 0.5), (hx + 10, hy + 1.3 - roar * 0.8), 0.7, 0.5, M['black'], z=40)
    c.ellipse((hx + 1.4, hy - 0.6), 2.6, 2.2, M['black'], z=40)
    c.capsule((hx + 0.8, hy - 0.6), (hx + 2.4, hy - 0.8), 0.9, 0.7, CRACK, z=46)
    for i in range(4):
        c.dot((hx + 4 + i * 2.0, hy + 4.9 - roar * 0.4 + i * 0.2), M['bone'], z=44)
    antler(c, (hx - 1.0, hy - 4.6), -2.05 - roar * 0.15, 29, ANTLER, 34, r0=1.9, curve=0.28, tines=(1, 2, 3))
    # ön kol: uzun, ağır; omuzda yosun, ön kolda çatlak, yumrukta kök pençeler
    ar = p.get('ar', (0.25, 0.15))
    shf = (sh[0] + 1, sh[1] + 3)
    e, h = fk_arm(shf, ar[0], ar[1], 19, 19)
    c.capsule(shf, e, 6.5, 5.2, IBARK, z=50, paint=[(grooves, IBARK_D)])
    c.capsule(e, h, 5.2, 4.2, IBARK, z=50, paint=[(grooves, IBARK_D)])
    c.ellipse((shf[0] - 0.5, shf[1] - 3), 7.0, 4.2, IMOSS, z=58, rot=ar[0] * 0.3, paint=[(moss_d, IMOSS_D)])
    for j in range(3):
        q = (shf[0] - 4 + j * 3.5, shf[1] + 0.5)
        c.capsule(q, (q[0] - 0.5, q[1] + 3 + j % 2 * 2), 1.0, 0.5, IMOSS_D, z=57)
    m1, m2 = lerp2(e, h, 0.15), lerp2(e, h, 0.75)
    _crack(c, [m1, (lerp2(m1, m2, 0.5)[0] + 1.2, lerp2(m1, m2, 0.5)[1]), m2], 62, 0.5)
    c.ellipse(h, 5.0, 4.6, IBARK, z=56, paint=[(grooves, IBARK_D)])
    a = ar[0] + ar[1]
    for k in (-0.65, -0.22, 0.22, 0.65):
        tip = (h[0] + math.sin(a + k) * 8.5, h[1] + math.cos(a + k) * 8.5)
        c.capsule(h, tip, 2.0, 0.5, IBARK, z=55)
    return {'hand': h}


def _iye_walk(t):
    s = math.sin(t * 6.28)
    return dict(bob=-abs(s) * 1.6, lean=0.06 + 0.03 * s, step=3.0 * s, al=(0.15 + 0.3 * s, 0.25), ar=(0.25 - 0.3 * s, 0.2), hdy=abs(s) * 0.8)


IYE_ANIMS = {
    'idle': (4, lambda t: dict(bob=math.sin(t * 6.28) * 0.9, lean=0.05 + 0.02 * math.sin(t * 6.28), al=(0.12, 0.22), ar=(0.25 + 0.05 * math.sin(t * 6.28), 0.12),
                               hdy=0.6 * math.sin(t * 6.28 + 0.8))),
    'walk': (6, _iye_walk),
    # hazırlık: kolu başının üstüne kaldırır, kükrer; ikinci kare daha geride (tutulur)
    'windup': (2, lambda t: keyed(t, [
        dict(bob=-1.5, lean=-0.06, ar=(2.6, 0.7), al=(0.4, 0.5), roar=0.6),
        dict(bob=-2.5, lean=-0.14, ar=(3.3, 0.6), al=(0.6, 0.6), roar=1.0)])),
    # ezme: yumruk yere iner, sonra gövde çöker (aşma)
    'slam': (2, lambda t: keyed(t, [
        dict(bob=3.0, lean=0.34, ar=(0.5, 0.08), al=(0.3, 0.3), roar=0.8, step=1.0),
        dict(bob=4.5, lean=0.30, ar=(0.42, 0.18), al=(0.15, 0.25), roar=0.3, step=1.0, hdy=1.5)])),
    'hurt': (1, lambda t: dict(bob=1, lean=-0.12, ar=(-0.4, 0.6), al=(-0.3, 0.5), roar=0.5, hdy=-1)),
}


# ------------------------------------------------------------ BALBAL (canlanan Göktürk taş heykeli)
BSTONE = Mat(ramp(36, 0.10, 0.66, spread=0.45), name='balbal taşı')
BSTONE2 = Mat(ramp(36, 0.10, 0.70, spread=0.45), name='kabartma taş')
BSTONE_D = Mat(ramp(222, 0.14, 0.38, spread=0.4), name='oyma gölgesi')
BSTONE_L = Mat(ramp(40, 0.12, 0.84, spread=0.4), name='açık taş')
BMOSS = Mat(ramp(92, 0.50, 0.55), name='taş yosunu')
RUNE = Mat(ramp(186, 0.75, 1.0, spread=0.2), emissive=1.0, outline='#06343e', name='Orhun runası')

# Orhun yazısını anımsatan 3x4 damgalar
RUNES = [
    ('010', '111', '010', '010'),
    ('101', '101', '010', '010'),
    ('100', '110', '101', '100'),
    ('011', '100', '011', '100'),
    ('111', '001', '010', '100'),
    ('101', '010', '101', '010'),
    ('110', '101', '110', '100'),
]


def _rune(c, x, y, k, mat, z=60):
    for j, row in enumerate(RUNES[k % len(RUNES)]):
        for i, ch in enumerate(row):
            if ch == '1':
                c.dot((x + i, y + j), mat, z=z)


def draw_balbal(c, p):
    """Balbal: kaidesi üstünde Göktürk taş savaşçısı. Oyma yüz ve sarkık bıyık, göğsünde kadeh, kemer, taş kılıç;
    gövdede ve kaidede Orhun runaları uyanınca camgöbeği yanar. Çatlaklar, yosun lekeleri."""
    sq = p.get('squash', 0.0)
    awake = p.get('awake', 1.0) > 0.5
    S = Sq(c, 1 + sq * 0.12, 1 - sq * 0.14, p.get('bob', 0.0))
    lean = p.get('lean', 0.0)
    L = lambda x, y: (x + lean * (-y) * 0.12, y)   # üst gövde eğilmesi
    rm = RUNE if awake else BSTONE_D
    crack = lambda lu, lv, px, py: (np.abs(px - (-3.5 + np.sin(py * 0.9) * 1.3 + py * 0.08)) < 0.55) & (py > -29) & (py < -17)
    crack2 = lambda lu, lv, px, py: (np.abs(px - (4 + np.sin(py * 1.3) * 1.0)) < 0.5) & (py > -45) & (py < -39)
    # kaide
    S.poly([(-12, 0), (12, 0), (11, -5.5), (-11, -5.5)], BSTONE_D, z=-2, bevel=1.6, height=2)
    S.poly([(-11.5, -4.5), (11.5, -4.5), (10.5, -6.5), (-10.5, -6.5)], BSTONE, z=-1, bevel=1, height=1.5)
    for i in range(3):
        _rune(S, -7.5 + i * 6, -4.4, i + 2, rm, z=40)
    S.ellipse((-9.5, -5.5), 3.2, 1.5, BMOSS, z=6)
    S.ellipse((8.5, -1), 2.2, 1.2, BMOSS, z=6)
    # arka saç örgüsü
    S.capsule(L(-5.5, -40), L(-7.5, -30), 1.6, 1.2, BSTONE_D, z=-3)
    # gövde (kaftanlı taş blok)
    S.poly([L(-9.5, -6), L(9.5, -6), L(9.8, -13), L(8.8, -27), L(5, -30.5), L(-5.5, -30.5), L(-9, -27.5), L(-9.8, -13)], BSTONE, z=0, bevel=2.6, height=3,
           paint=[(crack, BSTONE_D)])
    S.ellipse(L(-8.5, -24), 1.6, 3.0, BMOSS, z=7)
    S.ellipse(L(7.5, -8), 2.2, 1.6, BMOSS, z=7)
    # etek kenarı (oyma)
    S.capsule(L(-9.6, -7.5), L(9.6, -7.5), 0.55, 0.55, BSTONE_D, z=8)
    # kaftan yakası (oyma çizgi)
    S.capsule(L(1, -30), L(2.5, -15), 0.5, 0.5, BSTONE_D, z=8)
    # runalar: gövdenin arka yanı ve etek
    _rune(S, *L(-8, -26), 0, rm, z=40)
    _rune(S, *L(-8, -21), 1, rm, z=40)
    # kemer: toka + sarkan kese
    S.capsule(L(-9.6, -14.5), L(9.6, -14.5), 1.3, 1.3, BSTONE_D, z=9)
    S.ellipse(L(3.5, -14.5), 1.4, 1.4, BSTONE_L, z=14)
    S.poly([L(-6, -13.5), L(-3.5, -13.5), L(-3.8, -9.5), L(-5.8, -9.8)], BSTONE2, z=12, bevel=0.8, height=1)
    # kılıç: uyurken kında, uyanınca elde
    sword = p.get('sword', 1.0 if awake else 0.0)
    if sword < 0.5:
        S.capsule(L(7.5, -14), L(1.5, -1.5), 1.5, 1.1, BSTONE_D, z=13)
        S.capsule(L(6.5, -16), L(9.5, -13), 0.9, 0.9, BSTONE2, z=14)
    # arka kol: kadehi göğüste tutar
    shb = L(-5.5, -27.5)
    S.capsule(shb, L(-5.5, -20), 2.6, 2.3, BSTONE2, z=10)
    S.capsule(L(-5.5, -20), L(1.5, -21.5), 2.3, 2.0, BSTONE2, z=12)
    S.poly([L(-0.4, -27.8), L(6.0, -27.8), L(4.8, -23.2), L(0.8, -23.2)], BSTONE_L, z=18, bevel=1.0, height=1.2)
    S.capsule(L(2.8, -23.2), L(2.8, -21), 0.8, 0.8, BSTONE_L, z=18)
    S.capsule(L(-0.2, -27.6), L(5.8, -27.6), 0.6, 0.6, BSTONE_D, z=20)
    # baş: yuvarlak yüz, alçak börk, sarkık bıyık
    hc = L(1.5, -38.5)
    S.capsule(L(0.5, -31), L(1.2, -33), 3.0, 3.0, BSTONE, z=1)
    S.ellipse(hc, 7.0, 8.0, BSTONE, z=2, paint=[(crack2, BSTONE_D)])
    hx, hy = hc
    S.poly([(hx - 7.2, hy - 3.5), (hx + 6.8, hy - 3.5), (hx + 5.5, hy - 8.8), (hx + 0.5, hy - 10.5), (hx - 5.5, hy - 9.2)], BSTONE2, z=10, bevel=1.6, height=2)
    S.capsule((hx - 7.4, hy - 3.6), (hx + 7.0, hy - 3.6), 1.1, 1.1, BSTONE_D, z=13)
    S.ellipse((hx - 3, hy - 9.5), 3.5, 1.4, BMOSS, z=16)
    # yüz düzlemi (açık taş), kaş çıkıntısı, gözler, sarkık bıyık
    S.ellipse((hx + 3.4, hy + 0.8), 4.2, 5.2, BSTONE_L, z=16, flat=0.85)
    S.capsule((hx + 0.2, hy - 2.0), (hx + 6.8, hy - 2.0), 0.6, 0.6, BSTONE_D, z=20)
    eye = RUNE if awake else BSTONE_D
    S.capsule((hx + 1.2, hy - 0.4), (hx + 2.6, hy - 0.4), 0.6, 0.5, eye, z=22)
    S.capsule((hx + 4.6, hy - 0.4), (hx + 5.8, hy - 0.4), 0.6, 0.5, eye, z=22)
    S.capsule((hx + 3.7, hy + 0.4), (hx + 3.7, hy + 1.8), 0.4, 0.4, BSTONE, z=22)
    S.capsule((hx + 3.4, hy + 2.6), (hx + 1.0, hy + 3.4), 1.0, 0.8, BSTONE_D, z=24)
    S.capsule((hx + 1.0, hy + 3.4), (hx + 0.5, hy + 5.6), 0.8, 0.5, BSTONE_D, z=24)
    S.capsule((hx + 4.0, hy + 2.6), (hx + 6.4, hy + 3.4), 1.0, 0.8, BSTONE_D, z=24)
    S.capsule((hx + 6.4, hy + 3.4), (hx + 6.8, hy + 5.6), 0.8, 0.5, BSTONE_D, z=24)
    # ön kol + kılıç
    sa = p.get('arm', (0.15, 0.6))
    shf = L(6.5, -27.5)
    e, h = fk_arm(shf, sa[0], sa[1], 7.0, 6.5)
    S.capsule(shf, e, 2.8, 2.5, BSTONE2, z=26)
    S.capsule(e, h, 2.5, 2.2, BSTONE2, z=27)
    S.ellipse(h, 2.3, 2.3, BSTONE2, z=28)
    S.ellipse((shf[0] - 0.5, shf[1] - 0.8), 2.4, 1.3, BMOSS, z=30)
    if sword >= 0.5:
        ang = p.get('swang', sa[0] + sa[1])
        dx, dy = math.sin(ang), math.cos(ang)
        tip = (h[0] + dx * 18, h[1] + dy * 18)
        pom = (h[0] - dx * 3, h[1] - dy * 3)
        S.capsule(pom, h, 0.9, 0.9, BSTONE_D, z=25)
        S.capsule((h[0] - dy * 3.2, h[1] + dx * 3.2), (h[0] + dy * 3.2, h[1] - dx * 3.2), 1.0, 1.0, BSTONE_D, z=29)
        S.capsule((h[0] + dx * 2, h[1] + dy * 2), tip, 1.9, 0.9, BSTONE_L, z=27)
        if awake:
            S.capsule((h[0] + dx * 4, h[1] + dy * 4), (h[0] + dx * 15, h[1] + dy * 15), 0.45, 0.45, RUNE, z=34)
    return {}


BALBAL_ANIMS = {
    'idle': (2, lambda t: keyed(t, [dict(awake=1.0, bob=0, arm=(0.35, 0.9), swang=1.0), dict(awake=1.0, bob=-0.5, squash=-0.1, arm=(0.4, 0.9), swang=1.05)])),
    'dormant': (1, lambda t: dict(awake=0.0, sword=0.0, arm=(0.05, 0.4))),
    'hop': (4, lambda t: keyed(t, [dict(squash=0.8, bob=0, arm=(0.5, 0.9), swang=1.2),
                                    dict(squash=-0.5, bob=-3, arm=(0.2, 0.9), swang=0.7),
                                    dict(squash=-0.2, bob=-4, arm=(0.3, 0.9), swang=0.9),
                                    dict(squash=0.5, bob=0, arm=(0.6, 0.9), swang=1.3)])),
    # hazırlık: kılıç başın üstünden geriye; ikinci kare daha geride, gövde geriye eğik
    'windup': (2, lambda t: keyed(t, [dict(arm=(2.7, 0.3), swang=3.3, bob=-1, lean=-0.4, squash=-0.1),
                                       dict(arm=(3.1, 0.4), swang=3.8, bob=-1.5, lean=-0.7, squash=-0.15)])),
    # vuruş: öne iner, sonra yere değecek kadar aşar
    'strike': (2, lambda t: keyed(t, [dict(arm=(1.5, 0.1), swang=1.45, bob=1, squash=0.3, lean=0.5),
                                       dict(arm=(1.05, 0.15), swang=0.8, bob=1, squash=0.4, lean=0.6)])),
}


# ------------------------------------------------------------ KARA KAM (kimlik: arcura)
KCOAT = Mat(ramp(18, 0.45, 0.34, spread=0.45), name='kam postu')
KCOAT_D = Mat(ramp(10, 0.45, 0.20, spread=0.4), name='post gölgesi')
FRINGE = Mat(ramp(36, 0.55, 0.70), name='saçak')
OWL = Mat(ramp(32, 0.28, 0.66, spread=0.45), name='baykuş tüyü')
OWL_D = Mat(ramp(24, 0.35, 0.36), name='tüy çizgisi')
KMASK = Mat(ramp(42, 0.10, 0.92, spread=0.4), name='kemik maske')
DRUM = Mat(ramp(38, 0.38, 0.80, spread=0.4), name='davul derisi')
KSKIN = Mat(ramp(250, 0.14, 0.36), name='kam eli')
CURSE = Mat(ramp(288, 0.75, 1.0, spread=0.2), emissive=1.0, outline='#2a0838', name='kara büyü')


def draw_kam(c, p):
    """Kara Kam: Erlik'e kul olmuş kötü kam. Kemik maske, geyik boynuzlu ve baykuş tüylü başlık, saçaklı
    ve çıngıraklı kam postu, bir elinde kam davulu, öbür elinde mor yanan lanet."""
    bob, lean = p.get('bob', 0.0), p.get('lean', 0.0)
    cast = p.get('cast', 0.0)
    ph = p.get('ph', 0.0)
    hip = (0.0, -12 + bob)
    lx = lean * 5
    # bacaklar: kısa, koyu çizme
    for side, (a1, a2) in ((-1, p.get('lb', (0.2, 0.3))), (1, p.get('lf', (-0.15, 0.3)))):
        z = -4 if side < 0 else 4
        base = (hip[0] + side * 2, hip[1])
        k, f = fk_leg(base, a1, a2, 5.6, 6.0)
        mat = KCOAT_D
        c.capsule(base, k, 1.9, 1.6, mat, z=z)
        c.capsule(k, f, 1.6, 1.5, M['black'] if side < 0 else KSKIN, z=z)
        c.capsule(f, (f[0] + 2.4, f[1] - 0.3), 1.4, 1.0, KCOAT_D, z=z + 0.1)
    # davul (arka elde, gövdenin arkasında)
    dr = p.get('drum', 0.0)
    dc = (hip[0] - 9.5 + lx * 0.5, hip[1] - 12 - dr * 3)
    c.ellipse(dc, 5.4, 7.2, M['wood'], z=-16, rot=0.25 - dr * 0.3, depth=0.3)
    sym = lambda lu, lv, px, py: (np.abs(lu * lu + lv * lv - 0.36) < 0.08) | ((np.abs(lu) < 0.1) & (np.abs(lv) < 0.55)) | ((np.abs(lv) < 0.1) & (np.abs(lu) < 0.55))
    c.ellipse(dc, 4.4, 6.2, DRUM, z=-13.5, rot=0.25 - dr * 0.3, depth=0.3, flat=0.7, paint=[(sym, M['red_paint'])])
    for i in range(3):
        a = 1.3 + i * 0.35
        q = (dc[0] + math.cos(a) * 4.8, dc[1] + math.sin(a) * 6.6)
        c.capsule(q, (q[0] + math.sin(ph + i) * 0.6, q[1] + 2.5), 0.5, 0.5, M['iron'], z=-13)
    # arka kol (davulu tutar)
    shb = (hip[0] - 3 + lx, hip[1] - 12)
    c.capsule(shb, (dc[0] + 3, dc[1] + 1), 1.8, 1.5, KCOAT_D, z=-10)
    # kam postu: aşağı genişler
    seams = lambda lu, lv, px, py: (np.floor(px - lx * 0.5 * 0) % 5 == 0) & (py > hip[1] - 6)
    coat = [(-4.5 + lx, hip[1] - 14), (5.5 + lx, hip[1] - 14), (6.8 + lx * 0.5, hip[1] - 6), (9.5, hip[1] + 5), (-9.5, hip[1] + 5), (-6.5 + lx * 0.5, hip[1] - 6)]
    c.poly(coat, KCOAT, z=0, bevel=2.2, height=2.5, paint=[(seams, KCOAT_D)])
    # göğüs saçakları ve çıngıraklar
    for i in range(6):
        x = -4 + lx * 0.8 + i * 1.8
        y = hip[1] - 8
        c.capsule((x, y), (x + math.sin(ph + i) * 0.5 - lean * 1.5, y + 3), 0.55, 0.45, FRINGE, z=12)
    c.capsule((-5 + lx * 0.7, hip[1] - 8.5), (6.5 + lx * 0.7, hip[1] - 8.5), 0.6, 0.6, M['red_paint'], z=12.5)
    # etek saçakları: deri püsküller, kızıl şeritler, demir çıngıraklar
    for i in range(10):
        x = -9 + i * 2.0
        y = hip[1] + 4.5
        sway = math.sin(ph * 1.0 + i * 0.7) * 0.6 - lean * 2.5
        Ln = 4.0 if i % 3 else 6.0
        mat = M['red_paint'] if i % 3 == 0 else FRINGE
        c.capsule((x, y), (x + sway, y + Ln), 0.65, 0.5, mat, z=8 + (i % 2) * 0.3)
        if i % 3 == 1:
            q = (x + sway * 0.8 + 0.7, y + 2.5)
            c.poly([(q[0] - 0.8, q[1]), (q[0] + 0.8, q[1]), (q[0] + 0.3, q[1] + 3.2), (q[0] - 0.3, q[1] + 3.2)], M['iron'], z=10, bevel=0.5, height=0.6)
    # baş: kemik maske + sarkan saçak sakal
    hd = (2.0 + lx * 1.3, hip[1] - 18.5)
    c.ellipse((hd[0] - 1.5, hd[1] + 0.5), 3.6, 4.0, KCOAT_D, z=3)
    for i in range(4):
        x = hd[0] - 0.5 + i * 1.3
        c.capsule((x, hd[1] + 2.5), (x - lean * 1.0, hd[1] + 6.5 + (i % 2)), 0.55, 0.45, M['black'], z=13)
    c.ellipse((hd[0] + 1.6, hd[1] + 0.2), 3.4, 4.6, KMASK, z=14, flat=0.85)
    c.ellipse((hd[0] + 0.6, hd[1] - 0.8), 0.9, 1.1, M['black'], z=20)
    c.ellipse((hd[0] + 3.0, hd[1] - 0.8), 0.8, 1.1, M['black'], z=20)
    glint = CURSE if cast > 0.3 else M['red_paint']
    c.dot((hd[0] + 0.6, hd[1] - 0.9), glint, z=24); c.dot((hd[0] + 3.0, hd[1] - 0.9), glint, z=24)
    c.capsule((hd[0] + 0.6, hd[1] + 0.6), (hd[0] + 0.4, hd[1] + 2.4), 0.35, 0.35, M['red_paint'], z=22)
    c.capsule((hd[0] + 3.0, hd[1] + 0.6), (hd[0] + 3.2, hd[1] + 2.4), 0.35, 0.35, M['red_paint'], z=22)
    c.capsule((hd[0] + 0.9, hd[1] + 2.8), (hd[0] + 3.0, hd[1] + 2.8), 0.45, 0.45, M['black'], z=22)
    # başlık: baykuş tüyleri (yelpaze), boynuzlar, alın bandı
    feather = lambda lu, lv, px, py: (np.floor(py * 0.7) % 2 == 0)
    for k in range(5):
        a = -2.6 + k * 0.28 + math.sin(ph + k) * 0.05 - lean * 0.2
        b = (hd[0] - 1.5, hd[1] - 3.0)
        tip = (b[0] + math.cos(a) * 9.5, b[1] + math.sin(a) * 9.5)
        perp = (-math.sin(a) * 1.4, math.cos(a) * 1.4)
        mid = lerp2(b, tip, 0.55)
        c.poly([b, (mid[0] + perp[0], mid[1] + perp[1]), tip, (mid[0] - perp[0], mid[1] - perp[1])], OWL, z=1 + k * 0.2, bevel=0.8, height=0.8, paint=[(feather, OWL_D)])
        c.dot(tip, OWL_D, z=3)
    antler(c, (hd[0] - 0.5, hd[1] - 3.5), -1.85, 10, ANTLER_D, 4, r0=0.9, curve=-0.25, tines=(2,), tine_len=0.4, n=3)
    antler(c, (hd[0] + 1.6, hd[1] - 3.6), -1.4, 11, ANTLER, 16, r0=1.0, curve=-0.2, tines=(1, 2), tine_len=0.42, n=3)
    c.capsule((hd[0] - 2.2, hd[1] - 3.2), (hd[0] + 4.2, hd[1] - 3.4), 1.0, 1.0, M['red_paint'], z=18)
    for i in range(3):
        c.dot((hd[0] - 1.0 + i * 2.2, hd[1] - 3.4), M['iron'], z=22)
    # ön kol: lanet eli
    ar = p.get('ar', (0.6, 0.8))
    shf = (hip[0] + 3.5 + lx, hip[1] - 12)
    e, h = fk_arm(shf, ar[0], ar[1], 5.5, 5.5)
    c.capsule(shf, e, 1.9, 1.7, KCOAT, z=26)
    c.capsule(e, lerp2(e, h, 0.6), 1.7, 1.9, KCOAT, z=26)
    a = ar[0] + ar[1]
    cuff = lerp2(e, h, 0.6)
    for k in (-1, 1):
        c.capsule(cuff, (cuff[0] + k * 0.8, cuff[1] + 2.6), 0.45, 0.4, FRINGE, z=26.5)
    c.capsule(lerp2(e, h, 0.6), h, 0.9, 0.9, KSKIN, z=27)
    for k in (-0.5, 0.0, 0.5):
        c.capsule(h, (h[0] + math.sin(a + k) * 2.4, h[1] + math.cos(a + k) * 2.4), 0.45, 0.35, KSKIN, z=27.5)
    gc = (h[0] + math.sin(a) * 2.6, h[1] + math.cos(a) * 2.6)
    r = 1.0 + cast * 2.2 + p.get('flick', 0.0)
    c.ellipse(gc, r, r, CURSE, z=30)
    if cast > 0.5:
        for i in range(4):
            aa = ph + i * 1.57
            c.dot((gc[0] + math.cos(aa) * (r + 2), gc[1] + math.sin(aa) * (r + 2)), CURSE, z=31)
    return {'hand': gc}


KAM_ANIMS = {
    'idle': (4, lambda t: dict(bob=0.6 * math.sin(t * 6.28), cast=0.2, ar=(0.75 + 0.15 * math.sin(t * 6.28), 0.9), ph=t * 6.28, flick=0.3 * math.sin(t * 12.56), drum=0.1 * math.sin(t * 6.28))),
    'run': (6, lambda t: dict(bob=-abs(math.sin(t * 6.28)) * 1.5, lean=0.3, ph=t * 6.28 * 2,
                              lb=(0.8 * math.sin(t * 6.28), 0.5 + 0.6 * max(0, -math.sin(t * 6.28))),
                              lf=(-0.8 * math.sin(t * 6.28), 0.5 + 0.6 * max(0, math.sin(t * 6.28))), ar=(1.0, 0.7), drum=0.2)),
    # büyü: 0 eli geriye kaldırır + davula vurur, 1 öne savurur (fırlatma), 2 aşma
    'cast': (3, lambda t: keyed(t, [dict(bob=-1, lean=-0.25, cast=0.6, ar=(2.6, 0.7), drum=0.8, ph=1.0),
                                     dict(bob=-2, lean=0.25, cast=1.0, ar=(1.6, 0.05), drum=0.3, ph=2.0),
                                     dict(bob=0, lean=0.15, cast=0.7, ar=(1.3, 0.35), drum=0.1, ph=3.0)])),
    'hurt': (1, lambda t: dict(bob=1, lean=-0.35, ar=(-0.5, 0.9), drum=-0.3, ph=0.5)),
}


# ------------------------------------------------------------ GULYABANİ (kimlik: surale)
GSKIN = Mat(ramp(196, 0.10, 0.80, spread=0.45), name='ölü ten')
GSKIN_D = Mat(ramp(210, 0.16, 0.56, spread=0.4), name='ölü ten gölgesi')
GSKIN_DD = Mat(ramp(218, 0.18, 0.38, spread=0.4), name='arka bacak')
SHROUD = Mat(ramp(40, 0.16, 0.46, spread=0.45), name='kefen')
SHROUD_D = Mat(ramp(30, 0.22, 0.28, spread=0.4), name='kefen gölgesi')
GHAIR = Mat(ramp(250, 0.25, 0.16, spread=0.3), name='kara saç')
GEYE = Mat(ramp(62, 0.55, 1.0, spread=0.2), emissive=1.0, outline='#2a2a04', name='ölü göz')
GCLAW = Mat(ramp(42, 0.35, 0.78, spread=0.4), name='sarı tırnak')


def draw_gul(c, p):
    """Gulyabani: kambur, sıska, solgun gul. Yere değen çok uzun kollar ve pençeler, yırtık kefen, uzun yağlı
    kara saç, oyuk gözlerde soluk ışık."""
    bob, lean = p.get('bob', 0.0), p.get('lean', 0.0)
    grab = p.get('grab', 0.0)
    ph = p.get('ph', 0.0)
    hip = (-2.0, -36 + bob)
    # bacaklar: uzun, sıska, dizler bükük
    for side, (a1, a2) in ((-1, p.get('lb', (0.35, 0.7))), (1, p.get('lf', (0.1, 0.6)))):
        z = -8 if side < 0 else 8
        base = (hip[0] + side * 2.5, hip[1])
        k, f = fk_leg(base, a1, a2, 19.0, 19.0)
        mat = GSKIN_D if side > 0 else GSKIN_DD
        c.capsule(base, k, 3.0, 1.9, mat, z=z)
        c.ellipse(k, 1.9, 1.9, mat, z=z + 0.5)
        c.capsule(k, f, 1.7, 1.2, mat, z=z)
        for j in range(3):
            c.capsule(f, (f[0] + 3.5 + j * 0.3, f[1] - 0.2 + (j - 1) * 0.9), 0.8, 0.4, GCLAW if side > 0 else GSKIN_DD, z=z + 0.2)
    # omurga: kambur eğri
    mid = (hip[0] + 6 + lean * 10, hip[1] - 15 + lean * 2)
    sh = (hip[0] + 13 + lean * 20, hip[1] - 21 + lean * 6)
    ribs = lambda lu, lv, px, py: (np.floor(py * 0.55) % 2 == 0) & (lv < -0.0) & (lv > -0.8)
    # arka kol
    ab = p.get('ab', (0.3, 0.3))
    grab_open = grab

    def arm(shp, a, z, mat, matd, front):
        e, h = fk_arm(shp, a[0], a[1], 20.0, 20.0)
        c.capsule(shp, e, 2.4, 1.7, mat, z=z)
        c.ellipse(e, 1.8, 1.8, matd, z=z + 0.4)
        c.capsule(e, h, 1.7, 1.4, mat, z=z)
        c.ellipse(h, 2.2, 1.9, mat, z=z + 0.5)
        ang = a[0] + a[1]
        for k in range(4):
            fa = ang + (k - 1.5) * (0.28 + 0.25 * grab_open)
            m1 = (h[0] + math.sin(fa) * 4.5, h[1] + math.cos(fa) * 4.5)
            fb = fa - (0.9 - 0.7 * grab_open)
            tip = (m1[0] + math.sin(fb) * 5.5, m1[1] + math.cos(fb) * 5.5)
            c.capsule(h, m1, 0.8, 0.6, mat, z=z + 0.6)
            c.capsule(m1, tip, 0.65, 0.3, GCLAW if front else matd, z=z + 0.7)
        if front:
            # yenden sarkan kefen şeritleri
            for j in range(2):
                q = lerp2(shp, e, 0.4 + j * 0.35)
                st = chain(q, 3, 2.4, math.pi * 0.55 + math.sin(ph + j) * 0.2 - lean * 0.5, 0.1, ph + j, 0.3)
                strand(c, st, 1.0, 0.5, SHROUD, z + 1.2)
        return h

    arm((sh[0] - 3, sh[1] + 1), ab, -12, GSKIN_D, GSKIN_D, False)
    # saç (arkada sarkan)
    hd = (sh[0] + 7 + lean * 3, sh[1] + 4 + lean * 2 - p.get('hup', 0.0))
    for k in range(7):
        st = chain((hd[0] - 2.5 + k * 0.4, hd[1] - 3.5), 6, 2.9 + (k % 3) * 0.3, math.pi * 0.62 + k * 0.05 - lean * 0.5, 0.04, ph + k * 0.8, 0.22)
        strand(c, st, 1.3, 0.5, GHAIR, -4)
    # gövde: sıska, kaburgalı
    c.capsule(hip, mid, 5.5, 8.0, GSKIN, z=0, paint=[(ribs, GSKIN_D)])
    c.capsule(mid, sh, 8.0, 6.2, GSKIN, z=0.5, paint=[(ribs, GSKIN_D)])
    # kefen: sırttan dizlere, yırtık etek
    hx0, hy0 = hip
    shroud = [(sh[0] + 3, sh[1] - 5.5), (mid[0] - 2, mid[1] - 8), (hx0 - 6, hy0 - 6), (hx0 - 9, hy0 + 13), (hx0 - 6, hy0 + 9),
              (hx0 - 4, hy0 + 16), (hx0 - 1, hy0 + 8), (hx0 + 2.5, hy0 + 14), (hx0 + 4, hy0 + 5), (mid[0] + 1, mid[1] + 3), (sh[0] - 1, sh[1] + 2)]
    folds = lambda lu, lv, px, py: (np.floor(px * 0.5 + py * 0.15) % 3 == 0)
    c.poly(shroud, SHROUD, z=6, bevel=2.2, height=2.5, paint=[(folds, SHROUD_D)])
    for j in range(3):
        q = (hx0 - 8 + j * 4.5, hy0 + 11 + (j % 2) * 3)
        st = chain(q, 3, 2.6, math.pi * 0.5 + 0.2 + math.sin(ph + j * 1.7) * 0.25 - lean * 0.6, 0.0, ph + j, 0.3)
        strand(c, st, 1.1, 0.5, SHROUD_D, 6)
    # omurga çıkıntıları
    for k in range(4):
        q = lerp2(hip, sh, 0.25 + k * 0.2)
        c.dot((q[0] - 3.5 - k * 0.6, q[1] - 5.5 - k * 0.3), M['bone'], z=40)
    # boyun + baş: öne sarkık, iri kafatası, oyuk gözler, açılan çene
    c.capsule((sh[0] + 1, sh[1] - 1), hd, 2.8, 2.4, GSKIN, z=8)
    hx, hy = hd
    K = 1.25
    c.ellipse((hx, hy - 0.5), 4.6 * K, 4.8 * K, GSKIN, z=12, paint=[(lambda lu, lv, px, py: (lu < -0.3), GSKIN_D)])
    jaw = 0.8 + grab * 3.2
    c.poly([(hx + 0.5, hy + 2.2), (hx + 7.0, hy + 2.8), (hx + 6.0, hy + 4.4 + jaw), (hx + 0.5, hy + 4.2 + jaw * 0.7)], M['black'], z=24, bevel=0.5, height=0.3)
    c.capsule((hx - 0.5, hy + 4.6 + jaw * 0.7), (hx + 5.6, hy + 5.2 + jaw), 1.1, 0.8, GSKIN_D, z=20)
    for i in range(4):
        c.dot((hx + 1.6 + i * 1.4, hy + 2.7), M['bone'], z=30)
        if jaw > 1.5:
            c.dot((hx + 1.4 + i * 1.3, hy + 3.6 + jaw * 0.8), M['bone'], z=30)
    c.ellipse((hx + 1.8, hy - 1.4), 1.9, 1.7, M['black'], z=24)
    c.ellipse((hx + 5.0, hy - 1.4), 1.3, 1.6, M['black'], z=24)
    c.capsule((hx + 1.5, hy - 1.4), (hx + 2.2, hy - 1.4), 0.6, 0.6, GEYE, z=30)
    c.dot((hx + 5.0, hy - 1.4), GEYE, z=30)
    # kefen başlığı: kafayı arkadan örter, solgun yüzü çerçeveler; altından yağlı kara saç sarkar
    for k, dx in enumerate((-4.6, -3.2, -1.8)):
        st = chain((hx + dx, hy - 3.5), 5, 2.8, math.pi * 0.5 + 0.05 + math.sin(ph + k) * 0.1 - lean * 0.4, 0.03, ph + k, 0.15)
        strand(c, st, 1.0, 0.45, GHAIR, 30 + k * 0.1)
    hood = [(sh[0] + 3, sh[1] - 5.5), (hx - 6.5, hy - 3), (hx - 4, hy - 8.5), (hx + 1.5, hy - 9.5), (hx + 6, hy - 7), (hx + 7.2, hy - 4.2),
            (hx + 4.5, hy - 4.6), (hx + 1.0, hy - 5.2), (hx - 2.2, hy - 3.0), (hx - 3.5, hy + 2.5), (hx - 5.5, hy + 4.5), (sh[0] - 1, sh[1] + 2)]
    c.poly(hood, SHROUD, z=36, bevel=2.0, height=2.5, paint=[(lambda lu, lv, px, py: (px < hx - 3.5), SHROUD_D)])
    af = p.get('af', (0.2, 0.3))
    arm((sh[0] + 2, sh[1] + 2), af, 40, GSKIN, GSKIN_D, True)
    return {}


def _gul_walk(t):
    s = math.sin(t * 6.28)
    return dict(bob=-abs(s) * 2.0, lean=0.22, ph=t * 6.28,
                lb=(0.35 + 0.55 * s, 0.6 + 0.4 * max(0, -s)), lf=(0.35 - 0.55 * s, 0.6 + 0.4 * max(0, s)),
                ab=(0.35 - 0.35 * s, 0.25), af=(0.3 + 0.35 * s, 0.3))


GUL_ANIMS = {
    'idle': (4, lambda t: dict(bob=0.9 * math.sin(t * 6.28), lean=0.12, ph=t * 6.28, ab=(0.32 + 0.08 * math.sin(t * 6.28), 0.3),
                               af=(0.18, 0.32 + 0.1 * math.sin(t * 6.28 + 1)), grab=0.15 + 0.1 * math.sin(t * 6.28))),
    'walk': (6, _gul_walk),
    # hazırlık: kollar havada, arkaya gerilir, ağız açılır; ikinci kare daha derin
    'windup': (2, lambda t: keyed(t, [dict(bob=1.5, lean=-0.05, ab=(2.3, 0.9), af=(2.2, 1.0), grab=0.7, ph=1.0, hup=1),
                                       dict(bob=2.5, lean=-0.15, ab=(2.7, 0.9), af=(2.6, 1.1), grab=1.0, ph=2.0, hup=2)])),
    # yakalama: kollar ileri fırlar (pençeler açık), sonra kapanır
    'grab': (2, lambda t: keyed(t, [dict(bob=-1, lean=0.42, ab=(1.45, 0.05), af=(1.55, -0.05), grab=1.0, ph=3.0, lb=(-0.2, 0.4), lf=(0.6, 0.5)),
                                     dict(bob=0, lean=0.4, ab=(1.3, 0.25), af=(1.4, 0.2), grab=0.2, ph=4.0, lb=(-0.15, 0.45), lf=(0.55, 0.55))])),
    'hurt': (1, lambda t: dict(bob=1, lean=-0.2, ab=(-0.4, 0.7), af=(-0.5, 0.8), grab=0.7, ph=0.5)),
}


# ------------------------------------------------------------ BOZKURT (Bengü'nün ruh biçimi)
SFUR = Mat(ramp(205, 0.08, 0.96, spread=0.3), name='ak ruh postu')
SFUR_D = Mat(ramp(200, 0.25, 0.7, spread=0.35), name='ruh postu gölgesi')
SMANE = Mat(ramp(172, 0.7, 0.95, spread=0.25), emissive=0.7, outline='#0b4a52', name='kut yelesi')


def draw_spirit_wolf(c, p):
    """Büyük ruh kurdu: kara börünün 1.6 katı; ak post, kut ışığıyla yanan yele ve gözler, turkuaz atkı.
    Pozlar: bob, tilt, jaw, hb/hf/fb/ff bacak açıları, tw kuyruk, hy baş, crouch (sıçrama hazırlığı), howl (uluma)."""
    K = 1.6
    bob, tilt, jaw = p.get('bob', 0.0), p.get('tilt', 0.0), p.get('jaw', 0.0)
    howl = p.get('howl', 0.0)
    crouch = p.get('crouch', 0.0)
    hipp = (-9.5 * K, (-17 + bob - tilt * 6) * K + crouch * 6)
    shp = (8.5 * K, (-18 + bob + tilt * 6) * K + crouch * 6)
    back_dark = lambda lu, lv, px, py: lv < -0.35
    fur_s = lambda lu, lv, px, py: (np.floor(px * 0.5 - py * 0.8) % 5 == 0) & (lv < 0.2)

    def leg(base, a, z, front):
        if front:
            k, f = fk_leg(base, a[0], a[1], 8.5 * K, 9.0 * K)
        else:
            k, f = fk_leg(base, a[0], a[1], 8.0 * K, 9.5 * K)
        mat = SFUR if z > 0 else SFUR_D
        c.capsule(base, k, (3.4 if not front else 3.0) * K, 2.3 * K, mat, z=z)
        c.capsule(k, f, 2.2 * K, 1.7 * K, mat, z=z)
        c.ellipse((f[0] + 1.3 * K, f[1] - 0.8 * K), 2.3 * K, 1.4 * K, mat, z=z + 0.1)
        for i in range(3):
            c.dot((f[0] + (2.6 + i * 0.1) * K, f[1] - 1.6 * K + i * K), M['bone'], z=z + 2)
        return f

    leg(hipp, p['hb'], -8, False)
    leg(shp, p['fb'], -8, True)
    # kuyruk: uzun, uçta kut alevi
    tl = chain((hipp[0] - 4 * K, hipp[1] - 2 * K), 6, 3.6 * K, math.pi * 1.12 + p.get('tw', 0.0), -0.12, p.get('ph', 0.0), 0.25)
    for i, (a, b) in enumerate(zip(tl, tl[1:])):
        c.capsule(a, b, (3.0 - i * 0.3) * K, (2.6 - i * 0.3) * K, SFUR if i < 4 else SMANE, z=-6)
    # gövde
    c.ellipse(hipp, 7.6 * K, 7.0 * K, SFUR, z=0, paint=[(back_dark, SFUR_D), (fur_s, SFUR_D)])
    c.capsule(hipp, shp, 6.3 * K, 7.0 * K, SFUR, z=1, paint=[(back_dark, SFUR_D), (fur_s, SFUR_D)])
    c.ellipse(shp, 8.0 * K, 8.4 * K, SFUR, z=2, paint=[(back_dark, SFUR_D), (fur_s, SFUR_D)])
    # sırt yelesi: kut ışığıyla yanan alev dilleri
    for k, (t, h) in enumerate(((0.1, 7), (0.3, 10), (0.5, 9), (0.7, 8), (0.88, 6))):
        bx, by = lerp2(hipp, shp, t)
        by -= 6.5 * K
        sway = math.sin(p.get('ph', 0.0) + k) * 1.5
        c.poly([(bx - 2.4 * K, by + 2), (bx + 2.4 * K, by + 2), (bx + 0.6 * K + sway, by - h * K)], SMANE, z=6, bevel=1.4, height=2)
    # turkuaz atkı (boyunda)
    c.capsule((shp[0] - 4 * K, shp[1] - 4 * K), (shp[0] + 5 * K, shp[1] - 2 * K), 2.2 * K, 2.0 * K, M['turq'], z=5)
    sc = chain((shp[0] - 5 * K, shp[1] - 3 * K), 4, 4.0 * K, math.pi * 0.95 + p.get('tw', 0.0) * 0.5, 0.05, p.get('ph', 0.0), 0.35)
    for i, (a, b) in enumerate(zip(sc, sc[1:])):
        c.capsule(a, b, (1.8 - i * 0.25) * K, (1.6 - i * 0.25) * K, M['turq'], z=-5)
    # boyun + baş
    hy_off = p.get('hy', 0.0) * K - howl * 10
    head = (shp[0] + 9.5 * K - howl * 3, shp[1] - 6 * K + hy_off)
    c.capsule((shp[0] + 2 * K, shp[1] - 2 * K), head, 5.6 * K, 4.6 * K, SFUR, z=4, paint=[(back_dark, SFUR_D)])
    hx_, hy_ = head
    c.ellipse(head, 5.4 * K, 4.6 * K, SFUR, z=6, paint=[(back_dark, SFUR_D)])
    c.poly([(hx_ - 3.5 * K, hy_ - 2.5 * K), (hx_ - 0.6 * K, hy_ - 3.5 * K), (hx_ - 2.4 * K, hy_ - 9.5 * K)], SFUR, z=7, bevel=1.2, height=1.5)
    c.poly([(hx_ - 0.4 * K, hy_ - 3.6 * K), (hx_ + 2.0 * K, hy_ - 3.0 * K), (hx_ + 0.2 * K, hy_ - 9.0 * K)], SFUR_D, z=6.5, bevel=1.2, height=1.5)
    # burun: ulurken yukarı kalkar
    ang = -howl * 0.9
    sn1 = (hx_ + 2.5 * K + math.cos(ang) * 8 * K, hy_ + 0.6 * K + math.sin(ang) * 8 * K)
    c.capsule((hx_ + 2.5 * K, hy_ + 0.6 * K), sn1, 3.0 * K, 1.9 * K, SFUR, z=8)
    c.ellipse((sn1[0] + 0.5 * K, sn1[1] - 0.4 * K), 1.2 * K, 1.0 * K, M['black'], z=10)
    jd = (jaw + howl * 0.5) * 3.2 * K
    jaw0 = (hx_ + 2.5 * K, hy_ + 3.0 * K)
    jaw1 = (hx_ + 2.5 * K + math.cos(ang + 0.15) * 7 * K, hy_ + 3.0 * K + math.sin(ang + 0.15) * 7 * K + jd)
    c.capsule(jaw0, jaw1, 1.7 * K, 1.1 * K, SFUR_D, z=7.5)
    if jaw + howl > 0.2:
        c.poly([(hx_ + 4 * K, hy_ + 2.6 * K), (sn1[0] - 1, sn1[1] + 2.2 * K), (jaw1[0], jaw1[1] - 1), (hx_ + 4 * K, hy_ + 3.4 * K + jd * 0.5)], M['red_paint'], z=7.4, bevel=0.5, height=0.3)
    for i in range(4):
        c.dot((hx_ + (4.4 + i * 1.6) * K, hy_ + 2.4 * K), M['bone'], z=12, size=2)
    # göz: kut ışığı; savaş boyası
    c.capsule((hx_ + 1.0 * K, hy_ - 1.8 * K), (hx_ + 3.8 * K, hy_ - 1.2 * K), 0.9 * K, 0.8 * K, M['kut'], z=20)
    c.capsule((hx_ + 0.2 * K, hy_ + 0.8 * K), (hx_ + 2.2 * K, hy_ + 2.6 * K), 0.6, 0.6, M['red_paint'], z=14)
    leg(hipp, p['hf'], 8, False)
    leg(shp, p['ff'], 8, True)
    return {'mouth': (sn1[0], sn1[1] + 2 * K)}


def _swolf_run(t):
    ph = t * math.tau
    s, s2 = math.sin(ph), math.sin(ph + 0.6)
    return dict(bob=-abs(math.cos(ph)) * 1.8 + 0.6, tilt=0.14 * math.sin(ph),
                hb=(0.95 * s, 0.9 - 0.4 * s), hf=(0.95 * s2, 0.9 - 0.4 * s2),
                fb=(-0.95 * s + 0.1, 0.2 + 0.8 * max(0, s)), ff=(-0.95 * s2 + 0.1, 0.2 + 0.8 * max(0, s2)), tw=-0.2, ph=ph, jaw=0.2)


SPIRIT_WOLF = {
    'idle': (6, lambda t: dict(bob=0.5 * math.sin(t * 6.28), hb=(0.25, 0.9), hf=(0.1, 0.8), fb=(-0.05, 0.1), ff=(0.08, 0.1), tw=0.1 * math.sin(t * 6.28), ph=t * 6.28, jaw=0.1)),
    'run': (8, _swolf_run),
    'bite': (5, lambda t: [dict(bob=2.0, tilt=-0.12, hb=(0.5, 1.5), hf=(0.4, 1.4), fb=(0.4, 1.0), ff=(0.5, 1.1), tw=0.4, jaw=0.9, hy=1.5, ph=0.0),
                           dict(bob=-1.5, tilt=0.0, hb=(-0.8, 0.3), hf=(-0.7, 0.4), fb=(1.0, 0.2), ff=(1.1, 0.3), tw=-0.3, jaw=1.0, hy=0.5, ph=1.0),
                           dict(bob=-2.0, tilt=0.06, hb=(-1.0, 0.2), hf=(-0.9, 0.3), fb=(1.2, 0.2), ff=(1.3, 0.3), tw=-0.5, jaw=0.0, hy=0.0, ph=2.0),
                           dict(bob=-1.0, tilt=0.04, hb=(-0.6, 0.4), hf=(-0.5, 0.5), fb=(0.9, 0.3), ff=(1.0, 0.3), tw=-0.4, jaw=0.1, hy=0.0, ph=3.0),
                           dict(bob=0.0, tilt=0.0, hb=(0.2, 0.9), hf=(0.1, 0.8), fb=(0.0, 0.2), ff=(0.1, 0.2), tw=0.0, jaw=0.2, hy=0.0, ph=4.0)][min(4, int(t * 5))]),
    'pounce': (4, lambda t: [dict(bob=3.5, tilt=-0.2, crouch=1.0, hb=(0.7, 1.7), hf=(0.6, 1.6), fb=(0.6, 1.3), ff=(0.7, 1.4), tw=0.5, jaw=0.4, hy=2.5),
                             dict(bob=-2.0, tilt=-0.1, hb=(-1.1, 0.3), hf=(-1.0, 0.4), fb=(1.3, 0.2), ff=(1.4, 0.3), tw=-0.5, jaw=1.0, hy=0.0),
                             dict(bob=-2.5, tilt=0.02, hb=(-1.2, 0.2), hf=(-1.1, 0.3), fb=(1.4, 0.2), ff=(1.5, 0.3), tw=-0.6, jaw=1.0, hy=0.0),
                             dict(bob=0.5, tilt=0.1, hb=(0.3, 1.0), hf=(0.2, 0.9), fb=(0.4, 0.6), ff=(0.5, 0.7), tw=0.2, jaw=0.3, hy=0.5)][min(3, int(t * 4))]),
    'howl': (4, lambda t: dict(bob=0.5, tilt=-0.25, hb=(0.4, 1.0), hf=(0.3, 0.9), fb=(0.2, 0.3), ff=(0.3, 0.3), tw=0.6, howl=[0.4, 1.0, 1.0, 0.7][min(3, int(t * 4))], ph=t * 6.28)),
    'hurt': (2, lambda t: dict(bob=1, tilt=0.2, hb=(0.3, 0.9), hf=(0.2, 0.8), fb=(-0.3, 0.3), ff=(-0.2, 0.2), tw=0.6, jaw=0.5, hy=-1)),
}

CREATURES = {
    'kara_boru': (draw_hound, HOUND_ANIMS, (80, 56), (36, 52)),      # Erlik Tazısı
    'cor': (draw_cor, COR_ANIMS, (64, 76), (28, 70)),                # Çor Ruhu
    'agac_iyesi': (draw_iye, IYE_ANIMS, (112, 104), (52, 100)),      # Kara İye
    'balbal': (draw_balbal, BALBAL_ANIMS, (72, 72), (30, 68)),       # Balbal
    'arcura': (draw_kam, KAM_ANIMS, (64, 64), (30, 60)),             # Kara Kam
    'surale': (draw_gul, GUL_ANIMS, (128, 104), (50, 100)),          # Gulyabani
    'bengu_kurt': (bozkurt.draw_bozkurt, bozkurt.BOZKURT_ANIMS, bozkurt.CELL, bozkurt.FEET),
}
import creatures2
CREATURES.update(creatures2.CREATURES2)
import creatures3
CREATURES.update(creatures3.CREATURES3)



def render_creature(name, anim, i):
    draw, anims, cell, feet = CREATURES[name]
    n, fn = anims[anim]
    t = i / n
    p = fn(t)
    c = (VCanvas if name in VOLUME else Canvas)(cell[0], cell[1], feet[0], feet[1])
    if name == 'kara_boru_han':
        c.zscale = 2.3
    if name in ('kara_boru', 'kara_boru_han'):
        c.shade_kw = {'rim_th': 0.42, 'rim_amt': 0.4}   # koyu post: sırtta ay ışığı kenarı hacmi okutur
    info = draw(c, p)
    rgba = c.shade()
    nm = c.normal_map(rgba[..., 3])
    return c, rgba, nm, info
