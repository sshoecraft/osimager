# Getting Started with OSImager

## What is OSImager

OSImager is a Python-based tool for building virtual machine images from ISO installers. It wraps HashiCorp Packer with a hierarchical configuration system that lets you define _what_ to build (the OS), _where_ to build it (your environment), and _how_ to build it (your hypervisor) -- all as composable JSON configurations. You specify a target like `virtualbox/mylab/centos-7.9-x86_64` and OSImager assembles a complete Packer build configuration from the matching platform, location, and spec files, generates kickstart/preseed/autoyast/cloud-init answer files, runs the build, and then provisions the resulting VM with Ansible.

The project ships with specs for over 300 OS version/architecture combinations spanning decades of operating system releases: RHEL 2.1 (2002) through RHEL 9.5, all CentOS versions from 5.0 through 8.5, AlmaLinux 8.3-9.7, Rocky Linux 8.3-10.1, Debian 8 through 13, Ubuntu 18.04 through 24.04, SLES 12 through 16, Oracle Enterprise Linux 5 through 9, VMware ESXi 5.5 through 8.0, Windows Server 2016 through 2025, and even System V Release 4. Each spec includes the correct answer file templates, boot commands, ISO URLs (where publicly available), and per-platform overrides for guest OS type, disk controllers, network adapters, and firmware.

OSImager supports multiple hypervisor platforms: VirtualBox, VMware Workstation/Fusion, vSphere, Proxmox, QEMU/KVM, and libvirt. The configuration inheritance system means adding a new location (say, a new lab) or a new platform only requires a single JSON file -- all existing specs automatically work with it.

## Prerequisites

Before using OSImager, you need the following installed on your system:

### Python 3.8+

OSImager requires Python 3.8 or later. Verify with:

```bash
python3 --version
```

### HashiCorp Packer

Packer is the underlying build engine. Install it for your platform:

**macOS (Homebrew):**
```bash
brew tap hashicorp/tap
brew install hashicorp/tap/packer
```

**Debian/Ubuntu:**
```bash
wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install packer
```

**RHEL/CentOS/Fedora:**
```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
sudo yum -y install packer
```

**Windows:** Download from https://developer.hashicorp.com/packer/install

Verify the installation:
```bash
packer --version
```

### Packer Plugins

After installing Packer, install the plugins for your target hypervisor(s) and the Ansible provisioner:

```bash
# Required: Ansible provisioner (used by all builds)
packer plugins install github.com/hashicorp/ansible

# Install the plugin(s) for your hypervisor:
packer plugins install github.com/hashicorp/virtualbox     # VirtualBox
packer plugins install github.com/hashicorp/vmware         # VMware Workstation/Fusion
packer plugins install github.com/hashicorp/vsphere        # vSphere
packer plugins install github.com/hashicorp/proxmox        # Proxmox
packer plugins install github.com/hashicorp/qemu           # QEMU/KVM
```

Or install all plugins at once with the included script:
```bash
./install-plugins.sh
```

### Ansible

Ansible is used for post-installation provisioning of the built VMs:

```bash
pip3 install ansible
```

### A Hypervisor

You need at least one supported hypervisor installed:

- **VirtualBox** -- Free and the easiest way to get started. Download from https://www.virtualbox.org/
- **VMware Workstation** (Linux) or **VMware Fusion** (macOS) -- Commercial, requires a license
- **Proxmox VE** -- Free, runs on a separate server
- **QEMU/KVM** -- Free, Linux-only
- **vSphere** -- Enterprise, requires existing vSphere infrastructure

For first-time users, VirtualBox is recommended.

### ISO Images

OS installation requires ISO images. Many specs include public download URLs -- for example, CentOS ISOs are available from vault.centos.org, RHEL ISOs from archive.org, Ubuntu from releases.ubuntu.com, and Oracle Linux from yum.oracle.com. These are downloaded automatically by Packer during the build.

