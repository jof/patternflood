# Pi controller appliance

Raspberry Pi OS Lite (trixie), set up to boot straight into the demos
([`../demos`](../demos/README.md)): knobs on I²C, frames over Ethernet to
receiver75 on the Colorlight card. Hold k0 and k3 for a second for the menu
that switches demos. The Pi 5 runs the arm64 image and uses its own gigabit port. (The
Pi Zero W, the first controller, runs the armhf image with a USB gigabit adapter:
[`pi-zero-w-controller.md`](../../docs/desktop/design-notes/pi-zero-w-controller.md).) Wiring: [`docs/desktop/wiring-pi-controller.md`](../../docs/desktop/wiring.md).

## Making a card

1. Write the image and verify it. One write on the bench reader had a 12 KiB
   bad stretch, so always compare after writing:
   ```sh
   xz -dk 2026-10-06-raspios-trixie-arm64-lite.img.xz      # armhf for the Zero W
   sudo dd if=…img of=/dev/sdX bs=4M conv=fsync
   sudo cmp -n $(stat -c %s …img) …img /dev/sdX
   ```
2. Mount both partitions and run, as root:
   ```sh
   sudo ./provision_card.py --boot BOOT --root ROOT --userconf userconf.txt \
       --wifi-ssid YOUR_SSID --wifi-pass-file wifi.pass --ssh-key ~/.ssh/id_ed25519.pub
   ```
   `userconf.txt` holds `USER:HASH` (the hash from `openssl passwd -6`); `wifi.pass`
   holds the passphrase. Neither belongs in the repo. Use the same user name as on
   your own machine and `ssh patternflood.local` needs no `USER@`. The script tells the image's
   architecture from its rootfs and builds the matching `pf-splash`
   (`arm-linux-gnueabihf-gcc` for armhf, `aarch64-linux-gnu-gcc` for arm64).

## What it sets up

