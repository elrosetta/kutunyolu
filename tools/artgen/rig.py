"""İskelet yardımcıları: ileri kinematik, dönüşümlü çizim vekili."""
import math


def fk_leg(hip, a1, a2, l1=10.5, l2=10.5):
    k = (hip[0] + math.sin(a1) * l1, hip[1] + math.cos(a1) * l1)
    f = (k[0] + math.sin(a1 - a2) * l2, k[1] + math.cos(a1 - a2) * l2)
    return k, f


def fk_arm(sh, a1, a2, l1=8.5, l2=8.0):
    e = (sh[0] + math.sin(a1) * l1, sh[1] + math.cos(a1) * l1)
    h = (e[0] + math.sin(a1 + a2) * l2, e[1] + math.cos(a1 + a2) * l2)
    return e, h


def lerp2(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def chain(start, n, seg, ang0, bend, phase, wave, sway=0.0):
    """Sarkan/salınan zincir noktaları (saç örgüsü, kuyruk, kuşak ucu)."""
    pts = [start]
    a = ang0
    x, y = start
    for i in range(n):
        a = ang0 + bend * i + math.sin(phase - i * 0.9) * wave * (0.3 + i / n) + sway * (i / n)
        x += math.cos(a) * seg
        y += math.sin(a) * seg
        pts.append((x, y))
    return pts


class Xf:
    """Dönüşümlü çizim: tüm noktaları (ox,oy) etrafında döndürüp taşır."""
    def __init__(self, c, ox=0.0, oy=0.0, ang=0.0, z=0.0, pivot=(0.0, 0.0), flip=1):
        self.c, self.ox, self.oy, self.z, self.flip = c, ox, oy, z, flip
        self.ca, self.sa, self.ang = math.cos(ang), math.sin(ang), ang
        self.pv = pivot

    def P(self, p):
        x, y = p[0] - self.pv[0], (p[1] - self.pv[1]) * self.flip
        return (self.ox + x * self.ca - y * self.sa, self.oy + x * self.sa + y * self.ca)

    def capsule(self, p0, p1, r0, r1, mat, z=0.0, **kw):
        self.c.capsule(self.P(p0), self.P(p1), r0, r1, mat, z=z + self.z, **kw)

    def ellipse(self, c_, rx, ry, mat, z=0.0, rot=0.0, **kw):
        self.c.ellipse(self.P(c_), rx, ry, mat, z=z + self.z, rot=rot + self.ang, **kw)

    def poly(self, pts, mat, z=0.0, **kw):
        self.c.poly([self.P(p) for p in pts], mat, z=z + self.z, **kw)

    def dot(self, p, mat, z=50.0, **kw):
        self.c.dot(self.P(p), mat, z=z + self.z, **kw)
