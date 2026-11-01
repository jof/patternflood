"""The web remote: the panel, the knobs, the buttons and every shelf, in a browser.

    ./run.py --web :8080                     # then http://localhost:8080/
    ./run.py --web :8080 --out none --knobs none     # no hardware at all: the browser is the box

On the box it listens on port 80 (patternflood.service, PF_WEB), so http://patternflood.local/
works from a phone on the same network. It has no login: anyone who can reach it can play.

A plain HTTP server (the standard library's, on threads of its own), so the box needs nothing
more installed. The frame loop never waits on it:

  - input from the page goes into a queue, which the runtime drains each frame (`poll`) and
    feeds through the same path as the knobs and buttons, so the session keeps it too;
  - while a page is watching, the runtime hands over each frame it showed (`publish`), as the
    eye sees it (before the panel's gamma and brightness), with the knob lights and its state;
    each page's own thread compresses the newest one and sends it, dropping what it missed.

A demo that has been on for a few seconds, with no menu or banner over it, leaves a picture of
itself for the page's shelves (`thumbs/`, in the renderer's cache directory).

    GET  /                    the page (pfd/web_static/)
    GET  /api/demos           the shelves and their demos, and which have pictures
    GET  /api/state           what's on, the menu, sleep, brightness, frame rate, ...
    GET  /api/stream          frames, as they're shown (below); ?fps=N, at most 60
    GET  /api/label?s=TEXT    TEXT in the panel's own bitmap font
    GET  /thumbs/N.png        demo N's picture
    POST /api/cmd             one command, or a list: {"op": "turn", "k": 0, "d": 1}, down/up (k),
                              bdown/bup (b, the buttons: 0 previous, 1 select, 2 next, 3 sleep),
                              goto (i), bright (v, 0..1), audio_knobs (on), sleep, wake

The stream is gzip (as Content-Encoding, flushed after each frame, so the browser inflates it
as it comes). Each record is a little-endian u32 n, then n bytes of state as JSON (n is 0 when
the state hasn't changed since the last record), then the frame, 128 x 128 RGB bytes, rows
top first, then the four knob lights, RGB bytes.
"""
import json
import os
import queue
import socket
import struct
import threading
import time
import urllib.parse
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

from .io import log

STATIC = Path(__file__).with_name("web_static")
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon"}
HELD_MAX_S = 60.0       # a knob or button the page pushed and never let go (the page closed): let go
STREAM_FPS = 30
QUEUE_MAX = 512


def default_thumbs():
    """$CACHE_DIRECTORY/thumbs on the box (systemd's CacheDirectory), else ~/.cache/patternflood/thumbs."""
    cache = os.environ.get("CACHE_DIRECTORY")
    base = Path(cache.split(":")[0]) if cache else Path.home() / ".cache/patternflood"
    return base / "thumbs"


def png(rgb):
    """An RGB uint8 (h, w, 3) array as PNG bytes, without Pillow."""
    h, w = rgb.shape[:2]
    raw = b"".join(b"\0" + rgb[y].tobytes() for y in range(h))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def thumb_name(key):
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in key) + ".png"


