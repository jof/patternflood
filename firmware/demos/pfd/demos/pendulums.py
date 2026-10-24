"""Pendulums: the pendulum wave, a row of swinging balls falling in and out of step.

After Lee's Wave Saw. Eighteen pendulums hang from one bar; their lengths are
chosen so that, in one cycle of the dance, the first swings 51 times, the
next 52, and so on. Released together they make a travelling snake, then two
interleaved lines, three, a scatter, and at the end of the cycle they all line
up again. We look down the row a little from above and in perspective, so the
pattern reads as waves running away from us. The balls are shaded spheres
that pass in front of and behind one another properly.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

COUNT = 18
CYCLE = 60.0                    # seconds for the whole dance to come round
BASE = 51                       # swings per cycle for the first pendulum
AMP = 0.45                      # swing, radians
BAR = 40.0                      # the bar's height above the balls' rest


class Pendulums(Inked):
    name = "Pendulums"
    blurb = "The pendulum wave: a row of pendulums falling in and out of step (after Lee's Wave Saw). k0 speed, k1 view, k2 screen, k3 inks. Click k0 release them together, k2 chunky."
    palette, screen_kind = "riso", "bayer4"

    def __init__(self, rt):
        super().__init__(rt)
        self.speed, self.view = 1.0, 1.0
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.speed = max(0.0, min(4.0, self.speed + d * 0.1))
        elif k == 1:
            self.view = max(0.1, min(1.4, self.view + d * 0.03))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.t = 0.0
        elif k == 2:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        self.t += dt * self.speed * (1 + self.sound[0])
        if self.on_phrase:
            self.t = 0.0

    def render(self):
        n = np.arange(COUNT)
        omega = 2 * math.pi * (BASE + n) / CYCLE
        swing = AMP * np.cos(omega * self.t) * (1 + 0.25 * self.beat)
        length = 9.8 * (CYCLE / (BASE + n) / (2 * math.pi)) ** 2 * 150     # from the period (metres), scaled to the scene
        # world: the bar runs along z (away from us), pendulums swing in x, y is down
        z = n * 4.0
        bx = np.sin(swing) * length
        by = np.cos(swing) * length - BAR
        # camera: looking down the row from a little above and to the side
        cv, sv = math.cos(self.view), math.sin(self.view)
        def project(x, y, zz):
            yy = y * cv - zz * sv
            zc = y * sv + zz * cv + 70
            f = 120 / zc
            return 63.5 + x * f, 64 + (yy + 34) * f, zc, f
        tone = np.full((N, N), 0.03, np.float32)
        depth = np.full((N, N), 1e9, np.float32)
        # the bar and the strings, faint
        for i in range(COUNT):
            sx, sy, _, _ = project(np.linspace(0, bx[i], 24), np.linspace(-BAR, by[i], 24), np.full(24, z[i]))
            xi, yi = np.rint(sx).astype(int), np.rint(sy).astype(int)
            ok = (xi >= 0) & (xi < N) & (yi >= 0) & (yi < N)
            tone[yi[ok], xi[ok]] = np.maximum(tone[yi[ok], xi[ok]], 0.22)
        bx_, by_, _, _ = project(np.zeros(60), np.full(60, -BAR), np.linspace(z[0] - 3, z[-1] + 3, 60))
        xi, yi = np.rint(bx_).astype(int), np.rint(by_).astype(int)
        ok = (xi >= 0) & (xi < N) & (yi >= 0) & (yi < N)
        tone[yi[ok], xi[ok]] = 0.4
        # the balls: shaded spheres, nearest wins
        light = np.array([-0.4, -0.7, -0.6], np.float32)
        light /= np.linalg.norm(light)
        cx, cy, cz, f = project(bx, by, z)
        for i in np.argsort(-cz):
            r = 3.4 * f[i]
            x0, x1 = max(0, int(cx[i] - r - 1)), min(N, int(cx[i] + r) + 2)
            y0, y1 = max(0, int(cy[i] - r - 1)), min(N, int(cy[i] + r) + 2)
            if x0 >= x1 or y0 >= y1:
                continue
            u = (X[y0:y1, x0:x1] - cx[i]) / r
            v = (Y[y0:y1, x0:x1] - cy[i]) / r
            q = 1 - u * u - v * v
            inside = q > 0
            w = np.sqrt(np.clip(q, 0, 1))
            dz = cz[i] - w * r
            front = inside & (dz < depth[y0:y1, x0:x1])
            shade = np.clip(u * light[0] + v * light[1] - w * light[2], 0, 1)
            hue = 0.45 + 0.4 * (i % 3) / 2                       # three ball tones, so the lines read
            val = hue * (0.25 + 0.7 * shade) + 0.4 * shade ** 14
            tone[y0:y1, x0:x1] = np.where(front, val, tone[y0:y1, x0:x1])
            depth[y0:y1, x0:x1] = np.where(front, dz, depth[y0:y1, x0:x1])
        return self.print(np.clip(tone, 0, 1))

    def lights(self):
        return [self.glow(0, 0.95, 0.2 + 0.2 * self.speed), self.glow(1, 0.55, 0.2 + 0.4 * self.view)] + self.ink_lights()
