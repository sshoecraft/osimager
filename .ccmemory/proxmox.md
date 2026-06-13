# Proxmox Platform Notes

## Template Issue — RESOLVED

Patched `packer-plugin-proxmox` v1.2.3 installed at `~/.config/packer/plugins/github.com/hashicorp/proxmox/`. Built from upstream + PR #283 (`mpywell:skip-convert-to-template`). The `skip_convert_to_template` option defaults to true, so no config change needed — VMs are no longer converted to templates after build. The post_build script (`scripts/proxmox_post_build.py`) is re-enabled and simplified to just rename the VM from `build_id` (packer-<uuid>) to the actual name via the Proxmox API.

## Known Issues

1. **EFI/OVMF boot entries break on kernel upgrades** — UEFI NVRAM stored in the efivars disk goes stale after major version upgrades (e.g. AlmaLinux 9.2 to 9.7). Results in "failed to load boot UEFI from PCI root" / "no bootable device found". This is why Proxmox defaults to SeaBIOS (BIOS) via `platform_defs`.

2. **Disk cache defaults to none** — On iSCSI-backed storage, default `cache=none` causes 25+ minute installs. Must set `cache_mode: writeback` in proxmox.json to get reasonable (~5 min) performance.

3. **No auto-HA enrollment** — Proxmox does not automatically add VMs to HA. Requires explicit `ha-manager add` per VM after build.

4. **Removing storage doesn't unmount it** — `pvesm remove` only removes the storage definition from the config but doesn't actually unmount the filesystem. Have to manually unmount from every node.

## Configuration Decisions

- **SeaBIOS (BIOS) is the default** — enforced via `platform_defs` in proxmox.json, which prevents specs from overriding `firmware` to `efi`
- **Boot order**: `virtio0;ide2;net0` — disk first (empty disk falls through to CD), avoids re-booting from CD after install
- **boot_iso pinned to ide2**, additional_iso to ide3
- **Disk cache**: `writeback` for iSCSI performance
- **`skip_convert_to_template`** defaults to true in patched plugin — do NOT add it to proxmox.json config
- **`os` field** set per-spec via platform_specific (linux=l26, windows=win11, freebsd/sysvr4=other)
