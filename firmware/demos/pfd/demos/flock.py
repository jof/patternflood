"""Flock: a murmuration of starlings at dusk, and the falcon that shapes it, dithered.

After Lee's Vector Field Flow. Eighteen hundred birds follow three rules,
each taken from the birds near it: steer the way they're flying (alignment),
towards where they are (cohesion), and away from where they're crowded
(separation). "Near" is a grid of cells averaged together, so it costs little
per bird. A falcon cruises through and the birds flee it, and the flight
from it ripples across the flock as a dark wave, which is what makes a
murmuration twist and pulse. Birds are dark against a sunset sky, darker
where they bunch.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

BIRDS = 1800
CELL = 8
G = N // CELL


def _cells(p):
    ix = np.clip((p[:, 0] // CELL).astype(int), 0, G - 1)
    iy = np.clip((p[:, 1] // CELL).astype(int), 0, G - 1)
    return iy * G + ix


def _spread(a):
    """Average each cell with its neighbours (so a bird sees the birds next door too)."""
    return (a + np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1)) / 5


class Flock(Inked):
    name = "Flock"
    blurb = "A murmuration of starlings at dusk, and the falcon that shapes it, dithered (after Lee's Vector Field Flow). k0 cohesion, k1 the falcon's hunger, k2 screen, k3 inks. Click k0 scatter, k1 the falcon stoops, k2 chunky."
    palette, screen_kind = "dusk", "bayer4"

    def __init__(self, rt):
        super().__init__(rt)
        rng = self.rng = np.random.default_rng()
        a = rng.uniform(0, 2 * math.pi, BIRDS)
        r = rng.normal(0, 14, BIRDS)
        self.p = np.column_stack([64 + r * np.cos(a), 50 + r * np.sin(a) * 0.6]).astype(np.float32)
        self.v = np.column_stack([np.cos(a), np.sin(a)]).astype(np.float32) * 20
        self.falcon = np.array([10.0, 20.0], np.float32)
        self.fv = np.array([30.0, 8.0], np.float32)
        self.cohesion, self.hunger = 1.0, 1.0
        self.stoop = 0.0
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.cohesion = max(0.2, min(3.0, self.cohesion * 1.07 ** d))
        elif k == 1:
            self.hunger = max(0.0, min(3.0, self.hunger + d * 0.1))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.v += self.rng.normal(0, 40, self.v.shape).astype(np.float32)
        elif k == 1:
            self.stoop = 1.0
        elif k == 2:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        dt = min(dt, 1 / 30)
        self.t += dt
        p, v = self.p, self.v
        c = _cells(p)
        count = np.bincount(c, minlength=G * G).reshape(G, G).astype(np.float32)
        sx = np.bincount(c, weights=p[:, 0], minlength=G * G).reshape(G, G)
        sy = np.bincount(c, weights=p[:, 1], minlength=G * G).reshape(G, G)
        svx = np.bincount(c, weights=v[:, 0], minlength=G * G).reshape(G, G)
        svy = np.bincount(c, weights=v[:, 1], minlength=G * G).reshape(G, G)
        n = _spread(count) + 1e-3
        mx, my = _spread(sx) / n, _spread(sy) / n
        mvx, mvy = _spread(svx) / n, _spread(svy) / n
        # crowding: the slope of the density field pushes birds out of the thick of it
        dens = _spread(_spread(count))
        gx = (np.roll(dens, -1, 1) - np.roll(dens, 1, 1)).ravel()
        gy = (np.roll(dens, -1, 0) - np.roll(dens, 1, 0)).ravel()
        acc = np.zeros_like(v)
        acc[:, 0] += (mvx.ravel()[c] - v[:, 0]) * 3.0                       # alignment
        acc[:, 1] += (mvy.ravel()[c] - v[:, 1]) * 3.0
        acc += (v.mean(0) - v) * 0.6                                         # and with the flock's heading
        acc[:, 0] += (mx.ravel()[c] - p[:, 0]) * 0.3 * self.cohesion        # cohesion, with neighbours
        acc[:, 1] += (my.ravel()[c] - p[:, 1]) * 0.3 * self.cohesion
        acc[:, 0] -= gx[c] * 1.2                                            # separation
        acc[:, 1] -= gy[c] * 1.2
        acc += (p.mean(0) - p) * 0.18 * self.cohesion                       # and the flock holds together
        acc += self.rng.normal(0, 6, acc.shape).astype(np.float32)          # every bird a little wayward
        # the whole flock wanders round a roost point in the sky, and stays on screen
        roost = np.array([64 + 30 * math.sin(self.t * 0.11), 52 + 18 * math.sin(self.t * 0.07)], np.float32)
        acc += (roost - p.mean(0)) * 0.6                                    # the roost steers the whole flock
        # the falcon: birds near it flee hard, and the flight spreads through the flock by alignment
        d = p - self.falcon
        dist = np.sqrt((d ** 2).sum(1)) + 1e-3
        fear = np.clip(1 - dist / (14 + 8 * self.hunger), 0, 1) ** 2 * 140 * (0.5 + self.hunger)
        acc += d / dist[:, None] * fear[:, None]
        v += acc * dt
        speed = np.sqrt((v ** 2).sum(1)) + 1e-3
        v *= (np.clip(speed, 12, 28) / speed)[:, None]                       # starlings keep their pace
        p += v * dt
        for axis in (0, 1):                                                  # the edges of the sky push back
            lo, hi = 6.0, (N - 6.0 if axis == 0 else 108.0)
            v[:, axis] += (np.clip(lo - p[:, axis], 0, None) - np.clip(p[:, axis] - hi, 0, None)) * 8 * dt
        np.clip(p, -10, N + 10, out=p)
        # the falcon cruises through, now and then turning to stoop at the flock's middle
        centre = p.mean(0)
        want = (centre - self.falcon)
        want /= np.linalg.norm(want) + 1e-6
        lunge = self.stoop or (self.listening and self.on_beat and self.rt.audio.kick > 0.6)
        if lunge:
            self.stoop = 1.0
        self.stoop *= math.exp(-dt / 1.5)
        target = want * (34 + 40 * self.stoop) * self.hunger + np.array([math.cos(self.t * 0.3), math.sin(self.t * 0.23)]) * 20
        self.fv += (target - self.fv) * min(1.0, dt * (1.5 + 3 * self.stoop))
        self.falcon += self.fv * dt
        self.falcon = np.clip(self.falcon, -20, N + 20).astype(np.float32)
        if self.on_phrase:
            self.v += self.rng.normal(0, 30, self.v.shape).astype(np.float32)

    def render(self):
        sky = 0.85 - 0.6 * np.clip((1 - Y / 128) ** 1.4, 0, 1)                # bright at the horizon, deep above
        sky = sky + 0.12 * np.exp(-((X - 30) ** 2 + (Y - 120) ** 2) / 600)     # where the sun went down
        xi, yi = np.rint(self.p[:, 0]).astype(int), np.rint(self.p[:, 1]).astype(int)
        ok = (xi >= 0) & (xi < N) & (yi >= 0) & (yi < N)
        cover = np.zeros((N, N), np.float32)
        np.add.at(cover, (yi[ok], xi[ok]), 1.0)
        tone = sky * np.exp(-cover * 0.9)                                      # each bird a dark speck; clumps darker
        fx, fy = int(self.falcon[0]), int(self.falcon[1])
        if 1 <= fx < N - 1 and 1 <= fy < N - 1:                                # the falcon: a small dark cross
            tone[fy, fx - 1:fx + 2] = 0
            tone[fy - 1:fy + 1, fx] = 0
        ground = Y > 118 + 2 * np.sin(X * 0.1)                                 # a line of trees on the horizon
        tone[ground] = 0.02
        return self.print(np.clip(tone, 0, 1))

    def lights(self):
        return [self.glow(0, 0.75, 0.2 + 0.2 * self.cohesion), self.glow(1, 0.0, 0.2 + 0.25 * self.hunger)] + self.ink_lights()
