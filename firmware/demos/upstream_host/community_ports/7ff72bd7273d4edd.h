// ===== Patternflow pattern =====
// Title:    Dual Metamorphic Lifecycle
// Author:   @martinnlopez
// Source:   https://community.patternflow.work/community/p/7ff72bd7273d4edd
// SPDX-License-Identifier: CC-BY-SA-4.0
// ===============================
// Adapted for Patternflood's 128 x 128 panel (2026-10-27): the two reactors were one
// mandala drawn twice (same structure, same knobs, two palettes), stacked as two 64 x 64
// squares. Here it is drawn once at twice the size, filling the square, with the earthy
// reactor as its top half and the solar-magma one as its bottom half, blended across a
// narrow seam through the core. The geometry (rings, rails, needles, pearls, haze, core,
// shock ring, seed arcs) scales with the reactor (S = 64, the octant fold 64 x 64), while
// rails and needles widen only by 1.35 (DML_LW), so the bigger lattice reads finer.
#pragma once

#include <Arduino.h>
#include "config.h"
#include "src/core_display.h"
#include "src/core_encoders.h"
#include "src/core_canvas.h"
#include "src/core_params.h"
#include "src/core_math.h"

namespace DualMetamorphicLifecyclePattern {

const char* NAME = "Dual Metamorphic Lifecycle";
const char* const KNOB_LABELS[4] = {"Stage", "Speed", "Complexity", "Overdrive"};
constexpr bool ABSOLUTE_READY = true;

constexpr int FRAME_W = 128;
constexpr int FRAME_H = 128;
constexpr int OCT_N = 64;       // half the reactor's box (the original: 32)
constexpr int OCT_POINTS = OCT_N * (OCT_N + 1) / 2; // unique (u, v) points in a D4 octant
constexpr float DML_S = (float)OCT_N;   // the reactor's radius in px
constexpr float DML_SC = DML_S / 32.0f; // ... over the original's
constexpr float DML_LW = 1.35f;         // rail and needle width over the original's
constexpr float DML_SEAM = 5.0f;        // half-height of the blend between the two palettes, px

constexpr float DML_TAU = 6.283185307179586f;
constexpr float DML_QPI = 0.7853981633974483f;
constexpr float DML_F_MIN = 0.1f;
constexpr float DML_F_MAX = 0.35f;
constexpr float DML_LINE_I = 1.0f / (0.68f * 0.68f * DML_LW * DML_LW);
constexpr int BEAD_CAP = 192;
constexpr int PRIM_CAP = 300;
constexpr int U_BINS = OCT_N / 4;

inline float clampF(float x, float a, float b) { return PFMath::clamp(x, a, b); }
inline float satF(float x) { return PFMath::clamp01(x); }
inline float smoothF(float x) { x = satF(x); return x * x * (3.0f - 2.0f * x); }
inline float smootherF(float x) { x = satF(x); return x * x * x * (x * (x * 6.0f - 15.0f) + 10.0f); }

static float GT[513];
static uint8_t TM[4097];

static const float RC_R1[9] = {0.16f, 0.28f, 0.38f, 0.55f, 0.75f, 0.87f, 0.74f, 0.85f, 1.00f};
static const float RC_G1[9] = {0.21f, 0.35f, 0.42f, 0.52f, 0.63f, 0.55f, 0.42f, 0.60f, 0.98f};
static const float RC_B1[9] = {0.09f, 0.15f, 0.22f, 0.28f, 0.37f, 0.25f, 0.15f, 0.40f, 0.88f};

static const float RC_R2[9] = {0.20f, 0.45f, 0.70f, 0.85f, 1.00f, 1.00f, 0.90f, 0.75f, 0.60f};
static const float RC_G2[9] = {0.08f, 0.22f, 0.35f, 0.50f, 0.75f, 0.50f, 0.30f, 0.15f, 0.05f};
static const float RC_B2[9] = {0.05f, 0.08f, 0.12f, 0.18f, 0.25f, 0.15f, 0.08f, 0.05f, 0.02f};

static float GRAD_R1[32], GRAD_G1[32], GRAD_B1[32];
static float GRAD_R2[32], GRAD_G2[32], GRAD_B2[32];

// Precomputed D4 octant geometry
static uint16_t iu_offsets[OCT_N];
static float oct_geom_r[OCT_POINTS];
static float oct_geom_ph[OCT_POINTS];
static float oct_geom_lobe[OCT_POINTS];
static float oct_geom_ef[OCT_POINTS];
static uint8_t oct_geom_pab[OCT_POINTS];

// Octant frame accumulators, one per reactor (palette)
static float oct_buf_r[2][OCT_POINTS];
static float oct_buf_g[2][OCT_POINTS];
static float oct_buf_b[2][OCT_POINTS];

inline uint8_t tone(float x) {
    if (x <= 0.0f) return 0;
    int idx = (int)(x * 512.0f);
    if (idx > 4095) idx = 4095;
    return TM[idx];
}

enum KeyIndex {
    K_CORE_I = 0, K_CORE_R, K_RAIL_G, K_RAIL_A, K_NEED_A, K_NEED_F, K_NEED_L,
    K_RING_R, K_BEAD_A, K_BEAD_S, K_HAZE, K_SEED_A, K_LIFT, KEY_COUNT
};

static const float KF_VALS[KEY_COUNT][5] = {
    {0.72f, 0.10f, 0.90f, 1.00f, 0.00f},
    {0.07f, 0.11f, 0.24f, 0.28f, 0.45f},
    {0.00f, 0.45f, 0.80f, 1.00f, 0.20f},
    {0.00f, 0.90f, 1.00f, 1.00f, 0.00f},
    {0.00f, 0.60f, 0.80f, 1.00f, 0.95f},
    {0.00f, 0.25f, 0.55f, 0.95f, 0.00f},
    {0.00f, 5.00f, 7.00f, 8.00f, 12.0f},
    {0.14f, 0.36f, 0.47f, 0.56f, 0.66f},
    {0.00f, 0.55f, 0.70f, 0.80f, 1.00f},
    {0.60f, 0.85f, 1.00f, 1.00f, 1.20f},
    {0.20f, 0.25f, 0.45f, 0.50f, 0.28f},
    {1.00f, 0.10f, 0.00f, 0.00f, 0.00f},
    {0.85f, 0.94f, 1.00f, 1.00f, 0.94f}
};

static const float KW_VALS[KEY_COUNT][10] = {
    {0.00f, 0.50f, 0.20f, 0.90f, 0.10f, 0.90f, 0.20f, 0.85f, 0.55f, 1.00f},
    {0.00f, 0.50f, 0.20f, 0.90f, 0.10f, 0.90f, 0.20f, 0.85f, 0.55f, 1.00f},
    {0.10f, 1.00f, 0.00f, 1.00f, 0.00f, 1.00f, 0.25f, 0.95f, 0.00f, 1.00f},
    {0.05f, 0.60f, 0.10f, 0.90f, 0.10f, 0.90f, 0.35f, 0.95f, 0.10f, 0.90f},
    {0.40f, 1.00f, 0.10f, 0.90f, 0.10f, 0.90f, 0.10f, 0.90f, 0.40f, 0.95f},
    {0.35f, 1.00f, 0.10f, 0.90f, 0.10f, 0.90f, 0.15f, 0.85f, 0.35f, 0.95f},
    {0.35f, 1.00f, 0.10f, 0.90f, 0.10f, 0.90f, 0.15f, 0.85f, 0.35f, 0.95f},
    {0.10f, 1.00f, 0.10f, 0.90f, 0.10f, 0.90f, 0.20f, 0.95f, 0.35f, 0.98f},
    {0.35f, 1.00f, 0.10f, 0.90f, 0.10f, 0.90f, 0.30f, 0.95f, 0.60f, 1.00f},
    {0.10f, 0.90f, 0.10f, 0.90f, 0.10f, 0.90f, 0.10f, 0.90f, 0.10f, 0.90f},
    {0.10f, 0.90f, 0.10f, 0.90f, 0.10f, 0.90f, 0.10f, 0.90f, 0.10f, 0.90f},
    {0.00f, 0.50f, 0.00f, 0.50f, 0.10f, 0.90f, 0.10f, 0.90f, 0.50f, 1.00f},
    {0.10f, 0.90f, 0.10f, 0.90f, 0.10f, 0.90f, 0.10f, 0.90f, 0.10f, 0.90f}
};

static const float WT[5] = {1.0f, 1.0f, 1.0f, 1.4f, 1.6f};
constexpr float WSUM = 6.0f;

inline float wrapd(float d) { return d > 2.5f ? d - 5.0f : (d < -2.5f ? d + 5.0f : d); }

inline float kfw(float s, const float arr[5], const float win[10], bool hasWin) {
    int i = PFMath::ifloor(s);
    if (i > 4) i = 4;
    if (i < 0) i = 0;
    float f = s - (float)i;
    int j = (i == 4) ? 0 : i + 1;
    float d0 = 0.10f, d1 = 0.90f;
    if (hasWin) { d0 = win[i * 2]; d1 = win[i * 2 + 1]; }
    return arr[i] + (arr[j] - arr[i]) * smootherF((f - d0) / (d1 - d0));
}

struct SimpleRnd {
    uint32_t s;
    void init(uint32_t seed) { s = seed; }
    float next() {
        s = s * 1664525u + 1013904223u;
        return (float)s / 4294967296.0f;
    }
};

struct ReactorParams {
    float coreI, coreR, railG, railA, needA, needF, needL;
    float ringR, beadA, beadS, haze, seedA, lift;
    float gCore, gLine, bloom, shA, shR;
    float coreInv;
    float hazeInv;
};

struct ReactorState {
    bool ready;
    float S;
    float s;
    float f;
    bool held;
    float lastStage;
    bool stageInit;
    float sv;
    float soft;
    float tgtSm;
    bool tgtSmInit;
    float cxS;
    float odS;
    bool knobInit;
    float F;
    float flareHold;
    float flareAge;
    float phB, phW1, phW2, phR, phFlow;

