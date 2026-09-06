# Architecture Options

Raised mid-planning: a Raspberry Pi + Colorlight 5A-75B path, for more compute
at the cost of electrical power. Worth taking seriously, and worth separating
into its two independent halves before deciding anything.

---

## 1. Two axes, not one

"Pi + Colorlight" bundles two decisions that don't have to move together:

| Axis | Question | Answered by |
|---|---|---|
| **Compute** | Can the host process a 2268-zone depth map and still paint pixels? | Pi vs. ESP32 |
| **Panel driving** | How many panels, at what bit depth and refresh? | Colorlight/FPGA vs. bit-banged DMA |

**For this build, only the compute axis is under real pressure.** Two panels is
8192 pixels — four, if the spares get used, is 16384. That is nowhere near the
point where panel driving needs an FPGA. The 5A-75B has 8 HUB75 outputs and
drives dozens of panels; using it for two is like renting a truck to move a
bookshelf.

So: **the lidar is the reason to want a Pi. The Colorlight is a separate,
later, and mostly unrelated question.** Keeping them separate makes the
decision much easier.

---

## 2. The four architectures

### A. Matrix Portal S3 — the current plan

What's already planned in [`mechanical-plan.md`](../desktop/mechanical-plan.md) and
[`firmware-delta.md`](../desktop/firmware-delta.md).

- **Compute:** 240 MHz Xtensa, 2 MB quad PSRAM. Tight — see firmware-delta §2.
- **Panels:** I²S DMA bit-bang, 5–6 bit colour at this memory budget.
- **Power:** ~0.5–1 W on top of the panels.
- **Keeps:** *everything*. `.pfm` loader, frozen ABI, features/editions,
  web console, browser flasher, Pattern Lab → device pipeline, the whole
  community pattern library.
- **Lidar:** binning 6–8, ~130–250 zones at 25–60 fps. Real, but capped.

### B. ESP32 + Pi as a lidar co-processor — the hybrid

Matrix Portal keeps driving the panels and running Patternflow unchanged. A Pi
Zero 2 W (or any small Linux box) does nothing but talk to the VL53L9CX, do the
depth processing, and hand back four scalars over UART.

```
   VL53L9CX ──I²C──► Pi Zero 2 W ──UART──► Matrix Portal S3 ──HUB75──► panels
                     full 2268 zones,        paramAbsolute[0..3]
                     blob tracking,          (existing ABI tier —
                     whatever you like        no changes at all)
```

- **Compute:** full resolution, real point-cloud work, even pose estimation.
- **Power:** +1.5–2.5 W. Cheapest compute upgrade on the list.
- **Keeps:** everything in A. The Patternflow firmware doesn't know the Pi
  exists — it just sees absolute param values arriving, exactly as the audio
  tier already does.
- **Cost:** two boards, two things to boot, a serial protocol to define.

This is the **highest ratio of gain to loss** on the list, and it exists only
because of the `paramAbsolute` finding in [`lidar-plan.md`](lidar-plan.md) §2 —
there is already a documented way for an outside source to drive the knobs.

### C. Raspberry Pi + hzeller `rpi-rgb-led-matrix`

Pi does everything: panels via GPIO through an active-3 adapter, lidar over
I²C/USB, patterns in whatever language you like.

- **Compute:** unconstrained by comparison. GPU shaders via VideoCore are on the
  table — patterns as GLSL rather than hand-written C++ pixel loops.
- **Panels:** hzeller's library is mature, well-understood, and trivially
  handles 2–4 panels. No FPGA anywhere.
- **Power:** +3–7 W (Pi 4) or +5–12 W (Pi 5).
- **Loses:** the entire upstream firmware. See §3 — this is the real cost.

### D. Raspberry Pi + Colorlight 5A-75B

Pi computes; an ECP5 FPGA on a ~$20 repurposed LED receiver card does the panel
driving over Ethernet.

