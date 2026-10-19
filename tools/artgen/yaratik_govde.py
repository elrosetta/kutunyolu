"""v29 yer yaratıklarının tam gövde animasyonu: ortak anahtar poz / zaman çizelgesi ve sprite json eşleme yardımcıları.

Bkz. docs/TASARIM.md "v29: yer yaratıklarının tam gövde animasyonu" ve docs/v29/enemy_anim_json.md (json sözleşmesi).

Bir yaratık modülü (ör. kara_boru_ink.py) şunları tanımlar:
  SEQS   : {ad: Seq}     satır sırası = sözlük sırası; her Seq anahtar pozlardan kareleri üretir
  DURUM  : {anahtar: {...}}  yapay zekâ durumu -> animasyon / evre eşlemesi (json "durum"; Enemy._anim_tick)
  render_frame(anim, i[, var])  -> (rgba, nm, em, info)   (SEQS[anim].pose(i) ile çizer)

Poz: düz sözlük (sayı ya da sayı demeti). Anahtarlar arası yumuşatma (ease) bengu_govde.py ile aynı adlarla:
  'l' doğrusal, 'io' yumuşak, 'i' / 'i2' hızlanarak (vuruş), 'o' / 'o2' yavaşlayarak (oturma), 'h' tut sonra geç.
Kare: (rt, ts) — rt pozun çizildiği an (anahtar zamanı, 0..1), ts karenin kendi evresi içindeki başlangıç anı (0..1).
Evre (seg): satırın kare aralığı [ilk, son) bir yapay zekâ evresine (windup / strike / recover ...) bağlanır; oyunda
o evrenin ilerleyişi (ör. hazırlıkta 1 - st / st0) ts'lerle kareye çevrilir. lead: evrenin son karesi, evrenin son N
saniyesinde gösterilir (ör. hazırlığın bitiminde 0,05 sn "fırlayış" karesi: isabet karesinden hemen önce süpürme).
"""
import math


def clamp(v, a, b):
    return a if v < a else (b if v > b else v)


def ease(u, e):
    u = clamp(u, 0.0, 1.0)
    if e == 'l':
        return u
    if e == 'i':
        return u * u * u
    if e == 'i2':
        return u * u
    if e == 'o':
        return 1.0 - (1.0 - u) ** 3
    if e == 'o2':
        return 1.0 - (1.0 - u) ** 2
    if e == 'h':
        return 0.0 if u < 0.5 else ease((u - 0.5) * 2.0, 'io')
    if e == 'b':          # geri tepme: hedefi biraz aşıp oturur
        return 1.0 - (1.0 - u) ** 2 * (1.0 - 2.2 * u)
    return u * u * (3 - 2 * u)


def mix(a, b, u):
    out = dict(a)
    for k, vb in b.items():
        va = a.get(k, vb)
        if isinstance(va, tuple):
            out[k] = tuple(x + (y - x) * u for x, y in zip(va, vb))
        elif isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            out[k] = va + (vb - va) * u
        else:
            out[k] = vb if u >= 0.5 else va
    return out


class Seq:
    """Bir sprite satırı.

    keys  : [(tau, poz, ease)] — poz dinlenme pozunun (rest) üstüne yazılan farklar; ease bu anahtara VARAN parçanın eğrisi
    frames: [(rt, ts)] ya da yalnızca rt listesi (ts = evre içinde eşit aralık)
    seg   : [(evre, kare_sayısı)] sırayla; None = tek evre (döngü / tepki)
    loop  : döngü (keys 0 ve 1 aynı poz olmalı; rt = i / n kendiliğinden)
    lead  : {evre: sn}
    extra : json satırına eklenecek alanlar (ör. {"vx": 90, "alt": [["walk", 50]]})
    proc  : proc(poz, rt) -> poz  (nefes, kuyruk dalgası gibi döngüsel ekler; anahtarlardan sonra uygulanır)
    """

    def __init__(self, keys, frames=None, n=None, fps=10, loop=False, seg=None, lead=None, extra=None, proc=None,
                 rest=None):
        self.keys = sorted(keys, key=lambda k: k[0])
        self.loop = loop
        self.fps = fps
        self.lead = lead or {}
        self.extra = extra or {}
        self.proc = proc
        self.rest = rest or {}
        if frames is None:
            n = n or 6
            frames = [i / n for i in range(n)] if loop else [i / max(1, n - 1) for i in range(n)]
        fr = []
        for f in frames:
            fr.append(tuple(f) if isinstance(f, (tuple, list)) else (f, None))
        self.seg = seg or [('all', len(fr))]
        assert sum(c for _, c in self.seg) == len(fr), 'seg kare sayısı tutmuyor'
        # ts verilmemişse evre içinde eşit aralık
        out = []
        i = 0
        for _name, c in self.seg:
            for j in range(c):
                rt, ts = fr[i]
                out.append((rt, ts if ts is not None else j / c))
                i += 1
        self.frames = out

    def __len__(self):
        return len(self.frames)

    def q(self, t):
        ks = self.keys
        base = dict(self.rest)
        if self.loop:
            t = t % 1.0
        if t <= ks[0][0]:
            return mix(base, ks[0][1], 1.0)
        for (t0, q0, _e0), (t1, q1, e1) in zip(ks, ks[1:]):
            if t <= t1:
                u = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                return mix(mix(base, q0, 1.0), mix(base, q1, 1.0), ease(u, e1))
        return mix(base, ks[-1][1], 1.0)

    def pose(self, i):
        rt = self.frames[i][0]
        p = self.q(rt)
        p['_t'] = rt
        if self.proc:
            p = self.proc(p, rt)
        return p

    def meta(self):
        """json satır alanları: seg / ts / lead + extra"""
        m = {}
        if len(self.seg) > 1 or self.seg[0][0] != 'all':
            sg, i = {}, 0
            for name, c in self.seg:
                sg[name] = [i, i + c]
                i += c
            m['seg'] = sg
        if not self.loop:
            m['ts'] = [round(f[1], 4) for f in self.frames]
        if self.lead:
            m['lead'] = {k: round(v, 3) for k, v in self.lead.items()}
        m.update(self.extra)
        return m