class Web:
    """The server, and the runtime's side of it."""

    def __init__(self, spec, demos, thumbs=None):
        host, _, port = spec.rpartition(":")
        self.addr = (host or "", int(port or 80))
        self.demos = demos
        self.keys = [f"{d.group}/{d.__name__}" for d in demos]
        self.cmds = queue.Queue(QUEUE_MAX)
        self.cv = threading.Condition()
        self.seq = 0                    # frames published
        self.frame = self.lights = None
        self.state_json, self.state_seq = b"{}", 0
        self.watchers = 0
        self.t_asked = -10.0            # when /api/state was last asked for (it wants a frame's state too)
        self.t_published = 0.0
        self.thumbs_dir = Path(thumbs) if thumbs else default_thumbs()
        self.thumbs = {}                # demo index -> mtime of its picture
        self.thumb_rev = 0
        self.thumbed = set()            # demos pictured since we started
        self.held = {}                  # ("k"|"b", n) -> when the page pushed it
        self.labels = {}
        self._scan_thumbs()
        self.catalog = self._catalog()
        handler = type("Handler", (_Handler,), {"web": self})
        self.server = _Server(self.addr, handler)
        threading.Thread(target=self.server.serve_forever, daemon=True, name="web").start()
        log(f"web: http://{socket.gethostname()}{'' if self.addr[1] == 80 else f':{self.addr[1]}'}/ "
            f"(listening on {self.addr[0] or '*'}:{self.server.server_address[1]})")

    # ---- the runtime's side

    def poll(self, now):
        """The page's commands since the last frame; and lets go of anything it's held too long."""
        out = []
        while True:
            try:
                out.append(self.cmds.get_nowait())
            except queue.Empty:
                break
        for c in out:
            op = c.get("op")
            if op in ("down", "bdown"):
                self.held[(op[0], c.get("k", c.get("b")))] = now
            elif op in ("up", "bup"):
                self.held.pop(("d" if op == "up" else "b", c.get("k", c.get("b"))), None)
        for (kind, n), t in list(self.held.items()):
            if now - t > HELD_MAX_S:
                del self.held[(kind, n)]
                out.append({"op": "up", "k": n} if kind == "d" else {"op": "bup", "b": n})
                log(f"web: {'knob' if kind == 'd' else 'button'} {n} held {HELD_MAX_S:.0f} s from a page: let go")
        return out

    def wants(self, now, fps=STREAM_FPS):
        """Is a page watching, and due another frame?"""
        return ((self.watchers > 0 or now - self.t_asked < 1.0)
                and now - self.t_published >= 1.0 / fps * 0.9)

    def publish(self, now, rgb, lights, state):
        """rgb: uint8 (128, 128, 3) as the eye sees it; lights: four 0..1 (r, g, b); state: a dict."""
        js = json.dumps(state, separators=(",", ":")).encode()
        lit = bytes(int(min(1.0, max(0.0, c)) * 255 + 0.5) for rgb_ in lights[:4] for c in rgb_)
        lit = lit.ljust(12, b"\0")
        with self.cv:
            if js != self.state_json:
                self.state_json, self.state_seq = js, self.seq + 1
            self.frame, self.lights = rgb, lit
            self.seq += 1
            self.t_published = now
            self.cv.notify_all()

    def maybe_thumb(self, index, rgb):
        """Keep a picture of demo `index` (no overlay on rgb), once a run."""
        if index in self.thumbed:
            return
        self.thumbed.add(index)
        threading.Thread(target=self._save_thumb, args=(index, rgb.copy()), daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()

    # ---- the server's side

    def _scan_thumbs(self):
        try:
            have = {p.name: p.stat().st_mtime for p in self.thumbs_dir.glob("*.png")}
        except OSError:
            have = {}
        self.thumbs = {i: int(have[thumb_name(k)]) for i, k in enumerate(self.keys) if thumb_name(k) in have}

    def _save_thumb(self, index, rgb):
        path = self.thumbs_dir / thumb_name(self.keys[index])
        try:
            self.thumbs_dir.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_bytes(png(rgb))
            os.replace(tmp, path)
        except OSError as e:
            log(f"web: can't keep a picture in {self.thumbs_dir} ({e})")
            return
        self.thumbs[index] = int(time.time())
        self.thumb_rev += 1

    def _catalog(self):
        from .runtime import SHELF_NAMES
        shelves = list(dict.fromkeys(d.group for d in self.demos))
        return {"shelves": [{"group": g, "name": SHELF_NAMES.get(g, g.upper()),
                             "count": sum(d.group == g for d in self.demos)} for g in shelves],
                "demos": [{"i": i, "name": d.name, "blurb": d.blurb, "group": d.group, "key": k,
                           "audio": bool(d.audio_knobs_ok)} for i, (d, k) in enumerate(zip(self.demos, self.keys))]}

    def label(self, s):
        """s in the panel's bitmap font: {"w", "h", "rows": ["0110...", ...]}."""
        s = s[:64]
        if s not in self.labels:
            from . import draw
            try:
                m = draw._mask(s)
            except Exception:           # a character the font can't draw
                m = np.zeros((1, 1), np.float32)
            ink = np.flatnonzero(m.max(1) > 0.5)
            if len(ink):
                m = m[ink[0]:ink[-1] + 1]         # no blank rows above or below
            rows = ["".join("1" if v > 0.5 else "0" for v in row) for row in m]
            if len(self.labels) > 2048:
                self.labels.clear()
            self.labels[s] = {"w": int(m.shape[1]), "h": int(m.shape[0]), "rows": rows}
        return self.labels[s]

    def command(self, c):
        if not isinstance(c, dict) or not isinstance(c.get("op"), str):
            raise ValueError("a command is an object with an op")
        op = c["op"]
        ints = {"turn": ("k", "d"), "down": ("k",), "up": ("k",), "bdown": ("b",), "bup": ("b",), "goto": ("i",)}
        for f in ints.get(op, ()):
            if not isinstance(c.get(f), int) or isinstance(c.get(f), bool):
                raise ValueError(f"{op} needs an integer {f}")
        if op in ("turn", "down", "up") and not 0 <= c["k"] < 4:
            raise ValueError("k is 0..3")
        if op in ("bdown", "bup") and not 0 <= c["b"] < 4:
            raise ValueError("b is 0..3")
        if op == "turn" and not -48 <= c["d"] <= 48:
            raise ValueError("d is -48..48")
        if op == "goto" and not 0 <= c["i"] < len(self.demos):
            raise ValueError(f"i is 0..{len(self.demos) - 1}")
        if op == "bright" and not isinstance(c.get("v"), (int, float)):
            raise ValueError("bright needs a number v")
        if op not in ints and op not in ("bright", "audio_knobs", "sleep", "wake"):
            raise ValueError(f"no such op {op!r}")
        try:
            self.cmds.put_nowait(c)
        except queue.Full:
            raise ValueError("too many commands at once") from None


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        pass                            # a page that went away mid-stream


class _Handler(BaseHTTPRequestHandler):
    web = None
    protocol_version = "HTTP/1.1"
    server_version = "patternflood"

    def log_message(self, *a):
        pass

    def _send(self, body, ctype="application/json", status=200, cache="no-store"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        q = urllib.parse.parse_qs(url.query)
        path = url.path
        w = self.web
        if path == "/api/stream":
            return self._stream(q)
        if path == "/api/demos":
            w._scan_thumbs()            # pictures copied in while it runs (tools/thumbs.py) count too
            return self._send(dict(w.catalog, thumbs=w.thumbs))
        if path == "/api/thumbs":
            w._scan_thumbs()
            return self._send({"rev": w.thumb_rev, "thumbs": w.thumbs})
        if path == "/api/state":
            with w.cv:
                w.t_asked = time.monotonic()
                seq = w.seq
                w.cv.wait_for(lambda: w.seq != seq, timeout=1.0)    # the next frame's
                return self._send(w.state_json)
        if path == "/api/label":
            return self._send(w.label(q.get("s", [""])[0]), cache="max-age=86400")
        if path.startswith("/thumbs/") and path.endswith(".png"):
            try:
                i = int(path[8:-4])
                data = (w.thumbs_dir / thumb_name(w.keys[i])).read_bytes()
            except (ValueError, IndexError, OSError):
                return self._send({"error": "no picture of that demo yet"}, status=404)
            return self._send(data, "image/png", cache="max-age=60")
        name = "index.html" if path == "/" else path.lstrip("/")
        f = (STATIC / name).resolve()
        if f.parent != STATIC.resolve() or not f.is_file() or f.suffix not in TYPES:
            return self._send({"error": f"nothing at {path}"}, status=404)
        return self._send(f.read_bytes(), TYPES[f.suffix], cache="no-cache")

    def do_POST(self):
        if urllib.parse.urlsplit(self.path).path != "/api/cmd":
            return self._send({"error": "POST /api/cmd"}, status=404)
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n > 65536:
                raise ValueError("too long")
            body = json.loads(self.rfile.read(n) or b"null")
            for c in body if isinstance(body, list) else [body]:
                self.web.command(c)
        except (ValueError, TypeError) as e:
            return self._send({"error": str(e)}, status=400)
        return self._send({"ok": True})

    def _stream(self, q):
        w = self.web
        try:
            fps = min(60.0, max(1.0, float(q.get("fps", [STREAM_FPS])[0])))
        except ValueError:
            fps = STREAM_FPS
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Encoding", "gzip")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        self.close_connection = True
        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        z = zlib.compressobj(1, zlib.DEFLATED, 31)
        seen, state_sent = 0, -1
        with w.cv:
            w.watchers += 1
        try:
            while True:
                t0 = time.monotonic()
                with w.cv:
                    if not w.cv.wait_for(lambda: w.seq != seen, timeout=5):
                        continue                    # the loop is busy elsewhere (a long compile, say)
                    seen, frame, lights = w.seq, w.frame, w.lights
                    js = w.state_json if w.state_seq > state_sent else b""
                    if js:
                        state_sent = w.state_seq
                rec = struct.pack("<I", len(js)) + js + frame.tobytes() + lights
                self.wfile.write(z.compress(rec) + z.flush(zlib.Z_SYNC_FLUSH))
                self.wfile.flush()
                time.sleep(max(0.0, 1.0 / fps - (time.monotonic() - t0)))
        except OSError:
            pass
        finally:
            with w.cv:
                w.watchers -= 1
