# Colorlight 5A-75B tools

The card is a **5A-75B v8.2**: LFE5U-25F (IDCODE `0x41111043`), 4 MiB GigaDevice
GD25Q32C config flash. v8.2 has the same FPGA pinout as v8.0, and litex-boards
supports it as revision `8.2`.

## JTAG with a Glasgow

The 4-pin header next to the FPGA, wired to Glasgow port A at 3.3 V. Ground comes
from HUB75 pin 16 of an unused port, or the GND screw on the 5 V terminal. Don't
connect the board's 3.3 V.

| Pad | Signal | Glasgow |
|---|---|---|
| J27 | TCK | A0 |
| J31 | TMS | A1 |
| J32 | TDI | A2 |
| J30 | TDO | A3 |

What works, measured 2026-10-21 at 2 MHz TCK:

- **`glasgow script` against `jtag-probe`**, via `ecp5_flash_dump.py`, reads the
  flash at **~60 KiB/s** (4 MiB in ~70 s). Use this.
- `openFPGALoader -c remote-bitbang` through `glasgow run jtag-openocd` works, at
  ~3 KiB/s.
- `openFPGALoader -c xvc-client` through `glasgow run jtag-xvc` **deadlocks** on
  the first full-size shift. Glasgow advertises 4095; openFPGALoader treats that
  as per-vector, so it sends ~8 KiB shifts. A proxy that advertises 1024 fixes the
  hang, but each shift takes ~1.2 s (~0.24 KiB/s).
- The `jtag-probe scan` and `jtag-pinout` applets misreport this chip: "DR shift
  chain is too long", and no TDI found. The wiring is fine; OpenOCD and the
  script both work.

**Open fault, 2026-10-21: TDI–TDO interaction on the bench wiring.**

Measured with `jtag-probe` in a script, at both 2 MHz and 500 kHz:
- IDCODE reads correctly when TDI is held high.
- With TDI driven low, 1 bits on TDO randomly read as 0.

That's why Glasgow's `scan`, `pinout` and `jtag-svf` applets fail. An SRAM load via
`svf_play.py` got through ID, erase and burst, then stopped with status `0x05A00000`:
DONE clear, BSE error 3 (CRC). The bitstream was corrupted on the way in.

Reads that hold TDI high are unaffected. The flash backup is one; it was checked
by two identical passes plus an openFPGALoader cross-read. Check the J32/J30 pads
and jumpers for a bridge before loading anything.

Re-seating the jumpers cut the failures to about one TDI-low read in three. The
bad reads are the IDCODE shifted by one bit, which points to TCK double-clocking
on the long leads rather than a short. A ground run alongside TCK, or shorter
leads, should cure it.

## receiver75: working, 2026-10-21

- Built as `--revision 8.0` against 2021 LiteX (see the memory and build notes).
- Loaded into SRAM with `svf_play.py`, with DONE set.
- Answers ARP at 192.168.75.39 as `10:e2:d5:00:00:00`. It has no ICMP, so ping
  doesn't work.
- A dim solid frame via `tools/sender75.py` lit all four P2 panels evenly,
  with no flicker: the 1/32 scan works.
- `r75_slot_ids.py` draws each of the 16 slots' numbers, to map slots to panel
  positions and orientation.
- The map: each connector Jn shows slot 2n−1. Upper-left J5 is slot 9,
  upper-right J8 is 15, lower-left J4 is 7, lower-right J1 is 1, all upright.
- `r75_frame.py`'s seam test (border, diagonals, ring, centre cross) runs
  continuously across all four seams: the 2×2 is one 128×128 display.

## receiver75 in flash, 2026-10-21

```sh
glasgow script ecp5_flash_write.py jtag-probe -V 3.3 -f 2000 -- colorlight_5a_75b.bit 0
glasgow script ecp5_flash_write.py jtag-probe -V 3.3 -f 2000 -- status   # read-only
```

- The stock firmware ships the flash with **SR1 = 0x1C** (BP2..0 set), which
  protects the whole array. SRP0/SRP1/CMP are 0, so it's software-only.
- The script clears the protection with a one-byte `01 00`. This GD25Q32C
  ignores the two-byte `01 xx yy` form. It then erases, programs, verifies every
  byte, and restores 0x1C.
- receiver75 (663,499 bytes) was written at offset 0 and verified.
- **The card boots it after a power cycle**: dark, answering ARP at
  192.168.75.39. The `LSC_REFRESH` at the end of the script doesn't reboot this
  card; power-cycle it.
- The rest of the stock contents (second image at 0x200000, data blocks) are
  still in place but unused.
- No IP config block is written. The config location (byte 4,000,000 =
  0x3D0900) is blank, so the patched BIOS keeps the built-in IP.
- To restore stock, write the backup image from offset 0.

## Knobs → patterns (bench demo)

The FeatherS3 knob bridge is on ash's USB, and the card is on durian's USB NIC.
`knob_link.py` (on ash) pipes knob events over SSH to `knob_renderer.py` (on
durian) and passes knob-light commands back:

```sh
scp r75_frame.py knob_renderer.py durian:/tmp/r75/tools/
./knob_link.py /dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_XX:XX:XX:XX:XX:XX-if00 \
    durian -- python3 -u /tmp/r75/tools/knob_renderer.py --eth-ip 192.168.75.39
```

| Knob | Turn | Press |
|---|---|---|
| k0 (0x37) | hue | next pattern (plasma → tunnel → ripples) |
| k1 (0x38) | speed | freeze / unfreeze |
| k2 (0x39) | scale | reset all |
| k3 (0x3A) | brightness, 30 % at start | blackout |

- Frames are double-buffered through receiver75's two banks, at ~60 fps.
- Gamma is 2.2, applied on the host.
- Per-frame current cap, from estimated duty: 1.2 A a panel, 4 A in total. It
  assumes 2.4 A per panel at full white, so recalibrate on this driver.
- Ctrl-C blanks the display.

## Loading a bitstream into SRAM

```sh
glasgow script svf_play.py jtag-probe -V 3.3 -f 2000 -- design.svf
```

`ecppack --svf` output, played by a small SVF player. It keeps the Pause-DR end
state between burst chunks and checks every expected TDO, ending with DONE. RAM
only: a power cycle restores the stock image.

## Backing up the stock flash

```sh
glasgow script ecp5_flash_dump.py jtag-probe -V 3.3 -f 2000 -- stock.bin
```

The script erases the FPGA's SRAM, reads the flash through `LSC_PROG_SPI`, and
sends `LSC_REFRESH` so the card reboots from flash. Give it a few seconds
before the next JTAG session: one started straight after a refresh read the
flash ID as `ffffff`.

The stock image (two bitstreams, at 0x000000 and 0x200000, plus data blocks) is
kept outside the repo, in `~/colorlight-5a75b-v8.2-backup/`. It is Colorlight's
proprietary gateware.
