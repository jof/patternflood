"""Kids' TV, nature documentaries, science, how-it's-made, cooking, PSAs and lessons from other dimensions."""
import math

import numpy as np

from .. import draw
from ..draw import N, X, Y
from .kit import (BLACK, LEG, SKINS, WHITE, caption, chatter, cue, ellipse, face, hand, line, poly, rect, star, toon, vgrad,
                  words)
from .shows import Show


def _clip(u):
    return min(1.0, max(0.0, u))


def _ease(u):
    u = _clip(u)
    return u * u * (3 - 2 * u)


def _bump(t, t0, t1, ramp=0.4):
    """0 before t0, easing up to 1, held, and easing back to 0 by t1."""
    return min(_ease((t - t0) / ramp), _ease((t1 - t) / ramp))


def _dizzy(img, x, y, t, r=9.0):
    for k in range(3):
        a = t * 6 + k * 2.1
        star(img, x + r * math.cos(a), y + 3 * math.sin(a), 2.5, (1, .9, .2), n=5, inner=0.45)


def _sprite(paint, w, h):
    """Paint something centred on (64, 64) once, and keep it as a w x h sprite: (rgb, alpha)."""
    a, b = np.zeros((N, N, 3), np.float32), np.ones((N, N, 3), np.float32)
    paint(a, 64, 64)
    paint(b, 64, 64)
    alpha = np.clip(1 - (b - a).mean(-1, keepdims=True), 0, 1)
    rgb = a / np.maximum(alpha, 1e-3)
    y0, x0 = 64 - h // 2, 64 - w // 2
    return rgb[y0:y0 + h, x0:x0 + w].copy(), alpha[y0:y0 + h, x0:x0 + w].copy()


def _blit(img, spr, x, y):
    """A sprite centred at (x, y), to the nearest pixel, clipped to the screen."""
    rgb, a = spr
    h, w = a.shape[:2]
    x0, y0 = int(round(x)) - w // 2, int(round(y)) - h // 2
    sx, sy = max(0, -x0), max(0, -y0)
    ex, ey = min(w, N - x0), min(h, N - y0)
    if sx >= ex or sy >= ey:
        return
    region = img[y0 + sy:y0 + ey, x0 + sx:x0 + ex]
    region += (rgb[sy:ey, sx:ex] - region) * a[sy:ey, sx:ex]


def _eyes(img, x, y, r, t, look=(0.0, 0.0), seed=0.0, shock=False):
    """A pair of cartoon eyes, r each, centred on (x, y)."""
    for dx in (-1.25 * r, 1.25 * r):
        if (t * 0.37 + seed * 0.13) % 1.0 < 0.04 and not shock:
            line(img, x + dx - r, y, x + dx + r, y, BLACK, w=max(1.0, r * 0.35))
            continue
        ellipse(img, x + dx, y, r, r * 1.15, WHITE)
        p = 0.35 if shock else 0.55
        ellipse(img, x + dx + look[0] * r * 0.4, y + look[1] * r * 0.4, r * p, r * p * 1.1, BLACK)


# ---------------------------------------------------------------- kids' TV

class Socko(Show):
    """Silent: a sock puppet with ambitions."""
    num, title, length = 501, "SOCKO'S BIG DREAM", 11.0
    C = 90
    SOCK, STRIPE, MOUTH = (.9, .15, .25), (1, .9, .35), (.35, .02, .08)
    LAUNCH = 5.6

    def __init__(self):
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.5, .8, .95), (.9, .75, .95), 0, self.C)
        for j in range(7):
            for i in range(10):
                ellipse(bg, i * 14 + 7 * (j % 2), j * 14 + 4, 2.5, 2.5, WHITE, a=0.3)
        rect(bg, 5, 6, 47, 48, (.95, .8, .3))       # a window, with a painted moon
        rect(bg, 8, 9, 44, 45, (.06, .08, .25))
        rng = np.random.default_rng(self.num)
        for _ in range(14):
            ellipse(bg, rng.uniform(10, 42), rng.uniform(11, 43), .7, .7, (1, 1, .8))
        ellipse(bg, 22, 30, 9, 9, (.95, .93, .75))
        ellipse(bg, 19, 28, 2, 2, (.8, .78, .6))
        ellipse(bg, 25, 33, 1.5, 1.5, (.8, .78, .6))
        rect(bg, 0, self.C, N, N, (.85, .2, .55))
        rect(bg, 0, self.C, N, self.C + 4, (1, .8, .2))
        for k in range(6):
            star(bg, 11 + k * 21, 104, 5, (1, .85, .3), n=5, inner=0.45)
        self.bg = bg

    def _sock(self, img, x, y, t, talk, look):
        rect(img, x - 10, y, x + 8, y + 72, self.SOCK)
        for k in range(5):
            rect(img, x - 10, y + 14 + k * 12, x + 8, y + 19 + k * 12, self.STRIPE)
        ellipse(img, x + 2, y, 16, 12, self.SOCK)
        if talk > 0.05:
            poly(img, [(x + 2, y + 3), (x + 20, y + 1 - 8 * talk), (x + 20, y + 4 + 6 * talk)], self.MOUTH)
        else:
            line(img, x + 4, y + 3, x + 17, y + 2, self.MOUTH, w=1.5)
        for k, (ex, ey) in enumerate(((x - 3, y - 8), (x + 8, y - 9))):
            ellipse(img, ex, ey, 4.5, 4.5, WHITE)
            ellipse(img, ex + look[0] * 2 + 0.6 * math.sin(t * 13 + k * 2), ey + look[1] * 2 + 0.6 * math.cos(t * 11 + k),
                    2, 2, BLACK)
        for k in (-1, 0, 1):
            line(img, x - 4 + k * 3, y - 10, x - 6 + k * 5, y - 18 + abs(k) * 2, (1, .55, .1), w=1.5)

    def _hand(self, img, x, y, o, d):
        sk, dk = SKINS[0], (.8, .55, .45)
        rect(img, x - 7, y + 4, x + 7, self.C + 1, sk)
        ellipse(img, x, y + 2, 9, 9, sk)
        ellipse(img, x + d * 9, y - 4, 12, 5, sk)
        ellipse(img, x + d * 8, y + 8 + 3 * o, 10, 3.5, sk, rot=d * 0.4 * o)
        for k in range(3):
            line(img, x + d * (11 + k * 4), y - 6, x + d * (11 + k * 4), y - 1, dk, w=1)

    def draw(self, img, t):
        img[:] = self.bg
        x, y = 62, 44
        if t >= self.LAUNCH:                        # left behind
            u = t - self.LAUNCH
            d = 1 if u < 1.4 or 2.0 < u < 2.5 else -1
            o = 0.0
            hx = x
            if u > 2.6:
                hx = x + 3 * math.sin(t * 9)
                o = max(0.0, math.sin(t * 9))
            hy = 66 if u > 1.2 else max(66.0, 44 - 160 * u * u + 82)
            self._hand(img, hx, hy, o, d)
        if t < self.LAUNCH:
            talk = chatter(t) if t < 2.6 else 0
            look = (1, 0) if t < 2.6 else (0.4, -1)
            rumble = t > 4.4
            self._sock(img, x + (1.5 * math.sin(t * 60) if rumble else 0), y + (2 * math.sin(t * 4) if t < 2.6 else 0),
                       t, talk, look)
        elif t < self.LAUNCH + 1.2:
            u = t - self.LAUNCH
            sy = y - 160 * u * u
            self._sock(img, x, sy, t, 0, (0, -1))
            fy = sy + 74
            f = 1 + 0.25 * math.sin(t * 50)
            ellipse(img, x - 1, fy + 6 * f, 8, 10 * f, (1, .45, .1))
            ellipse(img, x - 1, fy + 3 * f, 4.5, 6 * f, (1, .9, .4))
        img[self.C:] = self.bg[self.C:]             # the counter, in front of all of it
        if self.LAUNCH - 1.2 < t < self.LAUNCH + 2.5:
            for k in range(6):
                u = (t * 0.9 + k / 6) % 1.0
                s = _clip((t - self.LAUNCH + 1.2) / 0.6) * _clip((self.LAUNCH + 2.5 - t) / 0.8)
                ellipse(img, 40 + k * 9 + 6 * math.sin(k * 3 + t), self.C - 2 - 26 * u, (4 + 8 * u) * s, (3 + 6 * u) * s,
                        (.75, .75, .8), a=0.8 * (1 - u))
        if t > 8.0:                                 # meanwhile, on the moon
            rect(img, 16, 15, 20, 21, self.SOCK)
            ellipse(img, 18, 15, 2.5, 2, self.SOCK)
            ellipse(img, 19, 14.5, .8, .8, WHITE)
            line(img, 27, 11, 27, 22, WHITE, w=1)
            rect(img, 27, 11, 33, 15, self.SOCK)
            if t % 1.0 < 0.5:
                star(img, 34, 9, 2.5, (1, 1, .7), n=4, inner=0.3)
        if t < 2.6:
            caption(img, "HI KIDS! IT'S SOCKO!")
        elif t < self.LAUNCH:
            caption(img, "SOCKO HAS A DREAM.")
        elif t > 8.0:
            caption(img, "WE'RE SO PROUD.")


class Ducks(Show):
    """Counting ducks, until there's one."""
    num, title, length = 507, "COUNT THE DUCKS", 10.0
    LEVELS = [(0, 1, "ONE!"), (1.3, 2, "FOUR!"), (2.4, 3, "NINE!"), (3.3, 4, "16!"), (4.0, 6, "36!"),
              (4.55, 8, "64!"), (5.0, 12, "144!"), (5.35, 16, "256!"), (5.65, 24, "576!"), (5.9, 32, "1024!"),
              (6.15, 64, "4096!")]
    WHOLE = 6.8

    @staticmethod
    def _duck(img, quack=0.0, blink=False, mono=False):
        y1, y2, org, org2 = (1, .85, .1), (1, .72, .05), (1, .5, .05), (.9, .4, .05)
        if mono:
            img[:] = 0
            y1 = y2 = org = org2 = WHITE
        else:
            vgrad(img, (.45, .75, 1), (.7, .88, 1), 0, 86)
            vgrad(img, (.15, .45, .85), (.06, .22, .55), 86, N)
            for k in range(5):
                line(img, 8 + k * 26, 96 + (k % 2) * 14, 20 + k * 26, 96 + (k % 2) * 14, (.4, .65, .95), w=1.5)
        cx, cy = 50, 70
        poly(img, [(cx - 34, cy + 2), (cx - 48, cy - 14), (cx - 26, cy - 6)], y1)
        ellipse(img, cx, cy + 10, 38, 24, y1)
        ellipse(img, cx + 28, cy - 22, 19, 18, y1)
        ellipse(img, cx + 47, cy - 15 + 6 * quack, 12, 3.5, org2, rot=0.35 * quack)
        ellipse(img, cx + 49, cy - 20, 13, 4.5, org)
        if not mono:
            ellipse(img, cx - 6, cy + 8, 20, 11, y2, rot=-0.25)
            if blink:
                line(img, cx + 29, cy - 27, cx + 37, cy - 27, BLACK, w=1.5)
            else:
                ellipse(img, cx + 33, cy - 27, 4, 4.5, BLACK)
                ellipse(img, cx + 34.5, cy - 29, 1.2, 1.2, WHITE)

    def __init__(self):
        base, mono = np.empty((N, N, 3), np.float32), np.empty((N, N, 3), np.float32)
        self._duck(base)
        self._duck(mono, mono=True)
        mask = mono[..., :1]
        self.frames = []
        for _, n, _ in self.LEVELS:
            if n == 1:
                self.frames.append(base)
                continue
            c = N / n
            ci, cj = np.floor((X + 0.5) / c), np.floor((Y + 0.5) / c)
            sx = np.clip(((X + 0.5) / c - ci) * N, 0, N - 1).astype(int)
            sy = np.clip(((Y + 0.5) / c - cj) * N, 0, N - 1).astype(int)
            cx = np.clip((ci + 0.5) * c, 0, N - 1).astype(int)
            cy = np.clip((cj + 0.5) * c, 0, N - 1).astype(int)
            small, cell = base[sy, sx], base[cy, cx]
            w = min(0.9, (n - 1) / 5)
            self.frames.append(small * (1 - w) + w * np.clip(cell * (0.55 + 0.6 * mask[sy, sx]), 0, 1))

    def draw(self, img, t):
        if t < self.WHOLE:
            i, (n, say), lt = cue(t, [(a, (b, c)) for a, b, c in self.LEVELS])
            img[:] = self.frames[i]
            if t > self.WHOLE - 0.5:
                u = (t - self.WHOLE + 0.5) / 0.5
                img += (self.frames[0] - img) * u
            if t < 1.3:
                say = "LET'S COUNT DUCKS!" if t < 0.8 else say
            pop = 1 + (lt < 0.12 and i < 4)
        else:
            lt = t - self.WHOLE
            q = max(0.0, math.sin((lt - 1.4) * 9)) if 1.4 < lt < 2.4 else 0
            self._duck(img, quack=q, blink=2.9 < lt < 3.05)
            say, pop = "ONE." if lt > 0.6 else "", 1
        if say:
            sc = 1 if say.startswith("LET") else 2
            rect(img, 0, 104, N, N, (.05, .1, .3), a=0.7)
            words(img, say, 106 + (sc == 1) * 6 - (pop - 1) * 2, (1, .9, .2), scale=sc)


