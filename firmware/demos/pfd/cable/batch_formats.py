"""TV formats gone wrong: talk shows, quizzes, sport, dating, courts, lotteries and live TV from other dimensions."""
import math

import numpy as np

from .. import draw
from ..draw import N, X, Y
from .kit import (BLACK, LEG, SKINS, WHITE, caption, chatter, cue, ellipse, face, hand, line, person, poly, rect,
                  star, ticker, toon, vgrad, words)
from .shows import Show

_CONF = np.random.default_rng(200).uniform(size=(48, 4))
_CONF_COLS = [(1, .3, .3), (1, .85, .2), (.3, .8, 1), (.5, 1, .4), (1, .5, .9)]


def _confetti(img, u, n=48, speed=1.0):
    """Confetti falling, u seconds after it was thrown."""
    for k in range(n):
        a, b, c, d = _CONF[k]
        y = -8 - c * 90 + u * (45 + 45 * b) * speed
        if -4 < y < N:
            x = a * N + 4 * math.sin(u * 4 + d * 6)
            w = 1 + 2 * abs(math.sin(u * 6 + d * 9))
            rect(img, x, y, x + w, y + 3, _CONF_COLS[k % 5])


def _dizzy(img, x, y, t, r=9.0, s=2.5):
    for k in range(3):
        a = t * 6 + k * 2.1
        star(img, x + r * math.cos(a), y + 3 * math.sin(a), s, (1, .9, .2), n=5, inner=0.45)


def _heart(img, x, y, r, rgb=(1, .2, .4)):
    ellipse(img, x - r * 0.5, y - r * 0.25, r * 0.56, r * 0.56, rgb)
    ellipse(img, x + r * 0.5, y - r * 0.25, r * 0.56, r * 0.56, rgb)
    poly(img, [(x - r * 1.03, y - r * 0.1), (x + r * 1.03, y - r * 0.1), (x, y + r * 0.95)], rgb)


def _rrect(img, cx, cy, w, h, rot, rgb):
    """A w x h rectangle centred on (cx, cy), turned rot radians."""
    c, s = math.cos(rot), math.sin(rot)
    poly(img, [(cx + dx * c - dy * s, cy + dx * s + dy * c)
               for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))], rgb)


HAIR = [(.25, .15, .08), (.1, .08, .06), (.6, .35, .15), (.85, .7, .35), (.45, .45, .5), (.5, .2, .1)]


def _backs(img, y, xs, t=0.0, arms=0.0, seed=0):
    """An audience seen from behind: the backs of heads at row y, arms up by `arms` (0..1, pumping)."""
    for k, x in enumerate(xs):
        shirt = [(.3, .3, .6), (.6, .2, .2), (.2, .5, .3), (.5, .4, .2)][(k + seed) % 4]
        bob = 2 * arms * abs(math.sin(t * 7 + k * 1.3))
        if arms > 0:
            for s in (-1, 1):
                ex, ey = x + s * 9, y - 10 - 8 * arms - bob
                line(img, x + s * 6, y + 8, ex, ey, shirt, w=3)
                ellipse(img, ex, ey, 2, 2, SKINS[(k + seed) % 3])
        ellipse(img, x, y + 14, 11, 9, shirt)
        ellipse(img, x, y - bob * 0.3, 7, 8, HAIR[(k * 7 + seed) % 6])


def _live(img, label, y=104, bg=(.95, .95, .95), fg=BLACK):
    """A news lower third: a red LIVE box and a white strap."""
    rect(img, 0, y, N, y + 12, bg)
    rect(img, 0, y, 26, y + 12, (.85, .05, .05))
    draw.text(img, "LIVE", 13, y + 1, WHITE, center=True)
    draw.text(img, label, 30, y + 1, fg)


# ---------------------------------------------------------------- the talk show

class Chair(Show):
    """Silent: the guest is a chair; the host laughs at everything it doesn't say, and shrinks."""
    num, title, length = 201, "LATE NITE", 11.0
    # (from, host height, where his feet are, his x): behind the desk, then on it, then on the mug
    BEATS = [(0.0, (64, 112, 30)), (2.0, (46, 112, 30)), (4.0, (32, 112, 30)), (6.0, (20, 82, 30)), (8.0, (8, 74, 47)),
             (9.4, (0, 0, 0))]

    def __init__(self):
        rng = np.random.default_rng(201)
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.03, .02, .18), (.22, .1, .45), 0, 92)
        ellipse(bg, 112, 16, 7, 7, (1, .97, .8))
        x = 0
        while x < N:
            w, h = int(rng.integers(9, 18)), int(rng.integers(18, 52))
            rect(bg, x, 92 - h, x + w - 1, 92, (.07, .05, .18))
            for wy in range(92 - h + 3, 89, 5):
                for wx in range(x + 2, x + w - 3, 4):
                    if rng.random() < 0.35:
                        rect(bg, wx, wy, wx + 2, wy + 2, (1, .8, .35))
            x += w
        rect(bg, 0, 92, N, N, (.42, .23, .14))
        for k in range(0, N + 40, 14):
            line(bg, k, 92, k - 30, N, (.34, .18, .1), w=1)
        self.bg = bg

    def _chair(self, img, x, y):
        red, dark = (.8, .15, .25), (.55, .08, .16)
        for s in (-1, 1):
            rect(img, x + s * 11 - 2, y - 14, x + s * 11 + 2, y, (.3, .15, .08))
        ellipse(img, x, y - 40, 14, 10, red)
        rect(img, x - 14, y - 40, x + 14, y - 18, red)
        rect(img, x - 17, y - 20, x + 17, y - 11, dark)
        for s in (-1, 1):
            rect(img, x + s * 17 - 3, y - 28, x + s * 17 + 3, y - 11, red)
            ellipse(img, x + s * 17, y - 28, 4, 3, red)

    def _desk(self, img):
        rect(img, 0, 84, 62, 114, (.5, .28, .12))
        rect(img, 0, 81, 64, 85, (.72, .45, .22))
        rect(img, 4, 94, 58, 98, (.95, .75, .2))
        rect(img, 43, 73, 51, 81, (.92, .92, .96))
        draw.ring(img, 52, 77, 2.5, (.92, .92, .96), width=1.2)

    def draw(self, img, t):
        img[:] = self.bg
        i, (h, feet, hx), lt = cue(t, self.BEATS)
        final = h == 0
        laugh = lt > 1.15 and not final
        if final:
            self._chair(img, 30, 112)
        elif feet > 100:
            self._host(img, t, h, feet, hx, laugh, lt)
        self._desk(img)
        if not final and feet <= 100:
            self._host(img, t, h, feet, hx, laugh, lt)
        if final:
            wave = (2.4 + 0.5 * math.sin(t * 12), 0.3)
            toon(img, 96, 112 - LEG * 11, 11, SKINS[0], (.2, .25, .35), t, arms=wave, mood=1, seed=1)
        else:
            self._chair(img, 96, 112)
        lit = laugh or (final and int(t * 3) % 2 == 0)
        rect(img, 4, 4, 62, 18, (.2, .03, .03))
        rect(img, 5, 5, 61, 17, (.7, .1, .1) if lit else (.28, .05, .05))
        draw.text(img, "APPLAUSE", 33, 6, (1, 1, .85) if lit else (.5, .2, .2), center=True)

    def _host(self, img, t, h, feet, hx, laugh, lt):
        if laugh:
            rock = math.sin(t * 26)
            pose = dict(rot=-0.18 + 0.1 * rock, arms=(0.9 + 0.5 * rock, 0.9 - 0.5 * rock), talk=1.0, mood=1, look=(0, -1))
        else:
            pose = dict(arms=(0.3, 0.9 + 0.4 * math.sin(t * 5)), talk=chatter(t) if lt < 0.9 else 0.0, look=(1, 0))
        toon(img, hx, feet - LEG * h, h, SKINS[0], (.2, .25, .35), t, seed=1, **pose)


# ---------------------------------------------------------------- the quiz

