---
name: iso-path-is-flat-and-a-symlink
description: ISOs live flat in iso_path (/iso → NFS /data/media/cdimages/os/). Spec file:// URLs must be flat; ls -F / find on /iso don't follow the symlink.
metadata:
  type: project
---

**Convention:** every ISO sits directly in `iso_path` (`/iso`), never in a vendor subdirectory. Platforms build the path as `>>iso_path<</>>iso_name<<`. Spec `file://` URLs must match: `file://>>iso_path<</<file>`. Until 1.9.1, 64 spec URLs used `<iso_path>/<Vendor>/<file>` (RedHat/, AlmaLinux/, Debian/, SUSE/, Windows/…) — `check_iso_local` and pre-flight `check_iso_url` test the literal file:// path, so those targets vanished from `--list --local --avail` and failed "ISO file not found" even with the ISO at the root. The user corrected this directly: "I thought everything just went into /iso".

**Trap — `/iso` is a symlink** to `/data/media/cdimages/os/` (NFS from 192.168.1.4, 11T, ~91% full). `ls -F /iso` and `find /iso …` without a trailing slash or `-H` report the LINK, not its contents — this produced a false "no subdirectories" claim. Use `/iso/` or `readlink -f /iso` first.

**The share is also a vSphere datastore**: `vCLS-*` directories hold live vSphere Cluster Services VM disks, plus `.vSphere-HA`. Never move/delete anything under those. `os -> .` and `packer_cache -> .` are self-referencing symlinks — don't recurse with `-L`.

Leftover vendor subdirs hold non-ISO helpers (`d`, `dl`, `t`, `tl` scripts, Windows serial/license text) — not ISOs; leave them. Old duplicate ISOs in subdirs were byte-verified with `cmp` against the root copy before deletion (user-authorized).
