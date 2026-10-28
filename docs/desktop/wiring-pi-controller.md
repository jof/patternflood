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
| **Black** | GND | **pin 6** (or 20) | GND |
| **Blue** | SDA | **pin 3** | GPIO2 / SDA1 |
| **Yellow** | SCL | **pin 5** | GPIO3 / SCL1 |

```
            Pi Zero W 40-pin header (top view, SD-card end at the left)

     Red ──  3V3   (1) (2)   5V
    Blue ──  SDA   (3) (4)   5V
  Yellow ──  SCL   (5) (6)   GND  ── Black
                   (7) (8)
             GND   (9) (10)
                  ...          buttons: §7
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
- **Power:** the NeoPixels follow the panel brightness (k3), from a floor of
  15 % up to full scale at 1.0. Four boards draw about 50 mA with the lights dim, and up to
  about 250 mA from the Pi's 3V3 with all four lit white at full brightness.

## 2. Pi → Colorlight card (Ethernet)

```
  Pi Zero W "USB" port (micro-USB OTG, the one nearer the middle)
     └─ micro-B-to-A OTG cable ─ USB gigabit Ethernet adapter ─ Cat6 ─ 5A-75B (either RJ45)
```

- **The adapter must be gigabit** (e.g. RTL8153 or ASIX AX88179). The 5A-75B
  won't link at 100 Mbit. Over the Zero's USB 2.0 it runs at about 300 Mbit/s,
  far more than the frames need.
- **Use an OTG cable, not a plug-style OTG dongle.** On 2026-10-22 two RTL8153
  adapters never worked through a dongle. On 2026-10-26 a plain micro-B-to-A OTG
  cable (no power input) ran the generic one at high speed, powered from the
  Zero's port (§5).
- **⚠ Plug the adapter in with the Pi off.** Hot-plugging it browns the Pi out.

### 2.1 Power-injected USB extension (fallback, not needed so far)

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
RXD (pin 10), 115200. Free grounds are pins 20, 25, 30, 34 and 39; pin 6 is the
knob chain's and pins 9 and 14 the buttons' (§7). With a Glasgow on port B, Pi TXD → B0 and Pi RXD → B1:

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

**Resolved, 2026-10-26: it was the dongle.** The fix was a plain micro-B-to-A OTG cable, with no power input. On the Zero W, with the same card, the generic RTL8153 plugged in and a cold boot:

| Check | Result |
|---|---|
| Enumeration | `usb 1-1: new high-speed USB device` at 5.6 s; r8152 binds it as `eth0` |
| Supply | `throttled=0x0` |
| Link to the 5A-75B (direct Cat6) | **1000 Mb/s full duplex**; `colorlight` profile up at 192.168.75.1; card at .39 in ARP |
| Renderer (`--res 64 --fps 30`) | Plasma shows on the panels; 27k packets, 0 TX errors. **10–15 fps**, CPU-bound (0 % idle: python 63 %, sys + softirq 30 %) |

- Still plug the adapter in before power-on.
- `pf-splash` step 5 in `ExecStartPre` fails with `no wired link` if the Cat6 isn't in at boot. It's harmless; the renderer starts anyway.

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
5. Buttons (§7), once the overlay is in: `evtest` lists `btn0`–`btn3`, and each
   press shows up as a key event.

## 7. Buttons (GPIO)

Four momentary buttons on the top wall, so patterns change without the k0 + k3
chord, on GPIO the knob chain and the console don't use. Each button joins its
GPIO to ground. There are no resistors: the Pi's internal pull-up holds the line
high, and a press pulls it low.

| Button | Where (top wall, seen from the front) | Colour | Does | Pi header pin | Pi name | Ground |
|---|---|---|---|---|---|---|
| **btn0** | left end, 1st of the row | blue | **previous** demo | **pin 11** | GPIO17 | pin 9 |
| **btn1** | 2nd | orange | **select** | **pin 13** | GPIO27 | pin 9 |
| **btn2** | 3rd | blue | **next** demo | **pin 15** | GPIO22 | pin 9 |
| **btn3** | right end, alone | black | **sleep** (blackout) | **pin 16** | GPIO23 | pin 14 |

```
            Pi Zero W 40-pin header (top view, SD-card end at the left)

                    (7) (8)   TXD     console (§4)
  common ── GND     (9) (10)  RXD     console (§4)
    btn0 ── GPIO17 (11) (12)
    btn1 ── GPIO27 (13) (14)  GND     ── btn3's ground
    btn2 ── GPIO22 (15) (16)  GPIO23  ── btn3
                   (17) (18)  GPIO24  ┐
                   (19) (20)  GND     │ kept free for two more
                   (21) (22)  GPIO25  ┘
```

Pins 9, 11, 13 and 15 sit next to each other in the odd-numbered column, so one
4-way female header (or a 4-pin Dupont housing) carries the row's ground and its
three buttons. The sleep button is a 2-way on pins 14 and 16, side by side in the
even column. Its lead runs the length of the top wall, ~270 mm, under the top
doubler.

**What they do.** Playing: previous and next step through the demos on the
current shelf, and select opens the menu. In the menu, previous and next step
along the shelf (the knobs keep their menu jobs: k1 shelves, k3 brightness), and
select picks the highlighted demo and closes the menu, as "close" does in the
Patternflow modals. Sleep blanks the panels and wakes them again. The k0 + k3
chord stays, for a box without buttons. Not in the renderer yet.

- **⚠ 3.3 V only, and switch to ground.** Never wire a button to 5 V. If the
  buttons have built-in LEDs, power those separately, not through these pins.
- **Room for more.** GPIO24 (pin 18) and GPIO25 (pin 22), with GND on pin 20,
  are the next two, in the even-numbered column. The knobs (GPIO2/3) and the
  console (GPIO14/15) leave 22 GPIO for buttons in all. Past that, MCP23017
  expanders on the knob chain (0x20–0x27) don't clash with the knobs.
- **The buttons** are the 12 mm waterproof momentaries in rev 2.2's keyed holes
  (`BTN_*` in `enclosure.fs`); their pack comes in white, black, red, yellow and
  green, so the blue and orange ones are a separate buy. Each one's colour,
  role and GPIO is in the button's name in the Onshape model.
- **Software (not set up yet).** `dtoverlay=gpio-key` in `config.txt`, one line
  per button, turns each into a key on `/dev/input`, debounced by the kernel.
  Pull-up and active-low are its defaults:
  ```
  dtoverlay=gpio-key,gpio=17,keycode=59,label=btn0
  dtoverlay=gpio-key,gpio=27,keycode=60,label=btn1
  dtoverlay=gpio-key,gpio=22,keycode=61,label=btn2
  dtoverlay=gpio-key,gpio=23,keycode=62,label=btn3
  ```
  The keycodes are F1–F4 (neutral codes), so the renderer, not the wiring,
  decides what each button does. The renderer's user, `patternflood`, needs
  group `input` as well as `i2c`.
