# Demos

Interactive demos for the 2×2 (128 × 128), written once and run in either place.
There are 139: 91 of ours, plus all 48 of upstream Patternflow's patterns, run
natively ([below](#upstream-patternflow-presets)). That's the 34 firmware presets and
our ports of the 14 that upstream only had as web sources. Fifty-six of ours are
[Patternflow-style originals](#our-originals-on-the-patternflow-shelf), shelved among SeungHun's.
On top of those, the [community's patterns](#community-patterns) run natively on a shelf of
their own: every one on community.patternflow.work with a firmware header, 211 of them as of
2026-10-27.

| | Knobs | Frames | Renders on |
|---|---|---|---|
| **Bench, now** | FeatherS3 knob bridge on ash's USB (`serial:`) | UDP over the LAN, straight to the card (`auto`); or via durian (`pipe:durian`) | ash |
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
./run.py --only upstream                   # just SeungHun's presets (native code: the Pi Zero's choice)
./run.py --only play,audio                 # just these shelves
```

Needs `numpy` and `pyserial` (bench only). Text (demo names, labels) needs
Pillow; without it the demos run without text. The upstream presets need `g++`
and the `upstream/` clone; without them they're skipped. It imports `r75_frame`,
`seesaw` and `knob_renderer` from `../colorlight`.

## Menu

**Hold the two outer knobs (k0 and k3) for a second.** The demos sit on four shelves:

| Shelf | What's on it |
|---|---|
| **Play** | our interactive demos: the knob toys and games |
| **Audio** | visualizers, and some of the Play demos played by the music |
| **Patternflow** | upstream's 48 patterns |
| **Community** | the community wall's patterns, most liked first (only once synced: [below](#community-patterns)) |

In the menu:
- **k1** moves between shelves, back to wherever you were on each.
- **k0** steps along the shelf. Demos switch live behind the overlay and keep their state.
  Spin it to skip ahead (`rt.accel`), which is how to cross the Community shelf.
- **k3** sets brightness (0.3 at start).
- **k2,** on the Patternflow and Community shelves only, turns *audio knobs* on or off (below).
- **A click on any knob** closes the menu, or it closes after 6 s with no input.

A demo's shelf is its class's `group`: `play` (the default), `audio`, `patternflow` or `community`.

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

Five more, each taking one of SeungHun's visual ideas from upstream and making it
something you play rather than tune:

| Demo | After SeungHun's | Knobs | Hypothesis | Watch for |
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

## Audio

Every demo can hear music: `rt.audio`, refreshed each frame (`pfd/audio.py`). On the bench
it listens to whatever ash is playing, through the default output's PulseAudio/PipeWire
monitor, so nothing has to be wired in.

```sh
./run.py --demo spectrum                                  # --audio pulse is the default
./run.py --audio-delay 0.25                               # if beats land early or late
./run.py --audio file:~/Music/set.mp4@600 --demo pulse    # a track, silently, in real time
./run.py --audio alsa:hw:1                                # the Pi 5, with a line-in or mic
```

**Sync.** The analysis runs on audio held back by `--audio-delay`, so beats land on the panel
when they're heard. Bluetooth (A2DP, SBC; e.g. to headphones) trails its own
monitor by ~0.2 s, and the panel shows a frame ~30-50 ms after the analysis sees it, so the
default for a `bluez` sink is 0.15 s (0 for wired output). Fine-tune it live with k2 in Tempo.

**What the analyzer hears**, at 48 kHz in 512-sample hops (93.75 a second), at about 1 % of one core:
- **Level and spectrum:** RMS and 24 log-spaced bands from 30 Hz to 16 kHz, each against its own
  slow peak; bass, mid and treble summaries.
- **Onsets:** spectral flux, with kick, snare and hat split by range.
- **Tempo:** autocorrelation of the last 8 s of onsets.
  - Each candidate is scored with its bar (4×) and two-bar (8×) repeats and its off-beat (½), under
    a broad prior.
  - The multiples are what reject the 3:2 alias breakbeats invite: 174 BPM heard as 116.
  - A new tempo has to persist: about 2 s for an unrelated one, 6 s for a 3:2 relation. An exact
    octave never replaces the current tempo, since it's the same groove.
- **Beats:** a phase-locked clock, aligned to the onsets four times a second.
  - The onsets it aligns to weight *kicks*: low onsets whose added energy is gone within 85 ms,
    unlike an off-beat bass note.
  - Corrections scale with how decisively one phase wins, so the clock coasts through rolls and
    risers, and a big jump has to repeat three times running.
- **Downbeats:** which of the four beats carries the most low-end onset and spectral change,
  accumulated over many bars.
- **Phrases:** 8-bar phrases, *predicted*, not just noticed.
  - Bar-by-bar novelty (the last four bars against the four before) is accumulated by bar
    position mod 8, and boundary events fire on the grid.
  - **Drops:** a bar starting with over 6× the low end of the previous four bars.
  - **Impacts:** any big change, whatever its loudness. The last ~0.4 s is set against the
    *strongest* and *most similar* moments of the ~6 s before, not their average. So a warm bass
    drop that isn't loud still counts (it outdoes every recent low end), and a stab that recurs
    every two bars doesn't (it's been heard).
    - It also counts the sound turning into something not heard in those 6 s, or the level
      passing the loudest recent moment.
    - A drop that swells in over a bar, from an intro whose hits already reach most of the way,
      is caught by the last 0.6 s against the *average* of the 8 s before (Calibre's "Moonlight"
      at 1:29). That term sits out for 8 s after any hit, so one drop is one impact.
    - It fires once per change, re-arming only after the contrast settles, and gives a strength
      (0.55-1).
    - The Audio shelf's visualizers **flare** on it: lit parts blaze towards white and everything
      lifts, near full strength on every hit, fading over about half a second. Tempo, Waterfall
      and Scope don't.
    - Milk punches its zoom and fires a white ring; Pulse bursts and Spectrum shockwaves.
    - Tempo shows the live contrast (purple bar) and the envelope after a hit (gold).
  - **Builds:** rising highs over thinning bass.

**Scores**, from `tools/audio_test.py synth`: a generated house track with known truth, with
a kick on every beat, so downbeats must come from the bass line.

| Tempo | Tempo error | Beats (F) | Downbeats | Phrases | Drops |
|---|---|---|---|---|---|
| 100 | +0.26 % | 0.92 | 0.78 | 0.50 | 1 of 1, 1 false |
| 128 | +0.21 % | 0.91 | 0.77 | 0.71 | 0 of 1 |
| 174 | −0.09 % | 0.94 | 0.94 | 0.86 | 1 of 1 |

On real drum & bass (the Boiler Room sets in `~/Music`), it holds 174–175 or 87 at confidence
0.8–1.0. A cold start can still catch the 3:2 alias (~117) for half a minute.

**When it's wrong, people can fix it**, in Tempo:
- **k1 click:** tap the tempo (it holds for 8 s).
- **k3 click:** mark the one.
- **k0:** shift the phrase grid a bar.
- **k2:** the A/V delay.

**Demos**, on the Audio shelf. All need audio; without it they run on a quiet 120 BPM stand-in.
Winamp's visualizers inspire the first six.

**The Milk family**, after MilkDrop (`pfd/demos/milk.py`, one engine, five families of presets):
- Each frame, the last one is resampled through a per-pixel motion field, as MilkDrop does:
  - **zoom,** pushed by the bass, and growing towards the edges for tunnels;
  - **turn,** pushed by the mids, twisting the middle more for whirlpools;
  - **a warp** pushed by the treble, a centre that wanders with the bass, a drift and a stretch,
    and edges that can wrap.
- **On top:** waves (circle, spiral, line, double, dots, spectrum, stereo XY) and shapes, solid or
  *textured*: filled with a shrunken copy of the screen, MilkDrop's signature look.
- **On the way out, never into the buffer:** video echo (the frame zoomed and flipped over itself),
  a kaleidoscope fold, a colour map of brightness, and a flash of inversion on a drop.
- **A rhythm layer from the beat tracker, on every preset:**
  - **Each beat:** a zoom punch decaying through the beat, a wave that swells on the kick, a hue
    step, and a warp wobble that cycles in beat time.
  - **Each bar:** the turn swings one way and back the next, and the downbeat stamps a ring that
    the field carries off.
  - **Across the phrase:** zoom and warp ramp up over the eight bars, then let go.
  - **At the boundary:** the next preset cuts in over half a bar with a flash. A drop punches the
    zoom, flashes and inverts, and jumps to a random preset.
- Measured on a drum & bass set, against the loudness-only version:
  - Frame-to-frame motion roughly doubled.
  - The first quarter of each beat now moves 1.8-1.9x as much as the rest (Milk, Milk Tunnel).
  - Downbeats now move ~2x as much as other beats; before, they were indistinguishable.
- Frames take 1.3-2.8 ms on ash.
- Knobs: k0 preset (click for a random one), k1 hue, k2 trails, k3 sensitivity.

| Demo | Presets | Look |
|---|---|---|
| **Milk** | bloom, vortex, ripple, mandala, nebula | the classic: waves flowing out through zoom, turn and warp |
| **Milk Tunnel** | wormhole, hyperspace, twister, spectrum tunnel | edge-growing zoom and a twisted middle, centre wandering with the bass |
| **Milk Flame** | bonfire, blue gas, aurora, embers | upward drift through a wobble, coloured by a heat, gas or aurora map |
| **Milk Mirror** | hexes, quad bloom, triad, rose window | kaleidoscope folds over spinning screen-textured shapes |
| **Milk Echo** | hall of mirrors, double vision, tiles, ghosts | video echo and wrapping edges |

And AVS:

| Demo | What | Knobs |
|---|---|---|
| **Superscope** | point shapes made of the music, after AVS superscopes: spectrum ring, a tunnel of waveform rings launched on each beat, a torus knot breathing with the bass, a sphere pushed out by the spectrum; the shape changes each phrase | k0 shape, k1 hue, k2 trails, k3 spin |

Some of our Play demos, played by the music (`pfd/demos/played.py`). They keep their own knobs, so
you can still steer, and the music does what a hand would:

| Demo | From | What the music does |
|---|---|---|
| **Prism** | Kaleido | turns the barrel a nudge each bar (beads settle and tumble through the view), kicks tap the tube, phrases change the mirrors, drops pour in new beads |
| **Rain** | Droplet | kicks drop big drops, snares middling ones, hats drizzle |
| **Spores** | Reaction | kicks seed it, the section's intensity sets its pace, each phrase starts a new preset fresh, drops wipe and reseed |
| **Lissajous** | Harmono | glides to a new locked ratio each phrase, turns a quarter each bar, pumps on the kick, longer trails when it's loud |
| **Night Drive** | Resort | cruises ten pixels a beat, the day moves on a twelfth each phrase (the sunset follows the set), palms sway with the bass, drops turn the colour story |

And the analysis made visible:

| Demo | What | Knobs |
|---|---|---|
| **Tempo** | the tracker shown: BPM and confidence, beats of the bar (the one in red), bars of the phrase, onset trace under the beat grid, spectrum, drops and builds | k0 phrase shift, k1 tap, k2 A/V delay, k3 mark the one |
| **Spectrum** | 24 bands with falling caps, as bars, mirrored or radial; caps flash on the beat, colour steps each phrase, drops send a shockwave | k0 style, k1 hue, k2 fall, k3 gain |
| **Scope** | an oscilloscope with phosphor: circle, stereo XY (a goniometer), or a triggered wave | k0 mode, k1 persistence, k2 gain, k3 hue |
| **Waterfall** | a scrolling spectrogram with the analyzer's grid drawn in: beat ticks (the one in red), phrase lines, drop lines | k0 speed, k1 palette, k2 gain, k3 click: marks |
| **Pulse** | rings on the kick, a figure turning once a bar, colour per phrase, builds tighten and drops burst; soft, never strobing | k0 hue, k1 symmetry, k2 reactivity, k3 trails |

**The upstream patterns, too.** In the menu, k2 turns on *audio knobs*. Then, as in
upstream's audio edition, sound turns each upstream pattern's four knobs:
- k0 follows the mids, k1 the level, k2 the bass and k3 the treble.
- Each rises fast and falls slowly, through upstream's own `knobAudioActive`/`knobAudioValue`
  fields, so every one of the 48 reacts without a line of it changing.

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

- **They're derived from CC BY-SA 4.0 sources,** so they carry that licence and SeungHun's
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

### Our originals on the Patternflow shelf

Thirty-eight patterns of ours, in Patternflow's manner: each runs by itself, and the four knobs turn
its qualities, not a game. They're in our own style, which is print-shop and demoscene,
and each sits on the shelf right after the preset of SeungHun's it riffs on.

| Demo | After | What it is | Knobs (turn; click) |
|---|---|---|---|
| **Bit Tunnel** | pf 0521 | A flight down a tunnel papered with XOR texture, fogged into the dark through a dither screen. The cross-section morphs round → square → diamond → petals. | k0 speed, through zero to reverse; k1 roll; k2 bit pattern (xor, 0521's xor mask, and, or, checker, xor mod, each with 1–5 bits); k3 inks. Click: k0 stop, k1 next shape, k2 chunky pixels, k3 next screen. |
| **Obra** | pf 0522 | A raymarched solid (torus, metaballs, twisted box, gyroid ball, octahedron, gimbal rings) lit by a circling light, printed in 2–5 inks through a screen, with an ink outline. | k0 turns it; k1 morphs to the next form; k2 screen (Bayer 8/4/2, blue noise, halftone dots, engraving lines, IGN); k3 inks. Click: k0 auto-spin, k2 chunky, k3 outline. |
| **Riso** | pf 0528 | A moving colour field printed as three halftone plates at 15°, 75° and 45°. The plates turn against each other, so the rosettes and moiré churn, and drifting misregistration fringes the colours. | k0 dot size; k1 how fast the screens turn; k2 misprint; k3 inks (riso, RGB light, sunset, mint, or ink on lit paper). Click: k0 next picture, k1 square the screens. |
| **Pixel Sort** | pf 0519-2 | A landscape (sunset, aurora, orbs) melted by sorting each run of bright pixels by brightness. Runs also break at intervals that crawl, so the streaks drip. | k0 threshold (it sweeps by itself until turned); k1 direction; k2 drift speed; k3 hue. Click: k0 auto sweep, k1 next scene, k2 sort the other way. |
| **Smoke** | pf Vector Field Flow | Incense smoke, dithered. Dye rises from a source and rides a curl-noise flow (no divergence, so it never bunches or thins) whose swirl grows with height: a smooth ribbon at the stick that breaks into curls as it climbs. Each frame it's advected semi-Lagrangian style and fades slowly. | k0 turbulence; k1 moves the source; k2 screen; k3 inks. Click: k0 gust, k1 puff, k2 chunky, k3 a second source. |
| **Moon** | pf Poincaré Sphere | A world in the dark, lit through its phases: a cratered moon (bump-mapped bowls and rims, dark maria), an Earth (continents, ice caps, drifting clouds, a sun glint on the sea, an atmosphere's rim), or a banded giant whose rings take its shadow and cast theirs on it. Analytic sphere, one-pixel twinkling stars. | k0 turns it; k1 moves the sun; k2 screen; k3 inks. Click: k0 next world, k1 auto phase, k2 chunky. |
| **Sea** | pf Midsummer Sea | Open water from a boat riding the swell: eight deep-water waves (each at the speed its length gives it), raycast column by column so crests hide the troughs behind them. Fresnel reflection of the sky, ripples that only tilt the normals, and a glitter path from the moon, or the sun at sunset. | k0 swell; k1 moves the moon; k2 screen; k3 inks. Click: k0 storm (with lightning), k1 sunset, k2 chunky. |
| **Caustics** | pf 0530 | Sunlight through moving water, netting a pool floor. Light through each point of the surface lands where the slope throws it, splatted over the four nearest floor pixels; the focused places blaze. The tile grout wobbles by the same refraction, and pebbles (click k0, or every kick) send rings out. | k0 chop; k1 depth (focus); k2 screen; k3 inks. Click: k0 a pebble, k1 tiles, k2 chunky. |
| **Galaxy** | pf Chromatic Vortex | A spiral galaxy whose arms are a density wave: 40 000 stars ride slightly out-of-round orbits whose shapes twist with radius, so they crowd into arms that persist while the stars flow through them. Dust lanes trail the arms; tilted in 3D. | k0 arm twist; k1 tilt; k2 screen; k3 inks. Click: k0 arm count (2–4), k1 a bar, k2 chunky. |
| **Valley** | pf 0624 | Low flight over a tiling ridged-fractal range, Comanche style (each column a ray across the heightmap). Sun-shaded slopes, snow on the peaks, lakes that mirror the sky, haze; the plane banks into its turns and steers clear of high ground. Dawn, night (moon and wheeling stars) or dusk. | k0 steers; k1 altitude; k2 screen; k3 inks. Click: k0 autopilot, k1 time of day, k2 chunky, k3 new land. |
| **Op Art** | pf Warped Wave | Hard black and white, after Bridget Riley: wavy lines whose spacing breathes, a checkerboard crowding into a drifting fold, a grid under a roaming lens, two crossing ring sets, a twisting sunburst. | k0 line spacing; k1 warp; k2 picture; k3 inks. Click: k0 invert, k1 hold still, k2 screen, k3 chunky. |
| **Bonfire** | pf Firefly Hollow | Flames over crossed logs: a teardrop of heat eaten by fractal noise that streams upward faster than the flame, so tongues lick and break off; wind leans the tips. Sparks rise and waver; the ground catches the glow. | k0 fire size; k1 wind; k2 screen; k3 inks. Click: k0 stoke, k1 calm, k2 chunky. |
| **Mandel** | pf Retro Digital Tapestry | An endless dive into the Mandelbrot set: a million times in on one of six deep places, then out and on to the next. Points iterate only until they escape (or are caught in a cycle), with a smooth count whose bands flow inward. | k0 zoom (takes over for 20 s); k1 colour flow; k2 screen; k3 inks. Click: k0 next place, k1 turn the view, k2 chunky. |
| **Lava** | pf 0520 | A lava lamp: wax blobs warm over the bulb, rise, cool at the cap and sink, stretching as they move and merging as metaballs (compact ones, so they only touch when close) over a pool on the bottom. | k0 heat; k1 how much wax; k2 screen; k3 inks. Click: k0 shake, k2 chunky. |
| **Tesla** | pf MagVortex | A plasma globe: jagged filaments, re-drawn each frame from a few octaves of wiggle, writhe from the electrode to the glass, with forks. Hold k0 to touch the glass and every filament leaps to your finger. | k0 moves your finger (hold to touch); k1 filaments; k2 screen; k3 inks. Click: k1 forks, k2 chunky. |
| **Window** | pf 0609 | Rain on glass over a city out of focus. A mist of droplets, and larger drops that are lenses, each showing the bokeh small and upside down; heavy drops slide, clearing a path and leaving droplets. | k0 rain; k1 focus (bokeh size); k2 screen; k3 inks. Click: k0 the wiper, k1 lightning, k2 chunky. |
| **Life** | pf TileWaves | Conway's Life on a wrapping board: newborn cells blaze, old ones glow, the dead leave fading ghosts (gliders trail comets). It reseeds when it settles: soup, a glider fleet, an R-pentomino, an acorn. | k0 speed; k1 ghost length; k2 screen; k3 inks. Click: k0 pause, k1 reseed, k2 big cells. |
| **Jellyfish** | pf 0529 | Glowing jellies climbing through the deep in fits: each bell squeezes (narrower, taller) and shoves itself up, then relaxes and sinks a little. Tentacles are chains of links, each easing after the one before, so they stream and ripple. Marine snow drifts past. | k0 pulse rate; k1 current; k2 screen; k3 inks. Click: k0 all pulse at once, k2 chunky. |
| **Aurora** | pf 0602 | Northern lights over mountains and a still lake: folding curtains brightest at the hem, made of fine rays that flicker and travel, over a faint airglow. Substorms (now and then, or each phrase) brighten and quicken everything; the lake mirrors it with a slow ripple. | k0 activity; k1 curtain height; k2 screen; k3 inks. Click: k0 substorm, k1 the lake, k2 chunky. |
| **Warp** | pf 0510 | A 3D starfield drawn as streaks from where each star is to where it was, so cruise shows points and speed shows lines. A jump winds up into a tunnel of light, holds, and drops out with a flash among new stars. A big hit in the music jumps. | k0 throttle; k1 steer; k2 screen; k3 inks. Click: k0 jump, k2 chunky. |
| **Snow** | pf 0515-3 | A village at night in three layers of snowfall (far small and slow, near big and swaying). Chimneys smoke downwind, windows go on and off (in a warm spot ink printed over the palette), and drifts build where flakes land. | k0 snowfall; k1 wind; k2 screen; k3 inks. Click: k0 clear the drifts, k1 lights, k2 chunky. |
| **Helix** | pf 0512 | A DNA double helix (10.5 base pairs a turn, with the minor groove) turning and rising forever. Every atom is a shaded sphere impostor in a depth buffer, so the strands pass properly in front and behind. Unzipping parts the base pairs from the top down. | k0 spin; k1 tilt; k2 screen; k3 inks. Click: k0 unzip, k2 chunky. |
| **Fireworks** | pf a big hit | Rockets climb on sparking trails and burst into shells thrown evenly over a sphere: peonies, drooping willows with long golden trails, tilted rings, and crackle that pops. The sky keeps faint trails, and each burst lights the town's skyline. With music, shells go up on the kicks and each phrase brings a finale. | k0 launch rate; k1 shell size; k2 screen; k3 inks. Click: k0 a volley, k1 the finale, k2 chunky. |
| **Gears** | pf Origin | A clockwork train of meshing gears (one tooth size, each set at the angle that slots its teeth into its neighbour's gaps; checked to overlap by a few pixels at most). Brushed-brass shading under the cross-hatch screen, like an engraving. With music it ticks forward on each beat, like an escapement. | k0 crank speed; k1 a new train; k2 screen; k3 inks. Click: k0 reverse, k2 chunky. |
| **Pendulums** | pf Wave Saw | The pendulum wave from above: 18 pendulums whose lengths make the first swing 51 times a minute, the next 52, and so on, so they fall into snakes, interleaved lines and scatter, and line up again every 60 s. Shaded balls, depth-sorted. | k0 speed; k1 view; k2 screen; k3 inks. Click: k0 release them together, k2 chunky. |
| **Spiro** | pf Lissajous Weave | A spirograph: a wheel rolling inside a 96-tooth ring draws a hypotrochoid onto a fading page, so fresh ink is white and ages down through the inks. The wheel and the pen's hole drift, laying each figure over the ghost of the last. | k0 pen speed; k1 wheel size (teeth); k2 screen; k3 inks. Click: k0 clear the page, k1 a new figure, k2 chunky. |
| **Orrery** | pf 0513 | A sun and five planets on tilted orbits with Kepler's periods (radius to the 1.5), one ringed, two with moons. Each world is lit from its sun, so it waxes and wanes as it goes round, and crosses the sun as a dark disc. | k0 time; k1 tilt; k2 screen; k3 inks. Click: k0 reverse time, k1 orbits, k2 chunky. |
| **Flock** | pf Vector Field Flow | A murmuration: 1800 starlings align with, close on and keep off the birds near them (a grid of cells stands in for "near"), hold together as one cloud steered by a drifting roost, and flee a falcon, whose wake folds and hollows the flock. Dark birds on a sunset. | k0 cohesion; k1 the falcon's hunger; k2 screen; k3 inks. Click: k0 scatter, k1 the falcon stoops, k2 chunky. |
| **Koi** | pf 0614-2 | Carp on linked spines (the head steers, each segment follows at a fixed distance), tapered bodies in orange, white and black patches with fanned tails, under drifting lily pads in a green spot ink. They mouth the surface in rings, and mob food when it's dropped. | k0 swim speed; k2 screen; k3 inks. Click: k1 drop food, k2 chunky. |
| **Shore** | pf Midsummer Sea | A beach from above: swells refracting along the shoreline, breaking white in the shallows, the swash running up the sand with a lacy foam edge and sliding back, leaving wet sand that dries. Sets of bigger waves now and then. | k0 swell; k1 tide; k2 screen; k3 inks. Click: k0 a set of big waves, k2 chunky. |
| **Grove** | pf 0601 | Fractal trees (seven forks deep) growing from saplings and swaying, more at the tips, in silhouette against dusk. The year turns: blossom, green, orange with leaves falling and blowing, bare. Leaves are spot inks. | k0 wind; k1 season; k2 screen; k3 inks. Click: k0 a gust, k1 grow a new grove, k2 chunky. |
| **Cumulus** | pf 0517 | Clouds of drifting fractal noise across a low sun, each shaded by the cloud lying sunward of it (silver linings near the sun, dark undersides), with crepuscular rays smeared outward from the sun through the gaps. | k0 wind; k1 cloud cover; k2 screen; k3 inks. Click: k0 time-lapse, k1 move the sun, k2 chunky. |
| **Radar** | pf 0614 | A phosphor radar scope: the sweep paints what it passes (a speckled coastline, drifting rain cells, aircraft that move between sweeps), and the phosphor fades over the turn. Range rings and bearing ticks on the glass. | k0 sweep speed; k1 range; k2 screen; k3 inks. Click: k0 new traffic, k1 rain, k2 chunky. |
| **Zen** | pf 0619 | A raked sand garden: grooves run straight and bend into rings around three rocks, lit by a low sun, in a sand palette whose inks sit close so the ridges are a fine grain. A rake re-rakes it top to bottom at a new angle; petals drift down in a spot ink. | k0 rake speed; k1 groove spacing; k2 screen; k3 inks. Click: k0 rake now, k1 move the stones, k2 chunky. |
| **Plankton** | pf 0526 | Six thousand plankton drift dark on a slow current and flare blue where they're disturbed: a hand trails through them (k0 and k1 steer it), splashes ring outward, and the wake swirls away. | k0/k1 steer the hand; k2 screen; k3 inks. Click: k0 splash, k1 a wave over all of it, k2 chunky. |
| **Neon** | pf 0622 | A neon sign on bricks (OPEN, a cocktail bar, a palm and sun, a heart): each colour is its own dithered plate, cores white-hot, glow lighting the wall; tubes hum, and now and then one fails and stutters. | k0 glow; k1 sign; k2 screen; k3 wall inks. Click: k0 a failing tube, k1 lights out, k2 chunky. |
| **Clock** | pf 0515-4 | The real local time on an engraved dial (bars, dots or minimal), hands as tapered blades with drop shadows, and a red spot-ink second hand that ticks with a quartz overshoot, or sweeps. With music it ticks on the beat. | k0 face; k1 tick or sweep; k2 screen; k3 inks. Click: k1 tick on the beat, k2 chunky. |
| **Strange** | pf Lissajous Weave | A Clifford attractor drawn as the glowing density of 30 000 points, coloured by which way each point jumped. A form change fades out, jumps, and fades in, because gliding between forms passes through dull periodic orbits. | k0–k3 bend its a, b, c, d. Click: k0 next form, k1 colours, k2 freeze the drift, k3 long glow. |

Left alone, each moves on by itself: a new form, shape or scene every 14–40 s. The menu's
*audio knobs* switch (k2 on this shelf) works for them too. With it on, the music's mid,
level, bass and treble envelopes add to what the knobs set (the same four upstream's audio
edition reads). Each beat pulses them, each 8-bar phrase brings the next form, shape, picture,
world or scene (a gust in Smoke, lightning at Sea), in Bit Tunnel each bar steps the bit mask,
in Smoke each kick puffs, in Caustics a kick drops a pebble, in Tesla it touches the glass, in Life a
generation passes on every beat, Fireworks launch on the kicks, and Gears tick like an escapement.

Their shared parts are `pfd/ink.py` (threshold screens: Bayer, blue noise by void filling,
interleaved gradient noise, halftone dots, engraving lines and pixel-exact cross-hatching,
whose line sets come in one at a time as the tone rises; and the ink palettes) and
`pfd/demos/original.py` (the shelf, the audio envelopes and the bar and phrase events; and
`Inked`, which gives a pattern the k2 screen and k3 inks knobs, the chunky toggle and
`print(tone)`).

#### In full colour

Eighteen more, closer to Patternflow's own look: bold procedural colour, no dither. They share
`Chromatic` (in `pfd/demos/original.py`), whose k3 slides the palette's hues as it turns and
changes palette when clicked. The palettes are `pfd/hues.py`'s cosine gradients
(colour = a + b cos 2π(ct + d), per channel), tuned to stay bright all the way round.

| Demo | After | What it is | Knobs (turn; click) |
|---|---|---|---|
| **Truchet** | pf 0514 | Quarter-circle arc tiles whose arcs join into endless paths: shaded ribbons carrying a rainbow that flows across the grid, over a two-colour maze that stays continuous across tiles. Tiles spin a quarter turn now and then, rerouting the paths; waves of spins come on each bar with music. | k0 tile size; k1 spin rate; k2 ribbon width; k3 colour. Click: k0 a wave of spins, k1 hold still, k2 fills, k3 next palette. |
| **Isobands** | pf 0531 | A flowing domain-warped field cut into bands of flat colour, each shaded like a terrace from its low edge up, with contour lines between. | k0 bands; k1 warp; k2 flow speed; k3 colour. Click: k0 contour lines, k1 hold still, k2 terraces, k3 next palette. |
| **Stained Glass** | pf 0601 | Voronoi panes of coloured glass in lead lines, the seeds drifting so panes grow and trade neighbours, lit from behind by a wandering sun through rippled glass. | k0 panes; k1 drift; k2 lead width; k3 colour. Click: k0 a new window, k1 hold still, k3 next palette. |
| **Chroma Waves** | pf Retro Digital Tapestry | A ripple tank in colour: two to seven drifting sources each send out rings in their own colour, and where they cross, the colours add into a shimmering moiré. | k0 wavelength; k1 drift; k2 sources; k3 colour. Click: k0 sharp rings or soft waves, k1 hold still, k3 next palette. |
| **Guilloche** | pf Poincaré Sphere | Banknote rosettes: rings of lobed curves, K of them each, crossing into woven bands, three colours turning against each other. Each pixel finds which curves pass through it (an arcsine), so it's one pass per ring. | k0 lobes; k1 lines; k2 amplitude; k3 colour. Click: k0 next rosette, k1 hold still, k3 next palette. |
| **Weave** | pf 0511 | Cloth off the loom: warp and weft in mirrored stripe setts make a plaid, woven plain, twill, basket or satin, threads shaded round and dipping at crossings; it scrolls and ripples. | k0 thread size; k1 weave; k2 ripple; k3 colour. Click: k1 a new plaid, k2 hold still, k3 next palette. |
| **Quasicrystal** | pf 0515-4 | n plane waves at evenly spaced angles summed: four tile like a carpet, five or seven never repeat (a quasicrystal, with a Penrose tiling's order). Their phases slide, so the rosettes breathe and reform; flowing bands or flat steps. | k0 scale; k1 symmetry (3–13); k2 phase speed; k3 colour. Click: k0 bands or steps, k1 hold still, k3 next palette. |
| **Cyclic** | pf TileWaves | Griffeath's cyclic cellular automaton: each cell steps to the next of N colours when a neighbour already has it, and noise organizes into rainbow spirals winding out for ever. It warms up before it shows, and reseeds if it freezes. | k0 speed; k1 colours; k2 neighbourhood; k3 colour. Click: k0 reseed, k1 big cells, k2 drop a seed, k3 next palette. |
| **Wallpaper** | pf 0619 | A flowing colour field folded through five of the seventeen wallpaper groups (p4m, p6m, p4, pmm, p3), so whatever it does repeats with that symmetry everywhere: kaleidoscope squares, snowflakes, pinwheels, panels, triskeles. | k0 tile size; k1 group; k2 field speed; k3 colour. Click: k1 hold still, k3 next palette. |
| **Droste** | pf Chromatic Vortex | Spiral bands zooming in for ever: in log-polar coordinates a zoom is a slide and a spiral is a sloping line. A second family crossing the other way makes Escher's checker of curved tiles. | k0 zoom speed (and reverse); k1 arms; k2 twist; k3 colour. Click: k0 stop, k1 checker, k3 next palette. |
| **Hex Pulse** | pf 0528 | A bevelled honeycomb, each tile one colour read from a wave field at its centre (wandering rings, crossing planes or a spiral), so waves sweep across tile by tile. Clicks, and kicks with music, drop ripples. | k0 tile size; k1 wave speed; k2 wave kind; k3 colour. Click: k0 gaps, k1 drop a ripple, k3 next palette. |
| **Ribbons** | pf Wave Saw | Saturated stripes in a run of palette colours, bent by travelling waves (after Bridget Riley's colour stripes), running up, across, or round in lobed rings. | k0 stripe width; k1 wave height; k2 wave length; k3 colour. Click: k1 up, across or rings, k2 hold still, k3 next palette. |
| **Moiré** | pf 0515 | Two or three gratings of thin lines (or rings, or dots), each in its own colour, turning together but a few degrees apart, so broad fringes in none of the layers sweep across, and colours add where lines coincide. | k0 pitch; k1 turn speed; k2 pattern; k3 colour. Click: k0 thick lines, k1 a third layer, k3 next palette. |
| **Copper** | pf 0511 | Amiga copper bars, each a bright-centred gradient, rolling on staggered sine paths (front ones drawn over back ones) over a dim plasma, with a rainbow sine scroller sending greetings. | k0 bars; k1 bounce speed; k2 scroll speed; k3 colour. Click: k0 plasma, k2 scroller, k3 next palette. |
| **Streams** | pf Vector Field Flow | Eighteen hundred particles riding a curl-noise flow, each leaving a trail on a fading canvas in its colour (by birthplace, or by heading), so the flow is drawn as silky combed strands. | k0 speed; k1 swirl size; k2 trail length; k3 colour. Click: k0 a new flow, k1 colour by heading or birthplace, k3 next palette. |
| **Girih** | pf 0514 | Star tilings with white strapwork and inner rosettes that morph from one star to the next: {n/k} stars of 8, 16, 4, 6, 12 and 10 points, on a square or hexagonal lattice to suit. Each pixel is folded into one mirrored wedge, where the star is a single edge, so k (sharpness) turns smoothly from polygon to spike and a change of star blends the outlines (or dissolves, when the lattice changes). Left alone it moves on every 12 s. | k0 tile size; k1 star (morphs); k2 sharpness; k3 colour. Click: k0 strap width, k1 auto morph, k2 inner rosettes, k3 next palette. |
| **Marbling** | pf 0520 | Paper marbling, exactly (Jaffer and Lu): each ink drop spreads and pushes the older ink out into rings, keeping its area; combs drag it all into feathered chevrons. The tray keeps its recent drops and strokes (older ones are baked into a stored picture, so nothing pops), each pixel is traced back through them at four sample points for smooth edges, and new drops swell into place. | k0 drop size; k1 drop rate; k2 comb spacing; k3 colour. Click: k0 fresh tray, k1 a big drop, k2 comb it, k3 next palette. |
| **Dial** | pf 0614 | Eight rings of coloured segments turning each their own way, like a combination lock; now and then (click k0, or each phrase) every ring eases round until its seams line up, and it flashes open. | k0 speed; k1 segments; k2 rings; k3 colour. Click: k0 open the lock, k3 next palette. |

## Community patterns

[community.patternflow.work](https://community.patternflow.work) is upstream's pattern wall.
Every pattern there is JavaScript, and most also carry a **firmware header**: the author's
own, or a port someone else verified on hardware. Those headers run here natively, the way
SeungHun's presets do, one small shared library each:

```sh
./upstream_host/community.py sync     # the public wall: headers, titles, authors, likes; upstream main's cores
./upstream_host/community.py check    # each under AddressSanitizer, through a scripted player (13 s on ash)
./upstream_host/community.py build    # compile what's new (run.py does this itself, 6 s on ash for all)
./upstream_host/community.py sheet /tmp/cs   # contact sheets of the check's frames
./run.py --only community
```

Re-run `sync` and `check` to pick up new patterns, then `../pi-controller/update_pi.py` to
send them to the box. It compiles only what's new or changed, over ssh, before the restart.
All 211 from scratch take 79 s on the Pi 5.

How it differs from the presets:
- **Upstream main's cores.** The community builds against upstream's current firmware, not our
  pinned clone (newer `PFMath` helpers, for one). `sync` fetches the portable cores (math, colour,
  noise, tables, mem, params) at main's current commit. The pattern-facing API (`InputFrame`,
  `PFCanvas`) is the same, so the same shim serves both.
- **One library per pattern** (`build/community/lib/<id>-<size>-<hash>.so`). Namespaces collide
  between authors, a header that doesn't compile costs only itself, and a new header compiles
  alone. The libraries use hidden visibility and `-fno-gnu-unique`. Without that, the dynamic
  linker would merge every library's `PFCanvas::buffer` (an inline variable) into one.
- **Mechanical fixups only:** `"../src/..."` includes, a namespace with a space in its name,
  and `pf_module.h` (upstream's module SDK header, stood in for by `upstream_host/community_shim/`).
  With those, all 211 build.
- **Each at its own canvas, centred.** A header that calls `PFCanvas::setFrame` (all of them
  portrait, 64 × 128) stands in the middle of the square, pillarboxed. The rest were written for
  upstream's 128 × 64 and are letterboxed. Nothing is stretched or turned.
- **Vetted before it runs.** Anyone can post to the wall, including C++ ports of other people's
  patterns, and a pattern runs as native code in the demo process. So every built library is
  inspected before anything of it runs, on ash or on the Pi (`vet` in `community.py`):
  - Its dynamic imports must all be maths, memory, strings or the C++ runtime's plumbing
    (`ALLOWED`), so nothing that opens a file or a socket or starts a process gets through,
    however the source spells it.
  - Its disassembly must have no system-call instruction of its own.
  All 211 pass. A source scan (2026-10-27) found nothing reaching beyond drawing in them, or in
  the 77 JS-only patterns either.
- **The check.** A pattern runs inside the demo process, so `check` runs each one under
  AddressSanitizer for 11 s of scripted input: idle, the knobs out to their extremes and back,
  fast spins, clicks, push-and-turn and the audio edition. A pattern it fails is left off the
  shelf. All 211 pass at their own canvas. (One, *Day and Night dreamy beach*, overflows a
  global at 128 × 128, which is a reason not to fill the square.) The verdicts are keyed by each
  header's hash, so a header that changed since is trusted until the next check.
- **Menu blurb:** author, porter if any, and knob labels. Shelf order is most liked first.

Not yet: the 77 patterns that are JavaScript only. Running those needs upstream's JS harness
under node.

**Licence:** the patterns are CC BY-SA 4.0, their authors'. They're fetched into the gitignored
`upstream_host/build/` and never committed here.

## Speed

Measured per frame on ash:
- Most of our demos take 0.4–1.1 ms (render, gamma, cap). Rotor, Echo, Rocket, Vault and
  Mandala take under 1 ms; Droplet, Terrain and Glitch about 1 ms; **Kaleido 3.1 ms**; and
  Pool 1.4 ms (it was 8.3 ms before drawing a diagonal of pillars at a time).
- **Reaction takes 4.3 ms** at 10 iterations a frame.
- The upstream presets take **0.1–0.6 ms** natively, and the community's a median of
  **0.15 ms** (none over 1 ms). On the Pi 5 the community's take a median of 0.51 ms, and the
  slowest, Rose Mushroom, takes 3.2 ms.
- The Patternflow originals, fastest first: Life 0.3 ms, Op Art 0.3 ms, Fireworks 0.4 ms,
  Streams 0.4 ms, Aurora 0.5 ms, Cyclic 0.5 ms, Moiré 0.5 ms, Snow 0.5 ms, Warp 0.5 ms, Lava
  0.6 ms, Orrery 0.6 ms, Quasicrystal 0.6 ms, Ribbons 0.6 ms, Spiro 0.6 ms, Bit Tunnel 0.7 ms,
  Droste 0.7 ms, Isobands 0.7 ms, Chroma Waves 0.8 ms, Grove 0.8 ms, Jellyfish 0.8 ms, Flock
  0.9 ms, Wallpaper 0.9 ms, Guilloche 1.0 ms, Gears 1.1 ms, Pendulums 1.1 ms, Plankton 1.1 ms,
  Hex Pulse 1.2 ms, Radar 1.2 ms, Tesla 1.2 ms, Zen 1.5 ms, Clock 1.6 ms, Galaxy 1.6 ms, Smoke
  1.6 ms, Window 1.7 ms, Copper 1.8 ms, Dial 1.8 ms, Moon 1.9 ms, Riso 1.9 ms, Pixel Sort 2.0
  ms, Caustics 2.1 ms, Weave 2.1 ms, Neon 2.2 ms, Strange 2.2 ms, Shore 2.3 ms, Truchet 2.3 ms,
  Cumulus 2.4 ms, Koi 2.5 ms, Valley 2.7 ms, Bonfire 2.8 ms, Girih 2.8 ms, Sea 2.9 ms, Stained
  Glass 3.7 ms and Marbling 4.1 ms. **Helix takes 5.7 ms** (a hundred-odd sphere impostors),
  **Obra 2.6–5.3 ms** depending on the form (octahedron fastest, metaballs slowest), and
  **Mandel averages 8 ms**, rising with depth as more points take hundreds of iterations.

The Pi 5 has 16.7 ms a frame at 60 fps and is a few times slower per core, so it should fit
everything. If Reaction doesn't, turn its k2 (speed) down. Obra watches its own time: if
its render averages over 12 ms, it marches at half resolution (one ray per 2 × 2 block, about
half the cost). The dither and outline stay at full resolution, so it looks nearly the same.
It logs when it does this. Mandel does the same past 14 ms, and goes back to full resolution
once a frame would be cheap again, so on ash only the deepest seconds of a dive (into a
mini-Mandelbrot, whose inside burns every iteration) drop to half.

## Bench network

Since 2026-10-23 the card is on the home LAN, through a gigabit switch port, since the 5A-75B
won't link at 100 Mbit. Ash renders and sends UDP straight to it over its own wired port, with
no Wi-Fi in the loop:
- **The card keeps its built-in 192.168.75.39.** Ash's NetworkManager connection `wired` carries
  an extra address, 192.168.75.2/24, beside its DHCP one, so the card's subnet is on the same wire.
  Remove it with `nmcli con modify wired -ipv4.addresses 192.168.75.2/24`.
- **`--out auto` (the default)** checks at start whether the card answers ARP on one of ash's own
  links. If it does, frames go over UDP; if not, they fall back to `pipe:durian`.

**The durian pipe**, still there as the fallback:
- `pipe:durian` sends `pfd/r75_pipe.py`'s source over ssh and streams frames to it. Durian
  forwards them as UDP from its USB NIC `enx000000000000`, through NetworkManager profile
  `colorlight` (static 192.168.75.1/24, no default route).
- `pipe:` keeps only the newest frame, so a Wi-Fi stall drops frames rather than building lag.
- Durian's Wi-Fi power saving is off in its Wi-Fi profile (2026-10-23). With it on, the link
  spiked to 100-270 ms.
- Durian also stays awake on AC power (2026-10-23):
  - The GDM greeter's `sleep-inactive-ac-type='nothing'` is in `/etc/gdm3/greeter.dconf-defaults`.
    The original is kept as `.orig-2026-10-23`.
  - jof's GNOME session has the same setting.
  - `HandleLidSwitchExternalPower=ignore` is in `/etc/systemd/logind.conf.d/50-patternflood-ac-awake.conf`.

## Adding a demo

Subclass `pfd.runtime.Demo` in `pfd/demos/`, and add it to `ALL` in `pfd/demos/__init__.py`.
For the Patternflow shelf, subclass `Original` (`pfd/demos/original.py`) instead, and add it to
`ORIGINALS` with the preset it should follow.
The interface is in `pfd/runtime.py`'s docstring. `render()` returns float RGB in perceptual
units; the runtime applies gamma, brightness and the current cap. Check it with a preview
before it goes near the panels:

```sh
./run.py --demo NAME --knobs "script:0.5:k0+12,1.5:k1 click,2:k3 down,3:k3 up" --out preview:/tmp/x.gif
```
