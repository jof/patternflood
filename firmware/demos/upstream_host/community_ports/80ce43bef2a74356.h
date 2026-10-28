// ===== Patternflow pattern =====
// Title:    Pattern 0512
// Author:   @engmung
// Source:   https://community.patternflow.work/community/p/80ce43bef2a74356
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the same lotus, twice the size,
// so it fills the square as it filled the original's 64-row panel (petal tips about 60 px
// out; the aura runs off into the corners). The lines stay fine rather than growing with
// it: the outline is a soft-edged 2.4 px stroke instead of 3 px, the aura has twice the
// stripes (as narrow as the original's at its larger radius), and the core's diagonal
// hatching stays one pixel. Distances and angles come from tables built once, and the four
// colours are worked out once a frame, not per pixel.
#pragma once
#include <Arduino.h>
#include <math.h>
#include "../config.h"
#include "../src/core_display.h"
#include "../src/core_encoders.h"
#include "../src/core_canvas.h"
#include "../src/core_math.h"
#include "../src/core_color.h"
#include "../src/core_noise.h"

namespace Pattern0512 {
  const char* NAME = "0512";
  const char* const KNOB_LABELS[4] = {"hueBase", "speed", "petals", "fold"};

  constexpr int FRAME_W = 128;
  constexpr int FRAME_H = 128;
  constexpr float S = 2.0f;             // the lotus's scale against the original

  struct Params {
    float hueBase = 0.0f;
    float speed = 0.0f;
    float petals = 0.0f;
    float fold = 0.0f;
    float timeAcc = 0.0f;
  };
  Params params;

  static float s_dist[FRAME_W * FRAME_H];
  static float s_angle[FRAME_W * FRAME_H];

void setup() {
    PFMath::buildSinLUT();

    params.hueBase = 0.85f;
    params.speed = 1.0f;
    params.petals = 6.0f;
    params.fold = 1.0f;
    params.timeAcc = 0.0f;

    const int cx = FRAME_W / 2, cy = FRAME_H / 2;
    for (int y = 0; y < FRAME_H; y++) {
        for (int x = 0; x < FRAME_W; x++) {
            const float dx = (float)(x - cx), dy = (float)(y - cy);
            s_dist[y * FRAME_W + x] = sqrtf(dx * dx + dy * dy);
            s_angle[y * FRAME_W + x] = atan2f(dy, dx);
        }
    }
  }

void update(float dt, const InputFrame& input) {
    params.hueBase = fmodf((float)((params.hueBase + input.knobDeltas[0] * 0.05f)), (float)(1.0f));
    if (params.hueBase < 0) params.hueBase += 1.0f;
    params.speed = max(0.0f, params.speed + input.knobDeltas[1] * 0.05f);
    params.petals = constrain(params.petals + input.knobDeltas[2] * 0.5f, 3.0f, 16.0f);
    params.fold = constrain(params.fold + input.knobDeltas[3] * 0.05f, 0.0f, 5.0f);
    params.timeAcc += dt * params.speed;
  }

static inline uint8_t sc(uint8_t c, float k) { return (uint8_t)((float)c * k + 0.5f); }

void draw() {
    PFCanvas::setFrame(FRAME_W, FRAME_H);

    const float t = params.timeAcc;
    const float p = floorf(params.petals);
    const float fold = params.fold;
    const float hue = params.hueBase;
    const float hatch = floorf(t * 10);

    // The four colours, at full value; the glow and the aura scale theirs down.
    uint8_t oR, oG, oB, gR, gG, gB, cR, cG, cB, aR, aG, aB;
    PFColor::hsvToRgb(hue, 0.5f, 1.0f, oR, oG, oB);
    PFColor::hsvToRgb(fmodf(hue + 0.1f, 1.0f), 0.9f, 1.0f, gR, gG, gB);
    PFColor::hsvToRgb(fmodf(hue + 0.4f, 1.0f), 1.0f, 1.0f, cR, cG, cB);
    PFColor::hsvToRgb(fmodf(hue + 0.6f, 1.0f), 1.0f, 1.0f, aR, aG, aB);

    constexpr float LINE = 1.6f, LINE_SOFT = 0.8f;      // the outline: solid, then fading out
    constexpr float GLOW = 5.0f * S, AURA = 10.0f * S;
    const float t2 = t * 2.0f, t3 = t * 3.0f;
    const float ripple = 0.5f / S, foldAmp = fold * 5.0f * S;

    for (int y = 0; y < FRAME_H; y++) {
        for (int x = 0; x < FRAME_W; x++) {
            const int i = y * FRAME_W + x;
            const float angle = s_angle[i];
            const float dist = s_dist[i];

            // Sacred Geometry / Lotus math: the radius rises and falls with the angle to make petals
            const float petalWave = PFMath::fastSin(angle * p + t2);
            const float targetDist = (15.0f + petalWave * 10.0f) * S
                                   + PFMath::fastSin(dist * ripple - t3) * foldAmp;
            const float val = fabsf(dist - targetDist);

            uint8_t r = 0, g = 0, b = 0;
            if (val < LINE + LINE_SOFT) {
                // Bright outline, its outer edge softened
                const float k = val < LINE ? 1.0f : 1.0f - (val - LINE) / LINE_SOFT;
                r = sc(oR, k); g = sc(oG, k); b = sc(oB, k);
                if (k < 1.0f && dist < targetDist) {            // under the soft edge, the glow
                    const float kg = 1.0f - val / GLOW;
                    const uint8_t r2 = sc(gR, kg), g2 = sc(gG, kg), b2 = sc(gB, kg);
                    if (r2 > r) r = r2;
                    if (g2 > g) g = g2;
                    if (b2 > b) b = b2;
                }
            } else if (val < GLOW && dist < targetDist) {
                // Inner petal glow
                const float k = 1.0f - val / GLOW;
                r = sc(gR, k); g = sc(gG, k); b = sc(gB, k);
            } else if (dist < targetDist * 0.4f) {
                // Core: one-pixel diagonal hatching, marching
                if (fmodf((float)(x + y) + hatch, 3.0f) == 0) {
                    r = cR; g = cG; b = cB;
                }
            } else if (val < AURA && dist > targetDist) {
                // Outer aura: stripes as narrow as the original's at twice the radius
                // (and, as there, only where the angle is positive)
                if (floorf(fmodf(angle * 40.0f, 2.0f)) == 0) {
                    const float k = 0.4f * (1.0f - val / AURA);
                    r = sc(aR, k); g = sc(aG, k); b = sc(aB, k);
                }
            }

            PFCanvas::setPixel(x, y, r, g, b);
        }
    }

    PFCanvas::present();
  }
} // namespace Pattern0512
