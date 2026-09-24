---
name: iterate-ansible-with-rfosimage-on-kept-vm
description: Fast osimager workflow for debugging ansible/post-install failures: mkosimage -k keeps the failed VM, rfosimage re-runs ONLY ansible against it (no O…
metadata:
  type: reference
---

# Iterating on ansible failures without rebuilding (mkosimage -k + rfosimage)

When an osimager build fails in the **ansible/post-install** step (not the install), do NOT keep re-running full `mkosimage` builds (~7–9 min each: install + reboot + SSH + ansible). Use the built-in retrofit loop:

1. **`mkosimage -k <platform>/<location>/<spec> <name>`** — the `-k`/`--keep` flag keeps the VM (and temp files) on failure instead of deleting the output dir / shutting down. So a build that dies in ansible leaves a **running, SSH-reachable VM** at its `ssh_host` (`<name>.<domain>` on the build network, e.g. br0).

2. **`rfosimage <platform>/<location>/<spec> <name>`** — re-runs **only the ansible provisioner** against that existing VM. Internally (`cli.py:main_rfosimage`) it calls `make_build`, deletes `spec['files']`, then **replaces the qemu/real builder with a `type: "null"` builder that keeps only the communicator (`ssh_*`) keys**, and runs packer. So packer skips VM creation and just SSHes into the live VM and runs `config.yml`. Fast (~1–3 min), repeatable after each fix.

Loop: `mkosimage -k` once → edit ansible task files → `rfosimage` → repeat until green → one final clean `mkosimage` to confirm.

## Why hand-rolling ansible yourself is worse (learned the hard way)
Running `ansible-playbook -i myinv config.yml` directly against a VM with `ansible_user=root` gives a **FALSE green**: ansible optimizes away `become` when remote user == become_user, so `become: true` never invokes `sudo`. osimager's real invocation (which `rfosimage` reproduces exactly) DOES invoke `become`, so it catches issues like "sudo: not found" that the hand-rolled run silently passes. Always use `rfosimage` — it matches the real Packer/ansible environment (same vars, same communicator, same become behavior).

## Caveats
- `rfosimage` runs against the VM's **current state**; already-applied tasks re-run, so ansible tasks must be idempotent or you'll see spurious changed/failed on re-run.
- The kept VM must still be running and reachable at the build's `ssh_host`. If it rebooted to the install CD (boot-order quirk) it won't be reachable.
