"""The demo runtime: knob events in, frames and knob lights out.

A demo is a class with any of these methods; all have defaults:

    turn(k, d)            knob k turned d detents (+ = clockwise)
    press(k)              knob k pushed down
    release(k, click)     knob k let go; click is True for a short press with no turn in it
    step(dt)              advance the simulation by dt seconds
    render()              -> float RGB (128, 128, 3), 0..1, perceptual (the runtime applies gamma)
    lights()              -> four (r, g, b) 0..1 knob light colours

and these runtime helpers on self.rt:

    rt.held(k)            knob k is down
    rt.held_for(k)        seconds it has been down (0 if up)
    rt.accel(k, d)        d scaled up when the knob is spun fast (for cursors and paddles)
    rt.t                  seconds since start

System gesture, in every demo: hold the two outer knobs (k0 and k3) for a
second to open the menu. In the menu k0 picks the demo (live), k3 sets
brightness, and a click on any knob, or 6 s with no input, closes it.
"""
import math
import signal
import time

import numpy as np

from knob_renderer import GAMMA, capped
from . import draw
from .io import log

CLICK_S = 0.45          # a press shorter than this, with no turn in it, is a click
MENU_HOLD_S = 1.0
MENU_IDLE_S = 6.0
LIGHT_MAX = 64          # the 4991 NeoPixels are bright next to a dim panel
NKNOBS = 4


class Demo:
    name = "?"
    blurb = ""

    def __init__(self, rt):
        self.rt = rt

    def turn(self, k, d):
        pass

    def press(self, k):
        pass

    def release(self, k, click):
        pass

    def step(self, dt):
        pass

    def render(self):
        return draw.blank()

    def lights(self):
        return [(0.0, 0.0, 0.0)] * NKNOBS


class Knob:
    def __init__(self):
        self.down = False
        self.t_down = 0.0
        self.turned = False         # turned while down: not a click
        self.consumed = False       # the menu took this press
        self.rate = 0.0             # detents per second, smoothed
        self.t_turn = -1.0