    ReactorParams q;

    int nK;
    float RR0[9];
    float RR[9];
    int nRay;
    float rayA[16];
    int rayRank[16];
    float rayDel[16];
    float rayLen[16];
    float rayBead[16];

    float rC[16], rS[16], rBase[16], rAmp[16], rLab[16], rLfr[16];
    float sR[5], sHW[5], sSpd[5], sAng[5], sRpx[5];
    float sNX[10], sNY[10];
    float sAmp;

    int nT;
    int tS[12], tN[12];
    float tDel[12], tOff[12], tVis[12], tThr[12];

    int nSegments;
    int sType[64], sK[64], sK2[64];
    float sA0[64], sA1[64], sT0[64], sT1[64];

    int nA, nL, nB;
    float aLo[PRIM_CAP], aHi[PRIM_CAP], aAmp[PRIM_CAP], aCr[PRIM_CAP], aCg[PRIM_CAP], aCb[PRIM_CAP];
    float lC[PRIM_CAP], lS[PRIM_CAP], lLo[PRIM_CAP], lHi[PRIM_CAP], lAmp[PRIM_CAP], lCr[PRIM_CAP], lCg[PRIM_CAP], lCb[PRIM_CAP];
    float bX[BEAD_CAP], bY[BEAD_CAP], bAmp[BEAD_CAP], bHr[BEAD_CAP], bHg[BEAD_CAP], bHb[BEAD_CAP], bI1[BEAD_CAP], bI2[BEAD_CAP], bRL[BEAD_CAP];

    uint8_t ringArcCount[9];
    uint16_t ringArcs[9][48];

    uint8_t beadBinCount[U_BINS];
    uint8_t beadBin[U_BINS][BEAD_CAP];