class Shapes(Show):
    """Learn your shapes: circle, square, triangle, and that."""
    num, title, length = 514, "SHAPE PALS", 11.0

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (1, .95, .75), (1, .82, .85))
        for k, c in enumerate([(1, .6, .6), (1, .85, .5), (.7, .9, .6), (.6, .8, 1)]):
            ring = np.abs(np.hypot(X - 64, Y - 150) - (110 - k * 7)) < 3
            self.bg[ring] = self.bg[ring] * 0.5 + np.asarray(c, np.float32) * 0.5
        self.ang = np.linspace(0, 2 * math.pi, 48, endpoint=False)

    def _pal(self, img, kind, x, y, s, t, scared, seed):
        if s <= 0.02:
            return
        if kind == 0:
            ellipse(img, x, y, 15 * s, 15 * s, (.95, .2, .25))
        elif kind == 1:
            rect(img, x - 14 * s, y - 14 * s, x + 14 * s, y + 14 * s, (.2, .45, .95))
        else:
            poly(img, [(x, y - 19 * s), (x + 17 * s, y + 12 * s), (x - 17 * s, y + 12 * s)], (.2, .75, .3))
            y += 2 * s
        _eyes(img, x, y - 3 * s, 3.2 * s, t, look=(0.6 * (scared and kind != 1) * (1 if kind == 0 else -1), 0.5 * scared),
              seed=seed, shock=scared)
        if scared:
            ellipse(img, x, y + 6 * s, 2.5 * s, 3 * s, (.25, .02, .05))
        else:
            for a, b in ((-4, 0), (0, 4)):
                line(img, x + a * s, y + (5 + (a == 0) * 2 - (b == 0) * 0) * s, x + b * s, y + (5 + (b == 0) * 2) * s,
                     (.2, .05, .05), w=1.2)

    def draw(self, img, t):
        img[:] = self.bg
        scared = 6.6 < t < 9.6
        flee = _ease((t - 6.6) / 0.6) * (1 - _ease((t - 9.6) / 0.8))
        shake = math.sin(t * 50) * 1.2 if scared else 0
        pals = [(0, 24 - 14 * flee, 0.0), (1, 64, 2.0), (2, 104 + 14 * flee, 4.0)]
        for kind, x, t0 in pals:
            u = (t - t0) / 0.35
            s = 0 if u < 0 else 1.25 - 0.25 * math.cos(min(u, 3) * math.pi) * math.exp(-u) if u < 3 else 1
            y = 40 - (36 * flee if kind == 1 else 0)
            self._pal(img, kind, x + shake, y, min(s, 1.3), t, scared, kind + 1)
        if t > 6.0:                                 # and this
            rise = _ease((t - 6.0) / 1.2)
            cx, cy = 64, 150 - 76 * rise
            k = self.ang
            r = 30 * (1 + 0.16 * np.sin(3 * k + 2 * t) + 0.1 * np.sin(5 * k - 3 * t) + 0.06 * np.sin(9 * k + 5 * t))
            col = draw.hsv1(t * 0.2, 0.7, 1)
            poly(img, np.stack([cx + r * np.cos(k), cy + 0.85 * r * np.sin(k)], 1), col)
            if t > 9.0:                             # it waves
                a = -0.9 + 0.5 * math.sin(t * 7)
                ex, ey = cx + 30, cy - 10
                for j in range(5):
                    line(img, ex + j * 4 * math.cos(a + j * 0.3), ey + j * 4 * math.sin(a + j * 0.3),
                         ex + (j + 1) * 4 * math.cos(a + (j + 1) * 0.3), ey + (j + 1) * 4 * math.sin(a + (j + 1) * 0.3),
                         col, w=5 - j * 0.7)
            for j, (dx, dy, er) in enumerate([(-14, -14, 4.5), (2, -18, 3), (15, -10, 5.5), (-4, -4, 2.5), (10, 2, 3.5),
                                              (-17, 2, 3)]):
                bl = (t * 0.5 + j * 0.37) % 1.0 < 0.06
                ex, ey = cx + dx + 1.5 * math.sin(t * 2 + j), cy + dy
                if bl:
                    line(img, ex - er, ey, ex + er, ey, BLACK, w=1.2)
                else:
                    ellipse(img, ex, ey, er, er, WHITE)
                    ellipse(img, ex + er * 0.3 * math.sin(t * 1.3 + j), ey + er * 0.2, er * 0.5, er * 0.5, BLACK)
            for j in range(6):
                line(img, cx - 12 + j * 4, cy + 12 + 2 * (j % 2), cx - 8 + j * 4, cy + 12 + 2 * ((j + 1) % 2),
                     (.2, .02, .1), w=1.5)
        say = cue(t, [(0, "THIS IS A CIRCLE."), (2, "THIS IS A SQUARE."), (4, "THIS IS A TRIANGLE."),
                      (6, "AND THIS IS..."), (8.0, "...WE DON'T KNOW."), (9.6, "SAY HI, KIDS!")])[1]
        caption(img, say, rgb=(1, 1, .7), bg=(.35, .1, .45))


# ---------------------------------------------------------------- nature

class Lamp(Show):
    """Nature: a desk lamp hunts a moth."""
    num, title, length = 520, "WILD LAMPS", 11.5
    G = 108
    METAL, GRASS, WARM = (.2, .65, .6), (.12, .06, .07), (1, .95, .6)
    POUNCE = 5.9

    def __init__(self):
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.22, .08, .32), (1, .5, .2), 0, 94)
        ellipse(bg, 96, 94, 15, 15, (1, .82, .35), half="top")
        rect(bg, 0, 94, N, N, (.22, .1, .1))
        dark = (.1, .04, .08)
        line(bg, 26, 94, 29, 58, dark, w=3)
        line(bg, 28, 66, 18, 54, dark, w=2)
        line(bg, 29, 62, 40, 52, dark, w=2)
        ellipse(bg, 29, 50, 22, 4.5, dark)
        ellipse(bg, 22, 47, 11, 3.5, dark)
        self.bg = bg
        g = np.zeros((N, N, 3), np.float32)
        rng = np.random.default_rng(self.num)
        for _ in range(110):
            x, h = rng.uniform(-2, 130), rng.uniform(8, 20)
            line(g, x, 116, x + rng.uniform(-6, 6), 116 - h, WHITE, w=1.6)
        rect(g, 0, 112, N, N, WHITE)
        self.grass = g[80:, :, :1].copy()

    @staticmethod
    def _joints(bx, by, a1, a2, aim):
        x1, y1 = bx, by - 2
        x2, y2 = x1 + 31 * math.sin(a1), y1 - 31 * math.cos(a1)
        x3, y3 = x2 + 28 * math.sin(a2), y2 - 28 * math.cos(a2)
        dx, dy = math.cos(aim), math.sin(aim)
        return x1, y1, x2, y2, x3, y3, x3 + 17 * dx, y3 + 17 * dy, dx, dy

    def _lamp(self, img, bx, by, a1, a2, aim, on):
        m = self.METAL
        x1, y1, x2, y2, x3, y3, mx, my, dx, dy = self._joints(bx, by, a1, a2, aim)
        ellipse(img, bx, by, 13, 4.5, m)
        line(img, x1, y1, x2, y2, m, w=3.5)
        line(img, x2, y2, x3, y3, m, w=3.5)
        ellipse(img, x2, y2, 3, 3, (.1, .3, .3))
        px, py = -dy, dx
        bx2, by2 = x3 - 3 * dx, y3 - 3 * dy
        poly(img, [(bx2 + 4 * px, by2 + 4 * py), (mx + 12 * px, my + 12 * py), (mx - 12 * px, my - 12 * py),
                   (bx2 - 4 * px, by2 - 4 * py)], m)
        ellipse(img, mx - dx, my - dy, 5.5, 5.5, self.WARM if on else (.45, .45, .4))
        return mx, my, dx, dy

    def _beam(self, img, mx, my, dx, dy):
        vx, vy = X + 0.5 - mx, Y + 0.5 - my
        along = vx * dx + vy * dy
        perp = np.abs(vx * dy - vy * dx)
        cov = np.clip((11 + along * 0.55 - perp) * 0.5, 0, 1) * (along > 0) * 0.5 * np.exp(-along / 90)
        img += (np.asarray(self.WARM, np.float32) - img) * cov[..., None]

    @staticmethod
    def _moth(img, x, y, t):
        f = 0.4 + 0.6 * abs(math.sin(t * 22))
        for s in (-1, 1):
            ellipse(img, x + s * 3, y - 1, 3.2, 3 * f, (.95, .9, .75), rot=s * 0.4)
        ellipse(img, x, y, 1.2, 2.8, (.45, .35, .25))

    def draw(self, img, t):
        img[:] = self.bg
        crouch = (0.95, -1.4, math.pi + 0.25)
        tall = (0.15, -1.1, math.pi + 0.62)
        on = t > self.POUNCE + 0.7
        if t < 3.2:                                 # the stalk: slink, freeze, slink
            p = t / 3.2
            bx, by, pose = 150 - 52 * (p - math.sin(2 * math.pi * 4 * p) / (2 * math.pi * 4)), self.G, crouch
        elif t < self.POUNCE:
            bx, by, pose = 98, self.G, crouch
            if t > self.POUNCE - 1.1:               # the wiggle
                w = math.sin(t * 28)
                bx, pose = 98 + 2.5 * w, (crouch[0] + 0.12 * w, crouch[1], crouch[2])
        elif t < self.POUNCE + 0.6:
            u = (t - self.POUNCE) / 0.6
            bx, by = 98 - 36 * u, self.G - 34 * math.sin(math.pi * u)
            pose = tuple(a + (b - a) * _ease(u * 1.3) for a, b in zip(crouch, tall))
        else:
            bx, by, pose = 62, self.G, tall
            u = t - self.POUNCE - 0.6
            if u < 0.25:
                by += 2 * math.sin(u * 40) * (1 - u * 4)
        if on:                                      # predict the beam from the pose
            mx, my, dx, dy = self._joints(bx, by, *pose)[6:]
            self._beam(img, mx, my, dx, dy)
        mx, my, dx, dy = self._lamp(img, bx, by, *pose, on)
        sl = img[80:]
        sl += (np.asarray(self.GRASS, np.float32) - sl) * self.grass
        if not on:
            self._moth(img, 34 + 9 * math.sin(t * 1.3), 58 + 6 * math.sin(t * 2.1), t)
        else:
            u = t - self.POUNCE - 0.7
            hx, hy = 34 + 9 * math.sin(t * 1.3), 58 + 6 * math.sin(t * 2.1)
            k = _ease(u / 0.6)
            b = abs(math.sin(t * 5))
            tx, ty = mx + dx * (7 + 12 * b) + 3 * math.sin(t * 3), my + dy * (5 + 12 * b)
            x, y = hx + (tx - hx) * k, hy + (ty - hy) * k
            self._moth(img, x, y, t)
            if k >= 1 and b < 0.25:
                star(img, mx + dx * 7, my + dy * 7, 3, WHITE, n=4, inner=0.3)
            if u > 1.5:
                hy2 = y - 6 - (u * 10) % 18
                for s in (-1.4, 1.4):
                    ellipse(img, x + 5 + s, hy2, 1.8, 1.8, (1, .3, .45))
                poly(img, [(x + 2, hy2 + 0.6), (x + 8, hy2 + 0.6), (x + 5, hy2 + 4.5)], (1, .3, .45))
        say = cue(t, [(0, "THE DESK LAMP."), (3.2, "A PATIENT HUNTER."), (self.POUNCE, ""), (self.POUNCE + 2.0, "A PERFECT MATCH.")])[1]
        if say:
            caption(img, say, rgb=(1, .95, .8), a=0.5)


