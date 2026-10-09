---
name: trap-alma-point-release-moves-to-vault
description: AlmaLinux keeps only the current point release per major on repo.almalinux.org; the previous one moves to vault.almalinux.org/<ver>/ and 404s on repo.
metadata:
  type: project
tags: [alma, iso_url, vault, http-not-found, spec]
---

AlmaLinux keeps ONE point release per major on `repo.almalinux.org/almalinux/<ver>/`. When a new one ships, the old directory is reduced to a `README.txt` ("deprecated … go to https://vault.almalinux.org/<ver>/"), and every pinned ISO URL there starts returning 404. The ISOs stay available at `https://vault.almalinux.org/<ver>/isos/<arch>/AlmaLinux-<ver>-<arch>-dvd.iso` (no `almalinux/` path segment).

9.8 and 10.2 shipped on the same day (May 2026), which retired 9.7 and 10.1 together. The fix in v1.9.4: in `osimager/data/specs/alma/spec.json`, point the retired version at the vault, add the new version on repo, and widen `provides.versions`. No rhel spec change is needed, because the alma per-version `iso_url` overrides rhel's `9.*` / `10.*` defaults. The generated build for the new version is byte-identical to the old one apart from random IDs.

Also update the hand-written version ranges: `README.md` (AlmaLinux row), `docs/reference/spec-reference.md` (alma row), and `docs/reference/supported-os.md`, which `docs/generate.py` also produces.

Detect: `curl -sSL https://repo.almalinux.org/almalinux/ | grep -o 'href="[0-9][^"]*"'`. The `-beta` entries show the next point release coming.
