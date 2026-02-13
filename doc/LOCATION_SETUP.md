# Location Setup Guide

## What is a Location

A location represents a physical or virtual environment where VMs are built. It defines everything OSImager needs to know about your network, storage, and infrastructure: DNS servers, NTP servers, default gateway, domain name, where ISOs are stored, where VM files go, and per-platform overrides for things like vSphere credentials, Proxmox node names, or VMware network configuration.

Every build target has the form `platform/location/spec`. The location is the middle piece -- it bridges the gap between the generic platform definition (how VirtualBox or vSphere works) and the generic spec definition (how to install RHEL 9) by injecting the specifics of YOUR environment (your DNS servers, your storage paths, your vSphere cluster name).

You can have multiple location files for different environments: a home lab, an office lab, a production datacenter, a cloud region. Each is a single JSON file in the `data/locations/` directory inside the osimager package.

## Location File Structure

Location files are JSON documents stored in `data/locations/` within the osimager package directory. Find this directory with:

```bash
python3 -c "import osimager; import os; print(os.path.join(os.path.dirname(osimager.__file__), 'data', 'locations'))"
```

### Complete Field Reference

Here is a fully annotated location file showing every available field:

```json
{
  "platforms": [
    "virtualbox",
    "vmware",
    "vsphere",
    "proxmox",
    "qemu"
  ],
  "defs": {
    "domain": "lab.example.com",
    "cidr": "192.168.1.0/24",
    "dns": {
      "search": [
        "lab.example.com",
        "example.com"
      ],
      "servers": [
        "192.168.1.10",
        "192.168.1.11"
      ]
    },
    "gateway": "192.168.1.1",
    "ntp": {
      "servers": [
        "ntp1.example.com",
        "pool.ntp.org"
      ]
    },
    "vms_path": "/data/vms",
    "iso_path": "/data/iso/"
  },
  "platform_specific": [
    {
      "platform": "vmware",
      "config": {
        "vnc_bind_address": "192.168.1.100",
        "vmx_data": {
          "ethernet0.present": "TRUE",
          "ethernet0.startConnected": "TRUE",
          "ethernet0.connectiontype": "custom",
          "ethernet0.vnet": "/dev/vmnet0"
        }
      }
    },
    {
      "platform": "vsphere",
      "defs": {
        "datacenter": "DC1",
        "cluster": "Cluster1",
        "esxi_host": "esxi01.example.com",
        "datastore": "datastore1",
        "folder": "templates",
        "vm_network": "VM Network",
        "iso_path": "[datastore1] iso/"
      }
    },
    {
      "platform": "proxmox",
      "defs": {
        "proxmox_node": "pve1",
        "vm_storage_pool": "local-lvm",
        "iso_storage_pool": "local"
      }
    }
  ]
}
```

### Field Details

#### Top-Level Fields

**`platforms`** (array of strings, required)

Lists which hypervisor platforms are available at this location. If a user tries to build with a platform not in this list, the build fails with an error. Valid values: `virtualbox`, `vmware`, `vsphere`, `proxmox`, `qemu`, `libvirt`, `hyperv`.

**`defs`** (object, required)

Definitions (variables) that are available for template substitution in spec files. These are merged into the global definition namespace and can be referenced in answer file templates using `>>variable_name<<` syntax.

**`platform_specific`** (array of objects, optional)

Per-platform overrides. Each entry has a `platform` key identifying which platform it applies to, plus `defs` and/or `config` objects that are merged when that platform is selected.

#### Definition Fields (`defs`)

| Field | Type | Description |
|-------|------|-------------|
| `domain` | string | DNS domain for VMs. Combined with VM name to form FQDN: `vmname.domain`. Referenced as `>>domain<<` in templates. |
| `cidr` | string | Network CIDR notation (e.g., `192.168.1.0/24`). Automatically split into `>>subnet<<`, `>>prefix<<`, and `>>netmask<<` for use in kickstart/preseed templates. |
| `dns.search` | array | DNS search domain list. Written into guest resolver config. |
| `dns.servers` | array | DNS server IP addresses. Available as `>>dns1<<`, `>>dns2<<`, etc. |
| `gateway` | string | Default gateway IP. If omitted, computed as the last usable address in the CIDR. Available as `>>gateway<<` and `>>gw<<`. |
| `ntp.servers` | array | NTP server hostnames or IPs. Available as `>>ntp1<<`, `>>ntp2<<`, etc. |
| `vms_path` | string | Base directory for storing VM disk images and configuration files. Platform configs reference this as `>>vms_path<<`. |
| `iso_path` | string | Directory where ISO files are stored or downloaded to. Used by `file://` ISO URLs and as the download target. Must end with `/`. |

## Platform-Specific Configuration

### VirtualBox

VirtualBox is the simplest platform to configure. It creates VMs locally and manages its own networking. The main things you need in your location are `dns`, `gateway`, `domain`, `iso_path`, and `vms_path`.

A minimal VirtualBox-only location:

