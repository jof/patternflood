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

## Rev 2 — stiffened, Pi 5, vents, etched art (2026-10-21)

Git tag **`rev-2`**. No Onshape version: the workspace had moved on to Rev 2.2
before one was made. To see Rev 2 in Onshape, check out `rev-2` and push it to a
branch workspace. Designed, not yet built.

| Change | Variable | Why |
|---|---|---|
| Bezel back to two sheets, the inner one **glued** behind the outer | `#frontLayers` 2 | The knobs push on it. Still pocketed 35 mm square at each knob, so the encoder clamps only the outer sheet |
| A **glued** doubler inside every wall | `#wallLayers` 2 (new) | Rev 1 flexed. Glued, wall + doubler bend as one 6.4 mm section, ~8× a single sheet |
| PSU in the corner: on the bottom doubler, against the bezel | `#psuStandoff` 0, `#psuZFront` −6.36 | Rev 1 floated on spacers off a single wall |
| ~~Pi and USB adapter 3.5 mm right~~ | — | superseded by the Pi 5 below |
| **Raspberry Pi 5** replaces the Pi Zero 2 W + USB gigabit adapter | `#piX` −108, `#piY` 0, `#piScrewDia` 2.55, `#piNutAF` 5 (new); `#nic*` deleted | Gigabit Ethernet on board; headroom for JS patterns. It stands on end at the tray's left, Ethernet jack pointing down past the tray edge, so the patch cable has room |
| **Vents**: intake through the **bottom** wall + doubler (3 mm slots running front to back, between the knob ribs and right of the PSU); exhaust **high on both side walls** + doublers, between the tray's top edge and the top doubler. The back cover is plain — the box sometimes stands against a wall | `#ventSlotW` 3, `#ventPitch` 6 (new) | The box is closed with a 50 W PSU, a Pi 5 and the card inside; it breathes like a chimney, in low and out high. **Stand it on feet ≥ 8 mm**, on the solid strips along the bottom's front and back edges, clear of the slots |
| **Etched art** on the outer faces: a dense generated circuit board on a 1.27 mm grid — QFP/BGA/SOIC chips with fan-out, passives, headers, crystals, test points, fiducials, spiral inductors, Hilbert meanders, serpentines, wide power traces, buses, silkscreen designators, hatch/contour/stipple pours; hidden: a real, scannable QR code on every etched part (each with its own message), a space invader, a Lissajous figure, tiny words in empty spaces. Each knob gets an unlabelled dial (270° of fine ticks and a dotted gauge arc). All of it one **Score** process, dots as concentric circles | `art.py`, `decals.py` (new) | Cosmetic. Etched before cutting, from `sheets/sheet-N.svg` (cut red, score blue, engrave black); the DXFs stay cut-only. **Visible in Onshape** as decals on the outer faces: the shell imports art.py's PNGs and lays each on its part's outer face, framed by an `Art origin` mate connector, so it shows where the laser will put it |
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

## Rev 2.1 — knob light slits (2026-10-21, after the `rev-2` tag)

Each Adafruit 4991 carries a NeoPixel on its encoder side, shining at the back of
the outer bezel sheet (the inner sheet is pocketed there). A ring of **36 fine
radial slits** round each knob, through the outer sheet only, lets it through:
0.7 mm wide, r 13–16.5 mm — just outside a 1" knob's skirt, inside the 35 mm
pocket. A full ring, so it works wherever the LED sits on the board and however
the board is turned; it glows brightest on the LED's side. ~1.6 mm of wood
between slits at the inner end. The etched dial moved outside it (rings at
r 18.6/19.4, ticks to r 22). Constants `KNOB_SLITS`, `KNOB_SLIT_R0/R1/W` in
`enclosure.fs`.

**Renamed Patternflood (2026-10-22).** The back cover's etched title block and QR
code now read "PATTERNFLOOD / DESKTOP / REV 2.1", and the "PATTERNFLOW" easter
egg became "PATTERNFLOOD". `art.py` was re-run, then `nest_sheets.py`. Only the
back-cover art and sheet 2's SVG/PNG changed; the other parts regenerate
byte-identical, and every QR still decodes. The back-cover decal is part of the
`decals.py` step below.

