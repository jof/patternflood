// ===== Patternflow pattern =====
// Title:    Bouncy Beholder
// Author:   @martinnlopez
// Source:   https://community.patternflow.work/community/p/f68385bf44a04a29
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the eyes are twice the size
// (a 32 px radius to the sclera's edge, not 16), and bounce 1.4 times as high from a floor
// set lower, so a single beholder fills the square as it filled the narrow original; the
// sway still spans the middle half. The extra pixels go into the eye: the sclera is shaded
// round, the red veins are finer, with thin capillaries branching in toward the rim, the
// iris has twice the fibres, a dark outer ring and a pale ring by the pupil, the highlight
// has a soft edge and a small second glint, and a blink shows the lid's dark rim.
#pragma once
#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_math.h"
#include "src/core_color.h"

namespace BouncyBeholder {

const char* NAME = "Bouncy Beholder";
const char* const KNOB_LABELS[4] = {"Count", "LookSpeed", "AnimSpeed", "Bounce"};

constexpr int FRAME_W = 128;
constexpr int FRAME_H = 128;
constexpr float S = 2.0f;               // the eye's size against the original's

// Knob parameter ranges and defaults
constexpr float COUNT_MIN = 1.0f;
constexpr float COUNT_MAX = 6.0f;
constexpr float COUNT_STEP = 0.104f;

constexpr float LOOKSPEED_MIN = 0.1f;
constexpr float LOOKSPEED_MAX = 10.0f;
constexpr float LOOKSPEED_STEP = 0.206f;

constexpr float ANIMSPEED_MIN = 0.1f;
constexpr float ANIMSPEED_MAX = 10.0f;
constexpr float ANIMSPEED_STEP = 0.206f;

constexpr float BOUNCE_MIN = 0.0f;
constexpr float BOUNCE_MAX = 1.0f;
constexpr float BOUNCE_STEP = 0.021f;

// Internal state
static float t = 0.0f;
static float countParam = 1.0f;
static float lookSpeedParam = 2.0f;
static float animSpeedParam = 10.0f;
static float bounceParam = 1.0f;

void setup() {
    PFMath::buildSinLUT();
}

void update(float dt, const InputFrame& input) {
    countParam     += input.knobDeltas[0] * COUNT_STEP;
    lookSpeedParam += input.knobDeltas[1] * LOOKSPEED_STEP;
    animSpeedParam += input.knobDeltas[2] * ANIMSPEED_STEP;
    bounceParam    += input.knobDeltas[3] * BOUNCE_STEP;

    if (countParam < COUNT_MIN) countParam = COUNT_MIN;
    if (countParam > COUNT_MAX) countParam = COUNT_MAX;
    if (lookSpeedParam < LOOKSPEED_MIN) lookSpeedParam = LOOKSPEED_MIN;
    if (lookSpeedParam > LOOKSPEED_MAX) lookSpeedParam = LOOKSPEED_MAX;
    if (animSpeedParam < ANIMSPEED_MIN) animSpeedParam = ANIMSPEED_MIN;
    if (animSpeedParam > ANIMSPEED_MAX) animSpeedParam = ANIMSPEED_MAX;
    if (bounceParam < BOUNCE_MIN) bounceParam = BOUNCE_MIN;
    if (bounceParam > BOUNCE_MAX) bounceParam = BOUNCE_MAX;

    // As the original: t wraps at 2 pi (every multiplier of it is then continuous but lookSpeed's)
    t += dt;
    if (t > TWO_PI) t -= TWO_PI;
}

static inline uint8_t c8(float v) { return (uint8_t)fmaxf(0.0f, fminf(255.0f, v)); }

void draw() {
    PFCanvas::setFrame(FRAME_W, FRAME_H);

    const int count = (int)fmaxf(1.0f, floorf(countParam));
    const float lookSpeed = lookSpeedParam;
    const float animSpeed = animSpeedParam;
    const float bounceAmt = bounceParam;

    const float fw = (float)FRAME_W;
    const float fh = (float)FRAME_H;
    const float halfW = fw * 0.5f;
    const float quarterW = fw * 0.25f;
    const float bounceHeight = fh * 0.2f * 1.4f * bounceAmt;

    // Background (dark fleshy/veiny purple)
    for (int y = 0; y < FRAME_H; y++) {
        for (int x = 0; x < FRAME_W; x++) {
            PFCanvas::setPixel(x, y, 25, 5, 15);
        }
    }

    for (int e = 0; e < count; e++) {
        // 1. Base position: rows as the original, the floor dropped by half the bounce
        float baseCX = halfW;
        if (count > 1) {
            baseCX += PFMath::fastSin(e * 2.0f + t * 0.5f) * quarterW;
        }
        const float baseCY = (fh / (float)(count + 1)) * (float)(e + 1) + bounceHeight * 0.5f;

        // 2. Bounce
        const float bouncePhase = t * animSpeed * 0.8f + (e * 0.5f);
        const float sinBounce = PFMath::fastSin(bouncePhase);
        const float cy = baseCY - fabsf(sinBounce) * bounceHeight;

        // 3. Squash and stretch
        const float vel = PFMath::fastCos(bouncePhase);
        const float stretch = 1.0f + (vel * 0.15f * bounceAmt);
        const float squash = 1.0f / stretch;

        // 4. Throb and blink
        const float throb = PFMath::fastSin(t * animSpeed) * 0.08f + 1.0f;
        const float blinkPhase = t * animSpeed * 0.4f + (float)e;
        const float blink = PFMath::fastPow(fabsf(PFMath::fastSin(blinkPhase)), 15.0f);
        const float lidPos = (1.0f - blink) * (18.0f * S * throb * stretch);

        // 5. Looking around
        const float lookX = PFMath::fastSin(t * lookSpeed + (float)e) * 5.0f * S;
        const float lookY = PFMath::fastCos(t * lookSpeed * 0.8f + (float)e) * 3.0f * S;

        const float eyeRadius = 16.0f * S * throb;
        const float irisRadius = 8.0f * S * throb;
        const float pupilRadius = 3.5f * S * throb;
        const float rim = 2.0f * S;                     // the edge vignette's width
        const float lidRim = 2.2f;                      // the lid's dark edge, in pixels

        const float boundW = 22.0f * S * throb * squash;
        const float boundH = 22.0f * S * throb * stretch;
        const int startX = (int)fmaxf(0.0f, floorf(baseCX - boundW));
        const int endX   = (int)fminf(fw, ceilf(baseCX + boundW));
        const int startY = (int)fmaxf(0.0f, floorf(cy - boundH));
        const int endY   = (int)fminf(fh, ceilf(cy + boundH));

        const float irisCenterX = baseCX + lookX;
        const float irisCenterY = cy + lookY;
        const float invEye = 1.0f / eyeRadius;

        for (int py = startY; py < endY; py++) {
            const float dy = ((float)py - cy) / stretch;
            const float lidGap = lidPos - fabsf(dy);
            if (lidGap < 0.0f) continue;

            for (int px = startX; px < endX; px++) {
                const float dx = ((float)px - baseCX) / squash;
                const float dist = sqrtf(dx * dx + dy * dy);
                if (dist >= eyeRadius) continue;

                // Sclera, shaded round
                const float rn = dist * invEye;
                const float shade = 1.0f - 0.22f * rn * rn;
                float r = 245.0f * shade, g = 242.0f * shade, b = 240.0f * shade;

                // Red veins: the original's spirals, finer, and thin capillaries off them
                if (dist > irisRadius) {
                    const float angle = PFMath::fastAtan2(dy, dx);
                    const float out = (dist - irisRadius) / (eyeRadius - irisRadius);    // 0 at the iris, 1 at the rim
                    const float vein = PFMath::fastSin(angle * 10.0f + dist * (0.4f / S) + t);
                    const float cap = PFMath::fastSin(angle * 31.0f - dist * (0.9f / S) + t * 0.6f
                                                      + PFMath::fastSin(dist * (0.7f / S) + angle * 3.0f) * 1.6f);
                    if (vein > 0.93f - 0.05f * out) {
                        r = 220.0f; g = 40.0f; b = 40.0f;
                    } else if (out > 0.3f && cap > 0.96f - 0.06f * out) {
                        const float k = 0.35f + 0.5f * out;
                        r = r + (225.0f - r) * k; g = g + (70.0f - g) * k; b = b + (75.0f - b) * k;
                    }
                }

                // Blue iris
                const float idx = ((float)px - irisCenterX) / squash;
                const float idy = ((float)py - irisCenterY) / stretch;
                const float iDist = sqrtf(idx * idx + idy * idy);

                if (iDist < irisRadius) {
                    const float irisAngle = PFMath::fastAtan2(idy, idx);
                    const float in = iDist / irisRadius;
                    // Fibres, twice the original's 16, with a slow wobble so they aren't ruled
                    const float tex = PFMath::fastSin(irisAngle * 32.0f + PFMath::fastSin(irisAngle * 5.0f) * 0.9f) * 34.0f
                                    + PFMath::fastSin(irisAngle * 13.0f - in * 4.0f) * 14.0f;
                    r = 20.0f + tex; g = 80.0f + tex; b = 200.0f + tex;
                    if (in > 0.82f) {                       // dark limbal ring
                        const float k = 1.0f - (in - 0.82f) * 3.0f;
                        r *= k; g *= k; b *= k;
                    } else if (iDist < pupilRadius * 1.6f) {    // pale collarette by the pupil
                        r += 30.0f; g += 40.0f; b += 30.0f;
                    }

                    if (iDist < pupilRadius) {
                        const float k = fmaxf(0.0f, (iDist - (pupilRadius - 1.2f)) / 1.2f);   // soft pupil edge
                        r *= k * 0.4f; g *= k * 0.4f; b *= k * 0.4f;
                    }

                    // Specular reflection, soft-edged, and a small second glint
                    const float sx = idx + 2.5f * S, sy = idy + 2.5f * S;
                    const float sd = sqrtf(sx * sx + sy * sy);
                    const float sR = 1.8f * S;
                    if (sd < sR) {
                        const float k = fminf(1.0f, (sR - sd) * 1.2f);
                        r += (255.0f - r) * k; g += (255.0f - g) * k; b += (255.0f - b) * k;
                    }
                    const float gx = idx - 1.6f * S, gy = idy - 1.9f * S;
                    if (gx * gx + gy * gy < 0.6f * S * 0.6f * S) {
                        r = r * 0.4f + 150.0f; g = g * 0.4f + 150.0f; b = b * 0.4f + 150.0f;
                    }
                }

                // The lid's dark rim, where a blink cuts the eye
                if (lidGap < lidRim) {
                    const float k = lidGap / lidRim;
                    r = 70.0f + (r - 70.0f) * k; g = 12.0f + (g - 12.0f) * k; b = 30.0f + (b - 30.0f) * k;
                }

                // Edge vignette
                if (dist > eyeRadius - rim) {
                    const float edgeAlpha = (eyeRadius - dist) / rim;
                    r *= edgeAlpha; g *= edgeAlpha; b *= edgeAlpha;
                }

                PFCanvas::setPixel(px, py, c8(r), c8(g), c8(b));
            }
        }
    }

    PFCanvas::present();
}

} // namespace BouncyBeholder
