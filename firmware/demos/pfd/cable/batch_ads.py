"""Commercials and infomercials from other dimensions: products demonstrated with total conviction."""
import math

import numpy as np

from .. import draw
from ..draw import N, X, Y
from .kit import (LEG, SKINS, WHITE, body, caption, chatter, cue, ellipse, face, grey, hand, line, poly, rays, rect,
                  star, toon, vgrad, words)
from .shows import Show


def _u(t, a, b):
    """How far t is from a to b, 0..1."""
    return min(1.0, max(0.0, (t - a) / (b - a)))


def _ease(u):
    return u * u * (3 - 2 * u)


def _mix(a, b, k):
    return tuple(p + (q - p) * k for p, q in zip(a, b))


def _xf(x, y, rot=0.0, k=1.0):
    """Local (dx, dy) to the screen, about (x, y), turned rot radians clockwise and scaled k."""
    c, s = math.cos(rot) * k, math.sin(rot) * k
    return lambda dx, dy: (x + dx * c - dy * s, y + dx * s + dy * c)


def _dizzy(img, x, y, t, r=9.0):
    for k in range(3):
        a = t * 6 + k * 2.1
        star(img, x + r * math.cos(a), y + 3 * math.sin(a), 2.5, (1, .9, .2), n=5, inner=0.45)


def _sparkle(img, x, y, r, t, rgb=(1, 1, .75)):
    star(img, x, y, r, rgb, n=4, inner=0.22, rot=t * 2)


# ---------------------------------------------------------------- 101

def _halves(img, fn, cx, s, y0, y1):
    """Draw fn(img, x) cut in two at column cx, the halves s apart."""
    if s <= 0.3:
        fn(img, cx)
        return
    a = img.copy()
    fn(a, cx - s)
    c = int(round(cx - s))
    img[y0:y1, :c] = a[y0:y1, :c]
    a = img.copy()
    fn(a, cx + s)
    c = int(round(cx + s))
    img[y0:y1, c:] = a[y0:y1, c:]


class Slice(Show):
    """Silent: a knife that cuts anything. Anything at all."""
    num, title, length = 101, "SLICE-O-MATIC", 10.0
    G, H, PX = 86, 52, 34
    # the arm and the knife: keyframes of (time, arm angle, blade angle)
    KEYS = [(0, 1.5, -.1), (.5, 1.5, -.1), (.8, 2.3, -.7), (.92, 1.25, .13), (1.5, 1.25, .13), (1.9, 1.5, -.1),
            (2.3, 1.5, -.1), (2.6, 2.3, -.7), (2.72, 1.25, .13), (3.3, 1.25, .13), (3.7, 1.5, -.1), (4.1, 2.9, -1.45),
            (4.72, 2.9, -1.45), (4.85, .7, .9), (10, .7, .9)]

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.1, .45, .55), (.04, .22, .32), 0, self.G)
        for k in range(6):
            star(self.bg, 10 + k * 22, 14 + 6 * (k % 2), 4, (.15, .55, .65), n=4, inner=0.3)
        rng = np.random.default_rng(self.num)
        self.snow = (rng.uniform(.05, .5, (2 * N, N, 1)) * np.ones(3)).astype(np.float32)
        self.upper = (Y + 0.5) < 100 - 0.5625 * (X + 0.5)
        k = np.array(self.KEYS, np.float64)
        self.kt, self.ka, self.kp = k[:, 0], k[:, 1], k[:, 2]

    def _counter(self, img):
        rect(img, 0, self.G, N, N, (.75, .16, .22))
        rect(img, 0, self.G, N, self.G + 3, (.85, .8, .7))
        rect(img, 64, self.G - 3, 116, self.G, (.85, .68, .45))

    @staticmethod
    def _tomato(img, x):
        ellipse(img, x, 77, 7.5, 6.5, (.9, .15, .1))
        ellipse(img, x - 2.5, 74.5, 2, 1.2, (1, .5, .4))
        star(img, x, 71, 2.5, (.2, .6, .15), n=5, inner=0.4)

    @staticmethod
    def _boot(img, x):
        rect(img, x - 7, 58, x + 2, 80, (.45, .25, .1))
        ellipse(img, x + 2, 79, 10, 4.5, (.45, .25, .1))
        rect(img, x - 8, 81, x + 13, 83, (.2, .12, .08))
        rect(img, x - 8, 58, x + 3, 61, (.32, .17, .07))

    def draw(self, img, t):
        img[:] = self.bg
        a, phi = float(np.interp(t, self.kt, self.ka)), float(np.interp(t, self.kt, self.kp))
        if t < 3.7:
            look, mood = (1, 0.6), 1
        elif t < 5.6:
            look, mood = (0, 0), 1
        elif t < 8.8:
            look, mood = (-0.5, 1), -1
        else:
            look, mood = (0, 0), 1
        toon(img, self.PX, 90, self.H, SKINS[0], (.2, .3, .8), t, arms=(0.3, a), look=look, mood=mood, seed=1)
        self._counter(img)
        if t < 1.8:
            _halves(img, self._tomato, 88, 4 * _ease(_u(t, .92, 1.3)), 60, self.G)
        elif t < 3.6:
            _halves(img, self._boot, 90, 4 * _ease(_u(t, 2.72, 3.1)), 50, self.G)
        hx, hy = hand(self.PX, 90, self.H, a, 1)
        c, s = math.cos(phi), math.sin(phi)
        line(img, hx - 5 * c, hy - 5 * s, hx, hy, (.15, .1, .1), w=3.5)
        line(img, hx, hy, hx + 34 * c, hy + 34 * s, (.8, .82, .88), w=3)
        ellipse(img, hx, hy, 2.6, 2.6, SKINS[0])
        if 4.3 < t < 4.72:
            _sparkle(img, hx + 34 * c, hy + 34 * s, 6, t)
        if 4.72 < t < 5.4:                          # the swing, right across the picture
            u, fade = _u(t, 4.72, 4.85), 1 - _u(t, 4.85, 5.4)
            line(img, 128, 28, 128 - 128 * u, 28 + 72 * u, (1, 1, .8), w=2, a=fade)
        s = 34 * _ease(_u(t, 5.6, 6.5)) - 34 * _ease(_u(t, 8.2, 8.7))
        if s > 0.5:                                 # and the picture comes apart along it
            scene = img.copy()
            o = (int(t * 24) * 41) % N
            img[:] = self.snow[o:o + N]
            low = ~self.upper
            img[low] = scene[low]
            dx, dy = -int(round(.872 * s)), int(round(.49 * s))
            m = self.upper[:N - dy, -dx:]
            tgt = img[dy:, :N + dx]
            tgt[m] = scene[:N - dy, -dx:][m]
        elif t > 8.7:
            line(img, 0, 100, 128, 28, (.1, .1, .1), w=1, a=0.6)
        caption(img, cue(t, [(0, "CUTS TOMATOES!"), (1.8, "CUTS BOOTS!"), (3.6, "CUTS ANYTHING!"), (5.6, ""),
                             (8.8, "NO REFUNDS.")])[1])


# ---------------------------------------------------------------- 107

class Rock(Show):
    """Silent: this year's must-have toy is a rock."""
    num, title, length = 107, "ROCK!", 9.0
    G, H = 124, 44

    @staticmethod
    def _rock(img, x, y, s):
        ellipse(img, x, y, 13 * s, 9 * s, (.5, .48, .46), rot=0.2)
        ellipse(img, x + 4 * s, y - 2 * s, 7 * s, 5 * s, (.58, .56, .54), rot=-0.3)
        ellipse(img, x - 5 * s, y + 3 * s, 3 * s, 2 * s, (.4, .38, .37))
        ellipse(img, x - 4 * s, y - 4 * s, 3 * s, 1.5 * s, (.75, .73, .7), rot=-0.4)

    def draw(self, img, t):
        i, _, lt = cue(t, [(0, 0), (3.0, 1), (5.4, 2)])
        if i == 1:                                  # the close-up
            rays(img, 64, 70, (.5, .12, .55), (.62, .22, .66), n=16, rot=t * 0.3)
            ellipse(img, 64, 98, 50, 14, (.6, .05, .15))
            ellipse(img, 64, 93, 46, 10, (.8, .15, .25))
            self._rock(img, 64, 76 - 2 * math.sin(t * 2), 2.8)
            for k in range(4):
                a = t * 0.8 + k * math.pi / 2
                _sparkle(img, 64 + 44 * math.cos(a), 70 + 30 * math.sin(a), 3 + 2 * abs(math.sin(t * 4 + k)), t)
            caption(img, "IT'S A ROCK.")
            return
        rays(img, 64, 100, (1, .5, .08), (1, .72, .2), n=14, rot=t * 0.5)
        rect(img, 46, 98, 82, N, (.4, .1, .6))
        rect(img, 44, 96, 84, 100, (1, .82, .2))
        self._rock(img, 64, 87, 1.0)
        if i == 2:
            u = _u(lt, 0, 0.35)
            y = -20 + 98 * u * u if u < 1 else 78 - 5 * abs(math.sin((lt - 0.35) * 12)) * math.exp(-(lt - 0.35) * 5)
            self._rock(img, 64, y, 0.75)
        base = self.G - LEG * self.H
        for k, (x, shirt) in enumerate(((22, (.2, .7, .3)), (106, (.2, .45, .9)))):
            d = 1 if k == 0 else -1
            jump = abs(math.sin(t * 7 + k * 1.3)) * (10 if i == 0 else 20)
            rot, y, mood, talk = 0.0, base - jump, 1, 0.8 + 0.2 * math.sin(t * 20 + k)
            arms = (2.6 + 0.3 * math.sin(t * 14 + k), 2.6 + 0.3 * math.sin(t * 14 + k + 1))
            if i == 2 and k == 1 and lt > 1.0:      # it's all too much
                u = _u(lt, 1.0, 1.5)
                rot, y, arms, talk = -math.pi / 2 * _ease(u), base + (self.G - 5 - base) * u, (2.5, 2.5), 0
            hx, hy, r = toon(img, x, y, self.H, SKINS[1 + 2 * k], shirt, t, arms=arms, rot=rot, mood=mood, talk=talk,
                             look=(0.5 * d, 0.4), seed=k)
            if rot < -1.2:
                _dizzy(img, hx, hy - r, t)
        late = i == 2 and lt > 2.2
        if i == 0:
            words(img, "ROCK!", 40 - 3 * abs(math.sin(t * 5)), WHITE, scale=3, shadow=(.55, .05, .1))
        elif not late:
            words(img, "2 ROCKS!", 40 - 3 * abs(math.sin(t * 5)), WHITE, scale=2, shadow=(.55, .05, .1))
        if (i == 0 and t > 1.0) or (i == 2 and not late):
            star(img, 22, 22, 17, (.9, .08, .2), n=14, rot=t)
            draw.text(img, "$99", 22, 18, WHITE, center=True)
        if late:
            caption(img, "ROCK SOLD SEPARATELY", y=0)


# ---------------------------------------------------------------- 113

