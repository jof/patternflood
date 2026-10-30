# receiver75, with a boot splash

[receiver75](https://github.com/dgym/receiver75) by Jim Bailey is open LiteX
gateware for the Colorlight 5A-75B. It turns the card into a framebuffer that
takes UDP packets. Patternflood runs it with three patches, on top of upstream
`4c44c91`:

| Patch | Does |
|---|---|
| `0001` | The BIOS keeps its built-in IP (192.168.75.39) when the flash config block is blank, so no config block needs writing |
| `0002` | A boot splash: from power-on the BIOS draws a dim spinner and a five-step progress bar, until a host takes the display. The Pi moves the bar on (`../../pi-controller/pf-splash`) |
| `0003` | The BIOS runs the SDRAM init sequence without LiteX's memtest, which hung on this SoC's memory map |

`receiver75-splash-5f2185b.bit` is the bitstream built from those patches
(`--revision 8.0`, against 2021 LiteX), and the one in the cards we run. It is
for the 5A-75B v8.0 pinout, which the v8.2 shares. Its panel map, a 2 × 2 of
64 × 64 panels on slots 9, 15, 7 and 1, is compiled in.

sha256 `4efe80894b2ec8b4701c7b244b9611b9f21f06e2a5232380e79d0a0e670ac0cf`

To flash it, see [`../README.md`](../README.md#receiver75-in-flash-2026-10-21). To rebuild:

```sh
git clone https://github.com/dgym/receiver75
cd receiver75
git checkout 4c44c91
git am /path/to/patternflood/firmware/colorlight/receiver75/*.patch
# then build as receiver75's README describes, with --revision 8.0
```

receiver75 is MIT-licensed; its licence is in [`LICENSE`](LICENSE).
