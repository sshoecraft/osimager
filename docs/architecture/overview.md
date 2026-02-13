# System Architecture

OSImager v1.3.0 -- a Python-based OS image builder that orchestrates HashiCorp Packer to create VM images across 13 platforms and 12 OS distribution families. The entire build pipeline is driven by a single `OSImager` class that loads JSON/TOML configuration, performs template substitution, and executes Packer.

## Package Structure

```
osimager/
    __init__.py          -- re-exports OSImager class
    core.py              -- OSImager class, all build logic (1415 lines)
    cli.py               -- 3 CLI entry points: main_mkosimage, main_rfosimage, main_mkvenv (204 lines)
    utils.py             -- template substitution engine, version expansion, password hashing, network utils (847 lines)
    constants.py         -- OSIMAGER_VERSION, SUPPORTED_PLATFORMS, SUPPORTED_DISTRIBUTIONS, SUPPORTED_ARCHITECTURES, DEFAULT_SETTINGS, ERROR_MESSAGES, EXIT_CODES (227 lines)
    data/
        platforms/       -- 13 platform configs + all.json (base defaults)
        specs/           -- 15 spec directories (one per distro family + base communicator/OS specs)
        files/           -- installer templates organized by distro (8 directories)
        tasks/           -- 21 Ansible task files for post-install provisioning
        ansible/         -- config.yml (main Ansible playbook)
        examples/        -- quickstart-location.toml, example-secrets, example-vault, example-location.json, example-location.toml
```

## The OSImager Class

Single class in `core.py` that orchestrates everything. Instantiated with `OSImager(argv, which, extra_args)` where `which` is `"full"` (build mode) or `"venv"` (setup only). The constructor calls `init_vars()` then `init_settings(argv, which, extra_args)`.

### Instance Variables

**Accumulator state** -- populated progressively as platform, location, and spec configs are loaded:

| Variable | Type | Purpose |
|---|---|---|
| `settings` | dict | Runtime configuration: `base_dir`, `user_dir`, `data_dir`, `packer_cmd`, `venv_dir`, `ansible_playbook`, `packer_cache_dir`, `local_only`, `save_index`, `credential_source`, `vault_addr`, `vault_token` |
| `defs` | dict | All template substitution variables accumulated from settings, platform, location, spec, and runtime values. Used by `>>var<<` and all other marker patterns. |
| `config` | dict | Packer builder configuration. Populated by platform/location/spec `config` sections via `load_data()`. Becomes `builders[0]` in final output. |
| `variables` | dict | Packer user variables for `{{user ...}}` references. Contains `platform-name`, `location-name`, `spec-name`, `spec-config`, `name`, `fqdn`. |
| `evars` | dict | Environment variables set before Packer runs. Includes Ansible control vars (`ANSIBLE_RETRY_FILES_ENABLED`, `ANSIBLE_NOCOWS`, etc.) and optionally `VAULT_TOKEN`, `VAULT_ADDR`, `PATH`. |
| `files` | list | Installer file generation recipes. Each entry has `sources` (template fragments) and `dest` (output filename). Processed by `gen_files()`. |
| `provisioners` | list | Main Ansible provisioners. Initialized with a default ansible provisioner in `make_build()`. |
| `pre_provisioners` | list | Provisioners that run before main provisioners. |
| `post_provisioners` | list | Provisioners that run after main provisioners. |
| `platform` | dict | Raw loaded platform config data. |
| `location` | dict | Raw loaded location config data. |
| `spec` | dict | Raw loaded spec config data. |
| `vault` | hvac.Client or None | HashiCorp Vault client instance (vault credential mode). |
| `secrets` | dict | Loaded secrets keyed by path (config credential mode). |
| `fqdn` | str | Fully qualified domain name for the instance. |

**CLI flags** -- set from parsed arguments:

`target`, `name`, `ip`, `verbose`, `debug`, `list`, `on_error`, `log`, `logfile`, `force`, `keep`, `timestamp`, `dump_defs`, `dump_build`, `user_temp_dir`, `local_only`, `dry_run`, `user_defines`, `config_file`

### Initialization Sequence

