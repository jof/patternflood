"""Tesla: a plasma globe. Filaments crackle from the electrode out to the glass.

After SeungHun's MagVortex, its lines bursting from a centre. Each filament is a
jagged path from the electrode to the glass: a straight line bent sideways
by a few octaves of wiggle that swell in the middle and pin at both ends,
re-drawn every frame so it writhes, with a fork or two off it. The far ends
wander over the glass. Touch the glass (hold k0) and every filament leaps to
your fingertip, as on the real thing; turn k0 to move the finger round. The
filaments glow, the electrode burns, the glass catches a faint rim, and it
all goes through a dither screen.
"""
import math

import numpy as np

from ..draw import N, X, Y
from ..runtime import DETENTS_PER_REV
from .original import Inked

R_GLASS = 58.0
R_CORE = 9.0
STEPS = 70                      # points along each filament


def _blur(a):
    a = (np.roll(a, 1, 0) + 2 * a + np.roll(a, -1, 0)) / 4
    return (np.roll(a, 1, 1) + 2 * a + np.roll(a, -1, 1)) / 4


class Tesla(Inked):
    name = "Tesla"
    blurb = "A plasma globe, dithered (after SeungHun's MagVortex). k0 moves your finger round the glass (hold it to touch), k1 filaments, k2 screen, k3 inks. Click k1 forks, k2 chunky."
    palette, screen_kind = "nebula", "bayer4"

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.count = 9
        self.forks = True
        self.finger = -math.pi / 2
        self.touching = 0.0
        self.ends = self.rng.uniform(0, 2 * math.pi, 16).astype(np.float32)
        self.drift = self.rng.normal(0, 0.3, 16).astype(np.float32)
        self.t = 0.0
        self.glow_img = np.zeros((N, N), np.float32)

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.finger += d * 2 * math.pi / DETENTS_PER_REV
        elif k == 1:
            self.count = max(3, min(16, self.count + (1 if d > 0 else -1)))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 1:
            self.forks = not self.forks
        elif k == 2:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        self.t += dt
        held = self.rt.held(0) or (self.listening and self.rt.audio.kick > 0.7)
        self.touching += ((1.0 if held else 0.0) - self.touching) * (1 - math.exp(-dt / (0.08 if held else 0.4)))
        # the ends wander over the glass, pushing apart a little
        self.drift += self.rng.normal(0, 1.2, 16).astype(np.float32) * dt
        self.drift *= math.exp(-dt * 0.8)
        e = self.ends[:self.count]
        diff = (e[:, None] - e[None, :] + math.pi) % (2 * math.pi) - math.pi
        push = np.sign(diff) * np.exp(-np.abs(diff) / 0.35)
        np.fill_diagonal(push, 0)
        self.ends[:self.count] += (self.drift[:self.count] * (1 + 2 * self.sound[0]) + push.sum(1) * 0.6) * dt
        if self.rt.t - self.t_touch[0] > 20:            # left alone, a ghost finger visits now and then
            self.touching = max(self.touching, max(0.0, math.sin(self.rt.t * 0.15)) ** 8)
            self.finger += dt * 0.2

    def filament(self, a0, a1, seed, wild=1.0):
        """Points of one filament from the electrode at angle a0 to the glass at angle a1."""
        s = np.linspace(0, 1, STEPS, dtype=np.float32)
        x0, y0 = 63.5 + R_CORE * math.cos(a0), 63.5 + R_CORE * math.sin(a0)
        x1, y1 = 63.5 + R_GLASS * math.cos(a1), 63.5 + R_GLASS * math.sin(a1)
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy) + 1e-6
        nx, ny = -dy / ln, dx / ln
        off = np.zeros_like(s)
        t = self.t
        for o, (f, amp, sp) in enumerate(((1.5, 6, 2.0), (4, 3, 5.0), (11, 1.4, 11.0), (27, 0.7, 23.0))):
            off += amp * np.sin(s * f * math.pi + t * sp + seed * (o + 1) * 1.7) * \
                np.sin(s * f * 0.37 + t * sp * 0.61 + seed * 2.3)
        off *= np.sin(s * math.pi) * wild * (1 + 0.6 * self.sound[3])
        return x0 + dx * s + nx * off, y0 + dy * s + ny * off

    def render(self):
        img = np.zeros((N, N), np.float32)
        for i in range(self.count):
            a1 = float(self.ends[i])
            if self.touching > 0.01:                    # the finger draws them in
                d = (self.finger - a1 + math.pi) % (2 * math.pi) - math.pi
                a1 += d * self.touching * 0.95
            a0 = a1 + 0.3 * math.sin(self.t * 0.7 + i)
            xs, ys = self.filament(a0, a1, i)
            bright = 0.7 + 0.3 * math.sin(self.t * 9 + i * 2.1) * math.sin(self.t * 5.3 + i)
            _plot(img, xs, ys, bright)
            if self.forks and (i + int(self.t * 3)) % 3 == 0:                   # a fork, flickering on and off
                k = STEPS // 2 + (i * 7) % (STEPS // 3)
                ang = math.atan2(ys[k] - 63.5, xs[k] - 63.5) + (0.5 if i % 2 else -0.5)
                fx, fy = self.filament(ang, ang + 0.25 * (1 if i % 2 else -1), i + 50, 0.5)
                cut = k // 2
                sx = xs[k] + (fx[cut:] - fx[cut]) * 0.6
                sy = ys[k] + (fy[cut:] - fy[cut]) * 0.6
                _plot(img, sx, sy, bright * 0.6)
        # the filaments' glow lingers a moment (persistence of vision, and of plasma)
        self.glow_img = np.maximum(self.glow_img * 0.55, _blur(_blur(img)) * 1.6)
        r = np.hypot(X - 63.5, Y - 63.5)
        core = np.exp(-np.maximum(r - R_CORE * 0.6, 0) / 3.0) * (0.9 + 0.1 * math.sin(self.t * 13))
        rim = np.exp(-((r - R_GLASS - 1.5) / 1.4) ** 2) * 0.22
        spot = 0.0
        if self.touching > 0.05:                        # where the finger meets the glass, it blazes
            fx, fy = 63.5 + R_GLASS * math.cos(self.finger), 63.5 + R_GLASS * math.sin(self.finger)
            spot = np.exp(-((X - fx) ** 2 + (Y - fy) ** 2) / 18) * self.touching
        tone = np.maximum.reduce([img * 0.95, self.glow_img * 0.55, core, rim + 0.04 * (r < R_GLASS)])
        tone = np.maximum(tone, spot)
        return self.print(np.clip(tone * (1 + 0.3 * self.beat), 0, 1))

    def lights(self):
        return [self.glow(0, 0.85, 0.3 + 0.7 * self.touching), self.glow(1, 0.75, 0.1 + 0.04 * self.count)] + self.ink_lights()


def _plot(img, xs, ys, v):
    """Light single pixels of img (N, N) at (xs, ys) to at least v; off-screen points are skipped."""
    xi, yi = np.rint(xs).astype(np.int32), np.rint(ys).astype(np.int32)
    ok = (xi >= 0) & (xi < N) & (yi >= 0) & (yi < N)
    np.maximum.at(img, (yi[ok], xi[ok]), v)
