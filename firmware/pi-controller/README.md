# Pi Zero W controller appliance

Raspberry Pi OS Lite (trixie, armhf), set up to boot straight into the knob
renderer: knobs on I²C, frames over a USB gigabit adapter to receiver75 on
the Colorlight card. Wiring: [`docs/desktop/wiring-pi-controller.md`](../../docs/desktop/wiring-pi-controller.md).

## Making a card

1. Write the image and verify it. One write on the bench reader had a 12 KiB
   bad stretch, so always compare after writing:
   ```sh
   xz -dk 2026-10-06-raspios-trixie-armhf-lite.img.xz
   sudo dd if=…img of=/dev/sdX bs=4M conv=fsync
   sudo cmp -n $(stat -c %s …img) …img /dev/sdX
   ```
2. Mount both partitions and run, as root:
   ```sh
   sudo ./provision_card.py --boot BOOT --root ROOT --userconf userconf.txt \
       --wifi-ssid YOUR_SSID --wifi-pass-file wifi.pass --ssh-key ~/.ssh/id_ed25519.pub
   ```
   `userconf.txt` holds `jof:<openssl passwd -6 hash>`; `wifi.pass` holds the
   passphrase. Neither belongs in the repo.

## What it sets up

| | |
|---|---|
| User | `pi` renamed to `jof` by `userconf.txt` (password in `a password file` on ash); SSH key only; passwordless sudo from `/etc/sudoers.d/010_jof-nopasswd` (trixie has no pi-nopasswd rule to inherit) |
| Host | `patternflood` / `patternflood.local` (avahi) |
| Wi-Fi | via cloud-init `network-config` (regulatory domain US) |
| Card link | NetworkManager `colorlight`: any wired interface → 192.168.75.1/24, no default route |
| I²C | `i2c_arm` on at 100 kHz, `i2c-dev` loaded; Bluetooth off |
| Serial console | `enable_uart=1`: GPIO14 TXD (pin 8), GPIO15 RXD (pin 10), 115200. With a Glasgow on port B: `glasgow run uart -V 3.3 --rx B0 --tx B1 -b 115200 tty` |
| Login | `update-motd.d/05-patternflood`: wordmark, plus renderer, card link and power (under-voltage) status |
| First boot | cloud-init installs `python3-numpy` and `i2c-tools` |
| Service | `patternflood.service` runs `/opt/patternflood/knob_renderer.py --knobs i2c --res 64 --fps 30` as user `patternflood` (group i2c), CPU governor `performance`, restarts forever |
| Boot splash | `pf-splash` moves the card's progress bar on (below); needs `arm-linux-gnueabihf-gcc` on the provisioning host |

To update the renderer on a running Pi:

```sh
scp ../colorlight/{knob_renderer,r75_frame,seesaw}.py jof@patternflood.local:/tmp/
ssh jof@patternflood.local 'sudo install -m 644 /tmp/{r75_frame,seesaw}.py /opt/patternflood/ \
    && sudo install -m 755 /tmp/knob_renderer.py /opt/patternflood/ && sudo systemctl restart patternflood'
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
| 5 | `patternflood.service`'s `ExecStartPre` | renderer starting (numpy import) |

When `patternflood.service` stops or restarts, its `ExecStopPost` runs `pf-splash --show 5`, which puts the spinner back.

`pf-splash` (in `pf-splash/`) is freestanding C: raw syscalls, no libc, 3.6 KB, ARMv6.
It writes the card's CSRs with the same 8-byte UDP packets as `r75_frame.poke()`, built
by hand and sent as raw Ethernet frames to `10:e2:d5:00:00:00`. That way it needs no IP
address or ARP, only link, so it works before NetworkManager. It finds the NIC with
ioctls, not `/sys`, because the initramfs copy outlives the switch to the real root.
`make host` builds an x86-64 copy for testing.

The initramfs hook is picked up by cloud-init's `update-initramfs -u` on first
boot, so step 2 first shows on the second boot. Steps out of order (2 arriving
after 3) are ignored: the bar only moves forward.

**Blocked, 2026-10-22: the USB gigabit adapter doesn't work on the Zero's bare port.**
That leaves the Pi with no link to the card, so steps 2–5 and the renderer can't
reach it. See [`wiring-pi-controller.md` §5](../../docs/desktop/wiring-pi-controller.md);
the fix to try is §2.1, powering the adapter from the PSU.

Not done yet: a read-only root filesystem (overlayfs) before the box is closed.
