// SPDX-License-Identifier: CC-BY-SA-4.0
// Pattern: Isometric Pillars
// Author:  Seunghun LEE
// Lineage: AI generated and curated via Pattern Lab
// Ported for Patternflood from web/src/lib/presets/pattern-0624.ts (web-only upstream; not an upstream port)
//
// Isometric Pillars waving in 3D projection space
// Made with Patternflow Pattern Lab — https://patternflow.work/pattern-lab
//
// Knobs (from update()): k0 grid size (8 + floor(k0 * 12) pillars per side),
// k1 wave speed, k2 max pillar height (10 + k2 * 35 px), k3 hue shift.

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

namespace Pattern0624 {
  const char* NAME = "0624";
  const char* const KNOB_LABELS[4] = {"Grid Size", "Speed", "Max Height", "Color Shift"};
  constexpr bool ABSOLUTE_READY = true;

  // Raw knob state at the web's default ranges and starting values. The JS
  // reads input.knobValues directly, so these are used as-is.
  static float rawKnob0 = 0.0f;   // cols       0..1 (wraps)
  static float rawKnob1 = 2.0f;   // speed      0.1..10
  static float rawKnob2 = 0.0f;   // maxHeight  0..4.9
  static float rawKnob3 = 0.06f;  // colorShift 0..1 (wraps)
  static float timeAcc = 0.0f;

  static inline void plot(int px, int py, const uint8_t* rgb) {
    if (px >= 0 && px < PANEL_RES_W && py >= 0 && py < PANEL_RES_H) {
      PFCanvas::setPixel(px, py, rgb[0], rgb[1], rgb[2]);
    }
  }

  static void drawIsoPillar(int tx, int ty, int sx, int sy, int h,
                            const uint8_t* rgbTop, const uint8_t* rgbLeft, const uint8_t* rgbRight) {
    for (int dy = -sy; dy <= sy; dy++) {
      const int span = (int)floorf((1.0f - (float)abs(dy) / sy) * sx);
      for (int dx = -span; dx <= span; dx++) plot(tx + dx, ty + dy, rgbTop);
    }

    for (int dy = 0; dy < h; dy++) {
      for (int stepY = 0; stepY <= sy; stepY++) {
        const int span = (int)floorf(((float)stepY / sy) * sx);
        for (int dx = -span; dx < 0; dx++) plot(tx + dx, ty + dy + stepY, rgbLeft);
      }
    }

    for (int dy = 0; dy < h; dy++) {
      for (int stepY = 0; stepY <= sy; stepY++) {
        const int span = (int)floorf(((float)stepY / sy) * sx);
        for (int dx = 0; dx <= span; dx++) plot(tx + dx, ty + dy + stepY, rgbRight);
      }
    }
  }

  void setup() {
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
    // t only reaches sin() with a multiplier of 1, so wrap at 2π.
    if (timeAcc > TWO_PI) timeAcc -= TWO_PI;
  }

  void draw() {
    const int w = PANEL_RES_W;
    const int h = PANEL_RES_H;
    const float t = timeAcc;

    for (int py = 0; py < h; py++) {
      for (int px = 0; px < w; px++) {
        PFCanvas::setPixel(px, py, 10, 10, 20);
      }
    }

    const int cols = 8 + (int)floorf(rawKnob0 * 12.0f);
    const int rows = cols;
    const float maxHeight = 10.0f + rawKnob2 * 35.0f;
    const float colorShift = rawKnob3;
    const int sizeX = 8;
    const int sizeY = 4;
    const float cx = w / 2.0f;
    const float cy = h / 2.0f - 10.0f;
    const float half = cols / 2.0f;

    // Back to front along the diagonals, so nearer pillars overdraw farther ones.
    for (int sum = 0; sum < rows + cols; sum++) {
      for (int r = 0; r < rows; r++) {
        const int c = sum - r;
        if (c < 0 || c >= cols) continue;

        const float isoX = cx + (c - r) * sizeX;
        const float isoY = cy + (c + r) * sizeY;

        const float dc = c - half, dr = r - half;
        const float dist = sqrtf(dc * dc + dr * dr);
        // Once per pillar (at most 19 x 19), not per pixel: full-precision
        // sinf keeps pillar heights exact; the LUT's error moves edges by a pixel.
        const float wave = sinf(dist * 0.8f - t) * 0.5f + 0.5f;
        const int height = (int)floorf(wave * maxHeight);

        const int tx = (int)floorf(isoX);
        const int ty = (int)floorf(isoY - height);

        const float hue = PFMath::jsMod(wave * 0.3f + colorShift, 1.0f);
        uint8_t top[3], left[3], right[3];
        PFColor::hsvToRgb(hue, 0.85f, 0.95f, top[0], top[1], top[2]);
        PFColor::hsvToRgb(hue, 0.9f, 0.6f, left[0], left[1], left[2]);
        PFColor::hsvToRgb(hue, 0.95f, 0.4f, right[0], right[1], right[2]);

        drawIsoPillar(tx, ty, sizeX, sizeY, height, top, left, right);
      }
    }

    PFCanvas::present();
  }
} // namespace Pattern0624
