"""v28 gerçek gövde animasyonları (Bengü, stil v2 mürekkep-cel). Bkz. docs/TASARIM.md "v28: gerçek gövde animasyonları".

Eski saldırı gövdeleri (bengu.py v1 anahtarları + bengu_ink.dynamic) bacak AÇILARIYLA kurulmuştu: kalça kayınca ayaklar
yerde kayıyor, arka ayak çoğu karede yerden 3-10 birim havada asılı kalıyordu; gövde yalnızca öne / arkaya yatıyordu.
v28 pozları AYAK HEDEFLERİYLE kurulur (iki kemikli bacak IK): her anahtar kalça konumu + yüksekliği ve iki ayağın yerdeki
yeri / kalkıklığı / topuk açısıyla yazılır; böylece adım atma, kayarak duruş açma, ön ayak üstünde dönme, arka ayağın
parmak ucuyla itmesi gerçek ayak işi olur (yere basan ayak kaymaz; erişilemeyen ayak için kalça kendiliğinden iner).

Zamanlama: oyunda gövde karesi savuruşun EVRELERİNE göre seçilir (Player._body_frame): savuruşun k zamanı
[0, hit0, ck, hit1, 1] -> gövdenin kendi zamanı tau [0, W, C, H, 1] parça parça doğrusal eşlenir (MK = (W, C, H)).
Her karenin bir başlangıç anı (TS) ve çizildiği an (RT) vardır: oyun tau'dan önceki son TS'li kareyi gösterir. Böylece
temas karesi tam isabet anında (ck) açılır, derin hazırlık karesi tutuşta (hold_k) bekler, süreler / isabet anları /
vuruş kutuları değişmez; gövde savuruşun evre sürelerine gerilir.

Poz alanları (Q): hx, hy kalça (x, yerden yükseklik; dinlenme 23,3), f / b ön / arka ayak (x, kalkıklık, topuk açısı rad:
+ parmak ucunda), lean gövde eğimi, tw omuz burulması, sx omuz kayması, hdx / hdy baş (önden giden baş), ab arka kol
(oyunda iki elli olmayan silahlarda bu açılarla sürülür), sk etek savrulması, pk kuşak kuyrukları, cf post pelerin
savrulması, jaw nara, ear kulak.

v29 (docs/TASARIM.md "v29: Bengü poz cilası"): tuval bükmesi (shr / crv eylem çizgisi, stx / sty esneme-ezilme), 3/4
dönüş taklidi, v28 anahtarlarının evreye göre abartılması (v29(); omuz erim sınırıyla) ve ayak hedefli hareket gövdeleri
(durgun, koşu, depar, sıçrama, düşüş, iniş, darbe, çömelme).
"""
import math

from bengu import P

FOOT_Y = -2.1
HIP_Y = -23.6
L_THIGH, L_SHIN = 13.0, 12.6
REACH = L_THIGH + L_SHIN - 0.25
TOE_LIFT = 4.6           # topuk açısı başına ayak bileğinin kalkması (parmak ucu yerde kalsın)

# dinlenme duruşu (bengu_ink._idle ile uyumlu: alçak, geniş savaş duruşu)
REST = dict(hx=0.0, hy=23.3, f=(5.4, 0.0, 0.0), b=(-13.6, 0.0, 0.25), lean=0.16, tw=0.0, sx=0.4, hdx=0.0, hdy=0.0,
            ab=(-0.3, 0.9), sk=0.2, pk=0.3, jaw=0.0, cf=0.0, ear=0.0, br=0.0, turn=0.0,
            shr=0.0, crv=0.0, stx=1.0, sty=1.0)
# v29 eylem çizgisi / leke bozulması alanları (tüm çizime uygulanan tuval bükmesi, ayaklar yerde kalır; bkz. warp_fn):
# shr doğrusal eğme (yerden yükseklikle orantılı öne kayma), crv eğrilik (yüksekliğin karesiyle: C eğrisi; shr < 0 ile
# birlikte S eğrisi), stx / sty kalça altındaki yer noktası çevresinde esneme-ezilme (süpürme lekesi, iniş ezilmesi).

# standart 10 kare: (başlangıç tau, çizim tau). Hazırlık 3 (kalkış, kurulma, derin hazırlık / tutuş), süpürme 1 (gerilmiş
# ara poz), temas 1 (tam isabet anında), kilit 2 (aşma, tutma), toparlanma 3.
MK = (0.30, 0.42, 0.58)
STD = ((0.0, 0.05), (0.10, 0.17), (0.21, 0.29), (0.30, 0.37), (0.42, 0.42), (0.49, 0.51), (0.58, 0.62),
       (0.70, 0.74), (0.82, 0.86), (0.92, 0.97))
# çok vuruşlu / çark savuruşları: süpürme yok (ck = hit0), etkin pencere [C, H] içinde dönen kareler
SPIN = ((0.0, 0.06), (0.14, 0.2), (0.3, 0.3), (0.42, 0.42), (0.47, 0.47), (0.52, 0.52), (0.58, 0.6),
        (0.70, 0.73), (0.82, 0.86), (0.92, 0.97))


def _clamp(v, a, b):
    return a if v < a else (b if v > b else v)


def leg_ik(hip, foot, l1=L_THIGH, l2=L_SHIN):
    """İki kemikli bacak: (uyluk açısı, diz bükümü) — rig.fk_leg kuralı (0 aşağı, + ileri; diz öne bükülür)."""
    dx, dy = foot[0] - hip[0], foot[1] - hip[1]
    d = _clamp(math.hypot(dx, dy), abs(l1 - l2) + 0.5, l1 + l2 - 0.02)
    th = math.atan2(dx, dy)
    al = math.acos(_clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1.0, 1.0))
    be = math.pi - math.acos(_clamp((l1 * l1 + l2 * l2 - d * d) / (2 * l1 * l2), -1.0, 1.0))
    return (th + al, be)


def to_p(q, t=0.0):
    """Q pozu -> bengu_ink.draw parametreleri (P). Erişilemeyen yere basan ayak için kalça iner."""
    hx = q['hx']
    hip_y = FOOT_Y - q['hy']
    feet = []
    for key, ox in (('f', 1.0), ('b', 0.0)):
        fx, lift, pitch = q[key]
        fy = FOOT_Y - lift - TOE_LIFT * math.sin(max(0.0, pitch))
        dx = fx - (hx + ox)
        if abs(dx) > REACH - 0.3:
            fx = hx + ox + math.copysign(REACH - 0.3, dx)
            dx = fx - (hx + ox)
        hip_y = max(hip_y, fy - math.sqrt(max(0.0, REACH * REACH - dx * dx)))
        feet.append((fx, fy, pitch))
    lf = leg_ik((hx + 1.0, hip_y), feet[0][:2])
    lb = leg_ik((hx, hip_y), feet[1][:2])
    return P(bob=(hip_y - HIP_Y) / 1.1, hx=hx, lf=lf, lb=lb, lean=q['lean'], tw=q['tw'], sx=q['sx'], hdx=q['hdx'],
             hdy=q['hdy'], ab=tuple(q['ab']), sk=q['sk'], pk=q['pk'], jaw=q['jaw'], ear=q['ear'], br=q['br'],
             bp=q.get('bp', t), cf=q['cf'], fpf=feet[0][2], fpb=feet[1][2], turn=q.get('turn', 0.0),
             shr=q.get('shr', 0.0), crv=q.get('crv', 0.0), stx=q.get('stx', 1.0), sty=q.get('sty', 1.0),
             **({'af': tuple(q['af'])} if 'af' in q else {}))


def warp_fn(p):
    """v29 tuval bükmesi (dönüş + esneme-ezilme + eylem çizgisi). None: bükme yok. Yer çizgisi (FOOT_Y) sabit kalır:
    yere basan ayak kaymaz; eğme / eğrilik yükseklikle büyür (baş en çok kayar: önden giden baş, C / S eğrisi)."""
    turn = p.get('turn', 0.0)
    shr, crv = p.get('shr', 0.0), p.get('crv', 0.0)
    stx, sty = p.get('stx', 1.0), p.get('sty', 1.0)
    if abs(turn) <= 1e-3 and abs(shr) < 1e-4 and abs(crv) < 1e-4 and abs(stx - 1.0) < 1e-4 and abs(sty - 1.0) < 1e-4:
        return None
    hx = p.get('hx', 0.0)
    cx = hx + 2.0
    if abs(turn) > 1e-3:
        # v29: dönüşte en dar 0,72 (v28: 0,6, ince şerit gibi görünüyordu); genişlik |cos| ile yumuşak azalır
        c_ = math.cos(math.pi * turn)
        s_ = math.copysign(0.72 + 0.28 * abs(c_), c_)
    else:
        s_ = 1.0
    gy = FOOT_Y + 1.0

    s_up = math.copysign(max(abs(s_), 0.88), s_)

    def f(q):
        x, y = q[0], q[1]
        if s_ != 1.0:
            # 3/4 dönüş taklidi: bacak / kalça tam daralır, gövde ve baş daha az (göğüs önden geniş görünür, kalça önden
            # döner — omuzlar bir adım geriden gelir)
            u = _clamp((gy - y - 14.0) / 20.0, 0.0, 1.0)
            u = u * u * (3 - 2 * u)
            x = cx + (x - cx) * (s_ + (s_up - s_) * u)
            x = hx + (x - hx) * stx
            y = gy + (y - gy) * sty
            h = max(0.0, gy - y)
            return (x + shr * h + crv * h * h / 40.0, y)
        x = hx + (x - hx) * stx
        y = gy + (y - gy) * sty
        h = max(0.0, gy - y)
        return (x + shr * h + crv * h * h / 40.0, y)
    f.s_ = s_
    return f


def shoulder(q):
    """Q pozunda ön omuz (sh_f) dünya konumu: bengu_ink.draw ile aynı kural + bükme (erim denetimi)."""
    from bengu_v2 import TORSO
    p = to_p(q)
    hip = (p['hx'], HIP_Y + p['bob'] * 1.1)
    tl = TORSO + p['br'] * 0.3
    neck = (hip[0] + math.sin(p['lean']) * tl, hip[1] - math.cos(p['lean']) * tl)
    s = (neck[0] + 1.4 + p['sx'] + p['tw'] * 0.7, neck[1] + 3.2)
    w = warp_fn(p)
    return w(s) if w else s


def Q(base=None, **kw):
    q = dict(REST if base is None else base)
    q.update(kw)
    return q


def _ease(u, e):
    u = _clamp(u, 0.0, 1.0)
    if e == 'l':
        return u
    if e == 'i':          # hızlanarak (vuruş)
        return u * u * u
    if e == 'i2':
        return u * u
    if e == 'o':          # yavaşlayarak (oturma, takip)
        return 1.0 - (1.0 - u) ** 3
    if e == 'o2':
        return 1.0 - (1.0 - u) ** 2
    if e == 'h':          # tut, sonra hızla geç
        return 0.0 if u < 0.5 else _ease((u - 0.5) * 2.0, 'io')
    return u * u * (3 - 2 * u)


def _mix(a, b, u):
    out = {}
    for k, va in a.items():
        vb = b.get(k, va)
        if isinstance(va, tuple):
            out[k] = tuple(x + (y - x) * u for x, y in zip(va, vb))
        else:
            out[k] = va + (vb - va) * u
    return out


