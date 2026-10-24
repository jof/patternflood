// SPDX-License-Identifier: CC-BY-SA-4.0
// Pattern: 0530
// Author:  Seunghun LEE
// Lineage: AI generated and curated
// Ported for Patternflood from web/src/lib/presets/pattern-0530.ts (web-only upstream; not an upstream port)
//
// Variation 5: Psychedelic Liquid Phase
// Over time, the color wheel rotates as a whole, creating a psychedelic liquid water surface.
// Knob 1: Multi-Wave Distortion (0.0 to 1.0) -> complexity of multi-wave distortion for flowing lines
// Knob 2: Spectrum Rotation Velocity (0.1 to 10.0) -> speed of spectrum cycling and rotation
// Knob 3: Sharpness Blackout Gate (0.0 to 4.9) -> contrast falloff threshold around light rays
// Knob 4: Spatial Phase Distance (0.0 to 1.0) -> spatial prism distance splitting colors based on position

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

namespace Pattern0530 {
  const char* NAME = "0530";
  const char* const KNOB_LABELS[4] = {"Distortion", "Spectrum Spd", "Gate", "Prism Phase"};
  constexpr bool ABSOLUTE_READY = true;

  // Time multipliers 1, 0.8 and 0.6 all complete whole turns over 10π.
  constexpr float P0530_T_PERIOD = 10.0f * (float)M_PI;

  // Raw knob state, at the web's default ranges and starting values.
  static float rawKnob0 = 0.0f;   // distortion  0..1 (wraps)
  static float rawKnob1 = 2.0f;   // speed       0.1..10
  static float rawKnob2 = 0.0f;   // gate        0..4.9
  static float rawKnob3 = 0.06f;  // prism       0..1 (wraps)
  static float timeAcc = 0.0f;
  static float hueAcc = 0.0f;     // t * 0.25, kept as its own fract()ed accumulator
  static float powLUT[256];       // (i/255)^0.6
  static float colYOff[PANEL_RES_W];

  void setup() {
    PFMath::buildSinLUT();
    PFColor::buildPowLUTf(0.6f, powLUT);
    rawKnob0 = 0.0f;
    rawKnob1 = 2.0f;
    rawKnob2 = 0.0f;
    rawKnob3 = 0.06f;
    timeAcc = 0.0f;
    hueAcc = 0.0f;
  }

  void update(float dt, const InputFrame& input) {
    PFParams::applyUnit(input, 0, &rawKnob0, 0.05f);
    PFParams::apply(input, 1, &rawKnob1, 0.1f, 10.0f, 0.1f);
    PFParams::apply(input, 2, &rawKnob2, 0.0f, 4.9f, 0.05f);
    PFParams::applyUnit(input, 3, &rawKnob3, 0.05f);
    const float step = dt * rawKnob1 * 0.4f;
    timeAcc += step;
    if (timeAcc > P0530_T_PERIOD) timeAcc -= P0530_T_PERIOD;
    hueAcc = PFMath::fract(hueAcc + step * 0.25f);
  }

  void draw() {
    const int w = PANEL_RES_W;
    const int h = PANEL_RES_H;
    const float t = timeAcc;
    const float warp = 1.0f + rawKnob0 * 5.0f;
    const float gate = 0.35f + (rawKnob2 / 4.9f) * 0.7f;
    const float invRange = 1.0f / (1.0f - gate);
    const float spatialPhase = rawKnob3 * 0.4f;
    const float sx = 4.0f / (float)w;
    const float sy = 4.0f / (float)h;
    const float t08 = t * 0.8f;
    const float t06 = t * 0.6f;

    // yOff depends only on the column.
    for (int x = 0; x < w; x++) colYOff[x] = PFMath::fastCos((float)x * sx - t08) * warp;

    for (int y = 0; y < h; y++) {
      const float ny = (float)y * sy;
      const float xOff = PFMath::fastSin(ny + t) * warp;
      for (int x = 0; x < w; x++) {
        const float nx = (float)x * sx;

        const float f1 = PFMath::fastSin(nx + xOff + t);
        const float f2 = PFMath::fastCos(ny + colYOff[x] - t06);
        const float field = 1.0f - sqrtf(fabsf(f1 * f2)) - gate;
        if (field <= 0.0f) {
          PFCanvas::setPixel(x, y, 0, 0, 0);
          continue;
        }

        const float core = field * invRange;

        // Psychedelic wheel where the hue axis rotates over time and splits based on spatial coordinates
        const float hue = hueAcc + (nx - ny) * spatialPhase + core * 0.05f;
        const float val = powLUT[(int)(core * 255.0f + 0.5f)];

        uint8_t r, g, b;
        PFColor::hsvToRgb(hue, 1.0f, val, r, g, b);
        PFCanvas::setPixel(x, y, r, g, b);
      }
    }

    PFCanvas::present();
  }
} // namespace Pattern0530