class Mattress(Show):
    """Silent: the softest mattress in any dimension."""
    num, title, length = 113, "DREAMSINK", 10.0
    TOP, X0, X1, BASE, H, MX = 84, 14, 116, 104, 50, 62
    SHIRT = (.3, .55, .95)

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.5, .45, .72), (.38, .33, .58), 0, 100)
        rect(self.bg, 0, 100, N, N, (.42, .28, .18))
        rect(self.bg, 26, 14, 52, 36, (.75, .6, .3))
        rect(self.bg, 28, 16, 50, 34, (.12, .15, .35))
        ellipse(self.bg, 39, 25, 6, 6, (.95, .9, .6))
        ellipse(self.bg, 42, 23, 5, 5, (.12, .15, .35))
        rect(self.bg, 5, 54, self.X0 + 2, 112, (.45, .28, .15))
        ellipse(self.bg, 10.5, 54, 5.5, 5.5, (.45, .28, .15))
        self.mat = np.empty((N, N, 3), np.float32)
        self.mat[:] = (.78, .84, .95)
        self.mat[((X + Y) % 12 < 1) | ((X - Y) % 12 < 1)] = (.62, .7, .88)
        self.inbed = (X >= self.X0) & (X < self.X1) & (Y < self.BASE)
        self.dip = np.exp(-((X + 0.5 - self.MX) / 26) ** 2)

    def draw(self, img, t):
        img[:] = self.bg
        lie = self.TOP - 3
        x, y, rot, arms, mood, dip = self.MX, self.TOP - LEG * self.H, 0.0, (1.5, 1.5), 1, 2.0
        if t < 1.0:
            pass
        elif t < 1.45:
            u = _ease(_u(t, 1.0, 1.45))
            rot, y = -math.pi / 2 * u, y + (lie - y) * u
        elif t < 2.6:
            rot, y = -math.pi / 2, lie - 2 * abs(math.sin((t - 1.45) * 9)) * math.exp(-(t - 1.45) * 3)
            arms, dip = (0.3, 0.3), 4
        else:
            u = _u(t, 2.6, 6.0)
            rot, y, dip = -math.pi / 2, lie + 22 * _ease(u), 4 + 5 * u
            arms = (0.3, math.pi / 2 + 0.4 * math.sin(t * 6)) if t > 3.4 else (0.3, 0.3)
        if t > 8.3:
            dip = 9 * (1 - _ease(_u(t, 8.3, 9.0)))
        if y < self.TOP + 20:
            toon(img, x, y, self.H, SKINS[0], self.SHIRT, t, rot=rot, arms=arms, mood=mood, look=(0, 0), seed=3,
                 pants=self.SHIRT)
        img[self.BASE:, self.X0:self.X1] = self.bg[self.BASE:, self.X0:self.X1]
        if 5.0 < t < 6.4:                           # goodbye
            wx = 46 + 3 * math.sin(t * 9)
            hy = self.TOP - 12 + 20 * _ease(_u(t, 5.8, 6.4))
            line(img, 46, self.TOP + 8, wx, hy + 3, self.SHIRT, w=4)
            ellipse(img, wx, hy, 3, 3.3, SKINS[0])
        mask = self.inbed & (Y >= self.TOP + dip * self.dip)
        img[mask] = self.mat[mask]
        hi = mask & (Y < self.TOP + 1.6 + dip * self.dip)
        img[hi] = (.9, .93, 1)
        rect(img, self.X0, self.BASE, self.X1, self.BASE + 7, (.35, .22, .15))
        for lx in (self.X0 + 2, self.X1 - 6):
            rect(img, lx, self.BASE + 7, lx + 4, self.BASE + 11, (.3, .18, .12))
        for k in range(3):                          # bubbles
            u = _u(t, 6.4 + 0.4 * k, 7.0 + 0.4 * k)
            if 0 < u < 1:
                bx, by = 52 + 10 * k + 2 * math.sin(t * 9), self.TOP - 4 - 14 * u
                draw.ring(img, bx, by, 2 + u, (.85, .9, 1))
            elif u >= 1 and t < 7.25 + 0.4 * k:
                star(img, 52 + 10 * k, self.TOP - 19, 3, (.85, .9, 1), n=5, inner=0.4)
        if t > 7.6:                                 # and the mattress gives one thing back
            u = _u(t, 7.6, 8.3)
            sx, sy = self.MX + 34 * u, self.TOP - 44 * math.sin(math.pi * u) - 3 * u
            r = 14 * u if u < 1 else 0.3
            ellipse(img, sx, sy, 7, 2.8, (.95, .5, .65), rot=r)
            ellipse(img, sx - 4 * math.cos(r), sy - 4 * math.sin(r) - 1.5, 2.5, 2.5, (1, .8, .9))
        caption(img, cue(t, [(0, "SO SOFT."), (2.6, "SO, SO SOFT."), (6.4, ""), (8.4, "NO RETURNS.")])[1])


# ---------------------------------------------------------------- 119

class Perfume(Show):
    """Silent, in slow motion: one spritz of a very strong fragrance."""
    num, title, length = 119, "PROPULSION", 11.0
    PINK, GOLD, HAIR = (.95, .4, .68), (1, .78, .3), (.6, .12, .08)
    H = 60

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.28, .05, .32), (.07, .0, .1))
        ellipse(self.bg, 44, 72, 42, 56, (.36, .08, .38), a=0.6)
        rect(self.bg, 0, 123, N, N, (.12, .02, .14))
        rng = np.random.default_rng(self.num)
        self.dust = rng.uniform(0, N, (40, 2))
        self.dv = rng.uniform(-3, 3, (40, 2))

    def _model(self, img, x, y, rot, arm, t, h, look=(1, 0)):
        at = _xf(x, y, rot)
        for k in range(5):                          # hair, in a breeze that isn't there
            pts = [at(-h * 0.06 - j * 2.2 - k * 0.9 + 1.8 * math.sin(t * 1.6 + j * 0.7 + k),
                      -h * 0.56 + j * h * 0.075 + k * 1.2) for j in range(6)]
            for p, q in zip(pts, pts[1:]):
                line(img, *p, *q, self.HAIR, w=h * 0.045)
        ellipse(img, *at(0, -h * 0.54), h * 0.16, h * 0.1, self.HAIR, rot=rot)
        poly(img, [at(-h * 0.07, -h * 0.1), at(h * 0.07, -h * 0.1), at(h * 0.22, h * 0.42), at(-h * 0.22, h * 0.42)],
             self.PINK)
        toon(img, x, y, h, SKINS[1], self.PINK, t, rot=rot, arms=(0.25, arm), look=look, mood=1, seed=7,
             pants=self.PINK)
        bx, by = hand(x, y, h, arm, 1, rot)
        ellipse(img, bx, by - h * 0.03, h * 0.05, h * 0.07, (1, .65, .85))
        ellipse(img, bx, by - h * 0.11, h * 0.025, h * 0.03, self.GOLD)

    def draw(self, img, t):
        img[:] = self.bg
        xs = (self.dust[:, 0] + self.dv[:, 0] * t) % N
        ys = (self.dust[:, 1] + self.dv[:, 1] * t - 4 * t) % N
        draw.plot(img, xs, ys, (.5, .4, .15))
        if t >= 7.0:                                # the product
            if t > 7.8:                             # and her, still going
                u = _u(t, 7.8, 11.0)
                self._model(img, 160 - 210 * u, 12 + 2 * math.sin(t), -math.pi / 2, 2.3, t, 34, look=(-1, 0))
            ellipse(img, 64, 74, 20, 4, (.15, .02, .15))
            ellipse(img, 64, 56, 17, 19, self.PINK)
            ellipse(img, 58, 50, 5, 9, (1, .7, .88))
            rect(img, 59, 34, 69, 40, self.GOLD)
            rect(img, 56, 22, 72, 35, self.GOLD)
            rect(img, 58, 24, 61, 33, (1, .92, .6))
            words(img, "PROPULSION", 88, self.GOLD, scale=2, shadow=(.35, .0, .2))
            return
        arm = 0.25 + 2.15 * _ease(_u(t, 0.3, 3.0))
        v = _u(t, 3.35, 7.0)
        x, y = 40 + 130 * v ** 1.7, 98 - 24 * _ease(_u(t, 3.35, 5.2))
        rot = math.pi / 2 * _ease(_u(t, 3.35, 4.6))
        if t > 3.35:                                # a shoe stays behind
            r = -1.3 * _ease(_u(t, 4.6, 6.2))
            at = _xf(36, 123, r)
            poly(img, [at(-7, 0), at(7, 0), at(7, -4), at(0, -6), at(-7, -3)], (1, .2, .35))
            line(img, *at(-6, 0), *at(-6, 5), (1, .2, .35), w=2)
        self._model(img, x, y, rot, arm, t, self.H)
        if t > 3.2:                                 # one spritz
            g, fade = _ease(_u(t, 3.2, 5.0)), 1 - _u(t, 5.6, 7.0)
            for k in range(6):
                a = k * 1.05 + 0.3
                ellipse(img, 48 + 22 * g * math.cos(a), 70 + 16 * g * math.sin(a), 4 + 16 * g, 4 + 12 * g,
                        (1, .72, .88), a=0.35 * fade)


# ---------------------------------------------------------------- 124

