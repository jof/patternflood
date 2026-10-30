# Wiring

Everything electrical in the Rev 2.7 desktop build, in one place. For the order
to do it in, see [`BUILD.md`](BUILD.md). The design reasoning is in
[`driver-colorlight.md`](driver-colorlight.md).

```
   mains ─► IEC inlet (switch, 1 A T fuse) ─► LRS-50-5 ─┬─ 5 V ─► 4 × panel power
                                                        ├─ 5 V ─► Colorlight 5A-75B
                                                        └─ 5 V ─► Pi 5 (USB-C pigtail)

   Pi 5 ─ gigabit Ethernet ─ Cat6 ─► 5A-75B ─ HUB75 J5 J8 J4 J1 ─► the four panels
   Pi 5 ─ I²C (header pins 1 3 5 6) ─► 4 × Adafruit 4991 encoders, daisy-chained
   Pi 5 ─ GPIO (header) ─► 4 push buttons
   Pi 5 ─ Wi-Fi ─► your network (ssh, updates)
```

## 1. Knob chain → Pi header (I²C)

The four Adafruit 4991 encoders are daisy-chained by their STEMMA QT
connectors. The free end goes to the Pi's 40-pin header.

| STEMMA QT wire | Signal | Pi header pin | Pi name |
|---|---|---|---|
| **Red** | V+ | **pin 1** | **3V3** (not 5 V) |
| **Black** | GND | **pin 6** | GND |
| **Blue** | SDA | **pin 3** | GPIO2 / SDA1 |
| **Yellow** | SCL | **pin 5** | GPIO3 / SCL1 |

```
            Pi 40-pin header (pin 1 is the square pad)

     Red ──  3V3   (1) (2)   5V
    Blue ──  SDA   (3) (4)   5V
  Yellow ──  SCL   (5) (6)   GND  ── Black
                   (7) (8)   TXD    console (§5)
                   (9) (10)  RXD    console (§5)
                  ...          buttons: §4
```

- **Cable:** a STEMMA QT / Qwiic to female-socket cable (Adafruit 4397).
- **⚠ 3.3 V only.** Each 4991 pulls SDA and SCL up to its own supply. On 5 V
  it would put 5 V on GPIO2/3, which are not 5 V-tolerant.
- **Addresses:** 0x37, 0x38, 0x39 and 0x3A (k0–k3), set by the solder jumpers
  (A0; A1; A0 + A1; A2). Chain order doesn't matter: knobs are numbered by
  address. **k0 is the leftmost knob** seen from the front.
- **One I²C master.** If you used a FeatherS3 knob bridge on the bench
  ([`firmware/knob_bridge/`](../../firmware/knob_bridge/)), unplug it from the
  chain: two masters corrupt each other's transfers.
- **Pull-ups:** the Pi's on-board 1.8 kΩ in parallel with four boards' 10 kΩ
  gives about 1.1 kΩ. Fine at 3.3 V and 100 kHz. Keep the chain under ~1 m.
- **Power:** the knob lights follow the panel brightness. Four boards draw about
  50 mA dim, and up to ~250 mA from the Pi's 3V3 with all four lit white.

## 2. Pi → Colorlight card (Ethernet)

A ~20 cm flat Cat6 patch cable from the Pi's own jack to either of the card's.
The card **won't link at 100 Mbit**, so it must be a gigabit port, which the
Pi 5's is.

The appliance gives any wired interface **192.168.75.1/24**, with no default
route. The card is at **192.168.75.39**: it answers ARP, but not ping.

### HUB75: card → panels

One panel per output, each ribbon into the panel's **IN** (on the left, seen
from behind):

| Panel (seen from the front) | Card connector | receiver75 slot |
|---|---|---|
| Upper left | **J5** | 9 |
| Upper right | **J8** | 15 |
| Lower left | **J4** | 7 |
| Lower right | **J1** | 1 |

All upright. `firmware/colorlight/r75_frame.py` maps a 128 × 128 frame onto
these slots, and the card's boot splash has the same map compiled in. Change
both if you rewire.

## 3. Power

