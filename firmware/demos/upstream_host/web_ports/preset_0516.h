// SPDX-License-Identifier: CC-BY-SA-4.0
// Pattern: 0516
// Author:  Seunghun LEE
// Lineage: AI generated and curated
// Ported for Patternflood from web/src/lib/presets/pattern-0516.ts (web-only upstream; not an upstream port)
//
// Color bands pattern.
//
// Controls:
// Knob 1 (Normalized): Ribbon Base Hue
// Knob 2 (Value): Oscillation Speed
// Knob 3 (Normalized): Number of Ribbons (Density)
// Knob 4 (Normalized): Amplitude/Height Spread

#pragma once
#include <Arduino.h>
#include <math.h>
#include "../config.h"
#include "../src/core_display.h"
#include "../src/core_encoders.h"
#include "../src/core_canvas.h"
#include "../src/core_math.h"
#include "../src/core_color.h"
#include "../src/core_params.h"

namespace Pattern0516 {
  const char* NAME = "0516";
  const char* const KNOB_LABELS[4] = {"Hue", "Speed", "Ribbons", "Amplitude"};
  constexpr bool ABSOLUTE_READY = true;

  // The JS reads at most floor(2 + 1 * 8) = 10 ribbons.
  constexpr int P0516_MAX_RIBBONS = 10;
  // t feeds sin(.. + t) and cos(.. - 0.8 t): both are periodic over 10π.
  constexpr float P0516_T_PERIOD = 10.0f * (float)M_PI;

  struct Params {
    // Raw knob state, at the web's default ranges and starting values.
    float rawKnob0 = 0.0f;   // [0, 1], wraps
    float rawKnob1 = 2.0f;   // [0.1, 10]
    float rawKnob2 = 0.0f;   // [0, 4.9]
    float rawKnob3 = 0.06f;  // [0, 1], wraps
    float hue = 0.5f;
    float speed = 1.0f;
    float ribbons = 0.5f;
    float amplitude = 0.5f;
    float timeAcc = 0.0f;
  };
  Params params;

  void setup() {
    PFMath::buildSinLUT();
    params = Params();
  }

  void update(float dt, const InputFrame& input) {
    PFParams::applyUnit(input, 0, &params.rawKnob0, 0.05f);
    PFParams::apply(input, 1, &params.rawKnob1, 0.1f, 10.0f, 0.1f);
    PFParams::apply(input, 2, &params.rawKnob2, 0.0f, 4.9f, 0.05f);
    PFParams::applyUnit(input, 3, &params.rawKnob3, 0.05f);

    params.hue = params.rawKnob0;                            // knobNormalized[0]
    params.speed = params.rawKnob1 != 0.0f ? params.rawKnob1 : 1.0f;  // knobValues[1] || 1.0
    params.ribbons = params.rawKnob2 / 4.9f;                 // knobNormalized[2]
    params.amplitude = params.rawKnob3;                      // knobNormalized[3]

    params.timeAcc += dt * params.speed * 2.0f;
    if (params.timeAcc > P0516_T_PERIOD) params.timeAcc -= P0516_T_PERIOD;
  }

  void draw() {
    const int w = PANEL_RES_W;
    const int h = PANEL_RES_H;
    const float t = params.timeAcc;

    int numRibbons = (int)floorf(2.0f + params.ribbons * 8.0f);
    if (numRibbons > P0516_MAX_RIBBONS) numRibbons = P0516_MAX_RIBBONS;
    const float amp = 5.0f + params.amplitude * (h / 2.0f - 5.0f);
    const float s = 0.05f;
    const float midY = h / 2.0f;

    // Each ribbon's centre depends only on the column, so do the trig once per
    // column rather than once per pixel.
    float centerY[P0516_MAX_RIBBONS];
    float ribbonHue[P0516_MAX_RIBBONS];
    for (int i = 0; i < numRibbons; i++) ribbonHue[i] = params.hue + i * 0.1f;

    for (int x = 0; x < w; x++) {
      const float nx = x * s;
      for (int i = 0; i < numRibbons; i++) {
        const float phaseOffset = i * 1.337f;
        // 1D plasma slice moving through time
        const float v1 = PFMath::fastSin(nx + t + phaseOffset);
        const float v2 = PFMath::fastCos(nx * 1.5f - t * 0.8f + phaseOffset);
        centerY[i] = midY + (v1 + v2) * amp;
      }

      for (int y = 0; y < h; y++) {
        float totalGlow = 0.0f;
        float sumHue = 0.0f;

        // Render multiple overlapping ribbons
        for (int i = 0; i < numRibbons; i++) {
          // Distance from current pixel Y to ribbon center
          const float dist = fabsf(y - centerY[i]);
          // Additive glow logic
          if (dist < 4.0f) {
            float glow = 1.0f / (dist + 1.0f);  // Inverse distance falloff
            glow = glow * sqrtf(glow);          // pow(glow, 1.5)
            totalGlow += glow;
            // Mix hue based on ribbon index
            sumHue += ribbonHue[i];
          }
        }

        uint8_t r = 0, g = 0, b = 0;
        if (totalGlow > 0.1f) {
          const float avgHue = PFMath::jsMod(sumHue / fmaxf(1.0f, ceilf(totalGlow)), 1.0f);
          const float val = fminf(1.0f, totalGlow * 0.8f);
          PFColor::hsvToRgb(avgHue, 1.0f - val * 0.3f, val, r, g, b);
        }
        PFCanvas::setPixel(x, y, r, g, b);
      }
    }

    PFCanvas::present();
  }
} // namespace Pattern0516