class Quiz(Show):
    """Silent: a man and a toaster on a quiz show; the toaster knows everything."""
    num, title, length = 207, "BRAIN BUZZ", 10.0
    MAN, TST, NPOP = 30, 96, 24
    CRUST, BREAD = (.62, .36, .12), (.96, .8, .45)

    def __init__(self):
        rng = np.random.default_rng(207)
        bg = np.empty((N, N, 3), np.float32)
        ang = np.arctan2(Y + 0.5 - 150, X + 0.5 - 64)
        m = (np.floor(ang * 20 / (2 * math.pi)) % 2)[..., None]
        bg[:] = np.array((.12, .1, .42), np.float32) * (1 - m) + np.array((.2, .14, .55), np.float32) * m
        rect(bg, 0, 104, N, N, (.08, .04, .18))
        for k in range(10):
            ellipse(bg, 6 + k * 13, 102, 2, 2, (1, .85, .3))
        self.bg = bg
        k = np.arange(self.NPOP)
        self.pops = 1.2 + 6.9 * np.sqrt(k / (self.NPOP - 1))
        self.land = [(8 + (j % 4) * 12.5 + rng.uniform(-2, 2), 110 - (j // 4) * 9 + rng.uniform(-2, 1))
                     for j in range(self.NPOP - 1)] + [(30, 36)]

    def _toast(self, img, x, y, rot=None):
        if rot is None:
            rect(img, x - 6, y - 5, x + 6, y + 5, self.CRUST)
            rect(img, x - 4, y - 3, x + 4, y + 4, self.BREAD)
        else:
            _rrect(img, x, y, 12, 10, rot, self.CRUST)
            _rrect(img, x, y, 8.5, 7, rot, self.BREAD)

    def _podium(self, img, x, score, lit):
        rect(img, x - 22, 74, x + 22, 112, (.35, .45, 1) if lit else (.2, .28, .85))
        rect(img, x - 22, 74, x + 22, 77, (1, .8, .2))
        rect(img, x - 18, 80, x + 18, 92, (0, 0, .08))
        draw.text(img, score, x, 81, (1, .9, .2), center=True)

    def draw(self, img, t):
        img[:] = self.bg
        n = int(np.searchsorted(self.pops, t, side="right"))
        won = t > 8.7
        lit = n and t - self.pops[n - 1] < 0.3
        rect(img, self.TST - 2, 64, self.TST + 2, 74, (.3, .3, .35))
        self._podium(img, self.TST, f"${n * 100}", lit)
        x = self.TST
        rect(img, x - 15, 54, x + 15, 74, (.75, .78, .84))
        ellipse(img, x, 54, 15, 4, (.85, .88, .92))
        for s in (-1, 1):
            rect(img, x + s * 6 - 3, 52, x + s * 6 + 3, 55, (.15, .12, .1))
        rect(img, x + 15, 60 + (4 if lit else 0), x + 19, 63 + (4 if lit else 0), BLACK)
        ellipse(img, x - 8, 60, 3, 1.5, WHITE, a=0.5)
        if lit:
            for k in range(5):
                a = -math.pi / 2 + (k - 2) * 0.45
                line(img, x + 21 * math.cos(a), 50 + 21 * math.sin(a), x + 27 * math.cos(a), 50 + 27 * math.sin(a),
                     (1, 1, .6), w=1.5)
        if won:
            y = 30 + 20 * min(1.0, (t - 8.7) / 0.3) ** 2
            poly(img, [(x - 10, y), (x - 10, y - 9), (x - 5, y - 4), (x, y - 11), (x + 5, y - 4), (x + 10, y - 9),
                       (x + 10, y)], (1, .8, .1))
        mood = -1 if t > 4 else 0
        person(img, self.MAN, 54, 12, SKINS[2], (.85, .45, .1), t, look=(1, 0) if t < 7 else (0, -1), mood=mood, seed=3)
        self._podium(img, self.MAN, "$0", False)
        press = abs(math.sin(t * 22)) if t > 1.6 else 0.0
        ellipse(img, self.MAN + 12, 73, 5, 3, (.9, .1, .1), half="top")
        ellipse(img, self.MAN + 12, 67 + 4 * press, 3, 3, SKINS[2])
        for j in range(n):
            u = (t - self.pops[j]) / 0.7
            sx = self.TST + (6 if j % 2 else -6)
            lx, ly = self.land[j]
            if u < 1:
                self._toast(img, sx + (lx - sx) * u, 50 + (ly - 50) * u - 46 * math.sin(math.pi * u), rot=u * 9)
            else:
                self._toast(img, lx, ly)
        if won:
            _confetti(img, t - 8.7, speed=1.5)
        q = n + 1 if n < 8 else 9 + (n - 8) ** 2 * 3
        s = cue(t, [(0, "WHAT IS 2 + 2?"), (2.8, "NAME A FRUIT."), (4.2, None), (8.7, "THE WINNER!")])[1]
        caption(img, s or f"QUESTION {q}", None, (1, 1, .6), BLACK, a=0.8)


# ---------------------------------------------------------------- sport

class Grape(Show):
    """Silent: the grape drop final, the slow-motion replay, the second angle and the scores."""
    num, title, length = 213, "GRAPE DROP", 11.0
    G, H, AX = 112, 60, 40

    def __init__(self):
        rng = np.random.default_rng(213)
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.08, .06, .14), (.18, .14, .25), 0, 58)
        for row in range(6):
            for k in range(23):
                x, y = 2 + k * 5.6 + (row % 2) * 2.8 + rng.uniform(-1, 1), 4 + row * 9
                rect(bg, x - 2.5, y + 2, x + 2.5, y + 7, [(.6, .1, .1), (.1, .3, .7), (.8, .7, .1), (.3, .3, .3)][rng.integers(4)])
                ellipse(bg, x, y, 2.2, 2.4, SKINS[rng.integers(3)])
        rect(bg, 0, 58, N, 68, (.05, .35, .2))
        draw.text(bg, "* WORLD GRAPE DROP *", 64, 59, (1, .95, .7), center=True)
        vgrad(bg, (.2, .45, .85), (.1, .25, .6), 68, N)
        rect(bg, 0, 100, N, 101, (.8, .85, 1))
        self.bg = bg
        self.base = self.G - LEG * self.H
        self.hx, self.hy = hand(self.AX, self.base, self.H, math.pi / 2, 1)
        close = np.empty((N, N, 3), np.float32)
        vgrad(close, (.05, .05, .1), (.15, .12, .25), 0, 96)
        vgrad(close, (.25, .5, .95), (.1, .2, .55), 96, N)
        for k in range(-6, 8):
            line(close, 64 + k * 8, 96, 64 + k * 40, N, (.35, .6, 1), w=1)
        self.close = close

    def _gy(self, u):
        top, floor = self.hy + 4, self.G - 3
        if u < 1.0:
            return top
        f = top + 0.5 * 1150 * (u - 1.0) ** 2
        if f < floor:
            return f
        land = 1.0 + math.sqrt(2 * (floor - top) / 1150)
        return floor - 5 * abs(math.sin((u - land) * 14)) * math.exp(-(u - land) * 7)

    def _scene(self, img, u):
        img[:] = self.bg
        cheer = u > 1.45
        arms = (2.8, 2.8) if cheer else (0.3, math.pi / 2)
        jump = 6 * abs(math.sin(u * 9)) if cheer else 0
        toon(img, self.AX, self.base - jump, self.H, SKINS[1], (.9, .2, .2), u, arms=arms, mood=1 if cheer else 0,
             look=(1, 1) if not cheer else (0, 0), pants=(.9, .9, .95), seed=5)
        gy = self._gy(u)
        ellipse(img, self.hx, gy, 3, 3.2, (.45, .1, .55))
        ellipse(img, self.hx - 1, gy - 1, 1, 1, (.8, .6, .9))
        return gy

    def draw(self, img, t):
        i, _, lt = cue(t, [(0, 0), (2.4, 1), (6.4, 2), (8.6, 3)])
        if i == 0:
            self._scene(img, t)
            _live(img, "GRAPE DROP FINAL", 116)
        elif i == 1:
            u = 0.9 + lt * 0.11
            gy = self._scene(img, u)
            img *= np.array((.75, .85, 1.1), np.float32)
            if lt > 0.8:
                draw.ring(img, self.hx, gy, 8, (1, 1, .1), width=1.2)
            p = min(1.0, max(0.0, (lt - 1.6) / 1.4))
            if p > 0:
                y1 = gy + 10 + (self.G - 4 - gy - 10) * p
                line(img, self.hx + 14, gy + 2, self.hx + 14, max(gy + 2, y1), (1, 1, .1), w=2)
                if p >= 1:
                    poly(img, [(self.hx + 9, y1 - 6), (self.hx + 19, y1 - 6), (self.hx + 14, y1)], (1, 1, .1))
            if lt > 3.0:
                line(img, self.hx - 6, self.G - 2, self.hx + 6, self.G + 6, (1, 1, .1), w=2)
                line(img, self.hx - 6, self.G + 6, self.hx + 6, self.G - 2, (1, 1, .1), w=2)
            rect(img, 0, 4, min(60, lt * 200), 17, (.1, .3, .9))
            draw.text(img, "REPLAY", 30, 6, WHITE, center=True)
            draw.text(img, "SLO-MO", 104, 116, (1, 1, .3), center=True)
        elif i == 2:
            img[:] = self.close
            v = min(1.0, lt / 1.5)
            fy = 98 - 26
            if lt < 1.5:
                gy, sq = -30 + (fy + 30) * v * v, 1.0
            else:
                gy, sq = fy, 1 - 0.28 * math.cos((lt - 1.5) * 16) * math.exp(-(lt - 1.5) * 3)
                for k in (-1, 1):
                    d = (lt - 1.5) * 40
                    ellipse(img, 64 + k * (30 + d), 96, 8 + d * 0.3, 4, (.75, .75, .85), a=max(0.0, 0.7 - (lt - 1.5)))
            ry = 26 * sq
            ellipse(img, 64, 98 - ry, 26 / sq ** 0.5, ry, (.42, .08, .5))
            ellipse(img, 54, 98 - ry * 1.4, 6, 4, (.75, .5, .85))
            line(img, 64, 98 - 2 * ry, 66, 98 - 2 * ry - 8, (.35, .25, .1), w=2.5)
            ellipse(img, 72, 98 - 2 * ry - 8, 6, 3, (.3, .7, .2), rot=-0.4)
            rect(img, 0, 4, 60, 17, (.1, .3, .9))
            draw.text(img, "ANGLE 2", 30, 6, WHITE, center=True)
        else:
            vgrad(img, (.1, .25, .6), (.05, .1, .3))
            for k, (x, sc) in enumerate(((24, "10"), (64, "10"), (104, "11"))):
                person(img, x, 66, 11, SKINS[(k + 1) % 3], (.15, .15, .2), t, mood=1 if k < 2 else 0, seed=k,
                       look=(0, -1))
                up = min(1.0, max(0.0, (lt - 0.4 - k * 0.45) / 0.2))
                if up > 0:
                    cy = 40 - 6 * up
                    line(img, x + 12, 80, x + 8, cy + 12, SKINS[(k + 1) % 3], w=3)
                    rect(img, x - 14, cy - 12, x + 14, cy + 12, WHITE)
                    draw.text(img, sc, x, cy - 10, BLACK, center=True, scale=2)
                if k == 2 and lt > 1.5:
                    for s in (-1, 1):
                        for j in range(4):
                            v = ((t * 2 + j * 0.25) % 1)
                            ellipse(img, x + s * (5 + 10 * v), 64 + 30 * v * v - 8 * v, 1.2, 1.6, (.5, .8, 1))
            rect(img, 0, 90, N, N, (.3, .15, .1))
            rect(img, 0, 90, N, 93, (.6, .35, .15))


# ---------------------------------------------------------------- the dating show

class Booth(Show):
    """Silent: three hidden suitors; the bachelor picks number three, a vending machine."""
    num, title, length = 219, "LOVE BOOTH", 11.0
    G = 106

    def __init__(self):
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.85, .3, .55), (.45, .08, .32), 0, self.G)
        rng = np.random.default_rng(219)
        for _ in range(14):
            _heart(bg, rng.uniform(0, N), rng.uniform(0, 90), rng.uniform(3, 6), (.95, .45, .65))
        rect(bg, 0, self.G, N, N, (.3, .05, .22))
        for k, (x, y) in enumerate(((60, 44), (80, 48), (111, 26))):
            ellipse(bg, x, self.G + 3, 10, 3, (.95, .8, .3))
            line(bg, x, 0, x, y, (.9, .8, .4), w=1)
            ellipse(bg, x, y + 4, 6, 6, (.95, .8, .3))
            draw.text(bg, str(k + 1), x + 1, y - 1, (.5, .05, .25), center=True)
        self.bg = bg

    def _machine(self, img, t, glow):
        rect(img, 98, 38, 125, self.G, (.15, .35, .85))
        rect(img, 101, 44, 117, 84, (.05, .08, .15))
        for r in range(4):
            for c in range(3):
                rect(img, 103 + c * 5, 47 + r * 9, 106 + c * 5, 53 + r * 9, [(1, .2, .2), (.2, .9, .3), (1, .8, .1)][(r + c) % 3])
        for k in range(4):
            on = glow and (int(t * 8) + k) % 2
            rect(img, 119, 48 + k * 6, 123, 52 + k * 6, (1, 1, .5) if on else (.3, .3, .4))
        rect(img, 101, 90, 117, 98, (.02, .02, .05))

    def draw(self, img, t):
        img[:] = self.bg
        speak = cue(t, [(0, 0), (1.4, 1), (2.4, 2), (3.4, 3), (4.6, 0)])[1]
        glow = speak == 3 or t > 8.0
        self._machine(img, t, glow)
        if (3.9 < t < 6.0) or t > 8.6:
            rect(img, 106, 92, 112, 98, (.9, .1, .1))
        after = t > 8.2
        toon(img, 60, self.G - LEG * 44, 44, SKINS[1], (.95, .75, .15), t, look=(1, 0) if after else (-1, 0),
             talk=chatter(t) if speak == 1 else 0, arms=(1.3, 1.3) if after else (0.3, 0.3), seed=2, pants=(.2, .2, .5))
        toon(img, 80, self.G - LEG * 40, 40, SKINS[4], (.2, .7, .5), t, look=(-1, 0),
             talk=chatter(t, 2) if speak == 2 else 0, arms=(1.3, 1.3) if after else (0.3, 0.3), seed=3)
        lift = max(0.0, t - 6.0) * 130
        if lift < 90:
            rect(img, 38, 24 - lift, 46, self.G - lift, (.97, .85, .92))
            _heart(img, 42, 60 - lift, 3.5, (.9, .2, .4))
        if t < 7.0:
            bx, walk, arms, rot = 20, 0.0, (0.3, 0.3), 0.0
        elif t < 7.9:
            bx, walk, arms, rot = 20 + 70 * (t - 7.0) / 0.9, 1.0, (0.3, 0.3), 0.0
        else:
            bx, walk, arms, rot = 90, 0.0, (1.5, 1.5), 0.12
        smit = t > 4.0
        hx, hy, r = toon(img, bx, self.G - LEG * 50, 50, SKINS[0], (.95, .2, .3), t, walk=walk, arms=arms, rot=rot,
                         look=(1, 0), mood=1 if smit else 0, talk=chatter(t) if speak == 0 and t < 1.4 else 0, seed=4)
        if smit:
            for k in range(3 if t < 7.9 else 7):
                u = (t * 0.7 + k / 3) % 1
                _heart(img, hx + 8 * math.sin(u * 9 + k) + (k - 1) * 6, hy - r - 2 - 40 * u, 2.5 + 3 * u)
        if 4.6 < t < 6.4:
            ellipse(img, 26, 20, 13, 10, WHITE)
            poly(img, [(22, 28), (30, 28), (22, 36)], WHITE)
            draw.text(img, "#3!", 26, 13, (.8, .1, .3), center=True, scale=1)
        if t < 3.4:
            caption(img, "WHO WILL HE PICK?", None, (1, .9, .95), (.3, 0, .15))
        elif t > 9.4:
            caption(img, "MARRIED IN JUNE.", None, (1, .9, .95), (.3, 0, .15))