class Anim:
    """keys: [(tau, Q, ease)] (ease: bu anahtara VARAN parçanın eğrisi). frames: [(ts, rt)]."""

    def __init__(self, keys, frames=STD, marks=MK, fps=12, flap=1.0):
        self.keys = keys
        self.frames = frames
        self.marks = marks
        self.fps = fps
        self.flap = flap

    def q(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return dict(ks[0][1])
        for (t0, q0, _e0), (t1, q1, e1) in zip(ks, ks[1:]):
            if t <= t1:
                u = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                return _mix(q0, q1, _ease(u, e1))
        return dict(ks[-1][1])

    def __call__(self, t):
        q = self.q(t)
        q.setdefault('bp', t * 1.6 * self.flap)
        return to_p(q, t)


V28 = {}      # ad -> Anim


def _shift(q, dx):
    q = dict(q)
    q['hx'] -= dx
    q['f'] = (q['f'][0] - dx,) + tuple(q['f'][1:])
    q['b'] = (q['b'][0] - dx,) + tuple(q['b'][1:])
    return q


# erim dengesi: temas / kilit / toparlanma başında tüm duruş bu kadar geri (dünya birimi). Vuruş kutuları sabit; derin
# öne çöken pozlarda omuz (dolayısıyla bıçak) v27 temas karesinden en çok ~6-8 birim önde kalsın.
PULL = {'atk_heavy': 3.0, 'atk_overhead_2h': 3.0, 'atk_slam_jump': 3.0, 'atk_a_chop': 2.0, 'atk_dual': 2.0,
        'atk_whip': 2.0, 'atk_horiz': 1.5, 'atk_k_step': 1.5, 'atk_h_spin': 2.0, 'atk_h_flurry': 1.5}


# ====================================================================== v29 poz cilası (abartı katmanı)
# v28 anahtarları korunur (ayak işi, evreler); v29 her anahtarı evresine göre dinlenme duruşundan uzaklaştırır (abartı),
# eylem çizgisi / leke bükmesi ekler, temas-kilitte arka bacağı düz iter ve toparlanmayı dinlenme duruşuna bağlar.
# Erim: abartılmış pozun ön omzu v28 omzundan en çok OMUZ_X öne / OMUZ_Y aşağı kayabilir (fazlası tüm duruşu geri
# kaydırır / kalçayı kaldırır): bıçak temas karesinde vuruş kutusunun payı içinde kalır.
OMUZ_X, OMUZ_Y = 2.5, 3.0
FOOT_G = 1.22           # ayak yerlerinin dinlenmeden uzaklaşma katsayısı (daha geniş adım / duruş)
# evre -> (abartı katsayısı, ayak katsayısı)
GAIN = ((0.13, 1.25, 1.1), (0.2, 1.35, 1.15), (0.31, 1.6, 1.25), (0.38, 1.45, 1.25), (0.45, 1.6, 1.3),
        (0.56, 1.5, 1.25), (0.66, 1.25, 1.15), (0.85, 1.05, 1.0))
AMP_KEYS = ('hx', 'lean', 'tw', 'sx', 'cf', 'sk', 'pk')
# aile vuruş yönü: fwd (öne kesik / saplama), down (çakma), up (yükselen), back (geri çekerek), spin (dönüş), air
STYLE = {'atk_up': 'up', 'atk_uppercut': 'up', 'atk_a_lift': 'up', 'atk_m_rise': 'up', 'atk_backstep': 'back',
         'atk_u_reap': 'back', 'atk_heavy': 'down', 'atk_overhead_2h': 'down', 'atk_a_chop': 'down',
         'atk_slam_jump': 'air', 'atk_spin': 'spin', 'atk_spin_2h': 'spin', 'atk_w_whirl': 'spin',
         'atk_h_spin': 'spin', 'atk_down': 'down', 'atk_k_step': 'down', 'bow': 'none', 'throw': 'none',
         'cast': 'none'}
# evre -> stil -> bükme (shr, crv, stx, sty)
WARP = {
    'ant': {'fwd': (-0.02, -0.06, 1.0, 1.0), 'down': (-0.01, -0.07, 0.98, 1.04), 'up': (0.0, 0.02, 1.04, 0.95),
            'back': (0.03, 0.03, 1.0, 0.98), 'spin': (0.0, -0.02, 1.0, 0.98), 'air': (0.0, -0.04, 1.0, 1.02),
            'coil': (0.0, 0.03, 1.05, 0.93)},
    'smear': {'fwd': (0.07, 0.02, 1.1, 0.95), 'down': (0.05, 0.05, 1.04, 1.04), 'up': (0.02, -0.02, 0.95, 1.09),
              'back': (-0.06, -0.02, 1.08, 0.96), 'spin': (0.0, 0.0, 1.0, 1.0), 'air': (0.03, 0.03, 0.97, 1.06)},
    'hit': {'fwd': (0.03, 0.05, 1.04, 0.98), 'down': (0.02, 0.045, 1.03, 0.97), 'up': (0.0, -0.035, 0.97, 1.06),
            'back': (-0.03, -0.04, 1.03, 0.98), 'spin': (0.0, 0.02, 1.0, 1.0), 'air': (0.02, 0.07, 1.08, 0.93)},
    'lock': {'fwd': (0.02, 0.035, 1.02, 0.98), 'down': (0.01, 0.035, 1.02, 0.98), 'up': (0.0, -0.025, 0.98, 1.04),
             'back': (-0.02, -0.03, 1.02, 0.99), 'spin': (0.0, 0.01, 1.0, 1.0), 'air': (0.01, 0.05, 1.05, 0.95)},
    'hold': {'fwd': (0.0, 0.015, 1.0, 1.0), 'down': (0.0, 0.02, 1.01, 0.99), 'up': (0.0, -0.01, 1.0, 1.01),
             'back': (0.0, -0.01, 1.0, 1.0), 'spin': (0.0, 0.0, 1.0, 1.0), 'air': (0.0, 0.02, 1.02, 0.98)},
}
V29_OFF = False         # True: v28 pozları (karşılaştırma)
OVR = {}                # ad -> {tau: {alan: değer}} el ayarı (abartıdan sonra, mutlak değer)


def _gain(t):
    for t1, g, gf in GAIN:
        if t <= t1:
            return g, gf
    return 1.0, 1.0


def _phase(t, marks):
    W, C, H = marks
    if t <= 0.02 or t >= 0.9:
        return None
    if t < W - 0.03:
        return 'ant'
    if t < C - 0.001:
        return 'smear'
    if t < C + 0.05:
        return 'hit'
    if t < H - 0.02:
        return 'lock'
    if t < H + 0.08:
        return 'hold'
    return None


def _straight_back(q, k=0.985, exact=False):
    """Arka bacak düz (temas: arka ayak gerilmiş, topuk kalkık iter): ayak, kalçadan erime yakın uzaklığa geri itilir."""
    q = dict(q)
    bx, lift, pitch = q['b']
    pitch = max(pitch, 0.7)
    hip_h = q['hy'] - TOE_LIFT * math.sin(pitch) - lift
    d = math.sqrt(max(0.0, (REACH * k) ** 2 - hip_h * hip_h))
    q['b'] = (q['hx'] - d if exact else min(bx, q['hx'] - d), lift, pitch)
    return q


def v29(name, keys, marks=MK):
    if V29_OFF:
        return keys
    st = STYLE.get(name, 'fwd')
    if st == 'none':
        return keys
    out = []
    for t, q, e in keys:
        q = dict(q)
        q0 = dict(q)
        ph = _phase(t, marks)
        if ph is None:
            if t >= 0.9:          # toparlanma sonu = dinlenme duruşu (idle'a sıçramasız geçiş)
                q = Q(ab=q['ab'], turn=q.get('turn', 0.0) % 2.0)
            out.append((t, q, e))
            continue
        g, gf = _gain(t)
        for k_ in AMP_KEYS:
            q[k_] = REST[k_] + (q[k_] - REST[k_]) * g
        # önden giden baş: öne itme abartılır, başı eğme (hdy) abartılmaz — baş hedefe bakar, göğüs açık kalır
        q['hdx'] = q['hdx'] * (1.0 + (g - 1.0) * 1.6)
        lo = 15.0 if ph in ('hit', 'lock') and st in ('fwd', 'down') else 11.5
        q['hy'] = _clamp(REST['hy'] + (q['hy'] - REST['hy']) * g, min(lo, q0['hy']), 34.0)
        q['lean'] = _clamp(q['lean'], min(q0['lean'], -0.5), max(q0['lean'], 0.72 if st == 'fwd' else 0.8))
        for fk, f0 in (('f', REST['f'][0]), ('b', REST['b'][0])):
            fx, lift, pitch = q[fk]
            # tek ayak katsayısı (anahtarlar arasında yere basan ayak kaymasın)
            q[fk] = (f0 + (fx - f0) * FOOT_G, lift * g, _clamp(pitch, -0.4, 1.15))
        if 'jaw' in q:
            q['jaw'] = min(1.0, q['jaw'] * 1.15)
        sty_ = st
        if ph == 'ant' and st == 'fwd' and q0['lean'] > 0.3:
            sty_ = 'coil'           # öne çömelerek kurulma: sıkışma (esneme-ezilme)
        if ph == 'ant' and st in ('down', 'up', 'back', 'spin', 'air'):
            sty_ = st
        w = WARP[ph].get(sty_, WARP[ph]['fwd'])
        q['shr'], q['crv'], q['stx'], q['sty'] = w
        if ph == 'ant' and sty_ == 'fwd' and t > 0.2:
            # ağırlık arka bacakta: ön ayak hafifçe kalkık (adıma hazır), kalça biraz daha geride
            q['f'] = (q['f'][0], q['f'][1] + 1.6, min(q['f'][2], -0.2))
            q['hx'] -= 0.8
        if ph in ('hit', 'lock') and st in ('fwd', 'down'):
            q = _straight_back(q)
        if ph in ('smear', 'hit', 'lock') and st == 'up':
            # yükselen kesik: parmak ucunda tam gerilme, sırt geriye kavisli, baş yukarı (dikey eylem çizgisi)
            k_ = 0.5 if ph == 'smear' else 1.0
            q['hy'] += 3.0 * k_
            q['lean'] -= 0.12 * k_
            q['hdy'] -= 0.8 * k_
            q['f'] = (q['f'][0], q['f'][1], max(q['f'][2], 0.55 * k_))
            q['b'] = (q['b'][0], q['b'][1] + 1.0 * k_, max(q['b'][2], 0.9 * k_))
        for k_, v in OVR.get(name, {}).get(t, {}).items():
            q[k_] = v
        # erim: ön omuz v28'den çok kaçmasın (vuruş kutusu sabit)
        if ph in ('smear', 'hit', 'lock', 'hold') and abs((q.get('turn', 0.0) + 1.0) % 2.0 - 1.0) < 0.2:
            s0 = shoulder(q0)
            for _it in range(4):
                s1 = shoulder(q)
                dx, dy = s1[0] - s0[0], s1[1] - s0[1]
                if dx <= OMUZ_X + 0.05 and dy <= OMUZ_Y + 0.05:
                    break
                if dy > OMUZ_Y:
                    q['hy'] += dy - OMUZ_Y
                    if ph in ('hit', 'lock') and st in ('fwd', 'down'):
                        q = _straight_back(q, exact=True)
                if dx > OMUZ_X:
                    q = _shift(q, dx - OMUZ_X)
        out.append((t, q, e))
    return out


def add(name, keys, frames=STD, marks=MK, fps=12, flap=1.0):
    keys = v29(name, keys, marks)
    dx = PULL.get(name, 0.0)
    if dx:
        keys = [(t, _shift(q, dx * (1.0 if 0.36 <= t <= 0.66 else 0.5 if 0.66 < t < 0.9 else 0.0)), e)
                for t, q, e in keys]
    V28[name] = Anim(keys, frames, marks, fps, flap)
    return V28[name]


# ====================================================================== pozlar
# Kılıç (temel gövdeler; kilic / düello ailesi bunları kullanır, diğer aileler yoksa bunlara düşer)
END = Q(hx=1.5, f=(8.4, 0.0, 0.0), b=(-11.6, 0.0, 0.25))      # toparlanma sonu (dinlenmeye yakın, yarım adım önde)

# ---------------------------------------------------------------------- yatay kesik: geniş duruş, kalça önden döner
add('atk_horiz', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-2.5, hy=21.5, f=(4.5, 0.0, 0.0), b=(-14.5, 0.0, 0.0), lean=-0.12, tw=-1.0, sx=-1.4, hdx=-0.3,
             ab=(0.6, 0.7), sk=0.4, pk=0.5), 'o'),
    (0.30, Q(hx=-5.0, hy=19.8, f=(4.5, 0.0, -0.2), b=(-15.0, 0.0, 0.0), lean=-0.28, tw=-1.8, sx=-2.8, hdx=-0.2,
             hdy=0.6, ab=(1.0, 0.5), sk=0.6, pk=0.7, cf=-0.4), 'o'),
    (0.37, Q(hx=3.4, hy=19.6, f=(12.0, 2.2, 0.0), b=(-15.2, 0.0, 0.35), lean=0.32, tw=0.4, sx=1.6, hdx=0.8,
             ab=(-0.4, 0.6), sk=-0.5, pk=-0.6, jaw=0.5, cf=0.6), 'i'),
    (0.42, Q(hx=6.0, hy=17.8, f=(16.5, 0.0, 0.0), b=(-14.2, 0.0, 0.6), lean=0.48, tw=1.5, sx=3.0, hdx=1.4,
             hdy=0.6, ab=(-1.25, 0.5), sk=-0.9, pk=-1.0, jaw=0.9, cf=1.0), 'i2'),
    (0.52, Q(hx=6.8, hy=17.0, f=(16.5, 0.0, 0.0), b=(-13.4, 0.0, 0.7), lean=0.56, tw=1.9, sx=3.4, hdx=1.6,
             hdy=0.9, ab=(-1.45, 0.45), sk=-1.1, pk=-1.2, jaw=0.7, cf=0.8), 'o'),
    (0.62, Q(hx=5.6, hy=18.4, f=(16.5, 0.0, 0.0), b=(-13.0, 0.0, 0.4), lean=0.4, tw=1.0, sx=2.2, hdx=1.0,
             hdy=0.5, ab=(-0.9, 0.6), sk=-0.5, pk=-0.4, jaw=0.2, cf=0.3), 'o'),
    (0.8, Q(hx=3.2, hy=21.4, f=(12.5, 0.0, 0.0), b=(-11.0, 1.6, 0.2), lean=0.26, tw=0.4, sx=1.0, ab=(-0.5, 0.8),
            sk=0.1, pk=0.1), 'io'),
    (1.0, END, 'io'),
])

# ---------------------------------------------------------------------- yukarıdan iniş: parmak ucunda kurulur, adımla çöker
_DOWN = [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-1.5, hy=23.0, f=(3.5, 1.2, 0.0), b=(-13.5, 0.0, 0.2), lean=-0.15, tw=-0.6, sx=-1.0, hdy=-0.3,
             ab=(1.0, 0.6), sk=0.3, pk=0.4), 'o'),
    (0.30, Q(hx=-3.0, hy=24.4, f=(2.0, 2.6, 0.3), b=(-12.5, 0.0, 0.5), lean=-0.34, tw=-1.2, sx=-2.0, hdx=-0.4,
             hdy=-0.8, ab=(1.3, 0.5), sk=0.5, pk=0.6, cf=-0.3, ear=0.2), 'o'),
    (0.37, Q(hx=3.0, hy=21.0, f=(12.5, 2.0, 0.0), b=(-14.5, 0.0, 0.5), lean=0.25, tw=0.2, sx=1.2, hdx=0.8, hdy=0.2,
             ab=(0.8, 0.4), sk=-0.4, pk=-0.5, jaw=0.6, cf=0.7), 'i'),
    (0.42, Q(hx=6.2, hy=16.5, f=(17.5, 0.0, 0.0), b=(-13.5, 0.0, 0.7), lean=0.62, tw=1.2, sx=2.6, hdx=1.4, hdy=1.0,
             ab=(-1.0, 0.5), sk=-1.0, pk=-1.1, jaw=1.0, cf=1.0), 'i2'),
    (0.52, Q(hx=6.8, hy=15.6, f=(17.5, 0.0, 0.0), b=(-13.0, 0.0, 0.75), lean=0.72, tw=1.5, sx=3.0, hdx=1.6, hdy=1.4,
             ab=(-1.3, 0.4), sk=-1.2, pk=-1.2, jaw=0.6, cf=0.8), 'o'),
    (0.62, Q(hx=5.8, hy=17.2, f=(17.5, 0.0, 0.0), b=(-12.6, 0.0, 0.4), lean=0.5, tw=0.8, sx=2.0, hdx=1.0, hdy=0.8,
             ab=(-0.8, 0.6), sk=-0.5, pk=-0.4, cf=0.3), 'o'),
    (0.80, Q(hx=3.4, hy=21.0, f=(13.0, 0.0, 0.0), b=(-10.5, 1.8, 0.2), lean=0.3, tw=0.3, sx=1.0, ab=(-0.5, 0.8),
             sk=0.1, pk=0.1), 'io'),
    (1.0, END, 'io'),
]
add('atk_down', _DOWN)

