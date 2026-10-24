// SPDX-License-Identifier: CC-BY-SA-4.0
// Pattern: 0614
// Author:  Seunghun LEE
// Lineage: AI generated and curated
// Ported for Patternflood from web/src/lib/presets/pattern-0614.ts (web-only upstream; not an upstream port)
//

#pragma once
#include <Arduino.h>
#include <math.h>
#include "../config.h"
#include "../src/core_display.h"
#include "../src/core_encoders.h"
#include "../src/core_canvas.h"
#include "../src/core_math.h"
#include "../src/core_color.h"
#include "../src/core_tables.h"
#include "../src/core_params.h"

namespace Pattern0614 {
  const char* NAME = "0614";
  const char* const KNOB_LABELS[4] = {"Ring Freq", "Vortex Speed", "Edge Softness", "Hue"};
constexpr bool ABSOLUTE_READY = true;

  // The only time term is sin(... - t): the accumulator wraps at 2π.
  constexpr float P0614_TIME_WRAP = 2.0f * (float)M_PI;

  struct Params {
    float rawKnob0 = 0.0f;
    float rawKnob1 = 2.0f;
    float rawKnob2 = 0.0f;
    float rawKnob3 = 0.06f;
    float timeAcc = 0.0f;
    float freq = 0.0f;
    float speed = 0.0f;
    float soft = 0.0f;
    float hue = 0.0f;
  };
  Params params;

// Pattern: 0614
// Author: Seunghun LEE
// SPDX-License-Identifier: CC-BY-SA-4.0
// Date: 2026-06-14
// Lineage: AI generated and curated
//
// Concentric Velvet Rings: 부드러운 벨벳 질감의 물결이 원형으로 중첩되며 안쪽으로 빨려 들어가는 정적인 명상 효과
// Knob 1: Ring Frequency (동심원 링의 압축률)
// Knob 2: Vortex Speed (흡입 및 확장 속도)
// Knob 3: Edge Softness (경계면 소프트 필터 강도)
// Knob 4: Color Depth Hue (메인 테마 컬러 필터)

void setup() {
    PFMath::buildSinLUT();
    PFTables::init();
    params.rawKnob0 = 0.0f;
    params.rawKnob1 = 2.0f;
    params.rawKnob2 = 0.0f;
    params.rawKnob3 = 0.06f;
    params.timeAcc = 0.0f;
  }

void update(float dt, const InputFrame& input) {
    PFParams::applyUnit(input, 0, &params.rawKnob0, 0.05f);
    PFParams::apply(input, 1, &params.rawKnob1, 0.1f, 10.0f, 0.1f);
    PFParams::apply(input, 2, &params.rawKnob2, 0.0f, 4.9f, 0.05f);
    PFParams::applyUnit(input, 3, &params.rawKnob3, 0.05f);

    params.freq = 0.5f + params.rawKnob0 * 5.0f;
    params.speed = params.rawKnob1;
    params.soft = 0.1f + params.rawKnob2 * 0.9f;
    params.hue = params.rawKnob3;
    params.timeAcc += dt * params.speed;
    if (params.timeAcc >= P0614_TIME_WRAP) params.timeAcc -= P0614_TIME_WRAP;
  }

void draw() {
    if (!PFTables::rT) { PFCanvas::present(); return; }
    const int w = PANEL_RES_W;
    const int h = PANEL_RES_H;
    const float t = params.timeAcc;
    const float freq = params.freq;
    const float expo = params.soft * 3.0f;
    const float hue = params.hue;

    for (int y = 0; y < h; y++) {
        const int row = y * w;
        for (int x = 0; x < w; x++) {
            // sqrt(dx*dx + dy*dy) * 0.1 from (w/2, h/2); rT is in screen heights
            float dist = PFTables::rT[row + x] * (float)h * 0.1f;
            float wave = PFMath::fastSin(dist * freq - t);

            float smoothSig = fabsf(wave);
            smoothSig = PFMath::fastPow(smoothSig, expo);

            uint8_t r = 0, g = 0, b = 0;
            if (smoothSig > 0.05f) {
                float hVal = PFMath::jsMod(hue + dist * 0.01f, 1.0f);
                PFColor::hsvToRgb(hVal, 0.85f, smoothSig, r, g, b);

                if (smoothSig > 0.9f) {
                    r = r > 175 ? 255 : r + 80; g = g > 175 ? 255 : g + 80; b = b > 175 ? 255 : b + 80;
                }
            }

            PFCanvas::setPixel(x, y, r, g, b);
        }
    }

    PFCanvas::present();
  }
} // namespace Pattern0614
