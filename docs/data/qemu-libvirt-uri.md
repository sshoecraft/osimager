# QEMU — libvirt connection URI (`libvirt_uri`)

The qemu platform's `post_build` hook (`scripts/qemu_post_build.py`) registers the
finished VM into libvirt with `virsh define`. `libvirt_uri` selects **which**
libvirt instance: local `qemu:///session` (per-user) vs `qemu:///system`
(host-wide), or a remote `qemu+ssh://host/system`. It is the libvirt analog of
Proxmox's `proxmox_url` / vSphere's `vcenter_server`.

## Setting it
- Platform default: `platforms/qemu.json` → `defs.libvirt_uri` (ships empty = auto).
- Per location/spec: a `defs` block in the location or spec JSON.
- Per run: `mkosimage -D libvirt_uri=qemu:///system …`.

## Resolution precedence (in the hook)
1. `libvirt_uri` from defs (`-D` > spec > location > qemu.json)
2. `LIBVIRT_DEFAULT_URI` env var (fallback when unconfigured)
3. uid default: root → `qemu:///system`, else `qemu:///session`

Empty everywhere collapses to "env, else root?system:session" — an unprivileged
build lands under `qemu:///session`, a root / `libvirt`-group build under
`qemu:///system`, unless you pin it. The hook passes the resolved URI to both
`virsh --connect … undefine` and `… define`, and echoes it:
`libvirt: VM '<name>' defined (qemu:///system)`.

## Notes
- It lives in a plain `defs` block (NOT `platform_defs`) on purpose, so
  location/spec/`-D` can override it. `platform_defs` would make it un-overridable.
- `qemu:///system` does **not** require root — membership in the `libvirt` group is
  enough (no sudo).
- Under `qemu:///system`, libvirt-qemu/root must be able to read the qcow2 under
  `vms_path`; may need a group/ACL or AppArmor allowance.
- A remote `qemu+ssh://` URI defines a domain whose XML references a **local** disk
  path, so that path must exist on the remote host. Local session/system is the
  fully-supported case.