def layout(seqs):
    """export_ink.export_sheet için satır düzeni (sözlük; sıra = satır)."""
    return {'anims': {n: {'row': r, 'frames': len(s), 'fps': s.fps, 'loop': s.loop, 'arm': False}
                      for r, (n, s) in enumerate(seqs.items())}}


def anim_meta(seqs):
    return {n: s.meta() for n, s in seqs.items()}


def check_durum(seqs, durum):
    """DURUM tutarlılığı: animasyon ve evre adları var mı."""
    for k, e in durum.items():
        a = e['a']
        assert a in seqs, '%s: animasyon yok: %s' % (k, a)
        s = e.get('s')
        if s:
            assert s in [n for n, _ in seqs[a].seg], '%s: %s satırında evre yok: %s' % (k, a, s)
        assert e.get('u', 'st') in ('st', 'up', 'vy', 'loop'), k


# ---------------------------------------------------------------- iskelet yardımcıları
def rot(v, a):
    ca, sa = math.cos(a), math.sin(a)
    return (v[0] * ca - v[1] * sa, v[0] * sa + v[1] * ca)


def rot_about(p, c, a):
    d = rot((p[0] - c[0], p[1] - c[1]), a)
    return (c[0] + d[0], c[1] + d[1])


def ik2(a, b, l1, l2, bend):
    """a'dan b'ye iki kemik; bend=+1/-1 eklemin tarafı. Erişilemezse b'ye doğru uzanır. (eklem, uç)"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    d = max(abs(l1 - l2) + 0.05, min(l1 + l2 - 0.05, d))
    ca = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1.0, 1.0)
    ang = math.acos(ca)
    base = math.atan2(dy, dx)
    j = (a[0] + math.cos(base + bend * ang) * l1, a[1] + math.sin(base + bend * ang) * l1)
    e = (a[0] + math.cos(base) * d, a[1] + math.sin(base) * d)
    return j, e


def xf_push(cv, c, ang=0.0, dx=0.0, dy=0.0, sx=1.0, sy=1.0):
    """Tuvale dünya dönüşümü: c çevresinde ölçek + dönüş, sonra öteleme (tüm çizim; devrilme, yuvarlanma, ölüm)."""
    ca, sa = math.cos(ang), math.sin(ang)

    def f(q):
        x, y = (q[0] - c[0]) * sx, (q[1] - c[1]) * sy
        return (c[0] + x * ca - y * sa + dx, c[1] + x * sa + y * ca + dy)
    cv.push(f)


def wave(t, k=1.0, ph=0.0):
    return math.sin((t * k + ph) * math.tau)


# ---------------------------------------------------------------- standart tepki zamanlamaları (oyunla uyumlu)
# _hurt (hafif sarsılma) ~0,22 sn, _hurt_big (ağır sendeleme) ~0,45 sn, _break (duruş kırık / sersem) döngü,
# _launch (havada savrulma) dikey hız evresi, _getup ~0,5 sn, _death ~0,9 sn, _turn ~0,22 sn.
REACT = {
    '_hurt': {'a': 'hurt', 'u': 'up', 'd': 0.22},
    '_hurt_big': {'a': 'hurt_big', 'u': 'up', 'd': 0.45},
    '_break': {'a': 'stun', 'u': 'loop'},
    '_launch': {'a': 'launch', 'u': 'vy'},
    '_getup': {'a': 'getup', 'u': 'up', 'd': 0.5},
    '_death': {'a': 'death', 'u': 'up', 'd': 0.9},
    '_turn': {'a': 'turn', 'u': 'up', 'd': 0.22},
}


# ---------------------------------------------------------------- tuval eki: dönüşüm altında ayrıntılar
def world(cv, p):
    """Tuvalin o anki dönüşüm yığınıyla dünya noktası (çapalar: ağız, el)."""
    x, y = p[0], p[1]
    for f in reversed(cv.xf):
        x, y = f((x, y))
    return (x, y)


def bake_xf(cv):
    """inkkit.shape ayrıntılarındaki ('ink' / 'stroke') dünya noktaları çizim anında (finish) dönüştürülür; o anda
    dönüşüm yığını boş olduğundan push altında kurulan ayrıntılar kayardı. Bu tuval için (yalnızca bu örnekte)
    ayrıntı noktaları kuyruğa girerken dönüştürülür. Diğer çizimleri (Bengü vb.) etkilemez."""
    if getattr(cv, '_bake', False):
        return cv
    cv._bake = True
    o_shape = cv.shape

    def shape(path, mat, z=0.0, details=(), **kw):
        if cv.xf and details:
            nd = []
            for d in details:
                if d and d[0] in ('ink', 'stroke'):
                    d = (d[0], [world(cv, p) for p in d[1]]) + tuple(d[2:])
                nd.append(d)
            details = nd
        if cv.xf and details:
            saved = cv.xf
            cv.xf = []
            try:
                o_shape(path, mat, z=z, details=details, **kw)
            finally:
                cv.xf = saved
            return
        o_shape(path, mat, z=z, details=details, **kw)
    cv.shape = shape
    return cv
