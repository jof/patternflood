"""Pure strangeness: stop motion, action figures, lessons, music videos, trailers and things that are the wrong size."""
import math

import numpy as np

from .. import draw
from ..draw import N, X, Y
from .kit import BLACK, LEG, SKINS, WHITE, cue, ellipse, face, hand, line, poly, rays, rect, star, toon, vgrad, words
from .shows import Show


# ---------------------------------------------------------------- helpers

def _stop(t, fps=8):
    """Time as the animator saw it: fps poses a second."""
    return math.floor(t * fps) / fps


def _jit(t, k, amp=0.7, fps=8):
    """A fingerprint's wobble: a small offset, fixed within a frame, new every frame."""
    v = math.sin(math.floor(t * fps) * 12.9898 + k * 78.233) * 43758.5453
    return (v - math.floor(v) - 0.5) * 2 * amp


def _u(t, t0, t1):
    return min(1.0, max(0.0, (t - t0) / (t1 - t0)))


def _ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def _lerp(a, b, u):
    return a + (b - a) * u


def _dizzy(img, x, y, t, r=9.0):
    for k in range(3):
        a = t * 6 + k * 2.1
        star(img, x + r * math.cos(a), y + 3 * math.sin(a), 2.5, (1, .9, .2), n=5, inner=0.45)


def _bubble(img, x, y, s, rgb=BLACK):
    w = draw.text_width(s) + 6
    rect(img, x - w / 2, y, x + w / 2, y + 12, WHITE)
    poly(img, [(x - 2, y + 12), (x + 4, y + 12), (x + 6, y + 17)], WHITE)
    draw.text(img, s, x, y + 1, rgb, center=True)


def _texture(seed, amp=0.05, f=0.18):
    rng = np.random.default_rng(seed)
    v = np.zeros((N, N), np.float32)
    for _ in range(5):
        a, b, p = rng.uniform(-f, f), rng.uniform(-f, f), rng.uniform(0, 6.3)
        v += np.sin(X * a + Y * b + p)
    return (v / 5 * amp)[..., None]


# ---------------------------------------------------------------- 601 clay

class ClayDay(Show):
    """Silent, in clay: the animator keeps fixing his face; he fixes the camera."""
    num, title, length = 601, "CLAY DAY", 9.5
    GY = 104
    CLAY = (.3, .72, .32)
    THUMB = (.93, .72, .58)

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.35, .65, .95), (.6, .8, .95), 0, self.GY)
        self.bg[self.GY:] = (.85, .5, .25)
        self.bg += _texture(601, 0.06)
        ellipse(self.bg, 22, 22, 11, 11, (1, .85, .2))
        for cx, cy in ((90, 20), (60, 34)):
            for dx in (-7, 0, 7):
                ellipse(self.bg, cx + dx, cy - (dx == 0) * 3, 8, 6, (.95, .95, .98))
        for fx, c in ((14, (1, .3, .4)), (116, (.95, .6, .1))):
            line(self.bg, fx, self.GY, fx, self.GY - 16, (.2, .55, .2), w=2)
            for k in range(5):
                a = k * 2 * math.pi / 5
                ellipse(self.bg, fx + 4 * math.cos(a), self.GY - 18 + 4 * math.sin(a), 2.8, 2.8, c)
            ellipse(self.bg, fx, self.GY - 18, 2, 2, (1, .9, .3))
        r = np.hypot((X - 64) / 1.0, (Y - 62) / 1.3)
        ang = np.arctan2(Y - 62, X - 64)
        ridge = 0.5 + 0.5 * np.sin(r * 1.25 + 1.2 * np.sin(2 * ang) + 0.04 * X)
        self.ridge = ridge[..., None].astype(np.float32)
        edge = np.clip((58 - r) / 10, 0, 1)
        self.smudge = ((ridge > 0.8) * edge)[..., None].astype(np.float32)

    def _man(self, img, x, gy, s, t, mood, flat, arms, brow=0.0):
        j = lambda k: _jit(t, k, 0.6 * s)       # noqa: E731
        for k in (-1, 1):
            ellipse(img, x + k * 5 * s + j(1 + k), gy - 6 * s, 4 * s, 7 * s, (.2, .5, .25))
        ellipse(img, x + j(3), gy - 19 * s, 11 * s, 13 * s, self.CLAY)
        for k, a in zip((-1, 1), arms):
            sx, sy = x + k * 9 * s, gy - 27 * s
            ex, ey = sx + k * math.sin(a) * 13 * s + j(4 + k), sy + math.cos(a) * 13 * s + j(6 + k)
            line(img, sx, sy, ex, ey, self.CLAY, w=5 * s)
            ellipse(img, ex, ey, 3 * s, 3 * s, self.CLAY)
        r = 11 * s
        hx, hy = x + j(8), gy - 31 * s - r * 1.12 * flat + 2 * s
        face(img, hx, hy, r, (.98, .72, .45), t, mood=mood, flat=flat, seed=1.3)
        if brow:
            for k in (-1, 1):
                line(img, hx + k * r * 0.6, hy - r * 0.5 * flat - brow * r * 0.15, hx + k * r * 0.15,
                     hy - r * 0.35 * flat + brow * r * 0.1, (.3, .15, .05), w=max(1, 1.6 * s))
        return hx, hy, r

    def _thumb(self, img, x, tip):
        rect(img, x - 13, -2, x + 13, tip - 14, self.THUMB)
        ellipse(img, x, tip - 14, 13, 14, self.THUMB)
        ellipse(img, x, tip - 12, 8, 9, (.98, .85, .8))
        line(img, x - 13, tip - 40, x + 13, tip - 38, (.8, .55, .45), w=1)

    def draw(self, img, t):
        t = _stop(t)
        if 6.6 <= t < 7.4:                          # his finger, on the lens
            u = _u(t, 6.6, 6.9)
            img[:] = self.bg
            if u < 1:
                self._man(img, 64, 200, 3.2, t, 1, 0.5, (0.3, 2.0), brow=1)
            ellipse(img, 64, 64, 10 + 100 * u, 10 + 100 * u, self.CLAY)
            if u >= 1:
                img *= 0.75 + 0.25 * self.ridge
            return
        img[:] = self.bg
        mood, flat, arms, brow = -1, 1.0, (0.25, 0.25), 0.0
        x, gy, s = 64.0, float(self.GY), 1.0
        tip = None
        if t < 1.2:
            arms = (0.15, 0.15)
        elif t < 3.0:                               # a smile, pressed in
            tip = _lerp(-10, 72, _ease(_u(t, 1.2, 2.0))) if t < 2.4 else _lerp(72, -10, _u(t, 2.4, 3.0))
            mood = -1 if t < 2.2 else 1
            arms = (0.6, 0.6) if 2.0 <= t < 2.4 else arms
        elif t < 3.8:
            mood, arms = 1, (2.6, 2.6 + 0.4 * (int(t * 8) % 2))
        elif t < 4.2:
            mood = 0 if t < 4.0 else -1
        elif t < 5.8:                               # a better smile, pressed in harder
            mood = 1
            if t < 5.0:
                tip = _lerp(-10, 52, _ease(_u(t, 4.2, 5.0)))
            elif t < 5.4:
                flat = _lerp(1.0, 0.5, _u(t, 5.0, 5.3))
                tip = _lerp(52, 76, _u(t, 5.0, 5.3))
                arms = (1.2, 1.2)
            else:
                flat, tip, brow, mood = 0.5, _lerp(76, -10, _u(t, 5.4, 5.8)), 1, -1
        elif t < 6.6:                               # he comes to have a word
            u = _ease(_u(t, 5.8, 6.6))
            flat, brow, mood = 0.5, 1, -1
            s, gy = _lerp(1, 3.2, u), _lerp(self.GY, 200, u)
            arms = (0.3, _lerp(0.3, 2.0, u))
        else:                                       # better
            flat, mood, arms = 0.5, 1, (2.4, 2.4)
        hx, hy, r = self._man(img, x, gy, s, t, mood, flat, arms, brow)
        if tip is not None:
            self._thumb(img, hx, tip)
        if t >= 7.4:
            img += self.smudge * 0.13


# ---------------------------------------------------------------- action figures

SUIT = (.15, .3, .85)


def _phead(img, x, y, rot=0.0, skin=SKINS[0], hair=(.25, .15, .05), helmet=None):
    """A moulded plastic head, painted on: it can't change its expression."""
    c, s = math.cos(rot), math.sin(rot)

    def at(dx, dy):
        return x + dx * c - dy * s, y + dx * s + dy * c

    ellipse(img, x, y, 8, 9.5, skin, rot=rot)
    if helmet:
        ellipse(img, *at(0, -3), 9.5, 8, helmet, rot=rot)
        ellipse(img, *at(0, 1), 6.5, 4.5, skin, rot=rot)
    else:
        ellipse(img, *at(0, -5), 8.4, 5, hair, rot=rot)
    for k in (-1, 1):
        ellipse(img, *at(k * 3.2, -0.5), 1.2, 1.4, BLACK, rot=rot)
        line(img, *at(k * 1.5, -3.2), *at(k * 5, -2.6), BLACK, w=1)
    line(img, *at(-3, 4.2), *at(0, 5.6), (.5, .1, .1), w=1.2)
    line(img, *at(0, 5.6), *at(3, 4.2), (.5, .1, .1), w=1.2)


def _figure(img, x, gy, arms, t, suit=SUIT, head=True, has=(True, True), skin=SKINS[0], helmet=None, j=0.0):
    """A stiff action figure, feet at gy: arms swing at the shoulders and nothing else bends.
    Returns the neck peg's top and each hand."""
    x += _jit(t, 1, j, 12)
    gy += _jit(t, 2, j * 0.5, 12)
    for k in (-1, 1):
        line(img, x + k * 4, gy - 24, x + k * 9, gy - 3, suit, w=6)
        rect(img, x + k * 9 - 4, gy - 6, x + k * 9 + 4, gy, (.1, .1, .15))
    poly(img, [(x - 14, gy - 47), (x + 14, gy - 47), (x + 8, gy - 24), (x - 8, gy - 24)], suit)
    rect(img, x - 8, gy - 28, x + 8, gy - 24, (1, .8, .1))
    star(img, x, gy - 39, 4.5, (1, .8, .1), n=5, inner=0.45)
    rect(img, x - 2, gy - 52, x + 2, gy - 46, (.6, .6, .6))
    hands = []
    for k, a, on in zip((-1, 1), arms, has):
        sx, sy = x + k * 14, gy - 44
        ex, ey = sx + k * math.sin(a) * 15, sy + math.cos(a) * 15
        hands.append((ex, ey))
        if on:
            line(img, sx, sy, ex, ey, suit, w=6)
            ellipse(img, ex, ey, 3.5, 3.5, skin)
        else:
            ellipse(img, sx, sy, 2.5, 2.5, (.6, .6, .6))
    if head:
        _phead(img, x, gy - 58, skin=skin, helmet=helmet)
    return (x, gy - 52), hands