# ---------------------------------------------------------------- the chase

class Chase(Show):
    """Silent: a slow police pursuit of a runaway shopping trolley, and it goes all the way around the world."""
    num, title, length = 224, "LIVE PURSUIT", 10.0
    V, GAP = 9.0, 27.0

    def __init__(self):
        rng = np.random.default_rng(224)
        sp = np.zeros((N, N, 3), np.float32)
        for _ in range(70):
            x, y = rng.integers(0, N, 2)
            sp[y, x] = rng.uniform(.3, 1)
        self.space = sp
        g = np.zeros((N, N, 3), np.float32)
        d = np.hypot(X + 0.5 - 64, Y + 0.5 - 64)
        land = (np.sin(X * 0.11 + 1) * np.sin(Y * 0.13) + 0.6 * np.sin(X * 0.23 + Y * 0.07)) > 0.35
        g[:] = (.12, .35, .85)
        g[land] = (.25, .65, .3)
        shade = np.clip(1.1 - 0.6 * ((X - 50) ** 2 + (Y - 50) ** 2) ** 0.5 / 38, 0.35, 1)[..., None]
        self.globe_in = np.clip(38 + 0.5 - d, 0, 1)[..., None]
        self.globe = g * shade
        self.ring = np.linspace(0, 2 * math.pi, 64, endpoint=False)

    def _car(self, img, sx, sy, s, t, k):
        w, h = 13 * s, 22 * s
        rect(img, sx - w / 2, sy - h / 2, sx + w / 2, sy + h / 2, (.95, .95, .95))
        flip = (int(t * 6) + k) % 2
        if s > 0.35:
            rect(img, sx - w / 2, sy - h / 2, sx + w / 2, sy - h / 2 + 5 * s, (.1, .1, .12))
            rect(img, sx - w / 2, sy + h / 2 - 4 * s, sx + w / 2, sy + h / 2, (.1, .1, .12))
            rect(img, sx - w / 2 + s, sy - 4 * s, sx + w / 2 - s, sy - 1 * s, (.2, .3, .5))
            rect(img, sx - w / 2, sy + 1 * s, sx, sy + 4 * s, (1, .1, .1) if flip else (.3, 0, 0))
            rect(img, sx, sy + 1 * s, sx + w / 2, sy + 4 * s, (.15, .3, 1) if not flip else (0, 0, .3))
        else:
            rect(img, sx - 1, sy - 1, sx + 1, sy + 1, (1, .1, .1) if flip else (.15, .3, 1))

    def _cart(self, img, sx, sy, s):
        w, h = 12 * s, 16 * s
        rect(img, sx - w / 2, sy - h / 2, sx + w / 2, sy + h / 2, (.55, .6, .65))
        if s > 0.4:
            rect(img, sx - w / 2 + 1.5 * s, sy - h / 2 + 1.5 * s, sx + w / 2 - 1.5 * s, sy + h / 2 - 1.5 * s, (.35, .38, .42))
            for k in (-1, 0, 1):
                line(img, sx + k * 3 * s, sy - h / 2, sx + k * 3 * s, sy + h / 2, (.8, .85, .9), w=1)
            for k in (-1, 0, 1):
                line(img, sx - w / 2, sy + k * 4 * s, sx + w / 2, sy + k * 4 * s, (.8, .85, .9), w=1)
            rect(img, sx - w / 2 - s, sy + h / 2 + 2 * s, sx + w / 2 + s, sy + h / 2 + 4 * s, (.9, .2, .2))

    def _road(self, img, t, s, camy, ahead=None):
        rows = np.arange(N, dtype=np.float32)
        wy = camy + (rows + 0.5 - 64) / s
        band = (np.floor(wy / 40) % 2)[:, None]
        img[:] = (np.array((.25, .55, .2), np.float32) * (1 - band) + np.array((.22, .5, .18), np.float32) * band)[:, None, :]

        def sx(x):
            return 64 + (x - 64) * s

        rect(img, sx(30), 0, sx(98), N, (.28, .28, .3))
        dash = (wy % 20) < 10
        for lx in (52.67, 75.33):
            c = int(sx(lx))
            img[dash, c:c + max(1, int(round(1.5 * s)))] = (.95, .95, .8)
        for lx in (31, 96):
            c = int(sx(lx))
            img[:, c:c + max(1, int(round(1.5 * s)))] = (.95, .85, .2)
        t0 = math.floor((camy - 64 / s) / 60) * 60
        for wy0 in np.arange(t0, camy + 70 / s, 60):
            for tx in (12, 116):
                ellipse(img, sx(tx), 64 + (wy0 - camy) * s, 7 * s, 7 * s, (.1, .35, .12))
        cart = -self.V * t
        if ahead is not None:
            ay = cart - ahead
            self._car(img, sx(64), 64 + (ay - camy) * s, s, t, 0)
        lim = camy + 70 / s
        for lane, off in ((64, 30), (41.3, 160), (86.7, 190)):
            k = 0
            while True:
                wy0 = cart + off + k * self.GAP
                if wy0 > lim:
                    break
                sy = 64 + (wy0 - camy) * s
                if sy > -20:
                    self._car(img, sx(lane), sy, s, t, k)
                k += 1
        cy = 64 + (cart - camy) * s
        ellipse(img, sx(64), cy, 26 * s, 26 * s, (1, 1, .8), a=0.22)
        self._cart(img, sx(64), cy, s)
        return cy

    def draw(self, img, t):
        i, _, lt = cue(t, [(0, 0), (6.4, 1), (8.4, 2)])
        cart = -self.V * t
        if i == 0:
            u = min(1.0, max(0.0, (t - 2.8) / 3.4))
            u = u * u * (3 - 2 * u)
            s = math.exp(math.log(0.1) * u)
            ys = 52 - 26 * u
            camy = cart + (64 - ys) / s
            self._road(img, t, s, camy)
        elif i == 1:
            img[:] = self.space
            pts = [(64 + 50 * math.cos(a + t * 0.4), 64 + 14 * math.sin(a + t * 0.4)) for a in self.ring]
            rot = -0.35
            c, sn = math.cos(rot), math.sin(rot)
            pts = [(64 + (x - 64) * c - (y - 64) * sn, 64 + (x - 64) * sn + (y - 64) * c) for x, y in pts]
            front = [math.sin(a + t * 0.4) > 0 for a in self.ring]
            for k, ((x, y), f) in enumerate(zip(pts, front)):
                if not f:
                    rect(img, x - 1, y - 1, x + 1, y + 1, (1, .1, .1) if (int(t * 6) + k) % 2 else (.15, .3, 1))
            img[:] = img * (1 - self.globe_in) + self.globe * self.globe_in
            for k, ((x, y), f) in enumerate(zip(pts, front)):
                if f:
                    rect(img, x - 1, y - 1, x + 2, y + 2, (1, .1, .1) if (int(t * 6) + k) % 2 else (.15, .3, 1))
            x, y = pts[16]
            ellipse(img, x, y, 2, 2, WHITE)
            line(img, x, y - 3, x + 10, y - 16, WHITE, w=1)
            draw.text(img, "CART", x + 12, y - 24, WHITE)
        else:
            gap = max(0.0, 46 - lt * 30)
            self._road(img, t, 1.0, cart + 12, ahead=self.GAP - 2 + gap)
            if gap == 0:
                ellipse(img, 64, 22, 7, 6, WHITE)
                draw.text(img, "!", 64, 17, (.9, .1, .1), center=True)
        _live(img, "POLICE PURSUIT", 116)
        if t > 2.6 and i != 1:
            rect(img, 92, 4, 124, 16, (0, 0, 0), a=0.6)
            draw.text(img, "2 MPH", 108, 5, (1, 1, .3), center=True)


# ---------------------------------------------------------------- the court

class Order(Show):
    """Silent: a judge calls for order, with a bigger gavel every time."""
    num, title, length = 231, "ORDER IN COURT", 10.0
    BANGS = [(1.2, 1.0), (3.0, 1.9), (4.8, 3.2)]
    BIG = 7.0
    GALLERY = (10, 33, 56, 79, 102, 122)
    SAY = ["BLAH", "?!", "NO!", "BLAH", "OOH", "!!"]

    def __init__(self):
        bg = np.empty((N, N, 3), np.float32)
        bg[:] = (.42, .26, .13)
        for x in range(0, N, 12):
            rect(bg, x, 0, x + 2, N, (.34, .2, .1))
        draw.ring(bg, 64, 16, 11, (.95, .8, .3), width=1.5)
        draw.ring(bg, 64, 16, 7, (.95, .8, .3), width=1)
        star(bg, 64, 16, 5, (.95, .8, .3), n=5, inner=0.45, rot=-math.pi / 2)
        self.bg = bg
        self.tmp = np.empty_like(bg)

    def _gavel(self, img, px, py, a, sc):
        dx, dy = math.cos(a), math.sin(a)
        hx, hy = px + dx * 13 * sc, py + dy * 13 * sc
        line(img, px - dx * 3 * sc, py - dy * 3 * sc, hx, hy, (.55, .32, .12), w=2 * sc)
        _rrect(img, hx, hy, 6 * sc, 12 * sc, a, (.4, .2, .08))
        _rrect(img, hx, hy, 6.5 * sc, 3 * sc, a, (.95, .75, .25))

    def _big(self, img, y1):
        rect(img, 52, -10, 76, y1 - 30, (.75, .5, .25))
        rect(img, 55, -10, 59, y1 - 30, (.9, .7, .4))
        rect(img, 4, y1 - 38, 124, y1, BLACK)
        rect(img, 6, y1 - 36, 122, y1 - 2, (.22, .1, .04))
        rect(img, 6, y1 - 34, 122, y1 - 28, (.38, .2, .08))
        rect(img, 30, y1 - 36, 40, y1 - 2, (.95, .75, .25))
        rect(img, 88, y1 - 36, 98, y1 - 2, (.95, .75, .25))

    def _scene(self, img, t):
        img[:] = self.bg
        k = sum(t >= tb for tb, _ in self.BANGS)
        tb, sc = self.BANGS[k - 1] if k else (-9.0, 1.0)
        mad = min(1.0, k / 3)
        skin = tuple(np.array(SKINS[1]) * (1 - mad * 0.45) + np.array((.95, .15, .1)) * mad * 0.45)
        for s in (-1, 1):
            ellipse(img, 64 + s * 12, 36, 6, 11, (.93, .93, .9))
        person(img, 64, 32, 12, skin, (.08, .08, .1), t, mood=-1 if k else 0, talk=0.8 if 0 < t - tb < 0.6 else 0,
               seed=2)
        ellipse(img, 64, 22, 12, 6, (.93, .93, .9), half="top")
        rect(img, 16, 52, 112, 96, (.3, .16, .07))
        rect(img, 14, 49, 114, 54, (.55, .33, .15))
        rect(img, 24, 60, 104, 90, (.36, .2, .09))
        if k < 3:
            nb, nsc = self.BANGS[k]
            a = 0.5
            if nb - 0.5 < t < nb - 0.1:
                a = -1.4
            elif nb - 0.1 <= t < nb:
                a = -1.4 + 1.9 * (t - nb + 0.1) / 0.1
            self._gavel(img, 82, 44, a, nsc if a < 0.5 or not k else sc)
        elif t < self.BIG - 0.6:
            self._gavel(img, 82, 44, 0.5, sc)
        quiet = 0 <= t - tb < 0.7
        for j, x in enumerate(self.GALLERY):
            if not quiet and j < 2 + 2 * k and t < self.BIG - 0.45:
                jump = 3 * abs(math.sin(t * 9 + j)) if k == 3 else 0
                by = 84 - (j % 2) * 12 - jump + 2 * math.sin(t * 5 + j)
                ellipse(img, x, by, 13 + 3 * (k == 3), 7, WHITE)
                poly(img, [(x - 3, by + 5), (x + 3, by + 5), (x - 1, by + 12)], WHITE)
                draw.text(img, self.SAY[(j + k) % 6], x, by - 5, (.7, .1, .1), center=True)
        _backs(img, 108, self.GALLERY, t, seed=1)
        if k and t - tb < 0.7:
            words(img, "ORDER!", 4, (1, .95, .6), scale=k)

    def draw(self, img, t):
        if t < self.BIG:
            self._scene(img, t)
            for tb, sc in self.BANGS:
                if 0 <= t - tb < 0.3:
                    img[:] = np.roll(img, int(sc * 2 * math.cos((t - tb) * 60) * (1 - (t - tb) / 0.3)), 0)
            if t > self.BIG - 0.45:
                u = (t - self.BIG + 0.45) / 0.45
                self._big(img, -20 + (N - 2) * u * u)
            return
        self._scene(self.tmp, self.BIG - 0.8)
        img[:] = self.bg
        img[N - 28:] = self.tmp[np.linspace(16, N - 1, 28).astype(int)]
        u = t - self.BIG
        y1 = N - 28 + int(5 * math.cos(u * 50) * max(0.0, 1 - u / 0.4))
        self._big(img, y1)
        if u > 0.5:
            _dizzy(img, 22, y1 + 6, t, r=12)
            _dizzy(img, 104, y1 + 6, t + 1, r=12)
        if u > 1.3:
            rect(img, 34, 30, 94, 44, BLACK, a=0.6)
            draw.text(img, "...ORDER.", 64, 32, (1, .95, .8), center=True)


