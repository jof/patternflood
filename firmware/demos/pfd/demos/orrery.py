"""Orrery: a little solar system turning, every world lit from its sun, dithered.

After SeungHun's 0513, its rings of tiles. A sun burns in the middle; five planets
circle it at speeds that fall off with distance, as Kepler's third law has
it (the period grows as the orbit's radius to the power 1.5). One has rings,
two have moons. The orbits are tilted towards us, so planets pass in front
of the sun and behind it, nearer ones larger, drawn far to near. Each planet
is lit from the sun's direction, so seen from the side it's half lit, and
crossing in front of the sun it's a dark disc with a bright rim. The orbits
themselves show as faint dotted ellipses.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

# radius (orbit), size, albedo, moons, ringed
PLANETS = [(15, 3.2, 0.8, 0, False), (24, 4.8, 0.9, 0, False), (34, 5.4, 0.75, 1, False),
           (46, 7.5, 0.85, 2, True), (58, 5.8, 0.7, 0, False)]


class Orrery(Inked):
    name = "Orrery"
    blurb = "A little solar system, each world lit from its sun, dithered (after SeungHun's 0513). k0 time, k1 tilt, k2 screen, k3 inks. Click k0 reverse time, k1 orbits on or off, k2 chunky."
    palette, screen_kind = "dusk", "bayer4"

    def __init__(self, rt):
        super().__init__(rt)
        rng = np.random.default_rng(21)
        self.phase0 = rng.uniform(0, 2 * math.pi, len(PLANETS))
        self.speed, self.dir = 1.0, 1
        self.tilt = 1.05                # radians from face-on
        self.orbits = True
        self.days = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.speed = max(0.05, min(8.0, self.speed * 1.1 ** d))
        elif k == 1:
            self.tilt = max(0.0, min(1.5, self.tilt + d * 0.03))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.dir = -self.dir
        elif k == 1:
            self.orbits = not self.orbits
        elif k == 2:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        self.days += dt * self.speed * self.dir * (1 + 1.5 * self.sound[0])

    def place(self, radius, phase):
        """A point on a tilted circular orbit: screen x, y and depth (towards us positive)."""
        x, y = radius * math.cos(phase), radius * math.sin(phase)
        ct, st = math.cos(self.tilt), math.sin(self.tilt)
        return 63.5 + x, 63.5 + y * ct, y * st

    def render(self):
        tone = np.full((N, N), 0.02, np.float32)
        bodies = []                     # (depth, x, y, size, albedo, kind)
        for i, (rad, size, alb, moons, ringed) in enumerate(PLANETS):
            period = (rad / 14) ** 1.5 * 6                         # Kepler: period ~ radius^1.5
            ph = self.phase0[i] + self.days * 2 * math.pi / period
            x, y, z = self.place(rad, ph)
            bodies.append((z, x, y, size, alb, "ringed" if ringed else "planet"))
            for m in range(moons):
                mr = size * 1.6 + 4 + 3 * m
                mp = self.days * 2 * math.pi / (1.2 + m) + m * 2
                ct, st = math.cos(self.tilt), math.sin(self.tilt)
                mx, my = mr * math.cos(mp), mr * math.sin(mp)
                bodies.append((z + my * st, x + mx, y + my * ct, 1.6, 0.7, "moon"))
            if self.orbits:                                        # the orbit, dotted
                a = np.linspace(0, 2 * math.pi, int(rad * 3), endpoint=False)
                ox = 63.5 + rad * np.cos(a)
                oy = 63.5 + rad * np.sin(a) * math.cos(self.tilt)
                xi, yi = np.rint(ox).astype(int), np.rint(oy).astype(int)
                ok = (xi >= 0) & (xi < N) & (yi >= 0) & (yi < N) & (np.arange(len(a)) % 2 == 0)
                tone[yi[ok], xi[ok]] = np.maximum(tone[yi[ok], xi[ok]], 0.2)
        bodies.append((0.0, 63.5, 63.5, 8.5, 1.0, "sun"))
        for z, x, y, size, alb, kind in sorted(bodies, key=lambda b: b[0]):
            r = size * (1 + z / 180)                               # perspective, gently
            if kind == "sun":
                d = np.hypot(X - x, Y - y)
                glow = np.exp(-np.maximum(d - r, 0) / 5) * (0.95 + 0.05 * math.sin(self.rt.t * 7)) * (1 + 0.2 * self.beat)
                tone = np.maximum(tone, np.where(d < r, 1.0, glow * 0.6))
                continue
            reach = r * (2.3 if kind == "ringed" else 1) + 1
            x0, x1 = max(0, int(x - reach)), min(N, int(x + reach) + 2)
            y0, y1 = max(0, int(y - reach)), min(N, int(y + reach) + 2)
            if x0 >= x1 or y0 >= y1:
                continue
            u, v = (X[y0:y1, x0:x1] - x) / r, (Y[y0:y1, x0:x1] - y) / r
            q = 1 - u * u - v * v
            inside = q > 0
            w = np.sqrt(np.clip(q, 0, 1))
            # lit from the sun: the direction from the planet back to the sun, in view space
            ct, st = math.cos(self.tilt), math.sin(self.tilt)
            sx, sy = 63.5 - x, (63.5 - y)
            depth_to_sun = -z
            L = np.array([sx, sy, depth_to_sun], np.float32)
            L /= np.linalg.norm(L) + 1e-6
            lit = np.clip(u * L[0] + v * L[1] + w * L[2], 0, 1)
            val = alb * (0.04 + 0.95 * lit)
            if kind == "ringed":                                   # bands, and rings in the orbit's plane
                val = val * (0.85 + 0.15 * np.sin(v * 9))
            region = tone[y0:y1, x0:x1]
            if kind == "ringed":
                rv = (Y[y0:y1, x0:x1] - y) / max(0.3, ct)
                ring_r = np.hypot((X[y0:y1, x0:x1] - x), rv) / r
                ring = (ring_r > 1.35) & (ring_r < 2.2) & (np.abs(ring_r - 1.8) > 0.07)
                behind = ring & (rv < 0)
                region[behind & ~inside] = 0.45 * alb
                region[inside] = val[inside]
                front = ring & (rv >= 0)
                region[front] = 0.45 * alb + 0.1 * np.sin(ring_r[front] * 30)
            else:
                region[inside] = val[inside]
        return self.print(np.clip(tone, 0, 1))

    def lights(self):
        return [self.glow(0, 0.1, 0.2 + 0.1 * self.speed), self.glow(1, 0.6, 0.2 + 0.3 * self.tilt)] + self.ink_lights()