    float warp[256];
    float rip[192];
};

static ReactorState reactor1;
static ReactorState reactor2;

static float knob_stage = 0.0f;
static float knob_speed = 0.35f;
static float knob_complexity = 1.0f;
static float knob_overdrive = 1.0f;

static float path_px = 0.0f;
static float path_py = 0.0f;

void buildTracks(ReactorState& p) {
    SimpleRnd rnd;
    rnd.init(20240607u);
    int nT = 12;
    int K = p.nK;
    const int startRing[12] = {4, 2, 6, 1, 7, 3, 5, 0, 3, 6, 2, 5};
    const float initThr[12] = {-0.2f, -0.1f, 0.0f, 0.15f, 0.30f, 0.45f, 0.55f, 0.65f, 0.75f, 0.82f, 0.90f, 0.95f};

    p.nT = nT;
    for (int i = 0; i < 12; i++) p.tThr[i] = initThr[i];
    p.nSegments = 0;

    for (int t = 0; t < nT; t++) {
        int k = startRing[t % 12];
        float a = 0.04f + rnd.next() * 0.5f;
        int dir = (t & 1) ? -1 : 1;
        int nArcs = 2 + (int)(rnd.next() * 2.8f);
        int first = p.nSegments;
        float lens[16];
        float total = 0.0f;
        int segCount = 0;

        for (int st = 0; st < nArcs; st++) {
            if (a > 0.92f) dir = -1;
            else if (a < 0.08f) dir = 1;
            float la = 0.12f + rnd.next() * 0.22f;
            float a2 = a + (float)dir * la;
            if (a2 > 1.0f || a2 < 0.0f) {
                dir = -dir;
                a2 = clampF(a + (float)dir * la, 0.0f, 1.0f);
            }

            int mIdx = p.nSegments++;
            p.sType[mIdx] = 0;
            p.sK[mIdx] = k;
            p.sK2[mIdx] = k;
            p.sA0[mIdx] = a;
            p.sA1[mIdx] = a2;

            float len = p.RR0[k] * fabsf(a2 - a) * DML_QPI + 0.001f;
            lens[segCount++] = len;
            total += len;
            a = a2;

            if (rnd.next() < 0.3f) dir = -dir;

            if (st < nArcs - 1) {
                int k2 = k + (rnd.next() < 0.5f ? -1 : 1);
                if (k2 < 0) k2 = 1;
                else if (k2 >= K) k2 = K - 2;

                int mIdx2 = p.nSegments++;
                p.sType[mIdx2] = 1;
                p.sK[mIdx2] = k;
                p.sK2[mIdx2] = k2;
                p.sA0[mIdx2] = a;
                p.sA1[mIdx2] = a;

                len = fabsf(p.RR0[k2] - p.RR0[k]) + 0.001f;
                lens[segCount++] = len;
                total += len;
                k = k2;
            }
        }

        float cum = 0.0f;
        for (int m = 0; m < segCount; m++) {
            int segIdx = first + m;
            p.sT0[segIdx] = cum / total;
            cum += lens[m];
            p.sT1[segIdx] = cum / total;
        }

        p.tS[t] = first;
        p.tN[t] = segCount;
        p.tDel[t] = 0.9f * (float)startRing[t % 12] / (float)(K - 1);
        p.tOff[t] = rnd.next();
        p.tVis[t] = 0.0f;
    }
}

void buildStructure(ReactorState& p) {
    p.nK = 9;
    const float initRR0[9] = {0.175f, 0.275f, 0.381f, 0.481f, 0.581f, 0.675f, 0.769f, 0.856f, 0.944f};
    for (int i = 0; i < 9; i++) {
        p.RR0[i] = initRR0[i];
        p.RR[i] = initRR0[i];
    }

    p.nRay = 16;
    const float initRayA[16] = {0.00f, 0.06f, 0.12f, 0.25f, 0.36f, 0.44f, 0.50f, 0.56f, 0.64f, 0.72f, 0.78f, 0.84f, 0.90f, 0.94f, 0.97f, 1.00f};
    const int initRayRank[16] = {0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3};
    const float initRayDel[16] = {-0.14f, 0.04f, 0.10f, -0.06f, 0.30f, 0.22f, 0.52f, 0.46f, -0.10f, 0.08f, 0.15f, -0.02f, 0.25f, 0.18f, 0.40f, 0.35f};
    const float initRayLen[16] = {1.00f, 0.80f, 0.90f, 0.70f, 0.60f, 0.75f, 0.55f, 0.65f, 0.95f, 0.85f, 0.75f, 0.65f, 0.80f, 0.70f, 0.60f, 0.50f};
    const float initRayBead[16] = {1.15f, 1.05f, 1.00f, 1.00f, 1.10f, 1.00f, 0.90f, 0.80f, 1.15f, 1.05f, 1.00f, 1.00f, 0.90f, 0.80f, 0.00f, 0.00f};

    for (int i = 0; i < 16; i++) {
        p.rayA[i] = initRayA[i];
        p.rayRank[i] = initRayRank[i];
        p.rayDel[i] = initRayDel[i];
        p.rayLen[i] = initRayLen[i];
        p.rayBead[i] = initRayBead[i];
        p.rC[i] = 1.0f;
        p.rS[i] = 0.0f;
        p.rBase[i] = 0.0f;
        p.rAmp[i] = 0.0f;
        p.rLab[i] = 0.0f;
        p.rLfr[i] = 0.0f;
    }

    const float initsR[5] = {0.20f, 0.32f, 0.46f, 0.60f, 0.75f};
    const float initsHW[5] = {0.95f, 0.70f, 0.85f, 0.60f, 0.50f};
    const float initsSpd[5] = {0.040f, -0.030f, 0.024f, -0.045f, 0.035f};
    const float initsAng[5] = {0.3f, 2.1f, 4.0f, 5.2f, 1.5f};

    for (int i = 0; i < 5; i++) {
        p.sR[i] = initsR[i];
        p.sHW[i] = initsHW[i];
        p.sSpd[i] = initsSpd[i];
        p.sAng[i] = initsAng[i];
        p.sRpx[i] = 0.0f;
    }
    for (int i = 0; i < 10; i++) {
        p.sNX[i] = 0.0f;
        p.sNY[i] = 0.0f;
    }
    p.sAmp = 0.0f;

    buildTracks(p);

    p.nA = 0;
    p.nL = 0;
    p.nB = 0;
    for (int i = 0; i < 256; i++) p.warp[i] = 0.0f;
    for (int i = 0; i < 192; i++) p.rip[i] = 0.0f;
}

void initReactor(ReactorState& p) {
    p.ready = true;
    p.S = DML_S;
    p.s = 0.0f;
    p.f = 0.2f;
    p.held = false;
    p.lastStage = 0.0f;
    p.stageInit = false;
    p.sv = 0.0f;
    p.soft = 0.0f;
    p.tgtSm = 0.0f;
    p.tgtSmInit = false;
    p.cxS = 0.7f;
    p.odS = 0.6f;
    p.knobInit = false;
    p.F = 0.0f;
    p.flareHold = 0.0f;
    p.flareAge = 99.0f;
    p.phB = 0.0f;
    p.phW1 = 0.0f;
    p.phW2 = 0.0f;
    p.phR = 0.0f;
    p.phFlow = 0.0f;

    p.q.coreI = 0.0f;
    p.q.coreR = 0.0f;
    p.q.railG = 0.0f;
    p.q.railA = 0.0f;
    p.q.needA = 0.0f;
    p.q.needF = 0.0f;
    p.q.needL = 0.0f;
    p.q.ringR = 0.14f;
    p.q.beadA = 0.0f;
    p.q.beadS = 1.0f;
    p.q.haze = 0.0f;
    p.q.seedA = 0.0f;
    p.q.lift = 1.0f;
    p.q.gCore = 1.0f;
    p.q.gLine = 1.0f;
    p.q.bloom = 0.22f;
    p.q.shA = 0.0f;
    p.q.shR = 0.0f;
    p.q.coreInv = 1.0f;
    p.q.hazeInv = 1.0f;

    buildStructure(p);
}

void buildOctantGeometry() {
    float hw = DML_S;
    for (int iu = 0; iu < OCT_N; iu++) {
        iu_offsets[iu] = (iu * (iu + 1)) / 2;
        float uu = (float)iu + 0.5f;
        for (int iv = 0; iv <= iu; iv++) {
            int idx = iu_offsets[iu] + iv;
            float vv = (float)iv + 0.5f;
            float r = sqrtf(uu * uu + vv * vv);
            float ph = PFMath::fastAtan2(vv, uu);
            float edge = r * (hw / uu);

            oct_geom_r[idx] = r;
            oct_geom_ph[idx] = ph;
            oct_geom_lobe[idx] = 0.5f + 0.5f * PFMath::fastCos(4.0f * ph);
            oct_geom_ef[idx] = 0.70f * edge + 0.30f * 1.12f * hw;

            int pab = (int)(ph * (256.0f / DML_TAU) + 0.5f);
            if (pab > 32) pab = 32;
            oct_geom_pab[idx] = (uint8_t)pab;
        }
    }
}

void pathPos(ReactorState& p, int t, float x) {
    int m = p.tS[t];
    int e = m + p.tN[t] - 1;
    for (; m < e; m++) {
        if (x <= p.sT1[m]) break;
    }
    float f = satF((x - p.sT0[m]) / (p.sT1[m] - p.sT0[m]));
    float a, rad;
    if (p.sType[m] == 0) {
        a = (p.sA0[m] + (p.sA1[m] - p.sA0[m]) * f) * DML_QPI;
        rad = p.RR[p.sK[m]];
    } else {
        a = p.sA0[m] * DML_QPI;
        rad = p.RR[p.sK[m]] + (p.RR[p.sK2[m]] - p.RR[p.sK[m]]) * f;
    }
    path_px = rad * PFMath::fastCos(a);
    path_py = rad * PFMath::fastSin(a);
}

void addBead(ReactorState& p, float x, float y, float rad, float amp, float hr, float hg, float hb) {
    amp *= 1.0f - 0.35f * p.soft;
    rad *= 1.0f + 0.25f * p.soft;
    int n = p.nB;
    if (n >= BEAD_CAP || amp < 0.01f) return;
    float s1 = 0.60f * rad + 0.25f;
    float s2 = 1.6f * rad;
    p.bX[n] = x;
    p.bY[n] = y;
    p.bAmp[n] = amp;
    p.bHr[n] = hr;
    p.bHg[n] = hg;
    p.bHb[n] = hb;
    p.bI1[n] = 1.0f / (s1 * s1);
    p.bI2[n] = 1.0f / (s2 * s2);
    p.bRL[n] = 3.0f * s2;
    p.nB = n + 1;
}

void setup() {
    PFMath::buildSinLUT();

    for (int i = 0; i <= 512; i++) GT[i] = expf(-(float)i / 64.0f);
    for (int i = 0; i <= 4096; i++) TM[i] = (uint8_t)clampF((int)roundf(240.0f * (1.0f - expf(-1.5f * (float)i / 512.0f))), 0, 255);

    const float stops1[5][4] = {
        {0.00f, 0.16f, 0.21f, 0.09f}, {0.25f, 0.38f, 0.42f, 0.22f},
        {0.50f, 0.87f, 0.63f, 0.37f}, {0.75f, 0.74f, 0.42f, 0.15f}, {1.00f, 0.99f, 0.98f, 0.88f}
    };
    for (int i = 0; i < 32; i++) {
        float t = (float)i / 31.0f;
        int k = 0;
        while (k < 3 && t > stops1[k + 1][0]) k++;
        float f = (t - stops1[k][0]) / (stops1[k + 1][0] - stops1[k][0]);
        GRAD_R1[i] = stops1[k][1] + (stops1[k + 1][1] - stops1[k][1]) * f;
        GRAD_G1[i] = stops1[k][2] + (stops1[k + 1][2] - stops1[k][2]) * f;
        GRAD_B1[i] = stops1[k][3] + (stops1[k + 1][3] - stops1[k][3]) * f;
    }

    const float stops2[5][4] = {
        {0.00f, 0.20f, 0.08f, 0.05f}, {0.25f, 0.70f, 0.35f, 0.12f},
        {0.50f, 1.00f, 0.75f, 0.25f}, {0.75f, 0.90f, 0.30f, 0.08f}, {1.00f, 1.00f, 0.95f, 0.80f}
    };
    for (int i = 0; i < 32; i++) {
        float t = (float)i / 31.0f;
        int k = 0;
        while (k < 3 && t > stops2[k + 1][0]) k++;
        float f = (t - stops2[k][0]) / (stops2[k + 1][0] - stops2[k][0]);
        GRAD_R2[i] = stops2[k][1] + (stops2[k + 1][1] - stops2[k][1]) * f;
        GRAD_G2[i] = stops2[k][2] + (stops2[k + 1][2] - stops2[k][2]) * f;
        GRAD_B2[i] = stops2[k][3] + (stops2[k + 1][3] - stops2[k][3]) * f;
    }

    buildOctantGeometry();
    initReactor(reactor1);
    initReactor(reactor2);
}

void updateReactor(float dt, const InputFrame& input, ReactorState& p, bool isReactor2) {
    if (!p.ready) initReactor(p);
    if (!(dt > 0.0f)) dt = 1.0f / 60.0f;
    if (dt > 0.1f) dt = 0.1f;

    float vSpeed = knob_speed;
    float fT = clampF(vSpeed, DML_F_MIN, DML_F_MAX);
    p.f += (fT - p.f) * (1.0f - expf(-dt / 0.9f));
    p.f = clampF(p.f, DML_F_MIN, DML_F_MAX);
    float f = p.f;
    float ratio = f / 0.2f;
    p.soft = smoothF((f - 0.2f) / 0.15f);

    float cxT = clampF(knob_complexity, 0.0f, 1.0f);
    float odT = clampF((knob_overdrive - 0.4f) / 0.6f, 0.0f, 1.0f);
    if (!p.knobInit) {
        p.cxS = cxT;
        p.odS = odT;
        p.knobInit = true;
    }
    float kLP = 1.0f - expf(-dt / 0.5f);
    p.cxS += (cxT - p.cxS) * kLP;
    p.odS += (odT - p.odS) * kLP;
    float cx = p.cxS;
    float odn = p.odS * 2.0f;

    float nst = clampF(knob_stage / 5.0f, 0.0f, 1.0f);
    if (!p.stageInit) {
        p.lastStage = nst;
        p.stageInit = true;
    }
    if (fabsf(nst - p.lastStage) > 0.0005f) {
        p.held = true;
        p.lastStage = nst;
    }
    if (nst < 0.1f) p.held = false;

    if (input.btnPressed[0] || input.btnPressed[1] || input.btnPressed[2] || input.btnPressed[3]) {
        p.flareHold = 1.8f;
        if (p.flareAge > 3.6f) p.flareAge = 0.0f;
    }
    float ft = 0.0f;
    if (p.flareHold > 0.0f) {
        p.flareHold -= dt;
        ft = 1.0f;
    }
    float slew = (ft > p.F ? 0.62f : 0.30f) * dt;
    p.F += clampF(ft - p.F, -slew, slew);
    p.flareAge += dt;
    float Fs = smootherF(p.F);

    float vDes;
    if (!p.held) {
        int sIdx = PFMath::ifloor(p.s);
        if (sIdx > 4) sIdx = 4;
        if (sIdx < 0) sIdx = 0;
        vDes = f * WSUM / WT[sIdx];
        p.tgtSmInit = false;
    } else {
        float tgt = clampF((nst - 0.2f) / 0.8f, 0.0f, 1.0f) * 4.0f;
        if (!p.tgtSmInit) {
            p.tgtSm = p.s;
            p.tgtSmInit = true;
        }
        p.tgtSm += wrapd(tgt - p.tgtSm) * (1.0f - expf(-dt / 0.25f));
        if (p.tgtSm >= 5.0f) p.tgtSm -= 5.0f;
        else if (p.tgtSm < 0.0f) p.tgtSm += 5.0f;
        vDes = clampF(wrapd(p.tgtSm - p.s) * 1.5f, -1.2f, 1.2f);
    }

    float acc = 4.0f * dt;
    p.sv += clampF(vDes - p.sv, -acc, acc);
    p.s += p.sv * dt;
    if (p.s >= 5.0f) p.s -= 5.0f;
    else if (p.s < 0.0f) p.s += 5.0f;

    p.phB += DML_TAU * 0.10f * ratio * dt;
    if (p.phB > DML_TAU) p.phB -= DML_TAU;

    p.phW1 += DML_TAU * 0.07f * ratio * dt;
    if (p.phW1 > DML_TAU) p.phW1 -= DML_TAU;

    p.phW2 += DML_TAU * 0.05f * ratio * dt;
    if (p.phW2 > DML_TAU) p.phW2 -= DML_TAU;

    p.phR += DML_TAU * 0.12f * ratio * dt;
    if (p.phR > DML_TAU) p.phR -= DML_TAU;

    p.phFlow += 0.12f * ratio * dt;
    if (p.phFlow > 1.0f) p.phFlow -= 1.0f;

    float S = p.S;
    float sc = S / 32.0f;

    p.q.coreI = kfw(p.s, KF_VALS[K_CORE_I], KW_VALS[K_CORE_I], true);
    p.q.coreR = kfw(p.s, KF_VALS[K_CORE_R], KW_VALS[K_CORE_R], true);
    p.q.railG = kfw(p.s, KF_VALS[K_RAIL_G], KW_VALS[K_RAIL_G], true);
    p.q.railA = kfw(p.s, KF_VALS[K_RAIL_A], KW_VALS[K_RAIL_A], true);
    p.q.needA = kfw(p.s, KF_VALS[K_NEED_A], KW_VALS[K_NEED_A], true);
    p.q.needF = kfw(p.s, KF_VALS[K_NEED_F], KW_VALS[K_NEED_F], true);
    p.q.needL = kfw(p.s, KF_VALS[K_NEED_L], KW_VALS[K_NEED_L], true);
    p.q.ringR = kfw(p.s, KF_VALS[K_RING_R], KW_VALS[K_RING_R], true);
    p.q.beadA = kfw(p.s, KF_VALS[K_BEAD_A], KW_VALS[K_BEAD_A], true);
    p.q.beadS = kfw(p.s, KF_VALS[K_BEAD_S], KW_VALS[K_BEAD_S], false);
    p.q.haze  = kfw(p.s, KF_VALS[K_HAZE],   KW_VALS[K_HAZE],   false);
    p.q.seedA = kfw(p.s, KF_VALS[K_SEED_A], KW_VALS[K_SEED_A], true);
    p.q.lift  = kfw(p.s, KF_VALS[K_LIFT],   KW_VALS[K_LIFT],   false);

    float wb = 0.9f * Fs;
    p.q.coreI += (KF_VALS[K_CORE_I][3] - p.q.coreI) * wb;
    p.q.coreR += (KF_VALS[K_CORE_R][3] - p.q.coreR) * wb;
    p.q.railG += (KF_VALS[K_RAIL_G][3] - p.q.railG) * wb;
    p.q.railA += (KF_VALS[K_RAIL_A][3] - p.q.railA) * wb;
    p.q.needA += (KF_VALS[K_NEED_A][3] - p.q.needA) * wb;
    p.q.needF += (KF_VALS[K_NEED_F][3] - p.q.needF) * wb;
    p.q.needL += (KF_VALS[K_NEED_L][3] - p.q.needL) * wb;
    p.q.beadA += (KF_VALS[K_BEAD_A][3] - p.q.beadA) * wb;
    p.q.haze  += (KF_VALS[K_HAZE][3]   - p.q.haze)  * wb;
    p.q.seedA += (KF_VALS[K_SEED_A][3] - p.q.seedA) * wb;
    p.q.lift  += (KF_VALS[K_LIFT][3]   - p.q.lift)  * wb;

    p.q.coreI += 0.28f * Fs;
    p.q.coreR *= 1.0f + 0.25f * Fs;
    p.q.haze += 0.20f * Fs;

    p.q.gCore = 0.80f + 0.90f * odn;
    p.q.gLine = 0.88f + 0.56f * odn;
    p.q.coreR *= 0.92f + 0.40f * odn;
    p.q.bloom = 0.14f + 0.48f * odn;

    float cRad = p.q.coreR * S;
    if (cRad < 0.8f) cRad = 0.8f;
    p.q.coreInv = 1.0f / (cRad * cRad);
    p.q.hazeInv = 1.0f / (0.95f * S * 0.95f * S);

    float ag = p.flareAge / 3.4f;
    if (ag < 1.0f) {
        p.q.shA = 0.22f * PFMath::fastSin(PI * ag);
        p.q.shR = S * (0.12f + 1.5f * smoothF(ag));
    } else {
        p.q.shA = 0.0f;
    }

    for (int k = 0; k < p.nK; k++) {
        p.RR[k] = p.RR0[k] * S * (1.0f + 0.028f * PFMath::fastSin(p.phB + 0.45f * (float)k));
    }

    for (int i = 0; i < 256; i++) {
        float th = ((float)i + 0.5f) / 256.0f * DML_TAU - PI;
        p.warp[i] = 0.75f * DML_SC * (0.55f * PFMath::fastSin(3.0f * th + p.phW1) +
                             0.35f * PFMath::fastSin(5.0f * th - p.phW2 + 1.3f) +
                             0.20f * PFMath::fastSin(2.0f * th + 0.7f * p.phW2));
    }
    for (int i = 0; i < 192; i++) {
        p.rip[i] = 0.32f * DML_SC * PFMath::fastSin(DML_TAU * (((float)i + 0.5f) * 0.5f) / 13.0f - p.phR);
    }

    int nA = 0, nL = 0;
    p.nB = 0;
    for (int k = 0; k < 9; k++) p.ringArcCount[k] = 0;

    float lineAmp = p.q.railA * p.q.gLine;
    float g = p.q.railG;

    const float* rcR = isReactor2 ? RC_R2 : RC_R1;
    const float* rcG = isReactor2 ? RC_G2 : RC_G1;
    const float* rcB = isReactor2 ? RC_B2 : RC_B1;

    for (int t = 0; t < p.nT; t++) {
        p.tVis[t] = smoothF((cx - p.tThr[t]) / 0.15f);
        float amp = lineAmp * p.tVis[t];
        if (amp < 0.01f) continue;
        float pt = satF(g * 1.6f - 0.6f * p.tDel[t]);
        if (pt < 0.002f) continue;
        int m0 = p.tS[t];
        int m1 = m0 + p.tN[t];

        for (int m = m0; m < m1; m++) {
            float s0 = p.sT0[m], s1 = p.sT1[m];
            if (pt <= s0) break;
            float fr = satF((pt - s0) / (s1 - s0));
            float fa = amp * smoothF(fr * 8.0f);
            int kA = p.sK[m];

            if (p.sType[m] == 0) {
                if (nA >= 280) continue;
                float a0 = p.sA0[m] * DML_QPI;
                float a1 = p.sA1[m] * DML_QPI;
                float lo = a0 < a1 ? a0 : a1;
                float hi = a0 < a1 ? a1 : a0;
                float vlo, vhi;
                if (a1 >= a0) { vlo = lo; vhi = lo + (hi - lo) * fr; }
                else { vhi = hi; vlo = hi - (hi - lo) * fr; }
                if (vlo <= 0.001f) vlo = -10.0f;
                if (vhi >= DML_QPI - 0.001f) vhi = 10.0f;

                p.aLo[nA] = vlo;
                p.aHi[nA] = vhi;
                p.aAmp[nA] = fa;
                p.aCr[nA] = rcR[kA];
                p.aCg[nA] = rcG[kA];
                p.aCb[nA] = rcB[kA];

                if (kA >= 0 && kA < 9 && p.ringArcCount[kA] < 48) {
                    p.ringArcs[kA][p.ringArcCount[kA]++] = (uint16_t)nA;
                }
                nA++;
            } else {
                if (nL >= 280) continue;
                int kB = p.sK2[m];
                float al = p.sA0[m] * DML_QPI;
                float r0 = p.RR[kA];
                float r1 = p.RR[kB];
                float rv = r0 + (r1 - r0) * fr;

                p.lC[nL] = PFMath::fastCos(al);
                p.lS[nL] = PFMath::fastSin(al);
                p.lLo[nL] = r0 < rv ? r0 : rv;
                p.lHi[nL] = r0 < rv ? rv : r0;
                p.lAmp[nL] = fa * 0.85f;
                p.lCr[nL] = 0.5f * (rcR[kA] + rcR[kB]);
                p.lCg[nL] = 0.5f * (rcG[kA] + rcG[kB]);
                p.lCb[nL] = 0.5f * (rcB[kA] + rcB[kB]);
                nL++;
            }
        }

        float growing = p.s < 3.0f ? 1.0f : (p.s < 3.3f ? 1.0f - smoothF((p.s - 3.0f) / 0.3f) : 0.0f);
        float headEnv = smoothF(pt / 0.04f) * (1.0f - smoothF((pt - 0.93f) / 0.065f)) * growing;
        if (headEnv > 0.01f) {
            pathPos(p, t, pt);
            addBead(p, path_px, path_py, 1.1f * sc, amp * 0.6f * headEnv, rcR[5], rcG[5], rcB[5]);
        }
        if (pt > 0.01f) {
            pathPos(p, t, 0.0f);
            addBead(p, path_px, path_py, 0.7f * sc, amp * 0.45f * smoothF(pt * 15.0f), rcR[2], rcG[2], rcB[2]);
        }
        if (pt > 0.9f) {
            pathPos(p, t, 1.0f);
            addBead(p, path_px, path_py, 0.7f * sc, amp * 0.45f * smoothF((pt - 0.9f) * 10.0f), rcR[2], rcG[2], rcB[2]);
        }
        float pulseEnv = smoothF((pt - 0.9f) / 0.08f);
        if (pulseEnv > 0.01f) {
            float xf = p.phFlow + p.tOff[t];
            xf = PFMath::fract(xf);
            pathPos(p, t, xf);
            addBead(p, path_px, path_py, 0.7f * sc, amp * 0.4f * PFMath::fastSin(PI * xf) * pulseEnv, rcR[8], rcG[8], rcB[8]);
        }
    }
    p.nA = nA;
    p.nL = nL;

    for (int b = 0; b < U_BINS; b++) p.beadBinCount[b] = 0;
    for (int b = 0; b < p.nB; b++) {
        float minU = p.bX[b] - p.bRL[b];
        float maxU = p.bX[b] + p.bRL[b];
        int b0 = (int)(minU * 0.25f);
        int b1 = (int)(maxU * 0.25f);
        if (b0 < 0) b0 = 0;
        if (b1 >= U_BINS) b1 = U_BINS - 1;
        for (int bin = b0; bin <= b1; bin++) {
            if (p.beadBinCount[bin] < BEAD_CAP) {
                p.beadBin[bin][p.beadBinCount[bin]++] = (uint8_t)b;
            }
        }
    }

    float needAmp = p.q.needA * p.q.gLine;
    for (int j = 0; j < p.nRay; j++) {
        int rank = p.rayRank[j];
        float rvis = rank == 0 ? 1.0f : (rank == 1 ? smoothF((cx - 0.05f) / 0.2f) : (rank == 2 ? smoothF((cx - 0.5f) / 0.3f) : smoothF((cx - 0.72f) / 0.25f)));
        float ra = p.rayA[j] * DML_QPI;
        if (j >= 2) ra += 0.018f * PFMath::fastSin(p.phW1 + (float)j * 2.1f);
        p.rC[j] = PFMath::fastCos(ra);
        p.rS[j] = PFMath::fastSin(ra);
        float base = p.q.ringR * S * (1.0f + p.rayDel[j]);
        p.rBase[j] = base;
        p.rAmp[j] = needAmp * rvis;
        p.rLab[j] = p.q.needL * sc * p.rayLen[j];
        p.rLfr[j] = p.q.needF * p.rayLen[j];
        if (p.rayBead[j] > 0.0f) {
            addBead(p, base * p.rC[j], base * p.rS[j], p.rayBead[j] * p.q.beadS * sc, p.q.beadA * rvis * p.q.gLine, rcR[4], rcG[4], rcB[4]);
        }
    }

    p.sAmp = p.q.seedA * p.q.gLine;
    for (int k = 0; k < 5; k++) {
        p.sAng[k] += DML_TAU * p.sSpd[k] * ratio * dt;
        if (p.sAng[k] > DML_TAU) p.sAng[k] -= DML_TAU;
        else if (p.sAng[k] < -DML_TAU) p.sAng[k] += DML_TAU;

        float sr = p.sR[k] * S;
        float c0 = p.sAng[k];
        float hwid = p.sHW[k];
        p.sRpx[k] = sr;
        p.sNX[2 * k] = sr * PFMath::fastCos(c0 - hwid);
        p.sNY[2 * k] = sr * PFMath::fastSin(c0 - hwid);
        p.sNX[2 * k + 1] = sr * PFMath::fastCos(c0 + hwid);
        p.sNY[2 * k + 1] = sr * PFMath::fastSin(c0 + hwid);
    }
}

void update(float dt, const InputFrame& input) {
    PFParams::apply(input, 0, &knob_stage, 0.0f, 5.0f, 0.104f);
    PFParams::apply(input, 1, &knob_speed, 0.1f, 0.35f, 0.005f);
    PFParams::apply(input, 2, &knob_complexity, 0.3f, 1.0f, 0.015f);
    PFParams::apply(input, 3, &knob_overdrive, 0.4f, 1.0f, 0.012f);

    updateReactor(dt, input, reactor1, false);
    updateReactor(dt, input, reactor2, true);
}

// Pre-renders the 6 heavy symmetric components for 528 octant cells (D4 symmetry fold)
void renderOctant(const ReactorState& p, bool isReactor2) {
    float* bufR = oct_buf_r[isReactor2 ? 1 : 0];
    float* bufG = oct_buf_g[isReactor2 ? 1 : 0];
    float* bufB = oct_buf_b[isReactor2 ? 1 : 0];
    const ReactorParams& q = p.q;
    const float* gradR = isReactor2 ? GRAD_R2 : GRAD_R1;
    const float* gradG = isReactor2 ? GRAD_G2 : GRAD_G1;
    const float* gradB = isReactor2 ? GRAD_B2 : GRAD_B1;

    for (int iu = 0; iu < OCT_N; iu++) {
        float uu = (float)iu + 0.5f;
        int uBin = (int)(uu * 0.25f);
        if (uBin >= U_BINS) uBin = U_BINS - 1;
        int bCount = p.beadBinCount[uBin];
        const uint8_t* bList = p.beadBin[uBin];

        for (int iv = 0; iv <= iu; iv++) {
            int idx = iu_offsets[iu] + iv;
            float vv = (float)iv + 0.5f;
            float r = oct_geom_r[idx];
            float cr = 0.0f, cg = 0.0f, cb = 0.0f;

            // 1. Ambient Haze
            if (q.haze > 0.004f) {
                float q1 = r * r * q.hazeInv;
                if (q1 < 8.0f) {
                    float v = q.haze * GT[(int)(q1 * 64.0f)];
                    if (!isReactor2) { cr += v * 0.06f; cg += v * 0.09f; cb += v * 0.04f; }
                    else             { cr += v * 0.09f; cg += v * 0.04f; cb += v * 0.03f; }
                }
            }

            // 2. Plasma Core
            float coreI = q.coreI * q.gCore;
            if (coreI > 0.004f) {
                float re = r * (1.0f - 0.42f * oct_geom_lobe[idx]);
                float q1 = re * re * q.coreInv;
                if (q1 < 36.0f) {
                    float g1 = (q1 < 8.0f) ? GT[(int)(q1 * 64.0f)] : 0.0f;
                    float q2 = q1 * 0.30f;
                    float g2 = (q2 < 8.0f) ? GT[(int)(q2 * 64.0f)] : 0.0f;
                    float cI = coreI * (g1 + q.bloom * g2);
                    float hot = coreI * g1 * g1;
                    if (!isReactor2) {
                        cr += cI * 0.50f + hot * 0.99f;
                        cg += cI * 0.40f + hot * 0.90f;
                        cb += cI * 0.20f + hot * 0.75f;
                    } else {
                        cr += cI * 0.80f + hot * 1.00f;
                        cg += cI * 0.30f + hot * 0.85f;
                        cb += cI * 0.10f + hot * 0.50f;
                    }
                }
            }

            // 3. Flare Shock Ring
            if (q.shA > 0.004f) {
                float v = r - q.shR;
                float q1 = v * v * (1.0f / (2.4f * 2.4f * DML_SC * DML_SC));
                if (q1 < 8.0f) {
                    float g = q.shA * GT[(int)(q1 * 64.0f)];
                    if (!isReactor2) { cr += g * 0.87f; cg += g * 0.63f; cb += g * 0.37f; }
                    else             { cr += g * 1.00f; cg += g * 0.50f; cb += g * 0.20f; }
                }
            }

            // 4. Circuit Rails: Radial Links
            for (int l = 0; l < p.nL; l++) {
                if (r < p.lLo[l] - 0.5f || r > p.lHi[l] + 2.5f) continue;
                float v = vv * p.lC[l] - uu * p.lS[l];
                if (v > 2.4f * DML_LW || v < -2.4f * DML_LW) continue;
                float al = uu * p.lC[l] + vv * p.lS[l];
                float e1 = al - p.lLo[l] + 0.5f; if (e1 <= 0.0f) continue;
                float e2 = p.lHi[l] - al + 0.5f; if (e2 <= 0.0f) continue;
                float q1 = v * v * DML_LINE_I; if (q1 >= 8.0f) continue;
                float g = p.lAmp[l] * GT[(int)(q1 * 64.0f)] * (e1 > 1.0f ? 1.0f : e1) * (e2 > 1.0f ? 1.0f : e2);
                cr += g * p.lCr[l]; cg += g * p.lCg[l]; cb += g * p.lCb[l];
            }

            // 5. Needle Rays
            for (int j = 0; j < p.nRay; j++) {
                float ramp = p.rAmp[j]; if (ramp < 0.01f) continue;
                if (r < p.rBase[j] - 1.0f) continue;
                float v = vv * p.rC[j] - uu * p.rS[j];
                if (v > 2.6f * DML_LW || v < -2.6f * DML_LW) continue;
                float t0 = uu * p.rC[j] + vv * p.rS[j] - p.rBase[j];
                if (t0 < -1.0f) continue;
                float Lj = p.rLfr[j] * (oct_geom_ef[idx] - p.rBase[j]);
                if (Lj < p.rLab[j]) Lj = p.rLab[j];
                if (Lj < 1.0f) continue;
                float tt = t0 / Lj; if (tt > 1.0f || tt < 0.0f) continue;
                float sg = (0.80f - 0.35f * tt) * DML_LW;
                float q1 = v * v / (sg * sg); if (q1 >= 8.0f) continue;
                float om = 1.0f - tt;
                float prof = 0.28f + 0.72f * om * om * (0.6f + 0.4f * om);
                float st = clampF((t0 + 1.0f) * 0.625f, 0.0f, 1.0f);
                float en = clampF((tt - 0.86f) / 0.14f, 0.0f, 1.0f);
                en = 1.0f - en * en * (3.0f - 2.0f * en);
                float g = ramp * GT[(int)(q1 * 64.0f)] * prof * st * en;
                int gi = (int)(tt * 31.0f); if (gi > 31) gi = 31;
                cr += g * gradR[gi]; cg += g * gradG[gi]; cb += g * gradB[gi];
            }

            // 6. Pearls / Beads
            for (int bi = 0; bi < bCount; bi++) {
                int b = bList[bi];
                float ddx = uu - p.bX[b];
                float rl = p.bRL[b];
                if (ddx > rl || ddx < -rl) continue;
                float ddy = vv - p.bY[b];
                if (ddy > rl || ddy < -rl) continue;
                float d2 = ddx * ddx + ddy * ddy;
                float q1 = d2 * p.bI1[b];
                float q2 = d2 * p.bI2[b];
                float c1 = (q1 < 8.0f) ? GT[(int)(q1 * 64.0f)] : 0.0f;
                float c2 = (q2 < 8.0f) ? GT[(int)(q2 * 64.0f)] : 0.0f;
                float core = p.bAmp[b] * c1;
                float halo = p.bAmp[b] * 0.30f * c2;
                cr += core * 0.82f + halo * p.bHr[b];
                cg += core * 0.95f + halo * p.bHg[b];
                cb += core * 0.90f + halo * p.bHb[b];
            }

            bufR[idx] = cr;
            bufG[idx] = cg;
            bufB[idx] = cb;
        }
    }
}

// One reactor's light at pixel (x, y): its octant buffer plus the per-pixel rails and seed arcs.
inline void shadePixel(const ReactorState& p, bool isReactor2, int x, int y, int idx, int ab, int rb,
                       float& outR, float& outG, float& outB) {
    const int which = isReactor2 ? 1 : 0;
    float cr = oct_buf_r[which][idx];
    float cg = oct_buf_g[which][idx];
    float cb = oct_buf_b[which][idx];
    float r = oct_geom_r[idx];

    // Circuit Rails: Arcs (evaluated per pixel using fast radius bucketing)
    if (p.nA > 0) {
        float rw = r + p.warp[ab] + p.rip[rb];
        float ph = oct_geom_ph[idx];
        for (int k = 0; k < p.nK; k++) {
            float v = rw - p.RR[k];
            if (v > 1.92f * DML_LW || v < -1.92f * DML_LW) continue;
            int count = p.ringArcCount[k];
            if (count == 0) continue;
            float q1 = v * v * DML_LINE_I;
            float ringG = GT[(int)(q1 * 64.0f)];
            const uint16_t* arcList = p.ringArcs[k];
            for (int ai = 0; ai < count; ai++) {
                int a = arcList[ai];
                float e1 = (ph - p.aLo[a]) * r + 0.5f; if (e1 <= 0.0f) continue;
                float e2 = (p.aHi[a] - ph) * r + 0.5f; if (e2 <= 0.0f) continue;
                float g = p.aAmp[a] * ringG * (e1 > 1.0f ? 1.0f : e1) * (e2 > 1.0f ? 1.0f : e2);
                cr += g * p.aCr[a]; cg += g * p.aCg[a]; cb += g * p.aCb[a];
            }
        }
    }

    // Seed Arcs (only active in Stage 1)
    if (p.sAmp > 0.006f) {
        constexpr float NODE_R = 6.0f * DML_SC;
        constexpr float NODE_I = 1.0f / (DML_SC * DML_SC);
        float dx = (float)x - (DML_S - 0.5f);
        float dy = (float)y - (DML_S - 0.5f);
        float th = PFMath::fastAtan2(dy, dx);
        for (int k = 0; k < 5; k++) {
            float v = r - p.sRpx[k];
            if (v > 2.4f * DML_LW || v < -2.4f * DML_LW) continue;
            float dth = th - p.sAng[k];
            dth -= DML_TAU * PFMath::floorF((dth + PI) / DML_TAU);
            float e1 = (p.sHW[k] - fabsf(dth)) * r + 0.5f; if (e1 <= 0.0f) continue;
            float q1 = v * v * DML_LINE_I; if (q1 >= 8.0f) continue;
            float g = p.sAmp * GT[(int)(q1 * 64.0f)] * (e1 > 1.0f ? 1.0f : e1);
            if (!isReactor2) { cr += g * 0.38f; cg += g * 0.42f; cb += g * 0.22f; }
            else             { cr += g * 0.50f; cg += g * 0.25f; cb += g * 0.10f; }
        }
        for (int k = 0; k < 10; k++) {
            float ddx = dx - p.sNX[k]; if (ddx > NODE_R || ddx < -NODE_R) continue;
            float ddy = dy - p.sNY[k]; if (ddy > NODE_R || ddy < -NODE_R) continue;
            float dd = ddx * ddx + ddy * ddy; if (dd > NODE_R * NODE_R) continue;
            float q1 = dd * 2.2f * NODE_I;
            float q2 = dd * 0.22f * NODE_I;
            float s1 = (q1 < 8.0f) ? GT[(int)(q1 * 64.0f)] : 0.0f;
            float s2 = (q2 < 8.0f) ? GT[(int)(q2 * 64.0f)] : 0.0f;
            float sc1 = p.sAmp * 0.9f * s1, sh1 = p.sAmp * 0.34f * s2;
            if (!isReactor2) { cr += sc1 * 0.87f + sh1 * 0.38f; cg += sc1 * 0.63f + sh1 * 0.42f; cb += sc1 * 0.37f + sh1 * 0.22f; }
            else             { cr += sc1 * 0.90f + sh1 * 0.50f; cg += sc1 * 0.40f + sh1 * 0.20f; cb += sc1 * 0.20f + sh1 * 0.10f; }
        }
    }

    outR = cr * p.q.lift;
    outG = cg * p.q.lift;
    outB = cb * p.q.lift;
}

void draw() {
    PFCanvas::setFrame(FRAME_W, FRAME_H);

    renderOctant(reactor1, false);
    renderOctant(reactor2, true);

    for (int y = 0; y < FRAME_H; y++) {
        int iy = (y < OCT_N) ? (OCT_N - 1 - y) : (y - OCT_N);
        // Top half earthy (reactor 1), bottom half solar magma (reactor 2), a soft seam between.
        float w2 = smoothF(((float)y + 0.5f - DML_S + DML_SEAM) / (2.0f * DML_SEAM));
        for (int x = 0; x < FRAME_W; x++) {
            int ix = (x < OCT_N) ? (OCT_N - 1 - x) : (x - OCT_N);
            int iu = (ix > iy) ? ix : iy;
            int iv = (ix > iy) ? iy : ix;
            int idx = iu_offsets[iu] + iv;

            // Fold-derived 8-octant full circle angle index
            int pab = oct_geom_pab[idx];
            int ab;
            if (x >= OCT_N) {
                if (y >= OCT_N) ab = (ix >= iy) ? (128 + pab) : (192 - pab);
                else            ab = (ix >= iy) ? (128 - pab) : (64 + pab);
            } else {
                if (y >= OCT_N) ab = (iy >= ix) ? (192 + pab) : (256 - pab);
                else            ab = (ix >= iy) ? (pab) : (64 - pab);
            }
            if (ab > 255) ab = 255;
            else if (ab < 0) ab = 0;

            // the ripple keeps its wavelength in proportion to the reactor
            int rb = (int)(oct_geom_r[idx] * (2.0f / DML_SC));
            if (rb > 188) rb = 188;

            float cr, cg, cb;
            if (w2 <= 0.0f) {
                shadePixel(reactor1, false, x, y, idx, ab, rb, cr, cg, cb);
            } else if (w2 >= 1.0f) {
                shadePixel(reactor2, true, x, y, idx, ab, rb, cr, cg, cb);
            } else {
                float r1, g1, b1, r2, g2, b2;
                shadePixel(reactor1, false, x, y, idx, ab, rb, r1, g1, b1);
                shadePixel(reactor2, true, x, y, idx, ab, rb, r2, g2, b2);
                cr = r1 + (r2 - r1) * w2;
                cg = g1 + (g2 - g1) * w2;
                cb = b1 + (b2 - b1) * w2;
            }
            PFCanvas::setPixel(x, y, tone(cr), tone(cg), tone(cb));
        }
    }

    PFCanvas::present();
}

} // namespace DualMetamorphicLifecyclePattern