```json
{
  "platforms": ["virtualbox"],
  "defs": {
    "domain": "home.lab",
    "dns": {
      "search": ["home.lab"],
      "servers": ["192.168.1.1"]
    },
    "gateway": "192.168.1.1",
    "ntp": {
      "servers": ["pool.ntp.org"]
    },
    "vms_path": "/vms",
    "iso_path": "/iso/"
  }
}
```

VirtualBox VMs are stored under `>>vms_path<</vbox/` and default to bridged networking. The platform configuration handles VBoxManage commands for NIC type, IOAPIC, and hardware virtualization settings.

### VMware Workstation / Fusion

VMware Workstation (Linux) and VMware Fusion (macOS) require a VNC bind address and VMX network configuration for Packer to communicate with the VM during build.

Add a `platform_specific` entry for VMware:

```json
{
  "platforms": ["vmware"],
  "defs": {
    "domain": "lab.example.com",
    "cidr": "192.168.1.0/24",
    "dns": {
      "search": ["lab.example.com"],
      "servers": ["192.168.1.1"]
    },
    "gateway": "192.168.1.1",
    "ntp": {
      "servers": ["pool.ntp.org"]
    },
    "vms_path": "/data/vms",
    "iso_path": "/data/iso/"
  },
  "platform_specific": [
    {
      "platform": "vmware",
      "config": {
        "vnc_bind_address": "192.168.1.100",
        "vmx_data": {
          "ethernet0.present": "TRUE",
          "ethernet0.startConnected": "TRUE",
          "ethernet0.connectiontype": "custom",
          "ethernet0.vnet": "/dev/vmnet0"
        }
      }
    }
  ]
}
```

**Key settings:**

- `vnc_bind_address`: IP address Packer binds VNC to for the build console. Set this to an IP on the build machine.
- `vmx_data.ethernet0.vnet`: VMware virtual network device for the VM's network adapter. On Linux this is typically `/dev/vmnet0` (bridged) or `/dev/vmnet8` (NAT). On macOS Fusion, check your vmnet configuration.

VMware VMs are stored under `>>vms_path<</vmware/`.

### vSphere

vSphere requires the most configuration because it builds on a remote vCenter/ESXi infrastructure. Credentials are pulled from HashiCorp Vault (see `data/.vaultconfig`) to avoid storing passwords in configuration files.

```json
{
  "platforms": ["vsphere"],
  "defs": {
    "domain": "dc.example.com",
    "cidr": "10.0.1.0/24",
    "dns": {
      "search": ["dc.example.com"],
      "servers": ["10.0.1.10", "10.0.1.11"]
    },
    "gateway": "10.0.1.1",
    "ntp": {
      "servers": ["ntp.example.com"]
    },
    "vms_path": "/data/vms",
    "iso_path": "/data/iso/"
  },
  "platform_specific": [
    {
      "platform": "vsphere",
      "defs": {
        "datacenter": "DC1",
        "cluster": "Production",
        "esxi_host": "esxi01.dc.example.com",
        "datastore": "vsanDatastore",
        "folder": "templates",
        "vm_network": "VM Network",
        "iso_path": "[vsanDatastore] iso/"
      }
    }
  ]
}
```

**Key settings:**

| Field | Description |
|-------|-------------|
| `datacenter` | vSphere datacenter name |
| `cluster` | Compute cluster name |
| `esxi_host` | Target ESXi host for the build (optional if using DRS) |
| `datastore` | Datastore for the VM's disk files |
| `folder` | VM folder in the vSphere inventory |
| `vm_network` | Port group name for the VM's network adapter |
| `iso_path` | Datastore path for ISOs (note the `[datastore]` prefix syntax) |

**Vault setup for vSphere credentials:**

Create `data/.vaultconfig`:
```
addr=https://vault.example.com:8200
token=your-vault-token
```

Store credentials in Vault at the path `vsphere/<location_name>`:
```bash
vault kv put vsphere/mydc server=vcenter.example.com username=administrator@vsphere.local password=secret
```

The vSphere platform config references these as `{{vault "vsphere/>>location_name<<" "server"}}` etc.

### Proxmox

Proxmox builds require a node name and storage pool names. Like vSphere, credentials are stored in Vault.

```json
{
  "platforms": ["proxmox"],
  "defs": {
    "domain": "lab.example.com",
    "cidr": "192.168.10.0/24",
    "dns": {
      "search": ["lab.example.com"],
      "servers": ["192.168.10.1"]
    },
    "gateway": "192.168.10.1",
    "ntp": {
      "servers": ["pool.ntp.org"]
    },
    "vms_path": "/data/vms",
    "iso_path": "/data/iso/"
  },
  "platform_specific": [
    {
      "platform": "proxmox",
      "defs": {
        "proxmox_node": "pve1",
        "vm_storage_pool": "local-lvm",
        "iso_storage_pool": "local"
      }
    }
  ]
}
```

**Key settings:**