**Model sync: done 2026-10-25 with Rev 2.2, below.** At first the model
change was in `enclosure.fs` but not pushed, and `bezel-outer.dxf` was patched to
match it by a one-off script mirroring the FeatureScript exactly. To sync:

    python3 hardware/cad/tools/push.py          # the slits into the model
    python3 hardware/cad/tools/export_dxf.py    # must reproduce bezel-outer.dxf: check git diff
    python3 hardware/cad/tools/decals.py        # the new dial art onto the bezel decal

then tag `rev-2.1` and make the Onshape version.


## Rev 2.2 — push buttons, credits (2026-10-25)

Git tag **`rev-2.2`**. Onshape version **"Rev 2.2 final"**
(`b6f738065d04b263138e2a9b`), made from the main workspace once it matched the
tag's `enclosure.fs` exactly. Includes Rev 2.1 (the knob light slits), which got
no tag or version of its own, and the two changes below it: the etch font, and
the buttons moved to the top wall with a second shelf passthrough. Designed,
not yet built.

An earlier Onshape version, **"Rev 2.2"** (`ce56787b0137070520ec6a19`), predates
both of those: it has the buttons on the left wall, 4 left vents and the old
plate lettering. Use "Rev 2.2 final".

**Three push buttons**, a vertical row high on the **left wall**: 12 mm
waterproof momentaries, the VanMoof S3 boost button (Amazon B07F24Y1TB has the
drawing): head Ø17.5, 8.1 proud; 9.9 of thread and body behind the panel, then
3.6 of solder lugs. The thread has two flats 11 mm apart that key it.

| | |
|---|---|
| Where | y 130.1 / 106.1 / 82.1 (box frame; 24 mm pitch, 6.5 mm between heads), z −32.6: midway between the upper brace's back and the doubler's rear end. Inside, the nearest thing is the top-left panel's HUB75 plug ~40 mm in; the Pi's GPIO header is just below |
| Wall | a **keyed hole**: Ø12.2 with flats 11.2 apart (0.2 clearance on each, kerf-compensated), flats top and bottom |
| Doubler | **cut away** behind the row: a notch out of its rear top corner (from 11 mm below the lowest button to the top, and from its rear edge to 11 mm in front of the buttons). The thread is only ~6.4 mm, the same as wall + doubler, so each nut clamps the outer wall alone, like the encoders |
| Vents | the left wall's exhaust moves down under the buttons: **4 slots** (was 14), between the notch and the middle brace's mortise, just above the Pi. The right wall keeps its 14 |
| Model | constants `BTN_*` in `enclosure.fs`; a mate connector per button on the wall's outer face |

Check before cutting: the key's fit (0.2 clearance) on a test hole, and that
the nut turns in the notch.

