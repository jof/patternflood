// ===== Patternflow pattern =====
// Title:    SnowFall
// Author:   @engmung
// Source:   https://community.patternflow.work/community/p/a45354db83104580
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the same flight through falling
// snow, seen through a lens twice as long (fov 68, not 34) so the streaks and sparkles are
// drawn at twice the size, with the field of flakes squeezed to the square's view (it shows
// half the original's height of sky) and three times as many of them: FlakeCount runs
// 60..1000 (default 900, the original's 300) so the snow is as thick as it was on the
// narrow canvas, and thicker at the top of the knob. Tails take the brighter of what's
// there, so a near flake's streak isn't cut by a far one's, and the nearest pearls glint
// in a wider cross. New flakes start a little lower in the sky, so the square's lower
// third isn't left bare.
#pragma once

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_math.h"

namespace SnowFall {

const char* NAME = "SnowFall";
const char* const KNOB_LABELS[4] = {"FallSpeed", "FlakeCount", "FlutterAmt", "TrailLen"};

constexpr int FRAME_W = 128;
constexpr int FRAME_H = 128;
constexpr int MAX_FLAKES = 1000;
constexpr float COUNT_MIN = 60.0f;
constexpr float S = 2.0f;               // the picture's scale against the original
constexpr float SKY = 0.5f;             // the flake field's height, against the original's

// Knob parameters
static float g_speed = 3.729f;
static float g_count = 900.0f;
static float g_flutter = 0.0f;
static float g_trail = 5.65f;

static float g_t = 0.0f;

struct Flake {
    float x;
    float y;
    float z;
    float phase;
    float freq;
    bool isPearl;
    float speedMult;
};

static Flake g_flakes[MAX_FLAKES];
static float vbuf[FRAME_W * FRAME_H];

static const uint8_t RAMP_LUT[256][3] = {
  {0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},{0,0,0},
  {0,0,0},{0,0,0},{0,0,0},{0,0,0},{1,1,1},{2,2,2},{4,4,4},{5,5,5},
  {6,6,6},{7,7,7},{9,9,9},{10,10,10},{11,11,11},{13,13,13},{14,14,14},{15,15,15},
  {16,16,16},{18,18,18},{19,19,19},{20,20,20},{21,21,21},{23,23,23},{24,24,24},{25,25,25},
  {27,27,27},{28,28,28},{29,29,29},{30,30,30},{32,32,32},{33,33,33},{34,34,34},{36,36,36},
  {37,37,37},{38,38,38},{39,39,39},{41,41,41},{42,42,42},{43,43,43},{45,45,45},{46,46,46},
  {47,47,47},{48,48,48},{50,50,50},{51,51,51},{52,52,52},{53,53,53},{55,55,55},{56,56,56},
  {57,57,57},{59,59,59},{60,60,60},{61,61,61},{62,62,62},{64,64,64},{65,65,65},{66,66,66},
  {68,68,68},{69,69,69},{70,70,70},{71,71,71},{73,73,73},{74,74,74},{75,75,75},{77,77,77},
  {78,78,78},{79,79,79},{80,80,80},{82,82,82},{83,83,83},{84,84,84},{86,86,86},{87,87,87},
  {88,88,88},{89,89,89},{91,91,91},{92,92,92},{93,93,93},{94,94,94},{96,96,96},{97,97,97},
  {98,98,98},{100,100,100},{101,101,101},{102,102,102},{103,103,103},{105,105,105},{106,106,106},{107,107,107},
  {109,109,109},{110,110,110},{111,111,111},{112,112,112},{114,114,114},{115,115,115},{116,116,116},{118,118,118},
  {119,119,119},{120,120,120},{121,121,121},{123,123,123},{124,124,124},{125,125,125},{126,126,126},{128,128,128},
  {129,129,129},{130,130,130},{132,132,132},{133,133,133},{134,134,134},{135,135,135},{137,137,137},{138,138,138},
  {139,139,139},{141,141,141},{142,142,142},{143,143,143},{144,144,144},{146,146,146},{147,147,147},{148,148,148},
  {150,150,150},{151,151,151},{152,152,152},{153,153,153},{155,155,155},{156,156,156},{157,157,157},{158,158,158},
  {160,160,160},{161,161,161},{162,162,162},{164,164,164},{165,165,165},{166,166,166},{167,167,167},{169,169,169},
  {170,170,170},{171,171,171},{173,173,173},{174,174,174},{175,175,175},{176,176,176},{178,178,178},{179,179,179},
  {180,180,180},{182,182,182},{183,183,183},{184,184,184},{185,185,185},{187,187,187},{188,188,188},{189,189,189},
  {190,190,190},{192,192,192},{193,193,193},{194,194,194},{196,196,196},{197,197,197},{198,198,198},{199,199,199},
  {201,201,201},{202,202,202},{203,203,203},{205,205,205},{206,206,206},{207,207,207},{208,208,208},{210,210,210},
  {211,211,211},{212,212,212},{214,214,214},{215,215,215},{216,216,216},{217,217,217},{219,219,219},{220,220,220},
  {221,221,221},{223,223,223},{224,224,224},{225,225,225},{226,226,226},{228,228,228},{229,229,229},{230,230,230},
  {231,231,231},{233,233,233},{234,234,234},{235,235,235},{237,237,237},{238,238,238},{239,239,239},{240,240,240},
  {242,242,242},{243,243,243},{244,244,244},{246,246,246},{247,247,247},{248,248,248},{249,249,249},{251,251,251},
  {252,252,252},{253,253,253},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},
  {255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},
  {255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},
  {255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},
  {255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},
  {255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},{255,255,255},
};