# adımlı iniş (kılıç / düello step_down): daha yüksek kurulma, daha uzun adım, daha derin çökme
add('atk_k_step', [
    (0.0, Q(), 'io'),
    (0.15, Q(_DOWN[1][1], hy=23.6, f=(2.5, 2.0, 0.2), ab=(1.1, 0.5)), 'o'),
    (0.30, Q(hx=-3.6, hy=25.0, f=(1.0, 3.6, 0.4), b=(-12.0, 0.0, 0.7), lean=-0.42, tw=-1.4, sx=-2.4, hdx=-0.6,
             hdy=-1.0, ab=(1.4, 0.4), sk=0.6, pk=0.7, cf=-0.5, ear=0.3, jaw=0.2), 'o'),
    (0.37, Q(hx=3.6, hy=21.5, f=(15.0, 2.6, 0.0), b=(-15.0, 0.0, 0.6), lean=0.22, tw=0.2, sx=1.2, hdx=0.8,
             ab=(0.8, 0.4), sk=-0.5, pk=-0.6, jaw=0.7, cf=0.8), 'i'),
    (0.42, Q(hx=7.0, hy=15.0, f=(19.5, 0.0, 0.0), b=(-13.5, 0.0, 0.8), lean=0.66, tw=1.3, sx=2.8, hdx=1.5,
             hdy=1.2, ab=(-1.1, 0.5), sk=-1.1, pk=-1.2, jaw=1.0, cf=1.1), 'i2'),
    (0.52, Q(hx=7.6, hy=14.2, f=(19.5, 0.0, 0.0), b=(-13.0, 0.0, 0.85), lean=0.76, tw=1.6, sx=3.1, hdx=1.7,
             hdy=1.6, ab=(-1.4, 0.4), sk=-1.2, pk=-1.2, jaw=0.6, cf=0.8), 'o'),
    (0.62, Q(hx=6.6, hy=16.0, f=(19.0, 0.0, 0.0), b=(-12.5, 0.0, 0.5), lean=0.54, tw=0.9, sx=2.1, hdx=1.1,
             hdy=1.0, ab=(-0.8, 0.6), sk=-0.5, pk=-0.4, cf=0.3), 'o'),
    (0.80, Q(hx=4.2, hy=20.5, f=(14.0, 0.0, 0.0), b=(-9.5, 2.0, 0.2), lean=0.32, tw=0.3, sx=1.0, ab=(-0.5, 0.8),
             sk=0.1, pk=0.1), 'io'),
    (1.0, Q(END, hx=2.5, f=(9.4, 0.0, 0.0), b=(-10.6, 0.0, 0.25)), 'io'),
])

# ---------------------------------------------------------------------- yükselen kesik: çömel, parmak ucunda yüksel
add('atk_up', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=0.5, hy=20.0, f=(7.0, 0.0, 0.0), b=(-13.5, 0.0, 0.3), lean=0.3, tw=-0.6, sx=-0.8, hdy=0.6,
             ab=(-0.8, 0.6), sk=0.3, pk=0.3), 'o'),
    (0.30, Q(hx=1.0, hy=16.0, f=(9.0, 0.0, 0.0), b=(-13.0, 0.0, 0.6), lean=0.5, tw=-1.2, sx=-1.8, hdx=0.4, hdy=1.2,
             ab=(-1.4, 0.5), sk=0.6, pk=0.4, cf=-0.2), 'o'),
    (0.37, Q(hx=3.2, hy=21.5, f=(12.0, 0.0, 0.0), b=(-11.5, 0.0, 0.9), lean=0.2, tw=0.4, sx=1.0, hdx=0.6, hdy=-0.4,
             ab=(-0.6, 0.5), sk=-0.2, pk=-0.6, jaw=0.6, cf=0.6), 'i'),
    (0.42, Q(hx=4.6, hy=25.0, f=(12.5, 0.0, 0.2), b=(-9.5, 1.0, 1.0), lean=-0.1, tw=1.2, sx=2.2, hdx=0.6, hdy=-1.2,
             ab=(-1.6, 0.3), sk=-0.6, pk=-1.1, jaw=1.0, cf=1.0), 'i2'),
    (0.52, Q(hx=5.0, hy=26.2, f=(12.0, 1.2, 0.5), b=(-8.0, 3.0, 0.9), lean=-0.2, tw=1.4, sx=2.4, hdx=0.4, hdy=-1.5,
             ab=(-1.8, 0.3), sk=-0.9, pk=-1.3, jaw=0.6, cf=0.9), 'o'),
    (0.62, Q(hx=4.4, hy=21.0, f=(12.0, 0.0, 0.0), b=(-10.0, 0.0, 0.4), lean=0.15, tw=0.6, sx=1.4, hdy=0.3,
             ab=(-0.9, 0.6), sk=0.4, pk=0.5, cf=0.2), 'i2'),
    (0.80, Q(hx=2.8, hy=22.0, f=(10.5, 0.0, 0.0), b=(-11.5, 0.0, 0.3), lean=0.2, ab=(-0.5, 0.8), sk=0.2, pk=0.3), 'o'),
    (1.0, END, 'io'),
])

# ---------------------------------------------------------------------- saplama: eskrim hamlesi (arka ayak düz, kol geride)
add('atk_thrust', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-2.0, hy=22.0, f=(5.5, 0.0, 0.0), b=(-14.0, 0.0, 0.1), lean=0.0, tw=-0.8, sx=-1.4, ab=(-1.4, 0.9),
             sk=0.3, pk=0.4), 'o'),
    (0.30, Q(hx=-4.2, hy=20.5, f=(5.0, 0.0, -0.15), b=(-15.0, 0.0, 0.0), lean=-0.12, tw=-1.4, sx=-2.6, hdx=0.2,
             ab=(-2.3, 1.0), sk=0.5, pk=0.6, cf=-0.3), 'o'),
    (0.37, Q(hx=2.5, hy=19.0, f=(13.0, 2.6, -0.2), b=(-15.0, 0.0, 0.0), lean=0.25, tw=0.2, sx=0.8, hdx=0.8,
             ab=(-1.9, 0.5), sk=-0.6, pk=-0.7, jaw=0.5, cf=0.7), 'i'),
    (0.42, Q(hx=6.5, hy=16.0, f=(19.0, 0.0, 0.0), b=(-14.5, 0.0, 0.0), lean=0.36, tw=1.2, sx=2.8, hdx=1.4, hdy=0.4,
             ab=(-1.55, 0.1), sk=-1.0, pk=-1.1, jaw=0.9, cf=1.0), 'i2'),
    (0.52, Q(hx=7.0, hy=15.4, f=(19.0, 0.0, 0.0), b=(-14.0, 0.0, 0.0), lean=0.42, tw=1.4, sx=3.0, hdx=1.6, hdy=0.6,
             ab=(-1.6, 0.05), sk=-1.1, pk=-1.2, jaw=0.6, cf=0.8), 'o'),
    (0.62, Q(hx=5.4, hy=17.5, f=(18.0, 0.0, 0.0), b=(-13.0, 0.0, 0.0), lean=0.3, tw=0.8, sx=2.0, ab=(-1.2, 0.4),
             sk=-0.4, pk=-0.4, cf=0.3), 'o'),
    (0.80, Q(hx=2.0, hy=21.5, f=(10.5, 1.4, 0.0), b=(-12.5, 0.0, 0.1), lean=0.2, ab=(-0.6, 0.8), sk=0.2, pk=0.2), 'io'),
    (1.0, END, 'io'),
])

# ---------------------------------------------------------------------- hücum (lunge, Şimşek Çekişi): koşucu çıkışı
add('atk_lunge', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-1.0, hy=19.5, f=(5.0, 0.0, 0.0), b=(-12.5, 0.0, 0.4), lean=0.35, tw=-0.6, sx=-0.8, hdx=0.3, hdy=0.8,
             ab=(-0.8, 0.6), sk=0.4, pk=0.4), 'o'),
    (0.30, Q(hx=-1.5, hy=15.5, f=(6.0, 0.0, 0.0), b=(-12.0, 0.0, 0.9), lean=0.62, tw=-1.2, sx=-1.6, hdx=0.8, hdy=1.6,
             ab=(-1.2, 0.8), sk=0.6, pk=0.5, cf=-0.3, ear=0.3), 'o'),
    (0.37, Q(hx=6.0, hy=17.0, f=(17.0, 3.0, 0.0), b=(-9.0, 0.0, 1.0), lean=0.62, tw=0.4, sx=1.4, hdx=1.6, hdy=1.0,
             ab=(-1.6, 0.4), sk=-1.0, pk=-1.3, jaw=0.6, cf=1.0), 'i'),
    (0.42, Q(hx=8.5, hy=14.8, f=(22.0, 0.0, 0.0), b=(-11.0, 0.0, 0.8), lean=0.66, tw=1.3, sx=3.0, hdx=1.8, hdy=1.2,
             ab=(-1.7, 0.2), sk=-1.2, pk=-1.4, jaw=1.0, cf=1.2), 'i2'),
    (0.52, Q(hx=9.0, hy=14.2, f=(22.0, 0.0, 0.0), b=(-10.5, 0.0, 0.85), lean=0.72, tw=1.5, sx=3.2, hdx=2.0, hdy=1.4,
             ab=(-1.8, 0.15), sk=-1.3, pk=-1.4, jaw=0.6, cf=1.0), 'o'),
    (0.62, Q(hx=8.0, hy=16.0, f=(21.5, 0.0, 0.0), b=(-10.0, 0.0, 0.5), lean=0.55, tw=0.9, sx=2.2, hdx=1.2, hdy=0.8,
             ab=(-1.1, 0.5), sk=-0.5, pk=-0.5, cf=0.4), 'o'),
    (0.80, Q(hx=5.0, hy=20.5, f=(15.0, 0.0, 0.0), b=(-8.0, 1.8, 0.3), lean=0.32, tw=0.3, sx=1.0, ab=(-0.6, 0.8),
             sk=0.2, pk=0.1), 'io'),
    (1.0, Q(END, hx=2.5, f=(9.4, 0.0, 0.0), b=(-10.6, 0.0, 0.25)), 'io'),
])

# ---------------------------------------------------------------------- iaido çekişi (iai, Yıldırım çekişi, düello ters tutuş)
add('atk_iai', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-1.0, hy=20.5, f=(6.5, 0.0, 0.0), b=(-14.0, 0.0, 0.2), lean=0.3, tw=-0.8, sx=-0.6, hdx=0.5, hdy=0.6,
             ab=(0.4, 1.5), sk=0.3, pk=0.3), 'o'),
    (0.30, Q(hx=-2.0, hy=16.5, f=(8.0, 0.0, 0.0), b=(-14.5, 0.0, 0.5), lean=0.48, tw=-1.3, sx=-1.2, hdx=1.0, hdy=1.2,
             ab=(0.6, 1.6), sk=0.5, pk=0.5, cf=-0.2, ear=0.3), 'o'),
    (0.37, Q(hx=5.0, hy=16.0, f=(17.0, 2.4, 0.0), b=(-12.5, 0.0, 0.8), lean=0.4, tw=0.6, sx=1.4, hdx=1.4, hdy=0.8,
             ab=(0.3, 1.2), sk=-0.9, pk=-1.2, jaw=0.4, cf=1.0), 'i'),
    (0.42, Q(hx=8.0, hy=15.0, f=(21.0, 0.0, 0.0), b=(-12.0, 0.0, 0.9), lean=0.38, tw=1.4, sx=2.8, hdx=1.6, hdy=0.8,
             ab=(-1.5, 0.3), sk=-1.2, pk=-1.4, jaw=0.9, cf=1.2), 'i2'),
    (0.52, Q(hx=8.4, hy=14.6, f=(21.0, 0.0, 0.0), b=(-11.5, 0.0, 0.95), lean=0.34, tw=1.6, sx=3.0, hdx=1.6, hdy=0.6,
             ab=(-1.7, 0.2), sk=-1.0, pk=-1.1, jaw=0.3, cf=0.8), 'o'),
    (0.62, Q(hx=8.2, hy=15.2, f=(21.0, 0.0, 0.0), b=(-11.5, 0.0, 0.8), lean=0.3, tw=1.4, sx=2.6, hdx=1.4, hdy=0.4,
             ab=(-1.6, 0.25), sk=-0.5, pk=-0.5, cf=0.4), 'o'),
    (0.80, Q(hx=5.4, hy=20.5, f=(16.0, 0.0, 0.0), b=(-8.5, 1.6, 0.2), lean=0.12, tw=0.3, sx=0.8, hdy=-0.2,
             ab=(0.4, 1.5), sk=0.1, pk=0.1), 'io'),
    (1.0, Q(END, hx=3.0, f=(10.4, 0.0, 0.0), b=(-10.0, 0.0, 0.25), ab=(0.2, 1.2)), 'io'),
])

# ---------------------------------------------------------------------- ağır iniş (ağır aile): omuz üstü büyük kurulma, çakma
add('atk_heavy', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-2.0, hy=22.5, f=(5.0, 0.0, 0.0), b=(-14.5, 0.0, 0.0), lean=-0.15, tw=-0.8, sx=-1.4, hdx=-0.3,
             ab=(2.2, 0.6), sk=0.4, pk=0.4), 'o'),
    (0.30, Q(hx=-4.5, hy=23.0, f=(3.0, 4.5, 0.4), b=(-14.0, 0.0, 0.0), lean=-0.42, tw=-1.8, sx=-2.8, hdx=-0.8,
             hdy=-0.6, ab=(2.8, 0.5), sk=0.7, pk=0.7, cf=-0.5, jaw=0.3, ear=0.2), 'o'),
    (0.37, Q(hx=2.0, hy=21.0, f=(13.0, 0.8, 0.0), b=(-15.0, 0.0, 0.3), lean=0.15, tw=-0.2, sx=0.4, hdx=0.6,
             ab=(1.8, 0.4), sk=-0.3, pk=-0.4, jaw=0.7, cf=0.6), 'i'),
    (0.42, Q(hx=5.0, hy=14.5, f=(15.5, 0.0, 0.0), b=(-14.5, 0.0, 0.8), lean=0.78, tw=1.2, sx=2.4, hdx=1.2, hdy=1.8,
             ab=(0.6, 0.4), sk=-1.0, pk=-1.0, jaw=1.0, cf=1.1), 'i2'),
    (0.52, Q(hx=5.2, hy=13.4, f=(15.5, 0.0, 0.0), b=(-14.0, 0.0, 0.9), lean=0.85, tw=1.3, sx=2.6, hdx=1.3, hdy=2.2,
             ab=(0.4, 0.5), sk=-0.6, pk=-0.4, jaw=0.6, cf=0.4), 'o'),
    (0.62, Q(hx=4.8, hy=15.0, f=(15.5, 0.0, 0.0), b=(-13.5, 0.0, 0.6), lean=0.7, tw=1.0, sx=2.2, hdx=1.0, hdy=1.6,
             ab=(0.2, 0.6), sk=0.2, pk=0.4), 'o'),
    (0.80, Q(hx=3.2, hy=20.0, f=(12.5, 0.0, 0.0), b=(-11.5, 1.4, 0.2), lean=0.4, tw=0.4, sx=1.0, hdy=0.4,
             ab=(-0.3, 0.8), sk=0.2, pk=0.2), 'io'),
    (1.0, END, 'io'),
])