1. `__init__()` calls `init_vars()` -- zeros all accumulator state
2. `__init__()` calls `init_settings(argv, which, extra_args)`:
   - Sets `settings` dict with hardcoded defaults (`base_dir` = package dir, `user_dir` = `~/.config/osimager`, etc.)
   - Builds argparse parser from `arg_base_defs` (always) and `arg_full_defs` (when `which="full"`)
   - Merges `extra_args` if provided (used by rfosimage)
   - Parses `argv`, stores results as instance attributes
   - Calls `load_settings()` to read `~/.config/osimager/osimager.conf` (INI format via `configparser`)
   - Applies `--set key=value` overrides; saves back to conf if any changed
   - Creates `~/.config/osimager/locations/` directory
   - Seeds `defs` with all settings values plus `base_path` alias

## Data Directory Layout

### Platforms (`data/platforms/`)

13 platform JSON files + `all.json`:

- `all.json` -- base defaults loaded for every build (common config keys, communicator settings)
- `vmware.json`, `vmware-vmx.json`, `virtualbox.json`, `qemu.json`, `libvirt.json`, `proxmox.json`, `vsphere.json`, `hyperv.json`, `xenserver.json` -- on-premise hypervisors
- `aws.json`, `azure.json`, `gcp.json` -- cloud platforms
- `none.json` -- null builder (no hypervisor)

Each platform file contains `config`, `defs`, `evars`, `variables`, `provisioners`, and optional `platform_specific` / `dist_specific` / `arch_specific` sections.

### Specs (`data/specs/`)

15 spec directories, each containing `spec.json`:

- **Distro families**: `alma/`, `centos/`, `debian/`, `esxi/`, `oel/`, `rhel/`, `rocky/`, `sles/`, `sysvr4/`, `ubuntu/`, `windows/`, `windows-server/`
- **Base specs**: `linux/` (common Linux config), `ssh/` (SSH communicator), `winrm/` (WinRM communicator)

Spec files declare `provides` (dist, versions with range syntax, architectures), `include` (inheritance chain), `version_specific` entries (regex-matched overrides), `required_files`, `files`, and all accumulator sections.

### Files (`data/files/`)

8 directories of installer templates: `debian/`, `esxi/`, `linux/`, `oel/`, `rhel/`, `sles/`, `ubuntu/`, `windows/`

Templates contain `>>var<<` markers and other substitution patterns. Assembled by `gen_files()` from `sources` lists in spec `files` entries.

### Tasks (`data/tasks/`)

21 Ansible task files for post-install provisioning:

- OS-family pairs: `RedHat_pre.yml`/`RedHat_post.yml`, `Debian_pre.yml`/`Debian_post.yml`, `Suse_pre.yml`/`Suse_post.yml`, `Windows_pre.yml`/`Windows_post.yml`, `Linux_pre.yml`/`Linux_post.yml`
- Platform-specific: `vsphere_post.yml`, `proxmox_pre.yml`, `gcp_post.yml`, `gcp_linux_post.yml`
- Utility: `spec.yml`, `local_repo.yml`, `rhel_6_config.yml`, `windows_updates.yml`, `copy_files_if.yml`, `include_role_if.yml`, `include_tasks_if.yml`

### Ansible Config (`data/ansible/`)

`config.yml` -- the main Ansible playbook referenced by the default provisioner. Invoked by Packer with extra-vars containing platform, location, spec, and install directory.

### Examples (`data/examples/`)

`quickstart-location.toml`, `example-location.json`, `example-location.toml`, `example-secrets`, `example-vault` -- reference files for user setup.

## User Configuration

All user-specific configuration lives outside the package at `~/.config/osimager/`:

| Path | Format | Purpose |
|---|---|---|
| `osimager.conf` | INI (configparser) | Persistent settings. Written only on `--set`. Section `[osimager]` with keys matching `settings` dict. |
| `locations/*.json` or `locations/*.toml` | JSON or TOML | User-created location files. JSON takes priority over TOML if both exist for same name. |
| `secrets` | Custom text | Credentials file for config mode. Format: `path key1=value1 key2=value2`. Lines starting with `#` are comments. |
| `specs/index.json` | JSON | Cached spec index. Created when `save_index=True`. Maps `dist-version-arch` keys to spec file paths and provides entries. |

## CLI Entry Points

Defined in `cli.py`, registered as console_scripts in `pyproject.toml`:

### mkosimage (`main_mkosimage`)

Primary build command. Flow:

1. `OSImager(argv, which="full")` -- parse args, load settings
2. If `--list`: call `get_index()`, print all specs with ISO availability flags, exit
3. If no target: print usage with platform/location discovery, exit
4. `make_build(target, name, ip)` -- load configs, resolve ISO, load credentials, perform substitutions, assemble Packer JSON
5. If `--dump-defs` or `--dump-config`: print and exit
6. `run_packer()` -- generate files, write build JSON, set environment, execute `packer build`

### rfosimage (`main_rfosimage`)

Re-provision command. Replaces the platform builder with a null builder, keeping only the communicator settings. Flow:

1. `OSImager(argv, "full", extra_args)` -- same init as mkosimage
2. `make_build()` -- full build assembly
3. Extract communicator type from `config`
4. Replace `builders[0]` with a `null` type builder that keeps only communicator-prefixed keys
5. `run_packer()` -- runs provisioners against existing VM

### mkvenv (`main_mkvenv`)

Virtual environment setup. Creates `OSImager(argv, which="venv")` which only runs initialization (settings load) without build logic.

## Config Loading Pipeline

The `make_build()` method loads configs in this order. Each layer can define `config`, `defs`, `evars`, `variables`, `files`, `pre_provisioners`, `provisioners`, `post_provisioners`. Layers merge additively (dicts update, lists extend) unless `method: "replace"` is specified.

1. **all.json** -- loaded implicitly as the base platform (via `include` in platform files, or as `all.json` in platforms dir)
2. **Platform** (`load_data_file("platforms", name)`) -- hypervisor-specific builder type, connection settings
3. **Location** (`load_data_file("locations", name)`) -- site-specific networking, storage paths, credentials references
4. **Spec** (`load_file("specs", path)`) -- OS-specific installer config, boot commands, ISO URLs

Each config file can use:
- `include` -- loads another spec first (string or list), creating inheritance chains (e.g., alma includes rhel)
- `*_specific` sections -- conditional overrides matched by regex against `platform`, `location`, `dist`, `version`, `arch`, `firmware`
- `method` -- `"merge"` (default) or `"replace"` to control how sections combine

## Template Substitution Engine

Defined in `utils.py`. Two core functions:

- `do_sub(item, inst)` -- recursively walks dicts, lists, tuples, sets, strings and applies substitution
- `do_substr(text, inst)` -- processes a single string through all ACTIONS

### ACTIONS Table

12 marker patterns, each with a numeric action ID and start/end delimiters:

| Action | Markers | Description |
|---|---|---|
| 1 | `%>..<%` | Replace complete value (including quotes) with defs variable |
| 2 | `>>..<<` | Replace marker with defs variable (most common) |
| 3 | `+>..<+` | Replace marker with basename of defs variable |
| 4 | `*>..<*` | Replace marker with IP address (DNS lookup) |
| 5 | `\|>..<\|` | Replace marker with secret value (vault or config) |
| 6 | `#>..<#` | Numeric eval (arithmetic on def values) |
| 7 | `$>..<$` | Replace marker with environment variable |
| 8 | `1>..<1` | MD5 password hash of secret value |
| 9 | `5>..<5` | SHA-256 password hash of secret value |
| 10 | `6>..<6` | SHA-512 password hash of secret value |
| 11 | `E>..<E` | Python eval of expression |
| 12 | `[>..<]` | Insert list items (expand list from defs) |

Actions are applied in order. For each action, `extract_all()` finds all tokens matching the start/end pattern, then `ACTION_HANDLERS[action]` produces the replacement value.

### Spec Index System

`make_index()` scans all spec files and builds a lookup table:
- Calls `spec_get_provides()` on each spec to expand version ranges into individual entries
- Version strings support `[0-7]` (range) and `[3,4,5]` (list) syntax via `explode_string_with_dynamic_range()`
- Filters by architectures supported by configured platforms and locations
- Keys are `dist-version-arch` strings (e.g., `alma-9.4-x86_64`)
- Values contain `provides` dict, spec `path`, and `iso_local` flag
- Optionally cached to `~/.config/osimager/specs/index.json`

## Credential System

Two modes, selected by `credential_source` setting:

### Vault Mode (`credential_source=vault`)

