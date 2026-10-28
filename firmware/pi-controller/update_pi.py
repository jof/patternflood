#!/usr/bin/env python3
"""Update a running controller's renderer and demos from this checkout, then restart it.

    ./update_pi.py                          # jof@patternflood.local
    ./update_pi.py jof@ADDRESS -o HostKeyAlias=patternflood.local

Installs what provision_card.py puts in /opt/patternflood (the demo suite, the
renderer, the upstream presets' source tree and the community's patterns as
this checkout last synced them), plus patternflood.service. An existing
/etc/default/patternflood is kept: it holds the box's own settings. The Pi
compiles new or changed community patterns before the restart, and the presets
again on the restart if any of their sources changed.
"""
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from provision_card import HERE, install_payload

UNIT = "etc/systemd/system/patternflood.service"
DEFAULTS = "etc/default/patternflood"


def main():
    host, ssh_opts = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("jof@patternflood.local", [])
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
            f"sudo rm -rf {o}/demos/upstream_host/build/tree {o}/demos/upstream_host/build/community/src; "
            "sudo cp -a $t/. /; sudo rm -rf $t; "
            # The community's patterns compile here, where you can watch, rather than behind the splash
            # on the restart. Only what's new or changed: the libraries are kept, keyed by their sources.
            f"sudo chown -R patternflood:patternflood {o}/demos/upstream_host/build; "
            f"if [ -e {o}/demos/upstream_host/build/community/src/index.json ]; then "
            f"sudo -u patternflood python3 {o}/demos/upstream_host/community.py build; fi; "
            "sudo systemctl daemon-reload; sudo systemctl restart patternflood; echo restarted"
        )
        with open(tgz, "rb") as f:
            subprocess.run(["ssh", *ssh_opts, host, remote], stdin=f, check=True)


if __name__ == "__main__":
    main()