# ---------------------------------------------------------------------- ağır tek el doğrama (gürz / topuz / balta iniş)
add('atk_a_chop', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-2.0, hy=22.5, f=(5.0, 0.0, 0.0), b=(-14.5, 0.0, 0.0), lean=-0.2, tw=-1.2, sx=-1.8, hdx=-0.3,
             ab=(1.2, 0.8), sk=0.4, pk=0.4), 'o'),
    (0.30, Q(hx=-4.0, hy=21.5, f=(4.5, 0.0, -0.2), b=(-15.5, 0.0, 0.0), lean=-0.38, tw=-2.0, sx=-3.0, hdx=-0.6,
             hdy=-0.2, ab=(1.6, 0.6), sk=0.6, pk=0.6, cf=-0.5, jaw=0.2), 'o'),
    (0.37, Q(hx=2.0, hy=19.5, f=(13.0, 1.6, 0.0), b=(-15.5, 0.0, 0.4), lean=0.2, tw=-0.2, sx=0.6, hdx=0.8,
             ab=(0.6, 0.6), sk=-0.4, pk=-0.5, jaw=0.7, cf=0.6), 'i'),
    (0.42, Q(hx=5.0, hy=15.0, f=(16.0, 0.0, 0.0), b=(-14.5, 0.0, 0.8), lean=0.7, tw=1.4, sx=2.6, hdx=1.3, hdy=1.6,
             ab=(-1.2, 0.4), sk=-1.0, pk=-1.0, jaw=1.0, cf=1.0), 'i2'),
    (0.52, Q(hx=5.2, hy=14.0, f=(16.0, 0.0, 0.0), b=(-14.0, 0.0, 0.85), lean=0.78, tw=1.6, sx=2.8, hdx=1.4, hdy=2.0,
             ab=(-1.4, 0.3), sk=-0.7, pk=-0.6, jaw=0.6, cf=0.5), 'o'),
    (0.62, Q(hx=4.8, hy=15.5, f=(16.0, 0.0, 0.0), b=(-13.5, 0.0, 0.6), lean=0.62, tw=1.1, sx=2.2, hdx=1.0, hdy=1.4,
             ab=(-0.9, 0.6), sk=0.0, pk=0.2), 'o'),
    (0.80, Q(hx=3.2, hy=20.0, f=(12.5, 0.0, 0.0), b=(-11.5, 1.4, 0.2), lean=0.38, tw=0.4, sx=1.0, hdy=0.4,
             ab=(-0.4, 0.8), sk=0.2, pk=0.2), 'io'),
    (1.0, END, 'io'),
])

# ---------------------------------------------------------------------- dev baş üstü (iki el): diz kalkık kurulma, çömelerek çakma
add('atk_overhead_2h', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-2.0, hy=23.0, f=(4.0, 0.0, 0.0), b=(-14.5, 0.0, 0.0), lean=-0.25, tw=-0.6, sx=-1.2, hdy=-0.4,
             ab=(2.6, 0.5), sk=0.4, pk=0.4), 'o'),
    (0.30, Q(hx=-4.5, hy=24.4, f=(2.5, 3.6, 0.3), b=(-13.0, 0.0, 0.3), lean=-0.5, tw=-1.0, sx=-2.4, hdx=-0.8,
             hdy=-1.2, ab=(3.0, 0.3), sk=0.6, pk=0.7, cf=-0.6, jaw=0.4, ear=0.3), 'o'),
    (0.37, Q(hx=3.0, hy=22.5, f=(15.0, 2.0, 0.0), b=(-15.0, 0.0, 0.4), lean=0.1, tw=0.0, sx=0.6, hdx=0.6, hdy=-0.2,
             ab=(2.2, 0.3), sk=-0.4, pk=-0.5, jaw=0.8, cf=0.7), 'i'),
    (0.42, Q(hx=5.5, hy=13.0, f=(17.0, 0.0, 0.0), b=(-12.5, 0.0, 0.6), lean=0.82, tw=1.0, sx=2.4, hdx=1.2, hdy=2.0,
             ab=(0.9, 0.3), sk=-1.0, pk=-1.0, jaw=1.0, cf=1.2), 'i2'),
    (0.52, Q(hx=5.6, hy=12.0, f=(17.0, 0.0, 0.0), b=(-12.0, 0.0, 0.7), lean=0.88, tw=1.1, sx=2.6, hdx=1.3, hdy=2.6,
             ab=(0.7, 0.4), sk=-0.4, pk=-0.2, jaw=0.6, cf=0.2), 'o'),
    (0.62, Q(hx=5.3, hy=13.5, f=(17.0, 0.0, 0.0), b=(-12.0, 0.0, 0.5), lean=0.75, tw=0.9, sx=2.2, hdx=1.0, hdy=2.0,
             ab=(0.5, 0.5), sk=0.3, pk=0.5), 'o'),
    (0.80, Q(hx=3.6, hy=19.0, f=(13.5, 0.0, 0.0), b=(-10.8, 1.6, 0.2), lean=0.45, tw=0.4, sx=1.0, hdy=0.6,
             ab=(-0.2, 0.8), sk=0.3, pk=0.3), 'io'),
    (1.0, END, 'io'),
])

# ---------------------------------------------------------------------- geri sıçrayış kesiği: öne yüklen, geriye kayarak kes
add('atk_backstep', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=1.5, hy=21.5, f=(8.0, 0.0, 0.0), b=(-12.5, 0.0, 0.4), lean=0.32, tw=-0.4, sx=0.6, hdx=0.6,
             ab=(-0.6, 0.6), sk=0.0), 'o'),
    (0.30, Q(hx=2.5, hy=19.5, f=(10.0, 0.0, 0.0), b=(-11.5, 0.0, 0.8), lean=0.45, tw=-1.2, sx=-0.8, hdx=0.8, hdy=0.8,
             ab=(-1.0, 0.5), sk=-0.3, pk=-0.2), 'o'),
    (0.37, Q(hx=-2.5, hy=21.0, f=(8.5, 2.5, -0.3), b=(-14.5, 0.0, 0.2), lean=0.05, tw=0.0, sx=0.6, hdx=0.2,
             ab=(0.6, 0.5), sk=0.8, pk=0.9, jaw=0.5, cf=-0.6), 'i'),
    (0.42, Q(hx=-5.5, hy=16.5, f=(9.0, 0.0, -0.2), b=(-17.5, 0.0, 0.0), lean=-0.1, tw=1.0, sx=2.4, hdx=0.6, hdy=0.6,
             ab=(1.0, 0.5), sk=1.0, pk=1.0, jaw=0.9, cf=-0.8), 'i2'),
    (0.52, Q(hx=-6.0, hy=15.6, f=(8.5, 0.0, -0.2), b=(-17.5, 0.0, 0.0), lean=-0.15, tw=1.3, sx=2.8, hdx=0.6, hdy=0.8,
             ab=(1.2, 0.4), sk=1.1, pk=1.1, jaw=0.5, cf=-0.6), 'o'),
    (0.62, Q(hx=-5.0, hy=17.5, f=(8.0, 0.0, 0.0), b=(-16.5, 0.0, 0.1), lean=0.0, tw=0.8, sx=2.0, ab=(0.6, 0.6),
             sk=0.5, pk=0.5, cf=-0.2), 'o'),
    (0.80, Q(hx=-2.8, hy=21.5, f=(4.5, 1.6, 0.0), b=(-15.0, 0.0, 0.2), lean=0.12, tw=0.3, sx=0.8, ab=(0.0, 0.8),
             sk=0.2, pk=0.3), 'io'),
    (1.0, Q(END, hx=-1.5, f=(4.4, 0.0, 0.0), b=(-14.6, 0.0, 0.25)), 'io'),
])

# ---------------------------------------------------------------------- alçak süpürme: kayarak yarık duruş
add('atk_sweep_low', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-1.0, hy=19.5, f=(6.5, 0.0, 0.0), b=(-14.0, 0.0, 0.3), lean=0.2, tw=-1.0, sx=-1.2, hdy=0.6,
             ab=(0.4, 0.6), sk=0.4, pk=0.4), 'o'),
    (0.30, Q(hx=-2.5, hy=15.0, f=(7.0, 0.0, 0.0), b=(-15.0, 0.0, 0.5), lean=0.3, tw=-1.8, sx=-2.4, hdx=0.2, hdy=1.4,
             ab=(1.0, 0.5), sk=0.6, pk=0.6, cf=-0.3), 'o'),
    (0.37, Q(hx=3.0, hy=12.5, f=(14.0, 0.0, 0.0), b=(-17.0, 0.0, 0.3), lean=0.45, tw=0.0, sx=0.6, hdx=0.8, hdy=1.6,
             ab=(0.0, 0.5), sk=-0.6, pk=-0.8, jaw=0.6, cf=0.8), 'i'),
    (0.42, Q(hx=5.0, hy=10.5, f=(17.0, 0.0, 0.0), b=(-17.5, 0.0, 0.2), lean=0.5, tw=1.4, sx=2.6, hdx=1.2, hdy=2.0,
             ab=(-1.3, 0.4), sk=-1.0, pk=-1.2, jaw=1.0, cf=1.0), 'i2'),
    (0.52, Q(hx=5.4, hy=10.0, f=(17.0, 0.0, 0.0), b=(-17.0, 0.0, 0.2), lean=0.55, tw=1.7, sx=3.0, hdx=1.3, hdy=2.2,
             ab=(-1.5, 0.3), sk=-1.1, pk=-1.2, jaw=0.6, cf=0.8), 'o'),
    (0.62, Q(hx=4.8, hy=12.0, f=(16.5, 0.0, 0.0), b=(-16.0, 0.0, 0.3), lean=0.45, tw=1.0, sx=2.0, hdy=1.6,
             ab=(-1.0, 0.5), sk=-0.4, pk=-0.4, cf=0.3), 'o'),
    (0.80, Q(hx=3.0, hy=18.5, f=(12.5, 0.0, 0.0), b=(-12.0, 1.6, 0.2), lean=0.3, tw=0.3, sx=0.8, hdy=0.6,
             ab=(-0.5, 0.8), sk=0.2, pk=0.2), 'io'),
    (1.0, END, 'io'),
])

# ---------------------------------------------------------------------- aparkat: derin çömelme, sıçrayarak yükselen kesik
add('atk_uppercut', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=0.5, hy=19.0, f=(7.5, 0.0, 0.0), b=(-13.0, 0.0, 0.4), lean=0.35, tw=-0.6, sx=-0.6, hdy=0.8,
             ab=(-0.6, 0.6), sk=0.4, pk=0.3), 'o'),
    (0.30, Q(hx=1.0, hy=13.5, f=(8.5, 0.0, 0.0), b=(-11.5, 0.0, 0.8), lean=0.55, tw=-1.4, sx=-1.6, hdx=0.6, hdy=1.8,
             ab=(-1.5, 0.4), sk=0.6, pk=0.5, cf=-0.3, ear=0.3), 'o'),
    (0.37, Q(hx=3.0, hy=23.0, f=(10.5, 0.0, 0.4), b=(-9.0, 0.5, 1.1), lean=0.1, tw=0.4, sx=1.0, hdx=0.4, hdy=-0.6,
             ab=(-1.0, 0.4), sk=-0.4, pk=-0.8, jaw=0.6, cf=0.8), 'i'),
    (0.42, Q(hx=4.0, hy=27.5, f=(9.5, 3.5, 0.6), b=(-7.0, 4.5, 0.9), lean=-0.15, tw=1.2, sx=2.2, hdx=0.4, hdy=-1.4,
             ab=(-1.8, 0.3), sk=-0.8, pk=-1.2, jaw=1.0, cf=1.0), 'i2'),
    (0.52, Q(hx=4.4, hy=29.0, f=(8.5, 6.5, 0.4), b=(-5.0, 7.5, 0.6), lean=-0.25, tw=1.4, sx=2.4, hdx=0.3, hdy=-1.6,
             ab=(-2.0, 0.3), sk=-1.0, pk=-1.3, jaw=0.6, cf=1.0), 'o'),
    (0.62, Q(hx=4.4, hy=26.0, f=(9.5, 3.0, 0.2), b=(-7.5, 2.5, 0.4), lean=0.0, tw=0.8, sx=1.6, hdy=-0.4,
             ab=(-1.0, 0.6), sk=0.6, pk=0.8, cf=-0.4), 'i2'),
    (0.80, Q(hx=3.5, hy=18.0, f=(10.5, 0.0, 0.0), b=(-10.5, 0.0, 0.4), lean=0.35, tw=0.3, sx=0.8, hdy=0.8,
             ab=(-0.5, 0.7), sk=0.6, pk=0.6), 'i2'),
    (1.0, END, 'io'),
])

