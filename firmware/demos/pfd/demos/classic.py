"""The three bench patterns from knob_renderer.py, with the same knob map: the baseline."""
import knob_renderer as kr
from ..draw import hsv1
from ..runtime import Demo


class Classic(Demo):
    name = "Classic"
    blurb = "Plasma, tunnel, ripples. k0 hue, k1 speed, k2 scale, k3 level. Click k0 next pattern, k1 freeze, k3 blackout."

    def __init__(self, rt):
        super().__init__(rt)
        self.pattern, self.hue, self.speed, self.scale, self.level = 0, 0.0, 1.0, 1.0, 1.0
        self.frozen = self.black = False
        self.t_anim = 0.0

    def turn(self, k, d):
        if k == 0:
            self.hue = (self.hue + d / 48.0) % 1.0
        elif k == 1:
            self.speed = min(5.0, max(0.0, self.speed + d * 0.1))
        elif k == 2:
            self.scale = min(4.0, max(0.25, self.scale * (1.06 ** d)))
        elif k == 3:
            self.level = min(1.0, max(0.05, self.level + d * 0.04))

    def release(self, k, click):
        if not click:
            return
        if k == 0:
            self.pattern = (self.pattern + 1) % len(kr.PATTERNS)
            self.rt.t_banner = self.rt.t
        elif k == 1:
            self.frozen = not self.frozen
        elif k == 2:
            self.__init__(self.rt)
        elif k == 3:
            self.black = not self.black

    def step(self, dt):
        if not self.frozen:
            self.t_anim += dt * self.speed

    def render(self):
        rgb = kr.PATTERNS[self.pattern][1](self.t_anim, self.scale, self.hue)
        return rgb * (0.0 if self.black else self.level)

    def lights(self):
        return [hsv1(self.hue),
                (0.7, 0, 0) if self.frozen else (0, 0.3 + 0.7 * self.speed / 5, 0),
                (0, 0, 0.3 + 0.35 * self.scale / 4),
                (0, 0, 0) if self.black else (self.level,) * 3]
