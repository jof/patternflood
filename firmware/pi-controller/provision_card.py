#!/usr/bin/env python3
"""Turn a freshly written Raspberry Pi OS Lite (trixie) card into the patternflood controller.

Run as root against the card's mounted partitions:

    sudo ./provision_card.py --boot /mnt/boot --root /mnt/root \\
        --userconf userconf.txt --wifi-ssid YOUR_SSID --wifi-pass-file wifi.pass \\
        --ssh-key ~/.ssh/id_ed25519.pub

The image picks the board: armhf for the Pi Zero W, arm64 for the Pi 5.

Secrets (the userconf.txt password hash, the Wi-Fi passphrase) come from files
and are never part of the repo. Safe to re-run: config.txt is only appended once.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RENDERER = HERE.parent / "colorlight"
RENDERER_FILES = ["knob_renderer.py", "r75_frame.py", "seesaw.py"]
DEMOS = HERE.parent / "demos"
# The demo suite, as laid out in the repo (run.py finds ../colorlight). upstream_host
# carries only what builds the presets; the preset tree itself is written by build.py.
DEMO_FILES = ["run.py", "pfd", "upstream_host/build.py", "upstream_host/shim", "upstream_host/web_ports",
              "upstream_host/community.py", "upstream_host/community_shim", "upstream_host/jsrun.mjs",
              "upstream_host/community_ports", "upstream_host/community_review.json", "upstream_host/originals"]
# The community's patterns, as `community.py sync` and `check` left them in this checkout.
COMMUNITY = DEMOS / "upstream_host/build/community/src"
MARKER = "# --- patternflood controller ---"
FIRST_UID = 1000                        # the image's "pi" user, renamed by userconf.txt
# unit -> the target that pulls it in
UNITS = {
    "patternflood.service": "multi-user.target",
    "patternflood-splash-early.service": "sysinit.target",
    "patternflood-splash-network.service": "multi-user.target",
}


def install(src, dst, mode, uid=0, gid=0, quiet=False):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    shutil.copystat(src, dst)           # keep mtimes: the Pi rebuilds the presets only if their sources changed
    if os.geteuid() == 0:               # update_pi.py stages as a user; tar makes it root-owned
        os.chown(dst, uid, gid)
    os.chmod(dst, mode)
    if not quiet:
        print(f"  {dst}  {oct(mode)}")


def install_payload(opt):
    """The renderer and the demo suite into OPT (/opt/patternflood on the card)."""
    for name in RENDERER_FILES:
        install(RENDERER / name, opt / "colorlight" / name, 0o644)
    n = 0
    for entry in DEMO_FILES:
        src = DEMOS / entry
        for f in sorted(src.rglob("*")) if src.is_dir() else [src]:
            if f.is_file() and "__pycache__" not in f.parts:
                install(f, opt / "demos" / f.relative_to(DEMOS),
                        0o755 if f.name in ("run.py", "build.py", "community.py") else 0o644, quiet=True)
                n += 1
    print(f"  {opt / 'demos'}  ({n} files)")
    # The presets' self-contained source tree (from the upstream clone); the Pi compiles it with g++.
    tree = opt / "demos/upstream_host/build/tree"
    subprocess.run([sys.executable, str(DEMOS / "upstream_host/build.py"), "--tree-only", "--out", str(tree)],
                   check=True)
    # The community's patterns: their headers, upstream's cores and ash's check. The Pi compiles them too.
    if (COMMUNITY / "index.json").exists():
        n = 0
        for f in sorted(COMMUNITY.rglob("*")):
            if f.is_file():
                install(f, opt / "demos/upstream_host/build/community/src" / f.relative_to(COMMUNITY), 0o644, quiet=True)
                n += 1
        print(f"  {opt / 'demos/upstream_host/build/community/src'}  ({n} files)")
    else:
        print("  no community patterns: run firmware/demos/upstream_host/community.py sync (and check) first")


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
    # The boot splash sender, cross-built for the image: ARMv6 for the Zero W (needs
    # arm-linux-gnueabihf-gcc), AArch64 for the Pi 5 (needs aarch64-linux-gnu-gcc).
    arm64 = (root / "usr/lib/aarch64-linux-gnu").is_dir()
    splash = "pf-splash-arm64" if arm64 else "pf-splash"
    print(f"image: {'arm64' if arm64 else 'armhf'}")
    subprocess.run(["make", "-C", str(HERE / "pf-splash"), splash], check=True)

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
    install_payload(root / "opt/patternflood")
    install(HERE / "pf-splash" / splash, root / "usr/local/sbin/pf-splash", 0o755)
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
