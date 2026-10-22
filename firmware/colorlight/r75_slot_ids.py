#!/usr/bin/env python3
"""Draw each receiver75 panel slot's index as big digits, to map slots to panels.

receiver75 has 16 slots of 64x64 (two per HUB75 connector). Each slot gets its
number in white on a dim tint, plus a white corner marker at the slot's (0,0),
so the panel shows both which slot drives it and how it is oriented. Raw
values, no gamma: the white digits are ~20 % of a panel, so the draw stays well
under 0.3 A a panel.

    r75_slot_ids.py --eth-ip 192.168.75.39
"""
import argparse
import socket
import struct

import numpy as np

FONT = {  # 3x5 digits, rows top to bottom
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"], "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"], "7": ["111", "001", "010", "010", "010"],
    "8": ["111", "101", "111", "101", "111"], "9": ["111", "101", "111", "001", "111"],
}
TINTS = [(8, 0, 0), (0, 8, 0), (0, 0, 8), (8, 8, 0), (0, 8, 8), (8, 0, 8), (8, 4, 0), (4, 4, 8)]
WHITE = 48
SCALE = 6


def slot_image(slot):
    im = np.zeros((64, 64, 3), np.uint8)
    im[:, :] = TINTS[slot % 8]
    if slot >= 8:                       # second half of the slots: striped tint
        im[::4, :] = 0
    text = str(slot)
    width = len(text) * 4 * SCALE - SCALE
    x0, y0 = (64 - width) // 2, (64 - 5 * SCALE) // 2
    for n, ch in enumerate(text):
        for r, line in enumerate(FONT[ch]):
            for c, on in enumerate(line):
                if on == "1":
                    y, x = y0 + r * SCALE, x0 + (n * 4 + c) * SCALE
                    im[y:y + SCALE, x:x + SCALE] = WHITE
    im[0:4, 0:12] = WHITE               # corner marker at pixel (0,0): top-left if upright
    im[0:12, 0:4] = WHITE
    return im


def send_slot(sock, ip, im, slot):
    for r in range(16):                 # 4 rows (768 bytes) a packet, as sender75 does
        offset = r * 4 * 48 + slot * 64 * 48
        sock.sendto(struct.pack("<i", offset) + im[r * 4:r * 4 + 4].tobytes(), (ip, 4343))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--eth-ip", default="192.168.75.39")
    args = p.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for slot in range(16):
        send_slot(sock, args.eth_ip, slot_image(slot), slot)
    print("drew slots 0-15")


if __name__ == "__main__":
    main()
