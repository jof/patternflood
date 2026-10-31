"""Patternflow's community patterns (community.patternflow.work), on their own shelf.

upstream_host/community.py fetches the wall (`sync`, on a PC). Patterns with a firmware
header are compiled, each into its own library, and run as an upstream preset runs
(pfd/upstream.py). The JavaScript-only ones run under node, in upstream's own harness
(upstream_host/jsrun.mjs, one child process for them all). Each comes as published, at
its own canvas, centred (turned upright if community.py's TURN says it lies on its side),
and most also at 128 x 128: the same code given the bigger square, or our port of it. Two
shelves: COMMUNITY shows each at its best, as community_review.json chose, and COMMUNITY
1:1 shows them all as published, with only the mechanical fixups. COMMUNITY is most liked
first, and COMMUNITY 1:1 newest first, so what a pull brings leads it. Our own patterns for
the wall (upstream_host/originals/) go on the PATTERNFLOOD shelf instead, at 128 x 128. With
nothing synced, the shelves aren't there. Node runs only sandboxed, with no network (see
jsrun.mjs); where that can't be arranged, the shelves hold just the compiled ones.
"""
import ctypes
import importlib.util
import json
import os
import re
import select
import signal
import subprocess
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from .draw import N
from .io import log
from . import session
from .runtime import Demo
from .upstream import BUILD, Upstream, knobs_blurb, open_lib

# Past these, the node process is taken to be stuck, and restarted. A first frame gets as long as a load:
# some patterns do their warming up in it (CALM TURING takes 1.05 s for its first on a Pi 5, then 6-10 ms).
LOAD_S, FRAME_S = 5.0, 1.0
LOST = object()                         # JSHost.poll: no reply is coming for that pattern; ask again


