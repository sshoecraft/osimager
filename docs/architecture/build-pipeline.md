# OSImager Build Pipeline

Technical reference for the complete build pipeline executed when a user runs a command such as:

```
mkosimage vmware/lab/rhel-9.5-x86_64 myhost 192.168.1.100
```

All line numbers reference the source as of v1.3.0.

---

## Pipeline Overview

The build pipeline proceeds through these phases in order:

1. CLI parsing and OSImager initialization
2. Target parsing and index lookup
3. Platform loading
4. Location loading
5. Spec loading (recursive include chain)
6. Defs computation (networking, DNS, NTP, CIDR, FQDN, user overrides)
7. ISO resolution
8. Credential loading
9. Template substitution (`do_sub()` pass)
10. Installer file generation (`gen_files()`)
11. Required file check
12. Packer JSON assembly
13. Packer execution

---

## Step 1: CLI Parsing

**File:** `osimager/cli.py` lines 15-123
**Entry point:** `main_mkosimage()`

The console script entry point creates an `OSImager` instance with `which="full"`, which triggers full argument parsing including positional arguments (`target`, `name`, `ip`) and all build flags (`--force`, `--keep`, `--dry`, `--on_error`, `--define`, `--dump-defs`, `--dump-config`, `--temp`, `--local-only`).

```python
osimager = OSImager(argv=argv, which="full")
```

**File:** `osimager/core.py` lines 20-200
**Method:** `OSImager.__init__()` -> `init_vars()` -> `init_settings()`

`init_vars()` (line 29) zeroes all instance state: `vault`, `secrets`, `platform`, `location`, `spec`, `defs`, `evars`, `variables`, `pre_provisioners`, `provisioners`, `post_provisioners`, `config`, `files`, `fqdn`.

`init_settings()` (line 45) performs:
- Default settings initialization (line 48-61): `base_dir`, `user_dir`, `data_dir`, `packer_cmd`, `venv_dir`, `ansible_playbook`, `packer_cache_dir`, `local_only`, `save_index`, `credential_source`, `vault_addr`, `vault_token`
- argparse setup with base args and full args (lines 64-106)
- Positional argument extraction: `target`, `name`, `ip` (lines 120-127)
- Config file loading via `load_settings()` from `~/.config/osimager/osimager.conf` (line 156)
- `--set` overrides applied and persisted if changed (lines 160-189)
- `base_path` set from `base_dir` setting (line 192)
- User config directory `~/.config/osimager/locations/` created (line 194)
- All settings seeded into `self.defs` (line 196)

If `--list` is set, `main_mkosimage()` calls `get_index()` and prints available specs (cli.py lines 23-37), then returns.

If no target is provided, usage information and available platforms/locations are printed (cli.py lines 39-102).

Otherwise, the pipeline continues:

```python
build_config = osimager.make_build(osimager.target, name=osimager.name, ip=osimager.ip or "")
```

---

## Step 2: Parse Target

**File:** `osimager/core.py` lines 964-991
**Method:** `make_build(target, name, ip)`

The target string `vmware/lab/rhel-9.5-x86_64` is split on `/`:

```python
tuple = target.split('/')  # ['vmware', 'lab', 'rhel-9.5-x86_64']
```

If fewer than 3 parts, raises `ValueError`.

Extracts and stores:
- `platform_name` = `"vmware"` -> `self.defs['platform']`
- `location_name` = `"lab"` -> `self.defs['location']`
- `spec_name` = `"rhel-9.5-x86_64"`

**Index lookup** (lines 980-991): Calls `self.get_index(spec_name)` which either reads the cached index from `~/.config/osimager/specs/index.json` or builds it via `make_index()` (line 814-872). The index maps spec keys like `rhel-9.5-x86_64` to their spec file path and provides metadata.

From the index entry, extracts and stores in `self.defs`:
- `dist` = `"rhel"`
- `version` = `"9.5"`
- `arch` = `"x86_64"`

Sets `instance_name` = `name` if provided, else `spec_name` (line 993). For our example: `"myhost"`.

