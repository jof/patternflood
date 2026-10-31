"""Where the box was left, kept across restarts and power cuts.

The runtime remembers the demo that's on, where each shelf was left, the brightness and
the menu's audio-knobs switch. For each demo it also keeps the knob input that demo has had:
SeungHun's presets and the community's keep their knob values inside their own code
(compiled C++, or a script in node) where Python can't read them. So a demo's state is
brought back by replaying that input into a fresh instance, a frame's worth at a time,
in order. On a pattern that adds each turn to a value (nearly all of them) that lands on
exactly the values it had; what the pattern did with time, or with long holds, isn't kept.

A frame's input is a string of tokens: t<k><+-><d> turn, p<k> press, r<k>[c] release (c: a
click), s<+-><d> a previous/next the demo took (`skip`). A demo whose input means nothing on
a fresh start (Cable, which deals a new shuffle each time) sets `remembers = False`.

The file is JSON, written beside itself and renamed over it once it's on the card (the box's
power switch is a hard power cut), a couple of seconds after the last change.
"""
import json
import os
import threading

from .io import log

VERSION = 1
SAVE_AFTER_S = 2.0          # quiet this long after a change, then save
MAX_RECORDS = 1000          # frames of input kept per demo; past it, runs of turns are merged
REPLAY_DT = 1 / 60


def key(cls):
    """A demo class's name in the file: unique (names repeat across shelves) and stable."""
    return f"{cls.group}/{cls.__name__}"


def default_path():
    """$PF_STATE ("none": don't), else systemd's StateDirectory (/var/lib/patternflood on the box), else none."""
    path = os.environ.get("PF_STATE")
    if path:
        return None if path == "none" else path
    state = os.environ.get("STATE_DIRECTORY")
    return os.path.join(state.split(":")[0], "session.json") if state else None


def load(path):
    try:
        with open(path) as f:
            s = json.load(f)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        log(f"session: can't read {path} ({e}), starting afresh")
        return {}
    if not isinstance(s, dict) or s.get("v") != VERSION:
        log(f"session: {path} is from another version, starting afresh")
        return {}
    return s


class Saver:
    """Writes snapshots on a thread of its own, so the card's write never holds up a frame."""

    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.thread = None

    def save(self, state, wait=False):
        data = json.dumps(state, separators=(",", ":"))
        self.thread = threading.Thread(target=self._write, args=(data,), daemon=True)
        self.thread.start()
        if wait:
            self.thread.join(timeout=5)

    def _write(self, data):
        with self.lock:
            tmp = self.path + ".tmp"
            try:
                d = os.path.dirname(self.path) or "."
                os.makedirs(d, exist_ok=True)
                with open(tmp, "w") as f:
                    f.write(data)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp, self.path)
                fd = os.open(d, os.O_RDONLY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
            except OSError as e:
                log(f"session: can't save {self.path} ({e})")


def _turns(rec):
    """{k: d} if a frame's input is only turns, else None."""
    out = {}
    for tok in rec.split():
        if tok[0] != "t":
            return None
        k = int(tok[1])
        out[k] = out.get(k, 0) + int(tok[2:])
    return out


def merge_turns(records):
    """Adjacent frames of nothing but turns, one frame where no knob changes direction. Exact for a
    pattern that adds turns to a value and clamps or wraps it; one that steps once per frame of
    input, whatever its size, takes fewer steps."""
    out, acc = [], None
    for rec in records:
        t = _turns(rec)
        if t is not None and acc is not None and all(acc.get(k, d) * d > 0 for k, d in t.items()):
            for k, d in t.items():
                acc[k] = acc.get(k, 0) + d
            continue
        if acc is not None:
            out.append(" ".join(f"t{k}{d:+d}" for k, d in sorted(acc.items())))
            acc = None
        if t is not None and t and all(t.values()):
            acc = t
        else:
            out.append(rec)
    if acc is not None:
        out.append(" ".join(f"t{k}{d:+d}" for k, d in sorted(acc.items())))
    return out


def trim(records):
    """Keep a demo's input to MAX_RECORDS frames: merge runs of turns, then, if still over, the oldest go."""
    if len(records) <= MAX_RECORDS:
        return records
    records = merge_turns(records)
    return records[-MAX_RECORDS:]


def apply(demo, rec, held):
    """One frame's input, into a demo. `held` is the knobs' up/down during the replay, for rt.held()."""
    for tok in rec.split():
        try:
            c = tok[0]
            if c == "t":
                demo.turn(int(tok[1]), int(tok[2:]))
            elif c == "p":
                held[int(tok[1])] = True
                demo.press(int(tok[1]))
            elif c == "r":
                held[int(tok[1])] = False
                demo.release(int(tok[1]), tok.endswith("c"))
            elif c == "s":
                demo.skip(int(tok[1:]))
        except (ValueError, IndexError):
            continue                    # a token from another version: leave it
