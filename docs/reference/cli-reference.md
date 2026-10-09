# CLI Reference

OSImager installs three commands: `mkosimage` builds images, `rfosimage` re-runs provisioning on an existing VM, and `mkvenv` manages the Ansible virtual environments that specs require.

---

## mkosimage

Assembles a Packer build from a platform, a location and a spec, then runs it. Without a target it answers questions instead: what specs exist, what you can build, and how things are configured.

### Synopsis

```
mkosimage [OPTIONS] PLATFORM/LOCATION/SPEC [NAME] [IP]
mkosimage [LISTING OPTIONS]
```

### Positional Arguments

| Argument | Description |
|----------|-------------|
| `PLATFORM/LOCATION/SPEC` | What to build. `PLATFORM` is a file in `platforms/` (e.g. `proxmox`), `LOCATION` is a file in your `locations/` (e.g. `pve`), `SPEC` is `<dist>-<version>-<arch>` (e.g. `alma-9.8-x86_64`). Example: `proxmox/pve/alma-9.8-x86_64`. |
| `NAME` | Hostname of the VM. Defaults to the spec name. Its FQDN is `NAME.<location domain>`, unless `NAME` already contains a dot, in which case it is the FQDN. |
| `IP` | Static IP for the VM. If omitted, the FQDN is looked up in the location's DNS servers; if it resolves, that address is used as a static IP, otherwise the VM uses DHCP. |

#### Latest targets

In place of a version, `SPEC` can be `<dist>-latest-<arch>`, e.g. `alma-latest-x86_64`. It resolves to the highest version the specs provide for that dist and architecture, and the resolution is printed (`alma-latest-x86_64 -> alma-10.2-x86_64`). Everything after that, including the default VM name, uses the real version.

With `--local`, `latest` means the newest version whose ISO is already present. If none is present, the build stops with an error.

`latest` reflects the specs, not the vendor's site: a new upstream release only appears once a spec is updated for it.

### Listing Options

These print information and exit. They need no target.

| Flag | What it prints |
|------|----------------|
| `-l`, `--list` | Every spec OSImager knows about, one per line in version order, whether or not you can build it. A `(*)` after a name means its ISO is present locally. |
| `-a`, `--avail` | Only the specs you can build right now, one per line, with where the ISO comes from: a local path if the ISO is present, otherwise the download URL. Specs that are local-only and whose ISO is missing are not listed. |
| `--local` | With no target: the same list as `-a`, but only the specs whose ISO is present (path entries only). With a target: see Build Options. |
| `--latest` | Each `<dist>-latest-<arch>` target and the spec it resolves to. Combined with `-a` or `--local`, those lists are narrowed to the latest spec of each dist. With `--local`, latest means the newest version present locally. |
| `--arch ARCH` | Filter any of the lists above to one architecture, e.g. `--arch aarch64`. |
| `--check-urls` | HEAD-checks every download URL in every spec, in parallel, and prints each failure with its HTTP status, then totals of OK, failed and local-only. |
| `--list-platforms` | Each platform with its Packer builder type and supported architectures. |
| `--list-defs` | Every def (template variable) with its default value and where it comes from. |
| `--show-config` | The settings in effect, as loaded from `config.json`. |
| `--init-plugins` | Runs `packer plugins install` for the plugin each platform needs, plus the Ansible provisioner plugin, every time (installed plugins are not skipped). |
| `-V`, `--version` | The OSImager version. |

"Present locally" means the file exists on the machine running OSImager: at the spec's `file://` path, or as `<iso_path>/<ISO file name>` for a download URL.

### Build Options

| Flag | Effect |
|------|--------|
| `--local`, `--local-only` | Build only from an ISO that is already present; never download. If the ISO is missing, the build fails. Applies to this run only. |
| `-n`, `--dry` | Do everything except run Packer: resolve the config, generate the answer files, write the build JSON and print the `packer build` command. |
| `-f` | Pass `-force` to Packer, which replaces an existing VM or output with the same name. |
| `-k` | Keep things around for debugging: pass `-on-error=abort` to Packer so a failed VM is not destroyed, and keep the temporary build directory. |
| `-e`, `--on_error MODE` | Pass `-on-error=MODE` to Packer (`cleanup`, `abort` or `ask`). Takes precedence over `-k` for Packer's behavior. |
| `--skip` | Skip post-install configuration: no Ansible run, and no Ansible venv required. |
| `-m`, `--temp DIR` | Use `DIR` for the generated files instead of a new temporary directory. It is not deleted afterwards. |
| `-t` | Pass `-timestamp-ui` to Packer, so each output line is timestamped. |
| `--dispatcher` | Print machine-readable progress lines (`PROGRESS=`, `ERROR=`, `RESULT=`) for a controlling program. |

