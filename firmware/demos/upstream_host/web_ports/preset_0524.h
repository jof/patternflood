// SPDX-License-Identifier: CC-BY-SA-4.0
// Pattern: 0524
// Author:  Seunghun LEE
// Lineage: AI generated and curated
// Ported for Patternflood from web/src/lib/presets/pattern-0524.ts (web-only upstream; not an upstream port)
//
// Layered fluid dynamic vorticity field.
//
// Layered Vorticity Field
// Break the fixed grid completely, simulating multiple fluid vortex center points
// pushing and pulling space non-linearly to simulate mixed paint structure.
//
// Knob 1 (0.0 to 1.0): Swirl Radius
// Knob 2 (0.1 to 10.0): Flow Speed
// Knob 3 (0.0 to 4.9): Vortex Count
// Knob 4 (0.0 to 1.0): Color Phase Spread

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

namespace Pattern0524 {
  const char* NAME = "0524";
  const char* const KNOB_LABELS[4] = {"Swirl Radius", "Flow Speed", "Vortex Count", "Color Spread"};
  constexpr bool ABSOLUTE_READY = true;

  // 1 + floor(4.9) vortex cores at most.
  constexpr int P0524_MAX_VORTICES = 5;
  // Every multiplier of t is a multiple of 0.1 (0.8 + 0.3 i, 0.6 + 0.4 i, 1),
  // so the whole field is periodic over 20π.
  constexpr float P0524_T_PERIOD = 20.0f * (float)M_PI;

  struct Params {
    // Raw knob state, at the web's default ranges and starting values.
    float rawKnob0 = 0.0f;   // [0, 1], wraps
    float rawKnob1 = 2.0f;   // [0.1, 10]
    float rawKnob2 = 0.0f;   // [0, 4.9]
    float rawKnob3 = 0.06f;  // [0, 1], wraps
    float radius = 0.5f;
    float speed = 1.0f;
    float vortices = 2.0f;
    float colorSpread = 0.5f;
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

    params.radius = params.rawKnob0;
    params.speed = params.rawKnob1;
    params.vortices = params.rawKnob2;
    params.colorSpread = params.rawKnob3;

    params.timeAcc += dt * params.speed * 0.5f;
    if (params.timeAcc > P0524_T_PERIOD) params.timeAcc -= P0524_T_PERIOD;
  }

  void draw() {
    const int w = PANEL_RES_W;
    const int h = PANEL_RES_H;
    const float t = params.timeAcc;
    const float radius = params.radius;
    const float colorSpread = params.colorSpread;

    // The moving vortex cores depend only on time: once per frame.
    int maxV = 1 + (int)floorf(params.vortices);
    if (maxV > P0524_MAX_VORTICES) maxV = P0524_MAX_VORTICES;
    float coreX[P0524_MAX_VORTICES], coreY[P0524_MAX_VORTICES];
    for (int i = 0; i < maxV; i++) {
      coreX[i] = 0.5f * sinf(t * (0.8f + i * 0.3f) + i * 1.5f);
      coreY[i] = 0.3f * cosf(t * (0.6f + i * 0.4f) + i * 2.0f);
    }

    const float aspect = (float)w / (float)h;
    for (int y = 0; y < h; y++) {
      const float ny = ((float)y / h) * 2.0f - 1.0f;
      for (int x = 0; x < w; x++) {
        const float nx = (((float)x / w) * 2.0f - 1.0f) * aspect;

        float wx = nx;
        float wy = ny;

        // Fluid dynamic coordinate distortion of moving vortex cores
        // (no distortion at all when the swirl radius is 0)
        if (radius != 0.0f) {
          for (int i = 0; i < maxV; i++) {
            const float cx = coreX[i];
            const float cy = coreY[i];
            const float dx = wx - cx;
            const float dy = wy - cy;
            const float dist = sqrtf(dx * dx + dy * dy) + 0.1f;

            const float swirl = PFMath::fastSin(dist * 3.0f - t) * radius / dist;
            const float cosS = PFMath::fastCos(swirl);
            const float sinS = PFMath::fastSin(swirl);

            wx = dx * cosS - dy * sinS + cx;
            wy = dx * sinS + dy * cosS + cy;
          }
        }

        // Calculate fluid signal based on distorted space
        const float fluidSignal = PFMath::fastSin(wx * 4.0f) * PFMath::fastCos(wy * 4.0f)
                                + PFMath::fastSin(wx * 2.0f + t);
        const float normalized = (fluidSignal + 2.0f) / 4.0f;

        uint8_t r = 0, g = 0, b = 0;

        // Local color mapping according to flowing density
        if (normalized > 0.1f) {
          const float localHue = 0.6f + normalized * 0.3f + colorSpread * PFMath::fastSin(wx * wy + t);
          const float brightness = fminf(1.0f, normalized * 1.5f);
          const float saturation = 0.9f - (1.0f - brightness) * 0.4f;

          PFColor::hsvToRgb(localHue, saturation, brightness, r, g, b);

          // Insert intense white highlights at fluid peak points
          if (normalized > 0.75f) {
            r = r > 105 ? 255 : (uint8_t)(r + 150);
            g = g > 105 ? 255 : (uint8_t)(g + 150);
            b = 255;  // min(255, b + 255)
          }
        }

        PFCanvas::setPixel(x, y, r, g, b);
      }
    }

    PFCanvas::present();
  }
} // namespace Pattern0524
