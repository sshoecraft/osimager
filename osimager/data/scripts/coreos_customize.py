"""
Pre-build hook for Ignition-based distros (Fedora CoreOS, Flatcar).

CoreOS-style images do not accept an answer file on a CD; the Ignition config must
be embedded into the live ISO before boot. This runs `coreos-installer iso customize`
to bake the generated Ignition config (config.ign, produced from the spec's files[]
into temp_dir) into the installer ISO, then repoints iso_url at the customized image.

Runs as a spec-level pre_build hook (engine >= 1.8.0), before the Packer build JSON is
written, so updating osimager.defs['iso_url'] takes effect for the build.
"""

import os
import shutil
import subprocess
import urllib.request


def run(osimager):
    if not shutil.which('coreos-installer'):
        print("coreos-installer not found in PATH; cannot embed Ignition config")
        print("  install: https://coreos.github.io/coreos-installer/")
        raise SystemExit(1)

    temp_dir = osimager.defs.get('temp_dir', '/tmp')
    ign = os.path.join(temp_dir, 'config.ign')
    if not os.path.isfile(ign):
        raise SystemExit(f"Ignition config not found: {ign}")

    iso_url = osimager.defs.get('iso_url', '')
    if iso_url.startswith('file://'):
        src_iso = iso_url[len('file://'):]
    elif iso_url.startswith('/'):
        src_iso = iso_url
    else:
        # Remote ISO: fetch it locally before customizing.
        src_iso = os.path.join(temp_dir, 'source.iso')
        if osimager.verbose:
            print(f"downloading {iso_url} -> {src_iso}")
        urllib.request.urlretrieve(iso_url, src_iso)

    out_iso = os.path.join(temp_dir, 'customized.iso')
    if os.path.exists(out_iso):
        os.remove(out_iso)

    cmd = [
        'coreos-installer', 'iso', 'customize',
        '--dest-ignition', ign,
        '--dest-device', '/dev/sda',
        '-o', out_iso,
        src_iso,
    ]
    if osimager.verbose:
        print('running: ' + ' '.join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"coreos-installer failed: {result.stderr.strip()}")

    osimager.defs['iso_url'] = 'file://' + out_iso
    print(f"Ignition config baked into {out_iso}")