class Car(Show):
    """Silent: nought to sixty in a tenth of a second, which is too fast."""
    num, title, length = 124, "THE ZOOM GT", 10.0
    RY, CX = 114, 60
    RED, DUST = (.9, .1, .12), (.72, .56, .4)

    def __init__(self):
        bg = self.bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.22, .08, .35), (1, .55, .3), 0, 84)
        ellipse(bg, 98, 84, 20, 20, (1, .85, .4), half="top")
        poly(bg, [(0, 84), (0, 64), (8, 60), (30, 60), (36, 68), (46, 84)], (.38, .13, .3))
        poly(bg, [(66, 84), (74, 70), (80, 68), (88, 70), (90, 76), (100, 76), (104, 84)], (.33, .1, .28))
        rect(bg, 0, 84, N, N, (.78, .5, .3))
        rect(bg, 0, 96, N, 122, (.26, .22, .26))
        for x in range(0, N, 16):
            rect(bg, x, 107, x + 8, 109, (.95, .8, .2))
        self.edge = (6 * np.sin(np.arange(N) * 0.2) + 4 * np.sin(np.arange(N) * 0.53))[:, None]

    def _car(self, img, x, col):
        y = self.RY
        poly(img, [(x - 36, y - 6), (x - 37, y - 14), (x - 30, y - 19), (x + 16, y - 19), (x + 30, y - 15),
                   (x + 38, y - 12), (x + 38, y - 6)], col)
        line(img, x - 34, y - 13, x + 32, y - 12, _mix(col, WHITE, 0.35), w=1.2)
        line(img, x + 12, y - 19, x + 6, y - 29, (.6, .85, 1), w=2)
        ellipse(img, x + 36, y - 11, 2, 1.5, (1, 1, .7))
        for wx in (x - 22, x + 22):
            ellipse(img, wx, y - 5, 6.5, 6.5, (.1, .1, .1))
            ellipse(img, wx, y - 5, 3, 3, (.7, .7, .75))

    def _sitter(self, img, x, y, t, mood, look, swept, dust):
        skin, shirt, pants, hair = (_mix(c, self.DUST, dust) for c in (SKINS[0], (.2, .5, .9), (.2, .2, .3),
                                                                     (.35, .2, .1)))
        line(img, x, y, x + 12, y, pants, w=4.5)
        line(img, x + 12, y, x + 13, y + 9, pants, w=3.5)
        ellipse(img, x + 15, y + 10, 3, 1.8, (.1, .1, .1))
        ellipse(img, x, y - 8, 5, 8.5, shirt)
        line(img, x + 2, y - 12, x + 12, y - 9, shirt, w=3)
        line(img, x + 14, y - 15, x + 12, y - 3, (.12, .12, .12), w=2.5)
        ellipse(img, x + 12, y - 9, 2, 2, skin)
        if swept:
            for k in range(4):
                line(img, x - 1, y - 27 + k * 2.2, x - 13 - k, y - 27 + k * 3, hair, w=2.5)
        else:
            ellipse(img, x + 1, y - 27, 6, 3, hair)
        face(img, x + 1, y - 21, 6, skin, t, mood=mood, look=look, seed=8)

    def draw(self, img, t):
        img[:] = self.bg
        gone = 2.5 <= t < 4.0
        cx = self.CX if not 4.0 <= t < 4.1 else -60 + 120 * _u(t, 4.0, 4.1)
        dust = _u(t, 6.8, 7.0)
        if t < 2.5:
            mood, look = 1, (0, 0)
        elif t < 3.1:
            mood, look = 1, (1, 0)
        elif t < 3.6:
            mood, look = 0, (0, 1)
        elif t < 5.0:
            mood, look = -1, (0, 0)
        else:
            mood, look = 0, (0, 0)
        self._sitter(img, self.CX - 8, self.RY - 17, t, mood, look, t > 4.1, 0.7 * dust)
        if not gone:
            self._car(img, cx, _mix(self.RED, self.DUST, 0.75 * dust))
        if 2.5 <= t < 3.2:                          # gone
            fade = 1 - _u(t, 2.5, 3.2)
            for k in range(5):
                line(img, 20 + 9 * k, 98 + 4 * k, 128, 98 + 4 * k, (1, .95, .8), w=1, a=fade)
            for k in range(3):
                ellipse(img, 22 - 6 * k * (t - 2.5) * 3, 106 - 3 * k, 6 + 10 * (t - 2.5), 4 + 6 * (t - 2.5), self.DUST,
                        a=0.7 * fade)
        if 3.9 <= t < 4.6:                          # back already, from the other side
            fade = 1 - _u(t, 4.1, 4.6)
            for k in range(5):
                line(img, 0, 98 + 4 * k, cx - 30, 98 + 4 * k, (1, .95, .8), w=1, a=fade)
        if 4.1 < t < 6.2:
            for k in range(2):
                ph = (t * 1.5 + k * 0.5) % 1
                ellipse(img, self.CX - 22 + 44 * k - 4 * ph, self.RY - 6 - 14 * ph, 2 + 4 * ph, 2 + 4 * ph,
                        (.7, .7, .7), a=0.6 * (1 - ph))
        if 6.2 < t < 8.6:                           # the dust catches up
            front = -40 + 240 * _u(t, 6.2, 6.9)
            k = 1 - _u(t, 7.2, 8.6)
            a = np.clip((front + self.edge - X) / 24, 0, 1)[..., None] * k
            img += (np.asarray(self.DUST, np.float32) - img) * a
        if 8.8 < t < 9.6:
            u = _u(t, 8.8, 9.6)
            ellipse(img, self.CX - 2 + 8 * u, self.RY - 37 - 6 * u, 1 + 4 * u, 1 + 3 * u, self.DUST, a=1 - u)
        caption(img, cue(t, [(0, "THE ZOOM GT"), (2.5, ""), (4.4, "0-60 IN 0.1 SEC"), (6.2, ""),
                             (8.4, "NOW IN BEIGE.")])[1])


# ---------------------------------------------------------------- 130

