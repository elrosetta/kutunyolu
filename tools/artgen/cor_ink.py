"""Çor Ruhu (kimlik cor) ve biyom çeşitlemeleri — stil v2 "mürekkep-cel". v1: creatures.draw_cor.

v29: tam gövde animasyonu (ucan_v29). Eski satırlar (idle 6, attack 3, hurt 1) tek gövde çiziminde yalnızca kol ve
buhurdanı oynatıyordu. Şimdi her kare bütün gövdeyle kurulur: kefen pivot çevresinde döner, eksen boyunca ezilir /
uzar, kuyruklar / etek / başlık ucu gövdeden gecikir (overlap), buhurdan dünya yerçekimiyle sarkaç gibi salınır.
Dalıcıların (Kurgan Ruhu, Ayaz Çoru, Demir Gaga) sırtından tüylü kanat, Kan Çoru'nun zar kanat çıkar; kanat
çırpışı, katlanmış pike, saplanma, sıyrılıp kalkış çizilir. Rol başına satır düzeni `anims_for(var)`:
  cor (flyer_ranged)                 idle 8, move 8, tele 4, tele_zirh 4, attack 8 (ts/mk), dive 6 (ts/mk), hop 5,
                                     hurt 3, stagger 6, death 9, spawn 7
  kan_yarasasi, kayip_ruh (swarm)    idle 8, move 6, tele 4, tele_zirh 4, attack 9 (süzülüş, ts/mk), hop 5, hurt 3,
                                     stagger 6, death 9, spawn 7
  kara_kus_yavrusu, kaf_kartali,     idle 8, move 6, tele 4, tele_zirh 4, attack 10 (pike, ts/mk), stuck 4, hop 5,
  demir_gaga (diver)                 hurt 3, stagger 6, death 9, spawn 7
Eski kod uyumu: `attack` satırının 0. karesi hazırlık (uyarı) anahtarı, 1. karesi vuruş anahtarıdır (Enemy bugün
`show_frame("attack", 0/1)` ile seçiyor); `mk` = [W, C, H] (hazırlık sonu, temas, etkin evre sonu; Bengü v28 gibi,
0 ve 1 örtük) ve W = ts[1]. Kaçış satırı `hop` (Enemy._tick_evade `_pa(["leap", "hop", ...])` onu seçer; `leap` adı
oyuncunun Ruh Kuşu'nun (SpiritWolf, cor sayfası) saldırı satırı olduğundan kullanılmaz).

'mouth' çapası = buhurdan / fenerin merkezi (mermi oradan çıkar), gövde dönüşümünden geçmiş dünya konumu.
Doku 4 piksel / dünya birimi; hücre dünya 96x88, ayak (38, 80) (v29; eski 80x76).

Tasarım: Türk halk inancında "çor" hastalık getiren kötü ruhtur. Kirli, küllü bir kefene sarınmış, ayaksız süzülen
uzun bir gölge: sivri ucu geriye sarkan başlık, içinde zifiri karanlık ve iki solgun ışık; yırtık kefen kuyrukları,
kemik eller, bileğe bağlanmış çalınmış dilek çaputları (hastalar için ağaca bağlanan bez parçaları). Zincirdeki tunç
buhurdanın kafes pencerelerinden salgın ateşi yanar, sporlu duman tüter.

Çeşitlemeler (VARIANTS; oyunda `<kimlik>_v2` sprite'ı, biyom tonu uygulanmaz):
  cor               Çor Ruhu       (Ötüken)  küllü kefen, salgın yeşili
  kara_kus_yavrusu  Kurgan Ruhu    (Bozkır)  aşı boyalı keçe, sivri Saka börkü, altın ölü maskesi, kehribar ateş,
                                             sırtta kara kuş kanatları
  kan_yarasasi      Kan Çoru       (Şahmeran) kan kızılı yarasa zar kanatlı kefen, kulaklı başlık, kızıl ışık
  kaf_kartali       Ayaz Çoru      (Kaf)     buz mavisi donmuş kefen, kartal tüyü yaka ve ak kartal kanatları, buz sarkıtları
  kayip_ruh         Kayıp Ruh      (Tamu)    soluk mor, saydamlaşan uzun duman kuyrukları, kırık pranga, ruh feneri
  demir_gaga        Demir Gaga     (Tamu)    pas-kara kefen, demir kuş gagası maske, demir bıçak tüylü kanatlar, kor buhurdan
"""
import math

import inkkit as ik
from inkkit import Ink, INK
from rig import fk_arm, lerp2, chain
import yaratik_ink_kit as yk
import ucan_v29 as u29
from ucan_v29 import pose_at, flap

TEX = 4.0
CELL = (384, 352)       # dünya 96 x 88 (v29: kanat çırpışı ve pike sığsın; v28 80 x 76)
FEET = (152, 320)       # dünya (38, 80)

BONE = Ink('#e4dcc4', '#8a7f72', '#fffbec', '#544a48', name='kemik')
BRONZE = Ink('#b98a3e', '#5e3a1c', '#f4d88a', '#33200f', kind='metal', name='tunç')
IRON = Ink('#5e6070', '#2a2a36', '#a0a4b8', '#17171f', kind='metal', name='demir')
GOLD = Ink('#e8b84a', '#8e541c', '#fff2b8', '#4a2a0c', kind='metal', name='altın')


def _v(**kw):
    base = dict(
        robe=Ink('#c3bcae', '#6a6280', '#ece6d6', '#3c3654', name='küllü kefen'),
        robe_b=Ink('#a39cab', '#575170', '#c8c2cc', '#322d48', name='kefen arkası'),
        mantle=Ink('#a59d9a', '#57506c', '#cfc8c0', '#332e48', name='omuz örtüsü'),
        stain=(0.42, 0.52, 0.28), stain_a=0.5,
        fire=(0.74, 1.0, 0.36), fire_hot=(0.93, 1.0, 0.7), glow=(0.45, 0.95, 0.12),
        eye=(0.85, 1.0, 0.55), eye_glow=(0.5, 1.0, 0.2),
        smoke=Ink('#8fa070', '#4e5c40', '#c4d49a', name='salgın dumanı'), smoke_glow=(0.18, 0.4, 0.04),
        metal=BRONZE, bone=BONE, caput=((0.78, 0.22, 0.2), (0.9, 0.86, 0.74), (0.3, 0.42, 0.62)),
        face='void', hood='tip', extra=(), lantern='censer', tail_fade=0.0,
        role='ranged', wing=None, seed=1,
    )
    base.update(kw)
    return base


VARIANTS = {
    'cor': _v(),
    'kara_kus_yavrusu': _v(
        robe=Ink('#c48a4c', '#6c3a2c', '#ecc07a', '#3a1c1a', name='aşı keçe'),
        robe_b=Ink('#8e5a36', '#4a2420', '#b07a4c', '#2a1214', name='keçe arkası'),
        mantle=Ink('#a4342c', '#541a24', '#d4604a', '#2e0c16', name='kızıl keçe'),
        stain=(0.35, 0.22, 0.12), stain_a=0.35,
        fire=(1.0, 0.72, 0.25), fire_hot=(1.0, 0.92, 0.6), glow=(1.0, 0.55, 0.08),
        eye=(1.0, 0.85, 0.4), eye_glow=(1.0, 0.6, 0.1),
        smoke=Ink('#b89a72', '#6a5040', '#e2caa0', name='kurgan tozu'), smoke_glow=(0.4, 0.22, 0.02),
        metal=GOLD, face='gold', hood='cap', role='diver', seed=3,
        wing=dict(style='feather', L=25.0, chord=8.6,
                  cov=Ink('#3a3446', '#18141e', '#6c6480', '#0c0a10', kind='fur', name='kara kuş örtü tüyü'),
                  fea=Ink('#2a2834', '#121018', '#5c5a74', '#08070c', name='kara kuş uçuş tüyü'), sep=(0.78, 0.55, 0.26))),
    'kan_yarasasi': _v(
        robe=Ink('#8e2232', '#3e0c24', '#c8424a', '#22061a', name='kan kefen'),
        robe_b=Ink('#5e1426', '#2c0818', '#7e2232', '#16040e', name='kanat zarı'),
        mantle=Ink('#3a2030', '#1c0e1c', '#5e3a4a', '#0e060e', name='kara örtü'),
        stain=(0.2, 0.02, 0.06), stain_a=0.45,
        fire=(1.0, 0.3, 0.3), fire_hot=(1.0, 0.75, 0.7), glow=(1.0, 0.1, 0.12),
        eye=(1.0, 0.55, 0.5), eye_glow=(1.0, 0.12, 0.1),
        smoke=Ink('#a04656', '#521c30', '#d47a84', name='kan buğusu'), smoke_glow=(0.45, 0.02, 0.05),
        metal=IRON, face='void', hood='ears', extra=('wings',), role='swarm', seed=5,
        caput=((0.18, 0.1, 0.14), (0.62, 0.12, 0.16), (0.18, 0.1, 0.14)),
        wing=dict(style='bat', L=34.0, mem=Ink('#4a1024', '#260612', '#8a2c40', '#120208', name='kanat zarı'),
                  bone=Ink('#b8968e', '#6a4448', '#e8ccc0', '#3a2228', name='kanat kemiği'), vein=(0.42, 0.08, 0.14))),
    'kaf_kartali': _v(
        robe=Ink('#bcd0e4', '#58689a', '#f2f8ff', '#323c6a', name='donmuş kefen'),
        robe_b=Ink('#7e92b4', '#3c4874', '#a8bcd8', '#222a4e', name='buz arkası'),
        mantle=Ink('#e8e2d4', '#7c7a96', '#ffffff', '#4a4864', name='kartal tüyü'),
        stain=(0.6, 0.85, 1.0), stain_a=0.3,
        fire=(0.62, 0.92, 1.0), fire_hot=(0.92, 1.0, 1.0), glow=(0.3, 0.75, 1.0),
        eye=(0.85, 0.98, 1.0), eye_glow=(0.35, 0.8, 1.0),
        smoke=Ink('#cfe4f4', '#6a84b0', '#ffffff', name='ayaz buğusu'), smoke_glow=(0.08, 0.22, 0.42),
        metal=IRON, face='void', hood='tip', extra=('icicles', 'feathers'), role='diver', seed=7,
        caput=((0.36, 0.52, 0.8), (0.92, 0.94, 1.0), (0.36, 0.52, 0.8)),
        wing=dict(style='feather', L=27.0, chord=9.2,
                  cov=Ink('#f2f6fb', '#8c9cc2', '#ffffff', '#56648c', kind='fur', name='ak kartal örtü tüyü'),
                  fea=Ink('#d2e2f2', '#6a80b0', '#f6fbff', '#3a4a78', name='buzlu uçuş tüyü'), sep=(0.32, 0.42, 0.68),
                  glow=None)),
    'kayip_ruh': _v(
        robe=Ink('#9a8cc8', '#4a3c84', '#cec4f0', '#281e52', name='ruh örtüsü'),
        robe_b=Ink('#6a5ca0', '#342a68', '#8e82c0', '#1c1440', name='ruh arkası'),
        mantle=Ink('#7c6eb0', '#3c3072', '#a69ad8', '#20184a', name='ruh örtüsü 2'),
        stain=(0.6, 0.9, 1.0), stain_a=0.25,
        fire=(0.6, 0.95, 1.0), fire_hot=(0.92, 1.0, 1.0), glow=(0.35, 0.8, 1.0),
        eye=(0.85, 1.0, 1.0), eye_glow=(0.3, 0.85, 1.0),
        smoke=Ink('#a8c8f0', '#5466a8', '#e4f0ff', name='ruh buğusu'), smoke_glow=(0.08, 0.3, 0.5),
        metal=IRON, face='mask', extra=('shackle', 'wisps'), lantern='cage', tail_fade=0.7, role='ghost', seed=9,
        caput=((0.5, 0.45, 0.7), (0.8, 0.8, 0.9), (0.5, 0.45, 0.7))),
    'demir_gaga': _v(
        robe=Ink('#7a6c6a', '#3a2c34', '#a69690', '#1c1218', name='kurum kefen'),
        robe_b=Ink('#564a4c', '#2a1e24', '#76686a', '#140c10', name='kefen arkası'),
        mantle=Ink('#8a4426', '#3a1614', '#a85a34', '#1e0a0a', name='pas'),
        stain=(1.0, 0.45, 0.1), stain_a=0.0,
        fire=(1.0, 0.55, 0.15), fire_hot=(1.0, 0.88, 0.5), glow=(1.0, 0.4, 0.04),
        eye=(1.0, 0.82, 0.4), eye_glow=(1.0, 0.45, 0.05),
        smoke=Ink('#6a5a5a', '#2e2428', '#9a8484', name='kurum'), smoke_glow=(0.5, 0.15, 0.0),
        metal=IRON, face='beak', extra=('embers',), role='diver', seed=11,
        caput=((0.5, 0.2, 0.12), (0.3, 0.26, 0.26), (0.5, 0.2, 0.12)),
        wing=dict(style='ice', L=25.0, chord=8.4,
                  cov=Ink('#5a4644', '#261a1c', '#8c6c60', '#140c0e', name='pas örtü'),
                  fea=Ink('#6a6c7c', '#2a2a36', '#b0b4c8', '#17171f', kind='metal', name='demir bıçak tüy'), sep=(1.0, 0.5, 0.12))),
}