# ---------------------------------------------------------------------- ağır kaldırma (iki elli aparkat, sürükleme): bacaktan yüklen
add('atk_a_lift', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-1.0, hy=19.0, f=(6.5, 0.0, 0.0), b=(-14.5, 0.0, 0.3), lean=0.3, tw=-1.0, sx=-1.4, hdy=0.8,
             ab=(-0.6, 0.8), sk=0.4, pk=0.4), 'o'),
    (0.30, Q(hx=-2.5, hy=14.5, f=(8.0, 0.0, 0.0), b=(-15.0, 0.0, 0.5), lean=0.55, tw=-1.8, sx=-2.4, hdx=0.4,
             hdy=1.8, ab=(-1.2, 0.6), sk=0.6, pk=0.5, cf=-0.3, jaw=0.3), 'o'),
    (0.37, Q(hx=2.0, hy=18.0, f=(12.0, 0.0, 0.0), b=(-14.0, 0.0, 0.8), lean=0.35, tw=0.0, sx=0.6, hdx=0.8, hdy=0.6,
             ab=(-0.6, 0.5), sk=-0.4, pk=-0.6, jaw=0.7, cf=0.6), 'i'),
    (0.42, Q(hx=4.5, hy=24.0, f=(13.0, 0.0, 0.2), b=(-10.0, 0.0, 1.0), lean=-0.15, tw=1.2, sx=2.2, hdx=0.4,
             hdy=-1.4, ab=(-1.4, 0.4), sk=-0.6, pk=-1.0, jaw=1.0, cf=1.0), 'i2'),
    (0.52, Q(hx=4.8, hy=24.8, f=(13.0, 0.0, 0.3), b=(-9.0, 0.8, 1.0), lean=-0.25, tw=1.4, sx=2.4, hdx=0.2,
             hdy=-1.6, ab=(-1.6, 0.3), sk=-0.8, pk=-1.2, jaw=0.6, cf=0.9), 'o'),
    (0.62, Q(hx=4.4, hy=21.0, f=(13.0, 0.0, 0.0), b=(-10.5, 0.0, 0.4), lean=0.05, tw=0.8, sx=1.6, hdy=-0.4,
             ab=(-0.9, 0.6), sk=0.3, pk=0.4, cf=0.2), 'o'),
    (0.80, Q(hx=3.0, hy=21.0, f=(11.0, 0.0, 0.0), b=(-11.5, 0.0, 0.3), lean=0.25, tw=0.3, sx=0.8, ab=(-0.5, 0.8),
             sk=0.2, pk=0.3), 'io'),
    (1.0, END, 'io'),
])

# ---------------------------------------------------------------------- mızrak uzun hamlesi (lunge_long, stab_heavy, alçak saplama)
add('atk_lunge_long', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-2.0, hy=21.5, f=(5.0, 0.0, 0.0), b=(-14.5, 0.0, 0.1), lean=0.0, tw=-0.8, sx=-1.4, ab=(0.4, 1.2),
             sk=0.3, pk=0.4), 'o'),
    (0.30, Q(hx=-4.5, hy=19.0, f=(5.0, 0.0, -0.2), b=(-16.0, 0.0, 0.2), lean=-0.15, tw=-1.4, sx=-2.6, hdx=0.2,
             hdy=0.4, ab=(0.4, 1.4), sk=0.6, pk=0.6, cf=-0.4), 'o'),
    (0.37, Q(hx=3.0, hy=17.0, f=(15.0, 2.6, 0.0), b=(-16.0, 0.0, 0.4), lean=0.4, tw=0.2, sx=1.0, hdx=1.0, hdy=0.6,
             ab=(1.0, 0.8), sk=-0.7, pk=-0.9, jaw=0.6, cf=0.8), 'i'),
    (0.42, Q(hx=8.5, hy=13.0, f=(23.0, 0.0, 0.0), b=(-14.5, 0.0, 0.7), lean=0.66, tw=1.2, sx=2.8, hdx=1.6, hdy=1.4,
             ab=(1.4, 0.4), sk=-1.2, pk=-1.3, jaw=1.0, cf=1.2), 'i2'),
    (0.52, Q(hx=9.0, hy=12.4, f=(23.0, 0.0, 0.0), b=(-14.0, 0.0, 0.75), lean=0.72, tw=1.4, sx=3.0, hdx=1.8, hdy=1.6,
             ab=(1.5, 0.3), sk=-1.2, pk=-1.3, jaw=0.6, cf=1.0), 'o'),
    (0.62, Q(hx=8.2, hy=14.0, f=(22.5, 0.0, 0.0), b=(-13.0, 0.0, 0.5), lean=0.6, tw=1.0, sx=2.2, hdx=1.2, hdy=1.0,
             ab=(1.0, 0.6), sk=-0.5, pk=-0.5, cf=0.4), 'o'),
    (0.80, Q(hx=5.0, hy=19.5, f=(15.5, 0.0, 0.0), b=(-9.0, 1.8, 0.3), lean=0.35, tw=0.3, sx=1.0, ab=(0.2, 1.0),
             sk=0.2, pk=0.2), 'io'),
    (1.0, Q(END, hx=2.5, f=(9.4, 0.0, 0.0), b=(-10.6, 0.0, 0.25)), 'io'),
])

# ---------------------------------------------------------------------- mızrak saplaması: yerleşik duruş, kayan adım (shuffle)
add('atk_m_thrust', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-1.5, hy=21.0, f=(6.0, 0.0, 0.0), b=(-14.5, 0.0, 0.1), lean=0.05, tw=-0.8, sx=-1.4, hdx=0.3,
             ab=(0.5, 1.2), sk=0.3, pk=0.3), 'o'),
    (0.30, Q(hx=-3.8, hy=18.8, f=(6.5, 0.0, 0.0), b=(-15.5, 0.0, 0.1), lean=-0.05, tw=-1.4, sx=-2.6, hdx=0.5,
             hdy=0.5, ab=(0.4, 1.4), sk=0.5, pk=0.5, cf=-0.3), 'o'),
    (0.37, Q(hx=1.0, hy=18.0, f=(13.0, 0.8, 0.0), b=(-15.5, 0.0, 0.3), lean=0.2, tw=0.0, sx=0.6, hdx=1.0, hdy=0.4,
             ab=(0.9, 0.9), sk=-0.5, pk=-0.6, jaw=0.4, cf=0.6), 'i'),
    (0.42, Q(hx=5.0, hy=16.5, f=(17.0, 0.0, 0.0), b=(-15.0, 0.0, 0.5), lean=0.32, tw=1.0, sx=2.6, hdx=1.4, hdy=0.6,
             ab=(1.3, 0.5), sk=-0.9, pk=-1.0, jaw=0.9, cf=1.0), 'i2'),
    (0.52, Q(hx=5.6, hy=16.8, f=(17.0, 0.0, 0.0), b=(-11.0, 1.8, 0.3), lean=0.36, tw=1.2, sx=2.8, hdx=1.5, hdy=0.6,
             ab=(1.4, 0.45), sk=-0.6, pk=-0.8, jaw=0.5, cf=0.6), 'o'),
    (0.62, Q(hx=5.5, hy=17.5, f=(17.0, 0.0, 0.0), b=(-9.5, 0.0, 0.3), lean=0.3, tw=0.9, sx=2.2, hdx=1.2,
             ab=(1.1, 0.6), sk=-0.2, pk=-0.2, cf=0.2), 'o'),
    (0.80, Q(hx=4.0, hy=21.0, f=(14.0, 0.0, 0.0), b=(-8.5, 0.0, 0.25), lean=0.22, tw=0.3, sx=1.0, ab=(0.6, 0.9),
             sk=0.2, pk=0.2), 'io'),
    (1.0, Q(END, hx=3.0, f=(11.0, 0.0, 0.0), b=(-9.5, 0.0, 0.25)), 'io'),
])

# ---------------------------------------------------------------------- mızrak yükselişi: alçaktan çevirip baş üstüne
add('atk_m_rise', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-0.5, hy=19.5, f=(7.0, 0.0, 0.0), b=(-14.5, 0.0, 0.3), lean=0.25, tw=-0.8, sx=-1.0, hdy=0.6,
             ab=(0.4, 1.2), sk=0.4, pk=0.4), 'o'),
    (0.30, Q(hx=-1.5, hy=15.0, f=(9.5, 0.0, 0.0), b=(-15.0, 0.0, 0.6), lean=0.45, tw=-1.6, sx=-2.0, hdx=0.4,
             hdy=1.4, ab=(0.2, 1.3), sk=0.6, pk=0.5, cf=-0.3), 'o'),
    (0.37, Q(hx=2.5, hy=20.0, f=(12.5, 0.0, 0.0), b=(-13.5, 0.0, 0.8), lean=0.15, tw=0.2, sx=0.8, hdx=0.6, hdy=-0.2,
             ab=(0.8, 1.0), sk=-0.3, pk=-0.6, jaw=0.6, cf=0.6), 'i'),
    (0.42, Q(hx=4.0, hy=24.5, f=(13.5, 0.0, 0.1), b=(-11.0, 0.6, 1.0), lean=-0.12, tw=1.2, sx=2.2, hdx=0.5,
             hdy=-1.3, ab=(1.6, 0.5), sk=-0.6, pk=-1.1, jaw=1.0, cf=1.0), 'i2'),
    (0.52, Q(hx=4.4, hy=25.4, f=(13.5, 0.0, 0.25), b=(-10.0, 1.4, 1.0), lean=-0.22, tw=1.4, sx=2.4, hdx=0.4,
             hdy=-1.6, ab=(1.9, 0.4), sk=-0.9, pk=-1.3, jaw=0.6, cf=0.9), 'o'),
    (0.62, Q(hx=4.0, hy=21.5, f=(13.5, 0.0, 0.0), b=(-11.0, 0.0, 0.4), lean=0.05, tw=0.8, sx=1.6, hdy=-0.3,
             ab=(1.2, 0.7), sk=0.3, pk=0.5, cf=0.1), 'o'),
    (0.80, Q(hx=2.8, hy=21.5, f=(11.0, 0.0, 0.0), b=(-11.5, 0.0, 0.3), lean=0.2, tw=0.3, sx=0.8, ab=(0.5, 1.0),
             sk=0.2, pk=0.3), 'io'),
    (1.0, END, 'io'),
])

# ---------------------------------------------------------------------- çevrinti / bilek çevrimi: ön ayak üstünde tam tur
_TURN_SET = ((0.0, 0.06), (0.14, 0.2), (0.3, 0.3), (0.42, 0.43), (0.46, 0.47), (0.5, 0.51), (0.54, 0.55),
             (0.62, 0.64), (0.76, 0.8), (0.9, 0.95))


def _spin(low=0.0, up=0.0, wide=0.0, ab_up=0.0):
    return [
        (0.0, Q(), 'io'),
        (0.15, Q(hx=-1.0, hy=21.0 - low * 0.5, f=(6.0 + wide * 0.5, 0.0, 0.0), b=(-13.5 - wide * 0.5, 0.0, 0.2),
                 lean=0.1, tw=-1.0, sx=-1.4, ab=(0.6 + ab_up, 0.6), sk=0.4, pk=0.4, turn=-0.05), 'o'),
        (0.30, Q(hx=-1.5, hy=18.5 - low, f=(6.5 + wide, 0.0, 0.0), b=(-13.0 - wide, 0.0, 0.4), lean=0.15, tw=-1.8,
                 sx=-2.4, hdx=-0.4, hdy=0.6, ab=(1.1 + ab_up, 0.4), sk=0.6, pk=0.7, cf=-0.4, turn=-0.12), 'o'),
        (0.42, Q(hx=2.0, hy=21.0 - low + up, f=(7.0 + wide, 0.0, 0.5), b=(-6.0 - wide, 3.0, 0.3), lean=0.1, tw=0.6,
                 sx=1.0, hdx=0.6, ab=(-1.4 + ab_up * 2.5, 0.3), sk=-0.6, pk=-0.9, jaw=0.6, cf=0.8, turn=0.3), 'i2'),
        (0.47, Q(hx=2.4, hy=22.0 - low + up, f=(7.0 + wide, 0.0, 0.7), b=(-2.0, 4.0, 0.2), lean=0.0, tw=1.0, sx=1.4,
                 hdx=0.4, ab=(-1.8 + ab_up * 2.8, 0.2), sk=-1.0, pk=-1.2, jaw=0.9, cf=1.0, turn=0.8), 'l'),
        (0.52, Q(hx=2.4, hy=22.0 - low + up, f=(7.0 + wide, 0.0, 0.7), b=(-4.0 - wide * 0.5, 3.5, 0.2), lean=0.05,
                 tw=1.0, sx=1.4, ab=(-1.8 + ab_up * 2.8, 0.2), sk=0.8, pk=1.0, jaw=0.7, cf=-0.6, turn=1.25), 'l'),
        (0.58, Q(hx=2.4, hy=20.5 - low + up * 0.5, f=(7.5 + wide, 0.0, 0.3), b=(-10.0 - wide, 1.5, 0.3), lean=0.2,
                 tw=0.8, sx=1.6, hdx=0.6, ab=(-1.4 + ab_up * 2.5, 0.3), sk=-0.8, pk=-1.0, jaw=0.4, cf=0.8, turn=1.75), 'l'),
        (0.66, Q(hx=2.4, hy=19.0 - low, f=(8.5 + wide, 0.0, 0.0), b=(-12.0 - wide, 0.0, 0.4), lean=0.3, tw=0.6,
                 sx=1.4, hdx=0.6, hdy=0.6, ab=(-1.0, 0.5), sk=-0.5, pk=-0.4, cf=0.3, turn=2.0), 'o'),
        (0.82, Q(hx=1.8, hy=21.5, f=(8.4, 0.0, 0.0), b=(-12.0, 0.0, 0.3), lean=0.2, tw=0.2, sx=0.8, ab=(-0.5, 0.8),
                 sk=0.1, pk=0.2, turn=2.0), 'io'),
        (1.0, Q(END, turn=2.0), 'io'),
    ]


add('atk_spin', _spin(), frames=_TURN_SET)
add('atk_spin_2h', _spin(low=3.0, wide=4.0, ab_up=0.3), frames=_TURN_SET)       # tam gövde çark: alçak, geniş
add('atk_w_whirl', _spin(up=3.0, ab_up=1.0), frames=_TURN_SET)                  # kırbaç baş üstü girdabı: dik, parmak ucunda