class Vacuum(Show):
    """Silent: the most powerful vacuum cleaner ever demonstrated."""
    num, title, length = 130, "VAC-U-LUX 9000", 11.0
    G, P = 96, (58.0, 108.0)
    MX, MY, H = 100, 90.5, 56

    def __init__(self):
        bg = self.bg = np.empty((N, N, 3), np.float32)
        bg[:] = np.where((((X // 6) % 2) > 0)[..., None], np.array((.95, .68, .72), np.float32),
                         np.array((.88, .58, .66), np.float32))
        rect(bg, 0, self.G, N, N, (.55, .35, .2))
        for y in range(self.G + 6, N, 7):
            rect(bg, 0, y, N, y + 1, (.45, .28, .15))
        rect(bg, 0, self.G - 3, N, self.G, (.8, .75, .7))
        rect(bg, 86, 18, 118, 50, (.85, .8, .75))
        rect(bg, 88, 20, 116, 48, (.5, .75, .95))
        rect(bg, 101, 20, 103, 48, (.85, .8, .75))
        rect(bg, 88, 33, 116, 35, (.85, .8, .75))
        dx, dy = X + 0.5 - self.P[0], Y + 0.5 - self.P[1]
        self.r, self.ang = np.hypot(dx, dy), np.arctan2(dy, dx)

    @staticmethod
    def _rug(img, x, y, k):
        ellipse(img, x, y, 22 * k, 4.5 * k, (.75, .15, .2))
        ellipse(img, x, y, 15 * k, 2.8 * k, (.95, .75, .2))
        ellipse(img, x, y, 8 * k, 1.5 * k, (.75, .15, .2))

    @staticmethod
    def _chair(img, x, y, k, rot):
        at = _xf(x, y, rot, k)
        green, dark = (.25, .6, .35), (.18, .42, .25)
        poly(img, [at(-12, -32), at(12, -32), at(12, -12), at(-12, -12)], green)
        poly(img, [at(-15, -14), at(15, -14), at(15, -5), at(-15, -5)], dark)
        for s in (-1, 1):
            poly(img, [at(14 * s, -20), at(18 * s, -20), at(18 * s, -6), at(14 * s, -6)], green)
            line(img, *at(13 * s, -5), *at(13 * s, 0), (.3, .2, .1), w=2 * k)

    @staticmethod
    def _frame(img, x, y, k, rot):
        at = _xf(x, y, rot, k)
        poly(img, [at(-12, -10), at(12, -10), at(12, 10), at(-12, 10)], (.85, .65, .2))
        poly(img, [at(-9, -7), at(9, -7), at(9, 7), at(-9, 7)], (.4, .7, .9))
        poly(img, [at(-9, 7), at(-2, -2), at(4, 4), at(9, 0), at(9, 7)], (.3, .6, .25))
        ellipse(img, *at(4, -3), 2.2 * k, 2.2 * k, (1, .9, .3))

    def _vac(self, img, k, top=None):
        k *= 1.3
        at = _xf(self.P[0], self.P[1], 0, k)
        poly(img, [at(0, -6), at(22, -6), at(24, 3), at(0, 3)], (.8, .1, .15))
        ellipse(img, *at(18, 3), 3 * k, 3 * k, (.15, .15, .15))
        ellipse(img, *at(0, -1.5), 1.6 * k, 4 * k, (.05, .05, .05))
        top = top or at(21, -26)
        line(img, *at(20, -6), *top, (.2, .2, .22), w=2.2 * k)
        ellipse(img, *at(20, -16), 5 * k, 10 * k, (.3, .3, .38))
        star(img, *at(20, -16), 3 * k, (1, .85, .2), n=5, inner=0.45)

    def _warp(self, src, d, tw):
        rs = self.r + d
        a = self.ang + tw / (1 + self.r / 18)
        sx = np.floor(self.P[0] + rs * np.cos(a)).astype(np.int32)
        sy = np.floor(self.P[1] + rs * np.sin(a)).astype(np.int32)
        ok = (sx >= 0) & (sx < N) & (sy >= 0) & (sy < N)
        out = src[np.clip(sy, 0, N - 1), np.clip(sx, 0, N - 1)]
        out[~ok] = 0
        return out

    def _toward(self, x, y, u):
        return x + (self.P[0] - x) * u, y + (self.P[1] - y) * u, 1 - 0.95 * u

    def draw(self, img, t):
        if t < 7.8:
            room = img
            room[:] = self.bg
            u = _u(t, 4.6, 5.4) ** 2
            if u < 1:
                x, y, k = self._toward(36, 44, u)
                self._frame(room, x, y, k, u * 8)
            u = _u(t, 3.2, 4.2) ** 2
            if u < 1:
                x, y, k = self._toward(24, 104, u)
                self._chair(room, x, y, k, -u * 3)
            u = _u(t, 1.8, 2.7) ** 2
            if u < 1:
                x, y, k = self._toward(26, 111, u)
                self._rug(room, x, y, k)
            u = _u(t, 0.8, 1.3) ** 2
            if u < 1:
                x, y, k = self._toward(34, 112, u)
                ellipse(room, x, y, 2 * k, 1.4 * k, (.6, .4, .15))
            s = _u(t, 5.8, 7.8) ** 2
            if s > 0:
                img[:] = self._warp(room.copy(), s * 170, s * 4)
        else:
            img[:] = 0
        if t < 5.6 and int(t * 3) % 6 != 5:         # suction
            for k in range(6):
                a = math.pi + 0.15 - 0.35 * k
                d = 44 - (t * 70 + k * 17) % 44
                c, s = math.cos(a), math.sin(a)
                line(img, self.P[0] + (d + 10) * c, self.P[1] + (d + 10) * s * 0.6, self.P[0] + d * c,
                     self.P[1] + d * s * 0.6, (1, 1, 1), w=1, a=0.45)
        if t < 8.6:
            u = _u(t, 7.9, 8.6) ** 2
            x, y = self.MX + (self.P[0] - self.MX) * u, self.MY + (self.P[1] - self.MY) * u
            h = self.H * (1 - u)
            arms = (0.3, 1.0) if u == 0 else (2.8, 2.8)
            mood = 1 if t < 7.2 else -1
            look = (-1, 0.3) if t < 5.8 else (0, 0) if t < 7.2 else (-1, 0.5)
            if h > 2:
                toon(img, x, y, h, SKINS[2], (.95, .55, .15), t, arms=arms, rot=-u * 7, look=look, mood=mood, seed=5)
            self._vac(img, 1.0, hand(self.MX, self.MY, self.H, 1.0, -1) if u == 0 else None)
        elif t < 9.2:
            self._vac(img, 1 - _u(t, 8.7, 9.2) ** 2)
        if 9.1 < t < 9.5:
            star(img, *self.P, 6 * math.sin(math.pi * _u(t, 9.1, 9.5)), (1, 1, .8), n=6, inner=0.3)
        if t > 9.7:                                 # all but one crumb
            u = _u(t, 9.7, 10.2)
            y = -5 + 117 * u * u if u < 1 else 112 - 3 * abs(math.sin((t - 10.2) * 14)) * math.exp(-(t - 10.2) * 6)
            ellipse(img, 34, y, 2, 1.4, (.6, .4, .15))
        caption(img, cue(t, [(0, "POWERFUL!"), (3.2, "VERY POWERFUL!"), (5.8, ""), (9.3, "IT REALLY SUCKS.")])[1])


# ---------------------------------------------------------------- 136

class Breakfast(Show):
    """Silent: part of a balanced breakfast."""
    num, title, length = 136, "STAK-O'S", 10.0
    T, BX = 100, 44
    PURPLE = (.55, .25, .85)
    HS = [12, 20, 16, 14, 5]
    DROPS = [None, 0.4, 1.2, 2.0, None]
    ENDS = [(100, 31, math.pi), (72, 93, math.pi / 2), (24, 100, -0.15), (100, 19, 0.0), (100, 5, 0.0)]

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        chk = (((X // 10) + (Y // 10)) % 2)[..., None]
        self.bg[:] = np.where(chk > 0, np.array((1, .85, .35), np.float32), np.array((.98, .76, .25), np.float32))

    def _item(self, img, i, x, y, rot):
        at = _xf(x, y, rot)
        if i == 0:
            poly(img, [at(-14, -12), at(14, -12), at(10, -3), at(5, 0), at(-5, 0), at(-10, -3)], (.55, .8, .95))
            if abs(rot) < 2:
                ellipse(img, *at(0, -12), 14, 3, (.97, .95, .88), rot=rot)
                for dx in (-8, -3, 2, 7):
                    ellipse(img, *at(dx, -12.5), 2, 1.3, (1, .55, .1), rot=rot)
        elif i == 1:
            poly(img, [at(-7, 0), at(7, 0), at(8, -20), at(-8, -20)], (.75, .88, .97))
            poly(img, [at(-5.5, -1.5), at(5.5, -1.5), at(6.5, -16), at(-6.5, -16)], (1, .6, .05))
        elif i == 2:
            poly(img, [at(-9, 0), at(9, 0), at(9, -11), at(6, -16), at(-6, -16), at(-9, -11)], (.65, .38, .15))
            poly(img, [at(-7, -2), at(7, -2), at(7, -10.5), at(5, -14), at(-5, -14), at(-7, -10.5)], (.95, .78, .45))
        elif i == 3:
            ellipse(img, *at(0, -7), 5, 7, (.97, .92, .82), rot=rot)
        else:
            ellipse(img, *at(0, -2.5), 3.2, 2.6, (1, .55, .1), rot=rot)
            ellipse(img, *at(0, -2.5), 1.2, 1, (.7, .3, .05), rot=rot)

    def _arm(self, t):
        """Where the mascot's reaching hand is."""
        rest = (80.0, 86.0)
        if 2.8 < t < 5.0:
            if t < 4.0:
                u = _ease(_u(t, 2.8, 4.0))
                return rest[0] + (self.BX + 4 - rest[0]) * u, rest[1] + (28 - rest[1]) * u
            if t < 4.4:
                return self.BX + 4 * (1 - _u(t, 4.0, 4.4)), 28 + 6 * _u(t, 4.0, 4.4)
            u = _ease(_u(t, 4.4, 5.0))
            return self.BX + (rest[0] - self.BX) * u, 34 + (rest[1] - 34) * u
        return rest

    def _tower(self, t):
        if t < 2.8:
            amp = 0.0
        elif t < 4.4:
            amp = 0.12 * _u(t, 2.8, 4.4)
        else:
            amp = 0.12 * (1 - _u(t, 4.4, 5.0))
        sway = amp * math.sin(t * 7)
        tip = 1.1 * _u(t, 6.0, 6.5) ** 2
        out, x, y = [], float(self.BX), float(self.T)
        for i, h in enumerate(self.HS):
            th = sway * (0.4 + 0.3 * i) + tip * (0.5 + 0.25 * i)
            d = self.DROPS[i]
            if d is not None and t < d:
                break
            if i == 4 and t < 4.4:
                break
            yo = 0.0
            if d is not None and t < d + 0.35:
                yo = -110 * (1 - (t - d) / 0.35) ** 2
            out.append((i, x, y + yo, th))
            x, y = x + h * math.sin(th), y - h * math.cos(th)
        return out

    def _mascot(self, img, t):
        ellipse(img, 100, 76, 20, 28, self.PURPLE)
        ellipse(img, 100, 84, 12, 16, (.7, .45, .95))
        for k in range(3):
            ellipse(img, 92 + 8 * k, 49, 4, 4, self.PURPLE)
        look = -2 if t < 6.0 else 0
        for ex in (93, 107):
            ellipse(img, ex, 63, 5.5, 6.5, WHITE)
            ellipse(img, ex + look, 64, 2.5, 3, (.05, .05, .1))
        if 5.2 < t < 6.4:
            ellipse(img, 100, 73, 6, 5, (.35, .05, .15), half="bottom")
        else:
            line(img, 95, 73, 100, 75, (.3, .05, .15), w=1.5)
            line(img, 100, 75, 105, 73, (.3, .05, .15), w=1.5)
        if 5.2 < t < 6.2:
            hands = [(82, 50), (118, 50)]
        else:
            hands = [self._arm(t), (118, 88)]
        for (sx, sy), (hx, hy) in zip(((84, 74), (116, 74)), hands):
            line(img, sx, sy, hx, hy, self.PURPLE, w=4)
            ellipse(img, hx, hy, 3.5, 3.5, self.PURPLE)
        return hands[0]

    def draw(self, img, t):
        img[:] = self.bg
        hx, hy = self._mascot(img, t)
        rect(img, 0, self.T, N, self.T + 5, (.6, .35, .15))
        rect(img, 0, self.T + 5, N, N, (.48, .27, .1))
        if t < 6.5:
            for i, x, y, th in self._tower(t):
                self._item(img, i, x, y, th)
            if 2.8 < t < 4.4:
                self._item(img, 4, hx, hy - 2, 0)
        else:
            start = {i: (x, y, th) for i, x, y, th in self._tower(6.5)}
            for i in range(5):
                u = _ease(_u(t, 6.5 + 0.06 * i, 7.0 + 0.06 * i))
                (sx, sy, sa), (ex, ey, ea) = start[i], self.ENDS[i]
                self._item(img, i, sx + (ex - sx) * u, sy + (ey - sy) * u - 28 * math.sin(math.pi * u),
                           sa + (ea - sa) * u)
            if t > 7.0:
                k = _u(t, 7.0, 7.4)
                ellipse(img, 86, self.T + 1, 10 * k, 2 * k, (1, .6, .05))
                for dx, ln in ((-6, 9), (3, 14), (9, 6)):
                    ellipse(img, 100 + dx, 80 + ln * k * 0.5, 2, ln * k * 0.5 + 0.5, (1, .6, .05))
        caption(img, cue(t, [(0, "PART OF A BALANCED BREAKFAST"), (6.5, ""), (7.6, "STILL BALANCED!")])[1], y=0
                if t < 6.5 else None)


# ---------------------------------------------------------------- 142

class Bars(Show):
    """Silent: a phone plan with more bars than anyone could want."""
    num, title, length = 142, "UNLIMITED BARS", 10.0
    G, H, MX = 122, 58, 64
    CAGE = (23, 37, 51, 77, 91, 105)

    def __init__(self):
        bg = self.bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.35, .75, .92), (.75, .92, .85), 0, 104)
        rng = np.random.default_rng(self.num)
        x = 0
        while x < N:
            w, h = rng.integers(8, 16), rng.integers(14, 36)
            rect(bg, x, 104 - h, x + w - 1, 104, (.55, .72, .82))
            x += w
        rect(bg, 0, 104, N, N, (.5, .5, .56))

    def _icon(self, img, n, lit):
        for j in range(n):
            x0, h = 6 + j * 6, 4 + j * 4
            rect(img, x0, 34 - h, x0 + 4, 34, (.15, .85, .3) if j < lit else (.12, .3, .36))

    @staticmethod
    def _phone(img, x, y, rot=0.0):
        at = _xf(x, y, rot)
        poly(img, [at(-3.5, -6), at(3.5, -6), at(3.5, 6), at(-3.5, 6)], (.1, .1, .12))
        poly(img, [at(-2.3, -4.5), at(2.3, -4.5), at(2.3, 3.5), at(-2.3, 3.5)], (.3, .8, .9))

    def draw(self, img, t):
        img[:] = self.bg
        base = self.G - LEG * self.H
        y = base
        risen = sum(t > 4.18 + 0.32 * j for j in range(len(self.CAGE))) + (t > 6.2)
        if t < 2.6:
            arms, look, mood, lit = (0.3, 2.5 + 0.35 * math.sin(t * 5)), (0.6, -1), -1, 1
        elif t < 4.0:
            arms, look, mood = (2.6 + 0.3 * math.sin(t * 12), 2.6), (0.6, -1), 1
            y -= 6 * abs(math.sin(t * 9))
            lit = min(4, 2 + int((t - 2.6) / 0.35))
        elif t < 6.3:
            arms, look, mood, lit = (0.6, 2.2), (math.sin(t * 4), 0), -1, 4 + risen
        else:
            arms, look, mood, lit = (2.3, 2.3), (0, 0), -1, 4 + risen
        toon(img, self.MX, y, self.H, SKINS[4], (.95, .45, .2), t, arms=arms, look=look, mood=mood, seed=6)
        if t < 6.3:
            self._phone(img, *hand(self.MX, y, self.H, arms[1], 1))
        else:
            px, py = hand(self.MX, base, self.H, 2.2, 1)
            u = _u(t, 6.3, 6.65)
            self._phone(img, px + (84 - px) * u, py + (121 - py) * u * u, math.pi / 2 * u)
        for j, bx in enumerate(self.CAGE):
            top = N - (N - 20) * _ease(_u(t, 4.0 + 0.32 * j, 4.18 + 0.32 * j))
            if top < N:
                rect(img, bx - 2.5, top, bx + 2.5, self.G, (.3, .3, .36))
                rect(img, bx - 1.5, top, bx - 0.5, self.G, (.6, .6, .66))
        if t > 6.0:
            ty = -10 + 30 * _ease(_u(t, 6.0, 6.2))
            rect(img, 18, ty, 110, ty + 5, (.3, .3, .36))
            rect(img, 18, ty + 1, 110, ty + 2, (.6, .6, .66))
        if t > 6.3:
            for k in (-1, 1):
                ellipse(img, *hand(self.MX, base, self.H, 2.3, k), 3, 3, SKINS[4])
        self._icon(img, max(4, lit), lit)
        caption(img, cue(t, [(0, "ONE BAR?"), (2.6, "MORE BARS!"), (4.0, ""), (6.3, "UNLIMITED BARS!")])[1])


# ---------------------------------------------------------------- 148

class Burger(Show):
    """Silent: a burger so fresh it fights back."""
    num, title, length = 148, "THE BIG CHOMP", 10.0
    BUN = (.88, .55, .2)
    SEEDS = [(-12, 6), (-5, 10), (3, 11), (11, 7), (-9, 2), (7, 2), (15, 2), (-1, 5)]

    def __init__(self):
        r = np.hypot(X - 64, Y - 70)
        k = np.clip(r / 90, 0, 1)[..., None]
        self.bg = (np.array((.85, .3, .05), np.float32) * (1 - k) + np.array((.2, .03, .03), np.float32) * k)
        ang = np.arctan2(Y - 70, X - 64)
        self.bg *= (0.9 + 0.1 * (np.floor(ang * 8 / math.pi) % 2))[..., None]
        self.bg = self.bg.astype(np.float32)
        ellipse(self.bg, 64, 102, 36, 8, (.6, .6, .66))
        ellipse(self.bg, 64, 101, 30, 5.5, (.85, .85, .9))

    def _burger(self, img, x, y, eyes=0.0, look=(0, 0), mouth=0.0, legs=None, t=0.0):
        if legs is not None:
            for k in (-1, 1):
                a = 0.7 * math.sin(legs * 14) * k
                fx, fy = x + k * 6 + 7 * math.sin(a), y + 7 * math.cos(a)
                line(img, x + k * 6, y - 3, fx, fy, (.95, .85, .7), w=2)
                ellipse(img, fx + 1.5, fy, 3, 1.8, (.15, .1, .1))
        ellipse(img, x, y - 4, 19, 5, self.BUN)
        ellipse(img, x, y - 9, 21, 4.5, (.38, .18, .08))
        poly(img, [(x - 20, y - 13), (x + 20, y - 13), (x + 14, y - 8), (x + 8, y - 12), (x, y - 6), (x - 6, y - 12),
                   (x - 14, y - 8)], (1, .8, .1))
        for k in range(6):
            ellipse(img, x - 17 + k * 6.8, y - 14, 4.5, 2.5, (.3, .8, .2))
        ellipse(img, x, y - 15.5, 18, 2, (.9, .15, .1))
        top = y - 17 - mouth
        if mouth > 0.5:
            ellipse(img, x, y - 17 - mouth / 2, 17, mouth / 2 + 1, (.3, .0, .05))
            for k in range(-3, 4):
                poly(img, [(x + k * 5 - 2, top - 0.5), (x + k * 5 + 2, top - 0.5), (x + k * 5, top + 3)],
                     (.97, .97, .9))
        ellipse(img, x, top, 21, 15, self.BUN, half="top")
        for sx, sy in self.SEEDS:
            ellipse(img, x + sx, top - sy, 1.3, 0.8, (1, .95, .8))
        for ex in (x - 7, x + 7):
            ey = top - 8
            if eyes > 0:
                ellipse(img, ex, ey, 4 * eyes, 4.5 * eyes, WHITE)
                ellipse(img, ex + look[0] * 1.6, ey + look[1] * 1.6, 2 * eyes, 2.2 * eyes, (.05, .05, .1))
            elif eyes < 0:
                line(img, ex - 3, ey + 1, ex + 3, ey + 1, (.3, .1, .05), w=1.2)

    @staticmethod
    def _hand(img, x, y, mitt):
        rect(img, x + 10, y - 6, x + 90, y + 6, (.25, .35, .75))
        if mitt:
            ellipse(img, x + 2, y, 12, 9, (.85, .1, .1))
            ellipse(img, x - 4, y - 8, 4, 6, (.85, .1, .1), rot=-0.5)
            for k in range(3):
                line(img, x - 6 + 6 * k, y - 6, x - 6 + 6 * k, y + 6, (.65, .05, .05), w=1)
        else:
            ellipse(img, x + 4, y, 8, 6, SKINS[0])
            for f in range(3):
                line(img, x + 2, y - 3 + f * 3, x - 9, y - 3 + f * 3, SKINS[0], w=2.4)
            line(img, x + 2, y - 4, x - 3, y - 9, SKINS[0], w=2.4)

    def draw(self, img, t):
        img[:] = self.bg
        x, y, eyes, look, mouth, legs = 64.0, 100 + 1.5 * math.sin(t * 2), 0.0, (1, 0), 0.0, None
        if t < 3.0:
            for k in range(7):
                sy = (t * 10 + k * 17) % 90 - 5
                ellipse(img, 22 + k * 14 + 3 * math.sin(t + k), sy, 1.3, 0.8, (1, .95, .8), rot=t + k)
            for k in range(3):
                pts = [(52 + k * 12 + 2 * math.sin(t * 3 + k + j * 0.9), 64 - j * 4) for j in range(6)]
                for p, q in zip(pts, pts[1:]):
                    line(img, *p, *q, (1, .9, .8), w=1, a=0.45)
        if t >= 3.5:
            eyes = min(1.0, (t - 3.5) / 0.1)
        if 4.2 < t < 4.45:
            mouth = 13 * math.sin(math.pi * _u(t, 4.2, 4.45))
        if 5.2 <= t < 6.6:
            u = _u(t, 5.2, 6.6)
            x = 64 - 110 * u
            y = 100 + 12 * min(1.0, u * 5) - 6 * abs(math.sin(t * 9))
            legs, look = t, (-1, 0)
        elif 6.6 <= t < 8.6:
            u = _u(t, 7.4, 8.4)
            x, legs, look = -40 + 104 * u, t, (1, 0)
            y = 112 - 6 * abs(math.sin(t * 9)) - 12 * _u(t, 8.2, 8.4)
            if t > 8.4:
                legs = None
        if 8.4 <= t < 9.3:
            eyes = -1
        elif t >= 9.3:
            eyes, look = 1.25, (1, 0)
        if x > -30:
            self._burger(img, x, y, eyes, look, mouth, legs, t)
        if 8.4 < t < 9.3:                           # nothing to see here
            for k in range(2):
                ph = (t * 1.2 + k * 0.5) % 1
                nx, ny = 92 + 8 * ph + 6 * k, 70 - 24 * ph
                ellipse(img, nx, ny, 2, 1.6, (1, .95, .7))
                line(img, nx + 1.6, ny, nx + 1.6, ny - 7, (1, .95, .7), w=1)
        if t > 9.5:
            u = _u(t, 9.5, 10)
            ellipse(img, 88, 70 + 10 * u, 1.8, 2.6, (.6, .85, 1))
        hx = None
        if 3.0 < t < 4.42:
            hx = 150 - 62 * _ease(_u(t, 3.0, 4.2))
        elif 4.42 <= t < 5.6:
            hx = 88 + 24 * _u(t, 4.42, 4.5) + 3 * math.sin(t * 50) + 60 * _u(t, 5.2, 5.6) ** 2
        if hx is not None:
            self._hand(img, hx, 84, False)
            if 4.45 < t < 5.2:
                _sparkle(img, hx - 10, 79, 4, t * 4, (1, .9, .3))
        if t > 8.8:
            self._hand(img, 150 - 58 * _ease(_u(t, 8.8, 9.8)), 84, True)
        if t < 3.0:
            star(img, 24, 24, 20, (1, .85, .1), n=12, rot=t * 0.5)
            draw.text(img, "NEW!", 24, 20, (.8, .1, .05), center=True)
        caption(img, cue(t, [(0, "NEW! THE BIG CHOMP"), (3.0, ""), (6.6, "SO FRESH IT RUNS")])[1])


# ---------------------------------------------------------------- 153

class Sunscreen(Show):
    """Silent: sunscreen so strong it burns the sun."""
    num, title, length = 153, "SPF 9000", 10.0
    SEA, SX, SY = 70, 30, 28
    MX, H = 86, 54

    def __init__(self):
        rng = np.random.default_rng(self.num)
        self.day = np.empty((N, N, 3), np.float32)
        vgrad(self.day, (.3, .6, .95), (.6, .85, 1), 0, self.SEA)
        rect(self.day, 0, self.SEA, N, 84, (.1, .38, .72))
        rect(self.day, 0, 84, N, N, (.95, .8, .5))
        self.night = np.empty((N, N, 3), np.float32)
        vgrad(self.night, (.02, .03, .12), (.1, .1, .28), 0, self.SEA)
        rect(self.night, 0, self.SEA, N, 84, (.03, .08, .22))
        rect(self.night, 0, 84, N, N, (.3, .26, .22))
        draw.plot(self.night, rng.uniform(0, N, 40), rng.uniform(0, 60, 40), (.7, .7, .6))
        for img, c in ((self.day, (.6, .8, 1)), (self.night, (.2, .25, .4))):
            for k in range(9):
                x, y = rng.uniform(0, 120), rng.uniform(self.SEA + 2, 82)
                rect(img, x, y, x + 6, y + 1, c)

    def draw(self, img, t):
        k = _ease(_u(t, 6.0, 7.6))
        img[:] = self.day + (self.night - self.day) * k if 0 < k < 1 else (self.night if k >= 1 else self.day)
        burn = _u(t, 3.4, 5.6)
        col = _mix((1, .85, .2), (.95, .22, .1), burn)
        sy = self.SY + (96 - self.SY) * _ease(_u(t, 6.0, 7.2))
        if t > 8.4:
            sy = 96 - 22 * _ease(_u(t, 8.4, 9.0))
        if t < 6.5:
            for j in range(10):
                a = j * math.pi / 5 + t * 0.6
                line(img, self.SX + 16 * math.cos(a), sy + 16 * math.sin(a), self.SX + 21 * math.cos(a),
                     sy + 21 * math.sin(a), col, w=2)
        face(img, self.SX, sy, 13, col, t, mood=1 if burn < 0.3 else -1, look=(1, 1) if t > 3.2 else (0, 0), seed=9)
        if 0.5 < burn and t < 6.5:
            for j in range(2):
                ph = (t * 1.3 + j * 0.5) % 1
                ellipse(img, self.SX - 12 + 24 * j, sy + 4 + 14 * ph, 1.5, 2.2, (.6, .85, 1), a=1 - ph)
        img[self.SEA:] = self.day[self.SEA:] + (self.night[self.SEA:] - self.day[self.SEA:]) * k
        if t > 8.4:                                 # it's watching
            for ex in (self.SX - 5, self.SX + 5):
                ellipse(img, ex, 66, 2.6, 2.2, WHITE)
                ellipse(img, ex + 1.2, 66.5, 1.2, 1.3, (.05, .05, .1))
            line(img, self.SX - 8, 62, self.SX - 2, 64, (.4, .05, .05), w=1.2)
            line(img, self.SX + 8, 62, self.SX + 2, 64, (.4, .05, .05), w=1.2)
        chrome = _ease(_u(t, 2.6, 3.2))
        silver = (.78, .82, .88)
        skin, shirt, pants = (_mix(c, silver, chrome) for c in (SKINS[1], (.95, .35, .55), (.2, .55, .5)))
        base = self.N_BASE = 120 - LEG * self.H
        if t < 2.6:
            arms = (1.1 + 0.5 * math.sin(t * 10), 1.9 + 0.25 * math.sin(t * 10 + 1))
        else:
            arms = (-0.4, -0.4)
        hx, hy, r = toon(img, self.MX, base, self.H, skin, shirt, t, arms=arms, mood=1,
                         look=(-1, -1) if t > 3.2 else (-0.6, 0.5), seed=10, pants=pants)
        if t < 2.6:
            bx, by = hand(self.MX, base, self.H, arms[1], 1)
            rect(img, bx - 2.5, by - 9, bx + 2.5, by, (.95, .95, .9))
            rect(img, bx - 1.5, by - 11, bx + 1.5, by - 9, (1, .5, .1))
        if chrome > 0.5:
            for j, (dx, dy) in enumerate(((-4, -8), (5, 6), (-3, 20), (3, -30))):
                if (t * 2 + j * 0.37) % 1 < 0.5:
                    _sparkle(img, self.MX + dx, base + dy, 3, t + j)
        if 3.2 < t < 6.3:                           # straight back at it
            a = 0.55 + 0.1 * math.sin(t * 20)
            line(img, self.SX + 6, sy + 4, self.MX - 2, base - 16, (1, 1, .6), w=2.5, a=a)
            line(img, self.MX - 4, base - 18, self.SX + 9, sy + 1, (1, .95, .4), w=1.5, a=a)
        caption(img, cue(t, [(0, "SPF 9000"), (3.2, "TOTAL PROTECTION"), (6.0, ""), (8.0, "THE SUN HATES IT.")])[1])


# ---------------------------------------------------------------- 159

def _spat(img, x, y, rot, c=lambda v: v, s=1.0):
    at = _xf(x, y, rot, s)
    line(img, *at(0, 0), *at(0, 14), c((.5, .3, .15)), w=2 * s)
    poly(img, [at(-4, -12), at(4, -12), at(4, 0), at(-4, 0)], c((1, .5, .1)))
    for k in (-1.5, 1.5):
        line(img, *at(k, -10), *at(k, -3), c((.75, .3, .05)), w=1)


class ButWait(Show):
    """Silent: but wait, there's more. And more."""
    num, title, length = 159, "BUT WAIT!", 10.0
    COUNTS = [(0, 1), (2.6, 2), (3.4, 4), (4.1, 8), (4.7, 16), (5.2, 32), (5.6, 64)]
    MX, H = 28, 54

    def __init__(self):
        rng = np.random.default_rng(self.num)
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.12, .22, .62), (.05, .08, .3), 0, 104)
        rect(self.bg, 0, 104, N, N, (.28, .2, .45))
        for _ in range(12):
            star(self.bg, rng.uniform(0, N), rng.uniform(0, 100), 2, (.3, .4, .8), n=4, inner=0.3)
        pos = np.stack([rng.uniform(56, 122, 64), rng.uniform(30, 100, 64), rng.uniform(-0.7, 0.7, 64)], 1)
        self.layers = {}
        rgb, a = np.zeros((N, N, 3), np.float32), np.zeros((N, N, 3), np.float32)
        done = 1
        for _, n in self.COUNTS[1:]:
            for x, y, r in pos[done:n]:
                _spat(rgb, x, y, r)
                _spat(a, x, y, r, lambda v: WHITE)
            done = n
            self.layers[n] = (rgb.copy(), a.copy())
        self.pile = np.empty((N, N, 3), np.float32)
        self.pile[:] = (.45, .22, .05)
        for _ in range(240):
            _spat(self.pile, rng.uniform(-4, N + 4), rng.uniform(10, N + 6), rng.uniform(0, 6.3), s=1.2)
        x = np.arange(N, dtype=np.float32)
        self.bump = (5 * np.sin(x * 0.13) + 3 * np.sin(x * 0.31 + 1))[None, :]
        self.rain = np.stack([rng.uniform(0, N, 16), rng.uniform(0, 160, 16), rng.uniform(0, 6.3, 16)], 1)

    def draw(self, img, t):
        img[:] = self.bg
        _, n, _ = cue(t, self.COUNTS)
        base = self.G = 122 - LEG * self.H
        if t < 5.6:
            mood, look, arms = 1, (0, 0), (0.6 + 0.4 * math.sin(t * 3), 2.2)
        else:
            mood, look, arms = -1, (0.5, -1), (2.6, 2.6)
        toon(img, self.MX, base, self.H, SKINS[0], (.9, .9, .3), t, arms=arms, mood=mood, look=look,
             talk=chatter(t) if t < 5.6 else 0, seed=11, pants=(.3, .3, .35))
        hx, hy = hand(self.MX, base, self.H, arms[1], 1)
        _spat(img, hx + 4, hy - 2, 0.3)
        if n > 1:
            rgb, a = self.layers[n]
            img *= 1 - a
            img += rgb
        else:
            star(img, 92, 62, 20, (.9, .1, .2), n=14, rot=t)
            draw.text(img, "$19", 92, 58, WHITE, center=True)
        level = N - 100 * _ease(_u(t, 6.2, 8.0))
        if t > 5.9:
            for x, ph, r in self.rain:
                y = -20 + ((t - 5.9) * 150 + ph) % 160
                if y < level + 4:
                    _spat(img, x, y, r + t * 3)
        if level < N:
            m = Y >= level + self.bump
            img[m] = self.pile[m]
        if n > 1:
            words(img, f"X{n}" if t < 6.2 else "X999", 6, (1, .9, .2), scale=3, shadow=(.5, .1, .1), x=88)
        if t > 8.3:                                 # someone is still in there
            top = level + self.bump[0, 40] + 4
            y = top - 20 * _ease(_u(t, 8.3, 8.7))
            line(img, 40, top + 2, 40, y + 4, (.9, .9, .3), w=4)
            ellipse(img, 40, y + 3, 3.5, 3.5, SKINS[0])
            rect(img, 37, y - 8, 43, y + 2, (.1, .1, .12))
            rect(img, 38, y - 7, 42, y, (.3, .8, .9))
        caption(img, cue(t, [(0, "ONE SPATULA!"), (2.6, "BUT WAIT!"), (6.2, "THERE'S MORE!"), (8.3, "CALL NOW!")])[1])


# ---------------------------------------------------------------- 165

class Walkable(Show):
    """Silent: a lovely neighbourhood. Very walkable."""
    num, title, length = 165, "OPEN HOUSE", 11.0
    GR = 94
    HOUSES = [(22, (.95, .6, .6), (.7, .25, .3), 5.0), (64, (.6, .8, .95), (.25, .35, .6), 4.5),
              (106, (.95, .85, .45), (.6, .4, .2), 4.0)]
    RX, H = 44, 48

    def __init__(self):
        bg = self.bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.4, .7, .95), (.75, .9, 1), 0, 88)
        for cx, cy in ((30, 16), (92, 26)):
            for dx in (-7, 0, 7):
                ellipse(bg, cx + dx, cy - (dx == 0) * 3, 8, 5, (.95, .97, 1))
        rect(bg, 0, 88, N, N, (.35, .7, .3))
        rect(bg, 0, 110, N, 116, (.7, .7, .68))
        for x, *_ in self.HOUSES:
            rect(bg, x - 18, self.GR - 1, x + 18, self.GR + 3, (.6, .6, .6))

    @staticmethod
    def _house(img, x, base, w, col, roof, lift, phase):
        y = base - lift
        if lift > 0.5:
            for k in (-1, 1):
                a = 0.5 * math.sin(phase * 10) * k
                fx, fy = x + k * w * 0.25 + lift * math.sin(a), y + lift * math.cos(a)
                line(img, x + k * w * 0.25, y - 1, fx, fy, (.3, .22, .18), w=w * 0.1)
                ellipse(img, fx + 1.5, fy, w * 0.1, w * 0.06, (.2, .15, .12))
        rect(img, x - w / 2, y - w * 0.66, x + w / 2, y, col)
        poly(img, [(x - w * 0.6, y - w * 0.63), (x + w * 0.6, y - w * 0.63), (x, y - w * 1.08)], roof)
        rect(img, x - w * 0.09, y - w * 0.33, x + w * 0.09, y, _mix(roof, (0, 0, 0), 0.3))
        for k in (-1, 1):
            rect(img, x + k * w * 0.27 - w * 0.09, y - w * 0.5, x + k * w * 0.27 + w * 0.09, y - w * 0.33, (.35, .5, .7))

    def draw(self, img, t):
        img[:] = self.bg
        for i, (x0, col, roof, go) in enumerate(self.HOUSES):
            lift = 12 * _ease(_u(t, 3.0 + 0.2 * i, 3.5 + 0.2 * i))
            x, bob = float(x0), 0.0
            if t > go:
                x += 32 * (t - go)
                bob = 1.5 * abs(math.sin(t * 10))
            if x < N + 30:
                self._house(img, x, self.GR - bob, 32, col, roof, lift, t if t > go else 0)
        dx = 14.0
        if t > 8.6:
            dx += 70 * (t - 8.6)
        if dx < N + 10:
            self._house(img, dx, 104, 13, (.85, .2, .15), (.5, .1, .08), 4 * _ease(_u(t, 8.2, 8.5)),
                        t if t > 8.6 else 0)
        rect(img, 97, 98, 99, 124, (.45, .3, .2))
        rect(img, 84, 90, 112, 102, (.95, .93, .86))
        draw.text(img, "SALE", 98, 91, (.85, .1, .1), center=True)
        base = 124 - LEG * self.H
        if t < 3.0:
            arms, look, mood, talk = (0.3, 1.6 + 0.6 * math.sin(t * 2)), (0, 0), 1, chatter(t)
        elif t < 4.6:
            arms, look, mood, talk = (0.3, 0.3), (1, -1), 0, 0
        elif t < 6.6:
            arms, look, mood, talk = (0.9, 0.9), (1, -0.5), -1, 0
        else:
            arms, look, mood, talk = (0.3, 1.8), (0, 0), 1, chatter(t * 1.3) if t < 8.2 else 0
        toon(img, self.RX, base, self.H, SKINS[2], (.15, .2, .45), t, arms=arms, look=look, mood=mood, talk=talk,
             seed=12, pants=(.15, .2, .45))
        caption(img, cue(t, [(0, "VERY WALKABLE!"), (3.0, ""), (7.0, "OPEN HOUSE SUNDAY?")])[1])