class PlasticHeroes(Show):
    """Silent, in stop motion: a hero pose, a head pops off, a head goes back on (upside down)."""
    num, title, length = 607, "PLASTIC HEROES", 9.5
    GY = 104

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.25, .55, .55), (.2, .42, .45), 0, 96)
        self.bg[96:] = (.6, .38, .2)
        self.bg[96:] += (0.04 * np.sin(Y[96:] * 1.7 + np.sin(X[96:] * 0.05) * 3))[..., None]
        rect(self.bg, 2, 8, 40, 96, (.85, .15, .2))         # a cereal box, very big
        rect(self.bg, 2, 30, 40, 50, (1, .8, .1))
        star(self.bg, 21, 72, 13, (1, .95, .4), n=10)
        ellipse(self.bg, 21, 72, 7, 5, (.9, .55, .2))
        rect(self.bg, 92, 52, 124, 96, (.85, .85, .78))     # a mug, very big
        ellipse(self.bg, 124, 72, 9, 12, (.85, .85, .78))
        ellipse(self.bg, 124, 72, 4.5, 7, (.2, .42, .45))
        rect(self.bg, 92, 52, 124, 56, (.4, .22, .1))
        ellipse(self.bg, 108, 80, 6, 6, (.9, .35, .4))

    def draw(self, img, t):
        t = _stop(t, 12)
        img[:] = self.bg
        x, gy, arms, j = 64.0, float(self.GY), (0.15, 0.15), 0.3
        head = True
        hpos = None                                 # (x, y, rot) of a loose head
        if t < 1.5:
            p = t / 1.5 * 3
            x = -20 + 28 * p
            gy -= 10 * math.sin(math.pi * (p % 1))
        elif t < 2.0:
            arms = (2.9, 2.9)
        elif t < 3.0:
            arms, j = (1.6, 1.6), 0.4 + (t - 2.0) * 1.5
        elif t < 4.4:                               # sproing
            arms, j, head = (1.6, 1.6), 1.6, False
            u = t - 3.0
            if u < 0.8:
                hpos = (64 + 44 * u, gy - 58 - 90 * u + 115 * u * u, u * 9)
            else:
                v = u - 0.8
                hpos = (99 + 14 * v, self.GY - 6 - 8 * abs(math.sin(v * 9)) * math.exp(-v * 4), 7.2 + v * 6)
        elif t < 7.2:
            head = False
            hpos = (107, self.GY - 6, 10.6)
            if t < 4.8:
                arms = (0.4, 2.7 + 0.2 * math.sin(t * 40))
            elif t < 6.0:
                p = (t - 4.8) / 1.2 * 2
                x, gy = 64 + 16 * p, gy - 8 * math.sin(math.pi * (p % 1))
                arms = (0.6, 1.0)
            elif t < 6.6:
                x, arms = 96.0, (0.3, 0.15)
                hpos = (110, self.GY - 6, 10.6) if t < 6.3 else (110, self.GY - 10, math.pi)
            else:
                x, arms = 96.0, (0.3, 2.6)
                u = _u(t, 6.6, 7.1)
                hpos = (_lerp(110, 96, u), _lerp(self.GY - 10, self.GY - 58, u), math.pi)
        else:
            p = min(1.0, (t - 7.2) / 0.6)
            x = 96 - 32 * p
            gy -= 8 * math.sin(math.pi * p)
            arms = (2.9, 2.9) if t > 7.8 else (0.3, 0.3)
            hpos = None
        neck, _ = _figure(img, x, gy, arms, t, head=head, j=j)
        if t >= 7.2:
            _phead(img, neck[0], neck[1] - 6, rot=math.pi)
            if t > 7.9:
                for k in range(4):
                    a = k * math.pi / 2 + t * 2
                    star(img, x + 30 * math.cos(a), gy - 50 + 22 * math.sin(a), 3, (1, 1, .6), n=4, inner=0.3)
        if hpos:
            _phead(img, *hpos)
        if 3.0 <= t < 3.25:
            star(img, 64, self.GY - 54, 9, (1, .9, .3), n=8, inner=0.4)
            for k in range(4):
                line(img, 61 + 2 * (k % 2) * 3, self.GY - 52 - k * 3, 67 - 2 * (k % 2) * 3, self.GY - 55 - k * 3,
                     (.7, .7, .7), w=1)


# ---------------------------------------------------------------- lessons

ALIEN, ALIEN_SHIRT = (.55, .9, .5), (.5, .25, .7)
CAVE, CAVE_SHIRT = (.72, .5, .32), (.75, .45, .15)


def _lesson_card(img, n, name, bites=0):
    img[:] = (.35, .22, .1)
    rect(img, 6, 10, 122, 112, (.1, .25, .15))
    words(img, f"LESSON {n}:", 24, (.9, .9, .85), shadow=None)
    words(img, name, 40, (.9, .9, .85), scale=2, shadow=None)
    for k in range(bites):                          # someone has been at it
        for j in range(4):
            ellipse(img, 122 - k * 34 - j * 8, 11 + (j % 2) * 2, 8, 8, (.05, .03, .02))


def _alien(img, x, base, t, h=52, **kw):
    kw.setdefault("look", (1, 0))
    return toon(img, x, base, h, ALIEN, ALIEN_SHIRT, t, headr=h * 0.2, pants=ALIEN_SHIRT, seed=6, **kw)


def _caveman(img, x, base, t, h=52, **kw):
    kw.setdefault("look", (-1, 0))
    hx, hy, r = toon(img, x, base, h, CAVE, CAVE_SHIRT, t, pants=(.6, .35, .12), seed=5, **kw)
    rot = kw.get("rot", 0.0)
    c, s = math.cos(rot), math.sin(rot)
    line(img, hx - r * 0.7 * c + r * 0.45 * s, hy - r * 0.7 * s - r * 0.45 * c, hx + r * 0.7 * c + r * 0.45 * s,
         hy + r * 0.7 * s - r * 0.45 * c, (.15, .08, .05), w=2)
    ellipse(img, hx - r * 0.3, hy - r * 1.0, r * 0.9, r * 0.35, (.2, .1, .05), rot=rot)
    return hx, hy, r


def _spoon(img, x, y, ang=-1.2, s=1.0):
    ex, ey = x + math.cos(ang) * 9 * s, y + math.sin(ang) * 9 * s
    line(img, x, y, ex, ey, (.8, .8, .85), w=1.6)
    ellipse(img, ex + math.cos(ang) * 2.5, ey + math.sin(ang) * 2.5, 3, 2, (.85, .85, .9), rot=ang)


def _bowl(img, x, y, r=8):
    ellipse(img, x, y, r, r * 0.7, (.55, .35, .2), half="bottom")
    ellipse(img, x, y, r, r * 0.22, (.85, .6, .3))


class Spoon(Show):
    """Silent, in stop motion: an alien teaches the spoon; it goes down well."""
    num, title, length = 613, "LESSON 19", 10.5
    G, H, P, C = 108, 52, 32, 96

    def __init__(self):
        rng = np.random.default_rng(613)
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.2, .2, .35), (.1, .08, .18))
        for _ in range(24):
            ellipse(self.bg, rng.uniform(0, N), rng.uniform(0, 80), rng.uniform(4, 12), rng.uniform(3, 8),
                    (.26, .25, .42), a=0.6)
        self.bg[self.G - 6:] = (.22, .2, .3)
        ellipse(self.bg, 60, self.G - 6, 13, 7, (.45, .43, .5), half="top")

    def draw(self, img, t):
        t = _stop(t)
        if t < 1.4 or t >= 9.0:
            _lesson_card(img, 19, "THE SPOON", bites=2 if t >= 9.0 else 0)
            if t < 1.4:
                _spoon(img, 64, 84, ang=-0.3, s=2.2)
            return
        img[:] = self.bg
        base = self.G - LEG * self.H
        pa, ca, pm, cm, ptalk, ctalk, plook, clook = (0.3, 0.9), (0.3, 0.3), 0, 0, 0.0, 0.0, (1, 0), (-1, 0)
        bowl = None
        bowl = (60, self.G - 13)
        if t < 2.8:                                 # scoop, sip, mmm
            up = (t - 1.4) % 0.75 > 0.375
            pa = (0.3, 2.9 if up else 0.9)
            pm, ptalk = 1, 0.3 if up else 0
        elif t < 3.6:
            pa, ca = (0.3, 1.6), (_lerp(0.3, 1.6, _u(t, 2.8, 3.2)), 0.3)
        elif t < 4.6:
            ca, clook = (2.4 if t < 4.2 else 3.0, 0.3), (-1, -1)
            ctalk = 1.0 if t >= 4.2 else 0
        elif t < 5.4:
            ctalk, cm, plook, ptalk = (int(t * 8) % 2) * 0.5, 1, (1, 0), 0.8
        elif t < 6.2:                               # perhaps the bowl
            pa = (0.3, 1.2)
            u = _u(t, 5.4, 5.9)
            bowl = (_lerp(60, 74, u), _lerp(self.G - 13, 72, u))
            ca = (_lerp(0.3, 1.6, u), 0.3)
            if t >= 5.9:
                ca, ctalk = (3.0, 0.3), 1.0
                bowl = None
        elif t < 7.0:
            bowl, ctalk, cm, ptalk = None, (int(t * 8) % 2) * 0.5, 1, 0.8
        elif t < 8.0:
            bowl, pa, pm, plook = None, (0.3, 3.0), -1, (0, 1)
            cm = 1
        else:
            bowl, pa, pm, plook, cm, ca = None, (0.3, 3.0), -1, (0, 1), 1, (0.3, 2.7)
        if bowl:
            _bowl(img, *bowl)
        phx, phy, pr = _alien(img, self.P, base, t, arms=pa, mood=pm, talk=ptalk, look=plook)
        chx, chy, cr = _caveman(img, self.C, base, t, arms=ca, mood=cm, talk=ctalk, look=clook)
        if t < 2.8:
            sx, sy = hand(self.P, base, self.H, pa[1], 1)
            _spoon(img, sx, sy, ang=-2.2 if pa[1] > 2 else 0.9)
        elif t < 3.6:
            u = _u(t, 3.0, 3.4)
            a = hand(self.P, base, self.H, 1.6, 1)
            b = hand(self.C, base, self.H, ca[0], -1)
            _spoon(img, _lerp(a[0], b[0], u), _lerp(a[1], b[1], u), ang=-0.4)
        elif t < 4.2:
            sx, sy = hand(self.C, base, self.H, ca[0], -1)
            _spoon(img, sx, sy, ang=-0.2 if t < 3.9 else -1.6)
        elif t < 4.4:
            _spoon(img, chx - 2, chy + cr * 0.5, ang=0.4, s=0.5)
        if 5.9 <= t < 6.2:
            _bowl(img, chx - 4, chy + cr * 0.4, 6)
        if 4.6 <= t < 5.4 or 6.2 <= t < 7.0:       # crunch
            for k in range(3):
                v = (t * 2 + k / 3) % 1
                ellipse(img, chx - 3 + k * 3 - 4 * v, chy + cr + 20 * v * v, 1.2, 1.2,
                        (.8, .8, .85) if t < 6 else (.55, .35, .2))
        if t >= 8.3:
            _bubble(img, chx - 10, chy - cr - 24, "MORE?")


