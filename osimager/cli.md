# cli.py — CLI Entry Points

## Overview

Three console script entry points installed via pip. Each creates an `OSImager` instance and dispatches based on parsed arguments.

## Entry Points

- `main_mkosimage()` — Full build command. Handles `--list`, `--list-platforms`, `--list-defs`, no-target help, and build execution.
- `main_rfosimage()` — Re-provisioning. Same pipeline as mkosimage but replaces the builder with a null builder (keeps communicator + provisioners only).
- `main_mkvenv()` — Virtual environment setup for Ansible version pinning.

## List Flags (handled before target parsing)

1. `--list-platforms` — Iterates `get_platforms()`, skips `all`, prints name/builder_type/arches.
2. `--list-defs` — Collects defs from all platform JSON files, categorizes into base (all.json), platform-specific, and computed. Shows overridable keys.
3. `--list` / `--avail` — Builds spec index via `get_index()`, prints all specs (or only those with local ISOs).

## No-Target Help

When invoked without a target, mkosimage prints contextual setup guidance:
- Missing locations → shows quickstart copy command
- Missing credentials → shows both vault and config options
- Has locations → shows available platform/location pairs

## History

- v1.1.0: Added contextual no-target help with setup guidance
- v1.3.0: Updated docs_url to GitHub Pages
- v1.4.1: Added --list-platforms and --list-defs flags
