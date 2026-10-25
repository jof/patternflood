"""Base for our own patterns on the Patternflow shelf.

They sit among SeungHun's presets and follow the shelf's rules: four knobs, each
turning one quality of a pattern that runs by itself. The menu's "audio knobs"
switch (k2 on that shelf) works for them too. With it on, `self.sound` holds
four envelopes (mid, level, bass, treble, as upstream's audio edition reads
them) and `self.beat` the beat's pulse, and each pattern adds them to what its
knobs set. `self.on_bar` and `self.on_phrase` are true for the frame a bar or an
8-bar phrase begins, so patterns can change form with the music's structure.
"""
import math

from .. import hues, ink
from ..draw import hsv1
from ..runtime import Demo

ATTACK_S, RELEASE_S = 0.04, 0.35


class Original(Demo):
    group = "patternflow"

    def __init__(self, rt):
        super().__init__(rt)
        self.sound = [0.0] * 4
        self.beat = 0.0
        self.on_beat = self.on_bar = self.on_phrase = False
        self.t_touch = [-10.0] * 4

    @property
    def listening(self):
        return self.rt.audio_knobs and self.rt.audio.live

    def touch(self, k):
        self.t_touch[k] = self.rt.t

    def hear(self, dt):
        """Call from step(): moves the envelopes, which fall to zero when not listening."""
        a = self.rt.audio
        on = self.listening
        targets = (a.mid, a.level, a.bass, a.treble) if on else (0.0,) * 4
        for k in range(4):
            tc = ATTACK_S if targets[k] > self.sound[k] else RELEASE_S
            self.sound[k] += (targets[k] - self.sound[k]) * (1 - math.exp(-dt / tc))
        self.beat = (1 - a.phase) ** 3 if on else 0.0
        self.on_beat, self.on_bar, self.on_phrase = (on and a.beat), (on and a.bar), (on and a.phrase)

    def glow(self, k, hue, level=0.5):
        """A knob light: `level` at rest, brighter for a moment after the knob is used."""
        a = max(0.0, 1 - (self.rt.t - self.t_touch[k]) / 0.6)
        return tuple(min(1.0, (level + 0.5 * a) * c) for c in hsv1(hue, 0.8))


class Inked(Original):
    """An Original printed through pfd.ink: by the shelf's convention k2 turns the screen and k3
    the inks (call `turn_ink` from turn()); `chunky()` doubles the pixels; `print(tone)` dithers."""
    palette, screen_kind, pitch = "silver", "bayer8", 3.0

    def __init__(self, rt):
        super().__init__(rt)
        self.pal_i = ink.palette_index(self.palette)
        self.screen_i = ink.SCREENS.index(self.screen_kind)
        self.scale = 1
        self.set_screen()

    def set_screen(self):
        self.thresh = ink.screen(ink.SCREENS[self.screen_i], self.scale, angle=0.3, pitch=self.pitch * self.scale)

    def turn_ink(self, k, d):
        """k2 steps the screen, k3 the inks; True if it took the turn."""
        if k == 2:
            self.screen_i = (self.screen_i + (1 if d > 0 else -1)) % len(ink.SCREENS)
            self.set_screen()
        elif k == 3:
            self.pal_i = (self.pal_i + (1 if d > 0 else -1)) % len(ink.PALETTES)
        else:
            return False
        return True

    def chunky(self):
        self.scale = 3 - self.scale
        self.set_screen()

    @property
    def inks(self):
        return ink.PALETTES[self.pal_i][1]

    def print(self, tone):
        return ink.dither(tone, self.inks, self.thresh, self.scale)

    def ink_lights(self):
        """Lights for k2 and k3: the screen's hue, and the palette's top ink."""
        return [self.glow(2, self.screen_i / len(ink.SCREENS)), tuple(float(c) for c in self.inks[-1])]


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