# ---------------------------------------------------------------- 171

def _moth(img, x, y, s, t, ph=0.0, flap=20.0):
    f = 0.35 + 0.65 * abs(math.sin(t * flap + ph))
    for k in (-1, 1):
        ellipse(img, x + k * 2.2 * s * f, y, 2.4 * s * f + 0.3, 2.1 * s, (.82, .76, .62))
        if s > 3:
            ellipse(img, x + k * 2.6 * s * f, y, 0.6 * s * f + 0.2, 0.6 * s, (.35, .25, .4))
            ellipse(img, x + k * 2.6 * s * f, y, 0.3 * s * f + 0.1, 0.3 * s, (.95, .7, .2))
    ellipse(img, x, y, 0.75 * s, 2 * s, (.4, .3, .2))
    if s > 3:
        for k in (-1, 1):
            line(img, x + k * 0.4 * s, y - 1.8 * s, x + k * 1.6 * s, y - 3.2 * s, (.4, .3, .2), w=max(1, s * 0.2))


class Dazzle(Show):
    """Silent: a toothpaste for the brightest smile there is."""
    num, title, length = 171, "DAZZLE-DENT", 11.0
    MX, MY = 22.0, 35.5            # the smile, on the cliff

    def __init__(self):
        rng = np.random.default_rng(self.num)
        self.bath = np.empty((N, N, 3), np.float32)
        self.bath[:] = (.55, .85, .8)
        self.bath[(X % 16 < 1) | (Y % 16 < 1)] = (.45, .72, .68)
        sea = self.sea = np.empty((N, N, 3), np.float32)
        vgrad(sea, (.02, .02, .1), (.06, .08, .26), 0, 82)
        draw.plot(sea, rng.uniform(0, N, 50), rng.uniform(0, 78, 50), (.6, .6, .55))
        rect(sea, 0, 82, N, N, (.02, .08, .2))
        for _ in range(14):
            x, y = rng.uniform(40, N), rng.uniform(84, N)
            rect(sea, x, y, x + 7, y + 1, (.08, .16, .32))
        poly(sea, [(0, 72), (12, 73), (34, 74), (42, 86), (50, 128), (0, 128)], (.14, .11, .13))
        poly(sea, [(0, 72), (34, 74), (32, 77), (0, 76)], (.22, .2, .18))
        dx, dy = X + 0.5 - self.MX, Y + 0.5 - self.MY
        self.r, self.ang = np.hypot(dx, dy), np.arctan2(dy, dx)
        self.fall = np.clip(1 - self.r / 180, 0, 1) * (self.r > 4)
        self.moths = [(rng.uniform(0, 6.3), 9 + (j % 3) * 4, 2.5 + 0.4 * j, 20 + 12 * j % 60) for j in range(8)]

    def _closeup(self, img, t):
        img[:] = self.bath
        body(img, 64, 60, 26, (.2, .4, .85))
        face(img, 64, 60, 26, SKINS[0], t, mood=1, look=(0, 0), seed=13)
        ellipse(img, 64, 73, 14, 8, (.4, .05, .08), half="bottom")
        ellipse(img, 64, 73.5, 12.5, 3.8, (.97, .97, .92), half="bottom")
        if t < 1.8:
            bx = 64 + 7 * math.sin(t * 16)
            line(img, bx + 6, 76, bx + 40, 92, (.3, .6, .95), w=4)
            rect(img, bx - 7, 72, bx + 6, 76, (.9, .9, .95))
            for k in range(5):
                ellipse(img, 52 + 6 * k + 2 * math.sin(t * 9 + k), 77 + 2 * math.sin(t * 7 + 2 * k), 3, 2.4,
                        (.92, .95, 1), a=0.85)
        else:
            _sparkle(img, 72, 74, 4 + 9 * _ease(_u(t, 1.8, 2.2)), t)

    def draw(self, img, t):
        if t < 2.6:
            self._closeup(img, t)
            caption(img, "DAZZLE-DENT" if t > 1.8 else "")
            return
        img[:] = self.sea
        sx = 112 - 4 * (t - 2.6)                    # a little boat
        poly(img, [(sx - 9, 88), (sx + 9, 88), (sx + 6, 93), (sx - 6, 93)], (.35, .22, .14))
        line(img, sx, 88, sx, 74, (.3, .2, .15), w=1)
        poly(img, [(sx + 1, 75), (sx + 1, 87), (sx + 9, 87)], (.6, .6, .55))
        base = 74 - LEG * 46
        mood = 1
        hx, hy, r = toon(img, self.MX, base, 46, SKINS[0], (.2, .4, .85), t, arms=(0.3, 0.3), mood=mood, look=(1, 0),
                         seed=13)
        rect(img, hx - 3, hy + r * 0.38, hx + 3, hy + r * 0.62, (.97, .97, .92))
        for j, (ph, rad, w, y0) in enumerate(self.moths):
            u = _ease(_u(t, 4.2 + 0.35 * j, 5.2 + 0.35 * j))
            if u <= 0:
                continue
            a = ph + t * w
            ox, oy = hx + rad * math.cos(a), hy + rad * 0.7 * math.sin(a)
            _moth(img, 140 + (ox - 140) * u, y0 + (oy - y0) * u, 1.4, t, j)
        if t > 7.4:                                 # and then the big one
            u = _ease(_u(t, 7.4, 8.8))
            gx, gy = 150 + (hx + 1 - 150) * u, -30 + (hy - 1 + 30) * u
            _moth(img, gx, gy, 8, t, flap=4 if u < 1 else 1.5)
        beam = 0.35 + 0.45 * math.sin((t - 2.6) * 1.1)
        soft = np.clip(1 - np.abs(self.ang - beam) / 0.09, 0, 1) * self.fall
        img += soft[..., None] * np.array((.6, .57, .38), np.float32)
        caption(img, cue(t, [(2.6, ""), (4.0, "SO BRIGHT!"), (8.9, "MOTHS INCLUDED.")])[1])


