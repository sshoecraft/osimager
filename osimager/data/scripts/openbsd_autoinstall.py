"""
Pre-build hook for OpenBSD autoinstall.

OpenBSD's autoinstall(8) fetches its response file over HTTP rather than reading it
from a CD. This serves the generated install.conf (placed in temp_dir by the spec's
files[]) over HTTP on a fixed port so the installer can fetch it; the boot_command
selects (A)utoinstall and points it at this server.

Runs as a spec-level pre_build hook (engine >= 1.8.0). The server is spawned detached
so it survives for the duration of the Packer build; its PID is written to
temp_dir/.openbsd_httpd.pid for optional cleanup by a post_build hook.
"""

import os
import subprocess

HTTP_PORT = 8765


def run(osimager):
    temp_dir = osimager.defs.get('temp_dir', '/tmp')
    conf = os.path.join(temp_dir, 'install.conf')
    if not os.path.isfile(conf):
        raise SystemExit(f"OpenBSD response file not found: {conf}")

    # Serve temp_dir (which holds install.conf) over HTTP, detached.
    proc = subprocess.Popen(
        ['python3', '-m', 'http.server', str(HTTP_PORT), '--directory', temp_dir],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    with open(os.path.join(temp_dir, '.openbsd_httpd.pid'), 'w') as f:
        f.write(str(proc.pid))

    # Expose the URL host/port to the build so boot_command can reference it.
    osimager.defs['http_port'] = HTTP_PORT
    if osimager.verbose:
        print(f"serving OpenBSD install.conf on port {HTTP_PORT} (pid {proc.pid})")
