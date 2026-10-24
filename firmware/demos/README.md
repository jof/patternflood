# Demos

Interactive demos for the 2×2 (128 × 128), written once and run in either place:

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
Pillow; without it the demos run without text. It imports `r75_frame`, `seesaw`
and `knob_renderer` from `../colorlight`.

## Menu

**Hold the two outer knobs (k0 and k3) for a second.** In the menu:
- **k0** steps through the demos (anticlockwise = next, which felt right on the bench). They switch live behind the overlay and keep their state.
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

Cross-cutting questions, worth noting on every demo:

1. **Acceleration curve.** 1× to about 6 detents/s, then up to 6×. Too twitchy? Too slow?
2. **The menu chord.** Is holding two knobs discoverable, and does it ever fire by accident (e.g. two Squash players clicking at once)?
3. **Knob lights.** Are they read at a glance, or ignored? If they're ignored, they may be worth less than the NeoPixel power and the light-slit work in the enclosure.
4. **Attract mode.** `--knobs auto` plays the demos by itself. Does an idle box running it draw people in?

## Speed

Measured per frame on ash (render, gamma, cap). Most demos take 0.4–1.1 ms. **Reaction
takes 4.3 ms** at 10 iterations a frame. The Pi 5 has 16.7 ms a frame at 60 fps and is a few
times slower per core, so it should fit everything. If Reaction doesn't, turn k2 down.

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
