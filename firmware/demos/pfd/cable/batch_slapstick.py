"""Silent slapstick and cartoon physics: rakes, hiccups, cliffs, toast and a cat, with no words at all."""
import math

import numpy as np

from .. import draw
from ..draw import N, X, Y
from .kit import BLACK, LEG, SKINS, WHITE, ellipse, face, hand, line, poly, rect, star, toon, vgrad
from .shows import Show

YEL = (1, .9, .2)


# ---------------------------------------------------------------- timing

def _cl(u):
    return 0.0 if u < 0 else 1.0 if u > 1 else u


def _ease(u):
    u = _cl(u)
    return u * u * (3 - 2 * u)


def _ramp(t, t0, t1):
    return _cl((t - t0) / (t1 - t0))


def _lerp(a, b, u):
    return a + (b - a) * u


# ---------------------------------------------------------------- the business

def _stars(img, x, y, t, r=9.0, n=3, s=2.5):
    """Stars round a head."""
    for k in range(n):
        a = t * 6 + k * 2 * math.pi / n
        star(img, x + r * math.cos(a), y + 0.35 * r * math.sin(a), s, YEL, n=5, inner=0.45)


def _dust(img, x, y, u, n=6, spread=1.0, col=(.85, .82, .75)):
    """A puff of dust kicked up either side of (x, y), u seconds after the thump."""
    if not 0 <= u < 1.0:
        return
    for k in range(n):
        s = -1 if k % 2 else 1
        ellipse(img, x + s * (4 + 26 * spread * u * (1 + k // 2) / 2), y - 2 - k // 2 * 3 - 6 * u, 3 + 6 * u * spread,
                2 + 4 * u * spread, col, a=0.85 * (1 - u))


def _shake(img, u, amp=4.0):
    """The camera jolts, u seconds after a thump."""
    if 0 <= u < 0.8:
        s = int(round(amp * math.sin(u * 50) * math.exp(-u * 6)))
        if s:
            img[:] = np.roll(img, (s, -s // 2), (0, 1))


def _bang(img, x, y, r, t, col=(1, .95, .4)):
    """The little starburst where something connects."""
    star(img, x, y, r, col, n=8, inner=0.45, rot=t * 3)
    star(img, x, y, r * 0.5, WHITE, n=8, inner=0.5, rot=t * 3)


def _sprite(img, prims, x, y, ang=0.0, sx=1.0, sy=1.0):
    """Shapes in a sprite's own coordinates, moved to (x, y), turned by ang and flipped by sx, sy:
    ("e", x, y, rx, ry, rgb) ellipses, ("p", pts, rgb) polygons, ("r", x0, y0, x1, y1, rgb) boxes,
    ("l", x0, y0, x1, y1, w, rgb) lines."""
    c, s = math.cos(ang), math.sin(ang)

    def at(px, py):
        px, py = px * sx, py * sy
        return x + px * c - py * s, y + px * s + py * c

    for p in prims:
        k = p[0]
        if k == "e":
            ellipse(img, *at(p[1], p[2]), p[3] * abs(sx), p[4] * abs(sy), p[5], rot=ang)
        elif k == "p":
            poly(img, [at(*q) for q in p[1]], p[2])
        elif k == "r":
            _, x0, y0, x1, y1, col = p
            poly(img, [at(x0, y0), at(x1, y0), at(x1, y1), at(x0, y1)], col)
        else:
            _, x0, y0, x1, y1, w, col = p
            line(img, *at(x0, y0), *at(x1, y1), col, w=w * abs(sx))


def _figure(img, x, y, h, skin, shirt, t=0.0, d=1, thigh=0.0, shin=0.0, arms=(0.3, 0.3), look=(0.0, 0.0), mood=0,
            talk=0.0, seed=0.0, pants=(.2, .2, .35), rot=0.0):
    """A toon that can sit: hips at (x, y), legs in two parts, thigh and shin each at an angle from
    hanging down, swung towards d (1 right, -1 left): thigh pi/2 and shin 0 is sitting on a chair.
    rot tips the body above the hips. Returns the head, (x, y, r)."""
    w = max(1.5, h * 0.09)
    half = LEG * h / 2
    for k in (-1, 1):
        hx = x + k * h * 0.05
        kx, ky = hx + d * half * math.sin(thigh), y + half * math.cos(thigh)
        line(img, hx, y, kx, ky, pants, w)
        line(img, kx, ky, kx + d * half * math.sin(shin), ky + half * math.cos(shin), pants, w)
    c, s = math.cos(rot), math.sin(rot)

    def at(dx, dy):
        return x + dx * c - dy * s, y + dx * s + dy * c

    sy = -h * 0.3
    for k, a in zip((-1, 1), arms):
        line(img, *at(k * h * 0.12, sy), *at(k * h * 0.12 + k * math.sin(a) * h * 0.28, sy + math.cos(a) * h * 0.28),
             shirt, w * 0.85)
        ellipse(img, *at(k * h * 0.12 + k * math.sin(a) * h * 0.3, sy + math.cos(a) * h * 0.3), w * 0.7, w * 0.7, skin)
    ellipse(img, *at(0, -h * 0.17), h * 0.15, h * 0.2, shirt, rot=rot)
    r = h * 0.14
    hx, hy = at(0, -h * 0.34 - r * 1.05)
    face(img, hx, hy, r, skin, t, talk, look, mood, seed, rot=rot)
    return hx, hy, r


def _settle(t, t0, flat=0.3):
    """Squashed flat at t0, then popping back into shape with a wobble."""
    u = t - t0
    if u < 0:
        return 1.0
    return 1 - (1 - flat) * math.exp(-u * 7) * math.cos(u * 18)


# ---------------------------------------------------------------- the shows

class Rakes(Show):
    """Silent: a garden, two rakes, and a man caught between them."""
    num, title, length = 301, "RAKES", 9.5
    G, H = 106, 46
    A, B = 56, 30                   # where the rakes' heads lie
    PA, PB = 52, 34                 # where he stands on each
    L = 42
    HITS = [1.8, 2.55, 3.15, 3.6, 3.95, 4.25, 4.5, 4.72]       # A, B, A, B, ...
    LAST = 8.6

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.98, .78, .45), (.95, .55, .45), 0, self.G)
        ellipse(self.bg, 28, 34, 11, 11, (1, .93, .65))
        for x in range(2, N, 10):
            poly(self.bg, [(x, self.G - 30), (x + 3.5, self.G - 35), (x + 7, self.G - 30), (x + 7, self.G), (x, self.G)],
                 (.92, .86, .74))
        rect(self.bg, 0, self.G - 22, N, self.G - 19, (.8, .72, .62))
        vgrad(self.bg, (.35, .72, .25), (.18, .48, .14), self.G, N)
        rng = np.random.default_rng(301)
        for _ in range(30):
            x, y = rng.uniform(0, N), rng.uniform(self.G + 3, N)
            line(self.bg, x, y, x + rng.uniform(-2, 2), y - 3, (.15, .4, .1), w=1)

    def _rake(self, img, x, d, th):
        y = self.G - 1
        c, s = math.cos(th), math.sin(th)
        ux, uy = d * c, -s
        line(img, x, y, x + ux * self.L, y + uy * self.L, (.78, .52, .22), w=2.6)
        px, py = -d * s, -c                         # the tines point this way
        line(img, x - ux * 3, y - uy * 3, x + ux * 3, y + uy * 3, (.5, .5, .55), w=2.4)
        for k in (-2.5, 0, 2.5):
            line(img, x + ux * k, y + uy * k, x + ux * k + px * 5, y + uy * k + py * 5, (.5, .5, .55), w=1)

    def _theta(self, t, hits):
        th = 0.0
        for h in hits:
            u = t - h
            if -0.1 <= u < 0:
                th = max(th, 1.75 * (u + 0.1) / 0.1)
            elif 0 <= u < 0.12:
                th = max(th, 1.75)
            elif 0.12 <= u < 0.4:
                th = max(th, 1.75 * (1 - ((u - 0.12) / 0.28) ** 2))
        return th

    def _man(self, t):
        base = self.G - LEG * self.H
        m = dict(x=-10.0, y=base, rot=0.0, arms=(0.3, 0.3), walk=0.0, look=(1, 0), mood=0, stars=False)
        hits = self.HITS
        if t < hits[0]:
            m.update(x=-10 + (self.PA + 10) * t / hits[0], walk=1)
        elif t < hits[-1]:
            k = max(i for i, h in enumerate(hits) if h <= t)
            p0, p1 = (self.PA, self.PB) if k % 2 == 0 else (self.PB, self.PA)
            u = (t - hits[k]) / (hits[k + 1] - hits[k])
            sgn = -1 if k % 2 == 0 else 1
            m.update(x=_lerp(p0, p1, _ease(u)), rot=sgn * (0.3 + 0.06 * k) * math.sin(math.pi * min(1.0, u * 1.3)),
                     arms=(2.2 + 0.6 * math.sin(t * 25), 2.2 - 0.6 * math.sin(t * 25)), mood=-1, look=(0, 0),
                     stars=k >= 2)
        elif t < 5.3:
            u = (t - hits[-1]) / (5.3 - hits[-1])
            m.update(x=_lerp(self.PB, 46, u), rot=math.pi / 2 * u, y=base - 10 * math.sin(math.pi * u) + (self.G - 5 - base) * u,
                     arms=(2.6, 2.6), mood=-1)
        elif t < 7.0:
            m.update(x=46, rot=math.pi / 2, y=self.G - 5, stars=True, look=(0, 0))
        elif t < 7.4:
            u = _ease((t - 7.0) / 0.4)
            m.update(x=46, rot=math.pi / 2 * (1 - u), y=_lerp(self.G - 5, base, u))
        elif t < 8.2:
            m.update(x=46, look=(-1, 0) if t < 7.7 else (1, 0) if t < 8.0 else (0, 0), mood=1 if t >= 8.0 else 0,
                     arms=(0.3, 0.3) if t < 8.0 else (0.3, 2.6))
        elif t < self.LAST:
            m.update(x=_lerp(46, self.PA, (t - 8.2) / (self.LAST - 8.2)), walk=1, mood=1)
        else:
            u = _ease((t - self.LAST - 0.08) / 0.35)
            m.update(x=self.PA, rot=-math.pi / 2 * u, y=_lerp(base, self.G - 5, u), arms=(0.3, 0.3), look=(0, 0),
                     mood=-1, stars=t > self.LAST + 0.5)
        return m

    def draw(self, img, t):
        img[:] = self.bg
        m = self._man(t)
        hx, hy, r = toon(img, m["x"], m["y"], self.H, SKINS[0], (.25, .35, .8), t, walk=m["walk"], rot=m["rot"],
                         arms=m["arms"], look=m["look"], mood=m["mood"], seed=1, pants=(.45, .3, .15))
        self._rake(img, self.A, 1, self._theta(t, self.HITS[0::2] + [self.LAST]))
        self._rake(img, self.B, -1, self._theta(t, self.HITS[1::2]))
        for h in self.HITS + [self.LAST]:
            if 0 <= t - h < 0.12:
                _bang(img, hx + (-r if h in self.HITS[1::2] else r) * 0.8, hy, 7, t)
        if m["stars"]:
            _stars(img, hx, hy - r - 2, t)


class Hiccup(Show):
    """Silent: hiccups, in a library."""
    num, title, length = 307, "HIC", 10.0
    G, H, X0 = 112, 48, 44
    HICS = [(0.9, 3), (2.0, 8), (3.0, 16), (3.9, 28)]
    LAUNCH, DOWN, LAST = 4.8, 6.9, 8.7
    SKY = (.45, .75, 1)

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        wall = (.45, .2, .35) + 0.04 * np.sin(X * 0.8)[..., None] * np.array((1, 1, 1), np.float32)
        self.bg[:] = wall
        rect(self.bg, 0, 0, N, 10, (.85, .78, .65))
        rect(self.bg, 0, 10, N, 12, (.6, .5, .4))
        rect(self.bg, 0, self.G, N, N, (.4, .25, .15))
        rect(self.bg, 0, self.G, N, self.G + 2, (.3, .18, .1))
        rect(self.bg, 6, 22, 44, 36, (.95, .9, .75))
        draw.text(self.bg, "QUIET", 25, 24, (.6, .1, .1), center=True)
        # the bookshelf, kept apart so it can jump
        rng = np.random.default_rng(307)
        self.shelf = np.empty((self.G - 30, 46, 3), np.float32)
        self.shelf[:] = (.35, .2, .1)
        for row in range(4):
            y0 = 4 + row * 20
            rect(self.shelf, 3, y0, 43, y0 + 16, (.18, .1, .05))
            x = 4
            while x < 41:
                w = int(rng.integers(3, 6))
                hgt = int(rng.integers(10, 16))
                col = [(.8, .2, .2), (.2, .5, .8), (.9, .75, .2), (.25, .6, .3), (.7, .4, .8)][int(rng.integers(5))]
                rect(self.shelf, x, y0 + 16 - hgt, min(42, x + w), y0 + 16, col)
                x += w + 1
            rect(self.shelf, 0, y0 + 16, 46, y0 + 19, (.45, .28, .14))

    def _lift(self, t):
        """How high he is, and how squashed (flat < 1) or stretched (flat > 1)."""
        for h0, a in self.HICS:
            dur = 0.22 + a / 70
            u = t - h0
            if -0.08 <= u < 0:
                return 0.0, 0.88
            if 0 <= u < dur:
                v = u / dur
                return a * math.sin(math.pi * v), 1.12 if v < 0.5 else 1.0
            if dur <= u < dur + 0.1:
                return 0.0, 0.88
        return 0.0, 1.0

    def draw(self, img, t):
        img[:] = self.bg
        hop = 0.0
        if t > self.LAST:
            hop = 10 * math.sin(math.pi * min(1.0, (t - self.LAST - 0.05) / 0.3)) if t < self.LAST + 0.35 else 0.0
        y0 = 30 - int(hop)
        img[y0:y0 + self.shelf.shape[0], 76:122] = self.shelf
        if t > self.LAST + 0.2:                     # books jump out
            for k, (bx, col) in enumerate(((84, (.8, .2, .2)), (98, (.9, .75, .2)), (112, (.2, .5, .8)))):
                u = t - self.LAST - 0.2 - k * 0.08
                if u > 0:
                    fy = min(self.G - 3, 40 + k * 20 + 150 * u * u)
                    _sprite(img, [("r", -2, -6, 2, 6, col)], bx + 10 * u, fy, ang=min(1.57, u * 6))
        x, base = self.X0, self.G - LEG * self.H
        hole = t > self.LAUNCH + 0.12
        if hole:                                    # the ceiling, with him-shaped hole
            ellipse(img, x, 4, 7, 6, self.SKY)
            rect(img, x - 7, 4, x + 8, 12, self.SKY)
            for k in (-1, 1):
                line(img, x + k * 10, 6, x + k * 4, 11, self.SKY, w=3)
        lift, flat = self._lift(t)
        hat = None
        if self.LAUNCH - 0.2 <= t < self.LAUNCH:     # the big one: a crouch
            flat = 0.72
        elif self.LAUNCH <= t < self.DOWN:
            u = t - self.LAUNCH
            lift, flat = 900 * u * u + 60 * u, 1.4
        elif self.DOWN <= t < self.DOWN + 0.15:
            lift, flat = 160 * (1 - (t - self.DOWN) / 0.15), 1.4
        elif t >= self.DOWN + 0.15:
            flat = _settle(t, 7.9, 0.3) if t > 7.9 else 0.3
        y = self.G - LEG * self.H * flat - lift
        if lift < 200:
            arms = (2.4 + 0.4 * math.sin(t * 30), 2.4 - 0.4 * math.sin(t * 30)) if lift > 2 else (0.3, 0.3)
            hx, hy, r = toon(img, x, y, self.H, SKINS[3], (.95, .6, .15), t, rot=0.0, arms=arms, flat=flat,
                             look=(0, 0) if t > self.LAST + 0.4 or t < 0.9 else (0, -1) if lift > 0 else (1, 0),
                             mood=-1 if self.DOWN < t else 0, talk=0.7 if lift > 3 else 0, seed=7, pants=(.3, .3, .5))
            if not self.LAUNCH + 0.05 <= t < self.DOWN + 0.15:
                hat = (hx, hy - r * flat)
            if self.DOWN + 0.15 < t < 8.2:
                _stars(img, hx, hy - 6, t, r=12)
        if self.LAUNCH + 0.05 <= t < self.DOWN + 0.15:     # the hat stays behind a moment, then falls
            u = t - self.LAUNCH - 0.05
            hy0 = base - self.H * 0.34 - self.H * 0.14 * 2.1
            hat = (x, min(self.G - 1, hy0 + (0 if u < 0.5 else 200 * (u - 0.5) ** 2)))
        if hat:
            ellipse(img, hat[0], hat[1], 9, 2, (.2, .2, .2))
            rect(img, hat[0] - 5, hat[1] - 8, hat[0] + 5, hat[1], (.2, .2, .2))
            rect(img, hat[0] - 5, hat[1] - 3, hat[0] + 5, hat[1] - 1, (.7, .15, .15))
        if self.LAUNCH < t < self.LAUNCH + 0.4:     # speed lines and plaster
            for k in range(-2, 3):
                line(img, x + k * 5, base - 20, x + k * 5, self.G, WHITE, w=1, a=0.6)
        if self.LAUNCH + 0.1 < t < self.LAUNCH + 1.4:
            u = t - self.LAUNCH - 0.1
            for k in range(6):
                ellipse(img, x - 8 + k * 3.2, 12 + 160 * u * u * (0.8 + 0.07 * k), 1.5, 1.5, (.85, .78, .65))
        _dust(img, x, self.G, t - self.DOWN - 0.15, spread=1.2)
        _shake(img, t - self.DOWN - 0.15, 5)
        _shake(img, t - self.LAST - 0.3, 2)


class LookDown(Show):
    """Silent: running off a cliff, and the moment you notice."""
    num, title, length = 313, "LOOK DOWN", 9.5
    TOP, CRACK, H = 62, 30, 40
    CHUNK = [(30, 62), (58, 62), (56, 70), (50, 82), (42, 96), (30, 104)]

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.98, .55, .25), (1, .8, .45), 0, 80)
        vgrad(self.bg, (.55, .25, .2), (.18, .06, .08), 80, N)
        ellipse(self.bg, 92, 52, 14, 14, (1, .95, .6))
        for x0, w, h in ((34, 16, 6), (64, 10, 4)):
            rect(self.bg, x0, 80 - h, x0 + w, 80, (.85, .5, .4))
        poly(self.bg, [(64, 80), (128, 80), (128, 128), (60, 128), (66, 100)], (.4, .18, .14))
        poly(self.bg, [(106, 58), (128, 58), (128, 128), (100, 128), (104, 96), (100, 78)], (.75, .38, .25))
        rect(self.bg, 106, 58, N, 62, (.85, .5, .3))
        poly(self.bg, [(0, self.TOP), (self.CRACK, self.TOP), (self.CRACK, 104), (26, 128), (0, 128)], (.75, .38, .25))
        rect(self.bg, 0, self.TOP, self.CRACK, self.TOP + 4, (.85, .5, .3))
        for y in (78, 94, 112):
            line(self.bg, 2, y, 24, y + 2, (.6, .28, .18), w=1)

    def _chunk(self, img, dy):
        poly(img, [(x, y + dy) for x, y in self.CHUNK], (.75, .38, .25))
        rect(img, self.CRACK, self.TOP + dy, 58, self.TOP + 4 + dy, (.85, .5, .3))
        line(img, 36, 76 + dy, 50, 78 + dy, (.6, .28, .18), w=1)

    def draw(self, img, t):
        img[:] = self.bg
        base = self.TOP - LEG * self.H
        x, y, walk, look, mood, arms, flat = 82.0, base, 0.0, (1, 0), 0, (0.3, 0.3), 1.0
        dy = 0.0
        if t < 1.0:
            x, walk = -10 + 50 * t, 2.0
        elif t < 1.7:
            x, walk = 40 + 42 * (t - 1.0) / 0.7, 2.0
        elif t < 2.1:
            walk = 2.0 * (1 - (t - 1.7) / 0.4)
        elif t < 2.6:
            look = (0, 0)
        elif t < 3.2:
            look = (0, 1)
        elif t < 3.7:
            look, mood = (0, 0), -1
        elif t < 4.2:
            look, mood, arms = (0, 0), -1, (0.3, 2.6 + 0.4 * math.sin(t * 20))
        elif t < 6.4:
            u = t - 4.2
            y, flat, look, mood = base + 600 * u * u, 1.4, (0, -1), -1
        elif t < 7.6:
            u = (t - 6.4) / 1.2
            x, y, walk, look = _lerp(82, 44, u), _lerp(150, base, u), 2.0, (-1, -1)
        elif t < 8.5:
            x, mood, look = 44, 1, (0, 0) if t < 8.2 else (0, 1)
            arms = (1.2 + 0.4 * math.sin(t * 25), 1.2 - 0.4 * math.sin(t * 25)) if t < 8.0 else (0.3, 0.3)
        else:
            u = t - 8.5
            dy = 400 * u * u
            x, y, look, mood = 44, base + dy, (0, 0), 0
        if t >= 8.2:
            for k in range(4):
                line(img, self.CRACK + (k % 2) * 2, self.TOP + k * 10 + 2, self.CRACK + ((k + 1) % 2) * 2,
                     self.TOP + k * 10 + 12, (.25, .1, .08), w=1)
        self._chunk(img, dy)
        if y < 150:
            hx, hy, r = toon(img, x, y, self.H, SKINS[1], (.85, .15, .2), t, walk=walk, arms=arms, look=look, mood=mood,
                             flat=flat, seed=11, pants=(.25, .25, .5))
            if 1.0 < t < 1.7 or 6.4 < t < 7.6:
                for k in range(3):
                    line(img, x - 14 - k * 4, y - 10 + k * 7, x - 24 - k * 4, y - 10 + k * 7, WHITE, w=1, a=0.7)
            if 2.6 < t < 3.7:
                ellipse(img, hx + r + 2, hy - r * 0.6 + ((t * 20) % 8), 1.2, 1.8, (.6, .85, 1))
        if 4.2 <= t < 4.5:                          # where he was
            _dust(img, 82, base + 10, (t - 4.2) * 2.5, spread=0.6, col=(1, .9, .8))
        u = t - 5.3
        if 0 <= u < 1:                              # far, far below
            for k in range(3):
                ellipse(img, 82 + (k - 1) * 4 * (1 + u * 3), 126 - 4 * u, 2 + 3 * u, 1.5 + 2 * u, (.85, .7, .55),
                        a=0.9 * (1 - u))


