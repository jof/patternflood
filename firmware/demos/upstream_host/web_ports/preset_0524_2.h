// SPDX-License-Identifier: CC-BY-SA-4.0
// Pattern: 0524-2
// Author:  Seunghun LEE
// Lineage: AI generated and curated
// Ported for Patternflood from web/src/lib/presets/pattern-0524-2.ts (web-only upstream; not an upstream port)
//
// Liquid Ripple Refraction
// Using virtual aspherical water droplet waves falling on the center and edges of the screen,
// refracts the entire 2D plane like a lens and creates ripples.
//
// Knob 1 (0.0 to 1.0): Refraction Depth
// Knob 2 (0.1 to 10.0): Ripple Speed
// Knob 3 (0.0 to 4.9): Ripple Wave Count
// Knob 4 (0.0 to 1.0): Specular Reflection

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

namespace Pattern05242 {
  const char* NAME = "0524-2";
  const char* const KNOB_LABELS[4] = {"Refraction", "Ripple Speed", "Wave Count", "Specular"};
  constexpr bool ABSOLUTE_READY = true;

  // Time multipliers 0.4, 1, 1.3 and 0.5 all complete whole turns over 20π.
  constexpr float P05242_T_PERIOD = 20.0f * (float)M_PI;

  // Raw knob state, at the web's default ranges and starting values.
  static float rawKnob0 = 0.0f;   // warp      0..1 (wraps)
  static float rawKnob1 = 2.0f;   // speed     0.1..10
  static float rawKnob2 = 0.0f;   // waves     0..4.9
  static float rawKnob3 = 0.06f;  // specular  0..1 (wraps)
  static float timeAcc = 0.0f;

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
    timeAcc += dt * rawKnob1 * 1.5f;
    if (timeAcc > P05242_T_PERIOD) timeAcc -= P05242_T_PERIOD;
  }

  void draw() {
    const int w = PANEL_RES_W;
    const int h = PANEL_RES_H;
    const float t = timeAcc;
    const float invW = 1.0f / (float)w;
    const float invH = 1.0f / (float)h;
    const float aspect = (float)w / (float)h;

    // Per-frame constants.
    const float c1x = 0.3f * sinf(t * 0.4f);
    const float waveFreq = 4.0f + rawKnob2 * 4.0f;
    const float waveFreq2 = waveFreq * 0.7f;
    const float t13 = t * 1.3f;
    const float t05 = t * 0.5f;
    const float t04 = t * 0.4f;
    const float warpFactor = rawKnob0 * 0.3f;
    const float specCos = cosf(rawKnob3 * (float)M_PI * 2.0f);
    const float specSin = sinf(rawKnob3 * (float)M_PI * 2.0f);

    for (int y = 0; y < h; y++) {
      const float ny = ((float)y * invH) * 2.0f - 1.0f;
      const float ny2 = ny * ny;
      const float dy2 = (ny - 0.2f) * (ny - 0.2f);
      for (int x = 0; x < w; x++) {
        const float nx = (((float)x * invW) * 2.0f - 1.0f) * aspect;

        // Calculate surface refraction field based on distance from wave centers
        const float ax = nx - c1x;
        const float d1 = sqrtf(ax * ax + ny2);
        const float bx = nx + 0.4f;
        const float d2 = sqrtf(bx * bx + dy2);

        const float rippleField = PFMath::fastSin(d1 * waveFreq - t) * 0.6f +
                                  PFMath::fastSin(d2 * waveFreq2 - t13) * 0.4f;

        // Induce refraction using gradient displacement of wave slopes
        const float wx = nx + rippleField * warpFactor;
        const float wy = ny + rippleField * warpFactor;

        // Sample bottom fluid base layer
        const float liquidBase = PFMath::fastSin(wx * 3.0f + t05) * PFMath::fastCos(wy * 3.0f - t04);
        const float nLiquid = (liquidBase + 1.0f) * 0.5f;

        // Calculate surface reflection highlights (specular vector)
        const float specularAngle = wx * specCos + wy * specSin;
        const float specTrigger = PFMath::fastSin(specularAngle * 8.0f + rippleField * 4.0f);

        const float hue = 0.5f + nLiquid * 0.25f + rippleField * 0.1f;
        const float sat = 0.95f - fmaxf(0.0f, specTrigger * 0.3f);  // Saturation decreases in specular reflection highlights
        const float val = 0.2f + nLiquid * 0.6f + fmaxf(0.0f, rippleField * 0.2f);

        uint8_t r, g, b;
        PFColor::hsvToRgb(hue, sat, val, r, g, b);

        // Ultra-bright specular sparkle effect on wave ridges
        if (specTrigger > 0.88f && rippleField > 0.2f) {
          r = (uint8_t)(r + 180 > 255 ? 255 : r + 180);
          g = (uint8_t)(g + 180 > 255 ? 255 : g + 180);
          b = 255;
        }

        PFCanvas::setPixel(x, y, r, g, b);
      }
    }

    PFCanvas::present();
  }
} // namespace Pattern05242
