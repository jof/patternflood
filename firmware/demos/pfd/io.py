"""Knob sources and frame sinks, so the same demos run on the bench and on the Pi.

Knob sources yield events:  ("turn", k, d)  ("down", k)  ("up", k)  ("hello", n),
with d > 0 for clockwise. The 4991's seesaw counts down when turned clockwise
(Adafruit's examples negate it too), so the hardware sources flip the sign.
and take knob lights as a list of (r, g, b) 0..255.

    serial:PORT    FeatherS3 knob_bridge on USB (bench)
    i2c[:BUS]      4991 seesaw boards on this host's I2C bus (Pi)
    auto[:SEED]    a random player, for previews and attract mode
    script:SPEC    timed gestures, e.g. "0.5:k0+12,1:k3 click,2:k1 down,3:k1 up,4:b1 click"
    none

Button sources yield ("bdown", b) and ("bup", b) for the box's four push buttons:

    gpio           the gpio-key overlay's devices (Pi)
    keys           the terminal: , . Enter s (bench)
    auto           gpio if there are any, else keys on a terminal
    none

Frame sinks take uint8 (128, 128, 3) frames, post-gamma, as receiver75 shows them:

    auto[:HOST]        udp if the card is on this host's own Ethernet, else pipe via HOST
    udp[:IP]           straight to the card (Pi, or any host on its link)
    pipe:HOST[:IP]     over ssh to a host on the card's link, which just forwards UDP
    preview:FILE.gif   an animated GIF, for checking a demo without the panels
"""
import base64
import json
import os
import queue
import random
import socket
import struct
import subprocess
import sys
import threading
import time
import zlib
from pathlib import Path

import numpy as np

import r75_frame


def log(*a):
    print(*a, file=sys.stderr, flush=True)


_notify = None


def sd_notify(msg):
    """Tell systemd (patternflood.service is Type=notify, with a watchdog) e.g. READY=1 or WATCHDOG=1.
    A no-op off the Pi, where there's no NOTIFY_SOCKET."""
    global _notify
    addr = os.environ.get("NOTIFY_SOCKET")
    if not addr:
        return
    if _notify is None:
        _notify = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        _notify.sendto(msg.encode(), "\0" + addr[1:] if addr[0] == "@" else addr)
    except OSError as e:
        log(f"sd_notify: {e}")


# ---------------------------------------------------------------- knob sources

class _QueueSource:
    def __init__(self):
        self.q = queue.Queue()
        self.n = 4

    def poll(self, t):
        out = []
        while True:
            try:
                out.append(self.q.get_nowait())
            except queue.Empty:
                return out

    def set_lights(self, rgbs):
        pass

    def close(self):
        pass


class SerialKnobs(_QueueSource):
    """knob_bridge JSON lines over USB serial; reopens the port if the FeatherS3 resets."""

    def __init__(self, port):
        super().__init__()
        import serial
        self.serial = serial
        self.port = port
        self.ser = None
        self.lock = threading.Lock()
        threading.Thread(target=self._reader, daemon=True).start()

    def _open(self):
        ser = self.serial.Serial()
        ser.port, ser.baudrate, ser.timeout = self.port, 115200, 0.2
        ser.dtr = ser.rts = False       # asserting these drops the FeatherS3 into download mode
        ser.open()
        return ser

    def _reader(self):
        buf = b""
        while True:
            if self.ser is None:
                try:
                    self.ser = self._open()
                    self.ser.write(b"scan\n")      # get a fresh hello with the knob list
                except (OSError, self.serial.SerialException) as e:
                    log(f"knobs: {self.port}: {e}; retrying")
                    time.sleep(1)
                    continue
            try:
                buf += self.ser.read(256)
            except (OSError, self.serial.SerialException) as e:
                log(f"knobs: lost {self.port} ({e})")
                self.ser = None
                continue
            *lines, buf = buf.split(b"\n")
            for line in lines:
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                t, k = ev.get("t"), ev.get("k")
                if t == "enc":
                    self.q.put(("turn", k, -ev["d"]))       # seesaw counts down clockwise
                elif t == "btn":
                    self.q.put(("down" if ev["down"] else "up", k))
                elif t == "hello":
                    self.n = len(ev["knobs"])
                    self.q.put(("hello", self.n))

    def set_lights(self, rgbs):
        cmd = "".join("px %d %02x%02x%02x\n" % (k, *c) for k, c in enumerate(rgbs))
        try:
            if self.ser:
                self.ser.write(cmd.encode())
        except (OSError, self.serial.SerialException):
            pass


