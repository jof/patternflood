FeatureScript 3070;
import(path : "onshape/std/geometry.fs", version : "3070.0");

// Mean Well's own LRS-50-5 model: the Part Studio the vendor STEP was imported
// into, in this document. The PSU proxy merges it in (Detailed on), so the
// enclosure studio shows the real part rather than an envelope. Re-pin the
// version if that studio ever changes.
LRS50::import(path : "e474d54d0ff1822f6f0a417d", version : "2366f6cc2b6f7f82cd8dca33");

/**
 * Patternflow desktop enclosure — parametric features.
 *
 * Laser-cut 3 mm finger-joint box, a 2 x 2 array of Waveshare P2 64x64 GOB
 * panels driven by a Colorlight 5A-75B receiver card and a Raspberry Pi Zero 2 W,
 * 4 x Adafruit 4991 seesaw encoders.
 *
 * DATUM CONVENTION — every part depends on this:
 *   z = 0          the LED panel FRONT face
 *   z < 0          into the enclosure (panels, electronics, back cover)
 *   z > 0          out of the enclosure (the bezel laminations)
 *   x = 0, y = 0   centre of the display area
 *
 * The bezel sits flush on the panel face: GOB panels are resin-filled and
 * already diffuse, so there is no air gap and no separate diffuser.
 *
 * Drive every parameter from the Variables studio. Placeholders that MUST be
 * measured before cutting: #thickness, #kerf. (#panelDepth was measured on the
 * P2 64x64-B, 2026-10-03.) The EC11 bushing
 * thread length caps #frontThickness — measure it first.
 *
 * Source of truth for this file is the repo, not the Onshape document:
 *   hardware/cad/featurescript/enclosure.fs
 */

// ────────────────────────────────────────────────────────────────────────
// Part naming
// ────────────────────────────────────────────────────────────────────────
// A body created by fCuboid has no name, and Onshape will happily call it
// "Part 12". That is invisible until a DXF export or a BOM needs to say
// WHICH part, so every body that survives to the end gets named here.

function nameBody(context is Context, id is Id, bodyId is Id, name is string)
{
    setProperty(context, {
            "entities"     : qCreatedBy(bodyId, EntityType.BODY),
            "propertyType" : PropertyType.NAME,
            "value"        : name });
}

// ────────────────────────────────────────────────────────────────────────
// Board data
// ────────────────────────────────────────────────────────────────────────
// Fixed properties of the bought boards, in each board's own frame:
// component side up, origin at the board's lower-left corner, mm. They are
// constants rather than variables because they are facts about a part, not
// design choices; where a board sits in the box is a variable.
//
// Colorlight 5A-75B, MEASURED 2026-10-12 off 600 dpi flatbed scans of both
// faces (outline and holes from the back scan, which lay flat; component
// outlines from the component-side scan, registered to it through the holes).
// RJ45 edge at +y.

const CL_W = 91.76;     // across (x)
const CL_H = 143.67;    // along (y), RJ45 edge at the top
const CL_PCB_HOLE = 4.23;
const CL_HOLES = [[5.11, 139.08], [86.51, 139.35], [16.07, 3.81], [76.44, 3.96]];
// Eight 2x8 shrouded HUB75 headers (J1..J8), centre and long-axis angle from
// +x. They are genuinely angled on this board, +/-25 deg off vertical, and
// mirrored left to right. Centres are the through-hole pad clusters.
const CL_HUBS = [[11.72, 98.59, 65], [12.11, 71.88, 65], [11.84, 44.53, 65], [11.80, 16.95, 65],
                 [80.28, 98.72, 115], [80.30, 71.53, 115], [80.39, 44.26, 115], [80.39, 17.15, 115]];
const CL_HUB_L = 33.0;  // standard 16-way 2.54 box header
const CL_HUB_W = 8.9;
// [x0, y0, x1, y1] outlines, component-side scan (+/-1 mm)
const CL_RJ45 = [29.5, 117.0, 63.5, 147.2];   // dual ganged jack, overhangs the top edge
const CL_TERM = [66.0, 130.0, 86.5, 144.0];   // 2-way barrier terminal, 5 V in
const CL_JST_SMALL = [2.5, 110.0, 9.0, 124.5];    // white 4-pin, signal
const CL_JST_BIG   = [83.5, 113.0, 91.5, 128.0];  // 4-pin power header, GND GND D5V D5V

// Raspberry Pi Zero 2 W, from the official mechanical drawing
// (datasheets.raspberrypi.com, rpizero2 mechanical drawing). The connector
// edge is y = 0.
const PI_W = 65;
const PI_H = 30;
const PI_HOLES = [[3.5, 3.5], [61.5, 3.5], [3.5, 26.5], [61.5, 26.5]];
const PI_HOLE = 2.75;
// [cx, width, depth into board, overhang past y = 0, height]
const PI_EDGE_PARTS = [[12.4, 11.2, 7.5, 0.5, 3.2],     // mini HDMI
                       [41.4, 8.0, 5.6, 1.0, 2.6],      // micro USB, OTG (data)
                       [54.0, 8.0, 5.6, 1.0, 2.6]];     // micro USB, power
// [x0, y0, x1, y1, height] — low parts, from the same drawing
const PI_TOP_PARTS = [[19.0, 8.0, 34.0, 23.0, 1.4],      // RP3A0 SiP
                      [37.3, 9.7, 48.9, 21.2, 1.2],      // second package
                      [1.5, 9.0, 12.6, 21.0, 1.4],       // microSD
                      [60.5, 7.0, 65.0, 23.0, 1.3]];     // camera FPC

// Where the boards sit. All of them mount on the ELECTRONICS TRAY, a plate
// that screws to the back of the (doubled) middle panel brace, component side
// facing BACK — so the back cover lifts away with nothing attached to it,
// everything is in reach once it is off, and the tray comes out as one unit
// when a panel needs to.
//
//   Colorlight: long axis horizontal, RJ45 end toward -x (the Pi side).
//     Its frame (x_b across, y_b along, z_b out of the component side) maps
//     to box -y, -x, -z:  box = (clX + CL_H/2 - y_b,  clY + CL_W/2 - x_b).
//   Pi Zero 2 W: long axis horizontal, connector edge DOWN.
//     Its frame (x_p along, y_p across, z_p out) maps to box -x, +y, -z:
//     box = (piX + PI_W/2 - x_p,  piY - PI_H/2 + y_p).
function clToBox(clX, clY, xb is number, yb is number) returns Vector
{
    return vector(clX + (CL_H / 2 - yb) * millimeter, clY + (CL_W / 2 - xb) * millimeter);
}

function piToBox(piX, piY, xp is number, yp is number) returns Vector
{
    return vector(piX + (PI_W / 2 - xp) * millimeter, piY + (yp - PI_H / 2) * millimeter);
}

// ────────────────────────────────────────────────────────────────────────
// Panel proxy
// ────────────────────────────────────────────────────────────────────────
// Two levels of fidelity, switched by "Detailed":
//
//   OFF  a plain 128 x 128 x 14.5 envelope. What the enclosure actually
//        needs, and what every clearance check in the doc was written
//        against. Leave it off when checking geometry.
//   ON   the stack a GOB panel really is, so renders and interference
//        checks read honestly:
//
//        z=0     ┬──────────────────────────────┬  emissive area, its own
//        -0.3    ┼──┤ 0.5mm reveal all round ├──┼  body so a render can
//                │      GOB resin module        │  make it a light source
//        -3.0    ┼──────────────────────────────┼
//                │            PCB               │  driver ICs on the back
//        -4.6    ┼──┬────────────────────────┬──┼
//                │  │  cavity: connectors,   │  │  rear frame, a ring
//                │  │  posts, ICs            │  │
//        -14.5   ┴──┴────────────────────────┴──┴
//
// Behind the PCB, only the inserts and registration pins are MEASURED (on
// the P2 64x64-B, 2026-10-03), and they are the only rear features the
// enclosure touches. Everything else back there — frame ring, ICs, HUB75
// shrouds, power header — is REPRESENTATIVE. These panels have no published
// drawing and no consistency between batches (enclosure-lasercut.md §11), so
// a different batch means re-measuring the inserts and pins, not trusting
// this.