class Geese(Show):
    """Nature: the geese fly south, in formation, then do the quarterly report."""
    num, title, length = 526, "THE MIGRATION", 11.5
    DIVE = 9.4

    def __init__(self):
        self.bg = np.empty((N, N, 3), np.float32)
        vgrad(self.bg, (.3, .55, .95), (.8, .9, 1))
        for k in range(6):
            ellipse(self.bg, k * 26, 128, 22, 12, (.45, .6, .7))
        v = [(88, 52)] + [(88 - 7 * k, 52 + s * 5 * k) for k in range(1, 8) for s in (-1, 1)]
        grid = [(34 + 15 * i, 34 + 14 * j) for i in range(5) for j in range(3)]
        bars = [(34 + 15 * i, 94 - 12 * j) for i in range(5) for j in range(i + 1)]
        arrow = [(20 + 6.6 * k, 26 + 6 * k) for k in range(11)] + [(86, 74), (86, 62), (74, 86), (62, 86)]
        self.shapes = [sorted(s) for s in (v, grid, bars, arrow)]
        self.frames = []
        for f in np.linspace(-1, 1, 6):
            self.frames.append(_sprite(lambda img, x, y, f=f: self._goose(img, x, y, f), 22, 18))

    @staticmethod
    def _goose(img, x, y, f):
        line(img, x - 1, y - 1, x - 4, y - 1 - 7 * f, (.45, .4, .35), w=2.2)
        ellipse(img, x, y, 5.5, 2.4, (.35, .3, .25))
        line(img, x + 3, y - 0.5, x + 8, y - 2.5, BLACK, w=1.6)
        ellipse(img, x + 8.5, y - 2.8, 1.8, 1.5, BLACK)
        ellipse(img, x + 8, y - 1.6, 1.2, 0.7, WHITE)
        line(img, x - 4, y + 0.5, x - 7, y + 0.5, BLACK, w=1.5)

    def draw(self, img, t):
        img[:] = self.bg
        for k in range(3):
            cx = (k * 67 + 40 - t * 22) % 190 - 30
            cy = 18 + k * 21
            for dx, r in ((-8, 6), (0, 9), (9, 6)):
                ellipse(img, cx + dx, cy, r, r * 0.6, (1, 1, 1), a=0.8)
        stages = [0.0, 3.0, 5.5, 8.0]
        i = max(k for k, s in enumerate(stages) if t >= s)
        axes = _ease((t - 5.5) / 0.8) * (1 - _ease((t - self.DIVE - 0.8) / 0.6))
        if axes > 0:
            line(img, 24, 102, 112, 102, (.1, .15, .3), w=1.5, a=axes)
            line(img, 24, 102, 24, 22, (.1, .15, .3), w=1.5, a=axes)
        drop = 160 * max(0.0, t - self.DIVE) ** 2
        for k in range(15):
            u = _ease((t - stages[i] - k * 0.03) / 1.2) if i else 1
            ax, ay = self.shapes[max(0, i - 1)][k]
            bx, by = self.shapes[i][k]
            x, y = ax + (bx - ax) * u, ay + (by - ay) * u
            f = int((math.sin(t * 9 + k * 0.7) * 0.5 + 0.5) * 5.99) if drop == 0 else 5
            _blit(img, self.frames[f], x + drop * 0.7, y + drop)
        if t > self.DIVE + 1.0:                     # what's left
            u = t - self.DIVE - 1.0
            ellipse(img, 70 + 8 * math.sin(u * 3), 10 + 22 * u, 3, 1.2, WHITE, rot=0.5 * math.sin(u * 3))
        say = cue(t, [(0, "THE GEESE FLY SOUTH."), (3, "IN PERFECT FORMATION."), (5.5, "Q3 WAS STRONG."), (8, "Q4.")])[1]
        caption(img, say, rgb=(1, 1, .85), a=0.55)


class Commute(Show):
    """Nature: the clownfish commute."""
    num, title, length = 532, "RUSH HOUR REEF", 11.5
    LX, STOPX, SAND = 102, 86, 112
    QUEUE = [(74, 48), (52, 48), (30, 48), (77, 70), (55, 70), (33, 70), (73, 92), (51, 92)]

    def __init__(self):
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.08, .45, .7), (.02, .15, .35), 0, self.SAND)
        shaft = (np.sin((X * 0.8 + Y * 0.45) * 0.09) > 0.75)[..., None] * (Y < self.SAND)[..., None]
        bg += shaft * np.float32(0.07) * (1 - Y / N)[..., None]
        rect(bg, 0, self.SAND, N, N, (.75, .65, .4))
        for k in range(6):
            rect(bg, 6 + k * 21, self.SAND + 6, 18 + k * 21, self.SAND + 10, (.95, .92, .8))
        for k, (x, h) in enumerate(((8, 40), (14, 28), (120, 34))):
            for j in range(7):
                line(bg, x + 3 * math.sin(j), self.SAND - j * h / 7, x + 3 * math.sin(j + 1), self.SAND - (j + 1) * h / 7,
                     (.15, .55, .3), w=3)
        rect(bg, self.LX - 1, 30, self.LX + 2, self.SAND, (.3, .3, .32))
        rect(bg, self.LX - 6, 14, self.LX + 7, 44, (.15, .15, .15))
        self.bg = bg
        self.fish = [_sprite(lambda img, x, y, w=w, c=c: self._fish(img, x, y, w, c), 34, 28)
                     for w in (-1, 1) for c in (False, True)]

    @staticmethod
    def _fish(img, x, y, wob, coffee):
        org = (1, .45, .08)
        poly(img, [(x - 7, y), (x - 14, y - 6 - wob), (x - 14, y + 6 - wob)], org)
        ellipse(img, x, y, 10, 6.5, org)
        ellipse(img, x - 1, y, 2, 6.2, WHITE)
        ellipse(img, x + 5.5, y - 2, 1.6, 1.6, BLACK)
        poly(img, [(x + 2.5, y + 4), (x + 5, y + 4), (x + 4, y + 11 + wob * 0.5)], (.1, .15, .5))
        if coffee:
            rect(img, x + 8, y + 2, x + 12, y + 8, WHITE)
            rect(img, x + 7.5, y + 1, x + 12.5, y + 2.5, (.4, .25, .15))
        else:
            line(img, x - 3, y + 5, x - 3, y + 8, BLACK, w=1)
            rect(img, x - 8, y + 8, x + 2, y + 13, (.45, .25, .1))

    def draw(self, img, t):
        img[:] = self.bg
        if t < 3.0 or t > 6.2:
            light = 0
        elif t < 3.3 or t > 5.8:
            light = 1
        else:
            light = 2
        for k, c in enumerate(((1, .1, .1), (1, .75, .1), (.1, 1, .3))):
            ellipse(img, self.LX + 0.5, 21 + k * 9, 3.5, 3.5, c if light == k else tuple(v * 0.2 for v in c))
        go = max(0.0, t - 3.3)
        for k, (x, y) in enumerate(self.QUEUE):
            g = max(0.0, go - (74 - x) * 0.008)
            fx = x + 50 * g * g
            if fx > 150:
                continue
            w = int(t * 4 + k) % 2
            _blit(img, self.fish[w * 2 + (k == 4)], fx, y + 1.5 * math.sin(t * 2 + k))
        if t > 4.6:                                 # late
            u = t - 4.6
            x = -20 + (self.STOPX - 12 + 20) * _ease(u / 1.9) if u < 1.9 else self.STOPX - 12
            if u < 1.9:
                for j in range(3):
                    line(img, x - 24 - j * 3, 66 + j * 5, x - 16 - j * 3, 66 + j * 5, (.6, .85, 1), w=1, a=0.7)
            _blit(img, self.fish[int(t * 12) % 2 * 2], x, 70)
            if u > 2.4:                             # the sigh
                for j in range(3):
                    b = (t * 0.8 + j / 3) % 1.0
                    ellipse(img, x + 9 + 3 * math.sin(b * 9), 64 - 40 * b, 1.5 + b * 2, 1.5 + b * 2, (.7, .9, 1), a=0.8 - 0.6 * b)
        if t > 6.6:                                 # who it's for
            cx = 140 - 24 * (t - 6.6)
            cy = self.SAND + 4
            for s in (-1, 1):
                for j in range(3):
                    lx = cx + s * (4 + j * 3)
                    line(img, lx, cy, lx + s * 3, cy + 6 + 1.5 * math.sin(t * 16 + j + s), (.85, .2, .1), w=1.3)
            ellipse(img, cx, cy, 9, 5, (.9, .25, .1))
            for s in (-1, 1):
                ellipse(img, cx + s * 3, cy - 6, 1.5, 1.5, BLACK)
            line(img, cx - 8, cy - 2, cx - 12, cy - 22, (.6, .6, .6), w=1.2)
            ellipse(img, cx - 12, cy - 26, 6, 6, (.9, .1, .1))
            rect(img, cx - 16, cy - 27, cx - 8, cy - 25, WHITE)
        say = cue(t, [(0, "THE MORNING COMMUTE."), (3.0, ""), (7.6, "EVERY. SINGLE. DAY.")])[1]
        if say:
            caption(img, say, 0 if t > 3 else None, rgb=(.85, 1, 1), bg=(0, .05, .15), a=0.6)


