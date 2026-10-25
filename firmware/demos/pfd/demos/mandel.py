"""Mandel: an endless dive into the Mandelbrot set, dithered.

After SeungHun's Retro Digital Tapestry. The view zooms in on one of a few deep
places on the set's edge (seahorse valley, an elephant, a spiral, a mini-brot),
about a million times, then eases back out and heads for the next. Each
pixel is iterated only until it escapes (the ones still inside are carried on
alone), and the escape count is smoothed, so the bands become a continuous
tone. That tone cycles slowly, so the bands flow inwards, and it all goes
through a dither screen onto the inks.
"""
import math
import time

import numpy as np

from ..draw import N
from ..io import log
from .original import Inked

# (centre re, centre im, deepest zoom) — the zoom is the half-width of the view
SPOTS = [(-0.743643887037151, 0.131825904205330, 2e-6), (0.2549870375144766, -0.0005679790528465, 4e-6),
         (-1.7685736562, 0.0017036751, 2e-6), (-0.1011, 0.9563, 3e-5), (-0.77568377, 0.13646737, 2e-6),
         (0.360240443437614, -0.641313061064803, 3e-6)]
DIVE_S = 26.0                   # seconds in, and the same back out
SLOW_S = 0.014                  # past this a frame (deep in, or a slower machine), iterate one pixel in four


class Mandel(Inked):
    name = "Mandel"
    blurb = "An endless dive into the Mandelbrot set, dithered (after SeungHun's Retro Digital Tapestry). k0 zoom (take over), k1 colour flow, k2 screen, k3 inks. Click k0 next place, k1 turn the view, k2 chunky."
    palette, screen_kind = "dusk", "bayer8"

    def __init__(self, rt):
        super().__init__(rt)
        self.spot = 0
        self.phase = 0.0                # 0..2: in, then out
        self.manual = None              # log zoom while a hand is on k0
        self.flow, self.cycle = 0.15, 0.0
        self.spin = 0.0
        self.turning = False
        self.res, self.cost = 1, 0.0
        self._grid()

    def _grid(self):
        c = (np.arange(N // self.res, dtype=np.float64) * self.res + (self.res - 1) / 2 - 63.5) / 64
        self.u, self.v = np.meshgrid(c, c)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            z = self.manual if self.manual is not None else math.log(self.zoom())
            self.manual = max(math.log(1e-13), min(math.log(2.0), z - d * 0.08))
        elif k == 1:
            self.flow = max(-1.0, min(1.0, self.flow + d * 0.02))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.spot = (self.spot + 1) % len(SPOTS)
            self.phase, self.manual = 0.0, None
        elif k == 1:
            self.turning = not self.turning
        elif k == 2:
            self.chunky()

    def zoom(self):
        deep = SPOTS[self.spot][2]
        p = self.phase if self.phase < 1 else 2 - self.phase
        e = p * p * (3 - 2 * p)
        return math.exp(math.log(1.6) + (math.log(deep) - math.log(1.6)) * e)

    def step(self, dt):
        self.hear(dt)
        if self.manual is not None and self.rt.t - self.t_touch[0] > 20:
            self.manual = None                  # hands off: back to the dive
        if self.manual is None:
            self.phase += dt / DIVE_S * (1 + 0.5 * self.sound[2])
            if self.phase >= 2 or self.on_phrase and self.phase > 1.6:
                self.phase = 0.0
                self.spot = (self.spot + 1) % len(SPOTS)
        self.cycle += dt * self.flow * (1 + 2 * self.sound[1])
        if self.turning:
            self.spin += dt * 0.12

    def render(self):
        t0 = time.perf_counter()
        zoom = math.exp(self.manual) if self.manual is not None else self.zoom()
        cr, ci, _ = SPOTS[self.spot]
        c, s = math.cos(self.spin), math.sin(self.spin)
        re = cr + (self.u * c - self.v * s) * zoom
        im = ci + (self.u * s + self.v * c) * zoom
        depth = -math.log10(zoom)
        iters = min(400, int(100 + 60 * max(0.0, depth)))
        c0 = (re + 1j * im).ravel()
        z = np.zeros_like(c0)
        out = np.full(c0.shape, -1.0)
        idx = np.arange(c0.size)
        saved, next_save = z.copy(), 8
        eps = 1e-14                        # |dz| under 1e-7: orbits settle well below this, escapes never do
        for i in range(iters):
            z = z * z + c0
            esc = (z.real * z.real + z.imag * z.imag) > 256.0
            if esc.any():
                zz = np.abs(z[esc])
                out[idx[esc]] = i + 1 - np.log2(np.log2(zz))     # the smooth count
            # Brent's periodicity check: an orbit back where it was at the last power of two is
            # caught in a cycle, so the point is in the set; stop iterating it
            d = z - saved
            cyc = (d.real * d.real + d.imag * d.imag) < eps
            gone = esc | cyc
            if gone.any():
                keep = ~gone
                z, c0, idx, saved = z[keep], c0[keep], idx[keep], saved[keep]
                if not idx.size:
                    break
            if i + 1 == next_save:
                saved, next_save = z.copy(), next_save * 2
        n = N // self.res
        out = out.reshape(n, n)
        if self.res > 1:
            out = out.repeat(self.res, 0).repeat(self.res, 1)
        inside = out < 0
        tone = 0.5 + 0.5 * np.sin(np.sqrt(np.maximum(out, 0)) * 1.9 - self.cycle * 6)
        tone = tone * (0.55 + 0.45 * np.clip(out / 40, 0, 1))          # dimmer far out, where little happens
        tone[inside] = 0.0
        self.cost += (time.perf_counter() - t0 - self.cost) * 0.05
        if self.cost > SLOW_S and self.res == 1 and self.rt.t > 2:
            self.res, self.cost = 2, self.cost / 4
            self._grid()
            log(f"mandel: over {SLOW_S * 1000:.0f} ms a frame, iterating at half resolution")
        elif self.res == 2 and self.cost * 4 < SLOW_S * 0.6:          # it'd be cheap again at full
            self.res, self.cost = 1, self.cost * 4
            self._grid()
        return self.print(np.clip(tone * (1 + 0.3 * self.beat), 0, 1))

    def lights(self):
        return [self.glow(0, (self.phase / 2) % 1), self.glow(1, 0.9, 0.2 + 0.3 * abs(self.flow))] + self.ink_lights()
