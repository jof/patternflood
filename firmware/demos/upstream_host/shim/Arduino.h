// Host stand-in for the Arduino core: just what upstream's pattern headers use.
// License: MIT
#pragma once
#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <cmath>
#include <cstdlib>
#include <random>
#include <type_traits>

using std::abs;     // float abs(), as Arduino's macro allows

#ifndef PI
#define PI 3.1415926535897932384626433832795
#endif
#define HALF_PI 1.5707963267948966192313216916398
#define TWO_PI 6.283185307179586476925286766559
#define DEG_TO_RAD 0.017453292519943295769236907684886
#define RAD_TO_DEG 57.295779513082320876798154814105
#define IRAM_ATTR

typedef bool boolean;
typedef uint8_t byte;

// Arduino's min/max/constrain are macros that take mixed types. Return by value:
// decltype(a < b ? a : b) would be a reference to a parameter, dangling on return.
template <class A, class B> inline std::common_type_t<A, B> min(A a, B b) { return b < a ? b : a; }
template <class A, class B> inline std::common_type_t<A, B> max(A a, B b) { return a < b ? b : a; }
template <class T, class L, class H> inline T constrain(T x, L lo, H hi) {
  return x < (T)lo ? (T)lo : (x > (T)hi ? (T)hi : x);
}
inline long map(long x, long in_min, long in_max, long out_min, long out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

// The host sets the clock before each frame (pf_frame's `now`).
inline uint32_t pf_host_now_ms = 0;
inline unsigned long millis() { return pf_host_now_ms; }
inline unsigned long micros() { return (unsigned long)pf_host_now_ms * 1000UL; }
inline void delay(unsigned long) {}

inline std::mt19937& pf_host_rng() { static std::mt19937 r(12345); return r; }
inline void randomSeed(unsigned long s) { pf_host_rng().seed((uint32_t)s); }
inline long random(long hi) { return hi <= 0 ? 0 : (long)(pf_host_rng()() % (uint32_t)hi); }
inline long random(long lo, long hi) { return hi <= lo ? lo : lo + random(hi - lo); }
inline uint32_t esp_random() { return pf_host_rng()(); }

struct PFHostSerial {
  template <class... A> void print(A...) {}
  template <class... A> void println(A...) {}
  template <class... A> void printf(const char*, A...) {}
};
inline PFHostSerial Serial;
