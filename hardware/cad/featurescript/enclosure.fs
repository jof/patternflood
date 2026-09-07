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
    }
    {
        const n = definition.count;
        const totalW = n * definition.panelW;

        for (var i = 0; i < n; i += 1)
        {
            const x0 = -totalW / 2 + i * definition.panelW;

            fCuboid(context, id + ("panel" ~ i), {
                    "corner1" : vector(x0, -definition.panelH / 2, -definition.panelDepth),
                    "corner2" : vector(x0 + definition.panelW, definition.panelH / 2, 0 * meter)
            });
        }
    });

// ────────────────────────────────────────────────────────────────────────
// Bezel
// ────────────────────────────────────────────────────────────────────────
// The doubled front face: display aperture, knob bores, and a control band
// below the display. One solid body per lamination, because each is a
// separate DXF and they are glued with grain crossed (basswood sheet is
// solid wood, not ply — cross-graining makes plywood exactly where the
// narrow rails around the aperture would otherwise split).
//
// There is no front retaining lip. Tiling LED panels have no bezel margin —
// 128 mm of pixels in a 128 mm module — so the panels cannot be held from
// the front and hang from cross-braces instead. The aperture is inset only
// ~0.5 mm, which clips the outer quarter-pixel and hides the module seam.

annotation { "Feature Type Name" : "Bezel" }
export const bezel = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Aperture width" }
        isLength(definition.apertureW, LENGTH_BOUNDS);

        annotation { "Name" : "Aperture height" }
        isLength(definition.apertureH, LENGTH_BOUNDS);

        annotation { "Name" : "Sheet thickness" }
        isLength(definition.thickness, LENGTH_BOUNDS);

        annotation { "Name" : "Laminations" }
        isInteger(definition.layers, POSITIVE_COUNT_BOUNDS);

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
    }
    {
        // Outer extents. The display aperture is centred on the origin, and
        // the control band hangs below it, so the bezel is NOT symmetric in y.
        const left   = -definition.apertureW / 2 - definition.marginSide;
        const right  =  definition.apertureW / 2 + definition.marginSide;
        const bottom = -definition.apertureH / 2 - definition.controlH;
        const top    =  definition.apertureH / 2 + definition.marginTop;
        const total  = definition.layers * definition.thickness;
        const over   = 1 * millimeter;   // tool overshoot, keeps cuts clean

        // One body per lamination, stacked forward out of the panel face.
        var plates = [];
        for (var i = 0; i < definition.layers; i += 1)
        {
            fCuboid(context, id + ("layer" ~ i), {
                    "corner1" : vector(left,  bottom, i * definition.thickness),
                    "corner2" : vector(right, top,   (i + 1) * definition.thickness)
            });
            plates = append(plates, qCreatedBy(id + ("layer" ~ i), EntityType.BODY));
        }

        // Cutting tools: the display aperture, then one bore per knob.
        var tools = [];

        fCuboid(context, id + "apTool", {
                "corner1" : vector(-definition.apertureW / 2, -definition.apertureH / 2, -over),
                "corner2" : vector( definition.apertureW / 2,  definition.apertureH / 2, total + over)
        });
        tools = append(tools, qCreatedBy(id + "apTool", EntityType.BODY));

        // Knobs sit centred in the control band, evenly spaced about x = 0.
        const knobY = -definition.apertureH / 2 - definition.controlH / 2;
        for (var i = 0; i < definition.knobCount; i += 1)
        {
            const knobX = (i - (definition.knobCount - 1) / 2) * definition.knobPitch;

            fCylinder(context, id + ("bore" ~ i), {
                    "topCenter"    : vector(knobX, knobY, total + over),
                    "bottomCenter" : vector(knobX, knobY, -over),
                    "radius"       : definition.boreDia / 2
            });
            tools = append(tools, qCreatedBy(id + ("bore" ~ i), EntityType.BODY));
        }

        opBoolean(context, id + "cut", {
                "tools"         : qUnion(tools),
                "targets"       : qUnion(plates),
                "operationType" : BooleanOperationType.SUBTRACTION
        });
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
// Box walls
// ────────────────────────────────────────────────────────────────────────
// Four walls forming a rectangular tube along z, finger-jointed to each
// other at the four vertical corners. The tube runs from the panel front
// face (z = 0) back to the electronics bay floor; the bezel caps the front
// and the back cover closes the rear.
//
// Left/right walls take phase 0 at every corner and top/bottom take phase
// 1, so the interlock alternates consistently the whole way round.

annotation { "Feature Type Name" : "Box walls" }
export const boxWalls = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Box width" }
        isLength(definition.boxW, LENGTH_BOUNDS);

        annotation { "Name" : "Box height" }
        isLength(definition.boxH, LENGTH_BOUNDS);

        annotation { "Name" : "Box y centre" }
        isLength(definition.boxYCentre, ANY_LENGTH_BOUNDS);

        annotation { "Name" : "Internal depth" }
        isLength(definition.depth, LENGTH_BOUNDS);

        annotation { "Name" : "Sheet thickness" }
        isLength(definition.thickness, LENGTH_BOUNDS);

        annotation { "Name" : "Target finger length" }
        isLength(definition.fingerLen, LENGTH_BOUNDS);

        annotation { "Name" : "Kerf" }
        isLength(definition.kerf, KERF_BOUNDS);
    }
    {
        const t      = definition.thickness;
        const left   = -definition.boxW / 2;
        const right  =  definition.boxW / 2;
        const bottom = definition.boxYCentre - definition.boxH / 2;
        const top    = definition.boxYCentre + definition.boxH / 2;
        const zFront = 0 * meter;
        const zBack  = -definition.depth;

        const n = fingerCount(definition.depth, definition.fingerLen);

        // Left/right span the full height; top/bottom span the full width.
        // They overlap at the four corners, which the joints then resolve.
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
                       ranges, 2, n, 0, definition.kerf);
            cutFingers(context, id + ("ch" ~ ci), qCreatedBy(id + c.horz, EntityType.BODY),
                       ranges, 2, n, 1, definition.kerf);
        }
    });
