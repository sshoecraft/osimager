# core.py — OSImager Class

## Overview

Single-class module containing the `OSImager` class. Orchestrates the entire build pipeline: CLI arg parsing, settings management, config loading (platform/location/spec with recursive includes), template substitution, ISO resolution, credential handling, and Packer execution.

## Class: OSImager

### Construction

`OSImager(argv, which, extra_args)` — `which` is `"full"` (build mode) or `"venv"` (setup only). Calls `init_vars()` then `init_settings()`.

### Key Instance Variables

- `settings` — Runtime config: `base_dir`, `user_dir`, `packer_cmd`, `venv_dir`, `ansible_playbook`, `packer_cache_dir`, `local_only`, `credential_source`, `vault_addr`, `vault_token`, `iso_path`
- `system_data_dir` — Path to osimager-data package (baseline data), or None if not installed
- `defs` — All template substitution variables, accumulated from settings/platform/location/spec/runtime
- `config` — Packer builder configuration, becomes `builders[0]` in output
- `variables` — Packer user variables for `{{user ...}}` references
- `evars` — Environment variables set before Packer runs
- `files` — Installer file generation recipes (sources + dest)
- `provisioners`, `pre_provisioners`, `post_provisioners` — Ansible provisioner lists
- `platform`, `location`, `spec` — Raw loaded config data
- `vault`, `secrets` — Credential storage (vault client or local secrets dict)

### CLI Flags

`target`, `name`, `ip`, `list`, `avail`, `list_platforms`, `list_defs`, `init_plugins`, `check_urls`, `show_config`, `dump_defs`, `dump_build`, `verbose`, `debug`, `on_error`, `log`, `logfile`, `force`, `keep`, `timestamp`, `local_only`, `dry_run`, `user_defines`, `user_temp_dir`, `config_file`

## Method Groups

### Initialization
- `init_vars()` — Zero all accumulator state
- `init_settings(argv, which, extra_args)` — Parse CLI args, load/save settings, create user dirs, seed defs
- `load_settings(config_path)` — Read `~/.config/osimager/config.json` via JSON
- `save_settings(config_path)` — Write current settings to config.json

### Data Resolution (Two-Layer)
- `resolve_data_path(*parts)` — Find a data file: checks user dir (`~/.config/osimager/`) first, then osimager-data package. Returns first existing path, or None.
- `resolve_data_files(subdir, pattern)` — Scan both layers, merge results (user wins on name collisions). Used for listings.

### Data Loading
- `read_data(file_path)` — Load JSON or TOML file
- `load_file(where, file_path)` — Read data file, recursively process `include` chains, call `load_data()`
- `load_data_file(where, what)` — Resolve logical name via `resolve_data_path()`, call `load_file()`
- `load_data(data)` — Merge config dict sections into instance accumulators, process `*_specific` overrides
- `load_inc(where, what, data)` — Handle include directive
- `load_specific(data)` — Process platform/location/dist/version/arch/firmware_specific sections via regex matching

### Index and Discovery
- `make_index()` — Scan all specs, expand version ranges, iterate candidate arches per version, probe `resolve_iso_url()` and `resolve_disk_image_url()` to determine arch availability. An entry is indexed if it has **either** an installer ISO or a prebuilt disk image; entries with neither are skipped. Disk-image entries carry `disk_image_url`, `disk_image_local`, and `image_import: True`. Always built fresh (no file caching).
- `get_index(name)` — Calls `make_index()`, optionally filters by name
- `spec_get_provides(file_name, data)` — Extract provides entries (dist+version pairs), expand version ranges. Arches are no longer part of provides — they are derived at index time by probing `resolve_iso_url()`.
- `get_platforms(names)` — List platform configs
- `get_locations(platform_names)` — List location configs from user dir
- `get_specs(search_string)` — List spec configs

