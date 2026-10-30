#!/usr/bin/env python3
"""Update a running controller's renderer and demos from this checkout, then restart it.

    ./update_pi.py                          # patternflood.local, as your local user name
    ./update_pi.py USER@ADDRESS -o HostKeyAlias=patternflood.local     # when mDNS fails

Installs what provision_card.py puts in /opt/patternflood (the demo suite, the
renderer, the upstream presets' source tree and the community's patterns as
this checkout last synced them), plus patternflood.service. An existing
/etc/default/patternflood is kept: it holds the box's own settings. A box from
before the push buttons gets their overlays in config.txt (read at the next
reboot) and the renderer's user joins group input. The Pi
compiles new or changed community patterns before the restart, and the presets
again on the restart if any of their sources changed.
"""
import shlex
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from provision_card import HERE, install_payload

UNIT = "etc/systemd/system/patternflood.service"
DEFAULTS = "etc/default/patternflood"


def button_lines():
    """config-append.txt's push-button block: its comment and the gpio-key overlays."""
    lines = (HERE / "boot/config-append.txt").read_text().splitlines()
    start = next(i for i, s in enumerate(lines) if s.startswith("# Push buttons"))
    end = max(i for i, s in enumerate(lines) if s.startswith("dtoverlay=gpio-key"))
    return ["[all]"] + lines[start:end + 1]


def main():
    host, ssh_opts = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("patternflood.local", [])
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "stage"
        install_payload(stage / "opt/patternflood")
        for rel in (UNIT, DEFAULTS):
            (stage / rel).parent.mkdir(parents=True, exist_ok=True)
            (stage / rel).write_bytes((HERE / "rootfs" / rel).read_bytes())
        tgz = Path(tmp) / "payload.tgz"
        with tarfile.open(tgz, "w:gz") as t:
            def root_owned(info):
                info.uid = info.gid = 0
                info.uname = info.gname = "root"
                return info
            t.add(stage, arcname=".", filter=root_owned)
        o = "/opt/patternflood"
        remote = (
            "set -e; t=$(mktemp -d); sudo tar -xzf - -C $t; "
            f"if [ -e /{DEFAULTS} ]; then sudo rm $t/{DEFAULTS}; fi; "
            # Replace the code, but keep the compiled presets (build/*.so): an unchanged tree needn't rebuild.
            f"sudo find {o} -mindepth 1 -maxdepth 1 ! -name demos -exec rm -rf {{}} +; "
            f"sudo mkdir -p {o}/demos/upstream_host; "
            f"sudo find {o}/demos -mindepth 1 -maxdepth 1 ! -name upstream_host -exec rm -rf {{}} +; "
            f"sudo find {o}/demos/upstream_host -mindepth 1 -maxdepth 1 ! -name build -exec rm -rf {{}} +; "
            f"sudo rm -rf {o}/demos/upstream_host/build/tree; "
            # The community's synced sources aren't in git: a checkout without them (a fresh worktree)
            # leaves the Pi's alone rather than emptying its shelf.
            f"if [ -e $t{o}/demos/upstream_host/build/community/src/index.json ]; then "
            f"sudo rm -rf {o}/demos/upstream_host/build/community/src; fi; "
            "sudo cp -a $t/. /; sudo rm -rf $t; "
            # The community's patterns compile here, where you can watch, rather than behind the splash
            # on the restart. Only what's new or changed: the libraries are kept, keyed by their sources.
            f"sudo chown -R patternflood:patternflood {o}/demos/upstream_host/build; "
            f"if [ -e {o}/demos/upstream_host/build/community/src/index.json ]; then "
            f"sudo -u patternflood python3 {o}/demos/upstream_host/community.py build; fi; "
            # The restart may rebuild the presets; those fsync themselves. Everything above is on the card
            # before this returns, so the power switch is safe as soon as it does.
            # Boxes provisioned before user-data switched cloud-init off after its first boot.
            "if [ -e /var/lib/cloud/instance/boot-finished ]; then sudo touch /etc/cloud/cloud-init.disabled; fi; "
            # Boxes from before the push buttons: their overlays (from the next boot), and access to them.
            "if ! grep -q '^dtoverlay=gpio-key' /boot/firmware/config.txt; then "
            f"printf '%s\\n' {' '.join(map(shlex.quote, button_lines()))} | sudo tee -a /boot/firmware/config.txt >/dev/null; "
            "echo 'buttons: added to config.txt; reboot to read them'; fi; "
            "sudo usermod -aG input patternflood; "
            "sudo systemctl daemon-reload; sudo systemctl restart patternflood; sync; echo restarted"
        )
        with open(tgz, "rb") as f:
            subprocess.run(["ssh", *ssh_opts, host, remote], stdin=f, check=True)


if __name__ == "__main__":
    main()
