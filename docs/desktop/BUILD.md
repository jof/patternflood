# Building the Patternflood desktop

A 256 mm square LED instrument: four P2 GOB panels in a 2 × 2 (128 × 128 px),
four knobs with light rings, four push buttons, and a laser-cut birch ply box
that runs off mains. A Raspberry Pi 5 renders the frames, and a Colorlight
5A-75B running open gateware drives the panels.

This guide builds **Rev 2.7**, the revision that is built and running
([`hardware/REVISIONS.md`](../../hardware/REVISIONS.md) has the history). Every
cut file, model and script referred to here is in this repository.

![The etched outer faces as cut: bezel, left, right and top walls, back cover](../../hardware/laser/art/preview.png)

The box stands upright, 293 × 373 × 61 mm: the display at the top, the four
knobs below it on the left, the supply behind the bezel on the right.

> ⚠️ **This build has mains wiring inside a wooden box.** The supply's input
> terminals are open screw terminals behind a removable back. Read
> [§8](#8-mains-and-the-5-v-bus) before wiring anything, and if you are not
> comfortable working on mains, have someone who is check your wiring.

**Contents**

1. [What you need](#1-what-you-need)
2. [Flash the Colorlight card](#2-flash-the-colorlight-card)
3. [Make the Pi's SD card](#3-make-the-pis-sd-card)
4. [Bench test before you cut](#4-bench-test-before-you-cut)
5. [Test cuts](#5-test-cuts)
6. [Cut the box](#6-cut-the-box)
7. [Glue and assemble the box](#7-glue-and-assemble-the-box)
8. [Mains and the 5 V bus](#8-mains-and-the-5-v-bus)
9. [Electronics in](#9-electronics-in)
10. [First power-up](#10-first-power-up)
11. [Known gaps](#11-known-gaps)

---

## 1. What you need

### Electronics

| Qty | Part | Notes |
|---|---|---|
| 4 | **Waveshare RGB-Matrix-P2-64x64-B** (GOB) | 128 × 128 mm, FM6124 column drivers, RUC7258 row drivers, 1/32 scan. Measured in [`design-notes/mechanical-plan.md`](design-notes/mechanical-plan.md) §2.1. Other panels need a different box: hole positions differ between panel types ([`enclosure-lasercut.md`](enclosure-lasercut.md) §11) |
| 4 | HUB75 ribbon cables, 16-way IDC | One per panel, from the card to the panel's IN |
| 4 | Panel power leads | One per panel, to the 5 V bus |
| 1 | **Colorlight 5A-75B**, v8.x | Ours is a v8.2. The gateware is built for the v8.0 pinout, which v8.2 shares |
| 1 | **Raspberry Pi 5** | With the official **Active Cooler**. The box is closed |
| 1 | microSD card | 16 GB or more |
| 1 | 5 V → USB-C pigtail | Feeds the Pi from the 5 V bus. No USB-PD |
| 1 | Flat Cat6 patch cable, ~20 cm | Pi to card. The card will not link at 100 Mbit |
| 4 | **Adafruit 4991** I²C QT rotary encoder breakout | Each has a NeoPixel, which lights the knob's ring |
| 4 | **Adafruit 377** rotary encoder (EC11) | Soldered to the 4991s |
| 4 | Knobs for a 6 mm D shaft, about 1" (25.4 mm) | The light slits sit just outside a 1" knob's skirt |
| 3 | STEMMA QT / Qwiic cable, 100 mm | Between the encoders |
| 1 | STEMMA QT to female sockets (Adafruit 4397) | Last encoder to the Pi's header |
| 4 | 12 mm waterproof momentary push buttons, with a keyed lip | The VanMoof S3 boost-button type (Amazon B07F24Y1TB has the drawing). Two blue, one orange, one black, in the build as drawn |
| — | Dupont housings (one 4-way, one 2-way) and hook-up wire | Button leads |

### Power

| Qty | Part | Notes |
|---|---|---|
| 1 | **Mean Well LRS-50-5** | 5 V, 10 A |
| 1 | IEC C14 inlet with rocker switch and 5 × 20 mm fuse holder | AC-14-F16A; cutout 46.75 × 27.25 mm, flange screws 40 mm apart |
| 1 | **1 A time-delay (T) fuse**, 5 × 20 mm | Sized for the supply's 45 A inrush, not its load. A fast-blow fuse will trip at switch-on |
| 1 | IEC power cord | |
| — | 18 AWG mains wire (L, N, earth), insulated fork terminals, heatshrink | |
| 1 | Insulating boot or shroud for the supply's input terminals | |
| — | 22 AWG red and black wire | The bus is four strands per pole ([§8](#8-mains-and-the-5-v-bus)) |
| — | 1.5 mm² (16 AWG) ferrules, 10 mm | One per bundled pole at the supply |

### Enclosure

| Qty | Part | Notes |
|---|---|---|
| 8 | **3 mm Baltic birch ply, B/BB, 12 × 24"** | 6 for the box, 1 for the test cuts, 1 spare. Every part fits a 305 mm wide bed |
| — | PVA wood glue | The laminations are glued; the box's finger joints are glued |
| — | Transfer tape (masking) | For the good face, against smoke marks |
| — | Printer paper | Knob light diffusers |
| 4 | Feet, ≥ 8 mm tall (optional) | The intake vents are in the bottom wall. It runs fine standing flat for a while; on feet for long runs at brightness |

### Fasteners

Every nut sits in a laser-cut three-layer pocket, so no inserts are needed.

| Qty | Fastener | Where |
|---|---|---|
| 6 | M3 × 10 ultra-low socket head (Ø5.5 × 1.0, e.g. Accu ZUL602); DIN 7984 low heads also work | Back cover |
| 8 | M3 × 8 + M3 washer | Panels to the upper and lower braces |
| 8 | M3 × 14 + M3 washer | Panels to the middle brace |
| 4 | M3 × 16 | Electronics tray to the middle brace |
| 4 | M3 × 8 | Colorlight to the tray |
| 4 | M2.5 × 8 + M2.5 nut | Pi 5 to the tray (its holes are 2.7 mm) |
| 2 | M3 × 8, no washer | Supply, up through the bottom wall (heads sit in recesses) |
| 1 + 1 | M3 × 16 and M3 × 12, each with a washer and nut | IEC inlet flange |
| 16 | M3 nuts | 6 back cover, 4 tray, 4 Colorlight, 2 IEC |

Screw lengths are taken from the model. The panel screws give about 4 mm of
thread in the panel's inserts. Don't go longer on the supply (it allows 5 mm
of screw into its case) or on the tray (M3 × 18 touches the panel).

### Tools

- A CO₂ laser with at least a 600 × 305 mm cut area. The files are set up for
  an xTool P2 and xTool Creative Space (XCS), but they are plain DXF and SVG.
- Calipers.
- A JTAG adapter for the card's one-time flash: a
  [Glasgow](https://glasgow-embedded.org/) (what we used), or an FT232H with
  openFPGALoader (what receiver75 documents; not tried here).
- Soldering iron (encoders, buttons, maybe the card's JTAG header), wire
  strippers, a ferrule crimper, small screwdrivers, a 2 mm hex key.
- Clamps and two flat boards for the glue-ups.
- A multimeter, for trimming the supply.
- A Linux machine with an SD card reader, to provision the Pi's card.

---

## 2. Flash the Colorlight card

The card ships with Colorlight's own gateware, which needs Windows software to
configure. Patternflood replaces it with
[receiver75](https://github.com/dgym/receiver75), open gateware that takes
frames as UDP packets. The version here adds a boot splash (a spinner and
progress bar while the Pi boots). It is in
[`firmware/colorlight/receiver75/`](../../firmware/colorlight/receiver75/README.md),
as patches and a ready-built bitstream.

1. **Back up the stock flash first**, so the card can go back to stock. With a
   Glasgow on port A ([wiring](../../firmware/colorlight/README.md#jtag-with-a-glasgow):
   J27 TCK, J31 TMS, J32 TDI, J30 TDO, ground from a spare HUB75 connector;
   don't connect the board's 3.3 V):

   ```sh
   cd firmware/colorlight
   glasgow script ecp5_flash_dump.py jtag-probe -V 3.3 -f 2000 -- stock.bin
   ```

   Keep `stock.bin` safe, and out of the repository: it is Colorlight's
   proprietary gateware.

2. **Write receiver75:**

   ```sh
   glasgow script ecp5_flash_write.py jtag-probe -V 3.3 -f 2000 -- receiver75/receiver75-splash-5f2185b.bit 0
   ```

   The stock flash is write-protected. The script lifts the protection, erases,
   writes, verifies every byte and puts the protection back.

3. **Power-cycle the card.** It boots dark, shows a dim spinner, and answers
   ARP at **192.168.75.39** (it doesn't answer ping). That address is built in.

With an FT232H instead of a Glasgow, `openFPGALoader --unprotect-flash
--write-flash` should do the same job. Keep the JTAG leads short: long leads
caused bit errors here ([`firmware/colorlight/README.md`](../../firmware/colorlight/README.md)).

---

## 3. Make the Pi's SD card

[`firmware/pi-controller/`](../../firmware/pi-controller/README.md) turns a
stock Raspberry Pi OS Lite (trixie, arm64) card into the appliance. It boots
straight into the demos, reads the knobs on I²C, and sends frames to the card
over the Pi's own Ethernet.

1. Write the image and **compare it after writing**. One write on a bench
   reader had a bad stretch:
   ```sh
   xz -dk 2026-10-06-raspios-trixie-arm64-lite.img.xz
   sudo dd if=2026-10-06-raspios-trixie-arm64-lite.img of=/dev/sdX bs=4M conv=fsync
   sudo cmp -n $(stat -c %s 2026-10-06-raspios-trixie-arm64-lite.img) 2026-10-06-raspios-trixie-arm64-lite.img /dev/sdX
   ```
2. Fetch upstream Patternflow (its patterns are compiled on the Pi):
   ```sh
   git clone https://github.com/engmung/patternflow upstream
   git -C upstream checkout 87700bd
   ```
3. Optionally fetch the community patterns
   ([`firmware/demos/README.md`](../../firmware/demos/README.md#community-patterns)).
4. Mount both partitions and provision, as root:
   ```sh
   sudo firmware/pi-controller/provision_card.py --boot /mnt/boot --root /mnt/root \
       --userconf userconf.txt --wifi-ssid YOUR_SSID --wifi-pass-file wifi.pass \
       --ssh-key ~/.ssh/id_ed25519.pub
   ```
   `userconf.txt` holds `USER:HASH` (make the hash with `openssl passwd -6`),
   and `wifi.pass` holds the Wi-Fi passphrase. The provisioning host needs
   `aarch64-linux-gnu-gcc` to build the boot-splash helper.

The first boot takes a few minutes: it installs packages over Wi-Fi and
compiles upstream's patterns. After that the Pi is reachable as
`patternflood.local`, and `firmware/pi-controller/update_pi.py` pushes code
changes to it.

---

## 4. Bench test before you cut

Get pixels on the panels on the bench, before any wood. It is much easier to
debug a ribbon or a panel lying flat.

1. Lay the four panels face down in their 2 × 2, as they will sit in the box
   (seen from behind, upper-left is on your right).
2. Ribbons from the card to each panel's **IN** connector, which is on the left
   seen from behind:

   | Panel (seen from the front) | Card connector |
   |---|---|
   | Upper left | **J5** |
   | Upper right | **J8** |
   | Lower left | **J4** |
   | Lower right | **J1** |

   J2, J3, J6 and J7 stay free. The mapping is also compiled into the card's
   splash, so keep to it.
3. Power the panels, the card and the Pi from the LRS-50-5 (temporary leads are
   fine on the bench; [§8](#8-mains-and-the-5-v-bus) has the gauges), Cat6 from
   the Pi to either of the card's jacks, and the encoder chain to the Pi
   ([`wiring.md`](wiring.md) §1).
4. Power on. The card shows its spinner within a couple of seconds, the bar
   steps forward as the Pi boots, and the demos start about 17 s after power-on.

If the picture is split or a quadrant is wrong, check the ribbons against the
table. `firmware/colorlight/r75_slot_ids.py` draws each output's slot number,
and `r75_frame.py` has a seam test.

---

## 5. Test cuts

The cut files have the stock thickness (**3.18 mm**) and the kerf (**0.15 mm**)
built in. Tabs, pockets and holes are compensated for them. Before you cut the
box, check that your laser and your ply match.

1. Caliper your sheet in several places.
2. Cut [`hardware/laser/test-cuts/`](../../hardware/laser/test-cuts/README.md)
   on a 12 × 12" sheet: finger-joint and tenon combs, nut pockets, a hole
   gauge, a panel fit jig, board templates, the IEC cutout and the supply's
   holes. Each piece's README section says what a good result looks like.
3. Cut [`hardware/laser/test-cuts/since-rev-1/`](../../hardware/laser/test-cuts/since-rev-1/README.md)
   too. It covers the two-sheet knob stack with its light slits and dial, the
   Pi 5 template, the button holes, and an etch sampler to tune the Score
   setting on (a fine, even line, and a QR code that scans).

If the joints are loose or tight, or your stock isn't 3.18 mm, change
`#thickness` and `#kerf` in the model and re-export the cut files
([`onshape-workflow.md`](onshape-workflow.md),
`hardware/cad/tools/export_dxf.py`, then `nest_sheets.py`).

---

## 6. Cut the box

[`hardware/laser/sheets/`](../../hardware/laser/sheets/README.md) has every part
nested on **six 12 × 24" sheets**, with a picture and a parts table for each.
That README covers the settings in detail. In short:

- **Load `sheet-N.svg`** for the sheets with etched art (1 to 3). In XCS,
  set **red = Cut** and **blue = Score**, put the blue layer above the red,
  and process **by layer**, so the art is scored before anything is cut loose.
  Sheets 4 to 6 have no art; their DXFs are fine.
- **Good face up, nothing mirrored.** Parts are drawn as seen from outside the
  box, so the face up on the bed becomes the outside. Mask it.
- **Inner shapes first** (XCS's default). The knob ribs are nested inside the
  inner bezel's display aperture on sheet 4.
- The art is a lot of line: about 20 to 30 minutes for the back cover's score,
  5 to 15 for the bezel and each wall.
- Cut the **paper knob diffusers** too
  ([`hardware/laser/diffusers/`](../../hardware/laser/diffusers/README.md)).

Label the parts as they come off; the sheet pictures tell them apart.

---

## 7. Glue and assemble the box

The bezel, every wall and the back cover are two sheets glued together. Glued,
two sheets bend as one section about eight times as stiff as a single sheet.
Rev 1 used single sheets, and pushing a knob visibly flexed the box.

### 7.1 Laminate

PVA, clamped flat between boards. Keep glue out of mortises, holes and nut
pockets.

1. **Inner bezel to outer bezel**, face down, aperture edges flush. A panel
   dropped into the aperture squares them up.
2. **Each doubler to its wall.**
   - Side walls: push a brace and the stiffener shelf through the wall's and
     doubler's mortises, dry, to register them. Keep the doubler's front edge
     6.36 mm back from the wall's front edge; a two-sheet offcut is the gauge.
   - Bottom wall: line up the doubler's supply holes with the wall's using two
     M3 screws.
   - Top wall: centred, with the same 6.36 mm setback.
3. **Back cover doubler** to the inside of the back cover, in the band between
   the two rail stacks.

### 7.2 The box

Bezel face down on a flat surface.

1. **Knob ribs** into their slots in the inner bezel, standing up, glued.
2. **Walls**, glued at the finger joints. Then the **stiffener shelf**: glue its
   front edge, and where the ribs' top edges meet it. Glue the ribs' bottom
   edges to the bottom doubler as that wall goes on.
3. **Braces**, tenoned through the side walls. The middle brace is three
   sheets with the tray's four nuts trapped in the middle one: fit the front
   and middle sheets, drop four M3 nuts into the middle sheet's hex pockets,
   then fit the rear sheet. Its sheets are clamped together by the panel
   screws, not glued.
4. **Rail stacks**, top and bottom, glued: rail C (tenoned into the side
   walls), then rail B with three M3 nuts in its hex pockets, then rail A. The
   back cover's screws come through rail A into those nuts.

### 7.3 Front-panel parts

- **Encoders**: solder each 377 encoder to its 4991. Set the address jumpers so
  the four boards are **0x37, 0x38, 0x39 and 0x3A** (A0; A1; A0 + A1; A2). The
  board at 0x37 is k0, and it must be the **leftmost** knob seen from the front;
  the demos' seat layouts assume it.
- A **paper diffuser** in each knob pocket against the outer bezel sheet, then
  the encoder through it, its nut on the front. The nut clamps the outer sheet
  only; the inner sheet is pocketed.
- **Buttons** into the top wall's keyed holes. Left to right seen from the
  front: blue (previous), orange (select), blue (next), and the black one
  (sleep) alone at the right end. Their nuts clamp the outer wall; the top
  doubler is notched behind them.
- Daisy-chain the encoders with the STEMMA QT cables, through the cable holes
  in knob rib 1. Order doesn't matter: the knobs are numbered by address.

### 7.4 Panels

Each panel's two registration pins drop into holes in a brace, and four M3
screws with washers go through the braces into its inserts: **M3 × 8** through
the upper and lower braces, **M3 × 14** through the three-sheet middle brace.
The brace holes are exact vertically and have 1.5 mm of play sideways, so push
the panels together by hand before tightening. The seams are the most visible
thing on the box.

Panel screws are only reachable with the electronics tray out.

---

## 8. Mains and the 5 V bus

The supply sits in the bottom corner on the bottom doubler, against the bezel,
fixed by two **M3 × 8** screws up through the bottom wall. Their heads sit in
recesses, flush, so tighten gently: the supply rests on the doubler and the
screws only locate it. **Its terminals must face the back cover**, or they
can't be reached. The IEC inlet is in the right wall beside it.

**Wire the supply before the rear rails get in the way.** There is about
19 mm above its terminals with the back cover off.

### Mains

Four things are not optional:

1. **Insulate the input terminals.** L, N and earth are open screw terminals,
   and the back comes off with six screws. Use insulated fork terminals with
   heatshrink, and a boot or shroud over the input block. The IEC switch is the
   second layer.
2. **Earth the supply.** IEC earth → the supply's FG terminal. The case is
   metal; the box isn't, so nothing else needs bonding.
3. **1 A time-delay fuse** in the inlet.
4. **Restrain the wiring.** Strain-relieve and tie down the mains leads at the
   inlet, and keep them away from the 5 V side and the I²C chain. It is a box
   that gets picked up.

The terminals are, in order: **L, N, FG (earth), −V, +V.**

### The 5 V bus

The supply has one +V and one −V screw, so the loads meet on a bus. In 22 AWG:

| Run | Carries | Strands per pole |
|---|---|---|
| Supply → bus | up to 10 A (8 A planned) | **4**, same length, crimped into one 1.5 mm² ferrule at the supply |
| Bus → each panel | 1.4 A capped, 2.4 A at full white | 1 (2 for headroom) |
| Bus → Pi 5 (USB-C pigtail) | ~1.6 A | 1 (2 for less drop) |
| Bus → Colorlight terminal (D5V / GND) | ~0.8 A | 1 |

**Trim the supply to about 5.15 V** with its adjustment pot, measured at the
bus, so the Pi sees at least 5.0 V under load.

The Pi takes its power from the bus, never through a panel's harness. The
pigtail does no USB-PD, so the Pi assumes a 3 A supply and warns. Tell it
otherwise, once it's running:

```sh
sudo rpi-eeprom-config -e      # add: PSU_MAX_CURRENT=5000
```

Power budget: the supply is good for 8 A continuous. The Pi takes ~1.6 A and
the card ~0.8 A, which leaves ~1.4 A per panel. A typical pattern draws about
0.8 A per panel; full white draws 2.4 A. The renderer caps each frame's
estimated current, so full-white frames are scaled down rather than tripping
the supply ([`driver-colorlight.md`](driver-colorlight.md) §4).

---

## 9. Electronics in

The card and the Pi live on a removable **electronics tray**: two sheets
screwed to the back of the middle brace, the boards on its rear face, component
side facing the back cover.

1. **On the bench**, tray face down: M3 nuts into the rear sheet's hex pockets
   for the card, M2.5 nuts for the Pi, a spacer ring over each, then the boards.
   **M3 × 8** through the Colorlight, **M2.5 × 8** through the Pi. The card lies
   horizontal, its RJ45 end toward the left; the Pi stands on end at the left,
   Ethernet jack pointing down past the tray's edge. Fit the Active Cooler.
2. **Plug the four HUB75 ribbons into the card** (J5, J8, J4, J1, as in
   [§4](#4-bench-test-before-you-cut)).
3. **Tray in from the back.** Plug each ribbon into its panel's IN, then four
   **M3 × 16** through the tray and a spacer ring into the brace's nuts.
4. **Cat6** from the Pi's jack round the tray's bottom edge to the card.
5. **Knob chain** to the Pi's header, at **3.3 V**:

   | STEMMA QT wire | Pi pin |
   |---|---|
   | Red (V+) | **1** (3V3, *not* 5 V) |
   | Blue (SDA) | **3** |
   | Yellow (SCL) | **5** |
   | Black (GND) | **6** |

6. **Buttons**, each switching its GPIO to ground (no resistors; the Pi's
   pull-ups are used). The row is one 4-way housing on pins 9 (GND), 11, 13 and
   15; the sleep button is a 2-way on pins 14 (GND) and 16. The sleep lead runs
   ~270 mm along the top wall, under the top doubler.
7. **5 V** to the panels, the card's terminal and the Pi's pigtail, from the
   bus.
8. Back cover on: six M3 × 10 low-head screws into the nuts in rail B.

[`wiring.md`](wiring.md) has the whole wiring in one place, with header
diagrams and the serial console.

---

## 10. First power-up

1. Switch on at the inlet. Within two seconds the card shows its spinner and the
   first segment of a five-step bar.
2. The bar steps forward as the Pi boots. The first demo starts about 17 s after
   power-on (the Pi's bootloader takes ~9 s of that).
3. Turn the knobs: their rings light up, following the brightness.
4. **Hold the two outer knobs (k0 and k3) for a second** for the menu. k1 picks
   a shelf, k0 a demo, k3 sets brightness, and a click on any knob closes it.
   [`firmware/demos/README.md`](../../firmware/demos/README.md) describes the
   demos and the shelves.

If something is wrong, `ssh patternflood.local`:

```sh
i2cdetect -y 1                  # 37 38 39 3a: the four knobs
journalctl -u patternflood -f   # a "knobs:" line, then frames per second every 5 s
```

Settings (start demo, brightness, which shelves) are in
`/etc/default/patternflood`. Edit, then `sudo systemctl restart patternflood`.

**Switching it off at the wall is safe** once it's running: the journal is in
RAM, writes are rare, and it was tested by forced reboots. Avoid it during an
`apt upgrade`. A hardware watchdog reboots a hung Pi, and the service restarts
a renderer that stops sending frames.

---

## 11. Known gaps

These are open in Rev 2.7:

- **The buttons are wired but not read yet.** The `gpio-key` overlay lines and
  the renderer side are in [`wiring.md`](wiring.md) §4, not yet in the
  provisioned image. The knob chord (k0 + k3) does everything meanwhile.
- **The power cap is uncalibrated.** It assumes 2.4 A per panel at full white,
  measured upstream on a different driver. Measure one panel at full white,
  and at full red, green and blue, on this card.
- **No read-only root filesystem.** Power cuts have been safe in testing, but
  an overlay root is still the plan.
- **The supply's terminal shroud** is not yet a drawn part. Use a commercial
  boot or heatshrink.
- No microphone: the audio-reactive demos need a sound source on the Pi.
