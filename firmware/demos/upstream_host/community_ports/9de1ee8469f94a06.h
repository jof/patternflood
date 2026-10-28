// ===== Patternflow pattern =====
// Title:    Hyper-Radial Kaleidoscope Star
// Author:   @engmung
// Source:   https://community.patternflow.work/community/p/9de1ee8469f94a06
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the same 1-D reaction-diffusion
// ring drawn as a rotating phosphor star, finer and filling the square. The ring has 128
// cells instead of 64, so it carries twice as many spots and the star twice as many rays,
// each as fine as before. The star is round (radius 85 v + 5 in x and y alike), where the
// original stretched it 1.8 times in y to fill its 64 x 128 frame, and centred. Knobs and
// the click (reseed) as the original.
#pragma once

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_params.h"
#include "src/core_math.h"
#include "src/core_mem.h"

namespace HyperRadialKaleidoscopeStar {

const char* NAME = "Hyper Radial";
const char* const KNOB_LABELS[4] = {"Feed", "Petals", "Gain", "Decay"};
constexpr bool ABSOLUTE_READY = true;

constexpr int FRAME_W = 128;
constexpr int FRAME_H = 128;
constexpr int N = 128;                 // ring cells; the original: 64
constexpr float RADIUS_V = 85.0f;      // the original: 45 v + 3 in x, 1.8 times that in y
constexpr float RADIUS_0 = 5.0f;

// Color ramp lookup table (stops 0.000:#000000, 1.000:#ffffff; mode oklab; wrap off)
static const uint8_t RAMP_LUT[256][3] = {
  {0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},
  {0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{1,1,1},{1,1,1},
  {1,1,1},{1,1,1},{1,1,1},{1,1,1},{2,2,2},{2,2,2},{2,2,2},{2,2,2},
  {3,3,3},{3,3,3},{3,3,3},{4,4,4},{4,4,4},{5,5,5},{5,5,5},{6,6,6},
  {7,7,7},{7,7,7},{8,8,8},{9,9,9},{9,9,9},{10,10,10},{11,11,11},{12,12,12},
  {13,13,13},{13,13,13},{14,14,14},{15,15,15},{16,16,16},{17,17,17},{18,18,18},{18,18,18},
  {19,19,19},{20,20,20},{21,21,21},{22,22,22},{23,23,23},{24,24,24},{25,25,25},{26,26,26},
  {26,26,26},{27,27,27},{28,28,28},{29,29,29},{30,30,30},{31,31,31},{32,32,32},{33,33,33},
  {34,34,34},{35,35,35},{36,36,36},{37,37,37},{38,38,38},{38,38,38},{39,39,39},{40,40,40},
  {41,41,41},{42,42,42},{43,43,43},{44,44,44},{45,45,45},{46,46,46},{47,47,47},{48,48,48},
  {49,49,49},{50,50,50},{51,51,51},{52,52,52},{53,53,53},{54,54,54},{55,55,55},{56,56,56},
  {57,57,57},{58,58,58},{59,59,59},{60,60,60},{61,61,61},{62,62,62},{63,63,63},{64,64,64},
  {65,65,65},{66,66,66},{67,67,67},{68,68,68},{69,69,69},{71,71,71},{72,72,72},{73,73,73},
  {74,74,74},{75,75,75},{76,76,76},{77,77,77},{78,78,78},{79,79,79},{80,80,80},{81,81,81},
  {82,82,82},{83,83,83},{84,84,84},{85,85,85},{86,86,86},{88,88,88},{89,89,89},{90,90,90},
  {91,91,91},{92,92,92},{93,93,93},{94,94,94},{95,95,95},{96,96,96},{97,97,97},{99,99,99},
  {100,100,100},{101,101,101},{102,102,102},{103,103,103},{104,104,104},{105,105,105},{106,106,106},{107,107,107},
  {109,109,109},{110,110,110},{111,111,111},{112,112,112},{113,113,113},{114,114,114},{115,115,115},{117,117,117},
  {118,118,118},{119,119,119},{120,120,120},{121,121,121},{122,122,122},{123,123,123},{125,125,125},{126,126,126},
  {127,127,127},{128,128,128},{129,129,129},{130,130,130},{132,132,132},{133,133,133},{134,134,134},{135,135,135},
  {136,136,136},{137,137,137},{139,139,139},{140,140,140},{141,141,141},{142,142,142},{143,143,143},{144,144,144},
  {146,146,146},{147,147,147},{148,148,148},{149,149,149},{150,150,150},{152,152,152},{153,153,153},{154,154,154},
  {155,155,155},{156,156,156},{158,158,158},{159,159,159},{160,160,160},{161,161,161},{162,162,162},{164,164,164},
  {165,165,165},{166,166,166},{167,167,167},{169,169,169},{170,170,170},{171,171,171},{172,172,172},{173,173,173},
  {175,175,175},{176,176,176},{177,177,177},{178,178,178},{180,180,180},{181,181,181},{182,182,182},{183,183,183},
  {185,185,185},{186,186,186},{187,187,187},{188,188,188},{190,190,190},{191,191,191},{192,192,192},{193,193,193},
  {195,195,195},{196,196,196},{197,197,197},{198,198,198},{200,200,200},{201,201,201},{202,202,202},{203,203,203},
  {205,205,205},{206,206,206},{207,207,207},{208,208,208},{210,210,210},{211,211,211},{212,212,212},{213,213,213},
  {215,215,215},{216,216,216},{217,217,217},{219,219,219},{220,220,220},{221,221,221},{222,222,222},{224,224,224},
  {225,225,225},{226,226,226},{228,228,228},{229,229,229},{230,230,230},{231,231,231},{233,233,233},{234,234,234},
  {235,235,235},{237,237,237},{238,238,238},{239,239,239},{241,241,241},{242,242,242},{243,243,243},{244,244,244},
  {246,246,246},{247,247,247},{248,248,248},{250,250,250},{251,251,251},{252,252,252},{254,254,254},{255,255,255},
};

// Sqrt LUT for fast normalization of scalar field to ramp index
static uint8_t SQRT_LUT[256];

// Knobs
static float feedParam = 0.016f;
static float petalsParam = 2.0f;
static float gainParam = 8.0f;
static float phosphorDecayParam = 0.98f;

// State
static float u[N];
static float v[N];
static float nextU[N];
static float nextV[N];
static float* buf = nullptr;

static float t = 0.0f;
static uint32_t rngState = 987654321;

static float randF() {
  rngState = (1664525u * rngState + 1013904223u);
  return (float)rngState * (1.0f / 4294967296.0f);
}

static void reseed() {
  for (int i = 0; i < N; i++) {
    u[i] = 1.0f;
    v[i] = 0.0f;
  }
  const int c = N >> 1;
  for (int d = -3; d <= 3; d++) {
    u[c + d] = 0.35f;
    v[c + d] = 0.6f + 0.2f * randF();
  }
}

static void step1D(float feed) {
  constexpr float Du = 0.16f;
  constexpr float Dv = 0.08f;
  constexpr float k = 0.062f;
  constexpr float dtStep = 0.8f;

  for (int x = 0; x < N; x++) {
    const int left = (x - 1 + N) % N;
    const int right = (x + 1) % N;
    const float u0 = u[x];
    const float v0 = v[x];

    const float lapU = u[left] + u[right] - 2.0f * u0;
    const float lapV = v[left] + v[right] - 2.0f * v0;
    const float uvv = u0 * v0 * v0;

    const float next_u = u0 + (Du * lapU - uvv + feed * (1.0f - u0)) * dtStep;
    const float next_v = v0 + (Dv * lapV + uvv - (feed + k) * v0) * dtStep;

    if (!isfinite(next_u) || !isfinite(next_v)) {
      reseed();
      return;
    }
    nextU[x] = next_u < 0.0f ? 0.0f : (next_u > 1.0f ? 1.0f : next_u);
    nextV[x] = next_v < 0.0f ? 0.0f : (next_v > 1.0f ? 1.0f : next_v);
  }
  for (int x = 0; x < N; x++) {
    u[x] = nextU[x];
    v[x] = nextV[x];
  }
}

void setup() {
  PFMath::buildSinLUT();
  if (!buf) {
    buf = PFMem::allocFloats(FRAME_W * FRAME_H);
  }

  for (int i = 0; i < 256; i++) {
    float norm = (float)i / 255.0f;
    SQRT_LUT[i] = (uint8_t)(sqrtf(norm) * 255.0f + 0.5f);
  }

  reseed();
}

void update(float dt, const InputFrame& input) {
  if (!buf) return;

  PFParams::apply(input, 0, &feedParam, 0.016f, 0.044f, 0.001f);
  PFParams::apply(input, 1, &petalsParam, 2.0f, 14.0f, 0.25f);
  PFParams::apply(input, 2, &gainParam, 1.5f, 8.0f, 0.135f);
  PFParams::apply(input, 3, &phosphorDecayParam, 0.85f, 0.98f, 0.003f);

  if (input.btnPressed[0] && !input.paramAbsoluteActive[0] && !input.knobAudioActive[0]) {
    reseed();
  }

  const float dtClamped = dt > 0.1f ? 0.1f : dt;
  t += dtClamped;
  constexpr float TIME_PERIOD = 10.0f * TWO_PI; // t * 0.2 rotates periodically at 10*TWO_PI
  if (t >= TIME_PERIOD) {
    t -= TIME_PERIOD;
  }

  const float feed = feedParam;
  const int petals = (int)petalsParam;
  const float gain = gainParam;
  const float decay = phosphorDecayParam;

  for (int s = 0; s < 12; s++) {
    step1D(feed);
  }

  // Auto-revival
  float sumV = 0.0f;
  for (int i = 0; i < N; i++) {
    sumV += v[i];
  }
  if (sumV < 0.1f) {
    const int rx = ((int)(randF() * (float)(N - 24))) + 12;
    v[rx] = 0.6f;
    u[rx] = 0.3f;
  }

  // Phosphor decay
  constexpr int total = FRAME_W * FRAME_H;
  for (int i = 0; i < total; i++) {
    buf[i] *= decay;
  }

  constexpr float cx = 63.5f;
  constexpr float cy = 63.5f;
  const float rotOffset = t * 0.2f;
  const float petalAngleStep = TWO_PI / (float)petals;

  for (int i = 0; i < N; i++) {
    const float vVal = v[i];
    if (vVal > 0.02f) {
      const float baseAngle = ((float)i / (float)N) * TWO_PI;
      const float radius = vVal * RADIUS_V + RADIUS_0;
      const float energy = vVal * gain * 0.35f;
      const float energySide = energy * 0.4f;

      for (int p = 0; p < petals; p++) {
        const float angle = baseAngle + ((float)p * petalAngleStep) + rotOffset;
        const int px = (int)(cx + PFMath::fastCos(angle) * radius);
        const int py = (int)(cy + PFMath::fastSin(angle) * radius);

        if (px >= 1 && px < FRAME_W - 1 && py >= 1 && py < FRAME_H - 1) {
          const int idx = py * FRAME_W + px;
          buf[idx] += energy;
          buf[idx + 1] += energySide;
          buf[idx - 1] += energySide;
          buf[idx + FRAME_W] += energySide;
          buf[idx - FRAME_W] += energySide;
        }
      }
    }
  }
}

void draw() {
  PFCanvas::setFrame(FRAME_W, FRAME_H);
  if (!buf) {
    PFCanvas::present();
    return;
  }

  for (int y = 0; y < FRAME_H; y++) {
    const int yRow = y * FRAME_W;
    for (int x = 0; x < FRAME_W; x++) {
      float val = buf[yRow + x];
      val = val < 0.0f ? 0.0f : (val > 1.0f ? 1.0f : val);
      const int rawIdx = (int)(val * 255.0f + 0.5f);
      const int li = SQRT_LUT[rawIdx];
      PFCanvas::setPixel(x, y, RAMP_LUT[li][0], RAMP_LUT[li][1], RAMP_LUT[li][2]);
    }
  }

  PFCanvas::present();
}

} // namespace HyperRadialKaleidoscopeStar