Initializes default Ansible environment variables (lines 999-1005):
```python
self.evars = {
    "ANSIBLE_RETRY_FILES_ENABLED": "False",
    "ANSIBLE_WARNINGS": "False",
    "ANSIBLE_NOCOWS": "1",
    "ANSIBLE_DISPLAY_SKIPPED_HOSTS": "False",
    "ANSIBLE_STDOUT_CALLBACK": "minimal"
}
```

Creates the default Ansible provisioner (lines 1010-1020) with template markers for `ansible_playbook`, `ansible_extra_args`, and `ansible_extra_vars`.

---

## Step 3: Load Platform

**File:** `osimager/core.py` line 1026
**Method:** `load_data_file("platforms", "vmware")`

Resolves to `<data_dir>/platforms/vmware.json`.

The VMware platform file includes `"all"`, triggering the recursive include mechanism:

### Include Chain for VMware Platform

`vmware.json` -> `include: "all"` -> `all.json`

**`all.json`** provides base hardware defaults:
```json
{ "defs": { "cpu_sockets": 1, "cpu_cores": 2, "memory": 2048, "boot_disk_size": 16385 } }
```

**`vmware.json`** adds VMware-specific builder config:
- `type`: `"vmware-iso"`
- `vm_name`, `output_directory`, `cpus`, `cores`, `memory`, `firmware`, `iso_url`, `disk_size`, `network_adapter_type`, etc.
- All values use template markers (`>>name<<`, `#>cpu_cores<#`, `E>...<E`) for deferred substitution.

The `load_data_file()` method (line 444) calls `load_file()` (line 421), which calls `read_data()` to parse JSON/TOML, then processes `include` keys recursively via `load_inc()` (line 404). Each level calls `load_data()` (line 315) which merges `files`, `evars`, `defs`, `variables`, `pre_provisioners`, `provisioners`, `post_provisioners`, and `config` into the OSImager instance. After merging, `load_specific()` (line 294) processes any `platform_specific`, `location_specific`, `dist_specific`, `version_specific`, `arch_specific`, and `firmware_specific` sections using `re.fullmatch()` against the current defs.

After loading, `platform_type` is extracted from `self.config['type']` (line 1030), yielding `"vmware-iso"` for the VMware platform.

---

## Step 4: Load Location

**File:** `osimager/core.py` line 1035
**Method:** `load_data_file("locations", "lab")`

Locations are loaded from `~/.config/osimager/locations/`. The method checks for `lab.json` first, then `lab.toml` (line 453-461).

A typical location file provides:
- `platforms`: list of supported platform names
- `defs`: network configuration (`cidr`, `gateway`, `domain`, `dns`, `ntp`, `iso_path`, `vms_path`, etc.)
- `platform_specific`: per-platform overrides (e.g., vSphere datacenter/cluster, Proxmox node settings)

After loading, `load_specific()` processes `platform_specific` entries, matching `vmware` against the current `platform` def. This is where platform-location intersection config (e.g., VMware datastore paths specific to a lab) gets merged.

Validation at lines 1053-1058 checks:
- Location supports the requested platform
- Spec supports the requested platform
- Spec supports the requested location

---

## Step 5: Load Spec

**File:** `osimager/core.py` lines 1039-1042

The spec path comes from the index entry (line 1039). For `rhel-9.5-x86_64`, this resolves to the full filesystem path of `specs/rhel/spec.json`.

```python
self.spec = self.load_file('specs', spec_path)
```

### Include Chain for RHEL Spec

The recursive include chain for RHEL is:

```
rhel/spec.json
  -> include: "linux"
     linux/spec.json
       -> include: "ssh"
          ssh/spec.json  (base — no further includes)
```

**Loading order** (deepest first due to recursion in `load_file()`, line 421):

1. **`ssh/spec.json`** -- Sets `config.communicator` = `"ssh"`, `ssh_host`, `ssh_port`, `ssh_username`, `ssh_password`, `ssh_timeout`. The `ssh_host` value uses a Python eval expression (`E>...<E`) that dynamically selects the SSH target based on `platform_type` and whether an IP was provided.

2. **`linux/spec.json`** -- Sets `defs.boot_disk_size` = 16384, `variables.ssh-username` and `variables.ssh-password` as Packer vault references (`{{vault \`images/linux\` \`username\`}}`).