- Creates `hvac.Client` with `vault_addr` and `vault_token` from settings
- `get_secret("mount/path:key")` calls `vault.secrets.kv.v2.read_secret_version()`
- Packer natively resolves `{{vault ...}}` references via `VAULT_TOKEN` and `VAULT_ADDR` environment variables

### Config Mode (`credential_source=config`)

- Reads `~/.config/osimager/secrets` file
- Format: `path key1=value1 key2=value2` per line
- `get_secret("path:key")` looks up in the loaded `secrets` dict
- `resolve_packer_vault_refs()` replaces Packer `{{vault \`path\` \`key\`}}` syntax with values from the secrets dict before writing the build JSON

Actions 5, 8, 9, 10 all call `imager.get_secret()` which dispatches to the active credential source.

## Build Execution

`run_packer()` performs the final execution steps:

1. Changes working directory to `data/` (so relative paths in Ansible config resolve)
2. Calls `check_required_files()` -- verifies spec's `required_files` entries exist on disk
3. Calls `gen_files()` -- assembles installer files from template fragments, writes to temp directory
4. Writes the complete Packer build JSON to `{temp_dir}/{name}.json`
5. Sets environment variables from `evars` dict
6. Constructs packer command: optional venv activation, `packer build` with flags (`-timestamp-ui`, `-on-error`, `-force`, `-debug`)
7. Executes via `os.system()`
8. Cleans up temp directory unless `--keep` or `--temp` was specified

## Key Methods Overview

### Initialization
- `init_vars()` -- zero all accumulator state (vault, secrets, platform, location, spec, defs, evars, variables, provisioners, config, files, fqdn)
- `init_settings(argv, which, extra_args)` -- parse CLI args, load/save settings, create user dirs, seed defs
- `load_settings(config_path)` -- read `~/.config/osimager/osimager.conf` via configparser
- `save_settings(config_path)` -- write current settings to osimager.conf

### Data Loading
- `read_data(file_path)` -- load a JSON or TOML file based on extension
- `load_file(where, file_path)` -- read a data file, recursively process `include` chains, call `load_data()`
- `load_data_file(where, what)` -- resolve a logical name to a file path, then call `load_file()`
- `load_data(data)` -- merge a config dict's sections into instance accumulators (config, defs, evars, variables, files, provisioners), then process `*_specific` overrides
- `load_inc(where, what, data)` -- handle an include directive: load the included file, then apply current data on top
- `load_specific(data)` -- process `platform_specific`, `location_specific`, `dist_specific`, `version_specific`, `arch_specific`, `firmware_specific` sections using regex matching

### Index and Discovery
- `make_index()` -- scan all specs, expand version ranges, build dist-version-arch lookup table
- `get_index(name)` -- return cached or freshly built index, optionally filtered by name
- `spec_get_provides(file_name, data)` -- extract provides entries from a spec, expanding version ranges and per-version arch overrides
- `get_platforms(names)` -- list platform configs, optionally filtered by regex
- `get_locations(platform_names)` -- list location configs from user dir, optionally filtered by platform support
- `get_specs(search_string)` -- list spec configs, filtered by regex

### ISO and URL Handling
- `resolve_iso_url(data, version, arch)` -- best-effort resolve iso_url from spec defs with version/arch substitution
- `check_iso_local(iso_url)` -- check if ISO exists locally (file:// path or packer cache)
- `check_iso_urls(urls)` -- validate remote ISO URLs, download checksums, set defs
- `get_iso_file(urls)` -- resolve local ISO file path, set defs for local-only mode

### Credentials
- `load_credentials()` -- dispatch to vault or config mode initialization
- `load_secrets()` -- parse `~/.config/osimager/secrets` file
- `get_secret(string)` -- retrieve a secret value from vault or local secrets
- `resolve_packer_vault_refs(data)` -- replace `{{vault ...}}` references in Packer JSON with local secret values

### Build Assembly
- `make_build(target, name, ip)` -- full build pipeline: parse target, load platform/location/spec, resolve ISO, load credentials, perform substitutions, assemble final Packer JSON
- `gen_files()` -- assemble installer files from template fragments, write to temp directory
- `check_required_files()` -- verify all required_files from spec exist on disk
- `run_packer()` -- write build JSON, set environment, execute packer command

### Utility
- `version()` -- print and return version string
- `get_path(what, *paths)` -- resolve a settings key to an absolute path, join with optional sub-paths
