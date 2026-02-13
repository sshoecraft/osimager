# Spec Reference

Spec files are JSON documents that define everything OSImager needs to build an OS image: the distribution, versions, architectures, installer files, boot commands, provisioners, and platform-specific configuration. They live in `osimager/data/specs/<name>/spec.json`.

---

## Spec File Anatomy

Every top-level key that can appear in a spec JSON file:

| Key | Type | Description |
|-----|------|-------------|
| `provides` | object | What the spec produces: `dist`, `versions`, and `arches` |
| `include` | string or list | Inheritance chain -- references to other spec(s) to load first |
| `method` | string | `"merge"` (default) or `"replace"` -- controls how this spec's data merges with inherited data |
| `merge` | list | Key names within dict sections that should be deep-merged instead of overwritten |
| `flavor` | string | OS family: `"linux"`, `"unix"`, or `"windows"` |
| `platforms` | array | Which platforms this spec supports (e.g., `["virtualbox", "vmware", "vsphere"]`) |
| `locations` | array | Optional filter restricting which locations can use this spec |
| `install_notice` | array | Informational messages displayed before build |
| `defs` | object | Definition variables available for template substitution |
| `config` | object | Packer builder configuration (boot_command, shutdown_command, firmware, etc.) |
| `variables` | object | Packer user variables passed to the build |
| `evars` | object | Environment variables set during the build |
| `files` | array | Installer file generation recipes -- each entry has `sources` (array of file paths concatenated) and `dest` (output filename) |
| `pre_provisioners` | array | Packer provisioners that run before the main Ansible provisioner |
| `provisioners` | array | Main Packer provisioners (default: Ansible playbook) |
| `post_provisioners` | array | Packer provisioners that run after the main provisioner |
| `venv` | string | Python virtual environment name (for older distros needing legacy Ansible) |
| `required_files` | array | Files that must exist before build starts, with download instructions |
| `platform_specific` | array | Conditional overrides matched against the target platform |
| `location_specific` | array | Conditional overrides matched against the target location |
| `dist_specific` | array | Conditional overrides matched against the distribution name |
| `version_specific` | array | Conditional overrides matched against the version string |
| `arch_specific` | array | Conditional overrides matched against the architecture |
| `firmware_specific` | array | Conditional overrides matched against the firmware type (bios/efi) |

### The `provides` Object

```json
{
  "provides": {
    "dist": "rhel",
    "versions": [
      "8.[0,1,2,3,5,6,7,8,9,10]",
      "9.[0-7]",
      "10.[0-1]"
    ],
    "arches": [
      "x86_64",
      "aarch64"
    ]
  }
}
```

