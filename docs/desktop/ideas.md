# Ideas for Rev 3 and later

Hacks and improvements to consider for future revisions of the desktop box.
None of these have been started. Many need cutouts in the walls, so it's best to
gather them into one enclosure revision.

## Sound

- **Mic in:** a 1/4" mic jack, holes on the side to hold a small mic stand, and a
  cabled microphone. That closes the loop back to Nam June Paik's
  *Participation TV*, the work behind the whole project.
- **Audio out:** a 1/4" output jack, maybe with a small internal amp and speaker.

## Sensing and feedback

- **Camera with a mechanical shutter**, so you can see when it's covered.
- **Ambient light sensor** to set the brightness automatically.
- **Haptics:** vibration behind the knobs, or a linear actuator that knocks.

## Software

- **A web UI:** built, as the [web remote](../../firmware/demos/README.md#web-remote) at http://patternflood.local/.
- **OSC endpoints** for remote control.
- **Dream demo:** ask the audience to describe their dream demo, then run speech
  to text into a coding harness and show the result on the display.

## Power and security

- **USB-C power only,** so it can run from a battery bank. The panels' current
  cap matters here (see [`driver-colorlight.md`](driver-colorlight.md)).
- **AirTag slot** in the enclosure.
- **Kensington lock slot.**

## Mechanical
- Stiffen the mouting for the top-most and bottom-most panel mounting rails. In 2.x, these are single-layer 3mm wood, and with all the wires behind everything, it kinda bulges the panel out.
- Each panel should have a scored identifier with like a name, so that it's clear to the assembler where to place it. For example, the two bottom panels should be labeled so that the user does lay it up backwards.