static uint32_t g_seed = 12345u;
static float randomFloat(float minVal, float maxVal) {
    g_seed = g_seed * 1664525u + 1013904223u;
    return minVal + (float)(g_seed >> 8) * (1.0f / 16777216.0f) * (maxVal - minVal);
}

void setup() {
    PFMath::buildSinLUT();
    for (int i = 0; i < MAX_FLAKES; i++) {
        g_flakes[i].x = (randomFloat(0.0f, 1.0f) - 0.5f) * 150.0f;
        g_flakes[i].y = (randomFloat(0.0f, 1.0f) - 0.5f) * 300.0f * SKY;
        g_flakes[i].z = randomFloat(0.0f, 1.0f) * 100.0f + 1.0f;
        g_flakes[i].phase = randomFloat(0.0f, 1.0f) * TWO_PI;
        g_flakes[i].freq = 3.0f + randomFloat(0.0f, 1.0f) * 4.0f;
        g_flakes[i].isPearl = (randomFloat(0.0f, 1.0f) < 0.25f);
        g_flakes[i].speedMult = 0.85f + randomFloat(0.0f, 1.0f) * 0.3f;
    }
}

void update(float dt, const InputFrame& input) {
    g_speed += input.knobDeltas[0] * 0.05f;
    g_speed = fminf(15.0f, fmaxf(1.0f, g_speed));

    // Two turns end to end, as near as the original's 5 a detent over 20..300 came to it
    g_count += input.knobDeltas[1] * ((float)MAX_FLAKES - COUNT_MIN) / 48.0f;
    g_count = fminf((float)MAX_FLAKES, fmaxf(COUNT_MIN, g_count));

    g_flutter += input.knobDeltas[2] * 0.05f;
    g_flutter = fminf(10.0f, fmaxf(0.0f, g_flutter));

    g_trail += input.knobDeltas[3] * 0.05f;
    g_trail = fminf(8.0f, fmaxf(1.0f, g_trail));

    g_t += dt * (g_speed * 0.2f);
    if (g_t > 200.0f * TWO_PI) {
        g_t -= 200.0f * TWO_PI;
    }

    // Always update every flake so their physical positions stay active when count increases
    for (int i = 0; i < MAX_FLAKES; i++) {
        Flake& f = g_flakes[i];
        f.z -= dt * g_speed * 20.0f * f.speedMult;
        f.y += dt * g_speed * 2.0f * SKY;

        if (f.z <= 0.8f || f.y > 160.0f * SKY) {
            f.z = 100.0f;
            f.x = (randomFloat(0.0f, 1.0f) - 0.5f) * 150.0f;
            f.y = (randomFloat(0.0f, 1.0f) - 0.72f) * 300.0f * SKY;   // the original: - 0.8
            f.isPearl = (randomFloat(0.0f, 1.0f) < 0.25f);
        }
    }
}

static inline void lift(int x, int y, float v) {
    if (x < 0 || x >= FRAME_W || y < 0 || y >= FRAME_H) return;
    float& p = vbuf[y * FRAME_W + x];
    if (v > p) p = v;
}

