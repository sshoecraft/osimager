# Getting Started

A quickstart walkthrough for building your first OS image with OSImager and VirtualBox.

**Prerequisites:** OSImager installed (`pip install osimager`), Packer, Ansible, VirtualBox, and mkisofs. See [Installation](installation.md) for details.

---

## Step 1: Create a Location

A location defines your build environment: network settings, DNS, NTP, and where ISOs and VMs live on disk.

Copy the quickstart template into your user config directory:

```bash
mkdir -p ~/.config/osimager/locations
cp $(python3 -c "import osimager; import os; print(os.path.join(os.path.dirname(osimager.__file__), 'data', 'examples', 'quickstart-location.toml'))") \
   ~/.config/osimager/locations/local.toml
```

Edit `~/.config/osimager/locations/local.toml` to match your network:

```toml
platforms = ["virtualbox"]

[defs]
domain = "home.local"
gateway = "192.168.1.1"
cidr = "192.168.1.0/24"
vms_path = "/vms"
iso_path = "/iso"

[defs.dns]
servers = ["192.168.1.1"]

[defs.ntp]
servers = ["pool.ntp.org"]
```

Field reference:

| Field | Description |
|-------|-------------|
| `platforms` | Hypervisors this location supports. Must match a platform name OSImager knows about (e.g. `virtualbox`, `vmware`, `vsphere`, `proxmox`). |
| `domain` | DNS domain suffix appended to hostnames to form FQDNs (e.g. `myvm.home.local`). |
| `gateway` | Default network gateway for built VMs. |
| `cidr` | Network CIDR. OSImager derives the subnet, prefix length, and netmask from this automatically. |
| `vms_path` | Directory where built VM images are stored. |
| `iso_path` | Directory containing OS installation ISO files. Point this at wherever you download ISOs. |
| `dns.servers` | List of DNS servers injected into kickstart/preseed/autoinst configs. |
| `ntp.servers` | List of NTP servers for time synchronization during and after install. |

---

## Step 2: Set Up Credentials

OS image builds need credentials for SSH access during the build and for setting the root/admin password in the installed OS.

Switch to local secrets mode:

```bash
mkosimage --set credential_source=config
```

Create `~/.config/osimager/secrets` with your credentials:

```
images/linux username=root password=YourPassword
images/windows username=Administrator password=YourPassword
```

The `images/linux` path is referenced by Linux spec files. During the build, OSImager uses these credentials for SSH access to the VM and injects them into kickstart/preseed templates to set the root password. The `images/windows` path works the same way for Windows builds via WinRM and Autounattend.xml.

For HashiCorp Vault integration instead of local secrets, see [Credential Setup](configuration/credential-setup.md).

---

## Step 3: Install the VirtualBox Packer Plugin

```bash
packer plugins install github.com/hashicorp/virtualbox
packer plugins install github.com/hashicorp/ansible
```

---

## Step 4: List Available Specs

```bash
mkosimage --list
```

Output shows every spec OSImager knows about. Specs with a `*` suffix have a matching ISO found in your `iso_path`:

```
Available specs:
  alma-8.10-x86_64 (alma 8.10 x86_64)
  alma-9.5-x86_64 (alma 9.5 x86_64) *
  centos-7.9-x86_64 (centos 7.9 x86_64)
  debian-12-amd64 (debian 12 amd64) *
  rocky-9.5-x86_64 (rocky 9.5 x86_64)
  ...
```

Download the ISO for the spec you want to build and place it in your `iso_path` directory.

---

## Step 5: Build an Image

```bash
mkosimage virtualbox/local/alma-9.5-x86_64
```

The target format is `platform/location/spec`. OSImager:

1. Loads the `virtualbox` platform config (builder type, VM settings).
2. Loads the `local` location config (network, paths, DNS, NTP).
3. Loads the `alma-9.5-x86_64` spec (ISO, kickstart template, provisioners).
4. Merges all three into a unified defs dictionary.
5. Generates a kickstart file from the spec template with the merged values.
6. Produces a Packer build JSON and executes `packer build`.

To assign a hostname and static IP:

```bash
mkosimage virtualbox/local/alma-9.5-x86_64 myvm 192.168.1.100
```

---

## Step 6: Explore

Inspect what OSImager will do before committing to a full build:

```bash
# Dry run -- shows the Packer command without executing it
mkosimage -n virtualbox/local/alma-9.5-x86_64

# Dump the resolved defs dictionary -- see all merged variables
mkosimage -x virtualbox/local/alma-9.5-x86_64

# Dump the Packer build JSON -- see exactly what gets sent to Packer
mkosimage -u virtualbox/local/alma-9.5-x86_64
```

These are useful for debugging location or spec issues, and for understanding how platform + location + spec configs merge together.

---

## Next Steps

- [Location Setup](configuration/location-setup.md) -- multi-platform locations, vSphere/Proxmox network configs
- [Credential Setup](configuration/credential-setup.md) -- HashiCorp Vault integration
- [Platform Reference](reference/platform-reference.md) -- all 13 supported platforms and their options
- [Spec Reference](reference/spec-reference.md) -- spec file format, version ranges, template substitution
- [Supported Operating Systems](reference/supported-os.md) -- full list of distributions and versions