# ---------------------------------------------------------------------- hançer: alçak akrobatik çömelme kesiği
_DUAL = [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=0.5, hy=19.0, f=(7.5, 0.0, 0.0), b=(-12.5, 0.0, 0.5), lean=0.4, tw=-0.6, sx=-0.4, hdx=0.6, hdy=0.8,
             ab=(-0.8, 1.2), sk=0.3, pk=0.3), 'o'),
    (0.30, Q(hx=0.0, hy=15.5, f=(8.5, 0.0, 0.0), b=(-11.5, 0.0, 0.9), lean=0.55, tw=-1.4, sx=-1.4, hdx=0.9, hdy=1.6,
             ab=(-1.4, 1.4), sk=0.5, pk=0.5, cf=-0.2, ear=0.3), 'o'),
    (0.37, Q(hx=4.5, hy=18.0, f=(14.0, 2.5, 0.0), b=(-9.0, 1.0, 0.9), lean=0.5, tw=0.2, sx=0.8, hdx=1.2, hdy=1.0,
             ab=(-1.6, 0.8), sk=-0.8, pk=-1.0, jaw=0.5, cf=0.9), 'i'),
    (0.42, Q(hx=6.0, hy=14.0, f=(16.5, 0.0, 0.0), b=(-10.5, 0.0, 1.0), lean=0.62, tw=1.3, sx=2.6, hdx=1.5, hdy=1.6,
             ab=(-1.9, 0.6), sk=-1.0, pk=-1.2, jaw=0.9, cf=1.0), 'i2'),
    (0.52, Q(hx=6.4, hy=13.4, f=(16.5, 0.0, 0.0), b=(-10.0, 0.0, 1.05), lean=0.68, tw=1.5, sx=2.8, hdx=1.6, hdy=1.8,
             ab=(-2.0, 0.5), sk=-1.1, pk=-1.2, jaw=0.5, cf=0.8), 'o'),
    (0.62, Q(hx=5.6, hy=15.5, f=(16.0, 0.0, 0.0), b=(-9.5, 0.0, 0.7), lean=0.5, tw=0.9, sx=2.0, hdx=1.0, hdy=1.2,
             ab=(-1.2, 0.9), sk=-0.4, pk=-0.4, cf=0.3), 'o'),
    (0.80, Q(hx=3.6, hy=19.5, f=(12.5, 0.0, 0.0), b=(-9.0, 1.4, 0.4), lean=0.35, tw=0.3, sx=0.8, hdy=0.6,
             ab=(-0.6, 1.0), sk=0.2, pk=0.2), 'io'),
    (1.0, Q(END, hx=2.0, f=(9.0, 0.0, 0.0), b=(-11.0, 0.0, 0.3)), 'io'),
]
add('atk_dual', _DUAL)

# ters el (dual_r): çapraz adım — arka ayak öne geçer, arka el ikinci bıçakla öne fırlar
add('atk_dual_r', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=1.0, hy=19.5, f=(8.0, 0.0, 0.0), b=(-12.0, 0.0, 0.5), lean=0.35, tw=0.4, sx=1.0, hdx=0.6, hdy=0.6,
             ab=(-1.2, 1.4), sk=0.2, pk=0.3), 'o'),
    (0.30, Q(hx=1.5, hy=16.5, f=(9.0, 0.0, 0.0), b=(-11.0, 0.0, 0.9), lean=0.45, tw=1.2, sx=1.6, hdx=0.8, hdy=1.2,
             ab=(-2.0, 1.8), sk=0.0, pk=0.2, ear=0.3), 'o'),
    (0.37, Q(hx=5.0, hy=18.0, f=(11.0, 0.0, 0.6), b=(4.0, 3.0, 0.2), lean=0.4, tw=-0.4, sx=-0.6, hdx=1.2, hdy=0.8,
             ab=(0.4, 0.6), sk=-0.7, pk=-0.9, jaw=0.5, cf=0.8), 'i'),
    (0.42, Q(hx=6.5, hy=16.5, f=(9.0, 0.0, 0.9), b=(12.0, 0.0, 0.0), lean=0.5, tw=-1.4, sx=-1.2, hdx=1.4, hdy=1.2,
             ab=(1.55, 0.1), sk=-1.0, pk=-1.2, jaw=0.9, cf=1.0), 'i2'),
    (0.52, Q(hx=6.9, hy=16.0, f=(9.0, 0.0, 0.95), b=(12.0, 0.0, 0.0), lean=0.55, tw=-1.6, sx=-1.4, hdx=1.5, hdy=1.4,
             ab=(1.65, 0.05), sk=-1.1, pk=-1.2, jaw=0.5, cf=0.8), 'o'),
    (0.62, Q(hx=6.4, hy=17.5, f=(9.5, 0.0, 0.6), b=(11.5, 0.0, 0.0), lean=0.45, tw=-1.0, sx=-0.6, hdx=1.0, hdy=1.0,
             ab=(1.2, 0.4), sk=-0.4, pk=-0.4, cf=0.3), 'o'),
    (0.80, Q(hx=5.0, hy=19.5, f=(13.5, 0.0, 0.2), b=(0.0, 3.0, 0.2), lean=0.3, tw=-0.3, sx=0.2, ab=(0.2, 0.9),
             sk=0.1, pk=0.1), 'io'),
    (1.0, Q(END, hx=3.5, f=(10.5, 0.0, 0.0), b=(-9.5, 0.0, 0.25)), 'io'),
])

# ters tutuşlu pivot (hançer reverse_grip / twirl): hazırlıkta sırtını döner, süpürmede tur tamamlanır
add('atk_h_spin', [
    (0.0, Q(), 'io'),
    (0.12, Q(hx=0.5, hy=19.0, f=(7.0, 0.0, 0.0), b=(-12.0, 0.0, 0.5), lean=0.35, tw=0.4, sx=0.6, hdx=0.5, hdy=0.8,
             ab=(-0.8, 1.2), sk=0.2, pk=0.3, turn=0.15), 'o'),
    (0.30, Q(hx=1.5, hy=15.5, f=(6.5, 0.0, 0.6), b=(-9.0, 0.0, 0.6), lean=0.45, tw=1.0, sx=1.2, hdx=0.8, hdy=1.4,
             ab=(-1.6, 1.0), sk=0.8, pk=1.0, cf=-0.6, turn=1.0), 'o'),
    (0.37, Q(hx=4.0, hy=16.0, f=(11.0, 1.5, 0.3), b=(-10.0, 0.0, 0.8), lean=0.5, tw=0.4, sx=1.0, hdx=1.0, hdy=1.2,
             ab=(-1.8, 0.8), sk=-0.6, pk=-0.8, jaw=0.5, cf=0.8, turn=1.75), 'i2'),
] + [(t_, Q(q_, turn=2.0), e_) for t_, q_, e_ in _DUAL[4:]])

# seri saplama (hançer flurry): sekerek gidip gelen alçak duruş, her saplamada öne
_FL_FR = ((0.0, 0.05), (0.15, 0.27), (0.42, 0.438), (0.455, 0.462), (0.48, 0.487), (0.505, 0.512), (0.53, 0.536),
          (0.6, 0.64), (0.75, 0.78), (0.9, 0.95))
_FE = dict(hy=15.0, b=(-10.5, 0.0, 1.0), lean=0.6, tw=1.2, sx=2.6, hdx=1.5, hdy=1.4, ab=(-1.8, 0.6), sk=-1.0,
           pk=-1.1, jaw=0.9, cf=0.9)
_FR = dict(hy=16.5, b=(-11.0, 0.0, 0.7), lean=0.45, tw=-0.4, sx=0.0, hdx=1.0, hdy=1.2, ab=(-1.4, 1.0), sk=-0.3,
           pk=-0.6, jaw=0.3, cf=0.4)
add('atk_h_flurry', [
    (0.0, Q(), 'io'),
    (0.27, Q(hx=0.0, hy=15.5, f=(8.5, 0.0, 0.0), b=(-11.5, 0.0, 0.9), lean=0.55, tw=-1.4, sx=-1.4, hdx=0.9,
             hdy=1.6, ab=(-1.4, 1.4), sk=0.5, pk=0.5, cf=-0.2, ear=0.3), 'o'),
    (0.438, Q(hx=5.0, f=(14.5, 0.0, 0.0), **_FE), 'i2'),
    (0.462, Q(hx=3.4, f=(14.5, 0.0, 0.0), **_FR), 'o2'),
    (0.487, Q(hx=6.0, f=(15.5, 0.0, 0.0), **_FE), 'i2'),
    (0.512, Q(hx=4.4, f=(15.5, 0.0, 0.0), **_FR), 'o2'),
    (0.536, Q(Q(**_FE), hx=7.4, f=(17.0, 0.0, 0.0), hy=13.6, lean=0.7, ab=(-2.0, 0.4), cf=1.1), 'i2'),
    (0.64, Q(hx=6.0, hy=15.5, f=(16.5, 0.0, 0.0), b=(-9.5, 0.0, 0.7), lean=0.5, tw=0.9, sx=2.0, hdx=1.0, hdy=1.2,
             ab=(-1.2, 0.9), sk=-0.4, pk=-0.4, cf=0.3), 'o'),
    (0.80, Q(hx=3.6, hy=19.5, f=(12.5, 0.0, 0.0), b=(-9.0, 1.4, 0.4), lean=0.35, tw=0.3, sx=0.8, hdy=0.6,
             ab=(-0.6, 1.0), sk=0.2, pk=0.2), 'io'),
    (1.0, Q(END, hx=2.0, f=(9.0, 0.0, 0.0), b=(-11.0, 0.0, 0.3)), 'io'),
], frames=_FL_FR)

# ---------------------------------------------------------------------- uzun sap süpürmesi: arkadan çapraz adım, at duruşu
add('atk_u_sweep', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-1.5, hy=20.5, f=(6.0, 0.0, 0.0), b=(-15.0, 0.0, 0.1), lean=0.05, tw=-1.2, sx=-1.8, hdx=-0.2,
             ab=(0.6, 1.2), sk=0.4, pk=0.4), 'o'),
    (0.30, Q(hx=-3.0, hy=18.0, f=(5.0, 0.0, 0.3), b=(-17.0, 0.0, 0.0), lean=-0.2, tw=-2.0, sx=-3.0, hdx=-0.4,
             hdy=0.4, ab=(0.8, 1.3), sk=0.7, pk=0.7, cf=-0.5), 'o'),
    (0.37, Q(hx=2.0, hy=17.0, f=(13.0, 2.0, 0.0), b=(-16.5, 0.0, 0.3), lean=0.1, tw=-0.4, sx=0.0, hdx=0.6,
             ab=(0.9, 0.9), sk=-0.5, pk=-0.6, jaw=0.5, cf=0.7, turn=0.15), 'i'),
    (0.42, Q(hx=3.5, hy=14.5, f=(18.5, 0.0, 0.0), b=(-15.5, 0.0, 0.4), lean=0.22, tw=1.4, sx=2.6, hdx=1.0, hdy=0.8,
             ab=(1.3, 0.5), sk=-1.0, pk=-1.1, jaw=0.9, cf=1.0), 'i2'),
    (0.52, Q(hx=4.0, hy=14.0, f=(18.5, 0.0, 0.0), b=(-14.5, 0.0, 0.7), lean=0.3, tw=1.8, sx=3.0, hdx=1.2, hdy=1.0,
             ab=(1.4, 0.4), sk=-1.2, pk=-1.2, jaw=0.5, cf=0.8), 'o'),
    (0.62, Q(hx=3.8, hy=15.8, f=(18.0, 0.0, 0.0), b=(-14.0, 0.0, 0.4), lean=0.22, tw=1.0, sx=2.0, hdx=0.8,
             ab=(1.0, 0.7), sk=-0.4, pk=-0.4, cf=0.3), 'o'),
    (0.80, Q(hx=2.6, hy=20.5, f=(12.0, 0.0, 0.0), b=(-12.5, 1.4, 0.2), lean=0.2, tw=0.3, sx=0.8, ab=(0.4, 1.0),
             sk=0.2, pk=0.2), 'io'),
    (1.0, END, 'io'),
])

# ---------------------------------------------------------------------- biçme (tırpan reap): öne uzan, ağırlığı geri çekerek biç
add('atk_u_reap', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=1.5, hy=20.5, f=(9.5, 0.0, 0.0), b=(-13.0, 0.0, 0.5), lean=0.3, tw=0.4, sx=1.0, hdx=0.6, hdy=0.4,
             ab=(1.0, 0.8), sk=-0.2, pk=-0.2), 'o'),
    (0.30, Q(hx=4.0, hy=17.5, f=(14.0, 0.0, 0.0), b=(-13.0, 0.0, 0.8), lean=0.55, tw=1.2, sx=2.4, hdx=1.2, hdy=1.0,
             ab=(1.4, 0.4), sk=-0.6, pk=-0.6, cf=0.5, ear=0.2), 'o'),
    (0.37, Q(hx=0.0, hy=17.5, f=(13.5, 0.0, -0.2), b=(-14.5, 0.0, 0.2), lean=0.1, tw=0.2, sx=0.6, hdx=0.4,
             ab=(0.6, 0.8), sk=0.5, pk=0.6, jaw=0.6, cf=-0.6), 'i'),
    (0.42, Q(hx=-4.0, hy=16.0, f=(12.5, 0.0, -0.3), b=(-16.0, 0.0, 0.0), lean=-0.22, tw=-1.2, sx=-2.0, hdx=0.0,
             hdy=0.4, ab=(-0.4, 0.8), sk=1.0, pk=1.1, jaw=1.0, cf=-1.0), 'i2'),
    (0.52, Q(hx=-4.6, hy=15.4, f=(12.0, 0.0, -0.3), b=(-16.0, 0.0, 0.0), lean=-0.28, tw=-1.5, sx=-2.4, hdy=0.6,
             ab=(-0.6, 0.8), sk=1.1, pk=1.1, jaw=0.5, cf=-0.8), 'o'),
    (0.62, Q(hx=-3.5, hy=17.5, f=(11.0, 0.0, 0.0), b=(-15.0, 0.0, 0.1), lean=-0.1, tw=-0.8, sx=-1.0, ab=(-0.4, 0.9),
             sk=0.6, pk=0.6, cf=-0.3), 'o'),
    (0.80, Q(hx=-1.0, hy=21.5, f=(7.0, 1.4, 0.0), b=(-14.0, 0.0, 0.2), lean=0.1, tw=-0.2, sx=0.2, ab=(-0.3, 0.9),
             sk=0.3, pk=0.3), 'io'),
    (1.0, Q(END, hx=0.0, f=(6.4, 0.0, 0.0), b=(-13.6, 0.0, 0.25)), 'io'),
])

