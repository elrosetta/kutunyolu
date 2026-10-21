"""v39: Erlik Yasavulu (kimlik yasavul) — Tamu'da Erlik Han'ın şeref muhafızı iblis (AI lancer, ateş).

Tasarım: iri, ağır, yere basan boynuzlu iblis muhafız. Kara demir dikenli zırh, çatlaklarından erimiş turuncu kor
sızar (ışır); yakın omuzda öküz kafatası omuzluk, uzak omuzda dikenli demir omuzluk; kapalı boynuzlu miğfer, yatay
yarık siperden turuncu-kızıl ışık; kızıl-kara cüppe önlüğü (tabard) üstünde ışıyan Erlik mührü; pençeli demir
eldivenler, zırhlı baldırlık ve sivri demir çizmeler. Silah: zincir sarılı sapın ucunda yanan kavisli ağız (glaive /
teber): ağzın kenarı akkor, üstünden alevler yükselir.

Satırlar (y39_mizrak_kit ortak tabloları, ağır bedene uyarlı): idle 8 (ağır soluk, alev titrer), move 8 (ağır
yürüyüş, vx), hurt 3, atk_lunge 9 (mk; teber hücum dürtmesi), atk_sweep 8 (mk; baş üstünden yana alevli yarma yayı),
atk_throw 8 (mk; elde beliren ateş ciridi fırlatılır, teber uzak elde dik).
Çapa 'hand' = teber ucu (fırlatmada ateş ciridinin ucu), her karede. Hücre 448x352 (dünya 112x88), ayak (144, 336).
"""
import math

import numpy as np

import inkkit as ik
from inkkit import Ink, INK
from rig import lerp2
import yaratik_govde as yg
import yaratik_ink_kit as yk
import ucan_v29 as u29
import y39_mizrak_kit as mk
from y39_mizrak_kit import along, add, dirv

TEX = 4.0
CELL = (448, 352)      # dünya 112 x 88
FEET = (144, 336)      # dünya (36, 84)

# ------------------------------------------------------------ malzemeler
IRON = Ink('#3c3842', '#19161e', '#847c90', '#0a080c', kind='metal', name='kara demir')
IRON_B = IRON.darker(0.72)
BONE = Ink('#d8ccae', '#83755e', '#fff8e2', '#463a30', name='öküz kafatası')
HORN = Ink('#3a3030', '#171214', '#7a6660', '#0a0808', name='kara boynuz')
TABARD = Ink('#9a1e22', '#480a14', '#d23e32', '#22050a', name='kızıl önlük')
TAB_B = Ink('#2a1418', '#12080a', '#4a2a2c', '#060304', name='kara astar')
LEATHER = Ink('#4a2e26', '#22141a', '#74503e', name='deri')
HAFT = Ink('#2e2626', '#120e10', '#5e5050', name='teber sapı')
CHAIN = Ink('#5a5460', '#24202a', '#a8a0b4', '#100e14', kind='metal', name='zincir')
MOLT = (1.0, 0.56, 0.14)
HOT = (1.0, 0.88, 0.5)
GLOW = (1.0, 0.36, 0.04)
GLOW_R = (0.95, 0.12, 0.04)
STEEL = Ink('#6c6474', '#2e2836', '#c0b8cc', '#141018', kind='metal', name='kara çelik ağız')
EMBER = Ink('#ff8a2a', '#c03c10', '#ffe2a0', name='kor')


def _crack(cv, pts, z, w=1.0, k=1.0):
    """Erimiş kor çatlağı: mürekkep yarığı + içinde ışıyan turuncu çekirdek."""
    cv.stroke(pts, 1.5 * w, z=z, col=INK, taper=(0.3, 0.5))
    cv.stroke(pts, 0.85 * w, z=z + 0.01, col=HOT if k > 0.7 else MOLT, taper=(0.3, 0.5), glow=(GLOW[0] * k, GLOW[1] * k, GLOW[2] * k))


def _zig(a, b, n, amp, seed):
    rng = np.random.default_rng(seed)
    out = [a]
    for i in range(1, n):
        q = lerp2(a, b, i / n)
        out.append((q[0] + rng.uniform(-amp, amp), q[1] + rng.uniform(-amp, amp)))
    out.append(b)
    return out


