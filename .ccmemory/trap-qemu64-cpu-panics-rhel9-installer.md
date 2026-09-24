---
name: trap-qemu64-cpu-panics-rhel9-installer
description: qemu build VM with no -cpu gets qemu64 (x86-64-v1); RHEL 9 (v2) / RHEL 10 (v3) installer init exits 127 → kernel panic ~26s. Fixed: qemu.json cpu_mod…
metadata:
  type: project
---

Symptom: RHEL 9/10 qemu build hangs forever at "Waiting for the guest address… br0"; guest console shows `Attempted to kill init! exitcode=0x00007f00` ~26 s into boot; build disk stays ~196 KB. RHEL 8 builds fine on the same host.

Cause: packer-plugin-qemu passes no `-cpu` unless `cpu_model` is set, so the guest gets QEMU's `qemu64` model (baseline x86-64 only). RHEL 9 glibc needs x86-64-v2, RHEL 10 needs v3, so init can't exec. The engine's bridged-NIC `qemuargs` block (core.py) never had `-cpu` either, but the fix belongs in data, not there.

Fix (1.9.1): `platforms/qemu.json` config `"cpu_model": "E>'host' if os.access('/dev/kvm', os.W_OK) else 'max'<E"` — mirrors the `accelerator` expression; `-cpu host` refuses to start under TCG, hence `max`. Covers bridged and non-bridged builds.

The finished VM was never affected: `scripts/qemu_post_build.py` writes libvirt XML with `<cpu mode='host-passthrough'/>`.

Verify: `PACKER_LOG=1` and grep the `Executing /usr/bin/qemu-system-x86_64` line for `"-cpu", "host"`; a healthy install reaches "Found guest address" and the disk grows past hundreds of MB within a few minutes.
