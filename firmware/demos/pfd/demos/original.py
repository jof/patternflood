"""Base for our own patterns in Patternflow's manner, on the Patternflood shelf.

They follow the rules of SeungHun's presets: four knobs, each turning one quality
of a pattern that runs by itself. The menu's "audio knobs" switch (k2) works for
them too. With it on, `self.sound` holds
four envelopes (mid, level, bass, treble, as upstream's audio edition reads
them) and `self.beat` the beat's pulse, and each pattern adds them to what its
knobs set. `self.on_bar` and `self.on_phrase` are true for the frame a bar or an
8-bar phrase begins, so patterns can change form with the music's structure.

Knobs made with `self.dial(...)` and `self.choice(...)` (pfd.knobs: smooth values that stop at
their ends, and lists that dissolve from one item to the next) are moved on by `hear(dt)`.
`self.knob(k, "speed", d, lo, hi, curve)` in turn() makes a plain attribute such a Dial: the
first turn starts it from the attribute's value, and hear() keeps the attribute where the Dial
has glided to (taking up any value the demo gives the attribute itself, a click's say).
"""
import math

from .. import hues, ink, knobs
from ..draw import hsv1
from ..runtime import Demo

ATTACK_S, RELEASE_S = 0.04, 0.35


class Original(Demo):
    audio_knobs_ok = True

    def __init__(self, rt):
        super().__init__(rt)
        self.sound = [0.0] * 4
        self.beat = 0.0
        self.on_beat = self.on_bar = self.on_phrase = False
        self.t_touch = [-10.0] * 4
        self.knobs = []
        self.dials = {}             # attribute name -> Dial, for knob()
        self._wrote = {}            # what hear() last gave each of those attributes
        self._by_knob = {}          # knob -> its Dial, for glow()'s blink at the ends
        self._t_end = [-10.0] * 4   # when each knob was last turned against the end of a list (along)

    def dial(self, k, lo, hi, value, curve="lin", **kw):
        """A pfd.knobs.Dial on knob k, moved on by hear()."""
        self.knobs.append(knobs.Dial(self.rt, k, lo, hi, value, curve, **kw))
        return self.knobs[-1]

    def knob(self, k, name, d, lo, hi, curve="lin", **kw):
        """Turn attribute `name` d detents as a Dial on knob k over lo..hi (see pfd.knobs)."""
        dl = self.dials.get(name)
        if dl is None:
            v = getattr(self, name)
            dl = self.dials[name] = knobs.Dial(self.rt, k, lo, hi, v, curve, **kw)
            self.knobs.append(dl)
            self._wrote[name] = v
        self._by_knob[k] = dl
        return dl.turn(d)

    def along(self, k, i, d, n):
        """List index i one along on knob k (d's sign), stopping at the first and last rather than
        coming round; turned against an end, the knob's light blinks (glow, blink)."""
        j = i + (1 if d > 0 else -1)
        if 0 <= j < n:
            return j
        self._t_end[k] = self.rt.t
        return i

    def blink(self, k, rgb):
        """A knob light, white while it blinks for an end (along, or its Dial's)."""
        dl = self._by_knob.get(k)
        a = self.rt.t - self._t_end[k]
        if (dl is not None and dl.stopped) or (a < knobs.STOP_S and int(a / 0.075) % 2 == 0):
            return (1.0, 1.0, 1.0)
        return rgb

    def choice(self, n, index=0):
        """A pfd.knobs.Choice over n items, moved on by hear()."""
        self.knobs.append(knobs.Choice(self.rt, n, index))
        return self.knobs[-1]

    @property
    def listening(self):
        return self.rt.audio_knobs and self.rt.audio.live

    def touch(self, k):
        self.t_touch[k] = self.rt.t

    def hear(self, dt):
        """Call from step(): moves the envelopes, which fall to zero when not listening, and the knobs."""
        for name, dl in self.dials.items():
            if getattr(self, name) != self._wrote[name]:        # the demo set it: start from there
                dl.set(getattr(self, name), glide=False)
        for kn in self.knobs:
            kn.step(dt)
        for name, dl in self.dials.items():
            self._wrote[name] = dl.v
            setattr(self, name, self._wrote[name])
        a = self.rt.audio
        on = self.listening
        targets = (a.mid, a.level, a.bass, a.treble) if on else (0.0,) * 4
        for k in range(4):
            tc = ATTACK_S if targets[k] > self.sound[k] else RELEASE_S
            self.sound[k] += (targets[k] - self.sound[k]) * (1 - math.exp(-dt / tc))
        self.beat = (1 - a.phase) ** 3 if on else 0.0
        self.on_beat, self.on_bar, self.on_phrase = (on and a.beat), (on and a.bar), (on and a.phrase)

    def glow(self, k, hue, level=0.5, knob=None):
        """A knob light: `level` at rest, brighter for a moment after the knob is used. Given its
        Dial or Choice, it blinks white when turned against an end."""
        if knob is not None and knob.stopped:
            return (1.0, 1.0, 1.0)
        a = max(0.0, 1 - (self.rt.t - self.t_touch[k]) / 0.6)
        return self.blink(k, tuple(min(1.0, (level + 0.5 * a) * c) for c in hsv1(hue, 0.8)))


