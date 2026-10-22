#!/usr/bin/env python3
"""Join the FeatherS3 knob bridge to a remote knob_renderer.py over SSH.

Knob JSON lines go from the serial port to the renderer's stdin; "px ..." knob
light commands come back from its stdout to the serial port. Renderer logs pass
through to this terminal. Ctrl-C stops both (the renderer blanks the display).

    knob_link.py /dev/ttyACM1 durian -- python3 -u /tmp/r75/tools/knob_renderer.py
"""
import subprocess
import sys
import threading

import serial


def main():
    if len(sys.argv) < 4 or "--" not in sys.argv:
        sys.exit(__doc__)
    port, host = sys.argv[1], sys.argv[2]
    remote = sys.argv[sys.argv.index("--") + 1:]

    ser = serial.Serial()
    ser.port, ser.baudrate, ser.timeout = port, 115200, 0.2
    ser.dtr = ser.rts = False           # asserting these drops the FeatherS3 into download mode
    ser.open()

    proc = subprocess.Popen(["ssh", "-o", "BatchMode=yes", host, *remote],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def to_renderer():
        buf = b""
        while proc.poll() is None:
            buf += ser.read(256)
            *lines, buf = buf.split(b"\n")
            for line in lines:
                line = line.strip().decode("utf-8", "replace")
                if line.startswith("{"):
                    proc.stdin.write(line + "\n")
                    proc.stdin.flush()

    def to_bridge():
        for line in proc.stdout:
            if line.startswith("px "):
                ser.write(line.encode())
            else:
                print(line, end="", flush=True)

    threading.Thread(target=to_renderer, daemon=True).start()
    threading.Thread(target=to_bridge, daemon=True).start()
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.stdin.close()              # renderer sees EOF, blanks the display and exits
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            print("renderer did not exit in 15 s; closing ssh (display may hold its last frame)",
                  file=sys.stderr)
            proc.terminate()
            proc.wait(timeout=5)


if __name__ == "__main__":
    main()
