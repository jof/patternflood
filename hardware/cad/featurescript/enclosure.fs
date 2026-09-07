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
