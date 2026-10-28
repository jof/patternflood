// ===== Patternflow pattern =====
// Title:    Oil pastel
// Author:   @engmung
// Source:   https://community.patternflow.work/community/p/551ac69c88834e41
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the same four bands of colour,
// red, blue, green and white, top to bottom, each still 32 pixels tall, and each stroke the
// original's size and shape. A band is now drawn by two pens instead of one, side by side
// across the square's width (centres 40 and 88, so they cross in the middle), the second a
// little behind in time and a quarter-tone apart in its first frequency, so the two make
// different loops in the same colour rather than a copy. Knobs and the click as the original.
#pragma once

#include <Arduino.h>
#include <math.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_params.h"
#include "src/core_math.h"
#include "src/core_mem.h"

namespace CausticTapestry {

constexpr int FRAME_W = 128;
constexpr int FRAME_H = 128;
constexpr int PENS = 2;                                   // the original: one pen a band, at x 31.5
static const float PEN_X[PENS] = {40.0f, 88.0f};
static const float PEN_LAG[PENS] = {0.0f, 2.3f};           // in sim time
static const float PEN_DF[PENS] = {0.0f, 0.25f};           // added to the band's first frequency

const char* NAME = "Caustic";
const char* const KNOB_LABELS[4] = {"Detune", "Speed", "Glow", "Fade"};
constexpr bool ABSOLUTE_READY = true;

// Knob parameters initialized to Pattern Lab values
static float kDetune = 0.12f;
static float kSpeed  = 1.262f;
static float kGlow   = 5.0f;
static float kFade   = 0.884f;

static float* tierInk = nullptr;
static float tAccum = 0.0f;
static float simT = 0.0f;
static float phaseKick = 0.0f;
static float ampEma[4] = {0.3f, 0.3f, 0.3f, 0.3f};

// Pre-baked Color Ramp LUT (verbatim)
static const uint8_t RAMP_LUT[][3] = {
  {0,0,0},{0,0,0},{0,0,0},{0,0,0},{1,0,0},{2,0,0},{3,0,0},{5,0,0},
  {8,0,0},{11,0,0},{14,0,0},{18,0,0},{22,0,0},{25,0,0},{29,0,0},{33,0,0},
  {37,0,0},{41,0,0},{45,0,0},{49,0,0},{54,0,0},{58,0,0},{62,0,0},{66,0,0},
  {71,0,0},{75,0,0},{80,0,0},{84,0,0},{89,0,0},{93,0,0},{98,0,0},{103,0,0},
  {107,0,0},{112,0,0},{117,0,0},{122,0,0},{127,0,0},{132,0,0},{137,0,0},{142,0,0},
  {147,0,0},{152,0,0},{157,0,0},{162,0,0},{167,0,0},{172,0,0},{177,0,0},{182,0,0},
  {188,0,0},{193,0,0},{198,0,0},{204,0,0},{209,0,0},{214,0,0},{220,0,0},{225,0,0},
  {231,0,0},{236,0,0},{242,0,0},{247,0,0},{253,0,0},{212,0,0},{140,0,0},{74,0,0},
  {17,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,1},{0,0,1},{0,0,2},{0,0,4},
  {0,0,6},{0,0,9},{0,0,12},{0,0,16},{0,0,20},{0,0,23},{0,0,27},{0,1,31},
  {0,1,35},{0,1,39},{0,1,43},{0,1,47},{0,1,52},{0,2,56},{0,2,60},{0,2,65},
  {0,3,69},{0,3,74},{0,3,78},{0,4,83},{0,4,87},{0,5,92},{0,5,97},{0,6,102},
  {0,6,106},{0,7,111},{0,7,116},{0,8,121},{0,9,126},{0,10,131},{0,11,136},{0,11,141},
  {0,12,146},{0,13,151},{0,14,156},{0,15,162},{0,16,167},{0,16,172},{0,17,177},{0,18,183},
  {0,19,188},{0,20,193},{0,21,199},{0,22,204},{0,23,210},{0,23,215},{0,24,220},{0,25,226},
  {0,26,232},{0,27,237},{0,28,243},{0,29,248},{0,30,254},{0,20,193},{0,8,123},{0,2,59},
  {0,0,6},{0,0,0},{0,0,0},{0,0,0},{0,1,0},{0,1,0},{0,2,0},{0,4,0},
  {0,6,0},{0,9,0},{0,12,0},{0,16,0},{0,19,0},{0,23,0},{0,27,0},{1,30,0},
  {1,34,0},{1,38,0},{1,42,0},{1,46,0},{1,50,0},{2,54,0},{2,59,0},{2,63,0},
  {2,67,0},{3,72,0},{3,76,0},{3,80,0},{4,85,0},{4,89,0},{5,94,0},{5,99,0},
  {6,103,0},{6,108,0},{7,113,0},{8,117,0},{8,122,0},{9,127,0},{10,132,0},{11,137,0},
  {11,142,0},{12,146,0},{13,151,0},{14,156,0},{15,161,0},{16,167,0},{16,172,0},{17,177,0},
  {18,182,0},{19,187,0},{20,192,0},{21,197,0},{21,203,0},{22,208,0},{23,213,0},{24,219,0},
  {25,224,0},{26,229,0},{27,235,0},{28,240,0},{28,246,0},{29,251,0},{23,210,0},{2,64,0},
  {0,0,0},{0,0,0},{0,0,0},{0,0,0},{1,1,1},{2,2,2},{3,3,3},{5,5,5},
  {7,7,7},{10,10,10},{14,14,14},{17,17,17},{21,21,21},{24,24,24},{28,28,28},{31,31,31},
  {35,35,35},{39,39,39},{43,43,43},{47,47,47},{51,51,51},{55,55,55},{59,59,59},{63,63,63},
  {67,67,67},{71,71,71},{76,76,76},{80,80,80},{84,84,84},{89,89,89},{93,93,93},{97,97,97},
  {102,102,102},{106,106,106},{111,111,111},{115,115,115},{120,120,120},{125,125,125},{129,129,129},{134,134,134},
  {139,139,139},{144,144,144},{148,148,148},{153,153,153},{158,158,158},{163,163,163},{168,168,168},{173,173,173},
  {178,178,178},{183,183,183},{188,188,188},{193,193,193},{198,198,198},{203,203,203},{208,208,208},{213,213,213},
  {218,218,218},{223,223,223},{229,229,229},{234,234,234},{239,239,239},{244,244,244},{250,250,250},{255,255,255},
};

static inline void deposit(int tier, float px, float py, float weight) {
  if (px < 1.0f || px >= (float)(FRAME_W - 2) || py < 1.0f || py >= (float)(FRAME_H - 2)) return;

  int x0 = (int)px;
  int y0 = (int)py;
  float fx = px - (float)x0;
  float fy = py - (float)y0;

  float* ink = tierInk + tier * (FRAME_W * FRAME_H);

  float wy[3];
  wy[0] = fmaxf(0.0f, 1.0f - fabsf(-1.0f - fy));
  wy[1] = fmaxf(0.0f, 1.0f - fabsf( 0.0f - fy));
  wy[2] = fmaxf(0.0f, 1.0f - fabsf( 1.0f - fy));

  float wx[3];
  wx[0] = fmaxf(0.0f, 1.0f - fabsf(-1.0f - fx));
  wx[1] = fmaxf(0.0f, 1.0f - fabsf( 0.0f - fx));
  wx[2] = fmaxf(0.0f, 1.0f - fabsf( 1.0f - fx));

  for (int dy = -1; dy <= 1; dy++) {
    float rowWeight = wy[dy + 1] * weight;
    int row = (y0 + dy) * FRAME_W;
    for (int dx = -1; dx <= 1; dx++) {
      ink[row + (x0 + dx)] += wx[dx + 1] * rowWeight;
    }
  }
}

void setup() {
  PFMath::buildSinLUT();

  if (!tierInk) {
    tierInk = PFMem::allocFloats(4 * FRAME_W * FRAME_H);
  }
  if (!tierInk) return;

  ampEma[0] = 0.3f;
  ampEma[1] = 0.3f;
  ampEma[2] = 0.3f;
  ampEma[3] = 0.3f;
  tAccum = 0.0f;
  simT = 0.0f;
  phaseKick = 0.0f;

  const float dtStep = 0.005f;
  float tSim = 0.0f;
  for (int s = 0; s < 6000; s++) {
    tSim += dtStep;
    for (int tier = 0; tier < 4; tier++) {
      for (int pen = 0; pen < PENS; pen++) {
        float ts = tSim + PEN_LAG[pen];
        float cy = 16.0f + (float)tier * 32.0f;
        float f1 = 2.0f + (float)tier * 0.5f + PEN_DF[pen];
        float f2 = 3.0f + 0.035f;
        float env = 0.85f + 0.15f * PFMath::fastSin(ts * 0.4f + (float)tier);
        float px = PEN_X[pen] + (22.0f * PFMath::fastSin(f1 * ts) + 8.0f * PFMath::fastCos(f2 * ts + (float)tier)) * env;
        float py = cy + (15.0f * PFMath::fastSin(3.0f * ts + (float)tier * 0.7f) + 6.0f * PFMath::fastCos(1.5f * ts)) * env;
        deposit(tier, px, py, 0.03f);
      }
    }
  }
}

void update(float dt, const InputFrame& input) {
  PFParams::apply(input, 0, &kDetune, 0.0f, 0.12f, 0.003f);
  PFParams::apply(input, 1, &kSpeed, 0.2f, 3.0f, 0.058f);
  PFParams::apply(input, 2, &kGlow, 1.0f, 5.0f, 0.083f);
  PFParams::apply(input, 3, &kFade, 0.75f, 0.98f, 0.005f);

  if (input.btnPressed[0] && !input.paramAbsoluteActive[0] && !input.knobAudioActive[0]) {
    phaseKick += PI * 0.5f;
    if (phaseKick > TWO_PI * 4.0f) phaseKick = fmodf(phaseKick, TWO_PI);
  }

  if (!tierInk) return;

  float safeDt = fminf(dt > 0.0f ? dt : 0.016f, 0.1f);
  tAccum += safeDt;
  if (tAccum > 200.0f * PI) tAccum -= 200.0f * PI;

  float fadeVal = fmaxf(0.65f, fminf(0.99f, kFade));
  int totalLen = 4 * FRAME_W * FRAME_H;
  for (int i = 0; i < totalLen; i++) {
    tierInk[i] *= fadeVal;
  }

  const int steps = 300;
  float subDt = (safeDt * 5.0f * kSpeed) / (float)steps;

  for (int s = 0; s < steps; s++) {
    simT += subDt;

    for (int tier = 0; tier < 4; tier++) {
      for (int pen = 0; pen < PENS; pen++) {
      float ts = simT + PEN_LAG[pen];
      float cy = 16.0f + (float)tier * 32.0f;
      float f1 = 2.0f + (float)tier * 0.5f + PEN_DF[pen];
      float f2 = 3.0f + kDetune;
      float pMod = tAccum * 0.1f + (float)tier * 1.57f + phaseKick;

      float env = 0.85f + 0.15f * PFMath::fastSin(ts * 0.35f + (float)tier * 0.8f);
      float px = PEN_X[pen] + (22.0f * PFMath::fastSin(f1 * ts + pMod) + 8.0f * PFMath::fastCos(f2 * ts + (float)tier)) * env;
      float py = cy + (15.0f * PFMath::fastSin(3.0f * ts + (float)tier * 0.7f) + 6.0f * PFMath::fastCos(1.5f * ts)) * env;

      if (!isfinite(px) || !isfinite(py)) {
        simT = 0.0f;
        memset(tierInk, 0, sizeof(float) * totalLen);
        return;
      }

      deposit(tier, px, py, 0.035f);
      }
    }
  }

  if (simT > 2000.0f * PI) simT = fmodf(simT, 200.0f * PI);
}

void draw() {
  PFCanvas::setFrame(FRAME_W, FRAME_H);

  if (!tierInk) {
    PFCanvas::present();
    return;
  }

  constexpr int planeSize = FRAME_W * FRAME_H;

  float norm[4];
  for (int tier = 0; tier < 4; tier++) {
    const float* ink = tierInk + tier * planeSize;
    float maxV = 0.001f;
    for (int i = 0; i < planeSize; i += 8) {
      float val = ink[i];
      if (val > maxV) maxV = val;
    }
    ampEma[tier] = ampEma[tier] * 0.90f + maxV * 0.10f;
    norm[tier] = (1.0f / fmaxf(ampEma[tier], 0.04f)) * kGlow;
  }

  const float* t0 = tierInk;
  const float* t1 = tierInk + planeSize;
  const float* t2 = tierInk + 2 * planeSize;
  const float* t3 = tierInk + 3 * planeSize;

  const float n0 = norm[0];
  const float n1 = norm[1];
  const float n2 = norm[2];
  const float n3 = norm[3];

  for (int y = 0; y < FRAME_H; y++) {
    int row = y * FRAME_W;
    for (int x = 0; x < FRAME_W; x++) {
      int idx = row + x;

      float v0 = t0[idx] * n0;
      float v1 = t1[idx] * n1;
      float v2 = t2[idx] * n2;
      float v3 = t3[idx] * n3;

      int bestTier = -1;
      float maxTierVal = 0.005f;

      if (v0 > maxTierVal && isfinite(v0)) { maxTierVal = v0; bestTier = 0; }
      if (v1 > maxTierVal && isfinite(v1)) { maxTierVal = v1; bestTier = 1; }
      if (v2 > maxTierVal && isfinite(v2)) { maxTierVal = v2; bestTier = 2; }
      if (v3 > maxTierVal && isfinite(v3)) { maxTierVal = v3; bestTier = 3; }

      if (bestTier == -1) {
        PFCanvas::setPixel(x, y, RAMP_LUT[0][0], RAMP_LUT[0][1], RAMP_LUT[0][2]);
        continue;
      }

      float shaped = 1.0f - expf(-maxTierVal * 1.4f);
      if (shaped < 0.0f) shaped = 0.0f;
      else if (shaped > 1.0f) shaped = 1.0f;
      shaped = shaped * shaped * (3.0f - 2.0f * shaped);

      float bandBase = 0.01f + (float)bestTier * 0.25f;
      float bandVal = bandBase + shaped * 0.23f;

      int li = (int)(bandVal * 255.0f + 0.5f);
      if (li < 0) li = 0;
      else if (li > 255) li = 255;

      PFCanvas::setPixel(x, y, RAMP_LUT[li][0], RAMP_LUT[li][1], RAMP_LUT[li][2]);
    }
  }

  PFCanvas::present();
}

} // namespace CausticTapestry