"""Base for our own patterns on the Patternflow shelf.

They sit among Lee's presets and follow the shelf's rules: four knobs, each
turning one quality of a pattern that runs by itself. The menu's "audio knobs"
switch (k2 on that shelf) works for them too. With it on, `self.sound` holds
four envelopes (mid, level, bass, treble, as upstream's audio edition reads
them) and `self.beat` the beat's pulse, and each pattern adds them to what its
knobs set. `self.on_bar` and `self.on_phrase` are true for the frame a bar or an
8-bar phrase begins, so patterns can change form with the music's structure.
"""
import math

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