class Lapse(Show):
    """Time-lapse: an apple tree grows, and its apples leave home."""
    num, title, length = 538, "TIME-LAPSE", 12.0
    STOP, SILL = 6.5, 96
    APPLES = [(46, 34), (64, 22), (80, 32), (58, 42), (74, 46)]
    LAND = [(96, 0.0), (106, 0.12), (88, 0.24), (116, 0.36), (80, 0.48)]

    def __init__(self):
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.9, .8, .6), (.75, .62, .45))
        rect(bg, 12, 4, 116, 64, (.95, .95, .92))
        rect(bg, 10, self.SILL, 118, self.SILL + 6, (.95, .95, .92))
        rect(bg, 10, self.SILL + 6, 118, self.SILL + 8, (.6, .5, .4))
        rect(bg, 0, 112, N, N, (.45, .3, .22))
        self.bg = bg

    def draw(self, img, t):
        img[:] = self.bg
        lapse = t < self.STOP
        ph = (t * 0.9) % 1.0
        day = 0.5 + 0.5 * math.sin(2 * math.pi * ph) if lapse else 1.0
        sky = tuple(n + (d - n) * day for n, d in zip((.04, .04, .18), (.45, .72, 1)))
        rect(img, 15, 7, 113, 61, sky)
        if lapse:
            if ph < 0.5:
                ellipse(img, 20 + 180 * ph, 40 - 60 * math.sin(math.pi * 2 * ph) * 0.4, 6, 6, (1, .9, .4))
            else:
                ellipse(img, 20 + 180 * (ph - 0.5), 36 - 24 * math.sin(math.pi * 2 * (ph - 0.5)), 4.5, 4.5, (.9, .9, .8))
        else:
            ellipse(img, 100, 18, 6, 6, (1, .9, .4))
        rect(img, 63, 7, 65, 61, (.95, .95, .92))
        rect(img, 15, 33, 113, 35, (.95, .95, .92))
        g = _clip((t - 0.3) / 5.2)
        sway = 2 * math.sin(t * 7) if t > 10.2 else 0
        top = 78 - 46 * g
        line(img, 64, 80, 64 + sway * 0.3, top, (.4, .3, .15), w=2 + 2.5 * g)
        for k in range(4):
            lg = _clip((g - k * 0.12) / 0.2) * (1 - _clip((g - 0.75) / 0.2))
            if lg > 0:
                s = -1 if k % 2 else 1
                ellipse(img, 64 + s * 6 * lg, 74 - k * 9, 6 * lg, 2.5 * lg, (.3, .7, .25), rot=-s * 0.4)
        c = _clip((g - 0.45) / 0.55)
        if c > 0:
            for dx, dy, rx, ry in ((0, 34, 32, 20), (-20, 40, 14, 11), (20, 40, 14, 11), (0, 22, 20, 12)):
                ellipse(img, 64 + dx * c + sway, dy + (34 - dy) * (1 - c), rx * c, ry * c, (.2, .6 - dy * .003, .2))
        pot = (.8, .4, .2)
        poly(img, [(51, 80), (77, 80), (73, self.SILL), (55, self.SILL)], pot)
        rect(img, 49, 77, 79, 82, (.9, .5, .25))
        for k, (ax, ay) in enumerate(self.APPLES):
            r = 4.5 * _clip((t - 4.4 - k * 0.2) / 1.2)
            if r <= 0:
                continue
            lx, d = self.LAND[k]
            legs = 0.0
            if t < 7.6 + d:
                x, y = ax + sway + (0.8 * math.sin(t * 40 + k) if 6.9 < t else 0), ay
            elif t < 8.2 + d:
                u = (t - 7.6 - d) / 0.6
                x, y = ax + (lx - ax) * u, ay + (self.SILL - 9 - ay) * u - 24 * math.sin(math.pi * u)
                legs = 1.0
            else:
                x, y, legs = lx - 36 * max(0.0, t - 8.6 - d * 0.5), self.SILL - 9, 2.0
            if legs:
                sw = 2.5 * math.sin(t * 18 + k) if legs > 1 else 1.5
                for s in (-1, 1):
                    line(img, x + s * 1.5, y + 3, x + s * 1.5 + s * sw * 0.5 + (sw if s > 0 else -sw) * 0.3, y + 9, BLACK, w=1.2)
            ellipse(img, x, y, r, r, (.9, .1, .12))
            line(img, x, y - r, x + 1, y - r - 2.5, (.35, .2, .1), w=1)
            if legs:
                for s in (-1.6, 1.6):
                    ellipse(img, x - 1.5 + s, y - 1, 0.9, 1.1, BLACK)
        if lapse:
            img *= np.float32(0.8 + 0.2 * day)
        rect(img, 0, 0, 52, 13, (0, 0, 0), a=0.6)
        draw.text(img, f"DAY {1 + int(89 * min(1.0, t / self.STOP))}", 4, 2, (1, .3, .3))
        if t > 9.6:
            caption(img, "THEY GROW UP SO FAST.")


# ---------------------------------------------------------------- how it's made, science, PSAs

class Holes(Show):
    """How it's made: holes."""
    num, title, length = 545, "HOW IT'S MADE", 12.5
    BELT, PRESS, CLAW, BOXX, FLOOR = 74, 40, 80, 110, 108
    STARTS = (0.0, 3.6)
    SPILL = 8.2
    HOLES = [(46, 0.0), (62, 0.1), (76, 0.2), (90, 0.3), (102, 0.4)]
    FLOORC = (.3, .3, .34)

    def __init__(self):
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.35, .42, .55), (.25, .3, .4), 0, 96)
        for k in range(7):
            rect(bg, 0, 12 + k * 12, N, 13 + k * 12, (.3, .36, .48))
        rect(bg, 0, 96, N, N, self.FLOORC)
        rect(bg, 0, 0, N, 4, (.2, .2, .22))
        rect(bg, 0, self.BELT, N, self.BELT + 6, (.12, .12, .14))
        for x in range(4, N, 16):
            rect(bg, x, self.BELT + 6, x + 3, 96, (.2, .2, .22))
        rect(bg, self.PRESS - 12, 4, self.PRESS + 12, 30, (.85, .6, .1))
        for k in range(4):
            line(bg, self.PRESS - 12 + k * 7, 30, self.PRESS - 6 + k * 7, 4, (.15, .15, .15), w=2)
        self.bg = bg

    def _plate(self, lt):
        """Where a plate is lt seconds into its trip, and whether it has a hole."""
        if lt < 1.0:
            x = -20 + (self.PRESS + 20) * _ease(lt)
        elif lt < 1.5:
            x = self.PRESS
        elif lt < 2.3:
            x = self.PRESS + (self.CLAW - self.PRESS) * _ease((lt - 1.5) / 0.8)
        elif lt < 3.0:
            x = self.CLAW
        else:
            x = self.CLAW + 70 * (lt - 3.0)
        return x, 1.2 <= lt < 2.65

    def _claw(self, t):
        """The claw's x, its tip's y, and whether it holds a hole."""
        for s in self.STARTS:
            lt = t - s
            if 2.3 <= lt < 2.65:
                return self.CLAW, 20 + 38 * _ease((lt - 2.3) / 0.3), False
            if 2.65 <= lt < 3.0:
                return self.CLAW, 58 - 38 * _ease((lt - 2.65) / 0.3), True
            if 3.0 <= lt < 3.5:
                return self.CLAW + (self.BOXX - self.CLAW) * _ease((lt - 3.0) / 0.5), 20, True
            if 3.5 <= lt < 4.3:
                return self.BOXX + (self.CLAW - self.BOXX) * _ease((lt - 3.6) / 0.6), 20, False
        return self.CLAW, 20, False

    def draw(self, img, t):
        img[:] = self.bg
        for x in range(int(-(t * 30) % 8) - 8, N, 8):
            rect(img, x, self.BELT + 1, x + 3, self.BELT + 3, (.25, .25, .28))
        for s in self.STARTS:
            x, hole = self._plate(t - s)
            if -20 < x < 150:
                rect(img, x - 10, self.BELT - 20, x + 10, self.BELT, (.7, .72, .75))
                rect(img, x - 10, self.BELT - 20, x + 10, self.BELT - 18, (.85, .87, .9))
                if hole:
                    ellipse(img, x, self.BELT - 10, 6, 6, BLACK)
        press = 0.0
        for s in self.STARTS:
            press = max(press, _bump(t - s, 1.0, 1.5, 0.15))
        rect(img, self.PRESS - 4, 30, self.PRESS + 4, 31 + 22 * press, (.6, .6, .65))
        rect(img, self.PRESS - 9, 30 + 22 * press, self.PRESS + 9, 34 + 22 * press, (.5, .5, .55))
        cx, cy, held = self._claw(t)
        line(img, cx, 4, cx, cy, (.15, .15, .15), w=1.2)
        rect(img, cx - 5, cy - 3, cx + 5, cy, (.9, .3, .1))
        if held:
            ellipse(img, cx, cy + 6, 6, 6, BLACK)
        for k in (-1, 1):
            line(img, cx + k * 4, cy, cx + k * (7 if held else 5), cy + 6, (.15, .15, .15), w=1.5)
        drops = sum(1 for s in self.STARTS if t - s >= 3.5)
        for s in self.STARTS:
            u = (t - s - 3.5) / 0.3
            if 0 <= u < 1:
                ellipse(img, self.BOXX, 26 + 60 * u * u, 6, 6, BLACK)
        tip = _ease((t - self.SPILL) / 0.4)
        bw, bh = 26, 20
        bx0, by0 = self.BOXX - bw / 2, self.FLOOR - bh
        if tip <= 0:
            for k in range(min(drops, 2) + 1):
                ellipse(img, self.BOXX - 6 + k * 6, by0, 4.5, 1.6, BLACK)
            rect(img, bx0, by0, bx0 + bw, self.FLOOR, (.75, .55, .3))
            rect(img, bx0, by0, bx0 + bw, by0 + 2, (.6, .42, .2))
            draw.text(img, "HOLES", self.BOXX, by0 + 7, (.25, .12, .05), center=True)
        else:
            a = -tip * math.pi / 2                  # it tips over to the left
            c, sn = math.cos(a), math.sin(a)

            def at(dx, dy):
                return bx0 + dx * c - dy * sn, self.FLOOR + dx * sn + dy * c

            poly(img, [at(0, 0), at(bw, 0), at(bw, -bh), at(0, -bh)], (.75, .55, .3))
            poly(img, [at(2, -bh + 2), at(bw - 2, -bh + 2), at(bw - 2, -bh), at(2, -bh)], (.15, .1, .05))
        if t > self.SPILL + 0.2:
            for hx, d in self.HOLES:
                u = _ease((t - self.SPILL - 0.2 - d) / 0.7)
                if u > 0:
                    ellipse(img, 104 + (hx - 104) * u, self.FLOOR, 6.5, 2.2, BLACK)
        if t > self.SPILL + 0.9:                    # someone to tidy up
            u = t - self.SPILL - 0.9
            fall = u > 1.2
            x = -12 + 48 * min(u, 1.2)
            H = 44
            y = self.FLOOR - LEG * H
            if fall:
                v = u - 1.2
                x = 46 - 2 + 2 * _ease(v / 0.1)
                y += 260 * max(0.0, v - 0.05) ** 2
            if y < self.FLOOR + 60:
                hx, hy, r = toon(img, x, y, H, SKINS[2], (.2, .4, .8), t, walk=0 if fall else 1,
                                 look=(1, 0) if not fall else (0, -1), arms=(2.6, 2.6) if fall else (0.3, 0.3),
                                 mood=-1 if fall else 0, seed=7)
                ellipse(img, hx, hy - r * 0.6, r * 1.1, r * 0.8, (1, .8, .1), half="top")
            rect(img, 0, self.FLOOR, N, N, self.FLOORC)
            for hx, d in self.HOLES:
                ellipse(img, hx, self.FLOOR, 6.5, 2.2, BLACK, half="bottom")
        say = cue(t, [(0, "HOW IT'S MADE: HOLES"), (3.6, "THE REST IS SCRAP."), (self.SPILL, ""),
                      (self.SPILL + 2.8, "MIND THE HOLES.")])[1]
        if say:
            caption(img, say, rgb=(1, .9, .4))


