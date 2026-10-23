#!/usr/bin/env python3
"""Turn a freshly written Raspberry Pi OS Lite (trixie, armhf) card into the patternflood controller.

Run as root against the card's mounted partitions:

    sudo ./provision_card.py --boot /mnt/boot --root /mnt/root \\
        --userconf userconf.txt --wifi-ssid YOUR_SSID --wifi-pass-file wifi.pass \\
        --ssh-key ~/.ssh/id_ed25519.pub

Secrets (the userconf.txt password hash, the Wi-Fi passphrase) come from files
and are never part of the repo. Safe to re-run: config.txt is only appended once.
"""
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
RENDERER = HERE.parent / "colorlight"
RENDERER_FILES = ["knob_renderer.py", "r75_frame.py", "seesaw.py"]
MARKER = "# --- patternflood controller ---"
FIRST_UID = 1000                        # the image's "pi" user, renamed by userconf.txt
# unit -> the target that pulls it in
UNITS = {
    "patternflood.service": "multi-user.target",
    "patternflood-splash-early.service": "sysinit.target",
    "patternflood-splash-network.service": "multi-user.target",
}


def install(src, dst, mode, uid=0, gid=0):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    os.chown(dst, uid, gid)
    os.chmod(dst, mode)
    print(f"  {dst}  {oct(mode)}")


def write(dst, text, mode, uid=0, gid=0):
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text)
    os.chown(dst, uid, gid)
    os.chmod(dst, mode)
    print(f"  {dst}  {oct(mode)}")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--boot", type=Path, required=True)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--userconf", type=Path, required=True, help="user:sha512-hash, as for userconf.txt")
    p.add_argument("--wifi-ssid", required=True)
    p.add_argument("--wifi-pass-file", type=Path, required=True)
    p.add_argument("--wifi-country", default="US")
    p.add_argument("--ssh-key", type=Path, required=True)
    args = p.parse_args()
    boot, root = args.boot, args.root
    assert (boot / "cmdline.txt").exists() and (root / "etc/os-release").exists(), "not a Pi OS card"
    assert os.geteuid() == 0, "run as root (files are written root-owned)"
    # The boot splash sender, cross-built for the Zero's ARMv6 (needs arm-linux-gnueabihf-gcc).
    subprocess.run(["make", "-C", str(HERE / "pf-splash")], check=True)

    print("boot partition:")
    install(args.userconf, boot / "userconf.txt", 0o600)
    write(boot / "ssh", "", 0o644)
    install(HERE / "boot/user-data", boot / "user-data", 0o644)
    wifi_pass = args.wifi_pass_file.read_text().strip()
    # network-config is YAML; JSON strings are valid YAML scalars and quote safely.
    write(boot / "network-config",
          "network:\n"
          "  version: 2\n"
          "  wifis:\n"
          "    wlan0:\n"
          "      dhcp4: true\n"
          "      optional: false\n"
          f"      regulatory-domain: {args.wifi_country}\n"
          "      access-points:\n"
          f"        {json.dumps(args.wifi_ssid)}:\n"
          f"          password: {json.dumps(wifi_pass)}\n", 0o600)
    config = (boot / "config.txt").read_text()
    if MARKER not in config:
        (boot / "config.txt").write_text(config.rstrip("\n") + "\n" + (HERE / "boot/config-append.txt").read_text())
        print(f"  {boot / 'config.txt'}  (appended)")

    print("rootfs:")
    for src in sorted((HERE / "rootfs").rglob("*")):
        if src.is_file():
            rel = src.relative_to(HERE / "rootfs")
            if "system-connections" in rel.parts:
                mode = 0o600
            elif "sudoers.d" in rel.parts:
                mode = 0o440
            elif "initramfs-tools" in rel.parts or "update-motd.d" in rel.parts:
                mode = 0o755
            else:
                mode = 0o644
            install(src, root / rel, mode)
    for name in RENDERER_FILES:
        install(RENDERER / name, root / "opt/patternflood" / name, 0o755 if name == "knob_renderer.py" else 0o644)
    install(HERE / "pf-splash/pf-splash", root / "usr/local/sbin/pf-splash", 0o755)
    for unit, target in UNITS.items():
        wants = root / f"etc/systemd/system/{target}.wants" / unit
        wants.parent.mkdir(parents=True, exist_ok=True)
        if not wants.is_symlink():
            wants.symlink_to(f"/etc/systemd/system/{unit}")
            print(f"  {wants} -> /etc/systemd/system/{unit}")

    home = root / "home/pi"                 # usermod -m moves it to /home/jof at first boot
    ssh_dir = home / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    os.chown(ssh_dir, FIRST_UID, FIRST_UID)
    install(args.ssh_key, ssh_dir / "authorized_keys", 0o600, FIRST_UID, FIRST_UID)
    print("done")


if __name__ == "__main__":
    main()