class I2CKnobs(_QueueSource):
    """4991 seesaw encoders on a local I2C bus, polled; lights set over I2C."""
    POLL_S = 0.02                       # ~33 Hz with bus time: the seesaw counts detents, so this is only latency
    MAX_STEP = 24                       # bigger jumps between polls are bus glitches: resync

    def __init__(self, bus):
        super().__init__()
        self.bus, self.knobs, self.n, self.errors = bus, [], 0, 0
        # Found on the polling thread (resetting them takes half a second), so the first frames
        # needn't wait; "hello" says when they're there.
        threading.Thread(target=self._poll, daemon=True).start()

    def _find(self):
        import seesaw
        try:
            knobs = seesaw.find_encoders(self.bus)
        except OSError as e:
            log(f"knobs: I2C bus {self.bus} unavailable ({e}); running without knobs")
            knobs = []
        self.pos = [ss.position() for ss in knobs]
        self.down = [ss.pressed() for ss in knobs]
        self.knobs, self.n = knobs, len(knobs)
        self.q.put(("hello", self.n))

    def _poll(self):
        self._find()
        while True:
            for k, ss in enumerate(self.knobs):
                try:
                    p, d = ss.position(), ss.pressed()
                except OSError:
                    self.errors += 1
                    continue
                step = p - self.pos[k]
                if step and abs(step) <= self.MAX_STEP:
                    self.q.put(("turn", k, -step))          # seesaw counts down clockwise
                self.pos[k] = p
                if d != self.down[k]:
                    self.q.put(("down" if d else "up", k))
                    self.down[k] = d
            time.sleep(self.POLL_S)

    def set_lights(self, rgbs):
        for k, (r, g, b) in enumerate(rgbs[:self.n]):
            try:
                self.knobs[k].pixel(r, g, b)
            except OSError:
                self.errors += 1

    def close(self):
        self.set_lights([(0, 0, 0)] * self.n)


class ScriptKnobs:
    """Timed gestures. "T:kN+D" turns knob N by D detents over ~0.3 s; "T:kN click|down|up";
    "T:bN click|down|up" for button N."""

    def __init__(self, spec):
        self.n = 4
        self.events = [(0.0, ("hello", 4))]
        for item in filter(None, (s.strip() for s in spec.split(","))):
            t, what = item.split(":", 1)
            t = float(t)
            if " " in what:
                knob, act = what.split()
                k = int(knob[1:])
                down, up = ("bdown", "bup") if knob[0] == "b" else ("down", "up")
                if act == "click":
                    self.events += [(t, (down, k)), (t + 0.12, (up, k))]
                else:
                    self.events.append((t, (down if act == "down" else up, k)))
            else:
                sign = "+" if "+" in what else "-"
                knob, n = what.split(sign)
                k, n = int(knob[1:]), int(n)
                for i in range(n):
                    self.events.append((t + 0.3 * i / max(1, n), ("turn", k, 1 if sign == "+" else -1)))
        self.events.sort(key=lambda e: e[0])

    def poll(self, t):
        out = []
        while self.events and self.events[0][0] <= t:
            out.append(self.events.pop(0)[1])
        return out

    def set_lights(self, rgbs):
        self.lights = rgbs

    def close(self):
        pass


class AutoKnobs:
    """A restless player: bursts of turning, the odd click and hold. Seeded, so previews repeat."""

    def __init__(self, seed=1):
        self.n = 4
        self.rng = random.Random(seed)
        self.t_next = 0.0
        self.pending = [("hello", 4)]
        self.plan = []                  # (t, event)

    def poll(self, t):
        out, self.pending = self.pending, []
        if t >= self.t_next:
            r = self.rng
            k = r.randrange(4)
            roll = r.random()
            if roll < 0.75:
                n, sign, dur = r.randint(2, 18), r.choice((1, -1)), r.uniform(0.2, 1.2)
                self.plan += [(t + dur * i / n, ("turn", k, sign)) for i in range(n)]
            elif roll < 0.92:
                self.plan += [(t, ("down", k)), (t + 0.15, ("up", k))]
            else:
                hold = r.uniform(0.6, 2.0)
                self.plan += [(t, ("down", k)), (t + hold, ("up", k))]
            self.plan.sort(key=lambda e: e[0])
            self.t_next = t + r.uniform(0.3, 2.0)
        while self.plan and self.plan[0][0] <= t:
            out.append(self.plan.pop(0)[1])
        return out

    def set_lights(self, rgbs):
        self.lights = rgbs

    def close(self):
        pass


