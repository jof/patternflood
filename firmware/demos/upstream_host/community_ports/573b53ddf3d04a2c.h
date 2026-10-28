// ===== Patternflow pattern =====
// Title:    heart
// Author:   @engmung
// Source:   https://community.patternflow.work/community/p/573b53ddf3d04a2c
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the same caustic heart, 1.7 times
// the size (x and y alike, so it keeps its tall shape) and centred, so it spans the square
// top to bottom instead of sitting small in the middle. It is drawn with five strands at the
// original's spacing instead of three, so the lace is denser, and 480 sub-steps a frame
// instead of 320, so the bigger stroke stays a continuous line. Knobs as the original.
#pragma once

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_params.h"
#include "src/core_math.h"
#include "src/core_mem.h"

namespace CausticHeart {

const char* NAME = "Caustic Heart";
const char* const KNOB_LABELS[4] = {"Detune", "Speed", "Lace", "Fade"};
constexpr bool ABSOLUTE_READY = true;

constexpr int FRAME_W = 128;
constexpr int FRAME_H = 128;
constexpr int TOTAL_PIXELS = FRAME_W * FRAME_H;
constexpr float SCALE = 1.7f;                    // the original: 1, on a 64 x 128 frame
constexpr float CX = 63.5f;
constexpr float CY = 63.5f - 4.5f * SCALE;        // the figure's box centred, as the original's was
constexpr int STRANDS = 2;                       // -2..2: five strands (the original: -1..1)

static float k_detune = 0.0f;
static float k_speed = 3.0f;
static float k_lace = 2.643f;
static float k_fade = 0.882f;

static float* ink = nullptr;
static float t_accum = 0.0f;
static float simT = 0.0f;
static float shock = 1.0f;
static float ampEma = 0.3f;

static uint8_t TRANSFER_LUT[1024];

static const uint8_t RAMP_LUT[256][3] = {
  {0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},
  {0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{1,0,0},{1,0,0},{1,0,0},
  {1,0,0},{1,0,0},{1,0,0},{2,0,0},{2,0,0},{2,0,0},{3,0,0},{3,0,0},
  {4,0,0},{4,0,0},{4,0,0},{5,0,0},{6,0,0},{6,0,0},{7,0,0},{8,0,0},
  {8,0,0},{9,0,0},{10,0,0},{11,0,0},{12,0,0},{13,0,0},{14,0,0},{15,0,0},
  {15,0,0},{16,0,0},{17,0,0},{18,0,0},{19,0,0},{20,0,0},{21,0,0},{22,0,0},
  {23,0,0},{24,0,0},{25,0,0},{26,0,0},{27,0,0},{28,0,0},{29,0,0},{30,0,0},
  {31,0,0},{32,0,0},{33,0,0},{34,0,0},{35,0,0},{36,0,0},{37,0,0},{38,0,0},
  {39,0,0},{40,0,0},{41,0,0},{42,0,0},{43,0,0},{44,0,0},{45,0,0},{46,0,0},
  {48,0,0},{49,0,0},{50,0,0},{51,0,0},{52,0,0},{53,0,0},{54,0,0},{55,0,0},
  {56,0,0},{57,0,0},{58,0,0},{59,0,0},{61,0,0},{62,0,0},{63,0,0},{64,0,0},
  {65,0,0},{66,0,0},{67,0,0},{68,0,0},{70,0,0},{71,0,0},{72,0,0},{73,0,0},
  {74,0,0},{75,0,0},{76,0,0},{78,0,0},{79,0,0},{80,0,0},{81,0,0},{82,0,0},
  {83,0,0},{85,0,0},{86,0,0},{87,0,0},{88,0,0},{89,0,0},{90,0,0},{92,0,0},
  {93,0,0},{94,0,0},{95,0,0},{96,0,0},{98,0,0},{99,0,0},{100,0,0},{101,0,0},
  {103,0,0},{104,0,0},{105,0,0},{106,0,0},{107,0,0},{109,0,0},{110,0,0},{111,0,0},
  {112,0,0},{114,0,0},{115,0,0},{116,0,0},{117,0,0},{118,0,0},{120,0,0},{121,0,0},
  {122,0,0},{123,0,0},{125,0,0},{126,0,0},{127,0,0},{129,0,0},{130,0,0},{131,0,0},
  {132,0,0},{134,0,0},{135,0,0},{136,0,0},{137,0,0},{139,0,0},{140,0,0},{141,0,0},
  {143,0,0},{144,0,0},{145,0,0},{146,0,0},{148,0,0},{149,0,0},{150,0,0},{152,0,0},
  {153,0,0},{154,0,0},{156,0,0},{157,0,0},{158,0,0},{159,0,0},{161,0,0},{162,0,0},
  {163,0,0},{165,0,0},{166,0,0},{167,0,0},{169,0,0},{170,0,0},{171,0,0},{173,0,0},
  {174,0,0},{175,0,0},{177,0,0},{178,0,0},{179,0,0},{181,0,0},{182,0,0},{183,0,0},
  {185,0,0},{186,0,0},{188,0,0},{189,0,0},{190,0,0},{192,0,0},{193,0,0},{194,0,0},
  {196,0,0},{197,0,0},{198,0,0},{200,0,0},{201,0,0},{203,0,0},{204,0,0},{205,0,0},
  {207,0,0},{208,0,0},{209,0,0},{211,0,0},{212,0,0},{214,0,0},{215,0,0},{216,0,0},
  {218,0,0},{219,0,0},{221,0,0},{222,0,0},{223,0,0},{225,0,0},{226,0,0},{228,0,0},
  {229,0,0},{230,0,0},{232,0,0},{233,0,0},{235,0,0},{236,0,0},{237,0,0},{239,0,0},
  {240,0,0},{242,0,0},{243,0,0},{245,0,0},{246,0,0},{247,0,0},{249,0,0},{250,0,0},
  {252,0,0},{253,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},
  {255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},
  {255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},
};

static inline void deposit(float px, float py, float weight) {
  if (px < 1.0f || px >= 126.0f || py < 1.0f || py >= 126.0f) return;
  int x0 = (int)px;
  int y0 = (int)py;
  float fx = px - (float)x0;
  float fy = py - (float)y0;

  float w00 = (1.0f - fx) * (1.0f - fy) * weight;
  float w10 = fx * (1.0f - fy) * weight;
  float w01 = (1.0f - fx) * fy * weight;
  float w11 = fx * fy * weight;

  int row0 = y0 * FRAME_W;
  int row1 = (y0 + 1) * FRAME_W;

  ink[row0 + x0]     += w00;
  ink[row0 + x0 + 1] += w10;
  ink[row1 + x0]     += w01;
  ink[row1 + x0 + 1] += w11;
}

void setup() {
  PFMath::buildSinLUT();

  for (int i = 0; i < 1024; i++) {
    float v = (float)i * (6.0f / 1023.0f);
    float out = 1.0f - expf(-v);
    out = out * out * (3.0f - 2.0f * out);
    if (out < 0.0f) out = 0.0f;
    else if (out > 1.0f) out = 1.0f;
    int li = (int)(out * 255.0f + 0.5f);
    if (li < 0) li = 0;
    else if (li > 255) li = 255;
    TRANSFER_LUT[i] = (uint8_t)li;
  }

  if (!ink) ink = PFMem::allocFloats(TOTAL_PIXELS);
  if (!ink) return;

  t_accum = 0.0f;
  simT = 0.0f;
  shock = 1.0f;
  ampEma = 0.3f;

  float tSimInit = 0.0f;
  constexpr float defaultLace = 3.5f;
  for (int s = 0; s < 10000; s++) {
    tSimInit += 0.0042f;
    float u = tSimInit * 1.5f;

    float sinU = PFMath::fastSin(u);
    float hx = 16.0f * (sinU * sinU * sinU);
    float hy = -(13.0f * PFMath::fastCos(u) - 5.0f * PFMath::fastCos(2.0f * u) - 2.0f * PFMath::fastCos(3.0f * u) - PFMath::fastCos(4.0f * u));

    float rx = (2.2f + 0.6f * defaultLace) * PFMath::fastSin((2.0f + defaultLace + 0.035f) * tSimInit + 0.8f);
    float ry = (3.2f + 0.9f * defaultLace) * PFMath::fastCos((1.0f + defaultLace) * tSimInit);

    float px = CX + (hx * 1.25f + rx) * (0.95f * SCALE);
    float py = CY + (hy * 1.60f + ry) * (1.15f * SCALE);

    deposit(px, py, 0.022f);
  }
}

void update(float dt, const InputFrame& input) {
  if (!ink) return;

  PFParams::apply(input, 0, &k_detune, 0.0f, 0.12f, 0.003f);
  PFParams::apply(input, 1, &k_speed, 0.2f, 3.0f, 0.058f);
  PFParams::apply(input, 2, &k_lace, 1.0f, 6.0f, 0.104f);
  PFParams::apply(input, 3, &k_fade, 0.75f, 0.98f, 0.005f);

  float safeDt = (dt > 0.1f) ? 0.1f : ((dt < 0.001f) ? 0.016f : dt);

  constexpr float TIME_WRAP = 200.0f * TWO_PI;
  t_accum += safeDt;
  if (t_accum >= TIME_WRAP) {
    t_accum -= TIME_WRAP;
  }

  if (input.btnPressed[0] && !input.paramAbsoluteActive[0] && !input.knobAudioActive[0]) {
    shock = 2.4f;
  }
  shock = shock * 0.94f + 1.0f * 0.06f;

  for (int i = 0; i < TOTAL_PIXELS; i++) {
    ink[i] *= k_fade;
  }

  constexpr int steps = 480;
  float subDt = (safeDt * 5.0f * k_speed) * (1.0f / (float)steps);

  float fHarmX = 2.0f + k_lace + k_detune;
  float fHarmY = 1.0f + k_lace + k_detune * 0.5f;
  float ampX = 2.0f + 0.7f * k_lace;
  float ampY = 3.0f + 1.0f * k_lace;

  float pMod1 = t_accum * 0.12f;
  float pMod2 = t_accum * 0.08f + 0.8f;

  for (int s = 0; s < steps; s++) {
    simT += subDt * 2.8f;
    if (simT >= TIME_WRAP) {
      simT -= TIME_WRAP;
    }

    float heartPulse = 1.0f + (0.12f * PFMath::fastSin(simT * 1.5f) * PFMath::fastSin(simT * 0.75f)) * shock;

    for (int tr = -STRANDS; tr <= STRANDS; tr++) {
      float dPhase = (float)tr * 0.035f;
      float u = (simT + dPhase) * 1.5f;

      float sinU = PFMath::fastSin(u);
      float hx = 16.0f * (sinU * sinU * sinU);
      float hy = -(13.0f * PFMath::fastCos(u) - 5.0f * PFMath::fastCos(2.0f * u) - 2.0f * PFMath::fastCos(3.0f * u) - PFMath::fastCos(4.0f * u));

      float rx = ampX * PFMath::fastSin(fHarmX * simT + pMod1 + (float)tr * 0.22f);
      float ry = ampY * PFMath::fastCos(fHarmY * simT + pMod2 + (float)tr * 0.16f);

      float px = CX + (hx * 1.25f + rx) * (0.95f * SCALE * heartPulse);
      float py = CY + (hy * 1.60f + ry) * (1.15f * SCALE * heartPulse);

      if (!isfinite(px) || !isfinite(py)) {
        simT = 0.0f;
        memset(ink, 0, sizeof(float) * TOTAL_PIXELS);
        return;
      }

      deposit(px, py, 0.026f);
    }
  }
}

void draw() {
  PFCanvas::setFrame(FRAME_W, FRAME_H);

  if (!ink) {
    PFCanvas::present();
    return;
  }

  constexpr float FIXED_GLOW = 5.0f;

  float maxV = 0.001f;
  for (int i = 0; i < TOTAL_PIXELS; i += 8) {
    if (ink[i] > maxV) maxV = ink[i];
  }
  ampEma = ampEma * 0.90f + maxV * 0.10f;
  float norm = (1.0f / fmaxf(ampEma, 0.04f)) * FIXED_GLOW;

  float vScale = norm * 1.4f * (1023.0f / 6.0f);

  for (int y = 0; y < FRAME_H; y++) {
    int row = y * FRAME_W;
    for (int x = 0; x < FRAME_W; x++) {
      float val = ink[row + x];
      if (!isfinite(val) || val <= 0.0f) {
        PFCanvas::setPixel(x, y, RAMP_LUT[0][0], RAMP_LUT[0][1], RAMP_LUT[0][2]);
        continue;
      }

      int idx = (int)(val * vScale);
      if (idx > 1023) idx = 1023;

      uint8_t li = TRANSFER_LUT[idx];
      PFCanvas::setPixel(x, y, RAMP_LUT[li][0], RAMP_LUT[li][1], RAMP_LUT[li][2]);
    }
  }

  PFCanvas::present();
}

} // namespace CausticHeart