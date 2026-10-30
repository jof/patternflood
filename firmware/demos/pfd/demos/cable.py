"""Interdimensional Cable: a TV that surfs through very weird channels from other dimensions,
in the spirit of Rick and Morty's interdimensional cable, Robot Chicken and Prometheus and Bob.

Each channel is a short clip (pfd/cable/lineup.py), drawn whole from a script, so it starts
over when you come back to it. A clip plays a few times over (about LOOP_S in all, and at
least twice), then the TV surfs on by itself. The channels come in a shuffled order, new each
time Cable starts and again after every lap, so every channel plays once before any comes
round again. Video files in ~/cable (or $PF_CABLE) join the line-up as more channels: each
tune-in plays a random excerpt, cropped square, silent like everything else here, so physical
comedy plays best.

Any knob steps forward or back through the shuffled order, one channel a detent (back goes
back to what you were just watching), and so do the previous and next buttons; a click skips
ahead; hold a knob for a moment to stay tuned (the clip loops for good), and again to surf.

Starting is quick, as the menu passes through it: each channel is made the first time it's
tuned, and the tapes are probed in the background, joining the lap in progress when ready. The knob lights glow with the picture and
fill left to right as the channel's time runs out.
"""
import os
import random
import subprocess
import threading
from pathlib import Path

import numpy as np

from .. import draw
from ..cable import headlines
from ..cable.lineup import CHANNELS
from ..cable.shows import Show
from ..draw import N, Y
from ..io import log
from ..runtime import Demo

STATIC_S = 0.22         # snow between channels
OSD_S = 2.5             # the channel number, after a change
HOLD_S = 0.7            # hold one knob this long to stay tuned
TAPE_FPS = 24
TAPE_S = (8.0, 14.0)    # how long an excerpt of a tape runs
TAPE_EXT = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v", ".gif"}
TAPE_NUM = 700          # tapes are numbered from here, three apart
LOOP_S = 24.0           # a channel stays about this long before surfing on
LOOPS = (2, 4)          # playing its clip at least this many times, and at most this many
OSD = (.35, 1, .35)


class Tape(Show):
    """A video file, as a channel: a random excerpt of it each time it's tuned in, or all of it
    if it's no longer than an excerpt (a trim, as tools/cable_trims.py makes)."""
    reception = 0.08

    def __init__(self, path, num):
        self.path, self.num = path, num
        self.title = path.stem.upper().replace("_", " ")[:20]
        self.duration = _probe(path)
        self.trim = 0 < self.duration <= TAPE_S[1] + 1
        self.length = self.duration if self.trim else TAPE_S[1]
        self.frames, self.proc, self.gen = [], None, 0

    def tune(self):
        self.stop()
        if self.trim:
            start = 0.0
        else:
            self.length = random.uniform(*TAPE_S)
            start = random.uniform(0, max(0.0, self.duration - self.length)) if self.duration else 0.0
        self.frames = []
        self.gen += 1
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.2f}", "-i", str(self.path), "-t", f"{self.length:.2f}", "-an",
               "-vf", f"fps={TAPE_FPS},scale={N}:{N}:force_original_aspect_ratio=increase,crop={N}:{N}",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        try:
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.DEVNULL)
        except OSError as e:
            log(f"cable: {self.path.name}: {e}")
            return
        threading.Thread(target=self._read, args=(self.proc, self.gen), daemon=True).start()

    def _read(self, proc, gen):
        size = N * N * 3
        while gen == self.gen:
            buf = proc.stdout.read(size)
            if len(buf) < size:
                break
            self.frames.append(np.frombuffer(buf, np.uint8).reshape(N, N, 3))
        proc.stdout.close()

    def stop(self):
        self.gen += 1
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
        self.proc = None

    def draw(self, img, t):
        if not self.frames:
            img[:] = 0.03
            return
        img[:] = self.frames[min(len(self.frames) - 1, int(t * TAPE_FPS))] / np.float32(255)


def _probe(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                             capture_output=True, text=True, timeout=10).stdout
        return float(out.strip())
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return 0.0


def tapes(start):
    root = Path(os.path.expanduser(os.environ.get("PF_CABLE", "~/cable")))
    if not root.is_dir():
        return []
    files = sorted(p for p in root.rglob("*") if p.suffix.lower() in TAPE_EXT)
    return [Tape(p, start + 3 * i) for i, p in enumerate(files)]


