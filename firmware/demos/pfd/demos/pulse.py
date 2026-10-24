"""Geometry that plays along: rings on the kick, a turning figure on the bar,
colour on the phrase, and the build and drop as tension and release.

Every kick sends a ring out from the centre, sized by the bass. A polygon at
the centre turns once a bar and steps its sides with the beat. The hue moves
on at each phrase boundary. Through a build the rings come faster and tighter
and the figure spins up; a drop bursts outward and flips the palette for a bar.
No strobing: flashes are soft and the current cap applies as everywhere.

    k0  hue
    k1  symmetry (sides of the figure, folds of the rings)
    k2  reactivity
    k3  trails
"""
import math
import random

import numpy as np

from .. import draw
from ..draw import N, hsv, hsv1
from ..runtime import Demo

C = 63.5


class Pulse(Demo):
    name = "Pulse"
    blurb = "Rings on the kick, a figure turning with the bar, colour by phrase, and builds and drops as tension and release. k0 hue, k1 symmetry, k2 reactivity, k3 trails."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = random.Random()
        self.hue = 0.6
        self.sym = 6
        self.react = 1.0
        self.trails = 0.82
        self.rings = []                  # [radius, speed, strength, hue offset]
        self.canvas = draw.blank()
        self.burst = 0.0
        self.invert = 0.0
        self.spin = 0.0
        self.R = np.hypot(draw.X - C, draw.Y - C)
        self.A = np.arctan2(draw.Y - C, draw.X - C)

    def turn(self, k, d):
        if k == 0:
            self.hue = (self.hue + d / 48) % 1.0
        elif k == 1:
            self.sym = min(12, max(3, self.sym + (1 if d > 0 else -1)))
        elif k == 2:
            self.react = min(3.0, max(0.2, self.react * 1.1 ** d))
        elif k == 3:
            self.trails = min(0.96, max(0.5, self.trails + d * 0.02))

    def step(self, dt):
        a = self.rt.audio
        build = a.build
        if a.kick_hit or (a.beat and not a.live) or (a.beat and a.kick < 0.2):
            self.rings.append([4.0, 40 + 50 * a.bass * self.react + 40 * build,
                               0.5 + 0.5 * min(1.0, a.kick * self.react + 0.3), self.rng.uniform(-.05, .05)])
        if a.snare_hit:
            self.rings.append([2.0, 70, 0.35, 0.5])
        if a.phrase:
            self.hue = (self.hue + 0.18) % 1.0
        if a.drop:
            self.burst = 1.0
            self.invert = 1.0
        if a.bar and self.invert > 0:
            self.invert = max(0.0, self.invert - 0.5)
        for r in self.rings:
            r[0] += r[1] * dt
            r[2] *= math.exp(-dt * 1.2)
        self.rings = [r for r in self.rings if r[0] < 100 and r[2] > 0.03][-24:]
        self.burst = max(0.0, self.burst - dt * 1.5)
        self.spin += dt * (0.4 + 3 * build) * (1 if a.beat_in_bar % 2 == 0 else 1.15)
        self.canvas *= self.trails ** (dt * 60)

    def render(self):
        a = self.rt.audio
        hue = self.hue + 0.5 * self.invert
        img = self.canvas
        # rings, folded into symmetry so they wobble like petals
        petal = 1 + 0.08 * np.cos(self.A * self.sym + self.spin * 2)
        for rad, _, strength, dh in self.rings:
            band = np.clip(1 - np.abs(self.R * petal - rad) / (1.6 + 2 * a.bass), 0, 1) * strength
            img += band[..., None] * np.array(hsv1(hue + dh + rad / 300, 0.8, 1.0), np.float32) * 0.6
        # the figure: a polygon turning once a bar, its size breathing with the bass
        sides = self.sym
        rot = a.bar_phase * 2 * math.pi / sides * 2 + self.spin
        r0 = 10 + 10 * a.bass * self.react + 6 * math.exp(-a.phase * 4)
        pts = [(C + r0 * math.cos(rot + 2 * math.pi * i / sides), C + r0 * math.sin(rot + 2 * math.pi * i / sides))
               for i in range(sides)]
        fig = draw.blank()
        draw.poly(fig, pts, hsv1(hue + 0.33, 0.6, 0.6 + 0.4 * math.exp(-a.phase * 4)))
        img = np.maximum(img, fig)
        self.canvas = img
        out = img.copy()
        if self.burst > 0:
            k = self.burst
            out += np.clip(1 - np.abs(self.R - (1 - k) * 110) / 10, 0, 1)[..., None] * k * np.array(hsv1(hue + .5), np.float32)
        # the beat, softly, at the rim
        rim = np.clip((self.R - 58) / 8, 0, 1) * math.exp(-a.phase * 5) * 0.25 * self.react
        out += rim[..., None] * np.array(hsv1(hue + 0.1, 0.6, 1.0), np.float32)
        return out

    def lights(self):
        a = self.rt.audio
        b = math.exp(-a.phase * 4)
        return [hsv1(self.hue, .8, .3 + .7 * b), (self.sym / 12 * .6,) * 3,
                (min(1, self.react / 2),) * 3, (1, .3, .2) if self.burst else hsv1(self.hue + .5, .5, .3)]
