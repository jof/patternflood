// ===== Patternflow pattern =====
// Title:    flower_0917
// Author:   @engmung
// Source:   https://community.patternflow.work/community/p/dbbfed6b6a404299
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the published bouquet already
// spans the full 128 rows, so the square's extra width becomes a meadow: twelve spires
// across the frame instead of five, front ones tall and back ones short as in the original,
// with florets a fifth larger and two more per spire, finer stalks (one sample per row) and
// twice the drifting spores. Sway, petal count, speed and the green-violet-yellow ramp are
// the original's.
#pragma once

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_params.h"
#include "src/core_math.h"
#include "src/core_mem.h"

namespace flower_0917 {

const char* NAME = "flower_0917";
const char* const KNOB_LABELS[4] = {"PetalCount", "SpireSpeed", "FloretScale", "SwayAmp"};
constexpr bool ABSOLUTE_READY = true;

constexpr int FRAME_W = 128;
constexpr int FRAME_H = 128;

static const uint8_t RAMP_LUT[256][3] = {
  {0,0,0},{0,7,1},{0,28,3},{0,63,7},{0,112,13},{0,174,20},{0,239,28},{0,236,29},
  {0,232,30},{0,228,30},{0,224,31},{0,221,32},{0,217,33},{0,213,33},{0,209,34},{0,206,35},
  {0,202,35},{0,198,36},{0,194,37},{0,190,38},{0,187,38},{0,183,39},{0,179,40},{0,175,41},
  {0,172,41},{0,168,42},{0,164,43},{0,160,44},{0,157,44},{0,153,45},{0,149,46},{0,145,47},
  {0,142,47},{0,138,48},{0,134,49},{0,130,50},{0,126,50},{0,123,51},{0,119,52},{0,115,52},
  {0,111,53},{0,108,54},{0,104,55},{0,100,55},{0,96,56},{0,93,57},{1,93,58},{2,95,58},
  {3,97,59},{4,98,59},{5,100,60},{6,102,61},{7,103,61},{8,105,62},{9,106,62},{10,108,63},
  {11,110,64},{12,111,64},{13,113,65},{14,114,66},{15,116,66},{17,118,67},{18,119,67},{19,121,68},
  {20,123,69},{21,124,69},{22,126,70},{23,127,71},{24,129,71},{25,131,72},{26,132,72},{27,134,73},
  {28,136,74},{29,137,74},{30,139,75},{31,140,76},{32,142,76},{33,144,77},{34,145,77},{35,147,78},
  {36,149,79},{37,150,79},{38,152,80},{39,153,80},{40,155,81},{41,157,82},{43,158,82},{44,160,83},
  {45,161,84},{46,163,84},{47,165,85},{48,166,85},{49,168,86},{50,170,87},{51,171,87},{52,173,88},
  {68,161,96},{85,147,104},{103,133,113},{121,119,121},{138,105,130},{156,91,139},{169,81,145},{170,82,146},
  {170,83,146},{170,84,147},{171,85,147},{171,85,148},{172,86,148},{172,87,149},{173,88,150},{173,89,150},
  {174,90,151},{174,90,151},{174,91,152},{175,92,152},{175,93,153},{176,94,153},{176,95,154},{177,96,154},
  {177,96,155},{177,97,156},{178,98,156},{178,99,157},{179,100,157},{179,101,158},{180,101,158},{180,102,159},
  {181,103,159},{181,104,160},{192,126,154},{202,149,149},{213,172,143},{224,194,137},{235,217,132},{246,240,126},
  {253,255,122},{252,254,121},{252,254,120},{251,254,119},{251,253,118},{251,253,118},{250,252,117},{250,252,116},
  {249,251,115},{249,251,114},{248,250,114},{248,250,113},{247,250,112},{247,249,111},{246,249,110},{246,248,110},
  {246,248,109},{245,247,108},{245,247,107},{244,246,106},{244,246,106},{243,246,105},{243,245,104},{242,245,103},
  {242,244,102},{241,244,102},{241,243,101},{240,243,100},{240,243,99},{240,242,98},{239,242,97},{239,241,97},
  {238,241,96},{238,240,95},{237,240,94},{237,239,93},{236,239,93},{236,239,92},{235,238,91},{235,238,90},
  {235,237,89},{234,237,89},{234,236,88},{233,236,87},{233,236,86},{232,235,85},{232,235,85},{231,234,84},
  {231,234,83},{230,233,82},{230,233,81},{230,232,80},{229,232,80},{229,232,79},{228,231,78},{228,231,77},
  {227,230,76},{231,235,62},{241,244,32},{250,254,2},{251,255,0},{251,254,0},{251,254,0},{251,254,0},
  {251,253,0},{251,253,0},{251,253,0},{252,252,0},{252,252,0},{252,251,0},{252,251,0},{252,251,0},
  {252,250,0},{252,250,0},{252,250,0},{252,249,0},{252,249,0},{252,249,0},{252,248,0},{252,248,0},
  {252,247,0},{253,247,0},{253,247,0},{253,246,0},{253,246,0},{253,246,0},{253,245,0},{253,245,0},
  {253,245,0},{253,244,0},{253,244,0},{253,244,0},{253,243,0},{253,243,0},{253,242,0},{253,242,0},
  {254,242,0},{254,241,0},{254,241,0},{254,241,0},{254,240,0},{254,240,0},{254,240,0},{254,239,0},
  {254,239,0},{254,238,0},{254,238,0},{254,238,0},{254,237,0},{254,237,0},{254,237,0},{255,236,0},
  {255,236,0},{255,236,0},{255,235,0},{255,235,0},{255,235,0},{255,234,0},{255,234,0},{255,234,0}
};

struct Spire {
  float x;
  float baseY;
  float tipY;
  float seed;
  float baseAmp;
  float flex;
};

// The original's five (x 16..48 on its 64-wide frame) become a dozen across 128: tall ones
// in front, shorter ones between and behind them, each with its own sway phase.
static const int SPIRE_COUNT = 12;
static const Spire spires[SPIRE_COUNT] = {
  {  14.0f, 127.0f, 38.0f, 5.1f, 4.4f, 1.22f },
  {  31.0f, 127.0f, 24.0f, 1.2f, 5.0f, 1.15f },
  {  48.0f, 127.0f, 12.0f, 2.8f, 6.5f, 1.05f },
  {  65.0f, 127.0f, 30.0f, 4.5f, 4.5f, 1.25f },
  {  82.0f, 127.0f, 16.0f, 6.0f, 5.8f, 1.10f },
  {  99.0f, 127.0f, 28.0f, 3.9f, 5.2f, 1.18f },
  { 115.0f, 127.0f, 42.0f, 2.2f, 4.2f, 1.28f },
  {  22.0f, 127.0f, 56.0f, 0.7f, 3.5f, 1.30f },
  {  40.0f, 127.0f, 50.0f, 3.3f, 3.8f, 1.20f },
  {  57.0f, 127.0f, 60.0f, 5.6f, 3.6f, 1.26f },
  {  74.0f, 127.0f, 52.0f, 1.9f, 3.9f, 1.22f },
  {  91.0f, 127.0f, 58.0f, 4.1f, 3.4f, 1.30f }
};

static float param_petalCount = 8.077f;
static float param_spireSpeed = 4.0f;
static float param_floretScale = 2.601f;
static float param_swayAmp = 1.365f;

static float timeWave = 0.0f;
static float timeSporeY = 0.0f;
static float timeBlink = 0.0f;
static float* valField = nullptr;

static inline void addVal(float px, float py, float v) {
  int ix = PFMath::ifloor(px);
  int iy = PFMath::ifloor(py);
  if (ix >= 0 && ix < FRAME_W && iy >= 0 && iy < FRAME_H) {
    int idx = iy * FRAME_W + ix;
    float cv = PFMath::clamp01(v);
    if (cv > valField[idx]) {
      valField[idx] = cv;
    }
  }
}

static inline float getSilkDisplacement(float frac, const Spire& sp, float t, float ampMult) {
  float lagPhase = frac * 1.55f;
  float wave = PFMath::fastSin(t * 1.05f + sp.seed - lagPhase);
  float counterWave = PFMath::fastSin(t * 0.52f + sp.seed * 0.5f) * 0.35f;
  float curve = PFMath::fastPow(frac, 1.8f) * sp.flex;
  return (wave + counterWave) * (sp.baseAmp * ampMult) * curve;
}

void setup() {
  PFMath::buildSinLUT();
  if (!valField) {
    valField = PFMem::allocFloats(FRAME_W * FRAME_H);
  }
}

void update(float dt, const InputFrame& input) {
  if (!valField) return;

  PFParams::apply(input, 0, &param_petalCount, 3.0f, 12.0f, 0.188f);
  PFParams::apply(input, 1, &param_spireSpeed, 0.2f, 4.0f, 0.079f);
  PFParams::apply(input, 2, &param_floretScale, 1.2f, 3.5f, 0.048f);
  PFParams::apply(input, 3, &param_swayAmp, 0.5f, 3.5f, 0.063f);

  float rate = dt * param_spireSpeed;

  constexpr float WAVE_PERIOD = TWO_PI * 100.0f;
  timeWave += rate;
  if (timeWave >= WAVE_PERIOD) {
    timeWave -= WAVE_PERIOD;
  }

  constexpr float SPORE_Y_PERIOD = (float)(FRAME_H + 30);
  timeSporeY += rate * 18.0f;
  if (timeSporeY >= SPORE_Y_PERIOD) {
    timeSporeY = PFMath::jsMod(timeSporeY, SPORE_Y_PERIOD);
  }

  timeBlink += rate * 3.0f;
  if (timeBlink >= TWO_PI * 10.0f) {
    timeBlink -= TWO_PI * 10.0f;
  }
}

void draw() {
  PFCanvas::setFrame(FRAME_W, FRAME_H);

  if (!valField) {
    PFCanvas::present();
    return;
  }

  for (int i = 0; i < FRAME_W * FRAME_H; i++) {
    valField[i] = 0.0f;
  }

  const float t = timeWave;
  const float petals = param_petalCount;
  const float scale = param_floretScale;
  const float ampMult = param_swayAmp;
  constexpr float glow = 0.68f;

  for (int s = 0; s < SPIRE_COUNT; s++) {
    const Spire& sp = spires[s];
    const float totalHeight = sp.baseY - sp.tipY;
    constexpr int steps = 115;   // the original: 75; about one per row now
    constexpr float invSteps = 1.0f / (float)steps;

    for (int i = 0; i <= steps; i++) {
      float frac = (float)i * invSteps;
      float py = sp.baseY - frac * totalHeight;
      float bend = getSilkDisplacement(frac, sp, t, ampMult);
      float px = sp.x + bend;

      float stalkVal = 0.18f + frac * 0.18f;
      addVal(px, py, stalkVal);
      addVal(px + 1.0f, py, stalkVal * 0.7f);
    }

    constexpr int nodeCount = 13;   // the original: 11
    constexpr float invNodeCount = 1.0f / (float)nodeCount;

    for (int n = 0; n < nodeCount; n++) {
      float nFrac = 0.35f + ((float)n * invNodeCount) * 0.65f;
      float fy = sp.baseY - nFrac * totalHeight;

      float bend = getSilkDisplacement(nFrac, sp, t, ampMult);
      float microSway = PFMath::fastSin(t * 1.4f + (float)n * 0.5f) * 0.4f * ampMult * nFrac;
      float fx = sp.x + bend + microSway;

      float fRad = (1.5f + nFrac * 2.5f) * (scale * 0.45f) * 1.2f;   // a fifth larger
      int radLimit = (int)ceilf(fRad * 1.8f);
      float maxDistSq = (fRad * 1.7f) * (fRad * 1.7f);

      for (int dy = -radLimit; dy <= radLimit; dy++) {
        float fdy = (float)dy;
        float dySq = fdy * fdy;
        for (int dx = -radLimit; dx <= radLimit; dx++) {
          float fdx = (float)dx;
          float distSq = fdx * fdx + dySq;
          if (distSq <= maxDistSq) {
            float dist = sqrtf(distSq);
            float angle = PFMath::fastAtan2(fdy, fdx);
            float petalWave = 0.5f + 0.5f * PFMath::fastCos(angle * petals + t + (float)n);
            float denom = fRad * (0.8f + 0.6f * petalWave);
            float edgeDrop = 1.0f - dist / denom;
            if (edgeDrop < 0.0f) edgeDrop = 0.0f;

            if (edgeDrop > 0.05f) {
              float ringVal = PFMath::fastPow(edgeDrop, 1.3f) * (0.45f + 0.55f * glow);
              int px = PFMath::ifloor(fx + fdx);
              int py = PFMath::ifloor(fy + fdy);
              if (px >= 0 && px < FRAME_W && py >= 0 && py < FRAME_H) {
                int idx = py * FRAME_W + px;
                float clampedRing = PFMath::clamp01(ringVal);
                if (clampedRing > valField[idx]) {
                  valField[idx] = clampedRing;
                }
              }
            }
          }
        }
      }

      addVal(fx, fy, PFMath::clamp01(0.85f + glow * 0.15f));
      addVal(fx + 1.0f, fy, 0.7f * glow);
    }
  }

  for (int p = 0; p < 48; p++) {   // the original: 24, over half the width
    float fp = (float)p;
    float pyRaw = (float)(FRAME_H + 20) - PFMath::jsMod(timeSporeY + fp * 19.0f, (float)(FRAME_H + 30));
    float py = PFMath::jsMod(pyRaw, (float)FRAME_H);
    float px = PFMath::jsMod(fp * 17.0f + PFMath::fastSin(t + fp) * 12.0f + (float)FRAME_W, (float)FRAME_W);
    float pVal = 0.4f + 0.6f * PFMath::fastSin(fp + timeBlink);
    float val = pVal * glow;
    if (val < 0.0f) val = 0.0f;
    addVal(px, py, val);
  }

  for (int y = 0; y < FRAME_H; y++) {
    int rowOffset = y * FRAME_W;
    for (int x = 0; x < FRAME_W; x++) {
      float v = PFMath::clamp01(valField[rowOffset + x]);
      int li = (int)(v * 255.0f + 0.5f);
      PFCanvas::setPixel(x, y, RAMP_LUT[li][0], RAMP_LUT[li][1], RAMP_LUT[li][2]);
    }
  }

  PFCanvas::present();
}

} // namespace flower_0917