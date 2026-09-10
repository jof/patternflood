FeatureScript 3070;
import(path : "onshape/std/geometry.fs", version : "3070.0");

/**
 * Patternflow desktop enclosure — parametric features.
 *
 * Laser-cut 3 mm basswood finger-joint box, 2 x Waveshare P2 64x64 GOB panels,
 * Matrix Portal S3, 4 x Adafruit 4991 seesaw encoders.
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
 * measured before cutting: #thickness, #kerf, #panelDepth. The EC11 bushing
 * thread length caps #frontThickness — measure it first.
 *
 * Source of truth for this file is the repo, not the Onshape document:
 *   hardware/cad/featurescript/enclosure.fs
 */

// ────────────────────────────────────────────────────────────────────────
// Panel proxy
// ────────────────────────────────────────────────────────────────────────
// Deliberately a plain envelope. A laser-cut enclosure needs the outline,
// the depth and a datum, not detail.

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

        annotation { "Name" : "Panel count" }
        isInteger(definition.count, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Panel body (undersize)" }
        isLength(definition.panelBody, LENGTH_BOUNDS);
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
        const n = definition.count;
        const gap = definition.panelW - definition.panelBody;
        const bodySpan = n * definition.panelBody + (n - 1) * gap;

        for (var i = 0; i < n; i += 1)
        {
            const x0 = -bodySpan / 2 + i * definition.panelW;

            fCuboid(context, id + ("panel" ~ i), {
                    "corner1" : vector(x0, -definition.panelBody / 2, -definition.panelDepth),
                    "corner2" : vector(x0 + definition.panelBody, definition.panelBody / 2, 0 * meter)
            });
        }
    });

// ────────────────────────────────────────────────────────────────────────
// PSU proxy
// ────────────────────────────────────────────────────────────────────────
// Mean Well LRS-50-5 — 99 x 82 x 30 mm, 210 g, 5V 10A. An envelope only.
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
    }
    {
        fCuboid(context, id + "psu", {
                "corner1" : vector(definition.psuX - definition.psuL / 2,
                                   definition.psuYTop - definition.psuW,
                                   definition.psuZFront - definition.psuT),
                "corner2" : vector(definition.psuX + definition.psuL / 2,
                                   definition.psuYTop,
                                   definition.psuZFront) });
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
// short extent is cutH + 2*tip = 48.75mm against a 44.5mm deep case.

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
    }
    {
        // body behind the panel
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
    });

// ────────────────────────────────────────────────────────────────────────
// Bay obstructions
// ────────────────────────────────────────────────────────────────────────
// Proxies for everything that already occupies the bay, so anything added
// there can be checked against them instead of assumed to fit.
//
// Per panel, one connector KEEP-OUT covering the HUB75 IN and OUT headers
// and the JST power connector. Positions are not published and vary, so
// this is one generous envelope rather than individual bosses — measure it
// off a real panel and shrink it.
//
// Plus the Matrix Portal itself, which is the big one: it does not sit
// against the panel, it rides ON the HUB75 header, so it reaches roughly
// 20mm back even though the board's own span is 19.1mm. Footprint measured
// from the vendored Adafruit STEP.