3. **`rhel/spec.json`** -- The main RHEL spec. Loaded last so its values take precedence. Provides:
   - `provides` section (dist, versions, arches) -- used only for indexing
   - `platforms` list restricting supported platforms
   - `files` array defining kickstart generation: concatenation of `rhel/kickstart_>>major<<.cfg`, `rhel/ks-part.sh`, `rhel/kickstart_end.cfg`, `rhel/kickstart_post.cfg`, `rhel/install_vmwtools.sh`, `rhel/kickstart_end.cfg` -> output as `ks.cfg`
   - `defs`: `cd_files`, `cd_label` = `"OEMDRV"`, `ansible_extra_args`
   - `config`: `boot_wait`, `shutdown_command`
   - `version_specific` array with regex-matched overrides

**Version-specific processing** (via `load_specific()` at line 378): For version `9.5`, the `"9.*"` version_specific entry matches via `re.fullmatch("9.*", "9.5")`. This sets:
- `defs.cpu_cores` = 4, `defs.memory` = 4096
- `defs.spec_config` = `"specs/rhel/config_9.yml"`
- `defs.ansible_extra_vars` with python3 interpreter
- `defs.iso_url` with archive.org template
- Cloud provider image references (Azure, GCP, AWS)
- `config.firmware` = `"efi"`
- `config.boot_command` for EFI kickstart boot

**Platform-specific within version-specific**: The `9.*` entry also has `platform_specific` entries. The `vmware` match sets `defs.cpu_sockets` = 2, `config.guest_os_type` = `"rhel9-64"`, and merges `vmx_data` with `scsi0.virtualdev` = `"pvscsi"`.

After spec loading, venv activation is checked (lines 1047-1051) -- if the spec declares a `venv`, the PATH environment variable is modified to prioritize the venv bin directory.

---

## Step 6: Build Defs

**File:** `osimager/core.py` lines 1062-1178

### Spec Name Decomposition (lines 1062-1076)

The spec name `rhel-9.5-x86_64` is split on `-`:
- `dist` = `"rhel"`
- `version` = `"9.5"` -> `major` = `"9"`, `minor` = `"5"`
- `arch` = `"x86_64"`

### Boot/Shutdown Conditional Removal (lines 1078-1082)

If `defs.boot` is falsy, `boot_command` and `boot_wait` are removed from config.
If `defs.shutcmd` is falsy, `shutdown_command` is removed from config.

### Temp Directory (lines 1084-1089)

If `--temp` was specified, uses that directory. Otherwise creates a new `tempfile.mkdtemp()`.

### Core Defs Update (lines 1094-1106)

```python
self.defs.update({
    "base_path": ..., "data_path": ..., "user_dir": ...,
    "temp_dir": ..., "tmpdir": ..., "spec_dir": ...,
    "dist": ..., "version": ..., "major": ..., "minor": ..., "arch": ...
})
```

### Path Normalization (lines 1108-1112)

Strips trailing slashes from `iso_path` and `vms_path` defs so templates can append their own separators.

### Packer Variables (lines 1114-1119)

Sets `platform-name`, `location-name`, `spec-name`, `spec-config` in `self.variables` (these become Packer `{{user \`...\`}}` variables).

### DNS Expansion (lines 1121-1124)

Extracts `dns` dict from defs. Expands:
- `dns.search` list -> `dns_search` (space-joined string)
- `dns.servers` list -> `dns1`, `dns2`, `dns3`, ... (numbered individual entries)

### NTP Expansion (lines 1126-1128)

Extracts `ntp` dict. Expands `ntp.servers` list -> `ntp1`, `ntp2`, ...

### Instance Name and FQDN (lines 1130-1142)

- `defs.name` = instance_name (`"myhost"`)
- FQDN computation priority:
  1. `--fqdn` flag if specified
  2. If `name` contains a dot, use it as FQDN directly
  3. Otherwise: `instance_name + "." + defs['domain']`
- Sets both `defs.fqdn` and `variables.fqdn`

### CIDR Splitting (lines 1144-1159)

Splits `defs.cidr` (e.g., `"192.168.1.0/24"`) into:
- `subnet` = `"192.168.1.0"`
- `prefix` = `"24"`
- `gateway` = computed from last usable address if not explicitly set (`ipaddress.IPv4Network`)
- `gw` = alias for `gateway`
- `netmask` = converted from prefix via `prefix_to_netmask()` (e.g., `"255.255.255.0"`)

