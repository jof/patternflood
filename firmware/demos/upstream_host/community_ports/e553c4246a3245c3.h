// ===== Patternflow pattern =====
// Title:    Strange Ink
// Author:   @engmung
// Source:   https://community.patternflow.work/community/p/e553c4246a3245c3
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the same drifting attractor,
// drawn at its true shape and about twice as wide. The original squeezed it into its 64-wide
// frame at half the vertical scale; here both axes share one scale (22 px a unit, the
// original's 24 eased so the fullest figures just fit), so it spans the square. Twice the
// area takes twice the ink for the same depth of colour: Ink runs 1000..16000 (default
// 12000, the original's 6000 at full), and the extra points resolve filaments the narrow
// frame merged. The coefficients' slow drift starts 10 s along its course, in an open
// spell, so the first look is a full figure rather than the thin zigzag the original opens
// on; from there it breathes in and out (down to a single point) as the original does.
#pragma once

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_math.h"
#include "src/core_mem.h"

namespace Strange_Ink {

const char* NAME = "Strange Ink";
const char* const KNOB_LABELS[4] = {"Morph", "Ink", "Fade", "Warp"};

constexpr int FRAME_W = 128;
constexpr int FRAME_H = 128;

static const uint8_t RAMP_LUT[256][3] = {
  {0,0,0},{0,2,11},{0,4,22},{0,5,33},{0,7,44},{0,9,55},{0,11,66},{0,13,77},
  {0,14,88},{0,16,99},{0,18,110},{0,20,121},{0,22,132},{0,24,143},{0,25,154},{0,27,165},
  {0,29,176},{0,31,187},{0,33,198},{0,34,209},{0,36,220},{0,38,231},{0,40,242},{0,42,253},
  {1,42,254},{2,42,253},{3,41,252},{5,41,250},{6,41,249},{7,41,248},{9,41,246},{10,40,245},
  {11,40,244},{12,40,243},{14,40,241},{15,40,240},{16,39,239},{17,39,238},{19,39,236},{20,39,235},
  {21,39,234},{22,38,233},{24,38,231},{25,38,230},{26,38,229},{27,38,228},{29,37,226},{30,37,225},
  {31,37,224},{32,37,223},{34,36,221},{35,36,220},{36,36,219},{37,36,218},{39,36,216},{40,35,215},
  {41,35,214},{42,35,213},{44,35,211},{45,35,210},{46,34,209},{47,34,208},{49,34,206},{50,34,205},
  {51,34,204},{52,33,203},{54,33,201},{55,33,200},{56,33,199},{57,33,198},{59,32,196},{60,32,195},
  {61,32,194},{62,32,193},{64,32,191},{65,31,190},{66,31,189},{67,31,188},{69,31,186},{70,30,185},
  {71,30,184},{72,30,183},{74,30,181},{75,30,180},{76,29,179},{77,29,178},{79,29,176},{80,29,175},
  {81,29,174},{82,28,173},{84,28,171},{85,28,170},{86,28,169},{87,28,168},{89,27,166},{90,27,165},
  {91,27,164},{92,27,163},{94,27,161},{95,26,160},{96,26,159},{97,26,158},{99,26,156},{100,26,155},
  {101,25,154},{102,25,153},{104,25,151},{105,25,150},{106,25,149},{107,24,148},{109,24,146},{110,24,145},
  {111,24,144},{112,23,143},{114,23,141},{115,23,140},{116,23,139},{117,23,138},{119,22,136},{120,22,135},
  {121,22,134},{122,22,133},{124,22,131},{125,21,130},{126,21,129},{127,21,128},{129,21,126},{130,21,125},
  {131,20,124},{132,20,123},{134,20,121},{135,20,120},{136,20,119},{137,19,118},{139,19,116},{140,19,115},
  {141,19,114},{142,19,113},{144,18,111},{145,18,110},{146,18,109},{147,18,108},{149,18,106},{150,17,105},
  {151,17,104},{152,17,103},{154,17,101},{155,16,100},{156,16,99},{157,16,98},{159,16,96},{160,16,95},
  {161,15,94},{162,15,93},{164,15,91},{165,15,90},{166,15,89},{167,14,88},{169,14,86},{170,14,85},
  {171,14,84},{172,14,83},{174,13,81},{175,13,80},{176,13,79},{177,13,78},{179,13,76},{180,12,75},
  {181,12,74},{182,12,73},{184,12,71},{185,12,70},{186,11,69},{187,11,68},{189,11,66},{190,11,65},
  {191,11,64},{192,10,63},{194,10,61},{195,10,60},{196,10,59},{197,9,58},{199,9,56},{200,9,55},
  {201,9,54},{202,9,53},{204,8,51},{205,8,50},{206,8,49},{208,8,47},{209,8,46},{210,7,45},
  {211,7,44},{213,7,42},{214,7,41},{215,7,40},{216,6,39},{218,6,37},{219,6,36},{220,6,35},
  {221,6,34},{223,5,32},{224,5,31},{225,5,30},{226,5,29},{228,5,27},{229,4,26},{230,4,25},
  {231,4,24},{233,4,22},{234,3,21},{235,3,20},{236,3,19},{238,3,17},{239,3,16},{240,2,15},
  {241,2,14},{243,2,12},{244,2,11},{245,2,10},{246,1,9},{248,1,7},{249,1,6},{250,1,5},
  {251,1,4},{253,0,2},{254,0,1},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},
  {255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},
  {255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},
  {255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},{255,0,0},
};

