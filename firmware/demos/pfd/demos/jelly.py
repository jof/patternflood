"""Jellyfish: glowing jellies pulsing up through the deep, dithered.

After SeungHun's 0529, its glowing curves on black. Each jelly is a bell that
pulses: it squeezes (narrower, taller) and shoves itself upward, then
relaxes and drifts, sinking a little, so they climb in fits. Their tentacles
trail behind as chains that follow the bell with a lag, each link easing
after the one before, so they ripple and stream. The bells are translucent,
brightest at the rim, with a glowing core. Motes of marine snow drift past.
Dithered into deep-sea inks.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

NJ = 5
LINKS = 16
TENTACLES = 5
NSNOW = 60


class Jelly(Inked):
    name = "Jellyfish"
    blurb = "Glowing jellyfish pulsing up through the deep, dithered (after SeungHun's 0529). k0 pulse rate, k1 current, k2 screen, k3 inks. Click k0 all pulse at once, k2 chunky."
    palette, screen_kind = "ice", "blue"

    def __init__(self, rt):
        super().__init__(rt)
        rng = self.rng = np.random.default_rng()
        xs = (np.arange(NJ) + 0.5) / NJ * 108 + 10 + rng.uniform(-6, 6, NJ)          # spread out across
        ys = rng.permutation((np.arange(NJ) + 0.5) / NJ * 150)            # staggered heights
        self.pos = np.column_stack([xs, ys]).astype(np.float32)
        self.vel = np.zeros((NJ, 2), np.float32)
        self.size = rng.uniform(8, 15, NJ).astype(np.float32)
        self.phase = rng.uniform(0, 1, NJ).astype(np.float32)
        self.rate_j = rng.uniform(0.7, 1.2, NJ).astype(np.float32)
        self.tent = np.repeat(self.pos[:, None, None, :], TENTACLES, 1).repeat(LINKS, 2)    # (NJ, T, L, 2)
        self.snow = np.column_stack([rng.uniform(0, N, NSNOW), rng.uniform(0, N, NSNOW), rng.uniform(0.2, 1, NSNOW)]).astype(np.float32)
        self.rate, self.current = 0.5, 0.0
        self.t = 0.0

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.rate = max(0.15, min(2.0, self.rate * 1.07 ** d))
        elif k == 1:
            self.current = max(-20.0, min(20.0, self.current + d))
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.phase[:] = 0.0
        elif k == 2:
            self.chunky()

    def squeeze(self):
        """How contracted each bell is, 0..1: a quick squeeze, a slow release."""
        p = self.phase
        return np.where(p < 0.25, np.sin(p / 0.25 * math.pi / 2), np.cos((p - 0.25) / 0.75 * math.pi / 2) ** 2)

    def step(self, dt):
        self.hear(dt)
        dt = min(dt, 1 / 20)
        self.t += dt
        before = self.phase.copy()
        self.phase = (self.phase + dt * self.rate * self.rate_j * (1 + self.sound[1])) % 1
        if self.on_beat and self.rt.audio.kick > 0.6:
            self.phase[self.rng.integers(0, NJ)] = 0.0
        kick = (self.phase < before) | (self.phase < 0.25)      # the squeeze drives them up
        self.vel[:, 1] -= np.where(kick, 40, 0) * dt           # net: a slow climb, a few pixels a second
        self.vel[:, 1] += 5.0 * dt                              # they sink when they rest
        self.vel[:, 0] += (self.current + 4 * np.sin(self.t * 0.3 + np.arange(NJ) * 2)) * dt * 0.5
        dx = self.pos[:, None, 0] - self.pos[None, :, 0]            # they keep a little apart, side to side
        near = np.exp(-np.abs(dx) / 14) * np.sign(dx)
        np.fill_diagonal(near, 0)
        self.vel[:, 0] += near.sum(1) * 10 * dt
        self.vel *= math.exp(-dt * 1.4)
        self.pos += self.vel * dt
        gone = self.pos[:, 1] < -30                             # off the top: back in from below
        self.pos[gone, 1] = N + 16
        self.pos[gone, 0] = self.rng.uniform(20, 108, gone.sum())
        wrapped = (self.pos[:, 0] + 20) % (N + 40) - 20
        self.tent[:, :, :, 0] += (wrapped - self.pos[:, 0])[:, None, None]    # the tentacles come round too
        self.pos[:, 0] = wrapped
        low = self.pos[:, 1] > N - 12                           # sunk too far: swim for it
        self.vel[low, 1] -= 20 * dt
        # tentacles: the first link hangs from the bell's rim, each next one eases after its leader
        sq = self.squeeze()
        w = self.size * (1 - 0.3 * sq)                                   # (NJ,)
        across = (np.arange(TENTACLES) / (TENTACLES - 1) - 0.5) * 1.6      # (T,)
        root = np.stack([self.pos[:, None, 0] + across[None, :] * w[:, None],
                         np.repeat(self.pos[:, None, 1] + 0.2 * self.size[:, None], TENTACLES, 1)], -1)
        self.tent[gone] = root[gone][:, :, None, :]
        lead = root
        ease = min(1.0, dt * 14)
        for i in range(LINKS):
            sway = 0.6 * np.sin(self.t * 2 + i * 0.5 + np.arange(TENTACLES))[None, :]
            want = lead + np.stack([np.broadcast_to(sway, lead.shape[:2]), np.full(lead.shape[:2], 2.2)], -1)
            self.tent[:, :, i] += (want - self.tent[:, :, i]) * ease
            lead = self.tent[:, :, i]
        self.snow[:, 1] -= dt * 4 * self.snow[:, 2]
        self.snow[:, 0] += dt * self.current * 0.3
        self.snow[:, :2] %= N

    def render(self):
        tone = (0.03 + 0.05 * np.clip(1 - Y / 100, 0, 1)).astype(np.float32)     # a little light from above
        sx, sy, sb = self.snow.T
        tone[sy.astype(int) % N, sx.astype(int) % N] += 0.25 * sb
        sq = self.squeeze()
        for j in np.argsort(self.size):                         # small (far) ones first
            x, y = self.pos[j]
            s = self.size[j]
            w, h = s * (1 - 0.3 * sq[j]), s * (0.75 + 0.35 * sq[j])
            # tentacles, faint
            pts = self.tent[j].reshape(-1, 2)
            xi, yi = np.rint(pts[:, 0]).astype(int), np.rint(pts[:, 1]).astype(int)
            ok = (xi >= 0) & (xi < N) & (yi >= 0) & (yi < N)
            fade = np.tile(np.linspace(0.85, 0.25, LINKS), TENTACLES)[ok]
            np.maximum.at(tone, (yi[ok], xi[ok]), fade * (0.7 + 0.3 * sq[j]))
            # the bell: a half-ellipse dome, glowing at the rim, a bright core inside
            x0, x1 = max(0, int(x - w - 2)), min(N, int(x + w) + 3)
            y0, y1 = max(0, int(y - h - 2)), min(N, int(y + 0.4 * s) + 3)
            if x0 >= x1 or y0 >= y1:
                continue
            u = (X[y0:y1, x0:x1] - x) / w
            v = (Y[y0:y1, x0:x1] - y) / h
            r = np.sqrt(u * u + np.where(v < 0, v * v, (v * 2.5) ** 2))
            inside = r < 1
            rim = np.exp(-((r - 0.92) / 0.09) ** 2)
            body = 0.25 + 0.2 * (1 - r)
            core = np.exp(-(u * u + (v + 0.35) ** 2) / 0.06) * 0.6
            frill = (v > 0) & (v < 0.45) & (np.sin(u * 14 + self.t * 5) > 0.3) & (np.abs(u) < 1)
            bell = np.where(inside, np.maximum(body + core, rim), rim * (r < 1.15)) + 0.4 * frill
            glow = 0.85 + 0.35 * sq[j] + 0.3 * self.beat
            tone[y0:y1, x0:x1] = np.maximum(tone[y0:y1, x0:x1], bell * glow * (0.6 + 0.04 * s))
        return self.print(np.clip(tone, 0, 1))

    def lights(self):
        return [self.glow(0, 0.55, 0.2 + 0.3 * self.rate), self.glow(1, 0.5, 0.2 + 0.02 * abs(self.current))] + self.ink_lights()
