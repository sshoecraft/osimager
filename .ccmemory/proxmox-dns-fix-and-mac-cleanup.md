---
name: proxmox-dns-fix-and-mac-cleanup
description: Proxmox self-registers via a shutdown static→dhcp flip. The per-build MAC injection is KEPT — not for parallel collisions (disproved) but for packer…
metadata:
  type: project
tags: [proxmox-ve, dns, dnsmasq, dhcp, mac, discovery, ssh_host, shutdown_command, cleanup]
---

## The DNS problem & the ONE fix
Proxmox VMs didn't register in the lab dnsmasq — neither `from-dhcp` nor a static IP. Root cause (Proxmox docs + live VMs): **the PVE installer ALWAYS writes a STATIC `/etc/network/interfaces`.** A static host never sends a DHCP request, so dnsmasq never learns its name. Only DHCP clients that send a hostname self-register (that's why Ubuntu registers and static Proxmox can't; passing a static IP does NOT register — false claim for Proxmox).

**THE FIX (proven, pve9-4):** the `proxmox-ve` spec `shutdown_command` flips the installed interface `static`→`dhcp` over packer's root SSH session before halt — no sudo, no dnsmasq edit, no ISO repack. On run, the VM DHCPs, sends its hostname, dnsmasq registers `<name>.vm.localdomain`. Only when NO static IP was passed:
```
shutdown_command = E>("sed -i '/vmbr0 inet/s/static/dhcp/; /address /d; /gateway /d' /etc/network/interfaces; " if ">>ip<<" in ("", "dhcp") else "") + "/sbin/shutdown -P now"<E
```
Proof: `mkosimage qemu/lab/proxmox-ve-9.1-x86_64 pve9-4` → `virsh start pve9-4` → lease `... pve9-4` (hostname present) → `pve9-4.vm.localdomain` resolves to .132.
Trade-off (protocol reality): deterministic IP AND zero-config self-registration are mutually exclusive; registration IS the DHCP request.

## The per-build MAC injection: KEEP IT — reason corrected
- **WRONG original rationale:** "parallel qemu builds collide on the shared default `52:54:00:12:34:56`." Dispatcher DISPROVED this — 26 parallel qemu/lab/ubuntu builds succeeded on the shared MAC (well-behaved distros send unique DHCP client-ids, so dnsmasq distinguishes them).
- **REAL reason it's needed:** packer's **SSH-address DISCOVERY**. With the shared default MAC, packer's bridge discovery matches a **STALE ARP entry** from an old build and connects to a DEAD IP. **Proven:** removed the injection → pve9-5 installed fine and ran on `.158`, but packer hung forever on stale `.159`. A unique per-build MAC = one clean bridge address. Proxmox hits this because it's **static during the build**, so `ssh_host` uses discovery, not a resolvable FQDN.
- So `make_build` KEEPS the qemuargs unique-MAC block. It does NOT set a `mac_address` def anymore (the answer.toml filter is `eth0` now, not MAC-based), and the dead `dnsmasq_hostsdir` write is gone.

## Final minimal diff (v1.8.5)
KEEP:
- `proxmox-ve` `skip_config: true` — skip the linux ansible (appliance, no sudo); engine honors it in `make_build`.
- `proxmox-ve` `shutdown_command` DHCP flip (above) — the DNS fix.
- qemu unique-MAC injection in `make_build` — packer discovery reliability.
- ssh spec `ssh_host` scoped: `'' if dist=='proxmox-ve' else fqdn` for qemu (Proxmox→discovery, others→FQDN). `>>dist<<` set at core.py:1165.
- answer.toml `from-answer` needs `filter` → `filter.ID_NET_NAME = "eth0"` (net.ifnames=0).
REMOVED: `dnsmasq_hostsdir` engine write + setting (dead, never enabled).

## REVERT
Pre-cleanup full-file backups (this session): `scratchpad/pre-cleanup-backup/`. The removed dnsmasq write was inside the MAC block (`hostsdir = self.settings.get('dnsmasq_hostsdir')` → write `<mac>,<name>`); the removed setting was `"dnsmasq_hostsdir": ""`. Supersedes the original MAC analysis in [[qemu-build-mac-two-layer-and-parallel-fix]] (its parallel-collision framing was wrong; the discovery framing here is right).