| | |
|---|---|
| User | `pi` renamed to yours by `userconf.txt`; SSH key only; passwordless sudo from `/etc/sudoers.d/010_USER-nopasswd`, written for that user (trixie has no pi-nopasswd rule to inherit) |
| Host | `patternflood` / `patternflood.local` (avahi) |
| Wi-Fi | via cloud-init `network-config` (regulatory domain US) |
| Card link | NetworkManager `colorlight`: any wired interface → 192.168.75.1/24, no default route |
| I²C | `i2c_arm` on at 100 kHz, `i2c-dev` loaded; Bluetooth off |
| Serial console | `enable_uart=1`: GPIO14 TXD (pin 8), GPIO15 RXD (pin 10), 115200 (on the Pi 5, `dtparam=uart0_console` moves it there from the debug connector). With a Glasgow on port B: `glasgow run uart -V 3.3 --rx B0 --tx B1 -b 115200 tty` |
| Login | `update-motd.d/05-patternflood`: wordmark, plus renderer, card link and power (under-voltage) status |
| First boot | cloud-init installs `python3-numpy`, `i2c-tools`, `python3-pil` and `g++`, then switches itself off for later boots (`/etc/cloud/cloud-init.disabled`; delete it to have `user-data` or `network-config` applied again) |
| Code | `/opt/patternflood/demos` (`run.py`, `pfd/`, the upstream presets' build files and source tree) and `/opt/patternflood/colorlight` (`knob_renderer`, `r75_frame`, `seesaw`), as in the repo |
| Service | `patternflood.service` runs `demos/run.py --knobs i2c:1 --out udp:192.168.75.39 --fps 60 --audio none` as user `patternflood` (group i2c), CPU governor `performance`, restarts forever. On its first start after g++ lands it compiles upstream's presets (a few minutes on a Zero W, behind splash step 5) |
| Settings | `/etc/default/patternflood`: which demos (`PF_ONLY`), start demo, fps, brightness, knob and frame specs. Edit it, then `sudo systemctl restart patternflood` |
| Speed on the Zero W | SeungHun's presets (`PF_ONLY=upstream`) run at about 12 fps with the knobs polled; our numpy demos at 2–7. Sending (69 UDP packets a frame through the USB adapter) and the knob thread are the fixed costs. The Pi 5 is the real fix |
| Boot splash | `pf-splash` moves the card's progress bar on (below); needs `arm-linux-gnueabihf-gcc` (Zero W) or `aarch64-linux-gnu-gcc` (Pi 5) on the provisioning host |

To update the demos and the renderer on a running Pi (keeps its `/etc/default/patternflood`):

```sh
./update_pi.py                                                    # patternflood.local
./update_pi.py USER@ADDRESS -o HostKeyAlias=patternflood.local    # when mDNS fails
```

## Boot splash

The card draws a spinner and a five-step bar from power-on, until the renderer
takes the display (receiver75's `bios/splash.c`; see
[`../colorlight/README.md`](../colorlight/README.md#boot-splash)). The Pi moves the
bar on with `pf-splash STEP`:

| Step | Lit by | When |
|---|---|---|
| 1 | the card's BIOS | power-on, about 2 s |
| 2 | initramfs (`init-premount/patternflood-splash`, in the background) | kernel up |
| 3 | `patternflood-splash-early.service` (sysinit, after `udevadm settle`) | systemd up |
| 4 | `patternflood-splash-network.service` | NetworkManager up; on first boot it sits here through cloud-init's package install |
| 5 | `patternflood.service`'s `ExecStartPre` (in the background) | renderer starting; it doesn't wait for the network, so this usually beats step 4, which is then ignored |

**Boot time** (Pi 5, 2026-10-28; frames reach the panels about 7.9 s after the kernel starts, from
16.2): the bootloader takes about 8.8 s before that ("Starting OS" in `sudo vclog --msg`). What
bought the rest: the renderer doesn't wait for `network.target`; cloud-init runs on the first boot
only; the knobs are found on their polling thread, reset together (one 0.5 s wait, not four); node's
sandbox is probed during the community build; and the initramfs leaves the NIC up (no `--restore`),
so NetworkManager finds the link already negotiated instead of spending another 3 s on it. The
link (NetworkManager's activation of `colorlight`) is now what the first frame waits for.

When `patternflood.service` stops or restarts, its `ExecStopPost` runs `pf-splash --show 5`, which puts the spinner back.

`pf-splash` (in `pf-splash/`) is freestanding C: raw syscalls, no libc, under 4 KB, ARMv6 (`make`) or AArch64 (`make pf-splash-arm64`).
It writes the card's CSRs with the same 8-byte UDP packets as `r75_frame.poke()`, built
by hand and sent as raw Ethernet frames to `10:e2:d5:00:00:00`. That way it needs no IP
address or ARP, only link, so it works before NetworkManager. It finds the NIC with
ioctls, not `/sys`, because the initramfs copy outlives the switch to the real root.
`make host` builds an x86-64 copy for testing.

The initramfs hook is picked up by cloud-init's `update-initramfs -u` on first
boot, so step 2 first shows on the second boot. Steps out of order (2 arriving
after 3) are ignored: the bar only moves forward.

On the Zero W, the USB gigabit adapter needs a micro-B-to-A OTG **cable**, not a plug-style
dongle, and goes in with the Pi off
([`pi-zero-w-controller.md`](../../docs/desktop/design-notes/pi-zero-w-controller.md)).

**Power switch.** Cutting the power is safe once the box is running: it writes about 1 KB/s (the
journal is in RAM, and there are no unattended upgrades), and ext4 replays its journal on the next
boot. Twice crashed with sysrq-b (2026-10-28): clean filesystem, renderer back in 15 s. The one risky
moment was the half-minute after a compile, when a library could be named but still empty, so the
libraries are now fsynced before they get their names, an empty preset library is rebuilt, and
`update_pi.py` syncs before it returns. Don't cut the power during an `apt upgrade` (it writes the
FAT boot partition).

**Watchdogs.** Raspberry Pi OS already runs the hardware watchdog (systemd `RuntimeWatchdogSec=1min`),
so the kernel or systemd hanging reboots the box. `patternflood.service` is `Type=notify` with
`WatchdogSec=20`: the frame loop checks in about once a second, and a renderer that hangs is
killed and restarted (tested 2026-10-28 by SIGSTOPping it: back in 21 s).

Not done yet: a read-only root filesystem (overlayfs) before the box is closed.