# ---------------------------------------------------------------- the sitcom

class Sitcom(Show):
    """Silent: a sitcom, until the camera pulls back: the studio rides on a turtle swimming through space."""
    num, title, length = 238, "HOME SWEET HOME", 12.0
    SMIN = 0.085
    FAR = (150.0, 300.0)

    def __init__(self):
        rng = np.random.default_rng(238)
        sp = np.zeros((N, N, 3), np.float32)
        sp[:] = (.01, .0, .05)
        for _ in range(90):
            x, y = rng.integers(0, N, 2)
            sp[y, x] = rng.uniform(.3, 1) * np.array((1, 1, rng.uniform(.6, 1)))
        ellipse(sp, 20, 24, 9, 9, (.8, .4, .3))
        ellipse(sp, 17, 21, 3, 2, (.9, .55, .4))
        self.space = sp

    def _cam(self, t):
        u = min(1.0, max(0.0, (t - 3.0) / 5.5))
        u = u * u * (3 - 2 * u)
        s = math.exp(math.log(self.SMIN) * u)
        f = (1 / s - 1) / (1 / self.SMIN - 1)
        return s, 64 + (self.FAR[0] - 64) * f, 64 + (self.FAR[1] - 64) * f

    def draw(self, img, t):
        s, cx, cy = self._cam(t)

        def P(x, y):
            return 64 + (x - cx) * s, 64 + (y - cy) * s

        def R(x0, y0, x1, y1, rgb, a=1.0):
            (a0, b0), (a1, b1) = P(x0, y0), P(x1, y1)
            rect(img, a0, b0, a1, b1, rgb, a)

        def E(x, y, rx, ry, rgb, **kw):
            ellipse(img, *P(x, y), rx * s, ry * s, rgb, **kw)

        img[:] = self.space
        if s < 0.5:                                 # the turtle, swimming
            green, dark, skin = (.3, .6, .35), (.2, .42, .25), (.45, .65, .35)
            pad = math.sin(t * 2)
            for fx, fy, k in ((520, 470, 1), (-360, 470, -1), (420, 500, 1), (-260, 500, -1)):
                E(fx, fy + 20 * pad * k, 130, 40, skin, rot=0.5 * k + 0.3 * pad)
            E(64, 450, 580, 70, (.75, .65, .35))
            E(64, 440, 560, 225, green, half="top")
            for hx, hy, r in ((-300, 380, 70), (-120, 300, 80), (250, 300, 80), (430, 380, 70), (64, 380, 70),
                              (-180, 410, 50), (310, 410, 50)):
                E(hx, hy, r, r * 0.6, dark)
            hx, hy = 700, 400 + 10 * math.sin(t * 1.3)
            E(hx - 70, hy + 10, 60, 40, skin)
            E(hx, hy, 95, 70, skin)
            if (t % 3.0) > 2.8:
                line(img, *P(hx + 10, hy - 20), *P(hx + 50, hy - 20), BLACK, w=max(1, 5 * s))
            else:
                E(hx + 30, hy - 20, 22, 24, WHITE)
                E(hx + 38, hy - 18, 11, 13, BLACK)
            line(img, *P(hx + 40, hy + 30), *P(hx + 88, hy + 22), (.15, .3, .15), w=max(1, 5 * s))
            R(-200, -130, 328, 215, (.78, .74, .7))
            poly(img, [P(-225, -125), P(64, -270), P(353, -125)], (.6, .2, .15))
        R(-170, -100, 298, 205, (.07, .07, .09))
        if s < 0.9:
            R(-120, -62, 248, -54, (.4, .4, .45))
            for lx in (-60, 0, 128, 188):
                E(lx, -48, 9, 7, (1, 1, .8))
            (x0, y0), (x1, y1) = P(40, -36), P(88, -16)
            lit = 2.2 < t < 6.0 and int(t * 2) % 2 == 0
            rect(img, x0, y0, x1, y1, (.9, .1, .1) if lit else (.3, .05, .05))
            if s > 0.3:
                draw.text(img, "LAUGH", (x0 + x1) / 2, (y0 + y1) / 2 - 4, WHITE if lit else (.6, .3, .3), center=True)
            for camx in (-90, 220):
                for k in (-1, 1):
                    line(img, *P(camx, 175), *P(camx + k * 22, 205), (.3, .3, .32), w=max(1, 3 * s))
                R(camx - 25, 140, camx + 25, 172, (.25, .25, .28))
                E(camx + (25 if camx < 0 else -25), 150, 10, 10, (.1, .1, .15))
        self._room(img, t, P, R, E, s)

    def _room(self, img, t, P, R, E, s):
        R(0, 0, 128, 128, (.95, .8, .55))
        if s > 0.25:
            for x in range(6, 128, 14):
                R(x, 0, x + 5, 98, (.9, .72, .48))
        R(10, 12, 42, 46, (.95, .95, .9))
        R(13, 15, 40, 43, (.5, .75, 1))
        R(25, 15, 28, 43, (.95, .95, .9))
        R(88, 14, 114, 36, (.5, .3, .15))
        R(91, 17, 111, 33, (.4, .65, .4))
        R(0, 98, 128, 128, (.55, .35, .2))
        R(116, 44, 120, 98, (.3, .2, .1))
        poly(img, [P(108, 48), P(128, 48), P(124, 34), P(112, 34)], (.95, .9, .6))
        R(22, 64, 106, 86, (.3, .55, .45))
        E(64, 66, 42, 6, (.3, .55, .45))
        joke = 2.2 < t < 4.6
        for x, y, r, skin, shirt, sd, talk in ((46, 56, 10, SKINS[0], (.85, .3, .4), 1, t < 1.2),
                                               (82, 54, 11, SKINS[2], (.3, .4, .8), 2, 1.2 < t < 2.2)):
            rock = 2 * math.sin(t * 20) if joke else 0
            if s > 0.15:
                ellipse(img, *P(x, y + r * 2.6), r * 1.7 * s, r * 1.6 * s, shirt)
                face(img, *P(x, y + rock), r * s, skin, t, talk=1.0 if joke else chatter(t, sd) if talk else 0,
                     look=(1 if x < 64 else -1, 0), mood=1 if joke else 0, seed=sd)
            else:
                E(x, y + r * 2.6, r * 1.7, r * 1.6, shirt)
                E(x, y, r, r, skin)
        R(18, 82, 110, 98, (.25, .48, .38))
        R(14, 72, 24, 98, (.22, .45, .35))
        R(104, 72, 114, 98, (.22, .45, .35))


# ---------------------------------------------------------------- the makeover

