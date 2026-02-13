# CLI Reference

OSImager provides three command-line tools installed as console scripts via pip.

---

## mkosimage

The primary build command. Assembles a Packer build configuration from platform, location, and spec files, then executes it.

### Synopsis

```
mkosimage [OPTIONS] PLATFORM/LOCATION/SPEC [NAME] [IP]
```

### Positional Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `PLATFORM/LOCATION/SPEC` | Yes (for builds) | Target triple specifying the platform, location, and spec to build. Example: `vmware/lab/rhel-9.5-x86_64` |
| `NAME` | No | Hostname for the built VM. Defaults to the spec name if omitted. |
| `IP` | No | Static IP address for the built VM. If omitted, OSImager attempts DNS resolution of the hostname. |

### Options

#### General

| Flag | Long Form | Description |
|------|-----------|-------------|
| `-V` | `--version` | Print the OSImager version and exit. |
| `-l` | `--list` | List all available specs. Specs with a local ISO in your `iso_path` are marked with `*`. |
| `-a` | `--avail` | List only specs that have a matching local ISO present. |
| | `--list-platforms` | List all available platforms with their Packer builder type and supported architectures. |
| | `--list-defs` | List all available defs (template variables) with their default values and sources. Shows base defaults, platform defs, and computed defs. |
| `-d` | `--debug` | Enable debug output. Prints internal variable resolution, file loading paths, and Packer debug flag. |
| `-v` | `--verbose` | Enable verbose output. Prints loaded settings, file paths, and environment variables as they are set. |
| `-c` | `--config` | Path to the osimager.conf configuration file. Default: `osimager.conf` (resolved in `~/.config/osimager/`). |

#### Build Control

| Flag | Long Form | Description |
|------|-----------|-------------|
| `-n` | `--dry` | Dry run. Builds the full Packer JSON configuration but does not execute `packer build`. Prints the command that would be run. |
| `-f` | | Force rebuild. Passes `-force` to Packer, which causes it to delete and re-create any existing output artifacts. |
| `-k` | | Keep temp files and VMs on error. Sets Packer's `-on-error=abort` so the VM is not destroyed if the build fails, allowing inspection. |
| `-e` | `--on_error` | Set Packer's on-error behavior explicitly. Valid values: `cleanup` (default Packer behavior), `abort`, `ask`. Overrides `-k`. |
| `-t` | | Enable Packer's timestamp UI (`-timestamp-ui`), which prefixes each output line with a timestamp. |
|      | `--local-only` | Restrict builds to local ISOs only. Specs without a matching local ISO will fail instead of attempting a download. This setting is persisted to `osimager.conf`. |
| `-m` | `--temp` | Specify a custom temp directory for build artifacts. By default, OSImager creates a temporary directory in `/tmp` and cleans it up after the build (unless `-k` is set). |

#### Output and Debugging

| Flag | Long Form | Description |
|------|-----------|-------------|
| `-x` | `--defs` | Dump the fully resolved defs dictionary and exit. Shows all merged variables from platform, location, and spec configs after template substitution. |
| `-u` | `--dump` | Dump the complete Packer build JSON and exit. Useful for inspecting the exact configuration that would be sent to Packer. |
| `-L` | | Enable Packer logging. Sets the `PACKER_LOG=1` environment variable. |
| `-N` | `--logfile` | Path for Packer log output. Sets `PACKER_LOG_PATH` to this value. Only meaningful when `-L` is also set. |

#### Customization

| Flag | Long Form | Description |
|------|-----------|-------------|
| `-F` | `--fqdn` | Override the auto-generated FQDN. By default, OSImager constructs the FQDN from the hostname and the location's `domain` setting. |
| `-D` | `--define` | Define custom defs as a comma-separated list of `KEY=VALUE` pairs. These override any values from platform, location, or spec configs. |

#### Persistent Settings

