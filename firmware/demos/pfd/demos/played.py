"""Our demos, played by the music. Each keeps its original's look and knobs, so you can
still steer, and the music does what a hand would.

    Prism        Kaleido: the barrel turns with the bar, kicks jolt the beads, the mirrors
                 change at each phrase, a drop pours in new beads
    Rain         Droplet: kicks drop big drops, snares middling ones, hats drizzle
    Spores       Reaction: kicks seed it, the section's intensity sets its pace, each phrase
                 moves it to the next preset, a drop wipes and reseeds
    Lissajous    Harmono: glides to a new locked ratio at each phrase, turns a quarter each
                 bar, the kick pumps its size, louder sections draw longer trails
    Night Drive  Resort: cruises at a speed set by the tempo, the day moves on with each phrase
                 (the sunset follows the set), palms sway with the bass, drops turn the colour
"""
import math
import random

import numpy as np

from .harmono import Harmono
from .kaleido import Kaleido
from .droplet import Droplet, LANES
from .reaction import PRESETS, Reaction
from .resort import Resort
from ..draw import N


def bar_seconds(a):
    return 4 * 60.0 / max(60.0, a.bpm or 120.0)


class Prism(Kaleido):
    name = "Prism"
    group = "audio"
    blurb = "Kaleido, played: the barrel turns with the bar, kicks jolt the beads, mirrors change each phrase, drops pour in new beads."
    FOLDS = [4, 6, 8, 5, 12, 6]

    def __init__(self, rt):
        super().__init__(rt)
        self.zoom_base = self.zoom
        self.fold_i = 1
        self.barrel_target = self.barrel

    def turn(self, k, d):
        if k == 1:
            self.zoom_base = min(2.5, max(0.4, self.zoom_base * 1.08 ** d))
        else:
            super().turn(k, d)
            self.barrel_target = self.barrel

    def step(self, dt):
        a = self.rt.audio
        # Turn the barrel the way a hand does: a nudge of 45 degrees on each bar, eased in
        # over a quarter of it, then a pause while the beads tumble down through the view.
        # (Turning it steadily outruns the beads: they lag gravity and leave the mirrors.)
        if a.bar:
            self.barrel_target += math.pi / 4
        self.barrel += (self.barrel_target - self.barrel) * (1 - math.exp(-dt / (bar_seconds(a) / 4)))
        if a.kick_hit:
            # a tap on the tube: knock the beads up against gravity, so they tumble back
            # down through the mirrors' view
            up = -np.array([math.sin(-self.barrel), math.cos(-self.barrel)], np.float32)
            j = 0.8 + 1.2 * a.kick
            self.v += up * j * np.array([self.rng.uniform(0.5, 1.0) for _ in range(len(self.v))], np.float32)[:, None]
            self.v += np.array([[self.rng.uniform(-.3, .3), self.rng.uniform(-.3, .3)] for _ in range(len(self.v))],
                               np.float32)
        if a.phrase:
            self.fold_i = (self.fold_i + 1) % len(self.FOLDS)
            self.folds = self.FOLDS[self.fold_i]
            self._map()
        if a.drop:
            self.beads()
        z = self.zoom_base * (1 + 0.12 * a.bass)
        if abs(z - self.zoom) > 0.01:
            self.zoom = z
            self._map()
        self.hue = (self.hue + dt * 0.01 + (0.08 if a.phrase else 0)) % 1.0
        super().step(dt)


class Rain(Droplet):
    name = "Rain"
    group = "audio"
    blurb = "Droplet, played: kicks drop big drops, snares middling ones, hats drizzle across the pool."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng2 = random.Random()

    def _drip(self, size, lanes):
        k = self.rng2.choice(lanes)
        self.x[k] = self.rng2.uniform(8, N - 8)
        self.drop(k, size)

    def step(self, dt):
        a = self.rt.audio
        if a.kick_hit:
            self._drip(0.8 + 0.6 * a.kick, [1, 2])
        elif a.beat and a.kick < 0.15:
            self._drip(0.6, [1, 2])
        if a.snare_hit:
            self._drip(0.55, [0, 3])
        if a.hat_hit:
            self._drip(0.22, [0, 1, 2, 3])
        if a.drop:
            for k in range(4):
                self.x[k] = 16 + 32 * k
                self.drop(k, 1.4)
        super().step(dt)