class Volcano(Show):
    """Science: the baking soda volcano, with a little more soda."""
    num, title, length = 551, "SCIENCE TIME!", 11.5
    T, VX, G, H, SX = 92, 94, 120, 56, 46
    LIFT = 5.8

    def __init__(self):
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.3, .5, .45), (.22, .38, .35), 0, 112)
        rect(bg, 6, 4, 122, 48, (.45, .3, .15))
        rect(bg, 8, 6, 120, 46, (.1, .25, .15))
        chalk = (.8, .85, .8)
        draw.text(bg, "SODA + ? = !", 40, 12, chalk, center=True)
        line(bg, 74, 40, 88, 22, chalk, w=1)
        line(bg, 88, 22, 102, 40, chalk, w=1)
        for k in range(3):
            line(bg, 88, 22, 82 + k * 6, 10, chalk, w=1)
        line(bg, 14, 30, 60, 30, chalk, w=1)
        line(bg, 14, 38, 48, 38, chalk, w=1)
        rect(bg, 0, 112, N, N, (.3, .25, .25))
        self.bg = bg

    def _table(self, img, scorch):
        rect(img, 60, self.T, 126, self.T + 5, (.55, .35, .2))
        rect(img, 62, self.T + 5, 124, self.T + 10, (.45, .28, .15))
        for x in (64, 118):
            rect(img, x, self.T + 10, x + 4, self.G, (.45, .28, .15))
        if scorch:
            ellipse(img, self.VX, self.T + 0.5, 16, 2, (.12, .1, .08))

    def _cone(self, img, x, y):
        poly(img, [(x - 20, y), (x + 20, y), (x + 6, y - 30), (x - 6, y - 30)], (.55, .33, .15))
        poly(img, [(x - 20, y), (x - 8, y), (x - 2, y - 30), (x - 6, y - 30)], (.45, .26, .1))
        ellipse(img, x, y - 30, 6, 2, (.25, .1, .05))

    def draw(self, img, t):
        img[:] = self.bg
        base = self.G - LEG * self.H
        lift = t >= self.LIFT
        arms, mood, look = (0.3, 0.4), 1, (1, 0)
        if 2.0 <= t < 3.6:
            arms = (0.3, 1.75)
        elif 3.6 <= t < 5.2:
            arms = (0.3, 2.1)
        elif 5.2 <= t < self.LIFT:
            arms, mood, look = (0.6, 0.6), -1, (1, 0)
        elif self.LIFT <= t < 9.0:
            arms, mood, look = (0.2, 0.2), 0, (0.6, -1)
        elif t >= 9.0:
            arms, mood, look = (0.3, 2.9), 1, (1, 0.3)
        skin = SKINS[0] if not lift else (.4, .38, .38)
        hx, hy, r = toon(img, self.SX, base, self.H, skin, (.95, .95, .97), t, arms=arms, mood=mood, look=look,
                         talk=chatter(t) if t < 2.0 else 0, pants=(.25, .25, .3), seed=11)
        n = 7 if lift else 4
        for k in range(n):
            a = -math.pi / 2 + (k - (n - 1) / 2) * (0.35 if lift else 0.4)
            ln = r * (1.0 if lift else 0.55)
            line(img, hx + r * 0.9 * math.cos(a), hy + r * 1.0 * math.sin(a), hx + (r + ln) * math.cos(a),
                 hy + (r + ln) * math.sin(a), (.85, .85, .85), w=1.5)
        for s in (-1, 1):
            draw.ring(img, hx + s * r * 0.36, hy - r * 0.18, r * 0.32, (.3, .7, 1), width=1.0)
        hpx, hpy = hand(self.SX, base, self.H, arms[1], 1)
        if 2.0 <= t < 3.6:                          # a little
            line(img, hpx, hpy, hpx + 6, hpy - 6, (.9, .9, 1), w=3)
            line(img, hpx + 7, hpy - 6, self.VX - 1, self.T - 30, (.9, .9, 1), w=1, a=0.8)
        elif 3.6 <= t < 5.2:                        # a little more
            c, s = math.cos(-0.6), math.sin(-0.6)
            jx, jy = hpx + 10, hpy - 14

            def at(dx, dy):
                return jx + dx * c - dy * s, jy + dx * s + dy * c
            line(img, *at(12, -6), self.VX, self.T - 30, (.9, .9, 1), w=4, a=0.8)
            poly(img, [at(-12, -12), at(12, -12), at(12, 12), at(-12, 12)], (.2, .4, .9))
            draw.text(img, "SODA", jx, jy - 4, WHITE, center=True)
        if not lift:
            self._table(img, False)
            sh = 1.5 * math.sin(t * 60) if t > 5.0 else 0
            self._cone(img, self.VX + sh, self.T)
            foam = _clip((t - 2.4) / 1.0) + 2 * _clip((t - 4.0) / 1.2)
            if foam > 0:
                for k in range(5):
                    s = -1 if k % 2 else 1
                    d = min(26.0, foam * 9 * (0.6 + 0.4 * (k % 3)))
                    ellipse(img, self.VX + sh + s * (2 + d * 0.45), self.T - 30 + d, 2.5, 3.5, (1, .45, .6))
                ellipse(img, self.VX + sh, self.T - 31, 6 + foam, 2.5 + foam, (1, .55, .7))
                for k in range(3):
                    b = (t * 1.5 + k / 3) % 1.0
                    ellipse(img, self.VX + sh + (k - 1) * 3, self.T - 33 - b * 6 * foam, 1.5, 1.5, (1, .7, .8))
        else:
            self._table(img, True)
            u = t - self.LIFT
            vy = self.T - 150 * u * u
            if vy > -30:
                for k in range(3):
                    f = 1 + 0.3 * math.sin(t * 40 + k)
                    ellipse(img, self.VX + (k - 1) * 9, vy + 6 * f, 4, 9 * f, (1, .5, .1))
                    ellipse(img, self.VX + (k - 1) * 9, vy + 3 * f, 2, 5 * f, (1, .95, .5))
                self._cone(img, self.VX, vy)
        if 4.8 < t < 8.5:
            for k in range(6):
                u = (t * 0.7 + k / 6) % 1.0
                a = _clip((t - 4.8) / 0.5) * _clip((8.5 - t) / 1.0)
                ellipse(img, self.VX - 24 + k * 9, self.T - 4 - 30 * u, 3 + 7 * u, 3 + 5 * u, (.8, .8, .8), a=a * (1 - u))
        if t >= 8.3:                                # what came down
            u = t - 8.3
            my = -12 + (self.T - 9 + 12) * min(1.0, (u / 0.45) ** 2)
            if u > 0.45:
                my -= 5 * abs(math.sin((u - 0.45) * 9)) * math.exp(-(u - 0.45) * 6)
            ellipse(img, self.VX, my, 9, 9, (.85, .85, .8))
            ellipse(img, self.VX - 3, my - 3, 2, 2, (.65, .65, .6))
            ellipse(img, self.VX + 4, my + 3, 1.5, 1.5, (.65, .65, .6))
            if u > 1.0:
                for s in (-1, 1):
                    line(img, self.VX + s * 3.5 - 1.5, my - 1, self.VX + s * 3.5 + 1.5, my - 1, BLACK, w=1)
                line(img, self.VX - 2, my + 3, self.VX + 2, my + 3, BLACK, w=1)
        say = cue(t, [(0, "TODAY: VOLCANOES!"), (2.0, "ADD A LITTLE SODA..."), (3.6, "...AND A LITTLE MORE."),
                      (self.LIFT, ""), (7.0, "RESULTS:"), (8.8, "RESULTS: A MOON.")])[1]
        if say:
            caption(img, say)


class Clouds(Show):
    """A public service announcement about feeding the clouds."""
    num, title, length = 558, "PUBLIC SERVICE", 11.5
    G, H, MX = 112, 48, 50
    PATHS = [(1.0, (-20, 16), (52, 40)), (3.4, (150, 20), (88, 30)), (4.2, (-30, 6), (24, 26))]
    MERGE = 7.0

    def __init__(self):
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.35, .65, 1), (.75, .9, 1), 0, 96)
        vgrad(bg, (.4, .75, .3), (.25, .55, .2), 96, N)
        wood = (.55, .35, .18)
        for k in range(3):
            rect(bg, 82, 76 + k * 5, 122, 79 + k * 5, wood)
        rect(bg, 80, 92, 124, 96, wood)
        for x in (84, 118):
            rect(bg, x, 96, x + 3, 106, (.25, .25, .25))
        self.bg = bg
        rng = np.random.default_rng(self.num)
        rain = np.zeros((N, N), np.float32)
        for _ in range(45):
            x, y = rng.integers(0, N), rng.integers(0, N - 6)
            rain[y:y + 5, x] = 1
        self.rain = np.concatenate([rain, rain])[..., None]

    @staticmethod
    def _cloud(img, x, y, s, shade, t, chomp=0.0, seed=0.0):
        col = (1 - .55 * shade, 1 - .55 * shade, 1 - .45 * shade)
        for dx, dy, rx, ry in ((0, 0, 12, 8), (-10, 3, 8, 6), (10, 3, 8, 6), (0, 5, 15, 5)):
            ellipse(img, x + dx * s, y + dy * s, rx * s, ry * s, col)
        _eyes(img, x, y, 1.6 * s, t, look=(0, 1), seed=seed)
        if chomp > 0.05:
            ellipse(img, x, y + 5 * s, 2.2 * s, 1.8 * s * chomp, (.2, .05, .1))
        else:
            line(img, x - 2.5 * s, y + 4.5 * s, x + 2.5 * s, y + 4.5 * s, (.2, .05, .1), w=max(1.0, 0.4 * s))

    def draw(self, img, t):
        img[:] = self.bg
        shade = _clip((t - 4.8) / 2.5)
        clouds = []
        m = _ease((t - self.MERGE) / 1.0)
        for k, (t0, a, b) in enumerate(self.PATHS):
            if t < t0:
                continue
            u = _ease((t - t0) / 1.4)
            s = 1 + 0.6 * _clip((t - t0 - 1.4) / 3.0)
            x, y = a[0] + (b[0] - a[0]) * u + 3 * math.sin(t * 1.5 + k), a[1] + (b[1] - a[1]) * u
            clouds.append((x + (60 - x) * m, y + (30 - y) * m, s + (3.0 - s) * m, k))
        if m >= 1:                                  # one big cloud now
            clouds = [(60, 30, 3.0, 0)]
        if shade > 0.25 and clouds:
            x0 = int(max(0, min(x - 10 * s for x, y, s, k in clouds)))
            x1 = int(min(N, max(x + 10 * s for x, y, s, k in clouds)))
            y0 = int(max(0, min(y + 6 * s for x, y, s, k in clouds)))
            off = N - int(t * 140) % N
            mask = self.rain[off + y0:off + self.G, x0:x1]
            sl = img[y0:self.G, x0:x1]
            sl += (np.asarray((.6, .7, .95), np.float32) - sl) * mask * (0.8 * _clip((shade - 0.25) * 3))
            pw = _clip((t - 6.0) / 3.0)
            if pw > 0:
                ellipse(img, self.MX, self.G + 1, 10 + 14 * pw, 2 + 2 * pw, (.4, .55, .9))
        base = self.G - LEG * self.H
        toss = t < 6.0
        arm = 0.3 + 2.4 * max(0.0, math.sin(t * 3)) if toss else 0.25
        hx, hy, r = toon(img, self.MX, base, self.H, SKINS[0], (.6, .4, .7), t, arms=(0.4, arm),
                         look=(0.5, -1) if t < 6.5 else (0, 0), mood=1 if t < 5.0 else -1, pants=(.35, .3, .25), seed=12)
        ellipse(img, hx, hy - r * 0.95, r * 0.9, r * 0.35, (.85, .85, .85))
        bx, by = hand(self.MX, base, self.H, 0.4, -1)
        rect(img, bx - 4, by - 2, bx + 3, by + 7, (.7, .5, .3))
        if toss:
            for k in range(4):
                u = (t * 0.9 + k / 4) % 1.0
                ellipse(img, hx + 6 + 10 * u, hy - 8 - 60 * u + 40 * u * u, 1.2, 1.2, (.95, .8, .5))
        for x, y, s, k in clouds:
            chomp = max(0.0, math.sin(t * 10 + k)) if t < self.MERGE + 1 else (max(0.0, math.sin(t * 3)) if t > 9.5 else 0)
            self._cloud(img, x, y, s, shade, t, chomp, seed=k)
        say = cue(t, [(0, "A NICE DAY IN THE PARK."), (2.6, ""), (8.6, "PLEASE. DON'T FEED THE CLOUDS.")])[1]
        if say:
            caption(img, say, rgb=(1, 1, .7), bg=(.05, .1, .4), a=0.85)


