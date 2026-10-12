---
name: compiled-osimager-mirror-iso-and-proxmox-platform-traps
description: Assorted osimager traps: AlmaLinux slow mirrorlist, FreeBSD old-release 404s and NIC naming, Proxmox forced SeaBIOS and platform quirks.
metadata:
  type: project
tags: [compiled, almalinux, freebsd, proxmox, trap, platform_defs]
---

Assorted group (loosely clustered): per-OS and per-platform build traps in osimager that each made a build stall, 404, or fail to boot.

## AlmaLinux: mirrorlist picks slow mirrors
- `trap-almalinux-mirrorlist-picks-slow-mirrors`: the default `mirrorlist=` sent a lab VM to a mirror at about 43 KB/s; `repo.almalinux.org` ran at about 25 MB/s on the same host. Builds running dnf looked hung.
- Fix is in `osimager/data/tasks/AlmaLinux_post.yml`: comments out `mirrorlist=` and sets `baseurl` to repo.almalinux.org for every repo, including debug and source variants. `config.yml` loads it via the `ansible_distribution` per-distro include.
- If an Alma build stalls in a dnf step, check the repo config before blaming the network. (Provenance: 2026-03-11 session.)

## FreeBSD: old releases and NIC names
- `trap-freebsd-old-releases-leave-download-server`: download.freebsd.org drops superseded releases. In March 2026, 14.2 already returned 404 while 14.3, 14.4 and 15.0 were present. Older versions move to the FreeBSD archive mirror. A spec URL that worked last month can 404 this way, like Alma's move to vault (see `trap-alma-point-release-moves-to-vault`). Older versions become local-only or point at the archive.
- NIC names come from the driver (vtnet0 / em0 / vmx0 by platform); there is no equivalent of Linux `net.ifnames=0`. `ifconfig_DEFAULT=DHCP` works on every driver. A static IP needs the installerconfig to find the first non-loopback interface first.
- The `bsd_arch` def maps x86_64 to amd64 for the URL. (Provenance: 2026-03-10 FreeBSD spec session.)

## Proxmox: forced SeaBIOS and platform quirks
- `proxmox-forces-seabios-and-platform-quirks`: EFI/OVMF guests on Proxmox lose their boot entry after a major in-guest upgrade (seen AlmaLinux 9.2 to 9.7). The UEFI NVRAM in the efivars disk goes stale; the VM fails with "failed to load boot UEFI from PCI root" / "no bootable device found".
- So `proxmox.json` (and `qemu.json`) set `platform_defs: { "firmware": "bios" }`. `platform_defs` are defs a spec cannot override; they are filtered during `load_data`, not applied at the end, so `firmware_specific` in a spec still fires against the forced value. Do not "fix" a spec's `firmware: efi` with a platform_specific override: firmware is the OS's decision and the platform translates it.
- No automatic HA enrollment: a built VM is not in HA until `ha-manager add` is run.
- `pvesm remove` does not unmount: it drops the storage definition only; the filesystem stays mounted on every node until unmounted by hand.
- Boot order is `order=virtio0;ide2;net0` (disk first). An empty disk falls through to the CD on first boot; after install the VM boots from disk and never re-enters the installer. Ejecting the CD from Ansible does not work, because the reboot back onto the CD happens before Ansible runs.
- `os` (l26 / win11 / other) is set per spec through `platform_specific`, not in the platform file. (Provenance: March 2026 Proxmox sessions.)