# ---------------------------------------------------------------------- kırbaç şaklaması: sırt kavisli kurulma, kalça şaklar
add('atk_whip', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-1.5, hy=22.0, f=(6.0, 0.0, 0.0), b=(-14.0, 0.0, 0.1), lean=-0.2, tw=-1.0, sx=-1.6, hdx=-0.4,
             hdy=-0.2, ab=(0.8, 0.6), sk=0.4, pk=0.5), 'o'),
    (0.30, Q(hx=-3.5, hy=21.0, f=(6.5, 0.0, -0.2), b=(-15.0, 0.0, 0.0), lean=-0.45, tw=-1.6, sx=-2.6, hdx=-0.8,
             hdy=-0.6, ab=(1.4, 0.4), sk=0.6, pk=0.7, cf=-0.6, ear=0.2), 'o'),
    (0.37, Q(hx=1.5, hy=19.5, f=(12.0, 1.5, 0.0), b=(-15.0, 0.0, 0.4), lean=0.15, tw=0.0, sx=0.8, hdx=0.8,
             ab=(0.0, 0.6), sk=-0.4, pk=-0.6, jaw=0.6, cf=0.6), 'i'),
    (0.42, Q(hx=4.5, hy=17.0, f=(15.0, 0.0, 0.0), b=(-14.0, 0.0, 0.7), lean=0.55, tw=1.6, sx=3.0, hdx=1.4, hdy=1.0,
             ab=(-1.4, 0.4), sk=-1.0, pk=-1.2, jaw=1.0, cf=1.0), 'i2'),
    (0.52, Q(hx=5.0, hy=16.5, f=(15.0, 0.0, 0.0), b=(-13.5, 0.0, 0.75), lean=0.6, tw=1.8, sx=3.2, hdx=1.5, hdy=1.2,
             ab=(-1.6, 0.3), sk=-1.1, pk=-1.2, jaw=0.6, cf=0.8), 'o'),
    (0.62, Q(hx=4.4, hy=18.0, f=(15.0, 0.0, 0.0), b=(-13.0, 0.0, 0.4), lean=0.42, tw=1.0, sx=2.0, hdx=1.0, hdy=0.6,
             ab=(-1.0, 0.6), sk=-0.4, pk=-0.4, cf=0.3), 'o'),
    (0.80, Q(hx=2.8, hy=21.5, f=(11.5, 0.0, 0.0), b=(-11.5, 1.4, 0.2), lean=0.25, tw=0.3, sx=0.8, ab=(-0.5, 0.8),
             sk=0.2, pk=0.2), 'io'),
    (1.0, END, 'io'),
])

# kırbaç yan şaklaması: bükülüp açılan kalça, ön ayak üstünde yarım dönüş, arka ayak savrulur
add('atk_w_side', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-1.0, hy=21.0, f=(6.0, 0.0, 0.0), b=(-14.0, 0.0, 0.1), lean=0.05, tw=-1.2, sx=-1.8, ab=(0.9, 0.5),
             sk=0.4, pk=0.4), 'o'),
    (0.30, Q(hx=-2.5, hy=19.0, f=(6.5, 0.0, 0.0), b=(-15.0, 0.0, 0.1), lean=-0.1, tw=-2.0, sx=-3.0, hdx=-0.2,
             hdy=0.4, ab=(1.3, 0.4), sk=0.7, pk=0.7, cf=-0.5, turn=-0.12), 'o'),
    (0.37, Q(hx=2.0, hy=18.5, f=(11.0, 0.0, 0.2), b=(-14.0, 0.0, 0.6), lean=0.25, tw=0.2, sx=0.8, hdx=0.8,
             ab=(0.2, 0.5), sk=-0.5, pk=-0.7, jaw=0.6, cf=0.7), 'i'),
    (0.42, Q(hx=4.0, hy=17.5, f=(12.5, 0.0, 0.3), b=(-10.0, 2.0, 0.6), lean=0.4, tw=1.8, sx=3.0, hdx=1.2, hdy=0.6,
             ab=(-1.6, 0.3), sk=-1.1, pk=-1.3, jaw=1.0, cf=1.0, turn=0.1), 'i2'),
    (0.52, Q(hx=4.4, hy=17.5, f=(12.5, 0.0, 0.3), b=(-8.0, 2.5, 0.5), lean=0.45, tw=2.0, sx=3.2, hdx=1.2, hdy=0.8,
             ab=(-1.8, 0.25), sk=-1.2, pk=-1.3, jaw=0.5, cf=0.8, turn=0.12), 'o'),
    (0.62, Q(hx=4.2, hy=18.5, f=(12.5, 0.0, 0.0), b=(-9.5, 0.0, 0.4), lean=0.35, tw=1.0, sx=2.0, hdx=0.8,
             ab=(-1.0, 0.6), sk=-0.4, pk=-0.4, cf=0.3), 'o'),
    (0.80, Q(hx=2.8, hy=21.5, f=(10.5, 0.0, 0.0), b=(-11.5, 0.0, 0.25), lean=0.22, tw=0.3, sx=0.8, ab=(-0.5, 0.8),
             sk=0.2, pk=0.2), 'io'),
    (1.0, END, 'io'),
])

# ---------------------------------------------------------------------- sıçrayıp çakma: çömel (tutuş), sıçra, havada kurul, çak
add('atk_slam_jump', [
    (0.0, Q(), 'io'),
    (0.14, Q(hx=-0.5, hy=15.0, f=(7.0, 0.0, 0.0), b=(-12.5, 0.0, 0.6), lean=0.45, tw=-0.6, sx=-1.0, hdy=1.6,
             ab=(1.6, 0.8), sk=0.6, pk=0.5, cf=-0.3, ear=0.3), 'o'),
    (0.22, Q(hx=1.5, hy=30.0, f=(8.0, 5.0, 0.6), b=(-8.0, 3.0, 0.9), lean=-0.1, tw=-0.4, sx=-0.6, hdy=-1.0,
             ab=(2.8, 0.4), sk=0.4, pk=0.6, cf=-0.6), 'o2'),
    (0.30, Q(hx=3.0, hy=33.0, f=(9.0, 9.0, 0.5), b=(-4.0, 8.0, 0.6), lean=-0.3, tw=-0.8, sx=-1.4, hdx=-0.4,
             hdy=-1.4, ab=(3.0, 0.3), sk=0.7, pk=0.9, cf=-0.8, jaw=0.4), 'o'),
    (0.37, Q(hx=5.0, hy=24.0, f=(14.0, 2.5, 0.0), b=(-9.0, 2.0, 0.6), lean=0.4, tw=0.4, sx=1.2, hdx=0.8, hdy=0.4,
             ab=(1.5, 0.4), sk=-0.8, pk=-1.0, jaw=0.9, cf=1.0), 'i'),
    (0.42, Q(hx=5.5, hy=12.5, f=(15.0, 0.0, 0.0), b=(-11.5, 0.0, 0.7), lean=0.82, tw=1.2, sx=2.4, hdx=1.2, hdy=2.4,
             ab=(0.6, 0.4), sk=-0.6, pk=-0.5, jaw=1.0, cf=0.8), 'i2'),
    (0.52, Q(hx=5.6, hy=11.5, f=(15.0, 0.0, 0.0), b=(-11.0, 0.0, 0.8), lean=0.88, tw=1.3, sx=2.6, hdx=1.3, hdy=2.8,
             ab=(0.4, 0.5), sk=0.4, pk=0.6, jaw=0.6, cf=-0.2), 'o'),
    (0.62, Q(hx=5.3, hy=13.0, f=(15.0, 0.0, 0.0), b=(-11.0, 0.0, 0.5), lean=0.75, tw=1.0, sx=2.2, hdy=2.0,
             ab=(0.3, 0.6), sk=0.5, pk=0.6), 'o'),
    (0.80, Q(hx=3.5, hy=19.5, f=(12.5, 0.0, 0.0), b=(-10.8, 1.6, 0.2), lean=0.45, tw=0.4, sx=1.0, hdy=0.6,
             ab=(-0.2, 0.8), sk=0.3, pk=0.3), 'io'),
    (1.0, END, 'io'),
], frames=((0.0, 0.06), (0.08, 0.14), (0.18, 0.22), (0.26, 0.30), (0.34, 0.37), (0.42, 0.42), (0.49, 0.52),
           (0.58, 0.62), (0.72, 0.78), (0.88, 0.95)))

# ---------------------------------------------------------------------- balta fırlatma: geriye burulup tam gövdeyle bırak
add('atk_throw_axe', [
    (0.0, Q(), 'io'),
    (0.15, Q(hx=-2.0, hy=21.5, f=(5.0, 0.0, 0.0), b=(-14.5, 0.0, 0.1), lean=-0.25, tw=-1.4, sx=-2.0, hdx=-0.4,
             ab=(1.2, 0.6), sk=0.4, pk=0.5), 'o'),
    (0.30, Q(hx=-4.5, hy=20.0, f=(6.0, 1.5, -0.2), b=(-15.0, 0.0, 0.0), lean=-0.45, tw=-2.2, sx=-3.2, hdx=-0.8,
             hdy=-0.4, ab=(1.5, 0.3), sk=0.6, pk=0.7, cf=-0.6), 'o'),
    (0.37, Q(hx=2.0, hy=19.0, f=(13.0, 0.6, 0.0), b=(-15.0, 0.0, 0.5), lean=0.3, tw=0.6, sx=1.6, hdx=1.0,
             ab=(-0.6, 0.5), sk=-0.6, pk=-0.8, jaw=0.8, cf=0.8), 'i'),
    (0.42, Q(hx=5.0, hy=16.5, f=(15.5, 0.0, 0.0), b=(-13.0, 0.0, 0.8), lean=0.62, tw=1.6, sx=3.0, hdx=1.4, hdy=1.2,
             ab=(-1.5, 0.3), sk=-1.0, pk=-1.1, jaw=1.0, cf=1.0), 'i2'),
    (0.52, Q(hx=5.5, hy=15.8, f=(15.5, 0.0, 0.0), b=(-11.0, 1.5, 0.8), lean=0.7, tw=1.8, sx=3.2, hdx=1.5, hdy=1.4,
             ab=(-1.7, 0.25), sk=-1.1, pk=-1.1, jaw=0.5, cf=0.8), 'o'),
    (0.62, Q(hx=5.0, hy=17.5, f=(15.5, 0.0, 0.0), b=(-10.5, 0.0, 0.4), lean=0.5, tw=1.0, sx=2.0, hdx=1.0, hdy=0.8,
             ab=(-1.0, 0.6), sk=-0.4, pk=-0.4, cf=0.3), 'o'),
    (0.80, Q(hx=3.2, hy=21.0, f=(12.0, 0.0, 0.0), b=(-11.0, 1.2, 0.2), lean=0.3, tw=0.3, sx=0.8, ab=(-0.5, 0.8),
             sk=0.2, pk=0.2), 'io'),
    (1.0, END, 'io'),
])

# ====================================================================== uzak silah gövdeleri (kollar oyunda sürülür)
# Yay: yan duruş, geniş taban; germede gövde arkaya yaslanır; bırakışta geri teper.
# Kareler: 0 ok takma, 1 germe, 2 tam gerili, 3 bırakış (Player: aim_t / bow_rel_t)
add('bow', [
    (0.0, Q(hx=-0.5, hy=21.5, f=(7.5, 0.0, 0.0), b=(-12.0, 0.0, 0.1), lean=0.02, tw=0.4, sx=0.6, hdx=0.6,
            ab=(1.4, -1.2), sk=0.2, pk=0.3), 'io'),
    (0.33, Q(hx=-1.5, hy=21.0, f=(8.5, 0.0, 0.0), b=(-12.5, 0.0, 0.0), lean=-0.06, tw=0.8, sx=1.0, hdx=0.8, hdy=0.2,
             ab=(1.45, -2.3), sk=0.2, pk=0.3), 'io'),
    (0.66, Q(hx=-2.8, hy=19.8, f=(10.0, 0.0, 0.0), b=(-13.8, 0.0, 0.0), lean=-0.2, tw=1.3, sx=1.6, hdx=1.1, hdy=0.3,
             ab=(1.5, -2.5), sk=0.25, pk=0.3, crv=-0.025, br=0.8), 'io'),
    (1.0, Q(hx=-4.4, hy=20.6, f=(9.0, 1.2, -0.25), b=(-14.5, 0.0, 0.0), lean=-0.34, tw=0.5, sx=0.2, hdx=-0.2,
            hdy=-0.5, ab=(0.6, -0.4), sk=0.8, pk=0.9, cf=-0.6, crv=-0.045, shr=-0.02, jaw=0.3), 'io'),
], frames=((0.0, 0.0), (0.25, 0.33), (0.5, 0.66), (0.75, 1.0)), fps=10)

# Fırlatma (cirit / bıçak; 0,28 sn, bırakış 0,07 sn): baş arkasına kurul, adımla bırak, takip, otur
add('throw', [
    (0.0, Q(hx=-2.0, hy=21.5, f=(6.0, 0.0, 0.0), b=(-14.0, 0.0, 0.1), lean=-0.25, tw=-1.2, sx=-1.8, hdx=-0.3,
            ab=(1.2, 0.6), sk=0.4, pk=0.4), 'io'),
    (0.2, Q(hx=-4.8, hy=20.0, f=(6.5, 2.4, -0.3), b=(-14.8, 0.0, 0.0), lean=-0.58, tw=-2.6, sx=-3.8, hdx=-0.6,
            hdy=-0.3, ab=(1.5, 0.4), sk=0.8, pk=0.8, cf=-0.7, crv=-0.06, sty=1.03), 'o'),
    (0.4, Q(hx=3.5, hy=16.5, f=(15.5, 0.0, 0.0), b=(-15.5, 0.0, 0.85), lean=0.66, tw=1.9, sx=3.4, hdx=2.0, hdy=0.6,
            ab=(-1.3, 0.4), sk=-1.2, pk=-1.3, jaw=1.0, cf=1.3, crv=0.05, shr=0.03, stx=1.05, sty=0.97), 'i'),
    (0.65, Q(hx=4.0, hy=18.0, f=(14.0, 0.0, 0.0), b=(-11.0, 1.2, 0.6), lean=0.45, tw=1.2, sx=2.4, hdx=1.0, hdy=0.6,
             ab=(-1.2, 0.5), sk=-0.6, pk=-0.6, jaw=0.4, cf=0.5), 'o'),
    (0.9, Q(hx=2.5, hy=21.0, f=(10.5, 0.0, 0.0), b=(-11.5, 0.0, 0.25), lean=0.25, tw=0.3, sx=0.8, ab=(-0.5, 0.8),
            sk=0.1, pk=0.1), 'io'),
], frames=((0.0, 0.05), (0.125, 0.2), (0.25, 0.4), (0.43, 0.65), (0.7, 0.9)), fps=14)

