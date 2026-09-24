---
name: trap-firmware-in-spec-config-breaks-qemu
description: Spec `firmware` belongs in `defs` (osimager selector), never `config` — config.firmware reaches packer qemu as `-bios efi` and qemu dies in 2s.
metadata:
  type: project
---

Symptom: qemu build halts ~2s after "Starting VM" with only "Qemu failed to start". `PACKER_LOG=1` shows `-bios efi` on the qemu cmdline and `qemu: could not load PC BIOS 'efi'`.

Cause: a spec `version_specific` block set `"firmware": "efi"` under `config`. Spec `config` merges straight into the Packer builder, and packer-plugin-qemu's `firmware` is a firmware *file path*. The osimager firmware selector is the `firmware` **def**, which drives `firmware_specific` overlays; qemu.json forces `platform_defs.firmware = "bios"` (platform_defs beat spec defs), so on qemu the bios boot_command is used.

Correct shape (RHEL 8/9/10): `defs.firmware: "efi"`, EFI `boot_command` + `boot_wait: 45s` in `config`, and a `firmware_specific` `bios` entry with the BIOS boot_command + `boot_wait: 10s`. A `platform_specific` proxmox `config.firmware: ""` override is a tell that someone put firmware in config.

Fixed for RHEL 8 in v1.9.0. RHEL 7.* still had `config.firmware: efi` at that point — grep other specs for `"firmware"` inside `config` when a qemu build dies at launch.

Diagnose with `PACKER_LOG=1 bin/mkosimage ...` and grep `Qemu stderr`.
