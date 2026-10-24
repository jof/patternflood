// SPDX-License-Identifier: CC-BY-SA-4.0
// Pattern: 0517
// Author:  Seunghun LEE
// Lineage: AI generated and curated
// Ported for Patternflood from web/src/lib/presets/pattern-0517.ts (web-only upstream; not an upstream port)
//
// Sweeping scan beams.
//
// Knob 1: Beam Thickness (Width of the sweeping scan)
// Knob 2: Rotation Speed (How fast the radar sweeps)
// Knob 3: Noise Turbulence (How much the sweep is distorted)
// Knob 4: Highlight Color (Hue of the leading edge)
//
// Host port: the JS's sin-hash value noise is kept literally, in double, so
// the turbulence field matches the web pixel for pixel. That is fine on x86
// and aarch64 hosts and too slow for an ESP32 (use PFNoise there).

#pragma once
#include <Arduino.h>
#include <math.h>
#include "../config.h"
#include "../src/core_display.h"
#include "../src/core_encoders.h"
#include "../src/core_canvas.h"
#include "../src/core_color.h"
#include "../src/core_tables.h"
#include "../src/core_params.h"

namespace Pattern0517 {
  const char* NAME = "0517";
  const char* const KNOB_LABELS[4] = {"Thickness", "Speed", "Turbulence", "Hue"};
  constexpr bool ABSOLUTE_READY = true;

  constexpr float P0517_TWO_PI = 6.28318530717958647692f;

  struct Params {
    // Raw knob state, at the web's default ranges and starting values.
    float rawKnob0 = 0.0f;   // [0, 1], wraps
    float rawKnob1 = 2.0f;   // [0.1, 10]
    float rawKnob2 = 0.0f;   // [0, 4.9]
    float rawKnob3 = 0.06f;  // [0, 1], wraps
    float thickness = 0.5f;
    float speed = 0.5f;
    float turbulence = 0.5f;
    float baseHue = 0.5f;
    // The JS keeps one timeAcc t and uses (t * 0.5) % 2π for the sweep and
    // t * 0.2 * 0.4 for the noise drift. The sweep wraps at 2π; the sin-hash
    // noise has no period, so its drift is a double that is left to run (in
    // double it stays precise for years of uptime).
    float sweepAngle = 0.0f;  // t * 0.5, wrapped at 2π
    double noiseDrift = 0.0;  // t * 0.2 * 0.4, unwrapped
  };
  Params params;

  // fbm(x, y, t, 3) from the JS: unnormalized, 0..1.75.
  // host port: double/sin-hash kept for fidelity to the JS; not ESP32-friendly
  inline double hash21(double x, double y) {
    const double n = sin(x * 12.9898 + y * 78.233) * 43758.5453;
    return n - floor(n);
  }
  inline double noise2D(double x, double y) {
    const double ix = floor(x), iy = floor(y), fx = x - ix, fy = y - iy;
    const double ux = fx * fx * (3.0 - 2.0 * fx), uy = fy * fy * (3.0 - 2.0 * fy);
    const double a = hash21(ix, iy), b = hash21(ix + 1.0, iy);
    const double c = hash21(ix, iy + 1.0), d = hash21(ix + 1.0, iy + 1.0);
    return (a * (1.0 - ux) + b * ux) * (1.0 - uy) + (c * (1.0 - ux) + d * ux) * uy;
  }
  inline double fbm3(double x, double y, double drift) {
    double v = 0.0, amp = 1.0, freq = 1.0;
    for (int i = 0; i < 3; i++) {
      v += amp * noise2D(x * freq, y * freq + drift);
      freq *= 2.0;
      amp *= 0.5;
    }
    return v;
  }

  void setup() {
    PFTables::init();
    params = Params();
  }

  void update(float dt, const InputFrame& input) {
    PFParams::applyUnit(input, 0, &params.rawKnob0, 0.05f);
    PFParams::apply(input, 1, &params.rawKnob1, 0.1f, 10.0f, 0.1f);
    PFParams::apply(input, 2, &params.rawKnob2, 0.0f, 4.9f, 0.05f);
    PFParams::applyUnit(input, 3, &params.rawKnob3, 0.05f);

    params.thickness = 0.1f + params.rawKnob0 * 0.6f;
    params.speed = params.rawKnob1;
    params.turbulence = params.rawKnob2 * 2.0f;
    params.baseHue = params.rawKnob3;

    const float dT = dt * (1.0f + params.speed * 4.0f);
    params.sweepAngle += dT * 0.5f;
    if (params.sweepAngle >= P0517_TWO_PI) params.sweepAngle -= P0517_TWO_PI;
    params.noiseDrift += (double)dT * 0.2 * 0.4;
  }

  void draw() {
    if (!PFTables::thetaT) { PFCanvas::present(); return; }
    const int w = PANEL_RES_W;
    const int h = PANEL_RES_H;

    // Global rotation angle
    const float sweepAngle = params.sweepAngle;
    const double drift = params.noiseDrift;
    const float beamWidth = params.thickness * (float)M_PI;
    const float invBeamWidth = 1.0f / beamWidth;
    const float turbulence = params.turbulence;

    for (int y = 0; y < h; y++) {
      const int row = y * PANEL_RES_W;
      for (int x = 0; x < w; x++) {
        // Base polar angle of the pixel, from the panel centre (w/2, h/2)
        float pixelAngle = PFTables::thetaT[row + x];
        if (pixelAngle < 0.0f) pixelAngle += P0517_TWO_PI;

        // Calculate noise to displace the angle (none at zero turbulence)
        float displacement = 0.0f;
        if (turbulence != 0.0f) {
          displacement = (float)((fbm3(x * 0.03, y * 0.03, drift) - 0.5) * turbulence);
        }

        // Compare pixel angle (plus noise) to the sweep angle, wrapped to 0..2π
        float angleDiff = sweepAngle - (pixelAngle + displacement);
        angleDiff -= P0517_TWO_PI * floorf(angleDiff * (1.0f / P0517_TWO_PI));

        float brightness = 0.0f;
        float saturation = 1.0f;
        float hue = params.baseHue;

        // Render the beam tail
        if (angleDiff < beamWidth) {
          // 0.0 = leading edge, 1.0 = trailing edge
          const float beamPos = angleDiff * invBeamWidth;
          const float fade = 1.0f - beamPos;
          brightness = fade * fade;  // Exponential fade out
          // Leading edge gets hot/white, trailing edge cools to saturated color
          saturation = beamPos * 1.5f;
          hue = params.baseHue + fade * 0.2f;  // Shift hue near the edge
        }

        // Add a slight ambient glow based on raw noise
        brightness += fmaxf(0.0f, displacement * 0.3f);

        uint8_t r, g, b;
        PFColor::hsvToRgb(hue, fminf(1.0f, saturation), fminf(1.0f, brightness), r, g, b);
        PFCanvas::setPixel(x, y, r, g, b);
      }
    }

    PFCanvas::present();
  }
} // namespace Pattern0517