class Dream(Show):
    """Silent: the bus moves, the dream home is a teapot, and the teapot walks off."""
    num, title, length = 242, "DREAM HOME", 11.0
    GND = 88
    PINK = (.95, .45, .62)

    def __init__(self):
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.4, .7, 1), (.8, .9, 1), 0, self.GND)
        for cx, cy in ((22, 14), (100, 24)):
            for dx in (-7, 0, 7):
                ellipse(bg, cx + dx, cy - (dx == 0) * 3, 8, 5, (.97, .97, 1))
        rect(bg, 0, self.GND, N, N, (.35, .7, .3))
        rect(bg, 0, 100, N, 106, (.75, .75, .72))
        self.bg = bg

    def _teapot(self, img, x, y, t):
        p = self.PINK
        ellipse(img, x - 32, y - 2, 11, 13, p)
        ellipse(img, x - 32, y - 2, 6, 8, tuple(self.bg[int(np.clip(y, 0, self.GND - 1)), 10]))
        poly(img, [(x + 24, y + 6), (x + 46, y - 20), (x + 51, y - 18), (x + 32, y + 14)], p)
        ellipse(img, x, y, 30, 24, p)
        ellipse(img, x, y - 23, 15, 5, (.85, .35, .5))
        ellipse(img, x, y - 30, 4, 4, (1, .8, .2))
        for s in (-1, 1):
            ellipse(img, x + s * 16, y - 4, 5, 5, (.6, .85, 1))
            line(img, x + s * 16 - 5, y - 4, x + s * 16 + 5, y - 4, WHITE, w=1)
            line(img, x + s * 16, y - 9, x + s * 16, y + 1, WHITE, w=1)
        rect(img, x - 6, y + 10, x + 6, y + 24, (.5, .25, .12))
        ellipse(img, x + 3, y + 17, 1, 1, (1, .8, .2))
        for k in range(3):
            px = x + 50 + k * 3
            pts = [(px + 2 * math.sin(t * 5 + k + j), y - 22 - j * 3) for j in range(5)]
            for (a, b), (c, d) in zip(pts, pts[1:]):
                line(img, a, b, c, d, WHITE, w=1, a=0.6)

    def _bus(self, img, x):
        rect(img, x + 6, 44, x + 122, 94, (.55, .25, .78))
        rect(img, x + 6, 74, x + 122, 79, (1, .8, .2))
        for k in range(7):
            rect(img, x + 12 + k * 15, 50, x + 23 + k * 15, 64, (.6, .85, 1))
        for wx in (30, 98):
            ellipse(img, x + wx, 94, 9, 9, (.08, .08, .08))
            ellipse(img, x + wx, 94, 3.5, 3.5, (.7, .7, .7))
        draw.text(img, "TEAM DREAM", x + 64, 65, WHITE, center=True)

    def draw(self, img, t):
        if t < 2.6:
            vgrad(img, (.2, .15, .3), (.1, .08, .15))
            _rrect(img, 64, 60, 64, 72, 0.05, (.95, .95, .92))
            _rrect(img, 63.5, 54, 54, 48, 0.05, (.55, .6, .65))
            rect(img, 50, 58, 76, 78, (.45, .38, .3))
            poly(img, [(46, 60), (64, 44), (82, 62)], (.35, .3, .25))
            rect(img, 60, 66, 66, 78, (.2, .17, .15))
            line(img, 52, 64, 58, 70, (.25, .2, .18), w=1)
            draw.text(img, "BEFORE", 65, 84, BLACK, center=True)
            return
        img[:] = self.bg
        cheer = 0.0
        if t < 5.0:
            self._teapot(img, 64, 62, t)
            self._bus(img, 0.0 if t < 4.4 else -170 * ((t - 4.4) / 0.6) ** 2)
            cheer = 1.0 if t < 4.4 else 0.4
            words(img, "MOVE THE BUS!", 6, (1, .95, .3))
        else:
            lift = 0.0 if t < 7.0 else 26 * min(1.0, (t - 7.0) / 0.8)
            hx = 64 if t < 8.0 else 64 + 34 * (t - 8.0)
            hy = 62 - lift - (2 * abs(math.sin(t * 8)) if t > 8.0 else 0)
            if lift > 0:
                for k in (-1, 1):
                    fx = hx + k * 10 + (8 * math.sin(t * 8) * k if t > 8.0 else 0)
                    line(img, hx + k * 9, hy + 22, fx, self.GND + 2, (1, .6, .1), w=3)
                    for d in (-4, 0, 4):
                        line(img, fx, self.GND + 2, fx + d, self.GND + 5, (1, .6, .1), w=1.5)
            if hx < 170:
                self._teapot(img, hx, hy, t)
            if 5.0 < t < 7.0:
                for k in range(6):
                    a = k * 1.05 + t
                    star(img, 64 + 44 * math.cos(a), 60 + 30 * math.sin(a), 3 + abs(math.sin(t * 6 + k)) * 2,
                         (1, 1, .7), n=4, inner=0.3)
                cheer = 1.0
        happy = 5.0 < t < 8.2
        for x, skin, shirt, sd in ((16, SKINS[0], (.2, .6, .9), 1), (112, SKINS[2], (.95, .4, .2), 2)):
            jump = 8 * abs(math.sin(t * 9 + sd)) if 5.0 < t < 7.2 else 0
            toon(img, x, 118 - LEG * 40 - jump, 40, skin, shirt, t, arms=(2.7, 2.7) if happy else (0.3, 0.3),
                 mood=1 if happy else -1 if t > 9.0 else 0, look=(0, 0) if t < 7.0 else (1, -1), seed=sd,
                 talk=1.0 if 7.0 < t < 8.0 else 0)
        _backs(img, 120, (36, 58, 80, 100), t, arms=cheer, seed=2)


# ---------------------------------------------------------------- the awards

class Rock(Show):
    """Silent: best actor goes to a rock, whose speech runs long."""
    num, title, length = 249, "AWARDS NIGHT", 12.0
    BOXES = [(6, 4), (66, 4), (6, 54), (66, 54)]
    RX, RY = 64, 63

    def __init__(self):
        rng = np.random.default_rng(249)
        self.curtain = np.array((.6, .05, .1), np.float32) * (0.65 + 0.35 * np.sin(X * 0.5))[..., None]
        rect(self.curtain, 0, 98, N, N, (.45, .27, .12))
        rect(self.curtain, 0, 98, N, 100, (.95, .75, .25))
        void = np.zeros((N, N, 3), np.float32)
        for _ in range(60):
            x, y = rng.integers(0, N, 2)
            void[y, x] = rng.uniform(.2, .8)
        self.void = void

    def _rock(self, img, x, y, k=1.0):
        ellipse(img, x, y, 15 * k, 10 * k, (.5, .48, .45))
        ellipse(img, x - 4 * k, y - 4 * k, 6 * k, 3 * k, (.68, .66, .62))
        ellipse(img, x + 6 * k, y + 3 * k, 3 * k, 2 * k, (.4, .38, .36))
        line(img, x - 2 * k, y + 1 * k, x + 4 * k, y + 5 * k, (.35, .33, .3), w=1)

    def draw(self, img, t):
        if t < 3.6:
            vgrad(img, (.1, .05, .2), (.02, .0, .05))
            u = min(1.0, t / 2.7)
            pick = int(15.99 * (1 - (1 - u) ** 2.2)) % 4
            for k, (x, y) in enumerate(self.BOXES):
                on = k == pick and (t < 2.7 or int(t * 4) % 2 == 0)
                rect(img, x - 2, y - 2, x + 58, y + 46, (1, .95, .4) if on else (.6, .45, .15))
                rect(img, x, y, x + 56, y + 44, (.2, .15, .3) if not on else (.35, .3, .45))
                if k < 3:
                    ellipse(img, x + 28, y + 44, 17, 14, [(.1, .1, .1), (.5, .1, .3), (.1, .2, .4)][k], half="top")
                    face(img, x + 28, y + 19, 10, SKINS[k], t, seed=k, mood=1 if k == 1 else 0)
                else:
                    self._rock(img, x + 28, y + 28)
            caption(img, "BEST ACTOR", None, (1, .9, .4), BLACK, a=0.9)
            return
        lt = t - 3.6
        img[:] = self.curtain
        ellipse(img, 64, 70, 40, 34, (1, .95, .7), a=0.15)
        poly(img, [(46, 72), (82, 72), (86, 100), (42, 100)], (.4, .22, .1))
        star(img, 64, 86, 7, (1, .8, .2), n=5, inner=0.45, rot=-math.pi / 2)
        line(img, 76, 72, 74, 60, (.2, .2, .2), w=1.5)
        ellipse(img, 74, 58, 2.5, 3, (.15, .15, .15))
        _backs(img, 116, (12, 38, 64, 90, 116), t, arms=0.6 if lt < 1.6 else 0.0, seed=0)
        secs = int(lt * 11)
        rect(img, 92, 4, 124, 16, BLACK)
        draw.text(img, f"{secs // 60}:{secs % 60:02d}", 108, 5, (1, .2, .2), center=True)
        if 2.4 < lt < 5.0 and int(lt * 3) % 2 == 0:
            rect(img, 6, 4, 84, 16, (.85, .05, .05))
            draw.text(img, "WRAP IT UP", 45, 5, WHITE, center=True)
        if 3.6 < lt:
            reach = min(1.0, (lt - 3.6) / 0.5)
            tug = 3 * math.sin(lt * 30) if 4.2 < lt < 5.0 else 0
            ex = -10 + (self.RX - 14 + 10) * reach + tug
            line(img, -10, 50, ex, 50, (.9, .85, .7), w=3)
            for j in range(8):
                a0, a1 = j * math.pi / 8, (j + 1) * math.pi / 8
                line(img, ex + 7 * math.sin(a0), 57 - 7 * math.cos(a0), ex + 7 * math.sin(a1), 57 - 7 * math.cos(a1),
                     (.9, .85, .7), w=3)
        if lt > 5.0:
            dx = int(min(N, 220 * (lt - 5.0) ** 2))
            if dx:
                img[:, :N - dx] = img[:, dx:].copy()
                img[:, N - dx:] = self.void[:, N - dx:]
        self._rock(img, self.RX, self.RY)
        if lt > 6.2:
            words(img, "BEST ACTOR", 96, (1, .85, .3))
            words(img, "A ROCK", 108, WHITE)


# ---------------------------------------------------------------- the telethon

class Moon(Show):
    """Silent: a telethon to fill up the moon raises far too much."""
    num, title, length = 255, "SAVE THE MOON", 11.0
    MX, MY, MR = 34, 36, 19
    CALLS = [0.8, 1.6, 2.3, 2.9, 3.5, 4.0, 4.5, 4.9, 5.3, 5.7, 6.0, 6.3, 6.6, 6.9]
    MOON = (1, .93, .6)

    def __init__(self):
        rng = np.random.default_rng(255)
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.02, .02, .12), (.12, .05, .28), 0, 80)
        for _ in range(40):
            x, y = rng.integers(0, N), rng.integers(0, 78)
            bg[y, x] = rng.uniform(.4, 1)
        rect(bg, 0, 80, N, N, (.2, .1, .25))
        self.bg = bg
        self.chunks = rng.uniform(size=(36, 3))

    def draw(self, img, t):
        img[:] = self.bg
        v = sum(t >= c for c in self.CALLS) / len(self.CALLS) + (0.6 * (t - 6.9) ** 2 if t > 6.9 else 0)
        sky = tuple(self.bg[self.MY, 2])
        if t < 9.0:
            r = self.MR + (42 * ((t - 7.4) / 1.6) ** 2 + 1.5 * math.sin(t * 30) if t > 7.4 else 0)
            mx, my = self.MX + (r - self.MR) * 0.5, self.MY + (r - self.MR) * 0.3
            ellipse(img, mx, my, r, r, self.MOON)
            if v < 1:
                off = r * (0.3 + 1.7 * v)
                ellipse(img, mx - off, my - off * 0.15, r * 1.02, r * 1.02, sky)
            else:
                face(img, mx, my, r, self.MOON, t, mood=1, look=(0.5, 0.3) if t < 7.6 else (0, -1),
                     talk=0.6 if t > 8.3 else 0, seed=3)
                for s in (-1, 1):
                    ellipse(img, mx + s * r * 0.55, my + r * 0.25, r * 0.15, r * 0.1, (1, .5, .5), a=0.7)
        else:
            u = t - 9.0
            if u < 0.4:
                draw.ring(img, 54, 48, 20 + u * 150, (1, 1, .7), width=3)
            for cx, cy, z in self.chunks:
                a = cx * 2 * math.pi
                sp = 40 + 60 * cy
                ellipse(img, 54 + math.cos(a) * sp * u, 48 + math.sin(a) * sp * u + 70 * u * u, 2 + 3 * z, 1.5 + 2 * z,
                        self.MOON, rot=a + u * 5)
            if u > 1.2:
                ellipse(img, self.MX, self.MY, self.MR, self.MR, self.MOON, a=min(1.0, u - 1.2))
                ellipse(img, self.MX - self.MR * 0.3, self.MY, self.MR * 1.02, self.MR * 1.02, sky)
        rect(img, 66, 40, 126, 64, (.05, .02, .02))
        rect(img, 67, 41, 125, 63, (.15, .05, .02))
        draw.text(img, "TOTAL", 96, 42, (1, .55, .2), center=True)
        num = "$0" if t >= 9.0 else "GOAL!" if t > 6.9 and int(t * 3) % 2 == 0 else f"${int(v * 1000000):,}"
        draw.text(img, num, 96, 52, (1, .8, .2), center=True)
        scared = t > 9.0
        for k, x in enumerate((16, 48, 80, 112)):
            ring = any(0 <= t - c < 0.5 for c in self.CALLS[k::4])
            on = any(0.5 <= t - c < 1.6 for c in self.CALLS[k::4]) or 6.9 < t < 9.0
            person(img, x, 82, 8, SKINS[(k + 2) % 6], [(.9, .9, .9), (.3, .6, .9), (.9, .5, .7), (.6, .9, .5)][k], t,
                   talk=1.0 if scared else chatter(t, k) if on else 0, look=(0, -1) if scared else (0, 0), seed=k)
            if on:
                ellipse(img, x + 8, 82, 2.5, 5, BLACK)
            rect(img, x + 6, 93, x + 14, 97, (.1, .1, .1))
            if ring:
                for s in (-1, 1):
                    line(img, x + 10 + s * 6, 90, x + 10 + s * 8, 86, (1, 1, .5), w=1)
        rect(img, 0, 98, N, N, (.2, .3, .75))
        rect(img, 0, 98, N, 100, (.9, .9, .95))
        words(img, "SAVE THE MOON", 109, (1, .95, .5))