class NoKnobs(_QueueSource):
    def __init__(self):
        super().__init__()
        self.q.put(("hello", 0))


def knob_source(spec):
    kind, _, arg = spec.partition(":")
    if kind == "serial":
        return SerialKnobs(arg)
    if kind == "i2c":
        return I2CKnobs(int(arg or 1))
    if kind == "auto":
        return AutoKnobs(int(arg or 1))
    if kind == "script":
        return ScriptKnobs(arg)
    if kind == "none":
        return NoKnobs()
    raise SystemExit(f"unknown knob source {spec!r}")


# ---------------------------------------------------------------- button sources
#
# The box's four push buttons (docs/desktop/wiring.md §4), as events ("bdown", b) and ("bup", b).

BTN_0 = 0x100           # the gpio-key overlay gives btn0..btn3 the codes BTN_0..BTN_3: the console's
NBUTTONS = 4            # keyboard handler ignores codes from BTN_MISC (= BTN_0) up, so a press can't
                        # type at the HDMI login or switch VTs


class GpioButtons(_QueueSource):
    """The buttons as the kernel's gpio-keys devices, one per button (dtoverlay=gpio-key in
    config.txt), read from /dev/input. The kernel debounces them; the pull-ups are the Pi's own."""
    EV_KEY = 1
    EVENT = struct.Struct("llHHi")      # struct input_event: timeval, type, code, value
    REBOUND_S = 0.03                    # a press this soon after a release is the switch bouncing

    def __init__(self):
        super().__init__()
        self.fds = []
        for dev in sorted(Path("/sys/class/input").glob("event*")):
            if self._is_ours(dev):
                try:
                    self.fds.append(os.open(f"/dev/input/{dev.name}", os.O_RDONLY))
                except OSError as e:
                    log(f"buttons: /dev/input/{dev.name}: {e}")
        log(f"buttons: {len(self.fds)} found")
        if self.fds:
            threading.Thread(target=self._reader, daemon=True).start()

    @staticmethod
    def _is_ours(dev):
        try:
            if (dev / "device/device/driver").resolve().name != "gpio-keys":
                return False                # not the HDMI CEC remotes
            words = (dev / "device/capabilities/key").read_text().split()
        except OSError:
            return False
        bits = 8 * struct.calcsize("l")     # the kernel prints its key bitmap a long at a time, high first
        keys = sum(int(w, 16) << (bits * i) for i, w in enumerate(reversed(words)))
        return any(keys >> (BTN_0 + b) & 1 for b in range(NBUTTONS))     # not the Pi 5's power button

    def _reader(self):
        import select
        t_up = [0.0] * NBUTTONS
        while True:
            for fd in select.select(self.fds, [], [])[0]:
                data = os.read(fd, self.EVENT.size * 16)
                for _, _, typ, code, value in self.EVENT.iter_unpack(data):
                    b = code - BTN_0
                    if typ != self.EV_KEY or not 0 <= b < NBUTTONS or value == 2:
                        continue
                    if value:
                        if time.monotonic() - t_up[b] > self.REBOUND_S:
                            self.q.put(("bdown", b))
                    else:
                        t_up[b] = time.monotonic()
                        self.q.put(("bup", b))


class KeyButtons(_QueueSource):
    """The buttons on the terminal's keys, for the bench: , previous, Enter select, . next, s sleep."""
    KEYS = {",": 0, "\n": 1, " ": 1, ".": 2, "s": 3}

    def __init__(self):
        super().__init__()
        import atexit
        import termios
        import tty
        fd = sys.stdin.fileno()
        saved = termios.tcgetattr(fd)
        atexit.register(termios.tcsetattr, fd, termios.TCSADRAIN, saved)
        tty.setcbreak(fd)               # keys as they're typed, unechoed; Ctrl-C still stops us
        log("buttons: keys  , previous  Enter select  . next  s sleep")
        threading.Thread(target=self._reader, args=(fd,), daemon=True).start()

    def _reader(self, fd):
        while True:
            b = self.KEYS.get(os.read(fd, 1).decode(errors="ignore"))
            if b is not None:
                self.q.put(("bdown", b))
                self.q.put(("bup", b))


