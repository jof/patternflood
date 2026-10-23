# Wiring the Pi Zero W controller

The controller for now is a **Raspberry Pi Zero W (Rev 1.1)**, set up as an
appliance by [`firmware/pi-controller/`](../../firmware/pi-controller/README.md).
It reads the four knobs over I²C, renders, and sends frames to the Colorlight
card over a USB gigabit Ethernet link. This replaces the bench arrangement,
where a FeatherS3 read the knobs and a laptop rendered.

## 1. Knob chain → Pi header (I²C)

The four Adafruit 4991 encoders stay daisy-chained by their STEMMA QT
connectors, exactly as now. Only the end that went into the FeatherS3 moves:
it goes to the Pi's 40-pin header.

| STEMMA QT wire | Signal | Pi header pin | Pi name |
|---|---|---|---|
| **Red** | V+ | **pin 1** | **3V3** (not 5 V) |
| **Black** | GND | **pin 6** (or 9, 14) | GND |
| **Blue** | SDA | **pin 3** | GPIO2 / SDA1 |
| **Yellow** | SCL | **pin 5** | GPIO3 / SCL1 |

```
            Pi Zero W 40-pin header (top view, SD-card end at the left)

     Red ──  3V3   (1) (2)   5V
    Blue ──  SDA   (3) (4)   5V
  Yellow ──  SCL   (5) (6)   GND  ── Black
                   (7) (8)
             GND   (9) (10)
                  ...
```

Pin 1 is the square pad, at the SD-card end of the header, on the row nearer
the board edge.

- **Cable:** a STEMMA QT / Qwiic JST-SH 4-pin to female-socket cable (Adafruit
  4397) if the Zero has a header fitted. Use the male-pin version, or solder
  the wires straight to the pads, if it doesn't.
- **⚠ 3.3 V only.** Each 4991 board pulls SDA and SCL up to its own supply. On
  5 V it would put 5 V on the Pi's GPIO2/3, which are not 5 V-tolerant.
- **Unplug the FeatherS3 from the chain.** Two I²C masters on one bus will
  corrupt each other's transfers. The FeatherS3 is only for bench work now.
- **Addresses are unchanged:** 0x37, 0x38, 0x39, 0x3A (k0–k3), set by the
  solder jumpers. Chain order doesn't matter; knobs are numbered by address.
- **Pull-ups:** the Pi's on-board 1.8 kΩ in parallel with four boards' 10 kΩ
  gives about 1.1 kΩ. That's fine at 3.3 V and 100 kHz. Keep the whole chain
  under about 1 m.
- **Power:** four boards plus their NeoPixels (which the renderer keeps dim)
  draw well under 150 mA from the Pi's 3V3.

## 2. Pi → Colorlight card (Ethernet)

```
  Pi Zero W "USB" port (micro-USB OTG, the one nearer the middle)
     └─ micro-USB OTG adapter ─ USB gigabit Ethernet adapter ─ Cat6 ─ 5A-75B (either RJ45)
```

- **The adapter must be gigabit** (e.g. RTL8153 or ASIX AX88179). The 5A-75B
  won't link at 100 Mbit. Over the Zero's USB 2.0 it runs at about 300 Mbit/s,
  far more than the frames need.
- **⚠ Don't power the adapter from the Zero's port.** On 2026-10-22 two RTL8153
  adapters (a generic one and an Anker) never worked on the bare port. Details are
  in §5. Give the adapter its own 5 V (§2.1), or use a Pi with Ethernet on board.

### 2.1 Power-injected USB extension (the fix to try)

Open a USB-A extension's jacket partway along, between the OTG dongle and the
adapter:

| Wire | Change |
|---|---|
| Red (VBUS) | **Cut.** Adapter-side end to the LRS +5 V; tape off the Pi-side end |
| Black (GND) | Leave it continuous to the Pi, **and** run a wire from it to the LRS GND |
| Green (D+), white (D−), shield | Unchanged |

The adapter then draws from the PSU, and the Zero's port carries data only. Never
join the two 5 V feeds: the Pi-side red stays cut. A powered USB hub does the same
job.
- The appliance gives any wired interface 192.168.75.1/24. receiver75 is at
  192.168.75.39.

