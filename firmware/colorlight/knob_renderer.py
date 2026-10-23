#!/usr/bin/env python3
"""Knob-driven patterns on the 2x2, through receiver75 (runs on the host wired to the card).

Renders 128x128 frames and double-buffers them into receiver75. Knobs come from:
  --knobs stdin  knob_bridge JSON lines on stdin; knob NeoPixel commands
                 ("px k rrggbb") go to stdout for knob_link.py to pass back to
                 the FeatherS3. Logs go to stderr.
  --knobs i2c    the 4991 seesaw boards directly on this host's I2C bus
                 (the Pi controller); lights are set over I2C too.
--res 64 renders at half resolution and doubles pixels, for slow hosts (Pi Zero W).

Knobs (k0..k3 in address order, shown red/green/blue/yellow at bridge boot):
    k0  turn: hue          press: next pattern
    k1  turn: speed        press: freeze / unfreeze
    k2  turn: scale        press: reset all
    k3  turn: brightness   press: blackout toggle

Current is capped per frame, after gamma: each panel's draw is estimated from
its duty (2.4 A at full white, the upstream ESP32 figure; recalibrate on this
driver) and the whole frame scaled down if any panel would exceed PANEL_AMPS
or the four together TOTAL_AMPS.
"""
import argparse
import json
import math
import queue
import signal
import socket
import sys
import threading
import time

import numpy as np

import r75_frame

FULL_WHITE_AMPS = 2.4      # per panel, measured upstream on an ESP32 driver
PANEL_AMPS = 1.2           # conservative until calibrated on the Colorlight
TOTAL_AMPS = 4.0
GAMMA = 2.2
FPS = 60

X = Y = R = A = None


def set_resolution(n):
    """Sample grids for an n x n render, in 128-pixel coordinates so patterns keep their geometry."""
    global X, Y, R, A
    c = (np.arange(n, dtype=np.float32) + 0.5) * (128 / n) - 0.5
    Y, X = np.meshgrid(c, c, indexing="ij")
    R = np.hypot(X - 63.5, Y - 63.5)
    A = np.arctan2(Y - 63.5, X - 63.5)


set_resolution(128)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def hsv(h, s, v):
    """Vectorised HSV -> RGB, all inputs in 0..1, output float RGB 0..1."""
    h = (h % 1.0) * 6.0
    i = np.floor(h).astype(np.int32) % 6
    f = h - np.floor(h)
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], axis=-1)


def plasma(t, scale, hue):
    s = 0.06 * scale
    v = (np.sin(X * s + t) + np.sin(Y * s * 0.8 + t * 1.3)
         + np.sin((X + Y) * s * 0.55 + t * 0.7) + np.sin(R * s * 1.2 - t * 1.1))
    return hsv(hue + v / 8.0, 1.0, 0.55 + 0.45 * np.sin(v * 1.5 + t))


def tunnel(t, scale, hue):
    rr = 1.0 / (R * 0.02 * scale + 0.15)
    v = np.sin(rr * 4.0 - t * 3.0) * np.cos(A * 3.0 + t * 0.5)
    return hsv(hue + rr * 0.08 + A / (2 * math.pi), 0.9, np.clip(0.5 + 0.5 * v, 0, 1) * np.clip(R / 20, 0, 1))


def ripples(t, scale, hue):
    s = 0.12 * scale
    c = [(32 + 20 * math.sin(t * 0.7), 40 + 18 * math.cos(t * 0.5)),
         (96 + 18 * math.cos(t * 0.6), 88 + 20 * math.sin(t * 0.8))]
    v = sum(np.sin(np.hypot(X - cx, Y - cy) * s - t * 4.0) for cx, cy in c) / 2.0
    return hsv(hue + 0.15 * v, 0.85, np.clip(0.5 + 0.5 * v, 0, 1) ** 1.5)


PATTERNS = [("plasma", plasma), ("tunnel", tunnel), ("ripples", ripples)]


class State:
    def __init__(self):
        self.reset()
        self.pattern = 0

    def reset(self):
        self.hue = 0.0
        self.speed = 1.0
        self.scale = 1.0
        self.bright = 0.3
        self.frozen = False
        self.black = False


