// SPDX-License-Identifier: CC-BY-SA-4.0
// Pattern: 0614-2
// Author:  Seunghun LEE
// Lineage: AI generated and curated
// Ported for Patternflood from web/src/lib/presets/pattern-0614-2.ts (web-only upstream; not an upstream port)
//

#pragma once
#include <Arduino.h>
#include <math.h>
#include "../config.h"
#include "../src/core_display.h"
#include "../src/core_encoders.h"
#include "../src/core_canvas.h"
#include "../src/core_math.h"
#include "../src/core_params.h"

namespace Pattern06142 {
  const char* NAME = "0614-2";
  const char* const KNOB_LABELS[4] = {"Matrix Density", "Core Speed", "Fold Limit", "Color Mask"};
constexpr bool ABSOLUTE_READY = true;

  // Time terms t and 1.5t repeat together after 4π: the accumulator wraps there.
  constexpr float P06142_TIME_WRAP = 4.0f * (float)M_PI;

  struct Params {
    float rawKnob0 = 0.0f;
    float rawKnob1 = 2.0f;
    float rawKnob2 = 0.0f;
    float rawKnob3 = 0.06f;
    float timeAcc = 0.0f;
  };
  Params params;

  // fx depends only on x and fy only on y, so both cross terms are separable:
  // per-column / per-row factors, refreshed once a frame (sinf outside the
  // pixel loop).
  static float colA[PANEL_RES_W], colB[PANEL_RES_W];
  static float rowA[PANEL_RES_H], rowB[PANEL_RES_H];

// Pattern: 0614-2
// Author: Seunghun LEE
// SPDX-License-Identifier: CC-BY-SA-4.0
// Date: 2026-06-14
// Lineage: AI generated and curated
//
// Hyper-Dimensional Folded Cross Matrix
// Knob 1: Matrix Scale/Density (0.0 to 1.0)
// Knob 2: Translation Core Speed (0.1 to 10.0)
// Knob 3: Spatial Tiling Grid Fold Limit (0.0 to 4.9)
// Knob 4: Color Inversion Mask State (0.0 to 1.0)

void setup() {
    params.rawKnob0 = 0.0f;
    params.rawKnob1 = 2.0f;
    params.rawKnob2 = 0.0f;
    params.rawKnob3 = 0.06f;
    params.timeAcc = 0.0f;
  }

void update(float dt, const InputFrame& input) {
    PFParams::applyUnit(input, 0, &params.rawKnob0, 0.05f);
    PFParams::apply(input, 1, &params.rawKnob1, 0.1f, 10.0f, 0.1f);
    PFParams::apply(input, 2, &params.rawKnob2, 0.0f, 4.9f, 0.05f);
    PFParams::applyUnit(input, 3, &params.rawKnob3, 0.05f);

    // scale = knobValues[0], speed = [1], folds = [2], colorMask = [3]
    params.timeAcc += dt * params.rawKnob1;
    if (params.timeAcc >= P06142_TIME_WRAP) params.timeAcc -= P06142_TIME_WRAP;
  }

void draw() {
    const int w = PANEL_RES_W;
    const int h = PANEL_RES_H;
    const float t = params.timeAcc;

    const int fSize = 8 + (int)floorf(params.rawKnob0 * 24.0f);
    const int fPeriod = fSize * 2;
    const float foldLimit = params.rawKnob2;
    const bool maskLow = params.rawKnob3 < 0.5f;

    // Advanced coordinate mirror packing
    // crossA = sin(fx*0.2 + t) * cos(fy*0.2 - t)
    // crossB = cos(fx*0.1 - 1.5t) * sin(fy*0.1 + t)
    for (int x = 0; x < w; x++) {
        float fx = abs((x % fPeriod) - fSize) * foldLimit;
        colA[x] = sinf(fx * 0.2f + t);
        colB[x] = cosf(fx * 0.1f - t * 1.5f);
    }
    for (int y = 0; y < h; y++) {
        float fy = abs((y % fPeriod) - fSize) * foldLimit;
        rowA[y] = cosf(fy * 0.2f - t);
        rowB[y] = sinf(fy * 0.1f + t);
    }

    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            // Generate interlocking hard geometries inside folded matrix spaces
            float crossA = colA[x] * rowA[y];
            float crossB = colB[x] * rowB[y];

            float combined = fabsf(crossA + crossB);

            uint8_t r = 0, g = 0, b = 0;

            if (combined > 0.65f) {
                float edge = (combined - 0.65f) / 0.35f;

                // Absolute punchy neon fill colors
                if (maskLow) {
                    r = (uint8_t)floorf(255.0f * edge);
                    g = 0;
                    b = (uint8_t)floorf(120.0f + 135.0f * (1.0f - edge));
                } else {
                    r = 0;
                    g = (uint8_t)floorf(255.0f * edge);
                    b = (uint8_t)floorf(180.0f * edge);
                }

                // Sharp laser lines tracking intersections
                if (combined > 0.92f) {
                    r = 255; g = 255; b = 255;
                }
            } else if (combined < 0.08f) {
                // Sharp vector dots tracking inverse centers
                r = 255; g = 255; b = 0;
            }

            PFCanvas::setPixel(x, y, r, g, b);
        }
    }

    PFCanvas::present();
  }
} // namespace Pattern06142
