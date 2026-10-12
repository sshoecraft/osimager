---
name: compiled-proxmox-qemu-build-networking-and-iteration
description: Proxmox/qemu build networking: ssh_host no-value trap, DNS static->dhcp flip, per-build MAC rationale, libvirt_uri knob, rfosimage ansible loop.
metadata:
  type: project
tags: [compiled, proxmox, qemu, packer, ssh_host, mac, libvirt, dns, rfosimage]
---

Topic: how osimager builds reach/identify guests on proxmox-iso and qemu (SSH address discovery, MACs, DNS registration), plus the libvirt registration knob and the fast ansible-debug loop.

## SSH address: `<no value>` trap
- Symptom: proxmox-iso hangs at "Waiting for SSH to become available...", prior line `Using SSH communicator to connect: <no value>`. The VM itself is fine (has an IP, reaches the gateway). Cause: ssh spec (`osimager/data/specs/ssh/spec.json`) `ssh_host` fell through to `'{{ .Host }}'` for every platform not listed explicitly; proxmox-iso has no `.Host` in its template context, Go templating renders literal `<no value>`, and a non-empty `ssh_host` beats guest-agent discovery, so packer dials that name until `ssh_timeout`.
- Fix (v1.9.3): proxmox -> `''`. osimager strips empties ("warning: removing empty value for: ssh_host"); with `ssh_host` unset the builder takes the IP from the QEMU guest agent (`qemu_agent: true` in proxmox.json; kickstarts install `qemu-guest-agent`). A spec with `qemu_agent: false` on proxmox (the old rhel ones) has no discovery path. General tell: `<no value>` in packer output = a `{{ .X }}` the builder doesn't provide; verify with `python3 bin/mkosimage -u <target> <name>` and grep the dump. See `trap-proxmox-ssh-host-no-value`.
- For qemu (v1.8.5) `ssh_host` is scoped `'' if dist=='proxmox-ve' else fqdn` (`>>dist<<` set at core.py:1165): Proxmox uses discovery (static IP during build, no resolvable FQDN), others use FQDN. See `proxmox-dns-fix-and-mac-cleanup`.

## MACs (chronological, with a corrected rationale)
1. v1.8.1: every qemu VM has two MACs. Build-time (packer -> qemu): `osimager_data/platforms/qemu.json` sets `net_device: virtio-net`, no MAC, no qemuargs, so qemu's hardcoded default `52:54:00:12:34:56` is used, identical for EVERY build (verified via `/proc/<pid>/cmdline`: `-device virtio-net,netdev=user.0`, no `mac=`). Run-time (post_build -> libvirt): `osimager_data/scripts/qemu_post_build.py` (platform `post_build` hook wired in qemu.json) writes domain XML whose `<interface>` has no `<mac>`, then `virsh undefine <name>` + `virsh define`; libvirt auto-assigns unique `52:54:00:xx:xx:xx`. That is why `~/vms/qemu/test1..test32` each show a distinct MAC in `virsh dumpxml` though the on-disk `<name>.xml` template has none. Do not conflate: a prior session saw all live build VMs on `52:54:00:12:34:56` over QMP, compared with its memory of test1-32 unique MACs (libvirt run-time ones), and wrongly concluded per-build MAC assignment "regressed" after a plugin/qemu bump. Nothing regressed; osimager never assigned a build-time MAC on any path.
   - Original (later disproved) defect framing: `lab` location (`~/.config/osimager/locations/lab.json`) sets qemu `net_bridge: br0` (bridged on shared L2, not isolated SLIRP NAT); SSH discovery is FQDN/DNS-based (`ssh_host = >>fqdn<<`), dnsmasq on br0 does DHCP keyed on MAC, so concurrent builds with the same MAC were thought to collapse to one lease. Serial builds dodge it.
   - Fix (engine-side, `core.py` `make_build`, just before `self.build` is assembled), bridged qemu only:
```python
if (self.config.get('type') == 'qemu'
        and self.config.get('net_bridge')
        and 'qemuargs' not in self.config):
    h = uuid.uuid4().hex
    nic_mac = "52:54:00:%s:%s:%s" % (h[0:2], h[2:4], h[4:6])
    net_device = self.config.get('net_device', 'virtio-net')
    self.config['qemuargs'] = [
        ["-netdev", "bridge,id=user.0,br=%s" % self.config['net_bridge']],
        ["-device", "%s,netdev=user.0,mac=%s" % (net_device, nic_mac)],
    ]
```
   - Why correct: bridge-only because user-mode NICs are isolated per-VM NATs (shared MAC harmless) and overriding `-netdev` there would drop packer's `hostfwd=tcp::{{.SSHHostPort}}-:22`. Packer overrides its default `-netdev`/`-device` by flag key (prints "Overriding default Qemu arguments with QemuArgs...", packer v1.15.0, plugin qemu v1.1.4), replacing not duplicating. Assumes the NIC is the only `-device` (true while disks are `-drive if=virtio`); a future `disk_interface: scsi` adds a `-device` this override would drop. `net_bridge` stays in config so packer keeps its bridge SSH strategy.
   - Install/verify: engine `/src/osimager` is an editable pip install (`{"editable": true}`), edits to `osimager/core.py` are live; osimager-data is a copied install from `/src/osimager-data` (this fix touched no data). Validate with 2+ parallel bridged builds: `tr '\0' '\n' < /proc/<pid>/cmdline | grep -i mac=` shows distinct MAC per build. See `qemu-build-mac-two-layer-and-parallel-fix`.
2. Later correction: the "parallel builds collide on the shared MAC" premise was DISPROVED by the dispatcher (26 parallel qemu/lab/ubuntu builds worked on the shared MAC; well-behaved distros send unique DHCP client-ids so dnsmasq distinguishes them). Injection KEPT for a different reason: with the shared MAC, packer's bridge SSH-address discovery matches a STALE ARP entry from an old build and hangs on a dead IP. Proven: removed injection -> pve9-5 installed fine and ran on `.158`, but packer hung forever on stale `.159`. Unique per-build MAC = one clean bridge address. Proxmox hits this because it is static during the build, so `ssh_host` uses discovery. `make_build` no longer sets a `mac_address` def (answer.toml filter is `eth0`, not MAC-based). The earlier collision framing is superseded. See `proxmox-dns-fix-and-mac-cleanup`.

## Proxmox DNS self-registration
- PVE installer ALWAYS writes a static `/etc/network/interfaces` (Proxmox docs + live VMs). A static host never sends a DHCP request, so dnsmasq never learns its name; only DHCP clients that send a hostname self-register (why Ubuntu registers). Passing a static IP does NOT register (false claim for Proxmox); neither did `from-dhcp` originally.
- Fix (proven, pve9-4): `proxmox-ve` spec `shutdown_command` flips static->dhcp over packer's root SSH session before halt (no sudo, no dnsmasq edit, no ISO repack), only when no static IP was passed:
```
shutdown_command = E>("sed -i '/vmbr0 inet/s/static/dhcp/; /address /d; /gateway /d' /etc/network/interfaces; " if ">>ip<<" in ("", "dhcp") else "") + "/sbin/shutdown -P now"<E
```
  Proof: `mkosimage qemu/lab/proxmox-ve-9.1-x86_64 pve9-4` -> `virsh start pve9-4` -> lease shows hostname `pve9-4` -> `pve9-4.vm.localdomain` resolves to .132. Trade-off: deterministic IP and zero-config registration are mutually exclusive (registration IS the DHCP request).
- v1.8.5 minimal set KEPT: `skip_config: true` for proxmox-ve (skip linux ansible, appliance, no sudo; engine honors it in `make_build`), the shutdown flip, unique-MAC injection, scoped ssh_host, answer.toml `from-answer` `filter.ID_NET_NAME = "eth0"` (net.ifnames=0). REMOVED: dead `dnsmasq_hostsdir` engine write + setting (`"dnsmasq_hostsdir": ""`, never enabled).
- REVERT: pre-cleanup full-file backups in `scratchpad/pre-cleanup-backup/`. The removed write was inside the MAC block (`hostsdir = self.settings.get('dnsmasq_hostsdir')` -> write `<mac>,<name>`). See `proxmox-dns-fix-and-mac-cleanup`.

