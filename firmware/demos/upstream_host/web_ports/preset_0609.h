// SPDX-License-Identifier: CC-BY-SA-4.0
// Pattern: 0609
// Author:  Seunghun LEE
// Lineage: AI generated and curated
// Ported for Patternflood from web/src/lib/presets/pattern-0609.ts (web-only upstream; not an upstream port)
//

#pragma once
#include <Arduino.h>
#include <math.h>
#include "../config.h"
#include "../src/core_display.h"
#include "../src/core_encoders.h"
#include "../src/core_canvas.h"
#include "../src/core_math.h"
#include "../src/core_tables.h"
#include "../src/core_params.h"

namespace Pattern0609 {
  const char* NAME = "0609";
  const char* const KNOB_LABELS[4] = {"Viscosity", "Flow Speed", "Core Expansion", "Crust Fracture"};
constexpr bool ABSOLUTE_READY = true;

  // Every time term (t, 0.4t, 0.6t, 1.5t) repeats after 20π, so the
  // accumulator wraps there without a visible jump.
  constexpr float P0609_TIME_WRAP = 20.0f * (float)M_PI;

  struct Params {
    float rawKnob0 = 0.0f;
    float rawKnob1 = 2.0f;
    float rawKnob2 = 0.0f;
    float rawKnob3 = 0.06f;
    float timeAcc = 0.0f;
  };
  Params params;

  // Separable terms: per-column / per-row factors, refreshed once a frame
  // (sinf outside the pixel loop), and the static crack field's factors.
  static float colN1[PANEL_RES_W], colN2[PANEL_RES_W], colCrack[PANEL_RES_W];
  static float rowN1[PANEL_RES_H], rowN2[PANEL_RES_H], rowCrack[PANEL_RES_H];

// Pattern: 0609
// Author: Seunghun LEE
// SPDX-License-Identifier: CC-BY-SA-4.0
// Date: 2026-06-09
// Lineage: AI generated and curated
//
// Molten Magma Heat-Map — Emulates thermal energy color bands where bright hotspots cooling down leave dark crusts.
// Knob 1: Thermal Fluid Viscosity (0.0 to 1.0)
// Knob 2: Boiling Flow Speed (0.1 to 10.0)
// Knob 3: Hotspot Core Expansion (0.0 to 4.9)
// Knob 4: Cool Crust Fracturing (0.0 to 1.0)

void setup() {
    PFMath::buildSinLUT();
    PFTables::init();
    params.rawKnob0 = 0.0f;
    params.rawKnob1 = 2.0f;
    params.rawKnob2 = 0.0f;
    params.rawKnob3 = 0.06f;
    params.timeAcc = 0.0f;
    for (int x = 0; x < PANEL_RES_W; x++) colCrack[x] = sinf(x * 1.5f);
    for (int y = 0; y < PANEL_RES_H; y++) rowCrack[y] = cosf(y * 1.5f);
  }

void update(float dt, const InputFrame& input) {
    PFParams::applyUnit(input, 0, &params.rawKnob0, 0.05f);
    PFParams::apply(input, 1, &params.rawKnob1, 0.1f, 10.0f, 0.1f);
    PFParams::apply(input, 2, &params.rawKnob2, 0.0f, 4.9f, 0.05f);
    PFParams::applyUnit(input, 3, &params.rawKnob3, 0.05f);

    // viscosity = knobValues[0], speed = [1], expansion = [2], crust = [3]
    params.timeAcc += dt * params.rawKnob1;
    if (params.timeAcc >= P0609_TIME_WRAP) params.timeAcc -= P0609_TIME_WRAP;
  }

void draw() {
    if (!PFTables::rT) { PFCanvas::present(); return; }
    const int w = PANEL_RES_W;
    const int h = PANEL_RES_H;
    const float t = params.timeAcc;
    const float viscosity = params.rawKnob0;
    const float expansion = params.rawKnob2;
    const float crust = params.rawKnob3;

    const float visc = 0.02f + viscosity * 0.08f;
    const float coreShift = expansion - 2.5f;
    const float halfW = w * 0.5f;
    const float halfH = h * 0.5f;

    // n1 = sin(x*visc + t) * cos(y*visc - t)
    // n2 = sin((x - w/2)*0.05 - 0.4t) * sin((y - h/2)*0.05 + 0.6t)
    for (int x = 0; x < w; x++) {
        colN1[x] = sinf(x * visc + t);
        colN2[x] = sinf((x - halfW) * 0.05f - t * 0.4f);
    }
    for (int y = 0; y < h; y++) {
        rowN1[y] = cosf(y * visc - t);
        rowN2[y] = sinf((y - halfH) * 0.05f + t * 0.6f);
    }

    const bool cracks = crust > 0.05f;
    const float crackLimit = 1.0f - crust;
    const float t15 = t * 1.5f;

    for (int y = 0; y < h; y++) {
        const int row = y * w;
        for (int x = 0; x < w; x++) {

            // Multiple layers of wave signals create fluid thermal paths
            float n1 = colN1[x] * rowN1[y];
            float n2 = colN2[x] * rowN2[y];
            float dist = PFTables::rT[row + x] * (float)h;   // pixels from (w/2, h/2)
            float n3 = PFMath::fastCos(dist * 0.1f - t15);

            float heatSum = (n1 + n2 * 0.7f + n3 * 0.5f) / 2.2f;
            heatSum = heatSum + coreShift * 0.3f; // Manual shift balancing
            float temp = fmaxf(0.0f, fminf(1.0f, (heatSum + 1.0f) * 0.5f));

            int r = 0, g = 0, b = 0;

            // Heat map color palette step assignments
            if (temp > 0.85f) {
                // Incandescent Superhot White Core
                r = 255; g = 255; b = 230;
            } else if (temp > 0.65f) {
                // Liquid Yellow Plasma
                r = 255; g = 180 + (int)floorf((temp - 0.65f) * 375.0f); b = 20;
            } else if (temp > 0.4f) {
                // Flowing Viscous Orange-Red
                r = 220; g = (int)floorf((temp - 0.4f) * 700.0f); b = 5;
            } else if (temp > 0.18f) {
                // Deep Cooled Dormant Crimson
                r = 40 + (int)floorf((temp - 0.18f) * 800.0f); g = 0; b = 0;
            } else {
                // Charcoal Rock Base
                r = 10; g = 5; b = 15;
            }

            // Introduce cool surface fractures/cracking maps
            if (cracks) {
                float crackPattern = colCrack[x] * rowCrack[y];
                if (crackPattern > crackLimit && temp < 0.6f) {
                    // Reduce thermal radiation, exposing dark deep cracks
                    r = (int)(r * 0.15f);
                    g = 0;
                    b = (int)(b * 0.1f);
                }
            }

            PFCanvas::setPixel(x, y, (uint8_t)r, (uint8_t)g, (uint8_t)b);
        }
    }

    PFCanvas::present();
  }
} // namespace Pattern0609
