#pragma once

// ===== Patternflow pattern =====
// Title:    Fireworks
// Author:   @akacoda
// Source:   https://community.patternflow.work/community/p/84ce122b64d241eb
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the original's 128 x 64 sky,
// doubled in height. Everything that moves is scaled by SCALE = 1.6 (shell rise, burst and
// split speeds, gravity, drift), so the bursts open 1.6 times as wide with the same timing,
// and they carry 2.2 times the sparks (DENSITY; rings, which are lines, 1.6 times) so they
// read as full as the originals. The pools grow to match (1280 sparks, 1024 trail embers,
// found from a cursor instead of a scan from zero), sparks leave an ember every frame rather
// than half of them, shells go up a third more often over the taller sky, and the show
// opens with a pair of shells. Styles, palette, timing and the multi-break logic are the
// original's.

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_math.h"
#include "src/core_mem.h"

namespace Fireworks {

const char* NAME = "Fireworks";
const char* const KNOB_LABELS[4] = {"Rate", "Spread", "Size", "Gravity"};

constexpr int FRAME_W = 128;
constexpr int FRAME_H = 128;

static constexpr int FW_MAX_SHELLS = 14;      // the original: 10
static constexpr int FW_MAX_SPARKS = 1280;    // the original: 256
static constexpr int FW_MAX_TRAILS = 1024;    // the original: 128
static constexpr int FW_PIX_COUNT = FRAME_W * FRAME_H * 3;
static constexpr float SCALE = 1.6f;          // lengths and speeds, against the original's 64-high sky
static constexpr float DENSITY = 2.2f;        // sparks per burst (about SCALE squared, for an area)
static constexpr float LAUNCH_RATE = 1.35f;   // shells per second, against the original

static constexpr uint8_t STYLE_PEONY = 0;
static constexpr uint8_t STYLE_CHRYS = 1;
static constexpr uint8_t STYLE_WILLOW = 2;
static constexpr uint8_t STYLE_RING = 3;
static constexpr uint8_t STYLE_PALM = 4;
static constexpr uint8_t STYLE_CROSSETTE = 5;
static constexpr uint8_t STYLE_PISTIL = 6;

static constexpr uint8_t FW_PALETTE[11][3] = {
    {255, 60, 50},
    {255, 140, 40},
    {255, 220, 70},
    {255, 255, 200},
    {180, 255, 120},
    {50, 220, 90},
    {60, 200, 255},
    {70, 110, 255},
    {180, 80, 255},
    {255, 90, 180},
    {220, 220, 255},
};

static constexpr uint8_t FW_SECONDARY_STYLES[4] = {
    STYLE_PEONY, STYLE_RING, STYLE_CHRYS, STYLE_PISTIL
};

struct FwShell {
    uint8_t alive;
    float x, y, vx, vy;
    float targetY;
    float age;
    uint8_t style;
    uint8_t colorA;
    uint8_t colorB;
    float size;
    uint8_t breaksLeft;   // remaining delayed bursts after the first pop
    uint8_t glitter;
    uint8_t phase;        // 0 = rising mortar, 1 = hanging for delayed break
    float burstTimer;
};

struct FwSpark {
    uint8_t alive;
    float x, y, vx, vy;
    float life;
    float maxLife;
    uint8_t r, g, b;
    float drag;
    float gravity;
    uint8_t twinkle;
    uint8_t sparkle;
    uint8_t canSplit;
    float splitT;
    uint8_t trail;
};

struct FwTrail {
    uint8_t alive;
    float x, y;
    float life;
    uint8_t r, g, b;
};

static FwShell shells[FW_MAX_SHELLS];
static FwSpark sparks[FW_MAX_SPARKS];
static FwTrail trails[FW_MAX_TRAILS];

static float* pixBuf = nullptr;
static int32_t rngState = 12345;
static float spawnAcc = 0.2f;
static float nextLaunch = 0.4f;
static float skyPulse = 0.0f;
static float t = 0.0f;

static float fwClamp(float v, float a, float b) {
    return fmaxf(a, fminf(b, v));
}

static float fwRnd() {
    rngState = (rngState * 48271) % 2147483647;
    if (rngState <= 0) rngState += 2147483647;
    return static_cast<float>(rngState) / 2147483647.0f;
}

static float fwRandRange(float a, float b) {
    return a + (b - a) * fwRnd();
}

static void fwColorOf(uint8_t idx, uint8_t& r, uint8_t& g, uint8_t& b) {
    const uint8_t i = idx % 11;
    r = FW_PALETTE[i][0];
    g = FW_PALETTE[i][1];
    b = FW_PALETTE[i][2];
}

static void fwHeatTint(uint8_t r, uint8_t g, uint8_t b, float heat,
                       uint8_t& outR, uint8_t& outG, uint8_t& outB) {
    const float h = fwClamp(heat, 0.0f, 1.0f);
    outR = static_cast<uint8_t>(r + (255 - r) * h);
    outG = static_cast<uint8_t>(g + (255 - g) * h);
    outB = static_cast<uint8_t>(b + (255 - b) * h);
}

static int sparkCursor = 0;
static int trailCursor = 0;
static int trailsAlive = 0;

// The original scans from zero; with five times the pool that's a cost, so each search starts
// where the last one stopped.
static FwSpark* allocSpark() {
    for (int k = 0; k < FW_MAX_SPARKS; ++k) {
        const int i = (sparkCursor + k) % FW_MAX_SPARKS;
        if (!sparks[i].alive) {
            sparkCursor = (i + 1) % FW_MAX_SPARKS;
            return &sparks[i];
        }
    }
    int i = static_cast<int>(fwRnd() * FW_MAX_SPARKS);
    if (i >= FW_MAX_SPARKS) i = FW_MAX_SPARKS - 1;
    return &sparks[i];
}

static FwTrail* allocTrail() {
    if (trailsAlive >= FW_MAX_TRAILS) return nullptr;
    for (int k = 0; k < FW_MAX_TRAILS; ++k) {
        const int i = (trailCursor + k) % FW_MAX_TRAILS;
        if (!trails[i].alive) {
            trailCursor = (i + 1) % FW_MAX_TRAILS;
            trailsAlive++;
            return &trails[i];
        }
    }
    return nullptr;
}

static FwShell* allocShell() {
    for (int i = 0; i < FW_MAX_SHELLS; ++i) {
        if (!shells[i].alive) return &shells[i];
    }
    return nullptr;
}

static void spawnSpark(float x, float y, float vx, float vy,
                       uint8_t r, uint8_t g, uint8_t b, float life,
                       float drag, float gravity,
                       uint8_t twinkle, uint8_t sparkle,
                       uint8_t canSplit, float splitT, uint8_t trail) {
    FwSpark* p = allocSpark();
    p->alive = 1;
    p->x = x;
    p->y = y;
    p->vx = vx;
    p->vy = vy;
    p->life = life;
    p->maxLife = life;
    p->r = r;
    p->g = g;
    p->b = b;
    p->drag = drag;
    p->gravity = gravity;
    p->twinkle = twinkle;
    p->sparkle = sparkle;
    p->canSplit = canSplit;
    p->splitT = splitT;
    p->trail = trail;
}

static void burstShell(FwShell& shell);

static void launchShell(int w, int h) {
    FwShell* s = allocShell();
    if (!s) return;

    const float midY = h * 0.5f;
    const float targetY = fwRandRange(h * 0.08f, midY - 2.0f);

    s->alive = 1;
    s->x = fwRandRange(w * 0.12f, w * 0.88f);
    s->y = static_cast<float>(h - 1);
    s->vx = fwRandRange(-8.0f, 8.0f) * SCALE;

    const float rise = s->y - targetY;
    s->vy = -sqrtf(fmaxf(40.0f * SCALE * SCALE, 2.0f * 55.0f * SCALE * rise)) * fwRandRange(0.85f, 1.15f);
    s->targetY = targetY;
    s->age = 0.0f;
    s->style = static_cast<uint8_t>(fwRnd() * 7.0f);
    s->colorA = static_cast<uint8_t>(fwRnd() * 11.0f);
    s->colorB = static_cast<uint8_t>(fwRnd() * 11.0f);
    if (s->colorB == s->colorA) s->colorB = static_cast<uint8_t>((s->colorA + 3) % 11);
    s->size = fwRandRange(0.7f, 1.35f);
    // ~55% multi-break shells: 1-3 extra timed pops after the first burst
    if (fwRnd() < 0.55f) {
        s->breaksLeft = static_cast<uint8_t>(1 + static_cast<int>(fwRnd() * 3.0f));
    } else {
        s->breaksLeft = 0;
    }
    s->glitter = fwRnd() < 0.45f ? 1 : 0;
    s->phase = 0;
    s->burstTimer = 0.0f;
}

static void splitSpark(FwSpark& sp) {
    const int n = 4 + static_cast<int>(fwRnd() * 4.0f);   // the original: 3..5
    for (int i = 0; i < n; ++i) {
        const float a = fwRnd() * TWO_PI;
        const float speed = fwRandRange(12.0f, 26.0f) * SCALE;
        spawnSpark(sp.x, sp.y,
            cosf(a) * speed, sinf(a) * speed,
            sp.r, sp.g, sp.b, fwRandRange(0.35f, 0.7f),
            0.97f, 34.0f * SCALE, 0, 1, 0, 0.0f, 0);
    }
    sp.alive = 0;
}

static void burstShell(FwShell& shell) {
    uint8_t caR, caG, caB;
    uint8_t cbR, cbG, cbB;
    fwColorOf(shell.colorA, caR, caG, caB);
    fwColorOf(shell.colorB, cbR, cbG, cbB);

    const float sz = shell.size;
    const float x = shell.x;
    const float y = shell.y;

    for (int i = 0; i < 22; ++i) {   // the original: 10
        const float a = fwRnd() * TWO_PI;
        const float sp = fwRandRange(4.0f, 18.0f) * sz * SCALE;
        spawnSpark(x, y, cosf(a) * sp, sinf(a) * sp,
            255, 255, 240, fwRandRange(0.12f, 0.28f),
            0.9f, 10.0f * SCALE, 0, 1, 0, 0.0f, 0);
    }

    if (shell.style == STYLE_PEONY || shell.style == STYLE_PISTIL) {
        const int n = static_cast<int>((55.0f + fwRnd() * 35.0f * sz) * DENSITY);
        for (int i = 0; i < n; ++i) {
            const float a = (static_cast<float>(i) / n) * TWO_PI + fwRandRange(-0.08f, 0.08f);
            const float sp = fwRandRange(28.0f, 52.0f) * sz * SCALE;
            const bool useB = shell.style == STYLE_PISTIL && i < n * 22 / 100;
            spawnSpark(x, y,
                cosf(a) * sp * fwRandRange(0.85f, 1.1f),
                sinf(a) * sp * fwRandRange(0.85f, 1.1f) * 0.92f,
                useB ? cbR : caR, useB ? cbG : caG, useB ? cbB : caB,
                fwRandRange(0.7f, 1.4f), 0.982f, 30.0f * SCALE, shell.glitter, 0, 0, 0.0f, 1);
        }
    } else if (shell.style == STYLE_CHRYS) {
        const int n = static_cast<int>((70.0f + fwRnd() * 40.0f * sz) * DENSITY);
        for (int i = 0; i < n; ++i) {
            const float a = fwRnd() * TWO_PI;
            const float sp = fwRandRange(20.0f, 48.0f) * sz * SCALE;
            spawnSpark(x, y, cosf(a) * sp, sinf(a) * sp * 0.9f,
                caR, caG, caB, fwRandRange(1.1f, 2.0f),
                0.988f, 26.0f * SCALE, 1, shell.glitter, 0, 0.0f, 1);
        }
    } else if (shell.style == STYLE_WILLOW) {
        const int n = static_cast<int>((45.0f + fwRnd() * 25.0f * sz) * DENSITY);
        for (int i = 0; i < n; ++i) {
            const float a = -PI * 0.15f + fwRnd() * PI * 1.3f;
            const float sp = fwRandRange(18.0f, 36.0f) * sz * SCALE;
            spawnSpark(x, y, cosf(a) * sp, sinf(a) * sp - 8.0f * SCALE,
                caR, caG, caB, fwRandRange(1.6f, 2.8f),
                0.992f, 38.0f * SCALE, 1, 0, 0, 0.0f, 1);
        }
    } else if (shell.style == STYLE_RING) {
        const int n = static_cast<int>((36.0f + fwRnd() * 16.0f) * SCALE);   // a line: SCALE, not DENSITY
        const float sp = fwRandRange(34.0f, 46.0f) * sz * SCALE;
        for (int i = 0; i < n; ++i) {
            const float a = (static_cast<float>(i) / n) * TWO_PI;
            spawnSpark(x, y, cosf(a) * sp, sinf(a) * sp * 0.88f,
                caR, caG, caB, fwRandRange(0.8f, 1.3f),
                0.984f, 28.0f * SCALE, 0, 0, 0, 0.0f, 1);
        }
        for (int i = 0; i < 26; ++i) {   // the original: 12
            const float a = fwRnd() * TWO_PI;
            const float s2 = sp * fwRandRange(0.15f, 0.45f);
            spawnSpark(x, y, cosf(a) * s2, sinf(a) * s2,
                cbR, cbG, cbB, fwRandRange(0.4f, 0.8f),
                0.97f, 22.0f * SCALE, 0, 0, 0, 0.0f, 0);
        }
    } else if (shell.style == STYLE_PALM) {
        const int arms = 7 + static_cast<int>(fwRnd() * 5.0f);   // the original: 5..8
        for (int a = 0; a < arms; ++a) {
            const float ang = -PI * 0.75f + (static_cast<float>(a) / (arms - 1)) * PI * 1.5f;
            const float sp = fwRandRange(30.0f, 50.0f) * sz * SCALE;
            for (int k = 0; k < 11; ++k) {   // the original: 7 along each arm
                const float f = 0.55f + k * 0.051f;
                spawnSpark(x, y,
                    cosf(ang) * sp * f + fwRandRange(-3.0f, 3.0f) * SCALE,
                    sinf(ang) * sp * f * 0.85f - 6.0f * SCALE,
                    caR, caG, caB, fwRandRange(1.0f, 1.8f),
                    0.99f, 36.0f * SCALE, 0, 0, 0, 0.0f, 1);
            }
        }
    } else if (shell.style == STYLE_CROSSETTE) {
        const int n = static_cast<int>((28.0f + fwRnd() * 18.0f * sz) * DENSITY);
        for (int i = 0; i < n; ++i) {
            const float a = fwRnd() * TWO_PI;
            const float sp = fwRandRange(22.0f, 40.0f) * sz * SCALE;
            spawnSpark(x, y, cosf(a) * sp, sinf(a) * sp * 0.9f,
                caR, caG, caB, fwRandRange(0.55f, 0.95f),
                0.983f, 30.0f * SCALE, 0, 0, 1, fwRandRange(0.25f, 0.55f), 1);
        }
    }

    if (shell.breaksLeft > 0) {
        shell.breaksLeft--;
        shell.alive = 1;
        shell.phase = 1;
        shell.vx = 0.0f;
        shell.vy = 0.0f;
        shell.burstTimer = fwRandRange(0.12f, 0.38f);
        shell.style = FW_SECONDARY_STYLES[static_cast<int>(fwRnd() * 4.0f)];
        shell.size = fwClamp(shell.size * fwRandRange(0.75f, 0.95f), 0.5f, 1.35f);
        if (fwRnd() < 0.5f) {
            const uint8_t tmp = shell.colorA;
            shell.colorA = shell.colorB;
            shell.colorB = tmp;
        }
        return;
    }

    shell.alive = 0;
}

static void addPix(int x, int y, float r, float g, float b) {
    if (x < 0 || y < 0 || x >= FRAME_W || y >= FRAME_H || !pixBuf) return;
    const int i = (y * FRAME_W + x) * 3;
    pixBuf[i] = fminf(255.0f, pixBuf[i] + r);
    pixBuf[i + 1] = fminf(255.0f, pixBuf[i + 1] + g);
    pixBuf[i + 2] = fminf(255.0f, pixBuf[i + 2] + b);
}

void setup() {
    PFMath::buildSinLUT();

    if (!pixBuf) {
        pixBuf = PFMem::allocFloats(FW_PIX_COUNT);
    }

    memset(shells, 0, sizeof(shells));
    memset(sparks, 0, sizeof(sparks));
    memset(trails, 0, sizeof(trails));

    sparkCursor = 0;
    trailCursor = 0;
    trailsAlive = 0;
    rngState = 12345;
    spawnAcc = 0.2f;
    nextLaunch = 0.4f;
    // The show opens with a pair (the original: one shell at 0.4 s), so the square isn't empty
    // while the first rises its longer way.
    launchShell(FRAME_W, FRAME_H);
    launchShell(FRAME_W, FRAME_H);
    skyPulse = 0.0f;
    t = 0.0f;
}

void update(float dt, const InputFrame& input) {
    (void)input;

    if (!pixBuf) return;

    const int W = FRAME_W;
    const int H = FRAME_H;

    t += dt;
    if (t > PI * 200.0f) t -= PI * 200.0f;

    spawnAcc += dt;
    if (spawnAcc >= nextLaunch) {
        spawnAcc = 0.0f;
        nextLaunch = (0.35f + fwRnd() * 0.7f) / LAUNCH_RATE;
        const int volley = fwRnd() < 0.22f ? (2 + static_cast<int>(fwRnd() * 2.0f)) : 1;
        for (int i = 0; i < volley; ++i) launchShell(W, H);
    }

    for (int i = 0; i < FW_MAX_SHELLS; ++i) {
        FwShell& s = shells[i];
        if (!s.alive) continue;

        s.age += dt;

        if (s.phase == 0) {
            // Rising mortar
            s.vy += 55.0f * SCALE * dt;
            s.x += s.vx * dt;
            s.y += s.vy * dt;

            if (fwRnd() < 0.7f) {
                FwTrail* tr = allocTrail();
                if (tr) {
                    tr->alive = 1;
                    tr->x = s.x + fwRandRange(-0.6f, 0.6f);
                    tr->y = s.y + fwRandRange(0.0f, 1.5f);
                    tr->life = fwRandRange(0.15f, 0.35f);
                    tr->r = 255;
                    tr->g = static_cast<uint8_t>(200.0f + fwRnd() * 40.0f);
                    tr->b = 120;
                }
            }

            const bool pastMid = s.y < H * 0.48f;
            const bool atApex = s.vy >= -4.0f * SCALE;
            const bool hitTarget = s.y <= s.targetY;
            const bool tooHigh = s.y < 2.0f;
            const bool tooOld = s.age > 3.2f;
            const bool fellBack = s.vy > 2.0f * SCALE && s.y > H * 0.55f;

            if (pastMid && (hitTarget || atApex || tooHigh || tooOld)) {
                burstShell(s);
                skyPulse = fminf(1.0f, skyPulse + 0.25f);
            } else if (fellBack) {
                // Missed apex somehow — pop before it drifts away
                burstShell(s);
                skyPulse = fminf(1.0f, skyPulse + 0.15f);
            }

            if (s.y > H + 4.0f || s.x < -10.0f || s.x > W + 10.0f) s.alive = 0;
        } else {
            // Delayed secondary break — hang in place, then pop again
            s.burstTimer -= dt;
            if (s.burstTimer <= 0.0f) {
                burstShell(s);
                skyPulse = fminf(1.0f, skyPulse + 0.2f);
            }
        }
    }

    for (int i = 0; i < FW_MAX_SPARKS; ++i) {
        FwSpark& p = sparks[i];
        if (!p.alive) continue;

        p.life -= dt;
        if (p.life <= 0.0f) {
            p.alive = 0;
            continue;
        }

        p.vy += p.gravity * dt;
        const float dragPow = powf(p.drag, dt * 60.0f);
        p.vx *= dragPow;
        p.vy *= dragPow;
        p.x += p.vx * dt;
        p.y += p.vy * dt;

        if (p.trail) {   // the original: on 55 % of frames; finer streaks here
            FwTrail* tr = allocTrail();
            if (tr) {
                tr->alive = 1;
                tr->x = p.x;
                tr->y = p.y;
                tr->life = fwRandRange(0.12f, 0.35f);
                const float fade = p.life / p.maxLife;
                tr->r = static_cast<uint8_t>(p.r * fade);
                tr->g = static_cast<uint8_t>(p.g * fade);
                tr->b = static_cast<uint8_t>(p.b * fade);
            }
        }

        if (p.canSplit) {
            p.splitT -= dt;
            if (p.splitT <= 0.0f) splitSpark(p);
        }

        if (p.y > H + 2 || p.x < -4.0f || p.x > W + 4.0f) p.alive = 0;
    }

    for (int i = 0; i < FW_MAX_TRAILS; ++i) {
        FwTrail& tr = trails[i];
        if (!tr.alive) continue;
        tr.life -= dt;
        tr.y += 6.0f * SCALE * dt;
        if (tr.life <= 0.0f) {
            tr.alive = 0;
            trailsAlive--;
        }
    }

    skyPulse = fmaxf(0.0f, skyPulse - dt * 1.8f);
}

void draw() {
    PFCanvas::setFrame(FRAME_W, FRAME_H);
    if (!pixBuf) {
        PFCanvas::present();
        return;
    }

    const int W = FRAME_W;
    const int H = FRAME_H;

    for (int y = 0; y < H; ++y) {
        const float skyBase = 4.0f + (static_cast<float>(y) / H) * 10.0f + skyPulse * 18.0f;
        for (int x = 0; x < W; ++x) {
            const int i = (y * W + x) * 3;
            pixBuf[i] = skyBase * 0.35f;
            pixBuf[i + 1] = skyBase * 0.4f;
            pixBuf[i + 2] = skyBase * 0.7f;
        }
    }

    for (int i = 0; i < FW_MAX_TRAILS; ++i) {
        const FwTrail& tr = trails[i];
        if (!tr.alive) continue;
        const float a = fwClamp(tr.life * 3.0f, 0.0f, 1.0f);
        addPix(static_cast<int>(tr.x), static_cast<int>(tr.y),
            tr.r * a * 0.55f, tr.g * a * 0.55f, tr.b * a * 0.55f);
    }

    for (int i = 0; i < FW_MAX_SHELLS; ++i) {
        const FwShell& s = shells[i];
        if (!s.alive) continue;
        if (s.phase == 1) {
            // Dim ember while waiting for the next timed break
            const float pulse = 0.5f + 0.5f * PFMath::fastSin(t * 18.0f + s.x);
            addPix(static_cast<int>(s.x), static_cast<int>(s.y),
                200.0f * pulse, 140.0f * pulse, 60.0f * pulse);
        } else {
            addPix(static_cast<int>(s.x), static_cast<int>(s.y), 255.0f, 230.0f, 160.0f);
            addPix(static_cast<int>(s.x), static_cast<int>(s.y) + 1, 180.0f, 100.0f, 40.0f);
        }
    }

    for (int i = 0; i < FW_MAX_SPARKS; ++i) {
        const FwSpark& p = sparks[i];
        if (!p.alive) continue;

        const float age = 1.0f - p.life / p.maxLife;
        const float fade = powf(p.life / p.maxLife, 0.65f);
        float heat = fwClamp(1.0f - age * 3.2f, 0.0f, 1.0f);

        if (p.sparkle) {
            const float flicker = PFMath::fastSin(t * 40.0f + i * 2.3f) > 0.7f ? 0.85f : 0.0f;
            heat = fmaxf(heat, flicker);
        }

        uint8_t rr, gg, bb;
        fwHeatTint(p.r, p.g, p.b, heat, rr, gg, bb);

        float bright = fade;
        if (p.twinkle) {
            bright *= 0.55f + 0.45f * PFMath::fastSin(t * 28.0f + i * 1.7f + p.x);
        }

        const float r = rr * bright;
        const float g = gg * bright;
        const float b = bb * bright;
        const int px = static_cast<int>(p.x);
        const int py = static_cast<int>(p.y);

        addPix(px, py, r, g, b);

        if (bright > 0.65f) {
            addPix(px + 1, py, r * 0.35f, g * 0.35f, b * 0.35f);
            addPix(px, py + 1, r * 0.25f, g * 0.25f, b * 0.25f);
        }
    }

    for (int y = 0; y < H; ++y) {
        for (int x = 0; x < W; ++x) {
            const int i = (y * W + x) * 3;
            PFCanvas::setPixel(x, y,
                static_cast<uint8_t>(pixBuf[i]),
                static_cast<uint8_t>(pixBuf[i + 1]),
                static_cast<uint8_t>(pixBuf[i + 2]));
        }
    }

    PFCanvas::present();
}

} // namespace Fireworks