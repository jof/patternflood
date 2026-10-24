// SPDX-License-Identifier: CC-BY-SA-4.0
// Pattern: 0519-2
// Author:  Seunghun LEE
// Lineage: AI generated and curated
// Ported for Patternflood from web/src/lib/presets/pattern-0519-2.ts (web-only upstream; not an upstream port)
//
// Glitch typography on matrix grid.
//
// Knobs for Glitch Typography:
// Knob 1: Glitch Preset (10 distinct modes: 0.0=Clean to 1.0=Meltdown)
// Knob 2: Overall Pattern Speed (Animation speed of background, 0.1 - 10.0)
// Knob 3: Motif Density (Scale of the underlying shapes, 0.0 - 4.9)
// Knob 4: Chromatic Aberration (RGB channel splitting width, 0.0 - 1.0)

#pragma once
#include <Arduino.h>
#include <math.h>
#include "../config.h"
#include "../src/core_display.h"
#include "../src/core_encoders.h"
#include "../src/core_canvas.h"
#include "../src/core_params.h"

namespace Pattern05192 {
  const char* NAME = "0519-2";
  const char* const KNOB_LABELS[4] = {"Glitch Mode", "Speed", "Density", "Aberration"};
  constexpr bool ABSOLUTE_READY = true;

  // patternTime only feeds sin(0.5 t + ..), and glitchTime only feeds sines
  // with integer multipliers or 1.5: both are periodic over 4π.
  constexpr float P05192_T_PERIOD = 4.0f * (float)M_PI;

  struct Params {
    // Raw knob state, at the web's default ranges and starting values.
    float rawKnob0 = 0.0f;   // [0, 1], wraps
    float rawKnob1 = 2.0f;   // [0.1, 10]
    float rawKnob2 = 0.0f;   // [0, 4.9]
    float rawKnob3 = 0.06f;  // [0, 1], wraps
    double patternTime = 0.0;  // host port: double/sin-hash kept for fidelity to the JS; not ESP32-friendly
    double glitchTime = 0.0;
    int glitchPreset = 4;
    int cellSize = 12;
    double aberration = 5.0;
  };
  Params params;

  // The base "typography" pattern at a coordinate (x may be fractional or
  // negative: the aberration and glitch offsets shift it).
  //
  // host port: double/sin-hash kept for fidelity to the JS; not ESP32-friendly.
  // When the aberration shift lands a sample exactly on a cross-arm edge
  // (|lx| == cellSize * 0.1, e.g. at the default 0.6 aberration and 6 px
  // cells), the JS decides the tie by double rounding; float decides it
  // differently and whole 1 px columns flip.
  inline bool getShapeAt(double x, int y, double cellSize, double patternT) {
    const double gx = floor(x / cellSize);
    const double gy = floor(y / cellSize);
    const double lx = fmod(x, cellSize) - cellSize * 0.5;  // fmod has JS %'s sign rule
    const double ly = fmod((double)y, cellSize) - cellSize * 0.5;

    const double offset = gx * 11.3 + gy * 5.7;
    const double shapeAnim = sin(patternT * 0.5 + offset);

    const double boxD = fmax(fabs(lx), fabs(ly)) - cellSize * 0.4;
    const double cross = fmin(fabs(lx), fabs(ly)) - cellSize * 0.1;

    const double val = fmax(boxD, -cross * shapeAnim);
    return val < 0.0;
  }

  void setup() {
    params = Params();
  }

  void update(float dt, const InputFrame& input) {
    PFParams::applyUnit(input, 0, &params.rawKnob0, 0.05f);
    PFParams::apply(input, 1, &params.rawKnob1, 0.1f, 10.0f, 0.1f);
    PFParams::apply(input, 2, &params.rawKnob2, 0.0f, 4.9f, 0.05f);
    PFParams::applyUnit(input, 3, &params.rawKnob3, 0.05f);

    const double speed = params.rawKnob1;
    params.patternTime += (double)dt * speed;
    if (params.patternTime > P05192_T_PERIOD) params.patternTime -= P05192_T_PERIOD;
    params.glitchTime += (double)dt * 2.0;
    if (params.glitchTime > P05192_T_PERIOD) params.glitchTime -= P05192_T_PERIOD;

    // Convert 0.0-1.0 (knobNormalized[0]) into exactly 10 discrete states: 0 to 9
    params.glitchPreset = (int)floorf(params.rawKnob0 * 9.99f);

    const float densityRatio = params.rawKnob2 / 4.9f;
    params.cellSize = (int)floorf(6.0f + densityRatio * 14.0f);

    // Knob state is float (PFParams): snap it to 1e-4 in double so 0.06f
    // reads as the JS's 0.06 and edge ties resolve the same way.
    params.aberration = round((double)params.rawKnob3 * 1e4) / 1e4 * 10.0;
  }