# ---------------------------------------------------------------- 177

class Stik(Show):
    """Silent: shoes that never slip on ice, because they never leave it."""
    num, title, length = 177, "STIK-SHOES", 11.0
    G, H, FX = 110, 50, 56

    def __init__(self):
        bg = self.bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.5, .7, .95), (.8, .88, .98), 0, 88)
        ellipse(bg, 24, 92, 50, 16, (.78, .84, .92))
        ellipse(bg, 104, 94, 46, 12, (.74, .8, .9))
        for x, h in ((8, 30), (20, 22), (112, 34), (124, 24)):
            poly(bg, [(x - h * 0.3, 90), (x + h * 0.3, 90), (x, 90 - h)], (.1, .35, .25))
        rect(bg, 0, 88, N, N, (.62, .85, .95))
        rng = np.random.default_rng(self.num)
        for _ in range(12):
            x, y = rng.uniform(0, N), rng.uniform(92, N)
            line(bg, x, y, x + 8, y - 2, (.8, .93, 1), w=1)

    @staticmethod
    def _penguin(img, x, y, t):
        tilt = 0.12 * math.sin(t * 3)
        at = _xf(x, y, tilt)
        line(img, *at(-5, -12), *at(-13, -6), (.1, .1, .15), w=3)
        ellipse(img, *at(0, -10), 7, 11, (.1, .1, .15), rot=tilt)
        ellipse(img, *at(1.5, -8), 4.5, 8.5, (.95, .95, .92), rot=tilt)
        rect(img, *at(-6, -18), *at(6, -16), (.85, .1, .15))
        line(img, *at(-5, -17), *at(-11, -14 + math.sin(t * 12)), (.85, .1, .15), w=2)
        ellipse(img, *at(3, -21), 1.3, 1.3, WHITE)
        ellipse(img, *at(3.4, -21), 0.6, 0.7, (0, 0, 0))
        poly(img, [at(6, -20), at(10, -19), at(6, -18)], (1, .6, .1))
        ellipse(img, *at(2, 0.5), 4, 1.5, (1, .6, .1))

    def draw(self, img, t):
        img[:] = self.bg
        if t < 3.0:                                 # before
            base = self.G - LEG * self.H
            x, y, rot, arms, stars = -10 + 60 * min(1.0, t / 1.2), base, 0.0, (0.3, 0.3), False
            if 1.2 <= t < 1.8:
                u = _u(t, 1.2, 1.8)
                rot = -math.pi / 2 * min(1.0, u * 1.4)
                y = base - 18 * math.sin(math.pi * u) + (self.G - 5 - base) * u
                arms = (2.5 + math.sin(t * 30), 2.5 - math.sin(t * 30))
            elif t >= 1.8:
                rot, y, stars = -math.pi / 2, self.G - 5, True
            hx, hy, r = toon(img, x, y, self.H, SKINS[3], (.2, .6, .9), t, walk=1 if t < 1.2 else 0, rot=rot,
                             arms=arms, mood=-1 if t > 1.2 else 0, look=(1, 0), seed=14)
            if stars:
                _dizzy(img, hx, hy - r, t)
            grey(img, 0.85)
            caption(img, "SLIPPERY ICE?")
            return
        if t < 4.0:
            th = 0.0
        elif t < 4.5:
            th = 0.2 * _ease(_u(t, 4.0, 4.5))
        elif t < 5.1:
            th = 0.2 + 1.15 * _u(t, 4.5, 5.1) ** 2
        else:
            th = 1.35 * math.cos(5.5 * (t - 5.1)) * math.exp(-0.42 * (t - 5.1))
        hx, hy = self.FX + LEG * self.H * math.sin(th), self.G - LEG * self.H * math.cos(th)
        if t < 4.0:
            arms, mood = (0.3, 2.6), 1
        elif t < 4.5:
            arms, mood = (1.2, 1.2), 0
        else:
            arms, mood = (2.6 + 0.4 * math.sin(t * 13), 2.6 + 0.4 * math.sin(t * 11)), -1
        toon(img, hx, hy, self.H, SKINS[3], (.2, .6, .9), t, rot=th, arms=arms, mood=mood, look=(0, 0), seed=14)
        at = _xf(hx, hy, th)
        for k in (-1, 1):
            fx, fy = at(k * self.H * 0.05, LEG * self.H)
            ellipse(img, fx + 2.5, fy - 1.5, 5.5, 3.5, (.9, .1, .12))
            ellipse(img, fx + 1, fy - 4, 3, 3, (.9, .1, .12))
        if t > 7.0:
            self._penguin(img, -20 + 170 * _u(t, 7.0, 10.5), 120, t)
        caption(img, cue(t, [(3.0, "STIK-SHOES!"), (4.5, ""), (7.5, "NEVER SLIP AGAIN!")])[1])


