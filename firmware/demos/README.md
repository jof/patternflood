# Demos

Interactive demos for the 2×2 (128 × 128), written once and run in either place.
There are 67: 19 of ours, plus all 48 of upstream Patternflow's patterns, run
natively ([below](#upstream-patternflow-presets)). That's the 34 firmware presets and
our ports of the 14 that upstream only had as web sources.

| | Knobs | Frames | Renders on |
|---|---|---|---|
| **Bench, now** | FeatherS3 knob bridge on ash's USB (`serial:`) | ssh to durian, which forwards UDP to the card (`pipe:durian`) | ash |
| **Production** | 4991s on the Pi 5's I²C (`i2c:1`) | the Pi's own Ethernet (`udp:`) | Pi 5 |
| **No hardware** | a random or scripted player (`auto`, `script:`) | an animated GIF (`preview:`) | anywhere |

Durian is a dumb pipe. `pipe:durian` sends `pfd/r75_pipe.py`'s source on the ssh
command line, so nothing is installed there. The pipe then turns
`(port, length, payload)` records on stdin into UDP datagrams. Durian's only
requirement is an address on the card's link (below). The demos never know which
path they're on: the Pi 5 port is a change of flags.

```sh
./run.py                                   # bench defaults: FeatherS3 on ash, pipe through durian
./run.py --demo sand                       # start on a given demo
./run.py --knobs i2c:1 --out udp           # Pi 5
./run.py --demo etch --knobs auto --out preview:/tmp/etch.gif --seconds 8
./run.py --list
```

Needs `numpy` and `pyserial` (bench only). Text (demo names, labels) needs
Pillow; without it the demos run without text. The upstream presets need `g++`
and the `upstream/` clone; without them they're skipped. It imports `r75_frame`,
`seesaw` and `knob_renderer` from `../colorlight`.

## Menu

**Hold the two outer knobs (k0 and k3) for a second.** In the menu:
- **k0** steps through the demos (clockwise = next), and **k1** jumps eight at a time. They switch
  live behind the overlay and keep their state. The overlay shows the demo's place in the list
  and its group (patternflood or patternflow).
- **k3** sets brightness (0.3 at start).
- **A click on any knob** closes the menu, or it closes after 6 s with no input.

The power cap is the same as `knob_renderer.py`'s and still uncalibrated: 1.2 A
a panel and 4 A in total, from estimated duty.

## Knobs

`k0`–`k3` are the 4991s in address order (0x37–0x3A). The bridge shows them red, green,
blue and yellow at boot. **The seat layouts assume k0 is the leftmost knob.**
Squash and Cycles put k0 on the left wall, k3 on the right wall, k1 on the floor and
k2 on the ceiling. Both use the same four colours.

Conventions shared by every demo, so they transfer:
- **Discrete actions fire on a click** (release, under 0.45 s, no turn in it), not on
  press. That frees press-and-hold for continuous actions (pour, drain, scrub-hold) and
  for push-and-turn as a second layer.
- **Clockwise is positive.** The 4991s count down when turned clockwise, so `pfd/io.py`
  negates them at the source. Demos never see the raw sign.
- **Spinning fast accelerates** (`rt.accel`). One detent is still one pixel when you
  go slowly, but you can cross the panel in about a turn.
- **Knob lights carry state:** join state, lock, recharge, reverse. They aren't decoration.

## The demos, as hypotheses

Each one exists to test one idea about what makes four knobs and a 128-pixel square fun.
Notes from playing them should go here.

| Demo | Knobs | Hypothesis | Watch for |
|---|---|---|---|
| **Classic** | hue, speed, scale, level; click: next, freeze, reset, blackout | *The baseline.* Turning parameters on a generative pattern is pleasant but not sticky. | How long before you stop touching it. Every other demo should beat this number. |
| **Etch** | x, y, colour, brush; click: mirror x, mirror y, rainbow, shake; hold k3 + turn: fade | **Direct manipulation:** two knobs steering one point (the Etch A Sketch) feels precise and owned, and acceleration keeps 128 px reachable without losing the single pixel. | Whether diagonals feel possible (two hands), whether the mirrors make people draw more, and whether anyone finds hold-and-turn without being told. |
| **Squash** | one paddle per knob; turn to join; click just before a hit to smash | **Knobs are the native Pong controller** (Pong shipped with pots), and four seats on a square make a social toy. Turning your knob is how you join. | Whether players work out which wall is theirs from colour alone. The knob row is linear and the walls aren't, which is the biggest mapping risk here. Is the smash timing learnable? |
| **Cycles** | one rider per knob: a detent is a 90° turn; click: boost | **Detents as discrete commands:** one click, one turn. A tactile mapping, crisper than a continuous one. | Over-turning on a fast flick (each detent queues a turn, at most two), and whether clockwise = right reads naturally for riders heading down the screen. |
| **Sand** | k0 tilts the box; k1 spout, hold to pour; k2 colour; hold k3 drain, click obstacles | **A physical metaphor:** turning a knob to rotate gravity feels like tilting a box in your hands. | Which direction feels right. Clockwise turns the box clockwise, so gravity swings anticlockwise on screen. Flip it if people expect the opposite. Is hold-to-pour satisfying? |
| **Harmono** | k0/k1 tune two pendulums; k2 spin; k3 trail | **Tuning to a lock rewards like an instrument.** Near a simple ratio the figure snaps still and the lights flare. | Whether people hunt for locks unprompted, and whether the lock window (0.8 % of the ratio, a couple of detents) is too sticky or too slippery. |
| **Rewind** | k0 scrubs generations; k1 play speed through zero into reverse; click k2: drop a pattern | **Time as a knob:** scrubbing history with a jog wheel is a knob-only pleasure. Change the past and watch a new future. | Whether "reverse" on k1 is understood without the history bar, and whether people drop patterns in the past on purpose. |
| **Reaction** | k0 feed, k1 kill, k2 speed, k3 colour; click k1: preset | **Delayed response:** a slow, emergent reply (seconds, not frames) is still fun when the results are this varied. | Impatience. If people turn and turn again before the field responds, the lag is too long, and a faster sim or a preview inset is needed. |

Added on 2026-10-23, each testing something the first eight don't:

| Demo | Knobs | Hypothesis | Watch for |
|---|---|---|---|
| **Rotor** | k0 heading; hold k1 thrust; click/hold k2 fire; hold k3 shield | **Absolute mapping:** the knob *is* the ship, with one revolution of k0 = one revolution of the ship (`DETENTS_PER_REV`, assumed 24). No acceleration and no rate. | Whether it feels like holding the ship. If the ship's turn doesn't match the knob's, the detent count is wrong: count a revolution and fix `runtime.DETENTS_PER_REV`. |
| **Echo** | press (later also turn) the knobs to repeat the sequence | **The knob lights as the primary display.** The sequence plays on the caps as well as the panel. From round 5, **turn direction is a second vocabulary**: steps can be "turn this one clockwise". | Whether players watch the caps or the panel; whether turn steps feel fair or like a trick; whether pressing wobbles the knob. Turns while a knob is held are ignored for that reason. |
| **Rocket** | k0 aim; hold k1 charge, release to fire; k2 colour; k3 burst | **Hold to charge, release to fire:** press duration as an analogue input, with a predicted arc while aiming. | Whether the 1.2 s charge feels right, and whether the arc makes aiming a skill or takes the fun out of it. |
| **Vault** | each knob rolls its own tumbler; click to try | **Feedback through the knob alone:** each cap warms as its number gets close, the same within ±1, so the last step is a guess. One knob, one tumbler, in the row's order. | Whether people find the warmth readable without being told; whether the ±1 ambiguity is tension or annoyance. |
| **Mandala** | k0 orbits the pen, k1 radius, k2 colour, k3 symmetry | **Polar against Cartesian:** the same drawing toy as Etch, but turning the angle knob literally orbits the pen. | Compare with Etch. Which do people draw more with, and which knob do they reach for first? |

Five more, each taking one of Seunghun Lee's visual ideas from upstream and making it
something you play rather than tune:

| Demo | After Lee's | Knobs | Hypothesis | Watch for |
|---|---|---|---|---|
| **Droplet** | 0524-2 droplet refraction, 0530 water surface | each knob a dropper: turn to slide, click to drip, hold to rain | **A click as a physical event:** a real wave equation, refracting a tiled pool floor, with caustics. Four droppers, so ripples from different hands interfere. | Whether people play together, timing drops to make patterns, or each just pokes at their own. |
| **Terrain** | 0519-1 isocontours, 0529 contour lines | k0/k1 brush, k2 piles or digs earth, k3 sea level | **Turning moves earth,** and **a global reveal knob** (sea level) gives what you sculpted a meaning. | Whether k3 makes people go back and sculpt more: dig a channel, then flood it. |
| **Glitch** | 0519-2 glitch type, 0511 sliding rows, 0602 colour separation | k0 tear, k1 colour split, k2 smear, k3 crush; click k0 changes the text | **A knob as a whammy bar:** each knob injects one unmistakable effect that springs back over ~1.6 s. Hold to pin it. And a clock gives the box a reason to sit on a desk. | Whether the spring-back reads as playful or as the knob "not working". |
| **Kaleido** | 0522 quad-fold, 0526 kaleidoscope, 0622 mirror grid | k0 barrel, k1 zoom, k2 mirrors, k3 colour; click k0 shake, k3 oil | **The literal physical gesture:** twisting k0 twists the barrel, and real beads tumble under gravity inside the cell. | Whether the lag of falling beads feels analogue and pleasant, or mushy next to Classic's instant response. |
| **Pool** | 0624 isometric pillars | each knob a wave paddle on one side (Squash's seats) | **Rate as input:** every detent is a push, so spinning faster makes bigger waves. Four people can collide waves. | Whether people discover that speed matters, and whether waves from opposite sides read in isometric 3D. |

And one generator:

| Demo | After | Knobs | Hypothesis | Watch for |
|---|---|---|---|---|
| **Resort** | Hiroshi Nagai's city-pop illustrations: flat colour, cobalt skies, pools, palms, white modernist blocks | k0 time of day (click: let the day pass), k1 pan along the coast (click: cruise), k2 horizon (click: mirror), k3 colour story, continuous (click: album-cover frame) | **One story knob:** a single continuous control (noon → golden hour → sunset → night) can carry a whole demo. And **a world you pan through,** with parallax, rather than scenes you switch between. | Whether people sweep k0 back and forth to watch the light change, or park it at sunset; whether they explore the coast or cruise and watch. |

Resort's coast is generated lot by lot (`World` in `pfd/demos/resort.py`), so it is endless, and each stretch
always looks the same:
- Lots are 128 px wide: pools, sun decks, beach, and a coast road. They come in runs, and every six lots hold
  all three kinds.
- Kinds meet along a diagonal curb, and the shore's depth eases between lot centres, so it never steps.
- Panning eases towards the knob. Clouds move at a third of the speed, the stars barely move, and the sun
  stays put.
- k3 turns the hue of the sky, sea, sun and pool continuously, in YIQ so brightness holds, through cobalt,
  lagoon, vivid and violet. Pools turn only a third as far, so they never go green.
- Speed: lots are cached per lighting state, and palms are cached as part maps, recoloured per lighting and
  drawn in seven real sway poses (picked per frame, so the whole tree bends). Frames take about 0.9 ms on ash while panning, and under 3 ms while turning
  the light or colour.

Cross-cutting questions, worth noting on every demo:

1. **Acceleration curve.** 1× to about 6 detents/s, then up to 6×. Too twitchy? Too slow?
2. **The menu chord.** Is holding two knobs discoverable, and does it ever fire by accident (e.g. two Squash players clicking at once)?
3. **Knob lights.** Are they read at a glance, or ignored? If they're ignored, they may be worth less than the NeoPixel power and the light-slit work in the enclosure.
4. **Attract mode.** `--knobs auto` plays the demos by itself. Does an idle box running it draw people in?

## Upstream Patternflow presets

All 34 of upstream's preset patterns (`upstream/firmware/patternflow/presets/`, minus the
calibration card) run here **natively and unchanged**:

- `upstream_host/build.py` copies the preset headers and upstream's portable cores (math,
  colour, noise, tables, params) into `upstream_host/build/tree/`. It overlays small host
  stand-ins for the hardware-specific headers (`upstream_host/shim/`: `Arduino.h`, `config.h`,
  canvas, display, encoders).
- It generates a C API over every preset's namespace, and compiles everything into one shared
  library in about 2 s.
- `pfd/upstream.py` loads that library with ctypes and wraps each preset as a demo named
  `pf <name>`:
  - Knob turns become `knobDeltas`: raw detents, no acceleration, as upstream.
  - Presses become `btnPressed` (edge) and `btnHeld`.
  - Upstream's saturation boost (1.62) is applied. Gamma and the current cap are ours, as for
    every demo.
- `run.py` builds the library on first start if it's missing.

```sh
./upstream_host/build.py                # 128 x 128 (the default; run.py does this itself)
./upstream_host/build.py --size 128x64  # upstream's own panel size, for comparison
```

**Geometry.** Upstream panels are 128 × 64. The presets are compiled with `PANEL_RES` set
to 128 × 128, and almost all of them scale to fill the square. Three are portrait patterns:
upstream's device usually stands on end, and these draw with "up" along the panel's +x, as
upstream's canvas maps a 64 × 128 frame.
- **Midsummer Sea** and **Firefly Hollow** are turned a quarter anticlockwise to stand upright,
  and still fill the square.
- **Breakout Arcade**'s layout needs exactly 64 rows, so it runs at 128 × 64, turned, as a
  centred 64 × 128 column.

The table is `PORTRAIT`/`PORTRAIT_NATIVE` in `pfd/upstream.py`, and was chosen by eye from
contact sheets at both sizes.

**Known quirk:** `0519-1` starts black. Its knob 1 defaults to 0, which puts the whole field
below zero. Turn k0 up about ten detents. That is upstream's behaviour, kept as it is.

**Licence:** the presets are CC BY-SA 4.0 (upstream's). They are read from the gitignored
`upstream/` clone at build time and never committed here. The shim and build script are ours (MIT).

**On the Pi 5:**
1. Install `g++`.
2. Clone upstream next to the repo:
   ```sh
   git clone https://github.com/engmung/patternflow upstream && git -C upstream checkout 87700bd
   ```
   The `desktop` branch's only change is the HUB75 pinout, which no preset touches.
3. Start `run.py`. The first start builds the library for aarch64.

### The web-only patterns (ported here)

Fourteen of upstream's patterns exist only as JavaScript, in `upstream/web/src/lib/presets/`:
0516, 0517, 0519-2, 0524, 0524-2, 0526, 0529, 0530, 0609, 0614, 0614-2, 0619, 0622 and 0624.
Upstream turns JavaScript into firmware headers with an AI prompt (`web/src/lib/lab/cppPrompt.ts`).
We did the same, following that prompt and the knob conventions of upstream's existing ports,
into `upstream_host/web_ports/preset_*.h`. `build.py` adds them to the library.

- **They're derived from CC BY-SA 4.0 sources,** so they carry that licence and Lee's
  attribution in their headers, and they are committed here (share-alike).
- **Every port was checked against the original.**
  `upstream_host/tools/compare.py` runs the JavaScript in Node and the C++ side by side, for
  the same frames, at two knob settings (upstream's defaults, and every knob turned). It
  compares the last frames:
  ```sh
  upstream_host/tools/compare.py ../../upstream/web/src/lib/presets/pattern-0526.ts \
      upstream_host/web_ports/preset_0526.h --size 128x128 --png /tmp/0526.png
  ```
  All 14 match within 1.9/255 mean difference and 1 % of pixels; six match exactly. The rest
  is the sine lookup table's error landing on hard thresholds.
- **Fidelity over ESP32 rules.** Upstream's prompt forbids double maths and sine-hash noise,
  because the ESP32 is slow at the one and its sine table bands the other. These ports run on
  x86 and a Pi 5, where both are native. So 0517 keeps the JavaScript's sine-hash noise, and
  0519-2 decides its cross-arm edges in double precision. Each spot is marked in the code.
- **The checker also caught a slip in one of upstream's own ports.** `preset_0519_1.h` uses
  knob 3's raw value (0–4.9) where the JavaScript uses it normalized (0–1), so zoom comes out
  about 2.5× too large. It's upstream's file, so it's left as it is and noted here.

Not ported: the community library on patternflow.work. Any community `.h` should build the
same way: drop it in `upstream_host/web_ports/`.

## Speed

Measured per frame on ash:
- Most of our demos take 0.4–1.1 ms (render, gamma, cap). Rotor, Echo, Rocket, Vault and
  Mandala take under 1 ms; Droplet, Terrain and Glitch about 1 ms; **Kaleido 3.1 ms**; and
  Pool 1.4 ms (it was 8.3 ms before drawing a diagonal of pillars at a time).
- **Reaction takes 4.3 ms** at 10 iterations a frame.
- The upstream presets take **0.1–0.6 ms** natively.

The Pi 5 has 16.7 ms a frame at 60 fps and is a few times slower per core, so it should fit
everything. If Reaction doesn't, turn its k2 (speed) down.

## Bench network: durian

- Durian's USB NIC (`enx000000000000`) carries the card link through the NetworkManager
  profile `colorlight`, added 2026-10-23: static 192.168.75.1/24, no default route, and
  autoconnect priority 50 over the stock DHCP "Wired connection 2". It's the same idea as the
  Pi appliance's profile.
  - Don't add the address by hand with `ip addr`. NetworkManager's DHCP attempt timed out
    and wiped it within minutes.
  - When the address is missing, frames route over Wi-Fi to the home router with no error.
    `run.py` reports healthy sends while the card keeps showing its spinner.
  - Check it with `ssh durian ip route get 192.168.75.39`.
- ash → durian runs over Wi-Fi. About 27 MB/s through ssh was measured; frames need about 2.9 MB/s.
  `pipe:` keeps only the newest frame, so a stall drops frames instead of building lag.
  Drops show in the 5-second status line.
- Durian stays awake on AC power (set 2026-10-23):
  - The GDM greeter's `sleep-inactive-ac-type='nothing'` is in `/etc/gdm3/greeter.dconf-defaults`. The original is kept as `.orig-2026-10-23`.
  - jof's GNOME session has the same setting.
  - `HandleLidSwitchExternalPower=ignore` is in `/etc/systemd/logind.conf.d/50-patternflood-ac-awake.conf`.
  - Battery behaviour is unchanged.

## Adding a demo

Subclass `pfd.runtime.Demo` in `pfd/demos/`, and add it to `ALL` in `pfd/demos/__init__.py`.
The interface is in `pfd/runtime.py`'s docstring. `render()` returns float RGB in perceptual
units; the runtime applies gamma, brightness and the current cap. Check it with a preview
before it goes near the panels:

```sh
./run.py --demo NAME --knobs "script:0.5:k0+12,1.5:k1 click,2:k3 down,3:k3 up" --out preview:/tmp/x.gif
```