### IP Resolution (lines 1161-1165)

If no IP was provided on the command line, attempts DNS resolution via `get_ip(fqdn, location_dns_config)` using the location's DNS servers and search domains. Falls back to empty string.

For our example, IP = `"192.168.1.100"` (provided directly).

### User --define Overrides (lines 1167-1178)

If `--define` was used (e.g., `-D memory=8192,firmware=bios`), splits on commas, then on `=`, and overwrites `self.defs` entries. This allows command-line override of any def value.

---

## Step 7: Resolve ISOs

**File:** `osimager/core.py` lines 1183-1201

Checks `defs.urls` (array of `{url, checksum}` dicts). Runs `do_sub()` on the URLs first to resolve any template markers.

Two modes based on `local_only` setting:

- **Local mode** (`get_iso_file()`, line 892-921): Takes the first URL entry, extracts `iso_name` and `iso_path` for local filesystem access. Sets `defs.iso_file`, `defs.iso_name`, `defs.iso_checksum` = `"none"`. Removes `iso_urls` from config.

- **Remote mode** (`check_iso_urls()`, line 923-962): Iterates URL entries, performs HTTP HEAD checks (`check_url()`), downloads checksum files (`get_checksum()`), and sets `defs.iso_url`, `defs.iso_name`, `defs.iso_checksum`.

If `iso_url` is defined but `iso_name` is not, derives `iso_name` from the URL via `get_filename_from_url()` (lines 1193-1201).

---

## Step 8: Load Credentials

**File:** `osimager/core.py` lines 547-583, called at line 1204
**Method:** `load_credentials()`

Dispatches based on `credential_source` setting:

### Vault Mode (`credential_source` = `"vault"`)

Lines 556-583. Reads `vault_addr` and `vault_token` from settings. Creates `hvac.Client` (line 571). Verifies authentication via `vault.is_authenticated()`. If successful, stores `vault_addr` and `vault_token` in defs for later use as environment variables.

### Config Mode (`credential_source` = `"config"`)

Calls `load_secrets()` (lines 507-545). Parses `~/.config/osimager/secrets` file. Format:
```
path key1=value1 key2=value2
```
Example:
```
images/linux username=root password=T3mp@dm1n!
vsphere/lab server=vcenter.local username=admin password=P@ss
```

Populates `self.secrets` dict keyed by path.

### Credential Error Handling (lines 1203-1215)

If credential loading fails, checks whether the configuration actually references secrets (vault template functions `{{vault ...}}`, or substitution markers `|>`, `6>`, `5>`). Only aborts if secrets are actually needed.

---

## Step 9: Template Substitution

**File:** `osimager/core.py` lines 1222-1237
**File:** `osimager/utils.py` lines 301-846

The `do_sub()` function is the core template engine. It recursively walks all data structures (dicts, lists, tuples, sets, strings) and delegates string processing to `do_substr()`.

### Substitution Pass Order (line 1222-1237)

```python
self.defs = do_sub(self.defs, self)           # Resolve defs against themselves
self.evars = do_sub(self.evars, self)         # Resolve environment variables
self.variables = do_sub(self.variables, self)  # Resolve Packer variables
# Provisioner assembly:
provisioners = []
provisioners.extend(do_sub(self.pre_provisioners, self))
provisioners.extend(do_sub(self.provisioners, self))
provisioners.extend(do_sub(self.post_provisioners, self))
self.spec['files'] = do_sub(self.spec.get("files", []), self)
self.config = do_sub(self.config, self)
```

### Template Marker Types

Defined in `ACTIONS` (utils.py lines 698-711):