def _lit(bg, pts, rgb, a):
    """Light a polygon of a background: a spotlight's cone."""
    m = np.zeros((N, N), bool)
    draw.poly(np.zeros_like(bg), pts, (1, 1, 1), mask_out=m)
    bg[m] += (np.asarray(rgb, np.float32) - bg[m]) * a


# ---------------------------------------------------------------- the singing contest

def _kettle(img, x, y, r, col, d=-1):
    """A kettle with its belly at (x, y), r wide, its spout to side d. Returns the spout's tip."""
    dark = tuple(c * 0.6 for c in col)
    hc, w = (.15, .15, .18), max(1.0, r * 0.18)
    line(img, x - r * 0.6, y - r * 0.7, x - r * 0.45, y - r * 1.35, hc, w=w)
    line(img, x - r * 0.45, y - r * 1.35, x + r * 0.45, y - r * 1.35, hc, w=w)
    line(img, x + r * 0.45, y - r * 1.35, x + r * 0.6, y - r * 0.7, hc, w=w)
    tip = (x + d * r * 1.6, y - r * 1.0)
    poly(img, [(x + d * r * 0.7, y + r * 0.1), tip, (x + d * r * 1.5, y - r * 1.15), (x + d * r * 0.6, y - r * 0.5)], col)
    ellipse(img, x, y, r, r * 0.85, col)
    rect(img, x - r * 0.85, y + r * 0.55, x + r * 0.85, y + r * 0.85, dark)
    ellipse(img, x, y - r * 0.8, r * 0.5, r * 0.17, dark)
    ellipse(img, x, y - r * 0.98, r * 0.15, r * 0.15, BLACK)
    ellipse(img, x - r * 0.4, y - r * 0.3, r * 0.2, r * 0.35, WHITE, a=0.5)
    return tip


def _whistle(img, tip, t, d=-1, n=6, h=30):
    for k in range(n):
        u = (t * 2.2 + k / n) % 1
        ellipse(img, tip[0] + d * 4 * u + 3 * math.sin(t * 9 + k), tip[1] - h * u, 2 + 5 * u, 2 + 4 * u, WHITE,
                a=0.85 * (1 - u))


class Kettle(Show):
    """Silent: a blind singing contest; the judges turn, one by one, for a kettle, and the last judge is a kettle too."""
    num, title, length = 262, "SING-OFF", 10.0
    CHAIRS = (17, 49, 81, 113)
    SPINS = (2.2, 3.5, 4.7, 6.3)

    def __init__(self):
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.08, .02, .18), (.3, .06, .4), 0, 86)
        rect(bg, 0, 86, N, N, (.1, .02, .12))
        _lit(bg, [(10, 0), (24, 0), (72, 74), (44, 76)], (.95, .85, 1), 0.25)
        _lit(bg, [(104, 0), (118, 0), (86, 76), (56, 74)], (.95, .85, 1), 0.25)
        ellipse(bg, 64, 76, 42, 8, (.45, .2, .55))
        ellipse(bg, 64, 75, 30, 5, (.7, .5, .8))
        for s in (-1, 1):
            line(bg, 64 + s * 4, 64, 64 + s * 9, 75, (.2, .2, .22), w=2)
        line(bg, 34, 76, 36, 42, (.2, .2, .22), w=1.5)
        self.bg = bg

    def _chair(self, img, x, t, k):
        u = min(1.0, max(0.0, (t - self.SPINS[k]) / 0.5))
        wf = abs(math.cos(math.pi * u))
        hw = 14 * wf + 0.5
        if u < 0.5:
            rect(img, x - hw, 90, x + hw, N, (.8, .1, .12))
            ellipse(img, x, 90, hw, 6, (.8, .1, .12))
            rect(img, x - hw * 0.6, 96, x + hw * 0.6, 120, (.65, .06, .1))
            return
        rect(img, x - hw, 90, x + hw, N, (.45, .04, .08))
        ellipse(img, x, 90, hw, 6, (.45, .04, .08))
        if wf < 0.6:
            return
        if k == 3:
            tip = _kettle(img, x, 110, 10, (.2, .5, .95), d=-1)
            if t > 6.9:
                _whistle(img, tip, t, d=-1, h=40)
            return
        skin = SKINS[(k * 2 + 1) % 6]
        shirt = [(.95, .8, .2), (.3, .8, .9), (.9, .4, .7)][k]
        ellipse(img, x, 124, 10, 9, shirt)
        up = 1.0 if t < 6.9 else 0.4 + 0.3 * math.sin(t * 6 + k)
        for s in (-1, 1):
            ex, ey = x + s * 12, 112 - 16 * up
            line(img, x + s * 7, 118, ex, ey, shirt, w=3)
            ellipse(img, ex, ey, 2.5, 2.5, skin)
        face(img, x, 105, 8, skin, t, talk=1.0, look=(1, 0) if t > 6.9 else (0, -1), seed=k)

    def draw(self, img, t):
        img[:] = self.bg
        sh = 0.8 * math.sin(t * 30)
        tip = _kettle(img, 64 + sh, 52, 15, (.92, .2, .15), d=-1)
        ellipse(img, 37, 41, 2.5, 3.5, (.15, .15, .15))
        if t < 6.9:
            for k in range(4):
                u = (t * 0.7 + k / 4) % 1
                nx = tip[0] - 4 - 22 * u + 3 * math.sin(t * 3 + k * 2)
                ny = tip[1] - 34 * u
                c = (.7 + .3 * u, 1, 1)
                ellipse(img, nx, ny, 2.4, 1.9, c, rot=-0.4)
                line(img, nx + 2, ny, nx + 2, ny - 7, c, w=1)
        else:
            _whistle(img, tip, t, d=-1, h=34)
        if t > 7.6:
            for k in range(3):
                u = (t * 0.6 + k / 3) % 1
                _heart(img, 92 + 6 * math.sin(t * 3 + k * 2), 82 - 50 * u, 2 + 4 * u, (1, .3, .5))
        for k, x in enumerate(self.CHAIRS):
            self._chair(img, x, t, k)


# ---------------------------------------------------------------- the lottery