def _tail(cv, start, n, seg, ang, ph, mat, z, w0, seed, fade=0.0, glow=None, wave=0.5):
    pts = chain(start, n, seg, ang, 0.1, ph, wave)
    W = [cv.W(q) for q in pts]
    path = ik.taper_path(W, cv.u(w0), prof=lambda u: max(0.08, (1.0 - min(1.0, u)) ** 0.8 * (0.9 + 0.25 * math.sin(u * 9 + seed))))
    # yırtık uç: iki diş
    e, e1 = pts[-1], pts[-2]
    dx, dy = e[0] - e1[0], e[1] - e1[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    fork = cv.blob([(e1[0] + nx * 1.2, e1[1] + ny * 1.2), (e[0] + nx * 1.6 + dx * 0.3, e[1] + ny * 1.6 + dy * 0.3, 0.0),
                    (e1[0] + dx * 0.4, e1[1] + dy * 0.4)])
    path = ik.union(path, fork)
    det = [('ink', [pts[1], lerp2(pts[1], pts[3], 0.5), pts[3]], 1.1, (0.3, 0.6))]
    if fade > 0:   # kuyruk ucu saydamlaşır (kayıp ruh): önce çiz, sonra silgi
        cv.shape(path, mat, z=z, sd=1.6, hi=0.25, details=det, ol=0.8, glow=glow)
        er = ik.taper_path(W[len(W) // 2:], cv.u(w0 * 2.2), (0.6, 0.0))

        def fn(c, er=er):
            import skia
            p = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, fade))
            p.setBlendMode(skia.BlendMode.kDstOut)
            p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.BlurStyle.kNormal_BlurStyle, cv.u(2.0)))
            c.drawPath(er, p)
        cv._q(z + 0.05, fn)
    else:
        cv.shape(path, mat, z=z, sd=1.6, hi=0.25, details=det, ol=0.9)
    return pts


