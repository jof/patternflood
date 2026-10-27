"""Minimal Adafruit seesaw driver for the 4991 rotary encoder, over Linux i2c-dev.

No dependencies beyond the standard library: register numbers are those of
Adafruit_seesaw.h. Each read is a write of (module, function) followed, after
a short delay for the ATtiny to prepare the reply, by a separate read.
"""
import fcntl
import os
import struct
import threading
import time

I2C_SLAVE = 0x0703
BUS_LOCK = threading.Lock()      # a read is write + delay + read; keep threads from interleaving

STATUS, GPIO, NEOPIXEL, ENCODER = 0x00, 0x01, 0x0E, 0x11
STATUS_VERSION, STATUS_SWRST = 0x02, 0x7F
GPIO_DIRCLR_BULK, GPIO_BULK, GPIO_BULK_SET, GPIO_PULLENSET = 0x03, 0x04, 0x05, 0x0B
NEO_PIN, NEO_BUF_LENGTH, NEO_BUF, NEO_SHOW = 0x01, 0x03, 0x04, 0x05
ENCODER_POSITION = 0x30

PID_4991 = 4991
SWITCH_PIN = 24          # encoder push switch
NEOPIXEL_PIN = 6
READ_DELAY = 0.0005


class Seesaw:
    def __init__(self, bus, addr):
        self.addr = addr
        self.fd = os.open(f"/dev/i2c-{bus}", os.O_RDWR)
        fcntl.ioctl(self.fd, I2C_SLAVE, addr)

    def close(self):
        os.close(self.fd)

    def write(self, module, function, data=b""):
        with BUS_LOCK:
            os.write(self.fd, bytes([module, function]) + data)

    def read(self, module, function, n, delay=READ_DELAY):
        with BUS_LOCK:
            os.write(self.fd, bytes([module, function]))
            time.sleep(delay)
            data = os.read(self.fd, n)
        if len(data) != n:
            raise OSError(f"short read from 0x{self.addr:02x}")
        return data

    def product_id(self):
        return struct.unpack(">I", self.read(STATUS, STATUS_VERSION, 4))[0] >> 16

    def reset(self):
        self.write(STATUS, STATUS_SWRST, b"\xff")
        time.sleep(0.5)

    def setup_encoder(self):
        mask = struct.pack(">I", 1 << SWITCH_PIN)
        self.write(GPIO, GPIO_DIRCLR_BULK, mask)       # input
        self.write(GPIO, GPIO_PULLENSET, mask)         # pull enabled
        self.write(GPIO, GPIO_BULK_SET, mask)          # ... and pulled up
        self.write(NEOPIXEL, NEO_PIN, bytes([NEOPIXEL_PIN]))
        self.write(NEOPIXEL, NEO_BUF_LENGTH, struct.pack(">H", 3))

    def position(self):
        return struct.unpack(">i", self.read(ENCODER, ENCODER_POSITION, 4))[0]

    def pressed(self):
        return not (struct.unpack(">I", self.read(GPIO, GPIO_BULK, 4))[0] >> SWITCH_PIN) & 1

    def pixel(self, r, g, b):
        self.write(NEOPIXEL, NEO_BUF, struct.pack(">H", 0) + bytes([g, r, b]))   # GRB
        self.write(NEOPIXEL, NEO_SHOW)


def find_encoders(bus=1, addrs=range(0x36, 0x3E), expect=range(0x37, 0x3B), tries=5):
    """Return Seesaw objects for every 4991 encoder found, in address order.

    Knobs are numbered by their place in this list, so one that misses its probe
    shifts every role after it. The addresses we expect (k0-k3) get several tries:
    on the Zero W, a probe during the renderer's busy start-up has missed a knob
    that answered every probe on a quiet bus.
    """
    found = []
    for addr in addrs:
        ss = Seesaw(bus, addr)
        for attempt in range(tries if addr in expect else 1):
            try:
                if ss.product_id() != PID_4991:
                    break
                ss.reset()
                ss.setup_encoder()
                found.append(ss)
                break
            except OSError:             # nothing at this address (NACK), or a glitch: try again
                time.sleep(0.05)
        if not found or found[-1] is not ss:
            ss.close()
    return found
