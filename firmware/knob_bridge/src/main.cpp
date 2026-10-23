// Patternflood desktop - development knob bridge.
//
// Scans the FeatherS3's STEMMA QT bus for Adafruit 4991 seesaw encoders
// (0x36-0x3D, set by the A0-A2 jumpers) and reports them over USB serial,
// one JSON object per line. Knobs are numbered k0.. in address order.
//
// Device -> host:
//   {"t":"scan","i2c":["0x37",...]}                 every address that ACKed
//   {"t":"hello","knobs":[{"k":0,"addr":"0x37"},...]}
//   {"t":"enc","k":0,"pos":12,"d":1}                position and change since last report
//   {"t":"btn","k":0,"down":1}
//   {"t":"hb","ms":12345,"ok":[1,1,1,1]}            every 2 s; ok = product id still reads 4991
//
// Host -> device (newline-terminated):
//   scan                 re-scan the bus and re-send hello
//   px <k|*> <rrggbb>    set a knob's NeoPixel (k = index, * = all)
//
// At boot each knob's pixel shows its index colour (k0 red, k1 green, k2 blue,
// k3 yellow, ...) dimly, so the physical knob <-> k mapping can be read off the
// box. The host replaces it with px.

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_seesaw.h>
#include <seesaw_neopixel.h>

static const uint8_t  ADDR_FIRST = 0x36;
static const uint8_t  ADDR_LAST  = 0x3D;
static const uint8_t  MAX_KNOBS  = ADDR_LAST - ADDR_FIRST + 1;
static const uint8_t  SS_SWITCH  = 24;  // encoder push switch on the 4991
static const uint8_t  SS_NEOPIX  = 6;   // NeoPixel data line on the 4991
static const uint16_t PID_4991   = 4991;

struct Knob {
  uint8_t          addr;
  seesaw_NeoPixel *ss;    // seesaw_NeoPixel is an Adafruit_seesaw, so one object does both
  int32_t          pos;
  bool             down;
};

static Knob    knobs[MAX_KNOBS];
static uint8_t nKnobs = 0;

static const uint32_t INDEX_COLOURS[] = {
  0x200000, 0x002000, 0x000020, 0x181800, 0x180018, 0x001818, 0x101010, 0x200800,
};

static bool ack(uint8_t addr) {
  Wire.beginTransmission(addr);
  return Wire.endTransmission() == 0;
}

static uint16_t productId(seesaw_NeoPixel *ss) {
  return (ss->getVersion() >> 16) & 0xFFFF;
}

static void setPixel(uint8_t k, uint32_t rgb) {
  knobs[k].ss->setPixelColor(0, (rgb >> 16) & 0xFF, (rgb >> 8) & 0xFF, rgb & 0xFF);
  knobs[k].ss->show();
}

static void scan() {
  for (uint8_t k = 0; k < nKnobs; k++) delete knobs[k].ss;
  nKnobs = 0;

  Serial.print("{\"t\":\"scan\",\"i2c\":[");
  bool first = true;
  for (uint8_t a = 0x08; a <= 0x77; a++) {
    if (!ack(a)) continue;
    Serial.printf("%s\"0x%02X\"", first ? "" : ",", a);
    first = false;
  }
  Serial.println("]}");

  for (uint8_t a = ADDR_FIRST; a <= ADDR_LAST; a++) {
    if (!ack(a)) continue;
    auto *ss = new seesaw_NeoPixel(1, SS_NEOPIX, NEO_GRB + NEO_KHZ800);
    if (!ss->begin(a) || productId(ss) != PID_4991) {
      Serial.printf("{\"t\":\"warn\",\"msg\":\"0x%02X is not a 4991 encoder\"}\n", a);
      delete ss;
      continue;
    }
    ss->pinMode(SS_SWITCH, INPUT_PULLUP);
    ss->setBrightness(255);  // colours from the host are taken as-is
    Knob &kn = knobs[nKnobs];
    kn.addr = a;
    kn.ss   = ss;
    kn.pos  = ss->getEncoderPosition();
    kn.down = !ss->digitalRead(SS_SWITCH);
    setPixel(nKnobs, INDEX_COLOURS[nKnobs % 8]);
    nKnobs++;
  }

  Serial.print("{\"t\":\"hello\",\"knobs\":[");
  for (uint8_t k = 0; k < nKnobs; k++) {
    Serial.printf("%s{\"k\":%u,\"addr\":\"0x%02X\"}", k ? "," : "", k, knobs[k].addr);
  }
  Serial.println("]}");
}

static void command(char *line) {
  char *cmd = strtok(line, " \t");
  if (!cmd) return;
  if (!strcmp(cmd, "scan")) {
    scan();
  } else if (!strcmp(cmd, "px")) {
    char *which = strtok(nullptr, " \t");
    char *hex   = strtok(nullptr, " \t");
    if (!which || !hex) { Serial.println("{\"t\":\"err\",\"msg\":\"px <k|*> <rrggbb>\"}"); return; }
    uint32_t rgb = strtoul(hex, nullptr, 16);
    if (!strcmp(which, "*")) {
      for (uint8_t k = 0; k < nKnobs; k++) setPixel(k, rgb);
    } else {
      int k = atoi(which);
      if (k < 0 || k >= nKnobs) { Serial.println("{\"t\":\"err\",\"msg\":\"no such knob\"}"); return; }
      setPixel(k, rgb);
    }
  } else {
    Serial.printf("{\"t\":\"err\",\"msg\":\"unknown command: %s\"}\n", cmd);
  }
}

static void readHost() {
  static char   buf[64];
  static size_t len = 0;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c == '\n') { buf[len] = 0; command(buf); len = 0; continue; }
    if (len < sizeof buf - 1) buf[len++] = c;
  }
}

void setup() {
  // FeatherS3: STEMMA QT is on the always-on LDO1; LDO2 (GPIO39) feeds the
  // onboard RGB LED and header 3V3. Enable it so nothing on the board is dark.
  pinMode(LDO2, OUTPUT);
  digitalWrite(LDO2, HIGH);
  delay(50);

  Serial.begin(115200);
  uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 3000) delay(10);

  Wire.begin();  // um_feathers3: SDA 8, SCL 9
  Wire.setClock(400000);
  scan();
}

void loop() {
  readHost();

  for (uint8_t k = 0; k < nKnobs; k++) {
    Knob &kn  = knobs[k];
    int32_t p = kn.ss->getEncoderPosition();
    bool    d = !kn.ss->digitalRead(SS_SWITCH);
    if (p != kn.pos) {
      Serial.printf("{\"t\":\"enc\",\"k\":%u,\"pos\":%ld,\"d\":%ld}\n", k, (long)p, (long)(p - kn.pos));
      kn.pos = p;
    }
    if (d != kn.down) {
      Serial.printf("{\"t\":\"btn\",\"k\":%u,\"down\":%u}\n", k, d);
      kn.down = d;
    }
  }

  static uint32_t lastHb = 0;
  if (millis() - lastHb >= 2000) {
    lastHb = millis();
    Serial.printf("{\"t\":\"hb\",\"ms\":%lu,\"ok\":[", (unsigned long)lastHb);
    for (uint8_t k = 0; k < nKnobs; k++) {
      Serial.printf("%s%u", k ? "," : "", productId(knobs[k].ss) == PID_4991);
    }
    Serial.println("]}");
  }

  delay(5);
}
