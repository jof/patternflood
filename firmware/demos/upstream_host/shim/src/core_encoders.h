// Host stand-in: the InputFrame patterns receive. Field order matches upstream's
// src/core_encoders.h (mirrored by abi/pf_abi.h::PFInputFrame).
// License: MIT
#pragma once
#include <Arduino.h>
#include "config.h"

struct InputFrame {
  long knobs[4];
  int knobDeltas[4];
  bool btnPressed[4];
  bool btnHeld[4];
  uint32_t now;
  bool knobAudioActive[4];
  float knobAudioValue[4];
  bool paramAbsoluteActive[4];
  uint16_t paramAbsolute[4];
};
