# Location Setup

A **location** defines your build environment — the network settings, DNS servers, storage paths, and platform-specific infrastructure details that OSImager needs to build images in your environment.

## File Location

Location files live in `~/.config/osimager/locations/` and support both TOML and JSON formats:

```
~/.config/osimager/locations/
├── lab.toml        # Your lab environment
├── prod.json       # Production vSphere
└── cloud.toml      # Cloud platforms
```

If both `lab.toml` and `lab.json` exist, **JSON takes priority**.

The location name used in the build target matches the filename (without extension):

```bash
mkosimage vsphere/lab/rhel-9.5-x86_64
#                  ^^^
#                  loads ~/.config/osimager/locations/lab.toml (or .json)
```

## Location File Structure

### Minimal Example (VirtualBox)

=== "TOML"

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

=== "JSON"

    ```json
    {
      "platforms": ["virtualbox"],
      "defs": {
        "domain": "home.local",
        "gateway": "192.168.1.1",
        "cidr": "192.168.1.0/24",
        "vms_path": "/vms",
        "iso_path": "/iso",
        "dns": {
          "servers": ["192.168.1.1"]
        },
        "ntp": {
          "servers": ["pool.ntp.org"]
        }
      }
    }
    ```

## Field Reference

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `platforms` | array | Yes | Platform names this location supports (e.g., `["virtualbox", "vmware", "vsphere"]`) |
| `defs` | dict | Yes | Variable definitions used in template substitution |
| `platform_specific` | array | No | Per-platform overrides (see below) |

### Defs Fields

| Field | Type | Description |
|-------|------|-------------|
| `domain` | string | DNS domain suffix for FQDNs (e.g., `lab.example.com`) |
| `gateway` | string | Network gateway IP. Auto-calculated from `cidr` if not provided. |
| `cidr` | string | Network in CIDR notation (e.g., `192.168.1.0/24`). Auto-derives `subnet`, `prefix`, and `netmask`. |
| `vms_path` | string | Base directory for built VM output |
| `iso_path` | string | Directory containing OS installation ISOs |

### Network Auto-Derivation

When you set `cidr`, OSImager automatically computes:

- `subnet` — network address (e.g., `192.168.1.0`)
- `prefix` — CIDR prefix length (e.g., `24`)
- `netmask` — dotted decimal netmask (e.g., `255.255.255.0`)
- `gateway` — if not explicitly set, calculated as the second-to-last address in the subnet

These derived values are available as defs for template substitution in specs and platform configs.

### DNS Configuration

```toml
[defs.dns]
servers = ["192.168.1.1", "8.8.8.8"]
search = ["lab.example.com", "example.com"]
```

DNS servers are expanded into numbered defs: `dns1`, `dns2`, etc. The search domains are joined into a space-separated `dns_search` string. These are used in kickstart, preseed, and cloud-init templates.

### NTP Configuration

```toml
[defs.ntp]
servers = ["pool.ntp.org", "time.example.com"]
```

NTP servers are expanded into numbered defs: `ntp1`, `ntp2`, etc. Used in installer templates for time synchronization.

## Platform-Specific Overrides

Locations that support multiple platforms can provide per-platform defs using `platform_specific` sections. These override the base defs when building for that platform.

=== "TOML"

    ```toml
    platforms = ["virtualbox", "vmware", "vsphere", "proxmox"]

    [defs]
    domain = "lab.example.com"
    gateway = "10.0.1.1"
    cidr = "10.0.1.0/24"
    vms_path = "/vms"
    iso_path = "/iso"

    [defs.dns]
    servers = ["10.0.1.1"]

    [defs.ntp]
    servers = ["pool.ntp.org"]

    # vSphere-specific settings
    [[platform_specific]]
    platform = "vsphere"

    [platform_specific.defs]
    datacenter = "dc1"
    cluster = "cluster1"
    esxi_host = "esxi1.lab.example.com"
    datastore = "datastore1"
    folder = "templates"
    vm_network = "VM Network"

    # Proxmox-specific settings
    [[platform_specific]]
    platform = "proxmox"

    [platform_specific.defs]
    proxmox_node = "pve1"
    iso_storage_pool = "local"
    vm_storage_pool = "local-lvm"
    ```

=== "JSON"

    ```json
    {
      "platforms": ["virtualbox", "vmware", "vsphere", "proxmox"],
      "defs": {
        "domain": "lab.example.com",
        "gateway": "10.0.1.1",
        "cidr": "10.0.1.0/24",
        "vms_path": "/vms",
        "iso_path": "/iso",
        "dns": { "servers": ["10.0.1.1"] },
        "ntp": { "servers": ["pool.ntp.org"] }
      },
      "platform_specific": [
        {
          "platform": "vsphere",
          "defs": {
            "datacenter": "dc1",
            "cluster": "cluster1",
            "esxi_host": "esxi1.lab.example.com",
            "datastore": "datastore1",
            "folder": "templates",
            "vm_network": "VM Network"
          }
        },
        {
          "platform": "proxmox",
          "defs": {
            "proxmox_node": "pve1",
            "iso_storage_pool": "local",
            "vm_storage_pool": "local-lvm"
          }
        }
      ]
    }
    ```

### Platform-Specific Defs by Platform

Each platform has different infrastructure requirements. See the [Platform Reference](../reference/platform-reference.md) for complete details.

**Local ISO platforms** (virtualbox, vmware, qemu, libvirt, hyperv, xenserver):

- `vms_path` — where to store built VMs
- `iso_path` — where ISO files are located

**vSphere:**

- `datacenter` — vSphere datacenter name
- `esxi_host` — target ESXi host
- `cluster` — cluster name
- `datastore` — datastore for VM storage
- `folder` — template folder in vCenter
- `vm_network` — network name for the VM (default: `VM Network`)

**Proxmox:**

- `proxmox_node` — Proxmox node name
- `iso_storage_pool` — storage pool for ISOs
- `vm_storage_pool` — storage pool for VMs

**Azure:**

- `azure_location` — Azure region
- `azure_resource_group` — resource group name

**GCP:**

- `gcp_region` — GCP region
- `gcp_zone` — GCP zone

**AWS:**

- `aws_region` — AWS region
- `aws_vpc_id` — VPC ID
- `aws_subnet_id` — Subnet ID

## How Defs Flow Into the Build

Location defs are one layer in the hierarchical merge chain:

```
all.json defaults
    └── Platform JSON defs
        └── Location defs          <── you are here
            └── Location platform_specific defs
                └── Spec defs
                    └── Specific section overrides (recursive)
                        └── CLI --define overrides
```

Later layers override earlier ones. For example, if the platform sets `boot_disk_size: 16385` and your location sets `boot_disk_size: 40960`, the location value wins.

## Custom Defs

You can add any custom defs to your location. They become available for template substitution in specs and platform configs using the `>>key<<` syntax. This is useful for site-specific values that specs reference.

## Verifying Your Location

Use `--defs` to see the fully-resolved defs dictionary for a build:

```bash
mkosimage -x virtualbox/local/alma-9.5-x86_64
```

This shows every def value after all layers are merged, including auto-derived values like `subnet`, `prefix`, `netmask`, `dns1`, `ntp1`, etc.
