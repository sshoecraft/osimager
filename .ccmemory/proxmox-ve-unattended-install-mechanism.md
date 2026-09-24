---
name: proxmox-ve-unattended-install-mechanism
description: Proxmox VE 8.2+ unattended install in osimager: pure boot_command (no ISO repack/no tool), edit-default-GRUB + debug-shell fetch, version-scoped, ans…
metadata:
  type: project
---

# Proxmox VE unattended install (osimager)

Proven end-to-end on stock `proxmox-ve_9.1-1.iso` in qemu/KVM: full unattended install → reboot into installed PVE (`pvetest login:`, web UI :8006). **No ISO repack, no `proxmox-auto-install-assistant`, no engine dependency.**

## Why the old spec never worked
- Proxmox has NO answer-file auto-install on a stock ISO the way kickstart/preseed do. The old `boot_command` (`<esc> auto proxmox-start-auto-install<enter>`) was fiction — typed into a GRUB that has no such entry/prompt. Nothing read `answer.toml`.
- Auto-install is **PVE 8.2+ only**. Versions 3.4–7.4 predate it entirely.
- The old `answer.toml` was invalid for 9.x (see schema below).

## The mechanism (all verified live via qemu monitor sendkey/screendump)
1. The stock ISO's `grub.cfg` ALREADY contains an `Install Proxmox VE (Automated)` menuentry with kernel arg `proxmox-start-auto-installer`. On a stock ISO it's under **Advanced Options** (gated `if [ ! -f auto-installer-mode.toml ]`); a prepared ISO just drops that toml so it floats to a top-level auto-selected entry. We don't need the prepared ISO — we reach the same boot ourselves.
2. `boot_command` edits the **always-first default `Graphical` entry** (`e`, `<down><down><down><end>`, append ` proxmox-start-auto-installer`, `<leftCtrlOn>x<leftCtrlOff>`). Editing the default is **comport-independent** — the conditional "Serial Console" menu entry shifts Advanced Options' position, so menu-nav `down×N` is fragile; the default entry is always first.
3. Stock ISO has no `auto-installer-mode.toml` → installer prints "Automatic installation selected but no config for fetching the answer file found!" and **drops to a root debug shell** (`root@proxmox:/#`). This is Proxmox's own documented manual path.
4. In the shell: `proxmox-fetch-answer partition <LABEL> >/run/automatic-installer-answers` (LABEL arg is REQUIRED — bare `partition` errors "partition label expected"). It finds `/dev/disk/by-label/<LABEL>`, mounts, reads `answer.toml`.
5. `exit` → init pipes the answer to `proxmox-auto-installer` (which reads answer on STDIN) → unattended install → reboot.

The answer.toml still rides on the `proxmox-ais`-labelled CD osimager already builds (`cd_files`/`cd_label`). `>>cd_label<<` substitutes into the boot_command fetch line.

## answer.toml 9.x schema (was broken)
Kebab-case: `root-password`, `disk-list` (NOT `root_password`/`disk_list`). `country` is REQUIRED. `fqdn` lives in `[global]` (not `[network]`). For `source = "from-dhcp"` NO other `[network]` keys are allowed; for `from-answer` add cidr/gateway/dns. Conditional `[network]` body emitted via a multiline `E>...<E`. Disk device templated via `>>answer_disk<<`.

## Files changed (BOTH source AND installed copy — they are separate real dirs)
- `/src/osimager-data/osimager_data/specs/proxmox-ve/spec.json` and `files/proxmox-ve/answer.toml`
- `~/.local/lib/python3.12/site-packages/osimager_data/...` (installed copy is what the engine imports; the *engine* is editable but the *data* is a real installed copy — must update both)
- spec.json: added `version_specific` block `[89]\..*` (config: boot_wait 15s + the boot_command); top-level `boot_command` set to `[]`; added `answer_disk` def (default `vda`); platform_specific `answer_disk=sda` for virtualbox/vmware/vsphere.

## Follow-ups / caveats
- `answer_disk`: `vda` (qemu/virtio — PROVEN) vs `sda` (vmware/vsphere/virtualbox — best-effort, UNTESTED).
- `<wait60>` (boot→debug-shell) tuned for KVM (~35s observed). Slower/TCG builds may need more.
- Test harness kept in scratchpad: `sendkeys.py` (qemu HMP monitor keystroke/screendump driver) is reusable for the other broken distros (Fedora 43, Debian 13).
