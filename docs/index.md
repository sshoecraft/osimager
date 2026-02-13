# OSImager

**Multi-platform OS image builder using HashiCorp Packer.** Build VM images for any OS from a single command.

```
mkosimage <platform>/<location>/<spec> [name] [ip]
```

OSImager merges three configuration layers into a complete Packer build:

- **Platform** -- your hypervisor or cloud provider (ships with the package)
- **Location** -- your environment: network, DNS, storage paths, credentials (you create this)
- **Spec** -- the OS to build: distro, version, arch, install method (ships with the package)

---

## Feature Highlights

| Area | Details |
|------|---------|
| OS specs | **339+** covering 12 distributions, from RHEL 2.1 (2002) to current releases |
| Platforms | **13**: VirtualBox, VMware, vSphere, Proxmox, QEMU/KVM, libvirt, Hyper-V, XenServer, Azure, GCP, AWS, none |
| Config merging | Hierarchical with deep inheritance and **6 types of specific overrides** |
| Template engine | **12-action** substitution system with typed markers |
| Credentials | Two backends: HashiCorp Vault or local secrets file |
| Install methods | Kickstart, preseed, cloud-init, AutoYaST, Autounattend |
| Post-install | Ansible provisioning with per-distro and per-version task selection |

## Distributions

RHEL, CentOS, AlmaLinux, Rocky Linux, Oracle Enterprise Linux, Debian, Ubuntu, SLES, ESXi, SysVR4, Windows, Windows Server

---

## Configuration Merge Flow

Every build starts from `all.json` (global defaults) and layers configs on top. After the base merge, each layer's `*_specific` sections are applied when their condition matches the current build context.

```
all.json                          Global defaults (CPU, memory, disk)
  |
  v
platform/<name>.json              Builder type, platform settings
  |
  v
location/<name>.json|toml         Network, DNS, NTP, storage paths
  |
  v
spec/<name>/spec.json             OS-specific: iso, boot, install config
  |                               (may chain via "include" to a parent spec)
  v
+-------------------------------+
| Specific Overrides (per layer)|
|   platform_specific            |
|   location_specific            |
|   dist_specific                |
|   version_specific             |
|   arch_specific                |
|   firmware_specific            |
+-------------------------------+
  |
  v
Template substitution (12 actions)
  |
  v
Packer build JSON
```

Each `*_specific` section uses regex matching (`re.fullmatch`) against the current build's value for that dimension. This lets a single spec cover dozens of versions with targeted overrides where needed.

---

## Template Engine

The substitution engine processes all config values through 12 marker-delimited actions:

| Action | Markers | Purpose |
|--------|---------|---------|
| 1 | `%>..<%` | Replace entire value with defs variable |
| 2 | `>>..<<` | Inline substitution from defs |
| 3 | `+>..<+` | Basename of defs variable |
| 4 | `*>..<*` | DNS lookup (resolve to IP) |
| 5 | `\|>..<\|` | Secret from Vault or local secrets |
| 6 | `#>..<#` | Numeric expression evaluation |
| 7 | `$>..<$` | Environment variable |
| 8 | `1>..<1` | MD5 password hash of secret |
| 9 | `5>..<5` | SHA-256 password hash of secret |
| 10 | `6>..<6` | SHA-512 password hash of secret |
| 11 | `E>..<E` | Python expression evaluation |
| 12 | `[>..<]` | Insert list items (space-separated) |

---

## Quick Links

!!! tip "Getting started"
    - [Installation](installation.md) -- install from PyPI or source
    - [Getting Started](getting-started.md) -- first build walkthrough

!!! info "Configuration"
    - [Location Setup](configuration/location-setup.md) -- create your environment config
    - [Credential Setup](configuration/credential-setup.md) -- Vault or local secrets

!!! abstract "Reference"
    - [CLI Reference](reference/cli-reference.md) -- all command-line options
    - [Supported OS](reference/supported-os.md) -- full distro/version matrix
    - [Platform Reference](reference/platform-reference.md) -- platform configs and capabilities
    - [Spec Reference](reference/spec-reference.md) -- spec file format and fields

!!! note "Architecture"
    - [Build Pipeline](architecture/build-pipeline.md) -- end-to-end build flow
    - [Configuration Merging](architecture/configuration-merging.md) -- how layers compose
    - [Template Engine](architecture/template-engine.md) -- substitution actions in detail