def button_source(spec):
    """gpio (the box's), keys (the terminal's), auto (gpio if there are any, else keys on a
    terminal), or none."""
    if spec == "none":
        return _QueueSource()
    if spec in ("gpio", "auto"):
        buttons = GpioButtons()
        if buttons.fds or spec == "gpio":
            return buttons
        return KeyButtons() if sys.stdin.isatty() else _QueueSource()
    if spec == "keys":
        return KeyButtons()
    raise SystemExit(f"unknown button source {spec!r}")


# ---------------------------------------------------------------- frame sinks

BLACK = np.zeros((128, 128, 3), np.uint8)


class UdpOut:
    """Double-buffered frames straight to receiver75 (Pi 5, or any host on the card's link)."""
    realtime = True

    def __init__(self, ip):
        self.ip = ip
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bank = 1
        self.t_enable = 0.0
        self.t_err = 0.0
        self.ready = self._send(self._blank)        # else again before each frame, until the link is up

    def _blank(self, s):
        for b in (0, 1):
            r75_frame.send_frame(s, self.ip, BLACK, blank_unused=True, bank=b)
        r75_frame.show_bank(s, self.ip, 0)
        r75_frame.enable(s, self.ip)

    def _send(self, fn):
        try:
            fn(self.sock)
            return True
        except OSError as e:
            if time.monotonic() - self.t_err > 10:
                log(f"send to {self.ip} failed: {e}; retrying")
                self.t_err = time.monotonic()
            return False

    def show(self, frame, lights=None):
        def go(s):
            r75_frame.send_frame(s, self.ip, frame, bank=self.bank)
            r75_frame.show_bank(s, self.ip, self.bank)
            if time.monotonic() - self.t_enable >= 1.0:     # receiver75 boots disabled
                r75_frame.enable(s, self.ip)
                self.t_enable = time.monotonic()
        if not self.ready:
            self.ready = self._send(self._blank)
        if self.ready and self._send(go):
            self.bank ^= 1

    def stats(self):
        return ""

    def close(self):
        self._send(lambda s: (r75_frame.send_frame(s, self.ip, BLACK, bank=0), r75_frame.show_bank(s, self.ip, 0)))


class _BufSock:
    """Looks like a UDP socket to r75_frame; packs datagrams as r75_pipe records."""

    def __init__(self):
        self.buf = bytearray()

    def sendto(self, data, addr):
        self.buf += struct.pack("<HH", addr[1], len(data)) + data


class PipeOut:
    """Frames over ssh to a host on the card's link, which forwards them as UDP.

    The newest frame wins: if the link stalls, frames are dropped rather than
    queued, so the knobs never feel more than a frame or two behind. The writer
    thread owns the bank flip, so a dropped frame can't land in the shown bank.
    """
    realtime = True

    def __init__(self, host, ip):
        self.host, self.ip = host, ip
        src = (Path(__file__).with_name("r75_pipe.py")).read_bytes()
        blob = base64.b64encode(zlib.compress(src, 9)).decode()
        self.cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ServerAliveInterval=5", "-o", "ServerAliveCountMax=2",
                    host, f"python3 -u -c 'import base64,zlib;exec(zlib.decompress(base64.b64decode(\"{blob}\")))' {ip}"]
        self.cv = threading.Condition()
        self.pending = None
        self.closing = False
        self.proc = None
        self.written = self.dropped = 0
        self.thread = threading.Thread(target=self._writer, daemon=True)
        self.thread.start()

    def _connect(self):
        # own session: a Ctrl-C at the terminal must not kill ssh before the blanking frame goes out
        self.proc = subprocess.Popen(self.cmd, stdin=subprocess.PIPE, start_new_session=True)
        s = _BufSock()
        for b in (0, 1):
            r75_frame.send_frame(s, self.ip, BLACK, blank_unused=True, bank=b)
        r75_frame.show_bank(s, self.ip, 0)
        r75_frame.enable(s, self.ip)
        self.proc.stdin.write(s.buf)
        self.proc.stdin.flush()
        log(f"pipe: ssh {self.host} -> udp {self.ip}")

    def _writer(self):
        bank, t_enable = 1, 0.0
        while True:
            with self.cv:
                while self.pending is None and not self.closing:
                    self.cv.wait()
                frame, self.pending = self.pending, None
                closing = self.closing
            if closing:
                frame, bank = BLACK, 0
            try:
                if self.proc is None or self.proc.poll() is not None:
                    self._connect()
                s = _BufSock()
                r75_frame.send_frame(s, self.ip, frame, bank=bank)
                r75_frame.show_bank(s, self.ip, bank)
                if time.monotonic() - t_enable >= 1.0:
                    r75_frame.enable(s, self.ip)
                    t_enable = time.monotonic()
                self.proc.stdin.write(s.buf)
                self.proc.stdin.flush()
                self.written += 1
                bank ^= 1
            except OSError as e:
                log(f"pipe: {e}; reconnecting in 2 s")
                if self.proc:
                    self.proc.kill()
                self.proc = None
                time.sleep(2)
            if closing:
                return

    def show(self, frame, lights=None):
        with self.cv:
            if self.pending is not None:
                self.dropped += 1
            self.pending = frame
            self.cv.notify()

    def stats(self):
        s = f"pipe sent {self.written} dropped {self.dropped}"
        self.written = self.dropped = 0
        return s

    def close(self):
        with self.cv:
            self.closing = True
            self.cv.notify()
        self.thread.join(timeout=5)
        if self.proc:
            self.proc.stdin.close()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


