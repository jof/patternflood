#pragma once
#include <Arduino.h>
#include <math.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_params.h"
#include "src/core_mem.h"

// Solo Jazz: the 1990s paper-cup swash, improvised live, for playing like an instrument.
// A teal dry brush lays down the chord (one bar, its pressure on an attack/release envelope,
// each bristle running out of ink at its own rate), and a purple pen plays a zigzag solo
// over it: a walk on scale degrees in swung eighths, triplets or sixteenths that mostly
// turns back on itself. Both are crayon on toothy paper: ink is rub pressure, showing only
// where it beats the grain, so strokes are rough when fresh and wear into streaks as they
// fade. Each phrase lands where the paper is emptiest. The paper wraps round like the cup,
// so it tiles when you zoom out and never shows an edge when it spins.
// Knobs: Tempo (push: tap tempo, the tap is the downbeat); Jive (how wild the solo is and
// how hard the purple dances on the beat; push: a break on clean paper); Zoom (a third,
// tiled, to 3x; push: mirror off, mirror, kaleidoscope); Spin (either way, still in the
// middle, easing upright; push: cream paper or night).
//
// A line-for-line twin of solo_jazz.js: the same generator, hash and draws in the same
// order, so the device paints what Pattern Lab previews. Everything scales with the
// short side, so FRAME_W / FRAME_H may be any size (64 x 128 as shared, 128 x 128 too).
// knobLights() is extra, for hosts with lights in their knobs; the firmware ignores it.
//
// By Jonathan Lassoff. CC BY-SA 4.0.