Some specs reference local ISO files (using `file:///` URLs), particularly for commercial operating systems like SLES and Windows Server that require subscriptions or license agreements. For these, you need to obtain the ISOs yourself and place them in the directory specified by `iso_path` in your location configuration.

### mkisofs (Recommended)

Most builds create a secondary CD/ISO containing the answer file (kickstart, preseed, etc.). On macOS, install cdrtools to get mkisofs:

```bash
brew install cdrtools
```

On Linux, install `cdrtools` or `genisoimage` from your package manager. Without mkisofs, Packer falls back to macOS `hdiutil` which creates hybrid ISOs with Mac partition tables that Linux installers cannot read.

## Installation

Install from PyPI:

```bash
pip3 install osimager
```

Or install in development mode from a local clone:

```bash
pip3 install -e .
```

## Verify Installation

After installation, the `mkosimage` command should be available. List all available specs:

```bash
mkosimage --list
```

This prints every OS version/architecture combination that OSImager knows how to build. You should see entries like:

```
Available specs:
  alma-8.3-x86_64 (alma 8.3 x86_64)
  alma-8.4-aarch64 (alma 8.4 aarch64)
  alma-8.4-x86_64 (alma 8.4 x86_64)
  ...
  centos-7.9-x86_64 (centos 7.9 x86_64)
  ...
  debian-12.0-x86_64 (debian 12.0 x86_64)
  ...
  rhel-9.5-x86_64 (rhel 9.5 x86_64)
  ...
  ubuntu-24.04-x86_64 (ubuntu 24.04 x86_64)
  ...
```

## Configure Your Environment

OSImager uses a three-tier configuration hierarchy:

```
mkosimage  <platform> / <location> / <spec>
               |            |           |
               v            v           v
          Your hypervisor   Your env   The OS to build
```

- **Platform** = the hypervisor type (`virtualbox`, `vmware`, `vsphere`, `proxmox`, `qemu`). These ship with the package and define hypervisor-specific builder settings.
- **Location** = YOUR environment -- network topology, DNS, storage paths. You create this file.
- **Spec** = the operating system to build (`rhel-9.5-x86_64`, `centos-7.9-x86_64`, etc.). These ship with the package.

### Find the Data Directory

The platform, location, and spec files live inside the installed `osimager` package. Find the data directory:

```bash
python3 -c "import osimager; import os; print(os.path.join(os.path.dirname(osimager.__file__), 'data'))"
```

This prints something like:
```
/usr/local/lib/python3.12/site-packages/osimager/data
```

### Create Your Location File

Inside the data directory, there is a `locations/` subdirectory containing `example.json`. Copy it and customize it for your environment:

```bash
# Find where location files go
LOCATIONS=$(python3 -c "import osimager; import os; print(os.path.join(os.path.dirname(osimager.__file__), 'data', 'locations'))")

# Copy the example
cp "$LOCATIONS/example.json" "$LOCATIONS/mylab.json"
```

Edit `mylab.json` to match your network. Here is a complete example:

```json
{
  "platforms": [
    "virtualbox"
  ],
  "defs": {
    "domain": "home.lab",
    "cidr": "192.168.1.0/24",
    "dns": {
      "search": [
        "home.lab"
      ],
      "servers": [
        "192.168.1.1"
      ]
    },
    "gateway": "192.168.1.1",
    "ntp": {
      "servers": [
        "pool.ntp.org"
      ]
    },
    "vms_path": "/vms",
    "iso_path": "/iso/"
  }
}
```

**Field reference:**