| Flag | Description |
|------|-------------|
| `--set KEY=VALUE` | Set a persistent configuration value in `~/.config/osimager/osimager.conf`. Can be specified multiple times. Only saves if the value actually changes. |

The following keys are accepted by `--set`:

| Key | Default | Description |
|-----|---------|-------------|
| `credential_source` | `vault` | Credential backend: `vault` (HashiCorp Vault) or `config` (local secrets file). |
| `vault_addr` | _(empty)_ | HashiCorp Vault server URL (e.g. `http://vault.example.com:8200`). |
| `vault_token` | _(empty)_ | HashiCorp Vault access token. |
| `packer_cmd` | `packer` | Path to the Packer binary. |
| `packer_cache_dir` | `/tmp` | Directory for Packer's ISO download cache. |
| `local_only` | `False` | When `True`, only use local ISOs; never attempt downloads. |
| `data_dir` | `data` | Path to the OSImager data directory (relative to package or absolute). |
| `save_index` | `False` | When `True`, cache the spec index to `~/.config/osimager/specs/index.json`. |
| `ansible_playbook` | `config.yml` | Name of the Ansible playbook used during provisioning. |

---

## rfosimage

Re-provisions an existing VM using Ansible without rebuilding from an ISO. Replaces the Packer builder with a `null` builder, keeping only the communicator configuration and provisioners.

### Synopsis

```
rfosimage [OPTIONS] PLATFORM/LOCATION/SPEC [NAME] [IP]
```

### How It Differs from mkosimage

`rfosimage` runs the same configuration merge pipeline as `mkosimage` (platform + location + spec), but before executing Packer it:

1. Removes any `files` section from the spec (no file generation needed).
2. Extracts the communicator type and settings (e.g. SSH host, user, password) from the original builder.
3. Replaces the builder with a Packer `null` builder that only connects to the target via the communicator.
4. Runs the provisioners (typically Ansible) against the existing VM.

This means the VM must already exist and be reachable at the specified hostname/IP.

### When to Use

- Re-running Ansible provisioning after changing a spec's Ansible playbook or roles.
- Applying configuration updates to an already-built VM.
- Testing Ansible provisioner changes without waiting for a full OS install.

### Arguments and Options

`rfosimage` accepts the same positional arguments and options as `mkosimage`. The `NAME` and `IP` arguments are typically required since the target VM must be reachable.

!!! note
    The target VM must be running and accessible via the communicator (SSH or WinRM) defined in the platform config. If the VM was built with `mkosimage`, the same credentials configured in your secrets will be used.

---

## mkvenv

Creates a Python virtual environment for Ansible version pinning. Some older OS distributions require specific Ansible versions that differ from what is installed system-wide.

### Synopsis

```
mkvenv [OPTIONS]
```

### Purpose

Certain specs include a `venv` key that references a named virtual environment. When `mkosimage` encounters a spec with a `venv` value, it activates that virtual environment before running Packer, ensuring the correct Ansible version is on the `PATH`.

`mkvenv` creates and configures these virtual environments in the venv directory (`~/.venv/` by default).

### Options

`mkvenv` accepts the base options shared with all OSImager commands:

| Flag | Long Form | Description |
|------|-----------|-------------|
| `-V` | `--version` | Print the OSImager version and exit. |
| `-l` | `--list` | List available specs. |
| `-a` | `--avail` | List only specs with local ISOs. |
| `-d` | `--debug` | Enable debug output. |
| `-v` | `--verbose` | Enable verbose output. |
| `-c` | `--config` | Path to osimager.conf. |
|      | `--set KEY=VALUE` | Set a persistent configuration value. |

---

## Examples

### Listing

```bash
# List all available specs (* marks those with local ISOs)
mkosimage --list

# List only specs with local ISOs
mkosimage --avail

# List all available platforms with builder type and architectures
mkosimage --list-platforms

# List all available defs with defaults and sources
mkosimage --list-defs
```

### Building Images