namespace SoloJazz {

const char* NAME = "Solo Jazz";
const char* const KNOB_LABELS[4] = {"Tempo", "Jive", "Zoom", "Spin"};
constexpr bool ABSOLUTE_READY = true;

constexpr int FRAME_W = 64;
constexpr int FRAME_H = 128;
constexpr int SJ_N = FRAME_W * FRAME_H;

constexpr float SJ_BRUSH_BEATS = 4.0f, SJ_PEN_DELAY = 1.5f;
constexpr int SJ_PEN_BEATS = 4;
constexpr int SJ_MAX_LANES = 96, SJ_MAX_NOTES = 24;
constexpr float SJ_T_MAX = 1.45f, SJ_P_MAX = 1.4f;     // ink over 1 shows as solid: fading starts late
constexpr float SJ_SWING = 0.64f;
constexpr float SJ_NIB_C = 0.7071f, SJ_NIB_S = -0.7071f;  // the pen's nib, at 45 degrees
constexpr float SJ_PREROLL_BEATS = 7.0f;
// Crayon on paper: ink is rub pressure, and a pixel takes colour only where the pressure
// beats its paper tooth (fixed grain), so light strokes and fading ones break into specks.
constexpr uint32_t SJ_TOOTH_SEED = 0x1b873593u, SJ_TOOTH_SEED2 = 0xcc9e2d51u;
constexpr float SJ_TEAL_FLOOR = 0.45f, SJ_TEAL_TOOTH = 0.9f, SJ_PURPLE_FLOOR = 0.4f, SJ_PURPLE_TOOTH = 0.9f;
constexpr float SJ_GRIP = 0.5f;
constexpr float SJ_PAPER[3] = {242, 228, 198};
constexpr float SJ_PAPER_LEVEL = 0.8f;
constexpr float SJ_TEAL_LIGHT[3] = {64, 198, 204}, SJ_TEAL_DARK[3] = {10, 112, 148};
constexpr float SJ_PURPLE[3] = {96, 26, 176};
constexpr float SJ_SPIN_DEAD = 0.06f;    // about a detent either side of the middle: still
constexpr float SJ_TAP_WINDOW = 2.0f;    // seconds: taps further apart start a new count

// knobs, at the cards' start: mid-range
static float tempoKnob = 120.0f, jive = 0.5f, zoom = 0.5f, spin = 0.0f;
static float tempoS, jiveS, zoomS, spinS, paperS;
static bool press[4] = {false, false, false, false};
static float tempoAdj = 0.0f, tapAge = 10.0f, tapInt = 0.5f;
static int tapCount = 0;
static bool paperOn = true;
static int mirror = 0;
static float angle = 0.0f, beatF = 0.0f;
static int beatN = 0;
static float tapFlash = 0.0f, noteFlash = 0.0f;
static float wash = 0.0f;

static float* T = nullptr;      // teal ink
static float* Sh = nullptr;     // its shade, light 0 .. dark 1
static float* P = nullptr;      // purple ink
static float* tooth = nullptr;  // the paper's grain: per pixel, and in streaks along the strokes

static uint32_t rng = 0x2468ace1u;
static float S = 1.0f, fadeBeats = 20.0f, lastY = -1000.0f;

// the phrase
static float pb = 0.0f, phraseLen = 7.0f, dryP = 0.5f;
static bool hasBrush = true, hasPen = true;
static float hw, L, cx, cy, bend, wobA, wobF, wobP, dx, dy, nx, ny, bias, amp, hatchK, hatchP;
static uint32_t seed = 0, penSeed = 0;
static int nLanes = 0, nNotes = 0, lastNote = -1;
static float penX = -1e9f, penY = -1e9f, nib = 1.0f;

struct Lane { float load, dep, shade, t0, t1; uint32_t seed; };
struct Note { float t; int deg; float acc; bool rest; };
static Lane lanes[SJ_MAX_LANES];
static Note notes[SJ_MAX_NOTES];

static inline uint32_t hash32(uint32_t x) {
  x ^= x >> 16;
  x *= 0x7feb352du;
  x ^= x >> 15;
  x *= 0x846ca68bu;
  return x ^ (x >> 16);
}

static inline float h01(uint32_t s, int i) {
  return (float)hash32(s + (uint32_t)i * 0x9e3779b9u) * (1.0f / 4294967296.0f);
}

static inline float vnoise(uint32_t s, float t) {
  const float fi = floorf(t), f = t - fi;
  const int i = (int)fi;
  const float a = h01(s, i), b = h01(s, i + 1);
  return a + (b - a) * f * f * (3.0f - 2.0f * f);
}

static inline float h2(uint32_t s, int ix, int iy) {
  return (float)hash32(s + (uint32_t)ix * 0x9e3779b9u + (uint32_t)iy * 0x85ebca6bu) * (1.0f / 4294967296.0f);
}

// 2D value noise: across the brush (bristle clumps) by along the stroke.
static float vnoise2(uint32_t s, float x, float y) {
  const float fx0 = floorf(x), fy0 = floorf(y);
  const int ix = (int)fx0, iy = (int)fy0;
  float fx = x - fx0, fy = y - fy0;
  fx = fx * fx * (3.0f - 2.0f * fx);
  fy = fy * fy * (3.0f - 2.0f * fy);
  const float a = h2(s, ix, iy), b = h2(s, ix + 1, iy);
  const float c = h2(s, ix, iy + 1), d = h2(s, ix + 1, iy + 1);
  return a + (b - a) * fx + (c - a + (d - c - b + a) * fx) * fy;
}

static inline float smooth(float x) {
  return x <= 0.0f ? 0.0f : x >= 1.0f ? 1.0f : x * x * (3.0f - 2.0f * x);
}

static inline float clamp01(float x) {
  return x < 0.0f ? 0.0f : x > 1.0f ? 1.0f : x;
}

static inline int wrapI(int n, int m) {
  n %= m;
  return n < 0 ? n + m : n;
}

// -1 at whole numbers, +1 halfway: a zigzag
static inline float tri(float x) {
  return 1.0f - 4.0f * fabsf(x - floorf(x) - 0.5f);
}

static inline uint32_t nextU32() {
  uint32_t x = rng;
  x ^= x << 13;
  x ^= x >> 17;
  x ^= x << 5;
  rng = x;
  return x;
}

static inline float rnd() {
  return (float)(nextU32() >> 8) * (1.0f / 16777216.0f);
}

// Where the paper is emptiest, of six tries, and not on top of the last phrase.
static float pickY(float w) {
  float best = FRAME_H * 0.5f, bestScore = 1e30f;
  for (int k = 0; k < 6; k++) {
    const float y = FRAME_H * (0.1f + 0.8f * rnd());
    float score = fabsf(y - lastY) < w * 1.5f ? 1e6f : 0.0f;
    const int y0 = (int)floorf(y - w), y1 = (int)floorf(y + w);
    for (int yy = y0; yy <= y1; yy += 2) {
      const int row = wrapI(yy, FRAME_H) * FRAME_W;
      for (int x = 0; x < FRAME_W; x += 2) score += T[row + x] + P[row + x];
    }
    if (score < bestScore) { bestScore = score; best = y; }
  }
  return best;
}

static void newPhrase() {
  static const float RESTS[4] = {0.5f, 1.0f, 1.0f, 2.0f};
  pb = 0.0f;
  const float r = rnd();
  hasBrush = r >= 0.1f;                   // one in ten: the pen alone, a solo break
  hasPen = r < 0.1f || r >= 0.16f;        // and one in sixteen: the brush alone
  phraseLen = SJ_PEN_DELAY + SJ_PEN_BEATS + RESTS[(int)floorf(rnd() * 4.0f)];
  dryP = 0.15f + 0.7f * rnd();

  const float th = (rnd() * 2.0f - 1.0f) * 0.38f;
  const float dir = rnd() < 0.8f ? 1.0f : -1.0f;
  hw = S * (6.0f + rnd() * 3.0f);
  L = FRAME_W * (0.75f + rnd() * 0.3f) / cosf(th);    // under a turn of the wrapped paper
  cx = FRAME_W * (0.3f + rnd() * 0.4f);
  cy = pickY(hw);
  lastY = cy;
  bend = (rnd() * 2.0f - 1.0f) * 0.1f * L;
  wobA = S * (0.6f + rnd() * 1.2f);
  wobF = 0.8f + rnd() * 1.4f;
  wobP = rnd();
  dx = cosf(th) * dir; dy = sinf(th) * dir;
  nx = -dy; ny = dx;

  seed = nextU32();
  nLanes = (int)floorf(2.0f * hw / 0.55f) + 1;
  if (nLanes > SJ_MAX_LANES) nLanes = SJ_MAX_LANES;
  const float sf = 1.2f + rnd() * 1.6f;
  const float sp = rnd() * 6.2832f;
  const float hatchSign = rnd() < 0.5f ? -1.0f : 1.0f;
  hatchK = hatchSign * (0.6f + 0.6f * rnd());          // scribble: pressure in diagonal bands
  hatchP = S * (2.6f + 1.4f * rnd());
  penSeed = nextU32();
  for (int j = 0; j < nLanes; j++) {
    Lane& lane = lanes[j];
    const float u = -1.0f + 2.0f * j / (nLanes - 1);
    lane.load = 0.82f + 0.18f * rnd();
    lane.dep = 0.45f + 0.55f * rnd();
    lane.seed = nextU32();
    const float jitter = rnd() - 0.5f;
    lane.shade = clamp01(0.5f + 0.22f * sinf(u * 3.1416f * sf + sp) + jitter * 0.2f);
    lane.t0 = (0.05f + 0.03f * rnd()) * u * u;           // outer bristles touch down later
    lane.t1 = 1.0f - (0.06f + 0.06f * rnd()) * u * u;    // and lift sooner: a round start, a pointed tail
  }

  // The solo: a zigzag walk on scale degrees -6..6, one beat at a time.
  const float jv = jiveS;
  bias = (rnd() * 2.0f - 1.0f) * 0.3f * hw;
  amp = hw * (1.4f + 1.2f * jv) / 6.0f;
  int deg = (int)floorf((rnd() * 2.0f - 1.0f) * 2.0f + 0.5f);
  bool up = rnd() < 0.5f;
  int n = 0;
  for (int b = 0; b < SJ_PEN_BEATS; b++) {
    const float rs = rnd();
    const int sub = rs < 0.25f + 0.6f * jv ? 4 : rs < 0.45f + 0.5f * jv ? 3 : 2;
    for (int s = 0; s < sub; s++) {
      Note& note = notes[n++];
      note.t = (b + (sub == 2 ? (s == 0 ? 0.0f : SJ_SWING) : (float)s / sub)) / SJ_PEN_BEATS;
      note.deg = deg;
      note.acc = s == 0 ? (b % 2 == 0 ? 1.0f : 0.6f) : 0.0f;
      note.rest = n > 1 && b < SJ_PEN_BEATS - 1 && rnd() < 0.04f;
      int size;
      if (rnd() < 0.15f + 0.35f * jv) size = 4 + (int)floorf(rnd() * 3.0f);
      else size = rnd() < 0.5f ? 3 : 2;
      if (rnd() < 0.88f) up = !up;         // a zigzag: it nearly always turns back
      deg += up ? size : -size;
      if (deg > 6) deg = 12 - deg;
      if (deg < -6) deg = -12 - deg;
      if (deg > 6) deg = 6;
      if (deg < -6) deg = -6;
    }
  }
  Note& last = notes[n++];
  last.t = 1.0f; last.deg = deg; last.acc = 0.0f; last.rest = false;
  nNotes = n;
  lastNote = -1;
  penX = penY = -1e9f;
}

static inline float pathOff(float t) {
  const float s = t - 0.5f;
  return bend * (1.0f - 4.0f * s * s) + wobA * sinf(6.2832f * (wobF * t + wobP));
}

static void splat(float x, float y, float a, float shade) {
  const float fx0 = floorf(x), fy0 = floorf(y);
  const int ix = (int)fx0, iy = (int)fy0;
  const float fx = x - fx0, fy = y - fy0;
  for (int k = 0; k < 4; k++) {
    const int px = wrapI(ix + (k & 1), FRAME_W), py = wrapI(iy + (k >> 1), FRAME_H);
    const float wgt = ((k & 1) ? fx : 1.0f - fx) * ((k >> 1) ? fy : 1.0f - fy);
    const float aa = a * wgt;
    const int i = py * FRAME_W + px;
    const float t = T[i] + aa;
    T[i] = t > SJ_T_MAX ? SJ_T_MAX : t;
    const float m = aa * 2.0f;
    Sh[i] += (shade - Sh[i]) * (m > 1.0f ? 1.0f : m);
    const float q = P[i] - aa * 1.2f;     // fresh teal covers old purple
    P[i] = q > 0.0f ? q : 0.0f;
  }
}

static void paintBrush(float t0, float t1) {
  const float along = (t1 - t0) * L;
  int n = (int)ceilf(along / 0.45f);
  if (n < 1) n = 1;
  const float stepAlong = along / n;
  for (int i = 1; i <= n; i++) {
    const float t = t0 + (t1 - t0) * i / n;
    const float s = t - 0.5f, off0 = pathOff(t);
    const float x = cx + dx * s * L + nx * off0, y = cy + dy * s * L + ny * off0;
    const float att = t < 0.1f ? smooth(t / 0.1f) : 1.0f;
    const float rel = t > 0.78f ? smooth((1.0f - t) / 0.22f) : 1.0f;
    const float width = (0.4f + 0.6f * att) * (0.3f + 0.7f * rel);
    const float press = (0.75f + 0.25f * att) * (0.6f + 0.4f * rel);
    const float spacing = 2.0f * hw * width / (nLanes - 1);
    const float gain = 1.7f * stepAlong * spacing;
    const float tn = t * L / (4.5f * S), tc = t * L / (9.0f * S), te = t * L / (6.0f * S), ts = t * L / (14.0f * S);
    const float cu = hw / (1.4f * S);      // bristle clumps about 1.4 px wide
    for (int j = 0; j < nLanes; j++) {
      const Lane& lane = lanes[j];
      if (t < lane.t0 || t > lane.t1) continue;
      const float u = -1.0f + 2.0f * j / (nLanes - 1);
      const float hatch = 0.78f + 0.22f * sinf(6.2832f * (t * L + u * hw * hatchK) / hatchP);
      float ink = lane.load * press * hatch - dryP * lane.dep * t * 0.9f
        + (vnoise2(seed, (u + 1.0f) * cu, tc) - 0.5f) * (0.2f + 1.5f * dryP)
        + (vnoise(lane.seed, tn) - 0.5f) * 0.15f;
      const float edge = fabsf(u);
      if (edge > 0.7f) ink -= (edge - 0.7f) / 0.3f * (0.2f + 1.0f * vnoise2(seed ^ 0x5bd1e995u, (u + 1.0f) * cu, te));
      if (ink < 0.12f) continue;            // a dry bristle skips: paper shows through
      ink = 0.45f + ink;
      if (ink > 1.0f) ink = 1.0f;
      const float off = u * hw * width;
      const float shade = clamp01(lane.shade + (vnoise2(seed ^ 0x27d4eb2fu, (u + 1.0f) * cu * 0.6f, ts) - 0.5f) * 0.9f);
      splat(x + nx * off, y + ny * off, ink * gain, shade);
    }
  }
}

static void disc(float x, float y, float r, float pr) {
  const int x0 = (int)floorf(x - r - 1.0f), x1 = (int)ceilf(x + r + 1.0f);
  const int y0 = (int)floorf(y - r - 1.0f), y1 = (int)ceilf(y + r + 1.0f);
  for (int py = y0; py <= y1; py++) {
    for (int px = x0; px <= x1; px++) {
      const float ddx = px - x, ddy = py - y;
      const float c = r + 0.5f - sqrtf(ddx * ddx + ddy * ddy);
      if (c <= 0.0f) continue;
      const float v = (c > 1.0f ? 1.0f : c) * SJ_P_MAX * pr;
      const int i = wrapI(py, FRAME_H) * FRAME_W + wrapI(px, FRAME_W);
      if (v > P[i]) P[i] = v;
    }
  }
}

static void paintPen(float tp0, float tp1) {
  const float along = (tp1 - tp0) * 1.08f * L;
  int n = (int)ceilf(along / 0.12f);
  if (n < 1) n = 1;
  const float glide = 0.55f + 0.45f * jiveS;   // 0: notes joined by cosine glides, 1: straight, sharp corners
  for (int i = 1; i <= n; i++) {
    const float tp = tp0 + (tp1 - tp0) * i / n;
    int k = 0;
    while (k < nNotes - 2 && notes[k + 1].t <= tp) k++;
    const Note& a = notes[k];
    const Note& b = notes[k + 1];
    if (k != lastNote) {
      lastNote = k;
      if (!a.rest) noteFlash = 0.6f + 0.4f * a.acc;
    }
    const float f = clamp01((tp - a.t) / (b.t - a.t));
    const float cs = (1.0f - cosf(3.1416f * f)) * 0.5f;
    const float sm = cs + (f - cs) * glide;
    const float m = a.deg + (b.deg - a.deg) * sm;
    const float accent = a.acc * expf(-(tp - a.t) * SJ_PEN_BEATS * 6.0f);
    const float t = -0.04f + 1.08f * tp;
    const float s = t - 0.5f, off0 = pathOff(t);
    const float off = bias + m * amp;
    const float x = cx + dx * s * L + nx * off0 + nx * off;
    const float y = cy + dy * s * L + ny * off0 + ny * off;
    const float mx = x - penX, my = y - penY;
    const float len = sqrtf(mx * mx + my * my);
    if (penX > -1e8f && len > 1e-4f) nib = 0.6f + 0.6f * fabsf((my * SJ_NIB_C - mx * SJ_NIB_S) / len);
    else if (penX <= -1e8f) nib = 1.0f;
    penX = x; penY = y;
    if (a.rest) continue;
    const float taper = 0.35f + 0.65f * smooth(tp / 0.05f) * smooth((1.0f - tp) / 0.05f);
    const float pr = 0.8f + 0.4f * vnoise(penSeed, tp * 1.08f * L / (2.5f * S));   // the crayon skips
    disc(x, y, S * 1.1f * nib * (1.0f + 0.45f * accent) * taper, pr);
  }
}

static void step(float dt) {
  // The clicks: tap tempo, a break, the mirror, the paper.
  tapAge = tapAge + dt > 10.0f ? 10.0f : tapAge + dt;
  if (press[0]) {
    if (tapAge < SJ_TAP_WINDOW) {
      tapInt = tapCount > 0 ? 0.5f * tapInt + 0.5f * tapAge : tapAge;
      tapCount++;
      const float bpm = 60.0f / tapInt;
      tempoAdj = (bpm < 60.0f ? 60.0f : bpm > 180.0f ? 180.0f : bpm) - tempoKnob;
    } else {
      tapCount = 0;
    }
    tapAge = 0.0f;
    tapFlash = 1.0f;
    beatF = 0.0f; beatN = 0;              // the tap is the downbeat
  }
  if (press[1]) { wash = 1.0f; newPhrase(); }
  if (press[2]) mirror = (mirror + 1) % 3;
  if (press[3]) paperOn = !paperOn;
  for (int i = 0; i < 4; i++) press[i] = false;

  const float tempo = tempoKnob + tempoAdj;
  const float kk = dt * 3.0f > 1.0f ? 1.0f : dt * 3.0f;
  tempoS += ((tempo < 60.0f ? 60.0f : tempo > 180.0f ? 180.0f : tempo) - tempoS) * kk;
  jiveS += (jive - jiveS) * kk;
  zoomS += (zoom - zoomS) * kk;
  spinS += (spin - spinS) * kk;
  paperS += ((paperOn ? 1.0f : 0.0f) - paperS) * (dt * 2.0f > 1.0f ? 1.0f : dt * 2.0f);
  tapFlash = tapFlash - dt * 4.0f > 0.0f ? tapFlash - dt * 4.0f : 0.0f;
  noteFlash *= expf(-dt * 8.0f);

  const float bps = tempoS / 60.0f;
  beatF += dt * bps;
  if (beatF >= 1.0f) { beatF -= 1.0f; beatN = (beatN + 1) & 3; }

  if (fabsf(spinS) < SJ_SPIN_DEAD) {        // let go of the spin: ease back upright
    const float target = floorf(angle / 3.1416f + 0.5f) * 3.1416f;
    angle += (target - angle) * (dt * 2.5f > 1.0f ? 1.0f : dt * 2.5f);
  } else {
    angle += spinS * fabsf(spinS) * (6.2832f / 8.0f) * bps * dt;
  }
  if (angle > 3.1416f) angle -= 6.2832f;
  if (angle < -3.1416f) angle += 6.2832f;

  const float rate = bps / fadeBeats + (wash > 0.0f ? 3.0f : 0.0f);
  if (wash > 0.0f) wash -= dt;
  const float fade = expf(-dt * rate);
  for (int i = 0; i < SJ_N; i++) { T[i] *= fade; P[i] *= fade; }

  const float pb0 = pb;
  pb += dt * bps;
  if (hasBrush) {
    const float t0 = clamp01(pb0 / SJ_BRUSH_BEATS), t1 = clamp01(pb / SJ_BRUSH_BEATS);
    if (t1 > t0) paintBrush(t0, t1);
  }
  if (hasPen) {
    const float t0 = clamp01((pb0 - SJ_PEN_DELAY) / SJ_PEN_BEATS), t1 = clamp01((pb - SJ_PEN_DELAY) / SJ_PEN_BEATS);
    if (t1 > t0) paintPen(t0, t1);
  }
  if (pb >= phraseLen) newPhrase();
}

static bool buffersOk() { return T && Sh && P && tooth; }

void setup() {
  if (!T) T = PFMem::allocFloats(SJ_N);
  if (!Sh) Sh = PFMem::allocFloats(SJ_N);
  if (!P) P = PFMem::allocFloats(SJ_N);
  if (!tooth) tooth = PFMem::allocFloats(SJ_N);
  tempoKnob = 120.0f; jive = 0.5f; zoom = 0.5f; spin = 0.0f;
  tempoS = tempoKnob; jiveS = jive; zoomS = zoom; spinS = spin;
  for (int i = 0; i < 4; i++) press[i] = false;
  tempoAdj = 0.0f; tapAge = 10.0f; tapCount = 0; tapInt = 0.5f;
  paperOn = true; paperS = 1.0f;
  mirror = 0;
  angle = 0.0f;
  beatF = 0.0f; beatN = 0;
  tapFlash = 0.0f; noteFlash = 0.0f;
  wash = 0.0f;
  rng = 0x2468ace1u;
  S = (FRAME_W < FRAME_H ? FRAME_W : FRAME_H) / 64.0f;
  fadeBeats = 2.8f * (8.0f + 6.0f * FRAME_H / (64.0f * S));   // slow: a stroke spends its life wearing into the grain
  lastY = -1000.0f;
  if (!buffersOk()) return;
  for (int i = 0; i < SJ_N; i++) T[i] = Sh[i] = P[i] = 0.0f;
  for (int y = 0; y < FRAME_H; y++) {
    for (int x = 0; x < FRAME_W; x++) {
      const int i = y * FRAME_W + x;
      tooth[i] = 0.35f * h01(SJ_TOOTH_SEED, i) + 0.65f * vnoise2(SJ_TOOTH_SEED2, x * 0.35f, y * 1.1f);
    }
  }
  newPhrase();
  hasBrush = hasPen = true;               // open with the whole figure
  for (float b = 0.0f; b < SJ_PREROLL_BEATS; b += tempoS / 60.0f / 30.0f) step(1.0f / 30.0f);
}

void update(float dt, const InputFrame& input) {
  PFParams::apply(input, 0, &tempoKnob, 60.0f, 180.0f, 2.5f);
  PFParams::apply(input, 1, &jive, 0.0f, 1.0f, 0.020833f);
  PFParams::apply(input, 2, &zoom, 0.0f, 1.0f, 0.020833f);
  PFParams::apply(input, 3, &spin, -1.0f, 1.0f, 0.041667f);
  for (int i = 0; i < 4; i++) {
    if (input.btnPressed[i] && !input.paramAbsoluteActive[i] && !input.knobAudioActive[i]) press[i] = true;
  }
  if (!buffersOk()) return;
  step(dt > 0.1f ? 0.1f : dt);
}

void draw() {
  PFCanvas::setFrame(FRAME_W, FRAME_H);
  if (!buffersOk()) { PFCanvas::present(); return; }
  const float pa = SJ_PAPER_LEVEL * paperS;
  const float kick = expf(-beatF * 5.0f);
  const float zm = expf((zoomS - 0.5f) * 3.2f * 0.693147f) * (1.0f + 0.06f * jiveS * kick);
  const float ca = cosf(angle) / zm, sa = sinf(angle) / zm;
  const float jiveA = S * 3.2f * jiveS * (0.35f + 0.65f * kick);   // the purple dances on the beat
  const float jiveL = 6.0f * S, jiveShift = (beatN & 1) * 0.5f;
  for (int y = 0; y < FRAME_H; y++) {
    float sy = y + 0.5f - FRAME_H * 0.5f;
    if (mirror == 2) sy = fabsf(sy);
    for (int x = 0; x < FRAME_W; x++) {
      float sx = x + 0.5f - FRAME_W * 0.5f;
      if (mirror >= 1) sx = fabsf(sx);
      const float u = ca * sx + sa * sy + FRAME_W * 0.5f, v = -sa * sx + ca * sy + FRAME_H * 0.5f;
      const int iu = wrapI((int)floorf(u), FRAME_W);
      const int i = wrapI((int)floorf(v), FRAME_H) * FRAME_W + iu;
      const int j = wrapI((int)floorf(v + jiveA * tri(u / jiveL + jiveShift)), FRAME_H) * FRAME_W + iu;
      const float tc = clamp01((T[i] - SJ_TEAL_FLOOR - tooth[i] * SJ_TEAL_TOOTH) / SJ_GRIP);
      const float pc = clamp01((P[j] - SJ_PURPLE_FLOOR - tooth[j] * SJ_PURPLE_TOOTH) / SJ_GRIP), sh = Sh[i];
      const float grain = (h01(911u, y * FRAME_W + x) - 0.5f) * 10.0f * pa;
      float c[3];
      for (int ch = 0; ch < 3; ch++) {
        float val = SJ_PAPER[ch] * pa + grain;
        val += (SJ_TEAL_LIGHT[ch] + (SJ_TEAL_DARK[ch] - SJ_TEAL_LIGHT[ch]) * sh - val) * tc;
        val += (SJ_PURPLE[ch] - val) * pc;
        c[ch] = val < 0.0f ? 0.0f : val;
      }
      PFCanvas::setPixel(x, y, (uint8_t)(int)c[0], (uint8_t)(int)c[1], (uint8_t)(int)c[2]);
    }
  }
  PFCanvas::present();
}

// For knobs with lights (0..1 RGB each): k0 flashes teal on the beat, brightest on the
// downbeat, white on a tap; k1 flashes purple on every note the pen plays; k2 shows the
// mirror (white off, teal mirror, purple kaleidoscope), brighter the further from 1x;
// k3 is the paper's colour, pulsing as it spins.
void knobLights(float out[4][3]) {
  const float beat = expf(-beatF * 6.0f) * (beatN == 0 ? 1.0f : 0.55f);
  const float teal[3] = {0.25f, 0.78f, 0.8f}, purple[3] = {0.55f, 0.15f, 1.0f}, white[3] = {1.0f, 0.95f, 0.85f};
  const float cream[3] = {1.0f, 0.88f, 0.7f}, night[3] = {0.15f, 0.2f, 0.6f};
  const float* modes[3] = {white, teal, purple};
  const float zl = 0.2f + 0.8f * clamp01(fabsf(zoomS - 0.5f) * 2.0f);
  const float sl = 0.25f + 0.75f * fabsf(sinf(angle));
  for (int c = 0; c < 3; c++) {
    out[0][c] = clamp01(teal[c] * (0.12f + 0.88f * beat) + white[c] * tapFlash);
    out[1][c] = clamp01(purple[c] * (0.1f + 0.15f * jiveS + 0.75f * noteFlash));
    out[2][c] = clamp01(modes[mirror][c] * zl);
    out[3][c] = clamp01((cream[c] * paperS + night[c] * (1.0f - paperS)) * sl);
  }
}

}  // namespace SoloJazz
