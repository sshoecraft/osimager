# OSImager

Multi-platform OS image builder using HashiCorp Packer. Build virtual machine images for any operating system -- from RHEL 2.1 (2002) to the latest RHEL 9, CentOS, Debian, Ubuntu, SLES, and Windows Server -- on any supported hypervisor, from a single command.

## Quick Install

```bash
pip install osimager
```

### Prerequisites

- **Python 3.8+**
- **HashiCorp Packer** -- https://developer.hashicorp.com/packer/install
- **Ansible** -- `pip install ansible`
- **A hypervisor** -- VirtualBox is free and the easiest to start with
- **Packer plugins** -- At minimum, the Ansible provisioner and your target platform plugin:
  ```bash
  packer plugins install github.com/hashicorp/ansible
  packer plugins install github.com/hashicorp/virtualbox
  ```
- **mkisofs** (recommended) -- `brew install cdrtools` (macOS) or `apt install genisoimage` (Linux)

## Getting Started

After installing, run `mkosimage` with no arguments -- it will tell you exactly what to set up:

```
$ mkosimage
Usage: mkosimage [OPTIONS] PLATFORM/LOCATION/SPEC [NAME] [IP]

No locations configured.
  Create a location file in ~/.config/osimager/locations/
  ...
```

### 1. Create a location

A location defines your build environment -- network settings, DNS, and where ISOs/VMs live.

Copy the quickstart template and edit it:

```bash
cp "$(python3 -c "import osimager, os; print(os.path.join(os.path.dirname(osimager.__file__), 'data', 'examples', 'quickstart-location.toml'))")" \
   ~/.config/osimager/locations/local.toml
```

Edit `~/.config/osimager/locations/local.toml` -- set your network, gateway, DNS, and paths:

```toml
platforms = ["virtualbox"]

[defs]
domain = "home.local"
gateway = "192.168.1.1"
cidr = "192.168.1.0/24"
vms_path = "/vms"

[defs.dns]
servers = ["192.168.1.1"]

[defs.ntp]
servers = ["pool.ntp.org"]
```

Locations support both TOML and JSON formats. If both `lab.toml` and `lab.json` exist, JSON takes priority.

### 2. Set up credentials

OS image builds need credentials for SSH/WinRM access and root passwords. OSImager supports two credential sources:

**Option A: Local secrets file** (simplest)

```bash
mkosimage --set credential_source=config
```

Create `~/.config/osimager/secrets`:

```
images/linux username=root password=YourPassword
images/windows username=Administrator password=YourPassword
```

**Option B: HashiCorp Vault**

```bash
mkosimage --set vault_addr=http://your-vault:8200
mkosimage --set vault_token=your-token
```

See the example files shipped with the package for the full secret path reference (including platform credentials for vSphere and Proxmox).

### 3. Build

```bash
# List all available OS specs
mkosimage --list

# Dry run -- generates the Packer config without executing
mkosimage -n virtualbox/local/alma-9.5-x86_64

# Build
mkosimage virtualbox/local/alma-9.5-x86_64

# Build the newest version a spec provides
mkosimage virtualbox/local/alma-latest-x86_64
```

## How It Works

```
mkosimage <platform>/<location>/<spec>
```

- **Platform** = your hypervisor (ships with package)
- **Location** = your environment: network, DNS, storage paths (you create this)
- **Spec** = the OS to build (ships with package)

OSImager merges these three configs together, performs template substitution, generates the appropriate answer file (kickstart, preseed, autoyast, or autounattend), produces a Packer build JSON, and executes it.

## Features

