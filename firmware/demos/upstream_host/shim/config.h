// Host stand-in for upstream's config.h: the panel size and nothing else.
// The size comes from the build (-DPANEL_RES_W/H); the desktop 2x2 is 128 x 128.
// License: MIT
#pragma once
#ifndef PANEL_RES_W
#define PANEL_RES_W 128
#endif
#ifndef PANEL_RES_H
#define PANEL_RES_H 128
#endif
#define PANEL_CHAIN 1
