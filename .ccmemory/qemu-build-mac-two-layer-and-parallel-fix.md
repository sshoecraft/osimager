---
name: qemu-build-mac-two-layer-and-parallel-fix
description: Every qemu VM has TWO MACs: build-time qemu default 52:54:00:12:34:56 (all identical) vs run-time libvirt-assigned unique. v1.8.1 injects a per-build…
metadata:
  type: project
tags: [qemu, mac, networking, packer, libvirt, parallel-builds, bridge, v1.8.1]
---

## Every osimager qemu VM has TWO different MACs (this confused a prior session into a false "regression")

1. **Build-time (packer → qemu):** the qemu builder config (`osimager_data/platforms/qemu.json`) sets `net_device: virtio-net` but **no MAC and no qemuargs**. Packer's qemu builder, absent a qemuargs override, boots with qemu's hardcoded default **`52:54:00:12:34:56`** — identical for EVERY build. Verified via `/proc/<pid>/cmdline` (`-device virtio-net,netdev=user.0`, no `mac=`).
2. **Run-time (post_build → libvirt):** `osimager_data/scripts/qemu_post_build.py` (platform `post_build` hook, wired in `qemu.json`) writes a libvirt domain XML whose `<interface>` has **no `<mac>`**, then runs `virsh undefine <name>` + `virsh define`. libvirt auto-assigns a **unique `52:54:00:xx:xx:xx`** per domain. This is why `~/vms/qemu/test1..test32` each show a distinct MAC in `virsh dumpxml` even though the on-disk `<name>.xml` template has none.

**Do NOT conflate these.** A prior session saw all live build VMs on `52:54:00:12:34:56` over QMP, compared it to its memory of test1–32 having unique MACs (which are the *libvirt run-time* MACs), and wrongly concluded per-build MAC assignment had "regressed" and that a plugin/qemu bump broke it. Nothing regressed — osimager never assigned a build-time MAC on any path; libvirt supplies the run-time one. There was never a per-build build-time MAC to break.

## The real defect: parallel BRIDGED builds collide at build time

The `lab` location (`~/.config/osimager/locations/lab.json`) sets qemu `net_bridge: br0`, so builds are bridged onto a shared L2 segment (not the isolated SLIRP NAT that user-mode would give). SSH discovery is **FQDN/DNS-based**: the `ssh` spec sets `ssh_host = >>fqdn<<` for qemu, and dnsmasq on br0 hands out the IP by **DHCP keyed on MAC**. So two concurrent builds with the same `52:54:00:12:34:56` collapse to one DHCP lease/IP and packer's SSH lands on the wrong guest → parallel builds impossible. Serial builds dodge it (only one VM alive on br0 at a time).

## Fix (v1.8.1, engine-side, `core.py` `make_build`)

After the builder config is finalized (just before `self.build` is assembled), inject a unique MAC for **bridged qemu builds only**:
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
Key facts that make this correct:
- **Bridge-only on purpose.** User-mode NICs are isolated per-VM NATs (shared MAC harmless), and overriding `-netdev` there would drop packer's SSH `hostfwd=tcp::{{.SSHHostPort}}-:22` and break those builds.
- **packer overrides its default `-netdev`/`-device` by flag key** (prints "Overriding default Qemu arguments with QemuArgs…", packer v1.15.0 + plugin qemu v1.1.4), so these *replace* (not duplicate) its generated NIC. Assumes the NIC is the only `-device` — true while disks are virtio (`-drive if=virtio`, no `-device`); a future `disk_interface: scsi` would add a `-device` that this override would drop.
- `net_bridge` is intentionally kept in the config so packer still uses its bridge SSH strategy.

## Install/verify notes
- The **engine** (`/src/osimager`) is an **editable** pip install (`{"editable": true}`), so edits to `osimager/core.py` are live for `mkosimage` with no reinstall. (Contrast: **osimager-data** is a *copied* install from `/src/osimager-data` — data changes need `pip install`, but this fix touched no data.)
- Validate by launching 2+ parallel bridged builds and checking each qemu proc: `tr '\0' '\n' < /proc/<pid>/cmdline | grep -i mac=` should show a distinct `52:54:00:xx:xx:xx` per build.
