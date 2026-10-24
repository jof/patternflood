"""Polar painter: k0 orbits the pen round the centre, k1 moves it in and out.

The same drawing toy as Etch, in polar coordinates, with n-fold symmetry. The
question is whether a rotary knob driving an angle feels more natural than
two knobs driving x and y.
"""
import math

import numpy as np

from .. import draw
from ..draw import N, hsv1
from ..runtime import DETENTS_PER_REV, Demo

C = (N - 1) / 2


class Mandala(Demo):
    name = "Mandala"
    blurb = "k0 orbits the pen, k1 in and out, k2 colour, k3 symmetry (1-12 fold). Click k0 mirror, k1 clear, k2 rainbow, k3 spin."

    def __init__(self, rt):
        super().__init__(rt)
        self.canvas = draw.blank()
        self.a, self.r = -math.pi / 2, 30.0
        self.hue = 0.55
        self.fold = 6
        self.mirror = True
        self.rainbow = False
        self.spin = False
        self.rot = 0.0
        self.t_fold = -10.0
        self.clearing = 0.0

    def _pen(self, a=None, r=None):
        a, r = self.a if a is None else a, self.r if r is None else r
        return C + r * math.cos(a), C + r * math.sin(a)

    def _copies(self, a, r):
        pts = []
        for i in range(self.fold):
            b = a + 2 * math.pi * i / self.fold
            pts.append((C + r * math.cos(b), C + r * math.sin(b)))
            if self.mirror:
                b = -a + 2 * math.pi * i / self.fold
                pts.append((C + r * math.cos(b), C + r * math.sin(b)))
        return pts

    def turn(self, k, d):
        if k in (0, 1):
            a0, r0 = self.a, self.r
            if k == 0:
                self.a += self.rt.accel(0, d, top=3) * 2 * math.pi / (DETENTS_PER_REV * 2)
            else:
                self.r = min(62.0, max(0.0, self.r + self.rt.accel(1, d)))
            self._stroke(a0, r0, self.a, self.r)
        elif k == 2:
            self.hue = (self.hue + d / 36.0) % 1.0
        elif k == 3:
            self.fold = min(12, max(1, self.fold + (1 if d > 0 else -1)))
            self.t_fold = self.rt.t

    def _stroke(self, a0, r0, a1, r1):
        # walk the polar path in small steps so arcs stay arcs
        n = max(1, int(max(abs(a1 - a0) * max(r0, r1), abs(r1 - r0)) / 0.6))
        for i in range(1, n + 1):
            s = i / n
            a, r = a0 + (a1 - a0) * s, r0 + (r1 - r0) * s
            if self.rainbow:
                self.hue = (self.hue + 0.003) % 1.0
            c = hsv1(self.hue)
            for x, y in self._copies(a - self.rot, r):     # into canvas space, so spinning doesn't smear
                draw.disc(self.canvas, x, y, 0.7, c, soft=0.6)

    def release(self, k, click):
        if not click:
            return
        if k == 0:
            self.mirror = not self.mirror
        elif k == 1:
            self.clearing = 0.6
        elif k == 2:
            self.rainbow = not self.rainbow
        elif k == 3:
            self.spin = not self.spin

    def step(self, dt):
        if self.spin:
            self.rot += 0.35 * dt
        if self.clearing > 0:
            self.clearing -= dt
            r = np.hypot(draw.X - C, draw.Y - C)
            edge = 64 * (1 - max(0.0, self.clearing) / 0.6)
            self.canvas[r < edge] *= 0.6
            if self.clearing <= 0:
                self.canvas[:] = 0

    def render(self):
        if self.rot:
            # sample the canvas through the rotation (nearest pixel)
            c, s = math.cos(-self.rot), math.sin(-self.rot)
            xs = (draw.X - C) * c - (draw.Y - C) * s + C
            ys = (draw.X - C) * s + (draw.Y - C) * c + C
            xi, yi = np.rint(xs).astype(int), np.rint(ys).astype(int)
            ok = (xi >= 0) & (xi < N) & (yi >= 0) & (yi < N)
            img = np.zeros_like(self.canvas)
            img[ok] = self.canvas[yi[ok], xi[ok]]
        else:
            img = self.canvas.copy()
        # symmetry spokes, briefly, when the fold changes
        guide = max(0.0, 1 - (self.rt.t - self.t_fold) / 1.2)
        if guide:
            for i in range(self.fold):
                b = self.a + 2 * math.pi * i / self.fold
                xs, ys = draw.segment(C, C, C + 62 * math.cos(b), C + 62 * math.sin(b), step=1.5)
                draw.plot(img, xs, ys, (.25 * guide,) * 3, op="max")
            draw.text(img, f"{self.fold}-fold{' mirror' if self.mirror else ''}", 64, 2, (guide,) * 3, center=True)
        x, y = self._pen()
        draw.ring(img, x, y, 2.5, (1, 1, 1))
        for px, py in self._copies(self.a, self.r)[1:]:
            draw.ring(img, px, py, 2.0, (.25, .25, .25))
        return img

    def lights(self):
        c = hsv1(self.hue)
        return [(1, 1, 1) if self.mirror else tuple(v * .4 for v in c),
                tuple(v * (0.2 + self.r / 62 * 0.8) for v in c),
                hsv1(self.rt.t * 0.5) if self.rainbow else c,
                hsv1(self.rot * 0.2) if self.spin else ((self.fold / 12,) * 3)]
