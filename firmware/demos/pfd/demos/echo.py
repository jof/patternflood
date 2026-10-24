"""Simon, on the knobs: watch the lights, then play the sequence back.

Four columns, one per knob, in the knob row's order and colours. The knob
lights play the sequence as well as the panel. From round 5 some steps are
turns, not presses (an arrow shows which way), so turn direction becomes a
second vocabulary.
"""
import math
import random

import numpy as np

from .. import draw
from ..draw import N
from .squash import COLOURS
from ..runtime import Demo

TURNS_FROM = 5          # rounds before this are presses only
TURN_DEBOUNCE_S = 0.35  # the rest of a flick's detents belong to the same step


class Echo(Demo):
    name = "Echo"
    blurb = "Simon on the knobs. Watch the lights, then play it back: press, or later turn the way the arrow points. Click any knob to start."

    def __init__(self, rt):
        super().__init__(rt)
        self.rng = random.Random()
        self.best = 0
        self.state = "attract"
        self.t_state = rt.t
        self.seq = []
        self.lit = None             # (knob, action, until)
        self.t_turn_ok = [-10.0] * 4

    # ---- game flow

    def start(self):
        self.seq = []
        self.add_step()
        self.show()

    def add_step(self):
        k = self.rng.randrange(4)
        action = "press"
        if len(self.seq) + 1 >= TURNS_FROM and self.rng.random() < 0.4:
            action = self.rng.choice((1, -1))
        self.seq.append((k, action))

    def show(self):
        self.state, self.t_state, self.pos = "show", self.rt.t, 0

    def step_time(self):
        return max(0.28, 0.6 * 0.94 ** len(self.seq))

    def fail(self):
        self.best = max(self.best, len(self.seq) - 1)
        self.state, self.t_state = "fail", self.rt.t

    def _input(self, k, action):
        if self.state == "attract" or (self.state == "fail" and self.rt.t - self.t_state > 1.5):
            if action == "press":
                self.start()
            return
        if self.state != "input":
            return
        want = self.seq[self.pos]
        self.lit = (k, action, self.rt.t + 0.25)
        if (k, action) != want:
            self.fail()
            return
        self.pos += 1
        if self.pos == len(self.seq):
            self.state, self.t_state = "good", self.rt.t

    def press(self, k):
        self._input(k, "press")

    def turn(self, k, d):
        if self.rt.held(k):                 # a press that wobbled the knob: not a turn
            return
        if self.rt.t - self.t_turn_ok[k] < TURN_DEBOUNCE_S:
            self.t_turn_ok[k] = self.rt.t
            return
        self.t_turn_ok[k] = self.rt.t
        self._input(k, 1 if d > 0 else -1)

    def step(self, dt):
        t = self.rt.t
        if self.state == "show":
            st = self.step_time()
            i = int((t - self.t_state - 0.6) / st)
            if i >= len(self.seq):
                self.state, self.t_state, self.pos = "input", t, 0
                self.lit = None
            elif i >= 0:
                frac = (t - self.t_state - 0.6) / st - i
                k, action = self.seq[i]
                self.lit = (k, action, t + 1) if frac < 0.7 else None
        elif self.state == "good" and t - self.t_state > 0.8:
            self.add_step()
            self.show()
        elif self.state == "input" and t - self.t_state > 5 + 0.5 * len(self.seq):
            self.fail()                    # took too long
        if self.lit and self.state != "show" and t > self.lit[2]:
            self.lit = None

    # ---- drawing

    def _levels(self):
        t = self.rt.t
        lv = [0.07] * 4
        if self.state == "attract":
            lv = [0.1 + 0.5 * max(0.0, math.sin(t * 3 - k * 0.8)) for k in range(4)]
        elif self.state == "fail":
            if self.seq and self.pos < len(self.seq):
                k = self.seq[self.pos][0]          # show what it should have been
                lv[k] = 0.9 if int(t * 5) % 2 else 0.15
        elif self.state == "good":
            lv = [0.3 + 0.3 * math.sin(t * 20)] * 4
        if self.lit:
            lv[self.lit[0]] = 1.0
        return lv

    def render(self):
        img = draw.blank()
        lv = self._levels()
        for k in range(4):
            x0 = k * 32
            img[8:120, x0 + 1:x0 + 31] = np.array(COLOURS[k], np.float32) * lv[k]
        if self.lit and self.lit[1] != "press":
            k, d = self.lit[0], self.lit[1]
            cx = k * 32 + 16
            for i in range(12):                   # a solid arrow: up for clockwise, down for anticlockwise
                y = 50 + i if d > 0 else 78 - i
                img[y, cx - i:cx + i + 1] = 0
            img[(62 if d > 0 else 44):(84 if d > 0 else 66), cx - 4:cx + 5] = 0
        # round counter in the top band
        img[:8] = 0
        if self.state == "attract":
            draw.text(img, f"ECHO  best {self.best}" if self.best else "ECHO", 64, -2, (.6, .6, .6), center=True)
        elif self.state == "fail":
            draw.text(img, f"round {len(self.seq)}  best {self.best}", 64, -2, (1, .3, .2), center=True)
        else:
            draw.text(img, f"round {len(self.seq)}", 64, -2, (.5, .5, .5), center=True)
        if self.state == "input":                 # progress through the sequence
            for i in range(len(self.seq)):
                img[123:126, 2 + 4 * i:4 + 4 * i] = 0.6 if i < self.pos else 0.12
        return img

    def lights(self):
        lv = self._levels()
        return [tuple(c * lv[k] for c in COLOURS[k]) for k in range(4)]
