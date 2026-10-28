"""Patternflow's community patterns (community.patternflow.work), on their own shelf.

upstream_host/community.py fetches the wall (`sync`, on ash). Patterns with a firmware
header are compiled, each into its own library, and run as an upstream preset runs
(pfd/upstream.py). The JavaScript-only ones run under node, in upstream's own harness
(upstream_host/jsrun.mjs, one child process for them all). Each runs at its own canvas,
centred. Most liked first. With nothing synced, the shelf isn't there. Node runs only
sandboxed, with no network (see jsrun.mjs); where that can't be arranged, the shelf holds
just the compiled ones.
"""
import ctypes
import importlib.util
import json
import os
import re
import select
import subprocess
import time

import numpy as np

from .draw import N
from .io import log
from .runtime import Demo
from .upstream import BUILD, Upstream, knobs_blurb, open_lib

# Past these, the node process is taken to be stuck, and restarted. A first frame gets as long as a load:
# some patterns do their warming up in it (CALM TURING takes 1.05 s for its first on a Pi 5, then 6-10 ms).
LOAD_S, FRAME_S = 5.0, 1.0


def _builder():
    spec = importlib.util.spec_from_file_location("pf_community_build", BUILD / "community.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class JSHost:
    """The node process the JavaScript patterns share: JSON lines in, a JSON line and RGB bytes out."""

    def __init__(self, argv):
        self.argv = argv            # community.py's node_argv(): sandboxed, no network
        self.proc = None
        self.generation = 0         # bumped on every restart: patterns load themselves again

    def _start(self):
        self.proc = subprocess.Popen(self.argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0)
        self.buf = b""
        self.generation += 1

    def stop(self):
        if self.proc:
            self.proc.kill()
            self.proc.wait()
            self.proc = None

    def _read(self, n, deadline):
        """Exactly n bytes, or a line if n is None, before the deadline."""
        fd = self.proc.stdout.fileno()
        while (n is None and b"\n" not in self.buf) or (n is not None and len(self.buf) < n):
            left = deadline - time.monotonic()
            if left <= 0 or not select.select([fd], [], [], left)[0]:
                raise TimeoutError
            chunk = os.read(fd, 1 << 16)
            if not chunk:
                raise EOFError
            self.buf += chunk
        if n is None:
            n = self.buf.index(b"\n") + 1
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def call(self, req, nbytes=0, timeout=FRAME_S):
        """-> (reply, bytes); restarts node and raises if it's stuck or gone."""
        if not self.proc:
            self._start()
        deadline = time.monotonic() + timeout
        try:
            self.proc.stdin.write((json.dumps(req) + "\n").encode())
            reply = json.loads(self._read(None, deadline))
            data = self._read(nbytes, deadline) if reply.get("ok") and nbytes else b""
            return reply, data
        except (TimeoutError, EOFError, BrokenPipeError, ValueError) as e:
            log(f"community: node {'stuck' if isinstance(e, TimeoutError) else 'gone'} ({req['op']} {req['key']}); restarting it")
            self.stop()
            raise


class JSPattern(Upstream):
    """A JavaScript-only pattern: Upstream's knobs, lights and output stage, with node drawing."""
    host = None
    file = None

    def __init__(self, rt):
        Demo.__init__(self, rt)
        self.deltas = (ctypes.c_int * 4)()
        self.pressed = (ctypes.c_uint8 * 4)()
        self.t_touch = [-10.0] * 4
        self.frame = np.zeros((N, N, 3), np.float32)
        self.failed = False
        self._load()

    def _load(self):
        self.generation = self.host.generation
        try:
            info, _ = self.host.call({"op": "load", "key": self.key, "file": str(self.file)}, timeout=LOAD_S)
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
        if self.generation != self.host.generation:        # node restarted since: start over
            self._load()
            if self.failed:
                return
        req = {"op": "frame", "key": self.key, "dt": dt, "d": list(self.deltas), "p": list(self.pressed),
               "h": [int(self.rt.held(k)) for k in range(4)]}
        for k in range(4):
            self.deltas[k] = self.pressed[k] = 0
        try:
            reply, data = self.host.call(req, self.w * self.h * 3, timeout=LOAD_S if self.fresh else FRAME_S)
            self.fresh = False
        except Exception:
            self.failed = True          # it hung node, or node died under it: once is enough
            return
        if reply.get("error") == "not loaded":                # node let it go to make room: start over
            self._load()
            return
        if not reply.get("ok"):
            log(f"community: {self.name}: {reply.get('error')}")
            self.failed = True
            return
        self.present(np.frombuffer(data, np.uint8).reshape(self.h, self.w, 3))


def _js_knobs(code):
    """knobs_blurb's text from a script's `// @knobs Name=lo..hi, ...` line (upstream's lib/pattern/knobs.ts)."""
    m = re.search(r"^[ \t]*//[ \t]*@knobs[ \t]+(.+)$", code, re.M)
    if not m:
        return ""
    names = [part.split("=")[0].strip() for part in m.group(1).split(",")[:4]]
    named = [(k, n) for k, n in enumerate(names) if n and n != "-"]
    return " " + ", ".join(f"k{k} {n[:14]}" for k, n in named) + "." if named else ""


def demos():
    """One Demo class per community pattern that will run, or [] if none have been synced."""
    cm = _builder()
    if not (cm.SRC / "index.json").exists():
        return []
    try:
        built = cm.build(log=log)
        serve = cm.node_argv(["serve", cm.SRC])
        scripts = cm.js_patterns() if serve else []
    except Exception as e:              # a broken cache costs the shelf, not the box
        log(f"community: {e!r}; running without community patterns")
        return []
    if not serve:
        log("community: no JavaScript-only patterns: they need node, with its permission model, and unshare or bwrap")
    out = []
    for e, path in built:
        try:
            lib = open_lib(path)
        except OSError as err:
            log(f"community: {e['title']}: {err}")
            continue
        out.append((e, {"lib": lib, "index": 0}, knobs_blurb(lib, 0)))
    host = JSHost(serve) if scripts else None
    for e, path in scripts:
        out.append((e, {"host": host, "file": path, "key": e["id"]}, _js_knobs(path.read_text(errors="replace"))))
    log(f"community: {len(built)} compiled and {len(scripts)} JavaScript patterns")
    classes = []
    for e, attrs, knobs in sorted(out, key=lambda o: -o[0]["likes"]):
        by = f" by @{e['author']}" if e["author"] else ""
        port = f", ported by @{e['ported_by']}" if e.get("ported_by") else ""
        js = " In JavaScript." if "host" in attrs else ""
        attrs.update(name=e["title"], blurb=f"Community pattern{by}{port}.{js}{knobs}", group="community")
        classes.append(type(f"PFC_{e['id']}", (JSPattern if "host" in attrs else Upstream,), attrs))
    return classes
