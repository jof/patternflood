# Hardware revisions

Each revision is frozen twice: a git tag on the repo, and a named version in the
Onshape document (`8cfb8d4f799392c05f62f6ad`). Fork from either. The Onshape
main workspace always holds the revision in progress.

To get a revision's cut files back: `git checkout rev-1 -- hardware/laser`.

## Rev 1 — as built (2026-10-20)

Git tag **`rev-1`** (c1b00f8). Onshape version **"Rev 1 - as built"**
(`ab89ff622434de960ad866e2`).

One-sheet bezel, single-sheet walls, PSU 5 mm off the bottom wall on spacers,
three 12 × 24" sheets. Built and working.

**Found in the build:** it is a bit flimsy to the touch, and pushing a knob
visibly deforms the box. The PSU hangs on two screws through one 3 mm wall and
floats.

## Rev 2 — stiffened (in progress)

| Change | Variable | Why |
|---|---|---|
| Bezel back to two sheets, the inner one **glued** behind the outer | `#frontLayers` 2 | The knobs push on it. Still pocketed 35 mm square at each knob, so the encoder clamps only the outer sheet |
| A **glued** doubler inside every wall | `#wallLayers` 2 (new) | Rev 1 flexed. Glued, wall + doubler bend as one 6.4 mm section, ~8× a single sheet |
| PSU in the corner: on the bottom doubler, against the bezel | `#psuStandoff` 0, `#psuZFront` −6.36 | Rev 1 floated on spacers off a single wall |
| ~~Pi and USB adapter 3.5 mm right~~ | — | superseded by the Pi 5 below |
| **Raspberry Pi 5** replaces the Pi Zero 2 W + USB gigabit adapter | `#piX` −108, `#piY` 0, `#piScrewDia` 2.55, `#piNutAF` 5 (new); `#nic*` deleted | Gigabit Ethernet on board; headroom for JS patterns. It stands on end at the tray's left, Ethernet jack pointing down past the tray edge, so the patch cable has room |
| **Vents**: intake through the **bottom** wall + doubler (3 mm slots running front to back, between the knob ribs and right of the PSU); exhaust **high on both side walls** + doublers, between the tray's top edge and the top doubler. The back cover is plain — the box sometimes stands against a wall | `#ventSlotW` 3, `#ventPitch` 6 (new) | The box is closed with a 50 W PSU, a Pi 5 and the card inside; it breathes like a chimney, in low and out high. **Stand it on feet ≥ 8 mm**, on the solid strips along the bottom's front and back edges, clear of the slots |
| **Etched art** on the outer faces: a generated circuit-board pattern (traces, chips, vias; a dial ring with ticks round each knob) | `art.py`, `decals.py` (new) | Cosmetic. Etched before cutting, from `sheets/sheet-N.svg` (cut red, score blue, engrave black); the DXFs stay cut-only. **Visible in Onshape** as decals on the outer faces: the shell imports art.py's PNGs and lays each on its part's outer face, framed by an `Art origin` mate connector, so it shows where the laser will put it |
| Rail clearance 10 → 11.64 | `#psuRailClear` | Keeps the box depth at 60.72 now the PSU sits 1.64 further forward, so nothing behind it moves |
| Stiffener web carried forward to the bezel over the knobs: the **stiffener shelf** | — | Rev 1's knob band was supported on three sides; its top edge, the bottom of the display aperture, was free, and the top knob row is 25 mm from it. The shelf props that edge |
| Two **knob ribs**, bottom doubler to shelf, at x −95 (between the knob columns) and −50 (between the knobs and the PSU) | — | Each knob sits in a ~45 × 86 mm cell supported on all four sides |

**The doublers.** Each runs from the bezel's rear face (its front edge butts
the inner bezel, so a push on the face goes straight into the walls) back to
0.5 mm short of rail C, so the rail stacks, the back cover and the box depth are
unchanged. The side doublers span the full inside height; the top and bottom ones
fit between them. Brace and stiffener mortises, the PSU holes and the IEC
cutout go through wall and doubler alike. The stiffener's mortise reaches past
the side doublers' rear edge, so there it is an open notch, not a slot.

**The shelf and ribs.** The shelf is the old stiffener web extended forward to
the inner bezel, over the knob cluster only (x −140 to −44), so the PSU's
wiring still runs up past it on the right. It keeps the web's tenons through
the side walls, which locate it; its front edge butts the inner bezel. Each rib
has two hidden tabs into slots cut in the **inner** bezel only (blind against
the outer sheet, so nothing shows); its top and bottom edges are glued to the
shelf and the bottom doubler. Rib 1 has a cable hole per knob row for the
STEMMA chain; the shelf has one over the right knob column for the lead from
the Pi. On the cut sheets the ribs are nested inside the inner bezel's display
aperture — cut inner shapes first.

**Unchanged:** box outside, depth, braces, rails, back cover, panels, Colorlight.
The tray is 6.36 narrower (279.3).

### Hardware changes from rev 1

| Joint | Rev 1 | Rev 2 |
|---|---|---|
| PSU, through the bottom wall | 2 × M3 × 12 + 5 mm spacers | **2 × M3 × 10 + washers, no spacers** (6.36 of wood; M3 × 12 would pass the PSU's 5 mm limit) |
| IEC flange, front screw (through wall + doubler) | M3 × 12 | **M3 × 16** + washer + nut |
| IEC flange, rear screw (wall only, behind the doubler) | M3 × 12 | M3 × 12 + washer + nut |
| Glue | finger joints, rail stacks | **plus** inner bezel and four doublers — PVA, clamped flat |
| Pi mounting | 4 × M3 x 8 through drilled-out Zero holes | **4 × M2.5 x 8 + 4 M2.5 nuts** (Pi 5 holes are 2.7 mm) |
| Pi power and network | micro-USB lead, OTG adapter, USB gigabit adapter, zip ties | **5 V → USB-C pigtail**; a ~20 cm flat Cat6 patch cable; Active Cooler |

### Gluing order

1. **Inner bezel to outer**, face down, aperture edges flush (both are 257 mm
   square; a panel dropped in squares them up). Clamp flat between boards.
2. **Each doubler to its wall.** Side doublers: push a brace and the stiffener
   through the wall and doubler mortises dry, to register them, and keep the
   doubler's front edge 6.36 mm back from the wall's front edge (a two-sheet
   offcut is the gauge). Bottom doubler: line up its PSU holes with the wall's
   using two M3 screws. Top doubler: centred, same 6.36 setback. Keep glue out
   of the mortises and holes.
3. **Box glue-up, bezel face down:** glue the knob ribs into their slots in
   the inner bezel first, standing up. Then the walls, the shelf (glue its front
   edge and where the ribs' top edges meet it), braces and rails, exactly as rev
   1. Glue the ribs' bottom edges to the bottom doubler as that wall goes on.

### Still to check before cutting

- The IEC's front screw hole leaves 2.4 mm of doubler to its front edge
  (glued, so it should be fine).
- The Pi 5's ports and Active Cooler are envelopes from the drawing: check
  them against the real board (the stacked USB is the tallest, 3.2 mm short of
  the back cover). Test piece 8 is now a Pi 5 template with three M2.5 nut
  pockets to settle `#piNutAF`.
- Power budget: the Pi 5 takes ~1 A more than the Zero did, so the panels'
  share drops to ~1.4 A each (`driver-colorlight.md` §4).
