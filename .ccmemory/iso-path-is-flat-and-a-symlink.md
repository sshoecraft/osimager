---
name: iso-path-is-flat-and-a-symlink
description: ISOs live flat in iso_path (/iso → NFS /data/media/cdimages/os/). Spec file:// URLs must be flat; /iso is a symlink; template/iso/ is Proxmox's store…
metadata:
  type: project
---

**Convention:** every ISO sits directly in `iso_path` (`/iso`), never in a vendor subdirectory. Platforms build the path as `>>iso_path<</>>iso_name<<`. Spec `file://` URLs must match: `file://>>iso_path<</<file>`. Until 1.9.1, 64 spec URLs used `<iso_path>/<Vendor>/<file>` (RedHat/, AlmaLinux/, Debian/, SUSE/, Windows/…) — `check_iso_local` and pre-flight `check_iso_url` test the literal file:// path, so those targets vanished from `--list --local --avail` and failed "ISO file not found" even with the ISO at the root. The user corrected this directly: "I thought everything just went into /iso".

**Trap — `/iso` is a symlink** to `/data/media/cdimages/os/` (NFS from 192.168.1.4, 11T, ~91% full). `ls -F /iso` and `find /iso …` without a trailing slash or `-H` report the LINK, not its contents — this produced a false "no subdirectories" claim. Use `/iso/` or `readlink -f /iso` first. `find -type f` also skips symlinks, which hid most of `template/iso/`.

**`template/iso/` is a Proxmox directory-storage ISO store — never clean it up.** The Proxmox host mounts this share at `/mnt/pve/iso` (absent on this box). Proxmox only lists ISOs under `<storage>/template/iso/`, so ~151 entries there are symlinks `-> /mnt/pve/iso/<file>` exposing each root ISO (dangling from here, valid on the PVE host). The ~11 regular files there (AlmaLinux, debian, `packer*.iso` cd_files CDs) are uploads from Proxmox / osimager proxmox builds and may be attached to PVE VMs. A killed cleanup nearly deleted them as "duplicates/leftovers".

**The share is also a vSphere datastore**: `vCLS-*` directories hold live vSphere Cluster Services VM disks, plus `.vSphere-HA`. Never move/delete anything under those. `os -> .` and `packer_cache -> .` are self-referencing symlinks — don't recurse with `-L`.

Leftover vendor subdirs (`RedHat/`, `AlmaLinux/`, `Debian/`, `Windows/`) hold non-ISO helpers (`d`, `dl`, `t`, `tl` scripts, Windows serial/license text) — leave them. Duplicate ISOs outside `template/iso/` are removed only after a byte-for-byte `cmp` against the root copy, and only with the user's go-ahead.