| Field | Description |
|-------|-------------|
| `platforms` | Array of hypervisor names available at this location. Only these platforms can be used with this location. |
| `defs.domain` | DNS domain appended to VM hostnames to form FQDNs (e.g., `myvm.home.lab`) |
| `defs.cidr` | Network CIDR. Used to derive subnet and prefix length for static IP configurations in kickstart/preseed files. |
| `defs.dns.search` | DNS search domain list, written into the VM's resolver configuration. |
| `defs.dns.servers` | DNS server IP addresses. Referenced as `>>dns1<<`, `>>dns2<<`, etc. in answer file templates. |
| `defs.gateway` | Default gateway IP. If omitted, it is computed as the last usable address in the CIDR. |
| `defs.ntp.servers` | NTP server hostnames/IPs. Referenced as `>>ntp1<<`, `>>ntp2<<`, etc. in answer file templates. |
| `defs.vms_path` | Directory where built VM files (VMDKs, VDIs, qcow2 images) are stored. |
| `defs.iso_path` | Directory where ISO images are stored. Used by `file://` ISO URLs and as the download target for remote ISOs. |

**For VirtualBox users:** The essential fields are `domain`, `dns`, `gateway`, and `iso_path`. VirtualBox creates its own NAT/bridged networking, so the CIDR and gateway are primarily used for generating kickstart/preseed network configuration inside the guest.

## Your First Build

### Dry Run

Always start with a dry run to see what OSImager will do without actually building anything:

```bash
mkosimage --dry virtualbox/mylab/centos-7.9-x86_64
```

This displays the Packer command that would be executed, including the generated JSON configuration, without launching VirtualBox or downloading anything.

### Build

When you are ready to build:

```bash
mkosimage virtualbox/mylab/centos-7.9-x86_64
```

What happens during the build:

1. OSImager loads and merges the VirtualBox platform config, your mylab location config, and the CentOS 7.9 spec
2. It generates a kickstart file from templates, substituting your network values
3. It creates a Packer JSON configuration with all builder settings, boot commands, and provisioners
4. Packer downloads the CentOS 7.9 ISO from vault.centos.org (or uses a local copy if present)
5. Packer creates a VirtualBox VM, attaches the ISO and kickstart CD, and boots it
6. The boot command tells the installer to read the kickstart file for a fully automated installation
7. After installation, Packer connects via SSH and runs the Ansible provisioner for post-install configuration
8. The finished VM is left registered in VirtualBox, ready to use

### Useful Options

```bash
# Verbose output - see which files are loaded and what is happening
mkosimage -v virtualbox/mylab/centos-7.9-x86_64

# Debug mode - maximum detail, including Packer debug
mkosimage -d virtualbox/mylab/centos-7.9-x86_64

# Force rebuild even if a VM with that name already exists
mkosimage -f virtualbox/mylab/centos-7.9-x86_64

# Keep temporary files after build (useful for debugging kickstart issues)
mkosimage -k virtualbox/mylab/centos-7.9-x86_64

# Set a custom hostname and FQDN
mkosimage -F myserver.home.lab virtualbox/mylab/centos-7.9-x86_64

# Define custom variables (passed through to templates)
mkosimage -D hostname=myserver virtualbox/mylab/centos-7.9-x86_64

# Use local ISO only (do not download)
mkosimage --local-only virtualbox/mylab/centos-7.9-x86_64

# Dump the fully resolved build configuration as JSON (no build)
mkosimage -u virtualbox/mylab/centos-7.9-x86_64

# Dump all resolved variable definitions (no build)
mkosimage -x virtualbox/mylab/centos-7.9-x86_64
```

### Naming VMs

By default, the VM is named after the spec (e.g., `centos-7.9-x86_64`). You can provide a custom name and optionally a static IP as positional arguments:

```bash
mkosimage virtualbox/mylab/centos-7.9-x86_64 webserver01 192.168.1.50
```

## What's Next

- **[LOCATION_SETUP.md](LOCATION_SETUP.md)** -- Detailed guide on location configuration, including platform-specific settings for vSphere, Proxmox, VMware Workstation, and QEMU
- **[CONFIGURATION.md](CONFIGURATION.md)** -- Full reference for the spec configuration format, template substitution syntax, and configuration inheritance
