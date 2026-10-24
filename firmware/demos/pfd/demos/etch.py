"""Light painter: the Etch A Sketch, with a colour knob, mirrors, and a shake."""
import math

import numpy as np

from .. import draw
from ..draw import N, hsv1
from ..runtime import Demo


class Etch(Demo):
    name = "Etch"
    blurb = "k0 left-right, k1 up-down, k2 colour, k3 brush. Click k0/k1 mirror, k2 rainbow, k3 shake clear. Hold k3 + turn: fade."

    def __init__(self, rt):
        super().__init__(rt)
        self.canvas = draw.blank()
        self.x = self.y = N / 2 - 0.5
        self.hue, self.size = 0.0, 1.2
        self.mirror_x = self.mirror_y = False
        self.rainbow = False
        self.fade = 0.0                 # per-second trail decay; 0 keeps the drawing
        self.shake = 0.0                # seconds of shake-clear left
        self.t_moved = -10.0

    def turn(self, k, d):
        if k in (0, 1):
            step = self.rt.accel(k, d)
            x0, y0 = self.x, self.y
            if k == 0:
                self.x = min(N - 1.0, max(0.0, self.x + step))
            else:
                self.y = min(N - 1.0, max(0.0, self.y - step))      # clockwise draws upwards, as on the toy
            self._stroke(x0, y0, self.x, self.y)
            self.t_moved = self.rt.t
        elif k == 2:
            self.hue = (self.hue + d / 36.0) % 1.0
        elif k == 3:
            if self.rt.held(3):
                self.fade = min(3.0, max(0.0, self.fade + d * 0.05))
            else:
                self.size = min(8.0, max(0.6, self.size * (1.12 ** d)))

    def release(self, k, click):
        if not click:
            return
        if k == 0:
            self.mirror_x = not self.mirror_x
        elif k == 1:
            self.mirror_y = not self.mirror_y
        elif k == 2:
            self.rainbow = not self.rainbow
        elif k == 3:
            self.shake = 0.8

    def _stroke(self, x0, y0, x1, y1):
        xs, ys = draw.segment(x0, y0, x1, y1, step=max(0.4, self.size / 2))
        for x, y in zip(xs, ys):
            if self.rainbow:
                self.hue = (self.hue + 0.004) % 1.0
            c = hsv1(self.hue)
            for mx, my in self._mirrors(x, y):
                draw.disc(self.canvas, mx, my, self.size - 0.5, c, soft=0.6)

    def _mirrors(self, x, y):
        pts = [(x, y)]
        if self.mirror_x:
            pts += [(N - 1 - px, py) for px, py in pts]
        if self.mirror_y:
            pts += [(px, N - 1 - py) for px, py in pts]
        return pts

    def step(self, dt):
        if self.fade:
            self.canvas *= math.exp(-self.fade * dt)
        if self.shake > 0:
            self.shake -= dt
            # grains of light slide down and dim as the toy is shaken
            self.canvas[1:] = np.maximum(self.canvas[1:] * 0.9, self.canvas[:-1] * 0.75)
            self.canvas *= 0.88
            if self.shake <= 0:
                self.canvas[:] = 0

    def render(self):
        img = self.canvas.copy()
        if self.shake > 0:
            img = np.roll(img, int(3 * math.sin(self.rt.t * 60)), axis=1)
        # the pen: a pulsing ring, steady while moving so it's easy to follow
        idle = self.rt.t - self.t_moved
        pulse = 1.0 if idle < 0.5 else 0.55 + 0.45 * math.sin(self.rt.t * 6)
        for mx, my in self._mirrors(self.x, self.y):
            draw.disc(img, mx, my, max(0.0, self.size - 0.5), hsv1(self.hue), soft=0.6)
            draw.ring(img, mx, my, self.size + 1.5, (pulse,) * 3)
        return img

    def lights(self):
        c = hsv1(self.hue)
        return [(1, 1, 1) if self.mirror_x else tuple(0.5 * v for v in c),
                (1, 1, 1) if self.mirror_y else tuple(0.5 * v for v in c),
                hsv1(self.rt.t * 0.5) if self.rainbow else c,
                (1, 0.3, 0.1) if self.rt.held(3) else (0.15 + 0.1 * self.size,) * 3]
