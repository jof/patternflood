"""What the analyzer hears, and the controls to help it.

The tempo big, how sure it is, the four beats of the bar (the one in red), the
eight bars of the phrase, the onset trace with the beat grid over it, the
spectrum, and drops and builds as they're detected.

    k0  turn: shift the phrase grid a bar
    k1  click: tap the tempo (three taps or more; it holds for 8 s)
    k2  turn: A/V delay, 5 ms a detent, until the beats land when you hear them
    k3  click: this is the one: mark the downbeat
"""
import numpy as np

from .. import draw
from ..draw import N
from ..runtime import Demo


class Tempo(Demo):
    name = "Tempo"
    blurb = "The beat tracker, shown. k1 click taps tempo, k3 click marks the one, k2 A/V delay, k0 shifts the phrase grid."

    def __init__(self, rt):
        super().__init__(rt)
        self.t_tap = self.t_mark = self.t_delay = self.t_drop = self.t_phrase = -10.0
        self.flash = 0.0

    def turn(self, k, d):
        a = self.rt.audio_in
        if a is None:
            return
        if k == 0:
            a.shift_phrase(d)
        elif k == 2:
            a.delay = a.delay + 0.005 * d
            self.t_delay = self.rt.t

    def release(self, k, click):
        a = self.rt.audio_in
        if not click or a is None:
            return
        if k == 1:
            a.tap()
            self.t_tap = self.rt.t
        elif k == 3:
            a.mark_downbeat()
            self.t_mark = self.rt.t

    def step(self, dt):
        a = self.rt.audio
        if a.beat:
            self.flash = 1.0
        if a.drop:
            self.t_drop = self.rt.t
        if a.phrase:
            self.t_phrase = self.rt.t
        self.flash *= np.exp(-dt * 8)

    def render(self):
        a, t = self.rt.audio, self.rt.t
        img = draw.blank()
        if not a.live:
            draw.text(img, "NO AUDIO", 64, 50, (.6, .3, .3), center=True, scale=2)
            draw.text(img, "run with --audio pulse", 64, 76, (.4, .4, .4), center=True)
            return img
        # the tempo, big, and how sure
        bpm = f"{a.bpm:5.1f}" if a.bpm else "--"
        col = (1, .85, .4) if a.manual else ((.9, .95, 1) if a.locked else (.6, .65, .7))
        draw.text(img, bpm.strip(), 64, 2, col, center=True, scale=3)
        img[36:38, 14:114] = .08
        img[36:38, 14:14 + int(100 * a.conf)] = (.3, .8, .4) if a.locked else (.6, .5, .2)
        tag = "TAP" if a.manual else ("LOCK" if a.locked else "bpm")
        draw.text(img, tag, N - 2 - draw.text_width(tag), 28, (.5, .5, .5))
        # beats of the bar: the one is red, the current beat lit and fading through its length
        for b in range(4):
            x0 = 14 + b * 26
            on = b == a.beat_in_bar
            base = np.array((1, .25, .2) if b == 0 else (.3, .6, 1), np.float32)
            lvl = (1 - a.phase) * 0.9 + 0.1 if on else 0.12
            img[42:54, x0:x0 + 22] = base * lvl
        # bars of the phrase
        for b in range(8):
            x0 = 14 + b * 13
            on = b == a.bar_in_phrase
            img[58:64, x0:x0 + 11] = (.9, .8, .3) if on else ((.25, .22, .1) if b < a.bar_in_phrase else .07)
        phr = max(0.0, 1 - (t - self.t_phrase) / 0.6)
        if phr:
            img[56:66, 12:116] = np.maximum(img[56:66, 12:116], phr * np.array((.5, .45, .15)))
        # onset trace (the last ~2.7 s) with the beat grid predicted over it
        o = np.clip(a.onset_hist[-N:], 0, 1)
        base_y = 98
        for x in range(len(o)):
            h = int(o[x] * 26)
            img[base_y - h:base_y, x] = (.25, .55, .45)
        period_px = 60 / max(a.bpm, 1) * 93.75 if a.bpm else 0
        if period_px:
            x = N - 1 - a.phase * period_px
            k = 0
            while x >= 0:
                beat_no = (a.beat_in_bar - k) % 4
                img[70:99, int(x)] = (.9, .3, .25) if beat_no == 0 else (.35, .35, .45)
                x -= period_px
                k += 1
        # spectrum
        for i, v in enumerate(a.bands):
            x0 = 4 + i * 5
            h = int(v * 22)
            img[127 - h:127, x0:x0 + 4] = (.3 + .7 * v, .4, 1 - .6 * v)
        # events
        drop = max(0.0, 1 - (t - self.t_drop) / 1.0)
        if drop:
            draw.text(img, "DROP", 64, 102, (drop, drop * .3, drop * .2), center=True, scale=1)
        elif a.build > 0.2:
            img[103:105, 34:34 + int(60 * a.build)] = (.9, .6, .2)
            draw.text(img, "build", 64, 100, (.5, .4, .2), center=True)
        if t - self.t_delay < 1.5:
            d = self.rt.audio_in.delay if self.rt.audio_in else 0
            draw.text(img, f"delay {d * 1000:.0f} ms", 64, 100, (.8, .8, .8), center=True)
        if t - self.t_mark < 0.6:
            img[40:56, 12:38] = np.maximum(img[40:56, 12:38], (1, 1, 1))
        img[:, :2] = self.flash * np.array((1, .25, .2) if a.beat_in_bar == 0 else (.3, .6, 1))
        return img

    def lights(self):
        a = self.rt.audio
        beat = max(0.0, 1 - a.phase * 3)
        one = (beat, beat * .2, beat * .15) if a.beat_in_bar == 0 else (beat * .3, beat * .5, beat)
        return [(.2, .18, .08), (1, .8, .3) if a.manual else (.15, .15, .15), (.2, .2, .2), one]
