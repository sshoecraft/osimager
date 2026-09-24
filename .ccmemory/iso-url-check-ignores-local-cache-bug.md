---
name: iso-url-check-ignores-local-cache-bug
description: Fixed core.py check_iso_url(): it HEAD-checked http(s) ISO URLs even when the ISO was already cached locally, so an upstream 404 blocked builds of lo…
metadata:
  type: project
---

## Bug
`OSImager.check_iso_url()` (core.py, run from `run_packer()`) validated http/https
`iso_url` values with an unconditional `urllib.request` HEAD request before every
build. If the upstream URL had moved/been removed (e.g. AlmaLinux only mirrors the
latest point release at a given path — 9.7 disappeared once 9.8 shipped), the build
aborted with a 404 error even though the ISO file was already sitting in `iso_path`
or the packer cache.

This was inconsistent with the rest of the codebase: `check_iso_local()` (used by
`make_index()` for `--list`/`--avail`, and by `--check-urls`'s skip logic) already
knows how to detect a locally-cached remote ISO by filename. `check_iso_url()` just
never consulted it.

Symptom: `bin/mkosimage proxmox/pve1/alma-9.7-x86_64 alma-9-1` failed with
`error: ISO URL returned 404 (not found)` even though `mkosimage --list` showed
`alma-9.7-x86_64 (*)` (asterisk = iso_local True).

## Fix
In `check_iso_url()`, before doing the HEAD request on an http/https URL, call
`self.check_iso_local(iso_url)` and return early if true. Local file:// URLs were
already handled correctly (checked via `os.path.exists`, no network involved).

## Lesson
Any new "is this ISO available" check should reuse `check_iso_local()` rather than
re-deriving local-cache logic or assuming remote reachability implies buildability.
