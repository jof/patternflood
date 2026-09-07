# Vendor CAD

Third-party models, unmodified. Import into Onshape with **Insert → Import**.

| File | Part | Source | License |
|---|---|---|---|
| `adafruit-5778-matrix-portal-s3.step` | Matrix Portal S3 | [Adafruit_CAD_Parts](https://github.com/adafruit/Adafruit_CAD_Parts) `5778 Matrix Portal S3` | MIT |
| `adafruit-4991-qt-rotary-encoder.step` | I2C QT Rotary Encoder breakout | [Adafruit_CAD_Parts](https://github.com/adafruit/Adafruit_CAD_Parts) `4991 QT Rotary Encoder` | MIT |
| `adafruit-5991-husb238-pd-sink.step` | HUSB238 USB-C PD sink, I2C / switchable, STEMMA QT | [Adafruit_CAD_Parts](https://github.com/adafruit/Adafruit_CAD_Parts) `5991 HUSB238 USBC` | MIT |
| `adafruit-5807-husb238-pd-sink-fixed.step` | HUSB238 USB-C PD sink, I2C / fixed | [Adafruit_CAD_Parts](https://github.com/adafruit/Adafruit_CAD_Parts) `5807 HUSB238 Breakout` | MIT |

That repo indexes 472 parts by Adafruit product ID and also carries `.f3d` and
`.stl` for each. These two were the only BOM parts present — the PID 377
encoder, both knob sets and the STEMMA QT cables are not in it, and are modelled
as proxies instead. See [`onshape-workflow.md`](../../../docs/desktop/onshape-workflow.md) §4.

No Waveshare panel model is published; it's a proxy box built from measurements.

## Measured from these STEPs

Extracted by parsing the STEP text rather than opening a viewer — useful when a
vendor publishes no drawing.

| Part | Envelope | Notes |
|---|---|---|
| Matrix Portal S3 | 77.47 × 53.50 × 19.10 | rides ON the HUB75 header, so reaches ~20 mm behind the panel |
| HUSB238 5807 | 25.97 × 28.55 × 13.38 incl. terminal block | PCB 1.57 mm; 2 × Ø2.5 holes on **15.24 mm (0.6″)** centres, at the end opposite the USB-C receptacle |
| Adafruit 5036 panel (P2.5 64×32) | 160 × 80 × 17.5 | 4 × M3 posts, inset 12.45/12.50 in x and 15.75 in y — the only real panel mounting data found |