### Customization Options

| Flag | Effect |
|------|--------|
| `-D`, `--define K=V[,K=V...]` | Set defs for this build, overriding the platform, location and spec. Comma-separated, e.g. `-D memory=4096,cpu_cores=4`. |
| `-F`, `--fqdn FQDN` | Use this FQDN instead of the one derived from `NAME`. |

### Output and Debugging Options

| Flag | Effect |
|------|--------|
| `-x`, `--defs` | Print the fully resolved defs as JSON and exit without building. |
| `-u`, `--dump` | Print the complete Packer build JSON and exit without building. |
| `-v`, `--verbose` | Print what OSImager is doing: settings loaded, files read, environment variables set. |
| `-d`, `--debug` | Print internal resolution detail, and pass `-debug` to Packer (which pauses between steps). |
| `-L` | Set `PACKER_LOG=1` so Packer writes its detailed log. |
| `-N`, `--logfile FILE` | Set `PACKER_LOG_PATH=FILE`, so Packer's log goes to that file. Only useful with `-L`. |

### Settings

| Flag | Effect |
|------|--------|
| `--set KEY=VALUE` | Change a setting **and save it** to `~/.config/osimager/config.json`. Repeatable. The new value applies to this run and every run after it. If `--local` is given in the same command, `local_only=true` is saved too. |

To run against a different set of settings, locations and secrets, point `XDG_CONFIG_HOME` at another directory: OSImager then reads `$XDG_CONFIG_HOME/osimager/`.

Settings that are saved to `config.json`:

| Key | Default | Meaning |
|-----|---------|---------|
| `iso_path` | `/iso` | Directory on this machine holding ISOs. Downloaded ISOs are saved here, and spec `file://` URLs and the "present locally" check use it. |
| `packer_cache_dir` | `~/.cache/osimager` | Used only for a spec that lists its ISOs in a `urls` def, which no shipped spec does. It is not passed to Packer and not checked for "present locally". |
| `local_only` | `false` | When `true`, every run behaves as if `--local` was given. |
| `packer_cmd` | `packer` | Packer binary to run. |
| `credential_source` | `vault` | Where secrets come from: `vault` (HashiCorp Vault) or `config` (the local `secrets` file). |
| `vault_addr` | _(empty)_ | Vault server URL, e.g. `http://vault.example.com:8200`. |
| `vault_token` | _(empty)_ | Vault access token. |
| `cpu_sockets`, `cpu_cores`, `memory`, `boot_disk_size` | `1`, `2`, `2048`, `16384` | Default VM sizing (memory and disk in MB) when the spec doesn't set them. |
| `ansible_playbook` | `config.yml` | Playbook run for post-install configuration. |

---

## rfosimage

Re-runs provisioning (Ansible) against a VM that already exists, without reinstalling it.

### Synopsis

```
rfosimage [OPTIONS] PLATFORM/LOCATION/SPEC [NAME] [IP]
```

### How It Works

`rfosimage` resolves the same platform + location + spec configuration as `mkosimage`, then, before running Packer:

1. Drops the spec's generated files (nothing is installed, so no answer files are needed).
2. Keeps only the communicator settings (SSH or WinRM host, user, password) from the builder.
3. Replaces the builder with Packer's `null` builder, which just connects to the VM.
4. Runs the provisioners against it.

The VM must be running and reachable at `NAME` (or `IP`) with the credentials from your secrets.

### When to Use

- Re-running Ansible after changing a spec's playbook or roles.
- Applying configuration changes to a VM that's already built.
- Iterating on provisioning without waiting for a full OS install.

### Options

