"""Kurt anatomisi yardımcıları (v13): dört ayaklı bacaklar, tüy öbekleri, ters kinematik.

Eski kurt çizimleri iki parçalı "çubuk" bacak kullanıyordu (kalça -> diz -> ayak). Burada:
  * ön bacak: kürek kemiği kası -> üst kol -> dirsek (geride) -> ön kol -> bilek -> tarak -> pençe,
  * arka bacak: kalın uyluk -> diz (önde) -> baldır -> topuk (hock, geride) -> tarak -> pençe.
Ayağın yere değdiği nokta eski iki parçalı FK ile aynı hesaplanır (animasyonların yer teması bozulmaz);
ara eklemler o hedefe iki kemikli IK ile oturtulur.
Koordinatlar: ayak merkezi (0,0), y aşağı pozitif, yüz sağa. s: ölçek (piksel/birim).
"""
import math
from rig import fk_leg


def ik(a, b, l1, l2, bend):
    """a'dan b'ye iki kemik; bend=+1 eklem yön vektörünün saat yönünde (ekranda) tarafında."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    d = max(abs(l1 - l2) + 0.05, min(l1 + l2 - 0.05, d))
    ca = max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)))
    ang = math.acos(ca)
    base = math.atan2(dy, dx)
    j = (a[0] + math.cos(base + bend * ang) * l1, a[1] + math.sin(base + bend * ang) * l1)
    e = (a[0] + math.cos(base) * d, a[1] + math.sin(base) * d)
    return j, e


def rot(v, a):
    ca, sa = math.cos(a), math.sin(a)
    return (v[0] * ca - v[1] * sa, v[0] * sa + v[1] * ca)


def norm(v):
    l = math.hypot(v[0], v[1]) + 1e-9
    return (v[0] / l, v[1] / l)


def add(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def tufts(c, pts, mat, z, length, ang, width=None, jitter=0.0, bevel=1.0):
    """Sivri tüy öbekleri: her noktadan ang (radyan, 0 sağ) yönüne uzanan üçgenler."""
    width = width or length * 0.6
    for i, (x, y) in enumerate(pts):
        a = ang + math.sin(i * 2.3 + x * 0.1) * jitter
        ln = length * (0.78 + 0.22 * math.cos(i * 1.7))
        tip = (x + math.cos(a) * ln, y + math.sin(a) * ln)
        nx_, ny_ = -math.sin(a) * width * 0.5, math.cos(a) * width * 0.5
        c.poly([(x + nx_, y + ny_), (x - nx_, y - ny_), tip], mat, z=z, bevel=bevel, height=1.0)


def hind_leg(c, hip, a, s, mat, z, l_old=(9.0, 10.5), thigh_r=4.2, sh_mat=None, paw_mat=None, claw=None, fold=0.0):
    """Arka bacak. a: eski (a1, a2) açıları; ayak hedefi eski FK'dan. Dönüş: (diz, topuk, ayak) noktaları."""
    _, foot = fk_leg(hip, a[0], a[1], l_old[0] * s, l_old[1] * s)
    # topuk: kalça-ayak doğrultusunun gerisinde; bacak geriye uzadıkça tarak bacağa hizalanır
    up = norm((hip[0] - foot[0], hip[1] - foot[1]))
    meta_l = 5.4 * s
    hock = add(foot, rot(up, -0.55 - fold * 0.5), meta_l)
    knee, hock = ik(hip, hock, 7.6 * s, 7.2 * s, -1)
    sh = sh_mat or mat
    # uyluk kası: kalçaya kaynaşan büyük kütle (uyluk yönünde döndürülmüş elips)
    th = lerp(hip, knee, 0.42)
    ang = math.atan2(knee[1] - hip[1], knee[0] - hip[0])
    c.ellipse(th, 6.0 * s, thigh_r * s, mat, z=z, rot=ang)
    c.capsule(hip, knee, thigh_r * 0.9 * s, 2.3 * s, mat, z=z + 0.2)
    # baldır (diz -> topuk), arkası tüy fırçası
    c.capsule(knee, hock, 2.3 * s, 1.35 * s, mat, z=z + 0.3, paint=[(lambda lu, lv, px, py: lv < -0.45, sh)])
    c.ellipse(hock, 1.55 * s, 1.55 * s, sh, z=z + 0.25)
    c.capsule(hock, foot, 1.4 * s, 1.25 * s, mat, z=z + 0.4)
    _paw(c, foot, s, paw_mat or mat, z + 0.5, claw)
    return knee, hock, foot


def front_leg(c, sh, a, s, mat, z, l_old=(9.0, 10.0), sh_mat=None, paw_mat=None, claw=None, blade=True):
    """Ön bacak: kürek + üst kol + dirsek (geride) + ön kol + tarak + pençe."""
    _, foot = fk_leg(sh, a[0], a[1], l_old[0] * s, l_old[1] * s)
    up = norm((sh[0] - foot[0], sh[1] - foot[1]))
    wrist = add(foot, rot(up, 0.32), 3.2 * s)
    elbow, wrist = ik(sh, wrist, 7.6 * s, 8.4 * s, 1)
    shm = sh_mat or mat
    if blade:
        ang = math.atan2(elbow[1] - sh[1], elbow[0] - sh[0])
        c.ellipse(lerp(sh, elbow, 0.35), 5.2 * s, 3.4 * s, mat, z=z, rot=ang)
    c.capsule(sh, elbow, 3.1 * s, 2.3 * s, mat, z=z + 0.2)
    c.capsule(elbow, wrist, 2.0 * s, 1.45 * s, mat, z=z + 0.3, paint=[(lambda lu, lv, px, py: lv > 0.5, shm)])
    c.capsule(wrist, foot, 1.45 * s, 1.3 * s, mat, z=z + 0.4)
    _paw(c, foot, s, paw_mat or mat, z + 0.5, claw)
    return elbow, wrist, foot


def _paw(c, f, s, mat, z, claw):
    c.ellipse((f[0] + 1.3 * s, f[1] - 0.9 * s), 2.5 * s, 1.45 * s, mat, z=z)
    c.ellipse((f[0] + 2.6 * s, f[1] - 0.7 * s), 1.4 * s, 1.15 * s, mat, z=z + 0.3)
    if claw is not None:
        for i in range(2):
            x = f[0] + (3.4 + i * 0.3) * s
            y = f[1] - (1.1 - i * 0.9) * s
            c.poly([(x - 0.4 * s, y - 0.5 * s), (x - 0.4 * s, y + 0.5 * s), (x + 1.3 * s, y + 0.6 * s)], claw, z=z + 1.0, bevel=0.5, height=0.5)