# Büyü (asa / kopuz / boru; 0,35 sn, bırakış ~0,15 sn sonra): topla, kaldır, öne sal, otur
add('cast', [
    (0.0, Q(hx=-1.0, hy=21.5, f=(6.5, 0.0, 0.0), b=(-13.5, 0.0, 0.1), lean=-0.05, tw=-0.4, sx=-0.5, hdy=-0.2,
            ab=(0.5, 1.2), sk=0.3, pk=0.4), 'io'),
    (0.25, Q(hx=-3.2, hy=24.0, f=(5.0, 1.0, 0.2), b=(-13.5, 0.0, 0.5), lean=-0.36, tw=-1.1, sx=-1.4, hdx=-0.5,
             hdy=-1.1, ab=(2.2, 0.5), sk=0.7, pk=0.8, cf=-0.6, ear=0.4, crv=-0.05, sty=1.04, br=1.0), 'o'),
    (0.5, Q(hx=0.8, hy=18.0, f=(12.5, 0.0, 0.0), b=(-15.0, 0.0, 0.7), lean=0.45, tw=0.9, sx=2.0, hdx=1.6, hdy=0.4,
            ab=(1.4, 0.3), sk=-1.0, pk=-1.1, jaw=1.0, cf=1.2, crv=0.045, stx=1.04, sty=0.97), 'i'),
    (0.85, Q(hx=1.5, hy=21.5, f=(9.5, 0.0, 0.0), b=(-12.0, 0.0, 0.3), lean=0.15, tw=0.2, sx=0.6, ab=(0.4, 0.8),
             sk=0.0, pk=0.0), 'o'),
], frames=((0.0, 0.05), (0.18, 0.25), (0.43, 0.5), (0.7, 0.85)), fps=10)


# ====================================================================== v29 hareket gövdeleri (ön kol sprite'ta: af)
# Ayak hedefli IK ile: durgun (ayaklar dinlenme yerinde sabit — saldırı 0. karesi / toparlanma sonu ile birebir), koşu ve
# depar (gerçek temas / iniş / geçiş / itiş: basan ayak yerde geriye kayar, salınan ayak topuğu kalçaya çekip dizle öne
# gelir), sıçrama / düşüş (gerilme, toplanma, yere uzanma), iniş (ezilme), darbe (kırbaç: baş ve post geriden gelir),
# çömelme (ninja çömelmesi).
GUARD_AF = (0.3, 1.6)
TAU = math.tau


def idle(t):
    s, c = math.sin(TAU * t), math.cos(TAU * t)
    s2 = math.sin(TAU * t - 1.1)
    q = Q(hx=0.55 * s, hy=REST['hy'] - 0.5 * (1.0 - c), lean=REST['lean'] + 0.035 * s, sx=REST['sx'] + 0.3 * s,
          tw=0.12 * s, br=1.1 * s, hdx=0.15 * s2, hdy=0.35 * s2, b=(REST['b'][0], 0.0, 0.25 + 0.12 * s),
          ab=(-0.3 - 0.06 * s, 0.9 + 0.1 * s), sk=0.2 + 0.18 * math.sin(TAU * t - 0.9),
          pk=0.3 + 0.3 * math.sin(TAU * t - 1.3), cf=0.12 * math.sin(TAU * t - 1.6), ear=0.15 * s2)
    q['af'] = (GUARD_AF[0] + 0.06 * s, GUARD_AF[1] + 0.1 * s)
    p = to_p(q)
    p['bp'] = t
    return p


def _lerp_path(pts, u):
    """[(u, x, kalkıklık, topuk)] kapalı döngü üzerinde yumuşatılmış ara değer."""
    u = u % 1.0
    for (u0, *a), (u1, *b) in zip(pts, pts[1:]):
        if u <= u1:
            k = 0.0 if u1 == u0 else (u - u0) / (u1 - u0)
            k = k * k * (3 - 2 * k)
            return tuple(x + (y - x) * k for x, y in zip(a, b))
    return tuple(pts[-1][1:])


# tek bacağın koşu yolu (kalçaya göre x, kalkıklık, topuk açısı): 0 temas (topuk), 0..0,36 basış (ayak yerde geriye),
# 0,36 itiş (parmak ucu), 0,5 topuk kalçaya, 0,72 diz önde (geçiş), 0,9 uzanma, 1 temas
RUN_LEG = [(0.0, 14.5, 0.0, -0.25), (0.12, 7.0, 0.0, 0.0), (0.24, -4.5, 0.0, 0.3), (0.36, -15.5, 0.8, 1.05),
           (0.5, -13.0, 10.0, 1.2), (0.62, -4.0, 13.5, 0.75), (0.74, 7.5, 11.5, 0.2), (0.88, 16.0, 4.0, -0.3),
           (1.0, 14.5, 0.0, -0.25)]
SPRINT_LEG = [(0.0, 16.5, 0.0, -0.3), (0.1, 8.0, 0.0, 0.0), (0.2, -5.5, 0.0, 0.35), (0.32, -18.0, 1.4, 1.15),
              (0.46, -15.5, 12.0, 1.25), (0.6, -4.5, 15.5, 0.8), (0.72, 9.5, 12.0, 0.2), (0.86, 18.5, 4.5, -0.35),
              (1.0, 16.5, 0.0, -0.3)]


def _gait(t, leg, hy0, bob, lean0, af_, ab_, cf0, sprint=False):
    u = t % 1.0
    fx, fl, fp = _lerp_path(leg, u)
    bx, bl, bpp = _lerp_path(leg, u + 0.5)
    c2 = math.cos(2 * TAU * (u - 0.42))          # en yüksek: itişten sonra uçuş (0,42 / 0,92), en alçak: temastan sonra
    sw = math.cos(TAU * u)                         # ön (yakın) bacak önde: +1
    q = Q(hx=0.0, hy=hy0 + bob * c2, f=(fx + 1.0, fl, fp), b=(bx, bl, bpp),
          lean=lean0 + 0.05 * math.cos(2 * TAU * (u - 0.15)), tw=-0.75 * sw, sx=0.3 - 0.5 * sw, hdx=0.6 + 0.2 * c2,
          hdy=0.45 * math.sin(2 * TAU * u - 0.9), sk=-0.9 + 0.35 * math.sin(2 * TAU * u - 1.2),
          pk=-1.1 + 0.25 * math.sin(2 * TAU * u - 1.6), cf=cf0 + 0.18 * math.sin(2 * TAU * u - 1.5), ear=0.25,
          ab=ab_(sw), shr=0.02 if sprint else 0.0, crv=0.02 + 0.01 * c2)
    q['af'] = af_(sw)
    p = to_p(q)
    p['bp'] = t * (2.5 if sprint else 2.0)
    return p


def run(t):
    return _gait(t, RUN_LEG, 19.6, 1.4, 0.42, lambda sw: (-0.95 * sw + 0.25, 1.7 - 0.35 * sw),
                 lambda sw: (0.95 * sw + 0.05, 1.5 + 0.35 * sw), 0.35)


def sprint(t):
    return _gait(t, SPRINT_LEG, 18.6, 1.8, 0.64, lambda sw: (-1.15 + 0.15 * sw, 0.4),
                 lambda sw: (-1.3 - 0.15 * sw, 0.3), 0.75, sprint=True)


def _air(keys, n):
    a = Anim(keys, frames=tuple((i / n, i / n + 0.5 / n) for i in range(n)), fps=8)

    def f(t):
        q = a.q(t)
        p = to_p(q)
        p['bp'] = t
        return p
    return f


def _A(**kw):
    q = Q(**kw)
    q.setdefault('af', GUARD_AF)
    return q


# sıçrama: kalkış gerilmesi (arka bacak sivri uzanır, ön diz yukarı) -> yükseliş -> tepe toplanması
JUMP = _air([
    (0.0, _A(hy=27.0, f=(9.0, 9.0, 0.3), b=(-9.5, 0.0, 1.15), lean=0.32, tw=0.4, sx=0.6, hdx=0.8, hdy=-0.6,
             af=(-1.6, 0.5), ab=(-1.9, 0.3), sk=-1.2, pk=-1.5, cf=0.9, stx=0.94, sty=1.08, crv=-0.02, jaw=0.4), 'l'),
    (0.5, _A(hy=27.5, f=(9.5, 14.0, 0.2), b=(-6.5, 7.0, 1.0), lean=0.4, tw=0.2, sx=0.4, hdx=0.7, hdy=-0.4,
             af=(-1.0, 1.0), ab=(-1.5, 0.6), sk=-1.2, pk=-1.4, cf=0.7, stx=0.97, sty=1.04), 'io'),
    (1.0, _A(hy=27.5, f=(8.0, 17.0, 0.1), b=(-1.5, 13.0, 0.6), lean=0.48, tw=0.0, sx=0.2, hdx=0.6, hdy=0.2,
             af=(-0.5, 1.4), ab=(-0.9, 0.9), sk=-0.6, pk=-0.9, cf=0.3, stx=1.02, sty=0.97, ear=0.3), 'io'),
], 3)

# düşüş: tepeden açılma -> kollar dengede, post / etek yukarı -> bacaklar yere uzanır (gerilme)
FALL = _air([
    (0.0, _A(hy=27.0, f=(8.5, 10.0, 0.2), b=(-4.0, 6.5, 0.5), lean=0.3, sx=0.4, hdx=0.4, hdy=0.3,
             af=(0.9, 1.2), ab=(-1.0, 0.8), sk=0.2, pk=0.3, cf=0.2), 'l'),
    (0.5, _A(hy=27.0, f=(8.0, 6.0, -0.1), b=(-7.0, 3.5, 0.5), lean=0.12, sx=0.6, hdx=0.2, hdy=0.5,
             af=(1.6, 0.8), ab=(-1.6, 0.5), sk=0.9, pk=1.0, cf=-0.5, ear=-0.2), 'io'),
    (1.0, _A(hy=27.0, f=(8.5, 2.5, -0.2), b=(-9.0, 1.5, 0.6), lean=0.06, sx=0.6, hdy=0.6,
             af=(1.9, 0.6), ab=(-1.9, 0.4), sk=1.2, pk=1.3, cf=-0.8, stx=0.96, sty=1.05, ear=-0.3), 'io'),
], 3)


def land(t):
    # iniş: 0 tam ezilme (çok alçak, geniş, kollar aşağı-dışa, post öne düşer), 1 toparlanma (dinlenmeye doğru)
    k = 0.0 if t < 0.5 else 1.0
    q0 = _A(hx=0.5, hy=13.0, f=(9.0, 0.0, 0.0), b=(-13.0, 0.0, 0.9), lean=0.55, tw=0.2, sx=0.6, hdx=1.0, hdy=1.6,
            af=(0.9, 0.9), ab=(-0.2, 0.9), sk=0.8, pk=0.9, cf=-0.6, stx=1.1, sty=0.9, crv=0.02, br=-0.6, ear=0.3)
    q1 = _A(hx=0.2, hy=19.0, f=(7.0, 0.0, 0.0), b=(-13.6, 0.0, 0.5), lean=0.3, sx=0.5, hdx=0.4, hdy=0.6,
            af=(0.45, 1.3), ab=(-0.3, 0.9), sk=0.4, pk=0.5, cf=-0.2, stx=1.03, sty=0.97)
    p = to_p(_mix(q0, q1, k))
    p['bp'] = t
    return p


HURT_KEYS = [
    _A(hx=-2.5, hy=21.0, f=(6.5, 1.2, -0.3), b=(-15.0, 0.0, 0.1), lean=-0.55, tw=-0.8, sx=-1.2, hdx=-1.6, hdy=-1.0,
       af=(-1.5, 0.8), ab=(-1.8, 0.5), sk=1.2, pk=1.3, cf=-0.9, jaw=1.0, ear=-0.6, crv=-0.06, shr=-0.03,
       stx=1.04, sty=0.97),
    _A(hx=-1.8, hy=19.5, f=(6.0, 0.0, 0.0), b=(-15.0, 0.0, 0.2), lean=-0.15, tw=-0.3, sx=-0.4, hdx=0.8, hdy=1.0,
       af=(-0.6, 1.2), ab=(-1.0, 0.8), sk=0.6, pk=0.8, cf=0.4, jaw=0.4, ear=-0.2, crv=0.02),
    _A(hx=-0.8, hy=21.5, f=(5.8, 0.0, 0.0), b=(-14.5, 0.0, 0.25), lean=0.08, tw=0.0, sx=0.2, hdx=0.2, hdy=0.3,
       af=(0.1, 1.4), ab=(-0.5, 0.9), sk=0.3, pk=0.4, cf=0.1, jaw=0.2),
]


def hurt(t):
    # darbe (kırbaç): 0 gövde geriye fırlar, baş geriden gelir (boyun kırbacı), kollar öne savrulur, post öne çarpar;
    # 1 aşırı telafi (baş öne düşer); 2 toparlanma
    p = to_p(HURT_KEYS[min(2, int(t * 3))])
    p['bp'] = t
    return p


def crouch(t):
    # ninja çömelmesi: ön ayak düz basar, arka diz yere yakın (parmak ucunda), gövde öne yatık, baş hedefe bakar
    s = math.sin(TAU * t)
    q = _A(hx=0.5, hy=12.0 + 0.3 * s, f=(9.5, 0.0, 0.0), b=(-9.0, 0.0, 1.15), lean=0.42, tw=0.1, sx=0.4, hdx=0.9,
           hdy=-0.2, af=(0.65, 1.45), ab=(0.2, 1.1), sk=0.6, pk=0.4, cf=0.0, br=0.5 * s, crv=0.015)
    p = to_p(q)
    p['bp'] = t
    return p