# ---------------------------------------------------------------- lessons: fitness, art, cooking

def _frame(x, y, rot=0.0, sy=1.0, px=0.0):
    """Local coordinates for an object standing at (x, y): stretched tall by sy, tipped by rot about (x + px, y)."""
    c, s = math.cos(rot), math.sin(rot)

    def at(dx, dy):
        dx, dy = dx - px, dy * sy
        return x + px + dx * c - dy * s, y + dx * s + dy * c
    return at


def _quad(img, at, x0, y0, x1, y1, rgb):
    poly(img, [at(x0, y0), at(x1, y0), at(x1, y1), at(x0, y1)], rgb)


class Yoga(Show):
    """Yoga, for objects."""
    num, title, length = 564, "OBJECT YOGA", 12.0
    F = 100
    TOASTER, POT, CHAIR = 20, 62, 102

    def __init__(self):
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.75, .6, .88), (.6, .45, .75), 0, self.F)
        for k in range(5):
            ellipse(bg, 20 + k * 22, 26, 6, 6, (1, .85, .6), a=0.25)
        vgrad(bg, (.7, .48, .28), (.55, .35, .2), self.F, N)
        for y in (108, 118):
            rect(bg, 0, y, N, y + 1, (.45, .3, .15))
        for x, c in ((self.TOASTER, (.2, .7, .65)), (self.POT, (.95, .45, .3)), (self.CHAIR, (.35, .5, .9))):
            rect(bg, x - 17, self.F - 1, x + 17, self.F + 3, c)
        self.bg = bg

    @staticmethod
    def _face(img, at, x, y, t, strain, seed, look=(0, 0)):
        ex, ey = at(x, y)
        _eyes(img, ex, ey, 2.2, t, look=look, seed=seed, shock=strain)

    def _toaster(self, img, t, sy, rot, pop):
        at = _frame(self.TOASTER, self.F, rot, sy, px=13)
        for k, x0 in enumerate((-8, 3)):
            if rot < 0.3:
                y0 = self.F - 26 * sy - pop
                rect(img, self.TOASTER + x0, y0, self.TOASTER + x0 + 6, y0 + 9, (.85, .6, .3))
                rect(img, self.TOASTER + x0, y0, self.TOASTER + x0 + 6, y0 + 1.5, (.6, .35, .15))
            else:                                   # out it slid
                x = self.TOASTER - 4 - k * 7 - 6 * _clip(rot - 0.3)
                rect(img, x - 4.5, self.F - 3, x + 4.5, self.F, (.85, .6, .3))
        _quad(img, at, -13, 0, 13, -20, (.75, .78, .82))
        _quad(img, at, -13, -20, 13, -17, (.9, .92, .95))
        _quad(img, at, -9, -20, -2, -18.5, (.2, .2, .2))
        _quad(img, at, 2, -20, 9, -18.5, (.2, .2, .2))
        _quad(img, at, 13, -12, 16, -9, BLACK)
        self._face(img, at, 0, -10, t, sy > 1.3, 1)

    def _teapot(self, img, t, sy, rot):
        at = _frame(self.POT, self.F, rot, sy, px=10)
        col = (.3, .55, .95)
        line(img, *at(10, -10), *at(20, -21), col, w=3.5)
        line(img, *at(-12, -17), *at(-19, -13), col, w=2.5)
        line(img, *at(-19, -13), *at(-12, -5), col, w=2.5)
        _quad(img, at, -8, 0, 8, -3, col)
        ellipse(img, *at(0, -11), 13, 11 * sy, col, rot=rot)
        ellipse(img, *at(0, -21.5), 6, 2.5 * sy, (.5, .7, 1), rot=rot)
        ellipse(img, *at(0, -24.5), 2, 2, (.5, .7, 1))
        self._face(img, at, 0, -11, t, sy > 1.3, 2)
        return at(20.5, -21.5)

    def _chair(self, img, t, sy, rot, o):
        at = _frame(self.CHAIR, self.F, rot, sy, px=0)
        col, w = (.9, .25, .2), 2.5
        line(img, *at(-9 * o, 0), *at(9 * o, -16), col, w=w)
        line(img, *at(9 * o, 0), *at(-9 * o, -16), col, w=w)
        line(img, *at(-10 * o, -16), *at(-10 * o + 20 * o, -16 - 18 * (1 - o)), col, w=w)
        line(img, *at(-10 * o, -16), *at(-11 * o, -38), col, w=w)
        line(img, *at(-11 * o, -38), *at(-11 * o, -28), col, w=w + 2)
        ex, ey = at(-11 * o, -33)
        if o > 0.3:
            ellipse(img, ex + 5, ey, 2, 2.2, WHITE)
            ellipse(img, ex + 5.6, ey, 1, 1.1, BLACK)

    def draw(self, img, t):
        img[:] = self.bg
        reach = 1 + 0.9 * _bump(t, 0.4, 3.0, 0.7)
        u = (t - 3.4) / 1.4
        pop = 70 * math.sin(math.pi * u) if 0 <= u <= 1 else 0
        trot = 1.2 * _ease((t - 6.5) / 0.35) + 0.37 * _ease((t - 6.85) / 0.25)
        prot = 1.35 * _ease((t - 6.3) / 0.9)
        fold = _ease((t - 7.3) / 0.3)
        crot = math.pi / 2 * _clip((t - 7.7) / 0.35) ** 2
        self._toaster(img, t, reach, trot, pop)
        tip = self._teapot(img, t, reach, prot)
        if prot > 1.0:                              # all the way down
            pr = _clip((t - 7.0) / 3.0)
            ellipse(img, tip[0] + 6, self.F + 1, 4 + 14 * pr, 1.5 + 1.5 * pr, (.7, .4, .12))
            line(img, *tip, tip[0] + 6, self.F, (.75, .45, .15), w=2)
        elif 3.5 < t < 5.6:
            for k in range(3):
                b = (t * 1.2 + k / 3) % 1.0
                ellipse(img, tip[0] + 2 + 8 * b, tip[1] - 3 - 20 * b, 2 + 4 * b, 2 + 3 * b, WHITE, a=0.6 * (1 - b))
        self._chair(img, t, reach, crot, 1 - fold)
        say = cue(t, [(0, "AND... REACH UP."), (3.2, "AND EXHALE."), (6.0, "TOUCH YOUR TOES."), (9.0, "LOVELY. NAMASTE.")])[1]
        caption(img, say, 0 if t > 2.6 else None, rgb=(1, 1, .85), bg=(.35, .15, .4), a=0.7)


class Paint(Show):
    """An art lesson, where the painting has notes."""
    num, title, length = 571, "PAINT ALONG", 12.0
    G, H, PX = 112, 58, 32
    SX, SY = 94, 44
    YELLOW = (1, .8, .1)

    def __init__(self):
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.3, .55, .62), (.22, .45, .52), 0, 104)
        rect(bg, 0, 104, N, N, (.5, .36, .25))
        wood = (.5, .3, .15)
        line(bg, 72, 112, 84, 14, wood, w=2.5)
        line(bg, 116, 112, 104, 14, wood, w=2.5)
        line(bg, 94, 112, 94, 70, wood, w=2)
        rect(bg, 62, 72, 126, 76, wood)
        rect(bg, 63, 15, 125, 73, (.85, .82, .75))
        rect(bg, 65, 17, 123, 71, (.98, .96, .9))
        self.bg = bg

    def _sun(self, img, t):
        r = 13 * _ease((t - 0.3) / 1.6)
        if r <= 0.5:
            return
        rays = _clip((t - 1.8) / 0.6)
        for k in range(10):
            a = k * math.pi / 5 + 0.2
            line(img, self.SX + (r + 2) * math.cos(a), self.SY + (r + 2) * math.sin(a),
                 self.SX + (r + 2 + 6 * rays) * math.cos(a), self.SY + (r + 2 + 6 * rays) * math.sin(a), self.YELLOW, w=2)
        ellipse(img, self.SX, self.SY, r, r, self.YELLOW)
        if t < 2.4:
            return
        cross = 4.0 < t < 10.4
        for s in (-1, 1):
            ellipse(img, self.SX + s * 4.5, self.SY - 3, 1.6, 2, BLACK)
            if cross or (t >= 10.4 and s > 0):
                line(img, self.SX + s * 7.5, self.SY - 8 + (0 if cross else 1), self.SX + s * 2, self.SY - 6, BLACK, w=1.3)
        bend = -2.5 if cross else 2.5
        line(img, self.SX - 5, self.SY + 5 - bend * 0.4, self.SX, self.SY + 5 + bend, BLACK, w=1.3)
        line(img, self.SX, self.SY + 5 + bend, self.SX + 5, self.SY + 5 - bend * 0.4 - (1.5 if t >= 10.4 else 0), BLACK, w=1.3)

    def draw(self, img, t):
        img[:] = self.bg
        self._sun(img, t)
        cl = _ease((t - 5.0) / 1.2)
        if cl > 0:                                  # the clouds she won't have
            u = _clip((t - 7.0) / 0.9)
            cx = 86 + 50 * u
            cy = 40 + 70 * max(0.0, u - 0.5) ** 2 * 4
            for dx, dy, rx, ry in ((0, 0, 11, 7), (-9, 3, 7, 5), (9, 3, 7, 5)):
                ellipse(img, cx + dx, cy + dy, rx * cl, ry * cl, (.55, .55, .6))
            img[:, 126:] = self.bg[:, 126:] if u < 0.5 else img[:, 126:]
        base = self.G - LEG * self.H
        painting = t < 3.0 or 5.0 <= t < 6.8
        arm = 1.55 + 0.25 * math.sin(t * 14) if painting else 0.3
        look = (1, -0.2) if painting else (0, 0)
        mood = 1 if not painting else 0
        hx, hy, r = toon(img, self.PX, base, self.H, SKINS[1], (.9, .45, .2), t, arms=(0.3, arm), look=look, mood=mood,
                         talk=chatter(t) if 3.2 < t < 4.6 or 10.4 < t < 11.6 else 0, pants=(.25, .2, .4), seed=13)
        ellipse(img, hx + 1, hy - r * 0.95, r * 1.15, r * 0.45, (.7, .1, .25))
        ellipse(img, hx + 1, hy - r * 1.4, 1.5, 1.5, (.7, .1, .25))
        bx, by = hand(self.PX, base, self.H, arm, 1)
        line(img, bx, by, bx + 9, by - 5, (.6, .4, .2), w=1.5)
        ellipse(img, bx + 10, by - 5.5, 1.8, 1.8, self.YELLOW if t < 3 else (.55, .55, .6))
        lx, ly = hand(self.PX, base, self.H, 0.3, -1)
        ellipse(img, lx - 3, ly + 2, 7, 4, (.95, .9, .8))
        for k, c in enumerate(((1, .2, .2), (.2, .5, 1), (1, .8, .1))):
            ellipse(img, lx - 7 + k * 3.5, ly + 1, 1.3, 1.3, c)
        reach = _bump(t, 8.0, 9.8, 0.4)
        if reach > 0:                               # notes
            ax, ay = self.SX - 13, self.SY + 2
            tx, ty = hx + r * 1.5 + 6 * math.sin(t * 16) * (t > 8.4), hy + r * 0.4
            ex, ey = ax + (tx - ax) * reach, ay + (ty - ay) * reach
            line(img, ax, ay, ex, ey, self.YELLOW, w=3)
            line(img, ex, ey, ex - 6, ey + 1, (.6, .4, .2), w=1.5)
            ellipse(img, ex - 7, ey + 1, 1.6, 1.6, BLACK)
        st = _clip((t - 8.5) / 0.8)
        if st > 0:
            for s in (-1, 1):
                ellipse(img, hx + s * r * 0.35 * st, hy + r * 0.32, r * 0.42 * st, r * 0.17, BLACK, rot=-s * 0.35)
                if st >= 1:
                    ellipse(img, hx + s * r * 0.82, hy + r * 0.18, r * 0.12, r * 0.12, BLACK)
        say = cue(t, [(0, "LET'S PAINT A SUN."), (3.0, "PERFECT."), (5.0, "NOW, SOME CLOUDS..."), (6.8, ""),
                      (10.2, "SEE YOU NEXT WEEK!")])[1]
        if say:
            caption(img, say, rgb=(1, .95, .8))


