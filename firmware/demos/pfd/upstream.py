"""Upstream Patternflow's preset patterns, run natively, as demos.

upstream_host/build.py compiles the preset headers, unchanged, into a shared
library. This wraps each one as a Demo:

    knob turn  -> InputFrame.knobDeltas (raw detents, no acceleration, as upstream)
    knob press -> btnPressed on the next frame (edge), btnHeld while down

Upstream's own output stage is reproduced here, apart from its panel gamma: its
saturation boost (LED_SAT_BOOST 1.62, which the patterns were tuned under).
The runtime's gamma then treats the pattern's 0..255 as perceptual, as
upstream's panel driver does.
"""
import ctypes
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

from .draw import N, hsv1
from .io import log
from .runtime import Demo

BUILD = Path(__file__).resolve().parents[1] / "upstream_host"

# How each preset meets the square, by eye from contact sheets at 128x128 and at
# upstream's own 128x64 (2026-10-23). The default is to compile for 128x128 and
# fill it. Some presets are portrait (the upstream device stands on its end): they
# draw with "up" along the panel's +x, as upstream's canvas maps a 64x128 frame,
# so they're turned a quarter anticlockwise to stand upright.
PORTRAIT = {"Midsummer Sea", "Firefly Hollow"}       # scale fine to 128x128, then turn
PORTRAIT_NATIVE = {"Breakout Arcade"}               # layout needs 64 rows: 128x64, turned, centred
NOTES = {"0519-1": "Starts dark (upstream's default): turn k0 up."}
SAT_BOOST = 1.62
AUDIO_ATTACK_S, AUDIO_RELEASE_S = 0.04, 0.35
LUMA = np.array([0.299, 0.587, 0.114], np.float32)


def _stale(lib_path):
    """Missing, or older than anything of ours it's built from (the upstream clone itself is pinned)."""
    if not lib_path.exists():
        return True
    ours = [BUILD / "build.py", *BUILD.glob("shim/**/*.h"), *BUILD.glob("web_ports/*.h")]
    return max(p.stat().st_mtime for p in ours) > lib_path.stat().st_mtime


def _load(size="128x128"):
    lib_path = BUILD / "build" / f"libpfup_{size}.so"
    if _stale(lib_path):
        log(f"upstream: building {lib_path.name}")
        r = subprocess.run([sys.executable, str(BUILD / "build.py"), "--size", size], capture_output=True, text=True)
        if r.returncode:
            log(f"upstream: build failed, running without upstream patterns\n{r.stderr[-2000:]}")
            return None
    return open_lib(lib_path)


def open_lib(lib_path):
    """A library with build.py's C API (the community's, from community.py, have the same)."""
    lib = ctypes.CDLL(str(lib_path))
    lib.pf_name.restype = lib.pf_author.restype = lib.pf_label.restype = ctypes.c_char_p
    lib.pf_frame.restype = ctypes.POINTER(ctypes.c_uint8)
    lib.pf_frame.argtypes = [ctypes.c_int, ctypes.c_float, ctypes.POINTER(ctypes.c_int),
                             ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint32,
                             ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_float)]
    return lib


