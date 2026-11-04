"""Pendulums: the pendulum wave, a row of swinging balls falling in and out of step.

After SeungHun's Wave Saw. Eighteen pendulums hang from one bar; their lengths are
chosen so that, in one cycle of the dance, the first swings 51 times, the
next 52, and so on. Released together they make a travelling snake, then two
interleaved lines, three, a scatter, and at the end of the cycle they all line
up again. We look down the row a little from above and in perspective, so the
pattern reads as waves running away from us. The balls are shaded spheres
that pass in front of and behind one another properly, lit by a lamp in the
room up and to the left: each ball sees it from its own side, the ones nearer
it are brighter, its glint sits where the lamp would really show in the ball,
and a ball that comes between another and the lamp shades it.
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
BALL = 3.4                      # the balls' radius
LAMP = (-34.0, -62.0, 16.0)     # a bulb in the room: left of the row, above the bar, a little way down it
REACH = 78.0                    # the lamp's light is as given this far from it, and falls off as 1/d^2


class Pendulums(Inked):
    name = "Pendulums"
    blurb = "The pendulum wave: a row of pendulums falling in and out of step (after SeungHun's Wave Saw). k0 speed, k1 view, k2 screen, k3 inks. Click k0 release them together, k2 chunky."
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
        # the balls: shaded spheres, nearest wins, lit by the lamp. Everything below is in the
        # camera's frame, the eye at the origin looking along +z (screen x right, y down)
        def to_eye(x, y, zz):
            return np.stack([x, y * cv - zz * sv + 34, y * sv + zz * cv + 70], -1)
        cx, cy, cz, f = project(bx, by, z)
        centre = to_eye(bx, by, z)                                  # (COUNT, 3)
        lamp = to_eye(*(np.float64(c) for c in LAMP))
        # which balls can shade which: j can only reach i's surface if the line from i's centre to
        # the lamp passes within two radii (and a little) of j's centre, on the way
        dl = lamp - centre
        dl /= np.linalg.norm(dl, axis=-1, keepdims=True)
        oc = centre[None, :] - centre[:, None]                      # [i, j]: from i to j
        along = (oc * dl[:, None]).sum(-1)
        miss = np.sqrt(np.maximum((oc * oc).sum(-1) - along ** 2, 0))
        casts = (along > -2 * BALL) & (miss < 2.3 * BALL)       # neighbours overlap: the row is tighter than the balls
        np.fill_diagonal(casts, False)
        for i in np.argsort(-cz):
            r = BALL * f[i]
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
            if not front.any():
                continue
            nrm = np.stack([u, v, -w], -1)                          # the surface's normal, facing us
            pt = centre[i] + BALL * nrm                             # the surface point
            to_l = lamp - pt
            dist = np.linalg.norm(to_l, axis=-1)
            l = to_l / dist[..., None]
            diffuse = np.clip((nrm * l).sum(-1), 0, 1)
            eye = -pt / np.linalg.norm(pt, axis=-1, keepdims=True)
            half = l + eye
            half /= np.linalg.norm(half, axis=-1, keepdims=True)
            glint = np.clip((nrm * half).sum(-1), 0, 1) ** 60
            fall = np.minimum((REACH / dist) ** 2, 2.0)
            # the other balls' shadows: how near does the ray to the lamp pass each one? A soft
            # edge, as the bulb isn't a point
            lit = np.ones_like(dist)
            for j in np.flatnonzero(casts[i]):
                oc = centre[j] - pt
                along = (oc * l).sum(-1)
                miss = np.sqrt(np.maximum((oc * oc).sum(-1) - along ** 2, 0))
                shade = np.clip((miss - 0.7 * BALL) / (0.6 * BALL), 0, 1)
                lit = np.minimum(lit, np.where((along > 0) & (along < dist), shade, 1))
            light = fall * lit
            hue = 0.45 + 0.4 * (i % 3) / 2                       # three ball tones, so the lines read
            val = hue * (0.14 + 0.85 * diffuse * light) + 0.5 * glint * light
            tone[y0:y1, x0:x1] = np.where(front, val, tone[y0:y1, x0:x1])
            depth[y0:y1, x0:x1] = np.where(front, dz, depth[y0:y1, x0:x1])
        return self.print(np.clip(tone, 0, 1))

    def lights(self):
        return [self.glow(0, 0.95, 0.2 + 0.2 * self.speed), self.glow(1, 0.55, 0.2 + 0.4 * self.view)] + self.ink_lights()