class Runtime:
    def __init__(self, demos, knobs, out, fps=60.0, bright=0.3, start=0, duration=None):
        self.demo_classes = demos
        self.instances = {}
        self.knobs_in, self.out = knobs, out
        self.fps, self.bright, self.duration = fps, bright, duration
        self.k = [Knob() for _ in range(NKNOBS)]
        self.t = 0.0
        self.menu = False
        self.t_menu_input = 0.0
        self.t_banner = -10.0
        self.index = start % len(demos)
        self.demo = self._instance(self.index)

    # ---- helpers for demos

    def held(self, k):
        return self.k[k].down

    def held_for(self, k):
        return self.t - self.k[k].t_down if self.k[k].down else 0.0

    def accel(self, k, d, top=6.0):
        """Scale d by spin speed: 1x up to ~6 detents/s, rising to `top`x when spun hard."""
        return d * min(top, 1.0 + max(0.0, self.k[k].rate - 6.0) / 5.0)

    # ---- plumbing

    def _instance(self, i):
        if i not in self.instances:
            self.instances[i] = self.demo_classes[i](self)
            log(f"demo: {self.demo_classes[i].name}")
        self.t_banner = self.t
        return self.instances[i]

    def _event(self, ev):
        kind = ev[0]
        if kind == "hello":
            log(f"knobs: {ev[1]} found")
            self.last_lights = None            # bridge (re)booted: resend lights
            return
        k = ev[1]
        if k >= NKNOBS:
            return
        kn = self.k[k]
        if kind == "turn":
            d = ev[2]
            dt = self.t - kn.t_turn
            inst = abs(d) / max(dt, 1 / 120)
            kn.rate = inst if dt > 0.25 else 0.6 * kn.rate + 0.4 * inst
            kn.t_turn = self.t
            if kn.down:
                kn.turned = True
            if self.menu:
                self._menu_turn(k, d)
            else:
                self.demo.turn(k, d)
        elif kind == "down":
            kn.down, kn.t_down, kn.turned, kn.consumed = True, self.t, False, False
            if not self.menu:
                self.demo.press(k)
        elif kind == "up":
            if not kn.down:
                return
            kn.down = False
            click = not kn.turned and self.t - kn.t_down < CLICK_S
            if self.menu:
                if click and not kn.consumed:
                    self.menu = False
                    log("menu: closed")
                if kn.consumed:
                    self.demo.release(k, False)
            else:
                self.demo.release(k, click and not kn.consumed)
        if self.menu:
            self.t_menu_input = self.t

    def _menu_turn(self, k, d):
        if k == 0:
            self.index = (self.index + (1 if d > 0 else -1)) % len(self.demo_classes)
            self.demo = self._instance(self.index)
        elif k == 3:
            self.bright = min(1.0, max(0.02, self.bright * (1.08 ** d)))

    def _check_menu_chord(self):
        k0, k3 = self.k[0], self.k[NKNOBS - 1]
        if not self.menu and k0.down and k3.down and not (k0.consumed or k3.consumed) \
                and self.t - max(k0.t_down, k3.t_down) >= MENU_HOLD_S:
            self.menu = True
            self.t_menu_input = self.t
            for kn in self.k:
                if kn.down:
                    kn.consumed = True
            log("menu: open")
        if self.menu and self.t - self.t_menu_input > MENU_IDLE_S and not any(kn.down for kn in self.k):
            self.menu = False
            log("menu: closed (idle)")

    def _overlay(self, rgb):
        name = self.demo_classes[self.index].name
        if self.menu:
            rgb *= 0.35
            rgb[:16] *= 0.3
            draw.text(rgb, name.upper(), 64, 3, (1, 1, 1), center=True)
            n = len(self.demo_classes)
            for i in range(n):
                x = 64 + (i - (n - 1) / 2) * 8
                draw.disc(rgb, x, 20, 1.6 if i == self.index else 1.0, (1, 1, 1) if i == self.index else (.3, .3, .3))
            blurb = self.demo_classes[self.index].blurb
            for j, line in enumerate(_wrap(blurb, 120)[:6]):
                draw.text(rgb, line, 64, 30 + 12 * j, (.8, .8, .6), center=True)
            rgb[118:122, 4:124] = 0.15
            rgb[118:122, 4:4 + int(120 * self.bright)] = (1, .8, .3)
            draw.text(rgb, "k0 demo   k3 bright", 64, 104, (.5, .5, .5), center=True)
        elif self.t - self.t_banner < 1.5:
            a = min(1.0, 3 * (1.5 - (self.t - self.t_banner)))
            band = rgb[:14]
            band *= 1 - 0.7 * a
            draw.text(rgb, name.upper(), 64, 2, (a, a, a), center=True)
        return rgb

    def _lights(self):
        if self.menu:
            b = self.bright
            ls = [(1, 1, 1), (0, 0, 0), (0, 0, 0), (1, .8 * b + .1, .3 * b)]
        else:
            ls = self.demo.lights()
        return [tuple(int(LIGHT_MAX * min(1.0, max(0.0, c)) ** GAMMA + 0.5) for c in rgb) for rgb in ls[:NKNOBS]]

    def run(self):
        realtime = getattr(self.out, "realtime", True)
        t0 = time.monotonic()
        self.last_lights = None
        frames, t_stat, amps, scale = 0, 0.0, 0.0, 1.0
        period = dt = 1.0 / self.fps
        try:
            while self.duration is None or self.t < self.duration:
                t_frame = time.monotonic()
                for ev in self.knobs_in.poll(self.t):
                    self._event(ev)
                self._check_menu_chord()
                self.demo.step(dt)

                # NaN would slip through the current cap, so scrub it before anything else
                rgb = np.clip(np.nan_to_num(self.demo.render()), 0, 1).astype(np.float32, copy=True)
                rgb = self._overlay(rgb)
                rgb = np.clip(rgb, 0, 1) ** GAMMA * self.bright
                frame, amps, scale = capped(rgb)

                lights = self._lights()
                self.out.show(frame, lights)
                if lights != self.last_lights:
                    self.knobs_in.set_lights(lights)
                    self.last_lights = lights

                frames += 1
                if self.t - t_stat >= 5 and realtime:
                    log(f"{frames / (self.t - t_stat):5.1f} fps  est {amps:4.2f} A  cap x{scale:.2f}  "
                        f"{self.demo.name}  bright {self.bright:.2f}  {self.out.stats()}")
                    frames, t_stat = 0, self.t

                if realtime:
                    time.sleep(max(0.0, period - (time.monotonic() - t_frame)))
                    now = time.monotonic() - t0
                    dt, self.t = min(0.1, now - self.t), now
                else:
                    self.t += dt
        except KeyboardInterrupt:
            pass
        finally:
            signal.signal(signal.SIGINT, signal.SIG_IGN)       # a second Ctrl-C mustn't stop the blanking
            self.knobs_in.set_lights([(0, 0, 0)] * NKNOBS)
            self.knobs_in.close()
            self.out.close()
            log("stopped; display blanked")


def _wrap(s, width_px):
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if cur and draw.text_width(trial) > width_px:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines
