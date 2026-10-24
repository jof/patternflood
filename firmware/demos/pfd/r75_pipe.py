"""Dumb pipe: (port, length, payload) records on stdin -> UDP datagrams to receiver75.

Runs on whichever host is wired to the card. run.py sends this file's source
over the ssh command line, so nothing has to be installed there:

    python3 -u -c '<this file>' 192.168.75.39
"""
import socket
import struct
import sys


def main():
    ip = sys.argv[1]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inp = sys.stdin.buffer
    sent = 0
    while True:
        hdr = inp.read(4)
        if len(hdr) < 4:
            break
        port, n = struct.unpack("<HH", hdr)
        data = inp.read(n)
        if len(data) < n:
            break
        try:
            sock.sendto(data, (ip, port))
            sent += 1
        except OSError as e:            # link down: drop and carry on
            print(f"r75_pipe: {e}", file=sys.stderr, flush=True)
    print(f"r75_pipe: stdin closed after {sent} datagrams", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