# ---------------------------------------------------------------- 184

class Hair(Show):
    """Silent: one drop of hair tonic."""
    num, title, length = 184, "HAIR-O-GROW", 10.0
    HX, HY, R = 64, 68, 21
    CX, CY = 64, 46

    def __init__(self):
        bg = self.bg = np.empty((N, N, 3), np.float32)
        bg[:] = (.85, .65, .25)
        rect(bg, 5, 5, 123, 123, (.6, .76, .84))
        poly(bg, [(5, 40), (40, 5), (52, 5), (5, 52)], (.68, .84, .9))
        dx, dy = X + 0.5 - self.CX, Y + 0.5 - self.CY
        self.r, ang = np.hypot(dx, dy), np.arctan2(dy, dx)
        self.wob = 4 * np.sin(ang * 9) + 2 * np.sin(ang * 5 + 1)
        curl = np.sin(X * 1.3 + 2 * np.sin(Y * 0.9)) * np.sin(Y * 1.1 + 2 * np.cos(X * 0.7))
        self.tex = (np.array((.42, .23, .1), np.float32) * (0.75 + 0.25 * curl)[..., None]).astype(np.float32)

    @staticmethod
    def _bird(img, x, y, t):
        ellipse(img, x, y, 6, 4.5, (.25, .55, .95))
        ellipse(img, x - 4, y - 3, 3.5, 3.5, (.25, .55, .95))
        ellipse(img, x - 5, y - 4, 1, 1, (0, 0, 0))
        poly(img, [(x - 7, y - 4), (x - 11, y - 2.5), (x - 7, y - 1.5)], (1, .6, .1))
        f = math.sin(t * 25)
        poly(img, [(x - 1, y - 1), (x + 4, y - 1), (x + 3, y - 1 - 8 * f)], (.15, .4, .8))

    def draw(self, img, t):
        img[:] = self.bg
        R = 0.0 if t < 3.9 else 8 + 130 * _u(t, 3.9, 7.4) ** 1.6
        body(img, self.HX, self.HY, self.R, (.3, .5, .3))
        if R > 0:
            m = self.r < R + self.wob * min(1.0, R / 20)
            img[m] = self.tex[m]
        for s in (-1, 1):
            ellipse(img, self.HX + s * 21, self.HY + 2, 3.5, 5, SKINS[0])
        if t < 3.3:
            mood, look = -1, (0, -1)
        elif t < 5.5:
            mood, look = 1, (0, -1)
        elif t < 7.4:
            mood, look = 0, (math.sin(t * 3), 0)
        else:
            mood, look = -1, (1, -0.5)
        face(img, self.HX, self.HY, self.R, SKINS[0], t, mood=mood, look=look, seed=15)
        if R == 0:
            ellipse(img, 57, 52, 5, 2.5, (1, .95, .9), a=0.6, rot=-0.4)
        if 3.3 <= t < 4.4:                          # boing
            n = 1 if t < 3.6 else 5
            for k in range(n):
                x0 = 64 + (k - (n - 1) / 2) * 5
                pts = [(x0 + 2.5 * math.sin(j * 1.6 + k), 45 - j * 2.2) for j in range(6)]
                for p, q in zip(pts, pts[1:]):
                    line(img, *p, *q, (.42, .23, .1), w=1.5)
        if 2.4 < t < 3.9:                           # the tonic
            y = -20 + 34 * _ease(_u(t, 2.4, 2.8)) - 34 * _ease(_u(t, 3.4, 3.9))
            tip = 2.2 * _ease(_u(t, 2.6, 2.9))
            at = _xf(64, y, tip)
            poly(img, [at(-6, -8), at(6, -8), at(6, 10), at(-6, 10)], (.2, .7, .3))
            poly(img, [at(-2.5, -14), at(2.5, -14), at(2.5, -8), at(-2.5, -8)], (.9, .9, .85))
            rect(img, *at(-5, -2), *at(5, 3), (1, .9, .3))
            if 2.9 < t < 3.3:
                u = _u(t, 2.9, 3.25)
                ellipse(img, 64, 22 + 22 * u * u, 1.8, 2.6, (.4, .9, .5))
        if 7.4 < t < 8.4:
            u = _u(t, 7.4, 8.3)
            self._bird(img, 140 - 46 * u, 30 + 4 * math.sin(t * 10) + 6 * u, t)
        for j, (cx, cy) in enumerate(((26, 30), (100, 24), (104, 98))):
            k = _ease(_u(t, 9.0 + 0.15 * j, 9.25 + 0.15 * j))
            if k > 0:
                ellipse(img, cx, cy, 7 * k, 7 * k, (1, .9, .2))
                ellipse(img, cx - 2.5 * k, cy - 2.5 * k, 1.3 * k, 1.3 * k, (0, 0, 0))
                ellipse(img, cx + 2.5 * k, cy - 2.5 * k, 1.3 * k, 1.3 * k, (0, 0, 0))
                o = 3 * abs(math.sin(t * 12 + j))
                poly(img, [(cx - 3 * k, cy + 1), (cx + 3 * k, cy + 1), (cx, cy + (3 + o) * k)], (1, .5, .1))
                poly(img, [(cx - 3 * k, cy + 0.5), (cx + 3 * k, cy + 0.5), (cx, cy - o * k)], (1, .5, .1))
        caption(img, cue(t, [(0, "BALD?"), (2.4, ""), (4.2, "RESULTS IN SECONDS!"), (7.4, ""),
                             (9.0, "NOW WITH BIRDS!")])[1])


