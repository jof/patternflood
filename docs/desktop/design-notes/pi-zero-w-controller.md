# The Pi Zero W controller

> **Design history:** the first in-box controller, a Raspberry Pi Zero W with a
> USB gigabit adapter, before the Raspberry Pi 5 replaced it. The Zero W still
> runs the appliance image (armhf), but only upstream's native presets reach a
> usable frame rate (about 12 fps; our numpy demos 2–7). Current wiring:
> [`../wiring.md`](../wiring.md).

The header wiring (knobs, buttons, console) is the same on both boards. What
differed is the link to the card, and its power.

## 1. Pi → Colorlight card (Ethernet)

```
  Pi Zero W "USB" port (micro-USB OTG, the one nearer the middle)
     └─ micro-B-to-A OTG cable ─ USB gigabit Ethernet adapter ─ Cat6 ─ 5A-75B (either RJ45)
```

- **The adapter must be gigabit** (e.g. RTL8153 or ASIX AX88179). The 5A-75B
  won't link at 100 Mbit. Over the Zero's USB 2.0 it runs at about 300 Mbit/s,
  far more than the frames need.
- **Use an OTG cable, not a plug-style OTG dongle.** On 2026-10-22 two RTL8153
  adapters never worked through a dongle. On 2026-10-26 a plain micro-B-to-A OTG
  cable (no power input) ran the generic one at high speed, powered from the
  Zero's port (§2).
- **⚠ Plug the adapter in with the Pi off.** Hot-plugging it browns the Pi out.

### 1.1 Power-injected USB extension (fallback, not needed so far)

Open a USB-A extension's jacket partway along, between the OTG dongle and the
adapter:

| Wire | Change |
|---|---|
| Red (VBUS) | **Cut.** Adapter-side end to the LRS +5 V; tape off the Pi-side end |
| Black (GND) | Leave it continuous to the Pi, **and** run a wire from it to the LRS GND |
| Green (D+), white (D−), shield | Unchanged |

The adapter then draws from the PSU, and the Zero's port carries data only. Never
join the two 5 V feeds: the Pi-side red stays cut. A powered USB hub does the same
job.
- The appliance gives any wired interface 192.168.75.1/24. receiver75 is at
  192.168.75.39.

## 1.2 Power

Two options, both from the LRS-50-5's 5 V (trim to about 5.15 V, as in
[`power-plan.md`](power-plan.md)):

- **"PWR IN" micro-USB, through a 5 V pigtail.** The simplest, and it keeps the
  Zero's input protection in the path.
- **Header pin 2 (5 V) and pin 6 (GND).** Tidier inside the box, but it
  bypasses the micro-USB input's protection, so the supply has to be right.

The Zero W draws about 0.2–0.35 A. The USB gigabit adapter draws more than first
assumed: an Anker RTL8153 measured **0.41 A** on a PC with no link. Budget about
0.5 A for it, from its own feed (§1.1).

## 2. USB Ethernet on the bare Zero port: findings, 2026-10-22

Kernel 6.18.50, `dwc_otg` in host mode through a micro-B-to-A OTG dongle:

| Test | Result |
|---|---|
| SanDisk USB stick, through the dongle (and through dongle + extension) | **High speed**, every time |
| Generic RTL8153, Anker RTL8153 | No connect at all on some boots (`HPRT0 = 0x00001000`, D+ never pulled up). On others, **full speed with `device descriptor read/64, error -71`**, then the hub driver powers the port off |
| Same adapters on a desktop PC (xHCI) | Enumerate at once, at high speed |
| 5 V at the header, meter min-hold through boot | **5.045 V** min, 4.993 V with the Anker drawing; `throttled=0x0` |
| 5 V at the adapter on the Pi (inline USB meter) | 4.89 V, 0.635 A; later **4.81 V, 0.90 A**, and the Anker got hot |
| Anker on a desktop PC, same meter (no data) | 4.62 V, **0.41 A** |
| Panels and encoders off the PSU | No change |
| Hot-plugging an adapter | **Resets the Pi** (brown-out: the console stops with no panic) |
| True cold start (PSU off, adapter in, PSU on) | Still no connect |
| **Pi Zero 2 W** (patternflood card, same dongle chain, RTL8153) | **Same:** port powered, no connect, after a minute |

- The Anker no longer enumerated on a desktop PC afterwards. Take it as damaged.
- Two different Zeros fail the same way, so it isn't one bad board. Both tests shared the OTG dongle and the PSU.
- RTL8153 adapters on Zeros are a common working setup elsewhere, so **the dongle is the main suspect**. The stick proved its data lines, but only at about a tenth of the adapter's 0.4–0.9 A.
- The supply level at the Pi is fine.
- The mechanism isn't pinned down without a scope; candidates are the dongle's contacts under load, and latch-up after the brown-outs. `dwc_otg.speed=1` doesn't help, because full speed already fails, and it's too slow for frames anyway.
- **Next:** replace the dongle with a proper micro-B-to-A OTG cable, ideally a "Y" one with a separate power input. Or use §1.1, or a powered hub. Don't hot-plug adapters on the Zero.

**Resolved, 2026-10-26: it was the dongle.** The fix was a plain micro-B-to-A OTG cable, with no power input. On the Zero W, with the same card, the generic RTL8153 plugged in and a cold boot:

| Check | Result |
|---|---|
| Enumeration | `usb 1-1: new high-speed USB device` at 5.6 s; r8152 binds it as `eth0` |
| Supply | `throttled=0x0` |
| Link to the 5A-75B (direct Cat6) | **1000 Mb/s full duplex**; `colorlight` profile up at 192.168.75.1; card at .39 in ARP |
| Renderer (`--res 64 --fps 30`) | Plasma shows on the panels; 27k packets, 0 TX errors. **10–15 fps**, CPU-bound (0 % idle: python 63 %, sys + softirq 30 %) |

- Still plug the adapter in before power-on.
- `pf-splash` step 5 in `ExecStartPre` fails with `no wired link` if the Cat6 isn't in at boot. It's harmless; the renderer starts anyway.

A small script shows the port's state on the ACT LED at 20 Hz (off / blinking for D+ pulled up /
solid once enumerated), for cable-flex tests.