```bash
# Build with VirtualBox (hostname defaults to spec name, IP via DNS)
mkosimage virtualbox/local/alma-9.5-x86_64

# Build with explicit hostname and IP
mkosimage vmware/lab/rhel-9.5-x86_64 myhost 192.168.1.100

# Build with a custom FQDN
mkosimage -F myhost.custom.domain vmware/lab/rhel-9.5-x86_64 myhost 192.168.1.100

# Force rebuild, deleting any existing artifacts
mkosimage -f vmware/lab/rhel-9.5-x86_64 myhost
```

### Debugging and Inspection

```bash
# Dry run -- show the Packer command without executing it
mkosimage -n vmware/lab/rhel-9.5-x86_64 myhost 192.168.1.100

# Dump the resolved defs dictionary
mkosimage -x vmware/lab/rhel-9.5-x86_64 myhost 192.168.1.100

# Dump the Packer build JSON
mkosimage -u vmware/lab/rhel-9.5-x86_64 myhost 192.168.1.100

# Enable verbose and debug output together
mkosimage -v -d vmware/lab/rhel-9.5-x86_64 myhost 192.168.1.100
```

### Overriding Defs

```bash
# Override memory and CPU settings
mkosimage -D memory=4096,cpu_cores=4 vmware/lab/rhel-9.5-x86_64

# Override multiple values for a custom build
mkosimage -D memory=8192,cpu_cores=8,disk_size=51200 vmware/lab/rhel-9.5-x86_64 bighost
```

### Packer Logging

```bash
# Enable Packer logging to a file
mkosimage -L -N /tmp/packer.log vmware/lab/rhel-9.5-x86_64 myhost

# Keep VM on error for inspection
mkosimage -k vmware/lab/rhel-9.5-x86_64 myhost 192.168.1.100

# Explicit on-error behavior
mkosimage -e ask vmware/lab/rhel-9.5-x86_64 myhost 192.168.1.100
```

### Re-provisioning

```bash
# Re-run Ansible provisioning on an existing VM
rfosimage vmware/lab/rhel-9.5-x86_64 myhost 192.168.1.100

# Dry run re-provisioning to see what would execute
rfosimage -n vmware/lab/rhel-9.5-x86_64 myhost 192.168.1.100
```

### Persistent Configuration

```bash
# Switch to local secrets file mode
mkosimage --set credential_source=config

# Configure Vault
mkosimage --set vault_addr=http://vault.example.com:8200
mkosimage --set vault_token=hvs.your-token-here

# Use a custom Packer binary
mkosimage --set packer_cmd=/usr/local/bin/packer

# Restrict to local ISOs only
mkosimage --set local_only=True
```

---

## Exit Codes

| Code | Constant | Meaning |
|------|----------|---------|
| 0 | `EXIT_SUCCESS` | Command completed successfully. |
| 1 | `EXIT_GENERAL_ERROR` | General error (build failure, missing spec, invalid arguments). |
| 2 | `EXIT_MISUSE` | Command misuse (invalid argument combinations). |
| 3 | `EXIT_CONFIG_ERROR` | Configuration error (missing or invalid config files). |
| 4 | `EXIT_NETWORK_ERROR` | Network error (DNS resolution failure, unreachable host). |
| 5 | `EXIT_PERMISSION_ERROR` | Permission error (insufficient access to files or directories). |

---

## Configuration File

All three commands read settings from `~/.config/osimager/osimager.conf`, an INI-format file with an `[osimager]` section:

```ini
[osimager]
credential_source = config
packer_cmd = packer
packer_cache_dir = /tmp
local_only = False
data_dir = data
save_index = False
ansible_playbook = config.yml
```

Settings are loaded in this order (later overrides earlier):

1. Built-in defaults in the OSImager source.
2. Values from `~/.config/osimager/osimager.conf`.
3. Command-line `--set` overrides (which also persist back to the conf file).
4. Command-line flags (e.g. `--local-only`, `-d`, `-v`).