def _flames(cv, base, ang, L, n, z, ph, seed, w=2.0, up=(0.0, -1.0)):
    """Yükselen alev dilleri: kökü geniş, ucu kıvrılan sarı-turuncu şeritler (ışır)."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        st = base[i] if isinstance(base, list) else base
        ln = L * rng.uniform(0.6, 1.15) * (0.85 + 0.25 * math.sin(ph * 3 + i * 1.9))
        pts = [st]
        x, y = st
        for j in range(4):
            a = math.atan2(up[1], up[0]) + math.sin(ph * 2.5 + i * 1.3 + j * 1.1) * 0.35
            x += math.cos(a) * ln / 4
            y += math.sin(a) * ln / 4
            pts.append((x, y))
        W = [cv.W(q) for q in pts]
        outer = ik.taper_path(W, cv.u(w * rng.uniform(0.8, 1.2)), (0.05, 0.95))
        cv.fill(outer, (0.95, 0.32, 0.06), z=z + i * 0.01, glow=GLOW, alpha=0.95)
        inner = ik.taper_path(W[:4], cv.u(w * 0.5), (0.05, 0.9))
        cv.fill(inner, (1.0, 0.86, 0.42), z=z + 0.005 + i * 0.01, glow=HOT)


class Style:
    H0 = 22.0
    LIFT = 0.0
    TORSO = 17.0
    L_TH, L_SH = 12.0, 11.8
    LANCE = (10.0, 52.0)
    STREAK = (1.0, 0.5, 0.14)
    GLOW = GLOW

    def ground_fx(self, cv, p, J):
        ph = p['ph']
        x0 = min(J['fbt'][0], J['fft'][0]) - 2.0
        x1 = max(J['fbt'][0], J['fft'][0]) + 4.0
        yk.glow_soft(cv, ((x0 + x1) / 2, -0.5), (x1 - x0) * 0.6, GLOW_R, z=-45, blur=0.8, alpha=0.18 + 0.15 * p['flare'], ry=2.5)
        if p['mist'] > 0.02:   # hazırlık: ayak dibinden yükselen kor zerreleri + kızıl hale
            k = p['mist']
            c = (J['hip'][0], J['hip'][1] - 10.0)
            u29.flecks(cv, (c[0], -4.0), int(5 + 10 * k), 2.0, 16.0, EMBER, 40, seed=int(ph * 9) % 31, s0=0.3, s1=0.8, drift=(0.0, -1.0),
                       dk=10.0 * k, glow=GLOW)
            yk.glow_soft(cv, c, 18.0, GLOW_R, z=-46, blur=0.7, alpha=0.3 * k)
        if p['streak'] > 0.3:   # hücum: ayak altında kıvılcım
            yk.sparks(cv, (J['fbt'][0], -0.5), 6, 0.5, 5.0, HOT, -10, seed=int(ph * 5) % 17, w=1.0, glow=GLOW, ang=math.pi * 1.15, spread=1.0)

    def back_layer(self, cv, p, J):
        T = J['T']
        ph = p['ph']
        sk = p['sk']
        hip = J['hip']
        # arka önlük kanadı (kara astar)
        a = T(1.0, -6.0)
        b = (hip[0] - 7.5 + sk * 1.2, hip[1] + 15.0 - abs(sk) * 0.5)
        hem = yk.ragged(b, (hip[0] - 1.0 + sk * 0.6, hip[1] + 16.0), 3, 2.0, seed=3, side=1.0)
        cv.shape(cv.blob([a, T(1.0, 0.0), (hip[0] - 1.0 + sk * 0.6, hip[1] + 16.0, 0.0)] + hem[::-1] + [(b[0], b[1], 0.0)]),
                 TAB_B, z=-14.5, sd=1.6, details=cv.fold([lerp2(a, b, 0.2), lerp2(a, b, 0.8)], 0.8, 1.2, 1))
        yk.glow_soft(cv, T(9.0, 0.0), 16.0, GLOW_R, z=-48, blur=0.75, alpha=0.1 + 0.2 * p['flare'])

    def legs(self, cv, p, J):
        for side in (0, 1):
            near = side == 1
            hj = J['hb'] if side == 0 else J['hf']
            kn = J['kb'] if side == 0 else J['kf']
            f = J['fbt'] if side == 0 else J['fft']
            z = -12.0 if side == 0 else 0.6
            m = IRON if near else IRON_B
            cv.shape(cv.limb([hj, lerp2(hj, kn, 0.5), kn], [4.4, 4.2, 3.4]), LEATHER if near else LEATHER.darker(0.72), z=z, sd=2.0)
            # uyluk levhaları
            th = cv.blob([along(hj, kn, 0.05, -4.2), along(hj, kn, 0.0, 3.6), along(hj, kn, 0.85, 3.4), along(hj, kn, 0.95, -3.6)])
            cv.shape(th, m, z=z + 0.1, sd=1.6, hi=0.4 if near else 0.0,
                     details=[('ink', [along(hj, kn, t, -3.8), along(hj, kn, t + 0.04, 3.4)], 1.0, (0.1, 0.1)) for t in (0.3, 0.55, 0.78)])
            # baldır: zırhlı baldırlık (greave) + kor çatlağı
            sh = cv.limb([kn, lerp2(kn, f, 0.5), f], [3.4, 3.2, 2.6])
            cv.shape(sh, m, z=z + 0.2, sd=1.8, hi=0.45 if near else 0.0, details=[('ink', [along(kn, f, 0.15, 1.6), along(kn, f, 0.85, 1.2)], 0.9, (0.3, 0.3))])
            if near:
                _crack(cv, _zig(along(kn, f, 0.25, -1.0), along(kn, f, 0.7, 0.4), 4, 0.5, 11 + side), z + 0.3, 0.9, 0.8)
            # diz dikeni
            dk = along(kn, f, -0.02, 2.6)
            cv.shape(cv.blob([along(kn, f, -0.15, 1.2), (dk[0] + 2.6, dk[1] - 0.8, 0.0), along(kn, f, 0.12, 1.6)]), m, z=z + 0.35, sd=0.5, hi=0.3, ol=0.85)
            cv.shape(cv.ellipse(kn, 2.6, 2.2), m, z=z + 0.3, sd=0.8, hi=0.4 if near else 0.0, ol=0.9)
            # sivri demir çizme (pençe burun)
            boot = cv.blob([(f[0] - 2.8, f[1] - 3.2), (f[0] + 1.4, f[1] - 3.6), (f[0] + 4.2, f[1] - 1.6), (f[0] + 6.8, f[1] - 0.4, 0.0),
                            (f[0] + 4.4, f[1] + 0.2), (f[0] - 3.0, f[1] + 0.2, 0.0)])
            cv.shape(boot, m, z=z + 0.4, sd=1.2, hi=0.35 if near else 0.0, details=[('ink', [(f[0] + 0.8, f[1] - 3.2), (f[0] + 2.6, f[1] - 0.4)], 0.9)])
            cv.shape(cv.blob([(f[0] - 2.4, f[1] - 2.6), (f[0] - 5.2, f[1] - 1.0, 0.0), (f[0] - 2.4, f[1] - 0.4)]), m, z=z + 0.38, sd=0.4, ol=0.8)

    def torso(self, cv, p, J):
        T = J['T']
        ph = p['ph']
        k = 0.75 + 0.25 * math.sin(ph * 2.0) + 0.3 * p['flare']
        torso = cv.blob([T(-1.0, -7.0), T(4.0, -6.6), T(9.0, -8.4), T(13.4, -9.4), T(16.8, -8.0), T(18.6, -4.0), T(18.8, 2.4),
                         T(16.6, 8.6), T(12.0, 10.0), T(6.5, 8.0), T(2.5, 6.6), T(-1.0, 7.2)])
        det = [('ink', [T(8.5, -8.2), T(9.6, 0.4), T(8.6, 9.0)], 1.3, (0.1, 0.1)),
               ('shade', cv.wedge([T(9.0, -8.0), T(10.0, 0.6), T(9.0, 8.8)], 0.8, 1.0)),
               ('ink', [T(13.8, 6.0), T(11.0, 3.0), T(7.0, 3.6)], 1.0, (0.2, 0.4))]
        for u in (2.6, 5.4):
            det.append(('ink', [T(u, -6.8), T(u - 0.3, 0.4), T(u, 7.2)], 1.1, (0.05, 0.05)))
        cv.shape(torso, IRON, z=2.0, sd=3.6, hi=0.6, details=det, deep=0.25, bounce=0.3)
        # göğüs çatlakları (kor)
        _crack(cv, _zig(T(15.5, 1.0), T(10.5, 4.6), 5, 0.6, 3), 2.4, 1.1, min(1.0, k))
        _crack(cv, _zig(T(12.5, 2.4), T(14.6, 6.6), 3, 0.5, 4), 2.41, 0.9, min(1.0, k))
        _crack(cv, _zig(T(7.0, -3.0), T(4.2, 1.6), 4, 0.5, 5), 2.42, 0.9, min(1.0, k))
        _crack(cv, _zig(T(16.0, -5.0), T(11.5, -2.0), 4, 0.5, 6), 2.43, 1.0, min(1.0, k))
        _crack(cv, _zig(T(11.5, -2.0), T(9.0, 2.0), 3, 0.5, 7), 2.44, 0.8, min(1.0, k))
        yk.glow_soft(cv, T(12.0, 2.0), 6.0, GLOW, z=2.45, blur=0.7, alpha=0.18 * k)
        # göğüs dikenleri
        for (u, v, s) in ((15.4, 7.2, 1.0), (12.0, 8.8, 0.9), (8.0, 7.4, 0.75)):
            b0, b1 = T(u + 1.2 * s, v - 0.2), T(u - 1.2 * s, v + 0.3)
            tip = T(u, v + 3.4 * s)
            cv.shape(cv.blob([b0, (tip[0], tip[1], 0.0), b1]), IRON, z=2.6, sd=0.5, hi=0.3, ol=0.85)
        # kemer + kafatası tokası
        belt = cv.blob([T(-0.8, -7.2), T(2.4, -7.4), T(2.6, 7.6), T(-1.0, 7.4)])
        cv.shape(belt, LEATHER, z=3.0, sd=1.0, hi=0.3, cast=0.5)
        bc = T(0.9, 3.0)
        cv.shape(cv.ellipse(bc, 2.0, 1.8), BONE, z=3.1, sd=0.6, hi=0.3, ol=0.85,
                 details=[('col', cv.ellipse((bc[0] - 0.6, bc[1] - 0.2), 0.45, 0.5), INK), ('col', cv.ellipse((bc[0] + 0.7, bc[1] - 0.2), 0.45, 0.5), INK)])
        # tabard: kızıl önlük, kara kenar, ışıyan Erlik mührü
        hip = J['hip']
        sk = p['sk']
        kf = J['kf']
        top0, top1 = T(0.4, 0.6), T(0.4, 6.6)
        lo1 = (max(top1[0] + 0.5, kf[0] + 1.0) + sk * 0.5, hip[1] + 15.5)
        lo0 = (top0[0] - 1.5 + sk * 1.2, hip[1] + 16.0)
        hem = yk.ragged(lo1, lo0, 3, 2.2, seed=8, side=-1.0)
        tab = cv.blob([top0, top1, (lo1[0], lo1[1], 0.0)] + hem + [(lo0[0], lo0[1], 0.0)])
        tdet = cv.fold([lerp2(top0, lo0, 0.2), lerp2(top0, lo0, 0.9)], 0.7, 1.1, 1)
        tdet.append(('stroke', [(lo1[0] - 0.6, lo1[1] - 1.2)] + [(q[0], q[1] - 1.2) for q in hem[1::2]] + [(lo0[0] + 0.4, lo0[1] - 1.2)], 1.6, TAB_B.base, (0.0, 0.0)))
        cv.shape(tab, TABARD, z=3.3, sd=2.0, hi=0.35, details=tdet, hatch=0.3)
        sc = lerp2(lerp2(top0, top1, 0.5), lerp2(lo0, lo1, 0.5), 0.42)
        g = [((sc[0], sc[1] - 2.4), (sc[0], sc[1] + 2.6)), ((sc[0] - 1.8, sc[1] - 1.6), (sc[0] - 1.6, sc[1] + 1.0), (sc[0], sc[1] + 1.8), (sc[0] + 1.6, sc[1] + 1.0), (sc[0] + 1.8, sc[1] - 1.6)),
             ((sc[0] - 1.2, sc[1] + 3.6), (sc[0] + 1.2, sc[1] + 3.6))]
        for st in g:   # Erlik mührü: üç dişli çatal + taban çizgisi
            cv.stroke(list(st), 1.6, z=3.5, col=INK, taper=(0.1, 0.1))
            cv.stroke(list(st), 0.9, z=3.51, col=HOT, taper=(0.1, 0.1), glow=GLOW)

    def head(self, cv, p, J, hc):
        hx, hy = hc
        ph = p['ph']
        fl = p['flare']
        # boynuzlar: miğferin yanlarından öne-yukarı kıvrılan öküz boynuzları (uzak boynuz arkada)
        for (bx, m, zz, s) in ((-3.2, HORN.darker(0.75), 6.5, 0.9), (0.8, HORN, 10.5, 1.0)):
            b = (hx + bx, hy - 3.2)
            pts = [b, (b[0] - 3.4 * s, b[1] - 0.6 * s), (b[0] - 5.6 * s, b[1] - 3.4 * s), (b[0] - 4.8 * s, b[1] - 7.6 * s), (b[0] - 1.6 * s, b[1] - 10.4 * s),
                   (b[0] + 1.8 * s, b[1] - 11.0 * s)]
            path = ik.taper_path([cv.W(q) for q in pts], cv.u(2.8 * s), prof=lambda u: max(0.06, 1 - 0.92 * u))
            cv.shape(path, m, z=zz, sd=0.8, hi=0.35, ol=0.9,
                     details=[('ink', [lerp2(pts[1], pts[2], t), lerp2(pts[1], pts[2], t + 0.12)], 0.8) for t in (0.2, 0.6)] +
                     [('col', ik.taper_path([cv.W(q) for q in pts[3:]], cv.u(2.2 * s), (0.0, 0.9)), BONE.shadow if s < 1 else BONE.base)])
        # kapalı miğfer: yuvarlak kase, öne çıkık çene siperi
        helm = cv.blob([(hx - 4.6, hy + 4.4), (hx - 5.2, hy - 1.0), (hx - 3.6, hy - 5.2), (hx + 0.6, hy - 6.6), (hx + 4.4, hy - 5.0),
                        (hx + 6.0, hy - 1.4), (hx + 6.6, hy + 2.2, 0.4), (hx + 5.4, hy + 5.4), (hx + 1.0, hy + 6.2)])
        hdet = [('ink', [(hx + 0.4, hy - 6.4), (hx + 1.6, hy - 2.0), (hx + 5.4, hy + 4.8)], 1.0, (0.1, 0.4)),
                ('shade', cv.wedge([(hx - 4.4, hy + 4.0), (hx - 4.8, hy - 1.0), (hx - 3.2, hy - 5.0)], 1.6, -1.0)),
                ('col', cv.ellipse((hx - 2.0, hy + 1.6), 0.5, 0.5), IRON.hi), ('col', cv.ellipse((hx - 2.2, hy + 3.8), 0.5, 0.5), IRON.hi)]
        cv.shape(helm, IRON, z=9.0, sd=2.4, hi=0.6, details=hdet, cast=0.6)
        # tepe dikeni
        cv.shape(cv.blob([(hx - 0.6, hy - 6.0), (hx + 0.2, hy - 10.0, 0.0), (hx + 1.6, hy - 6.2)]), IRON, z=9.1, sd=0.5, hi=0.3, ol=0.85)
        # yarık siper: turuncu-kızıl ışık
        sl = cv.blob([(hx + 0.6, hy - 0.4), (hx + 6.2, hy - 1.0, 0.0), (hx + 6.3, hy + 0.2, 0.0), (hx + 0.8, hy + 0.7)])
        cv.fill(sl, (0.04, 0.01, 0.01), z=9.2)
        w = 0.32 + 0.22 * fl
        cv.fill(cv.blob([(hx + 1.2, hy + 0.15 - w), (hx + 6.0, hy - 0.45, 0.0), (hx + 1.2, hy + 0.15 + w)]), HOT if fl > 0.6 else MOLT, z=9.3, glow=GLOW)
        yk.glow_soft(cv, (hx + 4.0, hy - 0.2), 3.0 + 2.0 * fl, GLOW_R, z=9.35, blur=0.6, alpha=0.45 + 0.35 * fl)
        if fl > 0.3:
            cv.stroke([(hx + 5.6, hy - 0.3), (hx + 2.0, hy - 1.0 - fl * 0.4), (hx - 2.5 - fl * 3.0, hy - 1.6 - fl)], 1.0 + 1.4 * fl, z=9.4,
                      col=MOLT, taper=(0.1, 0.95), glow=GLOW, alpha=0.85)
        # nefes delikleri (çene siperi)
        for i in range(3):
            cv.fill(cv.ellipse((hx + 3.2 + i * 1.0, hy + 3.4), 0.3, 0.45), MOLT, z=9.25, glow=GLOW_R)

    def arm(self, cv, sh, e, h, near, z_up, z_lo, grip=True, d=(1.0, 0.0)):
        m = IRON if near else IRON_B
        up = cv.limb([sh, lerp2(sh, e, 0.5), e], [3.4, 3.2, 2.7])
        cv.shape(up, LEATHER if near else LEATHER.darker(0.72), z=z_up, sd=1.6)
        cv.shape(cv.capsule(lerp2(sh, e, 0.35), lerp2(sh, e, 0.95), 3.1, 2.7), m, z=z_up + 0.1, sd=1.4, hi=0.4 if near else 0.0,
                 details=[('ink', [along(sh, e, t, -3.0), along(sh, e, t, 3.0)], 0.9, (0.1, 0.1)) for t in (0.55, 0.75)])
        fo = cv.limb([e, lerp2(e, h, 0.5), lerp2(e, h, 0.9)], [2.9, 2.8, 2.3])
        cv.shape(fo, m, z=z_lo, sd=1.5, hi=0.45 if near else 0.0, details=[('ink', [along(e, h, 0.2, 2.0), along(e, h, 0.8, 1.6)], 0.8, (0.3, 0.3))])
        if near:
            _crack(cv, _zig(along(e, h, 0.25, -0.8), along(e, h, 0.7, 0.6), 3, 0.4, 21), z_lo + 0.05, 0.8, 0.8)
        # dirsek dikeni
        sp = along(e, h, -0.08, -2.8)
        cv.shape(cv.blob([along(e, h, -0.1, -1.0), (sp[0] - (h[0] - e[0]) * 0.18, sp[1] - (h[1] - e[1]) * 0.18, 0.0), along(e, h, 0.15, -2.2)]), m,
                 z=z_lo + 0.1, sd=0.4, ol=0.85)
        # pençeli eldiven
        ang = math.atan2(d[1], d[0])
        fist = cv.ellipse(h, 2.3, 1.9, ang + (math.pi / 2 if grip else 0.0))
        zf = z_lo + (2.0 if (near and grip) else 0.3)
        cv.shape(fist, m, z=zf, sd=0.7, hi=0.35, ol=0.9)
        nrm = (-d[1], d[0])
        for kk in range(3):
            b = add(add(h, d, (kk - 1) * 1.1), nrm, 1.4)
            tip = add(add(b, nrm, 1.6), d, -0.9)
            cv.shape(cv.blob([add(b, d, -0.45), (tip[0], tip[1], 0.0), add(b, d, 0.45)]), BONE.darker(0.8), z=zf + 0.05, sd=0.2, ol=0.7)
        if near:   # öküz kafatası omuzluk
            # demir omuz kabuğu + üstünde öküz kafatası (yandan: alın arkada, burun öne-aşağı)
            c = along(sh, e, 0.05, 0.0)
            cv.shape(cv.ellipse(c, 4.4, 3.6, 0.15), IRON, z=z_up + 0.6, sd=1.2, hi=0.4, cast=0.4)
            c = (c[0] + 0.4, c[1] - 2.2)
            sk_ = cv.blob([add(c, (-2.6, -1.4)), add(c, (0.4, -2.2)), add(c, (2.6, -1.0)), add(c, (4.4, 0.8)), add(c, (4.6, 2.0)) + (0.0,),
                           add(c, (3.0, 2.2)), add(c, (0.6, 1.6)), add(c, (-2.2, 1.2))])
            sdet = [('col', cv.ellipse(add(c, (0.8, -0.3)), 0.75, 0.6), INK), ('ink', [add(c, (2.4, 0.6)), add(c, (4.0, 1.4))], 0.7),
                    ('col', cv.ellipse(add(c, (4.0, 1.5)), 0.3, 0.25), INK), ('ink', [add(c, (-1.8, 0.8)), add(c, (0.0, 0.9))], 0.6, (0.2, 0.6))]
            cv.shape(sk_, BONE, z=z_up + 0.8, sd=0.9, hi=0.35, details=sdet)
            cv.fill(cv.ellipse(add(c, (0.9, -0.3)), 0.3, 0.25), MOLT, z=z_up + 0.85, glow=GLOW)
            for s_, m_, zz in ((-1, BONE.darker(0.7), z_up + 0.7), (1, BONE.darker(0.9), z_up + 0.9)):   # kafatası boynuzları: yana-yukarı
                b = add(c, (-1.2 + s_ * 0.6, -1.4))
                pts = [b, add(b, (-2.6, -0.8 - s_ * 0.3)), add(b, (-3.8, -2.8)), add(b, (-3.0, -4.6))]
                cv.shape(ik.taper_path([cv.W(q) for q in pts], cv.u(1.2), prof=lambda u: max(0.08, 1 - 0.9 * u)), m_, z=zz, sd=0.3, ol=0.8)
        else:      # uzak omuz: dikenli demir
            c = along(sh, e, 0.05, 0.0)
            cv.shape(cv.ellipse(c, 4.0, 3.4, 0.2), m, z=z_up + 0.6, sd=1.2)
            for a in (-2.2, -1.6, -1.0):
                b0 = add(c, (math.cos(a - 0.25) * 3.0, math.sin(a - 0.25) * 3.0))
                b1 = add(c, (math.cos(a + 0.25) * 3.0, math.sin(a + 0.25) * 3.0))
                tp = add(c, (math.cos(a) * 6.4, math.sin(a) * 6.4))
                cv.shape(cv.blob([b0, (tp[0], tp[1], 0.0), b1]), m, z=z_up + 0.62, sd=0.3, ol=0.8)

    def weapon(self, cv, p, J, butt, tip, z):
        ph = p['ph']
        d = J['d']
        n = (-d[1], d[0])     # sapın "alt" yanı (ekran: d sağa ise n aşağı)
        L = mk.dist(butt, tip)
        bl = 15.0
        bb = add(tip, d, -bl)
        cv.shape(cv.capsule(butt, bb, 0.9, 0.85), HAFT, z=z, sd=0.6, hi=0.25, ol=0.9,
                 details=[('ink', [add(butt, d, s), add(butt, d, s + 1.4)], 0.8) for s in (6.0, 18.0, 30.0)])
        for s in (0.8, L * 0.45):
            q = add(butt, d, s)
            cv.shape(cv.capsule(add(q, d, -0.9), add(q, d, 0.9), 1.25, 1.25), IRON, z=z + 0.05, sd=0.4, hi=0.3, ol=0.8)
        # dipçik dikeni
        cv.shape(cv.blob([add(butt, n, 1.0), add(butt, d, -3.6) + (0.0,), add(butt, n, -1.0)]), IRON, z=z + 0.04, sd=0.3, ol=0.8)
        # sapa sarılı zincir + sarkan uç
        for j in range(5):
            a = add(butt, d, L * 0.52 + j * 2.0)
            cv.stroke([add(a, n, -1.2), add(add(a, d, 1.0), n, 1.2)], 1.3, z=z + 0.1, col=CHAIN.hi)
            cv.stroke([add(a, n, -1.2), add(add(a, d, 1.0), n, 1.2)], 0.6, z=z + 0.11, col=INK)
        ca = add(butt, d, L * 0.62)
        sw = math.sin(ph * 1.4) * 1.5
        yk.chain_links(cv, ca, (ca[0] - 1.0 + sw - d[0] * 2.0, ca[1] + 8.0), 6, CHAIN, z - 0.3, r=0.75)
        # boğaz (soket)
        cv.shape(cv.capsule(add(bb, d, -3.0), add(bb, d, 1.0), 1.5, 1.3), IRON, z=z + 0.15, sd=0.5, hi=0.4, ol=0.85)
        # kavisli ağız: arka sırtta diken, ön kenar akkor
        P = lambda u, v: add(add(bb, d, u), n, v)
        blade = cv.blob([P(-0.5, 1.2), P(3.0, 3.6), P(8.0, 4.8), P(12.5, 3.6), (tip[0] + n[0] * 0.2, tip[1] + n[1] * 0.2, 0.0), P(11.5, -1.4),
                         P(7.0, -2.2), P(4.6, -5.4, ) + (0.0,), P(3.4, -1.8), P(-0.5, -1.0)])
        bdet = [('ink', [P(1.0, 0.0), P(7.0, 0.4), P(11.5, 0.4)], 0.9, (0.1, 0.6)),
                ('shade', cv.wedge([P(1.0, -0.8), P(6.0, -1.6), P(11.0, -1.0)], 0.9, -1.0))]
        cv.shape(blade, STEEL, z=z + 0.2, sd=1.1, hi=0.6, ol=0.95, details=bdet)
        edge = [P(2.0, 3.4), P(6.0, 4.6), P(10.0, 4.1), P(13.4, 2.2), (tip[0], tip[1])]
        cv.stroke(edge, 1.6, z=z + 0.25, col=HOT, taper=(0.4, 0.3), glow=GLOW)
        _crack(cv, [P(3.0, 0.8), P(5.5, 1.6), P(7.5, 1.0)], z + 0.26, 0.7, 1.0)
        # alevler: ağzın sırtından yukarı (dünya yukarısı) yükselir, hızla geriye yatar
        up = (-0.35 * p['streak'] - 0.2 * p['smear'], -1.0)
        _flames(cv, [P(u, 2.0 * math.sin(u / 4.0) - 0.5) for u in (2.0, 5.0, 8.0, 11.0)], 0.0, 7.0 + 2.0 * p['flare'], 4, z + 0.3, ph, 5, w=1.9, up=up)
        yk.glow_soft(cv, P(7.0, 0.0), 8.0, GLOW, z=z + 0.35, blur=0.7, alpha=0.4 + 0.3 * p['flare'])

    def javelin(self, cv, base, ang, k, L, ph, flying=False, trail=0.0):
        d = dirv(ang)
        n = (-d[1], d[0])
        Lk = L * (0.45 + 0.55 * min(1.0, k))
        tip = add(base, d, Lk)
        a = min(1.0, k * 1.3)
        if flying and trail > 0:
            _flames(cv, [add(add(base, d, -1.0), n, (j - 1) * 0.8) for j in range(3)], 0.0, 10.0 * trail + 4.0, 3, 28.8, ph, 9, w=2.2,
                    up=(-d[0], -d[1] - 0.25))
            u29.flecks(cv, add(base, d, -8.0 * trail), 6, 1.0, 6.0, EMBER, 28.7, seed=int(ph * 7) % 23, s0=0.3, s1=0.7, glow=GLOW)
        shaft = ik.taper_path([cv.W(add(base, d, -1.0)), cv.W(add(base, d, Lk * 0.5)), cv.W(add(tip, d, -4.0))], cv.u(1.5), (0.4, 0.1))
        cv.fill(shaft, (0.95, 0.38, 0.08), z=30.0, glow=GLOW, alpha=0.9 * a)
        hd_ = cv.blob([add(add(tip, d, -5.0), n, 1.7), (tip[0], tip[1], 0.0), add(add(tip, d, -5.0), n, -1.7), add(tip, d, -3.4)])
        cv.fill(hd_, (1.0, 0.7, 0.25), z=30.1, glow=GLOW, alpha=a)
        cv.stroke([add(base, d, 1.0), add(tip, d, -0.8)], 0.8, z=30.2, col=HOT, taper=(0.6, 0.3), glow=HOT, alpha=a)
        if not flying:
            _flames(cv, [add(base, d, Lk * u) for u in (0.25, 0.55, 0.8)], 0.0, 4.0 * a + 1.0, 3, 30.3, ph, 13, w=1.4)
        yk.glow_soft(cv, add(base, d, Lk * 0.6), Lk * 0.45, GLOW, z=29.9, blur=0.7, alpha=0.5 * a, ry=Lk * 0.25)
        if k < 0.95 and not flying:
            yk.sparks(cv, add(base, d, Lk * 0.5), 7, 2.0, 6.0 + 4.0 * (1 - k), HOT, 30.4, seed=int(ph * 11) % 40 + 1, w=0.9, glow=GLOW)
        return tip

    def smear(self, cv, c, r, a0, a1, k):
        mk.smear_arc(cv, c, r * 0.84, a0, a1, 10.0 * k, (1.0, 0.42, 0.08), GLOW_R, 11.0, alpha=0.55 * k, hot=(1.0, 0.9, 0.55))
        # yay boyunca kopan alev dilleri
        r_ = r * 0.84
        base = [(c[0] + math.cos(a0 + (a1 - a0) * u) * r_, c[1] + math.sin(a0 + (a1 - a0) * u) * r_) for u in (0.45, 0.65, 0.85)]
        _flames(cv, base, 0.0, 6.0 * k, 3, 11.2, 0.3, 21, w=1.8)


S = Style()


# ------------------------------------------------------------ ağır beden uyarlaması ve döngüler
def _tweak(keys):
    """Ortak pozlar: yasavul daha alçak ve geniş basar (kalça biraz daha aşağı, ayaklar yerde)."""
    out = []
    for t, d, e in keys:
        d = dict(d)
        if 'hy' in d:
            d['hy'] = d['hy'] + 0.6
        if d.get('mode', 0.0) > 0.5:   # fırlatma: teber uzak elde dik; ağız baş üstünde kalsın (sap kısa)
            d['sl'] = 9.0
        out.append((t, d, e))
    return out


def _idle(t):
    p = mk.idle_pose(t, mk.REST)
    s = math.sin(t * math.tau)
    s2 = math.sin(t * math.tau * 2)
    p.update(bob=0.5 * s2, hy=1.4 + 0.5 * s2, fb=(-8.0, 0.0), ff=(6.5, 0.0), gh=(4.0, -9.0 + 0.4 * s2), la=-0.8 + 0.02 * s,
             lean=0.14 + 0.02 * s2, sk=0.3 * s, flare=0.3 + 0.2 * max(0.0, s))
    return p


def _foot(phi, home, S_, duty, lift):
    phi %= 1.0
    if phi < duty:
        u = phi / duty
        return (home + S_ * (0.5 - u), 0.0)
    u = (phi - duty) / (1.0 - duty)
    e = u * u * (3 - 2 * u)
    return (home - S_ * 0.5 + S_ * e, lift * math.sin(math.pi * u) ** 0.9)


STRIDE, DUTY = 16.0, 0.6
_T_WALK = 8 / 10.0


def _move(t):
    p = dict(mk.REST)
    p.update(mk.G)
    c2 = math.cos(t * 4 * math.pi)
    s1 = math.sin(t * math.tau)
    p.update(ff=_foot(t, 1.0, STRIDE, DUTY, 3.6), fb=_foot(t - 0.5, -3.0, STRIDE, DUTY, 3.2), hy=2.0 + 0.9 * c2, hx=0.8, bob=0.3 * c2,
             lean=0.2 + 0.02 * c2, tw=0.08 * s1, gh=(5.0, -9.0 + 0.5 * c2), la=-0.55 + 0.04 * s1, hd=(0.6, 0.6 + 0.4 * c2),
             sk=-0.6 * s1, flare=0.35)
    return p


ROWS = None


def anims_for(var='yasavul'):
    global ROWS
    if ROWS is None:
        ROWS = mk.rows(mk.REST, idle=_idle, move=_move, move_vx=round(STRIDE / (DUTY * _T_WALK), 1), tweak=_tweak)
    return ROWS


def durum_for(var='yasavul'):
    return mk.durum(('lunge', 'sweep', 'throw'))


SHADE = dict(outer=0.5, rim=0.55, rim_col=(1.0, 0.55, 0.3), rim_dir=(0.6, -0.8), rim_w=1.3, form=(7.0, (0.72, 0.68, 0.8)))


def render_frame(anim, i, var='yasavul', ss=3):
    r = anims_for(var)[anim]
    tt = mk.frame_time(r, i)
    p = dict(r['pose'](tt))
    p['ph'] = tt * math.tau * (1 if r['loop'] else 0.7) + (0 if r['loop'] else i * 0.6)
    cv = u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss)
    info = mk.draw(cv, p, S)
    rgba, nm, em = cv.finish(**SHADE)
    return rgba, None, em, {'hand': info['hand'], 'head': info['head']}
