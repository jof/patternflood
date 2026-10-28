// Host stand-in for upstream's module SDK header (abi/pf_module.h), which a
// community pattern may include in place of the firmware's own headers: the
// same surface, from the shim and upstream's portable cores.
// License: MIT
#pragma once
#include <Arduino.h>
#include "config.h"
#include "src/core_canvas.h"
#include "src/core_encoders.h"
#include "src/core_math.h"
#include "src/core_color.h"
#include "src/core_noise.h"
#include "src/core_tables.h"
#include "src/core_mem.h"
#include "src/core_params.h"