annotation { "Feature Type Name" : "Bay obstructions" }
export const bayObstructions = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Panel width" }
        isLength(definition.panelW, LENGTH_BOUNDS);

        annotation { "Name" : "Panel count" }
        isInteger(definition.panelCount, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Panel depth" }
        isLength(definition.panelDepth, LENGTH_BOUNDS);

        annotation { "Name" : "Keep-out width" }
        isLength(definition.keepoutW, LENGTH_BOUNDS);

        annotation { "Name" : "Keep-out height" }
        isLength(definition.keepoutH, LENGTH_BOUNDS);

        annotation { "Name" : "Keep-out projection" }
        isLength(definition.keepoutProj, LENGTH_BOUNDS);

        annotation { "Name" : "Keep-out offset x" }
        isLength(definition.keepoutX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Keep-out offset y" }
        isLength(definition.keepoutY, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Board width" }
        isLength(definition.mpW, LENGTH_BOUNDS);

        annotation { "Name" : "Board height" }
        isLength(definition.mpH, LENGTH_BOUNDS);

        annotation { "Name" : "Board thickness" }
        isLength(definition.mpProj, LENGTH_BOUNDS);

        annotation { "Name" : "Board front face z" }
        isLength(definition.mpZFront, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Board centre x" }
        isLength(definition.mpX, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Board centre y" }
        isLength(definition.mpY, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "IEC outer face x" }
        isLength(definition.iecXFace, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "IEC centre y" }
        isLength(definition.iecY, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "IEC centre z" }
        isLength(definition.iecZ, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "IEC width (y)" }
        isLength(definition.iecCutW, LENGTH_BOUNDS);

        annotation { "Name" : "IEC height (z)" }
        isLength(definition.iecCutH, LENGTH_BOUNDS);

        annotation { "Name" : "IEC depth behind face" }
        isLength(definition.iecDepth, LENGTH_BOUNDS);
    }
    {
        const back = -definition.panelDepth;
        const span = definition.panelCount * definition.panelW;

        for (var i = 0; i < definition.panelCount; i += 1)
        {
            const pc = -span / 2 + (i + 0.5) * definition.panelW + definition.keepoutX;

            fCuboid(context, id + ("keepout" ~ i), {
                    "corner1" : vector(pc - definition.keepoutW / 2,
                                       definition.keepoutY - definition.keepoutH / 2,
                                       back - definition.keepoutProj),
                    "corner2" : vector(pc + definition.keepoutW / 2,
                                       definition.keepoutY + definition.keepoutH / 2,
                                       back) });
        }

        // The Matrix Portal is now mounted to the CASE, not plugged onto the
        // panel, so its depth is set by where it is bolted rather than by the
        // header height. A HUB75 ribbon reaches the panel instead — which is
        // why the keep-out above got deeper, not shallower: a ribbon needs
        // room to turn behind the connector where a board did not.
        // IEC module envelope — measured 46.75 x 27.25 cutout and 37.45mm of
        // depth behind the outer face. Modelled because it is the reason the
        // knobs are a 2x2 cluster: a full-width knob row left 10.5mm here
        // against the 37.45mm this actually needs.
        fCuboid(context, id + "iec", {
                "corner1" : vector(definition.iecXFace - definition.iecDepth,
                                   definition.iecY - definition.iecCutW / 2,
                                   definition.iecZ - definition.iecCutH / 2),
                "corner2" : vector(definition.iecXFace,
                                   definition.iecY + definition.iecCutW / 2,
                                   definition.iecZ + definition.iecCutH / 2) });

        fCuboid(context, id + "board", {
                "corner1" : vector(definition.mpX - definition.mpW / 2,
                                   definition.mpY - definition.mpH / 2,
                                   definition.mpZFront - definition.mpProj),
                "corner2" : vector(definition.mpX + definition.mpW / 2,
                                   definition.mpY + definition.mpH / 2,
                                   definition.mpZFront) });
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

        annotation { "Name" : "Panel width" }
        isLength(definition.panelW, LENGTH_BOUNDS);

        annotation { "Name" : "Panel count" }
        isInteger(definition.panelCount, POSITIVE_COUNT_BOUNDS);

        annotation { "Name" : "Panel depth" }
        isLength(definition.panelDepth, LENGTH_BOUNDS);

        annotation { "Name" : "Brace y offset" }
        isLength(definition.braceYOffset, LENGTH_BOUNDS);

        annotation { "Name" : "Brace width" }
        isLength(definition.braceW, LENGTH_BOUNDS);

        annotation { "Name" : "Panel post x offset" }
        isLength(definition.postXOffset, LENGTH_BOUNDS);

        annotation { "Name" : "Screw diameter" }
        isLength(definition.screwDia, LENGTH_BOUNDS);

        annotation { "Name" : "Screw slot length" }
        isLength(definition.slotLen, LENGTH_BOUNDS);

        annotation { "Name" : "Screw slot width" }
        isLength(definition.slotW, LENGTH_BOUNDS);

        annotation { "Name" : "Rear rail width" }
        isLength(definition.railW, LENGTH_BOUNDS);

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

        annotation { "Name" : "Mains divider x" }
        isLength(definition.dividerX, ANY_LENGTH_BOUNDS);

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

        annotation { "Name" : "IEC position y" }
        isLength(definition.iecY, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "IEC position z" }
        isLength(definition.iecZ, ANY_LENGTH_BOUNDS);
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
        // The screw holes are OBROUND, running in x. Panel post positions
        // shift between production runs and the datasheets do not give them,
        // so the slot absorbs the error; #postXOffset and #braceYOffset are
        // placeholders until measured off the actual panels.
        //
        // Each brace is a through-tenon: it spans the full box width, so its
        // ends sit inside the walls, and subtracting it from the walls cuts
        // an exactly matching mortise. Kerf goes the opposite way from the
        // finger joints here — the tenon is GROWN by kerf/2 per side and the
        // mortise SHRUNK by kerf/2, so both land on nominal after cutting.

        const zBraceF = -definition.panelDepth;         // against the panel backs
        const zBraceB = zBraceF - t;
        const panelSpan = definition.panelCount * definition.panelW;

        for (var s = 0; s < 2; s += 1)
        {
            var yc = definition.braceYOffset;
            if (s == 1)
            {
                yc = -definition.braceYOffset;
            }

            const tenonHalf = (definition.braceW + kerf) / 2;

            fCuboid(context, id + ("brace" ~ s), {
                    "corner1" : vector(left,  yc - tenonHalf, zBraceB),
                    "corner2" : vector(right, yc + tenonHalf, zBraceF) });

            // Mortise both side walls. Shrunk by kerf/2 in the wall's own
            // plane (y and z); x overshoots, which is harmless because only
            // the wall is a target.
            const mY0 = yc - definition.braceW / 2 + kerf / 2;
            const mY1 = yc + definition.braceW / 2 - kerf / 2;
            const mZ0 = zBraceB + kerf / 2;
            const mZ1 = zBraceF - kerf / 2;

            const sideWalls = ["wallL", "wallR"];
            for (var w = 0; w < 2; w += 1)
            {
                fCuboid(context, id + ("mort" ~ s ~ w), {
                        "corner1" : vector(left - over,  mY0, mZ0),
                        "corner2" : vector(right + over, mY1, mZ1) });
                opBoolean(context, id + ("mortCut" ~ s ~ w), {
                        "tools"         : qCreatedBy(id + ("mort" ~ s ~ w), EntityType.BODY),
                        "targets"       : qCreatedBy(id + sideWalls[w], EntityType.BODY),
                        "operationType" : BooleanOperationType.SUBTRACTION });
            }

            // Obround screw slots, two per panel. Deliberately oversize in
            // BOTH axes: slotLen absorbs x variation between production runs,
            // and slotW absorbs the fact that a panel's hole row is not
            // collinear — measured 8mm edge inset for the end holes and 9mm
            // for the centre hole on a P3, so a straight brace needs ~1mm of
            // perpendicular give too. Use washers under the screw heads.
            const r = definition.slotW / 2 - kerf / 2;
            var slots = [];
            for (var pi = 0; pi < definition.panelCount; pi += 1)
            {
                const pc = -panelSpan / 2 + (pi + 0.5) * definition.panelW;
                for (var k = 0; k < 2; k += 1)
                {
                    var px = pc + definition.postXOffset;
                    if (k == 1)
                    {
                        px = pc - definition.postXOffset;
                    }
                    const a = px - definition.slotLen / 2;
                    const b = px + definition.slotLen / 2;
                    const tag = "" ~ s ~ pi ~ k;

                    fCylinder(context, id + ("sa" ~ tag), {
                            "topCenter"    : vector(a, yc, zBraceF + over),
                            "bottomCenter" : vector(a, yc, zBraceB - over),
                            "radius"       : r });
                    fCylinder(context, id + ("sb" ~ tag), {
                            "topCenter"    : vector(b, yc, zBraceF + over),
                            "bottomCenter" : vector(b, yc, zBraceB - over),
                            "radius"       : r });
                    fCuboid(context, id + ("sm" ~ tag), {
                            "corner1" : vector(a, yc - r, zBraceB - over),
                            "corner2" : vector(b, yc + r, zBraceF + over) });

                    slots = append(slots, qCreatedBy(id + ("sa" ~ tag), EntityType.BODY));
                    slots = append(slots, qCreatedBy(id + ("sb" ~ tag), EntityType.BODY));
                    slots = append(slots, qCreatedBy(id + ("sm" ~ tag), EntityType.BODY));
                }
            }

            opBoolean(context, id + ("slotCut" ~ s), {
                    "tools"         : qUnion(slots),
                    "targets"       : qCreatedBy(id + ("brace" ~ s), EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION });
        }

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
        // Rail A takes the load: the nut bears on its rear face and rail A
        // is through-tenoned into the side walls, so the path is
        // nut -> rail A -> tenon -> wall. The screw head clamps the cover
        // against rail A's front face.
        //
        // Rail B holds the nut laterally. Rail C stops it escaping into the
        // box when the screw is out — its hole is smaller than the nut's
        // across-flats, so the nut cannot pass, but any screw length can.
        // A and C are geometrically identical, so they are the same DXF.
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

        const railY0 = [bottom + t, top - t - railW];
        var coverHoles = [];

        for (var ri = 0; ri < 2; ri += 1)
        {
            const y0 = railY0[ri];
            const y1 = y0 + railW;
            const yMid = (y0 + y1) / 2;

            // Rail A — load-bearing, through-tenoned into the side walls.
            fCuboid(context, id + ("railA" ~ ri), {
                    "corner1" : vector(left,  y0 - kerf / 2, railZ[0]),
                    "corner2" : vector(right, y1 + kerf / 2, railZ[1]) });

            const rSide = ["wallL", "wallR"];
            for (var w = 0; w < 2; w += 1)
            {
                fCuboid(context, id + ("rmort" ~ ri ~ w), {
                        "corner1" : vector(left - over,  y0 + kerf / 2, railZ[0] + kerf / 2),
                        "corner2" : vector(right + over, y1 - kerf / 2, railZ[1] - kerf / 2) });
                opBoolean(context, id + ("rmortCut" ~ ri ~ w), {
                        "tools"         : qCreatedBy(id + ("rmort" ~ ri ~ w), EntityType.BODY),
                        "targets"       : qCreatedBy(id + rSide[w], EntityType.BODY),
                        "operationType" : BooleanOperationType.SUBTRACTION });
            }

            // Rails B and C — inner width, glued to A, so no joints needed.
            fCuboid(context, id + ("railB" ~ ri), {
                    "corner1" : vector(left + t,  y0, railZ[1]),
                    "corner2" : vector(right - t, y1, railZ[2]) });
            fCuboid(context, id + ("railC" ~ ri), {
                    "corner1" : vector(left + t,  y0, railZ[2]),
                    "corner2" : vector(right - t, y1, railZ[3]) });

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

        // ── mains barrier: vertical divider + pocket top rail ───────────
        // The PSU sits in the bottom-right of the control band, boxed in by
        // the right wall, the bottom wall, a VERTICAL divider on its left and
        // a short horizontal rail across its top. Together those enclose it,
        // which is the point: every mains conductor stays inside that pocket,
        // and the knob cluster and its I2C wiring stay outside it.
        //
        // A vertical divider replaces the horizontal shelf of the previous
        // layout. Same job, and it falls out of clustering the knobs — the
        // band is now wide enough to share.

        const barZ0 = zBezB;                    // bezel back
        const barZ1 = zBack + t;                // back cover inner face
        const railTopY = -definition.apertureH / 2;
        const railBotY = railTopY - t;

        // vertical divider, tenoned into the bottom wall
        fCuboid(context, id + "divider", {
                "corner1" : vector(definition.dividerX - t / 2 - kerf / 2, bottom,   barZ0),
                "corner2" : vector(definition.dividerX + t / 2 + kerf / 2, railBotY, barZ1) });
        fCuboid(context, id + "dmort", {
                "corner1" : vector(definition.dividerX - t / 2 + kerf / 2, bottom - over,  barZ0 + kerf / 2),
                "corner2" : vector(definition.dividerX + t / 2 - kerf / 2, bottom + t - kerf / 2, barZ1 - kerf / 2) });
        opBoolean(context, id + "dmortCut", {
                "tools"         : qCreatedBy(id + "dmort", EntityType.BODY),
                "targets"       : qCreatedBy(id + "wallB", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });

        // pocket top rail, tenoned into the right wall
        fCuboid(context, id + "pocketRail", {
                "corner1" : vector(definition.dividerX, railBotY - kerf / 2, barZ0),
                "corner2" : vector(right,                railTopY + kerf / 2, barZ1) });
        fCuboid(context, id + "prmort", {
                "corner1" : vector(right - t - over, railBotY + kerf / 2, barZ0 + kerf / 2),
                "corner2" : vector(right + over,     railTopY - kerf / 2, barZ1 - kerf / 2) });
        opBoolean(context, id + "prmortCut", {
                "tools"         : qCreatedBy(id + "prmort", EntityType.BODY),
                "targets"       : qCreatedBy(id + "wallR", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION });

        // PSU mounting clearance through the BOTTOM wall. Its side-face holes
        // are 10 and 84 from one end of a 99mm case — 2.5mm off centre, so
        // these are not symmetric either. Screw path is 3mm wall + a
        // psuStandoff spacer + up to 5mm of thread, i.e. M3x12.
        var psuHoles = [];
        const psuX0 = definition.psuX - definition.psuL / 2;
        const psuHoleXs = [psuX0 + definition.psuHoleAX, psuX0 + definition.psuHoleBX];
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

        // ── IEC inlet, right wall, inside the mains compartment ─────────
        // Deliberately in the PSU compartment rather than the electronics bay,
        // so every mains conductor stays on one side of the shelf.

        var iecTools = [];

        fCuboid(context, id + "iecCut", {
                "corner1" : vector(right - t - over, definition.iecY - definition.iecCutW / 2 + kerf / 2,
                                                     definition.iecZ - definition.iecCutH / 2 + kerf / 2),
                "corner2" : vector(right + over,     definition.iecY + definition.iecCutW / 2 - kerf / 2,
                                                     definition.iecZ + definition.iecCutH / 2 - kerf / 2) });
        iecTools = append(iecTools, qCreatedBy(id + "iecCut", EntityType.BODY));

        // Flange screws, on the SHORT axis. That is what made the listing's
        // 40mm look impossible: 40mm cannot straddle the 46.75mm cutout, but
        // it straddles the 27.25mm one comfortably. The hole sits in the
        // triangular lobe, so the spacing is cutH + tip if it is at the
        // lobe's mid-height. Confirm by measuring hole centre to hole centre;
        // it is one variable either way.
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
        }

        opBoolean(context, id + "cut", {
                "tools"         : qUnion(tools),
                "targets"       : qUnion(plates),
                "operationType" : BooleanOperationType.SUBTRACTION });
    });