class Flip(Show):
    """Cooking: flip with confidence."""
    num, title, length = 577, "FLIP IT!", 10.5
    G, H, CX, TOP = 116, 56, 50, 100
    FLIPS = (0.8, 4.4)
    THROW, LAND = 5.8, 7.4
    CAKE = (.92, .68, .3)

    def __init__(self):
        chk = (((X // 10) + (Y // 10)) % 2)[..., None]
        self.bg = np.where(chk > 0, np.array((.85, .93, .95), np.float32), np.array((.65, .85, .9), np.float32))
        self.bg[self.TOP:] = (.3, .3, .35)
        self.bg[self.TOP:self.TOP + 4] = (.55, .55, .6)
        ellipse(self.bg, 84, self.TOP + 1, 14, 2, (.15, .15, .18))
        self.front = self.bg[self.TOP:].copy()

    def draw(self, img, t):
        img[:] = self.bg
        flat = 1.0
        if t > self.LAND:
            flat = 0.62 + 0.15 * math.exp(-(t - self.LAND) * 6) * math.cos((t - self.LAND) * 30)
        base = self.G - LEG * self.H * flat
        arm, other, look, mood = 1.4, 0.3, (1, 0.6), 1
        for f in self.FLIPS:
            if f - 0.15 < t < f + 0.15:
                arm = 2.1
        if 1.2 < t < 3.2 or 4.7 < t < 5.6 or 6.1 < t < self.LAND:
            look, mood = (0.5, -1), 0
        if 3.2 <= t < 3.9:
            arm, other, look, mood = 1.2, 1.2, (0, 0), -1
        if self.THROW - 0.2 < t:
            arm = 2.8 if t < self.THROW + 0.3 else (1.3 if t < self.LAND else 1.6)
            other = 0.3 if t < self.THROW + 0.3 else (1.3 if t < self.LAND else 1.6)
        if t > self.LAND:
            look, mood = (0, 0), -1
        hx, hy, r = toon(img, self.CX, base, self.H, SKINS[2], WHITE, t, arms=(other, arm), look=look, mood=mood, flat=flat,
                         seed=14)
        hat = (.97, .97, .97)
        rect(img, hx - r * 0.75, hy - r * 1.9 * flat, hx + r * 0.75, hy - r * 0.8 * flat, hat)
        ellipse(img, hx, hy - r * 2.1 * flat, r * 1.15, r * 0.75 * flat, hat)
        px, py = hand(self.CX, base, self.H, arm, 1)
        if t < self.THROW:
            pcx, pcy = px + 15, py - 2
            line(img, px, py, pcx - 8, pcy, (.2, .2, .2), w=2)
            ellipse(img, pcx, pcy, 10, 2.5, (.2, .2, .22))
            for k, f in enumerate(self.FLIPS):
                u = t - f
                if u < 0 and (k == 0 or t > 3.9):
                    s = 1.0 if k == 0 else _clip((t - 3.9) / 0.3)
                    ellipse(img, pcx, pcy - 2, 7 * s, 2 * s, self.CAKE)
                elif 0 <= u < 0.6:
                    ellipse(img, pcx + 4 * u, pcy - 2 - 260 * u, 7, 2 + 4 * abs(math.sin(u * 20)), self.CAKE)
        elif t < self.THROW + 0.6:
            u = t - self.THROW
            pcx, pcy = px + 10, py - 4 - 260 * u
            line(img, pcx - 9 * math.cos(u * 20), pcy - 9 * math.sin(u * 20), pcx, pcy, (.2, .2, .2), w=2)
            ellipse(img, pcx, pcy, 10, 2.5 + 2 * abs(math.sin(u * 20)), (.2, .2, .22))
        if t > self.LAND - 0.6:                     # what goes up
            top = hy - r * 2.7 * flat
            u = _clip((t - self.LAND + 0.6) / 0.6)
            y0 = -50 + (top + 50) * u * u
            for k in range(12):
                cy = y0 - k * 3.2
                ellipse(img, hx + 1.5 * math.sin(k * 1.7), cy, 12, 2.6, self.CAKE)
                ellipse(img, hx + 1.5 * math.sin(k * 1.7), cy - 0.5, 11, 1.2, (.98, .78, .4))
            ty = y0 - 12 * 3.2
            rect(img, hx - 3, ty - 3, hx + 3, ty + 1, (1, .95, .55))
            ellipse(img, hx, ty - 6, 10, 2.5, (.2, .2, .22))
            line(img, hx + 9, ty - 6, hx + 22, ty - 9, (.2, .2, .2), w=2)
            if t > self.LAND:
                d = _clip((t - self.LAND) / 2.0)
                for s in (-1, 1):
                    ellipse(img, hx + s * 11, y0 - 16 + 14 * d, 1.6, 3 + 6 * d, (.55, .25, .05))
                _dizzy(img, hx, top + 4, t, r=14)
        img[self.TOP + 4:] = self.front[4:]
        if t < 3.2:
            caption(img, "FLIP WITH CONFIDENCE.")
        elif t > self.LAND + 0.8:
            caption(img, "SERVES TWELVE.")


# ---------------------------------------------------------------- space and very small things

class Planet(Show):
    """Space: an unremarkable planet."""
    num, title, length = 584, "DEEP SPACE", 11.0
    PX, PY, PR = 80, 72, 42
    EYES = ((66, 60), (94, 60))
    MX, MY = 80, 90
    SNEEZE = 6.4

    def __init__(self):
        rng = np.random.default_rng(self.num)
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.02, 0, .08), (.08, .02, .16))
        for _ in range(70):
            b = rng.uniform(0.3, 1)
            bg[rng.integers(0, N), rng.integers(0, N)] = (b, b, b * 0.9)
        d = np.hypot(X + 0.5 - self.PX, Y + 0.5 - self.PY)
        cov = np.clip(self.PR - d + 0.5, 0, 1)[..., None]
        light = np.clip(0.6 - 0.45 * ((X - self.PX) + (Y - self.PY)) / self.PR / 1.4, 0.25, 1)[..., None]
        planet = np.asarray((.75, .5, .8), np.float32) * light
        bg = bg * (1 - cov) + planet * cov
        crater = (.45, .28, .5)
        for x, y, r in ((52, 80, 5), (100, 82, 4), (88, 46, 3.5), (62, 98, 3), (106, 64, 2.5)):
            ellipse(bg, x, y, r, r * 0.85, crater)
        for x, y in self.EYES:
            ellipse(bg, x, y, 7.5, 6.5, crater)
            ellipse(bg, x + 1, y + 1, 6, 5, (.38, .22, .42))
        line(bg, self.MX - 12, self.MY, self.MX + 12, self.MY + 1, crater, w=2.5)
        self.bg = bg

    @staticmethod
    def _probe(img, x, y, a):
        c, s = math.cos(a), math.sin(a)

        def at(dx, dy):
            return x + dx * c - dy * s, y + dx * s + dy * c

        _quad(img, at, -15, -3, -5, 3, (.2, .4, .9))
        _quad(img, at, 5, -3, 15, 3, (.2, .4, .9))
        _quad(img, at, -4, -4, 4, 4, (.95, .75, .2))
        line(img, *at(0, -4), *at(0, -9), (.8, .8, .8), w=1)
        ellipse(img, *at(0, -10), 2.5, 1.5, (.9, .9, .9), rot=a)

    def draw(self, img, t):
        img[:] = self.bg
        if t < self.SNEEZE:
            u = _ease(t / 4.0)
            x, y, a = -20 + 50 * u, 30 + 12 * u + 2 * math.sin(t * 2), 0.15 * math.sin(t)
        else:
            u = t - self.SNEEZE
            x, y, a = 30 - 140 * u, 42 - 70 * u, u * 18
        open_ = _ease((t - 4.0) / 0.4) * (1 - _ease((t - 9.0) / 0.5))
        squint = _ease((t - 5.0) / 1.2) * (1 - _ease((t - self.SNEEZE - 0.6) / 0.3))
        sneeze = self.SNEEZE <= t < self.SNEEZE + 0.6
        for ex, ey in self.EYES:
            if sneeze:
                line(img, ex - 5, ey - 3, ex + 4, ey, BLACK, w=1.6)
                line(img, ex + 4, ey, ex - 5, ey + 3, BLACK, w=1.6)
            elif open_ > 0.05:
                h = 5.5 * open_ * (1 - 0.6 * squint)
                ellipse(img, ex + 1, ey + 1, 6, h, WHITE)
                lx, ly = (x - ex), (y - ey)
                n = math.hypot(lx, ly) or 1
                ellipse(img, ex + 1 + 2.5 * lx / n, ey + 1 + min(h * 0.5, 2.5) * ly / n, 2.4, min(2.6, h), BLACK)
        if sneeze:
            ellipse(img, self.MX, self.MY, 13, 8, (.15, .02, .1))
            u = (t - self.SNEEZE) / 0.6
            k = np.arange(40)
            ang = math.pi + 0.55 * np.sin(k * 2.39) - 0.6
            dist = 30 + 140 * u * (0.5 + 0.5 * np.sin(k * 7.1) ** 2)
            draw.plot(img, self.MX - 10 + dist * np.cos(ang), self.MY - 8 + dist * np.sin(ang) * 0.7,
                      (.7, 1, .85), op="max")
        elif squint > 0.05:
            ellipse(img, self.MX, self.MY, 4 + 6 * squint, 1 + 4 * squint, (.15, .02, .1))
        if x > -30 and y > -30:
            self._probe(img, x, y, a)
        if self.SNEEZE + 0.4 < t < self.SNEEZE + 1.8:   # gone
            u = t - self.SNEEZE - 0.4
            if (u * 6) % 1 < 0.5:
                star(img, 4, 6, 3, WHITE, n=4, inner=0.3)
        say = cue(t, [(0, "PLANET KX-9."), (2.6, "UNREMARKABLE."), (5.0, "AH..."), (5.7, "AH... AH..."),
                      (self.SNEEZE, "CHOO!"), (self.SNEEZE + 0.8, ""), (8.8, "UNREMARKABLE.")])[1]
        if say:
            caption(img, say, rgb=(.9, .9, 1), bg=(0, 0, 0), a=0.5)


class Rocket(Show):
    """Space: a launch, sideways."""
    num, title, length = 590, "LAUNCH DAY", 11.5
    G, PAD, TX, TH = 100, 78, 24, 40
    TIP, GO = 4.0, 4.9
    PASSES = (7.2, 8.7, 10.0)

    def __init__(self):
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.3, .55, .95), (.85, .88, .95), 0, self.G)
        for k, (x, r) in enumerate(((10, 30), (60, 22), (110, 34))):
            ellipse(bg, x, self.G, r, 16 + k * 3, (.55, .58, .72), half="top")
        rect(bg, 0, self.G, N, N, (.8, .68, .42))
        rect(bg, self.PAD - 14, self.G - 2, self.PAD + 22, self.G + 3, (.45, .45, .5))
        for x in (56, 62):
            rect(bg, x, 44, x + 2, self.G - 2, (.6, .2, .15))
        for y in range(46, self.G - 2, 8):
            line(bg, 57, y, 63, y + 8, (.6, .2, .15), w=1)
        self.bg = bg

    def _rocket(self, img, x, y, rot, flame):
        """Its base's right-hand corner at (x, y), tipped clockwise by rot."""
        at = _frame(x - 6, y, rot, 1.0, px=6)
        if flame:
            f = 1 + 0.25 * math.sin(flame * 50)
            poly(img, [at(-5, 0), at(5, 0), at(0, 14 * f)], (1, .55, .1))
            poly(img, [at(-3, 0), at(3, 0), at(0, 8 * f)], (1, .95, .5))
        for s in (-1, 1):
            poly(img, [at(s * 6, -2), at(s * 11, 2), at(s * 6, -12)], (.9, .15, .15))
        _quad(img, at, -6, 0, 6, -34, (.95, .95, .95))
        poly(img, [at(-6, -34), at(6, -34), at(0, -46)], (.9, .15, .15))
        ex, ey = at(0, -24)
        ellipse(img, ex, ey, 3, 3, (.2, .4, .7))

    def draw(self, img, t):
        img[:] = self.bg
        rot, gx, flame = 0.0, self.PAD + 6, 0.0
        if self.TIP - 0.4 < t:
            flame = t
        if t >= self.TIP:
            rot = math.pi / 2 * min(1.0, ((t - self.TIP) / 0.7) ** 2)
        if t >= self.GO:
            gx = self.PAD + 6 + 300 * (t - self.GO) ** 2
        tx, ty, trot, tlook, tarms, dizzy = self.TX, self.G - LEG * self.TH, 0.0, (1, 0), (0.3, 0.4), False
        for k, p in enumerate(self.PASSES):        # around it comes
            u = t - p
            if -0.1 < u < 0.7:
                nose = -12 + 320 * u
                ry = self.G - 2 if k < 2 else self.G - 36
                self._rocket(img, nose - 46, ry, math.pi / 2, t)
            if k < 2 and 0.0 < u < 0.45:
                ty -= 30 * math.sin(math.pi * u / 0.45)
                tarms = (2.6, 2.6)
            if k == 2 and u > 0.08:
                v = u - 0.08
                trot = -math.pi / 2 * _ease(v / 0.3) - (2 * math.pi * _clip(v / 0.3) if v < 0.3 else 0)
                ty = self.G - 4 if v > 0.3 else ty - 10 * math.sin(math.pi * v / 0.3)
                dizzy = v > 0.3
        if gx < 200:
            self._rocket(img, gx, self.G - 2, rot, flame)
        if self.TIP - 0.4 < t < self.PASSES[0]:
            for k in range(8):
                u = (t * 0.6 + k / 8) % 1.0
                a = _clip((t - self.TIP + 0.4) / 0.4) * _clip((self.PASSES[0] - t) / 1.5)
                ellipse(img, self.PAD - 4 + 12 * math.sin(k * 2.3) - 30 * u * (t > self.GO), self.G - 4 - 16 * u * (k % 2),
                        4 + 8 * u, 3 + 5 * u, (.9, .9, .9), a=a * (1 - u * 0.7))
        if self.GO < t < self.GO + 2.0:
            a = 1 - (t - self.GO) / 2.0
            rect(img, self.PAD + 8, self.G - 9, min(N, self.PAD + 6 + 300 * (t - self.GO) ** 2 - 46), self.G - 5,
                 (.95, .95, .95), a=0.6 * a)
        if t > 1.0 and t < self.PASSES[0]:
            tlook = (1, 0) if t < self.GO + 0.3 else (1, -0.3)
        elif t >= self.PASSES[0]:
            tlook = (-1, 0) if (t - self.PASSES[0]) % 1.5 < 0.4 else (1, 0)
        hx, hy, r = toon(img, tx, ty, self.TH, SKINS[3], (.95, .6, .1), t, arms=tarms, rot=trot, look=tlook,
                         mood=-1 if dizzy else 0, pants=(.3, .3, .35), seed=15)
        if dizzy:
            _dizzy(img, hx, hy - 6, t)
        if 0.8 <= t < 3.8:
            n = 3 - int(t - 0.8)
            words(img, str(n), 6, (1, .95, .3), scale=4, x=32)
        say = cue(t, [(0, ""), (5.6, "A FLAWLESS LAUNCH."), (self.PASSES[0] + 0.4, "ORBIT ACHIEVED.")])[1]
        if say:
            caption(img, say)


