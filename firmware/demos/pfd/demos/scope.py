"""An oscilloscope with phosphor: the music's own waveform, drawn and left to glow.

XY mode plots left against right, turned so mono runs straight up and stereo
width spreads sideways, as a goniometer does. Circle wraps the waveform round
a ring that breathes with the bass. Wave is the plain trace, triggered on a
rising zero so it stands still on steady tones. The beat brightens the trace,
and each bar nudges the hue.

    k0  mode: xy, circle, wave
    k1  persistence
    k2  gain
    k3  hue
"""
import math

import numpy as np

from .. import draw
from ..draw import N, hsv1
from ..runtime import Demo

MODES = ["xy", "circle", "wave"]


class Scope(Demo):
    name = "Scope"
    group = "audio"
    blurb = "An oscilloscope with phosphor glow: stereo XY, circle, or wave. k0 mode, k1 persistence, k2 gain, k3 hue."

    def __init__(self, rt):
        super().__init__(rt)
        self.mode = 1                   # circle: reads well even on a mostly mono mix
        self.persist = 0.8
        self.gain = 1.5
        self.hue = 0.33
        self.phos = draw.blank()
        self.t_mode = -10.0
        self.peak = 0.05

    def turn(self, k, d):
        if k == 0:
            self.mode = (self.mode + (1 if d > 0 else -1)) % len(MODES)
            self.t_mode = self.rt.t
        elif k == 1:
            self.persist = min(0.97, max(0.3, self.persist + d * 0.02))
        elif k == 2:
            self.gain = min(8.0, max(0.25, self.gain * 1.1 ** d))
        elif k == 3:
            self.hue = (self.hue + d / 48) % 1.0

    def step(self, dt):
        a = self.rt.audio
        self.phos *= self.persist ** (dt * 60)
        if a.bar:
            self.hue = (self.hue + 0.03) % 1.0
        w = np.asarray(a.wave, np.float32)
        self.peak = max(float(np.abs(w).max()), self.peak * 0.995, 0.02)
        w = w / self.peak * 0.9 * self.gain / 1.5
        bright = 0.55 + 0.45 * math.exp(-a.phase * 5)
        col = np.array(hsv1(self.hue + 0.15 * a.treble, 0.7, 1.0), np.float32) * bright
        mode = MODES[self.mode]
        if mode == "xy":
            side = (w[:, 0] - w[:, 1]) * 0.7071
            mid = (w[:, 0] + w[:, 1]) * 0.7071
            xs, ys = 63.5 + side * 58, 63.5 - mid * 58
        elif mode == "circle":
            m = w.mean(1)
            th = np.linspace(0, 2 * np.pi, len(m), endpoint=False)
            r = 34 + 12 * a.bass + m * 22
            xs, ys = 63.5 + r * np.cos(th), 63.5 + r * np.sin(th)
        else:
            m = w.mean(1)
            z = np.nonzero((m[:-1] < 0) & (m[1:] >= 0))[0]           # trigger on a rising zero
            start = int(z[0]) if len(z) and z[0] < len(m) - 512 else 0
            seg = m[start:start + 512]
            xs = np.linspace(0, N - 1, len(seg))
            ys = 63.5 - seg * 58
        # join the dots so fast swings stay continuous
        xs2 = np.concatenate([xs, xs[1:] * 0.5 + xs[:-1] * 0.5])
        ys2 = np.concatenate([ys, ys[1:] * 0.5 + ys[:-1] * 0.5])
        draw.plot(self.phos, xs2, ys2, col * 0.35, op="add")

    def render(self):
        img = np.clip(self.phos, 0, 1)
        glow = (np.roll(img, 1, 0) + np.roll(img, -1, 0) + np.roll(img, 1, 1) + np.roll(img, -1, 1)) * 0.08
        img = img + glow
        img[63, ::4] = np.maximum(img[63, ::4], 0.05)                # the graticule, faintly
        img[::4, 63] = np.maximum(img[::4, 63], 0.05)
        if self.rt.t - self.t_mode < 1.0:
            draw.text(img, MODES[self.mode], 64, 2, (.8, .8, .8), center=True)
        return img

    def lights(self):
        a = self.rt.audio
        c = hsv1(self.hue, .7, .3 + .7 * a.level)
        return [c, (self.persist * .6,) * 3, (min(1, self.gain / 4),) * 3, hsv1(self.hue)]
