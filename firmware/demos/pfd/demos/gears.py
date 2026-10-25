"""Gears: a clockwork train of meshing gears, engraved.

After SeungHun's Origin, its tiles of rings. Gears of one tooth size are laid out
in a chain, each touching the last, so their teeth mesh: a gear with fewer
teeth turns faster, every neighbour turns the other way, and each is set at
the angle that slots its teeth into its neighbour's gaps. They're drawn from
their outlines in polar form (rim, teeth, spokes cut out, an axle), lit as
bevelled brass, and printed by default with the cross-hatch screen, like an
old engraving. With the music on, the train ticks forward a step on each beat,
like an escapement.
"""
import math

import numpy as np

from ..draw import N, X, Y
from .original import Inked

MODULE = 2.6                    # pitch radius per tooth: every gear meshes with every other


class Gears(Inked):
    name = "Gears"
    blurb = "A clockwork train of meshing gears, engraved (after SeungHun's Origin). k0 crank speed, k1 a new train, k2 screen, k3 inks. Click k0 reverse, k2 chunky."
    palette, screen_kind = "obra", "hatch"

    def __init__(self, rt):
        super().__init__(rt)
        self.seed = 4
        self.speed, self.dir = 0.4, 1
        self.angle = 0.0
        self.tick = 0.0
        self.layout()

    def layout(self):
        """A chain of gears from the middle outwards, each placed against the last at a free angle."""
        rng = np.random.default_rng(self.seed % 100000)      # k1 turns it either way; seeds must be >= 0
        gears = []                                       # (x, y, teeth, ratio, phase)
        teeth = int(rng.integers(14, 22))
        gears.append((64.0, 64.0, teeth, 1.0, 0.0))
        tries = 0
        while len(gears) < 7 and tries < 300:
            tries += 1
            px, py, pn, pratio, pphase = gears[int(rng.integers(len(gears)))]
            n = int(rng.integers(8, 26))
            a = rng.uniform(0, 2 * math.pi)
            dist = MODULE * (pn + n) / 2
            x, y = px + math.cos(a) * dist, py + math.sin(a) * dist
            r = MODULE * n / 2 + MODULE
            if not (-r * 0.4 < x < N + r * 0.4 and -r * 0.4 < y < N + r * 0.4):
                continue
            if any(math.hypot(x - gx, y - gy) < MODULE * (n + gn) / 2 + MODULE * 1.5
                   for gx, gy, gn, _, _ in gears if (gx, gy) != (px, py)):
                continue
            ratio = -pratio * pn / n
            # mesh: rotate so a gap of this gear faces a tooth of its neighbour along the line of centres
            phase = (pphase - a) * (-pn / n) + a + math.pi + math.pi / n
            gears.append((x, y, n, ratio, phase))
        self.gears = gears

    def turn(self, k, d):
        self.touch(k)
        if k == 0:
            self.speed = max(0.0, min(3.0, self.speed + d * 0.05))
        elif k == 1:
            self.seed += 1 if d > 0 else -1
            self.layout()
        else:
            self.turn_ink(k, d)

    def release(self, k, click):
        if not click:
            return
        self.touch(k)
        if k == 0:
            self.dir = -self.dir
        elif k == 2:
            self.chunky()

    def step(self, dt):
        self.hear(dt)
        if self.listening:                               # an escapement: a quick step on each beat
            if self.on_beat:
                self.tick = 1.0
            step = self.tick * (1 - math.exp(-dt / 0.06))
            self.tick -= step
            self.angle += step * 0.35 * self.dir
        else:
            self.angle += dt * self.speed * self.dir
        if self.on_phrase:
            self.seed += 1
            self.layout()
        if self.rt.t - self.t_touch[1] > 40 and int(self.rt.t / 40) != int((self.rt.t - dt) / 40):
            self.seed += 1
            self.layout()

    def render(self):
        tone = np.full((N, N), 0.06, np.float32)                       # a dim back plate
        tone += 0.05 * ((X + Y) % 9 < 1)                               # with a ruled texture
        light = (-0.6, -0.8)
        for gi, (x, y, n, ratio, phase) in enumerate(self.gears):
            pitch = MODULE * n / 2
            reach = pitch + MODULE * 1.2
            x0, x1 = max(0, int(x - reach)), min(N, int(x + reach) + 2)
            y0, y1 = max(0, int(y - reach)), min(N, int(y + reach) + 2)
            if x0 >= x1 or y0 >= y1:
                continue
            dx, dy = X[y0:y1, x0:x1] - x, Y[y0:y1, x0:x1] - y
            r = np.hypot(dx, dy)
            th = np.arctan2(dy, dx) - (self.angle * ratio + phase)
            tooth = np.clip(np.cos(n * th) * 2.2, -1, 1)              # flat-topped teeth
            edge = pitch + MODULE * 0.85 * tooth
            body = r < edge
            spokes = max(3, min(6, n // 4))
            hole = (r > pitch * 0.32) & (r < pitch - MODULE * 1.6) & (np.cos(spokes * th) < 0.35) & (n > 11)
            axle = r < max(1.8, pitch * 0.12)
            solid = body & ~hole & ~axle
            # bevel: lit where the outline faces the light, shadowed opposite
            nx, ny = dx / (r + 1e-6), dy / (r + 1e-6)
            rim = np.clip(1 - (edge - r) / 2.0, 0, 1) + np.clip(1 - np.abs(r - pitch * 0.32) / 1.5, 0, 1) * (n > 11)
            facing = nx * light[0] + ny * light[1]
            # brushed brass: a bright wedge where the circular grain faces the light, fine rings
            world = np.arctan2(dy, dx)
            sheen = np.clip(np.cos(world - math.atan2(light[1], light[0]) - math.pi / 2), 0, 1) ** 6 \
                + np.clip(np.cos(world - math.atan2(light[1], light[0]) + math.pi / 2), 0, 1) ** 6
            grain = 0.04 * np.sin(r * 2.1)
            base = 0.32 + 0.1 * ((gi * 0.37) % 1)
            shade = base + 0.38 * sheen + grain + 0.35 * rim * facing
            region = tone[y0:y1, x0:x1]
            region[solid] = np.clip(shade[solid], 0.08, 1)
            shadow = ~solid & (np.hypot(dx - 1.5, dy - 1.5) < edge) & ~axle   # a drop shadow down-right
            region[shadow & (region > 0.03)] *= 0.4
        return self.print(np.clip(tone, 0, 1))

    def lights(self):
        return [self.glow(0, 0.1, 0.2 + 0.25 * self.speed), self.glow(1, 0.12)] + self.ink_lights()
