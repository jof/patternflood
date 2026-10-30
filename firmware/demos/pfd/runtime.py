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
    rt.audio              this frame's music (pfd.audio.AudioState): level, bands, bass/mid/
                          treble, onsets, bpm, beat/bar/phrase phases and events, drops. With
                          no audio it's a quiet, steady 120 BPM, so visualizers still move.

The box's four push buttons (left to right: previous, select, next, sleep) belong to
the runtime, in every demo. Demos sit on shelves (Play, Audio, Interdimensional Cable,
Patternflow, Community, Community 1:1, from each class's `group`). Playing, previous
and next step along the shelf, holding them repeats, and select opens the menu. In the
menu, previous and next move between shelves, and the knobs work it: k1 moves between
shelves, k0 picks the demo on the shelf (live, faster when spun), k3 sets brightness,
and on the Patternflow and Community shelves k2 lets the music turn the patterns'
knobs. Select, a click on any knob, or 6 s with no input closes it. Sleep blanks the
panels and the knob lights; it, any other button or a knob push wakes them.
"""
import math
import signal
import time

import numpy as np

from knob_renderer import GAMMA, capped_u8
from . import draw
from .audio import SilentState
from .io import log, sd_notify

CLICK_S = 0.45          # a press shorter than this, with no turn in it, is a click
MENU_IDLE_S = 6.0
BTN_PREV, BTN_SELECT, BTN_NEXT, BTN_SLEEP = range(4)
REPEAT_DELAY_S = 0.5    # holding previous or next repeats after this long
REPEAT_S = 0.15         # at this rate
SHELF_NAMES = {"play": "PLAY", "audio": "AUDIO", "patternflow": "PATTERNFLOW", "community": "COMMUNITY",
               "community-1to1": "COMMUNITY 1:1", "cable": "INTERDIM. CABLE"}
AUDIO_KNOB_SHELVES = ("patternflow", "community", "community-1to1")     # Patternflow patterns: sound can turn their knobs
LIGHT_MAX = 255         # the 4991 NeoPixels at full scale; they dim with the panel's brightness (k3)
LIGHT_FLOOR = 0.15      # but no dimmer than this fraction of it, so the knobs still read on a dark panel
NKNOBS = 4
DETENTS_PER_REV = 24    # the 4991's encoder (PEC11-style); for demos that map a knob to an absolute angle
GAMMA_STEPS = 4096      # gamma by table: within 0.07 of an 8-bit step of the exact curve, and far cheaper than **


def _gamma_table(bright):
    """0..1 (in GAMMA_STEPS steps) -> the panel's 8-bit duty at this brightness."""
    return (np.linspace(0.0, 1.0, GAMMA_STEPS) ** GAMMA * bright * 255 + 0.5).astype(np.uint8)


class Demo:
    name = "?"
    blurb = ""
    group = "play"

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
    def __init__(self, demos, knobs, out, fps=60.0, bright=0.3, start=0, duration=None, audio=None, buttons=None):
        self.demo_classes = demos
        self.instances = {}
        self.knobs_in, self.buttons_in, self.out = knobs, buttons, out
        self.audio_in = audio
        self.audio = SilentState(0.0, -1)
        self.audio_knobs = False        # upstream patterns: sound turns their knobs, as upstream's audio edition
        self.fps, self.bright, self.duration = fps, bright, duration
        self.k = [Knob() for _ in range(NKNOBS)]
        self.t = 0.0
        self.menu = False
        self.t_menu_input = 0.0
        self.asleep = False
        self.t_repeat = [None] * 4      # previous/next held: when they next repeat
        self.t_banner = -10.0
        self.index = start % len(demos)
        self.shelves = list(dict.fromkeys(getattr(d, "group", "play") for d in demos))
        self.shelf_pos = {g: next(i for i, d in enumerate(demos) if d.group == g) for g in self.shelves}
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
        if kind in ("bdown", "bup"):
            self._button(ev[1], kind == "bdown")
            return
        k = ev[1]
        if k >= NKNOBS:
            return
        kn = self.k[k]
        if self.asleep:
            if kind == "down":                      # a push wakes the box, and does nothing else
                self._wake()
            elif kind == "up":
                kn.down = False                     # held through the sleep button: let go quietly
            return
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

    def _shelf(self, i=None):
        g = self.demo_classes[self.index if i is None else i].group
        return g, [j for j, d in enumerate(self.demo_classes) if d.group == g]

    def _step_demo(self, n):
        """n demos along the shelf."""
        g, members = self._shelf()
        self.index = members[(members.index(self.index) + n) % len(members)]
        self.shelf_pos[g] = self.index
        self.demo = self._instance(self.index)

    def _step_shelf(self, d):
        """To the next shelf (d > 0) or the previous, where we left it."""
        g = self.demo_classes[self.index].group
        s = self.shelves[(self.shelves.index(g) + (1 if d > 0 else -1)) % len(self.shelves)]
        self.index = self.shelf_pos[s]
        self.demo = self._instance(self.index)

    def _menu_turn(self, k, d):
        if k == 0:
            self._step_demo(round(self.accel(0, d)))        # the community's shelf is long: spin it
        elif k == 1:
            self._step_shelf(d)
        elif k == 3:
            self.bright = min(1.0, max(0.02, self.bright * (1.08 ** d)))
        elif k == 2 and self.demo_classes[self.index].group in AUDIO_KNOB_SHELVES:
            self.audio_knobs = d > 0
            log(f"menu: audio drives upstream knobs {'on' if self.audio_knobs else 'off'}")

    def _button(self, b, down):
        if not down:
            if b < len(self.t_repeat):
                self.t_repeat[b] = None
            return
        if self.asleep:
            self._wake()
            return
        if self.menu:
            self.t_menu_input = self.t
        if b in (BTN_PREV, BTN_NEXT):
            self._button_step(b)
            self.t_repeat[b] = self.t + REPEAT_DELAY_S
        elif b == BTN_SELECT:
            if self.menu:
                self.menu = False
                log("menu: closed")
            else:
                self.menu = True
                self.t_menu_input = self.t
                for kn in self.k:                   # a knob held now lets go without a click
                    if kn.down:
                        kn.consumed = True
                log("menu: open")
        elif b == BTN_SLEEP:
            self.menu = False
            self.asleep = True
            log("sleep")

    def _button_step(self, b):
        d = 1 if b == BTN_NEXT else -1
        if self.menu:
            self._step_shelf(d)
        else:
            self._step_demo(d)

    def _wake(self):
        self.asleep = False
        self.t_banner = self.t                      # say what's on
        log("awake")

    def _check_timers(self):
        for b in (BTN_PREV, BTN_NEXT):
            if self.t_repeat[b] is not None and self.t >= self.t_repeat[b] and not self.asleep:
                self._button_step(b)
                self.t_repeat[b] = self.t + REPEAT_S
                if self.menu:
                    self.t_menu_input = self.t
        if self.menu and self.t - self.t_menu_input > MENU_IDLE_S and not any(kn.down for kn in self.k):
            self.menu = False
            log("menu: closed (idle)")

    def _overlay(self, rgb):
        name = self.demo_classes[self.index].name
        if self.menu:
            rgb *= 0.35
            rgb[:27] *= 0.25
            g, members = self._shelf()
            # the shelf, with a dot for each shelf
            draw.text(rgb, f"< {SHELF_NAMES.get(g, g.upper())} >", 64, 0, (.55, .75, 1), center=True)
            for s, shelf in enumerate(self.shelves):
                x = 64 + (s - (len(self.shelves) - 1) / 2) * 6
                draw.disc(rgb, x, 12, 1.2, (.55, .75, 1) if shelf == g else (.25, .25, .3), soft=0.3)
            draw.text(rgb, name.upper(), 64, 15, (1, 1, 1), center=True)
            pos = members.index(self.index)
            rgb[29, 4:124] = 0.12                               # where we are on the shelf
            x = 4 + int(119 * pos / max(1, len(members) - 1))
            rgb[28:31, max(4, x - 1):x + 2] = (1, 1, 1)
            draw.text(rgb, f"{pos + 1}/{len(members)}", 64, 31, (.45, .45, .45), center=True)
            blurb = self.demo_classes[self.index].blurb
            for j, line in enumerate(_wrap(blurb, 120)[:5]):
                draw.text(rgb, line, 64, 43 + 11 * j, (.8, .8, .6), center=True)
            rgb[118:122, 4:124] = 0.15
            rgb[118:122, 4:4 + int(120 * self.bright)] = (1, .8, .3)
            draw.text(rgb, "k0 demo  k1 shelf", 64, 104, (.5, .5, .5), center=True)
            if g in AUDIO_KNOB_SHELVES and self.audio.live:
                draw.text(rgb, f"k2 audio knobs {'ON' if self.audio_knobs else 'off'}",
                          64, 96, (.45, .7, .9) if self.audio_knobs else (.4, .4, .4), center=True)
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
        scale = LIGHT_MAX * max(LIGHT_FLOOR, self.bright)     # same curve as the panel's gamma table
        return [tuple(int(scale * min(1.0, max(0.0, c)) ** GAMMA + 0.5) for c in rgb) for rgb in ls[:NKNOBS]]

    def _pace(self, realtime, t_frame, period):
        """Wait out the frame and advance the clock; -> the new frame's dt."""
        if realtime:
            time.sleep(max(0.0, period - (time.monotonic() - t_frame)))
            now = time.monotonic() - self.t0
            dt, self.t = min(0.1, now - self.t), now
        else:
            dt = period
            self.t += dt
        return dt

    def run(self):
        realtime = getattr(self.out, "realtime", True)
        self.t0 = time.monotonic()
        self.last_lights = None
        frames, t_stat, amps, scale = 0, 0.0, 0.0, 1.0
        table, table_bright = None, None
        period = dt = 1.0 / self.fps
        t_alive = None
        try:
            while self.duration is None or self.t < self.duration:
                t_frame = time.monotonic()
                if t_alive is None or t_frame - t_alive >= 1:     # systemd restarts us if this stops
                    sd_notify("WATCHDOG=1" if t_alive else "READY=1")
                    t_alive = t_frame
                for ev in self.knobs_in.poll(self.t):
                    self._event(ev)
                if self.buttons_in:
                    for ev in self.buttons_in.poll(self.t):
                        self._event(ev)
                self._check_timers()
                if self.audio_in:
                    self.audio = self.audio_in.frame(dt)
                else:
                    self.audio = SilentState(self.t, self.audio.counts["beat"])
                if self.asleep:
                    self.out.show(_BLACK, None)
                    if self.last_lights != _DARK:
                        self.knobs_in.set_lights(_DARK)
                        self.last_lights = _DARK
                    dt = self._pace(realtime, t_frame, period)
                    continue
                self.demo.step(dt)

                # NaN would slip through the current cap, so scrub it before anything else: fmax
                # takes NaN to 0 (as nan_to_num did), and the pair clips to 0..1, in a float32 copy.
                rgb = np.fmax(self.demo.render(), np.float32(0), dtype=np.float32)
                np.fmin(rgb, np.float32(1), out=rgb)
                # the music's big moments, made bright, on the Audio shelf's visualizers
                if getattr(self.demo, "flare", self.demo.group == "audio") and self.audio.live:
                    rgb = draw.flare(rgb, float(np.clip((self.audio.impact - 0.45) / 0.5, 0, 1)))
                rgb = self._overlay(rgb)
                if table_bright != self.bright:
                    table, table_bright = _gamma_table(self.bright), self.bright
                np.clip(rgb, 0, 1, out=rgb)
                rgb *= GAMMA_STEPS - 1
                rgb += 0.5
                frame, amps, scale = capped_u8(table[rgb.astype(np.uint16)])

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

                dt = self._pace(realtime, t_frame, period)
        except KeyboardInterrupt:
            pass
        finally:
            signal.signal(signal.SIGINT, signal.SIG_IGN)       # a second Ctrl-C mustn't stop the blanking
            self.knobs_in.set_lights([(0, 0, 0)] * NKNOBS)
            self.knobs_in.close()
            if self.buttons_in:
                self.buttons_in.close()
            self.out.close()
            if self.audio_in:
                self.audio_in.close()
            log("stopped; display blanked")


_BLACK = np.zeros((128, 128, 3), np.uint8)
_DARK = [(0, 0, 0)] * NKNOBS


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
