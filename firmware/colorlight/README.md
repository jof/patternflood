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