class Lotto(Show):
    """Silent: tonight's lucky numbers: 7, 23, 41, a watermelon, and the presenter."""
    num, title, length = 268, "LUCKY DRAW", 11.0
    MX, MY, MR = 84, 54, 27
    PATH = [(84, 27), (84, 8), (120, 8), (120, 113)]
    SLOTS = (16, 38, 60, 82, 104)
    DRAWS = [(0.6, "7", (1, .3, .3)), (2.0, "23", (.3, .6, 1)), (3.4, "41", (.3, .85, .4)), (4.8, None, None)]
    SPEED = 170.0
    GONE = 7.9
    HAIR = (.85, .55, .15)

    def __init__(self):
        rng = np.random.default_rng(268)
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.05, .1, .35), (.15, .3, .65))
        for _ in range(25):
            star(bg, rng.uniform(0, N), rng.uniform(0, 100), rng.uniform(1, 2.5), (.6, .7, 1), n=4, inner=0.3)
        rect(bg, 0, 100, N, N, (.08, .1, .3))
        for (x0, y0), (x1, y1) in zip(self.PATH, self.PATH[1:]):
            line(bg, x0, y0, x1, y1, (.75, .9, 1), w=19, a=0.22)
        rect(bg, 4, 103, 124, 123, (.75, .9, 1), a=0.22)
        rect(bg, 4, 123, 124, 125, (.8, .8, .85))
        rect(bg, 70, 80, 98, 96, (.95, .75, .25))
        rect(bg, 62, 96, 106, 100, (.8, .6, .2))
        self.bg = bg
        self.balls = rng.uniform(size=(16, 4))
        self.cols = [(1, .3, .3), (1, .85, .2), (.3, .6, 1), (.3, .85, .4), (.9, .4, .9), (1, .6, .2)]

    def _at(self, d, slot):
        pts = self.PATH + [(self.SLOTS[slot], 113)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            if d <= L:
                return x0 + (x1 - x0) * d / L, y0 + (y1 - y0) * d / L, False
            d -= L
        return pts[-1][0], pts[-1][1], True

    def _ball(self, img, x, y, label, col):
        ellipse(img, x, y, 9, 9, col)
        ellipse(img, x, y, 6.5, 6.5, WHITE)
        draw.text(img, label, x + 0.5, y - 4, BLACK, center=True)

    def _melon(self, img, x, y, squeeze=False):
        if squeeze:
            ellipse(img, x, y, 13, 12, (.75, .9, 1), a=0.5)
        ellipse(img, x, y, 11, 9, (.25, .6, .2))
        for k in (-6, 0, 6):
            line(img, x + k, y - 8 + abs(k) * 0.2, x + k * 1.1, y + 8 - abs(k) * 0.2, (.1, .35, .1), w=1.5)

    def _head(self, img, x, y, r, t, mood=0):
        ellipse(img, x, y - r * 0.3, r * 1.2, r * 1.1, self.HAIR)
        face(img, x, y, r, SKINS[0], t, mood=mood, look=(0, 0), seed=4)
        ellipse(img, x, y - r * 0.85, r * 1.05, r * 0.45, self.HAIR, half="top")

    def draw(self, img, t):
        img[:] = self.bg
        x, base, h = 24.0, 100 - LEG * 62, 62.0
        if t < 6.2:
            hx, hy, r = toon(img, x, base, h, SKINS[0], (.9, .15, .4), t, arms=(0.3, 1.9 + 0.25 * math.sin(t * 3)),
                             talk=chatter(t) if t < 5.4 else 0, mood=1 if t < 5.6 else -1,
                             look=(1, 0) if t < 5.6 else (1, 1), seed=4, pants=(.9, .15, .4))
            ellipse(img, hx, hy - r * 0.85, r * 1.1, r * 0.5, self.HAIR, half="top")
        elif t < 6.8:
            u = (t - 6.2) / 0.6
            hx, hy, r = toon(img, x + 20 * u, base, h, SKINS[0], (.9, .15, .4), t, rot=0.7 * u, arms=(0.3, 0.6),
                             look=(1, 0), seed=4, pants=(.9, .15, .4))
            ellipse(img, hx, hy - r * 0.85, r * 1.1, r * 0.5, self.HAIR, half="top")
        ellipse(img, self.MX, self.MY, self.MR, self.MR, (.7, .85, 1), a=0.18)
        for k, (a, b, c, d) in enumerate(self.balls):
            bx = self.MX + 19 * math.sin(t * (4 + 3 * a) + c * 6)
            by = self.MY + 17 * math.sin(t * (5 + 3 * b) + d * 6)
            ellipse(img, bx, by, 4, 4, self.cols[k % 6])
            ellipse(img, bx - 1.2, by - 1.2, 1.2, 1.2, WHITE, a=0.6)
        if 6.8 <= t < 7.3:
            u = (t - 6.8) / 0.5
            hs = 62 * (1 - u) + 14 * u
            toon(img, 44 + (self.MX - 44) * u, base + (self.MY - base) * u, hs, SKINS[0], (.9, .15, .4), t,
                 rot=0.7 + u * 9, arms=(2.8, 2.8), mood=-1, seed=4, pants=(.9, .15, .4))
        elif 7.3 <= t < self.GONE:
            self._head(img, self.MX + 15 * math.sin(t * 7), self.MY + 13 * math.sin(t * 9.3 + 1), 6, t, mood=-1)
        draw.ring(img, self.MX, self.MY, self.MR, (.85, .95, 1), width=1.2)
        ellipse(img, self.MX - 12, self.MY - 15, 6, 3, WHITE, a=0.4, rot=-0.6)
        for k, (t0, label, col) in enumerate(self.DRAWS):
            if t >= t0:
                bx, by, done = self._at((t - t0) * self.SPEED, k)
                if label:
                    self._ball(img, bx, by, label, col)
                else:
                    self._melon(img, bx, by, squeeze=not done and by < 110)
        if t >= self.GONE:
            bx, by, done = self._at((t - self.GONE) * self.SPEED, 4)
            ellipse(img, bx, by, 9, 9, (.9, .15, .4))
            self._head(img, bx, by + 1, 6.5, t, mood=1 if done and t > self.GONE + 1.8 else -1)


# ---------------------------------------------------------------- live on location

def _cow(img, x, y, t=0.0, walk=0.0):
    """A cow, side on, facing right, hooves at row y."""
    for k, lx in enumerate((-6, -3, 4, 7)):
        sw = walk * 2 * math.sin(t * 10 + k * math.pi / 2)
        line(img, x + lx, y - 7, x + lx + sw, y, (.95, .95, .95), w=2)
    line(img, x - 9, y - 10, x - 12, y - 4, (.95, .95, .95), w=1)
    ellipse(img, x, y - 10, 10, 5.5, (.97, .97, .97))
    ellipse(img, x - 3, y - 11, 3, 2.5, BLACK)
    ellipse(img, x + 4, y - 8, 2.5, 2, BLACK)
    ellipse(img, x + 11, y - 13, 4, 3.5, (.97, .97, .97))
    ellipse(img, x + 14, y - 12, 2.2, 1.8, (1, .65, .7))
    ellipse(img, x + 11, y - 14, 0.9, 0.9, BLACK)
    line(img, x + 8, y - 17, x + 9, y - 15, (.9, .85, .7), w=1)


def _ufo(img, x, y, r, t):
    ellipse(img, x, y - r * 0.25, r * 0.45, r * 0.38, (.6, .9, 1))
    ellipse(img, x, y, r, r * 0.3, (.65, .65, .75))
    ellipse(img, x, y - r * 0.05, r * 0.9, r * 0.12, (.85, .85, .9))
    for k in range(5):
        on = (int(t * 6) + k) % 2
        ellipse(img, x + (k - 2) * r * 0.38, y + r * 0.1, r * 0.07 + 0.5, r * 0.07 + 0.5, (1, .9, .2) if on else (.4, .2, .5))


def _beam(img, x, y0, y1, w0, w1, rgb=(1, 1, .6), a=0.35):
    y0, y1 = max(0, int(y0)), min(N, int(y1))
    if y1 <= y0:
        return
    rows = np.arange(y0, y1, dtype=np.float32)[:, None]
    hw = w0 + (w1 - w0) * (rows - y0) / max(1, y1 - y0)
    cov = (np.abs(X[y0:y1] + 0.5 - x) < hw) * a
    img[y0:y1] += (np.asarray(rgb, np.float32) - img[y0:y1]) * cov[..., None]


class Field(Show):
    """Silent: a live report from a quiet farm, while the sky takes the cow, the sky takes the sky, and gives the cow back."""
    num, title, length = 274, "LIVE AT FIVE", 12.0
    CX = 46

    def __init__(self):
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.45, .7, 1), (.85, .92, 1), 0, 74)
        ellipse(bg, 30, 78, 60, 14, (.45, .7, .35))
        ellipse(bg, 110, 80, 50, 12, (.42, .66, .32))
        rect(bg, 0, 74, N, N, (.38, .66, .27))
        rect(bg, 6, 54, 28, 74, (.75, .15, .12))
        poly(bg, [(4, 55), (17, 44), (30, 55)], (.5, .1, .08))
        rect(bg, 13, 62, 21, 74, WHITE)
        line(bg, 13, 62, 21, 74, (.75, .15, .12), w=1)
        line(bg, 21, 62, 13, 74, (.75, .15, .12), w=1)
        for x in range(2, N, 12):
            rect(bg, x, 78, x + 2, 88, (.55, .4, .25))
        rect(bg, 0, 80, N, 81, (.6, .45, .3))
        rect(bg, 0, 85, N, 86, (.6, .45, .3))
        self.bg = bg

    def draw(self, img, t):
        img[:] = self.bg
        G = 96
        cx, cy, cow = self.CX, float(G), True
        if t < 2.6:
            cx = -14 + (self.CX + 14) * t / 2.6
        elif 3.6 < t < 5.0:
            cy = G - (G - 46) * ((t - 3.6) / 1.4) ** 1.5
        elif 5.0 <= t < 9.6:
            cow = False
        elif 9.6 <= t < 10.1:
            cy = -10 + (G + 10) * ((t - 9.6) / 0.5) ** 2
        u1 = None
        if 2.6 <= t < 5.8:
            u1 = -20 + 62 * min(1.0, (t - 2.6) / 1.0)
        elif 5.8 <= t < 6.8:
            u1 = 42 - 18 * (t - 5.8)
        u2 = None
        if 4.8 <= t < 7.6:
            u2 = -40 + 64 * min(1.0, (t - 4.8) / 1.0)
        elif 7.6 <= t < 8.6:
            u2 = 24 - 160 * (t - 7.6) ** 2
        if u1 is not None and 3.6 < t < 5.0:
            _beam(img, self.CX + 4, u1 + 4, G + 2, 5, 14)
        if cow:
            _cow(img, cx, cy, t, walk=1.0 if t < 2.6 else 0.0)
            if 10.1 <= t < 10.6:
                ellipse(img, self.CX - 12 - (t - 10.1) * 30, G - 2, 5, 3, (.8, .75, .6), a=0.6)
                ellipse(img, self.CX + 16 + (t - 10.1) * 30, G - 2, 5, 3, (.8, .75, .6), a=0.6)
        if u2 is not None and 5.8 <= t < 6.8:
            _beam(img, self.CX + 4, u2 + 8, (u1 or 0) + 6, 8, 20)
        if u1 is not None:
            _ufo(img, self.CX + 4, u1, 16, t)
        if u2 is not None:
            _ufo(img, self.CX + 4, u2, 40, t)
        if 6.6 < t < 8.6:
            hy = -70 + 78 * min(1.0, (t - 6.6) / 0.8) if t < 7.6 else 8 - 160 * (t - 7.6) ** 2
            hx = self.CX + 4
            rect(img, hx - 18, hy - 80, hx + 18, hy - 20, (.2, .3, .7))
            ellipse(img, hx, hy - 6, 24, 20, SKINS[1])
            grip = 0 if t < 7.4 else 1
            for k in range(4):
                fx = hx - 16 + k * 10.5
                line(img, fx, hy + 6, fx + (k - 1.5) * 2 * grip, hy + 24 - 8 * grip, SKINS[1], w=7)
            line(img, hx + 22, hy - 6, hx + 30 - 8 * grip, hy + 12, SKINS[1], w=7)
        look = (-1, -0.3) if 9.3 < t < 10.7 else (0, 0)
        ellipse(img, 104, 76, 15, 17, (.25, .12, .05))
        person(img, 104, 78, 13, SKINS[2], (.15, .35, .7), t, talk=chatter(t) if look == (0, 0) else 0, look=look,
               mood=-1 if 10.7 < t < 11.4 else 1, seed=6)
        ellipse(img, 104, 69, 13, 6, (.25, .12, .05), half="top")
        line(img, 86, 100, 84, 92, (.15, .15, .15), w=2)
        ellipse(img, 84, 90, 3, 3.5, (.2, .2, .2))
        ellipse(img, 87, 100, 3, 3, SKINS[2])
        if 10.7 < t < 11.6:
            for s in (-1, 1):
                line(img, 104 + s * 14, 94, 104 + s * 22, 84, (.15, .35, .7), w=3)
                ellipse(img, 104 + s * 22, 84, 2.5, 2.5, SKINS[2])
        _live(img, "QUIET DAY HERE", 104)
        ticker(img, "NOTHING TO REPORT  *  NOTHING TO REPORT  *  ", 116, t, bg=(.1, .1, .3))


# ---------------------------------------------------------------- the cop show

