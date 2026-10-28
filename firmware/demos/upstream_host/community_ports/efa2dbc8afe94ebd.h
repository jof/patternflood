// ===== Patternflow pattern =====
// Title:    Pulsating Solar Flare
// Author:   @martinnlopez
// Source:   https://community.patternflow.work/community/p/efa2dbc8afe94ebd
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the same golden-angle spiral,
// finer and fuller. Points sit 2.1 * sqrt(i) out instead of 3 * sqrt(i), Density runs to
// 1500 (the original's 400 reached its 64-wide frame's edge), so the default disc is about
// twice as wide and the full knob reaches the corners. The pulse and the bloom scale with it.
#pragma once

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_math.h"

namespace PulsatingSolarFlare {

constexpr int FRAME_W = 128;
constexpr int FRAME_H = 128;
constexpr int MAX_POINTS = 1500;
constexpr float SPACING = 2.1f;         // the original: 3.0, on a 64-wide frame

const char* NAME = "Pulsating Solar Flare";
const char* const KNOB_LABELS[4] = {"Density", "Pulse Speed", "Wave Freq", "Glow"};

static float g_density = 400.0f;
static float g_pulseSpeed = 2.0f;
static float g_waveFreq = 10.0f;
static float g_glow = 1.0f;
static float g_t = 0.0f;

static float s_rBase[MAX_POINTS + 1];

void setup() {
    PFMath::buildSinLUT();
    for (int i = 0; i <= MAX_POINTS; i++) {
        s_rBase[i] = SPACING * sqrtf((float)i);
    }
}

void update(float dt, const InputFrame& input) {
    // Two turns end to end, as the original's knobs.
    g_density += input.knobDeltas[0] * (MAX_POINTS - 100) / 48.0f;
    g_density = fminf(fmaxf(g_density, 100.0f), (float)MAX_POINTS);

    g_pulseSpeed += input.knobDeltas[1] * 0.206f;
    g_pulseSpeed = fminf(fmaxf(g_pulseSpeed, 0.1f), 10.0f);

    g_waveFreq += input.knobDeltas[2] * 0.188f;
    g_waveFreq = fminf(fmaxf(g_waveFreq, 1.0f), 10.0f);

    g_glow += input.knobDeltas[3] * 0.021f;
    g_glow = fminf(fmaxf(g_glow, 0.0f), 1.0f);

    g_t += dt * g_pulseSpeed;

    constexpr float WRAP_PERIOD = 5.0f * TWO_PI;
    if (g_t >= WRAP_PERIOD) {
        g_t -= WRAP_PERIOD;
    }
}

static inline void dot(int x, int y, uint8_t r, uint8_t g) {
    if (x >= 0 && x < FRAME_W && y >= 0 && y < FRAME_H) PFCanvas::setPixel(x, y, r, g, 0);
}

void draw() {
    PFCanvas::setFrame(FRAME_W, FRAME_H);
    PFCanvas::clear();

    const float cx = FRAME_W * 0.5f;
    const float cy = FRAME_H * 0.5f;
    const int count = (int)g_density;
    const float amp = g_waveFreq * (SPACING / 3.0f) * 1.4f;      // the pulse, in proportion to the disc
    const float glow = g_glow;
    constexpr float GOLDEN_ANGLE = 2.39996f;
    const float t02 = g_t * 0.2f;

    for (int i = 1; i < count; i++) {
        const float rBase = s_rBase[i];
        // The wave travels out at the original's rate per point, whatever the spacing.
        const float pulse = PFMath::fastSin(rBase * (0.2f * 3.0f / SPACING) - g_t);
        const float radius = rBase + pulse * amp;
        const float angle = (float)i * GOLDEN_ANGLE + t02;

        const int x = (int)floorf(cx + PFMath::fastCos(angle) * radius);
        const int y = (int)floorf(cy + PFMath::fastSin(angle) * radius);
        if (x < 0 || x >= FRAME_W || y < 0 || y >= FRAME_H) continue;

        const float bri = 150.0f + 105.0f * PFMath::fastSin(pulse * g_waveFreq * 0.5f);
        const uint8_t r8 = (uint8_t)fminf(fmaxf(bri, 0.0f), 255.0f);
        const uint8_t g8 = (uint8_t)fminf(fmaxf(bri * glow, 0.0f), 255.0f);

        // Bloom first, so the core sits on top: a cross of half-red, wider the more Glow.
        if (glow > 0.5f) {
            const uint8_t bloomR = r8 / 2;
            dot(x + 1, y, bloomR, 0);
            dot(x, y + 1, bloomR, 0);
            if (glow > 0.8f) {
                dot(x - 1, y, bloomR / 2, 0);
                dot(x, y - 1, bloomR / 2, 0);
            }
        }
        dot(x, y, r8, g8);
    }

    PFCanvas::present();
}

} // namespace PulsatingSolarFlare