def _dog(img, x, g, d, t, walk=0.0, sit=False, look=0, ball=False, wag=1.0, col=(.95, .72, .4)):
    """A small dog, feet on row g, facing d (1 right, -1 left)."""
    by = g - 7 - (0 if not walk else abs(math.sin(t * 12)))
    lean = 0.35 if sit else 0.0
    for k, ox in enumerate((-5, -3, 3, 5)):
        sw = walk * 0.5 * math.sin(t * 12 + k * 1.6)
        if sit and ox * d < 0:
            line(img, x + d * ox, by + 2, x + d * (ox + 3), g, col, w=2)
        else:
            line(img, x + d * ox, by + 2, x + d * ox + 4 * sw, g, col, w=1.8)
    ellipse(img, x, by - (2 if sit else 0), 7, 4, col, rot=-d * lean)
    ellipse(img, x - d * 2, by - 1, 3, 2, (.75, .45, .2))
    w = math.sin(t * 18) * wag
    line(img, x - d * 6, by - 2 - (2 if sit else 0), x - d * (10 + 1 * w), by - 7 - 2 * w, col, w=1.6)
    hx, hy = x + d * 7, by - 6 - (3 if sit else 0)
    ellipse(img, hx, hy, 4, 3.6, col)
    ellipse(img, hx + d * 3.5, hy + 1, 2.6, 1.8, col)
    ellipse(img, hx + d * 5.8, hy + 0.3, 1, 1, BLACK)
    ellipse(img, hx - d * 1.8, hy - 0.5, 1.5, 3, (.6, .35, .15), rot=d * 0.3)
    ex = hx + d * 1.2 + (look * 0.8 if look else 0)
    ellipse(img, ex, hy - 1.2, 0.9, 0.9 if (t * 0.4) % 1 > 0.05 else 0.2, BLACK)
    if ball:
        ellipse(img, hx + d * 6, hy + 2.5, 2.2, 2.2, (.9, .15, .15))
    return hx + d * 5, hy + 1.5                     # its mouth


class GoodBoy(Show):
    """Silent: a small dog takes a large man for a walk."""
    num, title, length = 319, "GOOD BOY", 10.5
    G, H = 118, 104

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.4, .7, 1), (.75, .9, 1), 0, 84)
        for cx, r in ((12, 14), (40, 10), (104, 16)):
            rect(self.bg, cx - 2, 70, cx + 2, 86, (.4, .25, .15))
            ellipse(self.bg, cx, 64, r, r * 0.9, (.25, .55, .25))
        vgrad(self.bg, (.4, .75, .3), (.25, .55, .2), 84, N)
        rect(self.bg, 0, 108, N, 122, (.8, .72, .55))

    def _tree(self, img, x, y, ang=0.0):
        _sprite(img, [("r", -3, -70, 3, 0, (.45, .28, .15)), ("e", 0, 2, 9, 5, (.45, .3, .15)),
                      ("e", -12, -72, 14, 12, (.2, .55, .2)), ("e", 12, -74, 14, 12, (.25, .6, .22)),
                      ("e", 0, -86, 15, 13, (.3, .65, .25)), ("e", 4, -80, 3, 3, (.9, .2, .2)),
                      ("e", -9, -88, 3, 3, (.9, .2, .2))], x, y, ang)

    def draw(self, img, t):
        img[:] = self.bg
        base = self.G - LEG * self.H
        mx, mwalk, marms, mlook, mmood, mtalk, bob = -50.0, 0.0, (0.3, 0.3), (1, 0), 1, 0.0, 0.0
        dx, dd, dwalk, dsit, dlook, ball = 82.0, 1, 0.0, False, 0, False
        tree = None
        if t < 2.4:
            dx, dwalk = -6 + 88 * t / 2.4, 1.0
            mx, mwalk = -50 + 90 * t / 2.4, 1.0
        elif t < 3.3:
            mx, dd = 40, -1
            ball = t > 2.6 and t < 3.05
            if t > 2.6:
                bob = abs(math.sin(t * 14)) * 4
                marms, mtalk = (2.5, 2.5), 0.6
        elif t < 4.3:
            u = (t - 3.3) / 1.0
            mx, mwalk, dd, marms, mtalk = 40 + 130 * u * u, 2.0, -1 if t < 3.6 else 1, (2.2, 2.2), 0.6
        elif t < 5.8:
            mx, dsit, dlook = 999, t > 4.5, 0
        elif t < 7.0:
            u = (t - 5.8) / 1.2
            mx, mwalk, mlook, marms, mtalk, dsit = _lerp(170, 108, u), 1.0, (-1, 0), (1.4, -0.4), 0.6, True
            tree = (mx - 22, 100, 0.0)
        else:
            mx, mlook, dsit = 108, (-1, 1), True
            tree = (86, self.G - 2, 0.0)
            mtalk = 0.6 if t < 8.6 else 0.0
            if t > 9.0:
                mtalk, mmood = 0.6 * abs(math.sin(t * 10)), 1
            dd = 1
            dlook = 0 if t < 7.6 else 1
        if tree:
            self._tree(img, *tree)
        if mx < 200:
            hx, hy, r = toon(img, mx, base - bob, self.H, SKINS[4], (.95, .45, .15), t, walk=mwalk, arms=marms, look=mlook,
                             mood=mmood, talk=mtalk, seed=19, pants=(.2, .3, .55))
            neck = (mx, base - bob - self.H * 0.34 + 2)
            ellipse(img, neck[0], neck[1], 7, 2.2, (.9, .1, .2))
        mouth = _dog(img, dx, self.G - 2, dd, t, walk=dwalk, sit=dsit, look=dlook, ball=ball)
        if t < 3.05:
            if mx > -40:
                line(img, mouth[0], mouth[1], neck[0], neck[1] + 1, (.9, .1, .2), w=1.2)
        elif mx < 200:
            line(img, neck[0], neck[1] + 1, neck[0] + 4, base + 10 - bob, (.9, .1, .2), w=1.2)
        if 3.05 <= t < 3.6:                         # the ball, thrown
            u = (t - 3.05) / 0.55
            ellipse(img, _lerp(mouth[0], 140, u), mouth[1] - 60 * math.sin(math.pi * u * 0.7), 2.2, 2.2, (.9, .15, .15))
        if 7.0 <= t < 7.5:
            _dust(img, 86, self.G, (t - 7.0) * 2, spread=1.0)
        _shake(img, t - 7.0, 3)
        if 8.3 <= t < 8.9:                          # a biscuit, for a good boy
            u = (t - 8.3) / 0.6
            bx, by = _lerp(mouth[0], hx, u), _lerp(mouth[1], hy + r * 0.5, u) - 40 * math.sin(math.pi * u)
            rect(img, bx - 2, by - 1, bx + 2, by + 1, (.75, .5, .25))


