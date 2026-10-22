#!/usr/bin/env python3
"""Knob-driven patterns on the 2x2, through receiver75 (runs on the host wired to the card).

Reads knob_bridge JSON lines on stdin, renders 128x128 frames, and double-buffers
them into receiver75. Writes knob NeoPixel commands ("px k rrggbb") to stdout,
for knob_link.py to pass back to the FeatherS3; logs go to stderr.

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

Y, X = np.mgrid[0:128, 0:128].astype(np.float32)
R = np.hypot(X - 63.5, Y - 63.5)
A = np.arctan2(Y - 63.5, X - 63.5)


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
    duty = rgb.reshape(2, 64, 2, 64, 3).mean(axis=(1, 3, 4))   # per-panel mean duty, 2x2
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


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--eth-ip", default="192.168.75.39")
    args = p.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    q = queue.Queue()
    threading.Thread(target=stdin_reader, args=(q,), daemon=True).start()

    state = State()
    black = np.zeros((128, 128, 3), np.uint8)
    for bank in (0, 1):
        r75_frame.send_frame(sock, args.eth_ip, black, blank_unused=True, bank=bank)
    r75_frame.show_bank(sock, args.eth_ip, 0)
    r75_frame.enable(sock, args.eth_ip)

    t_anim, last, bank, lights, frames, t_stat = 0.0, time.monotonic(), 1, None, 0, time.monotonic()
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

            r75_frame.send_frame(sock, args.eth_ip, frame, bank=bank)
            r75_frame.show_bank(sock, args.eth_ip, bank)
            bank ^= 1

            new_lights = knob_lights(state)
            if refresh or new_lights != lights:
                lights = new_lights
                print("\n".join(lights), flush=True)

            frames += 1
            if now - t_stat >= 5:
                log(f"{frames / (now - t_stat):5.1f} fps  est {amps:4.2f} A  cap x{scale:.2f}  "
                    f"{PATTERNS[state.pattern][0]} hue {state.hue:.2f} speed {state.speed:.1f} "
                    f"scale {state.scale:.2f} bright {state.bright:.2f}")
                frames, t_stat = 0, now

            time.sleep(max(0.0, 1.0 / FPS - (time.monotonic() - now)))
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        r75_frame.send_frame(sock, args.eth_ip, black, bank=0)
        r75_frame.show_bank(sock, args.eth_ip, 0)
        log("stopped; display blanked")


if __name__ == "__main__":
    main()
