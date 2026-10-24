"""Isobands: a flowing field cut into terraces of flat colour.

After Lee's 0531 posterized thermal gradient and 0519-1's contours. A smooth
field (sine waves, each bent by the others: a cheap domain warp) flows and
folds over time. It's cut into bands of equal height, each a flat colour from
the palette, stepping round it, so the field reads as a contour map in bold
colour. Inside each band a little shading runs from its low edge to its high
one, so the bands look like terraces, and a line marks each contour.
"""
import numpy as np

from ..draw import X, Y
from .original import Chromatic


class Isobands(Chromatic):
    name = "Isobands"
    blurb = "A flowing field cut into terraces of flat colour (after Lee's 0531). k0 bands, k1 warp, k2 flow speed, k3 colour. Click k0 contour lines, k1 hold still, k2 terraces, k3 next palette."
    palette = 1

    def __init__(self, rt):
        super().__init__(rt)
        self.bands, self.warp, self.speed = 9, 1.0, 1.0
        self.lines, self.terraces, self.still = True, True, False
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.bands = max(3, min(28, self.bands + (1 if d > 0 else -1)))
        elif k == 1:
            self.warp = max(0.0, min(3.0, self.warp + d * 0.08))
        elif k == 2:
            self.speed = max(0.0, min(4.0, self.speed + d * 0.1))
        else:
            self.turn_hue(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.lines = not self.lines
        elif k == 1:
            self.still = not self.still
        elif k == 2:
            self.terraces = not self.terraces
        elif k == 3:
            self.next_palette()

    def step(self, dt):
        self.hear(dt)
        if not self.still:
            self.t += dt * self.speed * (1 + self.sound[1])
        self.shift += dt * 0.01 * (1 + 3 * self.sound[0])        # the colours creep round on their own

    def field(self):
        t = self.t * 0.35
        u, v = X / 128 * 6, Y / 128 * 6
        w = self.warp * (1 + 0.6 * self.sound[2])
        qx = np.sin(v * 0.9 + t) + 0.5 * np.sin(u * 1.7 - t * 1.3)
        qy = np.cos(u * 1.1 - t * 0.8) + 0.5 * np.cos(v * 1.5 + t * 0.6)
        f = (np.sin(u * 0.8 + w * qx * 1.3 + t * 0.5) + np.cos(v * 0.7 + w * qy * 1.3 - t * 0.4)
             + 0.5 * np.sin((u + v) * 0.6 + w * (qx - qy) + t * 0.3))
        return (f + 2.5) / 5.0                                       # about 0..1

    def render(self):
        f = self.field() * self.bands
        band = np.floor(f)
        frac = f - band
        img = self.colour(band / self.bands)
        if self.terraces:                                            # each terrace shaded from its low edge up
            img = img * (0.72 + 0.28 * frac)[..., None]
        if self.lines:
            edge = (band != np.roll(band, 1, 0)) | (band != np.roll(band, 1, 1))
            img[edge] = img[edge] * 0.25
        return np.clip(img * (1 + 0.25 * self.beat), 0, 1)

    def lights(self):
        return [self.glow(0, 0.1, 0.1 + 0.025 * self.bands), self.glow(1, 0.75, 0.2 + 0.2 * self.warp),
                self.glow(2, 0.5, 0.2 + 0.15 * self.speed), self.hue_light()]