| Action | Markers | Purpose | Example |
|--------|---------|---------|---------|
| 1 | `%>..<%` | Replace complete value (including quotes) with defs variable | `%>cd_files<%` |
| 2 | `>>..<<` | Replace marker inline with defs variable | `>>version<<` -> `9.5` |
| 3 | `+>..<+` | Replace with basename of defs variable | `+>iso_path<+` |
| 4 | `*>..<*` | Replace with IP address (DNS lookup) | `*>hostname<*` |
| 5 | `\|>..<\|` | Replace with HashiCorp Vault / secrets value | `\|>images/linux:password<\|` |
| 6 | `#>..<#` | Numeric eval (arithmetic on def values) | `#>cpu_sockets*cpu_cores<#` |
| 7 | `$>..<$` | Replace with environment variable | `$>HOME<$` |
| 8 | `1>..<1` | MD5 password hash of secret | `1>images/linux:password<1` |
| 9 | `5>..<5` | SHA-256 password hash of secret | `5>images/linux:password<5` |
| 10 | `6>..<6` | SHA-512 password hash of secret | `6>images/linux:password<6` |
| 11 | `E>..<E` | Python eval expression | `E>'efi' if ... else 'bios'<E` |
| 12 | `[>..<]` | Insert list items (expand list into parent) | `[>ansible_extra_args<]` |

### Processing Flow (`do_substr()`, utils.py lines 796-846)

For each string, iterates through all 12 action types. For each action, `extract_all()` finds all tokens matching the start/end markers. The corresponding `ACTION_HANDLER` (lines 683-696) is invoked to produce the replacement value. If the entire string is a single marker, the replacement can be a non-string type (dict, list, int); otherwise string substitution is performed.

---

## Step 10: Generate Installer Files

**File:** `osimager/core.py` lines 1300-1334
**Method:** `gen_files()`