**Etched art.** The back cover gets a framed **credits plate**: "MADE BY JOF /
JOF@THEJOF.COM / INSPIRED BY PATTERNFLOW / BY SEUNGHUN LEE / PATTERNFLOW.WORK"
beside a real QR code to `https://patternflow.work/` (it decodes from the drawn
score lines). The title block reads REV 2.2. Each button gets a double halo
ring just outside its head. `artfont.py` gained `@`. `art.py` now snaps arc
ends onto line ends when it finds holes (odd-angle arcs like the keyed holes
were left open by the DXF's rounding). The bezel, right and top walls
regenerate byte-identical.

**Model sync — done (2026-10-25).** `push.py`: the studio
compiles, all features OK. `export_dxf.py` then reproduces every DXF: 24 byte
for byte, and the three that had been patched by script (`bezel-outer` from
Rev 2.1, `wall-left` and its doubler) geometrically identical (same entities,
cut length and regions); the exported files are now the ones in the repo.
`decals.py` re-uploaded all five art images; every decal attaches. 

### Etch font (2026-10-25)

`artfont.py` now sets text in two faces, by size:

- **Under 1.3 mm** (the silkscreen designators, chip names, hidden words): the
  original 4 × 6-grid single-stroke font, unchanged, one beam pass per stroke.
  Ideal that small, where any filled face breaks up.
- **1.3 mm and up** (the title block and the credits plate, now in mixed
  case): **JetBrains Mono Medium** (SIL OFL), filled solid. Each glyph outline
  is filled with score lines 0.12 mm apart, like the QR codes, plus one pass
  round its edge, inset half a beam so the burn lands on the drawn outline.
  Fills follow the nonzero rule, as TrueType does (the variable font's 8 is
  two self-intersecting contours).

The font file is in `hardware/cad/tools/fonts/` with its licence. To try
another face (Berkeley Mono, if bought), point `artfont.FONT` at its file.
Designators now keep off the title block and credits plate. Only the back
cover's art changed; the bezel's and walls' are byte-identical to `rev-2.2`, and
so are the cut paths. Art re-run, sheets re-nested, decals re-uploaded: checks
clean, every QR decodes, every decal attaches.

### Buttons to the top wall; a wire passthrough per knob column (2026-10-25)

- **The push buttons move to the top wall**, a row along x at its left end
  (seen from the front, the knob side): x −128.1 / −104.1 / −80.1, still
  24 mm apart and at z −32.6, between the upper brace's back and rail C. Same
  keyed hole, flats now front and back, through the top wall; the **top
  doubler** is notched out of its rear left corner instead (from its left end
  to 11 mm past the last button, and from its rear edge to 11 mm in front of
  the row). Under them is open bay over the top-left panel's back.
- **The left wall is as it was before the buttons**: 14 exhaust slots, a plain
  doubler. Both DXFs and the left wall's art are byte-identical to `8fcdaa5`
  again.
- **The stiffener shelf has a 20 × 9 mm wire passthrough over each knob
  column**, not just the right one, so either column's wiring can run up past
  it.

Pushed and exported: only the shelf, top wall,
top doubler and the left wall + doubler changed. Art re-run (the top wall's
three buttons get halo rings), sheets re-nested, decals re-uploaded: checks
clean, every QR decodes, every decal attaches.

## Rev 2.3 — back cover doubler, French cleat holes (2026-10-25)

Git tag **`rev-2.3`**. Onshape version **"Rev 2.3"**
(`f1e44685512a7a748a065ae3`), made from the main workspace once it matched the
tag's `enclosure.fs` exactly. Designed, not yet built.

- **The back cover is two sheets.** A doubler is glued to its inside face, in
  the band between the two rail stacks and flush with rail A: 285.6 × 309.6,
  z −57.5 to −54.4, 0.5 mm clear of the walls and of rail A's edges. The rails,
  the cover screws and their lengths are unchanged; the doubler drops in
  between the rail A strips as the cover goes on, and lifts away with it.
- **Relief windows in the doubler** over the Pi 5's port block and cooler and
  over the Colorlight's RJ45 and 5 V terminal (each part's footprint grown
  2 mm, so overlapping windows merge). They had only 3.2–5.3 mm to the cover,
  and the Pi's stacked USB would have touched the doubler. Two more over what
  gets plugged in from the back: the Colorlight's **5 V power header** (merged
  with the terminal's window; 8.5 mm from its top to the cover, for the mated
  plug and its wires) and its **JTAG header**, new in the model: J27 J31 J32
  J30, the 1 × 4 row by the FPGA (`CL_JTAG`, off the back scan ±0.5 mm), as a
  straight 2.54 header 8.5 mm tall. Through its window the cover is 19.1 mm
  off the board, which takes a row of jumper housings (~16.5 mm) but not
  wires leaving them straight up: leave the Glasgow plugged in only with the
  leads bent flat, or fit a right-angle header. Every body inside is ≥ 2 mm
  from the doubler (checked with `evDistance`).
