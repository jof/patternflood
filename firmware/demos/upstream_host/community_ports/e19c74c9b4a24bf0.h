// ===== Patternflow pattern =====
// Title:    Branched flow
// Author:   @engmung
// Source:   https://community.patternflow.work/community/p/e19c74c9b4a24bf0
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the same rays bending through the
// same rotating potential, at the original's pixel scale, centred in the square. In the
// original, rays heading sideways left its 64-wide frame (and respawned) a third of the way
// out; here every ray runs on to the edge, to radius 92 so the corners fill, and there are
// 6400 of them instead of 2800 so the longer branches stay as dense. The potential keeps its
// 75-pixel span (beyond it, its outer ring). Knobs as the original.
#pragma once

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_params.h"
#include "src/core_math.h"
#include "src/core_color.h"
#include "src/core_mem.h"

namespace BranchedFlow {

const char* NAME = "Branched flow";
const char* const KNOB_LABELS[4] = {"Curvature", "PulseFreq", "Torsion", "Persistence"};
constexpr bool ABSOLUTE_READY = true;

constexpr int FRAME_W = 128;
constexpr int FRAME_H = 128;
constexpr int TOTAL_PIXELS = FRAME_W * FRAME_H;

constexpr int N_ANGLES = 32;
constexpr int N_RINGS = 16;
constexpr int RAY_COUNT = 6400;      // the original: 2800
constexpr float RAY_MAX_R = 92.0f;     // the original: 75, the potential's span

// Knob parameters
static float g_curv = 0.04f;
static float g_pulse = 1.088f;
static float g_torsion = 2.5f;
static float g_persistence = 0.852f;

// Pre-baked Power LUTs for draw mapping
static float g_pow075[256];
static float g_pow065[256];

// State & Buffers
static float g_t = 0.0f;
static float g_peakEMA0 = 1.0f;
static float g_peakEMA1 = 1.0f;
static uint32_t g_seed = 38471;

static float g_potMajor[N_ANGLES * N_RINGS];
static float g_potMinor[N_ANGLES * N_RINGS];

static float* g_bufMinor = nullptr;
static float* g_bufMajor = nullptr;

static float g_rayAngle[RAY_COUNT];
static float g_rayDist[RAY_COUNT];
static float g_rayVAngle[RAY_COUNT];
static uint8_t g_isMajor[RAY_COUNT];

static const uint8_t RAMP_LUT[256][3] = {
  {0,0,0},{0,0,0},{0,0,0},{0,0,2},{0,0,4},{0,0,8},{0,0,13},{0,0,18},
  {0,0,24},{0,0,30},{0,0,37},{0,0,43},{0,0,50},{0,0,56},{0,0,63},{0,0,70},
  {0,0,77},{0,0,84},{0,0,92},{1,0,99},{1,0,107},{1,0,114},{1,0,122},{1,0,130},
  {1,0,137},{1,0,145},{1,0,153},{1,0,162},{2,0,170},{2,0,178},{2,0,186},{2,0,195},
  {2,0,203},{3,0,212},{3,0,220},{3,0,229},{3,0,237},{4,0,246},{4,0,255},{0,49,232},
  {0,56,226},{0,61,222},{0,65,220},{0,68,218},{0,70,216},{0,73,215},{0,75,214},{0,77,213},
  {0,78,213},{0,80,212},{0,82,212},{0,84,211},{0,85,211},{0,87,211},{0,88,211},{0,90,211},
  {0,91,211},{0,92,211},{0,94,211},{0,95,211},{0,96,211},{0,98,212},{0,99,212},{0,100,212},
  {0,101,212},{0,103,213},{0,104,213},{0,105,213},{0,106,214},{0,107,214},{0,109,214},{0,110,215},
  {0,111,215},{0,112,216},{0,113,216},{0,114,217},{0,116,217},{0,117,218},{0,118,218},{0,119,219},
  {0,120,219},{0,121,220},{0,122,220},{0,123,221},{0,125,221},{0,126,222},{0,127,223},{0,128,223},
  {0,129,224},{0,130,224},{0,131,225},{0,132,226},{0,133,226},{0,134,227},{0,136,227},{0,137,228},
  {0,138,229},{0,139,229},{0,140,230},{0,141,231},{0,142,231},{0,143,232},{0,144,233},{0,145,233},
  {0,146,234},{0,148,235},{0,149,235},{0,150,236},{0,151,237},{0,152,237},{0,153,238},{0,154,239},
  {0,155,239},{0,156,240},{0,157,241},{0,158,241},{0,159,242},{0,160,243},{0,162,243},{0,163,244},
  {0,164,245},{0,165,246},{0,166,246},{0,167,247},{0,168,248},{0,169,248},{0,170,249},{0,171,250},
  {0,172,251},{0,173,251},{0,175,252},{0,176,253},{0,177,253},{0,178,254},{0,179,255},{0,129,185},
  {0,76,111},{0,28,45},{0,0,0},{0,0,0},{0,0,0},{2,1,0},{4,3,0},{8,6,0},
  {14,10,0},{20,16,0},{26,21,0},{33,27,0},{40,33,0},{47,39,0},{54,45,0},{61,52,0},
  {69,58,0},{76,65,0},{84,72,0},{92,78,0},{100,85,0},{108,92,0},{116,99,0},{124,107,0},
  {132,114,0},{141,121,0},{149,129,0},{158,136,0},{167,144,0},{176,152,0},{184,159,0},{193,167,0},
  {202,175,0},{212,183,0},{221,191,0},{230,199,0},{239,207,0},{249,216,0},{255,221,13},{255,222,33},
  {255,223,46},{255,224,56},{255,224,65},{255,225,72},{255,226,79},{255,227,85},{255,227,91},{255,228,97},
  {255,229,102},{255,230,107},{255,230,112},{255,231,117},{255,232,122},{255,233,126},{255,233,131},{255,234,135},
  {255,235,139},{255,236,143},{255,236,148},{255,237,152},{255,238,156},{255,238,159},{255,239,163},{255,240,167},
  {255,240,171},{255,241,175},{255,242,178},{255,242,182},{255,243,186},{255,244,189},{255,244,193},{255,245,197},
  {255,245,200},{255,246,204},{255,247,207},{255,247,211},{255,248,214},{255,249,217},{255,249,221},{255,250,224},
  {255,250,228},{255,251,231},{255,252,234},{255,252,238},{255,253,241},{255,253,245},{255,254,248},{255,254,251},
  {255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},
  {255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},
  {255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},
  {255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},
};

static inline float nextRandom() {
  g_seed = (g_seed * 1664525u + 1013904223u);
  return (float)g_seed * (1.0f / 4294967296.0f);
}

static inline void spawnRay(int i) {
  g_isMajor[i] = (i >= (RAY_COUNT >> 1)) ? 1 : 0;
  g_rayAngle[i] = ((float)i / (float)RAY_COUNT) * TWO_PI;
  g_rayDist[i] = 1.0f + nextRandom() * 2.5f;
  g_rayVAngle[i] = 0.0f;
}

static void bakeHarmonics(float curv, float torsion) {
  const float sinT12 = PFMath::fastSin(g_t * 1.2f);
  const float cosT15 = g_t * 1.5f;
  const float cosT18 = g_t * 1.8f;

  for (int ir = 0; ir < N_RINGS; ir++) {
    const float rNorm = (float)ir / (float)(N_RINGS - 1);
    const float twist = sinT12 * torsion * (1.0f - rNorm * 0.7f);
    const float rCosMaj = PFMath::fastCos(rNorm * 4.5f - cosT15) * curv;
    const float rCosMin = PFMath::fastCos(rNorm * 6.0f + cosT18) * curv * 0.8f;
    const int row = ir * N_ANGLES;

    for (int ia = 0; ia < N_ANGLES; ia++) {
      const float th = ((float)ia / (float)N_ANGLES) * TWO_PI;
      g_potMajor[row + ia] = PFMath::fastSin(th * 3.0f + twist) * rCosMaj;
      g_potMinor[row + ia] = PFMath::fastSin(th * 6.0f - twist * 1.2f + (PI / 3.0f)) * rCosMin;
    }
  }
}

static void stepHarmonics(float fade) {
  constexpr float cx = 63.5f;
  constexpr float cy = 63.5f;
  constexpr float maxR = 75.0f;
  constexpr float invTwoPi = 1.0f / TWO_PI;
  constexpr float gradScale = (float)N_ANGLES * invTwoPi;
  constexpr float rScale = (float)N_RINGS / maxR;
  constexpr float maxGR = (float)(N_RINGS - 1) - 0.001f;

  for (int i = 0; i < TOTAL_PIXELS; i++) {
    g_bufMinor[i] *= fade;
    g_bufMajor[i] *= fade;
  }

  for (int step = 0; step < 2; step++) {
    for (int i = 0; i < RAY_COUNT; i++) {
      float th = g_rayAngle[i];
      float r = g_rayDist[i];
      float vth = g_rayVAngle[i];
      const uint8_t isMaj = g_isMajor[i];

      const float normTh = PFMath::jsMod(PFMath::jsMod(th, TWO_PI) + TWO_PI, TWO_PI);
      const float gAngle = normTh * invTwoPi * (float)N_ANGLES;
      float gR = r * rScale;
      if (gR > maxGR) gR = maxGR;

      const int ia0 = ((int)gAngle) % N_ANGLES;
      const int ia1 = (ia0 + 1) % N_ANGLES;
      const int ir0 = (int)gR;

      const float* potGrid = isMaj ? g_potMajor : g_potMinor;
      const int rOffset = ir0 * N_ANGLES;
      const float p0 = potGrid[rOffset + ia0];
      const float p1 = potGrid[rOffset + ia1];
      const float dVdth = (p1 - p0) * gradScale;

      const float spd = isMaj ? 1.2f : 0.9f;
      const float torque = isMaj ? (dVdth * 0.35f) : (-dVdth * 0.25f);

      vth = (vth - torque / (r * 0.2f + 2.0f)) * 0.975f;
      th += vth;
      r += spd;

      const int px = (int)(cx + PFMath::fastCos(th) * r);
      const int py = (int)(cy + PFMath::fastSin(th) * r);

      if (r >= RAY_MAX_R || px < 0 || px >= FRAME_W || py < 0 || py >= FRAME_H) {
        spawnRay(i);
      } else {
        g_rayAngle[i] = th;
        g_rayDist[i] = r;
        g_rayVAngle[i] = vth;

        const int idx = py * FRAME_W + px;
        if (isMaj) {
          g_bufMajor[idx] += 1.4f;
        } else {
          g_bufMinor[idx] += 0.85f;
        }
      }
    }
  }
}

void setup() {
  PFMath::buildSinLUT();
  PFColor::buildPowLUTf(0.75f, g_pow075);
  PFColor::buildPowLUTf(0.65f, g_pow065);

  if (!g_bufMinor) g_bufMinor = PFMem::allocFloats(TOTAL_PIXELS);
  if (!g_bufMajor) g_bufMajor = PFMem::allocFloats(TOTAL_PIXELS);

  if (!g_bufMinor || !g_bufMajor) return;

  g_seed = 38471;
  for (int i = 0; i < RAY_COUNT; i++) {
    spawnRay(i);
    g_rayDist[i] = nextRandom() * 90.0f;
  }

  bakeHarmonics(0.35f, 2.5f);
  for (int i = 0; i < 160; i++) {
    stepHarmonics(0.94f);
  }
}

void update(float dt, const InputFrame& input) {
  PFParams::apply(input, 0, &g_curv, 0.04f, 0.7f, 0.014f);
  PFParams::apply(input, 1, &g_pulse, 0.2f, 2.5f, 0.048f);
  PFParams::apply(input, 2, &g_torsion, 0.5f, 5.0f, 0.094f);
  PFParams::apply(input, 3, &g_persistence, 0.82f, 0.985f, 0.003f);

  if (!g_bufMinor || !g_bufMajor) return;

  const float delta = fminf(dt, 0.1f);
  g_t += delta * g_pulse;
  constexpr float T_PERIOD = TWO_PI * 10.0f;
  if (g_t >= T_PERIOD) {
    g_t -= T_PERIOD;
  }

  bakeHarmonics(g_curv, g_torsion);
  stepHarmonics(g_persistence);

  float m0 = 0.01f;
  float m1 = 0.01f;
  for (int i = 0; i < TOTAL_PIXELS; i++) {
    if (g_bufMinor[i] > m0) m0 = g_bufMinor[i];
    if (g_bufMajor[i] > m1) m1 = g_bufMajor[i];
  }
  g_peakEMA0 = g_peakEMA0 * 0.90f + m0 * 0.10f;
  g_peakEMA1 = g_peakEMA1 * 0.90f + m1 * 0.10f;
}

void draw() {
  PFCanvas::setFrame(FRAME_W, FRAME_H);

  if (!g_bufMinor || !g_bufMajor) {
    PFCanvas::present();
    return;
  }

  const float inv0 = 1.0f / fmaxf(0.01f, g_peakEMA0);
  const float inv1 = 1.0f / fmaxf(0.01f, g_peakEMA1);

  for (int y = 0; y < FRAME_H; y++) {
    const int row = y * FRAME_W;
    for (int x = 0; x < FRAME_W; x++) {
      const int idx = row + x;

      float nMin = g_bufMinor[idx] * inv0;
      if (nMin > 1.0f) nMin = 1.0f;
      else if (nMin < 0.0f) nMin = 0.0f;
      const int lutIdxMin = (int)(nMin * 255.0f + 0.5f);
      const float valMin = g_pow075[lutIdxMin] * 0.48f;

      float nMaj = g_bufMajor[idx] * inv1;
      if (nMaj > 1.0f) nMaj = 1.0f;
      else if (nMaj < 0.0f) nMaj = 0.0f;
      const int lutIdxMaj = (int)(nMaj * 255.0f + 0.5f);
      const float valMaj = (nMaj > 0.04f) ? (0.52f + g_pow065[lutIdxMaj] * 0.48f) : 0.0f;

      float finalVal = fmaxf(valMin, valMaj);
      if (finalVal > 1.0f) finalVal = 1.0f;

      const int li = (int)(finalVal * 255.0f + 0.5f);
      PFCanvas::setPixel(x, y, RAMP_LUT[li][0], RAMP_LUT[li][1], RAMP_LUT[li][2]);
    }
  }

  PFCanvas::present();
}

} // namespace BranchedFlow