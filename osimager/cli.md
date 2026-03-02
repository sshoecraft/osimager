# cli.py — CLI Entry Points

## Overview

Three console script entry points installed via pip. Each creates an `OSImager` instance and dispatches based on parsed arguments.

## Entry Points

- `main_mkosimage()` — Full build command. Handles `--show-config`, `--check-urls`, `--avail`, `--list`, `--list-platforms`, `--list-defs`, `--init-plugins`, no-target help, and build execution.
- `main_rfosimage()` — Re-provisioning. Same pipeline as mkosimage but replaces the builder with a null builder (keeps communicator + provisioners only).
- `main_mkvenv()` — Virtual environment setup for Ansible version pinning.

## List/Query Flags (handled before target parsing)

1. `--show-config` — Prints current configuration file path and all settings.
2. `--check-urls` — Calls `check_all_urls()` to verify all remote ISO download URLs are accessible. Uses ThreadPoolExecutor for parallel HTTP HEAD checks. Reports OK/FAILED/local-only counts.
3. `--avail` (`-a`) — Shows ISO availability for all specs, categorized as:
   - **Download** — specs with http/https URLs (buildable with network access)
   - **Local** — specs with file:// ISOs that exist on disk (ready to build)
   - **Not available** — file:// ISOs not found locally (must obtain ISO)
4. `--list-platforms` — Iterates `get_platforms()`, skips `all`, prints name/builder_type/arches.
5. `--list-defs` — Collects defs from all platform JSON files, categorizes into base (all.json), platform-specific, and computed. Shows overridable keys.
6. `--list` (`-l`) — Builds spec index via `get_index()`, prints all specs with local ISO markers.
7. `--init-plugins` — Installs all required Packer plugins. Always installs `github.com/hashicorp/ansible`, then walks platform JSON files and installs each platform's `plugin` value (deduplicating).

## No-Target Help

When invoked without a target, mkosimage prints contextual setup guidance:
- Missing locations → shows quickstart copy command
- Missing credentials → shows copy command for example-secrets file + vault option
- Has locations → shows available platform/location pairs

## History

- v1.1.0: Added contextual no-target help with setup guidance
- v1.3.0: Updated docs_url to GitHub Pages
- v1.4.1: Added --list-platforms and --list-defs flags
- v1.4.2: Show cp command for example-secrets, packer prerequisite check, --init-plugins with plugin key in platform JSON files
- v1.4.3: ISO URL fixes across all distros, file:// for unavailable ISOs
- v1.4.4: Added --check-urls (maintenance URL checker), --avail (ISO availability report), pre-build ISO validation (check_iso_url), removed save_index/index file caching, resolve_iso_url now handles arch_specific and E>...<E expressions
- v1.5.0: Config format changed from INI to JSON (config.json), iso_path moved to global settings