`rfosimage` accepts the same arguments and options as `mkosimage`.

---

## mkvenv

Creates the Python virtual environments that hold specific Ansible versions. A spec's `ansible_version` (e.g. `"2.18"`) says which Ansible its post-install configuration needs; `mkosimage` activates `<venv_dir>/<version>` before running Packer and stops with an error if that venv is missing (unless `--skip` is given).

### Synopsis

```
mkvenv                  # show which venvs the specs need and which are installed
mkvenv VERSION          # create the venv for one Ansible version, e.g. mkvenv 2.17
mkvenv --all            # create every missing venv the specs need
```

### Details

- Venvs live in `~/.local/share/osimager/venvs/` (override with the `OSIMAGER_VENV_DIR` environment variable).
- Which Ansible package and Python versions each Ansible version needs comes from `ansible.json`. `mkvenv` looks for a matching Python on your `PATH` and reports if none is found.
- `mkvenv` shares the general options of `mkosimage` (`-v`, `-d`, `--set`), but the listing options do nothing here.

---

## Examples

### Listing

```bash
# Every spec OSImager knows about ((*) = ISO present locally)
mkosimage -l

# What you can build right now, with the local path or download URL of each ISO
mkosimage -a

# What you can build without downloading anything
mkosimage --local

# The latest target of each dist and what it resolves to
mkosimage --latest

# The newest locally present version of each dist
mkosimage --latest --local

# Only aarch64
mkosimage -a --arch aarch64

# Check every download URL
mkosimage --check-urls
```

### Building Images

```bash
# Build; the VM is named after the spec
mkosimage proxmox/pve/alma-9.8-x86_64

# Build the newest Alma the specs provide
mkosimage proxmox/pve/alma-latest-x86_64

# Build the newest Alma whose ISO is already present, never downloading
mkosimage --local proxmox/pve/alma-latest-x86_64

# Explicit hostname and static IP
mkosimage vmware/lab/rhel-9.5-x86_64 myhost 192.168.1.100

# Custom FQDN
mkosimage -F myhost.custom.domain vmware/lab/rhel-9.5-x86_64 myhost 192.168.1.100

# Replace an existing VM of the same name
mkosimage -f vmware/lab/rhel-9.5-x86_64 myhost
```

### Debugging and Inspection

```bash
# Generate everything and show the packer command, but don't run it
mkosimage -n vmware/lab/rhel-9.5-x86_64 myhost

# Show the resolved defs
mkosimage -x vmware/lab/rhel-9.5-x86_64 myhost

# Show the Packer build JSON
mkosimage -u vmware/lab/rhel-9.5-x86_64 myhost

# Keep the VM and temp files if the build fails
mkosimage -k vmware/lab/rhel-9.5-x86_64 myhost

# Packer's detailed log, written to a file
mkosimage -L -N /tmp/packer.log vmware/lab/rhel-9.5-x86_64 myhost
```

### Overriding Defs

```bash
mkosimage -D memory=8192,cpu_cores=8,boot_disk_size=51200 vmware/lab/rhel-9.5-x86_64 bighost
```

### Re-provisioning

```bash
rfosimage vmware/lab/rhel-9.5-x86_64 myhost 192.168.1.100
```

### Persistent Settings

```bash
# Use the local secrets file instead of Vault
mkosimage --set credential_source=config

# Configure Vault
mkosimage --set vault_addr=http://vault.example.com:8200 --set vault_token=hvs.your-token

# Where your ISOs live
mkosimage --set iso_path=/iso
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success. |
| 1 | OSImager error: unknown platform or spec, missing ISO, missing credentials, invalid arguments. |
| other | A build that reaches Packer exits with Packer's exit code. |

---

## Configuration File

All three commands read `~/.config/osimager/config.json` (or `$XDG_CONFIG_HOME/osimager/config.json`). `--set` writes it. Built-in defaults apply to any key it doesn't contain, and command-line flags such as `--local` override it for one run.

```json
{
    "iso_path": "/iso",
    "packer_cache_dir": "/home/you/.cache/osimager",
    "local_only": false,
    "packer_cmd": "packer",
    "credential_source": "config",
    "ansible_playbook": "config.yml"
}
```
