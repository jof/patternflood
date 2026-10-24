// SPDX-License-Identifier: CC-BY-SA-4.0
// Pattern: 0526
// Author:  Seunghun LEE
// Lineage: AI generated and curated
// Ported for Patternflood from web/src/lib/presets/pattern-0526.ts (web-only upstream; not an upstream port)
//
// Kaleidoscopic Vortex Vortex
// Change: Imposes a multi-axis radial reflection fold onto coordinate spaces prior to applying fluid warp matrices.
// Knob 1: Reflection Segment Symmetry Fold Count
// Knob 2: System Animation Speed
// Knob 3: Polar Center Warp Core Depth
// Knob 4: Spiral Twist Distortion Index

#pragma once
#include <Arduino.h>
#include <math.h>
#include "../config.h"
#include "../src/core_display.h"
#include "../src/core_encoders.h"
#include "../src/core_canvas.h"
#include "../src/core_math.h"
#include "../src/core_tables.h"
#include "../src/core_params.h"

namespace Pattern0526 {
  const char* NAME = "0526";
  const char* const KNOB_LABELS[4] = {"Symmetry", "Speed", "Core Depth", "Twist"};
  constexpr bool ABSOLUTE_READY = true;

  // Raw knob state, at the web's default ranges and starting values.
  static float rawKnob0 = 0.0f;   // fold count  0..1 (wraps)
  static float rawKnob1 = 2.0f;   // speed       0.1..10
  static float rawKnob2 = 0.0f;   // core depth  0..4.9
  static float rawKnob3 = 0.06f;  // twist       0..1 (wraps)
  static float timeAcc = 0.0f;

  void setup() {
    PFMath::buildSinLUT();
    PFTables::init();
    rawKnob0 = 0.0f;
    rawKnob1 = 2.0f;
    rawKnob2 = 0.0f;
    rawKnob3 = 0.06f;
    timeAcc = 0.0f;
  }

  void update(float dt, const InputFrame& input) {
    PFParams::applyUnit(input, 0, &rawKnob0, 0.05f);
    PFParams::apply(input, 1, &rawKnob1, 0.1f, 10.0f, 0.1f);
    PFParams::apply(input, 2, &rawKnob2, 0.0f, 4.9f, 0.05f);
    PFParams::applyUnit(input, 3, &rawKnob3, 0.05f);
    // t only feeds sin/cos with integer multipliers.
    timeAcc += dt * rawKnob1 * 0.6f;
    if (timeAcc > TWO_PI) timeAcc -= TWO_PI;
  }

  void draw() {
    if (!PFTables::rT || !PFTables::thetaT) { PFCanvas::present(); return; }
    const float t = timeAcc;

    const int sectors = (int)floorf(3.0f + rawKnob0 * 9.0f);
    const float coreDepth = rawKnob2 * 1.5f;
    const float twistFactor = rawKnob3 * 3.0f;
    const float slice = ((float)M_PI * 2.0f) / (float)sectors;
    const float halfSlice = slice * 0.5f;
    const float forcePhase = 2.0f * (float)M_PI - t + (float)M_PI / (float)PFMath::SIN_LUT_SIZE;

    for (int y = 0; y < PANEL_RES_H; y++) {
      for (int x = 0; x < PANEL_RES_W; x++) {
        const int i = y * PANEL_RES_W + x;
        // JS coordinates are centred and in half-height units; rT is in
        // height units from the same centre, thetaT the same angle.
        const float radius = PFTables::rT[i] * 2.0f + 0.001f;
        float angle = PFTables::thetaT[i];

        // Execute Kaleidoscope coordinate segment replication folds
        angle = PFMath::jsMod(PFMath::jsMod(angle, slice) + slice, slice);
        if (angle > halfSlice) angle = slice - angle;

        // Return spatial domain safely back to Cartesian grid vectors
        const float kx = PFMath::fastCos(angle) * radius;
        const float ky = PFMath::fastSin(angle) * radius;

        // Subject the reflected space vectors to a heavy internal fluid spiral
        const float vx = kx - 0.2f;
        const float vortexDist = sqrtf(vx * vx + ky * ky) + 0.05f;
        // force multiplies the sine by up to coreDepth / 0.05, so the sin LUT's
        // truncation bias would show near the vortex: shift the argument by a
        // whole turn (it stays positive, as t < 2π) plus half a bucket, so the
        // lookup rounds to the nearest entry.
        const float force = PFMath::fastSin(vortexDist * twistFactor + forcePhase) * (coreDepth / vortexDist);

        const float cf = PFMath::fastCos(force);
        const float sf = PFMath::fastSin(force);
        const float wx = kx * cf - ky * sf;
        const float wy = kx * sf + ky * cf;

        // Re-sample geometry inside the mirrored/warped universe
        const float signal = PFMath::fastSin(wx * 6.0f + t) * PFMath::fastCos(wy * 6.0f - t);
        const float norm = fabsf(signal);

        uint8_t r = 0, g = 0, b = 0;

        if (norm > 0.15f) {
          // High-saturation crystalline color signatures reflecting distance and phase
          const float hue = 0.55f + radius * 0.2f + PFMath::fastCos(angle * 4.0f + t) * 0.15f;
          // br runs from below 0 (past radius 2.2) up to 1.1 (at the centre);
          // the web clamps each channel to 0..255.
          const float br = fminf(1.0f, norm * 1.6f) * (1.1f - radius * 0.5f);

          if (br > 0.0f) {
            r = (uint8_t)fminf(255.0f, floorf((PFMath::fastSin(hue * 6.28f) * 0.5f + 0.5f) * 255.0f * br));
            g = (uint8_t)fminf(255.0f, floorf((PFMath::fastSin(hue * 6.28f + 2.0f) * 0.5f + 0.5f) * 230.0f * br));
            b = (uint8_t)fminf(255.0f, floorf(255.0f * br));
          }

          // Outer bounds matrix containment ring
          if (fabsf(radius - 0.8f) < 0.02f) {
            r = 255; g = 255; b = 255;
          }
        }

        PFCanvas::setPixel(x, y, r, g, b);
      }
    }

    PFCanvas::present();
  }
} // namespace Pattern0526