## 3. Power

Two options, both from the LRS-50-5's 5 V (trim to about 5.15 V, as in
[`power-plan.md`](power-plan.md)):

- **"PWR IN" micro-USB, through a 5 V pigtail.** The simplest, and it keeps the
  Zero's input protection in the path.
- **Header pin 2 (5 V) and pin 6 (GND).** Tidier inside the box, but it
  bypasses the micro-USB input's protection, so the supply has to be right.

The Zero W draws about 0.2–0.35 A. The USB gigabit adapter draws more than first
assumed: an Anker RTL8153 measured **0.41 A** on a PC with no link. Budget about
0.5 A for it, from its own feed (§2.1).

## 4. Serial console

`enable_uart=1` puts the Pi's console on the header: GPIO14 TXD (pin 8) and GPIO15
RXD (pin 10), 115200. Free grounds are pins 9, 14, 20, 25, 30, 34 and 39; pin 6 is the
knob chain's. With a Glasgow on port B, Pi TXD → B0 and Pi RXD → B1:

    glasgow run uart -V B=3.3 --rx B0 --tx B1 -b 115200 tty

The Glasgow reset off its host's USB twice when the Pi powered up, probably from the
power-on surge on the shared ground. Rerun the applet if the console stops.

## 5. USB Ethernet on the bare Zero port: findings, 2026-10-22

Kernel 6.18.50, `dwc_otg` in host mode through a micro-B-to-A OTG dongle:

| Test | Result |
|---|---|
| SanDisk USB stick, through the dongle (and through dongle + extension) | **High speed**, every time |
| Generic RTL8153, Anker RTL8153 | No connect at all on some boots (`HPRT0 = 0x00001000`, D+ never pulled up). On others, **full speed with `device descriptor read/64, error -71`**, then the hub driver powers the port off |
| Same adapters on ash (xHCI) | Enumerate at once, at high speed |
| 5 V at the header, meter min-hold through boot | **5.045 V** min, 4.993 V with the Anker drawing; `throttled=0x0` |
| 5 V at the adapter on the Pi (inline USB meter) | 4.89 V, 0.635 A; later **4.81 V, 0.90 A**, and the Anker got hot |
| Anker on ash, same meter (no data) | 4.62 V, **0.41 A** |
| Panels and encoders off the PSU | No change |
| Hot-plugging an adapter | **Resets the Pi** (brown-out: the console stops with no panic) |
| True cold start (PSU off, adapter in, PSU on) | Still no connect |
| **Pi Zero 2 W** (patternflood card, same dongle chain, RTL8153) | **Same:** port powered, no connect, after a minute |

- The Anker no longer enumerated on ash afterwards. Take it as damaged.
- Two different Zeros fail the same way, so it isn't one bad board. Both tests shared the OTG dongle and the PSU.
- RTL8153 adapters on Zeros are a common working setup elsewhere, so **the dongle is the main suspect**. The stick proved its data lines, but only at about a tenth of the adapter's 0.4–0.9 A.
- The supply level at the Pi is fine.
- The mechanism isn't pinned down without a scope; candidates are the dongle's contacts under load, and latch-up after the brown-outs. `dwc_otg.speed=1` doesn't help, because full speed already fails, and it's too slow for frames anyway.
- **Next:** replace the dongle with a proper micro-B-to-A OTG cable, ideally a "Y" one with a separate power input. Or use §2.1, or a powered hub. Don't hot-plug adapters on the Zero.

`~/patternflood-debug/` on ash keeps the UART console log and `usb-flex.sh`. That
script shows the port's state on the ACT LED at 20 Hz (off / blinking for D+ pulled up /
solid once enumerated), for cable-flex tests.

## 6. Bring-up check

1. Power the Pi with the knobs and the card connected. First boot takes a few
   minutes: it resizes the card and installs numpy over Wi-Fi.
2. `ssh jof@patternflood.local`
3. `i2cdetect -y 1` should show 37, 38, 39 and 3a.
4. `journalctl -u patternflood -f` should show the `knobs:` line, then a
   frames-per-second line every 5 s.