def _toast(img, x, y, phi):
    """A slice of toast, edge on, jam side up at phi 0."""
    _sprite(img, [("r", -8, -2.5, 8, 2.5, (.85, .6, .3)), ("r", -8, -4.5, 8, -2.5, (.85, .08, .2)),
                  ("r", -8, 1.5, 8, 2.5, (.6, .38, .15))], x, y, phi)


class Toast(Show):
    """Silent: toast lands jam side down. Always."""
    num, title, length = 326, "JAM SIDE", 11.0
    G, H, X0 = 112, 50, 56
    SLOT = (112, 70)

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        tile = ((X // 8 + Y // 8) % 2)[..., None]
        self.bg[:] = np.array((.55, .8, .85), np.float32) * (1 - tile) + np.array((.45, .7, .78), np.float32) * tile
        rect(self.bg, 0, 0, N, 7, (.92, .9, .85))
        rect(self.bg, 0, 7, N, 8, (.7, .7, .65))
        floor = ((X // 10 + Y // 6) % 2)[..., None]
        self.bg[self.G:] = (np.array((.95, .9, .8), np.float32) * (1 - floor)
                            + np.array((.3, .3, .35), np.float32) * floor)[self.G:]
        rect(self.bg, 88, 80, N, self.G, (.55, .35, .2))
        rect(self.bg, 86, 78, N, 82, (.85, .85, .8))
        rect(self.bg, 100, 66, 124, 78, (.75, .75, .8))
        rect(self.bg, 102, 66, 122, 68, (.9, .9, .95))
        rect(self.bg, 106, 66, 118, 68, (.15, .15, .15))
        rect(self.bg, 122, 70, 126, 72, (.3, .3, .3))

    def draw(self, img, t):
        img[:] = self.bg
        base = self.G - LEG * self.H
        x, y, rot, arm, look, mood, talk, larm = self.X0, base, 0.0, 1.3, (1, 1), 0, 0.0, 0.3
        lie = (40, self.G - 5)
        if t < 0.7:
            mood = 1
        elif t < 2.0:
            look, mood = (1, 1), -1 if t > 1.15 else 0
        elif t < 2.6:
            look = (1, -1)
        elif t < 3.2:
            arm, look = _lerp(1.3, 0.2, _ease((t - 2.6) / 0.6)), (1, 1)
        elif t < 4.4:
            arm, look, mood = 0.2, (1, 1) if t < 3.7 else (0, 0), -1 if t > 3.7 else 0
        elif t < 5.0:
            look = (1, -1)
        elif t < 5.4:
            arm, look = 0.3, (0, -1)
        elif t < 6.8:
            arm, look = _lerp(0.3, 3.0, _ease((t - 5.4) / 0.15)), (0, -1)
        elif t < 7.6:
            u = _ease((t - 6.8) / 0.8)
            x, y, rot, look, arm = _lerp(self.X0, lie[0], u), _lerp(base, lie[1], u), math.pi / 2 * u, (0, -1), 0.3
        else:
            x, y, rot, arm, look = lie[0], lie[1], math.pi / 2, 0.3, (-1, 0)
            talk = 1.0 if t < 8.45 else 0.0
            if t > 8.6:
                larm, mood = math.pi / 2 + 0.2 * math.sin(t * 6), 1
        hx, hy, r = toon(img, x, y, self.H, SKINS[2], (.95, .85, .2), t, rot=rot, arms=(larm, arm), look=look, mood=mood,
                         talk=talk, seed=26, pants=(.3, .25, .45))
        px, py = hand(x, y, self.H, arm, 1, rot)
        if t < 0.7:
            _toast(img, px + 3, py - 4, 0.0)
        hx0, hy0 = hand(self.X0, base, self.H, 1.3, 1)
        u = _ramp(t, 0.7, 1.15)                     # one: dropped
        tx1 = hx0 + 3 + 6 * u
        _toast(img, tx1, _lerp(hy0 - 4, self.G - 3, u * u), math.pi * _ease(u))
        if t >= 1.15:
            ellipse(img, tx1, self.G - 1, 11, 1.6, (.85, .08, .2))
        if 2.0 <= t < 2.6:                          # pop! and caught
            u = (t - 2.0) / 0.6
            _toast(img, _lerp(self.SLOT[0], hx0 + 3, u), _lerp(self.SLOT[1], hy0 - 4, u) - 40 * math.sin(math.pi * u),
                   -math.pi / 2 * (1 - u))
        elif 2.6 <= t < 3.2:
            _toast(img, px + 3, py - 4, 0.0)
        lo = hand(self.X0, base, self.H, 0.2, 1)
        if t >= 3.2:                                # two: lowered carefully, let go
            u = _ramp(t, 3.2, 3.45)
            _toast(img, lo[0] + 3 + 3 * u, _lerp(lo[1] - 4, self.G - 3, u * u), 3 * math.pi * u)
            if u >= 1:
                ellipse(img, lo[0] + 6, self.G - 1, 11, 1.6, (.85, .08, .2))
        if 4.4 <= t < 5.0:
            u = (t - 4.4) / 0.6
            _toast(img, _lerp(self.SLOT[0], hx0 + 3, u), _lerp(self.SLOT[1], hy0 - 4, u) - 40 * math.sin(math.pi * u),
                   -math.pi / 2 * (1 - u))
        elif 5.0 <= t < 5.45:
            _toast(img, px + 3, py - 4, 0.0)
        elif 5.45 <= t < 5.9:                       # three: thrown up, and it lands jam first, on the ceiling
            u = (t - 5.45) / 0.45
            _toast(img, _lerp(px + 3, 64, u), _lerp(py - 4, 12, 1 - (1 - u) ** 2), 4 * math.pi * u)
        elif 5.9 <= t < 8.0:
            _toast(img, 64, 12, 0.06 * math.sin(t * 40) if t > 7.6 else 0.0)
        elif t >= 8.0:
            u = _ramp(t, 8.0, 8.45)
            if u < 1:
                _toast(img, 64, _lerp(12, hy - r - 4, u * u), math.pi * _ease(u))
            else:
                _toast(img, hx, hy - r - 4 + math.sin(t * 14), math.pi)
                ellipse(img, hx + 5, hy - r + 1, 1.2, 2 + ((t * 2) % 1) * 3, (.85, .08, .2))
        if 5.9 <= t < 6.4:
            _dust(img, 64, 14, (t - 5.9) * 2, n=4, spread=0.5, col=(.95, .93, .85))
        for t0, dx in ((1.15, tx1), (3.45, lo[0] + 6)):
            if 0 <= t - t0 < 0.3:
                for k in range(5):
                    a = math.pi * (0.1 + 0.2 * k)
                    v = (t - t0) * 60
                    ellipse(img, dx - math.cos(a) * v, self.G - 2 - math.sin(a) * v * 0.6, 1.3, 1.3, (.85, .08, .2))


_BARN = [("r", -14, -22, 14, 0, (.8, .15, .12)), ("p", [(-17, -22), (0, -34), (17, -22)], (.5, .1, .1)),
         ("r", -5, -13, 5, 0, (.35, .08, .06)), ("l", -5, -13, 5, 0, 1, (.95, .9, .8)), ("l", 5, -13, -5, 0, 1, (.95, .9, .8)),
         ("r", -3, -29, 3, -24, (.95, .9, .8))]
_TREE = [("r", -2, -18, 2, 0, (.45, .28, .15)), ("e", 0, -26, 11, 10, (.2, .6, .25)), ("e", -7, -19, 7, 6, (.25, .65, .25)),
         ("e", 7, -20, 7, 6, (.22, .55, .22))]
_SUN = [("e", 0, 0, 10, 10, (1, .85, .2)), ("e", -3, -2, 1.3, 1.6, BLACK), ("e", 3, -2, 1.3, 1.6, BLACK),
        ("l", -3, 3, 3, 3, 1, (.6, .3, .1))]
_CLOUD = [("e", -7, 0, 7, 4.5, (.97, .97, 1)), ("e", 3, -3, 8, 5.5, (.97, .97, 1)), ("e", 10, 1, 6, 3.5, (.97, .97, 1))]


class Sneeze(Show):
    """Silent: a flower, a sneeze, and a world that doesn't come back quite right."""
    num, title, length = 332, "BLESS YOU", 9.5
    G, H, X0, HOR = 116, 48, 40, 86
    AT = 3.1                                        # the sneeze
    BACK = 6.2                                      # the world comes back
    # (sprite, where, where it is when it comes back, flipped then)
    THINGS = [(_SUN, (24, 22), (104, 92), 1), (_CLOUD, (70, 24), (60, 98), 1), (_CLOUD, (106, 42), (16, 30), -1),
              (_BARN, (98, 88), (98, 54), -1), (_TREE, (64, 88), (70, 64), -1)]

    def __init__(self):
        self.world = np.empty((N, N, 3), np.float32)
        vgrad(self.world, (.35, .65, 1), (.75, .9, 1), 0, self.HOR)
        vgrad(self.world, (.45, .8, .3), (.25, .6, .2), self.HOR, N)
        rng = np.random.default_rng(332)
        for _ in range(16):
            x, y = rng.uniform(0, N), rng.uniform(self.HOR + 6, N)
            ellipse(self.world, x, y, 1.6, 1.6, [(1, .4, .6), (1, .9, .3), (1, 1, 1)][int(rng.integers(3))])
        self.void = np.empty((N, N, 3), np.float32)
        vgrad(self.void, (.02, .02, .08), (.05, .02, .15))
        grid = ((X % 16 < 1) | (Y % 16 < 1))[..., None]
        self.void[:] = np.where(grid, np.array((.1, .6, .7), np.float32), self.void)

    def _gust(self, t):
        """How far the sneeze has blown the world to the right (negative: coming back from the left)."""
        if t < self.AT:
            return 0.0
        if t < self.BACK:
            u = t - self.AT
            return 260 * u * u + 30 * u
        return -(N + 60) * (1 - _ease((t - self.BACK) / 1.0))

    def draw(self, img, t):
        off = self._gust(t)
        k = int(min(N, abs(off)))
        if off >= 0:
            img[:, k:] = self.world[:, :N - k]
            img[:, :k] = self.void[:, :k]
        else:
            img[:, :N - k] = self.world[:, k:]
            img[:, N - k:] = self.void[:, N - k:]
        wrong = t >= self.BACK
        for i, (spr, (x, y), (wx, wy), flip) in enumerate(self.THINGS):
            if wrong:
                _sprite(img, spr, wx + off, wy, sy=flip)
            else:
                d = max(0.0, self._gust(t - (x - self.X0) / 500))
                if d < 200:
                    _sprite(img, spr, x + d, y - d * 0.1 * (i % 3), ang=d * 0.012 * (1 if i % 2 else -1))
        base = self.G - LEG * self.H
        rot, look, mood, talk, arms = 0.0, (1, -1), 1, 0.0, (0.3, 2.6)
        if 1.0 <= t < 1.6:
            rot, talk, mood = -0.15 * _ease((t - 1.0) / 0.3), 0.3, 0
        elif 2.0 <= t < self.AT:
            rot, talk, mood = -0.3 * _ease((t - 2.0) / 0.6) + 0.02 * math.sin(t * 50), 0.5, 0
        elif self.AT <= t < self.AT + 0.6:
            u = t - self.AT
            rot, talk, mood, arms = 0.4 * math.exp(-u * 4), 0.0, 0, (1.2, 2.4)
        elif t >= self.AT + 0.6:
            look = ((-1, 0) if (t * 1.2) % 2 < 1 else (1, 0)) if t < self.BACK + 1.0 else (0, 0)
            mood, arms = -1 if t > self.BACK + 1.0 else 0, (0.3, 2.0)
            if t > self.BACK + 2.0:
                rot, talk = -0.12 * _ease((t - self.BACK - 2.0) / 0.4), 0.3
        hx, hy, r = toon(img, self.X0, base, self.H, (.95, .7, .55), (.55, .3, .85), t, rot=rot, arms=arms, look=look,
                         mood=mood, talk=talk, seed=32, pants=(.2, .35, .3))
        fx, fy = hand(self.X0, base, self.H, arms[1], 1, rot)
        line(img, fx, fy, fx + 3, fy - 8, (.2, .55, .2), w=1.2)
        if t < self.AT:
            for k in range(5):
                a = k * 2 * math.pi / 5 + t
                ellipse(img, fx + 3 + 2.6 * math.cos(a), fy - 9 + 2.6 * math.sin(a), 1.8, 1.8, (1, .4, .65))
            ellipse(img, fx + 3, fy - 9, 1.4, 1.4, (1, .9, .2))
        u = t - self.AT
        if 0 <= u < 0.6:                            # a-CHOO
            for k in range(14):
                a = (k * 0.47) % 1.2 - 0.6
                v = u * (90 + 30 * (k % 3))
                ellipse(img, hx + r + v * math.cos(a), hy + r * 0.4 + v * math.sin(a), 1.2, 1.2, (.75, .95, 1),
                        a=1 - u / 0.6)
            for k in range(5):                      # the petals go too
                ellipse(img, fx + 3 + u * 120 + k * 6, fy - 9 - k * 3 + u * 20 * k, 1.8, 1.8, (1, .4, .65))
            for k in range(4):
                y = 20 + k * 22
                line(img, 60 + u * 100, y, 90 + u * 160, y + 2, WHITE, w=1, a=0.7)


_SAFE = [("r", -12, -24, 12, 0, (.3, .32, .35)), ("r", -10, -22, 10, -2, (.42, .44, .48)), ("e", 3, -12, 4.5, 4.5, (.8, .78, .7)),
         ("e", 3, -12, 1.4, 1.4, (.2, .2, .2)), ("l", -7, -16, -7, -8, 1.8, (.8, .78, .7))]
_ANVIL = [("p", [(-16, -16), (16, -16), (12, -11), (6, -10), (8, 0), (-8, 0), (-6, -10), (-10, -11)], (.28, .28, .33)),
          ("p", [(-15, -16), (-27, -15), (-15, -11)], (.28, .28, .33)), ("l", -14, -15, 14, -15, 1, (.55, .55, .6))]
_W, _K, _PINK = (.97, .95, .9), (.08, .08, .08), (1, .6, .65)
_COW = [("r", -14, -10, -10, 0, _W), ("r", -6, -10, -2, 0, _W), ("r", 5, -10, 9, 0, _W), ("r", 12, -10, 16, 0, _W),
        ("l", -17, -21, -21, -9, 1.2, _W), ("e", 0, -18, 19, 10, _W), ("e", -7, -20, 5, 4, _K), ("e", 8, -14, 4, 3, _K),
        ("e", -14, -14, 3, 3, _K), ("e", 3, -8, 4, 2.5, _PINK), ("l", 16, -31, 13, -36, 1.6, (.9, .85, .6)),
        ("l", 22, -31, 25, -36, 1.6, (.9, .85, .6)), ("e", 19, -26, 7, 6.5, _W), ("e", 13, -29, 3.5, 1.6, _W),
        ("e", 24, -22, 5, 3.2, _PINK), ("e", 23, -22, 0.8, 0.8, _K), ("e", 26, -22, 0.8, 0.8, _K),
        ("e", 17, -28, 1.4, 1.6, _K), ("e", 22, -28, 1.4, 1.6, _K)]


class HeadsUp(Show):
    """Silent: a man dodges a safe, an anvil and a cow, and doesn't dodge a feather."""
    num, title, length = 338, "HEADS UP", 10.5
    G, H = 116, 46
    # (lands at, where, what, half-width of its shadow)
    DROPS = [(1.9, 50, _SAFE, 13), (4.2, 76, _ANVIL, 16), (6.2, 96, _COW, 30)]
    FEATHER = 8.6

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.25, .7, 1), (.7, .92, 1), 0, 70)
        vgrad(self.bg, (.1, .45, .8), (.2, .6, .85), 70, 86)
        for y in (74, 80):
            line(self.bg, 0, y, N, y, (.6, .85, 1), w=1, a=0.5)
        vgrad(self.bg, (.98, .88, .6), (.9, .75, .45), 86, N)
        line(self.bg, 10, 60, 10, 112, (.9, .9, .9), w=1.5)
        for k in range(4):
            poly(self.bg, [(10, 52), (-8 + k * 9, 62), (1 + k * 9, 62)], [(1, .3, .3), (1, 1, 1)][k % 2])

    def _fall(self, t, t0):
        """Where the bottom of something dropped is, landing at t0."""
        u = _cl(1 - (t0 - t) / 0.4)
        return self.G - 300 * (1 - u) ** 2

    def draw(self, img, t):
        img[:] = self.bg
        for t0, x, spr, w in self.DROPS:            # shadows, then the things
            if t0 - 1.3 < t < t0:
                u = (t - t0 + 1.3) / 1.3
                ellipse(img, x, self.G + 1, 2 + w * u, 1 + 2.5 * u, (.45, .35, .2), a=0.6)
        if self.FEATHER - 1.4 < t < self.FEATHER:
            ellipse(img, 18, self.G + 1, 2.5, 1, (.45, .35, .2), a=0.6)
        for t0, x, spr, w in self.DROPS:
            if t > t0 - 0.4:
                y = self._fall(t, t0)
                squash = 1 - 0.25 * math.exp(-(t - t0) * 12) if t > t0 else 1.0
                _sprite(img, spr, x, y, sy=squash)
        x, walk, look, mood, arms, flat = 50.0, 0.0, (0, 0), 1, (0.3, 0.3), 1.0
        steps = [(1.4, 1.65, 50, 76), (3.7, 3.95, 76, 102), (5.45, 5.9, 102, 18)]
        for a, b, x0, x1 in steps:
            if t >= a:
                x = _lerp(x0, x1, _ramp(t, a, b))
                if t < b:
                    walk = 2.0 if x1 < x0 else 1.0
        looks = [(0.9, (0, 1)), (1.2, (0, -1)), (1.4, (1, 0)), (1.9, (0, 0)), (3.4, (0, 1)), (3.6, (0, -1)), (3.7, (1, 0)),
                 (4.2, (0, 0)), (5.2, (0, -1)), (5.45, (-1, 0)), (6.2, (0, 0)), (7.3, (0, 1)), (7.6, (0, -1)), (8.0, (0, 0))]
        for t0, lk in looks:
            if t >= t0:
                look = lk
        if 5.2 < t < 5.9:
            arms, mood = (2.6 + 0.4 * math.sin(t * 30), 2.6 - 0.4 * math.sin(t * 30)), -1
        elif 7.9 < t < self.FEATHER:
            arms = (1.4, 1.4)
        if t >= self.FEATHER:
            flat, mood, look = 0.16, -1, (0, 0)
        hx, hy, r = toon(img, x, self.G - LEG * self.H * flat, self.H, SKINS[0], (1, .4, .6), t, walk=walk, arms=arms,
                         look=look, mood=mood, flat=flat, seed=38, pants=(.1, .6, .6))
        if t < self.FEATHER:                        # shades
            rect(img, hx - r * 0.75, hy - r * 0.35, hx + r * 0.75, hy - r * 0.05, (.05, .05, .1))
        if t > self.FEATHER - 1.4:
            u = _cl((t - self.FEATHER + 1.4) / 1.4)
            top = hy - r * 1.1 * flat
            fy = _lerp(-8, top - 2, u)
            fx = x + 8 * math.sin(t * 3.5) * (1 - u) if t < self.FEATHER else x + 2
            ang = 0.5 * math.cos(t * 3.5) * (1 - u) if t < self.FEATHER else 0.1
            _sprite(img, [("e", 0, 0, 7, 2, (.98, .98, 1)), ("l", -8, 0, 7, 0, 0.8, (.7, .7, .75))], fx, fy, ang)
        if t > self.FEATHER:
            _stars(img, x, self.G - 6, t, r=12)
        if t > 6.3:                                 # the cow, chewing
            ellipse(img, 120, self.G - 21 + math.sin(t * 9), 3, 1.2, _PINK)
        for t0, xd, _, w in self.DROPS:
            _dust(img, xd, self.G, (t - t0) * 1.4, spread=w / 15)
        _shake(img, t - 1.9, 3)
        _shake(img, t - 4.2, 3)
        _shake(img, t - 6.2, 5)
        _shake(img, t - self.FEATHER, 6)
        _dust(img, x, self.G, (t - self.FEATHER) * 1.2, spread=1.4)


def _cat(img, x, y, t, look=(0.0, 0.0), paw=None, blink=False):
    """A ginger cat sitting with its feet at (x, y); paw is a point to reach for, or None."""
    fur, belly = (1, .55, .15), (1, .88, .7)
    sw = math.sin(t * 2.2)
    pts = [(x - 9, y - 3), (x - 17, y - 5), (x - 22 - 2 * sw, y - 13), (x - 20 - 4 * sw, y - 22)]
    for p, q in zip(pts, pts[1:]):
        line(img, *p, *q, fur, w=3.2)
    ellipse(img, x, y - 12, 11, 12, fur)
    ellipse(img, x, y - 9, 6, 8, belly)
    for k in (-1, 1):
        ellipse(img, x + 4 * k, y - 1.5, 3, 2, belly)
    hy = y - 29
    for k in (-1, 1):
        poly(img, [(x + 9 * k, hy - 3), (x + 7 * k, hy - 13), (x + 2 * k, hy - 7)], fur)
        poly(img, [(x + 7.5 * k, hy - 4), (x + 6.6 * k, hy - 10), (x + 4 * k, hy - 6.5)], (1, .6, .6))
    ellipse(img, x, hy, 10.5, 8.5, fur)
    for k in (-1, 1):
        ex = x + 4.2 * k
        if blink:
            line(img, ex - 2.4, hy - 1, ex + 2.4, hy - 1, _K, w=1)
        else:
            ellipse(img, ex, hy - 1, 2.7, 2.9, (.7, .95, .25))
            ellipse(img, ex + look[0] * 1.1, hy - 1 + look[1] * 0.8, 0.8, 2.4, _K)
        for j in (-1, 1):
            line(img, x + 5 * k, hy + 3, x + 13 * k, hy + 3 + 2 * j, (1, 1, .9), w=0.8, a=0.8)
    poly(img, [(x - 1.6, hy + 1.6), (x + 1.6, hy + 1.6), (x, hy + 3)], (1, .45, .55))
    line(img, x, hy + 3, x - 2, hy + 5, (.4, .15, .1), w=0.8)
    line(img, x, hy + 3, x + 2, hy + 5, (.4, .15, .1), w=0.8)
    if paw is not None:
        sx = x + (6 if paw[0] > x else -6)
        line(img, sx, y - 16, paw[0], paw[1], fur, w=4)
        ellipse(img, paw[0], paw[1], 3, 2.6, belly)


class Cat(Show):
    """Silent: a cat, a table, and everything on it, one thing at a time. Then the camera."""
    num, title, length = 345, "CAT TV", 11.0
    TOP, G, CX, L, R = 72, 118, 64, 24, 104
    # (start reaching, start falling, where, which side)
    PUSH = [(0.8, 1.7, 96, 1), (2.3, 3.2, 34, -1), (3.9, 4.6, 86, 1)]
    PAWCAM, DROP = 6.2, 7.0

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        stripe = (0.04 * np.sin(X * 0.9))[..., None]
        self.bg[:] = np.array((.15, .55, .55), np.float32) + stripe
        boards = (Y // 5 % 2)[..., None] * 0.05
        self.bg[self.G:] = (np.array((.55, .35, .2), np.float32) + boards)[self.G:]
        rect(self.bg, 8, 14, 36, 40, (.85, .7, .3))
        rect(self.bg, 10, 16, 34, 38, (.95, .85, .6))
        ellipse(self.bg, 22, 27, 6, 7, (.3, .3, .5))
        rect(self.bg, self.L, self.TOP, self.R, self.TOP + 4, (.45, .25, .12))
        for lx in (self.L + 3, self.R - 6):
            rect(self.bg, lx, self.TOP + 4, lx + 3, self.G, (.4, .22, .1))

    def _thing(self, img, i, x, y, ang):
        if i == 0:
            _sprite(img, [("e", 6, -5, 3.5, 3.5, (.95, .4, .5)), ("e", 6, -5, 1.8, 1.8, (.15, .55, .55)),
                          ("r", -5, -11, 5, 0, (.95, .4, .5)), ("r", -4, -11, 4, -9, (.35, .2, .1))], x, y, ang)
        elif i == 1:
            _sprite(img, [("l", 0, -16, -4, -26, 1, (.2, .6, .2)), ("l", 0, -16, 4, -24, 1, (.2, .6, .2)),
                          ("e", -4, -27, 3, 3, (1, .9, .2)), ("e", 4, -25, 3, 3, (.95, .3, .7)),
                          ("e", 0, -7, 6, 7, (.3, .45, .95)), ("r", -2, -17, 2, -12, (.3, .45, .95))], x, y, ang)

    def _scene(self, img, t, final=False):
        img[:] = self.bg
        paw, look, blink = None, (0, 0), False
        for i, (tr, tf, x0, d) in enumerate(self.PUSH):
            edge = self.R + 4 if d > 0 else self.L - 4
            if t < tr:
                x, y, ang = x0, self.TOP, 0.0
            elif t < tf:
                u = _ease((t - tr) / (tf - tr))
                x, y, ang = x0 + (edge - x0) * max(0.0, (u - 0.5) * 2), self.TOP, 0.0
                paw = (_lerp(self.CX + 8 * d, x - 5 * d, min(1.0, u * 2)), self.TOP - 6)
            else:
                u = _cl((t - tf) / 0.35)
                x, y, ang = edge + 6 * d * u, _lerp(self.TOP, self.G, u * u), 1.4 * d * u
                if t < tf + 0.4:
                    paw = (edge - 5 * d, self.TOP - 6)
            if i < 2:
                if t < tf + 0.35:
                    self._thing(img, i, x, y, ang)
                else:
                    v = min(1.0, t - tf - 0.35)
                    col = (.95, .4, .5) if i == 0 else (.3, .45, .95)
                    for k in range(5):
                        sx = edge + 6 * d + (k - 2) * 7 * v * 2
                        ellipse(img, sx, self.G - 1.5 - 10 * math.sin(math.pi * v) * (k % 2), 2, 1.5, col)
            else:                                   # a tiny man, who objects
                h = 22
                if t < tf:
                    bx, by, rot = x, self.TOP - LEG * h, 0.0
                    arms = (0.3, 2.7 + 0.3 * math.sin(t * 20)) if 3.4 < t < tr + 0.5 else (0.3, 0.3)
                    lk = ((-1, 0) if (t * 4) % 2 < 1 else (1, 0)) if 3.4 < t < tr + 0.5 else (-1, 0)
                    toon(img, bx, by, h, SKINS[1], (.3, .3, .35), t, rot=rot, arms=arms, look=lk, mood=-1, seed=45)
                else:
                    u = _cl((t - tf) / 0.4)
                    bx, by = edge + 8 * u, _lerp(self.TOP - LEG * h, self.G - 3, u * u)
                    hx, hy, r = toon(img, bx, by, h, SKINS[1], (.3, .3, .35), t, rot=math.pi / 2 * u + 2 * math.pi * u,
                                     arms=(2.5, 2.5), look=(0, 0), mood=-1, seed=45)
                    if u >= 1:
                        _stars(img, hx, hy - 4, t, r=6, s=1.8)
        if self.PAWCAM - 0.8 < t < self.PAWCAM:
            look = (-1, 0) if t < self.PAWCAM - 0.4 else (1, 0)
        if final:
            blink = (t % 2.6) < 0.35
            if t > 9.4:
                paw = (self.CX + 2, self.TOP - 28 + 2 * math.sin(t * 12))
        _cat(img, self.CX, self.TOP, t, look=look, paw=paw, blink=blink)

    def draw(self, img, t):
        if t < self.DROP:
            self._scene(img, t)
            if t > self.PAWCAM:                     # the paw, coming for the lens
                u = _ease((t - self.PAWCAM) / (self.DROP - self.PAWCAM))
                px, py, r = _lerp(self.CX + 8, 64, u), _lerp(56, 64, u), _lerp(4, 80, u * u)
                ellipse(img, px, py, r, r * 0.9, (1, .88, .7))
                for k in (-1.5, -0.5, 0.5, 1.5):
                    ellipse(img, px + k * r * 0.4, py - r * (0.55 - 0.15 * abs(k)), r * 0.16, r * 0.2, (1, .55, .6))
                ellipse(img, px, py + r * 0.15, r * 0.35, r * 0.28, (1, .55, .6))
            return
        if t < self.DROP + 0.35:                    # the camera goes over
            self._scene(img, self.DROP)
            k = int(N * ((t - self.DROP) / 0.35) ** 2)
            if k:
                img[k:] = img[:N - k].copy()
                img[:k] = 0
            return
        self._scene(img, t, final=True)
        img[:] = np.rot90(img).copy()
        for a, n in ((0.3, 3), (1.9, 2), (3.5, 3), (4.8, 2)):        # and the lens cracked
            x, y = 96.0, 30.0
            for j in range(n):
                nx, ny = x + 12 * math.cos(a + 0.4 * (j % 2 - 0.5)), y + 12 * math.sin(a + 0.4 * (j % 2 - 0.5))
                line(img, x, y, nx, ny, WHITE, w=1, a=0.7)
                x, y = nx, ny
        _shake(img, t - self.DROP - 0.35, 5)


_ALU, _WEB, _WEB2 = (.8, .82, .85), (.15, .7, .4), (.95, .95, .85)


def _bundle(img, x, y, ang=0.0):
    """A folded lawn chair."""
    _sprite(img, [("r", -13, -3, 13, 3, _ALU), ("r", -11, -2, 11, 2, _WEB), ("r", -5, -2, -2, 2, _WEB2),
                  ("r", 3, -2, 6, 2, _WEB2)], x, y, ang)


def _chair(img, px, py, ground, back=-0.35, step=0.0):
    """A folding lawn chair in profile, facing right: its back hinge at (px, py), feet on row ground.
    back is the backrest's tilt from upright (forwards positive: about 1.4 shuts it); step swings the legs."""
    bx, by = px + 22 * math.sin(back), py - 22 * math.cos(back)
    line(img, px, py, px - 3 + step, ground, _ALU, w=1.6)
    line(img, px + 18, py, px + 20 - step, ground, _ALU, w=1.6)
    line(img, px, py, bx, by, _WEB, w=3.5)
    for f in (0.3, 0.7):
        line(img, px + (bx - px) * f, py + (by - py) * f, px + (bx - px) * (f + 0.12), py + (by - py) * (f + 0.12), _WEB2, w=3.5)
    line(img, px, py, px + 18, py, _WEB, w=3.5)
    line(img, px + 7, py, px + 11, py, _WEB2, w=3.5)
    if back < 0.5:
        line(img, px + 2, py - 8, px + 17, py - 8, _ALU, w=1.4)
        line(img, px + 17, py - 8, px + 18, py, _ALU, w=1.4)


class LawnChair(Show):
    """Silent: a man against a folding lawn chair. The chair wins, then leaves with him."""
    num, title, length = 351, "SIT BACK", 11.0
    G, H, CX, SEAT = 114, 46, 58, 10

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.45, .78, 1), (.8, .93, 1), 0, 84)
        rect(self.bg, 0, 60, N, 84, (.25, .5, .25))
        for x in range(0, N, 12):
            ellipse(self.bg, x + 4, 62, 9, 7, (.2, .45, .2))
        vgrad(self.bg, (.4, .78, .3), (.25, .6, .2), 84, N)
        ellipse(self.bg, 104, 18, 9, 9, (1, .95, .55))
        ellipse(self.bg, 22, 124, 18, 3, (.3, .65, .25))

    def draw(self, img, t):
        img[:] = self.bg
        base = self.G - LEG * self.H
        py = self.G - self.SEAT
        px, back = self.CX, -0.35
        man = dict(x=63.0, y=base, thigh=0.0, arms=(0.3, 0.3), look=(1, 0), mood=0, walk=0.0)
        chair = "open"
        sit = (self.CX + 5, py - 2)
        if t < 1.5:
            chair = "carried"
            man.update(x=_lerp(-10, 34, _cl(t / 1.2)), walk=1.0 if t < 1.2 else 0.0, arms=(0.3, 0.3 if t < 1.2 else 1.6))
        elif t < 1.8:
            man.update(x=34, look=(1, 1))
        elif t < 2.2:
            man.update(x=_lerp(34, sit[0], (t - 1.8) / 0.4), walk=1.0)
        elif t < 3.0:
            u = _ease((t - 2.2) / 0.4)
            man.update(x=sit[0], y=_lerp(base, sit[1], u), thigh=math.pi / 2 * u, arms=(2.8, 2.8) if t > 2.6 else (0.6, 0.6),
                       mood=1 if t > 2.6 else 0, look=(0, 0))
        elif t < 5.0:
            chair = "shut"
            back = _lerp(-0.35, 1.45, _cl((t - 3.0) / 0.12))
            man.update(x=sit[0], y=sit[1], thigh=math.pi / 2, arms=(2.8, 2.8), look=(0, -1), mood=-1)
        elif t < 7.0:
            man.update(x=sit[0], look=(1, 1) if t > 6.2 else (0, 0), mood=-1,
                       arms=(0.3, 1.5) if 6.5 < t < 6.9 else (0.3, 0.3))
            if t < 5.4:
                man.update(y=base - 16 * math.sin(math.pi * (t - 5.0) / 0.4), arms=(2.6, 2.6))
            chair = "away" if t < 6.2 else "open"
        elif t < 8.4:
            u = _ease((t - 7.0) / 0.4)
            man.update(x=sit[0], y=_lerp(base, sit[1], u), thigh=math.pi / 2 * u, look=(0, 0),
                       arms=(2.8, 2.8) if t > 7.5 else (0.6, 0.6), mood=1 if t > 7.5 else 0)
        else:
            u = _ease((t - 8.4) / 0.5)
            lift = 22 * u
            walk = max(0.0, t - 8.9)
            px = self.CX + 38 * walk * walk + 10 * walk
            man.update(x=px + 5, y=sit[1] - lift, thigh=math.pi / 2, arms=(0.3, 0.3), look=(0, 0) if t < 9.6 else (-1, 0))
            py = self.G - self.SEAT - lift
        if chair == "carried":
            if t < 1.2:
                hx, hy = hand(man["x"], base, self.H, 0.3, 1)
                _bundle(img, hx + 2, hy, 0.0)
            else:
                u = (t - 1.2) / 0.3
                _bundle(img, _lerp(hand(34, base, self.H, 1.6, 1)[0], self.CX + 9, u), _lerp(base - 14, self.G - 3, u) -
                        14 * math.sin(math.pi * u), u * 3)
        elif chair == "away":
            u = t - 5.0
            if u < 0.5:
                _bundle(img, self.CX + 9 + 60 * u, self.G - 20 - 300 * u, u * 20)
        elif chair != "shut" or t < 3.12:
            step = 5 * math.sin(t * 12) if t > 8.9 else 0.0
            bounce = 3 * math.sin(math.pi * _cl((t - 1.5) / 0.25)) if t < 2.0 else 0.0
            if 5.9 < t < 6.2:
                u = (t - 5.9) / 0.3
                py = self.G - self.SEAT - 140 * (1 - u * u)
            _chair(img, px, py - bounce, self.G, back if chair == "shut" else -0.35, step)
        if chair == "shut" and t >= 3.12:           # shut, with him in it
            hop = abs(math.sin((t - 3.12) * 7)) * 6 if t > 3.5 else 0.0
            ox = 6 * math.sin((t - 3.12) * 3.5) if t > 3.5 else 0.0
            for k in (-1, 1):
                kx, ky = sit[0] + ox + 9 + k * 2, sit[1] - hop
                line(img, kx, ky, kx + 6 * math.sin(t * 20 + k), ky + 10, (.2, .2, .35), w=4)
            _sprite(img, [("r", -14, -16, 14, 16, _ALU), ("r", -12, -14, 12, 14, _WEB), ("r", -12, -6, 12, -2, _WEB2),
                          ("r", -12, 4, 12, 8, _WEB2)], sit[0] + ox, sit[1] - 12 - hop, 0.15 * math.sin(t * 6))
        else:
            if man["thigh"]:
                hx, hy, r = _figure(img, man["x"], man["y"], self.H, SKINS[5], (.95, .3, .2), t, d=1, thigh=man["thigh"],
                                    arms=man["arms"], look=man["look"], mood=man["mood"], seed=51)
            else:
                hx, hy, r = toon(img, man["x"], man["y"], self.H, SKINS[5], (.95, .3, .2), t, walk=man["walk"],
                                 arms=man["arms"], look=man["look"], mood=man["mood"], seed=51)
            if 5.0 < t < 6.2:
                _stars(img, hx, hy - r - 2, t)
        if 1.5 <= t < 2.0:
            _dust(img, self.CX + 9, self.G, (t - 1.5) * 2, spread=0.8)
        if 6.2 <= t < 6.7:
            _dust(img, self.CX + 9, self.G, (t - 6.2) * 2, spread=1.0)
        _shake(img, t - 6.2, 3)
        _shake(img, t - 3.12, 2)


_PINKY = (1, .45, .72)


class Taffy(Show):
    """Silent: a man pulls taffy so far it comes back round the world."""
    num, title, length = 358, "TAFFY PULL", 10.0
    G, H, HOOK = 114, 50, (103, 70)
    LET = 6.4

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        s = ((X // 6) % 2)[..., None]
        self.bg[:] = np.array((1, .82, .88), np.float32) * (1 - s) + np.array((.95, .55, .7), np.float32) * s
        rect(self.bg, 0, 0, N, 22, (.45, .2, .35))
        for k, col in enumerate(((1, .3, .3), (.3, .8, 1), (1, .85, .2), (.5, 1, .5))):
            rect(self.bg, 6 + k * 16, 8, 18 + k * 16, 20, (.85, .95, 1))
            for j in range(4):
                ellipse(self.bg, 9 + k * 16 + (j % 2) * 5, 17 - j * 2, 2.2, 2.2, col)
        rect(self.bg, 0, self.G, N, N, (.35, .2, .3))
        rect(self.bg, 108, 30, 113, self.G, (.6, .4, .25))
        line(self.bg, 108, self.HOOK[1] - 6, self.HOOK[0], self.HOOK[1] - 6, (.6, .6, .65), w=1.5)
        line(self.bg, self.HOOK[0], self.HOOK[1] - 6, self.HOOK[0], self.HOOK[1], (.6, .6, .65), w=1.5)

    def _strand(self, img, x0, y0, x1, y1, t, sag=1.0):
        w = max(1.6, 6 - abs(x1 - x0) / 25)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2 + sag * (3 + 2 * math.sin(t * 7))
        line(img, x0, y0, mx, my, _PINKY, w=w)
        line(img, mx, my, x1, y1, _PINKY, w=w)

    def draw(self, img, t):
        img[:] = self.bg
        base = self.G - LEG * self.H
        hk = self.HOOK
        x, walk, look, mood, arm = 80.0, 0.0, (1, 0), 0, 1.5
        if t < 0.8:
            look, mood = (1, -1), 1
        elif t < 2.8:
            x, walk = _lerp(80, -30, (t - 0.8) / 2.0), 1.0
        elif t < 3.6:
            x = -99
        elif t < 5.2:
            x, walk, look = _lerp(150, 64, (t - 3.6) / 1.6), 1.0, (-1, 0)
        elif t < self.LET:
            x = 64
            look, mood = ((1, 0), 0) if t < 5.6 else ((-1, 0), 0) if t < 6.0 else ((0, 0), -1)
        else:
            x, arm = 64, 0.3
        hx, hy = hand(x, base, self.H, arm, 1)
        if t < 2.8:
            self._strand(img, hk[0], hk[1], hx, hy, t)
        elif t < self.LET:
            self._strand(img, hk[0], hk[1], -2, 79, t, sag=2.0)
            if t >= 3.6:
                self._strand(img, N + 2, hy, hx, hy, t)
        ellipse(img, hk[0], hk[1] + 2, 4, 3.5, _PINKY)
        if t >= self.LET:                           # SNAP: home it comes, the long way round
            v = _cl((t - self.LET) / 0.5)
            if v < 1:
                self._strand(img, _lerp(-2, hk[0], v), _lerp(79, hk[1], v), hk[0], hk[1], t, sag=0)
                self._strand(img, _lerp(N + 2, x + 6, v), 79, x + 6, 79, t, sag=0)
        if x > -60:
            hop, fall = 0.0, 0.0
            if t >= self.LET + 0.6:
                hop = abs(math.sin((t - self.LET - 0.6) * 8)) * 5 if t < 8.4 else 0.0
                fall = _ease((t - 8.4) / 0.4)
            rot = -math.pi / 2 * fall
            yy = base - hop + 13 * fall
            spin = self.LET <= t < self.LET + 0.6
            hx2, hy2, r = toon(img, x, yy, self.H, SKINS[1], (.3, .55, .95), t, walk=walk, rot=rot, arms=(0.3, arm),
                               look=((-1, 0) if (t * 12) % 2 < 1 else (1, 0)) if spin else look,
                               mood=-1 if t >= self.LET else mood, seed=58, pants=(.4, .25, .2))
            if t >= self.LET:
                v = _cl((t - self.LET) / 0.6)
                c, s = math.cos(rot), math.sin(rot)

                def at(dx, dy):
                    return x + dx * c - dy * s, yy + dx * s + dy * c

                if v < 1:
                    for j in range(int(v * 8)):
                        dy = 18 - j * 5
                        line(img, *at(-10, dy + 2), *at(10, dy - 2), _PINKY, w=3)
                else:
                    ellipse(img, *at(0, -1), 11, 24, _PINKY, rot=rot)
                    for j in range(5):
                        line(img, *at(-10, 16 - j * 8), *at(10, 12 - j * 8), (.9, .3, .55), w=1)
                if fall >= 1:
                    _stars(img, hx2, hy2 - 4, t)
        if 8.8 < t < 9.4:
            _dust(img, 50, self.G, (t - 8.8) * 2, spread=1.2)


class Plank(Show):
    """Silent: a man with a long plank turns round, and round again, and then towards us."""
    num, title, length = 364, "LONG PLANK", 9.5
    G, H, HOR, D = 116, 48, 80, 100.0
    LONG, SHORT = 70, 22
    HITS = (-2.3, -0.84)                           # where the long end meets each passer-by

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.55, .75, .95), (.85, .9, .95), 0, self.HOR)
        rng = np.random.default_rng(364)
        x = 0
        while x < N:
            w, h = int(rng.integers(16, 28)), int(rng.integers(30, 60))
            col = [(.75, .45, .35), (.85, .75, .55), (.55, .6, .7), (.7, .55, .7)][int(rng.integers(4))]
            rect(self.bg, x, self.HOR - h, x + w - 1, self.HOR, col)
            for wy in range(self.HOR - h + 5, self.HOR - 6, 9):
                for wx in range(x + 3, x + w - 5, 7):
                    rect(self.bg, wx, wy, wx + 3, wy + 4, (.95, .9, .6) if rng.random() < 0.3 else (.3, .35, .45))
            x += w
        vgrad(self.bg, (.75, .75, .72), (.55, .55, .55), self.HOR, N)
        for k in range(-6, 8):
            line(self.bg, 64 + k * 6, self.HOR, 64 + k * 40, N + 40, (.65, .65, .62), w=1)
        self.crack = []
        for k in range(7):
            a = k * 2 * math.pi / 7 + rng.uniform(-0.3, 0.3)
            pts, r = [(0.0, 0.0)], 0.0
            for _ in range(4):
                r += rng.uniform(8, 16)
                b = a + rng.uniform(-0.35, 0.35)
                pts.append((r * math.cos(b), r * math.sin(b)))
            self.crack.append(pts)
        ts = np.linspace(0, self.length, 2000)
        psi = np.array([self._psi(t) for t in ts])
        self.hit_t = [float(ts[np.argmax(psi <= self.HITS[0])]),
                      float(ts[np.argmax((ts > 3.4) & (psi >= self.HITS[1]))])]

    def _psi(self, t):
        if t < 1.8:
            return 0.0
        if t < 3.4:
            return -math.pi * _ease((t - 1.8) / 0.8)
        if t < 5.0:
            return -math.pi * (1 - _ease((t - 3.4) / 0.8))
        if t < 6.6:
            return 1.5 * _ease((t - 5.0) / 0.35)
        return 1.5 * (1 - _ease((t - 6.6) / 0.6))

    def _cx(self, t):
        if t < 1.6:
            return _lerp(-30, 60, t / 1.6)
        if t < 7.4:
            return 60.0
        return _lerp(60, 170, (t - 7.4) / 2.0)

    def _proj(self, cx, ys, dx, z):
        s = self.D / (self.D - z)
        return 64 + (cx + dx - 64) * s, self.HOR + (ys - self.HOR) * s, s

    def _half(self, img, cx, ys, psi, length, sign):
        dx, z = sign * -length * math.cos(psi), sign * length * math.sin(psi)
        x0, y0, s0 = self._proj(cx, ys, 0, 0)
        x1, y1, s1 = self._proj(cx, ys, dx, z)
        h0, h1 = 2.5 * s0, 2.5 * s1
        poly(img, [(x0, y0 - h0), (x1, y1 - h1), (x1, y1 + h1), (x0, y0 + h0)], (.8, .6, .3))
        line(img, x0, y0 - h0 + 0.5, x1, y1 - h1 + 0.5, (.95, .78, .45), w=1)
        e = 3.5 * s1 * abs(math.sin(psi)) + 0.8
        rect(img, x1 - e, y1 - h1, x1 + e, y1 + h1, (.55, .38, .18))

    def _passer(self, img, k, t, ys):
        psi = self.HITS[k]
        ex, ey, s = self._proj(60, ys, -self.LONG * math.cos(psi), self.LONG * math.sin(psi))
        h = self.H * s
        hips = ey + 0.42 * h
        x, rot, u = ex - (4 if k == 0 else -4), 0.0, t - self.hit_t[k]
        if u > 0:
            d = 1 if k == 0 else -1
            x, hips, rot = x + d * 120 * u, hips - 70 * u + 90 * u * u, d * 9 * u
            if hips > 200:
                return
        hx, hy, r = toon(img, x, hips, h, SKINS[2 if k == 0 else 4], (.9, .8, .2) if k == 0 else (.2, .7, .65), t,
                         rot=rot, arms=(0.3, 2.0) if k else (0.3, 0.3), look=(0, 0), mood=-1 if u > 0 else 1, seed=k)
        if k == 1 and u <= 0:                       # reading the paper
            rect(img, hx - r * 1.4, hy, hx + r * 1.4, hy + r * 2, (.92, .92, .88))
        if 0 < u < 0.15:
            _bang(img, ex, ey, 6, t)

    def draw(self, img, t):
        img[:] = self.bg
        cx = self._cx(t)
        base = self.G - LEG * self.H
        ys = base - 16
        psi = self._psi(t)
        for k in (0, 1):
            self._passer(img, k, t, ys)
        front = self.LONG * math.sin(psi) > 0       # is the long end on our side of him?
        self._half(img, cx, ys, psi, *((self.SHORT, -1) if front else (self.LONG, 1)))
        look = (1, 0) if 1.8 <= t < 2.6 else (-1, 0) if 3.4 <= t < 4.2 else (0, 0)
        tip = 7.4 <= t
        toon(img, cx, base - (abs(math.sin(t * 10)) * 2 if tip else 0), self.H, SKINS[0], (.3, .3, .3), t,
             walk=1.0 if t < 1.6 or tip else 0.0, arms=(0.3, 2.8), look=look, mood=-1 if 5.3 < t < 7.4 else 0, seed=64,
             pants=(.3, .25, .2))
        if t < 1.6 or tip:                          # whistling
            ny = base - 40 - (t * 18) % 14
            ellipse(img, cx + 10, ny, 1.8, 1.4, (.2, .2, .4))
            line(img, cx + 11.5, ny, cx + 11.5, ny - 5, (.2, .2, .4), w=1)
        self._half(img, cx, ys, psi, *((self.LONG, 1) if front else (self.SHORT, -1)))
        if t >= 5.35:                               # the lens
            ox, oy, _ = self._proj(60, ys, -self.LONG * math.cos(1.5), self.LONG * math.sin(1.5))
            for pts in self.crack:
                for (a, b), (c, d) in zip(pts, pts[1:]):
                    line(img, ox + a, oy + b, ox + c, oy + d, WHITE, w=1, a=0.85)
            _shake(img, t - 5.35, 6)


class Machine(Show):
    """Silent: a very elaborate machine, for saying hello. Then it rewinds."""
    num, title, length = 371, "THE MACHINE", 9.3
    DOM = [26, 34, 42, 50, 58]
    SHELF, PIV = 76, (84, 80)
    REW, END = 7.0, 5.5
    INK = (.85, .92, 1)

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        self.bg[:] = (.07, .2, .5)
        grid = ((X % 8 < 1) | (Y % 8 < 1))[..., None]
        self.bg[:] = np.where(grid, np.array((.12, .28, .6), np.float32), self.bg)
        rect(self.bg, 4, 2, 15, 17, (.3, .45, .75))
        rect(self.bg, 6, 2, 13, 17, (.07, .2, .5))
        line(self.bg, 6, 22, 64, 32, self.INK, w=2)
        line(self.bg, 72, 44, 22, 54, self.INK, w=2)
        rect(self.bg, 8, self.SHELF, 74, self.SHELF + 3, self.INK)
        poly(self.bg, [(self.PIV[0] - 5, 90), (self.PIV[0] + 5, 90), (self.PIV[0], self.PIV[1])], (.95, .6, .2))
        rect(self.bg, 79, 90, 89, 92, self.INK)
        line(self.bg, 124, 14, 124, 124, (.6, .65, .75), w=1.5)
        draw.ring(self.bg, 118, 12, 4, self.INK)
        rect(self.bg, 0, 120, N, N, (.05, .14, .38))

    def _marble(self, T):
        if T < 0.3:
            return 9.5, _lerp(10, 19, T / 0.3)
        if T < 1.3:
            x = _lerp(9.5, 64, ((T - 0.3) / 1.0) ** 2)
            return x, 22 + (x - 6) * 10 / 58 - 3.5
        if T < 1.55:
            u = (T - 1.3) / 0.25
            return _lerp(65, 69, u), _lerp(29, 41, u * u)
        if T < 2.45:
            x = _lerp(69, 22, ((T - 1.55) / 0.9) ** 2)
            return x, 44 + (72 - x) * 10 / 50 - 3.5
        if T < 2.7:
            u = (T - 2.45) / 0.25
            return 19, _lerp(51, self.SHELF - 3.5, u * u)
        return _lerp(19, 22, _cl((T - 2.7) / 0.15)), self.SHELF - 3.5

    def draw(self, img, t):
        img[:] = self.bg
        T = t if t < self.REW else max(0.0, self.END - (t - self.REW) * 3)
        ellipse(img, *self._marble(T), 3.2, 3.2, (1, .25, .25))
        for k, x in enumerate(self.DOM):
            a = (math.pi / 2 if k == 4 else 1.15) * _ease((T - 2.85 - 0.13 * k) / 0.18)
            _sprite(img, [("r", -4, -16, 0, 0, (1, .85, .2)), ("e", -2, -12, 0.9, 0.9, _K), ("e", -2, -5, 0.9, 0.9, _K)],
                    x + 3, self.SHELF, ang=a)
        tilt = 0.25 - 0.5 * _ease((T - 3.55) / 0.1)
        c, s = math.cos(tilt), math.sin(tilt)
        line(img, self.PIV[0] - 14 * c, self.PIV[1] - 14 * s, self.PIV[0] + 14 * c, self.PIV[1] + 14 * s, (.95, .6, .2), w=2.5)
        rx, ry = self.PIV[0] + 13 * c, self.PIV[1] + 13 * s - 4
        drop = _ease((T - 4.37) / 0.63)
        cup = (114, 54 + 60 * drop)
        if T < 3.65:
            bx, by = rx, ry
        elif T < 4.37:
            u = (T - 3.65) / 0.72
            bx, by = _lerp(rx, cup[0], u), _lerp(ry, cup[1] - 4, u) - 40 * math.sin(math.pi * u)
        else:
            bx, by = cup[0], cup[1] - 3
        line(img, 114, 12, cup[0], cup[1] - 6, (.9, .9, .9), w=1)
        flag = 124 - 62 * drop
        line(img, 122, 12, 122, flag, (.9, .9, .9), w=1)
        ellipse(img, bx, by, 2.6, 2.6, (.3, 1, .5))
        poly(img, [(cup[0] - 5, cup[1] - 6), (cup[0] + 5, cup[1] - 6), (cup[0] + 3, cup[1] + 2), (cup[0] - 3, cup[1] + 2)],
             (.3, .85, 1))
        rect(img, 104, flag, 122, flag + 11, WHITE)
        draw.text(img, "HI", 113, flag + 1, (.9, .1, .2), center=True)
        rect(img, 0, 120, N, N, (.05, .14, .38))
        if self.END - 0.5 < T and t < self.REW:
            for k in range(6):
                a = k * math.pi / 3 + t * 2
                star(img, 113 + 15 * math.cos(a), flag + 5 + 11 * math.sin(a), 2, YEL, n=4, inner=0.4)
        if t >= self.REW:                           # be kind, rewind
            band = int((t * 70) % (N + 20)) - 10
            rect(img, 0, band, N, band + 3, (.8, .85, 1), a=0.35)
            img[:] = np.roll(img, int(t * 12) % 2, 1)
            for k in range(2):
                poly(img, [(14 + k * 9, 6), (6 + k * 9, 11), (14 + k * 9, 16)], WHITE)


_PIN = [("e", 0, -5, 4, 5.5, _W), ("e", 0, -13, 2.2, 3.5, _W), ("e", 0, -18, 3, 3.2, _W),
        ("r", -2.3, -14, 2.3, -12.5, (.9, .1, .1))]


class Bowling(Show):
    """Silent: the ball bounces off the pins, and bowls the bowler. The pins are delighted."""
    num, title, length = 377, "STRIKE", 10.5
    G, H, BX = 100, 44, 18
    PINS = [100, 107, 114, 121]

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.18, .04, .28), (.08, .02, .15), 0, self.G)
        for k, col in enumerate(((1, .2, .7), (.2, .9, 1))):
            line(self.bg, 0, 40 + k * 6, N, 40 + k * 6, col, w=1.5)
        rect(self.bg, 28, 4, 100, 30, (.05, .05, .08))
        rect(self.bg, 30, 6, 98, 28, (.12, .1, .2))
        for k in range(1, 4):
            rect(self.bg, 30 + k * 17, 6, 31 + k * 17, 28, (.3, .25, .4))
        rect(self.bg, 0, self.G, N, self.G + 8, (.9, .7, .45))
        for x in range(0, N, 9):
            rect(self.bg, x, self.G, x + 1, self.G + 8, (.8, .6, .38))
        rect(self.bg, 0, self.G + 8, N, N, (.12, .1, .15))
        rect(self.bg, 0, self.G + 8, N, self.G + 10, (.3, .3, .35))

    def _ball(self, img, x, r=5.0, col=(.45, .15, .75)):
        y = self.G - r
        ellipse(img, x, y, r, r, col)
        a = -x / r
        for k in range(3):
            b = a + k * 0.5
            ellipse(img, x + r * 0.55 * math.cos(b), y + r * 0.55 * math.sin(b), r * 0.13, r * 0.13, (.1, .05, .15))

    def draw(self, img, t):
        img[:] = self.bg
        base = self.G - LEG * self.H
        x, y, rot, arm, look, mood, held = float(self.BX), base, 0.0, 1.0, (1, 0), 0, True
        if t < 0.8:
            pass
        elif t < 1.2:
            arm = _lerp(1.0, -0.9, _ease((t - 0.8) / 0.4))
        elif t < 1.4:
            arm = _lerp(-0.9, 1.5, (t - 1.2) / 0.2)
        elif t < 4.6:
            held, arm = False, 1.5 if t < 2.0 else 0.3
            mood = -1 if t > 2.7 else 0
            look = (0, 0) if 3.8 < t < 4.2 else (1, 0)
        elif t < 5.4:
            u = (t - 4.6) / 0.8
            held, x, y, rot, arm = False, _lerp(self.BX, 8, u), base - 40 * math.sin(math.pi * u) + (self.G - 5 - base) * u, \
                -math.pi / 2 - 4 * math.pi * (1 - u), 2.5
            mood = -1
        elif t < 7.2:
            held, x, y, rot, mood, look = False, 8, self.G - 5, -math.pi / 2, -1, (0, 0)
        elif t < 7.8:
            u = _ease((t - 7.2) / 0.6)
            held, x, y, rot, mood = False, _lerp(8, self.BX, u), _lerp(self.G - 5, base, u), -math.pi / 2 * (1 - u), -1
        elif t < 9.2:
            held, mood, look = False, -1, (1, 0)
        else:
            u = _ease((t - 9.2) / 0.35)
            held, rot, mood, look = False, -math.pi / 2 * u, -1, (0, 0)
            y = _lerp(base, self.G - 5, u)
            x = self.BX
        hx, hy, r = toon(img, x, y, self.H, SKINS[1], (.2, .7, .7), t, rot=rot, arms=(0.3, arm), look=look, mood=mood,
                         seed=77, pants=(.15, .15, .2))
        if held:
            px, py = hand(x, y, self.H, arm, 1, rot)
            ellipse(img, px, py, 5, 5, (.45, .15, .75))
        elif t < 4.6:
            if t < 2.6:
                bx = _lerp(30, 91, (t - 1.4) / 1.2)
            elif t < 3.6:
                bx = _lerp(91, 86, _ease((t - 2.6) / 0.3))
            else:
                bx = _lerp(86, 24, ((t - 3.6) / 1.0) ** 2)
            self._ball(img, bx)
        else:
            self._ball(img, _lerp(24, 34, _ease((t - 4.6) / 0.8)))
        cheer = 5.4 < t < 7.4 or t > 9.6
        for k, px in enumerate(self.PINS):
            wob = 0.25 * math.sin(t * 25 + k) * math.exp(-(t - 2.6) * 4) if t > 2.6 else 0.0
            hop = abs(math.sin(t * 9 + k)) * 5 if cheer else 0.0
            if k == 0 and 7.8 < t < 8.3:
                hop = 3 * abs(math.sin(t * 12))
            _sprite(img, _PIN, px, self.G - hop, ang=wob)
            ey = self.G - hop - 18
            ex = -1 if 2.6 < t < 9.6 else 0
            for e in (-1.2, 1.2):
                ellipse(img, px + e + ex * 0.6, ey, 0.7, 0.9, _K)
            if cheer:
                for s in (-1, 1):
                    line(img, px + s * 3, ey + 8, px + s * 6, ey + 1, _W, w=1)
        if 8.3 <= t < 9.2:                          # and one back, for him
            self._ball(img, _lerp(94, self.BX + 6, (t - 8.3) / 0.9), r=2.5, col=(1, .35, .6))
        elif t >= 9.2:
            self._ball(img, self.BX + 6, r=2.5, col=(1, .35, .6))
        if 0 <= t - 2.6 < 0.12:
            _bang(img, 96, self.G - 6, 5, t)
        if 0 <= t - 4.6 < 0.12:
            _bang(img, self.BX + 4, self.G - 8, 7, t)
        if 5.4 < t < 7.4 or t > 9.6:                # the scoreboard approves
            col = (1, .2, .2) if int(t * 4) % 2 else (1, .9, .2)
            draw.text(img, "X", 64, 7, col, center=True, scale=2)
        else:
            draw.text(img, "-", 64, 7, (.5, .45, .6), center=True, scale=2)
        if 5.4 <= t < 5.9:
            _dust(img, 8, self.G, (t - 5.4) * 2, spread=0.8)


