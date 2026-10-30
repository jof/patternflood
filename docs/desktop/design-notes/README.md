# Design notes: earlier research and project states

**Historical. Don't build from these.** They are the research and plans from
earlier stages of the project, kept as written, to compare with what was
finally built and to show why it changed. Parts, layouts and numbers in them
were superseded, and some contradict the current design. Dates, open questions
and "next steps" are as of when each was written. Each starts with a note
saying what replaced it.

The build as it stands: [`../BUILD.md`](../BUILD.md) and [`../wiring.md`](../wiring.md).

| Doc | What it was |
|---|---|
| [`build-prep.md`](build-prep.md) | The ordered plan for the Matrix Portal S3 build: first light, caliper session, orders |
| [`firmware-delta.md`](firmware-delta.md) | The ESP32 fork of upstream firmware: HUB75 pinout, memory, I²C encoders. Its patch is in [`../../../firmware/patches/`](../../../firmware/patches/) |
| [`power-plan.md`](power-plan.md) | Battery and USB-C power, then the switch to mains (§8) and mains safety (§9) |
| [`mechanical-plan.md`](mechanical-plan.md) | Front-panel layouts, the stackup, sensor mounting, and the measured P2 panel (§2.1) |
| [`fastener-concepts.md`](fastener-concepts.md) | Concepts for assembling the box with M3 hardware and no glue |
| [`pi-zero-w-controller.md`](pi-zero-w-controller.md) | The Pi Zero W controller and its USB gigabit adapter, before the Pi 5 |