class Balloon(Show):
    """Silent, in stop motion: an alien teaches the balloon; it goes up well."""
    num, title, length = 685, "LESSON 52", 10.0
    G, H, P, C = 108, 52, 32, 96
    RED = (.95, .15, .2)

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.35, .65, 1), (.75, .9, 1), 0, self.G - 6)
        self.bg[self.G - 6:] = (.4, .65, .2)
        for x, y, r in ((14, self.G - 6, 9), (118, self.G - 6, 7)):
            ellipse(self.bg, x, y, r, r * 0.6, (.6, .58, .55), half="top")
        for cx, cy in ((22, 24), (70, 14)):
            for dx in (-7, 0, 7):
                ellipse(self.bg, cx + dx, cy - (dx == 0) * 3, 8, 5, (.97, .97, 1))

    def _balloon(self, img, x, y, r, sx=None, sy=None):
        if sx is not None:
            line(img, sx, sy, x, y + r, (.3, .3, .3), w=1)
        ellipse(img, x, y, r, r * 1.15, self.RED)
        ellipse(img, x - r * 0.35, y - r * 0.45, r * 0.22, r * 0.3, (1, .6, .6))
        poly(img, [(x - 1.5, y + r * 1.15 + 2), (x + 1.5, y + r * 1.15 + 2), (x, y + r * 1.1)], self.RED)

    def draw(self, img, t):
        t = _stop(t)
        if t < 1.4:
            _lesson_card(img, 52, "THE BALLOON")
            self._balloon(img, 64, 94, 6, 64, 108)
            return
        img[:] = self.bg
        base = self.G - LEG * self.H
        pa, ca, pm, cm, ptalk, ctalk, plook, clook = (0.3, 0.3), (0.3, 0.3), 0, 0, 0.0, 0.0, (1, 0), (-1, 0)
        prot, py, cy, pflat = 0.0, base, base, 1.0
        mine = None                                 # the alien's balloon (x, y, r, string from)
        theirs = None
        if t < 2.8:                                 # puff, puff, puff
            n = min(3, int((t - 1.4) / 0.45) + 1)
            pa, ptalk = (2.7, 2.7), 0.4
            mine = (self.P + 12 + 3 * n, 64 - n, 2 + 2.4 * n, None)
        elif t < 3.4:
            pa, pm = (0.3, 2.6), 1
        elif t < 4.0:
            pa, ca, pm = (0.3, 2.6), (1.6, 0.3), 1
        elif t < 6.0:                               # the caveman has a go
            pa, pm, plook = (0.3, 2.6), 0, (1, -1)
            n = int((t - 4.0) / 0.25) + 1
            ca, ctalk = (2.6, 0.3), 0.4
            theirs = (self.C - 14 - (3 + 3.2 * n), 62 - 2.4 * n, 3 + 3.2 * n)
            if t > 5.0:
                prot, pm = -0.25, -1
        if 2.8 <= t < 5.6:
            hx, hy = hand(self.P, base, self.H, 2.6, 1, prot)
            mine = (hx + 2, hy - 18, 8.8, (hx, hy))
        if t >= 6.0:                                # up, up and away
            u = t - 6.0
            lift = 0 if u < 0.3 else (u - 0.3) * 60 + 40 * (u - 0.3) ** 2
            cy = base - lift
            ca, cm, clook = (3.0, 3.0), 1, (0, -1)
            if u >= 0.4:
                py = cy + self.H * 0.95 if u > 0.6 else base - (u - 0.4) * 20
                pa, pm, ptalk, plook = (2.9, 2.9), -1, 0.8, (0, -1)
            if lift < 260:
                theirs = (self.C, cy - self.H - 30, 26)
        if t >= 5.6 and t < 8.0:                    # the alien let go of his
            u = t - 5.6
            mine = (self.P + 20 + 6 * u, 40 - 26 * u, 8.8, (self.P + 18 + 6 * u, 60 - 26 * u))
        if t >= 8.0:                                # what goes up
            u = _u(t, 8.25, 8.65)
            if u < 1:
                py = -60 + (base + 60) * u * u
                cy = py - 70
                pa, ca, pm, cm, plook, clook, ptalk, ctalk = (2.9, 2.9), (2.9, 2.9), -1, -1, (0, -1), (0, -1), 0.8, 0.8
            else:
                pflat, py, cy = 0.4, self.G - LEG * self.H * 0.4, base - 20
                pa, ca, pm, cm, plook, clook, ptalk, ctalk = (1.5, 1.5), (0.3, 2.7), -1, 1, (0, 0), (-1, 0), 0, 0
        if theirs:
            x, y, r = theirs
            self._balloon(img, x, y, r)
        if mine:
            x, y, r, sfrom = mine
            self._balloon(img, x, y, r, *(sfrom or (None, None)))
        if 3.4 <= t < 4.2:                          # a fresh one, for you
            hx2, hy2 = hand(self.C, base, self.H, 1.6, -1)
            u = _u(t, 3.4, 3.9)
            ellipse(img, _lerp(self.P + 18, hx2, u), _lerp(80, hy2, u) - 2, 3, 4.5, self.RED, rot=0.6)
        if 8.0 <= t < 8.25:
            star(img, 64, 8, 14, (1, .9, .2), n=10)
            draw.text(img, "POP", 64, 4, (.8, .1, .1), center=True)
        _alien(img, self.P if t < 6.4 else self.C, py, t, arms=pa, mood=pm, talk=ptalk, look=plook, rot=prot,
               flat=pflat)
        hx, hy, r = _caveman(img, self.C, cy, t, arms=ca, mood=cm, talk=ctalk, look=clook)
        if t >= 8.65:
            ellipse(img, hx, hy - r * 1.1, r * 0.8, r * 0.35, self.RED)
            _dizzy(img, self.C, self.G - 12, t, 14)


# ---------------------------------------------------------------- 619 egg band