def _monster(img, x, g, t, d=1, run=1.0):
    """A friendly furry monster: one eye, all teeth."""
    by = g - 22 - abs(math.sin(t * 10)) * 2 * run
    for k in (-1, 1):
        a = run * 0.6 * math.sin(t * 10) * k
        line(img, x + 4 * k, by + 8, x + 4 * k + 10 * math.sin(a), g, (.25, .55, .1), w=3)
    for k in (-1, 1):
        line(img, x + 9 * k, by - 4, x + 15 * k, by - 16 + 3 * math.sin(t * 12 + k), (.35, .75, .15), w=3)
    ellipse(img, x, by, 11, 14, (.35, .75, .15))
    for k in range(5):
        ellipse(img, x - 8 + k * 4, by - 13 + (k % 2) * 2, 2.5, 3, (.35, .75, .15))
    ellipse(img, x + d * 2, by - 5, 5, 5, WHITE)
    ellipse(img, x + d * 4, by - 5, 2.2, 2.4, _K)
    ellipse(img, x + d * 2, by + 5, 6, 3, (.3, .05, .1))
    for k in range(4):
        poly(img, [(x + d * 2 - 5 + k * 3, by + 2.5), (x + d * 2 - 3.5 + k * 3, by + 5), (x + d * 2 - 2 + k * 3, by + 2.5)], WHITE)