class PreviewOut:
    """An animated GIF of what the panels would show, with the four knob lights under it.

    receiver75 duty is linear light, so the preview re-encodes it for a monitor.
    """
    realtime = False

    def __init__(self, path, fps=20, scale=3):
        self.path, self.scale, self.every = path, scale, fps
        self.frames = []

    def show(self, frame, lights=None):
        img = ((frame / 255.0) ** (1 / 2.2) * 255).astype(np.uint8)
        img = img.repeat(self.scale, 0).repeat(self.scale, 1)
        h, w = img.shape[:2]
        strip = np.zeros((14 * self.scale // 3 + 8, w, 3), np.uint8)
        for k, c in enumerate(lights or []):
            cx = int(w * (k + 0.5) / 4)
            c = np.clip(np.array(c, float) * 4, 0, 255)        # knob lights run dim; brighten for the eye
            strip[3:-3, cx - 10:cx + 10] = c.astype(np.uint8)
        self.frames.append(np.concatenate([img, strip]))

    def stats(self):
        return f"preview {len(self.frames)} frames"

    def close(self):
        from PIL import Image
        ims = [Image.fromarray(f) for f in self.frames]
        if self.path.endswith(".png"):
            ims[-1].save(self.path)
        else:
            ims[0].save(self.path, save_all=True, append_images=ims[1:], duration=int(1000 / self.every),
                        loop=0, optimize=False)
        log(f"preview: wrote {len(ims)} frames to {self.path}")


def card_on_link(ip="192.168.75.39", timeout=1.0):
    """Is the card on one of this host's own Ethernet links? Nudge it with a datagram to the
    discard port (receiver75 ignores it) and see whether ARP resolves its address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(b"", (ip, 9))
    except OSError:
        return False
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        out = subprocess.run(["ip", "neigh", "show", ip], capture_output=True, text=True).stdout
        if "lladdr" in out and "FAILED" not in out and "INCOMPLETE" not in out:
            return True
        time.sleep(0.1)
    return False


def frame_sink(spec, preview_fps=20):
    kind, _, arg = spec.partition(":")
    if kind == "auto":
        # straight to the card if it's on our own wire (fastest), else via the bench pipe
        host, _, ip = arg.partition(":")
        ip = ip or "192.168.75.39"
        if card_on_link(ip):
            log(f"out: the card is on this host's link: udp {ip}")
            return UdpOut(ip)
        if not host:
            raise SystemExit(f"out: the card ({ip}) isn't on this host's link: give --out pipe:HOST for a host "
                             f"that is, or --out preview:FILE.gif to run without it")
        log(f"out: card not on this host's link; pipe through {host}")
        return PipeOut(host, ip)
    if kind == "udp":
        return UdpOut(arg or "192.168.75.39")
    if kind == "pipe":
        host, _, ip = arg.partition(":")
        return PipeOut(host, ip or "192.168.75.39")
    if kind == "preview":
        return PreviewOut(arg or "preview.gif", fps=preview_fps)
    raise SystemExit(f"unknown output {spec!r}")
