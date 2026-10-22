#!/usr/bin/env python3
"""Send 128x128 frames to the desktop 2x2 through receiver75.

Bench mapping, read off r75_slot_ids.py on 2026-10-21: each HUB75 connector Jn
drives receiver75 slot 2n-1 (one panel per connector; the even slot is the
unused second panel of the chain). All four panels read upright.

    upper-left  J5 -> slot 9     upper-right J8 -> slot 15
    lower-left  J4 -> slot 7     lower-right J1 -> slot 1

    r75_frame.py --eth-ip 192.168.75.39 [--level 40]   # seam test pattern
"""
import argparse
import socket
import struct

import numpy as np

# (row, col) of each 64x64 quadrant in the 128x128 frame -> receiver75 slot
QUADRANT_SLOTS = {(0, 0): 9, (0, 1): 15, (1, 0): 7, (1, 1): 1}
SLOTS = 16


def send_slot(sock, ip, im, slot):
    for r in range(16):                 # 4 rows (768 bytes) a packet, as sender75 does
        offset = r * 4 * 48 + slot * 64 * 48
        sock.sendto(struct.pack("<i", offset) + im[r * 4:r * 4 + 4].tobytes(), (ip, 4343))


def send_frame(sock, ip, frame, blank_unused=False):
    """frame: uint8 array (128, 128, 3), RGB, row 0 at the top as seen from the front."""
    assert frame.shape == (128, 128, 3) and frame.dtype == np.uint8
    for (qr, qc), slot in QUADRANT_SLOTS.items():
        send_slot(sock, ip, np.ascontiguousarray(frame[qr * 64:qr * 64 + 64, qc * 64:qc * 64 + 64]), slot)
    if blank_unused:
        black = np.zeros((64, 64, 3), np.uint8)
        for slot in set(range(SLOTS)) - set(QUADRANT_SLOTS.values()):
            send_slot(sock, ip, black, slot)


def seam_pattern(level):
    """Lines that cross both seams: border, diagonals, a ring, and a centre cross."""
    f = np.zeros((128, 128, 3), np.uint8)
    y, x = np.mgrid[0:128, 0:128]
    f[(x == 0) | (x == 127) | (y == 0) | (y == 127)] = (level, level, level)
    f[(x == y) | (x == 127 - y)] = (level, 0, 0)
    r = np.hypot(x - 63.5, y - 63.5)
    f[np.abs(r - 40) < 0.8] = (0, level, 0)
    f[(x == 63) | (x == 64)] |= np.array((0, 0, level), np.uint8)
    f[(y == 63) | (y == 64)] |= np.array((0, 0, level), np.uint8)
    return f


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--eth-ip", default="192.168.75.39")
    p.add_argument("--level", type=int, default=40, help="raw channel value, no gamma (default 40)")
    args = p.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send_frame(sock, args.eth_ip, seam_pattern(args.level), blank_unused=True)
    print("sent seam test pattern")


if __name__ == "__main__":
    main()