class Hallway(Show):
    """Silent: the chase, in a hotel hallway, through the doors, as it must be done."""
    num, title, length = 384, "CHASE", 12.0
    G, H = 112, 40
    DOORS = [16, 48, 80, 112]
    SCRIPT = [(0.3, 1.3, "man", 0, 2), (0.8, 1.8, "mon", 0, 2), (2.0, 2.9, "man", 3, 1), (2.4, 3.3, "mon", 3, 1),
              (3.7, 4.5, "mon", 1, 3), (4.0, 4.8, "man", 1, 3), (5.2, 6.8, "cow", 2, 0), (5.6, 6.5, "man", 3, "L"),
              (5.9, 6.8, "mon", 3, "L"), (7.1, 8.0, "man", 1, 1), (7.1, 8.0, "man2", 2, 2), (8.0, 8.4, "man", 1, 2),
              (8.0, 8.4, "man2", 2, 1), (8.8, 10.4, "man", "L", "R"), (9.0, 10.6, "mon", "L", "R"),
              (9.25, 11.0, "cow", "L", "R"), (9.5, 11.2, "man2", "L", "R"), (9.7, 11.0, "tiny", "L", "R"),
              (11.3, 12.1, "cow", 3, 3)]

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        s = (np.sin(X * 0.5) > 0.85)[..., None]
        self.bg[:] = np.where(s, np.array((.75, .6, .25), np.float32), np.array((.45, .12, .18), np.float32))
        rect(self.bg, 0, 90, N, 92, (.75, .6, .25))
        rect(self.bg, 0, 92, N, self.G, (.32, .1, .12))
        vgrad(self.bg, (.6, .12, .12), (.35, .05, .08), self.G, N)
        for k in range(0, N, 32):
            ellipse(self.bg, k + 32, 20, 4, 3, (1, .9, .6))
            rect(self.bg, k + 31, 8, k + 33, 18, (.75, .6, .25))
        for i, x in enumerate(self.DOORS):
            rect(self.bg, x - 12, self.G - 46, x + 12, self.G, (.3, .15, .05))
            rect(self.bg, x - 10, self.G - 44, x + 10, self.G, (.6, .35, .15))
            rect(self.bg, x - 7, self.G - 40, x + 7, self.G - 26, (.52, .3, .12))
            ellipse(self.bg, x + 6, self.G - 20, 1.5, 1.5, (1, .85, .3))
            draw.text(self.bg, str(i + 1), x, self.G - 38, (1, .85, .3), center=True)

    def _x(self, p):
        return -22 if p == "L" else 150 if p == "R" else self.DOORS[p]

    def draw(self, img, t):
        img[:] = self.bg
        actors = []
        for t0, t1, who, a, b in self.SCRIPT:
            for p, tt in ((a, t0), (b, t1)):
                if p not in ("L", "R") and (tt - 0.2 < t < tt + 0.25 or (a == b and t0 - 0.2 < t < t1 + 0.2)):
                    x = self.DOORS[p]
                    rect(img, x - 10, self.G - 44, x + 10, self.G, (.04, .02, .02))
                    poly(img, [(x - 10, self.G - 44), (x - 15, self.G - 48), (x - 15, self.G + 3), (x - 10, self.G)],
                         (.6, .35, .15))
            if t0 <= t < t1:
                actors.append((t0, t1, who, a, b))
        for t0, t1, who, a, b in actors:
            u = (t - t0) / (t1 - t0)
            xa, xb = self._x(a), self._x(b)
            x = _lerp(xa, xb, u)
            d = 1 if xb > xa else -1 if xb < xa else (1 if who == "man" else -1)
            run = 0.0 if a == b else 1.0
            if who in ("man", "man2", "tiny"):
                h = 18 if who == "tiny" else self.H
                look = (d, 0)
                arms = (2.4 + 0.4 * math.sin(t * 20), 2.4 - 0.4 * math.sin(t * 20)) if run else (0.3, 1.6 if 7.4 < t < 7.9 else 0.3)
                if who == "man" and 4.0 <= t0 < 5 and run:
                    arms = (1.5, 1.5)               # the chaser, for once
                hx, hy, r = toon(img, x, self.G - LEG * h, h, SKINS[0], (.9, .3, .2), t * 1.6, walk=run * 1.5, arms=arms,
                                 look=look, mood=-1 if (run and not (4.0 <= t0 < 5)) else 1 if who == "tiny" else 0,
                                 talk=0.8 if run and who != "tiny" else 0.0, seed=3)
            elif who == "mon":
                _monster(img, x, self.G, t * 1.4, d, run)
            else:
                _sprite(img, _COW, x, self.G, sx=0.8 * d, sy=0.8)


