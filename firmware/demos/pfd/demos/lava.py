"""Lava: a lava lamp, wax blobs rising and sinking, merging and pinching apart.

After Lee's 0520, whose soft blobs drift in pink. Each blob carries a
temperature: the lamp's bulb heats it near the bottom, so it expands, grows
buoyant and rises; near the top it cools, grows heavy and sinks. Blobs stretch
along their motion, and the wax is drawn as metaballs, so blobs that meet
merge and part again with a neck between them. A pool of wax always sits on
the bottom. The field's slope shades each blob, lit from below, and the
liquid glows warmest over the bulb. Dithered.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

MAX_BLOBS = 10


class Lava(Inked):
    name = "Lava"
    blurb = "A lava lamp: blobs warm, rise, cool and sink, merging as they meet (after Lee's 0520). k0 heat, k1 how much wax, k2 screen, k3 inks. Click k0 shake, k2 chunky."
    palette, screen_kind = "dusk", "bayer8"

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = np.random.default_rng()
        self.heat, self.wax = 1.0, 6
        n = MAX_BLOBS
        self.p = np.column_stack([self.rng.uniform(30, 98, n), self.rng.uniform(20, 120, n)]).astype(np.float32)
        self.v = np.zeros((n, 2), np.float32)
        self.r = self.rng.uniform(8, 14, n).astype(np.float32)
        self.temp = self.rng.uniform(0, 1, n).astype(np.float32)
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.heat = max(0.2, min(3.0, self.heat * 1.07 ** d))
        elif k == 1:
            self.wax = max(2, min(MAX_BLOBS, self.wax + (1 if d > 0 else -1)))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.v += self.rng.normal(0, 25, self.v.shape).astype(np.float32)
        elif k == 2:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        dt = min(dt, 1 / 20)
        self.t += dt
        n = self.wax
        p, v, temp = self.p[:n], self.v[:n], self.temp[:n]
        # the bulb warms wax that sits over it, the cap cools wax that reaches it; between, wax
        # keeps its temperature, so a warm blob rises all the way and a cool one sinks all the way
        warm = p[:, 1] > 100
        cool = p[:, 1] < 34
        temp[warm] += (1 - temp[warm]) * (1 - math.exp(-dt * 0.5 * self.heat * (1 + self.sound[2])))
        temp[cool] += (0 - temp[cool]) * (1 - math.exp(-dt * 0.6))
        buoy = (temp - 0.45) * 36 * self.heat
        v[:, 1] += -buoy * dt                                       # warm rises (screen y is down)
        # blobs keep a little apart, and drift sideways a touch
        d = p[:, None, :] - p[None, :, :]
        dist = np.sqrt((d ** 2).sum(-1)) + 1e-3
        near = np.clip(1 - dist / (self.r[:n, None] + self.r[None, :n]), 0, None)
        np.fill_diagonal(near, 0)
        v += (d / dist[..., None] * near[..., None]).sum(1) * 30 * dt
        v[:, 0] += np.sin(self.t * 0.3 + np.arange(n) * 1.7) * 3 * dt
        v *= math.exp(-dt * 1.2)                                    # thick liquid
        p += v * dt
        # the glass: soft walls, a cap and the pool at the bottom
        for axis, lo, hi in ((0, 16, 112), (1, 10, 122)):
            out = (p[:, axis] < lo) | (p[:, axis] > hi)
            v[out, axis] *= -0.4
            np.clip(p[:, axis], lo, hi, out=p[:, axis])
        if self.on_beat and self.rt.audio.kick > 0.6:
            v[:, 1] -= 8 * self.sound[2]

    def field(self):
        """The wax: a sum of stretched metaball falloffs, plus the pool along the bottom."""
        n = self.wax
        f = np.zeros((N, N), np.float32)
        for (x, y), (vx, vy), r, tp in zip(self.p[:n], self.v[:n], self.r[:n], self.temp[:n]):
            stretch = 1 + min(0.8, abs(vy) / 25)                   # long when moving fast
            reach = 2.0 * r * (0.9 + 0.2 * tp)                     # warm wax is a little bigger
            x0, x1 = max(0, int(x - reach * 1.5)), min(N, int(x + reach * 1.5) + 1)
            y0, y1 = max(0, int(y - reach * 1.5)), min(N, int(y + reach * 1.5) + 1)
            if x0 >= x1 or y0 >= y1:
                continue
            dx = (X[y0:y1, x0:x1] - x) * math.sqrt(stretch)
            dy = (Y[y0:y1, x0:x1] - y) / math.sqrt(stretch)
            q = np.clip(1 - (dx * dx + dy * dy) / (reach * reach), 0, None)
            f[y0:y1, x0:x1] += q * q * q                           # compact: blobs only touch when close
        pool = 118 + 3 * np.sin(X * 0.08 + self.t * 0.5)
        f += np.clip((Y - pool) / 8 + 0.5, 0, 1) * 0.6
        return f

    def render(self):
        f = self.field()
        wax = np.clip((f - 0.25) / 0.08, 0, 1)                      # a soft edge at the iso-line
        gy = np.roll(f, -1, 0) - np.roll(f, 1, 0)                   # lit from below: undersides glow
        gx = np.roll(f, -1, 1) - np.roll(f, 1, 1)
        shade = np.clip(0.65 + 0.3 * np.tanh(-gy * 6) + 0.1 * np.tanh(gx * 6), 0, 1)
        liquid = 0.12 + 0.18 * np.exp(-((X - 64) / 50) ** 2) * np.clip((Y - 30) / 98, 0, 1) ** 1.5
        tone = liquid * (1 - wax) + wax * (0.55 + 0.45 * shade) * (1 + 0.15 * self.beat)
        return self.print(np.clip(tone, 0, 1))

    def lights(self):
        return [self.glow(0, 0.04, 0.2 + 0.2 * self.heat), self.glow(1, 0.9, 0.15 + 0.06 * self.wax)] + self.ink_lights()