- **Six French cleat holes**, Ø5.2 through cover and doubler (`CLEAT_*` in
  `enclosure.fs`): four at y +105.3 (x ±40, ±120) for the cleat strip, two at
  y −181.3 (x ±80) for a spacer strip of the same thickness, each row 43.2 mm
  from its edge of the box. For #10 / 5 mm pan-head wood screws driven from
  inside, heads on the doubler; a 1" screw gives ~18 mm of bite in a 19 mm
  strip. Keep both strips 25 mm clear of the box's top and bottom edges (the
  cover's screw heads). A screw-head volume (Ø11 × 7 mm) behind each hole is
  clear of everything. Until a cleat goes on they are just holes.
- **Art:** each cleat hole is drawn as a plated mounting hole (annular ring,
  eight stitching vias, ground traces leaving in line with them). More
  variety in the meander family: besides Hilbert meanders and square spiral
  inductors there are now Moore, Peano and Minkowski-island curves, meandered
  inverted-F antennas with their ground bar and feed, meandered dipoles,
  strain-gauge serpentines, and octagonal, round and bifilar (transformer)
  spirals. Title block and back-cover QR say REV 2.3. Every part's art
  re-rolled; checks clean, every QR decodes, every decal attaches.
- **Paper knob diffusers** (`hardware/laser/diffusers/`, `diffusers.py`, new):
  a 34.5 mm square per knob (`#knobPocket` less 0.25 a side) with a Ø7.3 hole
  (`#boreDia` + 0.3) for the bushing. It lies in the inner bezel's pocket
  against the outer sheet, clamped by the encoder's face, and spreads each
  NeoPixel through the whole ring of light slits. 8 on one small sheet (4 +
  4 spares).
- **Five cut sheets**: the doubler has sheet 5 to itself.

## Rev 2.4 — for cutting (2026-10-25)

Git tag **`rev-2.4`**. Onshape version **"Rev 2.4 - for cutting"** (VERSION_ID),
made from the main workspace once it matched the tag's `enclosure.fs` exactly.
Rev 2.3 plus the PSU screw-head recesses below. This is the one to cut.

**Before cutting it:** cut [`laser/test-cuts/since-rev-1/`](laser/test-cuts/since-rev-1/README.md)
(`test_cuts_delta.py`, one 300 × 114 mm sheet). The full test set was last cut
on 2026-10-18 and Rev 1 was built on it, so that sheet covers only what has
changed since: the two-sheet knob stack with its light slits and dial (real
bezel geometry), the Pi 5 template and M2.5 rings, the push-button keys, the
PSU strip and its head-recess strip, a gauge for the new holes, and an etch
sampler (the back cover's credits plate and QR code) to set the Score process
on. Its README lists every change since rev 1 and what covers it.

### PSU screw heads recessed

- The bottom wall (the outer sheet) is cut **Ø7.5** round each of the PSU's two
  screws (`PSU_HEAD_RECESS`; 7.35 as cut), and the head clamps on the bottom
  doubler's hole, **no washer**. The screws on hand have heads 5.5 round and
  3.2 tall: flush with the 3.18 sheet (0.02 proud until it beds in), so the
  box sits flat on a table.
- **`#psuHoleDia` 4.45 → 4.1** (drawn 3.95), half way to an M3 clearance: the
  head now bears on ~0.8 mm of doubler round the hole instead of ~0.6, and
  there is still ±0.48 of slack for the PSU's ±1 mm hole tolerance (was ±0.65).
  The recess clears the head even with the screw hard over. **Re-cut test
  piece 10** and try it on the PSU before cutting the box; the hole gauge's
  row 4 now sweeps 3.75–4.35 round it.
- **Screws: 2 × M3 × 8, no washers** (were M3 × 10 + washers): 3.18 of doubler,
  leaving ~4.8 mm of thread, inside the PSU's 5 mm limit.
- Tighten gently all the same: the PSU sits on the doubler and the screws only
  locate it.
- Only `wall-bottom.dxf` changed (and sheet 3); the nearest other cut is
  ~13 mm from a recess.
- Standing it flat closes the **intake vents** in the bottom wall: fine for a
  while, but for long runs at brightness keep it on feet ≥ 8 mm as before.
