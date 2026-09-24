---
name: qemu-libvirt-uri-knob
description: qemu libvirt_uri knob (osimager-data v1.8.0): hook picks virsh --connect via defs -> LIBVIRT_DEFAULT_URI -> root?system:session; set it per-location…
metadata:
  type: project
tags: [qemu, libvirt, post_build, osimager-data, virsh, locations, platform_specific]
---

# qemu libvirt_uri knob (osimager-data v1.8.0)

## What
The qemu `post_build` hook (`osimager_data/scripts/qemu_post_build.py`) registers the
built VM into libvirt with `virsh define`. It used to call virsh **bare** (no
`--connect`) → unprivileged builds silently landed under `qemu:///session`. Now the
target is `libvirt_uri`, the libvirt analog of vSphere `vcenter_server` / Proxmox
`proxmox_url`.

## Resolution precedence (in the hook)
1. `osimager.defs['libvirt_uri']` — `-D libvirt_uri=` > spec `defs` > location `defs` >
   qemu.json `defs` (existing merge order; location loads AFTER platform, so it overrides
   the qemu.json default)
2. `LIBVIRT_DEFAULT_URI` env var (fallback when unconfigured)
3. `qemu:///system` if `os.geteuid()==0` else `qemu:///session`

`platforms/qemu.json` ships `defs: {"libvirt_uri": ""}` as the declared auto-default.
Hook echoes it: `libvirt: VM '<name>' defined (<uri>)`.

## WHERE to set it — per-location in platform_specific (NOT config.json)
Connection targets live in the **location file**, keyed by platform — same as every
other platform:
- `~/.config/osimager/locations/esx.json` → `platform_specific[vsphere].defs.esxi_host`
- `~/.config/osimager/locations/pve*.json` → `defs.proxmox_node`
- **libvirt_uri** → `lab.json` → `platform_specific[qemu].defs.libvirt_uri = "qemu:///system"`
  (a `defs` sub-block, NOT `config`, because libvirt_uri is read by the post-build hook,
  not the Packer qemu builder — that's why it isn't a Packer field like `net_bridge`).

**config.json is the WRONG layer** (dead end explored this session): `load_settings`
(core.py:263) only accepts keys already in `self.settings` — `--set`/config.json silently
drop unknown keys. config.json holds only build knobs (cpu/mem/paths/creds). AND settings
merge into defs at core.py:234 BEFORE the platform loads (1205), so the qemu.json empty
default would clobber a config.json value anyway. Use the location file.

## Verify without building
`mkosimage --defs qemu/lab/<spec> <name>` (`-x`) dumps resolved `self.defs` and exits
before packer (cli.py:308) → confirm `"libvirt_uri": "qemu:///system"`. `--dump` (`-u`)
dumps the Packer build config; libvirt_uri correctly does NOT appear there.

## Key mechanics
- `bin/mkosimage` is only a dev shim; real command = entry point `osimager.cli:main_mkosimage`.
- The virsh define lives in the osimager-data hook, not the engine.
- `qemu:///system` does NOT need root — steve is in the `libvirt` group (115).

## Packaging / environment
- engine `osimager` = editable install (`pip install -e`); data `osimager-data` = plain COPY.
- Reinstall data via `cd /src/osimager-data && pip3 install .` (defaults to `--user`). NOT `-e`.
- `/src` is NFS `all_squash` (anonuid=root) → files show `root:root` but steve can write; no sudo.
