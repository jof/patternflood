// ===== Patternflow pattern =====
// Title:    AizawaViscousInkPlume
// Author:   @engmung
// Source:   https://community.patternflow.work/community/p/a3ae492e7cc2413c
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the same plume, at its true
// shape. The original drew the attractor's x at 20.5 px a unit against its height's 44, to
// fit a 64-wide frame; here both get 38, the scale at which the plume's whole height
// (z from 2.7, where the cap no longer clips, down to -0.67) fills the square, so it opens
// out to about three-quarters of the width instead of standing in a narrow column. It
// covers 1.6 times the pixels, and carries three times the particles (2400, not 800), each
// leaving 0.6 of the original's mark: the ink is a little denser and finer-grained, and
// the vortex's swirls, crushed into vertical streaks in the narrow frame, read as curls.
#pragma once

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_mem.h"

namespace AizawaViscousInkPlume {

const char* NAME = "Aizawa Plume";
const char* const KNOB_LABELS[4] = {"Viscosity", "Downflow", "Vortex Core", "Thickness"};

constexpr int FRAME_W = 128;
constexpr int FRAME_H = 128;
constexpr int BUFFER_SIZE = FRAME_W * FRAME_H;
constexpr int COUNT = 2400;
// The attractor to the frame: one scale, the original's vertical one, both ways
constexpr float SCALE = 38.0f;                   // so z's 2.7..-0.67 fills the height
constexpr float INK = 0.6f;                       // each particle's mark, against the original's
constexpr float X0 = FRAME_W * 0.5f / SCALE;      // x = 0 at the middle, as the original's 1.55 * 20.5 put it
constexpr float Z_TOP = 2.7f;                      // the original: 2.6, which clipped the cap

// Knob ranges, defaults, and calibrated step sizes
constexpr float KNOB_VISCOSITY_MIN = 0.7f;
constexpr float KNOB_VISCOSITY_MAX = 1.05f;
constexpr float KNOB_VISCOSITY_STEP = 0.007f;

constexpr float KNOB_DOWNFLOW_MIN = 0.3f;
constexpr float KNOB_DOWNFLOW_MAX = 4.5f;
constexpr float KNOB_DOWNFLOW_STEP = 0.088f;

constexpr float KNOB_VORTEX_MIN = 1.5f;
constexpr float KNOB_VORTEX_MAX = 5.0f;
constexpr float KNOB_VORTEX_STEP = 0.073f;

constexpr float KNOB_THICKNESS_MIN = 0.5f;
constexpr float KNOB_THICKNESS_MAX = 3.0f;
constexpr float KNOB_THICKNESS_STEP = 0.052f;

static float knobViscosity = 0.7f;
static float knobDownflow  = 0.3f;
static float knobVortexCore = 5.0f;
static float knobThickness = 2.301f;

static float* buffer = nullptr;
static float* px = nullptr;
static float* py = nullptr;
static float* pz = nullptr;

static uint32_t rngState = 98712345u;
static float simTime = 0.0f;

// Color ramp (oklchShort; stops: 0.000:#000000, 0.837:#e100ff, 0.984:#ffffff; wrap off)
static const uint8_t RAMP_LUT[256][3] = {
  {0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},
  {0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,1},{1,0,1},{1,0,1},{1,0,1},
  {1,0,1},{1,0,2},{1,0,2},{2,0,2},{2,0,3},{2,0,3},{3,0,4},{3,0,4},
  {4,0,5},{4,0,5},{4,0,6},{5,0,7},{6,0,7},{6,0,8},{7,0,9},{8,0,10},
  {8,0,11},{9,0,12},{10,0,13},{11,0,14},{12,0,15},{13,0,16},{14,0,17},{15,0,18},
  {15,0,19},{16,0,20},{17,0,21},{18,0,22},{19,0,23},{20,0,24},{21,0,25},{22,0,27},
  {23,0,28},{24,0,29},{25,0,30},{26,0,31},{27,0,32},{28,0,33},{29,0,34},{30,0,35},
  {31,0,36},{32,0,38},{33,0,39},{34,0,40},{35,0,41},{36,0,42},{37,0,43},{38,0,45},
  {39,0,46},{40,0,47},{41,0,48},{42,0,49},{43,0,50},{44,0,52},{45,0,53},{46,0,54},
  {47,0,55},{48,0,56},{50,0,58},{51,0,59},{52,0,60},{53,0,61},{54,0,62},{55,0,64},
  {56,0,65},{57,0,66},{58,0,67},{59,0,69},{60,0,70},{62,0,71},{63,0,72},{64,0,74},
  {65,0,75},{66,0,76},{67,0,77},{68,0,79},{69,0,80},{71,0,81},{72,0,82},{73,0,84},
  {74,0,85},{75,0,86},{76,0,88},{77,0,89},{79,0,90},{80,0,92},{81,0,93},{82,0,94},
  {83,0,95},{84,0,97},{86,0,98},{87,0,99},{88,0,101},{89,0,102},{90,0,103},{92,0,105},
  {93,0,106},{94,0,107},{95,0,109},{96,0,110},{98,0,112},{99,0,113},{100,0,114},{101,0,116},
  {102,0,117},{104,0,118},{105,0,120},{106,0,121},{107,0,122},{108,0,124},{110,0,125},{111,0,127},
  {112,0,128},{113,0,129},{115,0,131},{116,0,132},{117,0,134},{118,0,135},{120,0,136},{121,0,138},
  {122,0,139},{123,0,141},{125,0,142},{126,0,143},{127,0,145},{128,0,146},{130,0,148},{131,0,149},
  {132,0,150},{133,0,152},{135,0,153},{136,0,155},{137,0,156},{139,0,158},{140,0,159},{141,0,161},
  {142,0,162},{144,0,163},{145,0,165},{146,0,166},{148,0,168},{149,0,169},{150,0,171},{151,0,172},
  {153,0,174},{154,0,175},{155,0,177},{157,0,178},{158,0,180},{159,0,181},{161,0,182},{162,0,184},
  {163,0,185},{165,0,187},{166,0,188},{167,0,190},{168,0,191},{170,0,193},{171,0,194},{172,0,196},
  {174,0,197},{175,0,199},{176,0,200},{178,0,202},{179,0,203},{180,0,205},{182,0,206},{183,0,208},
  {185,0,209},{186,0,211},{187,0,212},{189,0,214},{190,0,216},{191,0,217},{193,0,219},{194,0,220},
  {195,0,222},{197,0,223},{198,0,225},{199,0,226},{201,0,228},{202,0,229},{204,0,231},{205,0,232},
  {206,0,234},{208,0,236},{209,0,237},{210,0,239},{212,0,240},{213,0,242},{215,0,243},{216,0,245},
  {217,0,246},{219,0,248},{220,0,250},{222,0,251},{223,0,253},{224,0,254},{226,23,255},{227,43,255},
  {228,56,255},{229,67,255},{230,77,255},{231,85,255},{232,93,255},{233,101,255},{234,108,255},{234,114,255},
  {235,120,255},{236,127,255},{237,133,255},{238,138,255},{239,144,255},{240,149,255},{240,155,255},{241,160,255},
  {242,165,255},{243,170,255},{244,176,255},{244,181,255},{245,185,255},{246,190,255},{247,195,255},{247,200,255},
  {248,205,255},{249,210,255},{249,214,255},{250,219,255},{251,224,255},{251,228,255},{252,233,255},{253,237,255},
  {253,242,255},{254,246,255},{254,251,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255}
};

inline float lcgRand() {
  rngState = 1664525u * rngState + 1013904223u;
  return (float)rngState / 4294967296.0f;
}

void setup() {
  if (!buffer) buffer = PFMem::allocFloats(BUFFER_SIZE);
  if (!px) px = PFMem::allocFloats(COUNT);
  if (!py) py = PFMem::allocFloats(COUNT);
  if (!pz) pz = PFMem::allocFloats(COUNT);

  if (!buffer || !px || !py || !pz) return;

  memset(buffer, 0, BUFFER_SIZE * sizeof(float));
  rngState = 98712345u;

  for (int i = 0; i < COUNT; ++i) {
    px[i] = (lcgRand() - 0.5f) * 1.4f;
    py[i] = (lcgRand() - 0.5f) * 1.4f;
    pz[i] = 0.4f + lcgRand() * 2.2f;
  }

  // Pre-fill buffer
  for (int step = 0; step < 60; ++step) {
    for (int i = 0; i < COUNT; ++i) {
      float x = px[i];
      float y = py[i];
      float z = pz[i];

      const float dx = (z - 0.7f) * x - 3.5f * y;
      const float dy = 3.5f * x + (z - 0.7f) * y;
      const float dz = 0.6f + 0.95f * z - (z * z * z) * (1.0f / 3.0f) - (x * x + y * y) * (1.0f + 0.25f * z);

      x += dx * 0.014f;
      y += dy * 0.014f;
      z += dz * 0.014f;

      px[i] = x;
      py[i] = y;
      pz[i] = z;

      const int sx = (int)floorf((x + X0) * SCALE);
      const int sy = (int)floorf((Z_TOP - z) * SCALE);
      if (sx >= 0 && sx < FRAME_W && sy >= 0 && sy < FRAME_H) {
        buffer[sy * FRAME_W + sx] += 0.5f * INK;
      }
    }
  }
}

void update(float dt, const InputFrame& input) {
  if (!buffer || !px || !py || !pz) return;

  const float safeDt = fminf(fmaxf(dt, 0.001f), 0.1f);
  simTime += safeDt;
  if (simTime > TWO_PI) simTime -= TWO_PI;

  knobViscosity += input.knobDeltas[0] * KNOB_VISCOSITY_STEP;
  knobViscosity = fminf(fmaxf(knobViscosity, KNOB_VISCOSITY_MIN), KNOB_VISCOSITY_MAX);

  knobDownflow += input.knobDeltas[1] * KNOB_DOWNFLOW_STEP;
  knobDownflow = fminf(fmaxf(knobDownflow, KNOB_DOWNFLOW_MIN), KNOB_DOWNFLOW_MAX);

  knobVortexCore += input.knobDeltas[2] * KNOB_VORTEX_STEP;
  knobVortexCore = fminf(fmaxf(knobVortexCore, KNOB_VORTEX_MIN), KNOB_VORTEX_MAX);

  knobThickness += input.knobDeltas[3] * KNOB_THICKNESS_STEP;
  knobThickness = fminf(fmaxf(knobThickness, KNOB_THICKNESS_MIN), KNOB_THICKNESS_MAX);

  const float a = knobViscosity;
  const float speed = knobDownflow;
  const float d = knobVortexCore;

  constexpr float b = 0.7f;
  constexpr float c = 0.6f;
  constexpr float e = 0.25f;
  constexpr float f = 0.1f;

  const float fade = powf(0.87f, safeDt * 60.0f);
  for (int i = 0; i < BUFFER_SIZE; ++i) {
    buffer[i] *= fade;
  }

  const float h = 0.012f * speed;

  for (int i = 0; i < COUNT; ++i) {
    float x = px[i];
    float y = py[i];
    float z = pz[i];

    const float rSq = x * x + y * y;
    const float dx = (z - b) * x - d * y;
    const float dy = d * x + (z - b) * y;
    const float dz = c + a * z - (z * z * z) * (1.0f / 3.0f) - rSq * (1.0f + e * z) + f * z * (x * x * x);

    x += dx * h;
    y += dy * h;
    z += dz * h;

    if (isnan(x) || isnan(y) || isnan(z) || isinf(x) || isinf(y) || isinf(z) || z < -0.8f || (rSq + z * z) > 25.0f) {
      x = (lcgRand() - 0.5f) * 1.5f;
      y = (lcgRand() - 0.5f) * 0.5f;
      z = 2.4f + lcgRand() * 0.3f;
    }

    px[i] = x;
    py[i] = y;
    pz[i] = z;

    const int cx = (int)floorf((x + X0) * SCALE);
    const int cy = (int)floorf((Z_TOP - z) * SCALE);

    if (cx >= 0 && cx < FRAME_W && cy >= 0 && cy < FRAME_H) {
      const int idx = cy * FRAME_W + cx;
      buffer[idx] += 0.32f * INK;
      if (cx > 0) buffer[idx - 1] += 0.16f * INK;
      if (cx < FRAME_W - 1) buffer[idx + 1] += 0.16f * INK;
      if (cy > 0) buffer[idx - FRAME_W] += 0.16f * INK;
      if (cy < FRAME_H - 1) buffer[idx + FRAME_W] += 0.16f * INK;
    }
  }
}

void draw() {
  PFCanvas::setFrame(FRAME_W, FRAME_H);

  if (!buffer) {
    PFCanvas::present();
    return;
  }

  const float coeff = -0.38f * knobThickness;

  for (int y = 0; y < FRAME_H; ++y) {
    const int row = y * FRAME_W;
    for (int x = 0; x < FRAME_W; ++x) {
      float raw = buffer[row + x];
      if (isnan(raw) || isinf(raw) || raw < 0.0f) raw = 0.0f;

      float val = 1.0f - expf(raw * coeff);
      if (val < 0.0f) val = 0.0f;
      else if (val > 1.0f) val = 1.0f;

      float v = powf(val, 0.85f);
      if (v < 0.0f) v = 0.0f;
      else if (v > 1.0f) v = 1.0f;

      int li = (int)(v * 255.0f + 0.5f);
      if (li < 0) li = 0;
      else if (li > 255) li = 255;

      PFCanvas::setPixel(x, y, RAMP_LUT[li][0], RAMP_LUT[li][1], RAMP_LUT[li][2]);
    }
  }

  PFCanvas::present();
}

} // namespace AizawaViscousInkPlume