---
name: local-only-not-auto-detected-from-cached-iso
description: core.py make_build now auto-sets local_only=True when the resolved iso_url is already cached locally, instead of requiring the user to pass --local m…
metadata:
  type: project
---

## Bug
`local_only` (which flips Proxmox/other platform templates from downloading
`iso_url` to referencing an already-present `iso_file`) was ONLY ever set by
the explicit `--local`/`--local-only` CLI flag or `local_only` in config.json.
It was never inferred from whether the specific spec's ISO was actually
available locally (`check_iso_local()`), even though `--list`/`--avail` show
the exact same local-availability info via the `(*)` marker.

Result: an ISO already downloaded/cached (e.g. `/iso/AlmaLinux-9.7-x86_64-dvd.iso`,
confirmed via `check_iso_local()`) still required the user to manually pass
`--local` on every build, or `mkosimage` would try to have Packer download the
ISO fresh from `iso_url` — which fails outright if the upstream URL has since
gone stale (see `iso-url-check-ignores-local-cache-bug` memory for a related bug
in the pre-flight HEAD check).

## Fix
In `make_build()` (core.py), right after `self.defs = do_sub(self.defs,self)`
(~line 1414) and before provisioners/config get substituted, added:

```python
if not self.defs.get('local_only') and self.check_iso_local(self.defs.get('iso_url', '')):
    self.defs['local_only'] = True
```

This only ever turns local_only ON automatically (never overrides an explicit
True->False), and reuses the same `check_iso_local()` helper as `--avail`/`--list`
so the two code paths can't disagree about what counts as "local."

Verified via `mkosimage -x` (dump defs) and `mkosimage -u` (dump build json)
against `proxmox/pve1/alma-9.7-x86_64`: `local_only` resolves to `true` and the
Proxmox builder config emits `iso_file: "iso:iso/AlmaLinux-9.7-x86_64-dvd.iso"`
(the PVE-storage-pool path) with no `--local` flag passed.

## Note on what "local" means for Proxmox
For the proxmox platform, `local_only=True` doesn't mean "cached on the machine
running mkosimage" — it means "already uploaded to the Proxmox host's ISO
storage pool" (`iso_file: "<storage_pool>:iso/<name>"`). In this environment
`/iso` (checked by `check_iso_local`) happens to be the same NFS-backed storage
Proxmox's `iso` storage pool points at, so the local-file check is a valid proxy.
If a deployment's `/iso` mount and PVE storage pool ever diverge, this
auto-detection would need to become platform-aware.