## libvirt_uri knob (osimager-data v1.8.0)
- qemu post_build hook (`osimager_data/scripts/qemu_post_build.py`) called bare `virsh` (no `--connect`), so unprivileged builds silently landed in `qemu:///session`. Target is now `libvirt_uri`, analog of vSphere `vcenter_server` / Proxmox `proxmox_url`. Precedence: `defs['libvirt_uri']` (-D > spec defs > location defs > qemu.json defs; location loads after platform so overrides the default), then `LIBVIRT_DEFAULT_URI`, then `qemu:///system` if `os.geteuid()==0` else `qemu:///session`. `platforms/qemu.json` ships `defs: {"libvirt_uri": ""}`. Hook echoes `libvirt: VM '<name>' defined (<uri>)`.
- Set it in the location file: `lab.json` -> `platform_specific[qemu].defs.libvirt_uri = "qemu:///system"` (a `defs` sub-block, not `config`, since the post-build hook reads it, not the Packer qemu builder). Siblings: `locations/esx.json` -> `platform_specific[vsphere].defs.esxi_host`; `locations/pve*.json` -> `defs.proxmox_node`.
- config.json is the WRONG layer: `load_settings` (core.py:263) only accepts keys already in `self.settings`, so `--set`/config.json silently drop unknown keys (config.json holds only build knobs: cpu/mem/paths/creds); and settings merge into defs at core.py:234 BEFORE the platform loads (1205), so the empty qemu.json default clobbers it anyway.
- Verify without building: `mkosimage --defs qemu/lab/<spec> <name>` (`-x`) dumps resolved `self.defs`, exits before packer (cli.py:308) -> confirm `"libvirt_uri": "qemu:///system"`. `--dump` (`-u`) dumps the Packer build config and must NOT show it.
- Mechanics: `bin/mkosimage` is a dev shim; real command is entry point `osimager.cli:main_mkosimage`. The virsh define lives in the osimager-data hook, not the engine. `qemu:///system` needs the `libvirt` group (steve is in it, gid 115), not root. Engine = editable (`pip install -e`); data = plain copy, reinstall via `cd /src/osimager-data && pip3 install .` (defaults `--user`; not `-e`). `/src` is NFS `all_squash` (anonuid=root): files show `root:root` but steve can write; no sudo. See `qemu-libvirt-uri-knob`.

## Debugging ansible/post-install failures fast
- Full `mkosimage` is ~7-9 min (install + reboot + SSH + ansible). `mkosimage -k <platform>/<location>/<spec> <name>` (`--keep`) keeps the VM and temp files on failure instead of deleting the output dir/shutting down, leaving a running SSH-reachable VM at its `ssh_host` (`<name>.<domain>` on the build network, e.g. br0).
- `rfosimage <platform>/<location>/<spec> <name>` re-runs only the ansible provisioner against it (~1-3 min). Internals (`cli.py:main_rfosimage`): calls `make_build`, deletes `spec['files']`, replaces the qemu/real builder with a `type: "null"` builder keeping only the communicator `ssh_*` keys, runs packer (SSH into live VM, run `config.yml`). Loop: -k once, edit tasks, rfosimage, repeat until green, one final clean mkosimage.
- Do not hand-run `ansible-playbook -i myinv config.yml` with `ansible_user=root`: ansible optimizes away `become` when remote user == become_user, giving a FALSE green that misses "sudo: not found". rfosimage reproduces the real invocation (same vars, communicator, become behavior).
- Caveats: runs against the VM's current state, so tasks must be idempotent (else spurious changed/failed); the kept VM must still be running and reachable at `ssh_host` (not rebooted to the install CD via boot-order quirk). See `iterate-ansible-with-rfosimage-on-kept-vm`.