class Duck(Show):
    """Silent: a detective sweats a rubber duck, who says nothing, and whose lawyer is a much bigger duck."""
    num, title, length = 281, "INTERROGATION", 10.0
    COAT = (.6, .5, .32)

    def __init__(self):
        bg = np.empty((N, N, 3), np.float32)
        vgrad(bg, (.25, .3, .28), (.17, .21, .19), 0, 100)
        rect(bg, 0, 96, N, 100, (.12, .14, .13))
        rect(bg, 0, 100, N, N, (.13, .13, .15))
        rect(bg, 70, 18, 124, 50, (.12, .12, .12))
        rect(bg, 72, 20, 122, 48, (.06, .08, .1))
        line(bg, 80, 46, 96, 22, (.2, .24, .28), w=3)
        rect(bg, 4, 28, 36, 100, (.18, .12, .08))
        self.wall = bg.copy()
        _lit(bg, [(60, 18), (68, 18), (104, 96), (24, 96)], (1, .95, .7), 0.2)
        line(bg, 64, 0, 64, 13, BLACK, w=1)
        poly(bg, [(56, 18), (72, 18), (68, 12), (60, 12)], (.15, .15, .12))
        ellipse(bg, 64, 18, 3, 2.5, (1, 1, .75))
        self.bg = bg

    def _duck(self, img, x, y, k=1.0, d=1):
        ellipse(img, x - d * 2 * k, y - 6 * k, 9 * k, 6 * k, (1, .85, .1))
        poly(img, [(x - d * 9 * k, y - 8 * k), (x - d * 14 * k, y - 13 * k), (x - d * 8 * k, y - 4 * k)], (1, .85, .1))
        ellipse(img, x + d * 4 * k, y - 15 * k, 5.5 * k, 5.5 * k, (1, .85, .1))
        ellipse(img, x + d * 10 * k, y - 14 * k, 3.2 * k, 1.6 * k, (1, .45, .1))
        ellipse(img, x + d * 5.5 * k, y - 16.5 * k, 1.1 * k, 1.1 * k, BLACK)

    def draw(self, img, t):
        img[:] = self.bg
        door = 26.0 if t < 5.6 else max(3.0, 26 - 23 * (t - 5.6) / 0.5)
        if t >= 5.6:
            rect(img, 6, 30, 32, 100, (.02, .02, .03))
        if t >= 6.1:
            push = 2 * math.sin(t * 5)
            ellipse(img, 20 + push, 58, 30, 30, (1, .85, .1))
            ellipse(img, 26 + push, 48, 3, 3, BLACK)
            poly(img, [(14, 92), (26, 92), (20, 104)], (.85, .1, .1))
            img[0:30, 0:40] = self.wall[0:30, 0:40]
            img[30:100, 32:40] = self.wall[30:100, 32:40]
            img[30:100, 0:6] = self.wall[30:100, 0:6]
            ellipse(img, 40 + push, 60, 14, 6, (1, .45, .1))
            line(img, 30 + push, 61, 52 + push, 61, (.7, .25, .05), w=1)
        rect(img, 6, 30, 6 + door, 100, (.45, .35, .25))
        if door > 10:
            ellipse(img, door + 2, 66, 1.5, 1.5, (.9, .8, .3))
        shake = 2 * math.sin(t * 50) if 1.85 < t < 2.2 else 0
        rect(img, 32, 90, 36, 114, (.35, .28, .2))
        rect(img, 92, 90, 96, 114, (.35, .28, .2))
        rect(img, 28, 84 + shake, 100, 90 + shake, (.5, .42, .32))
        hop = 9 * math.sin(math.pi * (t - 1.85) / 0.4) if 1.85 < t < 2.25 else 0
        self._duck(img, 58, 84 + shake - hop, d=-1 if t > 7.4 else 1)
        x, rot, arms, look, mood, jump, talk = 104.0, -0.1, (1.6, 0.3), (-1, 0), 0, 0.0, chatter(t)
        if 1.4 <= t < 1.75:
            rot, arms, talk = -0.1, (2.8, 2.8), 1.0
        elif 1.75 <= t < 2.4:
            rot, arms, talk = -0.3, (1.1, 1.1), 1.0
        elif 2.4 <= t < 4.0:
            u = min(1.0, (t - 2.4) / 0.4)
            x, rot, arms, talk, look = 104 - 8 * u, -0.55 * u, (0.6, 0.6), 0, (-1, 0.3)
        elif 4.0 <= t < 6.2:
            x, rot, arms, talk, mood = 96 + math.sin(t * 25), -0.95, (1.4, 1.4), 0.6, -1
        elif t >= 6.2:
            u = min(1.0, (t - 6.2) / 0.3)
            x, rot, arms, talk, mood, jump = 108, 0.25 * u, (2.8, 2.8), 1.0, -1, 8 * u
        hx, hy, r = toon(img, x, 120 - LEG * 62 - jump, 62, SKINS[0], self.COAT, t, rot=rot, arms=arms, look=look,
                         mood=mood, talk=talk, pants=(.3, .3, .32), seed=7)
        hat = -9 if t >= 6.3 else 0
        c, s = math.cos(rot), math.sin(rot)
        bx, by = hx + (r * 0.9 - hat) * s, hy - (r * 0.9 - hat) * c
        _rrect(img, bx, by, r * 3, r * 0.35, rot, (.3, .25, .18))
        _rrect(img, bx + r * 0.5 * s, by - r * 0.5 * c, r * 1.6, r * 0.9, rot, (.3, .25, .18))
        if 2.8 < t < 6.2 or t > 6.4:
            for k in range(2):
                u = (t * 1.5 + k * 0.5) % 1
                ellipse(img, hx + (k * 2 - 1) * r * 0.9, hy - r * 0.3 + 14 * u, 1.3, 2, (.6, .85, 1))
        if 4.3 < t < 6.2:
            for sd in (-1, 1):
                for j in range(5):
                    u = (t * 2 + j * 0.2) % 1
                    ellipse(img, hx + sd * (4 + 16 * u), hy - 2 - 12 * u + 26 * u * u, 1.2, 1.6, (.5, .8, 1))


# ---------------------------------------------------------------- the dive

class Dive(Show):
    """Silent: the highest dive in the world, into a gentleman's cup of tea."""
    num, title, length = 287, "HIGH DIVE", 10.5
    YEND, T0, TL, H = 1400.0, 2.4, 6.6, 26
    CUPX, CUPY = 66, 96

    def __init__(self):
        rng = np.random.default_rng(287)
        self.clouds = [(rng.uniform(90, 1250), rng.uniform(0, N), rng.uniform(8, 16)) for _ in range(16)]
        self.streaks = rng.uniform(size=(8, 2))

    def _wy(self, t):
        if t < self.T0:
            return 0.0
        tau = min(1.0, (t - self.T0) / (self.TL - self.T0))
        return (self.YEND - 16) * tau ** 1.8 - 22 * math.sin(math.pi * min(1.0, tau * 5))

    def _cam(self, t):
        if t < self.T0:
            return -70.0
        tau = (t - self.T0) / (self.TL - self.T0)
        return min(self._wy(t) - 60 - 10 * max(0.0, 1 - tau * 4), self.YEND - self.CUPY)

    def draw(self, img, t):
        cam = self._cam(t)
        deep, pale = np.array((.06, .12, .45), np.float32), np.array((.6, .82, 1), np.float32)
        a, b = np.clip(cam / self.YEND, 0, 1), np.clip((cam + N) / self.YEND, 0, 1)
        vgrad(img, tuple(deep + (pale - deep) * a), tuple(deep + (pale - deep) * b))
        falling = self.T0 < t < self.TL
        if falling:
            for sx, sy in self.streaks:
                y = (sy * 200 - (t * 400) % 200)
                line(img, sx * N, y, sx * N, y + 30, WHITE, w=1, a=0.25)
        for wy, x, sz in self.clouds:
            sy = wy - cam
            if -20 < sy < N + 20:
                for dx in (-1, 0, 1):
                    ellipse(img, x + dx * sz * 0.8, sy - (dx == 0) * sz * 0.3, sz, sz * 0.55, (.97, .97, 1), a=0.9)
        sy = 470 - cam
        if -20 < sy < N + 20:
            px = 150 - (t - self.T0) * 70
            ellipse(img, px, sy, 18, 4, (.9, .9, .95))
            poly(img, [(px + 12, sy), (px + 20, sy - 9), (px + 18, sy)], (.85, .2, .2))
            poly(img, [(px - 4, sy), (px + 6, sy), (px + 2, sy + 9)], (.75, .75, .8))
            for k in range(4):
                rect(img, px - 10 + k * 4, sy - 2, px - 8 + k * 4, sy, (.3, .5, .8))
        sy = 820 - cam
        if -20 < sy < N + 20:
            for k in range(4):
                bx, by = 30 + k * 12 + (t * 20) % 10, sy + (k % 2) * 6
                f = 3 * math.sin(t * 12 + k)
                line(img, bx - 4, by - f, bx, by, BLACK, w=1)
                line(img, bx, by, bx + 4, by - f, BLACK, w=1)
        sy = 1060 - cam
        if -30 < sy < N + 20:
            ellipse(img, 22, sy, 11, 13, (1, .4, .2))
            rect(img, 20, sy - 13, 24, sy + 12, (1, .9, .3))
            line(img, 16, sy + 10, 19, sy + 18, BLACK, w=1)
            line(img, 28, sy + 10, 25, sy + 18, BLACK, w=1)
            rect(img, 18, sy + 18, 26, sy + 23, (.5, .3, .1))
        by = -cam
        if by < N:
            rect(img, 0, by, 58, by + 4, (.95, .95, .95))
            for px in (6, 40):
                rect(img, px, by + 4, px + 4, min(N, 45 - cam), (.6, .6, .65))
        if -40 < 45 - cam < N + 20:
            for k in range(7):
                ellipse(img, k * 21, 45 - cam + 3 * (k % 2), 16, 9, (.97, .97, 1))
        self._ground(img, t, cam)
        wy = self._wy(t)
        if t < self.TL:
            if t < self.T0:
                bounce = 4 * abs(math.sin(t * 7)) if t > 1.0 else 0
                toon(img, 48, -cam - LEG * self.H - bounce, self.H, SKINS[1], (.1, .5, .9), t,
                     arms=(2.9, 2.9) if t > 1.6 else (0.3, 0.3), look=(0, 1) if t < 1.0 else (0, 0), seed=8,
                     pants=(.1, .5, .9), mood=1 if t > 1.6 else 0)
            else:
                tau = (t - self.T0) / (self.TL - self.T0)
                sm = tau * tau * (3 - 2 * tau)
                rot = (t - self.T0) * 13 if tau < 0.82 else math.pi
                toon(img, 48 + (self.CUPX - 48) * sm, wy - cam - LEG * self.H, self.H, SKINS[1], (.1, .5, .9), t,
                     rot=rot, arms=(2.9, 2.9), seed=8, pants=(.1, .5, .9))
        self._cup(img, t, cam)
        if t < self.TL:
            alt = int(max(0.0, self.YEND - wy) * 7)
            rect(img, 2, 2, 52, 13, BLACK, a=0.5)
            draw.text(img, f"{alt:,} M", 27, 3, (1, 1, .5), center=True)
        lt = t - self.TL
        for k in range(3):
            up = min(1.0, max(0.0, (lt - 1.9 - k * 0.35) / 0.15))
            if up > 0:
                x = 26 + k * 38
                rect(img, x - 14, 6, x + 14, 6 + 26 * up, WHITE)
                if up >= 1:
                    draw.text(img, "10", x, 9, BLACK, center=True, scale=2)

    def _ground(self, img, t, cam):
        rim = self.YEND - cam
        if rim > N + 60:
            return
        rect(img, 0, rim + 12, N, N, (.75, .62, .45))
        line(img, 112, rim - 40, 112, rim + 12, (.4, .4, .4), w=1.5)
        for k in range(4):
            poly(img, [(112, rim - 50), (88 + k * 12, rim - 38), (100 + k * 12, rim - 38)],
                 (.9, .2, .2) if k % 2 else (.97, .97, .95))
        rect(img, 40, rim + 8, 104, rim + 12, (.97, .97, .97))
        for lx in (46, 96):
            rect(img, lx, rim + 12, lx + 3, rim + 30, (.4, .3, .2))
        ellipse(img, 90, rim - 12, 9, 9, (.85, .2, .25), half="top")
        rect(img, 81, rim - 12, 99, rim + 8, (.85, .2, .25))
        lt = t - self.TL
        look = (-1, 1) if 0 < lt < 0.9 or lt > 2.4 else (-1, 0)
        face(img, 90, rim - 22, 8, SKINS[0], t, look=look, mood=1 if lt > 2.0 else 0, seed=9)
        rect(img, 82, rim - 32, 98, rim - 28, (.15, .12, .1))
        rect(img, 85, rim - 40, 95, rim - 30, (.15, .12, .1))

    def _cup(self, img, t, cam):
        lt = t - self.TL
        sip = math.sin(math.pi * min(1.0, max(0.0, (lt - 0.9) / 1.0)))
        x, y = self.CUPX + 12 * sip, self.YEND - cam - 14 * sip
        if y > N + 20:
            return
        ellipse(img, self.CUPX, self.YEND - cam + 8, 10, 1.8, (.95, .95, .95))
        line(img, 84, y + 10 - 10 * sip, x + 8, y + 3, (.85, .2, .25), w=3)
        ellipse(img, x + 8, y + 3, 2.5, 2.5, SKINS[0])
        draw.ring(img, x + 7, y + 3, 2.5, WHITE, width=1.2)
        ellipse(img, x, y + 1, 6, 6, WHITE, half="bottom")
        ellipse(img, x, y + 1, 6, 1.6, (.6, .35, .15))
        if 0 <= lt < 0.6:
            for k in range(8):
                a = math.pi * (0.15 + 0.7 * k / 7)
                ellipse(img, x - math.cos(a) * 30 * lt, y - math.sin(a) * 40 * lt + 60 * lt * lt, 1.3, 1.3,
                        (.6, .35, .15))
        if lt > 2.2:
            w = math.sin(t * 10) * 2
            line(img, x - 1, y, x - 1 + w, y - 6, SKINS[1], w=1.5)
            ellipse(img, x - 1 + w, y - 7, 1.5, 1.5, SKINS[1])


CHANNELS = [Chair, Quiz, Grape, Booth, Chase, Order, Sitcom, Dream, Rock, Moon, Kettle, Lotto, Field, Duck, Dive]