def _dchair(img, x, g, col=(.4, .2, .1)):
    """A dining chair in profile, facing right: its back at x, feet on row g."""
    rect(img, x, g - 36, x + 2, g, col)
    rect(img, x + 14, g - 11, x + 16, g, col)
    rect(img, x, g - 12, x + 16, g - 9, col)
    rect(img, x + 1, g - 14, x + 16, g - 12, (.75, .1, .15))
    rect(img, x - 1, g - 37, x + 3, g - 34, col)


class Dinner(Show):
    """Silent: the butler pulls the chair away. The diner doesn't need it. Until he does."""
    num, title, length = 390, "FINE DINING", 9.5
    G, H = 114, 46
    CH, BX = 42, 24                                 # the chair's place; the butler's

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.5, .08, .14), (.35, .05, .1), 0, self.G)
        rect(self.bg, 0, 80, N, 82, (.85, .7, .3))
        tile = ((X // 8 + Y // 4) % 2)[..., None]
        self.bg[self.G:] = (np.array((.85, .8, .7), np.float32) * (1 - tile) + np.array((.2, .15, .15), np.float32) * tile)[self.G:]
        line(self.bg, 64, 0, 64, 10, (.85, .7, .3), w=1)
        ellipse(self.bg, 64, 12, 14, 3, (.85, .7, .3))
        for k in (-12, -4, 4, 12):
            rect(self.bg, 64 + k - 1, 5, 64 + k + 1, 10, (.95, .95, .85))
            ellipse(self.bg, 64 + k, 3.5, 1.2, 1.8, (1, .8, .3))
        rect(self.bg, 84, 86, N, 104, (.95, .93, .88))
        rect(self.bg, 90, 104, 93, self.G, (.4, .2, .1))
        rect(self.bg, 122, 104, 125, self.G, (.4, .2, .1))
        ellipse(self.bg, 98, 85, 9, 2, (.9, .9, .95))
        ellipse(self.bg, 98, 84.5, 5, 1, (.5, .7, .4))
        rect(self.bg, 112, 76, 114, 86, (.95, .95, .85))
        ellipse(self.bg, 113, 74, 1.3, 2, (1, .8, .3))

    def _butler(self, img, t):
        sit = _ease((t - 7.4) / 0.5)
        base = self.G - LEG * self.H
        y = _lerp(base, self.G - 12, sit)
        arms, look, mood, rot = (0.3, 0.3), (1, 0), 0, 0.0
        if 1.4 < t < 1.8:
            rot = 0.25 * math.sin(math.pi * (t - 1.4) / 0.4)
        elif 2.0 <= t < 2.3 or 4.4 <= t < 5.1:
            arms = (0.3, 1.4)
        elif 3.2 <= t < 4.4:
            look, mood = (0, 0), -1 if t > 3.7 else 0
        elif 5.4 <= t < 7.4:
            look, mood, arms = (0, 0), 0, (1.3, 1.3) if t > 6.2 else (0.3, 0.3)
        elif t >= 7.4:
            look, mood, arms = (0, 0), 1, (0.3, 1.2)
        hx, hy, r = _figure(img, self.BX, y, self.H, SKINS[0], (.08, .08, .12), t, d=1, thigh=math.pi / 2 * sit,
                            arms=arms, look=look, mood=mood, seed=90, pants=(.08, .08, .12), rot=rot)
        sx, sy = self.BX - math.sin(rot) * self.H * 0.25, y - self.H * 0.25 * math.cos(rot)
        ellipse(img, sx, sy, 2.5, 5, WHITE)
        poly(img, [(sx - 3, sy - 6), (sx + 3, sy - 4), (sx + 3, sy - 8), (sx - 3, sy - 6.5)], WHITE)
        line(img, hx - r * 0.5, hy + r * 0.3, hx + r * 0.5, hy + r * 0.3, (.25, .15, .1), w=1.6)
        if t >= 7.9:                                # tea
            px, py = hand(self.BX, y, self.H, 1.2, 1)
            rect(img, px - 2, py - 4, px + 2, py, WHITE)
            ellipse(img, px + 3, py - 2, 1.2, 1.2, WHITE)

    def draw(self, img, t):
        img[:] = self.bg
        if t < 2.0:
            cx = self.CH
        elif t < 2.2:
            cx = _lerp(self.CH, 6, _ease((t - 2.0) / 0.2))
        elif t < 4.4:
            cx = 6
        elif t < 5.1:
            cx = _lerp(6, self.CH, _ease((t - 4.4) / 0.7))
        else:
            cx = None
        self._butler(img, t)
        if cx is not None:
            _dchair(img, cx, self.G)
        base = self.G - LEG * self.H
        x, y, thigh, shin, arms, look, mood = 50.0, base, 0.0, 0.0, (0.3, 0.3), (-1, 0), 0
        seat = self.G - 11.7
        if t < 1.4:
            x = _lerp(140, 50, t / 1.4)
            toon(img, x, base, self.H, SKINS[2], (.3, .3, .65), t, walk=1, look=(-1, 0), seed=91)
        else:
            if t < 1.8:
                pass
            elif t < 2.3:
                u = _ease((t - 1.8) / 0.5)
                y, thigh = _lerp(base, seat, u), math.pi / 2 * u
            elif t < 5.15:
                y, thigh, look, mood = seat, math.pi / 2, (1, 0), 1
                arms = (2.0 + 0.2 * math.sin(t * 8), 2.0 - 0.2 * math.sin(t * 8)) if t > 3.0 else (0.3, 0.3)
            else:
                u = _cl((t - 5.15) / 0.12)
                y, thigh, shin, look, mood = _lerp(seat, self.G - 4, u), math.pi / 2, math.pi / 2 * u, (0, 0), -1
                if t > 8.0:
                    look = (-1, 0)
            hx, hy, r = _figure(img, x, y, self.H, SKINS[2], (.3, .3, .65), t, d=1, thigh=thigh, shin=shin, arms=arms,
                                look=look, mood=mood, seed=91)
            if 2.6 < t:
                poly(img, [(hx - 5, hy + r * 1.1), (hx + 5, hy + r * 1.1), (hx, hy + r * 2.4)], WHITE)
            if 3.0 < t < 5.15:
                for k, col in ((-1, (.8, .8, .85)), (1, (.8, .8, .85))):
                    px, py = hand(x, y, self.H, arms[0 if k < 0 else 1], k)
                    line(img, px, py, px, py - 7, col, w=1)
            if t > 5.4:
                _stars(img, hx, hy - r - 2, t)
        if t >= 5.15:                               # the chair, in kit form
            u = min(1.0, t - 5.15)
            for k, (dx, a) in enumerate(((-14, -1.2), (-6, -0.4), (6, 0.5), (14, 1.3), (20, 2.0))):
                gx = self.CH + 8 + dx * (0.3 + 1.6 * _ease(u * 2))
                gy = self.G - 2 - 18 * math.sin(math.pi * _cl(u * 2.5)) * (k % 2 + 0.5)
                _sprite(img, [("r", -7, -1.2, 7, 1.2, (.4, .2, .1))], gx, gy, ang=a * _cl(u * 3))
            _dust(img, x, self.G, (t - 5.15) * 1.5, spread=1.2)
            _shake(img, t - 5.15, 5)


class WrongRoom(Show):
    """Silent: a door that opens onto somewhere different every time. Then it follows him home."""
    num, title, length = 396, "WRONG DOOR", 11.5
    G, H, X0, DC = 114, 50, 30, 74
    TOP = 40
    # (opens, starts closing, takes, room)
    VISITS = [(0.5, 1.6, 0.1, "sea"), (2.2, 3.5, 0.1, "space"), (4.2, 5.4, 0.6, "eye"), (6.6, 7.8, 0.5, "me")]

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        dots = ((X % 10 < 1.5) & (Y % 10 < 1.5))[..., None]
        self.bg[:] = np.where(dots, np.array((.75, .55, .3), np.float32), np.array((.95, .82, .55), np.float32))
        rect(self.bg, 0, self.G - 5, N, self.G, (.5, .3, .15))
        rect(self.bg, 0, self.G, N, N, (.45, .3, .2))
        rng = np.random.default_rng(396)
        self.space = np.zeros((N, N, 3), np.float32)
        self.space[:] = (.02, .02, .07)
        for _ in range(40):
            ellipse(self.space, rng.uniform(50, 100), rng.uniform(36, 116), 0.6, 0.6, (1, 1, .9))
        ellipse(self.space, 80, 60, 7, 7, (.95, .55, .3))
        ellipse(self.space, 80, 60, 13, 2.5, (.95, .85, .6), a=0.7)
        ellipse(self.space, 80, 58, 7, 4, (.95, .55, .3), half="top")
        self.room = np.empty((N, N, 3), np.float32)

    def _open(self, t):
        for t0, tc, dur, room in self.VISITS:
            if t0 <= t < tc + dur:
                o = _cl((t - t0) / 0.15) if t < tc else 1 - _cl((t - tc) / dur)
                return o, room, t - t0
        return 0.0, None, 0.0

    def _room(self, t, room, lt):
        r = self.room
        x0, x1, y0, y1 = self.DC - 17, self.DC + 17, self.TOP, self.G
        if room == "sea":
            vgrad(r, (.1, .5, .9), (.02, .15, .45), y0, y1)
            fx = x1 - (lt * 30) % 50
            ellipse(r, fx, 70, 7, 4, (1, .5, .1))
            poly(r, [(fx + 6, 70), (fx + 12, 65), (fx + 12, 75)], (1, .5, .1))
            ellipse(r, fx - 3, 69, 1, 1, _K)
            for k in range(4):
                ellipse(r, x0 + 6 + k * 8, y1 - ((lt * 40 + k * 23) % 70), 1.5, 1.5, (.7, .9, 1))
        elif room == "space":
            r[y0:y1, x0:x1] = self.space[y0:y1, x0:x1]
        elif room == "eye":
            r[y0:y1, x0:x1] = (.95, .72, .6)
            ellipse(r, self.DC, 72, 15, 10, WHITE)
            ellipse(r, self.DC - 6, 72, 7, 7, (.2, .55, .3))
            ellipse(r, self.DC - 7, 72, 3.5, 3.5, _K)
            if 0.7 < lt < 0.9:
                rect(r, x0, 60, x1, 84, (.85, .6, .5))
        else:
            r[y0:y1, x0:x1] = self.bg[y0:y1, x0:x1]
            toon(r, self.DC + 6, self.G - LEG * self.H, self.H, SKINS[3], (.95, .75, .2), t, look=(-1, 0),
                 arms=(1.5 if 0.6 < lt < 1.0 else 0.3, 0.3), seed=96, pants=(.25, .25, .45))
        return r[y0:y1, x0:x1]

    def _door(self, img, dc, o, lift=0.0):
        top, g = self.TOP - lift, self.G - lift
        for box in ((dc - 19, top - 2, dc - 17, g), (dc + 17, top - 2, dc + 19, g), (dc - 19, top - 2, dc + 19, top)):
            rect(img, *box, (.35, .18, .08))
        if o <= 0:
            rect(img, dc - 17, top, dc + 17, g, (.6, .35, .15))
            rect(img, dc - 13, top + 6, dc + 13, top + 30, (.52, .3, .12))
            rect(img, dc - 13, top + 40, dc + 13, g - 6, (.52, .3, .12))
            ellipse(img, dc - 12, top + 38, 1.8, 1.8, (1, .85, .3))
        else:
            phi = 0.75 * math.pi * o
            hx = dc + 17
            fx = hx - 34 * math.cos(phi)
            s = 6 * math.sin(phi)
            poly(img, [(hx, top), (fx, top - s), (fx, g + s), (hx, g)], (.6, .35, .15))

    def draw(self, img, t):
        img[:] = self.bg
        o, room, lt = self._open(t)
        dc, lift = float(self.DC), 0.0
        if t > 9.4:
            dc = self.DC - 75 * (t - 9.4)
            lift = 5
        if room:
            img[self.TOP:self.G, self.DC - 17:self.DC + 17] = self._room(t, room, lt)
        if t > 9.4 and dc > -25:
            for k in (-1, 1):
                a = 0.5 * math.sin(t * 14) * k
                line(img, dc + 8 * k, self.G - 5, dc + 8 * k + 6 * math.sin(a), self.G, (.35, .18, .08), w=2)
        if dc > -25:
            self._door(img, dc, o, lift)
        base = self.G - LEG * self.H
        x, rot, arms, look, mood, walk = float(self.X0), 0.0, (0.3, 0.3), (1, 0), 0, 0.0
        if room == "sea":
            arms = (0.3, 1.5)
        elif room == "space":
            u = _cl(lt / 0.4)
            x, rot, arms = self.X0 + 8 * u, 0.35 * u + 0.05 * math.sin(t * 40), (1.9, 1.6)
        elif room == "eye":
            look, mood = (1, 0) if lt < 1.2 else (0, 0), -1
        elif room == "me":
            arms = (0.3, 1.5 if 0.6 < lt < 1.0 else 0.3)
        elif 1.7 < t < 2.2 or 3.6 < t < 4.2 or 6.0 < t < 6.6 or 8.3 < t < 8.8:
            look, mood = (0, 0), -1
        elif t >= 8.8:
            x, walk, look = _lerp(self.X0, -30, (t - 8.8) / 1.5), 1.0, (-1, 0)
            if t > 9.6:
                look = (1, 0)
        if x > -25:
            hx, hy, r = toon(img, x, base, self.H, SKINS[3], (.95, .75, .2), t, walk=walk, rot=rot, arms=arms, look=look,
                             mood=mood, seed=96, pants=(.25, .25, .45))
            if 1.6 < t < 3.0:                       # dripping
                ellipse(img, hx + 4, hy + r + ((t * 30) % 14), 1, 1.5, (.5, .75, 1))
        if room == "sea" and lt > 0.4:              # the sea comes in
            u = _cl((lt - 0.4) / 0.6)
            poly(img, [(self.DC - 17, self.G - 30 * (1 - u * 0.5)), (self.DC - 17 - 40 * u, self.G - 2), (self.DC - 17, self.G)],
                 (.2, .55, .95))
        if 1.0 < t < 2.6:                           # a puddle, and a fish who's having a day
            w = 24 * (1 - _cl((t - 2.3) / 0.3))
            ellipse(img, self.DC - 30, self.G + 2, w, 2.5, (.2, .55, .95), a=0.8)
        if 1.2 < t < 2.75:
            if t < 2.4:
                fx, fy, fa = self.DC - 30, self.G - 3 - 4 * abs(math.sin(t * 9)), 0.4 * math.sin(t * 9)
            else:
                u = (t - 2.4) / 0.35
                fx, fy, fa = _lerp(self.DC - 30, self.DC, u), _lerp(self.G - 3, 70, u), u * 9
            _sprite(img, [("e", 0, 0, 5, 3, (1, .5, .1)), ("p", [(4, 0), (9, -4), (9, 4)], (1, .5, .1)), ("e", -2.5, -1, 0.8, 0.8, _K)],
                    fx, fy, fa)
        if room == "space" and o > 0.5:
            for k in range(6):
                sx = (self.DC - 20) - ((-lt * 140 + k * 23) % 70)
                line(img, sx, 50 + k * 10, sx + 10, 50 + k * 10, WHITE, w=1, a=0.6)


CHANNELS = [Rakes, Hiccup, LookDown, GoodBoy, Toast, Sneeze, HeadsUp, Cat, LawnChair, Taffy, Plank, Machine, Bowling, Hallway,
            Dinner, WrongRoom]