class EggBand(Show):
    """Silent: a boy band of eggs, one always a beat behind, until he hatches into the best dancer."""
    num, title, length = 619, "SUNNY SIDE", 10.0
    XS = (22, 50, 78, 106)
    BASE = 96
    BEAT = 0.5
    SHELL = (.95, .9, .8)

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.2, .02, .3), (.05, .0, .12), 0, 92)
        tile = ((X // 16 + Y // 8) % 2)[92:]
        self.floors = []
        for c0, c1 in (((.9, .1, .6), (.15, .6, .95)), ((.15, .6, .95), (.9, .1, .6))):
            f = np.where(tile[..., None] > 0, np.array(c0, np.float32), np.array(c1, np.float32))
            self.floors.append(f * (0.55 + 0.45 * np.linspace(0, 1, N - 92)[:, None, None]).astype(np.float32))

    def _egg(self, img, x, move, u, t, look=0.0, crack=0.0, squash=1.0, lift=0.0, chick=False):
        rot, sx, hop = 0.0, 1.0, 0.0
        s = math.sin(math.pi * u)
        if move == 0:
            hop = 8 * s
        elif move == 1:
            rot = -0.4 * s
        elif move == 2:
            rot = 0.4 * s
        elif move == 3:
            sx = math.cos(2 * math.pi * u)
        by = self.BASE - hop - lift
        c, sn = math.cos(rot), math.sin(rot)

        def at(dx, dy):
            return x + dx * c - dy * sn, by + dx * sn + dy * c

        for k in (-1, 1):                           # little legs
            line(img, *at(k * 4, -2), *at(k * 5, 4), (1, .6, .1), w=2)
            ellipse(img, *at(k * 6, 5), 3, 1.5, (1, .6, .1))
        if chick:
            ellipse(img, *at(0, -19), 12, 12, (1, .85, .15))
            for k in (-1, 1):
                ellipse(img, *at(k * 11, -16 - 3 * abs(math.sin(t * 12))), 4, 2.5, (1, .8, .1))
            poly(img, [at(-3, -15), at(3, -15), at(0, -11)], (1, .5, .1))
            gx, gy = at(look, -22)
            rect(img, gx - 10, gy - 2, gx + 10, gy + 1, BLACK)
            for k in (-1, 1):
                ellipse(img, gx + k * 5, gy + 1, 4.5, 3, BLACK)
            for k in (-1, 1):
                line(img, *at(k * 1, -30), *at(k * 3, -35), (1, .85, .15), w=1.5)
            ellipse(img, *at(0, -6), 13, 9, self.SHELL, half="bottom")
            for k in range(5):
                poly(img, [at(-13 + k * 6.5, -6), at(-9.75 + k * 6.5, -11), at(-6.5 + k * 6.5, -6)], self.SHELL)
            return
        rx, ry = 12 * abs(sx) + 0.5, 16 * squash
        cy = -ry
        ellipse(img, *at(0, cy), rx, ry, self.SHELL, rot=rot)
        ellipse(img, *at(-rx * 0.4, cy - ry * 0.5), rx * 0.2, ry * 0.18, WHITE, rot=rot, a=0.6)
        if sx > 0:                                  # facing us: shades
            gx, gy = at(look * sx, cy - 4)
            w = 10 * sx
            line(img, gx - w, gy, gx + w, gy, BLACK, w=2)
            for k in (-1, 1):
                ellipse(img, gx + k * w * 0.45, gy + 1.5, 4 * sx + 0.3, 3, BLACK, rot=rot)
            line(img, *at(-4 * sx, cy + 5), *at(4 * sx, cy + 6), (.4, .2, .1), w=1.2)
        if crack > 0:
            pts = [at(-rx, cy + 1), at(-rx * 0.5, cy - 3), at(0, cy + 2), at(rx * 0.5, cy - 3), at(rx, cy + 1)]
            n = max(1, int(round(crack * 4)))
            for p, q in zip(pts[:n], pts[1:n + 1]):
                line(img, *p, *q, (.3, .2, .1), w=1.2)

    def draw(self, img, t):
        b = int(t / self.BEAT)
        u = (t / self.BEAT) % 1
        img[:] = self.bg
        img[92:] = self.floors[b % 2]
        for k in range(6):                          # lights from the disco ball
            a = 0.6 + k * 0.38 + 0.25 * math.sin(t * 1.3 + k)
            line(img, 34, 10, 34 + 140 * math.cos(a), 10 + 140 * math.sin(a),
                 [(1, .3, .7), (.3, .8, 1), (1, .9, .3)][k % 3], w=3, a=0.25)
        ellipse(img, 34, 10, 7, 7, (.6, .6, .7))
        for k in range(4):
            ellipse(img, 31 + (k % 2) * 5, 7 + (k // 2) * 5, 1.2, 1.2, WHITE, a=0.5 + 0.5 * math.sin(t * 9 + k))
        for k, x in enumerate(self.XS):
            if t < 6.0:
                mb = b - 1 if k == 3 else b
                self._egg(img, x, (mb % 4) if mb >= 0 else -1, u, t)
            elif t < 7.0:                           # they notice
                if k < 3:
                    self._egg(img, x, -1, 0, t, look=4)
                else:
                    self._egg(img, x, 3 if t < 6.5 else -1, u if t < 6.5 else 0, t, look=-4 if t > 6.5 else 0)
                    if t > 6.6:
                        ellipse(img, x + 12, self.BASE - 30, 1.6, 2.4, (.5, .8, 1))
            elif t < 7.8:                           # the big finish
                v = (t - 7.0) / 0.8
                lift = 30 * math.sin(math.pi * min(1.0, v * 1.4)) if v > 0.15 else 0
                sq = 0.8 if v < 0.15 or v > 0.85 else 1.0
                self._egg(img, x, -1, 0, t, squash=sq, lift=lift, crack=(v - 0.8) * 5 if k == 3 and v > 0.8 else 0)
            elif k < 3:
                self._egg(img, x, (b % 4) if t > 8.3 else -1, u if t > 8.3 else 0, t, look=0 if t > 8.3 else 4)
            else:
                v = t - 7.8
                if v < 0.5:                         # the top comes off
                    self._egg(img, x, -1, 0, t, chick=True, lift=-6 + 12 * min(1, v * 3))
                    tx, ty = x + 30 * v, self.BASE - 22 - 60 * v + 80 * v * v
                    ellipse(img, tx, ty, 12, 8, self.SHELL, rot=v * 8, half="top")
                else:
                    self._egg(img, x, (b % 4) if t > 8.3 else -1, u if t > 8.3 else 0, t, chick=True, lift=6)
        for k in range(3):                          # notes
            ny = 90 - ((t * 16 + k * 30) % 80)
            nx = 12 + k * 46 + 6 * math.sin(t * 2 + k)
            ellipse(img, nx, ny, 2.5, 2, (1, .9, .4), rot=-0.4)
            line(img, nx + 2, ny, nx + 2, ny - 7, (1, .9, .4), w=1)
        if 0.3 < t < 3.8:                           # the music-video credit
            rect(img, 0, 104, 76, 126, BLACK, a=0.6)
            draw.text(img, "THE EGGS", 4, 104, WHITE)
            draw.text(img, "'OVER EASY'", 4, 115, (1, .85, .3))


# ---------------------------------------------------------------- 625 snails

class Snails(Show):
    """Silent, in stop motion: a snail race, lap one of forty, until the third snail goes."""
    num, title, length = 625, "SNAIL RACE", 10.0
    LANES = (68, 96, 124)
    COLS = ((.85, .45, .15), (.3, .5, .9), (.9, .2, .25))
    CROWD = (22, 42)

    def __init__(self):
        rng = np.random.default_rng(625)
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.4, .7, 1), (.7, .85, 1), 0, 22)
        self.bg[22:44] = (.35, .35, .4)
        for _ in range(60):
            ellipse(self.bg, rng.uniform(0, N), rng.uniform(27, 40), 2.2, 2.2, SKINS[rng.integers(0, 6)])
        self.bg[44:] = (.65, .35, .25)
        for y in (44, 72, 100):
            self.bg[y:y + 2] = (.95, .95, .9)
        check = (((X // 4) + (Y // 4)) % 2)[..., None]
        fin = np.where(check > 0, np.array((.95, .95, .95), np.float32), np.array((.05, .05, .05), np.float32))
        self.bg[46:, 110:118] = fin[46:, 110:118]
        self.bg[46:, 16:18] = (.95, .95, .9)
        self.crowd = self.bg[self.CROWD[0]:self.CROWD[1]].copy()

    def _snail(self, img, x, y, col, t, spin=0.0, blown=0.0, back=False):
        d = -1 if back else 1
        ellipse(img, x, y - 1, 17, 4.5, (.8, .85, .55))
        for k in (-1, 1):
            ex, ey = x + d * (15 - blown * 16) + k * 2, y - 15 + blown * 8
            line(img, x + d * 12, y - 2, ex, ey, (.8, .85, .55), w=2)
            ellipse(img, ex, ey, 2.2, 2.2, BLACK)
        cx, cy = x - d * 3, y - 11
        ellipse(img, cx, cy, 11, 10, col)
        ellipse(img, cx, cy, 7, 6.5, tuple(c * 0.7 for c in col))
        ellipse(img, cx, cy, 3.5, 3.2, col)
        line(img, cx, cy, cx + 10 * math.cos(spin), cy + 9 * math.sin(spin), tuple(c * 0.5 for c in col), w=1.5)

    def draw(self, img, t):
        t = _stop(t)
        img[:] = self.bg
        w = (t * 50) % 200 - 30                     # the crowd does the wave
        x0, x1 = max(0, int(w)), min(N, int(w) + 24)
        if x1 > x0:
            img[self.CROWD[0] - 4:self.CROWD[1] - 4, x0:x1] = self.crowd[:, x0:x1]
            img[self.CROWD[1] - 4:self.CROWD[1], x0:x1] = (.35, .35, .4)
        go = t >= 4.5
        dist = (t - 4.5) * 2616 if go else 0       # a third of the screen further each frame, plus two laps
        lap = min(40, 1 + int(dist / 140))
        done = dist > 39 * 140 + 70
        blown = 0.0 if not go else (1.0 if not done else max(0.0, 1 - (t - 6.5) * 2))
        for k in range(2):
            x = 32 + 2 * min(t, 4.5) - 4 * (go and not done)
            dazed = done and t > 7.0
            self._snail(img, x, self.LANES[k], self.COLS[k], t, spin=t * 30 * blown + k, blown=blown, back=dazed)
            if dazed:
                _dizzy(img, x - 3, self.LANES[k] - 24, t + k, 7)
        y = self.LANES[2]
        if not go:
            crouch = 2 if t > 3.6 else 0
            self._snail(img, 32 - crouch, y, self.COLS[2], t)
            if t > 3.6:
                for k in range(3):
                    line(img, 12, y - 14 + k * 5, 6, y - 14 + k * 5, (.95, .95, .95), w=1)
        elif not done:
            x = (32 + dist) % 140 - 6
            for k in range(6):                      # a flaming blur
                ellipse(img, x - 10 - k * 10, y - 6, 9 - k, 5, (1, .3 + .1 * k, .1), a=0.8 - k * 0.12)
            ellipse(img, x, y - 7, 18, 9, self.COLS[2])
            line(img, x - 70, y - 18, x - 4, y - 18, WHITE, w=1, a=0.7)
            line(img, x - 80, y + 2, x - 10, y + 2, WHITE, w=1, a=0.7)
        else:
            self._snail(img, 100, y, self.COLS[2], t)
            for k in range(3):                      # smoke
                v = (t * 1.3 + k * 0.33) % 1
                ellipse(img, 86 - k * 5, y - 14 - v * 24, 2 + 3 * v, 2 + 3 * v, (.8, .8, .8), a=0.7 - 0.6 * v)
        rect(img, 2, 2, 74, 14, BLACK)
        draw.text(img, f"LAP {lap} OF 40", 38, 3, (1, .85, .2), center=True)


# ---------------------------------------------------------------- 631 trailer

def _bendy(img, x, gy, h, bend, skin, shirt, pants, t, arms=(0.3, 0.3), mood=0, look=(0, 0), talk=0.0):
    """A person with knees, feet at gy: bend 0 stands, 1.3 is a deep squat, knees out."""
    L = h * LEG / 2
    w = max(1.5, h * 0.09)
    hy = gy - 2 * L * math.cos(bend)
    for k in (-1, 1):
        fx = x + k * h * 0.12
        kx, ky = fx + k * L * math.sin(bend), gy - L * math.cos(bend)
        line(img, fx, gy, kx, ky, pants, w)
        line(img, kx, ky, x + k * h * 0.05, hy, pants, w)
        ellipse(img, fx + k * 2, gy, w, w * 0.6, (.1, .1, .1))
    sy = hy - h * 0.3
    for k, a in zip((-1, 1), arms):
        ex, ey = x + k * h * 0.12 + k * math.sin(a) * h * 0.28, sy + math.cos(a) * h * 0.28
        line(img, x + k * h * 0.12, sy, ex, ey, shirt, w * 0.85)
        ellipse(img, ex, ey, w * 0.7, w * 0.7, skin)
    ellipse(img, x, hy - h * 0.17, h * 0.15, h * 0.2, shirt)
    r = h * 0.14
    face(img, x, hy - h * 0.34 - r * 1.05, r, skin, t, mood=mood, look=look, talk=talk, seed=2.5)
    return x, hy - h * 0.34 - r * 1.05, r


class Knees(Show):
    """Silent but for the voice-over: in a world without knees, one man dares to bend."""
    num, title, length = 631, "KNEES", 10.5
    G = 104

    def __init__(self):
        self.sky = np.empty((N, N, 3), np.float32)
        vgrad(self.sky, (.35, .1, .3), (1, .55, .2), 14, 92)
        self.sky[92:] = (.25, .15, .12)
        ellipse(self.sky, 92, 92, 18, 18, (1, .85, .4), half="top")

    def _bars(self, img, s=""):
        rect(img, 0, 0, N, 14, BLACK)
        rect(img, 0, 114, N, N, BLACK)
        if s:
            draw.text(img, s, 64, 116, (.95, .9, .8), center=True)

    def draw(self, img, t):
        i, s, lt = cue(t, [(0, "IN A WORLD..."), (2.2, "WITHOUT KNEES"), (4.6, "ONE MAN"), (6.2, "DARES TO BEND"),
                           (7.8, "THIS SUMMER")])
        if i == 0:
            img[:] = 0
            k = min(1.0, lt / 0.8) * min(1.0, (2.2 - t) / 0.4)
            words(img, s, 58, (k * .95, k * .9, k * .8), shadow=None)
            return
        if i < 4:
            img[:] = self.sky
        else:                                       # it all goes off
            rays(img, 64, 64, (1, .45, .05), (.85, .15, .05), n=14, rot=lt * 0.4)
            ellipse(img, 64, 70, 60, 50, (1, .75, .2), a=0.4)
        if i == 1:
            for k in range(5):                      # the kneeless, waddling
                x = -30 + k * 34 + lt * 14
                toon(img, x, self.G - 6 - LEG * 40, 40, SKINS[k % 6], [(.3, .3, .5), (.5, .3, .3), (.3, .5, .3)][k % 3],
                     t, rot=0.17 * math.sin(t * 7 + k * 1.3), seed=k, look=(1, 0))
        elif i >= 2:
            bend = 0.0 if i == 2 else _ease(_u(lt, 0.3, 1.4)) * 1.15 if i == 3 else 1.15
            arms = (0.25, 0.25) if i < 4 else (2.8, 2.8)
            if i == 3:
                for k, x in enumerate((14, 114)):
                    toon(img, x, self.G - 6 - LEG * 34, 34, SKINS[k + 2], (.4, .3, .5), t, talk=1.0 * (lt > 0.8),
                         arms=(2.9, 2.9) if lt > 0.8 else (0.3, 0.3), look=(1 if k == 0 else -1, 0), seed=k)
            _bendy(img, 64, self.G + 2, 74 if i < 4 else 60, bend, SKINS[1], (.2, .25, .3), (.15, .15, .2), t, arms=arms,
                   mood=1 if i == 4 else 0, look=(0, 0), talk=0)
            if i == 4:
                words(img, "KNEES", 18, (1, .95, .7), scale=3, shadow=(.3, 0, 0))
        self._bars(img, s)


# ---------------------------------------------------------------- 637 screensaver

class Screensaver(Show):
    """Silent: the bouncing lines become a face, look around, and pretend nothing happened when the mouse moves."""
    num, title, length = 637, "SCREENSAVER", 9.0
    COLS = ((.2, 1, .9), (1, .3, .9), (1, .9, .2))
    EYES = ((42, 48), (86, 48))

    def __init__(self):
        rng = np.random.default_rng(637)
        self.p0 = rng.uniform(8, 120, (3, 4, 2))
        self.v = rng.uniform(25, 55, (3, 4, 2)) * rng.choice((-1, 1), (3, 4, 2))

    def _face(self, t):
        look = 6 * math.sin((t - 4.0) * 4) if 4.0 < t < 5.5 else (8 if t >= 5.6 else 0)
        blink = 0.15 if 3.9 < t < 4.05 else 1.0
        wide = 1.4 if t >= 5.6 else 1.0
        out = []
        for ex, ey in self.EYES:
            r = 11 * wide
            out.append([(ex + look - r, ey), (ex + look, ey - 1.5 * r * blink), (ex + look + r, ey),
                        (ex + look, ey + 1.5 * r * blink)])
        smile = 0 if t >= 5.6 else 1
        out.append([(36, 80), (64, 84 + 10 * smile), (92, 80), (64, 92 + 2 * (1 - smile) + 6 * smile)] if smile else
                   [(54, 82), (64, 74), (74, 82), (64, 92)])
        return np.array(out, np.float32)

    def _shape(self, t):
        p = self.p0 + self.v * t
        p = np.abs((p - 6) % 228 - 114) + 6         # bouncing off the edges
        m = _ease(_u(t, 2.5, 3.7)) if t < 6.3 else 1 - _u(t, 6.3, 6.45)
        if m > 0:
            p = p + (self._face(t) - p) * m
        if 7.9 < t < 8.5:                           # a wink, for you
            w = math.sin(math.pi * _u(t, 7.9, 8.5))
            tgt = np.array([(52, 50), (64, 47), (76, 50), (64, 49)], np.float32)
            p[0] = p[0] + (tgt - p[0]) * w
        return p

    def draw(self, img, t):
        img[:] = (0.0, 0.0, 0.02)
        for k in range(4, 0, -1):                   # the trails
            p = self._shape(t - k * 0.06)
            xs, ys = [], []
            for s in range(3):
                for i in range(4):
                    a, b = p[s, i], p[s, (i + 1) % 4]
                    sx, sy = draw.segment(a[0], a[1], b[0], b[1], 0.7)
                    xs.append(sx)
                    ys.append(sy)
            cols = np.concatenate([np.repeat([np.asarray(self.COLS[s], np.float32) * (0.55 - k * 0.11)],
                                             len(xs[s * 4 + i]), 0) for s in range(3) for i in range(4)])
            draw.plot(img, np.concatenate(xs), np.concatenate(ys), cols, op="max")
        p = self._shape(t)
        for s in range(3):
            for i in range(4):
                a, b = p[s, i], p[s, (i + 1) % 4]
                line(img, a[0], a[1], b[0], b[1], self.COLS[s], w=1.4)
        if 5.2 < t < 6.6:                           # someone touched the mouse
            u = _ease(_u(t, 5.2, 5.6))
            mx, my = _lerp(140, 98, u), _lerp(140, 104, u)
            poly(img, [(mx, my), (mx, my + 14), (mx + 4, my + 10), (mx + 7, my + 16), (mx + 9, my + 15),
                       (mx + 6, my + 9), (mx + 11, my + 9)], WHITE)


# ---------------------------------------------------------------- 643 a long cat

class LongCat(Show):
    """Silent: a cat walks past. It takes all day. And night. Then it comes round again."""
    num, title, length = 643, "CAT", 10.0
    V = 50.0
    BODY = (.95, .55, .15)
    STRIPE = (.75, .35, .08)
    TOP, BOT = 70, 90
    FLOOR = 104

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        self.bg[:] = (.55, .7, .55)
        self.bg[(X.astype(int) // 6) % 2 == 0] = (.5, .65, .5)
        self.bg[self.FLOOR:] = (.5, .32, .2)
        self.bg[self.FLOOR:self.FLOOR + 2] = (.35, .22, .12)
        rect(self.bg, 14, 14, 50, 50, (.95, .95, .9))
        rect(self.bg, 34, 54, 90, 58, (.4, .25, .15))       # a shelf, with a plant
        rect(self.bg, 72, 46, 80, 54, (.75, .35, .2))
        for k in range(3):
            ellipse(self.bg, 76 + (k - 1) * 4, 42 - (k == 1) * 3, 3, 5, (.2, .6, .25), rot=(k - 1) * 0.5)

    def _window(self, img, t):
        ph = (t / self.length) * 2 * math.pi       # one day per clip
        day = 0.5 + 0.5 * math.cos(ph)
        sky = np.array((.1 + .4 * day, .1 + .6 * day, .3 + .65 * day), np.float32)
        img[16:48, 16:48] = sky
        a = ph - math.pi / 2
        bx, by = 32 + 22 * math.cos(a), 44 + 26 * math.sin(a)
        if day > 0.4:
            ellipse(img, bx, by, 5, 5, (1, .85, .3))
        else:
            ellipse(img, 32 - 22 * math.cos(a), 44 - 26 * math.sin(a), 4, 4, (.9, .9, .8))
        rect(img, 12, 12, 52, 16, (.95, .95, .9))
        rect(img, 12, 48, 52, 52, (.95, .95, .9))
        rect(img, 12, 12, 16, 52, (.95, .95, .9))
        rect(img, 48, 12, 52, 52, (.95, .95, .9))
        rect(img, 31, 16, 33, 48, (.95, .95, .9))
        rect(img, 16, 31, 48, 33, (.95, .95, .9))
        # and a clock, going round
        ellipse(img, 106, 64, 9, 9, (.95, .95, .85))
        a1, a2 = t * 6, t * 0.5
        line(img, 106, 64, 106 + 7 * math.sin(a1), 64 - 7 * math.cos(a1), BLACK, w=1)
        line(img, 106, 64, 106 + 5 * math.sin(a2), 64 - 5 * math.cos(a2), BLACK, w=1.5)

    def _head(self, img, x, t):
        y = self.TOP - 2
        for k in (-1, 1):
            poly(img, [(x - 2 + k * 8, y - 8), (x + k * 12, y - 20), (x + 4 + k * 10, y - 6)], self.BODY)
        ellipse(img, x, y, 14, 12, self.BODY)
        ellipse(img, x + 5, y + 4, 7, 5, (1, .85, .7))
        for k in (-1, 1):
            if (t % 3.1) < 0.12:
                line(img, x + k * 5 - 2, y - 2, x + k * 5 + 2, y - 2, BLACK, w=1)
            else:
                ellipse(img, x + k * 5 + 1, y - 2, 2.2, 3, (.3, .7, .2))
                ellipse(img, x + k * 5 + 2, y - 2, 0.8, 2.4, BLACK)
        ellipse(img, x + 4, y + 3, 1.6, 1.2, (.9, .4, .5))
        for k in (-1, 1):
            line(img, x + 8, y + 4, x + 20, y + 4 + k * 3, (.95, .95, .95), w=1)

    def _legs(self, img, x, t, ph):
        for k, off in enumerate((0, 10)):
            sw = 4 * math.sin(t * 9 + k * math.pi + ph)
            line(img, x - off, self.BOT - 2, x - off + sw, self.FLOOR - 2, self.BODY, w=4)
            ellipse(img, x - off + sw, self.FLOOR - 2, 3.5, 2, self.BODY)

    def draw(self, img, t):
        img[:] = self.bg
        self._window(img, t)
        head = -10 + self.V * t
        rump = -14 + self.V * (t - 7.0)
        x0, x1 = max(0.0, rump), min(float(N), head - 6)
        if x1 > x0:
            rect(img, x0, self.TOP, x1, self.BOT, self.BODY)
            off = (self.V * t) % 12
            for sx in np.arange(-12, N + 12, 12) + off:
                if x0 <= sx and sx + 5 <= x1:
                    rect(img, sx, self.TOP, sx + 5, self.TOP + 9, self.STRIPE)
            ellipse(img, (x0 + x1) / 2, self.BOT, (x1 - x0) / 2, 2, (.8, .45, .1), half="top", a=0.0)
        if head > -20:
            self._legs(img, head - 6, t, 0)
            self._head(img, head, t)
        if rump > -30:
            ellipse(img, rump, (self.TOP + self.BOT) / 2, 10, 10, self.BODY)
            self._legs(img, rump + 8, t, 1)
            tw = 6 * math.sin(t * 4)
            pts = [(rump - 6, 76), (rump - 16, 66 + tw), (rump - 20, 52 + tw * 1.5), (rump - 16, 44 + tw * 2)]
            for p, q in zip(pts, pts[1:]):
                line(img, *p, *q, self.BODY, w=5)
        again = -10 + self.V * (t - self.length)    # here he comes again
        if again > -40:
            self._legs(img, again - 6, t, 0)
            self._head(img, again, t)
        # the dog, who has seen everything
        ex = (1 if 0.4 < t < 3 or t > 8 else 0)
        asleep = 3.6 < t < 7.4
        ellipse(img, 112, 122, 16, 12, (.5, .45, .45))
        for k in (-1, 1):
            ellipse(img, 112 + k * 14, 118, 4, 8, (.35, .3, .3), rot=k * 0.3)
            if asleep:
                line(img, 112 + k * 6 - 2.5, 117, 112 + k * 6 + 2.5, 117, BLACK, w=1.2)
            else:
                ellipse(img, 112 + k * 6, 116, 3, 3.3, WHITE)
                ellipse(img, 112 + k * 6 + ex * 1.2 - (1 - ex) * 1.2, 116, 1.5, 1.8, BLACK)
        ellipse(img, 112, 124, 3, 2, BLACK)
        if asleep:
            for k in range(3):
                v = (t * 0.8 + k / 3) % 1
                draw.text(img, "Z", 98 - v * 8, 104 - v * 22, (.95, .95, 1))


# ---------------------------------------------------------------- 649 the wrong size

class NightWalk(Show):
    """Silent: an evening stroll where everything is slightly the wrong size, especially the moon."""
    num, title, length = 649, "NIGHT WALK", 9.5
    G, H = 104, 42

    def __init__(self):
        rng = np.random.default_rng(649)
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.03, .04, .18), (.15, .1, .32), 0, self.G)
        for _ in range(40):
            draw.plot(self.bg, [rng.uniform(0, N)], [rng.uniform(0, 70)], (.6, .6, .7), op="max")
        for x0, w, h in ((0, 30, 40), (34, 24, 26), (62, 36, 48), (104, 24, 30)):
            rect(self.bg, x0, self.G - 8 - h, x0 + w, self.G - 8, (.08, .07, .14))
        for _ in range(9):
            wx, wy = rng.uniform(4, 120), rng.uniform(self.G - 50, self.G - 16)
            rect(self.bg, wx, wy, wx + 3, wy + 3, (.6, .5, .25))
        self.bg[self.G - 8:self.G] = (.3, .3, .34)
        self.bg[self.G:] = (.18, .18, .2)
        # a lamppost, ankle high
        rect(self.bg, 39, self.G - 13, 41, self.G - 4, (.5, .5, .55))
        ellipse(self.bg, 40, self.G - 14, 2.5, 2, (1, .9, .5))
        ellipse(self.bg, 40, self.G - 4, 6, 2, (1, .9, .5), a=0.3)
        # a fire hydrant, very large
        rect(self.bg, 92, self.G - 58, 120, self.G - 4, (.85, .15, .15))
        ellipse(self.bg, 106, self.G - 58, 14, 10, (.85, .15, .15), half="top")
        rect(self.bg, 86, self.G - 40, 126, self.G - 32, (.7, .1, .1))
        rect(self.bg, 88, self.G - 6, 124, self.G - 2, (.6, .08, .08))
        ellipse(self.bg, 106, self.G - 70, 4, 3, (.7, .1, .1))

    def _hat(self, img, x, y, rot=0.0):
        rect(img, x - 8, y - 1, x + 8, y + 1, (.3, .2, .12))
        rect(img, x - 5, y - 9, x + 5, y - 1, (.3, .2, .12))
        rect(img, x - 5, y - 3, x + 5, y - 1, (.7, .15, .2))

    def draw(self, img, t):
        img[:] = self.bg
        base = self.G - LEG * self.H
        x, rot, arms, look, mood, walk, yy = 70.0, 0.0, (0.3, 0.3), (1, 0), 0, 0.0, base
        moon = None                                  # (x, y, mood)
        hat_on = True
        if t < 2.6:
            x, walk = -10 + 80 * t / 2.6, 1.0
            if 1.3 < t < 1.75:                      # step over the lamppost
                yy = base - 6 * math.sin(math.pi * (t - 1.3) / 0.45)
        elif t < 3.2:
            look = (1, -1)
        if t < 3.4:
            u = _u(t, 0.8, 3.4)
            moon = (_lerp(150, 85, u), _lerp(-10, 56, math.sin(u * math.pi / 2)), 0)
        elif t < 4.4:                               # bonk
            u = t - 3.4
            rot, mood, look = -0.35 * math.exp(-u * 2) * math.cos(u * 6), -1, (0, 0)
            moon = (86 + 6 * u, 56 - 2 * u, -1)
        elif t < 5.2:
            look, mood, moon = (1, -1), 0, (92, 54 + math.sin(t * 3), -1)
        elif t < 6.4:                               # here, have a hat
            u = _u(t, 5.2, 6.2)
            arms, moon, hat_on = (0.3, _lerp(0.3, 2.4, min(1, u * 2))), (92, 54 + math.sin(t * 3), -1), False
        else:
            u = _ease(_u(t, 6.4, 8.6))
            hat_on, arms, mood, look = False, (0.3, 2.8 + 0.3 * math.sin(t * 10)), 1, (1, -1)
            moon = (_lerp(92, 34, u), _lerp(54, 18, u), 1)
        hx, hy, r = toon(img, x, yy, self.H, SKINS[0], (.25, .35, .6), t, walk=walk, rot=rot, arms=arms, look=look,
                         mood=mood, seed=7)
        if hat_on:
            self._hat(img, hx, hy - r * 0.9)
        else:
            ellipse(img, hx - 2, hy - r * 0.7, 2, 1.2, WHITE, a=0.6)
        if 3.4 <= t < 4.4:
            _dizzy(img, hx, hy - r - 4, t)
        if moon:
            mx, my, mm = moon
            ellipse(img, mx, my, 15, 15, (.95, .95, .7), a=0.15)
            face(img, mx, my, 8, (.95, .95, .75), t, mood=mm, look=(-1, 0) if mm < 1 else (1, 1), seed=9)
            ellipse(img, mx + 4, my + 5, 1.3, 1.3, (.8, .8, .6))
            if t >= 5.2:
                if t < 6.4:
                    u = _u(t, 5.2, 6.2)
                    hx2, hy2 = hx + 10 * u + (mx - hx - 10) * max(0, u * 2 - 1), hy - r * 0.9 - 8 * u + (my - 8 - hy + r * 0.9) * max(0, u * 2 - 1)
                    self._hat(img, hx2 if u < 1 else mx, hy2 if u < 1 else my - 8)
                else:
                    tip = 3 * max(0.0, math.sin((t - 8.6) * 8)) if t > 8.6 else 0
                    self._hat(img, mx, my - 8 - tip)


# ---------------------------------------------------------------- 655 test pattern

class TestPattern(Show):
    """Silent: the colour bars have eyes. The green one pops out for a coffee."""
    num, title, length = 655, "TEST PATTERN", 10.5
    COLS = [(.75, .75, .75), (.75, .75, 0), (0, .75, .75), (0, .75, 0), (.75, 0, .75), (.75, 0, 0), (0, 0, .75)]
    W = N / 7
    TOP = 84
    G = 3

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        for k, c in enumerate(self.COLS):
            x0, x1 = round(k * self.W), round((k + 1) * self.W)
            self.bg[:self.TOP, x0:x1] = c
            self.bg[self.TOP:94, x0:x1] = self.COLS[6 - k] if k % 2 == 0 else (0.05, 0.05, 0.05)
        for x0, x1, c in ((0, 23, (0, .15, .35)), (23, 46, (.75, .75, .75)), (46, 69, (.2, 0, .4)), (69, N, (.04, .04, .04))):
            self.bg[94:, x0:x1] = c
        self.bg[94:, 96:104] = (.0, .0, .0)
        self.bg[94:, 104:112] = (.1, .1, .1)
        g0, g1 = round(self.G * self.W), round((self.G + 1) * self.W)
        self.gap = (g0, g1)

    def _eyes(self, img, x, y, open_=1.0, look=(0.0, 0.0), wink=False):
        for k in (-1, 1):
            if open_ < 0.2 or (wink and k > 0):
                line(img, x + k * 4.5 - 3.5, y, x + k * 4.5 + 3.5, y, BLACK, w=1.5)
            else:
                ellipse(img, x + k * 4.5, y, 4, 4.5 * open_, (.97, .97, .97))
                ellipse(img, x + k * 4.5 + look[0] * 1.8, y + look[1] * 1.8, 2, 2.3 * open_, BLACK)

    def _bar(self, img, x, y, step, t, cup=False):
        x0 = x - self.W / 2
        rect(img, x0, y, x0 + self.W, y + self.TOP, self.COLS[self.G])
        for k in (-1, 1):
            sw = 3 * math.sin(t * 12) * k * step
            line(img, x + k * 4, y + self.TOP, x + k * 4 + sw, y + self.TOP + 10, (.0, .55, 0), w=2)
            ellipse(img, x + k * 4 + sw + k, y + self.TOP + 10, 3, 1.5, BLACK)
        if cup:
            rect(img, x - self.W / 2 - 7, y + 40, x - self.W / 2, y + 48, (.95, .95, .9))
            ellipse(img, x - self.W / 2 - 8, y + 44, 2.5, 3, (.95, .95, .9))
            for k in range(2):
                line(img, x - self.W / 2 - 5 + k * 3, y + 38, x - self.W / 2 - 4 + k * 3 + math.sin(t * 6 + k), y + 32,
                     (.8, .8, .8), w=1, a=0.6)

    def draw(self, img, t):
        img[:] = self.bg
        g0, g1 = self.gap
        gx = (g0 + g1) / 2
        out = 3.6 <= t < 9.0
        if out:
            img[:self.TOP, g0:g1] = 0.03
        if t < 2.4 or t >= 9.8:
            open_ = 0.0
        elif t < 2.9:
            open_ = _u(t, 2.4, 2.9)
        elif t >= 9.3:
            open_ = 1 - _u(t, 9.3, 9.8)
        else:
            open_ = 0.1 if 3.3 < t < 3.4 else 1.0
        if 4.2 < t < 5.6:
            look = (1, 0.4)                         # watching it go
        elif 5.6 <= t < 7.4:
            look = (math.copysign(1, math.sin(t * 5)), 0)
        elif 7.4 <= t < 9.0:
            look = (1, 0.4)
        else:
            look = (0, 0)
        for k in range(7):
            if k == self.G and (out or t >= 9.3):
                continue
            if open_ > 0:
                self._eyes(img, (k + 0.5) * self.W, 30, open_, look)
        if t >= 9.3:                                # all asleep; nearly all
            self._eyes(img, gx, 30, 1.0, (0, 0), wink=9.9 < t < 10.2)
        if out:
            if t < 4.0:                             # step out
                u = _u(t, 3.6, 4.0)
                self._bar(img, gx, 4 * u, 0, t)
                self._eyes(img, gx, 30 + 4 * u, 1, (1, 0))
            elif t < 5.6:                           # and off
                x = gx + 60 * (t - 4.0)
                self._bar(img, x, 4, 1, t)
                self._eyes(img, x, 34, 1, (1, 0))
            elif 7.4 <= t < 8.8:                    # with a coffee
                x = 160 - 60 * (t - 7.4)
                x = max(gx, x)
                self._bar(img, x, 4, 1 if x > gx else 0, t, cup=True)
                self._eyes(img, x, 34, 1, (-1, 0))
            elif t >= 8.8:
                u = _u(t, 8.8, 9.0)
                self._bar(img, gx, 4 * (1 - u), 0, t, cup=True)
                self._eyes(img, gx, 30 + 4 * (1 - u), 1, (0, 0))
        band = int((t * 30) % (N + 30)) - 30        # a slow hum bar rolling down
        img[max(0, band):max(0, band + 14)] *= 0.88


# ---------------------------------------------------------------- 661 alien home video

class Vacation(Show):
    """Silent, on tape: alien tourists pose with a man at a bus stop. He looks at the camera."""
    num, title, length = 661, "VACATION TAPE", 9.6
    G = 108
    MAN = 76

    def __init__(self):
        rng = np.random.default_rng(661)
        self.bg = np.empty((N, N, 3), np.float32)
        self.bg[:] = (.62, .32, .25)
        for row in range(0, 92, 6):
            off = 6 if (row // 6) % 2 else 0
            self.bg[row:row + 1] = (.5, .25, .2)
            for bx in range(off, N, 12):
                self.bg[row:row + 6, bx:bx + 1] = (.5, .25, .2)
        self.bg[92:] = (.6, .6, .58)
        self.bg[92:94] = (.45, .45, .44)
        rect(self.bg, 108, 30, 110, 94, (.5, .5, .55))
        ellipse(self.bg, 109, 30, 9, 9, (.15, .35, .8))
        rect(self.bg, 104, 27, 114, 33, (.95, .95, .9))
        self.noise = rng.uniform(0.2, 0.9, (8, N, 1)).astype(np.float32)
        self.buf = np.empty((N, N, 3), np.float32)
        self.cols = np.arange(N, dtype=np.float32)

    def _scene(self, img, t):
        img[:] = self.bg
        base = self.G - LEG * 56
        look = (1, 0) if t < 3.8 else (0, 0)
        man_mood = 1 if t >= 6.3 else 0
        arms = (0.3, 0.3)
        if t >= 6.3:
            arms = (0.3, 2.6 + 0.3 * math.sin(t * 9))
        hx, hy, r = toon(img, self.MAN, base, 56, SKINS[0], (.3, .3, .36), t, look=look, mood=man_mood, arms=arms,
                         talk=chatter_(t) if t >= 6.6 else 0, seed=1.7)
        bx, by = hand(self.MAN, base, 56, 0.3, -1)
        rect(img, bx - 6, by, bx + 3, by + 8, (.35, .2, .1))
        if t < 5.0:
            scream = t >= 4.6
            for k, (x, h, skin, eyes) in enumerate(((36, 46, (.7, .6, .95), 3), (56, 26, (.55, .85, .9), 1))):
                if scream:
                    x -= (t - 4.6) * 120
                    pa = (2.9, 2.9)
                elif t < 2.2:
                    pa = (2.6, 2.6 + 0.4 * math.sin(t * 10 + k))
                elif k == 1:
                    pa = (0.3, 1.5 + 0.2 * math.sin(t * 18))
                else:
                    pa = (0.3, 0.3)
                mood = 1 if not scream else 0
                talk = 1.0 if scream else (chatter_(t, k) if k == 0 and t > 2.2 else 0)
                ax, ay, ar = toon(img, x, self.G - LEG * h, h, skin, (.2, .6, .4) if k else (.9, .5, .2), t, arms=pa,
                                  seed=k + 3)
                face(img, ax, ay, ar, skin, t, talk=talk, mood=mood, eyes=eyes, look=(0, -1) if scream else (0, 0),
                     seed=k + 3)
                for s in (-1, 1):
                    line(img, ax + s * ar * 0.4, ay - ar, ax + s * ar * 0.7, ay - ar * 1.9, skin, w=1.2)
                    ellipse(img, ax + s * ar * 0.7, ay - ar * 1.9, 1.8, 1.8, (1, .9, .3))
                if k == 1 and 2.2 <= t < 4.6:     # poke, poke
                    sx, sy = hand(x, self.G - LEG * h, h, pa[1], 1)
                    line(img, sx, sy, sx + 12, sy - 2, (.5, .3, .1), w=1.5)
        return hx, hy

    def draw(self, img, t):
        if t >= 8.6:                                # STOP
            img[:] = (.05, .1, .7)
            draw.text(img, "STOP", 6, 6, WHITE)
            rect(img, 6, 18, 14, 26, WHITE)
            return
        hx, hy = self._scene(self.buf, t)
        z, cx, cy = 1.0, 64.0, 64.0
        if 3.6 <= t < 4.6:
            u = _ease(_u(t, 3.6, 4.1))
            z, cx, cy = _lerp(1, 2.8, u), _lerp(64, hx, u), _lerp(64, hy + 4, u)
        elif t >= 6.0:
            z, cx, cy = 3.0, hx, hy + 4
        dx = 1.5 * math.sin(t * 7.3) + math.sin(t * 13.1)
        dy = 1.2 * math.sin(t * 5.7 + 1) + 0.8 * math.sin(t * 11.3)
        if 4.9 <= t < 5.3:
            dx, dy = dx + 10 * math.sin(t * 40), dy + 6 * math.cos(t * 37)
        ix = np.clip((cx + dx + (self.cols - 64) / z).astype(np.int32), 0, N - 1)
        iy = np.clip((cy + dy + (self.cols - 64) / z).astype(np.int32), 0, N - 1)
        img[:] = self.buf[iy][:, ix]
        if 5.3 <= t < 6.0:                          # dropped it
            img[:] = np.rot90(img, 1)
        if t >= 7.8:                                # and off
            u = _u(t, 7.8, 8.4)
            h = max(1, int(64 * (1 - u)))
            img[:64 - h] = 0
            img[64 + h:] = 0
            if u > 0.8:
                img[:] = 0
                ellipse(img, 64, 64, 3, 2, (.8, .8, .8))
        band = int((t - 1.0) * 160) if t < 2.0 else int((t - 5.0) * 160) if 5.0 <= t < 6.0 else -1
        if 0 <= band < N - 8:
            k = int(t * 12) % 8
            img[band:band + 8] = img[band:band + 8] * 0.5 + np.roll(self.noise, k * 9, 1)[:, :, :] * 0.5
        draw.text(img, "PLAY", 4, 3, WHITE)
        poly(img, [(31, 4), (31, 12), (37, 8)], WHITE)
        draw.text(img, "JUL 04 3088", 4, 114, WHITE)


def chatter_(t, seed=0.0):
    v = math.sin(t * 15 + seed) * 0.6 + math.sin(t * 9.3 + 2 * seed) * 0.4
    return max(0.0, v) if math.sin(t * 1.7 + seed * 3) > -0.5 else 0.0


# ---------------------------------------------------------------- 667 catch

class Catch(Show):
    """Silent: the world wraps round, so a man playing catch with himself is hit from behind, then from below."""
    num, title, length = 667, "CATCH", 10.0
    G, H, X0 = 104, 44, 50
    RED = (.95, .15, .15)

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.35, .6, 1), (.75, .88, 1), 0, self.G)
        self.bg[self.G:] = (.35, .7, .25)
        for cx, cy in ((26, 22), (96, 34)):
            for dx in (-7, 0, 7):
                ellipse(self.bg, cx + dx, cy - (dx == 0) * 3, 8, 5, (.97, .97, 1))
        rng = np.random.default_rng(667)
        self.pile = []                              # a heap: wide at the bottom
        for row in range(8):
            for j in range(9 - row):
                self.pile.append(((j - (8 - row) / 2) * 7 + rng.uniform(-1, 1), row, row * 0.12 + rng.uniform(0, 0.12)))

    def _ball(self, img, x, y):
        for wx in (x, x - 136, x + 136):
            for wy in (y, y - 136, y + 136):
                if -6 < wx < N + 6 and -6 < wy < N + 6:
                    ellipse(img, wx, wy, 3.5, 3.5, self.RED)
                    ellipse(img, wx - 1, wy - 1, 1, 1, (1, .7, .7))

    def draw(self, img, t):
        img[:] = self.bg
        base = self.G - LEG * self.H
        x, y, rot, arms, look, mood, stars, mitt = float(self.X0), base, 0.0, (0.3, 0.3), (1, 0), 0, False, False
        ball = None
        hx0, hy0 = self.X0, base - self.H * 0.34 - self.H * 0.14 * 1.05     # where his head is, standing
        if t < 0.6:
            arms = (0.3, 3.0)
            ball = hand(x, y, self.H, 3.0, 1)
        elif t < 1.55:                              # off to the right... and in from the left
            arms = (0.3, 1.6)
            sx, sy = hand(x, y, self.H, 1.6, 1)
            bx = sx + 130 * (t - 0.6)
            ball = ((bx + 6) % 136 - 6, sy - 6)
        elif t < 2.6:
            u = t - 1.55
            rot, stars, mood = 0.35 * math.exp(-u * 3), True, -1
            ball = (hx0 - 6 - 20 * u, min(self.G - 4, hy0 + 60 * u * u))
        elif t < 3.2:
            look, ball = ((-1, 0) if t < 2.9 else (1, 0)), (hx0 - 26, self.G - 4)
        elif t < 3.6:
            arms = (0.3, 3.0)
            ball = hand(x, y, self.H, 3.0, 1)
        elif t < 4.5:                               # straight up... and up through the ground
            arms, look = (0.3, 3.0), (0, -1)
            sx, sy = hand(x, y, self.H, 3.0, 1)
            by = sy - 180 * (t - 3.6)
            ball = (sx, (by + 6) % 136 - 6)
            if ball[1] < hy0 + 14 and t > 4.2:
                ball = (sx, hy0 + 14)
        elif t < 5.4:
            u = t - 4.5
            rot = -2 * math.pi * min(1.0, u / 0.6)
            y = base - 30 * math.sin(math.pi * min(1.0, u / 0.6))
            stars, mood = u > 0.6, -1
            ball = (hx0 + 20 * u + 4, min(self.G - 4, hy0 - 30 + 80 * u * u))
        elif t < 6.2:                               # a plan
            mitt, look, arms = True, (-1, 0), (3.0, 1.6)
            ball = hand(x, y, self.H, 3.0, -1)
        elif t < 7.4:
            mitt, arms, look = True, (1.6, 1.6), (1, 0)
            sx, sy = hand(x, y, self.H, 1.6, -1)
            mx, my = hand(x, y, self.H, 1.6, 1)
            bx = sx - 130 * (t - 6.2)
            bx = (bx + 6) % 136 - 6
            if t > 6.9 and bx < mx + 3:
                bx = mx + 3
            ball = (bx, sy)
            if bx <= mx + 3:
                mood = 1
        else:
            mitt, arms, mood = True, (0.3, 3.0), 1
            ball = None
        hx, hy, r = toon(img, x, y, self.H, SKINS[2], (.95, .55, .1), t, rot=rot, arms=arms, look=look, mood=mood,
                         seed=4)
        if mitt:
            mx, my = hand(x, y, self.H, arms[1], 1, rot)
            ellipse(img, mx, my, 5, 5.5, (.55, .3, .12))
            if t >= 7.4:
                self._ball(img, mx, my - 5)
        if ball:
            self._ball(img, *ball)
        if stars:
            _dizzy(img, hx, hy - r - 4, t)
        if t >= 7.9:                                # every ball ever thrown, coming home
            for ox, row, d in self.pile:
                tk = 7.9 + d
                if t < tk:
                    continue
                v = t - tk
                by = min(self.G - 4 - row * 6.2, -10 + 400 * v * v)
                ellipse(img, self.X0 + ox, by, 3.6, 3.6, self.RED)
                ellipse(img, self.X0 + ox - 1, by - 1, 1, 1, (1, .7, .7))
            mx, my = hand(x, y, self.H, arms[1], 1, rot)    # still holding the one he caught
            ellipse(img, mx, my, 5, 5.5, (.55, .3, .12))
            self._ball(img, mx, my - 5)


# ---------------------------------------------------------------- 673 egg sun

class Morning(Show):
    """Silent: sunrise, sunny side up; a spatula flips it, and it's night; then the world gets salted."""
    num, title, length = 673, "GOOD MORNING", 9.5
    SX = 50

    def __init__(self):
        rng = np.random.default_rng(673)
        self.day = np.empty((N, N, 3), np.float32)
        vgrad(self.day, (.35, .65, 1), (.95, .85, .6))
        self.night = np.empty((N, N, 3), np.float32)
        vgrad(self.night, (.02, .02, .12), (.12, .05, .25))
        for _ in range(40):
            draw.plot(self.night, [rng.uniform(0, N)], [rng.uniform(0, 80)], (.8, .8, .9), op="max")
        self.hill = np.zeros((N, N, 3), np.float32)
        m = np.zeros((N, N), bool)
        m |= ((X - 30) / 70) ** 2 + ((Y - 130) / 40) ** 2 < 1
        m |= ((X - 100) / 60) ** 2 + ((Y - 136) / 46) ** 2 < 1
        self.mask = m[..., None]
        self.hill[:] = np.where(Y[..., None] > 0, np.array((.3, .7, .25), np.float32), 0)
        self.hill += _texture(673, 0.05)
        rect(self.hill, 92, 80, 110, 96, (.85, .2, .15))
        poly(self.hill, [(89, 81), (101, 70), (113, 81)], (.5, .25, .15))
        rect(self.hill, 99, 86, 104, 96, (.35, .2, .1))
        hm = np.zeros((N, N), bool)
        hm[70:96, 89:114] = True
        self.mask = self.mask | (hm[..., None] & (np.abs(self.hill - np.array((.3, .7, .25))).sum(-1, keepdims=True) > 0.2))
        self.salt = [(rng.uniform(4, 124), rng.uniform(0, 1)) for _ in range(70)]

    def _spatula(self, img, x, y, ang):
        c, s = math.cos(ang), math.sin(ang)

        def at(dx, dy):
            return x + dx * c - dy * s, y + dx * s + dy * c

        line(img, *at(16, 0), *at(80, 0), (.2, .12, .08), w=6)
        poly(img, [at(-22, -14), at(18, -10), at(18, 10), at(-22, 14)], (.75, .75, .8))
        for k in (-1, 0, 1):
            line(img, *at(-16, k * 6), *at(10, k * 5), (.5, .5, .55), w=2)

    def draw(self, img, t):
        if t < 2.5:                                 # rise
            u = _ease(t / 2.5)
            ey, flip, k = _lerp(118, 42, u), 0.0, _lerp(0.1, 1, u)
        elif t < 3.3:
            ey, flip, k = 42, 0.0, 1.0
        elif t < 4.1:                               # flip
            u = _u(t, 3.3, 4.1)
            ey, flip, k = 42 - 24 * math.sin(math.pi * u), u, 1 - _ease(_u(t, 3.6, 4.1))
        elif t < 5.8:
            ey, flip, k = 42, 1.0, 0.0
        elif t < 6.6:
            u = _u(t, 5.8, 6.6)
            ey, flip, k = 42 - 24 * math.sin(math.pi * u), 1 + u, _ease(_u(t, 6.1, 6.6))
        else:
            ey, flip, k = 42, 0.0, 1.0
        img[:] = self.night + (self.day - self.night) * k
        under = 0.5 < flip < 1.5
        ry = max(0.15, abs(math.cos(math.pi * flip)))
        for dx, dy, r in ((0, 0, 17), (-9, 4, 11), (10, 3, 12), (3, -7, 11)):
            ellipse(img, self.SX + dx, ey + dy * ry, r, r * ry, (.97, .95, .88))
        if under:
            ellipse(img, self.SX, ey, 13, 11 * ry, (.85, .7, .45))
        else:
            ellipse(img, self.SX + 1, ey - ry, 8, 8 * ry, (1, .7, .05))
            ellipse(img, self.SX - 2, ey - 3 * ry, 2.5, 2 * ry, (1, .95, .6))
        hill = self.hill * (0.3 + 0.7 * k)
        np.copyto(img, hill, where=self.mask)
        if k < 0.5:
            rect(img, 95, 84, 98, 88, (1, .85, .3))
            rect(img, 105, 84, 108, 88, (1, .85, .3))
        sp = None
        if 2.4 <= t < 4.4:
            u = _u(t, 2.4, 3.2)
            sp = (_lerp(140, self.SX + 6, _ease(u)), _lerp(-30, ey + 12, _ease(u)), -0.6 - 1.2 * _u(t, 3.3, 3.9))
            if t > 3.9:
                v = _u(t, 3.9, 4.4)
                sp = (_lerp(self.SX + 6, 150, v), _lerp(ey + 12, -40, v), -1.8)
        elif 5.4 <= t < 7.0:
            u = _u(t, 5.4, 5.8)
            sp = (_lerp(140, self.SX + 6, _ease(u)), _lerp(-30, ey + 12, _ease(u)), -0.6 - 1.2 * _u(t, 5.8, 6.4))
            if t > 6.4:
                v = _u(t, 6.4, 7.0)
                sp = (_lerp(self.SX + 6, 150, v), _lerp(ey + 12, -40, v), -1.8)
        if sp:
            self._spatula(img, *sp)
        if t >= 6.8:                                # season to taste
            u = _ease(_u(t, 6.8, 7.2))
            sx = _lerp(150, 92, u) if t < 8.8 else _lerp(92, 150, _u(t, 8.8, 9.3))
            shake = 0.4 * math.sin(t * 14) if 7.2 < t < 8.6 else 0
            c, s = math.cos(2.5 + shake), math.sin(2.5 + shake)

            def at(dx, dy):
                return sx + dx * c - dy * s, 22 + dx * s + dy * c

            poly(img, [at(-9, -14), at(9, -14), at(9, 14), at(-9, 14)], (.9, .92, .95))
            poly(img, [at(-9, -14), at(9, -14), at(7, -20), at(-7, -20)], (.6, .6, .65))
            for kk, (gx, d) in enumerate(self.salt):
                tk = 7.2 + d * 1.4
                if t < tk:
                    continue
                v = t - tk
                gy = 30 + 200 * v * v
                lx = _lerp(sx - 14, gx, min(1, v * 2))
                floor = 128 - 30 * math.exp(-((gx - 30) / 50) ** 2) - 20 * math.exp(-((gx - 100) / 40) ** 2)
                floor = min(floor, 124) - (kk % 5)
                rect(img, lx, min(gy, floor), lx + 1.6, min(gy, floor) + 1.6, (.98, .98, .98))


# ---------------------------------------------------------------- 679 tiny arms

class TinyArms(Show):
    """Silent, in stop motion: a dinosaur can't reach a high five, so the hero lends him an arm. It goes wrong."""
    num, title, length = 679, "TINY ARMS", 10.0
    GY = 104
    DINO = (.35, .7, .3)
    SUIT = (.95, .45, .1)

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.7, .6, .85), (.55, .45, .7), 0, 98)
        self.bg[98:] = (.45, .3, .2)
        rect(self.bg, 2, 20, 26, 98, (.2, .35, .75))        # a pencil cup, very big
        for k, c in enumerate(((1, .8, .2), (.9, .3, .3), (.3, .8, .4))):
            rect(self.bg, 5 + k * 7, 4 + k * 5, 10 + k * 7, 20, c)
            poly(self.bg, [(5 + k * 7, 4 + k * 5), (10 + k * 7, 4 + k * 5), (7.5 + k * 7, -2 + k * 5)], (.95, .8, .6))
        rect(self.bg, 2, 20, 26, 24, (.15, .25, .6))

    def _dino(self, img, x, gy, rot, arm, t, long_arm=False):
        x += _jit(t, 3, 0.3, 12)
        c, s = math.cos(rot), math.sin(rot)

        def at(dx, dy):
            return x + dx * c - dy * s, gy + dx * s + dy * c

        poly(img, [at(-8, -30), at(-30, -10), at(-34, -6), at(-6, -18)], self.DINO)
        for k in (-1, 1):
            ellipse(img, *at(k * 5, -7), 4.5, 8, (.25, .55, .22), rot=rot)
        ellipse(img, *at(0, -24), 13, 15, self.DINO, rot=rot)
        ellipse(img, *at(2, -20), 7, 9, (.75, .85, .5), rot=rot)
        ellipse(img, *at(10, -46), 14, 9, self.DINO, rot=rot)
        line(img, *at(10, -42), *at(23, -42), (.15, .3, .1), w=1)
        for k in range(4):
            poly(img, [at(11 + k * 3, -42), at(13 + k * 3, -42), at(12 + k * 3, -39.5)], WHITE)
        ellipse(img, *at(8, -50), 2.6, 2.6, WHITE)
        ellipse(img, *at(9, -50), 1.3, 1.5, BLACK)
        sx, sy = at(10, -30)
        if long_arm:
            ex, ey = sx + math.sin(arm) * 15, sy - math.cos(arm) * 15
            line(img, sx, sy, ex, ey, self.SUIT, w=6)
            ellipse(img, ex, ey, 3.5, 3.5, SKINS[1])
            other = at(6, -29)
            line(img, *other, other[0] + 4, other[1] + 3, self.DINO, w=2.5)
            return ex, ey
        ex, ey = sx + math.sin(arm) * 5, sy - math.cos(arm) * 5
        line(img, sx, sy, ex, ey, self.DINO, w=2.5)
        return ex, ey

    def draw(self, img, t):
        t = _stop(t, 12)
        img[:] = self.bg
        hx, arms, has, head = 96.0, (0.15, 0.15), (True, True), True
        drot, darm, dlong = 0.0, 1.0, False
        hgy = float(self.GY)
        loose_arm = loose_head = None
        if t < 1.2:
            p = t / 1.2 * 2
            hx = 150 - 27 * p
            hgy -= 8 * math.sin(math.pi * (p % 1))
        elif t < 1.8:
            arms = (2.6, 0.15)
        elif t < 3.4:                               # reach... reach...
            arms = (2.6, 0.15)
            n = min(3, int((t - 1.8) / 0.4) + 1)
            drot, darm = 0.12 * n, 2.6
            if t >= 3.0:
                drot = min(1.5, 0.36 + (t - 3.0) * 4)
        elif t < 4.0:
            arms, darm = (0.15, 0.15), 0.6
        elif t < 4.6:                               # pop
            arms, has = (0.6, 2.0), (True, False)
            lx, ly = hand(hx, 0, 1, 0, -1)
            loose_arm = (hx - 6, self.GY - 54, 0.2)
        elif t < 5.6:
            p = min(1.0, (t - 4.6) / 0.6)
            hx = 96 - 30 * p
            hgy -= 6 * math.sin(math.pi * p)
            arms, has = (1.5, 0.15), (True, False)
            u = _u(t, 5.2, 5.5)
            loose_arm = (hx - 22 + 2 * u, self.GY - 44 - 4 * u, -1.2)
        else:
            has, dlong = (True, False), True
            p = min(1.0, (t - 5.6) / 0.4)
            hx = 66 + 12 * p
            if t < 6.2:
                darm, arms = 0.6, (2.6, 0.15)
            elif t < 6.9:                           # high five!
                darm, arms = 1.0, (2.6, 0.15)
            elif t < 7.5:
                darm = 1.0 + (t - 6.9) * 14
                arms = (0.2, 0.15)
            else:
                darm, arms, head = 0.3, (2.7, 0.15), False
                v = t - 7.5
                if v < 0.7:
                    loose_head = (hx + 40 * v, self.GY - 58 - 60 * v + 110 * v * v, v * 10)
                else:
                    loose_head = (hx + 28, self.GY - 9, 1.4)
        if t >= 7.4:
            arms = (2.7, 0.15)
        _, hands = _figure(img, hx, hgy, arms, t, suit=self.SUIT, head=head, has=has, skin=SKINS[1],
                           helmet=(.2, .25, .3), j=0.3)
        if 7.4 <= t < 7.5:
            head = True
        dh = self._dino(img, 38, self.GY, drot, darm, t, dlong)
        if loose_arm:
            ax, ay, aa = loose_arm
            line(img, ax, ay, ax + math.sin(aa) * 15, ay + math.cos(aa) * 15, self.SUIT, w=6)
            ellipse(img, ax + math.sin(aa) * 15, ay + math.cos(aa) * 15, 3.5, 3.5, SKINS[1])
        if 4.0 <= t < 4.2:
            star(img, hx + 14, self.GY - 44, 7, (1, .9, .3), n=8, inner=0.4)
        if 6.4 <= t < 6.9:
            mx, my = (dh[0] + hands[0][0]) / 2, (dh[1] + hands[0][1]) / 2
            star(img, mx, my, 9 + 3 * (int(t * 12) % 2), (1, .9, .2), n=8, inner=0.45)
        if loose_head:
            _phead(img, *loose_head, skin=SKINS[1], helmet=(.2, .25, .3))
        if 7.45 <= t < 7.6:
            star(img, hx, self.GY - 56, 8, (1, .9, .3), n=8, inner=0.4)
        if t >= 8.2:                                # oops
            ellipse(img, 38 + 10, self.GY - 42, 3, 3, (.25, .55, .22))
            ellipse(img, 38 + 8, self.GY - 50, 3.5, 3.5, WHITE)
            ellipse(img, 38 + 9, self.GY - 50, 1.6, 1.8, BLACK)


CHANNELS = [ClayDay, PlasticHeroes, Spoon, EggBand, Snails, Knees, Screensaver, LongCat, NightWalk, TestPattern,
            Vacation, Catch, Morning, TinyArms, Balloon]