def handle(state, ev):
    t, k = ev.get("t"), ev.get("k")
    if t == "enc":
        d = ev["d"]
        if k == 0:
            state.hue = (state.hue + d / 48.0) % 1.0
        elif k == 1:
            state.speed = min(5.0, max(0.0, state.speed + d * 0.1))
        elif k == 2:
            state.scale = min(4.0, max(0.25, state.scale * (1.06 ** d)))
        elif k == 3:
            state.bright = min(1.0, max(0.0, state.bright + d * 0.02))
    elif t == "btn" and ev.get("down"):
        if k == 0:
            state.pattern = (state.pattern + 1) % len(PATTERNS)
            log("pattern:", PATTERNS[state.pattern][0])
        elif k == 1:
            state.frozen = not state.frozen
        elif k == 2:
            state.reset()
            log("reset")
        elif k == 3:
            state.black = not state.black
    elif t == "hello":
        log("knobs:", ev.get("knobs"))
        return True                     # bridge (re)booted: refresh knob lights
    return False


def capped(rgb):
    """rgb float 0..1 (post-gamma duty) -> uint8 frame, scaled to the current budget."""
    h = rgb.shape[0] // 2
    duty = rgb.reshape(2, h, 2, h, 3).mean(axis=(1, 3, 4))     # per-panel mean duty, 2x2
    amps = duty * FULL_WHITE_AMPS
    scale = 1.0
    if amps.max() > PANEL_AMPS:
        scale = PANEL_AMPS / amps.max()
    if amps.sum() * scale > TOTAL_AMPS:
        scale = TOTAL_AMPS / amps.sum()
    return (np.clip(rgb * scale, 0, 1) * 255 + 0.5).astype(np.uint8), amps.sum() * scale, scale


def knob_lights(state):
    h = hsv(np.array(state.hue), np.array(1.0), np.array(0.25))
    hue_rgb = tuple(int(c * 255) for c in h)
    sp = int(10 + 40 * state.speed / 5.0)
    sc = int(10 + 40 * (math.log(state.scale, 4) + 1) / 2)
    br = int(5 + 50 * state.bright)
    return [
        "px 0 %02x%02x%02x" % hue_rgb,
        "px 1 %02x%02x%02x" % ((0, sp, 0) if not state.frozen else (sp, 0, 0)),
        "px 2 %02x%02x%02x" % (0, 0, sc),
        "px 3 %02x%02x%02x" % ((br, br, br) if not state.black else (0, 0, 0)),
    ]


def stdin_reader(q):
    for line in sys.stdin:
        line = line.strip()
        if line.startswith("{"):
            try:
                q.put(json.loads(line))
            except json.JSONDecodeError:
                pass
    q.put(None)                         # EOF: the link went away


class StdoutLights:
    """Knob lights via knob_link.py: "px k rrggbb" lines on stdout."""
    def show(self, lines):
        print("\n".join(lines), flush=True)


class I2CKnobs:
    """4991 seesaw encoders on a local I2C bus: polled into the event queue; lights set directly."""
    POLL_S = 0.01
    MAX_STEP = 24                       # bigger jumps between polls are bus glitches: resync

    def __init__(self, bus, q):
        import seesaw
        self.q = q
        try:
            self.knobs = seesaw.find_encoders(bus)
        except OSError as e:            # no /dev/i2c-N: run the pattern without knobs
            log(f"I2C bus {bus} unavailable ({e}); running without knobs")
            self.knobs = []
        self.pos = [ss.position() for ss in self.knobs]
        self.down = [ss.pressed() for ss in self.knobs]
        self.errors = 0
        q.put({"t": "hello", "knobs": [{"k": k, "addr": f"0x{ss.addr:02X}"} for k, ss in enumerate(self.knobs)]})
        threading.Thread(target=self.poll, daemon=True).start()

    def poll(self):
        while True:
            for k, ss in enumerate(self.knobs):
                try:
                    p, d = ss.position(), ss.pressed()
                except OSError:
                    self.errors += 1
                    continue
                step = p - self.pos[k]
                if step and abs(step) <= self.MAX_STEP:
                    self.q.put({"t": "enc", "k": k, "pos": p, "d": step})
                self.pos[k] = p
                if d != self.down[k]:
                    self.q.put({"t": "btn", "k": k, "down": int(d)})
                    self.down[k] = d
            time.sleep(self.POLL_S)

    def show(self, lines):
        for line in lines:
            _, k, rgb = line.split()
            k, rgb = int(k), int(rgb, 16)
            if k < len(self.knobs):
                try:
                    self.knobs[k].pixel(rgb >> 16, (rgb >> 8) & 0xFF, rgb & 0xFF)
                except OSError:
                    self.errors += 1