  void draw() {
    const int w = PANEL_RES_W;
    const int h = PANEL_RES_H;

    const double pTime = params.patternTime;
    const float gTime = (float)params.glitchTime;
    const int preset = params.glitchPreset;
    const double cellSize = params.cellSize;

    for (int y = 0; y < h; y++) {
      bool isGlitched = false;
      int xOffset = 0;
      bool showFlash = false;
      float abMult = 1.0f;  // Local multiplier for chromatic aberration

      // 10-stage glitch rules. These run once per row, so they use full sinf:
      // several are near-hash row selectors (y * 84.1, y * 154.3) where the
      // sin LUT's error would pick different rows.
      switch (preset) {
        case 1:  // Gentle VHS
          if (sinf(y * 0.05f - gTime * 3.0f) > 0.98f) {
            isGlitched = true; xOffset = (int)floorf(sinf(y * 0.1f) * 6.0f);
          }
          break;
        case 2:  // Interlace Tear
          if (sinf(y * 77.0f + gTime * 2.0f) > 0.9f) {
            isGlitched = true; xOffset = (y % 2 == 0) ? 5 : -5;
          }
          break;
        case 3: {  // Macroblock
          const float bY3 = floorf(y / 6.0f);
          const float n3 = sinf(bY3 * 12.3f - gTime * 4.0f);
          if (n3 > 0.7f) {
            isGlitched = true; xOffset = (int)floorf(sinf(bY3 * 3.3f + gTime * 10.0f) * 12.0f);
            if (n3 > 0.95f) showFlash = true;
          }
          break;
        }
        case 4:  // Scanline Drops
          if (sinf(y * 84.1f + gTime * 5.0f) > 0.85f) {
            isGlitched = true; xOffset = (int)floorf(sinf(y * 99.9f + gTime * 20.0f) * 20.0f);
          }
          break;
        case 5:  // Wavy Warp
          isGlitched = true;
          xOffset = (int)floorf(sinf(y * 0.15f + gTime * 4.0f) * 4.0f);
          break;
        case 6:  // Chromatic Pulse
          if (sinf(y * 0.08f - gTime * 6.0f) > 0.9f) {
            isGlitched = true; abMult = 4.0f; xOffset = (y % 3 == 0) ? 3 : -3;
          }
          break;
        case 7: {  // Data Mosh
          const float bY7 = floorf(y / 16.0f);
          if (sinf(bY7 * 4.1f - gTime * 1.5f) > 0.5f) {
            isGlitched = true; xOffset = (int)floorf(sinf(bY7 * 9.1f + gTime * 10.0f) * 25.0f);
          }
          break;
        }
        case 8:  // High Freq Buzz
          if (sinf(y * 154.3f + gTime * 15.0f) > 0.0f) {
            isGlitched = true; xOffset = (int)floorf(sinf(y * 34.2f + gTime * 30.0f) * 3.0f);
          }
          break;
        case 9: {  // Total Meltdown
          const float n91 = sinf(y * 84.1f + gTime * 5.0f);
          const float n92 = cosf(floorf(y / 4.0f) * 13.3f - gTime * 8.0f);
          const float c9 = (n91 + n92) * 0.5f;
          if (c9 > 0.2f) {
            isGlitched = true; xOffset = (int)floorf(sinf(y * 99.9f + gTime * 25.0f) * 30.0f);
            abMult = 2.5f;
            if (c9 > 0.7f) showFlash = true;
          }
          break;
        }
        default:  // 0: Clean
          break;
      }
      (void)isGlitched;  // the JS sets it but never reads it

      const double currentAberration = params.aberration * abMult;

      for (int x = 0; x < w; x++) {
        uint8_t r = 0, g = 0, b = 0;

        const double gxPos = (double)(x + xOffset);
        const bool redHit = getShapeAt(gxPos - currentAberration, y, cellSize, pTime);
        const bool greenHit = getShapeAt(gxPos, y, cellSize, pTime);
        const bool blueHit = getShapeAt(gxPos + currentAberration, y, cellSize, pTime);

        if (redHit) r = 255;
        if (greenHit) g = 255;
        if (blueHit) b = 255;

        // Bright flash for heavy presets
        if (showFlash && !redHit && !greenHit && !blueHit) {
          r = 60; g = 60; b = 60;
        }

        PFCanvas::setPixel(x, y, r, g, b);
      }
    }

    PFCanvas::present();
  }
} // namespace Pattern05192
