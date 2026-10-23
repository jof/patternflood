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
| User | `pi` renamed to `jof` by `userconf.txt` (password in `a password file` on ash); SSH key only; passwordless sudo |
| Host | `patternflow` / `patternflow.local` (avahi) |
| Wi-Fi | via cloud-init `network-config` (regulatory domain US) |
| Card link | NetworkManager `colorlight`: any wired interface → 192.168.75.1/24, no default route |
| I²C | `i2c_arm` on at 100 kHz, `i2c-dev` loaded; Bluetooth off |
| First boot | cloud-init installs `python3-numpy` and `i2c-tools` |
| Service | `patternflow.service` runs `/opt/patternflow/knob_renderer.py --knobs i2c --res 64 --fps 30` as user `patternflow` (group i2c), CPU governor `performance`, restarts forever |

To update the renderer on a running Pi:

```sh
scp ../colorlight/{knob_renderer,r75_frame,seesaw}.py jof@patternflow.local:/tmp/
ssh jof@patternflow.local 'sudo install -m 644 /tmp/{r75_frame,seesaw}.py /opt/patternflow/ \
    && sudo install -m 755 /tmp/knob_renderer.py /opt/patternflow/ && sudo systemctl restart patternflow'
```

Not done yet: a read-only root filesystem (overlayfs) before the box is closed.