class Spores(Reaction):
    name = "Spores"
    group = "audio"
    blurb = "Reaction, played: kicks seed it, the section's intensity sets its pace, phrases move it on, drops wipe and reseed."

    def __init__(self, rt):
        super().__init__(rt)
        self.manual_iters = None

    def turn(self, k, d):
        if k == 2:
            self.manual_iters = self.iters
        super().turn(k, d)

    def step(self, dt):
        a = self.rt.audio
        if a.kick_hit:
            y, x = self.rng.integers(10, N - 10, 2)
            r = int(2 + 3 * a.kick)
            self.b[y - r:y + r, x - r:x + r] = 1.0
            self.a[y - r:y + r, x - r:x + r] = 0.5
            self.t_seed = self.rt.t
        if self.manual_iters is None:
            self.iters = int(4 + 18 * a.intensity)
        if a.phrase:
            # a grown field usually collapses under new parameters: start each phrase fresh
            self.preset = (self.preset + 1) % len(PRESETS)
            _, self.f, self.k = PRESETS[self.preset]
            self.t_param = self.rt.t
            self.wipe()
        if a.drop:
            self.wipe()
            self.seed(16)
        if a.bar:
            self.hue = (self.hue + 0.02) % 1.0
        super().step(dt)


class Lissajous(Harmono):
    name = "Lissajous"
    group = "audio"
    blurb = "Harmono, played: glides to a new locked ratio each phrase, turns a quarter each bar, pumps on the kick, longer trails when it's loud."
    RATIOS = [(3, 2), (2, 1), (4, 3), (5, 4), (3, 1), (5, 3), (1, 1), (5, 2)]

    def __init__(self, rt):
        super().__init__(rt)
        self.target = self.fx
        self.ri = 0
        self.amp = 1.0

    def step(self, dt):
        a = self.rt.audio
        if a.phrase:
            self.ri = (self.ri + 1) % len(self.RATIOS)
            p, q = self.RATIOS[self.ri]
            self.target = self.fy * p / q
        if a.drop:
            self.palette = (self.palette + 1) % 4
        self.fx += (self.target - self.fx) * (1 - math.exp(-dt / (bar_seconds(a) / 3)))
        self.spin = (math.pi / 2) / bar_seconds(a)                        # a quarter turn a bar
        self.trail = 1.0 + 4.0 * a.intensity
        pump = math.exp(-a.phase * 5) * (0.5 + 0.5 * a.kick)
        self.amp = 0.82 + 0.16 * pump
        super().step(dt)


class NightDrive(Resort):
    name = "Night Drive"
    group = "audio"
    blurb = "Resort, played: it cruises at the tempo, the day moves on each phrase so the sunset follows the set, palms sway with the bass, drops turn the colour."

    def __init__(self, rt):
        super().__init__(rt)
        self.t = self.t_target = 0.55
        self.grade_target = self.grade

    def turn(self, k, d):
        super().turn(k, d)
        if k == 0:
            self.t_target = self.t
        if k == 3:
            self.grade_target = self.grade

    def step(self, dt):
        a = self.rt.audio
        self.pan_target += dt * (a.bpm or 120) / 60 * 10                  # ten pixels a beat
        if a.phrase:
            self.t_target = self.t_target + 1 / 12                        # a day in twelve phrases
        if a.drop:
            self.grade_target += 0.25
        target = self.t_target % 1.0
        if target < self.t - 0.5:                                         # past night: the morning after
            self.t = target
        self.t += (target - self.t) * (1 - math.exp(-dt / 2.0))
        self.grade += (self.grade_target - self.grade) * (1 - math.exp(-dt / 2.0))
        self.bass = getattr(self, "bass", 0.0) * 0.8 + 0.2 * a.bass
        super().step(dt)

    def _wind(self, phase, t):
        return max(-1.0, min(1.0, super()._wind(phase, t) * (0.4 + 1.2 * getattr(self, "bass", 0.0))))