class Sender:
    """Frame output that rides out a missing or down link (USB NIC unplugged, card rebooting)."""
    def __init__(self, ip):
        self.ip, self.sock, self.t_err = ip, socket.socket(socket.AF_INET, socket.SOCK_DGRAM), 0.0

    def __call__(self, fn, *a, **kw):
        try:
            fn(self.sock, self.ip, *a, **kw)
            return True
        except OSError as e:
            if time.monotonic() - self.t_err > 10:
                log(f"send to {self.ip} failed: {e}; retrying")
                self.t_err = time.monotonic()
            return False


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--eth-ip", default="192.168.75.39")
    p.add_argument("--knobs", choices=["stdin", "i2c"], default="stdin")
    p.add_argument("--i2c-bus", type=int, default=1)
    p.add_argument("--res", type=int, choices=[128, 64, 32], default=128,
                   help="render resolution; frames are upscaled to 128x128")
    p.add_argument("--fps", type=float, default=FPS)
    args = p.parse_args()

    def on_term(*_):
        raise KeyboardInterrupt         # systemd stop: blank the display on the way out
    signal.signal(signal.SIGTERM, on_term)

    set_resolution(args.res)
    up = 128 // args.res
    send = Sender(args.eth_ip)
    q = queue.Queue()
    if args.knobs == "i2c":
        knobs = I2CKnobs(args.i2c_bus, q)
        lights_out = knobs
    else:
        threading.Thread(target=stdin_reader, args=(q,), daemon=True).start()
        knobs, lights_out = None, StdoutLights()

    state = State()
    black = np.zeros((128, 128, 3), np.uint8)
    for bank in (0, 1):
        send(r75_frame.send_frame, black, blank_unused=True, bank=bank)
    send(r75_frame.show_bank, 0)
    send(r75_frame.enable)

    t_anim, last, bank, lights, frames, t_stat = 0.0, time.monotonic(), 1, None, 0, time.monotonic()
    t_enable = time.monotonic()
    log("rendering; patterns:", [n for n, _ in PATTERNS])
    try:
        while True:
            refresh = False
            while True:
                try:
                    ev = q.get_nowait()
                except queue.Empty:
                    break
                if ev is None:
                    raise EOFError
                refresh |= handle(state, ev)

            now = time.monotonic()
            if not state.frozen:
                t_anim += (now - last) * state.speed
            last = now

            if state.black:
                frame, amps, scale = black, 0.0, 1.0
            else:
                rgb = PATTERNS[state.pattern][1](t_anim, state.scale, state.hue)
                rgb = np.clip(rgb, 0, 1) ** GAMMA * state.bright
                frame, amps, scale = capped(rgb)
                if up > 1:
                    frame = frame.repeat(up, axis=0).repeat(up, axis=1)

            if send(r75_frame.send_frame, frame, bank=bank):
                send(r75_frame.show_bank, bank)
                bank ^= 1
            if now - t_enable >= 1.0:       # receiver75 boots disabled: re-enable after a card reboot
                send(r75_frame.enable)
                t_enable = now

            new_lights = knob_lights(state)
            if refresh or new_lights != lights:
                lights = new_lights
                lights_out.show(lights)

            frames += 1
            if now - t_stat >= 5:
                i2c = f"  i2c errors {knobs.errors}" if knobs else ""
                log(f"{frames / (now - t_stat):5.1f} fps  est {amps:4.2f} A  cap x{scale:.2f}  "
                    f"{PATTERNS[state.pattern][0]} hue {state.hue:.2f} speed {state.speed:.1f} "
                    f"scale {state.scale:.2f} bright {state.bright:.2f}"
                    f"{'  BLACKOUT' if state.black else ''}{'  FROZEN' if state.frozen else ''}{i2c}")
                frames, t_stat = 0, now

            time.sleep(max(0.0, 1.0 / args.fps - (time.monotonic() - now)))
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        send(r75_frame.send_frame, black, bank=0)
        send(r75_frame.show_bank, 0)
        if knobs:
            knobs.show(["px %d 000000" % k for k in range(len(knobs.knobs))])
        log("stopped; display blanked")


if __name__ == "__main__":
    main()