class Upstream(Demo):
    """Base for the generated per-pattern classes; `index` and `lib` are set on each."""
    group = "patternflow"
    lib = None
    index = 0

    turn_upright = False
    audio_knobs_ok = True       # the menu's audio knobs may turn this one's knobs

    def __init__(self, rt):
        super().__init__(rt)
        self.w, self.h = self.lib.pf_width(), self.lib.pf_height()
        self.deltas = (ctypes.c_int * 4)()
        self.pressed = (ctypes.c_uint8 * 4)()
        self.held = (ctypes.c_uint8 * 4)()
        self.audio_on = (ctypes.c_uint8 * 4)()
        self.audio_val = (ctypes.c_float * 4)()
        self.ballistic = [0.0] * 4
        self.t_touch = [-10.0] * 4
        self.lib.pf_setup(self.index)
        self.frame = np.zeros((N, N, 3), np.float32)

    def turn(self, k, d):
        self.deltas[k] += d
        self.t_touch[k] = self.rt.t

    def press(self, k):
        self.pressed[k] = 1
        self.t_touch[k] = self.rt.t

    def step(self, dt):
        for k in range(4):
            self.held[k] = int(self.rt.held(k))
        # Upstream's audio edition: each knob follows the energy in one range of the spectrum,
        # quick to rise and slow to fall, and the pattern sees it as the knob's value (0..1).
        a = self.rt.audio
        on = self.rt.audio_knobs and a.live and self.audio_knobs_ok
        targets = (a.mid, a.level, a.bass, a.treble)
        for k in range(4):
            tc = AUDIO_ATTACK_S if targets[k] > self.ballistic[k] else AUDIO_RELEASE_S
            self.ballistic[k] += (targets[k] - self.ballistic[k]) * (1 - math.exp(-dt / tc))
            self.audio_on[k] = int(on)
            self.audio_val[k] = min(1.0, max(0.0, self.ballistic[k]))
        buf = self.lib.pf_frame(self.index, dt, self.deltas, self.pressed, self.held,
                                int(self.rt.t * 1000) & 0xFFFFFFFF, self.audio_on, self.audio_val)
        for k in range(4):
            self.deltas[k] = self.pressed[k] = 0
        self.present(np.ctypeslib.as_array(buf, shape=(self.h, self.w, 3)))

    def present(self, rgb888):
        """A frame of the pattern's (h, w, 3) uint8 -> self.frame, as upstream's output stage shows it."""
        # The saturation boost, in place, with the /255 folded in. No clip: the runtime clips
        # every demo's render to 0..1 straight away.
        img = rgb888.astype(np.float32)
        y = (img @ LUMA)[..., None]
        img -= y
        img *= np.float32(SAT_BOOST / 255.0)
        y *= np.float32(1 / 255.0)
        img += y
        if self.turn_upright:
            img = np.rot90(img)                 # the panel's right edge becomes the top
        if img.shape[:2] == (N, N):
            self.frame = img
        else:                                   # a library built for another panel size: centre it
            h, w = img.shape[:2]
            self.frame = np.zeros((N, N, 3), np.float32)
            oy, ox = max(0, (N - h) // 2), max(0, (N - w) // 2)
            self.frame[oy:oy + min(N, h), ox:ox + min(N, w)] = img[:N, :N]

    def render(self):
        return self.frame

    def lights(self):
        # upstream has no knob lights: a dim idle glow that flares when a knob is used
        out = []
        for k in range(4):
            a = max(0.0, 1 - (self.rt.t - self.t_touch[k]) / 0.6)
            out.append(tuple(0.12 + 0.6 * a * c for c in hsv1(0.6 - 0.15 * k, 0.5)))
        return out


def knobs_blurb(lib, i):
    """" k0 Speed, k1 Hue, ..." from the pattern's KNOB_LABELS, or "" when they're just "Knob 1".."Knob 4"."""
    labels = [lib.pf_label(i, k).decode(errors="replace") for k in range(4)]
    if all(lab.lower().startswith("knob") for lab in labels):
        return ""
    return " " + ", ".join(f"k{k} {lab}" for k, lab in enumerate(labels)) + "."


def demos():
    """One Demo class per upstream preset, or [] if the library can't be built."""
    lib = _load("128x128")
    if lib is None:
        return []
    native = None
    out = []
    for i in range(lib.pf_count()):
        name = lib.pf_name(i).decode()
        use, upright = lib, name in PORTRAIT
        index = i
        if name in PORTRAIT_NATIVE:
            native = native or _load("128x64")
            names = [native.pf_name(n).decode() for n in range(native.pf_count())] if native else []
            if name in names:                       # by name: the two libraries needn't list the same presets
                use, upright, index = native, True, names.index(name)
        author = lib.pf_author(i).decode()
        blurb = f"Patternflow preset{' by ' + author if author else ''}." + knobs_blurb(lib, i)
        if name in NOTES:
            blurb += " " + NOTES[name]
        out.append(type(f"PF_{name}", (Upstream,), {"name": f"pf {name}", "blurb": blurb, "lib": use, "index": index,
                                                    "turn_upright": upright}))
    return out