class Cable(Demo):
    name = "Cable"
    group = "cable"
    blurb = "TV from other dimensions. Any knob or previous/next changes channel, a click skips, hold one to stay tuned."
    flare = False

    def __init__(self, rt):
        super().__init__(rt)
        headlines.start()
        self.shows = sorted(CHANNELS, key=lambda c: c.num)     # classes, made when first tuned
        self.found = None
        threading.Thread(target=self._find_tapes, daemon=True).start()     # ffprobe: ~0.1 s a tape on the Pi
        self.rng = np.random.default_rng()
        self.order = random.sample(range(len(self.shows)), len(self.shows))
        self.pos = 0
        self.idx = self.order[0]
        self.t_show = 0.0
        self.loop = 0
        self.t_change = -1.0
        self.stay = False
        self.held_done = [False] * 4
        self.t_flash = [-9.0] * 4
        self.t_stay = -9.0
        self.glow = np.zeros((4, 3), np.float32)
        self.img = draw.blank()
        self.vignette = (1 - 0.35 * (np.hypot(np.arange(N) - 63.5, (np.arange(N) - 63.5)[:, None]) / 90) ** 2)[..., None]
        self.vignette = self.vignette.astype(np.float32) * np.where(Y % 2 == 1, 0.82, 1.0).astype(np.float32)[..., None]
        self._tune(0)

    def _find_tapes(self):
        self.found = tapes(TAPE_NUM)

    def _add_tapes(self):
        """The tapes, once probed: into the rest of this lap, at random."""
        found, self.found = self.found, None
        log(f"cable: {len(self.shows)} channels" + (f" and {len(found)} tapes" if found else ""))
        if not found:
            return
        new = list(range(len(self.shows), len(self.shows) + len(found)))
        self.shows += found
        rest = self.order[self.pos + 1:] + new
        random.shuffle(rest)
        self.order[self.pos + 1:] = rest

    def _show(self):
        show = self.shows[self.idx]
        if isinstance(show, type):
            show = self.shows[self.idx] = show()
        return show

    def _loops(self, show):
        return max(LOOPS[0], min(LOOPS[1], round(LOOP_S / show.length)))

    def _tune(self, d, k=None):
        """d channels on (or back) in the shuffled order; past the end, a new shuffle."""
        show = self.shows[self.idx]
        if isinstance(show, Tape):
            show.stop()
        n = len(self.order)
        pos = self.pos + d
        if pos >= n:                                  # a lap done: round again in a new order,
            self.order = random.sample(range(n), n)  # not starting on the channel just left
            if n > 1 and self.order[0] == self.idx:
                self.order.append(self.order.pop(0))
        self.pos = pos % n
        self.idx = self.order[self.pos]
        self.t_show = 0.0
        self.loop = 0
        self.t_change = self.rt.t
        self._show().tune()
        if k is not None:
            self.t_flash[k] = self.rt.t

    def turn(self, k, d):
        self._tune(d, k)

    def skip(self, d):
        self._tune(d)
        return True

    def press(self, k):
        self.held_done[k] = False

    def release(self, k, click):
        if click:
            self._tune(1, k)

    def step(self, dt):
        if self.found is not None:                  # the tapes are probed
            self._add_tapes()
        t = self.rt.t
        if t - self.t_change >= STATIC_S:
            self.t_show += dt
        down = [k for k in range(4) if self.rt.held(k)]
        if len(down) == 1 and not self.held_done[down[0]] and self.rt.held_for(down[0]) > HOLD_S \
                and not self.rt.k[down[0]].turned:
            self.held_done[down[0]] = True
            self.stay = not self.stay
            self.t_stay = t
        show = self.shows[self.idx]
        if self.t_show > show.length:
            self.loop += 1
            if self.stay or self.loop < self._loops(show):
                self.t_show = 0.0                     # again, straight on, without the snow
            else:
                self._tune(1)

    def render(self):
        t = self.rt.t
        img = self.img
        show = self.shows[self.idx]
        since = t - self.t_change
        snow = self.rng.random((N, N, 1), np.float32)
        if since < STATIC_S:
            img[:] = snow * 0.8
            img[int((t * 300) % N):][:12] *= 0.4                  # a rolling bar
        else:
            img[:] = 0
            show.draw(img, self.t_show)
            fuzz = max(show.reception, 0.6 * (1 - (since - STATIC_S) / 0.35))
            if fuzz > 0:
                img *= 1 - 0.55 * fuzz
                img += snow * (0.55 * fuzz)
                if fuzz > 0.2:                                      # tearing
                    shift = (self.rng.random(N) < fuzz * 0.15) * self.rng.integers(-6, 7, N)
                    rows = np.arange(N)[:, None]
                    img[:] = img[rows, (np.arange(N)[None, :] - shift[:, None]) % N]
        # sample the glow for the knobs before the TV's own marks go on
        q = img.reshape(N, 4, N // 4, 3).mean((0, 2))
        self.glow = q / max(0.25, float(q.max()))
        if since < OSD_S or t - self.t_stay < OSD_S:
            num = f"{show.num:d}"
            draw.text(img, num, N - 3 - draw.text_width(num, 2) + 2, 3, (0, 0, 0), scale=2)
            draw.text(img, num, N - 4 - draw.text_width(num, 2), 2, OSD, scale=2)
            label = "STAY TUNED" if self.stay and t - self.t_stay < OSD_S else show.title
            if label:
                draw.text(img, label, N - 3 - draw.text_width(label), 26, (0, 0, 0))
                draw.text(img, label, N - 4 - draw.text_width(label), 25, OSD)
        out = img * self.vignette
        out[..., 0] = np.roll(out[..., 0], 1, 1) * 0.6 + out[..., 0] * 0.4  # a little colour bleed
        return out

    def lights(self):
        t = self.rt.t
        show = self.shows[self.idx]
        left = 1.0 if self.stay else min(1.0, (self.loop + self.t_show / show.length) / self._loops(show))
        out = []
        for k in range(4):
            fill = min(1.0, max(0.0, left * 4 - k))
            c = self.glow[k] * (0.2 + 0.8 * fill)
            f = max(0.0, 1 - (t - self.t_flash[k]) / 0.3)
            out.append(tuple(float(v) * (1 - f) + f for v in c))
        return out