void draw() {
    PFCanvas::setFrame(FRAME_W, FRAME_H);

    const float cx = FRAME_W * 0.5f;
    const float cy = FRAME_H * 0.4f;
    constexpr float fov = 34.0f * S;

    // The faint frost underneath, its waves at the original's size against the picture
    for (int y = 0; y < FRAME_H; y++) {
        float cosTerm = PFMath::fastCos((float)y * (0.04f / S) - g_t * 1.2f);
        int rowIdx = y * FRAME_W;
        for (int x = 0; x < FRAME_W; x++) {
            float sinTerm = PFMath::fastSin((float)x * (0.08f / S) + g_t);
            vbuf[rowIdx + x] = (sinTerm * cosTerm) * 0.02f + 0.015f;
        }
    }

    const int activeCount = (int)fminf((float)MAX_FLAKES, floorf(g_count));
    const float maxTail = (7.0f + g_trail * 4.0f) * S;

    for (int i = 0; i < activeCount; i++) {
        const Flake& f = g_flakes[i];

        float flutterX = PFMath::fastSin(g_t * f.freq + f.phase) * (g_flutter * 1.8f);
        float flutterY = PFMath::fastCos(g_t * f.freq * 1.5f + f.phase) * (g_flutter * 0.9f * SKY);

        float k = fov / f.z;
        float px = cx + (f.x + flutterX) * k;
        float py = cy + (f.y + flutterY) * k;

        if (px < -40.0f || px > FRAME_W + 40.0f || py < -40.0f || py > FRAME_H + 40.0f) {
            continue;
        }

        float dx = px - cx;
        float dy = py - cy;
        float r = sqrtf(dx * dx + dy * dy);

        if (r < 0.5f) {
            lift((int)floorf(px), (int)floorf(py), 0.6f);
            continue;
        }

        float ux = dx / r;
        float uy = dy / r;

        float rawTail = r * (g_speed / (f.z + 5.0f)) * g_trail * 0.38f;
        float tailLen = maxTail * (1.0f - expf(-rawTail / maxTail));
        int steps = (int)fmaxf(1.0f, floorf(tailLen));

        float nearFade = fminf(1.0f, fmaxf(0.0f, (f.z - 0.8f) / 8.0f));
        float farFade = fminf(1.0f, (100.0f - f.z) / 25.0f);
        float edgeX = fminf(px, (float)FRAME_W - px);
        float edgeY = fminf(py, (float)FRAME_H - py);
        float edgeFade = fminf(1.0f, fmaxf(0.0f, fminf(edgeX, edgeY) / 5.0f));

        float brightness = nearFade * farFade * edgeFade;
        if (brightness <= 0.01f) continue;

        int headX = (int)floorf(px);
        int headY = (int)floorf(py);

        if (f.isPearl && f.z < 45.0f) {
            float coreBright = fminf(1.0f, brightness * 1.3f);
            lift(headX, headY, coreBright);
            lift(headX + 1, headY, coreBright * 0.4f);
            lift(headX - 1, headY, coreBright * 0.4f);
            lift(headX, headY + 1, coreBright * 0.4f);
            lift(headX, headY - 1, coreBright * 0.4f);
            if (f.z < 22.0f) {          // close enough to glint wider
                lift(headX + 2, headY, coreBright * 0.15f);
                lift(headX - 2, headY, coreBright * 0.15f);
                lift(headX, headY + 2, coreBright * 0.15f);
                lift(headX, headY - 2, coreBright * 0.15f);
                lift(headX + 1, headY + 1, coreBright * 0.12f);
                lift(headX - 1, headY - 1, coreBright * 0.12f);
                lift(headX + 1, headY - 1, coreBright * 0.12f);
                lift(headX - 1, headY + 1, coreBright * 0.12f);
            }
        }

        const float invSteps = 1.0f / (float)steps;
        for (int step = 0; step < steps; step++) {
            int sx = (int)floorf(px - ux * (float)step);
            int sy = (int)floorf(py - uy * (float)step);
            if (sx >= 0 && sx < FRAME_W && sy >= 0 && sy < FRAME_H) {
                float progress = (float)step * invSteps;
                float fade = brightness * PFMath::fastPow(1.0f - progress, 1.8f);
                lift(sx, sy, fminf(1.0f, 0.02f + fade));
            }
        }
    }

    for (int y = 0; y < FRAME_H; y++) {
        int rowIdx = y * FRAME_W;
        for (int x = 0; x < FRAME_W; x++) {
            float val = fminf(1.0f, fmaxf(0.0f, vbuf[rowIdx + x]));
            int li = (int)(val * 255.0f + 0.5f);
            PFCanvas::setPixel(x, y, RAMP_LUT[li][0], RAMP_LUT[li][1], RAMP_LUT[li][2]);
        }
    }

    PFCanvas::present();
}

} // namespace SnowFall
