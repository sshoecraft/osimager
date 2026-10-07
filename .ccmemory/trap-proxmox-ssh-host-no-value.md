---
name: trap-proxmox-ssh-host-no-value
description: Packer "Using SSH communicator to connect: <no value>" = ssh_host rendered a template var the builder lacks ({{ .Host }} on proxmox-iso). Proxmox nee…
metadata:
  type: project
tags: [proxmox, ssh_host, packer, guest-agent, discovery]
---

Symptom: proxmox-iso build hangs at "Waiting for SSH to become available...", the line before reads `Using SSH communicator to connect: <no value>`. The VM itself is fine — it has an IP and can reach the gateway.

Cause: the ssh spec (`osimager/data/specs/ssh/spec.json`) `ssh_host` fell through to `'{{ .Host }}'` for every platform not listed explicitly. proxmox-iso has no `.Host` in its template context, so Go templating renders the literal `<no value>`. A non-empty `ssh_host` wins over guest-agent discovery, so packer dials that name until `ssh_timeout`.

Fix (v1.9.3): proxmox → `''`. osimager strips empty values ("warning: removing empty value for: ssh_host"), and with `ssh_host` unset the builder takes the IP from the QEMU guest agent (`qemu_agent: true` in proxmox.json). The kickstarts install `qemu-guest-agent`. A spec that sets `qemu_agent: false` on proxmox (the old rhel ones) would have no discovery path at all.

General tell: `<no value>` anywhere in packer output means a `{{ .X }}` the builder doesn't provide. Verify with `python3 bin/mkosimage -u <target> <name>` and grep the dump.
