// ===== Patternflow pattern =====
// Title:    Slingshot Eight
// Author:   @engmung
// Source:   https://community.patternflow.work/community/p/daa5fb6dc5af452f
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the figure-eight lies along the
// square's diagonal instead of its height, so it is drawn 1.3 times larger (56 px per unit
// instead of 42.7), with a third more test particles (4000) and rings of 120 instead of 100,
// so the streams stay as dense over the larger picture. The frame's cut-offs (where
// particles die, where rings may be born, how far the view pulls back after a kick) are
// measured along the turned axes; the kick's spray scales with the particle count.
#pragma once
#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_params.h"
#include "src/core_math.h"
#include "src/core_mem.h"

// Restricted three-body problem: the Chenciner-Montgomery figure-eight with 3000 test particles.

namespace SlingshotEight {

const char* NAME = "Slingshot Eight";
const char* const KNOB_LABELS[4] = {"Perturb", "Speed", "Soften", "Mass"};
constexpr bool ABSOLUTE_READY = true;

// oklab ramp 0:#000000 0.3:#1d0b4a 0.65:#9d7fe0 0.9:#e8dcff 1:#ffffff
static const uint8_t RAMP_LUT[256][3] = {
  {0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},
  {0,0,0},{0,0,0},{0,0,1},{0,0,1},{0,0,1},{0,0,1},{0,0,1},{0,0,2},
  {0,0,2},{0,0,2},{1,0,3},{1,0,3},{1,0,4},{1,0,5},{1,0,5},{1,0,6},
  {1,0,7},{1,0,8},{2,0,9},{2,0,10},{2,1,11},{2,1,12},{2,1,13},{3,1,14},
  {3,1,16},{3,1,17},{4,1,18},{4,1,19},{4,1,20},{5,1,21},{5,1,23},{5,1,24},
  {6,2,25},{6,2,26},{7,2,28},{7,2,29},{8,2,30},{8,2,31},{9,2,33},{9,3,34},
  {10,3,35},{11,3,36},{11,3,38},{12,3,39},{13,3,40},{13,4,42},{14,4,43},{14,4,44},
  {15,4,46},{16,5,47},{16,5,48},{17,5,50},{18,5,51},{18,6,52},{19,6,54},{20,6,55},
  {20,6,56},{21,7,58},{22,7,59},{22,7,61},{23,8,62},{24,8,63},{24,8,65},{25,9,66},
  {26,9,68},{27,10,69},{27,10,70},{28,10,72},{29,11,73},{30,12,75},{31,13,76},{32,14,78},
  {33,16,79},{34,17,81},{35,18,82},{37,20,84},{38,21,86},{39,22,87},{40,23,89},{42,25,90},
  {43,26,92},{44,27,93},{45,28,95},{47,30,97},{48,31,98},{49,32,100},{51,33,101},{52,35,103},
  {53,36,105},{54,37,106},{56,38,108},{57,40,109},{58,41,111},{60,42,113},{61,43,114},{62,45,116},
  {64,46,117},{65,47,119},{67,48,121},{68,50,122},{69,51,124},{71,52,126},{72,53,127},{74,55,129},
  {75,56,131},{76,57,132},{78,58,134},{79,60,136},{81,61,137},{82,62,139},{83,63,141},{85,65,142},
  {86,66,144},{88,67,146},{89,69,147},{91,70,149},{92,71,151},{94,72,152},{95,74,154},{97,75,156},
  {98,76,158},{100,78,159},{101,79,161},{103,80,163},{104,81,164},{106,83,166},{107,84,168},{109,85,170},
  {110,87,171},{112,88,173},{113,89,175},{115,91,176},{116,92,178},{118,93,180},{119,95,182},{121,96,183},
  {122,97,185},{124,99,187},{126,100,189},{127,101,190},{129,103,192},{130,104,194},{132,105,196},{133,107,198},
  {135,108,199},{137,109,201},{138,111,203},{140,112,205},{141,114,206},{143,115,208},{144,116,210},{146,118,212},
  {148,119,214},{149,120,215},{151,122,217},{153,123,219},{154,125,221},{156,126,223},{157,127,224},{158,129,225},
  {159,130,225},{161,132,226},{162,133,226},{163,135,227},{164,136,227},{165,138,228},{166,139,228},{167,141,229},
  {168,142,230},{170,144,230},{171,145,231},{172,146,231},{173,148,232},{174,149,232},{175,151,233},{176,152,233},
  {178,154,234},{179,155,234},{180,157,235},{181,158,235},{182,160,236},{183,161,236},{184,163,237},{186,164,237},
  {187,165,238},{188,167,238},{189,168,239},{190,170,239},{191,171,240},{193,173,240},{194,174,241},{195,176,241},
  {196,177,242},{197,179,242},{199,180,243},{200,181,243},{201,183,244},{202,184,244},{203,186,244},{205,187,245},
  {206,189,245},{207,190,246},{208,192,246},{209,193,247},{211,194,247},{212,196,248},{213,197,248},{214,199,249},
  {215,200,249},{217,202,250},{218,203,250},{219,205,250},{220,206,251},{221,208,251},{223,209,252},{224,211,252},
  {225,212,253},{226,213,253},{228,215,254},{229,216,254},{230,218,254},{231,219,255},{232,221,255},{233,222,255},
  {234,223,255},{235,225,255},{236,226,255},{237,228,255},{238,229,255},{239,230,255},{240,232,255},{240,233,255},
  {241,234,255},{242,236,255},{243,237,255},{244,239,255},{245,240,255},{246,241,255},{247,243,255},{248,244,255},
  {249,245,255},{249,247,255},{250,248,255},{251,250,255},{252,251,255},{253,252,255},{254,254,255},{255,255,255},
};

constexpr int FRAME_W = 128;
constexpr int FRAME_H = 128;

constexpr int SE_N = 4000;
constexpr double SE_T = 6.32591398;   // period of the figure-eight choreography (G = m = 1)
constexpr int SE_TN = 1024;           // samples of the choreography table
constexpr double SE_BS = 0.03;        // body-body softening
constexpr float SE_TAU = 6.28318530718f;
constexpr int SE_RING = 120;
constexpr float SE_D = 0.70710678f;   // the view: world x runs up-right on screen, world y down-right
constexpr float SE_FLOOR = 0.47f;     // the tone curve's black floor (the original: 0.4): the square keeps more
                                      // of the faint outer streams than the narrow frame did

// knob state
static float sePert = 0.0f;
static float seSpeed = 2.0f;
static float seSoft = 0.01f;
static float seMass = 1.0f;

// particles (PSRAM)
static float* sePx = nullptr;
static float* sePy = nullptr;
static float* sePvx = nullptr;
static float* sePvy = nullptr;
static float* sePage = nullptr;
static float* sePlife = nullptr;
static float* sePw = nullptr;
static uint8_t* seAlive = nullptr;
static int32_t* seFree = nullptr;
static int seNfree = 0;
// choreography table [body][sample] -> x, y, vx, vy (PSRAM)
static float* seCT = nullptr;
// density accumulator (PSRAM)
static float* seH = nullptr;

static double bx[3], by[3], bvx[3], bvy[3];
static double bm[3] = {1, 1, 1};
static double bax[3], bay[3];
static uint32_t seLB[48];

// view (portrait frame: long axis = screen y)
static float seSc = 56.0f, seCx = 64.0f, seCy = 64.0f, seHw = 1.14f;   // seHw: half the frame, world units

static float seRS = 1.0f;
static double sePh = 0.0;
static float seBrk = 0.0f, seXf = -1.0f, seK1p = 0.0f;
static int seKstar = 0;
static float seH99 = 4.0f, seZm = 1.0f, seOx = 0.0f, seOy = 0.0f;
static bool seSeeded = false, seFollow = false, seDrawn = false, seRelist = false;
static int seFirst = 0;
static float sePump = 0.0f;
static float seDtLast = 1.0f / 60.0f;

// a world offset -> its larger extent along the screen's two axes (world units)
static inline float seScreenExt(float wx, float wy) {
  const float a = fabsf(wx + wy) * SE_D, b = fabsf(wy - wx) * SE_D;
  return a > b ? a : b;
}

static inline float seRand() { return (float)random(1 << 24) / 16777216.0f; }

// natural log for x > 0: exponent split + atanh series (error ~1e-7)
static inline float seLn(float x) {
  uint32_t b;
  memcpy(&b, &x, 4);
  int e = (int)((b >> 23) & 255) - 127;
  b = (b & 0x7FFFFFu) | 0x3F800000u;
  float m;
  memcpy(&m, &b, 4);
  if (m > 1.41421356f) { m *= 0.5f; e++; }
  float s = (m - 1.0f) / (m + 1.0f), s2 = s * s;
  float p = s * (2.0f + s2 * (0.6666667f + s2 * (0.4f + s2 * (0.2857143f + s2 * 0.2222222f))));
  return p + (float)e * 0.69314718f;
}

// 1/sqrt for r2 > 0: bit guess + two Newton steps
static inline float seRsqrt(float x) {
  uint32_t i;
  memcpy(&i, &x, 4);
  i = 0x5f3759dfu - (i >> 1);
  float y;
  memcpy(&y, &i, 4);
  float hx = 0.5f * x;
  y = y * (1.5f - hx * y * y);
  y = y * (1.5f - hx * y * y);
  return y;
}

static void bodyAcc(double soft2) {
  bax[0] = bax[1] = bax[2] = 0; bay[0] = bay[1] = bay[2] = 0;
  for (int i = 0; i < 3; i++) for (int j = i + 1; j < 3; j++) {
    double dx = bx[j] - bx[i], dy = by[j] - by[i];
    double r2 = dx * dx + dy * dy + soft2;
    double inv = 1.0 / (r2 * sqrt(r2));
    bax[i] += bm[j] * dx * inv; bay[i] += bm[j] * dy * inv;
    bax[j] -= bm[i] * dx * inv; bay[j] -= bm[i] * dy * inv;
  }
}

static void bodyStep(double h, double soft2) {   // kick-drift-kick leapfrog
  bodyAcc(soft2);
  for (int k = 0; k < 3; k++) { bvx[k] += bax[k] * h * 0.5; bvy[k] += bay[k] * h * 0.5; bx[k] += bvx[k] * h; by[k] += bvy[k] * h; }
  bodyAcc(soft2);
  for (int k = 0; k < 3; k++) { bvx[k] += bax[k] * h * 0.5; bvy[k] += bay[k] * h * 0.5; }
}

static void choreoIC() {
  bx[0] = 0.97000436; by[0] = -0.24308753; bx[1] = -bx[0]; by[1] = -by[0]; bx[2] = 0; by[2] = 0;
  bvx[2] = -0.93240737; bvy[2] = -0.86473146;
  bvx[0] = bvx[1] = -bvx[2] / 2; bvy[0] = bvy[1] = -bvy[2] / 2;
}

static void buildTable() {
  choreoIC();
  const int sub = 24;
  const double h = SE_T / (SE_TN * sub);
  for (int s = 0; s < SE_TN; s++) {
    for (int k = 0; k < 3; k++) {
      int o = (k * SE_TN + s) * 4;
      seCT[o] = (float)bx[k]; seCT[o + 1] = (float)by[k]; seCT[o + 2] = (float)bvx[k]; seCT[o + 3] = (float)bvy[k];
    }
    for (int q = 0; q < sub; q++) bodyStep(h, 0);
  }
}

static inline void kill(int i) { if (seAlive[i]) { seAlive[i] = 0; seFree[seNfree++] = i; } }

static bool emitRing(float ox, float oy, float ovx, float ovy, float M, float r) {
  if (seNfree < SE_RING) return false;
  float vf = (1.08f + 0.3f * seRand()) * (seRand() < 0.8f ? 1.0f : -1.0f);
  float v = sqrtf(M / r) * vf, off = seRand() * SE_TAU;
  float life = 4.5f + 8.0f * seRand();
  for (int j = 0; j < SE_RING; j++) {
    int i = seFree[--seNfree];
    float th = off + j * (SE_TAU / SE_RING);
    float c = PFMath::fastCos(th), s = PFMath::fastSin(th);
    sePx[i] = ox + r * c; sePy[i] = oy + r * s;
    sePvx[i] = ovx - v * s; sePvy[i] = ovy + v * c;
    sePage[i] = 0; sePw[i] = 1; sePlife[i] = life * (0.7f + 0.6f * seRand()); seAlive[i] = 1;
  }
  return true;
}

static void ring() {
  for (int i = 0; i < SE_N; i++) {
    float r = 0.22f + 0.06f * seRand(), th = seRand() * SE_TAU;
    float c = PFMath::fastCos(th), s = PFMath::fastSin(th), v = sqrtf(3.0f / r) * 0.9f;
    sePx[i] = r * c; sePy[i] = r * s; sePvx[i] = -v * s; sePvy[i] = v * c;
    sePage[i] = 0; sePw[i] = 1; sePlife[i] = 8.0f + 14.0f * seRand(); seAlive[i] = 1;
  }
  seNfree = 0;
}

static inline double gauss() { return (seRand() + seRand() + seRand() - 1.5) * 2.0; }

static void splat(float x0, float y0, float x1, float y1, float w) {
  const float sc = seSc * seZm;
  x0 -= seOx; x1 -= seOx; y0 -= seOy; y1 -= seOy;   // the camera follows a binary after a collapse
  const float k = sc * SE_D;
  const float ax = seCx + (x0 + y0) * k, ay = seCy + (y0 - x0) * k;
  const float cx = seCx + (x1 + y1) * k, cy = seCy + (y1 - x1) * k;
  const float dx = cx - ax, dy = cy - ay;
  const float adx = dx < 0 ? -dx : dx, ady = dy < 0 ? -dy : dy;
  const float m = adx > ady ? adx : ady;
  int n;
  if (!(m <= 20.0f)) n = 20;
  else { n = (int)m; if ((float)n < m) n++; }
  if (n < 1) n = 1;
  const float ww = w * (n > 1 ? 1.8f / (1.0f + 0.2f * n) : 1.0f);
  const float invn = 1.0f / n;
  for (int s = 1; s <= n; s++) {
    const float f = s * invn;
    const float fx = ax + dx * f - 0.5f, fy = ay + dy * f - 0.5f;
    if (!(fx >= 0.0f && fx < FRAME_W - 1 && fy >= 0.0f && fy < FRAME_H - 1)) continue;
    const int X = PFMath::ifloor(fx), Y = PFMath::ifloor(fy);
    if (X < 0 || X >= FRAME_W - 1 || Y < 0 || Y >= FRAME_H - 1) continue;
    const float u = fx - X, v = fy - Y;
    const int o = Y * FRAME_W + X;
    seH[o] += ww * (1 - u) * (1 - v); seH[o + 1] += ww * u * (1 - v);
    seH[o + FRAME_W] += ww * (1 - u) * v; seH[o + FRAME_W + 1] += ww * u * v;
  }
}

void setup() {
  PFMath::buildSinLUT();
  if (!seH) seH = PFMem::allocFloats(FRAME_W * FRAME_H);
  if (!sePx) sePx = PFMem::allocFloats(SE_N * 7);
  if (!seAlive) seAlive = (uint8_t*)PFMem::alloc(SE_N);
  if (!seFree) seFree = (int32_t*)PFMem::alloc(SE_N * sizeof(int32_t));
  if (!seCT) seCT = PFMem::allocFloats(3 * SE_TN * 4);
  if (sePx) {
    sePy = sePx + SE_N; sePvx = sePx + 2 * SE_N; sePvy = sePx + 3 * SE_N;
    sePage = sePx + 4 * SE_N; sePlife = sePx + 5 * SE_N; sePw = sePx + 6 * SE_N;
  }
  if (seCT) buildTable();
  // view: the eight along the diagonal, 3 world units from corner to corner as the
  // original's 3 units along its height, less a margin for the rings at its ends
  seSc = 56.0f;
  seCx = FRAME_W * 0.5f; seCy = FRAME_H * 0.5f;
  seHw = (FRAME_W * 0.5f) / seSc;
  if (seH) memset(seH, 0, sizeof(float) * FRAME_W * FRAME_H);
  if (seAlive) memset(seAlive, 0, SE_N);
  sePh = 0; seBrk = 0; seXf = -1;
  seK1p = 0; seKstar = 0; seH99 = 4; seZm = 1; seOx = 0; seOy = 0;
  seSeeded = false; seFirst = 0; seFollow = false; seDrawn = false; seRelist = false;
  sePump = 0; seDtLast = 1.0f / 60.0f; seNfree = 0;
  choreoIC(); bm[0] = bm[1] = bm[2] = 1;
}

static inline bool seReady() { return seH && sePx && seAlive && seFree && seCT; }

void update(float dt, const InputFrame& input) {
  PFParams::apply(input, 0, &sePert, 0.0f, 0.25f, 0.005f);
  PFParams::apply(input, 1, &seSpeed, 0.6f, 3.0f, 0.05f);
  PFParams::apply(input, 2, &seSoft, 0.01f, 0.15f, 0.003f);
  PFParams::apply(input, 3, &seMass, 1.0f, 1.6f, 0.013f);
  const float pert = sePert, speed = seSpeed, soft = seSoft, mass = seMass;
  seRS = 1.0f + soft * 6.0f;
  if (!seReady() || !seDrawn) return;
  if (!seSeeded) {
    seNfree = 0; memset(seAlive, 0, SE_N);
    for (int i = SE_N - 1; i >= 0; i--) seFree[seNfree++] = i;
    seSeeded = true;
  }
  bool press = false;
  for (int i = 0; i < 4; i++)
    if (input.btnPressed[i] && !input.paramAbsoluteActive[i] && !input.knobAudioActive[i]) press = true;
  if (press) ring();
  const float d = dt < 0.1f ? dt : 0.1f;
  seDtLast = d;
  sePump *= expf(-d / 0.18f);
  bm[0] = mass;

  // a rising Perturb (the kick) hurls one star along its velocity and sprays particles off it
  const float dk = pert - seK1p;
  seK1p = pert;
  if (dk > 0.004f) {
    const int k = seKstar;
    const double sp = sqrt(bvx[k] * bvx[k] + bvy[k] * bvy[k]) + 1e-6;
    const double J = dk * 4.0;
    const double dvx = bvx[k] / sp * J, dvy = bvy[k] / sp * J;
    bvx[k] += dvx; bvy[k] += dvy;
    const double tm = bm[0] + bm[1] + bm[2] - bm[k];
    for (int j = 0; j < 3; j++) if (j != k) { bvx[j] -= dvx * bm[k] / tm; bvy[j] -= dvy * bm[k] / tm; }
    // shock: every particle near the star is blown outward
    const float R = 0.9f, S = (float)(J * 2.2);
    const float bxk = (float)bx[k], byk = (float)by[k], fdvx = (float)dvx, fdvy = (float)dvy;
    for (int i = 0; i < SE_N; i++) {
      const float ex = sePx[i] - bxk, ey = sePy[i] - byk, r2 = ex * ex + ey * ey;
      if (r2 < R * R) {
        const float r = sqrtf(r2) + 1e-4f, f = S * (1 - r / R) / r;
        sePvx[i] += ex * f + fdvx; sePvy[i] += ey * f + fdvy;
      }
    }
    // two expanding shells sprayed off the star
    int nb = (int)(dk * 18000.0f * (SE_N / 3000.0f));
    if (nb > SE_N * 3 / 10) nb = SE_N * 3 / 10;
    const float off = seRand() * SE_TAU, v0 = 3.5f + 1.5f * seRand();
    const float bvxk = (float)bvx[k], bvyk = (float)bvy[k];
    for (int q = 0; q < nb; q++) {
      const int i = (int)random(SE_N);
      const float th = PFMath::jsMod(off + q * 2.39996f, SE_TAU), v = (q & 1) ? v0 : v0 * 1.45f;
      const float c = PFMath::fastCos(th), s = PFMath::fastSin(th);
      sePx[i] = bxk + 0.1f * c; sePy[i] = byk + 0.1f * s;
      sePvx[i] = bvxk + v * c; sePvy[i] = bvyk + v * s;
      sePage[i] = 0; sePw[i] = 2.5f; sePlife[i] = 5.0f + 6.0f * seRand();
      if (!seAlive[i]) { seAlive[i] = 1; seRelist = true; }
    }
    if (dk > 0.03f) seKstar = (k + 1) % 3;
    sePump += dk * 16.0f;
    if (sePump > 1.0f) sePump = 1.0f;
  }

  if (seRelist) {   // the spray revived dead slots: rebuild the free list
    seNfree = 0;
    for (int i = SE_N - 1; i >= 0; i--) if (!seAlive[i]) seFree[seNfree++] = i;
    seRelist = false;
  }
  // new rings, born around the stars in turn (weighted by mass)
  {
    if (seFirst < 1000) seFirst++;
    int lim = seFirst > 8 ? 4 : 5;
    int pa = 0, pb = 1; double best = 1e9;
    for (int i = 0; i < 3; i++) for (int j = i + 1; j < 3; j++) {
      const double q = (bx[i] - bx[j]) * (bx[i] - bx[j]) + (by[i] - by[j]) * (by[i] - by[j]);
      if (q < best) { best = q; pa = i; pb = j; }
    }
    const int pc = 3 - pa - pb;
    const double Mb = bm[pa] + bm[pb];
    const double gx = (bm[pa] * bx[pa] + bm[pb] * bx[pb]) / Mb, gy = (bm[pa] * by[pa] + bm[pb] * by[pb]) / Mb;
    const double ex = bx[pc] - gx, ey = by[pc] - gy;
    const bool binary = best < 0.2 && ex * ex + ey * ey > 1.21;
    const float hz = seHw / seZm;
    while (lim-- > 0) {
      const double u = seRand() * (bm[0] + bm[1] + bm[2]);
      const int k = u < bm[0] ? 0 : u < bm[0] + bm[1] ? 1 : 2;
      if (binary && k != pc) {
        // circumbinary rings
        const float r = ((float)sqrt(best) * 3.0f + 0.4f + 0.6f * seRand()) * seRS;
        const double gvx = (bm[pa] * bvx[pa] + bm[pb] * bvx[pb]) / Mb, gvy = (bm[pa] * bvy[pa] + bm[pb] * bvy[pb]) / Mb;
        if (!emitRing((float)gx, (float)gy, (float)gvx, (float)gvy, (float)Mb, r)) break;
        continue;
      }
      if (seScreenExt((float)bx[k] - seOx, (float)by[k] - seOy) > hz) continue;   // no rings around a star that left the frame
      if (!emitRing((float)bx[k], (float)by[k], (float)bvx[k], (float)bvy[k], (float)bm[k], (0.14f + 0.3f * seRand()) * seRS)) break;
    }
  }
  const float dts = d * speed * (float)(SE_T / 4.6);
  int ns;
  {
    const float q = dts / 0.028f;
    ns = (int)q; if ((float)ns < q) ns++;
  }
  ns = ns < 2 ? 2 : ns > 8 ? 8 : ns;
  const float h = dts / ns;
  const double bsx = SE_BS + soft * 0.5;
  const int nbs = 10;
  const double hb = (double)h / nbs, bs2 = bsx * bsx;
  const float e2 = soft * soft;
  const float lim = seHw * 1.2f / seZm, cox = seOx, coy = seOy;
  // zero-sum velocity noise on the stars
  const double amp = seFollow ? 0.0 : (double)pert * pert * 5.0 * sqrt((double)dts);
  const float cool = expf(-h / 0.35f);

  for (int s = 0; s < ns; s++) {
    // test particles feel the stars at time t (symplectic Euler)
    const float x0 = (float)bx[0], y0 = (float)by[0], x1 = (float)bx[1], y1 = (float)by[1], x2 = (float)bx[2], y2 = (float)by[2];
    const float m0 = (float)bm[0], m1 = (float)bm[1], m2 = (float)bm[2];
    for (int i = 0; i < SE_N; i++) {
      if (!seAlive[i]) continue;
      const float X = sePx[i], Y = sePy[i];
      float dx = x0 - X, dy = y0 - Y, r2 = dx * dx + dy * dy + e2, rs = seRsqrt(r2), iv = m0 * rs * rs * rs;
      float ax = dx * iv, ay = dy * iv;
      dx = x1 - X; dy = y1 - Y; r2 = dx * dx + dy * dy + e2; rs = seRsqrt(r2); iv = m1 * rs * rs * rs;
      ax += dx * iv; ay += dy * iv;
      dx = x2 - X; dy = y2 - Y; r2 = dx * dx + dy * dy + e2; rs = seRsqrt(r2); iv = m2 * rs * rs * rs;
      ax += dx * iv; ay += dy * iv;
      const float vx = sePvx[i] + ax * h, vy = sePvy[i] + ay * h;
      const float nx = X + vx * h, ny = Y + vy * h;
      sePvx[i] = vx; sePvy[i] = vy; sePx[i] = nx; sePy[i] = ny;
      sePage[i] += h;
      const float qa = (nx - cox + ny - coy) * SE_D, qb = (ny - coy - nx + cox) * SE_D;
      if (!(qa <= lim && qa >= -lim && qb <= lim && qb >= -lim) || sePage[i] > sePlife[i]) { kill(i); continue; }
      const float w = sePw[i];
      if (w > 1.0f) sePw[i] = 1.0f + (w - 1.0f) * cool;
      splat(X, Y, nx, ny, w);
    }
    for (int q = 0; q < nbs; q++) bodyStep(hb, bs2);
    if (amp > 0) {
      const double a = amp / sqrt((double)ns);
      const double gx0 = gauss() * a, gy0 = gauss() * a, gx1 = gauss() * a, gy1 = gauss() * a;
      const double gx2 = -(bm[0] * gx0 + bm[1] * gx1) / bm[2], gy2 = -(bm[0] * gy0 + bm[1] * gy1) / bm[2];
      bvx[0] += gx0; bvy[0] += gy0; bvx[1] += gx1; bvy[1] += gy1; bvx[2] += gx2; bvy[2] += gy2;
    }
  }
  sePh += dts;
  while (sePh >= SE_T) sePh -= SE_T;

  // keep the centre of mass at the origin
  {
    const double mt = bm[0] + bm[1] + bm[2];
    double cx = 0, cy = 0, vx = 0, vy = 0;
    for (int k = 0; k < 3; k++) { cx += bm[k] * bx[k]; cy += bm[k] * by[k]; vx += bm[k] * bvx[k]; vy += bm[k] * bvy[k]; }
    cx /= mt; cy /= mt; vx /= mt; vy /= mt;
    for (int k = 0; k < 3; k++) { bx[k] -= cx; by[k] -= cy; bvx[k] -= vx; bvy[k] -= vy; }
    const float fcx = (float)cx, fcy = (float)cy;
    for (int i = 0; i < SE_N; i++) { sePx[i] -= fcx; sePy[i] -= fcy; }
  }

  // breakup: a star wanders far from the centre -> after a while crossfade back to the choreography
  double dmax = 0;
  for (int k = 0; k < 3; k++) { const double r = sqrt(bx[k] * bx[k] + by[k] * by[k]); if (r > dmax) dmax = r; }
  float c = pert / 0.2f;
  { const float c2 = (mass - 1.35f) / 0.25f; if (c2 > c) c = c2; }
  if (c > 1.0f) c = 1.0f;
  int pa = 0, pb = 1; double best = 1e9;
  for (int i = 0; i < 3; i++) for (int j = i + 1; j < 3; j++) {
    const double q = (bx[i] - bx[j]) * (bx[i] - bx[j]) + (by[i] - by[j]) * (by[i] - by[j]);
    if (q < best) { best = q; pa = i; pb = j; }
  }
  const int pc = 3 - pa - pb;
  const double Mb = bm[pa] + bm[pb];
  const double gx = (bm[pa] * bx[pa] + bm[pb] * bx[pb]) / Mb, gy = (bm[pa] * by[pa] + bm[pb] * by[pb]) / Mb;
  const double ex = bx[pc] - gx, ey = by[pc] - gy;
  const bool follow = seXf < 0 && c >= 0.5f && best < 0.36 && ex * ex + ey * ey > 1.21;
  seFollow = follow;
  {
    const float a = 1.0f - expf(-d / (follow ? 0.12f : 0.5f));
    seOx += ((follow ? (float)gx : 0.0f) - seOx) * a; seOy += ((follow ? (float)gy : 0.0f) - seOy) * a;
  }
  const float hw = seHw;   // half-extent of the frame in world units, along either screen axis
  // the view pulls back while a star is thrown out
  {
    float mm = 0;
    for (int k = 0; k < 3; k++) {
      if (follow && k == pc) continue;
      const float e = seScreenExt((float)bx[k] - seOx, (float)by[k] - seOy);
      if (e > mm) mm = e;
    }
    float z = 0.8f * hw / (mm + 1e-3f);
    z = z > 1.0f ? 1.0f : z < 0.62f ? 0.62f : z;
    if (follow && z > 0.85f) z = 0.85f;
    seZm += (z - seZm) * (1.0f - expf(-d / 0.35f));
  }
  if (seXf < 0) {
    if (dmax > 1.3) seBrk += d;
    else { seBrk -= d * 0.5f; if (seBrk < 0) seBrk = 0; }
    bool off = false;   // a star beyond even the zoomed-out frame
    for (int k = 0; k < 3; k++)
      if (!(follow && k == pc) && seScreenExt((float)bx[k] - seOx, (float)by[k] - seOy) > hw / 0.62f) off = true;
    const bool reset = c < 0.5f ? (seBrk > 1.3f || dmax > 1.75)
      : follow ? seBrk > 1.3f + 5.0f * c : (seBrk > 1.3f + 2.5f * c || off);
    if (reset) { seXf = 0; seBrk = 0; }
  } else {
    seXf += d / 0.9f;
    const double f = sePh / SE_T * SE_TN;
    int i0 = (int)f;
    if (i0 < 0) i0 = 0;
    if (i0 >= SE_TN) i0 = SE_TN - 1;
    const int i1 = (i0 + 1) % SE_TN;
    const double fr = f - i0;
    const double a = seXf >= 1 ? 1.0 : 1.0 - exp(-d / 0.22);
    for (int k = 0; k < 3; k++) {
      const int o0 = (k * SE_TN + i0) * 4, o1 = (k * SE_TN + i1) * 4;
      const double tx = seCT[o0] + (seCT[o1] - seCT[o0]) * fr, ty = seCT[o0 + 1] + (seCT[o1 + 1] - seCT[o0 + 1]) * fr;
      const double tvx = seCT[o0 + 2] + (seCT[o1 + 2] - seCT[o0 + 2]) * fr, tvy = seCT[o0 + 3] + (seCT[o1 + 3] - seCT[o0 + 3]) * fr;
      bx[k] += (tx - bx[k]) * a; by[k] += (ty - by[k]) * a;
      bvx[k] += (tvx - bvx[k]) * a; bvy[k] += (tvy - bvy[k]) * a;
    }
    if (seXf >= 1) seXf = -1;
  }
  // a star that blew up numerically would poison everything: re-form the eight
  for (int k = 0; k < 3; k++)
    if (!(bx[k] == bx[k]) || !(by[k] == by[k]) || !(bvx[k] == bvx[k]) || !(bvy[k] == bvy[k])) { choreoIC(); sePh = 0; break; }
}

// density -> 0..1 value (the JS tone curve)
static inline float seTone(float v, float inv, float fl, float fs, float lin) {
  float t = seLn(1.0f + v) * inv;
  t = (t - fl) * fs;
  return t <= 0.0f ? 0.0f : t > 1.0f ? 1.0f : t * t * (1.8f - 0.8f * t) * (1.0f - lin) + t * lin;
}

static inline void sePut(int x, int y, float t) {
  t = PFMath::clamp01(t);
  const int li = (int)(t * 255.0f + 0.5f);
  PFCanvas::setPixel(x, y, RAMP_LUT[li][0], RAMP_LUT[li][1], RAMP_LUT[li][2]);
}

void draw() {
  PFCanvas::setFrame(FRAME_W, FRAME_H);
  if (!seReady()) { PFCanvas::present(); return; }
  seDrawn = true;
  const int n = FRAME_W * FRAME_H;
  float* hh = seH;
  // 99th percentile of the density, from a log-binned count
  memset(seLB, 0, sizeof(seLB));
  int cnt = 0;
  for (int q = 0; q < n; q += 2) {
    const float v = hh[q];
    if (v > 0.05f) {
      int b = (int)(seLn(v) * 4.0f + 12.0f);
      b = b < 0 ? 0 : b > 47 ? 47 : b;
      seLB[b]++; cnt++;
    }
  }
  float target = 4.0f;
  if (cnt > 20) {
    uint32_t acc = 0;
    const float lim = cnt * 0.008f;
    for (int b = 47; b >= 0; b--) { acc += seLB[b]; if ((float)acc >= lim) { target = expf((b + 0.5f - 12.0f) / 4.0f); break; } }
  }
  if (target < 2.0f) target = 2.0f;
  seH99 += (target - seH99) * 0.12f;
  const float lnh = seLn(1.0f + seH99);
  const float inv = 1.0f / lnh;
  // a kick opens the exposure: the black floor drops and the faint streams light up
  const float pm = sePump, fl = SE_FLOOR * (1.0f - 0.5f * pm), fs = 1.0f / (1.0f - fl), lin = 0.5f * pm;
  const float vthr = expf(fl * lnh) - 1.0f;   // below this the tone curve is black
  for (int y = 0; y < FRAME_H; y++) {
    const float* row = hh + y * FRAME_W;
    for (int x = 0; x < FRAME_W; x++) {
      const float v = row[x];
      if (v <= vthr) { PFCanvas::setPixel(x, y, RAMP_LUT[0][0], RAMP_LUT[0][1], RAMP_LUT[0][2]); continue; }
      sePut(x, y, seTone(v, inv, fl, fs, lin));
    }
  }
  // the three stars as Plummer spheres: core radius = softening length (heavier star, wider core)
  const float sc = seSc * seZm, eps = seSoft;
  for (int k = 0; k < 3; k++) {
    const float wx = (float)bx[k] - seOx, wy = (float)by[k] - seOy;
    const float X = seCx + (wx + wy) * SE_D * sc, Y = seCy + (wy - wx) * SE_D * sc;
    if (!(X > -1000.0f && X < 1000.0f && Y > -1000.0f && Y < 1000.0f)) continue;
    float Rp = eps * 1.6f * sc * (float)sqrt(bm[k]);
    if (Rp < 1.5f) Rp = 1.5f;
    const float ir2 = 1.0f / (Rp * Rp);
    int ext = (int)(Rp * 2.2f);
    if ((float)ext < Rp * 2.2f) ext++;
    const int xc = PFMath::ifloor(X), yc = PFMath::ifloor(Y);
    const int y0 = yc - ext < 0 ? 0 : yc - ext, y1 = yc + ext > FRAME_H - 1 ? FRAME_H - 1 : yc + ext;
    const int x0 = xc - ext < 0 ? 0 : xc - ext, x1 = xc + ext > FRAME_W - 1 ? FRAME_W - 1 : xc + ext;
    for (int yy = y0; yy <= y1; yy++) {
      for (int xx = x0; xx <= x1; xx++) {
        const float ex = xx + 0.5f - X, ey = yy + 0.5f - Y;
        const float q = 1.0f / (1.0f + (ex * ex + ey * ey) * ir2), g = q * q * 1.4f;
        const float v = hh[yy * FRAME_W + xx];
        const float t = v > vthr ? seTone(v, inv, fl, fs, lin) : 0.0f;
        sePut(xx, yy, g > t ? (g > 1.0f ? 1.0f : g) : t);
      }
    }
  }
  // decay the exposure (about 12 % per 1/60 s); flush values far below the black floor
  const float keep = expf(seDtLast * 60.0f * -0.07257069f);
  for (int q = 0; q < n; q++) {
    const float v = hh[q] * keep;
    hh[q] = v < 1e-5f ? 0.0f : v;
  }
  PFCanvas::present();
}

} // namespace SlingshotEight