def _builder():
    spec = importlib.util.spec_from_file_location("pf_community_build", BUILD / "community.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class JSHost:
    """The node process the JavaScript patterns share: JSON lines in, a JSON line and RGB bytes out.

    Loads are calls. Frames are pipelined: a pattern sends its request and picks the reply up
    on a later tick (poll), so the runtime's loop keeps its 60 Hz while node draws. A heavy
    pattern just updates less often. One request is in flight at a time."""

    def __init__(self, argv):
        self.argv = argv            # community.py's node_argv(): sandboxed, no network
        self.proc = None
        self.generation = 0         # bumped on every restart: patterns load themselves again
        self.inflight = None        # (key, nbytes, deadline) of the frame node is drawing

    def _start(self):
        # A session of its own, so stop() can kill all of it: under bwrap (Ubuntu) node is bwrap's
        # child, and killing bwrap alone leaves node running.
        self.proc = subprocess.Popen(self.argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0,
                                     start_new_session=True)
        self.buf = b""
        self.inflight = None
        self.generation += 1

    def stop(self):
        if self.proc:
            try:
                os.killpg(self.proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            self.proc.wait()
            self.proc = None
        self.inflight = None

    def _fill(self, wait):
        """Whatever node has written, waiting up to WAIT seconds for some."""
        fd = self.proc.stdout.fileno()
        if select.select([fd], [], [], max(0.0, wait))[0]:
            chunk = os.read(fd, 1 << 16)
            if not chunk:
                raise EOFError
            self.buf += chunk

    def _reply(self, nbytes):
        """A whole reply from the buffer -> (reply, bytes), or None if it isn't all here yet."""
        end = self.buf.find(b"\n")
        if end < 0:
            return None
        reply = json.loads(self.buf[:end])
        n = nbytes if reply.get("ok") else 0
        if len(self.buf) < end + 1 + n:
            return None
        data, self.buf = self.buf[end + 1:end + 1 + n], self.buf[end + 1 + n:]
        return reply, data

    def _wait(self, nbytes, deadline):
        while True:
            got = self._reply(nbytes)
            if got:
                return got
            left = deadline - time.monotonic()
            if left <= 0:
                raise TimeoutError
            self._fill(left)

    def _failed(self, e, what):
        log(f"community: node {'stuck' if isinstance(e, TimeoutError) else 'gone'} ({what}); restarting it")
        self.stop()

    def _drain(self):
        """Finish the frame in flight, whoever it was for, and drop it."""
        if self.inflight:
            key, nbytes, deadline = self.inflight
            self.inflight = None
            self._wait(nbytes, deadline)

    def call(self, req, nbytes=0, timeout=FRAME_S):
        """-> (reply, bytes), waiting for it; restarts node and raises if it's stuck or gone."""
        if not self.proc:
            self._start()
        try:
            self._drain()
            self.proc.stdin.write((json.dumps(req) + "\n").encode())
            return self._wait(nbytes, time.monotonic() + timeout)
        except (TimeoutError, EOFError, BrokenPipeError, ValueError) as e:
            self._failed(e, f"{req['op']} {req['key']}")
            raise

    def send(self, req, nbytes, timeout=FRAME_S):
        """Start a frame; its reply comes from poll()."""
        if not self.proc:
            self._start()
        try:
            self._drain()
            self.proc.stdin.write((json.dumps(req) + "\n").encode())
            self.inflight = (req["key"], nbytes, time.monotonic() + timeout)
        except (TimeoutError, EOFError, BrokenPipeError, ValueError) as e:
            self._failed(e, f"{req['op']} {req['key']}")
            raise

    def poll(self, key):
        """KEY's frame -> (reply, bytes) once it's here, None while node is still drawing it, or
        LOST if none is coming (another pattern's request took its place, or node restarted).
        Raises, after restarting node, if the frame is past its deadline."""
        if not self.inflight or self.inflight[0] != key:
            return LOST
        _, nbytes, deadline = self.inflight
        try:
            self._fill(0)
            got = self._reply(nbytes)
            if got:
                self.inflight = None
                return got
            if time.monotonic() > deadline:
                raise TimeoutError
            return None
        except (TimeoutError, EOFError, ValueError) as e:
            self._failed(e, f"frame {key}")
            raise


class JSPattern(Upstream):
    """A JavaScript-only pattern: Upstream's knobs, lights and output stage, with node drawing.

    Each step collects the frame node has finished, if it has, and sends the next with the
    time since the last: a pattern node can't draw at 60 fps runs slower but in real time,
    and the knobs and the menu stay at the loop's rate."""
    host = None
    file = None
    matrix = None                       # (w, h) to override the script's @matrix: its 128 x 128 version
    SLOW_FPS = 50                       # log a pattern's frame rate once, if it's under this

    def __init__(self, rt):
        Demo.__init__(self, rt)
        self.deltas = (ctypes.c_int * 4)()
        self.pressed = (ctypes.c_uint8 * 4)()
        self.t_touch = [-10.0] * 4
        self.frame = np.zeros((N, N, 3), np.float32)
        self.failed = False
        self.waiting = False            # a frame of ours is in flight
        self.elapsed = 0.0              # time since our last request: the next one's dt
        self.frames, self.t_shown, self.rate_logged = 0, 0.0, False     # for the one-off frame-rate log
        self.replaying = deque()        # saved input still to send (pfd.session), a frame of it per request
        self._load()

    def replay(self, records):
        """node draws in its own time, so the saved input goes with the next requests instead. Runs of
        turns go as one: live, node gets whatever piled up while it drew, so that's no different."""
        self.replaying.extend(session.merge_turns(records))

    def _load(self):
        self.generation = self.host.generation
        self.waiting = False
        try:
            req = {"op": "load", "key": self.key, "file": str(self.file)}
            if self.matrix:
                req["matrix"] = list(self.matrix)
            info, _ = self.host.call(req, timeout=LOAD_S)
        except Exception:
            info = {"ok": False, "error": "node"}
        if not info.get("ok"):
            log(f"community: {self.name}: {info.get('error')}")
            self.failed = True
            return
        self.w, self.h = info["w"], info["h"]
        self.generation = self.host.generation
        self.fresh = True

    def step(self, dt):
        if self.failed:
            return
        self.elapsed += dt
        self.t_shown += dt
        if self.generation != self.host.generation:        # node restarted since: start over
            self._load()
            if self.failed:
                return
        if self.waiting:
            try:
                got = self.host.poll(self.key)
            except Exception:
                self.failed = True      # it hung node, or node died under it: once is enough
                return
            if got is None:
                return                  # still drawing: the last frame stays up
            self.waiting = False
            if got is not LOST and not self._show(*got):
                return
        if self.replaying and not any(self.deltas) and not any(self.pressed):
            session.apply(self, self.replaying.popleft(), [False] * 4)
        req = {"op": "frame", "key": self.key, "dt": self.elapsed, "d": list(self.deltas), "p": list(self.pressed),
               "h": [int(self.rt.held(k)) for k in range(4)]}
        try:
            self.host.send(req, self.w * self.h * 3, timeout=LOAD_S if self.fresh else FRAME_S)
        except Exception:
            self.failed = True
            return
        for k in range(4):
            self.deltas[k] = self.pressed[k] = 0
        self.elapsed, self.fresh, self.waiting = 0.0, False, True

    def _show(self, reply, data):
        """A finished frame onto the panel -> False if there's nothing more to ask for this step."""
        if reply.get("error") == "not loaded":                # node let it go to make room: start over
            self._load()
            return False
        if not reply.get("ok"):
            log(f"community: {self.name}: {reply.get('error')}")
            self.failed = True
            return False
        self.present(np.frombuffer(data, np.uint8).reshape(self.h, self.w, 3))
        self.frames += 1
        if not self.rate_logged and self.t_shown >= 5.0:
            self.rate_logged = True
            fps = self.frames / self.t_shown
            if fps < self.SLOW_FPS:
                log(f"community: {self.name} draws at {fps:.0f} fps (node)")
        return True


def _js_knobs(code):
    """knobs_blurb's text from a script's `// @knobs Name=lo..hi, ...` line (upstream's lib/pattern/knobs.ts)."""
    m = re.search(r"^[ \t]*//[ \t]*@knobs[ \t]+(.+)$", code, re.M)
    if not m:
        return ""
    names = [part.split("=")[0].strip() for part in m.group(1).split(",")[:4]]
    named = [(k, n) for k, n in enumerate(names) if n and n != "-"]
    return " " + ", ".join(f"k{k} {n[:14]}" for k, n in named) + "." if named else ""


class Original(Upstream):
    """One of ours. Lit by the pattern itself where it has knobLights() (community.py's pf_lights).
    It keeps its own time: the menu's audio knobs leave it alone. The Audio shelf's copy (`listens`)
    hears the beat tracker through hostAudio() instead (pf_audio), and its k0 click taps the tempo."""
    audio_knobs_ok = False
    listens = False
    TAP_FLASH_S = 0.25

    def __init__(self, rt):
        super().__init__(rt)
        self.has_lights = hasattr(self.lib, "pf_lights")
        self.light_buf = (ctypes.c_float * 12)()
        self.feeds = self.listens and hasattr(self.lib, "pf_audio")
        self.audio_buf = (ctypes.c_float * 6)()
        self.t_tap = -10.0

    def press(self, k):
        if self.feeds and k == 0:
            if self.rt.audio_in is not None and not self.rt.replaying:
                self.rt.audio_in.tap()          # the tracker takes three taps or more, and holds them 8 s
            self.t_tap = self.t_touch[0] = self.rt.t
            return
        super().press(k)

    def step(self, dt):
        if self.feeds:
            a, b = self.rt.audio, self.audio_buf
            b[0] = 1.0 if a.live else 0.0
            b[1], b[2], b[3], b[4] = a.bpm or 120.0, a.phase, a.beat_in_bar, a.level
            b[5] = 1.0 if a.drop else 0.0
            self.lib.pf_audio(b)
        super().step(dt)

    def lights(self):
        if not self.has_lights:
            return super().lights()
        self.lib.pf_lights(self.light_buf)
        b = self.light_buf
        out = [(b[3 * k], b[3 * k + 1], b[3 * k + 2]) for k in range(4)]
        tap = max(0.0, 1 - (self.rt.t - self.t_tap) / self.TAP_FLASH_S)
        if tap:                                 # white on a tap
            out[0] = tuple(min(1.0, c + tap) for c in out[0])
        return out


def _originals(cm):
    """Our own patterns for the wall (upstream_host/originals/) -> (ours, audio): on the PATTERNFLOOD shelf
    at 128 x 128, keeping their own time; and, for a header with hostAudio(), a copy on the AUDIO shelf
    playing to the music. (As written, for the wall, they're for `community.py twin`.)"""
    try:
        built = cm.originals(log=log)
    except Exception as e:
        log(f"community: originals: {e!r}")
        return [], []
    shelves = {"patternflood": [], "audio": []}
    for e, paths in built:
        for shelf, name, about in (("patternflood", "big", " At 128 x 128, in its own time."),
                                   ("audio", "audio", " Playing to the music: the beat tracker's tempo and "
                                    "beats, a drop is a break, loudness adds jive. k0 half, straight or double "
                                    "time; click k0 to tap the tempo.")):
            if name not in paths:
                continue
            try:
                lib = open_lib(paths[name])
            except OSError as err:
                log(f"community: {e['title']} ({name}): {err}")
                continue
            blurb = f"Ours, for the community wall (originals/{e['id']}.js).{about}"
            if name != "audio":
                blurb += knobs_blurb(lib, 0)
            shelves[shelf].append(
                type(f"PFO_{e['id']}_{name}", (Original,), {"lib": lib, "index": 0, "name": e["title"],
                                                             "group": shelf, "blurb": blurb,
                                                             "listens": name == "audio"}))
    return shelves["patternflood"], shelves["audio"]


def demos():
    """The community's patterns, twice: the COMMUNITY shelf (each at its best: its 128 x 128 version
    where the review chose one, else as published) and COMMUNITY 1:1 (all as published); then our
    originals for the wall. [] if none have been synced."""
    cm = _builder()
    if not (cm.SRC / "index.json").exists():
        return []
    try:
        with ThreadPoolExecutor(1) as ex:
            probe = ex.submit(cm._sandbox)          # node starts slowly from a cold card: probe it meanwhile
            built = cm.build(log=log)
            probe.result()
        serve = cm.node_argv(["serve", cm.SRC])
        scripts = cm.js_patterns() if serve else []
    except Exception as e:              # a broken cache costs the shelf, not the box
        log(f"community: {e!r}; running without community patterns")
        return []
    if not serve:
        log("community: no JavaScript-only patterns: they need node, with its permission model, and unshare or bwrap")
    out = []                            # (entry, {version: (attrs, knobs blurb)})
    for e, paths in built:
        versions = {}
        for name, path in paths.items():
            try:
                lib = open_lib(path)
            except OSError as err:
                log(f"community: {e['title']} ({name}): {err}")
                continue
            versions[name] = ({"lib": lib, "index": 0}, knobs_blurb(lib, 0))
        if versions:
            out.append((e, versions))
    host = JSHost(serve) if scripts else None
    for e, specs in scripts:
        out.append((e, {name: ({"host": host, "file": s["file"], "matrix": s["matrix"], "key": f"{e['id']}:{name}"},
                               _js_knobs(s["file"].read_text(errors="replace")))
                        for name, s in specs.items()}))
    n_big = sum("big" in v for _, v in out)
    log(f"community: {len(built)} compiled and {len(scripts)} JavaScript patterns, {n_big} shown at 128 x 128")
    out.sort(key=lambda o: -o[0]["likes"])
    chosen = cm.review()
    best, as_published = [], []
    for e, versions in out:
        by = f" by @{e['author']}" if e["author"] else ""
        port = f", ported by @{e['ported_by']}" if e.get("ported_by") else ""
        for shelf, name in (("community", "big" if "big" in versions else "native"), ("community-1to1", "native")):
            if name not in versions:
                continue
            attrs, knobs = versions[name]
            attrs = dict(attrs, name=e["title"], group=shelf, turn_upright=e["id"] in (cm.TURN if name == "native" else cm.BIG_TURN))
            js = " In JavaScript." if "host" in attrs else ""
            size = (" Enlarged for this panel." if chosen.get(e["id"]) == "port" else " At 128 x 128.") \
                if name == "big" else ""
            attrs["blurb"] = f"Community pattern{by}{port}.{js}{size}{knobs}"
            cls = type(f"PFC_{e['id']}_{name}", (JSPattern if "host" in attrs else Upstream,), attrs)
            best.append(cls) if shelf == "community" else as_published.append((e.get("created") or "", cls))
    # COMMUNITY 1:1 newest first, so a pull's arrivals lead it (same day: most liked first, as sorted above)
    as_published = [cls for _, cls in sorted(as_published, key=lambda p: p[0], reverse=True)]
    return as_published + best + sum(_originals(cm), [])