static float* buf = nullptr;
static float morphVal = 1.371f;
constexpr float INK_MIN = 1000.0f, INK_MAX = 16000.0f;
static float inkVal = 12000.0f;
static float fadeVal = 0.8f;
static float warpVal = 0.978f;

static uint32_t rndSeed = 2718;
static float ph[4] = {0.7f, 2.1f, 4.4f, 1.3f};
static float px = 0.1f;
static float py = 0.0f;
static bool jump = false;

// The coefficients' slow drift starts 10 s along its course, at the start of an open spell,
// so the first look is a full figure (the original starts where one ends).
static float timeAccum = 10.0f;

inline float rnd() {
    rndSeed = rndSeed * 1664525u + 1013904223u;
    return (float)rndSeed / 4294967296.0f;
}

void setup() {
    PFMath::buildSinLUT();
    if (!buf) {
        buf = PFMem::allocFloats(FRAME_W * FRAME_H);
    }
}

void update(float dt, const InputFrame& input) {
    if (!buf) return;

    morphVal += input.knobDeltas[0] * 0.042f;
    if (morphVal < 0.0f) morphVal = 0.0f;
    if (morphVal > 2.0f) morphVal = 2.0f;

    inkVal += input.knobDeltas[1] * ((INK_MAX - INK_MIN) / 48.0f);    // two turns end to end, as the original
    if (inkVal < INK_MIN) inkVal = INK_MIN;
    if (inkVal > INK_MAX) inkVal = INK_MAX;

    fadeVal += input.knobDeltas[2] * 0.004f;
    if (fadeVal < 0.8f) fadeVal = 0.8f;
    if (fadeVal > 0.975f) fadeVal = 0.975f;

    warpVal += input.knobDeltas[3] * 0.029f;
    if (warpVal < 0.6f) warpVal = 0.6f;
    if (warpVal > 2.0f) warpVal = 2.0f;

    if (input.btnPressed[0]) jump = true;

    timeAccum += dt;
    if (timeAccum > 10000.0f * TWO_PI) timeAccum -= 10000.0f * TWO_PI;
}

void draw() {
    if (!buf) {
        PFCanvas::present();
        return;
    }

    PFCanvas::setFrame(FRAME_W, FRAME_H);

    // Fade trail buffer
    for (int i = 0; i < FRAME_W * FRAME_H; ++i) {
        buf[i] *= fadeVal;
    }

    // Jump to new attractor basin
    if (jump) {
        for (int i = 0; i < 4; ++i) {
            ph[i] = rnd() * 6.28318f;
        }
        px = rnd() - 0.5f;
        py = rnd() - 0.5f;
        jump = false;
    }

    // Time-varying attractor coefficients
    const float m = morphVal;
    const float warp = warpVal;
    const float a = -1.4f * warp + 0.9f * m * PFMath::fastSin(timeAccum * 0.47f + ph[0]);
    const float b =  1.6f * warp + 0.9f * m * PFMath::fastSin(timeAccum * 0.36f + ph[1]);
    const float c =  1.05f + 0.7f * m * PFMath::fastSin(timeAccum * 0.29f + ph[2]);
    const float d =  0.74f + 0.7f * m * PFMath::fastSin(timeAccum * 0.53f + ph[3]);

    const int n = (inkVal < 100.0f) ? 100 : (int)(inkVal + 0.5f);
    const float cx = FRAME_W * 0.5f;
    const float cy = FRAME_H * 0.5f;
    // One scale for both axes, near the original's vertical one (it had half that across)
    const float sx = (FRAME_H * 0.5f - 1.0f) / 2.8f;
    const float sy = sx;

    // Iterate attractor
    for (int j = 0; j < n; ++j) {
        const float sin_a_py = PFMath::fastSin(a * py);
        const float cos_a_px = PFMath::fastCos(a * px);
        const float sin_b_px = PFMath::fastSin(b * px);
        const float cos_b_py = PFMath::fastCos(b * py);

        float nx = sin_a_py + c * cos_a_px;
        float ny = sin_b_px + d * cos_b_py;

        if (fabsf(nx - px) + fabsf(ny - py) < 0.002f) {
            px = nx + (rnd() - 0.5f) * 0.2f;
            py = ny + (rnd() - 0.5f) * 0.2f;
            continue;
        }
        px = nx;
        py = ny;

        int ix = (int)(cx + py * sx);
        int iy = (int)(cy + px * sy);
        if (ix >= 0 && ix < FRAME_W && iy >= 0 && iy < FRAME_H) {
            int idx = iy * FRAME_W + ix;
            float v = buf[idx] + 0.22f;
            if (v > 1.0f) v = 1.0f;
            buf[idx] = v;
        }
    }

    // Render trail through colour ramp
    for (int y = 0; y < FRAME_H; ++y) {
        for (int x = 0; x < FRAME_W; ++x) {
            int i = y * FRAME_W + x;
            float t = buf[i];
            float v = t * t * (3.0f - 2.0f * t) * 1.15f;
            if (v > 1.0f) v = 1.0f;
            int li = (int)(v * 255.0f + 0.5f);
            if (li > 255) li = 255;
            else if (li < 0) li = 0;
            PFCanvas::setPixel(x, y, RAMP_LUT[li][0], RAMP_LUT[li][1], RAMP_LUT[li][2]);
        }
    }

    PFCanvas::present();
}

} // namespace Strange_Ink