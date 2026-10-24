// SPDX-License-Identifier: CC-BY-SA-4.0
// Pattern: 0622
// Author:  Seunghun LEE
// Lineage: AI generated and curated
// Ported for Patternflood from web/src/lib/presets/pattern-0622.ts (web-only upstream; not an upstream port)
//
// Domain Remix: Hyperbolic Mirror Grid
// Applies a dividing grid coordinate division that multiplies inwards toward the screen boundaries.
// Knob 1: Boundary Scaling Factor (0..1)
// Knob 2: Animation Speed (0.1..10.0) [Clamped, No Wrap]
// Knob 3: Sub-division Complexity Grid (0.0..4.9) [Clamped, No Wrap]
// Knob 4: Primary Color Domain Map (0..1)

#pragma once
#include <Arduino.h>
#include <math.h>
#include "../config.h"
#include "../src/core_display.h"
#include "../src/core_encoders.h"
#include "../src/core_canvas.h"
#include "../src/core_math.h"
#include "../src/core_params.h"

namespace Pattern0622 {
  const char* NAME = "0622";
  const char* const KNOB_LABELS[4] = {"Boundary", "Speed", "Subdivision", "Color Map"};
  constexpr bool ABSOLUTE_READY = true;

  // Raw knob state at the web's default ranges and starting values. The JS
  // reads input.knobValues directly, so these are used as-is.
  static float rawKnob0 = 0.0f;   // boundary 0..1 (wraps)
  static float rawKnob1 = 2.0f;   // speed    0.1..10
  static float rawKnob2 = 0.0f;   // subdiv   0..4.9
  static float rawKnob3 = 0.06f;  // colorMap 0..1 (wraps)
  static float timeAcc = 0.0f;

  // Per-column grid index: depends only on x, the width and the knobs, so it
  // is filled once per frame instead of once per pixel.
  static int colGrid[PANEL_RES_W];

  void setup() {
    PFMath::buildSinLUT();
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
    timeAcc += dt * rawKnob1;
    // t only reaches sin() with a multiplier of 1, so wrap at 2π.
    if (timeAcc > TWO_PI) timeAcc -= TWO_PI;
  }

  void draw() {
    const int w = PANEL_RES_W;
    const int h = PANEL_RES_H;
    const float t = timeAcc;
    const float boundary = rawKnob0;
    const float colorMap = rawKnob3;

    const float divFactor = 1.0f + rawKnob2 * 2.0f;
    const float warp = boundary * 0.9f;

    for (int x = 0; x < w; x++) {
      const float nx = (x - w / 2.0f) / (w / 2.0f);
      const float wx = nx / (1.001f - fabsf(nx) * warp);
      colGrid[x] = (int)floorf((wx + 2.0f) * divFactor);
    }

    // Colors that depend only on the knobs.
    const uint8_t cr = (uint8_t)(40.0f + colorMap * 180.0f);
    const uint8_t cb = (uint8_t)(20.0f + (1.0f - colorMap) * 200.0f);

    for (int y = 0; y < h; y++) {
      // Warp coordinates non-linearly outward from center
      const float ny = (y - h / 2.0f) / (h / 2.0f);
      const float wy = ny / (1.001f - fabsf(ny) * warp);
      const int gridY = (int)floorf((wy + 2.0f) * divFactor);
      const float rowPhase = gridY * 1.2f + t;

      for (int x = 0; x < w; x++) {
        const int gridX = colGrid[x];

        const float wave = PFMath::fastSin(gridX * 1.5f + rowPhase);
        const float sig = (wave + 1.0f) * 0.5f;

        uint8_t r = 0, g = 0, b = 0;

        if (sig > 0.7f) {
          r = 255; g = 255; b = 255;
        } else if (((gridX + gridY) % 2 == 0) && sig > 0.3f) {
          r = cr;
          g = (uint8_t)(200.0f * sig);
          b = cb;
        } else if (sig > 0.45f) {
          r = 30; g = 40; b = 100;
        }

        PFCanvas::setPixel(x, y, r, g, b);
      }
    }

    PFCanvas::present();
  }
} // namespace Pattern0622
