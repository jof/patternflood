# Vendor CAD

Third-party models, unmodified. Import into Onshape with **Insert → Import**.

| File | Part | Source | License |
|---|---|---|---|
| `adafruit-5778-matrix-portal-s3.step` | Matrix Portal S3 | [Adafruit_CAD_Parts](https://github.com/adafruit/Adafruit_CAD_Parts) `5778 Matrix Portal S3` | MIT |
| `adafruit-4991-qt-rotary-encoder.step` | I2C QT Rotary Encoder breakout | [Adafruit_CAD_Parts](https://github.com/adafruit/Adafruit_CAD_Parts) `4991 QT Rotary Encoder` | MIT |
| `adafruit-5991-husb238-pd-sink.step` | HUSB238 USB-C PD sink, I2C / switchable, STEMMA QT | [Adafruit_CAD_Parts](https://github.com/adafruit/Adafruit_CAD_Parts) `5991 HUSB238 USBC` | MIT |
| `adafruit-5807-husb238-pd-sink-fixed.step` | HUSB238 USB-C PD sink, I2C / fixed | [Adafruit_CAD_Parts](https://github.com/adafruit/Adafruit_CAD_Parts) `5807 HUSB238 Breakout` | MIT |
| `meanwell-lrs-50-5.step` | **Mean Well LRS-50 PSU** — the real one, 31 bodies | Mean Well vendor STEP (2017), via the public Onshape doc [`a46bc672`](https://cad.onshape.com/documents/a46bc672af8b94f9d83c7e9c) *MeanWell LRS-50* (Bukovinets) | vendor CAD |
| `waveshare-p2.5-64x64-rgb-matrix.step` | **Waveshare P2.5 64×64 RGB matrix** — ⚠ 160 × 160, and internally inconsistent; **no longer used**, see below | public Onshape doc [`731770dc`](https://cad.onshape.com/documents/731770dceeb7b7026a08d951) *HegBoard GanArray* (Samuel Gan) | third-party |
| *(not imported)* | **IEC AC-14-F16A** inlet — consulted for the flange screw spacing only | public Onshape doc [`a0851c0b`](https://cad.onshape.com/documents/a0851c0ba6a0a5e0e3d6bbcf) *DC POWER SUPPLY* (Simon Page), `AC INLET` studio | third-party |

That repo indexes 472 parts by Adafruit product ID and also carries `.f3d` and
`.stl` for each. These two were the only BOM parts present — the PID 377
encoder, both knob sets and the STEMMA QT cables are not in it, and are modelled
as proxies instead. See [`onshape-workflow.md`](../../../docs/desktop/onshape-workflow.md) §4.

A Waveshare panel model now exists in this folder, but **it is the P2.5
(160 × 160), not the P2 64×64 (128 × 128) this build uses** — see the warning in
the measured table below. It is here as shape and layout evidence, not as the
part. The enclosure still drives off the parametric proxy.

## Measured from these STEPs

Extracted by parsing the STEP text rather than opening a viewer — useful when a
vendor publishes no drawing.

| Part | Envelope | Notes |
|---|---|---|
| Matrix Portal S3 | 77.47 × 53.50 × 19.10 | rides ON the HUB75 header, so reaches ~20 mm behind the panel |
| HUSB238 5807 | 25.97 × 28.55 × 13.38 incl. terminal block | PCB 1.57 mm; 2 × Ø2.5 holes on **15.24 mm (0.6″)** centres, at the end opposite the USB-C receptacle |
| Adafruit 5036 panel (P2.5 64×32) | 160 × 80 × 17.5 | 4 × M3 posts, inset 12.45/12.50 in x and 15.75 in y |
| **Waveshare P2.5 64×64** | **160 × 160 × 16.5** | 4 × M3 posts at **(±63.5, ±63.5)** — a **16.5 mm inset**, equal in both axes |
| **Mean Well LRS-50** | 99 × 82 × 30 | side M3 at **x = 10 and 84 from the terminal end**, **z = 15** (dead centre of the 30 mm height); terminal block **5 ways at 9.3 mm pitch**, Ø6.5 screw heads sunk ~10 mm below the cover, **screws facing out of the cover** |
| **IEC AC-14-F16A** | flange 48.6 × 58.2, 34.0 deep | flange screws **40.0 mm apart, Ø3.5**, on the short (lobed) axis. Only this one number was taken — the rest disagrees with our calipers by ~1 mm |

> **Two of these three third-party models were wrong in ways that cost time.**
> The rule that came out of it: *take the one number the model is authoritative
> about, and keep your own measurements for everything else.* A hand-made model
> is evidence about a hole pattern, not about a size.

> ⚠️ **The Waveshare row is a P2.5, and this build uses P2.** 160 mm vs 128 mm
> body, 16.5 mm vs 14.5 mm depth. Do not point `#panelBody` at it. What it is
> good for is the one thing nobody publishes: what a Waveshare 64×64 rear
> actually looks like, and a third inset data point for
> [`enclosure-lasercut.md`](../../../docs/desktop/enclosure-lasercut.md) §11.