### ISO and URL Handling
- `resolve_url_field(data, version, arch, field)` — Shared resolver for URL-valued spec fields. Uses key-presence checks (not truthiness) so `"<field>": ""` can explicitly clear. Handles basic `>>var<<` substitution, `arch_specific` overrides (both top-level and within `version_specific`, version_specific arch_specific winning last), remaining `>>var<<` markers from spec defs (e.g., `deb_arch`), and `E>...<E` expression evaluation. Returns None when the field resolves to empty — this is how arch restriction works (empty URL blocks an arch).
- `resolve_iso_url(data, version, arch)` — Thin wrapper: `resolve_url_field(..., "iso_url")`.
- `resolve_disk_image_url(data, version, arch)` — Thin wrapper: `resolve_url_field(..., "disk_image_url")`. For appliances that ship a prebuilt qcow2/vmdk/ova instead of an installer ISO. The import builder consumes it as input rather than booting an installer. `make_build()` derives `disk_image_name` and sets the `image_import` def when present.
- `check_iso_local(iso_url)` — Check if ISO exists locally (file:// path or packer cache)
- `check_iso_url()` — Pre-build validation called from `run_packer()`. For file:// URLs, verifies file exists with helpful error message. For http(s):// URLs, does HEAD request and aborts on 404.
- `check_all_urls()` — Maintenance tool invoked by `--check-urls`. Creates a dummy location, resolves all spec URLs via `make_index()`, checks each unique URL in parallel (ThreadPoolExecutor, 10 workers). Reports OK/FAILED/local-only counts. Cleans up dummy location on exit.
- `check_iso_urls(urls)` — Validate remote ISO URLs during build, download checksums, set defs
- `get_iso_file(urls)` — Resolve local ISO file path, set defs for local-only mode

### Credentials
- `load_credentials()` — Dispatch to vault or config mode
- `load_secrets()` — Parse `~/.config/osimager/secrets` file
- `get_secret(string)` — Retrieve secret from vault or local secrets
- `resolve_packer_vault_refs(data)` — Replace `{{vault ...}}` in Packer JSON with local secret values

### Build Assembly
- `make_build(target, name, ip)` — Full build pipeline: parse target, load platform/location/spec, resolve ISO, load credentials, perform substitutions, assemble Packer JSON
- `gen_files()` — Assemble installer files from template fragments, write to temp dir
- `check_required_files()` — Verify spec's required_files exist on disk
- `run_packer()` — Validate prereqs, `check_required_files()`, `check_iso_url()`, `gen_files()`, run **pre_build** hooks, write build JSON, set environment, execute packer command, then run **post_build** hooks on success.

### Build Hooks
- `run_build_script(path)` — Load a Python script from the data dir (`resolve_data_path`) and call its `run(osimager)` function.
- `run_build_hooks(hook_name)` — Run `pre_build`/`post_build` hooks declared by the **spec** first, then the **platform** (`self.spec.get(hook_name)`, then `self.platform.get(hook_name)`). `pre_build` runs *before* the build JSON is written, so a hook may transform the ISO/disk image (e.g. `coreos-installer iso customize` to bake an Ignition config in) and adjust `self.config`/`self.defs`. Data-side contract: declare `"pre_build": "scripts/<name>.py"` (or `post_build`) in a spec or platform JSON; the script exposes `def run(osimager)` and reads `osimager.defs` (`iso_url`/`iso_name`, `disk_image_url`, `temp_dir`, etc.).

## History

- v1.0.0: Initial package refactor from lib/osimager/
- v1.1.0: User config system (~/.config/osimager/), credential_source (vault/config)
- v1.2.0: TOML location support, pyproject.toml dynamic version
- v1.3.0: Cloud platforms (aws/azure/gcp), additional hypervisors
- v1.4.0: MkDocs documentation
- v1.4.1: --list-platforms, --list-defs
- v1.4.2: --init-plugins, --show-config, example-secrets copy command
- v1.4.3: ISO URL fixes across all distros, file:// for unavailable ISOs
- v1.4.4: --check-urls, --avail (ISO availability), pre-build check_iso_url(), removed save_index/index file caching, resolve_iso_url handles arch_specific + expression eval
- v1.5.0: Config format changed from INI (configparser) to JSON (config.json), iso_path moved from location defs to global settings. Removed `provides.arches` and `version_specific[].arches` — arches now derived from ISO URL resolution at index time. Specs use `arch_specific` entries with explicit per-arch iso_url and `"iso_url": ""` to block unsupported arches.
- v1.7.0: Two-layer data resolution. Engine separated from data. User overrides in `~/.config/osimager/` (specs, platforms, files, scripts) take precedence over `osimager-data` package baseline. XDG paths for all directories. Removed constants.py (version/exit codes now in core.py). Fixed venv hoisting from version_specific entries.
- v1.8.0: Disk-image import builds — `resolve_disk_image_url()` (sibling of `resolve_iso_url()`, both now share `resolve_url_field()`); `make_index()` indexes a spec/version/arch when it has an ISO **or** a `disk_image_url`; `make_build()` derives `disk_image_name` and the `image_import` def. Per-spec build hooks — `run_build_hooks()` runs `pre_build`/`post_build` from the spec then the platform; `pre_build` now runs before the build JSON is written so a hook can mutate the ISO/disk image (e.g. bake an Ignition config for CoreOS/Flatcar) before Packer consumes it.
