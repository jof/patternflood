# Vendor CAD

Third-party models, unmodified. Import into Onshape with **Insert → Import**.

| File | Part | Source | License |
|---|---|---|---|
| `adafruit-5778-matrix-portal-s3.step` | Matrix Portal S3 | [Adafruit_CAD_Parts](https://github.com/adafruit/Adafruit_CAD_Parts) `5778 Matrix Portal S3` | MIT |
| `adafruit-4991-qt-rotary-encoder.step` | I2C QT Rotary Encoder breakout | [Adafruit_CAD_Parts](https://github.com/adafruit/Adafruit_CAD_Parts) `4991 QT Rotary Encoder` | MIT |

That repo indexes 472 parts by Adafruit product ID and also carries `.f3d` and
`.stl` for each. These two were the only BOM parts present — the PID 377
encoder, both knob sets and the STEMMA QT cables are not in it, and are modelled
as proxies instead. See [`onshape-workflow.md`](../../../docs/desktop/onshape-workflow.md) §4.

No Waveshare panel model is published; it's a proxy box built from measurements.