annotation { "Feature Type Name" : "Panel proxy" }
export const panelProxy = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Panel width" }
        isLength(definition.panelW, LENGTH_BOUNDS);

        annotation { "Name" : "Panel height" }
        isLength(definition.panelH, LENGTH_BOUNDS);

        annotation { "Name" : "Panel depth" }
        isLength(definition.panelDepth, LENGTH_BOUNDS);

        annotation { "Name" : "Panel columns" }
        isInteger(definition.cols, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Panel rows" }
        isInteger(definition.rows, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Panel body (undersize)" }
        isLength(definition.panelBody, LENGTH_BOUNDS);

        annotation { "Name" : "Detailed" }
        definition.detail is boolean;

        annotation { "Name" : "GOB module thickness" }
        isLength(definition.gobT, LENGTH_BOUNDS);

        annotation { "Name" : "PCB thickness" }
        isLength(definition.pcbT, LENGTH_BOUNDS);

        annotation { "Name" : "Rear frame rail width" }
        isLength(definition.frameW, LENGTH_BOUNDS);

        annotation { "Name" : "HUB75 shroud x from panel centre (both, +/-)" }
        isLength(definition.hubX, LENGTH_BOUNDS);

        annotation { "Name" : "HUB75 shroud y from panel centre" }
        isLength(definition.hubY, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "HUB75 shroud width (x)" }
        isLength(definition.hubW, LENGTH_BOUNDS);

        annotation { "Name" : "HUB75 shroud length (y)" }
        isLength(definition.hubL, LENGTH_BOUNDS);

        annotation { "Name" : "HUB75 shroud height above PCB" }
        isLength(definition.hubH, LENGTH_BOUNDS);

        annotation { "Name" : "5 V header x from panel centre" }
        isLength(definition.pwrX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "5 V header y from panel centre" }
        isLength(definition.pwrY, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "5 V header width (x)" }
        isLength(definition.pwrW, LENGTH_BOUNDS);

        annotation { "Name" : "5 V header length (y)" }
        isLength(definition.pwrL, LENGTH_BOUNDS);

        annotation { "Name" : "5 V header height above PCB" }
        isLength(definition.pwrH, LENGTH_BOUNDS);

        annotation { "Name" : "Mounting post diameter" }
        isLength(definition.postDia, LENGTH_BOUNDS);

        annotation { "Name" : "Post x from panel centre" }
        isLength(definition.postXOffset, LENGTH_BOUNDS);

        annotation { "Name" : "Post y from panel centre" }
        isLength(definition.postYOffset, LENGTH_BOUNDS);

        annotation { "Name" : "Mid-edge post y from panel centre" }
        isLength(definition.midPostYOffset, LENGTH_BOUNDS);

        annotation { "Name" : "Registration pin x from panel centre" }
        isLength(definition.pinXOffset, LENGTH_BOUNDS);

        annotation { "Name" : "Registration pin y from panel centre" }
        isLength(definition.pinYOffset, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Registration pin diameter" }
        isLength(definition.pinDia, LENGTH_BOUNDS);

        annotation { "Name" : "Registration pin projection" }
        isLength(definition.pinProj, LENGTH_BOUNDS);
    }
    {
        // panelW/panelH are the TILING PITCH; panelBody is the physical part,
        // which is smaller. The difference is the inter-panel gap, and that
        // gap is REQUIRED, not slop: each panel carries a half-gap border
        // between its edge pixel centre and its edge, so
        //     border + gap + border = one pixel pitch
        // keeps the pixel grid continuous across the seam. Butting the bodies
        // tight would put a whole gap's worth of error in the grid at every
        // seam. Measured on a Waveshare P3 64x64: body 190, pitch 192, gap 2,
        // and 189mm of pixel span — which is exactly 0.5mm of border per edge.
        const nc = definition.cols;
        const nr = definition.rows;
        const n  = nc * nr;
        const B = definition.panelBody;
        const D = definition.panelDepth;
        const gap = definition.panelW - B;

        // border + gap + border = one pixel pitch. On the P3 that was
        // 0.5 + 2 + 0.5; on the P2 the body IS the pitch, so the gap is zero
        // and the border is a full half-pitch, 1 + 0 + 1.
        const reveal = 0.3 * millimeter;
        const border = (definition.panelW / 64 - gap) / 2;
        const zPcbF  = 0 * millimeter - definition.gobT;
        const zPcbB  = zPcbF - definition.pcbT;

        // Panels are numbered in reading order, top-left first. Centres sit on
        // the tiling pitch, so the bodies are separated by exactly the gap.
        for (var i = 0; i < n; i += 1)
        {
            const col = i % nc;
            const row = floor(i / nc);
            const xc  = (col - (nc - 1) / 2) * definition.panelW;
            const yc  = ((nr - 1) / 2 - row) * definition.panelH;
            const x0  = xc - B / 2;
            const x1  = xc + B / 2;
            const y0  = yc - B / 2;
            const y1  = yc + B / 2;
            const pid = id + ("p" ~ i);

            if (!definition.detail)
            {
                fCuboid(context, pid + "box", {
                        "corner1" : vector(x0, y0, -D),
                        "corner2" : vector(x1, y1, 0 * millimeter) });
                continue;
            }

            // GOB resin module, and the lit area as a SEPARATE body so a
            // render can give it an emissive appearance. The reveal around
            // it is the border the pixel arithmetic above derives — it is
            // the real edge of the pixel field.
            fCuboid(context, pid + "face", {
                    "corner1" : vector(x0, y0, zPcbF),
                    "corner2" : vector(x1, y1, -reveal) });
            fCuboid(context, pid + "lit", {
                    "corner1" : vector(x0 + border, y0 + border, -reveal),
                    "corner2" : vector(x1 - border, y1 - border, 0 * millimeter) });

            fCuboid(context, pid + "pcb", {
                    "corner1" : vector(x0, y0, zPcbB),
                    "corner2" : vector(x1, y1, zPcbF) });

            // Rear frame: a ring, open in the middle where everything lives.
            fCuboid(context, pid + "frame", {
                    "corner1" : vector(x0, y0, -D),
                    "corner2" : vector(x1, y1, zPcbB) });
            fCuboid(context, pid + "cav", {
                    "corner1" : vector(x0 + definition.frameW,
                                       y0 + definition.frameW, -D - 1 * millimeter),
                    "corner2" : vector(x1 - definition.frameW,
                                       y1 - definition.frameW, zPcbB + 1 * millimeter) });
            opBoolean(context, pid + "frCut", {
                    "tools"         : qCreatedBy(pid + "cav", EntityType.BODY),
                    "targets"       : qCreatedBy(pid + "frame", EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION });

            // Threaded inserts, six of them, MEASURED on the P2 64x64-B: two
            // down each side at (+/-postX, +/-postY) — the ones the braces
            // screw into, so they are driven from the same variables the
            // braces are — and one mid-way along the top and bottom edges at
            // (0, +/-midPostY), which nothing uses yet.
            var inserts = [];
            for (var sx = -1; sx <= 1; sx += 2)
            {
                for (var sy = -1; sy <= 1; sy += 2)
                {
                    inserts = append(inserts, [sx * definition.postXOffset,
                                               sy * definition.postYOffset]);
                }
            }
            inserts = append(inserts, [0 * millimeter,  definition.midPostYOffset]);
            inserts = append(inserts, [0 * millimeter, -definition.midPostYOffset]);
            for (var ki = 0; ki < size(inserts); ki += 1)
            {
                const k  = "" ~ ki;
                const px = xc + inserts[ki][0];
                const py = yc + inserts[ki][1];
                fCylinder(context, pid + ("post" ~ k), {
                        "topCenter"    : vector(px, py, zPcbB),
                        "bottomCenter" : vector(px, py, -D),
                        "radius"       : definition.postDia / 2 });
                fCylinder(context, pid + ("bore" ~ k), {
                        "topCenter"    : vector(px, py, zPcbB - 6 * millimeter),
                        "bottomCenter" : vector(px, py, -D - 1 * millimeter),
                        "radius"       : 1.5 * millimeter });
                opBoolean(context, pid + ("boreCut" ~ k), {
                        "tools"         : qCreatedBy(pid + ("bore" ~ k), EntityType.BODY),
                        "targets"       : qCreatedBy(pid + ("post" ~ k), EntityType.BODY),
                        "operationType" : BooleanOperationType.SUBTRACTION });
            }

            var tag = "Panel";
            if (n > 1) { tag = "Panel " ~ (i + 1); }

            // Registration pins: two, near the TOP edge (the panel's own +y),
            // standing proud of the rear frame. They are why the upper brace
            // is as wide as it is — it carries the holes that locate them.
            for (var sx = -1; sx <= 1; sx += 2)
            {
                const k = "" ~ (sx + 1);
                fCylinder(context, pid + ("pin" ~ k), {
                        "topCenter"    : vector(xc + sx * definition.pinXOffset,
                                                yc + definition.pinYOffset, -D),
                        "bottomCenter" : vector(xc + sx * definition.pinXOffset,
                                                yc + definition.pinYOffset, -D - definition.pinProj),
                        "radius"       : definition.pinDia / 2 });
                nameBody(context, pid + ("npin" ~ k), pid + ("pin" ~ k), tag ~ " — registration pin");
            }

            // The connectors, MEASURED 2026-10-12 off the rule-calibrated
            // flatbed scan (positions only — heights are calipers, not yet
            // taken). HUB75 IN and OUT are two VERTICAL 2x8 shrouded headers,
            // symmetric about the centre; the 5 V input is a 4-way 3.96 mm
            // (VH-style) header just left of centre as seen from the front.
            // (The driver ICs that were drawn here were representative and
            // now sat inside the real shrouds, so they are gone.)
            for (var h = 0; h < 2; h += 1)
            {
                const hx = xc + (2 * h - 1) * definition.hubX;
                fCuboid(context, pid + ("hdr" ~ h), {
                        "corner1" : vector(hx - definition.hubW / 2,
                                           yc + definition.hubY - definition.hubL / 2,
                                           zPcbB - definition.hubH),
                        "corner2" : vector(hx + definition.hubW / 2,
                                           yc + definition.hubY + definition.hubL / 2, zPcbB) });
            }

            fCuboid(context, pid + "pwr", {
                    "corner1" : vector(xc + definition.pwrX - definition.pwrW / 2,
                                       yc + definition.pwrY - definition.pwrL / 2,
                                       zPcbB - definition.pwrH),
                    "corner2" : vector(xc + definition.pwrX + definition.pwrW / 2,
                                       yc + definition.pwrY + definition.pwrL / 2, zPcbB) });

            // Named for the same reason the enclosure parts are: an assembly
            // instance list and a BOM both need to say WHICH body.
            nameBody(context, pid + "na", pid + "face",  tag ~ " — GOB module");
            nameBody(context, pid + "nb", pid + "lit",   tag ~ " — lit area");
            nameBody(context, pid + "nc", pid + "pcb",   tag ~ " — PCB");
            nameBody(context, pid + "nd", pid + "frame", tag ~ " — rear frame");
            nameBody(context, pid + "ne", pid + "pwr",   tag ~ " — 5 V header");
            // IN is on the LEFT seen from behind, i.e. at +x seen from the
            // front (confirmed on the panels, 2026-10-12).
            nameBody(context, pid + "nh0", pid + "hdr0", tag ~ " — HUB75 OUT");
            nameBody(context, pid + "nh1", pid + "hdr1", tag ~ " — HUB75 IN");
        }
    });

// ────────────────────────────────────────────────────────────────────────
// PSU proxy
// ────────────────────────────────────────────────────────────────────────
// Mean Well LRS-50-5 — 99 x 82 x 30 mm, 210 g, 5V 10A.
//
// Detailed ON (the default): Mean Well's own model, merged in from its Part
// Studio and placed by the same STEP -> box mapping the assembly uses. Detailed
// OFF: the measured envelope (99.24 long) with its threaded side holes, for
// clearance work where 31 vendor bodies are noise.
//
// It hangs from the divider shelf's underside on its own side-face M3 holes,
// inside the mains compartment. Laid with its 82mm dimension along y, which
// is why that compartment exists at all: 82mm fits no clear band in the bay
// behind the panels, because the panel connector keep-outs occupy the middle
// of it.
//
// (The Voltaic V50 bank proxy this replaces is in git history — the design
// went mains on 2026-09-08.)

annotation { "Feature Type Name" : "PSU proxy" }
export const psuProxy = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Length (x)" }
        isLength(definition.psuL, LENGTH_BOUNDS);

        annotation { "Name" : "Width (y)" }
        isLength(definition.psuW, LENGTH_BOUNDS);

        annotation { "Name" : "Thickness (z)" }
        isLength(definition.psuT, LENGTH_BOUNDS);

        annotation { "Name" : "Centre x" }
        isLength(definition.psuX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Top face y" }
        isLength(definition.psuYTop, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Front face z" }
        isLength(definition.psuZFront, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Hole A x from terminal end" }
        isLength(definition.psuHoleAX, LENGTH_BOUNDS);

        annotation { "Name" : "Hole B x from terminal end" }
        isLength(definition.psuHoleBX, LENGTH_BOUNDS);

        annotation { "Name" : "Hole height from front face" }
        isLength(definition.psuHoleZ, LENGTH_BOUNDS);

        annotation { "Name" : "Thread nominal diameter" }
        isLength(definition.threadDia, LENGTH_BOUNDS);

        annotation { "Name" : "Max screw penetration" }
        isLength(definition.threadDepth, LENGTH_BOUNDS);

        annotation { "Name" : "Detailed" }
        definition.detail is boolean;

        annotation { "Name" : "Vent slot width" }
        isLength(definition.ventW, LENGTH_BOUNDS);

        annotation { "Name" : "Vent slot pitch" }
        isLength(definition.ventPitch, LENGTH_BOUNDS);

    }
    {
        fCuboid(context, id + "psu", {
                "corner1" : vector(definition.psuX - definition.psuL / 2,
                                   definition.psuYTop - definition.psuW,
                                   definition.psuZFront - definition.psuT),
                "corner2" : vector(definition.psuX + definition.psuL / 2,
                                   definition.psuYTop,
                                   definition.psuZFront) });

        // The threaded M3 side holes, blind into the low-y face — the one
        // that faces the bottom panel. Same datums the shell uses: x from
        // the TERMINAL (high-x) end, height down from the front face. The
        // point of putting them on the proxy is that the screw run is now
        // visible end to end: 3mm of wood, then psuStandoff of air, then
        // these threads. That sets the screw length, and it is the only
        // place the model can show the standoff being spanned rather than
        // bridged by nothing.
        //
        // Nominal Ø3, not a clearance hole — these are threaded, so the
        // proxy shows the thread envelope and the wall carries the 4.5mm
        // clearance. The opposite (high-y) face carries a matching pair;
        // it is not modelled because nothing bolts to it in this build.
        //
        // The depth is the spec sheet's L = 5mm MAXIMUM PENETRATION, not a
        // thread depth to aim for. Modelling it as a blind pocket makes the
        // limit visible: 3mm wood + 5mm standoff + 5mm penetration = 13mm,
        // so M3 x 12 is the longest screw that cannot reach the internals.
        const psuYLo = definition.psuYTop - definition.psuW;
        const psuXHi = definition.psuX + definition.psuL / 2;
        const holeZ = definition.psuZFront - definition.psuHoleZ;
        var tools = [];
        for (var i = 0; i < 2; i += 1)
        {
            var hx = psuXHi - definition.psuHoleAX;
            if (i == 1)
            {
                hx = psuXHi - definition.psuHoleBX;
            }
            fCylinder(context, id + ("th" ~ i), {
                    "topCenter"    : vector(hx, psuYLo + definition.threadDepth, holeZ),
                    "bottomCenter" : vector(hx, psuYLo - 1 * millimeter, holeZ),
                    "radius"       : definition.threadDia / 2 });
            tools = append(tools, qCreatedBy(id + ("th" ~ i), EntityType.BODY));
        }
        opBoolean(context, id + "threadDrill", {
                "tools"         : qUnion(tools),
                "targets"       : qCreatedBy(id + "psu", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });

        if (!definition.detail)
        {
            return;
        }

        // ── Detailed: Mean Well's model replaces the envelope ──────────
        // STEP frame (X from the terminal end, Y from the threaded-hole face,
        // Z up from the base) -> box: x = psuXHi - X, y = psuYLo + Y,
        // z = psuZFront - Z, i.e. a half turn about y, then a translation.
        // The vendor case is 99.00 long against the 99.24 measured, so its
        // far end sits 0.24 inside the envelope; the terminal end is the
        // datum and matches exactly.
        opDeleteBodies(context, id + "dropEnvelope", { "entities" : qCreatedBy(id + "psu", EntityType.BODY) });
        // Everything the merge brings in is collected — Mean Well's model has
        // surface bodies (the capacitors) as well as solids, and moving only
        // the solids left those floating in front of the panels. Its studio's
        // own default planes come across too; they are dropped.
        const before = evaluateQuery(context, qEverything(EntityType.BODY));
        opMergeContexts(context, id + "lrs", { "contextFrom" : LRS50::build() });
        const arrived = qSubtraction(qEverything(EntityType.BODY), qUnion(before));
        // (planes are sheet bodies too, so construction geometry is filtered
        // out explicitly)
        const keep = qConstructionFilter(qUnion([qBodyType(arrived, BodyType.SOLID),
                                                 qBodyType(arrived, BodyType.SHEET)]),
                                         ConstructionObject.NO);
        const extra = qSubtraction(arrived, keep);
        if (!isQueryEmpty(context, extra))
        {
            opDeleteBodies(context, id + "lrsPlanes", { "entities" : extra });
        }
        const merged = evaluateQuery(context, keep);
        opTransform(context, id + "lrsXf", {
                "bodies"    : qUnion(merged),
                "transform" : transform(vector(psuXHi, psuYLo, definition.psuZFront))
                            * rotationAround(line(vector(0, 0, 0) * millimeter, vector(0, 1, 0)), 180 * degree) });
        for (var i = 0; i < size(merged); i += 1)
        {
            const bb = evBox3d(context, { "topology" : merged[i] });
            const ext = bb.maxCorner - bb.minCorner;
            var nm = "LRS-50-5 internal (Mean Well STEP)";
            if (ext[0] > 98 * millimeter && ext[1] > 81 * millimeter)
            {
                nm = "LRS-50-5 case (Mean Well STEP)";
            }
            else if (ext[0] > 80 * millimeter && ext[1] > 79 * millimeter && ext[2] > 25 * millimeter)
            {
                nm = "LRS-50-5 cover (Mean Well STEP)";
            }
            setProperty(context, { "entities" : merged[i], "propertyType" : PropertyType.NAME, "value" : nm });
        }
    });

// ────────────────────────────────────────────────────────────────────────
// IEC inlet proxy
// ────────────────────────────────────────────────────────────────────────
// IEC320 C14 + rocker switch + 5x20mm fuse, all measured 2026-09-09.
//
// The flange is NOT a plain rectangle. It overhangs 6.25mm beyond the
// cutout on the short sides, but on the long sides it is a shallow
// triangular lobe peaking 10.75mm out at the middle and tapering to meet
// the short-side flange — with the screw hole sitting in that lobe.
//
// Modelling it settles the screw-spacing contradiction. The screws are on
// the SHORT axis, not the long one: cutH/2 + tip/2 from centre, so about
// 38mm apart. A 40mm spacing (as the listings claimed) puts the hole
// 6.38mm out of a 10.75mm lobe, which is also plausible — hence the
// derived variable and the note to measure hole centre to hole centre.
//
// It also shows why this module cannot go in a side wall: the flange's
// short extent is cutH + 2*tip = 48.75mm against a 44.5mm deep case. That
// is what drove bayDepth to 60mm, which is now what lets the flange live
// in ANY wall — the 48.75mm short extent fits a 60mm depth with 5.6mm
// each side, whichever wall it goes in.
//
// It sits in the RIGHT (+x) wall, low in the control band. The 2 x 2 box
// stands upright on its bottom wall, so an inlet there would be under the
// case; the right wall is a vertical side, the cord exits horizontally,
// and the inlet lands beside the PSU's terminals, which face +x. (The 2 x 1
// portrait design had it in the bottom wall for the mirror-image reason —
// that box stood on a side wall.)
//
// Placed low: its centre is #iecY, 40mm above the outer bottom face, so
// the flange clears the bottom corner joint and the cutout stays clear of
// the lower rail C mortise (which is 4.6mm away in z, not y). The body
// reaches 37.45mm in from the wall, to x ~111, against the PSU's
// x 54.6 — 56mm clear.

annotation { "Feature Type Name" : "IEC inlet proxy" }
export const iecProxy = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Outer face x" }
        isLength(definition.faceX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Centre y" }
        isLength(definition.cy, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Centre z" }
        isLength(definition.cz, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Cutout long (y)" }
        isLength(definition.cutW, LENGTH_BOUNDS);

        annotation { "Name" : "Cutout short (z)" }
        isLength(definition.cutH, LENGTH_BOUNDS);

        annotation { "Name" : "Body depth" }
        isLength(definition.depth, LENGTH_BOUNDS);

        annotation { "Name" : "Flange end overhang" }
        isLength(definition.flEnd, LENGTH_BOUNDS);

        annotation { "Name" : "Flange lobe tip" }
        isLength(definition.flTip, LENGTH_BOUNDS);

        annotation { "Name" : "Flange thickness" }
        isLength(definition.flThk, LENGTH_BOUNDS);

        annotation { "Name" : "Screw spacing (short axis)" }
        isLength(definition.screwSpacing, LENGTH_BOUNDS);

        annotation { "Name" : "Screw hole diameter" }
        isLength(definition.screwDia, LENGTH_BOUNDS);
    }
    {
        // body, reaching INWARD (-x) from the outer face of the right wall
        fCuboid(context, id + "body", {
                "corner1" : vector(definition.faceX - definition.depth,
                                   definition.cy - definition.cutW / 2,
                                   definition.cz - definition.cutH / 2),
                "corner2" : vector(definition.faceX,
                                   definition.cy + definition.cutW / 2,
                                   definition.cz + definition.cutH / 2) });

        // flange: hexagonal outline, sketched on the wall face
        const hl = definition.cutW / 2 + definition.flEnd;   // half long extent
        const hs = definition.cutH / 2;                      // half short extent
        const tp = hs + definition.flTip;                    // lobe apex

        // Sketch on the wall's OUTER face, normal pointing out of the box
        // (+x). With xDirection = global +y the sketch's own y axis is
        // normal x xDirection = global +z, so u is the long extent (along
        // the wall, y) and v the lobed short one (z).
        var sk = newSketchOnPlane(context, id + "flSk", {
                "sketchPlane" : plane(vector(definition.faceX, definition.cy, definition.cz),
                                      vector(1, 0, 0),
                                      vector(0, 1, 0)) });

        skPolyline(sk, "outline", {
                "points" : [
                    vector(-hl, -hs),
                    vector(0 * meter, -tp),
                    vector( hl, -hs),
                    vector( hl,  hs),
                    vector(0 * meter,  tp),
                    vector(-hl,  hs),
                    vector(-hl, -hs)
                ] });
        skSolve(sk);

        opExtrude(context, id + "flEx", {
                "entities"  : qSketchRegion(id + "flSk"),
                "direction" : vector(1, 0, 0),
                "endBound"  : BoundingType.BLIND,
                "endDepth"  : definition.flThk });

        // Drill the flange too. The wall had these holes but the flange did
        // not, so the model showed screws passing through solid material —
        // which is exactly the sort of thing a proxy is meant to catch.
        var holes = [];
        for (var i = 0; i < 2; i += 1)
        {
            var hz = definition.cz - definition.screwSpacing / 2;
            if (i == 1)
            {
                hz = definition.cz + definition.screwSpacing / 2;
            }
            fCylinder(context, id + ("fh" ~ i), {
                    "topCenter"    : vector(definition.faceX + definition.flThk + 1 * millimeter,
                                            definition.cy, hz),
                    "bottomCenter" : vector(definition.faceX - 1 * millimeter,
                                            definition.cy, hz),
                    "radius"       : definition.screwDia / 2 });
            holes = append(holes, qCreatedBy(id + ("fh" ~ i), EntityType.BODY));
        }
        opBoolean(context, id + "flDrill", {
                "tools"         : qUnion(holes),
                "targets"       : qCreatedBy(id + "flEx", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });

        nameBody(context, id + "nBody", id + "body", "IEC AC-14-F16A body");
        nameBody(context, id + "nFl",   id + "flEx", "IEC AC-14-F16A flange");
    });

// ────────────────────────────────────────────────────────────────────────
// Bay obstructions
// ────────────────────────────────────────────────────────────────────────
// Everything that occupies the bay, so the framing can be checked against
// real parts instead of assumed to fit.
//
// Per panel, one KEEP-OUT per connector — both HUB75 shrouds and the 5 V
// header — at the measured positions, grown by a margin, reaching back from
// the panel's rear face by what a mated plug and the turn of its cable need.
// That replaced a single 70 x 40 block per panel which, it turned out, did
// not even cover the HUB75 shrouds (their outer edges are at x +/-40.7).
//
// Then the driving electronics, on plywood bosses glued to the REAR face of
// the middle panel brace (the bosses are cut in the shell, with the other
// sheet parts), component side facing BACK — the back cover comes off
// clean, with nothing tethered to it:
//   - Colorlight 5A-75B, measured (see Board data), long axis horizontal so
//     its two rows of four HUB75 headers face the top and bottom panel rows;
//   - Raspberry Pi Zero 2 W, from the official drawing, connector edge down;
//   - the USB gigabit adapter, still an envelope (model not chosen yet).
// Heights calipered 2026-10-12, except the Pi PCB (2 mm assumed).

annotation { "Feature Type Name" : "Bay obstructions" }
export const bayObstructions = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Panel width (pitch x)" }
        isLength(definition.panelW, LENGTH_BOUNDS);

        annotation { "Name" : "Panel height (pitch y)" }
        isLength(definition.panelH, LENGTH_BOUNDS);

        annotation { "Name" : "Panel columns" }
        isInteger(definition.panelCols, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Panel rows" }
        isInteger(definition.panelRows, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Panel depth" }
        isLength(definition.panelDepth, LENGTH_BOUNDS);

        annotation { "Name" : "HUB75 shroud x from panel centre (both, +/-)" }
        isLength(definition.hubX, LENGTH_BOUNDS);

        annotation { "Name" : "HUB75 shroud y from panel centre" }
        isLength(definition.hubY, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "HUB75 shroud width (x)" }
        isLength(definition.hubW, LENGTH_BOUNDS);

        annotation { "Name" : "HUB75 shroud length (y)" }
        isLength(definition.hubL, LENGTH_BOUNDS);

        annotation { "Name" : "5 V header x from panel centre" }
        isLength(definition.pwrX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "5 V header y from panel centre" }
        isLength(definition.pwrY, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "5 V header width (x)" }
        isLength(definition.pwrW, LENGTH_BOUNDS);

        annotation { "Name" : "5 V header length (y)" }
        isLength(definition.pwrL, LENGTH_BOUNDS);

        annotation { "Name" : "HUB75 plug + ribbon turn, behind panel back" }
        isLength(definition.plugProj, LENGTH_BOUNDS);

        annotation { "Name" : "5 V plug + wire turn, behind panel back" }
        isLength(definition.pwrPlugProj, LENGTH_BOUNDS);

        annotation { "Name" : "Keep-out margin around connectors" }
        isLength(definition.connMargin, LENGTH_BOUNDS);

        annotation { "Name" : "Board mounting face z (boss tops)" }
        isLength(definition.mountZ, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Middle brace rear face z" }
        isLength(definition.braceRearZ, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Receiver card centre x" }
        isLength(definition.clX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Receiver card centre y" }
        isLength(definition.clY, ANY_LENGTH_BOUNDS);


        annotation { "Name" : "Receiver card PCB thickness" }
        isLength(definition.clPcbT, LENGTH_BOUNDS);

        annotation { "Name" : "Receiver card HUB75 shroud height" }
        isLength(definition.clHubH, LENGTH_BOUNDS);

        annotation { "Name" : "Receiver card RJ45 height" }
        isLength(definition.clRjH, LENGTH_BOUNDS);

        annotation { "Name" : "Receiver card terminal height" }
        isLength(definition.clTermH, LENGTH_BOUNDS);

        annotation { "Name" : "Receiver card big JST height" }
        isLength(definition.clJstBigH, LENGTH_BOUNDS);

        annotation { "Name" : "Receiver card small JST height" }
        isLength(definition.clJstSmallH, LENGTH_BOUNDS);

        annotation { "Name" : "Pi centre x" }
        isLength(definition.piX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Pi centre y" }
        isLength(definition.piY, ANY_LENGTH_BOUNDS);


        annotation { "Name" : "Pi PCB thickness" }
        isLength(definition.piPcbT, LENGTH_BOUNDS);

        annotation { "Name" : "Ethernet adapter width (x)" }
        isLength(definition.nicW, LENGTH_BOUNDS);

        annotation { "Name" : "Ethernet adapter height (y)" }
        isLength(definition.nicH, LENGTH_BOUNDS);

        annotation { "Name" : "Ethernet adapter height off the brace" }
        isLength(definition.nicT, LENGTH_BOUNDS);

        annotation { "Name" : "Ethernet adapter centre x" }
        isLength(definition.nicX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Ethernet adapter centre y" }
        isLength(definition.nicY, ANY_LENGTH_BOUNDS);
    }
    {
        const back = -definition.panelDepth;
        const nc = definition.panelCols;
        const nr = definition.panelRows;
        const m  = definition.connMargin;

        // ── panel connector keep-outs ───────────────────────────────────
        for (var i = 0; i < nc * nr; i += 1)
        {
            const xc = (i % nc - (nc - 1) / 2) * definition.panelW;
            const yc = ((nr - 1) / 2 - floor(i / nc)) * definition.panelH;
            // [cx, cy, w, l, projection, label]
            const conns = [
                [xc - definition.hubX, yc + definition.hubY, definition.hubW, definition.hubL,
                 definition.plugProj, "HUB75 OUT"],
                [xc + definition.hubX, yc + definition.hubY, definition.hubW, definition.hubL,
                 definition.plugProj, "HUB75 IN"],
                [xc + definition.pwrX, yc + definition.pwrY, definition.pwrW, definition.pwrL,
                 definition.pwrPlugProj, "5 V"]
            ];
            for (var k = 0; k < size(conns); k += 1)
            {
                const c = conns[k];
                const kid = id + ("ko" ~ i ~ k);
                fCuboid(context, kid, {
                        "corner1" : vector(c[0] - c[2] / 2 - m, c[1] - c[3] / 2 - m, back - c[4]),
                        "corner2" : vector(c[0] + c[2] / 2 + m, c[1] + c[3] / 2 + m, back + 1 * millimeter) });
                nameBody(context, kid + "n", kid, "Keep-out — panel " ~ (i + 1) ~ " " ~ c[5]);
            }
        }

        // ── Colorlight 5A-75B ───────────────────────────────────────────
        // Hung behind the middle brace, component side facing back: the PCB
        // occupies [mountZ - pcbT, mountZ] and every part grows toward -z.
        const mm = millimeter;
        const clX = definition.clX;
        const clY = definition.clY;
        const cTop = definition.mountZ;                    // solder side, on the bosses
        const cComp = cTop - definition.clPcbT;            // component side

        // a board-frame rectangle -> a box-frame cuboid hanging back from zFace
        const clPart = function(pid is Id, r is array, zFace, h, name is string)
        {
            const a = clToBox(clX, clY, r[0], r[1]);
            const b = clToBox(clX, clY, r[2], r[3]);
            fCuboid(context, pid, {
                    "corner1" : vector(min(a[0], b[0]), min(a[1], b[1]), zFace - h),
                    "corner2" : vector(max(a[0], b[0]), max(a[1], b[1]), zFace) });
            nameBody(context, pid + "n", pid, name);
        };

        clPart(id + "clPcb", [0, 0, CL_W, CL_H], cTop, definition.clPcbT, "Colorlight 5A-75B — PCB");
        var clHoles = [];
        for (var h = 0; h < size(CL_HOLES); h += 1)
        {
            const hp = clToBox(clX, clY, CL_HOLES[h][0], CL_HOLES[h][1]);
            fCylinder(context, id + ("clHole" ~ h), {
                    "topCenter"    : vector(hp[0], hp[1], cTop + 1 * mm),
                    "bottomCenter" : vector(hp[0], hp[1], cComp - 1 * mm),
                    "radius"       : CL_PCB_HOLE / 2 * mm });
            clHoles = append(clHoles, qCreatedBy(id + ("clHole" ~ h), EntityType.BODY));
        }
        opBoolean(context, id + "clDrill", {
                "tools"         : qUnion(clHoles),
                "targets"       : qCreatedBy(id + "clPcb", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });

        for (var j = 0; j < size(CL_HUBS); j += 1)
        {
            const hb = CL_HUBS[j];
            const hc = clToBox(clX, clY, hb[0], hb[1]);
            const ang = atan2(-cos(hb[2] * degree), -sin(hb[2] * degree));   // board axis -> box axis
            const hid = id + ("clHub" ~ j);
            fCuboid(context, hid, {
                    "corner1" : vector(-CL_HUB_L / 2 * mm, -CL_HUB_W / 2 * mm, cComp - definition.clHubH),
                    "corner2" : vector( CL_HUB_L / 2 * mm,  CL_HUB_W / 2 * mm, cComp) });
            opTransform(context, hid + "xf", {
                    "bodies"    : qCreatedBy(hid, EntityType.BODY),
                    "transform" : transform(vector(hc[0], hc[1], 0 * mm))
                                * rotationAround(line(vector(0, 0, 0) * mm, vector(0, 0, 1)), ang) });
            nameBody(context, hid + "n", hid, "Colorlight HUB75 J" ~ (j + 1));
        }
        clPart(id + "clRj",   CL_RJ45,      cComp, definition.clRjH,      "Colorlight RJ45 (dual)");
        clPart(id + "clTerm", CL_TERM,      cComp, definition.clTermH,    "Colorlight 5 V terminal");
        clPart(id + "clJstB", CL_JST_BIG,   cComp, definition.clJstBigH,  "Colorlight 5 V header (big JST)");
        clPart(id + "clJstS", CL_JST_SMALL, cComp, definition.clJstSmallH, "Colorlight JST (small)");

        // ── Raspberry Pi Zero 2 W ───────────────────────────────────────
        const piX = definition.piX;
        const piY = definition.piY;
        const pComp = cTop - definition.piPcbT;
        const piPart = function(pid is Id, r is array, zFace, h, name is string)
        {
            const a = piToBox(piX, piY, r[0], r[1]);
            const b = piToBox(piX, piY, r[2], r[3]);
            fCuboid(context, pid, {
                    "corner1" : vector(min(a[0], b[0]), min(a[1], b[1]), zFace - h),
                    "corner2" : vector(max(a[0], b[0]), max(a[1], b[1]), zFace) });
            nameBody(context, pid + "n", pid, name);
        };

        piPart(id + "piPcb", [0, 0, PI_W, PI_H], cTop, definition.piPcbT, "Raspberry Pi Zero 2 W — PCB");
        var piHoles = [];
        for (var h = 0; h < size(PI_HOLES); h += 1)
        {
            const hp = piToBox(piX, piY, PI_HOLES[h][0], PI_HOLES[h][1]);
            fCylinder(context, id + ("piHole" ~ h), {
                    "topCenter"    : vector(hp[0], hp[1], cTop + 1 * mm),
                    "bottomCenter" : vector(hp[0], hp[1], pComp - 1 * mm),
                    "radius"       : PI_HOLE / 2 * mm });
            piHoles = append(piHoles, qCreatedBy(id + ("piHole" ~ h), EntityType.BODY));
        }
        opBoolean(context, id + "piDrill", {
                "tools"         : qUnion(piHoles),
                "targets"       : qCreatedBy(id + "piPcb", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });

        const edgeNames = ["Pi mini HDMI", "Pi micro USB (OTG)", "Pi micro USB (power)"];
        for (var j = 0; j < size(PI_EDGE_PARTS); j += 1)
        {
            const e = PI_EDGE_PARTS[j];
            piPart(id + ("piEdge" ~ j), [e[0] - e[1] / 2, -e[3], e[0] + e[1] / 2, e[2] - e[3]],
                   pComp, e[4] * mm, edgeNames[j]);
        }
        for (var j = 0; j < size(PI_TOP_PARTS); j += 1)
        {
            const t = PI_TOP_PARTS[j];
            piPart(id + ("piTop" ~ j), [t[0], t[1], t[2], t[3]], pComp, t[4] * mm, "Pi Zero 2 W component");
        }

        // ── USB gigabit adapter (envelope until one is chosen) ──────────
        // Strapped to the same brace, under the Pi.
        fCuboid(context, id + "nic", {
                "corner1" : vector(definition.nicX - definition.nicW / 2,
                                   definition.nicY - definition.nicH / 2, definition.braceRearZ - definition.nicT),
                "corner2" : vector(definition.nicX + definition.nicW / 2,
                                   definition.nicY + definition.nicH / 2, definition.braceRearZ) });
        nameBody(context, id + "nicN", id + "nic", "USB gigabit Ethernet adapter");
    });

// ────────────────────────────────────────────────────────────────────────
// Finger joints
// ────────────────────────────────────────────────────────────────────────
// Two perpendicular plates meeting at an edge overlap in a rectangular
// prism. Slice that prism along the joint and give alternating slices to
// each plate: cut the even slices out of one and the odd slices out of the
// other, and they interlock with no interference anywhere.
//
// KERF. A laser removes material either side of the cut line, so a slot
// comes out `kerf` wider than modelled and a tab `kerf` narrower — 2 x kerf
// of slop, which is why an uncompensated box rattles. Every removed slice
// is therefore shrunk by kerf/2 at each end that is an INTERIOR cut. Ends
// that coincide with the plate's own outer edge are not cuts and get no
// compensation. After cutting, both tabs and slots land on nominal, giving
// a zero-clearance press fit.
//
// Compensation is applied along the finger axis only — the dimension that
// governs the fit. Notch DEPTH is left nominal, so a joint may sit up to
// kerf/2 proud; in basswood that sands flush. Cut a test comb first.

const ANY_LENGTH_BOUNDS = { (millimeter) : [-2000, 0, 2000] } as LengthBoundSpec;
const KERF_BOUNDS       = { (millimeter) : [0, 0.2, 5] } as LengthBoundSpec;

function fingerCount(extent is ValueWithUnits, target is ValueWithUnits) returns number
{
    var n = floor(extent / target);
    if (n < 3)
    {
        n = 3;
    }
    if (n % 2 == 0)
    {
        n += 1;                 // odd, so each plate keeps a tab at both ends
    }
    return n;
}

function cutFingers(context is Context, id is Id, target is Query,
                    ranges is array, axis is number, n is number,
                    phase is number, kerf is ValueWithUnits)
{
    const lo = ranges[axis][0];
    const hi = ranges[axis][1];
    const step = (hi - lo) / n;

    var tools = [];
    var k = 0;

    for (var i = 0; i < n; i += 1)
    {
        if (i % 2 != phase)
        {
            continue;
        }

        var a = lo + i * step;
        var b = lo + (i + 1) * step;

        if (i > 0)      { a = a + kerf / 2; }   // interior cut
        if (i < n - 1)  { b = b - kerf / 2; }   // interior cut

        var r = ranges;
        r[axis] = [a, b];

        fCuboid(context, id + ("f" ~ k), {
                "corner1" : vector(r[0][0], r[1][0], r[2][0]),
                "corner2" : vector(r[0][1], r[1][1], r[2][1])
        });
        tools = append(tools, qCreatedBy(id + ("f" ~ k), EntityType.BODY));
        k += 1;
    }

    if (size(tools) > 0)
    {
        opBoolean(context, id + "b", {
                "tools"         : qUnion(tools),
                "targets"       : target,
                "operationType" : BooleanOperationType.SUBTRACTION
        });
    }
}

// ────────────────────────────────────────────────────────────────────────
// Hex pocket
// ────────────────────────────────────────────────────────────────────────
// A hexagon is the intersection of three slabs at 60 degrees to each other,
// each as wide as the nut's across-flats. Cheaper and more robust than
// sketching a polygon, and it verifies easily: the result must be an
// 8-faced prism.

function hexPrism(context is Context, id is Id, cx is ValueWithUnits, cy is ValueWithUnits,
                  acrossFlats is ValueWithUnits, z0 is ValueWithUnits, z1 is ValueWithUnits) returns Query
{
    const reach = acrossFlats * 1.5;
    var slabs = [];

    for (var i = 0; i < 3; i += 1)
    {
        fCuboid(context, id + ("slab" ~ i), {
                "corner1" : vector(cx - reach, cy - acrossFlats / 2, z0),
                "corner2" : vector(cx + reach, cy + acrossFlats / 2, z1) });

        if (i > 0)
        {
            opTransform(context, id + ("rot" ~ i), {
                    "bodies"    : qCreatedBy(id + ("slab" ~ i), EntityType.BODY),
                    "transform" : rotationAround(line(vector(cx, cy, z0), vector(0, 0, 1)),
                                                 i * 60 * degree) });
        }
        slabs = append(slabs, qCreatedBy(id + ("slab" ~ i), EntityType.BODY));
    }

    opBoolean(context, id + "hex", {
            "tools"         : qUnion(slabs),
            "operationType" : BooleanOperationType.INTERSECTION });

    return qCreatedBy(id, EntityType.BODY);
}

// ────────────────────────────────────────────────────────────────────────
// Enclosure shell  (named enclosureShell — a bare `shell` collides with std)
// ────────────────────────────────────────────────────────────────────────
// Bezel laminations plus the four walls, in ONE feature — the finger joints
// couple them, so splitting them into two features would mean two places
// independently deriving the same finger layout and silently disagreeing.
//
// Construction, front to back:
//
//   z = 0    ┬─────────────────────────────┬  outer lamination: FULL footprint,
//            │  ┌───────────────────────┐  │  finger-jointed to the wall front
//   z = t    ┼──┤ inner lamination(s)   ├──┼  edges. Inner laminations are
//            │  │ INSET by t, drop      │  │  inset by t so they drop inside
//   z = 0    ┤  │ inside the tube       │  ├  the tube and self-locate the
//            │  └───────────────────────┘  │  bezel on the panel face.
//            │        panels, bay          │
//   z =-depth┴─────────────────────────────┴  walls: a tube along z
//
// Three joint families:
//   1. four VERTICAL corners, fingers along z, over the full wall height
//   2. four FRONT edges, outer lamination to wall, fingers along the edge,
//      restricted to between the corners so nothing triple-overlaps
//   3. the corner squares in the outer-lamination band are removed from the
//      horizontal walls, so the bezel owns its own corners
//
// (3) is deterministic because the finger count is forced odd: the last
// finger index is always even, so phase 0 — the vertical walls — always
// gives it up, and the horizontal walls are always the ones still holding
// corner material in that band.

annotation { "Feature Type Name" : "Enclosure shell" }
export const enclosureShell = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Aperture width" }
        isLength(definition.apertureW, LENGTH_BOUNDS);

        annotation { "Name" : "Aperture height" }
        isLength(definition.apertureH, LENGTH_BOUNDS);

        annotation { "Name" : "Side margin" }
        isLength(definition.marginSide, LENGTH_BOUNDS);

        annotation { "Name" : "Top margin" }
        isLength(definition.marginTop, LENGTH_BOUNDS);

        annotation { "Name" : "Control band height" }
        isLength(definition.controlH, LENGTH_BOUNDS);

        annotation { "Name" : "Knob pitch" }
        isLength(definition.knobPitch, LENGTH_BOUNDS);

        annotation { "Name" : "Knob count" }
        isInteger(definition.knobCount, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Bore diameter" }
        isLength(definition.boreDia, LENGTH_BOUNDS);

        annotation { "Name" : "Knob pocket in the inner laminations (square, clears the encoder breakout)" }
        isLength(definition.knobPocket, LENGTH_BOUNDS);

        annotation { "Name" : "Sheet thickness" }
        isLength(definition.thickness, LENGTH_BOUNDS);

        annotation { "Name" : "Bezel laminations" }
        isInteger(definition.layers, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Internal depth" }
        isLength(definition.depth, LENGTH_BOUNDS);

        annotation { "Name" : "Target finger length" }
        isLength(definition.fingerLen, LENGTH_BOUNDS);

        annotation { "Name" : "Kerf" }
        isLength(definition.kerf, KERF_BOUNDS);

        annotation { "Name" : "Panel width (pitch x)" }
        isLength(definition.panelW, LENGTH_BOUNDS);

        annotation { "Name" : "Panel height (pitch y)" }
        isLength(definition.panelH, LENGTH_BOUNDS);

        annotation { "Name" : "Panel columns" }
        isInteger(definition.panelCols, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Panel rows" }
        isInteger(definition.panelRows, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Panel depth" }
        isLength(definition.panelDepth, LENGTH_BOUNDS);

        annotation { "Name" : "Brace y offset" }
        isLength(definition.braceYOffset, LENGTH_BOUNDS);

        annotation { "Name" : "Brace width" }
        isLength(definition.braceW, LENGTH_BOUNDS);

        annotation { "Name" : "Panel post x offset" }
        isLength(definition.postXOffset, LENGTH_BOUNDS);

        annotation { "Name" : "Registration pin x offset" }
        isLength(definition.pinXOffset, LENGTH_BOUNDS);

        annotation { "Name" : "Registration pin y offset" }
        isLength(definition.pinYOffset, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Registration pin hole diameter" }
        isLength(definition.pinHoleDia, LENGTH_BOUNDS);

        annotation { "Name" : "Registration pin hole x travel" }
        isLength(definition.pinSlotLen, LENGTH_BOUNDS);

        annotation { "Name" : "Screw diameter" }
        isLength(definition.screwDia, LENGTH_BOUNDS);

        annotation { "Name" : "Screw slot length" }
        isLength(definition.slotLen, LENGTH_BOUNDS);

        annotation { "Name" : "Screw slot width" }
        isLength(definition.slotW, LENGTH_BOUNDS);

        annotation { "Name" : "Rear rail width" }
        isLength(definition.railW, LENGTH_BOUNDS);

        annotation { "Name" : "Rear rail inset from top/bottom walls" }
        isLength(definition.railInset, LENGTH_BOUNDS);

        annotation { "Name" : "Nut across flats" }
        isLength(definition.nutAcrossFlats, LENGTH_BOUNDS);

        annotation { "Name" : "Screw x span" }
        isLength(definition.screwXSpan, LENGTH_BOUNDS);

        annotation { "Name" : "Screws per rail" }
        isInteger(definition.screwsPerRail, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Back cover clearance" }
        isLength(definition.backClearance, KERF_BOUNDS);

        annotation { "Name" : "Knob cluster centre x" }
        isLength(definition.knobXCentre, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Knob grid columns" }
        isInteger(definition.knobCols, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Knob cluster centre y" }
        isLength(definition.knobYCentre, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "PSU standoff from bottom wall" }
        isLength(definition.psuStandoff, LENGTH_BOUNDS);

        annotation { "Name" : "Stiffening web depth" }
        isLength(definition.webDepth, LENGTH_BOUNDS);

        annotation { "Name" : "PSU length (x)" }
        isLength(definition.psuL, LENGTH_BOUNDS);

        annotation { "Name" : "PSU centre x" }
        isLength(definition.psuX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "PSU front face z" }
        isLength(definition.psuZFront, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "PSU hole A from low-x end" }
        isLength(definition.psuHoleAX, LENGTH_BOUNDS);

        annotation { "Name" : "PSU hole B from low-x end" }
        isLength(definition.psuHoleBX, LENGTH_BOUNDS);

        annotation { "Name" : "PSU hole height from base" }
        isLength(definition.psuHoleZ, LENGTH_BOUNDS);

        annotation { "Name" : "PSU hole clearance dia" }
        isLength(definition.psuHoleDia, LENGTH_BOUNDS);

        annotation { "Name" : "IEC cutout width" }
        isLength(definition.iecCutW, LENGTH_BOUNDS);

        annotation { "Name" : "IEC cutout height" }
        isLength(definition.iecCutH, LENGTH_BOUNDS);

        annotation { "Name" : "IEC screw spacing" }
        isLength(definition.iecScrewSpacing, LENGTH_BOUNDS);

        annotation { "Name" : "IEC screw diameter" }
        isLength(definition.iecScrewDia, LENGTH_BOUNDS);

        annotation { "Name" : "IEC position y (right wall)" }
        isLength(definition.iecY, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "IEC position z" }
        isLength(definition.iecZ, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Pi centre x (back cover)" }
        isLength(definition.piX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Pi centre y (back cover)" }
        isLength(definition.piY, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Receiver card centre x (back cover)" }
        isLength(definition.clX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Receiver card centre y (back cover)" }
        isLength(definition.clY, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Spacer rings, tray to brace (sheets)" }
        isInteger(definition.spacerRings, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Spacer ring outer diameter, tray to brace" }
        isLength(definition.spacerOD, LENGTH_BOUNDS);

        annotation { "Name" : "Spacer rings, board to tray (sheets)" }
        isInteger(definition.boardRings, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Spacer ring outer diameter, board to tray" }
        isLength(definition.boardRingOD, LENGTH_BOUNDS);

        annotation { "Name" : "Tray bottom edge y" }
        isLength(definition.trayY0, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Tray top edge y" }
        isLength(definition.trayY1, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Tray clearance to the side walls" }
        isLength(definition.trayClear, KERF_BOUNDS);

        annotation { "Name" : "Tray screw x, left pair" }
        isLength(definition.trayScrewX1, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Tray screw x, right pair" }
        isLength(definition.trayScrewX2, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Tray screw y (both pairs, +/-)" }
        isLength(definition.trayScrewY, LENGTH_BOUNDS);

        annotation { "Name" : "Adapter centre x" }
        isLength(definition.nicX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Adapter centre y" }
        isLength(definition.nicY, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Adapter width (x)" }
        isLength(definition.nicW, LENGTH_BOUNDS);

        annotation { "Name" : "Adapter height (y)" }
        isLength(definition.nicH, LENGTH_BOUNDS);
    }
    {
        const t    = definition.thickness;
        const nl   = definition.layers;
        const kerf = definition.kerf;
        const over = 1 * millimeter;

        const left   = -(definition.apertureW / 2 + definition.marginSide);
        const right  =   definition.apertureW / 2 + definition.marginSide;
        // The PSU shares the control band rather than having a compartment of
        // its own — the knobs are clustered to one end and the supply takes
        // the other. That is what keeps the box 43mm shorter than a separate
        // compartment below would.
        const bottom = -(definition.apertureH / 2 + definition.controlH);
        const top    =   definition.apertureH / 2 + definition.marginTop;

        // DATUM: z = 0 is the front plane — the bezel's outer face AND the
        // LED surface, coplanar. The bezel therefore hangs BACK from z = 0
        // and the panel passes through its aperture to finish flush.
        const zBack  = -definition.depth;
        const zFront = 0 * meter;               // outer face of the bezel
        const zOut0  = -t;                      // outer lamination band
        const zOut1  = 0 * meter;
        const zBezB  = -nl * t;                 // rearmost bezel lamination

        // ── walls ───────────────────────────────────────────────────────
        // Left/right span the full height, top/bottom the full width; they
        // overlap at the corners, which family (1) then resolves.
        fCuboid(context, id + "wallL", {
                "corner1" : vector(left,      bottom, zBack),
                "corner2" : vector(left + t,  top,    zFront) });
        fCuboid(context, id + "wallR", {
                "corner1" : vector(right - t, bottom, zBack),
                "corner2" : vector(right,     top,    zFront) });
        fCuboid(context, id + "wallB", {
                "corner1" : vector(left,  bottom,     zBack),
                "corner2" : vector(right, bottom + t, zFront) });
        fCuboid(context, id + "wallT", {
                "corner1" : vector(left,  top - t, zBack),
                "corner2" : vector(right, top,     zFront) });

        // ── family 1: vertical corner joints, fingers along z ───────────
        const nz = fingerCount(zFront - zBack, definition.fingerLen);

        const corners = [
            { "vert" : "wallL", "horz" : "wallB", "x" : [left, left + t],   "y" : [bottom, bottom + t] },
            { "vert" : "wallR", "horz" : "wallB", "x" : [right - t, right], "y" : [bottom, bottom + t] },
            { "vert" : "wallL", "horz" : "wallT", "x" : [left, left + t],   "y" : [top - t, top] },
            { "vert" : "wallR", "horz" : "wallT", "x" : [right - t, right], "y" : [top - t, top] }
        ];

        for (var ci = 0; ci < size(corners); ci += 1)
        {
            const c = corners[ci];
            const ranges = [c.x, c.y, [zBack, zFront]];
            cutFingers(context, id + ("cv" ~ ci), qCreatedBy(id + c.vert, EntityType.BODY),
                       ranges, 2, nz, 0, kerf);
            cutFingers(context, id + ("ch" ~ ci), qCreatedBy(id + c.horz, EntityType.BODY),
                       ranges, 2, nz, 1, kerf);
        }

        // ── family 3: hand the bezel its own corners ────────────────────
        // The horizontal walls are the ones still holding corner material in
        // the outer-lamination band (see the note above), so cut it from them.
        for (var ci = 0; ci < size(corners); ci += 1)
        {
            const c = corners[ci];
            fCuboid(context, id + ("csq" ~ ci), {
                    "corner1" : vector(c.x[0], c.y[0], zOut0 - kerf / 2),
                    "corner2" : vector(c.x[1], c.y[1], zOut1 + over) });
            opBoolean(context, id + ("csqCut" ~ ci), {
                    "tools"         : qCreatedBy(id + ("csq" ~ ci), EntityType.BODY),
                    "targets"       : qCreatedBy(id + c.horz, EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION });
        }

        // ── bezel laminations ───────────────────────────────────────────
        // Every lamination but the outermost is inset by t, so it drops
        // inside the tube. The outermost is full footprint and joints to
        // the walls.
        var plates = [];
        for (var i = 0; i < nl; i += 1)
        {
            // Every lamination but the outermost is inset.
            var in0 = t;
            if (i == nl - 1)
            {
                in0 = 0 * meter;
            }

            // i = 0 is the rearmost lamination; i = nl-1 is the outer face.
            fCuboid(context, id + ("layer" ~ i), {
                    "corner1" : vector(left + in0,  bottom + in0, -(nl - i) * t),
                    "corner2" : vector(right - in0, top - in0,    -(nl - i - 1) * t) });
            plates = append(plates, qCreatedBy(id + ("layer" ~ i), EntityType.BODY));
        }
        const outerPlate = qCreatedBy(id + ("layer" ~ (nl - 1)), EntityType.BODY);

        // ── family 2: front-edge joints ─────────────────────────────────
        // Restricted to between the corners so family 1 and family 3 stay
        // untouched.
        //
        // The bezel takes phase 1 and the walls phase 0, and that way round
        // matters: the finger count is forced odd, so phase 1 keeps the
        // fingers at BOTH ends of every edge. Give the bezel phase 0 instead
        // and it drops the first finger of both edges meeting at a corner,
        // which cuts the corner square free as a loose 3 x 3 x 3 fragment.
        const edges = [
            { "wall" : "wallL", "x" : [left, left + t],       "y" : [bottom + t, top - t], "axis" : 1 },
            { "wall" : "wallR", "x" : [right - t, right],     "y" : [bottom + t, top - t], "axis" : 1 },
            { "wall" : "wallB", "x" : [left + t, right - t],  "y" : [bottom, bottom + t],  "axis" : 0 },
            { "wall" : "wallT", "x" : [left + t, right - t],  "y" : [top - t, top],        "axis" : 0 }
        ];

        for (var ei = 0; ei < size(edges); ei += 1)
        {
            const e = edges[ei];
            const ranges = [e.x, e.y, [zOut0, zOut1]];
            const ne = fingerCount(ranges[e.axis][1] - ranges[e.axis][0], definition.fingerLen);

            cutFingers(context, id + ("fe" ~ ei), outerPlate,
                       ranges, e.axis, ne, 1, kerf);
            cutFingers(context, id + ("fw" ~ ei), qCreatedBy(id + e.wall, EntityType.BODY),
                       ranges, e.axis, ne, 0, kerf);
        }

        // ── panel cross-braces ──────────────────────────────────────────
        // The panels hang from these, not from the bezel. Each brace lies
        // flat against the panel backs and carries M3 screws driven from
        // BEHIND, forward into the panels' own rear threaded posts — so the
        // panel weight goes brace -> through-tenon -> wall, and the bezel
        // stays purely cosmetic.
        //
        // The screw holes are OBROUND, running in x, so the panels in a row
        // can be slid together and butted before the screws are tightened.
        //
        // There is a brace for every ROW of inserts: each panel row has its
        // side inserts at rowCentre +/- braceYOffset. In a 2 x 2 the lower
        // brace of the top row and the upper brace of the bottom row meet
        // exactly at y = 0, so braces that touch or overlap are merged into
        // one wider brace instead of being cut as two tenons sharing an
        // edge. With the measured numbers that gives three: [88, 128],
        // [-40, 40] and [-128, -88]. Each row's pins land in a brace with the
        // same 3.5mm of wood beyond the pin hole as the 2 x 1 design had.
        // #postXOffset and #braceYOffset are measured off the P2 64x64-B.
        //
        // Location in y is NOT the screws' job. The panels carry two
        // registration pins near their top edge, and whichever brace covers
        // them gets a hole for each: exact in y, with #pinSlotLen of travel
        // in x. y is the axis the seam shows — a row that jogs by a fraction
        // of a pixel is visible from across the room — and x is the one the
        // butt joint sets anyway.
        //
        // Each brace is a through-tenon: it spans the full box width, so its
        // ends sit inside the walls, and subtracting it from the walls cuts
        // an exactly matching mortise. Kerf goes the opposite way from the
        // finger joints here — the tenon is GROWN by kerf/2 per side and the
        // mortise SHRUNK by kerf/2, so both land on nominal after cutting.

        const zBraceF = -definition.panelDepth;         // against the panel backs
        const zBraceB = zBraceF - t;
        const nCols = definition.panelCols;
        const nRows = definition.panelRows;

        // Candidate spans, top row first and upper before lower within a
        // row, which is already descending in y while braceYOffset is under
        // half a pitch (44 < 64) — so merging only ever looks one back.
        var spans = [];
        for (var r = 0; r < nRows; r += 1)
        {
            const rc = ((nRows - 1) / 2 - r) * definition.panelH;
            spans = append(spans, [rc + definition.braceYOffset - definition.braceW / 2,
                                   rc + definition.braceYOffset + definition.braceW / 2]);
            spans = append(spans, [rc - definition.braceYOffset - definition.braceW / 2,
                                   rc - definition.braceYOffset + definition.braceW / 2]);
        }
        var braceSpans = [];
        for (var k = 0; k < size(spans); k += 1)
        {
            const nb = size(braceSpans);
            if (nb > 0 && spans[k][1] >= braceSpans[nb - 1][0] - 0.01 * millimeter)
            {
                var last = braceSpans[nb - 1];
                if (spans[k][0] < last[0])
                {
                    last[0] = spans[k][0];
                }
                braceSpans[nb - 1] = last;
            }
            else
            {
                braceSpans = append(braceSpans, spans[k]);
            }
        }

        // The middle brace — the one the tray hangs from — is THREE sheets,
        // the same nut sandwich as the cover rails: a clearance sheet against
        // the panels, a middle sheet with the tray's four nuts in hex pockets,
        // and a clearance sheet behind that the nuts pull against. All three
        // are tenoned into the side walls and the panel screws clamp them
        // together — no glue. The nuts go in before the rear sheet does.
        var trayBrace = 0;
        for (var k = 0; k < size(braceSpans); k += 1)
        {
            if (braceSpans[k][0] <= 0 * millimeter && braceSpans[k][1] >= 0 * millimeter)
            {
                trayBrace = k;
            }
        }
        const trayScrews = [[definition.trayScrewX1,  definition.trayScrewY],
                            [definition.trayScrewX1, -definition.trayScrewY],
                            [definition.trayScrewX2,  definition.trayScrewY],
                            [definition.trayScrewX2, -definition.trayScrewY]];

        for (var s = 0; s < size(braceSpans); s += 1)
        {
            const lo = braceSpans[s][0];
            const hi = braceSpans[s][1];

            fCuboid(context, id + ("brace" ~ s), {
                    "corner1" : vector(left,  lo - kerf / 2, zBraceB),
                    "corner2" : vector(right, hi + kerf / 2, zBraceF) });
            const doubled = (s == trayBrace);
            var braceBodies = [qCreatedBy(id + ("brace" ~ s), EntityType.BODY)];
            if (doubled)
            {
                fCuboid(context, id + ("braceMid" ~ s), {
                        "corner1" : vector(left,  lo - kerf / 2, zBraceB - t),
                        "corner2" : vector(right, hi + kerf / 2, zBraceB) });
                fCuboid(context, id + ("braceRear" ~ s), {
                        "corner1" : vector(left,  lo - kerf / 2, zBraceB - 2 * t),
                        "corner2" : vector(right, hi + kerf / 2, zBraceB - t) });
                braceBodies = append(braceBodies, qCreatedBy(id + ("braceMid" ~ s), EntityType.BODY));
                braceBodies = append(braceBodies, qCreatedBy(id + ("braceRear" ~ s), EntityType.BODY));
            }

            // Mortise both side walls. Shrunk by kerf/2 in the wall's own
            // plane (y and z); x overshoots, which is harmless because only
            // the wall is a target.
            var mZ0 = zBraceB + kerf / 2;
            if (doubled)
            {
                mZ0 = zBraceB - 2 * t + kerf / 2;
            }
            // slots and pin holes go through every sheet of this brace
            var zSlotB = zBraceB;
            if (doubled)
            {
                zSlotB = zBraceB - 2 * t;
            }
            const mZ1 = zBraceF - kerf / 2;

            const sideWalls = ["wallL", "wallR"];
            for (var w = 0; w < 2; w += 1)
            {
                fCuboid(context, id + ("mort" ~ s ~ w), {
                        "corner1" : vector(left - over,  lo + kerf / 2, mZ0),
                        "corner2" : vector(right + over, hi - kerf / 2, mZ1) });
                opBoolean(context, id + ("mortCut" ~ s ~ w), {
                        "tools"         : qCreatedBy(id + ("mort" ~ s ~ w), EntityType.BODY),
                        "targets"       : qCreatedBy(id + sideWalls[w], EntityType.BODY),
                        "operationType" : BooleanOperationType.SUBTRACTION });
            }

            // Obround screw slots, two per panel per insert row that falls in
            // this brace. Oversize in BOTH axes: slotLen is the butting
            // travel, and slotW leaves the y location to the pins rather than
            // fighting them — a screw that also located would over-constrain
            // the panel. Use washers under the screw heads.
            const rs = definition.slotW / 2 - kerf / 2;
            const pr = definition.pinHoleDia / 2 - kerf / 2;
            var slots = [];
            for (var r = 0; r < nRows; r += 1)
            {
                const rc = ((nRows - 1) / 2 - r) * definition.panelH;
                for (var pi = 0; pi < nCols; pi += 1)
                {
                    const pc = (pi - (nCols - 1) / 2) * definition.panelW;

                    for (var j = 0; j < 2; j += 1)
                    {
                        var py = rc + definition.braceYOffset;
                        if (j == 1)
                        {
                            py = rc - definition.braceYOffset;
                        }
                        if (py <= lo || py >= hi)
                        {
                            continue;
                        }
                        for (var k = 0; k < 2; k += 1)
                        {
                            var px = pc + definition.postXOffset;
                            if (k == 1)
                            {
                                px = pc - definition.postXOffset;
                            }
                            const tag = "" ~ s ~ r ~ pi ~ j ~ k;
                            const a = px - definition.slotLen / 2;
                            const b = px + definition.slotLen / 2;

                            fCylinder(context, id + ("sa" ~ tag), {
                                    "topCenter"    : vector(a, py, zBraceF + over),
                                    "bottomCenter" : vector(a, py, zSlotB - over),
                                    "radius"       : rs });
                            fCylinder(context, id + ("sb" ~ tag), {
                                    "topCenter"    : vector(b, py, zBraceF + over),
                                    "bottomCenter" : vector(b, py, zSlotB - over),
                                    "radius"       : rs });
                            fCuboid(context, id + ("sm" ~ tag), {
                                    "corner1" : vector(a, py - rs, zSlotB - over),
                                    "corner2" : vector(b, py + rs, zBraceF + over) });

                            slots = append(slots, qCreatedBy(id + ("sa" ~ tag), EntityType.BODY));
                            slots = append(slots, qCreatedBy(id + ("sb" ~ tag), EntityType.BODY));
                            slots = append(slots, qCreatedBy(id + ("sm" ~ tag), EntityType.BODY));
                        }
                    }

                    // Registration pin holes, if this row's pins land in
                    // this brace. Same obround construction and kerf rule.
                    const pinY = rc + definition.pinYOffset;
                    if (pinY - definition.pinHoleDia / 2 > lo && pinY + definition.pinHoleDia / 2 < hi)
                    {
                        for (var k = 0; k < 2; k += 1)
                        {
                            var px = pc + definition.pinXOffset;
                            if (k == 1)
                            {
                                px = pc - definition.pinXOffset;
                            }
                            const tag = "" ~ s ~ r ~ pi ~ k;
                            const a = px - definition.pinSlotLen / 2;
                            const b = px + definition.pinSlotLen / 2;

                            fCylinder(context, id + ("pa" ~ tag), {
                                    "topCenter"    : vector(a, pinY, zBraceF + over),
                                    "bottomCenter" : vector(a, pinY, zSlotB - over),
                                    "radius"       : pr });
                            fCylinder(context, id + ("pb" ~ tag), {
                                    "topCenter"    : vector(b, pinY, zBraceF + over),
                                    "bottomCenter" : vector(b, pinY, zSlotB - over),
                                    "radius"       : pr });
                            fCuboid(context, id + ("pm" ~ tag), {
                                    "corner1" : vector(a, pinY - pr, zSlotB - over),
                                    "corner2" : vector(b, pinY + pr, zBraceF + over) });

                            slots = append(slots, qCreatedBy(id + ("pa" ~ tag), EntityType.BODY));
                            slots = append(slots, qCreatedBy(id + ("pb" ~ tag), EntityType.BODY));
                            slots = append(slots, qCreatedBy(id + ("pm" ~ tag), EntityType.BODY));
                        }
                    }
                }
            }

            if (size(slots) > 0)
            {
                opBoolean(context, id + ("slotCut" ~ s), {
                        "tools"         : qUnion(slots),
                        "targets"       : qUnion(braceBodies),
                        "operationType" : BooleanOperationType.SUBTRACTION });
            }
        }

        // The tray's captive nuts: hex pockets in the MIDDLE sheet of the
        // middle brace, clearance through the front and rear sheets.
        const trayClrR = definition.screwDia / 2 + 0.25 * millimeter;
        var nutPockets = [];
        var nutClear = [];
        for (var k = 0; k < size(trayScrews); k += 1)
        {
            const sx = trayScrews[k][0];
            const sy = trayScrews[k][1];
            nutPockets = append(nutPockets,
                hexPrism(context, id + ("trayNut" ~ k), sx, sy, definition.nutAcrossFlats - kerf,
                         zBraceB - t - over, zBraceB + over));
            fCylinder(context, id + ("trayNutClr" ~ k), {
                    "topCenter"    : vector(sx, sy, zBraceF + over),
                    "bottomCenter" : vector(sx, sy, zBraceB - 2 * t - over),
                    "radius"       : trayClrR });
            nutClear = append(nutClear, qCreatedBy(id + ("trayNutClr" ~ k), EntityType.BODY));
        }
        opBoolean(context, id + "trayNutCut", {
                "tools"         : qUnion(nutPockets),
                "targets"       : qCreatedBy(id + ("braceMid" ~ trayBrace), EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });
        opBoolean(context, id + "trayNutClrCut", {
                "tools"         : qUnion(nutClear),
                "targets"       : qUnion([qCreatedBy(id + ("brace" ~ trayBrace), EntityType.BODY),
                                          qCreatedBy(id + ("braceRear" ~ trayBrace), EntityType.BODY)]),
                "operationType" : BooleanOperationType.SUBTRACTION });

        // ── rear rails and the removable back cover ─────────────────────
        // The finger joints get glued. The back does not, so it needs a
        // fastening that survives being opened indefinitely — wood screws in
        // 3mm basswood would strip after a few cycles.
        //
        // Tightening pulls the nut TOWARD the screw head, so the nut must
        // bear against material on that side, with only a clearance hole
        // through it. That is a counterbore, and one laser-cut sheet cannot
        // make one — so the rail is three laminations:
        //
        //     z:  -D      -D+t    -D+2t    -D+3t    -D+4t
        //         ├────────┼────────┼────────┼────────┤
        //         │ back   │ rail A │ rail B │ rail C │
        //         │ cover  │ Ø clr  │  hex   │ Ø clr  │
        //         │ Ø clr  │        │  nut   │        │
        //         └────────┴────────┴────────┴────────┘
        //          screw ───────────►  ↑
        //                    nut pulls back against rail A
        //
        // Rail A takes the nut's load — it bears on A's front face, and the
        // screw head clamps the cover against A's rear face.
        //
        // Rail B holds the nut laterally. Rail C stops it escaping into the
        // box when the screw is out — its hole is smaller than the nut's
        // across-flats, so the nut cannot pass, but any screw length can.
        //
        // THE TENON IS ON C, NOT A. A is the obvious choice — it is the one
        // the nut bears on — but A sits one thickness from the rear edge, so
        // its mortise leaves a 3mm sliver of side wall between the slot and
        // the edge, and that sliver lands exactly on the roots of the
        // bottom-wall finger notches. Any notch under it opens into the
        // slot: not thin, absent. Tenoning C instead puts the mortise 3t
        // from the rear edge with 9mm of wall behind it.
        //
        // The cost is that the nut's load reaches the wall through the two
        // glue lines of the lamination stack rather than directly. That is
        // not the weak link, and the numbers are not close:
        //
        //     tenon in shear   3 x 18 x 2 sides = 108mm^2 @ ~6MPa  ->  650N
        //     glue line        18 x 290         = 5220mm^2 @ ~2MPa -> 10kN
        //
        // The tenon is 15x weaker either way, so moving which lamination
        // carries it changes nothing that matters.
        //
        // The rails are also INSET from the top and bottom walls by
        // railInset, for the same reason in the other axis — flush against
        // the wall put the mortise hard against those same finger notches.
        //
        // The back cover is INSET into the wall opening rather than lapped
        // over it, so its outer face finishes flush with the wall rear edges
        // and the fixings are all that shows from behind.

        const zBc0 = zBack;                 // back cover, flush with wall rear
        const zBc1 = zBack + t;
        const railZ = [zBc1, zBc1 + t, zBc1 + 2 * t, zBc1 + 3 * t];

        const bcl = definition.backClearance;
        const railW = definition.railW;
        const clrR = definition.screwDia / 2 + 0.25 * millimeter;

        fCuboid(context, id + "backCover", {
                "corner1" : vector(left + t + bcl,  bottom + t + bcl, zBc0),
                "corner2" : vector(right - t - bcl, top - t - bcl,    zBc1) });

        const rIns = definition.railInset;
        const railY0 = [bottom + t + rIns, top - t - rIns - railW];
        var coverHoles = [];

        for (var ri = 0; ri < 2; ri += 1)
        {
            const y0 = railY0[ri];
            const y1 = y0 + railW;
            const yMid = (y0 + y1) / 2;

            // Rails A and B — inner width, glued to C, so no joints needed.
            fCuboid(context, id + ("railA" ~ ri), {
                    "corner1" : vector(left + t,  y0, railZ[0]),
                    "corner2" : vector(right - t, y1, railZ[1]) });
            fCuboid(context, id + ("railB" ~ ri), {
                    "corner1" : vector(left + t,  y0, railZ[1]),
                    "corner2" : vector(right - t, y1, railZ[2]) });

            // Rail C — through-tenoned into the side walls, 3t from the rear
            // edge so the mortise has wall material all the way round it.
            fCuboid(context, id + ("railC" ~ ri), {
                    "corner1" : vector(left,  y0 - kerf / 2, railZ[2]),
                    "corner2" : vector(right, y1 + kerf / 2, railZ[3]) });

            const rSide = ["wallL", "wallR"];
            for (var w = 0; w < 2; w += 1)
            {
                fCuboid(context, id + ("rmort" ~ ri ~ w), {
                        "corner1" : vector(left - over,  y0 + kerf / 2, railZ[2] + kerf / 2),
                        "corner2" : vector(right + over, y1 - kerf / 2, railZ[3] - kerf / 2) });
                opBoolean(context, id + ("rmortCut" ~ ri ~ w), {
                        "tools"         : qCreatedBy(id + ("rmort" ~ ri ~ w), EntityType.BODY),
                        "targets"       : qCreatedBy(id + rSide[w], EntityType.BODY),
                        "operationType" : BooleanOperationType.SUBTRACTION });
            }

            var clrA = [];
            var pockets = [];
            var clrC = [];

            for (var k = 0; k < definition.screwsPerRail; k += 1)
            {
                var sx = 0 * meter;
                if (definition.screwsPerRail > 1)
                {
                    sx = -definition.screwXSpan
                       + k * (2 * definition.screwXSpan / (definition.screwsPerRail - 1));
                }
                const tag = "" ~ ri ~ k;

                // clearance through the back cover
                fCylinder(context, id + ("bch" ~ tag), {
                        "topCenter"    : vector(sx, yMid, zBc1 + over),
                        "bottomCenter" : vector(sx, yMid, zBc0 - over),
                        "radius"       : definition.screwDia / 2 - kerf / 2 });
                coverHoles = append(coverHoles, qCreatedBy(id + ("bch" ~ tag), EntityType.BODY));

                // clearance through rail A — the nut bears on the ring around it
                fCylinder(context, id + ("cah" ~ tag), {
                        "topCenter"    : vector(sx, yMid, railZ[1] + over),
                        "bottomCenter" : vector(sx, yMid, railZ[0] - over),
                        "radius"       : clrR });
                clrA = append(clrA, qCreatedBy(id + ("cah" ~ tag), EntityType.BODY));

                // hex pocket through rail B — the nut itself
                pockets = append(pockets,
                    hexPrism(context, id + ("hexp" ~ tag), sx, yMid,
                             definition.nutAcrossFlats - kerf, railZ[1] - over, railZ[2] + over));

                // clearance through rail C — retains the nut, passes any screw
                fCylinder(context, id + ("cch" ~ tag), {
                        "topCenter"    : vector(sx, yMid, railZ[3] + over),
                        "bottomCenter" : vector(sx, yMid, railZ[2] - over),
                        "radius"       : clrR });
                clrC = append(clrC, qCreatedBy(id + ("cch" ~ tag), EntityType.BODY));
            }

            opBoolean(context, id + ("clrACut" ~ ri), {
                    "tools"         : qUnion(clrA),
                    "targets"       : qCreatedBy(id + ("railA" ~ ri), EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION });
            opBoolean(context, id + ("pocketCut" ~ ri), {
                    "tools"         : qUnion(pockets),
                    "targets"       : qCreatedBy(id + ("railB" ~ ri), EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION });
            opBoolean(context, id + ("clrCCut" ~ ri), {
                    "tools"         : qUnion(clrC),
                    "targets"       : qCreatedBy(id + ("railC" ~ ri), EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION });
        }

        // ── stiffening: one horizontal brace ────────────────────────────
        // Horizontal, and that orientation is the whole point. The
        // back-cover rail stacks run HORIZONTALLY along the top and bottom
        // edges, so a vertical brace has to cross both of them — no position
        // avoids it, only notching, which is what made the earlier vertical
        // web fight them. This brace is parallel to the rails and sits
        // between them, so it cannot clash at any depth.
        //
        // Placed just under the display aperture, which is the one y band
        // clear of everything: 3mm above the PSU, 0.5mm below the panels,
        // clear of the knob cluster, and nowhere near either rail stack.
        //
        // 18mm deep at the rear, leaving ~33mm at the front for the I2C run
        // from the knob cluster up to the Pi on the back cover.

        const braceTopY = -definition.apertureH / 2 - 0.5 * millimeter;
        const braceBotY = braceTopY - t;
        // Starts at the same depth as rail C's mortise, and for the same
        // reason: at zBack + t its own mortise left a 3mm sliver at the rear
        // edge of each side wall.
        const stiffZ0 = railZ[2];
        const stiffZ1 = stiffZ0 + definition.webDepth;

        fCuboid(context, id + "stiff", {
                "corner1" : vector(left,  braceBotY - kerf / 2, stiffZ0),
                "corner2" : vector(right, braceTopY + kerf / 2, stiffZ1) });

        const stiffSides = ["wallL", "wallR"];
        for (var w = 0; w < 2; w += 1)
        {
            fCuboid(context, id + ("stmort" ~ w), {
                    "corner1" : vector(left - over,  braceBotY + kerf / 2, stiffZ0 + kerf / 2),
                    "corner2" : vector(right + over, braceTopY - kerf / 2, stiffZ1 - kerf / 2) });
            opBoolean(context, id + ("stmortCut" ~ w), {
                    "tools"         : qCreatedBy(id + ("stmort" ~ w), EntityType.BODY),
                    "targets"       : qCreatedBy(id + stiffSides[w], EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION });
        }

        // PSU mounting clearance through the BOTTOM wall. Its side-face holes
        // are 10 and 84 from one end of a 99.24mm case — 2.5mm off centre, so
        // these are not symmetric either. Screw path is 3mm wall + a
        // psuStandoff spacer + up to 5mm of thread, i.e. M3x12.
        // Datum is the TERMINAL end. Both views on the spec sheet dimension
        // from it, and the terminals have to face +x toward the IEC inlet or
        // the mains run crosses the whole box — so these come off the HIGH-x
        // end. That matters because the pair is centred 2.62mm off the case
        // centre; referencing the wrong end puts them 5.24mm out.
        var psuHoles = [];
        const psuXHi = definition.psuX + definition.psuL / 2;
        const psuHoleXs = [psuXHi - definition.psuHoleBX, psuXHi - definition.psuHoleAX];
        // The two side holes ARE collinear — confirmed on the part — and they
        // are threaded M3, so ordinary M3 hardware bolts straight in and no
        // slot or insert is needed. One shared height.
        for (var ph = 0; ph < 2; ph += 1)
        {
            fCylinder(context, id + ("psuh" ~ ph), {
                    "topCenter"    : vector(psuHoleXs[ph], bottom + t + over, definition.psuZFront - definition.psuHoleZ),
                    "bottomCenter" : vector(psuHoleXs[ph], bottom - over,     definition.psuZFront - definition.psuHoleZ),
                    "radius"       : definition.psuHoleDia / 2 - kerf / 2 });
            psuHoles = append(psuHoles, qCreatedBy(id + ("psuh" ~ ph), EntityType.BODY));
        }
        opBoolean(context, id + "psuHoleCut", {
                "tools"         : qUnion(psuHoles),
                "targets"       : qCreatedBy(id + "wallB", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });

        // ── IEC inlet, right wall ───────────────────────────────────────
        // In the right wall, low in the control band, beside the PSU's
        // terminals so the mains run stays short. The 2 x 2 box stands on its
        // bottom wall, so that wall cannot carry the inlet any more. See the
        // iecProxy header for the clearances.

        var iecTools = [];

        fCuboid(context, id + "iecCut", {
                "corner1" : vector(right - t - over,
                                   definition.iecY - definition.iecCutW / 2 + kerf / 2,
                                   definition.iecZ - definition.iecCutH / 2 + kerf / 2),
                "corner2" : vector(right + over,
                                   definition.iecY + definition.iecCutW / 2 - kerf / 2,
                                   definition.iecZ + definition.iecCutH / 2 - kerf / 2) });
        iecTools = append(iecTools, qCreatedBy(id + "iecCut", EntityType.BODY));

        // Flange screws, on the SHORT axis (z), in the triangular lobes.
        for (var us = 0; us < 2; us += 1)
        {
            var uz = definition.iecZ - definition.iecScrewSpacing / 2;
            if (us == 1)
            {
                uz = definition.iecZ + definition.iecScrewSpacing / 2;
            }
            fCylinder(context, id + ("iecScrew" ~ us), {
                    "topCenter"    : vector(right + over,     definition.iecY, uz),
                    "bottomCenter" : vector(right - t - over, definition.iecY, uz),
                    "radius"       : definition.iecScrewDia / 2 - kerf / 2 });
            iecTools = append(iecTools, qCreatedBy(id + ("iecScrew" ~ us), EntityType.BODY));
        }

        opBoolean(context, id + "iecCutOp", {
                "tools"         : qUnion(iecTools),
                "targets"       : qCreatedBy(id + "wallR", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });

        // ── electronics tray ────────────────────────────────────────────
        // Two sheets, screwed to the back of the three-sheet middle brace by
        // four M3 into its captive nuts, on spacer rings. The boards mount on
        // the tray's rear face with the same nut sandwich again: the tray's
        // FRONT sheet is the clearance layer, its REAR sheet holds the nuts in
        // hex pockets, and a clearance ring between tray and board is the
        // layer the nut pulls against. The screws clamp it all — no glue:
        //
        //   panel│ C │ B │ A │ring│ A' │ B' │ C' │ board
        //        └─ middle brace ─┘    └─ tray ─┘ ring
        //   tray nut in B   ◄── M3 x 16 from behind, through tray, ring, A
        //   board nut in B' ◄── M3 x 8 from the board side, through ring C'
        //
        // Assembly: tray nuts into the brace's middle sheet, rear sheet on ->
        // panels on -> on the bench, tray face down, board nuts into the
        // tray's rear sheet, rings, boards, M3 x 8 -> tray in, 4 x M3 x 16 ->
        // back cover. To take a panel off: cover off, tray off, its screws
        // are exposed.
        //
        // The tray stops at |y| 47 so the HUB75 ribbons wrap round its top and
        // bottom edges to the panels' IN ports, and so it clears the panels'
        // 5 V plugs, which reach to z -33.5 at |y| >= 49.
        const sr = definition.spacerRings * t;
        const br = definition.boardRings * t;
        const trayF = zBraceB - 2 * t - sr;         // tray front face
        const trayM = trayF - t;                    // between its two sheets
        const trayB = trayF - 2 * t;                // tray rear face (boards side)
        const tx0 = left + t + definition.trayClear;
        const tx1 = right - t - definition.trayClear;

        fCuboid(context, id + "tray", {
                "corner1" : vector(tx0, definition.trayY0, trayM),
                "corner2" : vector(tx1, definition.trayY1, trayF) });
        fCuboid(context, id + "trayRear", {
                "corner1" : vector(tx0, definition.trayY0, trayB),
                "corner2" : vector(tx1, definition.trayY1, trayM) });

        var boardSites = [];
        for (var h = 0; h < size(CL_HOLES); h += 1)
        {
            const bp = clToBox(definition.clX, definition.clY, CL_HOLES[h][0], CL_HOLES[h][1]);
            boardSites = append(boardSites, [bp[0], bp[1], "Colorlight " ~ (h + 1)]);
        }
        for (var h = 0; h < size(PI_HOLES); h += 1)
        {
            const bp = piToBox(definition.piX, definition.piY, PI_HOLES[h][0], PI_HOLES[h][1]);
            boardSites = append(boardSites, [bp[0], bp[1], "Pi " ~ (h + 1)]);
        }

        var throughCuts = [];       // both tray sheets
        var frontCuts = [];         // front sheet only
        var rearCuts = [];          // rear sheet only
        var ringN = 0;

        const ring = function(rid is Id, sx, sy, z0, rOut, name is string)
        {
            fCylinder(context, rid, {
                    "topCenter"    : vector(sx, sy, z0 + t),
                    "bottomCenter" : vector(sx, sy, z0),
                    "radius"       : rOut });
            fCylinder(context, rid + "bore", {
                    "topCenter"    : vector(sx, sy, z0 + t + over),
                    "bottomCenter" : vector(sx, sy, z0 - over),
                    "radius"       : trayClrR - kerf / 2 });
            opBoolean(context, rid + "cut", {
                    "tools"         : qCreatedBy(rid + "bore", EntityType.BODY),
                    "targets"       : qSubtraction(qCreatedBy(rid, EntityType.BODY),
                                                   qCreatedBy(rid + "bore", EntityType.BODY)),
                    "operationType" : BooleanOperationType.SUBTRACTION });
            nameBody(context, rid + "n", rid, name);
        };

        // tray screws: clearance through both sheets; rings in front of the tray
        for (var k = 0; k < size(trayScrews); k += 1)
        {
            const sx = trayScrews[k][0];
            const sy = trayScrews[k][1];
            fCylinder(context, id + ("trayHole" ~ k), {
                    "topCenter"    : vector(sx, sy, trayF + over),
                    "bottomCenter" : vector(sx, sy, trayB - over),
                    "radius"       : trayClrR - kerf / 2 });
            throughCuts = append(throughCuts, qCreatedBy(id + ("trayHole" ~ k), EntityType.BODY));
            for (var L = 0; L < definition.spacerRings; L += 1)
            {
                ring(id + ("ring" ~ ringN), sx, sy, trayF + L * t, definition.spacerOD / 2,
                     "Spacer ring — tray to brace");
                ringN += 1;
            }
        }

        // board screws: clearance in the front sheet, nut pocket in the rear
        // sheet, rings between the tray and the board
        for (var k = 0; k < size(boardSites); k += 1)
        {
            const sx = boardSites[k][0];
            const sy = boardSites[k][1];
            fCylinder(context, id + ("boardHole" ~ k), {
                    "topCenter"    : vector(sx, sy, trayF + over),
                    "bottomCenter" : vector(sx, sy, trayM - over),
                    "radius"       : trayClrR - kerf / 2 });
            frontCuts = append(frontCuts, qCreatedBy(id + ("boardHole" ~ k), EntityType.BODY));
            rearCuts = append(rearCuts,
                hexPrism(context, id + ("boardNut" ~ k), sx, sy, definition.nutAcrossFlats - kerf,
                         trayB - over, trayM + over));
            for (var L = 0; L < definition.boardRings; L += 1)
            {
                ring(id + ("ring" ~ ringN), sx, sy, trayB - (L + 1) * t, definition.boardRingOD / 2,
                     "Spacer ring — " ~ boardSites[k][2]);
                ringN += 1;
            }
        }

        // two zip-tie strap positions round the USB adapter, a slot each side
        for (var k = 0; k < 2; k += 1)
        {
            const sxs = definition.nicX + (2 * k - 1) * definition.nicW / 4;
            for (var j = 0; j < 2; j += 1)
            {
                const sys = definition.nicY + (2 * j - 1) * (definition.nicH / 2 + 2.5 * millimeter);
                fCuboid(context, id + ("strap" ~ k ~ j), {
                        "corner1" : vector(sxs - 3 * millimeter, sys - 1.25 * millimeter, trayB - over),
                        "corner2" : vector(sxs + 3 * millimeter, sys + 1.25 * millimeter, trayF + over) });
                throughCuts = append(throughCuts, qCreatedBy(id + ("strap" ~ k ~ j), EntityType.BODY));
            }
        }
        opBoolean(context, id + "trayCutF", {
                "tools"         : qUnion(concatenateArrays([throughCuts, frontCuts])),
                "targets"       : qCreatedBy(id + "tray", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION,
                "keepTools"     : true });
        opBoolean(context, id + "trayCutR", {
                "tools"         : qUnion(concatenateArrays([throughCuts, rearCuts])),
                "targets"       : qCreatedBy(id + "trayRear", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });
        opDeleteBodies(context, id + "trayCutLeft", { "entities" : qUnion(frontCuts) });

        opBoolean(context, id + "coverCut", {
                "tools"         : qUnion(coverHoles),
                "targets"       : qCreatedBy(id + "backCover", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });

        // ── display aperture and knob bores, through every lamination ───
        var tools = [];

        fCuboid(context, id + "apTool", {
                "corner1" : vector(-definition.apertureW / 2, -definition.apertureH / 2, zBezB - over),
                "corner2" : vector( definition.apertureW / 2,  definition.apertureH / 2, over) });
        tools = append(tools, qCreatedBy(id + "apTool", EntityType.BODY));

        // A 2-D cluster, not a row. Four knobs in a 2x2 block occupy 70mm of
        // band width against 160mm for a 1x4 — and that 90mm is exactly what
        // the IEC module needs, because it protrudes ~30mm behind its panel
        // and a full-width knob row left only 10mm beside the PSU.
        //
        // Index order is reading order: K1 top-left, K2 top-right, K3
        // bottom-left, K4 bottom-right. Upstream assigns fixed functions to
        // K1..K4 (brightness, network, knob values, pattern list), so write
        // this down next to the I2C addresses or the front panel will not
        // match its own documentation.
        const kCols = definition.knobCols;
        const kRows = floor((definition.knobCount + kCols - 1) / kCols);
        var pockets = [];

        for (var i = 0; i < definition.knobCount; i += 1)
        {
            const kc = i % kCols;
            const kr = floor(i / kCols);
            const knobX = definition.knobXCentre
                        + (kc - (kCols - 1) / 2) * definition.knobPitch;
            const knobY = definition.knobYCentre
                        - (kr - (kRows - 1) / 2) * definition.knobPitch;
            fCylinder(context, id + ("bore" ~ i), {
                    "topCenter"    : vector(knobX, knobY, over),
                    "bottomCenter" : vector(knobX, knobY, zBezB - over),
                    "radius"       : definition.boreDia / 2 });
            tools = append(tools, qCreatedBy(id + ("bore" ~ i), EntityType.BODY));

            // The EC11's bushing has 5.5 mm of thread and its jam nut is
            // 2.3 mm: it can only clamp ONE sheet (measured 2026-10-18). So
            // every lamination behind the outer one is pocketed round the
            // knob and the encoder's mounting face sits against the outer
            // sheet's back. The pocket is sized for the Adafruit 4991 QT
            // breakout right behind the encoder body (~26 mm board, 35 mm
            // square with its STEMMA QT plugs), not just the 15 mm body.
            const hp = definition.knobPocket / 2;
            fCuboid(context, id + ("kpocket" ~ i), {
                    "corner1" : vector(knobX - hp, knobY - hp, zBezB - over),
                    "corner2" : vector(knobX + hp, knobY + hp, zOut0) });
            pockets = append(pockets, qCreatedBy(id + ("kpocket" ~ i), EntityType.BODY));
        }

        opBoolean(context, id + "cut", {
                "tools"         : qUnion(tools),
                "targets"       : qUnion(plates),
                "operationType" : BooleanOperationType.SUBTRACTION });
        if (nl > 1)
        {
            opBoolean(context, id + "kpocketCut", {
                    "tools"         : qUnion(pockets),
                    "targets"       : qSubtraction(qUnion(plates), outerPlate),
                    "operationType" : BooleanOperationType.SUBTRACTION });
        }

        // ── Part identity ──────────────────────────────────────────────
        // Until now every body was anonymous, which was fine while the only
        // consumer was a bounding-box query. It stops being fine the moment
        // anything downstream needs to refer to ONE part: an assembly
        // instance list, a BOM line, or a DXF file name. Naming here rather
        // than in the document keeps the repo the source of truth — rename a
        // body in Onshape and the next push silently reverts it.
        // layer0 is the REARMOST lamination (inset, drops inside the tube);
        // layer(nl-1) is the full-footprint outer face. These were the other
        // way round, so the DXF called "Bezel outer" was the inset one.
        nameBody(context, id + "n01", id + ("layer" ~ (nl - 1)), "Bezel outer");
        nameBody(context, id + "n02", id + "layer0",             "Bezel inner");
        nameBody(context, id + "n03", id + "wallL",   "Wall left");
        nameBody(context, id + "n04", id + "wallR",   "Wall right (IEC)");
        nameBody(context, id + "n05", id + "wallB",   "Wall bottom");
        nameBody(context, id + "n06", id + "wallT",   "Wall top");
        nameBody(context, id + "n07", id + "backCover", "Back cover");
        nameBody(context, id + "n08", id + "stiff",   "Stiffener web");
        nameBody(context, id + "n08t", id + "tray",   "Electronics tray, front sheet");
        nameBody(context, id + "n08r", id + "trayRear", "Electronics tray, rear sheet (board nuts)");
        // Braces top to bottom. brace0 and brace1 keep the ids they had in
        // the 2 x 1 design, so existing assembly instances follow them.
        const nBraces = size(braceSpans);
        for (var bi = 0; bi < nBraces; bi += 1)
        {
            var bn = "Panel brace " ~ (bi + 1);
            if (bi == 0)                         { bn = "Panel brace upper"; }
            else if (bi == nBraces - 1)          { bn = "Panel brace lower"; }
            else if (nBraces == 3)               { bn = "Panel brace middle"; }
            nameBody(context, id + ("nbr" ~ bi), id + ("brace" ~ bi), bn);
        }
        nameBody(context, id + "nbrM", id + ("braceMid" ~ trayBrace), "Panel brace middle, middle sheet (tray nuts)");
        nameBody(context, id + "nbrR", id + ("braceRear" ~ trayBrace), "Panel brace middle, rear sheet");
        for (var ri = 0; ri < 2; ri += 1)
        {
            var where = "lower";
            if (ri == 1) { where = "upper"; }
            nameBody(context, id + ("nrA" ~ ri), id + ("railA" ~ ri),
                     "Rail A " ~ where ~ " (screw clearance)");
            nameBody(context, id + ("nrB" ~ ri), id + ("railB" ~ ri),
                     "Rail B " ~ where ~ " (hex pocket)");
            nameBody(context, id + ("nrC" ~ ri), id + ("railC" ~ ri),
                     "Rail C " ~ where ~ " (tenoned)");
        }

        // ── Mate connectors ────────────────────────────────────────────
        // Published so the ASSEMBLY can position real vendor parts against
        // the enclosure without re-deriving a single coordinate. Both sides
        // then read the same Variable Studio, which is what keeps "the box
        // follows the insides" true without in-context references.
        opMateConnector(context, id + "mcOrigin", {
                "coordSystem" : coordSystem(vector(0, 0, 0) * millimeter,
                                            vector(1, 0, 0), vector(0, 0, 1)),
                "owner"       : qCreatedBy(id + "layer0", EntityType.BODY) });

        // One per panel, reading order, at the panel's centre on its face.
        for (var i = 0; i < nCols * nRows; i += 1)
        {
            const pcx = (i % nCols - (nCols - 1) / 2) * definition.panelW;
            const pcy = ((nRows - 1) / 2 - floor(i / nCols)) * definition.panelH;
            opMateConnector(context, id + ("mcPanel" ~ i), {
                    "coordSystem" : coordSystem(vector(pcx, pcy, 0 * millimeter),
                                                vector(1, 0, 0), vector(0, 0, 1)),
                    "owner"       : qCreatedBy(id + "layer0", EntityType.BODY) });
        }

        // PSU datum. Mean Well's STEP has its origin at the corner where the
        // TERMINAL end, the MOUNTING-HOLE face and the BASE meet, so this
        // connector maps that corner into our frame:
        //
        //   ours = (psuXHi - X,  psuYLo + Y,  psuZFront - Z)
        //
        // The z flip is the part that matters — it is what puts the cover,
        // and therefore the terminal screws, toward the removable back cover
        // rather than the glued bezel. Fasten the vendor part to this and the
        // orientation cannot be got wrong by hand.
        opMateConnector(context, id + "mcPsu", {
                "coordSystem" : coordSystem(vector(definition.psuX + definition.psuL / 2,
                                                   bottom + t + definition.psuStandoff,
                                                   definition.psuZFront),
                                            vector(-1, 0, 0), vector(0, 0, -1)),
                "owner"       : qCreatedBy(id + "wallB", EntityType.BODY) });

        // IEC datum: cutout centre on the right wall's outer face, long
        // axis along +y, z pointing out of the box.
        opMateConnector(context, id + "mcIec", {
                "coordSystem" : coordSystem(vector(right, definition.iecY, definition.iecZ),
                                            vector(0, 1, 0), vector(1, 0, 0)),
                "owner"       : qCreatedBy(id + "wallR", EntityType.BODY) });
    });
