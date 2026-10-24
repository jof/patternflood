// SPDX-License-Identifier: CC-BY-SA-4.0
// Pattern: 0619
// Author:  Seunghun LEE
// Lineage: AI generated and curated
// Ported for Patternflood from web/src/lib/presets/pattern-0619.ts (web-only upstream; not an upstream port)
//
// Bitwise Interference Shards with cyberpunk colors
// Knob 1: Block Division Resolution (0.0 to 1.0)
// Knob 2: Transition Frequency Speed (0.1 to 10.0)
// Knob 3: Bitwise Shift Modifier (0.0 to 4.9)
// Knob 4: Color Mapping Selection (0.0 to 1.0)

#pragma once
#include <Arduino.h>
#include <math.h>
#include "../config.h"
#include "../src/core_display.h"
#include "../src/core_encoders.h"
#include "../src/core_canvas.h"
#include "../src/core_math.h"
#include "../src/core_params.h"

namespace Pattern0619 {
  const char* NAME = "0619";
  const char* const KNOB_LABELS[4] = {"Block Size", "Speed", "Bit Shift", "Palette"};
  constexpr bool ABSOLUTE_READY = true;

  // Raw knob state at the web's default ranges and starting values. The JS
  // reads input.knobValues directly, so these are used as-is.
  static float rawKnob0 = 0.0f;   // res      0..1 (wraps)
  static float rawKnob1 = 2.0f;   // speed    0.1..10
  static float rawKnob2 = 0.0f;   // bitMod   0..4.9
  static float rawKnob3 = 0.06f;  // palette  0..1 (wraps)
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
    timeAcc += dt * rawKnob1;
    // t only reaches sin() with a multiplier of 1, so wrap at 2π.
    if (timeAcc > TWO_PI) timeAcc -= TWO_PI;
  }

  void draw() {
    const int w = PANEL_RES_W;
    const int h = PANEL_RES_H;
    const float t = timeAcc;

    const int blockSize = 4 + (int)floorf(rawKnob0 * 16.0f);
    const int shiftVal = (int)floorf(rawKnob2) + 1;
    const bool icePalette = rawKnob3 < 0.5f;

    for (int y = 0; y < h; y++) {
      // 비트연산과 결합하기 위한 축 데이터 정수화 및 미러링
      const int bx = y / blockSize;
      const int my = abs((y % (blockSize * 2)) - blockSize);

      for (int x = 0; x < w; x++) {
        const int ax = x / blockSize;
        const int mx = abs((x % (blockSize * 2)) - blockSize);

        // 정수 그리드 ID에 대한 비트 XOR 간섭 유도
        const int shardId = (ax ^ bx) << shiftVal;
        const float wave = PFMath::fastSin((mx + my) * 0.3f + shardId * 0.1f + t);
        const float combined = fabsf(wave);

        uint8_t r = 0, g = 0, b = 0;

        if (combined > 0.6f) {
          const float norm = (combined - 0.6f) / 0.4f;

          // 테마 분기를 통한 사이버펑크 3색 스웨치 맵핑
          if (icePalette) {
            // Ice & Violet
            r = (uint8_t)(130.0f * norm);
            g = (uint8_t)(255.0f * (1.0f - norm));
            b = 255;
          } else {
            // Gold & Crimson
            r = 255;
            g = (uint8_t)(180.0f * norm);
            b = 0;
          }

          if (combined > 0.93f) {
            r = 255; g = 255; b = 255;
          }
        } else if (combined < 0.05f) {
          // 파편의 경계면을 분리해주는 완전 암전 그루브 라인 스티치
          r = 20; g = 20; b = 40;
        }

        PFCanvas::setPixel(x, y, r, g, b);
      }
    }

    PFCanvas::present();
  }
} // namespace Pattern0619