From the LRS-50-5, **trimmed to ~5.15 V** at the bus. Mains wiring and safety
are in [`BUILD.md` §8](BUILD.md#8-mains-and-the-5-v-bus); read that first.

| Run | Carries | 22 AWG strands per pole |
|---|---|---|
| Supply → bus | up to 10 A (8 A planned) | **4**, same length, one 1.5 mm² ferrule at the supply |
| Bus → each panel | 1.4 A capped, 2.4 A full white | 1 (2 for headroom) |
| Bus → Pi 5 | ~1.6 A | 1 (2 for less drop) |
| Bus → Colorlight (D5V / GND terminal) | ~0.8 A | 1 |

- **Four strands are 16 AWG.** 22 AWG is 0.33 mm², so four make 1.30 mm².
  Bundled in a closed box a 22 AWG strand is good for about 2.5–3 A, so heat
  sets the count as much as voltage drop does.
- **The Pi is fed through a 5 V → USB-C pigtail** from the bus, never through
  a panel's harness. The pigtail does no USB-PD, so set
  `PSU_MAX_CURRENT=5000` with `sudo rpi-eeprom-config -e`, or the Pi limits
  its USB ports and warns about the supply.

## 4. Buttons (GPIO)

Four momentary buttons on the top wall. Each joins its GPIO to ground. There
are no resistors: the Pi's internal pull-up holds the line high, and a press
pulls it low.

| Button | Where (top wall, seen from the front) | Colour | Does | Pi header pin | Pi name | Ground |
|---|---|---|---|---|---|---|
| **btn0** | left end, 1st of the row | blue | **previous** demo | **pin 11** | GPIO17 | pin 9 |
| **btn1** | 2nd | orange | **select** | **pin 13** | GPIO27 | pin 9 |
| **btn2** | 3rd | blue | **next** demo | **pin 15** | GPIO22 | pin 9 |
| **btn3** | right end, alone | black | **sleep** (blackout) | **pin 16** | GPIO23 | pin 14 |

```
            Pi 40-pin header

                    (7) (8)   TXD     console (§5)
  common ── GND     (9) (10)  RXD     console (§5)
    btn0 ── GPIO17 (11) (12)
    btn1 ── GPIO27 (13) (14)  GND     ── btn3's ground
    btn2 ── GPIO22 (15) (16)  GPIO23  ── btn3
                   (17) (18)  GPIO24  ┐
                   (19) (20)  GND     │ free for two more
                   (21) (22)  GPIO25  ┘
```

Pins 9, 11, 13 and 15 sit next to each other in the odd column, so one 4-way
Dupont housing carries the row and its ground. The sleep button is a 2-way on
pins 14 and 16. Its lead runs the length of the top wall, ~270 mm, under the
top doubler.

- **⚠ 3.3 V only, and switch to ground.** Never wire a button to 5 V. If the
  buttons have LEDs, power those separately.
- **Room for more:** GPIO24 (pin 18) and GPIO25 (pin 22), with GND on pin 20.
  Past that, MCP23017 expanders on the knob chain (0x20–0x27) don't clash with
  the knobs.

**What they will do.** Playing: previous and next step through the demos on
the current shelf, and select opens the menu. In the menu, previous and next
step along the shelf, and select picks the highlighted demo. Sleep blanks the
panels and wakes them again. The k0 + k3 chord stays, for a box without
buttons.

**Software: not done yet.** The plan is the kernel's `gpio-key` overlay, which
turns each button into a debounced key on `/dev/input` (pull-up and active-low
are its defaults), so the renderer decides what each one does:

```
dtoverlay=gpio-key,gpio=17,keycode=59,label=btn0
dtoverlay=gpio-key,gpio=27,keycode=60,label=btn1
dtoverlay=gpio-key,gpio=22,keycode=61,label=btn2
dtoverlay=gpio-key,gpio=23,keycode=62,label=btn3
```

The keycodes are F1–F4. The renderer's user, `patternflood`, will need group
`input` as well as `i2c`. Once that's in, `evtest` lists `btn0`–`btn3`.

## 5. Serial console

The appliance puts the console on the header: GPIO14 TXD (pin 8) and GPIO15 RXD
(pin 10), 115200 baud (on the Pi 5, `dtparam=uart0_console` moves it there from
the debug connector). Use any 3.3 V USB serial adapter; free grounds are pins
20, 25, 30, 34 and 39. With a Glasgow on port B (Pi TXD → B0, Pi RXD → B1):

    glasgow run uart -V B=3.3 --rx B0 --tx B1 -b 115200 tty

## 6. Bring-up check

1. Power on with the knobs and the card connected. The first boot takes a few
   minutes: it installs packages over Wi-Fi and compiles upstream's patterns.
2. `ssh patternflood.local`
3. `i2cdetect -y 1` shows 37, 38, 39 and 3a.
4. `journalctl -u patternflood -f` shows a `knobs:` line, then frames per
   second every 5 s.