| Field | Description |
|-------|-------------|
| `proxmox_node` | Name of the Proxmox node where VMs are built |
| `vm_storage_pool` | Storage pool for VM disks (e.g., `local-lvm`, `ceph-pool`) |
| `iso_storage_pool` | Storage pool for ISO images (e.g., `local`) |

**Vault setup for Proxmox credentials:**

Store credentials in Vault at the path `proxmox/<location_name>`:
```bash
vault kv put proxmox/mylab server=pve1.example.com username=root@pam password=secret
```

Proxmox builds use virtio SCSI controllers and virtio network adapters by default. The VM connects to bridge `vmbr0`. Older OS specs that do not support virtio drivers automatically fall back to IDE disks and e1000 network adapters via `platform_specific` overrides in the spec configuration.

### QEMU / KVM

QEMU builds produce qcow2 disk images by default with KVM acceleration.

```json
{
  "platforms": ["qemu"],
  "defs": {
    "domain": "lab.example.com",
    "dns": {
      "search": ["lab.example.com"],
      "servers": ["192.168.1.1"]
    },
    "gateway": "192.168.1.1",
    "ntp": {
      "servers": ["pool.ntp.org"]
    },
    "vms_path": "/data/vms",
    "iso_path": "/data/iso/"
  }
}
```

QEMU uses virtio network and disk interfaces by default. The output goes to `>>vms_path<</vmware/>>name<<` (this follows the same layout as VMware for historical reasons). If you need to change the disk format or accelerator, you can add QEMU-specific overrides in `platform_specific`.

## Multiple Locations

You can create as many location files as you need. Each is a separate JSON file in the `data/locations/` directory:

```
data/locations/
    homelab.json       # Home lab with VirtualBox
    office.json        # Office with VMware Workstation
    datacenter.json    # Production datacenter with vSphere
    proxmox.json       # Proxmox cluster
```

Use them by referencing the filename (without `.json`) in your build target:

```bash
mkosimage virtualbox/homelab/debian-12.0-x86_64
mkosimage vmware/office/rhel-9.5-x86_64
mkosimage vsphere/datacenter/rhel-9.5-x86_64
mkosimage proxmox/proxmox/ubuntu-24.04-x86_64
```

## ISO Management

### Where to Get ISOs

Different distributions provide ISOs from different sources:

| Distribution | Source | Notes |
|-------------|--------|-------|
| CentOS | vault.centos.org | All versions available, downloaded automatically |
| AlmaLinux | vault.almalinux.org | All versions available, downloaded automatically |
| Rocky Linux | download.rockylinux.org | All versions available, downloaded automatically |
| Oracle Linux | yum.oracle.com | All versions available, downloaded automatically |
| Ubuntu | releases.ubuntu.com | All LTS versions available, downloaded automatically |
| Debian | cdimage.debian.org | All versions available, downloaded automatically |
| RHEL | archive.org | Many versions available, downloaded automatically |
| SLES | suse.com | Requires subscription; local ISOs via `file://` paths |
| Windows Server | microsoft.com | Requires license; local ISOs via `file://` paths |
| ESXi | vmware.com | Requires license; local ISOs via `file://` paths |

### How ISOs Work

When a spec defines an `iso_url` starting with `http://` or `https://`, Packer downloads the ISO automatically and caches it (by default in `/tmp`). When the URL starts with `file://`, it references a local file relative to your `iso_path`.

### Organizing Local ISOs

For specs that use `file://` URLs, store ISOs in your `iso_path` directory, organized by vendor:

```
/iso/
    RedHat/
        rhel-server-7.9-x86_64-dvd.iso
        rhel-8.10-x86_64-dvd.iso
    SUSE/
        SLE-15-SP6-Full-x86_64-GM-Media1.iso
    Windows/
        windows_server_2025_x64_dvd.iso
    VMware/
        VMware-VMvisor-Installer-8.0U2-22380479.x86_64.iso
```

The exact path convention matches what the specs expect. Check a spec's `iso_url` definition to see the expected path:

```bash
# View a spec's ISO URL
mkosimage -x vsphere/mylab/sles-15.6-x86_64 2>/dev/null | python3 -m json.tool | grep iso_url
```

### Packer Cache Directory

For remote ISOs, Packer caches downloads. The default cache directory is `/tmp`. You can change this with:

```bash
mkosimage --set packer_cache_dir=/data/packer_cache virtualbox/mylab/centos-7.9-x86_64
```

This setting is persisted in the osimager configuration file and applies to all subsequent builds.

### Local-Only Mode

If you have all your ISOs locally and do not want Packer to download anything, use `--local-only`:

```bash
mkosimage --local-only virtualbox/mylab/rhel-9.5-x86_64
```

Or set it permanently:

```bash
mkosimage --set local_only=True virtualbox/mylab/rhel-9.5-x86_64
```

In local-only mode, `iso_url` is set to the local `file://` path derived from `iso_path` + `iso_name`, and Packer will not attempt any downloads.