The 5A-75B is a Lattice **LFE5U-25F**, two Gigabit Ethernet PHYs, two 2 MB
166 MHz SDRAMs, 8 HUB75 outputs on 5 V level shifters, fully supported by the
open toolchain (Yosys / nextpnr / Project Trellis), and comprehensively reverse
engineered by the [chubby75](https://github.com/q3k/chubby75) project.

Two sub-paths, and they are very different amounts of work:

- **D1 — stock firmware, reverse-engineered protocol.** Leave the card's own
  firmware alone and send it Colorlight receiver frames over raw Ethernet from
  the Pi. **No FPGA development at all.** Much the easier path, and the one to
  try first if this route is taken.
- **D2 — custom gateware.** Write your own HUB75 driver in the ECP5. Total
  control: 14–16 bit colour, >3 kHz refresh, arbitrary scan patterns, and in
  principle even the S-PWM panels upstream's compatibility doc writes off as
  impossible. This is a genuine FPGA project — a fun one, and a separate one.

- **Power:** +3–4 W for the card (the two GbE PHYs are the hungry part), on top
  of the Pi.
- **Gains that are real:** bit depth and refresh. FPGA-generated PWM at 14+ bits
  is visibly better than 5–6 bits of I²S DMA — smoother gradients, no banding in
  dark scenes. Whether that matters depends on the patterns.
- **Gains that are theoretical here:** panel count. Nothing in this BOM needs 8
  chains.

---

## 3. What C and D actually cost

This is the part that decides it, and it's easy to undercount.

Upstream Patternflow is **ESP32 Arduino/C++ throughout**. Going to a Pi host
abandons:

- the `.pfm` module loader and the 128-slot install system
- the **frozen ABI** (`pf_module.h`, `pf_params.h`, `abi.sums`, CI enforcement)
- the features/editions structure from [`EDITIONS.md`](../../upstream/docs/EDITIONS.md)
- the web console, the browser flasher, `/update`, sleep mode
- **the community pattern library** — 100+ patterns compiled for Xtensa
- Pattern Lab's build-and-install-over-Wi-Fi pipeline, the thing that makes
  adding a pattern take ten seconds

That is not a port. It's a reimplementation of the host, keeping only the idea.

**One real mitigation:** patterns don't *originate* as C++. They start as
**JavaScript** in the Live Editor, and Pattern Lab compiles them to `.pfm`. A Pi
host could run the JavaScript form directly — QuickJS, or Node, or straight to
GLSL — and stay meaningfully compatible with the community library at the
*source* level even though the binaries don't transfer. That's speculative, but
it's the difference between "incompatible" and "a different backend for the
same patterns", and it's the thing to investigate before committing to C or D.

**Two smaller costs worth naming:**
- **Boot time.** Instant vs. 20–30 seconds. For an instrument you switch on,
  that is felt every single time.
- **SD card corruption.** A battery-powered device gets switched off abruptly.
  Plan a read-only rootfs from day one, not after the first dead card.

---

## 4. Power, concretely

Against the ~10 W typical panel load from [`power-plan.md`](../desktop/power-plan.md), on a
20 000 mAh bank:

| | Host overhead | Total typical | Runtime |
|---|---|---|---|
| **A** Matrix Portal S3 | ~1 W | ~11 W | **~5.5 h** |
| **B** + Pi Zero 2 W | ~2 W | ~12 W | **~5 h** |
| **C** Pi 4 | ~5 W | ~15 W | **~4 h** |
| **C** Pi 5 | ~9 W | ~19 W | **~3.3 h** |
| **D** Pi 4 + 5A-75B | ~8 W | ~18 W | **~3.5 h** |

Your instinct was right — D roughly halves runtime versus A. It also pushes the
5 V budget: the Colorlight and Pi want clean, well-regulated 5 V alongside a
panel load that swings by amps, which makes the buck converter's job harder than
[`power-plan.md`](../desktop/power-plan.md) assumes.

---

## 5. Recommendation

**Stay on A, and hold B in your pocket.**

The reasoning:

1. **The compute pressure is entirely the lidar's**, and B relieves it for ~2 W
   without giving up a single thing. The `paramAbsolute` tier means a
   co-processor integrates with *zero* firmware architecture change.
2. **The panel-driving pressure doesn't exist yet.** Two panels, maybe four.
   The Colorlight's value starts at an order of magnitude more than that.
3. **A's real constraint is memory, not MHz** — 2 MB quad PSRAM, per
   firmware-delta §2. If that's what bites, the fix is a different ESP32 module
   (an N16R8 DevKit on a carrier, back toward upstream's own design) long before
   it's a Pi.
4. Upstream is explicitly built to be forked — the RFC's whole point is that
   "each individual Patternflow gets made and shared by whoever makes it", with
   `features/` and `bundles/` as the seams. Staying on ESP32 means this fork can
   **track upstream**. C and D mean it can't, ever.

**Revisit D if any of these become true:**
- panel count grows past ~8 (all four spares plus more)
- 5–6 bit colour depth turns out to be visibly banding on your patterns
- you want the S-PWM panels upstream can't drive
- the FPGA work becomes the point rather than the cost

That last one is not a joke. D2 is a legitimately interesting project and you
clearly have the toolchain for it. But it is a **different project** that
happens to share a BOM — better done deliberately than arrived at while trying
to finish this one.

---

## 6. If C or D is taken anyway

Investigate in this order, because the first item decides how painful it is:

1. **Can the Live Editor's JavaScript patterns run on the Pi host?** (§3) This
   determines whether you keep the community library in any form.
2. **D1 before D2** — reverse-engineered Colorlight protocol with stock
   firmware, before writing gateware. It may be entirely sufficient.
3. **Read-only rootfs and power-fail behaviour** before the enclosure closes.
4. **Re-do the power plan.** The 5 V budget and the converter sizing in
   [`power-plan.md`](../desktop/power-plan.md) assume a ~1 W host.