Called from `run_packer()` (line 1350). Processes `self.files` (populated from the spec's `files` array during loading).

For RHEL 9.5, the files array specifies kickstart generation:
```json
{
    "sources": [
        "rhel/kickstart_9.cfg",
        "rhel/ks-part.sh",
        "rhel/kickstart_end.cfg",
        "rhel/kickstart_post.cfg",
        "rhel/install_vmwtools.sh",
        "rhel/kickstart_end.cfg"
    ],
    "dest": "ks.cfg"
}
```

For each file entry:
1. Iterates `sources` array
2. Each source path is resolved relative to `<data_dir>/files/`
3. Source file contents are read and concatenated into a single `data` string
4. `do_substr(data, self)` performs template substitution on the concatenated content
5. Result is written to `<temp_dir>/<dest>` (e.g., `/tmp/tmpXXXXXX/ks.cfg`)

The generated kickstart file contains the fully resolved network config, partition layout, package lists, and post-install scripts with all `>>variable<<` markers replaced by actual values.

---

## Step 11: Check Required Files

**File:** `osimager/core.py` lines 1268-1298
**Method:** `check_required_files()`

Called from `run_packer()` at line 1347. Reads the `required_files` array from the spec (if present). Each entry has:
- `file`: relative path under `<data_dir>/files/`
- `description`: human-readable description
- `url`: download URL
- `location`: where to place the file

Performs `do_sub()` on each entry, checks `os.path.exists()`. If any file is missing, prints download instructions and calls `sys.exit(1)`.

Most RHEL builds do not have `required_files`. ESXi specs use this for VIB files that must be manually downloaded.

---

## Step 12: Assemble Packer JSON

**File:** `osimager/core.py` lines 1248-1264

The final Packer build structure is assembled:

```python
self.build = {
    "variables": self.variables,
    "provisioners": provisioners,
    "builders": [ self.config ]
}
```

### Variables

Contains Packer user variables referenced by `{{user \`...\`}}` in builders/provisioners:
- `platform-name`, `location-name`, `spec-name`, `spec-config`
- `ssh-username`, `ssh-password` (vault references or resolved values)
- `name`, `fqdn`

### Provisioners

Ordered list: `pre_provisioners` + `provisioners` + `post_provisioners`. The default provisioner is an Ansible provisioner running the playbook specified by `ansible_playbook` with extra vars for platform, location, spec, and install directory.

### Builders

Single-element array containing `self.config` -- the fully resolved builder configuration. For VMware, this is a `vmware-iso` builder with all VM parameters, ISO paths, boot commands, and VMX data.

### Vault Reference Resolution (lines 1254-1256)

If using config-based secrets (`self.secrets` is populated), `resolve_packer_vault_refs()` (lines 612-634) walks the entire build structure and replaces Packer `{{vault \`path\` \`key\`}}` references with actual values from the secrets dict. This allows the same spec files to work with both Vault and local secrets.

### Dump and Exit Points (lines 1258-1264)

- `--dump-defs` (`-x`): prints `self.defs` as JSON and exits
- `--dump-config` (`-u`): prints `self.build` as JSON and exits

These are diagnostic tools for inspecting the resolved state without running Packer.

---

## Step 13: Execute Packer

**File:** `osimager/core.py` lines 1336-1416
**Method:** `run_packer()`

Called from `main_mkosimage()` at cli.py line 113.

### Directory Change (lines 1338-1344)

Changes working directory to `data_path` so that relative paths in config files (e.g., `config.yml`, Ansible roles) resolve correctly.

### File Generation and Validation (lines 1347-1350)

Calls `check_required_files()` then `gen_files()` (described in steps 10-11 above).

### Write Packer JSON (lines 1352-1356)

Writes the assembled build structure to `<temp_dir>/<instance_name>.json`:
```python
output_file = os.path.join(self.defs.get("tmpdir", "/tmp"), self.defs.get("name", "build") + ".json")
json.dump(self.build, fp, indent=4)
```

For our example: `/tmp/tmpXXXXXX/myhost.json`

### Set Environment Variables (lines 1358-1372)

All entries in `self.evars` are exported:
- Ansible control variables (`ANSIBLE_RETRY_FILES_ENABLED`, `ANSIBLE_WARNINGS`, etc.)
- `RES_OPTIONS` for DNS resolution during build
- `PATH` (if venv is active)

If Vault is configured:
- `VAULT_TOKEN` and `VAULT_ADDR` are exported (lines 1365-1368)

If logging is enabled:
- `PACKER_LOG` = `"1"` (line 1370)
- `PACKER_LOG_PATH` = logfile path (line 1372)

### Build Command Assembly (lines 1374-1404)

```python
cmd = []
```

If a venv is specified in the spec, prepends the activation command:
```
. ~/.venv/<venv_name>/bin/activate &&
```

Then appends the Packer command:
```
packer build [-timestamp-ui] [-on-error=<mode>] [-force] [-debug] <output_file>
```

Flag mapping:
- `--timestamp` -> `-timestamp-ui`
- `--on_error <mode>` -> `-on-error=<mode>`
- `--keep` -> `-on-error=abort`
- `--force` -> `-force`
- `--debug` -> `-debug`

### Execution (lines 1406-1412)

If not `--dry_run`, ensures CWD is `data_path` and calls:
```python
os.system(cmd_str)
```

Uses `os.system()` for direct shell execution, allowing Packer's interactive output (progress bars, prompts) to pass through to the terminal.

### Cleanup (lines 1414-1415)

If `--temp` was not specified and `--keep` was not set, removes the temp directory:
```python
shutil.rmtree(self.temp_dir)
```

---

## rfosimage Flow

**File:** `osimager/cli.py` lines 126-185
**Entry point:** `main_rfosimage()`

The `rfosimage` (refit OS image) command shares the entire pipeline through step 12, then modifies the builder before execution.

### Shared Pipeline

```python
img = OSImager(argv, "full", extra_args)
build = img.make_build(plan, name, ip)
```

All steps 1-12 execute identically.

### Builder Replacement (lines 153-173)

After `make_build()` returns, `rfosimage` replaces the platform-specific builder with a `null` builder. This skips VM creation/ISO boot and instead connects directly to an existing machine via its communicator (SSH/WinRM).

```python
config = builders[0]
comm = config.get('communicator', None)  # e.g., "ssh"

new_config = {
    "name": defs.get("spec_name", "name"),
    "type": "null"
}
# Copy only communicator-related keys (ssh_host, ssh_port, ssh_username, etc.)
for key in config:
    if key.startswith(comm):  # keys starting with "ssh" for SSH communicator
        new_config[key] = config[key]
```

This preserves `ssh_host`, `ssh_port`, `ssh_username`, `ssh_password`, `ssh_timeout`, etc., while discarding all builder-specific config (ISO, boot commands, VM hardware, disk settings).

The spec's `files` section is also removed (line 153-154) since installer files are not needed for refitting.

### Execution

Calls `img.run_packer()` which writes the null-builder JSON and executes Packer. Packer connects to the existing host and runs only the provisioners (Ansible playbook, shell scripts).

---

## Data Flow Diagram

```
CLI args
  |
  v
OSImager.__init__()
  |-- init_vars()        -> zero state
  |-- init_settings()    -> parse args, load settings, seed defs
  |
  v
make_build(target, name, ip)
  |
  |-- split target       -> platform_name, location_name, spec_name
  |-- get_index()        -> dist, version, arch
  |
  |-- load_data_file("platforms", ...)
  |     |-- all.json     -> base defs (cpu, memory, disk)
  |     |-- vmware.json  -> builder config (vmware-iso type)
  |
  |-- load_data_file("locations", ...)
  |     |-- lab.json     -> network defs (cidr, dns, ntp, domain)
  |     |-- platform_specific for vmware
  |
  |-- load_file("specs", ...)
  |     |-- ssh/spec.json   -> communicator config
  |     |-- linux/spec.json -> boot_disk_size, vault variables
  |     |-- rhel/spec.json  -> files, boot_command, version_specific
  |           |-- version_specific "9.*" match
  |           |-- platform_specific "vmware" match
  |
  |-- compute defs       -> major, minor, DNS, NTP, CIDR, FQDN, IP
  |-- user --define      -> override defs
  |-- resolve ISOs       -> iso_url, iso_name, iso_checksum
  |-- load_credentials() -> vault client or local secrets
  |
  |-- do_sub() pass      -> resolve all template markers
  |-- assemble build     -> { variables, provisioners, builders }
  |-- resolve_packer_vault_refs() if config mode
  |
  v
run_packer()
  |-- chdir(data_path)
  |-- check_required_files()
  |-- gen_files()        -> write ks.cfg to temp_dir
  |-- write JSON         -> temp_dir/myhost.json
  |-- set env vars       -> ANSIBLE_*, VAULT_*, PATH
  |-- os.system("packer build ... myhost.json")
  |-- cleanup temp_dir
```

---

## Key Source File Reference

| File | Lines | Purpose |
|------|-------|---------|
| `osimager/cli.py` | 15-123 | `main_mkosimage()` entry point |
| `osimager/cli.py` | 126-185 | `main_rfosimage()` entry point |
| `osimager/core.py` | 20-200 | `__init__()`, `init_vars()`, `init_settings()` |
| `osimager/core.py` | 294-378 | `load_specific()`, `load_data()` -- config merging |
| `osimager/core.py` | 404-469 | `load_inc()`, `load_file()`, `load_data_file()` -- recursive include loading |
| `osimager/core.py` | 507-545 | `load_secrets()` -- parse local secrets file |
| `osimager/core.py` | 547-583 | `load_credentials()` -- vault or config dispatch |
| `osimager/core.py` | 585-610 | `get_secret()` -- unified secret access |
| `osimager/core.py` | 612-634 | `resolve_packer_vault_refs()` -- replace `{{vault ...}}` in build JSON |
| `osimager/core.py` | 814-872 | `make_index()` -- build spec index from all spec files |
| `osimager/core.py` | 892-962 | `get_iso_file()`, `check_iso_urls()` -- ISO resolution |
| `osimager/core.py` | 964-1266 | `make_build()` -- main build orchestration |
| `osimager/core.py` | 1268-1298 | `check_required_files()` |
| `osimager/core.py` | 1300-1334 | `gen_files()` -- installer file generation |
| `osimager/core.py` | 1336-1416 | `run_packer()` -- write JSON, set env, execute |
| `osimager/utils.py` | 78-113 | `explode_string_with_dynamic_range()` -- version range expansion |
| `osimager/utils.py` | 219-227 | `prefix_to_netmask()` -- CIDR prefix to dotted netmask |
| `osimager/utils.py` | 229-250 | `get_ip()` -- DNS resolution with custom servers |
| `osimager/utils.py` | 301-334 | `do_sub()` -- recursive template substitution |
| `osimager/utils.py` | 543-582 | `hash_password()` -- crypt-compatible password hashing |
| `osimager/utils.py` | 683-711 | `ACTION_HANDLERS`, `ACTIONS` -- substitution marker definitions |
| `osimager/utils.py` | 796-846 | `do_substr()` -- per-string template processing |
| `osimager/constants.py` | 10 | `OSIMAGER_VERSION` -- single source of truth for version |
