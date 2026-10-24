// SPDX-License-Identifier: CC-BY-SA-4.0
// Pattern: 0529
// Author:  Seunghun LEE
// Lineage: AI generated and curated
// Ported for Patternflood from web/src/lib/presets/pattern-0529.ts (web-only upstream; not an upstream port)
//
// Contrast Remix: sparse, hard-edged topographic contour lines on near-black — inverse of the dense soft seed.
// (Only level-set lines of a morphing field glow; everything between stays dark and mechanical.)
// Knob 1: Field flow rotation (wraps, 0..2PI)
// Knob 2: Morph speed (0.1 - 10.0)
// Knob 3: Contour density (0.0 - 4.9 -> more, tighter rings)
// Knob 4: Line thickness / softness (wraps, thin & hard -> thicker)

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

namespace Pattern0529 {
  const char* NAME = "0529";
  const char* const KNOB_LABELS[4] = {"Rotation", "Morph Speed", "Density", "Thickness"};
  constexpr bool ABSOLUTE_READY = true;

  // Time multipliers 1 and 0.8 both complete whole turns over 10π.
  constexpr float P0529_T_PERIOD = 10.0f * (float)M_PI;

  // Raw knob state, at the web's default ranges and starting values.
  static float rawKnob0 = 0.0f;   // rotation   0..1 (wraps)
  static float rawKnob1 = 2.0f;   // speed      0.1..10
  static float rawKnob2 = 0.0f;   // density    0..4.9
  static float rawKnob3 = 0.06f;  // thickness  0..1 (wraps)
  static float timeAcc = 0.0f;
  static float powLUT[256];       // (i/255)^0.6

  void setup() {
    PFMath::buildSinLUT();
    PFColor::buildPowLUTf(0.6f, powLUT);
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
    timeAcc += dt * rawKnob1 * 0.4f;
    if (timeAcc > P0529_T_PERIOD) timeAcc -= P0529_T_PERIOD;
  }

  void draw() {
    const int w = PANEL_RES_W;
    const int h = PANEL_RES_H;
    const float cx = w * 0.5f, cy = h * 0.5f;
    const float t = timeAcc;
    const float rot = rawKnob0 * (float)M_PI * 2.0f;
    const float ca = cosf(rot), sa = sinf(rot);
    const float levels = 3.0f + rawKnob2 * 5.0f;
    const float thick = 0.04f + rawKnob3 * 0.22f;
    const float invThick = 1.0f / thick;
    // Phases for the three field terms. Each is shifted by whole turns so
    // every argument stays positive (fastSin then truncates the same way
    // everywhere), plus half a LUT bucket so that truncation rounds to the
    // nearest entry: the contour test amplifies the LUT's half-bucket bias.
    const float halfBucket = (float)M_PI / (float)PFMath::SIN_LUT_SIZE;
    const float ph1 = t + 2.0f * (float)M_PI + halfBucket;               // |rx * 6| < 2π
    const float ph2 = -t * 0.8f + 10.0f * (float)M_PI + halfBucket;      // t * 0.8 < 8π, |ry * 5| < 2π
    const float ph3 = sinf(t) * 2.0f + 4.0f * (float)M_PI + halfBucket;  // |(rx + ry) * 4| + 2 < 4π
    const float invW = 1.0f / (float)w;
    const float invH = 1.0f / (float)h;

    for (int y = 0; y < h; y++) {
      const float oy = ((float)y - cy) * invH;
      for (int x = 0; x < w; x++) {
        const float ox = ((float)x - cx) * invW;
        const float rx = ox * ca - oy * sa;
        const float ry = ox * sa + oy * ca;
        const float field =
            PFMath::fastSin(rx * 6.0f + ph1) +
            PFMath::fastSin(ry * 5.0f + ph2) +
            PFMath::fastSin((rx + ry) * 4.0f + ph3);
        const float norm = field / 3.0f * 0.5f + 0.5f;
        const float lf = norm * levels;
        const float fl = floorf(lf);
        const float fpart = lf - fl;
        const float di = fminf(fpart, 1.0f - fpart);
        uint8_t r = 0, g = 0, b = 0;
        if (di < thick) {
          const float core = 1.0f - di * invThick;
          const float hue = 0.55f + fl * 0.09f;
          const float sat = 1.0f - core * 0.7f;
          const float val = powLUT[(int)(core * 255.0f + 0.5f)];
          PFColor::hsvToRgb(hue, sat, val, r, g, b);
        }
        PFCanvas::setPixel(x, y, r, g, b);
      }
    }

    PFCanvas::present();
  }
} // namespace Pattern0529