- **`dist`** -- The distribution identifier used in build targets (e.g., `rhel`, `alma`, `debian`).
- **`versions`** -- Array of version strings, supporting range expansion syntax (see [Version Expansion Syntax](#version-expansion-syntax)).
- **`arches`** -- Array of supported architectures. Common values: `i386`, `x86_64`, `aarch64`.

### The `files` Array

Each entry in `files` concatenates multiple source files into a single output file used during installation:

```json
{
  "files": [
    {
      "sources": [
        "rhel/kickstart_>>major<<.cfg",
        "rhel/ks-part.sh",
        "rhel/kickstart_end.cfg",
        "rhel/kickstart_post.cfg",
        "rhel/install_vmwtools.sh",
        "rhel/kickstart_end.cfg"
      ],
      "dest": "ks.cfg"
    }
  ]
}
```

Source paths are relative to `osimager/data/files/`. Template substitution is applied to both source paths and file contents.

### The `required_files` Array

Declares files that must be present before a build can start. If missing, OSImager prints download instructions and exits:

```json
{
  "required_files": [
    {
      "file": "esxi/esx-tools-for-esxi-9.7.2-0.0.5911061.i386.vib",
      "description": "VMware Tools VIB required for ESXi 5.x/6.x installation",
      "url": "https://my.vmware.com/group/vmware/downloads/details?downloadGroup=ESXI55U3",
      "location": "esxi/"
    }
  ]
}
```

---

## Inheritance System

Specs use the `include` key to form inheritance chains. When a spec includes another, the parent spec is loaded first, then the child's data is merged on top. This allows distribution-specific specs to share common configuration from base specs.

### Inheritance Chains

```
alma -----> rhel -----> linux -----> ssh
rocky ----> rhel -----> linux -----> ssh
centos ---> rhel -----> linux -----> ssh
oel ------> rhel -----> linux -----> ssh
debian ---> linux ----> ssh
ubuntu ---> linux ----> ssh
sles -----> linux ----> ssh
windows-server -> windows -> winrm
esxi        (standalone -- no includes)
sysvr4      (standalone -- no includes)
```

### What Each Base Level Contributes

#### `ssh` -- SSH Communicator Base

The lowest-level base for all Linux/Unix specs. Configures the Packer SSH communicator:

- `config.communicator` = `"ssh"`
- `config.ssh_username` / `config.ssh_password` via Packer user variables
- `config.ssh_timeout` = `"25m"`
- Dynamic `ssh_host` and `ssh_port` using Python eval expressions that adapt to the platform type

#### `winrm` -- WinRM Communicator Base

The lowest-level base for all Windows specs. Configures the Packer WinRM communicator:

- `config.communicator` = `"winrm"`
- `config.winrm_username` / `config.winrm_password` via Packer user variables
- `config.winrm_timeout` = `"4h"`
- Dynamic `winrm_host` based on platform type

#### `linux` -- Linux Base

Inherits from `ssh`. Adds Linux-specific defaults:

- `defs.boot_disk_size` = `16384` (16 GB)
- `variables.ssh-username` and `variables.ssh-password` referencing the `images/linux` vault path

#### `windows` -- Windows Base

Inherits from `winrm`. Adds Windows-specific defaults:

- `defs.boot_disk_size` = `131072` (128 GB)
- `variables.winrm-username` and `variables.winrm-password` referencing the `images/windows` vault path

### Merge Behavior

The `method` key controls how inherited data combines:

- **`"merge"`** (default) -- Dictionaries are merged key-by-key (`update()`). Lists are appended to.
- **`"replace"`** -- Lists are cleared before new items are added. Dictionaries still merge.

The `merge` key within dict sections (like `config`) lists keys that should be deep-merged rather than overwritten:

```json
{
  "config": {
    "merge": ["vmx_data"],
    "vmx_data": {
      "scsi0.virtualdev": "pvscsi"
    }
  }
}
```

In this example, the `vmx_data` dictionary is merged into any existing `vmx_data` from the parent spec rather than replacing it entirely.

### Load Order

The loading process in `core.py` follows this sequence:

1. **Platform file** is loaded first
2. **Location file** is loaded second
3. **Spec file** is loaded third, which recursively loads its `include` chain (deepest parent first)
4. At each level, after loading data, all six `*_specific` sections are evaluated against the current build context

---

## The 6 Specific Section Types

Specific sections provide conditional overrides. Each entry in a specific section has a name field that is matched using `re.fullmatch()` with `re.IGNORECASE` against the current build value.

| Section | Match Key | Matched Against | Example Pattern |
|---------|-----------|-----------------|-----------------|
| `platform_specific` | `platform` | Target platform name | `"vsphere"`, `"proxmox"` |
| `location_specific` | `location` | Target location name | `"datacenter1"`, `"lab.*"` |
| `dist_specific` | `dist` | Distribution name | `"rhel"`, `"alma\|rocky"` |
| `version_specific` | `version` | Full version string | `"9.*"`, `"[23].*"`, `"8.10"` |
| `arch_specific` | `arch` | Architecture string | `"x86_64"`, `"i386"` |
| `firmware_specific` | `firmware` | Firmware type | `"efi"`, `"bios"` |

### Processing Order

The six specific types are always processed in this fixed order:

1. `platform_specific`
2. `location_specific`
3. `dist_specific`
4. `version_specific`
5. `arch_specific`
6. `firmware_specific`

### Recursive Nesting

Any specific section can contain any other specific section type. This enables precise conditional logic. For example, a `version_specific` entry can contain `platform_specific` entries:

```json
{
  "version_specific": [
    {
      "version": "7.*",
      "arches": ["x86_64"],
      "defs": {
        "spec_config": "specs/rhel/config_7.yml"
      },
      "platform_specific": [
        {
          "platform": "virtualbox",
          "config": {
            "guest_os_type": "RedHat7_64"
          }
        },
        {
          "platform": "vmware",
          "config": {
            "guest_os_type": "rhel7-64"
          }
        },
        {
          "platform": "vsphere",
          "config": {
            "guest_os_type": "rhel7_64Guest"
          }
        }
      ]
    }
  ]
}
```

And a `platform_specific` entry can contain `version_specific` entries:

```json
{
  "platform_specific": [
    {
      "platform": "vsphere",
      "config": {
        "NestedHV": true
      },
      "version_specific": [
        {
          "version": "7.*",
          "defs": {
            "memory": 8192,
            "firmware": "efi"
          },
          "config": {
            "guest_os_type": "vmkernel7Guest"
          }
        }
      ]
    }
  ]
}
```

### Additional Override Keys

Within any specific entry, beyond the standard data keys (`defs`, `config`, `files`, etc.), these override keys can also appear:

- **`arches`** -- Restricts the architectures this entry applies to (narrows the parent spec's `provides.arches`)
- **`method`** -- Can be set to `"replace"` within a specific entry to clear lists before adding new items
- **`venv`** -- Overrides the Python virtual environment for that match

---

## Version Expansion Syntax

The `provides.versions` array supports compact range syntax to define many versions without listing each individually.

### Range Expansion: `[start-end]`

Generates all integers from `start` to `end` (inclusive):

```json
"versions": ["9.[0-7]"]
```

Expands to: `9.0`, `9.1`, `9.2`, `9.3`, `9.4`, `9.5`, `9.6`, `9.7`

### Explicit List: `[a,b,c]`

Lists specific values separated by commas:

```json
"versions": ["8.[0,1,2,3,5,6,7,8,9,10]"]
```

Expands to: `8.0`, `8.1`, `8.2`, `8.3`, `8.5`, `8.6`, `8.7`, `8.8`, `8.9`, `8.10`

### Zero-Padded Range: `[01-03]`

Preserves leading zeros in the expansion:

```json
"versions": ["12.[01-03]"]
```

Expands to: `12.01`, `12.02`, `12.03`

### Plain Versions

Versions without brackets are used as-is:

```json
"versions": ["5.5U3", "6.0U2", "6.5", "7.0U3n", "8.0U2"]
```

!!! warning "Mixed Syntax Not Supported"
    Combined range and list syntax like `[0-3,5-7]` is **not** supported. Use separate entries instead:
    ```json
    "versions": ["8.[0-3]", "8.[5-7]"]
    ```

---

## Template Substitution Patterns

OSImager uses a marker-based template substitution system. Markers in spec values are replaced at build time with computed values.

| Syntax | Name | Description |
|--------|------|-------------|
| `>>key<<` | Def substitution | Replaces marker with the value of `defs[key]` |
| `%>key<%` | Full-value substitution | Replaces the entire JSON value (including quotes) with `defs[key]` -- allows injecting non-string types |
| `+>key<+` | Basename substitution | Replaces marker with the basename (filename only) of `defs[key]` |
| `*>key<*` | DNS lookup | Replaces marker with the IP address from an nslookup of `defs[key]` |
| `\|>path<\|` | Vault secret | Replaces marker with a value retrieved from HashiCorp Vault (or local secrets file) |
| `#>expr<#` | Numeric eval | Evaluates a numeric expression using def values (e.g., `#>memory * 2<#`) |
| `$>VAR<$` | Environment variable | Replaces marker with the value of environment variable `VAR` |
| `1>path<1` | MD5 password hash | Retrieves a secret and returns its MD5 crypt hash |
| `5>path<5` | SHA-256 password hash | Retrieves a secret and returns its SHA-256 crypt hash |
| `6>path<6` | SHA-512 password hash | Retrieves a secret and returns its SHA-512 crypt hash |
| `E>expr<E` | Python eval | Evaluates a Python expression with access to defs -- used for conditional logic |
| `[>key<]` | List expansion | Expands a defs list value inline, inserting each item as a separate element |

### Common Def Variables

These variables are automatically available in `defs` during a build:

| Variable | Source | Example Value |
|----------|--------|---------------|
| `platform` | Target platform | `vmware` |
| `platform_name` | Target platform | `vmware` |
| `platform_type` | Packer builder type | `vmware-iso` |
| `location` | Target location | `lab` |
| `location_name` | Target location | `lab` |
| `dist` | Distribution name | `rhel` |
| `version` | Full version string | `9.4` |
| `major` | Major version number | `9` |
| `minor` | Minor version number | `4` |
| `arch` | Architecture | `x86_64` |
| `name` | Instance name | `rhel-9.4-x86_64` |
| `fqdn` | Fully qualified domain name | `rhel-9.4-x86_64.lab.local` |
| `ip` | Resolved IP address | `192.168.1.100` |
| `base_path` | OSImager base directory | `/opt/osimager` |
| `data_path` | Data directory path | `/opt/osimager/data` |
| `spec_dir` | Directory containing the active spec file | `/opt/osimager/data/specs/rhel` |
| `temp_dir` | Temporary build directory | `/tmp/tmpXXXXXX` |
| `user_dir` | User config directory | `~/.config/osimager` |
| `boot_disk_size` | Boot disk size in MB | `16384` |
| `dns1`, `dns2`, ... | DNS server addresses | `192.168.1.1` |
| `dns_search` | DNS search domains | `lab.local` |
| `ntp1`, `ntp2`, ... | NTP server addresses | `pool.ntp.org` |
| `subnet` | Network subnet from CIDR | `192.168.1.0` |
| `prefix` | Network prefix from CIDR | `24` |
| `netmask` | Calculated netmask | `255.255.255.0` |
| `gateway` / `gw` | Gateway address | `192.168.1.254` |

### Python Eval Expressions

The `E>...<E` syntax allows inline Python expressions with access to all defs as local variables. This is used extensively in spec files for conditional logic:

```json
"ssh_host": "E>'>>ip<<' if '>>ip<<' != '' and '>>ip<<' != 'dhcp' else (None if '>>platform_type<<' in ['vsphere-iso', 'amazon-ebs', 'azure-arm', 'googlecompute'] else '{{ .Host }}')<E"
```

```json
"guest_os_type": "RedHat6E>'_64' if '>>arch<<' == 'x86_64' else ''<E"
```

```json
"deb_arch": "E>'amd64' if '>>arch<<' == 'x86_64' else ('arm64' if '>>arch<<' == 'aarch64' else '>>arch<<')<E"
```

---

## Per-Distribution Details

### RHEL (Red Hat Enterprise Linux)

| Property | Value |
|----------|-------|
| **Dist name** | `rhel` |
| **Versions** | 2.1, 3.0, 4.8, 5.[1,9,10,11], 6.[9-10], 7.[5-9], 8.[0,1,2,3,5,6,7,8,9,10], 9.[0-7], 10.[0-1] |
| **Architectures** | i386, x86_64, aarch64 |
| **Include chain** | rhel -> linux -> ssh |
| **Installer type** | Kickstart |
| **Platforms** | virtualbox, vmware, vsphere, proxmox, qemu, libvirt, xenserver, hyperv, azure, gcp, aws, none |

**Cloud support:**

- Versions 7.x: Azure (RHEL 7lvm-gen2), GCP (rhel-7), AWS (RHEL-7 HVM)
- Versions 8.x: Azure (RHEL 8-lvm-gen2), GCP (rhel-8), AWS (RHEL-8 HVM)
- Versions 9.x: Azure (RHEL 9-lvm-gen2), GCP (rhel-9), AWS (RHEL-9 HVM)
- Versions 10.x: Azure (RHEL 10-lvm-gen2), GCP (rhel-10), AWS (RHEL-10 HVM)

**Key version-specific patterns:**

- Versions 2.x-3.x: i386 only, legacy SSH algorithms, Ansible 2.10 venv, IDE disks, custom `configure_system` pre-provisioner
- Versions 4.x: i386/x86_64, legacy SSH, Ansible 2.10 venv, boot via `ks=cdrom:/ks.cfg`
- Versions 5.x: i386/x86_64, legacy SSH, Ansible 2.10 venv, Python 2 interpreter
- Versions 6.x: Ansible 2.10 venv, Python 2 interpreter, legacy SSH ciphers
- Versions 7.x+: x86_64 only, EFI firmware, OEMDRV-based boot
- Versions 8.x+: x86_64/aarch64, EFI firmware, Python 3 interpreter
- Versions 9.x+: 4 CPU cores, 4096 MB memory, pvscsi on VMware

**Key platform-specific patterns:**

- Proxmox: firmware set to empty string (uses Proxmox defaults), QEMU agent disabled for legacy versions
- VirtualBox: version-specific `guest_os_type` (RedHat7_64, RedHat8_64, RedHat9_64)
- VMware: version-specific `guest_os_type`, pvscsi for 9.x+, VMX data merging for legacy VMware tools ISOs
- vSphere: version-specific `guest_os_type` (rhel7_64Guest, rhel8_64Guest, rhel9_64Guest)

---

### AlmaLinux

| Property | Value |
|----------|-------|
| **Dist name** | `alma` |
| **Versions** | 8.[3-10], 9.[0-7], 10.[0-1] |
| **Architectures** | x86_64, aarch64 |
| **Include chain** | alma -> rhel -> linux -> ssh |
| **Installer type** | Kickstart (inherited from RHEL) |
| **Platforms** | Inherited from RHEL: virtualbox, vmware, vsphere, proxmox, qemu, libvirt, xenserver, hyperv, azure, gcp, aws, none |

**Cloud support:**

- Versions 8.x: Azure (almalinux 8-gen2), GCP (almalinux-8), AWS (AlmaLinux OS 8)
- Versions 9.x: Azure (almalinux 9-gen2), GCP (almalinux-9), AWS (AlmaLinux OS 9)
- Versions 10.x: Azure (almalinux 10-gen2), GCP (almalinux-10), AWS (AlmaLinux OS 10)

Uses merge method to overlay AlmaLinux-specific ISO URLs and cloud image references on top of the full RHEL configuration. Version 8.3 is restricted to x86_64 only.

---

### Rocky Linux

| Property | Value |
|----------|-------|
| **Dist name** | `rocky` |
| **Versions** | 8.[3-9], 9.[0-7], 10.[0-1] |
| **Architectures** | x86_64, aarch64 |
| **Include chain** | rocky -> rhel -> linux -> ssh |
| **Installer type** | Kickstart (inherited from RHEL) |
| **Platforms** | Inherited from RHEL |

**Cloud support:**

- Versions 8.x: Azure (rockylinux-x86_64 8-lvm), GCP (rocky-linux-8, rocky-linux-cloud), AWS (Rocky-8-EC2-Base)
- Versions 9.x: Azure (rockylinux-x86_64 9-lvm), GCP (rocky-linux-9, rocky-linux-cloud), AWS (Rocky-9-EC2-Base)
- Versions 10.x: Azure (rockylinux-x86_64 10-lvm), GCP (rocky-linux-10, rocky-linux-cloud), AWS (Rocky-10-EC2-Base)

Version 8.x uses a different ISO URL pattern (`-dvd1.iso` suffix) compared to 9.x/10.x (`-dvd.iso`).

---

### CentOS

| Property | Value |
|----------|-------|
| **Dist name** | `centos` |
| **Versions** | 5.[0-10], 6.[0-10], 7.[0-9], 8.[0-5] |
| **Architectures** | i386, x86_64, aarch64 |
| **Include chain** | centos -> rhel -> linux -> ssh |
| **Installer type** | Kickstart (inherited from RHEL) |
| **Platforms** | Inherited from RHEL |

**Cloud support:**

- Versions 7.x: Azure (CentOS-LVM 7-lvm-gen2), GCP (centos-7, centos-cloud), AWS (CentOS Linux 7)
- Versions 8.x: Azure (CentOS-LVM 8-lvm-gen2), GCP (centos-stream-8, centos-cloud), AWS (CentOS Stream 8)

**Key version-specific patterns:**

- Versions 5.x: i386/x86_64, ISOs from vault.centos.org
- Versions 6.x: i386/x86_64, ISOs from vault.centos.org
- Versions 7.x: x86_64 only, each minor version has a unique ISO naming convention with build date suffixes (e.g., `7.0.1406`, `7.9.2009`)
- Versions 8.x: x86_64/aarch64, ISOs from vault.centos.org with build date suffixes
- vSphere guest OS types: centos5Guest, centos6Guest, centos7_64Guest, centos8_64Guest

---

### Oracle Enterprise Linux (OEL)

| Property | Value |
|----------|-------|
| **Dist name** | `oel` |
| **Versions** | 5.[0-10], 6.[0-10], 7.[0-9], 8.[0-10], 9.[0-7], 10.[0-1] |
| **Architectures** | i386, x86_64, aarch64 |
| **Include chain** | oel -> rhel -> linux -> ssh |
| **Installer type** | Kickstart (inherited from RHEL) |
| **Platforms** | Inherited from RHEL |

**Cloud support:**

- Versions 7.x: Azure (Oracle-Linux ol79-lvm-gen2), GCP (oracle-linux-7), AWS (OL7 HVM)
- Versions 8.x: Azure (Oracle-Linux ol89-lvm-gen2), GCP (oracle-linux-8), AWS (OL8 HVM)
- Versions 9.x: Azure (Oracle-Linux ol9-lvm-gen2), GCP (oracle-linux-9), AWS (OL9 HVM)
- Versions 10.x: Azure (Oracle-Linux ol10-lvm-gen2), GCP (oracle-linux-10), AWS (OL10 HVM)

**Key version-specific patterns:**

- Versions 5.x/6.x: i386/x86_64, ISOs from yum.oracle.com using `u>>minor<<` URL pattern
- Version 6.x: custom kickstart file (`oel/kickstart_6.cfg`) with OEL-specific post-install
- Versions 7.x: x86_64 only, OEL-specific vSphere guest types (oracleLinux7_64Guest)
- Versions 8.x+: x86_64/aarch64
- VMware guest types use `oraclelinux-64` (legacy) or `oraclelinux8-64` / `oraclelinux9-64` (modern)

---

### Debian

| Property | Value |
|----------|-------|
| **Dist name** | `debian` |
| **Versions** | 8.[0-11], 9.[0-13], 10.[0-13], 11.[0-11], 12.[0-13], 13.[0-3] |
| **Architectures** | i386, x86_64, aarch64 |
| **Include chain** | debian -> linux -> ssh |
| **Installer type** | Preseed |
| **Platforms** | virtualbox, vmware, vsphere, proxmox, qemu, libvirt, xenserver, hyperv, azure, gcp, aws, none |

**Cloud support:**

- Versions 11.x: Azure (debian-11 11-gen2), GCP (debian-11, debian-cloud), AWS (debian-11-amd64)
- Versions 12.x: Azure (debian-12 12-gen2), GCP (debian-12, debian-cloud), AWS (debian-12-amd64)

**Key version-specific patterns:**

- Versions 8.x: i386/x86_64, uses `method: "replace"` for files with a Debian 8-specific preseed (`debian-8-preseed.cfg`), custom boot command that mounts and runs `debian.fix`
- Versions 9.x: i386/x86_64, uses `method: "replace"` for files with `debian_pre10.seed`
- Versions 10.x+: x86_64/aarch64, uses the standard `debian.seed` preseed file
- Architecture mapping: `deb_arch` def converts `x86_64` to `amd64` and `aarch64` to `arm64` using a Python eval expression
- ISO URLs reference `cdimage.debian.org/cdimage/archive/`
- Boot disk size: 32768 MB (32 GB), overriding the Linux base of 16 GB

**Boot process:** Uses a multi-step boot command that boots the installer, switches to a virtual console to mount the CD media, then switches back to continue the preseed-driven installation.

---

### Ubuntu

| Property | Value |
|----------|-------|
| **Dist name** | `ubuntu` |
| **Versions** | 18.04, 20.04, 22.04, 24.04 |
| **Architectures** | x86_64, aarch64 |
| **Include chain** | ubuntu -> linux -> ssh |
| **Installer type** | Preseed (18.04), Cloud-init/Autoinstall (20.04+) |
| **Platforms** | virtualbox, vmware, vsphere, proxmox, qemu, libvirt, xenserver, hyperv, azure, gcp, aws, none |

**Cloud support:**

- 20.04: Azure (ubuntu-server-focal 20_04-lts-gen2), GCP (ubuntu-2004-lts), AWS (ubuntu-focal-20.04)
- 22.04: Azure (ubuntu-server-jammy 22_04-lts-gen2), GCP (ubuntu-2204-lts), AWS (ubuntu-jammy-22.04)
- 24.04: Azure (ubuntu-24_04-lts server), GCP (ubuntu-2404-lts-amd64), AWS (ubuntu-noble-24.04)

**Key version-specific patterns:**

- Version 18.04: x86_64 only, uses legacy preseed installer (`ubuntu.seed`), `method: "replace"` for files, cd_label is `"media"`, different boot command using `/install/vmlinuz`
- Versions 20.04+: Uses cloud-init autoinstall (`user-data` + `meta-data`), cd_label is `"cidata"`, boot command edits GRUB to add `autoinstall` parameter
- Version 20.04: Different boot command using `/casper/vmlinuz` directly
- Versions 22.04/24.04: Use the default GRUB-edit boot command
- Architecture mapping: same `deb_arch` conversion as Debian
- Boot disk size: 32768 MB (32 GB)

---

### SLES (SUSE Linux Enterprise Server)

| Property | Value |
|----------|-------|
| **Dist name** | `sles` |
| **Versions** | 12.[1-5], 15.[0-7], 16.[0-0] |
| **Architectures** | x86_64, aarch64 |
| **Include chain** | sles -> linux -> ssh |
| **Installer type** | AutoYaST (XML) |
| **Platforms** | virtualbox, vmware, vsphere, proxmox, qemu, libvirt, xenserver, hyperv, azure, gcp, aws, none |

**Cloud support:**

- Versions 15.x: Azure (sles-15-spN gen2), GCP (sles-15, suse-cloud), AWS (suse-sles-15-spN)

**Key version-specific patterns:**

- Versions 12.x: x86_64 only, Python 2 interpreter, uses `autoinst_12.xml`, ISOs from local file paths
- Versions 15.x: x86_64/aarch64, Python 3 interpreter, uses `autoinst_15.xml`, cloud image refs with SP (service pack) number in names
- Versions 16.x: uses `autoinst_16.xml`
- Version 15.0: Special ISO URL pattern without SP suffix
- Boot command uses `textmode=1` and `autoyast=device://OEMDRV/autoinst.xml`
- Boot disk size: 32768 MB (32 GB)
- Timezone default: `America/Chicago`

**Platform-specific guest OS types:**

- VirtualBox: `OpenSUSE_64` (all versions)
- VMware: `sles12-64`, `sles15-64`, `sles16-64`
- vSphere: `sles12_64Guest`, `sles15_64Guest`, `sles16_64Guest`

---

### ESXi (VMware ESXi)

| Property | Value |
|----------|-------|
| **Dist name** | `esxi` |
| **Versions** | 5.5U3, 6.0U2, 6.5, 7.0U3n, 8.0U2 |
| **Architectures** | x86_64 |
| **Include chain** | None (standalone) |
| **Installer type** | Kickstart |
| **Flavor** | `linux` |
| **Platforms** | vmware, vsphere |

**Key version-specific patterns:**

- Versions 5.x, 6.0, 6.5: Require a VMware Tools VIB file (`required_files`), included on the CD alongside the kickstart
- Versions 7.x: No VIB required, 8192 MB memory, EFI firmware on vSphere
- Versions 8.x: No VIB required, 12288 MB memory, 4 CPU cores, EFI firmware on vSphere
- Default firmware is `bios`, overridden per-version on vSphere

**`firmware_specific` usage:** ESXi uses `firmware_specific` to change the boot command for EFI builds (shorter boot_wait, no initial Enter keypress).

**Platform-specific patterns:**

- vSphere: Enables `NestedHV` (nested virtualization), version-specific guest types (vmkernel5Guest through vmkernel8Guest), kickstart includes `kickstart_post.cfg` for post-install on virtual hardware, lsilogic-sas controller for older versions
- VMware Workstation/Fusion: Sets `vmx_data` for pvscsi, vmxnet3, VNC, nested HV; older versions override with lsisas1068 SCSI controller

---

### SysVR4 (System V Release 4)

| Property | Value |
|----------|-------|
| **Dist name** | `sysvr4` |
| **Versions** | 2.1 |
| **Architectures** | i386 |
| **Include chain** | None (standalone) |
| **Installer type** | Manual (with `configure_system` script) |
| **Flavor** | `unix` |
| **Platforms** | virtualbox, vmware, proxmox |

The most minimal spec in the system. Uses a `configure_system` script uploaded via `pre_provisioners` and an Ansible playbook referenced via `>>spec_dir<</config.yml`. No SSH/WinRM communicator base -- configuration is handled entirely through `pre_provisioners`.

**Platform-specific patterns:**

- Proxmox: IDE disks, e1000 NIC, QEMU agent disabled, `poweroff` post-provisioner
- VirtualBox: IDE disks, bridged e1000 NIC, `disable_shutdown` with manual `VBoxManage controlvm poweroff`
- VMware: IDE disk/CD adapters, e1000 NIC, VMware Tools ISO mounted, empty shutdown_command with sleep-based poweroff

---

### Windows (Desktop)

| Property | Value |
|----------|-------|
| **Dist name** | `windows` |
| **Include chain** | windows -> winrm |
| **Purpose** | Base spec for Windows -- not directly buildable; used only as a parent for `windows-server` |

Provides:

- `defs.boot_disk_size` = 131072 (128 GB)
- WinRM credentials from `images/windows` vault path

---

### Windows Server

| Property | Value |
|----------|-------|
| **Dist name** | `windows-server` |
| **Versions** | 2016, 2019, 2022, 2025 |
| **Architectures** | x86_64 |
| **Include chain** | windows-server -> windows -> winrm |
| **Installer type** | Autounattend.xml |
| **Platforms** | virtualbox, vmware, vsphere, proxmox, xenserver, hyperv, azure, gcp, aws, none |

**Cloud support:**

- 2016: Azure (WindowsServer 2016-datacenter-g2), GCP (windows-2016), AWS (Windows_Server-2016)
- 2019: Azure (WindowsServer 2019-datacenter-g2), GCP (windows-2019), AWS (Windows_Server-2019)
- 2022: Azure (WindowsServer 2022-datacenter-g2), GCP (windows-2022), AWS (Windows_Server-2022)
- 2025: Azure (WindowsServer 2025-datacenter-g2), GCP (windows-2025), AWS (Windows_Server-2025)

**Key version-specific patterns:**

- Each version has a unique KMS product key for evaluation installation
- Version 2016: 4096 MB memory (reduced from the default 8192)
- Versions 2019-2025: 8192 MB memory, 4 CPU cores
- CD includes both `Autounattend.xml` and the `windows/build/*` scripts directory

**Platform-specific patterns:**

- vSphere: `windows9Server64Guest` guest type, VMware Tools ISO path; 2025 uses `windows2019srvNext_64Guest`
- VirtualBox: version-specific guest types (Windows2016_64, Windows2019_64, Windows2022_64), VBoxSVGA controller, IDE hard drive interface

---

## Quick Reference: All Distributions at a Glance

| Distribution | Versions | Arches | Installer | Include Chain | Cloud |
|-------------|----------|--------|-----------|---------------|-------|
| rhel | 2.1 -- 10.1 | i386, x86_64, aarch64 | Kickstart | linux -> ssh | 7+ |
| alma | 8.3 -- 10.1 | x86_64, aarch64 | Kickstart | rhel -> linux -> ssh | 8+ |
| rocky | 8.3 -- 10.1 | x86_64, aarch64 | Kickstart | rhel -> linux -> ssh | 8+ |
| centos | 5.0 -- 8.5 | i386, x86_64, aarch64 | Kickstart | rhel -> linux -> ssh | 7+ |
| oel | 5.0 -- 10.1 | i386, x86_64, aarch64 | Kickstart | rhel -> linux -> ssh | 7+ |
| debian | 8.0 -- 13.3 | i386, x86_64, aarch64 | Preseed | linux -> ssh | 11+ |
| ubuntu | 18.04 -- 24.04 | x86_64, aarch64 | Preseed / Cloud-init | linux -> ssh | 20.04+ |
| sles | 12.1 -- 16.0 | x86_64, aarch64 | AutoYaST | linux -> ssh | 15+ |
| esxi | 5.5U3 -- 8.0U2 | x86_64 | Kickstart | (standalone) | No |
| sysvr4 | 2.1 | i386 | Manual | (standalone) | No |
| windows-server | 2016 -- 2025 | x86_64 | Autounattend | windows -> winrm | All |
