// ===== Patternflow pattern =====
// Title:    MercuryDrops
// Author:   @engmung
// Source:   https://community.patternflow.work/community/p/9ae85b2d6dbb4d7d
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the same condensing ring of
// metaballs in the same purple-to-white ramp, bigger and fuller. There are 18 drops instead
// of 12 (the same mass per drop, so the same condensing behaviour), their orbits 1.4 times
// the size and nearly as wide as they are tall (x 1.2 to y 1.45, where the original's were
// 0.75 to 1.45 for its 64-wide frame), so the pool spreads over the square instead of
// standing in a column and more separate droplets break away from it. Each drop is only
// 1.05 times the size, so they stay distinct rather than fusing into one disc, and keeps its
// own tall shape. Knobs as the original (Radius keeps its range, scaled in the drawing).
#pragma once

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_params.h"
#include "src/core_math.h"
#include "src/core_mem.h"

namespace MercuryDrops {

const char* NAME = "Mercury Drops";
const char* const KNOB_LABELS[4] = {"Condense", "Speed", "Tension", "Radius"};
constexpr bool ABSOLUTE_READY = true;

constexpr int FRAME_W = 128;
constexpr int FRAME_H = 128;
constexpr int NUM_DROPS = 18;                 // the original: 12
constexpr float SCALE = 1.4f;                 // orbits, x and y alike
constexpr float DROP_SCALE = 1.05f;           // the drops, x and y alike
constexpr float ORBIT_X = 1.2f;               // the original: 0.75 (and 1.45 for y)
constexpr float SPIN_SPREAD = 0.88f / (float)(NUM_DROPS - 1);   // the original's 0.08 a drop over 12

// Field LUT settings (0.0 to 32.0 range)
constexpr int FIELD_LUT_SIZE = 1024;
constexpr float FIELD_MAX = 32.0f;
constexpr float FIELD_TO_LUT_SCALE = (float)(FIELD_LUT_SIZE - 1) / FIELD_MAX;

// Knob states initialized to Pattern Lab values
static float kCondensation = 5.147f;
static float kSpeed = 3.202f;
static float kSurfaceTension = 2.04f;
static float kDropletRadius = 9.644f;

// Color ramp (stops 0.000:#000000, 0.755:#6600ff, 1.000:#ffffff; mode oklchShort; wrap off)
static const uint8_t RAMP_LUT[256][3] = {
  {0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},
  {0,0,0},{0,0,0},{0,0,0},{0,0,1},{0,0,1},{0,0,1},{0,0,1},{0,0,2},
  {0,0,2},{0,0,2},{0,0,3},{0,0,3},{0,0,4},{1,0,4},{1,0,5},{1,0,6},
  {1,0,6},{1,0,7},{1,0,8},{1,0,9},{1,0,10},{1,0,11},{2,0,12},{2,0,13},
  {2,0,15},{2,0,16},{2,0,17},{3,0,18},{3,0,19},{3,0,20},{3,0,21},{4,0,23},
  {4,0,24},{4,0,25},{5,0,26},{5,0,27},{5,0,28},{6,0,30},{6,0,31},{6,0,32},
  {7,0,33},{7,0,35},{8,0,36},{8,0,37},{9,0,38},{9,0,40},{10,0,41},{10,0,42},
  {11,0,43},{11,0,45},{12,0,46},{12,0,47},{13,0,49},{14,0,50},{14,0,51},{15,0,53},
  {15,0,54},{16,0,55},{16,0,57},{17,0,58},{18,0,59},{18,0,61},{19,0,62},{19,0,63},
  {20,0,65},{20,0,66},{21,0,67},{22,0,69},{22,0,70},{23,0,72},{23,0,73},{24,0,74},
  {25,0,76},{25,0,77},{26,0,79},{27,0,80},{27,0,81},{28,0,83},{28,0,84},{29,0,86},
  {30,0,87},{30,0,89},{31,0,90},{31,0,91},{32,0,93},{33,0,94},{33,0,96},{34,0,97},
  {35,0,99},{35,0,100},{36,0,102},{36,0,103},{37,0,105},{38,0,106},{38,0,108},{39,0,109},
  {40,0,111},{40,0,112},{41,0,114},{42,0,115},{42,0,117},{43,0,118},{44,0,120},{44,0,121},
  {45,0,123},{46,0,124},{46,0,126},{47,0,127},{48,0,129},{48,0,130},{49,0,132},{50,0,133},
  {50,0,135},{51,0,137},{52,0,138},{52,0,140},{53,0,141},{54,0,143},{54,0,144},{55,0,146},
  {56,0,147},{56,0,149},{57,0,151},{58,0,152},{58,0,154},{59,0,155},{60,0,157},{60,0,159},
  {61,0,160},{62,0,162},{62,0,163},{63,0,165},{64,0,167},{65,0,168},{65,0,170},{66,0,171},
  {67,0,173},{67,0,175},{68,0,176},{69,0,178},{69,0,180},{70,0,181},{71,0,183},{72,0,185},
  {72,0,186},{73,0,188},{74,0,189},{74,0,191},{75,0,193},{76,0,194},{77,0,196},{77,0,198},
  {78,0,199},{79,0,201},{79,0,203},{80,0,204},{81,0,206},{82,0,208},{82,0,209},{83,0,211},
  {84,0,213},{85,0,215},{85,0,216},{86,0,218},{87,0,220},{87,0,221},{88,0,223},{89,0,225},
  {90,0,226},{90,0,228},{91,0,230},{92,0,232},{93,0,233},{93,0,235},{94,0,237},{95,0,238},
  {96,0,240},{96,0,242},{97,0,244},{98,0,245},{99,0,247},{99,0,249},{100,0,251},{101,0,252},
  {102,0,254},{103,12,255},{104,28,255},{105,39,255},{107,47,255},{109,54,255},{110,61,255},{112,67,255},
  {114,72,255},{115,77,255},{117,82,255},{119,86,255},{121,91,255},{123,95,255},{125,99,255},{127,103,255},
  {129,107,255},{131,111,255},{134,115,255},{136,118,255},{138,122,255},{140,126,255},{143,129,255},{145,133,255},
  {147,136,255},{150,139,255},{152,143,255},{155,146,255},{157,149,255},{160,153,255},{162,156,255},{165,159,255},
  {167,162,255},{170,165,255},{173,168,255},{175,171,255},{178,175,255},{181,178,255},{183,181,255},{186,184,255},
  {189,187,255},{191,190,255},{194,193,255},{197,196,255},{200,199,255},{203,202,255},{205,205,255},{208,208,255},
  {211,211,255},{214,214,255},{217,217,255},{220,220,255},{223,223,255},{225,226,255},{228,229,255},{231,232,255},
  {234,234,255},{237,237,255},{240,240,255},{243,243,255},{246,246,255},{249,249,255},{252,252,255},{255,255,255},
};

// Simulation State
static float animTime = 0.0f;
static uint32_t seed = 202608U;
static int32_t sites[NUM_DROPS];
static float dropX[NUM_DROPS];
static float dropY[NUM_DROPS];
static float smoothMass[NUM_DROPS];
static float r2Cache[NUM_DROPS];
static float substepAcc = 0.0f;

// Precomputed Shading LUT: field (0..32) -> Ramp LUT Index (0..255)
static uint8_t fieldToRampLUT[FIELD_LUT_SIZE];

// Precomputed dx^2 table: [x * NUM_DROPS + i]
static float* dx2Table = nullptr;

static inline float nextRand() {
  seed = (seed * 1664525U + 1013904223U);
  return (float)seed / 4294967296.0f;
}

void setup() {
  PFMath::buildSinLUT();

  if (!dx2Table) {
    dx2Table = PFMem::allocFloats(FRAME_W * NUM_DROPS);
  }

  animTime = 0.0f;
  seed = 202608U;
  substepAcc = 0.0f;

  for (int i = 0; i < NUM_DROPS; i++) {
    sites[i] = 4;
    smoothMass[i] = 2.0f;
    dropX[i] = 16.0f + nextRand() * 96.0f;
    dropY[i] = 16.0f + nextRand() * 96.0f;
  }
}

void update(float dt, const InputFrame& input) {
  PFParams::apply(input, 0, &kCondensation, 0.5f, 36.0f, 0.74f);
  PFParams::apply(input, 1, &kSpeed, 0.1f, 8.0f, 0.165f);
  PFParams::apply(input, 2, &kSurfaceTension, 0.8f, 4.0f, 0.067f);
  PFParams::apply(input, 3, &kDropletRadius, 4.0f, 18.0f, 0.292f);

  if (!dx2Table) return;

  float safeDt = fminf(dt, 0.05f);
  animTime += safeDt * kSpeed;
  if (animTime >= 200.0f * PI) {
    animTime -= 200.0f * PI;
  }

  substepAcc += 200.0f * kSpeed * safeDt;
  int steps = (int)substepAcc;
  if (steps > 50) steps = 50;
  substepAcc -= (float)steps;

  for (int s = 0; s < steps; s++) {
    int i = (int)(nextRand() * (float)NUM_DROPS);
    if (i >= NUM_DROPS) i = NUM_DROPS - 1;

    int32_t n = sites[i];
    if (n > 0) {
      float rate = 1.0f + kCondensation / (float)n;
      if (nextRand() * (1.0f + kCondensation) < rate) {
        sites[i]--;
        int dir = (nextRand() < 0.5f) ? -1 : 1;
        int target = (i + dir + NUM_DROPS) % NUM_DROPS;
        sites[target]++;
        if (sites[target] > 70) {
          int32_t split = (int32_t)((float)sites[target] * 0.45f);
          sites[target] -= split;
          sites[(target + 1) % NUM_DROPS] += split;
        }
      }
    }
  }

  float cx = (float)FRAME_W * 0.5f;
  float cy = (float)FRAME_H * 0.5f;

  for (int i = 0; i < NUM_DROPS; i++) {
    float targetMass = log2f(1.0f + (float)sites[i]);
    smoothMass[i] += (targetMass - smoothMass[i]) * 0.04f;

    float mass = smoothMass[i];
    float orbitR = fmaxf(6.0f, 36.0f - mass * 5.5f) * SCALE;
    float ang = animTime * (0.3f + ((float)i * SPIN_SPREAD)) / fmaxf(0.6f, mass * 0.5f) + (float)i * (TWO_PI / (float)NUM_DROPS);

    float targetX = cx + PFMath::fastCos(ang) * (orbitR * ORBIT_X);
    float targetY = cy + PFMath::fastSin(ang * 1.2f + (float)i * 0.5f) * (orbitR * 1.45f);

    dropX[i] += (targetX - dropX[i]) * 0.06f;
    dropY[i] += (targetY - dropY[i]) * 0.06f;
  }
}

void draw() {
  PFCanvas::setFrame(FRAME_W, FRAME_H);

  if (!dx2Table) {
    PFCanvas::present();
    return;
  }

  // 1. Precalculate drop radius squares
  for (int i = 0; i < NUM_DROPS; i++) {
    float r = kDropletRadius * DROP_SCALE * (0.6f + smoothMass[i] * 0.5f);
    r2Cache[i] = r * r;
  }

  // 2. Precalculate dx^2 table for all X coordinates
  for (int x = 0; x < FRAME_W; x++) {
    float* rowPtr = &dx2Table[x * NUM_DROPS];
    float fx = (float)x;
    for (int i = 0; i < NUM_DROPS; i++) {
      float dx = fx - dropX[i];
      rowPtr[i] = dx * dx;
    }
  }

  // 3. Bake Shading & Smoothstep Transfer LUT (1024 entries, ~5 microseconds)
  constexpr float threshold = 8.0f;
  constexpr float invThreshold = 1.0f / threshold;
  constexpr float stepField = FIELD_MAX / (float)(FIELD_LUT_SIZE - 1);

  for (int idx = 0; idx < FIELD_LUT_SIZE; idx++) {
    float field = (float)idx * stepField;
    float v = 0.0f;
    if (field > threshold) {
      float distInside = (field - threshold) * 0.08f * kSurfaceTension;
      float core = fminf(1.0f, distInside);
      float s = PFMath::fastSin(fminf(PI, distInside * 1.5f));
      float rim = s * s * 0.45f;
      v = core * 0.65f + rim + 0.2f;
    } else {
      float ratio = field * invThreshold;
      v = ratio * ratio * ratio * 0.22f;
    }
    float clamped = fminf(fmaxf(v, 0.0f), 1.0f);
    float smoothV = clamped * clamped * (3.0f - 2.0f * clamped);
    fieldToRampLUT[idx] = (uint8_t)(smoothV * 255.0f + 0.5f);
  }

  // 4. Ultra-fast inner rendering loop
  for (int y = 0; y < FRAME_H; y++) {
    float dy2[NUM_DROPS];
    float fy = (float)y;
    for (int i = 0; i < NUM_DROPS; i++) {
      float dy = (fy - dropY[i]) * 0.65f;
      dy2[i] = dy * dy + 1.0f;
    }

    for (int x = 0; x < FRAME_W; x++) {
      const float* dx2_ptr = &dx2Table[x * NUM_DROPS];
      float field = 0.0f;

      #pragma GCC unroll 12
      for (int i = 0; i < NUM_DROPS; i++) {
        field += r2Cache[i] / (dx2_ptr[i] + dy2[i]);
      }

      int lutIdx = (int)(field * FIELD_TO_LUT_SCALE);
      if (lutIdx >= FIELD_LUT_SIZE) lutIdx = FIELD_LUT_SIZE - 1;

      uint8_t li = fieldToRampLUT[lutIdx];
      PFCanvas::setPixel(x, y, RAMP_LUT[li][0], RAMP_LUT[li][1], RAMP_LUT[li][2]);
    }
  }

  PFCanvas::present();
}

} // namespace MercuryDrops