# ---------------------------------------------------------------- 191

class PinPull(Show):
    """Silent: the puzzle from the ads, played the way the ads play it."""
    num, title, length = 191, "99% FAIL!", 11.0
    L0, L1, R0, R1, D0, D1 = 26, 30, 98, 102, 62, 66
    TOP, PIN, FLOOR = 14, 66, 106
    HX, HH = 80, 32

    def __init__(self):
        rng = np.random.default_rng(self.num)
        bg = self.bg = np.empty((N, N, 3), np.float32)
        bg[:] = (.16, .15, .25)
        for row in range(0, N, 8):
            off = 6 if (row // 8) % 2 else 0
            for bx in range(-12 + off, N, 12):
                rect(bg, bx + 1, row + 1, bx + 12, row + 8, (.2, .19, .3))
        stone = (.55, .5, .45)
        rect(bg, self.L1, self.TOP, self.R0, self.FLOOR, (.3, .28, .38))
        for x0, x1 in ((self.L0, self.L1), (self.R0, self.R1)):
            rect(bg, x0, self.TOP, x1, self.FLOOR + 4, stone)
        rect(bg, self.L0, self.FLOOR, self.R1, self.FLOOR + 4, stone)
        rect(bg, self.D0, self.TOP, self.D1, self.PIN, stone)
        self.coins = np.empty((N, N, 3), np.float32)
        self.coins[:] = (.7, .5, .05)
        for row in range(0, N + 6, 5):
            for col in range(-6, N + 6, 7):
                x = col + 3.5 * ((row // 5) % 2) + rng.uniform(-1, 1)
                ellipse(self.coins, x, row, 3.3, 2.4, (1, .8, .15))
                ellipse(self.coins, x - 1, row - 0.8, 1.2, 0.6, (1, .95, .6))

    def _lava(self, img, x0, y0, x1, y1, t, cool=0.0):
        y0, y1 = int(max(0, y0)), int(min(N, y1))
        if y0 >= y1:
            return
        xs, ys = X[y0:y1, x0:x1], Y[y0:y1, x0:x1]
        b = np.clip(np.sin(xs * 0.5 + t * 3) * np.sin(ys * 0.6 - t * 2), 0, 1)[..., None]
        hot = np.array((1, .32, .04), np.float32) + b * np.array((0, .5, .2), np.float32)
        img[y0:y1, x0:x1] = hot * (1 - cool) + np.array((.2, .18, .18), np.float32) * cool

    def _gold(self, img, x0, y0, x1, y1, off=0):
        y0, y1 = int(max(0, y0)), int(min(N, y1))
        if y0 < y1:
            img[y0:y1, x0:x1] = np.roll(self.coins, off, 0)[y0:y1, x0:x1]

    def _pin(self, img, x0, x1, knob):
        rect(img, x0, self.PIN + 1, x1, self.PIN + 5, (.6, .75, .9))
        rect(img, x0, self.PIN + 1, x1, self.PIN + 2, (.85, .92, 1))
        ellipse(img, knob, self.PIN + 3, 4, 4, (.6, .75, .9))

    @staticmethod
    def _glove(img, x, y):
        line(img, x, y, x, y + 7, (.95, .95, .95), w=3.5)
        ellipse(img, x + 2, y + 10, 4.5, 4, (.95, .95, .95))
        line(img, x + 4, y + 8, x + 7, y + 9, (.95, .95, .95), w=2.5)

    def _scene(self, img, t, try2):
        img[:] = self.bg
        F, P = self.FLOOR, self.PIN + 6
        base = F - LEG * self.HH
        pa = -36 * _ease(_u(t, 6.6, 7.1)) if try2 else 0.0
        pb = 0.0 if try2 else 36 * _ease(_u(t, 1.6, 2.1))
        charred = not try2 and t > 2.6
        if try2:
            self._lava(img, self.D1, 32, self.R0, self.PIN + 1, t)
            gtop = 36 + 30 * _u(t, 7.1, 7.9)
            self._gold(img, self.L1, gtop, self.D0, self.PIN + 1)
        else:
            ltop = 32 + 35 * _u(t, 2.1, 2.9)
            self._lava(img, self.D1, ltop, self.R0, self.PIN + 1, t)
            self._gold(img, self.L1, 36, self.D0, self.PIN + 1)
        sk, sh, pn = (((.14, .11, .11), (.18, .14, .14), (.1, .1, .1)) if charred
                      else (SKINS[0], (.2, .7, .3), (.3, .25, .5)))
        if not (try2 and t > 8.0):
            hx, hy, r = toon(img, self.HX, base, self.HH, sk, sh, t, arms=(0.4, 0.4), mood=-1 if t > 0.8 else 0,
                             look=(0, -1) if t < 2.6 or try2 else (0, 0), seed=16, pants=pn)
            if charred:
                for k in range(3):
                    ph = (t * 0.8 + k / 3) % 1
                    ellipse(img, hx + 3 * math.sin(ph * 9 + k), hy - r - 2 - 16 * ph, 1.5 + 3 * ph, 1.5 + 3 * ph,
                            (.5, .5, .5), a=0.7 * (1 - ph))
        if not try2 and 2.1 < t < 3.9:              # the lava comes down
            if t < 2.95:
                self._lava(img, self.D1, P, self.R0, P + (F - P) * _u(t, 2.1, 2.3), t)
            pool = F - 30 * _u(t, 2.3, 2.9) + 30 * _u(t, 3.3, 3.9)
            self._lava(img, self.L1, pool, self.R0, F, t, cool=_u(t, 3.0, 3.4))
        if try2 and t > 7.1:                        # the gold comes down
            if t < 7.95:
                self._gold(img, self.L1, P, self.D0, P + (F - P) * _u(t, 7.1, 7.3), int(t * 60))
            self._gold(img, self.L1, F - 36 * _ease(_u(t, 7.3, 8.1)), self.R0, F, int(t * 60) if t < 8.1 else 0)
        self._pin(img, self.L1 + pa, self.D0 + pa, 13 + pa)
        self._pin(img, self.D1 + pb, self.R0 + pb, 115 + pb)
        rect(img, self.L0, self.PIN, self.L1, self.PIN + 6, (.55, .5, .45))
        rect(img, self.R0, self.PIN, self.R1, self.PIN + 6, (.55, .5, .45))
        self._pin(img, self.L0 + pa, self.L1 + pa, 13 + pa) if pa else None
        if try2:
            u = _ease(_u(t, 5.6, 6.6))
            gx, gy = 110 + (13 - 110) * u + pa, 118 + (69 - 118) * u
        else:
            u = _ease(_u(t, 0.6, 1.6))
            gx, gy = 70 + (115 - 70) * u + pb, 120 + (69 - 120) * u
        self._glove(img, gx, gy)

    def draw(self, img, t):
        if t < 5.0:
            self._scene(img, t, False)
            if t > 3.7:
                words(img, "FAIL!", 22 + 3 * math.sin(t * 8), (1, .15, .1), scale=3, shadow=(.95, .9, .8))
        elif t < 5.6:                               # rewind
            self._scene(img, 5.0 - (t - 5.0) * 8.3, False)
            for b in range(0, N, 16):
                img[b:b + 16] = np.roll(img[b:b + 16], int(6 * math.sin(t * 40 + b)), 1)
            draw.text(img, "<<", 4, 4, (.9, .9, .9), scale=2)
        else:
            self._scene(img, t, True)
            if t > 8.6:                             # still in there, delighted
                y = 70 - 6 * _ease(_u(t, 8.6, 8.9))
                line(img, self.HX + 9, 74, self.HX + 11, y - 4, (.2, .7, .3), w=3)
                ellipse(img, self.HX + 11, y - 6, 2.5, 2.5, SKINS[0])
                line(img, self.HX + 11, y - 8, self.HX + 11, y - 12, SKINS[0], w=2)
                face(img, self.HX, y, 6, SKINS[0], t, mood=1, seed=16)
                self._gold(img, self.HX - 10, 70, self.HX + 14, 76)
                words(img, "YOU WIN!", 24 + 2 * math.sin(t * 6), (.3, 1, .3), scale=2, shadow=(.05, .2, .05))
        caption(img, cue(t, [(0, "ONLY 1% CAN SOLVE!"), (3.7, ""), (9.4, "LEVEL 2 OF 9000")])[1])


CHANNELS = [Slice, Rock, Mattress, Perfume, Car, Vacuum, Breakfast, Bars, Burger, Sunscreen, ButWait, Walkable, Dazzle,
            Stik, Hair, PinPull]