class Inked(Original):
    """An Original printed through pfd.ink: by the shelf's convention k2 turns the screen and k3
    the inks (call `turn_ink` from turn()); `chunky()` doubles the pixels; `print(tone)` dithers.

    With `smooth` set, the screens and inks are Choices (pfd.knobs): they stop at the first and
    last rather than coming round, and each change dissolves into the next. Set `screen_i` and
    `pal_i` through `set_screen(i)` and `set_inks(i)` so the dissolve follows."""
    palette, screen_kind, pitch = "silver", "bayer8", 3.0
    smooth = True

    def __init__(self, rt):
        super().__init__(rt)
        self.scale = 1
        self.screens = self.choice(len(ink.SCREENS), ink.SCREENS.index(self.screen_kind))
        self.palettes = self.choice(len(ink.PALETTES), ink.palette_index(self.palette))
        self._thresh = {}
        self.set_screen()

    # screen_i and pal_i, as plain demos (and their clicks) use them
    @property
    def screen_i(self):
        return self.screens.i

    @screen_i.setter
    def screen_i(self, i):
        self.screens.go(i, fade=self.smooth)

    @property
    def pal_i(self):
        return self.palettes.i

    @pal_i.setter
    def pal_i(self, i):
        self.palettes.go(i, fade=self.smooth)

    def screen_for(self, i):
        key = (i, self.scale)
        if key not in self._thresh:
            self._thresh[key] = ink.screen(ink.SCREENS[i], self.scale, angle=0.3, pitch=self.pitch * self.scale)
        return self._thresh[key]

    def set_screen(self, i=None):
        """To screen i (or just remake the current one, after chunky)."""
        if i is not None:
            self.screen_i = i

    def set_inks(self, i):
        self.pal_i = i

    @property
    def thresh(self):
        """The screen now: mid-dissolve, the old one's thresholds where the new hasn't reached."""
        s = self.screens
        new = self.screen_for(s.i)
        return knobs.dissolve(s, self.screen_for(s.was), new) if s.mixing else new

    def turn_ink(self, k, d):
        """k2 steps the screen, k3 the inks; True if it took the turn."""
        if k not in (2, 3):
            return False
        c = self.screens if k == 2 else self.palettes
        if self.smooth:
            c.turn(d)
        else:
            c.go(c.i + (1 if d > 0 else -1), fade=False)
        if k == 2:
            self.set_screen()               # for subclasses that build on the screen (Neon)
        return True

    def chunky(self):
        self.scale = 3 - self.scale
        self.set_screen()

    @property
    def inks(self):
        return ink.PALETTES[self.pal_i][1]

    def print(self, tone):
        out = ink.dither(tone, self.inks, self.thresh, self.scale)
        p = self.palettes
        if not p.mixing:
            return out
        return knobs.dissolve(p, ink.dither(tone, ink.PALETTES[p.was][1], self.thresh, self.scale), out)

    def ink_lights(self):
        """Lights for k2 and k3: the screen's hue, and the palette's top ink."""
        if self.palettes.stopped:
            k3 = (1.0, 1.0, 1.0)
        else:
            k3 = tuple(float(c) for c in self.inks[-1])
        return [self.glow(2, self.screen_i / len(ink.SCREENS), knob=self.screens), k3]


class Chromatic(Original):
    """An Original in full colour, through pfd.hues: by the shelf's convention k3 is colour.
    Turning it slides the palette's hues (call `turn_hue` from turn()); `next_palette()`
    (k3's click) changes palette; `colour(t)` looks colours up."""
    palette = 0

    def __init__(self, rt):
        super().__init__(rt)
        self.pal_i = self.palette
        self.shift = 0.0

    def turn_hue(self, k, d):
        """k3 slides the hues; True if it took the turn."""
        if k != 3:
            return False
        self.shift += d / 48
        return True

    def next_palette(self):
        self.pal_i = (self.pal_i + 1) % len(hues.PRESETS)

    def colour(self, t):
        return hues.cosine(t, self.pal_i, self.shift)

    def hue_light(self):
        return tuple(float(v) * 0.7 for v in hues.cosine(0.0, self.pal_i, self.shift))