def _sleeve(cv, sh, e, h, mat, z, r0, r1, seed, near):
    """Bol yen: omuzdan dirseğe genişler, bileğin üstünde yırtık ağızla biter."""
    mouth_c = lerp2(e, h, 0.25)
    dx, dy = mouth_c[0] - sh[0], mouth_c[1] - sh[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    a = (mouth_c[0] + nx * r1, mouth_c[1] + ny * r1)
    b = (mouth_c[0] - nx * r1 * 1.15, mouth_c[1] - ny * r1 * 1.15 + 1.5)
    edge = yk.ragged(a, b, 3, 1.6, seed=seed, side=-1.0)
    pts = [(sh[0] + nx * r0, sh[1] + ny * r0), lerp2((sh[0] + nx * r0, sh[1] + ny * r0), a, 0.5), a] + edge + [b,
           lerp2((sh[0] - nx * r0, sh[1] - ny * r0), b, 0.5), (sh[0] - nx * r0, sh[1] - ny * r0), (sh[0] - dx / L * r0, sh[1] - dy / L * r0)]
    path = cv.blob(pts)
    det = cv.fold([lerp2(sh, mouth_c, 0.25), lerp2(sh, mouth_c, 0.6), (mouth_c[0] - nx * 0.6, mouth_c[1] - ny * 0.6)], 0.7, 1.2, 1)
    det += [('deep', cv.ellipse(lerp2(a, b, 0.5), 1.4, r1 * 0.9, math.atan2(dy, dx)))]
    cv.shape(path, mat, z=z, sd=1.8, hi=0.3 if near else 0.0, details=det, hatch=0.4 if near else 0.0)
    return mouth_c


def _caput(cv, at, V, z, ph, k0=0):
    """Bileğe bağlı dilek çaputları: kısa incelen bez şeritler."""
    for k in range(3):
        col = V['caput'][(k + k0) % len(V['caput'])]
        a = math.pi * 0.5 + (k - 1) * 0.35 + math.sin(ph + k * 1.7) * 0.15
        L = 3.2 + (k % 2) * 1.4
        e = (at[0] + math.cos(a) * L - 0.6, at[1] + math.sin(a) * L)
        m = lerp2(at, e, 0.5)
        pts = [at, (m[0] + math.sin(ph + k) * 0.5, m[1]), e]
        cv.shape(ik.taper_path([cv.W(q) for q in pts], cv.u(1.0), (0.05, 0.4)), Ink(col), z=z + k * 0.01, sd=0.35, ol=0.65)


def _lantern(cv, cen, V, z, flare, t):
    """Buhurdan (tunç/demir kafes, pencerelerinden ateş) ya da ruh kafesi."""
    M = V['metal']
    cx, cy = cen
    gl, hot, fire = V['glow'], V['fire_hot'], V['fire']
    if V['lantern'] == 'cage':
        # ruh kafesi: demir çubuklar, içinde süzülen ruh alevi
        yk.glow_soft(cv, (cx, cy + 0.3), 7.0 + flare * 3.0, gl, z=z, blur=0.55, alpha=0.5 + 0.3 * flare)
        body = cv.ellipse((cx, cy + 0.4), 3.3, 4.0)
        cv.shape(body, Ink(fire), z=z, flat=True, ol=0.0, glow=gl)
        fl = cv.blob([(cx - 1.8, cy + 2.4), (cx - 0.6, cy - 1.0), (cx - 0.2, cy - 3.6 - flare, 0.0), (cx + 1.2, cy - 0.4), (cx + 1.8, cy + 2.4)])
        cv.fill(fl, hot, z=z + 0.2, glow=hot)
        for k in range(5):
            x = cx - 3.0 + k * 1.5
            bow = 1.0 - ((k - 2) / 2.4) ** 2
            cv.shape(ik.taper_path([cv.W((x * 0.9 + cx * 0.1, cy - 3.4)), cv.W((cx + (x - cx) * (1.0 + 0.25 * bow), cy + 0.4)), cv.W((x * 0.9 + cx * 0.1, cy + 4.2))],
                                   cv.u(0.6), (0.0, 0.0)), M, z=z + 0.5, sd=0.3, hi=0.15, ol=0.6)
        cv.shape(cv.ellipse((cx, cy - 3.6), 2.6, 0.9), M, z=z + 0.6, sd=0.5, hi=0.3)
        cv.shape(cv.ellipse((cx, cy + 4.3), 2.4, 0.8), M, z=z + 0.6, sd=0.5, hi=0.3)
        cv.shape(cv.ellipse((cx, cy - 4.8), 0.8, 0.8), M, z=z + 0.7, sd=0.3)
        return
    yk.glow_soft(cv, (cx, cy + 0.6), 6.5 + flare * 3.5, gl, z=z, blur=0.55, alpha=0.45 + 0.35 * flare)
    # gövde: çömlek biçimi, alt sivri uç, kulplar
    pot = cv.blob([(cx - 3.6, cy - 1.4), (cx - 3.9, cy + 1.2), (cx - 2.6, cy + 3.6), (cx - 0.8, cy + 4.6), (cx, cy + 6.4, 0.0),
                   (cx + 0.8, cy + 4.6), (cx + 2.6, cy + 3.6), (cx + 3.9, cy + 1.2), (cx + 3.6, cy - 1.4)])
    wins = []
    for k in range(3):
        x = cx - 2.1 + k * 2.1
        wins.append(cv.blob([(x - 0.55, cy - 0.8), (x + 0.55, cy - 0.8), (x + 0.6, cy + 1.6), (x, cy + 2.6 - abs(k - 1) * 0.5, 0.0), (x - 0.6, cy + 1.6)]))
    win = ik.union(*wins)
    det = [('col', win, fire), ('ink', [(cx - 3.4, cy + 2.9), (cx, cy + 3.5), (cx + 3.4, cy + 2.9)], 1.0)]
    cv.shape(pot, M, z=z, sd=1.3, hi=0.4, details=det)
    cv.fill(ik.isect(win, ik.moved(win, cv.u(0.3), cv.u(0.2))), hot, z=z + 0.05, glow=gl)
    # rim + kubbe kapak + tepe çubuğu
    cv.shape(cv.ellipse((cx, cy - 1.6), 4.1, 1.0), M, z=z + 0.2, sd=0.6, hi=0.35)
    lid = cv.blob([(cx - 3.0, cy - 2.0), (cx - 2.2, cy - 3.8), (cx, cy - 4.8), (cx + 2.2, cy - 3.8), (cx + 3.0, cy - 2.0)])
    holes = ik.union(*[cv.ellipse((cx - 1.4 + k * 1.4, cy - 3.0), 0.38, 0.5) for k in range(3)])
    cv.shape(lid, M, z=z + 0.3, sd=0.8, hi=0.35, details=[('col', holes, fire)])
    cv.fill(holes, hot, z=z + 0.35, glow=gl)
    cv.shape(cv.blob([(cx - 0.5, cy - 4.6), (cx, cy - 7.0, 0.0), (cx + 0.5, cy - 4.6)]), M, z=z + 0.4, sd=0.3, hi=0.2, ol=0.7)
    cv.shape(cv.ellipse((cx, cy - 5.0), 0.8, 0.8), M, z=z + 0.45, sd=0.3, hi=0.2, ol=0.7)
    # kulp halkaları
    for s in (-1, 1):
        ring = ik.diff(cv.ellipse((cx + s * 4.1, cy - 0.6), 1.1, 1.3), cv.ellipse((cx + s * 4.1, cy - 0.6), 0.5, 0.7))
        cv.shape(ring, M, z=z + 0.25, sd=0.3, hi=0.2, ol=0.7)


def _wings(cv, p, V, hx, cy):
    """Sırttan çıkan kanatlar (iki kanat da kefenin arkasında: yakın kanat açık tonda ve biraz önde, uzak kanat koyu,
    yukarı-geride ve küçük). p: ws (konum -1 yukarı .. 1 aşağı), wf (katlanma), wsp (uç tüy aralığı), wl (gecikme)."""
    W = V['wing']
    s, fold, spread, lag = p.get('ws', 0.0), p.get('wf', 0.0), p.get('wsp', 0.5), p.get('wl', 0.0)
    ph = p.get('t', 0.0) * math.tau
    far_s = max(-1.0, min(1.0, s * 0.92 + p.get('wfar', 0.0)))
    if W['style'] == 'bat':
        mats = (W['mem'], W['bone'], W['vein'])
        dk = (W['mem'].darker(0.62), W['bone'].darker(0.7), W['vein'])
        u29.bat_wing(cv, (hx - 6.5, cy - 9.5), far_s, fold, W['L'] * 0.86, lag, dk, z=-9.5, near=False, flank=(hx - 7.5, cy + 1.0), ph=ph + 0.4)
        # yakın zar kanat kefenin ÖNÜNDE (kırmızı kefenin arkasında okunmuyordu); baş / yüz / ön kol yine üstte
        u29.bat_wing(cv, (hx - 3.0, cy - 8.0), s, fold, W['L'], lag, mats, z=7.0, near=True, flank=(hx - 2.0, cy + 2.0), ph=ph)
        return
    mats = (W['cov'], W['fea'], W['sep'])
    dk = (W['cov'].darker(0.66), W['fea'].darker(0.66), W['sep'])
    u29.feather_wing(cv, (hx - 6.8, cy - 10.0), far_s, fold, spread, W['L'] * 0.88, W['chord'] * 0.92, lag, dk, z=-9.6, near=False,
                     seed=V['seed'] + 1, ph=ph + 0.5, style=W['style'])
    u29.feather_wing(cv, (hx - 4.0, cy - 8.4), s, fold, spread, W['L'], W['chord'], lag, mats, z=-3.6, near=True,
                     seed=V['seed'], ph=ph, style=W['style'])


def draw(cv, p, V):
    t = p.get('t', 0.0)
    ph = t * math.tau
    bob = p.get('bob', 0.0)
    lean = p.get('lean', 0.0)
    att = p.get('att', 0.0)
    flare = p.get('flare', 0.0)
    hurt = p.get('hurt', 0.0)
    rot = p.get('rot', 0.0)
    off = p.get('off', (0.0, 0.0))
    cx, cy = 0.0, -29 + bob
    hx = cx + lean * 3
    R, RB, MT = V['robe'], V['robe_b'], V['mantle']
    ex = V['extra']
    # ---- dünya uzayında: hız çizgileri, zerreler (gövde dönüşümünden önce)
    if p.get('streak', 0.0) > 0:
        d = p.get('sdir', (1.0, 0.0))
        u29.speed_lines(cv, (off[0] - d[0] * 6.0, cy + off[1] - d[1] * 6.0), d, n=6, L=16.0 * p['streak'], spread=14.0, w=1.8,
                        col=V['robe'].shadow, alpha=0.5 * min(1.0, p['streak']), z=-40, seed=int(t * 50) + V['seed'])
    if p.get('ash', 0.0) > 0:
        u29.flecks(cv, (off[0], cy + off[1] - 6), int(14 * p['ash']) + 3, 4.0, 13.0, V['smoke'], 60, seed=V['seed'] + int(t * 20),
                   s0=0.35, s1=1.0, drift=(0.0, -1.0), dk=10.0 * p['ash'])
        u29.flecks(cv, (off[0], cy + off[1] - 4), int(8 * p['ash']) + 2, 3.0, 11.0, V['fire_hot'], 61, seed=V['seed'] + 40 + int(t * 20),
                   s0=0.25, s1=0.6, drift=(0.3, -1.0), dk=14.0 * p['ash'], glow=V['glow'])
    if p.get('smoke_in', 0.0) > 0:   # doğuş: dört yandan toplanan duman telleri
        k = p['smoke_in']
        for i in range(5):
            a = i / 5 * math.tau + 0.4
            r = 9.0 + 14.0 * k
            st = (off[0] + math.cos(a) * r, cy + off[1] - 6 + math.sin(a) * r * 0.7)
            yk.wisp(cv, st, a + math.pi + 0.5, 9.0 + 8.0 * k, 2.4 + 1.2 * k, V['smoke'], -20 + i * 0.1, ph=ph + i, curl=0.9,
                    alpha=0.6 * min(1.0, k * 1.5), glow=V['smoke_glow'], glow_a=0.6, ink=True)
    u29.body_xf(cv, (cx, cy - 3.0), rot, p.get('sx', 1.0), p.get('sy', 1.0), off, p.get('skew', 0.0))
    if p.get('zirh', 0.0) > 0:
        u29.armor_aura(cv, (hx, cy - 7.0), 26.0, p['zirh'], z=-45, seed=V['seed'])
    if V['role'] == 'ghost':   # ruh halesi: gövdeyi saran soluk ışık
        yk.glow_soft(cv, (hx, cy - 4.0), 15.0, V['glow'], z=-44, blur=0.7, alpha=0.18 + 0.2 * flare)
    if V['wing'] is not None:
        _wings(cv, p, V, hx, cy)
    # ---- kefen kuyrukları: arkada yırtık şeritler (kumaş gibi geniş kök, gövdeden gecikerek dalgalanır)
    ta = p.get('tail_a', 0.86)
    tw = p.get('tail_w', 0.5)
    tl = p.get('tail_l', 1.0)
    tph = ph * p.get('tail_k', 1.0) + p.get('tail_ph', 0.0)
    _tail(cv, (cx - 7.5, cy + 5), 6, 3.4 * tl, math.pi * ta - lean * 0.4, tph, RB, -6, 7.0, 0.0, fade=V['tail_fade'], wave=tw)
    if 'wisps' in ex:   # kayıp ruh: iki uzun duman kuyruğu daha (saydamlaşan)
        _tail(cv, (cx - 4.0, cy + 9), 7, 3.6 * tl, math.pi * (ta - 0.06), tph + 1.7, R, -6.5, 5.0, 2.1, fade=0.85, wave=tw * 1.2)
        _tail(cv, (cx - 9.5, cy + 2), 6, 3.2 * tl, math.pi * (ta + 0.07), tph + 3.1, MT, -7.0, 4.6, 3.7, fade=0.85, wave=tw * 1.1)
    # ---- arka kol: yen + kemik pençe
    ab = p.get('ab', (1.2, 0.6))
    shb = (hx - 3.5, cy - 6)
    e, h = fk_arm(shb, ab[0], ab[1], 5.5, 5.5)
    m_ = _sleeve(cv, shb, e, h, RB, -8, 2.4, 3.0, 11, False)
    cv.shape(cv.limb([m_, h], [0.75, 0.6]), V['bone'], z=-8.5, sd=0.4)
    a = ab[0] + ab[1]
    yk.bone_hand(cv, h, math.pi / 2 - a, V['bone'], -8.4, n=4, L=4.0, spread=0.35 + p.get('claw', 0.0) * 0.25, curl=0.55 - p.get('claw', 0.0) * 0.4, r=0.36)
    # ---- kefen gövde: omuzdan aşağı daralır, yırtık etek
    fw = p.get('fw', math.sin(ph + 0.8) * 1.2)
    hem = [(cx + 8.0, cy + 2.0), (cx + 7.2, cy + 7.0)] + yk.ragged((cx + 6.0, cy + 9.0), (cx - 13.0 + fw, cy + 15.0 - fw * 0.3), 5, 5.0, seed=3, side=1.0) + \
        [(cx - 14.5 + fw * 1.3, cy + 13.0 - fw * 0.4, 0.0), (cx - 11.0, cy + 4.0), (cx - 9.5, cy - 1.0)]
    body = cv.blob([(hx - 7.0, cy - 9.0), (hx + 6.0, cy - 9.0), (cx + 8.2, cy - 2.0)] + hem)
    fold = []
    fold += cv.fold([(hx + 2.0, cy - 7.0), (cx + 2.8, cy - 1.0), (cx + 3.4, cy + 7.0)], 1.0, 1.4, -1)
    fold += cv.fold([(hx - 3.0, cy - 7.0), (cx - 3.0, cy + 0.0), (cx - 1.5, cy + 8.5)], 1.1, 1.4, 1)
    fold += cv.fold([(cx - 6.5, cy - 2.0), (cx - 6.0, cy + 4.0), (cx - 5.0 + fw * 0.4, cy + 8.0)], 0.8, 1.2, 1)
    if V['stain_a'] > 0:   # salgın lekesi: etekten yukarı sızan ıslak leke
        st = V['stain']
        stain = cv.blob([(cx - 9, cy + 2), (cx - 4, cy - 1.5), (cx + 1, cy + 1.5), (cx + 6, cy - 0.5), (cx + 9, cy + 3), (cx + 9, cy + 14), (cx - 9, cy + 14)])
        fold.append(('fn', lambda c, s=stain, st=st: c.drawPath(s, yk.paint(st, V['stain_a'], cv.u(0.8)))))
    for (hx_, hy_, rr) in ((cx - 4.5, cy + 3.5, 1.6), (cx + 3.2, cy + 7.0, 1.2), (cx - 9.0, cy + 9.5, 1.0)):
        hole_ = cv.blob(yk.ragged((hx_ - rr, hy_), (hx_ + rr, hy_), 2, rr * 0.9, seed=int(hx_ * 7) % 97, side=-1.0) +
                        yk.ragged((hx_ + rr, hy_), (hx_ - rr, hy_), 2, rr * 0.9, seed=int(hy_ * 5) % 89, side=-1.0))
        fold.append(('col', hole_, INK))
    cv.shape(body, R, z=0, sd=3.2, hi=0.45, details=fold, hatch=0.35, bounce=0.35)
    # göğüste kemik muska + ip
    cord = [(hx - 5.5, cy - 7.5), (hx - 1.0, cy - 4.2), (hx + 4.5, cy - 7.0)]
    cv.stroke(cord, 1.0, z=5.5, col=(0.35, 0.28, 0.24), taper=(0.0, 0.0))
    am = (hx - 1.0 + p.get('amul', 0.0), cy - 3.2)
    cv.shape(cv.blob([(am[0] - 1.0, am[1]), (am[0] + 1.0, am[1]), (am[0] + 0.6, am[1] + 2.6), (am[0], am[1] + 3.4, 0.0), (am[0] - 0.6, am[1] + 2.6)]),
             V['metal'] if V['face'] == 'gold' else V['bone'], z=5.6, sd=0.5, hi=0.3, ol=0.8,
             details=[('ink', [(am[0], am[1] + 0.6), (am[0], am[1] + 2.4)], 0.9)])
    # ---- omuz örtüsü (pelerin): yırtık kenarlı kısa katman
    mf = p.get('mf', 0.0)   # pelerin savrulması (+ arkaya-yukarı)
    mpts = [(hx - 8.2, cy - 10.0), (hx + 6.4, cy - 10.5), (hx + 7.8, cy - 6.0)] + \
        yk.ragged((hx + 7.0, cy - 4.5), (hx - 9.0 - mf * 1.5, cy - 3.5 - mf * 2.0), 4, 2.4, seed=7, side=1.0) + [(hx - 9.8 - mf * 1.8, cy - 6.5 - mf * 1.5)]
    mdet = cv.fold([(hx - 1.0, cy - 9.0), (hx - 0.5, cy - 6.0), (hx + 0.5, cy - 3.2)], 0.7, 1.2, 1)
    if 'feathers' in ex:   # kartal tüyü yaka: üst üste binen sivri tüyler
        mpts = [(hx - 8.2, cy - 10.0), (hx + 6.4, cy - 10.5), (hx + 8.4, cy - 6.0)] + \
            yk.ragged((hx + 8.0, cy - 4.5), (hx - 10.0 - mf * 1.5, cy - 2.5 - mf * 2.0), 6, 4.2, seed=8, side=1.0) + [(hx - 10.5 - mf * 1.8, cy - 6.5 - mf * 1.5)]
        for j in range(6):
            x0 = hx + 6.0 - j * 2.7
            mdet.append(('ink', [(x0, cy - 7.5), (x0 - 0.4, cy - 4.5 + (j % 2)), (x0 - 0.9, cy - 2.0 + (j % 2) * 1.2)], 0.9, (0.2, 0.7)))
            mdet.append(('stroke', [(x0 - 0.7, cy - 7.0), (x0 - 1.0, cy - 4.0)], 1.2, MT.shadow, (0.3, 0.6)))
    cv.shape(cv.blob(mpts), MT, z=6, sd=1.8, hi=0.4, details=mdet, fur=0.6 if 'feathers' in ex else 0.0)
    if 'icicles' in ex:
        yk.icicles(cv, [(hx + 6.5, cy - 4.5), (hx + 3.0, cy - 3.0), (hx - 1.0, cy - 2.6), (hx - 5.0, cy - 2.4)], Ink('#e8f6ff', '#7aa0d0', '#ffffff'), 6.5, L=3.0, w=0.7, seed=4)
        yk.icicles(cv, [(cx + 6.5, cy + 3.0), (cx + 3.0, cy + 7.0), (cx - 2.0, cy + 7.5), (cx - 6.5, cy + 5.5)], Ink('#e8f6ff', '#7aa0d0', '#ffffff'), 1.0, L=3.5, w=0.8, seed=5)
    # ---- başlık (ucu gövdeden gecikir: hlag)
    tip_y = cy - 13 + p.get('hlag', 0.0) - lean * 2
    tip_x = hx - 14.5 - abs(p.get('hlag', 0.0)) * 0.3
    hdx = p.get('hdx', 0.0)    # baş öne / arkaya (gövdeden ayrı)
    hdy = p.get('hdy', 0.0)
    hx2, cy2 = hx + hdx, cy + hdy
    if V['hood'] == 'cap':     # Saka börkü: dimdik sivri keçe külah, altın plakalı
        hood = cv.blob([(hx - 6.5, cy - 6), (hx2 - 8.0, cy2 - 13), (hx2 - 6.0, cy2 - 19), (hx2 - 4.0, cy2 - 25.0), (hx2 - 4.5 + p.get('hlag', 0.0) * 0.4, cy2 - 33.0, 0.0),
                        (hx2 + 0.5, cy2 - 26.0), (hx2 + 5.8, cy2 - 21.5), (hx2 + 8.5, cy2 - 15.5), (hx + 8, cy - 9), (hx + 5, cy - 5)])
    elif V['hood'] == 'ears':  # kulaklı başlık (yarasa): kulaklar da gecikir
        el = p.get('hlag', 0.0) * 0.6
        hood = cv.blob([(hx - 6.5, cy - 6), (hx2 - 9, cy2 - 13), (hx2 - 8.5, cy2 - 19), (hx2 - 7.5 - el, cy2 - 29.0 + abs(el) * 0.5, 0.0), (hx2 - 3.5, cy2 - 23.0),
                        (hx2 + 0.0, cy2 - 24.0), (hx2 + 3.0 - el * 0.7, cy2 - 31.0 + abs(el) * 0.4, 0.0), (hx2 + 5.0, cy2 - 22.5), (hx2 + 8.5, cy2 - 15.5), (hx + 8, cy - 9), (hx + 5, cy - 5)])
    else:
        hood = cv.blob([(hx - 6.5, cy - 6), (hx2 - 9, cy2 - 13), (tip_x + hdx, tip_y + hdy, 0.0), (hx2 - 8.5, cy2 - 19), (hx2 - 4, cy2 - 23.5),
                        (hx2 + 1.5, cy2 - 24.5), (hx2 + 6, cy2 - 21.5), (hx2 + 8.5, cy2 - 15.5), (hx + 8, cy - 9), (hx + 5, cy - 5)])
    hx, cy_h = hx2, cy2
    hdet = cv.fold([(hx - 5.0, cy_h - 21.0), (hx - 3.0, cy_h - 16.0), (hx - 3.5, cy - 9.0)], 1.0, 1.3, 1)
    hdet += cv.fold([(hx - 9.0, cy_h - 13.5), (hx - 6.0, cy_h - 12.0), (hx - 4.5, cy - 8.0)], 0.6, 1.1, 1)
    if V['hood'] == 'cap':
        for j in range(3):
            q = (hx - 3.8 + j * 0.2, cy_h - 28.0 + j * 4.0)
            hdet.append(('col', cv.blob([(q[0] - 1.0, q[1]), (q[0], q[1] - 1.2), (q[0] + 1.0, q[1]), (q[0], q[1] + 1.2)]), GOLD.base))
    cv.shape(hood, R, z=4, sd=3.0, hi=0.5, details=hdet, hatch=0.3, bounce=0.3, cast=0.8)
    # başlık ağzı
    oc = (hx + 4.2, cy_h - 14.0)
    lip = cv.ellipse(oc, 4.6, 6.0, 0.2)
    cv.shape(lip, MT if V['hood'] != 'cap' else R, z=10, sd=1.0, hi=0.4, ol=0.8)
    hole = cv.ellipse((oc[0] + 0.5, oc[1] + 0.4), 3.6, 5.0, 0.2)
    cv.fill(hole, INK, z=11)
    if flare > 0:
        yk.glow_soft(cv, (oc[0] + 1.0, oc[1] + 1.0), 3.5, V['eye_glow'], z=11.1, blur=0.6, alpha=0.2 * flare)
    ey = oc[1] - 1.4
    er = (1.0 + 0.35 * flare - 0.4 * hurt) * p.get('eyes', 1.0)
    face = V['face']
    if er > 0.05:
        if face == 'gold':      # altın ölü maskesi
            mask = cv.blob([(oc[0] - 2.4, oc[1] - 3.6), (oc[0] + 3.2, oc[1] - 3.8), (oc[0] + 3.6, oc[1] + 0.5), (oc[0] + 2.4, oc[1] + 3.8),
                            (oc[0] + 0.5, oc[1] + 4.6, 0.0), (oc[0] - 1.6, oc[1] + 3.2), (oc[0] - 2.6, oc[1] - 0.5)])
            slits = ik.union(cv.ellipse((oc[0] - 0.6, ey + 0.1), 1.1, 0.4, -0.1), cv.ellipse((oc[0] + 2.2, ey), 1.0, 0.4, 0.1))
            mdet = [('col', slits, INK), ('ink', [(oc[0] + 0.8, ey + 0.4), (oc[0] + 1.4, oc[1] + 1.6), (oc[0] + 0.7, oc[1] + 2.0)], 0.9),
                    ('ink', [(oc[0] - 0.6, oc[1] + 2.8 + att), (oc[0] + 2.2, oc[1] + 2.7 + att)], 1.0 + att * 0.8, (0.2, 0.2))]
            cv.shape(mask, GOLD, z=12, sd=1.0, hi=0.4, details=mdet)
            yk.eye_glow(cv, (oc[0] - 0.6, ey + 0.1), 0.7 * er, 0.28 * er, -0.1, V['eye'], V['eye_glow'], 13)
            yk.eye_glow(cv, (oc[0] + 2.2, ey), 0.65 * er, 0.28 * er, 0.1, V['eye'], V['eye_glow'], 13)
        elif face == 'beak':    # demir kuş gagası maske (saldırıda gaga açılır)
            mask = cv.blob([(oc[0] - 2.0, oc[1] - 3.6), (oc[0] + 2.8, oc[1] - 3.4), (oc[0] + 4.0, oc[1] - 1.0), (oc[0] + 12.5, oc[1] + 2.4 - att * 0.8, 0.0),
                            (oc[0] + 3.4, oc[1] + 2.4), (oc[0] - 1.0, oc[1] + 3.0)])
            mdet = [('ink', [(oc[0] + 3.4, oc[1] + 0.3), (oc[0] + 8.0, oc[1] + 1.6 - att * 0.4), (oc[0] + 12.0, oc[1] + 2.4 - att * 0.8)], 1.0, (0.1, 0.8))]
            mdet += [('col', cv.ellipse((oc[0] + 0.4 + j * 1.4, oc[1] + 2.0), 0.35, 0.35), IRON.hi) for j in range(3)]
            if att > 0.15:   # alt gaga
                low = cv.blob([(oc[0] + 2.0, oc[1] + 2.6), (oc[0] + 10.0, oc[1] + 3.6 + att * 2.0, 0.0), (oc[0] + 3.0, oc[1] + 4.2)])
                cv.shape(low, IRON.darker(0.8), z=11.8, sd=0.6, hi=0.3)
                yk.glow_soft(cv, (oc[0] + 5.5, oc[1] + 3.0 + att), 2.5, V['eye_glow'], z=11.9, blur=0.6, alpha=0.4 * att)
            cv.shape(mask, IRON, z=12, sd=1.1, hi=0.45, details=mdet)
            cv.fill(cv.ellipse((oc[0] + 1.2, ey), 1.3, 1.1), INK, z=12.5)
            yk.eye_glow(cv, (oc[0] + 1.3, ey), 0.75 * er, 0.55 * er, 0.0, V['eye'], V['eye_glow'], 13)
        elif face == 'mask':    # soluk ağlayan yüz maskesi (kayıp ruh); çığlıkta ağız açılır
            mask = cv.ellipse((oc[0] + 0.8, oc[1] + 0.2 + att * 0.4), 2.8, 3.8 + att * 0.8, 0.15)
            mdet = [('ink', [(oc[0] + 0.0, oc[1] + 2.6), (oc[0] + 1.0, oc[1] + 2.2), (oc[0] + 2.0, oc[1] + 2.8)], 0.9, (0.2, 0.2))]
            if att > 0.15:
                mdet = [('col', cv.ellipse((oc[0] + 1.0, oc[1] + 2.4 + att * 0.6), 0.9, 0.5 + att * 1.0), INK)]
            cv.shape(mask, Ink('#dcd8ec', '#7c78a4', '#ffffff'), z=12, sd=0.9, hi=0.3, details=mdet)
            for dx_ in (-0.4, 2.0):
                cv.fill(cv.ellipse((oc[0] + dx_, ey + 0.4), 0.7, 0.9), INK, z=12.4)
                yk.eye_glow(cv, (oc[0] + dx_, ey + 0.4), 0.38 * er, 0.5 * er, 0.0, V['eye'], V['eye_glow'], 13)
                cv.stroke([(oc[0] + dx_, ey + 1.2), (oc[0] + dx_ + 0.1, ey + 3.4), (oc[0] + dx_ - 0.1, ey + 5.0)], 0.9, z=13, col=V['fire'], taper=(0.1, 0.9), glow=V['eye_glow'])
        else:                   # karanlıkta iki göz + kemik dişler
            yk.eye_glow(cv, (oc[0] - 0.2, ey), 0.95 * er, 0.55 * er, -0.25, V['eye'], V['eye_glow'], 13)
            yk.eye_glow(cv, (oc[0] + 2.7, ey + 0.1), 0.8 * er, 0.5 * er, 0.2, V['eye'], V['eye_glow'], 13)
    if face == 'void':
        # karanlıkta seçilen kafatası: elmacık kemiği hilali ve sivri alt dişler (ağız saldırıda açılır)
        cv.fill(cv.blob([(oc[0] - 1.6, oc[1] + 0.2), (oc[0] + 0.8, oc[1] + 0.9), (oc[0] + 3.6, oc[1] + 0.1), (oc[0] + 3.4, oc[1] + 0.7),
                         (oc[0] + 0.8, oc[1] + 1.6), (oc[0] - 1.4, oc[1] + 0.9)]), V['robe'].shadow, z=12.4)
        jaw = 0.4 + att * 1.6
        for i, (dx_, ln) in enumerate(((-0.6, 1.3), (0.7, 1.7), (1.9, 1.5), (3.0, 1.1))):
            y0 = oc[1] + 3.6 + jaw
            cv.fill(cv.blob([(oc[0] + dx_ - 0.4, y0), (oc[0] + dx_ + 0.4, y0), (oc[0] + dx_ + 0.05, y0 - ln, 0.0)]), V['bone'].shadow, z=12.6)
    # ---- buhurdan (ön kolun zincirinde): salınım açısı dünyada (yerçekimi), gövde dönüşünden arındırılır
    af = p.get('af', (0.9, 0.5))
    sh = (hx + 4.5 - hdx, cy - 6)
    e, h = fk_arm(sh, af[0], af[1], 5.5, 5.5)
    sw = p.get('sw', 0.0) - rot
    L = 8.0
    cen = (h[0] + math.sin(sw) * L, h[1] + math.cos(sw) * L)
    cz = p.get('cz', 16)
    lid = (cen[0] - math.sin(sw) * 5.0, cen[1] - math.cos(sw) * 5.0)
    yk.chain_links(cv, h, lid, 4, V['metal'], cz - 0.5, r=0.7)
    _lantern(cv, cen, V, cz, flare, t)
    # tüten duman (sporlu teller): fenerden yükselip kıvrılır (dumanın yönü dünyada yukarı)
    sm = V['smoke']
    for i in range(2):
        uu = ((t + i * 0.5) % 1.0)
        yk.wisp(cv, (cen[0] - 0.3 + i * 0.6, cen[1] - 6.5), -math.pi / 2 - 0.25 + i * 0.2 - rot - p.get('drag', 0.0), 9.0 + 3.0 * uu, 2.6 + 0.8 * uu, sm, -2 + i * 0.1,
                ph=ph + i * 2.0, curl=0.8, alpha=0.55 - 0.25 * uu, glow=V['smoke_glow'], glow_a=0.5, ink=(i == 0))
    for i in range(3):
        uu = ((t * 1.0 + i / 3.0) % 1.0)
        q = (cen[0] - 1 + math.sin(uu * 6 + i) * 1.6 - uu * 2.5, cen[1] - 7 - uu * 10)
        cv.fill(cv.ellipse(q, 0.45, 0.45), V['fire_hot'], z=-1.9, glow=V['glow'], alpha=1.0 - uu * 0.6)
    pf = p.get('puff', 0.0)
    if pf > 0:   # spor patlaması: fenerin önünde büyük bulut + saçılan sporlar
        yk.cloud(cv, (cen[0] + 4.0 * pf, cen[1] - 0.5), 4.6 * pf, sm, cz + 4, seed=21, lobes=9, glow=V['smoke_glow'],
                 spores=10, spore_glow=V['glow'])
        yk.cloud(cv, (cen[0] + 8.5 * pf, cen[1] - 3.5 * pf), 2.4 * pf, sm, cz + 4.2, seed=22, lobes=7, glow=V['smoke_glow'])
        yk.sparks(cv, (cen[0] + 3, cen[1]), 9, 4.0 * pf, 9.0 * pf, V['fire_hot'], cz + 5, seed=4, w=1.3, glow=V['glow'])
    if flare > 0:   # hazırlık: buhurdandan fışkıran kıvılcımlar (uyarı)
        yk.sparks(cv, cen, 7, 3.5, 6.5 + 2.0 * flare, V['fire_hot'], cz + 2, seed=9 + int(t * 7), w=1.2, glow=V['glow'])
    if 'embers' in ex:
        yk.sparks(cv, (cen[0], cen[1] - 3), 4, 2.0, 5.0, V['fire_hot'], cz + 2, seed=int(t * 30) + 2, w=1.0, glow=V['glow'], ang=-math.pi / 2, spread=1.2)
    # ---- ön kol: yen, kemik ön kol ve zinciri tutan el
    m_ = _sleeve(cv, sh, e, h, R, 24, 2.5, 3.2, 21, True)
    cv.shape(cv.limb([m_, lerp2(m_, h, 0.5), h], [0.85, 0.7, 0.75]), V['bone'], z=23.6, sd=0.4, hi=0.2)
    a = af[0] + af[1]
    yk.bone_hand(cv, h, math.pi / 2 - a, V['bone'], 25.0, n=4, L=3.4, spread=0.42, curl=1.0, palm=1.1, r=0.38)
    _caput(cv, m_, V, 24.5, ph)
    if 'shackle' in ex:   # kırık pranga: bilekte demir halka, sarkan kopuk zincir
        cv.shape(cv.ellipse(lerp2(m_, h, 0.55), 1.5, 1.1, math.atan2(h[1] - m_[1], h[0] - m_[0]) + math.pi / 2), IRON, z=25.5, sd=0.5, hi=0.3)
        q0 = lerp2(m_, h, 0.55)
        q1 = (q0[0] - 1.5 + math.sin(ph) * 0.8, q0[1] + 6.0)
        yk.chain_links(cv, q0, q1, 4, IRON, 25.4, r=0.6)
    mouth = u29.to_world(cv, (cen[0], cen[1] + 0.5))
    cv.pop()
    return {'mouth': mouth}


# ================================================================== v29 animasyon tabloları
# Ortak dinlenme pozu (her anahtarın taşıdığı alanlar). Açılar: af / ab = (omuz, dirsek), fk_arm (0 aşağı, + öne).
REST = dict(bob=0.0, rot=0.0, sx=1.0, sy=1.0, off=(0.0, 0.0), skew=0.0, lean=0.0, att=0.0, flare=0.0, hurt=0.0,
            af=(0.9, 0.5), ab=(1.1, 0.7), sw=0.0, cz=16.0, puff=0.0, fw=0.0, hlag=0.0, hdx=0.0, hdy=0.0, mf=0.0,
            tail_a=0.86, tail_w=0.5, tail_l=1.0, tail_ph=0.0, streak=0.0, zirh=0.0, eyes=1.0, claw=0.0, drag=0.0,
            ws=0.0, wf=0.0, wsp=0.5, wl=0.0, wfar=0.0, ash=0.0, smoke_in=0.0, dis=0.0, amul=0.0)


def _k(t, keys, loop=False):
    return pose_at(t, keys, loop=loop, base=REST)


def _row(frames, fps, loop, pose, ts=None, mk=None):
    return dict(frames=frames, fps=fps, loop=loop, pose=pose, ts=ts, mk=mk)


S2 = math.tau


# ---- Çor Ruhu: kanatsız süzülen kefen (flyer_ranged)
def _cor_idle(t):
    s = math.sin
    return dict(REST, t=t, bob=2.2 * s(S2 * t), rot=0.055 * s(S2 * t - 0.9), sy=1.0 + 0.025 * s(S2 * t + 0.6), sx=1.0 - 0.02 * s(S2 * t + 0.6),
                hlag=-1.4 * s(S2 * t - 1.3), fw=1.6 * s(S2 * t + 0.8), sw=0.42 * s(S2 * t - 1.5), mf=0.4 * s(S2 * t - 1.0),
                af=(0.9 + 0.12 * s(S2 * t - 0.5), 0.5 + 0.12 * s(S2 * t - 1.0)), ab=(1.1 + 0.2 * s(S2 * t + 0.4), 0.7 + 0.1 * s(S2 * t)),
                tail_w=0.55)


def _cor_move(t):
    s = math.sin
    return dict(REST, t=t, bob=1.6 * s(S2 * t), rot=0.3 + 0.04 * s(S2 * t - 0.8), off=(1.0, 0.0), sy=1.04, sx=0.97,
                hlag=1.8 + 0.6 * s(S2 * t * 2 - 1.0), fw=-2.6 + 0.8 * s(S2 * t * 2), sw=-0.75 + 0.15 * s(S2 * t - 1.2), mf=1.4 + 0.4 * s(S2 * t * 2),
                af=(0.55, 0.65), ab=(0.45, 0.9), tail_a=0.97, tail_w=0.38, tail_k=2.0, tail_l=1.12, drag=0.9)


_COR_TELE = [(0.0, dict(bob=1.4, rot=0.08, sy=0.93, sx=1.05, sw=0.35, fw=0.8), 'io'),
             (0.33, dict(bob=-0.6, rot=-0.18, sy=1.05, sx=0.97, af=(2.3, 0.5), ab=(1.6, 0.8), sw=-1.0, flare=0.5, hlag=-1.5, fw=1.8), 'o'),
             (0.66, dict(bob=-1.4, rot=-0.32, sy=1.1, sx=0.93, af=(3.55, -0.35), ab=(1.9, 0.9), sw=-2.5, flare=1.0, att=0.3, hlag=-2.2, fw=2.4, mf=0.8), 'o'),
             (1.0, dict(bob=-1.6, rot=-0.34, sy=1.11, sx=0.92, af=(3.6, -0.35), ab=(1.95, 0.9), sw=-2.7, flare=1.0, att=0.45, hlag=-2.0, fw=2.2, mf=0.9, off=(-0.4, 0.0)), 'io')]

_COR_TELE_Z = [(0.0, dict(bob=1.6, rot=0.1, sy=0.9, sx=1.08, sw=0.4, fw=1.0, zirh=0.3), 'io'),
               (0.33, dict(bob=-1.0, rot=-0.12, sy=1.04, sx=1.08, af=(2.6, 0.3), ab=(2.5, 0.3), sw=-1.4, flare=0.7, hlag=-2.5, fw=3.4, mf=1.6, zirh=0.7, tail_a=0.74, tail_w=0.9), 'o'),
               (0.66, dict(bob=-2.2, rot=-0.22, sy=1.08, sx=1.14, af=(3.3, -0.1), ab=(2.9, 0.2), sw=-3.0, flare=1.0, att=0.7, hlag=-3.0, fw=4.0, mf=2.2, zirh=1.0, tail_a=0.7, tail_w=1.0), 'o'),
               (1.0, dict(bob=-2.4, rot=-0.24, sy=1.09, sx=1.15, af=(3.35, -0.1), ab=(2.95, 0.2), sw=-3.3, flare=1.0, att=0.8, hlag=-2.8, fw=4.2, mf=2.3, zirh=1.0, tail_a=0.7, tail_w=1.0), 'io')]

_COR_ATK_TS = [0.0, 0.30, 0.38, 0.46, 0.58, 0.70, 0.82, 0.92]
_COR_ATK = [(0.0, _COR_TELE[-1][1], 'l'),
            (0.30, dict(bob=1.0, rot=0.4, sy=1.12, sx=0.92, off=(3.0, 1.0), af=(1.75, -0.15), ab=(1.4, 0.3), sw=1.9, puff=1.0, att=1.0, flare=0.6,
                        fw=-2.4, hlag=2.6, tail_a=0.76, tail_w=0.85, streak=0.7, sdir=(1.0, 0.3), mf=1.8, cz=16.0), 'i'),
            (0.38, dict(bob=1.2, rot=0.47, sy=1.07, sx=0.95, off=(3.4, 1.2), af=(1.9, -0.25), sw=2.35, puff=1.35, att=0.9, flare=0.4, streak=0.3, hlag=3.0, fw=-2.8), 'o'),
            (0.46, dict(bob=1.0, rot=0.36, sy=1.0, sx=1.0, off=(3.0, 1.0), af=(1.8, -0.1), sw=2.0, puff=1.6, att=0.7, flare=0.2, streak=0.0, hlag=2.0, fw=-1.6), 'o'),
            (0.58, dict(bob=0.6, rot=0.16, off=(2.0, 0.6), af=(1.4, 0.2), sw=1.0, puff=1.15, att=0.4, flare=0.0, hlag=0.5, fw=0.4, tail_a=0.9, mf=0.6), 'io'),
            (0.70, dict(bob=-0.2, rot=-0.06, off=(1.0, 0.2), af=(1.05, 0.4), sw=-0.1, puff=0.6, att=0.15, hlag=-1.2, fw=1.6, tail_a=0.92, tail_w=0.6, mf=0.0), 'io'),
            (0.82, dict(bob=0.3, rot=0.03, off=(0.3, 0.0), af=(0.9, 0.5), sw=-0.45, puff=0.0, att=0.0, hlag=-0.4, fw=0.6, tail_a=0.86, tail_w=0.5), 'io'),
            (0.92, dict(bob=0.0, rot=0.0, off=(0.0, 0.0), sw=-0.15, hlag=0.0, fw=0.4), 'io')]

_COR_DIVE_TS = [0.0, 0.2, 0.35, 0.55, 0.72, 0.86]
_COR_DIVE = [(0.0, dict(bob=-1.0, rot=-0.15, sy=0.94, sx=1.04, af=(2.2, 0.6), ab=(1.8, 0.8), sw=-0.8, flare=0.8, hlag=-1.5, att=0.4), 'io'),
             (0.2, dict(bob=2.0, rot=1.05, sy=1.18, sx=0.86, off=(2.0, 2.0), af=(1.65, 0.05), ab=(1.5, 0.15), sw=-2.4, flare=0.6, att=1.0, claw=1.0,
                        tail_a=0.92, tail_w=0.3, tail_l=1.2, fw=-3.0, hlag=3.5, mf=2.0, streak=1.0, sdir=(0.55, 0.85), drag=1.4), 'i'),
             (0.35, dict(bob=2.5, rot=1.1, sy=1.2, sx=0.85, off=(2.4, 2.6), af=(1.7, 0.0), sw=-2.6, att=1.0, streak=1.0, hlag=3.8, tail_ph=1.4), 'l'),
             (0.55, dict(bob=1.0, rot=0.3, sy=0.88, sx=1.14, off=(2.0, 3.0), af=(1.2, 0.4), ab=(1.0, 0.6), sw=0.6, att=0.5, claw=0.4, streak=0.0, tail_a=0.8, tail_w=0.8,
                         fw=2.0, hlag=-1.0, mf=0.6, drag=0.0), 'o'),
             (0.72, dict(bob=-1.0, rot=-0.15, sy=1.05, sx=0.97, off=(1.0, 1.0), af=(0.8, 0.6), ab=(1.0, 0.7), sw=0.3, att=0.1, claw=0.0, hlag=-1.5, fw=1.0), 'io'),
             (0.86, dict(bob=0.0, rot=0.0, sy=1.0, sx=1.0, off=(0.0, 0.0), af=(0.9, 0.5), sw=0.0, att=0.0, hlag=0.0, fw=0.5), 'io')]

_COR_HOP = [(0.0, dict(rot=-0.45, off=(-2.5, -0.5), sx=0.92, sy=1.08, fw=3.2, tail_a=0.62, tail_w=0.9, sw=1.6, hlag=-2.6, mf=-0.8, af=(1.6, 0.8), ab=(2.0, 0.5), att=0.4), 'o'),
            (0.25, dict(rot=-0.36, off=(-4.5, -1.5), fw=2.6, tail_a=0.7, sw=1.8, hlag=-2.0), 'o'),
            (0.5, dict(rot=-0.22, off=(-5.5, -2.0), fw=1.4, tail_a=0.78, sw=1.2, hlag=-1.0, sx=1.0, sy=1.0, att=0.1), 'io'),
            (0.75, dict(rot=-0.08, off=(-5.0, -1.6), fw=0.6, tail_a=0.84, sw=0.5, hlag=0.0), 'io'),
            (1.0, dict(rot=0.0, off=(-4.2, -1.2), fw=0.2, tail_a=0.86, sw=0.1, af=(0.9, 0.5), ab=(1.1, 0.7), att=0.0), 'io')]

_HURT = [(0.0, dict(rot=-0.34, off=(-2.2, 0.0), sx=1.1, sy=0.9, hurt=1.0, sw=1.3, fw=2.4, hlag=-2.6, mf=-0.6, af=(1.4, 1.0), ab=(1.9, 0.6), att=0.7, eyes=0.6), 'l'),
         (0.5, dict(rot=-0.2, off=(-2.8, -0.4), sx=0.95, sy=1.05, hurt=0.7, sw=1.7, fw=1.6, hlag=-1.4, att=0.4, eyes=0.8), 'o'),
         (1.0, dict(rot=-0.08, off=(-2.4, -0.2), sx=1.0, sy=1.0, hurt=0.3, sw=0.9, fw=0.8, hlag=-0.5, att=0.1, eyes=1.0, af=(1.0, 0.6), ab=(1.2, 0.7)), 'io')]

_STAGGER = [(0.0, dict(rot=-0.5, off=(-2.0, 0.0), sx=1.08, sy=0.9, hurt=1.0, sw=1.5, fw=3.0, hlag=-3.0, att=0.8, eyes=0.5, af=(1.8, 1.2), ab=(2.4, 0.5)), 'l'),
            (0.2, dict(rot=0.22, off=(-3.0, 1.5), bob=1.5, sx=0.96, sy=1.05, sw=-1.4, fw=-2.0, hlag=2.0, eyes=0.2, af=(0.4, 1.4), ab=(0.6, 1.2)), 'o'),
            (0.4, dict(rot=-0.32, off=(-3.4, 2.5), bob=2.5, sw=1.6, fw=2.4, hlag=-2.2, eyes=0.7, af=(2.0, 0.8), ab=(2.2, 0.6)), 'io'),
            (0.6, dict(rot=0.12, off=(-3.0, 3.0), bob=3.0, sw=-0.8, fw=-1.0, hlag=1.2, eyes=0.3, tail_ph=2.0), 'io'),
            (0.8, dict(rot=-0.1, off=(-2.5, 2.4), bob=2.0, sw=0.5, fw=0.8, hlag=-0.6, eyes=0.8), 'io'),
            (1.0, dict(rot=0.0, off=(-2.0, 1.5), bob=1.0, sw=0.0, fw=0.3, hlag=0.0, eyes=1.0, hurt=0.2, att=0.0, af=(0.9, 0.5), ab=(1.1, 0.7)), 'io')]

_DEATH = [(0.0, dict(rot=-0.5, off=(-1.5, 0.0), sx=1.1, sy=0.88, hurt=1.0, att=1.0, flare=0.6, sw=1.2, fw=2.6, hlag=-3.0, af=(2.2, 0.9), ab=(2.6, 0.4), eyes=1.3), 'l'),
          (0.12, dict(rot=-0.7, off=(-2.5, 1.0), bob=2.0, sy=0.92, sx=1.04, sw=2.2, fw=3.4, hlag=-3.6, att=1.0, eyes=1.0, flare=0.0), 'o'),
          (0.25, dict(rot=-0.85, off=(-3.0, 3.0), bob=4.5, sy=0.84, sx=1.08, sw=2.6, dis=0.12, ash=0.3, eyes=0.5, att=0.6, af=(1.6, 1.4), ab=(2.0, 1.2), tail_ph=1.5), 'io'),
          (0.38, dict(rot=-1.0, off=(-3.2, 5.5), bob=7.0, sy=0.8, sx=1.1, sw=2.9, dis=0.28, ash=0.6, eyes=0.2), 'io'),
          (0.5, dict(rot=-1.1, off=(-3.4, 7.0), bob=8.5, dis=0.45, ash=0.8, eyes=0.0), 'io'),
          (0.62, dict(rot=-1.15, off=(-3.4, 8.0), bob=9.5, dis=0.62, ash=1.0), 'l'),
          (0.75, dict(off=(-3.4, 8.6), bob=10.0, dis=0.77, ash=1.0), 'l'),
          (0.88, dict(off=(-3.4, 9.0), bob=10.3, dis=0.88, ash=0.9), 'l'),
          (1.0, dict(off=(-3.4, 9.2), bob=10.5, dis=0.95, ash=0.7), 'l')]

_SPAWN = [(0.0, dict(dis=0.92, smoke_in=1.0, sy=1.2, sx=0.85, bob=-3.0, eyes=0.0), 'l'),
          (0.17, dict(dis=0.74, smoke_in=0.85, sy=1.18, sx=0.86, bob=-2.0), 'o'),
          (0.33, dict(dis=0.52, smoke_in=0.6, sy=1.12, sx=0.9, bob=-1.0, fw=2.0, hlag=-2.0), 'io'),
          (0.5, dict(dis=0.3, smoke_in=0.35, sy=1.06, sx=0.95, bob=0.0, fw=1.2), 'io'),
          (0.67, dict(dis=0.1, smoke_in=0.12, sy=0.92, sx=1.08, bob=1.2, flare=1.0, eyes=1.4, att=0.6, hlag=1.0), 'io'),
          (0.83, dict(dis=0.0, smoke_in=0.0, sy=1.04, sx=0.97, bob=-0.4, flare=0.5, eyes=1.1, att=0.2, fw=-0.6), 'o'),
          (1.0, dict(sy=1.0, sx=1.0, bob=0.0, flare=0.0, eyes=1.0, att=0.0, fw=0.4, hlag=0.0), 'io')]


def _nl(keys, n):
    """Döngüsüz satır: kareler eşit aralıkta (0 .. 1, son kare son anahtar)."""
    return lambda t: _k(t, keys)


def _even_last(n):
    return [round(i / (n - 1), 4) for i in range(n)]


def _cor_rows():
    return {
        'idle': _row(8, 10, True, _cor_idle),
        'move': _row(8, 12, True, _cor_move),
        'tele': _row(4, 10, False, _nl(_COR_TELE, 4)),
        'tele_zirh': _row(4, 10, False, _nl(_COR_TELE_Z, 4)),
        'attack': _row(8, 12, False, lambda t: _k(t, _COR_ATK), ts=_COR_ATK_TS, mk=[0.30, 0.34, 0.58]),
        'dive': _row(6, 12, False, lambda t: _k(t, _COR_DIVE), ts=_COR_DIVE_TS, mk=[0.2, 0.3, 0.55]),
        'hop': _row(5, 12, False, _nl(_COR_HOP, 5)),
        'hurt': _row(3, 16, False, _nl(_HURT, 3)),
        'stagger': _row(6, 10, False, _nl(_STAGGER, 6)),
        'death': _row(9, 12, False, _nl(_DEATH, 9)),
        'spawn': _row(7, 12, False, _nl(_SPAWN, 7)),
    }


# ---- dalıcılar: kanatlı kefen (Kurgan Ruhu, Ayaz Çoru, Demir Gaga) — kerkenez gibi çırpınarak asılı durur, pike yapar
def _dv_idle(t):
    w, bob = flap(t, down=0.45)
    s = math.sin
    return dict(REST, t=t, bob=bob, rot=0.05 * s(S2 * (t - 0.2)), sy=1.0 + 0.03 * s(S2 * (t - 0.1)), sx=1.0 - 0.02 * s(S2 * (t - 0.1)),
                hlag=1.6 * s(S2 * (t - 0.3)), fw=1.8 * s(S2 * (t - 0.35)), sw=0.3 * s(S2 * (t - 0.4)), mf=0.6 * s(S2 * (t - 0.25)),
                af=(0.75 + 0.1 * s(S2 * (t - 0.3)), 0.7), ab=(0.6 + 0.15 * s(S2 * (t - 0.3)), 1.0), claw=0.2,
                tail_w=0.6, tail_ph=0.0, **w)


def _dv_move(t):
    w, bob = flap(t, down=0.5, top=-0.85, bot=0.75, fold_max=0.75, bob_amp=1.3)
    s = math.sin
    return dict(REST, t=t, bob=bob, rot=0.32 + 0.04 * s(S2 * (t - 0.2)), off=(1.0, 0.0), sy=1.05, sx=0.96,
                hlag=2.2 + 0.6 * s(S2 * (t - 0.3)), fw=-2.6 + 0.8 * s(S2 * (t - 0.35)), sw=-0.7 + 0.12 * s(S2 * (t - 0.4)), mf=1.4,
                af=(0.5, 0.8), ab=(0.4, 1.0), tail_a=0.97, tail_w=0.4, tail_k=2.0, tail_l=1.1, drag=0.9, **w)


_DV_TELE = [(0.0, dict(bob=1.2, rot=0.06, sy=0.94, sx=1.05, ws=0.85, wf=0.1, wsp=0.4, wl=0.6, af=(0.9, 0.8), ab=(0.8, 1.0)), 'io'),
            (0.33, dict(bob=-1.2, rot=-0.12, sy=1.04, sx=0.97, ws=-0.55, wf=0.35, wsp=0.8, wl=-0.6, af=(1.5, 1.0), ab=(1.3, 1.2), flare=0.5, hlag=-1.5, fw=1.4, claw=0.6), 'o'),
            (0.66, dict(bob=-2.4, rot=-0.24, sy=1.09, sx=0.93, ws=-1.0, wf=0.05, wsp=1.0, wl=0.0, af=(2.0, 1.4), ab=(1.8, 1.4), flare=1.0, att=0.5, hlag=-2.4, fw=2.2, mf=0.8, claw=1.0), 'o'),
            (1.0, dict(bob=-2.6, rot=-0.26, sy=1.1, sx=0.92, ws=-1.0, wf=0.0, wsp=1.0, af=(2.05, 1.45), ab=(1.85, 1.45), flare=1.0, att=0.6, hlag=-2.2, fw=2.0, mf=0.9, claw=1.0, off=(-0.5, 0.0)), 'io')]

_DV_TELE_Z = [(0.0, dict(bob=1.4, rot=0.08, sy=0.9, sx=1.08, ws=0.9, wf=0.1, wsp=0.4, wl=0.6, zirh=0.3), 'io'),
              (0.33, dict(bob=-1.6, rot=-0.08, sy=1.05, sx=1.06, ws=-0.7, wf=0.0, wsp=1.0, wl=-0.4, wfar=-0.15, af=(2.2, 0.6), ab=(2.4, 0.5), flare=0.8, hlag=-2.6, fw=3.2, mf=1.8, zirh=0.7, claw=1.0), 'o'),
              (0.66, dict(bob=-3.0, rot=-0.16, sy=1.1, sx=1.1, ws=-1.0, wf=0.0, wsp=1.0, wl=0.0, wfar=-0.2, af=(2.8, 0.3), ab=(2.9, 0.3), flare=1.0, att=0.9, hlag=-3.0, fw=3.8, mf=2.4, zirh=1.0, claw=1.0, tail_a=0.72, tail_w=1.0), 'o'),
              (1.0, dict(bob=-3.2, rot=-0.17, sy=1.11, sx=1.12, ws=-1.0, wf=0.0, wsp=1.0, af=(2.85, 0.3), ab=(2.95, 0.3), flare=1.0, att=1.0, hlag=-2.8, fw=4.0, mf=2.5, zirh=1.0, claw=1.0, tail_a=0.7, tail_w=1.0), 'io')]

# pike: 0 hazırlık (kanatlar yukarı açık), 1 kanatları katlayıp pike (W), 2 akış biçimli dalış, 3 pençeler öne + kanat yarım
# açılır (fren), 4 çarpma / saplanma (C: ezilme, kanatlar açılır), 5-6 saplanmış çırpınma, 7 sıyrılış (H: güçlü aşağı vuruş),
# 8 yükseliş, 9 asılı duruşa dönüş
_DV_ATK_TS = [0.0, 0.25, 0.32, 0.40, 0.45, 0.52, 0.64, 0.78, 0.86, 0.93]
_DV_ATK = [(0.0, _DV_TELE[-1][1], 'l'),
           (0.25, dict(bob=1.0, rot=1.0, sy=1.16, sx=0.88, off=(1.5, 1.5), ws=-0.18, wf=1.0, wsp=0.0, wl=-1.0, wfar=0.05, af=(0.6, 1.6), ab=(0.5, 1.7),
                       flare=0.6, att=0.4, hlag=3.2, fw=-3.0, mf=2.2, claw=0.0, tail_a=0.94, tail_w=0.25, tail_l=1.2, streak=0.8, sdir=(0.35, 0.94), drag=1.4, sw=-2.6), 'i'),
           (0.32, dict(bob=4.0, rot=1.12, sy=1.22, sx=0.84, off=(2.2, 4.0), ws=-0.1, wf=1.0, wsp=0.0, wl=-1.0, streak=1.2, hlag=3.8, tail_ph=1.4, sw=-2.8), 'l'),
           (0.40, dict(bob=8.0, rot=0.85, sy=1.12, sx=0.9, off=(2.6, 8.0), ws=0.35, wf=0.5, wsp=0.6, wl=1.0, af=(1.7, 0.2), ab=(1.55, 0.3), claw=1.0, att=1.0,
                        streak=0.8, hlag=3.0, tail_ph=2.4), 'l'),
           (0.45, dict(bob=13.5, rot=0.95, sy=0.78, sx=1.3, off=(3.0, 13.5), ws=-0.6, wf=0.0, wsp=1.0, wl=1.0, wfar=-0.1, af=(1.95, 0.1), ab=(1.8, 0.2), claw=1.0, att=1.0,
                        streak=0.0, hlag=-1.5, fw=2.4, mf=-0.6, tail_a=0.8, tail_w=0.9, sw=1.0, drag=0.0), 'l'),
           (0.52, dict(bob=13.0, rot=0.9, sy=0.92, sx=1.08, off=(3.0, 13.0), ws=-1.0, wf=0.2, wsp=1.0, wl=-0.6, af=(1.9, 0.2), ab=(1.7, 0.4), att=0.8, hlag=-2.4, fw=2.8, sw=1.6), 'o'),
           (0.64, dict(bob=12.6, rot=0.72, sy=1.04, sx=0.97, off=(2.6, 12.6), ws=0.6, wf=0.3, wsp=0.7, wl=1.0, af=(1.6, 0.6), ab=(1.4, 0.7), att=0.6, hlag=1.2, fw=-1.0, sw=-0.4, tail_ph=3.6), 'io'),
           (0.78, dict(bob=8.0, rot=0.1, sy=1.12, sx=0.92, off=(1.6, 8.0), ws=0.95, wf=0.0, wsp=0.5, wl=1.0, af=(0.6, 1.0), ab=(0.5, 1.1), att=0.2, claw=0.3, hlag=2.4, fw=-2.2, mf=1.2, sw=-0.9,
                        streak=0.5, sdir=(0.0, -1.0)), 'o'),
           (0.86, dict(bob=3.0, rot=-0.1, sy=1.0, sx=1.0, off=(0.8, 3.0), ws=-0.3, wf=0.85, wsp=1.0, wl=-1.0, af=(0.7, 0.8), ab=(0.6, 1.0), att=0.0, hlag=0.8, fw=0.0, mf=0.4, sw=-0.3, streak=0.0), 'io'),
           (0.93, dict(bob=0.5, rot=0.0, off=(0.0, 0.5), ws=-0.95, wf=0.1, wsp=0.5, wl=0.0, af=(0.75, 0.7), ab=(0.6, 1.0), hlag=-0.6, fw=1.0, mf=0.0, sw=0.1, claw=0.2), 'io')]


def _dv_stuck(t):
    """Gagası / pençesi yere saplanmış: kanatlar çırpınır, gövde silkinir (dalış 'stuck' durumu)."""
    w, _ = flap(t, down=0.4, top=-1.0, bot=0.7, fold_max=0.6)
    s = math.sin
    return dict(REST, t=t, bob=13.0 + 0.4 * s(S2 * t), off=(3.0 + 0.6 * s(S2 * t * 2), 13.0), rot=0.86 + 0.1 * s(S2 * t), sy=0.95, sx=1.05,
                af=(1.9, 0.2), ab=(1.7, 0.4), claw=1.0, att=0.7 + 0.3 * s(S2 * t * 2), hlag=-1.5 * s(S2 * t), fw=2.0 * s(S2 * t + 1),
                sw=1.2 + 0.5 * s(S2 * t), tail_w=0.9, **w)


_DV_HOP = [(0.0, dict(rot=-0.5, off=(-2.5, -0.5), sx=0.92, sy=1.08, ws=0.9, wf=0.0, wsp=0.8, wl=1.0, fw=3.2, tail_a=0.64, tail_w=0.9, sw=1.4, hlag=-2.6, af=(1.6, 0.8), ab=(1.5, 0.9), att=0.5), 'o'),
           (0.25, dict(rot=-0.4, off=(-4.5, -2.0), ws=-0.4, wf=0.8, wsp=1.0, wl=-1.0, fw=2.4, tail_a=0.72, sw=1.6, hlag=-1.8), 'o'),
           (0.5, dict(rot=-0.25, off=(-5.5, -3.0), ws=-1.0, wf=0.1, wsp=0.7, wl=0.0, fw=1.4, tail_a=0.8, sw=1.0, hlag=-0.8, sx=1.0, sy=1.0, att=0.1), 'io'),
           (0.75, dict(rot=-0.1, off=(-5.0, -2.6), ws=0.8, wf=0.05, wsp=0.5, wl=1.0, fw=0.6, tail_a=0.84, sw=0.4, hlag=0.4), 'io'),
           (1.0, dict(rot=0.0, off=(-4.2, -2.0), ws=-0.2, wf=0.8, wsp=0.9, wl=-1.0, fw=0.2, tail_a=0.86, sw=0.1, af=(0.75, 0.7), ab=(0.6, 1.0), att=0.0), 'io')]


def _wing_over(keys, **wing):
    """Ortak anahtarların üstüne kanat alanları (yaralanma, sendeleme, ölüm, doğuşta kanatların ne yaptığı)."""
    out = []
    for i, (tk, d, e) in enumerate(keys):
        d2 = dict(d)
        for k, v in wing.items():
            d2[k] = v[min(i, len(v) - 1)]
        out.append((tk, d2, e))
    return out


_DV_HURT = _wing_over(_HURT, ws=[0.7, -0.6, -0.2], wf=[0.4, 0.7, 0.5], wsp=[1.0, 1.0, 0.7], wl=[-1.0, 1.0, 0.0])
_DV_STAGGER = _wing_over(_STAGGER, ws=[0.8, -0.9, 0.5, -0.4, 0.9, -0.6], wf=[0.5, 0.2, 0.8, 0.6, 0.1, 0.5], wsp=[1.0], wl=[1.0, -1.0, 1.0, -1.0, 1.0, 0.0],
                         wfar=[0.3, -0.4, 0.5, -0.3, 0.2, 0.0])
# ölüm: kanatlar kırılır (biri yukarı savrulur, öteki çöker), yuvarlanarak düşer, tüyler / kül saçılır, çözülür
_DV_DEATH = _wing_over(_DEATH, ws=[0.9, -1.0, 0.4, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0], wf=[0.3, 0.6, 1.0, 0.9, 0.9, 0.9], wsp=[1.0], wl=[-1.0, 1.0, -1.0, -1.0, -1.0, 0.0],
                       wfar=[-0.4, 0.8, -0.6, -0.5, -0.4, -0.4])
_DV_SPAWN = _wing_over(_SPAWN, ws=[0.2, 0.0, -0.4, -1.0, 0.9, -0.6, -0.9], wf=[1.0, 0.9, 0.6, 0.0, 0.0, 0.7, 0.1], wsp=[0.2, 0.4, 0.7, 1.0, 0.6, 1.0, 0.5], wl=[0.0, 0.0, -1.0, 0.0, 1.0, -1.0, 0.0])


def _dv_rows():
    return {
        'idle': _row(8, 12, True, _dv_idle),
        'move': _row(6, 12, True, _dv_move),
        'tele': _row(4, 10, False, _nl(_DV_TELE, 4)),
        'tele_zirh': _row(4, 10, False, _nl(_DV_TELE_Z, 4)),
        'attack': _row(10, 12, False, lambda t: _k(t, _DV_ATK), ts=_DV_ATK_TS, mk=[0.25, 0.45, 0.78]),
        'stuck': _row(4, 10, True, _dv_stuck),
        'hop': _row(5, 12, False, _nl(_DV_HOP, 5)),
        'hurt': _row(3, 16, False, _nl(_DV_HURT, 3)),
        'stagger': _row(6, 10, False, _nl(_DV_STAGGER, 6)),
        'death': _row(9, 12, False, _nl(_DV_DEATH, 9)),
        'spawn': _row(7, 12, False, _nl(_DV_SPAWN, 7)),
    }


# ---- sürü: Kan Çoru (yarasa zarı, düzensiz çırpınma) ve Kayıp Ruh (kanatsız, kıvrılan duman gövde)
def _jit(t, k, seed):
    """Düzensiz sürü titreşimi: kare başına sabit, döngüde kapanan sözde rastgele kayma."""
    a = math.sin(S2 * t * 2 + seed) * 0.6 + math.sin(S2 * t * 3 + seed * 1.7) * 0.4
    b = math.sin(S2 * t * 3 + seed * 0.7) * 0.6 + math.sin(S2 * t + seed * 2.3) * 0.4
    return (a * k, b * k * 0.8)


def _bat_idle(t):
    w, bob = flap((t * 2) % 1.0, down=0.42, top=-1.0, bot=1.0, fold_max=1.0, bob_amp=2.0)
    s = math.sin
    j = _jit(t, 1.6, 1.3)
    return dict(REST, t=t, bob=bob, off=j, rot=0.07 * s(S2 * t * 2 - 0.8) + 0.05 * s(S2 * t + 0.5), sy=1.0 + 0.04 * s(S2 * (2 * t - 0.1)), sx=1.0 - 0.03 * s(S2 * (2 * t - 0.1)),
                hlag=1.6 * s(S2 * (2 * t - 0.3)), fw=1.6 * s(S2 * (2 * t - 0.35)), sw=0.35 * s(S2 * (t - 0.3)), mf=0.5 * s(S2 * (2 * t - 0.25)),
                af=(0.8 + 0.1 * s(S2 * t), 0.6), ab=(0.9, 0.9), att=0.2 + 0.2 * s(S2 * t), tail_w=0.65, tail_k=2.0, **w)


def _bat_move(t):
    w, bob = flap(t, down=0.45, top=-0.9, bot=0.85, fold_max=0.95, bob_amp=1.6)
    s = math.sin
    return dict(REST, t=t, bob=bob, off=_jit(t, 0.8, 2.1), rot=0.3 + 0.05 * s(S2 * (t - 0.2)), sy=1.05, sx=0.96,
                hlag=2.4, fw=-2.6 + 0.8 * s(S2 * (t - 0.35)), sw=-0.7, mf=1.4, af=(0.5, 0.8), ab=(0.4, 1.0), att=0.3,
                tail_a=0.97, tail_w=0.45, tail_k=2.0, tail_l=1.1, drag=0.9, **w)


_BAT_TELE = [(0.0, dict(bob=1.0, rot=0.1, sy=0.93, sx=1.06, ws=0.9, wf=0.2, wsp=0.4, wl=0.6, att=0.3), 'io'),
             (0.33, dict(bob=-0.8, rot=-0.18, sy=1.05, sx=0.96, off=(-1.5, -0.5), ws=-0.7, wf=0.3, wl=-0.6, af=(1.9, 1.0), ab=(1.7, 1.1), flare=0.5, att=0.8, hlag=-2.0, fw=1.8, claw=0.6), 'o'),
             (0.66, dict(bob=-1.6, rot=-0.32, sy=1.1, sx=0.92, off=(-2.5, -1.0), ws=-1.0, wf=0.0, wl=0.0, af=(2.4, 1.3), ab=(2.2, 1.3), flare=1.0, att=1.0, hlag=-2.6, fw=2.4, mf=0.8, claw=1.0), 'o'),
             (1.0, dict(bob=-1.8, rot=-0.34, sy=1.11, sx=0.91, off=(-2.8, -1.0), ws=-1.0, wf=0.0, af=(2.45, 1.3), ab=(2.25, 1.3), flare=1.0, att=1.0, hlag=-2.4, fw=2.2, mf=0.9, claw=1.0), 'io')]

_BAT_TELE_Z = [(0.0, dict(bob=1.2, rot=0.1, sy=0.9, sx=1.08, ws=0.9, wf=0.2, wl=0.6, zirh=0.3, att=0.4), 'io'),
               (0.33, dict(bob=-1.4, rot=-0.1, sy=1.04, sx=1.08, ws=-0.8, wf=0.0, wl=-0.4, wfar=-0.15, af=(2.4, 0.5), ab=(2.5, 0.4), flare=0.8, att=1.0, hlag=-2.6, fw=3.2, mf=1.8, zirh=0.7, claw=1.0), 'o'),
               (0.66, dict(bob=-2.6, rot=-0.2, sy=1.08, sx=1.14, ws=-1.0, wf=0.0, wl=0.0, wfar=-0.2, af=(2.9, 0.3), ab=(3.0, 0.3), flare=1.0, att=1.0, hlag=-3.0, fw=4.0, mf=2.4, zirh=1.0, claw=1.0, tail_a=0.72, tail_w=1.0), 'o'),
               (1.0, dict(bob=-2.8, rot=-0.21, sy=1.09, sx=1.15, ws=-1.0, wf=0.0, af=(2.95, 0.3), ab=(3.05, 0.3), flare=1.0, att=1.0, hlag=-2.8, fw=4.2, mf=2.5, zirh=1.0, claw=1.0, tail_a=0.7, tail_w=1.0), 'io')]

# süzülüş: 0 hazırlık (geri çekilir, kanatlar yukarı açık, ağız açık), 1 süzülüş (W: kanatlar geriye yarı katlı, gövde
# çapraz uzar, pençeler önde), 2 ısırık (C), 3 geçiş sürer, 4 fren (kanatlar öne açılır), 5-8 çırparak yükselip toparlanma
_BAT_ATK_TS = [0.0, 0.28, 0.36, 0.46, 0.58, 0.68, 0.78, 0.86, 0.93]
_BAT_ATK = [(0.0, _BAT_TELE[-1][1], 'l'),
            (0.28, dict(bob=1.5, rot=0.75, sy=1.2, sx=0.85, off=(3.0, 2.0), ws=0.05, wf=0.75, wsp=0.0, wl=-1.0, af=(1.8, 0.1), ab=(1.65, 0.2), claw=1.0, att=0.8, flare=0.6,
                        hlag=3.4, fw=-3.0, mf=2.2, tail_a=0.95, tail_w=0.3, tail_l=1.2, streak=1.0, sdir=(0.8, 0.6), drag=1.2, sw=-2.0), 'i'),
             (0.36, dict(bob=2.5, rot=0.8, sy=1.24, sx=0.83, off=(4.0, 3.0), ws=0.1, wf=0.8, att=1.2, streak=1.2, hlag=3.8, tail_ph=1.5, sw=-2.3), 'l'),
             (0.46, dict(bob=3.0, rot=0.62, sy=1.14, sx=0.9, off=(4.4, 3.4), ws=0.2, wf=0.6, att=0.9, streak=0.8, hlag=3.0, tail_ph=2.6), 'l'),
             (0.58, dict(bob=2.0, rot=-0.2, sy=0.9, sx=1.12, off=(3.6, 2.4), ws=0.85, wf=0.0, wsp=1.0, wl=1.0, af=(1.2, 0.6), ab=(1.0, 0.8), claw=0.5, att=0.5, streak=0.0,
                         hlag=-2.0, fw=2.6, mf=-0.6, tail_a=0.78, tail_w=0.9, sw=1.2, drag=0.0), 'o'),
             (0.68, dict(bob=0.5, rot=-0.12, sy=1.04, sx=0.97, off=(2.6, 1.2), ws=-0.6, wf=0.9, wsp=1.0, wl=-1.0, att=0.3, hlag=1.0, fw=0.4, sw=0.8), 'io'),
             (0.78, dict(bob=-0.5, rot=0.02, off=(1.6, 0.4), ws=0.9, wf=0.0, wsp=0.5, wl=1.0, af=(0.9, 0.6), ab=(0.9, 0.9), claw=0.0, att=0.2, hlag=1.6, fw=-0.6, sw=0.0), 'io'),
             (0.86, dict(bob=0.3, rot=0.0, off=(0.8, 0.2), ws=-0.4, wf=0.9, wsp=1.0, wl=-1.0, hlag=-0.6, fw=0.8), 'io'),
             (0.93, dict(bob=0.0, off=(0.0, 0.0), ws=-0.95, wf=0.1, wsp=0.5, wl=0.0, hlag=-0.4, fw=0.6), 'io')]

_BAT_HOP = _wing_over(_COR_HOP, ws=[0.9, -0.5, -1.0, 0.8, -0.3], wf=[0.0, 0.9, 0.1, 0.0, 0.9], wsp=[0.8, 1.0, 0.7, 0.5, 0.9], wl=[1.0, -1.0, 0.0, 1.0, -1.0])
_BAT_HURT = _wing_over(_HURT, ws=[0.8, -0.7, -0.2], wf=[0.6, 0.9, 0.6], wsp=[1.0], wl=[-1.0, 1.0, 0.0])
_BAT_STAGGER = _wing_over(_STAGGER, ws=[0.9, -1.0, 0.6, -0.5, 1.0, -0.6], wf=[0.6, 0.3, 0.9, 0.7, 0.2, 0.6], wsp=[1.0], wl=[1.0, -1.0, 1.0, -1.0, 1.0, 0.0],
                          wfar=[0.3, -0.4, 0.5, -0.3, 0.2, 0.0])
_BAT_DEATH = _wing_over(_DEATH, ws=[0.9, -1.0, 0.5, 0.9, 1.0, 1.0], wf=[0.4, 0.5, 1.0, 1.0, 1.0, 1.0], wsp=[1.0], wl=[-1.0, 1.0, -1.0, -1.0, 0.0],
                        wfar=[-0.4, 0.8, -0.6, -0.5, -0.4])
_BAT_SPAWN = _wing_over(_SPAWN, ws=[0.2, 0.0, -0.4, -1.0, 0.9, -0.6, -0.9], wf=[1.0, 0.9, 0.6, 0.0, 0.0, 0.8, 0.1], wsp=[0.3, 0.5, 0.8, 1.0, 0.6, 1.0, 0.5],
                        wl=[0.0, 0.0, -1.0, 0.0, 1.0, -1.0, 0.0])


def _bat_rows():
    return {
        'idle': _row(8, 14, True, _bat_idle),
        'move': _row(6, 14, True, _bat_move),
        'tele': _row(4, 12, False, _nl(_BAT_TELE, 4)),
        'tele_zirh': _row(4, 12, False, _nl(_BAT_TELE_Z, 4)),
        'attack': _row(9, 14, False, lambda t: _k(t, _BAT_ATK), ts=_BAT_ATK_TS, mk=[0.28, 0.36, 0.58]),
        'hop': _row(5, 12, False, _nl(_BAT_HOP, 5)),
        'hurt': _row(3, 16, False, _nl(_BAT_HURT, 3)),
        'stagger': _row(6, 10, False, _nl(_BAT_STAGGER, 6)),
        'death': _row(9, 12, False, _nl(_BAT_DEATH, 9)),
        'spawn': _row(7, 12, False, _nl(_BAT_SPAWN, 7)),
    }


def _gh_idle(t):
    """Kayıp Ruh: gövde S dalgasıyla kıvrılır (eğilme dalgası yukarıdan aşağı akar), kuyruklar uzun ve gecikmeli."""
    s = math.sin
    return dict(REST, t=t, bob=2.6 * s(S2 * t), rot=0.07 * s(S2 * t - 1.2), skew=0.1 * s(S2 * t - 0.4), off=_jit(t, 0.7, 0.4),
                sy=1.0 + 0.04 * s(S2 * t + 0.3), sx=1.0 - 0.03 * s(S2 * t + 0.3),
                hlag=-1.2 * s(S2 * t - 1.6), fw=2.0 * s(S2 * t + 0.4), sw=0.5 * s(S2 * t - 1.8), mf=0.6 * s(S2 * t - 1.1),
                af=(0.9 + 0.15 * s(S2 * t - 0.7), 0.5 + 0.15 * s(S2 * t - 1.2)), ab=(1.2 + 0.25 * s(S2 * t + 0.2), 0.8),
                tail_w=0.75, tail_a=0.84, tail_l=1.1)


def _gh_move(t):
    s = math.sin
    return dict(REST, t=t, bob=1.8 * s(S2 * t), rot=0.32 + 0.05 * s(S2 * t - 0.8), skew=0.12 * s(S2 * t - 0.4), off=(1.0, 0.0), sy=1.06, sx=0.95,
                hlag=2.0, fw=-3.0 + 0.8 * s(S2 * t * 2), sw=-0.8 + 0.15 * s(S2 * t - 1.2), mf=1.6,
                af=(0.5, 0.7), ab=(0.4, 0.9), tail_a=0.97, tail_w=0.5, tail_k=2.0, tail_l=1.25, drag=0.9)


_GH_TELE = [(0.0, dict(bob=1.2, rot=0.06, sy=0.92, sx=1.06, skew=-0.1, sw=0.3, fw=1.0), 'io'),
            (0.33, dict(bob=-1.0, rot=-0.2, sy=1.08, sx=0.94, skew=0.12, off=(-1.5, -0.5), af=(2.4, 0.6), ab=(2.0, 0.8), sw=-1.0, flare=0.5, att=0.6, hlag=-1.8, fw=2.0, tail_w=1.0), 'o'),
            (0.66, dict(bob=-2.0, rot=-0.34, sy=1.14, sx=0.9, skew=0.18, off=(-2.5, -1.0), af=(3.0, 0.3), ab=(2.6, 0.5), sw=-2.2, flare=1.0, att=1.0, hlag=-2.6, fw=2.6, mf=1.0), 'o'),
            (1.0, dict(bob=-2.2, rot=-0.35, sy=1.15, sx=0.89, skew=0.2, off=(-2.8, -1.0), af=(3.05, 0.3), ab=(2.65, 0.5), sw=-2.4, flare=1.0, att=1.0, hlag=-2.4, fw=2.4, mf=1.1), 'io')]

_GH_TELE_Z = [(0.0, dict(bob=1.4, rot=0.08, sy=0.9, sx=1.08, sw=0.4, fw=1.0, zirh=0.3), 'io'),
              (0.33, dict(bob=-1.4, rot=-0.12, sy=1.05, sx=1.1, af=(2.6, 0.3), ab=(2.6, 0.3), sw=-1.4, flare=0.8, att=1.0, hlag=-2.6, fw=3.4, mf=1.8, zirh=0.7, tail_a=0.72, tail_w=1.1), 'o'),
              (0.66, dict(bob=-2.6, rot=-0.2, sy=1.1, sx=1.16, af=(3.2, 0.0), ab=(3.2, 0.0), sw=-3.0, flare=1.0, att=1.0, hlag=-3.0, fw=4.2, mf=2.4, zirh=1.0, tail_a=0.68, tail_w=1.2), 'o'),
              (1.0, dict(bob=-2.8, rot=-0.21, sy=1.11, sx=1.17, af=(3.25, 0.0), ab=(3.25, 0.0), sw=-3.2, flare=1.0, att=1.0, hlag=-2.8, fw=4.4, mf=2.5, zirh=1.0, tail_a=0.68, tail_w=1.2), 'io')]

# süzülüş: gövde ruh izine dönüşür (eksen boyunca uzar, kuyruklar dümdüz arkada), maske öne uzanıp çığlık atar
_GH_ATK = [(0.0, _GH_TELE[-1][1], 'l'),
           (0.28, dict(bob=1.5, rot=0.95, sy=1.38, sx=0.78, skew=-0.1, off=(3.5, 2.0), af=(1.75, 0.05), ab=(1.6, 0.1), claw=1.0, att=1.0, flare=0.8, hdx=2.0,
                       hlag=3.6, fw=-3.6, mf=2.4, tail_a=0.98, tail_w=0.2, tail_l=1.45, streak=1.2, sdir=(0.8, 0.6), drag=1.3, sw=-2.2), 'i'),
           (0.36, dict(bob=2.5, rot=1.0, sy=1.42, sx=0.76, off=(4.5, 3.0), att=1.0, streak=1.3, hlag=4.0, tail_ph=1.5, sw=-2.4), 'l'),
           (0.46, dict(bob=3.0, rot=0.8, sy=1.28, sx=0.82, off=(4.8, 3.4), att=0.9, streak=0.9, hlag=3.2, tail_ph=2.6, hdx=1.0), 'l'),
           (0.58, dict(bob=2.0, rot=-0.15, sy=0.88, sx=1.14, skew=0.2, off=(3.6, 2.4), af=(1.3, 0.7), ab=(1.2, 0.8), claw=0.4, att=0.5, streak=0.0, hdx=0.0,
                        hlag=-2.2, fw=3.0, mf=-0.6, tail_a=0.76, tail_w=1.1, tail_l=1.1, sw=1.3, drag=0.0), 'o'),
           (0.68, dict(bob=0.6, rot=-0.1, sy=1.06, sx=0.95, skew=-0.12, off=(2.6, 1.2), att=0.3, hlag=1.2, fw=-0.4, sw=0.8), 'io'),
           (0.78, dict(bob=-0.4, rot=0.04, skew=0.06, off=(1.6, 0.4), af=(0.9, 0.5), ab=(1.1, 0.7), claw=0.0, att=0.15, hlag=0.6, fw=1.0, sw=-0.2, tail_l=1.0), 'io'),
           (0.86, dict(bob=0.2, rot=0.0, skew=0.0, off=(0.8, 0.2), hlag=-0.4, fw=0.6), 'io'),
           (0.93, dict(bob=0.0, off=(0.0, 0.0), sx=1.0, sy=1.0, hlag=0.0, fw=0.5, att=0.0), 'io')]


def _gh_rows():
    return {
        'idle': _row(8, 10, True, _gh_idle),
        'move': _row(6, 12, True, _gh_move),
        'tele': _row(4, 12, False, _nl(_GH_TELE, 4)),
        'tele_zirh': _row(4, 12, False, _nl(_GH_TELE_Z, 4)),
        'attack': _row(9, 14, False, lambda t: _k(t, _GH_ATK), ts=_BAT_ATK_TS, mk=[0.28, 0.36, 0.58]),
        'hop': _row(5, 12, False, _nl(_COR_HOP, 5)),
        'hurt': _row(3, 16, False, _nl(_HURT, 3)),
        'stagger': _row(6, 10, False, _nl(_STAGGER, 6)),
        'death': _row(9, 12, False, _nl(_DEATH, 9)),
        'spawn': _row(7, 12, False, _nl(_SPAWN, 7)),
    }


_ROWS = {'ranged': _cor_rows, 'diver': _dv_rows, 'swarm': _bat_rows, 'ghost': _gh_rows}
# Enemy durumu -> satır (genel oynatım için öneri; sprite json "durum")
DURUM = {
    'ranged': {'idle': 'idle', 'chase': 'move', 'windup': 'tele', 'windup_zirh': 'tele_zirh', 'attack': 'attack', 'dive': 'dive',
               'recover': 'idle', 'evade': 'hop', 'hurt': 'hurt', 'stagger': 'stagger', 'death': 'death', 'spawn': 'spawn'},
    'diver': {'idle': 'idle', 'chase': 'move', 'windup': 'tele', 'windup_zirh': 'tele_zirh', 'dive': 'attack', 'stuck': 'stuck',
              'recover': 'attack', 'evade': 'hop', 'hurt': 'hurt', 'stagger': 'stagger', 'death': 'death', 'spawn': 'spawn'},
    'swarm': {'idle': 'idle', 'chase': 'idle', 'windup': 'tele', 'windup_zirh': 'tele_zirh', 'swoop': 'attack', 'recover': 'attack',
              'evade': 'hop', 'hurt': 'hurt', 'stagger': 'stagger', 'death': 'death', 'spawn': 'spawn'},
}
DURUM['ghost'] = DURUM['swarm']

_CACHE = {}


def anims_for(var):
    role = VARIANTS[var]['role']
    if role not in _CACHE:
        _CACHE[role] = _ROWS[role]()
    return _CACHE[role]


def durum_for(var):
    return DURUM[VARIANTS[var]['role']]


# preview_yaratik uyumu: Çor Ruhu satırları
ANIMS = {k: (v['frames'], v['pose'], v['loop'], True) for k, v in _cor_rows().items()}


def frame_time(row, i):
    if row['ts']:
        return row['ts'][i]
    if row['loop']:
        return i / row['frames']
    return i / max(1, row['frames'] - 1)


SHADE = dict(outer=0.5, rim=0.6, rim_col=(0.7, 0.78, 1.0), rim_dir=(0.6, -0.8), rim_w=1.4, form=(5.0, (0.76, 0.74, 0.88)))


def render_frame(anim, i, var='cor', ss=3):
    V = VARIANTS[var]
    row = anims_for(var)[anim]
    tt = frame_time(row, i)
    p = dict(row['pose'](tt))
    p['t'] = tt if row['loop'] else (tt * 0.6 + i * 0.13) % 1.0
    cv = u29.canvas(CELL[0], CELL[1], FEET[0], FEET[1], TEX, ss=ss)
    info = draw(cv, p, V)
    rgba, nm, em = cv.finish(**SHADE)
    if V['role'] == 'ghost':   # ruh: gövde hafif saydam
        rgba, em = u29.fade(rgba, em, 0.9)
    if p.get('dis', 0.0) > 0:
        rgba, em = u29.dissolve(rgba, em, p['dis'], seed=V['seed'] * 13 + (1 if anim == 'spawn' else 0), hd=cv.hd,
                                grad=(0.3, 0.7), hot=V['glow'], hot_a=0.9)
    return rgba, nm, em, info