- **500+ OS specs** spanning 20+ distributions across decades of releases (see [Supported OS](https://sshoecraft.github.io/osimager/reference/supported-os/) for the generated catalog)
- **11 platforms**: VirtualBox, VMware, vSphere, Proxmox, QEMU/KVM, Hyper-V, XenServer, Azure, GCP, AWS
- **Automated installation**: Kickstart (RHEL/CentOS/Alma/Rocky/OEL), preseed (Debian), cloud-init (Ubuntu 20.04+), AutoYaST (SLES), Autounattend (Windows)
- **Ansible provisioning**: Post-install configuration via Ansible playbooks
- **Hierarchical configuration**: Platform/location/spec system with deep inheritance and per-version/per-platform overrides
- **Flexible credentials**: Local secrets file or optional HashiCorp Vault integration
- **TOML or JSON locations**: User-editable location configs in either format

## Supported Operating Systems

| Distribution | Versions | Install Method |
|-------------|----------|----------------|
| RHEL | 2.1, 3.0, 4.8, 5.x, 6.x, 7.x, 8.x, 9.x, 10.x | Kickstart |
| CentOS | 5.0-5.10, 6.0-6.10, 7.0-7.9, 8.0-8.5 | Kickstart |
| AlmaLinux | 8.3-8.10, 9.0-9.8, 10.0-10.2 | Kickstart |
| Rocky Linux | 8.3-8.10, 9.0-9.8 | Kickstart |
| Oracle Linux | 5.0-5.10, 6.0-6.10, 7.0-7.9, 8.0-8.10, 9.0-9.8, 10.0-10.2 | Kickstart |
| Debian | 8-13 | Preseed / Cloud-Init |
| Ubuntu | 18.04, 20.04, 22.04, 24.04, 26.04 | Cloud-Init |
| SLES | 12.1-12.5, 15.0-15.7, 16.0 | AutoYaST |
| VMware ESXi | 5.5U3, 6.0U2, 6.5, 7.0U3n, 8.0U2 | Kickstart |
| Windows Server | 2016, 2019, 2022, 2025 | Autounattend |

## Supported Platforms

| Platform | Type | Plugin |
|----------|------|--------|
| VirtualBox | Local | `github.com/hashicorp/virtualbox` |
| VMware Workstation/Fusion | Local | `github.com/hashicorp/vmware` |
| vSphere | Enterprise | `github.com/hashicorp/vsphere` |
| Proxmox | Enterprise | `github.com/hashicorp/proxmox` |
| QEMU/KVM | Local | `github.com/hashicorp/qemu` |
| Hyper-V | Local | Built-in |
| XenServer | Local | `github.com/ddelnano/xenserver` |
| Azure | Cloud | `github.com/hashicorp/azure` |
| GCP | Cloud | `github.com/hashicorp/googlecompute` |
| AWS | Cloud | `github.com/hashicorp/amazon` |

## Configuration

All user configuration lives in `~/.config/osimager/`:

| File | Purpose |
|------|---------|
| `locations/*.toml` or `*.json` | Build environments (you create these) |
| `secrets` | Credentials when using `credential_source=config` |
| `config.json` | Persistent settings (managed via `--set`) |

Settings are configured with `--set`:

```bash
mkosimage --set credential_source=config    # use local secrets file
mkosimage --set vault_addr=http://vault:8200 # vault server address
mkosimage --set local_only=True              # only use local ISOs
mkosimage --set packer_cache_dir=/var/cache  # ISO download cache
```

## CLI Reference

```
mkosimage [OPTIONS] PLATFORM/LOCATION/SPEC [NAME] [IP]

Listing (no target needed):
  -l, --list          Every spec OSImager knows about; (*) = ISO present locally
  -a, --avail         Specs you can build now, with local ISO path or download URL
  --local             Like -a, but only specs whose ISO is already present
  --latest            Each <dist>-latest-<arch> target and the spec it resolves to;
                      with -a/--local, narrows those lists to the latest of each dist
  --arch ARCH         Limit any listing to one architecture
  --check-urls        HEAD-check every download URL in every spec

Building:
  --local             Build only from an ISO already present; never download
  -n, --dry           Generate everything and print the packer command, don't run it
  -f                  Replace an existing VM/output of the same name (packer -force)
  -k                  On failure keep the VM (packer -on-error=abort) and temp files
  --skip              Skip post-install configuration (Ansible)
  -D K=V[,K=V]        Override defs for this build
  -F FQDN             Use this FQDN instead of NAME.<location domain>

Inspecting:
  -x, --defs          Print the resolved defs and exit
  -u, --dump          Print the Packer build JSON and exit
  -v / -d             Verbose / debug output (-d also runs packer -debug)
  -L, -N FILE         Packer log on, written to FILE

Settings:
  --set KEY=VALUE     Change a setting and save it to ~/.config/osimager/config.json
  --show-config       Print the current settings
```

Every option, with exact behavior, is in the [CLI reference](https://sshoecraft.github.io/osimager/reference/cli-reference/).

## Documentation

For detailed documentation on location setup, platform configuration, spec format, template syntax, and the credential system, see the [OSImager Documentation](https://sshoecraft.github.io/osimager).

## License

MIT License -- see [LICENSE](LICENSE) for details.
