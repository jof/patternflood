"""A spectrum analyser that knows where it is in the music.

24 bands with peak caps that fall back slowly. Caps flash on the beat, the
palette steps round at each phrase boundary, and a drop sends a shockwave out
through the bars.

    k0  style: bars, mirrored, radial
    k1  colour: turn for hue; the phrase also steps it
    k2  fall: how fast bars and caps drop back
    k3  gain
"""
import math

import numpy as np

from .. import draw
from ..draw import N, hsv, hsv1
from ..runtime import Demo

STYLES = ["bars", "mirror", "radial"]


class Spectrum(Demo):
    name = "Spectrum"
    group = "audio"
    blurb = "Spectrum bars that know the beat: caps flash on it, colours step each phrase, drops shockwave. k0 style, k1 hue, k2 fall, k3 gain."

    def __init__(self, rt):
        super().__init__(rt)
        self.style = 0
        self.hue = 0.55
        self.fall = 1.0
        self.gain = 1.0
        self.v = np.zeros(24, np.float32)
        self.caps = np.zeros(24, np.float32)
        self.flash = 0.0
        self.shock = -1.0
        self.t_style = -10.0

    def turn(self, k, d):
        if k == 0:
            self.style = (self.style + (1 if d > 0 else -1)) % len(STYLES)
            self.t_style = self.rt.t
        elif k == 1:
            self.hue = (self.hue + d / 48) % 1.0
        elif k == 2:
            self.fall = min(4.0, max(0.25, self.fall * 1.15 ** d))
        elif k == 3:
            self.gain = min(4.0, max(0.25, self.gain * 1.1 ** d))

    def step(self, dt):
        a = self.rt.audio
        target = np.clip(np.asarray(a.bands, np.float32) * self.gain, 0, 1) ** 1.3
        rise = target > self.v
        self.v = np.where(rise, target, self.v - dt * 2.2 * self.fall)
        self.v = np.maximum(self.v, 0)
        self.caps = np.maximum(self.v, self.caps - dt * 0.5 * self.fall)
        if a.beat:
            self.flash = 1.0
        self.flash *= math.exp(-dt * 7)
        if a.phrase:
            self.hue = (self.hue + 0.137) % 1.0
        if a.drop or a.impact_hit:
            self.shock = 0.0
        if self.shock >= 0:
            self.shock += dt * 1.6
            if self.shock > 1.2:
                self.shock = -1.0

    def _colour(self, i, v):
        return hsv1(self.hue + i / 24 * 0.35 + v * 0.1, 0.85 - 0.3 * v, 0.35 + 0.65 * v)

    def render(self):
        img = draw.blank()
        a = self.rt.audio
        cap_col = np.array((1, 1, 1), np.float32) * (0.5 + 0.5 * self.flash)
        style = STYLES[self.style]
        if style in ("bars", "mirror"):
            w = N / 24
            for i in range(24):
                x0, x1 = int(i * w) + 1, int((i + 1) * w)
                if style == "bars":
                    h = int(self.v[i] * 118)
                    img[126 - h:126, x0:x1] = self._colour(i, self.v[i])
                    cy = 125 - int(self.caps[i] * 118)
                    img[max(0, cy - 1):cy + 1, x0:x1] = cap_col
                else:
                    h = int(self.v[i] * 60)
                    img[64 - h:64 + h, x0:x1] = self._colour(i, self.v[i])
                    c = int(self.caps[i] * 60)
                    img[max(0, 63 - c):64 - c, x0:x1] = cap_col
                    img[64 + c:min(N, 65 + c), x0:x1] = cap_col
        else:
            r0 = 14 + 6 * a.bass
            ang = np.arctan2(draw.Y - 63.5, draw.X - 63.5)
            rad = np.hypot(draw.X - 63.5, draw.Y - 63.5)
            # 48 spokes: the 24 bands mirrored, turning slowly with the bar
            k = ((ang / (2 * np.pi) + 0.5 + a.bar_phase * 0.25) * 48).astype(int) % 48
            band = np.where(k < 24, k, 47 - k)
            reach = r0 + self.v[band] * 48
            m = (rad >= r0) & (rad <= reach)
            cols = hsv(self.hue + band / 24 * 0.35, np.full(band.shape, 0.8), 0.35 + 0.65 * self.v[band])
            img[m] = cols[m]
            capr = r0 + self.caps[band] * 48
            img[np.abs(rad - capr) < 0.8] = cap_col
            draw.disc(img, 63.5, 63.5, r0 - 3, hsv1(self.hue + 0.5, 0.6, 0.2 + 0.6 * self.flash), soft=1)
        if self.shock >= 0:
            rad = np.hypot(draw.X - 63.5, draw.Y - (126 if style == "bars" else 63.5))
            ring = np.clip(1 - np.abs(rad - self.shock * 120) / 6, 0, 1) * (1.2 - self.shock)
            img += ring[..., None] * np.array(hsv1(self.hue + 0.5, 0.5, 1.0), np.float32)
        if self.rt.t - self.t_style < 1.0:
            draw.text(img, style, 64, 2, (.8, .8, .8), center=True)
        return img

    def lights(self):
        a = self.rt.audio
        return [hsv1(self.hue, .8, .3 + .7 * a.bass), hsv1(self.hue + .1, .8, .3 + .7 * a.mid),
                hsv1(self.hue + .2, .8, .3 + .7 * a.treble), tuple(.15 + .85 * self.flash * c for c in (1, 1, 1))]