class Cells(Show):
    """Under the microscope: the humble cell."""
    num, title, length = 597, "UNDER THE SCOPE", 11.5
    TX, TY, TR = 72, 66, 15
    Z0, Z1 = 2.6, 4.4
    LOOKUP, BLINDS = 7.6, 8.6
    DESKS = [(30, 62), (90, 62), (30, 100), (90, 100)]
    PAL = [(.85, .9, .6), (.4, .65, .3), (.72, .88, .5), (.45, .6, .3)]

    def __init__(self):
        rng = np.random.default_rng(self.num)
        d = np.hypot(X + 0.5 - 64, Y + 0.5 - 64)
        self.mask = np.clip(58 - d + 0.5, 0, 1)[..., None] * np.clip(1.15 - d / 70, 0, 1)[..., None]
        self.cells = [(self.TX, self.TY, self.TR)]
        while len(self.cells) < 11:
            x, y, r = rng.uniform(10, 118), rng.uniform(10, 118), rng.uniform(8, 13)
            if all(math.hypot(x - a, y - b) > r + c + 2 for a, b, c in self.cells):
                self.cells.append((x, y, r))
        self.office = np.empty((N, N, 3), np.float32)
        vgrad(self.office, (.75, .9, .55), (.6, .8, .45))
        ellipse(self.office, 20, 10, 40, 30, (.55, .72, .4))

    def draw(self, img, t):
        if t < self.Z1:
            z = 1 + 9 * _ease((t - self.Z0) / (self.Z1 - self.Z0)) ** 2
            img[:] = self.PAL[0]
            for k, (x, y, r) in enumerate(self.cells):
                x += 1.5 * math.sin(t * 0.8 + k)
                y += 1.5 * math.cos(t * 0.7 + k * 2)
                cx, cy, rr = 64 + (x - self.TX) * z, 64 + (y - self.TY) * z, r * z
                if cx + rr < 0 or cx - rr > N or cy + rr < 0 or cy - rr > N:
                    continue
                ellipse(img, cx, cy, rr, rr * 0.9, self.PAL[1])
                ellipse(img, cx, cy, rr - 1.5 * z, rr * 0.9 - 1.5 * z, self.PAL[2])
                if k:
                    ellipse(img, cx + rr * 0.25, cy - rr * 0.2, rr * 0.33, rr * 0.3, self.PAL[3])
                elif z > 2.5:                       # someone's in
                    for j, (dx, dy) in enumerate(self.DESKS):
                        px, py = 64 + (dx - 64) * z / 10, 64 + (dy - 64) * z / 10
                        rect(img, px - z * 1.3, py - z * 0.4, px + z * 1.3, py, (.5, .3, .15))
        else:
            img[:] = self.office
            up = t > self.LOOKUP
            for j, (dx, dy) in enumerate(self.DESKS):
                stand = j == 0 and t > self.LOOKUP + 0.6
                by = dy - 12 - (8 if stand else 0) + (0.8 * math.sin(t * 12 + j) if not up else 0)
                ellipse(img, dx - 6, by + 8, 9, 8, [(.3, .4, .7), (.7, .3, .3), (.3, .6, .5), (.6, .5, .2)][j])
                face_x, face_y = dx - 6, by - 4
                face(img, face_x, face_y, 7, SKINS[j % len(SKINS)], t, look=(0, -1) if up else (1, 0.5),
                     mood=0 if up else 1, seed=j)
                rect(img, dx + 2, dy - 18, dx + 20, dy - 6, (.2, .2, .25))
                rect(img, dx + 4, dy - 16, dx + 18, dy - 8, (.3, .9, .5) if not up else (.2, .5, .3))
                rect(img, dx - 22, dy - 6, dx + 22, dy - 2, (.55, .35, .18))
                rect(img, dx - 20, dy - 2, dx - 17, dy + 10, (.45, .28, .12))
                rect(img, dx + 17, dy - 2, dx + 20, dy + 10, (.45, .28, .12))
            if t > self.LOOKUP + 0.6:               # privacy, please
                ax, ay = 24, 46
                cord_y = 10 + 30 * _ease((t - self.BLINDS) / 0.8) if t > self.BLINDS else 10
                line(img, ax + 6, ay, 40, cord_y + 4, SKINS[0], w=2.5)
                drop = _ease((t - self.BLINDS) / 0.8) * N
                for y in range(0, int(drop), 7):
                    rect(img, 0, y, N, y + 6, (.92, .88, .75))
                    rect(img, 0, y + 6, N, y + 7, (.6, .55, .45))
                line(img, 40, 0, 40, cord_y + 4 if drop < 5 else min(drop, 60), (.4, .35, .3), w=1)
                if t > self.BLINDS + 1.0:
                    rect(img, 44, 54, 84, 68, (.9, .15, .1))
                    draw.text(img, "CLOSED", 64, 56, WHITE, center=True)
        img *= self.mask
        say = cue(t, [(0, "THE HUMBLE CELL."), (self.Z0, "ENHANCE."), (self.Z1 + 0.3, "CELL DIVISION."), (self.LOOKUP, "")])[1]
        if say:
            caption(img, say, rgb=(1, 1, .8), a=0.0)


CHANNELS = [Socko, Ducks, Shapes, Lamp, Geese, Commute, Lapse, Holes, Volcano, Clouds, Yoga, Paint, Flip, Planet, Rocket,
            Cells]
